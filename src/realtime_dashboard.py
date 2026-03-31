"""
Real-Time Global Dashboard module for TerraScout AI.
Combines multiple free real-time data sources (Open-Meteo weather, USGS earthquakes,
NASA EONET volcanoes, ISS tracking, air quality, marine data, UV/solar) into
composite map visualizations with dark glassmorphism styling.
"""

import io
import math
import html
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


# ═══════════════════════════════════════════════════════════════
# CONSTANTS & CITY DATA
# ═══════════════════════════════════════════════════════════════

WORLD_CITIES = [
    # North America
    {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "USA"},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "country": "USA"},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298, "country": "USA"},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698, "country": "USA"},
    {"name": "Toronto", "lat": 43.6532, "lon": -79.3832, "country": "Canada"},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332, "country": "Mexico"},
    {"name": "Vancouver", "lat": 49.2827, "lon": -123.1207, "country": "Canada"},
    {"name": "Miami", "lat": 25.7617, "lon": -80.1918, "country": "USA"},
    # South America
    {"name": "Sao Paulo", "lat": -23.5505, "lon": -46.6333, "country": "Brazil"},
    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816, "country": "Argentina"},
    {"name": "Lima", "lat": -12.0464, "lon": -77.0428, "country": "Peru"},
    {"name": "Bogota", "lat": 4.7110, "lon": -74.0721, "country": "Colombia"},
    {"name": "Santiago", "lat": -33.4489, "lon": -70.6693, "country": "Chile"},
    # Europe
    {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "UK"},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "country": "France"},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "country": "Germany"},
    {"name": "Rome", "lat": 41.9028, "lon": 12.4964, "country": "Italy"},
    {"name": "Madrid", "lat": 40.4168, "lon": -3.7038, "country": "Spain"},
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6173, "country": "Russia"},
    {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "country": "Turkey"},
    {"name": "Stockholm", "lat": 59.3293, "lon": 18.0686, "country": "Sweden"},
    {"name": "Athens", "lat": 37.9838, "lon": 23.7275, "country": "Greece"},
    {"name": "Lisbon", "lat": 38.7223, "lon": -9.1393, "country": "Portugal"},
    # Africa
    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "country": "Egypt"},
    {"name": "Lagos", "lat": 6.5244, "lon": 3.3792, "country": "Nigeria"},
    {"name": "Nairobi", "lat": -1.2921, "lon": 36.8219, "country": "Kenya"},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "country": "South Africa"},
    {"name": "Casablanca", "lat": 33.5731, "lon": -7.5898, "country": "Morocco"},
    {"name": "Addis Ababa", "lat": 9.0250, "lon": 38.7469, "country": "Ethiopia"},
    # Asia
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "Japan"},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "country": "China"},
    {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "country": "China"},
    {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "country": "India"},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "India"},
    {"name": "Seoul", "lat": 37.5665, "lon": 126.9780, "country": "South Korea"},
    {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "country": "Thailand"},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "country": "Singapore"},
    {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "country": "Indonesia"},
    {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "country": "UAE"},
    {"name": "Riyadh", "lat": 24.7136, "lon": 46.6753, "country": "Saudi Arabia"},
    {"name": "Tehran", "lat": 35.6892, "lon": 51.3890, "country": "Iran"},
    {"name": "Karachi", "lat": 24.8607, "lon": 67.0011, "country": "Pakistan"},
    {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694, "country": "China"},
    {"name": "Manila", "lat": 14.5995, "lon": 120.9842, "country": "Philippines"},
    # Oceania
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Australia"},
    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631, "country": "Australia"},
    {"name": "Auckland", "lat": -36.8485, "lon": 174.7633, "country": "New Zealand"},
    {"name": "Perth", "lat": -31.9505, "lon": 115.8605, "country": "Australia"},
]

# Ocean monitoring points (mid-ocean and coastal)
OCEAN_POINTS = [
    {"name": "North Atlantic", "lat": 40.0, "lon": -30.0},
    {"name": "South Atlantic", "lat": -25.0, "lon": -15.0},
    {"name": "North Pacific", "lat": 35.0, "lon": -170.0},
    {"name": "South Pacific", "lat": -30.0, "lon": -140.0},
    {"name": "Indian Ocean", "lat": -15.0, "lon": 75.0},
    {"name": "Arabian Sea", "lat": 15.0, "lon": 65.0},
    {"name": "Bay of Bengal", "lat": 12.0, "lon": 88.0},
    {"name": "Caribbean Sea", "lat": 15.0, "lon": -70.0},
    {"name": "Mediterranean", "lat": 36.0, "lon": 18.0},
    {"name": "Norwegian Sea", "lat": 65.0, "lon": 5.0},
    {"name": "Coral Sea", "lat": -18.0, "lon": 155.0},
    {"name": "Sea of Japan", "lat": 40.0, "lon": 135.0},
    {"name": "Gulf of Mexico", "lat": 25.0, "lon": -90.0},
    {"name": "Tasman Sea", "lat": -38.0, "lon": 160.0},
    {"name": "Philippine Sea", "lat": 20.0, "lon": 130.0},
    {"name": "Bering Sea", "lat": 57.0, "lon": -175.0},
    {"name": "South China Sea", "lat": 12.0, "lon": 115.0},
    {"name": "Drake Passage", "lat": -58.0, "lon": -65.0},
    {"name": "Mozambique Channel", "lat": -18.0, "lon": 42.0},
    {"name": "East Pacific", "lat": 5.0, "lon": -110.0},
]

# Ring of Fire coordinates for polyline visualization
RING_OF_FIRE = [
    (-54.8, -69.0), (-46.0, -75.0), (-38.0, -73.0), (-30.0, -71.5),
    (-20.0, -70.0), (-10.0, -76.0), (0.0, -80.0), (10.0, -84.0),
    (15.0, -90.0), (20.0, -105.0), (25.0, -110.0), (32.0, -117.0),
    (40.0, -124.0), (48.0, -123.0), (52.0, -132.0), (55.0, -135.0),
    (57.0, -155.0), (54.0, -165.0), (52.0, -178.0), (50.0, 175.0),
    (48.0, 158.0), (44.0, 148.0), (40.0, 143.0), (35.0, 140.0),
    (30.0, 132.0), (25.0, 125.0), (18.0, 120.0), (12.0, 124.0),
    (5.0, 127.0), (0.0, 128.0), (-5.0, 130.0), (-8.0, 140.0),
    (-15.0, 150.0), (-20.0, 170.0), (-25.0, 178.0), (-30.0, -178.0),
    (-35.0, -175.0), (-40.0, -176.0), (-44.0, 170.0), (-46.0, 167.0),
]

# WMO weather code to emoji mapping
WMO_EMOJI = {
    0: "\u2600\ufe0f", 1: "\U0001f324\ufe0f", 2: "\u26c5", 3: "\u2601\ufe0f",
    45: "\U0001f32b\ufe0f", 48: "\U0001f32b\ufe0f",
    51: "\U0001f326\ufe0f", 53: "\U0001f326\ufe0f", 55: "\U0001f327\ufe0f",
    61: "\U0001f327\ufe0f", 63: "\U0001f327\ufe0f", 65: "\U0001f327\ufe0f",
    71: "\U0001f328\ufe0f", 73: "\u2744\ufe0f", 75: "\u2744\ufe0f",
    80: "\U0001f326\ufe0f", 81: "\U0001f327\ufe0f", 82: "\u26c8\ufe0f",
    95: "\u26a1", 96: "\u26a1\u2744\ufe0f", 99: "\u26a1\u2744\ufe0f",
}

WMO_DESC = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm + hail", 99: "Thunderstorm + hail",
}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _temp_color(temp_c: float) -> str:
    """Map temperature to a blue-red gradient hex color."""
    if temp_c <= -20:
        return "#1e3a5f"
    elif temp_c <= -10:
        return "#2563eb"
    elif temp_c <= 0:
        return "#38bdf8"
    elif temp_c <= 10:
        return "#06b6d4"
    elif temp_c <= 20:
        return "#10b981"
    elif temp_c <= 30:
        return "#f59e0b"
    elif temp_c <= 40:
        return "#ef4444"
    else:
        return "#991b1b"


def _mag_color(mag: float) -> str:
    """Earthquake magnitude to color."""
    if mag < 3.0:
        return "#10b981"
    elif mag < 4.0:
        return "#f59e0b"
    elif mag < 5.0:
        return "#f97316"
    elif mag < 6.0:
        return "#ef4444"
    elif mag < 7.0:
        return "#dc2626"
    return "#991b1b"


def _mag_radius(mag: float) -> float:
    """Earthquake magnitude to circle radius."""
    if mag < 3.0:
        return 4
    elif mag < 4.0:
        return 6
    elif mag < 5.0:
        return 9
    elif mag < 6.0:
        return 13
    elif mag < 7.0:
        return 17
    return 22


def _aqi_color(aqi: float) -> str:
    """European AQI to color."""
    if aqi <= 20:
        return "#10b981"
    elif aqi <= 40:
        return "#22c55e"
    elif aqi <= 60:
        return "#f59e0b"
    elif aqi <= 80:
        return "#f97316"
    elif aqi <= 100:
        return "#ef4444"
    return "#8b5cf6"


def _aqi_label(aqi: float) -> str:
    """European AQI to label."""
    if aqi <= 20:
        return "Good"
    elif aqi <= 40:
        return "Fair"
    elif aqi <= 60:
        return "Moderate"
    elif aqi <= 80:
        return "Poor"
    elif aqi <= 100:
        return "Very Poor"
    return "Extremely Poor"


def _uv_color(uv: float) -> str:
    """UV index to color."""
    if uv <= 2:
        return "#10b981"
    elif uv <= 5:
        return "#f59e0b"
    elif uv <= 7:
        return "#f97316"
    elif uv <= 10:
        return "#ef4444"
    return "#8b5cf6"


def _uv_label(uv: float) -> str:
    """UV index to risk label."""
    if uv <= 2:
        return "Low"
    elif uv <= 5:
        return "Moderate"
    elif uv <= 7:
        return "High"
    elif uv <= 10:
        return "Very High"
    return "Extreme"


def _beaufort_color(wave_height: float) -> str:
    """Wave height to Beaufort-inspired color."""
    if wave_height < 0.5:
        return "#06b6d4"
    elif wave_height < 1.25:
        return "#10b981"
    elif wave_height < 2.5:
        return "#22c55e"
    elif wave_height < 4.0:
        return "#f59e0b"
    elif wave_height < 6.0:
        return "#f97316"
    elif wave_height < 9.0:
        return "#ef4444"
    return "#991b1b"


def _beaufort_label(wave_height: float) -> str:
    """Wave height to sea state description."""
    if wave_height < 0.1:
        return "Calm (glassy)"
    elif wave_height < 0.5:
        return "Calm (rippled)"
    elif wave_height < 1.25:
        return "Smooth"
    elif wave_height < 2.5:
        return "Slight"
    elif wave_height < 4.0:
        return "Moderate"
    elif wave_height < 6.0:
        return "Rough"
    elif wave_height < 9.0:
        return "Very Rough"
    elif wave_height < 14.0:
        return "High"
    return "Phenomenal"


def _wind_arrow_svg(direction_deg: float, speed: float = 10) -> str:
    """Create a small SVG wind direction arrow."""
    size = min(max(int(speed / 3) + 8, 8), 20)
    svg = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 20 20" '
        f'style="transform:rotate({direction_deg}deg)">'
        f'<polygon points="10,2 6,16 10,12 14,16" fill="#e8ecf4" opacity="0.9"/>'
        f'</svg>'
    )
    return svg


def _dark_fig(figsize=(8, 4)):
    """Create a matplotlib figure with dark theme."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.tick_params(colors="#8b97b0")
    ax.xaxis.label.set_color("#e8ecf4")
    ax.yaxis.label.set_color("#e8ecf4")
    ax.title.set_color("#e8ecf4")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


def _fig_to_buf(fig):
    """Convert matplotlib figure to bytes buffer."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════
# CACHED DATA FETCHING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_weather_batch(cities: list) -> list:
    """Fetch current weather for multiple cities using Open-Meteo batch API."""
    # Rate limiting configuration
    if rate_limiter:
        api_config = get_rate_limit_config("realtime_apis")
    results = []
    # Open-Meteo supports comma-separated lat/lon for batch requests
    batch_size = 25
    for i in range(0, len(cities), batch_size):
        batch = cities[i:i + batch_size]
        lats = ",".join(str(c["lat"]) for c in batch)
        lons = ",".join(str(c["lon"]) for c in batch)
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lats}&longitude={lons}&current_weather=true"
        )
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # When multiple locations, response is a list
            if isinstance(data, list):
                for j, item in enumerate(data):
                    cw = item.get("current_weather", {})
                    results.append({
                        "name": batch[j]["name"],
                        "country": batch[j].get("country", ""),
                        "lat": batch[j]["lat"],
                        "lon": batch[j]["lon"],
                        "temp": cw.get("temperature", None),
                        "windspeed": cw.get("windspeed", None),
                        "winddirection": cw.get("winddirection", None),
                        "weathercode": cw.get("weathercode", 0),
                    })
            else:
                # Single location response
                cw = data.get("current_weather", {})
                results.append({
                    "name": batch[0]["name"],
                    "country": batch[0].get("country", ""),
                    "lat": batch[0]["lat"],
                    "lon": batch[0]["lon"],
                    "temp": cw.get("temperature", None),
                    "windspeed": cw.get("windspeed", None),
                    "winddirection": cw.get("winddirection", None),
                    "weathercode": cw.get("weathercode", 0),
                })
        except Exception:
            # On failure, add cities with None values
            for c in batch:
                results.append({
                    "name": c["name"], "country": c.get("country", ""),
                    "lat": c["lat"], "lon": c["lon"],
                    "temp": None, "windspeed": None,
                    "winddirection": None, "weathercode": 0,
                })
    return results


@st.cache_data(ttl=300)
def fetch_earthquakes_recent(feed_url: str) -> list:
    """Fetch recent earthquakes from USGS GeoJSON feed."""
    try:
        resp = requests.get(feed_url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        quakes = []
        for f in data.get("features", []):
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [0, 0, 0])
            quakes.append({
                "place": props.get("place", "Unknown"),
                "mag": props.get("mag", 0),
                "time": props.get("time", 0),
                "lat": coords[1],
                "lon": coords[0],
                "depth": coords[2],
                "url": props.get("url", ""),
            })
        return quakes
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_iss_position() -> dict:
    """Fetch current ISS position."""
    try:
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pos = data.get("iss_position", {})
        return {
            "lat": float(pos.get("latitude", 0)),
            "lon": float(pos.get("longitude", 0)),
            "timestamp": data.get("timestamp", 0),
        }
    except Exception:
        return {"lat": 0, "lon": 0, "timestamp": 0}


@st.cache_data(ttl=300)
def fetch_nasa_volcanoes() -> list:
    """Fetch active volcano events from NASA EONET."""
    try:
        url = "https://eonet.gsfc.nasa.gov/api/v3/events?category=volcanoes&status=open&limit=50"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        volcanoes = []
        for event in data.get("events", []):
            geom = event.get("geometry", [])
            if geom:
                latest = geom[-1]
                coords = latest.get("coordinates", [0, 0])
                volcanoes.append({
                    "title": event.get("title", "Unknown"),
                    "lat": coords[1],
                    "lon": coords[0],
                    "date": latest.get("date", ""),
                    "id": event.get("id", ""),
                })
        return volcanoes
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_air_quality_batch(cities: list) -> list:
    """Fetch air quality for multiple cities."""
    results = []
    batch_size = 25
    for i in range(0, len(cities), batch_size):
        batch = cities[i:i + batch_size]
        lats = ",".join(str(c["lat"]) for c in batch)
        lons = ",".join(str(c["lon"]) for c in batch)
        url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={lats}&longitude={lons}"
            f"&current=pm2_5,pm10,nitrogen_dioxide,ozone,carbon_monoxide,european_aqi"
        )
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                for j, item in enumerate(data):
                    cur = item.get("current", {})
                    results.append({
                        "name": batch[j]["name"],
                        "country": batch[j].get("country", ""),
                        "lat": batch[j]["lat"],
                        "lon": batch[j]["lon"],
                        "pm2_5": cur.get("pm2_5", None),
                        "pm10": cur.get("pm10", None),
                        "no2": cur.get("nitrogen_dioxide", None),
                        "ozone": cur.get("ozone", None),
                        "co": cur.get("carbon_monoxide", None),
                        "aqi": cur.get("european_aqi", None),
                    })
            else:
                cur = data.get("current", {})
                results.append({
                    "name": batch[0]["name"],
                    "country": batch[0].get("country", ""),
                    "lat": batch[0]["lat"],
                    "lon": batch[0]["lon"],
                    "pm2_5": cur.get("pm2_5", None),
                    "pm10": cur.get("pm10", None),
                    "no2": cur.get("nitrogen_dioxide", None),
                    "ozone": cur.get("ozone", None),
                    "co": cur.get("carbon_monoxide", None),
                    "aqi": cur.get("european_aqi", None),
                })
        except Exception:
            for c in batch:
                results.append({
                    "name": c["name"], "country": c.get("country", ""),
                    "lat": c["lat"], "lon": c["lon"],
                    "pm2_5": None, "pm10": None, "no2": None,
                    "ozone": None, "co": None, "aqi": None,
                })
    return results


@st.cache_data(ttl=300)
def fetch_marine_data(points: list) -> list:
    """Fetch marine/ocean data for multiple points using Open-Meteo Marine API."""
    results = []
    batch_size = 25
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        lats = ",".join(str(p["lat"]) for p in batch)
        lons = ",".join(str(p["lon"]) for p in batch)
        url = (
            f"https://marine-api.open-meteo.com/v1/marine?"
            f"latitude={lats}&longitude={lons}"
            f"&current=wave_height,wave_period,wave_direction"
        )
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                for j, item in enumerate(data):
                    cur = item.get("current", {})
                    results.append({
                        "name": batch[j]["name"],
                        "lat": batch[j]["lat"],
                        "lon": batch[j]["lon"],
                        "wave_height": cur.get("wave_height", None),
                        "wave_period": cur.get("wave_period", None),
                        "wave_direction": cur.get("wave_direction", None),
                    })
            else:
                cur = data.get("current", {})
                results.append({
                    "name": batch[0]["name"],
                    "lat": batch[0]["lat"],
                    "lon": batch[0]["lon"],
                    "wave_height": cur.get("wave_height", None),
                    "wave_period": cur.get("wave_period", None),
                    "wave_direction": cur.get("wave_direction", None),
                })
        except Exception:
            for p in batch:
                results.append({
                    "name": p["name"], "lat": p["lat"], "lon": p["lon"],
                    "wave_height": None, "wave_period": None,
                    "wave_direction": None,
                })
    return results


@st.cache_data(ttl=300)
def fetch_uv_solar_batch(cities: list) -> list:
    """Fetch UV index and solar radiation for multiple cities."""
    results = []
    batch_size = 25
    for i in range(0, len(cities), batch_size):
        batch = cities[i:i + batch_size]
        lats = ",".join(str(c["lat"]) for c in batch)
        lons = ",".join(str(c["lon"]) for c in batch)
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lats}&longitude={lons}"
            f"&current=uv_index,direct_radiation"
        )
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                for j, item in enumerate(data):
                    cur = item.get("current", {})
                    results.append({
                        "name": batch[j]["name"],
                        "country": batch[j].get("country", ""),
                        "lat": batch[j]["lat"],
                        "lon": batch[j]["lon"],
                        "uv_index": cur.get("uv_index", None),
                        "direct_radiation": cur.get("direct_radiation", None),
                    })
            else:
                cur = data.get("current", {})
                results.append({
                    "name": batch[0]["name"],
                    "country": batch[0].get("country", ""),
                    "lat": batch[0]["lat"],
                    "lon": batch[0]["lon"],
                    "uv_index": cur.get("uv_index", None),
                    "direct_radiation": cur.get("direct_radiation", None),
                })
        except Exception:
            for c in batch:
                results.append({
                    "name": c["name"], "country": c.get("country", ""),
                    "lat": c["lat"], "lon": c["lon"],
                    "uv_index": None, "direct_radiation": None,
                })
    return results


# ═══════════════════════════════════════════════════════════════
# DASHBOARD MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_live_world_overview():
    """Mode 1: Live World Overview combining weather, earthquakes, and ISS."""
    st.markdown("#### Live World Overview")
    st.caption("Temperature for 30 major cities + recent earthquakes (M2.5+ past 24h) + ISS position")

    with st.spinner("Fetching live data from multiple sources..."):
        # Fetch weather for first 30 cities
        weather_data = fetch_weather_batch(WORLD_CITIES[:30])
        quakes = fetch_earthquakes_recent(
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
        )
        iss = fetch_iss_position()

    valid_weather = [w for w in weather_data if w["temp"] is not None]

    # ── Stats ──
    if valid_weather:
        temps = [w["temp"] for w in valid_weather]
        hottest = max(valid_weather, key=lambda x: x["temp"])
        coldest = min(valid_weather, key=lambda x: x["temp"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Hottest City", f"{hottest['name']}", f"{hottest['temp']:.1f} C")
        c2.metric("Coldest City", f"{coldest['name']}", f"{coldest['temp']:.1f} C")
        c3.metric("Earthquakes (24h)", f"{len(quakes)}")
        c4.metric("ISS Position", f"{iss['lat']:.2f}, {iss['lon']:.2f}")

    # ── Map ──
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # Temperature circles
    for w in valid_weather:
        color = _temp_color(w["temp"])
        popup_text = (
            f"<b>{html.escape(w['name'])}</b><br>"
            f"Temp: {w['temp']:.1f}&deg;C<br>"
            f"Wind: {w.get('windspeed', 'N/A')} km/h<br>"
            f"Code: {WMO_DESC.get(w.get('weathercode', 0), 'Unknown')}"
        )
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=200),
            tooltip=f"{html.escape(w['name'])}: {w['temp']:.1f}C",
        ).add_to(m)

    # Earthquake markers
    for q in quakes:
        color = _mag_color(q["mag"])
        radius = _mag_radius(q["mag"])
        eq_time = datetime.utcfromtimestamp(q["time"] / 1000).strftime("%Y-%m-%d %H:%M UTC")
        popup_text = (
            f"<b>M{q['mag']:.1f}</b><br>"
            f"{html.escape(q['place'])}<br>"
            f"Depth: {q['depth']:.1f} km<br>"
            f"Time: {html.escape(eq_time)}"
        )
        folium.CircleMarker(
            location=[q["lat"], q["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"M{q['mag']:.1f} - {html.escape(q['place'])}",
        ).add_to(m)

    # ISS marker
    if iss["lat"] != 0 or iss["lon"] != 0:
        iss_popup = (
            f"<b>International Space Station</b><br>"
            f"Lat: {iss['lat']:.4f}<br>"
            f"Lon: {iss['lon']:.4f}<br>"
            f"Altitude: ~408 km"
        )
        folium.CircleMarker(
            location=[iss["lat"], iss["lon"]],
            radius=10,
            color="#06b6d4",
            fill=True,
            fill_color="#06b6d4",
            fill_opacity=0.9,
            popup=folium.Popup(iss_popup, max_width=200),
            tooltip="ISS - International Space Station",
        ).add_to(m)
        # Orbit preview circle
        folium.Circle(
            location=[iss["lat"], iss["lon"]],
            radius=500000,
            color="#06b6d4",
            fill=False,
            weight=1,
            opacity=0.3,
            dash_array="5",
        ).add_to(m)

    map_html = m._repr_html_()
    components.html(map_html, height=650, scrolling=False)

    # ── Legend ──
    st.markdown(
        "**Legend:** "
        "Colored circles = city temperatures (blue=cold, red=hot) | "
        "Red circles = earthquakes (size = magnitude) | "
        "Cyan dot = ISS position"
    )

    # ── Data tables ──
    if valid_weather:
        with st.expander("City Temperature Data", expanded=False):
            df_w = pd.DataFrame(valid_weather)
            df_w = df_w.sort_values("temp", ascending=False).reset_index(drop=True)
            st.dataframe(df_w[["name", "country", "temp", "windspeed", "weathercode"]],
                         width="stretch")

    if quakes:
        with st.expander("Recent Earthquakes", expanded=False):
            df_q = pd.DataFrame(quakes)
            df_q["time_str"] = pd.to_datetime(df_q["time"], unit="ms").dt.strftime("%Y-%m-%d %H:%M")
            df_q = df_q.sort_values("mag", ascending=False).reset_index(drop=True)
            st.dataframe(df_q[["place", "mag", "depth", "time_str", "lat", "lon"]],
                         width="stretch")


def _render_global_weather():
    """Mode 2: Global Weather Now with 50 cities."""
    st.markdown("#### Global Weather Now")
    st.caption("Current weather for 50 cities across all continents")

    with st.spinner("Fetching weather data for 50 cities..."):
        weather_data = fetch_weather_batch(WORLD_CITIES)

    valid = [w for w in weather_data if w["temp"] is not None]
    if not valid:
        st.error("Could not fetch weather data. Please try again.")
        return

    temps = [w["temp"] for w in valid]
    hottest = max(valid, key=lambda x: x["temp"])
    coldest = min(valid, key=lambda x: x["temp"])
    windiest = max(valid, key=lambda x: (x["windspeed"] or 0))
    avg_temp = sum(temps) / len(temps)

    # ── Stats ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hottest", f"{hottest['name']}", f"{hottest['temp']:.1f} C")
    c2.metric("Coldest", f"{coldest['name']}", f"{coldest['temp']:.1f} C")
    c3.metric("Windiest", f"{windiest['name']}", f"{windiest.get('windspeed', 0):.0f} km/h")
    c4.metric("Global Avg", f"{avg_temp:.1f} C")

    # ── Map ──
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for w in valid:
        color = _temp_color(w["temp"])
        wcode = w.get("weathercode", 0)
        emoji = WMO_EMOJI.get(wcode, "")
        desc = WMO_DESC.get(wcode, "Unknown")
        popup_text = (
            f"<b>{html.escape(w['name'])}, {html.escape(w.get('country', ''))}</b><br>"
            f"Temp: {w['temp']:.1f}&deg;C<br>"
            f"Wind: {w.get('windspeed', 'N/A')} km/h "
            f"({w.get('winddirection', 'N/A')}&deg;)<br>"
            f"Conditions: {html.escape(desc)}"
        )
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=220),
            tooltip=f"{html.escape(w['name'])}: {w['temp']:.1f}C {emoji}",
        ).add_to(m)

        # Wind direction arrow as DivIcon
        if w.get("winddirection") is not None and w.get("windspeed") is not None:
            arrow_html = _wind_arrow_svg(w["winddirection"], w["windspeed"])
            folium.Marker(
                location=[w["lat"] + 0.8, w["lon"] + 0.8],
                icon=folium.DivIcon(
                    html=arrow_html,
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                ),
            ).add_to(m)

    map_html = m._repr_html_()
    components.html(map_html, height=650, scrolling=False)

    # ── Temperature distribution histogram ──
    st.markdown("#### Temperature Distribution")
    fig, ax = _dark_fig(figsize=(9, 3.5))
    colors_hist = [_temp_color(t) for t in sorted(temps)]
    ax.hist(temps, bins=15, color="#06b6d4", edgecolor="#2a3550", alpha=0.8)
    ax.set_xlabel("Temperature (C)")
    ax.set_ylabel("Number of Cities")
    ax.set_title("Global Temperature Distribution")
    ax.axvline(avg_temp, color="#f59e0b", linestyle="--", linewidth=1.5, label=f"Avg {avg_temp:.1f}C")
    ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4")
    st.image(_fig_to_buf(fig), use_container_width=True)

    # ── Data table ──
    with st.expander("Full Weather Data", expanded=False):
        df = pd.DataFrame(valid)
        df["condition"] = df["weathercode"].apply(lambda c: WMO_DESC.get(c, "Unknown"))
        df = df.sort_values("temp", ascending=False).reset_index(drop=True)
        st.dataframe(
            df[["name", "country", "temp", "windspeed", "winddirection", "condition"]],
            width="stretch",
        )

    # ── Download ──
    csv_buf = io.StringIO()
    pd.DataFrame(valid).to_csv(csv_buf, index=False)
    st.download_button(
        "Download Weather CSV", csv_buf.getvalue(),
        "global_weather.csv", "text/csv", key="dl_weather",
    )


def _render_earthquake_volcano():
    """Mode 3: Earthquake & Volcano Monitor."""
    st.markdown("#### Earthquake & Volcano Monitor")
    st.caption("USGS earthquakes (past 7 days, M2.5+) + NASA EONET active volcanoes")

    with st.spinner("Fetching seismic and volcanic data..."):
        quakes = fetch_earthquakes_recent(
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson"
        )
        volcanoes = fetch_nasa_volcanoes()

    # ── Stats ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Earthquakes (7d)", f"{len(quakes)}")
    c2.metric("Active Volcanoes", f"{len(volcanoes)}")
    max_mag = max((q["mag"] for q in quakes), default=0)
    c3.metric("Max Magnitude", f"M{max_mag:.1f}" if quakes else "N/A")
    avg_depth = sum(q["depth"] for q in quakes) / len(quakes) if quakes else 0
    c4.metric("Avg Depth", f"{avg_depth:.1f} km")

    # ── Map ──
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # Ring of Fire polyline
    folium.PolyLine(
        locations=RING_OF_FIRE,
        color="#f97316",
        weight=1.5,
        opacity=0.4,
        dash_array="8 4",
        tooltip="Ring of Fire",
    ).add_to(m)

    # Earthquakes
    for q in quakes:
        color = _mag_color(q["mag"])
        radius = _mag_radius(q["mag"])
        eq_time = datetime.utcfromtimestamp(q["time"] / 1000).strftime("%Y-%m-%d %H:%M UTC")
        popup_text = (
            f"<b>M{q['mag']:.1f} Earthquake</b><br>"
            f"{html.escape(q['place'])}<br>"
            f"Depth: {q['depth']:.1f} km<br>"
            f"Time: {html.escape(eq_time)}"
        )
        folium.CircleMarker(
            location=[q["lat"], q["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"M{q['mag']:.1f} - {html.escape(q['place'])}",
        ).add_to(m)

    # Volcanoes as triangle markers (using DivIcon)
    for v in volcanoes:
        triangle_html = (
            '<div style="font-size:18px;color:#f97316;text-shadow:0 0 4px #f97316;">'
            '&#9650;</div>'
        )
        popup_text = (
            f"<b>{html.escape(v['title'])}</b><br>"
            f"Status: Active<br>"
            f"Last update: {html.escape(v.get('date', 'N/A')[:10])}"
        )
        folium.Marker(
            location=[v["lat"], v["lon"]],
            icon=folium.DivIcon(
                html=triangle_html,
                icon_size=(20, 20),
                icon_anchor=(10, 18),
            ),
            popup=folium.Popup(popup_text, max_width=220),
            tooltip=html.escape(v["title"]),
        ).add_to(m)

    map_html = m._repr_html_()
    components.html(map_html, height=650, scrolling=False)

    st.markdown(
        "**Legend:** Red circles = earthquakes (size = magnitude) | "
        "Orange triangles = active volcanoes | "
        "Dashed line = Ring of Fire"
    )

    # ── Magnitude distribution chart ──
    if quakes:
        st.markdown("#### Magnitude Distribution")
        mags = [q["mag"] for q in quakes]
        fig, ax = _dark_fig(figsize=(9, 3.5))
        bins = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0]
        ax.hist(mags, bins=bins, color="#ef4444", edgecolor="#2a3550", alpha=0.8)
        ax.set_xlabel("Magnitude")
        ax.set_ylabel("Count")
        ax.set_title("Earthquake Magnitude Distribution (Past 7 Days)")
        st.image(_fig_to_buf(fig), use_container_width=True)

    # ── Timeline ──
    if quakes:
        st.markdown("#### Recent Events Timeline")
        sorted_quakes = sorted(quakes, key=lambda x: x["time"], reverse=True)[:20]
        timeline_data = []
        for q in sorted_quakes:
            t = datetime.utcfromtimestamp(q["time"] / 1000)
            timeline_data.append({
                "Time (UTC)": t.strftime("%Y-%m-%d %H:%M"),
                "Magnitude": f"M{q['mag']:.1f}",
                "Location": q["place"],
                "Depth (km)": f"{q['depth']:.1f}",
            })
        st.dataframe(pd.DataFrame(timeline_data), width="stretch")

    # ── Data tables ──
    if volcanoes:
        with st.expander("Active Volcanoes List", expanded=False):
            df_v = pd.DataFrame(volcanoes)
            st.dataframe(df_v[["title", "lat", "lon", "date"]], width="stretch")

    # ── Download ──
    if quakes:
        csv_buf = io.StringIO()
        pd.DataFrame(quakes).to_csv(csv_buf, index=False)
        st.download_button(
            "Download Earthquake CSV", csv_buf.getvalue(),
            "earthquakes_7d.csv", "text/csv", key="dl_eq",
        )


def _render_air_quality_world():
    """Mode 4: Air Quality World Map."""
    st.markdown("#### Air Quality World Map")
    st.caption("European AQI with PM2.5, PM10, NO2, O3, CO for 40+ cities worldwide")

    with st.spinner("Fetching air quality data..."):
        aq_data = fetch_air_quality_batch(WORLD_CITIES[:40])

    valid = [a for a in aq_data if a["aqi"] is not None]
    if not valid:
        st.error("Could not fetch air quality data. Please try again.")
        return

    # ── Stats ──
    best = min(valid, key=lambda x: x["aqi"])
    worst = max(valid, key=lambda x: x["aqi"])
    avg_aqi = sum(a["aqi"] for a in valid) / len(valid)
    pm25_vals = [a["pm2_5"] for a in valid if a["pm2_5"] is not None]
    avg_pm25 = sum(pm25_vals) / len(pm25_vals) if pm25_vals else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cleanest City", best["name"], f"AQI {best['aqi']:.0f}")
    c2.metric("Most Polluted", worst["name"], f"AQI {worst['aqi']:.0f}")
    c3.metric("Global Avg AQI", f"{avg_aqi:.0f}", _aqi_label(avg_aqi))
    c4.metric("Avg PM2.5", f"{avg_pm25:.1f} ug/m3")

    # ── Map ──
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for a in valid:
        color = _aqi_color(a["aqi"])
        label = _aqi_label(a["aqi"])
        popup_text = (
            f"<b>{html.escape(a['name'])}, {html.escape(a.get('country', ''))}</b><br>"
            f"European AQI: {a['aqi']:.0f} ({html.escape(label)})<br>"
            f"PM2.5: {a.get('pm2_5', 'N/A')} ug/m3<br>"
            f"PM10: {a.get('pm10', 'N/A')} ug/m3<br>"
            f"NO2: {a.get('no2', 'N/A')} ug/m3<br>"
            f"O3: {a.get('ozone', 'N/A')} ug/m3<br>"
            f"CO: {a.get('co', 'N/A')} ug/m3"
        )
        folium.CircleMarker(
            location=[a["lat"], a["lon"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"{html.escape(a['name'])}: AQI {a['aqi']:.0f} ({html.escape(label)})",
        ).add_to(m)

    map_html = m._repr_html_()
    components.html(map_html, height=650, scrolling=False)

    st.markdown(
        "**AQI Scale:** "
        '<span style="color:#10b981">Good (0-20)</span> | '
        '<span style="color:#22c55e">Fair (21-40)</span> | '
        '<span style="color:#f59e0b">Moderate (41-60)</span> | '
        '<span style="color:#f97316">Poor (61-80)</span> | '
        '<span style="color:#ef4444">Very Poor (81-100)</span> | '
        '<span style="color:#8b5cf6">Extremely Poor (100+)</span>',
        unsafe_allow_html=True,
    )

    # ── AQI bar chart ──
    st.markdown("#### AQI Ranking")
    sorted_aq = sorted(valid, key=lambda x: x["aqi"])
    fig, ax = _dark_fig(figsize=(10, max(4, len(sorted_aq) * 0.25)))
    names = [a["name"] for a in sorted_aq]
    aqis = [a["aqi"] for a in sorted_aq]
    bar_colors = [_aqi_color(a) for a in aqis]
    y_pos = range(len(names))
    ax.barh(y_pos, aqis, color=bar_colors, edgecolor="#2a3550", alpha=0.85)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=7, color="#8b97b0")
    ax.set_xlabel("European AQI")
    ax.set_title("Air Quality Index by City")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    # ── Ranking table ──
    with st.expander("Detailed AQI Data", expanded=False):
        df = pd.DataFrame(valid)
        df["label"] = df["aqi"].apply(_aqi_label)
        df = df.sort_values("aqi").reset_index(drop=True)
        df.index += 1
        df.index.name = "Rank"
        st.dataframe(
            df[["name", "country", "aqi", "label", "pm2_5", "pm10", "no2", "ozone", "co"]],
            width="stretch",
        )

    # ── Download ──
    csv_buf = io.StringIO()
    pd.DataFrame(valid).to_csv(csv_buf, index=False)
    st.download_button(
        "Download AQI CSV", csv_buf.getvalue(),
        "air_quality_world.csv", "text/csv", key="dl_aq",
    )


def _render_ocean_conditions():
    """Mode 5: Ocean Conditions Live."""
    st.markdown("#### Ocean Conditions Live")
    st.caption("Wave height, period, and direction for 20 ocean monitoring points worldwide")

    with st.spinner("Fetching marine data from Open-Meteo..."):
        marine_data = fetch_marine_data(OCEAN_POINTS)

    valid = [d for d in marine_data if d["wave_height"] is not None]
    if not valid:
        st.error("Could not fetch marine data. Please try again.")
        return

    # ── Stats ──
    heights = [d["wave_height"] for d in valid]
    roughest = max(valid, key=lambda x: x["wave_height"])
    calmest = min(valid, key=lambda x: x["wave_height"])
    avg_height = sum(heights) / len(heights)
    periods = [d["wave_period"] for d in valid if d["wave_period"] is not None]
    avg_period = sum(periods) / len(periods) if periods else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Roughest", roughest["name"], f"{roughest['wave_height']:.1f} m")
    c2.metric("Calmest", calmest["name"], f"{calmest['wave_height']:.1f} m")
    c3.metric("Avg Wave Height", f"{avg_height:.1f} m")
    c4.metric("Avg Wave Period", f"{avg_period:.1f} s")

    # ── Map ──
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for d in valid:
        wh = d["wave_height"]
        color = _beaufort_color(wh)
        label = _beaufort_label(wh)
        radius = max(4, min(int(wh * 3) + 4, 22))
        direction_str = f"{d['wave_direction']:.0f} deg" if d.get("wave_direction") is not None else "N/A"
        period_str = f"{d['wave_period']:.1f} s" if d.get("wave_period") is not None else "N/A"
        popup_text = (
            f"<b>{html.escape(d['name'])}</b><br>"
            f"Wave Height: {wh:.1f} m<br>"
            f"Wave Period: {html.escape(period_str)}<br>"
            f"Wave Direction: {html.escape(direction_str)}<br>"
            f"Sea State: {html.escape(label)}"
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_text, max_width=220),
            tooltip=f"{html.escape(d['name'])}: {wh:.1f}m ({html.escape(label)})",
        ).add_to(m)

        # Wave direction arrow
        if d.get("wave_direction") is not None:
            arrow_html = _wind_arrow_svg(d["wave_direction"], wh * 5)
            folium.Marker(
                location=[d["lat"] + 1.5, d["lon"] + 1.5],
                icon=folium.DivIcon(
                    html=arrow_html,
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                ),
            ).add_to(m)

    map_html = m._repr_html_()
    components.html(map_html, height=650, scrolling=False)

    st.markdown(
        "**Sea State:** "
        '<span style="color:#06b6d4">Calm</span> | '
        '<span style="color:#10b981">Smooth</span> | '
        '<span style="color:#22c55e">Slight</span> | '
        '<span style="color:#f59e0b">Moderate</span> | '
        '<span style="color:#f97316">Rough</span> | '
        '<span style="color:#ef4444">Very Rough</span> | '
        '<span style="color:#991b1b">High+</span>',
        unsafe_allow_html=True,
    )

    # ── Surf spot ratings ──
    st.markdown("#### Surf Spot Ratings")
    surf_data = []
    for d in valid:
        wh = d["wave_height"]
        wp = d.get("wave_period") or 0
        # Simple surf rating based on wave height and period
        if 1.0 <= wh <= 3.0 and wp >= 8:
            rating = "Excellent"
            stars = 5
        elif 0.5 <= wh <= 4.0 and wp >= 6:
            rating = "Good"
            stars = 4
        elif 0.3 <= wh <= 5.0 and wp >= 4:
            rating = "Fair"
            stars = 3
        elif wh < 0.3:
            rating = "Flat"
            stars = 1
        else:
            rating = "Too Rough"
            stars = 2
        surf_data.append({
            "Location": d["name"],
            "Wave Height (m)": f"{wh:.1f}",
            "Period (s)": f"{wp:.1f}" if wp else "N/A",
            "Sea State": _beaufort_label(wh),
            "Surf Rating": rating,
            "Stars": stars,
        })
    df_surf = pd.DataFrame(surf_data).sort_values("Stars", ascending=False).reset_index(drop=True)
    st.dataframe(df_surf, width="stretch")

    # ── Wave height chart ──
    st.markdown("#### Wave Height Comparison")
    sorted_marine = sorted(valid, key=lambda x: x["wave_height"], reverse=True)
    fig, ax = _dark_fig(figsize=(9, 4))
    names = [d["name"] for d in sorted_marine]
    hts = [d["wave_height"] for d in sorted_marine]
    bar_colors = [_beaufort_color(h) for h in hts]
    ax.bar(range(len(names)), hts, color=bar_colors, edgecolor="#2a3550", alpha=0.85)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7, color="#8b97b0")
    ax.set_ylabel("Wave Height (m)")
    ax.set_title("Ocean Wave Heights")
    st.image(_fig_to_buf(fig), use_container_width=True)

    # ── Download ──
    csv_buf = io.StringIO()
    pd.DataFrame(valid).to_csv(csv_buf, index=False)
    st.download_button(
        "Download Marine CSV", csv_buf.getvalue(),
        "ocean_conditions.csv", "text/csv", key="dl_ocean",
    )


def _render_solar_uv():
    """Mode 6: Solar & UV Index."""
    st.markdown("#### Solar & UV Index")
    st.caption("Current UV index and direct solar radiation for 40+ cities")

    with st.spinner("Fetching UV and solar data..."):
        uv_data = fetch_uv_solar_batch(WORLD_CITIES[:40])

    valid = [d for d in uv_data if d["uv_index"] is not None]
    if not valid:
        st.error("Could not fetch UV/solar data. Please try again.")
        return

    # ── Stats ──
    uv_vals = [d["uv_index"] for d in valid]
    highest_uv = max(valid, key=lambda x: x["uv_index"])
    lowest_uv = min(valid, key=lambda x: x["uv_index"])
    avg_uv = sum(uv_vals) / len(uv_vals)
    rad_vals = [d["direct_radiation"] for d in valid if d["direct_radiation"] is not None]
    avg_rad = sum(rad_vals) / len(rad_vals) if rad_vals else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Highest UV", highest_uv["name"],
              f"UV {highest_uv['uv_index']:.1f} ({_uv_label(highest_uv['uv_index'])})")
    c2.metric("Lowest UV", lowest_uv["name"],
              f"UV {lowest_uv['uv_index']:.1f} ({_uv_label(lowest_uv['uv_index'])})")
    c3.metric("Global Avg UV", f"{avg_uv:.1f}", _uv_label(avg_uv))
    c4.metric("Avg Solar Radiation", f"{avg_rad:.0f} W/m2")

    # ── Map ──
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for d in valid:
        uv = d["uv_index"]
        color = _uv_color(uv)
        label = _uv_label(uv)
        radius = max(4, min(int(uv * 1.5) + 4, 18))
        rad_str = f"{d['direct_radiation']:.0f} W/m2" if d.get("direct_radiation") is not None else "N/A"
        popup_text = (
            f"<b>{html.escape(d['name'])}, {html.escape(d.get('country', ''))}</b><br>"
            f"UV Index: {uv:.1f} ({html.escape(label)})<br>"
            f"Solar Radiation: {html.escape(rad_str)}"
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=220),
            tooltip=f"{html.escape(d['name'])}: UV {uv:.1f} ({html.escape(label)})",
        ).add_to(m)

    map_html = m._repr_html_()
    components.html(map_html, height=650, scrolling=False)

    st.markdown(
        "**UV Scale:** "
        '<span style="color:#10b981">Low (0-2)</span> | '
        '<span style="color:#f59e0b">Moderate (3-5)</span> | '
        '<span style="color:#f97316">High (6-7)</span> | '
        '<span style="color:#ef4444">Very High (8-10)</span> | '
        '<span style="color:#8b5cf6">Extreme (11+)</span>',
        unsafe_allow_html=True,
    )

    # ── UV bar chart ──
    st.markdown("#### UV Index Ranking")
    sorted_uv = sorted(valid, key=lambda x: x["uv_index"], reverse=True)
    fig, ax = _dark_fig(figsize=(10, max(4, len(sorted_uv) * 0.25)))
    names = [d["name"] for d in sorted_uv]
    uvs = [d["uv_index"] for d in sorted_uv]
    bar_colors = [_uv_color(u) for u in uvs]
    y_pos = range(len(names))
    ax.barh(y_pos, uvs, color=bar_colors, edgecolor="#2a3550", alpha=0.85)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=7, color="#8b97b0")
    ax.set_xlabel("UV Index")
    ax.set_title("UV Index by City")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    # ── Solar radiation stats ──
    if rad_vals:
        st.markdown("#### Solar Radiation Distribution")
        fig2, ax2 = _dark_fig(figsize=(9, 3.5))
        ax2.hist(rad_vals, bins=12, color="#f59e0b", edgecolor="#2a3550", alpha=0.8)
        ax2.set_xlabel("Direct Radiation (W/m2)")
        ax2.set_ylabel("Number of Cities")
        ax2.set_title("Solar Radiation Distribution")
        ax2.axvline(avg_rad, color="#06b6d4", linestyle="--", linewidth=1.5,
                     label=f"Avg {avg_rad:.0f} W/m2")
        ax2.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4")
        st.image(_fig_to_buf(fig2), use_container_width=True)

    # ── Data table ──
    with st.expander("Full UV/Solar Data", expanded=False):
        df = pd.DataFrame(valid)
        df["risk"] = df["uv_index"].apply(_uv_label)
        df = df.sort_values("uv_index", ascending=False).reset_index(drop=True)
        st.dataframe(
            df[["name", "country", "uv_index", "risk", "direct_radiation"]],
            width="stretch",
        )

    # ── Download ──
    csv_buf = io.StringIO()
    pd.DataFrame(valid).to_csv(csv_buf, index=False)
    st.download_button(
        "Download UV/Solar CSV", csv_buf.getvalue(),
        "uv_solar_data.csv", "text/csv", key="dl_uv",
    )


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_realtime_dashboard_tab():
    """Main render function for the Real-Time Global Dashboard tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header red">
        <h4>Real-Time Global Dashboard</h4>
        <p>Live weather, earthquakes, air quality, and ocean conditions worldwide</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("Data refreshes every 5 minutes. All data sources are free and require no API key.")

    # ── Dashboard Mode Selector ──
    mode = st.selectbox("Dashboard Mode", [
        "Live World Overview",
        "Global Weather Now",
        "Earthquake & Volcano Monitor",
        "Air Quality World Map",
        "Ocean Conditions Live",
        "Solar & UV Index",
    ], key="rtd_mode")

    st.markdown("---")

    # ── Render selected mode ──
    if mode == "Live World Overview":
        _render_live_world_overview()
    elif mode == "Global Weather Now":
        _render_global_weather()
    elif mode == "Earthquake & Volcano Monitor":
        _render_earthquake_volcano()
    elif mode == "Air Quality World Map":
        _render_air_quality_world()
    elif mode == "Ocean Conditions Live":
        _render_ocean_conditions()
    elif mode == "Solar & UV Index":
        _render_solar_uv()
