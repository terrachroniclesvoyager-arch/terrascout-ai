# -*- coding: utf-8 -*-
"""
Disaster & Risk Maps module for TerraScout AI.
Provides 10 disaster/risk map types using free APIs and hardcoded datasets.
Maps: Tectonic Plates, Volcanoes, Tsunamis, Flood Risk, Landslide Risk,
Tornado Alley, Hurricane Tracks, Drought Monitor, Nuclear Risk, Asteroid Impacts.
"""

import io
import html
import math
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USGS_EQ_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
NOAA_TSUNAMI_API = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events"
EONET_API = "https://eonet.gsfc.nasa.gov/api/v3/events"
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
OVERPASS_API = "https://overpass-api.de/api/interpreter"

MAP_TYPES = [
    "Tectonic Plate Boundaries",
    "Volcano Map",
    "Tsunami Zones",
    "Flood Risk",
    "Landslide Risk",
    "Tornado Alley",
    "Hurricane Tracks",
    "Drought Monitor",
    "Nuclear Risk Zones",
    "Asteroid Impact Sites",
]

RISK_COLORS = {
    "extreme": "#dc2626",
    "high": "#ef4444",
    "moderate": "#f97316",
    "low": "#f59e0b",
    "minimal": "#10b981",
    "info": "#06b6d4",
    "purple": "#8b5cf6",
    "pink": "#ec4899",
}

# ---------------------------------------------------------------------------
# 1. TECTONIC PLATE BOUNDARIES DATA
# ---------------------------------------------------------------------------
PLATE_BOUNDARIES = {
    "Pacific-North American": {
        "color": "#ef4444",
        "type": "Transform/Subduction",
        "coords": [
            [51.0, 179.0], [50.0, -175.0], [48.5, -170.0], [46.0, -165.0],
            [44.0, -160.0], [41.0, -155.0], [38.0, -148.0], [35.0, -140.0],
            [32.0, -132.0], [30.0, -125.0], [28.0, -120.0], [25.0, -115.0],
            [22.0, -110.0], [18.0, -106.0], [15.0, -103.0],
        ],
    },
    "Pacific-Philippine": {
        "color": "#f97316",
        "type": "Subduction",
        "coords": [
            [35.0, 142.0], [30.0, 140.0], [25.0, 137.0], [20.0, 135.0],
            [15.0, 132.0], [10.0, 130.0], [5.0, 128.0], [0.0, 127.0],
        ],
    },
    "Eurasian-African (Mediterranean)": {
        "color": "#f59e0b",
        "type": "Convergent",
        "coords": [
            [-10.0, -30.0], [-5.0, -25.0], [0.0, -18.0], [10.0, -15.0],
            [20.0, -12.0], [30.0, -8.0], [35.0, -5.0], [36.0, 0.0],
            [37.0, 5.0], [37.5, 10.0], [38.0, 15.0], [38.0, 20.0],
            [37.5, 25.0], [37.0, 30.0], [36.0, 35.0], [35.0, 40.0],
        ],
    },
    "Nazca-South American": {
        "color": "#dc2626",
        "type": "Subduction",
        "coords": [
            [5.0, -82.0], [0.0, -81.0], [-5.0, -81.5], [-10.0, -79.0],
            [-15.0, -76.0], [-20.0, -71.5], [-25.0, -71.0], [-30.0, -72.0],
            [-35.0, -73.0], [-40.0, -75.0], [-45.0, -76.0],
        ],
    },
    "Indo-Australian-Eurasian": {
        "color": "#8b5cf6",
        "type": "Convergent",
        "coords": [
            [35.0, 70.0], [33.0, 75.0], [30.0, 80.0], [28.0, 85.0],
            [26.0, 90.0], [23.0, 95.0], [18.0, 95.5], [10.0, 93.0],
            [5.0, 94.0], [0.0, 97.0], [-5.0, 100.0], [-8.0, 105.0],
            [-10.0, 110.0], [-10.5, 115.0], [-10.0, 120.0],
        ],
    },
    "Mid-Atlantic Ridge": {
        "color": "#10b981",
        "type": "Divergent",
        "coords": [
            [87.0, 0.0], [80.0, 5.0], [73.0, 8.0], [66.0, -18.0],
            [63.0, -20.0], [55.0, -32.0], [45.0, -28.0], [35.0, -35.0],
            [25.0, -45.0], [15.0, -46.0], [5.0, -32.0], [0.0, -20.0],
            [-10.0, -14.0], [-20.0, -12.0], [-30.0, -14.0], [-40.0, -16.0],
            [-50.0, -5.0], [-55.0, -1.0], [-58.0, 0.0],
        ],
    },
    "East Pacific Rise": {
        "color": "#06b6d4",
        "type": "Divergent",
        "coords": [
            [22.0, -108.0], [18.0, -107.0], [13.0, -104.0], [8.0, -103.0],
            [3.0, -102.0], [-2.0, -101.0], [-8.0, -107.0], [-15.0, -112.0],
            [-22.0, -113.0], [-30.0, -112.0], [-38.0, -110.0],
            [-45.0, -115.0], [-55.0, -120.0],
        ],
    },
    "Pacific-Antarctic Ridge": {
        "color": "#ec4899",
        "type": "Divergent",
        "coords": [
            [-55.0, -120.0], [-56.0, -130.0], [-58.0, -140.0],
            [-60.0, -150.0], [-62.0, -160.0], [-63.0, -170.0],
            [-64.0, 180.0], [-63.0, 170.0], [-62.0, 160.0],
            [-60.0, 150.0], [-55.0, 145.0],
        ],
    },
    "San Andreas Fault": {
        "color": "#ff0000",
        "type": "Transform",
        "coords": [
            [40.5, -124.5], [39.0, -123.0], [38.0, -122.5], [37.0, -121.8],
            [36.0, -120.5], [35.0, -119.5], [34.5, -118.0], [34.0, -116.5],
            [33.0, -115.5], [32.5, -115.5],
        ],
    },
    "Ring of Fire (Western Pacific)": {
        "color": "#ff4444",
        "type": "Subduction",
        "coords": [
            [-45.0, 167.0], [-40.0, 175.0], [-35.0, 178.0], [-30.0, -178.0],
            [-20.0, -175.0], [-15.0, -173.0], [-10.0, 165.0], [-5.0, 155.0],
            [0.0, 145.0], [5.0, 130.0], [10.0, 127.0], [15.0, 122.0],
            [20.0, 121.0], [25.0, 123.0], [30.0, 130.0], [35.0, 140.0],
            [40.0, 143.0], [45.0, 150.0], [50.0, 157.0], [55.0, 163.0],
            [60.0, 170.0],
        ],
    },
}

# ---------------------------------------------------------------------------
# 2. VOLCANO DATA (100+ worldwide)
# ---------------------------------------------------------------------------
VOLCANOES = [
    {"name": "Mount Fuji", "lat": 35.36, "lon": 138.73, "type": "Stratovolcano", "elevation": 3776, "last_eruption": "1707", "country": "Japan"},
    {"name": "Mount Vesuvius", "lat": 40.82, "lon": 14.43, "type": "Stratovolcano", "elevation": 1281, "last_eruption": "1944", "country": "Italy"},
    {"name": "Mount Etna", "lat": 37.75, "lon": 14.99, "type": "Stratovolcano", "elevation": 3357, "last_eruption": "2024", "country": "Italy"},
    {"name": "Kilauea", "lat": 19.42, "lon": -155.29, "type": "Shield", "elevation": 1247, "last_eruption": "2023", "country": "USA"},
    {"name": "Mauna Loa", "lat": 19.48, "lon": -155.61, "type": "Shield", "elevation": 4169, "last_eruption": "2022", "country": "USA"},
    {"name": "Mount St. Helens", "lat": 46.20, "lon": -122.18, "type": "Stratovolcano", "elevation": 2549, "last_eruption": "2008", "country": "USA"},
    {"name": "Mount Rainier", "lat": 46.85, "lon": -121.76, "type": "Stratovolcano", "elevation": 4392, "last_eruption": "1894", "country": "USA"},
    {"name": "Yellowstone Caldera", "lat": 44.43, "lon": -110.59, "type": "Caldera", "elevation": 2805, "last_eruption": "-70000", "country": "USA"},
    {"name": "Krakatoa", "lat": -6.10, "lon": 105.42, "type": "Caldera", "elevation": 813, "last_eruption": "2023", "country": "Indonesia"},
    {"name": "Mount Merapi", "lat": -7.54, "lon": 110.45, "type": "Stratovolcano", "elevation": 2968, "last_eruption": "2023", "country": "Indonesia"},
    {"name": "Mount Tambora", "lat": -8.25, "lon": 118.00, "type": "Stratovolcano", "elevation": 2850, "last_eruption": "1967", "country": "Indonesia"},
    {"name": "Pinatubo", "lat": 15.13, "lon": 120.35, "type": "Stratovolcano", "elevation": 1486, "last_eruption": "1991", "country": "Philippines"},
    {"name": "Taal", "lat": 14.01, "lon": 120.99, "type": "Caldera", "elevation": 311, "last_eruption": "2022", "country": "Philippines"},
    {"name": "Mayon", "lat": 13.26, "lon": 123.69, "type": "Stratovolcano", "elevation": 2462, "last_eruption": "2024", "country": "Philippines"},
    {"name": "Mount Pinatubo", "lat": 15.13, "lon": 120.35, "type": "Stratovolcano", "elevation": 1486, "last_eruption": "1991", "country": "Philippines"},
    {"name": "Popocatepetl", "lat": 19.02, "lon": -98.63, "type": "Stratovolcano", "elevation": 5426, "last_eruption": "2024", "country": "Mexico"},
    {"name": "Colima", "lat": 19.51, "lon": -103.62, "type": "Stratovolcano", "elevation": 3839, "last_eruption": "2019", "country": "Mexico"},
    {"name": "Cotopaxi", "lat": -0.68, "lon": -78.44, "type": "Stratovolcano", "elevation": 5897, "last_eruption": "2023", "country": "Ecuador"},
    {"name": "Tungurahua", "lat": -1.47, "lon": -78.44, "type": "Stratovolcano", "elevation": 5023, "last_eruption": "2016", "country": "Ecuador"},
    {"name": "Chimborazo", "lat": -1.47, "lon": -78.82, "type": "Stratovolcano", "elevation": 6263, "last_eruption": "550", "country": "Ecuador"},
    {"name": "Nevado del Ruiz", "lat": 4.89, "lon": -75.32, "type": "Stratovolcano", "elevation": 5321, "last_eruption": "2024", "country": "Colombia"},
    {"name": "Galeras", "lat": 1.22, "lon": -77.37, "type": "Stratovolcano", "elevation": 4276, "last_eruption": "2014", "country": "Colombia"},
    {"name": "Villarrica", "lat": -39.42, "lon": -71.93, "type": "Stratovolcano", "elevation": 2847, "last_eruption": "2024", "country": "Chile"},
    {"name": "Calbuco", "lat": -41.33, "lon": -72.61, "type": "Stratovolcano", "elevation": 2003, "last_eruption": "2015", "country": "Chile"},
    {"name": "Mount Erebus", "lat": -77.53, "lon": 167.17, "type": "Stratovolcano", "elevation": 3794, "last_eruption": "2024", "country": "Antarctica"},
    {"name": "Eyjafjallajokull", "lat": 63.63, "lon": -19.63, "type": "Stratovolcano", "elevation": 1651, "last_eruption": "2010", "country": "Iceland"},
    {"name": "Hekla", "lat": 63.98, "lon": -19.70, "type": "Stratovolcano", "elevation": 1491, "last_eruption": "2000", "country": "Iceland"},
    {"name": "Katla", "lat": 63.63, "lon": -19.05, "type": "Subglacial", "elevation": 1512, "last_eruption": "1918", "country": "Iceland"},
    {"name": "Fagradalsfjall", "lat": 63.88, "lon": -22.27, "type": "Tuya", "elevation": 385, "last_eruption": "2024", "country": "Iceland"},
    {"name": "Stromboli", "lat": 38.79, "lon": 15.21, "type": "Stratovolcano", "elevation": 924, "last_eruption": "2024", "country": "Italy"},
    {"name": "Santorini", "lat": 36.40, "lon": 25.40, "type": "Caldera", "elevation": 367, "last_eruption": "1950", "country": "Greece"},
    {"name": "Teide", "lat": 28.27, "lon": -16.64, "type": "Stratovolcano", "elevation": 3718, "last_eruption": "1909", "country": "Spain"},
    {"name": "Mount Cameroon", "lat": 4.20, "lon": 9.17, "type": "Stratovolcano", "elevation": 4095, "last_eruption": "2012", "country": "Cameroon"},
    {"name": "Nyiragongo", "lat": -1.52, "lon": 29.25, "type": "Stratovolcano", "elevation": 3470, "last_eruption": "2021", "country": "DR Congo"},
    {"name": "Nyamuragira", "lat": -1.41, "lon": 29.20, "type": "Shield", "elevation": 3058, "last_eruption": "2024", "country": "DR Congo"},
    {"name": "Ol Doinyo Lengai", "lat": -2.76, "lon": 35.91, "type": "Stratovolcano", "elevation": 2962, "last_eruption": "2024", "country": "Tanzania"},
    {"name": "Erta Ale", "lat": 13.60, "lon": 40.67, "type": "Shield", "elevation": 613, "last_eruption": "2024", "country": "Ethiopia"},
    {"name": "Mount Kenya", "lat": -0.15, "lon": 37.31, "type": "Stratovolcano", "elevation": 5199, "last_eruption": "-2600000", "country": "Kenya"},
    {"name": "Piton de la Fournaise", "lat": -21.24, "lon": 55.71, "type": "Shield", "elevation": 2632, "last_eruption": "2024", "country": "Reunion"},
    {"name": "Klyuchevskoy", "lat": 56.06, "lon": 160.64, "type": "Stratovolcano", "elevation": 4750, "last_eruption": "2024", "country": "Russia"},
    {"name": "Shiveluch", "lat": 56.65, "lon": 161.36, "type": "Stratovolcano", "elevation": 3283, "last_eruption": "2024", "country": "Russia"},
    {"name": "Bezymianny", "lat": 55.97, "lon": 160.59, "type": "Stratovolcano", "elevation": 2882, "last_eruption": "2024", "country": "Russia"},
    {"name": "Karymsky", "lat": 54.05, "lon": 159.44, "type": "Stratovolcano", "elevation": 1536, "last_eruption": "2023", "country": "Russia"},
    {"name": "Aso", "lat": 32.88, "lon": 131.10, "type": "Caldera", "elevation": 1592, "last_eruption": "2023", "country": "Japan"},
    {"name": "Sakurajima", "lat": 31.58, "lon": 130.66, "type": "Stratovolcano", "elevation": 1117, "last_eruption": "2024", "country": "Japan"},
    {"name": "Unzen", "lat": 32.76, "lon": 130.30, "type": "Complex", "elevation": 1500, "last_eruption": "1995", "country": "Japan"},
    {"name": "Suwanosejima", "lat": 29.64, "lon": 129.71, "type": "Stratovolcano", "elevation": 796, "last_eruption": "2024", "country": "Japan"},
    {"name": "White Island", "lat": -37.52, "lon": 177.18, "type": "Stratovolcano", "elevation": 321, "last_eruption": "2019", "country": "New Zealand"},
    {"name": "Ruapehu", "lat": -39.28, "lon": 175.57, "type": "Stratovolcano", "elevation": 2797, "last_eruption": "2007", "country": "New Zealand"},
    {"name": "Tongariro", "lat": -39.13, "lon": 175.64, "type": "Stratovolcano", "elevation": 1978, "last_eruption": "2012", "country": "New Zealand"},
    {"name": "Taupo", "lat": -38.82, "lon": 176.00, "type": "Caldera", "elevation": 760, "last_eruption": "232", "country": "New Zealand"},
    {"name": "Agung", "lat": -8.34, "lon": 115.51, "type": "Stratovolcano", "elevation": 3142, "last_eruption": "2019", "country": "Indonesia"},
    {"name": "Sinabung", "lat": 3.17, "lon": 98.39, "type": "Stratovolcano", "elevation": 2460, "last_eruption": "2021", "country": "Indonesia"},
    {"name": "Semeru", "lat": -8.11, "lon": 112.92, "type": "Stratovolcano", "elevation": 3676, "last_eruption": "2024", "country": "Indonesia"},
    {"name": "Bromo", "lat": -7.94, "lon": 112.95, "type": "Stratovolcano", "elevation": 2329, "last_eruption": "2019", "country": "Indonesia"},
    {"name": "Rinjani", "lat": -8.42, "lon": 116.47, "type": "Stratovolcano", "elevation": 3726, "last_eruption": "2016", "country": "Indonesia"},
    {"name": "Kelud", "lat": -7.93, "lon": 112.31, "type": "Stratovolcano", "elevation": 1731, "last_eruption": "2014", "country": "Indonesia"},
    {"name": "Mount Pele", "lat": 14.81, "lon": -61.17, "type": "Stratovolcano", "elevation": 1397, "last_eruption": "1932", "country": "Martinique"},
    {"name": "Soufriere Hills", "lat": 16.72, "lon": -62.18, "type": "Stratovolcano", "elevation": 915, "last_eruption": "2013", "country": "Montserrat"},
    {"name": "La Soufriere", "lat": 13.33, "lon": -61.18, "type": "Stratovolcano", "elevation": 1234, "last_eruption": "2021", "country": "St. Vincent"},
    {"name": "Arenal", "lat": 10.46, "lon": -84.70, "type": "Stratovolcano", "elevation": 1670, "last_eruption": "2010", "country": "Costa Rica"},
    {"name": "Irazu", "lat": 9.98, "lon": -83.85, "type": "Stratovolcano", "elevation": 3432, "last_eruption": "1994", "country": "Costa Rica"},
    {"name": "Fuego", "lat": 14.47, "lon": -90.88, "type": "Stratovolcano", "elevation": 3763, "last_eruption": "2024", "country": "Guatemala"},
    {"name": "Pacaya", "lat": 14.38, "lon": -90.60, "type": "Complex", "elevation": 2552, "last_eruption": "2024", "country": "Guatemala"},
    {"name": "Santa Maria", "lat": 14.76, "lon": -91.55, "type": "Stratovolcano", "elevation": 3772, "last_eruption": "2024", "country": "Guatemala"},
    {"name": "Masaya", "lat": 11.98, "lon": -86.16, "type": "Caldera", "elevation": 635, "last_eruption": "2024", "country": "Nicaragua"},
    {"name": "San Cristobal", "lat": 12.70, "lon": -87.00, "type": "Stratovolcano", "elevation": 1745, "last_eruption": "2015", "country": "Nicaragua"},
    {"name": "Kilimanjaro", "lat": -3.07, "lon": 37.35, "type": "Stratovolcano", "elevation": 5895, "last_eruption": "-360000", "country": "Tanzania"},
    {"name": "Mount Elgon", "lat": 1.12, "lon": 34.56, "type": "Shield", "elevation": 4321, "last_eruption": "-10000000", "country": "Uganda"},
    {"name": "Deception Island", "lat": -62.97, "lon": -60.65, "type": "Caldera", "elevation": 576, "last_eruption": "1970", "country": "Antarctica"},
    {"name": "Mount Spurr", "lat": 61.30, "lon": -152.25, "type": "Stratovolcano", "elevation": 3374, "last_eruption": "1992", "country": "USA"},
    {"name": "Augustine", "lat": 59.36, "lon": -153.43, "type": "Lava dome", "elevation": 1252, "last_eruption": "2006", "country": "USA"},
    {"name": "Redoubt", "lat": 60.49, "lon": -152.74, "type": "Stratovolcano", "elevation": 3108, "last_eruption": "2009", "country": "USA"},
    {"name": "Mount Shasta", "lat": 41.41, "lon": -122.19, "type": "Stratovolcano", "elevation": 4322, "last_eruption": "1250", "country": "USA"},
    {"name": "Lassen Peak", "lat": 40.49, "lon": -121.51, "type": "Lava dome", "elevation": 3189, "last_eruption": "1917", "country": "USA"},
    {"name": "Mount Hood", "lat": 45.37, "lon": -121.70, "type": "Stratovolcano", "elevation": 3429, "last_eruption": "1866", "country": "USA"},
    {"name": "Mount Baker", "lat": 48.78, "lon": -121.81, "type": "Stratovolcano", "elevation": 3286, "last_eruption": "1880", "country": "USA"},
    {"name": "Glacier Peak", "lat": 48.11, "lon": -121.11, "type": "Stratovolcano", "elevation": 3213, "last_eruption": "1700", "country": "USA"},
    {"name": "Avachinsky", "lat": 53.26, "lon": 158.83, "type": "Stratovolcano", "elevation": 2741, "last_eruption": "2001", "country": "Russia"},
    {"name": "Tolbachik", "lat": 55.83, "lon": 160.33, "type": "Shield", "elevation": 3682, "last_eruption": "2013", "country": "Russia"},
    {"name": "Mount Demavend", "lat": 35.95, "lon": 52.11, "type": "Stratovolcano", "elevation": 5610, "last_eruption": "-5350", "country": "Iran"},
    {"name": "Mount Ararat", "lat": 39.70, "lon": 44.30, "type": "Stratovolcano", "elevation": 5137, "last_eruption": "-2500", "country": "Turkey"},
    {"name": "Nevado Ojos del Salado", "lat": -27.11, "lon": -68.54, "type": "Stratovolcano", "elevation": 6893, "last_eruption": "750", "country": "Chile"},
    {"name": "Llaima", "lat": -38.69, "lon": -71.73, "type": "Stratovolcano", "elevation": 3125, "last_eruption": "2009", "country": "Chile"},
    {"name": "Osorno", "lat": -41.10, "lon": -72.49, "type": "Stratovolcano", "elevation": 2652, "last_eruption": "1869", "country": "Chile"},
    {"name": "Misti", "lat": -16.29, "lon": -71.41, "type": "Stratovolcano", "elevation": 5822, "last_eruption": "1985", "country": "Peru"},
    {"name": "Ubinas", "lat": -16.36, "lon": -70.90, "type": "Stratovolcano", "elevation": 5672, "last_eruption": "2024", "country": "Peru"},
    {"name": "Sangay", "lat": -2.00, "lon": -78.34, "type": "Stratovolcano", "elevation": 5230, "last_eruption": "2024", "country": "Ecuador"},
    {"name": "Reventador", "lat": -0.08, "lon": -77.66, "type": "Stratovolcano", "elevation": 3562, "last_eruption": "2024", "country": "Ecuador"},
    {"name": "Piton des Neiges", "lat": -21.10, "lon": 55.48, "type": "Shield", "elevation": 3069, "last_eruption": "-10000", "country": "Reunion"},
    {"name": "Heard Island", "lat": -53.11, "lon": 73.51, "type": "Stratovolcano", "elevation": 2745, "last_eruption": "2024", "country": "Australia"},
    {"name": "Mount Yasur", "lat": -19.53, "lon": 169.44, "type": "Stratovolcano", "elevation": 361, "last_eruption": "2024", "country": "Vanuatu"},
    {"name": "Ambae", "lat": -15.40, "lon": 167.84, "type": "Shield", "elevation": 1496, "last_eruption": "2019", "country": "Vanuatu"},
    {"name": "Ulawun", "lat": -5.05, "lon": 151.33, "type": "Stratovolcano", "elevation": 2334, "last_eruption": "2023", "country": "Papua New Guinea"},
    {"name": "Rabaul", "lat": -4.27, "lon": 152.20, "type": "Caldera", "elevation": 688, "last_eruption": "2014", "country": "Papua New Guinea"},
    {"name": "Manam", "lat": -4.10, "lon": 145.04, "type": "Stratovolcano", "elevation": 1807, "last_eruption": "2024", "country": "Papua New Guinea"},
    {"name": "Dukono", "lat": 1.69, "lon": 127.88, "type": "Complex", "elevation": 1229, "last_eruption": "2024", "country": "Indonesia"},
    {"name": "Ibu", "lat": 1.49, "lon": 127.63, "type": "Stratovolcano", "elevation": 1325, "last_eruption": "2024", "country": "Indonesia"},
    {"name": "Marapi", "lat": -0.38, "lon": 100.47, "type": "Complex", "elevation": 2891, "last_eruption": "2024", "country": "Indonesia"},
    {"name": "Lewotolo", "lat": -8.27, "lon": 123.51, "type": "Stratovolcano", "elevation": 1423, "last_eruption": "2020", "country": "Indonesia"},
    {"name": "Turrialba", "lat": 10.03, "lon": -83.77, "type": "Stratovolcano", "elevation": 3340, "last_eruption": "2020", "country": "Costa Rica"},
    {"name": "Rincon de la Vieja", "lat": 10.83, "lon": -85.32, "type": "Complex", "elevation": 1916, "last_eruption": "2024", "country": "Costa Rica"},
    {"name": "Cumbre Vieja", "lat": 28.57, "lon": -17.84, "type": "Fissure vent", "elevation": 1949, "last_eruption": "2021", "country": "Spain"},
    {"name": "Barren Island", "lat": 12.28, "lon": 93.86, "type": "Stratovolcano", "elevation": 354, "last_eruption": "2021", "country": "India"},
]

# ---------------------------------------------------------------------------
# 3. TSUNAMI-PRONE COASTLINES
# ---------------------------------------------------------------------------
TSUNAMI_COASTLINES = [
    {"name": "Pacific Coast Japan", "coords": [[35.0, 140.0], [38.0, 141.5], [41.0, 142.0], [43.0, 145.0]], "color": "#ef4444", "risk": "Extreme"},
    {"name": "Chile-Peru Trench", "coords": [[-18.0, -71.0], [-25.0, -71.0], [-33.0, -72.0], [-40.0, -74.0]], "color": "#ef4444", "risk": "Extreme"},
    {"name": "Cascadia Subduction", "coords": [[40.0, -124.5], [43.0, -124.5], [46.0, -124.0], [48.5, -125.0]], "color": "#dc2626", "risk": "Extreme"},
    {"name": "Sumatra-Andaman", "coords": [[-5.0, 100.0], [0.0, 96.0], [5.0, 94.0], [10.0, 93.0], [14.0, 93.0]], "color": "#ef4444", "risk": "Extreme"},
    {"name": "Tonga Trench", "coords": [[-15.0, -173.0], [-18.0, -174.0], [-22.0, -175.0], [-25.0, -176.0]], "color": "#f97316", "risk": "High"},
    {"name": "Alaska-Aleutians", "coords": [[55.0, -160.0], [53.0, -168.0], [52.0, -175.0], [51.0, 178.0]], "color": "#f97316", "risk": "High"},
    {"name": "Mediterranean", "coords": [[35.0, 15.0], [36.0, 20.0], [35.0, 25.0], [36.0, 30.0]], "color": "#f59e0b", "risk": "Moderate"},
    {"name": "Caribbean", "coords": [[12.0, -62.0], [15.0, -65.0], [18.0, -68.0], [19.5, -72.0]], "color": "#f59e0b", "risk": "Moderate"},
    {"name": "Philippines Trench", "coords": [[5.0, 127.0], [8.0, 127.0], [11.0, 126.5], [14.0, 125.0]], "color": "#f97316", "risk": "High"},
    {"name": "New Zealand East", "coords": [[-38.0, 178.0], [-40.0, 177.5], [-42.0, 175.0], [-44.0, 172.0]], "color": "#f59e0b", "risk": "Moderate"},
]

# ---------------------------------------------------------------------------
# 5. LANDSLIDE ZONES
# ---------------------------------------------------------------------------
LANDSLIDE_ZONES = [
    {"name": "Himalayan Foothills", "lat": 28.5, "lon": 84.0, "risk": "Extreme", "notes": "Steep terrain, monsoon rains, seismic activity"},
    {"name": "Andes - Colombia", "lat": 5.0, "lon": -75.5, "risk": "Extreme", "notes": "Steep volcanic terrain, heavy rainfall"},
    {"name": "Central America Highlands", "lat": 14.5, "lon": -89.0, "risk": "High", "notes": "Volcanic soils, hurricane rainfall"},
    {"name": "Italian Alps/Dolomites", "lat": 46.4, "lon": 11.8, "risk": "High", "notes": "Steep limestone, glacial retreat"},
    {"name": "Philippines Mountains", "lat": 16.0, "lon": 121.0, "risk": "Extreme", "notes": "Typhoon rainfall, volcanic terrain"},
    {"name": "Japan Mountains", "lat": 36.0, "lon": 138.0, "risk": "High", "notes": "Steep terrain, earthquakes, typhoons"},
    {"name": "Papua New Guinea Highlands", "lat": -5.5, "lon": 145.0, "risk": "High", "notes": "Steep terrain, heavy rainfall"},
    {"name": "Southeast Brazil", "lat": -22.5, "lon": -43.0, "risk": "High", "notes": "Serra do Mar escarpment, tropical rains"},
    {"name": "Western Ghats India", "lat": 12.0, "lon": 75.5, "risk": "High", "notes": "Monsoon rains, steep laterite slopes"},
    {"name": "Sichuan China", "lat": 31.0, "lon": 103.0, "risk": "Extreme", "notes": "Earthquake zone, steep gorges"},
    {"name": "Pacific Northwest USA", "lat": 47.0, "lon": -122.0, "risk": "Moderate", "notes": "Heavy rain, volcanic soils"},
    {"name": "Norwegian Fjords", "lat": 62.0, "lon": 7.0, "risk": "Moderate", "notes": "Steep fjord walls, glacial deposits"},
    {"name": "Swiss Alps", "lat": 46.8, "lon": 8.2, "risk": "Moderate", "notes": "Permafrost thaw, steep terrain"},
    {"name": "Taiwan Mountains", "lat": 23.5, "lon": 121.0, "risk": "Extreme", "notes": "Typhoons, earthquakes, steep slopes"},
    {"name": "Indonesia (Java)", "lat": -7.5, "lon": 110.0, "risk": "High", "notes": "Volcanic terrain, monsoon rainfall"},
]

# ---------------------------------------------------------------------------
# 6. TORNADO ALLEY DATA
# ---------------------------------------------------------------------------
TORNADO_ALLEY_COORDS = [
    [36.0, -102.0], [36.0, -94.0], [40.0, -92.0], [43.0, -94.0],
    [43.0, -100.0], [40.0, -103.0], [36.0, -102.0],
]

DIXIE_ALLEY_COORDS = [
    [30.0, -92.0], [30.0, -84.0], [35.0, -84.0], [36.0, -88.0],
    [35.0, -92.0], [30.0, -92.0],
]

TORNADO_HOTSPOTS = [
    {"name": "Moore, Oklahoma", "lat": 35.34, "lon": -97.49, "notable": "EF5 tornadoes in 1999, 2013"},
    {"name": "Joplin, Missouri", "lat": 37.08, "lon": -94.51, "notable": "EF5 in 2011, 158 killed"},
    {"name": "Tuscaloosa, Alabama", "lat": 33.21, "lon": -87.57, "notable": "Super Outbreak 2011"},
    {"name": "Xenia, Ohio", "lat": 39.68, "lon": -83.94, "notable": "F5 in 1974 Super Outbreak"},
    {"name": "Greensburg, Kansas", "lat": 37.60, "lon": -99.29, "notable": "EF5 in 2007, 95% destroyed"},
    {"name": "Jarrell, Texas", "lat": 30.82, "lon": -97.60, "notable": "F5 in 1997"},
    {"name": "Bridge Creek, Oklahoma", "lat": 35.23, "lon": -97.75, "notable": "301 mph wind recorded 1999"},
    {"name": "Tri-State Area (MO-IL-IN)", "lat": 37.75, "lon": -89.0, "notable": "1925 Tri-State F5, 695 killed"},
    {"name": "Waco, Texas", "lat": 31.55, "lon": -97.15, "notable": "1953 tornado, 114 killed"},
    {"name": "Tupelo, Mississippi", "lat": 34.26, "lon": -88.70, "notable": "1936 tornado, 216 killed"},
]

# ---------------------------------------------------------------------------
# 7. HURRICANE TRACKS DATA
# ---------------------------------------------------------------------------
HURRICANE_TRACKS = [
    {
        "name": "Katrina (2005)", "category": 5, "color": "#dc2626",
        "path": [[23.4, -75.1], [24.5, -76.0], [25.4, -78.4], [25.9, -80.1],
                 [26.2, -82.0], [27.2, -85.0], [28.2, -88.0], [29.3, -89.6],
                 [31.0, -89.5], [33.0, -89.0], [35.0, -87.5]],
    },
    {
        "name": "Harvey (2017)", "category": 4, "color": "#ef4444",
        "path": [[15.0, -58.0], [16.0, -63.0], [17.5, -68.0], [18.0, -73.0],
                 [19.5, -78.0], [21.5, -83.0], [24.0, -90.0], [26.0, -94.0],
                 [27.8, -96.5], [28.5, -97.0], [29.0, -96.0], [29.5, -95.0]],
    },
    {
        "name": "Maria (2017)", "category": 5, "color": "#dc2626",
        "path": [[12.0, -51.0], [13.0, -55.0], [14.5, -59.0], [15.5, -62.0],
                 [16.5, -65.0], [18.0, -67.5], [19.5, -68.5], [21.0, -69.5],
                 [23.0, -71.0], [26.0, -72.0], [30.0, -70.0], [34.0, -66.0]],
    },
    {
        "name": "Irma (2017)", "category": 5, "color": "#dc2626",
        "path": [[16.0, -30.0], [16.5, -40.0], [17.0, -50.0], [17.5, -57.0],
                 [18.0, -62.0], [18.5, -65.0], [19.5, -68.0], [21.5, -72.0],
                 [23.0, -78.0], [24.5, -80.5], [25.5, -81.5], [27.0, -82.0],
                 [29.0, -83.0], [31.0, -84.0], [33.0, -85.0]],
    },
    {
        "name": "Dorian (2019)", "category": 5, "color": "#dc2626",
        "path": [[14.0, -55.0], [16.0, -60.0], [18.0, -65.0], [20.0, -69.0],
                 [22.0, -73.0], [24.0, -76.0], [26.0, -77.5], [26.5, -78.0],
                 [27.5, -78.5], [29.0, -79.5], [31.0, -80.0], [33.5, -78.5],
                 [36.0, -75.0], [40.0, -70.0], [44.0, -63.0]],
    },
    {
        "name": "Sandy (2012)", "category": 3, "color": "#f97316",
        "path": [[14.0, -78.0], [16.0, -79.0], [18.0, -77.5], [20.0, -76.0],
                 [23.0, -76.5], [25.0, -76.0], [28.0, -75.5], [30.0, -74.0],
                 [33.0, -73.0], [36.0, -72.0], [38.0, -73.0], [39.5, -74.5]],
    },
    {
        "name": "Michael (2018)", "category": 5, "color": "#dc2626",
        "path": [[17.5, -86.0], [18.5, -86.5], [20.0, -86.5], [22.0, -86.0],
                 [24.0, -86.0], [26.0, -86.5], [28.0, -86.0], [29.5, -85.5],
                 [30.5, -85.0], [32.0, -84.0], [34.0, -82.0], [36.0, -78.0]],
    },
    {
        "name": "Ian (2022)", "category": 4, "color": "#ef4444",
        "path": [[14.5, -72.0], [15.5, -75.0], [17.0, -79.0], [19.0, -81.0],
                 [21.0, -82.5], [22.5, -83.5], [24.0, -83.5], [25.5, -83.0],
                 [26.8, -82.5], [28.0, -82.0], [29.5, -81.5], [31.0, -80.5],
                 [33.0, -79.5]],
    },
    {
        "name": "Ida (2021)", "category": 4, "color": "#ef4444",
        "path": [[16.0, -73.0], [17.5, -76.0], [19.0, -79.5], [21.0, -82.0],
                 [23.0, -84.0], [25.0, -86.0], [27.0, -88.0], [28.5, -89.5],
                 [29.5, -90.0], [31.0, -89.5], [33.5, -87.0], [37.0, -82.0],
                 [40.0, -75.0]],
    },
    {
        "name": "Laura (2020)", "category": 4, "color": "#ef4444",
        "path": [[14.0, -55.0], [15.5, -60.0], [17.0, -65.0], [18.0, -69.0],
                 [19.5, -73.0], [21.0, -78.0], [23.0, -83.0], [25.0, -87.0],
                 [27.0, -90.0], [28.5, -92.0], [30.0, -93.5], [32.0, -93.0],
                 [34.0, -91.0]],
    },
]

# ---------------------------------------------------------------------------
# 9. NUCLEAR PLANT DATA (fetched via Overpass, but fallback)
# ---------------------------------------------------------------------------
NUCLEAR_PLANTS_FALLBACK = [
    {"name": "Chernobyl", "lat": 51.39, "lon": 30.10, "country": "Ukraine", "status": "Decommissioned", "mw": 0},
    {"name": "Fukushima Daiichi", "lat": 37.42, "lon": 141.03, "country": "Japan", "status": "Decommissioned", "mw": 0},
    {"name": "Three Mile Island", "lat": 40.15, "lon": -76.72, "country": "USA", "status": "Decommissioned", "mw": 0},
    {"name": "Zaporizhzhia", "lat": 47.51, "lon": 34.59, "country": "Ukraine", "status": "Shutdown", "mw": 5700},
    {"name": "Bruce", "lat": 44.33, "lon": -81.60, "country": "Canada", "status": "Active", "mw": 6384},
    {"name": "Kashiwazaki-Kariwa", "lat": 37.43, "lon": 138.60, "country": "Japan", "status": "Idle", "mw": 7965},
    {"name": "Hanul", "lat": 37.09, "lon": 129.38, "country": "South Korea", "status": "Active", "mw": 5928},
    {"name": "Gravelines", "lat": 51.01, "lon": 2.11, "country": "France", "status": "Active", "mw": 5460},
    {"name": "Paluel", "lat": 49.86, "lon": 0.63, "country": "France", "status": "Active", "mw": 5320},
    {"name": "Cattenom", "lat": 49.41, "lon": 6.22, "country": "France", "status": "Active", "mw": 5200},
    {"name": "Palo Verde", "lat": 33.39, "lon": -112.86, "country": "USA", "status": "Active", "mw": 3937},
    {"name": "Vogtle", "lat": 33.14, "lon": -81.76, "country": "USA", "status": "Active", "mw": 4600},
    {"name": "South Texas", "lat": 28.80, "lon": -96.05, "country": "USA", "status": "Active", "mw": 2710},
    {"name": "Hinkley Point C", "lat": 51.21, "lon": -3.13, "country": "UK", "status": "Construction", "mw": 3260},
    {"name": "Taishan", "lat": 21.92, "lon": 112.98, "country": "China", "status": "Active", "mw": 3460},
    {"name": "Barakah", "lat": 23.96, "lon": 52.26, "country": "UAE", "status": "Active", "mw": 5600},
    {"name": "Kudankulam", "lat": 8.17, "lon": 77.71, "country": "India", "status": "Active", "mw": 2000},
    {"name": "Kola", "lat": 67.46, "lon": 32.47, "country": "Russia", "status": "Active", "mw": 1760},
    {"name": "Leningrad II", "lat": 59.84, "lon": 29.03, "country": "Russia", "status": "Active", "mw": 2400},
    {"name": "Cernavoda", "lat": 44.32, "lon": 28.06, "country": "Romania", "status": "Active", "mw": 1300},
]

# ---------------------------------------------------------------------------
# 10. ASTEROID IMPACT SITES
# ---------------------------------------------------------------------------
IMPACT_CRATERS = [
    {"name": "Chicxulub", "lat": 21.40, "lon": -89.52, "diameter_km": 150, "age_mya": 66, "notes": "K-Pg mass extinction event, dinosaur killer"},
    {"name": "Vredefort", "lat": -27.00, "lon": 27.50, "diameter_km": 300, "age_mya": 2023, "notes": "Largest confirmed impact structure on Earth"},
    {"name": "Sudbury", "lat": 46.60, "lon": -81.18, "diameter_km": 130, "age_mya": 1849, "notes": "Major nickel-copper mining district"},
    {"name": "Popigai", "lat": 71.65, "lon": 111.18, "diameter_km": 100, "age_mya": 35.7, "notes": "Contains industrial-grade diamonds"},
    {"name": "Manicouagan", "lat": 51.38, "lon": -68.70, "diameter_km": 100, "age_mya": 214, "notes": "Eye of Quebec - visible ring lake from space"},
    {"name": "Acraman", "lat": -32.02, "lon": 135.45, "diameter_km": 90, "age_mya": 580, "notes": "Ejecta found 300km away in Flinders Ranges"},
    {"name": "Chesapeake Bay", "lat": 37.28, "lon": -76.02, "diameter_km": 85, "age_mya": 35.5, "notes": "Buried under sediment, affects groundwater"},
    {"name": "Morokweng", "lat": -26.47, "lon": 23.53, "diameter_km": 70, "age_mya": 145, "notes": "Jurassic-Cretaceous boundary impact"},
    {"name": "Kara", "lat": 69.10, "lon": 64.15, "diameter_km": 65, "age_mya": 70.3, "notes": "Arctic Russia impact structure"},
    {"name": "Barringer (Meteor Crater)", "lat": 35.03, "lon": -111.02, "diameter_km": 1.2, "age_mya": 0.05, "notes": "Best preserved crater, Arizona, ~50,000 years old"},
    {"name": "Nördlinger Ries", "lat": 48.85, "lon": 10.61, "diameter_km": 24, "age_mya": 14.8, "notes": "Town of Nördlingen built inside crater"},
    {"name": "Rochechouart", "lat": 45.82, "lon": 0.78, "diameter_km": 23, "age_mya": 214, "notes": "Central France, same age as Manicouagan"},
    {"name": "Siljan", "lat": 61.02, "lon": 14.87, "diameter_km": 52, "age_mya": 376, "notes": "Largest impact structure in Europe"},
    {"name": "Clearwater Lakes", "lat": 56.05, "lon": -74.07, "diameter_km": 36, "age_mya": 290, "notes": "Twin craters - dual asteroid impact"},
    {"name": "Mistastin", "lat": 55.88, "lon": -63.32, "diameter_km": 28, "age_mya": 36.4, "notes": "Contains labradorite, Labrador Canada"},
    {"name": "Haughton", "lat": 75.38, "lon": -89.67, "diameter_km": 23, "age_mya": 39, "notes": "Mars analog research site, Devon Island"},
    {"name": "Gosses Bluff", "lat": -23.82, "lon": 132.31, "diameter_km": 22, "age_mya": 142, "notes": "Sacred Aboriginal site, central Australia"},
    {"name": "Lonar", "lat": 19.98, "lon": 76.51, "diameter_km": 1.8, "age_mya": 0.052, "notes": "Only hypervelocity crater in basaltic rock"},
    {"name": "Wolfe Creek", "lat": -19.17, "lon": 127.80, "diameter_km": 0.88, "age_mya": 0.3, "notes": "Well-preserved crater in Western Australia"},
    {"name": "Kaali", "lat": 58.37, "lon": 22.67, "diameter_km": 0.11, "age_mya": 0.004, "notes": "Meteorite crater field in Estonia, ~4000 years old"},
    {"name": "Pingualuit", "lat": 61.28, "lon": -73.65, "diameter_km": 3.4, "age_mya": 1.4, "notes": "Crystal-clear lake in Quebec, nearly perfect circle"},
    {"name": "Bosumtwi", "lat": 6.50, "lon": -1.41, "diameter_km": 10.5, "age_mya": 1.07, "notes": "Sacred lake in Ghana, source of tektites"},
    {"name": "Shoemaker (Teague Ring)", "lat": -25.87, "lon": 120.88, "diameter_km": 30, "age_mya": 1630, "notes": "Named after Eugene Shoemaker, Western Australia"},
    {"name": "Steinheim", "lat": 48.69, "lon": 10.07, "diameter_km": 3.8, "age_mya": 14.8, "notes": "Sister crater to Nördlinger Ries"},
    {"name": "Upheaval Dome", "lat": 38.44, "lon": -109.93, "diameter_km": 10, "age_mya": 170, "notes": "Canyonlands National Park, Utah"},
    {"name": "Tswaing", "lat": -25.41, "lon": 28.08, "diameter_km": 1.13, "age_mya": 0.22, "notes": "Salt pan crater near Pretoria, South Africa"},
    {"name": "Henbury", "lat": -24.57, "lon": 133.15, "diameter_km": 0.16, "age_mya": 0.005, "notes": "Cluster of 12 craters, central Australia"},
    {"name": "Campo del Cielo", "lat": -27.63, "lon": -61.68, "diameter_km": 0.05, "age_mya": 0.004, "notes": "Iron meteorite field, Argentina"},
    {"name": "Tunguska", "lat": 60.92, "lon": 101.90, "diameter_km": 0, "age_mya": 0.000116, "notes": "1908 airburst, no crater, 2,150 km2 forest flattened"},
    {"name": "Chelyabinsk", "lat": 54.82, "lon": 61.12, "diameter_km": 0, "age_mya": 0.000012, "notes": "2013 airburst, 1,500 injured, caught on dashcams"},
]


# =========================================================================
# DATA FETCHING FUNCTIONS
# =========================================================================

@st.cache_data(ttl=3600)
def fetch_earthquakes_for_plates(min_mag: float = 4.5, days: int = 30,
                                  limit: int = 500) -> list:
    """Fetch recent earthquakes from USGS for plate boundary overlay."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"),
        "minmagnitude": min_mag,
        "limit": limit,
        "orderby": "magnitude",
    }
    try:
        r = requests.get(USGS_EQ_API, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        results = []
        for f in data.get("features", []):
            p = f["properties"]
            c = f["geometry"]["coordinates"]
            results.append({
                "place": p.get("place", "Unknown"),
                "mag": p.get("mag", 0),
                "time": datetime.utcfromtimestamp(p["time"] / 1000).strftime("%Y-%m-%d %H:%M"),
                "lat": c[1],
                "lon": c[0],
                "depth": c[2],
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=3600)
def fetch_tsunami_events(min_year: int = 1900, max_results: int = 200) -> list:
    """Fetch historical tsunami events from NOAA."""
    try:
        params = {"minYear": min_year, "maxYear": 2026}
        r = requests.get(NOAA_TSUNAMI_API, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        results = []
        for ev in items[:max_results]:
            lat = ev.get("latitude") or ev.get("lat")
            lon = ev.get("longitude") or ev.get("lon") or ev.get("lng")
            if lat is None or lon is None:
                continue
            try:
                lat, lon = float(lat), float(lon)
            except (ValueError, TypeError):
                continue
            results.append({
                "year": ev.get("year", "Unknown"),
                "month": ev.get("month", ""),
                "country": ev.get("country", ev.get("locationName", "Unknown")),
                "lat": lat,
                "lon": lon,
                "max_water_height": ev.get("maxWaterHeight", ev.get("tpiMaxWaterHeight", None)),
                "deaths": ev.get("deaths", ev.get("deathsTotal", None)),
                "cause": ev.get("cause", ev.get("tpiCauseCode", "Unknown")),
                "magnitude": ev.get("eqMagnitude", ev.get("magnitude", None)),
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=3600)
def fetch_flood_features(lat: float, lon: float, radius: int = 50000) -> list:
    """Fetch waterway/flood-prone features near a location using Overpass."""
    query = f"""
    [out:json][timeout:25];
    (
      way["waterway"="river"](around:{radius},{lat},{lon});
      way["waterway"="canal"](around:{radius},{lat},{lon});
      way["natural"="water"]["water"="reservoir"](around:{radius},{lat},{lon});
      way["flood_prone"="yes"](around:{radius},{lat},{lon});
      node["natural"="spring"](around:{radius},{lat},{lon});
    );
    out center 100;
    """
    try:
        r = requests.post(OVERPASS_API, data={"data": query}, timeout=30)
        r.raise_for_status()
        elements = r.json().get("elements", [])
        results = []
        for el in elements[:100]:
            clat = el.get("lat") or el.get("center", {}).get("lat")
            clon = el.get("lon") or el.get("center", {}).get("lon")
            if clat is None or clon is None:
                continue
            tags = el.get("tags", {})
            results.append({
                "name": tags.get("name", "Unnamed"),
                "type": tags.get("waterway", tags.get("natural", "water")),
                "lat": clat,
                "lon": clon,
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=3600)
def fetch_precipitation(lat: float, lon: float, days: int = 14) -> dict:
    """Fetch recent precipitation data from Open-Meteo."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,rain_sum",
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "timezone": "auto",
    }
    try:
        r = requests.get(OPEN_METEO_API, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_drought_data(lat: float, lon: float, days: int = 90) -> dict:
    """Fetch soil moisture and precipitation for drought analysis."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,et0_fao_evapotranspiration",
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "timezone": "auto",
    }
    try:
        r = requests.get(OPEN_METEO_API, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_soil_moisture(lat: float, lon: float, days: int = 90) -> dict:
    """Fetch soil moisture data from Open-Meteo."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm",
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "timezone": "auto",
    }
    try:
        r = requests.get(OPEN_METEO_API, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_eonet_storms() -> list:
    """Fetch current severe storm events from NASA EONET."""
    try:
        params = {"category": "severeStorms", "status": "open", "limit": 50}
        r = requests.get(EONET_API, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = []
        for ev in data.get("events", []):
            geom = ev.get("geometry", [])
            if not geom:
                continue
            coords = geom[-1].get("coordinates", [])
            if len(coords) < 2:
                continue
            results.append({
                "title": ev.get("title", "Unknown"),
                "date": geom[-1].get("date", "")[:10],
                "lon": coords[0],
                "lat": coords[1],
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=3600)
def fetch_spc_reports(days: int = 1) -> list:
    """Fetch SPC storm reports for tornado/severe weather."""
    today = datetime.utcnow().strftime("%y%m%d")
    url = f"https://www.spc.noaa.gov/climo/reports/{today}_rpts_filtered_torn.csv"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        lines = r.text.strip().split("\n")
        if len(lines) < 2:
            return []
        results = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 8:
                try:
                    results.append({
                        "time": parts[0],
                        "f_scale": parts[1],
                        "location": parts[2],
                        "state": parts[3] if len(parts) > 3 else "",
                        "lat": float(parts[5]) if len(parts) > 5 else 0,
                        "lon": float(parts[6]) if len(parts) > 6 else 0,
                    })
                except (ValueError, IndexError):
                    continue
        return results
    except Exception:
        return []


@st.cache_data(ttl=3600)
def fetch_nuclear_plants_overpass(lat: float = 48.0, lon: float = 10.0,
                                   radius: int = 5000000) -> list:
    """Fetch nuclear power plants from Overpass API."""
    query = """
    [out:json][timeout:30];
    (
      node["generator:source"="nuclear"];
      way["generator:source"="nuclear"];
      node["plant:source"="nuclear"];
      way["plant:source"="nuclear"];
    );
    out center 200;
    """
    try:
        r = requests.post(OVERPASS_API, data={"data": query}, timeout=35)
        r.raise_for_status()
        elements = r.json().get("elements", [])
        results = []
        seen = set()
        for el in elements:
            clat = el.get("lat") or el.get("center", {}).get("lat")
            clon = el.get("lon") or el.get("center", {}).get("lon")
            if clat is None or clon is None:
                continue
            tags = el.get("tags", {})
            name = tags.get("name", tags.get("operator", "Unknown"))
            key = f"{round(clat, 2)}_{round(clon, 2)}"
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "name": name,
                "lat": clat,
                "lon": clon,
                "operator": tags.get("operator", "Unknown"),
                "status": tags.get("plant:output:electricity", tags.get("generator:output:electricity", "Unknown")),
            })
        return results
    except Exception:
        return []


# =========================================================================
# MAP BUILDER FUNCTIONS
# =========================================================================

def _base_map(lat: float = 20.0, lon: float = 0.0, zoom: int = 2) -> folium.Map:
    """Create a base folium map with dark theme."""
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        width="100%",
        height="100%",
    )


def _show_map(m: folium.Map, height: int = 550):
    """Render folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _mag_color(mag: float) -> str:
    if mag < 3.0:
        return "#10b981"
    elif mag < 5.0:
        return "#f59e0b"
    elif mag < 6.0:
        return "#f97316"
    elif mag < 7.0:
        return "#ef4444"
    return "#dc2626"


def _dark_chart(figsize=(10, 4)):
    """Create matplotlib figure with dark theme."""
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


# =========================================================================
# MAP 1: TECTONIC PLATE BOUNDARIES
# =========================================================================

def _render_tectonic_plates():
    """Render tectonic plate boundaries map."""
    st.markdown("""<div class="tab-header red"><h4>Tectonic Plate Boundaries</h4>
    <p>Major plate boundaries with real-time earthquake overlay from USGS</p></div>""",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        min_mag = st.slider("Min Earthquake Magnitude", 2.0, 8.0, 4.5, 0.5,
                             key="tect_minmag")
    with c2:
        eq_days = st.slider("Earthquake Days Back", 1, 90, 30, key="tect_days")
    with c3:
        show_eq = st.checkbox("Show Earthquakes", True, key="tect_show_eq")

    if st.button("Generate Tectonic Map", key="btn_tect", type="primary"):
        with st.spinner("Loading plate boundaries and earthquakes..."):
            earthquakes = fetch_earthquakes_for_plates(min_mag, eq_days) if show_eq else []

        m = _base_map(20, 0, 2)

        # Draw plate boundaries
        for name, boundary in PLATE_BOUNDARIES.items():
            folium.PolyLine(
                locations=boundary["coords"],
                color=boundary["color"],
                weight=3,
                opacity=0.8,
                popup=folium.Popup(
                    f"<b>{html.escape(name)}</b><br>Type: {html.escape(boundary['type'])}",
                    max_width=250,
                ),
                tooltip=html.escape(name),
            ).add_to(m)

        # Draw earthquakes
        for eq in earthquakes:
            folium.CircleMarker(
                location=[eq["lat"], eq["lon"]],
                radius=max(3, eq["mag"] * 1.5),
                color=_mag_color(eq["mag"]),
                fill=True,
                fill_color=_mag_color(eq["mag"]),
                fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>M{eq['mag']}</b><br>"
                    f"{html.escape(str(eq['place']))}<br>"
                    f"Depth: {eq['depth']:.1f} km<br>"
                    f"{html.escape(eq['time'])}",
                    max_width=250,
                ),
            ).add_to(m)

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Plate Boundaries", len(PLATE_BOUNDARIES))
        c2.metric("Earthquakes Shown", len(earthquakes))
        if earthquakes:
            c3.metric("Max Magnitude", f"{max(e['mag'] for e in earthquakes):.1f}")
            c4.metric("Avg Depth", f"{sum(e['depth'] for e in earthquakes) / len(earthquakes):.1f} km")
        else:
            c3.metric("Max Magnitude", "N/A")
            c4.metric("Avg Depth", "N/A")

        _show_map(m)

        # Data table
        if earthquakes:
            df = pd.DataFrame(earthquakes)
            st.subheader("Earthquake Data")
            st.dataframe(df, width="stretch")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Earthquake CSV", csv,
                               "tectonic_earthquakes.csv", "text/csv",
                               key="dl_tect")


# =========================================================================
# MAP 2: VOLCANO MAP
# =========================================================================

def _render_volcano_map():
    """Render worldwide volcano map."""
    st.markdown("""<div class="tab-header red"><h4>Volcano Map</h4>
    <p>100+ volcanoes worldwide with type, elevation, and eruption history</p></div>""",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        v_type = st.multiselect("Volcano Type", sorted(set(v["type"] for v in VOLCANOES)),
                                 default=sorted(set(v["type"] for v in VOLCANOES)),
                                 key="vol_type")
    with c2:
        v_country = st.multiselect("Country", sorted(set(v["country"] for v in VOLCANOES)),
                                    default=[], key="vol_country",
                                    help="Leave empty for all countries")

    if st.button("Generate Volcano Map", key="btn_vol", type="primary"):
        filtered = [v for v in VOLCANOES if v["type"] in v_type]
        if v_country:
            filtered = [v for v in filtered if v["country"] in v_country]

        m = _base_map(20, 0, 2)

        type_colors = {
            "Stratovolcano": "#ef4444",
            "Shield": "#f97316",
            "Caldera": "#dc2626",
            "Complex": "#8b5cf6",
            "Lava dome": "#f59e0b",
            "Subglacial": "#06b6d4",
            "Tuya": "#06b6d4",
            "Fissure vent": "#10b981",
        }

        for v in filtered:
            color = type_colors.get(v["type"], "#ec4899")
            folium.CircleMarker(
                location=[v["lat"], v["lon"]],
                radius=max(4, min(10, v["elevation"] / 800)),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>{html.escape(v['name'])}</b><br>"
                    f"Type: {html.escape(v['type'])}<br>"
                    f"Elevation: {v['elevation']}m<br>"
                    f"Last Eruption: {html.escape(str(v['last_eruption']))}<br>"
                    f"Country: {html.escape(v['country'])}",
                    max_width=280,
                ),
                tooltip=html.escape(v["name"]),
            ).add_to(m)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Volcanoes Shown", len(filtered))
        c2.metric("Countries", len(set(v["country"] for v in filtered)))
        c3.metric("Types", len(set(v["type"] for v in filtered)))
        elevations = [v["elevation"] for v in filtered]
        c4.metric("Highest", f"{max(elevations):,}m" if elevations else "N/A")

        _show_map(m)

        df = pd.DataFrame(filtered)
        st.subheader("Volcano Data")
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Volcano CSV", csv,
                           "volcanoes.csv", "text/csv", key="dl_vol")

        # Type distribution chart
        fig, ax = _dark_chart((8, 4))
        type_counts = df["type"].value_counts()
        bars = ax.barh(type_counts.index, type_counts.values, color="#ef4444", alpha=0.8)
        ax.set_xlabel("Count")
        ax.set_title("Volcano Types Distribution")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# =========================================================================
# MAP 3: TSUNAMI ZONES
# =========================================================================

def _render_tsunami_zones():
    """Render tsunami risk zones and historical events."""
    st.markdown("""<div class="tab-header red"><h4>Tsunami Zones</h4>
    <p>Tsunami-prone coastlines with historical events from NOAA database</p></div>""",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        min_year = st.slider("Min Year", 1800, 2025, 1900, key="tsu_year")
    with c2:
        max_events = st.slider("Max Events", 50, 500, 200, key="tsu_max")

    if st.button("Generate Tsunami Map", key="btn_tsu", type="primary"):
        with st.spinner("Fetching NOAA tsunami data..."):
            events = fetch_tsunami_events(min_year, max_events)

        m = _base_map(10, 140, 2)

        # Draw tsunami-prone coastlines
        for coast in TSUNAMI_COASTLINES:
            folium.PolyLine(
                locations=coast["coords"],
                color=coast["color"],
                weight=4,
                opacity=0.7,
                popup=folium.Popup(
                    f"<b>{html.escape(coast['name'])}</b><br>Risk: {html.escape(coast['risk'])}",
                    max_width=250,
                ),
                tooltip=html.escape(coast["name"]),
            ).add_to(m)

        # Draw historical events
        for ev in events:
            height = ev.get("max_water_height")
            radius = 4
            if height:
                try:
                    radius = max(3, min(15, float(height)))
                except (ValueError, TypeError):
                    pass
            color = "#ef4444" if ev.get("deaths") and str(ev["deaths"]).isdigit() and int(str(ev["deaths"])) > 100 else "#f59e0b"
            popup_text = (
                f"<b>Tsunami {html.escape(str(ev['year']))}</b><br>"
                f"Location: {html.escape(str(ev['country']))}<br>"
                f"Max Height: {html.escape(str(height or 'Unknown'))}m<br>"
                f"Deaths: {html.escape(str(ev.get('deaths', 'Unknown')))}<br>"
                f"Cause: {html.escape(str(ev.get('cause', 'Unknown')))}"
            )
            folium.CircleMarker(
                location=[ev["lat"], ev["lon"]],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=folium.Popup(popup_text, max_width=280),
            ).add_to(m)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Risk Coastlines", len(TSUNAMI_COASTLINES))
        c2.metric("Historical Events", len(events))
        deaths_list = [int(str(e["deaths"])) for e in events if e.get("deaths") and str(e["deaths"]).replace(".", "").isdigit()]
        c3.metric("Total Deaths", f"{sum(deaths_list):,}" if deaths_list else "N/A")
        c4.metric("Deadliest Year",
                  max(events, key=lambda x: int(str(x.get("deaths", 0))) if str(x.get("deaths", "0")).replace(".", "").isdigit() else 0).get("year", "N/A") if events else "N/A")

        _show_map(m)

        if events:
            df = pd.DataFrame(events)
            st.subheader("Tsunami Events")
            st.dataframe(df, width="stretch")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Tsunami CSV", csv,
                               "tsunami_events.csv", "text/csv", key="dl_tsu")


# =========================================================================
# MAP 4: FLOOD RISK
# =========================================================================

def _render_flood_risk():
    """Render flood risk analysis map."""
    st.markdown("""<div class="tab-header red"><h4>Flood Risk Analysis</h4>
    <p>Waterway features and precipitation data for flood risk assessment</p></div>""",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        flood_lat = st.number_input("Latitude", -90.0, 90.0, 51.5, key="flood_lat")
    with c2:
        flood_lon = st.number_input("Longitude", -180.0, 180.0, -0.12, key="flood_lon")
    with c3:
        flood_radius = st.slider("Search Radius (km)", 5, 100, 30, key="flood_rad")

    if st.button("Analyze Flood Risk", key="btn_flood", type="primary"):
        with st.spinner("Fetching waterway and precipitation data..."):
            features = fetch_flood_features(flood_lat, flood_lon, flood_radius * 1000)
            precip_data = fetch_precipitation(flood_lat, flood_lon, 14)

        m = _base_map(flood_lat, flood_lon, 10)

        # Center marker
        folium.Marker(
            location=[flood_lat, flood_lon],
            icon=folium.Icon(color="red", icon="info-sign"),
            popup="Analysis Center",
        ).add_to(m)

        # Search area
        folium.Circle(
            location=[flood_lat, flood_lon],
            radius=flood_radius * 1000,
            color="#06b6d4",
            fill=True,
            fill_opacity=0.1,
        ).add_to(m)

        # Waterway features
        for feat in features:
            folium.CircleMarker(
                location=[feat["lat"], feat["lon"]],
                radius=5,
                color="#3b82f6",
                fill=True,
                fill_color="#3b82f6",
                fill_opacity=0.6,
                popup=folium.Popup(
                    f"<b>{html.escape(feat['name'])}</b><br>"
                    f"Type: {html.escape(feat['type'])}",
                    max_width=250,
                ),
            ).add_to(m)

        # Precipitation analysis
        total_precip = 0
        max_daily = 0
        precip_days = []
        daily = precip_data.get("daily", {})
        dates = daily.get("time", [])
        precip_vals = daily.get("precipitation_sum", [])
        for i, (d, p) in enumerate(zip(dates, precip_vals)):
            if p is not None:
                total_precip += p
                max_daily = max(max_daily, p)
                precip_days.append({"date": d, "precipitation_mm": p})

        risk_level = "Low"
        if total_precip > 100 or max_daily > 50:
            risk_level = "High"
        elif total_precip > 50 or max_daily > 25:
            risk_level = "Moderate"
        elif total_precip > 20:
            risk_level = "Elevated"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Water Features", len(features))
        c2.metric("14-Day Precip", f"{total_precip:.1f} mm")
        c3.metric("Max Daily", f"{max_daily:.1f} mm")
        c4.metric("Flood Risk", risk_level)

        _show_map(m)

        # Precipitation chart
        if precip_days:
            fig, ax = _dark_chart((10, 4))
            pdf = pd.DataFrame(precip_days)
            ax.bar(range(len(pdf)), pdf["precipitation_mm"], color="#3b82f6", alpha=0.8)
            ax.set_xticks(range(len(pdf)))
            ax.set_xticklabels(pdf["date"], rotation=45, ha="right", fontsize=8, color="#8b97b0")
            ax.set_ylabel("Precipitation (mm)")
            ax.set_title("14-Day Precipitation")
            ax.axhline(y=25, color="#f59e0b", linestyle="--", alpha=0.5, label="Moderate threshold")
            ax.axhline(y=50, color="#ef4444", linestyle="--", alpha=0.5, label="High threshold")
            ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#8b97b0")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        if features:
            df = pd.DataFrame(features)
            st.subheader("Water Features")
            st.dataframe(df, width="stretch")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Flood Data CSV", csv,
                               "flood_features.csv", "text/csv", key="dl_flood")


# =========================================================================
# MAP 5: LANDSLIDE RISK
# =========================================================================

def _render_landslide_risk():
    """Render landslide risk assessment map."""
    st.markdown("""<div class="tab-header red"><h4>Landslide Risk Assessment</h4>
    <p>Major landslide zones with precipitation and terrain risk factors</p></div>""",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        ls_filter = st.multiselect("Risk Level", ["Extreme", "High", "Moderate"],
                                    default=["Extreme", "High", "Moderate"],
                                    key="ls_risk")
    with c2:
        show_precip = st.checkbox("Overlay Precipitation Data", True, key="ls_precip")

    if st.button("Generate Landslide Risk Map", key="btn_ls", type="primary"):
        filtered = [z for z in LANDSLIDE_ZONES if z["risk"] in ls_filter]

        m = _base_map(25, 80, 2)

        risk_colors = {"Extreme": "#dc2626", "High": "#ef4444", "Moderate": "#f59e0b"}

        precip_results = {}
        if show_precip:
            with st.spinner("Fetching precipitation data for landslide zones..."):
                for zone in filtered:
                    pdata = fetch_precipitation(zone["lat"], zone["lon"], 7)
                    daily = pdata.get("daily", {})
                    vals = daily.get("precipitation_sum", [])
                    total = sum(v for v in vals if v is not None)
                    precip_results[zone["name"]] = total

        for zone in filtered:
            color = risk_colors.get(zone["risk"], "#f59e0b")
            precip_info = ""
            if zone["name"] in precip_results:
                precip_info = f"<br>7-Day Precip: {precip_results[zone['name']]:.1f}mm"
            radius_val = {"Extreme": 35000, "High": 25000, "Moderate": 18000}.get(zone["risk"], 18000)

            folium.Circle(
                location=[zone["lat"], zone["lon"]],
                radius=radius_val * 5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.2,
                popup=folium.Popup(
                    f"<b>{html.escape(zone['name'])}</b><br>"
                    f"Risk: {html.escape(zone['risk'])}<br>"
                    f"{html.escape(zone['notes'])}{precip_info}",
                    max_width=300,
                ),
                tooltip=html.escape(zone["name"]),
            ).add_to(m)

            folium.Marker(
                location=[zone["lat"], zone["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size:10px;color:{color};font-weight:bold;">'
                         f'{html.escape(zone["name"][:20])}</div>',
                    icon_size=(150, 20),
                ),
            ).add_to(m)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Zones Shown", len(filtered))
        c2.metric("Extreme Risk", sum(1 for z in filtered if z["risk"] == "Extreme"))
        c3.metric("High Risk", sum(1 for z in filtered if z["risk"] == "High"))
        c4.metric("Moderate Risk", sum(1 for z in filtered if z["risk"] == "Moderate"))

        _show_map(m)

        # Build data table
        rows = []
        for zone in filtered:
            row = {**zone}
            if zone["name"] in precip_results:
                row["7day_precip_mm"] = round(precip_results[zone["name"]], 1)
            rows.append(row)
        df = pd.DataFrame(rows)
        st.subheader("Landslide Zone Data")
        st.dataframe(df, width="stretch")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Landslide CSV", csv,
                           "landslide_zones.csv", "text/csv", key="dl_ls")


# =========================================================================
# MAP 6: TORNADO ALLEY
# =========================================================================

def _render_tornado_alley():
    """Render Tornado Alley map with SPC reports."""
    st.markdown("""<div class="tab-header red"><h4>Tornado Alley &amp; Severe Weather</h4>
    <p>US tornado corridors with SPC storm reports and historical hotspots</p></div>""",
                unsafe_allow_html=True)

    show_hotspots = st.checkbox("Show Historical Hotspots", True, key="torn_hot")
    show_spc = st.checkbox("Fetch Today's SPC Tornado Reports", True, key="torn_spc")

    if st.button("Generate Tornado Map", key="btn_torn", type="primary"):
        spc_reports = []
        if show_spc:
            with st.spinner("Fetching SPC storm reports..."):
                spc_reports = fetch_spc_reports()

        m = _base_map(37, -95, 4)

        # Tornado Alley polygon
        folium.Polygon(
            locations=TORNADO_ALLEY_COORDS,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.15,
            popup=folium.Popup("<b>Tornado Alley</b><br>Primary US tornado corridor", max_width=250),
            tooltip="Tornado Alley",
        ).add_to(m)

        # Dixie Alley polygon
        folium.Polygon(
            locations=DIXIE_ALLEY_COORDS,
            color="#f97316",
            fill=True,
            fill_color="#f97316",
            fill_opacity=0.15,
            popup=folium.Popup("<b>Dixie Alley</b><br>Southeast US tornado corridor", max_width=250),
            tooltip="Dixie Alley",
        ).add_to(m)

        # Hotspots
        if show_hotspots:
            for spot in TORNADO_HOTSPOTS:
                folium.Marker(
                    location=[spot["lat"], spot["lon"]],
                    icon=folium.Icon(color="red", icon="warning-sign"),
                    popup=folium.Popup(
                        f"<b>{html.escape(spot['name'])}</b><br>"
                        f"{html.escape(spot['notable'])}",
                        max_width=300,
                    ),
                    tooltip=html.escape(spot["name"]),
                ).add_to(m)

        # SPC reports
        for rpt in spc_reports:
            if rpt["lat"] != 0 and rpt["lon"] != 0:
                folium.CircleMarker(
                    location=[rpt["lat"], rpt["lon"]],
                    radius=8,
                    color="#dc2626",
                    fill=True,
                    fill_color="#dc2626",
                    fill_opacity=0.8,
                    popup=folium.Popup(
                        f"<b>Tornado Report</b><br>"
                        f"Time: {html.escape(str(rpt.get('time', '')))}<br>"
                        f"F-Scale: {html.escape(str(rpt.get('f_scale', '')))}<br>"
                        f"Location: {html.escape(str(rpt.get('location', '')))}",
                        max_width=280,
                    ),
                ).add_to(m)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tornado Corridors", 2)
        c2.metric("Historical Hotspots", len(TORNADO_HOTSPOTS))
        c3.metric("Today's Reports", len(spc_reports))
        c4.metric("Active Zone States", "TX, OK, KS, NE, SD, IA, MO, IL, AL, MS")

        _show_map(m)

        if spc_reports:
            df = pd.DataFrame(spc_reports)
            st.subheader("Today's SPC Tornado Reports")
            st.dataframe(df, width="stretch")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download SPC Reports CSV", csv,
                               "spc_tornado_reports.csv", "text/csv", key="dl_torn")

        # Hotspot table
        df_hot = pd.DataFrame(TORNADO_HOTSPOTS)
        st.subheader("Historical Tornado Hotspots")
        st.dataframe(df_hot, width="stretch")


# =========================================================================
# MAP 7: HURRICANE TRACKS
# =========================================================================

def _render_hurricane_tracks():
    """Render historical hurricane tracks and current storms."""
    st.markdown("""<div class="tab-header red"><h4>Hurricane Tracks</h4>
    <p>Historical major hurricanes and current severe storms from NASA EONET</p></div>""",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        min_cat = st.slider("Min Category", 1, 5, 3, key="hurr_cat")
    with c2:
        show_eonet = st.checkbox("Show Current Storms (NASA EONET)", True, key="hurr_eonet")

    if st.button("Generate Hurricane Map", key="btn_hurr", type="primary"):
        eonet_storms = []
        if show_eonet:
            with st.spinner("Fetching current storm data from NASA EONET..."):
                eonet_storms = fetch_eonet_storms()

        filtered = [h for h in HURRICANE_TRACKS if h["category"] >= min_cat]

        m = _base_map(25, -70, 3)

        # Historical tracks
        for hurr in filtered:
            folium.PolyLine(
                locations=hurr["path"],
                color=hurr["color"],
                weight=3,
                opacity=0.8,
                popup=folium.Popup(
                    f"<b>{html.escape(hurr['name'])}</b><br>"
                    f"Category: {hurr['category']}",
                    max_width=250,
                ),
                tooltip=html.escape(hurr["name"]),
            ).add_to(m)
            # Start and end markers
            folium.CircleMarker(
                location=hurr["path"][0],
                radius=5,
                color=hurr["color"],
                fill=True,
                fill_color=hurr["color"],
                tooltip=f"{html.escape(hurr['name'])} - Origin",
            ).add_to(m)
            folium.CircleMarker(
                location=hurr["path"][-1],
                radius=7,
                color=hurr["color"],
                fill=True,
                fill_color="#ffffff",
                fill_opacity=0.8,
                tooltip=f"{html.escape(hurr['name'])} - End",
            ).add_to(m)

        # Current EONET storms
        for storm in eonet_storms:
            folium.Marker(
                location=[storm["lat"], storm["lon"]],
                icon=folium.Icon(color="orange", icon="cloud"),
                popup=folium.Popup(
                    f"<b>{html.escape(storm['title'])}</b><br>"
                    f"Date: {html.escape(storm['date'])}",
                    max_width=280,
                ),
                tooltip=html.escape(storm["title"]),
            ).add_to(m)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Historical Tracks", len(filtered))
        c2.metric("Current Storms", len(eonet_storms))
        c3.metric("Cat 5 Hurricanes", sum(1 for h in filtered if h["category"] == 5))
        c4.metric("Cat 4 Hurricanes", sum(1 for h in filtered if h["category"] == 4))

        _show_map(m)

        # Hurricane data table
        rows = [{"name": h["name"], "category": h["category"],
                 "path_points": len(h["path"])} for h in filtered]
        df = pd.DataFrame(rows)
        st.subheader("Hurricane Track Data")
        st.dataframe(df, width="stretch")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Hurricane CSV", csv,
                           "hurricane_tracks.csv", "text/csv", key="dl_hurr")

        if eonet_storms:
            df_eonet = pd.DataFrame(eonet_storms)
            st.subheader("Current Severe Storms")
            st.dataframe(df_eonet, width="stretch")


# =========================================================================
# MAP 8: DROUGHT MONITOR
# =========================================================================

def _render_drought_monitor():
    """Render drought analysis map."""
    st.markdown("""<div class="tab-header red"><h4>Drought Monitor</h4>
    <p>Soil moisture deficit and precipitation analysis using Open-Meteo</p></div>""",
                unsafe_allow_html=True)

    st.info("Enter multiple locations to compare drought conditions across regions.")

    locations = [
        {"name": "Central California", "lat": 36.77, "lon": -119.42},
        {"name": "West Texas", "lat": 31.99, "lon": -102.08},
        {"name": "Phoenix, Arizona", "lat": 33.45, "lon": -112.07},
        {"name": "Sahel, Africa", "lat": 14.0, "lon": 2.0},
        {"name": "Rajasthan, India", "lat": 26.92, "lon": 70.90},
        {"name": "Eastern Australia", "lat": -30.0, "lon": 146.0},
        {"name": "Southern Spain", "lat": 37.39, "lon": -5.98},
        {"name": "Horn of Africa", "lat": 5.0, "lon": 42.0},
    ]

    c1, c2 = st.columns(2)
    with c1:
        selected = st.multiselect("Monitoring Locations",
                                   [l["name"] for l in locations],
                                   default=[l["name"] for l in locations[:4]],
                                   key="drought_locs")
    with c2:
        drought_days = st.slider("Analysis Period (days)", 30, 180, 90, key="drought_days")

    custom_lat = st.number_input("Custom Lat (optional)", -90.0, 90.0, 0.0, key="drought_clat")
    custom_lon = st.number_input("Custom Lon (optional)", -180.0, 180.0, 0.0, key="drought_clon")

    if st.button("Analyze Drought Conditions", key="btn_drought", type="primary"):
        analysis_locs = [l for l in locations if l["name"] in selected]
        if custom_lat != 0.0 or custom_lon != 0.0:
            analysis_locs.append({"name": "Custom Location", "lat": custom_lat, "lon": custom_lon})

        results = []
        with st.spinner("Fetching drought data..."):
            for loc in analysis_locs:
                ddata = fetch_drought_data(loc["lat"], loc["lon"], drought_days)
                daily = ddata.get("daily", {})
                precip_vals = daily.get("precipitation_sum", [])
                et_vals = daily.get("et0_fao_evapotranspiration", [])
                total_precip = sum(v for v in precip_vals if v is not None)
                total_et = sum(v for v in et_vals if v is not None)
                deficit = total_precip - total_et
                rain_days = sum(1 for v in precip_vals if v is not None and v > 0.1)

                if deficit < -200:
                    severity = "Exceptional Drought"
                    color = "#730000"
                elif deficit < -100:
                    severity = "Extreme Drought"
                    color = "#dc2626"
                elif deficit < -50:
                    severity = "Severe Drought"
                    color = "#ef4444"
                elif deficit < 0:
                    severity = "Moderate Drought"
                    color = "#f97316"
                elif deficit < 50:
                    severity = "Abnormally Dry"
                    color = "#f59e0b"
                else:
                    severity = "No Drought"
                    color = "#10b981"

                results.append({
                    "name": loc["name"],
                    "lat": loc["lat"],
                    "lon": loc["lon"],
                    "total_precip_mm": round(total_precip, 1),
                    "total_et_mm": round(total_et, 1),
                    "deficit_mm": round(deficit, 1),
                    "rain_days": rain_days,
                    "severity": severity,
                    "color": color,
                })

        m = _base_map(20, 0, 2)
        for r in results:
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=12,
                color=r["color"],
                fill=True,
                fill_color=r["color"],
                fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>{html.escape(r['name'])}</b><br>"
                    f"Severity: {html.escape(r['severity'])}<br>"
                    f"Precip: {r['total_precip_mm']}mm<br>"
                    f"ET: {r['total_et_mm']}mm<br>"
                    f"Deficit: {r['deficit_mm']}mm<br>"
                    f"Rain Days: {r['rain_days']}",
                    max_width=280,
                ),
                tooltip=html.escape(f"{r['name']} - {r['severity']}"),
            ).add_to(m)

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations Analyzed", len(results))
        severe_count = sum(1 for r in results if "Drought" in r["severity"])
        c2.metric("In Drought", severe_count)
        if results:
            worst = min(results, key=lambda x: x["deficit_mm"])
            c3.metric("Worst Deficit", f"{worst['deficit_mm']}mm")
            c4.metric("Worst Location", worst["name"])

        _show_map(m)

        # Deficit comparison chart
        fig, ax = _dark_chart((10, 5))
        names = [r["name"] for r in results]
        deficits = [r["deficit_mm"] for r in results]
        colors = [r["color"] for r in results]
        bars = ax.barh(names, deficits, color=colors, alpha=0.85)
        ax.axvline(x=0, color="#8b97b0", linestyle="-", alpha=0.3)
        ax.set_xlabel("Water Deficit (mm) - Negative = Drought")
        ax.set_title(f"Drought Analysis ({drought_days}-Day Period)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame(results)
        df_display = df.drop(columns=["color"], errors="ignore")
        st.subheader("Drought Analysis Data")
        st.dataframe(df_display, width="stretch")
        csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button("Download Drought CSV", csv,
                           "drought_analysis.csv", "text/csv", key="dl_drought")


# =========================================================================
# MAP 9: NUCLEAR RISK ZONES
# =========================================================================

def _render_nuclear_risk():
    """Render nuclear power plant risk zones."""
    st.markdown("""<div class="tab-header red"><h4>Nuclear Risk Zones</h4>
    <p>Nuclear power plants with 30km evacuation zones (Overpass API + fallback data)</p></div>""",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        use_overpass = st.checkbox("Fetch from Overpass API (slower, more data)", False,
                                    key="nuke_overpass")
    with c2:
        evac_radius = st.slider("Evacuation Zone Radius (km)", 10, 80, 30, key="nuke_rad")

    if st.button("Generate Nuclear Risk Map", key="btn_nuke", type="primary"):
        plants = NUCLEAR_PLANTS_FALLBACK
        if use_overpass:
            with st.spinner("Fetching nuclear plants from OpenStreetMap..."):
                osm_plants = fetch_nuclear_plants_overpass()
                if osm_plants:
                    plants = osm_plants

        m = _base_map(35, 20, 2)

        for plant in plants:
            # Evacuation zone circle
            folium.Circle(
                location=[plant["lat"], plant["lon"]],
                radius=evac_radius * 1000,
                color="#ef4444",
                fill=True,
                fill_color="#ef4444",
                fill_opacity=0.1,
                weight=2,
            ).add_to(m)

            # 10km immediate zone
            folium.Circle(
                location=[plant["lat"], plant["lon"]],
                radius=10000,
                color="#dc2626",
                fill=True,
                fill_color="#dc2626",
                fill_opacity=0.2,
                weight=1,
            ).add_to(m)

            # Plant marker
            status = plant.get("status", plant.get("mw", "Unknown"))
            is_active = "Active" in str(status) or "active" in str(status)
            icon_color = "green" if is_active else "gray"
            popup_text = (
                f"<b>{html.escape(str(plant['name']))}</b><br>"
                f"Country: {html.escape(str(plant.get('country', plant.get('operator', 'Unknown'))))}<br>"
                f"Status: {html.escape(str(status))}<br>"
                f"Evacuation Zone: {evac_radius}km radius"
            )
            if "mw" in plant:
                popup_text += f"<br>Capacity: {plant['mw']} MW"

            folium.Marker(
                location=[plant["lat"], plant["lon"]],
                icon=folium.Icon(color=icon_color, icon="flash"),
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=html.escape(str(plant["name"])),
            ).add_to(m)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Plants Mapped", len(plants))
        if "mw" in plants[0]:
            active = sum(1 for p in plants if "Active" in str(p.get("status", "")))
            total_mw = sum(p.get("mw", 0) for p in plants if "Active" in str(p.get("status", "")))
            c2.metric("Active Plants", active)
            c3.metric("Total Active MW", f"{total_mw:,}")
            countries = len(set(p.get("country", "") for p in plants))
            c4.metric("Countries", countries)
        else:
            c2.metric("Data Source", "OpenStreetMap")
            c3.metric("Evac Radius", f"{evac_radius} km")
            c4.metric("Plants Found", len(plants))

        _show_map(m)

        df = pd.DataFrame(plants)
        st.subheader("Nuclear Plant Data")
        st.dataframe(df, width="stretch")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Nuclear Plants CSV", csv,
                           "nuclear_plants.csv", "text/csv", key="dl_nuke")


# =========================================================================
# MAP 10: ASTEROID IMPACT SITES
# =========================================================================

def _render_asteroid_impacts():
    """Render confirmed asteroid impact craters worldwide."""
    st.markdown("""<div class="tab-header red"><h4>Asteroid Impact Sites</h4>
    <p>Confirmed impact craters worldwide with diameter, age, and geological notes</p></div>""",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        min_diameter = st.slider("Min Diameter (km)", 0.0, 100.0, 0.0, 0.5,
                                  key="ast_diam")
    with c2:
        sort_by = st.selectbox("Sort By", ["diameter_km", "age_mya", "name"],
                                key="ast_sort")

    if st.button("Generate Impact Crater Map", key="btn_ast", type="primary"):
        filtered = [c for c in IMPACT_CRATERS if c["diameter_km"] >= min_diameter]
        filtered.sort(key=lambda x: x[sort_by], reverse=(sort_by != "name"))

        m = _base_map(20, 0, 2)

        for crater in filtered:
            # Size-based coloring
            diam = crater["diameter_km"]
            if diam >= 100:
                color = "#dc2626"
                radius = 15
            elif diam >= 50:
                color = "#ef4444"
                radius = 12
            elif diam >= 20:
                color = "#f97316"
                radius = 9
            elif diam >= 5:
                color = "#f59e0b"
                radius = 7
            elif diam >= 1:
                color = "#06b6d4"
                radius = 5
            else:
                color = "#10b981"
                radius = 4

            # Draw crater representation
            if diam > 0:
                folium.Circle(
                    location=[crater["lat"], crater["lon"]],
                    radius=max(5000, diam * 500),
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.15,
                    weight=1,
                ).add_to(m)

            age_str = f"{crater['age_mya']:.3f}" if crater["age_mya"] < 1 else f"{crater['age_mya']:.1f}"
            popup_text = (
                f"<b>{html.escape(crater['name'])}</b><br>"
                f"Diameter: {crater['diameter_km']} km<br>"
                f"Age: {age_str} Mya<br>"
                f"{html.escape(crater['notes'])}"
            )
            folium.CircleMarker(
                location=[crater["lat"], crater["lon"]],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=html.escape(crater["name"]),
            ).add_to(m)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Craters Shown", len(filtered))
        diameters = [c["diameter_km"] for c in filtered if c["diameter_km"] > 0]
        c2.metric("Largest", f"{max(diameters):.1f} km" if diameters else "N/A")
        ages = [c["age_mya"] for c in filtered]
        c3.metric("Oldest", f"{max(ages):.1f} Mya" if ages else "N/A")
        c4.metric("Most Recent",
                  min(filtered, key=lambda x: x["age_mya"])["name"] if filtered else "N/A")

        _show_map(m)

        # Size distribution chart
        if filtered:
            fig, ax = _dark_chart((10, 5))
            names = [c["name"][:20] for c in filtered if c["diameter_km"] > 0]
            diams = [c["diameter_km"] for c in filtered if c["diameter_km"] > 0]
            colors_list = []
            for d in diams:
                if d >= 100:
                    colors_list.append("#dc2626")
                elif d >= 50:
                    colors_list.append("#ef4444")
                elif d >= 20:
                    colors_list.append("#f97316")
                elif d >= 5:
                    colors_list.append("#f59e0b")
                else:
                    colors_list.append("#06b6d4")
            ax.barh(names, diams, color=colors_list, alpha=0.85)
            ax.set_xlabel("Diameter (km)")
            ax.set_title("Impact Crater Sizes")
            ax.set_xscale("log")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        df = pd.DataFrame(filtered)
        st.subheader("Impact Crater Data")
        st.dataframe(df, width="stretch")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Impact Craters CSV", csv,
                           "impact_craters.csv", "text/csv", key="dl_ast")


# =========================================================================
# MAIN RENDER FUNCTION
# =========================================================================

def render_disaster_maps_tab():
    """Main entry point for the Disaster & Risk Maps tab."""
    st.markdown("""<div class="tab-header red"><h4>Disaster &amp; Risk Maps</h4>
    <p>10 interactive disaster and natural hazard maps using free public APIs</p></div>""",
                unsafe_allow_html=True)

    map_choice = st.radio(
        "Select Disaster Map Type",
        MAP_TYPES,
        horizontal=True,
        key="disaster_map_type",
    )

    st.markdown("---")

    if map_choice == "Tectonic Plate Boundaries":
        _render_tectonic_plates()
    elif map_choice == "Volcano Map":
        _render_volcano_map()
    elif map_choice == "Tsunami Zones":
        _render_tsunami_zones()
    elif map_choice == "Flood Risk":
        _render_flood_risk()
    elif map_choice == "Landslide Risk":
        _render_landslide_risk()
    elif map_choice == "Tornado Alley":
        _render_tornado_alley()
    elif map_choice == "Hurricane Tracks":
        _render_hurricane_tracks()
    elif map_choice == "Drought Monitor":
        _render_drought_monitor()
    elif map_choice == "Nuclear Risk Zones":
        _render_nuclear_risk()
    elif map_choice == "Asteroid Impact Sites":
        _render_asteroid_impacts()
