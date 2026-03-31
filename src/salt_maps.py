"""
World Salt & Mining Heritage Explorer module for TerraScout AI.
Uses Overpass API to discover salt mines, evaporation ponds, salt trade routes,
and mining heritage features from OpenStreetMap.
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
    "Historic Salt Mines": {
        "query": '["resource"="salt"]["historic"]["historic"!="no"]',
        "fallback": '["name"~"[Ss]alt [Mm]ine|[Ss]alina|[Ss]alzbergwerk"]["historic"]',
        "color": "#f59e0b", "icon": "industry",
    },
    "Salt Evaporation Ponds": {
        "query": '["landuse"="salt_pond"]',
        "fallback": '["name"~"[Ss]alt [Pp]ond|[Ss]altern|[Ss]aline|[Mm]arais [Ss]alant"]',
        "color": "#38bdf8", "icon": "tint",
    },
    "Salt Trade Routes": {
        "query": '["name"~"[Ss]alt [Rr]oad|[Ss]alt [Rr]oute|[Vv]ia [Ss]alaria|[Ss]alzstra"]',
        "fallback": '["historic"="road"]["name"~"[Ss]alt|[Ss]al"]',
        "color": "#a855f7", "icon": "road",
    },
    "Himalayan Salt Heritage": {
        "query": '["man_made"="mineshaft"]["name"~"[Ss]alt|[Kk]hewra|[Ss]enda"]',
        "fallback": '["name"~"[Ss]alt [Rr]ange|[Kk]hewra"]',
        "color": "#ec4899", "icon": "mountain",
    },
    "European Salt Heritage": {
        "query": '["historic"]["name"~"[Ss]alz|[Ss]aline|[Ss]alina|[Ss]alt"]',
        "fallback": '["name"~"[Ww]ieliczka|[Hh]allstatt|[Ss]alzburg|[Bb]ochnia"]',
        "color": "#06b6d4", "icon": "landmark",
    },
    "Mediterranean Salt Pans": {
        "query": '["landuse"="salt_pond"]',
        "fallback": '["name"~"[Ss]aline|[Ss]alinas|[Ss]alt [Pp]an"]',
        "color": "#10b981", "icon": "water",
    },
    "African Salt Caravans": {
        "query": '["name"~"[Ss]alt|[Ss]el|[Tt]aoudenni|[Bb]ilma"]',
        "fallback": '["historic"]["name"~"[Cc]aravan|[Ss]alt"]',
        "color": "#f97316", "icon": "route",
    },
    "South American Salt Flats": {
        "query": '["natural"="salt_flat"]',
        "fallback": '["name"~"[Ss]alar|[Ss]alinas|[Ss]alt [Ff]lat"]',
        "color": "#e879f9", "icon": "globe",
    },
    "Salt Museums & Heritage": {
        "query": '["tourism"="museum"]["name"~"[Ss]alt|[Ss]alz|[Ss]aline|[Mm]ine"]',
        "fallback": '["name"~"[Ss]alt [Mm]useum|[Mm]useo [Ss]ale|[Ss]alzmuseum"]',
        "color": "#ef4444", "icon": "museum",
    },
    "World Salt Production Map": {
        "query": '["resource"="salt"]',
        "fallback": '["landuse"="salt_pond"]',
        "color": "#8b5cf6", "icon": "globe",
    },
}

# ═══════════════════════════════════════════
# PRESET LOCATIONS
# ═══════════════════════════════════════════
PRESETS = {
    "Custom": None,
    "Wieliczka Salt Mine, Poland": {"lat": 49.9833, "lon": 20.0556, "radius": 5},
    "Hallstatt, Austria": {"lat": 47.5622, "lon": 13.6493, "radius": 10},
    "Khewra Salt Mine, Pakistan": {"lat": 32.6490, "lon": 73.0089, "radius": 15},
    "Salar de Uyuni, Bolivia": {"lat": -20.1338, "lon": -67.4891, "radius": 50},
    "Salzburg, Austria": {"lat": 47.8095, "lon": 13.0550, "radius": 10},
    "Guerande Salt Pans, France": {"lat": 47.2900, "lon": -2.4300, "radius": 10},
    "Trapani Salt Pans, Sicily": {"lat": 37.9800, "lon": 12.4900, "radius": 10},
    "Maras Salt Terraces, Peru": {"lat": -13.3647, "lon": -72.1531, "radius": 10},
    "Dead Sea, Israel/Jordan": {"lat": 31.5000, "lon": 35.4700, "radius": 30},
    "Tuz Golu, Turkey": {"lat": 38.7500, "lon": 33.3500, "radius": 30},
    "Sambhar Lake, India": {"lat": 26.9200, "lon": 75.0800, "radius": 15},
    "Taoudenni, Mali": {"lat": 22.6800, "lon": -3.9800, "radius": 30},
    "Turda Salt Mine, Romania": {"lat": 46.5885, "lon": 23.7858, "radius": 5},
    "Salinas Grandes, Argentina": {"lat": -23.6200, "lon": -65.8900, "radius": 30},
    "Danakil Depression, Ethiopia": {"lat": 14.2417, "lon": 40.2950, "radius": 30},
}


@st.cache_data(ttl=3600)
def _search_salt(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for salt/mining features."""
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
            "type": tags.get("historic", tags.get("landuse", tags.get("natural", ""))),
            "wikipedia": tags.get("wikipedia", ""),
            "description": tags.get("description", tags.get("note", "")),
        })
    return features


def render_salt_maps_tab():
    """Main render function for the World Salt & Mining Heritage tab."""

    # ── Header ──
    header_html = '<div class="tab-header amber"><h4>\U0001f9c2 World Salt & Mining Heritage Explorer</h4><p>Discover salt mines, evaporation ponds & salt trade routes worldwide</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="salt_mode")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=47.5622, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="salt_lat")
    with c2:
        lon = st.number_input("Longitude", value=13.6493, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="salt_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, 15, key="salt_radius")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()), key="salt_preset")
    if preset != "Custom" and PRESETS.get(preset):
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Salt Heritage", key="salt_search", type="primary",
                 use_container_width=True):
        st.session_state.salt_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "salt_params" not in st.session_state:
        st.info("Select a mode and location, then click Explore to discover salt heritage sites.")
        return

    sp = st.session_state.salt_params
    mode_info = MODES[sp["mode"]]

    # ── Query ──
    with st.spinner(f"Searching {sp['mode']}..."):
        data = _search_salt(sp["lat"], sp["lon"], sp["radius"], sp["mode"])
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
    st.markdown("#### Salt Heritage Map")

    m = folium.Map(location=[sp["lat"], sp["lon"]], zoom_start=9, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    folium.Circle(
        location=[sp["lat"], sp["lon"]],
        radius=sp["radius"] * 1000,
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
        f"Download {len(rows)} Salt Heritage Sites (CSV)",
        data=buf.getvalue(), file_name="salt_heritage_sites.csv",
        mime="text/csv", key="salt_download",
    )
