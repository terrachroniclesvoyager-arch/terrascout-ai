"""
apex_data_sources.py - Apex-tier data sources for TerraScout AI.

Fetches data from 5 free APIs (no API keys required):
    A. Open-Meteo Climate Change Projections (CMIP6)
    B. Smithsonian Global Volcanism Program (GVP-VOTW)
    C. Open-Meteo Historical Archive (ERA5 Reanalysis)
    D. Open-Meteo Soil Moisture Profile
    E. Open-Meteo UV & Pollen Index

Each function is cached with st.cache_data and returns a structured dict.
The aggregator fetch_all_apex_sources() wraps each call in its own try/except.
"""

import logging
import math
import statistics
from datetime import datetime

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper: Haversine distance
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two lat/lon points."""
    R = 6371.0  # Earth radius in km
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# A. Open-Meteo Climate Change Projections (CMIP6)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_climate_projections(lat: float, lon: float) -> dict:
    """Fetch CMIP6 climate projections for 2050 from Open-Meteo Climate API.

    Returns ensemble statistics across 7 high-resolution climate models for
    temperature, precipitation, and wind speed under SSP3-7.0.
    """
    result = {
        "models": {},
        "ensemble_avg_temp": 0.0,
        "ensemble_total_precip": 0.0,
        "temp_spread": 0.0,
        "precip_spread": 0.0,
        "scenario": "SSP3-7.0",
    }
    models = [
        "CMCC_CM2_VHR4",
        "FGOALS_f3_H",
        "HiRAM_SIT_HR",
        "MRI_AGCM3_2_S",
        "EC_Earth3P_HR",
        "MPI_ESM1_2_XR",
        "NICAM16_8S",
    ]
    try:
        resp = requests.get(
            "https://climate-api.open-meteo.com/v1/climate",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": "2050-01-01",
                "end_date": "2050-12-31",
                "models": ",".join(models),
                "daily": "temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Climate projections API error: %s", exc)
        return result

    # The API may return per-model keys like "temperature_2m_mean_CMCC_CM2_VHR4"
    # or a single "daily" block when only one model responds.
    daily = data.get("daily", {}) if isinstance(data, dict) else {}

    temp_avgs = []
    precip_totals = []

    for model in models:
        # Try model-suffixed keys first, then plain keys as fallback
        temp_key = f"temperature_2m_mean_{model}"
        precip_key = f"precipitation_sum_{model}"
        wind_key = f"wind_speed_10m_max_{model}"

        temps = daily.get(temp_key, daily.get("temperature_2m_mean", []))
        precips = daily.get(precip_key, daily.get("precipitation_sum", []))
        winds = daily.get(wind_key, daily.get("wind_speed_10m_max", []))

        # Filter out None values for safe computation
        valid_temps = [v for v in (temps or []) if v is not None]
        valid_precips = [v for v in (precips or []) if v is not None]
        valid_winds = [v for v in (winds or []) if v is not None]

        avg_temp = statistics.mean(valid_temps) if valid_temps else 0.0
        total_precip = sum(valid_precips) if valid_precips else 0.0
        avg_wind = statistics.mean(valid_winds) if valid_winds else 0.0

        result["models"][model] = {
            "avg_temp": round(avg_temp, 2),
            "total_precip": round(total_precip, 1),
            "avg_wind": round(avg_wind, 2),
        }

        if valid_temps:
            temp_avgs.append(avg_temp)
        if valid_precips:
            precip_totals.append(total_precip)

    if temp_avgs:
        result["ensemble_avg_temp"] = round(statistics.mean(temp_avgs), 2)
        result["temp_spread"] = round(max(temp_avgs) - min(temp_avgs), 2)
    if precip_totals:
        result["ensemble_total_precip"] = round(statistics.mean(precip_totals), 1)
        result["precip_spread"] = round(max(precip_totals) - min(precip_totals), 1)

    logger.info(
        "Climate projections fetched for (%.4f, %.4f): %d models, ensemble temp %.1f C",
        lat, lon, len(result["models"]), result["ensemble_avg_temp"],
    )
    return result


# ---------------------------------------------------------------------------
# B. Smithsonian Global Volcanism Program
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_volcano_proximity(lat: float, lon: float, radius_km: float = 200) -> dict:
    """Fetch nearby Holocene volcanoes from the Smithsonian GVP-VOTW WFS service.

    Returns a list of volcanoes within *radius_km*, sorted by distance,
    along with a hazard level classification.
    """
    result = {
        "volcanoes": [],
        "nearest_km": None,
        "count": 0,
        "hazard_level": "LOW",
    }

    # Convert radius to approximate degree offset (1 degree ~ 111 km)
    offset = radius_km / 111.0

    bbox_filter = (
        f"BBOX(GeoLocation,{lon - offset},{lat - offset},{lon + offset},{lat + offset})"
    )

    try:
        resp = requests.get(
            "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows",
            params={
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes",
                "outputFormat": "application/json",
                "CQL_FILTER": bbox_filter,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Volcano proximity API error: %s", exc)
        return result

    features = data.get("features", []) if isinstance(data, dict) else []

    volcanoes = []
    for feat in features:
        if not isinstance(feat, dict):
            continue
        props = feat.get("properties", {}) or {}
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates", []) if isinstance(geom, dict) else []

        # GeoJSON coordinates are [lon, lat]
        if not coords or len(coords) < 2:
            continue

        vlat = coords[1] if coords[1] is not None else 0.0
        vlon = coords[0] if coords[0] is not None else 0.0
        dist = _haversine(lat, lon, vlat, vlon)

        # Only include volcanoes within the actual radius (BBOX is approximate)
        if dist > radius_km:
            continue

        volcanoes.append({
            "name": props.get("Volcano_Name", "Unknown"),
            "type": props.get("Volcano_Type", "Unknown"),
            "last_eruption_year": props.get("Last_Eruption_Year", "Unknown"),
            "elevation_m": props.get("Elevation", 0) or 0,
            "distance_km": round(dist, 1),
            "lat": round(vlat, 5),
            "lon": round(vlon, 5),
        })

    volcanoes.sort(key=lambda v: v["distance_km"])

    result["volcanoes"] = volcanoes
    result["count"] = len(volcanoes)

    if volcanoes:
        nearest = volcanoes[0]["distance_km"]
        result["nearest_km"] = nearest
        if nearest < 30:
            result["hazard_level"] = "CRITICAL"
        elif nearest < 100:
            result["hazard_level"] = "HIGH"
        elif nearest < 200:
            result["hazard_level"] = "MODERATE"
        else:
            result["hazard_level"] = "LOW"

    logger.info(
        "Volcano proximity for (%.4f, %.4f): %d volcanoes, nearest %.1f km, hazard %s",
        lat, lon, result["count"],
        result["nearest_km"] if result["nearest_km"] is not None else -1,
        result["hazard_level"],
    )
    return result


# ---------------------------------------------------------------------------
# C. Open-Meteo Historical Archive (ERA5 Reanalysis)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_climate_normals(lat: float, lon: float) -> dict:
    """Fetch ERA5 reanalysis data for the previous full year and compute monthly statistics.

    Returns monthly averages for temperature (max/min), precipitation,
    and summary statistics (hottest/coldest/wettest/driest month, annual totals).
    """
    # Use the previous full year
    prev_year = datetime.now().year - 1
    start_date = f"{prev_year}-01-01"
    end_date = f"{prev_year}-12-31"

    result = {
        "monthly_temp_max": [0.0] * 12,
        "monthly_temp_min": [0.0] * 12,
        "monthly_precip": [0.0] * 12,
        "annual_temp_avg": 0.0,
        "annual_precip_total": 0.0,
        "annual_wind_max": 0.0,
        "hottest_month": 1,
        "coldest_month": 1,
        "wettest_month": 1,
        "driest_month": 1,
        "temp_range": 0.0,
    }

    try:
        resp = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "timezone": "auto",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Climate normals API error: %s", exc)
        return result

    daily = data.get("daily", {}) if isinstance(data, dict) else {}
    dates = daily.get("time", []) or []
    temp_maxes = daily.get("temperature_2m_max", []) or []
    temp_mins = daily.get("temperature_2m_min", []) or []
    precips = daily.get("precipitation_sum", []) or []
    winds = daily.get("wind_speed_10m_max", []) or []

    # Bucket daily values into months (0-indexed)
    monthly_tmax = [[] for _ in range(12)]
    monthly_tmin = [[] for _ in range(12)]
    monthly_prec = [[] for _ in range(12)]
    all_winds = []

    for i, date_str in enumerate(dates):
        try:
            month_idx = int(date_str.split("-")[1]) - 1  # 0-indexed
        except (IndexError, ValueError):
            continue

        if i < len(temp_maxes) and temp_maxes[i] is not None:
            monthly_tmax[month_idx].append(temp_maxes[i])
        if i < len(temp_mins) and temp_mins[i] is not None:
            monthly_tmin[month_idx].append(temp_mins[i])
        if i < len(precips) and precips[i] is not None:
            monthly_prec[month_idx].append(precips[i])
        if i < len(winds) and winds[i] is not None:
            all_winds.append(winds[i])

    # Compute monthly averages
    for m in range(12):
        if monthly_tmax[m]:
            result["monthly_temp_max"][m] = round(statistics.mean(monthly_tmax[m]), 1)
        if monthly_tmin[m]:
            result["monthly_temp_min"][m] = round(statistics.mean(monthly_tmin[m]), 1)
        if monthly_prec[m]:
            result["monthly_precip"][m] = round(sum(monthly_prec[m]), 1)

    # Annual statistics
    all_tmax = result["monthly_temp_max"]
    all_tmin = result["monthly_temp_min"]
    all_prec = result["monthly_precip"]

    valid_maxes = [v for v in all_tmax if v != 0.0 or any(monthly_tmax[i] for i, x in enumerate(all_tmax) if x == 0.0)]
    valid_mins = [v for v in all_tmin if v != 0.0 or any(monthly_tmin[i] for i, x in enumerate(all_tmin) if x == 0.0)]

    # Use the simple averages of monthly values
    if any(monthly_tmax[m] for m in range(12)):
        avg_max = statistics.mean(all_tmax)
        avg_min = statistics.mean(all_tmin)
        result["annual_temp_avg"] = round((avg_max + avg_min) / 2, 1)

    result["annual_precip_total"] = round(sum(all_prec), 1)
    result["annual_wind_max"] = round(max(all_winds), 1) if all_winds else 0.0

    # Identify extreme months (1-indexed)
    # For temperature, use the average of max and min per month
    monthly_avg_temp = [
        (result["monthly_temp_max"][m] + result["monthly_temp_min"][m]) / 2
        for m in range(12)
    ]

    result["hottest_month"] = monthly_avg_temp.index(max(monthly_avg_temp)) + 1
    result["coldest_month"] = monthly_avg_temp.index(min(monthly_avg_temp)) + 1
    result["wettest_month"] = all_prec.index(max(all_prec)) + 1
    result["driest_month"] = all_prec.index(min(all_prec)) + 1
    result["temp_range"] = round(max(all_tmax) - min(all_tmin), 1)

    logger.info(
        "Climate normals for (%.4f, %.4f): annual avg %.1f C, precip %.0f mm",
        lat, lon, result["annual_temp_avg"], result["annual_precip_total"],
    )
    return result


# ---------------------------------------------------------------------------
# D. Open-Meteo Soil Moisture Profile
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def fetch_soil_moisture_profile(lat: float, lon: float) -> dict:
    """Fetch current soil moisture and temperature at multiple depths.

    Returns moisture values (m3/m3), temperatures (C), and a qualitative
    moisture trend classification.
    """
    result = {
        "moisture_0_7cm": 0.0,
        "moisture_7_28cm": 0.0,
        "moisture_28_100cm": 0.0,
        "moisture_100_255cm": 0.0,
        "temp_0_7cm": 0.0,
        "temp_28_100cm": 0.0,
        "moisture_avg": 0.0,
        "moisture_trend": "dry",
        "profile_gradient": 0.0,
    }

    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": (
                    "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,"
                    "soil_moisture_28_to_100cm,soil_moisture_100_to_255cm,"
                    "soil_temperature_0_to_7cm,soil_temperature_28_to_100cm"
                ),
                "forecast_days": 1,
                "timezone": "auto",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Soil moisture API error: %s", exc)
        return result

    hourly = data.get("hourly", {}) if isinstance(data, dict) else {}

    def _first_valid(key: str, default: float = 0.0) -> float:
        """Return the first non-None value from an hourly array."""
        values = hourly.get(key, []) or []
        for v in values:
            if v is not None:
                return float(v)
        return default

    m_0_7 = _first_valid("soil_moisture_0_to_7cm")
    m_7_28 = _first_valid("soil_moisture_7_to_28cm")
    m_28_100 = _first_valid("soil_moisture_28_to_100cm")
    m_100_255 = _first_valid("soil_moisture_100_to_255cm")
    t_0_7 = _first_valid("soil_temperature_0_to_7cm")
    t_28_100 = _first_valid("soil_temperature_28_to_100cm")

    result["moisture_0_7cm"] = round(m_0_7, 4)
    result["moisture_7_28cm"] = round(m_7_28, 4)
    result["moisture_28_100cm"] = round(m_28_100, 4)
    result["moisture_100_255cm"] = round(m_100_255, 4)
    result["temp_0_7cm"] = round(t_0_7, 1)
    result["temp_28_100cm"] = round(t_28_100, 1)

    # Average of all four layers
    moisture_values = [m_0_7, m_7_28, m_28_100, m_100_255]
    avg = statistics.mean(moisture_values) if moisture_values else 0.0
    result["moisture_avg"] = round(avg, 4)

    # Classify moisture trend based on volumetric water content (m3/m3)
    if avg >= 0.45:
        result["moisture_trend"] = "saturated"
    elif avg >= 0.35:
        result["moisture_trend"] = "wet"
    elif avg >= 0.20:
        result["moisture_trend"] = "moist"
    elif avg >= 0.10:
        result["moisture_trend"] = "dry"
    else:
        result["moisture_trend"] = "arid"

    # Profile gradient: deep minus shallow (positive = wetter at depth)
    result["profile_gradient"] = round(m_100_255 - m_0_7, 4)

    logger.info(
        "Soil moisture for (%.4f, %.4f): avg %.4f m3/m3 (%s), gradient %.4f",
        lat, lon, result["moisture_avg"], result["moisture_trend"],
        result["profile_gradient"],
    )
    return result


# ---------------------------------------------------------------------------
# E. Open-Meteo UV & Pollen Index
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def fetch_uv_pollen_index(lat: float, lon: float) -> dict:
    """Fetch current UV index, air quality indices, and pollen counts.

    Returns UV risk classification, AQI values, per-species pollen counts,
    and an overall pollen risk level.
    """
    result = {
        "uv_index": 0.0,
        "uv_index_clear_sky": 0.0,
        "uv_risk": "Low",
        "european_aqi": 0,
        "us_aqi": 0,
        "pollen": {
            "alder": 0.0,
            "birch": 0.0,
            "grass": 0.0,
            "mugwort": 0.0,
            "olive": 0.0,
            "ragweed": 0.0,
        },
        "pollen_risk": "Low",
        "total_pollen": 0.0,
    }

    try:
        resp = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "uv_index,uv_index_clear_sky,european_aqi,us_aqi,"
                    "alder_pollen,birch_pollen,grass_pollen,"
                    "mugwort_pollen,olive_pollen,ragweed_pollen"
                ),
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("UV/Pollen API error: %s", exc)
        return result

    current = data.get("current", {}) if isinstance(data, dict) else {}
    if not isinstance(current, dict):
        current = {}

    uv = float(current.get("uv_index", 0) or 0)
    uv_clear = float(current.get("uv_index_clear_sky", 0) or 0)

    result["uv_index"] = round(uv, 1)
    result["uv_index_clear_sky"] = round(uv_clear, 1)

    # UV risk classification
    if uv < 3:
        result["uv_risk"] = "Low"
    elif uv < 6:
        result["uv_risk"] = "Moderate"
    elif uv < 8:
        result["uv_risk"] = "High"
    elif uv < 11:
        result["uv_risk"] = "Very High"
    else:
        result["uv_risk"] = "Extreme"

    result["european_aqi"] = int(current.get("european_aqi", 0) or 0)
    result["us_aqi"] = int(current.get("us_aqi", 0) or 0)

    # Pollen counts
    pollen_map = {
        "alder": "alder_pollen",
        "birch": "birch_pollen",
        "grass": "grass_pollen",
        "mugwort": "mugwort_pollen",
        "olive": "olive_pollen",
        "ragweed": "ragweed_pollen",
    }
    total_pollen = 0.0
    for display_key, api_key in pollen_map.items():
        val = float(current.get(api_key, 0) or 0)
        result["pollen"][display_key] = round(val, 1)
        total_pollen += val

    result["total_pollen"] = round(total_pollen, 1)

    # Pollen risk classification
    if total_pollen < 20:
        result["pollen_risk"] = "Low"
    elif total_pollen < 50:
        result["pollen_risk"] = "Moderate"
    elif total_pollen < 100:
        result["pollen_risk"] = "High"
    else:
        result["pollen_risk"] = "Very High"

    logger.info(
        "UV/Pollen for (%.4f, %.4f): UV %.1f (%s), pollen %.1f (%s), AQI EU=%d US=%d",
        lat, lon, result["uv_index"], result["uv_risk"],
        result["total_pollen"], result["pollen_risk"],
        result["european_aqi"], result["us_aqi"],
    )
    return result


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def fetch_all_apex_sources(lat: float, lon: float) -> dict:
    """Fetch all 5 apex data sources and return a combined dict.

    Each source is independently wrapped in try/except so a single failure
    does not prevent the others from returning data.
    """
    results = {
        "climate_projections": {},
        "volcanoes": {},
        "climate_normals": {},
        "soil_moisture": {},
        "uv_pollen": {},
    }

    try:
        results["climate_projections"] = fetch_climate_projections(lat, lon)
    except Exception as exc:
        logger.error("Aggregator: climate projections failed: %s", exc)

    try:
        results["volcanoes"] = fetch_volcano_proximity(lat, lon)
    except Exception as exc:
        logger.error("Aggregator: volcano proximity failed: %s", exc)

    try:
        results["climate_normals"] = fetch_climate_normals(lat, lon)
    except Exception as exc:
        logger.error("Aggregator: climate normals failed: %s", exc)

    try:
        results["soil_moisture"] = fetch_soil_moisture_profile(lat, lon)
    except Exception as exc:
        logger.error("Aggregator: soil moisture failed: %s", exc)

    try:
        results["uv_pollen"] = fetch_uv_pollen_index(lat, lon)
    except Exception as exc:
        logger.error("Aggregator: UV/pollen failed: %s", exc)

    logger.info(
        "All apex sources fetched for (%.4f, %.4f): %d sources populated",
        lat, lon,
        sum(1 for v in results.values() if v),
    )
    return results
