"""
GLOBAL REAL-TIME DASHBOARD - Worldwide Intelligence
Aggregates real-time data from multiple free sources and displays on world map

Features:
- Fuel prices worldwide
- Oil prices (Brent, WTI)
- Commodity prices (Gold, Silver, etc.)
- Weather real-time
- Earthquakes
- Currency exchange rates
- Stock indices
- All overlaid on interactive world map
"""

import streamlit as st
try:
    import folium
    from folium.plugins import HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
try:
    from streamlit_folium import st_folium
    HAS_ST_FOLIUM = True
except ImportError:
    HAS_ST_FOLIUM = False
import html as html_module
import requests
from datetime import datetime, timedelta
import math
import random
import pandas as pd
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import UI components (separate try blocks so one failure doesn't break all)
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call, log_exception
except Exception:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None
    log_exception = lambda *args, **kwargs: None

try:
    from src.ui_components import hero_section, category_header, stats_grid
except Exception:
    hero_section = lambda *args, **kwargs: None
    category_header = lambda *args, **kwargs: None
    stats_grid = lambda *args, **kwargs: None

try:
    from src.ui_advanced import metric_card, progress_ring, alert_box, data_table_enhanced
except Exception:
    metric_card = lambda *args, **kwargs: None
    progress_ring = lambda *args, **kwargs: None
    alert_box = lambda *args, **kwargs: None
    data_table_enhanced = lambda *args, **kwargs: None

try:
    from src.lazy_data_loader import get_lazy_loader, ProgressiveDataFetcher, MapDataPaginator
except Exception:
    get_lazy_loader = lambda: None
    ProgressiveDataFetcher = None
    MapDataPaginator = None

try:
    from src.new_data_sources import (
        fetch_global_webcams, fetch_ocean_conditions, fetch_volcano_activity,
        fetch_satellite_positions, fetch_radiation_levels, fetch_global_winds,
        fetch_meteor_showers
    )
except Exception:
    fetch_global_webcams = lambda: {"success": False}
    fetch_ocean_conditions = lambda: {"success": False}
    fetch_volcano_activity = lambda: {"success": False}
    fetch_satellite_positions = lambda: {"success": False}
    fetch_radiation_levels = lambda: {"success": False}
    fetch_global_winds = lambda: {"success": False}
    fetch_meteor_showers = lambda: {"success": False}

try:
    from src.extended_data_sources import (
        fetch_river_levels, fetch_snow_cover, fetch_sea_ice_extent,
        fetch_tsunami_warnings, fetch_hurricane_tracking, fetch_solar_wind_realtime,
        fetch_asteroid_approaches, fetch_soil_moisture, fetch_wildfire_smoke,
        fetch_global_temperature_anomaly
    )
except Exception:
    fetch_river_levels = lambda: {"success": False, "error": "Not available"}
    fetch_snow_cover = lambda: {"success": False, "error": "Not available"}
    fetch_sea_ice_extent = lambda: {"success": False, "error": "Not available"}
    fetch_tsunami_warnings = lambda: {"success": False, "error": "Not available"}
    fetch_hurricane_tracking = lambda: {"success": False, "error": "Not available"}
    fetch_solar_wind_realtime = lambda: {"success": False, "error": "Not available"}
    fetch_asteroid_approaches = lambda: {"success": False, "error": "Not available"}
    fetch_soil_moisture = lambda: {"success": False, "error": "Not available"}
    fetch_wildfire_smoke = lambda: {"success": False, "error": "Not available"}
    fetch_global_temperature_anomaly = lambda: {"success": False, "error": "Not available"}

# Note: extended_data_sources_v2 functions available but loaded on-demand via Phase 5


@st.cache_data(ttl=300)
def _fetch_kp_index() -> str:
    """Fetch K-index from NOAA (cached 5 min)."""
    try:
        resp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 1:
                return str(data[-1][1])
    except Exception:
        pass
    return "N/A"


# Major world cities for data display
WORLD_CITIES = [
    {"name": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "region": "North America"},
    {"name": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "region": "Europe"},
    {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "region": "Asia"},
    {"name": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "region": "Europe"},
    {"name": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "region": "Middle East"},
    {"name": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "region": "Asia"},
    {"name": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "region": "Oceania"},
    {"name": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "region": "South America"},
    {"name": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "region": "Asia"},
    {"name": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "region": "Europe"},
    {"name": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074, "region": "Asia"},
    {"name": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "region": "North America"},
    {"name": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "region": "Africa"},
    {"name": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "region": "Africa"},
    {"name": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "region": "South America"},
]


@st.cache_data(ttl=900)
def fetch_active_wildfires() -> Dict:
    """
    Fetch active wildfire data from NASA FIRMS (Fire Information for Resource Management System).
    Returns last 24h fires worldwide.
    """
    try:
        # NASA FIRMS MODIS data (last 24h, worldwide)
        url = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        # Parse CSV
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return {"success": False, "fires": []}

        headers = lines[0].split(',')
        fires = []

        for line in lines[1:101]:  # First 100 fires
            values = line.split(',')
            if len(values) >= 4:
                try:
                    fires.append({
                        "lat": float(values[0]),
                        "lon": float(values[1]),
                        "brightness": float(values[2]) if values[2] else 0,
                        "confidence": values[8] if len(values) > 8 else "unknown"
                    })
                except (ValueError, IndexError):
                    continue

        return {"success": True, "fires": fires, "total": len(fires)}

    except Exception as e:
        return {"success": False, "fires": [], "error": str(e)}


@st.cache_data(ttl=900)
def fetch_aircraft_traffic() -> Dict:
    """
    Fetch real-time aircraft positions from OpenSky Network (free API, no key needed).
    Returns sample of current aircraft in flight.
    """
    try:
        # OpenSky Network - all current flights (limited to avoid rate limit)
        url = "https://opensky-network.org/api/states/all"

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()

        if not data or 'states' not in data:
            return {"success": False, "aircraft": []}

        aircraft = []
        for state in data['states'][:50]:  # First 50 aircraft
            if state[5] is not None and state[6] is not None:  # Has position
                aircraft.append({
                    "callsign": (state[1] or "Unknown").strip(),
                    "lat": state[6],
                    "lon": state[5],
                    "altitude": state[7] if state[7] else 0,
                    "velocity": state[9] if state[9] else 0,
                    "country": state[2] or "Unknown"
                })

        return {"success": True, "aircraft": aircraft, "total": len(aircraft)}

    except Exception as e:
        return {"success": False, "aircraft": [], "error": str(e)}


@st.cache_data(ttl=900)
def fetch_space_weather() -> Dict:
    """
    Fetch space weather data from NOAA Space Weather Prediction Center.
    Uses 6-hour plasma and mag endpoints (smaller/faster than 7-day).
    Fetches both in parallel to minimize total time.
    """
    try:
        solar_wind_speed = 0.0
        density = 0.0
        temperature = 0.0
        bz_gsm = 0.0
        bt = 0.0
        timestamp = ""

        def _fetch_plasma():
            """Fetch plasma data (speed, density, temperature)."""
            # Use 6-hour endpoint (much smaller than 7-day)
            resp = requests.get(
                "https://services.swpc.noaa.gov/products/solar-wind/plasma-6-hour.json",
                timeout=8
            )
            resp.raise_for_status()
            return resp.json()

        def _fetch_mag():
            """Fetch magnetic field data (Bz, Bt)."""
            resp = requests.get(
                "https://services.swpc.noaa.gov/products/solar-wind/mag-6-hour.json",
                timeout=8
            )
            resp.raise_for_status()
            return resp.json()

        # Fetch plasma and mag in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            plasma_future = executor.submit(_fetch_plasma)
            mag_future = executor.submit(_fetch_mag)

            # Parse plasma data
            try:
                plasma_data = plasma_future.result(timeout=10)
                if isinstance(plasma_data, list) and len(plasma_data) > 1:
                    headers = plasma_data[0]
                    idx_time = headers.index("time_tag") if "time_tag" in headers else 0
                    idx_density = headers.index("density") if "density" in headers else 1
                    idx_speed = headers.index("speed") if "speed" in headers else 2
                    idx_temp = headers.index("temperature") if "temperature" in headers else 3
                    for row in reversed(plasma_data[1:]):
                        if row[idx_speed] is not None:
                            solar_wind_speed = float(row[idx_speed])
                            density = float(row[idx_density]) if row[idx_density] is not None else 0.0
                            temperature = float(row[idx_temp]) if row[idx_temp] is not None else 0.0
                            timestamp = str(row[idx_time])
                            break
            except Exception:
                # Fallback to summary endpoint
                try:
                    resp = requests.get(
                        "https://services.swpc.noaa.gov/products/summary/solar-wind-speed.json",
                        timeout=5
                    )
                    resp.raise_for_status()
                    summary = resp.json()
                    if isinstance(summary, dict):
                        solar_wind_speed = float(summary.get("WindSpeed", 0))
                        timestamp = summary.get("TimeStamp", "")
                except Exception:
                    pass

            # Parse mag data
            try:
                mag_data = mag_future.result(timeout=10)
                if isinstance(mag_data, list) and len(mag_data) > 1:
                    headers = mag_data[0]
                    idx_bz = headers.index("bz_gsm") if "bz_gsm" in headers else 3
                    idx_bt = headers.index("bt") if "bt" in headers else 6
                    for row in reversed(mag_data[1:]):
                        if row[idx_bz] is not None:
                            bz_gsm = float(row[idx_bz])
                            bt = float(row[idx_bt]) if row[idx_bt] is not None else 0.0
                            break
            except Exception:
                pass

        if solar_wind_speed > 0:
            space_data = {
                "solar_wind_speed": solar_wind_speed,
                "density": density,
                "temperature": temperature,
                "bz_gsm": bz_gsm,
                "bt": bt,
                "timestamp": timestamp,
            }
            return {"success": True, "data": space_data, **space_data}

        return {"success": False, "data": {}}

    except Exception:
        return {"success": False, "data": {}, "solar_wind_speed": 0}


@st.cache_data(ttl=900)
def fetch_marine_traffic() -> Dict:
    """
    Fetch marine vessel positions from Finland Digitraffic AIS (free, no key).
    Provides real-time ship positions for Baltic Sea / global shipping lanes.
    """
    try:
        # Finland Digitraffic - free public AIS API (no auth needed)
        # Covers Baltic Sea with real vessel data
        regions = [
            {"lat": 60.1, "lon": 24.9, "radius": 200, "name": "Baltic Sea"},
            {"lat": 51.9, "lon": 1.5, "radius": 150, "name": "North Sea"},
            {"lat": 36.0, "lon": 14.4, "radius": 150, "name": "Mediterranean"},
        ]

        ships_data = []
        seen_mmsi = set()

        def fetch_region(region):
            url = (
                f"https://meri.digitraffic.fi/api/ais/v1/locations"
                f"?latitude={region['lat']}&longitude={region['lon']}"
                f"&radius={region['radius']}&from=0"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json(), region["name"]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fetch_region, r): r for r in regions}
            for future in futures:
                try:
                    geojson, region_name = future.result(timeout=12)
                    features = geojson.get("features", [])
                    for feat in features[:100]:
                        props = feat.get("properties", {})
                        mmsi = props.get("mmsi", 0)
                        if mmsi in seen_mmsi:
                            continue
                        seen_mmsi.add(mmsi)
                        geom = feat.get("geometry", {})
                        coords = geom.get("coordinates", [0, 0])
                        ships_data.append({
                            "mmsi": mmsi,
                            "latitude": coords[1] if len(coords) > 1 else 0,
                            "longitude": coords[0] if len(coords) > 0 else 0,
                            "speed": props.get("sog", 0),
                            "heading": props.get("heading", 0),
                            "course": props.get("cog", 0),
                            "nav_status": props.get("navStat", -1),
                            "region": region_name,
                            "timestamp": props.get("timestamp", ""),
                        })
                except Exception:
                    continue

        return {
            "success": True,
            "ships": ships_data,
            "data": ships_data,
            "total": len(ships_data)
        }
    except Exception as e:
        return {"success": False, "ships": [], "data": [], "error": str(e)}


@st.cache_data(ttl=900)
def fetch_natural_disasters() -> Dict:
    """
    Fetch active natural disasters from GDACS (Global Disaster Alert and Coordination System).
    Free GeoJSON API, no key required.
    """
    try:
        url = (
            "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
            "?eventlist=EQ,TC,FL,VO,DR,WF&alertlevel=Green;Orange;Red&limit=50"
        )

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        geojson = response.json()
        features = geojson.get("features", [])

        event_type_map = {
            "EQ": "Earthquake", "TC": "Tropical Cyclone", "FL": "Flood",
            "VO": "Volcano", "DR": "Drought", "WF": "Wildfire"
        }

        disasters_data = []
        for feat in features[:50]:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])
            severity = props.get("severitydata", {})
            etype = props.get("eventtype", "")

            disasters_data.append({
                "name": props.get("name", "Unknown Event"),
                "type": event_type_map.get(etype, etype),
                "type_code": etype,
                "country": props.get("country", "Unknown"),
                "alert_level": props.get("alertlevel", "Green"),
                "latitude": coords[1] if len(coords) > 1 else 0,
                "longitude": coords[0] if len(coords) > 0 else 0,
                "date": props.get("fromdate", ""),
                "severity": severity.get("severity", 0),
                "severity_text": severity.get("severitytext", ""),
                "description": props.get("description", ""),
            })

        return {
            "success": True,
            "disasters": disasters_data,
            "data": disasters_data,
            "total": len(disasters_data)
        }
    except Exception as e:
        return {"success": False, "disasters": [], "data": [], "error": str(e)}


@st.cache_data(ttl=900)
def fetch_solar_activity() -> Dict:
    """
    Fetch solar flares and sunspot data from NOAA.
    """
    try:
        # NOAA Solar flare data
        url = "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data and len(data) > 0:
            latest = data[-1]

            solar_data = {
                "flux": latest.get("flux", 0),
                "timestamp": latest.get("time_tag", "")
            }

            return {
                "success": True,
                "data": solar_data,
                **solar_data
            }

        return {"success": False, "data": {}}

    except Exception as e:
        return {"success": False, "data": {}, "error": str(e)}


@st.cache_data(ttl=900)
def fetch_iss_location() -> Dict:
    """
    Fetch current International Space Station location.
    Free API, no key required.
    """
    try:
        url = "http://api.open-notify.org/iss-now.json"

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data.get("message") == "success":
            pos = data.get("iss_position", {})

            iss_data = {
                "latitude": float(pos.get("latitude", 0)),
                "longitude": float(pos.get("longitude", 0)),
                "timestamp": data.get("timestamp", 0)
            }

            return {
                "success": True,
                "data": iss_data,
                **iss_data
            }

        return {"success": False, "data": {}}

    except Exception as e:
        return {"success": False, "data": {}, "error": str(e)}




@st.cache_data(ttl=900)
def fetch_aurora_forecast() -> Dict:
    """
    Fetch aurora borealis forecast from NOAA.
    Free API, shows where aurora is visible.
    """
    try:
        # NOAA Aurora 30-minute forecast
        url = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # API returns dict with "coordinates" key containing list of [lon, lat, intensity]
        if data and "coordinates" in data:
            coordinates = data["coordinates"]

            # Get coordinates where aurora is visible
            aurora_points = []
            for point in coordinates[:200]:  # First 200 points with aurora activity
                try:
                    lon = float(point[0])
                    lat = float(point[1])
                    intensity = float(point[2])

                    # Only include points with visible aurora (intensity > 20)
                    if intensity > 20:
                        aurora_points.append({
                            "lat": lat,
                            "lon": lon,
                            "intensity": intensity
                        })
                except (ValueError, IndexError, TypeError):
                    continue

            return {
                "success": True,
                "forecast_points": aurora_points,
                "total": len(aurora_points),
                "observation_time": data.get("Observation Time"),
                "forecast_time": data.get("Forecast Time")
            }

        return {"success": False, "forecast_points": []}

    except Exception as e:
        return {"success": False, "forecast_points": [], "error": str(e)}


@st.cache_data(ttl=900)
def fetch_air_pollution_detailed() -> Dict:
    """
    Fetch real-time air pollution data using Open-Meteo Air Quality API (FREE, no key).
    """
    # Cities to check (worldwide coverage)
    cities_to_check = [
        {"city": "Delhi", "country": "India", "lat": 28.7041, "lon": 77.1025},
        {"city": "Dhaka", "country": "Bangladesh", "lat": 23.8103, "lon": 90.4125},
        {"city": "Lahore", "country": "Pakistan", "lat": 31.5497, "lon": 74.3436},
        {"city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074},
        {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777},
        {"city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737},
        {"city": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357},
        {"city": "Jakarta", "country": "Indonesia", "lat": -6.2088, "lon": 106.8456},
        {"city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018},
        {"city": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333},
        {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332},
        {"city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437},
        {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278},
        {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522},
        {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503},
        {"city": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198},
        {"city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093},
        {"city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832},
        {"city": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708},
        {"city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173},
    ]

    try:
        # Open-Meteo Air Quality API - FREE, no key required
        # Batch request: build comma-separated lat/lon lists
        lats = ",".join(str(c["lat"]) for c in cities_to_check)
        lons = ",".join(str(c["lon"]) for c in cities_to_check)

        url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={lats}&longitude={lons}"
            f"&current=pm2_5,pm10,nitrogen_dioxide,ozone"
        )

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        pollution_data = []
        # Open-Meteo returns a list when multiple coords are passed
        results = data if isinstance(data, list) else [data]

        for i, city_info in enumerate(cities_to_check):
            if i < len(results):
                current = results[i].get("current", {})
                pm25_val = current.get("pm2_5", 0) or 0
                pollution_data.append({
                    "city": city_info["city"],
                    "country": city_info["country"],
                    "pm25": round(pm25_val, 1),
                    "lat": city_info["lat"],
                    "lon": city_info["lon"],
                    "last_updated": current.get("time", datetime.now().isoformat()),
                    "source": "live"
                })

        if pollution_data:
            return {
                "success": True,
                "cities": pollution_data,
                "total": len(pollution_data),
                "source": "Open-Meteo Air Quality API (real-time)"
            }

    except Exception:
        pass

    # Fallback: representative average data when API fails
    # Values based on WHO global air quality database averages
    _fallback_pm25 = {
        "Delhi": 120, "Dhaka": 130, "Lahore": 140, "Beijing": 70, "Mumbai": 80,
        "Shanghai": 50, "Cairo": 90, "Jakarta": 65, "Bangkok": 45, "São Paulo": 30,
        "Mexico City": 40, "Los Angeles": 22, "London": 14, "Paris": 12, "Tokyo": 10,
        "Singapore": 15, "Sydney": 7, "Toronto": 9, "Dubai": 38, "Moscow": 20,
    }
    try:
        fallback_data = []
        for city_info in cities_to_check:
            fallback_data.append({
                "city": city_info["city"],
                "country": city_info["country"],
                "pm25": _fallback_pm25.get(city_info["city"], 25),
                "lat": city_info["lat"],
                "lon": city_info["lon"],
                "last_updated": datetime.now().isoformat(),
                "source": "estimated"
            })
        return {
            "success": True,
            "cities": fallback_data,
            "total": len(fallback_data),
            "source": "fallback (API temporarily unavailable)"
        }
    except Exception as e:
        return {"success": False, "cities": [], "error": str(e)}


def fetch_stock_indices() -> Dict:
    """
    Fetch REAL major stock market indices using Yahoo Finance API (100% FREE).
    No API key required!
    """
    try:
        import yfinance as yf

        # Major indices with their Yahoo Finance tickers
        indices = {
            "^GSPC": {"name": "S&P 500", "country": "USA"},
            "^IXIC": {"name": "NASDAQ", "country": "USA"},
            "^DJI": {"name": "DOW", "country": "USA"}
        }

        indices_data = []

        for ticker, info in indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")

                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    open_price = float(hist['Open'].iloc[0])
                    change_percent = ((current_price - open_price) / open_price) * 100

                    indices_data.append({
                        "name": info["name"],
                        "value": round(current_price, 2),
                        "change_percent": round(change_percent, 2),
                        "country": info["country"]
                    })
            except Exception:
                # Skip this index if error
                continue

        if indices_data:
            return {
                "success": True,
                "indices": indices_data,
                "total": len(indices_data)
            }

        # Fallback if no indices fetched
        raise Exception("No index data available")

    except Exception as e:
        # Fallback to representative data
        indices_data = [
            {"name": "S&P 500", "value": 5127.50, "change_percent": 0.85, "country": "USA"},
            {"name": "NASDAQ", "value": 16085.30, "change_percent": 1.12, "country": "USA"},
            {"name": "DOW", "value": 38790.43, "change_percent": 0.45, "country": "USA"}
        ]

        return {
            "success": True,
            "indices": indices_data,
            "total": len(indices_data),
            "is_fallback": True,
            "note": "Using representative data (Yahoo Finance unavailable)"
        }


@st.cache_data(ttl=900)
def fetch_tide_data() -> Dict:
    """
    Fetch tide predictions for major coastal cities.
    Using NOAA Tides & Currents API (free).
    """
    try:
        # NOAA Tides API - example for one station
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        params = {
            "station": "8454000",  # Providence, RI
            "product": "predictions",
            "datum": "MLLW",
            "time_zone": "gmt",
            "units": "metric",
            "interval": "hilo",
            "format": "json",
            "date": "today"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("predictions"):
            return {
                "success": True,
                "predictions": data["predictions"][:4],  # Next 4 tides
                "station": "Providence, RI"
            }

        return {"success": False}

    except Exception as e:
        return {"success": False, "predictions": [], "error": str(e)}




def fetch_oil_prices() -> Dict:
    """
    Fetch REAL oil prices (Brent, WTI) using Yahoo Finance API (100% FREE).
    No API key required!
    """
    try:
        import yfinance as yf

        # Brent Crude Oil Futures ticker
        brent_ticker = yf.Ticker("BZ=F")
        brent_data = brent_ticker.history(period="1d")

        # WTI Crude Oil Futures ticker
        wti_ticker = yf.Ticker("CL=F")
        wti_data = wti_ticker.history(period="1d")

        if not brent_data.empty and not wti_data.empty:
            brent_price = float(brent_data['Close'].iloc[-1])
            wti_price = float(wti_data['Close'].iloc[-1])

            # Calculate 24h change if data available
            brent_change = 0
            if len(brent_data) > 1:
                brent_change = ((brent_price - brent_data['Open'].iloc[0]) / brent_data['Open'].iloc[0]) * 100

            oil_data = {
                "brent": round(brent_price, 2),
                "wti": round(wti_price, 2),
                "change_24h": round(brent_change, 2),
                "last_updated": datetime.now().isoformat()
            }

            return {
                "success": True,
                "data": oil_data,
                **oil_data  # Keep backward compatibility
            }

        # Fallback if no data
        raise Exception("No price data available")

    except Exception as e:
        if log_exception:
            log_exception(e, "Fetching oil prices", severity="WARNING")

        # Fallback to representative data
        oil_data = {
            "brent": 85.50,
            "wti": 82.30,
            "change_24h": 1.2,
            "last_updated": datetime.now().isoformat()
        }

        return {
            "success": True,
            "data": oil_data,
            **oil_data,
            "is_fallback": True,
            "note": "Using representative data (Yahoo Finance unavailable)"
        }


@st.cache_data(ttl=900)
def fetch_crypto_prices() -> Dict:
    """Fetch cryptocurrency prices from CoinGecko (free API)."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,tether,binancecoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data": data,
                "last_updated": datetime.now().isoformat()
            }

        return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        if log_exception:
            log_exception(e, "Fetching crypto prices", severity="WARNING")
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=900)
def fetch_exchange_rates() -> Dict:
    """Fetch currency exchange rates from ExchangeRate-API (free)."""
    try:
        # Free API: https://www.exchangerate-api.com
        url = "https://api.exchangerate-api.com/v4/latest/USD"

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            return {
                "success": True,
                "base": "USD",
                "rates": rates,
                "data": rates,  # For test compatibility
                "last_updated": data.get("time_last_updated")
            }

        return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        if log_exception:
            log_exception(e, "Fetching exchange rates", severity="WARNING")
        return {"success": False, "error": str(e)}


@st.cache_data(ttl=900)
def fetch_world_weather_summary():
    """Fetch weather for major cities (parallel). Returns list for backward compatibility."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = []

    def get_city_weather(city):
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": city["lat"],
                "longitude": city["lon"],
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "auto"
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})

                return {
                    "city": city["name"],
                    "country": city["country"],
                    "region": city["region"],
                    "lat": city["lat"],
                    "lon": city["lon"],
                    "temperature": current.get("temperature_2m"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "weather_code": current.get("weather_code")
                }
        except Exception:
            pass

        return None

    # Fetch in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_city_weather, city): city for city in WORLD_CITIES}

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    # Return list directly for backward compatibility
    # (Most code expects a list, not {"success": True, "cities": [...]})
    return results


@st.cache_data(ttl=900)
def fetch_recent_earthquakes_global() -> Dict:
    """Fetch recent earthquakes worldwide."""
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"

        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])

            return {
                "success": True,
                "total": len(features),
                "features": features[:50],  # Top 50
                "last_updated": datetime.now().isoformat()
            }

        return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        if log_exception:
            log_exception(e, "Fetching earthquakes", severity="WARNING")
        return {"success": False, "error": str(e)}


def create_global_map(weather_data, earthquakes_data, fires_data=None, aircraft_data=None, iss_data=None, aurora_data=None, pollution_data=None,
                       webcams_data=None, ocean_data=None, volcanoes_data=None, satellites_data=None, radiation_data=None,
                       rivers_data=None, hurricanes_data=None, asteroids_data=None,
                       marine_data=None, disasters_data=None) -> folium.Map:
    """Create interactive world map with ALL 35+ data layers (includes Phase 5)."""

    # Create map centered on world
    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
        max_bounds=True
    )

    # Add weather markers for cities
    if weather_data:
        for city in weather_data:
            # Color based on temperature
            temp = city.get("temperature", 20)
            if temp < 0:
                color = "blue"
            elif temp < 15:
                color = "lightblue"
            elif temp < 25:
                color = "green"
            elif temp < 35:
                color = "orange"
            else:
                color = "red"

            _city_name = html_module.escape(str(city.get('city', 'Unknown')))
            _city_country = html_module.escape(str(city.get('country', 'Unknown')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif; min-width: 200px;">
                <h4 style="margin: 0 0 0.5rem 0; color: #3b82f6;">{_city_name}, {_city_country}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>🌡️ Temperature:</strong> {temp}°C<br>
                    <strong>💨 Wind:</strong> {city.get('wind_speed', 'N/A')} km/h
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[city["lat"], city["lon"]],
                radius=8,
                popup=folium.Popup(popup_html, max_width=300),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)

    # Add earthquake markers
    if earthquakes_data and earthquakes_data.get("success"):
        for quake in earthquakes_data["features"][:30]:  # Top 30
            props = quake.get("properties", {})
            coords = quake.get("geometry", {}).get("coordinates", [])

            if len(coords) >= 2:
                mag = props.get("mag", 0)
                place = props.get("place", "Unknown")

                # Size based on magnitude
                radius = mag * 3

                # Color based on magnitude
                if mag < 5:
                    color = "yellow"
                elif mag < 6:
                    color = "orange"
                else:
                    color = "red"

                _place = html_module.escape(str(place))
                popup_html = f"""
                <div style="font-family: Inter, sans-serif;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ef4444;">🌋 Magnitude {mag}</h4>
                    <p style="margin: 0.25rem 0;">
                        <strong>Location:</strong> {_place}<br>
                        <strong>Time:</strong> {datetime.fromtimestamp(props.get('time', 0)/1000).strftime('%Y-%m-%d %H:%M')}
                    </p>
                </div>
                """

                folium.CircleMarker(
                    location=[coords[1], coords[0]],
                    radius=radius,
                    popup=folium.Popup(popup_html, max_width=300),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6,
                    weight=2
                ).add_to(m)

    # Add wildfire markers
    if fires_data and fires_data.get("success"):
        for fire in fires_data.get("fires", [])[:50]:  # First 50 fires
            _fire_confidence = html_module.escape(str(fire.get('confidence', 'Unknown')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #ef4444;">🔥 Active Fire</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Brightness:</strong> {fire.get('brightness', 'N/A')} K<br>
                    <strong>Confidence:</strong> {_fire_confidence}
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[fire["lat"], fire["lon"]],
                radius=4,
                popup=folium.Popup(popup_html, max_width=250),
                color="#ff6b6b",
                fill=True,
                fillColor="#ff6b6b",
                fillOpacity=0.8,
                weight=1
            ).add_to(m)

    # Add aircraft markers
    if aircraft_data and aircraft_data.get("success"):
        for aircraft in aircraft_data.get("aircraft", [])[:30]:  # First 30 aircraft
            _callsign = html_module.escape(str(aircraft.get('callsign', 'Unknown')))
            _ac_country = html_module.escape(str(aircraft.get('country', 'Unknown')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #3b82f6;">✈️ {_callsign}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Altitude:</strong> {aircraft.get('altitude', 0):.0f} m<br>
                    <strong>Speed:</strong> {aircraft.get('velocity', 0):.0f} m/s<br>
                    <strong>Country:</strong> {_ac_country}
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[aircraft["lat"], aircraft["lon"]],
                radius=3,
                popup=folium.Popup(popup_html, max_width=250),
                color="#3b82f6",
                fill=True,
                fillColor="#3b82f6",
                fillOpacity=0.7,
                weight=1
            ).add_to(m)

    # Add ISS marker (special - large and prominent)
    if iss_data and iss_data.get("success"):
        iss_lat = iss_data.get("latitude", 0)
        iss_lon = iss_data.get("longitude", 0)

        popup_html = f"""
        <div style="font-family: Inter, sans-serif;">
            <h4 style="margin: 0 0 0.5rem 0; color: #10b981;">🛰️ International Space Station</h4>
            <p style="margin: 0.25rem 0;">
                <strong>Position:</strong> {iss_lat:.2f}°, {iss_lon:.2f}°<br>
                <strong>Altitude:</strong> ~408 km<br>
                <strong>Speed:</strong> ~27,600 km/h
            </p>
        </div>
        """

        # ISS marker - special icon
        folium.Marker(
            location=[iss_lat, iss_lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color='green', icon='satellite', prefix='fa'),
            tooltip="International Space Station (ISS)"
        ).add_to(m)

    # Add aurora forecast zones
    if aurora_data and aurora_data.get("success"):
        for point in aurora_data.get("forecast_points", [])[:50]:  # First 50 points
            intensity = point.get("intensity", 0)

            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #a855f7;">🌌 Aurora Visible</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Intensity:</strong> {intensity:.1f}<br>
                    <strong>Best viewing:</strong> Clear, dark skies
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[point["lat"], point["lon"]],
                radius=6,
                popup=folium.Popup(popup_html, max_width=250),
                color="#a855f7",
                fill=True,
                fillColor="#a855f7",
                fillOpacity=min(intensity / 100, 0.9),
                weight=1
            ).add_to(m)

    # Add pollution hotspots
    if pollution_data and pollution_data.get("success"):
        for city in pollution_data.get("cities", [])[:20]:
            pm25 = city.get("pm25", 0)

            # Color based on AQI
            if pm25 < 12:
                color, status = "#10b981", "Good"
            elif pm25 < 35:
                color, status = "#f59e0b", "Moderate"
            elif pm25 < 55:
                color, status = "#ef4444", "Unhealthy"
            else:
                color, status = "#991b1b", "Hazardous"

            _poll_city = html_module.escape(str(city.get('city', 'Unknown')))
            _poll_country = html_module.escape(str(city.get('country', 'Unknown')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: {color};">💨 {_poll_city}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>PM2.5:</strong> {pm25:.1f} μg/m³<br>
                    <strong>Status:</strong> {status}<br>
                    <strong>Country:</strong> {_poll_country}
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[city.get("lat", 0), city.get("lon", 0)],
                radius=5,
                popup=folium.Popup(popup_html, max_width=250),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)

    # Add webcam markers
    if webcams_data and webcams_data.get("success"):
        for webcam in webcams_data.get("webcams", []):
            _wc_name = html_module.escape(str(webcam.get('name', 'Webcam')))
            _wc_country = html_module.escape(str(webcam.get('country', 'Unknown')))
            _wc_raw_url = str(webcam.get('url', '#'))
            _wc_url = html_module.escape(_wc_raw_url) if _wc_raw_url.startswith('http') else '#'
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #06b6d4;">📹 {_wc_name}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Location:</strong> {_wc_country}<br>
                    <a href="{_wc_url}" target="_blank" style="color: #06b6d4;">🔴 View Live Stream</a>
                </p>
            </div>
            """

            folium.Marker(
                location=[webcam.get("lat", 0), webcam.get("lon", 0)],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color='lightblue', icon='camera', prefix='fa'),
                tooltip=_wc_name
            ).add_to(m)

    # Add ocean buoy markers
    if ocean_data and ocean_data.get("success"):
        for buoy in ocean_data.get("buoys", []):
            _buoy_name = html_module.escape(str(buoy.get('name', 'Buoy')))
            _buoy_loc = html_module.escape(str(buoy.get('location', 'Unknown')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #0ea5e9;">🌊 {_buoy_name}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Location:</strong> {_buoy_loc}<br>
                    <strong>Wave Height:</strong> {buoy.get('wave_height_m', 'N/A')} m<br>
                    <strong>Water Temp:</strong> {buoy.get('water_temp_c', 'N/A')}°C<br>
                    <strong>Wind:</strong> {buoy.get('wind_speed_kph', 'N/A')} km/h
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[buoy.get("lat", 0), buoy.get("lon", 0)],
                radius=6,
                popup=folium.Popup(popup_html, max_width=300),
                color="#0ea5e9",
                fill=True,
                fillColor="#0ea5e9",
                fillOpacity=0.8,
                weight=2
            ).add_to(m)

    # Add volcano markers
    if volcanoes_data and volcanoes_data.get("success"):
        for volcano in volcanoes_data.get("volcanoes", []):
            alert = volcano.get("alert", "Normal")

            # Color by alert level
            if alert == "Advisory":
                color, icon_color = "#ef4444", 'red'
            elif alert == "Watch":
                color, icon_color = "#f59e0b", 'orange'
            else:
                color, icon_color = "#10b981", 'green'

            _vol_name = html_module.escape(str(volcano.get('name', 'Volcano')))
            _vol_country = html_module.escape(str(volcano.get('country', 'Unknown')))
            _vol_eruption = html_module.escape(str(volcano.get('last_eruption', 'Unknown')))
            _vol_alert = html_module.escape(str(alert))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: {color};">🌋 {_vol_name}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Country:</strong> {_vol_country}<br>
                    <strong>Alert Level:</strong> {_vol_alert}<br>
                    <strong>Last Activity:</strong> {_vol_eruption}
                </p>
            </div>
            """

            folium.Marker(
                location=[volcano.get("lat", 0), volcano.get("lon", 0)],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=icon_color, icon='fire', prefix='fa'),
                tooltip=f"{_vol_name} - {_vol_alert}"
            ).add_to(m)

    # Add satellite markers (beyond ISS)
    if satellites_data and satellites_data.get("success"):
        for sat in satellites_data.get("satellites", []):
            _sat_name = html_module.escape(str(sat.get('name', 'Satellite')))
            _sat_type = html_module.escape(str(sat.get('type', 'Unknown')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #8b5cf6;">🛰️ {_sat_name}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Type:</strong> {_sat_type}<br>
                    <strong>Altitude:</strong> {sat.get('altitude_km', 'N/A')} km<br>
                    <strong>Velocity:</strong> {sat.get('velocity_kms', 'N/A')} km/s
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[sat.get("lat", 0), sat.get("lon", 0)],
                radius=5,
                popup=folium.Popup(popup_html, max_width=250),
                color="#8b5cf6",
                fill=True,
                fillColor="#8b5cf6",
                fillOpacity=0.9,
                weight=2
            ).add_to(m)

    # Add radiation monitoring stations
    if radiation_data and radiation_data.get("success"):
        for station in radiation_data.get("stations", []):
            cpm = station.get("cpm", 0)

            # Color by radiation level
            if cpm < 50:
                color = "#10b981"  # Green - Normal
            elif cpm < 100:
                color = "#f59e0b"  # Orange - Elevated
            else:
                color = "#ef4444"  # Red - High

            _rad_city = html_module.escape(str(station.get('city', 'Station')))
            _rad_country = html_module.escape(str(station.get('country', 'Unknown')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: {color};">☢️ {_rad_city}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Country:</strong> {_rad_country}<br>
                    <strong>CPM:</strong> {cpm}<br>
                    <strong>µSv/h:</strong> {station.get('usv_h', 'N/A')}<br>
                    <strong>Status:</strong> {'Normal' if cpm < 50 else 'Elevated' if cpm < 100 else 'High'}
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[station.get("lat", 0), station.get("lon", 0)],
                radius=7,
                popup=folium.Popup(popup_html, max_width=300),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=3
            ).add_to(m)

    # === PHASE 5 DATA LAYERS ===

    # River Levels (USGS)
    if rivers_data and rivers_data.get("success"):
        for river in rivers_data.get("rivers", []):
            _riv_name = html_module.escape(str(river.get('name', 'River')))
            _riv_param = html_module.escape(str(river.get('parameter', 'N/A')))
            _riv_loc = html_module.escape(str(river.get('location', 'N/A')))
            _riv_unit = html_module.escape(str(river.get('unit', '')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #0ea5e9;">🏞️ {_riv_name}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Value:</strong> {river.get('value', 0):.2f} {_riv_unit}<br>
                    <strong>Parameter:</strong> {_riv_param}<br>
                    <strong>Location:</strong> {_riv_loc}
                </p>
            </div>
            """

            folium.Marker(
                location=[river.get("lat", 0), river.get("lon", 0)],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='blue', icon='tint', prefix='fa'),
                tooltip=_riv_name
            ).add_to(m)

    # Hurricane/Typhoon Tracking
    if hurricanes_data and hurricanes_data.get("success"):
        for storm in hurricanes_data.get("active_storms", []):
            intensity = storm.get("intensity", "Unknown")
            if "major" in intensity.lower() or "hurricane" in intensity.lower():
                color_storm = "#ef4444"  # Red for major
            elif "tropical storm" in intensity.lower():
                color_storm = "#f59e0b"  # Orange for TS
            else:
                color_storm = "#eab308"  # Yellow for TD

            _storm_name = html_module.escape(str(storm.get('name', 'Storm')))
            _storm_class = html_module.escape(str(storm.get('classification', 'N/A')))
            _storm_intensity = html_module.escape(str(storm.get('intensity', 'N/A')))
            _storm_wind = html_module.escape(str(storm.get('wind_speed', 'N/A')))
            _storm_pressure = html_module.escape(str(storm.get('pressure', 'N/A')))
            _storm_movement = html_module.escape(str(storm.get('movement', 'N/A')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: {color_storm};">🌀 {_storm_name}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Classification:</strong> {_storm_class}<br>
                    <strong>Intensity:</strong> {_storm_intensity}<br>
                    <strong>Wind Speed:</strong> {_storm_wind}<br>
                    <strong>Pressure:</strong> {_storm_pressure}<br>
                    <strong>Movement:</strong> {_storm_movement}
                </p>
            </div>
            """

            folium.CircleMarker(
                location=[storm.get("latitude", 0), storm.get("longitude", 0)],
                radius=15,
                popup=folium.Popup(popup_html, max_width=300),
                color=color_storm,
                fill=True,
                fillColor=color_storm,
                fillOpacity=0.8,
                weight=4,
                tooltip=f"🌀 {_storm_name}"
            ).add_to(m)

    # Near-Earth Asteroids (closest approaches)
    if asteroids_data and asteroids_data.get("success"):
        # Show only potentially hazardous or very close asteroids
        hazardous = [a for a in asteroids_data.get("asteroids", []) if a.get("potentially_hazardous")]

        for asteroid in hazardous[:10]:  # Top 10 hazardous
            _ast_name = html_module.escape(str(asteroid.get('name', 'Asteroid')))
            _ast_date = html_module.escape(str(asteroid.get('approach_date', 'N/A')))
            popup_html = f"""
            <div style="font-family: Inter, sans-serif;">
                <h4 style="margin: 0 0 0.5rem 0; color: #ef4444;">☄️ {_ast_name}</h4>
                <p style="margin: 0.25rem 0;">
                    <strong>Diameter:</strong> {asteroid.get('diameter_m', 0):.0f} meters<br>
                    <strong>Velocity:</strong> {asteroid.get('velocity_kmh', 0):,.0f} km/h<br>
                    <strong>Miss Distance:</strong> {asteroid.get('miss_distance_km', 0):,.0f} km<br>
                    <strong>Approach Date:</strong> {_ast_date}<br>
                    <strong>Status:</strong> <span style="color: #ef4444; font-weight: bold;">POTENTIALLY HAZARDOUS</span>
                </p>
            </div>
            """

            # Position asteroids in orbit visualization (simplified)
            # Use a circular pattern around Earth
            angle = hash(asteroid.get('name', '')) % 360
            radius_deg = 30  # Visual radius
            lat = radius_deg * math.sin(math.radians(angle))
            lon = radius_deg * math.cos(math.radians(angle))

            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_html, max_width=300),
                color="#ef4444",
                fill=True,
                fillColor="#ef4444",
                fillOpacity=0.9,
                weight=3,
                tooltip=f"☄️ {_ast_name} - HAZARDOUS"
            ).add_to(m)

    # === HEAT MAP OVERLAY FOR TEMPERATURE DISTRIBUTION ===
    # Add temperature heatmap layer for visual temperature distribution
    if weather_data and len(weather_data) > 0:
        heat_data = []
        for city in weather_data:
            if isinstance(city, dict) and city.get("lat") and city.get("temperature"):
                # Weight by temperature (normalized 0-1 range, assume -20 to 40°C)
                temp = city.get("temperature", 20)
                weight = (temp + 20) / 60  # Normalize to 0-1
                weight = max(0.1, min(1.0, weight))  # Clamp to valid range

                heat_data.append([
                    city.get("lat"),
                    city.get("lon"),
                    weight
                ])

        if heat_data:
            HeatMap(
                heat_data,
                name="Temperature Heat Map",
                min_opacity=0.2,
                max_opacity=0.6,
                radius=25,
                blur=20,
                gradient={
                    0.0: 'blue',
                    0.3: 'cyan',
                    0.5: 'lime',
                    0.7: 'yellow',
                    1.0: 'red'
                }
            ).add_to(m)

    # Add marine traffic markers
    if marine_data and marine_data.get("success"):
        for ship in marine_data.get("ships", [])[:100]:
            lat = ship.get("latitude", 0)
            lon = ship.get("longitude", 0)
            if lat and lon:
                speed = ship.get("speed", 0)
                color = "#06b6d4" if speed > 0.5 else "#475569"
                _ship_mmsi = html_module.escape(str(ship.get('mmsi', 'N/A')))
                _ship_region = html_module.escape(str(ship.get('region', '')))
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=3,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    tooltip=f"MMSI: {_ship_mmsi} | {speed:.1f} kn | {_ship_region}"
                ).add_to(m)

    # Add disaster markers (GDACS)
    if disasters_data and disasters_data.get("success"):
        alert_colors = {"Red": "#ef4444", "Orange": "#f59e0b", "Green": "#22c55e"}
        type_icons = {"Earthquake": "🌍", "Tropical Cyclone": "🌀", "Flood": "🌊",
                      "Volcano": "🌋", "Drought": "☀️", "Wildfire": "🔥"}
        for dis in disasters_data.get("disasters", [])[:30]:
            lat = dis.get("latitude", 0)
            lon = dis.get("longitude", 0)
            if lat and lon:
                alert = dis.get("alert_level", "Green")
                color = alert_colors.get(alert, "#94a3b8")
                radius = 10 if alert == "Red" else 7 if alert == "Orange" else 5
                icon = type_icons.get(dis.get("type", ""), "⚠️")
                _dis_name = html_module.escape(str(dis.get('name', 'Event')))
                _dis_type = html_module.escape(str(dis.get('type', 'Unknown')))
                _dis_country = html_module.escape(str(dis.get('country', 'Unknown')))
                _dis_alert = html_module.escape(str(alert))
                _dis_severity = html_module.escape(str(dis.get('severity_text', 'N/A')))
                popup_html = f"""
                <div style="font-family: sans-serif; min-width: 200px;">
                    <h4 style="margin: 0 0 0.5rem 0; color: {color};">{icon} {_dis_name}</h4>
                    <p style="margin: 0.25rem 0; font-size: 0.9rem;">
                        <strong>Type:</strong> {_dis_type}<br>
                        <strong>Country:</strong> {_dis_country}<br>
                        <strong>Alert:</strong> {_dis_alert}<br>
                        <strong>Severity:</strong> {_dis_severity}
                    </p>
                </div>
                """
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=radius,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{icon} {_dis_type} - {_dis_name} ({_dis_alert})"
                ).add_to(m)

    # Add layer control to toggle heatmap
    folium.LayerControl(position='topright', collapsed=False).add_to(m)

    return m


def render_global_dashboard_realtime_tab():
    """Main render function for Global Real-Time Dashboard."""

    # Hero section
    hero_section(
        title="Global Real-Time Intelligence",
        subtitle="Live worldwide data aggregation — 22+ real-time sources monitoring Earth, Ocean & Space",
        features=[
            "15 Cities Weather",
            "Earthquakes M4.5+",
            "Active Wildfires",
            "Aircraft Tracking",
            "ISS Location",
            "Solar Activity",
            "Aurora Forecast",
            "Air Pollution (20 cities)",
            "Crypto Prices",
            "Oil Prices",
            "Stock Indices",
            "Forex (166 currencies)",
            "Space Weather",
            "Marine Traffic",
            "Global Disasters",
            "Tide Predictions",
            "Live Webcams (10 locations)",
            "Ocean Conditions (5 buoys)",
            "Active Volcanoes (8 locations)",
            "Satellites (3+ tracking)",
            "Radiation Levels (6 stations)",
            "Global Winds",
            "Meteor Showers"
        ]
    )

    st.markdown("---")

    # Fetch all data with PROGRESSIVE LOADING and SMART CACHING
    st.markdown("### 🔄 Loading Real-Time Data...")

    # Define all data sources with timeouts
    if ProgressiveDataFetcher:
        sources = [
            # Original sources
            {"name": "weather", "function": fetch_world_weather_summary, "timeout": 25},
            {"name": "quakes", "function": fetch_recent_earthquakes_global, "timeout": 15},
            {"name": "crypto", "function": fetch_crypto_prices, "timeout": 10},
            {"name": "exchange", "function": fetch_exchange_rates, "timeout": 10},
            {"name": "oil", "function": fetch_oil_prices, "timeout": 5},
            # Phase 1
            {"name": "fires", "function": fetch_active_wildfires, "timeout": 20},
            {"name": "aircraft", "function": fetch_aircraft_traffic, "timeout": 15},
            {"name": "space", "function": fetch_space_weather, "timeout": 10},
            # Phase 2
            {"name": "solar", "function": fetch_solar_activity, "timeout": 20},
            {"name": "iss", "function": fetch_iss_location, "timeout": 10},
            {"name": "marine", "function": fetch_marine_traffic, "timeout": 5},
            {"name": "disasters", "function": fetch_natural_disasters, "timeout": 15},
            # Phase 3
            {"name": "aurora", "function": fetch_aurora_forecast, "timeout": 15},
            {"name": "pollution", "function": fetch_air_pollution_detailed, "timeout": 5},
            {"name": "stocks", "function": fetch_stock_indices, "timeout": 5},
            {"name": "tides", "function": fetch_tide_data, "timeout": 10},
            # Phase 4 - NEW SOURCES!
            {"name": "webcams", "function": fetch_global_webcams, "timeout": 5},
            {"name": "ocean", "function": fetch_ocean_conditions, "timeout": 5},
            {"name": "volcanoes", "function": fetch_volcano_activity, "timeout": 5},
            {"name": "satellites", "function": fetch_satellite_positions, "timeout": 10},
            {"name": "radiation", "function": fetch_radiation_levels, "timeout": 5},
            {"name": "winds", "function": fetch_global_winds, "timeout": 5},
            {"name": "meteors", "function": fetch_meteor_showers, "timeout": 5}
        ]

        # Fetch with progress bar
        all_results = ProgressiveDataFetcher.fetch_with_progress(
            sources,
            max_workers=15,
            show_progress=True
        )

        # Extract results
        weather_data = all_results.get("weather", [])
        quakes_data = all_results.get("quakes", {})
        crypto_data = all_results.get("crypto", {})
        exchange_data = all_results.get("exchange", {})
        oil_data = all_results.get("oil", {})
        fires_data = all_results.get("fires", {})
        aircraft_data = all_results.get("aircraft", {})
        space_data = all_results.get("space", {})
        solar_data = all_results.get("solar", {})
        iss_data = all_results.get("iss", {})
        marine_data = all_results.get("marine", {})
        disasters_data = all_results.get("disasters", {})
        aurora_data = all_results.get("aurora", {})
        pollution_data = all_results.get("pollution", {})
        stocks_data = all_results.get("stocks", {})
        tides_data = all_results.get("tides", {})
        # NEW!
        webcams_data = all_results.get("webcams", {})
        ocean_data = all_results.get("ocean", {})
        volcanoes_data = all_results.get("volcanoes", {})
        satellites_data = all_results.get("satellites", {})
        radiation_data = all_results.get("radiation", {})
        winds_data = all_results.get("winds", {})
        meteors_data = all_results.get("meteors", {})

    else:
        # Fallback to standard loading if ProgressiveDataFetcher not available
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {
                "weather": executor.submit(fetch_world_weather_summary),
                "quakes": executor.submit(fetch_recent_earthquakes_global),
                "crypto": executor.submit(fetch_crypto_prices),
                "exchange": executor.submit(fetch_exchange_rates),
                "oil": executor.submit(fetch_oil_prices),
                "fires": executor.submit(fetch_active_wildfires),
                "aircraft": executor.submit(fetch_aircraft_traffic),
                "space": executor.submit(fetch_space_weather),
                "solar": executor.submit(fetch_solar_activity),
                "iss": executor.submit(fetch_iss_location),
                "marine": executor.submit(fetch_marine_traffic),
                "disasters": executor.submit(fetch_natural_disasters),
                "aurora": executor.submit(fetch_aurora_forecast),
                "pollution": executor.submit(fetch_air_pollution_detailed),
                "stocks": executor.submit(fetch_stock_indices),
                "tides": executor.submit(fetch_tide_data),
                "webcams": executor.submit(fetch_global_webcams),
                "ocean": executor.submit(fetch_ocean_conditions),
                "volcanoes": executor.submit(fetch_volcano_activity),
                "satellites": executor.submit(fetch_satellite_positions),
                "radiation": executor.submit(fetch_radiation_levels),
                "winds": executor.submit(fetch_global_winds),
                "meteors": executor.submit(fetch_meteor_showers)
            }

            # Collect results (30s timeout per future to prevent hangs)
            weather_data = futures["weather"].result(timeout=30)
            quakes_data = futures["quakes"].result(timeout=30)
            crypto_data = futures["crypto"].result(timeout=30)
            exchange_data = futures["exchange"].result(timeout=30)
            oil_data = futures["oil"].result(timeout=30)
            fires_data = futures["fires"].result(timeout=30)
            aircraft_data = futures["aircraft"].result(timeout=30)
            space_data = futures["space"].result(timeout=30)
            solar_data = futures["solar"].result(timeout=30)
            iss_data = futures["iss"].result(timeout=30)
            marine_data = futures["marine"].result(timeout=30)
            disasters_data = futures["disasters"].result(timeout=30)
            aurora_data = futures["aurora"].result(timeout=30)
            pollution_data = futures["pollution"].result(timeout=30)
            stocks_data = futures["stocks"].result(timeout=30)
            tides_data = futures["tides"].result(timeout=30)
            webcams_data = futures["webcams"].result(timeout=30)
            ocean_data = futures["ocean"].result(timeout=30)
            volcanoes_data = futures["volcanoes"].result(timeout=30)
            satellites_data = futures["satellites"].result(timeout=30)
            radiation_data = futures["radiation"].result(timeout=30)
            winds_data = futures["winds"].result(timeout=30)
            meteors_data = futures["meteors"].result(timeout=30)

    # Count how many sources loaded successfully
    all_sources = [quakes_data, fires_data, aircraft_data, space_data,
                   iss_data, aurora_data, pollution_data, crypto_data, oil_data,
                   stocks_data, exchange_data, solar_data, tides_data,
                   marine_data, disasters_data,
                   webcams_data, ocean_data, volcanoes_data, satellites_data,
                   radiation_data, winds_data, meteors_data]
    # weather_data is a list, not a dict - count it separately
    success_count = sum(1 for s in all_sources if isinstance(s, dict) and s.get("success"))
    total_count = len(all_sources)
    if isinstance(weather_data, list) and len(weather_data) > 0:
        success_count += 1
    total_count += 1  # include weather in total
    if success_count == total_count:
        st.success(f"All {total_count} data sources loaded successfully!")
    elif success_count > total_count * 0.7:
        st.info(f"{success_count}/{total_count} data sources loaded ({total_count - success_count} temporarily unavailable)")
    else:
        st.warning(f"{success_count}/{total_count} data sources loaded - some services may be temporarily down")
    st.markdown("---")

    # === MASTER DASHBOARD - UNIFIED VIEW ===
    category_header("📊 Master Intelligence Dashboard", count=success_count, icon="🌐")

    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(16, 185, 129, 0.1));
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid rgba(59, 130, 246, 0.2);">
        <h3 style="margin: 0 0 1rem 0; color: #3b82f6; text-align: center;">
            🌍 Global Real-Time Intelligence at a Glance
        </h3>
    </div>
    """, unsafe_allow_html=True)

    # Create unified metrics grid (ALL 25 sources in one view)
    master_metrics = []

    # Weather
    if weather_data:
        avg_temp = sum(c.get('temperature', 0) for c in weather_data if c.get('temperature')) / max(len([c for c in weather_data if c.get('temperature')]), 1)
        master_metrics.append({
            "label": "Global Avg Temp",
            "value": f"{avg_temp:.1f}°C",
            "icon": "🌡️",
            "color": "#3b82f6"
        })

    # Earthquakes
    if quakes_data.get("success"):
        master_metrics.append({
            "label": "Earthquakes (24h)",
            "value": str(quakes_data.get("total", 0)),
            "icon": "🌋",
            "color": "#ef4444"
        })

    # Fires
    if fires_data.get("success"):
        master_metrics.append({
            "label": "Active Fires",
            "value": str(fires_data.get("total", 0)),
            "icon": "🔥",
            "color": "#f59e0b"
        })

    # Aircraft
    if aircraft_data.get("success"):
        master_metrics.append({
            "label": "Aircraft Tracked",
            "value": str(aircraft_data.get("total", 0)),
            "icon": "✈️",
            "color": "#06b6d4"
        })

    # Crypto
    if crypto_data.get("success") and "bitcoin" in crypto_data.get("data", {}):
        btc_price = crypto_data["data"]["bitcoin"]["usd"]
        master_metrics.append({
            "label": "Bitcoin",
            "value": f"${btc_price:,.0f}",
            "icon": "₿",
            "color": "#f59e0b"
        })

    # Oil
    if oil_data.get("success"):
        master_metrics.append({
            "label": "Brent Crude",
            "value": f"${oil_data.get('brent', 0):.0f}",
            "icon": "🛢️",
            "color": "#78350f"
        })

    # Space Weather
    if space_data.get("success"):
        master_metrics.append({
            "label": "Solar Wind",
            "value": f"{space_data.get('solar_wind_speed', 0):.0f} km/s",
            "icon": "☀️",
            "color": "#fbbf24"
        })

    # ISS
    if iss_data.get("success"):
        master_metrics.append({
            "label": "ISS Altitude",
            "value": "~408 km",
            "icon": "🛰️",
            "color": "#10b981"
        })

    # Aurora
    if aurora_data.get("success"):
        master_metrics.append({
            "label": "Aurora Zones",
            "value": str(len(aurora_data.get("forecast_points", []))),
            "icon": "🌌",
            "color": "#a855f7"
        })

    # Pollution
    if pollution_data.get("success"):
        cities = pollution_data.get("cities", [])
        worst_city = max(cities, key=lambda x: x.get("pm25", 0)) if cities else None
        if worst_city:
            master_metrics.append({
                "label": f"Worst AQI: {worst_city.get('city', 'Unknown')}",
                "value": f"{worst_city.get('pm25', 0):.0f}",
                "icon": "💨",
                "color": "#ef4444"
            })

    # Stocks
    if stocks_data.get("success"):
        indices = stocks_data.get("indices", [])
        if indices:
            sp500 = next((idx for idx in indices if "S&P" in idx.get("name", "")), indices[0])
            master_metrics.append({
                "label": sp500.get("name", "S&P 500"),
                "value": f"{sp500.get('value', 0):,.0f}",
                "icon": "📈",
                "color": "#3b82f6"
            })

    # Webcams
    if webcams_data.get("success"):
        master_metrics.append({
            "label": "Live Webcams",
            "value": str(len(webcams_data.get("webcams", []))),
            "icon": "📹",
            "color": "#06b6d4"
        })

    # Ocean
    if ocean_data.get("success"):
        buoys = ocean_data.get("buoys", [])
        if buoys:
            avg_wave = sum(b.get("wave_height_m", 0) for b in buoys) / len(buoys)
            master_metrics.append({
                "label": "Avg Wave Height",
                "value": f"{avg_wave:.1f}m",
                "icon": "🌊",
                "color": "#0ea5e9"
            })

    # Volcanoes
    if volcanoes_data.get("success"):
        volcanoes = volcanoes_data.get("volcanoes", [])
        watch = sum(1 for v in volcanoes if v.get("alert") in ["Watch", "Advisory"])
        master_metrics.append({
            "label": "Volcanoes on Alert",
            "value": f"{watch}/{len(volcanoes)}",
            "icon": "🌋",
            "color": "#f59e0b" if watch > 0 else "#10b981"
        })

    # Satellites
    if satellites_data.get("success"):
        master_metrics.append({
            "label": "Satellites Tracked",
            "value": str(len(satellites_data.get("satellites", []))),
            "icon": "🛰️",
            "color": "#8b5cf6"
        })

    # Natural Disasters (GDACS)
    if disasters_data.get("success"):
        total_dis = disasters_data.get("total", 0)
        red_alerts = sum(1 for d in disasters_data.get("disasters", []) if d.get("alert_level") == "Red")
        master_metrics.append({
            "label": "Active Disasters",
            "value": f"{total_dis}" + (f" ({red_alerts} Red)" if red_alerts else ""),
            "icon": "⚠️",
            "color": "#ef4444" if red_alerts else "#f59e0b"
        })

    # Marine Traffic
    if marine_data.get("success"):
        ship_count = len(marine_data.get("ships", []))
        if ship_count:
            master_metrics.append({
                "label": "Vessels Tracked",
                "value": str(ship_count),
                "icon": "🚢",
                "color": "#0ea5e9"
            })

    # Radiation
    if radiation_data.get("success"):
        stations = radiation_data.get("stations", [])
        avg_cpm = sum(s.get("cpm", 0) for s in stations) / max(len(stations), 1)
        master_metrics.append({
            "label": "Avg Radiation",
            "value": f"{avg_cpm:.0f} CPM",
            "icon": "☢️",
            "color": "#10b981" if avg_cpm < 50 else "#f59e0b"
        })

    # Winds
    if winds_data.get("success"):
        wind_points = winds_data.get("wind_data", [])
        if wind_points:
            avg_speed = sum(w.get("speed_kmh", 0) for w in wind_points) / len(wind_points)
            master_metrics.append({
                "label": "Avg Wind Speed",
                "value": f"{avg_speed:.0f} km/h",
                "icon": "💨",
                "color": "#06b6d4"
            })

    # Solar Activity
    if solar_data.get("success") and solar_data.get("flux"):
        flux_val = solar_data.get("flux", 0)
        master_metrics.append({
            "label": "X-Ray Flux",
            "value": f"{flux_val:.1e}",
            "icon": "☀️",
            "color": "#fbbf24"
        })

    # Meteors
    if meteors_data.get("success"):
        showers = meteors_data.get("showers", [])
        next_shower = showers[0] if showers else None
        if next_shower:
            master_metrics.append({
                "label": f"Next: {next_shower.get('name', 'Meteor Shower')}",
                "value": next_shower.get("peak_date", "TBD"),
                "icon": "☄️",
                "color": "#a855f7"
            })

    # Tides
    if tides_data.get("success"):
        predictions = tides_data.get("predictions", [])
        if predictions:
            next_tide = predictions[0]
            master_metrics.append({
                "label": f"Next Tide ({next_tide.get('type', 'N/A')})",
                "value": f"{next_tide.get('v', '?')} ft",
                "icon": "🌊",
                "color": "#06b6d4"
            })

    # Exchange Rates
    if exchange_data.get("success"):
        rates = exchange_data.get("rates", {})
        eur_rate = rates.get("EUR", 0)
        if eur_rate:
            master_metrics.append({
                "label": "USD → EUR",
                "value": f"{eur_rate:.2f}",
                "icon": "💱",
                "color": "#10b981"
            })

    # Display master metrics grid (5 columns for compact view)
    if master_metrics:
        stats_grid(master_metrics, columns=5)

    st.markdown("---")

    # === REAL-TIME ALERTS & STATUS INDICATORS ===
    st.markdown("### 🚨 Live Alerts & Global Status")

    alerts = []

    # Get Phase 5 data for alerts (uses separate variable names to avoid shadowing)
    _p5_hurricanes = st.session_state.get("phase5_data", {}).get("hurricanes", {}) if "phase5_data" in st.session_state else {}
    _p5_asteroids = st.session_state.get("phase5_data", {}).get("asteroids", {}) if "phase5_data" in st.session_state else {}

    # Check for critical earthquakes
    if quakes_data.get("success") and quakes_data.get("features"):
        major_quakes = [q for q in quakes_data["features"] if q.get("properties", {}).get("mag", 0) >= 6.0]
        if major_quakes:
            for quake in major_quakes[:3]:  # Top 3
                props = quake.get("properties", {})
                alerts.append({
                    "level": "critical" if props.get("mag", 0) >= 7.0 else "warning",
                    "icon": "🔴" if props.get("mag", 0) >= 7.0 else "🟡",
                    "message": f"M{props.get('mag', 0):.1f} Earthquake - {props.get('place', 'Unknown location')}",
                    "category": "Seismic"
                })

    # Check for active hurricanes (from Phase 5 data if loaded)
    if _p5_hurricanes.get("success") and _p5_hurricanes.get("active_storms"):
        for storm in _p5_hurricanes["active_storms"]:
            intensity = storm.get("intensity", "").lower()
            if "major" in intensity or "hurricane" in intensity:
                alerts.append({
                    "level": "critical",
                    "icon": "🌀",
                    "message": f"{storm.get('name', 'Storm')} - {storm.get('classification', 'N/A')} ({storm.get('intensity', 'Unknown')})",
                    "category": "Weather"
                })

    # Check for high pollution
    if pollution_data.get("success") and pollution_data.get("cities"):
        unhealthy_cities = [c for c in pollution_data["cities"] if c.get("pm25", 0) > 150]
        if unhealthy_cities:
            worst = max(unhealthy_cities, key=lambda x: x.get("pm25", 0))
            alerts.append({
                "level": "warning",
                "icon": "💨",
                "message": f"Unhealthy Air Quality in {worst.get('city', 'Unknown')} - PM2.5: {worst.get('pm25', 0):.0f}",
                "category": "Air Quality"
            })

    # Check for Red alert disasters (GDACS)
    if disasters_data.get("success"):
        red_disasters = [d for d in disasters_data.get("disasters", []) if d.get("alert_level") == "Red"]
        for dis in red_disasters[:3]:
            alerts.append({
                "level": "critical",
                "icon": "🔴",
                "message": f"{dis.get('type', 'Disaster')}: {dis.get('name', 'Unknown')} - {dis.get('country', '')}",
                "category": "GDACS"
            })
        orange_disasters = [d for d in disasters_data.get("disasters", []) if d.get("alert_level") == "Orange"]
        for dis in orange_disasters[:2]:
            alerts.append({
                "level": "warning",
                "icon": "🟠",
                "message": f"{dis.get('type', 'Disaster')}: {dis.get('name', 'Unknown')} - {dis.get('country', '')}",
                "category": "GDACS"
            })

    # Check for potentially hazardous asteroids (from Phase 5 data if loaded)
    if _p5_asteroids and _p5_asteroids.get("success"):
        hazardous = [a for a in _p5_asteroids.get("asteroids", []) if a.get("potentially_hazardous")]
        if hazardous:
            closest = min(hazardous, key=lambda x: x.get("miss_distance_km", float('inf')))
            if closest.get("miss_distance_km", float('inf')) < 10000000:  # < 10M km
                alerts.append({
                    "level": "info",
                    "icon": "☄️",
                    "message": f"{closest.get('name', 'Asteroid')} approaching - {closest.get('miss_distance_km', 0):,.0f} km miss distance",
                    "category": "Space"
                })

    # Display alerts
    if alerts:
        for alert in alerts:
            if alert["level"] == "critical":
                st.error(f"{alert['icon']} **{alert['category']}:** {alert['message']}")
            elif alert["level"] == "warning":
                st.warning(f"{alert['icon']} **{alert['category']}:** {alert['message']}")
            else:
                st.info(f"{alert['icon']} **{alert['category']}:** {alert['message']}")
    else:
        st.success("✅ No critical alerts - All monitored systems within normal parameters")

    st.markdown("---")

    # ============================================================================
    # TAB-BASED ORGANIZATION WITH LAZY LOADING
    # ============================================================================
    st.markdown("### 📂 Detailed Data by Category")
    st.markdown("*Select a category to load detailed data - optimized for memory efficiency*")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🌍 Earth Monitoring",
        "🚀 Space & Aviation",
        "💰 Financial Markets",
        "🌊 Marine & Ocean",
        "🏗️ Infrastructure",
        "🆕 Phase 5 Extensions"
    ])

    # === TAB 1: EARTH MONITORING ===
    with tab1:
        st.markdown("#### 🌍 Earth Monitoring - Real-Time Environmental Data")

        # Weather Section
        category_header("🌡️ World Cities Weather", count=len(weather_data), icon="☁️")

        if weather_data:
            df = pd.DataFrame(weather_data)
            df = df[["city", "country", "region", "temperature", "wind_speed"]]
            df.columns = ["City", "Country", "Region", "Temp (°C)", "Wind (km/h)"]
            df = df.sort_values("Temp (°C)", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False)
            st.download_button("📥 Download Weather Data (CSV)", csv, "world_weather.csv", "text/csv", key="dl_weather_tab")

        st.markdown("---")

        # Earthquakes Section
        category_header("🌋 Recent Earthquakes (M4.5+)", count=quakes_data.get("total", 0), icon="⚡")

        if quakes_data.get("success"):
            quake_list = []
            for quake in quakes_data["features"][:20]:
                props = quake.get("properties", {})
                coords = quake.get("geometry", {}).get("coordinates", [])
                quake_list.append({
                    "Magnitude": props.get("mag"),
                    "Location": props.get("place"),
                    "Depth (km)": coords[2] if len(coords) > 2 else None,
                    "Time": datetime.fromtimestamp(props.get("time", 0)/1000).strftime("%Y-%m-%d %H:%M")
                })

            if quake_list:
                df_quakes = pd.DataFrame(quake_list)
                st.dataframe(df_quakes, use_container_width=True, hide_index=True)
                csv_quakes = df_quakes.to_csv(index=False)
                st.download_button("📥 Download Earthquakes (CSV)", csv_quakes, "earthquakes.csv", "text/csv", key="dl_quakes_tab")

        st.markdown("---")

        # Fires Section
        if fires_data.get("success"):
            fires_list = fires_data.get("fires", [])
            category_header("🔥 Active Wildfires (24h)", count=len(fires_list), icon="🔥")
            st.info(f"**{len(fires_list)}** active fire detections from NASA FIRMS")
            if fires_list:
                fire_rows = [{
                    "Lat": round(f.get("lat", 0), 3),
                    "Lon": round(f.get("lon", 0), 3),
                    "Brightness": f.get("brightness", f.get("bright_ti4", "N/A")),
                    "Confidence": f.get("confidence", "N/A"),
                    "Satellite": f.get("satellite", "VIIRS"),
                } for f in fires_list[:50]]
                fire_df = pd.DataFrame(fire_rows)
                st.dataframe(fire_df, use_container_width=True, hide_index=True)
                csv_fires = fire_df.to_csv(index=False)
                st.download_button("📥 Download Fires (CSV)", csv_fires, "active_fires.csv", "text/csv", key="dl_fires_tab")

        # Natural Disasters Section (GDACS)
        if disasters_data.get("success") and disasters_data.get("disasters"):
            st.markdown("---")
            dis_list = disasters_data.get("disasters", [])
            category_header("⚠️ Active Natural Disasters (GDACS)", count=len(dis_list), icon="🌍")
            alert_colors = {"Red": "🔴", "Orange": "🟠", "Green": "🟢"}
            dis_rows = []
            for d in dis_list[:30]:
                dis_rows.append({
                    "Alert": alert_colors.get(d.get("alert_level", ""), "⚪") + " " + d.get("alert_level", ""),
                    "Type": d.get("type", "Unknown"),
                    "Event": d.get("name", "Unknown"),
                    "Country": d.get("country", ""),
                    "Severity": d.get("severity_text", "") or str(d.get("severity", "")),
                    "Lat": round(d.get("latitude", 0), 2),
                    "Lon": round(d.get("longitude", 0), 2),
                })
            if dis_rows:
                dis_df = pd.DataFrame(dis_rows)
                # Sort: Red first, then Orange, then Green
                alert_order = {"🔴 Red": 0, "🟠 Orange": 1, "🟢 Green": 2}
                dis_df["_sort"] = dis_df["Alert"].map(alert_order).fillna(3)
                dis_df = dis_df.sort_values("_sort").drop(columns=["_sort"])
                st.dataframe(dis_df, use_container_width=True, hide_index=True)
                csv_dis = dis_df.to_csv(index=False)
                st.download_button("📥 Download Disasters (CSV)", csv_dis, "gdacs_disasters.csv", "text/csv", key="dl_disasters_tab")

        # Volcanoes Section
        if volcanoes_data.get("success"):
            st.markdown("---")
            volcs = volcanoes_data.get("volcanoes", [])
            category_header("🌋 Active Volcanoes", count=len(volcs), icon="🔥")
            if volcs:
                volc_rows = [{
                    "Name": v.get("name", "Unknown"),
                    "Country": v.get("country", ""),
                    "Alert Level": v.get("alert", "Normal"),
                    "Last Eruption": v.get("last_eruption", "Unknown"),
                    "Lat": v.get("lat", 0),
                    "Lon": v.get("lon", 0)
                } for v in volcs]
                volc_df = pd.DataFrame(volc_rows)
                st.dataframe(volc_df, use_container_width=True, hide_index=True)

        # Aurora Section
        if aurora_data.get("success"):
            st.markdown("---")
            forecast_pts = aurora_data.get("forecast_points", [])
            category_header("🌌 Aurora Forecast", count=len(forecast_pts), icon="✨")
            zones = len(forecast_pts)
            max_intensity = max((p.get("intensity", 0) for p in forecast_pts), default=0)
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.metric("Active Aurora Zones", zones)
            with col_a2:
                st.metric("Max Intensity", f"{max_intensity:.0f}/100")

        # Pollution Section
        if pollution_data.get("success"):
            st.markdown("---")
            category_header("💨 Air Quality Index", count=len(pollution_data.get("cities", [])), icon="🌫️")
            cities = pollution_data.get("cities", [])
            if cities:
                pollution_df = pd.DataFrame(cities)
                # Compute AQI and category from PM2.5 if not present
                if "aqi" not in pollution_df.columns:
                    pollution_df["aqi"] = pollution_df.get("pm25", pd.Series([0])).apply(
                        lambda x: int(x * 4.2) if x else 0
                    )
                if "category" not in pollution_df.columns:
                    pollution_df["category"] = pollution_df["aqi"].apply(
                        lambda x: "Good" if x < 50 else "Moderate" if x < 100 else "Unhealthy for Sensitive" if x < 150 else "Unhealthy" if x < 200 else "Very Unhealthy"
                    )
                display_cols = [c for c in ["city", "country", "aqi", "pm25", "category"] if c in pollution_df.columns]
                pollution_df = pollution_df[display_cols]
                pollution_df.columns = [c.replace("city", "City").replace("country", "Country").replace("aqi", "AQI").replace("pm25", "PM2.5").replace("category", "Category") for c in display_cols]
                st.dataframe(pollution_df, use_container_width=True, hide_index=True)

    # === TAB 2: SPACE & AVIATION ===
    with tab2:
        st.markdown("#### 🚀 Space & Aviation - Real-Time Tracking")

        # ISS Location
        if iss_data.get("success"):
            category_header("🛰️ International Space Station", count=1, icon="🌍")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Latitude", f"{iss_data.get('latitude', 0):.2f}°")
            with col2:
                st.metric("Longitude", f"{iss_data.get('longitude', 0):.2f}°")
            with col3:
                st.metric("Altitude", "~408 km")

        st.markdown("---")

        # Aircraft Traffic
        if aircraft_data.get("success"):
            ac_list = aircraft_data.get("aircraft", [])
            category_header("✈️ Aircraft Traffic (OpenSky)", count=aircraft_data.get("total", 0), icon="🛫")
            st.info(f"**{aircraft_data.get('total', 0)}** aircraft currently tracked via ADS-B")
            if ac_list:
                ac_rows = [{
                    "Callsign": a.get("callsign", "").strip() or "N/A",
                    "Country": a.get("country", "Unknown"),
                    "Altitude (m)": round(a.get("altitude", a.get("baro_altitude", 0)) or 0),
                    "Velocity (m/s)": round(a.get("velocity", 0) or 0),
                    "Lat": round(a.get("lat", a.get("latitude", 0)) or 0, 3),
                    "Lon": round(a.get("lon", a.get("longitude", 0)) or 0, 3),
                } for a in ac_list[:50]]
                ac_df = pd.DataFrame(ac_rows)
                st.dataframe(ac_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Space Weather
        if space_data.get("success"):
            category_header("🌞 Space Weather (NOAA SWPC)", count=5, icon="☀️")
            sw_cols = st.columns(5)
            sw_cols[0].metric("Solar Wind", f"{space_data.get('solar_wind_speed', 0):.0f} km/s")
            density = space_data.get("density", 0)
            sw_cols[1].metric("Proton Density", f"{density:.1f} p/cm³" if density else "N/A")
            bz = space_data.get("bz_gsm", 0)
            sw_cols[2].metric("Bz (GSM)", f"{bz:.1f} nT" if bz else "N/A",
                              delta="Southward" if bz and bz < 0 else "Northward" if bz else None)
            bt = space_data.get("bt", 0)
            sw_cols[3].metric("Bt (Total)", f"{bt:.1f} nT" if bt else "N/A")
            kp_val = _fetch_kp_index()
            sw_cols[4].metric("K-Index", kp_val)

        # Satellites
        if satellites_data.get("success"):
            st.markdown("---")
            category_header("🛰️ Satellite Tracking", count=len(satellites_data.get("satellites", [])), icon="📡")
            sats = satellites_data.get("satellites", [])
            if sats:
                sat_df = pd.DataFrame(sats)
                st.dataframe(sat_df, use_container_width=True, hide_index=True)

        # Solar Activity (X-ray flux from NOAA GOES)
        if solar_data.get("success"):
            st.markdown("---")
            category_header("☀️ Solar Activity (NOAA GOES)", count=1, icon="🔆")
            sol_cols = st.columns(2)
            flux = solar_data.get("flux", 0)
            sol_cols[0].metric("X-Ray Flux", f"{flux:.2e} W/m²" if flux else "N/A")
            sol_cols[1].metric("Timestamp", solar_data.get("timestamp", "N/A")[:19])

    # === TAB 3: FINANCIAL MARKETS ===
    with tab3:
        st.markdown("#### 💰 Financial Markets - Real-Time Prices")

        # Crypto & Commodity Prices
        category_header("💰 Commodity & Crypto Prices", count=2, icon="📈")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🛢️ Oil Prices")
            if oil_data.get("success"):
                stats_grid([
                    {"label": "Brent Crude", "value": f"${oil_data['brent']:.2f}", "icon": "🛢️", "color": "#f59e0b"},
                    {"label": "WTI Crude", "value": f"${oil_data['wti']:.2f}", "icon": "⛽", "color": "#ef4444"}
                ], columns=2)
                if oil_data.get("is_fallback"):
                    st.caption("*Estimated values - live feed temporarily unavailable*")

        with col2:
            st.markdown("### 💎 Cryptocurrency")
            if crypto_data.get("success"):
                data = crypto_data["data"]
                crypto_stats = []
                if "bitcoin" in data:
                    crypto_stats.append({"label": "Bitcoin", "value": f"${data['bitcoin']['usd']:,.0f}", "icon": "₿", "color": "#f59e0b"})
                if "ethereum" in data:
                    crypto_stats.append({"label": "Ethereum", "value": f"${data['ethereum']['usd']:,.0f}", "icon": "Ξ", "color": "#3b82f6"})
                if crypto_stats:
                    stats_grid(crypto_stats, columns=2)

        # === CRYPTO PRICE TREND VISUALIZATION ===
        if crypto_data.get("success") and "bitcoin" in crypto_data.get("data", {}):
            st.markdown("---")
            st.markdown("### 📊 Price Trend Visualization (Simulated 24h)")

            # Simulate 24h price movement (in production, fetch historical data)

            btc_current = crypto_data["data"]["bitcoin"]["usd"]

            # Generate realistic price fluctuations
            hours = 24
            time_points = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]
            btc_prices = []

            # Start from ~3% below current and trend up
            price = btc_current * 0.97
            for i in range(hours):
                # Random walk with slight upward bias
                change = random.uniform(-0.015, 0.02)  # -1.5% to +2%
                price = price * (1 + change)
                btc_prices.append(price)

            # Ensure last price matches current
            btc_prices[-1] = btc_current

            # Create DataFrame for chart
            chart_data = pd.DataFrame({
                "Time": time_points,
                "Bitcoin ($)": btc_prices
            })

            # Display line chart
            st.line_chart(chart_data.set_index("Time"), use_container_width=True)

            # Show stats (simulated trend based on current real price)
            st.caption("*Simulated trend based on current real-time price*")
            col1, col2, col3 = st.columns(3)
            with col1:
                high_24h = max(btc_prices)
                st.metric("~24h High (est.)", f"${high_24h:,.0f}")
            with col2:
                low_24h = min(btc_prices)
                st.metric("~24h Low (est.)", f"${low_24h:,.0f}")
            with col3:
                change_24h = ((btc_current - btc_prices[0]) / btc_prices[0]) * 100
                st.metric("~24h Change (est.)", f"{change_24h:+.2f}%",
                         delta_color="normal" if change_24h > 0 else "inverse")

        st.markdown("---")

        # Stock Indices
        if stocks_data.get("success"):
            category_header("📈 Stock Market Indices", count=len(stocks_data.get("indices", [])), icon="📊")
            indices = stocks_data.get("indices", [])
            if indices:
                stock_stats = []
                for idx in indices:
                    color = "#10b981" if idx.get("change_percent", 0) > 0 else "#ef4444"
                    stock_stats.append({
                        "label": idx.get("name", ""),
                        "value": f"{idx.get('value', 0):,.2f}",
                        "icon": "📈" if idx.get("change_percent", 0) > 0 else "📉",
                        "color": color
                    })
                stats_grid(stock_stats, columns=3)
                if stocks_data.get("is_fallback"):
                    st.caption("*Estimated values - live feed temporarily unavailable*")

        st.markdown("---")

        # Exchange Rates
        if exchange_data.get("success"):
            category_header("💱 Currency Exchange Rates", count=1, icon="💵")
            rates = exchange_data.get("rates", {})
            major_currencies = ["EUR", "GBP", "JPY", "CNY", "INR", "AUD"]
            rate_stats = []
            for currency in major_currencies:
                if currency in rates:
                    rate_stats.append({
                        "label": f"USD → {currency}",
                        "value": f"{rates[currency]:.2f}",
                        "icon": "💱",
                        "color": "#10b981"
                    })
            if rate_stats:
                stats_grid(rate_stats, columns=3)

    # === TAB 4: MARINE & OCEAN ===
    with tab4:
        st.markdown("#### 🌊 Marine & Ocean - Maritime Data")

        # Marine Traffic
        if marine_data.get("success"):
            ships = marine_data.get("ships", [])
            category_header("🚢 Marine Traffic", count=len(ships), icon="⛴️")
            st.info(f"**{len(ships)}** vessels tracked in real-time via AIS")
            if ships:
                nav_labels = {0: "Underway", 1: "At Anchor", 2: "Not Commanded", 3: "Restricted", 5: "Moored"}
                ship_rows = []
                for s in ships[:200]:
                    ship_rows.append({
                        "MMSI": s.get("mmsi", ""),
                        "Region": s.get("region", ""),
                        "Speed (kn)": round(s.get("speed", 0), 1),
                        "Heading": s.get("heading", 0),
                        "Status": nav_labels.get(s.get("nav_status", -1), "Unknown"),
                        "Lat": round(s.get("latitude", 0), 4),
                        "Lon": round(s.get("longitude", 0), 4),
                    })
                ship_df = pd.DataFrame(ship_rows)
                moving = ship_df[ship_df["Speed (kn)"] > 0.5]
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Vessels", len(ship_rows))
                c2.metric("Moving", len(moving))
                c3.metric("Avg Speed", f"{moving['Speed (kn)'].mean():.1f} kn" if len(moving) > 0 else "0 kn")
                st.dataframe(ship_df.head(50), use_container_width=True, hide_index=True)

        st.markdown("---")

        # Ocean Conditions
        if ocean_data.get("success"):
            category_header("🌊 Ocean Buoy Data", count=len(ocean_data.get("buoys", [])), icon="🌡️")
            buoys = ocean_data.get("buoys", [])
            if buoys:
                ocean_df = pd.DataFrame(buoys)
                st.dataframe(ocean_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Tides
        if tides_data.get("success"):
            predictions = tides_data.get("predictions", [])
            category_header("🌊 Tide Predictions", count=len(predictions), icon="📊")
            station_name = tides_data.get("station", "Coastal Station")
            st.markdown(f"**Station:** {station_name}")
            if predictions:
                cols_t = st.columns(min(len(predictions), 4))
                for idx, pred in enumerate(predictions):
                    with cols_t[idx % 4]:
                        tide_type = pred.get("type", "")
                        icon_t = "High" if tide_type == "H" else "Low"
                        st.metric(f"Tide {idx+1} ({icon_t})", f"{pred.get('v', 0):.2f} m", delta=pred.get("t", ""))
            else:
                st.info("Tide predictions temporarily unavailable")

    # === TAB 5: INFRASTRUCTURE ===
    with tab5:
        st.markdown("#### 🏗️ Infrastructure - Monitoring Systems")

        # Webcams
        if webcams_data.get("success"):
            category_header("📹 Live Webcams", count=len(webcams_data.get("webcams", [])), icon="🎥")
            webcams = webcams_data.get("webcams", [])
            if webcams:
                for cam in webcams[:5]:
                    with st.expander(f"📹 {cam.get('name', 'Webcam')} - {cam.get('country', '')}"):
                        st.markdown(f"**Location:** {cam.get('lat', 0):.4f}, {cam.get('lon', 0):.4f}")
                        if cam.get('url'):
                            st.markdown(f"[🔴 View Live Stream]({cam.get('url')})")

        st.markdown("---")

        # Radiation Monitoring
        if radiation_data.get("success"):
            category_header("☢️ Radiation Levels", count=len(radiation_data.get("stations", [])), icon="📊")
            stations = radiation_data.get("stations", [])
            if stations:
                rad_df = pd.DataFrame(stations)
                st.dataframe(rad_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Winds
        if winds_data.get("success"):
            wind_pts = winds_data.get("wind_data", [])
            category_header("💨 Global Wind Patterns", count=len(wind_pts), icon="🌪️")
            if wind_pts:
                wind_rows = [{
                    "Lat": w.get("lat", 0),
                    "Lon": w.get("lon", 0),
                    "Speed (km/h)": round(w.get("speed_kmh", w.get("speed_kph", 0)), 1),
                    "Direction (°)": w.get("direction", 0)
                } for w in wind_pts]
                wind_df = pd.DataFrame(wind_rows)
                avg_speed = wind_df["Speed (km/h)"].mean()
                max_speed = wind_df["Speed (km/h)"].max()
                c1, c2, c3 = st.columns(3)
                c1.metric("Grid Points", len(wind_rows))
                c2.metric("Avg Wind Speed", f"{avg_speed:.1f} km/h")
                c3.metric("Max Wind Speed", f"{max_speed:.1f} km/h")
                st.dataframe(wind_df, use_container_width=True, hide_index=True)
            else:
                st.info("Wind data temporarily unavailable")

        # Meteors
        if meteors_data.get("success"):
            st.markdown("---")
            category_header("☄️ Meteor Showers", count=len(meteors_data.get("showers", [])), icon="🌠")
            showers = meteors_data.get("showers", [])
            if showers:
                for shower in showers[:3]:
                    st.markdown(f"**{shower.get('name')}** - Peak: {shower.get('peak_date')}")

    # === TAB 6: PHASE 5 EXTENSIONS ===
    with tab6:
        st.markdown("#### 🆕 Phase 5 Extensions - 10 New Data Sources")
        st.info("Loading Phase 5 data sources on-demand...")

        # Lazy load Phase 5 data only when this tab is opened
        if 'phase5_loaded' not in st.session_state:
            st.session_state.phase5_loaded = False

        if st.button("🔄 Load Phase 5 Data Sources", key="load_phase5"):
            with st.spinner("Loading 10 new data sources..."):
                try:
                    st.session_state.phase5_data = {
                        'rivers': fetch_river_levels(),
                        'snow': fetch_snow_cover(),
                        'sea_ice': fetch_sea_ice_extent(),
                        'tsunami': fetch_tsunami_warnings(),
                        'hurricanes': fetch_hurricane_tracking(),
                        'solar_wind': fetch_solar_wind_realtime(),
                        'asteroids': fetch_asteroid_approaches(),
                        'soil': fetch_soil_moisture(),
                        'smoke': fetch_wildfire_smoke(),
                        'temp_anomaly': fetch_global_temperature_anomaly()
                    }
                    st.session_state.phase5_loaded = True
                    st.success("✅ Phase 5 data loaded successfully!")
                except Exception as e:
                    st.error(f"Error loading Phase 5 data: {e}")

        if st.session_state.phase5_loaded:
            phase5 = st.session_state.phase5_data

            # River Levels
            if phase5['rivers'].get('success'):
                category_header("🏞️ River Levels (USGS)", count=phase5['rivers'].get('count', 0), icon="💧")
                rivers = phase5['rivers'].get('rivers', [])
                if rivers:
                    river_df = pd.DataFrame(rivers)
                    st.dataframe(river_df[['name', 'value', 'unit', 'parameter']], use_container_width=True, hide_index=True)

            st.markdown("---")

            # Snow Cover
            if phase5['snow'].get('success'):
                category_header("❄️ Snow Cover (NOAA)", count=phase5['snow'].get('count', 0), icon="🏔️")
                regions = phase5['snow'].get('regions', [])
                if regions:
                    for region in regions:
                        st.markdown(f"**{region['region']}**: {region['coverage_percent']}% coverage - {region['trend']}")

            st.markdown("---")

            # Sea Ice Extent
            if phase5['sea_ice'].get('success'):
                category_header("🧊 Sea Ice Extent (NSIDC)", count=2, icon="❄️")
                col1, col2 = st.columns(2)
                with col1:
                    arctic = phase5['sea_ice'].get('arctic', {})
                    st.metric("Arctic Ice", f"{arctic.get('extent_million_km2', 0):.2f}M km²",
                             f"{arctic.get('anomaly_percent', 0):.1f}%")
                with col2:
                    antarctic = phase5['sea_ice'].get('antarctic', {})
                    st.metric("Antarctic Ice", f"{antarctic.get('extent_million_km2', 0):.2f}M km²",
                             f"{antarctic.get('anomaly_percent', 0):.1f}%")

            st.markdown("---")

            # Hurricane Tracking
            if phase5['hurricanes'].get('success'):
                category_header("🌀 Active Hurricanes/Typhoons", count=phase5['hurricanes'].get('count', 0), icon="🌪️")
                storms = phase5['hurricanes'].get('active_storms', [])
                if storms:
                    for storm in storms:
                        st.warning(f"**{storm.get('name')}** - {storm.get('classification')} - {storm.get('intensity')}")
                else:
                    st.success("No active tropical systems")

            st.markdown("---")

            # Solar Wind Real-time
            if phase5['solar_wind'].get('success'):
                category_header("☀️ Solar Wind (NOAA DSCOVR)", count=1, icon="🌌")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Density", f"{phase5['solar_wind'].get('density', 0):.1f} p/cm³")
                with col2:
                    st.metric("Speed", f"{phase5['solar_wind'].get('speed', 0):.0f} km/s")
                with col3:
                    st.metric("Temperature", f"{phase5['solar_wind'].get('temperature', 0):,.0f} K")

            st.markdown("---")

            # Asteroids
            if phase5['asteroids'].get('success'):
                category_header("☄️ Near-Earth Asteroids", count=phase5['asteroids'].get('count', 0), icon="🪨")
                asteroids = phase5['asteroids'].get('asteroids', [])
                if asteroids:
                    for ast in asteroids[:5]:
                        hazard = "⚠️ HAZARDOUS" if ast.get('potentially_hazardous') else "✅ Safe"
                        st.markdown(f"**{ast.get('name')}** - {ast.get('diameter_m', 0):.0f}m - {hazard}")

            st.markdown("---")

            # Tsunami Warnings
            if phase5['tsunami'].get('success'):
                category_header("🌊 Tsunami Warnings", count=phase5['tsunami'].get('count', 0), icon="⚠️")
                warnings = phase5['tsunami'].get('warnings', [])
                if warnings:
                    for w in warnings:
                        st.warning(f"**{w.get('region', 'Unknown')}** - Level: {w.get('level', 'N/A')} - {w.get('message', '')}")
                else:
                    st.success("No active tsunami warnings")

            st.markdown("---")

            # Soil Moisture
            if phase5['soil'].get('success'):
                category_header("🌱 Soil Moisture (NASA SMAP)", count=phase5['soil'].get('count', 0), icon="🌍")
                soil_data = phase5['soil'].get('regions', phase5['soil'].get('data', []))
                if isinstance(soil_data, list) and soil_data:
                    soil_df = pd.DataFrame(soil_data)
                    st.dataframe(soil_df, use_container_width=True, hide_index=True)
                elif isinstance(soil_data, dict):
                    for k, v in soil_data.items():
                        st.metric(k, f"{v}")

            st.markdown("---")

            # Wildfire Smoke
            if phase5['smoke'].get('success'):
                category_header("💨 Wildfire Smoke Plumes", count=phase5['smoke'].get('count', 0), icon="🔥")
                smoke_events = phase5['smoke'].get('plumes', phase5['smoke'].get('data', []))
                if isinstance(smoke_events, list) and smoke_events:
                    for s in smoke_events[:5]:
                        st.markdown(f"**{s.get('region', s.get('name', 'Unknown'))}** - Density: {s.get('density', 'N/A')}")
                else:
                    st.info("No major smoke plumes detected")

            st.markdown("---")

            # Global Temperature Anomaly
            if phase5['temp_anomaly'].get('success'):
                category_header("🌡️ Global Temperature Anomaly", count=1, icon="📊")
                anom = phase5['temp_anomaly']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Global", f"+{anom.get('global_anomaly_celsius', 0):.2f}°C")
                with col2:
                    st.metric("Land", f"+{anom.get('land_anomaly_celsius', 0):.2f}°C")
                with col3:
                    st.metric("Ocean", f"+{anom.get('ocean_anomaly_celsius', 0):.2f}°C")

    # ============================================================================
    # END OF TAB-BASED SECTIONS
    # ============================================================================
    st.markdown("---")

    # Legacy duplicate sections removed - all data now in tabs above
    # Keeping unique content: Global Map, Weather Table, Earthquake Table

    # === WORLD MAP ===
    category_header("🌍 Global Real-Time Map", count=1, icon="🗺️")

    st.markdown("""
    **Interactive Map Legend (15+ Data Layers):**

    **Weather & Environment:**
    - 🔵 **Blue/Green circles** = City weather (color by temperature)
    - 💨 **Colored circles** = Air quality (green=good, orange=moderate, red=unhealthy)
    - 🟣 **Purple circles** = Aurora borealis (opacity = intensity)

    **Natural Hazards:**
    - 🟡🟠🔴 **Large circles** = Earthquakes M4.5+ (size = magnitude)
    - 🔴 **Small red dots** = Active wildfires (NASA FIRMS 24h)
    - 🌋 **Volcano markers** = Active volcanoes (color = alert level)
    - 🌀 **Red/Orange/Yellow circles** = Active hurricanes/typhoons (color = intensity)

    **Transportation & Space:**
    - ✈️ **Small blue dots** = Aircraft in flight (real-time)
    - 🛰️ **Green marker** = International Space Station (ISS)
    - 🛰️ **Purple circles** = Other satellites tracked
    - ☄️ **Red circles** = Potentially hazardous asteroids (near-Earth)

    **Marine & Disasters:**
    - 🚢 **Cyan dots** = Ship positions (AIS real-time)
    - ⚠️ **Red/Orange/Green circles** = GDACS disasters (size = alert level)
    - 🌡️ **Heat overlay** = Temperature distribution (blue→red gradient)

    **Monitoring & Infrastructure:**
    - 📹 **Light blue markers** = Live webcams worldwide
    - 🌊 **Cyan circles** = Ocean buoys (wave/temp data)
    - ☢️ **Green/Orange/Red circles** = Radiation monitoring stations
    - 🏞️ **Blue markers** = River gauges (USGS real-time)

    **Phase 5 Layers** (shown when Phase 5 data is loaded):
    - 🏞️ River levels | 🌀 Hurricane tracking | ☄️ Asteroid approaches

    *Click any marker for detailed information!*
    """)

    # Create and display map with ALL 12+ layers
    # Get Phase 5 data if available (lazy loaded in Tab 6)
    rivers_phase5 = st.session_state.get('phase5_data', {}).get('rivers') if 'phase5_data' in st.session_state else None
    hurricanes_phase5 = st.session_state.get('phase5_data', {}).get('hurricanes') if 'phase5_data' in st.session_state else None
    asteroids_phase5 = st.session_state.get('phase5_data', {}).get('asteroids') if 'phase5_data' in st.session_state else None

    world_map = create_global_map(
        weather_data, quakes_data, fires_data, aircraft_data, iss_data, aurora_data, pollution_data,
        webcams_data, ocean_data, volcanoes_data, satellites_data, radiation_data,
        rivers_phase5, hurricanes_phase5, asteroids_phase5,  # Phase 5 data (if loaded)
        marine_data=marine_data, disasters_data=disasters_data
    )
    st_folium(world_map, width=None, height=800, key="global_map")

    st.markdown("---")

    # Last updated
    st.markdown(f"""
    <div style="
        text-align: center;
        color: #94a3b8;
        font-size: 0.875rem;
        margin-top: 2rem;
        padding: 1rem;
        background: rgba(59, 130, 246, 0.05);
        border-radius: 8px;
    ">
        🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
        Data sources: Open-Meteo, USGS, NASA FIRMS, NOAA SWPC, GDACS, OpenSky, Digitraffic AIS, Yahoo Finance, ExchangeRate-API (all free, no auth)
    </div>
    """, unsafe_allow_html=True)
