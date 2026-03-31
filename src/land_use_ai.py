"""
Land Use Intelligence AI module for TerraScout AI.
Classifies current land use from multi-source geospatial data and computes
optimal land use recommendations using environmental suitability scoring.
Uses soil, weather, water, elevation, infrastructure, and protected area data
from the Deep Zone Analysis pipeline.
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
    fetch_protected_areas,
)

logger = logging.getLogger(__name__)

# ============================================================================
# LAND USE TYPE DEFINITIONS
# ============================================================================

LAND_USE_TYPES = {
    "agriculture": {
        "name": "Agriculture",
        "icon": "tractor",
        "color": "#10b981",
        "requirements": {
            "soil_quality": "high",
            "water_access": "high",
            "flat_terrain": "high",
            "climate_temperate": "moderate",
        },
    },
    "forestry": {
        "name": "Forestry",
        "icon": "tree",
        "color": "#059669",
        "requirements": {
            "precipitation": "high",
            "temperature_moderate": "moderate",
            "slope_tolerance": "high",
            "soil_organic_carbon": "moderate",
        },
    },
    "urban_residential": {
        "name": "Urban Residential",
        "icon": "home",
        "color": "#f59e0b",
        "requirements": {
            "flat_terrain": "high",
            "infrastructure": "high",
            "drainage": "moderate",
            "accessibility": "high",
        },
    },
    "commercial": {
        "name": "Commercial",
        "icon": "store",
        "color": "#8b5cf6",
        "requirements": {
            "infrastructure": "high",
            "accessibility": "high",
            "flat_terrain": "moderate",
            "population_density": "high",
        },
    },
    "industrial": {
        "name": "Industrial",
        "icon": "industry",
        "color": "#ef4444",
        "requirements": {
            "flat_terrain": "high",
            "infrastructure": "high",
            "distance_from_residential": "moderate",
            "water_access": "moderate",
        },
    },
    "conservation": {
        "name": "Conservation",
        "icon": "leaf",
        "color": "#06b6d4",
        "requirements": {
            "biodiversity_potential": "high",
            "water_features": "moderate",
            "low_development": "high",
            "ecosystem_value": "high",
        },
    },
    "recreation": {
        "name": "Recreation",
        "icon": "futbol",
        "color": "#ec4899",
        "requirements": {
            "accessibility": "moderate",
            "scenic_value": "high",
            "water_features": "moderate",
            "moderate_terrain": "moderate",
        },
    },
    "mixed_use": {
        "name": "Mixed Use",
        "icon": "city",
        "color": "#f97316",
        "requirements": {
            "infrastructure": "moderate",
            "flat_terrain": "moderate",
            "accessibility": "high",
            "population_density": "moderate",
        },
    },
    "pastoral": {
        "name": "Pastoral / Grazing",
        "icon": "horse",
        "color": "#84cc16",
        "requirements": {
            "grass_coverage": "high",
            "water_access": "moderate",
            "moderate_terrain": "moderate",
            "climate_temperate": "moderate",
        },
    },
    "agroforestry": {
        "name": "Agroforestry",
        "icon": "seedling",
        "color": "#14b8a6",
        "requirements": {
            "soil_quality": "moderate",
            "precipitation": "moderate",
            "slope_tolerance": "moderate",
            "soil_organic_carbon": "high",
        },
    },
}


# ============================================================================
# CORE INTELLIGENCE FUNCTION
# ============================================================================

@st.cache_data(ttl=1800)
def compute_land_use_intelligence(lat: float, lon: float) -> dict:
    """
    Fetch multi-source geospatial data and compute land use classification
    plus optimal-use recommendations with suitability scores (0-100).
    """

    # ------------------------------------------------------------------
    # 1. Fetch all data sources
    # ------------------------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elev = fetch_elevation_grid(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)
    protected = fetch_protected_areas(lat, lon)

    # ------------------------------------------------------------------
    # 2. Safe extraction with defensive patterns
    # ------------------------------------------------------------------
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    layers = props.get("layers", [])

    elements_water = (water if isinstance(water, dict) else {}).get("elements", [])
    elements_infra = (infra if isinstance(infra, dict) else {}).get("elements", [])
    elevations = (elev if isinstance(elev, dict) else {}).get("grid_elevations", [])
    protected_els = (protected if isinstance(protected, dict) else {}).get("elements", [])

    current_wx = (weather if isinstance(weather, dict) else {}).get("current", {})
    daily_wx = (weather if isinstance(weather, dict) else {}).get("daily", {})

    # ------------------------------------------------------------------
    # 3. Derive environmental indicators
    # ------------------------------------------------------------------

    # Soil indicators
    soc_value = 0.0
    ph_value = 7.0
    clay_pct = 0.0
    for layer in layers:
        lname = layer.get("name", "")
        depths = layer.get("depths", [])
        if depths:
            raw = depths[0].get("values", {}).get("mean")
            if raw is not None:
                if lname == "soc":
                    soc_value = raw / 10.0
                elif lname == "phh2o":
                    ph_value = raw / 10.0
                elif lname == "clay":
                    clay_pct = raw / 10.0

    soil_quality = min(100, soc_value * 3 + max(0, 50 - abs(ph_value - 6.5) * 15))

    # Weather indicators
    temp_now = current_wx.get("temperature_2m", 15.0)
    humidity = current_wx.get("relative_humidity_2m", 50)
    precip_list = daily_wx.get("precipitation_sum", [])
    precip_filtered = [p for p in precip_list if p is not None]
    total_precip = sum(precip_filtered) if precip_filtered else 0.0
    annual_precip_est = total_precip * (365.0 / max(len(precip_filtered), 1)) if precip_filtered else 500.0

    climate_score = min(100, max(0, 100 - abs(temp_now - 18) * 3 - max(0, 30 - humidity) * 0.5))
    precip_score = min(100, annual_precip_est / 12.0)

    # Water indicators
    water_count = len(elements_water)
    water_score = min(100, water_count * 8)

    # Elevation indicators
    valid_elevs = [e for e in elevations if e is not None]
    if valid_elevs:
        elev_min = min(valid_elevs)
        elev_max = max(valid_elevs)
        elev_center = (elev if isinstance(elev, dict) else {}).get("center_elevation", 0)
    else:
        elev_min = 0
        elev_max = 0
        elev_center = 0
    elev_range = elev_max - elev_min
    flatness = max(0, 100 - elev_range * 2)
    slope_tolerance = min(100, 40 + elev_range * 0.5)

    # Infrastructure indicators
    building_count = 0
    road_count = 0
    industrial_count = 0
    commercial_count = 0
    farmland_count = 0
    forest_count = 0
    park_count = 0

    for el in elements_infra:
        tags = el.get("tags", {})
        if "building" in tags:
            building_count += 1
        if "highway" in tags:
            road_count += 1
        lu = tags.get("landuse", "")
        if lu == "industrial":
            industrial_count += 1
        elif lu in ("commercial", "retail"):
            commercial_count += 1
        elif lu in ("farmland", "farm", "orchard", "vineyard"):
            farmland_count += 1
        elif lu == "forest":
            forest_count += 1
        if tags.get("leisure") == "park":
            park_count += 1

    infra_score = min(100, (building_count + road_count) * 2)
    dev_intensity = min(100, building_count * 3)
    low_dev = max(0, 100 - dev_intensity)

    # Protected area score
    protected_score = min(100, len(protected_els) * 25)

    # ------------------------------------------------------------------
    # 4. Classify current land use from infrastructure tags
    # ------------------------------------------------------------------
    if building_count > 50:
        if commercial_count > 5 or industrial_count > 5:
            current_use = "commercial" if commercial_count >= industrial_count else "industrial"
        else:
            current_use = "urban_residential"
    elif farmland_count > 3:
        current_use = "agriculture"
    elif forest_count > 3:
        current_use = "forestry"
    elif park_count > 2:
        current_use = "recreation"
    elif building_count > 10:
        current_use = "mixed_use"
    elif protected_score > 40:
        current_use = "conservation"
    elif farmland_count > 0 and forest_count > 0:
        current_use = "agroforestry"
    elif water_count > 5 and building_count < 5:
        current_use = "conservation"
    else:
        current_use = "pastoral"

    # ------------------------------------------------------------------
    # 5. Compute suitability scores for each land use type (0-100)
    # ------------------------------------------------------------------
    scores = {}

    # Agriculture: soil quality + water + climate + flat terrain
    scores["agriculture"] = min(100, int(
        soil_quality * 0.30
        + water_score * 0.25
        + climate_score * 0.20
        + flatness * 0.25
    ))

    # Forestry: precipitation + temp + slope OK + SOC
    forestry_temp = max(0, 100 - abs(temp_now - 12) * 4)
    scores["forestry"] = min(100, int(
        precip_score * 0.30
        + forestry_temp * 0.20
        + slope_tolerance * 0.20
        + min(100, soc_value * 5) * 0.30
    ))

    # Urban Residential: flat + infrastructure exists + good drainage
    drainage = max(0, 100 - clay_pct * 1.5)
    scores["urban_residential"] = min(100, int(
        flatness * 0.35
        + infra_score * 0.35
        + drainage * 0.30
    ))

    # Commercial: infrastructure + accessibility + flat + population
    scores["commercial"] = min(100, int(
        infra_score * 0.30
        + min(100, road_count * 5) * 0.25
        + flatness * 0.20
        + min(100, building_count * 2) * 0.25
    ))

    # Industrial: flat + infrastructure + distance from residential + water
    scores["industrial"] = min(100, int(
        flatness * 0.30
        + infra_score * 0.25
        + min(100, max(0, 100 - building_count)) * 0.20
        + water_score * 0.25
    ))

    # Conservation: biodiversity potential + water + low development
    biodiv_potential = min(100, water_score * 0.4 + precip_score * 0.3 + protected_score * 0.3)
    scores["conservation"] = min(100, int(
        biodiv_potential * 0.35
        + water_score * 0.25
        + low_dev * 0.25
        + protected_score * 0.15
    ))

    # Recreation: accessibility + scenic value + water + moderate terrain
    scenic = min(100, elev_range * 1.5 + water_score * 0.5)
    scores["recreation"] = min(100, int(
        min(100, road_count * 4) * 0.25
        + scenic * 0.30
        + water_score * 0.20
        + min(100, 50 + elev_range * 0.5) * 0.25
    ))

    # Mixed Use: infrastructure + flat + accessibility + population
    scores["mixed_use"] = min(100, int(
        infra_score * 0.30
        + flatness * 0.25
        + min(100, road_count * 4) * 0.25
        + min(100, building_count * 1.5) * 0.20
    ))

    # Pastoral: grass coverage proxy + water + moderate terrain + climate
    grass_proxy = max(0, 100 - dev_intensity * 0.8 - forest_count * 5)
    scores["pastoral"] = min(100, int(
        grass_proxy * 0.30
        + water_score * 0.25
        + min(100, 60 + elev_range * 0.3) * 0.20
        + climate_score * 0.25
    ))

    # Agroforestry: soil + precipitation + slope tolerance + SOC
    scores["agroforestry"] = min(100, int(
        soil_quality * 0.25
        + precip_score * 0.25
        + slope_tolerance * 0.20
        + min(100, soc_value * 6) * 0.30
    ))

    # ------------------------------------------------------------------
    # 6. Determine optimal use and conflicts
    # ------------------------------------------------------------------
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    optimal_use = sorted_scores[0][0] if sorted_scores else "pastoral"
    conflict_uses = [k for k, v in sorted_scores if v < 30]

    # ------------------------------------------------------------------
    # 7. Build transition recommendations
    # ------------------------------------------------------------------
    transition_recommendations = []

    if current_use != optimal_use:
        cur_info = LAND_USE_TYPES.get(current_use, {})
        opt_info = LAND_USE_TYPES.get(optimal_use, {})
        score_diff = scores.get(optimal_use, 0) - scores.get(current_use, 0)

        if score_diff > 15:
            transition_recommendations.append({
                "priority": "High",
                "from_use": cur_info.get("name", current_use),
                "to_use": opt_info.get("name", optimal_use),
                "score_gain": score_diff,
                "reason": (
                    f"Environmental suitability for {opt_info.get('name', optimal_use)} "
                    f"is {score_diff} points higher than current {cur_info.get('name', current_use)} use."
                ),
            })
        elif score_diff > 5:
            transition_recommendations.append({
                "priority": "Medium",
                "from_use": cur_info.get("name", current_use),
                "to_use": opt_info.get("name", optimal_use),
                "score_gain": score_diff,
                "reason": (
                    f"A moderate improvement of {score_diff} points is possible by "
                    f"transitioning to {opt_info.get('name', optimal_use)}."
                ),
            })

    # Suggest secondary alternatives
    for key, score in sorted_scores[1:4]:
        if key != current_use and score > scores.get(current_use, 0):
            alt_info = LAND_USE_TYPES.get(key, {})
            transition_recommendations.append({
                "priority": "Low",
                "from_use": LAND_USE_TYPES.get(current_use, {}).get("name", current_use),
                "to_use": alt_info.get("name", key),
                "score_gain": score - scores.get(current_use, 0),
                "reason": (
                    f"{alt_info.get('name', key)} scores {score}/100 and could serve as "
                    f"a viable alternative use."
                ),
            })

    # ------------------------------------------------------------------
    # 8. Build current environmental indicators
    # ------------------------------------------------------------------
    current_indicators = {
        "Soil Quality": round(soil_quality, 1),
        "Water Access": round(water_score, 1),
        "Climate Suitability": round(climate_score, 1),
        "Terrain Flatness": round(flatness, 1),
        "Precipitation": round(precip_score, 1),
        "Infrastructure": round(infra_score, 1),
        "Biodiversity Potential": round(biodiv_potential, 1),
        "Low Development": round(low_dev, 1),
    }

    return {
        "current_use": current_use,
        "optimal_use": optimal_use,
        "scores": scores,
        "current_indicators": current_indicators,
        "transition_recommendations": transition_recommendations,
        "conflicts": conflict_uses,
    }


# ============================================================================
# RENDER FUNCTION
# ============================================================================

def render_land_use_ai_tab():
    """Render the Land Use Intelligence AI tab in the Streamlit app."""

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
        'border:1px solid #0f3460;border-radius:12px;padding:18px 22px;'
        'margin-bottom:16px;">'
        '<h4 style="color:#06b6d4;margin:0 0 4px 0;">Land Use Intelligence AI</h4>'
        '<p style="color:#8b97b0;margin:0;font-size:13px;">'
        'AI-driven classification of current land use and computation of '
        'optimal land use recommendations from multi-source environmental data.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # -- Location selector ------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.4, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="luai_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50

    with col_lat:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="luai_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="luai_lon",
        )

    run = st.button(
        "Analyze Land Use", type="primary",
        key="luai_run", use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Land Use** to run the "
            "AI-powered land use intelligence scan."
        )
        return

    # -- Run analysis -----------------------------------------------------
    with st.spinner("Fetching environmental data and computing suitability..."):
        result = compute_land_use_intelligence(lat, lon)

    current_use = result["current_use"]
    optimal_use = result["optimal_use"]
    scores = result["scores"]
    indicators = result["current_indicators"]
    recommendations = result["transition_recommendations"]
    conflicts = result["conflicts"]

    cur_info = LAND_USE_TYPES.get(current_use, {})
    opt_info = LAND_USE_TYPES.get(optimal_use, {})

    # =====================================================================
    # Current vs Optimal header (side by side)
    # =====================================================================
    st.markdown("---")
    h_left, h_right = st.columns(2)
    with h_left:
        st.markdown(
            f'<div style="background:#1a1a2e;border:2px solid {cur_info.get("color","#8b97b0")};'
            f'border-radius:12px;padding:16px;text-align:center;">'
            f'<p style="color:#8b97b0;margin:0 0 4px 0;font-size:12px;">'
            f'CURRENT LAND USE</p>'
            f'<h3 style="color:{cur_info.get("color","#e8ecf4")};margin:0;">'
            f'{cur_info.get("name", current_use)}</h3>'
            f'<p style="color:#5a6580;margin:4px 0 0 0;font-size:13px;">'
            f'Suitability: {scores.get(current_use, 0)}/100</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with h_right:
        st.markdown(
            f'<div style="background:#1a1a2e;border:2px solid {opt_info.get("color","#06b6d4")};'
            f'border-radius:12px;padding:16px;text-align:center;">'
            f'<p style="color:#8b97b0;margin:0 0 4px 0;font-size:12px;">'
            f'OPTIMAL LAND USE</p>'
            f'<h3 style="color:{opt_info.get("color","#06b6d4")};margin:0;">'
            f'{opt_info.get("name", optimal_use)}</h3>'
            f'<p style="color:#5a6580;margin:4px 0 0 0;font-size:13px;">'
            f'Suitability: {scores.get(optimal_use, 0)}/100</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # =====================================================================
    # Horizontal bar chart -- all 10 land use types sorted by score
    # =====================================================================
    st.markdown("### Land Use Suitability Scores")

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    bar_names = [LAND_USE_TYPES.get(k, {}).get("name", k) for k, _ in sorted_items]
    bar_values = [v for _, v in sorted_items]
    bar_colors = [LAND_USE_TYPES.get(k, {}).get("color", "#8b97b0") for k, _ in sorted_items]

    fig_bar = go.Figure(go.Bar(
        x=bar_values,
        y=bar_names,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{v}" for v in bar_values],
        textposition="outside",
        textfont=dict(color="#e8ecf4", size=12),
    ))
    fig_bar.update_layout(
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4", size=12),
        xaxis=dict(
            title="Suitability Score (0-100)",
            range=[0, 110],
            gridcolor="#2a3550",
            zeroline=False,
        ),
        yaxis=dict(autorange="reversed", gridcolor="#2a3550"),
        margin=dict(l=10, r=30, t=10, b=40),
        height=380,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="lua_pchart1")

    # =====================================================================
    # Top 3 optimal uses -- detailed cards
    # =====================================================================
    st.markdown("### Top 3 Recommended Uses")
    top3 = sorted_items[:3]
    card_cols = st.columns(3)
    for idx, (key, score) in enumerate(top3):
        info = LAND_USE_TYPES.get(key, {})
        reqs = info.get("requirements", {})
        req_lines = "".join(
            f'<li style="color:#8b97b0;font-size:11px;">'
            f'{rk.replace("_", " ").title()}: {rv}</li>'
            for rk, rv in reqs.items()
        )
        rank_label = ["BEST MATCH", "2ND BEST", "3RD BEST"][idx]
        with card_cols[idx]:
            st.markdown(
                f'<div style="background:#1a1a2e;border:1px solid {info.get("color","#2a3550")};'
                f'border-radius:12px;padding:14px;min-height:220px;">'
                f'<span style="background:{info.get("color","#06b6d4")};color:#0a0e1a;'
                f'font-size:10px;font-weight:bold;padding:2px 8px;border-radius:6px;">'
                f'{rank_label}</span>'
                f'<h4 style="color:{info.get("color","#e8ecf4")};margin:10px 0 4px 0;">'
                f'{info.get("name", key)}</h4>'
                f'<p style="color:#06b6d4;font-size:22px;font-weight:bold;margin:0;">'
                f'{score}/100</p>'
                f'<p style="color:#5a6580;font-size:11px;margin:6px 0 4px 0;">'
                f'Key Requirements:</p>'
                f'<ul style="margin:0;padding-left:16px;">{req_lines}</ul>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # =====================================================================
    # Radar chart -- environmental factors
    # =====================================================================
    st.markdown("### Environmental Factor Analysis")

    radar_labels = list(indicators.keys())
    radar_values = list(indicators.values())
    # Close the polygon
    radar_labels_closed = radar_labels + [radar_labels[0]]
    radar_values_closed = radar_values + [radar_values[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values_closed,
        theta=radar_labels_closed,
        fill="toself",
        fillcolor="rgba(6, 182, 212, 0.18)",
        line=dict(color="#06b6d4", width=2),
        marker=dict(size=6, color="#06b6d4"),
        name="Environmental Factors",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#2a3550",
                tickfont=dict(color="#5a6580", size=10),
            ),
            angularaxis=dict(
                gridcolor="#2a3550",
                tickfont=dict(color="#8b97b0", size=11),
            ),
        ),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=400,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="lua_pchart2")

    # =====================================================================
    # Transition Recommendations
    # =====================================================================
    st.markdown("### Transition Recommendations")

    if recommendations:
        for rec in recommendations:
            priority = rec.get("priority", "Low")
            p_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}.get(
                priority, "#8b97b0"
            )
            st.markdown(
                f'<div style="background:#1a1a2e;border-left:4px solid {p_color};'
                f'border-radius:0 10px 10px 0;padding:12px 16px;margin:8px 0;">'
                f'<span style="background:{p_color};color:#0a0e1a;font-size:10px;'
                f'font-weight:bold;padding:2px 8px;border-radius:4px;">'
                f'{priority} Priority</span>'
                f'<p style="color:#e8ecf4;margin:8px 0 2px 0;font-size:14px;">'
                f'{rec.get("from_use", "?")}  &#8594;  {rec.get("to_use", "?")}'
                f'<span style="color:#06b6d4;font-size:12px;margin-left:10px;">'
                f'(+{rec.get("score_gain", 0)} points)</span></p>'
                f'<p style="color:#8b97b0;margin:0;font-size:12px;">'
                f'{rec.get("reason", "")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success(
            "Current land use aligns well with environmental conditions. "
            "No significant transitions recommended."
        )

    # =====================================================================
    # Conflict Warnings
    # =====================================================================
    st.markdown("### Conflict Warnings")

    if conflicts:
        for ckey in conflicts:
            c_info = LAND_USE_TYPES.get(ckey, {})
            c_score = scores.get(ckey, 0)
            st.markdown(
                f'<div style="background:rgba(239,68,68,0.08);border:1px solid #ef4444;'
                f'border-radius:10px;padding:10px 14px;margin:6px 0;">'
                f'<span style="color:#ef4444;font-weight:bold;font-size:13px;">'
                f'Low Suitability: {c_info.get("name", ckey)}</span>'
                f'<span style="color:#8b97b0;font-size:12px;margin-left:10px;">'
                f'Score: {c_score}/100</span>'
                f'<p style="color:#8b97b0;margin:4px 0 0 0;font-size:12px;">'
                f'This land use type is poorly suited to the environmental conditions '
                f'at this location. Implementing {c_info.get("name", ckey)} here would '
                f'likely face significant natural constraints.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info(
            "No severe conflict warnings. All land use types score above the "
            "minimum viability threshold (30/100)."
        )
