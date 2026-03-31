"""
Renewable Energy Grid AI -- Optimal renewable energy placement analysis
for solar, wind, and hybrid installations.
Uses: Open-Meteo, Open Topo Data, Overpass API, ISRIC SoilGrids.
Part of TerraScout AI (260+ modules).
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
    fetch_protected_areas,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

ENERGY_COMPONENTS = {
    "solar": {"name": "Solar Potential", "color": "#f59e0b", "weight": 0.25},
    "wind": {"name": "Wind Potential", "color": "#3b82f6", "weight": 0.20},
    "grid": {"name": "Grid Connectivity", "color": "#8b5cf6", "weight": 0.15},
    "installation": {"name": "Installation Feasibility", "color": "#22c55e", "weight": 0.15},
    "demand": {"name": "Energy Demand", "color": "#ef4444", "weight": 0.10},
    "environmental": {"name": "Environmental Impact", "color": "#10b981", "weight": 0.15},
}

_PLOTLY_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e2e8f0",
)

# ---------------------------------------------------------------------------
# CACHED DATA FETCHERS
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def fetch_solar_wind_data(lat: float, lon: float) -> dict:
    """Fetch solar radiation and wind data from Open-Meteo (14-day forecast)."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": (
                    "shortwave_radiation_sum,windspeed_10m_max,"
                    "sunshine_duration,temperature_2m_max,"
                    "temperature_2m_min"
                ),
                "timezone": "auto",
                "forecast_days": 14,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Solar/wind data error: %s", e)
        return {}


@st.cache_data(ttl=1800)
def fetch_power_infrastructure(lat: float, lon: float, radius: int = 5000) -> dict:
    """Fetch power lines, substations, generators and buildings via Overpass."""
    query = (
        f"[out:json][timeout:30];\n"
        f"(\n"
        f'  way["power"~"line|minor_line|cable"](around:{radius},{lat},{lon});\n'
        f'  node["power"~"tower|pole|substation|transformer"](around:{radius},{lat},{lon});\n'
        f'  way["power"="substation"](around:{radius},{lat},{lon});\n'
        f'  way["power"="plant"](around:{radius},{lat},{lon});\n'
        f'  way["power"="generator"](around:{radius},{lat},{lon});\n'
        f'  way["building"](around:2000,{lat},{lon});\n'
        f");\n"
        f"out body;"
    )
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Power infrastructure error: %s", e)
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_energy(lat: float, lon: float) -> dict:
    """Fetch a 7x7 elevation grid around the point from Open Topo Data."""
    points = "|".join(
        f"{lat + dy * 0.003},{lon + dx * 0.003}"
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
        logger.warning("Elevation error: %s", e)
        return {"results": []}


# ---------------------------------------------------------------------------
# SCORING HELPERS
# ---------------------------------------------------------------------------


def _safe_mean(values: list) -> float:
    """Return mean of a list, filtering None/non-numeric entries."""
    cleaned = [v for v in values if v is not None and isinstance(v, (int, float))]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def score_solar(solar_wind_data: dict, lat: float) -> tuple:
    """Score solar potential (0-100) and return detail dict."""
    daily = solar_wind_data.get("daily", {})
    radiation_vals = daily.get("shortwave_radiation_sum", [])
    sunshine_vals = daily.get("sunshine_duration", [])

    avg_radiation = _safe_mean(radiation_vals)
    avg_sunshine = _safe_mean(sunshine_vals)
    # sunshine_duration is in seconds; convert to hours
    avg_sunshine_hrs = avg_sunshine / 3600.0 if avg_sunshine else 0.0

    # Base score from radiation: typical good site ~25 MJ/m2/day
    radiation_score = _clamp(avg_radiation * 3.0, 0, 80)

    # Sunshine hours bonus (up to 15)
    sunshine_bonus = _clamp(avg_sunshine_hrs * 1.5, 0, 15)

    # Latitude factor: lower absolute latitude -> more sun potential
    abs_lat = abs(lat)
    if abs_lat < 25:
        lat_factor = 10
    elif abs_lat < 40:
        lat_factor = 7
    elif abs_lat < 55:
        lat_factor = 3
    else:
        lat_factor = 0

    score = _clamp(radiation_score + sunshine_bonus + lat_factor)

    details = {
        "avg_radiation_MJ": round(avg_radiation, 1),
        "avg_sunshine_hrs": round(avg_sunshine_hrs, 1),
        "latitude_abs": round(abs_lat, 1),
        "radiation_score": round(radiation_score, 1),
        "sunshine_bonus": round(sunshine_bonus, 1),
        "lat_factor": lat_factor,
    }
    return round(score, 1), details


def score_wind(solar_wind_data: dict, elevation_data: dict) -> tuple:
    """Score wind potential (0-100) and return detail dict."""
    daily = solar_wind_data.get("daily", {})
    wind_vals = daily.get("windspeed_10m_max", [])

    avg_wind = _safe_mean(wind_vals)

    # Base score: ideal wind speed 6+ m/s
    wind_base = _clamp(avg_wind * 8.0, 0, 70)

    # Consistency bonus: lower variance = more reliable
    cleaned_wind = [v for v in wind_vals if v is not None and isinstance(v, (int, float))]
    if len(cleaned_wind) >= 2:
        mean_w = sum(cleaned_wind) / len(cleaned_wind)
        variance = sum((w - mean_w) ** 2 for w in cleaned_wind) / len(cleaned_wind)
        std_dev = math.sqrt(variance)
        consistency_bonus = _clamp(10 - std_dev * 2, 0, 10)
    else:
        std_dev = 0.0
        consistency_bonus = 0.0

    # Elevation bonus: higher elevations -> more wind exposure
    results = elevation_data.get("results", [])
    elevations = [
        r.get("elevation") for r in results
        if r.get("elevation") is not None
    ]
    avg_elev = _safe_mean(elevations) if elevations else 0.0
    elev_bonus = _clamp(avg_elev / 100.0, 0, 15)

    score = _clamp(wind_base + consistency_bonus + elev_bonus)

    details = {
        "avg_windspeed_ms": round(avg_wind, 1),
        "wind_std_dev": round(std_dev, 2),
        "avg_elevation_m": round(avg_elev, 1),
        "wind_base": round(wind_base, 1),
        "consistency_bonus": round(consistency_bonus, 1),
        "elevation_bonus": round(elev_bonus, 1),
    }
    return round(score, 1), details


def score_grid_connectivity(power_data: dict) -> tuple:
    """Score proximity and density of existing grid infrastructure (0-100)."""
    elements = power_data.get("elements", [])

    power_lines = 0
    substations = 0
    transformers = 0
    plants_generators = 0

    for el in elements:
        tags = el.get("tags", {})
        ptype = tags.get("power", "")
        if ptype in ("line", "minor_line", "cable"):
            power_lines += 1
        elif ptype == "substation":
            substations += 1
        elif ptype in ("tower", "pole"):
            # Towers/poles indicate line presence
            power_lines += 0.3
        elif ptype == "transformer":
            transformers += 1
        elif ptype in ("plant", "generator"):
            plants_generators += 1

    raw = (
        power_lines * 3
        + substations * 20
        + transformers * 10
        + plants_generators * 15
    )
    score = _clamp(raw, 0, 100)

    details = {
        "power_lines": int(power_lines),
        "substations": substations,
        "transformers": transformers,
        "plants_generators": plants_generators,
        "raw_score": round(raw, 1),
    }
    return round(score, 1), details


def score_installation_feasibility(
    elevation_data: dict, soil_data: dict
) -> tuple:
    """Score how feasible it is to build at this site (0-100)."""
    # --- Slope penalty ---
    results = elevation_data.get("results", [])
    elevations = [
        r.get("elevation") for r in results
        if r.get("elevation") is not None
    ]
    if len(elevations) >= 2:
        elev_range = max(elevations) - min(elevations)
        # The grid spans ~0.018 deg ≈ 2 km; 50 m range is significant slope
        slope_penalty = _clamp(elev_range * 0.8, 0, 40)
    else:
        elev_range = 0.0
        slope_penalty = 10  # unknown = mild penalty

    # --- Soil stability ---
    clay_pct = 0.0
    sand_pct = 0.0
    layers = soil_data.get("properties", {}).get("layers", [])
    for layer in layers:
        layer_name = layer.get("name", "")
        depths = layer.get("depths", [])
        top_vals = []
        for d in depths[:2]:  # top two depth bands
            mean_val = d.get("values", {}).get("mean")
            if mean_val is not None:
                top_vals.append(mean_val)
        avg_val = _safe_mean(top_vals)
        if layer_name == "clay":
            clay_pct = avg_val / 10.0  # stored as g/kg -> %
        elif layer_name == "sand":
            sand_pct = avg_val / 10.0

    # High clay = poor drainage / instability
    clay_penalty = _clamp(clay_pct * 0.3, 0, 20)

    # Access roads bonus: check if there are highways in land-use data
    # (not available here directly; give a neutral bonus)
    access_bonus = 5.0

    score = _clamp(100.0 - slope_penalty - clay_penalty + access_bonus)

    details = {
        "elevation_range_m": round(elev_range, 1) if isinstance(elev_range, float) else elev_range,
        "slope_penalty": round(slope_penalty, 1),
        "clay_pct": round(clay_pct, 1),
        "sand_pct": round(sand_pct, 1),
        "clay_penalty": round(clay_penalty, 1),
        "access_bonus": access_bonus,
    }
    return round(score, 1), details


def score_energy_demand(power_data: dict) -> tuple:
    """Score nearby energy demand proxy from building density (0-100)."""
    elements = power_data.get("elements", [])
    buildings = sum(
        1
        for el in elements
        if el.get("tags", {}).get("building") is not None
    )
    score = _clamp(buildings * 0.5, 0, 100)
    details = {
        "buildings_nearby": buildings,
        "raw_score": round(buildings * 0.5, 1),
    }
    return round(score, 1), details


def score_environmental(protected_data: dict) -> tuple:
    """Score environmental impact (0-100). Higher = LESS impact = better."""
    elements = protected_data.get("elements", [])
    protected_count = len(elements)
    penalty = protected_count * 25
    score = _clamp(100.0 - penalty)

    details = {
        "protected_areas": protected_count,
        "penalty": min(penalty, 100),
    }
    return round(score, 1), details


def compute_composite_score(scores: dict) -> float:
    """Weighted average of all component scores."""
    total = 0.0
    weight_sum = 0.0
    for key, comp in ENERGY_COMPONENTS.items():
        s = scores.get(key, 0.0)
        w = comp["weight"]
        total += s * w
        weight_sum += w
    if weight_sum == 0:
        return 0.0
    return round(total / weight_sum, 1)


def recommend_type(scores: dict) -> str:
    """Return 'Solar', 'Wind', or 'Hybrid' recommendation."""
    solar = scores.get("solar", 0)
    wind = scores.get("wind", 0)
    if solar >= 65 and wind >= 55:
        return "Hybrid"
    if solar >= wind + 10:
        return "Solar"
    if wind >= solar + 10:
        return "Wind"
    return "Hybrid"


# ---------------------------------------------------------------------------
# PLOTLY CHARTS
# ---------------------------------------------------------------------------


def _build_radar_chart(scores: dict) -> go.Figure:
    """Build a radar chart of the 6 energy dimensions."""
    categories = []
    values = []
    for key, comp in ENERGY_COMPONENTS.items():
        categories.append(comp["name"])
        values.append(scores.get(key, 0))
    # Close the radar
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(59,130,246,0.18)",
            line=dict(color="#3b82f6", width=2),
            marker=dict(size=6, color="#3b82f6"),
            name="Score",
        )
    )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="rgba(148,163,184,0.15)",
                tickfont=dict(size=10, color="#94a3b8"),
            ),
            angularaxis=dict(
                gridcolor="rgba(148,163,184,0.15)",
                tickfont=dict(size=11, color="#e2e8f0"),
            ),
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
        height=420,
        **_PLOTLY_DARK,
    )
    return fig


def _build_solar_wind_comparison(scores: dict) -> go.Figure:
    """Horizontal bar chart comparing solar vs wind scores."""
    solar_score = scores.get("solar", 0)
    wind_score = scores.get("wind", 0)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=["Solar Potential"],
            x=[solar_score],
            orientation="h",
            marker_color="#f59e0b",
            text=[f"{solar_score}"],
            textposition="auto",
            name="Solar",
        )
    )
    fig.add_trace(
        go.Bar(
            y=["Wind Potential"],
            x=[wind_score],
            orientation="h",
            marker_color="#3b82f6",
            text=[f"{wind_score}"],
            textposition="auto",
            name="Wind",
        )
    )
    fig.update_layout(
        xaxis=dict(range=[0, 100], title="Score", gridcolor="rgba(148,163,184,0.1)"),
        yaxis=dict(tickfont=dict(size=13)),
        barmode="group",
        showlegend=False,
        margin=dict(l=10, r=20, t=30, b=40),
        height=200,
        **_PLOTLY_DARK,
    )
    return fig


def _build_daily_chart(solar_wind_data: dict) -> go.Figure:
    """Line chart of daily radiation and wind speed over 14 days."""
    daily = solar_wind_data.get("daily", {})
    dates = daily.get("time", [])
    radiation = daily.get("shortwave_radiation_sum", [])
    wind = daily.get("windspeed_10m_max", [])

    fig = go.Figure()
    if dates and radiation:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=radiation,
                mode="lines+markers",
                name="Radiation (MJ/m\u00b2)",
                line=dict(color="#f59e0b", width=2),
                marker=dict(size=5),
                yaxis="y",
            )
        )
    if dates and wind:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=wind,
                mode="lines+markers",
                name="Wind Max (m/s)",
                line=dict(color="#3b82f6", width=2),
                marker=dict(size=5),
                yaxis="y2",
            )
        )
    fig.update_layout(
        xaxis=dict(title="Date", gridcolor="rgba(148,163,184,0.1)"),
        yaxis=dict(
            title="Radiation (MJ/m\u00b2/day)",
            title_font=dict(color="#f59e0b"),
            tickfont=dict(color="#f59e0b"),
            gridcolor="rgba(148,163,184,0.1)",
        ),
        yaxis2=dict(
            title="Wind Speed (m/s)",
            title_font=dict(color="#3b82f6"),
            tickfont=dict(color="#3b82f6"),
            overlaying="y",
            side="right",
        ),
        legend=dict(x=0, y=1.12, orientation="h"),
        margin=dict(l=10, r=10, t=50, b=40),
        height=350,
        **_PLOTLY_DARK,
    )
    return fig


# ---------------------------------------------------------------------------
# METRIC CARD HELPER
# ---------------------------------------------------------------------------

_CARD_TEMPLATE = """
<div style="background:linear-gradient(135deg,{bg_from},{bg_to});
            border-radius:14px;padding:18px 20px;min-height:140px;
            border:1px solid rgba(255,255,255,0.06);">
  <div style="font-size:13px;color:#94a3b8;margin-bottom:4px;">{label}</div>
  <div style="font-size:32px;font-weight:700;color:{color};">{value}<span style="font-size:16px;">/100</span></div>
  <div style="font-size:12px;color:#cbd5e1;margin-top:6px;line-height:1.5;">{detail}</div>
</div>
"""


def _render_card(label: str, value: float, color: str, detail: str) -> None:
    bg_from = "rgba(30,41,59,0.85)"
    bg_to = "rgba(15,23,42,0.90)"
    st.markdown(
        _CARD_TEMPLATE.format(
            bg_from=bg_from,
            bg_to=bg_to,
            label=label,
            value=value,
            color=color,
            detail=detail,
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------


def render_renewable_grid_tab() -> None:
    """Render the Renewable Energy Grid AI tab."""

    st.markdown(
        "<h2 style='text-align:center;color:#f59e0b;'>"
        "Renewable Energy Grid AI"
        "</h2>"
        "<p style='text-align:center;color:#94a3b8;font-size:14px;'>"
        "Optimal placement analysis for solar, wind, and hybrid installations"
        "</p>",
        unsafe_allow_html=True,
    )

    # ── Location selector ──────────────────────────────────────────────────
    col_preset, col_lat, col_lon = st.columns([2, 1, 1])
    with col_preset:
        preset_name = st.selectbox(
            "Location preset",
            list(ANALYSIS_PRESETS.keys()),
            index=0,
            key="rg_preset",
        )
    p = ANALYSIS_PRESETS.get(preset_name)
    with col_lat:
        lat = st.number_input(
            "Latitude",
            value=p.get("lat", 41.90) if p else 41.90,
            format="%.4f",
            key="rg_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude",
            value=p.get("lon", 12.50) if p else 12.50,
            format="%.4f",
            key="rg_lon",
        )

    if not st.button("Analyze Renewable Potential", type="primary", key="rg_run"):
        st.info("Select a location and click **Analyze Renewable Potential** to begin.")
        return

    # ── Fetch all data ─────────────────────────────────────────────────────
    with st.spinner("Fetching solar & wind forecast..."):
        solar_wind_data = fetch_solar_wind_data(lat, lon)

    with st.spinner("Fetching power infrastructure..."):
        power_data = fetch_power_infrastructure(lat, lon)

    with st.spinner("Fetching elevation grid..."):
        elevation_data = fetch_elevation_energy(lat, lon)

    with st.spinner("Fetching soil data..."):
        soil_data = fetch_soil_data(lat, lon)

    with st.spinner("Fetching protected areas..."):
        protected_data = fetch_protected_areas(lat, lon)

    # ── Compute scores ─────────────────────────────────────────────────────
    solar_score, solar_det = score_solar(solar_wind_data, lat)
    wind_score, wind_det = score_wind(solar_wind_data, elevation_data)
    grid_score, grid_det = score_grid_connectivity(power_data)
    install_score, install_det = score_installation_feasibility(
        elevation_data, soil_data
    )
    demand_score, demand_det = score_energy_demand(power_data)
    env_score, env_det = score_environmental(protected_data)

    scores = {
        "solar": solar_score,
        "wind": wind_score,
        "grid": grid_score,
        "installation": install_score,
        "demand": demand_score,
        "environmental": env_score,
    }

    composite = compute_composite_score(scores)
    rec_type = recommend_type(scores)

    # ── Header banner ──────────────────────────────────────────────────────
    rec_colors = {"Solar": "#f59e0b", "Wind": "#3b82f6", "Hybrid": "#8b5cf6"}
    rec_color = rec_colors.get(rec_type, "#22c55e")
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,rgba(30,41,59,0.92),rgba(15,23,42,0.95));
                    border:1px solid {rec_color}44;border-radius:16px;
                    padding:24px 30px;text-align:center;margin-bottom:20px;">
          <div style="font-size:15px;color:#94a3b8;">Composite Grid Score</div>
          <div style="font-size:52px;font-weight:800;color:{rec_color};">
            {composite}<span style="font-size:22px;color:#94a3b8;">/100</span>
          </div>
          <div style="font-size:18px;color:{rec_color};margin-top:4px;">
            Recommendation: <strong>{rec_type}</strong>
          </div>
          <div style="font-size:13px;color:#64748b;margin-top:6px;">
            {lat:.4f}, {lon:.4f}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Radar chart ────────────────────────────────────────────────────────
    st.subheader("Energy Dimension Radar")
    radar_fig = _build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="rengri_pchart1")

    # ── 6 Metric cards (2 rows x 3 cols) ──────────────────────────────────
    st.subheader("Component Scores")

    detail_texts = {
        "solar": (
            f"Radiation {solar_det['avg_radiation_MJ']} MJ/m\u00b2 | "
            f"Sun {solar_det['avg_sunshine_hrs']}h | "
            f"Lat factor +{solar_det['lat_factor']}"
        ),
        "wind": (
            f"Avg wind {wind_det['avg_windspeed_ms']} m/s | "
            f"Elev {wind_det['avg_elevation_m']}m | "
            f"Consistency +{wind_det['consistency_bonus']}"
        ),
        "grid": (
            f"Lines {grid_det['power_lines']} | "
            f"Substations {grid_det['substations']} | "
            f"Plants {grid_det['plants_generators']}"
        ),
        "installation": (
            f"Elev range {install_det['elevation_range_m']}m | "
            f"Clay {install_det['clay_pct']}% | "
            f"Slope pen -{install_det['slope_penalty']}"
        ),
        "demand": (
            f"Buildings nearby: {demand_det['buildings_nearby']} | "
            f"Raw {demand_det['raw_score']}"
        ),
        "environmental": (
            f"Protected areas: {env_det['protected_areas']} | "
            f"Penalty: -{env_det['penalty']}"
        ),
    }

    row1_keys = ["solar", "wind", "grid"]
    row2_keys = ["installation", "demand", "environmental"]

    cols1 = st.columns(3)
    for idx, key in enumerate(row1_keys):
        comp = ENERGY_COMPONENTS[key]
        with cols1[idx]:
            _render_card(
                comp["name"],
                scores[key],
                comp["color"],
                detail_texts[key],
            )

    cols2 = st.columns(3)
    for idx, key in enumerate(row2_keys):
        comp = ENERGY_COMPONENTS[key]
        with cols2[idx]:
            _render_card(
                comp["name"],
                scores[key],
                comp["color"],
                detail_texts[key],
            )

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    # ── Solar vs Wind comparison ───────────────────────────────────────────
    st.subheader("Solar vs Wind Comparison")
    comparison_fig = _build_solar_wind_comparison(scores)
    st.plotly_chart(comparison_fig, use_container_width=True, key="rengri_pchart2")

    # ── Daily radiation & wind chart ───────────────────────────────────────
    st.subheader("14-Day Radiation & Wind Forecast")
    daily_fig = _build_daily_chart(solar_wind_data)
    st.plotly_chart(daily_fig, use_container_width=True, key="rengri_pchart3")

    # ── Installation Recommendation Summary ────────────────────────────────
    st.subheader("Installation Recommendation")

    if rec_type == "Solar":
        rec_icon = "&#9728;"  # sun
        rec_detail = (
            "This location favours <strong>solar photovoltaic</strong> installations. "
            "High radiation levels and favourable latitude offset moderate wind speeds. "
            "Consider fixed-tilt or single-axis tracking panels."
        )
    elif rec_type == "Wind":
        rec_icon = "&#127744;"  # wind
        rec_detail = (
            "This location favours <strong>wind turbine</strong> installations. "
            "Strong and consistent winds combined with elevated terrain provide "
            "excellent energy capture potential."
        )
    else:
        rec_icon = "&#9889;"  # lightning
        rec_detail = (
            "This location is well-suited for a <strong>hybrid solar + wind</strong> "
            "installation. Both resources score competitively, enabling complementary "
            "generation profiles and higher capacity factors."
        )

    grid_note = ""
    if grid_score < 30:
        grid_note = (
            "<br><strong>Note:</strong> Grid connectivity is low. "
            "Off-grid or micro-grid solutions with battery storage may be required."
        )
    elif grid_score >= 70:
        grid_note = (
            "<br><strong>Note:</strong> Excellent grid connectivity. "
            "Grid-tied installations with net metering are viable."
        )

    env_note = ""
    if env_score < 40:
        env_note = (
            "<br><strong>Warning:</strong> Nearby protected areas detected. "
            "Environmental impact assessments will be critical."
        )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,rgba(30,41,59,0.88),rgba(15,23,42,0.92));
                    border-radius:14px;padding:22px 26px;
                    border:1px solid {rec_color}33;margin-top:8px;">
          <div style="font-size:20px;margin-bottom:8px;">
            {rec_icon} <strong style="color:{rec_color};">{rec_type} Installation Recommended</strong>
          </div>
          <div style="font-size:14px;color:#cbd5e1;line-height:1.7;">
            {rec_detail}
            {grid_note}
            {env_note}
          </div>
          <div style="margin-top:14px;font-size:13px;color:#64748b;">
            Composite score {composite}/100 &mdash;
            Solar {solar_score} | Wind {wind_score} | Grid {grid_score} |
            Install {install_score} | Demand {demand_score} | Env {env_score}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
