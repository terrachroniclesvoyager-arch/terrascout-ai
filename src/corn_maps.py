# -*- coding: utf-8 -*-
"""
World Corn & Maize Heritage Explorer module for TerraScout AI.
Maps corn fields, ancient maize varieties, corn ethanol plants, corn palaces,
Mexican maize heritage, and Mesoamerican corn traditions using the Overpass API.
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
    "Modern Corn Fields",
    "Ancient Maize Varieties",
    "Corn Ethanol Plants",
    "Popcorn Heritage Sites",
    "Mexican Maize Heritage",
    "Sweet Corn Heritage",
    "Corn Belt Heritage",
    "Maize Research Centers",
    "Corn Festival Sites",
    "GMO Corn Fields",
]

MODE_CONFIG = {
    "Modern Corn Fields": {
        "color": "#10b981", "icon": "leaf",
        "desc": "Commercial corn and maize farmland worldwide.",
        "preset": {"lat": 42.0, "lon": -93.5, "radius": 50, "zoom": 8},
        "query_tags": [("landuse", "farmland"), ("crop", "maize")],
        "fallback_tags": [("landuse", "farmland"), ("crop", "corn")],
    },
    "Ancient Maize Varieties": {
        "color": "#f59e0b", "icon": "tree",
        "desc": "Heritage maize varieties and traditional corn cultivation.",
        "preset": {"lat": 17.1, "lon": -96.7, "radius": 30, "zoom": 9},
        "query_tags": [("crop", "maize"), ("heritage", "yes")],
        "fallback_tags": [("crop", "maize")],
    },
    "Corn Ethanol Plants": {
        "color": "#8b5cf6", "icon": "industry",
        "desc": "Corn-based ethanol production facilities.",
        "preset": {"lat": 41.3, "lon": -96.4, "radius": 50, "zoom": 8},
        "query_tags": [("industrial", "ethanol"), ("feedstock", "corn")],
        "fallback_tags": [("industrial", "ethanol")],
    },
    "Popcorn Heritage Sites": {
        "color": "#06b6d4", "icon": "museum",
        "desc": "Popcorn museums, corn palaces, and heritage attractions.",
        "preset": {"lat": 43.7, "lon": -98.3, "radius": 15, "zoom": 10},
        "query_tags": [("tourism", "attraction")],
        "fallback_tags": [("tourism", "museum")],
    },
    "Mexican Maize Heritage": {
        "color": "#ec4899", "icon": "tree",
        "desc": "Traditional maize cultivation in Mexico, birthplace of corn.",
        "preset": {"lat": 19.7, "lon": -98.9, "radius": 20, "zoom": 10},
        "query_tags": [("crop", "maize")],
        "fallback_tags": [("landuse", "farmland")],
    },
    "Sweet Corn Heritage": {
        "color": "#f97316", "icon": "leaf",
        "desc": "Sweet corn fields and heritage varieties.",
        "preset": {"lat": 40.1, "lon": -89.4, "radius": 50, "zoom": 8},
        "query_tags": [("crop", "sweet_corn")],
        "fallback_tags": [("crop", "maize")],
    },
    "Corn Belt Heritage": {
        "color": "#a855f7", "icon": "globe",
        "desc": "Historic corn belt regions in the US Midwest.",
        "preset": {"lat": 42.0, "lon": -93.5, "radius": 50, "zoom": 7},
        "query_tags": [("crop", "corn")],
        "fallback_tags": [("landuse", "farmland")],
    },
    "Maize Research Centers": {
        "color": "#14b8a6", "icon": "university",
        "desc": "Agricultural research stations and maize breeding programs.",
        "preset": {"lat": 19.7, "lon": -98.9, "radius": 20, "zoom": 10},
        "query_tags": [("amenity", "research_institute")],
        "fallback_tags": [("amenity", "university")],
    },
    "Corn Festival Sites": {
        "color": "#3b82f6", "icon": "star",
        "desc": "Corn festivals, maize fairs, and harvest celebrations.",
        "preset": {"lat": 43.7, "lon": -98.3, "radius": 15, "zoom": 10},
        "query_tags": [("tourism", "attraction")],
        "fallback_tags": [("leisure", "park")],
    },
    "GMO Corn Fields": {
        "color": "#ef4444", "icon": "leaf",
        "desc": "Genetically modified corn cultivation areas.",
        "preset": {"lat": 42.0, "lon": -93.5, "radius": 50, "zoom": 8},
        "query_tags": [("crop", "maize"), ("gmo", "yes")],
        "fallback_tags": [("crop", "maize")],
    },
}

PRESETS = {
    "Custom": None,
    "Iowa Corn Belt, USA": {"lat": 42.0, "lon": -93.5, "radius": 50},
    "Illinois, USA": {"lat": 40.1, "lon": -89.4, "radius": 50},
    "Nebraska, USA": {"lat": 41.3, "lon": -96.4, "radius": 50},
    "Oaxaca, Mexico": {"lat": 17.1, "lon": -96.7, "radius": 30},
    "Teotihuacan, Mexico": {"lat": 19.7, "lon": -98.9, "radius": 20},
    "Guatemala Highlands": {"lat": 14.6, "lon": -91.5, "radius": 30},
    "Corn Palace, South Dakota": {"lat": 43.7, "lon": -98.3, "radius": 15},
    "South Africa Maize Triangle": {"lat": -26.2, "lon": 28.0, "radius": 50},
    "Argentina Pampas": {"lat": -34.6, "lon": -61.0, "radius": 50},
    "Brazil Cerrado": {"lat": -15.8, "lon": -47.9, "radius": 50},
    "China Corn Belt": {"lat": 43.8, "lon": 125.3, "radius": 50},
    "Ukraine Maize Region": {"lat": 48.4, "lon": 35.0, "radius": 40},
    "France Maize Region": {"lat": 43.9, "lon": 0.9, "radius": 30},
    "Spain Corn Belt": {"lat": 42.6, "lon": -5.6, "radius": 30},
    "Indian Corn Belt": {"lat": 23.3, "lon": 85.3, "radius": 40},
}


# =====================================================================
# OVERPASS QUERY
# =====================================================================
@st.cache_data(ttl=3600)
def _search_corn(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for corn/maize-related features."""
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
            "crop": tags.get("crop", ""),
            "heritage": tags.get("heritage", ""),
            "gmo": tags.get("gmo", ""),
        })
    return features


# =====================================================================
# POPUP BUILDER
# =====================================================================
def _popup(f: dict, accent: str) -> str:
    """Dark-themed popup with XSS escaping."""
    name = html_module.escape(str(f["name"]))
    desc = html_module.escape(str(f.get("description", ""))[:120])
    crop = html_module.escape(str(f.get("crop", "")))
    heritage = html_module.escape(str(f.get("heritage", "")))
    gmo = html_module.escape(str(f.get("gmo", "")))
    lines = f"<b style='color:{accent};'>{name}</b><br>"
    if desc:
        lines += f"<span style='color:{_TEXT2};font-size:0.8em;'>{desc}</span><br>"
    if crop:
        lines += f"<span style='color:{_TEXT2};'>Crop:</span> {crop}<br>"
    if heritage:
        lines += f"<span style='color:{_TEXT2};'>Heritage:</span> {heritage}<br>"
    if gmo:
        lines += f"<span style='color:{_TEXT2};'>GMO:</span> {gmo}<br>"
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
def render_corn_maps_tab():
    """Render the World Corn & Maize Heritage Explorer tab."""

    header_html = (
        '<div class="tab-header emerald">'
        '<h4>🌽 World Corn & Maize Heritage Explorer</h4>'
        '<p>Discover maize fields, ancient varieties, corn palaces '
        '& Mesoamerican corn heritage</p></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Mode selection
    mode = st.selectbox("Exploration Mode", MAP_MODES, key="corn_mode")
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
                              max_value=90.0, key="corn_lat")
    with c2:
        lon = st.number_input("Longitude", value=cfg["preset"]["lon"],
                              format="%.4f", min_value=-180.0,
                              max_value=180.0, key="corn_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 150,
                           cfg["preset"]["radius"], key="corn_rad")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()),
                          key="corn_preset")
    if preset != "Custom" and PRESETS[preset]:
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Corn Heritage", key="corn_go", type="primary",
                 use_container_width=True):
        st.session_state.corn_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "corn_params" not in st.session_state:
        st.info("Choose a mode and location, then click Explore Corn Heritage.")
        return

    cp = st.session_state.corn_params

    # Fetch data
    with st.spinner(f"Searching {cp['mode']} via OpenStreetMap..."):
        data = _search_corn(cp["lat"], cp["lon"], cp["radius"], cp["mode"])
        features = _extract_features(data, cp["mode"])

    if not features:
        st.warning("No features found. Try a larger radius or different mode.")
        return

    # Stats
    st.markdown("---")
    st.markdown("#### Results Overview")
    named = sum(1 for f in features if f["name"] != "Unnamed")
    heritage = sum(1 for f in features if f.get("heritage"))
    cols = st.columns(4)
    cols[0].metric("Total Features", len(features))
    cols[1].metric("Named Sites", named)
    cols[2].metric("Heritage Sites", heritage)
    cols[3].metric("Search Radius", f"{cp['radius']} km")

    # Map
    st.markdown("---")
    accent = MODE_CONFIG[cp["mode"]]["color"]
    st.markdown(
        f"<span style='color:{accent};font-weight:600;'>"
        f"● {html_module.escape(cp['mode'])}</span>",
        unsafe_allow_html=True,
    )
    zoom = MODE_CONFIG[cp["mode"]]["preset"]["zoom"]
    m = _build_map(features, [cp["lat"], cp["lon"]], zoom, accent)
    folium.Circle(
        location=[cp["lat"], cp["lon"]],
        radius=cp["radius"] * 1000,
        color=_ACCENT, fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)
    st_html(m._repr_html_(), height=500)

    # Data table
    st.markdown("---")
    rows = [{
        "Name": f["name"], "Latitude": round(f["lat"], 5),
        "Longitude": round(f["lon"], 5),
        "Crop": f.get("crop", ""),
        "Heritage": f.get("heritage", ""),
        "GMO": f.get("gmo", ""),
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
        f"Download {len(rows)} Corn Heritage Sites (CSV)",
        data=buf.getvalue(),
        file_name=f"corn_{cp['mode'].lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="corn_dl",
    )
