"""
Archaeological & Heritage Explorer module for TerraScout AI.
Uses the Overpass API to find archaeological sites, historical monuments,
and cultural heritage features from OpenStreetMap.
Also integrates with OpenStreetMap's comprehensive tagging of heritage sites.
"""

import io
import html as html_module
from urllib.parse import quote as url_quote

import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

# Heritage/archaeology categories and their OSM tags
HERITAGE_CATEGORIES = {
    "Archaeological Sites": {
        "tag": "historic=archaeological_site",
        "color": "#f59e0b",
        "icon": "monument",
    },
    "Castles & Fortifications": {
        "tag": "historic=castle",
        "color": "#8b5cf6",
        "icon": "tower",
    },
    "Ruins": {
        "tag": "historic=ruins",
        "color": "#ef4444",
        "icon": "ruins",
    },
    "Monuments": {
        "tag": "historic=monument",
        "color": "#06b6d4",
        "icon": "monument",
    },
    "Churches & Religious": {
        "tag": "amenity=place_of_worship",
        "color": "#10b981",
        "icon": "church",
    },
    "Museums": {
        "tag": "tourism=museum",
        "color": "#ec4899",
        "icon": "museum",
    },
    "Memorials": {
        "tag": "historic=memorial",
        "color": "#38bdf8",
        "icon": "memorial",
    },
    "Historic Buildings": {
        "tag": "historic=building",
        "color": "#f97316",
        "icon": "building",
    },
    "Ancient City Walls": {
        "tag": "historic=city_gate",
        "color": "#a855f7",
        "icon": "gate",
    },
    "Tombs & Cemeteries": {
        "tag": "historic=tomb",
        "color": "#64748b",
        "icon": "tomb",
    },
}

from src.overpass_client import query_overpass

# Predefined interesting areas for archaeology
PRESETS = {
    "Custom": None,
    "Rome - Historic Center": {"lat": 41.8933, "lon": 12.4829, "radius": 3},
    "Athens - Acropolis Area": {"lat": 37.9715, "lon": 23.7267, "radius": 3},
    "Cairo - Pyramids & Old City": {"lat": 29.9792, "lon": 31.1342, "radius": 10},
    "Pompeii & Herculaneum": {"lat": 40.7509, "lon": 14.4869, "radius": 5},
    "Jerusalem - Old City": {"lat": 31.7767, "lon": 35.2345, "radius": 2},
    "Istanbul - Historic": {"lat": 41.0082, "lon": 28.9784, "radius": 3},
    "Agrigento - Valley of Temples": {"lat": 37.2906, "lon": 13.5886, "radius": 3},
    "Stonehenge Area": {"lat": 51.1789, "lon": -1.8262, "radius": 5},
    "Tulum - Mayan Ruins": {"lat": 20.2145, "lon": -87.4291, "radius": 5},
    "Angkor Wat Area": {"lat": 13.4125, "lon": 103.8670, "radius": 10},
    "Petra, Jordan": {"lat": 30.3285, "lon": 35.4444, "radius": 5},
    "Machu Picchu Area": {"lat": -13.1631, "lon": -72.5450, "radius": 5},
}


@st.cache_data(ttl=600)
def search_heritage(lat: float, lon: float, radius_km: float,
                    categories: list) -> dict:
    """Search heritage features via Overpass API."""
    # Build Overpass query for multiple categories
    radius_m = radius_km * 1000

    tag_queries = []
    for cat in categories:
        cat_info = HERITAGE_CATEGORIES.get(cat)
        if not cat_info:
            continue
        tag = cat_info["tag"]
        key, value = tag.split("=")
        tag_queries.append(f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});')
        tag_queries.append(f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});')

    if not tag_queries:
        return {"elements": []}

    all_queries = "\n  ".join(tag_queries)
    query = f"""
[out:json][timeout:60];
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
        st.error(f"All Overpass servers failed: {err}. Try a smaller radius or retry later.")
        return {"elements": []}
    return result


def _extract_features(data: dict) -> list:
    """Extract features with coordinates from Overpass response."""
    elements = data.get("elements", [])

    # Build node lookup for way resolution
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

        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1])
                      for n in nodes if n in node_lookup]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)

        if lat is None or lon is None:
            continue

        # Determine category
        category = "Unknown"
        color = "#8b97b0"
        for cat_name, cat_info in HERITAGE_CATEGORIES.items():
            key, value = cat_info["tag"].split("=")
            if tags.get(key) == value:
                category = cat_name
                color = cat_info["color"]
                break

        name = tags.get("name", tags.get("name:en", tags.get("name:it", "Unnamed")))
        features.append({
            "name": name,
            "category": category,
            "color": color,
            "lat": lat,
            "lon": lon,
            "tags": tags,
            "osm_id": el.get("id"),
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
            "heritage": tags.get("heritage", ""),
            "historic": tags.get("historic", ""),
            "description": tags.get("description", tags.get("description:en", "")),
        })

    return features


def render_archaeology_tab():
    """Main render function for the Archaeological Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header pink">
        <h4>Archaeological & Heritage Explorer</h4>
        <p>Discover archaeological sites, ruins, castles, monuments, and cultural heritage features from OpenStreetMap's comprehensive global database.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Search Parameters
    # ══════════════════════════════════════════
    st.markdown("#### Search Parameters")

    # Location
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        arch_lat = st.number_input("Latitude", value=41.8933, format="%.4f",
                                   min_value=-90.0, max_value=90.0, key="arch_lat")
    with col2:
        arch_lon = st.number_input("Longitude", value=12.4829, format="%.4f",
                                   min_value=-180.0, max_value=180.0, key="arch_lon")
    with col3:
        arch_radius = st.slider("Radius (km)", 1, 50, 5, key="arch_radius",
                                help="Search radius around center point")

    # Preset locations
    preset_name = st.selectbox("Famous Archaeological Areas", list(PRESETS.keys()),
                               key="arch_preset")
    if preset_name != "Custom" and PRESETS.get(preset_name):
        p = PRESETS[preset_name]
        arch_lat = p["lat"]
        arch_lon = p["lon"]
        arch_radius = p["radius"]

    # Category selection
    st.markdown("##### Categories to Search")
    selected_cats = st.multiselect(
        "Select heritage categories",
        list(HERITAGE_CATEGORIES.keys()),
        default=["Archaeological Sites", "Castles & Fortifications", "Ruins", "Monuments"],
        key="arch_cats",
    )

    if st.button("Explore Heritage", key="arch_search", width="stretch"):
        st.session_state.arch_params = {
            "lat": arch_lat, "lon": arch_lon,
            "radius": arch_radius, "cats": selected_cats,
        }

    if "arch_params" not in st.session_state:
        st.info("Select a location and categories, then click Explore to discover heritage sites.")
        return

    ap = st.session_state.arch_params

    # ══════════════════════════════════════════
    # SECTION 2: Results
    # ══════════════════════════════════════════
    with st.spinner("Searching heritage sites via OpenStreetMap..."):
        data = search_heritage(ap["lat"], ap["lon"], ap["radius"], ap["cats"])
        features = _extract_features(data)

    if not features:
        st.warning("No heritage sites found in this area. Try a larger radius or different categories.")
        return

    st.markdown("---")
    st.markdown("#### Discovery Overview")

    # Stats by category
    cat_counts = {}
    for f in features:
        cat = f["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    cols = st.columns(min(len(cat_counts) + 1, 5))
    cols[0].metric("Total Sites", len(features))
    for i, (cat, count) in enumerate(sorted(cat_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(cols):
            cols[i + 1].metric(cat[:20], count)

    # ══════════════════════════════════════════
    # SECTION 3: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Heritage Map")

    # Legend
    legend_items = " ".join([
        f'<span style="color:{info["color"]}; font-size:0.8rem;">● {name}</span>'
        for name, info in HERITAGE_CATEGORIES.items()
        if name in ap["cats"]
    ])
    st.markdown(f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
                unsafe_allow_html=True)

    m = folium.Map(location=[ap["lat"], ap["lon"]], zoom_start=13, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    # Search radius circle
    folium.Circle(
        location=[ap["lat"], ap["lon"]],
        radius=ap["radius"] * 1000,
        color="#06b6d4",
        fill=True,
        fill_opacity=0.03,
        weight=1,
    ).add_to(m)

    # Heritage markers
    for f in features:
        wiki_link = ""
        if f["wikipedia"]:
            lang, title = f["wikipedia"].split(":", 1) if ":" in f["wikipedia"] else ("en", f["wikipedia"])
            safe_lang = url_quote(lang, safe="")
            safe_title = url_quote(title, safe="")
            wiki_link = f'<br/><a href="https://{safe_lang}.wikipedia.org/wiki/{safe_title}" target="_blank" style="font-size:0.75rem;">Wikipedia</a>'

        safe_name = html_module.escape(str(f['name']))
        safe_category = html_module.escape(str(f['category']))
        safe_desc = html_module.escape(str(f.get('description', ''))[:100])

        popup_html = f"""
        <div style="max-width:220px;">
            <strong>{safe_name}</strong><br/>
            <span style="font-size:0.8rem; color:#666;">{safe_category}</span><br/>
            <span style="font-size:0.75rem;">{safe_desc}</span>
            {wiki_link}
        </div>
        """

        folium.CircleMarker(
            location=[f["lat"], f["lon"]],
            radius=6,
            color=f["color"],
            fill=True,
            fill_color=f["color"],
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 4: Site List & Details
    # ══════════════════════════════════════════
    st.markdown("---")

    col_sites, col_stats = st.columns([1, 1])

    with col_sites:
        st.markdown("#### Notable Sites")
        # Show sites with most tags/info first
        sorted_features = sorted(features, key=lambda x: len(x.get("tags", {})), reverse=True)

        for f in sorted_features[:20]:
            wiki_badge = ""
            if f["wikipedia"] or f["wikidata"]:
                wiki_badge = ' <span style="color:#3b82f6; font-size:0.7rem;">WIKI</span>'

            heritage_badge = ""
            if f["heritage"]:
                safe_heritage = html_module.escape(str(f["heritage"]))
                heritage_badge = f' <span style="color:#f59e0b; font-size:0.7rem;">HERITAGE {safe_heritage}</span>'

            safe_name = html_module.escape(str(f['name']))
            safe_category = html_module.escape(str(f['category']))
            safe_color = html_module.escape(str(f['color']))

            st.markdown(f"""
            <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
                <div style="width:10px; height:50px; border-radius:5px; background:{safe_color};
                            margin-right:0.75rem; flex-shrink:0;"></div>
                <div>
                    <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{safe_name}{wiki_badge}{heritage_badge}</div>
                    <div style="color:#8b97b0; font-size:0.75rem;">{safe_category}</div>
                    <div style="color:#5a6580; font-size:0.7rem;">{f['lat']:.4f}, {f['lon']:.4f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_stats:
        st.markdown("#### Category Breakdown")

        # Category chart
        if cat_counts:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#0a0e1a")

            cats = list(cat_counts.keys())
            counts = list(cat_counts.values())
            colors = [HERITAGE_CATEGORIES.get(c, {}).get("color", "#8b97b0") for c in cats]

            ax.barh(range(len(cats)), counts, color=colors, alpha=0.8)
            ax.set_yticks(range(len(cats)))
            ax.set_yticklabels([c[:25] for c in cats], color="#8b97b0", fontsize=9)
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
            "historic": f.get("historic", ""),
            "wikipedia": f.get("wikipedia", ""),
            "wikidata": f.get("wikidata", ""),
            "heritage": f.get("heritage", ""),
            "osm_id": f.get("osm_id", ""),
        })

    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Heritage Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name="heritage_sites.csv",
        mime="text/csv",
        key="arch_download",
    )
