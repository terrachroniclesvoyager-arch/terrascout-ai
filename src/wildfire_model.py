"""
Wildfire Risk Intelligence AI module for TerraScout AI.
Provides comprehensive wildfire risk assessment using weather, terrain,
vegetation, and soil data from free APIs via deep_zone_analysis helpers.
No API keys required.
"""

import math
import logging

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
    fetch_soil_data,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

FIRE_WEATHER_INDEX = {
    "Low":          {"range": (0, 2),   "color": "#22c55e", "icon": "LOW"},
    "Moderate":     {"range": (2, 4),   "color": "#fbbf24", "icon": "MOD"},
    "High":         {"range": (4, 6),   "color": "#f97316", "icon": "HIGH"},
    "Very High":    {"range": (6, 7.5), "color": "#ef4444", "icon": "V-HI"},
    "Extreme":      {"range": (7.5, 9), "color": "#dc2626", "icon": "EXT"},
    "Catastrophic": {"range": (9, 10),  "color": "#7f1d1d", "icon": "CAT"},
}

CLR_BG = "#1a1a2e"
CLR_CARD = "#16213e"
CLR_BORDER = "#2a3550"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"


def _clamp(val, lo=0.0, hi=10.0):
    return max(lo, min(hi, val))


def _fwi_level(score):
    """Return the Fire Weather Index level dict for a given score."""
    for name, info in FIRE_WEATHER_INDEX.items():
        lo, hi = info["range"]
        if lo <= score < hi:
            return name, info["color"]
    return "Catastrophic", "#7f1d1d"


# ═══════════════════════════════════════════════════════════════════════════════
# COMPUTE
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_wildfire_risk(lat, lon):
    """Compute comprehensive wildfire risk assessment for a location."""

    weather = fetch_weather_data(lat, lon)
    elev_data = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=6)
    soil = fetch_soil_data(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)

    # ── Weather factors ───────────────────────────────────────────────────
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}

    temp = current.get("temperature_2m") or 20.0
    humidity = current.get("relative_humidity_2m") or 50.0
    wind = current.get("wind_speed_10m") or 10.0
    precip_now = current.get("precipitation") or 0.0

    # Temperature factor
    if temp > 35:
        temp_factor = 9
    elif temp > 30:
        temp_factor = 7
    elif temp > 25:
        temp_factor = 5
    elif temp > 20:
        temp_factor = 3
    else:
        temp_factor = 1

    # Humidity factor (lower = worse)
    if humidity < 20:
        humid_factor = 9
    elif humidity < 30:
        humid_factor = 7
    elif humidity < 40:
        humid_factor = 5
    elif humidity < 60:
        humid_factor = 3
    else:
        humid_factor = 1

    # Wind factor
    if wind > 50:
        wind_factor = 9
    elif wind > 30:
        wind_factor = 7
    elif wind > 20:
        wind_factor = 5
    elif wind > 10:
        wind_factor = 3
    else:
        wind_factor = 1

    # Precipitation / drought
    precip_sums_raw = daily.get("precipitation_sum", [])
    precip_sums = [v for v in precip_sums_raw if v is not None]
    total_precip_7d = sum(precip_sums) if precip_sums else 0.0

    if total_precip_7d < 0.5:
        precip_factor = 9
    elif total_precip_7d < 2:
        precip_factor = 7
    elif total_precip_7d < 5:
        precip_factor = 5
    elif total_precip_7d < 15:
        precip_factor = 3
    else:
        precip_factor = 1

    # Consecutive dry days estimate
    dry_days = 0
    for v in reversed(precip_sums):
        if v < 0.2:
            dry_days += 1
        else:
            break

    drought_score = _clamp(dry_days * 1.4, 0, 10)

    # ── Terrain factors ───────────────────────────────────────────────────
    grid_elevations = elev_data.get("grid_elevations", []) if isinstance(elev_data, dict) else []
    elevations = [e for e in grid_elevations if e is not None]
    center_elev = elev_data.get("center_elevation", 0) if isinstance(elev_data, dict) else 0

    if len(elevations) >= 2:
        elev_range = max(elevations) - min(elevations)
        slope_estimate = elev_range / 500.0  # normalise
        slope_score = _clamp(slope_estimate * 10, 0, 10)
    else:
        slope_score = 3.0

    # Aspect: south-facing in N hemisphere = drier
    is_north_hemisphere = lat >= 0
    aspect_score = 5.0  # default neutral
    if len(elevations) >= 4:
        mid = len(elevations) // 2
        north_elev = sum(elevations[:mid]) / mid if mid > 0 else 0
        south_elev = sum(elevations[mid:]) / max(len(elevations[mid:]), 1)
        if is_north_hemisphere and south_elev < north_elev:
            aspect_score = 7.0  # south-facing slope = drier
        elif not is_north_hemisphere and north_elev < south_elev:
            aspect_score = 7.0

    # Elevation band risk: mid-elevation forests ~500-2000 m most at risk
    if 500 <= center_elev <= 2000:
        elev_band_score = 7.0
    elif 200 <= center_elev < 500 or 2000 < center_elev <= 3000:
        elev_band_score = 5.0
    else:
        elev_band_score = 3.0

    terrain_risk = _clamp((slope_score * 0.4 + aspect_score * 0.3 + elev_band_score * 0.3))

    # ── Fuel load (soil & land use) ───────────────────────────────────────
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    soc = _sv("soc") or 0
    fuel_organic = _clamp(soc / 5.0 * 10, 0, 10)  # higher SOC = more fuel

    elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in elements if isinstance(e, dict) and e.get("tags", {}).get("building"))
    roads = sum(1 for e in elements if isinstance(e, dict) and e.get("tags", {}).get("highway"))
    landuse_tags = [e.get("tags", {}).get("landuse", "") for e in elements if isinstance(e, dict)]

    forest_count = sum(1 for lu in landuse_tags if lu in ("forest", "meadow", "grass", "farmland"))
    developed_count = sum(1 for lu in landuse_tags if lu in ("residential", "commercial", "industrial", "retail"))
    total_lu = max(len(landuse_tags), 1)

    vegetation_density = _clamp((forest_count / total_lu) * 10, 0, 10) if total_lu > 0 else 5.0
    development_ratio = developed_count / total_lu if total_lu > 0 else 0.5
    natural_fuel = _clamp((1 - development_ratio) * 8, 0, 10)

    fuel_load = _clamp(vegetation_density * 0.4 + fuel_organic * 0.3 + natural_fuel * 0.3)

    # ── Ignition probability ──────────────────────────────────────────────
    human_proximity = _clamp(buildings / 50.0 * 6, 0, 8)
    cloud_cover = current.get("cloud_cover") or 0
    lightning_proxy = _clamp(cloud_cover / 100.0 * 4, 0, 4) if cloud_cover > 60 else 0.5
    ignition = _clamp(human_proximity + lightning_proxy)

    # ── Suppression difficulty ────────────────────────────────────────────
    remoteness = _clamp((1 - min(roads / 30.0, 1.0)) * 5, 0, 6)
    suppression = _clamp(remoteness + slope_score * 0.2 + wind_factor * 0.2)

    # ── Component scores ──────────────────────────────────────────────────
    fire_weather = _clamp(temp_factor * 0.35 + humid_factor * 0.35 + wind_factor * 0.30)
    drought_severity = _clamp(precip_factor * 0.5 + drought_score * 0.5)

    component_scores = {
        "Fire Weather": round(fire_weather, 1),
        "Drought Severity": round(drought_severity, 1),
        "Fuel Load": round(fuel_load, 1),
        "Terrain Fire Risk": round(terrain_risk, 1),
        "Ignition Probability": round(ignition, 1),
        "Suppression Difficulty": round(suppression, 1),
    }

    weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]
    overall_risk = _clamp(sum(s * w for s, w in zip(component_scores.values(), weights)))
    overall_risk = round(overall_risk, 1)

    risk_class, risk_color = _fwi_level(overall_risk)
    fwi_level = risk_class

    # ── Recommendations ───────────────────────────────────────────────────
    recommendations = []
    if overall_risk >= 7.5:
        recommendations.append("Extreme fire danger. Avoid all outdoor burning and activities that could cause sparks.")
        recommendations.append("Prepare evacuation routes and emergency supplies immediately.")
    if drought_severity >= 7:
        recommendations.append("Severe drought conditions detected. Water restrictions likely in effect.")
    if fire_weather >= 7:
        recommendations.append("Dangerous fire weather: high temperature, low humidity, and strong winds.")
    if fuel_load >= 7:
        recommendations.append("Heavy vegetation fuel load present. Controlled burns or fuel reduction recommended.")
    if terrain_risk >= 6:
        recommendations.append("Steep terrain will accelerate fire spread uphill. Position defensively.")
    if ignition >= 6:
        recommendations.append("High ignition probability from human activity or lightning risk.")
    if suppression >= 6:
        recommendations.append("Remote and rugged terrain will hamper suppression efforts.")
    if overall_risk < 4:
        recommendations.append("Low to moderate fire risk. Maintain standard fire safety precautions.")
    if not recommendations:
        recommendations.append("Moderate fire risk. Monitor conditions and follow local fire advisories.")

    # Evacuation urgency
    if overall_risk >= 8.5:
        evacuation_urgency = "Critical"
    elif overall_risk >= 6.5:
        evacuation_urgency = "High"
    elif overall_risk >= 4:
        evacuation_urgency = "Medium"
    else:
        evacuation_urgency = "Low"

    weather_conditions = {
        "temperature": round(temp, 1),
        "humidity": round(humidity, 1),
        "wind_speed": round(wind, 1),
        "precipitation_7d": round(total_precip_7d, 1),
        "dry_days": dry_days,
        "cloud_cover": cloud_cover,
    }

    terrain_factors = {
        "elevation": center_elev,
        "slope_score": round(slope_score, 1),
        "aspect_score": round(aspect_score, 1),
        "elevation_band": round(elev_band_score, 1),
    }

    return {
        "overall_risk": overall_risk,
        "risk_class": risk_class,
        "risk_color": risk_color,
        "fwi_level": fwi_level,
        "component_scores": component_scores,
        "weather_conditions": weather_conditions,
        "terrain_factors": terrain_factors,
        "recommendations": recommendations,
        "evacuation_urgency": evacuation_urgency,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def _risk_gradient_bar(score, height=18):
    pct = min(score / 10.0 * 100, 100)
    if score < 4:
        bar_color = "#fbbf24"
    elif score < 7:
        bar_color = "#f97316"
    else:
        bar_color = "#dc2626"
    return (
        f'<div style="background:#2a2a3e;border-radius:9px;height:{height}px;width:100%;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;border-radius:9px;'
        f'background:linear-gradient(90deg,#fbbf24,{bar_color});"></div></div>'
    )


def render_wildfire_model_tab():
    """Render the Wildfire Risk Intelligence tab."""

    st.markdown(
        f"""<div style="background:{CLR_BG};padding:18px 20px 10px;border-radius:12px;
        border:1px solid {CLR_BORDER};margin-bottom:18px;">
        <h2 style="color:#f97316;margin:0;">Wildfire Risk Intelligence AI</h2>
        <p style="color:{CLR_TEXT_SEC};margin:4px 0 0;">Comprehensive wildfire risk
        assessment using weather, terrain, vegetation &amp; soil data.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Location selector ─────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="wf_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="wf_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="wf_lon",
        )

    run = st.button(
        "Assess Wildfire Risk", type="primary",
        key="wf_run", use_container_width=True,
    )

    if not run:
        st.info("Select a location and press **Assess Wildfire Risk** to begin.")
        return

    with st.spinner("Fetching data and computing wildfire risk..."):
        result = compute_wildfire_risk(lat, lon)

    overall = result["overall_risk"]
    risk_class = result["risk_class"]
    risk_color = result["risk_color"]
    fwi_level = result["fwi_level"]
    comps = result["component_scores"]
    wc = result["weather_conditions"]
    tf = result["terrain_factors"]
    recs = result["recommendations"]
    evac = result["evacuation_urgency"]

    # ── FWI header ────────────────────────────────────────────────────────
    st.markdown(
        f"""<div style="background:{CLR_CARD};padding:18px 24px;border-radius:12px;
        border:1px solid {risk_color};margin-bottom:14px;text-align:center;">
        <span style="font-size:2.6rem;font-weight:800;color:{risk_color};">{overall}</span>
        <span style="font-size:1.1rem;color:{CLR_TEXT_SEC};">&nbsp;/ 10</span>
        <div style="margin-top:6px;">
        <span style="background:{risk_color};color:#fff;padding:4px 16px;border-radius:20px;
        font-weight:700;font-size:0.95rem;">{fwi_level}</span>
        </div>
        <p style="color:{CLR_TEXT_SEC};margin:8px 0 0;font-size:0.88rem;">
        Fire Weather Index Level</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Gauge chart ───────────────────────────────────────────────────────
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall,
        title={"text": "Overall Wildfire Risk", "font": {"color": CLR_TEXT, "size": 16}},
        number={"font": {"color": risk_color, "size": 42}},
        gauge={
            "axis": {"range": [0, 10], "tickcolor": CLR_TEXT_SEC, "tickwidth": 1},
            "bar": {"color": risk_color},
            "bgcolor": "#2a2a3e",
            "bordercolor": CLR_BORDER,
            "steps": [
                {"range": [0, 2], "color": "#143024"},
                {"range": [2, 4], "color": "#2a2a1e"},
                {"range": [4, 6], "color": "#3a2a1a"},
                {"range": [6, 7.5], "color": "#3a1a1a"},
                {"range": [7.5, 9], "color": "#4a1515"},
                {"range": [9, 10], "color": "#5a0f0f"},
            ],
            "threshold": {
                "line": {"color": "#fff", "width": 3},
                "thickness": 0.8,
                "value": overall,
            },
        },
    ))
    gauge.update_layout(
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
        height=280,
        margin=dict(t=50, b=20, l=40, r=40),
    )
    st.plotly_chart(gauge, use_container_width=True, key="wilmod_pchart1")

    # ── Component cards (3 cols x 2 rows) ─────────────────────────────────
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:16px 0 8px;">Risk Component Scores</h4>',
        unsafe_allow_html=True,
    )
    comp_icons = {
        "Fire Weather": "thermometer",
        "Drought Severity": "droplet-slash",
        "Fuel Load": "tree",
        "Terrain Fire Risk": "mountain-sun",
        "Ignition Probability": "bolt-lightning",
        "Suppression Difficulty": "truck-field",
    }
    comp_list = list(comps.items())
    for row_start in range(0, len(comp_list), 3):
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            ci = row_start + idx
            if ci >= len(comp_list):
                break
            name, score = comp_list[ci]
            _, sc = _fwi_level(score)
            bar_html = _risk_gradient_bar(score)
            col.markdown(
                f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
                border-radius:10px;padding:14px 16px;margin-bottom:10px;">
                <p style="color:{CLR_TEXT_SEC};margin:0 0 4px;font-size:0.82rem;">{name}</p>
                <span style="font-size:1.6rem;font-weight:700;color:{sc};">{score}</span>
                <span style="color:{CLR_TEXT_SEC};font-size:0.85rem;">/10</span>
                <div style="margin-top:6px;">{bar_html}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── Weather conditions row ────────────────────────────────────────────
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Current Weather Conditions</h4>',
        unsafe_allow_html=True,
    )
    wc1, wc2, wc3, wc4 = st.columns(4)
    wc1.metric("Temperature", f"{wc['temperature']} C")
    wc2.metric("Humidity", f"{wc['humidity']}%")
    wc3.metric("Wind Speed", f"{wc['wind_speed']} km/h")
    wc4.metric("Precip (7d)", f"{wc['precipitation_7d']} mm")

    # ── Risk radar chart ──────────────────────────────────────────────────
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Risk Radar</h4>',
        unsafe_allow_html=True,
    )
    categories = list(comps.keys())
    values = list(comps.values())
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(249,115,22,0.25)",
        line=dict(color="#f97316", width=2),
        marker=dict(size=6, color="#f97316"),
        name="Risk",
    ))
    radar.update_layout(
        polar=dict(
            bgcolor=CLR_BG,
            radialaxis=dict(
                visible=True, range=[0, 10],
                gridcolor=CLR_BORDER, tickfont=dict(color=CLR_TEXT_SEC, size=10),
            ),
            angularaxis=dict(
                gridcolor=CLR_BORDER,
                tickfont=dict(color=CLR_TEXT, size=11),
            ),
        ),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        showlegend=False,
        height=370,
        margin=dict(t=40, b=40, l=60, r=60),
    )
    st.plotly_chart(radar, use_container_width=True, key="wilmod_pchart2")

    # ── Fire spread potential (horizontal bars) ───────────────────────────
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Fire Spread Potential</h4>',
        unsafe_allow_html=True,
    )
    spread_factors = {
        "Wind-Driven Spread": min(wc["wind_speed"] / 6.0, 10),
        "Slope-Assisted Spread": tf["slope_score"],
        "Fuel Continuity": comps["Fuel Load"],
        "Drought Dryness": comps["Drought Severity"],
    }

    bar_fig = go.Figure()
    s_names = list(spread_factors.keys())
    s_vals = [round(v, 1) for v in spread_factors.values()]

    bar_colors = []
    for v in s_vals:
        if v < 4:
            bar_colors.append("#fbbf24")
        elif v < 7:
            bar_colors.append("#f97316")
        else:
            bar_colors.append("#dc2626")

    bar_fig.add_trace(go.Bar(
        y=s_names,
        x=s_vals,
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v}" for v in s_vals],
        textposition="auto",
        textfont=dict(color="#fff", size=13),
    ))
    bar_fig.update_layout(
        xaxis=dict(range=[0, 10], title="Score", gridcolor=CLR_BORDER,
                   tickfont=dict(color=CLR_TEXT_SEC), title_font=dict(color=CLR_TEXT_SEC)),
        yaxis=dict(tickfont=dict(color=CLR_TEXT, size=12)),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        height=250,
        margin=dict(t=20, b=40, l=160, r=30),
        bargap=0.3,
    )
    st.plotly_chart(bar_fig, use_container_width=True, key="wilmod_pchart3")

    # ── Recommendations & evacuation ──────────────────────────────────────
    evac_colors = {
        "Low": "#22c55e", "Medium": "#fbbf24",
        "High": "#f97316", "Critical": "#dc2626",
    }
    evac_clr = evac_colors.get(evac, "#fbbf24")

    recs_html = "".join(
        f'<li style="color:{CLR_TEXT};margin-bottom:6px;font-size:0.92rem;">{r}</li>'
        for r in recs
    )

    st.markdown(
        f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
        border-radius:12px;padding:18px 22px;margin-top:12px;">
        <h4 style="color:#f97316;margin:0 0 6px;">Recommendations</h4>
        <ul style="padding-left:20px;margin:0 0 14px;">{recs_html}</ul>
        <div style="margin-top:10px;padding:10px 16px;border-radius:8px;
        border:1px solid {evac_clr};background:rgba(0,0,0,0.25);">
        <span style="color:{CLR_TEXT_SEC};font-size:0.85rem;">Evacuation Urgency:&nbsp;</span>
        <span style="color:{evac_clr};font-weight:700;font-size:1.1rem;">{evac}</span>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )
