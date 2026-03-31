# -*- coding: utf-8 -*-
"""
World Soybean & Legume Heritage Explorer module for TerraScout AI.
Uses Overpass API to discover soy fields, tofu heritage, Asian legumes,
and global protein crop features from OpenStreetMap.
"""

import io
import html as html_module
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
from src.overpass_client import query_overpass

# ═══════════════════════════════════════════
# MODE DEFINITIONS
# ═══════════════════════════════════════════
MODES = {
    "Modern Soybean Fields": {
        "query": '["landuse"="farmland"]["crop"="soy"]',
        "fallback": '["crop"="soya"]',
        "color": "#10b981", "icon": "leaf",
    },
    "Tofu & Soy Sauce Heritage": {
        "query": '["craft"="tofu_maker"]',
        "fallback": '["name"~"[Tt]ofu|[Ss]hoyu|[Ss]oy [Ss]auce"]',
        "color": "#f59e0b", "icon": "flask",
    },
    "Asian Soybean Heritage": {
        "query": '["crop"="soy"]',
        "fallback": '["crop"="soya"]',
        "color": "#06b6d4", "icon": "tree",
    },
    "Brazilian Soy Belt": {
        "query": '["crop"="soy"]',
        "fallback": '["landuse"="farmland"]',
        "color": "#3b82f6", "icon": "globe",
    },
    "Argentine Soy Region": {
        "query": '["crop"="soy"]',
        "fallback": '["landuse"="farmland"]',
        "color": "#8b5cf6", "icon": "leaf",
    },
    "GMO Soybean Fields": {
        "query": '["crop"="soy"]["gmo"="yes"]',
        "fallback": '["crop"="soy"]',
        "color": "#ec4899", "icon": "dna",
    },
    "Organic Soy Farms": {
        "query": '["crop"="soy"]["organic"="yes"]',
        "fallback": '["crop"="soy"]',
        "color": "#14b8a6", "icon": "leaf",
    },
    "Edamame & Green Soy": {
        "query": '["crop"="edamame"]',
        "fallback": '["crop"="soy"]',
        "color": "#22c55e", "icon": "seedling",
    },
    "Lentil & Legume Heritage": {
        "query": '["crop"="lentils"]',
        "fallback": '["crop"="chickpeas"]',
        "color": "#f97316", "icon": "pagelines",
    },
    "Bean Museum Sites": {
        "query": '["tourism"="museum"]["name"~"[Bb]ean|[Ss]oy|[Ll]egume"]',
        "fallback": '["tourism"="museum"]',
        "color": "#ef4444", "icon": "museum",
    },
}

# ═══════════════════════════════════════════
# PRESET LOCATIONS
# ═══════════════════════════════════════════
PRESETS = {
    "Custom": None,
    "Mato Grosso, Brazil": {"lat": -13.0, "lon": -55.9, "radius": 60},
    "Rio Grande do Sul, Brazil": {"lat": -29.7, "lon": -53.1, "radius": 50},
    "Argentina Pampas": {"lat": -33.0, "lon": -61.0, "radius": 60},
    "Iowa Soy Belt, USA": {"lat": 42.0, "lon": -93.5, "radius": 50},
    "Illinois, USA": {"lat": 40.1, "lon": -89.4, "radius": 50},
    "Heilongjiang, China": {"lat": 47.4, "lon": 127.8, "radius": 60},
    "Jilin, China": {"lat": 43.9, "lon": 125.3, "radius": 50},
    "Parana, Brazil": {"lat": -24.5, "lon": -51.4, "radius": 50},
    "Uruguay": {"lat": -33.0, "lon": -56.0, "radius": 50},
    "Paraguay": {"lat": -23.4, "lon": -58.4, "radius": 50},
    "India Madhya Pradesh": {"lat": 23.3, "lon": 77.4, "radius": 40},
    "Canada Ontario": {"lat": 43.7, "lon": -79.4, "radius": 50},
    "Ukraine": {"lat": 48.4, "lon": 35.0, "radius": 40},
    "Japan Tohoku": {"lat": 38.3, "lon": 140.9, "radius": 30},
    "Kyoto Tofu Heritage": {"lat": 35.0, "lon": 135.8, "radius": 20},
}


@st.cache_data(ttl=3600)
def _search_soy(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for soybean-related features."""
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
            "type": tags.get("crop", tags.get("craft", tags.get("tourism", tags.get("landuse", "")))),
            "organic": tags.get("organic", ""),
            "gmo": tags.get("gmo", ""),
            "description": tags.get("description", tags.get("note", "")),
        })
    return features


def render_soy_maps_tab():
    """Main render function for the World Soybean & Legume Heritage tab."""

    # ── Header ──
    header_html = '<div class="tab-header emerald"><h4>🫘 World Soybean & Legume Heritage Explorer</h4><p>Discover soy fields, tofu heritage, Asian legumes & global protein crops</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="soy_mode")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=-13.0, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="soy_lat")
    with c2:
        lon = st.number_input("Longitude", value=-55.9, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="soy_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, 60, key="soy_radius")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()), key="soy_preset")
    if preset != "Custom" and PRESETS.get(preset):
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Soy Heritage", key="soy_search", type="primary",
                 use_container_width=True):
        st.session_state.soy_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "soy_params" not in st.session_state:
        st.info("Select a mode and location, then click Explore to discover soybean & legume heritage sites.")
        return

    op = st.session_state.soy_params
    mode_info = MODES[op["mode"]]

    # ── Query ──
    with st.spinner(f"Searching {op['mode']}..."):
        data = _search_soy(op["lat"], op["lon"], op["radius"], op["mode"])
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
    st.markdown("#### Soybean & Legume Heritage Map")

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
        organic_str = html_module.escape(f["organic"])
        gmo_str = html_module.escape(f["gmo"])
        extra = ""
        if organic_str:
            extra += f'<br/><span style="color:#10b981;">Organic: {organic_str}</span>'
        if gmo_str:
            extra += f'<br/><span style="color:#ec4899;">GMO: {gmo_str}</span>'
        popup = f'<div style="max-width:200px;"><strong>{safe_name}</strong><br/><span style="font-size:0.8rem;color:#999;">{safe_desc}</span>{extra}</div>'
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
        "Longitude": f["lon"], "Organic": f["organic"], "GMO": f["gmo"],
        "Description": f["description"][:100], "OSM ID": f["osm_id"],
    } for f in features]
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ── Download ──
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(rows)} Soybean & Legume Heritage Sites (CSV)",
        data=buf.getvalue(), file_name="soy_legume_heritage_sites.csv",
        mime="text/csv", key="soy_download",
    )
