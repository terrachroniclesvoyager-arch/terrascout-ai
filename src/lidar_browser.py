"""
LiDAR Browser module for Pocket GIS AI.
Search free LiDAR datasets from OpenTopography and USGS 3DEP.
"""

import html as html_module
import streamlit as st
import requests
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

OPENTOPO_API = "https://portal.opentopography.org/API/otCatalog"
USGS_TNM_API = "https://tnmaccess.nationalmap.gov/api/v1/products"


@st.cache_data(ttl=600)
def search_opentopography(min_lon: float, min_lat: float,
                           max_lon: float, max_lat: float) -> list:
    """Search OpenTopography catalog for LiDAR datasets in a bounding box."""
    params = {
        "minx": min_lon,
        "miny": min_lat,
        "maxx": max_lon,
        "maxy": max_lat,
        "detail": "true",
        "outputFormat": "json",
        "include_federated": "true",
    }
    try:
        resp = requests.get(OPENTOPO_API, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        datasets = data.get("Datasets", data) if isinstance(data, dict) else data
        if isinstance(datasets, list):
            return datasets
        return datasets if isinstance(datasets, list) else []
    except Exception as e:
        st.warning(f"OpenTopography API error: {e}")
        return []


@st.cache_data(ttl=600)
def search_usgs_3dep(min_lon: float, min_lat: float,
                      max_lon: float, max_lat: float) -> list:
    """Search USGS 3DEP for LiDAR point cloud products."""
    params = {
        "datasets": "Lidar Point Cloud (LPC)",
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "max": 50,
        "outputFormat": "JSON",
    }
    try:
        resp = requests.get(USGS_TNM_API, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        st.warning(f"USGS 3DEP API error: {e}")
        return []


def _render_opentopo_result(dataset: dict, idx: int):
    """Render a single OpenTopography dataset card."""
    name = dataset.get("Dataset", {}).get("name", dataset.get("name", "Unknown Dataset"))
    short_name = dataset.get("Dataset", {}).get("short_name", "")
    description = dataset.get("Dataset", {}).get("description", "")[:200]

    # Try to get metadata
    meta = dataset.get("Dataset", dataset)
    num_points = meta.get("num_points", meta.get("lidarNumReturns", "N/A"))
    area_km2 = meta.get("area", "N/A")
    date_collected = meta.get("date_collected_start", meta.get("dateCollectedStart", "N/A"))
    resolution = meta.get("resolution", "N/A")

    # Bounding box
    bbox = meta.get("spatial_extent", {})
    if not bbox:
        bbox = {
            "minX": meta.get("minx", ""),
            "minY": meta.get("miny", ""),
            "maxX": meta.get("maxx", ""),
            "maxY": meta.get("maxy", ""),
        }

    # Download URL
    download_url = meta.get("url", meta.get("downloadUrl", ""))

    safe_name = html_module.escape(str(name))
    safe_short_name = html_module.escape(str(short_name))
    safe_description = html_module.escape(str(description))
    safe_date_collected = html_module.escape(str(date_collected))
    st.markdown(f"""
    <div class="aurora-card" style="margin-bottom:0.75rem;">
        <div style="color:#e8ecf4; font-weight:600; font-size:0.95rem;">{safe_name}</div>
        <div style="color:#8b5cf6; font-size:0.75rem; margin:0.2rem 0;">{safe_short_name}</div>
        <div style="color:#8b97b0; font-size:0.8rem; margin-top:0.3rem;">{safe_description}...</div>
        <div style="display:flex; gap:1.5rem; margin-top:0.5rem; flex-wrap:wrap;">
            <span style="color:#5a6580; font-size:0.75rem;">Date: <strong style="color:#06b6d4;">{safe_date_collected}</strong></span>
            <span style="color:#5a6580; font-size:0.75rem;">Points: <strong style="color:#06b6d4;">{num_points}</strong></span>
            <span style="color:#5a6580; font-size:0.75rem;">Area: <strong style="color:#06b6d4;">{area_km2}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"Details - {name[:50]}", expanded=False):
        st.json(meta)
        if download_url:
            st.markdown(f"[Open Dataset Page]({download_url})")


def _render_usgs_result(item: dict, idx: int):
    """Render a single USGS 3DEP result card."""
    title = item.get("title", "Unknown")
    pub_date = item.get("publicationDate", "N/A")
    size = item.get("sizeInBytes", 0)
    size_mb = f"{size / 1024 / 1024:.1f} MB" if size else "N/A"
    download_url = item.get("downloadURL", "")
    format_type = item.get("format", "N/A")
    bbox = item.get("boundingBox", {})

    safe_title = html_module.escape(str(title[:80]))
    safe_pub_date = html_module.escape(str(pub_date))
    safe_format_type = html_module.escape(str(format_type))
    st.markdown(f"""
    <div class="aurora-card" style="margin-bottom:0.75rem;">
        <div style="color:#e8ecf4; font-weight:600; font-size:0.9rem;">{safe_title}</div>
        <div style="display:flex; gap:1.5rem; margin-top:0.4rem; flex-wrap:wrap;">
            <span style="color:#5a6580; font-size:0.75rem;">Published: <strong style="color:#06b6d4;">{safe_pub_date}</strong></span>
            <span style="color:#5a6580; font-size:0.75rem;">Size: <strong style="color:#06b6d4;">{size_mb}</strong></span>
            <span style="color:#5a6580; font-size:0.75rem;">Format: <strong style="color:#06b6d4;">{safe_format_type}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if download_url:
        with st.expander(f"Download - {title[:40]}"):
            st.markdown(f"[Download {format_type}]({download_url})")
            if bbox:
                st.markdown(f"**Bounding Box**: {bbox}")


def render_lidar_browser_tab():
    """Main render function for the LiDAR Browser tab."""

    # Header
    st.markdown("""
    <div class="tab-header violet">
        <h4>LiDAR Data Browser</h4>
        <p>Search free LiDAR point cloud datasets from OpenTopography and USGS 3DEP. Define a bounding box to find and download available data.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Search Parameters
    # ══════════════════════════════════════════
    st.markdown("#### Search Parameters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        min_lat = st.number_input("Min Latitude", value=37.0, format="%.4f",
                                   min_value=-90.0, max_value=90.0, key="lidar_min_lat")
    with col2:
        min_lon = st.number_input("Min Longitude", value=-122.5, format="%.4f",
                                   min_value=-180.0, max_value=180.0, key="lidar_min_lon")
    with col3:
        max_lat = st.number_input("Max Latitude", value=38.0, format="%.4f",
                                   min_value=-90.0, max_value=90.0, key="lidar_max_lat")
    with col4:
        max_lon = st.number_input("Max Longitude", value=-121.5, format="%.4f",
                                   min_value=-180.0, max_value=180.0, key="lidar_max_lon")

    # Quick area presets
    preset = st.selectbox("Quick Presets", [
        "Custom",
        "San Francisco Bay Area",
        "Grand Canyon, AZ",
        "Mount Rainier, WA",
        "Yellowstone, WY",
        "Alps - Mont Blanc",
        "Rome, Italy",
        "Tokyo, Japan",
    ], key="lidar_preset")

    presets_map = {
        "San Francisco Bay Area": (37.2, -122.6, 37.9, -121.7),
        "Grand Canyon, AZ": (35.9, -112.5, 36.3, -111.7),
        "Mount Rainier, WA": (46.7, -121.9, 46.9, -121.6),
        "Yellowstone, WY": (44.2, -111.2, 45.0, -109.8),
        "Alps - Mont Blanc": (45.7, 6.7, 45.9, 7.0),
        "Rome, Italy": (41.8, 12.3, 42.0, 12.6),
        "Tokyo, Japan": (35.5, 139.5, 35.8, 139.9),
    }

    if preset != "Custom" and preset in presets_map:
        min_lat, min_lon, max_lat, max_lon = presets_map[preset]

    # Search
    source = st.radio(
        "Data Source",
        ["Both", "OpenTopography", "USGS 3DEP"],
        horizontal=True,
        key="lidar_source",
    )

    if st.button("Search LiDAR Data", key="lidar_search", width="stretch"):
        st.session_state.lidar_search_params = {
            "min_lat": min_lat, "min_lon": min_lon,
            "max_lat": max_lat, "max_lon": max_lon,
            "source": source,
        }

    if "lidar_search_params" not in st.session_state:
        st.info("Define a bounding box and click Search to find LiDAR datasets.")
        return

    p = st.session_state.lidar_search_params

    # ══════════════════════════════════════════
    # SECTION 2: Search Area Preview
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Search Area Preview")
    m = folium.Map(
        location=[(p["min_lat"] + p["max_lat"]) / 2,
                   (p["min_lon"] + p["max_lon"]) / 2],
        zoom_start=8,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    # Search area rectangle
    folium.Rectangle(
        bounds=[[p["min_lat"], p["min_lon"]], [p["max_lat"], p["max_lon"]]],
        color="#06b6d4",
        fill=True,
        fill_opacity=0.1,
        weight=2,
        popup="Search Area",
    ).add_to(m)

    components.html(m._repr_html_(), height=400)

    # Fetch results
    ot_results = []
    usgs_results = []

    with st.spinner("Searching LiDAR databases..."):
        if p["source"] in ["Both", "OpenTopography"]:
            ot_results = search_opentopography(
                p["min_lon"], p["min_lat"], p["max_lon"], p["max_lat"]
            )
        if p["source"] in ["Both", "USGS 3DEP"]:
            usgs_results = search_usgs_3dep(
                p["min_lon"], p["min_lat"], p["max_lon"], p["max_lat"]
            )

    total = len(ot_results) + len(usgs_results)
    st.markdown(f"""
    <div style="margin:1rem 0;">
        <span class="counter-badge">Found {total} datasets</span>
        <span style="color:#8b97b0; font-size:0.85rem; margin-left:0.5rem;">
            (OpenTopography: {len(ot_results)} | USGS 3DEP: {len(usgs_results)})
        </span>
    </div>
    """, unsafe_allow_html=True)

    if total == 0:
        st.warning("No LiDAR datasets found in this area. Try a different location or expand the bounding box.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Dataset Results
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Available Datasets")
    tab_ot, tab_usgs = st.tabs([
        f"OpenTopography ({len(ot_results)})",
        f"USGS 3DEP ({len(usgs_results)})"
    ])

    with tab_ot:
        if ot_results:
            for idx, ds in enumerate(ot_results[:30]):
                _render_opentopo_result(ds, idx)
        else:
            st.info("No OpenTopography datasets found in this area.")

    with tab_usgs:
        if usgs_results:
            for idx, item in enumerate(usgs_results[:30]):
                _render_usgs_result(item, idx)
        else:
            st.info("No USGS 3DEP datasets found in this area.")
