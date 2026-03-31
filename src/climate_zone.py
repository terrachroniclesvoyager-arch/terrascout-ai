"""
Climate Zone Classifier module for TerraScout AI.
Classifies the Koppen climate zone of any location and provides
detailed climate analysis using free APIs (Open-Meteo, Open Topo Data).
No API keys required.
"""

import streamlit as st
import requests
import json
import math
from datetime import datetime, date

try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

# ======================================================================
# CONSTANTS & API ENDPOINTS
# ======================================================================

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

MONTH_FULL = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Koppen zone full names and descriptions
KOPPEN_INFO = {
    "Af":  ("Tropical Rainforest", "Hot and wet year-round with no dry season. Precipitation exceeds 60 mm every month."),
    "Am":  ("Tropical Monsoon", "Hot year-round with a short dry season offset by heavy monsoon rains."),
    "Aw":  ("Tropical Savanna (dry winter)", "Hot year-round with a distinct dry winter season."),
    "As":  ("Tropical Savanna (dry summer)", "Hot year-round with a distinct dry summer season."),
    "BWh": ("Hot Desert", "Extremely arid with high temperatures. Very low annual precipitation."),
    "BWk": ("Cold Desert", "Extremely arid with cold winters. Found at higher latitudes or elevations."),
    "BSh": ("Hot Semi-Arid (Steppe)", "Semi-arid with hot temperatures. Slightly more rain than true desert."),
    "BSk": ("Cold Semi-Arid (Steppe)", "Semi-arid with cold winters. Grassland and steppe landscapes."),
    "Cfa": ("Humid Subtropical", "Mild winters, hot humid summers with year-round precipitation."),
    "Cfb": ("Oceanic (Marine West Coast)", "Mild year-round temperatures, cool summers, frequent precipitation."),
    "Cfc": ("Subpolar Oceanic", "Cool summers and mild winters, maritime influence at high latitudes."),
    "Csa": ("Hot-summer Mediterranean", "Dry hot summers and mild wet winters. Classic Mediterranean climate."),
    "Csb": ("Warm-summer Mediterranean", "Dry warm summers and mild wet winters."),
    "Csc": ("Cold-summer Mediterranean", "Dry cool summers and mild wet winters. Rare classification."),
    "Cwa": ("Humid Subtropical (dry winter)", "Dry winters, hot wet summers. Monsoon-influenced subtropical."),
    "Cwb": ("Subtropical Highland (dry winter)", "Dry winters, warm wet summers at elevation."),
    "Cwc": ("Subpolar Oceanic (dry winter)", "Cool with dry winters. Very rare classification."),
    "Dfa": ("Hot-summer Continental", "Large seasonal temperature range, hot summers, cold snowy winters."),
    "Dfb": ("Warm-summer Continental", "Warm summers, cold winters, year-round precipitation."),
    "Dfc": ("Subarctic (Continental)", "Short cool summers, long very cold winters. Boreal/taiga climate."),
    "Dfd": ("Extremely Cold Subarctic", "Very short summers, extremely cold winters below -38C."),
    "Dsa": ("Hot-summer Continental (dry summer)", "Hot dry summers with cold winters. Rare, inland areas."),
    "Dsb": ("Warm-summer Continental (dry summer)", "Warm dry summers with cold snowy winters."),
    "Dsc": ("Subarctic (dry summer)", "Cool short dry summers with extremely cold winters."),
    "Dsd": ("Extremely Cold (dry summer)", "Extremely cold winters with dry summers. Very rare."),
    "Dwa": ("Hot-summer Continental (dry winter)", "Hot wet summers, cold dry winters. Monsoon-influenced."),
    "Dwb": ("Warm-summer Continental (dry winter)", "Warm wet summers, cold dry winters."),
    "Dwc": ("Subarctic (dry winter)", "Cool summers, very cold dry winters. Eastern Siberia type."),
    "Dwd": ("Extremely Cold (dry winter)", "Extremely cold dry winters, mild summers. Yakutsk type."),
    "ET":  ("Tundra", "Warmest month 0-10C. Permafrost, treeless landscape."),
    "EF":  ("Ice Cap", "All months below 0C. Permanent ice and snow cover."),
}

# Badge colors for each main Koppen group
KOPPEN_COLORS = {
    "A": "#e74c3c",   # Red for tropical
    "B": "#f39c12",   # Orange for arid
    "C": "#2ecc71",   # Green for temperate
    "D": "#3498db",   # Blue for continental
    "E": "#9b59b6",   # Purple for polar
}

# Reference cities for each major Koppen zone
REFERENCE_CITIES = {
    "Af":  [("Singapore", 1.35, 103.82), ("Kuala Lumpur", 3.14, 101.69), ("Manaus", -3.12, -60.02)],
    "Am":  [("Miami", 25.76, -80.19), ("Mumbai", 19.08, 72.88), ("Cairns", -16.92, 145.77)],
    "Aw":  [("Bangkok", 13.76, 100.50), ("Havana", 23.11, -82.37), ("Darwin", -12.46, 130.84)],
    "As":  [("Honolulu", 21.31, -157.86)],
    "BWh": [("Riyadh", 24.71, 46.68), ("Phoenix", 33.45, -112.07), ("Cairo", 30.04, 31.24)],
    "BWk": [("Ulaanbaatar", 47.92, 106.91), ("Lhasa", 29.65, 91.10)],
    "BSh": [("Marrakech", 31.63, -8.01), ("Niamey", 13.51, 2.11)],
    "BSk": [("Denver", 39.74, -104.98), ("Ankara", 39.93, 32.86), ("Tehran", 35.69, 51.39)],
    "Cfa": [("Tokyo", 35.68, 139.69), ("Buenos Aires", -34.60, -58.38), ("Atlanta", 33.75, -84.39)],
    "Cfb": [("London", 51.51, -0.13), ("Paris", 48.86, 2.35), ("Melbourne", -37.81, 144.96)],
    "Cfc": [("Reykjavik", 64.15, -21.94), ("Torshavn", 62.01, -6.77)],
    "Csa": [("Rome", 41.90, 12.50), ("Athens", 37.98, 23.73), ("Los Angeles", 34.05, -118.24)],
    "Csb": [("San Francisco", 37.77, -122.42), ("Porto", 41.15, -8.61), ("Cape Town", -33.93, 18.42)],
    "Csc": [("Haleakala Summit", 20.71, -156.17)],
    "Cwa": [("Hong Kong", 22.32, 114.17), ("Brasilia", -15.79, -47.88)],
    "Cwb": [("Mexico City", 19.43, -99.13), ("Addis Ababa", 9.02, 38.75), ("Bogota", 4.71, -74.07)],
    "Cwc": [],
    "Dfa": [("Chicago", 41.88, -87.63), ("Omaha", 41.26, -95.94)],
    "Dfb": [("Moscow", 55.76, 37.62), ("Helsinki", 60.17, 24.94), ("Montreal", 45.50, -73.57)],
    "Dfc": [("Anchorage", 61.22, -149.90), ("Murmansk", 68.97, 33.09), ("Yellowknife", 62.45, -114.37)],
    "Dfd": [("Yakutsk", 62.03, 129.73), ("Verkhoyansk", 67.55, 133.39)],
    "Dsa": [("Saqqez", 36.25, 46.27)],
    "Dsb": [("Flagstaff", 35.20, -111.65)],
    "Dsc": [],
    "Dsd": [],
    "Dwa": [("Beijing", 39.91, 116.40), ("Seoul", 37.57, 126.98)],
    "Dwb": [("Vladivostok", 43.12, 131.87)],
    "Dwc": [("Chita", 52.03, 113.50)],
    "Dwd": [("Oymyakon", 63.46, 142.77)],
    "ET":  [("Longyearbyen", 78.22, 15.65), ("Ushuaia", -54.81, -68.30)],
    "EF":  [("Vostok Station", -78.46, 106.84), ("Summit Camp", 72.58, -38.46)],
}

# Vegetation and crop suitability per main group
VEGETATION_SUITABILITY = {
    "A": {
        "vegetation": ["Tropical rainforest", "Mangroves", "Tropical grasslands", "Palm forests"],
        "crops": ["Rice", "Sugarcane", "Cocoa", "Coffee", "Rubber", "Bananas", "Cassava", "Oil palm"],
        "growing_season": "Year-round",
        "notes": "Very high biodiversity. Supports intensive agriculture with irrigation management.",
    },
    "B": {
        "vegetation": ["Desert scrub", "Cacti", "Sparse grassland", "Xerophytes", "Steppe grasses"],
        "crops": ["Dates", "Sorghum", "Millet", "Barley (irrigated)", "Cotton (irrigated)", "Olives"],
        "growing_season": "Variable, depends on irrigation",
        "notes": "Irrigation is critical. Drip irrigation and drought-resistant varieties recommended.",
    },
    "C": {
        "vegetation": ["Deciduous forest", "Mixed forest", "Mediterranean scrub", "Grasslands"],
        "crops": ["Wheat", "Corn", "Grapes", "Olives", "Citrus", "Soybeans", "Vegetables", "Apples"],
        "growing_season": "6-10 months",
        "notes": "Excellent for diverse agriculture. Mediterranean sub-types favor viticulture and orchards.",
    },
    "D": {
        "vegetation": ["Boreal forest (taiga)", "Mixed forest", "Coniferous forest", "Birch woodland"],
        "crops": ["Wheat", "Rye", "Oats", "Potatoes", "Flax", "Barley", "Canola", "Hardy vegetables"],
        "growing_season": "3-6 months",
        "notes": "Short growing seasons limit options. Cold-hardy and fast-maturing varieties essential.",
    },
    "E": {
        "vegetation": ["Tundra moss", "Lichens", "Arctic willow", "Sedges", "No vegetation (ice cap)"],
        "crops": ["None (traditional)", "Greenhouse crops possible", "Arctic berries"],
        "growing_season": "0-2 months",
        "notes": "Permafrost prevents conventional agriculture. Greenhouses and hydroponics used locally.",
    },
}


# ======================================================================
# API FUNCTIONS
# ======================================================================

@st.cache_data(ttl=900)
def fetch_daily_climate_data(lat: float, lon: float) -> dict:
    """Fetch daily climate data from Open-Meteo Archive and aggregate to monthly."""
    try:
        url = (
            f"{OPEN_METEO_ARCHIVE}?latitude={lat}&longitude={lon}"
            f"&start_date=2023-01-01&end_date=2023-12-31"
            f"&daily=temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&timezone=auto"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        t_mean = daily.get("temperature_2m_mean", [])
        t_max = daily.get("temperature_2m_max", [])
        t_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])

        if not dates:
            return {}

        # Aggregate to monthly
        monthly_temp_mean = [[] for _ in range(12)]
        monthly_temp_max = [[] for _ in range(12)]
        monthly_temp_min = [[] for _ in range(12)]
        monthly_precip = [0.0] * 12

        for i, d in enumerate(dates):
            try:
                month_idx = int(d.split("-")[1]) - 1
            except (ValueError, IndexError):
                continue
            if i < len(t_mean) and t_mean[i] is not None:
                monthly_temp_mean[month_idx].append(t_mean[i])
            if i < len(t_max) and t_max[i] is not None:
                monthly_temp_max[month_idx].append(t_max[i])
            if i < len(t_min) and t_min[i] is not None:
                monthly_temp_min[month_idx].append(t_min[i])
            if i < len(precip) and precip[i] is not None:
                monthly_precip[month_idx] += precip[i]

        def safe_avg(lst):
            return sum(lst) / len(lst) if lst else None

        result = {
            "temp_mean": [safe_avg(monthly_temp_mean[m]) for m in range(12)],
            "temp_max": [safe_avg(monthly_temp_max[m]) for m in range(12)],
            "temp_min": [safe_avg(monthly_temp_min[m]) for m in range(12)],
            "precip": monthly_precip,
        }
        return result
    except Exception:
        return {}


@st.cache_data(ttl=900)
def fetch_multi_year_climate(lat: float, lon: float) -> dict:
    """Fetch 4 years of daily data (2020-2023) for more robust monthly normals."""
    try:
        url = (
            f"{OPEN_METEO_ARCHIVE}?latitude={lat}&longitude={lon}"
            f"&start_date=2020-01-01&end_date=2023-12-31"
            f"&daily=temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&timezone=auto"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        t_mean = daily.get("temperature_2m_mean", [])
        t_max = daily.get("temperature_2m_max", [])
        t_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])

        if not dates:
            return {}

        monthly_temp_mean = [[] for _ in range(12)]
        monthly_temp_max = [[] for _ in range(12)]
        monthly_temp_min = [[] for _ in range(12)]
        monthly_precip_by_year = {}

        for i, d in enumerate(dates):
            try:
                parts = d.split("-")
                year = int(parts[0])
                month_idx = int(parts[1]) - 1
            except (ValueError, IndexError):
                continue
            if i < len(t_mean) and t_mean[i] is not None:
                monthly_temp_mean[month_idx].append(t_mean[i])
            if i < len(t_max) and t_max[i] is not None:
                monthly_temp_max[month_idx].append(t_max[i])
            if i < len(t_min) and t_min[i] is not None:
                monthly_temp_min[month_idx].append(t_min[i])
            if i < len(precip) and precip[i] is not None:
                key = (year, month_idx)
                monthly_precip_by_year.setdefault(key, 0.0)
                monthly_precip_by_year[key] += precip[i]

        def safe_avg(lst):
            return sum(lst) / len(lst) if lst else None

        # Average monthly precip across years
        monthly_precip_avg = []
        for m in range(12):
            vals = [monthly_precip_by_year.get((y, m), 0.0) for y in range(2020, 2024)
                    if (y, m) in monthly_precip_by_year]
            monthly_precip_avg.append(safe_avg(vals) if vals else 0.0)

        result = {
            "temp_mean": [safe_avg(monthly_temp_mean[m]) for m in range(12)],
            "temp_max": [safe_avg(monthly_temp_max[m]) for m in range(12)],
            "temp_min": [safe_avg(monthly_temp_min[m]) for m in range(12)],
            "precip": monthly_precip_avg,
        }
        return result
    except Exception:
        return {}


@st.cache_data(ttl=900)
def fetch_current_weather(lat: float, lon: float) -> dict:
    """Fetch current weather and 14-day forecast from Open-Meteo."""
    try:
        url = (
            f"{OPEN_METEO_FORECAST}?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&forecast_days=14&timezone=auto"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


@st.cache_data(ttl=900)
def fetch_elevation(lat: float, lon: float) -> float:
    """Fetch elevation from Open Topo Data."""
    try:
        url = f"{OPEN_TOPO_API}?locations={lat},{lon}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results and results[0].get("elevation") is not None:
            return float(results[0]["elevation"])
        return None
    except Exception:
        return None


# ======================================================================
# KOPPEN CLASSIFICATION ALGORITHM
# ======================================================================

def classify_koppen(temp_mean: list, precip: list) -> str:
    """
    Classify Koppen climate zone from 12 monthly temperature means (C)
    and 12 monthly precipitation totals (mm).
    Returns the Koppen code string (e.g. 'Cfa', 'BWh', 'Dfc').
    """
    if not temp_mean or not precip or len(temp_mean) != 12 or len(precip) != 12:
        return "Unknown"

    # Replace None values with 0
    temps = [t if t is not None else 0.0 for t in temp_mean]
    precs = [p if p is not None else 0.0 for p in precip]

    t_warmest = max(temps)
    t_coldest = min(temps)
    t_annual = sum(temps) / 12.0
    p_annual = sum(precs)

    # Determine if location is in Northern or Southern hemisphere
    # by checking if warmest months are Apr-Sep (Northern) or Oct-Mar (Southern)
    warmest_idx = temps.index(t_warmest)
    northern = warmest_idx in [3, 4, 5, 6, 7, 8]  # Apr-Sep

    if northern:
        summer_months = [3, 4, 5, 6, 7, 8]
        winter_months = [0, 1, 2, 9, 10, 11]
    else:
        summer_months = [0, 1, 2, 9, 10, 11]
        winter_months = [3, 4, 5, 6, 7, 8]

    p_summer = sum(precs[m] for m in summer_months)
    p_winter = sum(precs[m] for m in winter_months)
    p_driest = min(precs)
    p_wettest = max(precs)

    p_driest_summer = min(precs[m] for m in summer_months)
    p_wettest_summer = max(precs[m] for m in summer_months)
    p_driest_winter = min(precs[m] for m in winter_months)
    p_wettest_winter = max(precs[m] for m in winter_months)

    # Count months >= 10C
    months_above_10 = sum(1 for t in temps if t >= 10.0)

    # ---- Group E: Polar ----
    if t_warmest < 10.0:
        if t_warmest < 0.0:
            return "EF"
        else:
            return "ET"

    # ---- Group B: Arid ----
    # Determine precipitation threshold based on seasonality
    if p_annual > 0:
        summer_pct = p_summer / p_annual * 100.0
    else:
        summer_pct = 50.0

    if summer_pct >= 70.0:
        p_threshold = 20.0 * t_annual + 280.0
    elif summer_pct <= 30.0:
        p_threshold = 20.0 * t_annual
    else:
        p_threshold = 20.0 * t_annual + 140.0

    if p_annual < p_threshold:
        # Arid: desert vs steppe
        if p_annual < p_threshold / 2.0:
            # Desert (BW)
            if t_annual >= 18.0:
                return "BWh"
            else:
                return "BWk"
        else:
            # Steppe (BS)
            if t_annual >= 18.0:
                return "BSh"
            else:
                return "BSk"

    # ---- Group A: Tropical ----
    if t_coldest >= 18.0:
        if p_driest >= 60.0:
            return "Af"
        elif p_annual >= 25.0 * (100.0 - p_driest):
            return "Am"
        else:
            # Determine if dry season is summer or winter
            driest_idx = precs.index(p_driest)
            if driest_idx in summer_months:
                return "As"
            else:
                return "Aw"

    # ---- Group C: Temperate ----
    if t_coldest >= -3.0 and t_coldest < 18.0:
        return _classify_cd_subtypes("C", temps, precs,
                                      p_driest_summer, p_driest_winter,
                                      p_wettest_summer, p_wettest_winter,
                                      t_warmest, months_above_10)

    # ---- Group D: Continental ----
    if t_coldest < -3.0 and t_warmest >= 10.0:
        return _classify_cd_subtypes("D", temps, precs,
                                      p_driest_summer, p_driest_winter,
                                      p_wettest_summer, p_wettest_winter,
                                      t_warmest, months_above_10)

    return "Unknown"


def _classify_cd_subtypes(group: str, temps: list, precs: list,
                           p_driest_summer: float, p_driest_winter: float,
                           p_wettest_summer: float, p_wettest_winter: float,
                           t_warmest: float, months_above_10: int) -> str:
    """Classify C or D group subtypes (second and third letters)."""
    t_coldest = min(temps)

    # Second letter: precipitation pattern
    # 's' = dry summer, 'w' = dry winter, 'f' = no dry season
    dry_summer = (p_driest_summer < 40.0 and
                  p_driest_summer < (p_wettest_winter / 3.0))
    dry_winter = (p_driest_winter < (p_wettest_summer / 10.0))

    if dry_summer:
        second = "s"
    elif dry_winter:
        second = "w"
    else:
        second = "f"

    # Third letter: temperature
    if t_warmest >= 22.0:
        third = "a"
    elif months_above_10 >= 4:
        third = "b"
    elif group == "D" and t_coldest < -38.0:
        third = "d"
    else:
        third = "c"

    return f"{group}{second}{third}"


# ======================================================================
# CLIMATE ANALYSIS HELPERS
# ======================================================================

def compute_climate_indicators(temp_mean, temp_max, temp_min, precip, elevation):
    """Compute derived climate indicators from monthly data."""
    temps = [t if t is not None else 0.0 for t in temp_mean]
    tmaxs = [t if t is not None else 0.0 for t in temp_max]
    tmins = [t if t is not None else 0.0 for t in temp_min]
    precs = [p if p is not None else 0.0 for p in precip]

    annual_mean_temp = sum(temps) / 12.0
    annual_precip = sum(precs)
    warmest_month_temp = max(temps)
    coldest_month_temp = min(temps)
    seasonal_amplitude = warmest_month_temp - coldest_month_temp

    # Continentality index (Conrad index approximation)
    lat_factor = 1.0  # simplified
    continentality = (1.7 * seasonal_amplitude / (math.sin(math.radians(45)) + 0.1)) - 14.0
    continentality = max(0.0, min(100.0, continentality))

    # Estimate frost days (months where min temp < 0)
    frost_months = sum(1 for t in tmins if t < 0.0)

    # Growing season length (months with mean temp >= 5C)
    growing_months = sum(1 for t in temps if t >= 5.0)

    # Aridity index (simplified De Martonne)
    if annual_mean_temp + 10.0 > 0:
        aridity_index = annual_precip / (annual_mean_temp + 10.0)
    else:
        aridity_index = 0.0

    # Precipitation seasonality
    if annual_precip > 0:
        p_mean_monthly = annual_precip / 12.0
        p_variance = sum((p - p_mean_monthly) ** 2 for p in precs) / 12.0
        precip_seasonality = (math.sqrt(p_variance) / p_mean_monthly) * 100.0 if p_mean_monthly > 0 else 0.0
    else:
        precip_seasonality = 0.0

    return {
        "annual_mean_temp": round(annual_mean_temp, 1),
        "annual_precip": round(annual_precip, 1),
        "warmest_month": round(warmest_month_temp, 1),
        "coldest_month": round(coldest_month_temp, 1),
        "seasonal_amplitude": round(seasonal_amplitude, 1),
        "continentality": round(continentality, 1),
        "frost_months": frost_months,
        "growing_months": growing_months,
        "aridity_index": round(aridity_index, 1),
        "precip_seasonality": round(precip_seasonality, 1),
        "elevation": elevation,
    }


def compute_comfort_index(temp_mean, humidity_default=60.0):
    """
    Compute monthly climate comfort index (0-100).
    Based on temperature deviation from ideal (20-25C) and estimated humidity.
    100 = perfect comfort, 0 = extreme discomfort.
    """
    scores = []
    for i, t in enumerate(temp_mean):
        if t is None:
            scores.append(50.0)
            continue
        # Temperature comfort (ideal: 20-25C)
        if 20.0 <= t <= 25.0:
            temp_score = 100.0
        elif t < 20.0:
            temp_score = max(0.0, 100.0 - (20.0 - t) ** 1.5 * 2.5)
        else:
            temp_score = max(0.0, 100.0 - (t - 25.0) ** 1.5 * 3.0)

        # Humidity factor (penalize extremes)
        humidity_est = humidity_default + (t - 15.0) * 0.5
        humidity_est = max(20.0, min(95.0, humidity_est))
        if 40.0 <= humidity_est <= 60.0:
            humidity_factor = 1.0
        elif humidity_est < 40.0:
            humidity_factor = 0.85 + 0.15 * (humidity_est / 40.0)
        else:
            humidity_factor = max(0.6, 1.0 - (humidity_est - 60.0) / 100.0)

        comfort = temp_score * humidity_factor
        scores.append(round(max(0.0, min(100.0, comfort)), 1))
    return scores


def get_season_label(month_idx, is_northern):
    """Return season name for a given month index."""
    if is_northern:
        seasons = ["Winter", "Winter", "Spring", "Spring", "Spring", "Summer",
                    "Summer", "Summer", "Autumn", "Autumn", "Autumn", "Winter"]
    else:
        seasons = ["Summer", "Summer", "Autumn", "Autumn", "Autumn", "Winter",
                    "Winter", "Winter", "Spring", "Spring", "Spring", "Summer"]
    return seasons[month_idx]


# ======================================================================
# RENDER SECTIONS
# ======================================================================

def _render_koppen_badge(koppen_code: str):
    """Render a color-coded badge for the Koppen classification."""
    group = koppen_code[0] if koppen_code and koppen_code != "Unknown" else ""
    color = KOPPEN_COLORS.get(group, "#95a5a6")
    info = KOPPEN_INFO.get(koppen_code, ("Unknown Classification", "Could not determine climate zone."))
    full_name, description = info

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}22, {color}44);
            border: 2px solid {color};
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            text-align: center;
        ">
            <div style="font-size: 48px; font-weight: bold; color: {color};
                        letter-spacing: 4px; margin-bottom: 8px;">
                {koppen_code}
            </div>
            <div style="font-size: 20px; font-weight: 600; color: #e0e0e0;
                        margin-bottom: 6px;">
                {full_name}
            </div>
            <div style="font-size: 14px; color: #aaa; max-width: 600px;
                        margin: 0 auto;">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_classification_section(koppen_code, lat, lon, elevation):
    """Section 1: Koppen Classification with badge and location context."""
    st.subheader("1. Koppen Climate Classification")
    _render_koppen_badge(koppen_code)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Latitude", f"{lat:.4f}")
    with col2:
        st.metric("Longitude", f"{lon:.4f}")
    with col3:
        hemisphere = "Northern" if lat >= 0 else "Southern"
        st.metric("Hemisphere", hemisphere)
    with col4:
        elev_str = f"{elevation:.0f} m" if elevation is not None else "N/A"
        st.metric("Elevation", elev_str)

    # Show position on a simple folium map if available
    if HAS_FOLIUM:
        group = koppen_code[0] if koppen_code and koppen_code != "Unknown" else "C"
        color = {"A": "red", "B": "orange", "C": "green", "D": "blue", "E": "purple"}.get(group, "gray")
        m = folium.Map(location=[lat, lon], zoom_start=5, tiles="CartoDB positron")
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=f"{koppen_code}: {KOPPEN_INFO.get(koppen_code, ('',))[0]}",
        ).add_to(m)
        st_folium(m, width=700, height=350, key="clz_map_classification")
    else:
        st.info("Install folium and streamlit-folium for interactive map display.")


def _render_temperature_section(temp_mean, temp_max, temp_min):
    """Section 2: Monthly Temperature Profile."""
    st.subheader("2. Monthly Temperature Profile")

    if not HAS_PLOTLY:
        st.warning("Plotly is required for charts. Install with: pip install plotly")
        return

    temps_mean = [t if t is not None else 0.0 for t in temp_mean]
    temps_max = [t if t is not None else 0.0 for t in temp_max]
    temps_min = [t if t is not None else 0.0 for t in temp_min]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=MONTH_NAMES, y=temps_max, mode="lines+markers",
        name="Max Temp", line=dict(color="#ef4444", width=2),
        marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=MONTH_NAMES, y=temps_mean, mode="lines+markers",
        name="Mean Temp", line=dict(color="#f59e0b", width=3),
        marker=dict(size=7),
    ))
    fig.add_trace(go.Scatter(
        x=MONTH_NAMES, y=temps_min, mode="lines+markers",
        name="Min Temp", line=dict(color="#3b82f6", width=2),
        marker=dict(size=6),
    ))
    # Shade between max and min
    fig.add_trace(go.Scatter(
        x=MONTH_NAMES + MONTH_NAMES[::-1],
        y=temps_max + temps_min[::-1],
        fill="toself", fillcolor="rgba(245, 158, 11, 0.1)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_layout(
        title="Monthly Temperature Profile (2020-2023 Average)",
        xaxis_title="Month",
        yaxis_title="Temperature (C)",
        template="plotly_dark",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True, key="clz_temp_profile_chart")

    # Seasonal amplitude metrics
    amplitude = max(temps_mean) - min(temps_mean)
    warmest_idx = temps_mean.index(max(temps_mean))
    coldest_idx = temps_mean.index(min(temps_mean))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Seasonal Amplitude", f"{amplitude:.1f} C")
    with col2:
        st.metric("Warmest Month", f"{MONTH_FULL[warmest_idx]} ({temps_mean[warmest_idx]:.1f} C)")
    with col3:
        st.metric("Coldest Month", f"{MONTH_FULL[coldest_idx]} ({temps_mean[coldest_idx]:.1f} C)")


def _render_precipitation_section(precip, temp_mean):
    """Section 3: Monthly Precipitation Profile."""
    st.subheader("3. Monthly Precipitation Profile")

    if not HAS_PLOTLY:
        st.warning("Plotly is required for charts.")
        return

    precs = [p if p is not None else 0.0 for p in precip]
    annual = sum(precs)

    # Color bars by intensity
    colors = []
    for p in precs:
        if p < 20:
            colors.append("#f39c12")
        elif p < 60:
            colors.append("#27ae60")
        elif p < 150:
            colors.append("#2980b9")
        else:
            colors.append("#8e44ad")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=MONTH_NAMES, y=precs, marker_color=colors,
        text=[f"{p:.0f}" for p in precs], textposition="outside",
        name="Precipitation",
    ))
    # Add annual average line
    avg_monthly = annual / 12.0
    fig.add_hline(y=avg_monthly, line_dash="dash", line_color="#e74c3c",
                  annotation_text=f"Avg: {avg_monthly:.0f} mm")
    fig.update_layout(
        title="Monthly Precipitation Profile (2020-2023 Average)",
        xaxis_title="Month",
        yaxis_title="Precipitation (mm)",
        template="plotly_dark",
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True, key="clz_precip_profile_chart")

    # Wet/dry season identification
    wettest_idx = precs.index(max(precs))
    driest_idx = precs.index(min(precs))
    temps = [t if t is not None else 0.0 for t in temp_mean]
    warmest_idx = temps.index(max(temps))
    is_northern = warmest_idx in [3, 4, 5, 6, 7, 8]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Annual Total", f"{annual:.0f} mm")
    with col2:
        st.metric("Wettest Month", f"{MONTH_FULL[wettest_idx]} ({precs[wettest_idx]:.0f} mm)")
    with col3:
        st.metric("Driest Month", f"{MONTH_FULL[driest_idx]} ({precs[driest_idx]:.0f} mm)")
    with col4:
        ratio = precs[wettest_idx] / max(precs[driest_idx], 0.1)
        seasonality = "Strong" if ratio > 10 else "Moderate" if ratio > 3 else "Weak"
        st.metric("Seasonality", seasonality)


def _render_indicators_section(indicators):
    """Section 4: Climate Indicators."""
    st.subheader("4. Climate Indicators")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Annual Mean Temp", f"{indicators['annual_mean_temp']} C")
        st.metric("Warmest Month", f"{indicators['warmest_month']} C")
        st.metric("Coldest Month", f"{indicators['coldest_month']} C")
    with col2:
        st.metric("Annual Precipitation", f"{indicators['annual_precip']} mm")
        st.metric("Aridity Index (De Martonne)", f"{indicators['aridity_index']}")
        st.metric("Precip Seasonality", f"{indicators['precip_seasonality']:.0f}%")
    with col3:
        st.metric("Growing Season", f"{indicators['growing_months']} months")
        st.metric("Frost Months", f"{indicators['frost_months']}")
        st.metric("Continentality Index", f"{indicators['continentality']}")

    # Interpretation
    with st.expander("Indicator Interpretation Guide", expanded=False):
        st.markdown("""
**Aridity Index (De Martonne):**
- < 5: Hyper-arid desert
- 5-15: Arid
- 15-25: Semi-arid
- 25-35: Sub-humid
- 35-55: Humid
- > 55: Very humid / Perhumid

**Continentality Index:**
- < 20: Maritime / Oceanic (mild seasonal variation)
- 20-40: Sub-continental
- 40-60: Continental (large seasonal swings)
- > 60: Hyper-continental (extreme winter-summer contrast)

**Precipitation Seasonality:**
- < 30%: Fairly uniform year-round precipitation
- 30-60%: Moderate seasonal variation
- 60-100%: Strong wet/dry season contrast
- > 100%: Extreme monsoon or Mediterranean regime
        """)


def _render_vegetation_section(koppen_code):
    """Section 5: Vegetation & Agriculture Suitability."""
    st.subheader("5. Vegetation & Agriculture Suitability")

    group = koppen_code[0] if koppen_code and koppen_code != "Unknown" else None
    if group not in VEGETATION_SUITABILITY:
        st.info("Climate zone not recognized for vegetation analysis.")
        return

    veg = VEGETATION_SUITABILITY[group]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Natural Vegetation Types:**")
        for v in veg["vegetation"]:
            st.markdown(f"- {v}")
    with col2:
        st.markdown("**Suitable Crops:**")
        for c in veg["crops"]:
            st.markdown(f"- {c}")

    col3, col4 = st.columns(2)
    with col3:
        st.metric("Growing Season", veg["growing_season"])
    with col4:
        st.info(veg["notes"])

    # Detailed subtype table
    with st.expander("Detailed Suitability by Koppen Subtype", expanded=False):
        subtype_details = {
            "Af": "Year-round cropping. Ideal for rubber, palm oil, cocoa. Dense tropical forest.",
            "Am": "Monsoon crops (rice paddies). Forest with seasonal leaf drop.",
            "Aw": "Savanna grasslands. Suitable for cattle ranching, millet, sorghum.",
            "As": "Similar to Aw. Dry summer may require irrigation.",
            "BWh": "Minimal natural vegetation. Oasis agriculture with irrigation (dates, alfalfa).",
            "BWk": "Sparse scrub. Limited grazing. Irrigated crops in valleys.",
            "BSh": "Short grassland / steppe. Grazing, drought-resistant grains.",
            "BSk": "Grassland steppe. Wheat, barley. Ranching viable.",
            "Cfa": "Mixed deciduous forest. Excellent for corn, soybeans, rice, cotton.",
            "Cfb": "Temperate broadleaf forest. Wheat, barley, potatoes, dairy farming.",
            "Cfc": "Subpolar woodland. Limited agriculture, grazing, root vegetables.",
            "Csa": "Mediterranean scrub (maquis). Grapes, olives, citrus, figs.",
            "Csb": "Mediterranean woodland. Similar to Csa, cooler. Wine grapes, orchards.",
            "Csc": "Rare. Sparse heath vegetation. Very limited agriculture.",
            "Cwa": "Subtropical forest. Rice, sugarcane, tea in monsoon zones.",
            "Cwb": "Highland forest. Coffee, tea, temperate fruits at elevation.",
            "Cwc": "Rare. Mountain meadows. Limited pastoral use.",
            "Dfa": "Tallgrass prairie / mixed forest. Corn belt agriculture.",
            "Dfb": "Mixed / boreal forest transition. Wheat, rye, potatoes.",
            "Dfc": "Boreal taiga. Forestry dominant. Short-season crops (barley, oats).",
            "Dfd": "Extreme taiga. Very limited agriculture. Reindeer herding.",
            "Dsa": "Dry continental steppe. Irrigated wheat, orchards in valleys.",
            "Dsb": "Mountain forest. Forestry, limited alpine pasture.",
            "Dsc": "Sparse subarctic woodland. Minimal agriculture.",
            "Dsd": "Extreme cold. No conventional agriculture.",
            "Dwa": "Deciduous / mixed forest. Monsoon rice, soybeans, corn.",
            "Dwb": "Mixed forest. Wheat, potatoes, sunflowers.",
            "Dwc": "Boreal forest. Forestry, hunting. Very short growing season.",
            "Dwd": "Extreme continental taiga. No agriculture.",
            "ET": "Tundra mosses and lichens. No crops. Reindeer, muskox grazing.",
            "EF": "No vegetation. Permanent ice. No agriculture possible.",
        }
        detail = subtype_details.get(koppen_code, "No specific details available for this subtype.")
        st.markdown(f"**{koppen_code}:** {detail}")


def _render_comparison_section(koppen_code, indicators):
    """Section 6: Climate Comparison with reference cities."""
    st.subheader("6. Climate Comparison")

    ref_cities = REFERENCE_CITIES.get(koppen_code, [])
    if not ref_cities:
        # Fallback to group-level
        group = koppen_code[0] if koppen_code else ""
        for code, cities in REFERENCE_CITIES.items():
            if code.startswith(group) and cities:
                ref_cities = cities
                break

    if not ref_cities:
        st.info("No reference cities available for this climate zone.")
        return

    st.markdown(f"**Reference cities in the same Koppen zone ({koppen_code}):**")

    # Fetch data for up to 3 reference cities
    comparison_data = []
    for city_name, city_lat, city_lon in ref_cities[:3]:
        city_climate = fetch_daily_climate_data(city_lat, city_lon)
        if city_climate and city_climate.get("temp_mean"):
            c_temps = [t if t is not None else 0.0 for t in city_climate["temp_mean"]]
            c_precs = [p if p is not None else 0.0 for p in city_climate.get("precip", [0]*12)]
            comparison_data.append({
                "City": city_name,
                "Annual Mean Temp (C)": f"{sum(c_temps)/12:.1f}",
                "Annual Precip (mm)": f"{sum(c_precs):.0f}",
                "Warmest Month (C)": f"{max(c_temps):.1f}",
                "Coldest Month (C)": f"{min(c_temps):.1f}",
                "Amplitude (C)": f"{max(c_temps)-min(c_temps):.1f}",
            })

    # Add current location
    comparison_data.insert(0, {
        "City": "Your Location",
        "Annual Mean Temp (C)": f"{indicators['annual_mean_temp']}",
        "Annual Precip (mm)": f"{indicators['annual_precip']}",
        "Warmest Month (C)": f"{indicators['warmest_month']}",
        "Coldest Month (C)": f"{indicators['coldest_month']}",
        "Amplitude (C)": f"{indicators['seasonal_amplitude']}",
    })

    st.table(comparison_data)

    # Visual comparison chart
    if HAS_PLOTLY and len(comparison_data) > 1:
        cities = [d["City"] for d in comparison_data]
        mean_temps = [float(d["Annual Mean Temp (C)"]) for d in comparison_data]
        precips = [float(d["Annual Precip (mm)"]) for d in comparison_data]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=cities, y=mean_temps, name="Mean Temp (C)",
            marker_color="#ef4444", yaxis="y",
        ))
        fig.add_trace(go.Bar(
            x=cities, y=precips, name="Annual Precip (mm)",
            marker_color="#3b82f6", yaxis="y2",
        ))
        fig.update_layout(
            title="Comparison with Reference Cities",
            yaxis=dict(title="Temperature (C)", side="left"),
            yaxis2=dict(title="Precipitation (mm)", side="right", overlaying="y"),
            template="plotly_dark",
            barmode="group",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True, key="clz_comparison_chart")


def _render_comfort_section(temp_mean):
    """Section 7: Climate Comfort Index."""
    st.subheader("7. Climate Comfort Index")

    comfort_scores = compute_comfort_index(temp_mean)
    temps = [t if t is not None else 0.0 for t in temp_mean]
    warmest_idx = temps.index(max(temps))
    is_northern = warmest_idx in [3, 4, 5, 6, 7, 8]

    if HAS_PLOTLY:
        # Comfort line chart with color zones
        fig = go.Figure()

        # Background zones
        fig.add_hrect(y0=80, y1=100, fillcolor="rgba(46, 204, 113, 0.15)",
                      line_width=0, annotation_text="Comfortable",
                      annotation_position="top left")
        fig.add_hrect(y0=50, y1=80, fillcolor="rgba(241, 196, 15, 0.1)",
                      line_width=0, annotation_text="Moderate",
                      annotation_position="top left")
        fig.add_hrect(y0=20, y1=50, fillcolor="rgba(230, 126, 34, 0.1)",
                      line_width=0, annotation_text="Uncomfortable",
                      annotation_position="top left")
        fig.add_hrect(y0=0, y1=20, fillcolor="rgba(231, 76, 60, 0.1)",
                      line_width=0, annotation_text="Extreme",
                      annotation_position="top left")

        # Color each point by comfort level
        colors = []
        for s in comfort_scores:
            if s >= 80:
                colors.append("#2ecc71")
            elif s >= 50:
                colors.append("#f1c40f")
            elif s >= 20:
                colors.append("#e67e22")
            else:
                colors.append("#e74c3c")

        fig.add_trace(go.Scatter(
            x=MONTH_NAMES, y=comfort_scores,
            mode="lines+markers+text",
            text=[f"{s:.0f}" for s in comfort_scores],
            textposition="top center",
            line=dict(color="#2ecc71", width=3),
            marker=dict(size=12, color=colors, line=dict(width=2, color="#fff")),
            name="Comfort Score",
        ))

        fig.update_layout(
            title="Monthly Climate Comfort Index (0-100)",
            xaxis_title="Month",
            yaxis_title="Comfort Score",
            yaxis=dict(range=[0, 110]),
            template="plotly_dark",
            height=450,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, key="clz_comfort_chart")

    # Summary metrics
    best_month_idx = comfort_scores.index(max(comfort_scores))
    worst_month_idx = comfort_scores.index(min(comfort_scores))
    avg_comfort = sum(comfort_scores) / 12.0
    comfortable_months = sum(1 for s in comfort_scores if s >= 70)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Best Month", f"{MONTH_FULL[best_month_idx]} ({comfort_scores[best_month_idx]:.0f})")
    with col2:
        st.metric("Worst Month", f"{MONTH_FULL[worst_month_idx]} ({comfort_scores[worst_month_idx]:.0f})")
    with col3:
        st.metric("Annual Average", f"{avg_comfort:.0f}/100")
    with col4:
        st.metric("Comfortable Months", f"{comfortable_months}/12")

    # Seasonal comfort breakdown
    with st.expander("Seasonal Comfort Breakdown", expanded=False):
        seasons_data = []
        season_groups = {
            "Spring": [2, 3, 4] if is_northern else [8, 9, 10],
            "Summer": [5, 6, 7] if is_northern else [11, 0, 1],
            "Autumn": [8, 9, 10] if is_northern else [2, 3, 4],
            "Winter": [11, 0, 1] if is_northern else [5, 6, 7],
        }
        for season, months in season_groups.items():
            s_scores = [comfort_scores[m] for m in months]
            s_temps = [temps[m] for m in months]
            avg_s = sum(s_scores) / len(s_scores)
            avg_t = sum(s_temps) / len(s_temps)
            rating = "Excellent" if avg_s >= 80 else "Good" if avg_s >= 60 else "Fair" if avg_s >= 40 else "Poor"
            seasons_data.append({
                "Season": season,
                "Avg Comfort Score": f"{avg_s:.0f}",
                "Avg Temperature (C)": f"{avg_t:.1f}",
                "Rating": rating,
            })
        st.table(seasons_data)

    # Travel recommendation
    with st.expander("Best Time to Visit", expanded=False):
        good_months = [(MONTH_FULL[i], comfort_scores[i]) for i in range(12) if comfort_scores[i] >= 65]
        if good_months:
            good_months.sort(key=lambda x: -x[1])
            st.markdown("**Recommended months (comfort score >= 65):**")
            for m_name, m_score in good_months:
                bar_len = int(m_score / 2)
                bar = "=" * bar_len
                st.markdown(f"- **{m_name}**: {m_score:.0f}/100 `{bar}`")
        else:
            st.warning("No months achieve a comfort score of 65 or above. "
                       "This location has challenging climate conditions year-round.")


# ======================================================================
# CURRENT CONDITIONS SIDEBAR
# ======================================================================

def _render_current_conditions(weather_data):
    """Render current weather conditions in an expander."""
    current = weather_data.get("current", {})
    if not current:
        return

    with st.expander("Current Weather Conditions", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            temp = current.get("temperature_2m")
            st.metric("Temperature", f"{temp} C" if temp is not None else "N/A")
        with col2:
            humidity = current.get("relative_humidity_2m")
            st.metric("Humidity", f"{humidity}%" if humidity is not None else "N/A")
        with col3:
            wind = current.get("wind_speed_10m")
            st.metric("Wind Speed", f"{wind} km/h" if wind is not None else "N/A")

        # 14-day forecast summary
        daily = weather_data.get("daily", {})
        daily_dates = daily.get("time", [])
        daily_tmax = daily.get("temperature_2m_max", [])
        daily_tmin = daily.get("temperature_2m_min", [])
        daily_precip = daily.get("precipitation_sum", [])

        if daily_dates and HAS_PLOTLY:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_dates, y=daily_tmax, mode="lines",
                name="Max", line=dict(color="#ef4444"),
            ))
            fig.add_trace(go.Scatter(
                x=daily_dates, y=daily_tmin, mode="lines",
                name="Min", line=dict(color="#3b82f6"),
            ))
            fig.add_trace(go.Bar(
                x=daily_dates, y=daily_precip,
                name="Precip (mm)", marker_color="rgba(52, 152, 219, 0.5)",
                yaxis="y2",
            ))
            fig.update_layout(
                title="14-Day Forecast",
                yaxis=dict(title="Temp (C)"),
                yaxis2=dict(title="Precip (mm)", overlaying="y", side="right"),
                template="plotly_dark",
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True, key="clz_forecast_chart")


# ======================================================================
# MAIN ENTRY POINT
# ======================================================================

def render_climate_zone_tab():
    """Main entry point for the Climate Zone Classifier module."""
    st.title("Climate Zone Classifier")
    st.markdown(
        "Classify any location into its **Koppen climate zone** and explore "
        "detailed climate analysis including temperature/precipitation profiles, "
        "vegetation suitability, comfort indices, and comparisons with reference cities."
    )

    # --- Input Controls ---
    st.markdown("---")
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        lat = st.number_input(
            "Latitude", min_value=-90.0, max_value=90.0,
            value=41.9, step=0.01, format="%.4f", key="clz_lat",
        )
    with col_input2:
        lon = st.number_input(
            "Longitude", min_value=-180.0, max_value=180.0,
            value=12.5, step=0.01, format="%.4f", key="clz_lon",
        )

    # Quick preset locations
    preset_options = {
        "Custom": None,
        "Rome, Italy (Csa)": (41.90, 12.50),
        "London, UK (Cfb)": (51.51, -0.13),
        "Singapore (Af)": (1.35, 103.82),
        "Phoenix, USA (BWh)": (33.45, -112.07),
        "Moscow, Russia (Dfb)": (55.76, 37.62),
        "Manaus, Brazil (Af)": (-3.12, -60.02),
        "Anchorage, USA (Dfc)": (61.22, -149.90),
        "Cairo, Egypt (BWh)": (30.04, 31.24),
        "Tokyo, Japan (Cfa)": (35.68, 139.69),
        "Longyearbyen (ET)": (78.22, 15.65),
    }
    preset = st.selectbox(
        "Quick Presets", options=list(preset_options.keys()),
        index=0, key="clz_preset",
    )
    if preset != "Custom" and preset_options[preset] is not None:
        lat, lon = preset_options[preset]

    analyze_btn = st.button("Classify Climate Zone", key="clz_analyze_btn", type="primary")

    if not analyze_btn:
        st.info("Enter coordinates or select a preset, then click **Classify Climate Zone** to begin analysis.")
        return

    # --- Fetch Data ---
    with st.spinner("Fetching climate data (2020-2023 daily records)..."):
        climate_data = fetch_multi_year_climate(lat, lon)

    if not climate_data or not climate_data.get("temp_mean"):
        st.error("Could not retrieve climate data for this location. "
                 "The Open-Meteo archive may not cover this area or the API may be temporarily unavailable.")
        return

    temp_mean = climate_data["temp_mean"]
    temp_max = climate_data["temp_max"]
    temp_min = climate_data["temp_min"]
    precip = climate_data["precip"]

    # Validate data
    valid_temps = [t for t in temp_mean if t is not None]
    if len(valid_temps) < 12:
        st.warning(f"Only {len(valid_temps)}/12 months have valid temperature data. "
                   "Classification may be less accurate.")

    # Fetch supporting data
    with st.spinner("Fetching elevation and current weather..."):
        elevation = fetch_elevation(lat, lon)
        weather_data = fetch_current_weather(lat, lon)

    # --- Classify ---
    koppen_code = classify_koppen(temp_mean, precip)
    indicators = compute_climate_indicators(temp_mean, temp_max, temp_min, precip, elevation)

    # --- Render Current Conditions ---
    _render_current_conditions(weather_data)

    st.markdown("---")

    # --- Section 1: Classification ---
    _render_classification_section(koppen_code, lat, lon, elevation)

    st.markdown("---")

    # --- Section 2: Temperature ---
    _render_temperature_section(temp_mean, temp_max, temp_min)

    st.markdown("---")

    # --- Section 3: Precipitation ---
    _render_precipitation_section(precip, temp_mean)

    st.markdown("---")

    # --- Section 4: Climate Indicators ---
    _render_indicators_section(indicators)

    st.markdown("---")

    # --- Section 5: Vegetation ---
    _render_vegetation_section(koppen_code)

    st.markdown("---")

    # --- Section 6: Comparison ---
    _render_comparison_section(koppen_code, indicators)

    st.markdown("---")

    # --- Section 7: Comfort ---
    _render_comfort_section(temp_mean)

    # --- Footer ---
    st.markdown("---")
    st.caption(
        "Data sources: Open-Meteo Archive API (2020-2023 daily), "
        "Open-Meteo Forecast API, Open Topo Data (SRTM 30m). "
        "Koppen classification algorithm implemented in pure Python. "
        "All APIs are free and require no API keys."
    )
