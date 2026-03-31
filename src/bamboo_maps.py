# -*- coding: utf-8 -*-
"""
World Bamboo & Sustainable Materials module for TerraScout AI.
Maps bamboo forests, sustainable architecture, crafts, rattan heritage,
and research centers using the Overpass API.
"""

import io
import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import html as html_module
from streamlit.components.v1 import html as st_html
from src.overpass_client import query_overpass

_BG, _SURFACE, _CARD = "#0a0e1a", "#111827", "#1a2235"
_BORDER, _TEXT, _TEXT2, _ACCENT = "#2a3550", "#e8ecf4", "#8b97b0", "#06b6d4"
MAP_MODES = [
    "Giant Bamboo Forests",
    "Bamboo Architecture",
    "Japanese Bamboo Gardens",
    "Chinese Bamboo Heritage",
    "Southeast Asian Bamboo",
    "Bamboo Craft Centers",
    "Rattan & Wicker Heritage",
    "Sustainable Building Sites",
    "Bamboo Bicycle Projects",
    "World Bamboo Research",
]

MODE_CONFIG = {
    "Giant Bamboo Forests": {
        "color": "#10b981", "icon": "tree",
        "desc": "Major bamboo forests and natural groves worldwide.",
        "preset": {"lat": 24.5, "lon": 103.5, "radius": 80, "zoom": 5},
        "query_tags": [("natural", "wood"), ("leaf_type", "bamboo")],
        "fallback_tags": [("natural", "wood")],
    },
    "Bamboo Architecture": {
        "color": "#f59e0b", "icon": "building",
        "desc": "Buildings and structures made with bamboo materials.",
        "preset": {"lat": -8.5, "lon": 115.3, "radius": 50, "zoom": 9},
        "query_tags": [("building:material", "bamboo")],
        "fallback_tags": [("building:material", "bamboo")],
    },
    "Japanese Bamboo Gardens": {
        "color": "#8b5cf6", "icon": "leaf",
        "desc": "Famous bamboo groves and gardens in Japan.",
        "preset": {"lat": 35.01, "lon": 135.67, "radius": 30, "zoom": 10},
        "query_tags": [("leisure", "garden"), ("garden:type", "bamboo")],
        "fallback_tags": [("leisure", "garden")],
    },
    "Chinese Bamboo Heritage": {
        "color": "#06b6d4", "icon": "tree",
        "desc": "Bamboo forests and heritage sites across China.",
        "preset": {"lat": 29.8, "lon": 104.8, "radius": 100, "zoom": 6},
        "query_tags": [("natural", "wood"), ("leaf_type", "bamboo")],
        "fallback_tags": [("natural", "wood")],
    },
    "Southeast Asian Bamboo": {
        "color": "#ec4899", "icon": "tree",
        "desc": "Bamboo in Southeast Asian landscapes and cultures.",
        "preset": {"lat": 13.75, "lon": 100.5, "radius": 60, "zoom": 6},
        "query_tags": [("natural", "wood"), ("species", "bamboo")],
        "fallback_tags": [("natural", "wood")],
    },
    "Bamboo Craft Centers": {
        "color": "#f97316", "icon": "shop",
        "desc": "Workshops and shops specializing in bamboo crafts.",
        "preset": {"lat": 26.9, "lon": 75.8, "radius": 50, "zoom": 7},
        "query_tags": [("craft", "basket_maker"), ("shop", "craft")],
        "fallback_tags": [("craft", "basket_maker")],
    },
    "Rattan & Wicker Heritage": {
        "color": "#a855f7", "icon": "shop",
        "desc": "Rattan and wicker craft traditions and markets.",
        "preset": {"lat": 3.1, "lon": 101.7, "radius": 40, "zoom": 8},
        "query_tags": [("craft", "basket_maker"), ("shop", "furniture")],
        "fallback_tags": [("craft", "basket_maker")],
    },
    "Sustainable Building Sites": {
        "color": "#14b8a6", "icon": "building",
        "desc": "Eco-friendly and sustainable construction projects.",
        "preset": {"lat": 52.5, "lon": 13.4, "radius": 30, "zoom": 10},
        "query_tags": [("building:material", "wood"), ("sustainable", "yes")],
        "fallback_tags": [("building:material", "wood")],
    },
    "Bamboo Bicycle Projects": {
        "color": "#3b82f6", "icon": "bicycle",
        "desc": "Bamboo bicycle workshops and social enterprises.",
        "preset": {"lat": 5.6, "lon": -0.19, "radius": 30, "zoom": 10},
        "query_tags": [("shop", "bicycle"), ("craft", "bicycle")],
        "fallback_tags": [("shop", "bicycle")],
    },
    "World Bamboo Research": {
        "color": "#ef4444", "icon": "university",
        "desc": "Botanical gardens, universities, and research institutions.",
        "preset": {"lat": 22.3, "lon": 114.2, "radius": 50, "zoom": 8},
        "query_tags": [("leisure", "garden"), ("garden:type", "botanical")],
        "fallback_tags": [("leisure", "garden")],
    },
}

PRESETS = {
    "Custom": None,
    "Arashiyama, Kyoto, Japan": {"lat": 35.01, "lon": 135.67, "radius": 10},
    "Bali, Indonesia": {"lat": -8.5, "lon": 115.3, "radius": 30},
    "Sichuan Bamboo Sea, China": {"lat": 28.6, "lon": 104.8, "radius": 50},
    "Anji, Zhejiang, China": {"lat": 30.6, "lon": 119.7, "radius": 30},
    "Damyang, South Korea": {"lat": 35.3, "lon": 127.0, "radius": 20},
    "Assam, India": {"lat": 26.1, "lon": 91.7, "radius": 40},
    "Chiang Mai, Thailand": {"lat": 18.8, "lon": 99.0, "radius": 30},
    "Accra, Ghana (Bamboo Bikes)": {"lat": 5.6, "lon": -0.19, "radius": 20},
    "Berlin, Germany (Eco Build)": {"lat": 52.5, "lon": 13.4, "radius": 20},
    "Manizales, Colombia": {"lat": 5.07, "lon": -75.5, "radius": 30},
}


# =====================================================================
# OVERPASS QUERY
# =====================================================================
@st.cache_data(ttl=3600)
def _search_bamboo(lat: float, lon: float, radius_km: float,
                   mode: str) -> dict:
    """Query Overpass API for bamboo/sustainable material features."""
    cfg = MODE_CONFIG[mode]
    radius_m = int(radius_km * 1000)
    parts = []
    for key, val in cfg["query_tags"]:
        parts.append(f'node["{key}"="{val}"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["{key}"="{val}"](around:{radius_m},{lat},{lon});')
    query = f"""[out:json][timeout:60];({chr(10).join(parts)});out body;>;out skel qt;"""
    result = query_overpass(query)
    if result and "_error" not in result:
        return result
    # Fallback with broader tags
    parts2 = []
    for key, val in cfg["fallback_tags"]:
        parts2.append(f'node["{key}"="{val}"](around:{radius_m},{lat},{lon});')
        parts2.append(f'way["{key}"="{val}"](around:{radius_m},{lat},{lon});')
    query2 = f"""[out:json][timeout:60];({chr(10).join(parts2)});out body;>;out skel qt;"""
    result2 = query_overpass(query2)
    if result2 is None or "_error" in result2:
        err = (result2 or {}).get("_error", "Unknown error")
        st.error(f"Overpass query failed: {err}. Try a smaller radius.")
        return {"elements": []}
    return result2


# =====================================================================
# FEATURE EXTRACTION
# =====================================================================
def _extract_features(data: dict, mode: str) -> list:
    """Extract features with lat/lon from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])
    features, seen = [], set()
    cfg = MODE_CONFIG[mode]
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        eid = el.get("id")
        if eid in seen:
            continue
        seen.add(eid)
        lat, lon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [node_lookup[n] for n in nodes if n in node_lookup]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)
        if lat is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        features.append({
            "name": name, "lat": lat, "lon": lon,
            "color": cfg["color"], "osm_id": eid,
            "tags": tags,
            "description": tags.get("description", ""),
            "material": tags.get("building:material", tags.get("material", "")),
            "species": tags.get("species", tags.get("genus", "")),
        })
    return features


# =====================================================================
# POPUP BUILDER
# =====================================================================
def _popup(f: dict, accent: str) -> str:
    """Dark-themed popup with XSS escaping."""
    name = html_module.escape(str(f["name"]))
    desc = html_module.escape(str(f.get("description", ""))[:120])
    mat = html_module.escape(str(f.get("material", "")))
    sp = html_module.escape(str(f.get("species", "")))
    lines = f"<b style='color:{accent};'>{name}</b><br>"
    if desc:
        lines += f"<span style='color:{_TEXT2};font-size:0.8em;'>{desc}</span><br>"
    if mat:
        lines += f"<span style='color:{_TEXT2};'>Material:</span> {mat}<br>"
    if sp:
        lines += f"<span style='color:{_TEXT2};'>Species:</span> {sp}<br>"
    lines += f"<span style='color:#5a6580;font-size:0.75em;'>{f['lat']:.4f}, {f['lon']:.4f}</span>"
    return (f"<div style='min-width:200px;background:{_CARD};color:{_TEXT};"
            f"padding:8px;border-radius:8px;border:1px solid {accent};'>{lines}</div>")


# =====================================================================
# MAP BUILDER
# =====================================================================
def _build_map(features: list, center: list, zoom: int, accent: str):
    """Build a dark folium map with circle markers."""
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter")
    for f in features:
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=7,
            color=f["color"], fill=True, fill_color=f["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(_popup(f, accent), max_width=300),
            tooltip=html_module.escape(str(f["name"])),
        ).add_to(m)
    return m


# =====================================================================
# MAIN RENDER
# =====================================================================
def render_bamboo_maps_tab():
    """Render the World Bamboo & Sustainable Materials Explorer tab."""

    header_html = (
        '<div class="tab-header emerald">'
        '<h4>\U0001f38b World Bamboo & Sustainable Materials Explorer</h4>'
        '<p>Discover bamboo forests, sustainable building, rattan crafts '
        '& eco-materials worldwide</p></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Mode selection
    mode = st.selectbox("Exploration Mode", MAP_MODES, key="bamboo_mode")
    cfg = MODE_CONFIG[mode]
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(cfg['desc'])}</p>",
        unsafe_allow_html=True,
    )

    # Location controls
    st.markdown("#### Search Parameters")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=cfg["preset"]["lat"],
                              format="%.4f", min_value=-90.0,
                              max_value=90.0, key="bamboo_lat")
    with c2:
        lon = st.number_input("Longitude", value=cfg["preset"]["lon"],
                              format="%.4f", min_value=-180.0,
                              max_value=180.0, key="bamboo_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 150,
                           cfg["preset"]["radius"], key="bamboo_rad")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()),
                          key="bamboo_preset")
    if preset != "Custom" and PRESETS[preset]:
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore", key="bamboo_go", type="primary", width="stretch"):
        st.session_state.bamboo_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "bamboo_params" not in st.session_state:
        st.info("Choose a mode and location, then click Explore.")
        return

    bp = st.session_state.bamboo_params

    # Fetch data
    with st.spinner(f"Searching {bp['mode']} via OpenStreetMap..."):
        data = _search_bamboo(bp["lat"], bp["lon"], bp["radius"], bp["mode"])
        features = _extract_features(data, bp["mode"])

    if not features:
        st.warning("No features found. Try a larger radius or different mode.")
        return

    # Stats
    st.markdown("---")
    st.markdown("#### Results Overview")
    named = sum(1 for f in features if f["name"] != "Unnamed")
    cols = st.columns(3)
    cols[0].metric("Total Features", len(features))
    cols[1].metric("Named Features", named)
    cols[2].metric("Search Radius", f"{bp['radius']} km")

    # Map
    st.markdown("---")
    accent = MODE_CONFIG[bp["mode"]]["color"]
    st.markdown(
        f"<span style='color:{accent};font-weight:600;'>"
        f"● {html_module.escape(bp['mode'])}</span>",
        unsafe_allow_html=True,
    )
    zoom = MODE_CONFIG[bp["mode"]]["preset"]["zoom"]
    m = _build_map(features, [bp["lat"], bp["lon"]], zoom, accent)
    folium.Circle(
        location=[bp["lat"], bp["lon"]],
        radius=bp["radius"] * 1000,
        color=_ACCENT, fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)
    st_html(m._repr_html_(), height=500)

    # Data table
    st.markdown("---")
    rows = [{
        "Name": f["name"], "Latitude": round(f["lat"], 5),
        "Longitude": round(f["lon"], 5),
        "Material": f.get("material", ""),
        "Species": f.get("species", ""),
        "Description": f.get("description", ""),
        "OSM ID": f.get("osm_id", ""),
    } for f in features]
    df = pd.DataFrame(rows)
    with st.expander(f"Full Data Table ({len(df)} features)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # Download
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(rows)} Features (CSV)",
        data=buf.getvalue(),
        file_name=f"bamboo_{bp['mode'].lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="bamboo_dl",
    )
