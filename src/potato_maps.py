# -*- coding: utf-8 -*-
"""
World Potato & Tuber Heritage Explorer module for TerraScout AI.
Maps potato fields, Andean heritage, Irish culture, tuber diversity,
and research centers using the Overpass API.
"""

import io
import re
import html as html_module
from urllib.parse import quote as url_quote
import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
from streamlit.components.v1 import html as st_html
from src.overpass_client import query_overpass

# ═══════════════════════════════════════════
# MODE DEFINITIONS
# ═══════════════════════════════════════════
MODES = {
    "Modern Potato Fields": {
        "query": '["landuse"="farmland"]["crop"="potato"]',
        "fallback": '["name"~"[Pp]otato.*[Ff]ield|[Pp]atata|[Kk]artoffel"]',
        "color": "#10b981", "icon": "leaf",
    },
    "Andean Potato Heritage": {
        "query": '["crop"="potato"]',
        "fallback": '["name"~"[Pp]apa|[Cc]huño|[Pp]otato.*[Hh]eritage"]',
        "color": "#f59e0b", "icon": "mountain",
    },
    "Irish Potato Heritage": {
        "query": '["crop"="potato"]',
        "fallback": '["name"~"[Pp]rátaí|[Pp]otato.*[Ii]rish"]',
        "color": "#10b981", "icon": "tree",
    },
    "Sweet Potato Fields": {
        "query": '["crop"="sweet_potato"]',
        "fallback": '["name"~"[Ss]weet.*[Pp]otato|[Bb]atata|[Cc]amote"]',
        "color": "#f97316", "icon": "leaf",
    },
    "Potato Museum Sites": {
        "query": '["tourism"="museum"]["name"~"[Pp]otato|[Pp]atata"]',
        "fallback": '["name"~"[Pp]otato.*[Mm]useum|[Mm]useo.*[Pp]apa"]',
        "color": "#06b6d4", "icon": "museum",
    },
    "Potato Research Centers": {
        "query": '["amenity"="research_institute"]["name"~"[Pp]otato.*[Rr]esearch|CIP"]',
        "fallback": '["name"~"CIP|[Pp]otato.*[Ii]nstitute|[Pp]apa.*[Ii]nvestigación"]',
        "color": "#8b5cf6", "icon": "university",
    },
    "Historic Potato Famines": {
        "query": '["historic"="famine"]["name"~"[Pp]otato.*[Ff]amine"]',
        "fallback": '["name"~"[Gg]reat.*[Hh]unger|[Gg]orta.*[Mm]hór|[Ff]amine.*[Mm]emorial"]',
        "color": "#ef4444", "icon": "memorial",
    },
    "Yam & Taro Heritage": {
        "query": '["crop"="yam"]',
        "fallback": '["crop"="taro"]',
        "color": "#a855f7", "icon": "leaf",
    },
    "Cassava & Manioc Fields": {
        "query": '["crop"="cassava"]',
        "fallback": '["crop"="manioc"]',
        "color": "#ec4899", "icon": "leaf",
    },
    "Heritage Potato Varieties": {
        "query": '["crop"="potato"]["heritage"="yes"]',
        "fallback": '["name"~"[Hh]eirloom.*[Pp]otato|[Pp]atrimonio.*[Pp]apa"]',
        "color": "#14b8a6", "icon": "leaf",
    },
}

# ═══════════════════════════════════════════
# PRESET LOCATIONS
# ═══════════════════════════════════════════
PRESETS = {
    "Custom": None,
    "Sacred Valley, Peru": {"lat": -13.3, "lon": -71.9, "radius": 30},
    "Lake Titicaca, Peru": {"lat": -15.8, "lon": -69.7, "radius": 40},
    "Chiloé Island, Chile": {"lat": -42.6, "lon": -73.9, "radius": 25},
    "Idaho Potato Belt, USA": {"lat": 43.6, "lon": -116.2, "radius": 50},
    "Ireland": {"lat": 53.4, "lon": -8.2, "radius": 60},
    "Prince Edward Island, Canada": {"lat": 46.5, "lon": -63.4, "radius": 30},
    "Netherlands": {"lat": 52.5, "lon": 5.5, "radius": 40},
    "Poland": {"lat": 52.2, "lon": 21.0, "radius": 50},
    "Belarus": {"lat": 53.9, "lon": 27.6, "radius": 50},
    "India": {"lat": 28.6, "lon": 77.2, "radius": 40},
    "China Inner Mongolia": {"lat": 40.8, "lon": 111.7, "radius": 50},
    "Germany": {"lat": 52.5, "lon": 13.4, "radius": 40},
    "Belgium": {"lat": 50.5, "lon": 4.5, "radius": 30},
    "Scotland": {"lat": 56.5, "lon": -4.0, "radius": 40},
    "Peru Puno": {"lat": -15.8, "lon": -70.0, "radius": 35},
}


@st.cache_data(ttl=3600)
def _search_potatoes(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for potato-related features."""
    mode_info = MODES.get(mode)
    if not mode_info:
        return {"elements": []}
    radius_m = int(radius_km * 1000)
    q_filter = mode_info["query"]
    fb_filter = mode_info["fallback"]
    query = f"""
[out:json][timeout:60];
(
  node{q_filter}(around:{radius_m},{lat},{lon});
  way{q_filter}(around:{radius_m},{lat},{lon});
  node{fb_filter}(around:{radius_m},{lat},{lon});
  way{fb_filter}(around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown") if result else "No response"
        st.error(f"Overpass query failed: {err}. Try a smaller radius or retry later.")
        return {"elements": []}
    return result


def _extract(data: dict, color: str) -> list:
    """Extract features with coordinates from Overpass response."""
    elements = data.get("elements", [])
    nodes = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            nodes[el["id"]] = (el["lat"], el["lon"])

    features, seen = [], set()
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat, lon = None, None
        if el["type"] == "node" and "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif el["type"] == "way":
            coords = [nodes[n] for n in el.get("nodes", []) if n in nodes]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)
        if lat is None:
            continue
        oid = el.get("id")
        if oid in seen:
            continue
        seen.add(oid)
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        features.append({
            "name": name, "lat": lat, "lon": lon, "color": color,
            "osm_id": oid,
            "type": tags.get("crop", tags.get("tourism", tags.get("amenity", tags.get("landuse", "")))),
            "wikipedia": tags.get("wikipedia", ""),
            "description": tags.get("description", tags.get("note", "")),
        })
    return features


def render_potato_maps_tab():
    """Main render function for the World Potato & Tuber Heritage tab."""

    # ── Header ──
    header_html = '<div class="tab-header emerald"><h4>🥔 World Potato & Tuber Heritage Explorer</h4><p>Discover potato fields, Andean heritage, Irish potato culture & tuber diversity</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="potato_mode")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=-13.3, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="potato_lat")
    with c2:
        lon = st.number_input("Longitude", value=-71.9, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="potato_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, 30, key="potato_radius")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()), key="potato_preset")
    if preset != "Custom" and PRESETS.get(preset):
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Potato Heritage", key="potato_search", type="primary",
                 use_container_width=True):
        st.session_state.potato_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "potato_params" not in st.session_state:
        st.info("Select a mode and location, then click Explore to discover potato heritage sites.")
        return

    op = st.session_state.potato_params
    mode_info = MODES[op["mode"]]

    # ── Query ──
    with st.spinner(f"Searching {op['mode']}..."):
        data = _search_potatoes(op["lat"], op["lon"], op["radius"], op["mode"])
        features = _extract(data, mode_info["color"])

    if not features:
        st.warning("No features found. Try a larger radius or different mode.")
        return

    # ── Stats ──
    st.markdown("---")
    st.markdown("#### Discovery Overview")
    type_counts = {}
    for f in features:
        t = f["type"] or "other"
        type_counts[t] = type_counts.get(t, 0) + 1

    cols = st.columns(min(len(type_counts) + 1, 5))
    cols[0].metric("Total Sites", len(features))
    for i, (t, cnt) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(cols):
            cols[i + 1].metric(html_module.escape(t[:18]), cnt)

    # ── Map ──
    st.markdown("---")
    st.markdown("#### Potato Heritage Map")

    m = folium.Map(location=[op["lat"], op["lon"]], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    folium.Circle(
        location=[op["lat"], op["lon"]],
        radius=op["radius"] * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)

    for f in features:
        safe_name = html_module.escape(f["name"])
        safe_desc = html_module.escape(f["description"][:120])
        wiki = ""
        if f["wikipedia"]:
            parts = f["wikipedia"].split(":", 1)
            lang = parts[0] if len(parts) == 2 else "en"
            title = parts[1] if len(parts) == 2 else parts[0]
            # Sanitise: lang must be a valid wiki subdomain; title is URL-encoded
            if re.match(r'^[a-zA-Z\-]{2,12}$', lang):
                safe_lang = html_module.escape(lang)
                safe_title = url_quote(title, safe='')
                wiki = f'<br/><a href="https://{safe_lang}.wikipedia.org/wiki/{safe_title}" target="_blank">Wikipedia</a>'
        popup = f'<div style="max-width:200px;"><strong>{safe_name}</strong><br/><span style="font-size:0.8rem;color:#999;">{safe_desc}</span>{wiki}</div>'
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=7,
            color=f["color"], fill=True, fill_color=f["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=220),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_html(m._repr_html_(), height=500)

    # ── Data Table ──
    st.markdown("---")
    rows = [{
        "Name": f["name"], "Type": f["type"], "Latitude": f["lat"],
        "Longitude": f["lon"], "Wikipedia": f["wikipedia"],
        "Description": f["description"][:100], "OSM ID": f["osm_id"],
    } for f in features]
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ── Download ──
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(rows)} Potato Heritage Sites (CSV)",
        data=buf.getvalue(), file_name="potato_heritage_sites.csv",
        mime="text/csv", key="potato_download",
    )
