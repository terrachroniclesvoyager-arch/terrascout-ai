"""
Climate Risk Intelligence AI module for TerraScout AI.
Provides deep climate risk analysis combining current weather, forecasts,
and historical patterns to generate actionable risk assessments.
Uses Open-Meteo forecast API (free, no key required).
"""

import logging
from html import escape

import requests
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
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"
CLR_ACCENT = "#06b6d4"

# Risk color thresholds
CLR_MINIMAL = "#22c55e"    # green   (< 3)
CLR_MODERATE = "#f59e0b"   # amber   (3 - 6)
CLR_HIGH = "#ef4444"       # red     (> 6)
CLR_CRITICAL = "#991b1b"   # dark red (> 8)

RISK_LABELS = {
    "Heat Stress": {"icon": "fire", "desc": "Risk from extreme high temperatures"},
    "Cold Stress": {"icon": "snowflake-o", "desc": "Risk from extreme low temperatures"},
    "Flood Risk": {"icon": "tint", "desc": "Flooding potential from precipitation and terrain"},
    "Drought Risk": {"icon": "sun-o", "desc": "Drought potential from low rainfall and heat"},
    "Wind Damage": {"icon": "flag", "desc": "Risk of structural and vegetation damage from wind"},
    "UV Exposure": {"icon": "bolt", "desc": "Ultraviolet radiation exposure risk"},
    "Storm Risk": {"icon": "cloud", "desc": "Combined storm intensity from wind and precipitation"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _risk_color(score: float) -> str:
    """Return a hex color for a 0-10 risk score."""
    if score > 8:
        return CLR_CRITICAL
    if score > 6:
        return CLR_HIGH
    if score >= 3:
        return CLR_MODERATE
    return CLR_MINIMAL


def _risk_class(score: float) -> str:
    """Return a human-readable risk classification."""
    if score > 8:
        return "Critical"
    if score > 6:
        return "High"
    if score >= 3:
        return "Moderate"
    if score >= 1:
        return "Low"
    return "Minimal"


def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def _safe_mean(values: list) -> float:
    """Return mean of a list, or 0.0 if empty/None."""
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


def _safe_max(values: list, default: float = 0.0) -> float:
    """Return max of a list, or default if empty/None."""
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return default
    return max(cleaned)


def _safe_min(values: list, default: float = 0.0) -> float:
    """Return min of a list, or default if empty/None."""
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return default
    return min(cleaned)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_climate_forecast(lat: float, lon: float) -> dict:
    """
    Fetch a 14-day weather forecast from the Open-Meteo forecast API.
    Returns the JSON response or an empty dict on error.
    """
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,wind_speed_10m_max,uv_index_max"
            ),
            "forecast_days": 14,
            "timezone": "auto",
        }
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Climate forecast fetch error: %s", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# RISK COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_climate_risk(lat: float, lon: float) -> dict:
    """
    Compute a comprehensive climate risk assessment for a location.

    Returns a dict with:
        overall_risk   - weighted average risk score (0-10)
        risk_class     - Critical / High / Moderate / Low / Minimal
        risk_color     - hex color string
        scores         - dict of 7 individual risk scores
        timeline       - dict of daily risk series (heat, cold, flood, wind)
        forecast_summary - dict of summary statistics
        recommendations  - list of recommendation strings
    """
    # ── Fetch all data sources ────────────────────────────────────────────
    weather = fetch_weather_data(lat, lon)
    forecast = fetch_climate_forecast(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    water = fetch_water_features(lat, lon)

    # ── Extract forecast daily arrays ─────────────────────────────────────
    daily = forecast.get("daily", {})
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    precip_sums = daily.get("precipitation_sum", [])
    wind_maxes = daily.get("wind_speed_10m_max", [])
    uv_maxes = daily.get("uv_index_max", [])
    dates = daily.get("time", [])

    # ── Extract supporting data ───────────────────────────────────────────
    center_elev = 0.0
    if elevation and isinstance(elevation, dict):
        center_data = elevation.get("center", {})
        center_elev = center_data.get("elevation", 0.0) if isinstance(center_data, dict) else 0.0

    water_count = 0
    if water and isinstance(water, dict):
        elements = water.get("elements", [])
        if isinstance(elements, list):
            water_count = len(elements)

    # ── Compute individual risk scores (0-10) ─────────────────────────────

    # 1. Heat Stress
    max_temp = _safe_max(temps_max, default=20.0)
    if max_temp > 40:
        heat_score = 10.0
    elif max_temp > 35:
        heat_score = 7.0
    elif max_temp > 30:
        heat_score = 5.0
    elif max_temp > 25:
        heat_score = 3.0
    else:
        heat_score = max(0.0, (max_temp - 15) / 10 * 2)
    heat_score = _clamp(heat_score)

    # 2. Cold Stress
    min_temp = _safe_min(temps_min, default=10.0)
    if min_temp < -20:
        cold_score = 10.0
    elif min_temp < -10:
        cold_score = 7.0
    elif min_temp < 0:
        cold_score = 5.0
    elif min_temp < 5:
        cold_score = 3.0
    else:
        cold_score = max(0.0, (10 - min_temp) / 5)
    cold_score = _clamp(cold_score)

    # 3. Flood Risk (precipitation + water features + low elevation)
    total_precip = sum(v for v in precip_sums if v is not None) if precip_sums else 0.0
    avg_precip = _safe_mean(precip_sums)
    precip_component = min(6.0, avg_precip / 5.0 * 6.0)
    water_component = min(2.0, water_count / 5.0 * 2.0)
    elev_component = 2.0 if center_elev < 50 else (1.0 if center_elev < 200 else 0.0)
    flood_score = _clamp(precip_component + water_component + elev_component)

    # 4. Drought Risk (low precip + high temp + no water)
    low_precip_factor = max(0.0, 1.0 - avg_precip / 5.0) * 4.0
    high_temp_factor = max(0.0, (_safe_mean(temps_max) - 25) / 15) * 3.0
    no_water_factor = 3.0 if water_count == 0 else max(0.0, (3.0 - water_count) / 3.0 * 3.0)
    drought_score = _clamp(low_precip_factor + high_temp_factor + no_water_factor)

    # 5. Wind Damage
    max_wind = _safe_max(wind_maxes, default=10.0)
    if max_wind > 100:
        wind_score = 10.0
    elif max_wind > 70:
        wind_score = 8.0
    elif max_wind > 50:
        wind_score = 6.0
    elif max_wind > 30:
        wind_score = 4.0
    else:
        wind_score = max(0.0, (max_wind - 10) / 20 * 3)
    wind_score = _clamp(wind_score)

    # 6. UV Exposure
    max_uv = _safe_max(uv_maxes, default=3.0)
    avg_uv = _safe_mean(uv_maxes)
    uv_score = _clamp(avg_uv / 11.0 * 10.0)

    # 7. Storm Risk (wind + precipitation spikes)
    wind_factor = min(5.0, max_wind / 100 * 5.0)
    max_precip = _safe_max(precip_sums, default=0.0)
    precip_spike = min(5.0, max_precip / 50 * 5.0)
    storm_score = _clamp(wind_factor + precip_spike)

    scores = {
        "Heat Stress": round(heat_score, 1),
        "Cold Stress": round(cold_score, 1),
        "Flood Risk": round(flood_score, 1),
        "Drought Risk": round(drought_score, 1),
        "Wind Damage": round(wind_score, 1),
        "UV Exposure": round(uv_score, 1),
        "Storm Risk": round(storm_score, 1),
    }

    # ── Weighted overall risk ─────────────────────────────────────────────
    weights = {
        "Heat Stress": 1.5,
        "Cold Stress": 1.2,
        "Flood Risk": 2.0,
        "Drought Risk": 1.3,
        "Wind Damage": 1.5,
        "UV Exposure": 0.8,
        "Storm Risk": 1.7,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(scores[k] * weights[k] for k in scores)
    overall = round(weighted_sum / total_weight, 1)

    # ── 14-day risk timeline ──────────────────────────────────────────────
    timeline = {"dates": dates, "heat": [], "cold": [], "flood": [], "wind": []}
    for i in range(len(dates)):
        # Daily heat score
        t_max = temps_max[i] if i < len(temps_max) and temps_max[i] is not None else 20.0
        if t_max > 40:
            dh = 10.0
        elif t_max > 35:
            dh = 7.0
        elif t_max > 30:
            dh = 5.0
        elif t_max > 25:
            dh = 3.0
        else:
            dh = max(0.0, (t_max - 15) / 10 * 2)
        timeline["heat"].append(round(_clamp(dh), 1))

        # Daily cold score
        t_min = temps_min[i] if i < len(temps_min) and temps_min[i] is not None else 10.0
        if t_min < -20:
            dc = 10.0
        elif t_min < -10:
            dc = 7.0
        elif t_min < 0:
            dc = 5.0
        elif t_min < 5:
            dc = 3.0
        else:
            dc = max(0.0, (10 - t_min) / 5)
        timeline["cold"].append(round(_clamp(dc), 1))

        # Daily flood score
        p_day = precip_sums[i] if i < len(precip_sums) and precip_sums[i] is not None else 0.0
        df = _clamp(min(6.0, p_day / 10.0 * 6.0) + elev_component + water_component)
        timeline["flood"].append(round(df, 1))

        # Daily wind score
        w_day = wind_maxes[i] if i < len(wind_maxes) and wind_maxes[i] is not None else 10.0
        if w_day > 100:
            dw = 10.0
        elif w_day > 70:
            dw = 8.0
        elif w_day > 50:
            dw = 6.0
        elif w_day > 30:
            dw = 4.0
        else:
            dw = max(0.0, (w_day - 10) / 20 * 3)
        timeline["wind"].append(round(_clamp(dw), 1))

    # ── Forecast summary ──────────────────────────────────────────────────
    forecast_summary = {
        "avg_temp_max": round(_safe_mean(temps_max), 1),
        "avg_temp_min": round(_safe_mean(temps_min), 1),
        "total_precip": round(total_precip, 1),
        "max_wind": round(max_wind, 1),
        "avg_uv": round(_safe_mean(uv_maxes), 1),
        "max_uv": round(max_uv, 1),
        "elevation_m": round(center_elev, 0),
        "water_features": water_count,
        "days": len(dates),
    }

    # ── Recommendations ───────────────────────────────────────────────────
    recommendations = []

    if heat_score >= 7:
        recommendations.append(
            "HEAT ALERT: Extreme high temperatures expected. "
            "Implement heat action plans, ensure water availability, "
            "and schedule outdoor activities for early morning or evening."
        )
    elif heat_score >= 4:
        recommendations.append(
            "Heat Advisory: Elevated temperatures forecast. "
            "Monitor vulnerable populations and ensure adequate hydration."
        )

    if cold_score >= 7:
        recommendations.append(
            "COLD ALERT: Severe cold conditions expected. "
            "Protect crops and livestock, ensure heating systems, "
            "and monitor for frost damage."
        )
    elif cold_score >= 4:
        recommendations.append(
            "Cold Advisory: Low temperatures expected. "
            "Prepare frost protection for sensitive vegetation."
        )

    if flood_score >= 7:
        recommendations.append(
            "FLOOD WARNING: High flood risk from precipitation, "
            "proximity to water features, and low elevation. "
            "Activate drainage plans and monitor water levels closely."
        )
    elif flood_score >= 4:
        recommendations.append(
            "Flood Watch: Moderate flood potential. "
            "Clear drainage channels and monitor precipitation forecasts."
        )

    if drought_score >= 7:
        recommendations.append(
            "DROUGHT ALERT: Conditions favor severe drought. "
            "Implement water conservation measures immediately. "
            "Consider irrigation scheduling and drought-resistant crops."
        )
    elif drought_score >= 4:
        recommendations.append(
            "Drought Advisory: Below-average precipitation with warm conditions. "
            "Plan water usage carefully and monitor soil moisture."
        )

    if wind_score >= 7:
        recommendations.append(
            "WIND WARNING: Damaging winds expected. "
            "Secure structures, equipment, and loose materials. "
            "Postpone aerial operations."
        )
    elif wind_score >= 4:
        recommendations.append(
            "Wind Advisory: Strong winds forecast. "
            "Check structural integrity and secure lightweight objects."
        )

    if uv_score >= 7:
        recommendations.append(
            "UV ALERT: Very high UV index expected. "
            "Limit outdoor exposure during midday hours. "
            "Use protective clothing and sunscreen."
        )
    elif uv_score >= 4:
        recommendations.append(
            "UV Advisory: Elevated UV levels. "
            "Take standard sun protection precautions."
        )

    if storm_score >= 7:
        recommendations.append(
            "STORM WARNING: High storm potential from combined wind and precipitation. "
            "Activate emergency response protocols and ensure shelter availability."
        )
    elif storm_score >= 4:
        recommendations.append(
            "Storm Watch: Moderate storm conditions possible. "
            "Monitor weather updates and prepare contingency plans."
        )

    if not recommendations:
        recommendations.append(
            "Overall conditions appear favorable. "
            "Continue routine monitoring and standard operational planning."
        )

    return {
        "overall_risk": overall,
        "risk_class": _risk_class(overall),
        "risk_color": _risk_color(overall),
        "scores": scores,
        "timeline": timeline,
        "forecast_summary": forecast_summary,
        "recommendations": recommendations,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_gauge_chart(score: float, color: str) -> go.Figure:
    """Create a plotly gauge chart for overall risk score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"font": {"size": 48, "color": CLR_TEXT}},
        title={"text": "Overall Climate Risk", "font": {"size": 18, "color": CLR_TEXT_SEC}},
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
                {"range": [0, 3], "color": "rgba(34,197,94,0.15)"},
                {"range": [3, 6], "color": "rgba(245,158,11,0.15)"},
                {"range": [6, 8], "color": "rgba(239,68,68,0.15)"},
                {"range": [8, 10], "color": "rgba(153,27,27,0.15)"},
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


def _build_timeline_chart(timeline: dict) -> go.Figure:
    """Create a 14-day multi-series risk timeline chart."""
    dates = timeline.get("dates", [])
    if not dates:
        fig = go.Figure()
        fig.update_layout(
            height=350,
            paper_bgcolor=CLR_BG,
            plot_bgcolor=CLR_BG,
            annotations=[{
                "text": "No forecast data available",
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5, "showarrow": False,
                "font": {"size": 16, "color": CLR_TEXT_SEC},
            }],
        )
        return fig

    series_config = [
        ("heat", "Heat Risk", "#ef4444"),
        ("cold", "Cold Risk", "#3b82f6"),
        ("flood", "Flood Risk", "#8b5cf6"),
        ("wind", "Wind Risk", "#f59e0b"),
    ]

    fig = go.Figure()
    for key, name, color in series_config:
        values = timeline.get(key, [])
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name=name,
            line={"color": color, "width": 2.5},
            marker={"size": 5, "color": color},
            fill="tozeroy",
            fillcolor=(color.replace(")", ",0.05)").replace("rgb", "rgba")
            if color.startswith("rgb")
            else f"rgba({int(color.lstrip('#')[0:2],16)},{int(color.lstrip('#')[2:4],16)},{int(color.lstrip('#')[4:6],16)},0.05)"),
            hovertemplate=f"{name}: %{{y:.1f}}<br>%{{x}}<extra></extra>",
        ))

    # Risk zone bands
    fig.add_hrect(y0=0, y1=3, fillcolor="rgba(34,197,94,0.05)",
                  line_width=0, annotation_text="Low",
                  annotation_position="top left",
                  annotation_font_color=CLR_TEXT_SEC)
    fig.add_hrect(y0=3, y1=6, fillcolor="rgba(245,158,11,0.05)",
                  line_width=0, annotation_text="Moderate",
                  annotation_position="top left",
                  annotation_font_color=CLR_TEXT_SEC)
    fig.add_hrect(y0=6, y1=8, fillcolor="rgba(239,68,68,0.05)",
                  line_width=0, annotation_text="High",
                  annotation_position="top left",
                  annotation_font_color=CLR_TEXT_SEC)
    fig.add_hrect(y0=8, y1=10, fillcolor="rgba(153,27,27,0.05)",
                  line_width=0, annotation_text="Critical",
                  annotation_position="top left",
                  annotation_font_color=CLR_TEXT_SEC)

    fig.update_layout(
        title={"text": "14-Day Climate Risk Timeline", "font": {"color": CLR_TEXT, "size": 16}},
        height=380,
        margin=dict(l=40, r=20, t=50, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        xaxis={
            "title": "Date",
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title_font": {"color": CLR_TEXT_SEC},
        },
        yaxis={
            "title": "Risk Score",
            "range": [0, 10.5],
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
        hovermode="x unified",
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def render_climate_risk_tab():
    """Render the Climate Risk Intelligence tab in the Streamlit UI."""

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Climate Risk Intelligence AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Deep climate risk analysis combining current weather, 14-day forecasts,
                terrain data, and hydrological features.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Location selector ─────────────────────────────────────────────────
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="cri_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="cri_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="cri_lon",
        )

    run_btn = st.button(
        "Analyze Climate Risk",
        type="primary",
        key="cri_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Analyze Climate Risk** to begin.")
        return

    # ── Run analysis ──────────────────────────────────────────────────────
    with st.spinner("Fetching climate data and computing risk assessment..."):
        result = compute_climate_risk(lat, lon)

    overall = result["overall_risk"]
    rc = result["risk_class"]
    r_color = result["risk_color"]
    scores = result["scores"]
    timeline = result["timeline"]
    fsum = result["forecast_summary"]
    recommendations = result["recommendations"]

    # ── Overall risk header ───────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{r_color}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {r_color}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};text-transform:uppercase;
                                 letter-spacing:1px;">Overall Climate Risk</span>
                    <h1 style="margin:4px 0;color:{r_color};font-size:42px;">{overall}/10</h1>
                    <span style="font-size:18px;color:{r_color};font-weight:600;">{escape(rc)}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Forecast: {fsum.get('days', 0)} days<br>
                        Elevation: {fsum.get('elevation_m', 0):.0f} m
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Gauge chart ───────────────────────────────────────────────────────
    gauge_fig = _build_gauge_chart(overall, r_color)
    st.plotly_chart(gauge_fig, use_container_width=True, key="cri_gauge")

    # ── Risk score cards ──────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">Risk Breakdown</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display 7 risk cards in rows of columns
    risk_keys = list(scores.keys())
    row1_keys = risk_keys[:4]
    row2_keys = risk_keys[4:]

    cols_row1 = st.columns(len(row1_keys))
    for col, key in zip(cols_row1, row1_keys):
        score_val = scores[key]
        s_color = _risk_color(score_val)
        s_class = _risk_class(score_val)
        meta = RISK_LABELS.get(key, {"icon": "info", "desc": ""})
        bar_width = max(5, score_val / 10 * 100)
        with col:
            st.markdown(
                f"""
                <div style="background:{CLR_SURFACE};border:1px solid {s_color}44;
                            border-radius:10px;padding:16px;text-align:center;
                            min-height:180px;">
                    <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
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
                        <div style="background:{s_color};width:{bar_width}%;
                                    height:6px;border-radius:4px;"></div>
                    </div>
                    <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:6px;">
                        {escape(meta['desc'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if row2_keys:
        cols_row2 = st.columns(len(row2_keys))
        for col, key in zip(cols_row2, row2_keys):
            score_val = scores[key]
            s_color = _risk_color(score_val)
            s_class = _risk_class(score_val)
            meta = RISK_LABELS.get(key, {"icon": "info", "desc": ""})
            bar_width = max(5, score_val / 10 * 100)
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {s_color}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:180px;">
                        <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
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
                            <div style="background:{s_color};width:{bar_width}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:6px;">
                            {escape(meta['desc'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── 14-day timeline chart ─────────────────────────────────────────────
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    timeline_fig = _build_timeline_chart(timeline)
    st.plotly_chart(timeline_fig, use_container_width=True, key="cri_timeline")

    # ── Recommendations ───────────────────────────────────────────────────
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

    for i, rec in enumerate(recommendations):
        is_alert = rec.startswith(("HEAT ALERT", "COLD ALERT", "FLOOD WARNING",
                                   "DROUGHT ALERT", "WIND WARNING", "UV ALERT",
                                   "STORM WARNING"))
        card_border = CLR_HIGH if is_alert else CLR_BORDER
        card_icon = "exclamation-triangle" if is_alert else "info-circle"
        icon_color = CLR_HIGH if is_alert else CLR_ACCENT

        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {card_border};
                        border-left:4px solid {card_border};
                        border-radius:8px;padding:14px 18px;margin:8px 0;">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="color:{icon_color};font-size:18px;margin-top:2px;">
                        <i class="fa fa-{card_icon}"></i>
                    </span>
                    <span style="color:{CLR_TEXT};font-size:14px;line-height:1.5;">
                        {escape(rec)}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Forecast summary metrics ──────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Forecast Summary ({fsum.get('days', 0)}-Day)
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="Avg Max Temp",
            value=f"{fsum.get('avg_temp_max', 0):.1f} C",
        )
    with m2:
        st.metric(
            label="Avg Min Temp",
            value=f"{fsum.get('avg_temp_min', 0):.1f} C",
        )
    with m3:
        st.metric(
            label="Total Precip",
            value=f"{fsum.get('total_precip', 0):.1f} mm",
        )
    with m4:
        st.metric(
            label="Max Wind",
            value=f"{fsum.get('max_wind', 0):.1f} km/h",
        )

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.metric(
            label="Avg UV Index",
            value=f"{fsum.get('avg_uv', 0):.1f}",
        )
    with m6:
        st.metric(
            label="Max UV Index",
            value=f"{fsum.get('max_uv', 0):.1f}",
        )
    with m7:
        st.metric(
            label="Elevation",
            value=f"{fsum.get('elevation_m', 0):.0f} m",
        )
    with m8:
        st.metric(
            label="Water Features",
            value=f"{fsum.get('water_features', 0)}",
        )

    # ── Footer ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="text-align:center;padding:16px;margin-top:20px;
                    color:{CLR_TEXT_SEC};font-size:12px;">
            Climate Risk Intelligence powered by Open-Meteo, Open-Elevation, and OpenStreetMap.
            Risk scores are indicative and should be used alongside professional assessments.
        </div>
        """,
        unsafe_allow_html=True,
    )
