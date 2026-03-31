"""
World Rice & Paddy Heritage Explorer module for TerraScout AI.
Uses Overpass API to discover rice paddies, terraced fields, sake breweries,
rice mills, heritage sites, and rice culture features worldwide.
"""

import io
import re
import html as html_module
from urllib.parse import quote as url_quote
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
    "Asian Rice Paddies": {
        "query": '["landuse"="farmland"]["crop"="rice"]',
        "fallback": '["name"~"[Rr]ice [Pp]addy|[Rr]ice [Ff]ield|[Ss]awah|[Pp]adi"]',
        "color": "#10b981", "icon": "leaf",
    },
    "Terraced Rice Fields": {
        "query": '["landuse"="farmland"]["crop"="rice"]["terrace"="yes"]',
        "fallback": '["name"~"[Rr]ice [Tt]errace|[Tt]erraced|[Bb]anaue|[Yy]uanyang"]',
        "color": "#06b6d4", "icon": "mountain",
    },
    "Historic Rice Mills": {
        "query": '["craft"="rice_mill"]',
        "fallback": '["name"~"[Rr]ice [Mm]ill|[Rr]iseria|[Mm]olino [Aa]rroz|[Mm]oulin [Rr]iz"]',
        "color": "#f59e0b", "icon": "industry",
    },
    "Sake Brewery Heritage": {
        "query": '["craft"="brewery"]["product"="sake"]',
        "fallback": '["name"~"[Ss]ake|[Ss]aké|酒造|[Bb]rewery"]',
        "color": "#8b5cf6", "icon": "flask",
    },
    "Rice Museum & Heritage": {
        "query": '["tourism"="museum"]["name"~"[Rr]ice|[Aa]rroz|[Rr]iso|[Rr]iz"]',
        "fallback": '["name"~"[Rr]ice [Mm]useum|[Mm]useo [Aa]rroz|[Mm]usée [Rr]iz"]',
        "color": "#ec4899", "icon": "museum",
    },
    "Basmati Rice Heritage": {
        "query": '["crop"="rice"]["rice:variety"="basmati"]',
        "fallback": '["name"~"[Bb]asmati"]',
        "color": "#f97316", "icon": "pagelines",
    },
    "Japanese Rice Heritage": {
        "query": '["crop"="rice"]',
        "fallback": '["name"~"[Rr]ice|田|[Tt]anbo"]',
        "color": "#ef4444", "icon": "leaf",
    },
    "Italian Risotto Heritage": {
        "query": '["crop"="rice"]',
        "fallback": '["name"~"[Rr]isaia|[Rr]iseria|[Rr]iso"]',
        "color": "#3b82f6", "icon": "flask",
    },
    "Wild Rice Heritage": {
        "query": '["crop"="rice"]["rice:variety"="wild"]',
        "fallback": '["name"~"[Ww]ild [Rr]ice|[Mm]anomin"]',
        "color": "#14b8a6", "icon": "tree",
    },
    "Rice Research Centers": {
        "query": '["amenity"="research_institute"]["name"~"[Rr]ice [Rr]esearch"]',
        "fallback": '["name"~"[Rr]ice [Rr]esearch|[Rr]ice [Ii]nstitute|IRRI"]',
        "color": "#a855f7", "icon": "university",
    },
}

# ═══════════════════════════════════════════
# PRESET LOCATIONS
# ═══════════════════════════════════════════
PRESETS = {
    "Custom": None,
    "Banaue Rice Terraces, Philippines": {"lat": 17.0, "lon": 121.1, "radius": 20},
    "Yuanyang Terraces, China": {"lat": 23.1, "lon": 102.7, "radius": 30},
    "Jatiluwih Terraces, Bali": {"lat": -8.4, "lon": 115.1, "radius": 15},
    "Mekong Delta, Vietnam": {"lat": 10.0, "lon": 105.8, "radius": 40},
    "Sapa Terraces, Vietnam": {"lat": 22.3, "lon": 103.8, "radius": 25},
    "Po Valley, Italy": {"lat": 45.1, "lon": 9.5, "radius": 30},
    "Sacramento Valley, USA": {"lat": 38.9, "lon": -121.9, "radius": 40},
    "Ebro Delta, Spain": {"lat": 40.7, "lon": 0.7, "radius": 25},
    "Kerala Kuttanad, India": {"lat": 9.4, "lon": 76.5, "radius": 30},
    "Niigata Rice Region, Japan": {"lat": 37.9, "lon": 139.0, "radius": 30},
    "Bali Rice Culture (UNESCO)": {"lat": -8.5, "lon": 115.3, "radius": 25},
    "Camargue, France": {"lat": 43.5, "lon": 4.6, "radius": 25},
    "Arkansas Rice Belt, USA": {"lat": 34.7, "lon": -91.9, "radius": 40},
    "Thailand Central Plains": {"lat": 14.0, "lon": 100.5, "radius": 50},
    "Bangladesh Rice Plains": {"lat": 23.8, "lon": 90.4, "radius": 50},
}


@st.cache_data(ttl=3600)
def _search_rice(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for rice-related features."""
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
            "variety": tags.get("rice:variety", ""),
            "wikipedia": tags.get("wikipedia", ""),
            "description": tags.get("description", tags.get("note", "")),
        })
    return features


def render_rice_maps_tab():
    """Main render function for the World Rice & Paddy Heritage tab."""

    # ── Header ──
    header_html = '<div class="tab-header emerald"><h4>🌾 World Rice & Paddy Heritage Explorer</h4><p>Discover rice paddies, terraces, heritage mills, sake breweries & rice culture worldwide</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="rice_mode")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=17.0, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="rice_lat")
    with c2:
        lon = st.number_input("Longitude", value=121.1, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="rice_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, 20, key="rice_radius")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()), key="rice_preset")
    if preset != "Custom" and PRESETS.get(preset):
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Rice Heritage", key="rice_search", type="primary",
                 use_container_width=True):
        st.session_state.rice_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "rice_params" not in st.session_state:
        st.info("Select a mode and location, then click Explore to discover rice heritage sites.")
        return

    op = st.session_state.rice_params
    mode_info = MODES[op["mode"]]

    # ── Query ──
    with st.spinner(f"Searching {op['mode']}..."):
        data = _search_rice(op["lat"], op["lon"], op["radius"], op["mode"])
        features = _extract(data, mode_info["color"])

    if not features:
        st.warning("No features found. Try a larger radius or different mode.")
        return

    # ── Stats ──
    st.markdown("---")
    st.markdown("#### Discovery Overview")
    type_counts = {}
    named_count = sum(1 for f in features if f["name"] != "Unnamed")
    for f in features:
        t = f["type"] or "other"
        type_counts[t] = type_counts.get(t, 0) + 1

    cols = st.columns(3)
    cols[0].metric("Total Sites", len(features))
    cols[1].metric("Named Sites", named_count)
    cols[2].metric("Types Found", len(type_counts))

    # ── Map ──
    st.markdown("---")
    st.markdown("#### Rice Heritage Map")

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
        variety_str = f" ({html_module.escape(f['variety'])})" if f["variety"] else ""
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
        popup = f'<div style="max-width:200px;"><strong>{safe_name}{variety_str}</strong><br/><span style="font-size:0.8rem;color:#999;">{safe_desc}</span>{wiki}</div>'
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
        "Latitude": f["lat"], "Longitude": f["lon"],
        "Wikipedia": f["wikipedia"], "Description": f["description"][:100],
        "OSM ID": f["osm_id"],
    } for f in features]
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ── Download ──
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(rows)} Rice Heritage Sites (CSV)",
        data=buf.getvalue(), file_name="rice_heritage_sites.csv",
        mime="text/csv", key="rice_download",
    )
