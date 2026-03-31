"""
Satellite Imagery module for TerraScout AI.
Real-time satellite views with MODIS, VIIRS, Sentinel-2, NDVI overlays,
terrain elevation, camera altitude estimation, and date comparison.
Uses NASA GIBS, EOX, OpenTopoData, and Open-Meteo APIs (all free, no auth).
"""

import io
import logging
import math
import requests
import streamlit as st
from datetime import date, timedelta

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

try:
    from streamlit_folium import st_folium
except ImportError:
    st_folium = None

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from src.location_context import render_location_selector, get_location, has_location
from src.map_factory import MapFactory
from src.satellite_intelligence import fetch_ndvi_data

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IMAGERY_LAYERS = {
    "MODIS True Color": {
        "layer": "MODIS_Terra_CorrectedReflectance_TrueColor",
        "base": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best",
        "tilematrixset": "GoogleMapsCompatible_Level9",
        "ext": "jpg",
        "max_zoom": 9,
        "desc": "Terra MODIS corrected reflectance — 250 m daily",
        "daily": True,
    },
    "VIIRS True Color": {
        "layer": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
        "base": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best",
        "tilematrixset": "GoogleMapsCompatible_Level9",
        "ext": "jpg",
        "max_zoom": 9,
        "desc": "Suomi-NPP VIIRS corrected reflectance — 375 m daily",
        "daily": True,
    },
    "VIIRS False Color (IR)": {
        "layer": "VIIRS_SNPP_CorrectedReflectance_BandsM11-I2-I1",
        "base": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best",
        "tilematrixset": "GoogleMapsCompatible_Level9",
        "ext": "jpg",
        "max_zoom": 9,
        "desc": "VIIRS near-IR false color — vegetation & land use",
        "daily": True,
    },
    "NDVI 8-Day": {
        "layer": "MODIS_Terra_NDVI_8Day",
        "base": "https://map1.vis.earthdata.nasa.gov/wmts-webmerc",
        "tilematrixset": "GoogleMapsCompatible_Level9",
        "ext": "png",
        "max_zoom": 8,
        "desc": "MODIS 8-day NDVI composite — vegetation density",
        "daily": False,
    },
    "Thermal Anomalies": {
        "layer": "MODIS_Terra_Thermal_Anomalies_Day",
        "base": "https://map1.vis.earthdata.nasa.gov/wmts-webmerc",
        "tilematrixset": "GoogleMapsCompatible_Level7",
        "ext": "png",
        "max_zoom": 7,
        "desc": "MODIS daytime thermal anomalies — active fires & heat",
        "daily": True,
    },
}

S2_CLOUDLESS_YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018]

ZOOM_ALTITUDE_MAP = {
    1: "20,000 km",
    2: "10,000 km",
    3: "5,000 km",
    4: "2,500 km",
    5: "1,200 km",
    6: "600 km",
    7: "300 km",
    8: "150 km",
    9: "75 km",
    10: "38 km",
    11: "19 km",
    12: "9.5 km",
    13: "4.8 km",
    14: "2.4 km",
    15: "1.2 km",
    16: "600 m",
    17: "300 m",
    18: "150 m",
}

_CLR = {
    "bg": "#1a1a2e",
    "card": "rgba(26,26,46,0.85)",
    "border": "#2d5a3d",
    "text": "#e8ecf4",
    "muted": "#8b97b0",
    "accent": "#22c55e",
}

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _resolve_date(layer_cfg: dict, user_date: date) -> str:
    """Return the appropriate date string for a GIBS layer."""
    if layer_cfg["daily"]:
        return user_date.strftime("%Y-%m-%d")
    # 8-day composite: round down to nearest period start
    doy = user_date.timetuple().tm_yday
    ndvi_doy = max(1, (doy // 8) * 8 - 8)
    rounded = date(user_date.year, 1, 1) + timedelta(days=ndvi_doy - 1)
    return rounded.strftime("%Y-%m-%d")


def _build_tile_url(layer_cfg: dict, date_str: str) -> str:
    """Build a full WMTS tile URL for a GIBS layer."""
    return (
        f"{layer_cfg['base']}/{layer_cfg['layer']}/default/"
        f"{date_str}/{layer_cfg['tilematrixset']}/{{z}}/{{y}}/{{x}}.{layer_cfg['ext']}"
    )


@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> dict:
    """Fetch terrain elevation from OpenTopoData SRTM30m, fallback to Open-Meteo."""
    # Primary: OpenTopoData
    try:
        url = f"https://api.opentopodata.org/v1/srtm30m?locations={lat},{lon}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results and results[0].get("elevation") is not None:
            return {"elevation_m": round(results[0]["elevation"], 1), "source": "SRTM30m"}
    except Exception as exc:
        logger.debug("OpenTopoData elevation failed: %s", exc)

    # Fallback: Open-Meteo
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        elev = data.get("elevation")
        if elev is not None:
            vals = elev if isinstance(elev, list) else [elev]
            if vals and vals[0] is not None:
                return {"elevation_m": round(vals[0], 1), "source": "Open-Meteo"}
    except Exception as exc:
        logger.debug("Open-Meteo elevation failed: %s", exc)

    return {"elevation_m": None, "source": "N/A"}


# ---------------------------------------------------------------------------
# Satellite snapshot (tile stitching)
# ---------------------------------------------------------------------------

TILE_SIZE = 256  # Standard WMTS tile pixel size


def _latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple:
    """Convert lat/lon to tile (x, y) at a given zoom level (Web Mercator)."""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    x = max(0, min(n - 1, x))
    y = max(0, min(n - 1, y))
    return x, y


def _tile_to_latlon(x: int, y: int, zoom: int) -> tuple:
    """Convert tile (x, y) top-left corner to lat/lon."""
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def _fetch_snapshot_image(layer_cfg: dict, date_str: str, lat: float, lon: float,
                          zoom: int, grid: int = 5) -> "Image.Image | None":
    """Fetch a grid of WMTS tiles around (lat, lon) and stitch into one PIL Image.

    Args:
        layer_cfg: Layer configuration dict from IMAGERY_LAYERS.
        date_str: Resolved date string.
        lat, lon: Center coordinates.
        zoom: Zoom level (clamped to layer max_zoom).
        grid: Grid size (e.g. 5 means 5x5 tiles).

    Returns:
        A PIL Image or None on failure.
    """
    if not HAS_PIL:
        return None

    z = min(zoom, layer_cfg["max_zoom"])
    cx, cy = _latlon_to_tile(lat, lon, z)
    half = grid // 2

    img = Image.new("RGB", (grid * TILE_SIZE, grid * TILE_SIZE))
    n_tiles = 2 ** z
    ok = 0

    base_url = (
        f"{layer_cfg['base']}/{layer_cfg['layer']}/default/"
        f"{date_str}/{layer_cfg['tilematrixset']}"
    )

    for dy in range(grid):
        for dx in range(grid):
            tx = cx - half + dx
            ty = cy - half + dy
            if tx < 0 or ty < 0 or tx >= n_tiles or ty >= n_tiles:
                continue
            url = f"{base_url}/{z}/{ty}/{tx}.{layer_cfg['ext']}"
            try:
                resp = requests.get(url, timeout=8)
                if resp.status_code == 200 and len(resp.content) > 100:
                    tile_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    img.paste(tile_img, (dx * TILE_SIZE, dy * TILE_SIZE))
                    ok += 1
            except Exception:
                pass

    return img if ok > 0 else None


def _fetch_s2_snapshot(year: int, lat: float, lon: float,
                       zoom: int, grid: int = 5) -> "Image.Image | None":
    """Fetch Sentinel-2 Cloudless tiles and stitch into one PIL Image."""
    if not HAS_PIL:
        return None

    z = min(zoom, 15)  # EOX supports up to ~15
    cx, cy = _latlon_to_tile(lat, lon, z)
    half = grid // 2

    img = Image.new("RGB", (grid * TILE_SIZE, grid * TILE_SIZE))
    n_tiles = 2 ** z
    ok = 0

    for dy in range(grid):
        for dx in range(grid):
            tx = cx - half + dx
            ty = cy - half + dy
            if tx < 0 or ty < 0 or tx >= n_tiles or ty >= n_tiles:
                continue
            url = (
                f"https://tiles.maps.eox.at/wmts/1.0.0/"
                f"s2cloudless-{year}_3857/default/"
                f"GoogleMapsCompatible/{z}/{ty}/{tx}.jpg"
            )
            try:
                resp = requests.get(url, timeout=8)
                if resp.status_code == 200 and len(resp.content) > 100:
                    tile_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    img.paste(tile_img, (dx * TILE_SIZE, dy * TILE_SIZE))
                    ok += 1
            except Exception:
                pass

    return img if ok > 0 else None


def _image_to_bytes(img: "Image.Image", fmt: str = "PNG") -> bytes:
    """Convert a PIL Image to bytes for download."""
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Map builders
# ---------------------------------------------------------------------------


def _build_satellite_map(lat, lon, zoom, selected_layers, user_date, s2_year, show_s2):
    """Build a Folium map with selected GIBS layers and optional Sentinel-2."""
    m = MapFactory.create_base_map(center=(lat, lon), zoom=zoom, tile_layer="cartodb_dark")

    # Add GIBS layers
    for layer_name in selected_layers:
        cfg = IMAGERY_LAYERS.get(layer_name)
        if not cfg:
            continue
        date_str = _resolve_date(cfg, user_date)
        tile_url = _build_tile_url(cfg, date_str)
        folium.TileLayer(
            tiles=tile_url,
            attr="NASA GIBS",
            name=layer_name,
            overlay=True,
            opacity=0.75,
            max_zoom=cfg["max_zoom"],
        ).add_to(m)

    # Sentinel-2 Cloudless
    if show_s2:
        s2_url = (
            f"https://tiles.maps.eox.at/wmts/1.0.0/"
            f"s2cloudless-{s2_year}_3857/default/"
            f"GoogleMapsCompatible/{{z}}/{{y}}/{{x}}.jpg"
        )
        folium.TileLayer(
            tiles=s2_url,
            attr="EOX Sentinel-2 Cloudless",
            name=f"Sentinel-2 {s2_year}",
            overlay=True,
            opacity=0.85,
        ).add_to(m)

    # Center marker
    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        tooltip=f"{lat:.4f}, {lon:.4f}",
    ).add_to(m)

    # Coverage circle (approximate based on zoom)
    radius_map = {
        1: 5000000, 2: 2500000, 3: 1200000, 4: 600000, 5: 300000,
        6: 150000, 7: 75000, 8: 38000, 9: 19000, 10: 9500,
        11: 4800, 12: 2400, 13: 1200, 14: 600, 15: 300,
        16: 150, 17: 75, 18: 38,
    }
    radius = radius_map.get(zoom, 75000)
    folium.Circle(
        location=[lat, lon],
        radius=radius,
        color="#ef4444",
        fill=False,
        weight=1,
        dash_array="5",
        tooltip="Approximate coverage",
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _build_comparison_maps(lat, lon, zoom, layer_name, date_a, date_b):
    """Build two Folium maps for date comparison."""
    maps = []
    cfg = IMAGERY_LAYERS.get(layer_name)
    if not cfg:
        return None, None

    for d in [date_a, date_b]:
        m = MapFactory.create_base_map(center=(lat, lon), zoom=zoom, tile_layer="cartodb_dark")
        date_str = _resolve_date(cfg, d)
        tile_url = _build_tile_url(cfg, date_str)
        folium.TileLayer(
            tiles=tile_url,
            attr="NASA GIBS",
            name=f"{layer_name} ({date_str})",
            overlay=True,
            opacity=0.8,
            max_zoom=cfg["max_zoom"],
        ).add_to(m)
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
            tooltip=f"{lat:.4f}, {lon:.4f}",
        ).add_to(m)
        maps.append(m)

    return maps[0], maps[1]


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------


def render_satellite_imagery_tab():
    """Render the Satellite Imagery page."""
    st.markdown("## \U0001f6f0\ufe0f Satellite Imagery")
    st.caption(
        "Real-time satellite views — MODIS, VIIRS, Sentinel-2, NDVI, "
        "elevation & date comparison"
    )

    if not HAS_FOLIUM:
        st.error("Folium is required for this module. Install with: pip install folium")
        return
    if st_folium is None:
        st.error("streamlit-folium is required. Install with: pip install streamlit-folium")
        return

    # ── 1. Location selector ──────────────────────────────────────────────
    st.markdown("### 1 \u2014 Select Location")
    render_location_selector(key_prefix="satimg")

    if not has_location():
        st.info("Select a location above to view satellite imagery.")
        return

    loc = get_location()
    lat, lon = loc["lat"], loc["lon"]

    # ── 2. Imagery settings ───────────────────────────────────────────────
    st.markdown("### 2 \u2014 Imagery Settings")
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_layers = st.multiselect(
            "GIBS Layers",
            options=list(IMAGERY_LAYERS.keys()),
            default=["MODIS True Color"],
            key="satimg_layers",
        )
    with col2:
        yesterday = date.today() - timedelta(days=1)
        user_date = st.date_input(
            "Imagery Date",
            value=yesterday,
            max_value=yesterday,
            key="satimg_date",
        )
    with col3:
        zoom = st.slider(
            "Zoom Level",
            min_value=1,
            max_value=18,
            value=7,
            key="satimg_zoom",
        )

    col_s2a, col_s2b = st.columns(2)
    with col_s2a:
        show_s2 = st.checkbox("Overlay Sentinel-2 Cloudless", key="satimg_s2_toggle")
    with col_s2b:
        s2_year = st.selectbox(
            "Sentinel-2 Year",
            options=S2_CLOUDLESS_YEARS,
            index=0,
            key="satimg_s2_year",
            disabled=not show_s2,
        )

    # ── 3. Location & altitude info ───────────────────────────────────────
    st.markdown("### 3 \u2014 Location & Altitude Info")
    elev_data = _fetch_elevation(lat, lon)
    elev_m = elev_data["elevation_m"]
    elev_src = elev_data["source"]
    camera_alt = ZOOM_ALTITUDE_MAP.get(zoom, "N/A")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Coordinates", f"{lat:.4f}, {lon:.4f}")
    mc2.metric("Terrain Elevation", f"{elev_m} m" if elev_m is not None else "N/A", help=f"Source: {elev_src}")
    mc3.metric("Camera Altitude", camera_alt)
    mc4.metric("Zoom Level", f"{zoom}")

    # ── 4. Satellite map ──────────────────────────────────────────────────
    st.markdown("### 4 \u2014 Satellite Map")

    sat_map = _build_satellite_map(lat, lon, zoom, selected_layers, user_date, s2_year, show_s2)
    st_folium(sat_map, width=None, height=600, key="satimg_main_map", returned_objects=[])

    with st.expander("Layer details"):
        for lname in selected_layers:
            cfg = IMAGERY_LAYERS.get(lname)
            if cfg:
                date_str = _resolve_date(cfg, user_date)
                st.markdown(
                    f"**{lname}** — {cfg['desc']}  \n"
                    f"Date: `{date_str}` · Max zoom: {cfg['max_zoom']} · "
                    f"Format: {cfg['ext'].upper()}"
                )
        if show_s2:
            st.markdown(
                f"**Sentinel-2 Cloudless {s2_year}** — EOX annual composite at 10 m resolution"
            )

    # ── 5. Date comparison ────────────────────────────────────────────────
    st.markdown("### 5 \u2014 Date Comparison")

    cmp_col1, cmp_col2, cmp_col3 = st.columns(3)
    with cmp_col1:
        cmp_layer = st.selectbox(
            "Compare Layer",
            options=list(IMAGERY_LAYERS.keys()),
            index=0,
            key="satimg_cmp_layer",
        )
    with cmp_col2:
        date_a = st.date_input(
            "Date A",
            value=date.today() - timedelta(days=30),
            max_value=yesterday,
            key="satimg_date_a",
        )
    with cmp_col3:
        date_b = st.date_input(
            "Date B",
            value=yesterday,
            max_value=yesterday,
            key="satimg_date_b",
        )

    if st.button("Compare Dates", key="satimg_compare_btn", type="primary", use_container_width=True):
        map_a, map_b = _build_comparison_maps(lat, lon, zoom, cmp_layer, date_a, date_b)
        if map_a and map_b:
            cfg = IMAGERY_LAYERS[cmp_layer]
            left, right = st.columns(2)
            with left:
                st.caption(f"**Date A:** {_resolve_date(cfg, date_a)}")
                st_folium(map_a, width=None, height=400, key="satimg_cmp_a", returned_objects=[])
            with right:
                st.caption(f"**Date B:** {_resolve_date(cfg, date_b)}")
                st_folium(map_b, width=None, height=400, key="satimg_cmp_b", returned_objects=[])
        else:
            st.warning("Could not build comparison maps for the selected layer.")

    # ── 6. Satellite Snapshot (real image) ────────────────────────────────
    st.markdown("### 6 \u2014 Satellite Snapshot")
    st.caption(
        "Generate a real satellite image at this location, date, and zoom. "
        "Tiles are fetched from NASA GIBS / EOX and stitched into a single picture."
    )

    if not HAS_PIL:
        st.warning("Pillow is required for snapshots. Install with: pip install Pillow")
    else:
        snap_c1, snap_c2, snap_c3 = st.columns(3)
        with snap_c1:
            # Combine GIBS + Sentinel-2 options
            snap_sources = list(IMAGERY_LAYERS.keys()) + [
                f"Sentinel-2 Cloudless {y}" for y in S2_CLOUDLESS_YEARS
            ]
            snap_layer = st.selectbox(
                "Image Source",
                options=snap_sources,
                index=0,
                key="satimg_snap_source",
            )
        with snap_c2:
            snap_date = st.date_input(
                "Snapshot Date",
                value=yesterday,
                max_value=yesterday,
                key="satimg_snap_date",
            )
        with snap_c3:
            snap_zoom = st.slider(
                "Snapshot Zoom",
                min_value=1,
                max_value=14,
                value=min(zoom, 9),
                key="satimg_snap_zoom",
                help="Higher zoom = more detail but smaller area",
            )

        snap_gc1, snap_gc2 = st.columns(2)
        with snap_gc1:
            snap_grid = st.select_slider(
                "Image Size (tiles)",
                options=[3, 5, 7, 9],
                value=5,
                key="satimg_snap_grid",
                help="3x3 = 768px, 5x5 = 1280px, 7x7 = 1792px, 9x9 = 2304px",
            )
        with snap_gc2:
            snap_alt = ZOOM_ALTITUDE_MAP.get(snap_zoom, "N/A")
            st.metric("Camera Altitude", snap_alt)
            px = snap_grid * TILE_SIZE
            st.caption(f"Output: {px} x {px} px")

        if st.button("Generate Snapshot", key="satimg_snap_btn", type="primary", use_container_width=True):
            is_s2 = snap_layer.startswith("Sentinel-2 Cloudless")
            with st.spinner("Downloading satellite tiles..."):
                if is_s2:
                    s2_yr = int(snap_layer.split()[-1])
                    snap_img = _fetch_s2_snapshot(s2_yr, lat, lon, snap_zoom, snap_grid)
                    snap_label = f"Sentinel-2 Cloudless {s2_yr}"
                else:
                    cfg = IMAGERY_LAYERS[snap_layer]
                    date_str = _resolve_date(cfg, snap_date)
                    snap_img = _fetch_snapshot_image(cfg, date_str, lat, lon, snap_zoom, snap_grid)
                    snap_label = f"{snap_layer} — {date_str}"

            if snap_img:
                st.image(
                    snap_img,
                    caption=f"{snap_label} | {lat:.4f}, {lon:.4f} | Zoom {snap_zoom} ({snap_alt})",
                    use_container_width=True,
                )
                # Download buttons
                dl1, dl2 = st.columns(2)
                png_bytes = _image_to_bytes(snap_img, "PNG")
                jpg_bytes = _image_to_bytes(snap_img, "JPEG")
                fname = f"satellite_{lat:.4f}_{lon:.4f}_z{snap_zoom}"
                with dl1:
                    st.download_button(
                        "Download PNG",
                        data=png_bytes,
                        file_name=f"{fname}.png",
                        mime="image/png",
                        key="satimg_dl_png",
                        use_container_width=True,
                    )
                with dl2:
                    st.download_button(
                        "Download JPG",
                        data=jpg_bytes,
                        file_name=f"{fname}.jpg",
                        mime="image/jpeg",
                        key="satimg_dl_jpg",
                        use_container_width=True,
                    )
            else:
                st.error(
                    "Could not generate snapshot. The server may not have data "
                    "for this date/zoom. Try a different date or lower zoom."
                )

    # ── 7. NDVI Vegetation profile ────────────────────────────────────────
    st.markdown("### 7 \u2014 NDVI Vegetation Profile")

    with st.spinner("Fetching NDVI data..."):
        ndvi = fetch_ndvi_data(lat, lon)

    ndvi_val = ndvi.get("ndvi_current", 0)
    ndvi_class = ndvi.get("ndvi_classification", "Unknown")
    ndvi_health = ndvi.get("vegetation_health", "Unknown")
    ndvi_estimated = ndvi.get("estimated", True)
    green_pct = ndvi.get("green_cover_pct", 0)
    seasonal = ndvi.get("seasonal_variation", "N/A")

    n1, n2, n3 = st.columns(3)
    n1.metric("NDVI Value", f"{ndvi_val:.3f}", help="0=bare, 1=dense vegetation")
    n2.metric("Classification", ndvi_class)
    n3.metric("Vegetation Health", ndvi_health)

    n4, n5, n6 = st.columns(3)
    n4.metric("Green Cover", f"{green_pct}%")
    n5.metric("Seasonal Variation", seasonal)
    n6.metric("Data Source", "MODIS Satellite" if not ndvi_estimated else "Climate Estimate")

    # NDVI gauge
    if HAS_PLOTLY:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ndvi_val,
            title={"text": "NDVI Index"},
            gauge={
                "axis": {"range": [0, 1], "tickwidth": 1},
                "bar": {"color": "#22c55e"},
                "steps": [
                    {"range": [0, 0.1], "color": "#4a1a1a"},
                    {"range": [0.1, 0.2], "color": "#6b3a00"},
                    {"range": [0.2, 0.4], "color": "#4a6b00"},
                    {"range": [0.4, 0.6], "color": "#2d6b2d"},
                    {"range": [0.6, 0.8], "color": "#1a5c1a"},
                    {"range": [0.8, 1.0], "color": "#0d4d0d"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 2},
                    "thickness": 0.8,
                    "value": ndvi_val,
                },
            },
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=_CLR["bg"],
            plot_bgcolor=_CLR["bg"],
            height=250,
            margin=dict(t=40, b=10, l=30, r=30),
        )
        st.plotly_chart(fig, use_container_width=True, key="satimg_ndvi_gauge")
