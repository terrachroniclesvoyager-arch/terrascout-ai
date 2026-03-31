"""
Remote Structures & Deforestation Explorer for TerraScout AI.
Finds buildings, roads, airstrips, mines, logging, and camps in remote areas
(Amazon, Congo, Borneo, etc.) via Overpass API, and detects deforestation
alerts via the Global Forest Watch GLAD API.
All data sources are free and require no API key.
"""

import io
import math
import json
import html as html_module
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# Enhanced UI components
from src.ui_components import (
    success_banner, warning_banner, error_banner, info_card,
    section_header, stats_grid, enhanced_progress_bar
)

# NEW: Multi-source building detection
try:
    from src.remote_structures_db import RemoteStructuresDB
    MULTI_SOURCE_AVAILABLE = True
except ImportError:
    MULTI_SOURCE_AVAILABLE = False
    warning_banner("Multi-source detection not available. Install dependencies or use OSM Only mode.", "⚠️")

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Global Forest Watch GLAD alerts endpoint (free, no API key)
GFW_ALERTS_URL = (
    "https://data-api.globalforestwatch.org/dataset/"
    "gfw_integrated_alerts/latest/query"
)

# Sentinel-2 cloudless tiles for satellite base layer
SENTINEL2_TILES = (
    "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2021_3857"
    "/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg"
)

# ── Preset remote locations ──────────────────────────────────────────────────
PRESET_LOCATIONS = {
    "Custom": None,
    "Amazon (Manaus)": {
        "lat": -3.1, "lon": -60.0, "radius": 25,
        "desc": "Central Amazon basin near Manaus, Brazil",
    },
    "Amazon (Peru Border)": {
        "lat": -4.5, "lon": -71.5, "radius": 25,
        "desc": "Western Amazon, Peru-Colombia-Brazil tripoint",
    },
    "Congo Basin": {
        "lat": 1.5, "lon": 21.0, "radius": 25,
        "desc": "Central Africa rainforest, DRC",
    },
    "Borneo (Kalimantan)": {
        "lat": 0.5, "lon": 115.0, "radius": 25,
        "desc": "Indonesian Kalimantan, palm oil frontier",
    },
    "Papua New Guinea": {
        "lat": -6.0, "lon": 147.0, "radius": 25,
        "desc": "Highland and coastal forests of PNG",
    },
    "Madagascar": {
        "lat": -18.9, "lon": 47.5, "radius": 25,
        "desc": "Eastern rainforest corridor",
    },
}

# ── Structure categories with Overpass tags and colours ──────────────────────
FEATURE_CATEGORIES = {
    "Buildings": {
        "query": '["building"]',
        "color": "#f59e0b",
        "icon": "home",
    },
    "Roads & Tracks": {
        "query": '["highway"~"track|path|unclassified"]',
        "color": "#8b97b0",
        "icon": "road",
    },
    "Airstrips & Helipads": {
        "query": '["aeroway"~"aerodrome|runway|helipad"]',
        "color": "#ef4444",
        "icon": "plane",
    },
    "Mining & Extraction": {
        "query_multi": [
            '["landuse"="quarry"]',
            '["man_made"~"mineshaft|adit"]',
        ],
        "color": "#8b5cf6",
        "icon": "cog",
    },
    "Logging": {
        "query": '["landuse"="logging"]',
        "color": "#10b981",
        "icon": "tree",
    },
    "Camps": {
        "query_multi": [
            '["tourism"="camp_site"]',
            '["military"]',
        ],
        "color": "#ec4899",
        "icon": "tent",
    },
}

# ── 10 exploration modes ─────────────────────────────────────────────────────
EXPLORATION_MODES = [
    "All Structures",
    "Buildings & Settlements",
    "Roads & Access Tracks",
    "Airstrips & Helipads",
    "Mining & Extraction",
    "Logging & Deforestation",
    "Deforestation Alerts (GLAD)",
    "Infrastructure Overview",
    "Camp & Military Sites",
    "Custom Area Search",
]

# Map each mode to the categories it queries
MODE_CATEGORY_MAP = {
    "All Structures": list(FEATURE_CATEGORIES.keys()),
    "Buildings & Settlements": ["Buildings"],
    "Roads & Access Tracks": ["Roads & Tracks"],
    "Airstrips & Helipads": ["Airstrips & Helipads"],
    "Mining & Extraction": ["Mining & Extraction"],
    "Logging & Deforestation": ["Logging"],
    "Deforestation Alerts (GLAD)": [],
    "Infrastructure Overview": ["Buildings", "Roads & Tracks", "Airstrips & Helipads"],
    "Camp & Military Sites": ["Camps"],
    "Custom Area Search": list(FEATURE_CATEGORIES.keys()),
}


# ═══════════════════════════════════════════════════════════════════════════════
# API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_overpass_query(lat: float, lon: float, radius_km: float,
                          categories: list[str]) -> str:
    """Build an Overpass QL query for the selected categories within radius."""
    r = int(radius_km * 1000)
    parts = []
    for cat_name in categories:
        cat = FEATURE_CATEGORIES.get(cat_name)
        if not cat:
            continue
        if "query_multi" in cat:
            for q in cat["query_multi"]:
                parts.append(f'  nwr{q}(around:{r},{lat},{lon});')
        else:
            parts.append(f'  nwr{cat["query"]}(around:{r},{lat},{lon});')

    query = f"""[out:json][timeout:600][maxsize:2000000000];
(
{chr(10).join(parts)}
);
out center body;"""
    return query


def _classify_element(el: dict) -> tuple[str, str]:
    """Classify an OSM element into one of our categories. Returns (name, color)."""
    tags = el.get("tags", {})
    if tags.get("building"):
        return "Buildings", FEATURE_CATEGORIES["Buildings"]["color"]
    if tags.get("highway") in ("track", "path", "unclassified"):
        return "Roads & Tracks", FEATURE_CATEGORIES["Roads & Tracks"]["color"]
    if tags.get("aeroway") in ("aerodrome", "runway", "helipad"):
        return "Airstrips & Helipads", FEATURE_CATEGORIES["Airstrips & Helipads"]["color"]
    if tags.get("landuse") == "quarry" or tags.get("man_made") in ("mineshaft", "adit"):
        return "Mining & Extraction", FEATURE_CATEGORIES["Mining & Extraction"]["color"]
    if tags.get("landuse") == "logging":
        return "Logging", FEATURE_CATEGORIES["Logging"]["color"]
    if tags.get("tourism") == "camp_site" or tags.get("military"):
        return "Camps", FEATURE_CATEGORIES["Camps"]["color"]
    return "Other", "#06b6d4"


def _get_coords(el: dict) -> tuple:
    """Extract lat/lon from an OSM element (node, way center, relation center)."""
    if el["type"] == "node":
        return el.get("lat"), el.get("lon")
    center = el.get("center", {})
    return center.get("lat"), center.get("lon")


@st.cache_data(ttl=3600)
def _fetch_structures(lat: float, lon: float, radius_km: float,
                      categories: list[str]) -> tuple:
    """Fetch structures from Overpass API. Returns (DataFrame, error_or_None)."""
    if not categories:
        return pd.DataFrame(), "No categories selected"

    query = _build_overpass_query(lat, lon, radius_km, categories)
    try:
        data = query_overpass(query, timeout=300)
    except Exception as e:
        return pd.DataFrame(), str(e)

    if data is None or "_error" in data:
        err = data.get("_error", "Unknown error") if data else "No response"
        return pd.DataFrame(), err

    rows = []
    for el in data.get("elements", []):
        elat, elon = _get_coords(el)
        if elat is None or elon is None:
            continue
        cat, color = _classify_element(el)
        tags = el.get("tags", {})
        name = tags.get("name", tags.get("description", ""))
        rows.append({
            "category": cat,
            "color": color,
            "name": name,
            "latitude": elat,
            "longitude": elon,
            "osm_type": el["type"],
            "osm_id": el["id"],
            "tags_json": json.dumps(tags) if tags else "",
        })

    return pd.DataFrame(rows), None


@st.cache_data(ttl=3600)
def _fetch_glad_alerts(lat: float, lon: float, radius_km: float) -> tuple:
    """Fetch GLAD deforestation alerts from Global Forest Watch.
    Returns (DataFrame, error_or_None)."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.01, abs(math.cos(math.radians(lat)))))
    west, south = lon - dlon, lat - dlat
    east, north = lon + dlon, lat + dlat

    geojson_geom = json.dumps({
        "type": "Polygon",
        "coordinates": [[
            [west, south], [east, south],
            [east, north], [west, north],
            [west, south],
        ]],
    })

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    params = {
        "sql": (
            f"SELECT latitude, longitude, gfw_integrated_alerts__date, "
            f"gfw_integrated_alerts__confidence "
            f"FROM results "
            f"WHERE gfw_integrated_alerts__date >= '{cutoff}' "
            f"LIMIT 2000"
        ),
        "geostore_origin": "rw",
        "geometry": geojson_geom,
    }

    try:
        resp = requests.get(
            GFW_ALERTS_URL, params=params, timeout=45,
            headers={"User-Agent": "TerraScoutAI/1.0"},
        )
        if resp.status_code == 200:
            result = resp.json()
            rows = result.get("data", [])
            if rows:
                return pd.DataFrame(rows), None

        # Fallback: simpler query without date filter
        params_fallback = {
            "sql": (
                "SELECT latitude, longitude, gfw_integrated_alerts__date, "
                "gfw_integrated_alerts__confidence "
                "FROM results LIMIT 2000"
            ),
            "geostore_origin": "rw",
            "geometry": geojson_geom,
        }
        resp2 = requests.get(
            GFW_ALERTS_URL, params=params_fallback, timeout=45,
            headers={"User-Agent": "TerraScoutAI/1.0"},
        )
        if resp2.status_code == 200:
            result2 = resp2.json()
            rows2 = result2.get("data", [])
            if rows2:
                return pd.DataFrame(rows2), None

        return pd.DataFrame(), f"GLAD API returned status {resp.status_code}"
    except requests.exceptions.Timeout:
        return pd.DataFrame(), "GLAD API timed out (large area - try reducing radius)"
    except Exception as e:
        return pd.DataFrame(), str(e)


# ═══════════════════════════════════════════════════════════════════════════════
# MAP BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _build_map(center_lat: float, center_lon: float, radius_km: float,
               struct_df: pd.DataFrame, glad_df: pd.DataFrame | None = None,
               zoom: int = 10, max_markers: int = 15000) -> folium.Map:
    """Create a dark-themed folium map with structure markers and GLAD points."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles=None)

    # CartoDB dark_matter base
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    # Sentinel-2 cloudless satellite
    folium.TileLayer(
        tiles=SENTINEL2_TILES,
        attr="Sentinel-2 Cloudless (EOX)", name="Sentinel-2 Satellite",
        overlay=False,
    ).add_to(m)

    # Esri satellite fallback
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri", name="Esri Satellite", overlay=False,
    ).add_to(m)

    # Search radius circle
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius_km * 1000,
        color="#06b6d4", fill=False, weight=1.5,
        dash_array="6", opacity=0.5,
    ).add_to(m)

    # Structure markers (limit to max_markers for performance)
    if not struct_df.empty:
        fg_struct = folium.FeatureGroup(name="Structures")
        for _, row in struct_df.head(max_markers).iterrows():
            color = row.get("color", "#06b6d4")
            safe_name = html_module.escape(str(row.get("name", "")))
            safe_cat = html_module.escape(str(row["category"]))
            popup_html = (
                f'<div style="max-width:210px; font-size:0.85rem;">'
                f'<strong>{safe_cat}</strong><br/>'
                f'{f"<em>{safe_name}</em><br/>" if safe_name else ""}'
                f'<span style="font-size:0.75rem;">'
                f'{row["latitude"]:.5f}, {row["longitude"]:.5f}</span><br/>'
                f'<span style="font-size:0.7rem; color:#888;">'
                f'OSM {row["osm_type"]} #{row["osm_id"]}</span>'
                f'</div>'
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=5, color=color,
                fill=True, fill_color=color, fill_opacity=0.7, weight=1,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(fg_struct)
        fg_struct.add_to(m)

    # GLAD deforestation alert points
    if glad_df is not None and not glad_df.empty:
        fg_glad = folium.FeatureGroup(name="Deforestation Alerts")
        lat_col = next((c for c in glad_df.columns if "lat" in c.lower()), None)
        lon_col = next((c for c in glad_df.columns if "lon" in c.lower()), None)
        date_col = next((c for c in glad_df.columns if "date" in c.lower()), None)
        conf_col = next((c for c in glad_df.columns if "confidence" in c.lower()), None)

        if lat_col and lon_col:
            for _, row in glad_df.head(max_markers).iterrows():
                rlat, rlon = row[lat_col], row[lon_col]
                if pd.isna(rlat) or pd.isna(rlon):
                    continue
                alert_date = str(row.get(date_col, "Unknown")) if date_col else "Unknown"
                conf = str(row.get(conf_col, "Unknown")) if conf_col else "Unknown"

                # Color by confidence level
                if conf.lower() in ("high", "3"):
                    acolor = "#ef4444"
                elif conf.lower() in ("nominal", "2"):
                    acolor = "#f97316"
                else:
                    acolor = "#f59e0b"

                popup_html = (
                    f'<div style="max-width:190px; font-size:0.85rem;">'
                    f'<strong>Deforestation Alert</strong><br/>'
                    f'Date: {html_module.escape(alert_date)}<br/>'
                    f'Confidence: {html_module.escape(conf)}<br/>'
                    f'<span style="font-size:0.75rem;">'
                    f'{rlat:.5f}, {rlon:.5f}</span>'
                    f'</div>'
                )
                folium.CircleMarker(
                    location=[rlat, rlon], radius=4, color=acolor,
                    fill=True, fill_color=acolor, fill_opacity=0.65, weight=0.5,
                    popup=folium.Popup(popup_html, max_width=200),
                ).add_to(fg_glad)
        fg_glad.add_to(m)

    folium.LayerControl().add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════════
# GEOJSON EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

def _to_geojson(df: pd.DataFrame) -> str:
    """Convert a structure DataFrame to a GeoJSON FeatureCollection string."""
    features = []
    for _, row in df.iterrows():
        props = {k: v for k, v in row.items()
                 if k not in ("latitude", "longitude", "color", "tags_json")}
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]],
            },
            "properties": props,
        })
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def render_remote_explorer_tab():
    """Main render function for the Remote Structures & Deforestation Explorer tab."""

    # ── Header ────────────────────────────────────────────────────────────
    section_header(
        "Remote Structures & Deforestation Explorer",
        "Find hidden structures & deforestation in Amazon, Congo, Borneo & remote areas worldwide",
        "🛰️"
    )

    # ══════════════════════════════════════════
    # SECTION 1 : Search Parameters
    # ══════════════════════════════════════════
    section_header("Search Parameters", "Configure your exploration area and detection mode", "🔍")

    # Preset location dropdown
    preset_name = st.selectbox(
        "Preset Remote Areas",
        list(PRESET_LOCATIONS.keys()),
        key="remote_preset",
    )

    default_lat, default_lon, default_radius = -3.1, -60.0, 25
    if preset_name != "Custom" and PRESET_LOCATIONS.get(preset_name):
        p = PRESET_LOCATIONS[preset_name]
        default_lat = p["lat"]
        default_lon = p["lon"]
        default_radius = p["radius"]
        st.markdown(
            f'<p style="color:#8b97b0; font-size:0.85rem;">'
            f'{html_module.escape(p["desc"])}</p>',
            unsafe_allow_html=True,
        )

    # Lat / Lon / Radius controls
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        rem_lat = st.number_input(
            "Latitude", value=default_lat, format="%.4f",
            min_value=-90.0, max_value=90.0, key="remote_lat",
        )
    with col2:
        rem_lon = st.number_input(
            "Longitude", value=default_lon, format="%.4f",
            min_value=-180.0, max_value=180.0, key="remote_lon",
        )
    with col3:
        rem_radius = st.slider(
            "Radius (km)", 5, 500, default_radius, step=5, key="remote_radius",
            help="Search radius around center point. Warning: queries over 100km may take very long or fail if there are too many structures.",
        )
        
    max_markers = st.slider(
        "Max Markers to Render", 1000, 50000, 15000, step=1000, key="remote_max_markers",
        help="Limits the number of points drawn on the map to prevent your browser from crashing/freezing."
    )

    # ── NEW: Multi-Source AI Detection Settings ──
    st.markdown("##### 🤖 AI-Powered Building Detection")

    data_source_mode = st.selectbox(
        "Data Source Strategy",
        [
            "Fast (OSM + Google AI)",
            "Comprehensive (OSM + Google + Microsoft)",
            "AI Only (Google + Microsoft)",
            "AI Live Detection (SAM2 Real-Time)",
            "OSM Only (Legacy)"
        ],
        index=0,
        key="remote_data_source",
        help="Fast: Quick scan with OSM + Google Open Buildings. "
             "Comprehensive: All sources including Microsoft (slower). "
             "AI Only: Only ML-detected buildings (no OSM). "
             "AI Live: Real-time SAM2 detection (most accurate, very slow). "
             "OSM Only: Original behavior (community-mapped only)."
    )

    col_size1, col_size2 = st.columns(2)
    with col_size1:
        min_building_size = st.slider(
            "Min Building Size (m²)",
            min_value=5,
            max_value=200,
            value=10,
            step=5,
            key="remote_min_size",
            help="Filter for small structures like huts, cabins, shelters. Lower = more sensitive."
        )
    with col_size2:
        max_building_size = st.slider(
            "Max Building Size (m²)",
            min_value=50,
            max_value=10000,
            value=10000,
            step=50,
            key="remote_max_size",
            help="Exclude large buildings. Set low (e.g., 50m²) to find only small remote structures."
        )

    # Exploration mode (10 modes)
    st.markdown("##### 🔍 Exploration Mode")
    mode = st.selectbox(
        "Analysis Type", EXPLORATION_MODES, key="remote_mode",
    )

    # Category multiselect for modes that allow custom category selection
    is_glad_mode = mode == "Deforestation Alerts (GLAD)"
    if mode in ("All Structures", "Custom Area Search"):
        selected_cats = st.multiselect(
            "Structure Categories",
            list(FEATURE_CATEGORIES.keys()),
            default=list(FEATURE_CATEGORIES.keys()),
            key="remote_cats",
        )
    elif is_glad_mode:
        selected_cats = []
    else:
        selected_cats = MODE_CATEGORY_MAP.get(mode, [])

    # Search button
    btn_label = ("Fetch Deforestation Alerts" if is_glad_mode
                 else "Explore Remote Area")
    if st.button(btn_label, key="remote_search", type="primary"):
        st.session_state.remote_params = {
            "lat": rem_lat,
            "lon": rem_lon,
            "radius": rem_radius,
            "mode": mode,
            "cats": selected_cats,
            "is_glad": is_glad_mode,
            "data_source": data_source_mode,
            "min_size": min_building_size,
            "max_size": max_building_size,
        }

    if "remote_params" not in st.session_state:
        info_card(
            "Get Started",
            "Select a remote area and exploration mode, then click <strong>Explore</strong> to scan for structures and deforestation.",
            "ℹ️",
            "#06b6d4"
        )
        return

    rp = st.session_state.remote_params

    # ══════════════════════════════════════════
    # SECTION 2 : Data Fetching
    # ══════════════════════════════════════════
    struct_df = pd.DataFrame()
    glad_df = pd.DataFrame()
    struct_err = None
    glad_err = None

    if rp["is_glad"]:
        # GLAD-only mode
        with st.spinner("Fetching GLAD deforestation alerts from Global Forest Watch..."):
            glad_df, glad_err = _fetch_glad_alerts(rp["lat"], rp["lon"], rp["radius"])
        if glad_err:
            warning_banner(f"GLAD API issue: {html_module.escape(glad_err)}", "⚠️")
        if glad_df.empty:
            info_card(
                "No Deforestation Alerts Found",
                "No GLAD deforestation alerts detected in this area. Try a larger radius or a different region (e.g. Amazon Manaus, 50+ km radius).",
                "🌲",
                "#10b981"
            )
    else:
        # Determine if multi-source or legacy OSM mode
        use_multi_source = (
            MULTI_SOURCE_AVAILABLE and
            rp.get("data_source", "OSM Only (Legacy)") != "OSM Only (Legacy)" and
            rp["mode"] in ("Buildings & Settlements", "All Structures", "Custom Area Search")
        )

        if use_multi_source:
            # NEW: Multi-source AI-powered building detection
            info_card(
                "AI-Powered Detection Active",
                f"Using <strong>{rp['data_source']}</strong> for enhanced building detection with multi-source data fusion.",
                "🤖",
                "#8b5cf6"
            )

            # Map UI mode to DB mode
            mode_map = {
                "Fast (OSM + Google AI)": "fast",
                "Comprehensive (OSM + Google + Microsoft)": "comprehensive",
                "AI Only (Google + Microsoft)": "ai_only",
                "AI Live Detection (SAM2 Real-Time)": "ai_live"
            }
            db_mode = mode_map.get(rp.get("data_source"), "fast")

            # Convert radius to bbox (math is already imported at top)
            lat, lon, radius_km = rp["lat"], rp["lon"], rp["radius"]
            deg_per_km_lat = 1 / 111.32
            deg_per_km_lon = 1 / (111.32 * math.cos(math.radians(lat)))

            min_lat = lat - (radius_km * deg_per_km_lat)
            max_lat = lat + (radius_km * deg_per_km_lat)
            min_lon = lon - (radius_km * deg_per_km_lon)
            max_lon = lon + (radius_km * deg_per_km_lon)
            bbox = (min_lon, min_lat, max_lon, max_lat)

            # Detect region hint for faster tile lookup
            region_hint = None
            if -10 < lat < 15 and 10 < lon < 50:
                region_hint = "Africa"
            elif -10 < lat < 50 and 60 < lon < 150:
                region_hint = "Asia"
            elif -60 < lat < 15 and -85 < lon < -30:
                region_hint = "LatinAmerica"

            try:
                with st.spinner(f"Searching {db_mode} sources for buildings..."):
                    db = RemoteStructuresDB()
                    gdf = db.search_all_sources(
                        bbox=bbox,
                        mode=db_mode,
                        min_area_sqm=rp.get("min_size", 10),
                        max_area_sqm=rp.get("max_size", 10000),
                        region_hint=region_hint,
                        deduplicate=True
                    )

                    # Convert GeoDataFrame to legacy struct_df format
                    if not gdf.empty:
                        struct_df = pd.DataFrame({
                            "lat": gdf.geometry.centroid.y,
                            "lon": gdf.geometry.centroid.x,
                            "category": "Buildings",
                            "name": gdf.get("name", "AI-detected building"),
                            "source": gdf.get("source", "unknown"),
                            "area_sqm": gdf.get("area_in_meters", gdf.get("area_sqm", 0)),
                        })
                    else:
                        struct_df = pd.DataFrame()

                    struct_err = None

                    # Show multi-source stats
                    if not gdf.empty:
                        stats = db.get_summary_stats(gdf)

                        # Create stats grid for sources
                        source_stats = []
                        for source, count in stats.get('by_source', {}).items():
                            source_icons = {
                                "OSM": "🗺️",
                                "Google": "🌐",
                                "Microsoft": "🏢",
                                "SAM2": "🤖"
                            }
                            source_stats.append({
                                "label": source,
                                "value": f"{count:,}",
                                "icon": source_icons.get(source, "📍"),
                                "color": "#06b6d4"
                            })

                        if source_stats:
                            st.markdown("### 📊 Detection Sources")
                            stats_grid(source_stats, columns=min(len(source_stats), 4))

                        success_banner(
                            f"Found {stats['total']:,} buildings from {len(stats.get('by_source', {}))} data sources",
                            "✅"
                        )

            except Exception as e:
                error_banner(f"Multi-source detection failed: {e}", str(e), "❌")
                info_card(
                    "Fallback Mode Active",
                    "Switching to legacy OSM-only mode for this search...",
                    "🔄",
                    "#f59e0b"
                )
                struct_df = pd.DataFrame()
                struct_err = str(e)

        # Legacy OSM mode or fallback
        if struct_df.empty and (not use_multi_source or struct_err):
            with st.spinner("Querying Overpass API for remote structures..."):
                struct_df, struct_err = _fetch_structures(
                    rp["lat"], rp["lon"], rp["radius"], rp["cats"],
                )
            if struct_err:
                warning_banner(f"Overpass API issue: {html_module.escape(struct_err)}", "⚠️")

        # Also fetch GLAD alerts for Logging & Deforestation mode
        if rp["mode"] == "Logging & Deforestation":
            with st.spinner("Also checking GLAD deforestation alerts..."):
                glad_df, glad_err = _fetch_glad_alerts(
                    rp["lat"], rp["lon"], rp["radius"],
                )
                if glad_err:
                    st.caption(f"GLAD: {html_module.escape(glad_err)}")

    total_struct = len(struct_df)
    total_glad = len(glad_df)
    total_items = total_struct + total_glad

    if total_items == 0:
        info_card(
            "No Features Found",
            "No structures or deforestation alerts detected in this area. Try:\n- Increasing the search radius\n- Selecting different feature categories\n- Choosing a different preset location",
            "🔍",
            "#64748b"
        )
        return

    # ══════════════════════════════════════════
    # SECTION 3 : Stats Row
    # ══════════════════════════════════════════
    section_header("Discovery Overview", f"Analysis results for {rp['radius']}km radius area", "📊")

    area_km2 = math.pi * rp["radius"] ** 2
    density = total_items / max(area_km2, 1)

    cat_counts = {}
    if not struct_df.empty:
        cat_counts = struct_df["category"].value_counts().to_dict()

    # Build stats for grid
    overview_stats = [
        {
            "label": "Features Found",
            "value": f"{total_items:,}",
            "icon": "🎯",
            "color": "#06b6d4"
        },
        {
            "label": "Area Scanned",
            "value": f"{area_km2:,.0f} km²",
            "icon": "🗺️",
            "color": "#8b5cf6"
        },
        {
            "label": "Density",
            "value": f"{density:.2f}/km²",
            "icon": "📊",
            "color": "#10b981"
        }
    ]

    if total_glad > 0:
        overview_stats.append({
            "label": "Deforestation Alerts",
            "value": f"{total_glad:,}",
            "icon": "🌳",
            "color": "#ef4444"
        })
    elif cat_counts:
        top_cat = max(cat_counts, key=cat_counts.get)
        overview_stats.append({
            "label": "Top Category",
            "value": top_cat[:20],
            "icon": "🏆",
            "color": "#f59e0b"
        })
    else:
        overview_stats.append({
            "label": "Categories",
            "value": "0",
            "icon": "📁",
            "color": "#64748b"
        })

    stats_grid(overview_stats, columns=4)

    # Per-category breakdown row
    if cat_counts:
        n_cols = min(len(cat_counts), 6)
        cat_cols = st.columns(n_cols)
        for i, (cat, cnt) in enumerate(
            sorted(cat_counts.items(), key=lambda x: -x[1])
        ):
            if i < n_cols:
                cat_cols[i].metric(cat[:22], cnt)

    # ══════════════════════════════════════════
    # SECTION 4 : Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Detection Map")

    # Legend
    legend_parts = []
    if not struct_df.empty:
        for cat in struct_df["category"].unique():
            color = FEATURE_CATEGORIES.get(cat, {}).get("color", "#06b6d4")
            legend_parts.append(
                f'<span style="color:{color}; font-size:0.8rem;">'
                f'\u25cf {html_module.escape(cat)}</span>'
            )
    if total_glad > 0:
        legend_parts.append(
            '<span style="color:#ef4444; font-size:0.8rem;">'
            '\u25cf High confidence</span>'
        )
        legend_parts.append(
            '<span style="color:#f97316; font-size:0.8rem;">'
            '\u25cf Nominal</span>'
        )
        legend_parts.append(
            '<span style="color:#f59e0b; font-size:0.8rem;">'
            '\u25cf Low confidence</span>'
        )
    if legend_parts:
        st.markdown(
            '<div style="display:flex; gap:0.75rem; flex-wrap:wrap; '
            'margin-bottom:0.5rem;">'
            + " ".join(legend_parts) + '</div>',
            unsafe_allow_html=True,
        )

    zoom = 9 if rp["is_glad"] else 10
    max_m = st.session_state.get("remote_max_markers", 15000)
    m = _build_map(
        rp["lat"], rp["lon"], rp["radius"],
        struct_df, glad_df if total_glad > 0 else None, zoom, max_m
    )
    st_html(m._repr_html_(), height=500)

    if total_struct > max_m or total_glad > max_m:
        st.caption(f"Map limited to {max_m:,} markers per layer for performance. Adjust the 'Max Markers to Render' slider above to see more.")

    # ══════════════════════════════════════════
    # SECTION 5 : Notable Finds & Category Chart
    # ══════════════════════════════════════════
    st.markdown("---")

    col_sites, col_chart = st.columns([1, 1])

    with col_sites:
        st.markdown("#### Notable Finds")
        if not struct_df.empty:
            sorted_df = struct_df.sort_values("name", ascending=False).head(20)
            for _, f in sorted_df.iterrows():
                safe_name = html_module.escape(str(f.get("name", "") or "Unnamed"))
                safe_cat = html_module.escape(str(f["category"]))
                color = f.get("color", "#06b6d4")
                st.markdown(
                    f'<div class="bio-card" style="display:flex; '
                    f'align-items:center; margin-bottom:0.5rem;">'
                    f'<div style="width:10px; height:50px; border-radius:5px; '
                    f'background:{color}; margin-right:0.75rem; '
                    f'flex-shrink:0;"></div>'
                    f'<div>'
                    f'<div style="color:#e8ecf4; font-weight:600; '
                    f'font-size:0.85rem;">{safe_name}</div>'
                    f'<div style="color:#8b97b0; font-size:0.75rem;">'
                    f'{safe_cat}</div>'
                    f'<div style="color:#5a6580; font-size:0.7rem;">'
                    f'{f["latitude"]:.5f}, {f["longitude"]:.5f}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        if total_glad > 0:
            st.markdown(f"**+ {total_glad:,} GLAD deforestation alert(s)**")

    with col_chart:
        st.markdown("#### Category Breakdown")
        chart_data = dict(cat_counts)
        if total_glad > 0:
            chart_data["GLAD Alerts"] = total_glad

        if chart_data:
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#0a0e1a")

            cats = list(chart_data.keys())
            counts = list(chart_data.values())
            bar_colors = []
            for c in cats:
                if c == "GLAD Alerts":
                    bar_colors.append("#ef4444")
                else:
                    bar_colors.append(
                        FEATURE_CATEGORIES.get(c, {}).get("color", "#8b97b0")
                    )

            ax.barh(range(len(cats)), counts, color=bar_colors, alpha=0.8)
            ax.set_yticks(range(len(cats)))
            ax.set_yticklabels(
                [c[:25] for c in cats], color="#8b97b0", fontsize=9,
            )
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
    # SECTION 6 : Results Table & Downloads
    # ══════════════════════════════════════════
    st.markdown("---")

    # Combine structures + GLAD into one display table
    all_rows = []
    if not struct_df.empty:
        for _, row in struct_df.iterrows():
            all_rows.append({
                "name": row.get("name", ""),
                "category": row["category"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "osm_id": row.get("osm_id", ""),
                "type": row.get("osm_type", ""),
            })
    if not glad_df.empty:
        lat_col = next((c for c in glad_df.columns if "lat" in c.lower()), None)
        lon_col = next((c for c in glad_df.columns if "lon" in c.lower()), None)
        date_col = next((c for c in glad_df.columns if "date" in c.lower()), None)
        if lat_col and lon_col:
            for _, row in glad_df.iterrows():
                all_rows.append({
                    "name": f"Alert {str(row.get(date_col, ''))[:10]}" if date_col else "Alert",
                    "category": "GLAD Alert",
                    "latitude": row[lat_col],
                    "longitude": row[lon_col],
                    "osm_id": "",
                    "type": "alert",
                })

    combined_df = pd.DataFrame(all_rows)

    with st.expander(f"Full Data Table ({len(combined_df)} features)", expanded=False):
        st.dataframe(combined_df, width="stretch", hide_index=True)

    # Downloads
    dl1, dl2 = st.columns(2)
    with dl1:
        csv_buf = io.StringIO()
        combined_df.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download CSV ({len(combined_df)} features)",
            data=csv_buf.getvalue(),
            file_name="remote_structures.csv",
            mime="text/csv",
            key="remote_dl_csv",
        )
    with dl2:
        if not struct_df.empty:
            geojson_str = _to_geojson(struct_df)
            st.download_button(
                f"Download GeoJSON ({total_struct} structures)",
                data=geojson_str,
                file_name="remote_structures.geojson",
                mime="application/geo+json",
                key="remote_dl_geojson",
            )
        elif not glad_df.empty and "latitude" in combined_df.columns:
            # Export GLAD alerts as GeoJSON
            alert_geo = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [r["longitude"], r["latitude"]],
                        },
                        "properties": {"name": r["name"], "category": r["category"]},
                    }
                    for r in all_rows if r["category"] == "GLAD Alert"
                ],
            }
            st.download_button(
                f"Download GeoJSON ({total_glad} alerts)",
                data=json.dumps(alert_geo, indent=2),
                file_name="deforestation_alerts.geojson",
                mime="application/geo+json",
                key="remote_dl_geojson",
            )
