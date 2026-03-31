"""
Natural Resource Potential AI for TerraScout AI.
Evaluates the natural resource potential of a location across 8 categories:
Agricultural, Water Resources, Solar Energy, Wind Energy, Mineral Potential,
Timber/Forestry, Geothermal, and Tourism.
Combines soil, weather, water, elevation, and infrastructure data into
a unified resource potential assessment.
"""

import logging
import math

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
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
)


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# RESOURCE CATEGORY METADATA
# ═══════════════════════════════════════════════════════════════

RESOURCE_CATEGORIES = {
    "Agricultural": {"icon": "🌾", "color": "#22c55e"},
    "Water Resources": {"icon": "💧", "color": "#3b82f6"},
    "Solar Energy": {"icon": "☀️", "color": "#f59e0b"},
    "Wind Energy": {"icon": "💨", "color": "#06b6d4"},
    "Mineral Potential": {"icon": "⛏️", "color": "#8b5cf6"},
    "Timber/Forestry": {"icon": "🌲", "color": "#10b981"},
    "Geothermal": {"icon": "🌋", "color": "#ef4444"},
    "Tourism": {"icon": "🏞️", "color": "#ec4899"},
}


# ═══════════════════════════════════════════════════════════════
# COMPUTE RESOURCE POTENTIAL (CACHED)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_resource_potential(lat: float, lon: float) -> dict:
    """
    Evaluate the natural resource potential at a given location.
    Returns a dict with overall score, category_scores, details, and top_resources.
    """
    # ── Fetch all data sources ──
    soil = fetch_soil_data(lat, lon) or {}
    weather = fetch_weather_data(lat, lon) or {}
    water = fetch_water_features(lat, lon) or {}
    elevation = fetch_elevation_grid(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}

    # ── Extract soil properties using standard pattern ──
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    soc = _sv("soc") or 10
    ph = _sv("phh2o") or 7.0
    nitrogen = _sv("nitrogen", 100) or 1.0
    clay = _sv("clay") or 20
    sand = _sv("sand") or 30
    silt = _sv("silt") or 30
    cec = _sv("cec") or 15

    # ── Extract weather data ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max_list = daily.get("temperature_2m_max", [])
    temp_min_list = daily.get("temperature_2m_min", [])
    precip_list = daily.get("precipitation_sum", [])

    valid_tmax = [t for t in temp_max_list if t is not None]
    valid_tmin = [t for t in temp_min_list if t is not None]
    valid_precip = [p for p in precip_list if p is not None]

    avg_tmax = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20
    avg_tmin = sum(valid_tmin) / len(valid_tmin) if valid_tmin else 10
    avg_temp = (avg_tmax + avg_tmin) / 2
    weekly_precip = sum(valid_precip) if valid_precip else 5
    annual_precip_est = weekly_precip * 52

    cloud_cover = current.get("cloud_cover", 50) or 50
    wind_speed = current.get("wind_speed_10m", 0) or 0
    humidity = current.get("relative_humidity_2m", 50) or 50

    # ── Extract water features ──
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    springs = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "spring")
    wells = sum(1 for e in w_elements if e.get("tags", {}).get("man_made") == "water_well")
    rivers = sum(1 for e in w_elements
                 if e.get("tags", {}).get("waterway") in ("river", "stream"))
    wetlands = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "wetland")
    water_bodies = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "water")
    waterways = sum(1 for e in w_elements if e.get("tags", {}).get("waterway"))
    water_total = len(w_elements)

    # ── Extract elevation data ──
    center_elev = elevation.get("center", 0) or 0
    max_elev = elevation.get("max_elevation", 0) or 0
    min_elev = elevation.get("min_elevation", 0) or 0
    relief = max_elev - min_elev if isinstance(max_elev, (int, float)) and isinstance(min_elev, (int, float)) else 0

    # ── Extract infrastructure data ──
    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))
    forests = sum(1 for e in i_elements
                  if e.get("tags", {}).get("landuse") in ("forest", "wood"))
    farmlands = sum(1 for e in i_elements
                    if e.get("tags", {}).get("landuse") == "farmland")
    parks = sum(1 for e in i_elements
                if e.get("tags", {}).get("leisure") == "park")

    category_scores = {}
    details = {}

    # ════════════════════════════════════════════════════════════
    # 1. AGRICULTURAL POTENTIAL
    # ════════════════════════════════════════════════════════════
    ag_score = 30
    ag_detail = {}

    # Soil quality factors
    soc_factor = min(30, soc * 1.5)
    ph_factor = max(0, 20 - abs(ph - 6.5) * 8)
    n_factor = min(20, nitrogen * 8)
    ag_score += soc_factor + ph_factor + n_factor
    ag_detail["soil_organic_carbon"] = round(soc, 1)
    ag_detail["soil_ph"] = round(ph, 1)
    ag_detail["nitrogen"] = round(nitrogen, 2)

    # Climate factors
    if 10 <= avg_temp <= 28:
        ag_score += 10
    elif 5 <= avg_temp <= 35:
        ag_score += 5
    if 400 <= annual_precip_est <= 1200:
        ag_score += 10
    elif 200 <= annual_precip_est <= 2000:
        ag_score += 5
    ag_detail["avg_temperature"] = round(avg_temp, 1)
    ag_detail["annual_precip_est_mm"] = round(annual_precip_est)

    # Terrain factors (flat = better)
    if relief < 30:
        ag_score += 10
    elif relief < 100:
        ag_score += 5
    elif relief > 300:
        ag_score -= 10
    ag_detail["terrain_relief_m"] = round(relief)

    # Existing farmland bonus
    if farmlands > 0:
        ag_score += min(10, farmlands * 3)
        ag_detail["existing_farmland"] = farmlands

    category_scores["Agricultural"] = max(0, min(100, round(ag_score)))
    details["Agricultural"] = ag_detail

    # ════════════════════════════════════════════════════════════
    # 2. WATER RESOURCES
    # ════════════════════════════════════════════════════════════
    wr_score = 15
    wr_detail = {}

    wr_score += min(20, springs * 10)
    wr_score += min(15, rivers * 5)
    wr_score += min(10, wetlands * 8)
    wr_score += min(10, wells * 6)
    wr_score += min(10, water_bodies * 5)
    wr_detail["springs"] = springs
    wr_detail["rivers_streams"] = rivers
    wr_detail["wetlands"] = wetlands
    wr_detail["wells"] = wells
    wr_detail["water_bodies"] = water_bodies
    wr_detail["total_water_features"] = water_total

    # Rainfall contribution
    if annual_precip_est > 800:
        wr_score += 20
    elif annual_precip_est > 400:
        wr_score += 12
    elif annual_precip_est > 200:
        wr_score += 5
    wr_detail["annual_precip_est_mm"] = round(annual_precip_est)

    category_scores["Water Resources"] = max(0, min(100, round(wr_score)))
    details["Water Resources"] = wr_detail

    # ════════════════════════════════════════════════════════════
    # 3. SOLAR ENERGY
    # ════════════════════════════════════════════════════════════
    sol_score = 25
    sol_detail = {}

    # Cloud cover (less = better)
    if cloud_cover < 20:
        sol_score += 30
    elif cloud_cover < 40:
        sol_score += 22
    elif cloud_cover < 60:
        sol_score += 12
    elif cloud_cover < 80:
        sol_score += 5
    sol_detail["cloud_cover_pct"] = round(cloud_cover)

    # Latitude factor (closer to equator = more solar)
    abs_lat = abs(lat)
    if abs_lat < 25:
        sol_score += 25
    elif abs_lat < 35:
        sol_score += 18
    elif abs_lat < 45:
        sol_score += 10
    elif abs_lat < 55:
        sol_score += 4
    sol_detail["latitude"] = round(lat, 2)
    sol_detail["latitude_advantage"] = "High" if abs_lat < 30 else "Moderate" if abs_lat < 45 else "Low"

    # Temperature (warm = more solar energy available)
    if avg_temp > 25:
        sol_score += 10
    elif avg_temp > 15:
        sol_score += 6
    sol_detail["avg_temperature"] = round(avg_temp, 1)

    # Sunshine hours estimate based on cloud cover
    sunshine_est = max(0, (100 - cloud_cover) / 100 * 14)
    sol_score += min(10, sunshine_est)
    sol_detail["estimated_sunshine_hours"] = round(sunshine_est, 1)

    category_scores["Solar Energy"] = max(0, min(100, round(sol_score)))
    details["Solar Energy"] = sol_detail

    # ════════════════════════════════════════════════════════════
    # 4. WIND ENERGY
    # ════════════════════════════════════════════════════════════
    wind_score = 15
    wind_detail = {}

    # Wind speed scoring
    if wind_speed >= 25:
        wind_score += 35
    elif wind_speed >= 15:
        wind_score += 28
    elif wind_speed >= 10:
        wind_score += 22
    elif wind_speed >= 6:
        wind_score += 15
    elif wind_speed >= 3:
        wind_score += 8
    wind_detail["wind_speed_kmh"] = round(wind_speed, 1)

    # Elevation exposure (higher + more relief = better wind)
    if center_elev > 800:
        wind_score += 15
    elif center_elev > 400:
        wind_score += 10
    elif center_elev > 100:
        wind_score += 5
    wind_detail["elevation_m"] = round(center_elev)

    if relief > 200:
        wind_score += 10
    elif relief > 50:
        wind_score += 5
    wind_detail["terrain_relief_m"] = round(relief)

    # Coastal/open exposure bonus (fewer buildings = more exposed)
    if buildings < 5:
        wind_score += 10
    elif buildings < 20:
        wind_score += 5
    wind_detail["obstruction_level"] = "Low" if buildings < 10 else "Moderate" if buildings < 50 else "High"

    category_scores["Wind Energy"] = max(0, min(100, round(wind_score)))
    details["Wind Energy"] = wind_detail

    # ════════════════════════════════════════════════════════════
    # 5. MINERAL POTENTIAL
    # ════════════════════════════════════════════════════════════
    min_score = 20
    min_detail = {}

    # Geology estimate from soil composition
    total_texture = clay + sand + silt
    clay_pct = (clay / total_texture * 100) if total_texture > 0 else 33
    sand_pct = (sand / total_texture * 100) if total_texture > 0 else 33
    silt_pct = (silt / total_texture * 100) if total_texture > 0 else 33

    # High clay = sedimentary (potential for construction minerals)
    if clay_pct > 40:
        min_score += 15
        min_detail["geology_indicator"] = "Clay-rich sedimentary"
    elif sand_pct > 50:
        min_score += 10
        min_detail["geology_indicator"] = "Sandy/alluvial deposits"
    elif silt_pct > 40:
        min_score += 12
        min_detail["geology_indicator"] = "Silt-rich (loess/fluvial)"
    else:
        min_score += 8
        min_detail["geology_indicator"] = "Mixed composition"

    min_detail["clay_pct"] = round(clay_pct, 1)
    min_detail["sand_pct"] = round(sand_pct, 1)
    min_detail["silt_pct"] = round(silt_pct, 1)

    # CEC as indicator of mineral richness
    if cec > 25:
        min_score += 20
    elif cec > 15:
        min_score += 12
    elif cec > 8:
        min_score += 6
    min_detail["cec_cmol_kg"] = round(cec, 1)

    # Elevation and terrain variability (mountainous = more mineral exposure)
    if center_elev > 1500:
        min_score += 15
    elif center_elev > 600:
        min_score += 10
    elif center_elev > 200:
        min_score += 5
    if relief > 300:
        min_score += 10
    elif relief > 100:
        min_score += 5
    min_detail["elevation_m"] = round(center_elev)
    min_detail["relief_m"] = round(relief)

    category_scores["Mineral Potential"] = max(0, min(100, round(min_score)))
    details["Mineral Potential"] = min_detail

    # ════════════════════════════════════════════════════════════
    # 6. TIMBER / FORESTRY
    # ════════════════════════════════════════════════════════════
    timber_score = 15
    timber_detail = {}

    # Precipitation (forests need water)
    if annual_precip_est > 1000:
        timber_score += 20
    elif annual_precip_est > 600:
        timber_score += 14
    elif annual_precip_est > 300:
        timber_score += 7
    timber_detail["annual_precip_est_mm"] = round(annual_precip_est)

    # Temperature (moderate = best for forestry)
    if 8 <= avg_temp <= 22:
        timber_score += 15
    elif 3 <= avg_temp <= 28:
        timber_score += 8
    timber_detail["avg_temperature"] = round(avg_temp, 1)

    # Soil organic matter
    if soc > 25:
        timber_score += 15
    elif soc > 15:
        timber_score += 10
    elif soc > 8:
        timber_score += 5
    timber_detail["soil_organic_carbon"] = round(soc, 1)

    # Existing forests
    if forests > 0:
        timber_score += min(20, forests * 5)
        timber_detail["existing_forest_areas"] = forests
    else:
        timber_detail["existing_forest_areas"] = 0

    # Terrain (moderate slopes OK for forestry)
    if 20 < relief < 500:
        timber_score += 8
    elif relief <= 20:
        timber_score += 5
    timber_detail["terrain_relief_m"] = round(relief)

    category_scores["Timber/Forestry"] = max(0, min(100, round(timber_score)))
    details["Timber/Forestry"] = timber_detail

    # ════════════════════════════════════════════════════════════
    # 7. GEOTHERMAL
    # ════════════════════════════════════════════════════════════
    geo_score = 10
    geo_detail = {}

    # Volcanic proximity estimate from elevation and terrain
    # Geothermal is high in volcanic regions (usually high elevation, steep terrain)
    if center_elev > 2000:
        geo_score += 15
    elif center_elev > 1000:
        geo_score += 10
    elif center_elev > 500:
        geo_score += 5
    geo_detail["elevation_m"] = round(center_elev)

    if relief > 500:
        geo_score += 15
    elif relief > 200:
        geo_score += 8
    elif relief > 100:
        geo_score += 4
    geo_detail["terrain_relief_m"] = round(relief)

    # Hot springs indicator (springs in geologically active areas)
    if springs > 0:
        geo_score += min(20, springs * 10)
        geo_detail["hot_springs_indicator"] = springs
    else:
        geo_detail["hot_springs_indicator"] = 0

    # Latitude bands associated with tectonic boundaries
    # Pacific Ring of Fire, Mediterranean belt, Rift Valley
    if (30 <= abs(lat) <= 45) or (abs(lat) < 10):
        geo_score += 10
    elif 10 <= abs(lat) <= 30:
        geo_score += 5
    geo_detail["tectonic_zone_estimate"] = (
        "Likely active zone" if geo_score > 50 else
        "Moderate potential" if geo_score > 30 else
        "Low activity zone"
    )

    # Clay content can indicate hydrothermal alteration
    if clay > 35:
        geo_score += 10
    elif clay > 25:
        geo_score += 5
    geo_detail["clay_content"] = round(clay, 1)

    category_scores["Geothermal"] = max(0, min(100, round(geo_score)))
    details["Geothermal"] = geo_detail

    # ════════════════════════════════════════════════════════════
    # 8. TOURISM
    # ════════════════════════════════════════════════════════════
    tour_score = 20
    tour_detail = {}

    # Biodiversity potential (water features + forests + parks = more biodiversity)
    bio_indicator = water_total + forests * 3 + parks * 4
    if bio_indicator > 15:
        tour_score += 20
    elif bio_indicator > 8:
        tour_score += 14
    elif bio_indicator > 3:
        tour_score += 8
    tour_detail["biodiversity_indicator"] = bio_indicator

    # Landscape variety (terrain + water + elevation)
    landscape_var = 0
    if relief > 200:
        landscape_var += 3
    elif relief > 50:
        landscape_var += 2
    if water_total > 3:
        landscape_var += 2
    elif water_total > 0:
        landscape_var += 1
    if center_elev > 500:
        landscape_var += 2
    elif center_elev > 100:
        landscape_var += 1
    if forests > 0:
        landscape_var += 1
    if parks > 0:
        landscape_var += 1

    tour_score += min(25, landscape_var * 4)
    tour_detail["landscape_variety_score"] = landscape_var
    tour_detail["terrain_relief_m"] = round(relief)

    # Climate comfort (mild temps, moderate humidity)
    comfort = max(0, 100 - abs(avg_temp - 22) * 4 - abs(humidity - 50) * 0.5)
    comfort_bonus = min(20, comfort / 5)
    tour_score += comfort_bonus
    tour_detail["climate_comfort_pct"] = round(comfort)
    tour_detail["avg_temperature"] = round(avg_temp, 1)

    # Infrastructure access (some roads = accessible, not too urban)
    if 5 <= roads <= 50:
        tour_score += 10
    elif roads > 0:
        tour_score += 5
    tour_detail["road_accessibility"] = "Good" if roads >= 5 else "Limited" if roads > 0 else "Remote"

    # Water / coastal attraction
    if water_total > 5:
        tour_score += 5
    tour_detail["water_features"] = water_total

    category_scores["Tourism"] = max(0, min(100, round(tour_score)))
    details["Tourism"] = tour_detail

    # ════════════════════════════════════════════════════════════
    # OVERALL POTENTIAL
    # ════════════════════════════════════════════════════════════
    all_scores = list(category_scores.values())
    overall = round(sum(all_scores) / len(all_scores)) if all_scores else 0

    # Top resources sorted by score
    top_resources = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

    return {
        "overall": overall,
        "category_scores": category_scores,
        "details": details,
        "top_resources": top_resources,
    }


# ═══════════════════════════════════════════════════════════════
# RENDER TAB
# ═══════════════════════════════════════════════════════════════

def render_resource_potential_tab():
    """Render the Natural Resource Potential AI tab."""
    st.markdown("## Natural Resource Potential AI")
    st.caption("Evaluate natural resource potential across 8 categories")

    # ── Location selector ──
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="rp_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="rp_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="rp_lon", format="%.4f")

    if not st.button("Assess Resource Potential", type="primary", use_container_width=True):
        return

    with st.spinner("Evaluating resource potential across 8 dimensions..."):
        result = compute_resource_potential(lat, lon)

    if not result:
        st.error("Resource assessment failed.")
        return

    overall = result["overall"]
    category_scores = result["category_scores"]
    details_data = result["details"]
    top_resources = result["top_resources"]

    # ── Overall score classification ──
    if overall >= 75:
        grade_label = "Excellent"
        grade_color = "#10b981"
    elif overall >= 55:
        grade_label = "Good"
        grade_color = "#22c55e"
    elif overall >= 40:
        grade_label = "Moderate"
        grade_color = "#f59e0b"
    elif overall >= 25:
        grade_label = "Low"
        grade_color = "#f97316"
    else:
        grade_label = "Very Low"
        grade_color = "#ef4444"

    # ── Overall score header ──
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, {grade_color}22, {grade_color}44);
                border-left:5px solid {grade_color}; border-radius:12px;
                padding:25px; margin:10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#888; font-size:12px;">OVERALL RESOURCE POTENTIAL</div>
                <div style="color:{grade_color}; font-size:36px; font-weight:bold; margin:4px 0;">
                    {grade_label}
                </div>
                <div style="color:#aaa; font-size:13px;">
                    {lat:.4f}, {lon:.4f}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:56px; font-weight:bold; color:{grade_color};">
                    {overall}
                </div>
                <div style="color:#888; font-size:14px;">/100</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Radar chart of 8 dimensions ──
    st.markdown("### Resource Radar")
    cat_names = list(RESOURCE_CATEGORIES.keys())
    cat_values = [category_scores.get(c, 0) for c in cat_names]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=cat_values + [cat_values[0]],
        theta=cat_names + [cat_names[0]],
        fill="toself",
        fillcolor=_hex_rgba(grade_color, 0.13),
        line=dict(color=grade_color, width=2),
        marker=dict(size=6, color=grade_color),
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11)),
        ),
        showlegend=False,
        height=450,
        margin=dict(t=40, b=40, l=80, r=80),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="respot_pchart1")

    # ── Resource cards (2 rows x 4 columns) ──
    st.markdown("### Resource Scores")
    cat_list = list(RESOURCE_CATEGORIES.items())

    # Row 1: first 4 categories
    cols_row1 = st.columns(4)
    for idx in range(4):
        cat_name, cat_meta = cat_list[idx]
        score = category_scores.get(cat_name, 0)
        icon = cat_meta["icon"]
        color = cat_meta["color"]

        if score >= 70:
            sc = "#10b981"
        elif score >= 40:
            sc = "#f59e0b"
        else:
            sc = "#ef4444"

        with cols_row1[idx]:
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid {color}44;
                        border-radius:10px; padding:15px; margin:5px 0; min-height:140px;">
                <div style="color:{color}; font-weight:bold; font-size:13px;">
                    {icon} {cat_name}
                </div>
                <div style="font-size:36px; font-weight:bold; color:{sc}; margin:8px 0;">
                    {score}<span style="font-size:12px; color:#888;">%</span>
                </div>
                <div style="background:#111827; border-radius:6px; height:6px; margin-top:6px;">
                    <div style="background:{color}; height:6px; border-radius:6px;
                                width:{score}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Row 2: next 4 categories
    cols_row2 = st.columns(4)
    for idx in range(4, 8):
        cat_name, cat_meta = cat_list[idx]
        score = category_scores.get(cat_name, 0)
        icon = cat_meta["icon"]
        color = cat_meta["color"]

        if score >= 70:
            sc = "#10b981"
        elif score >= 40:
            sc = "#f59e0b"
        else:
            sc = "#ef4444"

        with cols_row2[idx - 4]:
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid {color}44;
                        border-radius:10px; padding:15px; margin:5px 0; min-height:140px;">
                <div style="color:{color}; font-weight:bold; font-size:13px;">
                    {icon} {cat_name}
                </div>
                <div style="font-size:36px; font-weight:bold; color:{sc}; margin:8px 0;">
                    {score}<span style="font-size:12px; color:#888;">%</span>
                </div>
                <div style="background:#111827; border-radius:6px; height:6px; margin-top:6px;">
                    <div style="background:{color}; height:6px; border-radius:6px;
                                width:{score}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Horizontal bar chart sorted by score ──
    st.markdown("### Resource Ranking")
    sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    bar_names = [c[0] for c in sorted_cats]
    bar_values = [c[1] for c in sorted_cats]
    bar_colors = [RESOURCE_CATEGORIES[c]["color"] for c in bar_names]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=bar_values,
        y=bar_names,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{v}%" for v in bar_values],
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig_bar.update_layout(
        height=380,
        margin=dict(t=20, b=20, l=120, r=40),
        xaxis=dict(range=[0, 110], title="Score"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="respot_pchart2")

    # ── Top 3 resources highlighted ──
    st.markdown("### Top Resources")
    top_3 = top_resources[:3]
    medals = ["🥇", "🥈", "🥉"]

    top_cols = st.columns(3)
    for idx, (res_name, res_score) in enumerate(top_3):
        medal = medals[idx]
        color = RESOURCE_CATEGORIES[res_name]["color"]
        icon = RESOURCE_CATEGORIES[res_name]["icon"]

        if res_score >= 70:
            verdict = "High Potential"
        elif res_score >= 45:
            verdict = "Moderate Potential"
        else:
            verdict = "Limited Potential"

        with top_cols[idx]:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, {color}15, {color}30);
                        border:2px solid {color}66; border-radius:12px;
                        padding:18px; text-align:center; min-height:160px;">
                <div style="font-size:28px;">{medal}</div>
                <div style="color:{color}; font-weight:bold; font-size:15px; margin:6px 0;">
                    {icon} {res_name}
                </div>
                <div style="font-size:38px; font-weight:bold; color:{color};">
                    {res_score}%
                </div>
                <div style="color:#aaa; font-size:12px; margin-top:4px;">{verdict}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Details expander per resource ──
    st.markdown("### Detailed Breakdown")
    for cat_name in [r[0] for r in top_resources]:
        cat_meta = RESOURCE_CATEGORIES[cat_name]
        score = category_scores[cat_name]
        detail = details_data.get(cat_name, {})
        color = cat_meta["color"]
        icon = cat_meta["icon"]

        with st.expander(f"{icon} {cat_name} -- Score: {score}/100"):
            detail_items = []
            for k, v in detail.items():
                label = k.replace("_", " ").title()
                detail_items.append(f"""
                <div style="display:flex; justify-content:space-between;
                            padding:6px 0; border-bottom:1px solid #ffffff10;">
                    <span style="color:#aaa; font-size:13px;">{label}</span>
                    <span style="color:{color}; font-weight:bold; font-size:13px;">{v}</span>
                </div>
                """)

            detail_html = "".join(detail_items)
            st.markdown(f"""
            <div style="background:#1a1a2e; border-radius:10px; padding:15px;">
                <div style="display:flex; align-items:center; margin-bottom:10px;">
                    <div style="font-size:20px; margin-right:8px;">{icon}</div>
                    <div>
                        <div style="color:{color}; font-weight:bold; font-size:15px;">{cat_name}</div>
                        <div style="color:#888; font-size:11px;">Score: {score}/100</div>
                    </div>
                </div>
                {detail_html}
            </div>
            """, unsafe_allow_html=True)
