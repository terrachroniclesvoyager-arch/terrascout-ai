"""
Forestry Intelligence AI -- Forest coverage, growth potential, timber value,
fire risk, conservation & harvesting feasibility assessment.
Uses: Overpass API, Open-Meteo, ISRIC SoilGrids, Open Topo Data.
All free, no API key required.
"""

import logging
import math
import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# =============================================================================
# COMPONENT DEFINITIONS
# =============================================================================

FOREST_COMPONENTS = {
    "coverage": {"name": "Forest Coverage", "color": "#166534", "weight": 0.20},
    "growth": {"name": "Growth Potential", "color": "#22c55e", "weight": 0.20},
    "timber": {"name": "Timber Value", "color": "#a16207", "weight": 0.15},
    "fire_risk": {"name": "Fire Risk", "color": "#ef4444", "weight": 0.15},
    "conservation": {"name": "Conservation Value", "color": "#10b981", "weight": 0.15},
    "harvesting": {"name": "Harvesting Feasibility", "color": "#f59e0b", "weight": 0.15},
}

FOREST_TYPE_COLORS = {
    "Deciduous Forest": "#22c55e",
    "Coniferous Forest": "#166534",
    "Mixed Forest": "#15803d",
    "Woodland": "#4ade80",
    "Tree Row": "#86efac",
    "Individual Tree": "#bbf7d0",
    "Nature Reserve": "#10b981",
    "Protected Area": "#059669",
    "Park": "#a3e635",
}


# =============================================================================
# DATA FETCHING (CACHED)
# =============================================================================

@st.cache_data(ttl=1800)
def fetch_forest_data(lat, lon, radius=3000):
    """Fetch forest, wood, tree, reserve and track data from Overpass API."""
    query = f"""
    [out:json][timeout:30];
    (
      way["natural"="wood"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
      relation["landuse"="forest"](around:{radius},{lat},{lon});
      way["natural"="tree_row"](around:{radius},{lat},{lon});
      node["natural"="tree"](around:{radius},{lat},{lon});
      way["leisure"="nature_reserve"](around:{radius},{lat},{lon});
      way["boundary"="protected_area"](around:{radius},{lat},{lon});
      way["highway"~"track|path"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Forest data error: {e}")
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_forestry(lat, lon):
    """Fetch a 7x7 elevation grid for slope and terrain analysis."""
    points = "|".join(
        f"{lat + dy * 0.004},{lon + dx * 0.004}"
        for dy in range(-3, 4)
        for dx in range(-3, 4)
    )
    try:
        resp = requests.get(
            "https://api.opentopodata.org/v1/srtm90m",
            params={"locations": points},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Elevation error: {e}")
        return {"results": []}


# =============================================================================
# HELPERS
# =============================================================================

def _clamp(v, lo=0.0, hi=100.0):
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, v))


def _range_score(value, lo, hi):
    """Return 0-100 score for how well *value* fits inside [lo, hi]."""
    if value is None:
        return 50.0
    if lo <= value <= hi:
        return 100.0
    if value < lo:
        dist = lo - value
        span = hi - lo if hi > lo else 1
        return max(0.0, 100.0 - (dist / span) * 100.0)
    dist = value - hi
    span = hi - lo if hi > lo else 1
    return max(0.0, 100.0 - (dist / span) * 100.0)


def _classify_forestry_score(score):
    """Classify the overall forestry intelligence score."""
    if score >= 80:
        return "Excellent", "#10b981"
    if score >= 65:
        return "Good", "#22c55e"
    if score >= 50:
        return "Moderate", "#f59e0b"
    if score >= 35:
        return "Fair", "#f97316"
    return "Poor", "#ef4444"


def _parse_forest_elements(elements):
    """Parse Overpass elements into categorised forest feature counts."""
    counts = {
        "forests": 0,
        "woods": 0,
        "tree_rows": 0,
        "individual_trees": 0,
        "nature_reserves": 0,
        "protected_areas": 0,
        "tracks": 0,
        "paths": 0,
    }
    forest_types = {}

    for el in elements:
        tags = el.get("tags", {})
        if not isinstance(tags, dict):
            tags = {}

        landuse = tags.get("landuse", "")
        natural = tags.get("natural", "")
        leisure = tags.get("leisure", "")
        boundary = tags.get("boundary", "")
        highway = tags.get("highway", "")
        leaf_type = tags.get("leaf_type", "")

        if landuse == "forest":
            counts["forests"] += 1
            if leaf_type == "broadleaved":
                forest_types["Deciduous Forest"] = forest_types.get("Deciduous Forest", 0) + 1
            elif leaf_type == "needleleaved":
                forest_types["Coniferous Forest"] = forest_types.get("Coniferous Forest", 0) + 1
            elif leaf_type == "mixed":
                forest_types["Mixed Forest"] = forest_types.get("Mixed Forest", 0) + 1
            else:
                forest_types["Mixed Forest"] = forest_types.get("Mixed Forest", 0) + 1
        elif natural == "wood":
            counts["woods"] += 1
            forest_types["Woodland"] = forest_types.get("Woodland", 0) + 1
        elif natural == "tree_row":
            counts["tree_rows"] += 1
            forest_types["Tree Row"] = forest_types.get("Tree Row", 0) + 1
        elif natural == "tree":
            counts["individual_trees"] += 1
            forest_types["Individual Tree"] = forest_types.get("Individual Tree", 0) + 1
        elif leisure == "nature_reserve":
            counts["nature_reserves"] += 1
            forest_types["Nature Reserve"] = forest_types.get("Nature Reserve", 0) + 1
        elif boundary == "protected_area":
            counts["protected_areas"] += 1
            forest_types["Protected Area"] = forest_types.get("Protected Area", 0) + 1
        elif highway == "track":
            counts["tracks"] += 1
        elif highway == "path":
            counts["paths"] += 1

    return counts, forest_types


# =============================================================================
# MAIN COMPUTATION (CACHED)
# =============================================================================

@st.cache_data(ttl=1800)
def compute_forestry_intelligence(lat, lon):
    """
    Fetch all data sources and compute 6 forestry dimension scores (0-100)
    plus an overall Forestry Intelligence Score.
    """
    # ---- fetch data --------------------------------------------------------
    forest_raw = fetch_forest_data(lat, lon, radius=3000)
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    elevation_raw = fetch_elevation_forestry(lat, lon)
    landuse = fetch_landuse_infrastructure(lat, lon, radius=3000)

    # ---- parse forest features ---------------------------------------------
    elements = (forest_raw if isinstance(forest_raw, dict) else {}).get("elements", [])
    counts, forest_types = _parse_forest_elements(
        elements if isinstance(elements, list) else []
    )

    # ---- parse soil --------------------------------------------------------
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l

    def _sv(name, div=10):
        p = _layer_map.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    soc = _sv("soc", 10)        # organic carbon g/kg
    nitrogen = _sv("nitrogen", 100)  # nitrogen g/kg
    ph = _sv("phh2o", 10)       # pH
    clay = _sv("clay", 10)      # clay %
    sand = _sv("sand", 10)      # sand %
    cec = _sv("cec", 10)        # cation exchange capacity

    # ---- parse weather -----------------------------------------------------
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}

    temp_now = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")

    raw_max = daily.get("temperature_2m_max", [])
    raw_min = daily.get("temperature_2m_min", [])
    raw_precip = daily.get("precipitation_sum", [])

    daily_maxs = [v for v in raw_max if v is not None]
    daily_mins = [v for v in raw_min if v is not None]
    daily_precips = [v for v in raw_precip if v is not None]

    avg_temp = (
        (sum(daily_maxs) + sum(daily_mins)) / (len(daily_maxs) + len(daily_mins))
        if (daily_maxs or daily_mins)
        else (temp_now if temp_now is not None else 15.0)
    )
    max_temp = max(daily_maxs) if daily_maxs else (avg_temp + 5)
    min_temp = min(daily_mins) if daily_mins else (avg_temp - 5)

    precip_7d = sum(daily_precips) if daily_precips else 0.0
    annual_precip_est = precip_7d * (365.0 / 7.0) if precip_7d > 0 else 500.0
    humidity_val = humidity if humidity is not None else 50.0

    # ---- parse elevation ---------------------------------------------------
    elev_results = (elevation_raw if isinstance(elevation_raw, dict) else {}).get("results", [])
    elevations = []
    for r in (elev_results if isinstance(elev_results, list) else []):
        e = r.get("elevation") if isinstance(r, dict) else None
        if e is not None:
            elevations.append(float(e))

    center_elev = elevations[len(elevations) // 2] if elevations else 0.0
    min_elev = min(elevations) if elevations else 0.0
    max_elev = max(elevations) if elevations else 0.0
    avg_elev = sum(elevations) / len(elevations) if elevations else 0.0
    elev_range = max_elev - min_elev

    # Slope proxy: elevation range across grid in metres
    # Grid spans ~7*0.004 deg ~ 0.028 deg ~ 2.5-3 km
    grid_span_km = 3.0
    slope_pct = (elev_range / (grid_span_km * 1000) * 100) if grid_span_km > 0 else 0.0
    slope_deg = math.degrees(math.atan(elev_range / (grid_span_km * 1000))) if grid_span_km > 0 else 0.0

    # ---- parse landuse for road access -------------------------------------
    landuse_elements = (landuse if isinstance(landuse, dict) else {}).get("elements", [])
    road_count = 0
    for el in (landuse_elements if isinstance(landuse_elements, list) else []):
        tags = el.get("tags", {})
        if isinstance(tags, dict) and "highway" in tags:
            road_count += 1

    # ====================================================================
    # SCORING: 6 DIMENSIONS (0-100 each)
    # ====================================================================

    # 1. FOREST COVERAGE (forests + woods density in radius)
    forest_area_count = counts["forests"] + counts["woods"]
    tree_row_count = counts["tree_rows"]
    individual_tree_count = counts["individual_trees"]

    if forest_area_count >= 20:
        coverage_base = 90.0
    elif forest_area_count >= 10:
        coverage_base = 65.0
    elif forest_area_count >= 5:
        coverage_base = 40.0
    elif forest_area_count >= 1:
        coverage_base = 20.0
    else:
        coverage_base = 0.0

    # Bonus from tree rows and individual trees
    tree_bonus = min(tree_row_count * 2.0 + individual_tree_count * 0.5, 10.0)
    coverage_score = _clamp(coverage_base + tree_bonus)

    # 2. GROWTH POTENTIAL (climate + soil suitability for tree growth)
    rainfall_score = _range_score(annual_precip_est, 600, 1500)
    temp_growth_score = _range_score(avg_temp, 10, 25)
    soc_score = _clamp(min((soc if soc is not None else 0) * 5.0, 100))
    nitrogen_score = _clamp(min((nitrogen if nitrogen is not None else 0) * 50.0, 100))
    ph_conifer_score = _range_score(ph, 5.5, 6.5) if ph is not None else 50.0

    growth_score = _clamp(
        rainfall_score * 0.30
        + temp_growth_score * 0.25
        + soc_score * 0.20
        + nitrogen_score * 0.15
        + ph_conifer_score * 0.10
    )

    # 3. TIMBER VALUE (species diversity, maturity, hardwood indicators)
    # Species diversity proxy: number of distinct forest types present
    num_forest_types = len([v for v in forest_types.values() if v > 0])
    diversity_score = _clamp(min(num_forest_types * 15.0, 80.0))

    # Maturity indicator: ratio of forest areas to individual trees
    # More forests relative to individual trees suggests mature stands
    total_veg = forest_area_count + individual_tree_count
    if total_veg > 0:
        maturity_ratio = forest_area_count / total_veg
        maturity_score = _clamp(maturity_ratio * 100.0)
    else:
        maturity_score = 0.0

    # Hardwood indicator from soil depth/clay content
    # Higher clay and CEC suggest deeper, more fertile soils for hardwood
    clay_val = clay if clay is not None else 20.0
    cec_val = cec if cec is not None else 10.0
    hardwood_score = _clamp(min(clay_val * 1.5 + cec_val * 2.0, 100.0))

    timber_score = _clamp(
        diversity_score * 0.35
        + maturity_score * 0.40
        + hardwood_score * 0.25
    )

    # 4. FIRE RISK (inverted: lower fire risk = higher score)
    # High temp + low humidity + low rainfall + abundant fuel = high risk
    temp_risk = _clamp((max_temp - 20.0) * 4.0, 0, 100) if max_temp > 20 else 0.0
    humidity_risk = _clamp((100.0 - humidity_val) * 1.2, 0, 100)
    drought_risk = _clamp(
        100.0 - (annual_precip_est / 15.0), 0, 100
    ) if annual_precip_est < 1500 else 0.0
    fuel_load = _clamp(forest_area_count * 4.0, 0, 60)

    raw_fire_risk = (
        temp_risk * 0.30
        + humidity_risk * 0.25
        + drought_risk * 0.25
        + fuel_load * 0.20
    )
    # INVERT: low fire risk = high score
    fire_risk_score = _clamp(100.0 - raw_fire_risk)

    # 5. CONSERVATION VALUE (protected areas, reserves, ecological corridors)
    reserve_count = counts["nature_reserves"] + counts["protected_areas"]
    reserve_score = _clamp(min(reserve_count * 18.0, 70.0))

    # Ecological corridor: connected forest patches (multiple forests nearby)
    corridor_score = 0.0
    if forest_area_count >= 5:
        corridor_score = 60.0
    elif forest_area_count >= 3:
        corridor_score = 40.0
    elif forest_area_count >= 1:
        corridor_score = 20.0

    # Biodiversity proxy from type diversity
    biodiversity_bonus = _clamp(num_forest_types * 10.0, 0, 30)

    conservation_score = _clamp(
        reserve_score * 0.45
        + corridor_score * 0.35
        + biodiversity_bonus * 0.20
    )

    # 6. HARVESTING FEASIBILITY (slope, road access, terrain)
    # Low slope = good
    if slope_deg < 5:
        slope_feasibility = 95.0
    elif slope_deg < 10:
        slope_feasibility = 75.0
    elif slope_deg < 20:
        slope_feasibility = 50.0
    elif slope_deg < 30:
        slope_feasibility = 25.0
    else:
        slope_feasibility = max(5.0, 100.0 - slope_deg * 2.5)

    # Road access: tracks and paths for equipment
    track_count = counts["tracks"] + counts["paths"]
    road_access_score = _clamp(min((track_count + road_count) * 5.0, 60.0))

    # Elevation: moderate elevation (200-1500m) is optimal for forestry
    elev_score = _range_score(center_elev, 200, 1500)

    harvesting_score = _clamp(
        slope_feasibility * 0.45
        + road_access_score * 0.35
        + elev_score * 0.20
    )

    # ====================================================================
    # OVERALL FORESTRY INTELLIGENCE SCORE
    # ====================================================================
    scores = {
        "coverage": round(coverage_score, 1),
        "growth": round(growth_score, 1),
        "timber": round(timber_score, 1),
        "fire_risk": round(fire_risk_score, 1),
        "conservation": round(conservation_score, 1),
        "harvesting": round(harvesting_score, 1),
    }

    overall = sum(
        scores[k] * FOREST_COMPONENTS[k]["weight"]
        for k in FOREST_COMPONENTS
    )
    overall = round(_clamp(overall), 1)

    # ====================================================================
    # CONDITIONS DICT
    # ====================================================================
    conditions = {
        "avg_temp": round(avg_temp, 1),
        "min_temp": round(min_temp, 1) if min_temp is not None else None,
        "max_temp": round(max_temp, 1) if max_temp is not None else None,
        "humidity": round(humidity_val, 1),
        "annual_precip_est": round(annual_precip_est, 0),
        "ph": round(ph, 1) if ph is not None else None,
        "soc": round(soc, 1) if soc is not None else None,
        "nitrogen": round(nitrogen, 2) if nitrogen is not None else None,
        "clay": round(clay, 1) if clay is not None else None,
        "sand": round(sand, 1) if sand is not None else None,
        "cec": round(cec, 1) if cec is not None else None,
        "elevation": round(center_elev, 0),
        "elevation_range": round(elev_range, 1),
        "slope_pct": round(slope_pct, 2),
        "slope_deg": round(slope_deg, 1),
    }

    # ====================================================================
    # RECOMMENDATIONS
    # ====================================================================
    recommendations = []
    if coverage_score < 30:
        recommendations.append(
            "Low forest coverage detected. This area may benefit from "
            "afforestation or reforestation programs to increase canopy cover."
        )
    if growth_score >= 60 and coverage_score < 50:
        recommendations.append(
            "Growth conditions are favorable but existing forest coverage is "
            "limited. High potential for new plantation establishment."
        )
    if fire_risk_score < 40:
        recommendations.append(
            "Elevated fire risk due to high temperatures, low humidity, or "
            "dry conditions. Fire breaks, controlled burning, and monitoring "
            "systems are recommended."
        )
    if conservation_score >= 50:
        recommendations.append(
            "Significant conservation value present with protected areas or "
            "ecological corridors. Sustainable management practices should "
            "prioritize biodiversity preservation."
        )
    if harvesting_score < 30:
        recommendations.append(
            "Difficult terrain for timber harvesting. Cable logging or "
            "helicopter extraction may be necessary. Consider leaving steep "
            "areas as conservation reserves."
        )
    if timber_score >= 60 and harvesting_score >= 50:
        recommendations.append(
            "Good timber value combined with feasible harvesting conditions. "
            "Selective logging with replanting programs could be economically "
            "viable while maintaining forest health."
        )
    if ph is not None and ph < 5.0:
        recommendations.append(
            "Very acidic soil (pH < 5). Favours conifers (spruce, pine) over "
            "broadleaf species. Liming could expand species options."
        )
    if annual_precip_est < 400:
        recommendations.append(
            "Low annual precipitation limits tree growth. Drought-resistant "
            "species (e.g., stone pine, cork oak) are recommended."
        )
    if not recommendations:
        recommendations.append(
            "Conditions appear broadly suitable for forestry. Match species "
            "selection to local climate, soil pH, and terrain characteristics."
        )

    return {
        "scores": scores,
        "overall": overall,
        "counts": counts,
        "forest_types": forest_types,
        "conditions": conditions,
        "recommendations": recommendations,
    }


# =============================================================================
# RENDER TAB
# =============================================================================

def render_forestry_ai_tab():
    """Render the Forestry Intelligence AI tab in Streamlit."""

    st.markdown(
        '<div class="tab-header" style="border-left:4px solid #166534;'
        'background:rgba(22,101,52,0.08);padding:12px 18px;border-radius:8px;'
        'margin-bottom:16px;">'
        "<h4 style='margin:0;color:#e8ecf4;'>Forestry Intelligence AI</h4>"
        "<p style='margin:4px 0 0;color:#8b97b0;font-size:13px;'>"
        "Forest coverage, growth potential, timber value, fire risk, "
        "conservation &amp; harvesting feasibility assessment</p></div>",
        unsafe_allow_html=True,
    )

    # ---- location selector -------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.4, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="forestry_ai_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with col_lat:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="forestry_ai_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="forestry_ai_lon",
        )

    run = st.button(
        "Analyze Forestry Potential",
        type="primary",
        use_container_width=True,
        key="forestry_ai_run",
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Forestry Potential** "
            "to generate forest intelligence scores and recommendations."
        )
        return

    # ---- compute -----------------------------------------------------------
    with st.spinner("Fetching forest, soil, weather and elevation data..."):
        result = compute_forestry_intelligence(lat, lon)

    scores = result["scores"]
    overall = result["overall"]
    counts = result["counts"]
    forest_types = result["forest_types"]
    conditions = result["conditions"]
    recommendations = result["recommendations"]

    classification, class_color = _classify_forestry_score(overall)

    st.markdown("---")

    # ====================================================================
    # 1. HEADER: FORESTRY INTELLIGENCE SCORE
    # ====================================================================
    st.markdown(
        f'<div style="background:rgba(26,26,46,0.85);border:1px solid {class_color};'
        f'border-radius:14px;padding:24px;text-align:center;margin-bottom:16px;">'
        f'<div style="color:#8b97b0;font-size:13px;text-transform:uppercase;'
        f'letter-spacing:1px;">Forestry Intelligence Score</div>'
        f'<div style="color:{class_color};font-size:52px;font-weight:bold;'
        f'margin:8px 0;">{overall}</div>'
        f'<div style="color:{class_color};font-size:18px;font-weight:600;">'
        f'{classification}</div>'
        f'<div style="color:#5a6580;font-size:12px;margin-top:6px;">'
        f'Weighted composite of 6 forestry dimensions</div></div>',
        unsafe_allow_html=True,
    )

    # ====================================================================
    # 2. RADAR CHART OF 6 DIMENSIONS
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "Forestry Dimensions Radar</h5>",
        unsafe_allow_html=True,
    )

    comp_keys = list(FOREST_COMPONENTS.keys())
    radar_names = [FOREST_COMPONENTS[k]["name"] for k in comp_keys]
    radar_values = [scores[k] for k in comp_keys]
    # Close polygon
    radar_names_closed = radar_names + [radar_names[0]]
    radar_values_closed = radar_values + [radar_values[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values_closed,
        theta=radar_names_closed,
        fill="toself",
        fillcolor="rgba(22,101,52,0.18)",
        line=dict(color="#22c55e", width=2),
        marker=dict(size=6, color="#22c55e"),
        name="Score",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(26,26,46,0.6)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2a3550",
                tickfont=dict(color="#5a6580", size=10),
            ),
            angularaxis=dict(
                gridcolor="#2a3550",
                tickfont=dict(color="#e8ecf4", size=11),
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30),
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="forai_pchart1")

    # ====================================================================
    # 3. SIX METRIC CARDS (3x2 grid)
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "Dimension Scores</h5>",
        unsafe_allow_html=True,
    )

    comp_items = list(FOREST_COMPONENTS.items())
    # Row 1: first 3
    row1_cols = st.columns(3)
    for idx, (key, meta) in enumerate(comp_items[:3]):
        with row1_cols[idx]:
            sc = scores[key]
            if sc >= 70:
                score_color = "#10b981"
            elif sc >= 45:
                score_color = "#f59e0b"
            else:
                score_color = "#ef4444"

            # Description per dimension
            desc_map = {
                "coverage": f"Forests: {counts['forests']} | Woods: {counts['woods']} | Trees: {counts['individual_trees']}",
                "growth": f"Rainfall: {conditions['annual_precip_est']:.0f} mm/yr | Temp: {conditions['avg_temp']} C",
                "timber": f"Types: {len([v for v in forest_types.values() if v > 0])} | Maturity index",
            }
            desc = desc_map.get(key, "")

            st.markdown(
                f'<div style="background:rgba(26,26,46,0.85);'
                f'border:1px solid {meta["color"]};border-radius:10px;'
                f'padding:14px;text-align:center;margin-bottom:8px;">'
                f'<div style="color:#8b97b0;font-size:11px;text-transform:uppercase;'
                f'letter-spacing:0.5px;">{meta["name"]}</div>'
                f'<div style="color:{score_color};font-size:32px;font-weight:bold;'
                f'margin:6px 0;">{sc}</div>'
                f'<div style="color:#5a6580;font-size:11px;">{desc}</div>'
                f'<div style="background:#1a2235;border-radius:6px;height:8px;'
                f'margin-top:8px;overflow:hidden;">'
                f'<div style="width:{sc}%;background:{meta["color"]};height:100%;'
                f'border-radius:6px;"></div></div></div>',
                unsafe_allow_html=True,
            )

    # Row 2: last 3
    row2_cols = st.columns(3)
    for idx, (key, meta) in enumerate(comp_items[3:]):
        with row2_cols[idx]:
            sc = scores[key]
            if sc >= 70:
                score_color = "#10b981"
            elif sc >= 45:
                score_color = "#f59e0b"
            else:
                score_color = "#ef4444"

            desc_map = {
                "fire_risk": f"Humidity: {conditions['humidity']}% | Max T: {conditions.get('max_temp', 'N/A')} C",
                "conservation": f"Reserves: {counts['nature_reserves']} | Protected: {counts['protected_areas']}",
                "harvesting": f"Slope: {conditions['slope_deg']} deg | Tracks: {counts['tracks']} | Paths: {counts['paths']}",
            }
            desc = desc_map.get(key, "")

            st.markdown(
                f'<div style="background:rgba(26,26,46,0.85);'
                f'border:1px solid {meta["color"]};border-radius:10px;'
                f'padding:14px;text-align:center;margin-bottom:8px;">'
                f'<div style="color:#8b97b0;font-size:11px;text-transform:uppercase;'
                f'letter-spacing:0.5px;">{meta["name"]}</div>'
                f'<div style="color:{score_color};font-size:32px;font-weight:bold;'
                f'margin:6px 0;">{sc}</div>'
                f'<div style="color:#5a6580;font-size:11px;">{desc}</div>'
                f'<div style="background:#1a2235;border-radius:6px;height:8px;'
                f'margin-top:8px;overflow:hidden;">'
                f'<div style="width:{sc}%;background:{meta["color"]};height:100%;'
                f'border-radius:6px;"></div></div></div>',
                unsafe_allow_html=True,
            )

    # ====================================================================
    # 4. FOREST TYPES PIE CHART
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "Forest Types Distribution</h5>",
        unsafe_allow_html=True,
    )

    if forest_types:
        pie_labels = list(forest_types.keys())
        pie_values = list(forest_types.values())
        pie_colors = [
            FOREST_TYPE_COLORS.get(lbl, "#8b97b0") for lbl in pie_labels
        ]

        fig_pie = go.Figure()
        fig_pie.add_trace(go.Pie(
            labels=pie_labels,
            values=pie_values,
            hole=0.45,
            marker=dict(colors=pie_colors, line=dict(color="#1a1a2e", width=2)),
            textfont=dict(color="#e8ecf4", size=12),
            textinfo="label+percent",
            hoverinfo="label+value+percent",
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
            height=350,
            legend=dict(
                font=dict(color="#8b97b0", size=11),
                bgcolor="rgba(26,26,46,0.6)",
            ),
            showlegend=True,
        )
        st.plotly_chart(fig_pie, use_container_width=True, key="forai_pchart2")
    else:
        st.info("No distinct forest types identified in the search radius.")

    # ====================================================================
    # 5. GROWTH CONDITIONS SUMMARY
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "Growth Conditions Summary</h5>",
        unsafe_allow_html=True,
    )

    gc1, gc2, gc3, gc4, gc5, gc6 = st.columns(6)
    gc1.metric("Avg Temp", f"{conditions['avg_temp']} C")
    gc2.metric("Humidity", f"{conditions['humidity']}%")
    gc3.metric("Annual Precip (est)", f"{conditions['annual_precip_est']:.0f} mm")
    gc4.metric("Elevation", f"{conditions['elevation']:.0f} m")
    gc5.metric("Slope", f"{conditions['slope_deg']} deg")
    gc6.metric("Elev Range", f"{conditions['elevation_range']:.0f} m")

    sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
    sc1.metric("pH", f"{conditions['ph']}" if conditions["ph"] is not None else "N/A")
    sc2.metric("SOC", f"{conditions['soc']} g/kg" if conditions["soc"] is not None else "N/A")
    sc3.metric("Nitrogen", f"{conditions['nitrogen']} g/kg" if conditions["nitrogen"] is not None else "N/A")
    sc4.metric("Clay", f"{conditions['clay']}%" if conditions["clay"] is not None else "N/A")
    sc5.metric("Sand", f"{conditions['sand']}%" if conditions["sand"] is not None else "N/A")
    sc6.metric("CEC", f"{conditions['cec']} cmol/kg" if conditions["cec"] is not None else "N/A")

    # ====================================================================
    # 6. FOREST FEATURE COUNTS
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "Forest Feature Inventory</h5>",
        unsafe_allow_html=True,
    )

    fc1, fc2, fc3, fc4 = st.columns(4)
    fc1.metric("Forests", counts["forests"])
    fc2.metric("Woodlands", counts["woods"])
    fc3.metric("Tree Rows", counts["tree_rows"])
    fc4.metric("Individual Trees", counts["individual_trees"])

    fc5, fc6, fc7, fc8 = st.columns(4)
    fc5.metric("Nature Reserves", counts["nature_reserves"])
    fc6.metric("Protected Areas", counts["protected_areas"])
    fc7.metric("Forest Tracks", counts["tracks"])
    fc8.metric("Paths", counts["paths"])

    # ====================================================================
    # 7. DIMENSION BREAKDOWN BAR CHART
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "Dimension Score Breakdown</h5>",
        unsafe_allow_html=True,
    )

    bar_names = [FOREST_COMPONENTS[k]["name"] for k in comp_keys]
    bar_values = [scores[k] for k in comp_keys]
    bar_colors = [FOREST_COMPONENTS[k]["color"] for k in comp_keys]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        y=bar_names,
        x=bar_values,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{v}" for v in bar_values],
        textposition="outside",
        textfont=dict(color="#e8ecf4", size=12),
    ))
    fig_bar.update_layout(
        xaxis=dict(
            range=[0, 110], title="Score (0-100)",
            gridcolor="#2a3550",
            tickfont=dict(color="#8b97b0"),
            title_font=dict(color="#8b97b0"),
        ),
        yaxis=dict(tickfont=dict(color="#e8ecf4", size=12)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.4)",
        margin=dict(l=180, r=50, t=10, b=30),
        height=300,
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="forai_pchart3")

    # ====================================================================
    # 8. RECOMMENDATIONS
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-top:12px;margin-bottom:4px;'>"
        "Forestry Recommendations</h5>",
        unsafe_allow_html=True,
    )
    for rec in recommendations:
        st.markdown(
            f'<div style="background:rgba(22,101,52,0.07);'
            f'border-left:3px solid #166534;padding:10px 14px;'
            f'border-radius:0 8px 8px 0;margin-bottom:6px;'
            f'color:#c8d0dc;font-size:13px;">'
            f'{rec}</div>',
            unsafe_allow_html=True,
        )
