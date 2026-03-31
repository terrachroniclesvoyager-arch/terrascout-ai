# -*- coding: utf-8 -*-
"""
Population Density & Demographics AI -- Estimates population density,
urbanization level, amenity richness & service coverage for any location.
Uses: Overpass API, Open Topo Data.
Part of TerraScout AI (252+ modules).
"""

import logging
import math

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests
import streamlit as st

from src.deep_zone_analysis import ANALYSIS_PRESETS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DENSITY_COMPONENTS = {
    "building_density": {"name": "Building Density", "color": "#ef4444", "weight": 0.20},
    "amenity_richness": {"name": "Amenity Richness", "color": "#f59e0b", "weight": 0.20},
    "infrastructure": {"name": "Infrastructure", "color": "#6366f1", "weight": 0.15},
    "residential": {"name": "Residential Character", "color": "#22c55e", "weight": 0.15},
    "service_coverage": {"name": "Service Coverage", "color": "#3b82f6", "weight": 0.15},
    "urbanization": {"name": "Urbanization Level", "color": "#ec4899", "weight": 0.15},
}

OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def fetch_overpass_density(lat, lon, radius=2000):
    """Fetch building, amenity and infrastructure data from Overpass API."""
    query = f"""
    [out:json][timeout:30];
    (
      way["building"](around:{radius},{lat},{lon});
      node["amenity"](around:{radius},{lat},{lon});
      way["highway"](around:{radius},{lat},{lon});
      way["railway"](around:{radius},{lat},{lon});
      node["shop"](around:{radius},{lat},{lon});
      way["landuse"](around:{radius},{lat},{lon});
      node["office"](around:{radius},{lat},{lon});
      way["power"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Overpass density error: %s", e)
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_for_density(lat, lon):
    """Fetch elevation from Open Topo Data for terrain context."""
    try:
        resp = requests.get(
            OPEN_TOPO_API,
            params={"locations": f"{lat},{lon}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return results[0].get("elevation")
    except Exception as e:
        logger.warning("Elevation fetch error: %s", e)
    return None


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def compute_population_density(lat, lon):
    """Compute population density analysis across 6 dimensions."""
    data = fetch_overpass_density(lat, lon)
    elements = data.get("elements", [])

    # Categorize elements
    buildings = [e for e in elements if e.get("tags", {}).get("building")]
    amenities = [e for e in elements if e.get("tags", {}).get("amenity")]
    roads = [e for e in elements if e.get("tags", {}).get("highway")]
    railways = [e for e in elements if e.get("tags", {}).get("railway")]
    shops = [e for e in elements if e.get("tags", {}).get("shop")]
    landuse = [e for e in elements if e.get("tags", {}).get("landuse")]
    offices = [e for e in elements if e.get("tags", {}).get("office")]
    power = [e for e in elements if e.get("tags", {}).get("power")]

    scores = {}
    details = {}

    # 1. Building Density ------------------------------------------------
    area_km2 = math.pi * (2.0 ** 2)  # pi * r^2, radius = 2 km
    bld_count = len(buildings)
    density_per_km2 = bld_count / max(area_km2, 0.01)
    bld_score = min(100, density_per_km2 / 5)  # ~500/km2 => 100
    scores["building_density"] = round(bld_score)
    details["building_density"] = {
        "buildings": bld_count,
        "density_per_km2": round(density_per_km2, 1),
        "area_km2": round(area_km2, 2),
    }

    # 2. Amenity Richness ------------------------------------------------
    amenity_types = {}
    for a in amenities:
        atype = a.get("tags", {}).get("amenity", "other")
        amenity_types[atype] = amenity_types.get(atype, 0) + 1

    healthcare = sum(
        1
        for a in amenities
        if a.get("tags", {}).get("amenity")
        in ("hospital", "clinic", "doctors", "pharmacy", "dentist")
    )
    education = sum(
        1
        for a in amenities
        if a.get("tags", {}).get("amenity")
        in ("school", "university", "college", "kindergarten", "library")
    )
    food = sum(
        1
        for a in amenities
        if a.get("tags", {}).get("amenity")
        in ("restaurant", "cafe", "fast_food", "bar", "pub")
    )
    finance = sum(
        1
        for a in amenities
        if a.get("tags", {}).get("amenity") in ("bank", "atm")
    )

    am_score = min(100, len(amenities) * 2 + len(amenity_types) * 5)
    scores["amenity_richness"] = round(am_score)
    details["amenity_richness"] = {
        "total_amenities": len(amenities),
        "unique_types": len(amenity_types),
        "healthcare": healthcare,
        "education": education,
        "food_drink": food,
        "financial": finance,
        "shops": len(shops),
    }

    # 3. Infrastructure Level --------------------------------------------
    major_roads = sum(
        1
        for r in roads
        if r.get("tags", {}).get("highway")
        in ("motorway", "trunk", "primary", "secondary")
    )
    minor_roads = sum(
        1
        for r in roads
        if r.get("tags", {}).get("highway")
        in ("tertiary", "residential", "service")
    )

    infra_score = min(
        100,
        len(roads) * 1.5
        + len(railways) * 10
        + len(power) * 5
        + major_roads * 5,
    )
    scores["infrastructure"] = round(infra_score)
    details["infrastructure"] = {
        "total_roads": len(roads),
        "major_roads": major_roads,
        "minor_roads": minor_roads,
        "railways": len(railways),
        "power_lines": len(power),
    }

    # 4. Residential Character -------------------------------------------
    residential = [
        e for e in landuse if e.get("tags", {}).get("landuse") == "residential"
    ]
    commercial = [
        e
        for e in landuse
        if e.get("tags", {}).get("landuse") in ("commercial", "retail")
    ]
    industrial = [
        e for e in landuse if e.get("tags", {}).get("landuse") == "industrial"
    ]

    res_buildings = sum(
        1
        for b in buildings
        if b.get("tags", {}).get("building")
        in ("residential", "apartments", "house", "detached", "yes")
    )

    total_classified = len(residential) + len(commercial) + len(industrial)
    res_ratio = len(residential) / max(1, total_classified)

    res_score = min(
        100, res_buildings * 2 + res_ratio * 40 + len(residential) * 10
    )
    scores["residential"] = round(res_score)

    if bld_count > 0:
        if res_ratio > 0.6:
            character = "Residential"
        elif res_ratio > 0.3:
            character = "Mixed"
        else:
            character = "Commercial/Industrial"
    else:
        character = "Undeveloped"

    details["residential"] = {
        "residential_areas": len(residential),
        "commercial_areas": len(commercial),
        "industrial_areas": len(industrial),
        "residential_buildings": res_buildings,
        "character": character,
    }

    # 5. Service Coverage ------------------------------------------------
    emergency = sum(
        1
        for a in amenities
        if a.get("tags", {}).get("amenity")
        in ("fire_station", "police", "hospital")
    )
    worship = sum(
        1
        for a in amenities
        if a.get("tags", {}).get("amenity") == "place_of_worship"
    )

    svc_score = min(
        100,
        (healthcare or 0) * 10
        + (education or 0) * 8
        + (emergency or 0) * 15
        + (finance or 0) * 5
        + (food or 0) * 2,
    )
    scores["service_coverage"] = round(svc_score)
    details["service_coverage"] = {
        "emergency_services": emergency,
        "healthcare_facilities": healthcare,
        "education_facilities": education,
        "financial_services": finance,
        "places_of_worship": worship,
    }

    # 6. Urbanization Score ----------------------------------------------
    urban_raw = (
        bld_score * 0.3
        + am_score * 0.25
        + infra_score * 0.25
        + len(shops) * 2
        + len(offices) * 3
    )
    urban_score = min(100, urban_raw)
    scores["urbanization"] = round(urban_score)

    if urban_score >= 80:
        urban_class = "Dense Urban"
        est_density = "5,000-50,000+/km2"
    elif urban_score >= 60:
        urban_class = "Urban"
        est_density = "1,000-5,000/km2"
    elif urban_score >= 40:
        urban_class = "Suburban"
        est_density = "200-1,000/km2"
    elif urban_score >= 20:
        urban_class = "Peri-urban"
        est_density = "50-200/km2"
    else:
        urban_class = "Rural"
        est_density = "<50/km2"

    details["urbanization"] = {
        "classification": urban_class,
        "estimated_density": est_density,
        "offices": len(offices),
        "total_shops": len(shops),
    }

    # Overall weighted score ---------------------------------------------
    overall = sum(
        scores.get(k, 0) * DENSITY_COMPONENTS[k]["weight"] for k in scores
    )
    overall = round(overall)

    if overall >= 75:
        ov_class = "Highly Developed"
        ov_color = "#ef4444"
    elif overall >= 55:
        ov_class = "Well Developed"
        ov_color = "#f59e0b"
    elif overall >= 35:
        ov_class = "Moderately Developed"
        ov_color = "#22c55e"
    elif overall >= 15:
        ov_class = "Lightly Developed"
        ov_color = "#3b82f6"
    else:
        ov_class = "Undeveloped"
        ov_color = "#6b7280"

    return {
        "overall": overall,
        "overall_class": ov_class,
        "overall_color": ov_color,
        "scores": scores,
        "details": details,
        "amenity_types": amenity_types,
    }


# ---------------------------------------------------------------------------
# Plotly chart builders (dark-theme compatible)
# ---------------------------------------------------------------------------

_CHART_BG = "#1a1a2e"
_CHART_PAPER = "#1a1a2e"
_CHART_FONT_COLOR = "#e2e8f0"


def _build_radar_chart(scores):
    """Build a radar chart of the 6 density dimensions."""
    categories = []
    values = []
    colors = []
    for key, meta in DENSITY_COMPONENTS.items():
        categories.append(meta["name"])
        values.append(scores.get(key, 0))
        colors.append(meta["color"])

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(99,102,241,0.25)",
            line=dict(color="#6366f1", width=2),
            marker=dict(size=6, color=colors + [colors[0]]),
            name="Score",
        )
    )
    fig.update_layout(
        polar=dict(
            bgcolor=_CHART_BG,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#94a3b8"),
                gridcolor="rgba(148,163,184,0.15)",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=_CHART_FONT_COLOR),
                gridcolor="rgba(148,163,184,0.15)",
            ),
        ),
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_CHART_FONT_COLOR),
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=False,
        height=420,
    )
    return fig


def _build_amenity_bar_chart(amenity_types):
    """Bar chart showing distribution of amenity types."""
    if not amenity_types:
        return None

    sorted_types = sorted(amenity_types.items(), key=lambda x: x[1], reverse=True)
    top_n = sorted_types[:20]  # top 20
    labels = [t[0].replace("_", " ").title() for t in top_n]
    counts = [t[1] for t in top_n]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=counts,
            y=labels,
            orientation="h",
            marker=dict(
                color=counts,
                colorscale="Viridis",
                line=dict(width=0),
            ),
            text=counts,
            textposition="outside",
            textfont=dict(color=_CHART_FONT_COLOR, size=11),
        )
    )
    fig.update_layout(
        title=dict(
            text="Amenity Types Distribution",
            font=dict(size=14, color=_CHART_FONT_COLOR),
        ),
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_CHART_FONT_COLOR),
        xaxis=dict(
            title="Count",
            gridcolor="rgba(148,163,184,0.15)",
            tickfont=dict(color="#94a3b8"),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(color=_CHART_FONT_COLOR, size=11),
        ),
        margin=dict(l=150, r=40, t=50, b=40),
        height=max(300, len(top_n) * 28 + 80),
    )
    return fig


def _build_landuse_pie(details):
    """Pie chart for land use breakdown."""
    res_details = details.get("residential", {})
    res_count = res_details.get("residential_areas", 0) or 0
    com_count = res_details.get("commercial_areas", 0) or 0
    ind_count = res_details.get("industrial_areas", 0) or 0

    labels = []
    values = []
    colors = []

    if res_count > 0:
        labels.append("Residential")
        values.append(res_count)
        colors.append("#22c55e")
    if com_count > 0:
        labels.append("Commercial")
        values.append(com_count)
        colors.append("#6366f1")
    if ind_count > 0:
        labels.append("Industrial")
        values.append(ind_count)
        colors.append("#ef4444")

    if not values:
        return None

    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors, line=dict(color=_CHART_BG, width=2)),
            hole=0.45,
            textinfo="label+percent",
            textfont=dict(color=_CHART_FONT_COLOR, size=12),
        )
    )
    fig.update_layout(
        title=dict(
            text="Land Use Breakdown",
            font=dict(size=14, color=_CHART_FONT_COLOR),
        ),
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_CHART_FONT_COLOR),
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(font=dict(color=_CHART_FONT_COLOR, size=11)),
        height=380,
    )
    return fig


# ---------------------------------------------------------------------------
# HTML card helpers
# ---------------------------------------------------------------------------


def _render_overall_card(result):
    """Render the big overall score header card."""
    overall = result.get("overall", 0) or 0
    ov_class = result.get("overall_class", "Unknown")
    ov_color = result.get("overall_color", "#6b7280")
    urb_details = result.get("details", {}).get("urbanization", {})
    classification = urb_details.get("classification", "N/A")
    est_density = urb_details.get("estimated_density", "N/A")
    bld_details = result.get("details", {}).get("building_density", {})
    bld_count = bld_details.get("buildings", 0) or 0
    density_km2 = bld_details.get("density_per_km2", 0) or 0

    html_str = f"""
    <div style="
        background: linear-gradient(135deg, {ov_color}22, {ov_color}44);
        border: 1px solid {ov_color}88;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 20px;
        text-align: center;
    ">
        <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase;
                    letter-spacing: 2px; margin-bottom: 8px;">
            Population Density &amp; Demographics
        </div>
        <div style="font-size: 56px; font-weight: 800; color: {ov_color};
                    line-height: 1.1;">
            {overall}<span style="font-size: 22px; color: #94a3b8;">/100</span>
        </div>
        <div style="font-size: 20px; font-weight: 600; color: {ov_color};
                    margin-top: 4px;">
            {ov_class}
        </div>
        <div style="
            display: flex; justify-content: center; gap: 32px;
            margin-top: 16px; flex-wrap: wrap;
        ">
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Urbanization</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {classification}
                </span>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Est. Density</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {est_density}
                </span>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Buildings Found</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {bld_count:,}
                </span>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Bldg/km2</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {density_km2:,.1f}
                </span>
            </div>
        </div>
    </div>
    """
    st.markdown(html_str, unsafe_allow_html=True)


def _metric_card_html(title, score, color, detail_lines):
    """Return HTML for a single metric card."""
    bar_width = max(0, min(100, score or 0))
    lines_html = ""
    for label, value in detail_lines:
        lines_html += f"""
        <div style="display:flex; justify-content:space-between;
                    font-size:12px; padding:2px 0;">
            <span style="color:#94a3b8;">{label}</span>
            <span style="color:#e2e8f0; font-weight:600;">{value}</span>
        </div>
        """
    return f"""
    <div style="
        background: #1a1a2e;
        border: 1px solid {color}55;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        min-height: 200px;
    ">
        <div style="display:flex; justify-content:space-between;
                    align-items:center; margin-bottom: 10px;">
            <span style="font-size:14px; font-weight:700; color:{color};">
                {title}
            </span>
            <span style="font-size:22px; font-weight:800; color:{color};">
                {score}
            </span>
        </div>
        <div style="
            background: #0f0f23;
            border-radius: 6px;
            height: 6px;
            margin-bottom: 14px;
            overflow: hidden;
        ">
            <div style="
                width: {bar_width}%;
                height: 100%;
                background: {color};
                border-radius: 6px;
            "></div>
        </div>
        {lines_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def render_population_density_tab():
    """Entry point: Population Density & Demographics AI tab."""

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #ef444422, #f59e0b22);
            border: 1px solid #ef444455;
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 20px;
        ">
            <span style="font-size:22px; font-weight:700; color:#ef4444;">
                Population Density &amp; Demographics AI
            </span><br>
            <span style="font-size:13px; color:#94a3b8;">
                Estimates population density, urbanization level, amenity richness
                and service coverage using OSM building / amenity / infrastructure data.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="pd_preset",
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
            key="pd_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude",
            value=default_lon,
            format="%.5f",
            min_value=-180.0,
            max_value=180.0,
            key="pd_lon",
        )

    run_btn = st.button(
        "Analyze Population Density",
        type="primary",
        key="pd_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Select a location and press **Analyze Population Density** to begin."
        )
        return

    # -- Fetch & compute --------------------------------------------------
    with st.spinner(
        "Querying Overpass API for buildings, amenities & infrastructure..."
    ):
        result = compute_population_density(lat, lon)

    if result is None:
        st.error("Analysis failed. Please try again.")
        return

    scores = result.get("scores", {})
    details = result.get("details", {})
    amenity_types = result.get("amenity_types", {})

    # -- Overall header card ----------------------------------------------
    _render_overall_card(result)

    # -- Elevation context ------------------------------------------------
    elev = fetch_elevation_for_density(lat, lon)
    if elev is not None:
        st.caption(f"Elevation at location: **{elev:,.0f} m** above sea level")

    # -- Radar chart ------------------------------------------------------
    st.subheader("Density Profile Radar")
    radar_fig = _build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="popden_pchart1")

    # -- 6 metric cards (3 cols x 2 rows) ---------------------------------
    st.subheader("Dimension Breakdown")

    # Row 1
    r1c1, r1c2, r1c3 = st.columns(3)

    # Building Density card
    bd = details.get("building_density", {})
    with r1c1:
        st.markdown(
            _metric_card_html(
                "Building Density",
                scores.get("building_density", 0),
                "#ef4444",
                [
                    ("Buildings", f"{bd.get('buildings', 0):,}"),
                    ("Density/km2", f"{bd.get('density_per_km2', 0):,.1f}"),
                    ("Area (km2)", f"{bd.get('area_km2', 0):.2f}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Amenity Richness card
    ar = details.get("amenity_richness", {})
    with r1c2:
        st.markdown(
            _metric_card_html(
                "Amenity Richness",
                scores.get("amenity_richness", 0),
                "#f59e0b",
                [
                    ("Total Amenities", f"{ar.get('total_amenities', 0):,}"),
                    ("Unique Types", f"{ar.get('unique_types', 0)}"),
                    ("Healthcare", f"{ar.get('healthcare', 0)}"),
                    ("Education", f"{ar.get('education', 0)}"),
                    ("Food & Drink", f"{ar.get('food_drink', 0)}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Infrastructure card
    inf = details.get("infrastructure", {})
    with r1c3:
        st.markdown(
            _metric_card_html(
                "Infrastructure",
                scores.get("infrastructure", 0),
                "#6366f1",
                [
                    ("Total Roads", f"{inf.get('total_roads', 0):,}"),
                    ("Major Roads", f"{inf.get('major_roads', 0)}"),
                    ("Minor Roads", f"{inf.get('minor_roads', 0)}"),
                    ("Railways", f"{inf.get('railways', 0)}"),
                    ("Power Lines", f"{inf.get('power_lines', 0)}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Row 2
    r2c1, r2c2, r2c3 = st.columns(3)

    # Residential Character card
    rc = details.get("residential", {})
    with r2c1:
        st.markdown(
            _metric_card_html(
                "Residential Character",
                scores.get("residential", 0),
                "#22c55e",
                [
                    ("Character", rc.get("character", "N/A")),
                    ("Residential Areas", f"{rc.get('residential_areas', 0)}"),
                    ("Commercial Areas", f"{rc.get('commercial_areas', 0)}"),
                    ("Industrial Areas", f"{rc.get('industrial_areas', 0)}"),
                    (
                        "Res. Buildings",
                        f"{rc.get('residential_buildings', 0):,}",
                    ),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Service Coverage card
    sc = details.get("service_coverage", {})
    with r2c2:
        st.markdown(
            _metric_card_html(
                "Service Coverage",
                scores.get("service_coverage", 0),
                "#3b82f6",
                [
                    ("Emergency", f"{sc.get('emergency_services', 0)}"),
                    ("Healthcare", f"{sc.get('healthcare_facilities', 0)}"),
                    ("Education", f"{sc.get('education_facilities', 0)}"),
                    ("Financial", f"{sc.get('financial_services', 0)}"),
                    ("Worship", f"{sc.get('places_of_worship', 0)}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Urbanization Level card
    urb = details.get("urbanization", {})
    with r2c3:
        st.markdown(
            _metric_card_html(
                "Urbanization Level",
                scores.get("urbanization", 0),
                "#ec4899",
                [
                    ("Classification", urb.get("classification", "N/A")),
                    ("Est. Density", urb.get("estimated_density", "N/A")),
                    ("Offices", f"{urb.get('offices', 0)}"),
                    ("Shops", f"{urb.get('total_shops', 0)}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # -- Charts -----------------------------------------------------------
    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        amenity_fig = _build_amenity_bar_chart(amenity_types)
        if amenity_fig is not None:
            st.plotly_chart(amenity_fig, use_container_width=True, key="popden_pchart2")
        else:
            st.info("No amenity data available for this location.")

    with chart_c2:
        pie_fig = _build_landuse_pie(details)
        if pie_fig is not None:
            st.plotly_chart(pie_fig, use_container_width=True, key="popden_pchart3")
        else:
            st.info(
                "No land use classification data available for this location."
            )

    # -- Raw data expander ------------------------------------------------
    with st.expander("Raw Analysis Data"):
        st.json(result)
