"""
Enhanced Data Sources — Additional free APIs for TerraScout AI.

Provides three new data feeds:
- GDACS (Global Disaster Alert System) — active disaster events
- WorldPop — population density estimates
- OpenAQ — real air quality monitoring stations

All functions use @st.cache_data with appropriate TTLs and safe error handling.
"""

import logging
import math

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. GDACS — Global Disaster Alert and Coordination System
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def fetch_gdacs_events(lat, lon, radius_km=250):
    """Fetch active disaster events from GDACS near the given location.

    Returns a list of dicts:
        [{type, severity, name, distance_km, alert_level, population_affected,
          event_id, from_date, to_date, country}]
    """
    try:
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP"
        resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("GDACS fetch failed: %s", e)
        return []

    features = data.get("features", [])
    if not isinstance(features, list):
        return []

    results = []
    for feat in features:
        try:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            if not coords or len(coords) < 2:
                continue

            evt_lon, evt_lat = float(coords[0]), float(coords[1])
            dist = _haversine(lat, lon, evt_lat, evt_lon)
            if dist > radius_km:
                continue

            alert_level = props.get("alertlevel", "").upper()
            severity_map = {"RED": 3, "ORANGE": 2, "GREEN": 1}
            severity = severity_map.get(alert_level, 0)

            results.append({
                "type": props.get("eventtype", "unknown"),
                "name": props.get("eventname", props.get("name", "Unknown Event")),
                "severity": severity,
                "alert_level": alert_level or "UNKNOWN",
                "distance_km": round(dist, 1),
                "population_affected": props.get("population", {}).get("value", 0)
                    if isinstance(props.get("population"), dict)
                    else props.get("population", 0),
                "event_id": props.get("eventid", ""),
                "from_date": props.get("fromdate", ""),
                "to_date": props.get("todate", ""),
                "country": props.get("country", ""),
            })
        except Exception:
            continue

    results.sort(key=lambda x: (x["severity"], -x["distance_km"]), reverse=True)
    return results[:20]


# ---------------------------------------------------------------------------
# 2. WorldPop — Population Density
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def fetch_population_density(lat, lon):
    """Fetch population density estimate from WorldPop.

    Returns a dict:
        {density_per_km2, total_estimated, dataset, source}
    or {} on failure.
    """
    try:
        url = "https://api.worldpop.org/v1/wopr/pointtotal"
        params = {"lat": lat, "lon": lon}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("WorldPop fetch failed: %s", e)
        return {}

    if not isinstance(data, dict):
        return {}

    # WorldPop returns { "data": [ { ... } ] } or similar structures
    results_data = data.get("data", [])
    if isinstance(results_data, list) and results_data:
        entry = results_data[0] if isinstance(results_data[0], dict) else {}
        pop = entry.get("pop_total", entry.get("pop", entry.get("population", 0)))
        return {
            "density_per_km2": _safe_float(pop),
            "total_estimated": _safe_float(pop),
            "dataset": entry.get("dataset", "worldpop"),
            "source": "WorldPop",
        }

    # Fallback: try direct fields
    pop = data.get("population", data.get("pop", data.get("total", 0)))
    if pop:
        return {
            "density_per_km2": _safe_float(pop),
            "total_estimated": _safe_float(pop),
            "dataset": data.get("dataset", "worldpop"),
            "source": "WorldPop",
        }

    return {}


# ---------------------------------------------------------------------------
# 3. OpenAQ — Real Air Quality Monitoring Stations
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def fetch_openaq_stations(lat, lon, radius_km=50):
    """Fetch nearest air quality monitoring stations from OpenAQ v2.

    Returns a list of dicts:
        [{station, distance_km, pm25, pm10, o3, no2, last_updated, location_id, city, country}]
    """
    radius_m = int(radius_km * 1000)
    try:
        url = "https://api.openaq.org/v2/latest"
        params = {
            "coordinates": f"{lat},{lon}",
            "radius": radius_m,
            "limit": 10,
            "order_by": "distance",
        }
        resp = requests.get(url, params=params, timeout=10,
                           headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("OpenAQ fetch failed: %s", e)
        return []

    results_list = data.get("results", [])
    if not isinstance(results_list, list):
        return []

    stations = []
    for entry in results_list:
        try:
            if not isinstance(entry, dict):
                continue

            loc_name = entry.get("location", "Unknown Station")
            city = entry.get("city", "")
            country = entry.get("country", "")
            loc_id = entry.get("id", "")

            coords = entry.get("coordinates", {})
            if isinstance(coords, dict):
                s_lat = coords.get("latitude", 0)
                s_lon = coords.get("longitude", 0)
                dist = _haversine(lat, lon, s_lat, s_lon)
            else:
                dist = entry.get("distance", 0) / 1000.0 if entry.get("distance") else 0

            measurements = entry.get("measurements", [])
            params_dict = {}
            last_updated = ""
            for m in (measurements if isinstance(measurements, list) else []):
                if not isinstance(m, dict):
                    continue
                param = m.get("parameter", "").lower()
                value = m.get("value")
                if param and value is not None:
                    params_dict[param] = _safe_float(value)
                lu = m.get("lastUpdated", "")
                if lu and lu > last_updated:
                    last_updated = lu

            stations.append({
                "station": loc_name,
                "distance_km": round(dist, 1),
                "pm25": params_dict.get("pm25", params_dict.get("pm2.5")),
                "pm10": params_dict.get("pm10"),
                "o3": params_dict.get("o3"),
                "no2": params_dict.get("no2"),
                "so2": params_dict.get("so2"),
                "co": params_dict.get("co"),
                "last_updated": last_updated,
                "location_id": loc_id,
                "city": city,
                "country": country,
            })
        except Exception:
            continue

    stations.sort(key=lambda x: x["distance_km"])
    return stations[:10]


# ---------------------------------------------------------------------------
# AGGREGATE: fetch all enhanced sources
# ---------------------------------------------------------------------------

def fetch_all_enhanced_sources(lat, lon):
    """Convenience: fetch all three enhanced data sources at once.

    Returns:
        {gdacs: [...], population: {...}, openaq: [...]}
    """
    gdacs = fetch_gdacs_events(lat, lon)
    population = fetch_population_density(lat, lon)
    openaq = fetch_openaq_stations(lat, lon)
    return {
        "gdacs": gdacs,
        "population": population,
        "openaq": openaq,
    }


# ---------------------------------------------------------------------------
# SCORING HELPERS — Derive scores from enhanced data
# ---------------------------------------------------------------------------

def gdacs_hazard_penalty(events):
    """Compute a hazard penalty [0-30] based on active GDACS events.

    Closer and more severe events produce higher penalties.
    """
    if not events:
        return 0.0
    penalty = 0.0
    for evt in events[:10]:
        severity = evt.get("severity", 0)
        dist = max(evt.get("distance_km", 250), 1)
        # Inverse distance weighting: closer = worse
        weight = severity * (100.0 / dist)
        penalty += weight
    return min(30.0, penalty)


def openaq_air_quality_score(stations):
    """Compute an air quality adjustment [-15, +10] from real station data.

    Returns negative values for poor air quality, positive for good.
    """
    if not stations:
        return 0.0

    pm25_values = [s["pm25"] for s in stations if s.get("pm25") is not None]
    pm10_values = [s["pm10"] for s in stations if s.get("pm10") is not None]

    if not pm25_values and not pm10_values:
        return 0.0

    adjustment = 0.0

    if pm25_values:
        avg_pm25 = sum(pm25_values) / len(pm25_values)
        if avg_pm25 <= 12:
            adjustment += 10.0  # Excellent
        elif avg_pm25 <= 35:
            adjustment += 5.0  # Good
        elif avg_pm25 <= 55:
            adjustment -= 5.0  # Moderate
        elif avg_pm25 <= 150:
            adjustment -= 10.0  # Unhealthy
        else:
            adjustment -= 15.0  # Hazardous

    if pm10_values:
        avg_pm10 = sum(pm10_values) / len(pm10_values)
        if avg_pm10 > 150:
            adjustment -= 5.0  # Extra penalty for high PM10

    return max(-15.0, min(10.0, adjustment))


def population_density_factor(pop_data):
    """Derive infrastructure and economic potential modifiers from population density.

    Returns:
        {infra_boost: float, economic_boost: float, carrying_capacity_warning: bool}
    """
    density = pop_data.get("density_per_km2", 0) if pop_data else 0
    if not density or density <= 0:
        return {"infra_boost": 0, "economic_boost": 0, "carrying_capacity_warning": False}

    # Infrastructure: moderate density = good, very low or very high = less ideal
    if 50 <= density <= 5000:
        infra_boost = min(8.0, math.log10(density) * 2.5)
    elif density > 5000:
        infra_boost = 5.0  # Still OK but congestion
    else:
        infra_boost = 0.0

    # Economic potential: higher density = more economic activity
    if density > 100:
        economic_boost = min(10.0, math.log10(density) * 3)
    else:
        economic_boost = 0.0

    # Carrying capacity warning if density > 10,000/km2
    carrying_warning = density > 10000

    return {
        "infra_boost": round(infra_boost, 1),
        "economic_boost": round(economic_boost, 1),
        "carrying_capacity_warning": carrying_warning,
    }


# ---------------------------------------------------------------------------
# PRIVATE HELPERS
# ---------------------------------------------------------------------------

def _haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _safe_float(val):
    """Convert a value to float safely, returning 0.0 on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0
