# -*- coding: utf-8 -*-
"""
Transport & Route Maps module for TerraScout AI.

Provides 12 composite transport/route map visualizations using free APIs:
1.  World Airports          (Overpass: aeroway=aerodrome)
2.  Global Railways         (Overpass: railway=rail + stations)
3.  Shipping Routes         (Hardcoded lanes + Overpass ports)
4.  World Bridges           (Overpass: man_made=bridge / bridge=yes)
5.  Tunnels                 (Overpass: tunnel=yes)
6.  Highway Networks        (Overpass: highway=motorway)
7.  Ferry Routes            (Overpass: route=ferry)
8.  Cycling Infrastructure  (Overpass: cycleway / highway=cycleway)
9.  Metro Systems           (Overpass: railway=subway)
10. Cable Cars & Funiculars (Overpass: aerialway=*)
11. Historic Railways       (Overpass: railway=abandoned|disused|preserved)
12. Canals & Waterways      (Overpass: waterway=canal|river)

All APIs are free, no keys required.
"""

import io
import json
import math
import logging
from html import escape

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & COLOUR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

TRANSPORT_COLORS = {
    "airports":    "#06b6d4",
    "railways":    "#f59e0b",
    "shipping":    "#3b82f6",
    "bridges":     "#8b5cf6",
    "tunnels":     "#ef4444",
    "highways":    "#10b981",
    "ferries":     "#ec4899",
    "cycling":     "#22d3ee",
    "metro":       "#a855f7",
    "cablecars":   "#f97316",
    "historic_rw": "#64748b",
    "canals":      "#38bdf8",
}

MAP_TYPES = [
    "World Airports",
    "Global Railways",
    "Shipping Routes",
    "World Bridges",
    "Tunnels",
    "Highway Networks",
    "Ferry Routes",
    "Cycling Infrastructure",
    "Metro Systems",
    "Cable Cars & Funiculars",
    "Historic Railways",
    "Canals & Waterways",
]

# ═══════════════════════════════════════════════════════════════════════════════
# PRESET LOCATIONS
# ═══════════════════════════════════════════════════════════════════════════════

AIRPORT_PRESETS = {
    "Custom": None,
    "London Heathrow Area": {"lat": 51.47, "lon": -0.46, "radius": 30},
    "New York Metro": {"lat": 40.64, "lon": -73.78, "radius": 40},
    "Paris CDG & Orly": {"lat": 48.86, "lon": 2.35, "radius": 35},
    "Tokyo Narita & Haneda": {"lat": 35.68, "lon": 139.77, "radius": 50},
    "Dubai International": {"lat": 25.25, "lon": 55.36, "radius": 25},
    "Los Angeles LAX Area": {"lat": 33.94, "lon": -118.41, "radius": 30},
    "Frankfurt Area": {"lat": 50.04, "lon": 8.57, "radius": 25},
    "Singapore Changi": {"lat": 1.36, "lon": 103.99, "radius": 20},
    "Rome Fiumicino & Ciampino": {"lat": 41.80, "lon": 12.25, "radius": 30},
    "Sydney Kingsford Smith": {"lat": -33.95, "lon": 151.18, "radius": 25},
}

RAILWAY_PRESETS = {
    "Custom": None,
    "London Rail Hub": {"lat": 51.53, "lon": -0.13, "radius": 15},
    "Tokyo Rail Network": {"lat": 35.68, "lon": 139.77, "radius": 15},
    "Paris Gare du Nord Area": {"lat": 48.88, "lon": 2.36, "radius": 12},
    "Berlin Hauptbahnhof": {"lat": 52.52, "lon": 13.37, "radius": 12},
    "Zurich Main Station": {"lat": 47.38, "lon": 8.54, "radius": 10},
    "Milan Central": {"lat": 45.48, "lon": 9.20, "radius": 12},
    "Mumbai Railways": {"lat": 19.02, "lon": 72.84, "radius": 15},
    "Chicago Union Station": {"lat": 41.88, "lon": -87.64, "radius": 15},
    "Rome Termini Area": {"lat": 41.90, "lon": 12.50, "radius": 10},
}

BRIDGE_PRESETS = {
    "Custom": None,
    "San Francisco Bay Bridges": {"lat": 37.82, "lon": -122.37, "radius": 10},
    "London Thames Bridges": {"lat": 51.51, "lon": -0.08, "radius": 5},
    "New York City Bridges": {"lat": 40.71, "lon": -73.99, "radius": 10},
    "Venice Bridges": {"lat": 45.44, "lon": 12.34, "radius": 3},
    "Paris Seine Bridges": {"lat": 48.86, "lon": 2.34, "radius": 4},
    "Florence Arno Bridges": {"lat": 43.77, "lon": 11.25, "radius": 3},
    "Istanbul Bosphorus": {"lat": 41.05, "lon": 29.03, "radius": 5},
    "Sydney Harbour Bridge": {"lat": -33.85, "lon": 151.21, "radius": 5},
    "Porto Douro Bridges": {"lat": 41.14, "lon": -8.61, "radius": 3},
}

TUNNEL_PRESETS = {
    "Custom": None,
    "Swiss Alps Tunnels": {"lat": 46.55, "lon": 8.57, "radius": 20},
    "Austrian Alps": {"lat": 47.07, "lon": 12.70, "radius": 20},
    "Norwegian Fjord Tunnels": {"lat": 60.39, "lon": 5.32, "radius": 20},
    "London Underground Area": {"lat": 51.51, "lon": -0.13, "radius": 10},
    "Tokyo Tunnel Network": {"lat": 35.68, "lon": 139.77, "radius": 10},
    "Italian Apennines": {"lat": 44.22, "lon": 11.10, "radius": 20},
    "Brenner Pass Area": {"lat": 47.00, "lon": 11.50, "radius": 15},
}

HIGHWAY_PRESETS = {
    "Custom": None,
    "Los Angeles Freeways": {"lat": 34.05, "lon": -118.25, "radius": 20},
    "German Autobahn - Frankfurt": {"lat": 50.11, "lon": 8.68, "radius": 25},
    "Italian Autostrada - Milan": {"lat": 45.46, "lon": 9.19, "radius": 20},
    "Tokyo Expressway": {"lat": 35.68, "lon": 139.77, "radius": 15},
    "London M25 Ring": {"lat": 51.50, "lon": -0.12, "radius": 30},
    "Dubai Highway Network": {"lat": 25.20, "lon": 55.27, "radius": 20},
    "Beijing Ring Roads": {"lat": 39.91, "lon": 116.40, "radius": 20},
    "Chicago Expressways": {"lat": 41.88, "lon": -87.63, "radius": 20},
}

FERRY_PRESETS = {
    "Custom": None,
    "Greek Islands": {"lat": 37.45, "lon": 24.94, "radius": 50},
    "Scandinavian Ferries": {"lat": 59.33, "lon": 18.07, "radius": 30},
    "Puget Sound, WA": {"lat": 47.60, "lon": -122.34, "radius": 25},
    "Istanbul Ferries": {"lat": 41.02, "lon": 29.00, "radius": 10},
    "Venice Water Transport": {"lat": 45.44, "lon": 12.34, "radius": 8},
    "Hong Kong Ferries": {"lat": 22.29, "lon": 114.17, "radius": 10},
    "Sydney Harbour Ferries": {"lat": -33.86, "lon": 151.21, "radius": 10},
    "Croatian Coast": {"lat": 43.51, "lon": 16.44, "radius": 40},
}

CYCLING_PRESETS = {
    "Custom": None,
    "Amsterdam": {"lat": 52.37, "lon": 4.90, "radius": 5},
    "Copenhagen": {"lat": 55.68, "lon": 12.57, "radius": 5},
    "Berlin": {"lat": 52.52, "lon": 13.41, "radius": 8},
    "Paris": {"lat": 48.86, "lon": 2.35, "radius": 5},
    "Portland, OR": {"lat": 45.52, "lon": -122.68, "radius": 8},
    "Barcelona": {"lat": 41.39, "lon": 2.17, "radius": 5},
    "Utrecht": {"lat": 52.09, "lon": 5.12, "radius": 5},
    "Tokyo": {"lat": 35.68, "lon": 139.77, "radius": 5},
}

METRO_PRESETS = {
    "Custom": None,
    "London Underground": {"lat": 51.51, "lon": -0.13, "radius": 10},
    "Paris Metro": {"lat": 48.86, "lon": 2.35, "radius": 8},
    "Tokyo Metro": {"lat": 35.68, "lon": 139.77, "radius": 10},
    "New York Subway": {"lat": 40.75, "lon": -73.99, "radius": 10},
    "Moscow Metro": {"lat": 55.76, "lon": 37.62, "radius": 10},
    "Berlin U-Bahn": {"lat": 52.52, "lon": 13.41, "radius": 8},
    "Madrid Metro": {"lat": 40.42, "lon": -3.70, "radius": 8},
    "Rome Metro": {"lat": 41.90, "lon": 12.50, "radius": 8},
    "Shanghai Metro": {"lat": 31.23, "lon": 121.47, "radius": 12},
}

CABLECAR_PRESETS = {
    "Custom": None,
    "Swiss Alps - Zermatt": {"lat": 46.02, "lon": 7.75, "radius": 10},
    "Austrian Alps - Innsbruck": {"lat": 47.26, "lon": 11.39, "radius": 15},
    "French Alps - Chamonix": {"lat": 45.92, "lon": 6.87, "radius": 10},
    "Dolomites, Italy": {"lat": 46.41, "lon": 11.84, "radius": 15},
    "La Paz, Bolivia": {"lat": -16.50, "lon": -68.15, "radius": 8},
    "Rio de Janeiro": {"lat": -22.95, "lon": -43.17, "radius": 8},
    "Madeira, Portugal": {"lat": 32.65, "lon": -16.91, "radius": 5},
    "Hong Kong Peak Tram": {"lat": 22.27, "lon": 114.15, "radius": 5},
}

HISTORIC_RW_PRESETS = {
    "Custom": None,
    "UK Peak District": {"lat": 53.30, "lon": -1.80, "radius": 15},
    "Welsh Railways": {"lat": 52.62, "lon": -3.73, "radius": 20},
    "Colorado Narrow Gauge": {"lat": 37.28, "lon": -107.88, "radius": 20},
    "German Heritage Lines": {"lat": 51.76, "lon": 11.00, "radius": 20},
    "Italian Apennine Lines": {"lat": 44.06, "lon": 11.78, "radius": 15},
    "Scottish Highlands": {"lat": 56.82, "lon": -5.10, "radius": 25},
    "Swiss Mountain Railways": {"lat": 46.60, "lon": 8.03, "radius": 15},
    "Japanese Heritage Lines": {"lat": 36.20, "lon": 139.10, "radius": 25},
}

CANAL_PRESETS = {
    "Custom": None,
    "Amsterdam Canal Ring": {"lat": 52.37, "lon": 4.90, "radius": 5},
    "Venice Grand Canal": {"lat": 45.44, "lon": 12.34, "radius": 3},
    "English Midlands Canals": {"lat": 52.48, "lon": -1.90, "radius": 15},
    "Bruges, Belgium": {"lat": 51.21, "lon": 3.22, "radius": 3},
    "St. Petersburg Canals": {"lat": 59.93, "lon": 30.32, "radius": 5},
    "Bangkok Klongs": {"lat": 13.73, "lon": 100.52, "radius": 8},
    "Suzhou, China": {"lat": 31.30, "lon": 120.59, "radius": 5},
    "Panama Canal": {"lat": 9.08, "lon": -79.68, "radius": 10},
    "Suez Canal Area": {"lat": 30.58, "lon": 32.27, "radius": 15},
}

# Shipping route presets are global so no lat/lon picker
SHIPPING_PORT_PRESETS = {
    "Custom": None,
    "Rotterdam & North Sea": {"lat": 51.92, "lon": 4.48, "radius": 15},
    "Singapore Strait": {"lat": 1.26, "lon": 103.83, "radius": 15},
    "Shanghai Port": {"lat": 31.35, "lon": 121.59, "radius": 15},
    "Los Angeles / Long Beach": {"lat": 33.74, "lon": -118.27, "radius": 12},
    "Dubai / Jebel Ali": {"lat": 25.00, "lon": 55.06, "radius": 12},
    "Hamburg Port": {"lat": 53.54, "lon": 9.97, "radius": 10},
    "Genoa, Italy": {"lat": 44.41, "lon": 8.93, "radius": 8},
    "Piraeus, Greece": {"lat": 37.94, "lon": 23.64, "radius": 8},
}

# ═══════════════════════════════════════════════════════════════════════════════
# HARDCODED SHIPPING LANES
# ═══════════════════════════════════════════════════════════════════════════════

MAJOR_SHIPPING_LANES = [
    {
        "name": "Suez Canal Route (Mediterranean - Red Sea)",
        "color": "#ef4444",
        "coords": [
            [31.27, 32.34], [30.45, 32.35], [29.95, 32.56],
            [29.87, 32.57], [12.60, 43.15],
        ],
        "desc": "Connects Mediterranean to Red Sea. ~12% of global trade.",
    },
    {
        "name": "Strait of Malacca Route",
        "color": "#f59e0b",
        "coords": [
            [6.25, 99.70], [4.20, 100.50], [2.50, 101.80],
            [1.26, 103.83], [1.10, 104.10],
        ],
        "desc": "Busiest shipping strait. ~25% of global trade passes through.",
    },
    {
        "name": "Panama Canal Route (Atlantic - Pacific)",
        "color": "#10b981",
        "coords": [
            [9.38, -79.92], [9.20, -79.85], [9.08, -79.68],
            [8.95, -79.55], [8.88, -79.52],
        ],
        "desc": "Connects Atlantic and Pacific oceans. ~5% of global trade.",
    },
    {
        "name": "English Channel Route",
        "color": "#3b82f6",
        "coords": [
            [48.50, -5.10], [49.50, -2.50], [50.50, 0.00],
            [51.00, 1.30], [51.50, 2.50],
        ],
        "desc": "One of the world's busiest shipping lanes. ~500 ships daily.",
    },
    {
        "name": "Strait of Hormuz Route",
        "color": "#ec4899",
        "coords": [
            [26.60, 56.25], [26.30, 56.40], [26.00, 56.55],
            [25.50, 57.00], [24.50, 58.50],
        ],
        "desc": "Critical oil shipping route. ~21% of global petroleum passes through.",
    },
    {
        "name": "Cape of Good Hope Route",
        "color": "#8b5cf6",
        "coords": [
            [-33.50, 17.50], [-34.35, 18.50], [-34.83, 20.00],
            [-33.00, 28.00], [-30.00, 31.00],
        ],
        "desc": "Alternative to Suez Canal around southern Africa.",
    },
    {
        "name": "Trans-Pacific Route (Shanghai - LA)",
        "color": "#06b6d4",
        "coords": [
            [31.35, 121.59], [33.00, 135.00], [35.00, 155.00],
            [38.00, 175.00], [37.00, -160.00], [35.00, -140.00],
            [33.74, -118.27],
        ],
        "desc": "Major container route across the Pacific Ocean.",
    },
    {
        "name": "Trans-Atlantic Route (Rotterdam - New York)",
        "color": "#22d3ee",
        "coords": [
            [51.92, 4.48], [51.00, -1.00], [50.00, -10.00],
            [48.00, -25.00], [43.00, -50.00], [40.70, -74.00],
        ],
        "desc": "Historic trade route across the North Atlantic.",
    },
    {
        "name": "Mediterranean Route (Gibraltar - Suez)",
        "color": "#f97316",
        "coords": [
            [35.98, -5.50], [36.50, -2.00], [37.00, 3.00],
            [36.00, 10.00], [35.00, 15.00], [33.50, 24.00],
            [31.50, 32.00],
        ],
        "desc": "Key Mediterranean east-west corridor.",
    },
    {
        "name": "Northern Sea Route (Arctic)",
        "color": "#64748b",
        "coords": [
            [69.00, 33.00], [72.00, 55.00], [74.00, 80.00],
            [75.00, 110.00], [73.00, 140.00], [68.00, 170.00],
        ],
        "desc": "Emerging Arctic shipping route. Seasonal, ice-dependent.",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _bbox_from_center(lat: float, lon: float, radius_km: float):
    """Compute south, west, north, east from center + radius in km."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.01, abs(math.cos(math.radians(lat)))))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def _bbox_str(south, west, north, east):
    return f"{south},{west},{north},{east}"


def _build_folium_map(lat, lon, zoom=11):
    """Create base dark folium map."""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )
    return m


def _render_map(m, height=550):
    """Render folium map via components.html."""
    components.html(m._repr_html_(), height=height)


def _safe_popup(name, category="", extras=None):
    """Build an HTML popup with escaped user content."""
    parts = [f"<strong>{escape(str(name))}</strong>"]
    if category:
        parts.append(f"<br/><span style='font-size:0.85rem;'>{escape(str(category))}</span>")
    if extras:
        for k, v in extras.items():
            parts.append(f"<br/><span style='font-size:0.8rem;'>{escape(str(k))}: {escape(str(v))}</span>")
    return folium.Popup("".join(parts), max_width=260)


def _overpass_result_ok(result):
    """Check if overpass result is usable."""
    if result is None:
        st.error("All Overpass servers unreachable. Check your internet connection.")
        return False
    if "_error" in result:
        st.error(f"Overpass query failed: {result['_error']}. Try a smaller area or retry later.")
        return False
    return True


def _build_node_lookup(elements):
    """Build id -> (lat, lon) mapping for nodes."""
    lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lookup[el["id"]] = (el["lat"], el["lon"])
    return lookup


def _way_coords(way, node_lookup):
    """Resolve a way's node references to coordinate list."""
    coords = []
    for nid in way.get("nodes", []):
        if nid in node_lookup:
            coords.append(node_lookup[nid])
    return coords


def _way_centroid(coords):
    """Compute centroid of a coordinate list."""
    if not coords:
        return None, None
    lat = sum(c[0] for c in coords) / len(coords)
    lon = sum(c[1] for c in coords) / len(coords)
    return lat, lon


def _features_to_dataframe(features, columns=None):
    """Convert feature dicts to a pandas DataFrame."""
    if not features:
        return pd.DataFrame()
    df = pd.DataFrame(features)
    if columns:
        available = [c for c in columns if c in df.columns]
        df = df[available]
    return df


def _make_chart(cat_counts, title="Distribution", palette=None):
    """Create a horizontal bar chart with dark theme."""
    if not cat_counts:
        return
    fig, ax = plt.subplots(figsize=(6, max(2.5, len(cat_counts) * 0.45)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    cats = list(cat_counts.keys())
    counts = list(cat_counts.values())
    if palette:
        colors = [palette.get(c, "#06b6d4") for c in cats]
    else:
        colors = ["#06b6d4"] * len(cats)

    ax.barh(range(len(cats)), counts, color=colors, alpha=0.85)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels([c[:28] for c in cats], color="#8b97b0", fontsize=9)
    ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=8)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _download_section(features, prefix="transport"):
    """Render CSV and GeoJSON download buttons."""
    if not features:
        return
    df = _features_to_dataframe(features)
    st.markdown("---")
    st.markdown("#### Export Data")
    dl1, dl2 = st.columns(2)
    with dl1:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download CSV ({len(features)} features)",
            data=csv_buf.getvalue(),
            file_name=f"{prefix}_data.csv",
            mime="text/csv",
            key=f"{prefix}_dl_csv",
            width="stretch",
        )
    with dl2:
        geojson_features = []
        for feat in features:
            lat = feat.get("lat") or feat.get("latitude")
            lon = feat.get("lon") or feat.get("longitude")
            if lat is not None and lon is not None:
                geojson_features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {k: v for k, v in feat.items()
                                   if k not in ("lat", "lon", "latitude", "longitude", "coords")},
                })
        geojson_col = {"type": "FeatureCollection", "features": geojson_features}
        st.download_button(
            "Download GeoJSON",
            data=json.dumps(geojson_col, indent=2, ensure_ascii=False),
            file_name=f"{prefix}_data.geojson",
            mime="application/json",
            key=f"{prefix}_dl_geojson",
            width="stretch",
        )


def _location_controls(prefix, presets, default_lat=45.0, default_lon=10.0,
                        default_radius=10, max_radius=50):
    """Shared location controls: preset selector, lat/lon/radius inputs."""
    preset_name = st.selectbox(
        "Preset Locations", list(presets.keys()), key=f"{prefix}_preset"
    )
    p_lat, p_lon, p_rad = default_lat, default_lon, default_radius
    if preset_name != "Custom" and presets.get(preset_name):
        p = presets[preset_name]
        p_lat, p_lon, p_rad = p["lat"], p["lon"], p["radius"]

    c1, c2, c3 = st.columns(3)
    with c1:
        lat = st.number_input("Latitude", value=p_lat, format="%.4f",
                               min_value=-90.0, max_value=90.0, key=f"{prefix}_lat")
    with c2:
        lon = st.number_input("Longitude", value=p_lon, format="%.4f",
                               min_value=-180.0, max_value=180.0, key=f"{prefix}_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, max_radius, p_rad, key=f"{prefix}_radius")

    return lat, lon, radius


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING FUNCTIONS (cached)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _fetch_airports(south, west, north, east):
    """Fetch aerodrome features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  node["aeroway"="aerodrome"]({bbox});
  way["aeroway"="aerodrome"]({bbox});
  relation["aeroway"="aerodrome"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_railways(south, west, north, east):
    """Fetch rail lines and stations from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["railway"="rail"]({bbox});
  node["railway"="station"]({bbox});
  node["railway"="halt"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_ports(south, west, north, east):
    """Fetch port/harbour features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  node["harbour"="yes"]({bbox});
  node["landuse"="port"]({bbox});
  way["landuse"="port"]({bbox});
  node["seamark:type"="harbour"]({bbox});
  node["industrial"="port"]({bbox});
  way["industrial"="port"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_bridges(south, west, north, east):
    """Fetch bridge features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["man_made"="bridge"]({bbox});
  way["bridge"="yes"]["name"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_tunnels(south, west, north, east):
    """Fetch tunnel features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["tunnel"="yes"]["name"]({bbox});
  way["tunnel"="building_passage"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_highways(south, west, north, east):
    """Fetch motorway/trunk features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["highway"="motorway"]({bbox});
  way["highway"="motorway_link"]({bbox});
  way["highway"="trunk"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_ferries(south, west, north, east):
    """Fetch ferry route features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  relation["route"="ferry"]({bbox});
  way["route"="ferry"]({bbox});
  node["amenity"="ferry_terminal"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_cycling(south, west, north, east):
    """Fetch cycling infrastructure from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["highway"="cycleway"]({bbox});
  way["cycleway"~"lane|track|shared_lane"]({bbox});
  node["amenity"="bicycle_rental"]({bbox});
  node["amenity"="bicycle_parking"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_metro(south, west, north, east):
    """Fetch subway/metro features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["railway"="subway"]({bbox});
  node["railway"="station"]["station"="subway"]({bbox});
  node["station"="subway"]({bbox});
  relation["route"="subway"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_cablecars(south, west, north, east):
    """Fetch aerialway features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["aerialway"]({bbox});
  node["aerialway"="station"]({bbox});
  node["aerialway"="pylon"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_historic_railways(south, west, north, east):
    """Fetch abandoned/disused/preserved railway features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["railway"="abandoned"]({bbox});
  way["railway"="disused"]({bbox});
  way["railway"="preserved"]({bbox});
  way["railway"="narrow_gauge"]({bbox});
  node["railway"="station"]["disused"="yes"]({bbox});
  node["historic"="railway_station"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_canals(south, west, north, east):
    """Fetch canal and navigable waterway features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["waterway"="canal"]({bbox});
  way["waterway"="river"]["boat"="yes"]({bbox});
  node["waterway"="lock_gate"]({bbox});
  node["waterway"="turning_point"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_airports(data):
    """Extract airport features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if tags.get("aeroway") != "aerodrome":
            continue
        lat, lon = None, None
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        elif el.get("type") == "way":
            coords = _way_coords(el, node_lookup)
            lat, lon = _way_centroid(coords)
        if lat is None or lon is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed Airport"))
        atype = tags.get("aerodrome:type", tags.get("type", "unknown"))
        iata = tags.get("iata", "")
        icao = tags.get("icao", "")
        features.append({
            "name": name, "lat": lat, "lon": lon,
            "aerodrome_type": atype, "iata": iata, "icao": icao,
            "operator": tags.get("operator", ""),
            "ele": tags.get("ele", ""),
            "osm_id": el.get("id"),
        })
    return features


def _extract_railways(data):
    """Extract railway lines and stations from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    lines = []
    stations = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") == "node" and tags.get("railway") in ("station", "halt"):
            lat, lon = el.get("lat"), el.get("lon")
            if lat and lon:
                stations.append({
                    "name": tags.get("name", "Unnamed Station"),
                    "lat": lat, "lon": lon,
                    "station_type": tags.get("railway", "station"),
                    "operator": tags.get("operator", ""),
                    "osm_id": el.get("id"),
                })
        elif el.get("type") == "way" and tags.get("railway") == "rail":
            coords = _way_coords(el, node_lookup)
            if len(coords) >= 2:
                clat, clon = _way_centroid(coords)
                lines.append({
                    "name": tags.get("name", tags.get("ref", "Rail Line")),
                    "lat": clat, "lon": clon,
                    "coords": coords,
                    "usage": tags.get("usage", ""),
                    "electrified": tags.get("electrified", ""),
                    "maxspeed": tags.get("maxspeed", ""),
                    "osm_id": el.get("id"),
                })
    return lines, stations


def _extract_bridges(data):
    """Extract bridge features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    seen_ids = set()
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("id") in seen_ids:
            continue
        seen_ids.add(el.get("id"))
        if el.get("type") == "way":
            coords = _way_coords(el, node_lookup)
            lat, lon = _way_centroid(coords)
            if lat is None:
                continue
            name = tags.get("name", tags.get("bridge:name", "Unnamed Bridge"))
            features.append({
                "name": name, "lat": lat, "lon": lon,
                "coords": coords,
                "bridge_type": tags.get("bridge", tags.get("man_made", "")),
                "material": tags.get("bridge:material", tags.get("material", "")),
                "layer": tags.get("layer", ""),
                "maxweight": tags.get("maxweight", ""),
                "osm_id": el.get("id"),
            })
    return features


def _extract_tunnels(data):
    """Extract tunnel features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") != "way":
            continue
        coords = _way_coords(el, node_lookup)
        lat, lon = _way_centroid(coords)
        if lat is None:
            continue
        name = tags.get("name", tags.get("tunnel:name", "Unnamed Tunnel"))
        features.append({
            "name": name, "lat": lat, "lon": lon,
            "coords": coords,
            "tunnel_type": tags.get("tunnel", "yes"),
            "highway": tags.get("highway", ""),
            "railway": tags.get("railway", ""),
            "length": tags.get("length", tags.get("tunnel:length", "")),
            "osm_id": el.get("id"),
        })
    return features


def _extract_highways(data):
    """Extract motorway features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") != "way":
            continue
        hw = tags.get("highway", "")
        if hw not in ("motorway", "motorway_link", "trunk"):
            continue
        coords = _way_coords(el, node_lookup)
        if len(coords) < 2:
            continue
        lat, lon = _way_centroid(coords)
        features.append({
            "name": tags.get("name", tags.get("ref", "Highway")),
            "lat": lat, "lon": lon,
            "coords": coords,
            "highway_type": hw,
            "ref": tags.get("ref", ""),
            "lanes": tags.get("lanes", ""),
            "maxspeed": tags.get("maxspeed", ""),
            "surface": tags.get("surface", ""),
            "osm_id": el.get("id"),
        })
    return features


def _extract_ferries(data):
    """Extract ferry route features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    routes = []
    terminals = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") == "node" and tags.get("amenity") == "ferry_terminal":
            lat, lon = el.get("lat"), el.get("lon")
            if lat and lon:
                terminals.append({
                    "name": tags.get("name", "Ferry Terminal"),
                    "lat": lat, "lon": lon,
                    "operator": tags.get("operator", ""),
                    "osm_id": el.get("id"),
                })
        elif el.get("type") == "way" and tags.get("route") == "ferry":
            coords = _way_coords(el, node_lookup)
            if len(coords) >= 2:
                lat, lon = _way_centroid(coords)
                routes.append({
                    "name": tags.get("name", "Ferry Route"),
                    "lat": lat, "lon": lon,
                    "coords": coords,
                    "operator": tags.get("operator", ""),
                    "duration": tags.get("duration", ""),
                    "motor_vehicle": tags.get("motor_vehicle", ""),
                    "osm_id": el.get("id"),
                })
    return routes, terminals


def _extract_cycling(data):
    """Extract cycling infrastructure features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    paths = []
    pois = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
            if lat and lon and tags.get("amenity") in ("bicycle_rental", "bicycle_parking"):
                pois.append({
                    "name": tags.get("name", tags.get("amenity", "Cycling POI")),
                    "lat": lat, "lon": lon,
                    "poi_type": tags.get("amenity", ""),
                    "capacity": tags.get("capacity", ""),
                    "osm_id": el.get("id"),
                })
        elif el.get("type") == "way":
            coords = _way_coords(el, node_lookup)
            if len(coords) >= 2:
                lat, lon = _way_centroid(coords)
                cycle_type = "cycleway"
                if tags.get("highway") == "cycleway":
                    cycle_type = "dedicated cycleway"
                elif tags.get("cycleway"):
                    cycle_type = f"cycleway:{tags['cycleway']}"
                paths.append({
                    "name": tags.get("name", tags.get("ref", "Cycle Path")),
                    "lat": lat, "lon": lon,
                    "coords": coords,
                    "cycle_type": cycle_type,
                    "surface": tags.get("surface", ""),
                    "lit": tags.get("lit", ""),
                    "osm_id": el.get("id"),
                })
    return paths, pois


def _extract_metro(data):
    """Extract metro/subway features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    lines = []
    stations = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") == "node" and ("station" in tags or tags.get("railway") == "station"):
            lat, lon = el.get("lat"), el.get("lon")
            if lat and lon:
                stations.append({
                    "name": tags.get("name", "Metro Station"),
                    "lat": lat, "lon": lon,
                    "network": tags.get("network", ""),
                    "line": tags.get("line", ""),
                    "colour": tags.get("colour", tags.get("color", "")),
                    "wheelchair": tags.get("wheelchair", ""),
                    "osm_id": el.get("id"),
                })
        elif el.get("type") == "way" and tags.get("railway") == "subway":
            coords = _way_coords(el, node_lookup)
            if len(coords) >= 2:
                lat, lon = _way_centroid(coords)
                lines.append({
                    "name": tags.get("name", tags.get("ref", "Metro Line")),
                    "lat": lat, "lon": lon,
                    "coords": coords,
                    "colour": tags.get("colour", tags.get("color", "#a855f7")),
                    "operator": tags.get("operator", ""),
                    "osm_id": el.get("id"),
                })
    return lines, stations


def _extract_cablecars(data):
    """Extract aerialway features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        aerialway = tags.get("aerialway", "")
        if not aerialway:
            continue
        if aerialway in ("pylon",):
            continue  # skip pylons for cleaner output
        lat, lon = None, None
        coords = []
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        elif el.get("type") == "way":
            coords = _way_coords(el, node_lookup)
            lat, lon = _way_centroid(coords)
        if lat is None:
            continue
        features.append({
            "name": tags.get("name", f"{aerialway.replace('_', ' ').title()}"),
            "lat": lat, "lon": lon,
            "coords": coords,
            "aerialway_type": aerialway,
            "occupancy": tags.get("aerialway:occupancy", ""),
            "capacity": tags.get("aerialway:capacity", ""),
            "duration": tags.get("aerialway:duration", tags.get("duration", "")),
            "operator": tags.get("operator", ""),
            "osm_id": el.get("id"),
        })
    return features


def _extract_historic_railways(data):
    """Extract historic/abandoned railway features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    lines = []
    stations = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
            if lat and lon:
                stations.append({
                    "name": tags.get("name", "Historic Station"),
                    "lat": lat, "lon": lon,
                    "status": "disused" if tags.get("disused") == "yes" else "historic",
                    "osm_id": el.get("id"),
                })
        elif el.get("type") == "way":
            rw = tags.get("railway", "")
            if rw not in ("abandoned", "disused", "preserved", "narrow_gauge"):
                continue
            coords = _way_coords(el, node_lookup)
            if len(coords) >= 2:
                lat, lon = _way_centroid(coords)
                lines.append({
                    "name": tags.get("name", tags.get("ref", f"{rw.title()} Railway")),
                    "lat": lat, "lon": lon,
                    "coords": coords,
                    "status": rw,
                    "gauge": tags.get("gauge", ""),
                    "operator": tags.get("operator", ""),
                    "osm_id": el.get("id"),
                })
    return lines, stations


def _extract_canals(data):
    """Extract canal and waterway features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    waterways = []
    locks = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el.get("type") == "node":
            ww = tags.get("waterway", "")
            if ww in ("lock_gate", "turning_point"):
                lat, lon = el.get("lat"), el.get("lon")
                if lat and lon:
                    locks.append({
                        "name": tags.get("name", ww.replace("_", " ").title()),
                        "lat": lat, "lon": lon,
                        "lock_type": ww,
                        "osm_id": el.get("id"),
                    })
        elif el.get("type") == "way":
            ww = tags.get("waterway", "")
            if ww not in ("canal", "river"):
                continue
            coords = _way_coords(el, node_lookup)
            if len(coords) >= 2:
                lat, lon = _way_centroid(coords)
                waterways.append({
                    "name": tags.get("name", f"{ww.title()}"),
                    "lat": lat, "lon": lon,
                    "coords": coords,
                    "waterway_type": ww,
                    "boat": tags.get("boat", ""),
                    "width": tags.get("width", ""),
                    "osm_id": el.get("id"),
                })
    return waterways, locks


# ═══════════════════════════════════════════════════════════════════════════════
# MAP RENDERERS (one per map type)
# ═══════════════════════════════════════════════════════════════════════════════

def _render_airports_map():
    """Render the World Airports map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("airports", AIRPORT_PRESETS,
                                           default_lat=51.47, default_lon=-0.46,
                                           default_radius=30, max_radius=80)
    if not st.button("Search Airports", key="airports_btn", width="stretch", type="primary"):
        st.info("Select a location and click Search to discover airports.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying airports from OpenStreetMap..."):
        data = _fetch_airports(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    features = _extract_airports(data)
    if not features:
        st.warning("No airports found. Try a larger radius or different location.")
        return

    # Stats
    st.markdown("---")
    st.markdown("#### Airport Overview")
    type_counts = {}
    for f in features:
        t = f["aerodrome_type"] or "unknown"
        type_counts[t] = type_counts.get(t, 0) + 1
    iata_count = sum(1 for f in features if f["iata"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Airports", len(features))
    c2.metric("With IATA Code", iata_count)
    c3.metric("Types", len(type_counts))
    c4.metric("Search Radius", f"{radius} km")

    # Map
    st.markdown("---")
    st.markdown("#### Airport Map")
    m = _build_folium_map(lat, lon, zoom=9)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#06b6d4", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for f in features:
        label = f["name"]
        if f["iata"]:
            label += f" ({f['iata']})"
        popup = _safe_popup(label, f"Type: {f['aerodrome_type']}",
                            {"ICAO": f["icao"], "Operator": f["operator"]} if f["icao"] else None)
        color = "#06b6d4" if f["iata"] else "#5a6580"
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=7 if f["iata"] else 4,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            weight=2, popup=popup,
        ).add_to(m)
    _render_map(m)

    # Chart & table
    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        _make_chart(type_counts, "Airports by Type")
    with col_table:
        st.markdown("#### Airport List")
        df = _features_to_dataframe(features,
                                     ["name", "iata", "icao", "aerodrome_type", "operator", "lat", "lon"])
        with st.expander(f"Data Table ({len(features)} airports)", expanded=False):
            st.dataframe(df, width="stretch", hide_index=True)
    _download_section(features, "airports")


def _render_railways_map():
    """Render the Global Railways map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("railways", RAILWAY_PRESETS,
                                           default_lat=51.53, default_lon=-0.13,
                                           default_radius=15, max_radius=50)
    if not st.button("Search Railways", key="railways_btn", width="stretch", type="primary"):
        st.info("Select a location and click Search to explore railway networks.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying railway data from OpenStreetMap..."):
        data = _fetch_railways(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    lines, stations = _extract_railways(data)
    total = len(lines) + len(stations)
    if total == 0:
        st.warning("No railway features found. Try a larger radius.")
        return

    st.markdown("---")
    st.markdown("#### Railway Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rail Lines", len(lines))
    c2.metric("Stations / Halts", len(stations))
    c3.metric("Total Features", total)

    st.markdown("---")
    st.markdown("#### Railway Map")
    m = _build_folium_map(lat, lon, zoom=11)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#f59e0b", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for line in lines:
        if line["coords"]:
            folium.PolyLine(
                locations=line["coords"], color="#f59e0b",
                weight=3, opacity=0.75,
                popup=_safe_popup(line["name"], "Rail Line",
                                  {"Max Speed": line["maxspeed"]} if line["maxspeed"] else None),
            ).add_to(m)
    for stn in stations:
        folium.CircleMarker(
            location=[stn["lat"], stn["lon"]], radius=5,
            color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.8,
            weight=2, popup=_safe_popup(stn["name"], stn["station_type"]),
        ).add_to(m)
    _render_map(m)

    # Data table
    all_features = []
    for s in stations:
        all_features.append({"name": s["name"], "type": "station", "lat": s["lat"],
                              "lon": s["lon"], "operator": s["operator"], "osm_id": s["osm_id"]})
    for ln in lines:
        all_features.append({"name": ln["name"], "type": "rail_line", "lat": ln["lat"],
                              "lon": ln["lon"], "usage": ln["usage"], "maxspeed": ln["maxspeed"],
                              "osm_id": ln["osm_id"]})
    with st.expander(f"Data Table ({len(all_features)} features)", expanded=False):
        st.dataframe(_features_to_dataframe(all_features), width="stretch", hide_index=True)
    _download_section(all_features, "railways")


def _render_shipping_map():
    """Render the Shipping Routes map."""
    st.markdown("#### Shipping Routes & Ports")
    st.markdown(
        '<p style="color:#8b97b0; font-size:0.9rem;">Major global shipping lanes '
        '(hardcoded) plus port markers from OpenStreetMap.</p>',
        unsafe_allow_html=True,
    )

    show_ports = st.checkbox("Show nearby ports (Overpass query)", value=True, key="ship_ports")
    port_lat, port_lon, port_radius = 51.92, 4.48, 15
    if show_ports:
        preset_name = st.selectbox("Port Region", list(SHIPPING_PORT_PRESETS.keys()),
                                    key="ship_port_preset")
        if preset_name != "Custom" and SHIPPING_PORT_PRESETS.get(preset_name):
            p = SHIPPING_PORT_PRESETS[preset_name]
            port_lat, port_lon, port_radius = p["lat"], p["lon"], p["radius"]
        c1, c2, c3 = st.columns(3)
        with c1:
            port_lat = st.number_input("Port Latitude", value=port_lat, format="%.4f",
                                        key="ship_port_lat")
        with c2:
            port_lon = st.number_input("Port Longitude", value=port_lon, format="%.4f",
                                        key="ship_port_lon")
        with c3:
            port_radius = st.slider("Port Search Radius (km)", 5, 50, port_radius,
                                     key="ship_port_radius")

    if not st.button("Show Shipping Routes", key="shipping_btn", width="stretch", type="primary"):
        st.info("Click the button to display major global shipping lanes.")
        return

    ports = []
    if show_ports:
        south, west, north, east = _bbox_from_center(port_lat, port_lon, port_radius)
        with st.spinner("Querying port data..."):
            port_data = _fetch_ports(south, west, north, east)
        if port_data and "_error" not in port_data:
            elements = port_data.get("elements", [])
            node_lookup = _build_node_lookup(elements)
            for el in elements:
                tags = el.get("tags", {})
                if not tags:
                    continue
                plat, plon = None, None
                if el.get("type") == "node":
                    plat, plon = el.get("lat"), el.get("lon")
                elif el.get("type") == "way":
                    coords = _way_coords(el, node_lookup)
                    plat, plon = _way_centroid(coords)
                if plat is None:
                    continue
                ports.append({
                    "name": tags.get("name", "Port"),
                    "lat": plat, "lon": plon,
                    "osm_id": el.get("id"),
                })

    st.markdown("---")
    st.markdown("#### Overview")
    c1, c2 = st.columns(2)
    c1.metric("Shipping Lanes", len(MAJOR_SHIPPING_LANES))
    c2.metric("Ports Found", len(ports))

    st.markdown("---")
    st.markdown("#### Global Shipping Map")
    m = _build_folium_map(25.0, 10.0, zoom=2)
    for lane in MAJOR_SHIPPING_LANES:
        folium.PolyLine(
            locations=lane["coords"], color=lane["color"],
            weight=3, opacity=0.8, dash_array="8",
            popup=_safe_popup(lane["name"], lane["desc"]),
        ).add_to(m)
        mid_idx = len(lane["coords"]) // 2
        mid = lane["coords"][mid_idx]
        folium.Marker(
            location=mid,
            icon=folium.DivIcon(html=(
                f'<div style="font-size:9px; color:{lane["color"]}; white-space:nowrap; '
                f'text-shadow:1px 1px 2px #000;">{escape(lane["name"][:30])}</div>'
            )),
        ).add_to(m)
    for port in ports:
        folium.CircleMarker(
            location=[port["lat"], port["lon"]], radius=5,
            color="#3b82f6", fill=True, fill_color="#3b82f6", fill_opacity=0.8,
            weight=2, popup=_safe_popup(port["name"], "Port"),
        ).add_to(m)
    _render_map(m)

    # Lane details
    with st.expander("Shipping Lane Details"):
        rows = [{"Name": lane["name"], "Description": lane["desc"]} for lane in MAJOR_SHIPPING_LANES]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    if ports:
        all_feats = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"],
                       "osm_id": p["osm_id"]} for p in ports]
        _download_section(all_feats, "shipping_ports")


def _render_bridges_map():
    """Render the World Bridges map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("bridges", BRIDGE_PRESETS,
                                           default_lat=51.51, default_lon=-0.08,
                                           default_radius=5, max_radius=30)
    if not st.button("Search Bridges", key="bridges_btn", width="stretch", type="primary"):
        st.info("Select a location and click Search to discover bridges.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying bridge data from OpenStreetMap..."):
        data = _fetch_bridges(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    features = _extract_bridges(data)
    if not features:
        st.warning("No bridges found. Try a larger radius or different location.")
        return

    named = [f for f in features if "unnamed" not in f["name"].lower()]
    type_counts = {}
    for f in features:
        t = f["bridge_type"] or "unknown"
        type_counts[t] = type_counts.get(t, 0) + 1

    st.markdown("---")
    st.markdown("#### Bridge Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Bridges", len(features))
    c2.metric("Named Bridges", len(named))
    c3.metric("Bridge Types", len(type_counts))

    st.markdown("---")
    st.markdown("#### Bridge Map")
    m = _build_folium_map(lat, lon, zoom=13)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#8b5cf6", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for f in features:
        if f["coords"] and len(f["coords"]) >= 2:
            folium.PolyLine(
                locations=f["coords"], color="#8b5cf6",
                weight=4, opacity=0.8,
                popup=_safe_popup(f["name"], f"Type: {f['bridge_type']}",
                                  {"Material": f["material"]} if f["material"] else None),
            ).add_to(m)
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=4,
            color="#8b5cf6", fill=True, fill_color="#8b5cf6", fill_opacity=0.8,
            weight=1, popup=_safe_popup(f["name"], "Bridge"),
        ).add_to(m)
    _render_map(m)

    _make_chart(type_counts, "Bridges by Type",
                palette={k: "#8b5cf6" for k in type_counts})

    with st.expander(f"Data Table ({len(features)} bridges)", expanded=False):
        st.dataframe(
            _features_to_dataframe(features, ["name", "bridge_type", "material", "lat", "lon"]),
            width="stretch", hide_index=True,
        )
    _download_section(features, "bridges")


def _render_tunnels_map():
    """Render the Tunnels map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("tunnels", TUNNEL_PRESETS,
                                           default_lat=46.55, default_lon=8.57,
                                           default_radius=20, max_radius=50)
    if not st.button("Search Tunnels", key="tunnels_btn", width="stretch", type="primary"):
        st.info("Select a location and click Search to discover tunnels.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying tunnel data from OpenStreetMap..."):
        data = _fetch_tunnels(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    features = _extract_tunnels(data)
    if not features:
        st.warning("No tunnels found. Try a larger radius.")
        return

    road_tunnels = [f for f in features if f["highway"]]
    rail_tunnels = [f for f in features if f["railway"]]

    st.markdown("---")
    st.markdown("#### Tunnel Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tunnels", len(features))
    c2.metric("Road Tunnels", len(road_tunnels))
    c3.metric("Rail Tunnels", len(rail_tunnels))

    st.markdown("---")
    st.markdown("#### Tunnel Map")
    m = _build_folium_map(lat, lon, zoom=10)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#ef4444", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for f in features:
        color = "#ef4444" if f["highway"] else "#f59e0b" if f["railway"] else "#8b97b0"
        if f["coords"] and len(f["coords"]) >= 2:
            folium.PolyLine(
                locations=f["coords"], color=color,
                weight=4, opacity=0.7, dash_array="5",
                popup=_safe_popup(f["name"], f["tunnel_type"],
                                  {"Length": f["length"]} if f["length"] else None),
            ).add_to(m)
    _render_map(m)

    cat_counts = {}
    for f in features:
        if f["highway"]:
            cat_counts["Road"] = cat_counts.get("Road", 0) + 1
        elif f["railway"]:
            cat_counts["Rail"] = cat_counts.get("Rail", 0) + 1
        else:
            cat_counts["Other"] = cat_counts.get("Other", 0) + 1
    _make_chart(cat_counts, "Tunnels by Transport Mode",
                palette={"Road": "#ef4444", "Rail": "#f59e0b", "Other": "#8b97b0"})

    with st.expander(f"Data Table ({len(features)} tunnels)", expanded=False):
        st.dataframe(
            _features_to_dataframe(features, ["name", "tunnel_type", "highway", "railway", "length", "lat", "lon"]),
            width="stretch", hide_index=True,
        )
    _download_section(features, "tunnels")


def _render_highways_map():
    """Render the Highway Networks map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("highways", HIGHWAY_PRESETS,
                                           default_lat=45.46, default_lon=9.19,
                                           default_radius=20, max_radius=60)
    if not st.button("Search Highways", key="highways_btn", width="stretch", type="primary"):
        st.info("Select a location and click Search to explore highway networks.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying motorway data from OpenStreetMap..."):
        data = _fetch_highways(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    features = _extract_highways(data)
    if not features:
        st.warning("No motorways/highways found. Try a larger radius.")
        return

    type_counts = {}
    for f in features:
        t = f["highway_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    refs = set(f["ref"] for f in features if f["ref"])

    st.markdown("---")
    st.markdown("#### Highway Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Road Segments", len(features))
    c2.metric("Unique Route Refs", len(refs))
    c3.metric("Road Types", len(type_counts))

    st.markdown("---")
    st.markdown("#### Highway Network Map")
    m = _build_folium_map(lat, lon, zoom=10)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#10b981", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    color_map = {"motorway": "#10b981", "motorway_link": "#22d3ee", "trunk": "#f59e0b"}
    for f in features:
        if f["coords"] and len(f["coords"]) >= 2:
            folium.PolyLine(
                locations=f["coords"], color=color_map.get(f["highway_type"], "#10b981"),
                weight=3, opacity=0.7,
                popup=_safe_popup(f["name"], f["ref"],
                                  {"Lanes": f["lanes"], "Max Speed": f["maxspeed"]}
                                  if f["lanes"] or f["maxspeed"] else None),
            ).add_to(m)
    _render_map(m)

    _make_chart(type_counts, "Segments by Type",
                palette=color_map)

    with st.expander(f"Data Table ({len(features)} segments)", expanded=False):
        st.dataframe(
            _features_to_dataframe(features, ["name", "ref", "highway_type", "lanes", "maxspeed", "surface"]),
            width="stretch", hide_index=True,
        )
    _download_section(features, "highways")


def _render_ferries_map():
    """Render the Ferry Routes map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("ferries", FERRY_PRESETS,
                                           default_lat=37.45, default_lon=24.94,
                                           default_radius=50, max_radius=80)
    if not st.button("Search Ferry Routes", key="ferries_btn", width="stretch", type="primary"):
        st.info("Select a location and click Search to discover ferry routes.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying ferry data from OpenStreetMap..."):
        data = _fetch_ferries(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    routes, terminals = _extract_ferries(data)
    total = len(routes) + len(terminals)
    if total == 0:
        st.warning("No ferry features found. Try a larger radius or coastal location.")
        return

    st.markdown("---")
    st.markdown("#### Ferry Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ferry Routes", len(routes))
    c2.metric("Ferry Terminals", len(terminals))
    c3.metric("Total Features", total)

    st.markdown("---")
    st.markdown("#### Ferry Map")
    m = _build_folium_map(lat, lon, zoom=8)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#ec4899", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for route in routes:
        if route["coords"]:
            folium.PolyLine(
                locations=route["coords"], color="#ec4899",
                weight=3, opacity=0.8, dash_array="8",
                popup=_safe_popup(route["name"], "Ferry Route",
                                  {"Operator": route["operator"],
                                   "Duration": route["duration"]} if route["operator"] else None),
            ).add_to(m)
    for term in terminals:
        folium.CircleMarker(
            location=[term["lat"], term["lon"]], radius=6,
            color="#f97316", fill=True, fill_color="#f97316", fill_opacity=0.8,
            weight=2, popup=_safe_popup(term["name"], "Ferry Terminal"),
        ).add_to(m)
    _render_map(m)

    all_features = []
    for r in routes:
        all_features.append({"name": r["name"], "type": "route", "lat": r["lat"],
                              "lon": r["lon"], "operator": r["operator"],
                              "duration": r["duration"], "osm_id": r["osm_id"]})
    for t in terminals:
        all_features.append({"name": t["name"], "type": "terminal", "lat": t["lat"],
                              "lon": t["lon"], "operator": t["operator"], "osm_id": t["osm_id"]})
    with st.expander(f"Data Table ({len(all_features)} features)", expanded=False):
        st.dataframe(_features_to_dataframe(all_features), width="stretch", hide_index=True)
    _download_section(all_features, "ferries")


def _render_cycling_map():
    """Render the Cycling Infrastructure map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("cycling", CYCLING_PRESETS,
                                           default_lat=52.37, default_lon=4.90,
                                           default_radius=5, max_radius=25)
    if not st.button("Search Cycling Infrastructure", key="cycling_btn", width="stretch",
                     type="primary"):
        st.info("Select a location and click Search to explore cycling infrastructure.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying cycling data from OpenStreetMap..."):
        data = _fetch_cycling(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    paths, pois = _extract_cycling(data)
    total = len(paths) + len(pois)
    if total == 0:
        st.warning("No cycling infrastructure found. Try a different city.")
        return

    cycle_type_counts = {}
    for p in paths:
        t = p["cycle_type"]
        cycle_type_counts[t] = cycle_type_counts.get(t, 0) + 1
    poi_type_counts = {}
    for p in pois:
        t = p["poi_type"]
        poi_type_counts[t] = poi_type_counts.get(t, 0) + 1

    st.markdown("---")
    st.markdown("#### Cycling Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cycle Paths", len(paths))
    c2.metric("Bike Rentals", poi_type_counts.get("bicycle_rental", 0))
    c3.metric("Bike Parking", poi_type_counts.get("bicycle_parking", 0))
    c4.metric("Total Features", total)

    st.markdown("---")
    st.markdown("#### Cycling Map")
    m = _build_folium_map(lat, lon, zoom=13)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#22d3ee", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for p in paths:
        if p["coords"]:
            folium.PolyLine(
                locations=p["coords"], color="#22d3ee",
                weight=3, opacity=0.7,
                popup=_safe_popup(p["name"], p["cycle_type"],
                                  {"Surface": p["surface"]} if p["surface"] else None),
            ).add_to(m)
    for poi in pois:
        color = "#10b981" if poi["poi_type"] == "bicycle_rental" else "#f59e0b"
        folium.CircleMarker(
            location=[poi["lat"], poi["lon"]], radius=4,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            weight=1, popup=_safe_popup(poi["name"], poi["poi_type"]),
        ).add_to(m)
    _render_map(m)

    col_a, col_b = st.columns(2)
    with col_a:
        _make_chart(cycle_type_counts, "Cycle Path Types",
                    palette={k: "#22d3ee" for k in cycle_type_counts})
    with col_b:
        _make_chart(poi_type_counts, "Cycling POIs",
                    palette={"bicycle_rental": "#10b981", "bicycle_parking": "#f59e0b"})

    all_features = []
    for p in paths:
        all_features.append({"name": p["name"], "type": p["cycle_type"], "surface": p["surface"],
                              "lat": p["lat"], "lon": p["lon"], "osm_id": p["osm_id"]})
    for poi in pois:
        all_features.append({"name": poi["name"], "type": poi["poi_type"],
                              "capacity": poi["capacity"],
                              "lat": poi["lat"], "lon": poi["lon"], "osm_id": poi["osm_id"]})
    with st.expander(f"Data Table ({len(all_features)} features)", expanded=False):
        st.dataframe(_features_to_dataframe(all_features), width="stretch", hide_index=True)
    _download_section(all_features, "cycling")


def _render_metro_map():
    """Render the Metro Systems map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("metro", METRO_PRESETS,
                                           default_lat=48.86, default_lon=2.35,
                                           default_radius=8, max_radius=30)
    if not st.button("Search Metro System", key="metro_btn", width="stretch", type="primary"):
        st.info("Select a city and click Search to explore its metro system.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying metro data from OpenStreetMap..."):
        data = _fetch_metro(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    lines, stations = _extract_metro(data)
    total = len(lines) + len(stations)
    if total == 0:
        st.warning("No metro features found. Try a larger radius or a city with a metro system.")
        return

    networks = set(s["network"] for s in stations if s["network"])

    st.markdown("---")
    st.markdown("#### Metro Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Metro Lines", len(lines))
    c2.metric("Stations", len(stations))
    c3.metric("Networks", len(networks) if networks else "N/A")

    st.markdown("---")
    st.markdown("#### Metro Map")
    m = _build_folium_map(lat, lon, zoom=12)
    for line in lines:
        if line["coords"]:
            line_color = line["colour"] if line["colour"] else "#a855f7"
            folium.PolyLine(
                locations=line["coords"], color=line_color,
                weight=4, opacity=0.8,
                popup=_safe_popup(line["name"], "Metro Line"),
            ).add_to(m)
    for stn in stations:
        folium.CircleMarker(
            location=[stn["lat"], stn["lon"]], radius=5,
            color="#e8ecf4", fill=True, fill_color="#a855f7", fill_opacity=0.9,
            weight=2, popup=_safe_popup(stn["name"], "Metro Station",
                                        {"Network": stn["network"], "Line": stn["line"]}
                                        if stn["network"] else None),
        ).add_to(m)
    _render_map(m)

    all_features = []
    for s in stations:
        all_features.append({"name": s["name"], "type": "station", "network": s["network"],
                              "line": s["line"], "wheelchair": s["wheelchair"],
                              "lat": s["lat"], "lon": s["lon"], "osm_id": s["osm_id"]})
    for ln in lines:
        all_features.append({"name": ln["name"], "type": "metro_line", "operator": ln["operator"],
                              "lat": ln["lat"], "lon": ln["lon"], "osm_id": ln["osm_id"]})
    with st.expander(f"Data Table ({len(all_features)} features)", expanded=False):
        st.dataframe(_features_to_dataframe(all_features), width="stretch", hide_index=True)
    _download_section(all_features, "metro")


def _render_cablecars_map():
    """Render the Cable Cars & Funiculars map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("cablecars", CABLECAR_PRESETS,
                                           default_lat=46.02, default_lon=7.75,
                                           default_radius=10, max_radius=40)
    if not st.button("Search Cable Cars", key="cablecars_btn", width="stretch", type="primary"):
        st.info("Select a location and click Search to discover cable cars and funiculars.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying aerialway data from OpenStreetMap..."):
        data = _fetch_cablecars(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    features = _extract_cablecars(data)
    if not features:
        st.warning("No cable cars or funiculars found. Try a mountain region.")
        return

    type_counts = {}
    for f in features:
        t = f["aerialway_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    st.markdown("---")
    st.markdown("#### Cable Car Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Features", len(features))
    c2.metric("Aerialway Types", len(type_counts))
    c3.metric("Stations", type_counts.get("station", 0))

    st.markdown("---")
    st.markdown("#### Cable Car Map")
    m = _build_folium_map(lat, lon, zoom=11)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#f97316", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for f in features:
        if f["coords"] and len(f["coords"]) >= 2:
            folium.PolyLine(
                locations=f["coords"], color="#f97316",
                weight=3, opacity=0.8,
                popup=_safe_popup(f["name"], f["aerialway_type"],
                                  {"Operator": f["operator"]} if f["operator"] else None),
            ).add_to(m)
        elif f["aerialway_type"] == "station":
            folium.CircleMarker(
                location=[f["lat"], f["lon"]], radius=6,
                color="#f97316", fill=True, fill_color="#f97316", fill_opacity=0.8,
                weight=2, popup=_safe_popup(f["name"], "Aerialway Station"),
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[f["lat"], f["lon"]], radius=3,
                color="#f97316", fill=True, fill_color="#f97316", fill_opacity=0.6,
                weight=1, popup=_safe_popup(f["name"], f["aerialway_type"]),
            ).add_to(m)
    _render_map(m)

    _make_chart(type_counts, "Aerialway Types",
                palette={k: "#f97316" for k in type_counts})

    with st.expander(f"Data Table ({len(features)} features)", expanded=False):
        st.dataframe(
            _features_to_dataframe(features,
                                    ["name", "aerialway_type", "operator", "capacity", "duration", "lat", "lon"]),
            width="stretch", hide_index=True,
        )
    _download_section(features, "cablecars")


def _render_historic_railways_map():
    """Render the Historic Railways map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("hist_rw", HISTORIC_RW_PRESETS,
                                           default_lat=53.30, default_lon=-1.80,
                                           default_radius=15, max_radius=50)
    if not st.button("Search Historic Railways", key="hist_rw_btn", width="stretch",
                     type="primary"):
        st.info("Select a location and click Search to discover historic railway lines.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying historic railway data from OpenStreetMap..."):
        data = _fetch_historic_railways(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    lines, stations = _extract_historic_railways(data)
    total = len(lines) + len(stations)
    if total == 0:
        st.warning("No historic railway features found. Try a different region or larger radius.")
        return

    status_counts = {}
    for ln in lines:
        s = ln["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    status_colors = {
        "abandoned": "#ef4444", "disused": "#f59e0b",
        "preserved": "#10b981", "narrow_gauge": "#8b5cf6",
    }

    st.markdown("---")
    st.markdown("#### Historic Railway Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Railway Lines", len(lines))
    c2.metric("Historic Stations", len(stations))
    c3.metric("Preserved Lines", status_counts.get("preserved", 0))
    c4.metric("Abandoned Lines", status_counts.get("abandoned", 0))

    st.markdown("---")
    st.markdown("#### Historic Railway Map")
    legend_items = " ".join([
        f'<span style="color:{status_colors.get(s, "#8b97b0")}; font-size:0.8rem;">'
        f"● {escape(s.title())}</span>"
        for s in status_colors
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'{legend_items}</div>',
        unsafe_allow_html=True,
    )

    m = _build_folium_map(lat, lon, zoom=10)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#64748b", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for ln in lines:
        if ln["coords"]:
            color = status_colors.get(ln["status"], "#8b97b0")
            folium.PolyLine(
                locations=ln["coords"], color=color,
                weight=3, opacity=0.7, dash_array="6",
                popup=_safe_popup(ln["name"], ln["status"].title(),
                                  {"Gauge": ln["gauge"]} if ln["gauge"] else None),
            ).add_to(m)
    for stn in stations:
        folium.CircleMarker(
            location=[stn["lat"], stn["lon"]], radius=5,
            color="#e8ecf4", fill=True, fill_color="#64748b", fill_opacity=0.8,
            weight=2, popup=_safe_popup(stn["name"], f"Historic Station ({stn['status']})"),
        ).add_to(m)
    _render_map(m)

    _make_chart(status_counts, "Railway Status", palette=status_colors)

    all_features = []
    for ln in lines:
        all_features.append({"name": ln["name"], "type": "railway_line", "status": ln["status"],
                              "gauge": ln["gauge"], "lat": ln["lat"], "lon": ln["lon"],
                              "osm_id": ln["osm_id"]})
    for stn in stations:
        all_features.append({"name": stn["name"], "type": "station", "status": stn["status"],
                              "lat": stn["lat"], "lon": stn["lon"], "osm_id": stn["osm_id"]})
    with st.expander(f"Data Table ({len(all_features)} features)", expanded=False):
        st.dataframe(_features_to_dataframe(all_features), width="stretch", hide_index=True)
    _download_section(all_features, "historic_railways")


def _render_canals_map():
    """Render the Canals & Waterways map."""
    st.markdown("#### Search Parameters")
    lat, lon, radius = _location_controls("canals", CANAL_PRESETS,
                                           default_lat=52.37, default_lon=4.90,
                                           default_radius=5, max_radius=40)
    if not st.button("Search Canals & Waterways", key="canals_btn", width="stretch",
                     type="primary"):
        st.info("Select a location and click Search to discover canals and navigable waterways.")
        return

    south, west, north, east = _bbox_from_center(lat, lon, radius)
    with st.spinner("Querying canal data from OpenStreetMap..."):
        data = _fetch_canals(south, west, north, east)
    if not _overpass_result_ok(data):
        return
    waterways, locks = _extract_canals(data)
    total = len(waterways) + len(locks)
    if total == 0:
        st.warning("No canals or navigable waterways found. Try a different location.")
        return

    ww_type_counts = {}
    for w in waterways:
        t = w["waterway_type"]
        ww_type_counts[t] = ww_type_counts.get(t, 0) + 1

    st.markdown("---")
    st.markdown("#### Canal & Waterway Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Waterway Segments", len(waterways))
    c2.metric("Locks / Features", len(locks))
    c3.metric("Canals", ww_type_counts.get("canal", 0))
    c4.metric("Navigable Rivers", ww_type_counts.get("river", 0))

    st.markdown("---")
    st.markdown("#### Waterway Map")
    ww_colors = {"canal": "#38bdf8", "river": "#3b82f6"}
    legend_items = " ".join([
        f'<span style="color:{ww_colors.get(k, "#8b97b0")}; font-size:0.8rem;">● {escape(k.title())}</span>'
        for k in ww_colors
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'{legend_items}'
        f' <span style="color:#f59e0b; font-size:0.8rem;">● Lock</span></div>',
        unsafe_allow_html=True,
    )

    m = _build_folium_map(lat, lon, zoom=13)
    folium.Circle(location=[lat, lon], radius=radius * 1000,
                  color="#38bdf8", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    for w in waterways:
        if w["coords"]:
            color = ww_colors.get(w["waterway_type"], "#38bdf8")
            folium.PolyLine(
                locations=w["coords"], color=color,
                weight=3, opacity=0.75,
                popup=_safe_popup(w["name"], w["waterway_type"].title(),
                                  {"Boat": w["boat"], "Width": w["width"]}
                                  if w["boat"] or w["width"] else None),
            ).add_to(m)
    for lk in locks:
        folium.CircleMarker(
            location=[lk["lat"], lk["lon"]], radius=5,
            color="#f59e0b", fill=True, fill_color="#f59e0b", fill_opacity=0.8,
            weight=2, popup=_safe_popup(lk["name"], lk["lock_type"].replace("_", " ").title()),
        ).add_to(m)
    _render_map(m)

    col_a, col_b = st.columns(2)
    with col_a:
        _make_chart(ww_type_counts, "Waterway Types",
                    palette=ww_colors)
    with col_b:
        named_ww = [w for w in waterways if w["name"] not in ("Canal", "River")]
        if named_ww:
            st.markdown("#### Named Waterways")
            for w in named_ww[:20]:
                color = ww_colors.get(w["waterway_type"], "#38bdf8")
                st.markdown(
                    f'<div style="display:flex; align-items:center; margin-bottom:0.4rem;">'
                    f'<div style="width:8px; height:30px; border-radius:4px; background:{color}; '
                    f'margin-right:0.6rem; flex-shrink:0;"></div>'
                    f'<div>'
                    f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">'
                    f'{escape(w["name"])}</div>'
                    f'<div style="color:#8b97b0; font-size:0.75rem;">'
                    f'{escape(w["waterway_type"].title())}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    all_features = []
    for w in waterways:
        all_features.append({"name": w["name"], "type": w["waterway_type"], "boat": w["boat"],
                              "width": w["width"], "lat": w["lat"], "lon": w["lon"],
                              "osm_id": w["osm_id"]})
    for lk in locks:
        all_features.append({"name": lk["name"], "type": lk["lock_type"],
                              "lat": lk["lat"], "lon": lk["lon"], "osm_id": lk["osm_id"]})
    with st.expander(f"Data Table ({len(all_features)} features)", expanded=False):
        st.dataframe(_features_to_dataframe(all_features), width="stretch", hide_index=True)
    _download_section(all_features, "canals")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

_MAP_RENDERERS = {
    "World Airports": _render_airports_map,
    "Global Railways": _render_railways_map,
    "Shipping Routes": _render_shipping_map,
    "World Bridges": _render_bridges_map,
    "Tunnels": _render_tunnels_map,
    "Highway Networks": _render_highways_map,
    "Ferry Routes": _render_ferries_map,
    "Cycling Infrastructure": _render_cycling_map,
    "Metro Systems": _render_metro_map,
    "Cable Cars & Funiculars": _render_cablecars_map,
    "Historic Railways": _render_historic_railways_map,
    "Canals & Waterways": _render_canals_map,
}


def render_transport_maps_tab():
    """Main entry point for the Transport & Route Maps tab."""

    st.markdown("""
    <div class="tab-header amber">
        <h4>Transport & Route Maps</h4>
        <p>Explore 12 composite transport visualizations: airports, railways, shipping lanes, bridges, tunnels, highways, ferries, cycling, metro, cable cars, historic railways, and canals. All data from free OpenStreetMap / Overpass APIs.</p>
    </div>
    """, unsafe_allow_html=True)

    # Map type selector
    selected_map = st.radio(
        "Select Transport Map",
        MAP_TYPES,
        horizontal=True,
        key="transport_map_type",
    )

    st.markdown("---")

    # Dispatch to the selected map renderer
    renderer = _MAP_RENDERERS.get(selected_map)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown map type: {selected_map}")
