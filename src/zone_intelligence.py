"""
Zone Intelligence Aggregator module for TerraScout AI.

The MOST comprehensive module in the platform. Lets users select any area on
the map and see ALL available data layers overlaid: terrain, weather, species,
infrastructure, risks, and real-time feeds.

Uses only free APIs with no API keys required:
  - Overpass API (3-server fallback via overpass_client)
  - Open-Meteo (weather + air quality)
  - USGS Earthquake Hazards
  - NASA FIRMS (active fires)
  - Open Topo Data (elevation)
  - iNaturalist (species observations)
  - Nominatim (reverse geocoding)
  - GBIF (biodiversity occurrences)
  - ISRIC SoilGrids (soil properties)
  - OpenSky Network (live flights)
"""

import io
import json
import math
import logging
from datetime import datetime, timedelta
from typing import Any

import streamlit as st
import requests
import pandas as pd
import numpy as np
try:
    import folium
    from folium.plugins import MarkerCluster, HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import html as html_module
from streamlit.components.v1 import html as st_html

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

_HEADERS = {"User-Agent": "TerraScoutAI/1.0"}

# API endpoints
OPEN_METEO_WEATHER = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AQ = "https://air-quality-api.open-meteo.com/v1/air-quality"
USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"
INAT_API = "https://api.inaturalist.org/v1"
NOMINATIM_API = "https://nominatim.openstreetmap.org/reverse"
GBIF_API = "https://api.gbif.org/v1/occurrence/search"
SOILGRIDS_API = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OPENSKY_API = "https://opensky-network.org/api/states/all"
FIRMS_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Layer color palette
LAYER_COLORS = {
    "buildings": "#f97316",
    "roads": "#a855f7",
    "water": "#3b82f6",
    "vegetation": "#22c55e",
    "terrain": "#8b5cf6",
    "earthquakes": "#ef4444",
    "fires": "#f97316",
    "species": "#06b6d4",
    "weather": "#fbbf24",
    "soil": "#92400e",
    "flights": "#e879f9",
    "amenities": "#14b8a6",
    "landuse": "#84cc16",
    "military": "#dc2626",
    "heritage": "#d97706",
}

# WMO Weather Code mapping
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain",
    65: "Heavy rain", 71: "Slight snow", 73: "Moderate snow",
    75: "Heavy snow", 80: "Slight showers", 81: "Moderate showers",
    82: "Violent showers", 95: "Thunderstorm", 96: "Thunderstorm + hail",
}

# Analysis modes
ANALYSIS_MODES = {
    "Full Intelligence Report": {
        "desc": "All layers active, comprehensive dashboard",
        "layers": [
            "buildings", "roads", "water", "vegetation", "terrain",
            "earthquakes", "fires", "species", "weather", "soil",
            "flights", "amenities", "landuse", "military", "heritage",
        ],
    },
    "Environmental Profile": {
        "desc": "Terrain, climate, soil, water, vegetation",
        "layers": ["terrain", "weather", "soil", "water", "vegetation"],
    },
    "Biodiversity Assessment": {
        "desc": "Species, habitats, protected areas",
        "layers": ["species", "vegetation", "water"],
    },
    "Infrastructure Analysis": {
        "desc": "Buildings, roads, utilities, population",
        "layers": ["buildings", "roads", "amenities", "landuse"],
    },
    "Risk Assessment": {
        "desc": "Seismic, fire, flood, conflict zones",
        "layers": ["earthquakes", "fires", "water", "military"],
    },
    "Historical Context": {
        "desc": "Archaeological sites, historic buildings, ancient features",
        "layers": ["heritage", "buildings"],
    },
    "Real-Time Monitor": {
        "desc": "Live weather, flights, earthquakes, fires",
        "layers": ["weather", "flights", "earthquakes", "fires"],
    },
    "Resource Survey": {
        "desc": "Soil, minerals, water table, agricultural potential",
        "layers": ["soil", "water", "vegetation", "landuse"],
    },
    "Urban Intelligence": {
        "desc": "Buildings, amenities, transport, population density",
        "layers": ["buildings", "roads", "amenities", "landuse"],
    },
    "Custom Analysis": {
        "desc": "User selects which layers to include",
        "layers": [],
    },
}

# Preset locations for quick access
ZONE_PRESETS = {
    "Custom": None,
    "Rome, Italy": {"lat": 41.9028, "lon": 12.4964},
    "New York, USA": {"lat": 40.7128, "lon": -74.0060},
    "Tokyo, Japan": {"lat": 35.6762, "lon": 139.6503},
    "Cairo, Egypt": {"lat": 30.0444, "lon": 31.2357},
    "Amazon Basin, Brazil": {"lat": -3.4653, "lon": -62.2159},
    "Great Barrier Reef": {"lat": -18.2871, "lon": 147.6992},
    "Yellowstone, USA": {"lat": 44.4280, "lon": -110.5885},
    "Sahara, Algeria": {"lat": 27.0, "lon": 2.0},
    "Kathmandu, Nepal": {"lat": 27.7172, "lon": 85.3240},
    "London, UK": {"lat": 51.5074, "lon": -0.1278},
    "Nairobi, Kenya": {"lat": -1.2921, "lon": 36.8219},
    "Sydney, Australia": {"lat": -33.8688, "lon": 151.2093},
    "Mexico City": {"lat": 19.4326, "lon": -99.1332},
    "Istanbul, Turkey": {"lat": 41.0082, "lon": 28.9784},
}

# Soil properties to query
SOIL_PROPERTIES = ["phh2o", "soc", "clay", "sand", "silt", "bdod", "nitrogen"]
SOIL_DIVISORS = {
    "phh2o": 10, "soc": 10, "clay": 10, "sand": 10,
    "silt": 10, "bdod": 100, "nitrogen": 100,
}
SOIL_LABELS = {
    "phh2o": "pH", "soc": "Organic C (g/kg)", "clay": "Clay (%)",
    "sand": "Sand (%)", "silt": "Silt (%)", "bdod": "Bulk Density (kg/dm3)",
    "nitrogen": "Nitrogen (g/kg)",
}


# ═══════════════════════════════════════════════════════════════════════════════
# IDW INTERPOLATION
# ═══════════════════════════════════════════════════════════════════════════════

def idw_interpolate(
    known_points: np.ndarray,
    known_values: np.ndarray,
    target_point: np.ndarray,
    power: float = 2.0,
) -> float:
    """Inverse Distance Weighting interpolation.

    Given known data points with associated values, estimate the value at
    *target_point* using IDW with the specified power parameter.

    Args:
        known_points: Array of shape (N, 2) with lat/lon of known points.
        known_values: Array of shape (N,) with values at known points.
        target_point: Array of shape (2,) for the query location.
        power: Distance weighting exponent (default 2).

    Returns:
        Estimated value at the target point.
    """
    if len(known_points) == 0:
        return 0.0
    distances = np.sqrt(np.sum((known_points - target_point) ** 2, axis=1))
    mask = distances > 0
    if not np.any(mask):
        return float(np.mean(known_values))
    weights = 1.0 / (distances[mask] ** power)
    return float(np.sum(weights * np.asarray(known_values)[mask]) / np.sum(weights))


# ═══════════════════════════════════════════════════════════════════════════════
# BBOX HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _km_to_deg(km: float) -> float:
    """Approximate km to degrees (rough, latitude-independent)."""
    return km / 111.32


def _compute_bbox(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Compute bounding box (south, west, north, east) from centre + radius."""
    delta = _km_to_deg(radius_km)
    cos_lat = math.cos(math.radians(lat))
    delta_lon = delta / max(cos_lat, 0.01)
    return (lat - delta, lon - delta_lon, lat + delta, lon + delta_lon)


def _bbox_str(bbox: tuple) -> str:
    """Format bbox as 'south,west,north,east' for Overpass."""
    return f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING FUNCTIONS  (each cached, with error handling)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Nominatim reverse geocoding ──────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_place_name(lat: float, lon: float) -> dict:
    """Reverse geocode a lat/lon to a place name via Nominatim."""
    try:
        resp = requests.get(
            NOMINATIM_API,
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "display_name": data.get("display_name", "Unknown"),
            "address": data.get("address", {}),
        }
    except Exception as e:
        logger.warning("Nominatim error: %s", e)
        return {"display_name": "Unknown", "address": {}, "error": str(e)}


# ── Open-Meteo weather ──────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current weather from Open-Meteo."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": (
                "temperature_2m,relative_humidity_2m,precipitation,"
                "wind_speed_10m,wind_direction_10m,weather_code,"
                "surface_pressure,cloud_cover,apparent_temperature"
            ),
            "timezone": "auto",
        }
        resp = requests.get(OPEN_METEO_WEATHER, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Weather error: %s", e)
        return {"error": str(e)}


# ── Open-Meteo air quality ──────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_air_quality(lat: float, lon: float) -> dict:
    """Fetch current air quality from Open-Meteo."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
            "timezone": "auto",
        }
        resp = requests.get(OPEN_METEO_AQ, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Air quality error: %s", e)
        return {"error": str(e)}


# ── USGS Earthquakes ────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_earthquakes(lat: float, lon: float, radius_km: float, days: int = 30) -> dict:
    """Fetch recent earthquakes from USGS within the zone."""
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        params = {
            "format": "geojson",
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"),
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": min(radius_km, 500),
            "minmagnitude": 1.0,
            "limit": 500,
            "orderby": "time",
        }
        resp = requests.get(USGS_API, params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("USGS error: %s", e)
        return {"type": "FeatureCollection", "features": [], "error": str(e)}


# ── NASA FIRMS active fires ─────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_fires(lat: float, lon: float, radius_km: float) -> list[dict]:
    """Fetch active fire detections from NASA FIRMS using the map API.
    Falls back to returning empty list if no data / errors."""
    try:
        bbox = _compute_bbox(lat, lon, radius_km)
        # Use area query with VIIRS source
        area_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/VIIRS_SNPP_NRT/{area_str}/1"
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        if resp.status_code == 200 and resp.text.strip():
            lines = resp.text.strip().split("\n")
            if len(lines) > 1:
                header = lines[0].split(",")
                records = []
                for line in lines[1:]:
                    vals = line.split(",")
                    if len(vals) >= len(header):
                        records.append(dict(zip(header, vals)))
                return records
        return []
    except Exception as e:
        logger.warning("FIRMS error: %s", e)
        return []


# ── Open Topo Data elevation ────────────────────────────────────────────────

@st.cache_data(ttl=600)
def fetch_elevation_grid(lat: float, lon: float, radius_km: float, grid_size: int = 5) -> dict:
    """Fetch elevation for a grid of points around the centre.

    Returns dict with 'points' list of {lat, lon, elevation} and summary stats.
    """
    try:
        delta = _km_to_deg(radius_km)
        cos_lat = math.cos(math.radians(lat))
        delta_lon = delta / max(cos_lat, 0.01)
        lats = np.linspace(lat - delta, lat + delta, grid_size)
        lons = np.linspace(lon - delta_lon, lon + delta_lon, grid_size)
        coords = []
        for la in lats:
            for lo in lons:
                coords.append(f"{la:.5f},{lo:.5f}")
        # API accepts up to 100 locations per call
        batch_size = 100
        all_results = []
        for i in range(0, len(coords), batch_size):
            batch = "|".join(coords[i:i + batch_size])
            resp = requests.get(
                OPEN_TOPO_API,
                params={"locations": batch},
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "OK":
                all_results.extend(data.get("results", []))

        points = []
        elevations = []
        for r in all_results:
            elev = r.get("elevation")
            loc = r.get("location", {})
            if elev is not None:
                points.append({"lat": loc.get("lat"), "lon": loc.get("lng"), "elevation": elev})
                elevations.append(elev)

        stats = {}
        if elevations:
            stats = {
                "min": min(elevations),
                "max": max(elevations),
                "avg": sum(elevations) / len(elevations),
                "range": max(elevations) - min(elevations),
            }
        return {"points": points, "stats": stats}
    except Exception as e:
        logger.warning("Elevation error: %s", e)
        return {"points": [], "stats": {}, "error": str(e)}


# ── iNaturalist species ─────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def fetch_species(lat: float, lon: float, radius_km: float, per_page: int = 200) -> dict:
    """Fetch species observations from iNaturalist."""
    try:
        params = {
            "lat": lat, "lng": lon,
            "radius": min(radius_km, 100),
            "per_page": min(per_page, 200),
            "order": "desc", "order_by": "observed_on",
            "quality_grade": "research",
        }
        resp = requests.get(f"{INAT_API}/observations", params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("iNaturalist error: %s", e)
        return {"total_results": 0, "results": [], "error": str(e)}


@st.cache_data(ttl=600)
def fetch_species_counts(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch species count summary from iNaturalist."""
    try:
        params = {
            "lat": lat, "lng": lon,
            "radius": min(radius_km, 100),
            "quality_grade": "research",
        }
        resp = requests.get(f"{INAT_API}/observations/species_counts", params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("iNaturalist species_counts error: %s", e)
        return {"total_results": 0, "results": [], "error": str(e)}


# ── GBIF biodiversity ───────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def fetch_gbif(lat: float, lon: float, radius_km: float, limit: int = 300) -> dict:
    """Fetch biodiversity occurrence data from GBIF."""
    try:
        params = {
            "decimalLatitude": f"{lat - _km_to_deg(radius_km)},{lat + _km_to_deg(radius_km)}",
            "decimalLongitude": f"{lon - _km_to_deg(radius_km)},{lon + _km_to_deg(radius_km)}",
            "limit": min(limit, 300),
            "hasCoordinate": "true",
            "hasGeospatialIssue": "false",
        }
        resp = requests.get(GBIF_API, params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("GBIF error: %s", e)
        return {"count": 0, "results": [], "error": str(e)}


# ── ISRIC SoilGrids ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_soil(lat: float, lon: float) -> dict:
    """Fetch soil properties from ISRIC SoilGrids."""
    try:
        params = {
            "lon": lon,
            "lat": lat,
            "property": SOIL_PROPERTIES,
            "depth": ["0-5cm", "5-15cm", "15-30cm"],
            "value": "mean",
        }
        resp = requests.get(SOILGRIDS_API, params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("SoilGrids error: %s", e)
        return {"error": str(e)}


# ── OpenSky flights ─────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_flights(lat: float, lon: float, radius_km: float) -> list[dict]:
    """Fetch live aircraft states from OpenSky Network."""
    try:
        bbox = _compute_bbox(lat, lon, radius_km)
        params = {
            "lamin": bbox[0], "lomin": bbox[1],
            "lamax": bbox[2], "lomax": bbox[3],
        }
        resp = requests.get(OPENSKY_API, params=params, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        states = data.get("states", []) or []
        flights = []
        for s in states[:200]:  # cap at 200 for performance
            if not isinstance(s, (list, tuple)) or len(s) < 11:
                continue
            if s[5] is not None and s[6] is not None:
                flights.append({
                    "callsign": (s[1] or "").strip(),
                    "origin_country": s[2] or "",
                    "lon": s[5],
                    "lat": s[6],
                    "altitude_m": s[7] if s[7] else 0,
                    "velocity_ms": s[9] if s[9] else 0,
                    "heading": s[10] if s[10] else 0,
                    "on_ground": s[8],
                })
        return flights
    except Exception as e:
        logger.warning("OpenSky error: %s", e)
        return []


# ── Overpass OSM queries ─────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def fetch_osm_buildings(bbox: tuple) -> list[dict]:
    """Fetch buildings from OpenStreetMap via Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      way["building"]({bb});
      node["building"]({bb});
    );
    out center 500;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon_v = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat_v and lon_v:
            tags = el.get("tags", {})
            results.append({
                "lat": lat_v, "lon": lon_v,
                "type": tags.get("building", "yes"),
                "name": tags.get("name", ""),
                "levels": tags.get("building:levels", ""),
            })
    return results


@st.cache_data(ttl=600)
def fetch_osm_roads(bbox: tuple) -> list[dict]:
    """Fetch roads from OpenStreetMap via Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      way["highway"]({bb});
    );
    out center 500;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        center = el.get("center", {})
        if center:
            tags = el.get("tags", {})
            results.append({
                "lat": center.get("lat"), "lon": center.get("lon"),
                "highway": tags.get("highway", ""),
                "name": tags.get("name", ""),
                "surface": tags.get("surface", ""),
            })
    return results


@st.cache_data(ttl=600)
def fetch_osm_water(bbox: tuple) -> list[dict]:
    """Fetch water features from OpenStreetMap via Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      way["waterway"]({bb});
      way["natural"="water"]({bb});
      node["natural"="spring"]({bb});
      relation["natural"="water"]({bb});
    );
    out center 300;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon_v = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat_v and lon_v:
            tags = el.get("tags", {})
            wtype = tags.get("waterway") or tags.get("natural") or tags.get("water", "water")
            results.append({
                "lat": lat_v, "lon": lon_v,
                "type": wtype,
                "name": tags.get("name", ""),
            })
    return results


@st.cache_data(ttl=600)
def fetch_osm_vegetation(bbox: tuple) -> list[dict]:
    """Fetch vegetation / natural features from Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      way["natural"~"wood|scrub|grassland|heath|wetland"]({bb});
      way["landuse"~"forest|meadow|orchard|vineyard"]({bb});
      node["natural"="tree"]({bb});
    );
    out center 300;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon_v = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat_v and lon_v:
            tags = el.get("tags", {})
            vtype = tags.get("natural") or tags.get("landuse", "vegetation")
            results.append({
                "lat": lat_v, "lon": lon_v,
                "type": vtype,
                "name": tags.get("name", ""),
                "leaf_type": tags.get("leaf_type", ""),
            })
    return results


@st.cache_data(ttl=600)
def fetch_osm_amenities(bbox: tuple) -> list[dict]:
    """Fetch amenities / POIs from Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"]({bb});
      node["shop"]({bb});
      node["tourism"]({bb});
    );
    out 300;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        if el.get("lat") and el.get("lon"):
            tags = el.get("tags", {})
            atype = tags.get("amenity") or tags.get("shop") or tags.get("tourism", "poi")
            results.append({
                "lat": el["lat"], "lon": el["lon"],
                "type": atype,
                "name": tags.get("name", ""),
            })
    return results


@st.cache_data(ttl=600)
def fetch_osm_landuse(bbox: tuple) -> list[dict]:
    """Fetch land use areas from Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      way["landuse"]({bb});
    );
    out center 300;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        center = el.get("center", {})
        if center:
            tags = el.get("tags", {})
            results.append({
                "lat": center.get("lat"), "lon": center.get("lon"),
                "type": tags.get("landuse", ""),
                "name": tags.get("name", ""),
            })
    return results


@st.cache_data(ttl=600)
def fetch_osm_military(bbox: tuple) -> list[dict]:
    """Fetch military / restricted areas from Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      way["military"]({bb});
      node["military"]({bb});
      way["landuse"="military"]({bb});
    );
    out center 200;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon_v = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat_v and lon_v:
            tags = el.get("tags", {})
            results.append({
                "lat": lat_v, "lon": lon_v,
                "type": tags.get("military", "military"),
                "name": tags.get("name", ""),
            })
    return results


@st.cache_data(ttl=600)
def fetch_osm_heritage(bbox: tuple) -> list[dict]:
    """Fetch heritage / archaeological sites from Overpass."""
    bb = _bbox_str(bbox)
    query = f"""
    [out:json][timeout:30];
    (
      node["historic"]({bb});
      way["historic"]({bb});
      node["archaeological_site"]({bb});
      way["archaeological_site"]({bb});
      node["heritage"]({bb});
    );
    out center 300;
    """
    data = query_overpass(query, timeout=35)
    if data is None or "_error" in (data or {}):
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon_v = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat_v and lon_v:
            tags = el.get("tags", {})
            htype = tags.get("historic") or tags.get("archaeological_site", "heritage")
            results.append({
                "lat": lat_v, "lon": lon_v,
                "type": htype,
                "name": tags.get("name", ""),
                "period": tags.get("historic:period", ""),
            })
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SOIL DATA PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_soil_data(soil_raw: dict) -> dict:
    """Parse SoilGrids response into a clean summary dict."""
    result = {}
    properties = soil_raw.get("properties", {})
    layers = properties.get("layers", [])
    for layer in layers:
        prop_name = layer.get("name", "")
        depths = layer.get("depths", [])
        if depths:
            top = depths[0]  # 0-5cm
            values = top.get("values", {})
            mean_val = values.get("mean")
            if mean_val is not None:
                divisor = SOIL_DIVISORS.get(prop_name, 1)
                result[prop_name] = round(mean_val / divisor, 2)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# MAP BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _build_zone_map(
    lat: float,
    lon: float,
    radius_km: float,
    layer_data: dict[str, Any],
    active_layers: list[str],
) -> folium.Map:
    """Build the folium map with all active layers overlaid."""
    m = folium.Map(location=[lat, lon], zoom_start=_auto_zoom(radius_km), tiles="CartoDB dark_matter")

    # Zone circle
    folium.Circle(
        location=[lat, lon],
        radius=radius_km * 1000,
        color="#06b6d4",
        fill=True,
        fill_opacity=0.05,
        weight=2,
        dash_array="8 4",
        popup="Analysis Zone",
    ).add_to(m)

    # Centre marker
    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(html='<div style="font-size:18px;">&#x1F3AF;</div>'),
        popup=f"Centre: {lat:.4f}, {lon:.4f}",
    ).add_to(m)

    # ── Buildings ────────────────────────────────────────────────────────────
    if "buildings" in active_layers and layer_data.get("buildings"):
        fg = folium.FeatureGroup(name="Buildings", show=True)
        cluster = MarkerCluster()
        for b in layer_data["buildings"][:500]:
            name = html_module.escape(b.get("name", "") or b.get("type", "building"))
            folium.CircleMarker(
                [b["lat"], b["lon"]], radius=3,
                color=LAYER_COLORS["buildings"], fill=True, fill_opacity=0.7,
                popup=f"<b>Building</b><br>{name}",
            ).add_to(cluster)
        cluster.add_to(fg)
        fg.add_to(m)

    # ── Roads ────────────────────────────────────────────────────────────────
    if "roads" in active_layers and layer_data.get("roads"):
        fg = folium.FeatureGroup(name="Roads", show=True)
        for r in layer_data["roads"][:500]:
            name = html_module.escape(r.get("name", "") or r.get("highway", "road"))
            folium.CircleMarker(
                [r["lat"], r["lon"]], radius=2,
                color=LAYER_COLORS["roads"], fill=True, fill_opacity=0.6,
                popup=f"<b>{html_module.escape(r.get('highway', 'road'))}</b><br>{name}",
            ).add_to(fg)
        fg.add_to(m)

    # ── Water ────────────────────────────────────────────────────────────────
    if "water" in active_layers and layer_data.get("water"):
        fg = folium.FeatureGroup(name="Water", show=True)
        for w in layer_data["water"][:300]:
            name = html_module.escape(w.get("name", "") or w.get("type", "water"))
            folium.CircleMarker(
                [w["lat"], w["lon"]], radius=4,
                color=LAYER_COLORS["water"], fill=True, fill_opacity=0.7,
                popup=f"<b>{html_module.escape(w.get('type', 'water'))}</b><br>{name}",
            ).add_to(fg)
        fg.add_to(m)

    # ── Vegetation ───────────────────────────────────────────────────────────
    if "vegetation" in active_layers and layer_data.get("vegetation"):
        fg = folium.FeatureGroup(name="Vegetation", show=True)
        for v in layer_data["vegetation"][:300]:
            name = html_module.escape(v.get("name", "") or v.get("type", "vegetation"))
            folium.CircleMarker(
                [v["lat"], v["lon"]], radius=4,
                color=LAYER_COLORS["vegetation"], fill=True, fill_opacity=0.6,
                popup=f"<b>{html_module.escape(v.get('type', 'vegetation'))}</b><br>{name}",
            ).add_to(fg)
        fg.add_to(m)

    # ── Terrain (elevation heatmap) ──────────────────────────────────────────
    if "terrain" in active_layers and layer_data.get("elevation", {}).get("points"):
        fg = folium.FeatureGroup(name="Terrain Elevation", show=True)
        heat_data = [
            [p["lat"], p["lon"], p["elevation"]]
            for p in layer_data["elevation"]["points"]
            if p.get("elevation") is not None
        ]
        if heat_data:
            HeatMap(
                heat_data,
                radius=25,
                blur=15,
                gradient={0.2: "#3b82f6", 0.4: "#22c55e", 0.6: "#f59e0b", 0.8: "#ef4444", 1.0: "#dc2626"},
            ).add_to(fg)
        fg.add_to(m)

    # ── Earthquakes ──────────────────────────────────────────────────────────
    if "earthquakes" in active_layers and layer_data.get("earthquakes", {}).get("features"):
        fg = folium.FeatureGroup(name="Earthquakes", show=True)
        for feat in layer_data["earthquakes"]["features"][:200]:
            props = feat.get("properties", {})
            coords = feat.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                mag = props.get("mag", 0) or 0
                place = html_module.escape(props.get("place", "Unknown"))
                radius = max(3, mag * 2.5)
                folium.CircleMarker(
                    [coords[1], coords[0]], radius=radius,
                    color=LAYER_COLORS["earthquakes"], fill=True, fill_opacity=0.7,
                    popup=f"<b>M{mag:.1f}</b><br>{place}",
                ).add_to(fg)
        fg.add_to(m)

    # ── Fires ────────────────────────────────────────────────────────────────
    if "fires" in active_layers and layer_data.get("fires"):
        fg = folium.FeatureGroup(name="Active Fires", show=True)
        for f in layer_data["fires"][:200]:
            try:
                flat = float(f.get("latitude", 0))
                flon = float(f.get("longitude", 0))
                frp = float(f.get("frp", 0))
                conf = html_module.escape(str(f.get("confidence", "N/A")))
                folium.CircleMarker(
                    [flat, flon], radius=max(4, min(frp / 10, 15)),
                    color=LAYER_COLORS["fires"], fill=True, fill_opacity=0.8,
                    popup=f"<b>Fire</b><br>FRP: {frp} MW<br>Confidence: {conf}",
                ).add_to(fg)
            except (ValueError, TypeError):
                continue
        fg.add_to(m)

    # ── Species (iNaturalist) ────────────────────────────────────────────────
    if "species" in active_layers and layer_data.get("species", {}).get("results"):
        fg = folium.FeatureGroup(name="Species", show=True)
        cluster = MarkerCluster()
        for obs in layer_data["species"]["results"][:200]:
            loc = obs.get("location", "")
            if loc:
                parts = loc.split(",")
                if len(parts) == 2:
                    try:
                        olat, olon = float(parts[0]), float(parts[1])
                        taxon = obs.get("taxon", {}) or {}
                        name = html_module.escape(taxon.get("preferred_common_name", taxon.get("name", "Unknown")))
                        iconic = html_module.escape(taxon.get("iconic_taxon_name", ""))
                        folium.CircleMarker(
                            [olat, olon], radius=4,
                            color=LAYER_COLORS["species"], fill=True, fill_opacity=0.7,
                            popup=f"<b>{name}</b><br>{iconic}",
                        ).add_to(cluster)
                    except (ValueError, TypeError):
                        continue
        cluster.add_to(fg)
        fg.add_to(m)

    # ── Flights ──────────────────────────────────────────────────────────────
    if "flights" in active_layers and layer_data.get("flights"):
        fg = folium.FeatureGroup(name="Live Flights", show=True)
        for fl in layer_data["flights"][:100]:
            callsign = html_module.escape(fl.get("callsign", "N/A"))
            alt = fl.get("altitude_m", 0)
            vel = fl.get("velocity_ms", 0)
            country = html_module.escape(fl.get("origin_country", ""))
            folium.Marker(
                [fl["lat"], fl["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="color:{LAYER_COLORS["flights"]};font-size:14px;" '
                         f'title="{callsign}">&#9992;</div>'
                ),
                popup=(
                    f"<b>{callsign}</b><br>"
                    f"Country: {country}<br>"
                    f"Alt: {alt:.0f} m<br>"
                    f"Speed: {vel:.0f} m/s"
                ),
            ).add_to(fg)
        fg.add_to(m)

    # ── Amenities ────────────────────────────────────────────────────────────
    if "amenities" in active_layers and layer_data.get("amenities"):
        fg = folium.FeatureGroup(name="Amenities", show=True)
        cluster = MarkerCluster()
        for a in layer_data["amenities"][:300]:
            name = html_module.escape(a.get("name", "") or a.get("type", "POI"))
            folium.CircleMarker(
                [a["lat"], a["lon"]], radius=3,
                color=LAYER_COLORS["amenities"], fill=True, fill_opacity=0.6,
                popup=f"<b>{html_module.escape(a.get('type', 'POI'))}</b><br>{name}",
            ).add_to(cluster)
        cluster.add_to(fg)
        fg.add_to(m)

    # ── Land Use ─────────────────────────────────────────────────────────────
    if "landuse" in active_layers and layer_data.get("landuse"):
        fg = folium.FeatureGroup(name="Land Use", show=True)
        for lu in layer_data["landuse"][:300]:
            name = html_module.escape(lu.get("name", "") or lu.get("type", ""))
            folium.CircleMarker(
                [lu["lat"], lu["lon"]], radius=5,
                color=LAYER_COLORS["landuse"], fill=True, fill_opacity=0.4,
                popup=f"<b>Land use: {html_module.escape(lu.get('type', ''))}</b><br>{name}",
            ).add_to(fg)
        fg.add_to(m)

    # ── Military ─────────────────────────────────────────────────────────────
    if "military" in active_layers and layer_data.get("military"):
        fg = folium.FeatureGroup(name="Military/Restricted", show=True)
        for mi in layer_data["military"][:100]:
            name = html_module.escape(mi.get("name", "") or mi.get("type", "military"))
            folium.CircleMarker(
                [mi["lat"], mi["lon"]], radius=8,
                color=LAYER_COLORS["military"], fill=True, fill_opacity=0.5,
                popup=f"<b>Military: {html_module.escape(mi.get('type', ''))}</b><br>{name}",
            ).add_to(fg)
        fg.add_to(m)

    # ── Heritage ─────────────────────────────────────────────────────────────
    if "heritage" in active_layers and layer_data.get("heritage"):
        fg = folium.FeatureGroup(name="Heritage Sites", show=True)
        for h in layer_data["heritage"][:200]:
            name = html_module.escape(h.get("name", "") or h.get("type", "heritage"))
            period = html_module.escape(h.get("period", ""))
            folium.CircleMarker(
                [h["lat"], h["lon"]], radius=5,
                color=LAYER_COLORS["heritage"], fill=True, fill_opacity=0.7,
                popup=f"<b>{html_module.escape(h.get('type', 'heritage'))}</b><br>{name}<br>{period}",
            ).add_to(fg)
        fg.add_to(m)

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def _auto_zoom(radius_km: float) -> int:
    """Choose an appropriate map zoom level for the given radius."""
    if radius_km <= 1:
        return 15
    elif radius_km <= 3:
        return 14
    elif radius_km <= 5:
        return 13
    elif radius_km <= 10:
        return 12
    elif radius_km <= 25:
        return 11
    elif radius_km <= 50:
        return 10
    elif radius_km <= 100:
        return 9
    return 8


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD RENDERING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _render_weather_card(weather: dict) -> None:
    """Render weather stats from Open-Meteo response."""
    current = weather.get("current", {})
    if not current:
        st.info("No weather data available for this zone.")
        return
    code = current.get("weather_code", 0)
    desc = WMO_CODES.get(code, "Unknown")
    cols = st.columns(5)
    cols[0].metric("Temperature", f"{current.get('temperature_2m', 'N/A')} C")
    cols[1].metric("Feels Like", f"{current.get('apparent_temperature', 'N/A')} C")
    cols[2].metric("Humidity", f"{current.get('relative_humidity_2m', 'N/A')}%")
    cols[3].metric("Wind", f"{current.get('wind_speed_10m', 'N/A')} km/h")
    cols[4].metric("Conditions", desc)

    cols2 = st.columns(3)
    cols2[0].metric("Precipitation", f"{current.get('precipitation', 0)} mm")
    cols2[1].metric("Pressure", f"{current.get('surface_pressure', 'N/A')} hPa")
    cols2[2].metric("Cloud Cover", f"{current.get('cloud_cover', 'N/A')}%")


def _render_air_quality_card(aq: dict) -> None:
    """Render air quality stats."""
    current = aq.get("current", {})
    if not current:
        st.info("No air quality data available.")
        return
    cols = st.columns(4)
    cols[0].metric("US AQI", current.get("us_aqi", "N/A"))
    cols[1].metric("PM2.5", f"{current.get('pm2_5', 'N/A')} ug/m3")
    cols[2].metric("PM10", f"{current.get('pm10', 'N/A')} ug/m3")
    cols[3].metric("Ozone", f"{current.get('ozone', 'N/A')} ug/m3")


def _render_elevation_card(elevation: dict) -> None:
    """Render elevation stats."""
    stats = elevation.get("stats", {})
    if not stats:
        st.info("No elevation data available.")
        return
    cols = st.columns(4)
    cols[0].metric("Min Elevation", f"{stats.get('min', 'N/A')} m")
    cols[1].metric("Max Elevation", f"{stats.get('max', 'N/A')} m")
    cols[2].metric("Avg Elevation", f"{stats.get('avg', 0):.0f} m")
    cols[3].metric("Elevation Range", f"{stats.get('range', 0):.0f} m")


def _render_soil_card(soil_raw: dict) -> None:
    """Render soil properties."""
    parsed = _parse_soil_data(soil_raw)
    if not parsed:
        st.info("No soil data available for this location.")
        return
    cols = st.columns(min(len(parsed), 4))
    for i, (key, val) in enumerate(parsed.items()):
        label = SOIL_LABELS.get(key, key)
        cols[i % len(cols)].metric(label, val)


def _render_biodiversity_card(species_data: dict, gbif_data: dict) -> None:
    """Render biodiversity summary."""
    inat_total = species_data.get("total_results", 0)
    gbif_count = gbif_data.get("count", 0)

    # Count unique species from iNaturalist
    species_set = set()
    iconic_counts: dict[str, int] = {}
    for obs in species_data.get("results", []):
        taxon = obs.get("taxon", {}) or {}
        species_name = taxon.get("name", "")
        if species_name:
            species_set.add(species_name)
        iconic = taxon.get("iconic_taxon_name", "Other")
        iconic_counts[iconic] = iconic_counts.get(iconic, 0) + 1

    cols = st.columns(4)
    cols[0].metric("iNaturalist Observations", inat_total)
    cols[1].metric("Unique Species (iNat)", len(species_set))
    cols[2].metric("GBIF Occurrences", gbif_count)
    cols[3].metric("Taxonomic Groups", len(iconic_counts))

    if iconic_counts:
        st.markdown("**Species by group:**")
        sorted_groups = sorted(iconic_counts.items(), key=lambda x: -x[1])
        group_cols = st.columns(min(len(sorted_groups), 6))
        for i, (group, count) in enumerate(sorted_groups[:6]):
            group_cols[i % len(group_cols)].metric(group, count)


def _render_infrastructure_card(buildings: list, roads: list, amenities: list) -> None:
    """Render infrastructure summary."""
    cols = st.columns(4)
    cols[0].metric("Buildings", len(buildings))
    cols[1].metric("Road Segments", len(roads))
    cols[2].metric("Amenities / POIs", len(amenities))

    # Estimate population from building count (rough: ~3.5 people per building)
    est_pop = int(len(buildings) * 3.5)
    cols[3].metric("Est. Population", f"~{est_pop:,}")

    # Road type breakdown
    if roads:
        road_types: dict[str, int] = {}
        for r in roads:
            rt = r.get("highway", "other")
            road_types[rt] = road_types.get(rt, 0) + 1
        sorted_types = sorted(road_types.items(), key=lambda x: -x[1])[:6]
        if sorted_types:
            st.markdown("**Road types:**")
            rcols = st.columns(min(len(sorted_types), 6))
            for i, (rt, count) in enumerate(sorted_types):
                rcols[i % len(rcols)].metric(rt.replace("_", " ").title(), count)


def _render_risk_card(earthquakes: dict, fires: list, military: list, water: list) -> None:
    """Render risk assessment summary."""
    eq_features = earthquakes.get("features", [])
    eq_count = len(eq_features)
    max_mag = 0.0
    if eq_features:
        mags = [f.get("properties", {}).get("mag", 0) or 0 for f in eq_features]
        max_mag = max(mags) if mags else 0.0

    cols = st.columns(5)
    cols[0].metric("Earthquakes (30d)", eq_count)
    cols[1].metric("Max Magnitude", f"{max_mag:.1f}" if max_mag > 0 else "None")
    cols[2].metric("Active Fires", len(fires))
    cols[3].metric("Military Zones", len(military))

    # Flood risk proxy: count of water features in zone
    flood_risk = "Low"
    if len(water) > 50:
        flood_risk = "High"
    elif len(water) > 20:
        flood_risk = "Moderate"
    cols[4].metric("Flood Risk Proxy", flood_risk)

    # Overall risk score
    risk_score = 0
    if eq_count > 10:
        risk_score += 3
    elif eq_count > 0:
        risk_score += 1
    if max_mag >= 5.0:
        risk_score += 3
    elif max_mag >= 3.0:
        risk_score += 1
    if len(fires) > 5:
        risk_score += 3
    elif len(fires) > 0:
        risk_score += 1
    if len(military) > 0:
        risk_score += 2
    if len(water) > 50:
        risk_score += 1

    risk_label = "Low"
    if risk_score >= 7:
        risk_label = "High"
    elif risk_score >= 4:
        risk_label = "Moderate"
    elif risk_score >= 2:
        risk_label = "Low-Moderate"

    st.markdown(f"**Overall Risk Assessment: {risk_label}** (score: {risk_score}/12)")


def _render_landuse_card(landuse: list) -> None:
    """Render land use breakdown."""
    if not landuse:
        st.info("No land use data available.")
        return
    lu_types: dict[str, int] = {}
    for lu in landuse:
        t = lu.get("type", "other")
        lu_types[t] = lu_types.get(t, 0) + 1
    sorted_lu = sorted(lu_types.items(), key=lambda x: -x[1])
    st.markdown("**Land use breakdown:**")
    cols = st.columns(min(len(sorted_lu), 5))
    for i, (t, c) in enumerate(sorted_lu[:10]):
        cols[i % len(cols)].metric(t.replace("_", " ").title(), c)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_export_csv(layer_data: dict, lat: float, lon: float, radius_km: float) -> str:
    """Build a combined CSV export of all layer data."""
    rows = []
    # Buildings
    for b in layer_data.get("buildings", []):
        rows.append({"layer": "building", "lat": b["lat"], "lon": b["lon"],
                      "type": b.get("type", ""), "name": b.get("name", "")})
    # Roads
    for r in layer_data.get("roads", []):
        rows.append({"layer": "road", "lat": r["lat"], "lon": r["lon"],
                      "type": r.get("highway", ""), "name": r.get("name", "")})
    # Water
    for w in layer_data.get("water", []):
        rows.append({"layer": "water", "lat": w["lat"], "lon": w["lon"],
                      "type": w.get("type", ""), "name": w.get("name", "")})
    # Vegetation
    for v in layer_data.get("vegetation", []):
        rows.append({"layer": "vegetation", "lat": v["lat"], "lon": v["lon"],
                      "type": v.get("type", ""), "name": v.get("name", "")})
    # Amenities
    for a in layer_data.get("amenities", []):
        rows.append({"layer": "amenity", "lat": a["lat"], "lon": a["lon"],
                      "type": a.get("type", ""), "name": a.get("name", "")})
    # Heritage
    for h in layer_data.get("heritage", []):
        rows.append({"layer": "heritage", "lat": h["lat"], "lon": h["lon"],
                      "type": h.get("type", ""), "name": h.get("name", "")})
    # Earthquakes
    for feat in layer_data.get("earthquakes", {}).get("features", []):
        coords = feat.get("geometry", {}).get("coordinates", [])
        props = feat.get("properties", {})
        if len(coords) >= 2:
            rows.append({"layer": "earthquake", "lat": coords[1], "lon": coords[0],
                          "type": f"M{props.get('mag', 0)}", "name": props.get("place", "")})
    # Fires
    for f in layer_data.get("fires", []):
        rows.append({"layer": "fire", "lat": f.get("latitude", ""), "lon": f.get("longitude", ""),
                      "type": "hotspot", "name": f"FRP:{f.get('frp', '')}"})
    # Species
    for obs in layer_data.get("species", {}).get("results", []):
        loc = obs.get("location", "")
        if loc and "," in loc:
            parts = loc.split(",")
            if len(parts) >= 2:
                try:
                    taxon = obs.get("taxon", {}) or {}
                    rows.append({"layer": "species", "lat": float(parts[0]), "lon": float(parts[1]),
                                  "type": taxon.get("iconic_taxon_name", ""),
                                  "name": taxon.get("preferred_common_name", taxon.get("name", ""))})
                except (ValueError, TypeError):
                    continue
    # Flights
    for fl in layer_data.get("flights", []):
        rows.append({"layer": "flight", "lat": fl["lat"], "lon": fl["lon"],
                      "type": "aircraft", "name": fl.get("callsign", "")})

    if not rows:
        rows.append({"layer": "zone_center", "lat": lat, "lon": lon,
                      "type": "center", "name": f"r={radius_km}km"})
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def _build_export_geojson(layer_data: dict, lat: float, lon: float, radius_km: float) -> str:
    """Build a GeoJSON FeatureCollection from all layer data."""
    features = []

    # Zone boundary
    features.append({
        "type": "Feature",
        "properties": {"layer": "zone", "name": "Analysis Zone", "radius_km": radius_km},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    })

    def _point_feature(layer: str, la: float, lo: float, props: dict) -> dict:
        props["layer"] = layer
        return {
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "Point", "coordinates": [lo, la]},
        }

    for b in layer_data.get("buildings", []):
        features.append(_point_feature("building", b["lat"], b["lon"],
                                        {"type": b.get("type", ""), "name": b.get("name", "")}))
    for r in layer_data.get("roads", []):
        features.append(_point_feature("road", r["lat"], r["lon"],
                                        {"type": r.get("highway", ""), "name": r.get("name", "")}))
    for w in layer_data.get("water", []):
        features.append(_point_feature("water", w["lat"], w["lon"],
                                        {"type": w.get("type", ""), "name": w.get("name", "")}))
    for v in layer_data.get("vegetation", []):
        features.append(_point_feature("vegetation", v["lat"], v["lon"],
                                        {"type": v.get("type", ""), "name": v.get("name", "")}))
    for a in layer_data.get("amenities", []):
        features.append(_point_feature("amenity", a["lat"], a["lon"],
                                        {"type": a.get("type", ""), "name": a.get("name", "")}))
    for h in layer_data.get("heritage", []):
        features.append(_point_feature("heritage", h["lat"], h["lon"],
                                        {"type": h.get("type", ""), "name": h.get("name", "")}))

    for feat in layer_data.get("earthquakes", {}).get("features", []):
        features.append(feat)  # already GeoJSON

    for f in layer_data.get("fires", []):
        try:
            features.append(_point_feature("fire", float(f.get("latitude", 0)),
                                            float(f.get("longitude", 0)),
                                            {"frp": f.get("frp", ""), "confidence": f.get("confidence", "")}))
        except (ValueError, TypeError):
            continue

    for obs in layer_data.get("species", {}).get("results", []):
        loc = obs.get("location", "")
        if loc and "," in loc:
            parts = loc.split(",")
            if len(parts) < 2:
                continue
            try:
                taxon = obs.get("taxon", {}) or {}
                features.append(_point_feature("species", float(parts[0]), float(parts[1]),
                                                {"name": taxon.get("name", ""),
                                                 "common_name": taxon.get("preferred_common_name", ""),
                                                 "group": taxon.get("iconic_taxon_name", "")}))
            except (ValueError, TypeError):
                continue

    for fl in layer_data.get("flights", []):
        features.append(_point_feature("flight", fl["lat"], fl["lon"],
                                        {"callsign": fl.get("callsign", ""),
                                         "altitude_m": fl.get("altitude_m", 0),
                                         "country": fl.get("origin_country", "")}))

    geojson = {"type": "FeatureCollection", "features": features}
    return json.dumps(geojson, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# IDW ESTIMATION HELPER (used when direct data is sparse)
# ═══════════════════════════════════════════════════════════════════════════════

def _idw_estimate_from_observations(
    observations: list[dict],
    target_lat: float,
    target_lon: float,
    value_key: str,
    power: float = 2.0,
) -> float | None:
    """Use IDW to estimate a value at target from nearby observations.

    Each observation dict must have 'lat', 'lon', and the value_key field.
    Returns estimated value or None if insufficient data.
    """
    points = []
    values = []
    for obs in observations:
        try:
            pt_lat = float(obs.get("lat", 0))
            pt_lon = float(obs.get("lon", 0))
            val = float(obs.get(value_key, 0))
            points.append([pt_lat, pt_lon])
            values.append(val)
        except (ValueError, TypeError):
            continue
    if len(points) < 2:
        return None
    return idw_interpolate(
        np.array(points),
        np.array(values),
        np.array([target_lat, target_lon]),
        power=power,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TAB RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def render_zone_intelligence_tab() -> None:
    """Render the Zone Intelligence Aggregator tab."""

    # ── Glass header ─────────────────────────────────────────────────────────
    st.markdown(
        '<div class="tab-header cyan">'
        "<h4>\U0001f6f0\ufe0f Zone Intelligence Aggregator</h4>"
        "<p>Select any area &mdash; see ALL data layers: terrain, weather, "
        "species, infrastructure, risks &amp; real-time feeds</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Sidebar-style controls ───────────────────────────────────────────────
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 1])

    with ctrl_col1:
        preset = st.selectbox(
            "Quick Location",
            list(ZONE_PRESETS.keys()),
            key="zi_preset",
        )
        if preset != "Custom" and ZONE_PRESETS[preset]:
            default_lat = ZONE_PRESETS[preset]["lat"]
            default_lon = ZONE_PRESETS[preset]["lon"]
        else:
            default_lat = 41.9028
            default_lon = 12.4964

    with ctrl_col2:
        lat = st.number_input("Latitude", value=default_lat, min_value=-90.0,
                              max_value=90.0, step=0.01, format="%.4f", key="zi_lat")
        lon = st.number_input("Longitude", value=default_lon, min_value=-180.0,
                              max_value=180.0, step=0.01, format="%.4f", key="zi_lon")

    with ctrl_col3:
        radius_km = st.slider("Radius (km)", 1, 100, 10, key="zi_radius")
        mode = st.selectbox(
            "Analysis Mode",
            list(ANALYSIS_MODES.keys()),
            key="zi_mode",
        )

    # ── Layer toggles ────────────────────────────────────────────────────────
    mode_info = ANALYSIS_MODES[mode]
    st.markdown(f"**Mode:** {mode} &mdash; *{mode_info['desc']}*")

    all_layer_names = list(LAYER_COLORS.keys())

    if mode == "Custom Analysis":
        st.markdown("Select layers to include:")
        layer_cols = st.columns(5)
        active_layers = []
        for i, lname in enumerate(all_layer_names):
            with layer_cols[i % 5]:
                if st.checkbox(lname.replace("_", " ").title(), value=False, key=f"zi_layer_{lname}"):
                    active_layers.append(lname)
    else:
        active_layers = mode_info["layers"]
        # Show active layers as chips
        chips_html = " ".join(
            f'<span style="display:inline-block;padding:2px 10px;margin:2px;'
            f'border-radius:12px;background:{LAYER_COLORS.get(l, "#333")};'
            f'color:#fff;font-size:12px;">{l.replace("_", " ").title()}</span>'
            for l in active_layers
        )
        st.markdown(chips_html, unsafe_allow_html=True)

    # ── Run analysis ─────────────────────────────────────────────────────────
    run_btn = st.button("Analyze Zone", type="primary", use_container_width=True, key="zi_run")

    if not run_btn:
        st.info("Configure the zone parameters above and click **Analyze Zone** to begin.")
        # Show an empty base map
        m = folium.Map(location=[lat, lon], zoom_start=_auto_zoom(radius_km), tiles="CartoDB dark_matter")
        folium.Circle(
            location=[lat, lon], radius=radius_km * 1000,
            color="#06b6d4", fill=True, fill_opacity=0.05, weight=2, dash_array="8 4",
        ).add_to(m)
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html='<div style="font-size:18px;">&#x1F3AF;</div>'),
        ).add_to(m)
        st_html(m._repr_html_(), height=600)
        return

    # ── Fetch all data ───────────────────────────────────────────────────────
    bbox = _compute_bbox(lat, lon, radius_km)
    layer_data: dict[str, Any] = {}

    progress = st.progress(0, text="Initializing zone analysis...")
    total_steps = len(active_layers) + 3  # +3 for geocoding, weather, air quality
    step = 0

    # Always fetch place name, weather, air quality
    progress.progress(step / total_steps, text="Reverse geocoding location...")
    place = fetch_place_name(lat, lon)
    step += 1

    progress.progress(step / total_steps, text="Fetching weather data...")
    weather = fetch_weather(lat, lon)
    layer_data["weather_data"] = weather
    step += 1

    progress.progress(step / total_steps, text="Fetching air quality...")
    aq = fetch_air_quality(lat, lon)
    layer_data["air_quality"] = aq
    step += 1

    # Fetch layer-specific data
    if "buildings" in active_layers:
        progress.progress(step / total_steps, text="Fetching buildings...")
        layer_data["buildings"] = fetch_osm_buildings(bbox)
        step += 1

    if "roads" in active_layers:
        progress.progress(step / total_steps, text="Fetching roads...")
        layer_data["roads"] = fetch_osm_roads(bbox)
        step += 1

    if "water" in active_layers:
        progress.progress(step / total_steps, text="Fetching water features...")
        layer_data["water"] = fetch_osm_water(bbox)
        step += 1

    if "vegetation" in active_layers:
        progress.progress(step / total_steps, text="Fetching vegetation...")
        layer_data["vegetation"] = fetch_osm_vegetation(bbox)
        step += 1

    if "terrain" in active_layers:
        progress.progress(step / total_steps, text="Fetching elevation data...")
        layer_data["elevation"] = fetch_elevation_grid(lat, lon, radius_km, grid_size=5)
        step += 1

    if "earthquakes" in active_layers:
        progress.progress(step / total_steps, text="Fetching earthquake data...")
        layer_data["earthquakes"] = fetch_earthquakes(lat, lon, radius_km)
        step += 1

    if "fires" in active_layers:
        progress.progress(step / total_steps, text="Fetching fire hotspots...")
        layer_data["fires"] = fetch_fires(lat, lon, radius_km)
        step += 1

    if "species" in active_layers:
        progress.progress(step / total_steps, text="Fetching species observations...")
        layer_data["species"] = fetch_species(lat, lon, radius_km)
        layer_data["species_counts"] = fetch_species_counts(lat, lon, radius_km)
        step += 1

    if "flights" in active_layers:
        progress.progress(step / total_steps, text="Fetching live flights...")
        layer_data["flights"] = fetch_flights(lat, lon, radius_km)
        step += 1

    if "amenities" in active_layers:
        progress.progress(step / total_steps, text="Fetching amenities...")
        layer_data["amenities"] = fetch_osm_amenities(bbox)
        step += 1

    if "landuse" in active_layers:
        progress.progress(step / total_steps, text="Fetching land use data...")
        layer_data["landuse"] = fetch_osm_landuse(bbox)
        step += 1

    if "military" in active_layers:
        progress.progress(step / total_steps, text="Fetching military zones...")
        layer_data["military"] = fetch_osm_military(bbox)
        step += 1

    if "heritage" in active_layers:
        progress.progress(step / total_steps, text="Fetching heritage sites...")
        layer_data["heritage"] = fetch_osm_heritage(bbox)
        step += 1

    if "soil" in active_layers:
        progress.progress(step / total_steps, text="Fetching soil data...")
        layer_data["soil"] = fetch_soil(lat, lon)
        step += 1

    # GBIF (biodiversity complement)
    if "species" in active_layers:
        layer_data["gbif"] = fetch_gbif(lat, lon, radius_km)

    progress.progress(1.0, text="Analysis complete!")

    # ── Zone header ──────────────────────────────────────────────────────────
    place_name = place.get("display_name", "Unknown Location")
    st.markdown(
        f"### Zone Report: {html_module.escape(place_name)}\n"
        f"**Centre:** {lat:.4f}, {lon:.4f} &nbsp;|&nbsp; "
        f"**Radius:** {radius_km} km &nbsp;|&nbsp; "
        f"**Mode:** {mode}",
        unsafe_allow_html=True,
    )

    # ── Summary statistics row ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Quick Stats")
    summary_cols = st.columns(6)
    summary_cols[0].metric("Buildings", len(layer_data.get("buildings", [])))
    summary_cols[1].metric("Roads", len(layer_data.get("roads", [])))
    summary_cols[2].metric("Water Features", len(layer_data.get("water", [])))

    sp_total = layer_data.get("species", {}).get("total_results", 0)
    summary_cols[3].metric("Species Obs.", sp_total)

    eq_count = len(layer_data.get("earthquakes", {}).get("features", []))
    summary_cols[4].metric("Earthquakes (30d)", eq_count)
    summary_cols[5].metric("Active Fires", len(layer_data.get("fires", [])))

    # ── Map ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Intelligence Map")
    zone_map = _build_zone_map(lat, lon, radius_km, layer_data, active_layers)
    st_html(zone_map._repr_html_(), height=600)

    # ── Detailed dashboard sections ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Detailed Analysis")

    # Weather & Air Quality
    with st.expander("Weather & Air Quality", expanded=True):
        st.markdown("##### Current Weather")
        _render_weather_card(weather)
        st.markdown("##### Air Quality")
        _render_air_quality_card(aq)

    # Terrain / Elevation
    if "terrain" in active_layers and layer_data.get("elevation"):
        with st.expander("Terrain & Elevation", expanded=True):
            _render_elevation_card(layer_data["elevation"])

            # IDW interpolation demo: estimate elevation at centre if we have grid
            elev_pts = layer_data["elevation"].get("points", [])
            if len(elev_pts) >= 3:
                est = _idw_estimate_from_observations(elev_pts, lat, lon, "elevation")
                if est is not None:
                    st.metric("IDW Estimated Elevation at Centre", f"{est:.1f} m")

            # Show elevation data table
            if elev_pts:
                df_elev = pd.DataFrame(elev_pts)
                st.dataframe(df_elev, use_container_width=True)

    # Biodiversity
    if "species" in active_layers:
        with st.expander("Biodiversity", expanded=True):
            _render_biodiversity_card(
                layer_data.get("species", {}),
                layer_data.get("gbif", {}),
            )
            # Species data table
            obs_rows = []
            for obs in layer_data.get("species", {}).get("results", []):
                taxon = obs.get("taxon", {}) or {}
                obs_rows.append({
                    "Species": taxon.get("name", ""),
                    "Common Name": taxon.get("preferred_common_name", ""),
                    "Group": taxon.get("iconic_taxon_name", ""),
                    "Observed": obs.get("observed_on", ""),
                    "Quality": obs.get("quality_grade", ""),
                })
            if obs_rows:
                st.markdown("**Recent Observations:**")
                st.dataframe(pd.DataFrame(obs_rows), use_container_width=True)

    # Infrastructure
    if any(l in active_layers for l in ["buildings", "roads", "amenities"]):
        with st.expander("Infrastructure", expanded=True):
            _render_infrastructure_card(
                layer_data.get("buildings", []),
                layer_data.get("roads", []),
                layer_data.get("amenities", []),
            )

    # Risk Assessment
    if any(l in active_layers for l in ["earthquakes", "fires", "military"]):
        with st.expander("Risk Assessment", expanded=True):
            _render_risk_card(
                layer_data.get("earthquakes", {}),
                layer_data.get("fires", []),
                layer_data.get("military", []),
                layer_data.get("water", []),
            )

    # Soil Data
    if "soil" in active_layers and layer_data.get("soil"):
        with st.expander("Soil Composition", expanded=True):
            _render_soil_card(layer_data["soil"])

    # Land Use
    if "landuse" in active_layers and layer_data.get("landuse"):
        with st.expander("Land Use", expanded=True):
            _render_landuse_card(layer_data["landuse"])
            if layer_data["landuse"]:
                df_lu = pd.DataFrame(layer_data["landuse"])
                st.dataframe(df_lu, use_container_width=True)

    # Heritage
    if "heritage" in active_layers and layer_data.get("heritage"):
        with st.expander("Heritage & Archaeological Sites", expanded=True):
            st.metric("Heritage Sites Found", len(layer_data["heritage"]))
            df_h = pd.DataFrame(layer_data["heritage"])
            st.dataframe(df_h, use_container_width=True)

    # Water Features
    if "water" in active_layers and layer_data.get("water"):
        with st.expander("Water Features", expanded=True):
            st.metric("Water Features", len(layer_data["water"]))
            # Type breakdown
            wt: dict[str, int] = {}
            for w in layer_data["water"]:
                t = w.get("type", "other")
                wt[t] = wt.get(t, 0) + 1
            sorted_wt = sorted(wt.items(), key=lambda x: -x[1])[:6]
            if sorted_wt:
                wcols = st.columns(min(len(sorted_wt), 6))
                for i, (t, c) in enumerate(sorted_wt):
                    wcols[i % len(wcols)].metric(t.title(), c)
            df_w = pd.DataFrame(layer_data["water"])
            st.dataframe(df_w, use_container_width=True)

    # Vegetation
    if "vegetation" in active_layers and layer_data.get("vegetation"):
        with st.expander("Vegetation", expanded=True):
            st.metric("Vegetation Features", len(layer_data["vegetation"]))
            df_v = pd.DataFrame(layer_data["vegetation"])
            st.dataframe(df_v, use_container_width=True)

    # Flights
    if "flights" in active_layers and layer_data.get("flights"):
        with st.expander("Live Flights", expanded=True):
            st.metric("Aircraft in Zone", len(layer_data["flights"]))
            df_fl = pd.DataFrame(layer_data["flights"])
            st.dataframe(df_fl, use_container_width=True)

    # Military
    if "military" in active_layers and layer_data.get("military"):
        with st.expander("Military / Restricted Zones", expanded=True):
            st.metric("Military Features", len(layer_data["military"]))
            df_m = pd.DataFrame(layer_data["military"])
            st.dataframe(df_m, use_container_width=True)

    # ── Export section ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Export Data")
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        csv_data = _build_export_csv(layer_data, lat, lon, radius_km)
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"zone_intel_{lat:.2f}_{lon:.2f}_{radius_km}km.csv",
            mime="text/csv",
            use_container_width=True,
            key="zi_csv_dl",
        )

    with exp_col2:
        geojson_data = _build_export_geojson(layer_data, lat, lon, radius_km)
        st.download_button(
            "Download GeoJSON",
            data=geojson_data,
            file_name=f"zone_intel_{lat:.2f}_{lon:.2f}_{radius_km}km.geojson",
            mime="application/json",
            use_container_width=True,
            key="zi_geojson_dl",
        )

    # ── Raw data JSON (collapsed) ────────────────────────────────────────────
    with st.expander("Raw JSON Data (Debug)", expanded=False):
        # Build a serializable summary (skip large nested objects)
        raw_summary = {}
        for k, v in layer_data.items():
            if isinstance(v, list):
                raw_summary[k] = f"[{len(v)} items]"
            elif isinstance(v, dict):
                if "features" in v:
                    raw_summary[k] = f"[{len(v.get('features', []))} features]"
                elif "results" in v:
                    raw_summary[k] = f"[{len(v.get('results', []))} results]"
                else:
                    raw_summary[k] = {kk: str(vv)[:100] for kk, vv in v.items()}
            else:
                raw_summary[k] = str(v)[:200]
        st.json(raw_summary)
