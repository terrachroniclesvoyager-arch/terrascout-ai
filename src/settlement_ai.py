"""
Settlement Planning AI module for TerraScout AI.
Evaluates a location's suitability for human settlement across multiple
factors: terrain, water supply, climate comfort, soil foundation,
natural hazard safety, access & connectivity, resource availability,
and environmental protection.
Uses free APIs: Open-Meteo, ISRIC SoilGrids, Overpass, Open-Elevation, USGS.
"""

import math
import logging
from html import escape

import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# THEME CONSTANTS  (dark + warm earth tones for settlement)
# ==============================================================================

CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"

CLR_EXCELLENT = "#22c55e"
CLR_GOOD = "#84cc16"
CLR_MODERATE = "#f59e0b"
CLR_CHALLENGING = "#ef4444"
CLR_UNSUITABLE = "#991b1b"

# Warm earth-tone palette for settlement factors
FACTOR_COLORS = {
    "Terrain Suitability": "#c9a66b",
    "Water Supply": "#3b82f6",
    "Climate Comfort": "#f59e0b",
    "Soil Foundation": "#a0785a",
    "Natural Hazard Safety": "#ef4444",
    "Access & Connectivity": "#8b5cf6",
    "Resource Availability": "#10b981",
    "Environmental Protection": "#06b6d4",
}


# ==============================================================================
# HELPERS
# ==============================================================================

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _class_color(score: float) -> str:
    if score >= 80:
        return CLR_EXCELLENT
    if score >= 60:
        return CLR_GOOD
    if score >= 40:
        return CLR_MODERATE
    if score >= 20:
        return CLR_CHALLENGING
    return CLR_UNSUITABLE


def _classify(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Challenging"
    return "Unsuitable"


# ==============================================================================
# COMPUTE SETTLEMENT SCORE
# ==============================================================================

@st.cache_data(ttl=1800)
def compute_settlement_score(lat: float, lon: float) -> dict:
    """
    Evaluate settlement suitability for the given location.

    Returns a dict with:
        overall            - weighted average score (0-100)
        classification     - Excellent / Good / Moderate / Challenging / Unsuitable
        class_color        - hex color for classification
        factor_scores      - dict of 8 factor scores (0-100)
        factor_details     - dict of short explanation per factor
        key_advantages     - list of advantage strings
        key_challenges     - list of challenge strings
        recommendations    - list of recommendation strings
    """

    # -- Fetch all data sources ------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elev = fetch_elevation_grid(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)
    protected = fetch_protected_areas(lat, lon)
    quakes = fetch_earthquakes(lat, lon)

    # -- Parse data safely -----------------------------------------------------

    # Soil
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay_pct = _sv("clay", 10)
    sand_pct = _sv("sand", 10)
    soc_val = _sv("soc", 10)

    # Weather
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    temp_c = current.get("temperature_2m", 20.0) or 20.0
    humidity = current.get("relative_humidity_2m", 50.0) or 50.0
    precip = current.get("precipitation", 0.0) or 0.0
    daily = (weather if isinstance(weather, dict) else {}).get("daily", {})
    daily_precip = daily.get("precipitation_sum", [])
    total_precip_7d = sum(v for v in daily_precip if v is not None)

    # Water
    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    water_count = len(water_elements) if isinstance(water_elements, list) else 0
    springs = [e for e in water_elements if e.get("tags", {}).get("natural") == "spring"]
    rivers = [e for e in water_elements if e.get("tags", {}).get("waterway") in
              ("river", "stream", "canal")]
    wells = [e for e in water_elements if e.get("tags", {}).get("man_made") == "water_well"]

    # Infrastructure
    infra_elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    infra_list = infra_elements if isinstance(infra_elements, list) else []
    roads = [e for e in infra_list if e.get("tags", {}).get("highway")]
    buildings = [e for e in infra_list if e.get("tags", {}).get("building")]
    farmland = [e for e in infra_list if
                e.get("tags", {}).get("landuse") in ("farmland", "orchard", "vineyard")]

    # Earthquakes
    features = (quakes if isinstance(quakes, dict) else {}).get("features", [])
    eq_count = len(features) if isinstance(features, list) else 0
    magnitudes = []
    for f in (features if isinstance(features, list) else []):
        mag = (f.get("properties") or {}).get("mag")
        if mag is not None:
            magnitudes.append(float(mag))
    max_mag = max(magnitudes) if magnitudes else 0.0

    # Elevation
    raw_elevations = (elev if isinstance(elev, dict) else {}).get("grid_elevations", [])
    elevations = [e for e in (raw_elevations if isinstance(raw_elevations, list) else [])
                  if e is not None]
    center_elev = (elev if isinstance(elev, dict) else {}).get("center_elevation", 0.0) or 0.0
    elev_min = min(elevations) if elevations else 0.0
    elev_max = max(elevations) if elevations else 0.0
    elev_range = elev_max - elev_min

    # Protected areas
    prot_elements = (protected if isinstance(protected, dict) else {}).get("elements", [])
    prot_count = len(prot_elements) if isinstance(prot_elements, list) else 0

    # =========================================================================
    # FACTOR 1: Terrain Suitability (flat to gentle slope, no flood-prone valleys)
    # =========================================================================
    if elev_range < 10:
        terrain_score = 95.0
        terrain_detail = "Very flat terrain, excellent for construction"
    elif elev_range < 30:
        terrain_score = 80.0
        terrain_detail = "Gentle slopes, good building conditions"
    elif elev_range < 80:
        terrain_score = 60.0
        terrain_detail = "Moderate slopes, requires grading"
    elif elev_range < 200:
        terrain_score = 35.0
        terrain_detail = "Steep terrain, significant earthwork needed"
    else:
        terrain_score = 15.0
        terrain_detail = "Extreme relief, very difficult for settlement"
    # Penalize very low elevation (flood-prone)
    if center_elev < 5:
        terrain_score = _clamp(terrain_score - 25)
        terrain_detail += "; flood-prone low elevation"
    elif center_elev < 20:
        terrain_score = _clamp(terrain_score - 10)
        terrain_detail += "; relatively low elevation"
    terrain_score = round(_clamp(terrain_score), 1)

    # =========================================================================
    # FACTOR 2: Water Supply
    # =========================================================================
    water_score = 20.0  # baseline
    if len(springs) > 0:
        water_score += min(30, len(springs) * 15)
    if len(rivers) > 0:
        water_score += min(25, len(rivers) * 10)
    if len(wells) > 0:
        water_score += min(25, len(wells) * 10)
    water_score = round(_clamp(water_score), 1)
    if water_score >= 70:
        water_detail = f"Abundant water: {len(springs)} springs, {len(rivers)} rivers, {len(wells)} wells"
    elif water_score >= 40:
        water_detail = f"Moderate water access: {water_count} features nearby"
    else:
        water_detail = "Limited water sources; wells or piped supply needed"

    # =========================================================================
    # FACTOR 3: Climate Comfort (10-30C, humidity 30-60%, adequate rainfall)
    # =========================================================================
    # Temperature component (ideal 15-25C)
    if 15 <= temp_c <= 25:
        temp_comp = 40.0
    elif 10 <= temp_c <= 30:
        temp_comp = 30.0
    elif 5 <= temp_c <= 35:
        temp_comp = 18.0
    else:
        temp_comp = 5.0
    # Humidity component (ideal 30-60%)
    if 30 <= humidity <= 60:
        hum_comp = 30.0
    elif 20 <= humidity <= 75:
        hum_comp = 20.0
    else:
        hum_comp = 8.0
    # Rainfall component (moderate is best)
    if 2 <= total_precip_7d <= 40:
        rain_comp = 30.0
    elif total_precip_7d <= 80:
        rain_comp = 20.0
    elif total_precip_7d == 0:
        rain_comp = 15.0
    else:
        rain_comp = 10.0
    climate_score = round(_clamp(temp_comp + hum_comp + rain_comp), 1)
    climate_detail = f"Temp {temp_c:.1f}C, humidity {humidity:.0f}%, 7d precip {total_precip_7d:.1f}mm"

    # =========================================================================
    # FACTOR 4: Soil Foundation (low clay, low moisture, good bearing)
    # =========================================================================
    if clay_pct is not None:
        if clay_pct < 15:
            soil_score = 85.0
            soil_detail = f"Low clay ({clay_pct:.1f}%), stable foundation"
        elif clay_pct < 30:
            soil_score = 65.0
            soil_detail = f"Moderate clay ({clay_pct:.1f}%), acceptable foundation"
        elif clay_pct < 50:
            soil_score = 40.0
            soil_detail = f"High clay ({clay_pct:.1f}%), expansive soil risk"
        else:
            soil_score = 20.0
            soil_detail = f"Very high clay ({clay_pct:.1f}%), poor foundation"
        # Sandy soil bonus (good drainage)
        if sand_pct is not None and sand_pct > 40:
            soil_score = _clamp(soil_score + 10)
            soil_detail += f"; sandy ({sand_pct:.0f}%), good drainage"
    else:
        soil_score = 50.0
        soil_detail = "Soil data unavailable; on-site testing recommended"
    soil_score = round(_clamp(soil_score), 1)

    # =========================================================================
    # FACTOR 5: Natural Hazard Safety (seismic + flood + landslide)
    # =========================================================================
    # Seismic component
    if eq_count == 0:
        seismic_comp = 40.0
    elif max_mag < 3:
        seismic_comp = 30.0
    elif max_mag < 5:
        seismic_comp = 18.0
    elif max_mag < 6:
        seismic_comp = 8.0
    else:
        seismic_comp = 2.0
    # Flood component (low elevation + water proximity)
    if center_elev > 100 and water_count < 3:
        flood_comp = 35.0
    elif center_elev > 30:
        flood_comp = 25.0
    elif center_elev > 10:
        flood_comp = 15.0
    else:
        flood_comp = 5.0
    # Landslide component (steep + wet)
    if elev_range < 30:
        landslide_comp = 25.0
    elif elev_range < 80:
        landslide_comp = 15.0
    else:
        landslide_comp = 5.0
    hazard_score = round(_clamp(seismic_comp + flood_comp + landslide_comp), 1)
    parts = []
    if eq_count > 0:
        parts.append(f"{eq_count} quakes (max M{max_mag:.1f})")
    else:
        parts.append("no recent seismic activity")
    if center_elev < 20:
        parts.append("flood-prone elevation")
    if elev_range > 80:
        parts.append("landslide-prone slopes")
    hazard_detail = "; ".join(parts) if parts else "Low natural hazard risk"

    # =========================================================================
    # FACTOR 6: Access & Connectivity
    # =========================================================================
    road_count = len(roads)
    building_count = len(buildings)
    if road_count > 20:
        access_score = 90.0
        access_detail = f"Well-connected: {road_count} road segments, {building_count} buildings"
    elif road_count > 10:
        access_score = 70.0
        access_detail = f"Good access: {road_count} roads nearby"
    elif road_count > 3:
        access_score = 50.0
        access_detail = f"Moderate access: {road_count} roads"
    elif road_count > 0:
        access_score = 30.0
        access_detail = f"Limited access: {road_count} road(s)"
    else:
        access_score = 10.0
        access_detail = "Remote location, no mapped roads nearby"
    access_score = round(_clamp(access_score), 1)

    # =========================================================================
    # FACTOR 7: Resource Availability (food production, building materials)
    # =========================================================================
    resource_score = 25.0  # baseline
    if len(farmland) > 0:
        resource_score += min(35, len(farmland) * 10)
    if soc_val is not None and soc_val > 10:
        resource_score += 15.0
    elif soc_val is not None and soc_val > 5:
        resource_score += 8.0
    if building_count > 5:
        resource_score += 15.0
    elif building_count > 0:
        resource_score += 8.0
    if water_count > 3:
        resource_score += 10.0
    resource_score = round(_clamp(resource_score), 1)
    if resource_score >= 70:
        resource_detail = "Rich resources: farmland, fertile soil, water, materials"
    elif resource_score >= 40:
        resource_detail = "Moderate resources available for settlement"
    else:
        resource_detail = "Limited local resources; supply chains required"

    # =========================================================================
    # FACTOR 8: Environmental Protection
    # =========================================================================
    if prot_count == 0:
        env_score = 90.0
        env_detail = "No protected areas nearby; minimal restrictions"
    elif prot_count <= 2:
        env_score = 65.0
        env_detail = f"{prot_count} protected area(s) nearby; moderate restrictions"
    elif prot_count <= 5:
        env_score = 40.0
        env_detail = f"{prot_count} protected areas; significant environmental constraints"
    else:
        env_score = 15.0
        env_detail = f"{prot_count} protected areas; severe development restrictions"
    env_score = round(_clamp(env_score), 1)

    # =========================================================================
    # AGGREGATE
    # =========================================================================
    factor_scores = {
        "Terrain Suitability": terrain_score,
        "Water Supply": water_score,
        "Climate Comfort": climate_score,
        "Soil Foundation": soil_score,
        "Natural Hazard Safety": hazard_score,
        "Access & Connectivity": access_score,
        "Resource Availability": resource_score,
        "Environmental Protection": env_score,
    }
    factor_details = {
        "Terrain Suitability": terrain_detail,
        "Water Supply": water_detail,
        "Climate Comfort": climate_detail,
        "Soil Foundation": soil_detail,
        "Natural Hazard Safety": hazard_detail,
        "Access & Connectivity": access_detail,
        "Resource Availability": resource_detail,
        "Environmental Protection": env_detail,
    }

    weights = {
        "Terrain Suitability": 1.5,
        "Water Supply": 2.0,
        "Climate Comfort": 1.5,
        "Soil Foundation": 1.2,
        "Natural Hazard Safety": 2.0,
        "Access & Connectivity": 1.3,
        "Resource Availability": 1.0,
        "Environmental Protection": 1.0,
    }
    total_w = sum(weights.values())
    overall = round(sum(factor_scores[k] * weights[k] for k in factor_scores) / total_w, 1)
    classification = _classify(overall)
    class_color = _class_color(overall)

    # -- Key advantages & challenges ------------------------------------------
    key_advantages = []
    key_challenges = []
    for k, v in factor_scores.items():
        if v >= 70:
            key_advantages.append(f"{k}: {v}/100 - {factor_details[k]}")
        if v < 40:
            key_challenges.append(f"{k}: {v}/100 - {factor_details[k]}")

    if not key_advantages:
        key_advantages.append("No strong advantages identified at this location")
    if not key_challenges:
        key_challenges.append("No critical challenges identified")

    # -- Recommendations -------------------------------------------------------
    recommendations = []
    if terrain_score < 40:
        recommendations.append(
            "Conduct detailed geotechnical survey before any construction. "
            "Significant earthwork or terracing may be required."
        )
    if water_score < 40:
        recommendations.append(
            "Water supply is limited. Plan for well drilling, rainwater harvesting, "
            "or piped water infrastructure before settlement."
        )
    if climate_score < 40:
        recommendations.append(
            "Climate conditions are challenging. Design structures for extreme weather "
            "with appropriate insulation, ventilation, and drainage."
        )
    if soil_score < 40:
        recommendations.append(
            "Soil conditions are poor for foundations. Use deep pilings or soil "
            "improvement techniques. Avoid standard shallow foundations."
        )
    if hazard_score < 40:
        recommendations.append(
            "Significant natural hazard exposure. Implement seismic-resistant design, "
            "flood barriers, or slope stabilization as needed."
        )
    if access_score < 40:
        recommendations.append(
            "Remote location with poor connectivity. Budget for access road "
            "construction and consider logistics for supply delivery."
        )
    if resource_score < 40:
        recommendations.append(
            "Local resources are scarce. Plan robust supply chains for food, "
            "water, and building materials."
        )
    if env_score < 40:
        recommendations.append(
            "Multiple protected areas nearby. Obtain environmental impact "
            "assessments and regulatory approvals before development."
        )
    if not recommendations:
        recommendations.append(
            "Location shows favorable conditions for settlement. "
            "Proceed with standard site investigation and planning procedures."
        )

    return {
        "overall": overall,
        "classification": classification,
        "class_color": class_color,
        "factor_scores": factor_scores,
        "factor_details": factor_details,
        "key_advantages": key_advantages,
        "key_challenges": key_challenges,
        "recommendations": recommendations,
    }


# ==============================================================================
# CHART BUILDERS
# ==============================================================================

def _build_radar_chart(factor_scores: dict) -> go.Figure:
    """Build a radar chart of the 8 settlement factors."""
    labels = list(factor_scores.keys())
    values = list(factor_scores.values())
    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(201,166,107,0.15)",
        line={"color": "#c9a66b", "width": 2.5},
        marker={"size": 6, "color": "#c9a66b"},
        name="Settlement Score",
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
    ))
    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
                "gridcolor": "#2a3550",
            },
            "angularaxis": {
                "tickfont": {"color": CLR_TEXT, "size": 11},
                "gridcolor": "#2a3550",
            },
            "bgcolor": CLR_BG,
        },
        title={
            "text": "Settlement Factor Profile",
            "font": {"color": CLR_TEXT, "size": 16},
        },
        height=420,
        margin=dict(l=60, r=60, t=60, b=40),
        paper_bgcolor=CLR_BG,
        showlegend=False,
    )
    return fig


def _build_bar_chart(factor_scores: dict) -> go.Figure:
    """Build a horizontal bar chart sorted by score."""
    sorted_items = sorted(factor_scores.items(), key=lambda x: x[1])
    names = [item[0] for item in sorted_items]
    scores = [item[1] for item in sorted_items]
    colors = [FACTOR_COLORS.get(n, "#c9a66b") for n in names]

    fig = go.Figure(go.Bar(
        x=scores,
        y=names,
        orientation="h",
        marker={"color": colors, "line": {"width": 0}},
        text=[f"{s:.0f}" for s in scores],
        textposition="auto",
        textfont={"color": CLR_TEXT, "size": 12},
        hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
    ))
    fig.update_layout(
        title={
            "text": "Factor Scores (sorted)",
            "font": {"color": CLR_TEXT, "size": 16},
        },
        height=380,
        margin=dict(l=180, r=30, t=50, b=30),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        xaxis={
            "range": [0, 105],
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title": {"text": "Score (0-100)", "font": {"color": CLR_TEXT_SEC}},
        },
        yaxis={
            "tickfont": {"color": CLR_TEXT, "size": 12},
        },
    )
    return fig


# ==============================================================================
# RENDER
# ==============================================================================

def render_settlement_ai_tab():
    """Render the Settlement Planning AI tab in the Streamlit UI."""

    # -- Header ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Settlement Planning AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Comprehensive settlement suitability analysis across terrain,
                water, climate, soil, hazards, connectivity, resources, and
                environmental constraints.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------------
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="sai_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="sai_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="sai_lon",
        )

    run_btn = st.button(
        "Evaluate Settlement Potential",
        type="primary",
        key="sai_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Evaluate Settlement Potential** to begin.")
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching multi-source data and evaluating settlement potential..."):
        result = compute_settlement_score(lat, lon)

    overall = result["overall"]
    classification = result["classification"]
    class_color = result["class_color"]
    factor_scores = result["factor_scores"]
    factor_details = result["factor_details"]
    advantages = result["key_advantages"]
    challenges = result["key_challenges"]
    recommendations = result["recommendations"]

    # -- Overall score header --------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{class_color}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {class_color}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                        flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};
                                 text-transform:uppercase;letter-spacing:1px;">
                        Overall Settlement Score
                    </span>
                    <h1 style="margin:4px 0;color:{class_color};font-size:42px;">
                        {overall}/100
                    </h1>
                    <span style="font-size:18px;color:{class_color};font-weight:600;">
                        {escape(classification)}
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Factor cards (4x2 grid) -----------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Settlement Factor Breakdown
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    factor_keys = list(factor_scores.keys())
    row1_keys = factor_keys[:4]
    row2_keys = factor_keys[4:]

    for row_keys in [row1_keys, row2_keys]:
        cols = st.columns(len(row_keys))
        for col, key in zip(cols, row_keys):
            score_val = factor_scores[key]
            s_color = _class_color(score_val)
            s_class = _classify(score_val)
            f_color = FACTOR_COLORS.get(key, "#c9a66b")
            bar_width = max(5, score_val)
            detail_text = escape(factor_details.get(key, ""))
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {f_color}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:195px;">
                        <div style="font-size:12px;color:{f_color};margin-bottom:6px;
                                    font-weight:600;">
                            {escape(key)}
                        </div>
                        <div style="font-size:32px;font-weight:700;color:{s_color};">
                            {score_val:.0f}
                        </div>
                        <div style="font-size:12px;color:{s_color};font-weight:600;
                                    margin-bottom:8px;">
                            {escape(s_class)}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                    margin:8px 0;">
                            <div style="background:{s_color};width:{bar_width}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:10px;color:{CLR_TEXT_SEC};margin-top:6px;
                                    line-height:1.4;">
                            {detail_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Radar chart -----------------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    radar_fig = _build_radar_chart(factor_scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="sai_radar")

    # -- Key Advantages --------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Key Advantages
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for adv in advantages:
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {CLR_EXCELLENT}44;
                        border-left:4px solid {CLR_EXCELLENT};
                        border-radius:8px;padding:12px 16px;margin:6px 0;">
                <span style="color:{CLR_TEXT};font-size:13px;line-height:1.5;">
                    {escape(adv)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Key Challenges --------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Key Challenges
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for ch in challenges:
        ch_color = CLR_CHALLENGING if "Unsuitable" not in ch else CLR_UNSUITABLE
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {ch_color}44;
                        border-left:4px solid {ch_color};
                        border-radius:8px;padding:12px 16px;margin:6px 0;">
                <span style="color:{CLR_TEXT};font-size:13px;line-height:1.5;">
                    {escape(ch)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Horizontal bar chart --------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    bar_fig = _build_bar_chart(factor_scores)
    st.plotly_chart(bar_fig, use_container_width=True, key="sai_bar")

    # -- Recommendations -------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Recommendations
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for rec in recommendations:
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {CLR_BORDER};
                        border-left:4px solid #c9a66b;
                        border-radius:8px;padding:14px 18px;margin:8px 0;">
                <span style="color:{CLR_TEXT};font-size:14px;line-height:1.5;">
                    {escape(rec)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Footer ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="text-align:center;padding:16px;margin-top:20px;
                    color:{CLR_TEXT_SEC};font-size:12px;">
            Settlement Planning AI powered by Open-Meteo, ISRIC SoilGrids,
            OpenStreetMap, Open-Elevation, and USGS.
            Scores are indicative and should complement professional site assessments.
        </div>
        """,
        unsafe_allow_html=True,
    )
