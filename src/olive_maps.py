"""
World Olive & Oil Heritage Explorer module for TerraScout AI.
Uses Overpass API to discover olive groves, oil mills, olive museums,
and Mediterranean olive heritage features from OpenStreetMap.
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
    "Mediterranean Olive Groves": {
        "query": '["landuse"="orchard"]["crop"="olive"]',
        "fallback": '["name"~"[Oo]live [Gg]rove|[Oo]liveto|[Oo]livar|[Ee]laiodendro"]',
        "color": "#10b981", "icon": "tree",
    },
    "Historic Oil Mills": {
        "query": '["craft"="oil_mill"]',
        "fallback": '["name"~"[Oo]il [Mm]ill|[Ff]rantoio|[Aa]lmazara|[Ee]laiotrivio|[Mm]oulin.*[Hh]uile"]',
        "color": "#f59e0b", "icon": "industry",
    },
    "Olive Oil Museums": {
        "query": '["tourism"="museum"]["name"~"[Oo]liv|[Oo]lio|[Aa]ceite|[Ee]laio"]',
        "fallback": '["name"~"[Oo]live.*[Mm]useum|[Mm]useo.*[Oo]lio|[Mm]usee.*[Oo]liv"]',
        "color": "#06b6d4", "icon": "museum",
    },
    "Greek Olive Heritage": {
        "query": '["crop"="olive"]',
        "fallback": '["name"~"[Ee]lia|[Ee]laio|[Oo]liv"]',
        "color": "#3b82f6", "icon": "leaf",
    },
    "Italian Oil Traditions": {
        "query": '["crop"="olive"]',
        "fallback": '["name"~"[Ff]rantoio|[Oo]liv|[Oo]leificio|[Oo]lio"]',
        "color": "#ef4444", "icon": "flask",
    },
    "Spanish Olive Heritage": {
        "query": '["crop"="olive"]',
        "fallback": '["name"~"[Oo]livar|[Aa]ceite|[Aa]lmazara|[Oo]livo"]',
        "color": "#f97316", "icon": "pagelines",
    },
    "North African Olives": {
        "query": '["crop"="olive"]',
        "fallback": '["name"~"[Zz]itoun|[Oo]liv|[Zz]aytun"]',
        "color": "#a855f7", "icon": "globe",
    },
    "Ancient Olive Trees": {
        "query": '["natural"="tree"]["species"~"[Oo]lea"]',
        "fallback": '["name"~"[Aa]ncient.*[Oo]live|[Oo]ld.*[Oo]live|[Mm]onumental.*[Oo]liv"]',
        "color": "#ec4899", "icon": "tree",
    },
    "Olive Oil Tasting Routes": {
        "query": '["route"~".*"]["name"~"[Oo]liv|[Oo]lio|[Aa]ceite"]',
        "fallback": '["name"~"[Oo]live.*[Rr]oute|[Rr]uta.*[Aa]ceite|[Ss]trada.*[Oo]lio"]',
        "color": "#14b8a6", "icon": "road",
    },
    "World Olive Production Map": {
        "query": '["crop"="olive"]',
        "fallback": '["landuse"="orchard"]["name"~"[Oo]liv"]',
        "color": "#8b5cf6", "icon": "globe",
    },
}

# ═══════════════════════════════════════════
# PRESET LOCATIONS
# ═══════════════════════════════════════════
PRESETS = {
    "Custom": None,
    "Kalamata, Greece": {"lat": 37.0422, "lon": 22.1140, "radius": 20},
    "Jaen, Spain (World Olive Capital)": {"lat": 37.7796, "lon": -3.7849, "radius": 25},
    "Puglia, Italy (Lecce)": {"lat": 40.3516, "lon": 18.1718, "radius": 20},
    "Crete, Greece (Heraklion)": {"lat": 35.3387, "lon": 25.1442, "radius": 25},
    "Tuscany, Italy (Lucca)": {"lat": 43.8430, "lon": 10.5027, "radius": 15},
    "Sfax, Tunisia": {"lat": 34.7406, "lon": 10.7603, "radius": 25},
    "Cordoba, Spain": {"lat": 37.8882, "lon": -4.7794, "radius": 20},
    "Lesbos, Greece": {"lat": 39.1000, "lon": 26.3300, "radius": 20},
    "Umbria, Italy (Spoleto)": {"lat": 42.7313, "lon": 12.7366, "radius": 15},
    "Baena, Spain (DOP)": {"lat": 37.6167, "lon": -4.3222, "radius": 15},
    "Provence, France (Nyons)": {"lat": 44.3617, "lon": 5.1394, "radius": 15},
    "Fez, Morocco": {"lat": 34.0181, "lon": -5.0078, "radius": 25},
    "Jerash, Jordan": {"lat": 32.2747, "lon": 35.8961, "radius": 20},
    "Galilee, Israel": {"lat": 32.8631, "lon": 35.5028, "radius": 20},
}


@st.cache_data(ttl=3600)
def _search_olives(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for olive-related features."""
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
            "wikipedia": tags.get("wikipedia", ""),
            "description": tags.get("description", tags.get("note", "")),
        })
    return features


def render_olive_maps_tab():
    """Main render function for the World Olive & Oil Heritage tab."""

    # ── Header ──
    header_html = '<div class="tab-header emerald"><h4>\U0001fad2 World Olive & Oil Heritage Explorer</h4><p>Discover olive groves, oil mills, olive heritage & Mediterranean traditions worldwide</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="olive_mode")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=37.0422, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="olive_lat")
    with c2:
        lon = st.number_input("Longitude", value=22.1140, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="olive_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, 20, key="olive_radius")

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()), key="olive_preset")
    if preset != "Custom" and PRESETS.get(preset):
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("Explore Olive Heritage", key="olive_search", type="primary",
                 use_container_width=True):
        st.session_state.olive_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "olive_params" not in st.session_state:
        st.info("Select a mode and location, then click Explore to discover olive heritage sites.")
        return

    op = st.session_state.olive_params
    mode_info = MODES[op["mode"]]

    # ── Query ──
    with st.spinner(f"Searching {op['mode']}..."):
        data = _search_olives(op["lat"], op["lon"], op["radius"], op["mode"])
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
    st.markdown("#### Olive Heritage Map")

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
        f"Download {len(rows)} Olive Heritage Sites (CSV)",
        data=buf.getvalue(), file_name="olive_heritage_sites.csv",
        mime="text/csv", key="olive_download",
    )
