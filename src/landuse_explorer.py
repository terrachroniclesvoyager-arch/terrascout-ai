"""
Land Use & Urban Explorer module for TerraScout AI.
Uses the Overpass API (free) and Copernicus/ESA tile layers to explore
land use patterns, urban areas, green spaces, industrial zones, and
infrastructure from OpenStreetMap.
"""

import io
import math
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

# Land use categories from OSM
LANDUSE_CATEGORIES = {
    "Residential": {"tag": "landuse=residential", "color": "#f59e0b", "desc": "Residential areas"},
    "Commercial": {"tag": "landuse=commercial", "color": "#8b5cf6", "desc": "Shops, offices, businesses"},
    "Industrial": {"tag": "landuse=industrial", "color": "#ef4444", "desc": "Factories, warehouses"},
    "Farmland": {"tag": "landuse=farmland", "color": "#10b981", "desc": "Agricultural land"},
    "Forest": {"tag": "landuse=forest", "color": "#059669", "desc": "Managed forests"},
    "Park / Green": {"tag": "leisure=park", "color": "#22c55e", "desc": "Public parks, gardens"},
    "Cemetery": {"tag": "landuse=cemetery", "color": "#64748b", "desc": "Cemeteries"},
    "Construction": {"tag": "landuse=construction", "color": "#f97316", "desc": "Active construction sites"},
    "Military": {"tag": "landuse=military", "color": "#dc2626", "desc": "Military installations"},
    "Railway": {"tag": "landuse=railway", "color": "#6366f1", "desc": "Railway infrastructure"},
    "Retail": {"tag": "landuse=retail", "color": "#ec4899", "desc": "Shopping centers, retail areas"},
    "Meadow": {"tag": "landuse=meadow", "color": "#84cc16", "desc": "Grassland, meadows"},
    "Vineyard": {"tag": "landuse=vineyard", "color": "#a855f7", "desc": "Vineyards, wine production"},
    "Orchard": {"tag": "landuse=orchard", "color": "#16a34a", "desc": "Fruit orchards"},
    "Quarry": {"tag": "landuse=quarry", "color": "#78716c", "desc": "Quarries, mining"},
}

# Presets
LANDUSE_PRESETS = {
    "Custom": None,
    "Rome - Historic Center": {"lat": 41.8967, "lon": 12.4822, "radius": 3},
    "Milan - Urban Core": {"lat": 45.4642, "lon": 9.1900, "radius": 5},
    "Florence - Tuscany": {"lat": 43.7696, "lon": 11.2558, "radius": 5},
    "Paris - Central": {"lat": 48.8566, "lon": 2.3522, "radius": 4},
    "Amsterdam - Center": {"lat": 52.3676, "lon": 4.9041, "radius": 3},
    "Barcelona - Eixample": {"lat": 41.3874, "lon": 2.1686, "radius": 3},
    "Tokyo - Central": {"lat": 35.6762, "lon": 139.6503, "radius": 3},
    "New York - Manhattan": {"lat": 40.7831, "lon": -73.9712, "radius": 3},
    "Rural Tuscany - Chianti": {"lat": 43.4500, "lon": 11.2500, "radius": 10},
    "Dutch Countryside": {"lat": 52.1500, "lon": 5.3800, "radius": 8},
}


@st.cache_data(ttl=600)
def search_landuse(south: float, west: float, north: float, east: float,
                   categories: list) -> dict:
    """Search land use features via Overpass API."""
    bbox_str = f"{south},{west},{north},{east}"

    query_parts = []
    for cat in categories:
        cat_info = LANDUSE_CATEGORIES.get(cat)
        if not cat_info:
            continue
        key, value = cat_info["tag"].split("=")
        query_parts.append(f'way["{key}"="{value}"]({bbox_str});')
        query_parts.append(f'relation["{key}"="{value}"]({bbox_str});')

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


def _extract_landuse_features(data: dict) -> list:
    """Extract land use features from Overpass response."""
    elements = data.get("elements", [])

    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    seen_ids = set()

    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        el_id = el.get("id")
        if el_id in seen_ids:
            continue
        seen_ids.add(el_id)

        lat, lon = None, None
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

        if lat is None or lon is None:
            continue

        # Determine category
        category = "Unknown"
        color = "#8b97b0"
        for cat_name, cat_info in LANDUSE_CATEGORIES.items():
            key, value = cat_info["tag"].split("=")
            if tags.get(key) == value:
                category = cat_name
                color = cat_info["color"]
                break

        name = tags.get("name", tags.get("name:en", ""))

        features.append({
            "name": name if name else f"{category} area",
            "category": category,
            "color": color,
            "lat": lat,
            "lon": lon,
            "coords": coords_list,
            "tags": tags,
            "osm_id": el_id,
        })

    return features


def render_landuse_explorer_tab():
    """Main render function for the Land Use Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>Land Use & Urban Explorer</h4>
        <p>Analyze land use patterns from OpenStreetMap &mdash; residential, commercial, industrial, agricultural, and green areas with spatial statistics.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Search Parameters
    # ══════════════════════════════════════════
    st.markdown("#### Search Parameters")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        lu_lat = st.number_input("Center Latitude", value=41.8967, format="%.4f",
                                 min_value=-90.0, max_value=90.0, key="lu_lat")
    with col2:
        lu_lon = st.number_input("Center Longitude", value=12.4822, format="%.4f",
                                 min_value=-180.0, max_value=180.0, key="lu_lon")
    with col3:
        lu_radius = st.slider("Radius (km)", 1, 30, 5, key="lu_radius",
                               help="Search radius (keep small for faster results)")

    preset_name = st.selectbox("Interesting Areas", list(LANDUSE_PRESETS.keys()),
                               key="lu_preset")
    if preset_name != "Custom" and LANDUSE_PRESETS.get(preset_name):
        p = LANDUSE_PRESETS[preset_name]
        lu_lat = p["lat"]
        lu_lon = p["lon"]
        lu_radius = p["radius"]

    # Category selection
    st.markdown("##### Land Use Categories")
    selected_cats = st.multiselect(
        "Select land use types to search",
        list(LANDUSE_CATEGORIES.keys()),
        default=["Residential", "Commercial", "Industrial", "Farmland", "Forest", "Park / Green"],
        key="lu_cats",
    )

    if st.button("Analyze Land Use", key="lu_search", width="stretch"):
        dlat = lu_radius / 111.0
        dlon = lu_radius / (111.0 * max(0.01, abs(math.cos(math.radians(lu_lat)))))
        st.session_state.lu_params = {
            "lat": lu_lat, "lon": lu_lon, "radius": lu_radius,
            "south": lu_lat - dlat, "west": lu_lon - dlon,
            "north": lu_lat + dlat, "east": lu_lon + dlon,
            "cats": selected_cats,
        }

    if "lu_params" not in st.session_state:
        st.info("Select a location and land use categories, then click Analyze to explore land use patterns.")
        return

    lp = st.session_state.lu_params

    # ══════════════════════════════════════════
    # SECTION 2: Results Overview
    # ══════════════════════════════════════════
    with st.spinner("Analyzing land use via OpenStreetMap..."):
        data = search_landuse(lp["south"], lp["west"], lp["north"], lp["east"], lp["cats"])
        features = _extract_landuse_features(data)

    if not features:
        st.warning("No land use data found. Try a larger radius or different categories.")
        return

    st.markdown("---")
    st.markdown("#### Land Use Overview")

    cat_counts = {}
    for f in features:
        cat = f["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Top metrics
    total = len(features)
    dominant = max(cat_counts, key=cat_counts.get) if cat_counts else "—"
    urban_count = sum(cat_counts.get(c, 0) for c in ["Residential", "Commercial", "Industrial", "Retail"])
    green_count = sum(cat_counts.get(c, 0) for c in ["Farmland", "Forest", "Park / Green", "Meadow", "Vineyard", "Orchard"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Zones", total)
    with c2:
        st.metric("Dominant Type", dominant[:15])
    with c3:
        st.metric("Urban Zones", urban_count)
    with c4:
        st.metric("Green Zones", green_count)

    # ══════════════════════════════════════════
    # SECTION 3: Land Use Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Land Use Map")

    # Legend
    legend_items = " ".join([
        f'<span style="color:{LANDUSE_CATEGORIES[c]["color"]}; font-size:0.8rem;">● {c}</span>'
        for c in cat_counts.keys()
        if c in LANDUSE_CATEGORIES
    ])
    st.markdown(f'<div style="display:flex; gap:0.7rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
                unsafe_allow_html=True)

    m = folium.Map(location=[lp["lat"], lp["lon"]], zoom_start=13, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    # Search area
    folium.Circle(
        location=[lp["lat"], lp["lon"]],
        radius=lp["radius"] * 1000,
        color="#06b6d4",
        fill=True,
        fill_opacity=0.03,
        weight=1,
    ).add_to(m)

    # Land use polygons
    for f in features[:500]:
        popup = f"<strong>{f['name']}</strong><br/>{f['category']}"

        if f["coords"] and len(f["coords"]) >= 3:
            folium.Polygon(
                locations=[(c[0], c[1]) for c in f["coords"]],
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.35,
                weight=1,
                popup=folium.Popup(popup, max_width=200),
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=5,
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.6,
                weight=1,
                popup=folium.Popup(popup, max_width=200),
            ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 4: Analysis & Charts
    # ══════════════════════════════════════════
    st.markdown("---")

    col_chart, col_details = st.columns([1, 1])

    with col_chart:
        st.markdown("#### Land Use Distribution")

        if cat_counts:
            # Pie chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            fig.patch.set_facecolor("#0a0e1a")

            cats = list(cat_counts.keys())
            counts = list(cat_counts.values())
            colors = [LANDUSE_CATEGORIES.get(c, {}).get("color", "#8b97b0") for c in cats]

            # Pie
            ax1.set_facecolor("#0a0e1a")
            wedges, texts, autotexts = ax1.pie(
                counts, labels=None, colors=colors,
                autopct='%1.0f%%', pctdistance=0.75,
                textprops={'color': '#e8ecf4', 'fontsize': 8}
            )
            ax1.set_title("Proportions", color="#e8ecf4", fontsize=11, fontweight="bold")

            # Bar
            ax2.set_facecolor("#0a0e1a")
            ax2.barh(range(len(cats)), counts, color=colors, alpha=0.8)
            ax2.set_yticks(range(len(cats)))
            ax2.set_yticklabels([c[:18] for c in cats], color="#8b97b0", fontsize=9)
            ax2.set_xlabel("Count", color="#8b97b0", fontsize=10)
            ax2.tick_params(axis="x", colors="#8b97b0", labelsize=9)
            ax2.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
            ax2.set_axisbelow(True)
            for spine in ax2.spines.values():
                spine.set_color("#2a3550")
            ax2.invert_yaxis()
            ax2.set_title("Counts", color="#e8ecf4", fontsize=11, fontweight="bold")

            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    with col_details:
        st.markdown("#### Category Details")
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            info = LANDUSE_CATEGORIES.get(cat, {"color": "#8b97b0", "desc": ""})
            pct = (count / total * 100) if total > 0 else 0
            st.markdown(f"""
            <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
                <div style="width:10px; height:40px; border-radius:5px; background:{info['color']};
                            margin-right:0.75rem; flex-shrink:0;"></div>
                <div style="flex:1;">
                    <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{cat}</div>
                    <div style="color:#8b97b0; font-size:0.75rem;">{info.get('desc', '')}</div>
                </div>
                <div style="text-align:right; margin-left:0.5rem;">
                    <div style="color:{info['color']}; font-weight:700; font-size:1.1rem;">{count}</div>
                    <div style="color:#5a6580; font-size:0.7rem;">{pct:.1f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

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
            "osm_id": f.get("osm_id", ""),
        })

    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} zones)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Land Use Zones (CSV)",
        data=csv_buf.getvalue(),
        file_name="landuse_data.csv",
        mime="text/csv",
        key="lu_download",
    )
