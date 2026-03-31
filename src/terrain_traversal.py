"""
Terrain Traversability AI module for TerraScout AI.
Analyzes how traversable terrain is for different movement types
(walking, cycling, vehicle, off-road, heavy vehicle) by combining
elevation, soil, weather, water, and infrastructure data.
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
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# =============================================================================
# MOVEMENT TYPE DEFINITIONS
# =============================================================================

MOVEMENT_TYPES = {
    "walking": {
        "label": "Walking / Hiking",
        "icon": "\U0001F6B6",
        "color": "#22c55e",
        "max_slope_pct": 40,
        "needs_roads": False,
        "weather_sensitivity": 0.3,
        "description": "On foot across varied terrain",
    },
    "cycling": {
        "label": "Cycling",
        "icon": "\U0001F6B2",
        "color": "#06b6d4",
        "max_slope_pct": 15,
        "needs_roads": True,
        "weather_sensitivity": 0.5,
        "description": "Bicycle on roads and paths",
    },
    "vehicle": {
        "label": "Standard Vehicle",
        "icon": "\U0001F697",
        "color": "#3b82f6",
        "max_slope_pct": 12,
        "needs_roads": True,
        "weather_sensitivity": 0.2,
        "description": "Car or van on paved roads",
    },
    "off_road": {
        "label": "Off-Road Vehicle",
        "icon": "\U0001F6FB",
        "color": "#f59e0b",
        "max_slope_pct": 25,
        "needs_roads": False,
        "weather_sensitivity": 0.4,
        "description": "4x4 / SUV across rough terrain",
    },
    "heavy_vehicle": {
        "label": "Heavy Vehicle",
        "icon": "\U0001F69A",
        "color": "#ef4444",
        "max_slope_pct": 8,
        "needs_roads": True,
        "weather_sensitivity": 0.15,
        "description": "Truck or large transport on roads",
    },
}

# =============================================================================
# HELPER: COMPUTE SLOPE FROM ELEVATION GRID
# =============================================================================

def _compute_slope_pct(elevation_data: dict) -> float:
    """Return average slope percentage from an elevation grid."""
    elevs = [e for e in elevation_data.get("grid_elevations", []) if e is not None]
    if len(elevs) < 2:
        return 0.0
    elev_min = min(elevs)
    elev_max = max(elevs)
    elev_range = elev_max - elev_min
    # Approximate horizontal distance from grid span
    lats = [la for la in elevation_data.get("grid_lats", []) if la is not None]
    lons = [lo for lo in elevation_data.get("grid_lons", []) if lo is not None]
    if not lats or not lons:
        return 0.0
    lat_span = max(lats) - min(lats)
    lon_span = max(lons) - min(lons)
    horiz_deg = math.sqrt(lat_span ** 2 + lon_span ** 2)
    horiz_m = horiz_deg * 111_320  # rough metres per degree
    if horiz_m < 1:
        return 0.0
    return (elev_range / horiz_m) * 100.0


# =============================================================================
# MAIN COMPUTATION
# =============================================================================

@st.cache_data(ttl=1800)
def compute_traversability(lat: float, lon: float) -> dict:
    """Analyse terrain traversability for every movement type at (lat, lon)."""

    # -- Fetch all data sources ------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon, radius=3000)
    elevation = fetch_elevation_grid(lat, lon, grid_size=8, radius_deg=0.04)
    infra = fetch_landuse_infrastructure(lat, lon, radius=3000)

    # -- Terrain analysis ------------------------------------------------------
    slope_pct = _compute_slope_pct(elevation)

    # Soil surface estimate
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    sand_pct = _sv("sand") or 0
    clay_pct = _sv("clay") or 0

    if sand_pct > 50:
        surface_type = "sandy"
        surface_quality = 55
    elif clay_pct > 40:
        surface_type = "clay"
        surface_quality = 60
    else:
        surface_type = "loam"
        surface_quality = 80

    # Obstacle density -- water features
    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    water_crossings = sum(
        1 for el in water_elements
        if el.get("tags", {}).get("waterway") in ("river", "stream", "canal")
    )

    # Dense-vegetation proxy (forest / scrub land use)
    infra_elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    dense_veg_count = sum(
        1 for el in infra_elements
        if el.get("tags", {}).get("landuse") in ("forest",)
        or el.get("tags", {}).get("natural") in ("wood", "scrub")
    )

    obstacles: list[dict] = []
    if water_crossings:
        obstacles.append({"type": "water_crossing", "count": water_crossings,
                          "severity": min(water_crossings * 15, 50)})
    if dense_veg_count:
        obstacles.append({"type": "dense_vegetation", "count": dense_veg_count,
                          "severity": min(dense_veg_count * 10, 40)})

    total_obstacle_penalty = sum(o["severity"] for o in obstacles)

    # -- Weather impact --------------------------------------------------------
    current = {}
    if isinstance(weather, dict):
        current = weather.get("current", {}) or weather.get("current_weather", {}) or {}

    temperature = current.get("temperature_2m") or current.get("temperature") or 20.0
    wind_speed = current.get("wind_speed_10m") or current.get("windspeed") or 0.0

    # Detect rain from weather code (WMO codes 51-67, 80-82 = rain/drizzle)
    w_code = current.get("weather_code") or current.get("weathercode") or 0
    is_raining = w_code in range(51, 68) or w_code in range(80, 83)

    weather_penalty = 0
    weather_notes: list[str] = []

    if is_raining:
        weather_penalty += 15
        weather_notes.append("Rain reduces traction on unpaved surfaces")
        if surface_type == "clay":
            weather_penalty += 10
            weather_notes.append("Clay soil becomes very slippery when wet")

    if wind_speed > 40:
        weather_penalty += 10
        weather_notes.append(f"Strong wind ({wind_speed:.0f} km/h) affects stability")
    elif wind_speed > 25:
        weather_penalty += 5
        weather_notes.append(f"Moderate wind ({wind_speed:.0f} km/h)")

    if temperature > 40 or temperature < -10:
        weather_penalty += 10
        weather_notes.append(f"Extreme temperature ({temperature:.1f} C) affects endurance")
    elif temperature > 35 or temperature < 0:
        weather_penalty += 5
        weather_notes.append(f"Challenging temperature ({temperature:.1f} C)")

    # -- Infrastructure --------------------------------------------------------
    road_types: dict[str, int] = {}
    bridge_count = 0
    for el in infra_elements:
        tags = el.get("tags", {})
        hw = tags.get("highway")
        if hw:
            road_types[hw] = road_types.get(hw, 0) + 1
        if tags.get("bridge") == "yes" or tags.get("man_made") == "bridge":
            bridge_count += 1

    paved_roads = sum(
        road_types.get(rt, 0)
        for rt in ("motorway", "trunk", "primary", "secondary", "tertiary",
                    "residential", "service")
    )
    unpaved_roads = sum(road_types.get(rt, 0) for rt in ("track", "path", "footway"))
    has_roads = paved_roads > 0
    has_paths = unpaved_roads > 0

    # Bridges mitigate water-crossing obstacles
    effective_water_penalty = max(0, water_crossings - bridge_count) * 12

    # -- Elevation stats -------------------------------------------------------
    elevs_clean = [e for e in elevation.get("grid_elevations", []) if e is not None]
    elev_min = min(elevs_clean) if elevs_clean else 0
    elev_max = max(elevs_clean) if elevs_clean else 0
    elev_avg = sum(elevs_clean) / len(elevs_clean) if elevs_clean else 0

    # -- Score each movement type 0-100 ----------------------------------------
    mode_scores: dict[str, dict] = {}

    for key, mt in MOVEMENT_TYPES.items():
        score = 100.0

        # 1) Slope penalty
        if slope_pct > mt["max_slope_pct"]:
            overshoot = slope_pct - mt["max_slope_pct"]
            score -= min(overshoot * 3, 50)
        elif slope_pct > mt["max_slope_pct"] * 0.6:
            score -= (slope_pct - mt["max_slope_pct"] * 0.6) * 1.5

        # 2) Surface / road availability
        if mt["needs_roads"]:
            if not has_roads:
                if has_paths and key == "cycling":
                    score -= 20
                else:
                    score -= 40
            else:
                # Bonus for good road network
                score += min(paved_roads * 0.5, 10)
        else:
            # Walking / off-road: surface quality matters
            score -= max(0, (80 - surface_quality) * 0.5)

        # 3) Weather modifier
        mode_weather = weather_penalty * mt["weather_sensitivity"]
        if key == "cycling" and wind_speed > 30:
            mode_weather += 10  # Extra wind penalty for cycling
        if key in ("walking",) and is_raining:
            mode_weather += 5   # Hiking in rain is less pleasant
        score -= mode_weather

        # 4) Obstacle penalty
        if key in ("vehicle", "heavy_vehicle"):
            score -= effective_water_penalty
        elif key == "off_road":
            score -= effective_water_penalty * 0.5
        elif key == "walking":
            score -= effective_water_penalty * 0.3
        else:
            score -= effective_water_penalty * 0.7

        # Dense vegetation penalty
        if key in ("vehicle", "heavy_vehicle", "cycling"):
            score -= min(dense_veg_count * 5, 20)
        elif key == "off_road":
            score -= min(dense_veg_count * 3, 15)

        # 5) Seasonal / temperature comfort
        if key == "walking" and 10 <= temperature <= 25:
            score += 5  # Ideal hiking weather
        if key == "cycling" and 15 <= temperature <= 28 and wind_speed < 15:
            score += 5  # Ideal cycling weather

        score = max(0, min(100, round(score)))
        mode_scores[key] = {
            "score": int(score),
            "label": mt["label"],
            "icon": mt["icon"],
            "color": mt["color"],
        }

    # -- Best mode recommendation ----------------------------------------------
    best_key = max(mode_scores, key=lambda k: mode_scores[k]["score"])
    best_mode = {
        "key": best_key,
        **mode_scores[best_key],
    }

    # -- Recommendations -------------------------------------------------------
    recommendations: list[str] = []
    if best_mode["score"] >= 80:
        recommendations.append(
            f"{best_mode['label']} is highly recommended for this terrain.")
    elif best_mode["score"] >= 50:
        recommendations.append(
            f"{best_mode['label']} is feasible but expect some challenges.")
    else:
        recommendations.append(
            "Terrain is difficult for all movement types. Plan carefully.")

    if slope_pct > 20:
        recommendations.append(
            f"Steep slopes ({slope_pct:.1f}%) detected -- consider switchback routes.")
    if is_raining and surface_type == "clay":
        recommendations.append(
            "Clay soil + rain creates hazardous conditions for wheeled transport.")
    if water_crossings > bridge_count:
        recommendations.append(
            f"{water_crossings - bridge_count} unbridged water crossing(s) found -- "
            "fording or detour may be needed.")
    if not has_roads and not has_paths:
        recommendations.append(
            "No mapped roads or paths -- only foot or off-road travel is practical.")

    terrain_summary = {
        "slope_pct": round(slope_pct, 1),
        "surface_type": surface_type,
        "surface_quality": surface_quality,
        "elevation_min": round(elev_min, 1),
        "elevation_max": round(elev_max, 1),
        "elevation_avg": round(elev_avg, 1),
        "paved_roads": paved_roads,
        "unpaved_roads": unpaved_roads,
        "bridges": bridge_count,
    }

    weather_impact = {
        "temperature": round(temperature, 1),
        "wind_speed": round(wind_speed, 1),
        "is_raining": is_raining,
        "penalty": weather_penalty,
        "notes": weather_notes,
    }

    return {
        "mode_scores": mode_scores,
        "terrain_summary": terrain_summary,
        "weather_impact": weather_impact,
        "best_mode": best_mode,
        "obstacles": obstacles,
        "recommendations": recommendations,
    }


# =============================================================================
# STREAMLIT RENDER
# =============================================================================

def render_terrain_traversal_tab():
    """Render the Terrain Traversability AI tab inside Streamlit."""

    st.markdown(
        "<h2 style='text-align:center;color:#22c55e;'>"
        "Terrain Traversability AI</h2>"
        "<p style='text-align:center;color:#aaa;'>"
        "Analyse how traversable terrain is for different movement types</p>",
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.4, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="tt_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50

    with col_lat:
        lat = st.number_input("Latitude", value=default_lat,
                              format="%.4f", key="tt_lat")
    with col_lon:
        lon = st.number_input("Longitude", value=default_lon,
                              format="%.4f", key="tt_lon")

    if not st.button("Analyze Traversability", type="primary", key="tt_run"):
        st.info("Select a location and press **Analyze Traversability** to begin.")
        return

    with st.spinner("Fetching terrain, soil, weather and infrastructure data..."):
        result = compute_traversability(lat, lon)

    mode_scores = result["mode_scores"]
    terrain = result["terrain_summary"]
    weather_imp = result["weather_impact"]
    best = result["best_mode"]
    obstacles = result["obstacles"]
    recs = result["recommendations"]

    # -- Best mode header ------------------------------------------------------
    st.markdown(
        f"<div style='background:linear-gradient(135deg,{best['color']}22,#1a1a2e);"
        f"border:1px solid {best['color']};border-radius:12px;padding:20px;"
        f"text-align:center;margin:16px 0;'>"
        f"<span style='font-size:2.5rem;'>{best['icon']}</span><br>"
        f"<span style='font-size:1.4rem;color:{best['color']};font-weight:700;'>"
        f"Best Mode: {best['label']}</span><br>"
        f"<span style='font-size:2rem;color:#fff;font-weight:800;'>"
        f"{best['score']} / 100</span></div>",
        unsafe_allow_html=True,
    )

    # -- Mode score cards ------------------------------------------------------
    st.subheader("Movement Mode Scores")
    cols = st.columns(len(MOVEMENT_TYPES))
    for idx, (key, ms) in enumerate(mode_scores.items()):
        with cols[idx]:
            score = ms["score"]
            if score >= 75:
                badge_bg = "rgba(34,197,94,0.2)"
            elif score >= 50:
                badge_bg = "rgba(245,158,11,0.2)"
            else:
                badge_bg = "rgba(239,68,68,0.2)"
            st.markdown(
                f"<div style='background:{badge_bg};border:1px solid {ms['color']};"
                f"border-radius:10px;padding:14px;text-align:center;'>"
                f"<span style='font-size:1.6rem;'>{ms['icon']}</span><br>"
                f"<span style='color:{ms['color']};font-weight:700;'>"
                f"{ms['label']}</span><br>"
                f"<span style='font-size:1.5rem;font-weight:800;color:#fff;'>"
                f"{score}</span></div>",
                unsafe_allow_html=True,
            )

    # -- Radar chart -----------------------------------------------------------
    st.subheader("Traversability Radar")
    labels = [ms["label"] for ms in mode_scores.values()]
    values = [ms["score"] for ms in mode_scores.values()]
    colors = [ms["color"] for ms in mode_scores.values()]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(34,197,94,0.15)",
        line=dict(color="#22c55e", width=2),
        marker=dict(color=colors + [colors[0]], size=8),
        name="Score",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor="#333", tickfont=dict(color="#aaa")),
            angularaxis=dict(gridcolor="#333", tickfont=dict(color="#ccc")),
        ),
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=400,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="tertra_pchart1")

    # -- Terrain factors -------------------------------------------------------
    st.subheader("Terrain Factors")
    tf1, tf2, tf3 = st.columns(3)
    with tf1:
        st.metric("Avg Slope", f"{terrain['slope_pct']}%")
        st.caption(
            "Gentle" if terrain["slope_pct"] < 8
            else "Moderate" if terrain["slope_pct"] < 20
            else "Steep"
        )
    with tf2:
        st.metric("Surface Type", terrain["surface_type"].title())
        st.caption(f"Quality score: {terrain['surface_quality']}/100")
    with tf3:
        obs_count = sum(o["count"] for o in obstacles) if obstacles else 0
        st.metric("Obstacles", obs_count)
        if obstacles:
            for o in obstacles:
                st.caption(
                    f"{o['type'].replace('_', ' ').title()}: {o['count']} "
                    f"(severity {o['severity']})")
        else:
            st.caption("No significant obstacles detected")

    elev_c1, elev_c2, elev_c3 = st.columns(3)
    with elev_c1:
        st.metric("Elevation Min", f"{terrain['elevation_min']} m")
    with elev_c2:
        st.metric("Elevation Max", f"{terrain['elevation_max']} m")
    with elev_c3:
        st.metric("Roads (paved / unpaved)",
                  f"{terrain['paved_roads']} / {terrain['unpaved_roads']}")

    # -- Weather impact --------------------------------------------------------
    st.subheader("Weather Impact")
    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        st.metric("Temperature", f"{weather_imp['temperature']} C")
    with wc2:
        st.metric("Wind Speed", f"{weather_imp['wind_speed']} km/h")
    with wc3:
        rain_label = "Yes -- surfaces affected" if weather_imp["is_raining"] else "No"
        st.metric("Raining", rain_label)

    if weather_imp["notes"]:
        for note in weather_imp["notes"]:
            st.warning(note)

    # -- Horizontal bar chart comparison ---------------------------------------
    st.subheader("Mode Comparison")
    bar_labels = [ms["label"] for ms in mode_scores.values()]
    bar_values = [ms["score"] for ms in mode_scores.values()]
    bar_colors = [ms["color"] for ms in mode_scores.values()]

    fig_bar = go.Figure(go.Bar(
        x=bar_values,
        y=bar_labels,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{v}" for v in bar_values],
        textposition="auto",
        textfont=dict(color="#fff"),
    ))
    fig_bar.update_layout(
        xaxis=dict(range=[0, 105], title="Traversability Score",
                   gridcolor="#333", tickfont=dict(color="#aaa"),
                   title_font=dict(color="#ccc")),
        yaxis=dict(tickfont=dict(color="#ccc"), autorange="reversed"),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        margin=dict(l=150, r=30, t=20, b=40),
        height=300,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="tertra_pchart2")

    # -- Recommendations -------------------------------------------------------
    st.subheader("Recommendations")
    for rec in recs:
        st.markdown(
            f"<div style='background:#1a1a2e;border-left:4px solid #22c55e;"
            f"padding:10px 16px;margin:6px 0;border-radius:4px;"
            f"color:#e0e0e0;'>{rec}</div>",
            unsafe_allow_html=True,
        )
