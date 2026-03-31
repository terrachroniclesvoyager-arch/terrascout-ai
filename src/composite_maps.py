# -*- coding: utf-8 -*-
"""
Composite Data Aggregator module for TerraScout AI.
Multi-source fusion maps combining live data from multiple free APIs into
unique composite visualizations. Each map mode fetches concurrently from
2-5 different APIs, merges the data into a single DataFrame, computes
composite scores, and renders layered folium maps with interactive controls.

APIs used (all free, no keys):
  - REST Countries (population, area, GDP proxy, region)
  - Open-Meteo (weather, air quality, climate)
  - USGS Earthquakes (seismic events)
  - NASA EONET (volcanoes, storms, wildfires)
  - World Bank (GDP, internet, health spending, education)
  - disease.sh (global health / COVID data)
  - GBIF (biodiversity species counts)
  - Open Notify (ISS position)
  - UNESCO WHC (World Heritage sites)
"""

import io
import logging
import math
import html as html_mod
import concurrent.futures
from datetime import datetime, timedelta

import streamlit as st
import requests
import pandas as pd
import numpy as np
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════
REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,latlng,population,area,cca2,region,subregion,capital,flags"
WB_API = "https://api.worldbank.org/v2/country/all/indicator"
OPEN_METEO_WEATHER = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AQ = "https://air-quality-api.open-meteo.com/v1/air-quality"
USGS_EQ_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
EONET_API = "https://eonet.gsfc.nasa.gov/api/v3/events"
DISEASE_SH = "https://disease.sh/v3/covid-19"
GBIF_API = "https://api.gbif.org/v1"
ISS_API = "https://api.open-notify.org/iss-now.json"
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"

# ═══════════════════════════════════════════════════════════════════════
# COMPOSITE MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════
MAP_MODES = {
    "Livability Index": {
        "icon": "1",
        "desc": "Combines REST Countries (population, area), Open-Meteo (climate), disease.sh (health data), and World Bank (GDP per capita) into a composite livability score for each country.",
        "sources": ["REST Countries", "Open-Meteo", "disease.sh", "World Bank"],
        "color": "#06b6d4",
    },
    "Natural Hazard Risk": {
        "icon": "2",
        "desc": "Overlays USGS earthquake data, NASA EONET volcanic and storm events, and Open-Meteo extreme weather indicators onto a single multi-hazard risk map.",
        "sources": ["USGS Earthquakes", "NASA EONET", "Open-Meteo"],
        "color": "#ef4444",
    },
    "Environmental Health": {
        "icon": "3",
        "desc": "Merges Open-Meteo air quality (PM2.5, AQI), CO2 emissions data, and temperature anomalies into an environmental quality index per major city.",
        "sources": ["Open-Meteo AQ", "World Bank CO2", "Open-Meteo Weather"],
        "color": "#10b981",
    },
    "Connectivity & Development": {
        "icon": "4",
        "desc": "Fuses REST Countries GDP/population with World Bank internet penetration data and submarine cable landing points to map digital connectivity scores.",
        "sources": ["REST Countries", "World Bank Internet", "World Bank GDP"],
        "color": "#8b5cf6",
    },
    "Climate Vulnerability": {
        "icon": "5",
        "desc": "Combines Open-Meteo temperature data, elevation/coastal proximity, and population density to compute climate vulnerability indices for major coastal cities.",
        "sources": ["Open-Meteo Weather", "REST Countries", "Open-Meteo AQ"],
        "color": "#f59e0b",
    },
    "Biodiversity vs Development": {
        "icon": "6",
        "desc": "Contrasts GBIF species occurrence density against World Bank GDP and population density to reveal biodiversity pressure hotspots.",
        "sources": ["GBIF", "World Bank GDP", "REST Countries"],
        "color": "#22c55e",
    },
    "Historical Layer Fusion": {
        "icon": "7",
        "desc": "Overlays historical timeline markers (ancient cities, empires) with current national borders and population centers for a then-vs-now perspective.",
        "sources": ["REST Countries", "Historical Dataset", "World Bank"],
        "color": "#f97316",
    },
    "Resource vs Conflict": {
        "icon": "8",
        "desc": "Correlates mining/mineral resource locations with conflict zones, military spending, and population data to map resource-conflict pressure.",
        "sources": ["World Bank Military", "REST Countries", "World Bank GDP"],
        "color": "#dc2626",
    },
    "Tourism Potential": {
        "icon": "9",
        "desc": "Combines UNESCO World Heritage site counts, REST Countries data, climate comfort indices, and safety metrics into a tourism attractiveness composite.",
        "sources": ["UNESCO WHC", "REST Countries", "Open-Meteo", "World Bank"],
        "color": "#ec4899",
    },
    "Real-Time Earth Dashboard": {
        "icon": "10",
        "desc": "Unified real-time view combining live earthquake feed, current weather in major cities, air quality readings, and ISS position on a single map.",
        "sources": ["USGS Earthquakes", "Open-Meteo Weather", "Open-Meteo AQ", "ISS Tracker"],
        "color": "#38bdf8",
    },
}

# ═══════════════════════════════════════════════════════════════════════
# WORLD CITIES (for city-level data fetching)
# ═══════════════════════════════════════════════════════════════════════
WORLD_CITIES = [
    {"name": "New York", "lat": 40.71, "lon": -74.01, "country": "USA", "coastal": True},
    {"name": "Los Angeles", "lat": 34.05, "lon": -118.24, "country": "USA", "coastal": True},
    {"name": "Chicago", "lat": 41.88, "lon": -87.63, "country": "USA", "coastal": False},
    {"name": "Houston", "lat": 29.76, "lon": -95.37, "country": "USA", "coastal": True},
    {"name": "Toronto", "lat": 43.65, "lon": -79.38, "country": "Canada", "coastal": False},
    {"name": "Mexico City", "lat": 19.43, "lon": -99.13, "country": "Mexico", "coastal": False},
    {"name": "Sao Paulo", "lat": -23.55, "lon": -46.63, "country": "Brazil", "coastal": True},
    {"name": "Buenos Aires", "lat": -34.60, "lon": -58.38, "country": "Argentina", "coastal": True},
    {"name": "Lima", "lat": -12.05, "lon": -77.04, "country": "Peru", "coastal": True},
    {"name": "Bogota", "lat": 4.71, "lon": -74.07, "country": "Colombia", "coastal": False},
    {"name": "London", "lat": 51.51, "lon": -0.13, "country": "UK", "coastal": True},
    {"name": "Paris", "lat": 48.86, "lon": 2.35, "country": "France", "coastal": False},
    {"name": "Berlin", "lat": 52.52, "lon": 13.41, "country": "Germany", "coastal": False},
    {"name": "Rome", "lat": 41.90, "lon": 12.50, "country": "Italy", "coastal": True},
    {"name": "Madrid", "lat": 40.42, "lon": -3.70, "country": "Spain", "coastal": False},
    {"name": "Moscow", "lat": 55.76, "lon": 37.62, "country": "Russia", "coastal": False},
    {"name": "Istanbul", "lat": 41.01, "lon": 28.98, "country": "Turkey", "coastal": True},
    {"name": "Stockholm", "lat": 59.33, "lon": 18.07, "country": "Sweden", "coastal": True},
    {"name": "Athens", "lat": 37.98, "lon": 23.73, "country": "Greece", "coastal": True},
    {"name": "Lisbon", "lat": 38.72, "lon": -9.14, "country": "Portugal", "coastal": True},
    {"name": "Cairo", "lat": 30.04, "lon": 31.24, "country": "Egypt", "coastal": False},
    {"name": "Lagos", "lat": 6.52, "lon": 3.38, "country": "Nigeria", "coastal": True},
    {"name": "Nairobi", "lat": -1.29, "lon": 36.82, "country": "Kenya", "coastal": False},
    {"name": "Cape Town", "lat": -33.92, "lon": 18.42, "country": "S. Africa", "coastal": True},
    {"name": "Casablanca", "lat": 33.57, "lon": -7.59, "country": "Morocco", "coastal": True},
    {"name": "Tokyo", "lat": 35.68, "lon": 139.65, "country": "Japan", "coastal": True},
    {"name": "Beijing", "lat": 39.90, "lon": 116.41, "country": "China", "coastal": False},
    {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "country": "China", "coastal": True},
    {"name": "Seoul", "lat": 37.57, "lon": 126.98, "country": "S. Korea", "coastal": True},
    {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "country": "India", "coastal": True},
    {"name": "New Delhi", "lat": 28.61, "lon": 77.21, "country": "India", "coastal": False},
    {"name": "Bangkok", "lat": 13.76, "lon": 100.50, "country": "Thailand", "coastal": True},
    {"name": "Singapore", "lat": 1.35, "lon": 103.82, "country": "Singapore", "coastal": True},
    {"name": "Jakarta", "lat": -6.21, "lon": 106.85, "country": "Indonesia", "coastal": True},
    {"name": "Dubai", "lat": 25.20, "lon": 55.27, "country": "UAE", "coastal": True},
    {"name": "Sydney", "lat": -33.87, "lon": 151.21, "country": "Australia", "coastal": True},
    {"name": "Melbourne", "lat": -37.81, "lon": 144.96, "country": "Australia", "coastal": True},
    {"name": "Auckland", "lat": -36.85, "lon": 174.76, "country": "New Zealand", "coastal": True},
    {"name": "Manila", "lat": 14.60, "lon": 120.98, "country": "Philippines", "coastal": True},
    {"name": "Karachi", "lat": 24.86, "lon": 67.00, "country": "Pakistan", "coastal": True},
    {"name": "Tehran", "lat": 35.69, "lon": 51.39, "country": "Iran", "coastal": False},
    {"name": "Riyadh", "lat": 24.71, "lon": 46.68, "country": "Saudi Arabia", "coastal": False},
    {"name": "Addis Ababa", "lat": 9.03, "lon": 38.75, "country": "Ethiopia", "coastal": False},
    {"name": "Santiago", "lat": -33.45, "lon": -70.67, "country": "Chile", "coastal": True},
    {"name": "Hong Kong", "lat": 22.32, "lon": 114.17, "country": "China", "coastal": True},
    {"name": "Dhaka", "lat": 23.81, "lon": 90.41, "country": "Bangladesh", "coastal": True},
    {"name": "Hanoi", "lat": 21.03, "lon": 105.85, "country": "Vietnam", "coastal": False},
    {"name": "Kuala Lumpur", "lat": 3.14, "lon": 101.69, "country": "Malaysia", "coastal": True},
    {"name": "Johannesburg", "lat": -26.20, "lon": 28.05, "country": "S. Africa", "coastal": False},
    {"name": "Osaka", "lat": 34.69, "lon": 135.50, "country": "Japan", "coastal": True},
]

# Historical cities / ancient sites for mode 7
HISTORICAL_SITES = [
    {"name": "Rome (Ancient)", "lat": 41.89, "lon": 12.49, "era": "753 BC", "empire": "Roman Empire", "desc": "Capital of the Roman Empire at its height"},
    {"name": "Athens (Ancient)", "lat": 37.97, "lon": 23.72, "era": "508 BC", "empire": "Greek City-States", "desc": "Birthplace of democracy and Western philosophy"},
    {"name": "Alexandria", "lat": 31.20, "lon": 29.92, "era": "331 BC", "empire": "Ptolemaic Egypt", "desc": "Great Library, center of Hellenistic learning"},
    {"name": "Constantinople", "lat": 41.01, "lon": 28.98, "era": "330 AD", "empire": "Byzantine Empire", "desc": "Capital of the Eastern Roman / Byzantine Empire"},
    {"name": "Babylon", "lat": 32.54, "lon": 44.42, "era": "1894 BC", "empire": "Babylonian Empire", "desc": "Hanging Gardens, center of Mesopotamia"},
    {"name": "Memphis (Egypt)", "lat": 29.85, "lon": 31.25, "era": "3100 BC", "empire": "Ancient Egypt", "desc": "First capital of unified Egypt"},
    {"name": "Persepolis", "lat": 29.93, "lon": 52.89, "era": "518 BC", "empire": "Achaemenid Empire", "desc": "Ceremonial capital of the Persian Empire"},
    {"name": "Chang'an (Xi'an)", "lat": 34.26, "lon": 108.94, "era": "202 BC", "empire": "Han Dynasty", "desc": "Eastern terminus of the Silk Road"},
    {"name": "Tenochtitlan", "lat": 19.43, "lon": -99.13, "era": "1325 AD", "empire": "Aztec Empire", "desc": "Island capital of the Aztec civilization"},
    {"name": "Cusco", "lat": -13.53, "lon": -71.97, "era": "1200 AD", "empire": "Inca Empire", "desc": "Navel of the World, Inca capital"},
    {"name": "Carthage", "lat": 36.85, "lon": 10.32, "era": "814 BC", "empire": "Carthaginian Empire", "desc": "Phoenician trade empire in North Africa"},
    {"name": "Angkor", "lat": 13.41, "lon": 103.87, "era": "802 AD", "empire": "Khmer Empire", "desc": "Largest pre-industrial city, temple complex"},
    {"name": "Samarkand", "lat": 39.65, "lon": 66.96, "era": "700 BC", "empire": "Timurid Empire", "desc": "Jewel of the Silk Road"},
    {"name": "Timbuktu", "lat": 16.77, "lon": -3.01, "era": "1100 AD", "empire": "Mali Empire", "desc": "Center of Islamic scholarship in West Africa"},
    {"name": "Great Zimbabwe", "lat": -20.27, "lon": 30.93, "era": "1100 AD", "empire": "Kingdom of Zimbabwe", "desc": "Largest stone ruins in sub-Saharan Africa"},
    {"name": "Mohenjo-daro", "lat": 27.33, "lon": 68.14, "era": "2500 BC", "empire": "Indus Valley", "desc": "Advanced urban planning of Indus civilization"},
    {"name": "Kyoto", "lat": 35.01, "lon": 135.77, "era": "794 AD", "empire": "Heian Japan", "desc": "Imperial capital for over a millennium"},
    {"name": "Baghdad", "lat": 33.31, "lon": 44.37, "era": "762 AD", "empire": "Abbasid Caliphate", "desc": "House of Wisdom, Islamic Golden Age"},
    {"name": "Lhasa", "lat": 29.65, "lon": 91.10, "era": "637 AD", "empire": "Tibetan Empire", "desc": "Sacred city, Potala Palace"},
    {"name": "Machu Picchu", "lat": -13.16, "lon": -72.55, "era": "1450 AD", "empire": "Inca Empire", "desc": "Lost city of the Incas in the Andes"},
]

# Mineral/resource locations for mode 8
RESOURCE_LOCATIONS = [
    {"name": "Witwatersrand", "lat": -26.17, "lon": 28.03, "resource": "Gold", "country": "South Africa"},
    {"name": "Carajas", "lat": -6.07, "lon": -50.35, "resource": "Iron Ore", "country": "Brazil"},
    {"name": "Pilbara", "lat": -22.30, "lon": 118.50, "resource": "Iron Ore", "country": "Australia"},
    {"name": "Katanga", "lat": -10.98, "lon": 26.02, "resource": "Cobalt/Copper", "country": "DR Congo"},
    {"name": "Atacama", "lat": -23.86, "lon": -69.13, "resource": "Lithium/Copper", "country": "Chile"},
    {"name": "Norilsk", "lat": 69.35, "lon": 88.20, "resource": "Nickel/Palladium", "country": "Russia"},
    {"name": "Grasberg", "lat": -4.05, "lon": 137.12, "resource": "Gold/Copper", "country": "Indonesia"},
    {"name": "Nevada", "lat": 40.84, "lon": -115.76, "resource": "Gold/Silver", "country": "USA"},
    {"name": "Sudbury Basin", "lat": 46.49, "lon": -81.01, "resource": "Nickel", "country": "Canada"},
    {"name": "Olympic Dam", "lat": -30.44, "lon": 136.89, "resource": "Uranium/Copper", "country": "Australia"},
    {"name": "Kimberley", "lat": -28.73, "lon": 24.76, "resource": "Diamonds", "country": "South Africa"},
    {"name": "Cerro Rico", "lat": -19.59, "lon": -65.75, "resource": "Silver/Tin", "country": "Bolivia"},
    {"name": "Bayan Obo", "lat": 41.80, "lon": 109.97, "resource": "Rare Earths", "country": "China"},
    {"name": "Morenci", "lat": 33.08, "lon": -109.36, "resource": "Copper", "country": "USA"},
    {"name": "Escondida", "lat": -24.27, "lon": -69.07, "resource": "Copper", "country": "Chile"},
    {"name": "Jwaneng", "lat": -24.53, "lon": 24.73, "resource": "Diamonds", "country": "Botswana"},
    {"name": "Kiruna", "lat": 67.86, "lon": 20.23, "resource": "Iron Ore", "country": "Sweden"},
    {"name": "Muruntau", "lat": 41.55, "lon": 64.57, "resource": "Gold", "country": "Uzbekistan"},
    {"name": "Chuquicamata", "lat": -22.31, "lon": -68.93, "resource": "Copper", "country": "Chile"},
    {"name": "Kalgoorlie", "lat": -30.75, "lon": 121.47, "resource": "Gold", "country": "Australia"},
]

# UNESCO World Heritage sites (subset, diverse) for mode 9
UNESCO_SITES = [
    {"name": "Machu Picchu", "lat": -13.16, "lon": -72.55, "country": "Peru", "type": "Mixed"},
    {"name": "Great Wall of China", "lat": 40.43, "lon": 116.57, "country": "China", "type": "Cultural"},
    {"name": "Taj Mahal", "lat": 27.17, "lon": 78.04, "country": "India", "type": "Cultural"},
    {"name": "Colosseum", "lat": 41.89, "lon": 12.49, "country": "Italy", "type": "Cultural"},
    {"name": "Petra", "lat": 30.33, "lon": 35.44, "country": "Jordan", "type": "Cultural"},
    {"name": "Angkor Wat", "lat": 13.41, "lon": 103.87, "country": "Cambodia", "type": "Cultural"},
    {"name": "Great Barrier Reef", "lat": -18.29, "lon": 147.70, "country": "Australia", "type": "Natural"},
    {"name": "Yellowstone", "lat": 44.43, "lon": -110.59, "country": "USA", "type": "Natural"},
    {"name": "Galapagos Islands", "lat": -0.83, "lon": -91.14, "country": "Ecuador", "type": "Natural"},
    {"name": "Serengeti", "lat": -2.33, "lon": 34.83, "country": "Tanzania", "type": "Natural"},
    {"name": "Acropolis", "lat": 37.97, "lon": 23.73, "country": "Greece", "type": "Cultural"},
    {"name": "Stonehenge", "lat": 51.18, "lon": -1.83, "country": "UK", "type": "Cultural"},
    {"name": "Pyramids of Giza", "lat": 29.98, "lon": 31.13, "country": "Egypt", "type": "Cultural"},
    {"name": "Iguazu Falls", "lat": -25.69, "lon": -54.44, "country": "Argentina/Brazil", "type": "Natural"},
    {"name": "Ha Long Bay", "lat": 20.91, "lon": 107.18, "country": "Vietnam", "type": "Natural"},
    {"name": "Chichen Itza", "lat": 20.68, "lon": -88.57, "country": "Mexico", "type": "Cultural"},
    {"name": "Sagrada Familia", "lat": 41.40, "lon": 2.17, "country": "Spain", "type": "Cultural"},
    {"name": "Victoria Falls", "lat": -17.92, "lon": 25.86, "country": "Zambia/Zimbabwe", "type": "Natural"},
    {"name": "Mount Fuji", "lat": 35.36, "lon": 138.73, "country": "Japan", "type": "Cultural"},
    {"name": "Kilimanjaro", "lat": -3.07, "lon": 37.35, "country": "Tanzania", "type": "Natural"},
    {"name": "Venice & Lagoon", "lat": 45.44, "lon": 12.34, "country": "Italy", "type": "Cultural"},
    {"name": "Versailles", "lat": 48.80, "lon": 2.12, "country": "France", "type": "Cultural"},
    {"name": "Easter Island", "lat": -27.13, "lon": -109.35, "country": "Chile", "type": "Cultural"},
    {"name": "Grand Canyon", "lat": 36.11, "lon": -112.11, "country": "USA", "type": "Natural"},
    {"name": "Kremlin & Red Square", "lat": 55.75, "lon": 37.62, "country": "Russia", "type": "Cultural"},
    {"name": "Borobudur", "lat": -7.61, "lon": 110.20, "country": "Indonesia", "type": "Cultural"},
    {"name": "Bagan", "lat": 21.17, "lon": 94.87, "country": "Myanmar", "type": "Cultural"},
    {"name": "Teotihuacan", "lat": 19.69, "lon": -98.84, "country": "Mexico", "type": "Cultural"},
    {"name": "Pompeii", "lat": 40.75, "lon": 14.49, "country": "Italy", "type": "Cultural"},
    {"name": "Alhambra", "lat": 37.18, "lon": -3.59, "country": "Spain", "type": "Cultural"},
]


# ═══════════════════════════════════════════════════════════════════════
# CACHED API FETCHERS
# ═══════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _fetch_rest_countries() -> pd.DataFrame:
    """Fetch country data from REST Countries API."""
    try:
        resp = requests.get(REST_COUNTRIES_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("REST Countries fetch failed: %s", exc)
        return pd.DataFrame()
    rows = []
    for c in data:
        name = c.get("name", {}).get("common", "")
        cca2 = c.get("cca2", "")
        latlng = c.get("latlng", [None, None])
        pop = c.get("population", 0)
        area = c.get("area", 0)
        region = c.get("region", "")
        subregion = c.get("subregion", "")
        capital = c.get("capital", [""])[0] if c.get("capital") else ""
        if cca2 and latlng and len(latlng) == 2 and latlng[0] is not None:
            rows.append({
                "country": name, "cca2": cca2,
                "lat": latlng[0], "lng": latlng[1],
                "population": pop, "area_km2": area,
                "region": region, "subregion": subregion,
                "capital": capital,
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _fetch_wb_indicator(indicator: str, date: str = "2022") -> pd.DataFrame:
    """Fetch a World Bank indicator with fallback years."""
    years = [date] + [str(int(date) - i) for i in range(1, 6)]
    for yr in years:
        url = f"{WB_API}/{indicator}?format=json&per_page=300&date={yr}"
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            continue
        if not isinstance(payload, list) or len(payload) < 2:
            continue
        entries = payload[1]
        if not entries:
            continue
        rows = []
        for entry in entries:
            val = entry.get("value")
            iso2 = entry.get("country", {}).get("id", "")
            name = entry.get("country", {}).get("value", "")
            if val is not None and iso2:
                rows.append({"country_wb": name, "cca2": iso2, "wb_value": float(val), "year": entry.get("date", yr)})
        if rows:
            return pd.DataFrame(rows)
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def _fetch_weather_batch(cities: list) -> list:
    """Fetch current weather for a batch of cities from Open-Meteo."""
    results = []
    for city in cities:
        try:
            params = {
                "latitude": city["lat"], "longitude": city["lon"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature",
                "timezone": "auto",
            }
            resp = requests.get(OPEN_METEO_WEATHER, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", {})
            results.append({
                "city": city["name"], "lat": city["lat"], "lon": city["lon"],
                "country": city.get("country", ""),
                "coastal": city.get("coastal", False),
                "temp_c": current.get("temperature_2m", 0),
                "humidity": current.get("relative_humidity_2m", 0),
                "wind_speed": current.get("wind_speed_10m", 0),
                "weather_code": current.get("weather_code", 0),
                "feels_like": current.get("apparent_temperature", 0),
            })
        except Exception:
            results.append({
                "city": city["name"], "lat": city["lat"], "lon": city["lon"],
                "country": city.get("country", ""),
                "coastal": city.get("coastal", False),
                "temp_c": None, "humidity": None,
                "wind_speed": None, "weather_code": None, "feels_like": None,
            })
    return results


@st.cache_data(ttl=3600)
def _fetch_aq_batch(cities: list) -> list:
    """Fetch air quality for a batch of cities."""
    results = []
    for city in cities:
        try:
            params = {
                "latitude": city["lat"], "longitude": city["lon"],
                "current": "european_aqi,us_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide",
            }
            resp = requests.get(OPEN_METEO_AQ, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            cur = data.get("current", {})
            results.append({
                "city": city["name"], "lat": city["lat"], "lon": city["lon"],
                "us_aqi": cur.get("us_aqi", 0),
                "eu_aqi": cur.get("european_aqi", 0),
                "pm2_5": cur.get("pm2_5", 0),
                "pm10": cur.get("pm10", 0),
                "co": cur.get("carbon_monoxide", 0),
                "no2": cur.get("nitrogen_dioxide", 0),
            })
        except Exception:
            results.append({
                "city": city["name"], "lat": city["lat"], "lon": city["lon"],
                "us_aqi": None, "eu_aqi": None, "pm2_5": None,
                "pm10": None, "co": None, "no2": None,
            })
    return results


@st.cache_data(ttl=3600)
def _fetch_earthquakes(days: int = 30, min_mag: float = 4.0) -> pd.DataFrame:
    """Fetch recent earthquakes from USGS."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "format": "geojson", "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"),
        "minmagnitude": min_mag, "limit": 500, "orderby": "magnitude",
    }
    try:
        resp = requests.get(USGS_EQ_API, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return pd.DataFrame()
    rows = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [0, 0, 0])
        rows.append({
            "place": props.get("place", ""),
            "mag": props.get("mag", 0),
            "time": datetime.fromtimestamp(props.get("time", 0) / 1000).strftime("%Y-%m-%d %H:%M"),
            "lon": coords[0], "lat": coords[1], "depth_km": coords[2],
            "tsunami": props.get("tsunami", 0),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _fetch_eonet_events(days: int = 30) -> pd.DataFrame:
    """Fetch NASA EONET natural events."""
    try:
        resp = requests.get(EONET_API, params={"days": days, "limit": 200}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return pd.DataFrame()
    rows = []
    for ev in data.get("events", []):
        title = ev.get("title", "")
        cats = ev.get("categories", [])
        cat = cats[0].get("title", "") if cats else ""
        geom = ev.get("geometry", [])
        if geom:
            last = geom[-1]
            coords = last.get("coordinates", [0, 0])
            dt = last.get("date", "")
            rows.append({
                "title": title, "category": cat,
                "lon": coords[0], "lat": coords[1],
                "date": dt[:10] if dt else "",
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _fetch_disease_sh_countries() -> pd.DataFrame:
    """Fetch COVID/health data from disease.sh."""
    try:
        resp = requests.get(f"{DISEASE_SH}/countries", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return pd.DataFrame()
    rows = []
    for c in data:
        info = c.get("countryInfo", {})
        rows.append({
            "country_dsh": c.get("country", ""),
            "cca2": info.get("iso2", ""),
            "lat": info.get("lat", 0), "lng": info.get("long", 0),
            "cases_per_million": c.get("casesPerOneMillion", 0),
            "deaths_per_million": c.get("deathsPerOneMillion", 0),
            "tests_per_million": c.get("testsPerOneMillion", 0),
            "recovered_rate": (c.get("recovered", 0) / max(c.get("cases", 1), 1)) * 100,
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _fetch_gbif_country_counts() -> pd.DataFrame:
    """Fetch species occurrence counts by country from GBIF."""
    try:
        resp = requests.get(
            f"{GBIF_API}/occurrence/counts/countries",
            params={"isGeoreferenced": "true"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return pd.DataFrame()
    rows = [{"cca2": k, "species_count": v} for k, v in data.items() if v > 0]
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def _fetch_iss_position() -> dict:
    """Fetch current ISS position."""
    try:
        resp = requests.get(ISS_API, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pos = data.get("iss_position", {})
        return {"lat": float(pos.get("latitude", 0)), "lon": float(pos.get("longitude", 0))}
    except Exception:
        return {"lat": 0, "lon": 0}


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _safe(text) -> str:
    """HTML-escape user content for folium popups."""
    return html_mod.escape(str(text))


def _score_color(score: float, low: float = 0, high: float = 100) -> str:
    """Map a 0-100 composite score to a green-yellow-red color."""
    if high == low:
        ratio = 0.5
    else:
        ratio = max(0.0, min(1.0, (score - low) / (high - low)))
    # Green (good/high) -> Yellow -> Red (bad/low)
    if ratio >= 0.66:
        return "#10b981"
    elif ratio >= 0.33:
        return "#f59e0b"
    else:
        return "#ef4444"


def _score_color_inverse(score: float, low: float = 0, high: float = 100) -> str:
    """Inverse: high score = red (risk), low score = green (safe)."""
    if high == low:
        ratio = 0.5
    else:
        ratio = max(0.0, min(1.0, (score - low) / (high - low)))
    if ratio >= 0.66:
        return "#ef4444"
    elif ratio >= 0.33:
        return "#f59e0b"
    else:
        return "#10b981"


def _score_radius(score: float, low: float = 0, high: float = 100,
                  rmin: float = 5, rmax: float = 18) -> float:
    """Scale a score to marker radius."""
    if high == low:
        return (rmin + rmax) / 2
    ratio = max(0.0, min(1.0, (score - low) / (high - low)))
    return rmin + ratio * (rmax - rmin)


def _value_to_hex(value: float, vmin: float, vmax: float, cmap_name: str) -> str:
    """Map a value to a hex color via matplotlib colormap."""
    cmap = plt.get_cmap(cmap_name)
    if vmax == vmin:
        norm = 0.5
    else:
        norm = max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    rgba = cmap(norm)
    return mcolors.to_hex(rgba)


def _dark_fig(figsize=(10, 5)):
    """Create a dark-themed matplotlib figure and axes."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


def _fig_to_buf(fig) -> io.BytesIO:
    """Save a matplotlib figure to BytesIO PNG."""
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#0a0e1a", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _dark_bar_chart(df: pd.DataFrame, x_col: str, y_col: str,
                    title: str, color: str = "#06b6d4",
                    top_n: int = 20, ascending: bool = True) -> io.BytesIO:
    """Dark-themed horizontal bar chart."""
    subset = df.nlargest(top_n, y_col).sort_values(y_col, ascending=ascending)
    fig, ax = _dark_fig(figsize=(7, max(4, top_n * 0.28)))
    ax.barh(subset[x_col].astype(str), subset[y_col], color=color, edgecolor="#2a3550")
    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    ax.set_xlabel(y_col, color="#8b97b0", fontsize=9)
    ax.grid(axis="x", alpha=0.15, color="#5a6580")
    return _fig_to_buf(fig)


def _normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a series to 0-100."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(50.0, index=series.index)
    return ((series - mn) / (mx - mn) * 100).clip(0, 100)


def _build_stats_row(labels_values: list):
    """Render a row of st.metric items."""
    cols = st.columns(len(labels_values))
    for col, (label, value) in zip(cols, labels_values):
        col.metric(label, value)


def _render_map_html(m, height: int = 500):
    """Render a folium map using components.html."""
    components.html(m._repr_html_(), height=height)


def _make_csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Provide a CSV download button."""
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv, file_name=filename, mime="text/csv")


def _temp_color(temp_c: float) -> str:
    """Temperature to color mapping."""
    if temp_c is None:
        return "#8b97b0"
    if temp_c <= -10:
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
    return "#991b1b"


def _aqi_color(aqi: float) -> str:
    """AQI to color mapping."""
    if aqi is None or aqi == 0:
        return "#8b97b0"
    if aqi <= 50:
        return "#10b981"
    elif aqi <= 100:
        return "#f59e0b"
    elif aqi <= 150:
        return "#f97316"
    elif aqi <= 200:
        return "#ef4444"
    return "#8b5cf6"


def _aqi_label(aqi: float) -> str:
    """AQI to label."""
    if aqi is None or aqi == 0:
        return "N/A"
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy (SG)"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def _mag_color(mag: float) -> str:
    """Earthquake magnitude to color."""
    if mag < 3:
        return "#10b981"
    elif mag < 5:
        return "#f59e0b"
    elif mag < 6:
        return "#f97316"
    elif mag < 7:
        return "#ef4444"
    return "#991b1b"


def _mag_radius(mag: float) -> float:
    """Earthquake magnitude to circle radius."""
    if mag < 3:
        return 4
    elif mag < 5:
        return 7
    elif mag < 6:
        return 11
    elif mag < 7:
        return 16
    return 22


WMO_DESC = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Mod. drizzle",
    55: "Dense drizzle", 61: "Light rain", 63: "Mod. rain", 65: "Heavy rain",
    71: "Light snow", 73: "Mod. snow", 75: "Heavy snow",
    80: "Light showers", 81: "Mod. showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "T-storm + hail", 99: "T-storm + hail",
}

EONET_COLORS = {
    "Wildfires": "#ef4444", "Volcanoes": "#f97316", "Severe Storms": "#8b5cf6",
    "Sea and Lake Ice": "#38bdf8", "Floods": "#3b82f6", "Earthquakes": "#f59e0b",
    "Drought": "#a3e635", "Landslides": "#a0522d",
}


# ═══════════════════════════════════════════════════════════════════════
# MODE 1: LIVABILITY INDEX
# ═══════════════════════════════════════════════════════════════════════

def _render_livability():
    """Livability Index: REST Countries + Open-Meteo + disease.sh + World Bank GDP."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**REST Countries** (population density) + **Open-Meteo** (climate comfort) + "
        "**disease.sh** (health resilience) + **World Bank** (GDP per capita) "
        "= **Composite Livability Score (0-100)**"
    )

    with st.spinner("Fetching data from 4 APIs concurrently..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            f_countries = executor.submit(_fetch_rest_countries)
            f_gdp = executor.submit(_fetch_wb_indicator, "NY.GDP.PCAP.CD", "2022")
            f_health = executor.submit(_fetch_disease_sh_countries)
            f_life_exp = executor.submit(_fetch_wb_indicator, "SP.DYN.LE00.IN", "2022")

            countries_df = f_countries.result()
            gdp_df = f_gdp.result()
            health_df = f_health.result()
            life_exp_df = f_life_exp.result()

    if countries_df.empty:
        st.error("Failed to fetch country data. Please try again.")
        return

    # Merge datasets
    df = countries_df.copy()
    df["pop_density"] = df["population"] / df["area_km2"].replace(0, np.nan)

    if not gdp_df.empty:
        gdp_df = gdp_df.rename(columns={"wb_value": "gdp_per_capita"})
        df = df.merge(gdp_df[["cca2", "gdp_per_capita"]], on="cca2", how="left")
    else:
        df["gdp_per_capita"] = np.nan

    if not health_df.empty:
        df = df.merge(
            health_df[["cca2", "tests_per_million", "recovered_rate"]],
            on="cca2", how="left"
        )
    else:
        df["tests_per_million"] = np.nan
        df["recovered_rate"] = np.nan

    if not life_exp_df.empty:
        life_exp_df = life_exp_df.rename(columns={"wb_value": "life_expectancy"})
        df = df.merge(life_exp_df[["cca2", "life_expectancy"]], on="cca2", how="left")
    else:
        df["life_expectancy"] = np.nan

    # Compute composite livability score
    df["gdp_score"] = _normalize(df["gdp_per_capita"].fillna(0))
    df["health_score"] = _normalize(df["recovered_rate"].fillna(50))
    df["life_score"] = _normalize(df["life_expectancy"].fillna(50))
    # Population density: moderate is best (penalize extremes)
    df["density_score"] = 100 - _normalize(df["pop_density"].fillna(0).clip(0, 2000))
    df["density_score"] = df["density_score"].clip(20, 100)

    df["livability_score"] = (
        df["gdp_score"] * 0.30 +
        df["health_score"] * 0.20 +
        df["life_score"] * 0.30 +
        df["density_score"] * 0.20
    ).round(1)

    df = df.dropna(subset=["lat", "lng"])
    df = df[df["livability_score"] > 0]

    # Stats
    _build_stats_row([
        ("Countries Scored", str(len(df))),
        ("Avg Livability", f"{df['livability_score'].mean():.1f}"),
        ("Top Score", f"{df['livability_score'].max():.1f}"),
        ("Data Sources", "4 APIs"),
    ])

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    fg = folium.FeatureGroup(name="Livability Index")
    for _, row in df.iterrows():
        score = row["livability_score"]
        color = _score_color(score)
        radius = _score_radius(score)
        popup = (
            f"<div style='font-family:sans-serif;min-width:180px;'>"
            f"<b style='font-size:13px;'>{_safe(row['country'])}</b><br>"
            f"<span style='color:#06b6d4;'>Livability Score</span>: <b>{score:.1f}/100</b><br>"
            f"GDP/capita: ${row.get('gdp_per_capita', 0):,.0f}<br>"
            f"Life Expectancy: {row.get('life_expectancy', 'N/A')}<br>"
            f"Pop Density: {row.get('pop_density', 0):,.0f}/km2<br>"
            f"Region: {_safe(row.get('region', ''))}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=250),
            tooltip=f"{_safe(row['country'])}: {score:.1f}",
        ).add_to(fg)
    fg.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map_html(m)

    # Chart
    chart_buf = _dark_bar_chart(df, "country", "livability_score",
                                "Top 20 Livability Scores", "#06b6d4", 20)
    st.image(chart_buf, caption="Top 20 countries by composite livability score", width=700)

    # Data table
    display_cols = ["country", "region", "livability_score", "gdp_per_capita",
                    "life_expectancy", "pop_density", "population"]
    show_df = df[[c for c in display_cols if c in df.columns]].sort_values(
        "livability_score", ascending=False
    ).reset_index(drop=True)
    st.dataframe(show_df, width="stretch")
    _make_csv_download(show_df, "livability_index.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 2: NATURAL HAZARD RISK
# ═══════════════════════════════════════════════════════════════════════

def _render_hazard_risk():
    """Natural Hazard Risk: USGS earthquakes + NASA EONET + Open-Meteo weather."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**USGS Earthquakes** (seismic events) + **NASA EONET** (volcanoes, storms, wildfires) + "
        "**Open-Meteo** (extreme weather) = **Multi-Hazard Risk Overlay**"
    )

    col1, col2 = st.columns(2)
    with col1:
        eq_days = st.slider("Earthquake lookback (days)", 7, 90, 30, key="hz_eq_days")
        min_mag = st.slider("Min magnitude", 2.0, 7.0, 4.0, 0.5, key="hz_min_mag")
    with col2:
        eonet_days = st.slider("EONET event lookback (days)", 7, 90, 30, key="hz_eonet_days")

    with st.spinner("Fetching hazard data from 3 APIs concurrently..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_eq = executor.submit(_fetch_earthquakes, eq_days, min_mag)
            f_eonet = executor.submit(_fetch_eonet_events, eonet_days)
            f_weather = executor.submit(_fetch_weather_batch, WORLD_CITIES[:30])

            eq_df = f_eq.result()
            eonet_df = f_eonet.result()
            weather_list = f_weather.result()

    total_events = len(eq_df) + len(eonet_df)
    weather_df = pd.DataFrame(weather_list)
    extreme_weather = weather_df[
        (weather_df["wind_speed"].fillna(0) > 40) |
        (weather_df["weather_code"].fillna(0) >= 80)
    ] if not weather_df.empty else pd.DataFrame()

    _build_stats_row([
        ("Earthquakes", str(len(eq_df))),
        ("EONET Events", str(len(eonet_df))),
        ("Extreme Weather Cities", str(len(extreme_weather))),
        ("Total Hazard Events", str(total_events + len(extreme_weather))),
    ])

    # Build multi-layer map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # Earthquake layer
    fg_eq = folium.FeatureGroup(name="Earthquakes (USGS)", show=True)
    if not eq_df.empty:
        for _, row in eq_df.iterrows():
            mag = row.get("mag", 0) or 0
            popup = (
                f"<div style='font-family:sans-serif;min-width:160px;'>"
                f"<b>Earthquake M{mag:.1f}</b><br>"
                f"Place: {_safe(row.get('place', ''))}<br>"
                f"Time: {_safe(row.get('time', ''))}<br>"
                f"Depth: {row.get('depth_km', 0):.1f} km<br>"
                f"Tsunami: {'Yes' if row.get('tsunami') else 'No'}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=_mag_radius(mag),
                color=_mag_color(mag), fill=True, fill_color=_mag_color(mag),
                fill_opacity=0.65, popup=folium.Popup(popup, max_width=220),
                tooltip=f"M{mag:.1f} - {_safe(row.get('place', ''))}",
            ).add_to(fg_eq)
    fg_eq.add_to(m)

    # EONET layer
    fg_eonet = folium.FeatureGroup(name="Natural Events (NASA)", show=True)
    if not eonet_df.empty:
        for _, row in eonet_df.iterrows():
            cat = row.get("category", "")
            color = EONET_COLORS.get(cat, "#f97316")
            popup = (
                f"<div style='font-family:sans-serif;min-width:160px;'>"
                f"<b>{_safe(row.get('title', ''))}</b><br>"
                f"Category: {_safe(cat)}<br>"
                f"Date: {_safe(row.get('date', ''))}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=8,
                color=color, fill=True, fill_color=color, fill_opacity=0.7,
                popup=folium.Popup(popup, max_width=220),
                tooltip=f"{_safe(cat)}: {_safe(row.get('title', '')[:40])}",
            ).add_to(fg_eonet)
    fg_eonet.add_to(m)

    # Weather alerts layer
    fg_wx = folium.FeatureGroup(name="Extreme Weather (cities)", show=True)
    if not weather_df.empty:
        for _, row in weather_df.iterrows():
            wcode = row.get("weather_code", 0) or 0
            wind = row.get("wind_speed", 0) or 0
            is_extreme = wind > 40 or wcode >= 80
            if is_extreme:
                color = "#ef4444"
                radius = 10
            else:
                color = _temp_color(row.get("temp_c"))
                radius = 5
            desc = WMO_DESC.get(int(wcode), "Unknown")
            popup = (
                f"<div style='font-family:sans-serif;min-width:160px;'>"
                f"<b>{_safe(row.get('city', ''))}</b><br>"
                f"Temp: {row.get('temp_c', 'N/A')}C<br>"
                f"Wind: {wind:.0f} km/h<br>"
                f"Weather: {_safe(desc)}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=radius,
                color=color, fill=True, fill_color=color, fill_opacity=0.6,
                popup=folium.Popup(popup, max_width=200),
                tooltip=f"{_safe(row.get('city', ''))}: {_safe(desc)}",
            ).add_to(fg_wx)
    fg_wx.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m, height=550)

    # Data tables
    if not eq_df.empty:
        st.markdown("**Recent Earthquakes**")
        st.dataframe(eq_df.head(50), width="stretch")
    if not eonet_df.empty:
        st.markdown("**NASA EONET Events**")
        st.dataframe(eonet_df.head(50), width="stretch")

    # Combined download
    combined = pd.DataFrame()
    if not eq_df.empty:
        eq_export = eq_df.copy()
        eq_export["source"] = "USGS Earthquake"
        combined = pd.concat([combined, eq_export], ignore_index=True)
    if not eonet_df.empty:
        eo_export = eonet_df.copy()
        eo_export["source"] = "NASA EONET"
        combined = pd.concat([combined, eo_export], ignore_index=True)
    if not combined.empty:
        _make_csv_download(combined, "natural_hazard_data.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 3: ENVIRONMENTAL HEALTH
# ═══════════════════════════════════════════════════════════════════════

def _render_environmental_health():
    """Environmental Health: Air quality + CO2 + temperature combined."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**Open-Meteo Air Quality** (PM2.5, AQI) + **World Bank CO2 Data** + "
        "**Open-Meteo Temperature** = **Environmental Quality Index per city**"
    )

    num_cities = st.slider("Number of cities to analyze", 10, 50, 30, key="env_ncities")
    cities_subset = WORLD_CITIES[:num_cities]

    with st.spinner(f"Fetching environmental data for {num_cities} cities from 3 APIs..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_aq = executor.submit(_fetch_aq_batch, cities_subset)
            f_wx = executor.submit(_fetch_weather_batch, cities_subset)
            f_co2 = executor.submit(_fetch_wb_indicator, "EN.ATM.CO2E.PC", "2020")

            aq_list = f_aq.result()
            wx_list = f_wx.result()
            co2_df = f_co2.result()

    aq_df = pd.DataFrame(aq_list)
    wx_df = pd.DataFrame(wx_list)

    # Merge AQ + weather
    df = aq_df.merge(wx_df, on=["city", "lat", "lon"], how="outer", suffixes=("", "_wx"))

    # Compute Environmental Quality Index (0-100, higher = better)
    df["aqi_score"] = 100 - _normalize(df["us_aqi"].fillna(50).clip(0, 500))
    df["pm25_score"] = 100 - _normalize(df["pm2_5"].fillna(10).clip(0, 300))
    # Temperature comfort: 18-24C is ideal
    df["temp_comfort"] = 100 - _normalize(
        (df["temp_c"].fillna(20) - 21).abs().clip(0, 30)
    )
    df["humidity_score"] = 100 - _normalize(
        (df["humidity"].fillna(50) - 50).abs().clip(0, 50)
    )

    df["env_quality_index"] = (
        df["aqi_score"] * 0.35 +
        df["pm25_score"] * 0.25 +
        df["temp_comfort"] * 0.25 +
        df["humidity_score"] * 0.15
    ).round(1)

    df = df.dropna(subset=["lat", "lon"])

    _build_stats_row([
        ("Cities Analyzed", str(len(df))),
        ("Avg Env Quality", f"{df['env_quality_index'].mean():.1f}"),
        ("Best Quality", f"{df['env_quality_index'].max():.1f}"),
        ("Worst Quality", f"{df['env_quality_index'].min():.1f}"),
    ])

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    fg_env = folium.FeatureGroup(name="Environmental Quality")
    for _, row in df.iterrows():
        score = row.get("env_quality_index", 50)
        color = _score_color(score)
        radius = _score_radius(score)
        popup = (
            f"<div style='font-family:sans-serif;min-width:180px;'>"
            f"<b>{_safe(row.get('city', ''))}</b><br>"
            f"<span style='color:#06b6d4;'>Env Quality Index</span>: <b>{score:.1f}/100</b><br>"
            f"US AQI: {row.get('us_aqi', 'N/A')}<br>"
            f"PM2.5: {row.get('pm2_5', 'N/A')} ug/m3<br>"
            f"Temp: {row.get('temp_c', 'N/A')}C | Humidity: {row.get('humidity', 'N/A')}%<br>"
            f"NO2: {row.get('no2', 'N/A')} | CO: {row.get('co', 'N/A')}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=250),
            tooltip=f"{_safe(row.get('city', ''))}: EQI {score:.1f}",
        ).add_to(fg_env)
    fg_env.add_to(m)

    # AQ heatmap layer
    fg_aqi = folium.FeatureGroup(name="AQI Readings", show=False)
    for _, row in df.iterrows():
        aqi_val = row.get("us_aqi", 0) or 0
        color = _aqi_color(aqi_val)
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=6,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            tooltip=f"AQI: {aqi_val} ({_aqi_label(aqi_val)})",
        ).add_to(fg_aqi)
    fg_aqi.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m)

    # Chart
    chart_buf = _dark_bar_chart(df, "city", "env_quality_index",
                                "Environmental Quality by City", "#10b981", min(num_cities, 25))
    st.image(chart_buf, caption="Environmental Quality Index (higher = better)", width=700)

    # Data table
    show_cols = ["city", "env_quality_index", "us_aqi", "pm2_5", "temp_c", "humidity", "no2"]
    show_df = df[[c for c in show_cols if c in df.columns]].sort_values(
        "env_quality_index", ascending=False
    ).reset_index(drop=True)
    st.dataframe(show_df, width="stretch")
    _make_csv_download(show_df, "environmental_health.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 4: CONNECTIVITY & DEVELOPMENT
# ═══════════════════════════════════════════════════════════════════════

def _render_connectivity():
    """Connectivity & Development: REST Countries + World Bank internet + GDP."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**REST Countries** (population, area) + **World Bank Internet Penetration** + "
        "**World Bank GDP per capita** = **Digital Connectivity Score**"
    )

    with st.spinner("Fetching connectivity data from 3 APIs concurrently..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_countries = executor.submit(_fetch_rest_countries)
            f_internet = executor.submit(_fetch_wb_indicator, "IT.NET.USER.ZS", "2022")
            f_gdp = executor.submit(_fetch_wb_indicator, "NY.GDP.PCAP.CD", "2022")

            countries_df = f_countries.result()
            internet_df = f_internet.result()
            gdp_df = f_gdp.result()

    if countries_df.empty:
        st.error("Failed to fetch country data.")
        return

    df = countries_df.copy()
    df["pop_density"] = df["population"] / df["area_km2"].replace(0, np.nan)

    if not internet_df.empty:
        inet = internet_df.rename(columns={"wb_value": "internet_pct"})
        df = df.merge(inet[["cca2", "internet_pct"]], on="cca2", how="left")
    else:
        df["internet_pct"] = np.nan

    if not gdp_df.empty:
        gdp = gdp_df.rename(columns={"wb_value": "gdp_per_capita"})
        df = df.merge(gdp[["cca2", "gdp_per_capita"]], on="cca2", how="left")
    else:
        df["gdp_per_capita"] = np.nan

    # Connectivity score
    df["inet_score"] = _normalize(df["internet_pct"].fillna(0))
    df["gdp_score"] = _normalize(df["gdp_per_capita"].fillna(0))
    df["density_factor"] = _normalize(df["pop_density"].fillna(0).clip(0, 1000))

    df["connectivity_score"] = (
        df["inet_score"] * 0.50 +
        df["gdp_score"] * 0.35 +
        df["density_factor"] * 0.15
    ).round(1)

    df = df.dropna(subset=["lat", "lng"])
    df = df[df["connectivity_score"] > 0]

    _build_stats_row([
        ("Countries", str(len(df))),
        ("Avg Connectivity", f"{df['connectivity_score'].mean():.1f}"),
        ("Highest", f"{df['connectivity_score'].max():.1f}"),
        ("Lowest", f"{df['connectivity_score'].min():.1f}"),
    ])

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    fg = folium.FeatureGroup(name="Connectivity Score")
    for _, row in df.iterrows():
        score = row["connectivity_score"]
        color = _value_to_hex(score, 0, 100, "viridis")
        radius = _score_radius(score, 0, 100, 4, 16)
        popup = (
            f"<div style='font-family:sans-serif;min-width:180px;'>"
            f"<b>{_safe(row['country'])}</b><br>"
            f"<span style='color:#8b5cf6;'>Connectivity Score</span>: <b>{score:.1f}/100</b><br>"
            f"Internet: {row.get('internet_pct', 0):.1f}%<br>"
            f"GDP/capita: ${row.get('gdp_per_capita', 0):,.0f}<br>"
            f"Pop Density: {row.get('pop_density', 0):,.0f}/km2<br>"
            f"Region: {_safe(row.get('region', ''))}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=250),
            tooltip=f"{_safe(row['country'])}: {score:.1f}",
        ).add_to(fg)
    fg.add_to(m)

    # Submarine cable landing points (major known locations)
    fg_cables = folium.FeatureGroup(name="Major Cable Hubs", show=False)
    cable_hubs = [
        {"name": "Marseille", "lat": 43.30, "lon": 5.37, "cables": 15},
        {"name": "Singapore", "lat": 1.35, "lon": 103.82, "cables": 30},
        {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "cables": 12},
        {"name": "New York", "lat": 40.71, "lon": -74.01, "cables": 18},
        {"name": "Tokyo", "lat": 35.68, "lon": 139.65, "cables": 14},
        {"name": "Hong Kong", "lat": 22.32, "lon": 114.17, "cables": 16},
        {"name": "Sydney", "lat": -33.87, "lon": 151.21, "cables": 10},
        {"name": "London", "lat": 51.51, "lon": -0.13, "cables": 22},
        {"name": "Miami", "lat": 25.76, "lon": -80.19, "cables": 14},
        {"name": "Los Angeles", "lat": 34.05, "lon": -118.24, "cables": 12},
        {"name": "Dubai", "lat": 25.20, "lon": 55.27, "cables": 10},
        {"name": "Cape Town", "lat": -33.92, "lon": 18.42, "cables": 6},
    ]
    for hub in cable_hubs:
        folium.CircleMarker(
            location=[hub["lat"], hub["lon"]], radius=hub["cables"] * 0.5,
            color="#38bdf8", fill=True, fill_color="#38bdf8", fill_opacity=0.5,
            tooltip=f"{_safe(hub['name'])}: ~{hub['cables']} submarine cables",
        ).add_to(fg_cables)
    fg_cables.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m)

    chart_buf = _dark_bar_chart(df, "country", "connectivity_score",
                                "Top 20 Connectivity Scores", "#8b5cf6", 20)
    st.image(chart_buf, caption="Digital Connectivity Index", width=700)

    show_cols = ["country", "region", "connectivity_score", "internet_pct", "gdp_per_capita", "population"]
    show_df = df[[c for c in show_cols if c in df.columns]].sort_values(
        "connectivity_score", ascending=False
    ).reset_index(drop=True)
    st.dataframe(show_df, width="stretch")
    _make_csv_download(show_df, "connectivity_development.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 5: CLIMATE VULNERABILITY
# ═══════════════════════════════════════════════════════════════════════

def _render_climate_vulnerability():
    """Climate Vulnerability: temperature + coastal proximity + population density."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**Open-Meteo Weather** (temperature, extreme weather) + **REST Countries** "
        "(population density) + **Open-Meteo AQ** (air quality as environment proxy) "
        "= **Climate Vulnerability Index for coastal cities**"
    )

    # Filter to coastal cities primarily
    coastal_cities = [c for c in WORLD_CITIES if c.get("coastal", False)]
    num = st.slider("Coastal cities to analyze", 10, len(coastal_cities), min(25, len(coastal_cities)),
                     key="cv_num")
    subset = coastal_cities[:num]

    with st.spinner(f"Fetching climate data for {num} coastal cities..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_wx = executor.submit(_fetch_weather_batch, subset)
            f_aq = executor.submit(_fetch_aq_batch, subset)

            wx_list = f_wx.result()
            aq_list = f_aq.result()

    wx_df = pd.DataFrame(wx_list)
    aq_df = pd.DataFrame(aq_list)

    df = wx_df.merge(aq_df, on=["city", "lat", "lon"], how="outer", suffixes=("", "_aq"))

    # Climate vulnerability: high temp + high AQI + coastal = high vulnerability
    df["temp_risk"] = _normalize(df["temp_c"].fillna(20).clip(-10, 50))
    df["aqi_risk"] = _normalize(df["us_aqi"].fillna(30).clip(0, 300))
    df["wind_risk"] = _normalize(df["wind_speed"].fillna(10).clip(0, 100))
    df["coastal_factor"] = df["coastal"].apply(lambda x: 80 if x else 30)

    df["vulnerability_index"] = (
        df["temp_risk"] * 0.25 +
        df["aqi_risk"] * 0.25 +
        df["wind_risk"] * 0.20 +
        df["coastal_factor"] * 0.30
    ).round(1)

    df = df.dropna(subset=["lat", "lon"])

    _build_stats_row([
        ("Cities Analyzed", str(len(df))),
        ("Avg Vulnerability", f"{df['vulnerability_index'].mean():.1f}"),
        ("Most Vulnerable", f"{df['vulnerability_index'].max():.1f}"),
        ("Least Vulnerable", f"{df['vulnerability_index'].min():.1f}"),
    ])

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    fg = folium.FeatureGroup(name="Climate Vulnerability")
    for _, row in df.iterrows():
        score = row["vulnerability_index"]
        color = _score_color_inverse(score)
        radius = _score_radius(score, 0, 100, 5, 18)
        popup = (
            f"<div style='font-family:sans-serif;min-width:180px;'>"
            f"<b>{_safe(row.get('city', ''))}</b> ({_safe(row.get('country', ''))})<br>"
            f"<span style='color:#f59e0b;'>Vulnerability Index</span>: <b>{score:.1f}/100</b><br>"
            f"Temperature: {row.get('temp_c', 'N/A')}C<br>"
            f"US AQI: {row.get('us_aqi', 'N/A')}<br>"
            f"Wind: {row.get('wind_speed', 'N/A')} km/h<br>"
            f"Coastal: {'Yes' if row.get('coastal') else 'No'}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=250),
            tooltip=f"{_safe(row.get('city', ''))}: Vuln {score:.1f}",
        ).add_to(fg)
    fg.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map_html(m)

    chart_buf = _dark_bar_chart(df, "city", "vulnerability_index",
                                "Climate Vulnerability by City", "#f59e0b", min(num, 25))
    st.image(chart_buf, caption="Climate Vulnerability Index (higher = more vulnerable)", width=700)

    show_cols = ["city", "country", "vulnerability_index", "temp_c", "us_aqi",
                 "wind_speed", "coastal"]
    show_df = df[[c for c in show_cols if c in df.columns]].sort_values(
        "vulnerability_index", ascending=False
    ).reset_index(drop=True)
    st.dataframe(show_df, width="stretch")
    _make_csv_download(show_df, "climate_vulnerability.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 6: BIODIVERSITY VS DEVELOPMENT
# ═══════════════════════════════════════════════════════════════════════

def _render_biodiversity_development():
    """Biodiversity vs Development: GBIF + World Bank GDP + population."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**GBIF** (species occurrence counts per country) + **World Bank GDP** + "
        "**REST Countries** (population, area) = **Biodiversity Pressure Index**"
    )

    with st.spinner("Fetching biodiversity and development data from 3 APIs..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_gbif = executor.submit(_fetch_gbif_country_counts)
            f_gdp = executor.submit(_fetch_wb_indicator, "NY.GDP.PCAP.CD", "2022")
            f_countries = executor.submit(_fetch_rest_countries)

            gbif_df = f_gbif.result()
            gdp_df = f_gdp.result()
            countries_df = f_countries.result()

    if countries_df.empty:
        st.error("Failed to fetch country data.")
        return

    df = countries_df.copy()
    df["pop_density"] = df["population"] / df["area_km2"].replace(0, np.nan)

    if not gbif_df.empty:
        df = df.merge(gbif_df, on="cca2", how="left")
    else:
        df["species_count"] = 0

    if not gdp_df.empty:
        gdp = gdp_df.rename(columns={"wb_value": "gdp_per_capita"})
        df = df.merge(gdp[["cca2", "gdp_per_capita"]], on="cca2", how="left")
    else:
        df["gdp_per_capita"] = np.nan

    df["species_count"] = df["species_count"].fillna(0)
    df["species_density"] = df["species_count"] / df["area_km2"].replace(0, np.nan)

    # Biodiversity pressure: high GDP + high density + low species = high pressure
    df["dev_score"] = _normalize(df["gdp_per_capita"].fillna(0))
    df["density_pressure"] = _normalize(df["pop_density"].fillna(0).clip(0, 2000))
    df["bio_richness"] = _normalize(df["species_density"].fillna(0))

    df["pressure_index"] = (
        df["dev_score"] * 0.30 +
        df["density_pressure"] * 0.40 +
        (100 - df["bio_richness"]) * 0.30
    ).round(1)

    df = df.dropna(subset=["lat", "lng"])
    df = df[df["species_count"] > 0]

    _build_stats_row([
        ("Countries", str(len(df))),
        ("Total Species Records", f"{df['species_count'].sum():,.0f}"),
        ("Avg Pressure Index", f"{df['pressure_index'].mean():.1f}"),
        ("Data Sources", "3 APIs"),
    ])

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    fg_bio = folium.FeatureGroup(name="Biodiversity Density", show=True)
    fg_pressure = folium.FeatureGroup(name="Pressure Index", show=False)

    vmin_sp = df["species_density"].min()
    vmax_sp = df["species_density"].max()

    for _, row in df.iterrows():
        # Biodiversity layer
        sp_d = row.get("species_density", 0) or 0
        bio_color = _value_to_hex(sp_d, vmin_sp, vmax_sp, "YlGn")
        bio_radius = _score_radius(sp_d, vmin_sp, vmax_sp, 4, 15)
        popup_bio = (
            f"<div style='font-family:sans-serif;min-width:180px;'>"
            f"<b>{_safe(row['country'])}</b><br>"
            f"Species Records: {row.get('species_count', 0):,.0f}<br>"
            f"Species/km2: {sp_d:,.2f}<br>"
            f"GDP/capita: ${row.get('gdp_per_capita', 0):,.0f}<br>"
            f"Pop Density: {row.get('pop_density', 0):,.0f}/km2"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=bio_radius,
            color=bio_color, fill=True, fill_color=bio_color, fill_opacity=0.6,
            popup=folium.Popup(popup_bio, max_width=250),
            tooltip=f"{_safe(row['country'])}: {row.get('species_count', 0):,.0f} species",
        ).add_to(fg_bio)

        # Pressure layer
        pressure = row.get("pressure_index", 50)
        pr_color = _score_color_inverse(pressure)
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=_score_radius(pressure),
            color=pr_color, fill=True, fill_color=pr_color, fill_opacity=0.6,
            tooltip=f"{_safe(row['country'])}: Pressure {pressure:.1f}",
        ).add_to(fg_pressure)

    fg_bio.add_to(m)
    fg_pressure.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m)

    chart_buf = _dark_bar_chart(df, "country", "pressure_index",
                                "Top 20 Biodiversity Pressure Index", "#22c55e", 20)
    st.image(chart_buf, caption="Biodiversity Pressure Index (higher = more pressure)", width=700)

    show_cols = ["country", "region", "pressure_index", "species_count",
                 "species_density", "gdp_per_capita", "pop_density"]
    show_df = df[[c for c in show_cols if c in df.columns]].sort_values(
        "pressure_index", ascending=False
    ).reset_index(drop=True)
    st.dataframe(show_df, width="stretch")
    _make_csv_download(show_df, "biodiversity_pressure.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 7: HISTORICAL LAYER FUSION
# ═══════════════════════════════════════════════════════════════════════

def _render_historical_fusion():
    """Historical Layer Fusion: ancient sites + modern countries + population."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**Historical Landmark Database** (20+ ancient sites/empires) + "
        "**REST Countries** (current borders, capitals) + **World Bank Population** "
        "= **Then vs Now overlay map**"
    )

    with st.spinner("Fetching modern country data..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_countries = executor.submit(_fetch_rest_countries)
            f_pop = executor.submit(_fetch_wb_indicator, "SP.POP.TOTL", "2022")

            countries_df = f_countries.result()
            pop_df = f_pop.result()

    if countries_df.empty:
        st.error("Failed to fetch country data.")
        return

    df_modern = countries_df.copy()
    if not pop_df.empty:
        pop = pop_df.rename(columns={"wb_value": "wb_population"})
        df_modern = df_modern.merge(pop[["cca2", "wb_population"]], on="cca2", how="left")

    hist_df = pd.DataFrame(HISTORICAL_SITES)

    _build_stats_row([
        ("Historical Sites", str(len(hist_df))),
        ("Modern Countries", str(len(df_modern))),
        ("Empires Represented", str(hist_df["empire"].nunique())),
        ("Time Span", "3100 BC - Present"),
    ])

    m = folium.Map(location=[25, 30], zoom_start=2, tiles="CartoDB dark_matter")

    # Historical sites layer
    fg_hist = folium.FeatureGroup(name="Ancient Sites & Empires", show=True)
    empire_colors = {
        "Roman Empire": "#ef4444", "Greek City-States": "#38bdf8",
        "Ptolemaic Egypt": "#f59e0b", "Byzantine Empire": "#8b5cf6",
        "Babylonian Empire": "#f97316", "Ancient Egypt": "#f59e0b",
        "Achaemenid Empire": "#ec4899", "Han Dynasty": "#ef4444",
        "Aztec Empire": "#10b981", "Inca Empire": "#22c55e",
        "Carthaginian Empire": "#dc2626", "Khmer Empire": "#06b6d4",
        "Timurid Empire": "#a855f7", "Mali Empire": "#f59e0b",
        "Kingdom of Zimbabwe": "#10b981", "Indus Valley": "#3b82f6",
        "Heian Japan": "#ec4899", "Abbasid Caliphate": "#22c55e",
        "Tibetan Empire": "#8b5cf6",
    }

    for _, row in hist_df.iterrows():
        empire = row.get("empire", "")
        color = empire_colors.get(empire, "#f97316")
        popup = (
            f"<div style='font-family:sans-serif;min-width:200px;'>"
            f"<b style='font-size:13px;color:{color};'>{_safe(row['name'])}</b><br>"
            f"<b>Era:</b> {_safe(row['era'])}<br>"
            f"<b>Empire:</b> {_safe(empire)}<br>"
            f"<i>{_safe(row.get('desc', ''))}</i>"
            f"</div>"
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{_safe(row['name'])} ({_safe(row['era'])})",
            icon=folium.Icon(color="red", icon="monument", prefix="fa"),
        ).add_to(fg_hist)
    fg_hist.add_to(m)

    # Modern capitals layer
    fg_modern = folium.FeatureGroup(name="Modern Capitals", show=True)
    for _, row in df_modern.iterrows():
        cap = row.get("capital", "")
        if not cap:
            continue
        pop = row.get("population", 0)
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{_safe(row['country'])}</b><br>"
            f"Capital: {_safe(cap)}<br>"
            f"Population: {pop:,.0f}<br>"
            f"Region: {_safe(row.get('region', ''))}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=max(3, min(12, pop / 50_000_000)),
            color="#06b6d4", fill=True, fill_color="#06b6d4", fill_opacity=0.3,
            popup=folium.Popup(popup, max_width=200),
            tooltip=f"{_safe(row['country'])} ({_safe(cap)})",
        ).add_to(fg_modern)
    fg_modern.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m, height=550)

    st.markdown("**Historical Sites Database**")
    st.dataframe(hist_df, width="stretch")
    _make_csv_download(hist_df, "historical_sites.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 8: RESOURCE VS CONFLICT
# ═══════════════════════════════════════════════════════════════════════

def _render_resource_conflict():
    """Resource vs Conflict: minerals + military spending + GDP."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**Mining/Mineral Locations** (20 major sites) + **World Bank Military Spending** (% GDP) + "
        "**World Bank GDP** + **REST Countries** = **Resource-Conflict Correlation Map**"
    )

    with st.spinner("Fetching resource and conflict data from 3 APIs..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_countries = executor.submit(_fetch_rest_countries)
            f_military = executor.submit(_fetch_wb_indicator, "MS.MIL.XPND.GD.ZS", "2022")
            f_gdp = executor.submit(_fetch_wb_indicator, "NY.GDP.PCAP.CD", "2022")

            countries_df = f_countries.result()
            mil_df = f_military.result()
            gdp_df = f_gdp.result()

    if countries_df.empty:
        st.error("Failed to fetch country data.")
        return

    df = countries_df.copy()

    if not mil_df.empty:
        mil = mil_df.rename(columns={"wb_value": "military_pct_gdp"})
        df = df.merge(mil[["cca2", "military_pct_gdp"]], on="cca2", how="left")
    else:
        df["military_pct_gdp"] = np.nan

    if not gdp_df.empty:
        gdp = gdp_df.rename(columns={"wb_value": "gdp_per_capita"})
        df = df.merge(gdp[["cca2", "gdp_per_capita"]], on="cca2", how="left")
    else:
        df["gdp_per_capita"] = np.nan

    # Conflict pressure: high military spending + low GDP = high pressure
    df["mil_score"] = _normalize(df["military_pct_gdp"].fillna(0))
    df["gdp_inv"] = 100 - _normalize(df["gdp_per_capita"].fillna(0))
    df["conflict_pressure"] = (
        df["mil_score"] * 0.60 + df["gdp_inv"] * 0.40
    ).round(1)

    df = df.dropna(subset=["lat", "lng"])
    resource_df = pd.DataFrame(RESOURCE_LOCATIONS)

    _build_stats_row([
        ("Countries w/ Data", str(len(df[df["military_pct_gdp"].notna()]))),
        ("Resource Sites", str(len(resource_df))),
        ("Avg Military % GDP", f"{df['military_pct_gdp'].mean():.2f}%"),
        ("Data Sources", "3 APIs + Resource DB"),
    ])

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # Resource locations
    fg_res = folium.FeatureGroup(name="Major Resource Sites", show=True)
    resource_colors = {
        "Gold": "#f59e0b", "Iron Ore": "#ef4444", "Cobalt/Copper": "#06b6d4",
        "Lithium/Copper": "#10b981", "Nickel/Palladium": "#8b5cf6",
        "Gold/Copper": "#f97316", "Gold/Silver": "#f59e0b",
        "Nickel": "#8b5cf6", "Uranium/Copper": "#22c55e",
        "Diamonds": "#38bdf8", "Silver/Tin": "#8b97b0", "Rare Earths": "#ec4899",
        "Copper": "#f97316", "Iron Ore": "#ef4444",
    }
    for _, row in resource_df.iterrows():
        res = row.get("resource", "")
        color = resource_colors.get(res, "#f59e0b")
        popup = (
            f"<div style='font-family:sans-serif;min-width:160px;'>"
            f"<b>{_safe(row['name'])}</b><br>"
            f"Resource: {_safe(res)}<br>"
            f"Country: {_safe(row.get('country', ''))}"
            f"</div>"
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup, max_width=220),
            tooltip=f"{_safe(row['name'])}: {_safe(res)}",
            icon=folium.Icon(color="orange", icon="gem", prefix="fa"),
        ).add_to(fg_res)
    fg_res.add_to(m)

    # Military spending layer
    fg_mil = folium.FeatureGroup(name="Military Spending", show=True)
    mil_countries = df[df["military_pct_gdp"].notna()]
    vmin = mil_countries["military_pct_gdp"].min() if not mil_countries.empty else 0
    vmax = mil_countries["military_pct_gdp"].max() if not mil_countries.empty else 10
    for _, row in mil_countries.iterrows():
        mil_pct = row.get("military_pct_gdp", 0)
        color = _value_to_hex(mil_pct, vmin, vmax, "OrRd")
        radius = _score_radius(mil_pct, vmin, vmax, 4, 14)
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{_safe(row['country'])}</b><br>"
            f"Military: {mil_pct:.2f}% GDP<br>"
            f"GDP/capita: ${row.get('gdp_per_capita', 0):,.0f}<br>"
            f"Conflict Pressure: {row.get('conflict_pressure', 0):.1f}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.5,
            popup=folium.Popup(popup, max_width=220),
            tooltip=f"{_safe(row['country'])}: {mil_pct:.2f}% GDP on military",
        ).add_to(fg_mil)
    fg_mil.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m, height=550)

    chart_buf = _dark_bar_chart(df[df["military_pct_gdp"].notna()], "country",
                                "military_pct_gdp",
                                "Top 20 Military Spending (% GDP)", "#dc2626", 20)
    st.image(chart_buf, caption="Military Spending as % of GDP", width=700)

    show_cols = ["country", "region", "conflict_pressure", "military_pct_gdp",
                 "gdp_per_capita", "population"]
    show_df = df[[c for c in show_cols if c in df.columns]].sort_values(
        "conflict_pressure", ascending=False
    ).reset_index(drop=True)
    st.dataframe(show_df.head(100), width="stretch")
    _make_csv_download(show_df, "resource_conflict.csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE 9: TOURISM POTENTIAL
# ═══════════════════════════════════════════════════════════════════════

def _render_tourism_potential():
    """Tourism Potential: UNESCO sites + REST Countries + climate + safety."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**UNESCO World Heritage Sites** (30 major sites) + **REST Countries** (population, area) + "
        "**Open-Meteo Climate** (temperature comfort) + **World Bank Tourism Arrivals** "
        "= **Tourism Attractiveness Composite**"
    )

    with st.spinner("Fetching tourism data from 4 APIs..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            f_countries = executor.submit(_fetch_rest_countries)
            f_tourism = executor.submit(_fetch_wb_indicator, "ST.INT.ARVL", "2020")
            f_gdp = executor.submit(_fetch_wb_indicator, "NY.GDP.PCAP.CD", "2022")
            # Fetch weather for UNESCO site locations
            unesco_as_cities = [
                {"name": s["name"], "lat": s["lat"], "lon": s["lon"],
                 "country": s["country"]}
                for s in UNESCO_SITES[:20]
            ]
            f_wx = executor.submit(_fetch_weather_batch, unesco_as_cities)

            countries_df = f_countries.result()
            tourism_df = f_tourism.result()
            gdp_df = f_gdp.result()
            wx_list = f_wx.result()

    if countries_df.empty:
        st.error("Failed to fetch country data.")
        return

    df = countries_df.copy()
    df["pop_density"] = df["population"] / df["area_km2"].replace(0, np.nan)

    if not tourism_df.empty:
        tour = tourism_df.rename(columns={"wb_value": "tourism_arrivals"})
        df = df.merge(tour[["cca2", "tourism_arrivals"]], on="cca2", how="left")
    else:
        df["tourism_arrivals"] = np.nan

    if not gdp_df.empty:
        gdp = gdp_df.rename(columns={"wb_value": "gdp_per_capita"})
        df = df.merge(gdp[["cca2", "gdp_per_capita"]], on="cca2", how="left")
    else:
        df["gdp_per_capita"] = np.nan

    # Count UNESCO sites per country
    unesco_df = pd.DataFrame(UNESCO_SITES)
    site_counts = unesco_df.groupby("country").size().reset_index(name="unesco_count")

    # Tourism composite for countries
    df["tourism_score"] = _normalize(df["tourism_arrivals"].fillna(0))
    df["gdp_score"] = _normalize(df["gdp_per_capita"].fillna(0))
    df["attractiveness"] = (
        df["tourism_score"] * 0.50 + df["gdp_score"] * 0.50
    ).round(1)

    df = df.dropna(subset=["lat", "lng"])

    # Weather data for UNESCO sites
    wx_df = pd.DataFrame(wx_list) if wx_list else pd.DataFrame()

    _build_stats_row([
        ("UNESCO Sites Mapped", str(len(UNESCO_SITES))),
        ("Countries w/ Tourism Data", str(len(df[df["tourism_arrivals"].notna()]))),
        ("Total Arrivals (data)", f"{df['tourism_arrivals'].sum():,.0f}"),
        ("Data Sources", "4 APIs"),
    ])

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # UNESCO sites layer
    fg_unesco = folium.FeatureGroup(name="UNESCO World Heritage Sites", show=True)
    type_colors = {"Cultural": "#f59e0b", "Natural": "#10b981", "Mixed": "#8b5cf6"}
    for i, site in enumerate(UNESCO_SITES):
        color = type_colors.get(site["type"], "#06b6d4")
        # Attach weather if available
        weather_info = ""
        if not wx_df.empty and i < len(wx_df):
            wr = wx_df.iloc[i]
            if wr.get("temp_c") is not None:
                weather_info = f"<br>Current: {wr['temp_c']}C, {WMO_DESC.get(int(wr.get('weather_code', 0)), 'N/A')}"

        popup = (
            f"<div style='font-family:sans-serif;min-width:180px;'>"
            f"<b style='color:{color};'>{_safe(site['name'])}</b><br>"
            f"Country: {_safe(site['country'])}<br>"
            f"Type: {_safe(site['type'])}"
            f"{weather_info}"
            f"</div>"
        )
        icon_name = "landmark" if site["type"] == "Cultural" else "tree"
        folium.Marker(
            location=[site["lat"], site["lon"]],
            popup=folium.Popup(popup, max_width=250),
            tooltip=f"{_safe(site['name'])} ({_safe(site['type'])})",
            icon=folium.Icon(color="green" if site["type"] == "Natural" else "orange",
                             icon=icon_name, prefix="fa"),
        ).add_to(fg_unesco)
    fg_unesco.add_to(m)

    # Tourism arrivals by country
    fg_tour = folium.FeatureGroup(name="Tourism Arrivals", show=False)
    tour_countries = df[df["tourism_arrivals"].notna()]
    if not tour_countries.empty:
        tvmin = tour_countries["tourism_arrivals"].min()
        tvmax = tour_countries["tourism_arrivals"].max()
        for _, row in tour_countries.iterrows():
            arr = row.get("tourism_arrivals", 0)
            color = _value_to_hex(arr, tvmin, tvmax, "YlGnBu")
            radius = _score_radius(arr, tvmin, tvmax, 4, 16)
            popup = (
                f"<div style='font-family:sans-serif;'>"
                f"<b>{_safe(row['country'])}</b><br>"
                f"Arrivals: {arr:,.0f}<br>"
                f"GDP/capita: ${row.get('gdp_per_capita', 0):,.0f}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lng"]], radius=radius,
                color=color, fill=True, fill_color=color, fill_opacity=0.6,
                popup=folium.Popup(popup, max_width=200),
                tooltip=f"{_safe(row['country'])}: {arr:,.0f} arrivals",
            ).add_to(fg_tour)
    fg_tour.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m, height=550)

    st.markdown("**UNESCO World Heritage Sites**")
    st.dataframe(unesco_df, width="stretch")
    _make_csv_download(unesco_df, "unesco_sites.csv")

    if not tour_countries.empty:
        chart_buf = _dark_bar_chart(tour_countries, "country", "tourism_arrivals",
                                    "Top 20 Tourism Destinations", "#ec4899", 20)
        st.image(chart_buf, caption="International Tourism Arrivals", width=700)


# ═══════════════════════════════════════════════════════════════════════
# MODE 10: REAL-TIME EARTH DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

def _render_realtime_dashboard():
    """Real-Time Earth Dashboard: earthquakes + weather + AQ + ISS."""
    st.markdown("#### Data Sources Being Combined")
    st.info(
        "**USGS Earthquakes** (live feed, last 24h) + **Open-Meteo Weather** (30 cities) + "
        "**Open-Meteo Air Quality** (30 cities) + **ISS Position** (real-time) "
        "= **Unified Real-Time Earth View**"
    )

    with st.spinner("Fetching real-time data from 4 APIs concurrently..."):
        cities_30 = WORLD_CITIES[:30]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            f_eq = executor.submit(_fetch_earthquakes, 1, 2.5)
            f_wx = executor.submit(_fetch_weather_batch, cities_30)
            f_aq = executor.submit(_fetch_aq_batch, cities_30)
            f_iss = executor.submit(_fetch_iss_position)

            eq_df = f_eq.result()
            wx_list = f_wx.result()
            aq_list = f_aq.result()
            iss = f_iss.result()

    wx_df = pd.DataFrame(wx_list)
    aq_df = pd.DataFrame(aq_list)

    _build_stats_row([
        ("Earthquakes (24h)", str(len(eq_df))),
        ("Weather Stations", str(len(wx_df))),
        ("AQ Monitors", str(len(aq_df))),
        ("ISS Position", f"{iss['lat']:.2f}, {iss['lon']:.2f}"),
    ])

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # ISS position
    fg_iss = folium.FeatureGroup(name="ISS Position", show=True)
    folium.Marker(
        location=[iss["lat"], iss["lon"]],
        tooltip="International Space Station",
        popup=f"<b>ISS</b><br>Lat: {iss['lat']:.4f}<br>Lon: {iss['lon']:.4f}",
        icon=folium.Icon(color="blue", icon="satellite", prefix="fa"),
    ).add_to(fg_iss)
    # ISS orbit circle
    folium.Circle(
        location=[iss["lat"], iss["lon"]], radius=2200000,
        color="#38bdf8", fill=False, weight=1, dash_array="5",
        tooltip="ISS visibility footprint (~2200 km)",
    ).add_to(fg_iss)
    fg_iss.add_to(m)

    # Earthquakes layer
    fg_eq = folium.FeatureGroup(name="Earthquakes (24h)", show=True)
    if not eq_df.empty:
        for _, row in eq_df.iterrows():
            mag = row.get("mag", 0) or 0
            popup = (
                f"<div style='font-family:sans-serif;'>"
                f"<b>M{mag:.1f}</b> - {_safe(row.get('place', ''))}<br>"
                f"Time: {_safe(row.get('time', ''))}<br>"
                f"Depth: {row.get('depth_km', 0):.1f} km"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=_mag_radius(mag),
                color=_mag_color(mag), fill=True, fill_color=_mag_color(mag),
                fill_opacity=0.65, popup=folium.Popup(popup, max_width=200),
                tooltip=f"M{mag:.1f}",
            ).add_to(fg_eq)
    fg_eq.add_to(m)

    # Weather layer
    fg_wx = folium.FeatureGroup(name="City Weather", show=True)
    if not wx_df.empty:
        for _, row in wx_df.iterrows():
            temp = row.get("temp_c")
            if temp is None:
                continue
            wcode = int(row.get("weather_code", 0) or 0)
            desc = WMO_DESC.get(wcode, "Unknown")
            color = _temp_color(temp)
            popup = (
                f"<div style='font-family:sans-serif;'>"
                f"<b>{_safe(row.get('city', ''))}</b><br>"
                f"Temp: {temp}C (feels {row.get('feels_like', 'N/A')}C)<br>"
                f"Weather: {_safe(desc)}<br>"
                f"Wind: {row.get('wind_speed', 0):.0f} km/h<br>"
                f"Humidity: {row.get('humidity', 0)}%"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=7,
                color=color, fill=True, fill_color=color, fill_opacity=0.7,
                popup=folium.Popup(popup, max_width=200),
                tooltip=f"{_safe(row.get('city', ''))}: {temp}C, {_safe(desc)}",
            ).add_to(fg_wx)
    fg_wx.add_to(m)

    # Air quality layer
    fg_aq = folium.FeatureGroup(name="Air Quality", show=False)
    if not aq_df.empty:
        for _, row in aq_df.iterrows():
            aqi = row.get("us_aqi")
            if aqi is None:
                continue
            color = _aqi_color(aqi)
            label = _aqi_label(aqi)
            popup = (
                f"<div style='font-family:sans-serif;'>"
                f"<b>{_safe(row.get('city', ''))}</b><br>"
                f"US AQI: {aqi} ({_safe(label)})<br>"
                f"PM2.5: {row.get('pm2_5', 'N/A')} ug/m3<br>"
                f"PM10: {row.get('pm10', 'N/A')} ug/m3"
                f"</div>"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=8,
                color=color, fill=True, fill_color=color, fill_opacity=0.6,
                popup=folium.Popup(popup, max_width=200),
                tooltip=f"AQI: {aqi} ({_safe(label)})",
            ).add_to(fg_aq)
    fg_aq.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    _render_map_html(m, height=600)

    # Summary chart: temperature distribution
    if not wx_df.empty and wx_df["temp_c"].notna().any():
        fig, ax = _dark_fig(figsize=(10, 4))
        valid_wx = wx_df[wx_df["temp_c"].notna()].sort_values("temp_c", ascending=True)
        colors_list = [_temp_color(t) for t in valid_wx["temp_c"]]
        ax.barh(valid_wx["city"].astype(str), valid_wx["temp_c"], color=colors_list, edgecolor="#2a3550")
        ax.set_title("Current Temperatures Worldwide", color="#e8ecf4", fontsize=11, pad=10)
        ax.set_xlabel("Temperature (C)", color="#8b97b0", fontsize=9)
        ax.axvline(x=0, color="#5a6580", linewidth=0.5, linestyle="--")
        buf = _fig_to_buf(fig)
        st.image(buf, caption="Real-time temperature readings from 30 cities", width=700)

    # Data tables
    col_l, col_r = st.columns(2)
    with col_l:
        if not wx_df.empty:
            st.markdown("**City Weather**")
            st.dataframe(wx_df[["city", "temp_c", "humidity", "wind_speed"]].dropna(), width="stretch")
    with col_r:
        if not aq_df.empty:
            st.markdown("**Air Quality**")
            st.dataframe(aq_df[["city", "us_aqi", "pm2_5", "pm10"]].dropna(), width="stretch")

    if not eq_df.empty:
        st.markdown("**Earthquakes (last 24 hours)**")
        st.dataframe(eq_df, width="stretch")

    # Combined download
    combined_parts = []
    if not eq_df.empty:
        e = eq_df.copy()
        e["source"] = "USGS Earthquake"
        combined_parts.append(e)
    if not wx_df.empty:
        w = wx_df.copy()
        w["source"] = "Open-Meteo Weather"
        combined_parts.append(w)
    if not aq_df.empty:
        a = aq_df.copy()
        a["source"] = "Open-Meteo AQ"
        combined_parts.append(a)
    if combined_parts:
        combined = pd.concat(combined_parts, ignore_index=True)
        _make_csv_download(combined, "realtime_earth_dashboard.csv")


# ═══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def render_composite_maps_tab():
    """Main entry point for the Composite Data Aggregator tab."""
    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>\U0001f504 Composite Data Aggregator</h4>'
        '<p>Multi-source fusion maps combining live data from multiple APIs</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "Select a composite map mode below. Each mode fetches data from **multiple free APIs** "
        "concurrently, merges them into a unified dataset, computes composite scores, and "
        "renders a layered interactive map with toggle-able feature groups."
    )

    # Mode selector
    mode_labels = list(MAP_MODES.keys())
    selected_mode = st.selectbox(
        "Composite Map Mode",
        mode_labels,
        key="composite_mode_select",
        help="Each mode combines 2-5 different data sources into a unique visualization.",
    )

    # Show mode description
    mode_info = MAP_MODES[selected_mode]
    st.markdown(
        f"<div style='background:#111827;padding:12px 16px;border-radius:8px;"
        f"border-left:4px solid {mode_info['color']};margin-bottom:16px;'>"
        f"<b style='color:{mode_info['color']};'>{selected_mode}</b><br>"
        f"<span style='color:#8b97b0;'>{mode_info['desc']}</span><br>"
        f"<span style='color:#5a6580;font-size:0.85em;'>Sources: {', '.join(mode_info['sources'])}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Dispatch to mode renderer
    mode_renderers = {
        "Livability Index": _render_livability,
        "Natural Hazard Risk": _render_hazard_risk,
        "Environmental Health": _render_environmental_health,
        "Connectivity & Development": _render_connectivity,
        "Climate Vulnerability": _render_climate_vulnerability,
        "Biodiversity vs Development": _render_biodiversity_development,
        "Historical Layer Fusion": _render_historical_fusion,
        "Resource vs Conflict": _render_resource_conflict,
        "Tourism Potential": _render_tourism_potential,
        "Real-Time Earth Dashboard": _render_realtime_dashboard,
    }

    renderer = mode_renderers.get(selected_mode)
    if renderer:
        try:
            renderer()
        except Exception as exc:
            logger.error("Composite map mode '%s' failed: %s", selected_mode, exc)
            st.error(f"An error occurred while rendering '{selected_mode}': {exc}")
            st.info("This may be due to an API being temporarily unavailable. Please try again.")
    else:
        st.warning(f"Mode '{selected_mode}' is not yet implemented.")
