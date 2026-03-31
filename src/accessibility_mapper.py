# -*- coding: utf-8 -*-
"""
Accessibility & Reachability AI module for TerraScout AI.
Analyzes how accessible a location is by computing reachability scores
across multiple dimensions: road network, emergency services, education,
transport links, utilities, and water access.
"""

import html as html_module
import logging

import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
try:
    from streamlit_folium import st_folium
    HAS_ST_FOLIUM = True
except ImportError:
    HAS_ST_FOLIUM = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_landuse_infrastructure,
    fetch_water_features,
    fetch_weather_data,
    fetch_elevation_grid,
)
from src.map_factory import MapFactory

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

SCORE_WEIGHTS = {
    "Road Network": 0.25,
    "Emergency Services": 0.20,
    "Education & Health": 0.15,
    "Transport Links": 0.20,
    "Utilities": 0.10,
    "Water Access": 0.10,
}

DIMENSION_COLORS = {
    "Road Network": "#3b82f6",
    "Emergency Services": "#ef4444",
    "Education & Health": "#8b5cf6",
    "Transport Links": "#f59e0b",
    "Utilities": "#06b6d4",
    "Water Access": "#10b981",
}

DIMENSION_ICONS = {
    "Road Network": "road",
    "Emergency Services": "plus-sign",
    "Education & Health": "education",
    "Transport Links": "transfer",
    "Utilities": "flash",
    "Water Access": "tint",
}

MARKER_COLORS_BY_TYPE = {
    "road": "blue",
    "emergency": "red",
    "education": "purple",
    "transport": "orange",
    "utility": "cadetblue",
    "water": "green",
}


# =============================================================================
# CACHED COMPUTE FUNCTION
# =============================================================================

@st.cache_data(ttl=1800)
def compute_accessibility(lat, lon):
    """
    Compute accessibility and reachability scores for a given location.

    Returns a dict with:
        - overall_score (float 0-100)
        - scores (dict of dimension -> score)
        - details (dict of dimension -> count details)
        - classification (str)
        - classification_color (str)
    """
    # ---- Fetch data from APIs ----
    infra_data = fetch_landuse_infrastructure(lat, lon, radius=5000)
    water_data = fetch_water_features(lat, lon)
    elevation_data = fetch_elevation_grid(lat, lon, radius_deg=0.05, grid_size=5)

    elements = infra_data.get("elements", [])
    water_elements = water_data.get("elements", [])

    # ---- Count infrastructure by category ----
    # Roads
    road_counts = {
        "primary": 0,
        "secondary": 0,
        "tertiary": 0,
        "residential": 0,
        "track": 0,
    }
    # Services
    service_counts = {
        "hospital": 0,
        "school": 0,
        "fire_station": 0,
        "police": 0,
        "pharmacy": 0,
        "post_office": 0,
        "fuel": 0,
    }
    # Utilities
    utility_counts = {
        "power_line": 0,
        "comm_tower": 0,
    }
    # Transport
    transport_counts = {
        "bus_stop": 0,
        "railway": 0,
        "airport": 0,
    }

    for el in elements:
        tags = el.get("tags", {})

        # Roads
        highway = tags.get("highway", "")
        if highway in road_counts:
            road_counts[highway] += 1

        # Services (amenity tag)
        amenity = tags.get("amenity", "")
        if amenity in service_counts:
            service_counts[amenity] += 1

        # Utilities
        power = tags.get("power", "")
        if power == "line":
            utility_counts["power_line"] += 1
        man_made = tags.get("man_made", "")
        if man_made == "communications_tower":
            utility_counts["comm_tower"] += 1

        # Transport
        if amenity == "bus_station" or tags.get("highway", "") == "bus_stop" or tags.get("public_transport", "") == "stop_position":
            transport_counts["bus_stop"] += 1
        if tags.get("railway", "") in ("station", "halt", "stop"):
            transport_counts["railway"] += 1
        if tags.get("aeroway", "") in ("aerodrome", "terminal"):
            transport_counts["airport"] += 1

    # Water features
    water_counts = {
        "spring": 0,
        "waterway": 0,
        "well": 0,
    }
    for el in water_elements:
        tags = el.get("tags", {})
        natural = tags.get("natural", "")
        if natural == "spring":
            water_counts["spring"] += 1
        if tags.get("waterway", ""):
            water_counts["waterway"] += 1
        man_made = tags.get("man_made", "")
        if man_made == "water_well":
            water_counts["well"] += 1

    # ---- Compute 6 dimension scores (0-100) ----
    road_score = min(100, (
        road_counts["primary"] * 15
        + road_counts["secondary"] * 12
        + road_counts["tertiary"] * 8
        + road_counts["residential"] * 5
        + road_counts["track"] * 3
    ))

    emergency_score = min(100, (
        service_counts["hospital"] * 20
        + service_counts["fire_station"] * 20
        + service_counts["police"] * 15
    ))

    education_score = min(100, (
        service_counts["school"] * 12
        + service_counts["hospital"] * 15
        + service_counts["pharmacy"] * 10
    ))

    transport_score = min(100, (
        transport_counts["bus_stop"] * 5
        + transport_counts["railway"] * 15
        + transport_counts["airport"] * 30
    ))

    utility_score = min(100, (
        utility_counts["power_line"] * 8
        + utility_counts["comm_tower"] * 12
    ))

    water_score = min(100, (
        water_counts["spring"] * 15
        + water_counts["waterway"] * 8
        + water_counts["well"] * 12
    ))

    scores = {
        "Road Network": road_score,
        "Emergency Services": emergency_score,
        "Education & Health": education_score,
        "Transport Links": transport_score,
        "Utilities": utility_score,
        "Water Access": water_score,
    }

    # ---- Weighted overall score ----
    overall_score = sum(
        scores[dim] * SCORE_WEIGHTS[dim] for dim in scores
    )
    overall_score = round(overall_score, 1)

    # ---- Classification ----
    if overall_score >= 80:
        classification = "Excellent"
        classification_color = "#10b981"
    elif overall_score >= 60:
        classification = "Good"
        classification_color = "#22c55e"
    elif overall_score >= 40:
        classification = "Fair"
        classification_color = "#f59e0b"
    elif overall_score >= 20:
        classification = "Poor"
        classification_color = "#ef4444"
    else:
        classification = "Remote"
        classification_color = "#dc2626"

    # ---- Detail dicts for display ----
    details = {
        "Road Network": road_counts,
        "Emergency Services": {
            "hospital": service_counts["hospital"],
            "fire_station": service_counts["fire_station"],
            "police": service_counts["police"],
        },
        "Education & Health": {
            "school": service_counts["school"],
            "hospital": service_counts["hospital"],
            "pharmacy": service_counts["pharmacy"],
        },
        "Transport Links": transport_counts,
        "Utilities": utility_counts,
        "Water Access": water_counts,
    }

    return {
        "overall_score": overall_score,
        "scores": scores,
        "details": details,
        "classification": classification,
        "classification_color": classification_color,
        "infra_elements": elements,
        "water_elements": water_elements,
    }


# =============================================================================
# HELPER: SCORE COLOR
# =============================================================================

def _score_color(score):
    """Return a CSS color string based on the score value."""
    if score > 70:
        return "#10b981"
    elif score > 40:
        return "#f59e0b"
    else:
        return "#ef4444"


# =============================================================================
# CHARTS
# =============================================================================

def _build_radar_chart(scores):
    """Build a Plotly radar chart of the 6 accessibility dimensions."""
    dimensions = list(scores.keys())
    values = list(scores.values())
    # Close the polygon
    dimensions_closed = dimensions + [dimensions[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=dimensions_closed,
        fill="toself",
        fillcolor="rgba(6, 182, 212, 0.25)",
        line=dict(color="#06b6d4", width=2),
        marker=dict(size=8, color="#06b6d4"),
        name="Accessibility",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#8b97b0", size=10),
                gridcolor="#2a2a4a",
            ),
            angularaxis=dict(
                tickfont=dict(color="#e2e8f0", size=11),
                gridcolor="#2a2a4a",
            ),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
        height=420,
    )
    return fig


def _build_bar_chart(scores):
    """Build a horizontal bar chart of all accessibility scores."""
    dimensions = list(scores.keys())
    values = list(scores.values())
    colors = [DIMENSION_COLORS.get(d, "#06b6d4") for d in dimensions]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=dimensions,
        x=values,
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(color="#1a1a2e", width=1),
        ),
        text=[f"{v:.0f}/100" for v in values],
        textposition="auto",
        textfont=dict(color="#ffffff", size=12),
    ))

    fig.update_layout(
        xaxis=dict(
            range=[0, 100],
            title="Score",
            title_font=dict(color="#8b97b0"),
            tickfont=dict(color="#8b97b0"),
            gridcolor="#2a2a4a",
        ),
        yaxis=dict(
            tickfont=dict(color="#e2e8f0", size=12),
            autorange="reversed",
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        margin=dict(l=140, r=30, t=20, b=40),
        height=320,
        showlegend=False,
    )
    return fig


# =============================================================================
# MAP BUILDER
# =============================================================================

def _build_infrastructure_map(lat, lon, result):
    """Build a Folium map with color-coded infrastructure markers."""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=13,
        tiles="CartoDB dark_matter",
    )

    # Center marker
    folium.Marker(
        location=[lat, lon],
        popup="Analysis Center",
        icon=folium.Icon(color="white", icon="screenshot", prefix="glyphicon"),
    ).add_to(m)

    elements = result.get("infra_elements", [])
    water_elements = result.get("water_elements", [])

    for el in elements:
        tags = el.get("tags", {})
        el_lat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        el_lon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if el_lat is None or el_lon is None:
            continue

        marker_color = "gray"
        icon_name = "info-sign"
        popup_text = ""

        highway = tags.get("highway", "")
        amenity = tags.get("amenity", "")
        power = tags.get("power", "")
        railway = tags.get("railway", "")
        aeroway = tags.get("aeroway", "")
        public_transport = tags.get("public_transport", "")
        man_made = tags.get("man_made", "")

        # Classify the element
        if highway in ("primary", "secondary", "tertiary", "residential", "track"):
            marker_color = MARKER_COLORS_BY_TYPE["road"]
            icon_name = "road"
            popup_text = f"Road: {highway}"
        elif amenity in ("hospital",):
            marker_color = MARKER_COLORS_BY_TYPE["emergency"]
            icon_name = "plus-sign"
            popup_text = f"Hospital: {html_module.escape(tags.get('name', 'Unknown'))}"
        elif amenity in ("fire_station",):
            marker_color = MARKER_COLORS_BY_TYPE["emergency"]
            icon_name = "fire"
            popup_text = f"Fire Station: {html_module.escape(tags.get('name', 'Unknown'))}"
        elif amenity in ("police",):
            marker_color = MARKER_COLORS_BY_TYPE["emergency"]
            icon_name = "tower"
            popup_text = f"Police: {html_module.escape(tags.get('name', 'Unknown'))}"
        elif amenity in ("school",):
            marker_color = MARKER_COLORS_BY_TYPE["education"]
            icon_name = "education"
            popup_text = f"School: {html_module.escape(tags.get('name', 'Unknown'))}"
        elif amenity in ("pharmacy",):
            marker_color = MARKER_COLORS_BY_TYPE["education"]
            icon_name = "heart"
            popup_text = f"Pharmacy: {html_module.escape(tags.get('name', 'Unknown'))}"
        elif amenity in ("bus_station",) or highway == "bus_stop" or public_transport == "stop_position":
            marker_color = MARKER_COLORS_BY_TYPE["transport"]
            icon_name = "transfer"
            popup_text = "Bus Stop"
        elif railway in ("station", "halt", "stop"):
            marker_color = MARKER_COLORS_BY_TYPE["transport"]
            icon_name = "transfer"
            popup_text = f"Railway: {html_module.escape(tags.get('name', 'Station'))}"
        elif aeroway in ("aerodrome", "terminal"):
            marker_color = MARKER_COLORS_BY_TYPE["transport"]
            icon_name = "plane"
            popup_text = f"Airport: {html_module.escape(tags.get('name', 'Airport'))}"
        elif power == "line":
            marker_color = MARKER_COLORS_BY_TYPE["utility"]
            icon_name = "flash"
            popup_text = "Power Line"
        elif man_made == "communications_tower":
            marker_color = MARKER_COLORS_BY_TYPE["utility"]
            icon_name = "signal"
            popup_text = "Communications Tower"
        else:
            # Skip elements that don't match our categories
            continue

        try:
            folium.Marker(
                location=[float(el_lat), float(el_lon)],
                popup=popup_text,
                icon=folium.Icon(color=marker_color, icon=icon_name, prefix="glyphicon"),
            ).add_to(m)
        except Exception:
            pass

    # Water features
    for el in water_elements:
        tags = el.get("tags", {})
        el_lat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        el_lon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if el_lat is None or el_lon is None:
            continue

        natural = tags.get("natural", "")
        man_made = tags.get("man_made", "")
        waterway = tags.get("waterway", "")

        popup_text = ""
        if natural == "spring":
            popup_text = "Spring"
        elif man_made == "water_well":
            popup_text = "Water Well"
        elif waterway:
            popup_text = f"Waterway: {html_module.escape(waterway)}"
        else:
            continue

        try:
            folium.Marker(
                location=[float(el_lat), float(el_lon)],
                popup=popup_text,
                icon=folium.Icon(color=MARKER_COLORS_BY_TYPE["water"], icon="tint", prefix="glyphicon"),
            ).add_to(m)
        except Exception:
            pass

    folium.LayerControl().add_to(m)
    return m


# =============================================================================
# RENDER FUNCTION
# =============================================================================

def render_accessibility_mapper_tab():
    """Main render function for the Accessibility & Reachability AI tab."""

    st.markdown(
        """<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px; border-radius: 12px; margin-bottom: 20px;
        border: 1px solid #2a2a4a;">
        <h2 style="color: #06b6d4; margin: 0;">Accessibility & Reachability AI</h2>
        <p style="color: #8b97b0; margin: 5px 0 0 0;">
        Analyze how accessible any location is across 6 key dimensions:
        roads, emergency services, education, transport, utilities, and water access.
        </p></div>""",
        unsafe_allow_html=True,
    )

    # ---- Location selector ----
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="acc_preset",
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
            key="acc_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude",
            value=default_lon,
            format="%.5f",
            min_value=-180.0,
            max_value=180.0,
            key="acc_lon",
        )

    run_analysis = st.button(
        "Analyze Accessibility",
        type="primary",
        key="acc_run",
        use_container_width=True,
    )

    if not run_analysis:
        st.info("Select a location and click **Analyze Accessibility** to begin.")
        return

    # ---- Run analysis ----
    with st.spinner("Computing accessibility scores..."):
        result = compute_accessibility(lat, lon)

    overall = result["overall_score"]
    scores = result["scores"]
    details = result["details"]
    classification = result["classification"]
    cls_color = result["classification_color"]

    # ---- Overall score header ----
    score_bg_color = _score_color(overall)
    st.markdown(
        f"""<div style="background: linear-gradient(135deg, {score_bg_color}22 0%, #1a1a2e 100%);
        padding: 25px; border-radius: 12px; margin: 15px 0;
        border: 1px solid {score_bg_color}55; text-align: center;">
        <h1 style="color: {score_bg_color}; margin: 0; font-size: 3.5em;">
        {overall:.1f}<span style="font-size: 0.4em; color: #8b97b0;">/100</span></h1>
        <p style="color: {cls_color}; font-size: 1.4em; margin: 5px 0; font-weight: bold;">
        {classification}</p>
        <p style="color: #8b97b0; margin: 0;">
        Overall Accessibility Score at ({lat:.4f}, {lon:.4f})</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ---- Radar chart ----
    st.markdown(
        """<div style="background: #1a1a2e; padding: 15px; border-radius: 12px;
        margin: 10px 0; border: 1px solid #2a2a4a;">
        <h3 style="color: #e2e8f0; margin: 0 0 10px 0;">Accessibility Radar</h3>
        </div>""",
        unsafe_allow_html=True,
    )
    radar_fig = _build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="accmap_pchart1")

    # ---- Component cards (6 dimensions, 3 columns) ----
    st.markdown(
        """<div style="background: #1a1a2e; padding: 15px; border-radius: 12px;
        margin: 10px 0; border: 1px solid #2a2a4a;">
        <h3 style="color: #e2e8f0; margin: 0;">Dimension Breakdown</h3>
        </div>""",
        unsafe_allow_html=True,
    )

    dims = list(scores.keys())
    for row_start in range(0, len(dims), 3):
        cols = st.columns(3)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(dims):
                break
            dim = dims[idx]
            s = scores[dim]
            d = details[dim]
            dim_color = DIMENSION_COLORS.get(dim, "#06b6d4")
            s_color = _score_color(s)

            # Build detail lines
            detail_lines = ""
            for k, v in d.items():
                label = k.replace("_", " ").title()
                detail_lines += (
                    f'<div style="display: flex; justify-content: space-between; '
                    f'padding: 3px 0; border-bottom: 1px solid #2a2a4a;">'
                    f'<span style="color: #8b97b0;">{label}</span>'
                    f'<span style="color: #e2e8f0; font-weight: bold;">{v}</span>'
                    f'</div>'
                )

            with col:
                st.markdown(
                    f"""<div style="background: linear-gradient(180deg, #1a1a2e 0%, #0f0f23 100%);
                    padding: 18px; border-radius: 10px; margin: 5px 0;
                    border: 1px solid {dim_color}44; min-height: 220px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;
                    margin-bottom: 12px;">
                    <h4 style="color: {dim_color}; margin: 0; font-size: 0.95em;">{dim}</h4>
                    <span style="color: {s_color}; font-size: 1.6em; font-weight: bold;">{s:.0f}</span>
                    </div>
                    <div style="background: #2a2a4a; border-radius: 6px; height: 8px;
                    margin-bottom: 12px; overflow: hidden;">
                    <div style="background: {s_color}; height: 100%; width: {s}%;
                    border-radius: 6px;"></div></div>
                    {detail_lines}
                    </div>""",
                    unsafe_allow_html=True,
                )

    # ---- Infrastructure map ----
    st.markdown(
        """<div style="background: #1a1a2e; padding: 15px; border-radius: 12px;
        margin: 15px 0 5px 0; border: 1px solid #2a2a4a;">
        <h3 style="color: #e2e8f0; margin: 0;">Infrastructure Map</h3>
        <p style="color: #8b97b0; margin: 5px 0 0 0; font-size: 0.9em;">
        Color-coded markers: <span style="color: #3b82f6;">Roads</span> |
        <span style="color: #ef4444;">Emergency</span> |
        <span style="color: #8b5cf6;">Education</span> |
        <span style="color: #f59e0b;">Transport</span> |
        <span style="color: #06b6d4;">Utilities</span> |
        <span style="color: #10b981;">Water</span></p>
        </div>""",
        unsafe_allow_html=True,
    )

    infra_map = _build_infrastructure_map(lat, lon, result)
    st_folium(infra_map, width=None, height=550, key="acc_infra_map", returned_objects=[])

    # ---- Horizontal bar chart ----
    st.markdown(
        """<div style="background: #1a1a2e; padding: 15px; border-radius: 12px;
        margin: 15px 0 5px 0; border: 1px solid #2a2a4a;">
        <h3 style="color: #e2e8f0; margin: 0;">Score Comparison</h3>
        </div>""",
        unsafe_allow_html=True,
    )
    bar_fig = _build_bar_chart(scores)
    st.plotly_chart(bar_fig, use_container_width=True, key="accmap_pchart2")

    # ---- Summary footer ----
    strong_dims = [d for d, s in scores.items() if s >= 70]
    weak_dims = [d for d, s in scores.items() if s < 40]

    strong_text = ", ".join(strong_dims) if strong_dims else "None"
    weak_text = ", ".join(weak_dims) if weak_dims else "None"

    st.markdown(
        f"""<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px; border-radius: 12px; margin: 15px 0;
        border: 1px solid #2a2a4a;">
        <h3 style="color: #e2e8f0; margin: 0 0 12px 0;">Analysis Summary</h3>
        <div style="display: flex; gap: 30px; flex-wrap: wrap;">
        <div>
        <p style="color: #8b97b0; margin: 0 0 4px 0; font-size: 0.85em;">CLASSIFICATION</p>
        <p style="color: {cls_color}; margin: 0; font-size: 1.2em; font-weight: bold;">
        {classification}</p>
        </div>
        <div>
        <p style="color: #8b97b0; margin: 0 0 4px 0; font-size: 0.85em;">STRONG DIMENSIONS</p>
        <p style="color: #10b981; margin: 0; font-size: 1em;">{strong_text}</p>
        </div>
        <div>
        <p style="color: #8b97b0; margin: 0 0 4px 0; font-size: 0.85em;">WEAK DIMENSIONS</p>
        <p style="color: #ef4444; margin: 0; font-size: 1em;">{weak_text}</p>
        </div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )
