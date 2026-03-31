"""
Climate Adaptation AI module for TerraScout AI.
Assesses climate change resilience across 6 dimensions using free data sources:
  - Open-Meteo Archive API (30-year historical temperature/precipitation trends)
  - Open-Meteo Forecast (current conditions)
  - ISRIC SoilGrids (soil moisture retention capacity)
  - Open Topo Data (elevation for flood/drought exposure)
  - Overpass API (green infrastructure, water management, shelters)
All free, no API key required.
"""

import logging
import math
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

OPEN_METEO_ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

DIMENSION_LABELS = [
    "Heat Resilience",
    "Drought Resilience",
    "Flood Adaptation",
    "Storm Resilience",
    "Sea Level Exposure",
    "Ecosystem Adaptation",
]

DIMENSION_COLORS = {
    "Heat Resilience": "#ef4444",
    "Drought Resilience": "#f59e0b",
    "Flood Adaptation": "#3b82f6",
    "Storm Resilience": "#8b5cf6",
    "Sea Level Exposure": "#06b6d4",
    "Ecosystem Adaptation": "#10b981",
}

RESILIENCE_LEVELS = {
    "Excellent": {"min": 80, "color": "#2ecc71"},
    "Good": {"min": 60, "color": "#a3d977"},
    "Moderate": {"min": 40, "color": "#f1c40f"},
    "Low": {"min": 20, "color": "#e67e22"},
    "Critical": {"min": 0, "color": "#e74c3c"},
}


# =============================================================================
# UTILITY
# =============================================================================

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def _classify_resilience(score: float) -> tuple:
    """Return (label, color) for a resilience score 0-100."""
    for label, info in RESILIENCE_LEVELS.items():
        if score >= info["min"]:
            return label, info["color"]
    return "Critical", "#e74c3c"


# =============================================================================
# DATA FETCHING
# =============================================================================

@st.cache_data(ttl=3600)
def fetch_climate_history(lat: float, lon: float) -> dict:
    """Fetch 30-year temperature/precipitation from Open-Meteo Archive."""
    try:
        resp = requests.get(OPEN_METEO_ARCHIVE_API,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": "1994-01-01",
                "end_date": "2023-12-31",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            }, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Climate history error: {e}")
        return {}


@st.cache_data(ttl=3600)
def fetch_elevation_point(lat: float, lon: float) -> dict:
    """Fetch elevation for a single point from Open Topo Data."""
    try:
        resp = requests.get(OPEN_TOPO_API,
            params={"locations": f"{lat},{lon}"},
            timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            elev = results[0].get("elevation")
            return {"elevation": float(elev) if elev is not None else 0.0}
        return {"elevation": 0.0}
    except Exception as e:
        logger.warning(f"Elevation fetch error: {e}")
        return {"elevation": 0.0}


@st.cache_data(ttl=3600)
def fetch_green_infrastructure(lat: float, lon: float, radius: int = 5000) -> dict:
    """Fetch green infrastructure and drainage from Overpass API."""
    from src.overpass_client import query_overpass
    query = f"""[out:json][timeout:25];
(
  way["natural"="tree_row"](around:{radius},{lat},{lon});
  way["landuse"="forest"](around:{radius},{lat},{lon});
  way["landuse"="meadow"](around:{radius},{lat},{lon});
  way["landuse"="grass"](around:{radius},{lat},{lon});
  way["leisure"="park"](around:{radius},{lat},{lon});
  way["leisure"="garden"](around:{radius},{lat},{lon});
  way["natural"="wetland"](around:{radius},{lat},{lon});
  way["man_made"="drainage"](around:{radius},{lat},{lon});
  node["man_made"="storm_water"](around:{radius},{lat},{lon});
  way["waterway"="drain"](around:{radius},{lat},{lon});
  way["waterway"="ditch"](around:{radius},{lat},{lon});
  node["amenity"="shelter"](around:{radius},{lat},{lon});
  way["building"="shelter"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=3600)
def fetch_coastal_water_bodies(lat: float, lon: float, radius: int = 15000) -> dict:
    """Fetch coastline and large water bodies for sea level exposure."""
    from src.overpass_client import query_overpass
    query = f"""[out:json][timeout:25];
(
  way["natural"="coastline"](around:{radius},{lat},{lon});
  way["natural"="water"]["water"="sea"](around:{radius},{lat},{lon});
  way["natural"="water"]["water"="lake"](around:{radius},{lat},{lon});
  relation["natural"="water"]["water"="sea"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


# =============================================================================
# TREND COMPUTATION
# =============================================================================

@st.cache_data(ttl=3600)
def compute_annual_trends(history: dict) -> dict:
    """
    Compute annual temperature and precipitation trends from 30-year data.
    Returns annual averages, trend slopes, and warming rate per decade.
    """
    daily = history.get("daily", {}) if isinstance(history, dict) else {}
    times = daily.get("time", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])

    if not times or not t_max or not t_min:
        return {
            "years": [], "temp_means": [], "precip_totals": [],
            "temp_slope": 0.0, "precip_slope": 0.0,
            "warming_rate_decade": 0.0,
            "avg_temp": 0.0, "avg_precip": 0.0,
            "temp_std": 0.0, "precip_std": 0.0,
        }

    # Group by year
    year_temps = {}
    year_precip = {}
    for i, date_str in enumerate(times):
        if i >= len(t_max) or i >= len(t_min) or i >= len(precip):
            break
        try:
            year = int(date_str[:4])
        except (ValueError, TypeError):
            continue

        tmax_val = t_max[i]
        tmin_val = t_min[i]
        prec_val = precip[i]

        if tmax_val is not None and tmin_val is not None:
            daily_mean = (float(tmax_val) + float(tmin_val)) / 2.0
            year_temps.setdefault(year, []).append(daily_mean)

        if prec_val is not None:
            year_precip.setdefault(year, []).append(float(prec_val))

    # Compute annual averages
    years = sorted(set(year_temps.keys()) & set(year_precip.keys()))
    if not years:
        return {
            "years": [], "temp_means": [], "precip_totals": [],
            "temp_slope": 0.0, "precip_slope": 0.0,
            "warming_rate_decade": 0.0,
            "avg_temp": 0.0, "avg_precip": 0.0,
            "temp_std": 0.0, "precip_std": 0.0,
        }

    temp_means = []
    precip_totals = []
    for y in years:
        t_vals = year_temps.get(y, [])
        p_vals = year_precip.get(y, [])
        temp_means.append(round(float(np.mean(t_vals)), 2) if t_vals else 0.0)
        precip_totals.append(round(float(np.sum(p_vals)), 1) if p_vals else 0.0)

    # Linear regression for trends
    if len(years) >= 3:
        x = np.array(years, dtype=float)
        y_temp = np.array(temp_means, dtype=float)
        y_prec = np.array(precip_totals, dtype=float)

        # Temperature trend
        valid_t = ~np.isnan(y_temp)
        if valid_t.sum() >= 3:
            coeffs_t = np.polyfit(x[valid_t], y_temp[valid_t], 1)
            temp_slope = float(coeffs_t[0])
        else:
            temp_slope = 0.0

        # Precipitation trend
        valid_p = ~np.isnan(y_prec)
        if valid_p.sum() >= 3:
            coeffs_p = np.polyfit(x[valid_p], y_prec[valid_p], 1)
            precip_slope = float(coeffs_p[0])
        else:
            precip_slope = 0.0
    else:
        temp_slope = 0.0
        precip_slope = 0.0

    warming_rate_decade = round(temp_slope * 10.0, 3)

    avg_temp = round(float(np.mean(temp_means)), 2) if temp_means else 0.0
    avg_precip = round(float(np.mean(precip_totals)), 1) if precip_totals else 0.0
    temp_std = round(float(np.std(temp_means)), 2) if len(temp_means) > 1 else 0.0
    precip_std = round(float(np.std(precip_totals)), 1) if len(precip_totals) > 1 else 0.0

    return {
        "years": years,
        "temp_means": temp_means,
        "precip_totals": precip_totals,
        "temp_slope": round(temp_slope, 5),
        "precip_slope": round(precip_slope, 3),
        "warming_rate_decade": warming_rate_decade,
        "avg_temp": avg_temp,
        "avg_precip": avg_precip,
        "temp_std": temp_std,
        "precip_std": precip_std,
    }


# =============================================================================
# SOIL DATA PARSING (CORRECT ISRIC SoilGrids FORMAT)
# =============================================================================

def _parse_soil_properties(soil: dict) -> dict:
    """
    Parse ISRIC SoilGrids response safely and extract soil values.
    Returns dict with clay, sand, silt, soc, cec, phh2o, nitrogen.
    """
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l

    def _sv(name, div=10):
        p = _layer_map.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay = _sv("clay", 10)
    sand = _sv("sand", 10)
    silt = _sv("silt", 10)
    soc = _sv("soc", 10)
    cec = _sv("cec", 10)
    phh2o = _sv("phh2o", 10)
    nitrogen = _sv("nitrogen", 100)

    return {
        "clay": clay,
        "sand": sand,
        "silt": silt,
        "soc": soc,
        "cec": cec,
        "phh2o": phh2o,
        "nitrogen": nitrogen,
    }


# =============================================================================
# INFRASTRUCTURE ANALYSIS HELPERS
# =============================================================================

def _count_infrastructure(elements: list) -> dict:
    """Categorize Overpass elements into infrastructure counts."""
    counts = {
        "forest": 0,
        "park": 0,
        "garden": 0,
        "meadow": 0,
        "grass": 0,
        "wetland": 0,
        "tree_row": 0,
        "drainage": 0,
        "storm_water": 0,
        "drain_ditch": 0,
        "shelter": 0,
        "building": 0,
        "road": 0,
        "industrial": 0,
        "residential": 0,
        "total_green": 0,
        "total_water_mgmt": 0,
    }
    for el in (elements if isinstance(elements, list) else []):
        if el is None or not isinstance(el, dict):
            continue
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        landuse = tags.get("landuse", "")
        natural = tags.get("natural", "")
        leisure = tags.get("leisure", "")
        man_made = tags.get("man_made", "")
        waterway = tags.get("waterway", "")
        highway = tags.get("highway", "")
        building = tags.get("building", "")
        amenity = tags.get("amenity", "")

        if landuse == "forest":
            counts["forest"] += 1
        if landuse == "meadow":
            counts["meadow"] += 1
        if landuse == "grass":
            counts["grass"] += 1
        if landuse == "industrial":
            counts["industrial"] += 1
        if landuse == "residential":
            counts["residential"] += 1
        if leisure == "park":
            counts["park"] += 1
        if leisure == "garden":
            counts["garden"] += 1
        if natural == "wetland":
            counts["wetland"] += 1
        if natural == "tree_row":
            counts["tree_row"] += 1
        if man_made == "drainage":
            counts["drainage"] += 1
        if man_made == "storm_water":
            counts["storm_water"] += 1
        if waterway in ("drain", "ditch"):
            counts["drain_ditch"] += 1
        if amenity == "shelter" or building == "shelter":
            counts["shelter"] += 1
        if building and building != "shelter":
            counts["building"] += 1
        if highway in ("motorway", "trunk", "primary", "secondary", "tertiary"):
            counts["road"] += 1

    counts["total_green"] = (
        counts["forest"] + counts["park"] + counts["garden"]
        + counts["meadow"] + counts["grass"] + counts["wetland"]
        + counts["tree_row"]
    )
    counts["total_water_mgmt"] = (
        counts["drainage"] + counts["storm_water"] + counts["drain_ditch"]
    )
    return counts


# =============================================================================
# CORE RESILIENCE COMPUTATION
# =============================================================================

@st.cache_data(ttl=3600)
def compute_climate_adaptation(lat: float, lon: float) -> dict:
    """
    Compute climate adaptation resilience across 6 dimensions.
    Each dimension scored 0-100 (higher = more resilient).
    """
    # -- Fetch all data sources -------------------------------------------------
    history = fetch_climate_history(lat, lon)
    weather = fetch_weather_data(lat, lon)
    soil = fetch_soil_data(lat, lon)
    elevation_data = fetch_elevation_point(lat, lon)
    water = fetch_water_features(lat, lon, radius=5000)
    infra = fetch_landuse_infrastructure(lat, lon, radius=3000)
    green_infra = fetch_green_infrastructure(lat, lon, radius=5000)
    protected = fetch_protected_areas(lat, lon, radius=10000)
    coastal = fetch_coastal_water_bodies(lat, lon, radius=15000)

    # -- Parse data safely ------------------------------------------------------
    trends = compute_annual_trends(history)
    soil_props = _parse_soil_properties(soil)
    current_wx = (weather if isinstance(weather, dict) else {}).get("current", {})
    if not isinstance(current_wx, dict):
        current_wx = {}
    daily_wx = (weather if isinstance(weather, dict) else {}).get("daily", {})
    if not isinstance(daily_wx, dict):
        daily_wx = {}

    elevation = elevation_data.get("elevation", 0.0)

    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    infra_elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    green_elements = (green_infra if isinstance(green_infra, dict) else {}).get("elements", [])
    protected_elements = (protected if isinstance(protected, dict) else {}).get("elements", [])
    coastal_elements = (coastal if isinstance(coastal, dict) else {}).get("elements", [])

    # Combine infrastructure elements for counting
    all_green_infra = _count_infrastructure(green_elements)
    all_infra = _count_infrastructure(infra_elements)

    # Current weather values
    current_temp = current_wx.get("temperature_2m")
    if current_temp is not None:
        current_temp = float(current_temp)
    else:
        current_temp = trends.get("avg_temp", 15.0)

    wind_speed = current_wx.get("wind_speed_10m")
    if wind_speed is not None:
        wind_speed = float(wind_speed)
    else:
        wind_speed = 10.0

    humidity = current_wx.get("relative_humidity_2m")
    if humidity is not None:
        humidity = float(humidity)
    else:
        humidity = 50.0

    # Soil values with safe defaults
    clay_pct = soil_props.get("clay") if soil_props.get("clay") is not None else 25.0
    sand_pct = soil_props.get("sand") if soil_props.get("sand") is not None else 40.0
    soc_val = soil_props.get("soc") if soil_props.get("soc") is not None else 15.0
    cec_val = soil_props.get("cec") if soil_props.get("cec") is not None else 15.0

    warming_rate = trends.get("warming_rate_decade", 0.0)
    avg_precip = trends.get("avg_precip", 500.0)
    precip_std = trends.get("precip_std", 100.0)

    # Water feature counts
    water_count = len([e for e in water_elements if e is not None])
    protected_count = len([e for e in protected_elements if e is not None])
    coastal_count = len([e for e in coastal_elements if e is not None])

    # =========================================================================
    # DIMENSION 1: Heat Resilience (0-100)
    # Factors: warming rate, current temp deviation, urban heat island, green space
    # =========================================================================
    # Warming rate penalty: faster warming = lower resilience
    if warming_rate <= 0.1:
        warming_penalty = 0
    elif warming_rate <= 0.2:
        warming_penalty = 10
    elif warming_rate <= 0.35:
        warming_penalty = 20
    elif warming_rate <= 0.5:
        warming_penalty = 35
    else:
        warming_penalty = min(warming_rate * 80, 50)

    # Current temperature deviation from comfortable range (18-25C)
    if 18 <= current_temp <= 25:
        temp_deviation_penalty = 0
    elif current_temp > 25:
        temp_deviation_penalty = min((current_temp - 25) * 3, 30)
    else:
        temp_deviation_penalty = min((18 - current_temp) * 1.5, 20)

    # Urban heat island indicator: high building density + low green
    uhi_ratio = (all_infra.get("building", 0) + 1) / (all_green_infra.get("total_green", 0) + 1)
    uhi_penalty = min(uhi_ratio * 3, 25) if uhi_ratio > 2 else 0

    # Green space cooling bonus
    green_cooling = min(all_green_infra.get("total_green", 0) * 2.5, 30)

    heat_resilience = _clamp(85 - warming_penalty - temp_deviation_penalty - uhi_penalty + green_cooling)

    # =========================================================================
    # DIMENSION 2: Drought Resilience (0-100)
    # Factors: precipitation reliability, water infrastructure, soil water retention
    # =========================================================================
    # Precipitation reliability (low std relative to mean = reliable)
    precip_cv = (precip_std / avg_precip) if avg_precip > 0 else 1.0
    if precip_cv <= 0.1:
        precip_reliability = 40
    elif precip_cv <= 0.2:
        precip_reliability = 30
    elif precip_cv <= 0.3:
        precip_reliability = 20
    else:
        precip_reliability = max(0, 40 - precip_cv * 60)

    # Water infrastructure (wells, springs, waterways)
    water_infra_score = min(water_count * 3.0, 25)

    # Soil water retention: clay + organic carbon = retention capacity
    soil_retention = min((clay_pct * 0.4 + soc_val * 0.6 + cec_val * 0.3), 35)

    drought_resilience = _clamp(precip_reliability + water_infra_score + soil_retention)

    # =========================================================================
    # DIMENSION 3: Flood Adaptation (0-100)
    # Factors: elevation, drainage infra, permeable surfaces, wetlands
    # =========================================================================
    # Elevation bonus (higher = safer from flooding)
    if elevation >= 500:
        elev_flood_bonus = 30
    elif elevation >= 200:
        elev_flood_bonus = 25
    elif elevation >= 50:
        elev_flood_bonus = 15
    elif elevation >= 10:
        elev_flood_bonus = 8
    else:
        elev_flood_bonus = 0

    # Drainage infrastructure
    drainage_score = min(all_green_infra.get("total_water_mgmt", 0) * 5, 25)

    # Permeable surface ratio (green vs built)
    total_built = all_infra.get("building", 0) + all_infra.get("road", 0)
    total_perm = all_green_infra.get("total_green", 0) + all_green_infra.get("wetland", 0)
    if (total_built + total_perm) > 0:
        permeable_ratio = total_perm / (total_built + total_perm)
    else:
        permeable_ratio = 0.5
    permeable_score = permeable_ratio * 25

    # Sand content helps drainage
    sand_drainage = min(sand_pct * 0.2, 10)

    # Wetland buffer
    wetland_bonus = min(all_green_infra.get("wetland", 0) * 5, 10)

    flood_adaptation = _clamp(elev_flood_bonus + drainage_score + permeable_score + sand_drainage + wetland_bonus)

    # =========================================================================
    # DIMENSION 4: Storm Resilience (0-100)
    # Factors: wind exposure, shelter availability, infrastructure robustness
    # =========================================================================
    # Wind exposure (lower current wind = less exposed)
    if wind_speed <= 10:
        wind_score = 35
    elif wind_speed <= 20:
        wind_score = 25
    elif wind_speed <= 30:
        wind_score = 15
    elif wind_speed <= 50:
        wind_score = 5
    else:
        wind_score = 0

    # Shelter availability
    shelter_count = all_green_infra.get("shelter", 0)
    shelter_score = min(shelter_count * 8, 25)

    # Infrastructure robustness (buildings provide wind break)
    building_count = all_infra.get("building", 0)
    infra_robustness = min(building_count * 0.3, 20)

    # Forest windbreak
    forest_windbreak = min(all_green_infra.get("forest", 0) * 3, 15)

    # Elevation penalty for exposed ridges
    elev_exposure = 0
    if elevation > 800:
        elev_exposure = min((elevation - 800) * 0.01, 10)

    storm_resilience = _clamp(wind_score + shelter_score + infra_robustness + forest_windbreak - elev_exposure + 5)

    # =========================================================================
    # DIMENSION 5: Sea Level Exposure (0-100, 100 = safe/not exposed)
    # Factors: elevation above sea level, coastal proximity
    # =========================================================================
    # Elevation-based safety
    if elevation >= 100:
        elev_safety = 70
    elif elevation >= 50:
        elev_safety = 55
    elif elevation >= 20:
        elev_safety = 40
    elif elevation >= 10:
        elev_safety = 25
    elif elevation >= 5:
        elev_safety = 15
    elif elevation >= 2:
        elev_safety = 8
    else:
        elev_safety = 2

    # Coastal proximity penalty (more coastal features nearby = more exposed)
    if coastal_count == 0:
        coastal_bonus = 30
    elif coastal_count <= 2:
        coastal_bonus = 15
    elif coastal_count <= 5:
        coastal_bonus = 5
    else:
        coastal_bonus = 0

    sea_level_exposure = _clamp(elev_safety + coastal_bonus)

    # =========================================================================
    # DIMENSION 6: Ecosystem Adaptation (0-100)
    # Factors: biodiversity buffer, protected areas, forest cover
    # =========================================================================
    # Protected area coverage
    protected_score = min(protected_count * 6, 30)

    # Forest cover
    forest_cover = min(all_green_infra.get("forest", 0) * 4, 25)

    # Biodiversity buffer (variety of green types)
    green_types = sum([
        1 if all_green_infra.get("forest", 0) > 0 else 0,
        1 if all_green_infra.get("park", 0) > 0 else 0,
        1 if all_green_infra.get("meadow", 0) > 0 else 0,
        1 if all_green_infra.get("wetland", 0) > 0 else 0,
        1 if all_green_infra.get("garden", 0) > 0 else 0,
        1 if all_green_infra.get("tree_row", 0) > 0 else 0,
        1 if all_green_infra.get("grass", 0) > 0 else 0,
    ])
    biodiversity_buffer = min(green_types * 5, 25)

    # Soil health (organic carbon + nitrogen indicate healthy ecosystem)
    nitrogen_val = soil_props.get("nitrogen") if soil_props.get("nitrogen") is not None else 1.0
    soil_health = min((soc_val * 0.3 + nitrogen_val * 5), 20)

    ecosystem_adaptation = _clamp(protected_score + forest_cover + biodiversity_buffer + soil_health)

    # =========================================================================
    # OVERALL SCORE (weighted average)
    # =========================================================================
    dimensions = {
        "Heat Resilience": round(heat_resilience, 1),
        "Drought Resilience": round(drought_resilience, 1),
        "Flood Adaptation": round(flood_adaptation, 1),
        "Storm Resilience": round(storm_resilience, 1),
        "Sea Level Exposure": round(sea_level_exposure, 1),
        "Ecosystem Adaptation": round(ecosystem_adaptation, 1),
    }

    weights = {
        "Heat Resilience": 0.20,
        "Drought Resilience": 0.20,
        "Flood Adaptation": 0.18,
        "Storm Resilience": 0.15,
        "Sea Level Exposure": 0.12,
        "Ecosystem Adaptation": 0.15,
    }

    overall = sum(dimensions[k] * weights[k] for k in DIMENSION_LABELS)
    overall = round(_clamp(overall), 1)

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================
    recommendations = []

    if heat_resilience < 50:
        recommendations.append(
            "Heat vulnerability detected. Increase urban tree canopy, install "
            "cool roofs, and establish cooling centers for heat events."
        )
    if drought_resilience < 50:
        recommendations.append(
            "Drought risk is elevated. Invest in rainwater harvesting, "
            "water recycling infrastructure, and drought-resistant landscaping."
        )
    if flood_adaptation < 50:
        recommendations.append(
            "Flood exposure is significant. Improve stormwater drainage, "
            "expand permeable surfaces, and protect/restore wetland buffers."
        )
    if storm_resilience < 50:
        recommendations.append(
            "Storm resilience is low. Establish shelter networks, plant "
            "windbreak forests, and reinforce critical infrastructure."
        )
    if sea_level_exposure < 50:
        recommendations.append(
            "Sea level rise risk present. Evaluate coastal defenses, "
            "consider managed retreat strategies, and build elevated infrastructure."
        )
    if ecosystem_adaptation < 50:
        recommendations.append(
            "Ecosystem buffer is weak. Expand protected areas, restore "
            "native habitats, and support reforestation programs."
        )
    if warming_rate > 0.3:
        recommendations.append(
            f"Warming rate of {warming_rate:.2f} C/decade exceeds global average. "
            "Prioritize heat adaptation strategies and monitor climate projections."
        )
    if not recommendations:
        recommendations.append(
            "Climate resilience is generally favorable. Continue monitoring "
            "trends and maintain existing green infrastructure."
        )

    return {
        "overall_score": overall,
        "dimensions": dimensions,
        "trends": trends,
        "elevation": elevation,
        "soil_props": soil_props,
        "current_temp": current_temp,
        "wind_speed": wind_speed,
        "humidity": humidity,
        "warming_rate": warming_rate,
        "green_infra_counts": all_green_infra,
        "infra_counts": all_infra,
        "water_feature_count": water_count,
        "protected_area_count": protected_count,
        "coastal_feature_count": coastal_count,
        "recommendations": recommendations,
    }


# =============================================================================
# RENDERING
# =============================================================================

def render_climate_adaptation_tab() -> None:
    """Render the Climate Adaptation AI tab in Streamlit."""
    st.markdown(
        "<h2 style='color:#10b981;'>Climate Adaptation AI</h2>"
        "<p style='color:#8b97b0;'>Climate change resilience assessment across 6 "
        "dimensions using 30-year historical trends, soil data, terrain, and "
        "green infrastructure analysis.</p>",
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------------
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="climate_adapt_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="climate_adapt_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="climate_adapt_lon",
        )

    run = st.button(
        "Assess Climate Resilience", type="primary",
        key="climate_adapt_run", use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Assess Climate Resilience** to generate "
            "a comprehensive climate adaptation report with 30-year trend analysis."
        )
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching 30-year climate data and analyzing resilience..."):
        result = compute_climate_adaptation(lat, lon)

    overall = result["overall_score"]
    dims = result["dimensions"]
    trends = result["trends"]
    recs = result["recommendations"]
    warming_rate = result["warming_rate"]

    classification, class_color = _classify_resilience(overall)

    # -- Overall score header --------------------------------------------------
    st.markdown(
        f"<div style='background:#1a1a2e;padding:20px;border-radius:12px;"
        f"border-left:5px solid {class_color};margin-bottom:16px;'>"
        f"<h1 style='color:{class_color};margin:0;'>{overall} / 100</h1>"
        f"<h3 style='color:{class_color};margin:4px 0 8px 0;'>"
        f"Climate Resilience: {classification}</h3>"
        f"<p style='color:#ccc;margin:0;font-size:0.95em;'>"
        f"Location: {lat:.4f}, {lon:.4f} | "
        f"Elevation: {result['elevation']:.0f} m | "
        f"Warming: {warming_rate:+.2f} C/decade</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # -- Key metrics row -------------------------------------------------------
    st.markdown("### Key Climate Indicators")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="Warming Rate",
            value=f"{warming_rate:+.2f} C/dec",
        )
    with m2:
        st.metric(
            label="Current Temp",
            value=f"{result['current_temp']:.1f} C",
        )
    with m3:
        st.metric(
            label="Avg Precip/yr",
            value=f"{trends.get('avg_precip', 0):.0f} mm",
        )
    with m4:
        st.metric(
            label="Elevation",
            value=f"{result['elevation']:.0f} m",
        )

    # -- 6 Dimension Cards -----------------------------------------------------
    st.markdown("### Resilience Dimensions")
    dim_cols = st.columns(3)
    for i, (label, score) in enumerate(dims.items()):
        with dim_cols[i % 3]:
            dim_color = DIMENSION_COLORS.get(label, "#06b6d4")
            dim_level, _ = _classify_resilience(score)
            st.markdown(
                f"<div style='background:#1a1a2e;padding:14px;border-radius:10px;"
                f"margin-bottom:10px;'>"
                f"<p style='color:#8b97b0;margin:0 0 4px 0;font-size:0.85em;'>"
                f"{label}</p>"
                f"<h3 style='color:{dim_color};margin:0;'>{score}</h3>"
                f"<div style='background:#2a2a3e;border-radius:6px;height:8px;"
                f"margin-top:6px;'>"
                f"<div style='background:{dim_color};width:{score}%;"
                f"height:8px;border-radius:6px;'></div></div>"
                f"<p style='color:#8b97b0;margin:4px 0 0 0;font-size:0.75em;'>"
                f"{dim_level}</p></div>",
                unsafe_allow_html=True,
            )

    # -- Radar Chart -----------------------------------------------------------
    st.markdown("### Resilience Profile")
    radar_values = [dims[k] for k in DIMENSION_LABELS]
    radar_values_closed = radar_values + [radar_values[0]]
    labels_closed = DIMENSION_LABELS + [DIMENSION_LABELS[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(16,185,129,0.2)",
        line=dict(color="#10b981", width=2),
        name="Resilience",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2a2a3e", tickfont=dict(color="#8b97b0"),
            ),
            angularaxis=dict(
                gridcolor="#2a2a3e", tickfont=dict(color="#ccc", size=11),
            ),
        ),
        paper_bgcolor="#0e0e1a",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#ccc"),
        showlegend=False,
        height=420,
        margin=dict(t=30, b=30, l=60, r=60),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="cliada_pchart1")

    # -- Temperature Trend (30 years) ------------------------------------------
    years = trends.get("years", [])
    temp_means = trends.get("temp_means", [])
    precip_totals = trends.get("precip_totals", [])

    if years and temp_means:
        st.markdown("### Temperature Trend (30-Year)")
        fig_temp = go.Figure()

        # Annual mean temperatures
        fig_temp.add_trace(go.Scatter(
            x=years,
            y=temp_means,
            mode="lines+markers",
            name="Annual Mean Temp",
            line=dict(color="#ef4444", width=2),
            marker=dict(size=4, color="#ef4444"),
        ))

        # Trend line
        temp_slope = trends.get("temp_slope", 0)
        if len(years) >= 2 and temp_slope != 0:
            x_arr = np.array(years, dtype=float)
            y_arr = np.array(temp_means, dtype=float)
            valid = ~np.isnan(y_arr)
            if valid.sum() >= 2:
                coeffs = np.polyfit(x_arr[valid], y_arr[valid], 1)
                trend_y = [coeffs[0] * x + coeffs[1] for x in years]
                fig_temp.add_trace(go.Scatter(
                    x=years,
                    y=trend_y,
                    mode="lines",
                    name=f"Trend ({warming_rate:+.2f} C/decade)",
                    line=dict(color="#f59e0b", width=2, dash="dash"),
                ))

        fig_temp.update_layout(
            paper_bgcolor="#0e0e1a",
            plot_bgcolor="#1a1a2e",
            font=dict(color="#ccc"),
            xaxis=dict(
                title="Year", gridcolor="#2a2a3e",
                tickfont=dict(color="#8b97b0"),
            ),
            yaxis=dict(
                title="Temperature (C)", gridcolor="#2a2a3e",
                tickfont=dict(color="#8b97b0"),
            ),
            height=380,
            margin=dict(t=30, b=40, l=60, r=30),
            legend=dict(
                bgcolor="rgba(26,26,46,0.8)",
                font=dict(color="#ccc"),
            ),
        )
        st.plotly_chart(fig_temp, use_container_width=True, key="cliada_pchart2")

    # -- Precipitation Trend ---------------------------------------------------
    if years and precip_totals:
        st.markdown("### Precipitation Trend (30-Year)")
        fig_precip = go.Figure()

        fig_precip.add_trace(go.Bar(
            x=years,
            y=precip_totals,
            name="Annual Precipitation",
            marker_color="#3b82f6",
            opacity=0.7,
        ))

        # Trend line for precipitation
        precip_slope = trends.get("precip_slope", 0)
        if len(years) >= 2 and precip_slope != 0:
            x_arr = np.array(years, dtype=float)
            y_arr = np.array(precip_totals, dtype=float)
            valid = ~np.isnan(y_arr)
            if valid.sum() >= 2:
                coeffs = np.polyfit(x_arr[valid], y_arr[valid], 1)
                trend_y = [coeffs[0] * x + coeffs[1] for x in years]
                fig_precip.add_trace(go.Scatter(
                    x=years,
                    y=trend_y,
                    mode="lines",
                    name=f"Trend ({precip_slope:+.1f} mm/yr)",
                    line=dict(color="#f59e0b", width=2, dash="dash"),
                ))

        fig_precip.update_layout(
            paper_bgcolor="#0e0e1a",
            plot_bgcolor="#1a1a2e",
            font=dict(color="#ccc"),
            xaxis=dict(
                title="Year", gridcolor="#2a2a3e",
                tickfont=dict(color="#8b97b0"),
            ),
            yaxis=dict(
                title="Precipitation (mm)", gridcolor="#2a2a3e",
                tickfont=dict(color="#8b97b0"),
            ),
            height=380,
            margin=dict(t=30, b=40, l=60, r=30),
            legend=dict(
                bgcolor="rgba(26,26,46,0.8)",
                font=dict(color="#ccc"),
            ),
        )
        st.plotly_chart(fig_precip, use_container_width=True, key="cliada_pchart3")

    # -- Warming rate highlight metric -----------------------------------------
    st.markdown("### Climate Change Signal")
    sig1, sig2, sig3 = st.columns(3)
    with sig1:
        st.metric(
            label="Warming Rate (C/decade)",
            value=f"{warming_rate:+.3f}",
        )
    with sig2:
        st.metric(
            label="Temp Variability (std)",
            value=f"{trends.get('temp_std', 0):.2f} C",
        )
    with sig3:
        st.metric(
            label="Precip Variability (std)",
            value=f"{trends.get('precip_std', 0):.0f} mm",
        )

    # -- Infrastructure summary ------------------------------------------------
    st.markdown("### Infrastructure & Environment")
    inf1, inf2 = st.columns(2)

    green = result["green_infra_counts"]
    infra_c = result["infra_counts"]

    with inf1:
        st.markdown(
            "<div style='background:#1a1a2e;padding:16px;border-radius:10px;'>"
            "<h4 style='color:#10b981;margin:0 0 10px 0;'>Green Infrastructure</h4>",
            unsafe_allow_html=True,
        )
        green_items = [
            f"<p style='color:#ccc;margin:2px 0;'>Forests: <b>{green.get('forest', 0)}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Parks: <b>{green.get('park', 0)}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Meadows/Grass: <b>{green.get('meadow', 0) + green.get('grass', 0)}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Wetlands: <b>{green.get('wetland', 0)}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Gardens: <b>{green.get('garden', 0)}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Tree rows: <b>{green.get('tree_row', 0)}</b></p>",
            f"<p style='color:#10b981;margin:6px 0 0 0;font-weight:bold;'>Total green: {green.get('total_green', 0)}</p>",
        ]
        st.markdown("".join(green_items) + "</div>", unsafe_allow_html=True)

    with inf2:
        st.markdown(
            "<div style='background:#1a1a2e;padding:16px;border-radius:10px;'>"
            "<h4 style='color:#3b82f6;margin:0 0 10px 0;'>Water & Protection</h4>",
            unsafe_allow_html=True,
        )
        water_items = [
            f"<p style='color:#ccc;margin:2px 0;'>Water features: <b>{result['water_feature_count']}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Drainage systems: <b>{green.get('total_water_mgmt', 0)}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Shelters: <b>{green.get('shelter', 0)}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Protected areas: <b>{result['protected_area_count']}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Coastal features: <b>{result['coastal_feature_count']}</b></p>",
            f"<p style='color:#ccc;margin:2px 0;'>Buildings: <b>{infra_c.get('building', 0)}</b></p>",
            f"<p style='color:#3b82f6;margin:6px 0 0 0;font-weight:bold;'>Elevation: {result['elevation']:.0f} m</p>",
        ]
        st.markdown("".join(water_items) + "</div>", unsafe_allow_html=True)

    # -- Soil properties -------------------------------------------------------
    st.markdown("### Soil Resilience Factors")
    sp = result["soil_props"]
    soil_items = {
        "Clay": (sp.get("clay"), "%"),
        "Sand": (sp.get("sand"), "%"),
        "Silt": (sp.get("silt"), "%"),
        "Organic Carbon": (sp.get("soc"), "g/kg"),
        "CEC": (sp.get("cec"), "cmol/kg"),
        "pH": (sp.get("phh2o"), ""),
        "Nitrogen": (sp.get("nitrogen"), "g/kg"),
    }
    valid_soil = {k: v for k, v in soil_items.items() if v[0] is not None}
    if valid_soil:
        soil_cols = st.columns(min(len(valid_soil), 4))
        for i, (name, (val, unit)) in enumerate(valid_soil.items()):
            with soil_cols[i % len(soil_cols)]:
                display_val = f"{val:.1f} {unit}".strip()
                st.metric(label=name, value=display_val)
    else:
        st.caption("Soil data not available for this location.")

    # -- Recommendations -------------------------------------------------------
    st.markdown("### Adaptation Recommendations")
    for rec in recs:
        st.markdown(
            f"<div style='background:#1a1a2e;padding:12px 16px;"
            f"border-radius:8px;margin-bottom:8px;border-left:3px solid #10b981;'>"
            f"<p style='color:#ccc;margin:0;'>{rec}</p></div>",
            unsafe_allow_html=True,
        )
