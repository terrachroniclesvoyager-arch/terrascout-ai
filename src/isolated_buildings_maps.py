# -*- coding: utf-8 -*-
"""
Regional Isolated Buildings Scanner module for TerraScout AI.
Finds buildings and structures that are geographically isolated from other
buildings, potentially indicating ancient ruins, remote outposts, hermitages,
or otherwise peculiar structures worth investigating in a specific radius.

Uses the Overpass API to fetch all buildings in a defined area, then computes
nearest-neighbor distances to identify the most isolated ones locally, displayed
in red on a dark map.
"""

import io
import math
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

# ── Theme ──
_BG, _SURFACE, _CARD = "#0a0e1a", "#111827", "#1a2235"
_BORDER, _TEXT, _TEXT2, _ACCENT = "#2a3550", "#e8ecf4", "#8b97b0", "#ef4444"

# ── Exploration modes ──
MAP_MODES = [
    "All Isolated Buildings",
    "Remote Historic Sites",
    "Lone Religious Buildings",
    "Isolated Ruins & Remains",
    "Remote Towers & Fortifications",
    "Lone Farms & Barns",
    "Remote Shelters & Huts",
    "Isolated Industrial Relics",
    "Remote Water Structures",
    "Mystery Structures",
]

MODE_CONFIG = {
    "All Isolated Buildings": {
        "color": "#ef4444", "icon": "home",
        "desc": "Any building far from other buildings — the most remote structures.",
        "preset": {"lat": 41.9, "lon": 12.5, "radius": 15, "zoom": 10},
        "query_tags": [("building", "yes")],
        "fallback_tags": [("building", "yes")],
    },
    "Remote Historic Sites": {
        "color": "#f59e0b", "icon": "monument",
        "desc": "Historic buildings far from modern settlements.",
        "preset": {"lat": 37.97, "lon": 23.73, "radius": 10, "zoom": 11},
        "query_tags": [("historic", "yes")],
        "fallback_tags": [("historic", "building"), ("historic", "ruins")],
    },
    "Lone Religious Buildings": {
        "color": "#a855f7", "icon": "church",
        "desc": "Churches, chapels, temples isolated in the countryside.",
        "preset": {"lat": 43.77, "lon": 11.25, "radius": 15, "zoom": 10},
        "query_tags": [("amenity", "place_of_worship")],
        "fallback_tags": [("building", "church"), ("building", "chapel")],
    },
    "Isolated Ruins & Remains": {
        "color": "#dc2626", "icon": "ruins",
        "desc": "Ancient ruins, abandoned structures, and archaeological remains far from habitation.",
        "preset": {"lat": 37.97, "lon": 23.73, "radius": 12, "zoom": 10},
        "query_tags": [("historic", "ruins")],
        "fallback_tags": [("building", "ruins")],
    },
    "Remote Towers & Fortifications": {
        "color": "#8b5cf6", "icon": "tower",
        "desc": "Watchtowers, signal towers, and fortifications in remote areas.",
        "preset": {"lat": 41.9, "lon": 12.5, "radius": 20, "zoom": 9},
        "query_tags": [("man_made", "tower")],
        "fallback_tags": [("historic", "castle"), ("building", "tower")],
    },
    "Lone Farms & Barns": {
        "color": "#10b981", "icon": "barn",
        "desc": "Farmsteads and barns isolated in the countryside.",
        "preset": {"lat": 43.3, "lon": 11.3, "radius": 10, "zoom": 11},
        "query_tags": [("building", "farm")],
        "fallback_tags": [("building", "barn"), ("building", "farm_auxiliary")],
    },
    "Remote Shelters & Huts": {
        "color": "#06b6d4", "icon": "hut",
        "desc": "Mountain huts, wilderness shelters, refuges far from roads.",
        "preset": {"lat": 46.5, "lon": 11.3, "radius": 15, "zoom": 10},
        "query_tags": [("tourism", "alpine_hut")],
        "fallback_tags": [("building", "hut"), ("tourism", "wilderness_hut")],
    },
    "Isolated Industrial Relics": {
        "color": "#f97316", "icon": "industry",
        "desc": "Abandoned mines, old mills, and industrial remains in remote locations.",
        "preset": {"lat": 54.0, "lon": -2.0, "radius": 15, "zoom": 10},
        "query_tags": [("historic", "mine")],
        "fallback_tags": [("man_made", "mineshaft"), ("historic", "mill")],
    },
    "Remote Water Structures": {
        "color": "#3b82f6", "icon": "water",
        "desc": "Isolated wells, cisterns, fountains, and aqueducts far from settlements.",
        "preset": {"lat": 35.0, "lon": 33.0, "radius": 15, "zoom": 10},
        "query_tags": [("man_made", "water_well")],
        "fallback_tags": [("amenity", "fountain"), ("man_made", "cistern")],
    },
    "Mystery Structures": {
        "color": "#ec4899", "icon": "question",
        "desc": "Unidentified or untagged buildings in very remote locations — true mysteries.",
        "preset": {"lat": 41.9, "lon": 12.5, "radius": 20, "zoom": 9},
        "query_tags": [("building", "yes")],
        "fallback_tags": [("building", "yes")],
    },
}

PRESETS = {
    "Custom": None,
    "Rome, Italy": {"lat": 41.9, "lon": 12.5, "radius": 15},
    "Athens, Greece": {"lat": 37.97, "lon": 23.73, "radius": 12},
    "Tuscany, Italy": {"lat": 43.3, "lon": 11.3, "radius": 15},
    "Scottish Highlands": {"lat": 57.5, "lon": -5.0, "radius": 20},
    "Sahara (Algeria)": {"lat": 27.0, "lon": 2.5, "radius": 30},
    "Dolomites, Italy": {"lat": 46.5, "lon": 11.8, "radius": 15},
    "Cappadocia, Turkey": {"lat": 38.65, "lon": 34.83, "radius": 15},
    "Jordanian Desert": {"lat": 30.3, "lon": 35.5, "radius": 20},
    "Patagonia, Argentina": {"lat": -50.0, "lon": -70.0, "radius": 25},
    "Outback, Australia": {"lat": -25.3, "lon": 131.0, "radius": 30},
    "Iceland Interior": {"lat": 64.8, "lon": -18.5, "radius": 20},
    "Siberia, Russia": {"lat": 62.0, "lon": 130.0, "radius": 30},
    "Gobi Desert, Mongolia": {"lat": 43.5, "lon": 104.0, "radius": 30},
    "Atacama, Chile": {"lat": -23.8, "lon": -69.5, "radius": 25},
}


# =====================================================================
# HAVERSINE DISTANCE
# =====================================================================
def _haversine_km(lat1, lon1, lat2, lon2):
    """Return distance in km between two points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# =====================================================================
# OVERPASS QUERY
# =====================================================================
@st.cache_data(ttl=3600)
def _search_structures(lat: float, lon: float, radius_km: float,
                       mode: str) -> dict:
    """Query Overpass API for structures in the given mode."""
    cfg = MODE_CONFIG[mode]
    radius_m = int(radius_km * 1000)
    parts = []
    for key, val in cfg["query_tags"]:
        parts.append(f'node["{key}"="{val}"](around:{radius_m},{lat},{lon});')
        parts.append(f'way["{key}"="{val}"](around:{radius_m},{lat},{lon});')
    query = f"""[out:json][timeout:90];({chr(10).join(parts)});out center;"""
    result = query_overpass(query)
    if result and "_error" not in result:
        return result
    # Fallback
    parts2 = []
    for key, val in cfg["fallback_tags"]:
        parts2.append(f'node["{key}"="{val}"](around:{radius_m},{lat},{lon});')
        parts2.append(f'way["{key}"="{val}"](around:{radius_m},{lat},{lon});')
    query2 = f"""[out:json][timeout:90];({chr(10).join(parts2)});out center;"""
    result2 = query_overpass(query2)
    if result2 is None or "_error" in result2:
        err = (result2 or {}).get("_error", "Unknown error")
        st.error(f"Overpass query failed: {err}. Try a smaller radius.")
        return {"elements": []}
    return result2


@st.cache_data(ttl=3600)
def _search_roads_for_context(lat: float, lon: float, radius_km: float) -> list:
    """Fetch all roads in the radius to provide geographical context."""
    radius_m = int(radius_km * 1000)
    query = f"""[out:json][timeout:90];
    way["highway"](around:{radius_m},{lat},{lon});
    out center;"""
    result = query_overpass(query)
    roads = []
    if result and "_error" not in result:
        for el in result.get("elements", []):
            center = el.get("center", {})
            if "lat" in center and "lon" in center:
                tags = el.get("tags", {})
                roads.append({
                    "lat": center["lat"],
                    "lon": center["lon"],
                    "highway": tags.get("highway", ""),
                    "name": tags.get("name", "")
                })
    return roads


# =====================================================================
# FEATURE EXTRACTION WITH ISOLATION SCORING
# =====================================================================
def _extract_and_score(data: dict, mode: str, min_isolation_km: float) -> list:
    """Extract features, compute nearest-neighbor distances, filter by isolation."""
    elements = data.get("elements", [])

    # Collect all structures with coordinates
    raw = []
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat, lon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            center = el.get("center", {})
            if "lat" in center and "lon" in center:
                lat, lon = center["lat"], center["lon"]
            else:
                nodes = el.get("nodes", [])
                coords = [node_lookup[n] for n in nodes if n in node_lookup]
                if coords:
                    lat = sum(c[0] for c in coords) / len(coords)
                    lon = sum(c[1] for c in coords) / len(coords)
        if lat is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed Structure"))
        raw.append({
            "name": name, "lat": lat, "lon": lon,
            "osm_id": el.get("id"),
            "tags": tags,
            "historic": tags.get("historic", ""),
            "building": tags.get("building", ""),
            "amenity": tags.get("amenity", ""),
            "description": tags.get("description", ""),
            "heritage": tags.get("heritage", ""),
        })

    if not raw:
        return []

    # Compute nearest-neighbor distance for each structure
    for i, s in enumerate(raw):
        min_dist = float("inf")
        for j, other in enumerate(raw):
            if i == j:
                continue
            d = _haversine_km(s["lat"], s["lon"], other["lat"], other["lon"])
            if d < min_dist:
                min_dist = d
        if min_dist == float("inf"):
            min_dist = 999.0  # Safe fallback if it's the only structure
        s["isolation_km"] = round(min_dist, 3)

    # Filter by minimum isolation distance and sort by most isolated first
    filtered = [s for s in raw if s["isolation_km"] >= min_isolation_km]
    filtered.sort(key=lambda x: x["isolation_km"], reverse=True)

    # Color gradient: more isolated = more intense red
    # Handle the edge case where max_iso is extremely large or 0
    max_iso = max((s["isolation_km"] for s in filtered), default=1)
    if max_iso == float("inf") or max_iso == 0:
        max_iso = 1.0
    for s in filtered:
        ratio = min(s["isolation_km"] / max(max_iso, 0.01), 1.0)
        # From dark red (#7f1d1d) to bright red (#ef4444)
        r = int(127 + ratio * 112)
        g = int(29 + ratio * (68 - 29) * (1 - ratio))
        b = int(29 + ratio * (68 - 29) * (1 - ratio))
        s["color"] = f"#{r:02x}{g:02x}{b:02x}"

    return filtered[:200]  # Cap at 200 results


# =====================================================================
# POPUP BUILDER
# =====================================================================
def _popup(f: dict) -> str:
    """Dark-themed popup for isolated structures."""
    name = html_module.escape(str(f["name"]))
    iso = f["isolation_km"]
    desc = html_module.escape(str(f.get("description", ""))[:120])
    hist = html_module.escape(str(f.get("historic", "")))
    bld = html_module.escape(str(f.get("building", "")))
    lines = f"<b style='color:#ef4444;'>{name}</b><br>"
    lines += (f"<span style='color:#fca5a5;font-weight:bold;'>"
              f"Isolation: {iso:.2f} km</span><br>")
    if hist:
        lines += f"<span style='color:{_TEXT2};'>Historic: </span>{hist}<br>"
    if bld and bld != "yes":
        lines += f"<span style='color:{_TEXT2};'>Type: </span>{bld}<br>"
    if desc:
        lines += f"<span style='color:{_TEXT2};font-size:0.8em;'>{desc}</span><br>"
    lines += (f"<span style='color:#5a6580;font-size:0.75em;'>"
              f"{f['lat']:.5f}, {f['lon']:.5f}</span>")
    return (f"<div style='min-width:220px;background:{_CARD};color:{_TEXT};"
            f"padding:10px;border-radius:8px;border:1px solid #ef4444;'>"
            f"{lines}</div>")


# =====================================================================
# MAP BUILDER
# =====================================================================
def _build_map(features: list, center: list, zoom: int, roads: list = None):
    """Build a dark folium map with red markers scaled by isolation."""
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter")
    
    if roads:
        fg_roads = folium.FeatureGroup(name="Roads Context", show=True)
        for r in roads:
            name = html_module.escape(r.get("name", "") or r.get("highway", "road"))
            folium.CircleMarker(
                location=[r["lat"], r["lon"]], radius=2,
                color="#5a6580", fill=True, fill_color="#5a6580",
                fill_opacity=0.6, weight=1,
                tooltip=f"Road: {name}"
            ).add_to(fg_roads)
        fg_roads.add_to(m)

    for f in features:
        radius = min(4 + f["isolation_km"] * 2, 14)
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=radius,
            color=f["color"], fill=True, fill_color=f["color"],
            fill_opacity=0.85, weight=2,
            popup=folium.Popup(_popup(f), max_width=320),
            tooltip=html_module.escape(str(f["name"])),
        ).add_to(m)
    return m


# =====================================================================
# MAIN RENDER
# =====================================================================
def render_isolated_buildings_maps_tab():
    """Render the Regional Isolated Buildings Scanner tab."""

    header_html = (
        '<div class="tab-header pink">'
        '<h4>🏚️ Local Region Isolated Buildings Scanner</h4>'
        '<p>Scan any specific forest, desert or local region perfectly. '
        'This fetches EVERY single building in the search radius and calculates '
        'its extreme isolation from its neighbors.</p></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Mode selection
    mode = st.selectbox("Exploration Mode", MAP_MODES, key="local_iso_mode")
    cfg = MODE_CONFIG[mode]
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(cfg['desc'])}</p>",
        unsafe_allow_html=True,
    )

    # Location controls
    st.markdown("#### Search Parameters")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lat = st.number_input("Latitude", value=cfg["preset"]["lat"],
                              format="%.4f", min_value=-90.0,
                              max_value=90.0, key="local_iso_lat")
    with c2:
        lon = st.number_input("Longitude", value=cfg["preset"]["lon"],
                              format="%.4f", min_value=-180.0,
                              max_value=180.0, key="local_iso_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, 50,
                           cfg["preset"]["radius"], key="local_iso_rad")

    # Isolation threshold
    min_iso = st.slider(
        "Minimum isolation distance (km)",
        0.1, 10.0, 0.5, 0.1,
        key="local_iso_min_iso",
        help="Only show structures at least this far from the nearest other structure."
    )

    preset = st.selectbox("Preset Locations", list(PRESETS.keys()),
                          key="local_iso_preset")
    if preset != "Custom" and PRESETS[preset]:
        p = PRESETS[preset]
        lat, lon, radius = p["lat"], p["lon"], p["radius"]

    if st.button("🔍 Scan for Isolated Buildings", key="local_iso_go", type="primary",
                 use_container_width=True):
        st.session_state.local_iso_params = {
            "lat": lat, "lon": lon, "radius": radius,
            "mode": mode, "min_iso": min_iso,
        }

    if "local_iso_params" not in st.session_state:
        st.info("Choose a local mode and specific coordinates/radius, then click Scan.")
        return

    hp = st.session_state.local_iso_params

    # Fetch and process data
    with st.spinner(f"Scanning {hp['mode']} in the local forest/region via OpenStreetMap..."):
        data = _search_structures(hp["lat"], hp["lon"], hp["radius"], hp["mode"])
        features = _extract_and_score(data, hp["mode"], hp["min_iso"])
        
        st.toast("Fetching roads context...")
        roads_data = _search_roads_for_context(hp["lat"], hp["lon"], hp["radius"])

    if not features:
        st.warning("No isolated structures found. Try a larger radius, "
                   "smaller isolation threshold, or different mode.")
        return

    # ── Stats ──
    st.markdown("---")
    st.markdown("#### Local Discovery Results")
    isolations = [f["isolation_km"] for f in features]
    cols = st.columns(5)
    cols[0].metric("Isolated Structures", len(features))
    cols[1].metric("Most Isolated", f"{max(isolations):.2f} km")
    cols[2].metric("Avg Isolation", f"{sum(isolations)/len(isolations):.2f} km")
    cols[3].metric("Named", sum(1 for f in features if f["name"] != "Unnamed Structure"))
    cols[4].metric("Search Radius", f"{hp['radius']} km")

    # ── Map ──
    st.markdown("---")
    st.markdown(
        f"<span style='color:#ef4444;font-weight:600;'>"
        f"● {html_module.escape(hp['mode'])}</span>"
        f" — <span style='color:{_TEXT2};'>larger markers = more isolated</span>",
        unsafe_allow_html=True,
    )
    zoom = cfg["preset"]["zoom"]
    m = _build_map(features, [hp["lat"], hp["lon"]], zoom, roads=roads_data)
    folium.Circle(
        location=[hp["lat"], hp["lon"]],
        radius=hp["radius"] * 1000,
        color="#ef4444", fill=True, fill_opacity=0.04, weight=1,
    ).add_to(m)
    st_html(m._repr_html_(), height=550)

    # ── Top 10 most isolated ──
    st.markdown("---")
    st.markdown("#### 🏆 Top 10 Most Isolated Locally")
    for i, f in enumerate(features[:10]):
        badge = ""
        if f.get("historic"):
            badge = f" <span style='color:#f59e0b;font-size:0.7rem;'>HISTORIC</span>"
        if f.get("heritage"):
            badge += f" <span style='color:#a855f7;font-size:0.7rem;'>HERITAGE</span>"
        st.markdown(
            f'<div style="display:flex;align-items:center;margin:6px 0;'
            f'background:{_CARD};border:1px solid #ef4444;border-radius:8px;padding:8px;">'
            f'<span style="color:#ef4444;font-weight:bold;font-size:1.2em;'
            f'min-width:30px;text-align:center;">{i+1}</span>'
            f'<div style="margin-left:10px;">'
            f'<div style="color:{_TEXT};font-weight:600;">'
            f'{html_module.escape(f["name"])}{badge}</div>'
            f'<div style="color:#fca5a5;font-size:0.85em;">'
            f'Isolation: {f["isolation_km"]:.2f} km</div>'
            f'<div style="color:{_TEXT2};font-size:0.75em;">'
            f'{f["lat"]:.5f}, {f["lon"]:.5f}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # ── Data table ──
    st.markdown("---")
    rows = [{
        "Name": f["name"], "Latitude": round(f["lat"], 5),
        "Longitude": round(f["lon"], 5),
        "Isolation (km)": f["isolation_km"],
        "Historic": f.get("historic", ""),
        "Building Type": f.get("building", ""),
        "Heritage": f.get("heritage", ""),
        "Description": f.get("description", ""),
        "OSM ID": f.get("osm_id", ""),
    } for f in features]
    df = pd.DataFrame(rows)
    with st.expander(f"Full Data Table ({len(df)} structures)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Isolation histogram ──
    st.markdown("#### Isolation Distance Distribution")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 3))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")
    ax.hist(isolations, bins=20, color="#ef4444", alpha=0.8, edgecolor="#7f1d1d")
    ax.set_xlabel("Isolation Distance (km)", color="#8b97b0", fontsize=10)
    ax.set_ylabel("Count", color="#8b97b0", fontsize=10)
    ax.tick_params(colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, axis="y", color="#2a3550", linewidth=0.5, alpha=0.5)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Download ──
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(rows)} Isolated Structures (CSV)",
        data=buf.getvalue(),
        file_name=f"local_isolated_structures_{hp['mode'].lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="local_iso_dl",
    )
