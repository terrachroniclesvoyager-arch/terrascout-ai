"""
Logistics & Supply Chain AI module for TerraScout AI.
Analyzes logistics feasibility, transport connectivity, and supply chain
potential by synthesizing multi-source geospatial data: road/rail/air/maritime
networks, storage infrastructure, terrain constraints, and weather reliability.
Computes 7 logistics indices and an overall logistics score.
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
    fetch_water_features,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ============================================================================
# LOGISTICS INDEX DEFINITIONS
# ============================================================================

LOGISTICS_INDICES = {
    "Road Network": {
        "color": "#6b7fa3",
        "description": "Road quality and density across motorways, primary, secondary, and local roads.",
    },
    "Rail Connectivity": {
        "color": "#7e8ea6",
        "description": "Accessibility of railway lines and stations for freight and passenger rail.",
    },
    "Air Access": {
        "color": "#8fa0b8",
        "description": "Proximity and availability of airports and helipads for air freight.",
    },
    "Maritime Access": {
        "color": "#5a7a9e",
        "description": "Port, harbour, and ferry terminal access for waterborne logistics.",
    },
    "Storage Infrastructure": {
        "color": "#4d6d8e",
        "description": "Warehouses, fuel stations, and parking areas supporting distribution.",
    },
    "Terrain Feasibility": {
        "color": "#8493a8",
        "description": "Flatness and accessibility of terrain for ground transport operations.",
    },
    "Weather Reliability": {
        "color": "#9aa8ba",
        "description": "Ratio of favourable weather days supporting reliable delivery schedules.",
    },
}


# ============================================================================
# CORE INTELLIGENCE FUNCTION
# ============================================================================

@st.cache_data(ttl=1800)
def compute_logistics(lat: float, lon: float) -> dict:
    """
    Fetch multi-source geospatial data and compute logistics indices,
    transport network counts, terrain constraints, and recommendations.
    """

    # ------------------------------------------------------------------
    # 1. Fetch all data sources
    # ------------------------------------------------------------------
    infra = fetch_landuse_infrastructure(lat, lon, radius=10000)
    water = fetch_water_features(lat, lon)
    elev = fetch_elevation_grid(lat, lon)
    weather = fetch_weather_data(lat, lon)

    # ------------------------------------------------------------------
    # 2. Safe extraction with defensive patterns
    # ------------------------------------------------------------------
    elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    elements_water = (water if isinstance(water, dict) else {}).get("elements", [])
    elevations = (elev if isinstance(elev, dict) else {}).get("grid_elevations", [])
    valid_elevs = [e for e in elevations if e is not None]

    current_wx = (weather if isinstance(weather, dict) else {}).get("current", {})
    daily_wx = (weather if isinstance(weather, dict) else {}).get("daily", {})

    # ------------------------------------------------------------------
    # 3. Transport network analysis
    # ------------------------------------------------------------------

    # Road types
    road_motorway = 0
    road_primary = 0
    road_secondary = 0
    road_tertiary = 0
    road_residential = 0
    road_track = 0

    # Rail
    rail_lines = 0
    rail_stations = 0

    # Air
    airports = 0
    helipads = 0

    # Water transport
    ports = 0
    harbours = 0
    ferry_terminals = 0
    navigable_waterways = 0

    # Storage / distribution
    warehouses = 0
    fuel_stations = 0
    parking_areas = 0

    for el in elements:
        tags = el.get("tags", {})

        # Roads
        hw = tags.get("highway", "")
        if hw in ("motorway", "motorway_link"):
            road_motorway += 1
        elif hw in ("primary", "primary_link", "trunk", "trunk_link"):
            road_primary += 1
        elif hw in ("secondary", "secondary_link"):
            road_secondary += 1
        elif hw in ("tertiary", "tertiary_link"):
            road_tertiary += 1
        elif hw in ("residential", "living_street", "unclassified"):
            road_residential += 1
        elif hw in ("track", "service"):
            road_track += 1

        # Railways
        rw = tags.get("railway", "")
        if rw in ("rail", "light_rail", "narrow_gauge", "tram"):
            rail_lines += 1
        elif rw in ("station", "halt", "stop"):
            rail_stations += 1

        # Airports and helipads
        aeroway = tags.get("aeroway", "")
        if aeroway in ("aerodrome", "runway", "terminal"):
            airports += 1
        elif aeroway == "helipad":
            helipads += 1

        # Ports / harbours / ferry
        if tags.get("harbour") == "yes" or tags.get("landuse") == "harbour":
            harbours += 1
        if tags.get("industrial") == "port" or tags.get("man_made") == "pier":
            ports += 1
        amenity = tags.get("amenity", "")
        if amenity == "ferry_terminal":
            ferry_terminals += 1

        # Warehouses
        if tags.get("building") == "warehouse":
            warehouses += 1

        # Fuel stations
        if amenity == "fuel":
            fuel_stations += 1

        # Parking
        if amenity == "parking" or tags.get("landuse") == "parking":
            parking_areas += 1

    # Navigable waterways from water features
    for el in elements_water:
        tags = el.get("tags", {})
        wway = tags.get("waterway", "")
        if wway in ("river", "canal"):
            navigable_waterways += 1

    # ------------------------------------------------------------------
    # 4. Transport counts summary
    # ------------------------------------------------------------------
    transport_counts = {
        "Motorways": road_motorway,
        "Primary Roads": road_primary,
        "Secondary Roads": road_secondary,
        "Tertiary Roads": road_tertiary,
        "Residential Roads": road_residential,
        "Tracks / Service": road_track,
        "Railway Lines": rail_lines,
        "Railway Stations": rail_stations,
        "Airports": airports,
        "Helipads": helipads,
        "Ports": ports,
        "Harbours": harbours,
        "Ferry Terminals": ferry_terminals,
        "Navigable Waterways": navigable_waterways,
        "Warehouses": warehouses,
        "Fuel Stations": fuel_stations,
        "Parking Areas": parking_areas,
    }

    # ------------------------------------------------------------------
    # 5. Terrain constraints
    # ------------------------------------------------------------------
    if valid_elevs:
        elev_min = min(valid_elevs)
        elev_max = max(valid_elevs)
        elev_mean = sum(valid_elevs) / len(valid_elevs)
    else:
        elev_min = 0
        elev_max = 0
        elev_mean = 0

    elev_range = elev_max - elev_min
    slope_severity = min(100, elev_range * 2.5)
    high_elevation_penalty = min(100, max(0, (elev_mean - 500) * 0.08))

    # Water crossings (bridges needed)
    water_crossing_count = 0
    for el in elements_water:
        tags = el.get("tags", {})
        ww = tags.get("waterway", "")
        if ww in ("river", "stream", "canal"):
            water_crossing_count += 1

    constraints = {
        "elevation_min": round(elev_min, 1),
        "elevation_max": round(elev_max, 1),
        "elevation_mean": round(elev_mean, 1),
        "elevation_range": round(elev_range, 1),
        "slope_severity": round(slope_severity, 1),
        "high_elevation_penalty": round(high_elevation_penalty, 1),
        "water_crossings": water_crossing_count,
    }

    # ------------------------------------------------------------------
    # 6. Weather impact
    # ------------------------------------------------------------------
    precip_list = daily_wx.get("precipitation_sum", [])
    precip_filtered = [p for p in precip_list if p is not None]
    total_precip = sum(precip_filtered) if precip_filtered else 0.0

    temp_max_list = daily_wx.get("temperature_2m_max", [])
    temp_min_list = daily_wx.get("temperature_2m_min", [])
    wind_list = daily_wx.get("wind_speed_10m_max", [])

    # Extreme weather days (heavy rain >20mm, extreme temp, or high wind)
    extreme_days = 0
    forecast_days = max(len(precip_filtered), 1)
    for i in range(len(precip_filtered)):
        is_extreme = False
        if precip_filtered[i] > 20:
            is_extreme = True
        if i < len(temp_max_list) and temp_max_list[i] is not None and temp_max_list[i] > 42:
            is_extreme = True
        if i < len(temp_min_list) and temp_min_list[i] is not None and temp_min_list[i] < -15:
            is_extreme = True
        if i < len(wind_list) and wind_list[i] is not None and wind_list[i] > 60:
            is_extreme = True
        if is_extreme:
            extreme_days += 1

    good_weather_ratio = max(0, (forecast_days - extreme_days) / forecast_days) * 100
    avg_daily_precip = (total_precip / forecast_days) if precip_filtered else 5.0

    # ------------------------------------------------------------------
    # 7. Compute 7 logistics indices (0-100)
    # ------------------------------------------------------------------
    total_roads = (road_motorway + road_primary + road_secondary
                   + road_tertiary + road_residential + road_track)
    road_quality_score = min(100, (
        road_motorway * 20
        + road_primary * 12
        + road_secondary * 6
        + road_tertiary * 3
        + road_residential * 1
        + road_track * 0.5
    ))
    road_density_score = min(100, total_roads * 2)
    idx_road = min(100, round(road_quality_score * 0.6 + road_density_score * 0.4, 1))

    idx_rail = min(100, round(
        min(100, rail_lines * 15) * 0.6
        + min(100, rail_stations * 30) * 0.4
    , 1))

    idx_air = min(100, round(
        min(100, airports * 40) * 0.7
        + min(100, helipads * 25) * 0.3
    , 1))

    idx_maritime = min(100, round(
        min(100, ports * 30) * 0.3
        + min(100, harbours * 30) * 0.3
        + min(100, ferry_terminals * 25) * 0.2
        + min(100, navigable_waterways * 10) * 0.2
    , 1))

    idx_storage = min(100, round(
        min(100, warehouses * 15) * 0.5
        + min(100, fuel_stations * 12) * 0.3
        + min(100, parking_areas * 5) * 0.2
    , 1))

    flatness = max(0, 100 - slope_severity)
    accessibility = max(0, 100 - high_elevation_penalty)
    idx_terrain = min(100, round(flatness * 0.6 + accessibility * 0.4, 1))

    precip_penalty = min(50, avg_daily_precip * 3)
    idx_weather = min(100, round(
        good_weather_ratio * 0.7
        + max(0, 100 - precip_penalty) * 0.3
    , 1))

    indices = {
        "Road Network": idx_road,
        "Rail Connectivity": idx_rail,
        "Air Access": idx_air,
        "Maritime Access": idx_maritime,
        "Storage Infrastructure": idx_storage,
        "Terrain Feasibility": idx_terrain,
        "Weather Reliability": idx_weather,
    }

    # ------------------------------------------------------------------
    # 8. Overall Logistics Score (weighted average)
    # ------------------------------------------------------------------
    weights = {
        "Road Network": 0.25,
        "Rail Connectivity": 0.15,
        "Air Access": 0.10,
        "Maritime Access": 0.10,
        "Storage Infrastructure": 0.15,
        "Terrain Feasibility": 0.15,
        "Weather Reliability": 0.10,
    }
    overall = round(sum(indices[k] * weights[k] for k in indices), 1)
    overall = min(100, max(0, overall))

    if overall >= 75:
        classification = "Excellent Logistics Hub"
    elif overall >= 55:
        classification = "Good Logistics Corridor"
    elif overall >= 35:
        classification = "Moderate Logistics Potential"
    elif overall >= 15:
        classification = "Challenging Logistics Environment"
    else:
        classification = "Severe Logistics Constraints"

    # ------------------------------------------------------------------
    # 9. Infrastructure details
    # ------------------------------------------------------------------
    infrastructure_details = {
        "total_roads": total_roads,
        "total_rail": rail_lines + rail_stations,
        "total_air": airports + helipads,
        "total_maritime": ports + harbours + ferry_terminals,
        "total_storage": warehouses + fuel_stations + parking_areas,
    }

    # ------------------------------------------------------------------
    # 10. Recommendations
    # ------------------------------------------------------------------
    recommendations = []

    if idx_road < 30:
        recommendations.append({
            "priority": "High",
            "title": "Critical road infrastructure gap",
            "detail": (
                f"Road Network index is only {idx_road}/100. Major investment in "
                f"road construction (especially primary/secondary roads) is needed "
                f"to support any supply chain operations."
            ),
        })
    elif idx_road < 60:
        recommendations.append({
            "priority": "Medium",
            "title": "Road network improvement needed",
            "detail": (
                f"Road Network index is {idx_road}/100. Upgrading existing roads "
                f"and adding secondary connections would improve freight throughput."
            ),
        })

    if idx_rail < 20:
        recommendations.append({
            "priority": "Medium",
            "title": "No significant rail connectivity",
            "detail": (
                f"Rail Connectivity index is {idx_rail}/100. Consider feasibility "
                f"of rail siding or intermodal terminal to reduce road dependence."
            ),
        })

    if idx_storage < 25:
        recommendations.append({
            "priority": "High",
            "title": "Storage and distribution infrastructure lacking",
            "detail": (
                f"Storage Infrastructure index is {idx_storage}/100. Warehouse "
                f"and fuel station development is critical for distribution viability."
            ),
        })

    if idx_terrain < 40:
        recommendations.append({
            "priority": "Medium",
            "title": "Terrain poses logistics challenges",
            "detail": (
                f"Terrain Feasibility index is {idx_terrain}/100. Steep slopes "
                f"(range: {elev_range:.0f}m) and high elevation ({elev_mean:.0f}m) "
                f"increase transport costs and limit vehicle types."
            ),
        })

    if idx_weather < 50:
        recommendations.append({
            "priority": "Medium",
            "title": "Weather reliability concerns",
            "detail": (
                f"Weather Reliability index is {idx_weather}/100. Frequent extreme "
                f"weather events or heavy precipitation may disrupt delivery schedules. "
                f"Consider climate-resilient routing and contingency planning."
            ),
        })

    if overall >= 55:
        recommendations.append({
            "priority": "Low",
            "title": "Location supports logistics operations",
            "detail": (
                f"Overall Logistics Score is {overall}/100 ({classification}). "
                f"The area has adequate multi-modal transport access and supporting "
                f"infrastructure for supply chain activities."
            ),
        })

    if not recommendations:
        recommendations.append({
            "priority": "Low",
            "title": "General logistics assessment",
            "detail": (
                f"Overall Logistics Score is {overall}/100 ({classification}). "
                f"Review individual indices for targeted improvement opportunities."
            ),
        })

    return {
        "overall": overall,
        "classification": classification,
        "indices": indices,
        "transport_counts": transport_counts,
        "infrastructure_details": infrastructure_details,
        "constraints": constraints,
        "recommendations": recommendations,
    }


# ============================================================================
# RENDER FUNCTION
# ============================================================================

def render_logistics_ai_tab():
    """Render the Logistics & Supply Chain AI tab in the Streamlit app."""

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
        'border:1px solid #334155;border-radius:12px;padding:18px 22px;'
        'margin-bottom:16px;">'
        '<h4 style="color:#6b7fa3;margin:0 0 4px 0;">Logistics &amp; Supply Chain AI</h4>'
        '<p style="color:#8b97b0;margin:0;font-size:13px;">'
        'Analyzes transport connectivity, storage infrastructure, terrain '
        'feasibility, and weather reliability for logistics operations.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # -- Location selector ------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.4, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="logai_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50

    with col_lat:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="logai_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="logai_lon",
        )

    run = st.button(
        "Analyze Logistics", type="primary",
        key="logai_run", use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Logistics** to run the "
            "AI-powered logistics and supply chain feasibility scan."
        )
        return

    # -- Run analysis -----------------------------------------------------
    with st.spinner("Fetching geospatial data and computing logistics indices..."):
        result = compute_logistics(lat, lon)

    overall = result["overall"]
    classification = result["classification"]
    indices = result["indices"]
    transport_counts = result["transport_counts"]
    infra_details = result["infrastructure_details"]
    constraints = result["constraints"]
    recommendations = result["recommendations"]

    # =====================================================================
    # Overall Logistics Score header
    # =====================================================================
    st.markdown("---")
    if overall >= 75:
        score_color = "#22c55e"
    elif overall >= 55:
        score_color = "#3b82f6"
    elif overall >= 35:
        score_color = "#f59e0b"
    else:
        score_color = "#ef4444"

    st.markdown(
        f'<div style="background:#1a1a2e;border:2px solid {score_color};'
        f'border-radius:12px;padding:16px;text-align:center;margin-bottom:16px;">'
        f'<p style="color:#8b97b0;margin:0 0 4px 0;font-size:12px;">'
        f'OVERALL LOGISTICS SCORE</p>'
        f'<h2 style="color:{score_color};margin:0;">{overall}/100</h2>'
        f'<p style="color:#5a6580;margin:6px 0 0 0;font-size:14px;">'
        f'{classification}</p>'
        f'<p style="color:#4d5d73;margin:4px 0 0 0;font-size:12px;">'
        f'{infra_details.get("total_roads", 0)} road segments &middot; '
        f'{infra_details.get("total_rail", 0)} rail features &middot; '
        f'{infra_details.get("total_air", 0)} air facilities &middot; '
        f'{infra_details.get("total_maritime", 0)} maritime features &middot; '
        f'{infra_details.get("total_storage", 0)} storage sites</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # =====================================================================
    # 7 Index Cards in rows
    # =====================================================================
    st.markdown("### Logistics Indices")

    index_keys = list(indices.keys())
    row1 = index_keys[:4]
    row2 = index_keys[4:]

    for row_items in [row1, row2]:
        cols = st.columns(len(row_items))
        for idx, ikey in enumerate(row_items):
            ival = indices.get(ikey, 0)
            iinfo = LOGISTICS_INDICES.get(ikey, {})
            icolor = iinfo.get("color", "#6b7fa3")
            bar_width = max(2, min(100, ival))
            with cols[idx]:
                st.markdown(
                    f'<div style="background:#1a1a2e;border:1px solid #334155;'
                    f'border-radius:10px;padding:12px;min-height:100px;">'
                    f'<p style="color:#8b97b0;margin:0;font-size:11px;">{ikey}</p>'
                    f'<p style="color:{icolor};font-size:24px;font-weight:bold;'
                    f'margin:4px 0;">{ival}</p>'
                    f'<div style="background:#0f172a;border-radius:4px;height:6px;'
                    f'overflow:hidden;">'
                    f'<div style="background:{icolor};width:{bar_width}%;height:100%;'
                    f'border-radius:4px;"></div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # =====================================================================
    # Radar chart of 7 indices
    # =====================================================================
    st.markdown("### Logistics Radar")

    radar_labels = list(indices.keys())
    radar_values = list(indices.values())
    radar_labels_closed = radar_labels + [radar_labels[0]]
    radar_values_closed = radar_values + [radar_values[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values_closed,
        theta=radar_labels_closed,
        fill="toself",
        fillcolor="rgba(107, 127, 163, 0.18)",
        line=dict(color="#6b7fa3", width=2),
        marker=dict(size=6, color="#6b7fa3"),
        name="Logistics Indices",
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
    st.plotly_chart(fig_radar, use_container_width=True, key="logai_pchart1")

    # =====================================================================
    # Transport Network Breakdown -- horizontal bar chart
    # =====================================================================
    st.markdown("### Transport Network Breakdown")

    # Filter to non-zero counts for cleaner display, but show all if all zero
    display_counts = {k: v for k, v in transport_counts.items() if v > 0}
    if not display_counts:
        display_counts = transport_counts

    sorted_transport = sorted(display_counts.items(), key=lambda x: x[1], reverse=True)
    bar_names = [k for k, _ in sorted_transport]
    bar_values = [v for _, v in sorted_transport]

    transport_colors = {
        "Motorways": "#4d6d8e",
        "Primary Roads": "#5a7a9e",
        "Secondary Roads": "#6b8aae",
        "Tertiary Roads": "#7e9abe",
        "Residential Roads": "#8fa8c8",
        "Tracks / Service": "#a0b6d0",
        "Railway Lines": "#6b7fa3",
        "Railway Stations": "#8493a8",
        "Airports": "#5a6d85",
        "Helipads": "#7a8da5",
        "Ports": "#4a6070",
        "Harbours": "#5a7080",
        "Ferry Terminals": "#6a8090",
        "Navigable Waterways": "#5a8090",
        "Warehouses": "#7b8a9a",
        "Fuel Stations": "#8b9aaa",
        "Parking Areas": "#9baaba",
    }
    bar_colors = [transport_colors.get(n, "#6b7fa3") for n in bar_names]

    fig_bar = go.Figure(go.Bar(
        x=bar_values,
        y=bar_names,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[str(v) for v in bar_values],
        textposition="outside",
        textfont=dict(color="#e8ecf4", size=12),
    ))
    fig_bar.update_layout(
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4", size=12),
        xaxis=dict(
            title="Count",
            gridcolor="#2a3550",
            zeroline=False,
        ),
        yaxis=dict(autorange="reversed", gridcolor="#2a3550"),
        margin=dict(l=10, r=40, t=10, b=40),
        height=max(280, len(bar_names) * 32),
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="logai_pchart2")

    # =====================================================================
    # Terrain Constraints section
    # =====================================================================
    st.markdown("### Terrain Constraints")

    tc1, tc2, tc3, tc4 = st.columns(4)
    constraint_items = [
        ("Elevation Range", f"{constraints.get('elevation_min', 0):.0f} - "
         f"{constraints.get('elevation_max', 0):.0f} m", tc1),
        ("Mean Elevation", f"{constraints.get('elevation_mean', 0):.0f} m", tc2),
        ("Slope Severity", f"{constraints.get('slope_severity', 0):.0f}/100", tc3),
        ("Water Crossings", f"{constraints.get('water_crossings', 0)}", tc4),
    ]

    for label, value, col in constraint_items:
        with col:
            st.markdown(
                f'<div style="background:#1a1a2e;border:1px solid #334155;'
                f'border-radius:10px;padding:12px;text-align:center;">'
                f'<p style="color:#8b97b0;margin:0;font-size:11px;">{label}</p>'
                f'<p style="color:#6b7fa3;font-size:20px;font-weight:bold;'
                f'margin:4px 0 0 0;">{value}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    slope_sev = constraints.get("slope_severity", 0)
    elev_pen = constraints.get("high_elevation_penalty", 0)
    water_cross = constraints.get("water_crossings", 0)

    constraint_notes = []
    if slope_sev > 60:
        constraint_notes.append(
            "Steep terrain significantly increases fuel consumption and limits "
            "heavy vehicle access. Consider alternative routing or rail options."
        )
    elif slope_sev > 30:
        constraint_notes.append(
            "Moderate slopes present manageable challenges. Standard freight "
            "vehicles can operate but with reduced efficiency."
        )
    if elev_pen > 30:
        constraint_notes.append(
            f"High elevation ({constraints.get('elevation_mean', 0):.0f}m) "
            f"increases engine stress and fuel costs for road freight."
        )
    if water_cross > 3:
        constraint_notes.append(
            f"{water_cross} water crossings detected. Bridge availability "
            f"and load capacity should be verified for heavy freight."
        )

    if constraint_notes:
        for note in constraint_notes:
            st.markdown(
                f'<div style="background:#1a1a2e;border-left:4px solid #6b7fa3;'
                f'border-radius:0 10px 10px 0;padding:10px 14px;margin:6px 0;">'
                f'<p style="color:#8b97b0;margin:0;font-size:12px;">{note}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # =====================================================================
    # Recommendations Section
    # =====================================================================
    st.markdown("### Logistics Recommendations")

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
            "No critical logistics recommendations at this time. "
            "The location shows adequate supply chain characteristics."
        )
