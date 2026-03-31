"""
Cultural Heritage AI module for TerraScout AI.
Assesses historical and cultural significance for any geographic location
using multi-source data: Overpass API (historic sites, museums, monuments,
churches, castles, ruins, UNESCO sites, theatres, libraries), Macrostrat
(geological age context), and Open-Meteo (climate for preservation).
All data from free APIs -- no keys required.
"""

import logging
import math

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.overpass_client import query_overpass
from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_weather_data,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

MACROSTRAT_API = "https://macrostrat.org/api/v2"

HERITAGE_CATEGORIES = {
    "religious": {
        "name": "Religious Sites",
        "color": "#a855f7",
        "tags": {"amenity": ["place_of_worship"]},
    },
    "military": {
        "name": "Military / Fortifications",
        "color": "#ef4444",
        "tags": {"historic": ["castle", "fort", "citadel", "battlefield", "city_gate"]},
    },
    "civic": {
        "name": "Civic / Administrative",
        "color": "#3b82f6",
        "tags": {"historic": ["monument", "memorial", "milestone", "boundary_stone"]},
    },
    "artistic": {
        "name": "Artistic / Cultural",
        "color": "#f97316",
        "tags": {"tourism": ["museum", "gallery", "artwork"]},
    },
    "ancient": {
        "name": "Ancient / Archaeological",
        "color": "#eab308",
        "tags": {"historic": ["ruins", "archaeological_site", "tomb", "wayside_shrine"]},
    },
    "infrastructure": {
        "name": "Cultural Infrastructure",
        "color": "#06b6d4",
        "tags": {"amenity": ["theatre", "library", "arts_centre", "community_centre"]},
    },
}

DIM_COLORS = {
    "Historical Density": "#f97316",
    "Monument Diversity": "#a855f7",
    "Preservation Status": "#22c55e",
    "Cultural Infrastructure": "#06b6d4",
    "Heritage Significance": "#eab308",
    "Accessibility": "#3b82f6",
}


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, val))


# ==============================================================================
# DATA FETCHING
# ==============================================================================

@st.cache_data(ttl=1800)
def fetch_cultural_data(lat, lon, radius=5000):
    """Fetch cultural heritage features from Overpass API."""
    query = f"""
    [out:json][timeout:30];
    (
      node["historic"](around:{radius},{lat},{lon});
      way["historic"](around:{radius},{lat},{lon});
      node["tourism"="museum"](around:{radius},{lat},{lon});
      node["amenity"="theatre"](around:{radius},{lat},{lon});
      node["amenity"="library"](around:{radius},{lat},{lon});
      node["amenity"="arts_centre"](around:{radius},{lat},{lon});
      node["amenity"="place_of_worship"](around:{radius},{lat},{lon});
      way["amenity"="place_of_worship"](around:{radius},{lat},{lon});
      node["tourism"="gallery"](around:{radius},{lat},{lon});
      node["tourism"="artwork"](around:{radius},{lat},{lon});
      node["heritage"](around:{radius},{lat},{lon});
      way["heritage"](around:{radius},{lat},{lon});
    );
    out body;
    """
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=1800)
def fetch_macrostrat_geology(lat, lon):
    """Fetch geological age context from Macrostrat."""
    try:
        resp = requests.get(
            f"{MACROSTRAT_API}/geologic_units/map",
            params={"lat": lat, "lng": lon, "response": "long"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Macrostrat error: %s", exc)
        return {}


# ==============================================================================
# CLASSIFICATION HELPERS
# ==============================================================================

def _classify_site(element):
    """Classify a cultural element into a heritage category and return (category_key, site_name, site_type)."""
    tags = element.get("tags", {})
    site_name = (
        tags.get("name")
        or tags.get("name:en")
        or tags.get("description")
        or tags.get("historic")
        or tags.get("tourism")
        or tags.get("amenity")
        or "Unknown"
    )

    # Check historic tag
    historic_val = tags.get("historic", "")
    if historic_val in ("castle", "fort", "citadel", "battlefield", "city_gate"):
        return "military", site_name, historic_val or "fortification"
    if historic_val in ("ruins", "archaeological_site", "tomb", "wayside_shrine"):
        return "ancient", site_name, historic_val or "ancient site"
    if historic_val in ("monument", "memorial", "milestone", "boundary_stone"):
        return "civic", site_name, historic_val or "monument"
    if historic_val:
        return "civic", site_name, historic_val

    # Check tourism tag
    tourism_val = tags.get("tourism", "")
    if tourism_val in ("museum", "gallery", "artwork"):
        return "artistic", site_name, tourism_val

    # Check amenity tag
    amenity_val = tags.get("amenity", "")
    if amenity_val == "place_of_worship":
        religion = tags.get("religion", "")
        worship_type = tags.get("building", amenity_val)
        label = f"{religion} {worship_type}".strip() if religion else "place of worship"
        return "religious", site_name, label
    if amenity_val in ("theatre", "library", "arts_centre", "community_centre"):
        return "infrastructure", site_name, amenity_val

    # Check heritage tag
    if tags.get("heritage"):
        return "ancient", site_name, "heritage site"

    return "civic", site_name, "cultural site"


def _has_heritage_tag(element):
    """Check if element has a heritage/UNESCO designation."""
    tags = element.get("tags", {})
    heritage = tags.get("heritage", "")
    heritage_operator = tags.get("heritage:operator", "")
    return bool(heritage) or "unesco" in heritage_operator.lower() or "whc" in heritage_operator.lower()


# ==============================================================================
# CORE COMPUTATION
# ==============================================================================

@st.cache_data(ttl=1800)
def compute_cultural_heritage(lat, lon):
    """
    Compute a comprehensive cultural heritage assessment for a location.
    Returns scores for 6 dimensions, site classifications, and detail data.
    """
    # ------------------------------------------------------------------
    # 1. Fetch data sources
    # ------------------------------------------------------------------
    try:
        cultural = fetch_cultural_data(lat, lon, radius=5000)
    except Exception as exc:
        logger.warning("Cultural data fetch error: %s", exc)
        cultural = {"elements": []}

    try:
        weather = fetch_weather_data(lat, lon)
    except Exception as exc:
        logger.warning("Weather fetch error: %s", exc)
        weather = {}

    try:
        infra = fetch_landuse_infrastructure(lat, lon, radius=3000)
    except Exception as exc:
        logger.warning("Infrastructure fetch error: %s", exc)
        infra = {"elements": []}

    try:
        geology = fetch_macrostrat_geology(lat, lon)
    except Exception as exc:
        logger.warning("Macrostrat fetch error: %s", exc)
        geology = {}

    # ------------------------------------------------------------------
    # 2. Parse cultural elements
    # ------------------------------------------------------------------
    cultural_elements = cultural.get("elements", []) if isinstance(cultural, dict) else []
    infra_elements = infra.get("elements", []) if isinstance(infra, dict) else []

    # Classify each cultural site
    classified_sites = []
    category_counts = {k: 0 for k in HERITAGE_CATEGORIES}
    site_types_set = set()
    heritage_designated = 0

    for el in cultural_elements:
        cat_key, site_name, site_type = _classify_site(el)
        category_counts[cat_key] = category_counts.get(cat_key, 0) + 1
        site_types_set.add(site_type)
        classified_sites.append({
            "name": site_name,
            "type": site_type,
            "category": cat_key,
        })
        if _has_heritage_tag(el):
            heritage_designated += 1

    total_sites = len(cultural_elements)

    # Specific counts
    castles = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("historic") in ("castle", "fort", "citadel")
    )
    ruins = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("historic") in ("ruins", "archaeological_site")
    )
    museums = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("tourism") == "museum"
    )
    theatres = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("amenity") == "theatre"
    )
    libraries = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("amenity") == "library"
    )
    galleries = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("tourism") in ("gallery", "artwork")
    )
    churches = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("amenity") == "place_of_worship"
    )
    arts_centres = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("amenity") in ("arts_centre", "community_centre")
    )
    monuments = sum(
        1 for el in cultural_elements
        if el.get("tags", {}).get("historic") in ("monument", "memorial")
    )

    # Infrastructure: roads, transport, tourism support
    roads = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("highway") in (
            "primary", "secondary", "tertiary", "motorway",
            "trunk", "residential", "unclassified",
        )
    )
    parking = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("amenity") == "parking"
    )
    hotels = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("tourism") in ("hotel", "motel", "guest_house", "hostel")
    )
    restaurants = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("amenity") in ("restaurant", "cafe")
    )
    tourist_info = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("tourism") == "information"
    )
    bus_stops = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("highway") == "bus_stop"
           or e.get("tags", {}).get("public_transport") == "stop_position"
    )

    # ------------------------------------------------------------------
    # 3. Weather / Preservation conditions
    # ------------------------------------------------------------------
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}

    temp_now = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    precip_now = current.get("precipitation")
    wind_speed = current.get("wind_speed_10m")

    precip_daily_list = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip_daily_list if p is not None]
    avg_daily_precip = sum(valid_precip) / len(valid_precip) if valid_precip else 0

    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    valid_max = [t for t in temps_max if t is not None]
    valid_min = [t for t in temps_min if t is not None]
    temp_range = (max(valid_max) - min(valid_min)) if valid_max and valid_min else 0

    # ------------------------------------------------------------------
    # 4. Geological age context
    # ------------------------------------------------------------------
    geo_success = geology.get("success", {}) if isinstance(geology, dict) else {}
    geo_data = geo_success.get("data", []) if isinstance(geo_success, dict) else []
    if not geo_data and isinstance(geology, dict):
        geo_data = geology.get("success", {}).get("data", []) if isinstance(geology.get("success"), dict) else []

    oldest_age_ma = 0
    geo_period = "Unknown"
    if geo_data and isinstance(geo_data, list):
        for unit in geo_data:
            if isinstance(unit, dict):
                t_age = unit.get("t_age") or unit.get("b_age") or 0
                if isinstance(t_age, (int, float)) and t_age > oldest_age_ma:
                    oldest_age_ma = t_age
                period = unit.get("t_int_name") or unit.get("strat_name") or ""
                if period:
                    geo_period = period

    # ------------------------------------------------------------------
    # 5. Compute 6 Dimension Scores (0-100)
    # ------------------------------------------------------------------

    # Area of search radius in km^2 (pi * r^2 with r = 5km)
    area_km2 = math.pi * (5.0 ** 2)

    # --- Dim 1: Historical Density ---
    density_per_km2 = total_sites / area_km2 if area_km2 > 0 else 0
    historical_density = _clamp(
        min(density_per_km2 * 12.0, 50)
        + min(total_sites * 0.8, 30)
        + min(monuments * 4, 20)
    )

    # --- Dim 2: Monument Diversity ---
    num_unique_types = len(site_types_set)
    num_active_categories = sum(1 for v in category_counts.values() if v > 0)

    monument_diversity = _clamp(
        min(num_unique_types * 6, 40)
        + min(num_active_categories * 12, 36)
        + min(castles * 5 + churches * 2 + museums * 4, 24)
    )

    # --- Dim 3: Preservation Status ---
    # Ideal preservation: moderate temp (10-20C), low humidity (40-60%), low precip, low wind
    temp_preservation = 50.0
    if temp_now is not None:
        if 10 <= temp_now <= 20:
            temp_preservation = 95.0
        elif 5 <= temp_now < 10 or 20 < temp_now <= 25:
            temp_preservation = 75.0
        elif 0 <= temp_now < 5 or 25 < temp_now <= 30:
            temp_preservation = 55.0
        elif temp_now < -5 or temp_now > 35:
            temp_preservation = 20.0
        else:
            temp_preservation = 40.0

    humidity_preservation = 50.0
    if humidity is not None:
        if 40 <= humidity <= 60:
            humidity_preservation = 90.0
        elif 30 <= humidity < 40 or 60 < humidity <= 70:
            humidity_preservation = 70.0
        elif 20 <= humidity < 30 or 70 < humidity <= 80:
            humidity_preservation = 50.0
        else:
            humidity_preservation = 25.0

    precip_preservation = 70.0
    if avg_daily_precip < 1.0:
        precip_preservation = 95.0
    elif avg_daily_precip < 3.0:
        precip_preservation = 75.0
    elif avg_daily_precip < 6.0:
        precip_preservation = 50.0
    elif avg_daily_precip < 10.0:
        precip_preservation = 30.0
    else:
        precip_preservation = 15.0

    wind_preservation = 60.0
    if wind_speed is not None:
        if wind_speed < 10:
            wind_preservation = 90.0
        elif wind_speed < 20:
            wind_preservation = 65.0
        elif wind_speed < 35:
            wind_preservation = 40.0
        else:
            wind_preservation = 20.0

    temp_cycle_penalty = _clamp(100 - temp_range * 2, 20, 100)

    preservation_status = _clamp(
        temp_preservation * 0.25
        + humidity_preservation * 0.25
        + precip_preservation * 0.20
        + wind_preservation * 0.15
        + temp_cycle_penalty * 0.15
    )

    # --- Dim 4: Cultural Infrastructure ---
    cultural_infra = _clamp(
        min(museums * 12, 30)
        + min(theatres * 15, 20)
        + min(libraries * 10, 15)
        + min(galleries * 8, 15)
        + min(arts_centres * 10, 10)
        + min(restaurants * 2, 10)
    )

    # --- Dim 5: Heritage Significance ---
    heritage_significance = _clamp(
        min(heritage_designated * 20, 35)
        + min(castles * 10, 25)
        + min(ruins * 8, 20)
        + min(oldest_age_ma / 50, 10)
        + min(churches * 3, 10)
    )

    # --- Dim 6: Accessibility ---
    accessibility = _clamp(
        min(roads * 3, 35)
        + min(parking * 8, 15)
        + min(hotels * 6, 15)
        + min(tourist_info * 10, 15)
        + min(bus_stops * 5, 10)
        + min(restaurants * 2, 10)
    )

    # ------------------------------------------------------------------
    # 6. Overall Score
    # ------------------------------------------------------------------
    overall = round(
        historical_density * 0.20
        + monument_diversity * 0.18
        + preservation_status * 0.12
        + cultural_infra * 0.20
        + heritage_significance * 0.18
        + accessibility * 0.12
    )
    overall = int(_clamp(overall))

    # ------------------------------------------------------------------
    # 7. Assemble dimensions dict
    # ------------------------------------------------------------------
    dimensions = {
        "Historical Density": round(historical_density),
        "Monument Diversity": round(monument_diversity),
        "Preservation Status": round(preservation_status),
        "Cultural Infrastructure": round(cultural_infra),
        "Heritage Significance": round(heritage_significance),
        "Accessibility": round(accessibility),
    }

    # ------------------------------------------------------------------
    # 8. Site type distribution for pie chart
    # ------------------------------------------------------------------
    type_distribution = {}
    for site in classified_sites:
        cat = site.get("category", "civic")
        cat_name = HERITAGE_CATEGORIES.get(cat, {}).get("name", cat)
        type_distribution[cat_name] = type_distribution.get(cat_name, 0) + 1

    # ------------------------------------------------------------------
    # 9. Counts summary
    # ------------------------------------------------------------------
    counts = {
        "Total Cultural Sites": total_sites,
        "Monuments & Memorials": monuments,
        "Castles & Forts": castles,
        "Ancient Ruins": ruins,
        "Museums": museums,
        "Theatres": theatres,
        "Libraries": libraries,
        "Galleries & Artworks": galleries,
        "Places of Worship": churches,
        "Arts Centres": arts_centres,
        "Heritage Designated": heritage_designated,
    }

    # ------------------------------------------------------------------
    # 10. Weather summary for display
    # ------------------------------------------------------------------
    climate_summary = {
        "temp_now": temp_now,
        "humidity": humidity,
        "precipitation": precip_now,
        "wind_speed": wind_speed,
        "avg_daily_precip": round(avg_daily_precip, 1),
        "temp_range_7d": round(temp_range, 1),
        "temp_preservation": round(temp_preservation),
        "humidity_preservation": round(humidity_preservation),
        "precip_preservation": round(precip_preservation),
        "wind_preservation": round(wind_preservation),
    }

    return {
        "overall": overall,
        "dimensions": dimensions,
        "type_distribution": type_distribution,
        "classified_sites": classified_sites,
        "counts": counts,
        "climate_summary": climate_summary,
        "geo_period": geo_period,
        "oldest_age_ma": oldest_age_ma,
        "category_counts": category_counts,
    }


# ==============================================================================
# UI HELPERS
# ==============================================================================

def _score_color(score):
    """Return a colour hex for a given 0-100 score."""
    if score >= 75:
        return "#22c55e"
    if score >= 55:
        return "#eab308"
    if score >= 35:
        return "#f97316"
    return "#ef4444"


def _score_label(score):
    """Return a human-readable label for a 0-100 score."""
    if score >= 80:
        return "Outstanding"
    if score >= 60:
        return "Rich"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Limited"
    return "Minimal"


# ==============================================================================
# STREAMLIT RENDER
# ==============================================================================

def render_cultural_heritage_tab():
    """Main render function for the Cultural Heritage AI tab."""

    st.markdown("""
    <div class="tab-header" style="border-image:linear-gradient(90deg,#eab308,#a855f7) 1;">
        <h4>Cultural Heritage Index</h4>
        <p>Historical and cultural significance assessment using multi-source geospatial intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # -- Location selector --------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="ch_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    d_lat = p.get("lat", 41.90) if p else 41.90
    d_lon = p.get("lon", 12.50) if p else 12.50

    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input(
                "Latitude", -90.0, 90.0, d_lat,
                step=0.01, key="ch_lat", format="%.4f",
            )
        with c2:
            lon = st.number_input(
                "Longitude", -180.0, 180.0, d_lon,
                step=0.01, key="ch_lon", format="%.4f",
            )

    # -- Run button ---------------------------------------------------------
    if st.button("Assess Cultural Heritage", type="primary", use_container_width=True):
        progress = st.progress(0, text="Initializing cultural heritage analysis...")
        progress.progress(10, text="Fetching cultural sites from OpenStreetMap...")
        progress.progress(30, text="Querying geological context...")
        progress.progress(50, text="Analysing weather for preservation...")
        result = compute_cultural_heritage(lat, lon)
        progress.progress(80, text="Scoring 6 heritage dimensions...")
        progress.progress(100, text="Cultural heritage assessment complete!")
        st.session_state["ch_result"] = {**result, "lat": lat, "lon": lon}

    # -- Guard: nothing to show yet -----------------------------------------
    if "ch_result" not in st.session_state:
        return

    res = st.session_state["ch_result"]
    overall = res["overall"]
    dimensions = res["dimensions"]
    type_dist = res["type_distribution"]
    sites_list = res["classified_sites"]
    counts = res["counts"]
    climate = res["climate_summary"]
    geo_period = res["geo_period"]
    oldest_age = res["oldest_age_ma"]
    r_lat = res["lat"]
    r_lon = res["lon"]

    st.markdown("---")

    # -- Overall Score Banner -----------------------------------------------
    oc = _score_color(overall)
    st.markdown(f"""
    <div style="text-align:center; padding:1.8rem; background:linear-gradient(135deg,#1a1a2e,#16213e);
                border-radius:16px; border:2px solid {oc}; margin-bottom:1.5rem;">
        <div style="font-size:3.8rem; font-weight:900; color:{oc};">{overall}</div>
        <div style="font-size:1.3rem; color:{oc}; font-weight:700;">{_score_label(overall)}</div>
        <div style="color:#94a3b8; margin-top:0.5rem;">Cultural Heritage Index</div>
        <div style="color:#64748b; font-size:0.85rem;">({r_lat:.4f}, {r_lon:.4f})</div>
    </div>
    """, unsafe_allow_html=True)

    # -- Geological context banner ------------------------------------------
    geo_display = geo_period if geo_period != "Unknown" else "N/A"
    age_display = f"{oldest_age:.0f} Ma" if oldest_age > 0 else "N/A"
    st.markdown(f"""
    <div style="text-align:center; padding:0.8rem; background:#1a1a2e;
                border-radius:10px; border:1px solid #2a2a4e; margin-bottom:1.5rem;">
        <span style="color:#94a3b8;">Geological Period:</span>
        <b style="color:#eab308;"> {geo_display}</b>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span style="color:#94a3b8;">Oldest Formation:</span>
        <b style="color:#eab308;"> {age_display}</b>
    </div>
    """, unsafe_allow_html=True)

    # -- 6 Dimension Metric Cards -------------------------------------------
    st.markdown("### Heritage Dimension Scores")
    dim_keys = list(dimensions.keys())
    row1_cols = st.columns(3)
    row2_cols = st.columns(3)
    all_cols = row1_cols + row2_cols

    for i, dim_name in enumerate(dim_keys):
        dim_val = dimensions[dim_name]
        dim_color = DIM_COLORS.get(dim_name, "#94a3b8")
        sc_col = _score_color(dim_val)
        with all_cols[i]:
            st.markdown(f"""
            <div style="background:#1a1a2e; border-radius:12px; padding:1rem;
                        text-align:center; border-top:3px solid {dim_color};
                        min-height:140px; margin-bottom:0.8rem;">
                <div style="font-size:2rem; font-weight:800; color:{sc_col};">{dim_val}</div>
                <div style="font-weight:600; color:#e2e8f0; font-size:0.85rem;">
                    {dim_name}
                </div>
                <div style="color:#64748b; font-size:0.72rem;">{_score_label(dim_val)}</div>
            </div>
            """, unsafe_allow_html=True)

    # -- Radar Chart: 6 Dimensions ------------------------------------------
    st.markdown("### Heritage Profile Radar")
    radar_labels = list(dimensions.keys())
    radar_values = list(dimensions.values())
    radar_values_closed = radar_values + [radar_values[0]]
    radar_labels_closed = radar_labels + [radar_labels[0]]

    fig_radar = go.Figure(data=go.Scatterpolar(
        r=radar_values_closed,
        theta=radar_labels_closed,
        fill="toself",
        line_color="#eab308",
        fillcolor="rgba(234, 179, 8, 0.15)",
        name="Heritage Dimensions",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#64748b"),
            angularaxis=dict(color="#94a3b8"),
            bgcolor="#1a1a2e",
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        height=440,
        margin=dict(t=40, b=40, l=80, r=80),
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="culher_pchart1")

    # -- Site Type Distribution Pie Chart -----------------------------------
    st.markdown("### Cultural Site Types")

    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        if type_dist:
            pie_labels = list(type_dist.keys())
            pie_values = list(type_dist.values())

            cat_color_map = {}
            for k, v in HERITAGE_CATEGORIES.items():
                cat_color_map[v["name"]] = v["color"]

            pie_colors = [cat_color_map.get(lbl, "#64748b") for lbl in pie_labels]

            fig_pie = go.Figure(data=go.Pie(
                labels=pie_labels,
                values=pie_values,
                marker=dict(colors=pie_colors),
                textinfo="label+value",
                textfont=dict(color="#e2e8f0"),
                hole=0.35,
            ))
            fig_pie.update_layout(
                paper_bgcolor="#1a1a2e",
                plot_bgcolor="#1a1a2e",
                font=dict(color="#e2e8f0"),
                height=360,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(font=dict(color="#94a3b8")),
            )
            st.plotly_chart(fig_pie, use_container_width=True, key="culher_pchart2")
        else:
            st.info("No cultural sites found in this area.")

    with chart_col2:
        # Count cards in a compact grid
        count_items = list(counts.items())
        for c_name, c_val in count_items:
            c_color = "#eab308" if c_val > 0 else "#475569"
            st.markdown(f"""
            <div style="background:#1a1a2e; border-radius:8px; padding:0.5rem 0.8rem;
                        display:flex; justify-content:space-between; align-items:center;
                        border:1px solid #2a2a4e; margin-bottom:0.3rem;">
                <span style="color:#94a3b8; font-size:0.8rem;">{c_name}</span>
                <span style="color:{c_color}; font-weight:700; font-size:1.05rem;">{c_val}</span>
            </div>
            """, unsafe_allow_html=True)

    # -- Heritage Significance Gauge ----------------------------------------
    st.markdown("### Heritage Significance")

    sig_score = dimensions.get("Heritage Significance", 0)
    sig_color = _score_color(sig_score)

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sig_score,
        title={"text": "Heritage Significance", "font": {"color": "#e2e8f0", "size": 16}},
        number={"font": {"color": sig_color, "size": 48}},
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#64748b"),
            bar=dict(color=sig_color),
            bgcolor="#2a2a4e",
            bordercolor="#1a1a2e",
            steps=[
                {"range": [0, 25], "color": "rgba(239,68,68,0.15)"},
                {"range": [25, 50], "color": "rgba(249,115,22,0.15)"},
                {"range": [50, 75], "color": "rgba(234,179,8,0.15)"},
                {"range": [75, 100], "color": "rgba(34,197,94,0.15)"},
            ],
            threshold=dict(
                line=dict(color="#e2e8f0", width=2),
                thickness=0.8,
                value=sig_score,
            ),
        ),
    ))
    fig_gauge.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        height=300,
        margin=dict(t=60, b=30, l=40, r=40),
    )
    st.plotly_chart(fig_gauge, use_container_width=True, key="culher_pchart3")

    # -- Cultural Sites Table -----------------------------------------------
    st.markdown("### Cultural Sites Inventory")

    if sites_list:
        # Deduplicate and prepare table data
        table_data = []
        seen = set()
        for site in sites_list:
            name = site.get("name", "Unknown")
            stype = site.get("type", "Unknown")
            cat_key = site.get("category", "civic")
            cat_label = HERITAGE_CATEGORIES.get(cat_key, {}).get("name", cat_key)
            key = (name, stype)
            if key not in seen:
                seen.add(key)
                table_data.append({
                    "Name": name,
                    "Type": stype.replace("_", " ").title(),
                    "Category": cat_label,
                })

        # Sort by category then name
        table_data.sort(key=lambda x: (x["Category"], x["Name"]))

        # Show count
        st.markdown(f"""
        <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:0.5rem;">
            Showing {len(table_data)} unique cultural sites within 5 km radius
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            table_data,
            use_container_width=True,
            height=min(400, 35 * len(table_data) + 38),
        )
    else:
        st.info("No cultural sites found in this area.")

    # -- Preservation Climate Panel -----------------------------------------
    st.markdown("### Preservation Climate Conditions")
    pres_cols = st.columns(4)

    pres_metrics = [
        ("Temperature", climate.get("temp_preservation", 0), "#f97316",
         f"{climate.get('temp_now', 'N/A')} C" if climate.get("temp_now") is not None else "N/A"),
        ("Humidity", climate.get("humidity_preservation", 0), "#3b82f6",
         f"{climate.get('humidity', 'N/A')}%" if climate.get("humidity") is not None else "N/A"),
        ("Precipitation", climate.get("precip_preservation", 0), "#06b6d4",
         f"{climate.get('avg_daily_precip', 0)} mm/d"),
        ("Wind", climate.get("wind_preservation", 0), "#a855f7",
         f"{climate.get('wind_speed', 'N/A')} km/h" if climate.get("wind_speed") is not None else "N/A"),
    ]
    for i, (pname, pval, pcolor, pdetail) in enumerate(pres_metrics):
        with pres_cols[i]:
            pc = _score_color(pval)
            st.markdown(f"""
            <div style="background:#1a1a2e; border-radius:10px; padding:0.9rem;
                        text-align:center; border-top:3px solid {pcolor}; margin-bottom:0.5rem;">
                <div style="font-size:1.8rem; font-weight:800; color:{pc};">{pval}</div>
                <div style="color:#94a3b8; font-size:0.78rem;">{pname} Suitability</div>
                <div style="color:#64748b; font-size:0.72rem; margin-top:0.2rem;">Current: {pdetail}</div>
            </div>
            """, unsafe_allow_html=True)
