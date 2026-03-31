# -*- coding: utf-8 -*-
"""
Population & Demographics Maps module for TerraScout AI.
Uses free public APIs (REST Countries, World Bank) and curated datasets
to visualize world population, megacities, density, urbanization and more.
All data sources are free — no API key required.
"""

import io
import math
import logging
import streamlit as st
import requests
import pandas as pd
from html import escape

import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════
REST_COUNTRIES_API = "https://restcountries.com/v3.1/all"
WORLD_BANK_API = "https://api.worldbank.org/v2/country/all/indicator"

# ═══════════════════════════════════════════
# COLOR SCALES
# ═══════════════════════════════════════════
POP_COLORS = {
    "tiny": "#3b82f6",       # < 1M
    "small": "#06b6d4",      # 1M - 10M
    "medium": "#10b981",     # 10M - 50M
    "large": "#f59e0b",      # 50M - 100M
    "huge": "#f97316",       # 100M - 500M
    "giant": "#ef4444",      # 500M - 1B
    "mega": "#dc2626",       # > 1B
}

DENSITY_COLORS = {
    "sparse": "#3b82f6",     # < 25/km2
    "low": "#06b6d4",        # 25 - 100
    "moderate": "#10b981",   # 100 - 300
    "high": "#f59e0b",       # 300 - 1000
    "very_high": "#f97316",  # 1000 - 5000
    "extreme": "#ef4444",    # > 5000
}

GROWTH_COLORS = {
    "shrinking": "#3b82f6",  # < 0%
    "stagnant": "#06b6d4",   # 0 - 0.5%
    "slow": "#10b981",       # 0.5 - 1%
    "moderate": "#f59e0b",   # 1 - 2%
    "fast": "#f97316",       # 2 - 3%
    "extreme": "#ef4444",    # > 3%
}


def _pop_color(pop: float) -> str:
    if pop < 1_000_000:
        return POP_COLORS["tiny"]
    elif pop < 10_000_000:
        return POP_COLORS["small"]
    elif pop < 50_000_000:
        return POP_COLORS["medium"]
    elif pop < 100_000_000:
        return POP_COLORS["large"]
    elif pop < 500_000_000:
        return POP_COLORS["huge"]
    elif pop < 1_000_000_000:
        return POP_COLORS["giant"]
    return POP_COLORS["mega"]


def _pop_radius(pop: float) -> float:
    if pop < 1_000_000:
        return 3
    elif pop < 10_000_000:
        return 5
    elif pop < 50_000_000:
        return 8
    elif pop < 100_000_000:
        return 11
    elif pop < 500_000_000:
        return 15
    elif pop < 1_000_000_000:
        return 19
    return 23


def _density_color(d: float) -> str:
    if d < 25:
        return DENSITY_COLORS["sparse"]
    elif d < 100:
        return DENSITY_COLORS["low"]
    elif d < 300:
        return DENSITY_COLORS["moderate"]
    elif d < 1000:
        return DENSITY_COLORS["high"]
    elif d < 5000:
        return DENSITY_COLORS["very_high"]
    return DENSITY_COLORS["extreme"]


def _growth_color(g: float) -> str:
    if g < 0:
        return GROWTH_COLORS["shrinking"]
    elif g < 0.5:
        return GROWTH_COLORS["stagnant"]
    elif g < 1.0:
        return GROWTH_COLORS["slow"]
    elif g < 2.0:
        return GROWTH_COLORS["moderate"]
    elif g < 3.0:
        return GROWTH_COLORS["fast"]
    return GROWTH_COLORS["extreme"]


def _fmt_pop(n: float) -> str:
    """Format population number to human-readable string."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return f"{n:.0f}"


def _dark_map(location=None, zoom=2):
    """Create a folium map with dark tiles."""
    import folium
    loc = location or [20, 0]
    m = folium.Map(location=loc, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)
    return m


def _dark_chart(figsize=(8, 4)):
    """Create a matplotlib figure with dark theme."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
    ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


def _show_map(m, height=500):
    """Render a folium map."""
    components.html(m._repr_html_(), height=height)


# ═══════════════════════════════════════════
# API FETCHERS
# ═══════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_rest_countries() -> list:
    """Fetch all countries from REST Countries API."""
    try:
        resp = requests.get(
            REST_COUNTRIES_API,
            params={"fields": "name,population,area,latlng,region,subregion,flags,cca3,capital"},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"REST Countries API error: {e}")
        return []


@st.cache_data(ttl=3600)
def fetch_world_bank_indicator(indicator: str, date: str = "2022") -> list:
    """Fetch a World Bank indicator for all countries."""
    results = []
    page = 1
    while True:
        try:
            url = f"{WORLD_BANK_API}/{indicator}"
            resp = requests.get(url, params={
                "format": "json",
                "per_page": 300,
                "page": page,
                "date": date,
            }, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if len(data) < 2 or not data[1]:
                break
            results.extend(data[1])
            total_pages = data[0].get("pages", 1)
            if page >= total_pages:
                break
            page += 1
        except Exception as e:
            logger.error(f"World Bank API error: {e}")
            break
    return results


# ═══════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════

MEGACITIES = [
    {"city": "Tokyo", "country": "Japan", "pop": 37_400_000, "lat": 35.6762, "lon": 139.6503, "area_km2": 2191, "growth": 0.2},
    {"city": "Delhi", "country": "India", "pop": 32_941_000, "lat": 28.7041, "lon": 77.1025, "area_km2": 2202, "growth": 2.8},
    {"city": "Shanghai", "country": "China", "pop": 29_210_000, "lat": 31.2304, "lon": 121.4737, "area_km2": 6341, "growth": 1.2},
    {"city": "Sao Paulo", "country": "Brazil", "pop": 22_430_000, "lat": -23.5505, "lon": -46.6333, "area_km2": 7947, "growth": 0.7},
    {"city": "Mexico City", "country": "Mexico", "pop": 22_085_000, "lat": 19.4326, "lon": -99.1332, "area_km2": 2530, "growth": 0.8},
    {"city": "Dhaka", "country": "Bangladesh", "pop": 23_210_000, "lat": 23.8103, "lon": 90.4125, "area_km2": 338, "growth": 3.2},
    {"city": "Cairo", "country": "Egypt", "pop": 22_183_000, "lat": 30.0444, "lon": 31.2357, "area_km2": 2734, "growth": 1.8},
    {"city": "Beijing", "country": "China", "pop": 21_540_000, "lat": 39.9042, "lon": 116.4074, "area_km2": 4144, "growth": 0.8},
    {"city": "Mumbai", "country": "India", "pop": 21_297_000, "lat": 19.0760, "lon": 72.8777, "area_km2": 944, "growth": 1.3},
    {"city": "Osaka", "country": "Japan", "pop": 19_165_000, "lat": 34.6937, "lon": 135.5023, "area_km2": 3213, "growth": -0.2},
    {"city": "Chongqing", "country": "China", "pop": 18_750_000, "lat": 29.4316, "lon": 106.9123, "area_km2": 5473, "growth": 1.5},
    {"city": "Karachi", "country": "Pakistan", "pop": 16_840_000, "lat": 24.8607, "lon": 67.0011, "area_km2": 3780, "growth": 2.3},
    {"city": "Istanbul", "country": "Turkey", "pop": 16_047_000, "lat": 41.0082, "lon": 28.9784, "area_km2": 5461, "growth": 1.2},
    {"city": "Kinshasa", "country": "DR Congo", "pop": 17_071_000, "lat": -4.4419, "lon": 15.2663, "area_km2": 9965, "growth": 4.1},
    {"city": "Lagos", "country": "Nigeria", "pop": 15_946_000, "lat": 6.5244, "lon": 3.3792, "area_km2": 2706, "growth": 3.3},
    {"city": "Buenos Aires", "country": "Argentina", "pop": 15_490_000, "lat": -34.6037, "lon": -58.3816, "area_km2": 4758, "growth": 0.6},
    {"city": "Kolkata", "country": "India", "pop": 15_333_000, "lat": 22.5726, "lon": 88.3639, "area_km2": 1887, "growth": 0.8},
    {"city": "Manila", "country": "Philippines", "pop": 14_406_000, "lat": 14.5995, "lon": 120.9842, "area_km2": 1580, "growth": 1.4},
    {"city": "Guangzhou", "country": "China", "pop": 14_284_000, "lat": 23.1291, "lon": 113.2644, "area_km2": 3843, "growth": 2.0},
    {"city": "Tianjin", "country": "China", "pop": 13_866_000, "lat": 39.3434, "lon": 117.3616, "area_km2": 4037, "growth": 1.0},
    {"city": "Lahore", "country": "Pakistan", "pop": 13_542_000, "lat": 31.5204, "lon": 74.3587, "area_km2": 1772, "growth": 2.7},
    {"city": "Bangalore", "country": "India", "pop": 13_193_000, "lat": 12.9716, "lon": 77.5946, "area_km2": 1166, "growth": 2.9},
    {"city": "Rio de Janeiro", "country": "Brazil", "pop": 13_544_000, "lat": -22.9068, "lon": -43.1729, "area_km2": 2271, "growth": 0.4},
    {"city": "Shenzhen", "country": "China", "pop": 13_438_000, "lat": 22.5431, "lon": 114.0579, "area_km2": 1997, "growth": 2.5},
    {"city": "Moscow", "country": "Russia", "pop": 12_680_000, "lat": 55.7558, "lon": 37.6173, "area_km2": 5891, "growth": 0.3},
    {"city": "Chennai", "country": "India", "pop": 11_503_000, "lat": 13.0827, "lon": 80.2707, "area_km2": 1189, "growth": 1.5},
    {"city": "Bogota", "country": "Colombia", "pop": 11_344_000, "lat": 4.7110, "lon": -74.0721, "area_km2": 1775, "growth": 1.2},
    {"city": "Paris", "country": "France", "pop": 11_276_000, "lat": 48.8566, "lon": 2.3522, "area_km2": 2845, "growth": 0.4},
    {"city": "Jakarta", "country": "Indonesia", "pop": 11_249_000, "lat": -6.2088, "lon": 106.8456, "area_km2": 3540, "growth": 1.0},
    {"city": "Lima", "country": "Peru", "pop": 11_044_000, "lat": -12.0464, "lon": -77.0428, "area_km2": 2672, "growth": 1.5},
    {"city": "Bangkok", "country": "Thailand", "pop": 11_066_000, "lat": 13.7563, "lon": 100.5018, "area_km2": 3043, "growth": 0.8},
    {"city": "Hyderabad", "country": "India", "pop": 10_534_000, "lat": 17.3850, "lon": 78.4867, "area_km2": 1595, "growth": 2.3},
    {"city": "Seoul", "country": "South Korea", "pop": 9_975_000, "lat": 37.5665, "lon": 126.9780, "area_km2": 605, "growth": -0.3},
    {"city": "Nagoya", "country": "Japan", "pop": 9_571_000, "lat": 35.1815, "lon": 136.9066, "area_km2": 3885, "growth": -0.1},
    {"city": "Wuhan", "country": "China", "pop": 12_326_000, "lat": 30.5928, "lon": 114.3055, "area_km2": 3279, "growth": 1.2},
    {"city": "Chengdu", "country": "China", "pop": 11_309_000, "lat": 30.5728, "lon": 104.0668, "area_km2": 3681, "growth": 1.8},
    {"city": "Luanda", "country": "Angola", "pop": 9_292_000, "lat": -8.8390, "lon": 13.2894, "area_km2": 2257, "growth": 4.0},
    {"city": "Ahmedabad", "country": "India", "pop": 8_650_000, "lat": 23.0225, "lon": 72.5714, "area_km2": 505, "growth": 2.1},
    {"city": "Kuala Lumpur", "country": "Malaysia", "pop": 8_622_000, "lat": 3.1390, "lon": 101.6869, "area_km2": 2243, "growth": 1.9},
    {"city": "Hangzhou", "country": "China", "pop": 8_700_000, "lat": 30.2741, "lon": 120.1551, "area_km2": 3068, "growth": 2.0},
    {"city": "Riyadh", "country": "Saudi Arabia", "pop": 7_676_000, "lat": 24.7136, "lon": 46.6753, "area_km2": 3115, "growth": 2.5},
    {"city": "London", "country": "United Kingdom", "pop": 9_541_000, "lat": 51.5074, "lon": -0.1278, "area_km2": 1572, "growth": 0.5},
    {"city": "New York", "country": "United States", "pop": 18_819_000, "lat": 40.7128, "lon": -74.0060, "area_km2": 11875, "growth": 0.2},
    {"city": "Los Angeles", "country": "United States", "pop": 12_488_000, "lat": 34.0522, "lon": -118.2437, "area_km2": 6299, "growth": 0.3},
    {"city": "Ho Chi Minh City", "country": "Vietnam", "pop": 9_321_000, "lat": 10.8231, "lon": 106.6297, "area_km2": 2061, "growth": 2.0},
    {"city": "Dar es Salaam", "country": "Tanzania", "pop": 7_405_000, "lat": -6.7924, "lon": 39.2083, "area_km2": 1631, "growth": 4.6},
    {"city": "Johannesburg", "country": "South Africa", "pop": 6_065_000, "lat": -26.2041, "lon": 28.0473, "area_km2": 1645, "growth": 1.5},
    {"city": "Nairobi", "country": "Kenya", "pop": 5_325_000, "lat": -1.2921, "lon": 36.8219, "area_km2": 696, "growth": 3.8},
    {"city": "Addis Ababa", "country": "Ethiopia", "pop": 5_461_000, "lat": 9.0250, "lon": 38.7469, "area_km2": 527, "growth": 3.6},
    {"city": "Singapore", "country": "Singapore", "pop": 5_917_000, "lat": 1.3521, "lon": 103.8198, "area_km2": 733, "growth": 0.8},
]

HISTORICAL_POPULATION = [
    {"year": -10000, "pop": 5_000_000, "label": "Neolithic Revolution"},
    {"year": -5000, "pop": 15_000_000, "label": "Early Agriculture"},
    {"year": -3000, "pop": 30_000_000, "label": "Bronze Age Civilizations"},
    {"year": -1000, "pop": 72_000_000, "label": "Iron Age"},
    {"year": 1, "pop": 190_000_000, "label": "Roman Empire peak era"},
    {"year": 200, "pop": 257_000_000, "label": "Han Dynasty peak"},
    {"year": 500, "pop": 210_000_000, "label": "Post-Roman decline"},
    {"year": 1000, "pop": 295_000_000, "label": "Medieval expansion"},
    {"year": 1200, "pop": 393_000_000, "label": "Mongol Empire era"},
    {"year": 1340, "pop": 443_000_000, "label": "Pre-Black Death peak"},
    {"year": 1400, "pop": 374_000_000, "label": "Post-Black Death nadir"},
    {"year": 1500, "pop": 461_000_000, "label": "Age of Exploration"},
    {"year": 1600, "pop": 554_000_000, "label": "Colonial era begins"},
    {"year": 1700, "pop": 603_000_000, "label": "Scientific Revolution"},
    {"year": 1804, "pop": 1_000_000_000, "label": "1 Billion milestone"},
    {"year": 1850, "pop": 1_260_000_000, "label": "Industrial Revolution peak"},
    {"year": 1900, "pop": 1_650_000_000, "label": "Turn of 20th century"},
    {"year": 1927, "pop": 2_000_000_000, "label": "2 Billion milestone"},
    {"year": 1950, "pop": 2_500_000_000, "label": "Post-WWII baby boom"},
    {"year": 1960, "pop": 3_034_000_000, "label": "3 Billion milestone"},
    {"year": 1974, "pop": 4_000_000_000, "label": "4 Billion milestone"},
    {"year": 1987, "pop": 5_000_000_000, "label": "5 Billion milestone"},
    {"year": 1999, "pop": 6_000_000_000, "label": "6 Billion milestone"},
    {"year": 2011, "pop": 7_000_000_000, "label": "7 Billion milestone"},
    {"year": 2022, "pop": 8_000_000_000, "label": "8 Billion milestone"},
    {"year": 2024, "pop": 8_160_000_000, "label": "Present day (est.)"},
]

AGE_DEMOGRAPHICS = [
    {"country": "Niger", "median_age": 15.2, "lat": 17.6078, "lon": 8.0817, "youth_pct": 50.0, "elderly_pct": 2.5, "category": "Very Young"},
    {"country": "Mali", "median_age": 16.0, "lat": 17.5707, "lon": -3.9962, "youth_pct": 48.0, "elderly_pct": 2.7, "category": "Very Young"},
    {"country": "Chad", "median_age": 16.1, "lat": 15.4542, "lon": 18.7322, "youth_pct": 47.5, "elderly_pct": 2.6, "category": "Very Young"},
    {"country": "Uganda", "median_age": 16.7, "lat": 1.3733, "lon": 32.2903, "youth_pct": 46.5, "elderly_pct": 2.1, "category": "Very Young"},
    {"country": "Angola", "median_age": 16.7, "lat": -11.2027, "lon": 17.8739, "youth_pct": 46.0, "elderly_pct": 2.3, "category": "Very Young"},
    {"country": "Somalia", "median_age": 16.7, "lat": 5.1521, "lon": 46.1996, "youth_pct": 46.3, "elderly_pct": 2.8, "category": "Very Young"},
    {"country": "DR Congo", "median_age": 17.0, "lat": -4.0383, "lon": 21.7587, "youth_pct": 46.0, "elderly_pct": 3.0, "category": "Very Young"},
    {"country": "Afghanistan", "median_age": 17.6, "lat": 33.9391, "lon": 67.7100, "youth_pct": 43.0, "elderly_pct": 2.6, "category": "Very Young"},
    {"country": "Nigeria", "median_age": 18.1, "lat": 9.0820, "lon": 8.6753, "youth_pct": 43.0, "elderly_pct": 2.7, "category": "Young"},
    {"country": "Ethiopia", "median_age": 19.5, "lat": 9.1450, "lon": 40.4897, "youth_pct": 40.0, "elderly_pct": 3.3, "category": "Young"},
    {"country": "Kenya", "median_age": 20.0, "lat": -0.0236, "lon": 37.9062, "youth_pct": 39.0, "elderly_pct": 2.8, "category": "Young"},
    {"country": "Philippines", "median_age": 25.7, "lat": 12.8797, "lon": 121.7740, "youth_pct": 30.0, "elderly_pct": 5.5, "category": "Transitional"},
    {"country": "India", "median_age": 28.4, "lat": 20.5937, "lon": 78.9629, "youth_pct": 26.0, "elderly_pct": 6.8, "category": "Transitional"},
    {"country": "Mexico", "median_age": 29.3, "lat": 23.6345, "lon": -102.5528, "youth_pct": 25.0, "elderly_pct": 7.6, "category": "Transitional"},
    {"country": "Brazil", "median_age": 33.5, "lat": -14.2350, "lon": -51.9253, "youth_pct": 21.0, "elderly_pct": 9.6, "category": "Mature"},
    {"country": "Indonesia", "median_age": 30.2, "lat": -0.7893, "lon": 113.9213, "youth_pct": 24.0, "elderly_pct": 6.5, "category": "Transitional"},
    {"country": "China", "median_age": 39.0, "lat": 35.8617, "lon": 104.1954, "youth_pct": 17.0, "elderly_pct": 13.5, "category": "Aging"},
    {"country": "United States", "median_age": 38.5, "lat": 37.0902, "lon": -95.7129, "youth_pct": 18.0, "elderly_pct": 16.9, "category": "Aging"},
    {"country": "Russia", "median_age": 39.6, "lat": 61.5240, "lon": 105.3188, "youth_pct": 17.0, "elderly_pct": 15.5, "category": "Aging"},
    {"country": "United Kingdom", "median_age": 40.5, "lat": 55.3781, "lon": -3.4360, "youth_pct": 17.5, "elderly_pct": 18.7, "category": "Aging"},
    {"country": "France", "median_age": 42.0, "lat": 46.2276, "lon": 2.2137, "youth_pct": 17.5, "elderly_pct": 21.0, "category": "Old"},
    {"country": "South Korea", "median_age": 44.0, "lat": 35.9078, "lon": 127.7669, "youth_pct": 12.0, "elderly_pct": 17.5, "category": "Very Old"},
    {"country": "Germany", "median_age": 45.7, "lat": 51.1657, "lon": 10.4515, "youth_pct": 14.0, "elderly_pct": 22.0, "category": "Very Old"},
    {"country": "Spain", "median_age": 45.5, "lat": 40.4637, "lon": -3.7492, "youth_pct": 14.0, "elderly_pct": 20.0, "category": "Very Old"},
    {"country": "Italy", "median_age": 47.3, "lat": 41.8719, "lon": 12.5674, "youth_pct": 13.0, "elderly_pct": 23.5, "category": "Very Old"},
    {"country": "Portugal", "median_age": 46.2, "lat": 39.3999, "lon": -8.2245, "youth_pct": 13.5, "elderly_pct": 23.0, "category": "Very Old"},
    {"country": "Greece", "median_age": 45.6, "lat": 39.0742, "lon": 21.8243, "youth_pct": 14.0, "elderly_pct": 22.5, "category": "Very Old"},
    {"country": "Japan", "median_age": 48.4, "lat": 36.2048, "lon": 138.2529, "youth_pct": 12.0, "elderly_pct": 29.0, "category": "Oldest"},
    {"country": "Monaco", "median_age": 55.4, "lat": 43.7384, "lon": 7.4246, "youth_pct": 10.0, "elderly_pct": 35.0, "category": "Oldest"},
]

CROWDED_PLACES = [
    {"name": "Dhaka", "type": "City", "country": "Bangladesh", "lat": 23.8103, "lon": 90.4125, "density": 47_500, "pop": 23_210_000, "area_km2": 306, "note": "Most crowded major city in the world"},
    {"name": "Manila", "type": "City", "country": "Philippines", "lat": 14.5995, "lon": 120.9842, "density": 46_178, "pop": 1_846_500, "area_km2": 42.88, "note": "City proper is one of the densest on Earth"},
    {"name": "Monaco", "type": "Country", "country": "Monaco", "lat": 43.7384, "lon": 7.4246, "density": 26_337, "pop": 39_511, "area_km2": 2.02, "note": "Densest sovereign nation on Earth"},
    {"name": "Singapore", "type": "City-State", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "density": 8_358, "pop": 5_917_000, "area_km2": 733, "note": "City-state with no rural hinterland"},
    {"name": "Hong Kong", "type": "SAR", "country": "China", "lat": 22.3193, "lon": 114.1694, "density": 6_801, "pop": 7_482_500, "area_km2": 1106, "note": "Mongkok is world's densest neighborhood"},
    {"name": "Macau", "type": "SAR", "country": "China", "lat": 22.1987, "lon": 113.5439, "density": 21_158, "pop": 695_168, "area_km2": 32.9, "note": "Second-densest territory globally"},
    {"name": "Gaza Strip", "type": "Territory", "country": "Palestine", "lat": 31.3547, "lon": 34.3088, "density": 5_357, "pop": 2_048_000, "area_km2": 365, "note": "Among the densest conflict zones"},
    {"name": "Kowloon Walled City (hist.)", "type": "Neighborhood", "country": "China", "lat": 22.3322, "lon": 114.1874, "density": 1_255_000, "pop": 33_000, "area_km2": 0.026, "note": "Demolished 1994 — densest place ever at 1.26M/km2"},
    {"name": "Male", "type": "City", "country": "Maldives", "lat": 4.1755, "lon": 73.5093, "density": 65_201, "pop": 252_768, "area_km2": 8.30, "note": "One of the densest island capitals"},
    {"name": "Bahrain", "type": "Country", "country": "Bahrain", "lat": 26.0667, "lon": 50.5577, "density": 2_239, "pop": 1_501_635, "area_km2": 780, "note": "Densest island nation by population"},
    {"name": "Vatican City", "type": "Country", "country": "Vatican City", "lat": 41.9029, "lon": 12.4534, "density": 1_818, "pop": 800, "area_km2": 0.44, "note": "Smallest sovereign state by area"},
    {"name": "Kolkata", "type": "City", "country": "India", "lat": 22.5726, "lon": 88.3639, "density": 24_252, "pop": 4_496_700, "area_km2": 205, "note": "Highest density among Indian megacities"},
    {"name": "Mumbai", "type": "City", "country": "India", "lat": 19.0760, "lon": 72.8777, "density": 20_694, "pop": 12_478_400, "area_km2": 603, "note": "India's financial capital, extremely dense"},
    {"name": "Paris", "type": "City", "country": "France", "lat": 48.8566, "lon": 2.3522, "density": 20_382, "pop": 2_145_906, "area_km2": 105, "note": "Densest major European city proper"},
    {"name": "Mogadishu", "type": "City", "country": "Somalia", "lat": 2.0469, "lon": 45.3182, "density": 18_900, "pop": 2_587_200, "area_km2": 137, "note": "One of Africa's densest cities"},
    {"name": "Barcelona", "type": "City", "country": "Spain", "lat": 41.3874, "lon": 2.1686, "density": 16_149, "pop": 1_636_762, "area_km2": 101, "note": "Densest major city in Europe after Paris"},
    {"name": "Kathmandu", "type": "City", "country": "Nepal", "lat": 27.7172, "lon": 85.3240, "density": 20_288, "pop": 1_003_285, "area_km2": 49.45, "note": "Dense Himalayan capital valley"},
    {"name": "Lagos Island", "type": "Neighborhood", "country": "Nigeria", "lat": 6.4541, "lon": 3.4084, "density": 79_100, "pop": 859_849, "area_km2": 8.7, "note": "Densest district of Africa's largest city"},
    {"name": "Karachi", "type": "City", "country": "Pakistan", "lat": 24.8607, "lon": 67.0011, "density": 14_000, "pop": 16_840_000, "area_km2": 3780, "note": "Pakistan's largest and densest city"},
    {"name": "Nairobi", "type": "City", "country": "Kenya", "lat": -1.2921, "lon": 36.8219, "density": 6_266, "pop": 4_397_073, "area_km2": 696, "note": "East Africa's most crowded capital"},
]

DEPOPULATING_REGIONS = [
    {"name": "Detroit", "country": "United States", "lat": 42.3314, "lon": -83.0458, "peak_pop": 1_849_568, "current_pop": 639_111, "peak_year": 1950, "decline_pct": -65.4, "note": "Deindustrialization: auto industry decline"},
    {"name": "St. Louis", "country": "United States", "lat": 38.6270, "lon": -90.1994, "peak_pop": 856_796, "current_pop": 301_578, "peak_year": 1950, "decline_pct": -64.8, "note": "Suburban flight and job loss"},
    {"name": "Cleveland", "country": "United States", "lat": 41.4993, "lon": -81.6944, "peak_pop": 914_808, "current_pop": 372_624, "peak_year": 1950, "decline_pct": -59.3, "note": "Rust Belt decline, steel industry collapse"},
    {"name": "Baltimore", "country": "United States", "lat": 39.2904, "lon": -76.6122, "peak_pop": 949_708, "current_pop": 585_708, "peak_year": 1950, "decline_pct": -38.3, "note": "Urban-suburban migration"},
    {"name": "Leipzig", "country": "Germany", "lat": 51.3397, "lon": 12.3731, "peak_pop": 718_217, "current_pop": 616_093, "peak_year": 1933, "decline_pct": -14.2, "note": "Post-reunification East German decline (recovering)"},
    {"name": "Halle (Saale)", "country": "Germany", "lat": 51.4969, "lon": 11.9688, "peak_pop": 333_769, "current_pop": 242_083, "peak_year": 1989, "decline_pct": -27.5, "note": "East German industrial decline"},
    {"name": "Turin", "country": "Italy", "lat": 45.0703, "lon": 7.6869, "peak_pop": 1_167_968, "current_pop": 848_885, "peak_year": 1971, "decline_pct": -27.3, "note": "FIAT restructuring, Southern Italian return migration"},
    {"name": "Genoa", "country": "Italy", "lat": 44.4056, "lon": 8.9463, "peak_pop": 848_121, "current_pop": 566_410, "peak_year": 1971, "decline_pct": -33.2, "note": "Industrial port decline, aging population"},
    {"name": "Venice", "country": "Italy", "lat": 45.4408, "lon": 12.3155, "peak_pop": 174_808, "current_pop": 50_000, "peak_year": 1951, "decline_pct": -71.4, "note": "Tourism overtakes residential life (historic center)"},
    {"name": "Liverpool", "country": "United Kingdom", "lat": 53.4084, "lon": -2.9916, "peak_pop": 846_101, "current_pop": 486_100, "peak_year": 1931, "decline_pct": -42.5, "note": "Port/maritime industry decline (partially recovering)"},
    {"name": "Murmansk", "country": "Russia", "lat": 68.9585, "lon": 33.0827, "peak_pop": 468_000, "current_pop": 270_000, "peak_year": 1991, "decline_pct": -42.3, "note": "Post-Soviet Arctic exodus"},
    {"name": "Norilsk", "country": "Russia", "lat": 69.3535, "lon": 88.1892, "peak_pop": 207_000, "current_pop": 175_000, "peak_year": 1993, "decline_pct": -15.5, "note": "Harsh Arctic mining city, post-Soviet decline"},
    {"name": "Vorkuta", "country": "Russia", "lat": 67.4966, "lon": 64.0602, "peak_pop": 117_000, "current_pop": 54_000, "peak_year": 1991, "decline_pct": -53.8, "note": "Former gulag coal town, extreme depopulation"},
    {"name": "Nagasaki", "country": "Japan", "lat": 32.7503, "lon": 129.8777, "peak_pop": 449_382, "current_pop": 401_179, "peak_year": 1975, "decline_pct": -10.7, "note": "Japan's rural depopulation, aging"},
    {"name": "Akita", "country": "Japan", "lat": 39.7200, "lon": 140.1025, "peak_pop": 336_415, "current_pop": 299_000, "peak_year": 2000, "decline_pct": -11.1, "note": "Fastest-shrinking prefecture in Japan"},
    {"name": "Plovdiv", "country": "Bulgaria", "lat": 42.1354, "lon": 24.7453, "peak_pop": 380_000, "current_pop": 346_893, "peak_year": 1989, "decline_pct": -8.7, "note": "Post-communist emigration to Western Europe"},
    {"name": "Riga", "country": "Latvia", "lat": 56.9496, "lon": 24.1052, "peak_pop": 910_000, "current_pop": 614_618, "peak_year": 1990, "decline_pct": -32.5, "note": "EU emigration drain, low birth rate"},
    {"name": "Vilnius", "country": "Lithuania", "lat": 54.6872, "lon": 25.2797, "peak_pop": 583_000, "current_pop": 592_389, "peak_year": 1992, "decline_pct": 1.6, "note": "Recovered after deep 1990s decline; country shrinks"},
    {"name": "Athens", "country": "Greece", "lat": 37.9838, "lon": 23.7275, "peak_pop": 3_200_000, "current_pop": 3_040_000, "peak_year": 2001, "decline_pct": -5.0, "note": "Economic crisis brain drain"},
    {"name": "Donetsk", "country": "Ukraine", "lat": 48.0159, "lon": 37.8029, "peak_pop": 1_100_000, "current_pop": 905_364, "peak_year": 1991, "decline_pct": -17.7, "note": "Post-Soviet decline, conflict displacement"},
    {"name": "Flint", "country": "United States", "lat": 43.0125, "lon": -83.6875, "peak_pop": 196_940, "current_pop": 87_092, "peak_year": 1960, "decline_pct": -55.8, "note": "GM plant closures, water crisis"},
    {"name": "Gary", "country": "United States", "lat": 41.5934, "lon": -87.3465, "peak_pop": 178_320, "current_pop": 69_093, "peak_year": 1960, "decline_pct": -61.3, "note": "US Steel decline, extreme urban decay"},
    {"name": "Youngstown", "country": "United States", "lat": 41.0998, "lon": -80.6495, "peak_pop": 166_689, "current_pop": 60_068, "peak_year": 1930, "decline_pct": -64.0, "note": "Steel industry collapse"},
]

FUTURE_PROJECTIONS = [
    {"region": "World", "pop_2024": 8_160_000_000, "pop_2050": 9_700_000_000, "pop_2100": 10_400_000_000, "lat": 20.0, "lon": 0.0},
    {"region": "Sub-Saharan Africa", "pop_2024": 1_210_000_000, "pop_2050": 2_094_000_000, "pop_2100": 3_440_000_000, "lat": 0.0, "lon": 25.0},
    {"region": "South Asia", "pop_2024": 2_040_000_000, "pop_2050": 2_390_000_000, "pop_2100": 2_060_000_000, "lat": 23.0, "lon": 78.0},
    {"region": "East & SE Asia", "pop_2024": 2_370_000_000, "pop_2050": 2_290_000_000, "pop_2100": 1_700_000_000, "lat": 30.0, "lon": 115.0},
    {"region": "Europe", "pop_2024": 745_000_000, "pop_2050": 715_000_000, "pop_2100": 587_000_000, "lat": 50.0, "lon": 15.0},
    {"region": "Latin America & Caribbean", "pop_2024": 663_000_000, "pop_2050": 752_000_000, "pop_2100": 646_000_000, "lat": -10.0, "lon": -60.0},
    {"region": "Northern America", "pop_2024": 379_000_000, "pop_2050": 425_000_000, "pop_2100": 446_000_000, "lat": 45.0, "lon": -100.0},
    {"region": "Northern Africa & West Asia", "pop_2024": 719_000_000, "pop_2050": 955_000_000, "pop_2100": 1_127_000_000, "lat": 28.0, "lon": 30.0},
    {"region": "Oceania", "pop_2024": 46_000_000, "pop_2050": 57_000_000, "pop_2100": 69_000_000, "lat": -25.0, "lon": 135.0},
    {"region": "Central Asia", "pop_2024": 78_000_000, "pop_2050": 99_000_000, "pop_2100": 103_000_000, "lat": 42.0, "lon": 65.0},
]


# ═══════════════════════════════════════════
# MAP MODE RENDERERS
# ═══════════════════════════════════════════

def _render_world_population():
    """Mode 1: World Population by Country — choropleth with population circles."""
    import folium

    st.markdown("##### World Population by Country")
    st.markdown(
        '<p style="color:#8b97b0;">Population data from the REST Countries API. '
        'Circle size represents total population, color indicates population bracket.</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Fetching country data from REST Countries API..."):
        countries = fetch_rest_countries()

    if not countries:
        st.error("Could not fetch country data. Please try again later.")
        return

    rows = []
    for c in countries:
        name = c.get("name", {}).get("common", "Unknown")
        pop = c.get("population", 0)
        area = c.get("area", 0)
        latlng = c.get("latlng", [0, 0])
        region = c.get("region", "")
        subregion = c.get("subregion", "")
        capital = c.get("capital", [""])[0] if c.get("capital") else ""
        if pop > 0 and len(latlng) == 2:
            rows.append({
                "country": name, "population": pop, "area_km2": area,
                "lat": latlng[0], "lon": latlng[1], "region": region,
                "subregion": subregion, "capital": capital,
                "density": round(pop / area, 1) if area > 0 else 0,
            })

    df = pd.DataFrame(rows).sort_values("population", ascending=False)
    total_pop = df["population"].sum()
    total_countries = len(df)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("World Population", _fmt_pop(total_pop))
    with c2:
        st.metric("Countries", f"{total_countries}")
    with c3:
        st.metric("Largest", df.iloc[0]["country"] if len(df) > 0 else "-")
    with c4:
        avg_pop = total_pop / total_countries if total_countries > 0 else 0
        st.metric("Average", _fmt_pop(avg_pop))

    # Color legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#3b82f6; font-size:0.8rem;">\u25cf &lt;1M</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf 1-10M</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf 10-50M</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf 50-100M</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf 100-500M</span>
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf 500M-1B</span>
        <span style="color:#dc2626; font-size:0.8rem;">\u25cf &gt;1B</span>
    </div>
    """, unsafe_allow_html=True)

    # Map
    m = _dark_map()
    for _, row in df.iterrows():
        color = _pop_color(row["population"])
        radius = _pop_radius(row["population"])
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(str(row["country"]))}</strong><br/>'
            f'Population: {row["population"]:,}<br/>'
            f'<span style="font-size:0.8rem;">Area: {row["area_km2"]:,.0f} km\u00b2</span><br/>'
            f'<span style="font-size:0.8rem;">Density: {row["density"]:,.1f}/km\u00b2</span><br/>'
            f'<span style="font-size:0.8rem;">Capital: {escape(str(row["capital"]))}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f'{escape(str(row["country"]))}: {_fmt_pop(row["population"])}',
        ).add_to(m)

    _show_map(m)

    # Top 20 bar chart
    st.markdown("##### Top 20 Most Populous Countries")
    top20 = df.head(20)
    fig, ax = _dark_chart(figsize=(10, 5))
    bars = ax.barh(
        range(len(top20)),
        top20["population"].values / 1_000_000,
        color=[_pop_color(p) for p in top20["population"].values],
        edgecolor="#0a0e1a",
        alpha=0.85,
    )
    ax.set_yticks(range(len(top20)))
    ax.set_yticklabels([escape(str(n)) for n in top20["country"].values], color="#e8ecf4", fontsize=9)
    ax.set_xlabel("Population (millions)", color="#8b97b0", fontsize=10)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table + download
    with st.expander(f"Full Data Table ({len(df)} countries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Countries (CSV)",
        data=csv_buf.getvalue(),
        file_name="world_population.csv",
        mime="text/csv",
        key="pop_world_dl",
    )


def _render_megacities():
    """Mode 2: Megacities (10M+) — Top 50 megacities with population, growth rate, area."""
    import folium

    st.markdown("##### Megacities of the World (10M+ metro population)")
    st.markdown(
        '<p style="color:#8b97b0;">Curated data on the world\'s largest metropolitan areas. '
        'Circle size = population, color = annual growth rate.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(MEGACITIES)
    df["density"] = (df["pop"] / df["area_km2"]).round(0).astype(int)
    df = df.sort_values("pop", ascending=False).reset_index(drop=True)

    total_pop = df["pop"].sum()
    avg_growth = df["growth"].mean()
    n_cities = len(df)
    max_density_city = df.loc[df["density"].idxmax()]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Metro Pop", _fmt_pop(total_pop))
    with c2:
        st.metric("Cities Listed", f"{n_cities}")
    with c3:
        st.metric("Avg Growth", f"{avg_growth:.1f}%/yr")
    with c4:
        st.metric("Densest", f'{max_density_city["city"]}')

    # Color legend by growth rate
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#3b82f6; font-size:0.8rem;">\u25cf Shrinking (&lt;0%)</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf Slow (0-0.5%)</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf Moderate (0.5-1%)</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf Growing (1-2%)</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf Fast (2-3%)</span>
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf Boom (&gt;3%)</span>
    </div>
    """, unsafe_allow_html=True)

    m = _dark_map()
    for _, row in df.iterrows():
        color = _growth_color(row["growth"])
        radius = max(4, math.sqrt(row["pop"] / 1_000_000) * 2)
        popup_html = (
            f'<div style="max-width:240px;">'
            f'<strong>{escape(str(row["city"]))}</strong>, {escape(str(row["country"]))}<br/>'
            f'Metro Pop: {row["pop"]:,}<br/>'
            f'<span style="font-size:0.8rem;">Area: {row["area_km2"]:,} km\u00b2</span><br/>'
            f'<span style="font-size:0.8rem;">Density: {row["density"]:,}/km\u00b2</span><br/>'
            f'<span style="font-size:0.8rem;">Growth: {row["growth"]:+.1f}%/yr</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.65,
            weight=1,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f'{escape(str(row["city"]))}: {_fmt_pop(row["pop"])}',
        ).add_to(m)

    _show_map(m)

    # Top 20 chart
    st.markdown("##### Top 20 Megacities by Population")
    top20 = df.head(20)
    fig, ax = _dark_chart(figsize=(10, 5))
    bars = ax.barh(
        range(len(top20)),
        top20["pop"].values / 1_000_000,
        color=[_growth_color(g) for g in top20["growth"].values],
        edgecolor="#0a0e1a",
        alpha=0.85,
    )
    ax.set_yticks(range(len(top20)))
    ax.set_yticklabels(top20["city"].values, color="#e8ecf4", fontsize=9)
    ax.set_xlabel("Metro Population (millions)", color="#8b97b0", fontsize=10)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    with st.expander(f"Full Data Table ({len(df)} cities)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Megacities (CSV)",
        data=csv_buf.getvalue(),
        file_name="megacities.csv",
        mime="text/csv",
        key="pop_mega_dl",
    )


def _render_population_density():
    """Mode 3: Population Density — Persons/km2 by country, color-coded world map."""
    import folium

    st.markdown("##### Population Density by Country")
    st.markdown(
        '<p style="color:#8b97b0;">Persons per km\u00b2 calculated from REST Countries data. '
        'Color intensity indicates density bracket.</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Fetching country data..."):
        countries = fetch_rest_countries()

    if not countries:
        st.error("Could not fetch country data. Please try again later.")
        return

    rows = []
    for c in countries:
        name = c.get("name", {}).get("common", "Unknown")
        pop = c.get("population", 0)
        area = c.get("area", 0)
        latlng = c.get("latlng", [0, 0])
        region = c.get("region", "")
        if pop > 0 and area > 0 and len(latlng) == 2:
            rows.append({
                "country": name, "population": pop, "area_km2": area,
                "density": round(pop / area, 1),
                "lat": latlng[0], "lon": latlng[1], "region": region,
            })

    df = pd.DataFrame(rows).sort_values("density", ascending=False)
    avg_density = df["density"].mean()
    median_density = df["density"].median()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Densest", f'{df.iloc[0]["country"]}' if len(df) > 0 else "-")
    with c2:
        st.metric("Highest Density", f'{df.iloc[0]["density"]:,.0f}/km\u00b2' if len(df) > 0 else "-")
    with c3:
        st.metric("Avg Density", f"{avg_density:,.1f}/km\u00b2")
    with c4:
        st.metric("Median Density", f"{median_density:,.1f}/km\u00b2")

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#3b82f6; font-size:0.8rem;">\u25cf &lt;25/km\u00b2</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf 25-100</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf 100-300</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf 300-1K</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf 1K-5K</span>
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf &gt;5K</span>
    </div>
    """, unsafe_allow_html=True)

    m = _dark_map()
    for _, row in df.iterrows():
        color = _density_color(row["density"])
        radius = min(18, max(3, math.log10(max(row["density"], 1)) * 4))
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(str(row["country"]))}</strong><br/>'
            f'Density: {row["density"]:,.1f}/km\u00b2<br/>'
            f'<span style="font-size:0.8rem;">Pop: {row["population"]:,}</span><br/>'
            f'<span style="font-size:0.8rem;">Area: {row["area_km2"]:,.0f} km\u00b2</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f'{escape(str(row["country"]))}: {row["density"]:,.1f}/km\u00b2',
        ).add_to(m)

    _show_map(m)

    # Top 25 density chart
    st.markdown("##### Top 25 Densest Countries")
    top25 = df.head(25)
    fig, ax = _dark_chart(figsize=(10, 6))
    ax.barh(
        range(len(top25)),
        top25["density"].values,
        color=[_density_color(d) for d in top25["density"].values],
        edgecolor="#0a0e1a",
        alpha=0.85,
    )
    ax.set_yticks(range(len(top25)))
    ax.set_yticklabels(top25["country"].values, color="#e8ecf4", fontsize=9)
    ax.set_xlabel("Persons per km\u00b2", color="#8b97b0", fontsize=10)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    with st.expander(f"Full Data Table ({len(df)} countries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Countries Density (CSV)",
        data=csv_buf.getvalue(),
        file_name="population_density.csv",
        mime="text/csv",
        key="pop_density_dl",
    )


def _render_urban_vs_rural():
    """Mode 4: Urban vs Rural — Urbanization rates by country (World Bank)."""
    import folium

    st.markdown("##### Urban vs Rural Population")
    st.markdown(
        '<p style="color:#8b97b0;">Urbanization rate (% of population living in cities) from the '
        'World Bank indicator SP.URB.TOTL.IN.ZS. Color indicates urbanization level.</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Fetching urbanization data from World Bank..."):
        wb_data = fetch_world_bank_indicator("SP.URB.TOTL.IN.ZS", "2022")

    if not wb_data:
        st.error("Could not fetch World Bank data. Please try again later.")
        return

    # Also fetch country coordinates from REST Countries
    with st.spinner("Fetching country coordinates..."):
        countries = fetch_rest_countries()

    coord_map = {}
    for c in countries:
        cca3 = c.get("cca3", "")
        latlng = c.get("latlng", [])
        if cca3 and len(latlng) == 2:
            coord_map[cca3] = {"lat": latlng[0], "lon": latlng[1]}

    # ISO3 mapping from World Bank countryiso3code
    rows = []
    for item in wb_data:
        if not item or not item.get("value"):
            continue
        iso3 = item.get("countryiso3code", "")
        name = item.get("country", {}).get("value", "Unknown")
        value = item["value"]
        coords = coord_map.get(iso3, {})
        if coords and value is not None:
            rows.append({
                "country": name, "iso3": iso3,
                "urban_pct": round(value, 1),
                "rural_pct": round(100 - value, 1),
                "lat": coords["lat"], "lon": coords["lon"],
            })

    if not rows:
        st.warning("No urbanization data available. Try again later.")
        return

    df = pd.DataFrame(rows).sort_values("urban_pct", ascending=False)
    # Remove aggregates (they have ISO codes like WLD, EAS, etc.)
    df = df[df["iso3"].str.len() == 3].reset_index(drop=True)
    # Filter out non-country aggregates by checking coordinates
    df = df[(df["lat"] != 0) | (df["lon"] != 0)].reset_index(drop=True)

    avg_urban = df["urban_pct"].mean()
    most_urban = df.iloc[0] if len(df) > 0 else None
    least_urban = df.iloc[-1] if len(df) > 0 else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries", f"{len(df)}")
    with c2:
        st.metric("Global Avg Urban", f"{avg_urban:.1f}%")
    with c3:
        st.metric("Most Urban", f'{most_urban["country"]}' if most_urban is not None else "-")
    with c4:
        st.metric("Most Rural", f'{least_urban["country"]}' if least_urban is not None else "-")

    urb_colors = {
        "very_low": "#ef4444",    # < 30%
        "low": "#f97316",         # 30-50%
        "medium": "#f59e0b",      # 50-70%
        "high": "#10b981",        # 70-85%
        "very_high": "#06b6d4",   # > 85%
    }

    def _urb_color(pct):
        if pct < 30:
            return urb_colors["very_low"]
        elif pct < 50:
            return urb_colors["low"]
        elif pct < 70:
            return urb_colors["medium"]
        elif pct < 85:
            return urb_colors["high"]
        return urb_colors["very_high"]

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf &lt;30% Urban</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf 30-50%</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf 50-70%</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf 70-85%</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf &gt;85%</span>
    </div>
    """, unsafe_allow_html=True)

    m = _dark_map()
    for _, row in df.iterrows():
        color = _urb_color(row["urban_pct"])
        radius = max(3, row["urban_pct"] / 10)
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(str(row["country"]))}</strong><br/>'
            f'Urban: {row["urban_pct"]:.1f}%<br/>'
            f'Rural: {row["rural_pct"]:.1f}%'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f'{escape(str(row["country"]))}: {row["urban_pct"]:.1f}% urban',
        ).add_to(m)

    _show_map(m)

    # Chart: Top 20 most urban + bottom 20 most rural
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### Top 20 Most Urban")
        top20 = df.head(20)
        fig, ax = _dark_chart(figsize=(6, 5))
        ax.barh(
            range(len(top20)),
            top20["urban_pct"].values,
            color=[_urb_color(v) for v in top20["urban_pct"].values],
            edgecolor="#0a0e1a", alpha=0.85,
        )
        ax.set_yticks(range(len(top20)))
        ax.set_yticklabels(top20["country"].values, color="#e8ecf4", fontsize=8)
        ax.set_xlabel("Urban %", color="#8b97b0", fontsize=10)
        ax.set_xlim(0, 105)
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_b:
        st.markdown("##### Top 20 Most Rural")
        bot20 = df.tail(20).sort_values("urban_pct")
        fig2, ax2 = _dark_chart(figsize=(6, 5))
        ax2.barh(
            range(len(bot20)),
            bot20["rural_pct"].values,
            color=[_urb_color(v) for v in bot20["urban_pct"].values],
            edgecolor="#0a0e1a", alpha=0.85,
        )
        ax2.set_yticks(range(len(bot20)))
        ax2.set_yticklabels(bot20["country"].values, color="#e8ecf4", fontsize=8)
        ax2.set_xlabel("Rural %", color="#8b97b0", fontsize=10)
        ax2.set_xlim(0, 105)
        ax2.invert_yaxis()
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    with st.expander(f"Full Data Table ({len(df)} countries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Countries Urbanization (CSV)",
        data=csv_buf.getvalue(),
        file_name="urbanization_rates.csv",
        mime="text/csv",
        key="pop_urban_dl",
    )


def _render_population_growth():
    """Mode 5: Population Growth Rate — Annual growth rates from World Bank."""
    import folium

    st.markdown("##### Population Growth Rate by Country")
    st.markdown(
        '<p style="color:#8b97b0;">Annual population growth rate (%) from World Bank indicator '
        'SP.POP.GROW. Color indicates growth bracket.</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Fetching growth rate data from World Bank..."):
        wb_data = fetch_world_bank_indicator("SP.POP.GROW", "2022")

    with st.spinner("Fetching country coordinates..."):
        countries = fetch_rest_countries()

    coord_map = {}
    for c in countries:
        cca3 = c.get("cca3", "")
        latlng = c.get("latlng", [])
        if cca3 and len(latlng) == 2:
            coord_map[cca3] = {"lat": latlng[0], "lon": latlng[1]}

    rows = []
    for item in wb_data:
        if not item or item.get("value") is None:
            continue
        iso3 = item.get("countryiso3code", "")
        name = item.get("country", {}).get("value", "Unknown")
        value = item["value"]
        coords = coord_map.get(iso3, {})
        if coords:
            rows.append({
                "country": name, "iso3": iso3,
                "growth_rate": round(value, 2),
                "lat": coords["lat"], "lon": coords["lon"],
            })

    if not rows:
        st.warning("No growth rate data available.")
        return

    df = pd.DataFrame(rows).sort_values("growth_rate", ascending=False)
    df = df[df["iso3"].str.len() == 3].reset_index(drop=True)
    df = df[(df["lat"] != 0) | (df["lon"] != 0)].reset_index(drop=True)

    n_growing = len(df[df["growth_rate"] > 0])
    n_shrinking = len(df[df["growth_rate"] < 0])
    avg_growth = df["growth_rate"].mean()
    fastest = df.iloc[0] if len(df) > 0 else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries", f"{len(df)}")
    with c2:
        st.metric("Growing", f"{n_growing}")
    with c3:
        st.metric("Shrinking", f"{n_shrinking}")
    with c4:
        st.metric("Fastest", f'{fastest["country"]} ({fastest["growth_rate"]:+.2f}%)' if fastest is not None else "-")

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#3b82f6; font-size:0.8rem;">\u25cf Shrinking (&lt;0%)</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf Stagnant (0-0.5%)</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf Slow (0.5-1%)</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf Moderate (1-2%)</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf Fast (2-3%)</span>
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf Extreme (&gt;3%)</span>
    </div>
    """, unsafe_allow_html=True)

    m = _dark_map()
    for _, row in df.iterrows():
        color = _growth_color(row["growth_rate"])
        radius = max(3, abs(row["growth_rate"]) * 3 + 2)
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(str(row["country"]))}</strong><br/>'
            f'Growth: {row["growth_rate"]:+.2f}%/yr'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f'{escape(str(row["country"]))}: {row["growth_rate"]:+.2f}%',
        ).add_to(m)

    _show_map(m)

    # Charts — fastest and slowest
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### Fastest Growing (Top 20)")
        top20 = df.head(20)
        fig, ax = _dark_chart(figsize=(6, 5))
        ax.barh(
            range(len(top20)),
            top20["growth_rate"].values,
            color=[_growth_color(g) for g in top20["growth_rate"].values],
            edgecolor="#0a0e1a", alpha=0.85,
        )
        ax.set_yticks(range(len(top20)))
        ax.set_yticklabels(top20["country"].values, color="#e8ecf4", fontsize=8)
        ax.set_xlabel("Annual Growth Rate (%)", color="#8b97b0", fontsize=10)
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_b:
        st.markdown("##### Fastest Shrinking (Bottom 20)")
        bot20 = df.tail(20).sort_values("growth_rate")
        fig2, ax2 = _dark_chart(figsize=(6, 5))
        ax2.barh(
            range(len(bot20)),
            bot20["growth_rate"].values,
            color=[_growth_color(g) for g in bot20["growth_rate"].values],
            edgecolor="#0a0e1a", alpha=0.85,
        )
        ax2.set_yticks(range(len(bot20)))
        ax2.set_yticklabels(bot20["country"].values, color="#e8ecf4", fontsize=8)
        ax2.set_xlabel("Annual Growth Rate (%)", color="#8b97b0", fontsize=10)
        ax2.invert_yaxis()
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    with st.expander(f"Full Data Table ({len(df)} countries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Countries Growth Rate (CSV)",
        data=csv_buf.getvalue(),
        file_name="population_growth_rate.csv",
        mime="text/csv",
        key="pop_growth_dl",
    )


def _render_historical_population():
    """Mode 6: Historical Population — World population milestones timeline."""
    st.markdown("##### Historical World Population")
    st.markdown(
        '<p style="color:#8b97b0;">Major milestones in world population growth from '
        'the Neolithic Revolution to the present. Data from UN, US Census Bureau, and academic estimates.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(HISTORICAL_POPULATION)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Current (est.)", "8.16 Billion")
    with c2:
        st.metric("1st Billion", "1804")
    with c3:
        st.metric("Doubling Time", "~47 years (6B to 8B)")
    with c4:
        st.metric("Data Points", f"{len(df)}")

    # Timeline chart
    st.markdown("##### Population Growth Timeline")
    fig, ax = _dark_chart(figsize=(12, 5))

    # Use post-1500 for main chart (pre-1500 values are tiny)
    modern = df[df["year"] >= 1500]
    ax.fill_between(
        modern["year"],
        modern["pop"] / 1_000_000_000,
        alpha=0.3,
        color="#06b6d4",
    )
    ax.plot(
        modern["year"],
        modern["pop"] / 1_000_000_000,
        color="#06b6d4",
        linewidth=2.5,
        marker="o",
        markersize=5,
        markerfacecolor="#e8ecf4",
        markeredgecolor="#06b6d4",
    )

    # Annotate billion milestones
    for _, row in modern.iterrows():
        if row["pop"] >= 1_000_000_000 and row["pop"] % 1_000_000_000 == 0:
            ax.annotate(
                f'{int(row["pop"] / 1_000_000_000)}B\n({int(row["year"])})',
                xy=(row["year"], row["pop"] / 1_000_000_000),
                fontsize=7,
                color="#e8ecf4",
                ha="center",
                va="bottom",
                textcoords="offset points",
                xytext=(0, 10),
            )

    ax.set_xlabel("Year", color="#8b97b0", fontsize=10)
    ax.set_ylabel("Population (Billions)", color="#e8ecf4", fontsize=10)
    ax.set_title("World Population Since 1500", color="#e8ecf4", fontsize=12, pad=10)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Full historical timeline (log scale)
    st.markdown("##### Full Historical Timeline (Log Scale)")
    fig2, ax2 = _dark_chart(figsize=(12, 5))
    ax2.semilogy(
        df["year"],
        df["pop"],
        color="#ec4899",
        linewidth=2,
        marker="o",
        markersize=5,
        markerfacecolor="#e8ecf4",
        markeredgecolor="#ec4899",
    )

    for _, row in df.iterrows():
        ax2.annotate(
            row["label"],
            xy=(row["year"], row["pop"]),
            fontsize=6,
            color="#8b97b0",
            rotation=35,
            ha="left",
            va="bottom",
            textcoords="offset points",
            xytext=(3, 5),
        )

    ax2.set_xlabel("Year", color="#8b97b0", fontsize=10)
    ax2.set_ylabel("Population (log scale)", color="#e8ecf4", fontsize=10)
    ax2.set_title("World Population: 10,000 BC to Present", color="#e8ecf4", fontsize=12, pad=10)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # Milestone table
    st.markdown("##### Population Milestones")
    display_df = df.copy()
    display_df["population"] = display_df["pop"].apply(lambda x: f"{x:,}")
    display_df = display_df[["year", "population", "label"]].rename(columns={
        "year": "Year", "population": "Population", "label": "Milestone / Era"
    })
    st.dataframe(display_df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Historical Population (CSV)",
        data=csv_buf.getvalue(),
        file_name="historical_population.csv",
        mime="text/csv",
        key="pop_hist_dl",
    )


def _render_age_demographics():
    """Mode 7: Age Demographics — Median age by country, youth bulge vs aging societies."""
    import folium

    st.markdown("##### Age Demographics: Youth Bulge vs Aging Societies")
    st.markdown(
        '<p style="color:#8b97b0;">Median age, youth percentage (under 15), and elderly percentage (65+) '
        'across countries. Data from CIA World Factbook and UN Population Division.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(AGE_DEMOGRAPHICS)
    df = df.sort_values("median_age").reset_index(drop=True)

    youngest = df.iloc[0]
    oldest = df.iloc[-1]
    avg_age = df["median_age"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Youngest Nation", f'{youngest["country"]} ({youngest["median_age"]:.1f})')
    with c2:
        st.metric("Oldest Nation", f'{oldest["country"]} ({oldest["median_age"]:.1f})')
    with c3:
        st.metric("Avg Median Age", f"{avg_age:.1f} years")
    with c4:
        st.metric("Countries", f"{len(df)}")

    age_colors = {
        "Very Young": "#ef4444",
        "Young": "#f97316",
        "Transitional": "#f59e0b",
        "Mature": "#10b981",
        "Aging": "#06b6d4",
        "Old": "#3b82f6",
        "Very Old": "#8b5cf6",
        "Oldest": "#ec4899",
    }

    st.markdown("""
    <div style="display:flex; gap:0.8rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf Very Young (&lt;17)</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf Young (17-20)</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf Transitional (20-33)</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf Mature (33-38)</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf Aging (38-42)</span>
        <span style="color:#8b5cf6; font-size:0.8rem;">\u25cf Very Old (42-48)</span>
        <span style="color:#ec4899; font-size:0.8rem;">\u25cf Oldest (&gt;48)</span>
    </div>
    """, unsafe_allow_html=True)

    m = _dark_map()
    for _, row in df.iterrows():
        color = age_colors.get(row["category"], "#8b97b0")
        radius = max(4, row["median_age"] / 4)
        popup_html = (
            f'<div style="max-width:240px;">'
            f'<strong>{escape(str(row["country"]))}</strong><br/>'
            f'Median Age: {row["median_age"]:.1f} yrs<br/>'
            f'<span style="font-size:0.8rem;">Youth (&lt;15): {row["youth_pct"]:.1f}%</span><br/>'
            f'<span style="font-size:0.8rem;">Elderly (65+): {row["elderly_pct"]:.1f}%</span><br/>'
            f'<span style="font-size:0.8rem;">Category: {escape(str(row["category"]))}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.65,
            weight=1,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f'{escape(str(row["country"]))}: {row["median_age"]:.1f} yrs',
        ).add_to(m)

    _show_map(m)

    # Chart — median age
    st.markdown("##### Median Age by Country")
    fig, ax = _dark_chart(figsize=(10, 7))
    ax.barh(
        range(len(df)),
        df["median_age"].values,
        color=[age_colors.get(c, "#8b97b0") for c in df["category"].values],
        edgecolor="#0a0e1a",
        alpha=0.85,
    )
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["country"].values, color="#e8ecf4", fontsize=8)
    ax.set_xlabel("Median Age (years)", color="#8b97b0", fontsize=10)
    ax.axvline(x=avg_age, color="#e8ecf4", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Youth vs Elderly scatter
    st.markdown("##### Youth vs Elderly Population")
    fig2, ax2 = _dark_chart(figsize=(8, 5))
    for _, row in df.iterrows():
        color = age_colors.get(row["category"], "#8b97b0")
        ax2.scatter(
            row["youth_pct"], row["elderly_pct"],
            color=color, s=60, alpha=0.8, edgecolors="#0a0e1a", linewidth=0.5,
        )
        ax2.annotate(
            row["country"], xy=(row["youth_pct"], row["elderly_pct"]),
            fontsize=6, color="#8b97b0", textcoords="offset points", xytext=(4, 4),
        )
    ax2.set_xlabel("Youth % (under 15)", color="#8b97b0", fontsize=10)
    ax2.set_ylabel("Elderly % (65+)", color="#8b97b0", fontsize=10)
    ax2.set_title("Youth Bulge vs Aging Society", color="#e8ecf4", fontsize=12, pad=10)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    with st.expander(f"Full Data Table ({len(df)} countries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Countries Age Demographics (CSV)",
        data=csv_buf.getvalue(),
        file_name="age_demographics.csv",
        mime="text/csv",
        key="pop_age_dl",
    )


def _render_crowded_places():
    """Mode 8: Most Crowded Places — Densest cities, neighborhoods, islands."""
    import folium

    st.markdown("##### Most Crowded Places on Earth")
    st.markdown(
        '<p style="color:#8b97b0;">The densest cities, territories, neighborhoods, and islands worldwide. '
        'Density measured as persons per km\u00b2. Curated from census and geographic data.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(CROWDED_PLACES)
    df = df.sort_values("density", ascending=False).reset_index(drop=True)

    max_density = df.iloc[0]
    avg_density = df["density"].mean()
    total_places = len(df)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Densest Place", f'{max_density["name"]}')
    with c2:
        st.metric("Peak Density", f'{max_density["density"]:,}/km\u00b2')
    with c3:
        st.metric("Avg Density", f'{avg_density:,.0f}/km\u00b2')
    with c4:
        st.metric("Places Listed", f"{total_places}")

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#10b981; font-size:0.8rem;">\u25cf &lt;10K/km\u00b2</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf 10-25K</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf 25-50K</span>
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf 50K+</span>
    </div>
    """, unsafe_allow_html=True)

    def _crowd_color(d):
        if d < 10_000:
            return "#10b981"
        elif d < 25_000:
            return "#f59e0b"
        elif d < 50_000:
            return "#f97316"
        return "#ef4444"

    m = _dark_map(zoom=2)
    for _, row in df.iterrows():
        color = _crowd_color(row["density"])
        radius = min(20, max(4, math.log10(max(row["density"], 1)) * 3))
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(str(row["name"]))}</strong> ({escape(str(row["type"]))})<br/>'
            f'{escape(str(row["country"]))}<br/>'
            f'Density: {row["density"]:,}/km\u00b2<br/>'
            f'<span style="font-size:0.8rem;">Pop: {row["pop"]:,}</span><br/>'
            f'<span style="font-size:0.8rem;">Area: {row["area_km2"]:,.2f} km\u00b2</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(str(row["note"]))}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f'{escape(str(row["name"]))}: {row["density"]:,}/km\u00b2',
        ).add_to(m)

    _show_map(m)

    # Chart
    st.markdown("##### Density Ranking")
    fig, ax = _dark_chart(figsize=(10, 7))
    ax.barh(
        range(len(df)),
        df["density"].values,
        color=[_crowd_color(d) for d in df["density"].values],
        edgecolor="#0a0e1a", alpha=0.85,
    )
    ax.set_yticks(range(len(df)))
    labels = [f'{row["name"]} ({row["type"]})' for _, row in df.iterrows()]
    ax.set_yticklabels(labels, color="#e8ecf4", fontsize=7)
    ax.set_xlabel("Persons per km\u00b2", color="#8b97b0", fontsize=10)
    ax.set_xscale("log")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    with st.expander(f"Full Data Table ({len(df)} places)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Crowded Places (CSV)",
        data=csv_buf.getvalue(),
        file_name="crowded_places.csv",
        mime="text/csv",
        key="pop_crowd_dl",
    )


def _render_depopulating_regions():
    """Mode 9: Depopulating Regions — Shrinking cities, rural exodus, ghost towns."""
    import folium

    st.markdown("##### Depopulating Regions & Shrinking Cities")
    st.markdown(
        '<p style="color:#8b97b0;">Cities and regions experiencing significant population decline. '
        'Causes include deindustrialization, conflict, economic collapse, and rural exodus. '
        'Curated from census data and academic studies.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(DEPOPULATING_REGIONS)
    df = df.sort_values("decline_pct").reset_index(drop=True)

    avg_decline = df["decline_pct"].mean()
    worst = df.iloc[0]
    total_lost = (df["peak_pop"] - df["current_pop"]).sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Cities Listed", f"{len(df)}")
    with c2:
        st.metric("Avg Decline", f"{avg_decline:.1f}%")
    with c3:
        st.metric("Worst Decline", f'{worst["name"]} ({worst["decline_pct"]:.1f}%)')
    with c4:
        st.metric("Total Pop Lost", _fmt_pop(total_lost))

    def _decline_color(d):
        if d > 0:
            return "#10b981"
        elif d > -15:
            return "#06b6d4"
        elif d > -30:
            return "#f59e0b"
        elif d > -50:
            return "#f97316"
        return "#ef4444"

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#10b981; font-size:0.8rem;">\u25cf Growing</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf Mild (&lt;15%)</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf Moderate (15-30%)</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf Severe (30-50%)</span>
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf Extreme (&gt;50%)</span>
    </div>
    """, unsafe_allow_html=True)

    m = _dark_map(zoom=2)
    for _, row in df.iterrows():
        color = _decline_color(row["decline_pct"])
        radius = max(4, abs(row["decline_pct"]) / 5)
        popup_html = (
            f'<div style="max-width:280px;">'
            f'<strong>{escape(str(row["name"]))}</strong>, {escape(str(row["country"]))}<br/>'
            f'Peak Pop: {row["peak_pop"]:,} ({row["peak_year"]})<br/>'
            f'Current Pop: {row["current_pop"]:,}<br/>'
            f'<span style="color:{color}; font-weight:bold;">Decline: {row["decline_pct"]:+.1f}%</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(str(row["note"]))}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.65,
            weight=1,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f'{escape(str(row["name"]))}: {row["decline_pct"]:+.1f}%',
        ).add_to(m)

    _show_map(m)

    # Before/after chart
    st.markdown("##### Peak vs Current Population")
    fig, ax = _dark_chart(figsize=(10, 7))
    y_pos = range(len(df))
    ax.barh(
        y_pos,
        df["peak_pop"].values / 1000,
        color="#2a3550",
        alpha=0.5,
        label="Peak",
        edgecolor="#0a0e1a",
    )
    ax.barh(
        y_pos,
        df["current_pop"].values / 1000,
        color=[_decline_color(d) for d in df["decline_pct"].values],
        alpha=0.85,
        label="Current",
        edgecolor="#0a0e1a",
    )
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(
        [f'{row["name"]} ({row["country"]})' for _, row in df.iterrows()],
        color="#e8ecf4", fontsize=7,
    )
    ax.set_xlabel("Population (thousands)", color="#8b97b0", fontsize=10)
    ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4", fontsize=8)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    with st.expander(f"Full Data Table ({len(df)} places)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} Depopulating Regions (CSV)",
        data=csv_buf.getvalue(),
        file_name="depopulating_regions.csv",
        mime="text/csv",
        key="pop_depop_dl",
    )


def _render_future_projections():
    """Mode 10: Future Projections — UN projected populations for 2050, 2100 by region."""
    import folium

    st.markdown("##### Future Population Projections (UN Medium Variant)")
    st.markdown(
        '<p style="color:#8b97b0;">Projected populations by world region for 2050 and 2100 based on '
        'UN Population Division medium-variant estimates. Highlights where growth and decline are expected.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(FUTURE_PROJECTIONS)
    df["change_2050"] = ((df["pop_2050"] - df["pop_2024"]) / df["pop_2024"] * 100).round(1)
    df["change_2100"] = ((df["pop_2100"] - df["pop_2024"]) / df["pop_2024"] * 100).round(1)

    world_row = df[df["region"] == "World"].iloc[0] if len(df[df["region"] == "World"]) > 0 else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("World 2024", _fmt_pop(world_row["pop_2024"]) if world_row is not None else "-")
    with c2:
        st.metric("World 2050 (proj.)", _fmt_pop(world_row["pop_2050"]) if world_row is not None else "-")
    with c3:
        st.metric("World 2100 (proj.)", _fmt_pop(world_row["pop_2100"]) if world_row is not None else "-")
    with c4:
        st.metric("Peak ~2086", "~10.4 Billion")

    def _proj_color(change):
        if change < -10:
            return "#3b82f6"
        elif change < 0:
            return "#06b6d4"
        elif change < 25:
            return "#10b981"
        elif change < 75:
            return "#f59e0b"
        elif change < 150:
            return "#f97316"
        return "#ef4444"

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#3b82f6; font-size:0.8rem;">\u25cf Major Decline (&lt;-10%)</span>
        <span style="color:#06b6d4; font-size:0.8rem;">\u25cf Slight Decline</span>
        <span style="color:#10b981; font-size:0.8rem;">\u25cf Slow Growth (&lt;25%)</span>
        <span style="color:#f59e0b; font-size:0.8rem;">\u25cf Moderate (25-75%)</span>
        <span style="color:#f97316; font-size:0.8rem;">\u25cf Fast (75-150%)</span>
        <span style="color:#ef4444; font-size:0.8rem;">\u25cf Extreme (&gt;150%)</span>
    </div>
    """, unsafe_allow_html=True)

    # Exclude "World" row from map
    df_regions = df[df["region"] != "World"].reset_index(drop=True)

    m = _dark_map()
    for _, row in df_regions.iterrows():
        color = _proj_color(row["change_2100"])
        radius = max(6, math.sqrt(row["pop_2050"] / 1_000_000_000) * 10)
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(str(row["region"]))}</strong><br/>'
            f'2024: {_fmt_pop(row["pop_2024"])}<br/>'
            f'2050: {_fmt_pop(row["pop_2050"])} ({row["change_2050"]:+.1f}%)<br/>'
            f'2100: {_fmt_pop(row["pop_2100"])} ({row["change_2100"]:+.1f}%)'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1.5,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f'{escape(str(row["region"]))}: {_fmt_pop(row["pop_2050"])} by 2050',
        ).add_to(m)

    _show_map(m)

    # Grouped bar chart: 2024 vs 2050 vs 2100
    st.markdown("##### Regional Population: 2024 vs 2050 vs 2100")
    fig, ax = _dark_chart(figsize=(12, 6))
    x = range(len(df_regions))
    bar_width = 0.25

    bars1 = ax.bar(
        [i - bar_width for i in x],
        df_regions["pop_2024"].values / 1_000_000_000,
        bar_width,
        color="#06b6d4",
        alpha=0.85,
        label="2024",
        edgecolor="#0a0e1a",
    )
    bars2 = ax.bar(
        list(x),
        df_regions["pop_2050"].values / 1_000_000_000,
        bar_width,
        color="#f59e0b",
        alpha=0.85,
        label="2050",
        edgecolor="#0a0e1a",
    )
    bars3 = ax.bar(
        [i + bar_width for i in x],
        df_regions["pop_2100"].values / 1_000_000_000,
        bar_width,
        color="#ec4899",
        alpha=0.85,
        label="2100",
        edgecolor="#0a0e1a",
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(df_regions["region"].values, color="#e8ecf4", fontsize=7, rotation=30, ha="right")
    ax.set_ylabel("Population (Billions)", color="#8b97b0", fontsize=10)
    ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4", fontsize=9)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Change chart
    st.markdown("##### Projected Change by 2100 (%)")
    fig2, ax2 = _dark_chart(figsize=(10, 5))
    ax2.barh(
        range(len(df_regions)),
        df_regions["change_2100"].values,
        color=[_proj_color(c) for c in df_regions["change_2100"].values],
        edgecolor="#0a0e1a", alpha=0.85,
    )
    ax2.set_yticks(range(len(df_regions)))
    ax2.set_yticklabels(df_regions["region"].values, color="#e8ecf4", fontsize=9)
    ax2.set_xlabel("Change from 2024 (%)", color="#8b97b0", fontsize=10)
    ax2.axvline(x=0, color="#e8ecf4", linewidth=0.8, alpha=0.5)
    ax2.invert_yaxis()
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    with st.expander(f"Full Data Table ({len(df)} regions)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Population Projections (CSV)",
        data=csv_buf.getvalue(),
        file_name="population_projections.csv",
        mime="text/csv",
        key="pop_proj_dl",
    )


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════

MAP_MODES = {
    "1. World Population by Country": _render_world_population,
    "2. Megacities (10M+)": _render_megacities,
    "3. Population Density": _render_population_density,
    "4. Urban vs Rural": _render_urban_vs_rural,
    "5. Population Growth Rate": _render_population_growth,
    "6. Historical Population": _render_historical_population,
    "7. Age Demographics": _render_age_demographics,
    "8. Most Crowded Places": _render_crowded_places,
    "9. Depopulating Regions": _render_depopulating_regions,
    "10. Future Projections": _render_future_projections,
}


def render_population_maps_tab():
    """Main render function for the Population & Demographics Maps tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f465 Population & Demographics Maps</h4>'
        '<p>World population, megacities, density, urbanization & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.selectbox(
        "Select Map Mode",
        list(MAP_MODES.keys()),
        key="pop_map_mode",
        help="Choose a population/demographics visualization",
    )

    st.markdown("---")

    # ── Render selected mode ──
    MAP_MODES[mode]()
