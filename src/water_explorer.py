"""
Water & Hydrology Explorer module for TerraScout AI.
Uses the Overpass API (free) to discover water features: rivers, lakes,
reservoirs, springs, waterfalls, wetlands, and more from OpenStreetMap.
"""

import io
import streamlit as st
import json
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# Water feature categories
WATER_CATEGORIES = {
    "Rivers & Streams": {
        "tag": "waterway~river|stream|canal",
        "color": "#06b6d4",
        "query": '(way["waterway"~"river|stream|canal"]({bbox});)',
    },
    "Lakes & Ponds": {
        "tag": "natural=water",
        "color": "#3b82f6",
        "query": '(way["natural"="water"]({bbox}); relation["natural"="water"]({bbox});)',
    },
    "Reservoirs": {
        "tag": "water=reservoir",
        "color": "#8b5cf6",
        "query": '(way["water"="reservoir"]({bbox}); relation["water"="reservoir"]({bbox});)',
    },
    "Wetlands": {
        "tag": "natural=wetland",
        "color": "#10b981",
        "query": '(way["natural"="wetland"]({bbox}); relation["natural"="wetland"]({bbox});)',
    },
    "Springs": {
        "tag": "natural=spring",
        "color": "#06b6d4",
        "query": '(node["natural"="spring"]({bbox});)',
    },
    "Waterfalls": {
        "tag": "waterway=waterfall",
        "color": "#38bdf8",
        "query": '(node["waterway"="waterfall"]({bbox}); way["waterway"="waterfall"]({bbox});)',
    },
    "Dams": {
        "tag": "waterway=dam",
        "color": "#f59e0b",
        "query": '(way["waterway"="dam"]({bbox}); node["waterway"="dam"]({bbox});)',
    },
    "Drinking Water": {
        "tag": "amenity=drinking_water",
        "color": "#14b8a6",
        "query": '(node["amenity"="drinking_water"]({bbox});)',
    },
}

# Presets for interesting water areas
WATER_PRESETS = {
    "Custom": None,
    "Lake Garda, Italy": {"lat": 45.6, "lon": 10.65, "radius": 15},
    "Lake Como, Italy": {"lat": 46.0, "lon": 9.27, "radius": 10},
    "Venice Lagoon": {"lat": 45.44, "lon": 12.33, "radius": 8},
    "Swiss Lakes - Interlaken": {"lat": 46.69, "lon": 7.86, "radius": 15},
    "Amsterdam Canals": {"lat": 52.37, "lon": 4.90, "radius": 3},
    "Nile River - Cairo": {"lat": 30.04, "lon": 31.24, "radius": 10},
    "Amazon Basin": {"lat": -3.12, "lon": -60.02, "radius": 30},
    "Great Lakes - Niagara": {"lat": 43.08, "lon": -79.07, "radius": 15},
    "Danube - Budapest": {"lat": 47.50, "lon": 19.04, "radius": 8},
    "Seine - Paris": {"lat": 48.86, "lon": 2.35, "radius": 5},
}


@st.cache_data(ttl=600)
def search_water_features(south: float, west: float, north: float, east: float,
                           categories: list) -> dict:
    """Search water features via Overpass API."""
    bbox_str = f"{south},{west},{north},{east}"

    query_parts = []
    for cat in categories:
        cat_info = WATER_CATEGORIES.get(cat)
        if not cat_info:
            continue
        query_parts.append(cat_info["query"].replace("{bbox}", bbox_str))

    if not query_parts:
        return {"elements": []}

    all_queries = "\n  ".join(query_parts)
    query = f"""
[out:json][timeout:90];
(
  {all_queries}
);
out body;
>;
out skel qt;
"""

    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        st.error(f"All Overpass servers failed: {err}. Try a smaller area or retry later.")
        return {"elements": []}
    return result


def _extract_water_features(data: dict) -> list:
    """Extract water features from Overpass response."""
    elements = data.get("elements", [])

    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        lat, lon = None, None
        geom_type = "Point"
        coords_list = []

        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords_list = [(node_lookup[n][0], node_lookup[n][1])
                           for n in nodes if n in node_lookup]
            if coords_list:
                lat = sum(c[0] for c in coords_list) / len(coords_list)
                lon = sum(c[1] for c in coords_list) / len(coords_list)
                geom_type = "Polygon" if len(coords_list) > 3 and coords_list[0] == coords_list[-1] else "LineString"

        if lat is None or lon is None:
            continue

        # Determine category
        category = "Unknown"
        color = "#8b97b0"
        for cat_name, cat_info in WATER_CATEGORIES.items():
            tag_parts = cat_info["tag"].split("=")
            if len(tag_parts) == 2:
                key, val = tag_parts
                if "~" in key:
                    key = key.split("~")[0]
                if tags.get(key) and (val in tags.get(key, "") or "~" in cat_info["tag"]):
                    category = cat_name
                    color = cat_info["color"]
                    break
            # Fallback: check common water tags
            if tags.get("waterway") or tags.get("natural") in ["water", "wetland", "spring"] or tags.get("water"):
                if category == "Unknown":
                    ww = tags.get("waterway", "")
                    nat = tags.get("natural", "")
                    if ww in ["river", "stream", "canal"]:
                        category = "Rivers & Streams"
                        color = "#06b6d4"
                    elif nat == "water" or tags.get("water"):
                        category = "Lakes & Ponds"
                        color = "#3b82f6"
                    elif nat == "wetland":
                        category = "Wetlands"
                        color = "#10b981"
                    elif nat == "spring":
                        category = "Springs"
                        color = "#06b6d4"
                    elif ww == "waterfall":
                        category = "Waterfalls"
                        color = "#38bdf8"
                    elif ww == "dam":
                        category = "Dams"
                        color = "#f59e0b"

        name = tags.get("name", tags.get("name:en", tags.get("name:it", "Unnamed")))

        features.append({
            "name": name,
            "category": category,
            "color": color,
            "lat": lat,
            "lon": lon,
            "geom_type": geom_type,
            "coords": coords_list,
            "tags": tags,
            "osm_id": el.get("id"),
        })

    return features


def render_water_explorer_tab():
    """Main render function for the Water & Hydrology Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Water & Hydrology Explorer</h4>
        <p>Discover rivers, lakes, reservoirs, wetlands, springs, waterfalls, and other water features from OpenStreetMap's global database.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Search Parameters
    # ══════════════════════════════════════════
    st.markdown("#### Search Parameters")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        w_lat = st.number_input("Center Latitude", value=45.6000, format="%.4f",
                                min_value=-90.0, max_value=90.0, key="water_lat")
    with col2:
        w_lon = st.number_input("Center Longitude", value=10.6500, format="%.4f",
                                min_value=-180.0, max_value=180.0, key="water_lon")
    with col3:
        w_radius = st.slider("Radius (km)", 1, 50, 10, key="water_radius",
                              help="Search radius around center point")

    # Presets
    preset_name = st.selectbox("Interesting Water Locations", list(WATER_PRESETS.keys()),
                               key="water_preset")
    if preset_name != "Custom" and WATER_PRESETS.get(preset_name):
        p = WATER_PRESETS[preset_name]
        w_lat = p["lat"]
        w_lon = p["lon"]
        w_radius = p["radius"]

    # Category selection
    st.markdown("##### Water Feature Categories")
    selected_cats = st.multiselect(
        "Select water feature types to search",
        list(WATER_CATEGORIES.keys()),
        default=["Rivers & Streams", "Lakes & Ponds", "Springs", "Waterfalls"],
        key="water_cats",
    )

    if st.button("Explore Water Features", key="water_search", width="stretch"):
        import math
        dlat = w_radius / 111.0
        dlon = w_radius / (111.0 * max(0.01, abs(math.cos(math.radians(w_lat)))))
        st.session_state.water_params = {
            "lat": w_lat, "lon": w_lon, "radius": w_radius,
            "south": w_lat - dlat, "west": w_lon - dlon,
            "north": w_lat + dlat, "east": w_lon + dlon,
            "cats": selected_cats,
        }

    if "water_params" not in st.session_state:
        st.info("Select a location and water feature categories, then click Explore to discover water bodies.")
        return

    wp = st.session_state.water_params

    # ══════════════════════════════════════════
    # SECTION 2: Results
    # ══════════════════════════════════════════
    with st.spinner("Searching water features via OpenStreetMap..."):
        data = search_water_features(wp["south"], wp["west"], wp["north"], wp["east"], wp["cats"])
        features = _extract_water_features(data)

    if not features:
        st.warning("No water features found. Try a larger radius or different categories.")
        return

    st.markdown("---")
    st.markdown("#### Discovery Overview")

    # Stats by category
    cat_counts = {}
    for f in features:
        cat = f["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    cols = st.columns(min(len(cat_counts) + 1, 5))
    cols[0].metric("Total Features", len(features))
    for i, (cat, count) in enumerate(sorted(cat_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(cols):
            cols[i + 1].metric(cat[:18], count)

    # ══════════════════════════════════════════
    # SECTION 3: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Water Features Map")

    # Legend
    legend_items = " ".join([
        f'<span style="color:{info["color"]}; font-size:0.8rem;">● {name}</span>'
        for name, info in WATER_CATEGORIES.items()
        if name in wp["cats"]
    ])
    st.markdown(f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
                unsafe_allow_html=True)

    m = folium.Map(location=[wp["lat"], wp["lon"]], zoom_start=11, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    # Search area circle
    folium.Circle(
        location=[wp["lat"], wp["lon"]],
        radius=wp["radius"] * 1000,
        color="#06b6d4",
        fill=True,
        fill_opacity=0.03,
        weight=1,
    ).add_to(m)

    # Water feature markers/shapes
    for f in features:
        popup_html = f"""
        <div style="max-width:200px;">
            <strong>{f['name']}</strong><br/>
            <span style="font-size:0.85rem;">{f['category']}</span>
        </div>
        """

        if f["geom_type"] == "LineString" and f["coords"]:
            folium.PolyLine(
                locations=[(c[0], c[1]) for c in f["coords"]],
                color=f["color"],
                weight=3,
                opacity=0.7,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)
        elif f["geom_type"] == "Polygon" and f["coords"]:
            folium.Polygon(
                locations=[(c[0], c[1]) for c in f["coords"]],
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.3,
                weight=2,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=5,
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 4: Feature List & Stats
    # ══════════════════════════════════════════
    st.markdown("---")

    col_list, col_chart = st.columns([1, 1])

    with col_list:
        st.markdown("#### Named Water Features")
        named = [f for f in features if f["name"] != "Unnamed"]
        for f in named[:25]:
            st.markdown(f"""
            <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
                <div style="width:10px; height:40px; border-radius:5px; background:{f['color']};
                            margin-right:0.75rem; flex-shrink:0;"></div>
                <div>
                    <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{f['name']}</div>
                    <div style="color:#8b97b0; font-size:0.75rem;">{f['category']}</div>
                    <div style="color:#5a6580; font-size:0.7rem;">{f['lat']:.4f}, {f['lon']:.4f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if not named:
            st.info("No named water features found. Features may be unnamed in OpenStreetMap.")

    with col_chart:
        st.markdown("#### Category Distribution")
        if cat_counts:
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#0a0e1a")

            cats = list(cat_counts.keys())
            counts = list(cat_counts.values())
            colors = [WATER_CATEGORIES.get(c, {}).get("color", "#8b97b0") for c in cats]

            ax.barh(range(len(cats)), counts, color=colors, alpha=0.8)
            ax.set_yticks(range(len(cats)))
            ax.set_yticklabels([c[:22] for c in cats], color="#8b97b0", fontsize=9)
            ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
            ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
            ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")
            ax.invert_yaxis()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # ══════════════════════════════════════════
    # SECTION 5: Download
    # ══════════════════════════════════════════
    st.markdown("---")

    rows = []
    for f in features:
        rows.append({
            "name": f["name"],
            "category": f["category"],
            "latitude": f["lat"],
            "longitude": f["lon"],
            "geometry_type": f["geom_type"],
            "osm_id": f.get("osm_id", ""),
        })

    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} features)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Water Features (CSV)",
        data=csv_buf.getvalue(),
        file_name="water_features.csv",
        mime="text/csv",
        key="water_download",
    )
