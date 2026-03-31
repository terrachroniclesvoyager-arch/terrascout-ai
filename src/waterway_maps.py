"""
World Rivers & Waterways Heritage Explorer for TerraScout AI.
Discovers great rivers, canals, locks, deltas & waterway heritage via Overpass API.
"""

import io
import math
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
    "World's Greatest Rivers": {
        "query": '(way["waterway"="river"]["name"]({bbox});relation["waterway"="river"]["name"]({bbox});)',
        "color": "#06b6d4", "icon": "water",
    },
    "Historic Canal Systems": {
        "query": '(way["waterway"="canal"]({bbox});)',
        "color": "#8b5cf6", "icon": "link",
    },
    "River Delta Ecosystems": {
        "query": '(way["natural"="wetland"]({bbox});way["wetland"="tidalflat"]({bbox});way["water"="river"]["natural"="water"]({bbox});)',
        "color": "#10b981", "icon": "leaf",
    },
    "Locks & Dam Heritage": {
        "query": '(node["waterway"="lock_gate"]({bbox});way["waterway"="dam"]({bbox});node["waterway"="dam"]({bbox});way["waterway"="weir"]({bbox});)',
        "color": "#f59e0b", "icon": "cog",
    },
    "Sacred & Holy Rivers": {
        "query": '(way["waterway"="river"]["name"]({bbox});relation["waterway"="river"]["name"]({bbox});)',
        "color": "#ec4899", "icon": "star",
    },
    "Underground Rivers": {
        "query": '(way["waterway"="river"]["tunnel"="yes"]({bbox});way["waterway"="stream"]["tunnel"="yes"]({bbox});way["waterway"="canal"]["tunnel"="yes"]({bbox});)',
        "color": "#a855f7", "icon": "eye-close",
    },
    "River Cruise Routes": {
        "query": '(way["waterway"="river"]["boat"="yes"]({bbox});way["waterway"="canal"]["boat"="yes"]({bbox});relation["route"="ferry"]["motor_vehicle"~"yes|no"]({bbox});)',
        "color": "#3b82f6", "icon": "plane",
    },
    "Floodplain Heritage": {
        "query": '(way["natural"="floodplain"]({bbox});way["flood_prone"="yes"]({bbox});way["natural"="wetland"]["wetland"="floodplain"]({bbox});node["natural"="spring"]({bbox});)',
        "color": "#14b8a6", "icon": "tint",
    },
    "River Bridges & Crossings": {
        "query": '(way["bridge"="yes"]["highway"]({bbox});node["man_made"="bridge"]({bbox});way["man_made"="bridge"]({bbox});)',
        "color": "#f97316", "icon": "road",
    },
    "World Watershed Map": {
        "query": '(way["waterway"~"river|stream|drain|ditch"]({bbox});)',
        "color": "#38bdf8", "icon": "tint",
    },
}

PRESETS = {
    "Custom Location": None,
    "Nile Delta, Egypt": {"lat": 31.05, "lon": 31.40, "r": 20},
    "Amazon Basin, Brazil": {"lat": -3.12, "lon": -60.02, "r": 25},
    "Ganges, Varanasi": {"lat": 25.32, "lon": 83.01, "r": 10},
    "Mississippi Delta, USA": {"lat": 29.15, "lon": -89.25, "r": 20},
    "Danube, Budapest": {"lat": 47.50, "lon": 19.04, "r": 8},
    "Rhine, Cologne": {"lat": 50.94, "lon": 6.96, "r": 8},
    "Thames, London": {"lat": 51.50, "lon": -0.08, "r": 6},
    "Mekong Delta, Vietnam": {"lat": 10.03, "lon": 105.78, "r": 20},
    "Venice Canals, Italy": {"lat": 45.44, "lon": 12.33, "r": 5},
    "Panama Canal": {"lat": 9.08, "lon": -79.68, "r": 10},
    "Seine, Paris": {"lat": 48.86, "lon": 2.35, "r": 5},
    "Yangtze, Three Gorges": {"lat": 30.83, "lon": 111.00, "r": 15},
}


@st.cache_data(ttl=3600)
def _query_waterways(mode_name: str, south: float, west: float, north: float, east: float) -> dict:
    """Query Overpass for waterway features."""
    mode = MODES[mode_name]
    bbox = f"{south},{west},{north},{east}"
    q = mode["query"].replace("{bbox}", bbox)
    query = f"[out:json][timeout:90];\n(\n  {q}\n);\nout body;\n>;\nout skel qt;"
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": (result or {}).get("_error", "Query failed")}
    return result


def _extract_features(data: dict, mode_color: str) -> list:
    """Parse Overpass elements into feature dicts."""
    elements = data.get("elements", [])
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in elements if e.get("type") == "node" and "lat" in e}
    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat, lon, coords = None, None, []
        if el.get("type") == "node" and "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            coords = [nodes[n] for n in el.get("nodes", []) if n in nodes]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)
        if lat is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        ftype = tags.get("waterway", tags.get("natural", tags.get("man_made", tags.get("highway", "feature"))))
        features.append({"name": name, "type": ftype, "lat": lat, "lon": lon,
                         "coords": coords, "color": mode_color, "tags": tags, "osm_id": el.get("id")})
    return features


def render_waterway_maps_tab():
    """Main render function for the World Rivers & Waterways Heritage Explorer."""
    header_html = '<div class="tab-header cyan"><h4>\U0001f3de\ufe0f World Rivers & Waterways Heritage Explorer</h4><p>Discover great rivers, canals, locks, river deltas & waterway heritage worldwide</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Explorer Settings")
    c1, c2 = st.columns([1, 1])
    with c1:
        mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="ww_mode")
    with c2:
        preset = st.selectbox("Preset Location", list(PRESETS.keys()), key="ww_preset")

    p = PRESETS.get(preset)
    defaults = (p["lat"], p["lon"], p["r"]) if p else (47.50, 19.04, 10)

    c3, c4, c5 = st.columns(3)
    with c3:
        lat = st.number_input("Latitude", value=defaults[0], format="%.4f", min_value=-90.0, max_value=90.0, key="ww_lat")
    with c4:
        lon = st.number_input("Longitude", value=defaults[1], format="%.4f", min_value=-180.0, max_value=180.0, key="ww_lon")
    with c5:
        radius = st.slider("Radius (km)", 1, 50, defaults[2], key="ww_radius")

    if not st.button("Explore Waterways", key="ww_go", type="primary"):
        st.info("Choose a mode and location, then click **Explore Waterways** to begin.")
        return

    # ── Query ──
    dlat = radius / 111.0
    dlon = radius / (111.0 * max(0.01, abs(math.cos(math.radians(lat)))))
    south, north = lat - dlat, lat + dlat
    west, east = lon - dlon, lon + dlon

    with st.spinner(f"Querying {html_module.escape(mode)} features..."):
        data = _query_waterways(mode, south, west, north, east)

    if "_error" in data:
        st.error(f"Overpass query failed: {html_module.escape(str(data['_error']))}")
        return

    mode_color = MODES[mode]["color"]
    features = _extract_features(data, mode_color)

    if not features:
        st.warning("No features found. Try a larger radius or different location.")
        return

    # ── Stats ──
    st.markdown("---")
    st.markdown("#### Discovery Overview")
    named = [f for f in features if f["name"] != "Unnamed"]
    type_counts = {}
    for f in features:
        type_counts[f["type"]] = type_counts.get(f["type"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Features", len(features))
    cols[1].metric("Named Features", len(named))
    cols[2].metric("Feature Types", len(type_counts))
    cols[3].metric("Search Radius", f"{radius} km")

    # Type breakdown
    if type_counts:
        top_types = sorted(type_counts.items(), key=lambda x: -x[1])[:6]
        tcols = st.columns(len(top_types))
        for i, (t, c) in enumerate(top_types):
            tcols[i].metric(html_module.escape(str(t)).title(), c)

    # ── Map ──
    st.markdown("---")
    st.markdown("#### Waterway Heritage Map")

    m = folium.Map(location=[lat, lon], zoom_start=11, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    folium.Circle(location=[lat, lon], radius=radius * 1000, color="#06b6d4",
                  fill=True, fill_opacity=0.03, weight=1).add_to(m)

    for f in features[:500]:
        safe_name = html_module.escape(f["name"])
        safe_type = html_module.escape(str(f["type"]))
        popup = f'<div style="max-width:200px;"><strong>{safe_name}</strong><br/><span style="font-size:0.85rem;">{safe_type}</span></div>'
        if f["coords"] and len(f["coords"]) > 1:
            is_closed = len(f["coords"]) > 3 and f["coords"][0] == f["coords"][-1]
            if is_closed:
                folium.Polygon(locations=f["coords"], color=f["color"], fill=True,
                               fill_color=f["color"], fill_opacity=0.25, weight=2,
                               popup=folium.Popup(popup, max_width=220)).add_to(m)
            else:
                folium.PolyLine(locations=f["coords"], color=f["color"], weight=3,
                                opacity=0.7, popup=folium.Popup(popup, max_width=220)).add_to(m)
        else:
            folium.CircleMarker(location=[f["lat"], f["lon"]], radius=5, color=f["color"],
                                fill=True, fill_color=f["color"], fill_opacity=0.7, weight=2,
                                popup=folium.Popup(popup, max_width=220)).add_to(m)

    folium.LayerControl().add_to(m)
    st_html(m._repr_html_(), height=500)

    # ── Data Table ──
    st.markdown("---")
    st.markdown("#### Feature Data")

    rows = [{"Name": f["name"], "Type": f["type"], "Latitude": round(f["lat"], 5),
             "Longitude": round(f["lon"], 5), "OSM ID": f.get("osm_id", "")} for f in features]
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} features)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ── Download ──
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(df)} Waterway Features (CSV)", data=buf.getvalue(),
        file_name=f"waterway_{mode.lower().replace(' ', '_')}.csv",
        mime="text/csv", key="ww_download",
    )
