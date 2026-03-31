# -*- coding: utf-8 -*-
"""
Military & Geopolitical Maps module for TerraScout AI.
Provides 10 thematic map types covering military bases, alliances,
nuclear arsenals, disputed territories, maritime boundaries, border
barriers, arms trade, conflict zones, and demilitarized zones.
All data is either hardcoded or sourced from free APIs (Overpass).
"""

import io
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# =====================================================================
# CONSTANTS
# =====================================================================
MAP_TYPES = [
    "Military Bases",
    "NATO vs Non-NATO",
    "Nuclear Powers",
    "Disputed Territories",
    "Maritime Boundaries",
    "Border Walls & Fences",
    "Military Alliances Timeline",
    "Arms Trade Routes",
    "Conflict Zones",
    "Demilitarized Zones",
]

MILITARY_BASE_REGIONS = {
    "Europe (Central)": {"lat": 50.0, "lon": 10.0, "radius": 500000},
    "Europe (Eastern)": {"lat": 50.0, "lon": 25.0, "radius": 500000},
    "Middle East": {"lat": 30.0, "lon": 45.0, "radius": 600000},
    "East Asia": {"lat": 35.0, "lon": 127.0, "radius": 500000},
    "South Asia": {"lat": 25.0, "lon": 75.0, "radius": 600000},
    "North Africa": {"lat": 30.0, "lon": 10.0, "radius": 600000},
    "Southeast Asia": {"lat": 10.0, "lon": 110.0, "radius": 600000},
    "North America (East)": {"lat": 38.0, "lon": -78.0, "radius": 500000},
    "North America (West)": {"lat": 37.0, "lon": -119.0, "radius": 500000},
    "Central America & Caribbean": {"lat": 18.0, "lon": -78.0, "radius": 500000},
    "South America (North)": {"lat": 0.0, "lon": -60.0, "radius": 600000},
    "Horn of Africa": {"lat": 8.0, "lon": 45.0, "radius": 500000},
    "Central Asia": {"lat": 42.0, "lon": 65.0, "radius": 600000},
    "Australia & Oceania": {"lat": -25.0, "lon": 135.0, "radius": 800000},
}

# =====================================================================
# 2. NATO vs NON-NATO DATA
# =====================================================================
NATO_MEMBERS = [
    {"country": "United States", "code": "US", "year": 1949, "lat": 38.9, "lon": -77.0},
    {"country": "United Kingdom", "code": "GB", "year": 1949, "lat": 51.5, "lon": -0.1},
    {"country": "France", "code": "FR", "year": 1949, "lat": 48.9, "lon": 2.3},
    {"country": "Canada", "code": "CA", "year": 1949, "lat": 45.4, "lon": -75.7},
    {"country": "Belgium", "code": "BE", "year": 1949, "lat": 50.8, "lon": 4.4},
    {"country": "Netherlands", "code": "NL", "year": 1949, "lat": 52.4, "lon": 4.9},
    {"country": "Luxembourg", "code": "LU", "year": 1949, "lat": 49.6, "lon": 6.1},
    {"country": "Norway", "code": "NO", "year": 1949, "lat": 59.9, "lon": 10.7},
    {"country": "Denmark", "code": "DK", "year": 1949, "lat": 55.7, "lon": 12.6},
    {"country": "Iceland", "code": "IS", "year": 1949, "lat": 64.1, "lon": -21.9},
    {"country": "Italy", "code": "IT", "year": 1949, "lat": 41.9, "lon": 12.5},
    {"country": "Portugal", "code": "PT", "year": 1949, "lat": 38.7, "lon": -9.1},
    {"country": "Greece", "code": "GR", "year": 1952, "lat": 37.98, "lon": 23.7},
    {"country": "Turkey", "code": "TR", "year": 1952, "lat": 39.93, "lon": 32.9},
    {"country": "Germany", "code": "DE", "year": 1955, "lat": 52.5, "lon": 13.4},
    {"country": "Spain", "code": "ES", "year": 1982, "lat": 40.4, "lon": -3.7},
    {"country": "Czech Republic", "code": "CZ", "year": 1999, "lat": 50.1, "lon": 14.4},
    {"country": "Hungary", "code": "HU", "year": 1999, "lat": 47.5, "lon": 19.0},
    {"country": "Poland", "code": "PL", "year": 1999, "lat": 52.2, "lon": 21.0},
    {"country": "Bulgaria", "code": "BG", "year": 2004, "lat": 42.7, "lon": 23.3},
    {"country": "Estonia", "code": "EE", "year": 2004, "lat": 59.4, "lon": 24.7},
    {"country": "Latvia", "code": "LV", "year": 2004, "lat": 56.9, "lon": 24.1},
    {"country": "Lithuania", "code": "LT", "year": 2004, "lat": 54.7, "lon": 25.3},
    {"country": "Romania", "code": "RO", "year": 2004, "lat": 44.4, "lon": 26.1},
    {"country": "Slovakia", "code": "SK", "year": 2004, "lat": 48.1, "lon": 17.1},
    {"country": "Slovenia", "code": "SI", "year": 2004, "lat": 46.1, "lon": 14.5},
    {"country": "Albania", "code": "AL", "year": 2009, "lat": 41.3, "lon": 19.8},
    {"country": "Croatia", "code": "HR", "year": 2009, "lat": 45.8, "lon": 16.0},
    {"country": "Montenegro", "code": "ME", "year": 2017, "lat": 42.4, "lon": 19.3},
    {"country": "North Macedonia", "code": "MK", "year": 2020, "lat": 42.0, "lon": 21.4},
    {"country": "Finland", "code": "FI", "year": 2023, "lat": 60.2, "lon": 24.9},
    {"country": "Sweden", "code": "SE", "year": 2024, "lat": 59.3, "lon": 18.1},
]

CSTO_MEMBERS = [
    {"country": "Russia", "code": "RU", "year": 1992, "lat": 55.8, "lon": 37.6},
    {"country": "Belarus", "code": "BY", "year": 1992, "lat": 53.9, "lon": 27.6},
    {"country": "Armenia", "code": "AM", "year": 1992, "lat": 40.2, "lon": 44.5},
    {"country": "Kazakhstan", "code": "KZ", "year": 1992, "lat": 51.2, "lon": 71.4},
    {"country": "Kyrgyzstan", "code": "KG", "year": 1992, "lat": 42.9, "lon": 74.6},
    {"country": "Tajikistan", "code": "TJ", "year": 1992, "lat": 38.6, "lon": 68.8},
]

# =====================================================================
# 3. NUCLEAR POWERS DATA
# =====================================================================
NUCLEAR_POWERS = [
    {"country": "United States", "lat": 38.9, "lon": -77.0, "warheads": 5244,
     "first_test": "1945 (Trinity)", "status": "NPT Nuclear State"},
    {"country": "Russia", "lat": 55.8, "lon": 37.6, "warheads": 6257,
     "first_test": "1949 (Joe-1)", "status": "NPT Nuclear State"},
    {"country": "United Kingdom", "lat": 51.5, "lon": -0.1, "warheads": 225,
     "first_test": "1952 (Hurricane)", "status": "NPT Nuclear State"},
    {"country": "France", "lat": 48.9, "lon": 2.3, "warheads": 290,
     "first_test": "1960 (Gerboise Bleue)", "status": "NPT Nuclear State"},
    {"country": "China", "lat": 39.9, "lon": 116.4, "warheads": 500,
     "first_test": "1964 (596)", "status": "NPT Nuclear State"},
    {"country": "India", "lat": 28.6, "lon": 77.2, "warheads": 172,
     "first_test": "1974 (Smiling Buddha)", "status": "Non-NPT"},
    {"country": "Pakistan", "lat": 33.7, "lon": 73.0, "warheads": 170,
     "first_test": "1998 (Chagai-I)", "status": "Non-NPT"},
    {"country": "Israel", "lat": 31.8, "lon": 35.2, "warheads": 90,
     "first_test": "Undeclared (~1966)", "status": "Undeclared"},
    {"country": "North Korea", "lat": 39.0, "lon": 125.8, "warheads": 50,
     "first_test": "2006", "status": "Withdrew NPT 2003"},
]

# =====================================================================
# 4. DISPUTED TERRITORIES DATA
# =====================================================================
DISPUTED_TERRITORIES = [
    {"name": "Kashmir", "claimants": "India, Pakistan, China",
     "status": "Divided / Line of Control",
     "polygon": [[32.5, 73.5], [35.5, 74.0], [37.0, 76.0], [36.5, 78.5],
                  [35.0, 79.0], [33.0, 78.0], [32.0, 76.0], [32.5, 73.5]],
     "color": "#ef4444"},
    {"name": "Crimea", "claimants": "Ukraine, Russia",
     "status": "Annexed by Russia (2014), internationally disputed",
     "polygon": [[44.4, 33.0], [45.5, 33.5], [46.2, 34.0], [45.8, 35.5],
                  [45.0, 36.5], [44.4, 36.0], [44.3, 34.5], [44.4, 33.0]],
     "color": "#f59e0b"},
    {"name": "Western Sahara", "claimants": "Morocco, Sahrawi Arab Democratic Republic",
     "status": "Partially occupied by Morocco",
     "polygon": [[21.3, -17.1], [27.7, -13.2], [27.7, -8.7], [25.0, -12.0],
                  [23.0, -13.0], [21.3, -17.1]],
     "color": "#10b981"},
    {"name": "South China Sea (Spratly Islands)", "claimants": "China, Vietnam, Philippines, Malaysia, Brunei, Taiwan",
     "status": "Multiple overlapping claims",
     "polygon": [[5.0, 109.0], [12.0, 109.0], [12.0, 118.0], [5.0, 118.0], [5.0, 109.0]],
     "color": "#3b82f6"},
    {"name": "Golan Heights", "claimants": "Syria, Israel",
     "status": "Occupied by Israel since 1967",
     "polygon": [[32.7, 35.7], [33.3, 35.7], [33.3, 36.1], [32.7, 36.1], [32.7, 35.7]],
     "color": "#8b5cf6"},
    {"name": "Arunachal Pradesh / South Tibet", "claimants": "India, China",
     "status": "Administered by India, claimed by China",
     "polygon": [[26.5, 91.5], [29.0, 91.5], [29.0, 97.5], [26.5, 97.5], [26.5, 91.5]],
     "color": "#ec4899"},
    {"name": "Aksai Chin", "claimants": "India, China",
     "status": "Administered by China, claimed by India",
     "polygon": [[34.0, 77.5], [36.0, 77.5], [36.0, 80.5], [34.0, 80.5], [34.0, 77.5]],
     "color": "#f97316"},
    {"name": "Taiwan Strait", "claimants": "People's Republic of China, Republic of China (Taiwan)",
     "status": "Self-governed by Taiwan, claimed by PRC",
     "polygon": [[21.9, 119.5], [25.3, 119.5], [25.3, 122.5], [21.9, 122.5], [21.9, 119.5]],
     "color": "#06b6d4"},
    {"name": "Northern Cyprus", "claimants": "Cyprus, Turkey/TRNC",
     "status": "Occupied by Turkey since 1974",
     "polygon": [[35.1, 32.7], [35.7, 32.7], [35.7, 34.6], [35.1, 34.6], [35.1, 32.7]],
     "color": "#84cc16"},
    {"name": "Nagorno-Karabakh", "claimants": "Azerbaijan, Armenia (historic)",
     "status": "Recaptured by Azerbaijan (2023)",
     "polygon": [[39.0, 46.3], [40.2, 46.3], [40.2, 47.3], [39.0, 47.3], [39.0, 46.3]],
     "color": "#a855f7"},
    {"name": "Transnistria", "claimants": "Moldova, Transnistria (de facto)",
     "status": "Breakaway region since 1990",
     "polygon": [[46.4, 28.5], [48.3, 28.5], [48.3, 30.1], [46.4, 30.1], [46.4, 28.5]],
     "color": "#e11d48"},
    {"name": "Abkhazia", "claimants": "Georgia, Abkhazia (de facto)",
     "status": "Breakaway region, recognized by Russia",
     "polygon": [[42.5, 40.0], [43.5, 40.0], [43.5, 42.0], [42.5, 42.0], [42.5, 40.0]],
     "color": "#0ea5e9"},
    {"name": "South Ossetia", "claimants": "Georgia, South Ossetia (de facto)",
     "status": "Breakaway region, recognized by Russia",
     "polygon": [[42.0, 43.5], [42.6, 43.5], [42.6, 44.5], [42.0, 44.5], [42.0, 43.5]],
     "color": "#14b8a6"},
    {"name": "Falkland Islands / Malvinas", "claimants": "United Kingdom, Argentina",
     "status": "British Overseas Territory, claimed by Argentina",
     "polygon": [[-52.5, -61.5], [-51.0, -61.5], [-51.0, -57.5], [-52.5, -57.5], [-52.5, -61.5]],
     "color": "#f472b6"},
    {"name": "Kuril Islands (Southern)", "claimants": "Russia, Japan",
     "status": "Administered by Russia, claimed by Japan",
     "polygon": [[43.5, 145.0], [45.5, 145.0], [45.5, 149.0], [43.5, 149.0], [43.5, 145.0]],
     "color": "#facc15"},
    {"name": "Paracel Islands", "claimants": "China, Vietnam, Taiwan",
     "status": "Controlled by China since 1974",
     "polygon": [[15.5, 111.0], [17.0, 111.0], [17.0, 113.0], [15.5, 113.0], [15.5, 111.0]],
     "color": "#22d3ee"},
    {"name": "Senkaku / Diaoyu Islands", "claimants": "Japan, China, Taiwan",
     "status": "Administered by Japan, claimed by China and Taiwan",
     "polygon": [[25.5, 123.0], [26.0, 123.0], [26.0, 124.5], [25.5, 124.5], [25.5, 123.0]],
     "color": "#fb923c"},
    {"name": "Dokdo / Takeshima", "claimants": "South Korea, Japan",
     "status": "Administered by South Korea, claimed by Japan",
     "polygon": [[37.1, 131.7], [37.3, 131.7], [37.3, 132.0], [37.1, 132.0], [37.1, 131.7]],
     "color": "#c084fc"},
    {"name": "Gibraltar", "claimants": "United Kingdom, Spain",
     "status": "British Overseas Territory",
     "polygon": [[36.1, -5.4], [36.2, -5.4], [36.2, -5.3], [36.1, -5.3], [36.1, -5.4]],
     "color": "#4ade80"},
    {"name": "Ceuta & Melilla", "claimants": "Spain, Morocco",
     "status": "Spanish autonomous cities in North Africa",
     "polygon": [[35.85, -5.35], [35.92, -5.35], [35.92, -5.25], [35.85, -5.25], [35.85, -5.35]],
     "color": "#818cf8"},
    {"name": "Somaliland", "claimants": "Somaliland (de facto), Somalia",
     "status": "Self-declared independent, unrecognized",
     "polygon": [[8.0, 43.0], [11.5, 43.0], [11.5, 49.0], [8.0, 49.0], [8.0, 43.0]],
     "color": "#fb7185"},
    {"name": "Hala'ib Triangle", "claimants": "Egypt, Sudan",
     "status": "Administered by Egypt, claimed by Sudan",
     "polygon": [[21.0, 35.0], [22.2, 35.0], [22.2, 37.0], [21.0, 37.0], [21.0, 35.0]],
     "color": "#a3e635"},
    {"name": "Ilemi Triangle", "claimants": "Kenya, South Sudan, Ethiopia",
     "status": "Administered by Kenya",
     "polygon": [[3.5, 35.5], [5.5, 35.5], [5.5, 36.5], [3.5, 36.5], [3.5, 35.5]],
     "color": "#2dd4bf"},
    {"name": "Essequibo", "claimants": "Venezuela, Guyana",
     "status": "Claimed by Venezuela, administered by Guyana",
     "polygon": [[1.0, -61.0], [8.5, -61.0], [8.5, -57.0], [1.0, -57.0], [1.0, -61.0]],
     "color": "#fbbf24"},
    {"name": "Scarborough Shoal", "claimants": "China, Philippines",
     "status": "Contested, controlled by China since 2012",
     "polygon": [[15.0, 117.5], [15.3, 117.5], [15.3, 117.9], [15.0, 117.9], [15.0, 117.5]],
     "color": "#f87171"},
    {"name": "Donbas (Donetsk & Luhansk)", "claimants": "Ukraine, Russia",
     "status": "Russian-occupied since 2022 invasion",
     "polygon": [[47.5, 37.0], [49.5, 37.0], [49.5, 40.0], [47.5, 40.0], [47.5, 37.0]],
     "color": "#e879f9"},
    {"name": "Zaporizhzhia & Kherson Oblasts", "claimants": "Ukraine, Russia",
     "status": "Partially occupied by Russia since 2022",
     "polygon": [[46.0, 33.0], [48.0, 33.0], [48.0, 36.5], [46.0, 36.5], [46.0, 33.0]],
     "color": "#34d399"},
    {"name": "Jammu (Azad Kashmir)", "claimants": "Pakistan, India",
     "status": "Administered by Pakistan, claimed by India",
     "polygon": [[33.0, 73.0], [35.0, 73.0], [35.0, 75.0], [33.0, 75.0], [33.0, 73.0]],
     "color": "#60a5fa"},
    {"name": "Bir Tawil", "claimants": "Unclaimed (Egypt/Sudan border)",
     "status": "Terra nullius - claimed by neither state",
     "polygon": [[21.3, 33.7], [22.0, 33.7], [22.0, 34.1], [21.3, 34.1], [21.3, 33.7]],
     "color": "#d946ef"},
    {"name": "Hans Island", "claimants": "Canada, Denmark (resolved 2022)",
     "status": "Divided between Canada and Denmark (2022)",
     "polygon": [[80.8, -66.5], [80.85, -66.5], [80.85, -66.3], [80.8, -66.3], [80.8, -66.5]],
     "color": "#38bdf8"},
    {"name": "Shebaa Farms", "claimants": "Lebanon, Syria, Israel",
     "status": "Occupied by Israel, claimed by Lebanon",
     "polygon": [[33.25, 35.7], [33.35, 35.7], [33.35, 35.85], [33.25, 35.85], [33.25, 35.7]],
     "color": "#fca5a5"},
]

# =====================================================================
# 5. MARITIME BOUNDARIES DATA
# =====================================================================
MARITIME_ZONES = [
    {"name": "South China Sea Nine-Dash Line",
     "claimant": "China (disputed by multiple nations)",
     "status": "Rejected by 2016 PCA ruling",
     "color": "#ef4444",
     "coords": [[25.0, 119.5], [21.0, 118.0], [15.0, 117.0], [7.0, 112.0],
                 [3.0, 108.0], [5.0, 105.0], [8.0, 106.0], [15.0, 109.0],
                 [18.0, 110.0], [21.0, 112.0], [23.0, 116.0], [25.0, 119.5]]},
    {"name": "Eastern Mediterranean EEZ Disputes",
     "claimant": "Turkey vs Greece/Cyprus",
     "status": "Active dispute over continental shelf",
     "color": "#3b82f6",
     "coords": [[34.0, 26.0], [36.0, 27.0], [38.0, 28.0], [37.0, 30.0],
                 [35.0, 33.0], [34.0, 34.0], [33.0, 32.0], [33.5, 29.0],
                 [34.0, 26.0]]},
    {"name": "Caspian Sea Division",
     "claimant": "Russia, Iran, Kazakhstan, Turkmenistan, Azerbaijan",
     "status": "Resolved by 2018 Convention",
     "color": "#10b981",
     "coords": [[37.0, 49.0], [38.5, 49.5], [40.0, 50.0], [42.0, 51.0],
                 [44.0, 51.5], [46.5, 51.0], [47.0, 52.5], [44.5, 53.0],
                 [42.0, 53.5], [40.0, 53.0], [38.0, 52.0], [37.0, 51.0],
                 [37.0, 49.0]]},
    {"name": "Arctic Claims (Northern Sea Route)",
     "claimant": "Russia (disputed by US, Canada, Norway)",
     "status": "Overlapping continental shelf claims",
     "color": "#f59e0b",
     "coords": [[70.0, 30.0], [75.0, 50.0], [78.0, 80.0], [77.0, 110.0],
                 [75.0, 140.0], [72.0, 170.0], [70.0, 180.0], [70.0, 170.0],
                 [68.0, 140.0], [68.0, 110.0], [68.0, 80.0], [68.0, 50.0],
                 [70.0, 30.0]]},
    {"name": "Persian Gulf Maritime Boundary",
     "claimant": "Iran vs Arab states",
     "status": "Multiple bilateral agreements, some unresolved",
     "color": "#8b5cf6",
     "coords": [[26.0, 50.0], [27.0, 51.0], [28.0, 51.5], [29.0, 50.5],
                 [30.0, 49.0], [30.5, 48.0], [29.5, 48.5], [28.0, 49.5],
                 [26.5, 49.0], [26.0, 50.0]]},
    {"name": "East China Sea EEZ Overlap",
     "claimant": "China vs Japan",
     "status": "Overlapping EEZ claims around median line",
     "color": "#ec4899",
     "coords": [[25.0, 123.0], [27.0, 124.0], [30.0, 125.5], [33.0, 126.0],
                 [33.0, 128.0], [30.0, 127.0], [27.0, 126.0], [25.0, 125.0],
                 [25.0, 123.0]]},
    {"name": "Aegean Sea Continental Shelf",
     "claimant": "Greece vs Turkey",
     "status": "Unresolved since 1970s",
     "color": "#14b8a6",
     "coords": [[36.0, 25.0], [38.0, 25.5], [40.0, 25.0], [40.5, 26.5],
                 [39.0, 27.5], [37.0, 27.0], [36.0, 26.5], [36.0, 25.0]]},
    {"name": "Gulf of Guinea Maritime Boundaries",
     "claimant": "Nigeria, Cameroon, Equatorial Guinea, Gabon",
     "status": "Partially resolved by ICJ rulings",
     "color": "#f97316",
     "coords": [[0.0, 5.0], [2.0, 6.0], [4.0, 7.0], [5.0, 5.0],
                 [4.0, 3.0], [2.0, 4.0], [0.0, 5.0]]},
    {"name": "Bay of Bengal Maritime Zone",
     "claimant": "Bangladesh, India, Myanmar",
     "status": "Partially resolved by ITLOS 2012",
     "color": "#06b6d4",
     "coords": [[15.0, 85.0], [18.0, 87.0], [20.0, 89.0], [21.5, 91.0],
                 [19.0, 93.0], [16.0, 92.0], [13.0, 88.0], [15.0, 85.0]]},
    {"name": "Black Sea EEZ (Romania-Ukraine)",
     "claimant": "Romania, Ukraine",
     "status": "Resolved by ICJ 2009 ruling around Snake Island",
     "color": "#84cc16",
     "coords": [[43.5, 29.0], [45.0, 30.0], [46.0, 31.5], [45.5, 33.0],
                 [44.0, 32.0], [43.0, 30.5], [43.5, 29.0]]},
]

# =====================================================================
# 6. BORDER WALLS & FENCES DATA
# =====================================================================
BORDER_WALLS = [
    {"name": "US-Mexico Border Wall",
     "countries": "United States / Mexico",
     "length_km": 1130, "year_start": 1994, "year_latest": 2021,
     "status": "Partial (approx 1130 km of 3145 km border)",
     "color": "#ef4444",
     "coords": [[32.55, -117.0], [32.2, -112.0], [31.4, -109.0],
                 [31.8, -106.4], [29.8, -104.0], [26.0, -97.5]]},
    {"name": "Israel-West Bank Barrier",
     "countries": "Israel / West Bank (Palestine)",
     "length_km": 708, "year_start": 2002, "year_latest": 2017,
     "status": "Mostly complete, declared illegal by ICJ (2004)",
     "color": "#3b82f6",
     "coords": [[31.3, 34.3], [31.5, 34.9], [32.0, 35.0], [32.4, 35.1],
                 [32.6, 35.3], [32.5, 35.5]]},
    {"name": "India-Bangladesh Border Fence",
     "countries": "India / Bangladesh",
     "length_km": 3200, "year_start": 1989, "year_latest": 2020,
     "status": "Nearly complete along 4096 km border",
     "color": "#10b981",
     "coords": [[21.5, 92.3], [23.0, 92.0], [24.5, 92.5], [25.5, 90.0],
                 [26.0, 89.0], [25.0, 88.0], [23.5, 88.5], [22.0, 89.0]]},
    {"name": "Hungary-Serbia Border Fence",
     "countries": "Hungary / Serbia",
     "length_km": 175, "year_start": 2015, "year_latest": 2015,
     "status": "Complete - anti-migration razor wire fence",
     "color": "#f59e0b",
     "coords": [[46.17, 18.8], [46.13, 19.5], [46.1, 20.3]]},
    {"name": "Saudi Arabia-Iraq Barrier",
     "countries": "Saudi Arabia / Iraq",
     "length_km": 900, "year_start": 2006, "year_latest": 2014,
     "status": "Complete - border security system",
     "color": "#8b5cf6",
     "coords": [[29.1, 46.5], [29.4, 43.5], [31.0, 40.0], [32.2, 39.0]]},
    {"name": "Saudi Arabia-Yemen Barrier",
     "countries": "Saudi Arabia / Yemen",
     "length_km": 75, "year_start": 2004, "year_latest": 2013,
     "status": "Partial, extended after Houthi conflict",
     "color": "#a855f7",
     "coords": [[16.5, 43.2], [17.5, 44.0], [18.5, 45.5], [19.0, 48.0]]},
    {"name": "India-Pakistan Border Fence (LoC)",
     "countries": "India / Pakistan",
     "length_km": 550, "year_start": 2000, "year_latest": 2004,
     "status": "Complete along Line of Control in Kashmir",
     "color": "#ec4899",
     "coords": [[32.5, 74.0], [33.5, 74.0], [34.5, 74.5], [35.0, 75.0]]},
    {"name": "Morocco-Western Sahara Berm",
     "countries": "Morocco / Western Sahara (Polisario)",
     "length_km": 2720, "year_start": 1980, "year_latest": 1987,
     "status": "Complete - sand berm with minefields",
     "color": "#06b6d4",
     "coords": [[21.5, -16.5], [23.0, -15.0], [24.5, -14.0],
                 [26.0, -12.0], [27.5, -9.0]]},
    {"name": "Turkey-Syria Border Wall",
     "countries": "Turkey / Syria",
     "length_km": 764, "year_start": 2015, "year_latest": 2018,
     "status": "Complete - concrete wall with surveillance",
     "color": "#f97316",
     "coords": [[36.2, 36.0], [36.5, 37.5], [36.8, 39.0], [37.0, 40.5],
                 [37.1, 42.0]]},
    {"name": "Greece-Turkey Evros Fence",
     "countries": "Greece / Turkey",
     "length_km": 40, "year_start": 2012, "year_latest": 2021,
     "status": "Extended from 12.5 km to 40 km",
     "color": "#22d3ee",
     "coords": [[40.85, 26.3], [41.2, 26.4], [41.6, 26.35]]},
    {"name": "Korean DMZ Fence",
     "countries": "South Korea / North Korea",
     "length_km": 250, "year_start": 1953, "year_latest": 1953,
     "status": "Complete - most heavily fortified border",
     "color": "#facc15",
     "coords": [[37.95, 126.6], [38.0, 127.0], [38.1, 127.5],
                 [38.3, 128.0], [38.6, 128.3]]},
    {"name": "Cyprus UN Buffer Zone",
     "countries": "Republic of Cyprus / Northern Cyprus",
     "length_km": 180, "year_start": 1974, "year_latest": 1974,
     "status": "UN-patrolled buffer zone (Green Line)",
     "color": "#4ade80",
     "coords": [[35.18, 32.9], [35.17, 33.3], [35.10, 33.6],
                 [35.05, 33.9], [35.08, 34.0]]},
    {"name": "Israel-Egypt Barrier",
     "countries": "Israel / Egypt (Sinai)",
     "length_km": 245, "year_start": 2010, "year_latest": 2013,
     "status": "Complete - anti-infiltration fence",
     "color": "#818cf8",
     "coords": [[29.5, 34.2], [30.0, 34.4], [31.0, 34.2], [31.2, 34.3]]},
    {"name": "Uzbekistan-Afghanistan Border Fence",
     "countries": "Uzbekistan / Afghanistan",
     "length_km": 209, "year_start": 2001, "year_latest": 2021,
     "status": "Complete along Termez sector",
     "color": "#fb7185",
     "coords": [[37.2, 66.9], [37.3, 67.5], [37.4, 68.0]]},
    {"name": "Botswana-Zimbabwe Electric Fence",
     "countries": "Botswana / Zimbabwe",
     "length_km": 500, "year_start": 2003, "year_latest": 2005,
     "status": "Electric fence, officially for veterinary control",
     "color": "#2dd4bf",
     "coords": [[-22.0, 27.0], [-21.5, 28.0], [-21.0, 29.0], [-20.5, 29.5]]},
]

# =====================================================================
# 7. MILITARY ALLIANCES TIMELINE DATA
# =====================================================================
MILITARY_ALLIANCES = [
    {"name": "NATO", "founded": 1949, "dissolved": None,
     "color": "#3b82f6", "type": "Collective defense",
     "members": ["US", "UK", "FR", "CA", "BE", "NL", "LU", "NO", "DK", "IS",
                  "IT", "PT", "GR", "TR", "DE", "ES", "CZ", "HU", "PL", "BG",
                  "EE", "LV", "LT", "RO", "SK", "SI", "AL", "HR", "ME", "MK",
                  "FI", "SE"],
     "member_coords": [
         [38.9, -77.0], [51.5, -0.1], [48.9, 2.3], [45.4, -75.7],
         [50.8, 4.4], [52.4, 4.9], [49.6, 6.1], [59.9, 10.7],
         [55.7, 12.6], [64.1, -21.9], [41.9, 12.5], [38.7, -9.1],
         [37.98, 23.7], [39.93, 32.9], [52.5, 13.4], [40.4, -3.7],
         [50.1, 14.4], [47.5, 19.0], [52.2, 21.0], [42.7, 23.3],
         [59.4, 24.7], [56.9, 24.1], [54.7, 25.3], [44.4, 26.1],
         [48.1, 17.1], [46.1, 14.5], [41.3, 19.8], [45.8, 16.0],
         [42.4, 19.3], [42.0, 21.4], [60.2, 24.9], [59.3, 18.1]]},
    {"name": "Warsaw Pact", "founded": 1955, "dissolved": 1991,
     "color": "#ef4444", "type": "Collective defense (dissolved)",
     "members": ["USSR", "Poland", "East Germany", "Czechoslovakia", "Hungary",
                  "Romania", "Bulgaria", "Albania (left 1968)"],
     "member_coords": [
         [55.8, 37.6], [52.2, 21.0], [52.5, 13.4], [50.1, 14.4],
         [47.5, 19.0], [44.4, 26.1], [42.7, 23.3], [41.3, 19.8]]},
    {"name": "SEATO", "founded": 1954, "dissolved": 1977,
     "color": "#f59e0b", "type": "Collective defense (dissolved)",
     "members": ["US", "UK", "FR", "Australia", "NZ", "Philippines",
                  "Thailand", "Pakistan"],
     "member_coords": [
         [38.9, -77.0], [51.5, -0.1], [48.9, 2.3], [-33.9, 151.2],
         [-41.3, 174.8], [14.6, 121.0], [13.8, 100.5], [33.7, 73.0]]},
    {"name": "ANZUS", "founded": 1951, "dissolved": None,
     "color": "#10b981", "type": "Collective security treaty",
     "members": ["Australia", "New Zealand", "United States"],
     "member_coords": [[-33.9, 151.2], [-41.3, 174.8], [38.9, -77.0]]},
    {"name": "Five Eyes", "founded": 1941, "dissolved": None,
     "color": "#8b5cf6", "type": "Intelligence alliance",
     "members": ["US", "UK", "Canada", "Australia", "New Zealand"],
     "member_coords": [
         [38.9, -77.0], [51.5, -0.1], [45.4, -75.7],
         [-33.9, 151.2], [-41.3, 174.8]]},
    {"name": "Quad (Quadrilateral Security Dialogue)", "founded": 2007, "dissolved": None,
     "color": "#06b6d4", "type": "Strategic dialogue",
     "members": ["US", "Japan", "India", "Australia"],
     "member_coords": [
         [38.9, -77.0], [35.7, 139.7], [28.6, 77.2], [-33.9, 151.2]]},
    {"name": "AUKUS", "founded": 2021, "dissolved": None,
     "color": "#ec4899", "type": "Trilateral security pact",
     "members": ["Australia", "United Kingdom", "United States"],
     "member_coords": [[-33.9, 151.2], [51.5, -0.1], [38.9, -77.0]]},
    {"name": "CSTO", "founded": 1992, "dissolved": None,
     "color": "#dc2626", "type": "Collective security",
     "members": ["Russia", "Belarus", "Armenia", "Kazakhstan",
                  "Kyrgyzstan", "Tajikistan"],
     "member_coords": [
         [55.8, 37.6], [53.9, 27.6], [40.2, 44.5],
         [51.2, 71.4], [42.9, 74.6], [38.6, 68.8]]},
    {"name": "SCO (Shanghai Cooperation Org.)", "founded": 2001, "dissolved": None,
     "color": "#f97316", "type": "Political-military alliance",
     "members": ["China", "Russia", "India", "Pakistan", "Kazakhstan",
                  "Uzbekistan", "Kyrgyzstan", "Tajikistan", "Iran"],
     "member_coords": [
         [39.9, 116.4], [55.8, 37.6], [28.6, 77.2], [33.7, 73.0],
         [51.2, 71.4], [41.3, 69.3], [42.9, 74.6], [38.6, 68.8],
         [35.7, 51.4]]},
    {"name": "African Union (Peace & Security)", "founded": 2002, "dissolved": None,
     "color": "#84cc16", "type": "Continental security framework",
     "members": ["55 African states"],
     "member_coords": [
         [36.8, 10.2], [30.0, 31.2], [9.0, 38.7], [-1.3, 36.8],
         [6.5, 3.4], [14.7, -17.5], [-4.3, 15.3], [-25.7, 28.2],
         [33.6, -7.6], [12.6, -8.0]]},
]

# =====================================================================
# 8. ARMS TRADE ROUTES DATA
# =====================================================================
ARMS_TRADE_ROUTES = [
    {"exporter": "United States", "ex_lat": 38.9, "ex_lon": -77.0,
     "importer": "Saudi Arabia", "im_lat": 24.7, "im_lon": 46.7,
     "volume": "Very High", "value_bn": 4.5, "color": "#3b82f6",
     "equipment": "F-15 jets, missiles, naval vessels"},
    {"exporter": "United States", "ex_lat": 38.9, "ex_lon": -77.0,
     "importer": "Japan", "im_lat": 35.7, "im_lon": 139.7,
     "volume": "High", "value_bn": 2.8, "color": "#3b82f6",
     "equipment": "F-35 jets, Aegis systems, Osprey"},
    {"exporter": "United States", "ex_lat": 38.9, "ex_lon": -77.0,
     "importer": "Australia", "im_lat": -33.9, "im_lon": 151.2,
     "volume": "High", "value_bn": 2.1, "color": "#3b82f6",
     "equipment": "F-35 jets, submarines (AUKUS), naval"},
    {"exporter": "United States", "ex_lat": 38.9, "ex_lon": -77.0,
     "importer": "South Korea", "im_lat": 37.6, "im_lon": 127.0,
     "volume": "High", "value_bn": 2.0, "color": "#3b82f6",
     "equipment": "F-35 jets, THAAD, helicopters"},
    {"exporter": "United States", "ex_lat": 38.9, "ex_lon": -77.0,
     "importer": "Taiwan", "im_lat": 25.0, "im_lon": 121.5,
     "volume": "High", "value_bn": 1.8, "color": "#3b82f6",
     "equipment": "F-16V, tanks, anti-ship missiles"},
    {"exporter": "Russia", "ex_lat": 55.8, "ex_lon": 37.6,
     "importer": "India", "im_lat": 28.6, "im_lon": 77.2,
     "volume": "Very High", "value_bn": 3.5, "color": "#ef4444",
     "equipment": "S-400, Su-30MKI, T-90 tanks"},
    {"exporter": "Russia", "ex_lat": 55.8, "ex_lon": 37.6,
     "importer": "China", "im_lat": 39.9, "im_lon": 116.4,
     "volume": "High", "value_bn": 2.5, "color": "#ef4444",
     "equipment": "Su-35, S-400, submarine tech"},
    {"exporter": "Russia", "ex_lat": 55.8, "ex_lon": 37.6,
     "importer": "Egypt", "im_lat": 30.0, "im_lon": 31.2,
     "volume": "Medium", "value_bn": 1.5, "color": "#ef4444",
     "equipment": "Su-35, MiG-29, Ka-52 helicopters"},
    {"exporter": "Russia", "ex_lat": 55.8, "ex_lon": 37.6,
     "importer": "Algeria", "im_lat": 36.8, "im_lon": 3.0,
     "volume": "Medium", "value_bn": 1.2, "color": "#ef4444",
     "equipment": "Su-30, frigates, T-90 tanks"},
    {"exporter": "France", "ex_lat": 48.9, "ex_lon": 2.3,
     "importer": "India", "im_lat": 28.6, "im_lon": 77.2,
     "volume": "High", "value_bn": 2.0, "color": "#f59e0b",
     "equipment": "Rafale jets, Scorpene submarines"},
    {"exporter": "France", "ex_lat": 48.9, "ex_lon": 2.3,
     "importer": "Qatar", "im_lat": 25.3, "im_lon": 51.5,
     "volume": "High", "value_bn": 1.8, "color": "#f59e0b",
     "equipment": "Rafale jets, NH90 helicopters"},
    {"exporter": "France", "ex_lat": 48.9, "ex_lon": 2.3,
     "importer": "Egypt", "im_lat": 30.0, "im_lon": 31.2,
     "volume": "Medium", "value_bn": 1.2, "color": "#f59e0b",
     "equipment": "Rafale jets, FREMM frigates"},
    {"exporter": "China", "ex_lat": 39.9, "ex_lon": 116.4,
     "importer": "Pakistan", "im_lat": 33.7, "im_lon": 73.0,
     "volume": "Very High", "value_bn": 2.8, "color": "#10b981",
     "equipment": "JF-17, frigates, HQ-9 SAM"},
    {"exporter": "China", "ex_lat": 39.9, "ex_lon": 116.4,
     "importer": "Bangladesh", "im_lat": 23.8, "im_lon": 90.4,
     "volume": "Medium", "value_bn": 1.0, "color": "#10b981",
     "equipment": "Submarines, frigates, aircraft"},
    {"exporter": "China", "ex_lat": 39.9, "ex_lon": 116.4,
     "importer": "Myanmar", "im_lat": 19.8, "im_lon": 96.2,
     "volume": "Medium", "value_bn": 0.8, "color": "#10b981",
     "equipment": "JF-17, naval vessels, armored vehicles"},
    {"exporter": "Germany", "ex_lat": 52.5, "ex_lon": 13.4,
     "importer": "South Korea", "im_lat": 37.6, "im_lon": 127.0,
     "volume": "Medium", "value_bn": 1.1, "color": "#8b5cf6",
     "equipment": "Submarines, tanks, naval guns"},
    {"exporter": "United Kingdom", "ex_lat": 51.5, "ex_lon": -0.1,
     "importer": "Saudi Arabia", "im_lat": 24.7, "im_lon": 46.7,
     "volume": "High", "value_bn": 1.8, "color": "#ec4899",
     "equipment": "Typhoon jets, BAE systems"},
    {"exporter": "Israel", "ex_lat": 31.8, "ex_lon": 35.2,
     "importer": "India", "im_lat": 28.6, "im_lon": 77.2,
     "volume": "High", "value_bn": 1.5, "color": "#06b6d4",
     "equipment": "Drones, radar, missiles, AWACS"},
    {"exporter": "South Korea", "ex_lat": 37.6, "ex_lon": 127.0,
     "importer": "Poland", "im_lat": 52.2, "im_lon": 21.0,
     "volume": "High", "value_bn": 1.4, "color": "#14b8a6",
     "equipment": "K2 tanks, K9 howitzers, FA-50"},
    {"exporter": "Turkey", "ex_lat": 39.93, "ex_lon": 32.9,
     "importer": "Ukraine", "im_lat": 50.4, "im_lon": 30.5,
     "volume": "Medium", "value_bn": 0.7, "color": "#f97316",
     "equipment": "Bayraktar TB2 drones"},
]

# =====================================================================
# 9. CONFLICT ZONES DATA
# =====================================================================
CONFLICT_ZONES = [
    {"name": "Russia-Ukraine War", "type": "Interstate war",
     "start_year": 2022, "parties": "Russia vs Ukraine",
     "lat": 48.5, "lon": 35.0, "radius": 25,
     "color": "#ef4444", "severity": "High intensity"},
    {"name": "Syrian Civil War", "type": "Civil war / proxy war",
     "start_year": 2011, "parties": "Multiple factions, foreign powers",
     "lat": 35.0, "lon": 38.5, "radius": 20,
     "color": "#f59e0b", "severity": "Reduced intensity"},
    {"name": "Yemen Civil War", "type": "Civil war / proxy war",
     "start_year": 2014, "parties": "Houthis vs Saudi-led coalition",
     "lat": 15.4, "lon": 44.2, "radius": 18,
     "color": "#dc2626", "severity": "High intensity"},
    {"name": "Myanmar Civil War", "type": "Civil war / revolution",
     "start_year": 2021, "parties": "Military junta vs resistance forces",
     "lat": 19.8, "lon": 96.2, "radius": 20,
     "color": "#f97316", "severity": "High intensity"},
    {"name": "Ethiopian Conflicts", "type": "Civil conflict / ethnic violence",
     "start_year": 2020, "parties": "Federal gov vs regional forces",
     "lat": 9.0, "lon": 38.7, "radius": 18,
     "color": "#a855f7", "severity": "Medium intensity"},
    {"name": "Sahel Insurgency", "type": "Jihadist insurgency",
     "start_year": 2012, "parties": "JNIM, ISGS vs national armies",
     "lat": 14.0, "lon": 0.0, "radius": 25,
     "color": "#ec4899", "severity": "High intensity"},
    {"name": "Somalia (Al-Shabaab)", "type": "Insurgency",
     "start_year": 2006, "parties": "Al-Shabaab vs Somali gov / AU forces",
     "lat": 2.0, "lon": 45.3, "radius": 18,
     "color": "#fb923c", "severity": "High intensity"},
    {"name": "DRC Eastern Conflict", "type": "Armed conflict / insurgency",
     "start_year": 1996, "parties": "M23, ADF, Mai-Mai vs DRC army / UN",
     "lat": -1.5, "lon": 29.0, "radius": 16,
     "color": "#e11d48", "severity": "High intensity"},
    {"name": "Lake Chad Basin (Boko Haram)", "type": "Jihadist insurgency",
     "start_year": 2009, "parties": "Boko Haram / ISWAP vs regional forces",
     "lat": 12.0, "lon": 13.5, "radius": 16,
     "color": "#f472b6", "severity": "High intensity"},
    {"name": "Afghanistan (Taliban regime)", "type": "Internal conflict / resistance",
     "start_year": 2021, "parties": "Taliban gov vs NRF, IS-KP",
     "lat": 34.5, "lon": 69.2, "radius": 20,
     "color": "#8b5cf6", "severity": "Medium intensity"},
    {"name": "Iraq (ISIS remnants)", "type": "Insurgency",
     "start_year": 2017, "parties": "ISIS cells vs Iraqi forces",
     "lat": 33.3, "lon": 44.4, "radius": 15,
     "color": "#fbbf24", "severity": "Low intensity"},
    {"name": "Israel-Palestine Conflict", "type": "Occupied territory / armed conflict",
     "start_year": 1948, "parties": "Israel vs Palestinian groups",
     "lat": 31.5, "lon": 34.8, "radius": 12,
     "color": "#14b8a6", "severity": "High intensity"},
    {"name": "India-Pakistan (Kashmir)", "type": "Border dispute / insurgency",
     "start_year": 1947, "parties": "India vs Pakistan, militant groups",
     "lat": 34.0, "lon": 75.5, "radius": 15,
     "color": "#06b6d4", "severity": "Low intensity"},
    {"name": "Mozambique (Cabo Delgado)", "type": "Jihadist insurgency",
     "start_year": 2017, "parties": "IS-Mozambique vs gov / SADC forces",
     "lat": -12.5, "lon": 40.0, "radius": 14,
     "color": "#84cc16", "severity": "Medium intensity"},
    {"name": "Colombia (armed groups)", "type": "Internal armed conflict",
     "start_year": 1964, "parties": "ELN, FARC dissidents vs Colombian gov",
     "lat": 4.6, "lon": -74.1, "radius": 18,
     "color": "#22d3ee", "severity": "Low intensity"},
    {"name": "Sudan Civil War", "type": "Civil war",
     "start_year": 2023, "parties": "SAF vs RSF",
     "lat": 15.6, "lon": 32.5, "radius": 20,
     "color": "#d946ef", "severity": "High intensity"},
    {"name": "Haiti Gang Violence", "type": "Armed gang conflict",
     "start_year": 2021, "parties": "Armed gangs vs transitional gov",
     "lat": 18.5, "lon": -72.3, "radius": 10,
     "color": "#fb7185", "severity": "High intensity"},
    {"name": "Papua New Guinea (Highlands)", "type": "Tribal / communal violence",
     "start_year": 2000, "parties": "Highland tribal groups",
     "lat": -5.5, "lon": 144.0, "radius": 12,
     "color": "#a3e635", "severity": "Low intensity"},
    {"name": "Cameroon (Anglophone Crisis)", "type": "Separatist conflict",
     "start_year": 2017, "parties": "Ambazonia separatists vs Cameroon army",
     "lat": 5.9, "lon": 10.1, "radius": 12,
     "color": "#38bdf8", "severity": "Medium intensity"},
    {"name": "Philippines (NPA / Mindanao)", "type": "Communist / separatist insurgency",
     "start_year": 1969, "parties": "NPA, Abu Sayyaf vs Philippine military",
     "lat": 7.5, "lon": 124.0, "radius": 14,
     "color": "#c084fc", "severity": "Low intensity"},
    {"name": "Nagorno-Karabakh (aftermath)", "type": "Post-conflict displacement",
     "start_year": 2023, "parties": "Azerbaijan (recaptured), Armenian displacement",
     "lat": 39.8, "lon": 46.8, "radius": 10,
     "color": "#fca5a5", "severity": "Post-conflict"},
    {"name": "Central African Republic", "type": "Civil war / armed groups",
     "start_year": 2012, "parties": "Ex-Seleka, Anti-Balaka vs CAR army / Wagner",
     "lat": 4.4, "lon": 18.6, "radius": 16,
     "color": "#2dd4bf", "severity": "Medium intensity"},
    {"name": "Libya (political instability)", "type": "Civil conflict / division",
     "start_year": 2014, "parties": "GNU (Tripoli) vs LNA (Benghazi)",
     "lat": 32.9, "lon": 13.2, "radius": 18,
     "color": "#818cf8", "severity": "Low intensity"},
    {"name": "Mexico Drug War", "type": "Narco-insurgency / organized crime",
     "start_year": 2006, "parties": "Cartels vs Mexican security forces",
     "lat": 23.6, "lon": -102.5, "radius": 22,
     "color": "#facc15", "severity": "High intensity"},
    {"name": "Niger (Sahel instability)", "type": "Jihadist insurgency / coup aftermath",
     "start_year": 2015, "parties": "JNIM, IS-Sahel vs military junta",
     "lat": 13.5, "lon": 2.1, "radius": 14,
     "color": "#4ade80", "severity": "Medium intensity"},
]

# =====================================================================
# 10. DEMILITARIZED ZONES DATA
# =====================================================================
DEMILITARIZED_ZONES = [
    {"name": "Korean DMZ",
     "location": "Korean Peninsula (38th parallel)",
     "width_km": 4.0, "length_km": 250,
     "year": 1953, "status": "Active - most fortified border",
     "parties": "North Korea / South Korea (UN Command)",
     "color": "#ef4444",
     "coords": [[37.95, 126.5], [38.0, 127.0], [38.1, 127.5],
                 [38.3, 128.0], [38.6, 128.4]],
     "polygon": [[37.93, 126.5], [38.62, 128.4], [38.58, 128.4], [37.91, 126.5]]},
    {"name": "Cyprus UN Buffer Zone (Green Line)",
     "location": "Cyprus - Nicosia to coast",
     "width_km": 3.5, "length_km": 180,
     "year": 1974, "status": "Active - UN peacekeeping (UNFICYP)",
     "parties": "Republic of Cyprus / Northern Cyprus (Turkey)",
     "color": "#10b981",
     "coords": [[35.18, 32.85], [35.17, 33.3], [35.10, 33.6],
                 [35.05, 33.95], [35.08, 34.05]],
     "polygon": [[35.20, 32.85], [35.10, 34.05], [35.06, 34.05], [35.16, 32.85]]},
    {"name": "Golan Heights UNDOF Zone",
     "location": "Golan Heights (Israel-Syria border)",
     "width_km": 10.0, "length_km": 70,
     "year": 1974, "status": "Active - UN Disengagement Observer Force",
     "parties": "Israel / Syria",
     "color": "#3b82f6",
     "coords": [[32.75, 35.85], [33.0, 35.88], [33.25, 35.90]],
     "polygon": [[32.75, 35.80], [33.25, 35.85], [33.25, 35.95], [32.75, 35.90]]},
    {"name": "Sinai Multinational Force Zone",
     "location": "Sinai Peninsula (Egypt-Israel border)",
     "width_km": 40.0, "length_km": 200,
     "year": 1982, "status": "Active - MFO peacekeeping",
     "parties": "Egypt / Israel",
     "color": "#f59e0b",
     "coords": [[29.5, 34.3], [30.0, 34.5], [30.5, 34.5], [31.0, 34.3]],
     "polygon": [[29.5, 34.0], [31.0, 34.0], [31.0, 34.6], [29.5, 34.6]]},
    {"name": "Aouzou Strip (former DMZ)",
     "location": "Chad-Libya border",
     "width_km": 100.0, "length_km": 1000,
     "year": 1994, "status": "Resolved - ICJ awarded to Chad (1994)",
     "parties": "Chad / Libya (historical)",
     "color": "#8b5cf6",
     "coords": [[21.0, 16.0], [22.0, 18.0], [23.0, 20.0], [23.5, 22.0]],
     "polygon": [[20.5, 16.0], [23.5, 22.0], [24.0, 22.0], [21.0, 16.0]]},
    {"name": "Kuwaiti DMZ (former)",
     "location": "Iraq-Kuwait border",
     "width_km": 15.0, "length_km": 200,
     "year": 1991, "status": "Demarcated 1993, DMZ lifted 2003",
     "parties": "Iraq / Kuwait (UN)",
     "color": "#ec4899",
     "coords": [[29.3, 46.5], [29.5, 47.5], [29.8, 48.0]],
     "polygon": [[29.2, 46.5], [29.7, 48.0], [29.9, 48.0], [29.4, 46.5]]},
    {"name": "Vietnam DMZ (former, 17th parallel)",
     "location": "Ben Hai River, Quang Tri Province",
     "width_km": 10.0, "length_km": 100,
     "year": 1954, "status": "Historical - dissolved 1976 (reunification)",
     "parties": "North Vietnam / South Vietnam (historical)",
     "color": "#f97316",
     "coords": [[16.9, 106.5], [17.0, 106.8], [17.1, 107.0], [17.1, 107.2]],
     "polygon": [[16.85, 106.5], [17.05, 107.2], [17.15, 107.2], [16.95, 106.5]]},
    {"name": "Antarctic Treaty Zone",
     "location": "South of 60 degrees South latitude",
     "width_km": 0, "length_km": 0,
     "year": 1959, "status": "Active - demilitarized continent",
     "parties": "54 signatory nations",
     "color": "#06b6d4",
     "coords": [[-60.0, -180.0], [-60.0, -90.0], [-60.0, 0.0],
                 [-60.0, 90.0], [-60.0, 180.0]],
     "polygon": [[-60.0, -180.0], [-60.0, 180.0], [-90.0, 180.0], [-90.0, -180.0]]},
    {"name": "Svalbard (demilitarized)",
     "location": "Svalbard Archipelago, Arctic Norway",
     "width_km": 0, "length_km": 0,
     "year": 1920, "status": "Active - Svalbard Treaty demilitarization",
     "parties": "Norway (sovereignty), 46 signatories",
     "color": "#14b8a6",
     "coords": [[76.5, 14.0], [78.0, 16.0], [79.5, 18.0], [80.0, 20.0]],
     "polygon": [[76.0, 10.0], [80.5, 10.0], [80.5, 35.0], [76.0, 35.0]]},
    {"name": "Rhineland (historical DMZ)",
     "location": "Western Germany (Rhine River area)",
     "width_km": 50.0, "length_km": 300,
     "year": 1919, "status": "Historical - Treaty of Versailles, remilitarized 1936",
     "parties": "Germany / Allied Powers (historical)",
     "color": "#a855f7",
     "coords": [[49.5, 6.5], [50.5, 7.0], [51.5, 6.8], [52.0, 7.2]],
     "polygon": [[49.0, 6.0], [52.5, 6.0], [52.5, 7.5], [49.0, 7.5]]},
]


# =====================================================================
# CACHED DATA FUNCTIONS
# =====================================================================
@st.cache_data(ttl=3600)
def fetch_military_bases(region_name: str) -> list[dict]:
    """Fetch military installations from Overpass API in a given region."""
    region = MILITARY_BASE_REGIONS.get(region_name)
    if not region:
        return []

    query = f"""
    [out:json][timeout:60];
    (
      node["military"](around:{region['radius']},{region['lat']},{region['lon']});
      way["military"](around:{region['radius']},{region['lat']},{region['lon']});
      relation["military"](around:{region['radius']},{region['lat']},{region['lon']});
    );
    out center 300;
    """
    data = query_overpass(query)
    if data is None or "_error" in data:
        return []

    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        results.append({
            "name": tags.get("name", "Unknown"),
            "type": tags.get("military", "unknown"),
            "operator": tags.get("operator", "N/A"),
            "lat": lat,
            "lon": lon,
        })
    return results


@st.cache_data(ttl=3600)
def get_nato_data() -> pd.DataFrame:
    """Return NATO members as a DataFrame."""
    return pd.DataFrame(NATO_MEMBERS)


@st.cache_data(ttl=3600)
def get_csto_data() -> pd.DataFrame:
    """Return CSTO members as a DataFrame."""
    return pd.DataFrame(CSTO_MEMBERS)


@st.cache_data(ttl=3600)
def get_nuclear_data() -> pd.DataFrame:
    """Return nuclear powers data as a DataFrame."""
    return pd.DataFrame(NUCLEAR_POWERS)


@st.cache_data(ttl=3600)
def get_disputed_data() -> pd.DataFrame:
    """Return disputed territories as a DataFrame."""
    rows = []
    for d in DISPUTED_TERRITORIES:
        rows.append({
            "Name": d["name"],
            "Claimants": d["claimants"],
            "Status": d["status"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_maritime_data() -> pd.DataFrame:
    """Return maritime boundary disputes as a DataFrame."""
    rows = []
    for m in MARITIME_ZONES:
        rows.append({
            "Zone": m["name"],
            "Claimant(s)": m["claimant"],
            "Status": m["status"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_border_walls_data() -> pd.DataFrame:
    """Return border walls/fences as a DataFrame."""
    rows = []
    for w in BORDER_WALLS:
        rows.append({
            "Name": w["name"],
            "Countries": w["countries"],
            "Length (km)": w["length_km"],
            "Year Started": w["year_start"],
            "Latest Expansion": w["year_latest"],
            "Status": w["status"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_alliances_data() -> pd.DataFrame:
    """Return military alliances as a DataFrame."""
    rows = []
    for a in MILITARY_ALLIANCES:
        dissolved = a["dissolved"] if a["dissolved"] else "Active"
        rows.append({
            "Alliance": a["name"],
            "Founded": a["founded"],
            "Dissolved": dissolved,
            "Type": a["type"],
            "Members": ", ".join(a["members"]),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_arms_trade_data() -> pd.DataFrame:
    """Return arms trade routes as a DataFrame."""
    rows = []
    for r in ARMS_TRADE_ROUTES:
        rows.append({
            "Exporter": r["exporter"],
            "Importer": r["importer"],
            "Volume": r["volume"],
            "Value ($B)": r["value_bn"],
            "Equipment": r["equipment"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_conflict_data() -> pd.DataFrame:
    """Return conflict zones as a DataFrame."""
    rows = []
    for c in CONFLICT_ZONES:
        rows.append({
            "Conflict": c["name"],
            "Type": c["type"],
            "Start Year": c["start_year"],
            "Parties": c["parties"],
            "Severity": c["severity"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_dmz_data() -> pd.DataFrame:
    """Return DMZ data as a DataFrame."""
    rows = []
    for d in DEMILITARIZED_ZONES:
        rows.append({
            "Name": d["name"],
            "Location": d["location"],
            "Width (km)": d["width_km"],
            "Length (km)": d["length_km"],
            "Year Established": d["year"],
            "Status": d["status"],
            "Parties": d["parties"],
        })
    return pd.DataFrame(rows)


# =====================================================================
# MAP BUILDER FUNCTIONS
# =====================================================================
def _build_military_bases_map(bases: list[dict]) -> folium.Map:
    """Build a folium map showing military bases."""
    if not bases:
        return folium.Map(location=[30, 0], zoom_start=3,
                          tiles="CartoDB dark_matter")
    avg_lat = sum(b["lat"] for b in bases) / len(bases)
    avg_lon = sum(b["lon"] for b in bases) / len(bases)
    fmap = folium.Map(location=[avg_lat, avg_lon], zoom_start=5,
                      tiles="CartoDB dark_matter")
    cluster = MarkerCluster().add_to(fmap)
    type_colors = {
        "barracks": "red", "airfield": "blue", "naval_base": "darkblue",
        "range": "orange", "training_area": "green", "danger_area": "darkred",
        "bunker": "gray", "checkpoint": "lightgray", "nuclear_explosion_site": "black",
        "office": "cadetblue", "ammunition": "darkred", "launchpad": "purple",
    }
    for b in bases:
        color = type_colors.get(b["type"], "red")
        popup_html = (
            f"<b>{escape(b['name'])}</b><br>"
            f"Type: {escape(b['type'])}<br>"
            f"Operator: {escape(b['operator'])}"
        )
        folium.Marker(
            location=[b["lat"], b["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color, icon="shield", prefix="fa"),
        ).add_to(cluster)
    return fmap


def _build_nato_map() -> folium.Map:
    """Build choropleth-style map for NATO vs CSTO."""
    fmap = folium.Map(location=[45, 30], zoom_start=3,
                      tiles="CartoDB dark_matter")
    for m in NATO_MEMBERS:
        folium.CircleMarker(
            location=[m["lat"], m["lon"]],
            radius=8, color="#3b82f6", fill=True,
            fill_color="#3b82f6", fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{escape(m['country'])}</b><br>"
                f"NATO since {m['year']}<br>"
                f"Code: {escape(m['code'])}",
                max_width=200),
        ).add_to(fmap)
    for m in CSTO_MEMBERS:
        folium.CircleMarker(
            location=[m["lat"], m["lon"]],
            radius=8, color="#ef4444", fill=True,
            fill_color="#ef4444", fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{escape(m['country'])}</b><br>"
                f"CSTO since {m['year']}<br>"
                f"Code: {escape(m['code'])}",
                max_width=200),
        ).add_to(fmap)
    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
    background:rgba(15,23,42,0.85);padding:10px 14px;border-radius:8px;
    border:1px solid #2a3550;font-size:13px;color:#e8ecf4;">
    <b>Alliance Blocs</b><br>
    <span style="color:#3b82f6;">&#9679;</span> NATO<br>
    <span style="color:#ef4444;">&#9679;</span> CSTO<br>
    <span style="color:#6b7280;">&#9679;</span> Non-aligned
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))
    return fmap


def _build_nuclear_map() -> folium.Map:
    """Build graduated circle map for nuclear powers."""
    fmap = folium.Map(location=[30, 30], zoom_start=2,
                      tiles="CartoDB dark_matter")
    max_warheads = max(n["warheads"] for n in NUCLEAR_POWERS)
    for n in NUCLEAR_POWERS:
        radius = max(8, (n["warheads"] / max_warheads) * 45)
        folium.CircleMarker(
            location=[n["lat"], n["lon"]],
            radius=radius,
            color="#ef4444", fill=True,
            fill_color="#ef4444", fill_opacity=0.5,
            popup=folium.Popup(
                f"<b>{escape(n['country'])}</b><br>"
                f"Warheads: ~{n['warheads']:,}<br>"
                f"First test: {escape(n['first_test'])}<br>"
                f"Status: {escape(n['status'])}",
                max_width=250),
        ).add_to(fmap)
        folium.Marker(
            location=[n["lat"], n["lon"]],
            icon=folium.DivIcon(html=(
                f"<div style='font-size:10px;color:#fca5a5;text-align:center;"
                f"text-shadow:1px 1px 2px #000;white-space:nowrap;'>"
                f"{escape(n['country'])}<br>{n['warheads']:,}</div>"
            )),
        ).add_to(fmap)
    return fmap


def _build_disputed_map(selected_territories: list[str]) -> folium.Map:
    """Build map showing disputed territories as polygons."""
    fmap = folium.Map(location=[30, 50], zoom_start=3,
                      tiles="CartoDB dark_matter")
    for d in DISPUTED_TERRITORIES:
        if selected_territories and d["name"] not in selected_territories:
            continue
        folium.Polygon(
            locations=d["polygon"],
            color=d["color"], fill=True,
            fill_color=d["color"], fill_opacity=0.35,
            popup=folium.Popup(
                f"<b>{escape(d['name'])}</b><br>"
                f"Claimants: {escape(d['claimants'])}<br>"
                f"Status: {escape(d['status'])}",
                max_width=280),
        ).add_to(fmap)
        center_lat = sum(p[0] for p in d["polygon"]) / len(d["polygon"])
        center_lon = sum(p[1] for p in d["polygon"]) / len(d["polygon"])
        folium.Marker(
            location=[center_lat, center_lon],
            icon=folium.DivIcon(html=(
                f"<div style='font-size:9px;color:{d['color']};text-align:center;"
                f"text-shadow:1px 1px 2px #000;white-space:nowrap;'>"
                f"{escape(d['name'])}</div>"
            )),
        ).add_to(fmap)
    return fmap


def _build_maritime_map() -> folium.Map:
    """Build map showing maritime boundary disputes."""
    fmap = folium.Map(location=[25, 60], zoom_start=3,
                      tiles="CartoDB dark_matter")
    for mz in MARITIME_ZONES:
        folium.Polygon(
            locations=mz["coords"],
            color=mz["color"], fill=True,
            fill_color=mz["color"], fill_opacity=0.25,
            weight=2,
            popup=folium.Popup(
                f"<b>{escape(mz['name'])}</b><br>"
                f"Claimant(s): {escape(mz['claimant'])}<br>"
                f"Status: {escape(mz['status'])}",
                max_width=280),
        ).add_to(fmap)
        center_lat = sum(c[0] for c in mz["coords"]) / len(mz["coords"])
        center_lon = sum(c[1] for c in mz["coords"]) / len(mz["coords"])
        folium.Marker(
            location=[center_lat, center_lon],
            icon=folium.DivIcon(html=(
                f"<div style='font-size:9px;color:{mz['color']};text-align:center;"
                f"text-shadow:1px 1px 2px #000;white-space:nowrap;'>"
                f"{escape(mz['name'])}</div>"
            )),
        ).add_to(fmap)
    return fmap


def _build_border_walls_map() -> folium.Map:
    """Build map showing border walls and fences as polylines."""
    fmap = folium.Map(location=[30, 30], zoom_start=3,
                      tiles="CartoDB dark_matter")
    for w in BORDER_WALLS:
        folium.PolyLine(
            locations=w["coords"],
            color=w["color"], weight=4,
            opacity=0.9,
            popup=folium.Popup(
                f"<b>{escape(w['name'])}</b><br>"
                f"Countries: {escape(w['countries'])}<br>"
                f"Length: {w['length_km']} km<br>"
                f"Built: {w['year_start']}-{w['year_latest']}<br>"
                f"Status: {escape(w['status'])}",
                max_width=280),
        ).add_to(fmap)
        mid_idx = len(w["coords"]) // 2
        folium.Marker(
            location=w["coords"][mid_idx],
            icon=folium.DivIcon(html=(
                f"<div style='font-size:9px;color:{w['color']};text-align:center;"
                f"text-shadow:1px 1px 2px #000;white-space:nowrap;'>"
                f"{escape(w['name'][:30])}</div>"
            )),
        ).add_to(fmap)
    return fmap


def _build_alliances_map(selected_alliance: str) -> folium.Map:
    """Build map showing members of a selected military alliance."""
    fmap = folium.Map(location=[30, 20], zoom_start=2,
                      tiles="CartoDB dark_matter")
    alliance = None
    for a in MILITARY_ALLIANCES:
        if a["name"] == selected_alliance:
            alliance = a
            break
    if alliance is None:
        return fmap
    for i, coord in enumerate(alliance["member_coords"]):
        member_name = alliance["members"][i] if i < len(alliance["members"]) else "Member"
        folium.CircleMarker(
            location=coord,
            radius=9, color=alliance["color"], fill=True,
            fill_color=alliance["color"], fill_opacity=0.75,
            popup=folium.Popup(
                f"<b>{escape(str(member_name))}</b><br>"
                f"Alliance: {escape(alliance['name'])}<br>"
                f"Founded: {alliance['founded']}",
                max_width=220),
        ).add_to(fmap)
    # Draw connecting lines between members
    if len(alliance["member_coords"]) > 1:
        for i in range(len(alliance["member_coords"])):
            for j in range(i + 1, len(alliance["member_coords"])):
                folium.PolyLine(
                    locations=[alliance["member_coords"][i],
                               alliance["member_coords"][j]],
                    color=alliance["color"], weight=1,
                    opacity=0.25, dash_array="5",
                ).add_to(fmap)
    return fmap


def _build_arms_trade_map(selected_exporters: list[str]) -> folium.Map:
    """Build flow-line map for arms trade routes."""
    fmap = folium.Map(location=[25, 40], zoom_start=2,
                      tiles="CartoDB dark_matter")
    volume_weight = {"Very High": 5, "High": 3.5, "Medium": 2, "Low": 1}
    for r in ARMS_TRADE_ROUTES:
        if selected_exporters and r["exporter"] not in selected_exporters:
            continue
        weight = volume_weight.get(r["volume"], 2)
        folium.PolyLine(
            locations=[[r["ex_lat"], r["ex_lon"]],
                        [r["im_lat"], r["im_lon"]]],
            color=r["color"], weight=weight,
            opacity=0.7, dash_array="8",
            popup=folium.Popup(
                f"<b>{escape(r['exporter'])} &#8594; {escape(r['importer'])}</b><br>"
                f"Volume: {escape(r['volume'])}<br>"
                f"Value: ${r['value_bn']}B<br>"
                f"Equipment: {escape(r['equipment'])}",
                max_width=300),
        ).add_to(fmap)
        # Importer marker
        folium.CircleMarker(
            location=[r["im_lat"], r["im_lon"]],
            radius=5, color=r["color"], fill=True,
            fill_color=r["color"], fill_opacity=0.7,
        ).add_to(fmap)
    # Exporter markers (larger)
    seen_exporters = set()
    for r in ARMS_TRADE_ROUTES:
        if selected_exporters and r["exporter"] not in selected_exporters:
            continue
        if r["exporter"] not in seen_exporters:
            seen_exporters.add(r["exporter"])
            folium.CircleMarker(
                location=[r["ex_lat"], r["ex_lon"]],
                radius=10, color=r["color"], fill=True,
                fill_color=r["color"], fill_opacity=0.9,
                popup=folium.Popup(
                    f"<b>Exporter: {escape(r['exporter'])}</b>",
                    max_width=200),
            ).add_to(fmap)
    return fmap


def _build_conflict_map(severity_filter: list[str]) -> folium.Map:
    """Build map showing active conflict zones."""
    fmap = folium.Map(location=[20, 30], zoom_start=2,
                      tiles="CartoDB dark_matter")
    for c in CONFLICT_ZONES:
        if severity_filter and c["severity"] not in severity_filter:
            continue
        folium.Circle(
            location=[c["lat"], c["lon"]],
            radius=c["radius"] * 20000,
            color=c["color"], fill=True,
            fill_color=c["color"], fill_opacity=0.3,
            popup=folium.Popup(
                f"<b>{escape(c['name'])}</b><br>"
                f"Type: {escape(c['type'])}<br>"
                f"Since: {c['start_year']}<br>"
                f"Parties: {escape(c['parties'])}<br>"
                f"Severity: {escape(c['severity'])}",
                max_width=300),
        ).add_to(fmap)
        folium.Marker(
            location=[c["lat"], c["lon"]],
            icon=folium.DivIcon(html=(
                f"<div style='font-size:9px;color:{c['color']};text-align:center;"
                f"text-shadow:1px 1px 2px #000;white-space:nowrap;'>"
                f"{escape(c['name'][:25])}</div>"
            )),
        ).add_to(fmap)
    return fmap


def _build_dmz_map() -> folium.Map:
    """Build map showing demilitarized zones."""
    fmap = folium.Map(location=[35, 40], zoom_start=3,
                      tiles="CartoDB dark_matter")
    for d in DEMILITARIZED_ZONES:
        # Draw polygon area
        if len(d["polygon"]) >= 3:
            folium.Polygon(
                locations=d["polygon"],
                color=d["color"], fill=True,
                fill_color=d["color"], fill_opacity=0.3,
                weight=2,
            ).add_to(fmap)
        # Draw center line
        folium.PolyLine(
            locations=d["coords"],
            color=d["color"], weight=3,
            opacity=0.9,
            popup=folium.Popup(
                f"<b>{escape(d['name'])}</b><br>"
                f"Location: {escape(d['location'])}<br>"
                f"Width: {d['width_km']} km | Length: {d['length_km']} km<br>"
                f"Established: {d['year']}<br>"
                f"Status: {escape(d['status'])}<br>"
                f"Parties: {escape(d['parties'])}",
                max_width=300),
        ).add_to(fmap)
        # Label
        mid_idx = len(d["coords"]) // 2
        folium.Marker(
            location=d["coords"][mid_idx],
            icon=folium.DivIcon(html=(
                f"<div style='font-size:9px;color:{d['color']};text-align:center;"
                f"text-shadow:1px 1px 2px #000;white-space:nowrap;'>"
                f"{escape(d['name'][:30])}</div>"
            )),
        ).add_to(fmap)
    return fmap


# =====================================================================
# CHART BUILDERS
# =====================================================================
def _build_warhead_chart() -> plt.Figure:
    """Bar chart of nuclear warheads by country."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    countries = [n["country"] for n in NUCLEAR_POWERS]
    warheads = [n["warheads"] for n in NUCLEAR_POWERS]
    colors = ["#ef4444", "#dc2626", "#3b82f6", "#f59e0b", "#10b981",
              "#f97316", "#8b5cf6", "#06b6d4", "#ec4899"]
    bars = ax.barh(countries, warheads, color=colors[:len(countries)])
    ax.set_xlabel("Estimated Warheads", color="#8b97b0", fontsize=11)
    ax.set_title("Nuclear Warheads by Country", color="#e8ecf4",
                 fontsize=14, fontweight="bold")
    ax.tick_params(colors="#8b97b0")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    for bar, count in zip(bars, warheads):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
                f"{count:,}", va="center", color="#e8ecf4", fontsize=10)
    fig.tight_layout()
    return fig


def _build_walls_length_chart() -> plt.Figure:
    """Bar chart of border wall lengths."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    sorted_walls = sorted(BORDER_WALLS, key=lambda w: w["length_km"], reverse=True)
    names = [w["name"][:30] for w in sorted_walls]
    lengths = [w["length_km"] for w in sorted_walls]
    colors = [w["color"] for w in sorted_walls]
    bars = ax.barh(names, lengths, color=colors)
    ax.set_xlabel("Length (km)", color="#8b97b0", fontsize=11)
    ax.set_title("Border Walls & Fences by Length", color="#e8ecf4",
                 fontsize=14, fontweight="bold")
    ax.tick_params(colors="#8b97b0")
    ax.tick_params(axis="y", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    for bar, length in zip(bars, lengths):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
                f"{length:,} km", va="center", color="#e8ecf4", fontsize=9)
    fig.tight_layout()
    return fig


def _build_arms_volume_chart() -> plt.Figure:
    """Bar chart of arms trade volumes by exporter."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    exporter_totals: dict[str, float] = {}
    exporter_colors: dict[str, str] = {}
    for r in ARMS_TRADE_ROUTES:
        exporter_totals[r["exporter"]] = (
            exporter_totals.get(r["exporter"], 0) + r["value_bn"]
        )
        exporter_colors[r["exporter"]] = r["color"]
    sorted_exp = sorted(exporter_totals.items(), key=lambda x: x[1], reverse=True)
    names = [e[0] for e in sorted_exp]
    values = [e[1] for e in sorted_exp]
    colors = [exporter_colors[n] for n in names]
    bars = ax.barh(names, values, color=colors)
    ax.set_xlabel("Total Trade Value ($B)", color="#8b97b0", fontsize=11)
    ax.set_title("Arms Export Volume by Country", color="#e8ecf4",
                 fontsize=14, fontweight="bold")
    ax.tick_params(colors="#8b97b0")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"${val:.1f}B", va="center", color="#e8ecf4", fontsize=10)
    fig.tight_layout()
    return fig


def _build_conflict_timeline_chart() -> plt.Figure:
    """Scatter chart showing conflict start years and severity."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    severity_y = {"High intensity": 3, "Medium intensity": 2,
                  "Low intensity": 1, "Post-conflict": 0.5}
    for c in CONFLICT_ZONES:
        y_val = severity_y.get(c["severity"], 1)
        ax.scatter(c["start_year"], y_val, s=120, color=c["color"],
                   alpha=0.8, edgecolors="#e8ecf4", linewidths=0.5, zorder=3)
        ax.annotate(c["name"][:18], (c["start_year"], y_val),
                    textcoords="offset points", xytext=(5, 5),
                    fontsize=7, color="#8b97b0", alpha=0.8)
    ax.set_xlabel("Start Year", color="#8b97b0", fontsize=11)
    ax.set_ylabel("Severity", color="#8b97b0", fontsize=11)
    ax.set_title("Conflict Zones by Start Year & Severity", color="#e8ecf4",
                 fontsize=14, fontweight="bold")
    ax.set_yticks([0.5, 1, 2, 3])
    ax.set_yticklabels(["Post-conflict", "Low", "Medium", "High"])
    ax.tick_params(colors="#8b97b0")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, alpha=0.15, color="#2a3550")
    fig.tight_layout()
    return fig


def _build_alliance_timeline_chart() -> plt.Figure:
    """Gantt-style chart of alliance timelines."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    current_year = 2025
    for i, a in enumerate(MILITARY_ALLIANCES):
        start = a["founded"]
        end = a["dissolved"] if a["dissolved"] else current_year
        duration = end - start
        ax.barh(i, duration, left=start, color=a["color"], height=0.6,
                alpha=0.8, edgecolor="#2a3550")
        label = a["name"]
        if a["dissolved"]:
            label += f" (dissolved {a['dissolved']})"
        ax.text(start + duration / 2, i, label, va="center", ha="center",
                fontsize=8, color="#e8ecf4", fontweight="bold")
    ax.set_xlabel("Year", color="#8b97b0", fontsize=11)
    ax.set_title("Military Alliance Timelines", color="#e8ecf4",
                 fontsize=14, fontweight="bold")
    ax.set_yticks(range(len(MILITARY_ALLIANCES)))
    ax.set_yticklabels([a["name"] for a in MILITARY_ALLIANCES],
                       fontsize=8, color="#8b97b0")
    ax.tick_params(colors="#8b97b0")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, axis="x", alpha=0.15, color="#2a3550")
    fig.tight_layout()
    return fig


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_military_maps_tab():
    """Render the Military & Geopolitical Maps tab in the Streamlit app."""
    st.markdown(
        '<div class="tab-header red"><h4>Military &amp; Geopolitical Maps</h4>'
        '<p>10 thematic maps: bases, alliances, nuclear arsenals, disputes, '
        'borders, arms trade, conflicts &amp; DMZs</p></div>',
        unsafe_allow_html=True,
    )

    selected_map = st.radio(
        "Select Map Type",
        MAP_TYPES,
        horizontal=True,
        key="military_map_type",
    )

    st.markdown("---")

    # =================================================================
    # 1. MILITARY BASES
    # =================================================================
    if selected_map == "Military Bases":
        st.markdown(
            "<p style='color:#8b97b0;'>Search for military installations "
            "(barracks, airfields, naval bases, ranges, training areas) using "
            "OpenStreetMap data via Overpass API.</p>",
            unsafe_allow_html=True,
        )
        region = st.selectbox(
            "Select Region",
            list(MILITARY_BASE_REGIONS.keys()),
            key="mil_base_region",
        )
        base_types = st.multiselect(
            "Filter by Type (leave empty for all)",
            ["barracks", "airfield", "naval_base", "range", "training_area",
             "danger_area", "bunker", "checkpoint", "office", "ammunition"],
            default=[],
            key="mil_base_types",
        )
        if st.button("Search Military Bases", key="btn_mil_bases"):
            with st.spinner("Querying Overpass API..."):
                bases = fetch_military_bases(region)
            if base_types:
                bases = [b for b in bases if b["type"] in base_types]
            c1, c2, c3 = st.columns(3)
            c1.metric("Installations Found", len(bases))
            types_found = len(set(b["type"] for b in bases)) if bases else 0
            c2.metric("Distinct Types", types_found)
            c3.metric("Region", region)

            fmap = _build_military_bases_map(bases)
            components.html(fmap._repr_html_(), height=550)

            if bases:
                st.subheader("Military Installations Data")
                df = pd.DataFrame(bases)
                st.dataframe(df, width="stretch")
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Military Bases CSV", csv,
                    "military_bases.csv", "text/csv",
                    key="dl_mil_bases",
                )
            else:
                st.info("No military installations found in this region. "
                        "Try a different region or remove type filters.")

    # =================================================================
    # 2. NATO vs NON-NATO
    # =================================================================
    elif selected_map == "NATO vs Non-NATO":
        st.markdown(
            "<p style='color:#8b97b0;'>NATO (blue) vs CSTO (red) member "
            "states with join year. Shows the major collective defense "
            "blocs on a global map.</p>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("NATO Members", len(NATO_MEMBERS))
        c2.metric("CSTO Members", len(CSTO_MEMBERS))
        c3.metric("Latest NATO Expansion", "Sweden (2024)")

        fmap = _build_nato_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("NATO Members")
        df_nato = get_nato_data()[["country", "code", "year"]]
        df_nato.columns = ["Country", "Code", "Joined"]
        st.dataframe(df_nato, width="stretch")

        st.subheader("CSTO Members")
        df_csto = get_csto_data()[["country", "code", "year"]]
        df_csto.columns = ["Country", "Code", "Joined"]
        st.dataframe(df_csto, width="stretch")

        # Combined download
        rows = []
        for m in NATO_MEMBERS:
            rows.append({"Alliance": "NATO", "Country": m["country"],
                         "Code": m["code"], "Year Joined": m["year"]})
        for m in CSTO_MEMBERS:
            rows.append({"Alliance": "CSTO", "Country": m["country"],
                         "Code": m["code"], "Year Joined": m["year"]})
        df_all = pd.DataFrame(rows)
        csv = df_all.to_csv(index=False).encode("utf-8")
        st.download_button("Download Alliances CSV", csv,
                           "nato_csto_members.csv", "text/csv",
                           key="dl_nato_csto")

    # =================================================================
    # 3. NUCLEAR POWERS
    # =================================================================
    elif selected_map == "Nuclear Powers":
        st.markdown(
            "<p style='color:#8b97b0;'>Nine nuclear-armed states shown as "
            "graduated circles proportional to estimated warhead counts. "
            "Data based on publicly available estimates.</p>",
            unsafe_allow_html=True,
        )
        total_warheads = sum(n["warheads"] for n in NUCLEAR_POWERS)
        c1, c2, c3 = st.columns(3)
        c1.metric("Nuclear States", len(NUCLEAR_POWERS))
        c2.metric("Total Warheads (est.)", f"~{total_warheads:,}")
        c3.metric("Largest Arsenal", "Russia (~6,257)")

        fmap = _build_nuclear_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Warhead Distribution")
        fig = _build_warhead_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Nuclear Powers Data")
        df = get_nuclear_data()[["country", "warheads", "first_test", "status"]]
        df.columns = ["Country", "Warheads (est.)", "First Test", "Status"]
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Nuclear Powers CSV", csv,
                           "nuclear_powers.csv", "text/csv",
                           key="dl_nuclear")

    # =================================================================
    # 4. DISPUTED TERRITORIES
    # =================================================================
    elif selected_map == "Disputed Territories":
        st.markdown(
            "<p style='color:#8b97b0;'>Over 30 disputed territories worldwide "
            "shown as colored polygons with claimant and status info. Includes "
            "Kashmir, Crimea, Western Sahara, South China Sea, and more.</p>",
            unsafe_allow_html=True,
        )
        territory_names = [d["name"] for d in DISPUTED_TERRITORIES]
        selected = st.multiselect(
            "Filter Territories (leave empty for all)",
            territory_names,
            default=[],
            key="mil_disputed_filter",
        )
        shown = selected if selected else territory_names
        c1, c2 = st.columns(2)
        c1.metric("Total Disputed Areas", len(DISPUTED_TERRITORIES))
        c2.metric("Showing", len(shown))

        fmap = _build_disputed_map(selected)
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Disputed Territories Details")
        df = get_disputed_data()
        if selected:
            df = df[df["Name"].isin(selected)]
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Disputed Territories CSV", csv,
                           "disputed_territories.csv", "text/csv",
                           key="dl_disputed")

    # =================================================================
    # 5. MARITIME BOUNDARIES
    # =================================================================
    elif selected_map == "Maritime Boundaries":
        st.markdown(
            "<p style='color:#8b97b0;'>Major Exclusive Economic Zone (EEZ) "
            "disputes and contested maritime boundaries worldwide. Includes "
            "South China Sea, Eastern Mediterranean, Arctic, and more.</p>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        c1.metric("Maritime Dispute Zones", len(MARITIME_ZONES))
        c2.metric("Most Contested", "South China Sea")

        fmap = _build_maritime_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Maritime Boundary Disputes")
        df = get_maritime_data()
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Maritime Boundaries CSV", csv,
                           "maritime_boundaries.csv", "text/csv",
                           key="milm_dl_maritime")

    # =================================================================
    # 6. BORDER WALLS & FENCES
    # =================================================================
    elif selected_map == "Border Walls & Fences":
        st.markdown(
            "<p style='color:#8b97b0;'>Existing and planned border barriers "
            "worldwide including walls, fences, and security barriers. Shows "
            "location, length, year of construction, and current status.</p>",
            unsafe_allow_html=True,
        )
        total_length = sum(w["length_km"] for w in BORDER_WALLS)
        c1, c2, c3 = st.columns(3)
        c1.metric("Border Barriers", len(BORDER_WALLS))
        c2.metric("Total Length", f"{total_length:,} km")
        c3.metric("Longest", "India-Bangladesh (3,200 km)")

        fmap = _build_border_walls_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Border Wall Lengths")
        fig = _build_walls_length_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Border Walls & Fences Data")
        df = get_border_walls_data()
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Border Walls CSV", csv,
                           "border_walls.csv", "text/csv",
                           key="milm_dl_walls")

    # =================================================================
    # 7. MILITARY ALLIANCES TIMELINE
    # =================================================================
    elif selected_map == "Military Alliances Timeline":
        st.markdown(
            "<p style='color:#8b97b0;'>Major military alliance blocs from "
            "1941 to present, including NATO, Warsaw Pact, SEATO, ANZUS, "
            "Five Eyes, Quad, AUKUS, CSTO, SCO, and AU Peace & Security.</p>",
            unsafe_allow_html=True,
        )
        alliance_names = [a["name"] for a in MILITARY_ALLIANCES]
        selected_alliance = st.selectbox(
            "Select Alliance to Map",
            alliance_names,
            key="mil_alliance_select",
        )
        active_count = sum(1 for a in MILITARY_ALLIANCES if a["dissolved"] is None)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Alliances", len(MILITARY_ALLIANCES))
        c2.metric("Currently Active", active_count)
        sel_a = next((a for a in MILITARY_ALLIANCES if a["name"] == selected_alliance), None)
        c3.metric("Members", len(sel_a["members"]) if sel_a else 0)

        st.subheader("Alliance Timeline")
        fig = _build_alliance_timeline_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader(f"{selected_alliance} - Member Locations")
        fmap = _build_alliances_map(selected_alliance)
        components.html(fmap._repr_html_(), height=550)

        st.subheader("All Alliances Data")
        df = get_alliances_data()
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Alliances CSV", csv,
                           "military_alliances.csv", "text/csv",
                           key="dl_alliances")

    # =================================================================
    # 8. ARMS TRADE ROUTES
    # =================================================================
    elif selected_map == "Arms Trade Routes":
        st.markdown(
            "<p style='color:#8b97b0;'>Major global arms trade flows between "
            "exporters and importers. Based on publicly available SIPRI data "
            "estimates. Line weight indicates trade volume.</p>",
            unsafe_allow_html=True,
        )
        exporters = sorted(set(r["exporter"] for r in ARMS_TRADE_ROUTES))
        selected_exporters = st.multiselect(
            "Filter by Exporter (leave empty for all)",
            exporters,
            default=[],
            key="mil_arms_exporters",
        )
        total_value = sum(r["value_bn"] for r in ARMS_TRADE_ROUTES)
        shown_routes = ARMS_TRADE_ROUTES
        if selected_exporters:
            shown_routes = [r for r in ARMS_TRADE_ROUTES
                           if r["exporter"] in selected_exporters]
        shown_value = sum(r["value_bn"] for r in shown_routes)
        c1, c2, c3 = st.columns(3)
        c1.metric("Trade Routes Shown", len(shown_routes))
        c2.metric("Shown Trade Value", f"${shown_value:.1f}B")
        c3.metric("Total Global Value", f"${total_value:.1f}B")

        fmap = _build_arms_trade_map(selected_exporters)
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Export Volumes by Country")
        fig = _build_arms_volume_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Arms Trade Routes Data")
        df = get_arms_trade_data()
        if selected_exporters:
            df = df[df["Exporter"].isin(selected_exporters)]
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Arms Trade CSV", csv,
                           "arms_trade_routes.csv", "text/csv",
                           key="dl_arms")

    # =================================================================
    # 9. CONFLICT ZONES
    # =================================================================
    elif selected_map == "Conflict Zones":
        st.markdown(
            "<p style='color:#8b97b0;'>Currently active conflict zones "
            "worldwide (~25 conflicts) with type classification, start year, "
            "belligerent parties, and severity assessment.</p>",
            unsafe_allow_html=True,
        )
        severities = sorted(set(c["severity"] for c in CONFLICT_ZONES))
        severity_filter = st.multiselect(
            "Filter by Severity (leave empty for all)",
            severities,
            default=[],
            key="mil_conflict_severity",
        )
        shown = CONFLICT_ZONES
        if severity_filter:
            shown = [c for c in CONFLICT_ZONES if c["severity"] in severity_filter]
        high_count = sum(1 for c in CONFLICT_ZONES if c["severity"] == "High intensity")
        c1, c2, c3 = st.columns(3)
        c1.metric("Conflicts Shown", len(shown))
        c2.metric("High Intensity", high_count)
        c3.metric("Total Tracked", len(CONFLICT_ZONES))

        fmap = _build_conflict_map(severity_filter)
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Conflict Timeline")
        fig = _build_conflict_timeline_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Conflict Zones Data")
        df = get_conflict_data()
        if severity_filter:
            df = df[df["Severity"].isin(severity_filter)]
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Conflicts CSV", csv,
                           "conflict_zones.csv", "text/csv",
                           key="milm_dl_conflicts")

    # =================================================================
    # 10. DEMILITARIZED ZONES
    # =================================================================
    elif selected_map == "Demilitarized Zones":
        st.markdown(
            "<p style='color:#8b97b0;'>Historical and active demilitarized "
            "zones (DMZs) worldwide, including the Korean DMZ, Cyprus Green "
            "Line, Golan Heights UNDOF, Antarctic Treaty Zone, and more.</p>",
            unsafe_allow_html=True,
        )
        active_count = sum(
            1 for d in DEMILITARIZED_ZONES if "Active" in d["status"]
        )
        historical_count = len(DEMILITARIZED_ZONES) - active_count
        c1, c2, c3 = st.columns(3)
        c1.metric("Total DMZs", len(DEMILITARIZED_ZONES))
        c2.metric("Currently Active", active_count)
        c3.metric("Historical", historical_count)

        fmap = _build_dmz_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Demilitarized Zones Data")
        df = get_dmz_data()
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download DMZs CSV", csv,
                           "demilitarized_zones.csv", "text/csv",
                           key="milm_dl_dmz")
