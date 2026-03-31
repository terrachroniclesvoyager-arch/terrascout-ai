# -*- coding: utf-8 -*-
"""
World Cotton & Textile Heritage Explorer module for TerraScout AI.
Maps cotton fields, textile mills, gin houses, and fabric heritage worldwide
using the Overpass API.
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
    "Modern Cotton Fields",
    "Historic Cotton Mills",
    "Cotton Gin Heritage",
    "American Cotton Belt",
    "Egyptian Cotton Heritage",
    "Indian Cotton Heritage",
    "Cotton Museum Sites",
    "Silk Road Textile Heritage",
    "Organic Cotton Farms",
    "GMO Cotton Fields",
]

MODE_CONFIG = {
    "Modern Cotton Fields": {"color": "#f0f8ff", "icon": "tree", "desc": "Contemporary cotton farming regions worldwide.",
        "preset": {"lat": 33.5, "lon": -90.9, "radius": 50, "zoom": 8}, "query_tags": [("landuse", "farmland"), ("crop", "cotton")], "fallback_tags": [("landuse", "farmland")]},
    "Historic Cotton Mills": {"color": "#8b4513", "icon": "industry", "desc": "Historic textile mills and cotton processing centers.",
        "preset": {"lat": 33.5, "lon": -90.9, "radius": 50, "zoom": 8}, "query_tags": [("historic", "mill")], "fallback_tags": [("building", "industrial")]},
    "Cotton Gin Heritage": {"color": "#d2691e", "icon": "cog", "desc": "Historic cotton gin houses and processing sites.",
        "preset": {"lat": 32.4, "lon": -86.9, "radius": 50, "zoom": 8}, "query_tags": [("craft", "cotton_gin")], "fallback_tags": [("historic", "industrial")]},
    "American Cotton Belt": {"color": "#4169e1", "icon": "map", "desc": "Cotton farming across the American South.",
        "preset": {"lat": 33.5, "lon": -90.9, "radius": 50, "zoom": 8}, "query_tags": [("crop", "cotton")], "fallback_tags": [("landuse", "farmland")]},
    "Egyptian Cotton Heritage": {"color": "#ffd700", "icon": "sun", "desc": "Famous Egyptian cotton growing regions.",
        "preset": {"lat": 30.8, "lon": 31.2, "radius": 40, "zoom": 9}, "query_tags": [("crop", "cotton")], "fallback_tags": [("landuse", "farmland")]},
    "Indian Cotton Heritage": {"color": "#ff6347", "icon": "leaf", "desc": "Cotton cultivation across India's textile heritage.",
        "preset": {"lat": 22.3, "lon": 72.6, "radius": 50, "zoom": 8}, "query_tags": [("crop", "cotton")], "fallback_tags": [("landuse", "farmland")]},
    "Cotton Museum Sites": {"color": "#9370db", "icon": "museum", "desc": "Museums dedicated to cotton and textile history.",
        "preset": {"lat": 33.5, "lon": -90.9, "radius": 50, "zoom": 8}, "query_tags": [("tourism", "museum")], "fallback_tags": [("tourism", "attraction")]},
    "Silk Road Textile Heritage": {"color": "#dc143c", "icon": "road", "desc": "Ancient textile routes and weaving traditions.",
        "preset": {"lat": 41.7, "lon": 86.1, "radius": 60, "zoom": 7}, "query_tags": [("historic", "silk_road"), ("craft", "weaver")], "fallback_tags": [("craft", "weaver")]},
    "Organic Cotton Farms": {"color": "#32cd32", "icon": "leaf", "desc": "Certified organic cotton farming operations.",
        "preset": {"lat": 33.5, "lon": -90.9, "radius": 50, "zoom": 8}, "query_tags": [("crop", "cotton"), ("organic", "yes")], "fallback_tags": [("crop", "cotton")]},
    "GMO Cotton Fields": {"color": "#ff1493", "icon": "flask", "desc": "Genetically modified cotton cultivation areas.",
        "preset": {"lat": 32.7, "lon": -96.8, "radius": 60, "zoom": 8}, "query_tags": [("crop", "cotton"), ("gmo", "yes")], "fallback_tags": [("crop", "cotton")]},
}

PRESETS = {
    "Custom": None,
    "Mississippi Delta, USA": {"lat": 33.5, "lon": -90.9, "radius": 50},
    "Texas Cotton Belt, USA": {"lat": 32.7, "lon": -96.8, "radius": 60},
    "Alabama, USA": {"lat": 32.4, "lon": -86.9, "radius": 50},
    "Georgia, USA": {"lat": 32.8, "lon": -83.6, "radius": 50},
    "Nile Delta, Egypt": {"lat": 30.8, "lon": 31.2, "radius": 40},
    "Gujarat, India": {"lat": 22.3, "lon": 72.6, "radius": 50},
    "Punjab, Pakistan": {"lat": 30.4, "lon": 73.1, "radius": 50},
    "Xinjiang, China": {"lat": 41.7, "lon": 86.1, "radius": 60},
    "Uzbekistan": {"lat": 40.1, "lon": 65.4, "radius": 60},
    "Mato Grosso, Brazil": {"lat": -13.0, "lon": -55.9, "radius": 50},
    "Queensland, Australia": {"lat": -27.5, "lon": 149.8, "radius": 50},
    "Adana, Turkey": {"lat": 37.9, "lon": 35.3, "radius": 40},
    "Gezira, Sudan": {"lat": 15.6, "lon": 32.5, "radius": 50},
    "Aleppo, Syria": {"lat": 36.2, "lon": 37.2, "radius": 40},
    "Sikasso, Mali": {"lat": 12.7, "lon": -8.0, "radius": 50},
}


@st.cache_data(ttl=3600)
def _search_cotton(lat: float, lon: float, radius_km: float,
                   mode: str) -> dict:
    """Query Overpass API for cotton and textile heritage features."""
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
            "historic": tags.get("historic", ""),
            "organic": tags.get("organic", ""),
        })
    return features


def _popup(f: dict, accent: str) -> str:
    """Dark-themed popup with XSS escaping."""
    name = html_module.escape(str(f["name"]))
    desc = html_module.escape(str(f.get("description", ""))[:120])
    crop = html_module.escape(str(f.get("crop", "")))
    hist = html_module.escape(str(f.get("historic", "")))
    org = html_module.escape(str(f.get("organic", "")))
    lines = f"<b style='color:{accent};'>{name}</b><br>"
    if desc:
        lines += f"<span style='color:{_TEXT2};font-size:0.8em;'>{desc}</span><br>"
    if crop:
        lines += f"<span style='color:{_TEXT2};'>Crop:</span> {crop}<br>"
    if hist:
        lines += f"<span style='color:{_TEXT2};'>Historic:</span> {hist}<br>"
    if org:
        lines += f"<span style='color:{_TEXT2};'>Organic:</span> {org}<br>"
    lines += f"<span style='color:#5a6580;font-size:0.75em;'>{f['lat']:.4f}, {f['lon']:.4f}</span>"
    return (f"<div style='min-width:200px;background:{_CARD};color:{_TEXT};"
            f"padding:8px;border-radius:8px;border:1px solid {accent};'>{lines}</div>")


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


def render_cotton_maps_tab():
    """Render the World Cotton & Textile Heritage Explorer tab."""

    header_html = (
        '<div class="tab-header amber">'
        '<h4>🧵 World Cotton & Textile Heritage Explorer</h4>'
        '<p>Discover cotton fields, textile mills, gin houses & fabric heritage worldwide</p></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Mode selection
    mode = st.selectbox("Exploration Mode", MAP_MODES, key="cotton_mode")
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
                              max_value=90.0, key="cotton_lat")
    with c2:
        lon = st.number_input("Longitude", value=cfg["preset"]["lon"],
                              format="%.4f", min_value=-180.0,
                              max_value=180.0, key="cotton_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 150,
                           cfg["preset"]["radius"], key="cotton_rad")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()),
                          key="cotton_preset")
    if preset != "Custom" and PRESETS[preset]:
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Cotton Heritage", key="cotton_go", type="primary",
                 use_container_width=True):
        st.session_state.cotton_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "cotton_params" not in st.session_state:
        st.info("Choose a mode and location, then click Explore Cotton Heritage.")
        return

    cp = st.session_state.cotton_params

    # Fetch data
    with st.spinner(f"Searching {cp['mode']} via OpenStreetMap..."):
        data = _search_cotton(cp["lat"], cp["lon"], cp["radius"], cp["mode"])
        features = _extract_features(data, cp["mode"])

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
    cols[2].metric("Search Radius", f"{cp['radius']} km")

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
        "Historic": f.get("historic", ""),
        "Organic": f.get("organic", ""),
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
        f"Download {len(rows)} Cotton Heritage Sites (CSV)",
        data=buf.getvalue(),
        file_name=f"cotton_{cp['mode'].lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="cotton_dl",
    )
