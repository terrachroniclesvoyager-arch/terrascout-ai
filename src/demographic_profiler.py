"""
TerraScout AI - Demographic Profiling Intelligence Module
Estimates population characteristics and settlement patterns around any GPS
coordinate using free APIs (Overpass / OpenStreetMap).
Dimensions: Settlement Density, Service Coverage, Commercial Activity,
Religious & Cultural, Recreation & Leisure, Education Density.
"""

import streamlit as st
import requests
import math
from typing import Dict, List, Tuple, Any

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DIMENSION_WEIGHTS = {
    "Settlement Density": 0.25, "Service Coverage": 0.20,
    "Commercial Activity": 0.20, "Religious & Cultural": 0.10,
    "Recreation & Leisure": 0.10, "Education Density": 0.15,
}
SETTLEMENT_THRESHOLDS = [
    (8.0, "Metro / Dense Urban", "#e74c3c"),
    (6.0, "Urban", "#e67e22"),
    (3.5, "Suburban", "#f1c40f"),
    (1.5, "Rural", "#27ae60"),
    (0.0, "Remote / Wilderness", "#2c3e50"),
]


def _build_overpass_query(lat: float, lon: float, radius: int,
                          tags: List[str], center: bool = False) -> str:
    """Build an Overpass QL query for nodes/ways matching *tags*."""
    parts = []
    for tag in tags:
        parts.append(f'  node[{tag}](around:{radius},{lat},{lon});')
        parts.append(f'  way[{tag}](around:{radius},{lat},{lon});')
    body = "\n".join(parts)
    out = "out center;" if center else "out body;"
    return f"[out:json][timeout:10];\n(\n{body}\n);\n{out}"


def _extract_locations(elements: List[Dict]) -> Tuple[Dict[str, int], List[Dict]]:
    """Return (counts-by-category, location-dicts) from Overpass elements."""
    counts: Dict[str, int] = {}
    locations: List[Dict] = []
    for el in elements:
        t = el.get("tags", {})
        cat = t.get("amenity") or t.get("shop") or t.get("leisure") or t.get("tourism") or "other"
        counts[cat] = counts.get(cat, 0) + 1
        lat_el = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon_el = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat_el and lon_el:
            locations.append({"lat": lat_el, "lon": lon_el,
                              "name": t.get("name", cat), "type": cat})
    return counts, locations


# ---------------------------------------------------------------------------
# Cached API fetchers (one per dimension)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def _fetch_settlement_data(lat: float, lon: float) -> Dict[str, Any]:
    """Dimension 1 -- Settlement Density within 3 km."""
    tags = ['"building"', '"building"="residential"', '"building"="apartments"',
            '"building"="house"', '"building"="commercial"',
            '"building"="industrial"', '"landuse"="residential"']
    query = _build_overpass_query(lat, lon, 3000, tags)
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return {"total_buildings": 0, "residential": 0, "apartments": 0,
                "houses": 0, "commercial": 0, "industrial": 0,
                "residential_areas": 0, "error": True}
    total = residential = apartments = houses = commercial = industrial = res_areas = 0
    for el in elements:
        t = el.get("tags", {})
        b, lu = t.get("building", ""), t.get("landuse", "")
        if b:
            total += 1
            if b == "residential": residential += 1
            elif b == "apartments": apartments += 1
            elif b == "house": houses += 1
            elif b == "commercial": commercial += 1
            elif b == "industrial": industrial += 1
        if lu == "residential":
            res_areas += 1
    return {"total_buildings": total, "residential": residential,
            "apartments": apartments, "houses": houses,
            "commercial": commercial, "industrial": industrial,
            "residential_areas": res_areas, "error": False}


@st.cache_data(ttl=900)
def _fetch_service_data(lat: float, lon: float) -> Dict[str, Any]:
    """Dimension 2 -- Service Coverage within 5 km."""
    tags = ['"amenity"="school"', '"amenity"="hospital"', '"amenity"="pharmacy"',
            '"amenity"="police"', '"amenity"="fire_station"',
            '"amenity"="post_office"', '"amenity"="clinic"', '"amenity"="doctors"']
    query = _build_overpass_query(lat, lon, 5000, tags, center=True)
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return {"counts": {}, "locations": [], "error": True}
    counts, locations = _extract_locations(elements)
    return {"counts": counts, "locations": locations, "error": False}


@st.cache_data(ttl=900)
def _fetch_commercial_data(lat: float, lon: float) -> Dict[str, Any]:
    """Dimension 3 -- Commercial Activity within 3 km."""
    tags = ['"shop"', '"amenity"="restaurant"', '"amenity"="cafe"',
            '"amenity"="fast_food"', '"shop"="supermarket"',
            '"amenity"="bank"', '"amenity"="atm"', '"amenity"="marketplace"']
    query = _build_overpass_query(lat, lon, 3000, tags, center=True)
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return {"counts": {}, "locations": [], "error": True}
    counts, locations = _extract_locations(elements)
    return {"counts": counts, "locations": locations, "error": False}


@st.cache_data(ttl=900)
def _fetch_religious_cultural_data(lat: float, lon: float) -> Dict[str, Any]:
    """Dimension 4 -- Religious & Cultural within 3 km."""
    tags = ['"amenity"="place_of_worship"', '"amenity"="community_centre"',
            '"amenity"="library"', '"amenity"="arts_centre"',
            '"tourism"="museum"', '"amenity"="theatre"']
    query = _build_overpass_query(lat, lon, 3000, tags, center=True)
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return {"counts": {}, "worship_types": {}, "locations": [], "error": True}
    counts, locations = _extract_locations(elements)
    worship_types: Dict[str, int] = {}
    for el in elements:
        t = el.get("tags", {})
        if t.get("amenity") == "place_of_worship":
            r = t.get("religion", "unknown")
            worship_types[r] = worship_types.get(r, 0) + 1
    return {"counts": counts, "worship_types": worship_types,
            "locations": locations, "error": False}


@st.cache_data(ttl=900)
def _fetch_recreation_data(lat: float, lon: float) -> Dict[str, Any]:
    """Dimension 5 -- Recreation & Leisure within 3 km."""
    tags = ['"leisure"="park"', '"leisure"="playground"',
            '"leisure"="sports_centre"', '"leisure"="swimming_pool"',
            '"leisure"="pitch"', '"leisure"="garden"',
            '"amenity"="cinema"', '"amenity"="theatre"',
            '"leisure"="fitness_centre"', '"leisure"="stadium"']
    query = _build_overpass_query(lat, lon, 3000, tags, center=True)
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return {"counts": {}, "locations": [], "error": True}
    counts, locations = _extract_locations(elements)
    return {"counts": counts, "locations": locations, "error": False}


@st.cache_data(ttl=900)
def _fetch_education_data(lat: float, lon: float) -> Dict[str, Any]:
    """Dimension 6 -- Education Density within 5 km."""
    tags = ['"amenity"="school"', '"amenity"="university"',
            '"amenity"="college"', '"amenity"="kindergarten"',
            '"amenity"="library"', '"amenity"="language_school"',
            '"amenity"="music_school"', '"amenity"="driving_school"']
    query = _build_overpass_query(lat, lon, 5000, tags, center=True)
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return {"counts": {}, "locations": [], "error": True}
    counts, locations = _extract_locations(elements)
    return {"counts": counts, "locations": locations, "error": False}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_settlement(data: Dict[str, Any]) -> Tuple[float, str]:
    """Score settlement density 0-10 and return (score, classification)."""
    if data.get("error"):
        return 0.0, "Unknown"
    total = data.get("total_buildings", 0)
    if total >= 5000:
        score = 10.0
    elif total >= 2000:
        score = 8.0 + 2.0 * (total - 2000) / 3000
    elif total >= 500:
        score = 5.0 + 3.0 * (total - 500) / 1500
    elif total >= 100:
        score = 2.5 + 2.5 * (total - 100) / 400
    elif total >= 20:
        score = 1.0 + 1.5 * (total - 20) / 80
    else:
        score = total * 0.05
    score = min(10.0, max(0.0, round(score, 1)))
    classification = "Remote / Wilderness"
    for threshold, label, _ in SETTLEMENT_THRESHOLDS:
        if score >= threshold:
            classification = label
            break
    return score, classification


def _score_services(data: Dict[str, Any]) -> float:
    if data.get("error"):
        return 0.0
    c = data.get("counts", {})
    weighted = ((c.get("hospital", 0) + c.get("clinic", 0)) * 2.0
                + c.get("pharmacy", 0) * 1.5 + c.get("police", 0) * 1.5
                + c.get("fire_station", 0) * 1.5 + c.get("post_office", 0) * 1.0
                + c.get("doctors", 0) * 1.0)
    return round(min(10.0, max(0.0, weighted / 5.0)), 1)


def _score_commercial(data: Dict[str, Any]) -> float:
    if data.get("error"):
        return 0.0
    total = sum(data.get("counts", {}).values())
    if total >= 500: score = 10.0
    elif total >= 200: score = 7.0 + 3.0 * (total - 200) / 300
    elif total >= 50: score = 4.0 + 3.0 * (total - 50) / 150
    elif total >= 10: score = 1.5 + 2.5 * (total - 10) / 40
    else: score = total * 0.15
    return round(min(10.0, max(0.0, score)), 1)


def _score_religious_cultural(data: Dict[str, Any]) -> float:
    if data.get("error"):
        return 0.0
    c = data.get("counts", {})
    weighted = (c.get("place_of_worship", 0) * 1.0 + c.get("museum", 0) * 2.0
                + c.get("library", 0) * 1.5 + c.get("arts_centre", 0) * 2.0
                + c.get("community_centre", 0) * 1.0)
    return round(min(10.0, max(0.0, weighted / 4.0)), 1)


def _score_recreation(data: Dict[str, Any]) -> float:
    if data.get("error"):
        return 0.0
    c = data.get("counts", {})
    parks = c.get("park", 0) + c.get("garden", 0)
    sports = c.get("sports_centre", 0) + c.get("pitch", 0) + c.get("fitness_centre", 0) + c.get("stadium", 0)
    weighted = (parks * 1.5 + c.get("playground", 0) * 1.0 + sports * 1.2
                + c.get("swimming_pool", 0) * 1.5
                + (c.get("cinema", 0) + c.get("theatre", 0)) * 2.0)
    return round(min(10.0, max(0.0, weighted / 5.0)), 1)


def _score_education(data: Dict[str, Any]) -> float:
    if data.get("error"):
        return 0.0
    c = data.get("counts", {})
    specialty = c.get("language_school", 0) + c.get("music_school", 0) + c.get("driving_school", 0)
    weighted = (c.get("school", 0) * 1.0
                + (c.get("university", 0) + c.get("college", 0)) * 3.0
                + c.get("kindergarten", 0) * 1.0 + c.get("library", 0) * 1.5
                + specialty * 0.8)
    return round(min(10.0, max(0.0, weighted / 4.0)), 1)


def _compute_livability_index(scores: Dict[str, float]) -> float:
    total = sum(scores.get(d, 0.0) * w for d, w in DIMENSION_WEIGHTS.items())
    wsum = sum(DIMENSION_WEIGHTS.values())
    return round(total / wsum, 1) if wsum else 0.0


def _classify_settlement(score: float) -> Tuple[str, str]:
    for threshold, label, colour in SETTLEMENT_THRESHOLDS:
        if score >= threshold:
            return label, colour
    return "Unknown", "#95a5a6"


# ---------------------------------------------------------------------------
# Visualisation helpers
# ---------------------------------------------------------------------------

def _render_radar_chart(scores: Dict[str, float]) -> None:
    """Plotly radar chart of the six dimensions."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.warning("Install plotly for radar chart visualisation.")
        return
    cats = list(scores.keys())
    vals = [scores[c] for c in cats]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]],
        fill="toself", fillcolor="rgba(52,152,219,0.25)",
        line=dict(color="#3498db", width=2), name="Score"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10],
                                   tickfont=dict(size=10)),
                   angularaxis=dict(tickfont=dict(size=11))),
        showlegend=False, margin=dict(l=60, r=60, t=40, b=40),
        height=420,
        title=dict(text="Demographic Profile Radar", x=0.5,
                   font=dict(size=14)))
    st.plotly_chart(fig, use_container_width=True, key="demoprof_radar")


def _render_map(lat: float, lon: float, all_locations: List[Dict]) -> None:
    """Folium map with service / POI markers."""
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("Install folium and streamlit-folium for map rendering.")
        return

    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB positron")
    folium.Marker([lat, lon], popup="Target Location",
                  icon=folium.Icon(color="red", icon="crosshairs",
                                   prefix="fa")).add_to(m)

    colour_map = {
        "hospital": "red", "clinic": "red", "doctors": "pink",
        "pharmacy": "orange", "police": "darkblue", "fire_station": "darkred",
        "school": "blue", "university": "darkpurple", "college": "darkpurple",
        "kindergarten": "lightblue", "library": "cadetblue",
        "restaurant": "green", "cafe": "green", "fast_food": "green",
        "supermarket": "lightgreen", "bank": "gray", "atm": "gray",
        "place_of_worship": "purple", "museum": "beige",
        "park": "darkgreen", "playground": "lightgreen",
        "cinema": "black", "theatre": "black",
    }
    icon_map = {
        "hospital": "plus-square", "clinic": "medkit",
        "doctors": "stethoscope", "pharmacy": "prescription-bottle-alt",
        "police": "shield-alt", "fire_station": "fire-extinguisher",
        "school": "graduation-cap", "university": "university",
        "college": "university", "kindergarten": "child", "library": "book",
        "restaurant": "utensils", "cafe": "coffee", "fast_food": "hamburger",
        "supermarket": "shopping-cart", "bank": "university",
        "atm": "money-bill", "place_of_worship": "church",
        "museum": "landmark", "park": "tree", "playground": "child",
        "cinema": "film", "theatre": "theater-masks",
    }

    for loc in all_locations[:250]:
        ptype = loc.get("type", "")
        folium.Marker(
            [loc["lat"], loc["lon"]],
            popup=f"{loc.get('name', '')} ({ptype})",
            icon=folium.Icon(color=colour_map.get(ptype, "gray"),
                             icon=icon_map.get(ptype, "info-sign"),
                             prefix="fa")).add_to(m)

    folium.Circle([lat, lon], radius=3000, color="#3498db",
                  fill=True, fill_opacity=0.05, weight=1,
                  popup="3 km radius").add_to(m)
    folium.Circle([lat, lon], radius=5000, color="#e67e22",
                  fill=False, weight=1, dash_array="5",
                  popup="5 km radius").add_to(m)
    st_folium(m, width=None, height=520, returned_objects=[], key="demoprof_map")


def _render_dimension_details(title: str, score: float,
                               counts: Dict[str, int]) -> None:
    """Expandable section for one dimension breakdown."""
    with st.expander(f"{title} -- Score: {score}/10", expanded=False):
        if not counts:
            st.write("No data found in the search radius.")
            return
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        col_a, col_b = st.columns(2)
        half = math.ceil(len(sorted_counts) / 2)
        for idx, (k, v) in enumerate(sorted_counts):
            target = col_a if idx < half else col_b
            target.write(f"**{k.replace('_', ' ').title()}**: {v}")
        st.caption(f"Total features: {sum(counts.values())}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_demographic_profiler_tab() -> None:
    """Render the Demographic Profiler AI tab in Streamlit."""

    st.markdown("## Demographic Profiler AI")
    st.caption("Settlement patterns & population characteristics analysis")

    # --- Coordinate inputs -------------------------------------------------
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, min_value=-90.0,
                          max_value=90.0, format="%.4f", key="demoprof_lat")
    lon = c2.number_input("Longitude", value=12.4964, min_value=-180.0,
                          max_value=180.0, format="%.4f", key="demoprof_lon")

    if not st.button("Profile Demographics", key="demoprof_btn"):
        st.info("Enter GPS coordinates and click **Profile Demographics** to "
                "analyse settlement patterns, services, commerce, culture, "
                "recreation and education around the target location.")
        return

    # --- Fetch all six dimensions ------------------------------------------
    with st.spinner("Profiling demographic characteristics..."):
        settlement_data = _fetch_settlement_data(lat, lon)
        service_data = _fetch_service_data(lat, lon)
        commercial_data = _fetch_commercial_data(lat, lon)
        religious_data = _fetch_religious_cultural_data(lat, lon)
        recreation_data = _fetch_recreation_data(lat, lon)
        education_data = _fetch_education_data(lat, lon)

    # --- Compute scores ----------------------------------------------------
    settlement_score, settlement_class = _score_settlement(settlement_data)
    service_score = _score_services(service_data)
    commercial_score = _score_commercial(commercial_data)
    religious_score = _score_religious_cultural(religious_data)
    recreation_score = _score_recreation(recreation_data)
    education_score = _score_education(education_data)

    scores: Dict[str, float] = {
        "Settlement Density": settlement_score,
        "Service Coverage": service_score,
        "Commercial Activity": commercial_score,
        "Religious & Cultural": religious_score,
        "Recreation & Leisure": recreation_score,
        "Education Density": education_score,
    }
    livability = _compute_livability_index(scores)
    _, badge_colour = _classify_settlement(settlement_score)

    # --- Error banner ------------------------------------------------------
    dim_labels = ["Settlement", "Services", "Commercial",
                  "Religious/Cultural", "Recreation", "Education"]
    dim_data = [settlement_data, service_data, commercial_data,
                religious_data, recreation_data, education_data]
    errors = [l for l, d in zip(dim_labels, dim_data) if d.get("error")]
    if errors:
        st.warning(f"Could not fetch data for: {', '.join(errors)}. "
                   "Scores may be incomplete. The Overpass API might be "
                   "rate-limited.")

    # --- Settlement classification badge -----------------------------------
    st.markdown(
        f'<div style="background:{badge_colour};color:#fff;padding:10px 18px;'
        f'border-radius:8px;display:inline-block;font-size:1.15em;'
        f'font-weight:600;margin-bottom:12px;">'
        f'{settlement_class} &mdash; Livability Index: {livability}/10'
        f'</div>', unsafe_allow_html=True)

    # --- Top-level metrics -------------------------------------------------
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Settlement", f"{settlement_score}/10")
    m2.metric("Services", f"{service_score}/10")
    m3.metric("Commerce", f"{commercial_score}/10")
    m4.metric("Culture", f"{religious_score}/10")
    m5.metric("Recreation", f"{recreation_score}/10")
    m6.metric("Education", f"{education_score}/10")
    st.markdown("---")

    # --- Radar chart & summary ---------------------------------------------
    left_col, right_col = st.columns([1, 1])
    with left_col:
        _render_radar_chart(scores)
    with right_col:
        st.markdown("### Dimension Summary")
        for dim_name, dim_score in scores.items():
            pct = int(dim_score * 10)
            bar_col = ("#27ae60" if dim_score >= 6
                       else "#f39c12" if dim_score >= 3
                       else "#e74c3c")
            st.markdown(
                f"**{dim_name}**: {dim_score}/10\n"
                f'<div style="background:#eee;border-radius:4px;height:14px;'
                f'margin-bottom:8px;">'
                f'<div style="width:{pct}%;background:{bar_col};'
                f'height:100%;border-radius:4px;"></div></div>',
                unsafe_allow_html=True)

        st.markdown("### Key Statistics")
        total_buildings = settlement_data.get("total_buildings", 0)
        total_services = sum(service_data.get("counts", {}).values())
        total_commerce = sum(commercial_data.get("counts", {}).values())
        total_education = sum(education_data.get("counts", {}).values())
        st.write(f"- Buildings (3 km): **{total_buildings}**")
        st.write(f"- Service points (5 km): **{total_services}**")
        st.write(f"- Commercial POIs (3 km): **{total_commerce}**")
        st.write(f"- Education facilities (5 km): **{total_education}**")
    st.markdown("---")

    # --- Dimension detail expanders ----------------------------------------
    _render_dimension_details("Settlement Density", settlement_score, {
        "Total Buildings": settlement_data.get("total_buildings", 0),
        "Residential": settlement_data.get("residential", 0),
        "Apartments": settlement_data.get("apartments", 0),
        "Houses": settlement_data.get("houses", 0),
        "Commercial": settlement_data.get("commercial", 0),
        "Industrial": settlement_data.get("industrial", 0),
        "Residential Areas": settlement_data.get("residential_areas", 0),
    })
    _render_dimension_details("Service Coverage", service_score,
                              service_data.get("counts", {}))
    _render_dimension_details("Commercial Activity", commercial_score,
                              commercial_data.get("counts", {}))

    rel_counts = dict(religious_data.get("counts", {}))
    for rname, rcount in religious_data.get("worship_types", {}).items():
        rel_counts[f"worship:{rname}"] = rcount
    _render_dimension_details("Religious & Cultural", religious_score,
                              rel_counts)
    _render_dimension_details("Recreation & Leisure", recreation_score,
                              recreation_data.get("counts", {}))
    _render_dimension_details("Education Density", education_score,
                              education_data.get("counts", {}))
    st.markdown("---")

    # --- Map ---------------------------------------------------------------
    st.markdown("### Service & POI Map")
    all_locations: List[Dict] = []
    for src in [service_data, commercial_data, religious_data,
                recreation_data, education_data]:
        all_locations.extend(src.get("locations", []))

    if all_locations:
        _render_map(lat, lon, all_locations)
        st.caption(f"Showing up to 250 of {len(all_locations)} points of interest.")
    else:
        st.info("No geo-located points of interest found to display on the map.")

    # --- Population estimate heuristic -------------------------------------
    st.markdown("---")
    st.markdown("### Population Estimate (Heuristic)")
    building_count = settlement_data.get("total_buildings", 0)
    residential_count = (settlement_data.get("residential", 0)
                         + settlement_data.get("apartments", 0)
                         + settlement_data.get("houses", 0))
    if residential_count == 0:
        residential_count = int(building_count * 0.6)

    avg_pp = 3.5
    if settlement_data.get("apartments", 0) > settlement_data.get("houses", 0):
        avg_pp = 8.0
    elif settlement_score >= 8:
        avg_pp = 6.0

    est_pop = int(residential_count * avg_pp)
    area_km2 = math.pi * 3.0 * 3.0
    density = round(est_pop / area_km2, 1) if area_km2 > 0 else 0

    pe1, pe2, pe3 = st.columns(3)
    pe1.metric("Estimated Population (3 km)", f"{est_pop:,}")
    pe2.metric("Density (per sq km)", f"{density:,}")
    pe3.metric("Residential Buildings", f"{residential_count:,}")
    st.caption("Population estimate is a rough heuristic based on building "
               "counts and types. Not for official planning purposes.")

    # --- Data quality note -------------------------------------------------
    st.markdown("---")
    st.caption("Data sourced from OpenStreetMap via the Overpass API. Coverage "
               "and accuracy vary by region. Scores reflect mapped features "
               "only and may undercount in areas with sparse OSM coverage.")
