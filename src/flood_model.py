"""
Flood Risk Modeling AI module for TerraScout AI.
Provides detailed flood risk analysis using terrain, precipitation,
water features, and soil data to compute inundation probability,
drainage capacity, and estimated flood depth.
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

# Flood-specific palette (blue shades)
CLR_FLOOD_DEEP = "#1e40af"
CLR_FLOOD_MID = "#3b82f6"
CLR_FLOOD_LIGHT = "#60a5fa"
CLR_FLOOD_PALE = "#93c5fd"
CLR_SAFE = "#22c55e"
CLR_WARN = "#f59e0b"
CLR_DANGER = "#ef4444"
CLR_CRITICAL = "#991b1b"

COMPONENT_META = {
    "Precipitation Risk": {
        "desc": "Recent and forecast precipitation intensity",
        "icon": "tint",
    },
    "Terrain Vulnerability": {
        "desc": "Low elevation, flat terrain, and valley position",
        "icon": "mountain",
    },
    "Soil Runoff Potential": {
        "desc": "Clay content and low infiltration capacity",
        "icon": "leaf",
    },
    "Water Proximity Risk": {
        "desc": "Nearby rivers, streams, and lakes",
        "icon": "water",
    },
    "Drainage Capacity": {
        "desc": "Slope steepness and soil permeability (inverted: high = poor drainage)",
        "icon": "filter",
    },
}


# =============================================================================
# HELPERS
# =============================================================================

def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def _safe_mean(values: list) -> float:
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


def _safe_max(values: list, default: float = 0.0) -> float:
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return default
    return max(cleaned)


def _risk_color(score: float) -> str:
    if score > 8:
        return CLR_CRITICAL
    if score > 6:
        return CLR_DANGER
    if score >= 3:
        return CLR_WARN
    return CLR_SAFE


def _risk_class(score: float) -> str:
    if score > 8:
        return "Critical"
    if score > 6:
        return "High"
    if score >= 3:
        return "Moderate"
    if score >= 1:
        return "Low"
    return "Minimal"


# =============================================================================
# COMPUTE
# =============================================================================

@st.cache_data(ttl=1800)
def compute_flood_risk(lat: float, lon: float) -> dict:
    """
    Compute comprehensive flood risk for a location.

    Returns a dict with:
        overall_risk, risk_class, risk_color,
        component_scores, precipitation_analysis, terrain_analysis,
        recommendations, flood_depth_estimate_cm
    """
    # -- Fetch data sources ---------------------------------------------------
    weather = fetch_weather_data(lat, lon)
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.05, grid_size=8)
    water = fetch_water_features(lat, lon)
    soil = fetch_soil_data(lat, lon)

    # -- Extract weather / precipitation --------------------------------------
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}
    current = weather.get("current", {}) if isinstance(weather, dict) else {}

    precip_daily = daily.get("precipitation_sum", [])
    dates = daily.get("time", [])
    valid_precip = [p for p in precip_daily if p is not None]

    daily_max_precip = max(valid_precip) if valid_precip else 0.0
    total_7d = sum(valid_precip[:7]) if valid_precip else 0.0
    total_3d = sum(valid_precip[:3]) if valid_precip else 0.0
    current_precip = current.get("precipitation", 0.0) or 0.0
    humidity = current.get("relative_humidity_2m", 50) or 50

    # Build cumulative series
    cumulative = []
    running = 0.0
    for p in valid_precip:
        running += p
        cumulative.append(round(running, 1))

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

    # Elevation variance (low variance = flat = poor drainage)
    if len(valid_elev) > 1:
        mean_e = sum(valid_elev) / len(valid_elev)
        variance = sum((e - mean_e) ** 2 for e in valid_elev) / len(valid_elev)
        std_dev = math.sqrt(variance)
    else:
        variance = 0.0
        std_dev = 0.0

    # Slope estimate (degrees) from elevation range over ~11 km grid
    grid_span_m = 0.05 * 111000  # approx meters for radius_deg=0.05
    slope_deg = math.degrees(math.atan2(elev_range, grid_span_m)) if grid_span_m > 0 else 0.0

    # Valley detection: center is lower than average
    is_valley = center_elev < (avg_elev - std_dev * 0.5) if std_dev > 0 else False

    # -- Extract soil data ----------------------------------------------------
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _soil_val(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay_pct = _soil_val("clay") or 20.0
    sand_pct = _soil_val("sand") or 30.0
    silt_pct = _soil_val("silt") or 30.0
    soc = _soil_val("soc") or 10.0

    # -- Extract water features -----------------------------------------------
    elements = water.get("elements", []) if isinstance(water, dict) else []
    rivers = sum(
        1 for e in elements
        if e.get("tags", {}).get("waterway") in ("river", "stream", "canal")
    )
    lakes = sum(
        1 for e in elements
        if e.get("tags", {}).get("natural") == "water"
    )
    springs = sum(
        1 for e in elements
        if e.get("tags", {}).get("natural") == "spring"
    )
    water_total = len(elements)

    # =========================================================================
    # COMPONENT SCORES (0-10)
    # =========================================================================

    # 1. Precipitation Risk
    precip_score = 0.0
    precip_score += min(4.0, daily_max_precip / 25.0 * 4.0)
    precip_score += min(3.0, total_3d / 50.0 * 3.0)
    precip_score += min(2.0, total_7d / 100.0 * 2.0)
    precip_score += min(1.0, current_precip / 10.0)
    precip_score = _clamp(precip_score)

    # 2. Terrain Vulnerability (low + flat + valley = high risk)
    terrain_score = 0.0
    if center_elev < 10:
        terrain_score += 4.0
    elif center_elev < 50:
        terrain_score += 3.0
    elif center_elev < 200:
        terrain_score += 2.0
    elif center_elev < 500:
        terrain_score += 1.0

    # Flat terrain penalty
    if std_dev < 5:
        terrain_score += 3.0
    elif std_dev < 15:
        terrain_score += 2.0
    elif std_dev < 30:
        terrain_score += 1.0

    if is_valley:
        terrain_score += 3.0
    terrain_score = _clamp(terrain_score)

    # 3. Soil Runoff Potential (high clay = poor infiltration)
    soil_score = 0.0
    soil_score += min(4.0, clay_pct / 40.0 * 4.0)
    soil_score += max(0.0, min(3.0, (60 - sand_pct) / 60.0 * 3.0))
    soil_score += max(0.0, min(2.0, (20 - soc) / 20.0 * 2.0))
    if humidity > 80:
        soil_score += 1.0
    soil_score = _clamp(soil_score)

    # 4. Water Proximity Risk
    water_score = 0.0
    water_score += min(4.0, rivers / 3.0 * 4.0)
    water_score += min(3.0, lakes / 2.0 * 3.0)
    water_score += min(2.0, springs / 3.0 * 2.0)
    water_score += min(1.0, water_total / 10.0)
    water_score = _clamp(water_score)

    # 5. Drainage Capacity (inverted: high score = poor drainage = more risk)
    drainage_score = 10.0  # start at worst
    drainage_score -= min(4.0, slope_deg / 5.0 * 4.0)  # steeper slope = better
    drainage_score -= min(3.0, sand_pct / 60.0 * 3.0)  # more sand = better
    drainage_score -= min(2.0, soc / 20.0 * 2.0)        # organic matter helps
    drainage_score -= min(1.0, elev_range / 100.0)       # more relief = better
    drainage_score = _clamp(drainage_score)

    component_scores = {
        "Precipitation Risk": round(precip_score, 1),
        "Terrain Vulnerability": round(terrain_score, 1),
        "Soil Runoff Potential": round(soil_score, 1),
        "Water Proximity Risk": round(water_score, 1),
        "Drainage Capacity": round(drainage_score, 1),
    }

    # -- Weighted overall risk ------------------------------------------------
    weights = {
        "Precipitation Risk": 2.5,
        "Terrain Vulnerability": 2.0,
        "Soil Runoff Potential": 1.5,
        "Water Proximity Risk": 2.0,
        "Drainage Capacity": 2.0,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(component_scores[k] * weights[k] for k in component_scores)
    overall_risk = round(weighted_sum / total_weight, 1)

    # -- Flood return period estimate (rough) ---------------------------------
    if overall_risk > 8:
        return_period = "< 10 years"
    elif overall_risk > 6:
        return_period = "10 - 25 years"
    elif overall_risk >= 3:
        return_period = "25 - 100 years"
    else:
        return_period = "> 100 years"

    # -- Flood depth estimate (cm) -------------------------------------------
    runoff_coeff = 0.3 + (clay_pct / 100.0) * 0.4
    depth_cm = total_7d * runoff_coeff * (1.0 + (water_total / 20.0))
    if is_valley:
        depth_cm *= 1.5
    if center_elev < 50:
        depth_cm *= 1.3
    depth_cm = round(min(depth_cm, 500), 1)

    # -- Precipitation analysis dict ------------------------------------------
    precipitation_analysis = {
        "dates": dates[:len(valid_precip)],
        "daily_values": [round(p, 1) for p in valid_precip],
        "cumulative": cumulative,
        "daily_max": round(daily_max_precip, 1),
        "total_3d": round(total_3d, 1),
        "total_7d": round(total_7d, 1),
        "current_mm": round(current_precip, 1),
    }

    # -- Terrain analysis dict ------------------------------------------------
    terrain_analysis = {
        "center_elevation": round(center_elev, 1),
        "min_elevation": round(min_elev, 1),
        "max_elevation": round(max_elev, 1),
        "elevation_range": round(elev_range, 1),
        "std_deviation": round(std_dev, 1),
        "slope_deg": round(slope_deg, 2),
        "is_valley": is_valley,
        "ns_profile": ns_profile,
        "ew_profile": ew_profile,
    }

    # -- Recommendations ------------------------------------------------------
    recommendations = []
    if precip_score >= 7:
        recommendations.append(
            "FLOOD ALERT: Heavy precipitation detected or forecast. "
            "Activate flood response plans and monitor drainage systems."
        )
    elif precip_score >= 4:
        recommendations.append(
            "Precipitation Advisory: Significant rainfall expected. "
            "Inspect drainage channels and prepare sandbag supplies."
        )

    if terrain_score >= 7:
        recommendations.append(
            "TERRAIN WARNING: Location is in a low-lying valley with flat terrain. "
            "High vulnerability to water accumulation. Consider permanent flood barriers."
        )
    elif terrain_score >= 4:
        recommendations.append(
            "Terrain Advisory: Moderately vulnerable topography. "
            "Ensure surface grading directs water away from structures."
        )

    if soil_score >= 7:
        recommendations.append(
            "SOIL WARNING: Clay-heavy soil with poor infiltration. "
            "Surface runoff will be severe. Install French drains or retention basins."
        )
    elif soil_score >= 4:
        recommendations.append(
            "Soil Advisory: Limited soil absorption capacity. "
            "Improve ground permeability with organic amendments or permeable surfaces."
        )

    if water_score >= 7:
        recommendations.append(
            "WATER PROXIMITY ALERT: Multiple rivers and water bodies nearby. "
            "Monitor water levels closely. Maintain flood insurance coverage."
        )
    elif water_score >= 4:
        recommendations.append(
            "Water Advisory: Proximity to water features increases risk. "
            "Keep emergency supplies and evacuation routes planned."
        )

    if drainage_score >= 7:
        recommendations.append(
            "DRAINAGE CRITICAL: Very poor natural drainage due to flat terrain and "
            "impermeable soil. Install pumping stations or engineered drainage."
        )
    elif drainage_score >= 4:
        recommendations.append(
            "Drainage Advisory: Below-average natural drainage. "
            "Maintain clear storm drains and consider rain gardens."
        )

    if not recommendations:
        recommendations.append(
            "Flood risk is currently low. Continue routine monitoring "
            "and maintain drainage infrastructure."
        )

    return {
        "overall_risk": overall_risk,
        "risk_class": _risk_class(overall_risk),
        "risk_color": _risk_color(overall_risk),
        "component_scores": component_scores,
        "precipitation_analysis": precipitation_analysis,
        "terrain_analysis": terrain_analysis,
        "recommendations": recommendations,
        "flood_depth_estimate_cm": depth_cm,
        "return_period": return_period,
        "soil_summary": {
            "clay": round(clay_pct, 1),
            "sand": round(sand_pct, 1),
            "silt": round(silt_pct, 1),
            "organic_carbon": round(soc, 1),
        },
        "water_summary": {
            "rivers": rivers,
            "lakes": lakes,
            "springs": springs,
            "total": water_total,
        },
    }


# =============================================================================
# CHART BUILDERS
# =============================================================================

def _build_gauge(score: float, color: str) -> go.Figure:
    """Plotly gauge indicator for overall flood risk 0-10."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 52, "color": CLR_TEXT}},
        title={
            "text": "Overall Flood Risk",
            "font": {"size": 18, "color": CLR_TEXT_SEC},
        },
        gauge={
            "axis": {
                "range": [0, 10],
                "tickwidth": 2,
                "tickcolor": CLR_TEXT_SEC,
                "tickfont": {"color": CLR_TEXT_SEC},
            },
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": CLR_SURFACE,
            "borderwidth": 2,
            "bordercolor": CLR_BORDER,
            "steps": [
                {"range": [0, 3], "color": "rgba(34,197,94,0.12)"},
                {"range": [3, 6], "color": "rgba(245,158,11,0.12)"},
                {"range": [6, 8], "color": "rgba(59,130,246,0.15)"},
                {"range": [8, 10], "color": "rgba(30,64,175,0.20)"},
            ],
            "threshold": {
                "line": {"color": "#ffffff", "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=30, r=30, t=50, b=20),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
    )
    return fig


def _build_precip_chart(precip: dict) -> go.Figure:
    """Daily precipitation bars + cumulative line chart."""
    dates = precip.get("dates", [])
    daily_vals = precip.get("daily_values", [])
    cumulative = precip.get("cumulative", [])

    fig = go.Figure()

    if dates and daily_vals:
        fig.add_trace(go.Bar(
            x=dates,
            y=daily_vals,
            name="Daily (mm)",
            marker_color=CLR_FLOOD_MID,
            opacity=0.7,
            yaxis="y",
            hovertemplate="Daily: %{y:.1f} mm<extra></extra>",
        ))

    if dates and cumulative:
        fig.add_trace(go.Scatter(
            x=dates[:len(cumulative)],
            y=cumulative,
            name="Cumulative (mm)",
            mode="lines+markers",
            line={"color": CLR_FLOOD_DEEP, "width": 3},
            marker={"size": 5, "color": CLR_FLOOD_DEEP},
            yaxis="y2",
            hovertemplate="Cumulative: %{y:.1f} mm<extra></extra>",
        ))

    fig.update_layout(
        title={"text": "Precipitation Analysis", "font": {"color": CLR_TEXT, "size": 16}},
        height=350,
        margin=dict(l=50, r=50, t=50, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        xaxis={
            "title": "Date",
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title_font": {"color": CLR_TEXT_SEC},
        },
        yaxis={
            "title": "Daily (mm)",
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title_font": {"color": CLR_TEXT_SEC},
            "side": "left",
        },
        yaxis2={
            "title": "Cumulative (mm)",
            "overlaying": "y",
            "side": "right",
            "tickfont": {"color": CLR_FLOOD_DEEP},
            "title_font": {"color": CLR_FLOOD_DEEP},
            "showgrid": False,
        },
        legend={
            "font": {"color": CLR_TEXT_SEC},
            "bgcolor": "rgba(0,0,0,0.3)",
            "bordercolor": CLR_BORDER,
            "borderwidth": 1,
        },
        barmode="overlay",
        hovermode="x unified",
    )
    return fig


def _build_terrain_chart(terrain: dict) -> go.Figure:
    """Elevation profile visualization (N-S and E-W)."""
    ns = terrain.get("ns_profile", [])
    ew = terrain.get("ew_profile", [])

    fig = go.Figure()

    if ns:
        ns_lats = [p.get("lat", 0) for p in ns]
        ns_elevs = [p.get("elevation", 0) for p in ns]
        fig.add_trace(go.Scatter(
            x=ns_lats,
            y=ns_elevs,
            mode="lines+markers",
            name="N-S Profile",
            line={"color": CLR_FLOOD_LIGHT, "width": 2.5},
            marker={"size": 5, "color": CLR_FLOOD_LIGHT},
            fill="tozeroy",
            fillcolor="rgba(96,165,250,0.1)",
            hovertemplate="Lat: %{x:.4f}<br>Elev: %{y:.0f} m<extra></extra>",
        ))

    if ew:
        ew_lons = [p.get("lon", 0) for p in ew]
        ew_elevs = [p.get("elevation", 0) for p in ew]
        fig.add_trace(go.Scatter(
            x=ew_lons,
            y=ew_elevs,
            mode="lines+markers",
            name="E-W Profile",
            line={"color": CLR_FLOOD_PALE, "width": 2.5},
            marker={"size": 5, "color": CLR_FLOOD_PALE},
            fill="tozeroy",
            fillcolor="rgba(147,197,253,0.1)",
            xaxis="x2",
            hovertemplate="Lon: %{x:.4f}<br>Elev: %{y:.0f} m<extra></extra>",
        ))

    fig.update_layout(
        title={"text": "Terrain Drainage Profile", "font": {"color": CLR_TEXT, "size": 16}},
        height=320,
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
            "tickfont": {"color": CLR_FLOOD_PALE},
            "title_font": {"color": CLR_FLOOD_PALE},
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


def _build_radar_chart(scores: dict) -> go.Figure:
    """Radar chart of the 5 flood risk components."""
    labels = list(scores.keys())
    values = list(scores.values())
    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(59,130,246,0.15)",
        line={"color": CLR_FLOOD_MID, "width": 2.5},
        marker={"size": 7, "color": CLR_FLOOD_MID},
        name="Risk Factors",
        hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
    ))

    fig.update_layout(
        title={"text": "Risk Factor Radar", "font": {"color": CLR_TEXT, "size": 16}},
        height=380,
        margin=dict(l=60, r=60, t=60, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        polar={
            "bgcolor": CLR_SURFACE,
            "radialaxis": {
                "visible": True,
                "range": [0, 10],
                "gridcolor": "#2a3550",
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
            },
            "angularaxis": {
                "gridcolor": "#2a3550",
                "tickfont": {"color": CLR_TEXT_SEC, "size": 11},
            },
        },
        showlegend=False,
    )
    return fig


# =============================================================================
# RENDER
# =============================================================================

def render_flood_model_tab():
    """Render the Flood Risk Modeling tab in the Streamlit UI."""

    # -- Header ---------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Flood Risk Modeling AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Detailed flood risk analysis using terrain, precipitation,
                water features, and soil data. Computes inundation probability
                and estimated flood depth.
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
            key="fm_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="fm_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="fm_lon",
        )

    run_btn = st.button(
        "Model Flood Risk",
        type="primary",
        key="fm_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Model Flood Risk** to begin.")
        return

    # -- Run computation ------------------------------------------------------
    with st.spinner("Fetching terrain, weather, soil, and water data..."):
        result = compute_flood_risk(lat, lon)

    overall = result["overall_risk"]
    rc = result["risk_class"]
    r_color = result["risk_color"]
    comp = result["component_scores"]
    precip_a = result["precipitation_analysis"]
    terrain_a = result["terrain_analysis"]
    recs = result["recommendations"]
    depth_cm = result["flood_depth_estimate_cm"]
    ret_period = result["return_period"]
    soil_s = result["soil_summary"]
    water_s = result["water_summary"]

    # -- Overall risk banner --------------------------------------------------
    depth_str = f"{depth_cm:.0f}" if depth_cm >= 1 else "< 1"
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{r_color}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {r_color}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                        flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};
                                 text-transform:uppercase;letter-spacing:1px;">
                        Overall Flood Risk
                    </span>
                    <h1 style="margin:4px 0;color:{r_color};font-size:42px;">
                        {overall}/10
                    </h1>
                    <span style="font-size:18px;color:{r_color};font-weight:600;">
                        {escape(rc)}
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Est. Flood Depth: {depth_str} cm<br>
                        Return Period: {escape(ret_period)}<br>
                        Elevation: {terrain_a['center_elevation']:.0f} m
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Gauge chart ----------------------------------------------------------
    gauge_fig = _build_gauge(overall, r_color)
    st.plotly_chart(gauge_fig, use_container_width=True, key="fm_gauge")

    # -- Component score cards ------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Risk Component Breakdown
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    comp_keys = list(comp.keys())
    cols = st.columns(len(comp_keys))
    for col, key in zip(cols, comp_keys):
        score_val = comp[key]
        s_color = _risk_color(score_val)
        s_class = _risk_class(score_val)
        meta = COMPONENT_META.get(key, {"desc": "", "icon": "info"})
        bar_w = max(5, score_val / 10 * 100)
        with col:
            st.markdown(
                f"""
                <div style="background:{CLR_SURFACE};border:1px solid {s_color}44;
                            border-radius:10px;padding:16px;text-align:center;
                            min-height:190px;">
                    <div style="font-size:12px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                        {escape(key)}
                    </div>
                    <div style="font-size:32px;font-weight:700;color:{s_color};">
                        {score_val}
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

    # -- Precipitation chart --------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    precip_fig = _build_precip_chart(precip_a)
    st.plotly_chart(precip_fig, use_container_width=True, key="fm_precip")

    # -- Summary metrics row --------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Daily Max Precip", f"{precip_a['daily_max']:.1f} mm")
    with m2:
        st.metric("3-Day Total", f"{precip_a['total_3d']:.1f} mm")
    with m3:
        st.metric("7-Day Total", f"{precip_a['total_7d']:.1f} mm")
    with m4:
        st.metric("Current Precip", f"{precip_a['current_mm']:.1f} mm")

    # -- Terrain chart --------------------------------------------------------
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    terrain_fig = _build_terrain_chart(terrain_a)
    st.plotly_chart(terrain_fig, use_container_width=True, key="fm_terrain")

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Center Elevation", f"{terrain_a['center_elevation']:.0f} m")
    with t2:
        st.metric("Elev. Range", f"{terrain_a['elevation_range']:.0f} m")
    with t3:
        st.metric("Slope", f"{terrain_a['slope_deg']:.1f} deg")
    with t4:
        valley_txt = "Yes" if terrain_a["is_valley"] else "No"
        st.metric("Valley Position", valley_txt)

    # -- Radar chart ----------------------------------------------------------
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    radar_fig = _build_radar_chart(comp)
    st.plotly_chart(radar_fig, use_container_width=True, key="fm_radar")

    # -- Soil and water summary -----------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Soil &amp; Hydrology Summary
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Clay", f"{soil_s['clay']:.0f} %")
    with s2:
        st.metric("Sand", f"{soil_s['sand']:.0f} %")
    with s3:
        st.metric("Organic C", f"{soil_s['organic_carbon']:.1f} g/kg")
    with s4:
        st.metric("Water Features", f"{water_s['total']}")

    w1, w2, w3 = st.columns(3)
    with w1:
        st.metric("Rivers / Streams", f"{water_s['rivers']}")
    with w2:
        st.metric("Lakes / Ponds", f"{water_s['lakes']}")
    with w3:
        st.metric("Springs", f"{water_s['springs']}")

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
            for kw in ("FLOOD ALERT", "TERRAIN WARNING", "SOIL WARNING",
                        "WATER PROXIMITY ALERT", "DRAINAGE CRITICAL")
        )
        card_border = CLR_DANGER if is_alert else CLR_BORDER
        icon_color = CLR_DANGER if is_alert else CLR_FLOOD_MID

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
            Flood Risk Modeling powered by Open-Meteo, Open-Elevation,
            ISRIC SoilGrids, and OpenStreetMap.
            Estimates are indicative and should complement professional
            hydrological assessments.
        </div>
        """,
        unsafe_allow_html=True,
    )
