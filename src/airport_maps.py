# -*- coding: utf-8 -*-
"""
Airports & Aviation Maps module for TerraScout AI.
Explores world airports, busiest hubs, extreme airfields, aviation history,
military airbases, abandoned airfields, airline hubs, heliports, spaceports,
and air traffic control zones using curated datasets and the Overpass API.
All data sources are free and require no API key.
"""

import io
import logging
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

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ======================================================================
# THEME CONSTANTS
# ======================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_AMBER = "#f59e0b"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"
ACCENT_PINK = "#ec4899"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"

MAP_TILES = "CartoDB dark_matter"
MAP_HEIGHT = 500

# ======================================================================
# MAP MODE DEFINITIONS
# ======================================================================
MAP_MODES = [
    "World's Busiest Airports",
    "Longest Runways",
    "Extreme Airports",
    "Aviation History",
    "Military Airbases",
    "Abandoned Airfields",
    "Airline Hubs",
    "Helicopter & Heliports",
    "Space Ports & Launch Sites",
    "Air Traffic Control",
]

# ======================================================================
# 1. WORLD'S BUSIEST AIRPORTS (Top 50 by passengers, 2023-2024 data)
# ======================================================================
BUSIEST_AIRPORTS = [
    {"name": "Hartsfield-Jackson Atlanta Intl", "iata": "ATL", "city": "Atlanta", "country": "USA", "lat": 33.6407, "lon": -84.4277, "pax_millions": 104.7, "rank": 1},
    {"name": "Dubai International", "iata": "DXB", "city": "Dubai", "country": "UAE", "lat": 25.2532, "lon": 55.3657, "pax_millions": 92.0, "rank": 2},
    {"name": "Dallas/Fort Worth Intl", "iata": "DFW", "city": "Dallas", "country": "USA", "lat": 32.8998, "lon": -97.0403, "pax_millions": 81.8, "rank": 3},
    {"name": "London Heathrow", "iata": "LHR", "city": "London", "country": "UK", "lat": 51.4700, "lon": -0.4543, "pax_millions": 79.2, "rank": 4},
    {"name": "Denver International", "iata": "DEN", "city": "Denver", "country": "USA", "lat": 39.8561, "lon": -104.6737, "pax_millions": 77.8, "rank": 5},
    {"name": "Istanbul Airport", "iata": "IST", "city": "Istanbul", "country": "Turkey", "lat": 41.2753, "lon": 28.7519, "pax_millions": 76.0, "rank": 6},
    {"name": "Los Angeles Intl", "iata": "LAX", "city": "Los Angeles", "country": "USA", "lat": 33.9425, "lon": -118.4081, "pax_millions": 75.1, "rank": 7},
    {"name": "Chicago O'Hare Intl", "iata": "ORD", "city": "Chicago", "country": "USA", "lat": 41.9742, "lon": -87.9073, "pax_millions": 74.0, "rank": 8},
    {"name": "Rajiv Gandhi Intl", "iata": "DEL", "city": "New Delhi", "country": "India", "lat": 28.5562, "lon": 77.1000, "pax_millions": 72.3, "rank": 9},
    {"name": "Paris Charles de Gaulle", "iata": "CDG", "city": "Paris", "country": "France", "lat": 49.0097, "lon": 2.5479, "pax_millions": 69.5, "rank": 10},
    {"name": "Amsterdam Schiphol", "iata": "AMS", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3105, "lon": 4.7683, "pax_millions": 62.0, "rank": 11},
    {"name": "Guangzhou Baiyun Intl", "iata": "CAN", "city": "Guangzhou", "country": "China", "lat": 23.3924, "lon": 113.2988, "pax_millions": 61.3, "rank": 12},
    {"name": "Frankfurt Airport", "iata": "FRA", "city": "Frankfurt", "country": "Germany", "lat": 50.0379, "lon": 8.5622, "pax_millions": 59.4, "rank": 13},
    {"name": "Cancun International", "iata": "CUN", "city": "Cancun", "country": "Mexico", "lat": 21.0365, "lon": -86.8771, "pax_millions": 58.7, "rank": 14},
    {"name": "Madrid Barajas", "iata": "MAD", "city": "Madrid", "country": "Spain", "lat": 40.4936, "lon": -3.5668, "pax_millions": 57.9, "rank": 15},
    {"name": "Tokyo Haneda", "iata": "HND", "city": "Tokyo", "country": "Japan", "lat": 35.5494, "lon": 139.7798, "pax_millions": 57.5, "rank": 16},
    {"name": "Charlotte Douglas Intl", "iata": "CLT", "city": "Charlotte", "country": "USA", "lat": 35.2140, "lon": -80.9431, "pax_millions": 56.4, "rank": 17},
    {"name": "Orlando International", "iata": "MCO", "city": "Orlando", "country": "USA", "lat": 28.4312, "lon": -81.3081, "pax_millions": 55.6, "rank": 18},
    {"name": "Singapore Changi", "iata": "SIN", "city": "Singapore", "country": "Singapore", "lat": 1.3644, "lon": 103.9915, "pax_millions": 55.4, "rank": 19},
    {"name": "Seattle-Tacoma Intl", "iata": "SEA", "city": "Seattle", "country": "USA", "lat": 47.4502, "lon": -122.3088, "pax_millions": 52.3, "rank": 20},
    {"name": "Incheon International", "iata": "ICN", "city": "Seoul", "country": "South Korea", "lat": 37.4602, "lon": 126.4407, "pax_millions": 51.8, "rank": 21},
    {"name": "Bangkok Suvarnabhumi", "iata": "BKK", "city": "Bangkok", "country": "Thailand", "lat": 13.6900, "lon": 100.7501, "pax_millions": 51.5, "rank": 22},
    {"name": "Shanghai Pudong Intl", "iata": "PVG", "city": "Shanghai", "country": "China", "lat": 31.1443, "lon": 121.8083, "pax_millions": 50.3, "rank": 23},
    {"name": "Miami International", "iata": "MIA", "city": "Miami", "country": "USA", "lat": 25.7959, "lon": -80.2870, "pax_millions": 49.6, "rank": 24},
    {"name": "John F. Kennedy Intl", "iata": "JFK", "city": "New York", "country": "USA", "lat": 40.6413, "lon": -73.7781, "pax_millions": 48.9, "rank": 25},
    {"name": "San Francisco Intl", "iata": "SFO", "city": "San Francisco", "country": "USA", "lat": 37.6213, "lon": -122.3790, "pax_millions": 48.5, "rank": 26},
    {"name": "Barcelona El Prat", "iata": "BCN", "city": "Barcelona", "country": "Spain", "lat": 41.2974, "lon": 2.0833, "pax_millions": 47.8, "rank": 27},
    {"name": "Beijing Capital Intl", "iata": "PEK", "city": "Beijing", "country": "China", "lat": 40.0799, "lon": 116.6031, "pax_millions": 47.2, "rank": 28},
    {"name": "Newark Liberty Intl", "iata": "EWR", "city": "Newark", "country": "USA", "lat": 40.6895, "lon": -74.1745, "pax_millions": 46.8, "rank": 29},
    {"name": "Mexico City Intl", "iata": "MEX", "city": "Mexico City", "country": "Mexico", "lat": 19.4363, "lon": -99.0721, "pax_millions": 46.5, "rank": 30},
    {"name": "Chhatrapati Shivaji Intl", "iata": "BOM", "city": "Mumbai", "country": "India", "lat": 19.0896, "lon": 72.8656, "pax_millions": 45.7, "rank": 31},
    {"name": "Rome Fiumicino", "iata": "FCO", "city": "Rome", "country": "Italy", "lat": 41.8003, "lon": 12.2389, "pax_millions": 44.4, "rank": 32},
    {"name": "Munich Airport", "iata": "MUC", "city": "Munich", "country": "Germany", "lat": 48.3537, "lon": 11.7750, "pax_millions": 43.8, "rank": 33},
    {"name": "Las Vegas Harry Reid Intl", "iata": "LAS", "city": "Las Vegas", "country": "USA", "lat": 36.0840, "lon": -115.1537, "pax_millions": 43.5, "rank": 34},
    {"name": "Sydney Kingsford Smith", "iata": "SYD", "city": "Sydney", "country": "Australia", "lat": -33.9461, "lon": 151.1772, "pax_millions": 42.8, "rank": 35},
    {"name": "Antalya Airport", "iata": "AYT", "city": "Antalya", "country": "Turkey", "lat": 36.8987, "lon": 30.8005, "pax_millions": 42.3, "rank": 36},
    {"name": "Bogota El Dorado Intl", "iata": "BOG", "city": "Bogota", "country": "Colombia", "lat": 4.7016, "lon": -74.1469, "pax_millions": 41.9, "rank": 37},
    {"name": "Sao Paulo Guarulhos Intl", "iata": "GRU", "city": "Sao Paulo", "country": "Brazil", "lat": -23.4356, "lon": -46.4731, "pax_millions": 41.5, "rank": 38},
    {"name": "Kuala Lumpur Intl", "iata": "KUL", "city": "Kuala Lumpur", "country": "Malaysia", "lat": 2.7456, "lon": 101.7099, "pax_millions": 41.0, "rank": 39},
    {"name": "Zurich Airport", "iata": "ZRH", "city": "Zurich", "country": "Switzerland", "lat": 47.4647, "lon": 8.5492, "pax_millions": 40.2, "rank": 40},
    {"name": "Phoenix Sky Harbor Intl", "iata": "PHX", "city": "Phoenix", "country": "USA", "lat": 33.4373, "lon": -112.0078, "pax_millions": 39.8, "rank": 41},
    {"name": "Doha Hamad Intl", "iata": "DOH", "city": "Doha", "country": "Qatar", "lat": 25.2731, "lon": 51.6081, "pax_millions": 39.5, "rank": 42},
    {"name": "Lisbon Humberto Delgado", "iata": "LIS", "city": "Lisbon", "country": "Portugal", "lat": 38.7742, "lon": -9.1342, "pax_millions": 39.1, "rank": 43},
    {"name": "Jakarta Soekarno-Hatta Intl", "iata": "CGK", "city": "Jakarta", "country": "Indonesia", "lat": -6.1256, "lon": 106.6558, "pax_millions": 38.7, "rank": 44},
    {"name": "Manila Ninoy Aquino Intl", "iata": "MNL", "city": "Manila", "country": "Philippines", "lat": 14.5086, "lon": 121.0194, "pax_millions": 38.3, "rank": 45},
    {"name": "Toronto Pearson Intl", "iata": "YYZ", "city": "Toronto", "country": "Canada", "lat": 43.6777, "lon": -79.6248, "pax_millions": 37.8, "rank": 46},
    {"name": "Boston Logan Intl", "iata": "BOS", "city": "Boston", "country": "USA", "lat": 42.3656, "lon": -71.0096, "pax_millions": 37.4, "rank": 47},
    {"name": "Minneapolis-Saint Paul Intl", "iata": "MSP", "city": "Minneapolis", "country": "USA", "lat": 44.8848, "lon": -93.2223, "pax_millions": 36.9, "rank": 48},
    {"name": "Hong Kong International", "iata": "HKG", "city": "Hong Kong", "country": "China", "lat": 22.3080, "lon": 113.9185, "pax_millions": 36.5, "rank": 49},
    {"name": "Palma de Mallorca", "iata": "PMI", "city": "Palma", "country": "Spain", "lat": 39.5517, "lon": 2.7388, "pax_millions": 36.1, "rank": 50},
]

# ======================================================================
# 2. LONGEST RUNWAYS IN THE WORLD
# ======================================================================
LONGEST_RUNWAYS = [
    {"name": "Qamdo Bamda Airport", "iata": "BPX", "country": "China", "lat": 30.5536, "lon": 97.1083, "length_m": 5500, "length_ft": 18045, "elevation_m": 4334, "notes": "World's longest runway; highest commercial airport"},
    {"name": "Ulyanovsk Vostochny Airport", "iata": "ULY", "country": "Russia", "lat": 54.4010, "lon": 48.8027, "length_m": 5000, "length_ft": 16404, "elevation_m": 78, "notes": "Built for Buran space shuttle landings"},
    {"name": "Zhukovsky International Airport", "iata": "ZIA", "country": "Russia", "lat": 55.5533, "lon": 38.1500, "length_m": 5403, "length_ft": 17727, "elevation_m": 118, "notes": "Former Soviet test facility; Gromov Flight Research Institute"},
    {"name": "Edwards Air Force Base", "iata": "EDW", "country": "USA", "lat": 34.9054, "lon": -117.8839, "length_m": 4580, "length_ft": 15024, "elevation_m": 702, "notes": "Space Shuttle alternate landing site; dry lakebed runways up to 12 km"},
    {"name": "Upington Airport", "iata": "UTN", "country": "South Africa", "lat": -28.3960, "lon": 21.2602, "length_m": 4900, "length_ft": 16076, "elevation_m": 836, "notes": "One of longest commercial runways in the Southern Hemisphere"},
    {"name": "Erbil International Airport", "iata": "EBL", "country": "Iraq", "lat": 36.2376, "lon": 43.9632, "length_m": 4800, "length_ft": 15748, "elevation_m": 411, "notes": "Built 2005; major Iraqi Kurdistan hub"},
    {"name": "Shigatse Peace Airport", "iata": "RKZ", "country": "China", "lat": 29.3519, "lon": 89.3114, "length_m": 5000, "length_ft": 16404, "elevation_m": 3782, "notes": "Second highest airport in China; high altitude requires long runway"},
    {"name": "Ramenskoye Airport", "iata": "---", "country": "Russia", "lat": 55.5667, "lon": 38.1500, "length_m": 5403, "length_ft": 17727, "elevation_m": 119, "notes": "Russia's primary flight test center"},
    {"name": "Denver International", "iata": "DEN", "country": "USA", "lat": 39.8561, "lon": -104.6737, "length_m": 4877, "length_ft": 16000, "elevation_m": 1655, "notes": "Longest commercial runway in North America; mile-high altitude"},
    {"name": "King Fahd International", "iata": "DMM", "country": "Saudi Arabia", "lat": 26.4712, "lon": 49.7979, "length_m": 4572, "length_ft": 15000, "elevation_m": 22, "notes": "World's largest airport by area (780 km2)"},
    {"name": "Madrid Barajas", "iata": "MAD", "country": "Spain", "lat": 40.4936, "lon": -3.5668, "length_m": 4350, "length_ft": 14272, "elevation_m": 610, "notes": "Longest runway in the European Union"},
    {"name": "Nagqu Dagring Airport", "iata": "NQG", "country": "China", "lat": 30.9715, "lon": 92.0670, "length_m": 4500, "length_ft": 14764, "elevation_m": 4436, "notes": "World's highest airport (4436m / 14,554ft)"},
    {"name": "Embraer Unidade Gaviao Peixoto", "iata": "---", "country": "Brazil", "lat": -21.7750, "lon": -48.4083, "length_m": 4967, "length_ft": 16296, "elevation_m": 542, "notes": "Embraer test facility; one of the longest runways in the Americas"},
    {"name": "Vandenberg SFB", "iata": "VBG", "country": "USA", "lat": 34.7373, "lon": -120.5840, "length_m": 4572, "length_ft": 15000, "elevation_m": 113, "notes": "Space launch facility with very long runway"},
    {"name": "Runway 14R/32L, O'Hare Intl", "iata": "ORD", "country": "USA", "lat": 41.9742, "lon": -87.9073, "length_m": 4014, "length_ft": 13171, "elevation_m": 204, "notes": "Longest runway at one of the world's busiest airports"},
]

# ======================================================================
# 3. EXTREME AIRPORTS
# ======================================================================
EXTREME_AIRPORTS = [
    {"name": "Tenzing-Hillary Airport (Lukla)", "iata": "LUA", "country": "Nepal", "lat": 27.6869, "lon": 86.7298, "elevation_m": 2845, "category": "Dangerous", "color": ACCENT_RED, "notes": "Gateway to Everest; 527m sloped runway, cliff at one end, mountain at the other"},
    {"name": "Juancho E. Yrausquin Airport", "iata": "SAB", "country": "Caribbean Netherlands", "lat": 17.6450, "lon": -63.2200, "elevation_m": 18, "category": "Shortest Runway", "color": ACCENT_ORANGE, "notes": "World's shortest commercial runway (400m); cliffs on three sides"},
    {"name": "Madeira Airport", "iata": "FNC", "country": "Portugal", "lat": 32.6940, "lon": -16.7745, "elevation_m": 59, "category": "Engineering Marvel", "color": ACCENT_CYAN, "notes": "Runway extended on 180 concrete columns over the ocean; extreme crosswinds"},
    {"name": "Courchevel Altiport", "iata": "CVF", "country": "France", "lat": 45.3967, "lon": 6.6347, "elevation_m": 2007, "category": "Mountain", "color": ACCENT_VIOLET, "notes": "537m runway with 18.5% gradient; featured in James Bond film"},
    {"name": "Princess Juliana Intl", "iata": "SXM", "country": "Sint Maarten", "lat": 18.0410, "lon": -63.1089, "elevation_m": 4, "category": "Beach Approach", "color": ACCENT_AMBER, "notes": "Famous Maho Beach approach — jets pass just meters over beachgoers"},
    {"name": "Paro Airport", "iata": "PBH", "country": "Bhutan", "lat": 27.4032, "lon": 89.4246, "elevation_m": 2235, "category": "Mountain Valley", "color": ACCENT_EMERALD, "notes": "Surrounded by 5,500m peaks; only 8 pilots in the world certified to land here"},
    {"name": "Barra Airport", "iata": "BRR", "country": "UK (Scotland)", "lat": 57.0228, "lon": -7.4431, "elevation_m": 0, "category": "Beach Runway", "color": ACCENT_AMBER, "notes": "Only airport where scheduled flights use a beach; tides determine operations"},
    {"name": "Ice Runway (McMurdo)", "iata": "---", "country": "Antarctica", "lat": -77.8541, "lon": 166.4690, "elevation_m": 0, "category": "Ice Runway", "color": ACCENT_BLUE, "notes": "Built annually on sea ice; supports C-17 Globemaster and LC-130 Hercules"},
    {"name": "Matekane Air Strip", "iata": "---", "country": "Lesotho", "lat": -29.4667, "lon": 28.8000, "elevation_m": 2286, "category": "Cliff Edge", "color": ACCENT_RED, "notes": "400m runway ending at a 600m cliff drop; aircraft must become airborne before the edge"},
    {"name": "Narsarsuaq Airport", "iata": "UAK", "country": "Greenland", "lat": 61.1605, "lon": -45.4250, "elevation_m": 34, "category": "Fjord Approach", "color": ACCENT_CYAN, "notes": "Approach through fjord between mountains; katabatic winds from ice cap"},
    {"name": "Toncontin International", "iata": "TGU", "country": "Honduras", "lat": 14.0609, "lon": -87.2172, "elevation_m": 1005, "category": "Dangerous", "color": ACCENT_RED, "notes": "Mountain approach requires sharp turn at low altitude; short runway with terrain on all sides"},
    {"name": "Gibraltar Airport", "iata": "GIB", "country": "Gibraltar", "lat": 36.1512, "lon": -5.3497, "elevation_m": 5, "category": "Road Crossing", "color": ACCENT_PINK, "notes": "Main road (Winston Churchill Avenue) crosses the runway; traffic stops for aircraft"},
    {"name": "Svalbard Airport, Longyearbyen", "iata": "LYR", "country": "Norway", "lat": 78.2461, "lon": 15.4656, "elevation_m": 28, "category": "Northernmost", "color": ACCENT_BLUE, "notes": "World's northernmost airport with public scheduled flights; permafrost challenges"},
    {"name": "Kansai International", "iata": "KIX", "country": "Japan", "lat": 34.4347, "lon": 135.2440, "elevation_m": 8, "category": "Artificial Island", "color": ACCENT_CYAN, "notes": "Built on artificial island in Osaka Bay; sinking 6cm/year; typhoon-resistant"},
    {"name": "Gustaf III Airport (St. Barts)", "iata": "SBH", "country": "France (Caribbean)", "lat": 17.9044, "lon": -62.8436, "elevation_m": 15, "category": "Short & Steep", "color": ACCENT_ORANGE, "notes": "650m runway; steep descent over hilltop road; only small aircraft permitted"},
    {"name": "Telluride Regional", "iata": "TEX", "country": "USA", "lat": 37.9536, "lon": -107.9086, "elevation_m": 2767, "category": "Highest in USA", "color": ACCENT_VIOLET, "notes": "Highest commercial airport in North America; mesa-top location with steep drop-offs"},
    {"name": "Pegasus Field (Antarctica)", "iata": "---", "country": "Antarctica", "lat": -77.9633, "lon": 166.5247, "elevation_m": 10, "category": "Ice Runway", "color": ACCENT_BLUE, "notes": "Permanent ice shelf runway for wheeled aircraft; Ross Ice Shelf location"},
    {"name": "Agatti Aerodrome", "iata": "AGX", "country": "India", "lat": 10.8237, "lon": 72.1761, "elevation_m": 3, "category": "Island Strip", "color": ACCENT_EMERALD, "notes": "Tiny coral island runway in Lakshadweep; ocean on both sides"},
]

# ======================================================================
# 4. AVIATION HISTORY MILESTONES
# ======================================================================
AVIATION_HISTORY = [
    {"event": "Wright Brothers First Flight", "year": 1903, "lat": 36.0148, "lon": -75.6680, "location": "Kill Devil Hills, North Carolina", "color": ACCENT_AMBER, "notes": "Dec 17, 1903 — Orville Wright flew 37m in 12 seconds; 4 flights that day, max 260m"},
    {"event": "Louis Bleriot Crosses English Channel", "year": 1909, "lat": 50.9464, "lon": 1.8580, "location": "Calais to Dover", "color": ACCENT_CYAN, "notes": "Jul 25, 1909 — First heavier-than-air Channel crossing in 37 minutes"},
    {"event": "First Transcontinental US Flight", "year": 1911, "lat": 40.7128, "lon": -74.0060, "location": "New York to Pasadena", "color": ACCENT_VIOLET, "notes": "Calbraith Perry Rodgers; 84 days with 70+ stops and multiple crashes"},
    {"event": "Red Baron's Last Flight", "year": 1918, "lat": 49.8617, "lon": 2.7008, "location": "Vaux-sur-Somme, France", "color": ACCENT_RED, "notes": "Apr 21, 1918 — Manfred von Richthofen shot down after 80 aerial victories"},
    {"event": "First Non-Stop Transatlantic Flight", "year": 1919, "lat": 53.4106, "lon": -8.9399, "location": "St. John's to Clifden, Ireland", "color": ACCENT_EMERALD, "notes": "Jun 14-15, 1919 — Alcock & Brown in a Vickers Vimy; 16h 12m flight"},
    {"event": "Lindbergh Crosses Atlantic Solo", "year": 1927, "lat": 48.9694, "lon": 2.4414, "location": "New York to Paris (Le Bourget)", "color": ACCENT_AMBER, "notes": "May 20-21, 1927 — Spirit of St. Louis; 33.5 hours non-stop; won $25,000 Orteig Prize"},
    {"event": "Amelia Earhart Atlantic Solo (Woman)", "year": 1932, "lat": 54.2817, "lon": -8.5950, "location": "Harbour Grace to Derry, Ireland", "color": ACCENT_PINK, "notes": "May 20-21, 1932 — First woman to fly solo across the Atlantic; 14h 56m"},
    {"event": "Hindenburg Disaster", "year": 1937, "lat": 40.0337, "lon": -74.3234, "location": "Lakehurst, New Jersey", "color": ACCENT_RED, "notes": "May 6, 1937 — Hydrogen airship caught fire during landing; 36 killed; ended airship era"},
    {"event": "Amelia Earhart Disappears", "year": 1937, "lat": 2.6167, "lon": -174.6333, "location": "Near Howland Island, Pacific", "color": ACCENT_PINK, "notes": "Jul 2, 1937 — Lost during circumnavigation attempt; one of aviation's greatest mysteries"},
    {"event": "First Jet Aircraft Flight (He 178)", "year": 1939, "lat": 54.1833, "lon": 13.2833, "location": "Rostock-Marienehe, Germany", "color": ACCENT_ORANGE, "notes": "Aug 27, 1939 — Heinkel He 178; world's first turbojet-powered flight"},
    {"event": "Chuck Yeager Breaks Sound Barrier", "year": 1947, "lat": 34.9054, "lon": -117.8839, "location": "Muroc/Edwards AFB, California", "color": ACCENT_AMBER, "notes": "Oct 14, 1947 — Bell X-1 'Glamorous Glennis'; Mach 1.06 at 13,106m altitude"},
    {"event": "De Havilland Comet — First Jet Airliner", "year": 1949, "lat": 51.7411, "lon": -0.2277, "location": "Hatfield, England", "color": ACCENT_CYAN, "notes": "Jul 27, 1949 — First flight of world's first commercial jet airliner"},
    {"event": "Boeing 707 Enters Service", "year": 1958, "lat": 40.6413, "lon": -73.7781, "location": "New York (Pan Am)", "color": ACCENT_BLUE, "notes": "Oct 26, 1958 — Pan Am inaugurated jet age for transatlantic travel"},
    {"event": "Concorde First Flight", "year": 1969, "lat": 43.6290, "lon": 1.3678, "location": "Toulouse, France", "color": ACCENT_VIOLET, "notes": "Mar 2, 1969 — Supersonic airliner; Mach 2.04 cruise; retired 2003"},
    {"event": "Boeing 747 First Flight", "year": 1969, "lat": 47.5382, "lon": -122.3030, "location": "Everett, Washington", "color": ACCENT_AMBER, "notes": "Feb 9, 1969 — 'Queen of the Skies'; revolutionized mass air travel"},
    {"event": "Tenerife Airport Disaster", "year": 1977, "lat": 28.4827, "lon": -16.3415, "location": "Los Rodeos, Tenerife", "color": ACCENT_RED, "notes": "Mar 27, 1977 — 583 killed when two 747s collided on runway; deadliest aviation accident"},
    {"event": "Airbus A380 First Flight", "year": 2005, "lat": 43.6290, "lon": 1.3678, "location": "Toulouse, France", "color": ACCENT_EMERALD, "notes": "Apr 27, 2005 — World's largest passenger aircraft; double-decker; 853 max capacity"},
    {"event": "Boeing 787 Dreamliner First Flight", "year": 2009, "lat": 47.5382, "lon": -122.3030, "location": "Everett, Washington", "color": ACCENT_BLUE, "notes": "Dec 15, 2009 — First largely composite airframe airliner; 20% more fuel efficient"},
    {"event": "Solar Impulse 2 Circumnavigation", "year": 2016, "lat": 24.4539, "lon": 54.6533, "location": "Abu Dhabi (start & finish)", "color": ACCENT_EMERALD, "notes": "Mar 2015-Jul 2016 — First solar-powered aircraft to circumnavigate the globe"},
]

# ======================================================================
# 5. MILITARY AIRBASES (curated notable worldwide)
# ======================================================================
MILITARY_AIRBASES = [
    {"name": "Nellis Air Force Base", "country": "USA", "lat": 36.2361, "lon": -115.0342, "branch": "USAF", "notes": "Home of USAF Weapons School; Red Flag exercises; Nevada Test and Training Range"},
    {"name": "RAF Lakenheath", "country": "UK", "lat": 52.4093, "lon": 0.5609, "branch": "USAF/RAF", "notes": "Largest USAF base in England; F-15E Strike Eagles, F-35A Lightning II"},
    {"name": "Ramstein Air Base", "country": "Germany", "lat": 49.4369, "lon": 7.6003, "branch": "USAF", "notes": "HQ USAFE-AFAFRICA; NATO Allied Air Command; critical logistics hub"},
    {"name": "Kadena Air Base", "country": "Japan (Okinawa)", "lat": 26.3516, "lon": 127.7685, "branch": "USAF", "notes": "Largest US Air Force base in the Pacific; 'Keystone of the Pacific'"},
    {"name": "Incirlik Air Base", "country": "Turkey", "lat": 37.0021, "lon": 35.4259, "branch": "USAF/TuAF", "notes": "Strategic Middle East operations hub; hosts US nuclear weapons"},
    {"name": "Al Udeid Air Base", "country": "Qatar", "lat": 25.1174, "lon": 51.3150, "branch": "USAF/QEAF", "notes": "Largest US military facility in Middle East; Combined Air Operations Center"},
    {"name": "Diego Garcia", "country": "British Indian Ocean Territory", "lat": -7.3195, "lon": 72.4111, "branch": "US/UK", "notes": "Strategic Indian Ocean atoll; B-52/B-2 bomber base; naval support facility"},
    {"name": "Thule Air Base", "country": "Greenland (Denmark)", "lat": 76.5312, "lon": -68.7031, "branch": "USSF/Danish", "notes": "Northernmost US base; Ballistic Missile Early Warning; Space Force tracking"},
    {"name": "Aviano Air Base", "country": "Italy", "lat": 46.0319, "lon": 12.5965, "branch": "USAF/AMI", "notes": "31st Fighter Wing; F-16s; key Southern European operations base"},
    {"name": "Baikonur Cosmodrome Airfield", "country": "Kazakhstan", "lat": 45.9644, "lon": 63.3050, "branch": "Russian/Kazakh", "notes": "World's first and largest spaceport; Yuri Gagarin launched here 1961"},
    {"name": "RAF Brize Norton", "country": "UK", "lat": 51.7500, "lon": -1.5836, "branch": "RAF", "notes": "Largest RAF station; Air Mobility Force; C-17, A400M, Voyager tankers"},
    {"name": "Andersen Air Force Base", "country": "Guam (USA)", "lat": 13.5840, "lon": 144.9247, "branch": "USAF", "notes": "Pacific bomber hub; B-52H/B-1B/B-2 rotational deployments; 'Tip of the Spear'"},
    {"name": "Istres-Le Tube Air Base", "country": "France", "lat": 43.5233, "lon": 4.9283, "branch": "French Air Force", "notes": "Nuclear deterrent (Rafale); longest runway in Europe (5000m); flight test center"},
    {"name": "Zhukovsky Air Base", "country": "Russia", "lat": 55.5533, "lon": 38.1500, "branch": "Russian AF", "notes": "MAKS air show venue; LII Gromov flight research; aircraft testing center"},
    {"name": "Kunsan Air Base", "country": "South Korea", "lat": 35.9038, "lon": 126.6158, "branch": "USAF/ROKAF", "notes": "8th Fighter Wing 'Wolf Pack'; F-16s; frontline Korean Peninsula defense"},
    {"name": "Cervia Air Base", "country": "Italy", "lat": 44.2222, "lon": 12.3072, "branch": "Italian AF", "notes": "15th Stormo; MQ-9 Reaper drones; key Italian RPAS operations base"},
    {"name": "Lossiemouth RAF Base", "country": "UK (Scotland)", "lat": 57.7053, "lon": -3.3392, "branch": "RAF", "notes": "Typhoon FGR4 QRA; Scotland's primary air defense; Maritime patrol P-8A"},
    {"name": "Pine Gap", "country": "Australia", "lat": -23.7990, "lon": 133.7370, "branch": "US/Australian", "notes": "Joint Defence Facility; satellite intelligence; signals intercept station"},
    {"name": "Osan Air Base", "country": "South Korea", "lat": 37.0908, "lon": 127.0297, "branch": "USAF/ROKAF", "notes": "51st Fighter Wing; A-10s, F-16s; closest USAF base to North Korea"},
    {"name": "Moron Air Base", "country": "Spain", "lat": 37.1749, "lon": -5.6157, "branch": "USAF/Spanish AF", "notes": "Forward staging for Africa operations; crisis response hub; KC-135s"},
]

# ======================================================================
# 6. ABANDONED/DECOMMISSIONED AIRFIELDS
# ======================================================================
ABANDONED_AIRFIELDS = [
    {"name": "Tempelhof Airport", "city": "Berlin", "country": "Germany", "lat": 52.4730, "lon": 13.4020, "closed": 2008, "notes": "Iconic 1920s terminal; Berlin Airlift 1948-49; now a massive public park", "status": "Public Park"},
    {"name": "Kai Tak Airport", "city": "Hong Kong", "country": "China", "lat": 22.3157, "lon": 114.2014, "closed": 1998, "notes": "Famous checkerboard approach over Kowloon; replaced by Chek Lap Kok", "status": "Redeveloped"},
    {"name": "Hellenikon Airport", "city": "Athens", "country": "Greece", "lat": 37.8933, "lon": 23.7267, "closed": 2001, "notes": "Used for 2004 Olympics venues; now being redeveloped as coastal park", "status": "Redevelopment"},
    {"name": "Stapleton International Airport", "city": "Denver", "country": "USA", "lat": 39.7731, "lon": -104.8793, "closed": 1995, "notes": "Replaced by DEN; site redeveloped into mixed-use Stapleton neighborhood", "status": "Residential"},
    {"name": "Croydon Airport", "city": "London", "country": "UK", "lat": 51.3570, "lon": -0.1164, "closed": 1959, "notes": "London's main airport 1920-1946; first air traffic control tower; now residential", "status": "Heritage Site"},
    {"name": "Floyd Bennett Field", "city": "New York", "country": "USA", "lat": 40.5908, "lon": -73.8914, "closed": 1972, "notes": "NYC's first municipal airport (1931); wrong-way Corrigan departed here; national recreation area", "status": "National Park"},
    {"name": "Nicosia International Airport", "city": "Nicosia", "country": "Cyprus", "lat": 35.1515, "lon": 33.2757, "closed": 1974, "notes": "Abandoned in UN buffer zone since Turkish invasion; planes still on tarmac", "status": "UN Buffer Zone"},
    {"name": "Tegucigalpa Toncontin (Old Terminal)", "city": "Tegucigalpa", "country": "Honduras", "lat": 14.0609, "lon": -87.2172, "closed": 2024, "notes": "One of world's most dangerous airports; replaced by Palmerola XPL", "status": "Closing"},
    {"name": "Don Mueang (Original Closure)", "city": "Bangkok", "country": "Thailand", "lat": 13.9133, "lon": 100.6070, "closed": 2006, "notes": "Closed when Suvarnabhumi opened; later reopened for LCCs — zombie airport revival!", "status": "Reopened (LCC)"},
    {"name": "Subic Bay International", "city": "Subic Bay", "country": "Philippines", "lat": 14.7944, "lon": 120.2712, "closed": 2010, "notes": "Former US Naval Air Station; brief commercial use; now special economic zone", "status": "Economic Zone"},
    {"name": "Mirabel Airport", "city": "Montreal", "country": "Canada", "lat": 45.6817, "lon": -74.0386, "closed": 2004, "notes": "Passenger terminal demolished 2014; still used for cargo; white elephant of aviation", "status": "Cargo Only"},
    {"name": "RAF Upper Heyford", "city": "Oxfordshire", "country": "UK", "lat": 51.9357, "lon": -1.2498, "closed": 1994, "notes": "Cold War USAF F-111 base; now Heyford Park development with heritage center", "status": "Heritage/Housing"},
    {"name": "Tegel Airport", "city": "Berlin", "country": "Germany", "lat": 52.5597, "lon": 13.2877, "closed": 2020, "notes": "Iconic hexagonal terminal; replaced by BER; becoming tech/innovation hub", "status": "Redevelopment"},
    {"name": "Forlanini Airport (Linate Old)", "city": "Milan", "country": "Italy", "lat": 45.4434, "lon": 9.2778, "closed": 1937, "notes": "Italy's first civil airport (1910); now Idroscalo park and residential", "status": "Park"},
    {"name": "Ellinikon (Old Athens)", "city": "Athens", "country": "Greece", "lat": 37.8933, "lon": 23.7267, "closed": 2001, "notes": "Being transformed into Hellinikon mega-project: park, mall, casino, marina", "status": "Mega-Redevelopment"},
]

# ======================================================================
# 7. AIRLINE HUBS (major hub-and-spoke centers)
# ======================================================================
AIRLINE_HUBS = [
    {"airline": "Delta Air Lines", "alliance": "SkyTeam", "hub": "Atlanta ATL", "lat": 33.6407, "lon": -84.4277, "color": "#c8102e", "notes": "World's largest airline hub; 1000+ daily departures"},
    {"airline": "American Airlines", "alliance": "oneworld", "hub": "Dallas/Fort Worth DFW", "lat": 32.8998, "lon": -97.0403, "color": "#0078d2", "notes": "Largest airline by fleet size; 900+ daily departures from DFW"},
    {"airline": "United Airlines", "alliance": "Star Alliance", "hub": "Chicago O'Hare ORD", "lat": 41.9742, "lon": -87.9073, "color": "#002244", "notes": "Major Star Alliance hub; connecting hub for US domestic/international"},
    {"airline": "Emirates", "alliance": "None", "hub": "Dubai DXB", "lat": 25.2532, "lon": 55.3657, "color": "#d71921", "notes": "Largest A380 operator; connecting East-West traffic; 250+ destinations"},
    {"airline": "British Airways", "alliance": "oneworld", "hub": "London Heathrow LHR", "lat": 51.4700, "lon": -0.4543, "color": "#075aaa", "notes": "Flag carrier of UK; Terminal 5 dedicated hub; 183 destinations"},
    {"airline": "Lufthansa", "alliance": "Star Alliance", "hub": "Frankfurt FRA", "lat": 50.0379, "lon": 8.5622, "color": "#05164d", "notes": "Largest German airline; Europe's major connecting hub; 220+ destinations"},
    {"airline": "Air France", "alliance": "SkyTeam", "hub": "Paris CDG", "lat": 49.0097, "lon": 2.5479, "color": "#002157", "notes": "Terminal 2E/2F hub; strong Africa/Middle East network"},
    {"airline": "Singapore Airlines", "alliance": "Star Alliance", "hub": "Singapore Changi SIN", "lat": 1.3644, "lon": 103.9915, "color": "#00467f", "notes": "Consistently rated world's best; connects Europe-Australasia; famous service"},
    {"airline": "Qatar Airways", "alliance": "oneworld", "hub": "Doha Hamad DOH", "lat": 25.2731, "lon": 51.6081, "color": "#5c0632", "notes": "Rapid expansion; Al Mourjan lounge; connecting Middle East hub"},
    {"airline": "Turkish Airlines", "alliance": "Star Alliance", "hub": "Istanbul IST", "lat": 41.2753, "lon": 28.7519, "color": "#e31837", "notes": "Flies to more countries than any airline (120+); geographic advantage of Istanbul"},
    {"airline": "Cathay Pacific", "alliance": "oneworld", "hub": "Hong Kong HKG", "lat": 22.3080, "lon": 113.9185, "color": "#006564", "notes": "Gateway to Asia; premium carrier; strong cargo operations"},
    {"airline": "KLM Royal Dutch", "alliance": "SkyTeam", "hub": "Amsterdam AMS", "lat": 52.3105, "lon": 4.7683, "color": "#00a1de", "notes": "World's oldest airline still operating under original name (est. 1919)"},
    {"airline": "Qantas", "alliance": "oneworld", "hub": "Sydney SYD", "lat": -33.9461, "lon": 151.1772, "color": "#e0002a", "notes": "Australia's flag carrier; ultra-long-haul pioneer; 'Flying Kangaroo'"},
    {"airline": "ANA (All Nippon Airways)", "alliance": "Star Alliance", "hub": "Tokyo Haneda HND", "lat": 35.5494, "lon": 139.7798, "color": "#00467f", "notes": "Japan's largest airline; dual hub Haneda/Narita; 5-star airline"},
    {"name": "Korean Air", "alliance": "SkyTeam", "hub": "Seoul Incheon ICN", "lat": 37.4602, "lon": 126.4407, "color": "#00256c", "notes": "South Korea's flag carrier; major Asian connecting hub; strong cargo"},
    {"airline": "Ethiopian Airlines", "alliance": "Star Alliance", "hub": "Addis Ababa ADD", "lat": 8.9779, "lon": 38.7994, "color": "#009a44", "notes": "Africa's largest/most profitable airline; Pan-African hub; fastest growing"},
    {"airline": "LATAM Airlines", "alliance": "None (oneworld partner)", "hub": "Santiago SCL", "lat": -33.3930, "lon": -70.7858, "color": "#1b0088", "notes": "Latin America's largest airline group; hubs in Santiago and Sao Paulo"},
    {"airline": "Etihad Airways", "alliance": "None", "hub": "Abu Dhabi AUH", "lat": 24.4539, "lon": 54.6533, "color": "#bd8b13", "notes": "UAE national airline; innovative cabins; The Residence first-class suite"},
    {"airline": "Ryanair", "alliance": "None (LCC)", "hub": "Dublin DUB (+ 80 bases)", "lat": 53.4264, "lon": -6.2499, "color": "#073590", "notes": "Europe's largest airline by passengers; ultra-low-cost; 250+ destinations"},
    {"airline": "IndiGo", "alliance": "None", "hub": "New Delhi DEL", "lat": 28.5562, "lon": 77.1000, "color": "#0033a0", "notes": "India's largest airline (60%+ market share); fastest growing major airline globally"},
]

# ======================================================================
# 8. HELIPORTS (notable worldwide)
# ======================================================================
HELIPORTS = [
    {"name": "New York Downtown Manhattan Heliport", "city": "New York", "country": "USA", "lat": 40.7011, "lon": -74.0091, "type": "Urban", "color": ACCENT_CYAN, "notes": "Pier 6, East River; sightseeing flights; commuter helicopter services"},
    {"name": "London Heliport (Battersea)", "city": "London", "country": "UK", "lat": 51.4700, "lon": -0.1788, "type": "Urban", "color": ACCENT_CYAN, "notes": "Only licensed heliport in London; charter, corporate, emergency services"},
    {"name": "Monaco Heliport", "city": "Monaco", "country": "Monaco", "lat": 43.7262, "lon": 7.4175, "type": "Urban", "color": ACCENT_VIOLET, "notes": "Fontvieille; 7-minute shuttle to Nice airport; busiest heliport in Europe"},
    {"name": "Pawan Hans Heliport (Juhu)", "city": "Mumbai", "country": "India", "lat": 19.0980, "lon": 72.8340, "type": "Urban", "color": ACCENT_AMBER, "notes": "Offshore oil platform helicopter services; busy urban heliport"},
    {"name": "São Paulo Helipads Network", "city": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "type": "Urban Network", "color": ACCENT_EMERALD, "notes": "700+ registered helipads; world's busiest helicopter city; traffic-driven demand"},
    {"name": "Interalpen Hotel Helipad", "city": "Telfs, Tyrol", "country": "Austria", "lat": 47.3064, "lon": 11.0797, "type": "Mountain", "color": ACCENT_EMERALD, "notes": "Alpine mountain rescue and luxury hotel helicopter landing"},
    {"name": "Snowy Hydro Heliport", "city": "Kosciuszko NP", "country": "Australia", "lat": -36.4088, "lon": 148.3531, "type": "Mountain Rescue", "color": ACCENT_ORANGE, "notes": "Emergency mountain rescue operations; Snowy Mountains region"},
    {"name": "Isles of Scilly Heliport", "city": "Tresco", "country": "UK", "lat": 49.9458, "lon": -6.3314, "type": "Island", "color": ACCENT_BLUE, "notes": "Helicopter link to Penzance; island community lifeline"},
    {"name": "Burj Al Arab Helipad", "city": "Dubai", "country": "UAE", "lat": 25.1412, "lon": 55.1853, "type": "Rooftop", "color": ACCENT_AMBER, "notes": "210m-high rooftop helipad; used for tennis matches and stunts; iconic landmark"},
    {"name": "North Sea Oil Platform Helidecks", "city": "North Sea", "country": "UK/Norway", "lat": 57.5000, "lon": 1.5000, "type": "Offshore", "color": ACCENT_RED, "notes": "Hundreds of offshore helidecks; crucial for oil/gas crew transfers; harsh weather ops"},
    {"name": "Zermatt Air Heliport", "city": "Zermatt", "country": "Switzerland", "lat": 46.0207, "lon": 7.7491, "type": "Mountain Rescue", "color": ACCENT_EMERALD, "notes": "Alpine rescue base near Matterhorn; Air Zermatt mountain rescue operations"},
    {"name": "ADAC Helicopter Base Munich", "city": "Munich", "country": "Germany", "lat": 48.3537, "lon": 11.7860, "type": "EMS", "color": ACCENT_RED, "notes": "ADAC air rescue (Christoph 1); Germany's busiest EMS helicopter base"},
    {"name": "Corcovado Helipad (Christ the Redeemer)", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9519, "lon": -43.2105, "type": "Tourist", "color": ACCENT_VIOLET, "notes": "Scenic helicopter tours over Rio; Sugarloaf Mountain and Christ the Redeemer"},
    {"name": "Victoria Harbour Heliport", "city": "Hong Kong", "country": "China", "lat": 22.2816, "lon": 114.1585, "type": "Urban", "color": ACCENT_CYAN, "notes": "Cross-harbor helicopter service; Macau helicopter shuttle"},
    {"name": "Grand Canyon Heliport", "city": "Tusayan", "country": "USA", "lat": 35.9541, "lon": -112.1468, "type": "Tourist", "color": ACCENT_ORANGE, "notes": "Grand Canyon helicopter tours; one of America's busiest scenic heliports"},
]

# ======================================================================
# 9. SPACEPORTS & LAUNCH SITES
# ======================================================================
SPACEPORTS = [
    {"name": "Kennedy Space Center (LC-39)", "operator": "NASA/SpaceX", "country": "USA", "lat": 28.5728, "lon": -80.6490, "color": ACCENT_CYAN, "notes": "Apollo, Space Shuttle, SpaceX Falcon/Starship; most famous launch complex"},
    {"name": "Baikonur Cosmodrome", "operator": "Roscosmos", "country": "Kazakhstan", "lat": 45.9644, "lon": 63.3050, "color": ACCENT_RED, "notes": "World's first spaceport; Sputnik 1957; Gagarin 1961; ISS crew launches"},
    {"name": "Vandenberg SFB (SLC-4)", "operator": "USSF/SpaceX", "country": "USA", "lat": 34.7420, "lon": -120.5724, "color": ACCENT_BLUE, "notes": "Polar orbit launches; SpaceX west coast landing pad; military satellites"},
    {"name": "Cape Canaveral SFS", "operator": "USSF/ULA", "country": "USA", "lat": 28.4889, "lon": -80.5778, "color": ACCENT_CYAN, "notes": "Atlas V, Delta IV Heavy launches; first American orbital flights; Mercury program"},
    {"name": "Guiana Space Centre (Kourou)", "operator": "ESA/Arianespace", "country": "French Guiana", "lat": 5.2361, "lon": -52.7685, "color": ACCENT_EMERALD, "notes": "Ariane 5/6, Vega, Soyuz launches; ideal equatorial location for GTO"},
    {"name": "Jiuquan Satellite Launch Center", "operator": "CNSA", "country": "China", "lat": 40.9606, "lon": 100.2864, "color": ACCENT_AMBER, "notes": "China's first launch center; crewed Shenzhou missions; Gobi Desert location"},
    {"name": "Tanegashima Space Center", "operator": "JAXA", "country": "Japan", "lat": 30.4000, "lon": 131.0000, "notes": "Japan's main launch site; H-IIA/H3 rockets; beautiful island location", "color": ACCENT_VIOLET},
    {"name": "Satish Dhawan Space Centre (Sriharikota)", "operator": "ISRO", "country": "India", "lat": 13.7199, "lon": 80.2304, "color": ACCENT_ORANGE, "notes": "India's primary launch site; Chandrayaan, Mangalyaan missions; barrier island"},
    {"name": "Vostochny Cosmodrome", "operator": "Roscosmos", "country": "Russia", "lat": 51.8844, "lon": 128.3333, "color": ACCENT_RED, "notes": "Russia's newest spaceport (2016); intended to reduce Baikonur dependence"},
    {"name": "Wenchang Space Launch Site", "operator": "CNSA", "country": "China (Hainan)", "lat": 19.6145, "lon": 110.9510, "color": ACCENT_AMBER, "notes": "China's newest; Long March 5; near equator for heavy-lift advantage"},
    {"name": "Starbase (SpaceX Boca Chica)", "operator": "SpaceX", "country": "USA", "lat": 25.9968, "lon": -97.1558, "color": ACCENT_CYAN, "notes": "Starship development & launch facility; world's most powerful rocket tested here"},
    {"name": "Rocket Lab Launch Complex 1", "operator": "Rocket Lab", "country": "New Zealand", "lat": -39.2616, "lon": 177.8649, "color": ACCENT_EMERALD, "notes": "Electron rocket launches; first private orbital launch site in Southern Hemisphere"},
    {"name": "Mojave Air & Space Port", "operator": "Various", "country": "USA", "lat": 35.0594, "lon": -118.1517, "color": ACCENT_AMBER, "notes": "SpaceShipOne/Two; first inland spaceport; Virgin Galactic's test base"},
    {"name": "Spaceport America", "operator": "Virgin Galactic", "country": "USA (New Mexico)", "lat": 32.9903, "lon": -106.9753, "color": ACCENT_VIOLET, "notes": "Purpose-built commercial spaceport; Virgin Galactic space tourism flights"},
    {"name": "Plesetsk Cosmodrome", "operator": "Russian MoD", "country": "Russia", "lat": 62.9272, "lon": 40.5778, "color": ACCENT_RED, "notes": "Most-used launch site by number of launches; military and Angara rockets"},
    {"name": "Xichang Satellite Launch Center", "operator": "CNSA", "country": "China", "lat": 28.2463, "lon": 102.0267, "color": ACCENT_AMBER, "notes": "BeiDou navigation satellites; Chang'e lunar missions launched here"},
    {"name": "Esrange Space Center", "operator": "SSC", "country": "Sweden", "lat": 67.8933, "lon": 21.1044, "color": ACCENT_BLUE, "notes": "Sounding rockets; ESA balloon launches; upcoming orbital launches"},
    {"name": "SaxaVord Spaceport", "operator": "SaxaVord", "country": "UK (Shetland)", "lat": 60.8262, "lon": -0.8694, "color": ACCENT_EMERALD, "notes": "UK's first vertical launch spaceport; Unst island; polar orbit access"},
]

# ======================================================================
# 10. AIR TRAFFIC CONTROL — major ATC centers and FIR regions
# ======================================================================
ATC_CENTERS = [
    {"name": "Eurocontrol Maastricht UAC", "city": "Maastricht", "country": "Netherlands", "lat": 50.8514, "lon": 5.6910, "type": "Upper Area Control", "color": ACCENT_CYAN, "notes": "Controls upper airspace over Benelux, NW Germany; 1.7M+ flights/year"},
    {"name": "NATS Swanwick Centre", "city": "Swanwick", "country": "UK", "lat": 50.8720, "lon": -1.2500, "type": "Area Control", "color": ACCENT_BLUE, "notes": "Controls en-route traffic across England and Wales; 2.5M+ flights/year"},
    {"name": "New York TRACON (N90)", "city": "Westbury, NY", "country": "USA", "lat": 40.7554, "lon": -73.5563, "type": "TRACON", "color": ACCENT_VIOLET, "notes": "Busiest TRACON in the world; handles JFK, EWR, LGA, TEB, HPN approaches"},
    {"name": "Chicago TRACON (C90)", "city": "Elgin, IL", "country": "USA", "lat": 42.0387, "lon": -88.2764, "type": "TRACON", "color": ACCENT_VIOLET, "notes": "One of FAA's busiest TRACONs; O'Hare and Midway approach/departure control"},
    {"name": "FAA Washington ARTCC (ZDC)", "city": "Leesburg, VA", "country": "USA", "lat": 39.1157, "lon": -77.5636, "type": "ARTCC", "color": ACCENT_AMBER, "notes": "Handles DC metro airspace including complex restricted areas around Capitol"},
    {"name": "Dubai ACC", "city": "Dubai", "country": "UAE", "lat": 25.2532, "lon": 55.3657, "type": "Area Control", "color": ACCENT_ORANGE, "notes": "Controls one of busiest airspaces; DXB + DWC traffic; East-West corridor"},
    {"name": "Tokyo ACC (JCAB)", "city": "Tokorozawa", "country": "Japan", "lat": 35.7996, "lon": 139.4700, "type": "Area Control", "color": ACCENT_PINK, "notes": "Manages dense Haneda/Narita traffic; one of world's busiest airspaces"},
    {"name": "Beijing ACC", "city": "Beijing", "country": "China", "lat": 40.0799, "lon": 116.6031, "type": "Area Control", "color": ACCENT_RED, "notes": "Growing rapidly with Chinese aviation expansion; complex military airspace"},
    {"name": "ENAV Rome ACC", "city": "Rome", "country": "Italy", "lat": 41.8003, "lon": 12.2389, "type": "Area Control", "color": ACCENT_EMERALD, "notes": "Italian air navigation; busy Mediterranean crossroads; 2M+ flights/year"},
    {"name": "DFS Langen ACC", "city": "Langen", "country": "Germany", "lat": 49.9917, "lon": 8.6544, "type": "Area Control", "color": ACCENT_CYAN, "notes": "Deutsche Flugsicherung; busiest European national airspace; 3.3M flights/year"},
    {"name": "NavCanada Gander Oceanic", "city": "Gander", "country": "Canada", "lat": 48.9569, "lon": -54.5681, "type": "Oceanic Control", "color": ACCENT_BLUE, "notes": "Controls North Atlantic tracks (NAT); 500K+ oceanic crossings per year"},
    {"name": "Shanwick Oceanic (Shannon/Prestwick)", "city": "Shannon", "country": "Ireland", "lat": 52.7019, "lon": -8.9247, "type": "Oceanic Control", "color": ACCENT_BLUE, "notes": "Eastern half of North Atlantic; coordinated with Gander; SELCAL procedures"},
    {"name": "Jeddah ACC", "city": "Jeddah", "country": "Saudi Arabia", "lat": 21.6796, "lon": 39.1565, "type": "Area Control", "color": ACCENT_AMBER, "notes": "GACA control; massive seasonal Hajj traffic; Middle East corridor"},
    {"name": "Singapore ACC", "city": "Singapore", "country": "Singapore", "lat": 1.3644, "lon": 103.9915, "type": "Area Control", "color": ACCENT_EMERALD, "notes": "Strait of Malacca corridor; busy Southeast Asian airspace; modern systems"},
    {"name": "Johannesburg ACC", "city": "Johannesburg", "country": "South Africa", "lat": -26.1367, "lon": 28.2422, "type": "Area Control", "color": ACCENT_ORANGE, "notes": "ATNS; busiest African airspace; gateway for sub-Saharan aviation"},
    {"name": "São Paulo ACC (CINDACTA III)", "city": "Recife", "country": "Brazil", "lat": -8.0576, "lon": -34.8770, "type": "Area Control", "color": ACCENT_VIOLET, "notes": "Brazilian ATC DECEA system; manages South Atlantic oceanic traffic"},
    {"name": "Melbourne Centre", "city": "Melbourne", "country": "Australia", "lat": -37.6690, "lon": 144.8410, "type": "Area Control", "color": ACCENT_CYAN, "notes": "Airservices Australia; covers vast oceanic FIR; Indian/Pacific Ocean sectors"},
    {"name": "Mumbai ACC", "city": "Mumbai", "country": "India", "lat": 19.0896, "lon": 72.8656, "type": "Area Control", "color": ACCENT_AMBER, "notes": "AAI; rapidly growing Indian airspace; Arabian Sea oceanic control"},
]


# ======================================================================
# OVERPASS QUERY BUILDERS
# ======================================================================
@st.cache_data(ttl=3600)
def _query_overpass_airports(lat: float, lon: float, radius_m: int = 30000):
    """Query Overpass API for airports/aerodromes near a location."""
    query = f"""
    [out:json][timeout:60];
    (
      node["aeroway"="aerodrome"](around:{radius_m},{lat},{lon});
      way["aeroway"="aerodrome"](around:{radius_m},{lat},{lon});
      relation["aeroway"="aerodrome"](around:{radius_m},{lat},{lon});
    );
    out center 200;
    """
    return query_overpass(query)


@st.cache_data(ttl=3600)
def _query_overpass_runways(lat: float, lon: float, radius_m: int = 15000):
    """Query Overpass API for runways near a location."""
    query = f"""
    [out:json][timeout:60];
    (
      way["aeroway"="runway"](around:{radius_m},{lat},{lon});
    );
    out center 100;
    """
    return query_overpass(query)


@st.cache_data(ttl=3600)
def _query_overpass_heliports(lat: float, lon: float, radius_m: int = 30000):
    """Query Overpass API for helipads/heliports near a location."""
    query = f"""
    [out:json][timeout:60];
    (
      node["aeroway"="helipad"](around:{radius_m},{lat},{lon});
      way["aeroway"="helipad"](around:{radius_m},{lat},{lon});
      node["aeroway"="heliport"](around:{radius_m},{lat},{lon});
      way["aeroway"="heliport"](around:{radius_m},{lat},{lon});
    );
    out center 200;
    """
    return query_overpass(query)


@st.cache_data(ttl=3600)
def _query_overpass_military(lat: float, lon: float, radius_m: int = 50000):
    """Query Overpass API for military airfields near a location."""
    query = f"""
    [out:json][timeout:60];
    (
      node["aeroway"="aerodrome"]["military"](around:{radius_m},{lat},{lon});
      way["aeroway"="aerodrome"]["military"](around:{radius_m},{lat},{lon});
      node["military"="airfield"](around:{radius_m},{lat},{lon});
      way["military"="airfield"](around:{radius_m},{lat},{lon});
    );
    out center 100;
    """
    return query_overpass(query)


@st.cache_data(ttl=3600)
def _query_overpass_abandoned(lat: float, lon: float, radius_m: int = 50000):
    """Query Overpass API for abandoned/disused aerodromes."""
    query = f"""
    [out:json][timeout:60];
    (
      node["aeroway"="aerodrome"]["disused"="yes"](around:{radius_m},{lat},{lon});
      way["aeroway"="aerodrome"]["disused"="yes"](around:{radius_m},{lat},{lon});
      node["abandoned:aeroway"="aerodrome"](around:{radius_m},{lat},{lon});
      way["abandoned:aeroway"="aerodrome"](around:{radius_m},{lat},{lon});
      node["aeroway"="aerodrome"]["abandoned"="yes"](around:{radius_m},{lat},{lon});
      way["aeroway"="aerodrome"]["abandoned"="yes"](around:{radius_m},{lat},{lon});
    );
    out center 100;
    """
    return query_overpass(query)


# ======================================================================
# HELPER FUNCTIONS
# ======================================================================
def _create_map(center_lat: float, center_lon: float, zoom: int = 3) -> folium.Map:
    """Create a Folium map with dark theme tiles."""
    return folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=MAP_TILES,
        attr="CartoDB",
    )


def _render_map(m: folium.Map, height: int = MAP_HEIGHT):
    """Render a Folium map using components.html."""
    components.html(m._repr_html_(), height=height)


def _safe_popup(html_content: str, max_width: int = 300) -> folium.Popup:
    """Create a styled popup with dark theme."""
    styled = f"""
    <div style="font-family: 'Segoe UI', sans-serif; font-size: 13px;
                color: {TEXT_PRIMARY}; background: {SURFACE};
                padding: 8px 12px; border-radius: 8px;
                border: 1px solid #2a3550; min-width: 200px;">
        {html_content}
    </div>
    """
    return folium.Popup(styled, max_width=max_width)


def _make_chart_pax(data: list, title: str, xlabel: str, ylabel: str):
    """Create a horizontal bar chart for passenger data."""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)

    names = [d["name"][:30] for d in data]
    values = [d.get("pax_millions", 0) for d in data]

    bars = ax.barh(names, values, color=ACCENT_CYAN, alpha=0.85, edgecolor="#2a3550")
    ax.set_xlabel(xlabel, color=TEXT_PRIMARY, fontsize=11)
    ax.set_ylabel(ylabel, color=TEXT_PRIMARY, fontsize=11)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=14, fontweight="bold", pad=15)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.invert_yaxis()
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.xaxis.grid(True, color="#2a3550", alpha=0.3)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}M", ha="left", va="center", color=TEXT_SECONDARY, fontsize=8)

    plt.tight_layout()
    return fig


def _make_chart_bar(names: list, values: list, title: str, xlabel: str, color: str = ACCENT_AMBER):
    """Create a generic horizontal bar chart."""
    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.45)))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)

    bars = ax.barh(names, values, color=color, alpha=0.85, edgecolor="#2a3550")
    ax.set_xlabel(xlabel, color=TEXT_PRIMARY, fontsize=11)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=14, fontweight="bold", pad=15)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.invert_yaxis()
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.xaxis.grid(True, color="#2a3550", alpha=0.3)

    plt.tight_layout()
    return fig


def _make_chart_timeline(events: list, title: str):
    """Create a timeline scatter for aviation history."""
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)

    years = [e["year"] for e in events]
    y_pos = list(range(len(events)))
    colors = [e.get("color", ACCENT_CYAN) for e in events]
    labels = [e["event"][:40] for e in events]

    ax.scatter(years, y_pos, c=colors, s=80, zorder=5, edgecolors="#2a3550", linewidths=0.5)
    for i, (yr, label) in enumerate(zip(years, labels)):
        ax.annotate(f"{label} ({yr})", (yr, i), textcoords="offset points",
                     xytext=(10, 0), fontsize=8, color=TEXT_SECONDARY, va="center")

    ax.set_xlabel("Year", color=TEXT_PRIMARY, fontsize=11)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=14, fontweight="bold", pad=15)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.invert_yaxis()
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.xaxis.grid(True, color="#2a3550", alpha=0.3)
    ax.yaxis.set_visible(False)

    plt.tight_layout()
    return fig


def _df_to_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to CSV string."""
    return df.to_csv(index=False)


# ======================================================================
# MODE RENDERERS
# ======================================================================

def _render_busiest_airports():
    """Mode 1: World's Busiest Airports."""
    st.markdown("### World's Busiest Airports (Top 50 by Annual Passengers)")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "The 50 busiest airports in the world ranked by total annual passengers. "
        "Atlanta's Hartsfield-Jackson has held the top spot for over two decades, "
        "processing over 100 million passengers per year. Dubai, Dallas, and London "
        "Heathrow round out the top positions in this global ranking."
        "</p>",
        unsafe_allow_html=True,
    )

    top_n = st.slider("Show top N airports", 10, 50, 25, key="busiest_top_n")
    data = BUSIEST_AIRPORTS[:top_n]

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    total_pax = sum(d["pax_millions"] for d in data)
    countries = len(set(d["country"] for d in data))
    c1.metric("Airports Shown", top_n)
    c2.metric("Total Passengers", f"{total_pax:.0f}M")
    c3.metric("Countries", countries)
    c4.metric("Top Airport", data[0]["iata"])

    # Map
    m = _create_map(20, 0, zoom=2)
    for ap in data:
        radius = max(4, ap["pax_millions"] / 8)
        popup_html = (
            f"<b>{escape(ap['name'])}</b><br>"
            f"IATA: {escape(ap['iata'])}<br>"
            f"City: {escape(ap['city'])}, {escape(ap['country'])}<br>"
            f"Passengers: {ap['pax_millions']:.1f}M/year<br>"
            f"Rank: #{ap['rank']}"
        )
        folium.CircleMarker(
            location=[ap["lat"], ap["lon"]],
            radius=radius,
            color=ACCENT_CYAN,
            fill=True,
            fill_color=ACCENT_CYAN,
            fill_opacity=0.7,
            popup=_safe_popup(popup_html),
            tooltip=f"#{ap['rank']} {escape(ap['iata'])} — {ap['pax_millions']:.1f}M pax",
        ).add_to(m)
    _render_map(m)

    # Chart
    chart_data = data[:20]
    fig = _make_chart_pax(chart_data, f"Top {len(chart_data)} Busiest Airports by Passengers",
                          "Annual Passengers (Millions)", "")
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = pd.DataFrame(data)
    df = df[["rank", "name", "iata", "city", "country", "pax_millions"]]
    df.columns = ["Rank", "Airport", "IATA", "City", "Country", "Passengers (M)"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "busiest_airports.csv", "text/csv", key="dl_busiest")


def _render_longest_runways():
    """Mode 2: Longest Runways."""
    st.markdown("### Longest Runways in the World")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "The world's longest runways, from Qamdo Bamda's 5,500m strip at 4,334m elevation "
        "in Tibet to military test facilities and high-altitude airports that require "
        "exceptionally long runways. Many of these runways were built for specific purposes: "
        "space shuttle landings, military operations, or compensating for thin air at altitude."
        "</p>",
        unsafe_allow_html=True,
    )

    data = LONGEST_RUNWAYS

    c1, c2, c3 = st.columns(3)
    c1.metric("Runways Listed", len(data))
    c2.metric("Longest", f"{data[0]['length_m']:,}m")
    c3.metric("Highest Elevation", f"{max(d['elevation_m'] for d in data):,}m")

    # Map
    m = _create_map(30, 50, zoom=2)
    for rw in data:
        popup_html = (
            f"<b>{escape(rw['name'])}</b><br>"
            f"IATA: {escape(rw['iata'])}<br>"
            f"Country: {escape(rw['country'])}<br>"
            f"Length: {rw['length_m']:,}m ({rw['length_ft']:,} ft)<br>"
            f"Elevation: {rw['elevation_m']:,}m<br>"
            f"<em>{escape(rw['notes'])}</em>"
        )
        folium.Marker(
            location=[rw["lat"], rw["lon"]],
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{escape(rw['name'])} — {rw['length_m']:,}m",
            icon=folium.Icon(color="orange", icon="road", prefix="fa"),
        ).add_to(m)
    _render_map(m)

    # Chart
    names = [f"{d['name'][:25]} ({d['iata']})" for d in data]
    values = [d["length_m"] for d in data]
    fig = _make_chart_bar(names, values, "Runway Length Comparison", "Length (meters)", ACCENT_AMBER)
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = pd.DataFrame(data)
    df = df[["name", "iata", "country", "length_m", "length_ft", "elevation_m", "notes"]]
    df.columns = ["Airport", "IATA", "Country", "Length (m)", "Length (ft)", "Elevation (m)", "Notes"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "longest_runways.csv", "text/csv", key="dl_runways")


def _render_extreme_airports():
    """Mode 3: Extreme Airports."""
    st.markdown("### Extreme & Unusual Airports")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "From the terrifying cliff-edge runway at Lukla (gateway to Everest) to the beach "
        "runway at Barra in Scotland, these airports push the boundaries of aviation engineering. "
        "Ice runways in Antarctica, island strips barely wider than the aircraft, and approaches "
        "that require nerves of steel make these some of the most remarkable airfields on Earth."
        "</p>",
        unsafe_allow_html=True,
    )

    # Category filter
    categories = sorted(set(a["category"] for a in EXTREME_AIRPORTS))
    selected = st.multiselect("Filter by category", categories, default=categories, key="extreme_cat")
    data = [a for a in EXTREME_AIRPORTS if a["category"] in selected] if selected else EXTREME_AIRPORTS

    c1, c2, c3 = st.columns(3)
    c1.metric("Airports Shown", len(data))
    c2.metric("Categories", len(set(a["category"] for a in data)))
    highest = max(data, key=lambda x: x["elevation_m"]) if data else None
    c3.metric("Highest Elevation", f"{highest['elevation_m']:,}m" if highest else "N/A")

    # Map
    m = _create_map(20, 0, zoom=2)
    for ap in data:
        popup_html = (
            f"<b>{escape(ap['name'])}</b><br>"
            f"IATA: {escape(ap['iata'])}<br>"
            f"Country: {escape(ap['country'])}<br>"
            f"Category: {escape(ap['category'])}<br>"
            f"Elevation: {ap['elevation_m']:,}m<br>"
            f"<em>{escape(ap['notes'])}</em>"
        )
        folium.CircleMarker(
            location=[ap["lat"], ap["lon"]],
            radius=8,
            color=ap.get("color", ACCENT_RED),
            fill=True,
            fill_color=ap.get("color", ACCENT_RED),
            fill_opacity=0.8,
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{escape(ap['name'])} ({escape(ap['category'])})",
        ).add_to(m)
    _render_map(m)

    # Table
    df = pd.DataFrame(data)
    df = df[["name", "iata", "country", "category", "elevation_m", "notes"]]
    df.columns = ["Airport", "IATA", "Country", "Category", "Elevation (m)", "Notes"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "extreme_airports.csv", "text/csv", key="dl_extreme")


def _render_aviation_history():
    """Mode 4: Aviation History."""
    st.markdown("### Aviation History Milestones")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "Key moments in aviation history mapped across the globe, from the Wright Brothers' "
        "first 12-second flight in 1903 to the Solar Impulse circumnavigation in 2016. "
        "Each marker represents a pivotal event that shaped how we fly today."
        "</p>",
        unsafe_allow_html=True,
    )

    data = AVIATION_HISTORY

    c1, c2, c3 = st.columns(3)
    c1.metric("Milestones", len(data))
    c2.metric("Span", f"{data[0]['year']}—{data[-1]['year']}")
    c3.metric("Years of Flight", data[-1]["year"] - data[0]["year"])

    # Map
    m = _create_map(30, -20, zoom=2)
    for ev in data:
        popup_html = (
            f"<b>{escape(ev['event'])}</b><br>"
            f"Year: {ev['year']}<br>"
            f"Location: {escape(ev['location'])}<br>"
            f"<em>{escape(ev['notes'])}</em>"
        )
        folium.Marker(
            location=[ev["lat"], ev["lon"]],
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{ev['year']} — {escape(ev['event'][:50])}",
            icon=folium.Icon(color="red" if "disaster" in ev["event"].lower() or "disappear" in ev["event"].lower()
                             else "blue", icon="plane", prefix="fa"),
        ).add_to(m)
    _render_map(m)

    # Timeline chart
    fig = _make_chart_timeline(data, "Aviation History Timeline (1903-2016)")
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = pd.DataFrame(data)
    df = df[["year", "event", "location", "notes"]]
    df.columns = ["Year", "Event", "Location", "Details"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "aviation_history.csv", "text/csv", key="dl_history")


def _render_military_airbases():
    """Mode 5: Military Airbases."""
    st.markdown("### Major Military Airbases Worldwide")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "Significant military air installations around the world, from strategic USAF bases "
        "in Europe and the Pacific to remote facilities like Diego Garcia and Thule. "
        "Use the Overpass search below to find additional military airfields in any area."
        "</p>",
        unsafe_allow_html=True,
    )

    data = MILITARY_AIRBASES

    c1, c2, c3 = st.columns(3)
    c1.metric("Curated Bases", len(data))
    branches = len(set(d["branch"] for d in data))
    countries = len(set(d["country"] for d in data))
    c2.metric("Countries", countries)
    c3.metric("Branches/Forces", branches)

    # Map
    m = _create_map(30, 20, zoom=2)
    for base in data:
        popup_html = (
            f"<b>{escape(base['name'])}</b><br>"
            f"Country: {escape(base['country'])}<br>"
            f"Branch: {escape(base['branch'])}<br>"
            f"<em>{escape(base['notes'])}</em>"
        )
        folium.Marker(
            location=[base["lat"], base["lon"]],
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{escape(base['name'])} ({escape(base['branch'])})",
            icon=folium.Icon(color="darkred", icon="shield", prefix="fa"),
        ).add_to(m)
    _render_map(m)

    # Overpass search
    st.markdown("---")
    st.markdown(f"**Search Military Airfields via OSM (Overpass API)**")
    col_a, col_b, col_c = st.columns(3)
    search_lat = col_a.number_input("Latitude", -90.0, 90.0, 51.0, key="mil_lat")
    search_lon = col_b.number_input("Longitude", -180.0, 180.0, -1.0, key="mil_lon")
    search_r = col_c.number_input("Radius (km)", 5, 200, 50, key="mil_radius")

    if st.button("Search Military Airfields", key="mil_search"):
        with st.spinner("Querying Overpass API..."):
            result = _query_overpass_military(search_lat, search_lon, int(search_r * 1000))
        if result and "_error" not in result and "elements" in result:
            elements = result["elements"]
            st.success(f"Found {len(elements)} military airfield(s) within {search_r} km")
            if elements:
                osm_map = _create_map(search_lat, search_lon, zoom=8)
                rows = []
                for el in elements:
                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")
                    if lat and lon:
                        name = el.get("tags", {}).get("name", "Unknown")
                        popup_html = f"<b>{escape(name)}</b><br>OSM ID: {el.get('id', 'N/A')}"
                        folium.Marker(
                            [lat, lon],
                            popup=_safe_popup(popup_html),
                            tooltip=escape(name),
                            icon=folium.Icon(color="red", icon="plane", prefix="fa"),
                        ).add_to(osm_map)
                        rows.append({"Name": name, "Lat": lat, "Lon": lon, "OSM ID": el.get("id")})
                _render_map(osm_map)
                if rows:
                    osm_df = pd.DataFrame(rows)
                    st.dataframe(osm_df, width="stretch")
        else:
            err = result.get("_error", "Unknown error") if isinstance(result, dict) else "No response"
            st.warning(f"No results or error: {err}")

    # Table
    df = pd.DataFrame(data)
    df = df[["name", "country", "branch", "notes"]]
    df.columns = ["Base", "Country", "Branch", "Notes"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "military_airbases.csv", "text/csv", key="dl_military")


def _render_abandoned_airfields():
    """Mode 6: Abandoned Airfields."""
    st.markdown("### Abandoned & Decommissioned Airports")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "Ghost airports and decommissioned airfields around the world. Berlin's Tempelhof "
        "is now a beloved public park, Hong Kong's Kai Tak has been redeveloped, and "
        "Nicosia's airport has sat frozen in time in the UN buffer zone since 1974. "
        "These former hubs tell stories of changing times, political upheaval, and urban renewal."
        "</p>",
        unsafe_allow_html=True,
    )

    data = ABANDONED_AIRFIELDS

    c1, c2, c3 = st.columns(3)
    c1.metric("Abandoned Airports", len(data))
    statuses = len(set(d["status"] for d in data))
    c2.metric("Status Types", statuses)
    oldest_closed = min(d["closed"] for d in data)
    c3.metric("Earliest Closure", oldest_closed)

    # Status colors
    status_colors = {
        "Public Park": ACCENT_EMERALD,
        "Redeveloped": ACCENT_CYAN,
        "Redevelopment": ACCENT_CYAN,
        "Residential": ACCENT_BLUE,
        "Heritage Site": ACCENT_AMBER,
        "National Park": ACCENT_EMERALD,
        "UN Buffer Zone": ACCENT_RED,
        "Closing": ACCENT_ORANGE,
        "Reopened (LCC)": ACCENT_VIOLET,
        "Economic Zone": ACCENT_BLUE,
        "Cargo Only": ACCENT_AMBER,
        "Heritage/Housing": ACCENT_AMBER,
        "Park": ACCENT_EMERALD,
        "Mega-Redevelopment": ACCENT_PINK,
    }

    # Map
    m = _create_map(40, 10, zoom=3)
    for af in data:
        color = status_colors.get(af["status"], ACCENT_RED)
        popup_html = (
            f"<b>{escape(af['name'])}</b><br>"
            f"City: {escape(af['city'])}, {escape(af['country'])}<br>"
            f"Closed: {af['closed']}<br>"
            f"Status: {escape(af['status'])}<br>"
            f"<em>{escape(af['notes'])}</em>"
        )
        folium.CircleMarker(
            location=[af["lat"], af["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{escape(af['name'])} (closed {af['closed']})",
        ).add_to(m)
    _render_map(m)

    # Overpass search for abandoned airfields
    st.markdown("---")
    st.markdown(f"**Search Abandoned Airfields via OSM (Overpass API)**")
    col_a, col_b, col_c = st.columns(3)
    s_lat = col_a.number_input("Latitude", -90.0, 90.0, 52.0, key="abn_lat")
    s_lon = col_b.number_input("Longitude", -180.0, 180.0, 13.0, key="abn_lon")
    s_r = col_c.number_input("Radius (km)", 5, 200, 50, key="abn_radius")

    if st.button("Search Abandoned Airfields", key="abn_search"):
        with st.spinner("Querying Overpass API..."):
            result = _query_overpass_abandoned(s_lat, s_lon, int(s_r * 1000))
        if result and "_error" not in result and "elements" in result:
            elements = result["elements"]
            st.success(f"Found {len(elements)} abandoned/disused airfield(s) within {s_r} km")
            if elements:
                osm_map = _create_map(s_lat, s_lon, zoom=8)
                rows = []
                for el in elements:
                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")
                    if lat and lon:
                        name = el.get("tags", {}).get("name", "Unknown")
                        popup_html = f"<b>{escape(name)}</b><br>OSM ID: {el.get('id', 'N/A')}"
                        folium.CircleMarker(
                            [lat, lon], radius=7, color=ACCENT_RED, fill=True,
                            fill_color=ACCENT_RED, fill_opacity=0.7,
                            popup=_safe_popup(popup_html),
                            tooltip=escape(name),
                        ).add_to(osm_map)
                        rows.append({"Name": name, "Lat": lat, "Lon": lon, "OSM ID": el.get("id")})
                _render_map(osm_map)
                if rows:
                    osm_df = pd.DataFrame(rows)
                    st.dataframe(osm_df, width="stretch")
        else:
            err = result.get("_error", "Unknown error") if isinstance(result, dict) else "No response"
            st.warning(f"No results or error: {err}")

    # Table
    df = pd.DataFrame(data)
    df = df[["name", "city", "country", "closed", "status", "notes"]]
    df.columns = ["Airport", "City", "Country", "Closed", "Status", "Notes"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "abandoned_airfields.csv", "text/csv", key="dl_abandoned")


def _render_airline_hubs():
    """Mode 7: Airline Hubs."""
    st.markdown("### Major Airline Hub-and-Spoke Networks")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "The world's major airline hubs, where carriers concentrate operations for "
        "efficient passenger connections. Istanbul's geographic advantage makes Turkish Airlines "
        "serve more countries than any competitor. Atlanta processes over 1,000 daily departures "
        "as Delta's fortress hub. Global alliances (Star Alliance, SkyTeam, oneworld) "
        "link these hubs into worldwide networks."
        "</p>",
        unsafe_allow_html=True,
    )

    # Alliance filter
    alliances = sorted(set(d.get("alliance", "None") for d in AIRLINE_HUBS))
    sel_alliance = st.multiselect("Filter by alliance", alliances, default=alliances, key="hub_alliance")
    data = [d for d in AIRLINE_HUBS if d.get("alliance", "None") in sel_alliance] if sel_alliance else AIRLINE_HUBS

    c1, c2, c3 = st.columns(3)
    c1.metric("Airlines Shown", len(data))
    c2.metric("Alliances", len(set(d.get("alliance", "None") for d in data)))
    c3.metric("Countries", len(set(d.get("hub", "")[:3] for d in data)))

    # Alliance color map
    alliance_colors = {
        "Star Alliance": ACCENT_AMBER,
        "SkyTeam": ACCENT_CYAN,
        "oneworld": ACCENT_RED,
        "None": ACCENT_VIOLET,
        "None (LCC)": ACCENT_EMERALD,
        "None (oneworld partner)": ACCENT_PINK,
    }

    # Map
    m = _create_map(20, 20, zoom=2)
    for hub in data:
        airline = hub.get("airline", hub.get("name", "Unknown"))
        color = alliance_colors.get(hub.get("alliance", "None"), ACCENT_VIOLET)
        popup_html = (
            f"<b>{escape(airline)}</b><br>"
            f"Alliance: {escape(hub.get('alliance', 'None'))}<br>"
            f"Hub: {escape(hub['hub'])}<br>"
            f"<em>{escape(hub['notes'])}</em>"
        )
        folium.CircleMarker(
            location=[hub["lat"], hub["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{escape(airline)} — {escape(hub['hub'])}",
        ).add_to(m)

    # Add legend HTML
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(17,24,39,0.9); padding: 10px 14px; border-radius: 8px;
                border: 1px solid #2a3550; font-size: 12px; color: #e8ecf4;">
        <b>Alliances</b><br>
        <span style="color: #f59e0b;">&#9679;</span> Star Alliance<br>
        <span style="color: #06b6d4;">&#9679;</span> SkyTeam<br>
        <span style="color: #ef4444;">&#9679;</span> oneworld<br>
        <span style="color: #8b5cf6;">&#9679;</span> Independent
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    _render_map(m)

    # Table
    rows = []
    for hub in data:
        airline = hub.get("airline", hub.get("name", "Unknown"))
        rows.append({
            "Airline": airline,
            "Alliance": hub.get("alliance", "None"),
            "Hub": hub["hub"],
            "Notes": hub["notes"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "airline_hubs.csv", "text/csv", key="dl_hubs")


def _render_heliports():
    """Mode 8: Helicopter & Heliports."""
    st.markdown("### Heliports, Helipads & Helicopter Operations")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "From the 700+ rooftop helipads of Sao Paulo to the dramatic Burj Al Arab helipad "
        "at 210 meters above the Persian Gulf, helicopter operations serve critical roles: "
        "emergency medical services, offshore oil platforms, mountain rescue, urban commuting, "
        "and tourism. This mode shows curated notable heliports and allows OSM-based searching."
        "</p>",
        unsafe_allow_html=True,
    )

    data = HELIPORTS

    # Type filter
    types = sorted(set(h["type"] for h in data))
    sel_types = st.multiselect("Filter by type", types, default=types, key="heli_type")
    data = [h for h in data if h["type"] in sel_types] if sel_types else HELIPORTS

    c1, c2, c3 = st.columns(3)
    c1.metric("Heliports Shown", len(data))
    c2.metric("Types", len(set(h["type"] for h in data)))
    c3.metric("Countries", len(set(h["country"] for h in data)))

    # Map
    m = _create_map(30, 20, zoom=2)
    for hp in data:
        popup_html = (
            f"<b>{escape(hp['name'])}</b><br>"
            f"City: {escape(hp['city'])}, {escape(hp['country'])}<br>"
            f"Type: {escape(hp['type'])}<br>"
            f"<em>{escape(hp['notes'])}</em>"
        )
        folium.CircleMarker(
            location=[hp["lat"], hp["lon"]],
            radius=7,
            color=hp.get("color", ACCENT_CYAN),
            fill=True,
            fill_color=hp.get("color", ACCENT_CYAN),
            fill_opacity=0.8,
            popup=_safe_popup(popup_html, 300),
            tooltip=f"{escape(hp['name'])} ({escape(hp['type'])})",
        ).add_to(m)
    _render_map(m)

    # Overpass search for heliports
    st.markdown("---")
    st.markdown(f"**Search Heliports/Helipads via OSM (Overpass API)**")
    col_a, col_b, col_c = st.columns(3)
    h_lat = col_a.number_input("Latitude", -90.0, 90.0, 40.7, key="heli_lat")
    h_lon = col_b.number_input("Longitude", -180.0, 180.0, -74.0, key="heli_lon")
    h_r = col_c.number_input("Radius (km)", 1, 100, 30, key="heli_radius")

    if st.button("Search Helipads", key="heli_search"):
        with st.spinner("Querying Overpass API..."):
            result = _query_overpass_heliports(h_lat, h_lon, int(h_r * 1000))
        if result and "_error" not in result and "elements" in result:
            elements = result["elements"]
            st.success(f"Found {len(elements)} heliport/helipad(s) within {h_r} km")
            if elements:
                osm_map = _create_map(h_lat, h_lon, zoom=10)
                rows = []
                for el in elements[:200]:
                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")
                    if lat and lon:
                        name = el.get("tags", {}).get("name", "Helipad")
                        popup_html = f"<b>{escape(name)}</b><br>OSM ID: {el.get('id', 'N/A')}"
                        folium.CircleMarker(
                            [lat, lon], radius=5, color=ACCENT_ORANGE, fill=True,
                            fill_color=ACCENT_ORANGE, fill_opacity=0.7,
                            popup=_safe_popup(popup_html),
                            tooltip=escape(name),
                        ).add_to(osm_map)
                        rows.append({"Name": name, "Lat": lat, "Lon": lon, "OSM ID": el.get("id")})
                _render_map(osm_map)
                if rows:
                    osm_df = pd.DataFrame(rows)
                    st.dataframe(osm_df, width="stretch")
        else:
            err = result.get("_error", "Unknown error") if isinstance(result, dict) else "No response"
            st.warning(f"No results or error: {err}")

    # Table
    df = pd.DataFrame(data)
    df = df[["name", "city", "country", "type", "notes"]]
    df.columns = ["Heliport", "City", "Country", "Type", "Notes"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "heliports.csv", "text/csv", key="dl_heliports")


def _render_spaceports():
    """Mode 9: Space Ports & Launch Sites."""
    st.markdown("### Spaceports & Launch Sites")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "From the historic launch pads of Kennedy Space Center and Baikonur Cosmodrome "
        "to new commercial spaceports like SpaceX's Starbase in Boca Chica, Texas. "
        "The space launch industry has evolved from government monopolies to a vibrant "
        "commercial sector with sites on every inhabited continent. Equatorial locations "
        "like Kourou offer energy advantages for geostationary orbit launches."
        "</p>",
        unsafe_allow_html=True,
    )

    data = SPACEPORTS

    c1, c2, c3 = st.columns(3)
    c1.metric("Launch Sites", len(data))
    operators = len(set(d["operator"] for d in data))
    countries = len(set(d["country"] for d in data))
    c2.metric("Operators", operators)
    c3.metric("Countries", countries)

    # Map
    m = _create_map(20, 30, zoom=2)
    for sp in data:
        popup_html = (
            f"<b>{escape(sp['name'])}</b><br>"
            f"Operator: {escape(sp['operator'])}<br>"
            f"Country: {escape(sp['country'])}<br>"
            f"<em>{escape(sp['notes'])}</em>"
        )
        folium.Marker(
            location=[sp["lat"], sp["lon"]],
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{escape(sp['name'])} ({escape(sp['operator'])})",
            icon=folium.Icon(color="purple", icon="rocket", prefix="fa"),
        ).add_to(m)
    _render_map(m)

    # Operator breakdown chart
    op_counts = {}
    for sp in data:
        op = sp["operator"].split("/")[0].strip()
        op_counts[op] = op_counts.get(op, 0) + 1
    sorted_ops = sorted(op_counts.items(), key=lambda x: x[1], reverse=True)
    op_names = [o[0] for o in sorted_ops]
    op_vals = [o[1] for o in sorted_ops]

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)
    bars = ax.bar(op_names, op_vals, color=ACCENT_VIOLET, alpha=0.85, edgecolor="#2a3550")
    ax.set_title("Launch Sites by Primary Operator", color=TEXT_PRIMARY, fontsize=14, fontweight="bold")
    ax.set_ylabel("Number of Sites", color=TEXT_PRIMARY, fontsize=11)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    plt.xticks(rotation=45, ha="right")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.yaxis.grid(True, color="#2a3550", alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = pd.DataFrame(data)
    df = df[["name", "operator", "country", "lat", "lon", "notes"]]
    df.columns = ["Launch Site", "Operator", "Country", "Lat", "Lon", "Notes"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "spaceports.csv", "text/csv", key="dl_spaceports")


def _render_atc():
    """Mode 10: Air Traffic Control."""
    st.markdown("### Air Traffic Control Centers & Busiest Airspaces")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">'
        "Major air traffic control centers managing the world's busiest airspaces. "
        "From New York TRACON (N90) handling approaches to JFK, Newark, and LaGuardia, "
        "to the North Atlantic oceanic corridors managed by Gander and Shanwick, "
        "these centers keep millions of flights safe each year. "
        "The airspace above Europe is among the most congested, with DFS Germany alone "
        "handling over 3 million flights annually."
        "</p>",
        unsafe_allow_html=True,
    )

    data = ATC_CENTERS

    # Type filter
    atc_types = sorted(set(c["type"] for c in data))
    sel_types = st.multiselect("Filter by ATC type", atc_types, default=atc_types, key="atc_type")
    data = [c for c in data if c["type"] in sel_types] if sel_types else ATC_CENTERS

    c1, c2, c3 = st.columns(3)
    c1.metric("ATC Centers", len(data))
    c2.metric("Types", len(set(c["type"] for c in data)))
    c3.metric("Countries", len(set(c["country"] for c in data)))

    # Type colors
    type_colors = {
        "Upper Area Control": ACCENT_CYAN,
        "Area Control": ACCENT_BLUE,
        "TRACON": ACCENT_VIOLET,
        "ARTCC": ACCENT_AMBER,
        "Oceanic Control": ACCENT_EMERALD,
    }

    # Map
    m = _create_map(30, 10, zoom=2)
    for center in data:
        color = type_colors.get(center["type"], center.get("color", ACCENT_CYAN))
        popup_html = (
            f"<b>{escape(center['name'])}</b><br>"
            f"City: {escape(center['city'])}, {escape(center['country'])}<br>"
            f"Type: {escape(center['type'])}<br>"
            f"<em>{escape(center['notes'])}</em>"
        )
        folium.CircleMarker(
            location=[center["lat"], center["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=_safe_popup(popup_html, 320),
            tooltip=f"{escape(center['name'])} ({escape(center['type'])})",
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(17,24,39,0.9); padding: 10px 14px; border-radius: 8px;
                border: 1px solid #2a3550; font-size: 12px; color: #e8ecf4;">
        <b>ATC Types</b><br>
        <span style="color: #06b6d4;">&#9679;</span> Upper Area Control<br>
        <span style="color: #3b82f6;">&#9679;</span> Area Control<br>
        <span style="color: #8b5cf6;">&#9679;</span> TRACON<br>
        <span style="color: #f59e0b;">&#9679;</span> ARTCC<br>
        <span style="color: #10b981;">&#9679;</span> Oceanic Control
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    _render_map(m)

    # Type distribution pie chart
    type_counts = {}
    for c in ATC_CENTERS:
        type_counts[c["type"]] = type_counts.get(c["type"], 0) + 1
    labels = list(type_counts.keys())
    sizes = list(type_counts.values())
    colors = [type_colors.get(t, ACCENT_CYAN) for t in labels]

    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=140, textprops={"color": TEXT_PRIMARY, "fontsize": 10},
    )
    for autotext in autotexts:
        autotext.set_color(BG_DARK)
        autotext.set_fontweight("bold")
    ax.set_title("ATC Center Types Distribution", color=TEXT_PRIMARY, fontsize=14, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = pd.DataFrame(data)
    df = df[["name", "city", "country", "type", "notes"]]
    df.columns = ["ATC Center", "City", "Country", "Type", "Notes"]
    st.dataframe(df, width="stretch")

    csv = _df_to_csv(df)
    st.download_button("Download CSV", csv, "atc_centers.csv", "text/csv", key="dl_atc")


# ======================================================================
# MAIN RENDER FUNCTION
# ======================================================================
def render_airport_maps_tab():
    """Main entry point for the Airports & Aviation Maps tab."""

    # Tab header
    st.markdown(
        '<div class="tab-header amber">'
        '<h4>✈️ Airports & Aviation Maps</h4>'
        '<p>World airports, busiest hubs, aviation history & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Mode selector
    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        index=0,
        key="airport_map_mode",
        help="Choose from 10 different aviation map modes",
    )

    st.markdown("---")

    # Dispatch to mode renderer
    mode_renderers = {
        "World's Busiest Airports": _render_busiest_airports,
        "Longest Runways": _render_longest_runways,
        "Extreme Airports": _render_extreme_airports,
        "Aviation History": _render_aviation_history,
        "Military Airbases": _render_military_airbases,
        "Abandoned Airfields": _render_abandoned_airfields,
        "Airline Hubs": _render_airline_hubs,
        "Helicopter & Heliports": _render_heliports,
        "Space Ports & Launch Sites": _render_spaceports,
        "Air Traffic Control": _render_atc,
    }

    renderer = mode_renderers.get(mode)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown map mode: {mode}")
