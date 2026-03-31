# -*- coding: utf-8 -*-
"""
Crime & Safety Maps module for TerraScout AI.
Provides 10 interactive map modes covering global peace indices, safest cities,
travel advisories, piracy hotspots, cybercrime origins, police/fire stations,
prison locations, drug trafficking routes, and Interpol activity.
All static data is hardcoded; Overpass API is used for live amenity queries.
"""

import io
import html
import streamlit as st
import pandas as pd
try:
    import folium
    import folium.plugins as folium_plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# ──────────────────────────────────────────────────────────────────────
# COLOR PALETTE (dark theme)
# ──────────────────────────────────────────────────────────────────────
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_ACCENT = "#06b6d4"
_MUTED = "#5a6580"

# ──────────────────────────────────────────────────────────────────────
# 1. GLOBAL PEACE INDEX DATA (~163 countries, 2024 scores)
#    Lower score = more peaceful.  Scale 1.0 - 4.0
# ──────────────────────────────────────────────────────────────────────
GPI_DATA = {
    "Iceland": 1.124, "Ireland": 1.288, "Austria": 1.300, "New Zealand": 1.313,
    "Singapore": 1.326, "Switzerland": 1.339, "Portugal": 1.341, "Denmark": 1.353,
    "Slovenia": 1.357, "Malaysia": 1.368, "Czech Republic": 1.379, "Canada": 1.389,
    "Japan": 1.391, "Finland": 1.400, "Croatia": 1.408, "Hungary": 1.411,
    "Germany": 1.420, "Norway": 1.430, "Romania": 1.431, "Bulgaria": 1.432,
    "Netherlands": 1.435, "Australia": 1.442, "Belgium": 1.445, "Sweden": 1.457,
    "Bhutan": 1.462, "Chile": 1.470, "Slovakia": 1.478, "Poland": 1.480,
    "Estonia": 1.481, "Indonesia": 1.484, "Latvia": 1.492, "Lithuania": 1.497,
    "Uruguay": 1.500, "Italy": 1.503, "Spain": 1.510, "Costa Rica": 1.518,
    "Kuwait": 1.521, "Mongolia": 1.524, "South Korea": 1.527, "Albania": 1.530,
    "Oman": 1.539, "United Kingdom": 1.543, "Qatar": 1.548, "Panama": 1.553,
    "Taiwan": 1.558, "Vietnam": 1.560, "Greece": 1.563, "Botswana": 1.570,
    "Sierra Leone": 1.573, "Ghana": 1.575, "Laos": 1.578, "Tanzania": 1.580,
    "Zambia": 1.583, "Mauritius": 1.587, "Madagascar": 1.590, "Senegal": 1.592,
    "Nepal": 1.596, "Namibia": 1.600, "Serbia": 1.610, "North Macedonia": 1.612,
    "Montenegro": 1.615, "Bosnia and Herzegovina": 1.618, "Morocco": 1.620,
    "Jordan": 1.624, "Jamaica": 1.628, "Tunisia": 1.630, "Cuba": 1.632,
    "Rwanda": 1.637, "Kazakhstan": 1.640, "Georgia": 1.645, "Equatorial Guinea": 1.650,
    "United Arab Emirates": 1.652, "Bahrain": 1.655, "Trinidad and Tobago": 1.660,
    "Timor-Leste": 1.665, "Armenia": 1.668, "Bolivia": 1.670, "Paraguay": 1.675,
    "Moldova": 1.680, "Argentina": 1.685, "France": 1.687, "Bangladesh": 1.693,
    "Ecuador": 1.698, "Papua New Guinea": 1.700, "Dominican Republic": 1.705,
    "Peru": 1.710, "Togo": 1.712, "Benin": 1.715, "Malawi": 1.718,
    "Guyana": 1.720, "Angola": 1.725, "China": 1.730, "Gabon": 1.735,
    "Uzbekistan": 1.740, "Turkmenistan": 1.745, "Thailand": 1.748, "Sri Lanka": 1.750,
    "Tajikistan": 1.755, "Cyprus": 1.760, "Kyrgyzstan": 1.765, "Zimbabwe": 1.770,
    "Philippines": 1.780, "Saudi Arabia": 1.790, "Mozambique": 1.800,
    "Guatemala": 1.810, "Honduras": 1.820, "Egypt": 1.830, "El Salvador": 1.840,
    "Cambodia": 1.850, "Myanmar": 1.860, "United States": 1.870,
    "Algeria": 1.880, "Iran": 1.890, "Kenya": 1.900, "Uganda": 1.910,
    "Azerbaijan": 1.915, "Niger": 1.920, "Eritrea": 1.925, "Republic of the Congo": 1.930,
    "India": 1.950, "Ivory Coast": 1.960, "Mauritania": 1.970,
    "Cameroon": 1.980, "Chad": 1.990, "Ethiopia": 2.000, "Burundi": 2.010,
    "Guinea": 2.020, "Guinea-Bissau": 2.030, "Haiti": 2.050,
    "Turkey": 2.070, "Mexico": 2.100, "Brazil": 2.110, "South Africa": 2.120,
    "Lebanon": 2.130, "Colombia": 2.145, "Pakistan": 2.170, "Libya": 2.200,
    "Venezuela": 2.230, "Israel": 2.250, "Nigeria": 2.310,
    "Democratic Republic of the Congo": 2.380, "North Korea": 2.430,
    "Central African Republic": 2.480, "Mali": 2.510, "Sudan": 2.530,
    "Iraq": 2.560, "Ukraine": 2.620, "Somalia": 2.650,
    "Syria": 2.700, "South Sudan": 2.810, "Russia": 2.880,
    "Afghanistan": 3.113, "Yemen": 3.070,
}

# Approximate country centroids for choropleth markers
COUNTRY_COORDS = {
    "Iceland": (64.96, -19.02), "Ireland": (53.14, -7.69), "Austria": (47.52, 14.55),
    "New Zealand": (-40.90, 174.89), "Singapore": (1.35, 103.82), "Switzerland": (46.82, 8.23),
    "Portugal": (39.40, -8.22), "Denmark": (56.26, 9.50), "Slovenia": (46.15, 14.99),
    "Malaysia": (4.21, 101.98), "Czech Republic": (49.82, 15.47), "Canada": (56.13, -106.35),
    "Japan": (36.20, 138.25), "Finland": (61.92, 25.75), "Croatia": (45.10, 15.20),
    "Hungary": (47.16, 19.50), "Germany": (51.17, 10.45), "Norway": (60.47, 8.47),
    "Romania": (45.94, 24.97), "Bulgaria": (42.73, 25.49), "Netherlands": (52.13, 5.29),
    "Australia": (-25.27, 133.78), "Belgium": (50.50, 4.47), "Sweden": (60.13, 18.64),
    "Bhutan": (27.51, 90.43), "Chile": (-35.68, -71.54), "Slovakia": (48.67, 19.70),
    "Poland": (51.92, 19.15), "Estonia": (58.60, 25.01), "Indonesia": (-0.79, 113.92),
    "Latvia": (56.88, 24.60), "Lithuania": (55.17, 23.88), "Uruguay": (-32.52, -55.77),
    "Italy": (41.87, 12.57), "Spain": (40.46, -3.75), "Costa Rica": (9.75, -83.75),
    "Kuwait": (29.31, 47.48), "Mongolia": (46.86, 103.85), "South Korea": (35.91, 127.77),
    "Albania": (41.15, 20.17), "Oman": (21.47, 55.98), "United Kingdom": (55.38, -3.44),
    "Qatar": (25.35, 51.18), "Panama": (8.54, -80.78), "Taiwan": (23.70, 120.96),
    "Vietnam": (14.06, 108.28), "Greece": (39.07, 21.82), "Botswana": (-22.33, 24.68),
    "Sierra Leone": (8.46, -11.78), "Ghana": (7.95, -1.02), "Laos": (19.86, 102.50),
    "Tanzania": (-6.37, 34.89), "Zambia": (-13.13, 27.85), "Mauritius": (-20.35, 57.55),
    "Madagascar": (-18.77, 46.87), "Senegal": (14.50, -14.45), "Nepal": (28.39, 84.12),
    "Namibia": (-22.96, 18.49), "Serbia": (44.02, 21.01), "North Macedonia": (41.51, 21.75),
    "Montenegro": (42.71, 19.37), "Bosnia and Herzegovina": (43.92, 17.68),
    "Morocco": (31.79, -7.09), "Jordan": (30.59, 36.24), "Jamaica": (18.11, -77.30),
    "Tunisia": (33.89, 9.54), "Cuba": (21.52, -77.78), "Rwanda": (-1.94, 29.87),
    "Kazakhstan": (48.02, 66.92), "Georgia": (42.32, 43.36),
    "Equatorial Guinea": (1.65, 10.27), "United Arab Emirates": (23.42, 53.85),
    "Bahrain": (26.07, 50.56), "Trinidad and Tobago": (10.69, -61.22),
    "Timor-Leste": (-8.87, 125.73), "Armenia": (40.07, 45.04),
    "Bolivia": (-16.29, -63.59), "Paraguay": (-23.44, -58.44),
    "Moldova": (47.41, 28.37), "Argentina": (-38.42, -63.62), "France": (46.23, 2.21),
    "Bangladesh": (23.68, 90.36), "Ecuador": (-1.83, -78.18),
    "Papua New Guinea": (-6.31, 143.96), "Dominican Republic": (18.74, -70.16),
    "Peru": (-9.19, -75.02), "Togo": (8.62, 1.21), "Benin": (9.31, 2.32),
    "Malawi": (-13.25, 34.30), "Guyana": (4.86, -58.93), "Angola": (-11.20, 17.87),
    "China": (35.86, 104.20), "Gabon": (-0.80, 11.61), "Uzbekistan": (41.38, 64.59),
    "Turkmenistan": (38.97, 59.56), "Thailand": (15.87, 100.99),
    "Sri Lanka": (7.87, 80.77), "Tajikistan": (38.86, 71.28),
    "Cyprus": (35.13, 33.43), "Kyrgyzstan": (41.20, 74.77),
    "Zimbabwe": (-19.02, 29.15), "Philippines": (12.88, 121.77),
    "Saudi Arabia": (23.89, 45.08), "Mozambique": (-18.67, 35.53),
    "Guatemala": (15.78, -90.23), "Honduras": (15.20, -86.24),
    "Egypt": (26.82, 30.80), "El Salvador": (13.79, -88.90),
    "Cambodia": (12.57, 104.99), "Myanmar": (21.91, 95.96),
    "United States": (37.09, -95.71), "Algeria": (28.03, 1.66),
    "Iran": (32.43, 53.69), "Kenya": (-0.02, 37.91), "Uganda": (1.37, 32.29),
    "Azerbaijan": (40.14, 47.58), "Niger": (17.61, 8.08),
    "Eritrea": (15.18, 39.78), "Republic of the Congo": (-0.23, 15.83),
    "India": (20.59, 78.96), "Ivory Coast": (7.54, -5.55),
    "Mauritania": (21.01, -10.94), "Cameroon": (7.37, 12.35),
    "Chad": (15.45, 18.73), "Ethiopia": (9.15, 40.49),
    "Burundi": (-3.37, 29.92), "Guinea": (9.95, -9.70),
    "Guinea-Bissau": (11.80, -15.18), "Haiti": (18.97, -72.29),
    "Turkey": (38.96, 35.24), "Mexico": (23.63, -102.55),
    "Brazil": (-14.24, -51.93), "South Africa": (-30.56, 22.94),
    "Lebanon": (33.85, 35.86), "Colombia": (4.57, -74.30),
    "Pakistan": (30.38, 69.35), "Libya": (26.34, 17.23),
    "Venezuela": (6.42, -66.59), "Israel": (31.05, 34.85),
    "Nigeria": (9.08, 8.68), "Democratic Republic of the Congo": (-4.04, 21.76),
    "North Korea": (40.34, 127.51), "Central African Republic": (6.61, 20.94),
    "Mali": (17.57, -4.00), "Sudan": (12.86, 30.22),
    "Iraq": (33.22, 43.68), "Ukraine": (48.38, 31.17),
    "Somalia": (5.15, 46.20), "Syria": (34.80, 38.99),
    "South Sudan": (6.88, 31.31), "Russia": (61.52, 105.32),
    "Afghanistan": (33.94, 67.71), "Yemen": (15.55, 48.52),
}


def _gpi_color(score):
    """Return color based on GPI score."""
    if score < 1.4:
        return "#10b981"   # very peaceful - green
    elif score < 1.6:
        return "#34d399"   # peaceful
    elif score < 1.8:
        return "#a3e635"   # moderate-peaceful
    elif score < 2.0:
        return "#facc15"   # moderate
    elif score < 2.3:
        return "#f97316"   # less peaceful
    elif score < 2.7:
        return "#ef4444"   # dangerous
    return "#991b1b"       # very dangerous


# ──────────────────────────────────────────────────────────────────────
# 2. SAFEST CITIES DATA (~50 cities with safety scores 0-100)
# ──────────────────────────────────────────────────────────────────────
SAFEST_CITIES = [
    {"city": "Tokyo", "country": "Japan", "score": 92.0, "lat": 35.68, "lon": 139.69},
    {"city": "Singapore", "country": "Singapore", "score": 91.5, "lat": 1.35, "lon": 103.82},
    {"city": "Osaka", "country": "Japan", "score": 90.9, "lat": 34.69, "lon": 135.50},
    {"city": "Amsterdam", "country": "Netherlands", "score": 88.0, "lat": 52.37, "lon": 4.90},
    {"city": "Sydney", "country": "Australia", "score": 87.9, "lat": -33.87, "lon": 151.21},
    {"city": "Toronto", "country": "Canada", "score": 87.3, "lat": 43.65, "lon": -79.38},
    {"city": "Washington D.C.", "country": "USA", "score": 87.1, "lat": 38.91, "lon": -77.04},
    {"city": "Copenhagen", "country": "Denmark", "score": 86.4, "lat": 55.68, "lon": 12.57},
    {"city": "Seoul", "country": "South Korea", "score": 86.1, "lat": 37.57, "lon": 126.98},
    {"city": "Melbourne", "country": "Australia", "score": 85.9, "lat": -37.81, "lon": 144.96},
    {"city": "Stockholm", "country": "Sweden", "score": 85.5, "lat": 59.33, "lon": 18.07},
    {"city": "Zurich", "country": "Switzerland", "score": 85.2, "lat": 47.38, "lon": 8.54},
    {"city": "Hong Kong", "country": "China", "score": 84.7, "lat": 22.40, "lon": 114.11},
    {"city": "London", "country": "UK", "score": 84.3, "lat": 51.51, "lon": -0.13},
    {"city": "Wellington", "country": "New Zealand", "score": 84.0, "lat": -41.29, "lon": 174.78},
    {"city": "Frankfurt", "country": "Germany", "score": 83.8, "lat": 50.11, "lon": 8.68},
    {"city": "Barcelona", "country": "Spain", "score": 83.5, "lat": 41.39, "lon": 2.17},
    {"city": "Madrid", "country": "Spain", "score": 83.2, "lat": 40.42, "lon": -3.70},
    {"city": "Vienna", "country": "Austria", "score": 83.0, "lat": 48.21, "lon": 16.37},
    {"city": "Brussels", "country": "Belgium", "score": 82.6, "lat": 50.85, "lon": 4.35},
    {"city": "Helsinki", "country": "Finland", "score": 82.4, "lat": 60.17, "lon": 24.94},
    {"city": "Munich", "country": "Germany", "score": 82.1, "lat": 48.14, "lon": 11.58},
    {"city": "Dubai", "country": "UAE", "score": 81.8, "lat": 25.20, "lon": 55.27},
    {"city": "Abu Dhabi", "country": "UAE", "score": 81.5, "lat": 24.45, "lon": 54.65},
    {"city": "Taipei", "country": "Taiwan", "score": 81.3, "lat": 25.03, "lon": 121.57},
    {"city": "Prague", "country": "Czech Republic", "score": 81.0, "lat": 50.08, "lon": 14.44},
    {"city": "Reykjavik", "country": "Iceland", "score": 80.8, "lat": 64.15, "lon": -21.94},
    {"city": "Bern", "country": "Switzerland", "score": 80.5, "lat": 46.95, "lon": 7.45},
    {"city": "Oslo", "country": "Norway", "score": 80.2, "lat": 59.91, "lon": 10.75},
    {"city": "Lisbon", "country": "Portugal", "score": 80.0, "lat": 38.72, "lon": -9.14},
    {"city": "Montreal", "country": "Canada", "score": 79.8, "lat": 45.50, "lon": -73.57},
    {"city": "Perth", "country": "Australia", "score": 79.5, "lat": -31.95, "lon": 115.86},
    {"city": "Auckland", "country": "New Zealand", "score": 79.3, "lat": -36.85, "lon": 174.76},
    {"city": "Milan", "country": "Italy", "score": 79.0, "lat": 45.46, "lon": 9.19},
    {"city": "Berlin", "country": "Germany", "score": 78.7, "lat": 52.52, "lon": 13.41},
    {"city": "Rome", "country": "Italy", "score": 78.4, "lat": 41.90, "lon": 12.50},
    {"city": "Chicago", "country": "USA", "score": 78.0, "lat": 41.88, "lon": -87.63},
    {"city": "San Francisco", "country": "USA", "score": 77.7, "lat": 37.77, "lon": -122.42},
    {"city": "Boston", "country": "USA", "score": 77.3, "lat": 42.36, "lon": -71.06},
    {"city": "Doha", "country": "Qatar", "score": 77.0, "lat": 25.29, "lon": 51.53},
    {"city": "Kuala Lumpur", "country": "Malaysia", "score": 76.7, "lat": 3.14, "lon": 101.69},
    {"city": "Santiago", "country": "Chile", "score": 76.4, "lat": -33.45, "lon": -70.67},
    {"city": "Ljubljana", "country": "Slovenia", "score": 76.0, "lat": 46.06, "lon": 14.51},
    {"city": "Tallinn", "country": "Estonia", "score": 75.7, "lat": 59.44, "lon": 24.75},
    {"city": "Warsaw", "country": "Poland", "score": 75.4, "lat": 52.23, "lon": 21.01},
    {"city": "Budapest", "country": "Hungary", "score": 75.1, "lat": 47.50, "lon": 19.04},
    {"city": "Bratislava", "country": "Slovakia", "score": 74.8, "lat": 48.15, "lon": 17.11},
    {"city": "Panama City", "country": "Panama", "score": 74.3, "lat": 8.98, "lon": -79.52},
    {"city": "Montevideo", "country": "Uruguay", "score": 74.0, "lat": -34.88, "lon": -56.17},
    {"city": "Buenos Aires", "country": "Argentina", "score": 73.5, "lat": -34.60, "lon": -58.38},
]


def _city_score_color(score):
    if score >= 88:
        return "#10b981"
    elif score >= 82:
        return "#34d399"
    elif score >= 78:
        return "#06b6d4"
    elif score >= 75:
        return "#facc15"
    return "#f97316"


# ──────────────────────────────────────────────────────────────────────
# 3. TRAVEL ADVISORY DATA (risk levels 1-4)
# ──────────────────────────────────────────────────────────────────────
TRAVEL_ADVISORY_LEVELS = {1: "Exercise Normal Precautions", 2: "Exercise Increased Caution",
                          3: "Reconsider Travel", 4: "Do Not Travel"}
TRAVEL_ADVISORY_COLORS = {1: "#10b981", 2: "#facc15", 3: "#f97316", 4: "#ef4444"}

TRAVEL_ADVISORY = {
    "Iceland": 1, "Ireland": 1, "Austria": 1, "New Zealand": 1, "Switzerland": 1,
    "Portugal": 1, "Denmark": 1, "Slovenia": 1, "Finland": 1, "Norway": 1,
    "Canada": 1, "Japan": 1, "Australia": 1, "Czech Republic": 1, "Singapore": 1,
    "Croatia": 1, "Germany": 1, "Netherlands": 1, "Sweden": 1, "Belgium": 1,
    "Estonia": 1, "Latvia": 1, "Lithuania": 1, "Slovakia": 1, "Poland": 1,
    "Italy": 1, "Spain": 1, "South Korea": 1, "Chile": 1, "Uruguay": 1,
    "Costa Rica": 1, "Mongolia": 1, "Taiwan": 1, "Qatar": 1, "Oman": 1,
    "United Arab Emirates": 1, "Botswana": 1, "Mauritius": 1,
    "United Kingdom": 2, "France": 2, "Greece": 2, "India": 2, "Indonesia": 2,
    "Brazil": 2, "South Africa": 2, "Mexico": 2, "Turkey": 2, "Jamaica": 2,
    "Dominican Republic": 2, "Peru": 2, "Ecuador": 2, "Bolivia": 2,
    "Morocco": 2, "Tunisia": 2, "Egypt": 2, "Algeria": 2, "Jordan": 2,
    "China": 2, "Vietnam": 2, "Thailand": 2, "Philippines": 2,
    "Bangladesh": 2, "Argentina": 2, "Israel": 2, "Saudi Arabia": 2,
    "Ghana": 2, "Senegal": 2, "Rwanda": 2, "Tanzania": 2, "Kenya": 2,
    "Sri Lanka": 2, "Cambodia": 2, "Malaysia": 2, "Panama": 2, "Cuba": 2,
    "Honduras": 3, "El Salvador": 3, "Guatemala": 3, "Colombia": 3,
    "Venezuela": 3, "Nigeria": 3, "Pakistan": 3, "Lebanon": 3,
    "Myanmar": 3, "Haiti": 3, "Ethiopia": 3, "Cameroon": 3,
    "Mozambique": 3, "Chad": 3, "Niger": 3, "Uganda": 3, "Burundi": 3,
    "Mali": 3, "Eritrea": 3, "Central African Republic": 3,
    "Democratic Republic of the Congo": 3,
    "Afghanistan": 4, "Syria": 4, "Yemen": 4, "Somalia": 4, "South Sudan": 4,
    "Libya": 4, "Iraq": 4, "North Korea": 4, "Sudan": 4, "Ukraine": 4,
    "Russia": 4,
}


# ──────────────────────────────────────────────────────────────────────
# 4. PIRACY HOTSPOTS
# ──────────────────────────────────────────────────────────────────────
PIRACY_HOTSPOTS = [
    {"zone": "Gulf of Aden / Horn of Africa", "lat": 12.0, "lon": 47.0, "radius_nm": 300,
     "incidents_year": 35, "risk": "High",
     "desc": "Somali piracy corridor; warship patrols reduced attacks but risk persists."},
    {"zone": "Gulf of Guinea", "lat": 3.0, "lon": 4.0, "radius_nm": 400,
     "incidents_year": 65, "risk": "Very High",
     "desc": "World's most dangerous piracy zone; kidnapping-for-ransom, oil theft."},
    {"zone": "Strait of Malacca", "lat": 2.5, "lon": 101.5, "radius_nm": 200,
     "incidents_year": 42, "risk": "High",
     "desc": "Narrow strait between Malaysia and Indonesia; robbery of cargo ships."},
    {"zone": "South China Sea", "lat": 10.0, "lon": 113.0, "radius_nm": 350,
     "incidents_year": 22, "risk": "Moderate",
     "desc": "Piracy and armed robbery; territorial disputes complicate enforcement."},
    {"zone": "Caribbean Sea", "lat": 14.0, "lon": -70.0, "radius_nm": 250,
     "incidents_year": 18, "risk": "Moderate",
     "desc": "Yacht and small vessel theft; Venezuela and Trinidad waters affected."},
    {"zone": "Bangladesh / Bay of Bengal", "lat": 21.5, "lon": 89.5, "radius_nm": 150,
     "incidents_year": 20, "risk": "Moderate",
     "desc": "Attacks on anchored ships at Chittagong anchorage area."},
    {"zone": "Indian Ocean - Western", "lat": -2.0, "lon": 55.0, "radius_nm": 200,
     "incidents_year": 8, "risk": "Low-Moderate",
     "desc": "Occasional Somali piracy attempts extending into western Indian Ocean."},
    {"zone": "Singapore Strait", "lat": 1.2, "lon": 104.0, "radius_nm": 80,
     "incidents_year": 38, "risk": "High",
     "desc": "One of the busiest shipping lanes; petty theft and robbery."},
    {"zone": "Peru / Ecuador Coast", "lat": -3.5, "lon": -81.0, "radius_nm": 120,
     "incidents_year": 12, "risk": "Low-Moderate",
     "desc": "Robbery against anchored vessels, especially near Callao and Guayaquil."},
    {"zone": "Philippine Waters", "lat": 7.0, "lon": 124.0, "radius_nm": 200,
     "incidents_year": 15, "risk": "Moderate",
     "desc": "Kidnapping by Abu Sayyaf in Sulu Sea; general robbery near ports."},
    {"zone": "Red Sea / Bab el-Mandeb", "lat": 13.0, "lon": 43.0, "radius_nm": 120,
     "incidents_year": 28, "risk": "High",
     "desc": "Houthi attacks on commercial shipping; critical chokepoint."},
    {"zone": "West Africa - Ivory Coast", "lat": 5.0, "lon": -4.0, "radius_nm": 100,
     "incidents_year": 10, "risk": "Moderate",
     "desc": "Attacks off Abidjan; spillover from Gulf of Guinea piracy zone."},
]

PIRACY_RISK_COLORS = {"Very High": "#991b1b", "High": "#ef4444",
                       "Moderate": "#f97316", "Low-Moderate": "#facc15", "Low": "#10b981"}


# ──────────────────────────────────────────────────────────────────────
# 5. CYBERCRIME ORIGINS (index 0-100, higher = more cybercrime)
# ──────────────────────────────────────────────────────────────────────
CYBERCRIME_DATA = [
    {"country": "Russia", "index": 94.2, "specialties": "Ransomware, botnets, espionage"},
    {"country": "Ukraine", "index": 78.5, "specialties": "Carding, phishing, malware"},
    {"country": "China", "index": 77.1, "specialties": "IP theft, APT groups, espionage"},
    {"country": "United States", "index": 74.8, "specialties": "Fraud, hacking, data breaches"},
    {"country": "Nigeria", "index": 72.3, "specialties": "BEC fraud, romance scams, 419 scams"},
    {"country": "Romania", "index": 68.9, "specialties": "ATM skimming, auction fraud"},
    {"country": "North Korea", "index": 67.5, "specialties": "Crypto theft, state-sponsored hacking"},
    {"country": "Brazil", "index": 65.0, "specialties": "Banking trojans, card cloning"},
    {"country": "India", "index": 63.7, "specialties": "Tech support scams, call center fraud"},
    {"country": "Iran", "index": 62.1, "specialties": "Cyber espionage, DDoS, destructive malware"},
    {"country": "Vietnam", "index": 55.4, "specialties": "Click fraud, cryptocurrency mining"},
    {"country": "Turkey", "index": 53.8, "specialties": "DDoS, hacktivism, fraud"},
    {"country": "Indonesia", "index": 51.2, "specialties": "Phishing, online scams"},
    {"country": "Pakistan", "index": 49.0, "specialties": "Web defacement, hacktivism"},
    {"country": "Israel", "index": 47.5, "specialties": "Spyware (Pegasus), offensive cyber"},
    {"country": "Philippines", "index": 45.0, "specialties": "Sextortion, love scams"},
    {"country": "Ghana", "index": 43.8, "specialties": "Sakawa scams, romance fraud"},
    {"country": "South Africa", "index": 42.0, "specialties": "Banking fraud, ransomware"},
    {"country": "Malaysia", "index": 40.5, "specialties": "Online fraud, malware hosting"},
    {"country": "Poland", "index": 38.2, "specialties": "Malware development, carding"},
    {"country": "Germany", "index": 36.1, "specialties": "Dark web markets, hacking"},
    {"country": "United Kingdom", "index": 35.0, "specialties": "Fraud, hacking, dark web"},
    {"country": "France", "index": 33.5, "specialties": "Fraud, hacktivism"},
    {"country": "Thailand", "index": 32.0, "specialties": "Online scams, pig butchering"},
    {"country": "Cambodia", "index": 31.5, "specialties": "Forced scam compounds"},
    {"country": "Myanmar", "index": 30.0, "specialties": "Forced scam compounds, crypto fraud"},
    {"country": "Colombia", "index": 28.5, "specialties": "SIM swapping, phishing"},
    {"country": "Mexico", "index": 27.0, "specialties": "Ransomware, financial fraud"},
    {"country": "Argentina", "index": 25.5, "specialties": "Carding, phishing"},
    {"country": "Japan", "index": 22.0, "specialties": "Cryptocurrency exchange hacks"},
]


def _cyber_color(index):
    if index >= 70:
        return "#ef4444"
    elif index >= 50:
        return "#f97316"
    elif index >= 35:
        return "#facc15"
    return "#10b981"


# ──────────────────────────────────────────────────────────────────────
# 8. NOTABLE PRISONS (~30 locations)
# ──────────────────────────────────────────────────────────────────────
PRISONS = [
    {"name": "Alcatraz Federal Penitentiary", "city": "San Francisco", "country": "USA",
     "lat": 37.8267, "lon": -122.4230, "status": "Closed (1963)", "type": "Maximum Security",
     "note": "Iconic island prison; held Al Capone, Robert Stroud."},
    {"name": "Robben Island", "city": "Cape Town", "country": "South Africa",
     "lat": -33.8076, "lon": 18.3713, "status": "Closed (1996)", "type": "Political",
     "note": "Held Nelson Mandela for 18 years; UNESCO World Heritage Site."},
    {"name": "ADX Florence", "city": "Florence, CO", "country": "USA",
     "lat": 38.3572, "lon": -105.0967, "status": "Active", "type": "Supermax",
     "note": "Most secure US federal prison; Unabomber, El Chapo."},
    {"name": "La Sante Prison", "city": "Paris", "country": "France",
     "lat": 48.8336, "lon": 2.3372, "status": "Active", "type": "Maison d'arret",
     "note": "Historic Paris prison; held Carlos the Jackal."},
    {"name": "Guantanamo Bay", "city": "Guantanamo", "country": "Cuba (US)",
     "lat": 19.9023, "lon": -75.0962, "status": "Active", "type": "Military Detention",
     "note": "US military detention; controversial War on Terror facility."},
    {"name": "Rikers Island", "city": "New York", "country": "USA",
     "lat": 40.7930, "lon": -73.8860, "status": "Active (closing)", "type": "Jail Complex",
     "note": "NYC's main jail complex; 10 facilities on one island."},
    {"name": "Tower of London", "city": "London", "country": "UK",
     "lat": 51.5081, "lon": -0.0759, "status": "Closed (historic)", "type": "Royal Prison",
     "note": "Medieval fortress-prison; Anne Boleyn, Sir Walter Raleigh."},
    {"name": "Bastille (site)", "city": "Paris", "country": "France",
     "lat": 48.8533, "lon": 2.3692, "status": "Demolished (1789)", "type": "State Prison",
     "note": "Symbol of French Revolution; stormed on July 14, 1789."},
    {"name": "Devil's Island", "city": "French Guiana", "country": "France",
     "lat": 5.2894, "lon": -52.5850, "status": "Closed (1953)", "type": "Penal Colony",
     "note": "Notorious penal colony; held Alfred Dreyfus, Henri Charriere (Papillon)."},
    {"name": "Sing Sing", "city": "Ossining, NY", "country": "USA",
     "lat": 41.1620, "lon": -73.8707, "status": "Active", "type": "Maximum Security",
     "note": "Historic NY state prison; built by inmates in 1826."},
    {"name": "San Quentin", "city": "San Quentin, CA", "country": "USA",
     "lat": 37.9383, "lon": -122.4858, "status": "Active", "type": "State Prison",
     "note": "California's oldest prison (1852); formerly housed death row."},
    {"name": "Leavenworth", "city": "Leavenworth, KS", "country": "USA",
     "lat": 39.3217, "lon": -94.9225, "status": "Active", "type": "Federal",
     "note": "Major US federal prison since 1903; 'The Big House'."},
    {"name": "Evin Prison", "city": "Tehran", "country": "Iran",
     "lat": 35.8050, "lon": 51.3908, "status": "Active", "type": "Political",
     "note": "Infamous for holding political prisoners; human rights concerns."},
    {"name": "Black Dolphin Prison", "city": "Sol-Iletsk", "country": "Russia",
     "lat": 51.1590, "lon": 54.9967, "status": "Active", "type": "Maximum Security",
     "note": "Russia's strictest; holds serial killers, terrorists, cannibals."},
    {"name": "Tadmor Prison", "city": "Palmyra", "country": "Syria",
     "lat": 34.5600, "lon": 38.2800, "status": "Destroyed (2015)", "type": "Military",
     "note": "One of the most brutal prisons; site of 1980 massacre."},
    {"name": "Carandiru", "city": "Sao Paulo", "country": "Brazil",
     "lat": -23.5166, "lon": -46.6275, "status": "Demolished (2002)", "type": "State",
     "note": "Site of 1992 massacre; once held 8,000 inmates."},
    {"name": "Bang Kwang", "city": "Bangkok", "country": "Thailand",
     "lat": 13.8567, "lon": 100.4993, "status": "Active", "type": "Maximum Security",
     "note": "Known as 'Bangkok Hilton'; death row facility."},
    {"name": "Pollsmoor Prison", "city": "Cape Town", "country": "South Africa",
     "lat": -34.0808, "lon": 18.4578, "status": "Active", "type": "Medium-Maximum",
     "note": "Overcrowded and gang-ridden; held Mandela briefly."},
    {"name": "Camp 22 (Hoeryong)", "city": "Hoeryong", "country": "North Korea",
     "lat": 42.0500, "lon": 129.8500, "status": "Active (unconfirmed)", "type": "Labor Camp",
     "note": "Political prison camp; estimated 50,000 prisoners."},
    {"name": "Diyarbakir Prison", "city": "Diyarbakir", "country": "Turkey",
     "lat": 37.9100, "lon": 40.2200, "status": "Active", "type": "High Security",
     "note": "Notorious for torture of Kurdish political prisoners in 1980s."},
    {"name": "La Modelo", "city": "Bogota", "country": "Colombia",
     "lat": 4.6250, "lon": -74.0917, "status": "Active", "type": "Medium Security",
     "note": "Extremely overcrowded; frequent riots and violence."},
    {"name": "Pelican Bay", "city": "Crescent City, CA", "country": "USA",
     "lat": 41.7500, "lon": -124.1533, "status": "Active", "type": "Supermax",
     "note": "SHU (solitary confinement) housing; hunger strikes in 2013."},
    {"name": "Spandau Prison (site)", "city": "Berlin", "country": "Germany",
     "lat": 52.5350, "lon": 13.2000, "status": "Demolished (1987)", "type": "War Crimes",
     "note": "Held Nazi war criminals; Rudolf Hess was last prisoner."},
    {"name": "Port Arthur Penal Settlement", "city": "Tasmania", "country": "Australia",
     "lat": -43.1500, "lon": 147.8500, "status": "Closed (1877)", "type": "Penal Colony",
     "note": "Harsh British convict settlement; now heritage site."},
    {"name": "Changi Prison", "city": "Singapore", "country": "Singapore",
     "lat": 1.3570, "lon": 103.9760, "status": "Active", "type": "Maximum Security",
     "note": "WWII POW camp; modern facility carries death penalty."},
    {"name": "Landsberg Prison", "city": "Landsberg", "country": "Germany",
     "lat": 48.0500, "lon": 10.8667, "status": "Active", "type": "State",
     "note": "Where Hitler wrote Mein Kampf during 1924 imprisonment."},
    {"name": "Chateau d'If", "city": "Marseille", "country": "France",
     "lat": 43.2800, "lon": 5.3253, "status": "Closed (museum)", "type": "Island Prison",
     "note": "Made famous by 'The Count of Monte Cristo'; built 1524."},
    {"name": "Eastern State Penitentiary", "city": "Philadelphia", "country": "USA",
     "lat": 39.9683, "lon": -75.1727, "status": "Closed (1970)", "type": "Historic",
     "note": "First true penitentiary (1829); held Al Capone; now museum."},
    {"name": "Attica Correctional Facility", "city": "Attica, NY", "country": "USA",
     "lat": 42.8500, "lon": -78.2800, "status": "Active", "type": "Maximum Security",
     "note": "Site of deadly 1971 riot; 43 killed."},
    {"name": "Lubyanka (FSB HQ)", "city": "Moscow", "country": "Russia",
     "lat": 55.7601, "lon": 37.6267, "status": "Active (detention)", "type": "Intelligence HQ",
     "note": "KGB/FSB headquarters; internal prison for political detainees."},
]


# ──────────────────────────────────────────────────────────────────────
# 9. DRUG TRAFFICKING ROUTES
# ──────────────────────────────────────────────────────────────────────
DRUG_ROUTES = [
    {"name": "Andean Cocaine to North America",
     "drug": "Cocaine", "volume": "~900 tonnes/yr",
     "color": "#ef4444",
     "path": [(-2.0, -77.0), (7.0, -75.0), (12.0, -80.0), (20.0, -86.0), (25.0, -95.0), (30.0, -97.0)]},
    {"name": "Andean Cocaine to Europe (Atlantic)",
     "drug": "Cocaine", "volume": "~300 tonnes/yr",
     "color": "#dc2626",
     "path": [(-2.0, -77.0), (5.0, -50.0), (15.0, -30.0), (30.0, -15.0), (40.0, -5.0), (45.0, 0.0)]},
    {"name": "Cocaine via West Africa to Europe",
     "drug": "Cocaine", "volume": "~50 tonnes/yr",
     "color": "#f97316",
     "path": [(5.0, -50.0), (10.0, -20.0), (15.0, -15.0), (25.0, -10.0), (35.0, -5.0), (42.0, 2.0)]},
    {"name": "Afghan Opium Northern Route",
     "drug": "Heroin/Opium", "volume": "~150 tonnes/yr",
     "color": "#a855f7",
     "path": [(34.0, 67.0), (37.0, 65.0), (40.0, 60.0), (45.0, 55.0), (50.0, 45.0), (55.0, 37.0)]},
    {"name": "Afghan Opium Balkan Route",
     "drug": "Heroin/Opium", "volume": "~100 tonnes/yr",
     "color": "#8b5cf6",
     "path": [(34.0, 67.0), (35.0, 55.0), (38.0, 45.0), (40.0, 35.0), (42.0, 28.0), (45.0, 20.0), (48.0, 16.0)]},
    {"name": "Golden Triangle to Australia/China",
     "drug": "Methamphetamine/Heroin", "volume": "~200 tonnes/yr",
     "color": "#ec4899",
     "path": [(20.0, 100.0), (15.0, 105.0), (8.0, 110.0), (0.0, 115.0), (-10.0, 120.0), (-20.0, 130.0)]},
    {"name": "Mexican Meth/Fentanyl to USA",
     "drug": "Meth/Fentanyl", "volume": "~Massive",
     "color": "#f43f5e",
     "path": [(19.0, -99.0), (22.0, -100.0), (26.0, -100.0), (30.0, -98.0), (33.0, -97.0), (35.0, -95.0)]},
    {"name": "Cannabis from Morocco to Europe",
     "drug": "Cannabis/Hashish", "volume": "~700 tonnes/yr",
     "color": "#22c55e",
     "path": [(34.0, -5.0), (36.0, -5.0), (37.0, -3.0), (39.0, -1.0), (42.0, 2.0), (46.0, 3.0)]},
    {"name": "Captagon from Syria/Lebanon",
     "drug": "Captagon", "volume": "Billions of pills",
     "color": "#eab308",
     "path": [(34.0, 37.0), (32.0, 38.0), (28.0, 40.0), (25.0, 45.0), (22.0, 48.0)]},
    {"name": "Precursor Chemicals from China",
     "drug": "Fentanyl precursors", "volume": "Unknown",
     "color": "#06b6d4",
     "path": [(30.0, 120.0), (25.0, 115.0), (15.0, 110.0), (5.0, 100.0),
              (15.0, -90.0), (19.0, -99.0)]},
]


# ──────────────────────────────────────────────────────────────────────
# 10. INTERPOL RED NOTICE COUNTRIES (activity level, approximate)
# ──────────────────────────────────────────────────────────────────────
INTERPOL_DATA = [
    {"country": "Turkey", "red_notices": 890, "focus": "Terrorism, organized crime"},
    {"country": "Russia", "red_notices": 820, "focus": "Financial crime, fraud"},
    {"country": "United States", "red_notices": 750, "focus": "Drug trafficking, fraud"},
    {"country": "India", "red_notices": 680, "focus": "Financial crime, fugitives"},
    {"country": "China", "red_notices": 660, "focus": "Corruption, economic crime"},
    {"country": "Ukraine", "red_notices": 550, "focus": "Financial crime, fraud"},
    {"country": "Germany", "red_notices": 480, "focus": "Organized crime, fraud"},
    {"country": "United Kingdom", "red_notices": 420, "focus": "Financial crime, drug trafficking"},
    {"country": "Iran", "red_notices": 400, "focus": "Sanctions evasion, terrorism"},
    {"country": "Iraq", "red_notices": 380, "focus": "Terrorism, war crimes"},
    {"country": "Morocco", "red_notices": 360, "focus": "Drug trafficking, terrorism"},
    {"country": "Colombia", "red_notices": 340, "focus": "Drug trafficking, FARC"},
    {"country": "Egypt", "red_notices": 320, "focus": "Terrorism, financial crime"},
    {"country": "Pakistan", "red_notices": 310, "focus": "Terrorism, financial crime"},
    {"country": "Brazil", "red_notices": 300, "focus": "Drug trafficking, corruption"},
    {"country": "Mexico", "red_notices": 280, "focus": "Drug cartels, organized crime"},
    {"country": "Nigeria", "red_notices": 260, "focus": "Fraud, cybercrime"},
    {"country": "France", "red_notices": 250, "focus": "Terrorism, organized crime"},
    {"country": "Italy", "red_notices": 240, "focus": "Mafia, organized crime"},
    {"country": "South Africa", "red_notices": 220, "focus": "Organized crime, corruption"},
    {"country": "Peru", "red_notices": 200, "focus": "Drug trafficking"},
    {"country": "Argentina", "red_notices": 190, "focus": "Financial crime, fugitives"},
    {"country": "Saudi Arabia", "red_notices": 180, "focus": "Terrorism financing"},
    {"country": "Spain", "red_notices": 170, "focus": "Drug trafficking, terrorism"},
    {"country": "Philippines", "red_notices": 160, "focus": "Drug trafficking, cybercrime"},
    {"country": "Thailand", "red_notices": 150, "focus": "Human trafficking, fraud"},
    {"country": "Venezuela", "red_notices": 140, "focus": "Drug trafficking, corruption"},
    {"country": "Syria", "red_notices": 130, "focus": "War crimes, terrorism"},
    {"country": "Afghanistan", "red_notices": 120, "focus": "Terrorism, narcotics"},
    {"country": "Indonesia", "red_notices": 110, "focus": "Terrorism, fraud"},
]


def _interpol_color(notices):
    if notices >= 700:
        return "#ef4444"
    elif notices >= 400:
        return "#f97316"
    elif notices >= 250:
        return "#facc15"
    return "#10b981"


# ──────────────────────────────────────────────────────────────────────
# HELPER: Matplotlib dark-themed bar chart
# ──────────────────────────────────────────────────────────────────────
def _dark_bar_chart(labels, values, colors, title, xlabel, ylabel, figsize=(10, 5)):
    """Create a matplotlib bar chart with dark theme."""
    fig, ax = plt.subplots(figsize=figsize, facecolor=_BG)
    ax.set_facecolor(_SURFACE)
    bars = ax.barh(labels, values, color=colors, edgecolor="none", height=0.7)
    ax.set_xlabel(xlabel, color=_TEXT, fontsize=10)
    ax.set_ylabel(ylabel, color=_TEXT, fontsize=10)
    ax.set_title(title, color=_ACCENT, fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(axis="x", colors=_TEXT, labelsize=8)
    ax.tick_params(axis="y", colors=_TEXT, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(_MUTED)
    ax.grid(axis="x", color=_MUTED, alpha=0.3, linestyle="--")
    plt.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────
# HELPER: Overpass amenity search
# ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _search_amenity(lat, lon, radius_km, amenity_type):
    """Search for amenity (police / fire_station) via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["amenity"="{amenity_type}"](around:{radius_m},{lat},{lon});
  way["amenity"="{amenity_type}"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        return {"elements": [], "_error": err}
    return result


def _extract_amenity_features(data, amenity_type):
    """Extract features with coordinates from Overpass amenity response."""
    elements = data.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("amenity") != amenity_type:
            continue

        lat, lon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1])
                      for n in nodes if n in node_lookup]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)

        if lat is None or lon is None:
            continue

        name = tags.get("name", tags.get("name:en", "Unnamed"))
        features.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "phone": tags.get("phone", tags.get("contact:phone", "")),
            "addr": tags.get("addr:street", ""),
            "operator": tags.get("operator", ""),
            "osm_id": el.get("id"),
        })
    return features


# ══════════════════════════════════════════════════════════════════════
# INDIVIDUAL MODE RENDERERS
# ══════════════════════════════════════════════════════════════════════

def _render_global_peace_index():
    """Mode 1: Global Peace Index choropleth."""
    st.markdown("#### Global Peace Index (2024)")
    st.caption("Lower GPI score = more peaceful. Data: Institute for Economics & Peace.")

    sort_order = st.radio("Sort order", ["Most Peaceful First", "Least Peaceful First"],
                          horizontal=True, key="gpi_sort")
    ascending = sort_order == "Most Peaceful First"

    rows = [{"Country": k, "GPI Score": v} for k, v in GPI_DATA.items()]
    df = pd.DataFrame(rows).sort_values("GPI Score", ascending=ascending).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Most Peaceful", df.loc[df["GPI Score"].idxmin(), "Country"])
    c3.metric("Least Peaceful", df.loc[df["GPI Score"].idxmax(), "Country"])
    c4.metric("Global Avg", f"{df['GPI Score'].mean():.3f}")

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        country = row["Country"]
        score = row["GPI Score"]
        coords = COUNTRY_COORDS.get(country)
        if not coords:
            continue
        color = _gpi_color(score)
        popup_html = (f"<b>{html.escape(country)}</b><br>"
                      f"GPI Score: {score:.3f}<br>"
                      f"Rank: {_}")
        folium.CircleMarker(
            location=coords, radius=7, color=color,
            fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{country}: {score:.3f}",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart - top & bottom 15
    top15 = df.head(15) if ascending else df.tail(15)
    top_labels = top15["Country"].tolist()[::-1]
    top_vals = top15["GPI Score"].tolist()[::-1]
    top_colors = [_gpi_color(v) for v in top_vals]
    fig = _dark_bar_chart(top_labels, top_vals, top_colors,
                          "Top 15 Most Peaceful Countries", "GPI Score", "")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Dataframe & download
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "global_peace_index.csv", "text/csv",
                       key="gpi_csv")


def _render_safest_cities():
    """Mode 2: Safest cities in the world."""
    st.markdown("#### Safest Cities in the World")
    st.caption("Safety scores based on digital, health, infrastructure, and personal security.")

    min_score = st.slider("Minimum safety score", 70, 92, 74, key="safe_min")
    filtered = [c for c in SAFEST_CITIES if c["score"] >= min_score]

    df = pd.DataFrame(filtered)
    df.index += 1
    df.index.name = "Rank"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities Shown", len(df))
    c2.metric("Safest", df.iloc[0]["city"] if len(df) > 0 else "N/A")
    c3.metric("Highest Score", f"{df['score'].max():.1f}" if len(df) > 0 else "N/A")
    c4.metric("Avg Score", f"{df['score'].mean():.1f}" if len(df) > 0 else "N/A")

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        color = _city_score_color(row["score"])
        popup_html = (f"<b>{html.escape(row['city'])}</b><br>"
                      f"Country: {html.escape(row['country'])}<br>"
                      f"Safety Score: {row['score']}")
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=8, color=color,
            fill=True, fill_color=color, fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['city']}: {row['score']}",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart
    chart_df = df.head(20)
    labels = chart_df["city"].tolist()[::-1]
    vals = chart_df["score"].tolist()[::-1]
    colors = [_city_score_color(v) for v in vals]
    fig = _dark_bar_chart(labels, vals, colors, "Top 20 Safest Cities",
                          "Safety Score", "")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.dataframe(df[["city", "country", "score", "lat", "lon"]], width="stretch")
    csv = df.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "safest_cities.csv", "text/csv",
                       key="safecity_csv")


def _render_travel_advisory():
    """Mode 3: Travel Advisory Zones."""
    st.markdown("#### Travel Advisory Zones")
    st.caption("Risk levels based on aggregated government travel advisories.")

    level_filter = st.multiselect("Filter by risk level",
                                  [1, 2, 3, 4],
                                  default=[1, 2, 3, 4],
                                  format_func=lambda x: f"Level {x}: {TRAVEL_ADVISORY_LEVELS[x]}",
                                  key="ta_filter")

    rows = [{"Country": k, "Level": v, "Advisory": TRAVEL_ADVISORY_LEVELS[v]}
            for k, v in TRAVEL_ADVISORY.items() if v in level_filter]
    df = pd.DataFrame(rows).sort_values("Level").reset_index(drop=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    level_counts = df["Level"].value_counts()
    c2.metric("Level 1 (Safe)", level_counts.get(1, 0))
    c3.metric("Level 3 (Caution)", level_counts.get(3, 0))
    c4.metric("Level 4 (Do Not Travel)", level_counts.get(4, 0))

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        country = row["Country"]
        level = row["Level"]
        coords = COUNTRY_COORDS.get(country)
        if not coords:
            continue
        color = TRAVEL_ADVISORY_COLORS[level]
        popup_html = (f"<b>{html.escape(country)}</b><br>"
                      f"Level {level}: {html.escape(row['Advisory'])}")
        folium.CircleMarker(
            location=coords, radius=7, color=color,
            fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{country}: Level {level}",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Distribution pie chart
    fig, ax = plt.subplots(figsize=(6, 4), facecolor=_BG)
    ax.set_facecolor(_SURFACE)
    pie_data = [level_counts.get(i, 0) for i in [1, 2, 3, 4]]
    pie_labels = [f"Level {i}" for i in [1, 2, 3, 4]]
    pie_colors = [TRAVEL_ADVISORY_COLORS[i] for i in [1, 2, 3, 4]]
    wedges, texts, autotexts = ax.pie(pie_data, labels=pie_labels, colors=pie_colors,
                                       autopct="%1.0f%%", startangle=90,
                                       textprops={"color": _TEXT, "fontsize": 9})
    for t in autotexts:
        t.set_color(_TEXT)
    ax.set_title("Advisory Level Distribution", color=_ACCENT, fontsize=12, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "travel_advisories.csv", "text/csv",
                       key="ta_csv")


def _render_piracy_hotspots():
    """Mode 4: Maritime piracy hotspots."""
    st.markdown("#### Modern Maritime Piracy Hotspots")
    st.caption("Active piracy zones based on IMB Piracy Reporting Centre data.")

    df = pd.DataFrame(PIRACY_HOTSPOTS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Zones Tracked", len(df))
    c2.metric("Total Incidents/yr", int(df["incidents_year"].sum()))
    c3.metric("Most Dangerous", df.loc[df["incidents_year"].idxmax(), "zone"][:25])
    c4.metric("Avg Incidents", f"{df['incidents_year'].mean():.0f}")

    m = folium.Map(location=[10, 50], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        color = PIRACY_RISK_COLORS.get(row["risk"], "#f97316")
        popup_html = (f"<b>{html.escape(row['zone'])}</b><br>"
                      f"Risk: {html.escape(row['risk'])}<br>"
                      f"Incidents/yr: {row['incidents_year']}<br>"
                      f"{html.escape(row['desc'])}")
        folium.Circle(
            location=[row["lat"], row["lon"]],
            radius=row["radius_nm"] * 1852,
            color=color, fill=True, fill_color=color, fill_opacity=0.25,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['zone']} ({row['risk']})",
        ).add_to(m)
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.DivIcon(html=f'<div style="font-size:18px;">&#x2620;</div>'),
            tooltip=row["zone"],
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart
    labels = df["zone"].apply(lambda x: x[:30]).tolist()[::-1]
    vals = df["incidents_year"].tolist()[::-1]
    colors = [PIRACY_RISK_COLORS.get(r, "#f97316") for r in df["risk"].tolist()[::-1]]
    fig = _dark_bar_chart(labels, vals, colors, "Piracy Incidents by Zone",
                          "Incidents / Year", "", figsize=(10, 6))
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.dataframe(df[["zone", "risk", "incidents_year", "desc"]], width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "piracy_hotspots.csv", "text/csv",
                       key="piracy_csv")


def _render_cybercrime():
    """Mode 5: Cybercrime origins by country."""
    st.markdown("#### Cybercrime Origins by Country")
    st.caption("World Cybercrime Index based on academic research and law enforcement data.")

    df = pd.DataFrame(CYBERCRIME_DATA).sort_values("index", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries Indexed", len(df))
    c2.metric("Highest Index", df.iloc[0]["country"])
    c3.metric("Avg Index", f"{df['index'].mean():.1f}")
    c4.metric("Max Score", f"{df['index'].max():.1f}")

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        coords = COUNTRY_COORDS.get(row["country"])
        if not coords:
            continue
        color = _cyber_color(row["index"])
        popup_html = (f"<b>{html.escape(row['country'])}</b><br>"
                      f"Cybercrime Index: {row['index']}<br>"
                      f"Specialties: {html.escape(row['specialties'])}")
        folium.CircleMarker(
            location=coords, radius=max(5, row["index"] / 8),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['country']}: {row['index']}",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart top 15
    chart_df = df.head(15)
    labels = chart_df["country"].tolist()[::-1]
    vals = chart_df["index"].tolist()[::-1]
    colors = [_cyber_color(v) for v in vals]
    fig = _dark_bar_chart(labels, vals, colors, "Top 15 Cybercrime Countries",
                          "Cybercrime Index", "")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.dataframe(df[["country", "index", "specialties"]], width="stretch")
    csv = df.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "cybercrime_index.csv", "text/csv",
                       key="cyber_csv")


def _render_police_stations():
    """Mode 6: Police stations from Overpass API."""
    st.markdown("#### Police Stations & Emergency Services")
    st.caption("Live data from OpenStreetMap via Overpass API.")

    PRESETS = {
        "Custom": None,
        "New York City": {"lat": 40.7128, "lon": -74.0060},
        "London": {"lat": 51.5074, "lon": -0.1278},
        "Tokyo": {"lat": 35.6762, "lon": 139.6503},
        "Paris": {"lat": 48.8566, "lon": 2.3522},
        "Rome": {"lat": 41.9028, "lon": 12.4964},
        "Berlin": {"lat": 52.5200, "lon": 13.4050},
        "Sydney": {"lat": -33.8688, "lon": 151.2093},
        "Singapore": {"lat": 1.3521, "lon": 103.8198},
    }

    preset = st.selectbox("Quick location", list(PRESETS.keys()), key="police_preset")

    col1, col2, col3 = st.columns(3)
    default_lat = PRESETS[preset]["lat"] if preset != "Custom" else 40.7128
    default_lon = PRESETS[preset]["lon"] if preset != "Custom" else -74.0060
    with col1:
        p_lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                                min_value=-90.0, max_value=90.0, key="police_lat")
    with col2:
        p_lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                                min_value=-180.0, max_value=180.0, key="police_lon")
    with col3:
        p_radius = st.slider("Radius (km)", 1, 30, 5, key="police_radius")

    if st.button("Search Police Stations", type="primary", key="police_btn"):
        with st.spinner("Querying Overpass API..."):
            data = _search_amenity(p_lat, p_lon, p_radius, "police")
            if "_error" in data:
                st.error(f"Overpass API error: {data['_error']}")
                return
            features = _extract_amenity_features(data, "police")

        st.metric("Police Stations Found", len(features))

        if features:
            m = folium.Map(location=[p_lat, p_lon], zoom_start=13,
                           tiles="CartoDB dark_matter")
            for f in features:
                popup_html = (f"<b>{html.escape(f['name'])}</b><br>"
                              f"Phone: {html.escape(f['phone'])}<br>"
                              f"Address: {html.escape(f['addr'])}<br>"
                              f"Operator: {html.escape(f['operator'])}")
                folium.Marker(
                    location=[f["lat"], f["lon"]],
                    icon=folium.Icon(color="blue", icon="shield",
                                     prefix="fa"),
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f["name"],
                ).add_to(m)
            # Search radius circle
            folium.Circle(location=[p_lat, p_lon], radius=p_radius * 1000,
                          color=_ACCENT, fill=False, dash_array="5").add_to(m)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(features)
            st.dataframe(df[["name", "lat", "lon", "phone", "addr", "operator"]],
                         width="stretch")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "police_stations.csv",
                               "text/csv", key="police_csv")
        else:
            st.info("No police stations found in this area. Try a larger radius.")


def _render_fire_stations():
    """Mode 7: Fire stations from Overpass API."""
    st.markdown("#### Fire Stations")
    st.caption("Live data from OpenStreetMap via Overpass API.")

    PRESETS = {
        "Custom": None,
        "New York City": {"lat": 40.7128, "lon": -74.0060},
        "London": {"lat": 51.5074, "lon": -0.1278},
        "Tokyo": {"lat": 35.6762, "lon": 139.6503},
        "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
        "Chicago": {"lat": 41.8781, "lon": -87.6298},
        "Berlin": {"lat": 52.5200, "lon": 13.4050},
        "Mumbai": {"lat": 19.0760, "lon": 72.8777},
        "Sao Paulo": {"lat": -23.5505, "lon": -46.6333},
    }

    preset = st.selectbox("Quick location", list(PRESETS.keys()), key="fire_preset")

    col1, col2, col3 = st.columns(3)
    default_lat = PRESETS[preset]["lat"] if preset != "Custom" else 40.7128
    default_lon = PRESETS[preset]["lon"] if preset != "Custom" else -74.0060
    with col1:
        f_lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                                min_value=-90.0, max_value=90.0, key="fire_lat")
    with col2:
        f_lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                                min_value=-180.0, max_value=180.0, key="fire_lon")
    with col3:
        f_radius = st.slider("Radius (km)", 1, 30, 5, key="fire_radius")

    if st.button("Search Fire Stations", type="primary", key="fire_btn"):
        with st.spinner("Querying Overpass API..."):
            data = _search_amenity(f_lat, f_lon, f_radius, "fire_station")
            if "_error" in data:
                st.error(f"Overpass API error: {data['_error']}")
                return
            features = _extract_amenity_features(data, "fire_station")

        st.metric("Fire Stations Found", len(features))

        if features:
            m = folium.Map(location=[f_lat, f_lon], zoom_start=13,
                           tiles="CartoDB dark_matter")
            for f in features:
                popup_html = (f"<b>{html.escape(f['name'])}</b><br>"
                              f"Phone: {html.escape(f['phone'])}<br>"
                              f"Address: {html.escape(f['addr'])}<br>"
                              f"Operator: {html.escape(f['operator'])}")
                folium.Marker(
                    location=[f["lat"], f["lon"]],
                    icon=folium.Icon(color="red", icon="fire-extinguisher",
                                     prefix="fa"),
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f["name"],
                ).add_to(m)
            folium.Circle(location=[f_lat, f_lon], radius=f_radius * 1000,
                          color="#ef4444", fill=False, dash_array="5").add_to(m)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(features)
            st.dataframe(df[["name", "lat", "lon", "phone", "addr", "operator"]],
                         width="stretch")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "fire_stations.csv",
                               "text/csv", key="fire_csv")
        else:
            st.info("No fire stations found in this area. Try a larger radius.")


def _render_prisons():
    """Mode 8: Notable prisons worldwide."""
    st.markdown("#### Notable Prisons Worldwide")
    st.caption("Famous and infamous prisons, both active and historic.")

    status_filter = st.multiselect(
        "Filter by status",
        ["Active", "Closed", "Demolished", "Historic"],
        default=["Active", "Closed", "Demolished", "Historic"],
        key="prison_status",
    )

    filtered = []
    for p in PRISONS:
        s = p["status"].lower()
        if any(sf.lower() in s for sf in status_filter):
            filtered.append(p)

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Prisons Shown", len(df))
    active_count = sum(1 for p in filtered if "active" in p["status"].lower())
    c2.metric("Active", active_count)
    c3.metric("Closed / Historic", len(df) - active_count)

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        is_active = "active" in row["status"].lower()
        color = "#ef4444" if is_active else "#8b97b0"
        icon_color = "red" if is_active else "gray"
        popup_html = (f"<b>{html.escape(row['name'])}</b><br>"
                      f"City: {html.escape(row['city'])}<br>"
                      f"Country: {html.escape(row['country'])}<br>"
                      f"Status: {html.escape(row['status'])}<br>"
                      f"Type: {html.escape(row['type'])}<br>"
                      f"<i>{html.escape(row['note'])}</i>")
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.Icon(color=icon_color, icon="lock", prefix="fa"),
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{row['name']} ({row['status']})",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    st.dataframe(df[["name", "city", "country", "status", "type", "note"]],
                 width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "notable_prisons.csv", "text/csv",
                       key="prison_csv")


def _render_drug_routes():
    """Mode 9: Major drug trafficking routes."""
    st.markdown("#### Major Drug Trafficking Routes")
    st.caption("Global drug trade corridors based on UNODC and DEA intelligence.")

    drug_filter = st.multiselect(
        "Filter by drug type",
        list(set(r["drug"] for r in DRUG_ROUTES)),
        default=list(set(r["drug"] for r in DRUG_ROUTES)),
        key="drug_filter",
    )

    filtered = [r for r in DRUG_ROUTES if r["drug"] in drug_filter]
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "path"} for r in filtered])

    c1, c2, c3 = st.columns(3)
    c1.metric("Routes Shown", len(filtered))
    c2.metric("Drug Types", len(set(r["drug"] for r in filtered)))
    c3.metric("Primary Substances", ", ".join(sorted(set(r["drug"] for r in filtered)))[:40])

    m = folium.Map(location=[15, 20], zoom_start=2, tiles="CartoDB dark_matter")
    for route in filtered:
        popup_html = (f"<b>{html.escape(route['name'])}</b><br>"
                      f"Drug: {html.escape(route['drug'])}<br>"
                      f"Volume: {html.escape(route['volume'])}")
        folium.PolyLine(
            locations=route["path"],
            color=route["color"],
            weight=3,
            opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=route["name"],
        ).add_to(m)
        # Origin marker
        origin = route["path"][0]
        folium.CircleMarker(
            location=origin, radius=6, color=route["color"],
            fill=True, fill_color=route["color"], fill_opacity=0.9,
            tooltip=f"Origin: {route['name']}",
        ).add_to(m)
        # Destination marker
        dest = route["path"][-1]
        folium.CircleMarker(
            location=dest, radius=6, color=route["color"],
            fill=True, fill_color=route["color"], fill_opacity=0.5,
            tooltip=f"Destination: {route['name']}",
        ).add_to(m)
    # Arrows (AntPath-like dashed effect)
    components.html(m._repr_html_(), height=550)

    # Chart by drug type
    drug_counts = {}
    for r in filtered:
        drug_counts[r["drug"]] = drug_counts.get(r["drug"], 0) + 1
    if drug_counts:
        fig, ax = plt.subplots(figsize=(6, 4), facecolor=_BG)
        ax.set_facecolor(_SURFACE)
        drugs = list(drug_counts.keys())
        counts = list(drug_counts.values())
        bar_colors = ["#ef4444", "#a855f7", "#ec4899", "#22c55e", "#eab308",
                      "#06b6d4", "#f43f5e", "#f97316"][:len(drugs)]
        ax.bar(drugs, counts, color=bar_colors, edgecolor="none")
        ax.set_title("Routes by Drug Type", color=_ACCENT, fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of Routes", color=_TEXT, fontsize=10)
        ax.tick_params(axis="x", colors=_TEXT, labelsize=8, rotation=30)
        ax.tick_params(axis="y", colors=_TEXT, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(_MUTED)
        ax.grid(axis="y", color=_MUTED, alpha=0.3, linestyle="--")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    if len(df) > 0:
        st.dataframe(df, width="stretch")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "drug_trafficking_routes.csv",
                           "text/csv", key="drug_csv")


def _render_interpol():
    """Mode 10: Interpol Red Notice countries."""
    st.markdown("#### Interpol Red Notice Activity by Country")
    st.caption("Approximate Red Notice counts per country (public data, estimated).")

    df = pd.DataFrame(INTERPOL_DATA).sort_values("red_notices", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Top Country", df.iloc[0]["country"])
    c3.metric("Total Notices", int(df["red_notices"].sum()))
    c4.metric("Avg Notices", f"{df['red_notices'].mean():.0f}")

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        coords = COUNTRY_COORDS.get(row["country"])
        if not coords:
            continue
        color = _interpol_color(row["red_notices"])
        popup_html = (f"<b>{html.escape(row['country'])}</b><br>"
                      f"Red Notices: ~{row['red_notices']}<br>"
                      f"Focus: {html.escape(row['focus'])}")
        folium.CircleMarker(
            location=coords, radius=max(5, row["red_notices"] / 60),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{row['country']}: ~{row['red_notices']} notices",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart top 15
    chart_df = df.head(15)
    labels = chart_df["country"].tolist()[::-1]
    vals = chart_df["red_notices"].tolist()[::-1]
    colors = [_interpol_color(v) for v in vals]
    fig = _dark_bar_chart(labels, vals, colors, "Top 15 Interpol Red Notice Countries",
                          "Approximate Red Notices", "")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.dataframe(df[["country", "red_notices", "focus"]], width="stretch")
    csv = df.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "interpol_red_notices.csv", "text/csv",
                       key="interpol_csv")


# ══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════

MAP_MODES = [
    "Global Peace Index",
    "Safest Cities in the World",
    "Travel Advisory Zones",
    "Piracy Hotspots",
    "Cybercrime Origins",
    "Police Stations & Emergency",
    "Fire Stations",
    "Prison Locations",
    "Drug Trafficking Routes",
    "Interpol Red Notice Countries",
]

_MODE_RENDERERS = {
    "Global Peace Index": _render_global_peace_index,
    "Safest Cities in the World": _render_safest_cities,
    "Travel Advisory Zones": _render_travel_advisory,
    "Piracy Hotspots": _render_piracy_hotspots,
    "Cybercrime Origins": _render_cybercrime,
    "Police Stations & Emergency": _render_police_stations,
    "Fire Stations": _render_fire_stations,
    "Prison Locations": _render_prisons,
    "Drug Trafficking Routes": _render_drug_routes,
    "Interpol Red Notice Countries": _render_interpol,
}


def render_crime_safety_maps_tab():
    """Main render function for the Crime & Safety Maps tab."""

    # ── Tab header ──
    st.markdown(
        '<div class="tab-header red">'
        "<h4>Crime &amp; Safety Maps</h4>"
        "<p>Explore global safety indices, crime data, travel advisories, piracy zones, "
        "emergency services, and law enforcement activity worldwide.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.selectbox("Select map mode", MAP_MODES, key="crime_mode")

    st.markdown("---")

    # ── Dispatch to renderer ──
    renderer = _MODE_RENDERERS.get(mode)
    if renderer:
        renderer()
