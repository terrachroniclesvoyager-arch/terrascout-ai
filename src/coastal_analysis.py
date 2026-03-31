"""
Coastal Intelligence AI module for TerraScout AI.
Analyzes coastal and maritime risk including erosion, sea level rise exposure,
storm surge, marine resources, and coastal infrastructure vulnerability.
Uses Open-Meteo, Open-Elevation, Overpass API, and ISRIC SoilGrids.
All free, no API key required.
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
    fetch_weather_data,
    fetch_elevation_grid,
    fetch_water_features,
    fetch_soil_data,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# =============================================================================
# THEME CONSTANTS
# =============================================================================

CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"

# Ocean-specific palette (blues & teals)
CLR_OCEAN_DEEP = "#0e7490"
CLR_OCEAN_MID = "#0891b2"
CLR_OCEAN_LIGHT = "#06b6d4"
CLR_OCEAN_PALE = "#22d3ee"
CLR_SAFE = "#22c55e"
CLR_WARN = "#f59e0b"
CLR_DANGER = "#ef4444"
CLR_CRITICAL = "#991b1b"

INDEX_META = {
    "Coastal Proximity": {
        "desc": "Estimated distance to coastline from water features and elevation",
        "color": CLR_OCEAN_DEEP,
    },
    "Erosion Risk": {
        "desc": "Soil erodibility, wind exposure, wave action, and slope gradient",
        "color": "#f97316",
    },
    "Sea Level Rise Exposure": {
        "desc": "Vulnerability to rising seas based on elevation and terrain flatness",
        "color": "#3b82f6",
    },
    "Storm Surge Risk": {
        "desc": "Susceptibility to storm-driven water inundation events",
        "color": CLR_DANGER,
    },
    "Marine Resources": {
        "desc": "Nearby marine and coastal assets including ports and fishing areas",
        "color": "#10b981",
    },
    "Flood Inundation": {
        "desc": "Combined flood risk from precipitation, drainage, and coastal proximity",
        "color": "#8b5cf6",
    },
    "Coastal Infrastructure": {
        "desc": "Buildings and roads exposed in low-elevation coastal zones",
        "color": CLR_WARN,
    },
}


# =============================================================================
# HELPERS
# =============================================================================

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _safe_mean(values: list) -> float:
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


def _classify(score: float) -> tuple:
    """Return (classification, color) for a 0-100 score."""
    if score >= 80:
        return "Critical", CLR_CRITICAL
    if score >= 60:
        return "High", CLR_DANGER
    if score >= 40:
        return "Moderate", CLR_WARN
    if score >= 20:
        return "Low", CLR_SAFE
    return "Minimal", "#64748b"


# =============================================================================
# COMPUTE
# =============================================================================

@st.cache_data(ttl=1800)
def compute_coastal_analysis(lat: float, lon: float) -> dict:
    """
    Compute comprehensive coastal and maritime risk analysis.

    Returns a dict with:
        overall_risk, classification, class_color,
        indices, coastal_features, elevation_profile, recommendations
    """
    # -- Fetch data sources ---------------------------------------------------
    weather = fetch_weather_data(lat, lon)
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.06, grid_size=8)
    water = fetch_water_features(lat, lon)
    soil = fetch_soil_data(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)

    # -- Extract weather ------------------------------------------------------
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}
    current = weather.get("current", {}) if isinstance(weather, dict) else {}

    wind_speed = current.get("wind_speed_10m", 0.0) or 0.0
    wind_gusts = current.get("wind_gusts_10m", 0.0) or 0.0
    precip_now = current.get("precipitation", 0.0) or 0.0
    humidity = current.get("relative_humidity_2m", 50) or 50

    precip_daily = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip_daily if p is not None]
    total_7d = sum(valid_precip[:7]) if valid_precip else 0.0
    daily_max_precip = max(valid_precip) if valid_precip else 0.0

    # -- Extract elevation / terrain ------------------------------------------
    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elev = [e for e in elevations if e is not None]
    center_elev = elev.get("center_elevation", 0.0) if isinstance(elev, dict) else 0.0
    min_elev = min(valid_elev) if valid_elev else 0.0
    max_elev = max(valid_elev) if valid_elev else 0.0
    avg_elev = sum(valid_elev) / len(valid_elev) if valid_elev else 0.0
    elev_range = max_elev - min_elev

    ns_profile = elev.get("ns_profile", []) if isinstance(elev, dict) else []
    ew_profile = elev.get("ew_profile", []) if isinstance(elev, dict) else []

    if len(valid_elev) > 1:
        mean_e = sum(valid_elev) / len(valid_elev)
        variance = sum((e - mean_e) ** 2 for e in valid_elev) / len(valid_elev)
        std_dev = math.sqrt(variance)
    else:
        variance = 0.0
        std_dev = 0.0

    grid_span_m = 0.06 * 111000
    slope_deg = math.degrees(math.atan2(elev_range, grid_span_m)) if grid_span_m > 0 else 0.0
    is_low_elevation = center_elev < 10

    # -- Extract soil data ----------------------------------------------------
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay_pct = _sv("clay") or 20.0
    sand_pct = _sv("sand") or 30.0
    silt_pct = _sv("silt") or 30.0
    soc = _sv("soc") or 10.0

    # -- Extract water features -----------------------------------------------
    elements = (water if isinstance(water, dict) else {}).get("elements", [])

    coastline_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("natural") == "coastline"
    )
    bay_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("natural") == "bay"
    )
    beach_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("natural") == "beach"
    )
    river_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("waterway") == "river"
    )
    reef_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("natural") in ("reef", "shoal")
    )
    water_body_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("natural") == "water"
    )
    port_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("amenity") in ("ferry_terminal",)
        or e.get("tags", {}).get("harbour") is not None
        or e.get("tags", {}).get("man_made") in ("pier", "breakwater")
    )
    fishing_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("leisure") == "fishing"
        or e.get("tags", {}).get("amenity") == "fish_market"
    )
    water_total = len(elements)

    coastal_indicator = coastline_count + bay_count + beach_count
    estuary_indicator = min(river_count, 3)
    water_density = min(water_total / 10.0, 1.0)

    # -- Extract infrastructure -----------------------------------------------
    infra_elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    building_count = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("building") is not None
    )
    road_count = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("highway") is not None
    )
    total_infra = building_count + road_count

    # =========================================================================
    # COASTAL INDICES (0-100)
    # =========================================================================

    # 1. Coastal Proximity
    prox = 0.0
    prox += min(40.0, coastal_indicator * 15.0)
    prox += min(20.0, estuary_indicator * 10.0)
    prox += min(20.0, water_density * 20.0)
    if is_low_elevation:
        prox += 20.0
    elif center_elev < 30:
        prox += 10.0
    coastal_proximity = _clamp(prox)

    # 2. Erosion Risk
    erosion = 0.0
    erosion += min(30.0, sand_pct / 60.0 * 30.0)
    erosion += min(20.0, wind_speed / 30.0 * 20.0)
    erosion += min(20.0, (coastal_indicator + water_body_count) / 5.0 * 20.0)
    erosion += min(15.0, slope_deg / 10.0 * 15.0)
    erosion += max(0.0, min(15.0, (40.0 - clay_pct) / 40.0 * 15.0))
    erosion_risk = _clamp(erosion)

    # 3. Sea Level Rise Exposure
    slr = 0.0
    if center_elev <= 1:
        slr += 50.0
    elif center_elev <= 3:
        slr += 40.0
    elif center_elev <= 5:
        slr += 30.0
    elif center_elev <= 10:
        slr += 20.0
    elif center_elev <= 20:
        slr += 10.0

    if std_dev < 3:
        slr += 25.0
    elif std_dev < 8:
        slr += 15.0
    elif std_dev < 15:
        slr += 8.0

    slr += min(15.0, coastal_proximity / 100.0 * 15.0)
    slr += min(10.0, water_density * 10.0)
    sea_level_rise = _clamp(slr)

    # 4. Storm Surge Risk
    surge = 0.0
    if is_low_elevation:
        surge += 30.0
    elif center_elev < 20:
        surge += 20.0
    elif center_elev < 50:
        surge += 10.0

    surge += min(25.0, coastal_proximity / 100.0 * 25.0)
    surge += min(20.0, wind_speed / 25.0 * 20.0)
    surge += min(15.0, daily_max_precip / 40.0 * 15.0)
    surge += min(10.0, wind_gusts / 50.0 * 10.0)
    storm_surge = _clamp(surge)

    # 5. Marine Resources
    marine = 0.0
    marine += min(25.0, reef_count * 12.5)
    marine += min(20.0, fishing_count * 10.0)
    marine += min(20.0, port_count * 10.0)
    marine += min(15.0, coastline_count * 7.5)
    marine += min(10.0, beach_count * 5.0)
    marine += min(10.0, water_total / 15.0 * 10.0)
    marine_resources = _clamp(marine)

    # 6. Flood Inundation
    flood = 0.0
    if center_elev < 5:
        flood += 25.0
    elif center_elev < 15:
        flood += 18.0
    elif center_elev < 30:
        flood += 10.0

    flood += min(20.0, total_7d / 80.0 * 20.0)
    flood += max(0.0, min(20.0, (60.0 - sand_pct) / 60.0 * 20.0))
    flood += min(20.0, coastal_proximity / 100.0 * 20.0)
    flood += min(15.0, (river_count + water_body_count) / 5.0 * 15.0)
    flood_inundation = _clamp(flood)

    # 7. Coastal Infrastructure
    infra_risk = 0.0
    if is_low_elevation and coastal_proximity > 40:
        infra_risk += min(35.0, building_count / 20.0 * 35.0)
        infra_risk += min(25.0, road_count / 15.0 * 25.0)
        infra_risk += min(20.0, coastal_proximity / 100.0 * 20.0)
        infra_risk += min(20.0, storm_surge / 100.0 * 20.0)
    elif center_elev < 30:
        infra_risk += min(20.0, building_count / 30.0 * 20.0)
        infra_risk += min(15.0, road_count / 20.0 * 15.0)
        infra_risk += min(10.0, coastal_proximity / 100.0 * 10.0)
    coastal_infrastructure = _clamp(infra_risk)

    indices = {
        "Coastal Proximity": round(coastal_proximity, 1),
        "Erosion Risk": round(erosion_risk, 1),
        "Sea Level Rise Exposure": round(sea_level_rise, 1),
        "Storm Surge Risk": round(storm_surge, 1),
        "Marine Resources": round(marine_resources, 1),
        "Flood Inundation": round(flood_inundation, 1),
        "Coastal Infrastructure": round(coastal_infrastructure, 1),
    }

    # -- Weighted overall risk ------------------------------------------------
    weights = {
        "Coastal Proximity": 1.0,
        "Erosion Risk": 2.0,
        "Sea Level Rise Exposure": 2.5,
        "Storm Surge Risk": 2.5,
        "Marine Resources": 0.5,
        "Flood Inundation": 2.0,
        "Coastal Infrastructure": 1.5,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(indices[k] * weights[k] for k in indices)
    overall_risk = round(weighted_sum / total_weight, 1)

    classification, class_color = _classify(overall_risk)

    # -- Coastal features summary ---------------------------------------------
    coastal_features = {
        "coastlines": coastline_count,
        "bays": bay_count,
        "beaches": beach_count,
        "rivers": river_count,
        "reefs": reef_count,
        "ports": port_count,
        "fishing_areas": fishing_count,
        "water_bodies": water_body_count,
        "total_water_features": water_total,
        "buildings_nearby": building_count,
        "roads_nearby": road_count,
    }

    # -- Elevation profile for chart ------------------------------------------
    elevation_profile = {
        "center_elevation": round(center_elev, 1),
        "min_elevation": round(min_elev, 1),
        "max_elevation": round(max_elev, 1),
        "avg_elevation": round(avg_elev, 1),
        "elevation_range": round(elev_range, 1),
        "std_deviation": round(std_dev, 1),
        "slope_deg": round(slope_deg, 2),
        "ns_profile": ns_profile,
        "ew_profile": ew_profile,
    }

    # -- Recommendations ------------------------------------------------------
    recommendations = []

    if storm_surge >= 70:
        recommendations.append(
            "STORM SURGE ALERT: Extremely high storm surge risk. "
            "Implement coastal evacuation plans and reinforce sea walls."
        )
    elif storm_surge >= 40:
        recommendations.append(
            "Storm Surge Advisory: Significant surge potential. "
            "Maintain emergency response readiness and inspect coastal defences."
        )

    if erosion_risk >= 70:
        recommendations.append(
            "EROSION WARNING: Severe coastal erosion risk detected. "
            "Install breakwaters, revetments, or beach nourishment programs."
        )
    elif erosion_risk >= 40:
        recommendations.append(
            "Erosion Advisory: Moderate erosion susceptibility. "
            "Monitor shoreline retreat and plant coastal vegetation for stabilisation."
        )

    if sea_level_rise >= 70:
        recommendations.append(
            "SEA LEVEL RISE CRITICAL: Location is highly exposed to sea level rise. "
            "Plan managed retreat or elevate critical infrastructure above projected levels."
        )
    elif sea_level_rise >= 40:
        recommendations.append(
            "Sea Level Rise Advisory: Low-lying terrain faces long-term inundation risk. "
            "Incorporate climate projections into land-use planning."
        )

    if flood_inundation >= 70:
        recommendations.append(
            "FLOOD INUNDATION WARNING: High coastal flood risk from combined factors. "
            "Install flood barriers and improve drainage capacity immediately."
        )
    elif flood_inundation >= 40:
        recommendations.append(
            "Flood Advisory: Moderate inundation potential. "
            "Ensure storm-water systems are maintained and clear of debris."
        )

    if coastal_infrastructure >= 60:
        recommendations.append(
            "INFRASTRUCTURE AT RISK: Significant built environment in the coastal hazard zone. "
            "Conduct vulnerability assessments and prioritise protective measures."
        )

    if not recommendations:
        recommendations.append(
            "Coastal risk is currently low. Continue routine monitoring "
            "of shoreline conditions and weather forecasts."
        )

    return {
        "overall_risk": overall_risk,
        "classification": classification,
        "class_color": class_color,
        "indices": indices,
        "coastal_features": coastal_features,
        "elevation_profile": elevation_profile,
        "recommendations": recommendations,
    }


# =============================================================================
# CHART BUILDERS
# =============================================================================

def _build_radar_chart(indices: dict) -> go.Figure:
    """Radar chart of all 7 coastal indices."""
    labels = list(indices.keys())
    values = list(indices.values())
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(8,145,178,0.15)",
        line={"color": CLR_OCEAN_MID, "width": 2.5},
        marker={"size": 7, "color": CLR_OCEAN_LIGHT},
        name="Coastal Indices",
        hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
    ))

    fig.update_layout(
        title={"text": "Coastal Risk Radar", "font": {"color": CLR_TEXT, "size": 16}},
        height=400,
        margin=dict(l=70, r=70, t=60, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        polar={
            "bgcolor": CLR_SURFACE,
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "gridcolor": "#2a3550",
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
            },
            "angularaxis": {
                "gridcolor": "#2a3550",
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
            },
        },
        showlegend=False,
    )
    return fig


def _build_elevation_profile(profile: dict) -> go.Figure:
    """Elevation profile with sea level reference line."""
    ns = profile.get("ns_profile", [])
    ew = profile.get("ew_profile", [])

    fig = go.Figure()

    if ns:
        ns_x = [p.get("lat", 0) for p in ns]
        ns_y = [p.get("elevation", 0) for p in ns]
        fig.add_trace(go.Scatter(
            x=ns_x, y=ns_y,
            mode="lines+markers",
            name="N-S Profile",
            line={"color": CLR_OCEAN_LIGHT, "width": 2.5},
            marker={"size": 5, "color": CLR_OCEAN_LIGHT},
            fill="tozeroy",
            fillcolor="rgba(6,182,212,0.10)",
            hovertemplate="Lat: %{x:.4f}<br>Elev: %{y:.0f} m<extra></extra>",
        ))

    if ew:
        ew_x = [p.get("lon", 0) for p in ew]
        ew_y = [p.get("elevation", 0) for p in ew]
        fig.add_trace(go.Scatter(
            x=ew_x, y=ew_y,
            mode="lines+markers",
            name="E-W Profile",
            line={"color": CLR_OCEAN_PALE, "width": 2.5},
            marker={"size": 5, "color": CLR_OCEAN_PALE},
            fill="tozeroy",
            fillcolor="rgba(34,211,238,0.08)",
            xaxis="x2",
            hovertemplate="Lon: %{x:.4f}<br>Elev: %{y:.0f} m<extra></extra>",
        ))

    # Sea level reference line
    fig.add_hline(
        y=0, line_dash="dash", line_color="#3b82f6", line_width=2,
        annotation_text="Sea Level",
        annotation_font={"color": "#3b82f6", "size": 12},
        annotation_position="bottom right",
    )

    fig.update_layout(
        title={"text": "Coastal Elevation Profile", "font": {"color": CLR_TEXT, "size": 16}},
        height=340,
        margin=dict(l=50, r=50, t=50, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        xaxis={
            "title": "Latitude (N-S)",
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title_font": {"color": CLR_TEXT_SEC},
        },
        xaxis2={
            "title": "Longitude (E-W)",
            "overlaying": "x",
            "side": "top",
            "tickfont": {"color": CLR_OCEAN_PALE},
            "title_font": {"color": CLR_OCEAN_PALE},
            "showgrid": False,
        },
        yaxis={
            "title": "Elevation (m)",
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title_font": {"color": CLR_TEXT_SEC},
        },
        legend={
            "font": {"color": CLR_TEXT_SEC},
            "bgcolor": "rgba(0,0,0,0.3)",
            "bordercolor": CLR_BORDER,
            "borderwidth": 1,
        },
    )
    return fig


def _build_comparison_bars(indices: dict) -> go.Figure:
    """Horizontal bar chart comparing all coastal risk indices."""
    names = list(indices.keys())
    values = list(indices.values())
    colors = [INDEX_META.get(n, {}).get("color", CLR_OCEAN_MID) for n in names]

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.0f}" for v in values],
        textposition="auto",
        textfont={"color": CLR_TEXT, "size": 12},
        hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
    ))

    fig.update_layout(
        title={"text": "Risk Index Comparison", "font": {"color": CLR_TEXT, "size": 16}},
        height=340,
        margin=dict(l=160, r=40, t=50, b=30),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        xaxis={
            "title": "Score (0-100)",
            "range": [0, 105],
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title_font": {"color": CLR_TEXT_SEC},
        },
        yaxis={
            "tickfont": {"color": CLR_TEXT_SEC},
            "autorange": "reversed",
        },
    )
    return fig


# =============================================================================
# RENDER
# =============================================================================

def render_coastal_analysis_tab():
    """Render the Coastal Intelligence AI tab in the Streamlit UI."""

    # -- Header ---------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Coastal Intelligence AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Comprehensive coastal and maritime risk analysis covering erosion,
                sea level rise, storm surge, marine resources, and infrastructure
                vulnerability.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location selector ----------------------------------------------------
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="ca_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="ca_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="ca_lon",
        )

    run_btn = st.button(
        "Analyze Coastal Risk",
        type="primary",
        key="ca_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Analyze Coastal Risk** to begin.")
        return

    # -- Run computation ------------------------------------------------------
    with st.spinner("Fetching elevation, weather, soil, water, and infrastructure data..."):
        result = compute_coastal_analysis(lat, lon)

    overall = result["overall_risk"]
    classification = result["classification"]
    class_color = result["class_color"]
    indices = result["indices"]
    features = result["coastal_features"]
    elev_profile = result["elevation_profile"]
    recs = result["recommendations"]

    # -- Overall risk banner --------------------------------------------------
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
                        Overall Coastal Risk Score
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
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Elevation: {elev_profile['center_elevation']:.0f} m<br>
                        Elev. Range: {elev_profile['elevation_range']:.0f} m<br>
                        Water Features: {features['total_water_features']}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Index cards -----------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Coastal Risk Indices
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    index_keys = list(indices.keys())
    row1_keys = index_keys[:4]
    row2_keys = index_keys[4:]

    cols1 = st.columns(len(row1_keys))
    for col, key in zip(cols1, row1_keys):
        score_val = indices[key]
        s_class, s_color = _classify(score_val)
        meta = INDEX_META.get(key, {"desc": "", "color": CLR_OCEAN_MID})
        bar_w = max(3, score_val)
        with col:
            st.markdown(
                f"""
                <div style="background:{CLR_SURFACE};border:1px solid {s_color}44;
                            border-radius:10px;padding:16px;text-align:center;
                            min-height:190px;">
                    <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                        {escape(key)}
                    </div>
                    <div style="font-size:30px;font-weight:700;color:{s_color};">
                        {score_val:.0f}
                    </div>
                    <div style="font-size:12px;color:{s_color};font-weight:600;
                                margin-bottom:8px;">
                        {escape(s_class)}
                    </div>
                    <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                margin:8px 0;">
                        <div style="background:{s_color};width:{bar_w}%;
                                    height:6px;border-radius:4px;"></div>
                    </div>
                    <div style="font-size:10px;color:{CLR_TEXT_SEC};margin-top:6px;">
                        {escape(meta['desc'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if row2_keys:
        cols2 = st.columns(len(row2_keys))
        for col, key in zip(cols2, row2_keys):
            score_val = indices[key]
            s_class, s_color = _classify(score_val)
            meta = INDEX_META.get(key, {"desc": "", "color": CLR_OCEAN_MID})
            bar_w = max(3, score_val)
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {s_color}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:190px;">
                        <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                            {escape(key)}
                        </div>
                        <div style="font-size:30px;font-weight:700;color:{s_color};">
                            {score_val:.0f}
                        </div>
                        <div style="font-size:12px;color:{s_color};font-weight:600;
                                    margin-bottom:8px;">
                            {escape(s_class)}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                    margin:8px 0;">
                            <div style="background:{s_color};width:{bar_w}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:10px;color:{CLR_TEXT_SEC};margin-top:6px;">
                            {escape(meta['desc'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Radar chart ----------------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    radar_fig = _build_radar_chart(indices)
    st.plotly_chart(radar_fig, use_container_width=True, key="ca_radar")

    # -- Elevation profile chart ----------------------------------------------
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    elev_fig = _build_elevation_profile(elev_profile)
    st.plotly_chart(elev_fig, use_container_width=True, key="ca_elev")

    # -- Elevation metrics ----------------------------------------------------
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        st.metric("Center Elevation", f"{elev_profile['center_elevation']:.0f} m")
    with e2:
        st.metric("Min Elevation", f"{elev_profile['min_elevation']:.0f} m")
    with e3:
        st.metric("Max Elevation", f"{elev_profile['max_elevation']:.0f} m")
    with e4:
        st.metric("Slope", f"{elev_profile['slope_deg']:.1f} deg")

    # -- Coastal features summary ---------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Coastal Features Summary
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.metric("Coastlines", f"{features['coastlines']}")
    with f2:
        st.metric("Bays", f"{features['bays']}")
    with f3:
        st.metric("Beaches", f"{features['beaches']}")
    with f4:
        st.metric("Rivers", f"{features['rivers']}")

    f5, f6, f7, f8 = st.columns(4)
    with f5:
        st.metric("Reefs", f"{features['reefs']}")
    with f6:
        st.metric("Ports / Piers", f"{features['ports']}")
    with f7:
        st.metric("Buildings Nearby", f"{features['buildings_nearby']}")
    with f8:
        st.metric("Roads Nearby", f"{features['roads_nearby']}")

    # -- Risk comparison horizontal bars --------------------------------------
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    bar_fig = _build_comparison_bars(indices)
    st.plotly_chart(bar_fig, use_container_width=True, key="ca_bars")

    # -- Recommendations ------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Recommendations &amp; Advisories
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for rec in recs:
        is_alert = any(
            rec.startswith(kw)
            for kw in ("STORM SURGE ALERT", "EROSION WARNING",
                        "SEA LEVEL RISE CRITICAL", "FLOOD INUNDATION WARNING",
                        "INFRASTRUCTURE AT RISK")
        )
        card_border = CLR_DANGER if is_alert else CLR_BORDER
        icon_color = CLR_DANGER if is_alert else CLR_OCEAN_MID

        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {card_border};
                        border-left:4px solid {card_border};
                        border-radius:8px;padding:14px 18px;margin:8px 0;">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="color:{icon_color};font-size:18px;margin-top:2px;">
                        &#9679;
                    </span>
                    <span style="color:{CLR_TEXT};font-size:14px;line-height:1.5;">
                        {escape(rec)}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Footer ---------------------------------------------------------------
    st.markdown(
        f"""
        <div style="text-align:center;padding:16px;margin-top:20px;
                    color:{CLR_TEXT_SEC};font-size:12px;">
            Coastal Intelligence powered by Open-Meteo, Open-Elevation,
            ISRIC SoilGrids, and OpenStreetMap.
            Estimates are indicative and should complement professional
            coastal engineering assessments.
        </div>
        """,
        unsafe_allow_html=True,
    )
