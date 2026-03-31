"""
Microclimate Intelligence AI module for TerraScout AI.
Analyzes local microclimate conditions based on terrain, aspect, elevation,
vegetation, and proximity to water/urban features. Computes six microclimate
indices and classifies the site into a microclimate archetype.
Uses Open-Meteo, Open-Elevation, and Overpass API (free, no key required).
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
CLR_ACCENT = "#06b6d4"

# Index colours
CLR_THERMAL = "#ef4444"
CLR_WIND = "#06b6d4"
CLR_MOISTURE = "#3b82f6"
CLR_FROST = "#8b5cf6"
CLR_SUN = "#f59e0b"
CLR_GROWING = "#22c55e"

INDEX_META = {
    "Thermal Comfort": {"color": CLR_THERMAL, "icon": "thermometer",
                        "desc": "Day-night temperature range modulated by aspect and elevation"},
    "Wind Exposure":   {"color": CLR_WIND, "icon": "flag",
                        "desc": "Exposure to prevailing winds based on terrain prominence"},
    "Moisture Regime": {"color": CLR_MOISTURE, "icon": "tint",
                        "desc": "Available moisture from precipitation and nearby water bodies"},
    "Frost Risk":      {"color": CLR_FROST, "icon": "snowflake-o",
                        "desc": "Likelihood of frost events from cold-air pooling and elevation"},
    "Sun Exposure":    {"color": CLR_SUN, "icon": "sun-o",
                        "desc": "Solar radiation potential based on aspect, latitude, and cloud cover"},
    "Growing Season":  {"color": CLR_GROWING, "icon": "leaf",
                        "desc": "Length and quality of the growing season from GDD and frost-free days"},
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


def _safe_max(values: list, default: float = 0.0) -> float:
    cleaned = [v for v in (values or []) if v is not None]
    return max(cleaned) if cleaned else default


def _safe_min(values: list, default: float = 0.0) -> float:
    cleaned = [v for v in (values or []) if v is not None]
    return min(cleaned) if cleaned else default


def _index_label(score: float) -> str:
    if score >= 80:
        return "Very High"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Low"
    return "Very Low"


# =============================================================================
# MICROCLIMATE COMPUTATION
# =============================================================================

@st.cache_data(ttl=1800)
def compute_microclimate(lat: float, lon: float) -> dict:
    """
    Compute a comprehensive microclimate assessment for the given location.

    Returns
    -------
    dict with keys:
        indices            - dict of 6 index scores (0-100)
        aspect_info        - dict describing dominant slope aspect
        terrain            - dict of terrain characteristics
        weather_summary    - dict of weather metrics
        microclimate_class - str classification
        recommendations    - list[str]
    """

    # -- Fetch data sources ---------------------------------------------------
    weather = fetch_weather_data(lat, lon)
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=8)
    water = fetch_water_features(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)

    # -- Parse elevation grid -------------------------------------------------
    elev = elev or {}
    elevations = (elev).get("grid_elevations", [])
    center_elev = (elev).get("center_elevation", 0.0)
    min_elev = (elev).get("min_elevation", 0.0)
    max_elev = (elev).get("max_elevation", 0.0)
    avg_elev = (elev).get("avg_elevation", 0.0)
    ns_profile = (elev).get("ns_profile", [])
    ew_profile = (elev).get("ew_profile", [])

    terrain_relief = max_elev - min_elev if max_elev and min_elev else 0.0
    elevation_prominence = center_elev - avg_elev if center_elev and avg_elev else 0.0

    # -- Aspect analysis (N/S/E/W slope facing) ------------------------------
    north_avg = _safe_mean([p.get("elevation", 0) for p in ns_profile[:len(ns_profile) // 2]])
    south_avg = _safe_mean([p.get("elevation", 0) for p in ns_profile[len(ns_profile) // 2 + 1:]])
    west_avg = _safe_mean([p.get("elevation", 0) for p in ew_profile[:len(ew_profile) // 2]])
    east_avg = _safe_mean([p.get("elevation", 0) for p in ew_profile[len(ew_profile) // 2 + 1:]])

    # Slope direction: higher terrain to the X means the site faces away from X
    aspect_scores = {
        "North": max(0, south_avg - center_elev),
        "South": max(0, north_avg - center_elev),
        "East":  max(0, west_avg - center_elev),
        "West":  max(0, east_avg - center_elev),
    }
    dominant_aspect = max(aspect_scores, key=aspect_scores.get) if any(v > 0 for v in aspect_scores.values()) else "Flat"
    # In N hemisphere, S-facing = warm; in S hemisphere, N-facing = warm
    is_north_hemisphere = lat >= 0
    warm_facing = (dominant_aspect == "South") if is_north_hemisphere else (dominant_aspect == "North")

    aspect_info = {
        "dominant": dominant_aspect,
        "warm_facing": warm_facing,
        "scores": aspect_scores,
        "is_north_hemisphere": is_north_hemisphere,
    }

    # -- Wind exposure --------------------------------------------------------
    # Higher prominence = more exposed to wind
    wind_exposure_raw = 50 + elevation_prominence * 2.0
    # Open terrain (low relief) also means more exposure
    if terrain_relief < 20:
        wind_exposure_raw += 15

    # -- Cold air pooling -----------------------------------------------------
    # If center is lower than surroundings, cold air pools here at night
    is_valley = elevation_prominence < -5
    cold_pool_factor = max(0, -elevation_prominence) * 3.0

    # -- Rain shadow ----------------------------------------------------------
    # If high terrain to the west (prevailing wind direction), rain shadow effect
    rain_shadow = max(0, west_avg - center_elev) * 0.5 if west_avg else 0.0

    terrain = {
        "center_elevation": round(center_elev, 1),
        "terrain_relief": round(terrain_relief, 1),
        "elevation_prominence": round(elevation_prominence, 1),
        "is_valley": is_valley,
        "cold_pool_factor": round(cold_pool_factor, 1),
        "rain_shadow": round(rain_shadow, 1),
    }

    # -- Water features -------------------------------------------------------
    water_elements = (water or {}).get("elements", [])
    water_count = len(water_elements) if isinstance(water_elements, list) else 0
    humidity_modifier = min(30, water_count * 5)
    frost_reduction = min(20, water_count * 4)

    # -- Infrastructure (urban heat island) -----------------------------------
    infra_elements = (infra or {}).get("elements", [])
    building_count = 0
    if isinstance(infra_elements, list):
        for el in infra_elements:
            tags = el.get("tags", {})
            if isinstance(tags, dict) and tags.get("building"):
                building_count += 1
    urban_heat = min(25, building_count * 0.5)

    # -- Weather extraction ---------------------------------------------------
    current = (weather or {}).get("current", {})
    daily = (weather or {}).get("daily", {})

    temp_now = current.get("temperature_2m", 15.0) or 15.0
    humidity = current.get("relative_humidity_2m", 50.0) or 50.0
    wind_speed = current.get("wind_speed_10m", 10.0) or 10.0
    cloud_cover = current.get("cloud_cover", 50.0) or 50.0
    precip_now = current.get("precipitation", 0.0) or 0.0

    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    precip_sums = daily.get("precipitation_sum", [])

    avg_max = _safe_mean(temps_max) if temps_max else temp_now + 5
    avg_min = _safe_mean(temps_min) if temps_min else temp_now - 5
    diurnal_range = avg_max - avg_min
    total_precip = sum(v for v in precip_sums if v is not None) if precip_sums else 0.0

    # Growing degree days estimate (base 5C, 7-day projection)
    gdd_daily = max(0, ((avg_max + avg_min) / 2.0) - 5.0)
    gdd_estimate = gdd_daily * 7.0

    # Frost-free days estimate from min temps
    frost_days = sum(1 for t in temps_min if t is not None and t <= 0)
    forecast_days = max(1, len(temps_min)) if temps_min else 7
    frost_free_ratio = 1.0 - (frost_days / forecast_days)

    weather_summary = {
        "temperature": round(temp_now, 1),
        "humidity": round(humidity, 1),
        "wind_speed": round(wind_speed, 1),
        "cloud_cover": round(cloud_cover, 1),
        "diurnal_range": round(diurnal_range, 1),
        "total_precip_7d": round(total_precip, 1),
        "gdd_7d": round(gdd_estimate, 1),
        "frost_free_ratio": round(frost_free_ratio, 2),
        "avg_max": round(avg_max, 1),
        "avg_min": round(avg_min, 1),
    }

    # =========================================================================
    # COMPUTE 6 MICROCLIMATE INDICES (0 - 100)
    # =========================================================================

    # 1. Thermal Comfort -- best when diurnal range is moderate, warm-facing, not too high
    thermal = 60.0
    thermal -= abs(diurnal_range - 10) * 1.5          # ideal ~10C range
    if warm_facing:
        thermal += 15
    thermal -= max(0, center_elev - 800) * 0.01       # high elevation = cooler
    thermal += urban_heat * 0.5                        # UHI warms
    thermal = _clamp(thermal)

    # 2. Wind Exposure -- higher is more exposed
    wind_idx = _clamp(wind_exposure_raw + wind_speed * 0.8)

    # 3. Moisture Regime -- higher = more moisture available
    moisture = 30.0
    moisture += min(40, total_precip * 2.0)
    moisture += humidity_modifier
    moisture -= rain_shadow * 0.5
    moisture += humidity * 0.15
    moisture = _clamp(moisture)

    # 4. Frost Risk -- higher = greater risk of frost
    frost = 20.0
    frost += cold_pool_factor
    frost -= frost_reduction
    frost += max(0, -avg_min) * 3.0
    frost += max(0, center_elev - 500) * 0.02
    frost -= urban_heat * 0.8   # cities stay warmer
    frost = _clamp(frost)

    # 5. Sun Exposure -- higher = more solar radiation
    sun = 50.0
    sun += (100.0 - cloud_cover) * 0.3
    if warm_facing:
        sun += 15
    # Lower latitudes get more sun
    sun += max(0, 30 - abs(lat)) * 0.5
    sun -= max(0, center_elev - 2000) * 0.005  # very high = more cloud/fog
    sun = _clamp(sun)

    # 6. Growing Season -- higher = longer/better growing season
    growing = 30.0
    growing += min(40, gdd_estimate * 0.3)
    growing += frost_free_ratio * 25
    growing += min(10, total_precip * 0.5)
    growing -= max(0, center_elev - 1000) * 0.015
    growing = _clamp(growing)

    indices = {
        "Thermal Comfort": round(thermal, 1),
        "Wind Exposure":   round(wind_idx, 1),
        "Moisture Regime": round(moisture, 1),
        "Frost Risk":      round(frost, 1),
        "Sun Exposure":    round(sun, 1),
        "Growing Season":  round(growing, 1),
    }

    # =========================================================================
    # MICROCLIMATE CLASSIFICATION
    # =========================================================================

    if water_count > 5 and abs(lat) < 50 and center_elev < 100:
        mc_class = "Coastal"
    elif building_count > 30:
        mc_class = "Urban"
    elif center_elev > 1500:
        mc_class = "Alpine"
    elif is_valley and moisture > 55:
        mc_class = "Valley"
    elif diurnal_range > 15 and moisture < 40:
        mc_class = "Continental"
    elif diurnal_range < 10 and moisture > 50:
        mc_class = "Maritime"
    else:
        mc_class = "Continental"

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================

    recommendations = []

    if frost > 60:
        recommendations.append(
            "HIGH FROST RISK: This location is prone to frost events due to cold-air pooling "
            "and elevation. Use frost blankets, select frost-tolerant cultivars, and consider "
            "wind machines or smudge pots for high-value crops."
        )
    elif frost > 35:
        recommendations.append(
            "Moderate frost risk detected. Monitor overnight lows closely during transition "
            "seasons. Mulching and row covers can mitigate light frost damage."
        )

    if wind_idx > 70:
        recommendations.append(
            "HIGH WIND EXPOSURE: The site is prominently elevated and exposed. "
            "Install windbreaks (hedgerows or fencing) and select wind-resistant species. "
            "Structures should be anchored to withstand sustained gusts."
        )
    elif wind_idx > 45:
        recommendations.append(
            "Moderate wind exposure. Consider planting shelterbelts on the windward side "
            "to reduce wind stress on crops and reduce evapotranspiration."
        )

    if moisture < 30:
        recommendations.append(
            "LOW MOISTURE: Dry conditions prevail. Implement drip irrigation, "
            "apply organic mulch to conserve soil moisture, and choose drought-adapted species."
        )
    elif moisture > 75:
        recommendations.append(
            "High moisture regime. Ensure adequate drainage to prevent waterlogging. "
            "Select species tolerant of wet soils and monitor for fungal diseases."
        )

    if sun > 75:
        recommendations.append(
            "Excellent sun exposure for solar-dependent crops. Take advantage of the "
            "warm aspect for heat-loving cultivars (tomatoes, peppers, grapes)."
        )
    elif sun < 30:
        recommendations.append(
            "Limited sun exposure. Focus on shade-tolerant species and consider "
            "reflective mulch to maximize available light."
        )

    if growing > 70:
        recommendations.append(
            "Strong growing season potential. Long frost-free period and adequate GDD "
            "support a wide range of crops including warm-season varieties."
        )
    elif growing < 30:
        recommendations.append(
            "Short growing season. Focus on fast-maturing cultivars and consider "
            "season extension techniques (cold frames, polytunnels)."
        )

    if not recommendations:
        recommendations.append(
            "Conditions are generally balanced. Standard agricultural and land management "
            "practices should perform well at this location."
        )

    return {
        "indices": indices,
        "aspect_info": aspect_info,
        "terrain": terrain,
        "weather_summary": weather_summary,
        "microclimate_class": mc_class,
        "recommendations": recommendations,
    }


# =============================================================================
# CHART BUILDERS
# =============================================================================

def _build_radar_chart(indices: dict) -> go.Figure:
    """Build a radar (scatterpolar) chart of the 6 microclimate indices."""
    labels = list(indices.keys())
    values = list(indices.values())
    colors = [INDEX_META[k]["color"] for k in labels]

    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(6,182,212,0.15)",
        line={"color": CLR_ACCENT, "width": 2.5},
        marker={"size": 8, "color": colors + [colors[0]]},
        hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
    ))

    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True, "range": [0, 100],
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
                "gridcolor": "#2a3550",
            },
            "angularaxis": {
                "tickfont": {"color": CLR_TEXT, "size": 12},
                "gridcolor": "#2a3550",
            },
            "bgcolor": CLR_BG,
        },
        height=420,
        margin=dict(l=60, r=60, t=40, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
        showlegend=False,
    )
    return fig


def _build_aspect_chart(aspect_info: dict) -> go.Figure:
    """Build a polar bar (rose) chart showing slope aspect magnitudes."""
    scores = aspect_info.get("scores", {})
    directions = ["North", "East", "South", "West"]
    values = [scores.get(d, 0) for d in directions]
    dir_colors = ["#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]

    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=values,
        theta=directions,
        marker={"color": dir_colors, "line": {"color": CLR_TEXT, "width": 1}},
        opacity=0.85,
        hovertemplate="Aspect %{theta}: %{r:.1f} m<extra></extra>",
    ))

    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True,
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
                "gridcolor": "#2a3550",
            },
            "angularaxis": {
                "tickfont": {"color": CLR_TEXT, "size": 12},
                "gridcolor": "#2a3550",
                "direction": "clockwise",
                "rotation": 90,
            },
            "bgcolor": CLR_BG,
        },
        height=370,
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
        showlegend=False,
    )
    return fig


# =============================================================================
# RENDER
# =============================================================================

def render_microclimate_tab():
    """Render the Microclimate Intelligence tab in the Streamlit UI."""

    # -- Header ---------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Microclimate Intelligence AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Analyse local microclimate conditions from terrain aspect, elevation,
                water proximity, and urban density to guide land-use decisions.
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
            key="mc_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="mc_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="mc_lon",
        )

    run_btn = st.button(
        "Analyze Microclimate",
        type="primary",
        key="mc_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Analyze Microclimate** to begin.")
        return

    # -- Run analysis ---------------------------------------------------------
    with st.spinner("Fetching terrain, weather, and infrastructure data..."):
        result = compute_microclimate(lat, lon)

    indices = result["indices"]
    aspect_info = result["aspect_info"]
    terrain = result["terrain"]
    ws = result["weather_summary"]
    mc_class = result["microclimate_class"]
    recommendations = result["recommendations"]

    # -- Classification header ------------------------------------------------
    class_colors = {
        "Maritime": "#3b82f6", "Continental": "#f59e0b", "Alpine": "#8b5cf6",
        "Urban": "#ef4444", "Valley": "#22c55e", "Coastal": "#06b6d4",
    }
    cls_clr = class_colors.get(mc_class, CLR_ACCENT)

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{cls_clr}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {cls_clr}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};text-transform:uppercase;
                                 letter-spacing:1px;">Microclimate Classification</span>
                    <h1 style="margin:4px 0;color:{cls_clr};font-size:42px;">
                        {escape(mc_class)}
                    </h1>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};">
                        Dominant aspect: {escape(aspect_info['dominant'])}
                        {'(warm-facing)' if aspect_info['warm_facing'] else '(cool-facing)'}
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Elevation: {terrain['center_elevation']:.0f} m<br>
                        Relief: {terrain['terrain_relief']:.0f} m
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Radar chart ----------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Microclimate Index Profile
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    radar_fig = _build_radar_chart(indices)
    st.plotly_chart(radar_fig, use_container_width=True, key="mc_radar")

    # -- Index cards (3 columns x 2 rows) -------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">Index Breakdown</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    index_keys = list(indices.keys())
    for row_start in range(0, len(index_keys), 3):
        row_keys = index_keys[row_start:row_start + 3]
        cols = st.columns(len(row_keys))
        for col, key in zip(cols, row_keys):
            val = indices[key]
            meta = INDEX_META[key]
            clr = meta["color"]
            label = _index_label(val)
            bar_w = max(5, val)
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {clr}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:190px;">
                        <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                            {escape(key)}
                        </div>
                        <div style="font-size:36px;font-weight:700;color:{clr};">
                            {val}
                        </div>
                        <div style="font-size:12px;color:{clr};font-weight:600;
                                    margin-bottom:8px;">
                            {escape(label)}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                    margin:8px 0;">
                            <div style="background:{clr};width:{bar_w}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:6px;">
                            {escape(meta['desc'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Terrain aspect visualisation -----------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Terrain Aspect (Slope Direction)
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    aspect_fig = _build_aspect_chart(aspect_info)
    st.plotly_chart(aspect_fig, use_container_width=True, key="mc_aspect")

    # -- Weather summary metrics row ------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">Weather Summary</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    metric_data = [
        (m1, "Temperature", f"{ws['temperature']}C", CLR_THERMAL),
        (m2, "Humidity", f"{ws['humidity']}%", CLR_MOISTURE),
        (m3, "Wind", f"{ws['wind_speed']} km/h", CLR_WIND),
        (m4, "Diurnal Range", f"{ws['diurnal_range']}C", CLR_SUN),
        (m5, "Precip (7d)", f"{ws['total_precip_7d']} mm", CLR_FROST),
        (m6, "GDD (7d)", f"{ws['gdd_7d']}", CLR_GROWING),
    ]
    for col, title, value, color in metric_data:
        with col:
            st.markdown(
                f"""
                <div style="background:{CLR_CARD};border:1px solid {color}44;
                            border-radius:10px;padding:14px;text-align:center;">
                    <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-bottom:4px;">
                        {escape(title)}
                    </div>
                    <div style="font-size:22px;font-weight:700;color:{color};">
                        {escape(str(value))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -- Recommendations ------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">Recommendations</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for rec in recommendations:
        is_alert = rec.startswith("HIGH")
        rec_clr = CLR_THERMAL if is_alert else CLR_ACCENT
        st.markdown(
            f"""
            <div style="background:{CLR_CARD};border-left:4px solid {rec_clr};
                        border-radius:0 8px 8px 0;padding:14px 18px;margin:8px 0;">
                <p style="margin:0;color:{CLR_TEXT};font-size:14px;line-height:1.6;">
                    {escape(rec)}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
