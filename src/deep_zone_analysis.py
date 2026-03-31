"""
Deep Zone Analysis module for TerraScout AI.
Performs comprehensive multi-source analysis of any geographic point using
statistical interpolation and data triangulation from free APIs:
  - Open-Elevation / Open Topo Data (terrain)
  - ISRIC SoilGrids (soil composition)
  - Open-Meteo (climate & weather)
  - iNaturalist + GBIF (biodiversity)
  - Overpass API (water, land use, infrastructure, protected areas)
  - Macrostrat (geology)
  - USGS Earthquakes (seismic risk)
All free, no API key required.
"""

import io
import json
import logging
import math
import html as html_module
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

OPEN_ELEVATION_API = "https://api.open-elevation.com/api/v1/lookup"
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"
SOILGRIDS_API = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
CLIMATE_API = "https://climate-api.open-meteo.com/v1/climate"
INAT_API = "https://api.inaturalist.org/v1"
GBIF_API = "https://api.gbif.org/v1/occurrence/search"
MACROSTRAT_API = "https://macrostrat.org/api/v2"
USGS_EQ_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Soil property metadata
SOIL_PROPERTIES = {
    "clay": {"name": "Clay", "unit": "%", "color": "#f59e0b", "divisor": 10},
    "sand": {"name": "Sand", "unit": "%", "color": "#ef4444", "divisor": 10},
    "silt": {"name": "Silt", "unit": "%", "color": "#8b5cf6", "divisor": 10},
    "soc": {"name": "Organic Carbon", "unit": "g/kg", "color": "#10b981", "divisor": 10},
    "phh2o": {"name": "pH (H2O)", "unit": "pH*10", "color": "#06b6d4", "divisor": 10},
    "nitrogen": {"name": "Nitrogen", "unit": "g/kg", "color": "#14b8a6", "divisor": 100},
    "cec": {"name": "CEC", "unit": "cmol/kg", "color": "#f97316", "divisor": 10},
}

DEPTH_LABELS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]

RISK_COLORS = {
    "Seismic": "#ef4444",
    "Flood": "#3b82f6",
    "Fire": "#f97316",
    "Landslide": "#a855f7",
    "Pollution": "#64748b",
}

LANDUSE_COLORS = {
    "residential": "#f59e0b",
    "commercial": "#8b5cf6",
    "industrial": "#ef4444",
    "farmland": "#10b981",
    "forest": "#059669",
    "meadow": "#84cc16",
    "retail": "#ec4899",
    "construction": "#f97316",
    "military": "#dc2626",
    "cemetery": "#64748b",
    "quarry": "#78716c",
    "vineyard": "#a855f7",
    "orchard": "#16a34a",
    "park": "#22c55e",
    "water": "#3b82f6",
    "other": "#8b97b0",
}

KOPPEN_CLASSES = {
    "Af": "Tropical Rainforest",
    "Am": "Tropical Monsoon",
    "Aw": "Tropical Savanna",
    "BWh": "Hot Desert",
    "BWk": "Cold Desert",
    "BSh": "Hot Semi-Arid",
    "BSk": "Cold Semi-Arid",
    "Csa": "Hot-Summer Mediterranean",
    "Csb": "Warm-Summer Mediterranean",
    "Cwa": "Humid Subtropical (dry winter)",
    "Cwb": "Subtropical Highland",
    "Cfa": "Humid Subtropical",
    "Cfb": "Oceanic",
    "Cfc": "Subpolar Oceanic",
    "Dsa": "Hot-Summer Continental (dry)",
    "Dsb": "Warm-Summer Continental (dry)",
    "Dwa": "Hot-Summer Continental (monsoon)",
    "Dwb": "Warm-Summer Continental (monsoon)",
    "Dfa": "Hot-Summer Continental",
    "Dfb": "Warm-Summer Continental",
    "Dfc": "Subarctic",
    "Dfd": "Extremely Cold Subarctic",
    "ET": "Tundra",
    "EF": "Ice Cap",
}

ANALYSIS_PRESETS = {
    "Custom": None,
    "Rome, Italy": {"lat": 41.90, "lon": 12.50},
    "Grand Canyon, USA": {"lat": 36.11, "lon": -112.11},
    "Amazon Basin, Brazil": {"lat": -3.12, "lon": -60.02},
    "Swiss Alps - Jungfrau": {"lat": 46.56, "lon": 7.97},
    "Sahara Desert, Algeria": {"lat": 27.0, "lon": 2.0},
    "Tokyo, Japan": {"lat": 35.68, "lon": 139.69},
    "Iceland - Thingvellir Rift": {"lat": 64.26, "lon": -21.13},
    "Nile Delta, Egypt": {"lat": 30.9, "lon": 31.2},
    "Lake Garda, Italy": {"lat": 45.60, "lon": 10.65},
    "Yellowstone, Wyoming": {"lat": 44.43, "lon": -110.59},
    "Mount Etna, Sicily": {"lat": 37.75, "lon": 14.99},
    "Great Barrier Reef, Australia": {"lat": -18.29, "lon": 147.70},
    "Mount Kilimanjaro, Tanzania": {"lat": -3.07, "lon": 37.35},
    "Fjords of Norway": {"lat": 61.20, "lon": 6.75},
    "Dead Sea, Israel": {"lat": 31.50, "lon": 35.50},
}


# ═══════════════════════════════════════════════════════════════════════════════
# IDW INTERPOLATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in km between two points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def idw_interpolate(known_lats: list, known_lons: list, known_values: list,
                    target_lat: float, target_lon: float, power: float = 2.0) -> float:
    """
    Inverse Distance Weighting interpolation.
    Estimates a value at target_lat/target_lon from surrounding known data points.
    """
    if not known_lats or not known_values:
        return 0.0
    arr_vals = np.array(known_values, dtype=float)
    distances = np.array([
        haversine_distance(target_lat, target_lon, lat, lon)
        for lat, lon in zip(known_lats, known_lons)
    ])
    mask = distances > 0.001  # avoid division by zero
    if not np.any(mask):
        return float(np.mean(arr_vals))
    weights = 1.0 / (distances[mask] ** power)
    return float(np.sum(weights * arr_vals[mask]) / np.sum(weights))


def estimate_water_table_depth(springs: list, wells: list, elevations: dict,
                               target_lat: float, target_lon: float,
                               target_elev: float) -> float | None:
    """
    Estimate water table depth from nearby water features.
    Springs indicate water table at surface; wells have approximate depth.
    Uses elevation difference + IDW to produce an estimate in meters.
    """
    known_lats, known_lons, known_depths = [], [], []

    for s in springs:
        slat = s.get("lat", 0)
        slon = s.get("lon", 0)
        dist = haversine_distance(target_lat, target_lon, slat, slon)
        if dist < 0.01:
            return 0.0  # spring at the point = water at surface
        s_elev = elevations.get(f"{slat:.4f},{slon:.4f}", target_elev)
        depth = max(0.0, target_elev - s_elev) + dist * 0.5
        known_lats.append(slat)
        known_lons.append(slon)
        known_depths.append(depth)

    for w in wells:
        wlat = w.get("lat", 0)
        wlon = w.get("lon", 0)
        # Wells typically reach 10-50m; use tag depth if available
        well_depth = float(w.get("depth", 15))
        known_lats.append(wlat)
        known_lons.append(wlon)
        known_depths.append(well_depth)

    if not known_lats:
        return None
    return idw_interpolate(known_lats, known_lons, known_depths,
                           target_lat, target_lon, power=2)


def classify_koppen(temp_avg_c: float, precip_annual_mm: float,
                    temp_max_c: float, temp_min_c: float,
                    precip_driest_mm: float) -> str:
    """
    Simplified Koppen climate classification from temperature & precipitation.
    Returns the Koppen code string.
    """
    threshold = 20.0 * temp_avg_c + 280.0
    # Group E - Polar
    if temp_max_c < 10.0:
        if temp_max_c < 0.0:
            return "EF"
        return "ET"
    # Group B - Arid
    if precip_annual_mm < threshold:
        if precip_annual_mm < threshold / 2.0:
            if temp_avg_c >= 18.0:
                return "BWh"
            return "BWk"
        else:
            if temp_avg_c >= 18.0:
                return "BSh"
            return "BSk"
    # Group A - Tropical
    if temp_min_c >= 18.0:
        if precip_driest_mm >= 60.0:
            return "Af"
        if precip_annual_mm >= 25.0 * (100.0 - precip_driest_mm):
            return "Am"
        return "Aw"
    # Group C - Temperate vs D - Continental
    if temp_min_c >= -3.0:
        # C group
        if precip_driest_mm < 30.0:
            if temp_max_c >= 22.0:
                return "Csa"
            return "Csb"
        if temp_max_c >= 22.0:
            return "Cfa"
        if sum(1 for t in [temp_max_c, temp_avg_c, temp_min_c] if t > 10) >= 2:
            return "Cfb"
        return "Cfc"
    else:
        # D group
        if precip_driest_mm < 30.0:
            if temp_max_c >= 22.0:
                return "Dsa"
            return "Dsb"
        if temp_max_c >= 22.0:
            return "Dfa"
        if temp_min_c < -38.0:
            return "Dfd"
        return "Dfb"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING FUNCTIONS (ALL CACHED)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_elevation_grid(lat: float, lon: float, radius_deg: float = 0.05,
                         grid_size: int = 9) -> dict:
    """
    Fetch elevation data for a grid of points around the target.
    Returns a dict with 'center', 'grid', and 'profiles' (N-S, E-W).
    """
    try:
        # Build locations string: center + grid
        points = []
        lats_list, lons_list = [], []
        half = grid_size // 2
        for i in range(-half, half + 1):
            for j in range(-half, half + 1):
                plat = lat + i * radius_deg / half if half > 0 else lat
                plon = lon + j * radius_deg / half if half > 0 else lon
                points.append(f"{plat:.5f},{plon:.5f}")
                lats_list.append(plat)
                lons_list.append(plon)

        # Open Topo Data allows max 100 locations per request
        locations_str = "|".join(points[:100])
        resp = requests.get(OPEN_TOPO_API,
                            params={"locations": locations_str}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        elevations = []
        for r in results:
            e = r.get("elevation")
            elevations.append(float(e) if e is not None else 0.0)

        center_idx = len(elevations) // 2
        center_elev = elevations[center_idx] if elevations else 0.0

        # Extract N-S profile (column at center)
        ns_profile, ew_profile = [], []
        for i in range(grid_size):
            idx_ns = i * grid_size + half
            idx_ew = half * grid_size + i
            if idx_ns < len(elevations):
                ns_profile.append({
                    "lat": lats_list[idx_ns], "lon": lons_list[idx_ns],
                    "elevation": elevations[idx_ns]
                })
            if idx_ew < len(elevations):
                ew_profile.append({
                    "lat": lats_list[idx_ew], "lon": lons_list[idx_ew],
                    "elevation": elevations[idx_ew]
                })

        elev_map = {}
        for idx, r in enumerate(results):
            e = r.get("elevation")
            elev_map[f"{lats_list[idx]:.4f},{lons_list[idx]:.4f}"] = (
                float(e) if e is not None else 0.0
            )

        return {
            "center_elevation": center_elev,
            "min_elevation": min(elevations) if elevations else 0,
            "max_elevation": max(elevations) if elevations else 0,
            "avg_elevation": float(np.mean(elevations)) if elevations else 0,
            "ns_profile": ns_profile,
            "ew_profile": ew_profile,
            "grid_lats": lats_list,
            "grid_lons": lons_list,
            "grid_elevations": elevations,
            "elevation_map": elev_map,
        }
    except Exception as e:
        logger.warning(f"Elevation grid fetch error: {e}")
        return {
            "center_elevation": 0, "min_elevation": 0, "max_elevation": 0,
            "avg_elevation": 0, "ns_profile": [], "ew_profile": [],
            "grid_lats": [], "grid_lons": [], "grid_elevations": [],
            "elevation_map": {},
        }


@st.cache_data(ttl=3600)
def fetch_soil_data(lat: float, lon: float) -> dict:
    """Fetch soil composition from ISRIC SoilGrids."""
    try:
        params = {
            "lon": lon,
            "lat": lat,
            "property": ["clay", "sand", "silt", "soc", "phh2o", "nitrogen", "cec"],
            "depth": DEPTH_LABELS,
            "value": "mean",
        }
        resp = requests.get(SOILGRIDS_API, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"SoilGrids error: {e}")
        return {}


@st.cache_data(ttl=3600)
def fetch_weather_data(lat: float, lon: float) -> dict:
    """Fetch current + forecast weather from Open-Meteo."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,"
                       "wind_speed_10m,surface_pressure,cloud_cover",
            "hourly": "temperature_2m,precipitation",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
            "forecast_days": 7,
        }
        resp = requests.get(OPEN_METEO_API, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Open-Meteo error: {e}")
        return {}


@st.cache_data(ttl=3600)
def fetch_climate_data(lat: float, lon: float) -> dict:
    """Fetch historical climate normals from Open-Meteo Climate API."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": "1950-01-01",
            "end_date": "2050-12-31",
            "models": "EC_Earth3P_HR",
            "daily": "temperature_2m_mean,precipitation_sum",
        }
        resp = requests.get(CLIMATE_API, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Climate API error: {e}")
        return {}


@st.cache_data(ttl=3600)
def fetch_biodiversity(lat: float, lon: float, radius_km: int = 10) -> dict:
    """Fetch species observations from iNaturalist."""
    try:
        params = {
            "lat": lat,
            "lng": lon,
            "radius": radius_km,
            "per_page": 200,
            "order": "desc",
            "order_by": "created_at",
            "quality_grade": "research",
        }
        resp = requests.get(f"{INAT_API}/observations", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"iNaturalist error: {e}")
        return {"total_results": 0, "results": []}


@st.cache_data(ttl=3600)
def fetch_gbif_occurrences(lat: float, lon: float, radius_m: int = 10000) -> dict:
    """Fetch species occurrences from GBIF."""
    try:
        params = {
            "decimalLatitude": f"{lat - 0.1},{lat + 0.1}",
            "decimalLongitude": f"{lon - 0.1},{lon + 0.1}",
            "limit": 300,
            "hasCoordinate": "true",
        }
        resp = requests.get(GBIF_API, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"GBIF error: {e}")
        return {"count": 0, "results": []}


@st.cache_data(ttl=3600)
def fetch_water_features(lat: float, lon: float, radius: int = 5000) -> dict:
    """Fetch water features from Overpass API."""
    query = f"""[out:json][timeout:25];
(
  node["natural"="spring"](around:{radius},{lat},{lon});
  node["man_made"="water_well"](around:{radius},{lat},{lon});
  way["waterway"](around:{radius},{lat},{lon});
  way["natural"="water"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=3600)
def fetch_landuse_infrastructure(lat: float, lon: float, radius: int = 3000) -> dict:
    """Fetch land use and infrastructure from Overpass API."""
    query = f"""[out:json][timeout:25];
(
  way["building"](around:{radius},{lat},{lon});
  way["landuse"](around:{radius},{lat},{lon});
  way["highway"](around:{radius},{lat},{lon});
  way["leisure"="park"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=3600)
def fetch_protected_areas(lat: float, lon: float, radius: int = 10000) -> dict:
    """Fetch protected areas / nature reserves from Overpass API."""
    query = f"""[out:json][timeout:25];
(
  node["boundary"="protected_area"](around:{radius},{lat},{lon});
  way["boundary"="protected_area"](around:{radius},{lat},{lon});
  relation["boundary"="protected_area"](around:{radius},{lat},{lon});
  way["leisure"="nature_reserve"](around:{radius},{lat},{lon});
  relation["leisure"="nature_reserve"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=3600)
def fetch_geology(lat: float, lon: float) -> dict:
    """Fetch geological unit data from Macrostrat."""
    try:
        resp = requests.get(
            f"{MACROSTRAT_API}/geologic_units/map",
            params={"lat": lat, "lng": lon, "response": "long"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Macrostrat error: {e}")
        return {}


@st.cache_data(ttl=3600)
def fetch_earthquakes(lat: float, lon: float, radius_km: int = 100,
                      days: int = 365) -> dict:
    """Fetch recent earthquakes from USGS."""
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        params = {
            "format": "geojson",
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"),
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radius_km,
            "minmagnitude": 1.0,
            "limit": 500,
        }
        resp = requests.get(USGS_EQ_API, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"USGS earthquake error: {e}")
        return {"features": []}


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS PROCESSING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def parse_soil_layers(soil_data: dict) -> pd.DataFrame:
    """Parse SoilGrids response into a tidy DataFrame."""
    rows = []
    properties = soil_data.get("properties", {}).get("layers", [])
    for layer in properties:
        prop_name = layer.get("name", "unknown")
        meta = SOIL_PROPERTIES.get(prop_name, {"divisor": 1, "name": prop_name, "unit": ""})
        for depth_entry in layer.get("depths", []):
            depth_label = depth_entry.get("label", "?")
            val_raw = depth_entry.get("values", {}).get("mean")
            if val_raw is not None:
                val = val_raw / meta["divisor"]
            else:
                val = None
            rows.append({
                "property": meta["name"],
                "depth": depth_label,
                "value": val,
                "unit": meta.get("unit", ""),
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["property", "depth", "value", "unit"]
    )


def compute_landuse_breakdown(landuse_data: dict) -> dict:
    """Compute land use category counts and areas from Overpass elements."""
    categories = {}
    building_count = 0
    road_length_approx = 0
    for el in landuse_data.get("elements", []):
        tags = el.get("tags", {})
        if "building" in tags:
            building_count += 1
            continue
        if "highway" in tags:
            road_length_approx += 1
            continue
        lu = tags.get("landuse", tags.get("leisure", "other"))
        categories[lu] = categories.get(lu, 0) + 1
    return {
        "categories": categories,
        "building_count": building_count,
        "road_segments": road_length_approx,
    }


def compute_species_breakdown(inat_data: dict, gbif_data: dict) -> dict:
    """Aggregate biodiversity data from iNaturalist and GBIF."""
    kingdom_counts = {}
    species_list = {}
    taxon_names = {}

    for obs in inat_data.get("results", []):
        taxon = obs.get("taxon")
        if not taxon:
            continue
        kingdom = taxon.get("iconic_taxon_name", "Other")
        kingdom_counts[kingdom] = kingdom_counts.get(kingdom, 0) + 1
        sp_name = taxon.get("name", "Unknown")
        sp_common = taxon.get("preferred_common_name", sp_name)
        species_list[sp_name] = species_list.get(sp_name, 0) + 1
        taxon_names[sp_name] = sp_common

    gbif_species = set()
    for occ in gbif_data.get("results", []):
        sp = occ.get("species", occ.get("scientificName", ""))
        if sp:
            gbif_species.add(sp)
            kingdom = occ.get("kingdom", "Other")
            kingdom_counts[kingdom] = kingdom_counts.get(kingdom, 0) + 1

    # Sort species by count
    top_species = sorted(species_list.items(), key=lambda x: x[1], reverse=True)[:20]
    return {
        "kingdom_counts": kingdom_counts,
        "top_species": [(name, count, taxon_names.get(name, name)) for name, count in top_species],
        "inat_total": inat_data.get("total_results", 0),
        "gbif_total": gbif_data.get("count", 0),
        "gbif_unique_species": len(gbif_species),
    }


def compute_risk_assessment(earthquakes: dict, water_features: dict,
                            landuse_data: dict, elevation_data: dict,
                            lat: float, lon: float) -> dict:
    """
    Compute a multi-factor risk assessment on a 0-10 scale.
    Categories: Seismic, Flood, Fire, Landslide, Pollution.
    """
    # --- Seismic risk ---
    eq_features = earthquakes.get("features", [])
    seismic_risk = 0.0
    if eq_features:
        mags = [f["properties"].get("mag", 0) for f in eq_features]
        max_mag = max(mags) if mags else 0
        count = len(eq_features)
        seismic_risk = min(10.0, (max_mag / 9.0) * 6.0 + min(count / 50.0, 1.0) * 4.0)

    # --- Flood risk ---
    water_els = water_features.get("elements", [])
    water_count = len(water_els)
    elev = elevation_data.get("center_elevation", 100)
    elev_range = elevation_data.get("max_elevation", 100) - elevation_data.get("min_elevation", 0)
    flood_risk = min(10.0, (water_count / 30.0) * 5.0 + max(0, (50 - elev) / 50.0) * 3.0 +
                     max(0, (10 - elev_range) / 10.0) * 2.0)

    # --- Fire risk ---
    lu_breakdown = compute_landuse_breakdown(landuse_data)
    cats = lu_breakdown["categories"]
    veg_count = cats.get("forest", 0) + cats.get("meadow", 0) + cats.get("farmland", 0)
    fire_risk = min(10.0, (veg_count / 20.0) * 6.0 + max(0, (elev_range - 50) / 200.0) * 4.0)

    # --- Landslide risk ---
    slope_proxy = elev_range
    landslide_risk = min(10.0, (slope_proxy / 500.0) * 7.0 +
                         (water_count / 40.0) * 3.0)

    # --- Pollution risk ---
    industrial = cats.get("industrial", 0) + cats.get("construction", 0)
    road_seg = lu_breakdown["road_segments"]
    pollution_risk = min(10.0, (industrial / 10.0) * 5.0 + (road_seg / 100.0) * 3.0 +
                         (lu_breakdown["building_count"] / 200.0) * 2.0)

    return {
        "Seismic": round(max(0, seismic_risk), 1),
        "Flood": round(max(0, flood_risk), 1),
        "Fire": round(max(0, fire_risk), 1),
        "Landslide": round(max(0, landslide_risk), 1),
        "Pollution": round(max(0, pollution_risk), 1),
    }


def parse_geology_data(geo_data: dict) -> list:
    """Extract geological unit info from Macrostrat response."""
    units = []
    for item in geo_data.get("success", {}).get("data", []):
        strat_name = item.get("strat_name_long") or item.get("strat_name") or item.get("name") or "Unknown"
        units.append({
            "name": strat_name,
            "age": item.get("t_age", "?"),
            "lithology": item.get("lith", "Unknown"),
            "period": item.get("t_int_name", "Unknown"),
            "environment": item.get("environ", "Unknown"),
            "comments": item.get("comments", ""),
            "color": item.get("color", "#8b97b0"),
        })
    return units


# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _render_radar_chart_html(risk_data: dict) -> str:
    """Generate an HTML/SVG radar chart for risk assessment."""
    categories = list(risk_data.keys())
    values = [risk_data[c] for c in categories]
    n = len(categories)
    if n == 0:
        return "<p>No risk data available.</p>"

    cx, cy, r = 150, 150, 120
    angle_step = 2 * math.pi / n

    # Build polygon points for the data
    data_points = []
    axis_lines = []
    labels = []
    grid_rings = []

    for ring in [0.25, 0.5, 0.75, 1.0]:
        ring_pts = []
        for i in range(n):
            angle = -math.pi / 2 + i * angle_step
            px = cx + r * ring * math.cos(angle)
            py = cy + r * ring * math.sin(angle)
            ring_pts.append(f"{px:.1f},{py:.1f}")
        grid_rings.append(
            f'<polygon points="{" ".join(ring_pts)}" fill="none" '
            f'stroke="#2a3550" stroke-width="0.5"/>'
        )

    for i in range(n):
        angle = -math.pi / 2 + i * angle_step
        ax = cx + r * math.cos(angle)
        ay = cy + r * math.sin(angle)
        axis_lines.append(
            f'<line x1="{cx}" y1="{cy}" x2="{ax:.1f}" y2="{ay:.1f}" '
            f'stroke="#2a3550" stroke-width="0.5"/>'
        )

        lx = cx + (r + 22) * math.cos(angle)
        ly = cy + (r + 22) * math.sin(angle)
        color = RISK_COLORS.get(categories[i], "#8b97b0")
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" fill="{color}" '
            f'font-size="11" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="sans-serif">{html_module.escape(categories[i])} '
            f'({values[i]:.1f})</text>'
        )

        val_frac = min(values[i] / 10.0, 1.0)
        dx = cx + r * val_frac * math.cos(angle)
        dy = cy + r * val_frac * math.sin(angle)
        data_points.append(f"{dx:.1f},{dy:.1f}")

    polygon = (
        f'<polygon points="{" ".join(data_points)}" '
        f'fill="rgba(6,182,212,0.25)" stroke="#06b6d4" stroke-width="2"/>'
    )
    dots = ""
    for pt in data_points:
        px, py = pt.split(",")
        dots += (
            f'<circle cx="{px}" cy="{py}" r="4" fill="#06b6d4" '
            f'stroke="#0a0e1a" stroke-width="1.5"/>'
        )

    svg = (
        f'<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg" '
        f'style="max-width:340px;background:rgba(15,23,42,0.65);border-radius:12px;'
        f'border:1px solid #2a3550;padding:10px;">'
        f'{"".join(grid_rings)}{"".join(axis_lines)}{polygon}{dots}'
        f'{"".join(labels)}</svg>'
    )
    return svg


def _render_gauge_html(value: float, max_val: float, label: str,
                       unit: str, color: str = "#06b6d4") -> str:
    """Render a semicircular gauge as SVG."""
    frac = min(value / max_val, 1.0) if max_val > 0 else 0
    angle = 180 * frac
    end_angle_rad = math.radians(180 - angle)
    cx, cy, r = 100, 90, 70

    # Arc path
    ex = cx + r * math.cos(end_angle_rad)
    ey = cy - r * math.sin(end_angle_rad)
    large = 1 if angle > 180 else 0
    arc_path = (
        f"M {cx - r},{cy} A {r},{r} 0 {large},1 {ex:.1f},{ey:.1f}"
    )
    safe_label = html_module.escape(label)
    safe_unit = html_module.escape(unit)

    svg = (
        f'<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg" '
        f'style="max-width:220px;">'
        f'<path d="M {cx - r},{cy} A {r},{r} 0 0,1 {cx + r},{cy}" '
        f'fill="none" stroke="#2a3550" stroke-width="12" stroke-linecap="round"/>'
        f'<path d="{arc_path}" fill="none" stroke="{color}" '
        f'stroke-width="12" stroke-linecap="round"/>'
        f'<text x="{cx}" y="{cy - 10}" text-anchor="middle" '
        f'fill="#e8ecf4" font-size="20" font-weight="bold" '
        f'font-family="sans-serif">{value:.1f}</text>'
        f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" '
        f'fill="#8b97b0" font-size="10" font-family="sans-serif">{safe_unit}</text>'
        f'<text x="{cx}" y="{cy + 28}" text-anchor="middle" '
        f'fill="#5a6580" font-size="9" font-family="sans-serif">{safe_label}</text>'
        f'</svg>'
    )
    return svg


def _render_bar_chart_html(data: dict, title: str, max_val: float = 0,
                           height: int = 200) -> str:
    """Render a horizontal bar chart as HTML/CSS."""
    if not data:
        return f"<p style='color:#5a6580;'>No {html_module.escape(title)} data.</p>"
    if max_val <= 0:
        max_val = max(data.values()) if data.values() else 1

    bars_html = ""
    colors = list(LANDUSE_COLORS.values())
    for idx, (label, value) in enumerate(sorted(data.items(), key=lambda x: -x[1])):
        pct = min((value / max_val) * 100, 100) if max_val > 0 else 0
        color = colors[idx % len(colors)]
        safe_label = html_module.escape(str(label))
        bars_html += (
            f'<div style="display:flex;align-items:center;margin:3px 0;">'
            f'<span style="color:#8b97b0;font-size:11px;width:100px;'
            f'text-align:right;padding-right:8px;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis;">{safe_label}</span>'
            f'<div style="flex:1;background:#1a2235;border-radius:4px;height:18px;'
            f'overflow:hidden;">'
            f'<div style="width:{pct:.1f}%;background:{color};height:100%;'
            f'border-radius:4px;transition:width 0.5s;"></div></div>'
            f'<span style="color:#e8ecf4;font-size:11px;width:40px;'
            f'text-align:right;padding-left:6px;">{value}</span></div>'
        )

    safe_title = html_module.escape(title)
    return (
        f'<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;'
        f'border-radius:12px;padding:14px;backdrop-filter:blur(16px);">'
        f'<h5 style="color:#e8ecf4;margin:0 0 10px 0;font-size:13px;">'
        f'{safe_title}</h5>{bars_html}</div>'
    )


def _render_donut_html(data: dict, title: str) -> str:
    """Render a simple donut chart as SVG."""
    total = sum(data.values())
    if total == 0:
        return f"<p style='color:#5a6580;'>No {html_module.escape(title)} data.</p>"

    cx, cy, r, inner_r = 80, 80, 65, 40
    colors = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444",
              "#ec4899", "#3b82f6", "#14b8a6", "#f97316", "#84cc16"]
    segments = ""
    legend = ""
    cum_angle = 0

    for idx, (label, value) in enumerate(sorted(data.items(), key=lambda x: -x[1])):
        frac = value / total
        angle = frac * 360
        start_rad = math.radians(cum_angle - 90)
        end_rad = math.radians(cum_angle + angle - 90)

        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)
        ix1 = cx + inner_r * math.cos(end_rad)
        iy1 = cy + inner_r * math.sin(end_rad)
        ix2 = cx + inner_r * math.cos(start_rad)
        iy2 = cy + inner_r * math.sin(start_rad)
        large = 1 if angle > 180 else 0
        color = colors[idx % len(colors)]

        segments += (
            f'<path d="M {x1:.1f},{y1:.1f} A {r},{r} 0 {large},1 {x2:.1f},{y2:.1f}'
            f' L {ix1:.1f},{iy1:.1f} A {inner_r},{inner_r} 0 {large},0 '
            f'{ix2:.1f},{iy2:.1f} Z" fill="{color}" stroke="#0a0e1a" stroke-width="1"/>'
        )
        safe_label = html_module.escape(str(label)[:20])
        legend += (
            f'<div style="display:flex;align-items:center;margin:1px 0;">'
            f'<span style="width:8px;height:8px;border-radius:50%;'
            f'background:{color};margin-right:5px;flex-shrink:0;"></span>'
            f'<span style="color:#8b97b0;font-size:10px;">{safe_label} ({value})</span>'
            f'</div>'
        )
        cum_angle += angle

    safe_title = html_module.escape(title)
    return (
        f'<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;'
        f'border-radius:12px;padding:14px;backdrop-filter:blur(16px);">'
        f'<h5 style="color:#e8ecf4;margin:0 0 8px 0;font-size:13px;">{safe_title}</h5>'
        f'<div style="display:flex;align-items:flex-start;gap:12px;">'
        f'<svg viewBox="0 0 160 160" style="max-width:140px;">{segments}'
        f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" fill="#e8ecf4" '
        f'font-size="16" font-weight="bold" font-family="sans-serif">{total}</text>'
        f'</svg>'
        f'<div style="flex:1;max-height:140px;overflow-y:auto;">{legend}</div>'
        f'</div></div>'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_deep_zone_analysis_tab():
    """Render the Deep Zone Analysis tab UI."""

    # ── Tab header ──
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Deep Zone Analysis</h4>"
        "<p>Click any point &mdash; AI-powered analysis with interpolation: "
        "terrain, soil, climate, species, water table, geology &amp; risk</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Sidebar / Controls ──
    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        preset = st.selectbox("Preset Location", list(ANALYSIS_PRESETS.keys()),
                              key="dza_preset")
    with c2:
        if preset != "Custom" and ANALYSIS_PRESETS[preset]:
            default_lat = ANALYSIS_PRESETS[preset]["lat"]
            default_lon = ANALYSIS_PRESETS[preset]["lon"]
        else:
            default_lat = 41.90
            default_lon = 12.50
        lat = st.number_input("Latitude", value=default_lat, format="%.5f",
                              min_value=-90.0, max_value=90.0, key="dza_lat")
    with c3:
        lon = st.number_input("Longitude", value=default_lon, format="%.5f",
                              min_value=-180.0, max_value=180.0, key="dza_lon")

    rc1, rc2 = st.columns([1, 1])
    with rc1:
        search_radius_km = st.slider("Search radius (km)", 1, 30, 10,
                                     key="dza_radius")
    with rc2:
        analysis_depth = st.selectbox("Analysis depth", ["Standard", "Extended"],
                                      key="dza_depth")

    run_analysis = st.button("Run Deep Zone Analysis", type="primary",
                             key="dza_run", use_container_width=True)

    # ── Map display (always shown) ──
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB dark_matter")
    folium.Marker(
        [lat, lon],
        popup=f"Target: {lat:.5f}, {lon:.5f}",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)
    folium.Circle(
        [lat, lon], radius=search_radius_km * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.08, weight=1,
    ).add_to(m)
    st_html(m._repr_html_(), height=480)

    if not run_analysis:
        st.info("Set coordinates and click **Run Deep Zone Analysis** to start "
                "the multi-source intelligence scan.")
        return

    # ══════════════════════════════════════════════════════════════════════════
    # FETCH ALL DATA SOURCES
    # ══════════════════════════════════════════════════════════════════════════

    radius_m = search_radius_km * 1000
    progress = st.progress(0, text="Initializing deep scan...")

    progress.progress(5, text="Fetching elevation grid...")
    elev_data = fetch_elevation_grid(lat, lon, radius_deg=search_radius_km * 0.009)

    progress.progress(15, text="Fetching soil composition...")
    soil_data = fetch_soil_data(lat, lon)

    progress.progress(25, text="Fetching weather & climate...")
    weather_data = fetch_weather_data(lat, lon)

    progress.progress(35, text="Fetching biodiversity (iNaturalist)...")
    inat_data = fetch_biodiversity(lat, lon, radius_km=search_radius_km)

    progress.progress(42, text="Fetching biodiversity (GBIF)...")
    gbif_data = fetch_gbif_occurrences(lat, lon, radius_m=radius_m)

    progress.progress(50, text="Fetching water features...")
    water_data = fetch_water_features(lat, lon, radius=radius_m)

    progress.progress(60, text="Fetching land use & infrastructure...")
    landuse_data = fetch_landuse_infrastructure(lat, lon, radius=radius_m)

    progress.progress(70, text="Fetching protected areas...")
    protected_data = fetch_protected_areas(lat, lon, radius=radius_m)

    progress.progress(78, text="Fetching geological data...")
    geo_data = fetch_geology(lat, lon)

    progress.progress(85, text="Fetching seismic activity...")
    eq_data = fetch_earthquakes(lat, lon, radius_km=max(search_radius_km * 5, 100))

    climate_data = {}
    if analysis_depth == "Extended":
        progress.progress(90, text="Fetching climate projections (extended)...")
        climate_data = fetch_climate_data(lat, lon)

    progress.progress(95, text="Computing analysis & interpolations...")

    # ══════════════════════════════════════════════════════════════════════════
    # PROCESS & ANALYZE
    # ══════════════════════════════════════════════════════════════════════════

    soil_df = parse_soil_layers(soil_data)
    species_info = compute_species_breakdown(inat_data, gbif_data)
    lu_info = compute_landuse_breakdown(landuse_data)
    risks = compute_risk_assessment(eq_data, water_data, landuse_data, elev_data,
                                    lat, lon)
    geo_units = parse_geology_data(geo_data)

    # Water table estimate
    springs, wells = [], []
    for el in water_data.get("elements", []):
        tags = el.get("tags", {})
        elat = el.get("lat", el.get("center", {}).get("lat", 0))
        elon = el.get("lon", el.get("center", {}).get("lon", 0))
        if tags.get("natural") == "spring":
            springs.append({"lat": elat, "lon": elon})
        elif tags.get("man_made") == "water_well":
            depth_str = tags.get("depth", "15")
            try:
                depth_val = float(depth_str)
            except (ValueError, TypeError):
                depth_val = 15.0
            wells.append({"lat": elat, "lon": elon, "depth": depth_val})
    water_table = estimate_water_table_depth(
        springs, wells, elev_data.get("elevation_map", {}),
        lat, lon, elev_data.get("center_elevation", 0)
    )

    # Koppen classification
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    temp_now = current.get("temperature_2m", 15)
    daily_max = daily.get("temperature_2m_max", [])
    daily_min = daily.get("temperature_2m_min", [])
    daily_precip = daily.get("precipitation_sum", [])
    avg_temp = float(np.mean(daily_max + daily_min)) if (daily_max or daily_min) else temp_now
    max_temp = float(np.max(daily_max)) if daily_max else temp_now + 5
    min_temp = float(np.min(daily_min)) if daily_min else temp_now - 5
    annual_precip = float(np.sum(daily_precip)) * (365 / max(len(daily_precip), 1)) if daily_precip else 500
    driest_precip = float(np.min(daily_precip)) * 30 if daily_precip else 20
    koppen_code = classify_koppen(avg_temp, annual_precip, max_temp, min_temp,
                                  driest_precip)
    koppen_desc = KOPPEN_CLASSES.get(koppen_code, "Unknown")

    protected_count = len(protected_data.get("elements", []))
    protected_names = []
    for el in protected_data.get("elements", []):
        name = el.get("tags", {}).get("name", "Unnamed Protected Area")
        protected_names.append(name)

    progress.progress(100, text="Analysis complete!")

    # ══════════════════════════════════════════════════════════════════════════
    # DISPLAY RESULTS
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("---")
    st.subheader("Analysis Results")

    # ── Overview Metrics ──
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Elevation", f"{elev_data['center_elevation']:.0f} m")
    m2.metric("Temperature", f"{temp_now:.1f} C")
    m3.metric("Humidity",
              f"{current.get('relative_humidity_2m', 'N/A')}%")
    m4.metric("Species (iNat)", f"{species_info['inat_total']}")
    m5.metric("GBIF Records", f"{species_info['gbif_total']}")
    m6.metric("Water Features", f"{len(water_data.get('elements', []))}")

    m7, m8, m9, m10, m11, m12 = st.columns(6)
    m7.metric("Buildings", f"{lu_info['building_count']}")
    m8.metric("Road Segments", f"{lu_info['road_segments']}")
    m9.metric("Protected Areas", f"{protected_count}")
    m10.metric("Earthquakes (1yr)", f"{len(eq_data.get('features', []))}")
    m11.metric("Koppen Climate", koppen_code)
    m12.metric("Avg Risk Score",
               f"{np.mean(list(risks.values())):.1f}/10")

    # ═══════════════════════════════════════════════════════════════
    # 1. ELEVATION PROFILE
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 1. Terrain & Elevation Profile")
    elev_c1, elev_c2 = st.columns([1.2, 1])
    with elev_c1:
        ns_prof = elev_data.get("ns_profile", [])
        ew_prof = elev_data.get("ew_profile", [])
        if ns_prof and ew_prof:
            ns_df = pd.DataFrame({
                "N-S Profile": [p["elevation"] for p in ns_prof],
            }, index=[f"{p['lat']:.3f}" for p in ns_prof])
            ew_df = pd.DataFrame({
                "E-W Profile": [p["elevation"] for p in ew_prof],
            }, index=[f"{p['lon']:.3f}" for p in ew_prof])
            st.line_chart(ns_df, use_container_width=True)
            st.caption("North-South elevation cross-section (latitude)")
            st.line_chart(ew_df, use_container_width=True)
            st.caption("East-West elevation cross-section (longitude)")
        else:
            st.warning("Elevation profile data not available.")

    with elev_c2:
        em1, em2 = st.columns(2)
        em1.metric("Center Elevation", f"{elev_data['center_elevation']:.1f} m")
        em2.metric("Elevation Range",
                   f"{elev_data['max_elevation'] - elev_data['min_elevation']:.1f} m")
        em3, em4 = st.columns(2)
        em3.metric("Min Elevation", f"{elev_data['min_elevation']:.1f} m")
        em4.metric("Max Elevation", f"{elev_data['max_elevation']:.1f} m")
        st.metric("Average Elevation", f"{elev_data['avg_elevation']:.1f} m")

        # Slope estimate
        if ns_prof and len(ns_prof) >= 2:
            elev_diff = abs(ns_prof[-1]["elevation"] - ns_prof[0]["elevation"])
            dist_ns = haversine_distance(ns_prof[0]["lat"], ns_prof[0]["lon"],
                                         ns_prof[-1]["lat"], ns_prof[-1]["lon"])
            slope_pct = (elev_diff / (dist_ns * 1000) * 100) if dist_ns > 0 else 0
            st.metric("Approx. Slope (N-S)", f"{slope_pct:.2f}%")

    # ═══════════════════════════════════════════════════════════════
    # 2. SOIL COMPOSITION
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 2. Soil Composition (ISRIC SoilGrids)")
    if not soil_df.empty:
        soil_c1, soil_c2 = st.columns([1.3, 1])
        with soil_c1:
            # Stacked bar chart: Clay / Sand / Silt per depth
            texture_df = soil_df[soil_df["property"].isin(["Clay", "Sand", "Silt"])]
            if not texture_df.empty:
                pivot = texture_df.pivot_table(
                    index="depth", columns="property", values="value", aggfunc="first"
                )
                # Reorder depths logically
                depth_order = ["0-5cm", "5-15cm", "15-30cm", "30-60cm",
                               "60-100cm", "100-200cm"]
                ordered_depths = [d for d in depth_order if d in pivot.index]
                if ordered_depths:
                    pivot = pivot.loc[ordered_depths]
                st.bar_chart(pivot, use_container_width=True)
                st.caption("Soil texture (Clay / Sand / Silt %) by depth layer")

            # Other properties table
            other_df = soil_df[~soil_df["property"].isin(["Clay", "Sand", "Silt"])]
            if not other_df.empty:
                st.dataframe(other_df, use_container_width=True, hide_index=True)

        with soil_c2:
            # Top-layer pie (0-5cm)
            top_layer = soil_df[
                (soil_df["depth"] == "0-5cm") &
                (soil_df["property"].isin(["Clay", "Sand", "Silt"]))
            ]
            if not top_layer.empty:
                composition = {
                    row["property"]: row["value"]
                    for _, row in top_layer.iterrows()
                    if row["value"] is not None
                }
                st.markdown(
                    _render_donut_html(
                        {k: int(v) for k, v in composition.items()},
                        "Surface Soil Texture (0-5cm)"
                    ),
                    unsafe_allow_html=True,
                )
            # pH display
            ph_row = soil_df[
                (soil_df["property"] == "pH (H2O)") & (soil_df["depth"] == "0-5cm")
            ]
            if not ph_row.empty and ph_row.iloc[0]["value"] is not None:
                ph_val = ph_row.iloc[0]["value"]
                st.markdown(
                    _render_gauge_html(ph_val, 14.0, "Soil pH (0-5cm)", "pH",
                                       "#06b6d4"),
                    unsafe_allow_html=True,
                )
    else:
        st.warning("Soil data not available for this location.")

    # ═══════════════════════════════════════════════════════════════
    # 3. WEATHER & CLIMATE
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 3. Weather & Climate Profile")
    wx_c1, wx_c2 = st.columns([1.5, 1])
    with wx_c1:
        if daily_max and daily_min:
            dates = daily.get("time", list(range(len(daily_max))))
            temp_df = pd.DataFrame({
                "Max Temp (C)": daily_max,
                "Min Temp (C)": daily_min,
            }, index=dates[:len(daily_max)])
            st.line_chart(temp_df, use_container_width=True)
            st.caption("7-day temperature forecast")

        if daily_precip:
            precip_df = pd.DataFrame({
                "Precipitation (mm)": daily_precip,
            }, index=dates[:len(daily_precip)] if dates else None)
            st.bar_chart(precip_df, use_container_width=True)
            st.caption("7-day precipitation forecast")

    with wx_c2:
        wm1, wm2 = st.columns(2)
        wm1.metric("Temperature", f"{temp_now:.1f} C")
        wm2.metric("Humidity",
                    f"{current.get('relative_humidity_2m', 'N/A')}%")
        wm3, wm4 = st.columns(2)
        wm3.metric("Wind Speed",
                    f"{current.get('wind_speed_10m', 'N/A')} km/h")
        wm4.metric("Pressure",
                    f"{current.get('surface_pressure', 'N/A')} hPa")
        wm5, wm6 = st.columns(2)
        wm5.metric("Cloud Cover",
                    f"{current.get('cloud_cover', 'N/A')}%")
        wm6.metric("Precipitation",
                    f"{current.get('precipitation', 0)} mm")
        st.metric("Koppen Classification",
                  f"{koppen_code} - {koppen_desc}")

    # Extended climate projections
    if analysis_depth == "Extended" and climate_data:
        st.markdown("#### Climate Projections (EC-Earth3P-HR)")
        clim_daily = climate_data.get("daily", {})
        clim_temps = clim_daily.get("temperature_2m_mean", [])
        clim_dates = clim_daily.get("time", [])
        if clim_temps and clim_dates:
            # Subsample for performance: take every 365th value (annual)
            step = max(1, len(clim_temps) // 200)
            sampled_temps = clim_temps[::step]
            sampled_dates = clim_dates[::step]
            clim_df = pd.DataFrame({
                "Mean Temp (C)": sampled_temps,
            }, index=sampled_dates)
            st.line_chart(clim_df, use_container_width=True)
            st.caption("Historical & projected mean temperature (1950-2050)")

    # ═══════════════════════════════════════════════════════════════
    # 4. BIODIVERSITY
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 4. Species Diversity & Biodiversity")
    bio_c1, bio_c2 = st.columns([1, 1.2])
    with bio_c1:
        kc = species_info["kingdom_counts"]
        if kc:
            st.markdown(
                _render_donut_html(kc, "Species Kingdom Distribution"),
                unsafe_allow_html=True,
            )
        else:
            st.info("No biodiversity observations found in this area.")

    with bio_c2:
        top_sp = species_info["top_species"]
        if top_sp:
            sp_df = pd.DataFrame(top_sp, columns=["Scientific Name", "Count",
                                                    "Common Name"])
            st.dataframe(sp_df, use_container_width=True, hide_index=True)
        bm1, bm2, bm3 = st.columns(3)
        bm1.metric("iNaturalist Total", species_info["inat_total"])
        bm2.metric("GBIF Records", species_info["gbif_total"])
        bm3.metric("GBIF Unique Species", species_info["gbif_unique_species"])

    # ═══════════════════════════════════════════════════════════════
    # 5. WATER TABLE ESTIMATE
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 5. Water Table & Hydrology")
    wt_c1, wt_c2 = st.columns([1, 1])
    with wt_c1:
        water_els = water_data.get("elements", [])
        spring_count = sum(1 for el in water_els
                          if el.get("tags", {}).get("natural") == "spring")
        well_count = sum(1 for el in water_els
                        if el.get("tags", {}).get("man_made") == "water_well")
        waterway_count = sum(1 for el in water_els
                            if "waterway" in el.get("tags", {}))
        waterbody_count = sum(1 for el in water_els
                             if el.get("tags", {}).get("natural") == "water")

        wf1, wf2 = st.columns(2)
        wf1.metric("Springs", spring_count)
        wf2.metric("Wells", well_count)
        wf3, wf4 = st.columns(2)
        wf3.metric("Waterways", waterway_count)
        wf4.metric("Water Bodies", waterbody_count)

    with wt_c2:
        if water_table is not None:
            st.markdown(
                _render_gauge_html(water_table, 50.0,
                                   "Estimated Water Table Depth", "meters",
                                   "#3b82f6"),
                unsafe_allow_html=True,
            )
            st.caption("IDW-interpolated estimate from nearby springs & wells. "
                       "Accuracy depends on available data density.")
        else:
            st.info("Insufficient water feature data for water table estimation. "
                    "No springs or wells found within search radius.")

        # Water feature distance summary
        if water_els:
            distances = []
            for el in water_els[:50]:
                elat = el.get("lat", el.get("center", {}).get("lat"))
                elon = el.get("lon", el.get("center", {}).get("lon"))
                if elat and elon:
                    d = haversine_distance(lat, lon, elat, elon)
                    distances.append(d)
            if distances:
                st.metric("Nearest Water Feature", f"{min(distances):.2f} km")
                st.metric("Avg Distance to Water", f"{np.mean(distances):.2f} km")

    # ═══════════════════════════════════════════════════════════════
    # 6. LAND USE BREAKDOWN
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 6. Land Use & Infrastructure Density")
    lu_c1, lu_c2 = st.columns([1.2, 1])
    with lu_c1:
        cats = lu_info["categories"]
        if cats:
            st.markdown(
                _render_bar_chart_html(cats, "Land Use Categories"),
                unsafe_allow_html=True,
            )
        else:
            st.info("No land use data found in this area.")

    with lu_c2:
        area_km2 = math.pi * (search_radius_km ** 2)
        buildings = lu_info["building_count"]
        roads = lu_info["road_segments"]
        density_buildings = buildings / area_km2 if area_km2 > 0 else 0
        density_roads = roads / area_km2 if area_km2 > 0 else 0

        id1, id2 = st.columns(2)
        id1.metric("Buildings/km2", f"{density_buildings:.1f}")
        id2.metric("Road Segments/km2", f"{density_roads:.1f}")

        if buildings > 0:
            urbanization = "Urban" if density_buildings > 50 else (
                "Suburban" if density_buildings > 10 else (
                    "Rural" if density_buildings > 1 else "Wilderness"
                )
            )
            st.metric("Urbanization Level", urbanization)

        if protected_names:
            st.markdown("**Protected Areas Nearby:**")
            for pname in protected_names[:10]:
                st.markdown(f"- {html_module.escape(pname)}")

    # ═══════════════════════════════════════════════════════════════
    # 7. RISK ASSESSMENT RADAR
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 7. Risk Assessment")
    risk_c1, risk_c2 = st.columns([1, 1])
    with risk_c1:
        st.markdown(
            _render_radar_chart_html(risks),
            unsafe_allow_html=True,
        )
        st.caption("Multi-factor risk assessment (0-10 scale). "
                   "Based on proximity analysis and feature density.")

    with risk_c2:
        for cat, val in risks.items():
            color = RISK_COLORS.get(cat, "#8b97b0")
            bar_pct = min(val / 10.0 * 100, 100)
            level = "Low" if val < 3 else ("Moderate" if val < 6 else "High")
            st.markdown(
                f'<div style="margin:6px 0;">'
                f'<span style="color:{color};font-weight:bold;font-size:13px;">'
                f'{html_module.escape(cat)}: {val:.1f}/10 ({level})</span>'
                f'<div style="background:#1a2235;border-radius:6px;height:14px;'
                f'margin-top:3px;">'
                f'<div style="width:{bar_pct:.0f}%;background:{color};height:100%;'
                f'border-radius:6px;"></div></div></div>',
                unsafe_allow_html=True,
            )
        avg_risk = np.mean(list(risks.values()))
        overall = "LOW" if avg_risk < 3 else ("MODERATE" if avg_risk < 6 else "HIGH")
        st.metric("Overall Risk Level", f"{overall} ({avg_risk:.1f}/10)")

    # ═══════════════════════════════════════════════════════════════
    # 8. GEOLOGY
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 8. Geological Cross-Section (Macrostrat)")
    if geo_units:
        for unit in geo_units:
            unit_color = unit.get("color", "#2a3550")
            safe_name = html_module.escape(str(unit.get("name", "Unknown")))
            safe_lith = html_module.escape(str(unit.get("lithology", "Unknown")))
            safe_period = html_module.escape(str(unit.get("period", "Unknown")))
            safe_env = html_module.escape(str(unit.get("environment", "")))
            safe_age = html_module.escape(str(unit.get("age", "?")))

            st.markdown(
                f'<div style="background:rgba(15,23,42,0.65);border-left:4px solid '
                f'{unit_color};padding:10px 14px;margin:6px 0;border-radius:0 8px 8px 0;'
                f'backdrop-filter:blur(16px);">'
                f'<span style="color:#e8ecf4;font-weight:bold;font-size:14px;">'
                f'{safe_name}</span><br/>'
                f'<span style="color:#8b97b0;font-size:12px;">'
                f'Period: {safe_period} | Age: {safe_age} Ma</span><br/>'
                f'<span style="color:#06b6d4;font-size:12px;">'
                f'Lithology: {safe_lith}</span>'
                f'{"<br/><span style=color:#5a6580;font-size:11px;>" + safe_env + "</span>" if safe_env and safe_env != "Unknown" else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )
        if len(geo_units) > 0:
            geo_df = pd.DataFrame(geo_units)
            st.dataframe(geo_df[["name", "period", "age", "lithology"]],
                         use_container_width=True, hide_index=True)
    else:
        st.info("No geological unit data available from Macrostrat for this location.")

    # ═══════════════════════════════════════════════════════════════
    # 9. SEISMIC DETAIL
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 9. Seismic Activity Detail")
    eq_features = eq_data.get("features", [])
    if eq_features:
        eq_c1, eq_c2 = st.columns([1, 1.2])
        with eq_c1:
            mags = [f["properties"].get("mag", 0) for f in eq_features]
            eq_m1, eq_m2 = st.columns(2)
            eq_m1.metric("Total Earthquakes", len(eq_features))
            eq_m2.metric("Max Magnitude", f"{max(mags):.1f}" if mags else "N/A")
            eq_m3, eq_m4 = st.columns(2)
            eq_m3.metric("Avg Magnitude",
                         f"{np.mean(mags):.1f}" if mags else "N/A")
            eq_m4.metric("Min Distance",
                         f"{min(haversine_distance(lat, lon, f['geometry']['coordinates'][1], f['geometry']['coordinates'][0]) for f in eq_features if f.get('geometry', {}).get('coordinates')):.1f} km"
                         if eq_features else "N/A")

            # Magnitude distribution
            mag_bins = {"<2": 0, "2-3": 0, "3-4": 0, "4-5": 0, "5-6": 0, "6+": 0}
            for mag in mags:
                if mag < 2:
                    mag_bins["<2"] += 1
                elif mag < 3:
                    mag_bins["2-3"] += 1
                elif mag < 4:
                    mag_bins["3-4"] += 1
                elif mag < 5:
                    mag_bins["4-5"] += 1
                elif mag < 6:
                    mag_bins["5-6"] += 1
                else:
                    mag_bins["6+"] += 1

            mag_df = pd.DataFrame({
                "Count": list(mag_bins.values()),
            }, index=list(mag_bins.keys()))
            st.bar_chart(mag_df, use_container_width=True)
            st.caption("Earthquake magnitude distribution (past year)")

        with eq_c2:
            eq_rows = []
            for f in eq_features[:30]:
                props = f.get("properties", {})
                coords = f.get("geometry", {}).get("coordinates", [0, 0, 0])
                eq_rows.append({
                    "Magnitude": props.get("mag", 0),
                    "Place": props.get("place", "Unknown"),
                    "Time": props.get("time", ""),
                    "Depth (km)": coords[2] if len(coords) > 2 else 0,
                    "Distance (km)": round(
                        haversine_distance(lat, lon, coords[1], coords[0]), 1
                    ) if len(coords) >= 2 else 0,
                })
            if eq_rows:
                eq_df = pd.DataFrame(eq_rows)
                st.dataframe(eq_df, use_container_width=True, hide_index=True)
    else:
        st.info("No earthquakes recorded within the search area in the past year.")

    # ═══════════════════════════════════════════════════════════════
    # 10. CLIMATE CLASSIFICATION DETAIL
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 10. Climate Classification & Summary")
    cl_c1, cl_c2 = st.columns([1, 1])
    with cl_c1:
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;'
            f'border-radius:12px;padding:18px;backdrop-filter:blur(16px);'
            f'text-align:center;">'
            f'<span style="color:#06b6d4;font-size:36px;font-weight:bold;">'
            f'{html_module.escape(koppen_code)}</span><br/>'
            f'<span style="color:#e8ecf4;font-size:16px;">'
            f'{html_module.escape(koppen_desc)}</span><br/>'
            f'<span style="color:#8b97b0;font-size:12px;margin-top:6px;'
            f'display:inline-block;">'
            f'Based on temperature and precipitation analysis</span></div>',
            unsafe_allow_html=True,
        )

    with cl_c2:
        cl1, cl2 = st.columns(2)
        cl1.metric("Avg Temperature", f"{avg_temp:.1f} C")
        cl2.metric("Est. Annual Precip.", f"{annual_precip:.0f} mm")
        cl3, cl4 = st.columns(2)
        cl3.metric("Max Temperature", f"{max_temp:.1f} C")
        cl4.metric("Min Temperature", f"{min_temp:.1f} C")
        cl5, cl6 = st.columns(2)
        cl5.metric("Wind Speed",
                    f"{current.get('wind_speed_10m', 'N/A')} km/h")
        cl6.metric("Pressure",
                    f"{current.get('surface_pressure', 'N/A')} hPa")

    # ══════════════════════════════════════════════════════════════
    # COMPREHENSIVE MAP WITH ALL FEATURES
    # ══════════════════════════════════════════════════════════════
    st.markdown("### Comprehensive Feature Map")
    feature_map = folium.Map(location=[lat, lon], zoom_start=13,
                             tiles="CartoDB dark_matter")
    # Target marker
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(
            f"<b>Target Point</b><br/>"
            f"Lat: {lat:.5f}<br/>Lon: {lon:.5f}<br/>"
            f"Elev: {elev_data['center_elevation']:.0f}m<br/>"
            f"Koppen: {html_module.escape(koppen_code)}",
            max_width=200,
        ),
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(feature_map)

    # Search radius
    folium.Circle(
        [lat, lon], radius=radius_m,
        color="#06b6d4", fill=True, fill_opacity=0.05, weight=1,
    ).add_to(feature_map)

    # Water features
    water_group = folium.FeatureGroup(name="Water Features")
    for el in water_data.get("elements", [])[:100]:
        elat = el.get("lat", el.get("center", {}).get("lat"))
        elon = el.get("lon", el.get("center", {}).get("lon"))
        if elat and elon:
            tags = el.get("tags", {})
            wtype = tags.get("natural", tags.get("waterway",
                             tags.get("man_made", "water")))
            safe_name = html_module.escape(tags.get("name", wtype))
            folium.CircleMarker(
                [elat, elon], radius=4, color="#3b82f6",
                fill=True, fill_color="#3b82f6", fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>{safe_name}</b><br/>Type: {html_module.escape(wtype)}",
                    max_width=180,
                ),
            ).add_to(water_group)
    water_group.add_to(feature_map)

    # Earthquake markers
    eq_group = folium.FeatureGroup(name="Earthquakes")
    for f in eq_features[:80]:
        coords = f.get("geometry", {}).get("coordinates", [0, 0])
        mag = f.get("properties", {}).get("mag", 0)
        place = f.get("properties", {}).get("place", "Unknown")
        eq_color = "#ef4444" if mag >= 4 else ("#f59e0b" if mag >= 2 else "#10b981")
        folium.CircleMarker(
            [coords[1], coords[0]], radius=max(3, mag * 2),
            color=eq_color, fill=True, fill_color=eq_color, fill_opacity=0.6,
            popup=folium.Popup(
                f"<b>M{mag:.1f}</b><br/>{html_module.escape(str(place))}",
                max_width=180,
            ),
        ).add_to(eq_group)
    eq_group.add_to(feature_map)

    # Protected areas
    pa_group = folium.FeatureGroup(name="Protected Areas")
    for el in protected_data.get("elements", [])[:30]:
        plat = el.get("lat", el.get("center", {}).get("lat"))
        plon = el.get("lon", el.get("center", {}).get("lon"))
        if plat and plon:
            pname = html_module.escape(
                el.get("tags", {}).get("name", "Protected Area")
            )
            folium.CircleMarker(
                [plat, plon], radius=8, color="#10b981",
                fill=True, fill_color="#10b981", fill_opacity=0.4,
                popup=folium.Popup(f"<b>{pname}</b>", max_width=180),
            ).add_to(pa_group)
    pa_group.add_to(feature_map)

    # Biodiversity observations
    bio_group = folium.FeatureGroup(name="Species Observations")
    taxon_colors_map = {
        "Plantae": "#10b981", "Aves": "#06b6d4", "Mammalia": "#8b5cf6",
        "Insecta": "#f59e0b", "Reptilia": "#ef4444", "Amphibia": "#ec4899",
        "Actinopterygii": "#3b82f6", "Fungi": "#a855f7",
    }
    for obs in inat_data.get("results", [])[:80]:
        olat = (obs.get("geojson") or {}).get("coordinates", [None, None])
        if olat and len(olat) >= 2:
            olon, olat_v = olat[0], olat[1]
            taxon = obs.get("taxon", {})
            taxon_name = taxon.get("iconic_taxon_name", "Other")
            sp_name = html_module.escape(
                taxon.get("preferred_common_name",
                          taxon.get("name", "Unknown"))
            )
            bc = taxon_colors_map.get(taxon_name, "#8b97b0")
            folium.CircleMarker(
                [olat_v, olon], radius=3, color=bc,
                fill=True, fill_color=bc, fill_opacity=0.6,
                popup=folium.Popup(
                    f"<b>{sp_name}</b><br/>"
                    f"<i>{html_module.escape(taxon.get('name', ''))}</i>",
                    max_width=180,
                ),
            ).add_to(bio_group)
    bio_group.add_to(feature_map)

    folium.LayerControl().add_to(feature_map)
    st_html(feature_map._repr_html_(), height=520)

    # ══════════════════════════════════════════════════════════════
    # FULL REPORT DOWNLOAD
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### Download Full Analysis Report")

    report = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "target": {"latitude": lat, "longitude": lon,
                    "search_radius_km": search_radius_km},
        "elevation": {
            "center": elev_data["center_elevation"],
            "min": elev_data["min_elevation"],
            "max": elev_data["max_elevation"],
            "avg": elev_data["avg_elevation"],
        },
        "soil": soil_df.to_dict(orient="records") if not soil_df.empty else [],
        "weather": {
            "temperature_c": temp_now,
            "humidity_pct": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "pressure_hpa": current.get("surface_pressure"),
            "cloud_cover_pct": current.get("cloud_cover"),
            "precipitation_mm": current.get("precipitation"),
        },
        "climate_classification": {
            "koppen_code": koppen_code,
            "koppen_description": koppen_desc,
            "avg_temp_c": round(avg_temp, 1),
            "est_annual_precip_mm": round(annual_precip, 0),
        },
        "biodiversity": {
            "inat_total_observations": species_info["inat_total"],
            "gbif_total_records": species_info["gbif_total"],
            "gbif_unique_species": species_info["gbif_unique_species"],
            "kingdom_distribution": species_info["kingdom_counts"],
            "top_species": [
                {"scientific": s[0], "count": s[1], "common": s[2]}
                for s in species_info["top_species"]
            ],
        },
        "water": {
            "total_features": len(water_data.get("elements", [])),
            "springs": spring_count,
            "wells": well_count,
            "waterways": waterway_count,
            "water_bodies": waterbody_count,
            "estimated_water_table_m": round(water_table, 2) if water_table else None,
        },
        "land_use": {
            "categories": lu_info["categories"],
            "building_count": lu_info["building_count"],
            "road_segments": lu_info["road_segments"],
            "building_density_per_km2": round(density_buildings, 1),
            "road_density_per_km2": round(density_roads, 1),
        },
        "protected_areas": {
            "count": protected_count,
            "names": protected_names[:20],
        },
        "geology": [
            {"name": u["name"], "period": u["period"],
             "age_ma": u["age"], "lithology": u["lithology"]}
            for u in geo_units
        ],
        "seismic": {
            "earthquake_count_1yr": len(eq_features),
            "max_magnitude": max(
                (f["properties"].get("mag", 0) for f in eq_features), default=0
            ),
        },
        "risk_assessment": risks,
        "overall_risk": round(float(np.mean(list(risks.values()))), 1),
    }

    report_json = json.dumps(report, indent=2, ensure_ascii=False, default=str)
    st.download_button(
        label="Download Full Report (JSON)",
        data=report_json,
        file_name=f"deep_zone_{lat:.4f}_{lon:.4f}.json",
        mime="application/json",
        use_container_width=True,
    )

    # Summary table
    if 'ph_row' not in locals():
        ph_row = pd.DataFrame()
        
    summary_rows = [
        {"Category": "Elevation", "Key Value": f"{elev_data['center_elevation']:.0f} m",
         "Detail": f"Range: {elev_data['min_elevation']:.0f}-{elev_data['max_elevation']:.0f} m"},
        {"Category": "Soil pH (0-5cm)",
         "Key Value": f"{ph_row.iloc[0]['value']:.1f}" if (not ph_row.empty and 'value' in ph_row.columns and ph_row.iloc[0]['value'] is not None) else "N/A",
         "Detail": "Surface acidity/alkalinity"},
        {"Category": "Temperature", "Key Value": f"{temp_now:.1f} C",
         "Detail": f"Range: {min_temp:.1f} - {max_temp:.1f} C"},
        {"Category": "Climate", "Key Value": f"{koppen_code}",
         "Detail": koppen_desc},
        {"Category": "Biodiversity",
         "Key Value": f"{species_info['inat_total']} obs",
         "Detail": f"{species_info['gbif_unique_species']} unique GBIF species"},
        {"Category": "Water Table",
         "Key Value": f"{water_table:.1f} m" if water_table else "N/A",
         "Detail": f"{spring_count} springs, {well_count} wells nearby"},
        {"Category": "Urbanization",
         "Key Value": f"{density_buildings:.0f} bldg/km2",
         "Detail": f"{lu_info['building_count']} buildings, {lu_info['road_segments']} roads"},
        {"Category": "Seismic",
         "Key Value": f"{len(eq_features)} quakes",
         "Detail": f"Max M{max((f['properties'].get('mag', 0) for f in eq_features), default=0):.1f}" if eq_features else "No activity"},
        {"Category": "Overall Risk",
         "Key Value": f"{np.mean(list(risks.values())):.1f}/10",
         "Detail": f"S:{risks['Seismic']:.0f} F:{risks['Flood']:.0f} "
                   f"Fi:{risks['Fire']:.0f} L:{risks['Landslide']:.0f} "
                   f"P:{risks['Pollution']:.0f}"},
    ]
    st.markdown("### Analysis Summary Table")
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True,
                 hide_index=True)
