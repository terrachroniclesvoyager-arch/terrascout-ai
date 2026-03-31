# -*- coding: utf-8 -*-
"""
Islands & Archipelagos of the World module for TerraScout AI.
Comprehensive explorer of islands, atolls, archipelagos, and island nations
with 10 interactive map modes. Uses curated datasets and free public APIs
(Overpass/OSM, Wikipedia REST, Nominatim). No API keys required.
"""

import io
import logging
import streamlit as st
import pandas as pd
try:
    import folium
    import folium.plugins as plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_CYAN = "#06b6d4"
ACCENT_EMERALD = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_PINK = "#ec4899"
ACCENT_RED = "#ef4444"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"
MUTED_COLOR = "#5a6580"
SECONDARY_COLOR = "#8b97b0"

# ═══════════════════════════════════════════════════════════════
# MAP MODES
# ═══════════════════════════════════════════════════════════════
MAP_MODES = [
    "1. World's Largest Islands",
    "2. Volcanic Islands",
    "3. Coral Atolls",
    "4. Island Nations",
    "5. Uninhabited Islands",
    "6. Island Biodiversity Hotspots",
    "7. Artificial Islands",
    "8. Prison Islands",
    "9. Disappearing Islands",
    "10. Island Mysteries",
]

# ═══════════════════════════════════════════════════════════════
# 1. WORLD'S LARGEST ISLANDS (top 50 by area)
# ═══════════════════════════════════════════════════════════════
LARGEST_ISLANDS = [
    {"name": "Greenland", "country": "Denmark (autonomous)", "area_km2": 2166086, "lat": 71.71, "lon": -42.60, "population": 56421, "note": "Largest island, 80% ice-covered"},
    {"name": "New Guinea", "country": "Indonesia / Papua New Guinea", "area_km2": 786380, "lat": -5.00, "lon": 141.00, "population": 12000000, "note": "Most linguistically diverse island"},
    {"name": "Borneo", "country": "Indonesia / Malaysia / Brunei", "area_km2": 748168, "lat": 1.00, "lon": 114.00, "population": 21258000, "note": "Home to orangutans and ancient rainforest"},
    {"name": "Madagascar", "country": "Madagascar", "area_km2": 587041, "lat": -18.77, "lon": 46.87, "population": 28812195, "note": "90% of wildlife found nowhere else on Earth"},
    {"name": "Baffin Island", "country": "Canada", "area_km2": 507451, "lat": 68.00, "lon": -70.00, "population": 13039, "note": "Largest island in Canada"},
    {"name": "Sumatra", "country": "Indonesia", "area_km2": 473481, "lat": -0.59, "lon": 101.34, "population": 58680000, "note": "Home to Sumatran tiger, rhino, elephant"},
    {"name": "Honshu", "country": "Japan", "area_km2": 227960, "lat": 36.00, "lon": 138.00, "population": 104000000, "note": "Most populous island in the world"},
    {"name": "Great Britain", "country": "United Kingdom", "area_km2": 209331, "lat": 54.00, "lon": -2.00, "population": 63182000, "note": "Largest island in Europe"},
    {"name": "Victoria Island", "country": "Canada", "area_km2": 217291, "lat": 71.00, "lon": -110.00, "population": 2100, "note": "8th largest island, Arctic archipelago"},
    {"name": "Ellesmere Island", "country": "Canada", "area_km2": 196236, "lat": 80.00, "lon": -80.00, "population": 146, "note": "Northernmost island in Canada"},
    {"name": "Sulawesi (Celebes)", "country": "Indonesia", "area_km2": 180681, "lat": -2.00, "lon": 121.00, "population": 19360000, "note": "Unique K-shaped island with endemic species"},
    {"name": "South Island", "country": "New Zealand", "area_km2": 150437, "lat": -44.00, "lon": 170.00, "population": 1138748, "note": "Home to the Southern Alps and fjords"},
    {"name": "Java", "country": "Indonesia", "area_km2": 129000, "lat": -7.49, "lon": 110.00, "population": 151600000, "note": "Most densely populated large island"},
    {"name": "North Island", "country": "New Zealand", "area_km2": 113729, "lat": -38.00, "lon": 176.00, "population": 3860300, "note": "Geothermal wonders and Maori culture"},
    {"name": "Luzon", "country": "Philippines", "area_km2": 109965, "lat": 16.00, "lon": 121.00, "population": 53336134, "note": "Capital island of the Philippines"},
    {"name": "Iceland", "country": "Iceland", "area_km2": 103000, "lat": 64.96, "lon": -19.02, "population": 376248, "note": "Land of fire and ice, volcanic island"},
    {"name": "Mindanao", "country": "Philippines", "area_km2": 97530, "lat": 7.50, "lon": 126.00, "population": 25537691, "note": "Home to Mount Apo, Philippines highest peak"},
    {"name": "Ireland", "country": "Ireland / UK", "area_km2": 84421, "lat": 53.00, "lon": -8.00, "population": 6900000, "note": "The Emerald Isle"},
    {"name": "Hokkaido", "country": "Japan", "area_km2": 83424, "lat": 43.00, "lon": 143.00, "population": 5228885, "note": "Japan's northern frontier, home to Ainu"},
    {"name": "Hispaniola", "country": "Haiti / Dominican Republic", "area_km2": 76192, "lat": 19.00, "lon": -71.00, "population": 22278000, "note": "Two nations on one island"},
    {"name": "Sakhalin", "country": "Russia", "area_km2": 72493, "lat": 51.00, "lon": 143.00, "population": 497973, "note": "Largest Russian island"},
    {"name": "Banks Island", "country": "Canada", "area_km2": 70028, "lat": 73.00, "lon": -121.50, "population": 112, "note": "Arctic island, home to muskoxen"},
    {"name": "Sri Lanka", "country": "Sri Lanka", "area_km2": 65610, "lat": 7.87, "lon": 80.77, "population": 22156000, "note": "Teardrop of India"},
    {"name": "Tasmania", "country": "Australia", "area_km2": 64519, "lat": -42.00, "lon": 146.50, "population": 541071, "note": "Home of the Tasmanian devil"},
    {"name": "Devon Island", "country": "Canada", "area_km2": 55247, "lat": 75.00, "lon": -87.00, "population": 0, "note": "Largest uninhabited island on Earth"},
    {"name": "Tierra del Fuego", "country": "Argentina / Chile", "area_km2": 47992, "lat": -54.00, "lon": -69.00, "population": 250000, "note": "Land of Fire at the tip of South America"},
    {"name": "Alexander Island", "country": "Antarctica (UK claim)", "area_km2": 49070, "lat": -71.00, "lon": -70.00, "population": 0, "note": "Largest uninhabited island in Antarctica"},
    {"name": "Axel Heiberg Island", "country": "Canada", "area_km2": 43178, "lat": 79.50, "lon": -90.00, "population": 0, "note": "Arctic island with fossil forests"},
    {"name": "Melville Island", "country": "Canada", "area_km2": 42149, "lat": 75.50, "lon": -112.00, "population": 0, "note": "Part of the Queen Elizabeth Islands"},
    {"name": "Southampton Island", "country": "Canada", "area_km2": 41214, "lat": 64.50, "lon": -84.50, "population": 1000, "note": "At the mouth of Hudson Bay"},
    {"name": "Spitsbergen", "country": "Norway", "area_km2": 39044, "lat": 78.00, "lon": 16.00, "population": 2642, "note": "Svalbard main island, Arctic Norway"},
    {"name": "Kyushu", "country": "Japan", "area_km2": 36782, "lat": 33.00, "lon": 131.00, "population": 12970479, "note": "Southernmost major Japanese island"},
    {"name": "New Britain", "country": "Papua New Guinea", "area_km2": 36514, "lat": -6.00, "lon": 150.00, "population": 513926, "note": "Largest island of the Bismarck Archipelago"},
    {"name": "Taiwan", "country": "Taiwan", "area_km2": 35808, "lat": 23.70, "lon": 120.96, "population": 23570000, "note": "Ilha Formosa - Beautiful Island"},
    {"name": "Prince of Wales Island", "country": "Canada", "area_km2": 33339, "lat": 72.50, "lon": -99.00, "population": 0, "note": "Arctic Canadian island"},
    {"name": "Novaya Zemlya (North)", "country": "Russia", "area_km2": 33275, "lat": 74.00, "lon": 56.00, "population": 2716, "note": "Arctic Russia, former nuclear test site"},
    {"name": "Hainan", "country": "China", "area_km2": 33210, "lat": 19.20, "lon": 109.70, "population": 10081232, "note": "Tropical island, China's Hawaii"},
    {"name": "Timor", "country": "East Timor / Indonesia", "area_km2": 30777, "lat": -9.00, "lon": 125.50, "population": 3200000, "note": "Divided between two nations"},
    {"name": "Shikoku", "country": "Japan", "area_km2": 18800, "lat": 33.75, "lon": 133.50, "population": 3845534, "note": "Famous 88-temple pilgrimage route"},
    {"name": "Crete", "country": "Greece", "area_km2": 8450, "lat": 35.24, "lon": 24.90, "population": 623065, "note": "Largest Greek island, Minoan civilization"},
    {"name": "Corsica", "country": "France", "area_km2": 8680, "lat": 42.15, "lon": 9.11, "population": 340440, "note": "Birthplace of Napoleon Bonaparte"},
    {"name": "Sicily", "country": "Italy", "area_km2": 25711, "lat": 37.50, "lon": 14.00, "population": 4969147, "note": "Largest Mediterranean island, Mount Etna"},
    {"name": "Sardinia", "country": "Italy", "area_km2": 24090, "lat": 40.12, "lon": 9.01, "population": 1611621, "note": "One of the Blue Zones for longevity"},
    {"name": "Cuba", "country": "Cuba", "area_km2": 109884, "lat": 21.52, "lon": -79.95, "population": 11256372, "note": "Largest Caribbean island"},
    {"name": "Newfoundland", "country": "Canada", "area_km2": 108860, "lat": 48.50, "lon": -56.00, "population": 479105, "note": "First European settlement in Americas"},
    {"name": "Svalbard (Nordaustlandet)", "country": "Norway", "area_km2": 14443, "lat": 79.70, "lon": 22.00, "population": 0, "note": "Second largest Svalbard island"},
    {"name": "Maui", "country": "United States", "area_km2": 1883, "lat": 20.80, "lon": -156.33, "population": 164754, "note": "Valley Isle of Hawaii"},
    {"name": "Bali", "country": "Indonesia", "area_km2": 5780, "lat": -8.41, "lon": 115.19, "population": 4225384, "note": "Island of the Gods, Hindu culture"},
    {"name": "Zanzibar", "country": "Tanzania", "area_km2": 1666, "lat": -6.16, "lon": 39.20, "population": 1303569, "note": "Spice Island, Stone Town UNESCO site"},
    {"name": "Tenerife", "country": "Spain", "area_km2": 2034, "lat": 28.29, "lon": -16.63, "population": 928604, "note": "Largest Canary Island, Mount Teide"},
]

# ═══════════════════════════════════════════════════════════════
# 2. VOLCANIC ISLANDS
# ═══════════════════════════════════════════════════════════════
VOLCANIC_ISLANDS = [
    {"name": "Hawaii (Big Island)", "country": "United States", "lat": 19.59, "lon": -155.45, "volcano": "Kilauea / Mauna Loa", "status": "Active", "last_eruption": "2023", "elevation_m": 4207, "note": "World's most active volcano, shield volcano"},
    {"name": "Iceland", "country": "Iceland", "lat": 64.96, "lon": -19.02, "volcano": "Multiple (30+ active)", "status": "Active", "last_eruption": "2024", "elevation_m": 2110, "note": "Mid-Atlantic Ridge, land of fire and ice"},
    {"name": "Tenerife", "country": "Spain", "lat": 28.27, "lon": -16.64, "volcano": "Mount Teide", "status": "Dormant", "last_eruption": "1909", "elevation_m": 3718, "note": "Highest peak in Spain, Canary Islands"},
    {"name": "La Palma", "country": "Spain", "lat": 28.68, "lon": -17.87, "volcano": "Cumbre Vieja", "status": "Active", "last_eruption": "2021", "elevation_m": 2426, "note": "2021 eruption destroyed 3000+ buildings"},
    {"name": "Reunion", "country": "France", "lat": -21.12, "lon": 55.53, "volcano": "Piton de la Fournaise", "status": "Active", "last_eruption": "2024", "elevation_m": 2632, "note": "One of the most active volcanoes on Earth"},
    {"name": "Santorini", "country": "Greece", "lat": 36.39, "lon": 25.46, "volcano": "Santorini Caldera", "status": "Dormant", "last_eruption": "1950", "elevation_m": 567, "note": "Minoan eruption ~1600 BC destroyed civilization"},
    {"name": "Stromboli", "country": "Italy", "lat": 38.79, "lon": 15.21, "volcano": "Stromboli", "status": "Active", "last_eruption": "2024", "elevation_m": 924, "note": "Lighthouse of the Mediterranean, constant eruptions"},
    {"name": "Mount Etna (Sicily)", "country": "Italy", "lat": 37.75, "lon": 14.99, "volcano": "Mount Etna", "status": "Active", "last_eruption": "2024", "elevation_m": 3357, "note": "Tallest active volcano in Europe"},
    {"name": "Vulcano", "country": "Italy", "lat": 38.40, "lon": 14.96, "volcano": "Vulcano", "status": "Active", "last_eruption": "1890", "elevation_m": 500, "note": "Origin of the word 'volcano'"},
    {"name": "Montserrat", "country": "United Kingdom", "lat": 16.72, "lon": -62.18, "volcano": "Soufriere Hills", "status": "Active", "last_eruption": "2010", "elevation_m": 1050, "note": "Capital Plymouth buried in 1997 eruption"},
    {"name": "Krakatoa (Anak Krakatau)", "country": "Indonesia", "lat": -6.10, "lon": 105.42, "volcano": "Anak Krakatau", "status": "Active", "last_eruption": "2023", "elevation_m": 157, "note": "Child of legendary Krakatoa (1883 eruption)"},
    {"name": "Isabela Island", "country": "Ecuador (Galapagos)", "lat": -0.83, "lon": -91.13, "volcano": "Wolf / Sierra Negra", "status": "Active", "last_eruption": "2022", "elevation_m": 1707, "note": "Largest Galapagos island, 5 shield volcanoes"},
    {"name": "Fernandina Island", "country": "Ecuador (Galapagos)", "lat": -0.37, "lon": -91.55, "volcano": "La Cumbre", "status": "Active", "last_eruption": "2024", "elevation_m": 1476, "note": "Most pristine Galapagos island"},
    {"name": "Jeju Island", "country": "South Korea", "lat": 33.36, "lon": 126.53, "volcano": "Hallasan", "status": "Dormant", "last_eruption": "1007", "elevation_m": 1947, "note": "UNESCO World Heritage volcanic island"},
    {"name": "Surtsey", "country": "Iceland", "lat": 63.30, "lon": -20.60, "volcano": "Surtsey", "status": "Dormant", "last_eruption": "1967", "elevation_m": 155, "note": "Born from the sea in 1963, UNESCO site"},
    {"name": "Miyake-jima", "country": "Japan", "lat": 34.08, "lon": 139.53, "volcano": "Mount Oyama", "status": "Active", "last_eruption": "2005", "elevation_m": 816, "note": "Evacuated in 2000 due to toxic gas"},
    {"name": "White Island (Whakaari)", "country": "New Zealand", "lat": -37.52, "lon": 177.18, "volcano": "Whakaari", "status": "Active", "last_eruption": "2019", "elevation_m": 321, "note": "Deadly 2019 eruption, marine volcano"},
    {"name": "Nisyros", "country": "Greece", "lat": 36.58, "lon": 27.17, "volcano": "Nisyros", "status": "Dormant", "last_eruption": "1888", "elevation_m": 698, "note": "Active volcanic caldera visitors can walk into"},
    {"name": "Tristan da Cunha", "country": "United Kingdom", "lat": -37.11, "lon": -12.28, "volcano": "Queen Mary's Peak", "status": "Active", "last_eruption": "1961", "elevation_m": 2062, "note": "Most remote inhabited island, volcanic"},
    {"name": "Deception Island", "country": "Antarctica (disputed)", "lat": -62.97, "lon": -60.65, "volcano": "Deception Island", "status": "Active", "last_eruption": "1970", "elevation_m": 576, "note": "Volcanic caldera, hot springs in Antarctica"},
    {"name": "Heard Island", "country": "Australia", "lat": -53.10, "lon": 73.51, "volcano": "Big Ben", "status": "Active", "last_eruption": "2023", "elevation_m": 2745, "note": "Remote sub-Antarctic active volcano"},
    {"name": "Aogashima", "country": "Japan", "lat": 32.45, "lon": 139.77, "volcano": "Aogashima", "status": "Dormant", "last_eruption": "1785", "elevation_m": 423, "note": "Inhabited volcanic caldera, stunning landscape"},
    {"name": "Piton de la Fournaise", "country": "France (Reunion)", "lat": -21.23, "lon": 55.71, "volcano": "Piton de la Fournaise", "status": "Active", "last_eruption": "2024", "elevation_m": 2632, "note": "Erupts almost every year"},
    {"name": "Erta Ale", "country": "Ethiopia (Danakil)", "lat": 13.60, "lon": 40.67, "volcano": "Erta Ale", "status": "Active", "last_eruption": "2024", "elevation_m": 613, "note": "Persistent lava lake in Danakil Depression"},
]

# ═══════════════════════════════════════════════════════════════
# 3. CORAL ATOLLS
# ═══════════════════════════════════════════════════════════════
CORAL_ATOLLS = [
    {"name": "Male Atoll", "country": "Maldives", "lat": 4.18, "lon": 73.51, "type": "Atoll", "area_km2": 26.0, "max_elev_m": 2.4, "islands": 104, "note": "Capital of Maldives, one of the lowest nations"},
    {"name": "Ari Atoll", "country": "Maldives", "lat": 3.87, "lon": 72.84, "type": "Atoll", "area_km2": 89.0, "max_elev_m": 1.8, "islands": 82, "note": "Whale shark paradise, top dive destination"},
    {"name": "Addu Atoll", "country": "Maldives", "lat": -0.63, "lon": 73.16, "type": "Atoll", "area_km2": 15.0, "max_elev_m": 1.7, "islands": 23, "note": "Southernmost atoll of Maldives"},
    {"name": "Majuro Atoll", "country": "Marshall Islands", "lat": 7.09, "lon": 171.38, "type": "Atoll", "area_km2": 9.7, "max_elev_m": 3.0, "islands": 64, "note": "Capital of Marshall Islands, nuclear testing legacy"},
    {"name": "Bikini Atoll", "country": "Marshall Islands", "lat": 11.59, "lon": 165.38, "type": "Atoll", "area_km2": 6.0, "max_elev_m": 2.1, "islands": 23, "note": "Nuclear test site 1946-1958, UNESCO site"},
    {"name": "Kwajalein Atoll", "country": "Marshall Islands", "lat": 8.72, "lon": 167.73, "type": "Atoll", "area_km2": 16.4, "max_elev_m": 2.5, "islands": 97, "note": "World's largest atoll by lagoon area (2174 km2)"},
    {"name": "Tarawa", "country": "Kiribati", "lat": 1.45, "lon": 173.00, "type": "Atoll", "area_km2": 31.0, "max_elev_m": 3.0, "islands": 24, "note": "Capital of Kiribati, WWII battle site"},
    {"name": "Christmas Island (Kiritimati)", "country": "Kiribati", "lat": 1.87, "lon": -157.47, "type": "Atoll", "area_km2": 388.0, "max_elev_m": 13.0, "islands": 1, "note": "World's largest atoll by land area"},
    {"name": "Rangiroa", "country": "France (Tuamotu)", "lat": -15.13, "lon": -147.66, "type": "Atoll", "area_km2": 79.0, "max_elev_m": 3.0, "islands": 241, "note": "Second largest atoll in the world"},
    {"name": "Fakarava", "country": "France (Tuamotu)", "lat": -16.05, "lon": -145.66, "type": "Atoll", "area_km2": 16.0, "max_elev_m": 2.0, "islands": 90, "note": "UNESCO biosphere reserve"},
    {"name": "Tikehau", "country": "France (Tuamotu)", "lat": -15.00, "lon": -148.17, "type": "Atoll", "area_km2": 20.0, "max_elev_m": 2.0, "islands": 12, "note": "Jacques Cousteau called it the richest atoll"},
    {"name": "Funafuti", "country": "Tuvalu", "lat": -8.52, "lon": 179.20, "type": "Atoll", "area_km2": 2.4, "max_elev_m": 4.6, "islands": 30, "note": "Capital of Tuvalu, severely threatened by sea rise"},
    {"name": "Aldabra Atoll", "country": "Seychelles", "lat": -9.42, "lon": 46.35, "type": "Raised atoll", "area_km2": 155.0, "max_elev_m": 8.0, "islands": 4, "note": "UNESCO site, 100,000+ giant tortoises"},
    {"name": "Diego Garcia", "country": "UK (BIOT)", "lat": -7.32, "lon": 72.42, "type": "Atoll", "area_km2": 27.2, "max_elev_m": 3.0, "islands": 1, "note": "US military base, displaced Chagossians"},
    {"name": "Palmyra Atoll", "country": "United States", "lat": 5.88, "lon": -162.08, "type": "Atoll", "area_km2": 12.0, "max_elev_m": 2.0, "islands": 50, "note": "National Wildlife Refuge, no permanent residents"},
    {"name": "Wake Island", "country": "United States", "lat": 19.28, "lon": 166.63, "type": "Atoll", "area_km2": 6.5, "max_elev_m": 6.1, "islands": 3, "note": "WWII battle site, US military airfield"},
    {"name": "Midway Atoll", "country": "United States", "lat": 28.21, "lon": -177.37, "type": "Atoll", "area_km2": 6.2, "max_elev_m": 4.0, "islands": 3, "note": "WWII turning point, albatross breeding ground"},
    {"name": "Turneffe Atoll", "country": "Belize", "lat": 17.52, "lon": -87.83, "type": "Atoll", "area_km2": 532.0, "max_elev_m": 2.0, "islands": 200, "note": "Largest atoll in the Caribbean"},
    {"name": "Enewetak Atoll", "country": "Marshall Islands", "lat": 11.50, "lon": 162.35, "type": "Atoll", "area_km2": 5.85, "max_elev_m": 2.0, "islands": 40, "note": "43 nuclear tests, Runit Dome containment"},
    {"name": "Huvadhu Atoll", "country": "Maldives", "lat": 0.50, "lon": 73.30, "type": "Atoll", "area_km2": 38.5, "max_elev_m": 1.5, "islands": 255, "note": "One of the largest natural atolls by lagoon"},
]

# ═══════════════════════════════════════════════════════════════
# 4. ISLAND NATIONS
# ═══════════════════════════════════════════════════════════════
ISLAND_NATIONS = [
    {"name": "Indonesia", "lat": -2.00, "lon": 118.00, "population": 277534000, "area_km2": 1904569, "islands_count": 17508, "gdp_per_capita": 4788, "capital": "Jakarta", "note": "World's largest archipelago nation"},
    {"name": "Japan", "lat": 36.20, "lon": 138.25, "population": 125700000, "area_km2": 377975, "islands_count": 6852, "gdp_per_capita": 33815, "capital": "Tokyo", "note": "3rd largest economy, 4 main islands"},
    {"name": "Philippines", "lat": 12.88, "lon": 121.77, "population": 115559000, "area_km2": 300000, "islands_count": 7641, "gdp_per_capita": 3623, "capital": "Manila", "note": "Pearl of the Orient Seas"},
    {"name": "United Kingdom", "lat": 55.38, "lon": -3.44, "population": 67886000, "area_km2": 243610, "islands_count": 6289, "gdp_per_capita": 46125, "capital": "London", "note": "Island nation with global influence"},
    {"name": "Cuba", "lat": 21.52, "lon": -77.78, "population": 11256000, "area_km2": 109884, "islands_count": 4195, "gdp_per_capita": 9500, "capital": "Havana", "note": "Largest Caribbean island nation"},
    {"name": "Sri Lanka", "lat": 7.87, "lon": 80.77, "population": 22156000, "area_km2": 65610, "islands_count": 1, "gdp_per_capita": 3354, "capital": "Sri Jayawardenepura Kotte", "note": "Pearl of the Indian Ocean"},
    {"name": "New Zealand", "lat": -40.90, "lon": 174.89, "population": 5135000, "area_km2": 268838, "islands_count": 600, "gdp_per_capita": 48781, "capital": "Wellington", "note": "Aotearoa, land of the long white cloud"},
    {"name": "Taiwan", "lat": 23.70, "lon": 120.96, "population": 23570000, "area_km2": 36193, "islands_count": 166, "gdp_per_capita": 33140, "capital": "Taipei", "note": "Semiconductor powerhouse"},
    {"name": "Madagascar", "lat": -18.77, "lon": 46.87, "population": 28812000, "area_km2": 587041, "islands_count": 1, "gdp_per_capita": 515, "capital": "Antananarivo", "note": "90% endemic wildlife"},
    {"name": "Iceland", "lat": 64.96, "lon": -19.02, "population": 376000, "area_km2": 103000, "islands_count": 30, "gdp_per_capita": 73167, "capital": "Reykjavik", "note": "Northernmost capital city"},
    {"name": "Bahamas", "lat": 25.03, "lon": -77.40, "population": 407906, "area_km2": 13943, "islands_count": 700, "gdp_per_capita": 34864, "capital": "Nassau", "note": "700 islands, 16 inhabited"},
    {"name": "Maldives", "lat": 3.20, "lon": 73.22, "population": 540544, "area_km2": 298, "islands_count": 1192, "gdp_per_capita": 12527, "capital": "Male", "note": "Lowest-lying country, avg 1.5m above sea"},
    {"name": "Malta", "lat": 35.94, "lon": 14.38, "population": 519562, "area_km2": 316, "islands_count": 3, "gdp_per_capita": 34834, "capital": "Valletta", "note": "Knights of Malta, strategic Mediterranean"},
    {"name": "Singapore", "lat": 1.35, "lon": 103.82, "population": 5637000, "area_km2": 733, "islands_count": 63, "gdp_per_capita": 65234, "capital": "Singapore", "note": "City-state, one of the richest nations"},
    {"name": "Fiji", "lat": -17.71, "lon": 178.07, "population": 929766, "area_km2": 18274, "islands_count": 333, "gdp_per_capita": 5318, "capital": "Suva", "note": "Heart of the South Pacific"},
    {"name": "Mauritius", "lat": -20.35, "lon": 57.55, "population": 1266000, "area_km2": 2040, "islands_count": 18, "gdp_per_capita": 10218, "capital": "Port Louis", "note": "Home of the extinct dodo"},
    {"name": "Tonga", "lat": -21.18, "lon": -175.20, "population": 100209, "area_km2": 747, "islands_count": 169, "gdp_per_capita": 4903, "capital": "Nukualofa", "note": "Only remaining Polynesian monarchy"},
    {"name": "Samoa", "lat": -13.76, "lon": -172.10, "population": 218764, "area_km2": 2842, "islands_count": 9, "gdp_per_capita": 4067, "capital": "Apia", "note": "Heart of Polynesia"},
    {"name": "Seychelles", "lat": -4.68, "lon": 55.49, "population": 99202, "area_km2": 459, "islands_count": 115, "gdp_per_capita": 14653, "capital": "Victoria", "note": "Smallest African nation by population"},
    {"name": "Bahrain", "lat": 26.07, "lon": 50.55, "population": 1501635, "area_km2": 778, "islands_count": 33, "gdp_per_capita": 27238, "capital": "Manama", "note": "Pearl diving heritage, F1 Grand Prix"},
    {"name": "Comoros", "lat": -12.24, "lon": 44.26, "population": 836774, "area_km2": 1862, "islands_count": 4, "gdp_per_capita": 1402, "capital": "Moroni", "note": "Perfume Islands, ylang-ylang producer"},
    {"name": "Cape Verde", "lat": 16.00, "lon": -24.00, "population": 561898, "area_km2": 4033, "islands_count": 10, "gdp_per_capita": 3603, "capital": "Praia", "note": "Volcanic archipelago off West Africa"},
    {"name": "Palau", "lat": 7.51, "lon": 134.58, "population": 18024, "area_km2": 459, "islands_count": 340, "gdp_per_capita": 14907, "capital": "Ngerulmud", "note": "Rock Islands, jellyfish lake"},
    {"name": "Kiribati", "lat": 1.87, "lon": -157.36, "population": 119449, "area_km2": 811, "islands_count": 33, "gdp_per_capita": 1652, "capital": "Tarawa", "note": "Spans all 4 hemispheres"},
    {"name": "Tuvalu", "lat": -7.48, "lon": 178.68, "population": 11792, "area_km2": 26, "islands_count": 9, "gdp_per_capita": 4143, "capital": "Funafuti", "note": "4th smallest country, sinking nation"},
    {"name": "Nauru", "lat": -0.52, "lon": 166.93, "population": 10876, "area_km2": 21, "islands_count": 1, "gdp_per_capita": 11832, "capital": "Yaren", "note": "Smallest republic, phosphate mining legacy"},
    {"name": "Marshall Islands", "lat": 7.09, "lon": 171.18, "population": 59190, "area_km2": 181, "islands_count": 1156, "gdp_per_capita": 4073, "capital": "Majuro", "note": "Nuclear test legacy, rising seas threat"},
]

# ═══════════════════════════════════════════════════════════════
# 5. UNINHABITED ISLANDS
# ═══════════════════════════════════════════════════════════════
UNINHABITED_ISLANDS = [
    {"name": "Devon Island", "country": "Canada", "lat": 75.00, "lon": -87.00, "area_km2": 55247, "reason": "Extreme Arctic climate", "note": "Largest uninhabited island on Earth, NASA Mars analog site"},
    {"name": "Bouvet Island", "country": "Norway", "lat": -54.43, "lon": 3.38, "area_km2": 49, "reason": "Most remote island", "note": "1700 km from nearest land, 93% glacier-covered"},
    {"name": "Heard Island", "country": "Australia", "lat": -53.10, "lon": 73.51, "area_km2": 368, "reason": "Remote, active volcano", "note": "Sub-Antarctic volcanic island, UNESCO World Heritage"},
    {"name": "Clipperton Island", "country": "France", "lat": 10.30, "lon": -109.22, "area_km2": 6, "reason": "Remote, inhospitable", "note": "Only coral atoll in Eastern Pacific, tragic history"},
    {"name": "Ball's Pyramid", "country": "Australia", "lat": -31.75, "lon": 159.25, "area_km2": 0.01, "reason": "Volcanic sea stack", "note": "Tallest volcanic sea stack (562m), rediscovered stick insects"},
    {"name": "Kerguelen Islands", "country": "France", "lat": -49.28, "lon": 69.35, "area_km2": 7215, "reason": "Extreme isolation", "note": "Desolation Islands, French research stations only"},
    {"name": "Henderson Island", "country": "United Kingdom", "lat": -24.37, "lon": -128.33, "area_km2": 37, "reason": "Remote, raised coral", "note": "UNESCO site, despite remoteness covered in plastic pollution"},
    {"name": "Howland Island", "country": "United States", "lat": 0.81, "lon": -176.62, "area_km2": 2.6, "reason": "No fresh water", "note": "Amelia Earhart was headed here when she disappeared"},
    {"name": "Palmyra Atoll", "country": "United States", "lat": 5.88, "lon": -162.08, "area_km2": 12, "reason": "Wildlife refuge", "note": "Pristine coral atoll, research station only"},
    {"name": "Aldabra Atoll", "country": "Seychelles", "lat": -9.42, "lon": 46.35, "area_km2": 155, "reason": "Protected reserve", "note": "100,000+ giant tortoises, UNESCO World Heritage"},
    {"name": "Jan Mayen", "country": "Norway", "lat": 71.00, "lon": -8.32, "area_km2": 377, "reason": "Military/weather station only", "note": "Beerenberg volcano, northernmost active volcano"},
    {"name": "South Georgia", "country": "United Kingdom", "lat": -54.28, "lon": -36.51, "area_km2": 3903, "reason": "Extreme sub-Antarctic", "note": "Shackleton's rescue destination, penguin colonies"},
    {"name": "Isla de la Juventud", "country": "Cuba", "lat": 21.73, "lon": -82.85, "area_km2": 2200, "reason": "Partially inhabited", "note": "Treasure Island inspiration, former pirate haven"},
    {"name": "Peter I Island", "country": "Norway (Antarctic)", "lat": -68.78, "lon": -90.58, "area_km2": 156, "reason": "Antarctic, volcanic", "note": "Most remote uninhabited island with a territorial claim"},
    {"name": "Campbell Island", "country": "New Zealand", "lat": -52.54, "lon": 169.15, "area_km2": 113, "reason": "Sub-Antarctic reserve", "note": "UNESCO site, world's southernmost trees"},
    {"name": "Antipodes Islands", "country": "New Zealand", "lat": -49.68, "lon": 178.77, "area_km2": 22, "reason": "Extreme remoteness", "note": "Named for being antipodal to Greenwich, UK"},
    {"name": "Navassa Island", "country": "United States", "lat": 18.40, "lon": -75.01, "area_km2": 5.4, "reason": "Disputed territory", "note": "Caribbean wildlife refuge, Haiti also claims"},
    {"name": "Jarvis Island", "country": "United States", "lat": -0.37, "lon": -160.01, "area_km2": 4.5, "reason": "No fresh water", "note": "Equatorial Pacific, guano mining history"},
    {"name": "Rockall", "country": "United Kingdom (disputed)", "lat": 57.60, "lon": -13.69, "area_km2": 0.0006, "reason": "Tiny sea rock", "note": "Uninhabitable rocky islet, multiple nations claim"},
    {"name": "Isla de Malpelo", "country": "Colombia", "lat": 4.00, "lon": -81.61, "area_km2": 1.2, "reason": "Military outpost only", "note": "UNESCO site, hammerhead shark aggregation"},
]

# ═══════════════════════════════════════════════════════════════
# 6. ISLAND BIODIVERSITY HOTSPOTS
# ═══════════════════════════════════════════════════════════════
BIODIVERSITY_ISLANDS = [
    {"name": "Madagascar", "country": "Madagascar", "lat": -18.77, "lon": 46.87, "endemic_pct": 90, "key_species": "Lemurs (100+ species), baobabs, chameleons", "threats": "Deforestation, slash-and-burn", "note": "90% of species found nowhere else on Earth"},
    {"name": "Galapagos Islands", "country": "Ecuador", "lat": -0.95, "lon": -90.97, "endemic_pct": 80, "key_species": "Giant tortoises, marine iguanas, Darwin's finches", "threats": "Invasive species, tourism pressure", "note": "Inspired Darwin's theory of evolution"},
    {"name": "Socotra", "country": "Yemen", "lat": 12.47, "lon": 53.87, "endemic_pct": 37, "key_species": "Dragon blood trees, desert roses, Socotra starling", "threats": "Climate change, cyclones", "note": "Galapagos of the Indian Ocean, alien landscape"},
    {"name": "New Caledonia", "country": "France", "lat": -21.95, "lon": 165.62, "endemic_pct": 76, "key_species": "Kagu bird, Amborella (oldest flowering plant lineage)", "threats": "Nickel mining, invasive species", "note": "World's largest lagoon, ancient Gondwana fragment"},
    {"name": "Sri Lanka", "country": "Sri Lanka", "lat": 7.87, "lon": 80.77, "endemic_pct": 27, "key_species": "Purple-faced langur, Sri Lanka blue magpie", "threats": "Habitat loss, plantations", "note": "Biodiversity hotspot within Western Ghats-Sri Lanka"},
    {"name": "Borneo", "country": "Malaysia/Indonesia/Brunei", "lat": 1.00, "lon": 114.00, "endemic_pct": 44, "key_species": "Orangutans, proboscis monkeys, Rafflesia", "threats": "Palm oil deforestation", "note": "Third largest island, ancient rainforest"},
    {"name": "Hawaii", "country": "United States", "lat": 20.80, "lon": -156.33, "endemic_pct": 90, "key_species": "Hawaiian honeycreepers, silverswords, happy-face spider", "threats": "Invasive species, habitat loss", "note": "Most isolated population center on Earth"},
    {"name": "New Zealand", "country": "New Zealand", "lat": -41.00, "lon": 174.00, "endemic_pct": 82, "key_species": "Kiwi, tuatara, kakapo, weta", "threats": "Invasive predators (rats, stoats)", "note": "Evolved without land mammals for 80M years"},
    {"name": "Cuba", "country": "Cuba", "lat": 21.52, "lon": -79.95, "endemic_pct": 50, "key_species": "Bee hummingbird (smallest bird), Cuban solenodon", "threats": "Habitat conversion", "note": "Caribbean biodiversity hotspot leader"},
    {"name": "Sulawesi", "country": "Indonesia", "lat": -2.00, "lon": 121.00, "endemic_pct": 62, "key_species": "Babirusa, anoa, maleo bird, tarsiers", "threats": "Mining, deforestation", "note": "Wallace Line boundary, unique biogeography"},
    {"name": "Philippines", "country": "Philippines", "lat": 12.88, "lon": 121.77, "endemic_pct": 64, "key_species": "Philippine eagle, tarsier, Palawan peacock-pheasant", "threats": "Deforestation, mining", "note": "One of the megadiverse countries"},
    {"name": "Reunion Island", "country": "France", "lat": -21.12, "lon": 55.53, "endemic_pct": 30, "key_species": "Reunion cuckooshrike, day geckos, orchids", "threats": "Invasive species, urbanization", "note": "Volcanic island with 3 distinct ecosystems"},
    {"name": "Canary Islands", "country": "Spain", "lat": 28.10, "lon": -15.40, "endemic_pct": 40, "key_species": "Canary Islands dragon tree, laurel pigeons, blue chaffinch", "threats": "Tourism development, wildfires", "note": "Macaronesian biodiversity hotspot"},
    {"name": "Taiwan", "country": "Taiwan", "lat": 23.70, "lon": 120.96, "endemic_pct": 26, "key_species": "Formosan black bear, Mikado pheasant, Taiwan blue magpie", "threats": "Development, typhoons", "note": "Mountain island with subtropical to alpine zones"},
    {"name": "Lord Howe Island", "country": "Australia", "lat": -31.56, "lon": 159.08, "endemic_pct": 50, "key_species": "Lord Howe woodhen, Kentia palm, stick insect", "threats": "Invasive rats (eradicated 2019)", "note": "UNESCO site, southernmost coral reef in world"},
    {"name": "Juan Fernandez Islands", "country": "Chile", "lat": -33.64, "lon": -78.85, "endemic_pct": 64, "key_species": "Juan Fernandez firecrown, Robinson Crusoe cabbage tree", "threats": "Invasive plants, rabbits", "note": "Real Robinson Crusoe island"},
    {"name": "Mauritius", "country": "Mauritius", "lat": -20.35, "lon": 57.55, "endemic_pct": 39, "key_species": "Pink pigeon, Mauritius kestrel, echo parakeet", "threats": "Habitat loss, invasive species", "note": "Home of the extinct dodo, conservation success stories"},
    {"name": "Seychelles (inner islands)", "country": "Seychelles", "lat": -4.58, "lon": 55.45, "endemic_pct": 45, "key_species": "Coco de mer, Seychelles black parrot, jellyfish tree", "threats": "Sea level rise, invasive species", "note": "Ancient granite islands, Aldabra giant tortoises"},
]

# ═══════════════════════════════════════════════════════════════
# 7. ARTIFICIAL ISLANDS
# ═══════════════════════════════════════════════════════════════
ARTIFICIAL_ISLANDS = [
    {"name": "Palm Jumeirah", "country": "UAE (Dubai)", "lat": 25.11, "lon": 55.14, "area_km2": 5.72, "year_built": 2006, "cost_usd": "12 billion", "purpose": "Luxury residential & tourism", "note": "Iconic palm-shaped island visible from space"},
    {"name": "Palm Jebel Ali", "country": "UAE (Dubai)", "lat": 25.00, "lon": 54.99, "area_km2": 8.4, "year_built": 2025, "cost_usd": "15 billion", "purpose": "Residential & commercial", "note": "Larger than Palm Jumeirah, still under development"},
    {"name": "The World Islands", "country": "UAE (Dubai)", "lat": 25.22, "lon": 55.17, "area_km2": 9.34, "year_built": 2008, "cost_usd": "14 billion", "purpose": "Luxury development", "note": "300 islands forming world map, mostly undeveloped"},
    {"name": "Kansai International Airport", "country": "Japan", "lat": 34.43, "lon": 135.24, "area_km2": 10.5, "year_built": 1994, "cost_usd": "20 billion", "purpose": "Airport", "note": "First airport on artificial island, sinking 1cm/year"},
    {"name": "Hong Kong International Airport", "country": "China (Hong Kong)", "lat": 22.31, "lon": 113.92, "area_km2": 12.48, "year_built": 1998, "cost_usd": "20 billion", "purpose": "Airport", "note": "Chek Lap Kok island, one of world's busiest airports"},
    {"name": "Flevopolder", "country": "Netherlands", "lat": 52.53, "lon": 5.47, "area_km2": 970, "year_built": 1968, "cost_usd": "N/A", "purpose": "Agriculture & habitation", "note": "Largest artificial island ever, reclaimed from sea"},
    {"name": "Hulhumale", "country": "Maldives", "lat": 4.21, "lon": 73.54, "area_km2": 4.0, "year_built": 2004, "cost_usd": "0.6 billion", "purpose": "Population relief", "note": "Built 2m above sea level to resist rising seas"},
    {"name": "Marker Wadden", "country": "Netherlands", "lat": 52.55, "lon": 5.38, "area_km2": 1.0, "year_built": 2016, "cost_usd": "75 million", "purpose": "Nature restoration", "note": "Artificial archipelago for habitat restoration"},
    {"name": "Peberholm", "country": "Denmark/Sweden", "lat": 55.57, "lon": 12.72, "area_km2": 1.3, "year_built": 2000, "cost_usd": "Part of Oresund Bridge", "purpose": "Bridge-tunnel connection", "note": "Built for Oresund Bridge, left as nature reserve"},
    {"name": "Port Island", "country": "Japan (Kobe)", "lat": 34.66, "lon": 135.22, "area_km2": 4.36, "year_built": 1981, "cost_usd": "5 billion", "purpose": "Commercial & residential", "note": "Automated transit, convention center"},
    {"name": "Odaiba", "country": "Japan (Tokyo)", "lat": 35.63, "lon": 139.78, "area_km2": 2.5, "year_built": 1853, "cost_usd": "N/A", "purpose": "Defense, now entertainment", "note": "Originally cannon batteries, now entertainment hub"},
    {"name": "Fiery Cross Reef", "country": "China (disputed)", "lat": 9.55, "lon": 112.89, "area_km2": 2.74, "year_built": 2014, "cost_usd": "Unknown", "purpose": "Military base", "note": "Controversial South China Sea military installation"},
    {"name": "Northstar Island", "country": "United States (Alaska)", "lat": 70.50, "lon": -148.70, "area_km2": 0.02, "year_built": 2001, "cost_usd": "1.5 billion", "purpose": "Oil drilling", "note": "Arctic artificial island for oil production"},
    {"name": "Treasure Island", "country": "United States (SF)", "lat": 37.82, "lon": -122.37, "area_km2": 1.6, "year_built": 1939, "cost_usd": "N/A", "purpose": "World's Fair, now residential", "note": "Built for 1939 Golden Gate International Exposition"},
    {"name": "Yas Island", "country": "UAE (Abu Dhabi)", "lat": 24.49, "lon": 54.60, "area_km2": 25.0, "year_built": 2009, "cost_usd": "40 billion", "purpose": "Entertainment & tourism", "note": "Ferrari World, Yas Marina F1 Circuit"},
    {"name": "Bluewaters Island", "country": "UAE (Dubai)", "lat": 25.08, "lon": 55.12, "area_km2": 0.17, "year_built": 2020, "cost_usd": "1.6 billion", "purpose": "Tourism & residential", "note": "Home of Ain Dubai, world's largest observation wheel"},
    {"name": "Venetian Islands", "country": "United States (Miami)", "lat": 25.79, "lon": -80.16, "area_km2": 0.4, "year_built": 1926, "cost_usd": "N/A", "purpose": "Residential", "note": "Chain of 6 artificial islands in Biscayne Bay"},
    {"name": "Spiral Island", "country": "Mexico", "lat": 21.22, "lon": -86.73, "area_km2": 0.001, "year_built": 1998, "cost_usd": "Minimal", "purpose": "Eco-experiment", "note": "Built from 250,000 plastic bottles by Richart Sowa"},
]

# ═══════════════════════════════════════════════════════════════
# 8. PRISON ISLANDS
# ═══════════════════════════════════════════════════════════════
PRISON_ISLANDS = [
    {"name": "Alcatraz Island", "country": "United States", "lat": 37.83, "lon": -122.42, "years_active": "1934-1963", "famous_inmates": "Al Capone, Robert Stroud (Birdman)", "status": "Museum / National Park", "note": "The Rock, in San Francisco Bay, no confirmed escapes"},
    {"name": "Robben Island", "country": "South Africa", "lat": -33.81, "lon": 18.37, "years_active": "1961-1991", "famous_inmates": "Nelson Mandela (18 years)", "status": "UNESCO World Heritage Site", "note": "Symbol of apartheid resistance"},
    {"name": "Devil's Island", "country": "France (French Guiana)", "lat": 5.29, "lon": -52.58, "years_active": "1852-1953", "famous_inmates": "Alfred Dreyfus, Henri Charriere (Papillon)", "status": "Open to visitors", "note": "Notorious penal colony, 80% death rate"},
    {"name": "Asinara", "country": "Italy (Sardinia)", "lat": 41.06, "lon": 8.26, "years_active": "1885-1998", "famous_inmates": "Mafia bosses (supercarcere)", "status": "National Park", "note": "Held Mafia supermax prisoners, now nature reserve"},
    {"name": "Goli Otok", "country": "Croatia", "lat": 44.84, "lon": 14.82, "years_active": "1949-1989", "famous_inmates": "Yugoslav political dissidents", "status": "Open to visitors", "note": "Yugoslav gulag, Tito's political prison"},
    {"name": "Bastoy Prison Island", "country": "Norway", "lat": 59.47, "lon": 10.45, "years_active": "1982-present", "famous_inmates": "Low-security inmates", "status": "Active minimum-security prison", "note": "World's first ecological prison, 16% recidivism"},
    {"name": "Imrali Island", "country": "Turkey", "lat": 40.51, "lon": 28.87, "years_active": "1935-present", "famous_inmates": "Abdullah Ocalan (PKK leader)", "status": "Active high-security prison", "note": "Maximum security island prison in Sea of Marmara"},
    {"name": "Chateau d'If", "country": "France", "lat": 43.28, "lon": 5.33, "years_active": "1540-1890", "famous_inmates": "Fictional: Edmond Dantes (Count of Monte Cristo)", "status": "Museum", "note": "Made famous by Alexandre Dumas novel"},
    {"name": "Hashima Island (Gunkanjima)", "country": "Japan", "lat": 32.63, "lon": 129.74, "years_active": "1930s-1945 (forced labor)", "famous_inmates": "Korean & Chinese forced laborers", "status": "UNESCO World Heritage (industrial)", "note": "Battleship Island, forced labor during WWII"},
    {"name": "Norfolk Island", "country": "Australia", "lat": -29.04, "lon": 167.95, "years_active": "1788-1855", "famous_inmates": "British convicts", "status": "Australian territory", "note": "One of the harshest penal colonies in history"},
    {"name": "Rikers Island", "country": "United States", "lat": 40.79, "lon": -73.89, "years_active": "1932-2027 (planned closure)", "famous_inmates": "Sid Vicious, Tupac Shakur, Lil Wayne", "status": "Active jail complex", "note": "NYC's main jail, 413 acres, slated for closure"},
    {"name": "Makronisos", "country": "Greece", "lat": 37.69, "lon": 24.08, "years_active": "1947-1974", "famous_inmates": "Greek political prisoners, communists", "status": "Historical monument", "note": "Greek Civil War and junta political prison camp"},
    {"name": "Isle of Pines (Nueva Gerona)", "country": "Cuba", "lat": 21.88, "lon": -82.80, "years_active": "1926-1967", "famous_inmates": "Fidel Castro (1953-1955)", "status": "Museum (Presidio Modelo)", "note": "Panopticon design prison, held Castro"},
    {"name": "Con Dao Islands", "country": "Vietnam", "lat": 8.69, "lon": 106.61, "years_active": "1862-1975", "famous_inmates": "Vietnamese political prisoners", "status": "National Park / Museum", "note": "Tiger cages, French & American era prisons"},
    {"name": "Solovetsky Islands", "country": "Russia", "lat": 65.10, "lon": 35.66, "years_active": "1920-1939", "famous_inmates": "Soviet gulag prisoners", "status": "UNESCO World Heritage Site", "note": "First Soviet labor camp, model for gulag system"},
    {"name": "Spike Island", "country": "Ireland", "lat": 51.84, "lon": -8.28, "years_active": "1847-2004", "famous_inmates": "Irish political prisoners, Fenians", "status": "Tourist attraction", "note": "Ireland's Alcatraz, Cork Harbour"},
    {"name": "Zanzibar Prison Island", "country": "Tanzania", "lat": -6.13, "lon": 39.17, "years_active": "1893-early 1900s", "famous_inmates": "Rebellious slaves", "status": "Tourist attraction", "note": "Originally for slave trade, now Aldabra tortoise sanctuary"},
    {"name": "Dawson Island", "country": "Chile", "lat": -53.75, "lon": -70.75, "years_active": "1973-1974", "famous_inmates": "Allende government officials", "status": "Naval base", "note": "Pinochet dictatorship concentration camp"},
]

# ═══════════════════════════════════════════════════════════════
# 9. DISAPPEARING ISLANDS
# ═══════════════════════════════════════════════════════════════
DISAPPEARING_ISLANDS = [
    {"name": "Tuvalu", "country": "Tuvalu", "lat": -7.48, "lon": 178.68, "max_elev_m": 4.6, "population": 11792, "threat": "Sea level rise", "timeline": "Uninhabitable by 2050-2100", "note": "First nation to explore digital statehood in metaverse"},
    {"name": "Kiribati", "country": "Kiribati", "lat": 1.87, "lon": -157.36, "max_elev_m": 3.0, "population": 119449, "threat": "Sea level rise, saltwater intrusion", "timeline": "Purchased land in Fiji as backup", "note": "Already relocating citizens, bought land in Fiji"},
    {"name": "Marshall Islands", "country": "Marshall Islands", "lat": 7.09, "lon": 171.18, "max_elev_m": 2.0, "population": 59190, "threat": "Sea level rise, nuclear legacy", "timeline": "Significant loss by 2050", "note": "Nuclear testing legacy compounds flooding problems"},
    {"name": "Maldives", "country": "Maldives", "lat": 3.20, "lon": 73.22, "max_elev_m": 2.4, "population": 540544, "threat": "Sea level rise", "timeline": "80% could be uninhabitable by 2100", "note": "Cabinet met underwater in 2009 to highlight crisis"},
    {"name": "Carteret Islands", "country": "Papua New Guinea", "lat": -4.77, "lon": 155.37, "max_elev_m": 1.5, "population": 2700, "threat": "Erosion, king tides", "timeline": "Evacuation ongoing since 2007", "note": "First climate refugees, relocated to Bougainville"},
    {"name": "Tangier Island", "country": "United States", "lat": 37.83, "lon": -75.99, "max_elev_m": 1.2, "population": 436, "threat": "Erosion, sea level rise", "timeline": "Could disappear by 2050", "note": "Chesapeake Bay island, losing 5m of shore per year"},
    {"name": "Isle de Jean Charles", "country": "United States", "lat": 29.40, "lon": -90.58, "max_elev_m": 1.0, "population": 85, "threat": "Land subsidence, sea rise, hurricanes", "timeline": "98% of land lost since 1955", "note": "First US climate refugees, $48M federal relocation"},
    {"name": "Lohachara Island", "country": "India", "lat": 21.62, "lon": 88.30, "max_elev_m": 0, "population": 0, "threat": "Submerged", "timeline": "Disappeared ~2006", "note": "First inhabited island lost to sea level rise"},
    {"name": "New Moore Island", "country": "India/Bangladesh (disputed)", "lat": 21.62, "lon": 88.67, "max_elev_m": 0, "population": 0, "threat": "Submerged", "timeline": "Disappeared 2010", "note": "Resolved an India-Bangladesh border dispute by vanishing"},
    {"name": "Ghoramara Island", "country": "India", "lat": 21.59, "lon": 88.10, "max_elev_m": 1.5, "population": 3000, "threat": "Erosion, flooding", "timeline": "50% lost since 1970s", "note": "Sundarbans island, shrinking rapidly"},
    {"name": "Nauru", "country": "Nauru", "lat": -0.52, "lon": 166.93, "max_elev_m": 71, "population": 10876, "threat": "Phosphate mining, sea rise", "timeline": "Interior wasteland, coast eroding", "note": "80% of land destroyed by phosphate mining"},
    {"name": "Funafuti (Tuvalu)", "country": "Tuvalu", "lat": -8.52, "lon": 179.20, "max_elev_m": 4.6, "population": 6320, "threat": "King tides, saltwater intrusion", "timeline": "Regular flooding events", "note": "Capital atoll, groundwater contaminated"},
    {"name": "Majuro (Marshall Islands)", "country": "Marshall Islands", "lat": 7.09, "lon": 171.38, "max_elev_m": 3.0, "population": 27797, "threat": "Sea rise, storm surge", "timeline": "Flooding worsening annually", "note": "Capital, 50% of population at risk"},
    {"name": "Sundarbans Islands", "country": "India / Bangladesh", "lat": 21.95, "lon": 89.18, "max_elev_m": 2.0, "population": 4500000, "threat": "Sea rise, cyclones, erosion", "timeline": "4 islands already submerged", "note": "World's largest mangrove forest, tiger habitat"},
    {"name": "Torres Strait Islands", "country": "Australia", "lat": -10.50, "lon": 142.20, "max_elev_m": 3.0, "population": 4514, "threat": "Sea level rise, erosion", "timeline": "Significant impact by 2050", "note": "Indigenous communities threatened, cultural loss"},
    {"name": "Tegua Island", "country": "Vanuatu", "lat": -13.26, "lon": 166.56, "max_elev_m": 2.5, "population": 100, "threat": "Coastal erosion, flooding", "timeline": "Village relocated 2005", "note": "UN recognized as among first climate relocations"},
    {"name": "Bhola Island", "country": "Bangladesh", "lat": 22.17, "lon": 90.73, "max_elev_m": 3.0, "population": 1600000, "threat": "Erosion, cyclones, flooding", "timeline": "Losing territory annually", "note": "Largest island in Bangladesh, millions at risk"},
    {"name": "Shishmaref", "country": "United States (Alaska)", "lat": 66.26, "lon": -166.07, "max_elev_m": 4.0, "population": 600, "threat": "Permafrost thaw, erosion", "timeline": "Voted to relocate in 2016", "note": "Inupiat village on barrier island, Arctic erosion"},
]

# ═══════════════════════════════════════════════════════════════
# 10. ISLAND MYSTERIES
# ═══════════════════════════════════════════════════════════════
ISLAND_MYSTERIES = [
    {"name": "Easter Island (Rapa Nui)", "country": "Chile", "lat": -27.11, "lon": -109.35, "mystery": "Moai statues", "category": "Archaeological", "note": "887 stone statues, ecological collapse theory debated, rongorongo script undeciphered"},
    {"name": "North Sentinel Island", "country": "India", "lat": 11.55, "lon": 92.24, "mystery": "Uncontacted tribe", "category": "Anthropological", "note": "Sentinelese reject all contact, killed missionary in 2018, protected by Indian law"},
    {"name": "Hashima Island (Gunkanjima)", "country": "Japan", "lat": 32.63, "lon": 129.74, "mystery": "Abandoned city", "category": "Urban exploration", "note": "Battleship Island, once most densely populated place, abandoned 1974, James Bond film location"},
    {"name": "Socotra Island", "country": "Yemen", "lat": 12.47, "lon": 53.87, "mystery": "Alien-looking flora", "category": "Natural wonder", "note": "Dragon blood trees, cucumber trees, 700 endemic species, 'most alien place on Earth'"},
    {"name": "Oak Island", "country": "Canada", "lat": 44.51, "lon": -64.30, "mystery": "Money Pit treasure", "category": "Treasure hunt", "note": "230+ years of treasure hunting, booby-trapped pit, possible Knights Templar or pirate treasure"},
    {"name": "Nan Madol", "country": "Micronesia", "lat": 6.84, "lon": 158.34, "mystery": "Megalithic ruins on water", "category": "Archaeological", "note": "Venice of the Pacific, 92 artificial islands, 750,000 tons of basalt, unknown builders"},
    {"name": "Bermuda Triangle area", "country": "Multiple", "lat": 25.00, "lon": -71.00, "mystery": "Ship & plane disappearances", "category": "Maritime mystery", "note": "Statistical analysis shows no more disappearances than other busy shipping lanes"},
    {"name": "Poveglia Island", "country": "Italy", "lat": 45.38, "lon": 12.33, "mystery": "Haunted island", "category": "Paranormal/Historical", "note": "Plague quarantine island, 160,000+ died, asylum 1922-1968, considered most haunted island"},
    {"name": "Palmyra Atoll", "country": "United States", "lat": 5.88, "lon": -162.08, "mystery": "Cursed atoll", "category": "Maritime mystery", "note": "Numerous shipwrecks, 1974 murder mystery, sailors report unease and strange phenomena"},
    {"name": "Yonaguni Monument", "country": "Japan", "lat": 24.44, "lon": 123.01, "mystery": "Underwater stone structure", "category": "Archaeological/Geological", "note": "Submerged terraced structure, debate: natural formation vs 10,000-year-old ruins"},
    {"name": "Flores Island", "country": "Indonesia", "lat": -8.66, "lon": 121.07, "mystery": "Homo floresiensis (Hobbit)", "category": "Anthropological", "note": "Homo floresiensis discovered 2003, 1m tall hominins, lived until 50,000 years ago"},
    {"name": "Bouvet Island", "country": "Norway", "lat": -54.43, "lon": 3.38, "mystery": "Abandoned lifeboat 1964", "category": "Maritime mystery", "note": "Most remote island, abandoned lifeboat found with no explanation, owner never identified"},
    {"name": "Snake Island (Ilha da Queimada)", "country": "Brazil", "lat": -24.49, "lon": -46.68, "mystery": "Deadliest island", "category": "Natural danger", "note": "1-5 golden lancehead vipers per square meter, humans banned, lighthouse keeper legends"},
    {"name": "Hy-Brasil", "country": "Legendary (Atlantic)", "lat": 51.00, "lon": -16.00, "mystery": "Phantom island", "category": "Cartographic mystery", "note": "Appeared on maps from 1325-1865, sailors claimed to see it, never confirmed to exist"},
    {"name": "Sable Island", "country": "Canada", "lat": 43.93, "lon": -59.92, "mystery": "Graveyard of the Atlantic", "category": "Maritime danger", "note": "350+ documented shipwrecks, shifting sand bars, wild horse population of unknown origin"},
    {"name": "Antikythera Island", "country": "Greece", "lat": 35.86, "lon": 23.31, "mystery": "Antikythera mechanism", "category": "Archaeological", "note": "Ancient Greek analog computer found in shipwreck, 2000-year-old astronomical calculator"},
    {"name": "Skellig Michael", "country": "Ireland", "lat": 51.77, "lon": -10.54, "mystery": "Monastic settlement", "category": "Archaeological", "note": "6th century monks lived on rock pinnacle, Star Wars filming location, UNESCO site"},
    {"name": "Thonis-Heracleion", "country": "Egypt", "lat": 31.30, "lon": 30.10, "mystery": "Sunken island city", "category": "Archaeological", "note": "Ancient Egyptian port city submerged for 1200 years, rediscovered 2000, still being excavated"},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _build_folium_map(data, lat_key="lat", lon_key="lon", name_key="name",
                      popup_fields=None, color="#06b6d4", zoom=2,
                      center_lat=20, center_lon=0, radius=6,
                      use_color_func=None):
    """Build a folium map with circle markers for the given data."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )

    for item in data:
        lat = item.get(lat_key)
        lon = item.get(lon_key)
        if lat is None or lon is None:
            continue

        # Build popup HTML
        popup_parts = [f"<b>{escape(str(item.get(name_key, 'Unknown')))}</b><br>"]
        if popup_fields:
            for field_label, field_key in popup_fields:
                val = item.get(field_key, "N/A")
                popup_parts.append(f"<b>{escape(field_label)}:</b> {escape(str(val))}<br>")

        popup_html = "".join(popup_parts)

        marker_color = color
        marker_radius = radius
        if use_color_func:
            marker_color, marker_radius = use_color_func(item)

        folium.CircleMarker(
            location=[lat, lon],
            radius=marker_radius,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(str(item.get(name_key, ""))),
        ).add_to(m)

    return m


def _render_folium(m, height=500):
    """Render a folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _make_chart_area_bar(df, x_col, y_col, title, color=ACCENT_CYAN, top_n=20):
    """Create a horizontal bar chart for area/size comparisons."""
    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.35)))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    plot_df = df.head(top_n).sort_values(y_col, ascending=True)
    bars = ax.barh(plot_df[x_col], plot_df[y_col], color=color, edgecolor=color, alpha=0.85)

    ax.set_xlabel(y_col, color=TEXT_COLOR, fontsize=11)
    ax.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(MUTED_COLOR)
    ax.spines["left"].set_color(MUTED_COLOR)
    ax.xaxis.label.set_color(TEXT_COLOR)

    for bar, val in zip(bars, plot_df[y_col]):
        ax.text(bar.get_width() + bar.get_width() * 0.01, bar.get_y() + bar.get_height() / 2,
                f" {val:,.0f}" if isinstance(val, (int, float)) else f" {val}",
                va="center", color=TEXT_COLOR, fontsize=8)

    plt.tight_layout()
    return fig


def _make_chart_scatter(df, x_col, y_col, label_col, title, x_label, y_label,
                        color=ACCENT_CYAN, log_x=False, log_y=False):
    """Create a scatter plot."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    x_vals = df[x_col].values
    y_vals = df[y_col].values

    ax.scatter(x_vals, y_vals, c=color, s=60, alpha=0.8, edgecolors="white", linewidths=0.5)

    for i, row in df.iterrows():
        ax.annotate(str(row[label_col])[:18], (row[x_col], row[y_col]),
                     fontsize=6, color=SECONDARY_COLOR, ha="left", va="bottom",
                     xytext=(4, 4), textcoords="offset points")

    if log_x:
        ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")

    ax.set_xlabel(x_label, color=TEXT_COLOR, fontsize=11)
    ax.set_ylabel(y_label, color=TEXT_COLOR, fontsize=11)
    ax.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(MUTED_COLOR)
    ax.spines["left"].set_color(MUTED_COLOR)
    ax.grid(True, alpha=0.15, color=MUTED_COLOR)

    plt.tight_layout()
    return fig


def _make_pie_chart(labels, values, title, colors=None):
    """Create a pie/donut chart."""
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    if colors is None:
        colors = [ACCENT_CYAN, ACCENT_EMERALD, ACCENT_AMBER, ACCENT_VIOLET,
                  ACCENT_PINK, ACCENT_RED, ACCENT_ORANGE, ACCENT_BLUE,
                  SECONDARY_COLOR, MUTED_COLOR] * 3

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors[:len(values)],
        autopct="%1.1f%%", startangle=90, pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor=BG_COLOR, linewidth=2),
    )
    for t in texts:
        t.set_color(TEXT_COLOR)
        t.set_fontsize(8)
    for t in autotexts:
        t.set_color(TEXT_COLOR)
        t.set_fontsize(7)

    ax.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    plt.tight_layout()
    return fig


def _csv_download(df, filename, label="Download CSV"):
    """Provide a CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(label, csv_buf.getvalue(), file_name=filename,
                       mime="text/csv", use_container_width=True)


def _stat_row(stats_dict):
    """Display a row of stat metrics."""
    cols = st.columns(len(stats_dict))
    for col, (label, value) in zip(cols, stats_dict.items()):
        col.metric(label, value)


# ═══════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_largest_islands():
    """Mode 1: World's Largest Islands."""
    st.markdown("""
    **The 50 largest islands on Earth** span from Greenland's ice-covered expanse (2.17 million km2)
    to tropical paradises like Bali and Zanzibar. Continental islands broke away from mainlands,
    while volcanic and coral islands formed from the ocean floor. Together they host over
    500 million people and contain some of Earth's most diverse ecosystems.
    """)

    df = pd.DataFrame(LARGEST_ISLANDS)
    df = df.sort_values("area_km2", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"

    _stat_row({
        "Islands Listed": len(df),
        "Total Area": f"{df['area_km2'].sum():,.0f} km2",
        "Total Population": f"{df['population'].sum():,.0f}",
        "Largest": "Greenland (2.17M km2)",
    })

    def _color_func(item):
        area = item.get("area_km2", 0)
        if area > 500000:
            return ACCENT_RED, 12
        elif area > 100000:
            return ACCENT_ORANGE, 9
        elif area > 50000:
            return ACCENT_AMBER, 7
        elif area > 10000:
            return ACCENT_CYAN, 5
        return ACCENT_EMERALD, 4

    m = _build_folium_map(
        LARGEST_ISLANDS,
        popup_fields=[("Country", "country"), ("Area", "area_km2"),
                      ("Population", "population"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=20, center_lon=0,
    )
    _render_folium(m)

    st.markdown("##### Top 20 Islands by Area")
    fig = _make_chart_area_bar(df.reset_index(), "name", "area_km2",
                               "World's Largest Islands (km2)", ACCENT_CYAN, 20)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("##### Island Data Table")
    display_df = df[["name", "country", "area_km2", "population", "note"]].copy()
    display_df.columns = ["Island", "Country", "Area (km2)", "Population", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "largest_islands.csv")


def _render_volcanic_islands():
    """Mode 2: Volcanic Islands."""
    st.markdown("""
    **Volcanic islands** are born from the fiery depths of the Earth. From Hawaii's shield volcanoes
    rising over the Pacific hotspot to Iceland straddling the Mid-Atlantic Ridge, these islands
    represent the raw power of plate tectonics. Some erupt continuously (Stromboli, Kilauea),
    while others slumber between catastrophic events (Santorini, Krakatoa).
    """)

    df = pd.DataFrame(VOLCANIC_ISLANDS)

    active_count = len(df[df["status"] == "Active"])
    dormant_count = len(df[df["status"] == "Dormant"])
    max_elev = df["elevation_m"].max()
    max_elev_name = df.loc[df["elevation_m"].idxmax(), "name"]

    _stat_row({
        "Volcanic Islands": len(df),
        "Currently Active": active_count,
        "Dormant": dormant_count,
        "Highest": f"{max_elev_name} ({max_elev:,}m)",
    })

    def _color_func(item):
        status = item.get("status", "")
        if status == "Active":
            return ACCENT_RED, 8
        return ACCENT_AMBER, 6

    m = _build_folium_map(
        VOLCANIC_ISLANDS,
        popup_fields=[("Country", "country"), ("Volcano", "volcano"),
                      ("Status", "status"), ("Last Eruption", "last_eruption"),
                      ("Elevation", "elevation_m"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=15, center_lon=0,
    )
    _render_folium(m)

    st.markdown("##### Volcano Elevations")
    fig = _make_chart_area_bar(df.sort_values("elevation_m", ascending=False).reset_index(drop=True),
                               "name", "elevation_m",
                               "Volcanic Island Elevations (meters)", ACCENT_RED, 20)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("##### Volcanic Island Data")
    display_df = df[["name", "country", "volcano", "status", "last_eruption", "elevation_m", "note"]].copy()
    display_df.columns = ["Island", "Country", "Volcano", "Status", "Last Eruption", "Elevation (m)", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "volcanic_islands.csv")


def _render_coral_atolls():
    """Mode 3: Coral Atolls."""
    st.markdown("""
    **Coral atolls** are ring-shaped reef formations that encircle a lagoon. Charles Darwin first
    explained their formation: a volcanic island sinks while its fringing reef grows upward,
    eventually leaving only the coral ring. Most atolls rise barely 2-3 meters above sea level,
    making them the most vulnerable landforms to sea level rise. The Maldives, Marshall Islands,
    and Tuamotu Archipelago contain the world's most spectacular atolls.
    """)

    df = pd.DataFrame(CORAL_ATOLLS)

    avg_elev = df["max_elev_m"].mean()
    total_islands = df["islands"].sum()

    _stat_row({
        "Atolls Listed": len(df),
        "Total Islets": f"{total_islands:,}",
        "Avg Max Elevation": f"{avg_elev:.1f} m",
        "Lowest": f"{df.loc[df['max_elev_m'].idxmin(), 'name']} ({df['max_elev_m'].min()}m)",
    })

    def _color_func(item):
        elev = item.get("max_elev_m", 2)
        if elev <= 2.0:
            return ACCENT_RED, 7
        elif elev <= 3.0:
            return ACCENT_AMBER, 6
        return ACCENT_CYAN, 5

    m = _build_folium_map(
        CORAL_ATOLLS,
        popup_fields=[("Country", "country"), ("Type", "type"),
                      ("Area", "area_km2"), ("Max Elevation", "max_elev_m"),
                      ("Islands/Islets", "islands"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=5, center_lon=140,
    )
    _render_folium(m)

    st.markdown("##### Atoll Sizes by Land Area")
    fig = _make_chart_area_bar(df.sort_values("area_km2", ascending=False).reset_index(drop=True),
                               "name", "area_km2",
                               "Coral Atolls by Land Area (km2)", ACCENT_CYAN, 20)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("##### Maximum Elevation of Atolls")
    fig2 = _make_chart_area_bar(df.sort_values("max_elev_m", ascending=True).reset_index(drop=True),
                                "name", "max_elev_m",
                                "Atoll Maximum Elevations (meters) - Lower = More Vulnerable",
                                ACCENT_RED, 20)
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.markdown("##### Atoll Data Table")
    display_df = df[["name", "country", "type", "area_km2", "max_elev_m", "islands", "note"]].copy()
    display_df.columns = ["Atoll", "Country", "Type", "Area (km2)", "Max Elev (m)", "Islets", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "coral_atolls.csv")


def _render_island_nations():
    """Mode 4: Island Nations."""
    st.markdown("""
    **Island nations** are sovereign states composed entirely (or almost entirely) of islands.
    From Indonesia's 17,500+ islands to tiny Nauru (21 km2), these nations face unique challenges:
    isolation, limited resources, vulnerability to sea level rise, and reliance on maritime economies.
    Yet they also possess extraordinary cultural diversity, marine resources, and strategic importance.
    Together, island nations control vast Exclusive Economic Zones spanning millions of square kilometers.
    """)

    df = pd.DataFrame(ISLAND_NATIONS)
    df = df.sort_values("population", ascending=False).reset_index(drop=True)

    total_pop = df["population"].sum()
    total_area = df["area_km2"].sum()
    total_islands = df["islands_count"].sum()
    avg_gdp = df["gdp_per_capita"].mean()

    _stat_row({
        "Island Nations": len(df),
        "Total Population": f"{total_pop / 1e6:,.0f}M",
        "Total Islands": f"{total_islands:,}",
        "Avg GDP/Capita": f"${avg_gdp:,.0f}",
    })

    def _color_func(item):
        pop = item.get("population", 0)
        if pop > 100000000:
            return ACCENT_RED, 10
        elif pop > 10000000:
            return ACCENT_ORANGE, 8
        elif pop > 1000000:
            return ACCENT_AMBER, 6
        elif pop > 100000:
            return ACCENT_CYAN, 5
        return ACCENT_EMERALD, 4

    m = _build_folium_map(
        ISLAND_NATIONS,
        popup_fields=[("Capital", "capital"), ("Population", "population"),
                      ("Area", "area_km2"), ("Islands", "islands_count"),
                      ("GDP/Capita", "gdp_per_capita"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=10, center_lon=100,
    )
    _render_folium(m)

    st.markdown("##### Population vs GDP per Capita")
    fig = _make_chart_scatter(df, "population", "gdp_per_capita", "name",
                              "Island Nations: Population vs GDP per Capita",
                              "Population", "GDP per Capita (USD)",
                              color=ACCENT_CYAN, log_x=True, log_y=True)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("##### Top Island Nations by Number of Islands")
    fig2 = _make_chart_area_bar(
        df.sort_values("islands_count", ascending=False).head(15).reset_index(drop=True),
        "name", "islands_count",
        "Island Nations by Number of Islands", ACCENT_VIOLET, 15)
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.markdown("##### Island Nations Data")
    display_df = df[["name", "capital", "population", "area_km2", "islands_count",
                      "gdp_per_capita", "note"]].copy()
    display_df.columns = ["Nation", "Capital", "Population", "Area (km2)",
                           "Islands", "GDP/Capita ($)", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "island_nations.csv")


def _render_uninhabited_islands():
    """Mode 5: Uninhabited Islands."""
    st.markdown("""
    **Uninhabited islands** remain empty for reasons ranging from extreme climate and remoteness
    to deliberate protection. Devon Island (Canada) is the largest uninhabited island at 55,247 km2,
    while Bouvet Island (Norway) holds the record for most remote. Some, like Henderson Island,
    are UNESCO World Heritage sites; others, like Heard Island, host active volcanoes. These
    pristine places serve as baselines for understanding human impact on the planet.
    """)

    df = pd.DataFrame(UNINHABITED_ISLANDS)

    total_area = df["area_km2"].sum()
    largest = df.loc[df["area_km2"].idxmax()]

    _stat_row({
        "Islands Listed": len(df),
        "Total Area": f"{total_area:,.0f} km2",
        "Largest": f"{largest['name']} ({largest['area_km2']:,} km2)",
        "Most Remote": "Bouvet Island",
    })

    def _color_func(item):
        area = item.get("area_km2", 0)
        if area > 1000:
            return ACCENT_VIOLET, 9
        elif area > 100:
            return ACCENT_BLUE, 7
        elif area > 10:
            return ACCENT_CYAN, 5
        return ACCENT_EMERALD, 4

    m = _build_folium_map(
        UNINHABITED_ISLANDS,
        popup_fields=[("Country", "country"), ("Area", "area_km2"),
                      ("Reason Uninhabited", "reason"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=20, center_lon=0,
    )
    _render_folium(m)

    st.markdown("##### Uninhabited Islands by Area")
    fig = _make_chart_area_bar(
        df.sort_values("area_km2", ascending=False).reset_index(drop=True),
        "name", "area_km2",
        "Uninhabited Islands by Area (km2)", ACCENT_VIOLET, 20)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Reasons pie chart
    reason_counts = df["reason"].value_counts()
    fig2 = _make_pie_chart(reason_counts.index.tolist(), reason_counts.values.tolist(),
                           "Why Are These Islands Uninhabited?")
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.markdown("##### Uninhabited Island Data")
    display_df = df[["name", "country", "area_km2", "reason", "note"]].copy()
    display_df.columns = ["Island", "Country", "Area (km2)", "Reason", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "uninhabited_islands.csv")


def _render_biodiversity():
    """Mode 6: Island Biodiversity Hotspots."""
    st.markdown("""
    **Island biodiversity hotspots** harbor an extraordinary concentration of endemic species --
    organisms found nowhere else on Earth. Islands act as natural laboratories of evolution:
    geographic isolation drives speciation, producing unique life forms. Madagascar's lemurs,
    the Galapagos giant tortoises, and Socotra's dragon blood trees evolved in isolation over
    millions of years. Tragically, island species are also the most vulnerable to extinction,
    accounting for 75% of all known bird and mammal extinctions.
    """)

    df = pd.DataFrame(BIODIVERSITY_ISLANDS)

    avg_endemic = df["endemic_pct"].mean()
    highest_endemic = df.loc[df["endemic_pct"].idxmax()]

    _stat_row({
        "Hotspots Listed": len(df),
        "Avg Endemism": f"{avg_endemic:.0f}%",
        "Highest Endemism": f"{highest_endemic['name']} ({highest_endemic['endemic_pct']}%)",
        "Most Threatened": "Madagascar",
    })

    def _color_func(item):
        pct = item.get("endemic_pct", 0)
        if pct >= 80:
            return ACCENT_RED, 10
        elif pct >= 60:
            return ACCENT_ORANGE, 8
        elif pct >= 40:
            return ACCENT_AMBER, 6
        return ACCENT_EMERALD, 5

    m = _build_folium_map(
        BIODIVERSITY_ISLANDS,
        popup_fields=[("Country", "country"), ("Endemism", "endemic_pct"),
                      ("Key Species", "key_species"), ("Threats", "threats"),
                      ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=0, center_lon=80,
    )
    _render_folium(m)

    st.markdown("##### Endemism Rates by Island")
    fig = _make_chart_area_bar(
        df.sort_values("endemic_pct", ascending=False).reset_index(drop=True),
        "name", "endemic_pct",
        "Island Endemism Rates (% species found only here)", ACCENT_EMERALD, 18)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Threats breakdown
    all_threats = []
    for t in df["threats"]:
        for part in t.split(","):
            all_threats.append(part.strip())
    threat_counts = pd.Series(all_threats).value_counts().head(8)
    fig2 = _make_pie_chart(threat_counts.index.tolist(), threat_counts.values.tolist(),
                           "Primary Threats to Island Biodiversity")
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.markdown("##### Biodiversity Hotspot Data")
    display_df = df[["name", "country", "endemic_pct", "key_species", "threats", "note"]].copy()
    display_df.columns = ["Island", "Country", "Endemism (%)", "Key Species", "Threats", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "island_biodiversity.csv")


def _render_artificial_islands():
    """Mode 7: Artificial Islands."""
    st.markdown("""
    **Artificial islands** are human-made landmasses created by dredging, land reclamation, or
    construction. From the Netherlands' Flevopolder (970 km2, the largest ever) to Dubai's
    iconic Palm Jumeirah, these engineering marvels serve purposes from agriculture to airports,
    military bases to luxury resorts. Japan has built multiple airport islands to save land,
    while China has controversially created military installations in the South China Sea.
    The Maldives' Hulhumale was built specifically to resist rising sea levels.
    """)

    df = pd.DataFrame(ARTIFICIAL_ISLANDS)

    _stat_row({
        "Islands Listed": len(df),
        "Largest": "Flevopolder (970 km2)",
        "Most Expensive": "Yas Island ($40B)",
        "Oldest": "Odaiba (1853)",
    })

    def _color_func(item):
        purpose = item.get("purpose", "").lower()
        if "airport" in purpose:
            return ACCENT_BLUE, 8
        elif "military" in purpose:
            return ACCENT_RED, 8
        elif "luxury" in purpose or "tourism" in purpose or "entertainment" in purpose:
            return ACCENT_AMBER, 7
        elif "agriculture" in purpose or "nature" in purpose:
            return ACCENT_EMERALD, 7
        return ACCENT_CYAN, 6

    m = _build_folium_map(
        ARTIFICIAL_ISLANDS,
        popup_fields=[("Country", "country"), ("Area", "area_km2"),
                      ("Year Built", "year_built"), ("Cost", "cost_usd"),
                      ("Purpose", "purpose"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=25, center_lon=55,
    )
    _render_folium(m)

    st.markdown("##### Artificial Islands by Area")
    fig = _make_chart_area_bar(
        df.sort_values("area_km2", ascending=False).reset_index(drop=True),
        "name", "area_km2",
        "Artificial Islands by Area (km2)", ACCENT_AMBER, 18)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Purpose pie chart
    purpose_counts = df["purpose"].value_counts()
    fig2 = _make_pie_chart(purpose_counts.index.tolist(), purpose_counts.values.tolist(),
                           "Artificial Island Purposes")
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.markdown("##### Artificial Island Data")
    display_df = df[["name", "country", "area_km2", "year_built", "cost_usd", "purpose", "note"]].copy()
    display_df.columns = ["Island", "Country", "Area (km2)", "Year Built", "Cost (USD)", "Purpose", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "artificial_islands.csv")


def _render_prison_islands():
    """Mode 8: Prison Islands."""
    st.markdown("""
    **Prison islands** have been used throughout history to isolate, punish, and contain.
    The natural barrier of water made escape nearly impossible. From Alcatraz in San Francisco Bay
    to Robben Island where Nelson Mandela spent 18 years, these islands carry profound histories
    of injustice, resistance, and transformation. Many former prison islands have been converted
    into museums, national parks, or UNESCO World Heritage Sites, preserving their stories
    as reminders of humanity's capacity for both cruelty and redemption.
    """)

    df = pd.DataFrame(PRISON_ISLANDS)

    active_count = len(df[df["status"].str.contains("Active", case=False)])
    museum_count = len(df[df["status"].str.contains("Museum|UNESCO|Park|Monument|Tourist|attraction",
                                                      case=False, regex=True)])

    _stat_row({
        "Prison Islands": len(df),
        "Still Active": active_count,
        "Now Museums/Parks": museum_count,
        "Most Famous": "Alcatraz",
    })

    def _color_func(item):
        status = item.get("status", "").lower()
        if "active" in status:
            return ACCENT_RED, 8
        elif "museum" in status or "unesco" in status:
            return ACCENT_CYAN, 7
        elif "park" in status:
            return ACCENT_EMERALD, 7
        return ACCENT_AMBER, 6

    m = _build_folium_map(
        PRISON_ISLANDS,
        popup_fields=[("Country", "country"), ("Years Active", "years_active"),
                      ("Famous Inmates", "famous_inmates"),
                      ("Current Status", "status"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=25, center_lon=0,
    )
    _render_folium(m)

    st.markdown("##### Current Status of Prison Islands")
    status_cats = {"Active Prison": 0, "Museum/Memorial": 0, "Park/Reserve": 0,
                   "Tourist Site": 0, "Other": 0}
    for _, row in df.iterrows():
        s = row["status"].lower()
        if "active" in s and "prison" in s or "active" in s and "jail" in s or "active" in s and "security" in s:
            status_cats["Active Prison"] += 1
        elif "museum" in s or "memorial" in s or "unesco" in s or "monument" in s:
            status_cats["Museum/Memorial"] += 1
        elif "park" in s or "reserve" in s:
            status_cats["Park/Reserve"] += 1
        elif "tourist" in s or "visitor" in s or "open" in s or "attraction" in s:
            status_cats["Tourist Site"] += 1
        else:
            status_cats["Other"] += 1

    labels = [k for k, v in status_cats.items() if v > 0]
    values = [v for v in status_cats.values() if v > 0]
    fig = _make_pie_chart(labels, values, "Current Status of Historic Prison Islands")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("##### Prison Island Data")
    display_df = df[["name", "country", "years_active", "famous_inmates", "status", "note"]].copy()
    display_df.columns = ["Island", "Country", "Years Active", "Famous Inmates", "Status", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "prison_islands.csv")


def _render_disappearing_islands():
    """Mode 9: Disappearing Islands."""
    st.markdown("""
    **Disappearing islands** face an existential threat from sea level rise, erosion, and
    subsidence. With global sea levels projected to rise 0.3-1.0 meters by 2100, low-lying
    island nations like Tuvalu, Kiribati, and the Maldives face partial or complete submersion.
    Some islands have already vanished: Lohachara (India) was the first inhabited island lost
    to rising seas. The human cost is staggering -- millions of climate refugees may need
    relocation within decades, losing not just homes but entire cultures and nations.
    """)

    df = pd.DataFrame(DISAPPEARING_ISLANDS)

    already_gone = len(df[df["max_elev_m"] == 0])
    below_2m = len(df[df["max_elev_m"] <= 2.0])
    total_affected = df["population"].sum()

    _stat_row({
        "Threatened Islands": len(df),
        "Already Submerged": already_gone,
        "Below 2m Elevation": below_2m,
        "People at Risk": f"{total_affected:,.0f}",
    })

    def _color_func(item):
        elev = item.get("max_elev_m", 0)
        if elev == 0:
            return "#1a1a2e", 6  # Already gone
        elif elev <= 1.5:
            return ACCENT_RED, 9
        elif elev <= 3.0:
            return ACCENT_ORANGE, 7
        return ACCENT_AMBER, 6

    m = _build_folium_map(
        DISAPPEARING_ISLANDS,
        popup_fields=[("Country", "country"), ("Max Elevation", "max_elev_m"),
                      ("Population", "population"), ("Threat", "threat"),
                      ("Timeline", "timeline"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=5, center_lon=130,
    )
    _render_folium(m)

    st.markdown("##### Maximum Elevations - The Most Vulnerable")
    elev_df = df[df["max_elev_m"] > 0].sort_values("max_elev_m", ascending=False).reset_index(drop=True)
    fig = _make_chart_area_bar(elev_df, "name", "max_elev_m",
                               "Maximum Elevation (meters) - Lower = More Critical",
                               ACCENT_RED, len(elev_df))
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("##### Populations at Risk")
    pop_df = df[df["population"] > 0].sort_values("population", ascending=False).head(15).reset_index(drop=True)
    fig2 = _make_chart_area_bar(pop_df, "name", "population",
                                "Populations at Risk from Island Disappearance",
                                ACCENT_ORANGE, 15)
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    st.markdown("##### Disappearing Island Data")
    display_df = df[["name", "country", "max_elev_m", "population", "threat", "timeline", "note"]].copy()
    display_df.columns = ["Island", "Country", "Max Elev (m)", "Population",
                           "Threat", "Timeline", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "disappearing_islands.csv")


def _render_island_mysteries():
    """Mode 10: Island Mysteries."""
    st.markdown("""
    **Island mysteries** have captivated human imagination for centuries. Easter Island's massive
    Moai statues, North Sentinel Island's fiercely isolated tribe, the underwater Yonaguni
    Monument in Japan, phantom islands that appeared on maps for centuries but never existed --
    islands are theaters of the unexplained. From archaeological enigmas and sunken cities to
    dangerous forbidden zones and cryptic disappearances, these islands challenge our
    understanding of history, nature, and human civilization.
    """)

    df = pd.DataFrame(ISLAND_MYSTERIES)

    category_counts = df["category"].value_counts()
    top_category = category_counts.index[0]

    _stat_row({
        "Mysteries Listed": len(df),
        "Top Category": top_category,
        "Archaeological": len(df[df["category"].str.contains("Archaeo", case=False)]),
        "Maritime": len(df[df["category"].str.contains("Maritime|danger", case=False, regex=True)]),
    })

    category_colors = {
        "Archaeological": ACCENT_AMBER,
        "Anthropological": ACCENT_VIOLET,
        "Urban exploration": MUTED_COLOR,
        "Natural wonder": ACCENT_EMERALD,
        "Treasure hunt": ACCENT_AMBER,
        "Maritime mystery": ACCENT_BLUE,
        "Paranormal/Historical": ACCENT_PINK,
        "Maritime danger": ACCENT_RED,
        "Cartographic mystery": ACCENT_CYAN,
        "Natural danger": ACCENT_RED,
        "Archaeological/Geological": ACCENT_ORANGE,
        "Geological": ACCENT_ORANGE,
    }

    def _color_func(item):
        cat = item.get("category", "")
        color = category_colors.get(cat, ACCENT_CYAN)
        return color, 8

    m = _build_folium_map(
        ISLAND_MYSTERIES,
        popup_fields=[("Country", "country"), ("Mystery", "mystery"),
                      ("Category", "category"), ("Info", "note")],
        use_color_func=_color_func,
        zoom=2, center_lat=15, center_lon=30,
    )
    _render_folium(m)

    # Category breakdown
    fig = _make_pie_chart(category_counts.index.tolist(), category_counts.values.tolist(),
                          "Island Mysteries by Category")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("##### Mystery Details")
    for _, row in df.iterrows():
        cat_color = category_colors.get(row["category"], ACCENT_CYAN)
        st.markdown(
            f'<div style="border-left: 3px solid {cat_color}; padding: 8px 12px; '
            f'margin-bottom: 8px; background: rgba(17,24,39,0.5); border-radius: 4px;">'
            f'<b style="color:{TEXT_COLOR}">{escape(row["name"])}</b> '
            f'<span style="color:{SECONDARY_COLOR}">({escape(row["country"])})</span><br>'
            f'<span style="color:{cat_color}; font-size:0.85em;">{escape(row["category"])}: '
            f'{escape(row["mystery"])}</span><br>'
            f'<span style="color:{SECONDARY_COLOR}; font-size:0.85em;">{escape(row["note"])}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("##### Mystery Island Data")
    display_df = df[["name", "country", "mystery", "category", "note"]].copy()
    display_df.columns = ["Island", "Country", "Mystery", "Category", "Notes"]
    st.dataframe(display_df, width="stretch")

    _csv_download(display_df, "island_mysteries.csv")


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_island_maps_tab():
    """Main entry point for the Islands & Archipelagos tab."""

    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>\U0001f3dd\ufe0f Islands & Archipelagos of the World</h4>'
        '<p>Islands, atolls, archipelagos, island nations & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        index=0,
        help="Choose from 10 island exploration modes",
    )

    st.markdown("---")

    # Dispatch to the selected mode
    mode_index = MAP_MODES.index(mode)

    if mode_index == 0:
        _render_largest_islands()
    elif mode_index == 1:
        _render_volcanic_islands()
    elif mode_index == 2:
        _render_coral_atolls()
    elif mode_index == 3:
        _render_island_nations()
    elif mode_index == 4:
        _render_uninhabited_islands()
    elif mode_index == 5:
        _render_biodiversity()
    elif mode_index == 6:
        _render_artificial_islands()
    elif mode_index == 7:
        _render_prison_islands()
    elif mode_index == 8:
        _render_disappearing_islands()
    elif mode_index == 9:
        _render_island_mysteries()
