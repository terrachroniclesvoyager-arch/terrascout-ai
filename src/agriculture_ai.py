"""
Agricultural Intelligence AI module for TerraScout AI.
Provides comprehensive agricultural suitability and crop recommendation
analysis using multi-source data:
  - ISRIC SoilGrids (soil composition, pH, nutrients)
  - Open-Meteo (temperature, precipitation, climate)
  - Overpass API (water features, irrigation potential)
  - Open-Elevation (terrain slope, drainage)
All free, no API key required.
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
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CROP PROFILES (12 crops)
# =============================================================================

CROP_PROFILES = {
    "wheat": {
        "name": "Wheat",
        "emoji": "\U0001F33E",
        "ideal_temp_range": (10, 25),
        "ideal_ph_range": (6.0, 7.0),
        "ideal_precip": (400, 800),
        "color": "#d4a017",
    },
    "rice": {
        "name": "Rice",
        "emoji": "\U0001F33E",
        "ideal_temp_range": (20, 35),
        "ideal_ph_range": (5.5, 7.0),
        "ideal_precip": (1000, 2000),
        "color": "#7ec850",
    },
    "corn": {
        "name": "Corn / Maize",
        "emoji": "\U0001F33D",
        "ideal_temp_range": (18, 32),
        "ideal_ph_range": (5.5, 7.0),
        "ideal_precip": (500, 800),
        "color": "#f5c542",
    },
    "soybeans": {
        "name": "Soybeans",
        "emoji": "\U0001FAD8",
        "ideal_temp_range": (20, 30),
        "ideal_ph_range": (6.0, 7.0),
        "ideal_precip": (450, 700),
        "color": "#8db600",
    },
    "potatoes": {
        "name": "Potatoes",
        "emoji": "\U0001F954",
        "ideal_temp_range": (10, 20),
        "ideal_ph_range": (5.0, 6.0),
        "ideal_precip": (500, 700),
        "color": "#c2a366",
    },
    "grapes": {
        "name": "Grapes / Vineyard",
        "emoji": "\U0001F347",
        "ideal_temp_range": (15, 30),
        "ideal_ph_range": (6.0, 7.0),
        "ideal_precip": (500, 800),
        "color": "#7b2d8e",
    },
    "olives": {
        "name": "Olives",
        "emoji": "\U0001FAD2",
        "ideal_temp_range": (15, 30),
        "ideal_ph_range": (6.5, 8.0),
        "ideal_precip": (300, 700),
        "color": "#6b8e23",
    },
    "coffee": {
        "name": "Coffee",
        "emoji": "\u2615",
        "ideal_temp_range": (15, 24),
        "ideal_ph_range": (6.0, 6.5),
        "ideal_precip": (1200, 2000),
        "color": "#6f4e37",
    },
    "cotton": {
        "name": "Cotton",
        "emoji": "\U0001F9F6",
        "ideal_temp_range": (25, 35),
        "ideal_ph_range": (6.0, 7.5),
        "ideal_precip": (500, 1100),
        "color": "#f0ead6",
    },
    "citrus": {
        "name": "Citrus",
        "emoji": "\U0001F34A",
        "ideal_temp_range": (15, 30),
        "ideal_ph_range": (5.5, 6.5),
        "ideal_precip": (600, 1200),
        "color": "#ff9900",
    },
    "barley": {
        "name": "Barley",
        "emoji": "\U0001F33E",
        "ideal_temp_range": (8, 20),
        "ideal_ph_range": (6.0, 7.0),
        "ideal_precip": (300, 600),
        "color": "#c4a35a",
    },
    "sugarcane": {
        "name": "Sugarcane",
        "emoji": "\U0001F9C3",
        "ideal_temp_range": (25, 35),
        "ideal_ph_range": (5.5, 7.5),
        "ideal_precip": (1100, 2000),
        "color": "#56ab2f",
    },
}


# =============================================================================
# HELPER: safe soil value extraction
# =============================================================================

def _extract_soil_value(props, name, div=10):
    """Extract a soil property value from SoilGrids properties dict."""
    layers = props.get("layers", [])
    for layer in (layers if isinstance(layers, list) else []):
        if isinstance(layer, dict) and layer.get("name") == name:
            depths = layer.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
    return None


# =============================================================================
# SCORE HELPERS
# =============================================================================

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


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


# =============================================================================
# MAIN COMPUTATION (cached)
# =============================================================================

@st.cache_data(ttl=1800)
def compute_agriculture_intelligence(lat, lon):
    """
    Fetch all data sources and compute crop suitability scores,
    general agricultural factors, and recommendations.
    """
    # ---- fetch data --------------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)

    # ---- extract soil properties -------------------------------------------
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})

    # Build a quick nested-layer lookup keyed by layer name
    layers_lookup = {}
    for layer in props.get("layers", []):
        layers_lookup[layer.get("name", "")] = layer

    def _sv(name, div=10):
        p = layers_lookup.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay = _sv("clay", 10)
    sand = _sv("sand", 10)
    soc = _sv("soc", 10)
    ph = _sv("phh2o", 10)
    nitrogen = _sv("nitrogen", 100)
    cec = _sv("cec", 10)

    # ---- extract weather ---------------------------------------------------
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}

    temp_now = current.get("temperature_2m")

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

    # ---- water features ----------------------------------------------------
    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    water_count = len(water_elements)

    # ---- elevation / terrain -----------------------------------------------
    center_elev = elevation.get("center_elevation", 0) if isinstance(elevation, dict) else 0
    min_elev = elevation.get("min_elevation", 0) if isinstance(elevation, dict) else 0
    max_elev = elevation.get("max_elevation", 0) if isinstance(elevation, dict) else 0
    elev_range = max_elev - min_elev
    slope_proxy = elev_range  # metres over the grid

    # ---- per-crop suitability (0-100) --------------------------------------
    crop_scores = {}
    for key, profile in CROP_PROFILES.items():
        t_lo, t_hi = profile["ideal_temp_range"]
        ph_lo, ph_hi = profile["ideal_ph_range"]
        p_lo, p_hi = profile["ideal_precip"]

        temp_score = _range_score(avg_temp, t_lo, t_hi)
        ph_score = _range_score(ph, ph_lo, ph_hi)
        precip_score = _range_score(annual_precip_est, p_lo, p_hi)

        # Soil texture compatibility (0-100)
        if clay is not None and sand is not None:
            # Most crops like loamy soil (~20-40% clay, 30-50% sand)
            clay_score = _range_score(clay, 15, 40)
            sand_score = _range_score(sand, 25, 55)
            texture_score = (clay_score + sand_score) / 2.0
        else:
            texture_score = 50.0

        # Terrain suitability: flatter is generally better
        if slope_proxy < 20:
            terrain_score = 100.0
        elif slope_proxy < 100:
            terrain_score = 80.0
        elif slope_proxy < 300:
            terrain_score = 50.0
        else:
            terrain_score = max(10.0, 100.0 - slope_proxy / 5.0)

        overall = (
            temp_score * 0.30
            + ph_score * 0.20
            + precip_score * 0.25
            + texture_score * 0.15
            + terrain_score * 0.10
        )
        crop_scores[key] = {
            "overall": round(_clamp(overall), 1),
            "temperature": round(_clamp(temp_score), 1),
            "ph": round(_clamp(ph_score), 1),
            "precipitation": round(_clamp(precip_score), 1),
            "texture": round(_clamp(texture_score), 1),
            "terrain": round(_clamp(terrain_score), 1),
        }

    # ---- general agricultural factors (0-100) ------------------------------
    # Soil Fertility
    soc_val = soc if soc is not None else 0
    nit_val = nitrogen if nitrogen is not None else 0
    cec_val = cec if cec is not None else 0
    fertility = _clamp(
        min(soc_val * 3.0, 40) + min(nit_val * 20.0, 30) + min(cec_val * 2.0, 30)
    )

    # Water Availability
    precip_factor = _clamp(annual_precip_est / 15.0, 0, 60)
    water_factor = _clamp(water_count * 3.0, 0, 40)
    water_availability = _clamp(precip_factor + water_factor)

    # Growing Season (frost-free days estimate, GDD proxy)
    if min_temp is not None and min_temp > 0:
        frost_free_score = _clamp(min_temp * 5.0, 0, 50)
    else:
        frost_free_score = 0.0
    gdd_proxy = _clamp((avg_temp - 5.0) * 4.0, 0, 50) if avg_temp > 5 else 0.0
    growing_season = _clamp(frost_free_score + gdd_proxy)

    # Terrain (flatness, drainage)
    if slope_proxy < 10:
        flatness = 90.0
    elif slope_proxy < 50:
        flatness = 70.0
    elif slope_proxy < 200:
        flatness = 45.0
    else:
        flatness = max(5.0, 100.0 - slope_proxy / 4.0)
    drainage = _clamp(50.0 + (sand if sand is not None else 30) * 0.5
                       - (clay if clay is not None else 20) * 0.3)
    terrain_factor = _clamp((flatness + drainage) / 2.0)

    # Climate Stability (lower temp variance is better)
    temp_range = max_temp - min_temp if (max_temp is not None and min_temp is not None) else 15.0
    climate_stability = _clamp(100.0 - temp_range * 3.0)

    general_factors = {
        "Soil Fertility": round(fertility, 1),
        "Water Availability": round(water_availability, 1),
        "Growing Season": round(growing_season, 1),
        "Terrain": round(terrain_factor, 1),
        "Climate Stability": round(climate_stability, 1),
    }

    # ---- best crops (top 5) ------------------------------------------------
    sorted_crops = sorted(crop_scores.items(), key=lambda x: x[1]["overall"], reverse=True)
    best_crops = sorted_crops[:5]

    # ---- conditions dict ----------------------------------------------------
    conditions = {
        "avg_temp": round(avg_temp, 1),
        "min_temp": round(min_temp, 1) if min_temp is not None else None,
        "max_temp": round(max_temp, 1) if max_temp is not None else None,
        "annual_precip_est": round(annual_precip_est, 0),
        "ph": round(ph, 1) if ph is not None else None,
        "clay": round(clay, 1) if clay is not None else None,
        "sand": round(sand, 1) if sand is not None else None,
        "soc": round(soc, 1) if soc is not None else None,
        "nitrogen": round(nitrogen, 2) if nitrogen is not None else None,
        "cec": round(cec, 1) if cec is not None else None,
        "elevation": round(center_elev, 0),
        "slope_proxy": round(slope_proxy, 1),
        "water_features": water_count,
    }

    # ---- recommendations ---------------------------------------------------
    recommendations = []
    if fertility < 40:
        recommendations.append(
            "Soil fertility is low. Consider organic matter amendments, "
            "cover crops, or composting to boost SOC and nitrogen levels."
        )
    if water_availability < 35:
        recommendations.append(
            "Water availability is limited. Drought-tolerant crops (olives, barley) "
            "are advisable, or invest in irrigation infrastructure."
        )
    if growing_season < 30:
        recommendations.append(
            "Short growing season detected. Focus on fast-maturing varieties "
            "or cold-hardy crops like barley, wheat, or potatoes."
        )
    if climate_stability < 30:
        recommendations.append(
            "High temperature variability may stress crops. "
            "Greenhouses or protective structures can stabilise conditions."
        )
    if terrain_factor < 35:
        recommendations.append(
            "Steep terrain limits mechanised farming. "
            "Terracing or perennial tree crops (olives, coffee) may suit better."
        )
    if ph is not None and ph < 5.0:
        recommendations.append(
            "Soil is very acidic (pH < 5). Liming can raise pH "
            "to levels suitable for most crops."
        )
    if ph is not None and ph > 8.0:
        recommendations.append(
            "Soil is alkaline (pH > 8). Sulphur or acidifying fertilisers "
            "can help lower pH for sensitive crops."
        )
    if not recommendations:
        recommendations.append(
            "Conditions appear broadly favourable for agriculture. "
            "Select crops matching the top suitability scores above."
        )

    return {
        "crop_scores": crop_scores,
        "general_factors": general_factors,
        "best_crops": best_crops,
        "conditions": conditions,
        "recommendations": recommendations,
    }


# =============================================================================
# RENDER TAB
# =============================================================================

def render_agriculture_ai_tab():
    """Render the Agricultural Intelligence AI tab in Streamlit."""

    st.markdown(
        '<div class="tab-header" style="border-left:4px solid #10b981;'
        'background:rgba(16,185,129,0.08);padding:12px 18px;border-radius:8px;'
        'margin-bottom:16px;">'
        "<h4 style='margin:0;color:#e8ecf4;'>Agricultural Intelligence AI</h4>"
        "<p style='margin:4px 0 0;color:#8b97b0;font-size:13px;'>"
        "Crop suitability analysis, soil health, climate matching "
        "&amp; smart recommendations</p></div>",
        unsafe_allow_html=True,
    )

    # ---- location selector -------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.4, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="agri_ai_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with col_lat:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="agri_ai_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="agri_ai_lon",
        )

    run = st.button(
        "Analyze Agricultural Potential",
        type="primary",
        use_container_width=True,
        key="agri_ai_run",
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Agricultural Potential** "
            "to generate crop suitability scores and recommendations."
        )
        return

    # ---- compute -----------------------------------------------------------
    with st.spinner("Fetching soil, weather, water and elevation data..."):
        result = compute_agriculture_intelligence(lat, lon)

    crop_scores = result["crop_scores"]
    general_factors = result["general_factors"]
    best_crops = result["best_crops"]
    conditions = result["conditions"]
    recommendations = result["recommendations"]

    st.markdown("---")

    # ====================================================================
    # TOP 3 RECOMMENDED CROPS (header cards)
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:8px;'>"
        "Top Recommended Crops</h5>",
        unsafe_allow_html=True,
    )
    top3 = best_crops[:3]
    card_cols = st.columns(len(top3))
    for idx, (crop_key, scores) in enumerate(top3):
        profile = CROP_PROFILES[crop_key]
        with card_cols[idx]:
            medal = ["\U0001F947", "\U0001F948", "\U0001F949"][idx]
            st.markdown(
                f'<div style="background:rgba(26,26,46,0.85);'
                f"border:1px solid {profile['color']};border-radius:12px;"
                f'padding:16px;text-align:center;">'
                f'<div style="font-size:36px;">{profile["emoji"]}</div>'
                f'<div style="color:#e8ecf4;font-size:18px;font-weight:bold;'
                f'margin:6px 0;">{medal} {profile["name"]}</div>'
                f'<div style="color:{profile["color"]};font-size:28px;'
                f'font-weight:bold;">{scores["overall"]}%</div>'
                f'<div style="color:#8b97b0;font-size:11px;margin-top:4px;">'
                f"Suitability Score</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("")

    # ====================================================================
    # GENERAL FACTORS RADAR CHART
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "General Agricultural Factors</h5>",
        unsafe_allow_html=True,
    )

    factor_names = list(general_factors.keys())
    factor_values = list(general_factors.values())
    # Close the polygon by repeating the first value
    radar_values = factor_values + [factor_values[0]]
    radar_names = factor_names + [factor_names[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values,
        theta=radar_names,
        fill="toself",
        fillcolor="rgba(16,185,129,0.18)",
        line=dict(color="#10b981", width=2),
        marker=dict(size=6, color="#10b981"),
        name="Score",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(26,26,46,0.6)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2a3550", tickfont=dict(color="#5a6580", size=10),
            ),
            angularaxis=dict(
                gridcolor="#2a3550",
                tickfont=dict(color="#e8ecf4", size=11),
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30),
        height=370,
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="agrai_pchart1")

    # ====================================================================
    # ALL 12 CROPS HORIZONTAL BAR CHART (sorted by score)
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "All Crop Suitability Scores</h5>",
        unsafe_allow_html=True,
    )

    sorted_all = sorted(crop_scores.items(), key=lambda x: x[1]["overall"])
    bar_names = []
    bar_scores = []
    bar_colors = []
    for crop_key, scores in sorted_all:
        profile = CROP_PROFILES[crop_key]
        bar_names.append(f"{profile['emoji']} {profile['name']}")
        bar_scores.append(scores["overall"])
        bar_colors.append(profile["color"])

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        y=bar_names,
        x=bar_scores,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{s}%" for s in bar_scores],
        textposition="outside",
        textfont=dict(color="#e8ecf4", size=11),
    ))
    fig_bar.update_layout(
        xaxis=dict(
            range=[0, 110], title="Suitability %",
            gridcolor="#2a3550", tickfont=dict(color="#8b97b0"),
            title_font=dict(color="#8b97b0"),
        ),
        yaxis=dict(tickfont=dict(color="#e8ecf4", size=12)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.4)",
        margin=dict(l=160, r=50, t=10, b=30),
        height=max(380, len(bar_names) * 36),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="agrai_pchart2")

    # ====================================================================
    # SOIL CONDITIONS METRICS ROW
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>Soil Conditions</h5>",
        unsafe_allow_html=True,
    )
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("pH", f"{conditions['ph']}" if conditions["ph"] is not None else "N/A")
    s2.metric("Clay", f"{conditions['clay']}%" if conditions["clay"] is not None else "N/A")
    s3.metric("Sand", f"{conditions['sand']}%" if conditions["sand"] is not None else "N/A")
    s4.metric("SOC", f"{conditions['soc']} g/kg" if conditions["soc"] is not None else "N/A")
    s5.metric("Nitrogen", f"{conditions['nitrogen']} g/kg" if conditions["nitrogen"] is not None else "N/A")
    s6.metric("CEC", f"{conditions['cec']} cmol/kg" if conditions["cec"] is not None else "N/A")

    # ====================================================================
    # CLIMATE CONDITIONS METRICS ROW
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>Climate Conditions</h5>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Avg Temp", f"{conditions['avg_temp']} C")
    c2.metric("Min Temp", f"{conditions['min_temp']} C" if conditions["min_temp"] is not None else "N/A")
    c3.metric("Max Temp", f"{conditions['max_temp']} C" if conditions["max_temp"] is not None else "N/A")
    c4.metric("Annual Precip (est)", f"{conditions['annual_precip_est']} mm")
    c5.metric("Elevation", f"{conditions['elevation']} m")
    c6.metric("Water Features", f"{conditions['water_features']}")

    # ====================================================================
    # CROP DETAIL CARDS (4 columns x 3 rows)
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>Crop Detail Cards</h5>",
        unsafe_allow_html=True,
    )

    crop_keys = list(CROP_PROFILES.keys())
    for row_start in range(0, len(crop_keys), 4):
        row_keys = crop_keys[row_start:row_start + 4]
        cols = st.columns(4)
        for col_idx, crop_key in enumerate(row_keys):
            profile = CROP_PROFILES[crop_key]
            scores = crop_scores.get(crop_key, {})
            overall = scores.get("overall", 0)
            with cols[col_idx]:
                # Score color gradient
                if overall >= 70:
                    score_color = "#10b981"
                elif overall >= 45:
                    score_color = "#f59e0b"
                else:
                    score_color = "#ef4444"

                st.markdown(
                    f'<div style="background:rgba(26,26,46,0.85);'
                    f"border:1px solid #2a3550;border-radius:10px;"
                    f'padding:12px;margin-bottom:8px;">'
                    f'<div style="display:flex;align-items:center;gap:8px;">'
                    f'<span style="font-size:24px;">{profile["emoji"]}</span>'
                    f'<span style="color:#e8ecf4;font-weight:bold;'
                    f'font-size:14px;">{profile["name"]}</span></div>'
                    f'<div style="color:{score_color};font-size:22px;'
                    f'font-weight:bold;margin:6px 0;">{overall}%</div>'
                    f'<div style="font-size:11px;color:#8b97b0;line-height:1.6;">'
                    f'Temp: {scores.get("temperature", 0)}% &bull; '
                    f'pH: {scores.get("ph", 0)}%<br>'
                    f'Precip: {scores.get("precipitation", 0)}% &bull; '
                    f'Soil: {scores.get("texture", 0)}%<br>'
                    f'Terrain: {scores.get("terrain", 0)}%</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ====================================================================
    # RECOMMENDATIONS SECTION
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-top:12px;margin-bottom:4px;'>"
        "Recommendations</h5>",
        unsafe_allow_html=True,
    )
    for rec in recommendations:
        st.markdown(
            f'<div style="background:rgba(16,185,129,0.07);'
            f"border-left:3px solid #10b981;padding:10px 14px;"
            f'border-radius:0 8px 8px 0;margin-bottom:6px;'
            f'color:#c8d0dc;font-size:13px;">'
            f"{rec}</div>",
            unsafe_allow_html=True,
        )
