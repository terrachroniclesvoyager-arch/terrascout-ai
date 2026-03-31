"""
Habitat Suitability AI module for TerraScout AI.
Analyzes habitat suitability for different species groups and ecosystem types
by combining soil, weather, water, elevation, and biodiversity data from
multiple free APIs. Uses weighted scoring to determine how well a location
matches each of 8 canonical habitat profiles.
"""

import html as html_module
import logging
import math

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
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# HABITAT TYPE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

HABITAT_TYPES = {
    "temperate_forest": {
        "name": "Temperate Forest",
        "color": "#10b981",
        "icon": "\U0001F333",
        "ideal_temp_range": (5, 20),
        "ideal_precip_range": (600, 1500),
        "key_factors": [
            "moderate_soil_moisture",
            "tree_cover",
            "seasonal_variation",
            "moderate_elevation",
        ],
    },
    "tropical_forest": {
        "name": "Tropical Forest",
        "color": "#059669",
        "icon": "\U0001F334",
        "ideal_temp_range": (20, 30),
        "ideal_precip_range": (1500, 4000),
        "key_factors": [
            "high_humidity",
            "dense_vegetation",
            "low_elevation",
            "high_biodiversity",
        ],
    },
    "grassland": {
        "name": "Grassland",
        "color": "#84cc16",
        "icon": "\U0001F33E",
        "ideal_temp_range": (10, 25),
        "ideal_precip_range": (300, 900),
        "key_factors": [
            "low_slope",
            "moderate_soil_fertility",
            "open_terrain",
            "seasonal_drought",
        ],
    },
    "wetland": {
        "name": "Wetland",
        "color": "#3b82f6",
        "icon": "\U0001F4A7",
        "ideal_temp_range": (5, 30),
        "ideal_precip_range": (500, 2000),
        "key_factors": [
            "water_features_present",
            "high_clay_content",
            "low_elevation",
            "saturated_soil",
        ],
    },
    "desert": {
        "name": "Desert",
        "color": "#f59e0b",
        "icon": "\U0001F3DC\uFE0F",
        "ideal_temp_range": (25, 50),
        "ideal_precip_range": (0, 250),
        "key_factors": [
            "sandy_soil",
            "minimal_water",
            "extreme_temperature",
            "low_vegetation",
        ],
    },
    "alpine": {
        "name": "Alpine",
        "color": "#8b5cf6",
        "icon": "\U0001F3D4\uFE0F",
        "ideal_temp_range": (-10, 10),
        "ideal_precip_range": (500, 2000),
        "key_factors": [
            "high_elevation",
            "rocky_terrain",
            "steep_slope",
            "cold_adapted",
        ],
    },
    "coastal": {
        "name": "Coastal",
        "color": "#06b6d4",
        "icon": "\U0001F3D6\uFE0F",
        "ideal_temp_range": (10, 25),
        "ideal_precip_range": (400, 1200),
        "key_factors": [
            "near_water",
            "moderate_temp",
            "salt_tolerant",
            "tidal_influence",
        ],
    },
    "mediterranean": {
        "name": "Mediterranean",
        "color": "#ef4444",
        "icon": "\U0001F33B",
        "ideal_temp_range": (15, 25),
        "ideal_precip_range": (400, 800),
        "key_factors": [
            "dry_summers",
            "mild_winters",
            "sclerophyll_vegetation",
            "moderate_elevation",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _range_score(value, ideal_min, ideal_max):
    """Return 0-100 score for how well *value* falls within [ideal_min, ideal_max]."""
    if value is None:
        return 50.0
    if ideal_min <= value <= ideal_max:
        return 100.0
    if value < ideal_min:
        dist = ideal_min - value
        span = max(ideal_max - ideal_min, 1)
        return max(0.0, 100.0 - (dist / span) * 100.0)
    # value > ideal_max
    dist = value - ideal_max
    span = max(ideal_max - ideal_min, 1)
    return max(0.0, 100.0 - (dist / span) * 100.0)


def _compute_single_habitat_score(
    habitat_key,
    habitat_cfg,
    avg_temp,
    annual_precip,
    clay_pct,
    sand_pct,
    silt_pct,
    soil_moisture_proxy,
    center_elev,
    elev_range,
    water_count,
    humidity,
):
    """Compute a 0-100 suitability score for one habitat type."""
    temp_lo, temp_hi = habitat_cfg["ideal_temp_range"]
    precip_lo, precip_hi = habitat_cfg["ideal_precip_range"]

    temp_score = _range_score(avg_temp, temp_lo, temp_hi)
    precip_score = _range_score(annual_precip, precip_lo, precip_hi)

    # --- Soil characteristics ---
    soil_score = 50.0
    if habitat_key == "temperate_forest":
        # Prefers balanced texture, moderate moisture
        balance = 100.0 - abs((clay_pct or 30) - 30) - abs((silt_pct or 40) - 40)
        soil_score = max(0.0, min(100.0, balance + (soil_moisture_proxy or 0) * 2))
    elif habitat_key == "tropical_forest":
        # Deep weathered soils, low sand
        soil_score = max(0.0, 100.0 - (sand_pct or 30) * 1.5 + (clay_pct or 30) * 0.5)
    elif habitat_key == "grassland":
        # Fertile loam
        if silt_pct is not None and clay_pct is not None:
            loam = min(silt_pct, 50) + min(clay_pct, 30)
            soil_score = min(100.0, loam * 2)
        else:
            soil_score = 50.0
    elif habitat_key == "wetland":
        # High clay, low drainage
        soil_score = min(100.0, (clay_pct or 20) * 2.5)
    elif habitat_key == "desert":
        # Sandy
        soil_score = min(100.0, (sand_pct or 30) * 1.8)
    elif habitat_key == "alpine":
        # Rocky, low organic
        soil_score = max(0.0, 100.0 - (clay_pct or 20) * 2)
    elif habitat_key == "coastal":
        # Sandy-silt mix
        if sand_pct is not None and silt_pct is not None:
            soil_score = min(100.0, sand_pct + silt_pct)
        else:
            soil_score = 50.0
    elif habitat_key == "mediterranean":
        # Rocky-loam
        soil_score = 50.0
        if clay_pct is not None:
            soil_score = max(0.0, 100.0 - abs(clay_pct - 25) * 2)

    soil_score = max(0.0, min(100.0, soil_score))

    # --- Terrain match ---
    terrain_score = 50.0
    if habitat_key == "alpine":
        terrain_score = min(100.0, max(0.0, (center_elev - 1000) / 20.0)) if center_elev else 0.0
    elif habitat_key == "wetland":
        terrain_score = max(0.0, 100.0 - (center_elev or 200) * 0.3)
    elif habitat_key == "coastal":
        terrain_score = max(0.0, 100.0 - (center_elev or 100) * 0.5)
    elif habitat_key == "desert":
        # Flat terrain favoured
        terrain_score = max(0.0, 100.0 - (elev_range or 50) * 0.5)
    elif habitat_key == "grassland":
        terrain_score = max(0.0, 100.0 - (elev_range or 50) * 0.8)
    elif habitat_key in ("temperate_forest", "tropical_forest"):
        # Moderate elevation ok
        if center_elev is not None:
            if center_elev < 2500:
                terrain_score = min(100.0, 80.0 + center_elev * 0.01)
            else:
                terrain_score = max(0.0, 100.0 - (center_elev - 2500) * 0.1)
        else:
            terrain_score = 60.0
    elif habitat_key == "mediterranean":
        # Low-to-moderate elevation
        terrain_score = max(0.0, 100.0 - abs((center_elev or 300) - 300) * 0.1)

    terrain_score = max(0.0, min(100.0, terrain_score))

    # --- Water availability ---
    water_score = 50.0
    if habitat_key == "wetland":
        water_score = min(100.0, water_count * 10)
    elif habitat_key == "coastal":
        water_score = min(100.0, water_count * 8)
    elif habitat_key == "desert":
        water_score = max(0.0, 100.0 - water_count * 15)
    elif habitat_key == "tropical_forest":
        water_score = min(100.0, 40.0 + water_count * 5 + (humidity or 50) * 0.5)
    elif habitat_key == "temperate_forest":
        water_score = min(100.0, 30.0 + water_count * 4)
    elif habitat_key == "grassland":
        water_score = min(100.0, 40.0 + water_count * 3)
    elif habitat_key == "alpine":
        water_score = min(100.0, 30.0 + water_count * 3)
    elif habitat_key == "mediterranean":
        # Moderate water
        water_score = min(100.0, 50.0 + water_count * 3)

    water_score = max(0.0, min(100.0, water_score))

    # Weighted combination
    total = (
        temp_score * 0.30
        + precip_score * 0.25
        + soil_score * 0.20
        + terrain_score * 0.15
        + water_score * 0.10
    )
    return round(max(0.0, min(100.0, total)), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN COMPUTE FUNCTION (CACHED)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_habitat_suitability(lat, lon):
    """
    Fetch environmental data and compute suitability scores for all 8 habitat
    types.  Returns a dict with best_habitat, habitat_scores,
    biodiversity_summary, environmental_conditions, and recommendations.
    """
    # ── Fetch data ────────────────────────────────────────────────────────────
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    inat = fetch_biodiversity(lat, lon)
    gbif = fetch_gbif_occurrences(lat, lon)

    # ── Parse soil ────────────────────────────────────────────────────────────
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay_pct = _sv("clay")
    sand_pct = _sv("sand")
    silt_pct = _sv("silt")
    soc_val = _sv("soc")
    ph_val = _sv("phh2o")
    nitrogen_val = _sv("nitrogen", div=100)
    cec_val = _sv("cec")

    # Soil moisture proxy from organic carbon + clay
    soil_moisture_proxy = 0.0
    if clay_pct is not None and soc_val is not None:
        soil_moisture_proxy = clay_pct * 0.5 + soc_val * 2.0

    # ── Parse weather ─────────────────────────────────────────────────────────
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}

    temp_now = current.get("temperature_2m", 15)
    humidity = current.get("relative_humidity_2m", 50)
    daily_max = daily.get("temperature_2m_max", [])
    daily_min = daily.get("temperature_2m_min", [])
    daily_precip = daily.get("precipitation_sum", [])

    if daily_max and daily_min:
        all_temps = daily_max + daily_min
        avg_temp = sum(all_temps) / len(all_temps)
    else:
        avg_temp = temp_now

    if daily_precip:
        total_7d = sum(daily_precip)
        annual_precip = total_7d * (365.0 / max(len(daily_precip), 1))
    else:
        annual_precip = 500.0

    # ── Parse elevation ───────────────────────────────────────────────────────
    center_elev = elevation.get("center_elevation", 0)
    elev_range = (
        elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
    )
    avg_elev = elevation.get("avg_elevation", center_elev)

    # ── Parse water ───────────────────────────────────────────────────────────
    water_elements = water.get("elements", []) if isinstance(water, dict) else []
    water_count = len(water_elements)

    # ── Biodiversity ──────────────────────────────────────────────────────────
    bio_summary = compute_species_breakdown(inat, gbif)

    # ── Compute scores ────────────────────────────────────────────────────────
    habitat_scores = {}
    for hkey, hcfg in HABITAT_TYPES.items():
        score = _compute_single_habitat_score(
            hkey, hcfg,
            avg_temp, annual_precip,
            clay_pct, sand_pct, silt_pct,
            soil_moisture_proxy,
            center_elev, elev_range,
            water_count, humidity,
        )
        habitat_scores[hkey] = score

    # Determine best habitat
    if not habitat_scores:
        habitat_scores["temperate_forest"] = 50
    best_key = max(habitat_scores, key=habitat_scores.get)
    best_cfg = HABITAT_TYPES[best_key]
    best_score = habitat_scores[best_key]

    # ── Environmental conditions summary ──────────────────────────────────────
    environmental_conditions = {
        "temperature_c": round(avg_temp, 1),
        "humidity_pct": humidity,
        "annual_precip_mm": round(annual_precip, 0),
        "center_elevation_m": round(center_elev, 1),
        "elevation_range_m": round(elev_range, 1),
        "avg_elevation_m": round(avg_elev, 1),
        "water_feature_count": water_count,
        "clay_pct": round(clay_pct, 1) if clay_pct is not None else None,
        "sand_pct": round(sand_pct, 1) if sand_pct is not None else None,
        "silt_pct": round(silt_pct, 1) if silt_pct is not None else None,
        "soil_organic_carbon": round(soc_val, 2) if soc_val is not None else None,
        "soil_ph": round(ph_val, 1) if ph_val is not None else None,
        "nitrogen_g_kg": round(nitrogen_val, 2) if nitrogen_val is not None else None,
        "cec_cmol_kg": round(cec_val, 1) if cec_val is not None else None,
    }

    # ── Recommendations ───────────────────────────────────────────────────────
    recommendations = _build_recommendations(
        best_key, best_score, habitat_scores, environmental_conditions, bio_summary
    )

    return {
        "best_habitat": {
            "key": best_key,
            "name": best_cfg["name"],
            "icon": best_cfg["icon"],
            "color": best_cfg["color"],
            "score": best_score,
        },
        "habitat_scores": habitat_scores,
        "biodiversity_summary": bio_summary,
        "environmental_conditions": environmental_conditions,
        "recommendations": recommendations,
    }


def _build_recommendations(best_key, best_score, scores, env, bio):
    """Generate human-readable recommendations based on analysis results."""
    recs = []

    best_name = HABITAT_TYPES[best_key]["name"]
    recs.append(
        f"This location most closely matches a **{best_name}** habitat "
        f"with a suitability score of {best_score:.0f}/100."
    )

    # Temperature-based recommendations
    temp = env.get("temperature_c", 15)
    if temp < 5:
        recs.append(
            "Cold temperatures suggest cold-adapted species dominate. "
            "Consider frost-resistant plantings and winter shelter for wildlife."
        )
    elif temp > 30:
        recs.append(
            "High temperatures indicate a heat-stressed environment. "
            "Shade structures and water sources are critical for biodiversity."
        )

    # Water availability
    wc = env.get("water_feature_count", 0)
    if wc == 0:
        recs.append(
            "No water features detected nearby. Artificial water sources would "
            "significantly improve habitat value for most species groups."
        )
    elif wc > 15:
        recs.append(
            "Abundant water features provide excellent hydrology support. "
            "Wetland and riparian species are likely well-supported."
        )

    # Elevation
    elev = env.get("center_elevation_m", 0)
    if elev > 2000:
        recs.append(
            "High elevation site suited for alpine-adapted species. "
            "Consider erosion control and cold-climate restoration practices."
        )
    elif elev < 10:
        recs.append(
            "Very low elevation increases flood and storm surge risk. "
            "Coastal buffer planting and wetland restoration recommended."
        )

    # Biodiversity context
    inat_total = bio.get("inat_total", 0)
    gbif_unique = bio.get("gbif_unique_species", 0)
    if inat_total > 100:
        recs.append(
            f"Rich biodiversity detected ({inat_total} iNaturalist observations, "
            f"{gbif_unique} unique GBIF species). Conservation priority area."
        )
    elif inat_total < 10:
        recs.append(
            "Low recorded biodiversity. This may indicate under-surveying or "
            "genuinely low species density. Field surveys recommended."
        )

    # Second-best habitat
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_scores) > 1:
        second_key, second_score = sorted_scores[1]
        second_name = HABITAT_TYPES[second_key]["name"]
        if second_score > 50:
            recs.append(
                f"The location also shows moderate suitability for "
                f"**{second_name}** ({second_score:.0f}/100), suggesting "
                f"transitional or ecotone characteristics."
            )

    return recs


# ═══════════════════════════════════════════════════════════════════════════════
# UI RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_habitat_analyzer_tab():
    """Render the Habitat Suitability AI tab."""

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);'
        "border:1px solid #2a3550;border-radius:12px;padding:18px 22px;"
        'margin-bottom:16px;">'
        '<h4 style="color:#10b981;margin:0 0 6px 0;">'
        "\U0001F33F Habitat Suitability AI</h4>"
        '<p style="color:#8b97b0;margin:0;font-size:13px;">'
        "Analyze habitat suitability for 8 ecosystem types using soil, climate, "
        "terrain, water, and biodiversity data from multiple free APIs.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Location selector ─────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1.2, 1.0, 1.0])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="hab_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude",
            value=default_lat,
            format="%.5f",
            min_value=-90.0,
            max_value=90.0,
            key="hab_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude",
            value=default_lon,
            format="%.5f",
            min_value=-180.0,
            max_value=180.0,
            key="hab_lon",
        )

    run = st.button(
        "\U0001F50D Analyze Habitat",
        type="primary",
        key="hab_run",
        use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Habitat** to run the "
            "multi-factor suitability analysis."
        )
        return

    # ── Run analysis ──────────────────────────────────────────────────────────
    with st.spinner("Fetching environmental data and computing suitability..."):
        result = compute_habitat_suitability(lat, lon)

    best = result["best_habitat"]
    scores = result["habitat_scores"]
    env = result["environmental_conditions"]
    bio = result["biodiversity_summary"]
    recs = result["recommendations"]

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # BEST HABITAT HEADER
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);'
        f"border:2px solid {best['color']};border-radius:14px;"
        f'padding:22px 28px;text-align:center;margin-bottom:18px;">'
        f'<span style="font-size:48px;">{best["icon"]}</span><br/>'
        f'<h2 style="color:{best["color"]};margin:8px 0 4px 0;">'
        f'{best["name"]}</h2>'
        f'<span style="color:#e8ecf4;font-size:22px;font-weight:bold;">'
        f'{best["score"]:.0f}/100 Suitability</span><br/>'
        f'<span style="color:#8b97b0;font-size:13px;">'
        f"Best matching habitat for {lat:.4f}, {lon:.4f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # RADAR CHART
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Habitat Suitability Radar")

    categories_ordered = list(HABITAT_TYPES.keys())
    radar_labels = [HABITAT_TYPES[k]["name"] for k in categories_ordered]
    radar_values = [scores[k] for k in categories_ordered]
    radar_colors = [HABITAT_TYPES[k]["color"] for k in categories_ordered]

    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=radar_values + [radar_values[0]],
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            fillcolor="rgba(16,185,129,0.18)",
            line=dict(color="#10b981", width=2),
            marker=dict(size=6, color=radar_colors + [radar_colors[0]]),
            name="Suitability",
        )
    )
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(26,26,46,0.6)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#2a3550",
                tickfont=dict(color="#8b97b0", size=10),
            ),
            angularaxis=dict(
                gridcolor="#2a3550",
                tickfont=dict(color="#e8ecf4", size=11),
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="habana_pchart1")

    # ══════════════════════════════════════════════════════════════════════════
    # HABITAT CARDS (4 cols x 2 rows)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### All Habitat Scores")

    habitat_keys = list(HABITAT_TYPES.keys())
    for row in range(2):
        cols = st.columns(4)
        for ci in range(4):
            idx = row * 4 + ci
            if idx >= len(habitat_keys):
                break
            hkey = habitat_keys[idx]
            hcfg = HABITAT_TYPES[hkey]
            sc = scores[hkey]
            is_best = hkey == best["key"]

            border_style = (
                f"border:2px solid {hcfg['color']};"
                if is_best
                else "border:1px solid #2a3550;"
            )
            badge = (
                '<span style="background:#10b981;color:#fff;font-size:10px;'
                'padding:2px 8px;border-radius:8px;margin-left:6px;">BEST</span>'
                if is_best
                else ""
            )

            # Score bar fill
            bar_pct = min(sc, 100)
            if sc >= 70:
                bar_color = "#10b981"
            elif sc >= 40:
                bar_color = "#f59e0b"
            else:
                bar_color = "#ef4444"

            card_html = (
                f'<div style="background:rgba(26,26,46,0.85);{border_style}'
                f"border-radius:10px;padding:14px;text-align:center;"
                f'min-height:170px;margin-bottom:8px;">'
                f'<span style="font-size:28px;">{hcfg["icon"]}</span><br/>'
                f'<span style="color:{hcfg["color"]};font-weight:bold;'
                f'font-size:13px;">{hcfg["name"]}</span>{badge}<br/>'
                f'<span style="color:#e8ecf4;font-size:22px;font-weight:bold;">'
                f"{sc:.0f}%</span><br/>"
                f'<div style="background:#1a2235;border-radius:6px;height:8px;'
                f'margin:8px 4px 0 4px;overflow:hidden;">'
                f'<div style="width:{bar_pct:.0f}%;background:{bar_color};'
                f'height:100%;border-radius:6px;"></div></div>'
                f"</div>"
            )
            with cols[ci]:
                st.markdown(card_html, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # BAR CHART COMPARISON
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Habitat Comparison")

    sorted_habitats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    bar_names = [HABITAT_TYPES[k]["name"] for k, _ in sorted_habitats]
    bar_values = [v for _, v in sorted_habitats]
    bar_colors_list = [HABITAT_TYPES[k]["color"] for k, _ in sorted_habitats]

    fig_bar = go.Figure()
    fig_bar.add_trace(
        go.Bar(
            x=bar_values,
            y=bar_names,
            orientation="h",
            marker=dict(color=bar_colors_list),
            text=[f"{v:.0f}%" for v in bar_values],
            textposition="auto",
            textfont=dict(color="#e8ecf4", size=12),
        )
    )
    fig_bar.update_layout(
        xaxis=dict(
            range=[0, 105],
            title="Suitability Score",
            gridcolor="#2a3550",
            tickfont=dict(color="#8b97b0"),
            title_font=dict(color="#8b97b0"),
        ),
        yaxis=dict(
            tickfont=dict(color="#e8ecf4", size=12),
            autorange="reversed",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.6)",
        margin=dict(l=140, r=30, t=20, b=40),
        height=340,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="habana_pchart2")

    # ══════════════════════════════════════════════════════════════════════════
    # ENVIRONMENTAL CONDITIONS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Environmental Conditions")

    ec1, ec2, ec3, ec4 = st.columns(4)
    ec1.metric("Avg Temperature", f"{env['temperature_c']:.1f} \u00b0C")
    ec2.metric("Est. Annual Precip.", f"{env['annual_precip_mm']:.0f} mm")
    ec3.metric("Humidity", f"{env['humidity_pct']}%")
    ec4.metric("Center Elevation", f"{env['center_elevation_m']:.0f} m")

    ec5, ec6, ec7, ec8 = st.columns(4)
    ec5.metric("Elevation Range", f"{env['elevation_range_m']:.0f} m")
    ec6.metric("Water Features", f"{env['water_feature_count']}")
    ec7.metric(
        "Soil pH",
        f"{env['soil_ph']:.1f}" if env["soil_ph"] is not None else "N/A",
    )
    ec8.metric(
        "Organic Carbon",
        f"{env['soil_organic_carbon']:.1f} g/kg"
        if env["soil_organic_carbon"] is not None
        else "N/A",
    )

    # Soil texture row
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric(
        "Clay",
        f"{env['clay_pct']:.1f}%" if env["clay_pct"] is not None else "N/A",
    )
    sc2.metric(
        "Sand",
        f"{env['sand_pct']:.1f}%" if env["sand_pct"] is not None else "N/A",
    )
    sc3.metric(
        "Silt",
        f"{env['silt_pct']:.1f}%" if env["silt_pct"] is not None else "N/A",
    )
    sc4.metric(
        "CEC",
        f"{env['cec_cmol_kg']:.1f} cmol/kg"
        if env["cec_cmol_kg"] is not None
        else "N/A",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # BIODIVERSITY CONTEXT
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Biodiversity Context")

    bc1, bc2, bc3 = st.columns(3)
    bc1.metric("iNaturalist Observations", bio.get("inat_total", 0))
    bc2.metric("GBIF Records", bio.get("gbif_total", 0))
    bc3.metric("GBIF Unique Species", bio.get("gbif_unique_species", 0))

    # Kingdom distribution
    kc = bio.get("kingdom_counts", {})
    if kc:
        bio_c1, bio_c2 = st.columns([1, 1])
        with bio_c1:
            kingdom_colors = {
                "Plantae": "#10b981",
                "Aves": "#06b6d4",
                "Mammalia": "#8b5cf6",
                "Insecta": "#f59e0b",
                "Reptilia": "#ef4444",
                "Amphibia": "#ec4899",
                "Actinopterygii": "#3b82f6",
                "Fungi": "#a855f7",
                "Animalia": "#14b8a6",
                "Chromista": "#84cc16",
                "Other": "#8b97b0",
            }
            k_names = list(kc.keys())
            k_values = [kc[k] for k in k_names]
            k_colors = [kingdom_colors.get(k, "#8b97b0") for k in k_names]

            fig_kingdom = go.Figure()
            fig_kingdom.add_trace(
                go.Pie(
                    labels=k_names,
                    values=k_values,
                    marker=dict(colors=k_colors),
                    hole=0.45,
                    textinfo="label+percent",
                    textfont=dict(color="#e8ecf4", size=11),
                )
            )
            fig_kingdom.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                height=300,
            )
            st.plotly_chart(fig_kingdom, use_container_width=True, key="habana_pchart3")

        with bio_c2:
            top_sp = bio.get("top_species", [])
            if top_sp:
                st.markdown(
                    '<div style="background:rgba(26,26,46,0.7);border:1px solid #2a3550;'
                    'border-radius:10px;padding:12px;">'
                    '<h5 style="color:#e8ecf4;margin:0 0 8px 0;">Top Species</h5>',
                    unsafe_allow_html=True,
                )
                for sci_name, count, common_name in top_sp[:12]:
                    safe_common_name = html_module.escape(str(common_name))
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:3px 0;border-bottom:1px solid #1a2235;">'
                        f'<span style="color:#e8ecf4;font-size:12px;">'
                        f"{safe_common_name}</span>"
                        f'<span style="color:#8b97b0;font-size:11px;'
                        f'font-style:italic;">{count} obs</span></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No species observations found in this area.")
    else:
        st.info("No biodiversity data available for this location.")

    # ══════════════════════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Recommendations")

    for i, rec in enumerate(recs):
        icon = "\U00002705" if i == 0 else "\U000027A1\uFE0F"
        st.markdown(
            f'<div style="background:rgba(26,26,46,0.7);border:1px solid #2a3550;'
            f"border-radius:8px;padding:10px 14px;margin-bottom:8px;"
            f'border-left:3px solid {best["color"]};">'
            f'<span style="color:#e8ecf4;font-size:13px;">'
            f"{icon} {rec}</span></div>",
            unsafe_allow_html=True,
        )
