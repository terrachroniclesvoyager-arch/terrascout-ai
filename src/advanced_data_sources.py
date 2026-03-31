"""
Advanced Data Sources — 5 additional free APIs for TerraScout AI Phase 3.

F. Open-Meteo Marine  — Wave height, sea surface temp, ocean currents
G. Open-Meteo Flood   — River discharge forecasts, flood risk
H. USGS Water Services— Real-time streamflow, water stations
I. UN ReliefWeb       — Humanitarian crises & disaster events
J. GeoNames           — Nearby geographic features, landmarks, POIs

All free, no API keys required (GeoNames uses demo account).
"""

import logging
import math
import requests
import streamlit as st

logger = logging.getLogger(__name__)


def _haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lon points."""
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# F. Open-Meteo Marine — Wave & Ocean Data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def fetch_marine_data(lat, lon):
    """Fetch marine/ocean data from Open-Meteo Marine API.

    Returns dict with: wave_height, wave_period, wave_direction,
    sea_surface_temp, ocean_current_speed, swell_height,
    marine_risk_level (str), is_coastal (bool).
    """
    try:
        resp = requests.get(
            "https://marine-api.open-meteo.com/v1/marine",
            params={
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "current": "wave_height,wave_period,wave_direction,ocean_current_velocity,ocean_current_direction,swell_wave_height",
                "timezone": "auto",
            },
            timeout=10,
        )
        if resp.status_code == 400:
            # Likely inland location — not near ocean
            return {"is_coastal": False}
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})

        wave_h = current.get("wave_height")
        wave_p = current.get("wave_period")
        wave_d = current.get("wave_direction")
        current_v = current.get("ocean_current_velocity")
        current_d = current.get("ocean_current_direction")
        swell_h = current.get("swell_wave_height")

        # Risk assessment
        wh = wave_h if isinstance(wave_h, (int, float)) else 0
        if wh >= 4.0:
            risk = "SEVERE"
        elif wh >= 2.5:
            risk = "HIGH"
        elif wh >= 1.0:
            risk = "MODERATE"
        elif wh > 0:
            risk = "LOW"
        else:
            risk = "CALM"

        return {
            "is_coastal": True,
            "wave_height_m": round(wave_h, 2) if isinstance(wave_h, (int, float)) else None,
            "wave_period_s": round(wave_p, 1) if isinstance(wave_p, (int, float)) else None,
            "wave_direction_deg": wave_d,
            "ocean_current_speed": round(current_v, 3) if isinstance(current_v, (int, float)) else None,
            "ocean_current_direction": current_d,
            "swell_height_m": round(swell_h, 2) if isinstance(swell_h, (int, float)) else None,
            "marine_risk_level": risk,
        }
    except Exception as exc:
        logger.warning("Marine data fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# G. Open-Meteo Flood — River Discharge Forecasts
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def fetch_flood_data(lat, lon):
    """Fetch river discharge forecast from Open-Meteo Flood API.

    Returns dict with: current_discharge_m3s, max_forecast_discharge,
    forecast_days, flood_risk_level (str), discharge_trend.
    """
    try:
        resp = requests.get(
            "https://flood-api.open-meteo.com/v1/flood",
            params={
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "daily": "river_discharge",
                "forecast_days": 7,
            },
            timeout=10,
        )
        if resp.status_code == 400:
            return {"has_river_data": False}
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        discharges = daily.get("river_discharge", [])

        valid = [d for d in discharges if isinstance(d, (int, float)) and d >= 0]
        if not valid:
            return {"has_river_data": False}

        current = valid[0]
        max_discharge = max(valid)
        avg_discharge = sum(valid) / len(valid)

        # Trend: compare first half vs second half
        mid = len(valid) // 2
        first_half = sum(valid[:mid]) / mid if mid > 0 else avg_discharge
        second_half = sum(valid[mid:]) / (len(valid) - mid) if (len(valid) - mid) > 0 else avg_discharge

        if second_half > first_half * 1.5:
            trend = "RISING_FAST"
        elif second_half > first_half * 1.1:
            trend = "RISING"
        elif second_half < first_half * 0.7:
            trend = "FALLING_FAST"
        elif second_half < first_half * 0.9:
            trend = "FALLING"
        else:
            trend = "STABLE"

        # Risk level based on discharge magnitude and trend
        if max_discharge > 1000 and trend in ("RISING", "RISING_FAST"):
            risk = "HIGH"
        elif max_discharge > 500 or trend == "RISING_FAST":
            risk = "MODERATE"
        elif max_discharge > 100:
            risk = "LOW"
        else:
            risk = "MINIMAL"

        return {
            "has_river_data": True,
            "current_discharge_m3s": round(current, 2),
            "max_forecast_discharge": round(max_discharge, 2),
            "avg_discharge_m3s": round(avg_discharge, 2),
            "forecast_days": len(valid),
            "daily_discharges": [round(d, 2) for d in valid],
            "discharge_trend": trend,
            "flood_risk_level": risk,
        }
    except Exception as exc:
        logger.warning("Flood data fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# H. USGS Water Services — Real-Time Streamflow
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def fetch_usgs_streamflow(lat, lon, radius_km=50):
    """Fetch real-time streamflow data from USGS Water Services.

    Returns dict with: station_count, stations (list with name, value, unit),
    nearest_station, avg_flow, water_availability_rating.
    US only — returns empty for non-US locations.
    """
    try:
        # USGS bounding box: lat/lon ± radius
        delta = radius_km / 111.0
        bbox = f"{lon - delta:.4f},{lat - delta:.4f},{lon + delta:.4f},{lat + delta:.4f}"

        resp = requests.get(
            "https://waterservices.usgs.gov/nwis/iv/",
            params={
                "format": "json",
                "bBox": bbox,
                "parameterCd": "00060",  # Streamflow/discharge
                "siteStatus": "active",
                "siteType": "ST",  # Streams
            },
            timeout=10,
        )
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        data = resp.json()

        ts_list = data.get("value", {}).get("timeSeries", [])
        if not ts_list:
            return {"station_count": 0, "stations": []}

        stations = []
        for ts in ts_list[:20]:
            site_info = ts.get("sourceInfo", {})
            site_name = site_info.get("siteName", "Unknown")
            geo = site_info.get("geoLocation", {}).get("geogLocation", {})
            slat = geo.get("latitude", lat)
            slon = geo.get("longitude", lon)
            dist = _haversine(lat, lon, slat, slon)

            vals = ts.get("values", [{}])[0].get("value", [])
            latest = vals[-1] if vals else {}
            flow_val = latest.get("value")
            try:
                flow = float(flow_val) if flow_val is not None else None
            except (ValueError, TypeError):
                flow = None

            unit = ts.get("variable", {}).get("unit", {}).get("unitCode", "ft3/s")

            stations.append({
                "name": site_name,
                "lat": slat,
                "lon": slon,
                "distance_km": round(dist, 1),
                "flow_value": round(flow, 2) if flow is not None else None,
                "unit": unit,
            })

        stations.sort(key=lambda s: s["distance_km"])
        valid_flows = [s["flow_value"] for s in stations if s["flow_value"] is not None and s["flow_value"] >= 0]
        avg_flow = sum(valid_flows) / len(valid_flows) if valid_flows else None

        # Rating
        if avg_flow is None:
            rating = "NO DATA"
        elif avg_flow > 500:
            rating = "ABUNDANT"
        elif avg_flow > 100:
            rating = "GOOD"
        elif avg_flow > 10:
            rating = "MODERATE"
        else:
            rating = "LOW"

        return {
            "station_count": len(stations),
            "stations": stations[:10],
            "nearest_station": stations[0] if stations else None,
            "avg_flow": round(avg_flow, 2) if avg_flow is not None else None,
            "water_availability_rating": rating,
        }
    except Exception as exc:
        logger.warning("USGS streamflow fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# I. UN ReliefWeb — Humanitarian Crises & Disasters
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_reliefweb_data(lat, lon):
    """Fetch recent disaster/crisis reports from UN ReliefWeb.

    Returns dict with: report_count, reports (list), crisis_level,
    disaster_types, latest_update.
    """
    try:
        # ReliefWeb doesn't support lat/lon directly — reverse geocode first
        try:
            geo_resp = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lon, "format": "json", "zoom": 3,
                        "accept-language": "en"},
                headers={"User-Agent": "TerraScoutAI/2.0"},
                timeout=10,
            )
            geo_resp.raise_for_status()
            country_name = geo_resp.json().get("address", {}).get("country", "")
        except Exception:
            return {}

        if not country_name:
            return {}

        resp = requests.get(
            "https://api.reliefweb.int/v1/reports",
            params={
                "appname": "terrascout",
                "filter[field]": "country.name",
                "filter[value]": country_name,
                "sort[]": "date:desc",
                "limit": 10,
                "fields[include][]": "title,date.original,disaster_type.name,source.name,url",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", [])

        reports = []
        disaster_types = set()
        for item in items:
            fields = item.get("fields", {})
            title = fields.get("title", "")
            date = fields.get("date", {}).get("original", "")
            dtypes = fields.get("disaster_type", [])
            source = fields.get("source", [])
            url = fields.get("url", "")

            for dt in dtypes:
                if isinstance(dt, dict):
                    disaster_types.add(dt.get("name", ""))

            reports.append({
                "title": title[:200],
                "date": date[:10] if date else "",
                "disaster_types": [dt.get("name", "") for dt in dtypes if isinstance(dt, dict)],
                "source": source[0].get("name", "") if source and isinstance(source[0], dict) else "",
                "url": url,
            })

        # Crisis level assessment
        count = len(reports)
        if count >= 8:
            crisis = "ACTIVE CRISIS"
        elif count >= 4:
            crisis = "ELEVATED"
        elif count >= 1:
            crisis = "MONITORING"
        else:
            crisis = "STABLE"

        return {
            "country": country_name,
            "report_count": count,
            "reports": reports,
            "crisis_level": crisis,
            "disaster_types": list(disaster_types),
            "latest_update": reports[0]["date"] if reports else "",
        }
    except Exception as exc:
        logger.warning("ReliefWeb fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# J. GeoNames — Nearby Geographic Features
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_geonames_features(lat, lon, radius_km=20):
    """Fetch nearby geographic features from GeoNames.

    Returns dict with: feature_count, features (list with name, type, distance),
    nearest_city, terrain_description, cultural_features.
    """
    try:
        resp = requests.get(
            "http://api.geonames.org/findNearbyJSON",
            params={
                "lat": round(lat, 4),
                "lng": round(lon, 4),
                "radius": min(radius_km, 50),
                "maxRows": 20,
                "username": "demo",
                "style": "FULL",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        geonames = data.get("geonames", [])

        features = []
        nearest_city = None
        cultural = []
        terrain_types = set()

        for gn in geonames:
            name = gn.get("name", "Unknown")
            fcl = gn.get("fcl", "")
            fcode = gn.get("fcode", "")
            feat_class = gn.get("fclName", "")
            gnlat = gn.get("lat")
            gnlon = gn.get("lng")

            dist = 0
            if gnlat and gnlon:
                try:
                    dist = _haversine(lat, lon, float(gnlat), float(gnlon))
                except (ValueError, TypeError):
                    pass

            feature = {
                "name": name,
                "type": feat_class,
                "feature_code": fcode,
                "distance_km": round(dist, 1),
                "population": gn.get("population", 0),
            }
            features.append(feature)

            # Track city
            if fcl == "P" and nearest_city is None:
                nearest_city = {
                    "name": name,
                    "population": gn.get("population", 0),
                    "distance_km": round(dist, 1),
                }

            # Cultural features
            if fcl == "S":
                cultural.append(name)

            # Terrain categorization
            if fcl == "T":
                terrain_types.add(feat_class)
            elif fcl == "H":
                terrain_types.add("Hydrographic")
            elif fcl == "V":
                terrain_types.add("Vegetation")
            elif fcl == "L":
                terrain_types.add("Landscape")

        features.sort(key=lambda f: f["distance_km"])

        terrain_desc = ", ".join(sorted(terrain_types)) if terrain_types else "Mixed terrain"

        return {
            "feature_count": len(features),
            "features": features[:15],
            "nearest_city": nearest_city,
            "terrain_description": terrain_desc,
            "cultural_features": cultural[:10],
        }
    except Exception as exc:
        logger.warning("GeoNames fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# AGGREGATOR
# ---------------------------------------------------------------------------

def fetch_all_advanced_sources(lat, lon):
    """Fetch all Phase 3 data sources in one call.

    Returns dict with keys: marine, flood, streamflow, reliefweb, geonames.
    Each individually wrapped in try/except.
    """
    result = {}

    try:
        result["marine"] = fetch_marine_data(lat, lon)
    except Exception as exc:
        logger.warning("Marine aggregation failed: %s", exc)
        result["marine"] = {}

    try:
        result["flood"] = fetch_flood_data(lat, lon)
    except Exception as exc:
        logger.warning("Flood aggregation failed: %s", exc)
        result["flood"] = {}

    try:
        result["streamflow"] = fetch_usgs_streamflow(lat, lon)
    except Exception as exc:
        logger.warning("Streamflow aggregation failed: %s", exc)
        result["streamflow"] = {}

    try:
        result["reliefweb"] = fetch_reliefweb_data(lat, lon)
    except Exception as exc:
        logger.warning("ReliefWeb aggregation failed: %s", exc)
        result["reliefweb"] = {}

    try:
        result["geonames"] = fetch_geonames_features(lat, lon)
    except Exception as exc:
        logger.warning("GeoNames aggregation failed: %s", exc)
        result["geonames"] = {}

    return result
