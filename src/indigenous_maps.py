"""
Indigenous Peoples & Heritage Explorer module for TerraScout AI.
Uses the Overpass API to discover indigenous cultures, sacred sites,
tribal lands, and native heritage features worldwide.
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

# ── 10 Modes with OSM tags, colors, and preset locations ──
MODES = {
    "Aboriginal Dreamtime Sites": {
        "tags": [("historic", "archaeological_site"), ("tourism", "artwork")],
        "color": "#f59e0b",
        "preset": {"lat": -25.3444, "lon": 131.0369, "radius": 50, "label": "Uluru, Australia"},
    },
    "Native American Heritage": {
        "tags": [("historic", "archaeological_site"), ("historic", "memorial"), ("boundary", "aboriginal_lands")],
        "color": "#ef4444",
        "preset": {"lat": 36.0544, "lon": -112.1401, "radius": 30, "label": "Grand Canyon, USA"},
    },
    "Maori Sacred Sites": {
        "tags": [("historic", "archaeological_site"), ("historic", "monument"), ("amenity", "place_of_worship")],
        "color": "#10b981",
        "preset": {"lat": -38.1446, "lon": 176.2378, "radius": 20, "label": "Rotorua, NZ"},
    },
    "Amazonian Tribal Lands": {
        "tags": [("boundary", "aboriginal_lands"), ("boundary", "protected_area")],
        "color": "#22c55e",
        "preset": {"lat": -3.4653, "lon": -62.2159, "radius": 50, "label": "Manaus, Brazil"},
    },
    "Sami & Arctic Peoples": {
        "tags": [("historic", "archaeological_site"), ("historic", "monument"), ("tourism", "museum")],
        "color": "#3b82f6",
        "preset": {"lat": 69.6496, "lon": 18.9560, "radius": 30, "label": "Tromsø, Norway"},
    },
    "African Tribal Heritage": {
        "tags": [("historic", "archaeological_site"), ("historic", "monument"), ("tourism", "museum")],
        "color": "#a855f7",
        "preset": {"lat": -29.8587, "lon": 31.0218, "radius": 30, "label": "KwaZulu-Natal, SA"},
    },
    "Polynesian Heritage": {
        "tags": [("historic", "archaeological_site"), ("historic", "monument")],
        "color": "#06b6d4",
        "preset": {"lat": -17.5516, "lon": -149.5585, "radius": 20, "label": "Tahiti, Fr. Polynesia"},
    },
    "Himalayan Indigenous": {
        "tags": [("historic", "monument"), ("amenity", "place_of_worship"), ("amenity", "monastery")],
        "color": "#f97316",
        "preset": {"lat": 27.9881, "lon": 86.9250, "radius": 30, "label": "Everest Region, Nepal"},
    },
    "Indigenous Art & Rock Art": {
        "tags": [("historic", "archaeological_site"), ("tourism", "artwork"), ("historic", "ruins")],
        "color": "#ec4899",
        "preset": {"lat": -29.0883, "lon": 29.2163, "radius": 30, "label": "Drakensberg, SA"},
    },
    "World Indigenous Languages": {
        "tags": [("tourism", "museum"), ("amenity", "library"), ("amenity", "community_centre")],
        "color": "#8b5cf6",
        "preset": {"lat": -13.5320, "lon": -71.9675, "radius": 20, "label": "Cusco, Peru"},
    },
}


@st.cache_data(ttl=3600)
def _query_indigenous(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass API for indigenous heritage features."""
    cfg = MODES.get(mode)
    if not cfg:
        return {"elements": []}
    radius_m = radius_km * 1000
    parts = []
    for key, val in cfg["tags"]:
        parts.append(f'node["{key}"="{val}"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["{key}"="{val}"](around:{radius_m},{lat},{lon});')
        parts.append(f'relation["{key}"="{val}"](around:{radius_m},{lat},{lon});')
    q = f"[out:json][timeout:60];\n(\n  {chr(10).join('  ' + p for p in parts)}\n);\nout body;\n>;\nout skel qt;"
    result = query_overpass(q)
    if result is None or "_error" in result:
        return {"_error": result.get("_error", "Unknown") if result else "No response"}
    return result


def _extract(data: dict) -> list:
    """Extract features with coordinates from Overpass response."""
    elements = data.get("elements", [])
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in elements if e.get("type") == "node" and "lat" in e}
    feats = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat = lon = None
        if el.get("type") == "node" and "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") in ("way", "relation"):
            coords = [nodes[n] for n in el.get("nodes", []) if n in nodes]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)
        if lat is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        feats.append({
            "name": name, "lat": lat, "lon": lon,
            "type": tags.get("historic", tags.get("boundary", tags.get("tourism", tags.get("amenity", "")))),
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
            "description": tags.get("description", tags.get("description:en", "")),
            "osm_id": el.get("id"),
        })
    return feats


def render_indigenous_maps_tab():
    """Main render function for the Indigenous Peoples & Heritage Explorer tab."""

    # ── Header ──
    header_html = '<div class="tab-header pink"><h4>\U0001fab6 Indigenous Peoples & Heritage Explorer</h4><p>Discover indigenous cultures, sacred sites, tribal lands & native heritage worldwide</p></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Mode selector ──
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="indig_mode")
    cfg = MODES[mode]
    preset = cfg["preset"]

    # ── Controls ──
    st.markdown("#### Search Parameters")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=preset["lat"], format="%.4f",
                              min_value=-90.0, max_value=90.0, key="indig_lat")
    with c2:
        lon = st.number_input("Longitude", value=preset["lon"], format="%.4f",
                              min_value=-180.0, max_value=180.0, key="indig_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, preset["radius"], key="indig_radius")

    st.caption(f"Preset location: **{html_module.escape(preset['label'])}**")

    if st.button("Explore Indigenous Heritage", key="indig_search", type="primary"):
        st.session_state.indig_params = {"lat": lat, "lon": lon, "radius": radius, "mode": mode}

    if "indig_params" not in st.session_state:
        st.info("Select a mode and location, then click Explore to discover indigenous heritage sites.")
        return

    p = st.session_state.indig_params

    # ── Query ──
    with st.spinner(f"Searching {html_module.escape(p['mode'])} sites..."):
        data = _query_indigenous(p["lat"], p["lon"], p["radius"], p["mode"])

    if "_error" in data:
        st.error(f"Overpass query failed: {html_module.escape(str(data['_error']))}")
        return

    feats = _extract(data)
    if not feats:
        st.warning("No features found. Try a larger radius or different mode.")
        return

    color = MODES[p["mode"]]["color"]

    # ── Stats ──
    st.markdown("---")
    st.markdown("#### Discovery Overview")
    type_counts = {}
    for f in feats:
        t = f["type"] or "other"
        type_counts[t] = type_counts.get(t, 0) + 1

    cols = st.columns(min(len(type_counts) + 1, 5))
    cols[0].metric("Total Sites", len(feats))
    for i, (t, cnt) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(cols):
            cols[i + 1].metric(html_module.escape(t.replace("_", " ").title()), cnt)

    # ── Map ──
    st.markdown("---")
    st.markdown("#### Heritage Map")
    m = folium.Map(location=[p["lat"], p["lon"]], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)
    folium.Circle(
        location=[p["lat"], p["lon"]], radius=p["radius"] * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)

    for f in feats:
        safe_name = html_module.escape(f["name"])
        safe_desc = html_module.escape(f["description"][:120])
        wiki = ""
        if f["wikipedia"]:
            lang, title = (f["wikipedia"].split(":", 1) + [""])[:2] if ":" in f["wikipedia"] else ("en", f["wikipedia"])
            wiki = f'<br/><a href="https://{html_module.escape(lang)}.wikipedia.org/wiki/{html_module.escape(title)}" target="_blank" style="font-size:0.75rem;">Wikipedia</a>'
        popup = f'<div style="max-width:220px;"><strong>{safe_name}</strong><br/><span style="font-size:0.8rem;color:#666;">{html_module.escape(f["type"])}</span><br/><span style="font-size:0.75rem;">{safe_desc}</span>{wiki}</div>'
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=6, color=color,
            fill=True, fill_color=color, fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=240),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_html(m._repr_html_(), height=500)

    # ── Data table ──
    st.markdown("---")
    rows = [{
        "Name": f["name"], "Type": f["type"], "Latitude": f["lat"],
        "Longitude": f["lon"], "Wikipedia": f["wikipedia"],
        "Wikidata": f["wikidata"], "OSM ID": f["osm_id"],
    } for f in feats]
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ── Download ──
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Indigenous Heritage Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"indigenous_{p['mode'].lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="indig_download",
    )
