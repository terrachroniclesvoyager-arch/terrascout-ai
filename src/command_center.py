"""
Command Center - Unified Intelligence Home Page for TerraScout AI.
Satellite Ops-Center style dashboard with advanced charts:
polar area, sunburst, treemap, network graph, upgraded gauge/waterfall.
"""

import html as html_module
import logging
import math
from datetime import date, timedelta

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import folium
    from folium import plugins as folium_plugins
    from streamlit.components.v1 import html as st_html
    from src.map_factory import MapFactory
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

from src.location_context import (
    init_location_context,
    get_location,
    has_location,
    get_short_name,
    render_location_selector,
)
from src.data_hub import get_hub_data
from src.unified_intelligence import (
    INTELLIGENCE_DOMAINS,
    _classify_score,
    _compute_overall_score,
    compute_advanced_analytics,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OPS-CENTER COLOR PALETTE (shared across all charts)
# ---------------------------------------------------------------------------
OPS_BG = "#050510"
OPS_PANEL = "#0a0a18"
OPS_GRID = "#0d1225"
OPS_CYAN = "#00f0ff"
OPS_GREEN = "#00ff88"
OPS_AMBER = "#ffaa00"
OPS_RED = "#ff3344"
OPS_BLUE = "#4488ff"
OPS_PURPLE = "#aa55ff"
OPS_TEXT = "#e0e8f0"
OPS_TEXT_DIM = "#5a7090"

# Per-domain colors in the ops palette
_DOMAIN_OPS_COLORS = {
    "habitability": OPS_BLUE,
    "agriculture": OPS_GREEN,
    "ecology": "#00cc66",
    "hazard_safety": OPS_RED,
    "water_resources": OPS_CYAN,
    "infrastructure": OPS_PURPLE,
    "climate_comfort": OPS_AMBER,
    "economic_potential": "#ff66aa",
    "air_environment": "#6688ff",
    "geological_stability": "#cc88ff",
}

# ---------------------------------------------------------------------------
# FOLIUM MAP HELPERS
# ---------------------------------------------------------------------------

def _get_element_coords(el):
    """Get (lat, lon) from an Overpass element (node or way/relation with center)."""
    if not isinstance(el, dict):
        return None
    lat = el.get("lat")
    lon = el.get("lon")
    if lat is None or lon is None:
        c = el.get("center", {})
        lat = c.get("lat")
        lon = c.get("lon")
    if lat is not None and lon is not None:
        return (float(lat), float(lon))
    return None


# ---------------------------------------------------------------------------
# TOTAL INTELLIGENCE MAP — HELPER FUNCTIONS
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def _fetch_rainviewer_tiles():
    """Fetch latest radar + satellite IR tile URLs from RainViewer (1 GET, cached 10 min)."""
    try:
        resp = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        host = data.get("host", "https://tilecache.rainviewer.com")
        # Radar
        radar_frames = data.get("radar", {}).get("past", [])
        radar_url = None
        if radar_frames:
            ts = radar_frames[-1].get("path", "")
            radar_url = f"{host}{ts}/256/{{z}}/{{x}}/{{y}}/6/1_1.png"
        # Satellite IR
        ir_frames = data.get("satellite", {}).get("infrared", [])
        ir_url = None
        if ir_frames:
            ts = ir_frames[-1].get("path", "")
            ir_url = f"{host}{ts}/256/{{z}}/{{x}}/{{y}}/0/0_0.png"
        return {"success": True, "radar_url": radar_url, "infrared_url": ir_url}
    except Exception:
        return {"success": False, "radar_url": None, "infrared_url": None}


@st.cache_data(ttl=900)
def _fetch_marine_data(lat, lon):
    """Fetch current wave/swell data from Open-Meteo Marine API (cached 15 min)."""
    try:
        resp = requests.get(
            "https://marine-api.open-meteo.com/v1/marine",
            params={
                "latitude": lat, "longitude": lon,
                "current": "wave_height,wave_direction,wave_period,swell_wave_height",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def _wind_arrow_icon(speed, direction, color):
    """Create a DivIcon with a CSS-rotated wind arrow + speed label."""
    # Meteorological convention: direction is FROM; arrow points TO = direction + 180
    arrow_deg = (direction + 180) % 360
    return folium.DivIcon(
        icon_size=(40, 50),
        icon_anchor=(20, 25),
        html=(
            f'<div style="text-align:center;color:{color};font-family:monospace;'
            f'font-size:10px;line-height:1;">'
            f'<div style="font-size:22px;transform:rotate({arrow_deg}deg);">'
            f'\u2191</div>'
            f'{speed:.0f} m/s</div>'
        ),
    )


def _get_modis_date():
    """Return yesterday's date string for MODIS True Color tiles."""
    return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


def _get_ndvi_date():
    """Return latest 8-day NDVI composite date (round down to nearest 8-day period)."""
    today = date.today()
    doy = today.timetuple().tm_yday
    ndvi_doy = max(1, (doy // 8) * 8 - 8)
    ndvi_date = date(today.year, 1, 1) + timedelta(days=ndvi_doy - 1)
    return ndvi_date.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# LAYER CATEGORIES & PRESETS
# ---------------------------------------------------------------------------

_INTEL_LAYER_CATEGORIES = {
    "Real-Time Weather": [
        "Weather Radar",
        "Satellite IR",
    ],
    "Satellite Imagery": [
        "MODIS True Color",
        "NDVI Vegetation",
        "Thermal / Fires",
        "Sentinel-2 Cloudless",
    ],
    "Base Overlays": [
        "Ocean Basemap",
        "Geological Map",
    ],
    "Hazards & Seismic": [
        "Earthquakes",
        "Air Quality Zone",
    ],
    "Water & Environment": [
        "Water Features",
        "Protected Areas",
        "Biodiversity iNat",
        "Biodiversity GBIF",
    ],
    "Terrain & Meteo": [
        "Elevation Heatmap",
        "Infrastructure",
        "Wind Indicator",
        "Marine Conditions",
    ],
}

_ALL_LAYER_NAMES = [name for cat in _INTEL_LAYER_CATEGORIES.values() for name in cat]

_LAYER_PRESETS = {
    "Essential": [
        "Weather Radar", "Earthquakes", "Water Features",
        "Protected Areas", "Elevation Heatmap",
    ],
    "Environmental": [
        "NDVI Vegetation", "Sentinel-2 Cloudless", "Protected Areas",
        "Biodiversity iNat", "Biodiversity GBIF", "Air Quality Zone",
    ],
    "Hazards": [
        "Weather Radar", "Satellite IR", "Thermal / Fires",
        "Earthquakes", "Air Quality Zone", "Marine Conditions",
    ],
    "Full Intel": list(_ALL_LAYER_NAMES),
}

# Sets for quick lookup
_TILE_LAYERS = {
    "Weather Radar", "Satellite IR", "MODIS True Color",
    "NDVI Vegetation", "Thermal / Fires", "Sentinel-2 Cloudless",
    "Ocean Basemap", "Geological Map",
}
_DATA_LAYERS = set(_ALL_LAYER_NAMES) - _TILE_LAYERS


def _build_ops_map(lat, lon, raw, details, scores, selected_layers):
    """Build the interactive folium operations map from raw hub data (LEGACY)."""
    import datetime as _dt

    # --- Base map (dark theme) ---
    m = MapFactory.create_base_map(center=(lat, lon), zoom=12, tile_layer="cartodb_dark")

    # --- Add alternative tile layers for the layer control ---
    alt_tiles = [
        ("satellite", "Satellite"),
        ("osm", "OpenStreetMap"),
        ("terrain", "Terrain"),
        ("topo", "Topographic"),
        ("cartodb_positron", "Light"),
    ]
    for tile_key, display_name in alt_tiles:
        tc = MapFactory.TILE_LAYERS.get(tile_key)
        if tc:
            folium.TileLayer(
                tiles=tc["tiles"], attr=tc["attr"],
                name=display_name, overlay=False, control=True,
            ).add_to(m)

    # --- Center marker ---
    folium.Marker(
        location=(lat, lon),
        popup=folium.Popup(
            f"<b>Target Location</b><br>{lat:.5f}, {lon:.5f}", max_width=200
        ),
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        tooltip="Target",
    ).add_to(m)

    # --- Analysis radius circle (5 km) ---
    folium.Circle(
        location=(lat, lon), radius=5000,
        color=OPS_CYAN, weight=1, fill=False, dash_array="10",
        tooltip="5 km analysis radius",
    ).add_to(m)

    # ====================================================================
    # DATA LAYERS (each in a FeatureGroup)
    # ====================================================================

    # (a) Earthquakes
    if "Earthquakes" in selected_layers:
        quakes = raw.get("quakes") or {}
        features = quakes.get("features", [])
        if features:
            fg = folium.FeatureGroup(name="Earthquakes", show=True)
            for feat in features[:80]:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [])
                if len(coords) < 2:
                    continue
                eq_lon, eq_lat = coords[0], coords[1]
                mag = props.get("mag", 0) or 0
                place = props.get("place", "Unknown")
                t = props.get("time", 0)
                # Color by magnitude
                if mag >= 5:
                    eq_color = OPS_RED
                elif mag >= 3:
                    eq_color = OPS_AMBER
                else:
                    eq_color = "#ffdd44"
                radius = max(4, min(mag * 3, 18))
                time_str = ""
                if t:
                    try:
                        time_str = _dt.datetime.utcfromtimestamp(t / 1000).strftime("%Y-%m-%d")
                    except Exception:
                        time_str = str(t)
                folium.CircleMarker(
                    location=(eq_lat, eq_lon), radius=radius,
                    color=eq_color, fill=True, fill_color=eq_color,
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(
                        f"<b>M{mag:.1f}</b><br>{html_module.escape(place)}<br>{time_str}", max_width=250
                    ),
                    tooltip=f"M{mag:.1f}",
                ).add_to(fg)
            fg.add_to(m)

    # (b) Water Features
    if "Water Features" in selected_layers:
        water = raw.get("water") or {}
        elements = water.get("elements", [])
        if elements:
            fg = folium.FeatureGroup(name="Water Features", show=True)
            count = 0
            for el in elements:
                if count >= 100:
                    break
                coords = _get_element_coords(el)
                if not coords:
                    continue
                tags = el.get("tags", {})
                natural = tags.get("natural", "")
                waterway = tags.get("waterway", "")
                name = tags.get("name", "")
                if natural in ("spring",):
                    w_color, w_type = OPS_CYAN, "Spring"
                elif tags.get("man_made") == "water_well" or natural == "well":
                    w_color, w_type = OPS_CYAN, "Well"
                elif waterway in ("river", "stream"):
                    w_color, w_type = OPS_BLUE, "River/Stream"
                elif natural in ("water", "lake"):
                    w_color, w_type = OPS_BLUE, "Lake"
                else:
                    w_color, w_type = OPS_BLUE, "Water"
                label = f"{w_type}: {name}" if name else w_type
                safe_label = html_module.escape(label)
                folium.CircleMarker(
                    location=coords, radius=6,
                    color=w_color, fill=True, fill_color=w_color,
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(safe_label, max_width=200),
                    tooltip=safe_label,
                ).add_to(fg)
                count += 1
            fg.add_to(m)

    # (c) Infrastructure
    if "Infrastructure" in selected_layers:
        infra = raw.get("infra") or {}
        elements = infra.get("elements", [])
        if elements:
            fg = folium.FeatureGroup(name="Infrastructure", show=True)
            count = 0
            for el in elements:
                if count >= 50:
                    break
                coords = _get_element_coords(el)
                if not coords:
                    continue
                tags = el.get("tags", {})
                landuse = tags.get("landuse", "")
                highway = tags.get("highway", "")
                leisure = tags.get("leisure", "")
                name = tags.get("name", "")
                if landuse == "industrial":
                    i_color, i_type = OPS_PURPLE, "Industrial"
                elif leisure == "park" or landuse == "recreation_ground":
                    i_color, i_type = OPS_GREEN, "Park"
                elif highway in ("primary", "secondary", "trunk", "motorway"):
                    i_color, i_type = OPS_AMBER, "Major Road"
                else:
                    continue  # Skip minor features for performance
                label = f"{i_type}: {name}" if name else i_type
                safe_label = html_module.escape(label)
                folium.CircleMarker(
                    location=coords, radius=5,
                    color=i_color, fill=True, fill_color=i_color,
                    fill_opacity=0.6, weight=1,
                    popup=folium.Popup(safe_label, max_width=200),
                    tooltip=safe_label,
                ).add_to(fg)
                count += 1
            fg.add_to(m)

    # (d) Protected Areas
    if "Protected Areas" in selected_layers:
        prot = raw.get("protected") or {}
        elements = prot.get("elements", [])
        if elements:
            fg = folium.FeatureGroup(name="Protected Areas", show=True)
            for el in elements:
                coords = _get_element_coords(el)
                if not coords:
                    continue
                tags = el.get("tags", {})
                name = tags.get("name", "Protected Area")
                protect_class = tags.get("protect_class", "N/A")
                folium.CircleMarker(
                    location=coords, radius=12,
                    color=OPS_GREEN, fill=True, fill_color=OPS_GREEN,
                    fill_opacity=0.25, weight=2,
                    popup=folium.Popup(
                        f"<b>{html_module.escape(name)}</b><br>Class: {html_module.escape(protect_class)}", max_width=250
                    ),
                    tooltip=html_module.escape(name),
                ).add_to(fg)
            fg.add_to(m)

    # (e) Biodiversity (MarkerCluster)
    if "Biodiversity" in selected_layers:
        inat = raw.get("inat") or {}
        results = inat.get("results", [])
        if results:
            fg = folium.FeatureGroup(name="Biodiversity", show=True)
            cluster = folium_plugins.MarkerCluster(name="Species Observations")
            kingdom_colors = {
                "Aves": OPS_BLUE, "Plantae": OPS_GREEN,
                "Animalia": OPS_AMBER, "Fungi": OPS_PURPLE,
            }
            for obs in results[:100]:
                geojson = obs.get("geojson", {})
                obs_coords = geojson.get("coordinates", [])
                if len(obs_coords) < 2:
                    continue
                obs_lon, obs_lat = obs_coords[0], obs_coords[1]
                taxon = obs.get("taxon") or {}
                species = taxon.get("preferred_common_name") or taxon.get("name", "Unknown")
                kingdom = taxon.get("iconic_taxon_name", "")
                obs_date = obs.get("observed_on", "")
                bio_color = kingdom_colors.get(kingdom, OPS_CYAN)
                folium.CircleMarker(
                    location=(obs_lat, obs_lon), radius=5,
                    color=bio_color, fill=True, fill_color=bio_color,
                    fill_opacity=0.8, weight=1,
                    popup=folium.Popup(
                        f"<b>{html_module.escape(species)}</b><br>{html_module.escape(kingdom)}<br>{html_module.escape(obs_date)}", max_width=250
                    ),
                    tooltip=html_module.escape(species),
                ).add_to(cluster)
            cluster.add_to(fg)
            fg.add_to(m)

    # (f) Elevation Heatmap
    if "Elevation Heatmap" in selected_layers:
        elev = raw.get("elevation") or {}
        grid_lats = elev.get("grid_lats", [])
        grid_lons = elev.get("grid_lons", [])
        grid_elevs = elev.get("grid_elevations", [])
        if grid_lats and grid_lons and grid_elevs:
            heat_data = []
            max_e = max(grid_elevs) if grid_elevs else 1
            min_e = min(grid_elevs) if grid_elevs else 0
            rng = max_e - min_e if max_e != min_e else 1
            for i in range(min(len(grid_lats), len(grid_lons), len(grid_elevs))):
                weight = (grid_elevs[i] - min_e) / rng
                heat_data.append([grid_lats[i], grid_lons[i], weight])
            if heat_data:
                fg = folium.FeatureGroup(name="Elevation Heatmap", show=True)
                folium_plugins.HeatMap(
                    data=heat_data, radius=25, blur=20, max_zoom=14,
                    gradient={0.0: "#0044ff", 0.4: OPS_CYAN, 0.7: OPS_GREEN, 1.0: "#ffff00"},
                    name="Elevation Heat",
                ).add_to(fg)
                fg.add_to(m)

    # (g) Air Quality Indicator
    if "Air Quality Zone" in selected_layers:
        aq = raw.get("air_quality") or {}
        current_aq = aq.get("current", {}) if isinstance(aq, dict) else {}
        aqi = current_aq.get("european_aqi", 0) or 0
        pm25 = current_aq.get("pm2_5", 0) or 0
        pm10 = current_aq.get("pm10", 0) or 0
        if aqi or pm25 or pm10:
            if aqi < 50:
                aq_color = OPS_GREEN
            elif aqi <= 100:
                aq_color = OPS_AMBER
            else:
                aq_color = OPS_RED
            fg = folium.FeatureGroup(name="Air Quality Zone", show=True)
            folium.Circle(
                location=(lat, lon), radius=3000,
                color=aq_color, weight=1, fill=True,
                fill_color=aq_color, fill_opacity=0.12,
                popup=folium.Popup(
                    f"<b>Air Quality</b><br>AQI: {aqi}<br>"
                    f"PM2.5: {pm25}<br>PM10: {pm10}",
                    max_width=200,
                ),
                tooltip=f"AQI: {aqi}",
            ).add_to(fg)
            fg.add_to(m)

    # --- Plugins ---
    MapFactory.add_fullscreen(m)
    MapFactory.add_minimap(m)
    MapFactory.add_measure_control(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    return m


# ---------------------------------------------------------------------------
# TOTAL INTELLIGENCE MAP (18 layers)
# ---------------------------------------------------------------------------

def _build_total_intel_map(lat, lon, raw, details, scores, selected_layers,
                           marine_data=None, rainviewer=None):
    """Build the Total Intelligence Map with up to 18 layers."""
    import datetime as _dt

    marine_data = marine_data or {}
    rainviewer = rainviewer or {}

    # --- Base map (dark theme) ---
    m = MapFactory.create_base_map(center=(lat, lon), zoom=12, tile_layer="cartodb_dark")

    # --- Alternative base tile layers ---
    alt_tiles = [
        ("satellite", "Satellite"),
        ("osm", "OpenStreetMap"),
        ("terrain", "Terrain"),
        ("topo", "Topographic"),
        ("cartodb_positron", "Light"),
    ]
    for tile_key, display_name in alt_tiles:
        tc = MapFactory.TILE_LAYERS.get(tile_key)
        if tc:
            folium.TileLayer(
                tiles=tc["tiles"], attr=tc["attr"],
                name=display_name, overlay=False, control=True,
            ).add_to(m)

    # --- Center marker + analysis radius ---
    folium.Marker(
        location=(lat, lon),
        popup=folium.Popup(
            f"<b>Target Location</b><br>{lat:.5f}, {lon:.5f}", max_width=200
        ),
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        tooltip="Target",
    ).add_to(m)
    folium.Circle(
        location=(lat, lon), radius=5000,
        color=OPS_CYAN, weight=1, fill=False, dash_array="10",
        tooltip="5 km analysis radius",
    ).add_to(m)

    # ================================================================
    # TILE OVERLAYS (T1-T8)
    # ================================================================

    # T1 — Weather Radar
    if "Weather Radar" in selected_layers:
        radar_url = rainviewer.get("radar_url")
        if radar_url:
            fg = folium.FeatureGroup(name="Weather Radar", show=True)
            folium.TileLayer(
                tiles=radar_url, attr="RainViewer",
                name="Radar tiles", overlay=True, opacity=0.6,
                control=False,
            ).add_to(fg)
            fg.add_to(m)

    # T2 — Satellite IR
    if "Satellite IR" in selected_layers:
        ir_url = rainviewer.get("infrared_url")
        if ir_url:
            fg = folium.FeatureGroup(name="Satellite IR", show=True)
            folium.TileLayer(
                tiles=ir_url, attr="RainViewer",
                name="IR tiles", overlay=True, opacity=0.5,
                control=False,
            ).add_to(fg)
            fg.add_to(m)

    # T3 — MODIS True Color
    if "MODIS True Color" in selected_layers:
        modis_date = _get_modis_date()
        modis_url = (
            "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
            "MODIS_Terra_CorrectedReflectance_TrueColor/default/"
            f"{modis_date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
        )
        fg = folium.FeatureGroup(name="MODIS True Color", show=True)
        folium.TileLayer(
            tiles=modis_url, attr="NASA GIBS",
            name="MODIS tiles", overlay=True, opacity=0.7,
            max_zoom=9, control=False,
        ).add_to(fg)
        fg.add_to(m)

    # T4 — NDVI Vegetation
    if "NDVI Vegetation" in selected_layers:
        ndvi_date = _get_ndvi_date()
        ndvi_url = (
            "https://map1.vis.earthdata.nasa.gov/wmts-webmerc/"
            "MODIS_Terra_NDVI_8Day/default/"
            f"{ndvi_date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.png"
        )
        fg = folium.FeatureGroup(name="NDVI Vegetation", show=True)
        folium.TileLayer(
            tiles=ndvi_url, attr="NASA GIBS",
            name="NDVI tiles", overlay=True, opacity=0.6,
            max_zoom=8, control=False,
        ).add_to(fg)
        fg.add_to(m)

    # T5 — Thermal / Fires
    if "Thermal / Fires" in selected_layers:
        fire_date = _get_modis_date()
        fire_url = (
            "https://map1.vis.earthdata.nasa.gov/wmts-webmerc/"
            "MODIS_Terra_Thermal_Anomalies_Day/default/"
            f"{fire_date}/GoogleMapsCompatible_Level7/{{z}}/{{y}}/{{x}}.png"
        )
        fg = folium.FeatureGroup(name="Thermal / Fires", show=True)
        folium.TileLayer(
            tiles=fire_url, attr="NASA GIBS",
            name="Fire tiles", overlay=True, opacity=0.7,
            max_zoom=8, control=False,
        ).add_to(fg)
        fg.add_to(m)

    # T6 — Sentinel-2 Cloudless
    if "Sentinel-2 Cloudless" in selected_layers:
        s2_url = (
            "https://tiles.maps.eox.at/wmts/1.0.0/"
            "s2cloudless-2023_3857/default/"
            "GoogleMapsCompatible/{z}/{y}/{x}.jpg"
        )
        fg = folium.FeatureGroup(name="Sentinel-2 Cloudless", show=True)
        folium.TileLayer(
            tiles=s2_url, attr="EOX Sentinel-2",
            name="S2 tiles", overlay=True, opacity=0.8,
            control=False,
        ).add_to(fg)
        fg.add_to(m)

    # T7 — Ocean Basemap
    if "Ocean Basemap" in selected_layers:
        ocean_url = (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
        )
        fg = folium.FeatureGroup(name="Ocean Basemap", show=True)
        folium.TileLayer(
            tiles=ocean_url, attr="Esri Ocean",
            name="Ocean tiles", overlay=True, opacity=0.6,
            max_zoom=13, control=False,
        ).add_to(fg)
        fg.add_to(m)

    # T8 — Geological Map
    if "Geological Map" in selected_layers:
        fg = folium.FeatureGroup(name="Geological Map", show=True)
        folium.TileLayer(
            tiles="https://tiles.macrostrat.org/carto/{z}/{x}/{y}.png",
            attr="Macrostrat",
            name="Geology tiles", overlay=True, opacity=0.6,
            control=False,
        ).add_to(fg)
        fg.add_to(m)

    # ================================================================
    # DATA LAYERS (D1-D10)
    # ================================================================

    # D1 — Earthquakes
    if "Earthquakes" in selected_layers:
        quakes = raw.get("quakes") or {}
        features = quakes.get("features", [])
        if features:
            fg = folium.FeatureGroup(name="Earthquakes", show=True)
            for feat in features[:80]:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [])
                if len(coords) < 2:
                    continue
                eq_lon, eq_lat = coords[0], coords[1]
                mag = props.get("mag", 0) or 0
                place = props.get("place", "Unknown")
                t = props.get("time", 0)
                if mag >= 5:
                    eq_color = OPS_RED
                elif mag >= 3:
                    eq_color = OPS_AMBER
                else:
                    eq_color = "#ffdd44"
                radius = max(4, min(mag * 3, 18))
                time_str = ""
                if t:
                    try:
                        time_str = _dt.datetime.utcfromtimestamp(t / 1000).strftime("%Y-%m-%d")
                    except Exception:
                        time_str = str(t)
                folium.CircleMarker(
                    location=(eq_lat, eq_lon), radius=radius,
                    color=eq_color, fill=True, fill_color=eq_color,
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(
                        f"<b>M{mag:.1f}</b><br>{html_module.escape(place)}<br>{time_str}", max_width=250
                    ),
                    tooltip=f"M{mag:.1f}",
                ).add_to(fg)
            fg.add_to(m)

    # D2 — Water Features
    if "Water Features" in selected_layers:
        water = raw.get("water") or {}
        elements = water.get("elements", [])
        if elements:
            fg = folium.FeatureGroup(name="Water Features", show=True)
            count = 0
            for el in elements:
                if count >= 100:
                    break
                coords = _get_element_coords(el)
                if not coords:
                    continue
                tags = el.get("tags", {})
                natural = tags.get("natural", "")
                waterway = tags.get("waterway", "")
                name = tags.get("name", "")
                if natural in ("spring",):
                    w_color, w_type = OPS_CYAN, "Spring"
                elif tags.get("man_made") == "water_well" or natural == "well":
                    w_color, w_type = OPS_CYAN, "Well"
                elif waterway in ("river", "stream"):
                    w_color, w_type = OPS_BLUE, "River/Stream"
                elif natural in ("water", "lake"):
                    w_color, w_type = OPS_BLUE, "Lake"
                else:
                    w_color, w_type = OPS_BLUE, "Water"
                label = f"{w_type}: {name}" if name else w_type
                safe_label = html_module.escape(label)
                folium.CircleMarker(
                    location=coords, radius=6,
                    color=w_color, fill=True, fill_color=w_color,
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(safe_label, max_width=200),
                    tooltip=safe_label,
                ).add_to(fg)
                count += 1
            fg.add_to(m)

    # D3 — Infrastructure
    if "Infrastructure" in selected_layers:
        infra = raw.get("infra") or {}
        elements = infra.get("elements", [])
        if elements:
            fg = folium.FeatureGroup(name="Infrastructure", show=True)
            count = 0
            for el in elements:
                if count >= 50:
                    break
                coords = _get_element_coords(el)
                if not coords:
                    continue
                tags = el.get("tags", {})
                landuse = tags.get("landuse", "")
                highway = tags.get("highway", "")
                leisure = tags.get("leisure", "")
                name = tags.get("name", "")
                if landuse == "industrial":
                    i_color, i_type = OPS_PURPLE, "Industrial"
                elif leisure == "park" or landuse == "recreation_ground":
                    i_color, i_type = OPS_GREEN, "Park"
                elif highway in ("primary", "secondary", "trunk", "motorway"):
                    i_color, i_type = OPS_AMBER, "Major Road"
                else:
                    continue
                label = f"{i_type}: {name}" if name else i_type
                safe_label = html_module.escape(label)
                folium.CircleMarker(
                    location=coords, radius=5,
                    color=i_color, fill=True, fill_color=i_color,
                    fill_opacity=0.6, weight=1,
                    popup=folium.Popup(safe_label, max_width=200),
                    tooltip=safe_label,
                ).add_to(fg)
                count += 1
            fg.add_to(m)

    # D4 — Protected Areas
    if "Protected Areas" in selected_layers:
        prot = raw.get("protected") or {}
        elements = prot.get("elements", [])
        if elements:
            fg = folium.FeatureGroup(name="Protected Areas", show=True)
            for el in elements:
                coords = _get_element_coords(el)
                if not coords:
                    continue
                tags = el.get("tags", {})
                name = tags.get("name", "Protected Area")
                protect_class = tags.get("protect_class", "N/A")
                folium.CircleMarker(
                    location=coords, radius=12,
                    color=OPS_GREEN, fill=True, fill_color=OPS_GREEN,
                    fill_opacity=0.25, weight=2,
                    popup=folium.Popup(
                        f"<b>{html_module.escape(name)}</b><br>Class: {html_module.escape(protect_class)}", max_width=250
                    ),
                    tooltip=html_module.escape(name),
                ).add_to(fg)
            fg.add_to(m)

    # D5 — Biodiversity iNat (MarkerCluster)
    if "Biodiversity iNat" in selected_layers:
        inat = raw.get("inat") or {}
        results = inat.get("results", [])
        if results:
            fg = folium.FeatureGroup(name="Biodiversity iNat", show=True)
            cluster = folium_plugins.MarkerCluster(name="iNat Observations")
            kingdom_colors = {
                "Aves": OPS_BLUE, "Plantae": OPS_GREEN,
                "Animalia": OPS_AMBER, "Fungi": OPS_PURPLE,
            }
            for obs in results[:100]:
                geojson = obs.get("geojson", {})
                obs_coords = geojson.get("coordinates", [])
                if len(obs_coords) < 2:
                    continue
                obs_lon, obs_lat = obs_coords[0], obs_coords[1]
                taxon = obs.get("taxon") or {}
                species = taxon.get("preferred_common_name") or taxon.get("name", "Unknown")
                kingdom = taxon.get("iconic_taxon_name", "")
                obs_date = obs.get("observed_on", "")
                bio_color = kingdom_colors.get(kingdom, OPS_CYAN)
                folium.CircleMarker(
                    location=(obs_lat, obs_lon), radius=5,
                    color=bio_color, fill=True, fill_color=bio_color,
                    fill_opacity=0.8, weight=1,
                    popup=folium.Popup(
                        f"<b>{html_module.escape(species)}</b><br>{html_module.escape(kingdom)}<br>{html_module.escape(obs_date)}", max_width=250
                    ),
                    tooltip=html_module.escape(species),
                ).add_to(cluster)
            cluster.add_to(fg)
            fg.add_to(m)

    # D6 — Biodiversity GBIF (MarkerCluster)
    if "Biodiversity GBIF" in selected_layers:
        gbif = raw.get("gbif") or {}
        results = gbif.get("results", [])
        if results:
            fg = folium.FeatureGroup(name="Biodiversity GBIF", show=True)
            cluster = folium_plugins.MarkerCluster(name="GBIF Records")
            kingdom_colors = {
                "Aves": OPS_BLUE, "Plantae": OPS_GREEN,
                "Animalia": OPS_AMBER, "Fungi": OPS_PURPLE,
            }
            for rec in results[:100]:
                rlat = rec.get("decimalLatitude")
                rlon = rec.get("decimalLongitude")
                if rlat is None or rlon is None:
                    continue
                sp_name = rec.get("species") or rec.get("scientificName", "Unknown")
                kingdom = rec.get("kingdom", "")
                bio_color = kingdom_colors.get(kingdom, "#66bbff")
                folium.CircleMarker(
                    location=(float(rlat), float(rlon)), radius=4,
                    color=bio_color, fill=True, fill_color=bio_color,
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(
                        f"<b>{html_module.escape(sp_name)}</b><br>{html_module.escape(kingdom)}", max_width=250
                    ),
                    tooltip=html_module.escape(sp_name),
                ).add_to(cluster)
            cluster.add_to(fg)
            fg.add_to(m)

    # D7 — Elevation Heatmap
    if "Elevation Heatmap" in selected_layers:
        elev = raw.get("elevation") or {}
        grid_lats = elev.get("grid_lats", [])
        grid_lons = elev.get("grid_lons", [])
        grid_elevs = elev.get("grid_elevations", [])
        if grid_lats and grid_lons and grid_elevs:
            heat_data = []
            max_e = max(grid_elevs) if grid_elevs else 1
            min_e = min(grid_elevs) if grid_elevs else 0
            rng = max_e - min_e if max_e != min_e else 1
            for i in range(min(len(grid_lats), len(grid_lons), len(grid_elevs))):
                weight = (grid_elevs[i] - min_e) / rng
                heat_data.append([grid_lats[i], grid_lons[i], weight])
            if heat_data:
                fg = folium.FeatureGroup(name="Elevation Heatmap", show=True)
                folium_plugins.HeatMap(
                    data=heat_data, radius=25, blur=20, max_zoom=14,
                    gradient={0.0: "#0044ff", 0.4: OPS_CYAN, 0.7: OPS_GREEN, 1.0: "#ffff00"},
                    name="Elevation Heat",
                ).add_to(fg)
                fg.add_to(m)

    # D8 — Air Quality Zone
    if "Air Quality Zone" in selected_layers:
        aq = raw.get("air_quality") or {}
        current_aq = aq.get("current", {}) if isinstance(aq, dict) else {}
        aqi = current_aq.get("european_aqi", 0) or 0
        pm25 = current_aq.get("pm2_5", 0) or 0
        pm10 = current_aq.get("pm10", 0) or 0
        if aqi or pm25 or pm10:
            if aqi < 50:
                aq_color = OPS_GREEN
            elif aqi <= 100:
                aq_color = OPS_AMBER
            else:
                aq_color = OPS_RED
            fg = folium.FeatureGroup(name="Air Quality Zone", show=True)
            folium.Circle(
                location=(lat, lon), radius=3000,
                color=aq_color, weight=1, fill=True,
                fill_color=aq_color, fill_opacity=0.12,
                popup=folium.Popup(
                    f"<b>Air Quality</b><br>AQI: {aqi}<br>"
                    f"PM2.5: {pm25}<br>PM10: {pm10}",
                    max_width=200,
                ),
                tooltip=f"AQI: {aqi}",
            ).add_to(fg)
            fg.add_to(m)

    # D9 — Wind Indicator
    if "Wind Indicator" in selected_layers:
        weather = raw.get("weather") or {}
        current_w = weather.get("current", {}) if isinstance(weather, dict) else {}
        wind_speed = current_w.get("wind_speed_10m") or current_w.get("windspeed_10m", 0) or 0
        wind_dir = current_w.get("wind_direction_10m") or current_w.get("winddirection_10m", 0) or 0
        if wind_speed:
            if wind_speed > 15:
                w_color = OPS_RED
            elif wind_speed > 8:
                w_color = OPS_AMBER
            else:
                w_color = OPS_GREEN
            fg = folium.FeatureGroup(name="Wind Indicator", show=True)
            folium.Marker(
                location=(lat + 0.015, lon + 0.015),
                icon=_wind_arrow_icon(wind_speed, wind_dir, w_color),
                tooltip=f"Wind: {wind_speed:.1f} m/s from {wind_dir:.0f}\u00b0",
            ).add_to(fg)
            fg.add_to(m)

    # D10 — Marine Conditions
    if "Marine Conditions" in selected_layers:
        m_current = marine_data.get("current", {}) if isinstance(marine_data, dict) else {}
        wave_h = m_current.get("wave_height", 0) or 0
        wave_dir = m_current.get("wave_direction", 0) or 0
        wave_per = m_current.get("wave_period", 0) or 0
        swell_h = m_current.get("swell_wave_height", 0) or 0
        if wave_h:
            if wave_h > 3:
                mc_color = OPS_RED
            elif wave_h > 1.5:
                mc_color = OPS_AMBER
            else:
                mc_color = OPS_CYAN
            fg = folium.FeatureGroup(name="Marine Conditions", show=True)
            folium.CircleMarker(
                location=(lat, lon), radius=20,
                color=mc_color, fill=True, fill_color=mc_color,
                fill_opacity=0.15, weight=2,
                popup=folium.Popup(
                    f"<b>Marine</b><br>Waves: {wave_h:.1f}m"
                    f"<br>Dir: {wave_dir:.0f}\u00b0"
                    f"<br>Period: {wave_per:.1f}s"
                    f"<br>Swell: {swell_h:.1f}m",
                    max_width=200,
                ),
                tooltip=f"Waves: {wave_h:.1f}m",
            ).add_to(fg)
            fg.add_to(m)

    # --- Plugins ---
    MapFactory.add_fullscreen(m)
    MapFactory.add_minimap(m)
    MapFactory.add_measure_control(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    return m


# ---------------------------------------------------------------------------
# MODULE RELEVANCE SCORING
# ---------------------------------------------------------------------------

_DOMAIN_MODULE_MAP = {
    "habitability": [
        "livability_score", "real_estate_ai", "settlement_ai", "urban_planning_ai",
    ],
    "agriculture": [
        "agriculture_ai", "soil_health_ai", "grazing_potential", "food_security",
    ],
    "ecology": [
        "biodiversity_hotspot", "wildlife_corridor", "habitat_analyzer", "ecosystem_health",
    ],
    "hazard_safety": [
        "disaster_resilience", "multi_hazard", "threat_matrix", "evacuation_route",
    ],
    "water_resources": [
        "water_security", "hydrology_ai", "water_quality_ai", "flood_model",
    ],
    "infrastructure": [
        "infrastructure_scan", "construction_ai", "transportation_ai", "logistics_ai",
    ],
    "climate_comfort": [
        "climate_forecast", "seasonal_analysis", "microclimate_ai", "climate_adaptation",
    ],
    "economic_potential": [
        "real_estate_ai", "tourism_potential", "energy_potential", "strategic_value",
    ],
    "air_environment": [
        "air_quality_ai", "pollution_tracker", "carbon_footprint", "contamination_ai",
    ],
    "geological_stability": [
        "seismic_profiler", "geological_risk", "mineral_prospecting", "soil_erosion_ai",
    ],
}

_CORE_MODULES = [
    "unified_intelligence", "decision_matrix", "deep_analysis", "zone_intel",
]


def _get_recommended_modules(scores, max_count=8):
    """Return a list of module IDs most relevant for the current location."""
    if not scores:
        return _CORE_MODULES[:max_count]

    module_scores = {}
    for domain_key, score_val in scores.items():
        relevance = abs(score_val - 50) / 50.0
        modules = _DOMAIN_MODULE_MAP.get(domain_key, [])
        for mid in modules:
            module_scores[mid] = max(module_scores.get(mid, 0), relevance)

    for mid in _CORE_MODULES:
        module_scores[mid] = max(module_scores.get(mid, 0), 0.5)

    sorted_mods = sorted(module_scores.items(), key=lambda x: x[1], reverse=True)
    return [mid for mid, _ in sorted_mods[:max_count]]


# ---------------------------------------------------------------------------
# CHART 1: POLAR AREA CHART (replaces radar)
# ---------------------------------------------------------------------------

def _build_polar_area(scores):
    """Build a Barpolar chart - polar area with sectors per domain."""
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    names = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]
    vals = [scores.get(k, 0) for k in domain_keys]
    colors = [_DOMAIN_OPS_COLORS.get(k, OPS_CYAN) for k in domain_keys]

    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=vals,
        theta=names,
        marker_color=colors,
        marker_line_color=OPS_BG,
        marker_line_width=1,
        opacity=0.85,
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.0f}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=OPS_BG,
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(color=OPS_TEXT_DIM, size=9),
                gridcolor=OPS_GRID, linecolor=OPS_GRID,
            ),
            angularaxis=dict(
                tickfont=dict(color=OPS_TEXT, size=10),
                gridcolor=OPS_GRID, linecolor=OPS_GRID,
            ),
        ),
        paper_bgcolor=OPS_BG,
        plot_bgcolor=OPS_BG,
        font=dict(color=OPS_TEXT),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    return fig


# ---------------------------------------------------------------------------
# CHART 2: SUNBURST CHART (domain -> sub-factors)
# ---------------------------------------------------------------------------

def _build_sunburst(scores, details):
    """Sunburst: center=Overall, ring1=domains, ring2=sub-factors."""
    overall = _compute_overall_score(scores)

    ids = ["Overall"]
    labels = ["Overall"]
    parents = [""]
    values = [overall]
    colors_list = [OPS_CYAN]

    # Sub-factor definitions per domain
    _subfactors = {
        "habitability": [
            ("Buildings", details.get("building_count", 0)),
            ("Roads", details.get("road_count", 0)),
            ("Parks", details.get("park_count", 0)),
        ],
        "agriculture": [
            ("SOC", (details.get("soc_val") or 0) * 5),
            ("Nitrogen", (details.get("nitrogen_val") or 0) * 50),
            ("Farmland", details.get("farmland_count", 0) * 10),
        ],
        "ecology": [
            ("Species", min(details.get("total_species_obs", 0), 100)),
            ("Protected", details.get("protected_count", 0) * 20),
            ("Water", min(details.get("total_water", 0) * 5, 50)),
        ],
        "hazard_safety": [
            ("Seismic", max(0, 50 - details.get("max_mag", 0) * 5)),
            ("Flood", max(0, 50 - max(0, 50 - details.get("center_elev", 0)))),
            ("Pollution", max(0, 50 - details.get("aqi", 0) * 0.5)),
        ],
        "water_resources": [
            ("Springs", details.get("spring_count", 0) * 10),
            ("Rivers", details.get("river_count", 0) * 8),
            ("Lakes", details.get("lake_count", 0) * 10),
        ],
        "infrastructure": [
            ("Buildings", min(details.get("building_count", 0), 80)),
            ("Roads", min(details.get("road_count", 0), 60)),
            ("Major Roads", details.get("major_road_count", 0) * 10),
        ],
        "climate_comfort": [
            ("Temperature", max(0, 50 - abs(details.get("avg_temp", 20) - 20) * 3)),
            ("Humidity", max(0, 50 - abs(details.get("humidity", 50) - 50))),
            ("Wind", max(0, 30 - details.get("wind_speed", 10))),
        ],
        "economic_potential": [
            ("Infrastructure", min(details.get("building_count", 0) / 2, 40)),
            ("Access", min(details.get("road_count", 0) / 2, 30)),
            ("Terrain", max(0, 30 - details.get("slope_proxy", 0) / 10)),
        ],
        "air_environment": [
            ("AQI", max(0, 50 - details.get("aqi", 0) * 0.5)),
            ("PM2.5", max(0, 30 - details.get("pm25", 0) * 0.5)),
            ("Green", min(details.get("forest_count", 0) * 5 + details.get("park_count", 0) * 5, 30)),
        ],
        "geological_stability": [
            ("Seismic", max(0, 40 - details.get("eq_count", 0) * 0.5)),
            ("Slope", max(0, 30 - details.get("slope_proxy", 0) / 10)),
            ("Geology", min(details.get("geo_units", 0) * 5, 20)),
        ],
    }

    for dk in INTELLIGENCE_DOMAINS:
        domain_name = INTELLIGENCE_DOMAINS[dk]["name"]
        domain_score = scores.get(dk, 0)
        domain_color = _DOMAIN_OPS_COLORS.get(dk, OPS_CYAN)
        did = f"d_{dk}"
        ids.append(did)
        labels.append(domain_name)
        parents.append("Overall")
        values.append(max(domain_score, 1))
        colors_list.append(domain_color)

        for sf_name, sf_val in _subfactors.get(dk, []):
            sf_id = f"sf_{dk}_{sf_name}"
            ids.append(sf_id)
            labels.append(sf_name)
            parents.append(did)
            values.append(max(sf_val, 0.5))
            colors_list.append(domain_color)

    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors_list, line=dict(color=OPS_BG, width=1)),
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>Value: %{value:.0f}<extra></extra>",
        insidetextorientation="radial",
        textfont=dict(size=10, color=OPS_TEXT),
    ))
    fig.update_layout(
        paper_bgcolor=OPS_BG,
        font=dict(color=OPS_TEXT),
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
    )
    return fig


# ---------------------------------------------------------------------------
# CHART 3: RISK GAUGE (upgraded)
# ---------------------------------------------------------------------------

def _build_risk_gauge(scores):
    """Upgraded risk gauge with 5 zones and ops-center colors."""
    hazard_score = scores.get("hazard_safety", 50)

    if hazard_score >= 80:
        bar_color = OPS_GREEN
    elif hazard_score >= 65:
        bar_color = OPS_CYAN
    elif hazard_score >= 40:
        bar_color = OPS_AMBER
    elif hazard_score >= 20:
        bar_color = OPS_RED
    else:
        bar_color = "#cc0022"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=hazard_score,
        title={"text": "COMPOSITE SAFETY INDEX", "font": {"size": 12, "color": OPS_TEXT_DIM, "family": "JetBrains Mono, monospace"}},
        number={"font": {"size": 36, "color": OPS_TEXT, "family": "JetBrains Mono, monospace"}, "suffix": "/100"},
        delta={"reference": 50, "increasing": {"color": OPS_GREEN}, "decreasing": {"color": OPS_RED}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": OPS_TEXT_DIM, "size": 9}},
            "bar": {"color": bar_color, "thickness": 0.75},
            "bgcolor": OPS_BG,
            "bordercolor": OPS_GRID,
            "steps": [
                {"range": [0, 20], "color": "rgba(255,51,68,0.15)"},
                {"range": [20, 40], "color": "rgba(255,170,0,0.1)"},
                {"range": [40, 65], "color": "rgba(0,240,255,0.08)"},
                {"range": [65, 80], "color": "rgba(0,255,136,0.08)"},
                {"range": [80, 100], "color": "rgba(0,255,136,0.15)"},
            ],
            "threshold": {
                "line": {"color": OPS_CYAN, "width": 2},
                "thickness": 0.8,
                "value": hazard_score,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor=OPS_BG,
        font={"color": OPS_TEXT},
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


# ---------------------------------------------------------------------------
# CHART 4: TREEMAP (domain areas)
# ---------------------------------------------------------------------------

def _build_treemap(scores):
    """Treemap: each domain = rectangle, area proportional to score."""
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    names = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]
    vals = [max(scores.get(k, 0), 1) for k in domain_keys]
    colors = [_DOMAIN_OPS_COLORS.get(k, OPS_CYAN) for k in domain_keys]

    fig = go.Figure(go.Treemap(
        labels=names,
        parents=[""] * len(names),
        values=vals,
        marker=dict(
            colors=colors,
            line=dict(color=OPS_BG, width=2),
        ),
        texttemplate="<b>%{label}</b><br>%{value:.0f}",
        textfont=dict(size=12, color=OPS_TEXT, family="JetBrains Mono, monospace"),
        hovertemplate="<b>%{label}</b><br>Score: %{value:.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=OPS_BG,
        font=dict(color=OPS_TEXT),
        margin=dict(l=5, r=5, t=5, b=5),
        height=340,
    )
    return fig


# ---------------------------------------------------------------------------
# CHART 5: WATERFALL (upgraded)
# ---------------------------------------------------------------------------

def _build_risk_waterfall(details, scores):
    """Waterfall chart with ops-center colors showing risk factor breakdown."""
    base = 100
    eq_count = details.get("eq_count", 0)
    eq_penalty = 0
    if eq_count > 0:
        eq_penalty = min(30, (details.get("max_mag", 0) / 9.0) * 30)
        eq_penalty += min(15, eq_count / 50.0 * 15)
    flood_pen = min(20, max(0, (50 - details.get("center_elev", 0)) / 50.0) * 10 +
                     min(details.get("total_water", 0) / 20.0 * 10, 10))
    slide_pen = min(15, details.get("slope_proxy", 0) / 300.0 * 15)
    poll_pen = min(10, details.get("aqi", 0) / 5.0)
    indust_pen = min(10, details.get("industrial_count", 0) * 3.0)
    final = max(0, min(100, base - eq_penalty - flood_pen - slide_pen - poll_pen - indust_pen))

    factors = ["Base", "Seismic", "Flood", "Landslide", "Pollution", "Industrial", "Final"]
    values_measure = ["absolute", "relative", "relative", "relative", "relative", "relative", "total"]
    values_y = [base, -eq_penalty, -flood_pen, -slide_pen, -poll_pen, -indust_pen, 0]
    text_labels = (
        [f"{base:.0f}"]
        + [f"{v:+.0f}" for v in [-eq_penalty, -flood_pen, -slide_pen, -poll_pen, -indust_pen]]
        + [f"{final:.0f}"]
    )

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=values_measure,
        x=factors,
        y=values_y,
        connector={"line": {"color": OPS_GRID}},
        increasing={"marker": {"color": OPS_GREEN}},
        decreasing={"marker": {"color": OPS_RED}},
        totals={"marker": {"color": OPS_CYAN}},
        textposition="outside",
        text=text_labels,
        textfont={"color": OPS_TEXT, "size": 11, "family": "JetBrains Mono, monospace"},
    ))
    fig.update_layout(
        paper_bgcolor=OPS_BG,
        plot_bgcolor=OPS_BG,
        font={"color": OPS_TEXT},
        xaxis={"tickfont": {"color": OPS_TEXT_DIM, "size": 10, "family": "JetBrains Mono, monospace"}},
        yaxis={"gridcolor": OPS_GRID, "range": [0, 110], "tickfont": {"color": OPS_TEXT_DIM}},
        height=300,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# CHART 6: NETWORK GRAPH (domain correlations)
# ---------------------------------------------------------------------------

def _build_network_graph(scores, insights):
    """Network graph: nodes=domains positioned in circle, edges=cross-correlations."""
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    n = len(domain_keys)

    # Position nodes in a circle
    node_x = []
    node_y = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        node_x.append(math.cos(angle))
        node_y.append(math.sin(angle))

    # Build edges from insights
    edge_traces = []
    domain_idx = {k: i for i, k in enumerate(domain_keys)}

    for ins in insights:
        domains = ins.get("domains", [])
        if len(domains) < 2:
            continue
        conf = ins.get("confidence", 0.5)
        itype = ins.get("type", "synergy")
        edge_color = OPS_CYAN if itype in ("opportunity", "synergy") else OPS_RED if itype == "threat" else OPS_AMBER

        # Connect all pairs in the insight
        for i_d in range(len(domains)):
            for j_d in range(i_d + 1, len(domains)):
                d1, d2 = domains[i_d], domains[j_d]
                if d1 not in domain_idx or d2 not in domain_idx:
                    continue
                i1, i2 = domain_idx[d1], domain_idx[d2]
                edge_traces.append(go.Scatter(
                    x=[node_x[i1], node_x[i2], None],
                    y=[node_y[i1], node_y[i2], None],
                    mode="lines",
                    line=dict(color=edge_color, width=max(1, conf * 4)),
                    hoverinfo="skip",
                    showlegend=False,
                ))

    # Node trace
    node_colors = [_DOMAIN_OPS_COLORS.get(k, OPS_CYAN) for k in domain_keys]
    node_sizes = [max(20, scores.get(k, 0) / 3 + 10) for k in domain_keys]
    node_labels = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]
    node_scores = [f"{scores.get(k, 0):.0f}" for k in domain_keys]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(color=OPS_BG, width=2),
            opacity=0.9,
        ),
        text=node_scores,
        textposition="middle center",
        textfont=dict(color=OPS_TEXT, size=9, family="JetBrains Mono, monospace"),
        hovertext=[f"{name}: {scores.get(k, 0):.0f}" for name, k in zip(node_labels, domain_keys)],
        hoverinfo="text",
        showlegend=False,
    )

    # Label trace (outside)
    label_x = [x * 1.3 for x in node_x]
    label_y = [y * 1.3 for y in node_y]
    label_trace = go.Scatter(
        x=label_x,
        y=label_y,
        mode="text",
        text=[n.replace(" ", "<br>") for n in node_labels],
        textfont=dict(color=OPS_TEXT_DIM, size=8),
        hoverinfo="skip",
        showlegend=False,
    )

    fig = go.Figure(data=edge_traces + [node_trace, label_trace])
    fig.update_layout(
        paper_bgcolor=OPS_BG,
        plot_bgcolor=OPS_BG,
        xaxis=dict(visible=False, range=[-1.6, 1.6]),
        yaxis=dict(visible=False, range=[-1.6, 1.6], scaleanchor="x"),
        font=dict(color=OPS_TEXT),
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------------------------

def render_command_center():
    """Render the Command Center home page with ops-center style."""
    init_location_context()

    # ================================================================
    # SECTION 1: HERO + LOCATION INPUT
    # ================================================================
    st.markdown(
        '<div class="command-hero">'
        '<h1>TerraScout AI</h1>'
        '<p>UNIFIED GEOSPATIAL INTELLIGENCE PLATFORM &mdash; '
        'REAL-TIME DATA FROM 15+ API SOURCES</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container():
        changed = render_location_selector(key_prefix="cc")

    if changed:
        st.rerun()

    if not has_location():
        st.markdown(
            '<div class="ops-terminal">'
            '<span class="ops-term-label">SYSTEM STATUS</span>'
            'AWAITING TARGET COORDINATES...<br>'
            'Enter coordinates or search for a location above to initialize '
            'the intelligence dashboard.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        _render_category_links()
        return

    # ================================================================
    # FETCH DATA
    # ================================================================
    loc = get_location()
    lat, lon = loc["lat"], loc["lon"]

    with st.spinner("Loading intelligence data from 12+ sources..."):
        hub = get_hub_data(lat, lon)

    scores = hub.get("scores", {})
    details = hub.get("details", {})
    insights = hub.get("insights", [])
    swot = hub.get("swot", {})
    recommendations = hub.get("recommendations", [])
    overall = hub.get("overall_score", 50)
    overall_label = hub.get("overall_label", "Moderate")
    overall_color = hub.get("overall_color", "#fbbf24")
    _conf_raw = hub.get("confidence", 0)
    confidence = float(_conf_raw.get("overall", 0)) if isinstance(_conf_raw, dict) else float(_conf_raw or 0)

    # ================================================================
    # SECTION 2: LOCATION HEADER (ops-center style)
    # ================================================================
    name = get_short_name()
    safe_name = html_module.escape(name) if name else f"{lat:.5f}, {lon:.5f}"

    # Score badge CSS class
    if overall >= 65:
        badge_class = "ops-badge-green"
    elif overall >= 40:
        badge_class = "ops-badge-amber"
    else:
        badge_class = "ops-badge-red"

    st.markdown(
        f'<div style="text-align:center;margin:1rem 0;">'
        f'<h2 style="color:{OPS_TEXT};margin:0 0 4px;font-family:JetBrains Mono,monospace;">'
        f'{safe_name}</h2>'
        f'<p style="color:{OPS_CYAN};margin:0 0 12px;font-family:JetBrains Mono,monospace;'
        f'font-size:0.85rem;">{lat:.5f}, {lon:.5f}</p>'
        f'<div class="ops-badge ops-badge-lg {badge_class}" '
        f'style="margin:0 auto;">{overall:.0f}</div>'
        f'<p style="color:{overall_color};font-weight:600;margin:6px 0 0;'
        f'font-family:JetBrains Mono,monospace;font-size:0.85rem;">'
        f'{html_module.escape(overall_label)}</p>'
        f'<p style="color:{OPS_TEXT_DIM};font-size:0.75rem;margin:4px 0 0;'
        f'font-family:JetBrains Mono,monospace;">'
        f'DATA CONFIDENCE: {int(confidence * 100)}%</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ================================================================
    # QUICK INTELLIGENCE PANEL — Strategic conclusions at a glance
    # ================================================================
    try:
        from src.strategic_synthesis import compute_strategic_assessment
        from src.threat_radar import compute_threat_assessment
        from src.advanced_fusion_algorithms import bayesian_belief_network
        from src.unified_intelligence import compute_advanced_analytics
        from src.fusion_engine import (
            dempster_shafer_fusion, risk_propagation_cascade,
            composite_vulnerability_index, anomaly_severity_ranking,
            temporal_trend_synthesis, topsis_scenario_ranking,
        )

        analytics = compute_advanced_analytics(scores, details, hub.get("raw_data", {}))
        ds = dempster_shafer_fusion(scores, confidence)
        cascade = risk_propagation_cascade(scores, details)
        cvi = composite_vulnerability_index(scores, details, analytics)
        anomalies = anomaly_severity_ranking(scores, details, analytics)
        trends = temporal_trend_synthesis(hub.get("raw_data", {}), analytics, scores)
        bbn = bayesian_belief_network(scores, details, analytics)
        threats = compute_threat_assessment(hub.get("raw_data", {}), details, scores)

        strategic = compute_strategic_assessment(
            scores, details, analytics, ds, cascade, cvi,
            anomalies, trends, [], bbn, hub.get("raw_data", {}),
        )

        grade = strategic.get("strategic_grade", "N/A")
        s_score = strategic.get("strategic_score", 0)
        or_quad = strategic.get("opportunity_risk_quadrant", {})
        quad = or_quad.get("quadrant", "N/A")
        t_level = threats.get("threat_level", "LOW")
        dpq = strategic.get("decision_priority_queue", [])

        gc = OPS_GREEN if s_score >= 70 else (OPS_AMBER if s_score >= 40 else OPS_RED)
        tc = OPS_RED if t_level in ("CRITICAL", "HIGH") else (
            OPS_AMBER if t_level == "ELEVATED" else OPS_GREEN)
        q_colors = {"PRIME": OPS_GREEN, "HIGH-REWARD/HIGH-RISK": OPS_AMBER,
                    "STABLE/LIMITED": OPS_CYAN, "AVOID": OPS_RED}
        qc = q_colors.get(quad, OPS_CYAN)

        st.markdown("---")
        st.markdown(
            '<div class="ops-section-header">'
            '<span class="ops-section-label">INTEL</span>'
            '<span class="ops-section-title">Quick Intelligence Assessment</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Strategic grade + threat + quadrant strip
        qi1, qi2, qi3, qi4 = st.columns(4)
        qi1.markdown(
            f'<div style="text-align:center;padding:12px;border:1px solid {gc}33;'
            f'border-radius:8px;background:{gc}08;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
            f'color:{OPS_TEXT_DIM};letter-spacing:1px;">STRATEGIC GRADE</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:2rem;'
            f'font-weight:900;color:{gc};">{grade}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{gc};">{s_score:.0f}/100</div></div>',
            unsafe_allow_html=True,
        )
        qi2.markdown(
            f'<div style="text-align:center;padding:12px;border:1px solid {tc}33;'
            f'border-radius:8px;background:{tc}08;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
            f'color:{OPS_TEXT_DIM};letter-spacing:1px;">THREAT LEVEL</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:1.4rem;'
            f'font-weight:700;color:{tc};">{t_level}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
            f'color:{OPS_TEXT_DIM};">{threats.get("combined_threats", 0)} sources</div></div>',
            unsafe_allow_html=True,
        )
        qi3.markdown(
            f'<div style="text-align:center;padding:12px;border:1px solid {qc}33;'
            f'border-radius:8px;background:{qc}08;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
            f'color:{OPS_TEXT_DIM};letter-spacing:1px;">CLASSIFICATION</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:1rem;'
            f'font-weight:700;color:{qc};">{quad}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
            f'color:{OPS_TEXT_DIM};">opp-risk quadrant</div></div>',
            unsafe_allow_html=True,
        )

        # Priority #1 action
        if dpq:
            top_action = dpq[0]
            uc_colors = {"IMMEDIATE": OPS_RED, "SHORT-TERM": OPS_AMBER,
                        "MEDIUM-TERM": OPS_CYAN, "LONG-TERM": OPS_BLUE}
            uc = uc_colors.get(top_action.get("urgency", ""), OPS_CYAN)
            qi4.markdown(
                f'<div style="text-align:center;padding:12px;border:1px solid {uc}33;'
                f'border-radius:8px;background:{uc}08;">'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{OPS_TEXT_DIM};letter-spacing:1px;">PRIORITY #1</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
                f'font-weight:600;color:{uc};margin-top:4px;">'
                f'{top_action.get("urgency", "")}</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{OPS_TEXT};margin-top:2px;">'
                f'{html_module.escape(top_action.get("action", "")[:60])}...</div></div>',
                unsafe_allow_html=True,
            )
        else:
            qi4.markdown(
                f'<div style="text-align:center;padding:12px;border:1px solid {OPS_GREEN}33;'
                f'border-radius:8px;background:{OPS_GREEN}08;">'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{OPS_TEXT_DIM};">NO URGENT ACTIONS</div></div>',
                unsafe_allow_html=True,
            )

        # Top 3 insights compact
        key_insights = strategic.get("key_insights", [])
        if key_insights:
            for ins in key_insights[:3]:
                type_colors = {"opportunity": OPS_GREEN, "risk": OPS_RED,
                              "threat": OPS_RED, "constraint": OPS_AMBER,
                              "strength": OPS_CYAN, "insight": OPS_PURPLE}
                ic = type_colors.get(ins.get("type", ""), OPS_CYAN)
                st.markdown(
                    f'<div style="padding:6px 12px;border-left:3px solid {ic};margin:3px 0;'
                    f'background:{ic}06;border-radius:0 4px 4px 0;">'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
                    f'font-weight:700;color:{ic};">{html_module.escape(ins.get("title", ""))}</span> '
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
                    f'color:{OPS_TEXT};">— {html_module.escape(ins.get("text", "")[:120])}</span></div>',
                    unsafe_allow_html=True,
                )

    except Exception as e:
        logger.warning("Quick intelligence panel failed: %s", e)

    # ================================================================
    # GEOPOLITICAL CONTEXT STRIP
    # ================================================================
    try:
        geo = hub.get("raw_data", {}).get("geopolitical", {})
        country = geo.get("country", {})
        if country and country.get("country_name"):
            st.markdown("---")
            st.markdown(
                '<div class="ops-section-header">'
                '<span class="ops-section-label">GEO</span>'
                '<span class="ops-section-title">Geopolitical Context</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            gc1, gc2, gc3, gc4, gc5 = st.columns(5)
            gc1.markdown(
                f'<div style="text-align:center;padding:8px;border:1px solid {OPS_PURPLE}33;'
                f'border-radius:6px;background:{OPS_PURPLE}08;">'
                f'<div style="font-size:0.55rem;color:{OPS_TEXT_DIM};letter-spacing:1px;">'
                f'COUNTRY</div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:{OPS_PURPLE};">'
                f'{html_module.escape(country.get("country_name", "N/A"))}</div></div>',
                unsafe_allow_html=True,
            )
            gc2.markdown(
                f'<div style="text-align:center;padding:8px;border:1px solid {OPS_CYAN}33;'
                f'border-radius:6px;background:{OPS_CYAN}08;">'
                f'<div style="font-size:0.55rem;color:{OPS_TEXT_DIM};letter-spacing:1px;">'
                f'REGION</div>'
                f'<div style="font-size:0.75rem;font-weight:600;color:{OPS_CYAN};">'
                f'{html_module.escape(country.get("subregion", country.get("region", "N/A")))}</div></div>',
                unsafe_allow_html=True,
            )
            pop = country.get("population", 0)
            pop_str = f"{pop / 1e6:.1f}M" if pop >= 1e6 else f"{pop / 1e3:.0f}K" if pop >= 1e3 else str(pop)
            gc3.markdown(
                f'<div style="text-align:center;padding:8px;border:1px solid {OPS_GREEN}33;'
                f'border-radius:6px;background:{OPS_GREEN}08;">'
                f'<div style="font-size:0.55rem;color:{OPS_TEXT_DIM};letter-spacing:1px;">'
                f'POPULATION</div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:{OPS_GREEN};">'
                f'{pop_str}</div></div>',
                unsafe_allow_html=True,
            )
            indicators = geo.get("indicators", {})
            gdp_pc = indicators.get("gdp_per_capita", 0)
            gdp_str = f"${gdp_pc:,.0f}" if gdp_pc else "N/A"
            gc4.markdown(
                f'<div style="text-align:center;padding:8px;border:1px solid {OPS_AMBER}33;'
                f'border-radius:6px;background:{OPS_AMBER}08;">'
                f'<div style="font-size:0.55rem;color:{OPS_TEXT_DIM};letter-spacing:1px;">'
                f'GDP/CAPITA</div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:{OPS_AMBER};">'
                f'{gdp_str}</div></div>',
                unsafe_allow_html=True,
            )
            geo_score = geo.get("geopolitical_score", 0)
            geo_grade = geo.get("geopolitical_grade", "N/A")
            gs_color = OPS_GREEN if geo_score >= 65 else (OPS_AMBER if geo_score >= 40 else OPS_RED)
            gc5.markdown(
                f'<div style="text-align:center;padding:8px;border:1px solid {gs_color}33;'
                f'border-radius:6px;background:{gs_color}08;">'
                f'<div style="font-size:0.55rem;color:{OPS_TEXT_DIM};letter-spacing:1px;">'
                f'GEO STABILITY</div>'
                f'<div style="font-size:1rem;font-weight:900;color:{gs_color};">'
                f'{html_module.escape(geo_grade)}</div>'
                f'<div style="font-size:0.55rem;color:{gs_color};">{geo_score:.0f}/100</div></div>',
                unsafe_allow_html=True,
            )
    except Exception as e:
        logger.warning("Geopolitical context strip failed: %s", e)

    # ================================================================
    # SECTION MAP: TOTAL INTELLIGENCE MAP
    # ================================================================
    raw = hub.get("raw_data", {})

    if HAS_FOLIUM:
        st.markdown("---")
        st.markdown(
            '<div class="ops-section-header">'
            '<span class="ops-section-label">MAP</span>'
            '<span class="ops-section-title">Total Intelligence Map</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # --- Fetch additional data for map (cached) ---
        rainviewer = _fetch_rainviewer_tiles()
        marine_data = _fetch_marine_data(lat, lon)

        # --- Preset buttons ---
        if "cc_map_layers_v2" not in st.session_state:
            st.session_state["cc_map_layers_v2"] = list(_LAYER_PRESETS["Essential"])

        preset_cols = st.columns(len(_LAYER_PRESETS))
        for idx, (preset_name, preset_layers) in enumerate(_LAYER_PRESETS.items()):
            with preset_cols[idx]:
                if st.button(preset_name, key=f"cc_preset_{preset_name}",
                             use_container_width=True):
                    st.session_state["cc_map_layers_v2"] = list(preset_layers)
                    st.rerun()

        # --- Per-category checkboxes ---
        current_sel = set(st.session_state["cc_map_layers_v2"])
        new_sel = set()
        cat_list = list(_INTEL_LAYER_CATEGORIES.items())
        # 3 columns x 2 rows = 6 categories
        row1_cats = cat_list[:3]
        row2_cats = cat_list[3:]

        for row_cats in [row1_cats, row2_cats]:
            cols = st.columns(len(row_cats))
            for ci, (cat_name, layer_names) in enumerate(row_cats):
                with cols[ci]:
                    st.markdown(
                        f'<div style="color:{OPS_CYAN};font-size:0.72rem;'
                        f'font-weight:700;font-family:JetBrains Mono,monospace;'
                        f'margin-bottom:2px;">{cat_name.upper()}</div>',
                        unsafe_allow_html=True,
                    )
                    for lname in layer_names:
                        checked = lname in current_sel
                        is_tile = lname in _TILE_LAYERS
                        suffix = " [tile]" if is_tile else ""
                        if st.checkbox(
                            f"{lname}{suffix}",
                            value=checked,
                            key=f"cc_lyr_{lname}",
                        ):
                            new_sel.add(lname)

        # Sync back to session state
        if new_sel != current_sel:
            st.session_state["cc_map_layers_v2"] = list(new_sel)

        selected_layers = list(new_sel)

        # --- Status strip ---
        n_total = len(selected_layers)
        n_tiles = len([l for l in selected_layers if l in _TILE_LAYERS])
        n_data = n_total - n_tiles
        radar_ok = "LIVE" if rainviewer.get("success") else "N/A"
        marine_ok = "OK" if marine_data.get("current") else "N/A"
        st.markdown(
            f'<div class="ops-data-strip">'
            f'<span class="ops-strip-item" style="color:{OPS_CYAN};font-weight:700;">'
            f'LAYERS: {n_total}</span>'
            f'<span class="ops-strip-item">Tiles: {n_tiles}</span>'
            f'<span class="ops-strip-item">Data: {n_data}</span>'
            f'<span class="ops-strip-item">'
            f'RADAR: <span style="color:{OPS_GREEN if radar_ok == "LIVE" else OPS_RED};">'
            f'{radar_ok}</span></span>'
            f'<span class="ops-strip-item">'
            f'MARINE: <span style="color:{OPS_GREEN if marine_ok == "OK" else OPS_TEXT_DIM};">'
            f'{marine_ok}</span></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # --- Build and render the map ---
        if selected_layers:
            intel_map = _build_total_intel_map(
                lat, lon, raw, details, scores, selected_layers,
                marine_data=marine_data, rainviewer=rainviewer,
            )
            st_html(intel_map._repr_html_(), height=650)
        else:
            st.info("Select at least one layer to display the map.")

    # ================================================================
    # SECTION 3: INTELLIGENCE OVERVIEW (Polar Area + Sunburst)
    # ================================================================
    st.markdown("---")
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-01</span>'
        '<span class="ops-section-title">Intelligence Overview</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_polar, col_sun = st.columns(2)
    with col_polar:
        st.plotly_chart(
            _build_polar_area(scores),
            key="cc_polar", use_container_width=True,
        )
    with col_sun:
        st.plotly_chart(
            _build_sunburst(scores, details),
            key="cc_sunburst", use_container_width=True,
        )

    # ================================================================
    # SECTION 4: KEY METRICS STRIP (ops-terminal style)
    # ================================================================
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-02</span>'
        '<span class="ops-section-title">Key Metrics</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    _metrics = [
        (m1, "ELEV", f"{details.get('center_elev', 0):.0f}m"),
        (m2, "TEMP", f"{details.get('temp_now', 0):.1f}\u00b0C"),
        (m3, "PRECIP", f"{details.get('annual_precip_est', 0):.0f}mm/yr"),
        (m4, "AQI", f"{details.get('aqi', 0)}"),
        (m5, "SPECIES", f"{details.get('total_species_obs', 0)}"),
        (m6, "QUAKES", f"{details.get('eq_count', 0)}"),
    ]
    for col, label, value in _metrics:
        with col:
            st.markdown(
                f'<div class="ops-metric">'
                f'<div class="ops-metric-value">{value}</div>'
                f'<div class="ops-metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ================================================================
    # SECTION 5: RISK & ENVIRONMENT (Gauge + Waterfall + Treemap)
    # ================================================================
    st.markdown("---")
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-03</span>'
        '<span class="ops-section-title">Risk & Environment Analysis</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(
            _build_risk_gauge(scores),
            key="cc_gauge", use_container_width=True,
        )
    with ch2:
        st.plotly_chart(
            _build_risk_waterfall(details, scores),
            key="cc_waterfall", use_container_width=True,
        )

    # Treemap + Network side by side
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-04</span>'
        '<span class="ops-section-title">Domain Analysis</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    ch3, ch4 = st.columns(2)
    with ch3:
        st.plotly_chart(
            _build_treemap(scores),
            key="cc_treemap", use_container_width=True,
        )
    with ch4:
        st.plotly_chart(
            _build_network_graph(scores, insights),
            key="cc_network", use_container_width=True,
        )

    # ================================================================
    # SECTION 6: KEY FINDINGS
    # ================================================================
    st.markdown("---")
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-05</span>'
        '<span class="ops-section-title">Key Findings</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    type_styles = {
        "opportunity": (OPS_GREEN, "OPPORTUNITY"),
        "threat": (OPS_RED, "THREAT"),
        "synergy": (OPS_CYAN, "SYNERGY"),
        "warning": (OPS_AMBER, "WARNING"),
    }

    top_insights = sorted(insights, key=lambda i: i.get("confidence", 0), reverse=True)[:5]
    for insight in top_insights:
        itype = insight.get("type", "synergy")
        color, type_label = type_styles.get(itype, (OPS_TEXT_DIM, "INFO"))
        st.markdown(
            f'<div style="background:{OPS_BG};border-left:3px solid {color};'
            f'border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0;'
            f'font-family:JetBrains Mono,monospace;">'
            f'<span style="color:{color};font-weight:bold;font-size:0.8rem;">'
            f'{html_module.escape(type_label)}: '
            f'{html_module.escape(insight.get("title", ""))}</span>'
            f'<span style="color:{OPS_TEXT_DIM};font-size:0.7rem;margin-left:8px;">'
            f'({insight.get("confidence", 0):.0%})</span><br/>'
            f'<span style="color:{OPS_TEXT};font-size:0.75rem;">'
            f'{html_module.escape(insight.get("text", ""))}</span></div>',
            unsafe_allow_html=True,
        )

    # Top recommendations
    if recommendations:
        st.markdown(
            '<div class="ops-section-header">'
            '<span class="ops-section-label">SEC-06</span>'
            '<span class="ops-section-title">Recommendations</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        for rec in recommendations[:3]:
            conf = rec.get("confidence", "Medium")
            conf_colors = {"High": OPS_GREEN, "Medium": OPS_AMBER, "Low": OPS_TEXT_DIM}
            cc = conf_colors.get(conf, OPS_TEXT_DIM)
            st.markdown(
                f'<div style="background:{OPS_BG};border:1px solid {OPS_GRID};'
                f'border-radius:8px;padding:10px 14px;margin:6px 0;'
                f'font-family:JetBrains Mono,monospace;">'
                f'<span style="color:{OPS_TEXT};font-weight:bold;font-size:0.8rem;">'
                f'{html_module.escape(rec.get("action", ""))}</span>'
                f'<span style="color:{cc};font-size:0.7rem;margin-left:8px;'
                f'background:rgba(0,0,0,0.3);padding:2px 8px;border-radius:6px;">'
                f'{html_module.escape(conf)}</span><br/>'
                f'<span style="color:{OPS_TEXT_DIM};font-size:0.72rem;">'
                f'{html_module.escape(rec.get("rationale", ""))}</span></div>',
                unsafe_allow_html=True,
            )

    # SWOT summary
    with st.expander("SWOT Summary"):
        sc1, sc2 = st.columns(2)
        with sc1:
            strengths = swot.get("S", [])
            s_str = ", ".join(strengths) if strengths else "None identified"
            st.markdown(f"**Strengths:** {s_str}")
            opps = swot.get("O", [])
            o_str = ", ".join(o.get("title", "") for o in opps) if opps else "None identified"
            st.markdown(f"**Opportunities:** {o_str}")
        with sc2:
            weaknesses = swot.get("W", [])
            w_str = ", ".join(weaknesses) if weaknesses else "None identified"
            st.markdown(f"**Weaknesses:** {w_str}")
            threats = swot.get("T", [])
            t_str = ", ".join(t.get("title", "") for t in threats) if threats else "None identified"
            st.markdown(f"**Threats:** {t_str}")

    # ================================================================
    # SECTION 7: API HEALTH STATUS
    # ================================================================
    st.markdown("---")
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-07</span>'
        '<span class="ops-section-title">API Health Status</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    api_sources = [
        ("SoilGrids", "soil"), ("Open-Meteo Weather", "weather"),
        ("Overpass Water", "water"), ("Open Topo Elevation", "elevation"),
        ("Overpass Infra", "infra"), ("Overpass Protected", "protected"),
        ("iNaturalist", "inat"), ("GBIF", "gbif"),
        ("USGS Earthquakes", "quakes"), ("Open-Meteo AQI", "air_quality"),
        ("Macrostrat Geology", "geology"), ("Open-Meteo Archive", "annual_precip_hist"),
    ]

    api_html_items = []
    for api_name, key in api_sources:
        val = raw.get(key)
        is_ok = val not in (None, {}, [], 0)
        dot_color = OPS_GREEN if is_ok else OPS_RED
        status = "OK" if is_ok else "N/A"
        api_html_items.append(
            f'<span class="ops-strip-item">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{dot_color};'
            f'display:inline-block;margin-right:4px;"></span>'
            f'<span style="color:{OPS_TEXT_DIM};font-size:0.65rem;">{api_name}</span>'
            f'<span style="color:{dot_color};font-size:0.65rem;font-weight:600;margin-left:4px;">'
            f'{status}</span>'
            f'</span>'
        )

    st.markdown(
        f'<div class="ops-data-strip" style="flex-wrap:wrap;">'
        f'{"".join(api_html_items)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ================================================================
    # SECTION 8: ADVANCED ANALYTICS (Math Engine)
    # ================================================================
    st.markdown("---")
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-08</span>'
        '<span class="ops-section-title">Advanced Analytics Engine</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    try:
        adv = compute_advanced_analytics(scores, details, raw)
    except Exception as e:
        adv = {}
        st.warning(f"Advanced analytics error: {e}")

    if adv:
        # --- ROW 1: Terrain + Biodiversity ---
        ta1, ta2, ta3 = st.columns(3)
        with ta1:
            tri = adv.get("terrain_roughness", 0)
            tpi = adv.get("topographic_position", 0)
            lisa = adv.get("terrain_lisa", {})
            cluster = lisa.get("cluster", "N/A")
            mi = adv.get("morans_i", 0)
            # TRI classification
            if tri < 80:
                tri_label, tri_c = "Level", OPS_GREEN
            elif tri < 200:
                tri_label, tri_c = "Moderate", OPS_AMBER
            elif tri < 400:
                tri_label, tri_c = "Rough", OPS_RED
            else:
                tri_label, tri_c = "Extreme", OPS_RED
            # TPI classification
            if tpi > 20:
                tpi_label = "Ridge/Hilltop"
            elif tpi < -20:
                tpi_label = "Valley/Depression"
            else:
                tpi_label = "Flat/Mid-slope"
            # LISA cluster names
            cluster_names = {"HH": "High Cluster", "LL": "Low Cluster",
                             "HL": "High Outlier", "LH": "Low Outlier",
                             "uniform": "Uniform", "no_data": "No Data"}
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">TERRAIN ANALYSIS</span>'
                f'<b style="color:{OPS_CYAN};">Roughness (TRI):</b> '
                f'<span style="color:{tri_c};">{tri:.1f}m ({tri_label})</span><br>'
                f'<b style="color:{OPS_CYAN};">Position (TPI):</b> '
                f'{tpi:.1f}m ({tpi_label})<br>'
                f'<b style="color:{OPS_CYAN};">Moran\'s I:</b> {mi:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">LISA Cluster:</b> '
                f'{cluster_names.get(cluster, cluster)}<br>'
                f'<b style="color:{OPS_CYAN};">Slope CV:</b> '
                f'{adv.get("slope_variability", 0):.3f}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with ta2:
            sh = adv.get("shannon_h", 0)
            pe = adv.get("pielou_evenness", 0)
            si = adv.get("simpson_diversity", 0)
            bp = adv.get("berger_parker", 0)
            kl = adv.get("biodiversity_kl_divergence", 0)
            # Evenness quality
            if pe > 0.8:
                pe_label, pe_c = "Excellent", OPS_GREEN
            elif pe > 0.5:
                pe_label, pe_c = "Good", OPS_CYAN
            elif pe > 0.3:
                pe_label, pe_c = "Moderate", OPS_AMBER
            else:
                pe_label, pe_c = "Low", OPS_RED
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">BIODIVERSITY METRICS</span>'
                f'<b style="color:{OPS_CYAN};">Shannon H\':</b> {sh:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">Pielou Evenness:</b> '
                f'<span style="color:{pe_c};">{pe:.4f} ({pe_label})</span><br>'
                f'<b style="color:{OPS_CYAN};">Simpson D:</b> {si:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">Berger-Parker:</b> {bp:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">KL Divergence:</b> {kl:.4f} nats'
                f'</div>',
                unsafe_allow_html=True,
            )

        with ta3:
            sqi = adv.get("soil_quality_index", 0)
            cc_data = adv.get("carrying_capacity", {})
            cap = cc_data.get("capacity", 0)
            limiting = cc_data.get("limiting_factor", "unknown")
            cap_factors = cc_data.get("factors", {})
            if sqi > 0.7:
                sq_c = OPS_GREEN
            elif sqi > 0.4:
                sq_c = OPS_AMBER
            else:
                sq_c = OPS_RED
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">SOIL & CAPACITY</span>'
                f'<b style="color:{OPS_CYAN};">Soil Quality (Geom. Mean):</b> '
                f'<span style="color:{sq_c};">{sqi:.4f}</span><br>'
                f'<b style="color:{OPS_CYAN};">Carrying Capacity:</b> {cap:.3f}<br>'
                f'<b style="color:{OPS_CYAN};">Limiting Factor:</b> '
                f'<span style="color:{OPS_AMBER};">{limiting}</span><br>'
                + "".join(
                    f'<span style="color:{OPS_TEXT_DIM};font-size:0.7rem;">'
                    f'  {k}: {v:.3f}</span><br>'
                    for k, v in cap_factors.items()
                )
                + f'</div>',
                unsafe_allow_html=True,
            )

        # --- ROW 2: Seismic + Precipitation + Score Distribution ---
        tb1, tb2, tb3 = st.columns(3)
        with tb1:
            gr = adv.get("gutenberg_richter", {})
            b_val = gr.get("b", 1.0)
            gr_interp = gr.get("interpretation", "N/A")
            m_max = gr.get("m_max_est", 0)
            interp_labels = {
                "high_stress": ("High Tectonic Stress", OPS_RED),
                "swarm_volcanic": ("Swarm/Volcanic", OPS_AMBER),
                "normal_tectonic": ("Normal Tectonic", OPS_GREEN),
                "insufficient_data": ("Insufficient Data", OPS_TEXT_DIM),
                "uniform_magnitudes": ("Uniform", OPS_TEXT_DIM),
            }
            il, ic = interp_labels.get(gr_interp, ("Unknown", OPS_TEXT_DIM))
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">SEISMIC ANALYSIS</span>'
                f'<b style="color:{OPS_CYAN};">Gutenberg-Richter b:</b> {b_val:.2f}<br>'
                f'<b style="color:{OPS_CYAN};">Regime:</b> '
                f'<span style="color:{ic};">{il}</span><br>'
                f'<b style="color:{OPS_CYAN};">Est. Max Magnitude:</b> M{m_max}<br>'
                f'<b style="color:{OPS_CYAN};">Formula:</b> '
                f'<span style="font-size:0.7rem;">log₁₀(N) = {gr.get("a", 0):.2f} - '
                f'{b_val:.2f}·M</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with tb2:
            ps = adv.get("precip_seasonality", {})
            si_val = ps.get("si", 0)
            si_interp = ps.get("interpretation", "N/A").replace("_", " ").title()
            wettest = ps.get("wettest_month", 0)
            driest = ps.get("driest_month", 0)
            month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            wm = month_names[wettest] if 0 < wettest <= 12 else "?"
            dm = month_names[driest] if 0 < driest <= 12 else "?"
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">PRECIPITATION PATTERN</span>'
                f'<b style="color:{OPS_CYAN};">Seasonality Index:</b> {si_val:.3f}<br>'
                f'<b style="color:{OPS_CYAN};">Pattern:</b> {si_interp}<br>'
                f'<b style="color:{OPS_CYAN};">Wettest:</b> {wm} | '
                f'<b style="color:{OPS_CYAN};">Driest:</b> {dm}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with tb3:
            gini = adv.get("score_gini", 0)
            spread = adv.get("score_spread", 0)
            cv = adv.get("score_cv", 0)
            anom = adv.get("anomaly_score", 0)
            lu_ent = adv.get("landuse_entropy", 0)
            lu_cats = adv.get("landuse_categories", 0)
            if anom < 1.0:
                anom_label, anom_c = "Typical", OPS_GREEN
            elif anom < 2.0:
                anom_label, anom_c = "Unusual", OPS_AMBER
            else:
                anom_label, anom_c = "Anomalous", OPS_RED
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">SCORE DISTRIBUTION</span>'
                f'<b style="color:{OPS_CYAN};">Gini (inequality):</b> {gini:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">Score Spread:</b> {spread:.1f}<br>'
                f'<b style="color:{OPS_CYAN};">Coeff. of Variation:</b> {cv:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">Anomaly Score:</b> '
                f'<span style="color:{anom_c};">{anom:.3f} ({anom_label})</span><br>'
                f'<b style="color:{OPS_CYAN};">Land Use Entropy:</b> '
                f'{lu_ent:.3f} ({lu_cats} categories)'
                f'</div>',
                unsafe_allow_html=True,
            )

        # --- ROW 3: Monte Carlo Confidence Intervals ---
        mc = adv.get("monte_carlo", {})
        if mc:
            st.markdown(
                '<div class="ops-section-header" style="margin-top:12px;">'
                '<span class="ops-section-label">MC</span>'
                '<span class="ops-section-title">'
                'Monte Carlo Confidence Intervals (500 simulations)</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            mc_html = '<div class="ops-data-strip" style="flex-wrap:wrap;">'
            for d_key in INTELLIGENCE_DOMAINS:
                mc_d = mc.get(d_key, {})
                mean_v = mc_d.get("mean", 0)
                ci5 = mc_d.get("ci_5", 0)
                ci95 = mc_d.get("ci_95", 0)
                d_name = INTELLIGENCE_DOMAINS[d_key]["name"]
                d_color = _DOMAIN_OPS_COLORS.get(d_key, OPS_CYAN)
                mc_html += (
                    f'<span class="ops-strip-item">'
                    f'<span style="color:{d_color};font-weight:600;font-size:0.7rem;">'
                    f'{d_name[:12]}</span>'
                    f'<span style="color:{OPS_TEXT};font-size:0.75rem;font-weight:700;">'
                    f' {mean_v:.0f}</span>'
                    f'<span style="color:{OPS_TEXT_DIM};font-size:0.6rem;">'
                    f' [{ci5:.0f}-{ci95:.0f}]</span>'
                    f'</span>'
                )
            mc_overall = mc.get("overall", {})
            mc_html += (
                f'<span class="ops-strip-item" style="border-left:2px solid {OPS_CYAN};">'
                f'<span style="color:{OPS_CYAN};font-weight:700;font-size:0.75rem;">'
                f'OVERALL</span>'
                f'<span style="color:{OPS_TEXT};font-size:0.85rem;font-weight:700;">'
                f' {mc_overall.get("mean", 0):.1f}</span>'
                f'<span style="color:{OPS_TEXT_DIM};font-size:0.65rem;">'
                f' [{mc_overall.get("ci_5", 0):.1f}-{mc_overall.get("ci_95", 0):.1f}] '
                f'90% CI</span>'
                f'</span>'
            )
            mc_html += '</div>'
            st.markdown(mc_html, unsafe_allow_html=True)

        # --- ROW 4: Spectral, Fractal & Wavelet Analysis ---
        st.markdown(
            '<div class="ops-section-header" style="margin-top:12px;">'
            '<span class="ops-section-label">SPEC</span>'
            '<span class="ops-section-title">'
            'Spectral, Fractal & Wavelet Terrain Analysis</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            se = adv.get("spectral_entropy", 0)
            dp = adv.get("dominant_period", 0)
            fd = adv.get("fractal_dimension", 1.0)
            if fd < 1.2:
                fd_label = "Smooth"
            elif fd < 1.5:
                fd_label = "Moderate complexity"
            else:
                fd_label = "Highly complex"
            if se > 0.8:
                se_label = "Random (noise-like)"
            elif se > 0.5:
                se_label = "Mixed periodicity"
            else:
                se_label = "Periodic (regular features)"
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">SPECTRAL & FRACTAL</span>'
                f'<b style="color:{OPS_CYAN};">Fractal Dimension:</b> '
                f'{fd:.4f} ({fd_label})<br>'
                f'<b style="color:{OPS_CYAN};">Spectral Entropy:</b> '
                f'{se:.4f} ({se_label})<br>'
                f'<b style="color:{OPS_CYAN};">Dominant Period:</b> '
                f'{dp:.1f} samples<br>'
                f'<span style="font-size:0.65rem;color:{OPS_TEXT_DIM};">'
                f'DFT: X_k = \u03a3 x_n\u00b7e^(-2\u03c0ikn/N)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with tc2:
            wav = adv.get("wavelet", {})
            energies = wav.get("energies", [])
            dr = wav.get("detail_ratio", 0)
            n_levels = wav.get("levels", 0)
            if dr > 0.7:
                dr_label, dr_c = "Fine-scale dominated", OPS_AMBER
            elif dr > 0.3:
                dr_label, dr_c = "Multi-scale balanced", OPS_GREEN
            else:
                dr_label, dr_c = "Coarse-scale dominated", OPS_CYAN
            energy_str = " | ".join(f"L{i + 1}: {e:.4f}" for i, e in enumerate(energies[:4]))
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">HAAR WAVELET</span>'
                f'<b style="color:{OPS_CYAN};">Levels:</b> {n_levels}<br>'
                f'<b style="color:{OPS_CYAN};">Detail Ratio:</b> '
                f'<span style="color:{dr_c};">{dr:.4f} ({dr_label})</span><br>'
                f'<b style="color:{OPS_CYAN};">Energy/Level:</b><br>'
                f'<span style="font-size:0.7rem;">{energy_str}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with tc3:
            sv = adv.get("semivariogram", {})
            nugget = sv.get("nugget", 0)
            sill = sv.get("sill", 0)
            sv_range = sv.get("range_est", 0)
            gamma_str = " | ".join(f"\u03b3={g}" for g in sv.get("gamma", [])[:4])
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">SEMIVARIOGRAM</span>'
                f'<b style="color:{OPS_CYAN};">Nugget:</b> {nugget:.2f}<br>'
                f'<b style="color:{OPS_CYAN};">Sill:</b> {sill:.2f}<br>'
                f'<b style="color:{OPS_CYAN};">Range:</b> {sv_range:.1f}<br>'
                f'<b style="color:{OPS_CYAN};">Values:</b><br>'
                f'<span style="font-size:0.7rem;">{gamma_str}</span><br>'
                f'<span style="font-size:0.65rem;color:{OPS_TEXT_DIM};">'
                f'\u03b3(h) = (1/2N)\u03a3(Z(xi)-Z(xi+h))\u00b2</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # --- ROW 5: Stochastic & Probabilistic ---
        st.markdown(
            '<div class="ops-section-header" style="margin-top:12px;">'
            '<span class="ops-section-label">PROB</span>'
            '<span class="ops-section-title">'
            'Stochastic & Probabilistic Models</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        td1, td2, td3 = st.columns(3)
        with td1:
            mk = adv.get("precip_markov", {})
            stationary = mk.get("stationary", [])
            ent_rate = mk.get("entropy_rate", 0)
            mix_t = mk.get("mixing_time", 0)
            state_labels = ["Dry", "Light", "Heavy"]
            stat_str = " | ".join(
                f"{state_labels[i]}: {stationary[i]:.2f}"
                for i in range(min(len(stationary), 3))
            ) if stationary else "N/A"
            # Transition matrix display
            matrix = mk.get("matrix", [])
            mx_str = ""
            for i, row in enumerate(matrix[:3]):
                row_str = " ".join(f"{p:.2f}" for p in row[:3])
                mx_str += f"  {state_labels[i]:>5}: [{row_str}]<br>"
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">MARKOV CHAIN (Precip)</span>'
                f'<b style="color:{OPS_CYAN};">Stationary Dist:</b><br>'
                f'<span style="font-size:0.75rem;">{stat_str}</span><br>'
                f'<b style="color:{OPS_CYAN};">Entropy Rate:</b> {ent_rate:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">Mixing Time:</b> {mix_t:.1f} steps<br>'
                f'<b style="color:{OPS_CYAN};">P(i\u2192j):</b><br>'
                f'<span style="font-size:0.65rem;font-family:monospace;">{mx_str}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with td2:
            wb = adv.get("seismic_weibull", {})
            wb_k = wb.get("k", 1)
            wb_lam = wb.get("lam", 1)
            wb_interp = wb.get("interpretation", "N/A").replace("_", " ").title()
            wb_median = wb.get("median", 0)
            bt = adv.get("score_beta", {})
            bt_alpha = bt.get("alpha", 1)
            bt_beta = bt.get("beta", 1)
            bt_mode = bt.get("mode", 50)
            bt_skew = bt.get("skewness", 0)
            bt_conc = bt.get("concentration", 2)
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">DISTRIBUTION FITTING</span>'
                f'<b style="color:{OPS_CYAN};">Seismic Weibull k:</b> {wb_k:.3f}<br>'
                f'<b style="color:{OPS_CYAN};">Weibull \u03bb:</b> {wb_lam:.3f}<br>'
                f'<b style="color:{OPS_CYAN};">Hazard:</b> {wb_interp}<br>'
                f'<b style="color:{OPS_CYAN};">Median magnitude:</b> {wb_median:.2f}<br>'
                f'<span style="border-top:1px solid {OPS_GRID};display:block;margin:4px 0;"></span>'
                f'<b style="color:{OPS_CYAN};">Score Beta(\u03b1,\u03b2):</b> '
                f'({bt_alpha:.2f}, {bt_beta:.2f})<br>'
                f'<b style="color:{OPS_CYAN};">Mode:</b> {bt_mode:.1f} | '
                f'<b style="color:{OPS_CYAN};">Skew:</b> {bt_skew:.3f}<br>'
                f'<b style="color:{OPS_CYAN};">Concentration:</b> {bt_conc:.1f}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with td3:
            fz = adv.get("fuzzy_environment", {})
            fz_score = fz.get("fuzzy_score", 0)
            if fz_score > 70:
                fz_c = OPS_GREEN
            elif fz_score > 40:
                fz_c = OPS_AMBER
            else:
                fz_c = OPS_RED
            temp_m = fz.get("temperature", {})
            aqi_m = fz.get("air_quality", {})
            # Show dominant fuzzy set per variable
            def _dom(d):
                if not d:
                    return "N/A"
                return max(d, key=d.get)
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">FUZZY INFERENCE</span>'
                f'<b style="color:{OPS_CYAN};">Fuzzy Score:</b> '
                f'<span style="color:{fz_c};font-size:1.1rem;font-weight:700;">'
                f'{fz_score:.1f}</span><br>'
                f'<b style="color:{OPS_CYAN};">Temp class:</b> {_dom(temp_m)}<br>'
                f'<b style="color:{OPS_CYAN};">AQI class:</b> {_dom(aqi_m)}<br>'
                f'<b style="color:{OPS_CYAN};">Elev class:</b> '
                f'{_dom(fz.get("elevation", {}))}<br>'
                f'<b style="color:{OPS_CYAN};">Precip class:</b> '
                f'{_dom(fz.get("precipitation", {}))}<br>'
                f'<span style="font-size:0.6rem;color:{OPS_TEXT_DIM};">'
                f'6 Mamdani rules, centroid defuzz.</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # --- ROW 6: Graph, Entropy & Zipf ---
        st.markdown(
            '<div class="ops-section-header" style="margin-top:12px;">'
            '<span class="ops-section-label">INFO</span>'
            '<span class="ops-section-title">'
            'Information Theory, Graph & Power Laws</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        te1, te2, te3 = st.columns(3)
        with te1:
            gc = adv.get("graph_centrality", {})
            most_c = gc.get("most_central", "N/A")
            most_i = gc.get("most_isolated", "N/A")
            avg_cl = gc.get("avg_clustering", 0)
            net_d = gc.get("network_density", 0)
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">GRAPH CENTRALITY</span>'
                f'<b style="color:{OPS_CYAN};">Most Central:</b> '
                f'<span style="color:{OPS_GREEN};">{most_c}</span><br>'
                f'<b style="color:{OPS_CYAN};">Most Isolated:</b> '
                f'<span style="color:{OPS_AMBER};">{most_i}</span><br>'
                f'<b style="color:{OPS_CYAN};">Avg Clustering:</b> {avg_cl:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">Network Density:</b> {net_d:.4f}<br>'
                f'<span style="font-size:0.65rem;color:{OPS_TEXT_DIM};">'
                f'C_i = 2T_i/(k_i(k_i-1)), D = 2E/(V(V-1))</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with te2:
            r0 = adv.get("renyi_entropy_0", 0)
            r2 = adv.get("renyi_entropy_2", 0)
            ts2 = adv.get("tsallis_entropy_2", 0)
            sh = adv.get("shannon_h", 0)
            ks = adv.get("seismic_ks_test", {})
            ks_d = ks.get("d_stat", 0)
            ks_p = ks.get("p_value", 1)
            ks_reject = ks.get("reject_h0", False)
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">ENTROPY FAMILY</span>'
                f'<b style="color:{OPS_CYAN};">Shannon H\u2032:</b> {sh:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">R\u00e9nyi H\u2080:</b> {r0:.4f} '
                f'<span style="font-size:0.6rem;">(richness)</span><br>'
                f'<b style="color:{OPS_CYAN};">R\u00e9nyi H\u2082:</b> {r2:.4f} '
                f'<span style="font-size:0.6rem;">(collision)</span><br>'
                f'<b style="color:{OPS_CYAN};">Tsallis S\u2082:</b> {ts2:.4f}<br>'
                f'<span style="border-top:1px solid {OPS_GRID};display:block;margin:4px 0;"></span>'
                f'<b style="color:{OPS_CYAN};">Seismic K-S test:</b> '
                f'D={ks_d:.4f}, p={ks_p:.4f}<br>'
                f'<span style="font-size:0.7rem;color:'
                f'{OPS_RED if ks_reject else OPS_GREEN};">'
                f'{"Reject exponential" if ks_reject else "Consistent with exponential"}'
                f'</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with te3:
            lu_zipf = adv.get("landuse_zipf", {})
            sp_zipf = adv.get("species_zipf", {})
            lu_alpha = lu_zipf.get("alpha", 0)
            lu_r2 = lu_zipf.get("r_squared", 0)
            lu_is_z = lu_zipf.get("is_zipfian", False)
            sp_alpha = sp_zipf.get("alpha", 0)
            sp_r2 = sp_zipf.get("r_squared", 0)
            ek = adv.get("elev_spatial_kendall", {})
            ek_tau = ek.get("tau", 0)
            ek_str = ek.get("strength", "N/A")
            st.markdown(
                f'<div class="ops-terminal">'
                f'<span class="ops-term-label">POWER LAWS & DEPENDENCY</span>'
                f'<b style="color:{OPS_CYAN};">Land Use Zipf \u03b1:</b> {lu_alpha:.3f} '
                f'(R\u00b2={lu_r2:.3f})<br>'
                f'<span style="font-size:0.7rem;color:'
                f'{OPS_GREEN if lu_is_z else OPS_TEXT_DIM};">'
                f'{"Zipfian distribution" if lu_is_z else "Non-Zipfian"}</span><br>'
                f'<b style="color:{OPS_CYAN};">Species Zipf \u03b1:</b> {sp_alpha:.3f} '
                f'(R\u00b2={sp_r2:.3f})<br>'
                f'<span style="border-top:1px solid {OPS_GRID};display:block;margin:4px 0;"></span>'
                f'<b style="color:{OPS_CYAN};">Kendall \u03c4:</b> {ek_tau:.4f}<br>'
                f'<b style="color:{OPS_CYAN};">Correlation:</b> {ek_str}'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ================================================================
    # SECTION 9: RECOMMENDED MODULES
    # ================================================================
    st.markdown("---")
    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">SEC-08</span>'
        '<span class="ops-section-title">Recommended Modules</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    try:
        from app import _MODULE_LOOKUP
    except ImportError:
        _MODULE_LOOKUP = {}

    rec_ids = _get_recommended_modules(scores, max_count=8)
    rec_cols = st.columns(4)
    for idx, mid in enumerate(rec_ids):
        mod = _MODULE_LOOKUP.get(mid)
        if not mod:
            continue
        with rec_cols[idx % 4]:
            st.markdown(
                f'<div class="recommended-card">'
                f'<div class="mod-icon">{mod.get("icon", "")}</div>'
                f'<div class="mod-name">{html_module.escape(mod.get("name", mid))}</div>'
                f'<div class="mod-desc">{html_module.escape(mod.get("desc", "")[:80])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                f"Open", key=f"cc_rec_{mid}",
                use_container_width=True,
            ):
                st.session_state.current_page = mid
                st.rerun()

    # ================================================================
    # SECTION 9: QUICK ACCESS CATEGORIES + BROWSE ALL
    # ================================================================
    st.markdown("---")
    _render_category_links()

    try:
        from app import MODULE_REGISTRY as _reg
        _total = sum(len(c.get("modules", [])) for c in _reg)
    except ImportError:
        _total = 313

    st.markdown("")
    if st.button(
        f"Browse All {_total} Modules",
        key="cc_browse_all",
        use_container_width=True,
    ):
        st.session_state.current_page = "catalog"
        st.rerun()


# ---------------------------------------------------------------------------
# CATEGORY LINKS HELPER
# ---------------------------------------------------------------------------

def _render_category_links():
    """Render quick-access links to module categories."""
    try:
        from app import MODULE_REGISTRY
    except ImportError:
        return

    st.markdown(
        '<div class="ops-section-header">'
        '<span class="ops-section-label">NAV</span>'
        '<span class="ops-section-title">Module Categories</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    n_cols = min(len(MODULE_REGISTRY), 5)
    cat_cols = st.columns(n_cols)
    _cat_ops_colors = {
        "cyan": OPS_CYAN, "violet": OPS_PURPLE, "emerald": OPS_GREEN,
        "pink": "#ff66aa", "amber": OPS_AMBER, "red": OPS_RED,
        "indigo": OPS_BLUE, "blue": OPS_BLUE, "orange": OPS_AMBER,
        "teal": OPS_CYAN,
    }
    for idx, cat in enumerate(MODULE_REGISTRY):
        with cat_cols[idx % n_cols]:
            count = len(cat.get("modules", []))
            color = _cat_ops_colors.get(cat.get("color", ""), OPS_CYAN)
            st.markdown(
                f'<div style="background:{OPS_BG};border:1px solid {color}33;'
                f'border-radius:8px;padding:0.7rem;text-align:center;'
                f'border-top:2px solid {color};font-family:JetBrains Mono,monospace;">'
                f'<div style="color:{OPS_TEXT};font-weight:600;font-size:0.78rem;">'
                f'{html_module.escape(cat["category"])}</div>'
                f'<div style="color:{color};font-size:0.7rem;font-weight:600;">'
                f'{count} modules</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
