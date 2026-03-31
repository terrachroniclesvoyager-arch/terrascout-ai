"""
Medieval World Heritage Explorer module for TerraScout AI.
Discovers castles, monasteries, walled cities, medieval towns & feudal heritage
worldwide via the Overpass API.
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

# ── 10 exploration modes with OSM tags, colours, icons ──
MODES = {
    "Medieval Castles & Fortresses": {
        "tags": [("historic", "castle"), ("castle_type", "defensive")],
        "color": "#8b5cf6", "icon": "tower",
    },
    "Walled Cities & Towns": {
        "tags": [("historic", "city_gate"), ("historic", "citywalls")],
        "color": "#f59e0b", "icon": "gate",
    },
    "Monasteries & Abbeys": {
        "tags": [("historic", "monastery"), ("building", "monastery")],
        "color": "#10b981", "icon": "church",
    },
    "Medieval Cathedrals": {
        "tags": [("building", "cathedral")],
        "color": "#3b82f6", "icon": "church",
    },
    "Knights Templar Sites": {
        "tags": [("historic", "castle"), ("historic", "monastery")],
        "color": "#ef4444", "icon": "cross",
    },
    "Viking Settlements": {
        "tags": [("historic", "archaeological_site"), ("historic", "ruins")],
        "color": "#06b6d4", "icon": "anchor",
    },
    "Crusader Fortifications": {
        "tags": [("historic", "castle"), ("historic", "fort")],
        "color": "#ec4899", "icon": "shield",
    },
    "Medieval Markets & Guilds": {
        "tags": [("historic", "market"), ("historic", "building")],
        "color": "#f97316", "icon": "shopping-cart",
    },
    "Siege Sites & Battlefields": {
        "tags": [("historic", "battlefield"), ("historic", "ruins")],
        "color": "#64748b", "icon": "flag",
    },
    "Medieval University Towns": {
        "tags": [("historic", "building"), ("amenity", "university")],
        "color": "#a855f7", "icon": "book",
    },
}

# ── Preset locations ──
PRESETS = {
    "Custom": None,
    "Carcassonne, France": {"lat": 43.2065, "lon": 2.3663, "r": 5},
    "Edinburgh, Scotland": {"lat": 55.9486, "lon": -3.1999, "r": 5},
    "Toledo, Spain": {"lat": 39.8628, "lon": -4.0273, "r": 5},
    "Bruges, Belgium": {"lat": 51.2093, "lon": 3.2247, "r": 5},
    "Rothenburg, Germany": {"lat": 49.3769, "lon": 10.1789, "r": 5},
    "Rhodes Old Town, Greece": {"lat": 36.4441, "lon": 28.2244, "r": 5},
    "Siena, Italy": {"lat": 43.3188, "lon": 11.3308, "r": 5},
    "York, England": {"lat": 53.9591, "lon": -1.0815, "r": 5},
    "Prague, Czechia": {"lat": 50.0755, "lon": 14.4378, "r": 5},
    "Acre (Akko), Israel": {"lat": 32.9272, "lon": 35.0764, "r": 5},
    "Avignon, France": {"lat": 43.9493, "lon": 4.8055, "r": 5},
    "Dubrovnik, Croatia": {"lat": 42.6507, "lon": 18.0944, "r": 3},
}


@st.cache_data(ttl=3600)
def _query_medieval(lat: float, lon: float, radius_km: float,
                    tags: list[tuple[str, str]]) -> dict:
    """Run Overpass query for the given tags around a point."""
    r_m = radius_km * 1000
    parts = []
    for key, val in tags:
        parts.append(f'node["{key}"="{val}"](around:{r_m},{lat},{lon});')
        parts.append(f'way["{key}"="{val}"](around:{r_m},{lat},{lon});')
    body = "\n  ".join(parts)
    q = f"[out:json][timeout:60];\n(\n  {body}\n);\nout body;\n>;\nout skel qt;"
    result = query_overpass(q)
    if result is None or "_error" in result:
        return {"elements": [], "_error": (result or {}).get("_error", "Unknown")}
    return result


def _extract(data: dict) -> list[dict]:
    """Parse Overpass elements into a flat feature list."""
    els = data.get("elements", [])
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in els
             if e.get("type") == "node" and "lat" in e}
    out = []
    for e in els:
        tags = e.get("tags", {})
        if not tags:
            continue
        lat = lon = None
        if e.get("type") == "node" and "lat" in e:
            lat, lon = e["lat"], e["lon"]
        elif e.get("type") == "way":
            coords = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)
        if lat is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        out.append({
            "name": name, "lat": lat, "lon": lon,
            "historic": tags.get("historic", ""),
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
            "description": tags.get("description", tags.get("description:en", "")),
            "osm_id": e.get("id"),
        })
    return out


# ═══════════════════════════════════════════════
# Main render function
# ═══════════════════════════════════════════════
def render_medieval_maps_tab():
    """Render the Medieval World Heritage Explorer tab."""

    # ── Header ──
    header_html = (
        '<div class="tab-header violet">'
        '<h4>\U0001f3f0 Medieval World Heritage Explorer</h4>'
        '<p>Discover castles, monasteries, walled cities, medieval towns '
        '&amp; feudal heritage worldwide</p></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Controls ──
    st.markdown("#### Search Parameters")
    mode = st.selectbox("Exploration Mode", list(MODES.keys()), key="med_mode")
    mode_info = MODES[mode]

    preset = st.selectbox("Preset Location", list(PRESETS.keys()), key="med_preset")

    c1, c2, c3 = st.columns([1, 1, 1])
    default = PRESETS.get(preset) if preset != "Custom" else None
    with c1:
        lat = st.number_input("Latitude", value=default["lat"] if default else 48.8566,
                              format="%.4f", min_value=-90.0, max_value=90.0,
                              key="med_lat")
    with c2:
        lon = st.number_input("Longitude", value=default["lon"] if default else 2.3522,
                              format="%.4f", min_value=-180.0, max_value=180.0,
                              key="med_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 50,
                           value=default["r"] if default else 10, key="med_radius")

    if default:
        lat, lon, radius = default["lat"], default["lon"], default["r"]

    if st.button("Explore Medieval Sites", key="med_go", width="stretch"):
        st.session_state.med_params = {
            "lat": lat, "lon": lon, "radius": radius,
            "mode": mode, "tags": mode_info["tags"],
            "color": mode_info["color"],
        }

    if "med_params" not in st.session_state:
        st.info("Choose an exploration mode and location, then click Explore.")
        return

    p = st.session_state.med_params

    # ── Query ──
    with st.spinner("Querying OpenStreetMap for medieval heritage..."):
        data = _query_medieval(p["lat"], p["lon"], p["radius"], p["tags"])

    if "_error" in data and not data.get("elements"):
        st.error(f"Overpass error: {html_module.escape(str(data['_error']))}")
        return

    features = _extract(data)
    if not features:
        st.warning("No sites found. Try a larger radius or different mode.")
        return

    # ── Stats ──
    st.markdown("---")
    st.markdown(f"#### {html_module.escape(p['mode'])} &mdash; Results",
                unsafe_allow_html=True)

    cols = st.columns(4)
    cols[0].metric("Sites Found", len(features))
    named = sum(1 for f in features if f["name"] != "Unnamed")
    cols[1].metric("Named Sites", named)
    wiki = sum(1 for f in features if f["wikipedia"])
    cols[2].metric("With Wikipedia", wiki)
    cols[3].metric("Radius (km)", p["radius"])

    # ── Map ──
    st.markdown("---")
    st.markdown("#### Heritage Map")

    m = folium.Map(location=[p["lat"], p["lon"]], zoom_start=12, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    folium.Circle(
        location=[p["lat"], p["lon"]],
        radius=p["radius"] * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)

    color = p["color"]
    for f in features:
        safe_name = html_module.escape(f["name"])
        safe_desc = html_module.escape(f["description"][:120])
        wiki_link = ""
        if f["wikipedia"]:
            parts = f["wikipedia"].split(":", 1)
            lang, title = (parts[0], parts[1]) if len(parts) == 2 else ("en", parts[0])
            wiki_link = (f'<br/><a href="https://{html_module.escape(lang)}'
                         f'.wikipedia.org/wiki/{html_module.escape(title)}" '
                         f'target="_blank">Wikipedia</a>')
        popup = (f'<div style="max-width:200px;"><strong>{safe_name}</strong>'
                 f'<br/><span style="font-size:0.8rem;color:#666;">'
                 f'{html_module.escape(f["historic"])}</span>'
                 f'<br/><span style="font-size:0.75rem;">{safe_desc}</span>'
                 f'{wiki_link}</div>')
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=6,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=220),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_html(m._repr_html_(), height=500)

    # ── Notable sites list ──
    st.markdown("---")
    st.markdown("#### Notable Sites")
    sorted_f = sorted(features, key=lambda x: (x["wikipedia"] != "", x["name"] != "Unnamed"),
                      reverse=True)
    for f in sorted_f[:15]:
        badge = ""
        if f["wikipedia"]:
            badge = ' <span style="color:#3b82f6;font-size:0.7rem;">WIKI</span>'
        safe = html_module.escape(f["name"])
        st.markdown(
            f'<div style="display:flex;align-items:center;margin-bottom:0.4rem;">'
            f'<div style="width:8px;height:40px;border-radius:4px;background:{color};'
            f'margin-right:0.6rem;flex-shrink:0;"></div>'
            f'<div><div style="color:#e8ecf4;font-weight:600;font-size:0.85rem;">'
            f'{safe}{badge}</div>'
            f'<div style="color:#5a6580;font-size:0.7rem;">'
            f'{f["lat"]:.4f}, {f["lon"]:.4f}</div></div></div>',
            unsafe_allow_html=True,
        )

    # ── Data table & download ──
    st.markdown("---")
    rows = [{
        "name": f["name"], "latitude": f["lat"], "longitude": f["lon"],
        "historic": f["historic"], "wikipedia": f["wikipedia"],
        "wikidata": f["wikidata"], "osm_id": f["osm_id"],
    } for f in features]
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(df)} Medieval Sites (CSV)",
        data=buf.getvalue(),
        file_name="medieval_heritage.csv",
        mime="text/csv",
        key="med_dl",
    )
