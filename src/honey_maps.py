"""
World Honey & Beekeeping Heritage Explorer for TerraScout AI.
Uses the Overpass API to find apiaries, bee sanctuaries, honey museums,
and beekeeping heritage features from OpenStreetMap.
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

# ── Mode definitions: label -> (overpass tag filter, color, preset) ──
MODES = {
    "Apiaries & Bee Farms": {
        "tags": [('craft', 'beekeeper'), ('building', 'apiary'), ('landuse', 'apiary')],
        "color": "#f59e0b",
        "preset": {"lat": 45.4642, "lon": 9.1900, "z": 10, "r": 20},
    },
    "Honey Museums & Heritage": {
        "tags": [('tourism', 'museum'), ('museum', 'beekeeping'), ('museum', 'honey')],
        "color": "#8b5cf6",
        "preset": {"lat": 48.8566, "lon": 2.3522, "z": 8, "r": 50},
    },
    "Manuka Honey (New Zealand)": {
        "tags": [('craft', 'beekeeper'), ('product', 'honey'), ('shop', 'honey')],
        "color": "#10b981",
        "preset": {"lat": -38.14, "lon": 176.25, "z": 8, "r": 80},
    },
    "Mediterranean Beekeeping": {
        "tags": [('craft', 'beekeeper'), ('building', 'apiary')],
        "color": "#06b6d4",
        "preset": {"lat": 37.97, "lon": 23.73, "z": 9, "r": 30},
    },
    "African Wild Honey": {
        "tags": [('craft', 'beekeeper'), ('product', 'honey')],
        "color": "#ef4444",
        "preset": {"lat": -1.29, "lon": 36.82, "z": 9, "r": 40},
    },
    "Asian Bee Species": {
        "tags": [('craft', 'beekeeper'), ('building', 'apiary')],
        "color": "#ec4899",
        "preset": {"lat": 13.75, "lon": 100.52, "z": 9, "r": 30},
    },
    "Urban Beekeeping Projects": {
        "tags": [('craft', 'beekeeper'), ('leisure', 'garden')],
        "color": "#3b82f6",
        "preset": {"lat": 51.5074, "lon": -0.1278, "z": 11, "r": 15},
    },
    "Bee Sanctuary & Conservation": {
        "tags": [('leisure', 'nature_reserve'), ('protect_class', '4')],
        "color": "#14b8a6",
        "preset": {"lat": 50.11, "lon": 8.68, "z": 9, "r": 30},
    },
    "Historic Mead & Honey Wine": {
        "tags": [('craft', 'brewery'), ('product', 'mead'), ('drink', 'mead')],
        "color": "#a855f7",
        "preset": {"lat": 53.35, "lon": -6.26, "z": 9, "r": 40},
    },
    "World Pollinator Map": {
        "tags": [('leisure', 'garden'), ('garden:type', 'pollinator'),
                 ('habitat', 'pollinator')],
        "color": "#f97316",
        "preset": {"lat": 38.90, "lon": -77.04, "z": 10, "r": 20},
    },
}


def _build_query(lat: float, lon: float, radius_m: int, tags: list) -> str:
    """Build an Overpass QL query from a list of (key, value) tag pairs."""
    parts = []
    for k, v in tags:
        parts.append(f'node["{k}"="{v}"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["{k}"="{v}"](around:{radius_m},{lat},{lon});')
    joined = "\n  ".join(parts)
    return f"[out:json][timeout:60];\n(\n  {joined}\n);\nout body;\n>;\nout skel qt;"


@st.cache_data(ttl=3600)
def _fetch_honey_data(lat: float, lon: float, radius_km: float, mode: str) -> dict:
    """Query Overpass for honey/beekeeping features."""
    cfg = MODES.get(mode)
    if not cfg:
        return {"elements": []}
    query = _build_query(lat, lon, int(radius_km * 1000), cfg["tags"])
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": (result or {}).get("_error", "Unknown")}
    return result


def _extract(data: dict, color: str) -> list:
    """Parse Overpass elements into feature dicts."""
    elements = data.get("elements", [])
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in elements
             if e.get("type") == "node" and "lat" in e}
    feats = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat = lon = None
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
        feats.append({
            "name": name, "lat": lat, "lon": lon, "color": color,
            "type": tags.get("craft", tags.get("tourism", tags.get("landuse", ""))),
            "website": tags.get("website", ""),
            "osm_id": el.get("id"),
            "description": tags.get("description", ""),
        })
    return feats


def render_honey_maps_tab():
    """Main render function for the Honey & Beekeeping Heritage tab."""

    # ── Header ──
    header_html = (
        '<div class="tab-header emerald">'
        '<h4>\U0001f36f World Honey & Beekeeping Heritage Explorer</h4>'
        '<p>Discover apiaries, bee sanctuaries & honey traditions worldwide</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="honey_mode")
    cfg = MODES[mode]
    preset = cfg["preset"]

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=preset["lat"], format="%.4f",
                               min_value=-90.0, max_value=90.0, key="honey_lat")
    with c2:
        lon = st.number_input("Longitude", value=preset["lon"], format="%.4f",
                               min_value=-180.0, max_value=180.0, key="honey_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 100, preset["r"], key="honey_r")

    if st.button("Explore Beekeeping", key="honey_go", type="primary"):
        st.session_state.honey_params = {
            "lat": lat, "lon": lon, "radius": radius, "mode": mode,
        }

    if "honey_params" not in st.session_state:
        st.info("Choose a mode and location, then click Explore to discover honey heritage.")
        return

    hp = st.session_state.honey_params
    color = MODES[hp["mode"]]["color"]

    # ── Fetch ──
    with st.spinner("Querying OpenStreetMap for beekeeping features..."):
        data = _fetch_honey_data(hp["lat"], hp["lon"], hp["radius"], hp["mode"])

    if "_error" in data:
        st.error(f"Overpass query failed: {html_module.escape(str(data['_error']))}")
        return

    features = _extract(data, color)
    if not features:
        st.warning("No features found. Try a larger radius or different mode.")
        return

    # ── Stats row ──
    st.markdown("---")
    st.markdown("#### Results Overview")
    named = sum(1 for f in features if f["name"] != "Unnamed")
    with_web = sum(1 for f in features if f["website"])
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Features", len(features))
    s2.metric("Named Sites", named)
    s3.metric("With Website", with_web)
    s4.metric("Mode", hp["mode"][:18])

    # ── Map ──
    st.markdown("---")
    st.markdown("#### Beekeeping Heritage Map")

    m = folium.Map(location=[hp["lat"], hp["lon"]],
                   zoom_start=MODES[hp["mode"]]["preset"]["z"], tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    folium.Circle(
        location=[hp["lat"], hp["lon"]],
        radius=hp["radius"] * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)

    for f in features:
        safe_name = html_module.escape(f["name"])
        safe_desc = html_module.escape(f["description"][:120])
        web_link = ""
        if f["website"]:
            safe_url = html_module.escape(f["website"])
            web_link = f'<br/><a href="{safe_url}" target="_blank">Website</a>'
        popup = (
            f'<div style="max-width:200px;">'
            f'<strong>{safe_name}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(f["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{safe_desc}</span>'
            f'{web_link}</div>'
        )
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=7,
            color=f["color"], fill=True, fill_color=f["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=220),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_html(m._repr_html_(), height=500)

    # ── Data table ──
    st.markdown("---")
    rows = [{
        "Name": f["name"], "Type": f["type"],
        "Latitude": round(f["lat"], 5), "Longitude": round(f["lon"], 5),
        "Website": f["website"], "OSM ID": f["osm_id"],
    } for f in features]
    df = pd.DataFrame(rows)

    with st.expander(f"Data Table ({len(df)} features)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ── Download ──
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Features (CSV)",
        data=csv_buf.getvalue(),
        file_name="honey_beekeeping_data.csv",
        mime="text/csv",
        key="honey_dl",
    )
