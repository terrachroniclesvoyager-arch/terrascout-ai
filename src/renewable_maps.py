# -*- coding: utf-8 -*-
"""
Renewable Energy & Green Maps module for TerraScout AI.
Displays solar farms, wind farms, hydroelectric dams, geothermal plants,
tidal/wave energy, biomass, green hydrogen, solar/wind potential, and
EV infrastructure on interactive maps with curated global datasets.

Data sources:
  - Overpass API (OSM): power=generator, generator:source=solar|wind|hydro|geothermal
  - Curated datasets of major installations worldwide
  - All free, no API key required.
"""

import io
import logging
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_GREEN = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_PINK = "#ec4899"
ACCENT_BLUE = "#3b82f6"
ACCENT_ORANGE = "#f97316"
ACCENT_TEAL = "#14b8a6"
ACCENT_LIME = "#84cc16"

# ═══════════════════════════════════════════════════════════════════
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════
MAP_MODES = [
    "1. Solar Farms Worldwide",
    "2. Wind Farms",
    "3. Hydroelectric Dams",
    "4. Geothermal Plants",
    "5. Tidal & Wave Energy",
    "6. Biomass & Bioenergy",
    "7. Green Hydrogen",
    "8. Solar Potential Map",
    "9. Wind Potential Map",
    "10. Electric Vehicle Infrastructure",
]

# ═══════════════════════════════════════════════════════════════════
# 1. SOLAR FARMS — Curated dataset of major installations
# ═══════════════════════════════════════════════════════════════════
SOLAR_FARMS = [
    {"name": "Bhadla Solar Park", "country": "India", "state": "Rajasthan",
     "lat": 27.539, "lon": 71.07, "capacity_mw": 2245, "area_km2": 56.0,
     "year": 2020, "type": "PV", "notes": "World's largest solar park"},
    {"name": "Huanghe Hydropower Hainan Solar Park", "country": "China", "state": "Qinghai",
     "lat": 36.30, "lon": 100.60, "capacity_mw": 2200, "area_km2": 56.0,
     "year": 2020, "type": "PV", "notes": "High-altitude plateau installation"},
    {"name": "Pavagada Solar Park", "country": "India", "state": "Karnataka",
     "lat": 14.10, "lon": 77.28, "capacity_mw": 2050, "area_km2": 53.0,
     "year": 2019, "type": "PV", "notes": "Shakti Sthala solar park"},
    {"name": "Benban Solar Park", "country": "Egypt", "state": "Aswan",
     "lat": 24.45, "lon": 32.72, "capacity_mw": 1650, "area_km2": 37.0,
     "year": 2019, "type": "PV", "notes": "Largest solar park in Africa"},
    {"name": "Tengger Desert Solar Park", "country": "China", "state": "Ningxia",
     "lat": 37.50, "lon": 104.95, "capacity_mw": 1547, "area_km2": 43.0,
     "year": 2017, "type": "PV", "notes": "Great Wall of Solar"},
    {"name": "Noor-Ouarzazate Solar Complex", "country": "Morocco", "state": "Draa-Tafilalet",
     "lat": 31.03, "lon": -6.86, "capacity_mw": 580, "area_km2": 30.0,
     "year": 2018, "type": "CSP+PV", "notes": "Concentrated solar + PV hybrid"},
    {"name": "Mohammed bin Rashid Al Maktoum Solar Park", "country": "UAE", "state": "Dubai",
     "lat": 24.75, "lon": 55.37, "capacity_mw": 5000, "area_km2": 77.0,
     "year": 2030, "type": "PV+CSP", "notes": "Target 5 GW by 2030"},
    {"name": "Villanueva Solar Park", "country": "Mexico", "state": "Coahuila",
     "lat": 25.32, "lon": -100.99, "capacity_mw": 828, "area_km2": 24.0,
     "year": 2018, "type": "PV", "notes": "Largest solar plant in the Americas"},
    {"name": "Topaz Solar Farm", "country": "USA", "state": "California",
     "lat": 35.38, "lon": -120.04, "capacity_mw": 550, "area_km2": 25.0,
     "year": 2014, "type": "PV", "notes": "San Luis Obispo County"},
    {"name": "Solar Star", "country": "USA", "state": "California",
     "lat": 34.83, "lon": -118.39, "capacity_mw": 579, "area_km2": 13.0,
     "year": 2015, "type": "PV", "notes": "Kern & Los Angeles counties"},
    {"name": "Longyangxia Dam Solar Park", "country": "China", "state": "Qinghai",
     "lat": 35.93, "lon": 100.62, "capacity_mw": 850, "area_km2": 27.0,
     "year": 2015, "type": "PV", "notes": "Hybrid hydro-solar operation"},
    {"name": "Kamuthi Solar Power Project", "country": "India", "state": "Tamil Nadu",
     "lat": 9.35, "lon": 78.37, "capacity_mw": 648, "area_km2": 10.0,
     "year": 2016, "type": "PV", "notes": "Single-location solar plant"},
    {"name": "Cestas Solar Park", "country": "France", "state": "Nouvelle-Aquitaine",
     "lat": 44.73, "lon": -0.78, "capacity_mw": 300, "area_km2": 2.5,
     "year": 2015, "type": "PV", "notes": "Largest solar farm in Europe (at build)"},
    {"name": "Ivanpah Solar Electric", "country": "USA", "state": "California",
     "lat": 35.56, "lon": -115.47, "capacity_mw": 392, "area_km2": 14.0,
     "year": 2014, "type": "CSP", "notes": "Concentrated solar power towers"},
    {"name": "Copper Mountain Solar", "country": "USA", "state": "Nevada",
     "lat": 35.79, "lon": -115.01, "capacity_mw": 802, "area_km2": 16.0,
     "year": 2021, "type": "PV", "notes": "Largest solar PV in Nevada"},
    {"name": "Rewa Ultra Mega Solar", "country": "India", "state": "Madhya Pradesh",
     "lat": 24.53, "lon": 81.30, "capacity_mw": 750, "area_km2": 6.4,
     "year": 2018, "type": "PV", "notes": "Supplies Delhi Metro"},
    {"name": "Kurnool Ultra Mega Solar Park", "country": "India", "state": "Andhra Pradesh",
     "lat": 15.83, "lon": 78.04, "capacity_mw": 1000, "area_km2": 24.0,
     "year": 2017, "type": "PV", "notes": "Andhra Pradesh's flagship park"},
    {"name": "Sakaka Solar Project", "country": "Saudi Arabia", "state": "Al Jouf",
     "lat": 29.97, "lon": 40.21, "capacity_mw": 300, "area_km2": 6.0,
     "year": 2021, "type": "PV", "notes": "First utility-scale solar in Saudi Arabia"},
    {"name": "Solarpark Meuro", "country": "Germany", "state": "Brandenburg",
     "lat": 51.50, "lon": 13.77, "capacity_mw": 166, "area_km2": 2.0,
     "year": 2012, "type": "PV", "notes": "Built on former coal mine"},
    {"name": "Witznitz Energy Park", "country": "Germany", "state": "Saxony",
     "lat": 51.14, "lon": 12.42, "capacity_mw": 650, "area_km2": 5.0,
     "year": 2024, "type": "PV", "notes": "Largest solar plant in Europe"},
]

# ═══════════════════════════════════════════════════════════════════
# 2. WIND FARMS — Curated dataset
# ═══════════════════════════════════════════════════════════════════
WIND_FARMS = [
    {"name": "Hornsea 2", "country": "UK", "state": "North Sea",
     "lat": 53.88, "lon": 1.79, "capacity_mw": 1386, "turbines": 165,
     "year": 2022, "type": "Offshore", "notes": "World's largest offshore wind farm (at commissioning)"},
    {"name": "Hornsea 1", "country": "UK", "state": "North Sea",
     "lat": 53.88, "lon": 2.10, "capacity_mw": 1218, "turbines": 174,
     "year": 2020, "type": "Offshore", "notes": "120 km off Yorkshire coast"},
    {"name": "Dogger Bank A", "country": "UK", "state": "North Sea",
     "lat": 54.75, "lon": 2.00, "capacity_mw": 1200, "turbines": 95,
     "year": 2024, "type": "Offshore", "notes": "GE Haliade-X 13 MW turbines"},
    {"name": "Gansu Wind Farm", "country": "China", "state": "Gansu",
     "lat": 40.80, "lon": 96.60, "capacity_mw": 8000, "turbines": 7000,
     "year": 2020, "type": "Onshore", "notes": "World's largest onshore wind farm complex"},
    {"name": "Jaisalmer Wind Park", "country": "India", "state": "Rajasthan",
     "lat": 26.92, "lon": 70.90, "capacity_mw": 1600, "turbines": 3000,
     "year": 2012, "type": "Onshore", "notes": "Thar Desert wind corridor"},
    {"name": "Alta Wind Energy Center", "country": "USA", "state": "California",
     "lat": 35.07, "lon": -118.35, "capacity_mw": 1548, "turbines": 600,
     "year": 2014, "type": "Onshore", "notes": "Tehachapi Mountains, Kern County"},
    {"name": "Roscoe Wind Farm", "country": "USA", "state": "Texas",
     "lat": 32.45, "lon": -100.53, "capacity_mw": 782, "turbines": 627,
     "year": 2009, "type": "Onshore", "notes": "Nolan County, Texas"},
    {"name": "Shepherds Flat Wind Farm", "country": "USA", "state": "Oregon",
     "lat": 45.67, "lon": -120.12, "capacity_mw": 845, "turbines": 338,
     "year": 2012, "type": "Onshore", "notes": "Gilliam & Morrow counties"},
    {"name": "Walney Extension", "country": "UK", "state": "Irish Sea",
     "lat": 54.03, "lon": -3.53, "capacity_mw": 659, "turbines": 87,
     "year": 2018, "type": "Offshore", "notes": "Off Cumbria coast"},
    {"name": "London Array", "country": "UK", "state": "Thames Estuary",
     "lat": 51.63, "lon": 1.55, "capacity_mw": 630, "turbines": 175,
     "year": 2013, "type": "Offshore", "notes": "Outer Thames Estuary"},
    {"name": "Fosen Vind", "country": "Norway", "state": "Trondelag",
     "lat": 63.80, "lon": 10.20, "capacity_mw": 1057, "turbines": 277,
     "year": 2021, "type": "Onshore", "notes": "Europe's largest onshore wind farm"},
    {"name": "Borssele Wind Farm", "country": "Netherlands", "state": "North Sea",
     "lat": 51.70, "lon": 3.03, "capacity_mw": 1500, "turbines": 209,
     "year": 2021, "type": "Offshore", "notes": "Zeeland offshore zone"},
    {"name": "Markbygden Wind Farm", "country": "Sweden", "state": "Norrbotten",
     "lat": 65.40, "lon": 19.80, "capacity_mw": 4000, "turbines": 1101,
     "year": 2026, "type": "Onshore", "notes": "Europe's largest planned onshore farm"},
    {"name": "Vineyard Wind 1", "country": "USA", "state": "Massachusetts",
     "lat": 41.19, "lon": -70.09, "capacity_mw": 806, "turbines": 62,
     "year": 2024, "type": "Offshore", "notes": "First large-scale US offshore wind farm"},
    {"name": "Greater Changhua", "country": "Taiwan", "state": "Taiwan Strait",
     "lat": 24.10, "lon": 120.20, "capacity_mw": 2100, "turbines": 295,
     "year": 2025, "type": "Offshore", "notes": "Orsted project in Taiwan Strait"},
    {"name": "Anholt Offshore Wind Farm", "country": "Denmark", "state": "Kattegat",
     "lat": 56.60, "lon": 11.22, "capacity_mw": 400, "turbines": 111,
     "year": 2013, "type": "Offshore", "notes": "Denmark's largest offshore farm"},
    {"name": "Whitelee Wind Farm", "country": "UK", "state": "Scotland",
     "lat": 55.68, "lon": -4.28, "capacity_mw": 539, "turbines": 215,
     "year": 2009, "type": "Onshore", "notes": "UK's largest onshore wind farm"},
    {"name": "Fantanele-Cogealac", "country": "Romania", "state": "Dobrogea",
     "lat": 44.33, "lon": 28.60, "capacity_mw": 600, "turbines": 240,
     "year": 2012, "type": "Onshore", "notes": "Largest onshore farm in Europe (at build)"},
]

# ═══════════════════════════════════════════════════════════════════
# 3. HYDROELECTRIC DAMS — Curated dataset
# ═══════════════════════════════════════════════════════════════════
HYDRO_DAMS = [
    {"name": "Three Gorges Dam", "country": "China", "river": "Yangtze",
     "lat": 30.82, "lon": 111.00, "capacity_mw": 22500, "height_m": 181,
     "year": 2012, "notes": "World's largest power station by capacity"},
    {"name": "Itaipu Dam", "country": "Brazil/Paraguay", "river": "Parana",
     "lat": -25.41, "lon": -54.59, "capacity_mw": 14000, "height_m": 196,
     "year": 1984, "notes": "Highest annual energy generation worldwide"},
    {"name": "Xiluodu Dam", "country": "China", "river": "Jinsha",
     "lat": 28.25, "lon": 103.65, "capacity_mw": 13860, "height_m": 285,
     "year": 2014, "notes": "Double-curvature arch dam"},
    {"name": "Guri Dam", "country": "Venezuela", "river": "Caroni",
     "lat": 7.76, "lon": -63.00, "capacity_mw": 10235, "height_m": 162,
     "year": 1986, "notes": "Powers 73% of Venezuela's electricity"},
    {"name": "Tucurui Dam", "country": "Brazil", "river": "Tocantins",
     "lat": -3.83, "lon": -49.72, "capacity_mw": 8370, "height_m": 78,
     "year": 1984, "notes": "First large dam in Amazon rainforest"},
    {"name": "Baihetan Dam", "country": "China", "river": "Jinsha",
     "lat": 27.23, "lon": 102.90, "capacity_mw": 16000, "height_m": 289,
     "year": 2022, "notes": "World's second-largest by capacity"},
    {"name": "Grand Coulee Dam", "country": "USA", "river": "Columbia",
     "lat": 47.95, "lon": -118.98, "capacity_mw": 6809, "height_m": 168,
     "year": 1942, "notes": "Largest hydroelectric in USA"},
    {"name": "Sayano-Shushenskaya Dam", "country": "Russia", "river": "Yenisei",
     "lat": 52.83, "lon": 91.37, "capacity_mw": 6400, "height_m": 242,
     "year": 1978, "notes": "Russia's largest power station"},
    {"name": "Longtan Dam", "country": "China", "river": "Hongshui",
     "lat": 25.03, "lon": 107.05, "capacity_mw": 6426, "height_m": 216,
     "year": 2009, "notes": "Roller-compacted concrete dam"},
    {"name": "Robert-Bourassa Dam", "country": "Canada", "river": "La Grande",
     "lat": 53.78, "lon": -77.45, "capacity_mw": 5616, "height_m": 162,
     "year": 1981, "notes": "James Bay hydroelectric project"},
    {"name": "Churchill Falls", "country": "Canada", "river": "Churchill",
     "lat": 53.25, "lon": -64.00, "capacity_mw": 5428, "height_m": 312,
     "year": 1971, "notes": "Labrador, Newfoundland"},
    {"name": "Krasnoyarsk Dam", "country": "Russia", "river": "Yenisei",
     "lat": 55.93, "lon": 92.30, "capacity_mw": 6000, "height_m": 124,
     "year": 1972, "notes": "Second largest in Russia"},
    {"name": "Nuozhadu Dam", "country": "China", "river": "Mekong",
     "lat": 22.65, "lon": 100.42, "capacity_mw": 5850, "height_m": 261,
     "year": 2014, "notes": "Tallest dam on Mekong River"},
    {"name": "Aswan High Dam", "country": "Egypt", "river": "Nile",
     "lat": 23.97, "lon": 32.88, "capacity_mw": 2100, "height_m": 111,
     "year": 1970, "notes": "Created Lake Nasser, iconic dam"},
    {"name": "Hoover Dam", "country": "USA", "river": "Colorado",
     "lat": 36.02, "lon": -114.74, "capacity_mw": 2080, "height_m": 221,
     "year": 1936, "notes": "Iconic American dam on Nevada-Arizona border"},
    {"name": "Tarbela Dam", "country": "Pakistan", "river": "Indus",
     "lat": 34.09, "lon": 72.70, "capacity_mw": 4888, "height_m": 143,
     "year": 1976, "notes": "Largest earth-filled dam in the world"},
    {"name": "Cahora Bassa Dam", "country": "Mozambique", "river": "Zambezi",
     "lat": -15.60, "lon": 32.68, "capacity_mw": 2075, "height_m": 171,
     "year": 1974, "notes": "One of Africa's largest dams"},
    {"name": "Xiangjiaba Dam", "country": "China", "river": "Jinsha",
     "lat": 28.64, "lon": 104.40, "capacity_mw": 6448, "height_m": 161,
     "year": 2014, "notes": "Gravity dam on Jinsha River"},
]

# ═══════════════════════════════════════════════════════════════════
# 4. GEOTHERMAL PLANTS — Curated dataset
# ═══════════════════════════════════════════════════════════════════
GEOTHERMAL_PLANTS = [
    {"name": "The Geysers", "country": "USA", "state": "California",
     "lat": 38.79, "lon": -122.77, "capacity_mw": 1517,
     "year": 1960, "notes": "World's largest geothermal complex, 22 plants"},
    {"name": "Cerro Prieto Geothermal", "country": "Mexico", "state": "Baja California",
     "lat": 32.42, "lon": -115.24, "capacity_mw": 720,
     "year": 1973, "notes": "One of the world's largest geothermal fields"},
    {"name": "Larderello", "country": "Italy", "state": "Tuscany",
     "lat": 43.25, "lon": 10.87, "capacity_mw": 795,
     "year": 1913, "notes": "World's first geothermal power plant (1904 experiment)"},
    {"name": "Hellisheidi Power Station", "country": "Iceland", "state": "Hengill",
     "lat": 64.04, "lon": -21.40, "capacity_mw": 303,
     "year": 2006, "notes": "Largest single geothermal plant in Iceland"},
    {"name": "Wairakei Power Station", "country": "New Zealand", "state": "Taupo",
     "lat": -38.63, "lon": 176.10, "capacity_mw": 181,
     "year": 1958, "notes": "Second geothermal plant ever built"},
    {"name": "Olkaria Geothermal Complex", "country": "Kenya", "state": "Rift Valley",
     "lat": -0.88, "lon": 36.30, "capacity_mw": 985,
     "year": 1981, "notes": "East African Rift geothermal, Africa's largest"},
    {"name": "Salak Geothermal", "country": "Indonesia", "state": "West Java",
     "lat": -6.72, "lon": 106.73, "capacity_mw": 377,
     "year": 1994, "notes": "Star Energy operated, volcanic setting"},
    {"name": "Makban Geothermal", "country": "Philippines", "state": "Laguna",
     "lat": 14.08, "lon": 121.30, "capacity_mw": 458,
     "year": 1979, "notes": "Near Laguna de Bay"},
    {"name": "Tiwi Geothermal", "country": "Philippines", "state": "Albay",
     "lat": 13.45, "lon": 123.68, "capacity_mw": 330,
     "year": 1979, "notes": "Near Mount Mayon volcano"},
    {"name": "Wayang Windu", "country": "Indonesia", "state": "West Java",
     "lat": -7.21, "lon": 107.63, "capacity_mw": 227,
     "year": 2000, "notes": "Star Energy geothermal"},
    {"name": "Svartsengi Power Station", "country": "Iceland", "state": "Reykjanes",
     "lat": 63.88, "lon": -22.43, "capacity_mw": 75,
     "year": 1976, "notes": "Adjacent to famous Blue Lagoon"},
    {"name": "Nesjavellir Power Station", "country": "Iceland", "state": "Hengill",
     "lat": 64.11, "lon": -21.26, "capacity_mw": 120,
     "year": 1990, "notes": "Second largest in Iceland"},
    {"name": "Krafla Power Station", "country": "Iceland", "state": "Nordurland",
     "lat": 65.71, "lon": -16.78, "capacity_mw": 60,
     "year": 1977, "notes": "In active volcanic caldera"},
    {"name": "Reykjanes Power Station", "country": "Iceland", "state": "Reykjanes",
     "lat": 63.82, "lon": -22.69, "capacity_mw": 100,
     "year": 2006, "notes": "At the Mid-Atlantic Ridge"},
    {"name": "Mutnovsky Geothermal", "country": "Russia", "state": "Kamchatka",
     "lat": 52.45, "lon": 158.20, "capacity_mw": 50,
     "year": 2002, "notes": "Near Mutnovsky volcano, Kamchatka"},
    {"name": "Sarulla Geothermal", "country": "Indonesia", "state": "North Sumatra",
     "lat": 2.10, "lon": 98.87, "capacity_mw": 330,
     "year": 2018, "notes": "World's largest single-contract geothermal"},
    {"name": "Menengai Geothermal", "country": "Kenya", "state": "Rift Valley",
     "lat": -0.20, "lon": 36.07, "capacity_mw": 105,
     "year": 2022, "notes": "Menengai caldera, East African Rift"},
    {"name": "Djibouti Geothermal (Fiale)", "country": "Djibouti", "state": "Lake Assal",
     "lat": 11.50, "lon": 42.80, "capacity_mw": 50,
     "year": 2025, "notes": "East African Rift, pilot project"},
]

# ═══════════════════════════════════════════════════════════════════
# 5. TIDAL & WAVE ENERGY — Curated dataset
# ═══════════════════════════════════════════════════════════════════
TIDAL_WAVE = [
    {"name": "Sihwa Lake Tidal Power Station", "country": "South Korea", "state": "Gyeonggi",
     "lat": 37.32, "lon": 126.61, "capacity_mw": 254, "type": "Tidal Barrage",
     "year": 2011, "notes": "World's largest tidal power installation"},
    {"name": "La Rance Tidal Power Station", "country": "France", "state": "Brittany",
     "lat": 48.62, "lon": -2.03, "capacity_mw": 240, "type": "Tidal Barrage",
     "year": 1966, "notes": "World's first tidal power station"},
    {"name": "Annapolis Royal Tidal Station", "country": "Canada", "state": "Nova Scotia",
     "lat": 44.75, "lon": -65.52, "capacity_mw": 20, "type": "Tidal Barrage",
     "year": 1984, "notes": "Bay of Fundy, highest tides on Earth"},
    {"name": "Jiangxia Tidal Power Station", "country": "China", "state": "Zhejiang",
     "lat": 28.35, "lon": 121.23, "capacity_mw": 3.2, "type": "Tidal Barrage",
     "year": 1980, "notes": "China's largest tidal plant"},
    {"name": "MeyGen Tidal Array", "country": "UK", "state": "Scotland",
     "lat": 58.73, "lon": -3.11, "capacity_mw": 6, "type": "Tidal Stream",
     "year": 2017, "notes": "World's largest tidal stream array, Pentland Firth"},
    {"name": "EMEC Wave Test Site", "country": "UK", "state": "Orkney",
     "lat": 58.98, "lon": -3.37, "capacity_mw": 2, "type": "Wave Energy Test",
     "year": 2003, "notes": "European Marine Energy Centre test site"},
    {"name": "Mutriku Wave Power Plant", "country": "Spain", "state": "Basque Country",
     "lat": 43.31, "lon": -2.38, "capacity_mw": 0.3, "type": "Wave Energy (OWC)",
     "year": 2011, "notes": "First commercial wave power plant in Europe"},
    {"name": "Swansea Bay Tidal Lagoon (Planned)", "country": "UK", "state": "Wales",
     "lat": 51.61, "lon": -3.93, "capacity_mw": 320, "type": "Tidal Lagoon",
     "year": 2028, "notes": "Proposed tidal lagoon project"},
    {"name": "Uldolmok Tidal Power", "country": "South Korea", "state": "Jindo",
     "lat": 34.56, "lon": 126.27, "capacity_mw": 1, "type": "Tidal Stream",
     "year": 2009, "notes": "Experimental tidal current turbine"},
    {"name": "Fundy FORCE Test Site", "country": "Canada", "state": "Nova Scotia",
     "lat": 45.37, "lon": -64.43, "capacity_mw": 5, "type": "Tidal Stream Test",
     "year": 2009, "notes": "Fundy Ocean Research Centre for Energy"},
    {"name": "OTEC Pilot (Makai)", "country": "USA", "state": "Hawaii",
     "lat": 19.73, "lon": -156.06, "capacity_mw": 0.1, "type": "OTEC",
     "year": 2015, "notes": "Ocean Thermal Energy Conversion, Makai Ocean Engineering"},
    {"name": "Minesto Dragon 12", "country": "Faroe Islands", "state": "Vestmanna",
     "lat": 62.15, "lon": -7.17, "capacity_mw": 1.2, "type": "Tidal Kite",
     "year": 2023, "notes": "Underwater kite tidal energy"},
    {"name": "Orbital O2 Tidal Turbine", "country": "UK", "state": "Orkney",
     "lat": 58.97, "lon": -3.24, "capacity_mw": 2, "type": "Tidal Stream",
     "year": 2021, "notes": "World's most powerful tidal turbine"},
    {"name": "Tocardo Tidal Turbines", "country": "Netherlands", "state": "Zeeland",
     "lat": 51.60, "lon": 3.68, "capacity_mw": 1.2, "type": "Tidal Stream",
     "year": 2015, "notes": "Eastern Scheldt storm surge barrier"},
]

# ═══════════════════════════════════════════════════════════════════
# 6. BIOMASS & BIOENERGY — Curated dataset
# ═══════════════════════════════════════════════════════════════════
BIOMASS_PLANTS = [
    {"name": "Drax Power Station (Biomass)", "country": "UK", "state": "Yorkshire",
     "lat": 53.74, "lon": -0.99, "capacity_mw": 2595, "type": "Wood Pellets",
     "year": 2013, "notes": "Converted from coal, UK's largest biomass plant"},
    {"name": "Ironbridge Biomass Plant", "country": "UK", "state": "Shropshire",
     "lat": 52.63, "lon": -2.50, "capacity_mw": 740, "type": "Wood Pellets",
     "year": 2013, "notes": "Converted from coal (now decommissioned)"},
    {"name": "Alholmens Kraft", "country": "Finland", "state": "Ostrobothnia",
     "lat": 63.67, "lon": 22.70, "capacity_mw": 265, "type": "Wood/Peat",
     "year": 2001, "notes": "World's largest bio-fueled power plant"},
    {"name": "Polaniec Biomass Plant", "country": "Poland", "state": "Swietokrzyskie",
     "lat": 50.73, "lon": 21.28, "capacity_mw": 225, "type": "Wood/Agri",
     "year": 2012, "notes": "Green Block, one of Europe's largest biomass"},
    {"name": "Archer Daniels Midland (Decatur)", "country": "USA", "state": "Illinois",
     "lat": 39.85, "lon": -88.95, "capacity_mw": 0, "type": "Ethanol",
     "year": 1978, "notes": "Largest ethanol producer globally, 1.8B gallons/year"},
    {"name": "POET Biorefining", "country": "USA", "state": "South Dakota",
     "lat": 43.73, "lon": -96.62, "capacity_mw": 0, "type": "Ethanol",
     "year": 1986, "notes": "Largest privately-owned ethanol producer"},
    {"name": "Vivergo Fuels", "country": "UK", "state": "East Yorkshire",
     "lat": 53.73, "lon": -0.30, "capacity_mw": 0, "type": "Ethanol",
     "year": 2013, "notes": "Wheat-based bioethanol, 420M litres/year"},
    {"name": "Verbio AG Schwedt", "country": "Germany", "state": "Brandenburg",
     "lat": 53.06, "lon": 14.27, "capacity_mw": 20, "type": "Biogas/Biomethane",
     "year": 2010, "notes": "Straw-based biomethane production"},
    {"name": "Avedore Power Station", "country": "Denmark", "state": "Copenhagen",
     "lat": 55.59, "lon": 12.44, "capacity_mw": 570, "type": "Straw/Wood",
     "year": 2001, "notes": "CHP with biomass co-firing"},
    {"name": "Sao Martinho Sugar & Ethanol", "country": "Brazil", "state": "Sao Paulo",
     "lat": -21.32, "lon": -48.24, "capacity_mw": 180, "type": "Sugarcane Bagasse",
     "year": 1937, "notes": "Brazil's largest sugarcane ethanol producer"},
    {"name": "Raizen Bioenergy", "country": "Brazil", "state": "Sao Paulo",
     "lat": -22.31, "lon": -48.56, "capacity_mw": 1200, "type": "Sugarcane Bagasse",
     "year": 2010, "notes": "Shell-Cosan JV, 2nd gen ethanol pioneer"},
    {"name": "Amager Resource Center (CopenHill)", "country": "Denmark", "state": "Copenhagen",
     "lat": 55.68, "lon": 12.61, "capacity_mw": 67, "type": "Waste-to-Energy",
     "year": 2019, "notes": "Iconic building with ski slope on roof"},
    {"name": "Kymijärvi II", "country": "Finland", "state": "Paijat-Hame",
     "lat": 60.97, "lon": 25.67, "capacity_mw": 50, "type": "SRF Gasification",
     "year": 2012, "notes": "World's first SRF gasification plant"},
    {"name": "Tilbury Green Power", "country": "UK", "state": "Essex",
     "lat": 51.46, "lon": 0.37, "capacity_mw": 40, "type": "Wood Waste",
     "year": 2018, "notes": "Wood waste to electricity"},
]

# ═══════════════════════════════════════════════════════════════════
# 7. GREEN HYDROGEN — Curated dataset
# ═══════════════════════════════════════════════════════════════════
GREEN_HYDROGEN = [
    {"name": "NEOM Green Hydrogen (Helios)", "country": "Saudi Arabia", "state": "Tabuk",
     "lat": 27.95, "lon": 35.30, "capacity_mw": 2200, "status": "Under Construction",
     "year": 2026, "notes": "World's largest green H2 project, $8.4B, wind+solar powered"},
    {"name": "Asian Renewable Energy Hub (AREH)", "country": "Australia", "state": "Western Australia",
     "lat": -20.20, "lon": 121.50, "capacity_mw": 26000, "status": "Planning",
     "year": 2030, "notes": "26 GW wind+solar for green H2 & ammonia"},
    {"name": "HyDeal Ambition", "country": "Spain/France", "state": "Iberia",
     "lat": 40.50, "lon": -3.50, "capacity_mw": 9500, "status": "Planning",
     "year": 2030, "notes": "95 GW solar, 67 GW electrolyzer by 2030"},
    {"name": "Western Green Energy Hub", "country": "Australia", "state": "Western Australia",
     "lat": -32.80, "lon": 123.00, "capacity_mw": 50000, "status": "Planning",
     "year": 2030, "notes": "50 GW renewable H2 mega-project"},
    {"name": "Haru Oni (eFuels)", "country": "Chile", "state": "Magallanes",
     "lat": -52.30, "lon": -70.30, "capacity_mw": 3.4, "status": "Pilot Operational",
     "year": 2022, "notes": "Porsche/Siemens eFuel from wind-powered H2"},
    {"name": "NortH2 Project", "country": "Netherlands", "state": "Groningen",
     "lat": 53.44, "lon": 6.85, "capacity_mw": 4000, "status": "Planning",
     "year": 2030, "notes": "Shell/Gasunie/Groningen, offshore wind to H2"},
    {"name": "Wesseling Green Hydrogen", "country": "Germany", "state": "NRW",
     "lat": 50.83, "lon": 6.97, "capacity_mw": 10, "status": "Operational",
     "year": 2021, "notes": "Shell Refhyne, Europe's largest PEM electrolyzer"},
    {"name": "Kuqa Green Hydrogen Plant", "country": "China", "state": "Xinjiang",
     "lat": 41.73, "lon": 82.97, "capacity_mw": 260, "status": "Operational",
     "year": 2023, "notes": "Sinopec, world's largest green H2 plant (operating)"},
    {"name": "FlagshipONE eMethanol", "country": "Sweden", "state": "Ornskoldsvik",
     "lat": 63.29, "lon": 18.71, "capacity_mw": 70, "status": "Under Construction",
     "year": 2025, "notes": "Orsted, green methanol from H2 + captured CO2"},
    {"name": "H2 Green Steel (Boden)", "country": "Sweden", "state": "Norrbotten",
     "lat": 66.00, "lon": 21.70, "capacity_mw": 700, "status": "Under Construction",
     "year": 2025, "notes": "Green H2 for steel production, reducing coal"},
    {"name": "Hydrogen Park South Australia", "country": "Australia", "state": "South Australia",
     "lat": -34.78, "lon": 138.55, "capacity_mw": 1.25, "status": "Operational",
     "year": 2021, "notes": "Australia's first green H2 blending project"},
    {"name": "Port Lincoln H2 Hub", "country": "Australia", "state": "South Australia",
     "lat": -34.73, "lon": 135.86, "capacity_mw": 30, "status": "Planning",
     "year": 2025, "notes": "Hydrogen for export & local use"},
    {"name": "ACES Delta (Utah)", "country": "USA", "state": "Utah",
     "lat": 39.50, "lon": -112.50, "capacity_mw": 220, "status": "Under Construction",
     "year": 2025, "notes": "Advanced Clean Energy Storage, salt caverns"},
    {"name": "Fukushima Hydrogen Energy Research Field", "country": "Japan", "state": "Fukushima",
     "lat": 37.50, "lon": 141.00, "capacity_mw": 10, "status": "Operational",
     "year": 2020, "notes": "Solar-powered H2, 2020 Olympics showcase"},
    {"name": "Namibia Green Hydrogen (Hyphen)", "country": "Namibia", "state": "Tsau Khaeb",
     "lat": -26.60, "lon": 15.10, "capacity_mw": 5000, "status": "Planning",
     "year": 2030, "notes": "$10B project, wind+solar for green ammonia export"},
]

# ═══════════════════════════════════════════════════════════════════
# 8. SOLAR POTENTIAL — Curated regions
# ═══════════════════════════════════════════════════════════════════
SOLAR_POTENTIAL = [
    {"name": "Sahara Desert", "region": "North Africa", "lat": 25.0, "lon": 10.0,
     "irradiance_kwh_m2": 2500, "rating": "Exceptional",
     "notes": "World's highest solar potential; could theoretically power the world"},
    {"name": "Arabian Peninsula", "region": "Middle East", "lat": 23.5, "lon": 45.0,
     "irradiance_kwh_m2": 2400, "rating": "Exceptional",
     "notes": "Extremely high DNI, ideal for CSP and PV"},
    {"name": "Atacama Desert", "region": "Chile", "lat": -24.5, "lon": -69.3,
     "irradiance_kwh_m2": 2800, "rating": "Exceptional",
     "notes": "Highest recorded solar irradiance on Earth"},
    {"name": "Australian Outback", "region": "Australia", "lat": -25.0, "lon": 134.0,
     "irradiance_kwh_m2": 2200, "rating": "Excellent",
     "notes": "Vast land area with consistent sunshine"},
    {"name": "Thar Desert", "region": "India", "lat": 27.0, "lon": 71.0,
     "irradiance_kwh_m2": 2100, "rating": "Excellent",
     "notes": "India's prime solar belt, hosts Bhadla park"},
    {"name": "Mojave Desert", "region": "USA", "lat": 35.0, "lon": -117.0,
     "irradiance_kwh_m2": 2200, "rating": "Excellent",
     "notes": "Hosts major CSP and PV installations"},
    {"name": "Namib Desert", "region": "Namibia", "lat": -24.0, "lon": 15.5,
     "irradiance_kwh_m2": 2300, "rating": "Excellent",
     "notes": "High irradiance, low cloud cover"},
    {"name": "Gobi Desert", "region": "China/Mongolia", "lat": 42.5, "lon": 103.0,
     "irradiance_kwh_m2": 1800, "rating": "Very Good",
     "notes": "Large-scale solar farm development"},
    {"name": "Mediterranean (Spain)", "region": "Europe", "lat": 37.5, "lon": -3.0,
     "irradiance_kwh_m2": 1800, "rating": "Very Good",
     "notes": "Best solar potential in Europe"},
    {"name": "East African Highlands", "region": "East Africa", "lat": -1.0, "lon": 37.0,
     "irradiance_kwh_m2": 2000, "rating": "Excellent",
     "notes": "High altitude, equatorial position"},
    {"name": "Sonoran Desert", "region": "Mexico/USA", "lat": 31.0, "lon": -113.0,
     "irradiance_kwh_m2": 2100, "rating": "Excellent",
     "notes": "Ideal for large-scale PV deployment"},
    {"name": "Karakum Desert", "region": "Turkmenistan", "lat": 39.0, "lon": 59.0,
     "irradiance_kwh_m2": 1900, "rating": "Very Good",
     "notes": "Central Asian solar belt"},
    {"name": "Tibetan Plateau", "region": "China", "lat": 33.0, "lon": 90.0,
     "irradiance_kwh_m2": 2200, "rating": "Excellent",
     "notes": "High altitude amplifies solar radiation"},
    {"name": "Northern Chile (Antofagasta)", "region": "Chile", "lat": -23.6, "lon": -70.4,
     "irradiance_kwh_m2": 2700, "rating": "Exceptional",
     "notes": "Solar energy capital of South America"},
]

# ═══════════════════════════════════════════════════════════════════
# 9. WIND POTENTIAL — Curated regions
# ═══════════════════════════════════════════════════════════════════
WIND_POTENTIAL = [
    {"name": "North Sea", "region": "Europe", "lat": 55.0, "lon": 3.0,
     "wind_speed_ms": 10.5, "type": "Offshore", "rating": "Exceptional",
     "notes": "Premier offshore wind area, consistent strong winds"},
    {"name": "Patagonia", "region": "Argentina", "lat": -48.0, "lon": -68.0,
     "wind_speed_ms": 12.0, "type": "Onshore", "rating": "Exceptional",
     "notes": "Some of the strongest sustained winds on Earth"},
    {"name": "Great Plains (Texas)", "region": "USA", "lat": 33.0, "lon": -101.0,
     "wind_speed_ms": 8.5, "type": "Onshore", "rating": "Excellent",
     "notes": "US wind corridor, largest installed wind capacity"},
    {"name": "Inner Mongolia", "region": "China", "lat": 42.0, "lon": 110.0,
     "wind_speed_ms": 8.0, "type": "Onshore", "rating": "Excellent",
     "notes": "China's wind power heartland"},
    {"name": "Danish Straits", "region": "Denmark", "lat": 56.0, "lon": 11.0,
     "wind_speed_ms": 9.5, "type": "Offshore", "rating": "Excellent",
     "notes": "Pioneer of offshore wind energy"},
    {"name": "Thar Desert Wind Corridor", "region": "India", "lat": 26.5, "lon": 70.5,
     "wind_speed_ms": 7.5, "type": "Onshore", "rating": "Very Good",
     "notes": "India's prime wind belt, Rajasthan-Gujarat"},
    {"name": "Baltic Sea", "region": "Europe", "lat": 57.0, "lon": 17.0,
     "wind_speed_ms": 9.0, "type": "Offshore", "rating": "Excellent",
     "notes": "Growing offshore wind development"},
    {"name": "Irish Sea / Celtic Sea", "region": "UK/Ireland", "lat": 52.0, "lon": -6.0,
     "wind_speed_ms": 9.5, "type": "Offshore", "rating": "Excellent",
     "notes": "Strong Atlantic winds, major expansion planned"},
    {"name": "Cabo Delgado", "region": "Mozambique", "lat": -12.0, "lon": 40.5,
     "wind_speed_ms": 8.0, "type": "Onshore", "rating": "Very Good",
     "notes": "East African coast wind corridor"},
    {"name": "Cape Region (South Africa)", "region": "South Africa", "lat": -33.5, "lon": 19.0,
     "wind_speed_ms": 8.5, "type": "Onshore", "rating": "Excellent",
     "notes": "Strong & consistent trade winds"},
    {"name": "Hokkaido", "region": "Japan", "lat": 43.0, "lon": 143.0,
     "wind_speed_ms": 8.0, "type": "Offshore", "rating": "Very Good",
     "notes": "Japan's windiest region, floating wind potential"},
    {"name": "Taiwan Strait", "region": "Taiwan", "lat": 24.0, "lon": 119.0,
     "wind_speed_ms": 10.0, "type": "Offshore", "rating": "Exceptional",
     "notes": "Channeled monsoon winds, major offshore development"},
    {"name": "Southern Norway", "region": "Norway", "lat": 59.0, "lon": 6.0,
     "wind_speed_ms": 9.0, "type": "Onshore/Offshore", "rating": "Excellent",
     "notes": "Fosen wind farm area, strong & reliable"},
]

# ═══════════════════════════════════════════════════════════════════
# 10. EV INFRASTRUCTURE — Curated dataset
# ═══════════════════════════════════════════════════════════════════
EV_INFRASTRUCTURE = [
    {"name": "Tesla Gigafactory Nevada", "country": "USA", "state": "Nevada",
     "lat": 39.54, "lon": -119.44, "type": "Battery Factory",
     "year": 2016, "notes": "First Gigafactory, battery cell production with Panasonic"},
    {"name": "Tesla Gigafactory Shanghai", "country": "China", "state": "Shanghai",
     "lat": 30.89, "lon": 121.82, "type": "EV + Battery Factory",
     "year": 2019, "notes": "Model 3/Y production, Megapack batteries"},
    {"name": "Tesla Gigafactory Berlin", "country": "Germany", "state": "Brandenburg",
     "lat": 52.39, "lon": 13.79, "type": "EV + Battery Factory",
     "year": 2022, "notes": "Giga Berlin-Brandenburg, Model Y for Europe"},
    {"name": "Tesla Gigafactory Texas", "country": "USA", "state": "Texas",
     "lat": 30.22, "lon": -97.62, "type": "EV + Battery Factory",
     "year": 2022, "notes": "Cybertruck production, HQ campus"},
    {"name": "BYD Shenzhen HQ & Factory", "country": "China", "state": "Guangdong",
     "lat": 22.65, "lon": 114.02, "type": "EV + Battery Factory",
     "year": 2003, "notes": "World's largest EV manufacturer by sales"},
    {"name": "CATL Ningde Factory", "country": "China", "state": "Fujian",
     "lat": 26.66, "lon": 119.55, "type": "Battery Factory",
     "year": 2011, "notes": "World's largest battery manufacturer"},
    {"name": "LG Energy Wroclaw", "country": "Poland", "state": "Lower Silesia",
     "lat": 51.10, "lon": 16.98, "type": "Battery Factory",
     "year": 2018, "notes": "Largest battery factory in Europe"},
    {"name": "Samsung SDI Goed", "country": "Hungary", "state": "Komarom",
     "lat": 47.74, "lon": 18.12, "type": "Battery Factory",
     "year": 2018, "notes": "Samsung's European battery hub"},
    {"name": "Northvolt Ett", "country": "Sweden", "state": "Skelleftea",
     "lat": 64.75, "lon": 20.95, "type": "Battery Factory",
     "year": 2023, "notes": "Europe's first homegrown gigafactory"},
    {"name": "SK On Georgia Plant", "country": "USA", "state": "Georgia",
     "lat": 34.30, "lon": -83.82, "type": "Battery Factory",
     "year": 2022, "notes": "SK Innovation batteries for Ford, VW"},
    {"name": "Ionity Ultra-Rapid Hub (Munich)", "country": "Germany", "state": "Bavaria",
     "lat": 48.14, "lon": 11.58, "type": "Charging Network HQ",
     "year": 2017, "notes": "Pan-European 350kW charging JV (BMW, Mercedes, VW, Ford)"},
    {"name": "Gridserve Electric Forecourt (Braintree)", "country": "UK", "state": "Essex",
     "lat": 51.87, "lon": 0.55, "type": "Charging Hub",
     "year": 2020, "notes": "UK's first electric forecourt, solar-powered"},
    {"name": "Fastned Station (Limburg)", "country": "Netherlands", "state": "Limburg",
     "lat": 50.90, "lon": 5.93, "type": "Charging Network",
     "year": 2013, "notes": "European fast-charging pioneer, solar canopies"},
    {"name": "Tesla Supercharger Hub (Kettleman City)", "country": "USA", "state": "California",
     "lat": 35.99, "lon": -119.96, "type": "Supercharger Hub",
     "year": 2019, "notes": "40-stall Supercharger, lounge, solar canopy"},
    {"name": "Tesla Supercharger Hub (Shanghai)", "country": "China", "state": "Shanghai",
     "lat": 31.23, "lon": 121.47, "type": "Supercharger Hub",
     "year": 2020, "notes": "72-stall, largest Supercharger station in the world"},
    {"name": "ChargePoint HQ", "country": "USA", "state": "California",
     "lat": 37.39, "lon": -121.98, "type": "Charging Network HQ",
     "year": 2007, "notes": "Largest EV charging network globally (200k+ ports)"},
    {"name": "Volkswagen Salzgitter Battery Plant", "country": "Germany", "state": "Lower Saxony",
     "lat": 52.15, "lon": 10.33, "type": "Battery Factory",
     "year": 2025, "notes": "VW PowerCo unified cell factory"},
    {"name": "Rivian Normal Factory", "country": "USA", "state": "Illinois",
     "lat": 40.51, "lon": -89.00, "type": "EV Factory",
     "year": 2021, "notes": "R1T/R1S production, former Mitsubishi plant"},
    {"name": "AESC Sunderland Gigafactory", "country": "UK", "state": "Tyne and Wear",
     "lat": 54.91, "lon": -1.47, "type": "Battery Factory",
     "year": 2024, "notes": "Envision AESC, batteries for Nissan Leaf & Renault"},
]

# ═══════════════════════════════════════════════════════════════════
# CATEGORY COLOR MAP
# ═══════════════════════════════════════════════════════════════════
MODE_COLORS = {
    "solar": "#f59e0b",
    "wind": "#06b6d4",
    "hydro": "#3b82f6",
    "geothermal": "#ef4444",
    "tidal": "#8b5cf6",
    "biomass": "#10b981",
    "hydrogen": "#14b8a6",
    "solar_potential": "#f97316",
    "wind_potential": "#38bdf8",
    "ev": "#84cc16",
}


# ═══════════════════════════════════════════════════════════════════
# OVERPASS QUERIES
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _query_renewable_overpass(lat: float, lon: float, radius_m: int,
                              source: str) -> list:
    """
    Query Overpass API for power generators of a given source type
    (solar, wind, hydro, geothermal) near a location.
    """
    query = f"""
    [out:json][timeout:60];
    (
      node["power"="generator"]["generator:source"="{source}"](around:{radius_m},{lat},{lon});
      way["power"="generator"]["generator:source"="{source}"](around:{radius_m},{lat},{lon});
      relation["power"="generator"]["generator:source"="{source}"](around:{radius_m},{lat},{lon});
      node["power"="plant"]["plant:source"="{source}"](around:{radius_m},{lat},{lon});
      way["power"="plant"]["plant:source"="{source}"](around:{radius_m},{lat},{lon});
    );
    out center body;
    """
    data = query_overpass(query, timeout=60)
    if data is None or "_error" in data:
        err_msg = data.get("_error", "Unknown error") if data else "No response"
        logger.warning(f"Overpass query for {source} failed: {err_msg}")
        return []
    elements = data.get("elements", [])
    results = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon_v = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat_v is None or lon_v is None:
            continue
        tags = el.get("tags", {})
        results.append({
            "name": tags.get("name", f"Unnamed {source} generator"),
            "lat": lat_v,
            "lon": lon_v,
            "operator": tags.get("operator", "Unknown"),
            "output": tags.get("generator:output:electricity", tags.get("plant:output:electricity", "N/A")),
            "source": tags.get("generator:source", tags.get("plant:source", source)),
            "method": tags.get("generator:method", "N/A"),
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# MAP BUILDERS
# ═══════════════════════════════════════════════════════════════════
def _build_curated_map(data: list, lat_key: str, lon_key: str,
                       name_key: str, color: str, popup_fn,
                       center_lat: float = 20.0, center_lon: float = 0.0,
                       zoom: int = 2) -> folium.Map:
    """Build a folium map from curated data."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="TerraScout AI",
    )
    for item in data:
        lat = item.get(lat_key)
        lon = item.get(lon_key)
        name = item.get(name_key, "Unknown")
        if lat is None or lon is None:
            continue
        popup_html = popup_fn(item)
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(str(name)),
        ).add_to(m)
    return m


def _build_overpass_map(results: list, color: str, source_label: str,
                        center_lat: float, center_lon: float,
                        zoom: int = 10) -> folium.Map:
    """Build a folium map from Overpass query results."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="TerraScout AI",
    )
    for r in results:
        name = escape(str(r.get("name", "Unknown")))
        operator = escape(str(r.get("operator", "Unknown")))
        output = escape(str(r.get("output", "N/A")))
        method = escape(str(r.get("method", "N/A")))
        popup_html = (
            f'<div style="font-family:sans-serif;font-size:12px;">'
            f'<b>{name}</b><br>'
            f'<b>Operator:</b> {operator}<br>'
            f'<b>Output:</b> {output}<br>'
            f'<b>Method:</b> {method}<br>'
            f'<b>Source:</b> {escape(source_label)}'
            f'</div>'
        )
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=name,
        ).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════════
def _plot_bar_chart(labels: list, values: list, title: str,
                    xlabel: str, ylabel: str, color: str,
                    horizontal: bool = True) -> plt.Figure:
    """Create a dark-themed bar chart."""
    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.4)))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)
    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_xlabel(xlabel, color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel(ylabel, color=TEXT_PRIMARY, fontsize=10)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{val:,.0f}' if isinstance(val, (int, float)) else str(val),
                    va='center', ha='left', color=TEXT_SECONDARY, fontsize=8)
    else:
        bars = ax.bar(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_xlabel(xlabel, color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel(ylabel, color=TEXT_PRIMARY, fontsize=10)
        plt.xticks(rotation=45, ha='right')
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=13, fontweight='bold', pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis='x' if horizontal else 'y', color="#2a3550", alpha=0.3, linestyle='--')
    plt.tight_layout()
    return fig


def _plot_scatter_map(data: list, lat_key: str, lon_key: str,
                      size_key: str, label_key: str, title: str,
                      color: str, size_scale: float = 0.01) -> plt.Figure:
    """Create a matplotlib scatter 'map' for potential visualizations."""
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)
    lats = [d[lat_key] for d in data]
    lons = [d[lon_key] for d in data]
    sizes = [max(d.get(size_key, 100) * size_scale, 30) for d in data]
    labels = [d[label_key] for d in data]
    scatter = ax.scatter(lons, lats, s=sizes, c=color, alpha=0.7,
                         edgecolors='white', linewidth=0.5, zorder=5)
    for i, label in enumerate(labels):
        ax.annotate(label, (lons[i], lats[i]), fontsize=6,
                    color=TEXT_SECONDARY, ha='center', va='bottom',
                    xytext=(0, 6), textcoords='offset points')
    ax.set_xlabel("Longitude", color=TEXT_PRIMARY, fontsize=10)
    ax.set_ylabel("Latitude", color=TEXT_PRIMARY, fontsize=10)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=13, fontweight='bold', pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(color="#2a3550", alpha=0.3, linestyle='--')
    ax.set_xlim(-180, 180)
    ax.set_ylim(-70, 80)
    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════
# POPUP BUILDERS (all user content is escaped)
# ═══════════════════════════════════════════════════════════════════
def _solar_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#f59e0b;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>Capacity:</b> {item["capacity_mw"]:,} MW<br>'
        f'<b>Area:</b> {item["area_km2"]} km&sup2;<br>'
        f'<b>Type:</b> {escape(str(item["type"]))}<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _wind_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#06b6d4;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>Capacity:</b> {item["capacity_mw"]:,} MW<br>'
        f'<b>Turbines:</b> {item["turbines"]:,}<br>'
        f'<b>Type:</b> {escape(str(item["type"]))}<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _hydro_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#3b82f6;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>River:</b> {escape(str(item["river"]))}<br>'
        f'<b>Capacity:</b> {item["capacity_mw"]:,} MW<br>'
        f'<b>Height:</b> {item["height_m"]} m<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _geothermal_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#ef4444;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>Capacity:</b> {item["capacity_mw"]:,} MW<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _tidal_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#8b5cf6;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>Capacity:</b> {item["capacity_mw"]:,} MW<br>'
        f'<b>Type:</b> {escape(str(item["type"]))}<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _biomass_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#10b981;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>Capacity:</b> {item["capacity_mw"]:,} MW<br>'
        f'<b>Type:</b> {escape(str(item["type"]))}<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _hydrogen_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#14b8a6;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>Capacity:</b> {item["capacity_mw"]:,} MW (electrolyzer/renewable)<br>'
        f'<b>Status:</b> {escape(str(item["status"]))}<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _solar_potential_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#f97316;">{escape(str(item["name"]))}</b><br>'
        f'<b>Region:</b> {escape(str(item["region"]))}<br>'
        f'<b>GHI:</b> {item["irradiance_kwh_m2"]:,} kWh/m&sup2;/yr<br>'
        f'<b>Rating:</b> {escape(str(item["rating"]))}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _wind_potential_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#38bdf8;">{escape(str(item["name"]))}</b><br>'
        f'<b>Region:</b> {escape(str(item["region"]))}<br>'
        f'<b>Wind Speed:</b> {item["wind_speed_ms"]} m/s<br>'
        f'<b>Type:</b> {escape(str(item["type"]))}<br>'
        f'<b>Rating:</b> {escape(str(item["rating"]))}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


def _ev_popup(item: dict) -> str:
    return (
        f'<div style="font-family:sans-serif;font-size:12px;max-width:300px;">'
        f'<b style="color:#84cc16;">{escape(str(item["name"]))}</b><br>'
        f'<b>Country:</b> {escape(str(item["country"]))}<br>'
        f'<b>Type:</b> {escape(str(item["type"]))}<br>'
        f'<b>Year:</b> {item["year"]}<br>'
        f'<i>{escape(str(item["notes"]))}</i>'
        f'</div>'
    )


# ═══════════════════════════════════════════════════════════════════
# DATA DOWNLOAD HELPER
# ═══════════════════════════════════════════════════════════════════
def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Offer a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        label=label,
        data=buf.getvalue(),
        file_name=filename,
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════════════
# INDIVIDUAL MODE RENDERERS
# ═══════════════════════════════════════════════════════════════════

def _render_solar_farms():
    """Mode 1: Solar Farms Worldwide."""
    st.markdown("#### Solar Farms Worldwide")
    st.markdown(
        "Explore the world's largest solar photovoltaic (PV) and concentrated "
        "solar power (CSP) installations. These mega-projects span deserts and "
        "plains across India, China, the Middle East, Africa, and the Americas."
    )

    # Stats
    total_cap = sum(s["capacity_mw"] for s in SOLAR_FARMS)
    total_area = sum(s["area_km2"] for s in SOLAR_FARMS)
    countries = len(set(s["country"] for s in SOLAR_FARMS))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Installations", len(SOLAR_FARMS))
    c2.metric("Combined Capacity", f"{total_cap:,} MW")
    c3.metric("Total Area", f"{total_area:,.0f} km\u00b2")
    c4.metric("Countries", countries)

    # Overpass search option
    with st.expander("Search OSM for solar generators near a location"):
        oc1, oc2, oc3 = st.columns(3)
        osm_lat = oc1.number_input("Latitude", value=35.0, key="solar_osm_lat",
                                   min_value=-90.0, max_value=90.0)
        osm_lon = oc2.number_input("Longitude", value=-118.0, key="solar_osm_lon",
                                   min_value=-180.0, max_value=180.0)
        osm_radius = oc3.number_input("Radius (km)", value=20, key="solar_osm_r",
                                      min_value=1, max_value=100)
        if st.button("Search OSM Solar", key="solar_osm_btn"):
            with st.spinner("Querying Overpass API for solar generators..."):
                results = _query_renewable_overpass(osm_lat, osm_lon,
                                                   osm_radius * 1000, "solar")
            if results:
                st.success(f"Found {len(results)} solar generators from OSM")
                osm_map = _build_overpass_map(results, MODE_COLORS["solar"],
                                              "Solar", osm_lat, osm_lon, zoom=11)
                components.html(osm_map._repr_html_(), height=500)
                osm_df = pd.DataFrame(results)
                st.dataframe(osm_df, width="stretch")
            else:
                st.warning("No solar generators found in this area via OSM.")

    # Curated map
    st.markdown("##### Curated Major Solar Farms")
    m = _build_curated_map(
        SOLAR_FARMS, "lat", "lon", "name",
        MODE_COLORS["solar"], _solar_popup,
    )
    components.html(m._repr_html_(), height=500)

    # Bar chart
    sorted_farms = sorted(SOLAR_FARMS, key=lambda x: x["capacity_mw"], reverse=True)[:15]
    fig = _plot_bar_chart(
        [s["name"][:30] for s in sorted_farms],
        [s["capacity_mw"] for s in sorted_farms],
        "Top 15 Solar Farms by Capacity (MW)",
        "Capacity (MW)", "",
        MODE_COLORS["solar"],
    )
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    df = pd.DataFrame(SOLAR_FARMS)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "solar_farms_worldwide.csv", "Download Solar Farms CSV")


def _render_wind_farms():
    """Mode 2: Wind Farms."""
    st.markdown("#### Wind Farms — Onshore & Offshore")
    st.markdown(
        "Discover the world's major wind energy installations, from massive "
        "offshore arrays in the North Sea to sprawling onshore farms in China, "
        "the USA, and Scandinavia."
    )

    total_cap = sum(w["capacity_mw"] for w in WIND_FARMS)
    total_turbines = sum(w["turbines"] for w in WIND_FARMS)
    offshore = sum(1 for w in WIND_FARMS if "Offshore" in w["type"])
    onshore = len(WIND_FARMS) - offshore
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Farms", len(WIND_FARMS))
    c2.metric("Combined Capacity", f"{total_cap:,} MW")
    c3.metric("Total Turbines", f"{total_turbines:,}")
    c4.metric("Offshore / Onshore", f"{offshore} / {onshore}")

    with st.expander("Search OSM for wind generators near a location"):
        oc1, oc2, oc3 = st.columns(3)
        osm_lat = oc1.number_input("Latitude", value=53.88, key="wind_osm_lat",
                                   min_value=-90.0, max_value=90.0)
        osm_lon = oc2.number_input("Longitude", value=1.79, key="wind_osm_lon",
                                   min_value=-180.0, max_value=180.0)
        osm_radius = oc3.number_input("Radius (km)", value=20, key="wind_osm_r",
                                      min_value=1, max_value=100)
        if st.button("Search OSM Wind", key="wind_osm_btn"):
            with st.spinner("Querying Overpass API for wind generators..."):
                results = _query_renewable_overpass(osm_lat, osm_lon,
                                                   osm_radius * 1000, "wind")
            if results:
                st.success(f"Found {len(results)} wind generators from OSM")
                osm_map = _build_overpass_map(results, MODE_COLORS["wind"],
                                              "Wind", osm_lat, osm_lon, zoom=11)
                components.html(osm_map._repr_html_(), height=500)
                osm_df = pd.DataFrame(results)
                st.dataframe(osm_df, width="stretch")
            else:
                st.warning("No wind generators found in this area via OSM.")

    st.markdown("##### Curated Major Wind Farms")
    m = _build_curated_map(
        WIND_FARMS, "lat", "lon", "name",
        MODE_COLORS["wind"], _wind_popup,
    )
    components.html(m._repr_html_(), height=500)

    sorted_farms = sorted(WIND_FARMS, key=lambda x: x["capacity_mw"], reverse=True)[:15]
    fig = _plot_bar_chart(
        [w["name"][:30] for w in sorted_farms],
        [w["capacity_mw"] for w in sorted_farms],
        "Top 15 Wind Farms by Capacity (MW)",
        "Capacity (MW)", "",
        MODE_COLORS["wind"],
    )
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(WIND_FARMS)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "wind_farms_worldwide.csv", "Download Wind Farms CSV")


def _render_hydro_dams():
    """Mode 3: Hydroelectric Dams."""
    st.markdown("#### Hydroelectric Dams")
    st.markdown(
        "The world's mightiest dams harness river power to generate electricity. "
        "From the colossal Three Gorges Dam to the iconic Hoover Dam, hydroelectric "
        "power remains the largest source of renewable electricity globally."
    )

    total_cap = sum(h["capacity_mw"] for h in HYDRO_DAMS)
    avg_height = sum(h["height_m"] for h in HYDRO_DAMS) / len(HYDRO_DAMS)
    countries = len(set(h["country"] for h in HYDRO_DAMS))
    oldest = min(h["year"] for h in HYDRO_DAMS)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Dams", len(HYDRO_DAMS))
    c2.metric("Combined Capacity", f"{total_cap:,} MW")
    c3.metric("Avg Height", f"{avg_height:.0f} m")
    c4.metric("Oldest (Year)", oldest)

    with st.expander("Search OSM for hydro generators near a location"):
        oc1, oc2, oc3 = st.columns(3)
        osm_lat = oc1.number_input("Latitude", value=30.82, key="hydro_osm_lat",
                                   min_value=-90.0, max_value=90.0)
        osm_lon = oc2.number_input("Longitude", value=111.0, key="hydro_osm_lon",
                                   min_value=-180.0, max_value=180.0)
        osm_radius = oc3.number_input("Radius (km)", value=30, key="hydro_osm_r",
                                      min_value=1, max_value=100)
        if st.button("Search OSM Hydro", key="hydro_osm_btn"):
            with st.spinner("Querying Overpass API for hydro generators..."):
                results = _query_renewable_overpass(osm_lat, osm_lon,
                                                   osm_radius * 1000, "hydro")
            if results:
                st.success(f"Found {len(results)} hydro generators from OSM")
                osm_map = _build_overpass_map(results, MODE_COLORS["hydro"],
                                              "Hydro", osm_lat, osm_lon, zoom=10)
                components.html(osm_map._repr_html_(), height=500)
                osm_df = pd.DataFrame(results)
                st.dataframe(osm_df, width="stretch")
            else:
                st.warning("No hydro generators found in this area via OSM.")

    st.markdown("##### Curated Major Hydroelectric Dams")
    m = _build_curated_map(
        HYDRO_DAMS, "lat", "lon", "name",
        MODE_COLORS["hydro"], _hydro_popup,
    )
    components.html(m._repr_html_(), height=500)

    sorted_dams = sorted(HYDRO_DAMS, key=lambda x: x["capacity_mw"], reverse=True)[:15]
    fig = _plot_bar_chart(
        [h["name"][:30] for h in sorted_dams],
        [h["capacity_mw"] for h in sorted_dams],
        "Top 15 Hydroelectric Dams by Capacity (MW)",
        "Capacity (MW)", "",
        MODE_COLORS["hydro"],
    )
    st.pyplot(fig)
    plt.close(fig)

    # Height chart
    sorted_height = sorted(HYDRO_DAMS, key=lambda x: x["height_m"], reverse=True)[:15]
    fig2 = _plot_bar_chart(
        [h["name"][:30] for h in sorted_height],
        [h["height_m"] for h in sorted_height],
        "Top 15 Dams by Height (m)",
        "Height (m)", "",
        "#38bdf8",
    )
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(HYDRO_DAMS)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "hydroelectric_dams.csv", "Download Hydro Dams CSV")


def _render_geothermal():
    """Mode 4: Geothermal Plants."""
    st.markdown("#### Geothermal Power Plants")
    st.markdown(
        "Geothermal energy taps heat from the Earth's interior. Major installations "
        "are found along tectonic plate boundaries: Iceland's Mid-Atlantic Ridge, "
        "Italy's volcanic fields, the East African Rift, and the Pacific Ring of Fire."
    )

    total_cap = sum(g["capacity_mw"] for g in GEOTHERMAL_PLANTS)
    countries = len(set(g["country"] for g in GEOTHERMAL_PLANTS))
    oldest = min(g["year"] for g in GEOTHERMAL_PLANTS)
    iceland_count = sum(1 for g in GEOTHERMAL_PLANTS if g["country"] == "Iceland")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Plants", len(GEOTHERMAL_PLANTS))
    c2.metric("Combined Capacity", f"{total_cap:,} MW")
    c3.metric("Countries", countries)
    c4.metric("Iceland Plants", iceland_count)

    with st.expander("Search OSM for geothermal generators near a location"):
        oc1, oc2, oc3 = st.columns(3)
        osm_lat = oc1.number_input("Latitude", value=64.04, key="geo_osm_lat",
                                   min_value=-90.0, max_value=90.0)
        osm_lon = oc2.number_input("Longitude", value=-21.40, key="geo_osm_lon",
                                   min_value=-180.0, max_value=180.0)
        osm_radius = oc3.number_input("Radius (km)", value=30, key="geo_osm_r",
                                      min_value=1, max_value=100)
        if st.button("Search OSM Geothermal", key="geo_osm_btn"):
            with st.spinner("Querying Overpass API for geothermal generators..."):
                results = _query_renewable_overpass(osm_lat, osm_lon,
                                                   osm_radius * 1000, "geothermal")
            if results:
                st.success(f"Found {len(results)} geothermal generators from OSM")
                osm_map = _build_overpass_map(results, MODE_COLORS["geothermal"],
                                              "Geothermal", osm_lat, osm_lon, zoom=10)
                components.html(osm_map._repr_html_(), height=500)
                osm_df = pd.DataFrame(results)
                st.dataframe(osm_df, width="stretch")
            else:
                st.warning("No geothermal generators found in this area via OSM.")

    st.markdown("##### Curated Major Geothermal Plants")
    m = _build_curated_map(
        GEOTHERMAL_PLANTS, "lat", "lon", "name",
        MODE_COLORS["geothermal"], _geothermal_popup,
    )
    components.html(m._repr_html_(), height=500)

    sorted_plants = sorted(GEOTHERMAL_PLANTS, key=lambda x: x["capacity_mw"], reverse=True)[:15]
    fig = _plot_bar_chart(
        [g["name"][:30] for g in sorted_plants],
        [g["capacity_mw"] for g in sorted_plants],
        "Top Geothermal Plants by Capacity (MW)",
        "Capacity (MW)", "",
        MODE_COLORS["geothermal"],
    )
    st.pyplot(fig)
    plt.close(fig)

    # Country breakdown pie
    country_caps = {}
    for g in GEOTHERMAL_PLANTS:
        country_caps[g["country"]] = country_caps.get(g["country"], 0) + g["capacity_mw"]
    sorted_countries = sorted(country_caps.items(), key=lambda x: x[1], reverse=True)
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    fig2.patch.set_facecolor(BG_DARK)
    ax2.set_facecolor(SURFACE)
    labels_c = [c[0] for c in sorted_countries]
    values_c = [c[1] for c in sorted_countries]
    colors_c = [ACCENT_RED, ACCENT_CYAN, ACCENT_GREEN, ACCENT_AMBER,
                ACCENT_VIOLET, ACCENT_PINK, ACCENT_BLUE, ACCENT_ORANGE,
                ACCENT_TEAL, ACCENT_LIME]
    wedges, texts, autotexts = ax2.pie(
        values_c, labels=labels_c, autopct='%1.0f%%',
        colors=colors_c[:len(labels_c)],
        textprops={'color': TEXT_PRIMARY, 'fontsize': 8},
        pctdistance=0.85,
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color(TEXT_PRIMARY)
    ax2.set_title("Geothermal Capacity by Country", color=TEXT_PRIMARY,
                   fontsize=13, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(GEOTHERMAL_PLANTS)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "geothermal_plants.csv", "Download Geothermal CSV")


def _render_tidal_wave():
    """Mode 5: Tidal & Wave Energy."""
    st.markdown("#### Tidal & Wave Energy")
    st.markdown(
        "Ocean energy harnesses the power of tides, waves, and thermal gradients. "
        "While still a nascent industry, tidal barrages like La Rance (1966) and "
        "Sihwa Lake (2011) demonstrate commercial viability, while innovative tidal "
        "stream and wave energy converters are being tested worldwide."
    )

    total_cap = sum(t["capacity_mw"] for t in TIDAL_WAVE)
    types = set(t["type"] for t in TIDAL_WAVE)
    countries = len(set(t["country"] for t in TIDAL_WAVE))
    barrages = sum(1 for t in TIDAL_WAVE if "Barrage" in t["type"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(TIDAL_WAVE))
    c2.metric("Combined Capacity", f"{total_cap:,.1f} MW")
    c3.metric("Countries", countries)
    c4.metric("Technology Types", len(types))

    st.markdown("##### Global Tidal & Wave Energy Sites")
    m = _build_curated_map(
        TIDAL_WAVE, "lat", "lon", "name",
        MODE_COLORS["tidal"], _tidal_popup,
    )
    components.html(m._repr_html_(), height=500)

    sorted_sites = sorted(TIDAL_WAVE, key=lambda x: x["capacity_mw"], reverse=True)
    fig = _plot_bar_chart(
        [t["name"][:35] for t in sorted_sites],
        [t["capacity_mw"] for t in sorted_sites],
        "Tidal & Wave Energy Sites by Capacity (MW)",
        "Capacity (MW)", "",
        MODE_COLORS["tidal"],
    )
    st.pyplot(fig)
    plt.close(fig)

    # Type breakdown
    type_caps = {}
    for t in TIDAL_WAVE:
        type_caps[t["type"]] = type_caps.get(t["type"], 0) + t["capacity_mw"]
    fig2 = _plot_bar_chart(
        list(type_caps.keys()),
        list(type_caps.values()),
        "Capacity by Technology Type (MW)",
        "Capacity (MW)", "",
        ACCENT_VIOLET,
    )
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(TIDAL_WAVE)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "tidal_wave_energy.csv", "Download Tidal & Wave CSV")


def _render_biomass():
    """Mode 6: Biomass & Bioenergy."""
    st.markdown("#### Biomass & Bioenergy")
    st.markdown(
        "Bioenergy encompasses wood pellet power plants, ethanol production "
        "facilities, biogas plants, sugarcane bagasse co-generation, and waste-to-energy. "
        "From the massive Drax conversion in the UK to Brazil's sugarcane ethanol empire."
    )

    total_cap = sum(b["capacity_mw"] for b in BIOMASS_PLANTS)
    types = set(b["type"] for b in BIOMASS_PLANTS)
    countries = len(set(b["country"] for b in BIOMASS_PLANTS))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Facilities", len(BIOMASS_PLANTS))
    c2.metric("Electricity Capacity", f"{total_cap:,} MW")
    c3.metric("Countries", countries)
    c4.metric("Fuel Types", len(types))

    st.markdown("##### Global Biomass & Bioenergy Facilities")
    m = _build_curated_map(
        BIOMASS_PLANTS, "lat", "lon", "name",
        MODE_COLORS["biomass"], _biomass_popup,
    )
    components.html(m._repr_html_(), height=500)

    power_plants = [b for b in BIOMASS_PLANTS if b["capacity_mw"] > 0]
    sorted_bio = sorted(power_plants, key=lambda x: x["capacity_mw"], reverse=True)
    if sorted_bio:
        fig = _plot_bar_chart(
            [b["name"][:35] for b in sorted_bio],
            [b["capacity_mw"] for b in sorted_bio],
            "Biomass Power Plants by Capacity (MW)",
            "Capacity (MW)", "",
            MODE_COLORS["biomass"],
        )
        st.pyplot(fig)
        plt.close(fig)

    # Type breakdown
    type_counts = {}
    for b in BIOMASS_PLANTS:
        type_counts[b["type"]] = type_counts.get(b["type"], 0) + 1
    fig2 = _plot_bar_chart(
        list(type_counts.keys()),
        list(type_counts.values()),
        "Facilities by Fuel/Technology Type",
        "Count", "",
        ACCENT_GREEN,
    )
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(BIOMASS_PLANTS)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "biomass_bioenergy.csv", "Download Biomass CSV")


def _render_green_hydrogen():
    """Mode 7: Green Hydrogen."""
    st.markdown("#### Green Hydrogen Projects")
    st.markdown(
        "Green hydrogen -- produced by electrolysis powered by renewable energy -- "
        "is emerging as a key decarbonization pathway for industry, transport, and "
        "energy storage. Mega-projects in Saudi Arabia, Australia, and Chile aim to "
        "produce millions of tonnes of clean hydrogen annually."
    )

    total_cap = sum(h["capacity_mw"] for h in GREEN_HYDROGEN)
    operational = sum(1 for h in GREEN_HYDROGEN if h["status"] == "Operational")
    construction = sum(1 for h in GREEN_HYDROGEN if "Construction" in h["status"])
    planning = sum(1 for h in GREEN_HYDROGEN if h["status"] == "Planning")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Projects", len(GREEN_HYDROGEN))
    c2.metric("Total Capacity", f"{total_cap:,} MW")
    c3.metric("Operational", operational)
    c4.metric("Under Construction / Planned", f"{construction} / {planning}")

    st.markdown("##### Global Green Hydrogen Projects")
    m = _build_curated_map(
        GREEN_HYDROGEN, "lat", "lon", "name",
        MODE_COLORS["hydrogen"], _hydrogen_popup,
    )
    # Color-code by status
    for item in GREEN_HYDROGEN:
        status = item.get("status", "")
        if status == "Operational":
            color = ACCENT_GREEN
        elif "Construction" in status:
            color = ACCENT_AMBER
        elif "Pilot" in status:
            color = ACCENT_CYAN
        else:
            color = ACCENT_TEAL
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(_hydrogen_popup(item), max_width=320),
            tooltip=escape(str(item["name"])),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        "**Legend:** "
        '<span style="color:#10b981;">&#9679; Operational</span> | '
        '<span style="color:#f59e0b;">&#9679; Under Construction</span> | '
        '<span style="color:#06b6d4;">&#9679; Pilot</span> | '
        '<span style="color:#14b8a6;">&#9679; Planning</span>',
        unsafe_allow_html=True,
    )

    sorted_h = sorted(GREEN_HYDROGEN, key=lambda x: x["capacity_mw"], reverse=True)[:15]
    fig = _plot_bar_chart(
        [h["name"][:35] for h in sorted_h],
        [h["capacity_mw"] for h in sorted_h],
        "Top Green Hydrogen Projects by Capacity (MW)",
        "Capacity (MW)", "",
        MODE_COLORS["hydrogen"],
    )
    st.pyplot(fig)
    plt.close(fig)

    # Status breakdown
    status_caps = {}
    for h in GREEN_HYDROGEN:
        status_caps[h["status"]] = status_caps.get(h["status"], 0) + h["capacity_mw"]
    fig2 = _plot_bar_chart(
        list(status_caps.keys()),
        list(status_caps.values()),
        "Total Capacity by Project Status (MW)",
        "Capacity (MW)", "",
        ACCENT_TEAL,
    )
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(GREEN_HYDROGEN)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "green_hydrogen_projects.csv", "Download Green Hydrogen CSV")


def _render_solar_potential():
    """Mode 8: Solar Potential Map."""
    st.markdown("#### Global Solar Potential Map")
    st.markdown(
        "Solar irradiance -- measured as Global Horizontal Irradiance (GHI) in "
        "kWh/m\u00b2/year -- determines where solar energy is most productive. "
        "The Atacama Desert, Sahara, and Arabian Peninsula offer the highest "
        "irradiance on Earth, exceeding 2,400 kWh/m\u00b2/year."
    )

    avg_ghi = sum(s["irradiance_kwh_m2"] for s in SOLAR_POTENTIAL) / len(SOLAR_POTENTIAL)
    exceptional = sum(1 for s in SOLAR_POTENTIAL if s["rating"] == "Exceptional")
    c1, c2, c3 = st.columns(3)
    c1.metric("Regions Mapped", len(SOLAR_POTENTIAL))
    c2.metric("Avg GHI", f"{avg_ghi:,.0f} kWh/m\u00b2/yr")
    c3.metric("Exceptional Zones", exceptional)

    st.markdown("##### Global Solar Irradiance Hotspots")
    m = folium.Map(
        location=[20.0, 0.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
        attr="TerraScout AI",
    )
    for item in SOLAR_POTENTIAL:
        ghi = item["irradiance_kwh_m2"]
        # Color scale based on irradiance
        if ghi >= 2500:
            color = "#ff4500"
            radius = 18
        elif ghi >= 2200:
            color = "#ff8c00"
            radius = 15
        elif ghi >= 2000:
            color = "#ffa500"
            radius = 12
        elif ghi >= 1800:
            color = "#ffd700"
            radius = 10
        else:
            color = "#ffff00"
            radius = 8
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(_solar_potential_popup(item), max_width=320),
            tooltip=escape(f"{item['name']} - {ghi} kWh/m\u00b2/yr"),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        "**Irradiance Scale:** "
        '<span style="color:#ff4500;">&#9679; Exceptional (2500+)</span> | '
        '<span style="color:#ff8c00;">&#9679; Excellent (2200+)</span> | '
        '<span style="color:#ffa500;">&#9679; Very Good (2000+)</span> | '
        '<span style="color:#ffd700;">&#9679; Good (1800+)</span>  '
        "(kWh/m\u00b2/year)",
        unsafe_allow_html=True,
    )

    sorted_regions = sorted(SOLAR_POTENTIAL, key=lambda x: x["irradiance_kwh_m2"], reverse=True)
    fig = _plot_bar_chart(
        [s["name"][:30] for s in sorted_regions],
        [s["irradiance_kwh_m2"] for s in sorted_regions],
        "Global Solar Irradiance by Region (kWh/m\u00b2/yr)",
        "GHI (kWh/m\u00b2/yr)", "",
        ACCENT_ORANGE,
    )
    st.pyplot(fig)
    plt.close(fig)

    # Scatter visualization
    fig2 = _plot_scatter_map(
        SOLAR_POTENTIAL, "lat", "lon", "irradiance_kwh_m2", "name",
        "Solar Irradiance Hotspots (bubble size = GHI)",
        ACCENT_AMBER, size_scale=0.05,
    )
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(SOLAR_POTENTIAL)
    df = df.sort_values("irradiance_kwh_m2", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "solar_potential_regions.csv", "Download Solar Potential CSV")


def _render_wind_potential():
    """Mode 9: Wind Potential Map."""
    st.markdown("#### Global Wind Potential Map")
    st.markdown(
        "Wind resources are measured by average wind speed at hub height (typically "
        "80-120m). The best onshore sites include Patagonia, the US Great Plains, and "
        "Inner Mongolia, while premium offshore sites include the North Sea, Taiwan "
        "Strait, and Baltic Sea."
    )

    avg_speed = sum(w["wind_speed_ms"] for w in WIND_POTENTIAL) / len(WIND_POTENTIAL)
    offshore = sum(1 for w in WIND_POTENTIAL if "Offshore" in w["type"])
    exceptional = sum(1 for w in WIND_POTENTIAL if w["rating"] == "Exceptional")
    c1, c2, c3 = st.columns(3)
    c1.metric("Regions Mapped", len(WIND_POTENTIAL))
    c2.metric("Avg Wind Speed", f"{avg_speed:.1f} m/s")
    c3.metric("Exceptional Zones", exceptional)

    st.markdown("##### Global Wind Resource Hotspots")
    m = folium.Map(
        location=[30.0, 0.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
        attr="TerraScout AI",
    )
    for item in WIND_POTENTIAL:
        speed = item["wind_speed_ms"]
        if speed >= 10.0:
            color = "#00bfff"
            radius = 16
        elif speed >= 9.0:
            color = "#1e90ff"
            radius = 13
        elif speed >= 8.0:
            color = "#4169e1"
            radius = 10
        else:
            color = "#6495ed"
            radius = 8
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(_wind_potential_popup(item), max_width=320),
            tooltip=escape(f"{item['name']} - {speed} m/s"),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        "**Wind Speed Scale:** "
        '<span style="color:#00bfff;">&#9679; Exceptional (10+ m/s)</span> | '
        '<span style="color:#1e90ff;">&#9679; Excellent (9+ m/s)</span> | '
        '<span style="color:#4169e1;">&#9679; Very Good (8+ m/s)</span> | '
        '<span style="color:#6495ed;">&#9679; Good (&lt;8 m/s)</span>',
        unsafe_allow_html=True,
    )

    sorted_regions = sorted(WIND_POTENTIAL, key=lambda x: x["wind_speed_ms"], reverse=True)
    fig = _plot_bar_chart(
        [w["name"][:30] for w in sorted_regions],
        [w["wind_speed_ms"] for w in sorted_regions],
        "Global Wind Resources by Region (m/s)",
        "Wind Speed (m/s)", "",
        ACCENT_BLUE,
    )
    st.pyplot(fig)
    plt.close(fig)

    # Offshore vs onshore comparison
    type_speeds = {}
    for w in WIND_POTENTIAL:
        wtype = w["type"]
        if wtype not in type_speeds:
            type_speeds[wtype] = []
        type_speeds[wtype].append(w["wind_speed_ms"])
    type_avg = {k: sum(v) / len(v) for k, v in type_speeds.items()}
    fig2 = _plot_bar_chart(
        list(type_avg.keys()),
        list(type_avg.values()),
        "Average Wind Speed by Type (m/s)",
        "Avg Speed (m/s)", "",
        ACCENT_CYAN,
    )
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(WIND_POTENTIAL)
    df = df.sort_values("wind_speed_ms", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "wind_potential_regions.csv", "Download Wind Potential CSV")


def _render_ev_infrastructure():
    """Mode 10: Electric Vehicle Infrastructure."""
    st.markdown("#### Electric Vehicle Infrastructure")
    st.markdown(
        "The EV revolution requires massive infrastructure: battery gigafactories, "
        "ultra-rapid charging networks, and vehicle assembly plants. From Tesla "
        "Gigafactories to CATL battery plants and Ionity charging hubs, this map "
        "tracks the global EV ecosystem."
    )

    factories = sum(1 for e in EV_INFRASTRUCTURE if "Factory" in e["type"])
    charging = sum(1 for e in EV_INFRASTRUCTURE if "Charg" in e["type"] or "Supercharger" in e["type"])
    countries = len(set(e["country"] for e in EV_INFRASTRUCTURE))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(EV_INFRASTRUCTURE))
    c2.metric("Factories", factories)
    c3.metric("Charging Sites", charging)
    c4.metric("Countries", countries)

    st.markdown("##### Global EV Infrastructure Map")
    m = folium.Map(
        location=[30.0, 10.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
        attr="TerraScout AI",
    )
    for item in EV_INFRASTRUCTURE:
        itype = item["type"]
        if "Battery" in itype:
            color = ACCENT_LIME
            icon_prefix = "B"
        elif "EV" in itype and "Factory" in itype:
            color = ACCENT_GREEN
            icon_prefix = "EV"
        elif "Supercharger" in itype:
            color = ACCENT_RED
            icon_prefix = "SC"
        elif "Charg" in itype:
            color = ACCENT_CYAN
            icon_prefix = "C"
        else:
            color = ACCENT_AMBER
            icon_prefix = "?"
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(_ev_popup(item), max_width=320),
            tooltip=escape(str(item["name"])),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        "**Legend:** "
        '<span style="color:#84cc16;">&#9679; Battery Factory</span> | '
        '<span style="color:#10b981;">&#9679; EV + Battery Factory</span> | '
        '<span style="color:#ef4444;">&#9679; Supercharger Hub</span> | '
        '<span style="color:#06b6d4;">&#9679; Charging Network</span> | '
        '<span style="color:#f59e0b;">&#9679; Other</span>',
        unsafe_allow_html=True,
    )

    # Country breakdown
    country_counts = {}
    for e in EV_INFRASTRUCTURE:
        country_counts[e["country"]] = country_counts.get(e["country"], 0) + 1
    sorted_cc = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    fig = _plot_bar_chart(
        [c[0] for c in sorted_cc],
        [c[1] for c in sorted_cc],
        "EV Infrastructure Sites by Country",
        "Number of Sites", "",
        MODE_COLORS["ev"],
    )
    st.pyplot(fig)
    plt.close(fig)

    # Type breakdown
    type_counts = {}
    for e in EV_INFRASTRUCTURE:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
    fig2 = _plot_bar_chart(
        list(type_counts.keys()),
        list(type_counts.values()),
        "EV Infrastructure by Type",
        "Count", "",
        ACCENT_LIME,
    )
    st.pyplot(fig2)
    plt.close(fig2)

    # Timeline
    year_counts = {}
    for e in EV_INFRASTRUCTURE:
        year_counts[e["year"]] = year_counts.get(e["year"], 0) + 1
    sorted_years = sorted(year_counts.items())
    fig3 = _plot_bar_chart(
        [str(y[0]) for y in sorted_years],
        [y[1] for y in sorted_years],
        "EV Infrastructure Openings by Year",
        "Year", "Sites Opened",
        ACCENT_GREEN,
        horizontal=False,
    )
    st.pyplot(fig3)
    plt.close(fig3)

    df = pd.DataFrame(EV_INFRASTRUCTURE)
    df = df.sort_values("year", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")
    _csv_download(df, "ev_infrastructure.csv", "Download EV Infrastructure CSV")


# ═══════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════
def render_renewable_maps_tab():
    """Render the Renewable Energy & Green Maps tab."""

    # Tab header
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>\U0001f33f Renewable Energy & Green Maps</h4>'
        '<p>Solar farms, wind farms, hydroelectric, geothermal & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Mode selector
    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        index=0,
        key="renewable_map_mode",
    )

    st.markdown("---")

    # Dispatch to mode renderer
    mode_idx = MAP_MODES.index(mode)
    renderers = [
        _render_solar_farms,
        _render_wind_farms,
        _render_hydro_dams,
        _render_geothermal,
        _render_tidal_wave,
        _render_biomass,
        _render_green_hydrogen,
        _render_solar_potential,
        _render_wind_potential,
        _render_ev_infrastructure,
    ]
    renderers[mode_idx]()

    # Footer
    st.markdown("---")
    st.caption(
        "Data sources: OpenStreetMap (Overpass API), curated datasets of major "
        "installations. Capacity figures are approximate and may reflect nameplate "
        "or planned capacity. | TerraScout AI - Renewable Energy & Green Maps"
    )
