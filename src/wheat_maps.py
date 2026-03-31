# -*- coding: utf-8 -*-
"""
World Wheat & Grain Heritage Explorer module for TerraScout AI.
Maps wheat fields, ancient grains, flour mills, and breadbasket regions
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

# ═══════════════════════════════════════════
# MODE DEFINITIONS
# ═══════════════════════════════════════════
MODES = {
    "Modern Wheat Fields": {
        "query": '["landuse"="farmland"]["crop"="wheat"]',
        "fallback": '["landuse"="farmland"]["name"~"[Ww]heat"]',
        "color": "#10b981", "icon": "seedling",
    },
    "Ancient Grain Heritage": {
        "query": '["crop"="wheat"]["heritage"="yes"]',
        "fallback": '["crop"~"spelt|emmer|einkorn"]',
        "color": "#f59e0b", "icon": "history",
    },
    "Historic Flour Mills": {
        "query": '["craft"="flour_mill"]',
        "fallback": '["name"~"[Mm]ill|[Mm]olino|[Mm]oulin|[Mm]ühle"]',
        "color": "#06b6d4", "icon": "industry",
    },
    "Bread Museum Sites": {
        "query": '["tourism"="museum"]["name"~"[Bb]read|[Ff]lour|[Ww]heat"]',
        "fallback": '["name"~"[Bb]read.*[Mm]useum|[Mm]useo.*[Pp]an|[Mm]usée.*[Pp]ain"]',
        "color": "#8b5cf6", "icon": "museum",
    },
    "Durum Wheat Heritage": {
        "query": '["crop"="wheat"]["wheat:variety"="durum"]',
        "fallback": '["crop"="wheat"]["name"~"[Dd]urum"]',
        "color": "#ec4899", "icon": "wheat-awn",
    },
    "Kansas Wheat Belt": {
        "query": '["crop"="wheat"]',
        "fallback": '["landuse"="farmland"]["name"~"[Ww]heat"]',
        "color": "#f97316", "icon": "tractor",
    },
    "Ukraine Breadbasket": {
        "query": '["crop"="wheat"]',
        "fallback": '["landuse"="farmland"]',
        "color": "#14b8a6", "icon": "globe",
    },
    "Australian Wheat Belt": {
        "query": '["crop"="wheat"]',
        "fallback": '["landuse"="farmland"]["name"~"[Ww]heat"]',
        "color": "#3b82f6", "icon": "globe-oceania",
    },
    "Wheat Research Centers": {
        "query": '["amenity"="research_institute"]["name"~"[Ww]heat|[Gg]rain.*[Rr]esearch"]',
        "fallback": '["amenity"="research_institute"]["name"~"[Aa]gricult"]',
        "color": "#ef4444", "icon": "microscope",
    },
    "Organic Wheat Farms": {
        "query": '["crop"="wheat"]["organic"="yes"]',
        "fallback": '["landuse"="farmland"]["organic"="yes"]',
        "color": "#a855f7", "icon": "leaf",
    },
}

# ═══════════════════════════════════════════
# PRESET LOCATIONS
# ═══════════════════════════════════════════
PRESETS = {
    "Custom": None,
    "Kansas Wheat Belt (USA)": {"lat": 38.5, "lon": -98.4, "radius": 50},
    "Ukraine Breadbasket": {"lat": 49.0, "lon": 32.0, "radius": 60},
    "Palouse, Washington (USA)": {"lat": 46.7, "lon": -117.2, "radius": 30},
    "Canadian Prairies": {"lat": 50.4, "lon": -104.6, "radius": 60},
    "Australian Wheat Belt": {"lat": -31.9, "lon": 116.8, "radius": 60},
    "Argentina Pampas": {"lat": -37.0, "lon": -60.0, "radius": 50},
    "French Beauce": {"lat": 48.4, "lon": 1.5, "radius": 30},
    "Indian Punjab": {"lat": 30.9, "lon": 75.8, "radius": 40},
    "Pakistan Punjab": {"lat": 31.4, "lon": 73.1, "radius": 40},
    "Anatolia, Turkey": {"lat": 39.9, "lon": 32.9, "radius": 40},
    "Egypt Nile Delta": {"lat": 30.8, "lon": 31.2, "radius": 30},
    "Mesopotamia (Iraq)": {"lat": 35.5, "lon": 44.4, "radius": 40},
    "Po Valley, Italy": {"lat": 45.1, "lon": 9.5, "radius": 30},
    "Castile, Spain": {"lat": 41.7, "lon": -4.7, "radius": 40},
    "Morocco": {"lat": 33.6, "lon": -7.6, "radius": 40},
}


@st.cache_data(ttl=3600)
def _search_wheat(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for wheat-related features."""
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
            "variety": tags.get("wheat:variety", ""),
            "organic": tags.get("organic", ""),
            "heritage": tags.get("heritage", ""),
            "description": tags.get("description", tags.get("note", "")),
        })
    return features


def render_wheat_maps_tab():
    """Main render function for the World Wheat & Grain Heritage tab."""

    # ── Header ──
    header_html = '<div class="tab-header emerald"><h4>🌾 World Wheat & Grain Heritage Explorer</h4><p>Discover wheat fields, ancient grains, flour mills & breadbasket regions worldwide</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="wheat_mode")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=38.5, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="wheat_lat")
    with c2:
        lon = st.number_input("Longitude", value=-98.4, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="wheat_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, 50, key="wheat_radius")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()), key="wheat_preset")
    if preset != "Custom" and PRESETS.get(preset):
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Wheat Heritage", key="wheat_search", type="primary",
                 use_container_width=True):
        st.session_state.wheat_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "wheat_params" not in st.session_state:
        st.info("Select a mode and location, then click Explore to discover wheat heritage sites.")
        return

    wp = st.session_state.wheat_params
    mode_info = MODES[wp["mode"]]

    # ── Query ──
    with st.spinner(f"Searching {wp['mode']}..."):
        data = _search_wheat(wp["lat"], wp["lon"], wp["radius"], wp["mode"])
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
    st.markdown("#### Wheat Heritage Map")

    m = folium.Map(location=[wp["lat"], wp["lon"]], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    folium.Circle(
        location=[wp["lat"], wp["lon"]],
        radius=wp["radius"] * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)

    for f in features:
        safe_name = html_module.escape(f["name"])
        safe_desc = html_module.escape(f["description"][:120])
        variety = html_module.escape(f["variety"]) if f["variety"] else ""
        organic = "Organic" if f["organic"] == "yes" else ""
        heritage = "Heritage" if f["heritage"] == "yes" else ""

        extra = "<br/>".join(filter(None, [variety, organic, heritage]))
        if extra:
            extra = f"<br/><span style='font-size:0.75rem;color:#10b981;'>{extra}</span>"

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
        "Name": f["name"], "Type": f["type"], "Variety": f["variety"],
        "Organic": f["organic"], "Heritage": f["heritage"],
        "Latitude": f["lat"], "Longitude": f["lon"],
        "Description": f["description"][:100], "OSM ID": f["osm_id"],
    } for f in features]
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ── Download ──
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(rows)} Wheat Heritage Sites (CSV)",
        data=buf.getvalue(), file_name="wheat_heritage_sites.csv",
        mime="text/csv", key="wheat_download",
    )
