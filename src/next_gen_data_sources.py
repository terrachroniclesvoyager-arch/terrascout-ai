"""
Next-Gen Data Sources — 5 free APIs filling TerraScout intelligence gaps.

A. NASA POWER — Solar radiation & climate extremes
B. NOAA NWS  — Active severe weather alerts (US only)
C. NASA FIRMS — Active fire hotspots (EONET fallback)
D. WHO GHO   — Global health indicators
E. UNDP HDI  — Human Development Index proxy

Each fetcher is individually wrapped in try/except and cached.
"""

import logging
import math
import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lon points."""
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data(ttl=3600)
def _reverse_geocode_country(lat, lon):
    """Return ISO-3166-1 alpha-3 country code via Nominatim reverse geocoding."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 3,
                    "accept-language": "en"},
            headers={"User-Agent": "TerraScoutAI/2.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        addr = data.get("address", {})
        cc2 = addr.get("country_code", "").upper()
        if not cc2:
            return None
        # Convert alpha-2 to alpha-3 using REST Countries
        rc = requests.get(
            f"https://restcountries.com/v3.1/alpha/{cc2}",
            timeout=10,
        )
        rc.raise_for_status()
        items = rc.json()
        if isinstance(items, list) and items:
            return items[0].get("cca3", cc2)
        return cc2
    except Exception:
        return None


# ---------------------------------------------------------------------------
# A. NASA POWER — Solar Radiation & Climate Extremes
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_nasa_power_solar(lat, lon):
    """Fetch annual/monthly solar radiation and climate extremes from NASA POWER.

    Returns dict with keys:
        annual_ghi_kwh (kWh/m2/day avg), monthly_ghi (12 floats),
        temp_max_annual, temp_min_annual, hdd_annual, cdd_annual,
        solar_potential_rating (str)
    """
    try:
        params = {
            "parameters": "ALLSKY_SFC_SW_DWN,T2M_MAX,T2M_MIN",
            "community": "RE",
            "longitude": round(lon, 4),
            "latitude": round(lat, 4),
            "start": "2020",
            "end": "2023",
            "format": "JSON",
            "temporal": "monthly",
        }
        resp = requests.get(
            "https://power.larc.nasa.gov/api/temporal/monthly/point",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        props = data.get("properties", {})
        param_data = props.get("parameter", {})

        # Solar irradiance
        ghi_data = param_data.get("ALLSKY_SFC_SW_DWN", {})
        ghi_vals = [v for v in ghi_data.values() if isinstance(v, (int, float)) and v > -900]

        # Temperature extremes
        tmax_data = param_data.get("T2M_MAX", {})
        tmin_data = param_data.get("T2M_MIN", {})
        tmax_vals = [v for v in tmax_data.values() if isinstance(v, (int, float)) and v > -900]
        tmin_vals = [v for v in tmin_data.values() if isinstance(v, (int, float)) and v > -900]

        avg_ghi = sum(ghi_vals) / len(ghi_vals) if ghi_vals else 0
        max_temp = max(tmax_vals) if tmax_vals else None
        min_temp = min(tmin_vals) if tmin_vals else None

        # Monthly averages (last 12 available)
        monthly_ghi = ghi_vals[-12:] if len(ghi_vals) >= 12 else ghi_vals

        # Heating/cooling degree days (simplified)
        avg_temps = []
        for k in sorted(tmax_data.keys()):
            tx = tmax_data.get(k, -999)
            tn = tmin_data.get(k, -999)
            if isinstance(tx, (int, float)) and tx > -900 and isinstance(tn, (int, float)) and tn > -900:
                avg_temps.append((tx + tn) / 2)

        hdd = sum(max(18 - t, 0) for t in avg_temps[-12:]) if avg_temps else 0
        cdd = sum(max(t - 18, 0) for t in avg_temps[-12:]) if avg_temps else 0

        # Rating
        if avg_ghi >= 5.5:
            rating = "Excellent"
        elif avg_ghi >= 4.5:
            rating = "Good"
        elif avg_ghi >= 3.5:
            rating = "Moderate"
        else:
            rating = "Low"

        return {
            "annual_ghi_kwh": round(avg_ghi, 2),
            "monthly_ghi": [round(v, 2) for v in monthly_ghi],
            "temp_max_annual": round(max_temp, 1) if max_temp is not None else None,
            "temp_min_annual": round(min_temp, 1) if min_temp is not None else None,
            "hdd_annual": round(hdd, 0),
            "cdd_annual": round(cdd, 0),
            "solar_potential_rating": rating,
        }
    except Exception as exc:
        logger.warning("NASA POWER fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# B. NOAA NWS — Active Severe Weather Alerts
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def fetch_noaa_weather_alerts(lat, lon):
    """Fetch active weather alerts from NOAA NWS (US only).

    Returns list of dicts with: event, severity, urgency, headline, description.
    Empty list for non-US locations.
    """
    try:
        resp = requests.get(
            f"https://api.weather.gov/alerts/active?point={lat},{lon}",
            headers={"User-Agent": "TerraScoutAI/2.0"},
            timeout=10,
        )
        if resp.status_code == 404:
            return []  # non-US location
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        alerts = []
        for f in features[:10]:  # cap at 10
            props = f.get("properties", {})
            alerts.append({
                "event": props.get("event", "Unknown"),
                "severity": props.get("severity", "Unknown"),
                "urgency": props.get("urgency", "Unknown"),
                "headline": props.get("headline", ""),
                "description": (props.get("description", "") or "")[:500],
                "instruction": (props.get("instruction", "") or "")[:300],
            })
        return alerts
    except Exception as exc:
        logger.warning("NOAA NWS alerts fetch failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# C. NASA FIRMS / EONET — Active Fire Hotspots
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def fetch_nasa_firms_fires(lat, lon, radius_km=100):
    """Fetch active fire hotspots near location using NASA EONET.

    Returns dict with: fire_count, nearest_fire_km, fires (list).
    """
    try:
        # Use EONET (free, no key needed) for wildfire events
        resp = requests.get(
            "https://eonet.gsfc.nasa.gov/api/v3/events",
            params={"category": "wildfires", "status": "open", "limit": 50},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])

        fires = []
        for ev in events:
            geom_list = ev.get("geometry", [])
            if not geom_list:
                continue
            # Use most recent geometry point
            geom = geom_list[-1]
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            fire_lon, fire_lat = coords[0], coords[1]
            dist = _haversine(lat, lon, fire_lat, fire_lon)
            if dist <= radius_km:
                fires.append({
                    "title": ev.get("title", "Unknown fire"),
                    "lat": round(fire_lat, 4),
                    "lon": round(fire_lon, 4),
                    "distance_km": round(dist, 1),
                    "date": geom.get("date", ""),
                })

        fires.sort(key=lambda f: f["distance_km"])
        nearest = fires[0]["distance_km"] if fires else None

        return {
            "fire_count": len(fires),
            "nearest_fire_km": nearest,
            "fires": fires[:20],
            "search_radius_km": radius_km,
        }
    except Exception as exc:
        logger.warning("NASA FIRMS/EONET fire fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# D. WHO GHO — Global Health Indicators
# ---------------------------------------------------------------------------

_WHO_INDICATORS = {
    "WHOSIS_000001": "life_expectancy",
    "MDG_0000000001": "infant_mortality_rate",
    "HWF_0001": "physician_density",
    "HWF_0006": "hospital_bed_density",
    "WSH_SANITATION_SAFELY_MANAGED": "sanitation_access",
    "WSH_WATER_SAFELY_MANAGED": "water_access",
}


@st.cache_data(ttl=3600)
def fetch_who_health_indicators(lat, lon):
    """Fetch WHO Global Health Observatory indicators for the country at (lat, lon).

    Returns dict with: country, life_expectancy, infant_mortality_rate,
    physician_density, hospital_bed_density, sanitation_access, water_access,
    health_score (0-100).
    """
    try:
        iso3 = _reverse_geocode_country(lat, lon)
        if not iso3:
            return {}

        result = {"country_iso3": iso3}
        for code, key in _WHO_INDICATORS.items():
            try:
                resp = requests.get(
                    f"https://ghoapi.azureedge.net/api/{code}",
                    params={"$filter": f"SpatialDim eq '{iso3}'",
                            "$orderby": "TimeDim desc",
                            "$top": 1},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                values = data.get("value", [])
                if values:
                    num = values[0].get("NumericValue")
                    if num is not None:
                        result[key] = round(float(num), 2)
                        result[f"{key}_year"] = values[0].get("TimeDim", "")
            except Exception:
                continue

        # Compute composite health score (0-100)
        score_parts = []
        le = result.get("life_expectancy")
        if le is not None:
            score_parts.append(min(le / 85 * 100, 100))
        imr = result.get("infant_mortality_rate")
        if imr is not None:
            score_parts.append(max(100 - imr * 2, 0))
        pd_val = result.get("physician_density")
        if pd_val is not None:
            score_parts.append(min(pd_val / 5 * 100, 100))
        san = result.get("sanitation_access")
        if san is not None:
            score_parts.append(min(san, 100))
        wat = result.get("water_access")
        if wat is not None:
            score_parts.append(min(wat, 100))

        result["health_score"] = round(sum(score_parts) / len(score_parts), 1) if score_parts else None

        return result
    except Exception as exc:
        logger.warning("WHO GHO fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# E. UNDP HDI — Human Development Index (proxy via REST Countries)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_hdi_data(lat, lon):
    """Compute an HDI proxy from REST Countries data.

    Returns dict with: hdi_value, hdi_rank_estimate, hdi_category,
    education_index, income_index, health_index.
    """
    try:
        iso3 = _reverse_geocode_country(lat, lon)
        if not iso3:
            return {}

        resp = requests.get(
            f"https://restcountries.com/v3.1/alpha/{iso3}",
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json()
        if not isinstance(items, list) or not items:
            return {}
        country = items[0]

        # Extract available indicators
        pop = country.get("population", 0)
        area = country.get("area", 0)
        gini_data = country.get("gini", {})
        gini = list(gini_data.values())[0] if isinstance(gini_data, dict) and gini_data else None
        region = country.get("region", "")
        subregion = country.get("subregion", "")

        # HDI proxy based on region + available data
        # Regional base HDI estimates
        _region_hdi = {
            "Europe": 0.87, "Northern America": 0.92,
            "Oceania": 0.78, "Asia": 0.68,
            "Americas": 0.75, "Africa": 0.55,
        }
        _subregion_adj = {
            "Northern Europe": 0.05, "Western Europe": 0.05,
            "Southern Europe": 0.02, "Eastern Europe": -0.02,
            "Eastern Asia": 0.10, "South-Eastern Asia": -0.02,
            "Southern Asia": -0.05, "Western Asia": 0.03,
            "Northern Africa": 0.05, "Southern Africa": 0.05,
            "South America": 0.02, "Central America": -0.02,
            "Caribbean": 0.0, "Australia and New Zealand": 0.12,
        }

        base = _region_hdi.get(region, 0.65)
        adj = _subregion_adj.get(subregion, 0)
        hdi_est = min(max(base + adj, 0.3), 0.97)

        # Gini adjustment: higher inequality lowers HDI slightly
        if gini is not None:
            gini_penalty = max(0, (gini - 30)) * 0.002
            hdi_est = max(hdi_est - gini_penalty, 0.3)

        hdi_est = round(hdi_est, 3)

        # Category
        if hdi_est >= 0.8:
            cat = "Very High"
        elif hdi_est >= 0.7:
            cat = "High"
        elif hdi_est >= 0.55:
            cat = "Medium"
        else:
            cat = "Low"

        # Sub-indices (approximate)
        health_idx = round(min(hdi_est + 0.02, 1.0), 3)
        education_idx = round(hdi_est - 0.01, 3)
        income_idx = round(hdi_est + 0.01, 3)

        # Rank estimate (rough)
        rank_est = max(1, int((1 - hdi_est) * 190))

        return {
            "hdi_value": hdi_est,
            "hdi_rank_estimate": rank_est,
            "hdi_category": cat,
            "health_index": health_idx,
            "education_index": education_idx,
            "income_index": income_idx,
            "country_name": country.get("name", {}).get("common", ""),
            "region": region,
            "gini": gini,
        }
    except Exception as exc:
        logger.warning("HDI proxy fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# AGGREGATOR
# ---------------------------------------------------------------------------

def fetch_all_next_gen_sources(lat, lon):
    """Fetch all next-gen data sources in one call.

    Returns dict with keys: nasa_power, noaa_alerts, firms_fires,
    who_health, hdi. Each individually wrapped in try/except.
    """
    result = {}

    try:
        result["nasa_power"] = fetch_nasa_power_solar(lat, lon)
    except Exception as exc:
        logger.warning("NASA POWER aggregation failed: %s", exc)
        result["nasa_power"] = {}

    try:
        result["noaa_alerts"] = fetch_noaa_weather_alerts(lat, lon)
    except Exception as exc:
        logger.warning("NOAA alerts aggregation failed: %s", exc)
        result["noaa_alerts"] = []

    try:
        result["firms_fires"] = fetch_nasa_firms_fires(lat, lon)
    except Exception as exc:
        logger.warning("FIRMS fires aggregation failed: %s", exc)
        result["firms_fires"] = {}

    try:
        result["who_health"] = fetch_who_health_indicators(lat, lon)
    except Exception as exc:
        logger.warning("WHO health aggregation failed: %s", exc)
        result["who_health"] = {}

    try:
        result["hdi"] = fetch_hdi_data(lat, lon)
    except Exception as exc:
        logger.warning("HDI aggregation failed: %s", exc)
        result["hdi"] = {}

    return result
