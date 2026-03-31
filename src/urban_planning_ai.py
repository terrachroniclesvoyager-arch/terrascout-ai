"""
Urban Planning Intelligence AI module for TerraScout AI.
Provides comprehensive urban development analysis and zoning recommendations
by synthesizing multi-source geospatial data: soil stability, weather patterns,
water features, elevation terrain, land use infrastructure, and protected areas.
Computes 8 urban metrics and zoning suitability scores for 8 zone types.
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
# ZONING TYPE DEFINITIONS
# ============================================================================

ZONING_TYPES = {
    "residential_low": {
        "name": "Low-Density Residential",
        "color": "#60a5fa",
        "icon": "home",
        "description": (
            "Single-family homes, townhouses, and low-rise housing with gardens. "
            "Requires flat terrain, adequate drainage, and access to services."
        ),
    },
    "residential_high": {
        "name": "High-Density Residential",
        "color": "#3b82f6",
        "icon": "building",
        "description": (
            "Apartment blocks, condominiums, and multi-story housing complexes. "
            "Needs strong infrastructure, transit links, and solid ground."
        ),
    },
    "commercial": {
        "name": "Commercial District",
        "color": "#8b5cf6",
        "icon": "store",
        "description": (
            "Retail centres, offices, and business parks. Demands high road "
            "connectivity, existing infrastructure, and population catchment."
        ),
    },
    "industrial": {
        "name": "Industrial Zone",
        "color": "#ef4444",
        "icon": "industry",
        "description": (
            "Manufacturing plants, warehouses, and logistics hubs. Requires flat "
            "land, transport corridors, and separation from residential areas."
        ),
    },
    "green_space": {
        "name": "Green Space / Park",
        "color": "#22c55e",
        "icon": "tree",
        "description": (
            "Public parks, nature reserves, and recreational green areas. "
            "Prioritises ecological value, water features, and low development."
        ),
    },
    "mixed_use": {
        "name": "Mixed-Use Development",
        "color": "#f59e0b",
        "icon": "city",
        "description": (
            "Combined residential, commercial, and leisure within a single zone. "
            "Needs moderate infrastructure and good connectivity."
        ),
    },
    "institutional": {
        "name": "Institutional / Civic",
        "color": "#06b6d4",
        "icon": "landmark",
        "description": (
            "Schools, hospitals, government offices, and cultural centres. "
            "Requires central accessibility and service coverage."
        ),
    },
    "transport_corridor": {
        "name": "Transport Corridor",
        "color": "#64748b",
        "icon": "road",
        "description": (
            "Major road arteries, rail lines, transit hubs, and logistics routes. "
            "Needs flat to moderate terrain and existing road network foundations."
        ),
    },
}

# ============================================================================
# CORE INTELLIGENCE FUNCTION
# ============================================================================

@st.cache_data(ttl=1800)
def compute_urban_planning(lat: float, lon: float) -> dict:
    """
    Fetch multi-source geospatial data and compute urban planning metrics,
    zoning suitability scores, current urban profile, development capacity,
    and actionable recommendations.
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
    # 3. Derive urban indicators from raw data
    # ------------------------------------------------------------------

    # --- Soil stability indicators ---
    clay_pct = 0.0
    soc_value = 0.0
    ph_value = 7.0
    for layer in layers:
        lname = layer.get("name", "")
        depths = layer.get("depths", [])
        if depths:
            raw = depths[0].get("values", {}).get("mean")
            if raw is not None:
                if lname == "clay":
                    clay_pct = raw / 10.0
                elif lname == "soc":
                    soc_value = raw / 10.0
                elif lname == "phh2o":
                    ph_value = raw / 10.0

    ground_stability = max(0, min(100, 80 - clay_pct * 0.8 + min(soc_value, 10)))

    # --- Weather / climate indicators ---
    temp_now = current_wx.get("temperature_2m", 15.0)
    humidity = current_wx.get("relative_humidity_2m", 50)
    precip_list = daily_wx.get("precipitation_sum", [])
    precip_filtered = [p for p in precip_list if p is not None]
    total_precip = sum(precip_filtered) if precip_filtered else 0.0
    annual_precip_est = (
        total_precip * (365.0 / max(len(precip_filtered), 1))
        if precip_filtered
        else 500.0
    )
    climate_comfort = min(100, max(0, 100 - abs(temp_now - 20) * 3 - max(0, 30 - humidity) * 0.5))
    flood_risk_precip = min(100, annual_precip_est / 15.0)

    # --- Water feature indicators ---
    water_count = len(elements_water)
    water_proximity = min(100, water_count * 8)

    # --- Elevation / terrain indicators ---
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
    steep_slope = min(100, elev_range * 3)

    # --- Infrastructure analysis from OSM elements ---
    building_count = 0
    residential_buildings = 0
    commercial_buildings = 0
    industrial_buildings = 0
    road_count = 0
    road_primary = 0
    road_secondary = 0
    road_tertiary = 0
    park_count = 0
    forest_count = 0
    farmland_count = 0
    school_count = 0
    hospital_count = 0
    fire_station_count = 0

    for el in elements_infra:
        tags = el.get("tags", {})
        bld = tags.get("building", "")
        if bld:
            building_count += 1
            if bld in ("residential", "apartments", "house", "detached", "terrace"):
                residential_buildings += 1
            elif bld in ("commercial", "office", "retail", "shop"):
                commercial_buildings += 1
            elif bld in ("industrial", "warehouse", "factory"):
                industrial_buildings += 1
        hw = tags.get("highway", "")
        if hw:
            road_count += 1
            if hw in ("primary", "trunk", "motorway"):
                road_primary += 1
            elif hw in ("secondary", "tertiary"):
                road_secondary += 1
            else:
                road_tertiary += 1
        lu = tags.get("landuse", "")
        if lu in ("farmland", "farm", "orchard", "vineyard"):
            farmland_count += 1
        elif lu == "forest":
            forest_count += 1
        if tags.get("leisure") == "park":
            park_count += 1
        amenity = tags.get("amenity", "")
        if amenity in ("school", "university", "college"):
            school_count += 1
        elif amenity in ("hospital", "clinic", "doctors"):
            hospital_count += 1
        elif amenity == "fire_station":
            fire_station_count += 1

    # --- Protected area score ---
    protected_count = len(protected_els)
    protected_score = min(100, protected_count * 25)

    # --- Derived composite indicators ---
    total_natural = park_count + forest_count + farmland_count
    total_built = building_count + road_count
    green_ratio = (
        (total_natural / max(total_natural + total_built, 1)) * 100
    )

    service_count = school_count + hospital_count + fire_station_count
    service_coverage = min(100, service_count * 12)

    infra_quality = min(100, (road_primary * 10 + road_secondary * 5 + road_tertiary * 2 + building_count))

    dev_pressure = min(100, building_count * 2 + road_count)

    env_constraint = min(100, int(
        protected_score * 0.35
        + flood_risk_precip * 0.30
        + steep_slope * 0.35
    ))

    livability = min(100, int(
        service_coverage * 0.30
        + green_ratio * 0.25
        + climate_comfort * 0.25
        + max(0, 100 - env_constraint) * 0.20
    ))

    # ------------------------------------------------------------------
    # 4. Build 8 urban metrics (0-100)
    # ------------------------------------------------------------------
    building_density = min(100, building_count * 2)
    road_connectivity = min(100, road_count * 3)

    metrics = {
        "Building Density": round(building_density, 1),
        "Road Connectivity": round(road_connectivity, 1),
        "Service Coverage": round(service_coverage, 1),
        "Green Space Ratio": round(green_ratio, 1),
        "Infrastructure Quality": round(infra_quality, 1),
        "Development Pressure": round(dev_pressure, 1),
        "Environmental Constraint": round(env_constraint, 1),
        "Livability Score": round(livability, 1),
    }

    # ------------------------------------------------------------------
    # 5. Current urban profile
    # ------------------------------------------------------------------
    if building_density >= 70:
        density_class = "Dense Urban Core"
    elif building_density >= 45:
        density_class = "Urban"
    elif building_density >= 20:
        density_class = "Suburban"
    elif building_density >= 5:
        density_class = "Peri-Urban"
    else:
        density_class = "Rural / Undeveloped"

    current_profile = {
        "density_class": density_class,
        "building_count": building_count,
        "residential_pct": round(
            (residential_buildings / max(building_count, 1)) * 100, 1
        ),
        "commercial_pct": round(
            (commercial_buildings / max(building_count, 1)) * 100, 1
        ),
        "industrial_pct": round(
            (industrial_buildings / max(building_count, 1)) * 100, 1
        ),
        "road_network": road_count,
        "green_spaces": park_count + forest_count,
        "services": service_count,
    }

    # ------------------------------------------------------------------
    # 6. Zoning suitability scores (0-100 per zone)
    # ------------------------------------------------------------------
    drainage = max(0, 100 - clay_pct * 1.5)

    zoning_scores = {}

    # Residential Low: flat + drainage + green spaces + low density pressure
    zoning_scores["residential_low"] = min(100, int(
        flatness * 0.30
        + drainage * 0.20
        + min(100, green_ratio * 2) * 0.25
        + max(0, 100 - dev_pressure) * 0.25
    ))

    # Residential High: infrastructure + roads + services + ground stability
    zoning_scores["residential_high"] = min(100, int(
        infra_quality * 0.25
        + road_connectivity * 0.25
        + service_coverage * 0.25
        + ground_stability * 0.25
    ))

    # Commercial: roads + building density + infrastructure + flat
    zoning_scores["commercial"] = min(100, int(
        road_connectivity * 0.30
        + building_density * 0.25
        + infra_quality * 0.25
        + flatness * 0.20
    ))

    # Industrial: flat + transport links + separation from residential + water
    separation = max(0, 100 - residential_buildings * 3)
    zoning_scores["industrial"] = min(100, int(
        flatness * 0.30
        + min(100, road_primary * 15) * 0.25
        + separation * 0.20
        + water_proximity * 0.25
    ))

    # Green Space: water + low development + protected areas + ecology
    ecology_proxy = min(100, water_proximity * 0.4 + green_ratio * 0.3 + protected_score * 0.3)
    zoning_scores["green_space"] = min(100, int(
        ecology_proxy * 0.30
        + water_proximity * 0.25
        + max(0, 100 - building_density) * 0.25
        + protected_score * 0.20
    ))

    # Mixed Use: moderate infra + roads + livability + building density
    zoning_scores["mixed_use"] = min(100, int(
        infra_quality * 0.25
        + road_connectivity * 0.25
        + livability * 0.25
        + min(100, building_density * 0.8) * 0.25
    ))

    # Institutional: service coverage + roads + centrality + flat
    centrality = min(100, (building_density + road_connectivity) / 2)
    zoning_scores["institutional"] = min(100, int(
        service_coverage * 0.25
        + road_connectivity * 0.25
        + centrality * 0.25
        + flatness * 0.25
    ))

    # Transport Corridor: roads + flat + infrastructure + connectivity
    zoning_scores["transport_corridor"] = min(100, int(
        road_connectivity * 0.30
        + flatness * 0.25
        + infra_quality * 0.25
        + min(100, road_primary * 12 + road_secondary * 6) * 0.20
    ))

    # ------------------------------------------------------------------
    # 7. Development capacity (overall 0-100)
    # ------------------------------------------------------------------
    development_capacity = min(100, int(
        flatness * 0.20
        + ground_stability * 0.15
        + infra_quality * 0.15
        + road_connectivity * 0.15
        + max(0, 100 - env_constraint) * 0.15
        + drainage * 0.10
        + climate_comfort * 0.10
    ))

    # ------------------------------------------------------------------
    # 8. Recommendations
    # ------------------------------------------------------------------
    sorted_zones = sorted(zoning_scores.items(), key=lambda x: x[1], reverse=True)
    best_zone = sorted_zones[0][0] if sorted_zones else "mixed_use"
    best_info = ZONING_TYPES.get(best_zone, {})

    recommendations = []

    recommendations.append({
        "priority": "High",
        "title": f"Primary zoning: {best_info.get('name', best_zone)}",
        "detail": (
            f"Highest suitability score of {zoning_scores.get(best_zone, 0)}/100. "
            f"{best_info.get('description', '')}"
        ),
    })

    if development_capacity > 60:
        recommendations.append({
            "priority": "High",
            "title": "Strong development potential",
            "detail": (
                f"Development capacity is {development_capacity}/100, indicating "
                f"favourable terrain, ground stability, and existing infrastructure "
                f"for new construction."
            ),
        })
    elif development_capacity > 30:
        recommendations.append({
            "priority": "Medium",
            "title": "Moderate development potential",
            "detail": (
                f"Development capacity is {development_capacity}/100. Some "
                f"constraints exist; targeted infrastructure investment may be needed."
            ),
        })
    else:
        recommendations.append({
            "priority": "Low",
            "title": "Limited development potential",
            "detail": (
                f"Development capacity is only {development_capacity}/100. "
                f"Significant environmental or terrain constraints limit expansion."
            ),
        })

    if env_constraint > 60:
        recommendations.append({
            "priority": "Medium",
            "title": "Environmental constraints detected",
            "detail": (
                f"Environmental constraint index is {env_constraint}/100. "
                f"Protected areas, flood risk, or steep slopes may restrict "
                f"certain development types."
            ),
        })

    if green_ratio < 15:
        recommendations.append({
            "priority": "Medium",
            "title": "Increase green space allocation",
            "detail": (
                f"Current green space ratio is {green_ratio:.1f}%. Urban planning "
                f"guidelines recommend at least 15-20% green coverage for livability."
            ),
        })

    if service_coverage < 40:
        recommendations.append({
            "priority": "High",
            "title": "Expand essential services",
            "detail": (
                f"Service coverage is only {service_coverage}/100. Additional "
                f"schools, healthcare facilities, or emergency services are needed."
            ),
        })

    return {
        "metrics": metrics,
        "zoning_scores": zoning_scores,
        "current_profile": current_profile,
        "development_capacity": development_capacity,
        "recommendations": recommendations,
    }


# ============================================================================
# RENDER FUNCTION
# ============================================================================

def render_urban_planning_tab():
    """Render the Urban Planning Intelligence AI tab in the Streamlit app."""

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
        'border:1px solid #334155;border-radius:12px;padding:18px 22px;'
        'margin-bottom:16px;">'
        '<h4 style="color:#64748b;margin:0 0 4px 0;">Urban Planning Intelligence AI</h4>'
        '<p style="color:#8b97b0;margin:0;font-size:13px;">'
        'Comprehensive urban development analysis and zoning recommendations '
        'synthesised from multi-source geospatial data.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # -- Location selector ------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.4, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="upai_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50

    with col_lat:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="upai_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="upai_lon",
        )

    run = st.button(
        "Analyze Urban Potential", type="primary",
        key="upai_run", use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Urban Potential** to run the "
            "AI-powered urban planning intelligence scan."
        )
        return

    # -- Run analysis -----------------------------------------------------
    with st.spinner("Fetching geospatial data and computing urban metrics..."):
        result = compute_urban_planning(lat, lon)

    metrics = result["metrics"]
    zoning_scores = result["zoning_scores"]
    profile = result["current_profile"]
    dev_capacity = result["development_capacity"]
    recommendations = result["recommendations"]

    # =====================================================================
    # Current Urban Profile header
    # =====================================================================
    st.markdown("---")
    density_class = profile.get("density_class", "Unknown")
    dc_colors = {
        "Dense Urban Core": "#ef4444",
        "Urban": "#f59e0b",
        "Suburban": "#3b82f6",
        "Peri-Urban": "#22c55e",
        "Rural / Undeveloped": "#64748b",
    }
    dc_color = dc_colors.get(density_class, "#475569")

    st.markdown(
        f'<div style="background:#1a1a2e;border:2px solid {dc_color};'
        f'border-radius:12px;padding:16px;text-align:center;margin-bottom:16px;">'
        f'<p style="color:#8b97b0;margin:0 0 4px 0;font-size:12px;">'
        f'CURRENT URBAN CLASSIFICATION</p>'
        f'<h3 style="color:{dc_color};margin:0;">{density_class}</h3>'
        f'<p style="color:#5a6580;margin:6px 0 0 0;font-size:13px;">'
        f'{profile.get("building_count", 0)} buildings &middot; '
        f'{profile.get("road_network", 0)} road segments &middot; '
        f'{profile.get("green_spaces", 0)} green spaces &middot; '
        f'{profile.get("services", 0)} services</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # =====================================================================
    # 8 Metric Cards in 4x2 grid
    # =====================================================================
    st.markdown("### Urban Metrics")

    metric_colors = {
        "Building Density": "#475569",
        "Road Connectivity": "#64748b",
        "Service Coverage": "#06b6d4",
        "Green Space Ratio": "#22c55e",
        "Infrastructure Quality": "#3b82f6",
        "Development Pressure": "#f59e0b",
        "Environmental Constraint": "#ef4444",
        "Livability Score": "#8b5cf6",
    }

    metric_keys = list(metrics.keys())
    row1 = metric_keys[:4]
    row2 = metric_keys[4:]

    for row_items in [row1, row2]:
        cols = st.columns(4)
        for idx, mkey in enumerate(row_items):
            mval = metrics.get(mkey, 0)
            mcolor = metric_colors.get(mkey, "#475569")
            bar_width = max(2, min(100, mval))
            with cols[idx]:
                st.markdown(
                    f'<div style="background:#1a1a2e;border:1px solid #334155;'
                    f'border-radius:10px;padding:12px;min-height:100px;">'
                    f'<p style="color:#8b97b0;margin:0;font-size:11px;">{mkey}</p>'
                    f'<p style="color:{mcolor};font-size:24px;font-weight:bold;'
                    f'margin:4px 0;">{mval}</p>'
                    f'<div style="background:#0f172a;border-radius:4px;height:6px;'
                    f'overflow:hidden;">'
                    f'<div style="background:{mcolor};width:{bar_width}%;height:100%;'
                    f'border-radius:4px;"></div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # =====================================================================
    # Radar chart of 8 metrics
    # =====================================================================
    st.markdown("### Metrics Radar")

    radar_labels = list(metrics.keys())
    radar_values = list(metrics.values())
    radar_labels_closed = radar_labels + [radar_labels[0]]
    radar_values_closed = radar_values + [radar_values[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values_closed,
        theta=radar_labels_closed,
        fill="toself",
        fillcolor="rgba(100, 116, 139, 0.18)",
        line=dict(color="#64748b", width=2),
        marker=dict(size=6, color="#64748b"),
        name="Urban Metrics",
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
        height=420,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="upa_pchart1")

    # =====================================================================
    # Zoning Suitability horizontal bar chart
    # =====================================================================
    st.markdown("### Zoning Suitability Scores")

    sorted_zones = sorted(zoning_scores.items(), key=lambda x: x[1], reverse=True)
    bar_names = [ZONING_TYPES.get(k, {}).get("name", k) for k, _ in sorted_zones]
    bar_values = [v for _, v in sorted_zones]
    bar_colors = [ZONING_TYPES.get(k, {}).get("color", "#475569") for k, _ in sorted_zones]

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
        height=360,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="upa_pchart2")

    # =====================================================================
    # Top 3 Recommended Zones -- detailed cards
    # =====================================================================
    st.markdown("### Top 3 Recommended Zones")
    top3 = sorted_zones[:3]
    card_cols = st.columns(3)
    rank_labels = ["BEST MATCH", "2ND BEST", "3RD BEST"]

    for idx, (zkey, zscore) in enumerate(top3):
        zinfo = ZONING_TYPES.get(zkey, {})
        with card_cols[idx]:
            st.markdown(
                f'<div style="background:#1a1a2e;border:1px solid {zinfo.get("color","#334155")};'
                f'border-radius:12px;padding:14px;min-height:200px;">'
                f'<span style="background:{zinfo.get("color","#475569")};color:#0a0e1a;'
                f'font-size:10px;font-weight:bold;padding:2px 8px;border-radius:6px;">'
                f'{rank_labels[idx]}</span>'
                f'<h4 style="color:{zinfo.get("color","#e8ecf4")};margin:10px 0 4px 0;">'
                f'{zinfo.get("name", zkey)}</h4>'
                f'<p style="color:#64748b;font-size:22px;font-weight:bold;margin:0;">'
                f'{zscore}/100</p>'
                f'<p style="color:#8b97b0;font-size:11px;margin:8px 0 0 0;">'
                f'{zinfo.get("description", "")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # =====================================================================
    # Development Capacity Gauge
    # =====================================================================
    st.markdown("### Development Capacity")

    if dev_capacity >= 70:
        gauge_color = "#22c55e"
        cap_label = "High"
    elif dev_capacity >= 40:
        gauge_color = "#f59e0b"
        cap_label = "Moderate"
    else:
        gauge_color = "#ef4444"
        cap_label = "Low"

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=dev_capacity,
        number=dict(font=dict(color="#e8ecf4", size=40)),
        title=dict(
            text=f"Overall Development Capacity ({cap_label})",
            font=dict(color="#8b97b0", size=14),
        ),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#5a6580", tickfont=dict(color="#5a6580")),
            bar=dict(color=gauge_color),
            bgcolor="#0f172a",
            borderwidth=0,
            steps=[
                dict(range=[0, 30], color="#1e1e3a"),
                dict(range=[30, 60], color="#1a1a2e"),
                dict(range=[60, 100], color="#16213e"),
            ],
            threshold=dict(
                line=dict(color="#e8ecf4", width=2),
                thickness=0.75,
                value=dev_capacity,
            ),
        ),
    ))
    fig_gauge.update_layout(
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        margin=dict(l=30, r=30, t=60, b=20),
        height=280,
    )
    st.plotly_chart(fig_gauge, use_container_width=True, key="upa_pchart3")

    # =====================================================================
    # Recommendations Section
    # =====================================================================
    st.markdown("### Planning Recommendations")

    if recommendations:
        for rec in recommendations:
            priority = rec.get("priority", "Low")
            p_color = {
                "High": "#ef4444",
                "Medium": "#f59e0b",
                "Low": "#22c55e",
            }.get(priority, "#475569")
            st.markdown(
                f'<div style="background:#1a1a2e;border-left:4px solid {p_color};'
                f'border-radius:0 10px 10px 0;padding:12px 16px;margin:8px 0;">'
                f'<span style="background:{p_color};color:#0a0e1a;font-size:10px;'
                f'font-weight:bold;padding:2px 8px;border-radius:4px;">'
                f'{priority} Priority</span>'
                f'<p style="color:#e8ecf4;margin:8px 0 2px 0;font-size:14px;'
                f'font-weight:600;">{rec.get("title", "")}</p>'
                f'<p style="color:#8b97b0;margin:0;font-size:12px;">'
                f'{rec.get("detail", "")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success(
            "No critical planning recommendations at this time. "
            "The location shows balanced urban development characteristics."
        )
