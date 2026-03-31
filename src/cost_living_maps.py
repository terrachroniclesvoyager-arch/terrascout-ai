# -*- coding: utf-8 -*-
"""
Cost of Living & Economy Maps module for TerraScout AI.
Provides 10 map modes covering living costs, salaries, real estate,
Big Mac Index, GDP, minimum wages, tax rates, healthcare costs,
rent affordability, and digital nomad indices worldwide.
Uses curated datasets plus World Bank API (free, no key).
"""

import io
import streamlit as st
import requests
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

# ═══════════════════════════════════════════════════════════
# WORLD BANK API
# ═══════════════════════════════════════════════════════════
WB_GDP_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/"
    "NY.GDP.PCAP.CD?format=json&per_page=300&date=2022"
)

# ═══════════════════════════════════════════════════════════
# COUNTRY COORDINATES (ISO2 -> lat, lon)
# ═══════════════════════════════════════════════════════════
COUNTRY_COORDS = {
    "US": (39.83, -98.58), "GB": (55.38, -3.44), "FR": (46.60, 1.89),
    "DE": (51.17, 10.45), "IT": (41.87, 12.57), "ES": (40.46, -3.75),
    "PT": (39.40, -8.22), "NL": (52.13, 5.29), "BE": (50.50, 4.47),
    "CH": (46.82, 8.23), "AT": (47.52, 14.55), "SE": (60.13, 18.64),
    "NO": (60.47, 8.47), "DK": (56.26, 9.50), "FI": (61.92, 25.75),
    "IE": (53.14, -7.69), "PL": (51.92, 19.15), "CZ": (49.82, 15.47),
    "GR": (39.07, 21.82), "HU": (47.16, 19.50), "RO": (45.94, 24.97),
    "BG": (42.73, 25.49), "HR": (45.10, 15.20), "SK": (48.67, 19.70),
    "SI": (46.15, 14.99), "LT": (55.17, 23.88), "LV": (56.88, 24.60),
    "EE": (58.60, 25.01), "RS": (44.02, 21.01), "BA": (43.92, 17.68),
    "MK": (41.51, 21.75), "AL": (41.15, 20.17), "ME": (42.71, 19.37),
    "IS": (64.96, -19.02), "LU": (49.82, 6.13),
    "CA": (56.13, -106.35), "MX": (23.63, -102.55), "BR": (-14.24, -51.93),
    "AR": (-38.42, -63.62), "CL": (-35.68, -71.54), "CO": (4.57, -74.30),
    "PE": (-9.19, -75.02), "UY": (-32.52, -55.77), "EC": (-1.83, -78.18),
    "VE": (6.42, -66.59), "CR": (9.75, -83.75), "PA": (8.54, -80.78),
    "JP": (36.20, 138.25), "CN": (35.86, 104.20), "KR": (35.91, 127.77),
    "IN": (20.59, 78.96), "TH": (15.87, 100.99), "VN": (14.06, 108.28),
    "PH": (12.88, 121.77), "ID": (-0.79, 113.92), "MY": (4.21, 101.98),
    "SG": (1.35, 103.82), "TW": (23.70, 120.96), "HK": (22.40, 114.11),
    "AU": (-25.27, 133.78), "NZ": (-40.90, 174.89),
    "RU": (61.52, 105.32), "TR": (38.96, 35.24), "IL": (31.05, 34.85),
    "AE": (23.42, 53.85), "SA": (23.89, 45.08), "QA": (25.35, 51.18),
    "KW": (29.31, 47.48), "BH": (26.07, 50.55), "OM": (21.47, 55.98),
    "ZA": (-30.56, 22.94), "EG": (26.82, 30.80), "NG": (9.08, 8.68),
    "KE": (-0.02, 37.91), "MA": (31.79, -7.09), "TN": (33.89, 9.54),
    "GH": (7.95, -1.02), "ET": (9.15, 40.49), "TZ": (-6.37, 34.89),
    "UA": (48.38, 31.17), "PK": (30.38, 69.35), "BD": (23.68, 90.36),
    "LK": (7.87, 80.77), "NP": (28.39, 84.12), "MM": (21.91, 95.96),
    "KH": (12.57, 104.99), "GE": (42.32, 43.36), "JO": (30.59, 36.24),
    "LB": (33.85, 35.86), "DO": (18.74, -70.16), "GT": (15.78, -90.23),
    "HN": (15.20, -86.24), "SV": (13.79, -88.90), "NI": (12.87, -85.21),
    "BO": (-16.29, -63.59), "PY": (-23.44, -58.44),
}

# ═══════════════════════════════════════════════════════════
# MAP MODE 1: COST OF LIVING INDEX (80+ cities)
# ═══════════════════════════════════════════════════════════
COST_OF_LIVING_DATA = [
    # (city, country, lat, lon, overall_index, rent_idx, groceries_idx, restaurant_idx, transport_idx)
    ("Zurich", "Switzerland", 47.38, 8.54, 131.2, 62.4, 128.5, 130.0, 105.8),
    ("Geneva", "Switzerland", 46.20, 6.14, 126.8, 58.7, 125.0, 126.5, 101.3),
    ("Basel", "Switzerland", 47.56, 7.59, 122.5, 54.2, 120.7, 121.0, 98.7),
    ("New York", "USA", 40.71, -74.01, 100.0, 100.0, 100.0, 100.0, 100.0),
    ("San Francisco", "USA", 37.77, -122.42, 97.6, 104.2, 96.8, 95.4, 92.1),
    ("Los Angeles", "USA", 34.05, -118.24, 84.5, 80.1, 82.3, 82.8, 87.5),
    ("Chicago", "USA", 41.88, -87.63, 79.2, 62.4, 78.1, 80.0, 85.0),
    ("Washington DC", "USA", 38.91, -77.04, 87.9, 78.5, 84.2, 87.5, 91.0),
    ("Miami", "USA", 25.76, -80.19, 82.4, 73.6, 80.1, 79.5, 82.0),
    ("Boston", "USA", 42.36, -71.06, 90.7, 85.3, 86.4, 88.0, 89.2),
    ("Seattle", "USA", 47.61, -122.33, 88.0, 76.5, 83.5, 86.1, 87.5),
    ("London", "UK", 51.51, -0.13, 92.5, 74.2, 85.7, 90.3, 95.2),
    ("Edinburgh", "UK", 55.95, -3.19, 72.8, 45.3, 68.5, 70.2, 80.1),
    ("Paris", "France", 48.86, 2.35, 87.1, 59.4, 83.5, 85.0, 78.5),
    ("Lyon", "France", 45.76, 4.84, 70.2, 38.1, 69.8, 67.5, 71.0),
    ("Berlin", "Germany", 52.52, 13.41, 70.5, 37.0, 65.2, 62.8, 72.5),
    ("Munich", "Germany", 48.14, 11.58, 82.0, 52.3, 74.0, 78.5, 79.0),
    ("Frankfurt", "Germany", 50.11, 8.68, 76.3, 45.2, 70.1, 74.0, 76.5),
    ("Amsterdam", "Netherlands", 52.37, 4.90, 82.3, 55.6, 72.4, 79.8, 70.1),
    ("Copenhagen", "Denmark", 55.68, 12.57, 97.8, 49.5, 85.3, 98.2, 78.0),
    ("Stockholm", "Sweden", 59.33, 18.07, 84.3, 44.8, 72.8, 82.5, 79.8),
    ("Oslo", "Norway", 59.91, 10.75, 101.4, 46.8, 90.5, 105.0, 82.0),
    ("Helsinki", "Finland", 60.17, 24.94, 79.8, 38.2, 73.5, 80.5, 70.5),
    ("Dublin", "Ireland", 53.35, -6.26, 85.2, 60.8, 74.0, 82.0, 78.5),
    ("Vienna", "Austria", 48.21, 16.37, 72.5, 36.8, 68.5, 66.8, 65.5),
    ("Brussels", "Belgium", 50.85, 4.35, 73.8, 40.2, 66.5, 72.0, 63.5),
    ("Rome", "Italy", 41.90, 12.50, 70.0, 35.5, 63.0, 68.0, 55.0),
    ("Milan", "Italy", 45.46, 9.19, 76.0, 45.8, 66.5, 74.5, 60.5),
    ("Madrid", "Spain", 40.42, -3.70, 62.5, 30.5, 57.0, 58.0, 52.0),
    ("Barcelona", "Spain", 41.39, 2.17, 66.8, 38.2, 60.5, 62.0, 55.0),
    ("Lisbon", "Portugal", 38.72, -9.14, 56.2, 28.5, 48.5, 50.0, 42.0),
    ("Prague", "Czech Republic", 50.08, 14.44, 52.0, 25.8, 46.0, 45.0, 35.0),
    ("Warsaw", "Poland", 52.23, 21.01, 47.5, 22.0, 40.5, 40.0, 32.0),
    ("Budapest", "Hungary", 47.50, 19.04, 45.8, 19.5, 38.0, 35.5, 28.0),
    ("Bucharest", "Romania", 44.43, 26.10, 42.0, 17.5, 35.5, 33.0, 22.0),
    ("Athens", "Greece", 37.98, 23.73, 55.2, 22.0, 52.0, 48.0, 38.0),
    ("Tokyo", "Japan", 35.68, 139.69, 83.5, 46.0, 82.0, 55.5, 62.0),
    ("Osaka", "Japan", 34.69, 135.50, 73.0, 36.5, 75.0, 48.0, 55.0),
    ("Seoul", "South Korea", 37.57, 127.00, 78.2, 38.5, 80.5, 52.0, 42.0),
    ("Singapore", "Singapore", 1.35, 103.82, 91.8, 82.5, 78.0, 62.0, 55.5),
    ("Hong Kong", "China", 22.40, 114.11, 88.0, 95.8, 78.5, 58.0, 50.0),
    ("Shanghai", "China", 31.23, 121.47, 52.5, 30.2, 48.0, 32.0, 18.0),
    ("Beijing", "China", 39.90, 116.41, 50.8, 28.5, 46.0, 30.0, 16.0),
    ("Taipei", "Taiwan", 25.03, 121.57, 56.0, 26.5, 52.5, 28.5, 22.0),
    ("Bangkok", "Thailand", 13.76, 100.50, 40.2, 16.5, 38.0, 22.5, 15.0),
    ("Ho Chi Minh City", "Vietnam", 10.82, 106.63, 35.5, 12.0, 33.5, 18.0, 10.0),
    ("Hanoi", "Vietnam", 21.03, 105.85, 33.0, 10.5, 31.0, 16.0, 8.5),
    ("Kuala Lumpur", "Malaysia", 3.14, 101.69, 38.5, 14.0, 36.5, 20.0, 12.5),
    ("Jakarta", "Indonesia", -6.21, 106.85, 36.0, 10.8, 34.0, 16.5, 8.0),
    ("Manila", "Philippines", 14.60, 120.98, 37.5, 11.5, 36.0, 18.5, 9.0),
    ("Mumbai", "India", 19.08, 72.88, 30.0, 10.0, 28.5, 14.0, 6.5),
    ("New Delhi", "India", 28.61, 77.21, 28.5, 8.5, 27.0, 12.5, 6.0),
    ("Bangalore", "India", 12.97, 77.59, 26.8, 8.0, 25.5, 11.5, 5.5),
    ("Sydney", "Australia", -33.87, 151.21, 89.5, 65.0, 80.5, 82.0, 78.0),
    ("Melbourne", "Australia", -37.81, 144.96, 83.0, 55.2, 76.0, 78.0, 72.0),
    ("Auckland", "New Zealand", -36.85, 174.76, 76.5, 42.0, 72.5, 70.0, 65.0),
    ("Toronto", "Canada", 43.65, -79.38, 78.5, 55.8, 72.0, 70.5, 72.5),
    ("Vancouver", "Canada", 49.28, -123.12, 80.2, 60.5, 73.5, 72.0, 68.0),
    ("Montreal", "Canada", 45.50, -73.57, 67.5, 38.5, 64.0, 62.0, 58.0),
    ("Dubai", "UAE", 25.20, 55.27, 72.0, 48.5, 58.0, 62.0, 45.0),
    ("Abu Dhabi", "UAE", 24.45, 54.65, 68.5, 44.2, 55.5, 58.0, 42.0),
    ("Tel Aviv", "Israel", 32.09, 34.78, 93.2, 60.5, 82.5, 88.0, 62.0),
    ("Istanbul", "Turkey", 41.01, 28.98, 38.5, 12.8, 35.0, 25.0, 14.0),
    ("Moscow", "Russia", 55.76, 37.62, 45.0, 22.5, 42.0, 35.0, 18.5),
    ("St Petersburg", "Russia", 59.93, 30.32, 38.0, 16.5, 36.0, 28.0, 15.0),
    ("Sao Paulo", "Brazil", -23.55, -46.63, 42.5, 18.0, 38.0, 28.0, 15.5),
    ("Rio de Janeiro", "Brazil", -22.91, -43.17, 45.0, 20.5, 40.0, 30.0, 17.0),
    ("Buenos Aires", "Argentina", -34.60, -58.38, 32.0, 10.0, 30.0, 18.0, 8.5),
    ("Mexico City", "Mexico", 19.43, -99.13, 38.0, 13.0, 35.0, 24.0, 10.5),
    ("Santiago", "Chile", -33.45, -70.67, 45.5, 20.0, 42.0, 32.0, 18.0),
    ("Lima", "Peru", -12.05, -77.04, 35.0, 11.5, 32.0, 20.0, 10.0),
    ("Bogota", "Colombia", 4.71, -74.07, 30.5, 9.5, 28.0, 16.0, 8.0),
    ("Cairo", "Egypt", 30.04, 31.24, 25.0, 5.5, 23.5, 12.0, 4.5),
    ("Nairobi", "Kenya", -1.29, 36.82, 32.0, 10.0, 30.0, 18.0, 8.0),
    ("Cape Town", "South Africa", -33.93, 18.42, 38.0, 14.0, 35.0, 22.0, 12.0),
    ("Johannesburg", "South Africa", -26.20, 28.05, 35.5, 12.0, 32.5, 20.5, 10.5),
    ("Lagos", "Nigeria", 6.52, 3.38, 35.0, 15.0, 33.0, 19.0, 9.5),
    ("Casablanca", "Morocco", 33.59, -7.59, 32.5, 9.0, 30.0, 18.0, 7.5),
    ("Doha", "Qatar", 25.29, 51.53, 65.5, 44.0, 52.0, 55.0, 38.0),
    ("Riyadh", "Saudi Arabia", 24.71, 46.68, 48.0, 20.0, 42.0, 38.0, 22.0),
    ("Reykjavik", "Iceland", 64.15, -21.94, 100.5, 52.0, 92.0, 102.0, 75.0),
]

# ═══════════════════════════════════════════════════════════
# MAP MODE 2: AVERAGE SALARY BY COUNTRY (USD monthly)
# ═══════════════════════════════════════════════════════════
SALARY_DATA = {
    "US": 5500, "GB": 3800, "FR": 3200, "DE": 3600, "IT": 2600, "ES": 2200,
    "PT": 1500, "NL": 3700, "BE": 3400, "CH": 6800, "AT": 3400, "SE": 3800,
    "NO": 4800, "DK": 4600, "FI": 3500, "IE": 3900, "PL": 1500, "CZ": 1650,
    "GR": 1300, "HU": 1200, "RO": 1100, "BG": 900, "HR": 1200, "SK": 1400,
    "SI": 2100, "LT": 1400, "LV": 1250, "EE": 1600, "RS": 800, "BA": 650,
    "MK": 600, "AL": 500, "ME": 700, "IS": 5200, "LU": 5400,
    "CA": 4200, "MX": 600, "BR": 650, "AR": 450, "CL": 950, "CO": 400,
    "PE": 450, "UY": 850, "EC": 400, "CR": 750, "PA": 800,
    "JP": 3200, "CN": 1100, "KR": 2800, "IN": 350, "TH": 550, "VN": 300,
    "PH": 280, "ID": 300, "MY": 800, "SG": 4500, "TW": 1700, "HK": 3200,
    "AU": 4500, "NZ": 3500, "RU": 700, "TR": 500, "IL": 3400, "AE": 3500,
    "SA": 2500, "QA": 3800, "KW": 3200, "EG": 200, "NG": 150, "KE": 250,
    "MA": 350, "ZA": 700, "GH": 180, "TN": 280, "UA": 450, "PK": 180,
    "BD": 150, "LK": 200, "NP": 140, "GE": 500, "JO": 550, "DO": 350,
}

# ═══════════════════════════════════════════════════════════
# MAP MODE 3: REAL ESTATE PRICES (per sqm, city centre, USD)
# ═══════════════════════════════════════════════════════════
REAL_ESTATE_DATA = [
    # (city, country, lat, lon, price_sqm_centre, price_sqm_outside)
    ("Hong Kong", "China", 22.40, 114.11, 28500, 18200),
    ("Monaco", "Monaco", 43.73, 7.42, 53000, 40000),
    ("Singapore", "Singapore", 1.35, 103.82, 18500, 11200),
    ("London", "UK", 51.51, -0.13, 17800, 8500),
    ("New York", "USA", 40.71, -74.01, 16200, 8900),
    ("San Francisco", "USA", 37.77, -122.42, 12500, 8200),
    ("Paris", "France", 48.86, 2.35, 13200, 7500),
    ("Tokyo", "Japan", 35.68, 139.69, 12000, 6800),
    ("Sydney", "Australia", -33.87, 151.21, 11500, 7200),
    ("Zurich", "Switzerland", 47.38, 8.54, 14500, 9800),
    ("Geneva", "Switzerland", 46.20, 6.14, 15800, 10500),
    ("Tel Aviv", "Israel", 32.09, 34.78, 12800, 8500),
    ("Seoul", "South Korea", 37.57, 127.00, 11200, 6500),
    ("Vancouver", "Canada", 49.28, -123.12, 8500, 5800),
    ("Toronto", "Canada", 43.65, -79.38, 7800, 5200),
    ("Milan", "Italy", 45.46, 9.19, 5800, 3200),
    ("Munich", "Germany", 48.14, 11.58, 9500, 6200),
    ("Berlin", "Germany", 52.52, 13.41, 5200, 3500),
    ("Amsterdam", "Netherlands", 52.37, 4.90, 7800, 4800),
    ("Copenhagen", "Denmark", 55.68, 12.57, 6500, 4200),
    ("Stockholm", "Sweden", 59.33, 18.07, 7200, 4500),
    ("Oslo", "Norway", 59.91, 10.75, 7500, 4800),
    ("Dublin", "Ireland", 53.35, -6.26, 6200, 4000),
    ("Vienna", "Austria", 48.21, 16.37, 5800, 3800),
    ("Melbourne", "Australia", -37.81, 144.96, 7500, 5200),
    ("Auckland", "New Zealand", -36.85, 174.76, 6800, 4500),
    ("Los Angeles", "USA", 34.05, -118.24, 9200, 6800),
    ("Chicago", "USA", 41.88, -87.63, 3800, 2200),
    ("Miami", "USA", 25.76, -80.19, 5500, 3500),
    ("Dubai", "UAE", 25.20, 55.27, 4200, 2400),
    ("Shanghai", "China", 31.23, 121.47, 10500, 5800),
    ("Beijing", "China", 39.90, 116.41, 9800, 5200),
    ("Mumbai", "India", 19.08, 72.88, 5500, 2200),
    ("Bangkok", "Thailand", 13.76, 100.50, 3800, 1800),
    ("Istanbul", "Turkey", 41.01, 28.98, 1800, 900),
    ("Moscow", "Russia", 55.76, 37.62, 4500, 2500),
    ("Sao Paulo", "Brazil", -23.55, -46.63, 3200, 1800),
    ("Buenos Aires", "Argentina", -34.60, -58.38, 2200, 1200),
    ("Mexico City", "Mexico", 19.43, -99.13, 2500, 1200),
    ("Lisbon", "Portugal", 38.72, -9.14, 4800, 2800),
    ("Barcelona", "Spain", 41.39, 2.17, 4500, 2500),
    ("Madrid", "Spain", 40.42, -3.70, 4200, 2200),
    ("Rome", "Italy", 41.90, 12.50, 4200, 2500),
    ("Prague", "Czech Republic", 50.08, 14.44, 4200, 2600),
    ("Warsaw", "Poland", 52.23, 21.01, 3200, 2000),
    ("Budapest", "Hungary", 47.50, 19.04, 2800, 1600),
    ("Athens", "Greece", 37.98, 23.73, 2400, 1400),
    ("Taipei", "Taiwan", 25.03, 121.57, 8500, 4500),
    ("Kuala Lumpur", "Malaysia", 3.14, 101.69, 2200, 1100),
    ("Jakarta", "Indonesia", -6.21, 106.85, 2000, 900),
    ("Manila", "Philippines", 14.60, 120.98, 2800, 1200),
    ("Cape Town", "South Africa", -33.93, 18.42, 2100, 1200),
    ("Nairobi", "Kenya", -1.29, 36.82, 1500, 650),
    ("Cairo", "Egypt", 30.04, 31.24, 900, 450),
    ("Santiago", "Chile", -33.45, -70.67, 2800, 1500),
    ("Lima", "Peru", -12.05, -77.04, 1800, 800),
    ("Bogota", "Colombia", 4.71, -74.07, 1600, 700),
    ("Helsinki", "Finland", 60.17, 24.94, 5500, 3500),
    ("Brussels", "Belgium", 50.85, 4.35, 3800, 2400),
    ("Reykjavik", "Iceland", 64.15, -21.94, 5200, 3800),
]

# ═══════════════════════════════════════════════════════════
# MAP MODE 4: BIG MAC INDEX (prices in USD)
# ═══════════════════════════════════════════════════════════
BIG_MAC_DATA = {
    # country_code: (price_usd, implied_ppp_rate)
    "CH": (7.73, 1.17), "NO": (6.92, 1.05), "SE": (6.25, 0.95),
    "US": (5.69, 1.00), "CA": (5.42, 0.95), "DK": (5.18, 0.79),
    "IL": (5.12, 0.90), "AU": (5.08, 0.89), "NZ": (4.95, 0.87),
    "SG": (4.82, 0.85), "IE": (4.78, 0.84), "GB": (4.72, 0.83),
    "FI": (4.68, 0.82), "FR": (4.65, 0.82), "DE": (4.58, 0.80),
    "IT": (4.55, 0.80), "AT": (4.52, 0.79), "BE": (4.48, 0.79),
    "NL": (4.45, 0.78), "KR": (4.35, 0.76), "AE": (4.22, 0.74),
    "JP": (4.12, 0.72), "ES": (4.05, 0.71), "PT": (3.95, 0.69),
    "CZ": (3.85, 0.68), "SA": (3.78, 0.66), "GR": (3.72, 0.65),
    "CL": (3.65, 0.64), "PL": (3.55, 0.62), "HR": (3.48, 0.61),
    "HU": (3.42, 0.60), "BR": (3.35, 0.59), "CN": (3.28, 0.58),
    "TH": (3.18, 0.56), "MX": (3.12, 0.55), "CO": (3.05, 0.54),
    "TR": (2.95, 0.52), "PE": (2.88, 0.51), "AR": (2.82, 0.50),
    "VN": (2.75, 0.48), "PH": (2.68, 0.47), "ID": (2.55, 0.45),
    "MY": (2.45, 0.43), "IN": (2.35, 0.41), "RO": (2.78, 0.49),
    "ZA": (2.52, 0.44), "EG": (1.95, 0.34), "NG": (2.12, 0.37),
    "PK": (1.75, 0.31), "UA": (2.15, 0.38), "RU": (2.25, 0.40),
    "TW": (3.92, 0.69), "HK": (3.05, 0.54), "LB": (2.48, 0.44),
}

# ═══════════════════════════════════════════════════════════
# MAP MODE 6: MINIMUM WAGE (USD/month)
# ═══════════════════════════════════════════════════════════
MINIMUM_WAGE_DATA = {
    "LU": 2570, "AU": 2450, "NZ": 2350, "IE": 2080, "NL": 2070,
    "DE": 2050, "GB": 2000, "FR": 1970, "BE": 1955, "KR": 1800,
    "ES": 1260, "SI": 1250, "US": 1260, "CA": 1900, "JP": 1350,
    "IL": 1600, "PT": 960, "GR": 910, "PL": 900, "CZ": 780,
    "SK": 760, "HR": 750, "EE": 740, "LT": 720, "LV": 680,
    "HU": 660, "RO": 620, "BG": 430, "RS": 380, "BA": 280,
    "MK": 320, "AL": 300, "ME": 370, "TR": 370, "RU": 180,
    "UA": 180, "MX": 310, "BR": 280, "AR": 250, "CL": 500,
    "CO": 270, "PE": 260, "CR": 530, "PA": 550, "UY": 430,
    "EC": 450, "DO": 280, "GT": 400, "HN": 350, "SV": 365,
    "NI": 200, "BO": 310, "PY": 350, "CN": 380, "TH": 310,
    "VN": 180, "PH": 230, "ID": 180, "MY": 310, "TW": 900,
    "IN": 80, "BD": 95, "PK": 110, "NP": 90, "LK": 85,
    "KH": 200, "MM": 90, "KE": 150, "ZA": 280, "MA": 290,
    "TN": 160, "EG": 120, "NG": 70, "GH": 70, "ET": 0,
    "TZ": 55, "GE": 50, "JO": 280, "SA": 0, "AE": 0,
    "QA": 0, "KW": 0, "SG": 0, "HK": 960, "IS": 0,
    "NO": 0, "DK": 0, "SE": 0, "FI": 0, "CH": 0,
    "AT": 0, "IT": 0,
}

# ═══════════════════════════════════════════════════════════
# MAP MODE 7: TAX RATES (income tax top rate %, VAT %)
# ═══════════════════════════════════════════════════════════
TAX_DATA = {
    # code: (income_tax_top_pct, vat_pct)
    "DK": (55.9, 25), "SE": (52.3, 25), "JP": (55.9, 10), "AT": (55.0, 20),
    "FI": (53.8, 24), "BE": (53.5, 21), "PT": (53.0, 23), "FR": (51.5, 20),
    "NL": (49.5, 21), "IE": (48.0, 23), "SI": (50.0, 22), "DE": (47.5, 19),
    "IT": (47.2, 22), "NO": (46.4, 25), "ES": (47.0, 21), "GB": (45.0, 20),
    "GR": (44.0, 24), "IS": (46.2, 24), "LU": (45.8, 17), "AU": (45.0, 10),
    "CA": (53.5, 5), "NZ": (39.0, 15), "US": (37.0, 0), "KR": (45.0, 10),
    "PL": (36.0, 23), "CZ": (23.0, 21), "SK": (25.0, 20), "CH": (40.0, 7.7),
    "HR": (30.0, 25), "HU": (15.0, 27), "RO": (10.0, 19), "BG": (10.0, 20),
    "RS": (15.0, 20), "MK": (18.0, 18), "AL": (23.0, 20), "ME": (15.0, 21),
    "EE": (20.0, 22), "LT": (32.0, 21), "LV": (31.0, 21),
    "TR": (40.0, 20), "IL": (50.0, 17), "CN": (45.0, 13), "IN": (42.7, 18),
    "TH": (35.0, 7), "VN": (35.0, 8), "PH": (35.0, 12), "ID": (35.0, 11),
    "MY": (30.0, 0), "SG": (22.0, 9), "HK": (17.0, 0), "TW": (40.0, 5),
    "RU": (15.0, 20), "UA": (18.0, 20), "AE": (0.0, 5), "SA": (0.0, 15),
    "QA": (0.0, 0), "KW": (0.0, 0), "BH": (0.0, 10), "BR": (27.5, 17),
    "MX": (35.0, 16), "AR": (35.0, 21), "CL": (40.0, 19), "CO": (39.0, 19),
    "ZA": (45.0, 15), "EG": (25.0, 14), "NG": (24.0, 7.5), "KE": (30.0, 16),
    "MA": (38.0, 20), "GH": (35.0, 15),
}

# ═══════════════════════════════════════════════════════════
# MAP MODE 8: HEALTHCARE SPENDING (USD per capita)
# ═══════════════════════════════════════════════════════════
HEALTHCARE_DATA = {
    "US": 12555, "CH": 9660, "DE": 7380, "NO": 7065, "AT": 6690,
    "SE": 6260, "NL": 6190, "DK": 6380, "BE": 5930, "FR": 5680,
    "CA": 5740, "AU": 5630, "IE": 5820, "LU": 6110, "GB": 5270,
    "JP": 4690, "FI": 4640, "IS": 5400, "NZ": 4640, "IT": 3750,
    "KR": 3580, "ES": 3720, "IL": 3400, "PT": 3350, "SI": 3100,
    "CZ": 3010, "GR": 2280, "SK": 2260, "LT": 2160, "EE": 2100,
    "HU": 2050, "PL": 1850, "HR": 1630, "LV": 1560, "CL": 1640,
    "RO": 1160, "BG": 1100, "AR": 1150, "BR": 920, "MX": 600,
    "TR": 540, "RU": 580, "TH": 290, "CN": 440, "CO": 420,
    "ZA": 470, "MY": 420, "PE": 340, "UA": 200, "EG": 160,
    "ID": 120, "VN": 130, "PH": 140, "IN": 75, "PK": 45,
    "NG": 20, "KE": 80, "BD": 42, "ET": 25, "NP": 55,
    "AE": 2200, "SA": 1440, "QA": 2000, "KW": 1680, "SG": 2650,
    "HK": 2520, "TW": 1400,
}

# ═══════════════════════════════════════════════════════════
# MAP MODE 9: RENT AFFORDABILITY (rent-to-income %)
# ═══════════════════════════════════════════════════════════
RENT_AFFORD_DATA = [
    # (city, country, lat, lon, rent_to_income_pct)
    ("Hong Kong", "China", 22.40, 114.11, 72.5),
    ("New York", "USA", 40.71, -74.01, 62.0),
    ("San Francisco", "USA", 37.77, -122.42, 58.5),
    ("London", "UK", 51.51, -0.13, 55.8),
    ("Singapore", "Singapore", 1.35, 103.82, 52.0),
    ("Sydney", "Australia", -33.87, 151.21, 50.5),
    ("Miami", "USA", 25.76, -80.19, 54.0),
    ("Los Angeles", "USA", 34.05, -118.24, 53.5),
    ("Vancouver", "Canada", 49.28, -123.12, 51.8),
    ("Tokyo", "Japan", 35.68, 139.69, 42.0),
    ("Paris", "France", 48.86, 2.35, 48.5),
    ("Tel Aviv", "Israel", 32.09, 34.78, 47.0),
    ("Seoul", "South Korea", 37.57, 127.00, 45.5),
    ("Dublin", "Ireland", 53.35, -6.26, 46.2),
    ("Boston", "USA", 42.36, -71.06, 50.0),
    ("Melbourne", "Australia", -37.81, 144.96, 44.0),
    ("Toronto", "Canada", 43.65, -79.38, 48.5),
    ("Amsterdam", "Netherlands", 52.37, 4.90, 42.5),
    ("Zurich", "Switzerland", 47.38, 8.54, 38.0),
    ("Munich", "Germany", 48.14, 11.58, 40.5),
    ("Stockholm", "Sweden", 59.33, 18.07, 36.0),
    ("Copenhagen", "Denmark", 55.68, 12.57, 34.0),
    ("Oslo", "Norway", 59.91, 10.75, 32.5),
    ("Dubai", "UAE", 25.20, 55.27, 38.5),
    ("Berlin", "Germany", 52.52, 13.41, 32.0),
    ("Barcelona", "Spain", 41.39, 2.17, 40.0),
    ("Madrid", "Spain", 40.42, -3.70, 35.0),
    ("Milan", "Italy", 45.46, 9.19, 38.0),
    ("Rome", "Italy", 41.90, 12.50, 34.5),
    ("Vienna", "Austria", 48.21, 16.37, 30.0),
    ("Lisbon", "Portugal", 38.72, -9.14, 42.0),
    ("Brussels", "Belgium", 50.85, 4.35, 32.5),
    ("Helsinki", "Finland", 60.17, 24.94, 30.0),
    ("Prague", "Czech Republic", 50.08, 14.44, 38.5),
    ("Warsaw", "Poland", 52.23, 21.01, 34.0),
    ("Budapest", "Hungary", 47.50, 19.04, 32.0),
    ("Athens", "Greece", 37.98, 23.73, 36.0),
    ("Shanghai", "China", 31.23, 121.47, 50.0),
    ("Beijing", "China", 39.90, 116.41, 48.0),
    ("Taipei", "Taiwan", 25.03, 121.57, 42.5),
    ("Bangkok", "Thailand", 13.76, 100.50, 30.0),
    ("Ho Chi Minh City", "Vietnam", 10.82, 106.63, 28.0),
    ("Kuala Lumpur", "Malaysia", 3.14, 101.69, 25.0),
    ("Jakarta", "Indonesia", -6.21, 106.85, 22.0),
    ("Manila", "Philippines", 14.60, 120.98, 28.5),
    ("Mumbai", "India", 19.08, 72.88, 38.0),
    ("New Delhi", "India", 28.61, 77.21, 30.0),
    ("Sao Paulo", "Brazil", -23.55, -46.63, 35.0),
    ("Mexico City", "Mexico", 19.43, -99.13, 28.0),
    ("Buenos Aires", "Argentina", -34.60, -58.38, 22.0),
    ("Santiago", "Chile", -33.45, -70.67, 32.0),
    ("Lima", "Peru", -12.05, -77.04, 25.0),
    ("Bogota", "Colombia", 4.71, -74.07, 24.0),
    ("Moscow", "Russia", 55.76, 37.62, 42.0),
    ("Istanbul", "Turkey", 41.01, 28.98, 34.0),
    ("Cairo", "Egypt", 30.04, 31.24, 18.0),
    ("Nairobi", "Kenya", -1.29, 36.82, 20.0),
    ("Cape Town", "South Africa", -33.93, 18.42, 28.0),
    ("Lagos", "Nigeria", 6.52, 3.38, 32.0),
    ("Reykjavik", "Iceland", 64.15, -21.94, 35.0),
]

# ═══════════════════════════════════════════════════════════
# MAP MODE 10: DIGITAL NOMAD INDEX
# ═══════════════════════════════════════════════════════════
NOMAD_DATA = [
    # (city, country, lat, lon, internet_mbps, cowork_usd_month, visa_ease_1_10, safety_1_10, nomad_score)
    ("Lisbon", "Portugal", 38.72, -9.14, 120, 200, 9, 8, 92),
    ("Bangkok", "Thailand", 13.76, 100.50, 80, 100, 8, 7, 90),
    ("Chiang Mai", "Thailand", 18.79, 98.98, 70, 80, 8, 8, 89),
    ("Bali (Canggu)", "Indonesia", -8.65, 115.13, 50, 120, 9, 7, 87),
    ("Medellin", "Colombia", 6.25, -75.56, 55, 100, 8, 6, 85),
    ("Mexico City", "Mexico", 19.43, -99.13, 65, 130, 9, 6, 86),
    ("Tbilisi", "Georgia", 41.72, 44.79, 50, 80, 10, 8, 88),
    ("Budapest", "Hungary", 47.50, 19.04, 100, 150, 7, 8, 84),
    ("Prague", "Czech Republic", 50.08, 14.44, 95, 170, 7, 9, 83),
    ("Berlin", "Germany", 52.52, 13.41, 100, 200, 6, 9, 82),
    ("Barcelona", "Spain", 41.39, 2.17, 110, 220, 7, 8, 85),
    ("Buenos Aires", "Argentina", -34.60, -58.38, 45, 80, 9, 6, 83),
    ("Playa del Carmen", "Mexico", 20.63, -87.08, 55, 120, 9, 7, 84),
    ("Da Nang", "Vietnam", 16.05, 108.22, 50, 60, 8, 9, 86),
    ("Ho Chi Minh City", "Vietnam", 10.82, 106.63, 60, 80, 8, 8, 85),
    ("Kuala Lumpur", "Malaysia", 3.14, 101.69, 75, 100, 8, 8, 84),
    ("Tallinn", "Estonia", 59.44, 24.75, 90, 150, 9, 9, 87),
    ("Split", "Croatia", 43.51, 16.44, 70, 140, 7, 9, 82),
    ("Las Palmas", "Spain", 28.10, -15.41, 100, 180, 7, 9, 86),
    ("Belgrade", "Serbia", 44.79, 20.47, 55, 90, 9, 7, 81),
    ("Taipei", "Taiwan", 25.03, 121.57, 120, 130, 7, 9, 85),
    ("Seoul", "South Korea", 37.57, 127.00, 150, 200, 6, 9, 82),
    ("Cape Town", "South Africa", -33.93, 18.42, 50, 100, 8, 6, 80),
    ("Tulum", "Mexico", 20.21, -87.46, 40, 150, 9, 7, 79),
    ("Florianopolis", "Brazil", -27.60, -48.55, 55, 90, 8, 7, 78),
    ("Dubai", "UAE", 25.20, 55.27, 150, 350, 8, 9, 80),
    ("Riga", "Latvia", 56.95, 24.11, 80, 120, 7, 8, 79),
    ("Sofia", "Bulgaria", 42.70, 23.32, 65, 80, 7, 8, 80),
    ("Bucharest", "Romania", 44.43, 26.10, 70, 90, 7, 7, 78),
    ("Manila", "Philippines", 14.60, 120.98, 40, 80, 7, 5, 74),
    ("Colombo", "Sri Lanka", 6.93, 79.85, 30, 70, 7, 7, 73),
    ("Phnom Penh", "Cambodia", 11.56, 104.93, 35, 60, 9, 6, 76),
    ("Ubud", "Indonesia", -8.51, 115.26, 40, 100, 9, 8, 82),
    ("Porto", "Portugal", 41.15, -8.61, 100, 160, 9, 9, 88),
    ("Tenerife", "Spain", 28.29, -16.63, 90, 160, 7, 9, 84),
    ("Lima", "Peru", -12.05, -77.04, 50, 100, 8, 5, 75),
    ("Santiago", "Chile", -33.45, -70.67, 80, 130, 7, 7, 78),
    ("Athens", "Greece", 37.98, 23.73, 55, 120, 7, 8, 79),
    ("Koh Phangan", "Thailand", 9.75, 100.03, 40, 90, 8, 8, 80),
    ("Zanzibar", "Tanzania", -6.17, 39.19, 20, 60, 7, 7, 68),
    ("Oaxaca", "Mexico", 17.07, -96.73, 40, 80, 9, 6, 78),
    ("Cusco", "Peru", -13.53, -71.97, 35, 70, 8, 6, 72),
]


# ═══════════════════════════════════════════════════════════
# COLOR HELPERS
# ═══════════════════════════════════════════════════════════
def _value_color(value: float, vmin: float, vmax: float, reverse: bool = False) -> str:
    """Return a hex color from green->yellow->red gradient based on value."""
    if vmax == vmin:
        ratio = 0.5
    else:
        ratio = max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    if reverse:
        ratio = 1.0 - ratio
    # green (#10b981) -> yellow (#f59e0b) -> red (#ef4444)
    if ratio < 0.5:
        t = ratio * 2
        r = int(16 + t * (245 - 16))
        g = int(185 + t * (158 - 185))
        b = int(129 + t * (11 - 129))
    else:
        t = (ratio - 0.5) * 2
        r = int(245 + t * (239 - 245))
        g = int(158 + t * (68 - 158))
        b = int(11 + t * (68 - 11))
    return f"#{r:02x}{g:02x}{b:02x}"


def _make_popup(lines: list) -> str:
    """Build safe HTML popup string."""
    parts = []
    for label, val in lines:
        parts.append(
            f"<b>{escape(str(label))}</b>: {escape(str(val))}"
        )
    return "<br>".join(parts)


# ═══════════════════════════════════════════════════════════
# API: WORLD BANK GDP DATA
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def fetch_gdp_per_capita() -> list:
    """Fetch GDP per capita data from the World Bank API."""
    try:
        resp = requests.get(WB_GDP_URL, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        if len(payload) < 2:
            return []
        records = payload[1]
        results = []
        for rec in records:
            code = rec.get("country", {}).get("id", "")
            name = rec.get("country", {}).get("value", "")
            val = rec.get("value")
            if val is None or code not in COUNTRY_COORDS:
                continue
            lat, lon = COUNTRY_COORDS[code]
            results.append({
                "country": name,
                "code": code,
                "gdp_pc": round(float(val), 0),
                "lat": lat,
                "lon": lon,
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


# ═══════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════
def _bar_chart(df: pd.DataFrame, x_col: str, y_col: str,
               title: str, x_label: str, y_label: str,
               color: str = "#06b6d4", horizontal: bool = True) -> io.BytesIO:
    """Create a dark-themed bar chart and return as BytesIO PNG."""
    fig, ax = plt.subplots(figsize=(10, max(5, len(df) * 0.32)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    if horizontal:
        bars = ax.barh(df[x_col], df[y_col], color=color, edgecolor="#2a3550", linewidth=0.5)
        ax.set_xlabel(y_label, color="#e8ecf4", fontsize=10)
        ax.set_ylabel(x_label, color="#e8ecf4", fontsize=10)
        ax.invert_yaxis()
    else:
        bars = ax.bar(df[x_col], df[y_col], color=color, edgecolor="#2a3550", linewidth=0.5)
        ax.set_xlabel(x_label, color="#e8ecf4", fontsize=10)
        ax.set_ylabel(y_label, color="#e8ecf4", fontsize=10)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors="#8b97b0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x" if horizontal else "y", color="#2a3550", alpha=0.3, linewidth=0.5)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _dual_bar_chart(df: pd.DataFrame, x_col: str, y1_col: str, y2_col: str,
                    title: str, label1: str, label2: str,
                    color1: str = "#06b6d4", color2: str = "#f59e0b") -> io.BytesIO:
    """Create a grouped horizontal bar chart with two series."""
    import numpy as np
    fig, ax = plt.subplots(figsize=(10, max(5, len(df) * 0.38)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    y_pos = np.arange(len(df))
    bar_h = 0.35

    ax.barh(y_pos - bar_h / 2, df[y1_col], bar_h, label=label1,
            color=color1, edgecolor="#2a3550", linewidth=0.5)
    ax.barh(y_pos + bar_h / 2, df[y2_col], bar_h, label=label2,
            color=color2, edgecolor="#2a3550", linewidth=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df[x_col], fontsize=8)
    ax.invert_yaxis()
    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors="#8b97b0", labelsize=8)
    ax.legend(facecolor="#1a2235", edgecolor="#2a3550", labelcolor="#e8ecf4", fontsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3, linewidth=0.5)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════
# INDIVIDUAL MODE RENDERERS
# ═══════════════════════════════════════════════════════════

def _render_cost_of_living():
    """Mode 1: Cost of Living Index map."""
    st.markdown("#### Cost of Living Index")
    st.caption(
        "Numbeo-style index (NYC = 100). Higher values mean more expensive. "
        "Includes rent, groceries, restaurants, and transport sub-indices."
    )

    sort_by = st.selectbox("Sort / color by", [
        "Overall Index", "Rent Index", "Groceries Index",
        "Restaurant Index", "Transport Index"
    ], key="col_sort")

    col_map = {
        "Overall Index": 4, "Rent Index": 5, "Groceries Index": 6,
        "Restaurant Index": 7, "Transport Index": 8,
    }
    idx = col_map[sort_by]

    data = sorted(COST_OF_LIVING_DATA, key=lambda x: x[idx], reverse=True)
    vals = [r[idx] for r in data]
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", len(data))
    c2.metric("Most Expensive", data[0][0])
    c3.metric("Cheapest", data[-1][0])
    c4.metric("Median Index", f"{sorted(vals)[len(vals)//2]:.1f}")

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for row in data:
        city, country, lat, lon = row[0], row[1], row[2], row[3]
        overall, rent, groc, rest, trans = row[4], row[5], row[6], row[7], row[8]
        val = row[idx]
        color = _value_color(val, vmin, vmax)
        popup_html = _make_popup([
            ("City", f"{city}, {country}"),
            ("Overall Index", f"{overall:.1f}"),
            ("Rent Index", f"{rent:.1f}"),
            ("Groceries", f"{groc:.1f}"),
            ("Restaurants", f"{rest:.1f}"),
            ("Transport", f"{trans:.1f}"),
        ])
        folium.CircleMarker(
            location=[lat, lon], radius=max(5, val / 10),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{city}: {val:.1f}",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N cities to chart", 10, len(data), 25, key="col_topn")
    chart_data = data[:top_n]
    df_chart = pd.DataFrame(chart_data, columns=[
        "City", "Country", "Lat", "Lon", "Overall", "Rent", "Groceries", "Restaurant", "Transport"
    ])
    buf = _bar_chart(
        df_chart.head(top_n), "City", sort_by.split()[0] if sort_by == "Overall Index" else sort_by.split()[0],
        f"Top {top_n} Cities by {sort_by}", "City", sort_by,
        color="#06b6d4",
    )
    # Recalculate properly
    col_name_map = {
        "Overall Index": "Overall", "Rent Index": "Rent",
        "Groceries Index": "Groceries", "Restaurant Index": "Restaurant",
        "Transport Index": "Transport",
    }
    y_name = col_name_map[sort_by]
    buf = _bar_chart(df_chart.head(top_n), "City", y_name,
                     f"Top {top_n} Cities by {sort_by}", "City", sort_by)
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_all = pd.DataFrame(COST_OF_LIVING_DATA, columns=[
        "City", "Country", "Lat", "Lon", "Overall", "Rent", "Groceries", "Restaurant", "Transport"
    ])
    df_show = df_all.drop(columns=["Lat", "Lon"]).sort_values(y_name, ascending=False).reset_index(drop=True)
    df_show.index += 1
    st.dataframe(df_show, width="stretch")

    # -- Download --
    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "cost_of_living_index.csv", "text/csv", key="col_dl")


def _render_salary():
    """Mode 2: Average Salary by Country."""
    st.markdown("#### Average Monthly Salary by Country (USD)")
    st.caption("Curated average net monthly salary data combined with REST Countries API locations.")

    data_list = []
    for code, salary in SALARY_DATA.items():
        if code in COUNTRY_COORDS:
            lat, lon = COUNTRY_COORDS[code]
            data_list.append({"code": code, "salary_usd": salary, "lat": lat, "lon": lon})

    df = pd.DataFrame(data_list).sort_values("salary_usd", ascending=False).reset_index(drop=True)
    vals = df["salary_usd"].tolist()
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Highest", f"${df.iloc[0]['salary_usd']:,.0f}")
    c3.metric("Lowest", f"${df.iloc[-1]['salary_usd']:,.0f}")
    c4.metric("Median", f"${df['salary_usd'].median():,.0f}")

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        color = _value_color(row["salary_usd"], vmin, vmax, reverse=True)
        popup_html = _make_popup([
            ("Country", row["code"]),
            ("Avg. Salary", f"${row['salary_usd']:,.0f}/mo"),
        ])
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(4, row["salary_usd"] / 500),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['code']}: ${row['salary_usd']:,.0f}",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N countries", 10, len(df), 30, key="sal_topn")
    buf = _bar_chart(df.head(top_n), "code", "salary_usd",
                     f"Top {top_n} Countries by Avg. Salary", "Country", "USD/month")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_show = df.drop(columns=["lat", "lon"]).reset_index(drop=True)
    df_show.index += 1
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "avg_salary_by_country.csv", "text/csv", key="sal_dl")


def _render_real_estate():
    """Mode 3: Real Estate Prices per sqm."""
    st.markdown("#### Real Estate Prices (USD per sqm)")
    st.caption("Approximate property prices per square metre in city centres and outside centres.")

    view = st.radio("View", ["City Centre", "Outside Centre"], horizontal=True, key="re_view")
    price_col = 4 if view == "City Centre" else 5

    data = sorted(REAL_ESTATE_DATA, key=lambda x: x[price_col], reverse=True)
    vals = [r[price_col] for r in data]
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", len(data))
    c2.metric("Most Expensive", f"{data[0][0]}")
    c3.metric("Price", f"${data[0][price_col]:,.0f}/sqm")
    c4.metric("Cheapest", f"${data[-1][price_col]:,.0f}/sqm")

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for row in data:
        city, country, lat, lon = row[0], row[1], row[2], row[3]
        centre, outside = row[4], row[5]
        val = row[price_col]
        color = _value_color(val, vmin, vmax)
        popup_html = _make_popup([
            ("City", f"{city}, {country}"),
            ("Centre", f"${centre:,.0f}/sqm"),
            ("Outside", f"${outside:,.0f}/sqm"),
        ])
        folium.CircleMarker(
            location=[lat, lon], radius=max(4, val / 2500),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{city}: ${val:,.0f}/sqm",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N cities", 10, len(data), 25, key="re_topn")
    df_chart = pd.DataFrame(data[:top_n], columns=[
        "City", "Country", "Lat", "Lon", "Centre", "Outside"
    ])
    buf = _dual_bar_chart(df_chart, "City", "Centre", "Outside",
                          f"Top {top_n} Cities: Property Prices per sqm",
                          "City Centre", "Outside Centre")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_all = pd.DataFrame(REAL_ESTATE_DATA, columns=[
        "City", "Country", "Lat", "Lon", "Centre ($/sqm)", "Outside ($/sqm)"
    ])
    df_show = df_all.drop(columns=["Lat", "Lon"]).sort_values(
        "Centre ($/sqm)", ascending=False
    ).reset_index(drop=True)
    df_show.index += 1
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "real_estate_prices.csv", "text/csv", key="re_dl")


def _render_big_mac():
    """Mode 4: Big Mac Index."""
    st.markdown("#### Big Mac Index")
    st.caption(
        "The Big Mac Index compares burger prices worldwide as an informal PPP measure. "
        "Prices in USD. Implied PPP rate relative to the US dollar."
    )

    data_list = []
    for code, (price, ppp) in BIG_MAC_DATA.items():
        if code in COUNTRY_COORDS:
            lat, lon = COUNTRY_COORDS[code]
            overvalued = round((price / 5.69 - 1) * 100, 1)  # vs US price
            data_list.append({
                "code": code, "price_usd": price, "ppp_rate": ppp,
                "vs_usd_pct": overvalued, "lat": lat, "lon": lon,
            })

    df = pd.DataFrame(data_list).sort_values("price_usd", ascending=False).reset_index(drop=True)
    vals = df["price_usd"].tolist()
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Most Expensive", f"{df.iloc[0]['code']} (${df.iloc[0]['price_usd']:.2f})")
    c3.metric("Cheapest", f"{df.iloc[-1]['code']} (${df.iloc[-1]['price_usd']:.2f})")
    c4.metric("US Price", "$5.69")

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        color = _value_color(row["price_usd"], vmin, vmax)
        sign = "+" if row["vs_usd_pct"] > 0 else ""
        popup_html = _make_popup([
            ("Country", row["code"]),
            ("Big Mac Price", f"${row['price_usd']:.2f}"),
            ("vs USD", f"{sign}{row['vs_usd_pct']:.1f}%"),
            ("Implied PPP", f"{row['ppp_rate']:.2f}"),
        ])
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(4, row["price_usd"] * 2),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{row['code']}: ${row['price_usd']:.2f}",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    chart_mode = st.radio("Chart view", ["Price (USD)", "% vs US Dollar"], horizontal=True, key="bm_cv")
    if chart_mode == "Price (USD)":
        buf = _bar_chart(df, "code", "price_usd",
                         "Big Mac Prices Worldwide (USD)", "Country", "Price (USD)",
                         color="#f59e0b")
    else:
        df_sorted = df.sort_values("vs_usd_pct", ascending=False)
        buf = _bar_chart(df_sorted, "code", "vs_usd_pct",
                         "Big Mac Index: % Over/Under valued vs USD",
                         "Country", "% vs USD", color="#8b5cf6")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_show = df.drop(columns=["lat", "lon"]).reset_index(drop=True)
    df_show.index += 1
    df_show.columns = ["Country", "Price (USD)", "Implied PPP", "vs USD (%)", ]
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "big_mac_index.csv", "text/csv", key="bm_dl")


def _render_gdp():
    """Mode 5: GDP per Capita (World Bank API)."""
    st.markdown("#### GDP per Capita (World Bank, 2022)")
    st.caption("Data from the World Bank Open Data API. Values in current USD.")

    with st.spinner("Fetching GDP data from World Bank API..."):
        raw = fetch_gdp_per_capita()

    if not raw:
        st.error("No GDP data returned from the World Bank API.")
        return
    if isinstance(raw[0], dict) and "error" in raw[0]:
        st.error(f"API Error: {raw[0]['error']}")
        return

    df = pd.DataFrame(raw).sort_values("gdp_pc", ascending=False).reset_index(drop=True)
    vals = df["gdp_pc"].tolist()
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Highest", f"{df.iloc[0]['country']}")
    c3.metric("GDP/capita", f"${df.iloc[0]['gdp_pc']:,.0f}")
    c4.metric("Lowest", f"${df.iloc[-1]['gdp_pc']:,.0f}")

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        color = _value_color(row["gdp_pc"], vmin, vmax, reverse=True)
        popup_html = _make_popup([
            ("Country", row["country"]),
            ("GDP/capita", f"${row['gdp_pc']:,.0f}"),
        ])
        radius = max(3, min(18, row["gdp_pc"] / 5000))
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['country']}: ${row['gdp_pc']:,.0f}",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N countries", 10, len(df), 30, key="gdp_topn")
    buf = _bar_chart(df.head(top_n), "country", "gdp_pc",
                     f"Top {top_n} Countries by GDP per Capita",
                     "Country", "USD", color="#10b981")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_show = df.drop(columns=["lat", "lon"]).reset_index(drop=True)
    df_show.index += 1
    df_show.columns = ["Country", "Code", "GDP per Capita (USD)"]
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "gdp_per_capita.csv", "text/csv", key="gdp_dl")


def _render_min_wage():
    """Mode 6: Minimum Wage World Map."""
    st.markdown("#### Minimum Wage by Country (USD/month)")
    st.caption(
        "Statutory minimum wage converted to USD monthly equivalent. "
        "Countries marked $0 have no statutory minimum wage (often use sector-based agreements)."
    )

    show_zero = st.checkbox("Include countries with no statutory minimum", value=True, key="mw_zero")

    data_list = []
    for code, wage in MINIMUM_WAGE_DATA.items():
        if code in COUNTRY_COORDS:
            if not show_zero and wage == 0:
                continue
            lat, lon = COUNTRY_COORDS[code]
            data_list.append({"code": code, "wage_usd": wage, "lat": lat, "lon": lon})

    df = pd.DataFrame(data_list).sort_values("wage_usd", ascending=False).reset_index(drop=True)
    vals = [v for v in df["wage_usd"].tolist() if v > 0]
    vmin = min(vals) if vals else 0
    vmax = max(vals) if vals else 1

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    nonzero = df[df["wage_usd"] > 0]
    c2.metric("Highest", f"{nonzero.iloc[0]['code']} (${nonzero.iloc[0]['wage_usd']:,.0f})" if len(nonzero) > 0 else "N/A")
    c3.metric("Lowest (>0)", f"${nonzero.iloc[-1]['wage_usd']:,.0f}" if len(nonzero) > 0 else "N/A")
    no_min = df[df["wage_usd"] == 0]
    c4.metric("No Statutory Min", len(no_min))

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        if row["wage_usd"] == 0:
            color = "#5a6580"
            label = "No statutory minimum"
        else:
            color = _value_color(row["wage_usd"], vmin, vmax, reverse=True)
            label = f"${row['wage_usd']:,.0f}/mo"
        popup_html = _make_popup([
            ("Country", row["code"]),
            ("Minimum Wage", label),
        ])
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(4, row["wage_usd"] / 200) if row["wage_usd"] > 0 else 5,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['code']}: {label}",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart (exclude zeros) --
    st.markdown("---")
    df_nonzero = df[df["wage_usd"] > 0].reset_index(drop=True)
    top_n = st.slider("Top N countries", 10, min(len(df_nonzero), 80), 30, key="mw_topn")
    buf = _bar_chart(df_nonzero.head(top_n), "code", "wage_usd",
                     f"Top {top_n} Minimum Wages (USD/month)",
                     "Country", "USD/month", color="#ec4899")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_show = df.drop(columns=["lat", "lon"]).reset_index(drop=True)
    df_show.index += 1
    df_show.columns = ["Country", "Min Wage (USD/mo)"]
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "minimum_wage.csv", "text/csv", key="mw_dl")


def _render_tax():
    """Mode 7: Tax Rates by Country."""
    st.markdown("#### Tax Rates by Country")
    st.caption("Top marginal personal income tax rate and standard VAT / sales tax rate.")

    color_by = st.radio("Color by", ["Income Tax", "VAT / Sales Tax"], horizontal=True, key="tax_color")

    data_list = []
    for code, (income, vat) in TAX_DATA.items():
        if code in COUNTRY_COORDS:
            lat, lon = COUNTRY_COORDS[code]
            data_list.append({
                "code": code, "income_tax": income, "vat": vat,
                "lat": lat, "lon": lon,
            })

    df = pd.DataFrame(data_list)
    sort_col = "income_tax" if color_by == "Income Tax" else "vat"
    df = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
    vals = df[sort_col].tolist()
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Highest Income Tax", f"{df.sort_values('income_tax', ascending=False).iloc[0]['code']} ({df.sort_values('income_tax', ascending=False).iloc[0]['income_tax']}%)")
    c3.metric("Highest VAT", f"{df.sort_values('vat', ascending=False).iloc[0]['code']} ({df.sort_values('vat', ascending=False).iloc[0]['vat']}%)")
    zero_tax = df[df["income_tax"] == 0]
    c4.metric("0% Income Tax", len(zero_tax))

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        val = row[sort_col]
        color = _value_color(val, vmin, vmax)
        popup_html = _make_popup([
            ("Country", row["code"]),
            ("Top Income Tax", f"{row['income_tax']}%"),
            ("VAT / Sales Tax", f"{row['vat']}%"),
            ("Total Top Burden", f"{row['income_tax'] + row['vat']}%"),
        ])
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(4, val / 4),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{row['code']}: {val}%",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N countries", 10, len(df), 30, key="tax_topn")
    df_top = df.head(top_n)
    buf = _dual_bar_chart(df_top, "code", "income_tax", "vat",
                          f"Top {top_n} Countries: Tax Rates",
                          "Income Tax %", "VAT %",
                          color1="#ef4444", color2="#f59e0b")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_show = df.drop(columns=["lat", "lon"]).reset_index(drop=True)
    df_show.index += 1
    df_show.columns = ["Country", "Income Tax (%)", "VAT (%)", ]
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "tax_rates.csv", "text/csv", key="tax_dl")


def _render_healthcare():
    """Mode 8: Healthcare Cost per Capita."""
    st.markdown("#### Healthcare Spending per Capita (USD)")
    st.caption("Total health expenditure per capita in current USD (latest available data).")

    data_list = []
    for code, spend in HEALTHCARE_DATA.items():
        if code in COUNTRY_COORDS:
            lat, lon = COUNTRY_COORDS[code]
            data_list.append({"code": code, "spend_usd": spend, "lat": lat, "lon": lon})

    df = pd.DataFrame(data_list).sort_values("spend_usd", ascending=False).reset_index(drop=True)
    vals = df["spend_usd"].tolist()
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Highest", f"{df.iloc[0]['code']} (${df.iloc[0]['spend_usd']:,.0f})")
    c3.metric("Lowest", f"${df.iloc[-1]['spend_usd']:,.0f}")
    c4.metric("Median", f"${df['spend_usd'].median():,.0f}")

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        color = _value_color(row["spend_usd"], vmin, vmax, reverse=True)
        popup_html = _make_popup([
            ("Country", row["code"]),
            ("Health Spend", f"${row['spend_usd']:,.0f}/capita"),
        ])
        radius = max(3, min(18, row["spend_usd"] / 800))
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['code']}: ${row['spend_usd']:,.0f}",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N countries", 10, len(df), 30, key="hc_topn")
    buf = _bar_chart(df.head(top_n), "code", "spend_usd",
                     f"Top {top_n} Healthcare Spending (USD/capita)",
                     "Country", "USD/capita", color="#ef4444")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_show = df.drop(columns=["lat", "lon"]).reset_index(drop=True)
    df_show.index += 1
    df_show.columns = ["Country", "Health Spend (USD/capita)"]
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "healthcare_spending.csv", "text/csv", key="hc_dl")


def _render_rent_afford():
    """Mode 9: Rent Affordability (rent-to-income ratio)."""
    st.markdown("#### Rent Affordability Index")
    st.caption(
        "Average rent-to-income ratio (%). Higher means less affordable. "
        "A ratio above 40% is generally considered unaffordable."
    )

    data = sorted(RENT_AFFORD_DATA, key=lambda x: x[4], reverse=True)
    vals = [r[4] for r in data]
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", len(data))
    c2.metric("Least Affordable", data[0][0])
    c3.metric("Ratio", f"{data[0][4]:.1f}%")
    affordable = [r for r in data if r[4] <= 30]
    c4.metric("Affordable (<30%)", len(affordable))

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for row in data:
        city, country, lat, lon, ratio = row
        color = _value_color(ratio, vmin, vmax)
        if ratio > 50:
            level = "Severely Unaffordable"
        elif ratio > 40:
            level = "Unaffordable"
        elif ratio > 30:
            level = "Stretched"
        else:
            level = "Affordable"
        popup_html = _make_popup([
            ("City", f"{city}, {country}"),
            ("Rent/Income", f"{ratio:.1f}%"),
            ("Level", level),
        ])
        folium.CircleMarker(
            location=[lat, lon], radius=max(4, ratio / 5),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{city}: {ratio:.1f}%",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N cities", 10, len(data), 25, key="ra_topn")
    df_chart = pd.DataFrame(data[:top_n], columns=["City", "Country", "Lat", "Lon", "Ratio"])
    buf = _bar_chart(df_chart, "City", "Ratio",
                     f"Top {top_n} Least Affordable Cities (Rent/Income %)",
                     "City", "Rent-to-Income %", color="#f97316")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_all = pd.DataFrame(RENT_AFFORD_DATA, columns=["City", "Country", "Lat", "Lon", "Rent/Income (%)"])
    df_show = df_all.drop(columns=["Lat", "Lon"]).sort_values(
        "Rent/Income (%)", ascending=False
    ).reset_index(drop=True)
    df_show.index += 1
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "rent_affordability.csv", "text/csv", key="ra_dl")


def _render_nomad():
    """Mode 10: Digital Nomad Index."""
    st.markdown("#### Digital Nomad Index")
    st.caption(
        "Composite score (0-100) based on internet speed, coworking costs, "
        "visa accessibility, safety, and overall livability for remote workers."
    )

    sort_by = st.selectbox("Sort by", [
        "Nomad Score", "Internet Speed", "Coworking Cost", "Visa Ease", "Safety"
    ], key="nm_sort")

    col_map = {
        "Nomad Score": 8, "Internet Speed": 4,
        "Coworking Cost": 5, "Visa Ease": 6, "Safety": 7,
    }
    idx = col_map[sort_by]
    reverse = sort_by != "Coworking Cost"  # lower cowork cost is better

    data = sorted(NOMAD_DATA, key=lambda x: x[idx], reverse=reverse)
    vals = [r[idx] for r in data]
    vmin, vmax = min(vals), max(vals)

    # -- Stats --
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", len(data))
    c2.metric("Top Nomad City", data[0][0])
    c3.metric("Score", f"{data[0][8]}/100")
    avg_cost = sum(r[5] for r in data) / len(data)
    c4.metric("Avg Cowork Cost", f"${avg_cost:.0f}/mo")

    # -- Map --
    st.markdown("---")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for row in data:
        city, country, lat, lon = row[0], row[1], row[2], row[3]
        inet, cowork, visa, safety, score = row[4], row[5], row[6], row[7], row[8]
        val = row[idx]
        color = _value_color(val, vmin, vmax, reverse=(not reverse))
        popup_html = _make_popup([
            ("City", f"{city}, {country}"),
            ("Nomad Score", f"{score}/100"),
            ("Internet", f"{inet} Mbps"),
            ("Coworking", f"${cowork}/mo"),
            ("Visa Ease", f"{visa}/10"),
            ("Safety", f"{safety}/10"),
        ])
        folium.CircleMarker(
            location=[lat, lon], radius=max(4, score / 10),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{city}: Score {score}",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Radar-style comparison --
    st.markdown("---")
    st.markdown("##### Compare Cities")
    city_names = [r[0] for r in NOMAD_DATA]
    selected = st.multiselect("Select cities to compare", city_names,
                              default=city_names[:5], key="nm_compare")
    if selected:
        compare_data = [r for r in NOMAD_DATA if r[0] in selected]
        df_compare = pd.DataFrame(compare_data, columns=[
            "City", "Country", "Lat", "Lon", "Internet (Mbps)",
            "Cowork ($/mo)", "Visa Ease", "Safety", "Score"
        ]).drop(columns=["Lat", "Lon"])
        st.dataframe(df_compare, width="stretch")

    # -- Chart --
    st.markdown("---")
    top_n = st.slider("Top N cities", 10, len(data), 20, key="nm_topn")
    df_chart = pd.DataFrame(data[:top_n], columns=[
        "City", "Country", "Lat", "Lon", "Internet", "Cowork", "Visa", "Safety", "Score"
    ])
    buf = _bar_chart(df_chart, "City", "Score",
                     f"Top {top_n} Digital Nomad Cities",
                     "City", "Score (0-100)", color="#8b5cf6")
    st.image(buf, width=900)

    # -- Table --
    st.markdown("---")
    df_all = pd.DataFrame(NOMAD_DATA, columns=[
        "City", "Country", "Lat", "Lon", "Internet (Mbps)",
        "Cowork ($/mo)", "Visa Ease (/10)", "Safety (/10)", "Nomad Score"
    ])
    df_show = df_all.drop(columns=["Lat", "Lon"]).sort_values(
        "Nomad Score", ascending=False
    ).reset_index(drop=True)
    df_show.index += 1
    st.dataframe(df_show, width="stretch")

    csv = df_show.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV", csv, "digital_nomad_index.csv", "text/csv", key="nm_dl")


# ═══════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════
def render_cost_living_maps_tab():
    """Main render function for the Cost of Living & Economy Maps tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header amber"><h4>💰 Cost of Living & Economy Maps</h4>'
        '<p>Living costs, salaries, real estate prices &amp; economic indicators worldwide</p></div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.radio(
        "Select Map Mode",
        [
            "Cost of Living Index",
            "Average Salary by Country",
            "Real Estate Prices",
            "Big Mac Index",
            "GDP per Capita",
            "Minimum Wage World",
            "Tax Rates by Country",
            "Healthcare Cost",
            "Rent Affordability",
            "Digital Nomad Index",
        ],
        key="clm_mode",
        horizontal=False,
    )

    st.markdown("---")

    # ── Dispatch ──
    if mode == "Cost of Living Index":
        _render_cost_of_living()
    elif mode == "Average Salary by Country":
        _render_salary()
    elif mode == "Real Estate Prices":
        _render_real_estate()
    elif mode == "Big Mac Index":
        _render_big_mac()
    elif mode == "GDP per Capita":
        _render_gdp()
    elif mode == "Minimum Wage World":
        _render_min_wage()
    elif mode == "Tax Rates by Country":
        _render_tax()
    elif mode == "Healthcare Cost":
        _render_healthcare()
    elif mode == "Rent Affordability":
        _render_rent_afford()
    elif mode == "Digital Nomad Index":
        _render_nomad()

    # ── Footer ──
    st.markdown("---")
    st.caption(
        "Data sources: World Bank Open Data API, curated datasets based on Numbeo, "
        "The Economist Big Mac Index, OECD, WHO, and various national statistics offices. "
        "Values are approximate and may not reflect real-time changes."
    )
