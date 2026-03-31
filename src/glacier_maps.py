# -*- coding: utf-8 -*-
"""
Glaciers & Polar Regions module for TerraScout AI.
Curated catalog of the world's glaciers, ice sheets, icebergs, permafrost,
polar expeditions, ice-core drilling sites, glacial lakes, and polar wildlife
— presented across 10 interactive map modes.
All data is curated/static. No API keys required.
"""

import io
import streamlit as st
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
import numpy as np

# ═══════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
SECONDARY_TEXT = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_PINK = "#ec4899"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"
ACCENT_TEAL = "#14b8a6"
ACCENT_ICE = "#7dd3fc"
ACCENT_SNOW = "#bae6fd"
ACCENT_FROST = "#67e8f9"

MAP_TILES = "CartoDB dark_matter"

# ═══════════════════════════════════════════════════════════════
# MODE 1: WORLD'S MAJOR GLACIERS
# ═══════════════════════════════════════════════════════════════
MAJOR_GLACIERS = [
    {"name": "Lambert-Fisher Glacier", "lat": -71.0, "lon": 69.5, "area_km2": 90000,
     "length_km": 400, "region": "Antarctica", "type": "Outlet",
     "description": "Largest glacier on Earth by area, draining ~8% of the Antarctic ice sheet into the Amery Ice Shelf.",
     "status": "Monitored", "color": ACCENT_CYAN},
    {"name": "Fedchenko Glacier", "lat": 38.83, "lon": 72.2, "area_km2": 700,
     "length_km": 77, "region": "Central Asia", "type": "Valley",
     "description": "Longest glacier outside polar regions, located in the Pamir Mountains of Tajikistan.",
     "status": "Retreating", "color": ACCENT_ICE},
    {"name": "Siachen Glacier", "lat": 35.42, "lon": 77.11, "area_km2": 700,
     "length_km": 76, "region": "Karakoram", "type": "Valley",
     "description": "Second-longest non-polar glacier, site of the world's highest battlefield between India and Pakistan.",
     "status": "Retreating", "color": ACCENT_SNOW},
    {"name": "Biafo Glacier", "lat": 35.88, "lon": 75.75, "area_km2": 620,
     "length_km": 67, "region": "Karakoram", "type": "Valley",
     "description": "Connected to Hispar Glacier forming the longest glacial system outside polar regions (120 km).",
     "status": "Stable", "color": ACCENT_ICE},
    {"name": "Hubbard Glacier", "lat": 60.02, "lon": -139.5, "area_km2": 3400,
     "length_km": 122, "region": "Alaska", "type": "Tidewater",
     "description": "Largest tidewater glacier in North America, one of the few advancing glaciers in Alaska.",
     "status": "Advancing", "color": ACCENT_EMERALD},
    {"name": "Petermann Glacier", "lat": 80.75, "lon": -60.68, "area_km2": 1300,
     "length_km": 80, "region": "Greenland", "type": "Outlet",
     "description": "One of Greenland's largest outlet glaciers, connecting the ice sheet to the Arctic Ocean.",
     "status": "Retreating", "color": ACCENT_BLUE},
    {"name": "Jakobshavn Isbrae", "lat": 69.17, "lon": -49.83, "area_km2": 1100,
     "length_km": 65, "region": "Greenland", "type": "Outlet",
     "description": "Fastest-moving glacier in Greenland, draining ~6.5% of the Greenland ice sheet. Produced the iceberg that sank the Titanic.",
     "status": "Retreating", "color": ACCENT_RED},
    {"name": "Aletsch Glacier", "lat": 46.45, "lon": 8.03, "area_km2": 81.7,
     "length_km": 23, "region": "Alps", "type": "Valley",
     "description": "Largest glacier in the Alps, a UNESCO World Heritage Site in the Bernese Alps, Switzerland.",
     "status": "Retreating", "color": ACCENT_FROST},
    {"name": "Perito Moreno Glacier", "lat": -50.5, "lon": -73.05, "area_km2": 250,
     "length_km": 30, "region": "Patagonia", "type": "Tidewater",
     "description": "One of few stable glaciers in the world; famous for dramatic calving events into Lago Argentino.",
     "status": "Stable", "color": ACCENT_CYAN},
    {"name": "Vatnajokull", "lat": 64.42, "lon": -16.8, "area_km2": 7900,
     "length_km": 150, "region": "Iceland", "type": "Ice cap",
     "description": "Largest ice cap in Europe by volume, covering active volcanoes including Grimsvotn and Bardarbunga.",
     "status": "Retreating", "color": ACCENT_ICE},
    {"name": "Fox Glacier", "lat": -43.57, "lon": 170.13, "area_km2": 32,
     "length_km": 13, "region": "New Zealand", "type": "Valley",
     "description": "Temperate maritime glacier on the west coast of New Zealand's South Island, descending to 300m ASL.",
     "status": "Retreating", "color": ACCENT_SNOW},
    {"name": "Franz Josef Glacier", "lat": -43.47, "lon": 170.16, "area_km2": 35,
     "length_km": 12, "region": "New Zealand", "type": "Valley",
     "description": "Steepest glacier in New Zealand, terminating near temperate rainforest.",
     "status": "Retreating", "color": ACCENT_FROST},
    {"name": "Gangotri Glacier", "lat": 30.92, "lon": 79.08, "area_km2": 143,
     "length_km": 30.2, "region": "Himalayas", "type": "Valley",
     "description": "Source of the Ganges River, one of the largest glaciers in the Himalayas. Sacred in Hindu tradition.",
     "status": "Retreating", "color": ACCENT_AMBER},
    {"name": "Baltoro Glacier", "lat": 35.73, "lon": 76.52, "area_km2": 524,
     "length_km": 62, "region": "Karakoram", "type": "Valley",
     "description": "Gateway glacier to K2, providing the approach route to the world's second-highest peak.",
     "status": "Stable", "color": ACCENT_ICE},
    {"name": "Jostedalsbreen", "lat": 61.67, "lon": 6.85, "area_km2": 474,
     "length_km": 37, "region": "Norway", "type": "Ice cap",
     "description": "Largest glacier in continental Europe, located in western Norway with multiple outlet glaciers.",
     "status": "Retreating", "color": ACCENT_BLUE},
    {"name": "Glacier de la Meije", "lat": 44.97, "lon": 6.15, "area_km2": 8.5,
     "length_km": 5, "region": "Alps", "type": "Cirque",
     "description": "Iconic Alpine glacier on the north face of La Meije in the French Dauphine Alps.",
     "status": "Retreating", "color": ACCENT_FROST},
    {"name": "Columbia Glacier", "lat": 61.15, "lon": -147.08, "area_km2": 1010,
     "length_km": 51, "region": "Alaska", "type": "Tidewater",
     "description": "Once the largest tidewater glacier in Alaska; has retreated over 20 km since 1980.",
     "status": "Retreating rapidly", "color": ACCENT_RED},
    {"name": "Pine Island Glacier", "lat": -75.17, "lon": -100.0, "area_km2": 6250,
     "length_km": 250, "region": "Antarctica", "type": "Ice stream",
     "description": "One of Antarctica's fastest-retreating glaciers, contributing significantly to sea-level rise.",
     "status": "Retreating rapidly", "color": ACCENT_RED},
    {"name": "Thwaites Glacier", "lat": -75.5, "lon": -106.75, "area_km2": 5400,
     "length_km": 120, "region": "Antarctica", "type": "Ice stream",
     "description": "The 'Doomsday Glacier' — its collapse could raise global sea levels by over 60 cm.",
     "status": "Retreating rapidly", "color": ACCENT_RED},
    {"name": "Khumbu Glacier", "lat": 27.95, "lon": 86.83, "area_km2": 12,
     "length_km": 17, "region": "Himalayas", "type": "Valley",
     "description": "Glacier flowing from Everest Base Camp, the highest glacier in the world with the notorious Khumbu Icefall.",
     "status": "Retreating", "color": ACCENT_AMBER},
    {"name": "Gorner Glacier", "lat": 45.97, "lon": 7.8, "area_km2": 57,
     "length_km": 14, "region": "Alps", "type": "Valley",
     "description": "Second largest glacier in the Alps, at the foot of Monte Rosa and Matterhorn.",
     "status": "Retreating", "color": ACCENT_ICE},
    {"name": "Quelccaya Ice Cap", "lat": -13.93, "lon": -70.83, "area_km2": 44,
     "length_km": 8, "region": "Andes", "type": "Ice cap",
     "description": "Largest tropical ice cap on Earth, in the Peruvian Andes. Vital climate record spanning 1,800 years.",
     "status": "Retreating rapidly", "color": ACCENT_RED},
    {"name": "Malaspina Glacier", "lat": 60.0, "lon": -140.5, "area_km2": 3900,
     "length_km": 45, "region": "Alaska", "type": "Piedmont",
     "description": "Largest piedmont glacier in the world, visible from space as a huge lobe spreading onto the coastal plain.",
     "status": "Retreating", "color": ACCENT_BLUE},
    {"name": "Mer de Glace", "lat": 45.9, "lon": 6.93, "area_km2": 30,
     "length_km": 12, "region": "Alps", "type": "Valley",
     "description": "Largest glacier in France on Mont Blanc massif, losing 30m of thickness per century.",
     "status": "Retreating", "color": ACCENT_FROST},
    {"name": "Taku Glacier", "lat": 58.55, "lon": -134.1, "area_km2": 725,
     "length_km": 58, "region": "Alaska", "type": "Valley",
     "description": "Deepest and thickest known glacier in the world at 1,477m, one of few advancing glaciers.",
     "status": "Advancing", "color": ACCENT_EMERALD},
]

# ═══════════════════════════════════════════════════════════════
# MODE 2: ANTARCTIC ICE SHEET
# ═══════════════════════════════════════════════════════════════
ANTARCTIC_STATIONS = [
    {"name": "McMurdo Station", "lat": -77.85, "lon": 166.67, "country": "USA",
     "established": 1956, "population_summer": 1200, "type": "Research Station",
     "description": "Largest Antarctic station, logistics hub for US Antarctic Program on Ross Island.",
     "color": ACCENT_BLUE},
    {"name": "Amundsen-Scott South Pole", "lat": -90.0, "lon": 0.0, "country": "USA",
     "established": 1957, "population_summer": 150, "type": "Research Station",
     "description": "Located at the geographic South Pole; rebuilt in 2008 on elevated stilts above the moving ice.",
     "color": ACCENT_RED},
    {"name": "Vostok Station", "lat": -78.46, "lon": 106.84, "country": "Russia",
     "established": 1957, "population_summer": 25, "type": "Research Station",
     "description": "Site of the coldest temperature ever recorded (-89.2C). Above subglacial Lake Vostok.",
     "color": ACCENT_CYAN},
    {"name": "Concordia Station", "lat": -75.1, "lon": 123.33, "country": "France/Italy",
     "established": 2005, "population_summer": 60, "type": "Research Station",
     "description": "Year-round station at Dome C, site of the EPICA ice core — 800,000 years of climate data.",
     "color": ACCENT_VIOLET},
    {"name": "Casey Station", "lat": -66.28, "lon": 110.53, "country": "Australia",
     "established": 1969, "population_summer": 200, "type": "Research Station",
     "description": "Australian station in Wilkes Land, surrounded by the Windmill Islands.",
     "color": ACCENT_EMERALD},
    {"name": "Mawson Station", "lat": -67.6, "lon": 62.87, "country": "Australia",
     "established": 1954, "population_summer": 60, "type": "Research Station",
     "description": "Oldest continuously operating station south of the Antarctic Circle.",
     "color": ACCENT_EMERALD},
    {"name": "Davis Station", "lat": -68.58, "lon": 77.97, "country": "Australia",
     "established": 1957, "population_summer": 120, "type": "Research Station",
     "description": "Located in the ice-free Vestfold Hills, one of the warmest areas on the Antarctic coast.",
     "color": ACCENT_EMERALD},
    {"name": "Halley VI Station", "lat": -75.58, "lon": -26.57, "country": "UK",
     "established": 2012, "population_summer": 70, "type": "Research Station",
     "description": "Modular station on hydraulic legs on the Brunt Ice Shelf; where the ozone hole was discovered.",
     "color": ACCENT_AMBER},
    {"name": "Rothera Station", "lat": -67.57, "lon": -68.13, "country": "UK",
     "established": 1975, "population_summer": 130, "type": "Research Station",
     "description": "Main British Antarctic station on Adelaide Island, hub for biological and climate research.",
     "color": ACCENT_AMBER},
    {"name": "Scott Base", "lat": -77.85, "lon": 166.76, "country": "New Zealand",
     "established": 1957, "population_summer": 85, "type": "Research Station",
     "description": "New Zealand's Antarctic station on Ross Island, near McMurdo.",
     "color": ACCENT_TEAL},
    {"name": "Neumayer III", "lat": -70.65, "lon": -8.27, "country": "Germany",
     "established": 2009, "population_summer": 50, "type": "Research Station",
     "description": "Elevated on hydraulic pillars on the Ekstrom Ice Shelf, atmospheric observation focus.",
     "color": ACCENT_ORANGE},
    {"name": "Syowa Station", "lat": -69.0, "lon": 39.58, "country": "Japan",
     "established": 1957, "population_summer": 110, "type": "Research Station",
     "description": "Japanese research station on East Ongul Island, Lutzow-Holm Bay.",
     "color": ACCENT_PINK},
    {"name": "Princess Elisabeth", "lat": -71.95, "lon": 23.35, "country": "Belgium",
     "established": 2009, "population_summer": 40, "type": "Research Station",
     "description": "First zero-emission Antarctic station, powered entirely by wind and solar energy.",
     "color": ACCENT_VIOLET},
    {"name": "Dome Fuji", "lat": -77.32, "lon": 39.7, "country": "Japan",
     "established": 1995, "population_summer": 10, "type": "Ice Core Site",
     "description": "Second-coldest place on Earth. Drilled a 3,035m ice core spanning 720,000 years.",
     "color": ACCENT_ICE},
    {"name": "Kunlun Station", "lat": -80.42, "lon": 77.12, "country": "China",
     "established": 2009, "population_summer": 28, "type": "Research Station",
     "description": "Highest station in Antarctica at 4,087m on Dome A, the ice sheet summit.",
     "color": ACCENT_RED},
]

ANTARCTIC_FEATURES = [
    {"name": "Ross Ice Shelf", "lat": -81.5, "lon": 175.0, "type": "Ice Shelf",
     "area_km2": 487000, "description": "Largest ice shelf in Antarctica, the size of France.",
     "color": ACCENT_ICE},
    {"name": "Ronne-Filchner Ice Shelf", "lat": -79.0, "lon": -45.0, "type": "Ice Shelf",
     "area_km2": 422000, "description": "Second-largest ice shelf, in the Weddell Sea sector.",
     "color": ACCENT_SNOW},
    {"name": "Antarctic Peninsula", "lat": -65.0, "lon": -64.0, "type": "Peninsula",
     "area_km2": 520000, "description": "Most rapidly warming part of Antarctica, losing ice shelves at alarming rate.",
     "color": ACCENT_RED},
    {"name": "Lake Vostok", "lat": -77.5, "lon": 106.0, "type": "Subglacial Lake",
     "area_km2": 15690, "description": "Largest known subglacial lake, buried under 3.7 km of ice for 15 million years.",
     "color": ACCENT_BLUE},
    {"name": "Dry Valleys", "lat": -77.5, "lon": 162.0, "type": "Ice-free",
     "area_km2": 4800, "description": "Largest ice-free area in Antarctica, Mars analog research site.",
     "color": ACCENT_AMBER},
    {"name": "Transantarctic Mountains", "lat": -85.0, "lon": 175.0, "type": "Mountain Range",
     "area_km2": 0, "description": "3,500 km mountain range dividing East and West Antarctica.",
     "color": ACCENT_ORANGE},
    {"name": "Mount Erebus", "lat": -77.53, "lon": 167.15, "type": "Volcano",
     "area_km2": 0, "description": "Southernmost active volcano on Earth with a persistent lava lake.",
     "color": ACCENT_RED},
    {"name": "Pine Island Bay", "lat": -74.5, "lon": -102.0, "type": "Bay",
     "area_km2": 0, "description": "Critical area for West Antarctic ice sheet stability; site of rapid ice loss.",
     "color": ACCENT_RED},
]

# ═══════════════════════════════════════════════════════════════
# MODE 3: ARCTIC REGION
# ═══════════════════════════════════════════════════════════════
ARCTIC_SITES = [
    {"name": "North Pole", "lat": 90.0, "lon": 0.0, "type": "Geographic Pole",
     "country": "International", "description": "Geographic North Pole on shifting sea ice; average ice thickness ~2-3m.",
     "color": ACCENT_RED},
    {"name": "Svalbard", "lat": 78.23, "lon": 15.63, "type": "Archipelago",
     "country": "Norway", "description": "Norwegian archipelago; home to the Global Seed Vault and 3,000 polar bears.",
     "color": ACCENT_CYAN},
    {"name": "Barrow (Utqiagvik)", "lat": 71.29, "lon": -156.79, "type": "Arctic Community",
     "country": "USA", "description": "Northernmost city in the USA, 67 days of polar night annually.",
     "color": ACCENT_BLUE},
    {"name": "Resolute Bay", "lat": 74.69, "lon": -94.97, "type": "Arctic Community",
     "country": "Canada", "description": "Second-northernmost settlement in Canada, gateway to Northwest Passage.",
     "color": ACCENT_SNOW},
    {"name": "Iqaluit", "lat": 63.75, "lon": -68.52, "type": "Arctic Capital",
     "country": "Canada", "description": "Capital of Nunavut, Canada's newest territory. Population ~8,000.",
     "color": ACCENT_FROST},
    {"name": "Murmansk", "lat": 68.97, "lon": 33.08, "type": "Arctic City",
     "country": "Russia", "description": "Largest city above the Arctic Circle (~280,000), ice-free port on the Barents Sea.",
     "color": ACCENT_ORANGE},
    {"name": "Norilsk", "lat": 69.35, "lon": 88.2, "type": "Arctic City",
     "country": "Russia", "description": "Most polluted city in Russia, built on permafrost for nickel mining.",
     "color": ACCENT_RED},
    {"name": "Tromso", "lat": 69.65, "lon": 18.96, "type": "Arctic City",
     "country": "Norway", "description": "Gateway to the Arctic, northernmost university city, aurora viewing capital.",
     "color": ACCENT_EMERALD},
    {"name": "Longyearbyen", "lat": 78.22, "lon": 15.64, "type": "Settlement",
     "country": "Norway", "description": "World's northernmost town with over 1,000 residents. More polar bears than people on Svalbard.",
     "color": ACCENT_CYAN},
    {"name": "Ilulissat", "lat": 69.22, "lon": -51.1, "type": "Arctic Town",
     "country": "Greenland", "description": "Gateway to the Ilulissat Icefjord, UNESCO site where icebergs calve from Jakobshavn.",
     "color": ACCENT_ICE},
    {"name": "Alert (CFS Alert)", "lat": 82.5, "lon": -62.35, "type": "Military Station",
     "country": "Canada", "description": "Northernmost permanently inhabited place on Earth, just 817 km from the North Pole.",
     "color": ACCENT_AMBER},
    {"name": "Hammerfest", "lat": 70.66, "lon": 23.68, "type": "Arctic Town",
     "country": "Norway", "description": "One of the northernmost towns in Europe, with a rich history of Arctic whaling.",
     "color": ACCENT_TEAL},
    {"name": "Tiksi", "lat": 71.64, "lon": 128.87, "type": "Arctic Port",
     "country": "Russia", "description": "Key port on the Northern Sea Route along the Laptev Sea.",
     "color": ACCENT_VIOLET},
    {"name": "Pevek", "lat": 69.7, "lon": 170.31, "type": "Arctic Port",
     "country": "Russia", "description": "Northernmost city in Russia, home to the floating nuclear power plant Akademik Lomonosov.",
     "color": ACCENT_RED},
    {"name": "Qaanaaq (Thule)", "lat": 77.48, "lon": -69.36, "type": "Arctic Community",
     "country": "Greenland", "description": "Northernmost naturally inhabited town in Greenland, Inughuit homeland.",
     "color": ACCENT_ICE},
]

ARCTIC_ROUTES = [
    {"name": "Northwest Passage", "type": "Shipping Route",
     "description": "Sea route through the Canadian Arctic Archipelago connecting Atlantic and Pacific.",
     "points": [[74.0, -95.0], [72.0, -105.0], [70.0, -128.0], [68.0, -140.0], [65.0, -168.0]],
     "color": ACCENT_CYAN},
    {"name": "Northern Sea Route", "type": "Shipping Route",
     "description": "Russian Arctic sea route from Murmansk to Vladivostok along the Siberian coast.",
     "points": [[69.0, 33.0], [72.0, 55.0], [74.0, 80.0], [75.0, 110.0], [72.0, 140.0], [68.0, 170.0]],
     "color": ACCENT_ORANGE},
    {"name": "Transpolar Sea Route", "type": "Shipping Route",
     "description": "Direct route across the central Arctic Ocean, increasingly feasible with melting sea ice.",
     "points": [[70.0, 20.0], [80.0, 0.0], [88.0, -40.0], [80.0, -100.0], [65.0, -168.0]],
     "color": ACCENT_RED},
]

# ═══════════════════════════════════════════════════════════════
# MODE 4: RETREATING GLACIERS
# ═══════════════════════════════════════════════════════════════
RETREATING_GLACIERS = [
    {"name": "Jakobshavn Isbrae", "lat": 69.17, "lon": -49.83, "region": "Greenland",
     "retreat_km": 40, "retreat_period": "1850-2023", "rate_m_per_year": 230,
     "description": "Has retreated over 40 km since 1850; speeds exceeding 40 m/day make it one of the fastest.",
     "sea_level_mm": 1.0, "color": ACCENT_RED},
    {"name": "Columbia Glacier", "lat": 61.15, "lon": -147.08, "region": "Alaska",
     "retreat_km": 23, "retreat_period": "1980-2023", "rate_m_per_year": 535,
     "description": "Retreated 23 km since 1980; one of the most dramatic examples of tidewater glacier retreat.",
     "sea_level_mm": 0.3, "color": ACCENT_RED},
    {"name": "Pine Island Glacier", "lat": -75.17, "lon": -100.0, "region": "W. Antarctica",
     "retreat_km": 31, "retreat_period": "1992-2023", "rate_m_per_year": 1000,
     "description": "Retreating at ~1 km/year with warm ocean water melting its base; thinning rapidly.",
     "sea_level_mm": 0.5, "color": ACCENT_RED},
    {"name": "Thwaites Glacier", "lat": -75.5, "lon": -106.75, "region": "W. Antarctica",
     "retreat_km": 14, "retreat_period": "2000-2023", "rate_m_per_year": 600,
     "description": "Nicknamed 'Doomsday Glacier'; holds enough ice to raise sea level by 65 cm if fully collapsed.",
     "sea_level_mm": 4.0, "color": ACCENT_RED},
    {"name": "Mer de Glace", "lat": 45.9, "lon": 6.93, "region": "French Alps",
     "retreat_km": 2.3, "retreat_period": "1850-2023", "rate_m_per_year": 13,
     "description": "Has thinned by 150m and retreated 2.3 km since the Little Ice Age. Steps down to the ice grow each year.",
     "sea_level_mm": 0.0, "color": ACCENT_ORANGE},
    {"name": "Aletsch Glacier", "lat": 46.45, "lon": 8.03, "region": "Swiss Alps",
     "retreat_km": 3.5, "retreat_period": "1880-2023", "rate_m_per_year": 24,
     "description": "Lost 3.5 km and 50% of its volume since 1850. Projected to nearly vanish by 2100.",
     "sea_level_mm": 0.0, "color": ACCENT_ORANGE},
    {"name": "Gangotri Glacier", "lat": 30.92, "lon": 79.08, "region": "Himalayas",
     "retreat_km": 2.0, "retreat_period": "1936-2023", "rate_m_per_year": 22,
     "description": "Source of the Ganges retreating at 22 m/year, threatening freshwater supply for millions.",
     "sea_level_mm": 0.0, "color": ACCENT_AMBER},
    {"name": "Quelccaya Ice Cap", "lat": -13.93, "lon": -70.83, "region": "Peru",
     "retreat_km": 1.6, "retreat_period": "1963-2023", "rate_m_per_year": 60,
     "description": "Largest tropical ice cap retreating 60 m/year; ice that took 1,600 years to form melting in 25 years.",
     "sea_level_mm": 0.0, "color": ACCENT_AMBER},
    {"name": "Helheim Glacier", "lat": 66.37, "lon": -38.0, "region": "Greenland",
     "retreat_km": 8.0, "retreat_period": "2001-2023", "rate_m_per_year": 364,
     "description": "Major outlet glacier in southeastern Greenland; doubled its flow speed in early 2000s.",
     "sea_level_mm": 0.5, "color": ACCENT_RED},
    {"name": "Pasterze Glacier", "lat": 47.08, "lon": 12.72, "region": "Austrian Alps",
     "retreat_km": 2.0, "retreat_period": "1856-2023", "rate_m_per_year": 12,
     "description": "Austria's longest glacier, has lost half its area since 1850. Retreating steadily.",
     "sea_level_mm": 0.0, "color": ACCENT_ORANGE},
    {"name": "Athabasca Glacier", "lat": 52.2, "lon": -117.23, "region": "Canadian Rockies",
     "retreat_km": 1.5, "retreat_period": "1844-2023", "rate_m_per_year": 8,
     "description": "Part of the Columbia Icefield; retreated 1.5 km and lost half its volume since 1844.",
     "sea_level_mm": 0.0, "color": ACCENT_BLUE},
    {"name": "Furtwangler Glacier", "lat": -3.07, "lon": 37.35, "region": "Kilimanjaro",
     "retreat_km": 0.3, "retreat_period": "1912-2023", "rate_m_per_year": 3,
     "description": "Kilimanjaro's summit glacier lost 85% of its coverage since 1912. May vanish entirely by 2030.",
     "sea_level_mm": 0.0, "color": ACCENT_RED},
    {"name": "Lewis Glacier", "lat": -0.15, "lon": 37.3, "region": "Mount Kenya",
     "retreat_km": 0.5, "retreat_period": "1934-2023", "rate_m_per_year": 6,
     "description": "Kenya's largest glacier has shrunk by over 90% since 1934; likely to disappear within a decade.",
     "sea_level_mm": 0.0, "color": ACCENT_RED},
    {"name": "Pindari Glacier", "lat": 30.25, "lon": 79.98, "region": "Himalayas",
     "retreat_km": 2.5, "retreat_period": "1845-2023", "rate_m_per_year": 14,
     "description": "One of the most accessible Himalayan glaciers; retreated 2.5 km since first survey.",
     "sea_level_mm": 0.0, "color": ACCENT_AMBER},
]

# ═══════════════════════════════════════════════════════════════
# MODE 5: ICEBERGS & CALVING
# ═══════════════════════════════════════════════════════════════
ICEBERG_EVENTS = [
    {"name": "B-15 (Calved 2000)", "lat": -77.8, "lon": 175.0, "area_km2": 11000,
     "year": 2000, "source": "Ross Ice Shelf", "type": "Tabular",
     "description": "Largest recorded iceberg (295 km long), calved from the Ross Ice Shelf. Fragments still tracked in 2023.",
     "color": ACCENT_CYAN},
    {"name": "A-76 (Calved 2021)", "lat": -76.0, "lon": -60.0, "area_km2": 4320,
     "year": 2021, "source": "Ronne Ice Shelf", "type": "Tabular",
     "description": "Briefly the world's largest iceberg at 170 km long, calved from the Ronne Ice Shelf.",
     "color": ACCENT_ICE},
    {"name": "A-68 (Calved 2017)", "lat": -68.0, "lon": -61.0, "area_km2": 5800,
     "year": 2017, "source": "Larsen C Ice Shelf", "type": "Tabular",
     "description": "One of the largest ever; drifted toward South Georgia threatening penguin colonies before breaking up.",
     "color": ACCENT_BLUE},
    {"name": "A-23a (Calved 1986)", "lat": -75.0, "lon": -42.0, "area_km2": 4000,
     "year": 1986, "source": "Filchner Ice Shelf", "type": "Tabular",
     "description": "Grounded for decades on the Weddell Sea floor; refloated in 2023 and began drifting north.",
     "color": ACCENT_VIOLET},
    {"name": "C-19 (Calved 2002)", "lat": -77.0, "lon": 175.0, "area_km2": 5500,
     "year": 2002, "source": "Ross Ice Shelf", "type": "Tabular",
     "description": "200 km long iceberg that blocked McMurdo Sound, disrupting penguin colonies and supply routes.",
     "color": ACCENT_SNOW},
    {"name": "Titanic Iceberg", "lat": 41.73, "lon": -49.95, "area_km2": 0.3,
     "year": 1912, "source": "Jakobshavn (Greenland)", "type": "Pinnacle",
     "description": "The iceberg that sank RMS Titanic on April 15, 1912. Calved from Jakobshavn Isbrae.",
     "color": ACCENT_RED},
    {"name": "D-28 (Calved 2019)", "lat": -69.5, "lon": 73.0, "area_km2": 1636,
     "year": 2019, "source": "Amery Ice Shelf", "type": "Tabular",
     "description": "315 billion tonnes, calved from the Amery Ice Shelf, East Antarctica's largest.",
     "color": ACCENT_TEAL},
    {"name": "B-31 (Calved 2013)", "lat": -75.2, "lon": -100.0, "area_km2": 700,
     "year": 2013, "source": "Pine Island Glacier", "type": "Tabular",
     "description": "Major calving event from Pine Island Glacier, a harbinger of accelerating ice loss.",
     "color": ACCENT_ORANGE},
]

CALVING_ZONES = [
    {"name": "Iceberg Alley (Labrador Sea)", "lat": 48.0, "lon": -48.0,
     "description": "Route where Greenland icebergs drift southward past Newfoundland into North Atlantic shipping lanes.",
     "danger_level": "High", "color": ACCENT_RED},
    {"name": "Weddell Sea Calving Zone", "lat": -72.0, "lon": -45.0,
     "description": "Major calving region from Ronne-Filchner and Larsen ice shelves.",
     "danger_level": "Extreme", "color": ACCENT_RED},
    {"name": "Ross Sea Calving Front", "lat": -78.0, "lon": 175.0,
     "description": "Active calving zone along the Ross Ice Shelf barrier, producing tabular bergs.",
     "danger_level": "High", "color": ACCENT_ORANGE},
    {"name": "Amundsen Sea Embayment", "lat": -73.0, "lon": -112.0,
     "description": "Thwaites and Pine Island glaciers calve massive icebergs into this warm-water bay.",
     "danger_level": "Extreme", "color": ACCENT_RED},
    {"name": "Drake Passage Drift Zone", "lat": -60.0, "lon": -65.0,
     "description": "Icebergs drift through the Drake Passage between Antarctica and South America.",
     "danger_level": "Moderate", "color": ACCENT_AMBER},
    {"name": "Disko Bay (Greenland)", "lat": 69.25, "lon": -52.1,
     "description": "Spectacular calving from Jakobshavn Isbrae into the Ilulissat Icefjord — UNESCO World Heritage Site.",
     "danger_level": "High", "color": ACCENT_CYAN},
]

# ═══════════════════════════════════════════════════════════════
# MODE 6: PERMAFROST MAP
# ═══════════════════════════════════════════════════════════════
PERMAFROST_ZONES = [
    {"name": "Siberian Continuous Permafrost", "lat": 68.0, "lon": 110.0,
     "type": "Continuous (>90%)", "area_km2": 6500000, "depth_m": 1500,
     "description": "Deepest permafrost on Earth, up to 1,500m deep in Yakutia. Contains vast methane reserves.",
     "thaw_risk": "Moderate", "color": ACCENT_CYAN},
    {"name": "Canadian Shield Permafrost", "lat": 64.0, "lon": -100.0,
     "type": "Continuous (>90%)", "area_km2": 3500000, "depth_m": 600,
     "description": "Underlies much of northern Canada, increasingly thawing and creating thermokarst lakes.",
     "thaw_risk": "High", "color": ACCENT_ICE},
    {"name": "Alaskan North Slope", "lat": 70.0, "lon": -152.0,
     "type": "Continuous (>90%)", "area_km2": 230000, "depth_m": 400,
     "description": "Continuous permafrost zone including Prudhoe Bay; thawing threatens oil infrastructure.",
     "thaw_risk": "High", "color": ACCENT_ICE},
    {"name": "Tibetan Plateau Permafrost", "lat": 34.0, "lon": 90.0,
     "type": "Discontinuous (50-90%)", "area_km2": 1500000, "depth_m": 200,
     "description": "Highest-altitude permafrost, supporting the Qinghai-Tibet Railway. Rapidly degrading.",
     "thaw_risk": "Very High", "color": ACCENT_RED},
    {"name": "Svalbard Permafrost", "lat": 78.0, "lon": 16.0,
     "type": "Continuous (>90%)", "area_km2": 35000, "depth_m": 450,
     "description": "Warming faster than almost anywhere on Earth; threatens Global Seed Vault infrastructure.",
     "thaw_risk": "Very High", "color": ACCENT_RED},
    {"name": "Scandinavian Mountain Permafrost", "lat": 68.0, "lon": 18.0,
     "type": "Sporadic (<50%)", "area_km2": 70000, "depth_m": 50,
     "description": "Mountain permafrost in northern Scandinavia, rapidly degrading at lower elevations.",
     "thaw_risk": "Very High", "color": ACCENT_RED},
    {"name": "Alpine Permafrost (European Alps)", "lat": 46.5, "lon": 10.0,
     "type": "Sporadic (<50%)", "area_km2": 12000, "depth_m": 30,
     "description": "High-altitude permafrost destabilizing mountain slopes, causing rockfalls and infrastructure damage.",
     "thaw_risk": "Very High", "color": ACCENT_RED},
    {"name": "Mongolian Permafrost", "lat": 48.0, "lon": 100.0,
     "type": "Discontinuous (50-90%)", "area_km2": 600000, "depth_m": 250,
     "description": "Southernmost extensive permafrost in Central Asia, degrading due to overgrazing and warming.",
     "thaw_risk": "High", "color": ACCENT_ORANGE},
    {"name": "Norilsk-Taimyr Permafrost", "lat": 70.0, "lon": 90.0,
     "type": "Continuous (>90%)", "area_km2": 400000, "depth_m": 500,
     "description": "Underlies the Norilsk mining complex; thawing caused a major diesel spill in 2020.",
     "thaw_risk": "High", "color": ACCENT_ORANGE},
    {"name": "Antarctic Dry Valleys", "lat": -77.5, "lon": 162.0,
     "type": "Continuous (>90%)", "area_km2": 4800, "depth_m": 300,
     "description": "Oldest permafrost on Earth, millions of years old. Mars analog for astrobiology research.",
     "thaw_risk": "Low", "color": ACCENT_EMERALD},
]

METHANE_SITES = [
    {"name": "Batagay Megaslump", "lat": 67.58, "lon": 134.77,
     "description": "World's largest permafrost thaw crater, 1 km long and growing; releasing ancient organic carbon.",
     "type": "Thermokarst", "color": ACCENT_RED},
    {"name": "Yamal Crater", "lat": 69.97, "lon": 68.38,
     "description": "Mysterious explosion crater formed by methane blowout from thawing permafrost in 2014.",
     "type": "Methane Blowout", "color": ACCENT_RED},
    {"name": "East Siberian Arctic Shelf", "lat": 73.0, "lon": 150.0,
     "description": "Vast shallow shelf releasing methane from subsea permafrost — potential climate tipping point.",
     "type": "Subsea Methane", "color": ACCENT_ORANGE},
    {"name": "Mackenzie Delta", "lat": 68.5, "lon": -134.0,
     "description": "Major Canadian permafrost area with pingos and methane seeps from degrading permafrost.",
     "type": "Thermokarst", "color": ACCENT_AMBER},
    {"name": "Lena Delta", "lat": 72.5, "lon": 127.0,
     "description": "One of the largest Arctic river deltas; massive carbon stores thawing as permafrost degrades.",
     "type": "Thermokarst", "color": ACCENT_ORANGE},
]

# ═══════════════════════════════════════════════════════════════
# MODE 7: POLAR EXPEDITIONS
# ═══════════════════════════════════════════════════════════════
POLAR_EXPEDITIONS = [
    {"name": "Amundsen South Pole Expedition", "lat": -90.0, "lon": 0.0,
     "explorer": "Roald Amundsen", "year": 1911, "nationality": "Norwegian",
     "outcome": "Success",
     "description": "First to reach the South Pole on December 14, 1911 via the Bay of Whales and Axel Heiberg Glacier.",
     "route_points": [[-78.5, 164.0], [-82.0, 170.0], [-85.0, 175.0], [-90.0, 0.0]],
     "color": ACCENT_EMERALD},
    {"name": "Scott's Terra Nova Expedition", "lat": -90.0, "lon": 0.0,
     "explorer": "Robert Falcon Scott", "year": 1912, "nationality": "British",
     "outcome": "Tragic — all 5 died on return",
     "description": "Reached the South Pole on January 17, 1912 — 34 days after Amundsen. All five perished on the return.",
     "route_points": [[-77.85, 166.67], [-80.0, 169.0], [-83.5, 171.0], [-85.0, 175.0], [-90.0, 0.0]],
     "color": ACCENT_RED},
    {"name": "Shackleton's Endurance Expedition", "lat": -69.0, "lon": -51.0,
     "explorer": "Ernest Shackleton", "year": 1915, "nationality": "British",
     "outcome": "Ship crushed; all crew survived",
     "description": "Endurance trapped and crushed in Weddell Sea pack ice. Shackleton's boat journey to South Georgia saved all 28 men.",
     "route_points": [[-68.0, -52.0], [-72.0, -50.0], [-76.0, -47.0], [-69.0, -51.0], [-54.28, -36.5]],
     "color": ACCENT_AMBER},
    {"name": "Peary North Pole Claim", "lat": 90.0, "lon": 0.0,
     "explorer": "Robert Peary", "year": 1909, "nationality": "American",
     "outcome": "Disputed first to North Pole",
     "description": "Claimed to reach the North Pole on April 6, 1909 via Ellesmere Island. Disputed but officially recognized.",
     "route_points": [[82.5, -62.3], [85.0, -60.0], [88.0, -50.0], [90.0, 0.0]],
     "color": ACCENT_BLUE},
    {"name": "Nansen's Fram Expedition", "lat": 86.23, "lon": 96.0,
     "explorer": "Fridtjof Nansen", "year": 1896, "nationality": "Norwegian",
     "outcome": "New farthest north record",
     "description": "Intentionally froze the Fram in Arctic pack ice to drift across the pole. Reached 86d14'N by dogsled.",
     "route_points": [[69.0, 135.0], [78.0, 130.0], [83.0, 100.0], [86.23, 96.0]],
     "color": ACCENT_VIOLET},
    {"name": "Nordenskiold's Northeast Passage", "lat": 66.0, "lon": 170.0,
     "explorer": "Adolf Erik Nordenskiold", "year": 1879, "nationality": "Finnish-Swedish",
     "outcome": "First complete transit",
     "description": "First to navigate the entire Northeast Passage (Northern Sea Route) from Europe to the Pacific.",
     "route_points": [[69.0, 33.0], [72.0, 60.0], [75.0, 100.0], [73.0, 140.0], [66.0, 170.0]],
     "color": ACCENT_TEAL},
    {"name": "Amundsen's Northwest Passage", "lat": 69.6, "lon": -139.0,
     "explorer": "Roald Amundsen", "year": 1906, "nationality": "Norwegian",
     "outcome": "First complete transit",
     "description": "First to navigate the Northwest Passage in the small sloop Gjoa (1903-1906).",
     "route_points": [[59.0, -10.0], [66.0, -55.0], [74.0, -95.0], [69.6, -139.0]],
     "color": ACCENT_EMERALD},
    {"name": "Fuchs' Trans-Antarctic Expedition", "lat": -90.0, "lon": 0.0,
     "explorer": "Vivian Fuchs", "year": 1958, "nationality": "British",
     "outcome": "First land crossing of Antarctica",
     "description": "First overland crossing of Antarctica from Shackleton Base to Scott Base via the South Pole.",
     "route_points": [[-77.95, -37.15], [-82.0, -28.0], [-85.0, -10.0], [-90.0, 0.0], [-77.85, 166.67]],
     "color": ACCENT_PINK},
    {"name": "Borge Ousland Solo Antarctic Crossing", "lat": -90.0, "lon": 0.0,
     "explorer": "Borge Ousland", "year": 1997, "nationality": "Norwegian",
     "outcome": "First solo unsupported crossing",
     "description": "64-day solo unsupported crossing of Antarctica using parasailing on skis.",
     "route_points": [[-78.0, -37.0], [-85.0, -20.0], [-90.0, 0.0], [-85.0, 160.0], [-77.85, 166.67]],
     "color": ACCENT_ORANGE},
    {"name": "Erebus and Terror (Franklin Expedition)", "lat": 69.63, "lon": -98.93,
     "explorer": "Sir John Franklin", "year": 1845, "nationality": "British",
     "outcome": "All 129 crew perished",
     "description": "Most tragic Arctic expedition. Ships trapped in ice near King William Island; all hands lost. Wrecks found 2014/2016.",
     "route_points": [[74.7, -80.0], [74.0, -90.0], [70.5, -98.0], [69.63, -98.93]],
     "color": ACCENT_RED},
]

# ═══════════════════════════════════════════════════════════════
# MODE 8: ICE CORE SITES
# ═══════════════════════════════════════════════════════════════
ICE_CORE_SITES = [
    {"name": "Vostok Ice Core", "lat": -78.46, "lon": 106.84, "region": "East Antarctica",
     "depth_m": 3769, "years_covered": 420000, "completed": 1998,
     "organization": "Russia/France",
     "description": "Pioneering core revealing 420,000 years of climate history; proved CO2-temperature link.",
     "key_finding": "4 glacial-interglacial cycles; CO2 never exceeded 300 ppm in 420,000 years",
     "color": ACCENT_CYAN},
    {"name": "EPICA Dome C", "lat": -75.1, "lon": 123.33, "region": "East Antarctica",
     "depth_m": 3270, "years_covered": 800000, "completed": 2004,
     "organization": "European Consortium",
     "description": "Longest ice core record: 800,000 years of unbroken climate data, 8 glacial cycles.",
     "key_finding": "800,000 years of atmospheric CO2; current levels are unprecedented",
     "color": ACCENT_VIOLET},
    {"name": "GISP2 (Greenland)", "lat": 72.58, "lon": -38.46, "region": "Central Greenland",
     "depth_m": 3054, "years_covered": 110000, "completed": 1993,
     "organization": "USA (NSF)",
     "description": "American Greenland core revealing rapid climate shifts (Dansgaard-Oeschger events).",
     "key_finding": "Climate can shift 10C in a decade; abrupt climate change is real",
     "color": ACCENT_BLUE},
    {"name": "GRIP (Greenland)", "lat": 72.58, "lon": -37.64, "region": "Central Greenland",
     "depth_m": 3029, "years_covered": 100000, "completed": 1992,
     "organization": "European Consortium",
     "description": "European Greenland core drilled at the ice divide; companion to GISP2.",
     "key_finding": "Confirmed rapid Holocene climate variability",
     "color": ACCENT_EMERALD},
    {"name": "NGRIP (North Greenland)", "lat": 75.1, "lon": -42.32, "region": "North Greenland",
     "depth_m": 3085, "years_covered": 123000, "completed": 2003,
     "organization": "Denmark-led",
     "description": "Reached the last interglacial (Eemian) period; first to penetrate basal meltwater.",
     "key_finding": "Eemian temperatures were 5C warmer; sea level 4-6m higher than today",
     "color": ACCENT_TEAL},
    {"name": "WAIS Divide", "lat": -79.47, "lon": -112.09, "region": "West Antarctica",
     "depth_m": 3405, "years_covered": 68000, "completed": 2011,
     "organization": "USA (NSF)",
     "description": "Highest-resolution Antarctic ice core; reveals year-by-year climate for the last 30,000 years.",
     "key_finding": "Antarctic and Arctic climate changes are linked but not simultaneous",
     "color": ACCENT_AMBER},
    {"name": "Dome Fuji", "lat": -77.32, "lon": 39.7, "region": "East Antarctica",
     "depth_m": 3035, "years_covered": 720000, "completed": 2007,
     "organization": "Japan (NIPR)",
     "description": "Japanese deep ice core at one of the coldest places on Earth (-54.4C annual mean).",
     "key_finding": "Confirmed EPICA results; mid-Brunhes transition in CO2 around 430,000 years ago",
     "color": ACCENT_PINK},
    {"name": "Byrd Station Core", "lat": -80.02, "lon": -119.52, "region": "West Antarctica",
     "depth_m": 2164, "years_covered": 50000, "completed": 1968,
     "organization": "USA",
     "description": "First deep Antarctic core to reach bedrock; pioneered ice core science.",
     "key_finding": "Proved ice cores can reveal past temperatures via isotope ratios",
     "color": ACCENT_ORANGE},
    {"name": "NEEM (North Greenland Eemian)", "lat": 77.45, "lon": -51.06, "region": "NW Greenland",
     "depth_m": 2537, "years_covered": 128500, "completed": 2010,
     "organization": "Denmark-led (14 nations)",
     "description": "Targeted the Eemian interglacial to understand last warm period's ice sheet behavior.",
     "key_finding": "Greenland ice sheet survived the Eemian but was much reduced",
     "color": ACCENT_FROST},
    {"name": "Guliya Ice Cap Core", "lat": 35.28, "lon": 81.48, "region": "Tibetan Plateau",
     "depth_m": 309, "years_covered": 600000, "completed": 2015,
     "organization": "China/USA (Lonnie Thompson)",
     "description": "Highest-altitude deep ice core from the Kunlun Mountains, preserving ancient viruses.",
     "key_finding": "Contains 28 novel virus groups frozen for 15,000 years",
     "color": ACCENT_RED},
    {"name": "Kilimanjaro Ice Core", "lat": -3.07, "lon": 37.35, "region": "East Africa",
     "depth_m": 51, "years_covered": 11700, "completed": 2000,
     "organization": "USA (Lonnie Thompson)",
     "description": "Tropical ice core from a rapidly vanishing glacier; 11,700 years of African climate.",
     "key_finding": "Documented severe droughts; ice may vanish within a decade",
     "color": ACCENT_AMBER},
    {"name": "Beyond EPICA - Oldest Ice", "lat": -75.29, "lon": 122.45, "region": "East Antarctica",
     "depth_m": 2800, "years_covered": 1500000, "completed": 2025,
     "organization": "European Consortium",
     "description": "Ambitious project to recover ice spanning 1.5 million years near Dome C, Little Dome C site.",
     "key_finding": "Will reveal the Mid-Pleistocene Transition when glacial cycles shifted from 41k to 100k years",
     "color": ACCENT_VIOLET},
]

# ═══════════════════════════════════════════════════════════════
# MODE 9: GLACIAL LAKES
# ═══════════════════════════════════════════════════════════════
GLACIAL_LAKES = [
    {"name": "Jokulsarlon", "lat": 64.08, "lon": -16.18, "region": "Iceland",
     "area_km2": 18, "depth_m": 248, "type": "Proglacial lagoon",
     "description": "Iceland's most famous glacial lagoon filled with floating icebergs calved from Breidamerkurjokull.",
     "hazard": "Low", "color": ACCENT_CYAN},
    {"name": "Lake Vostok", "lat": -77.5, "lon": 106.0, "region": "Antarctica",
     "area_km2": 15690, "depth_m": 510, "type": "Subglacial",
     "description": "Earth's largest known subglacial lake, sealed under 3.7 km of ice for ~15 million years.",
     "hazard": "None (sealed)", "color": ACCENT_BLUE},
    {"name": "Tsho Rolpa", "lat": 27.86, "lon": 86.47, "region": "Nepal Himalayas",
     "area_km2": 1.54, "depth_m": 131, "type": "Moraine-dammed",
     "description": "Largest and most dangerous glacial lake in Nepal; GLOF threat to thousands downstream.",
     "hazard": "Critical", "color": ACCENT_RED},
    {"name": "Imja Tsho", "lat": 27.9, "lon": 86.93, "region": "Nepal Himalayas",
     "area_km2": 1.28, "depth_m": 116, "type": "Moraine-dammed",
     "description": "Rapidly growing lake near Everest; did not exist before 1960. Drainage works completed 2016.",
     "hazard": "High", "color": ACCENT_ORANGE},
    {"name": "Lake Palcacocha", "lat": -9.39, "lon": -77.38, "region": "Peru Andes",
     "area_km2": 0.52, "depth_m": 73, "type": "Moraine-dammed",
     "description": "GLOF from this lake destroyed Huaraz in 1941 (6,000 killed). Still a major hazard.",
     "hazard": "Critical", "color": ACCENT_RED},
    {"name": "Lago Argentino", "lat": -50.28, "lon": -72.97, "region": "Patagonia",
     "area_km2": 1466, "depth_m": 500, "type": "Proglacial",
     "description": "Largest freshwater lake in Argentina, fed by Perito Moreno and Upsala glaciers.",
     "hazard": "Low", "color": ACCENT_CYAN},
    {"name": "Lake Merzbacher", "lat": 42.22, "lon": 79.88, "region": "Tien Shan",
     "area_km2": 4.5, "depth_m": 100, "type": "Ice-dammed",
     "description": "Famous ice-dammed lake that drains catastrophically (jokulhlaup) every summer.",
     "hazard": "High (annual)", "color": ACCENT_ORANGE},
    {"name": "Grewingk Glacier Lake", "lat": 59.61, "lon": -151.06, "region": "Alaska",
     "area_km2": 0.8, "depth_m": 60, "type": "Moraine-dammed",
     "description": "Caused a tsunami-like wave in 1967 when a landslide entered the lake.",
     "hazard": "Moderate", "color": ACCENT_AMBER},
    {"name": "Lake Agassiz (Historical)", "lat": 50.0, "lon": -95.0, "region": "Canada",
     "area_km2": 440000, "depth_m": 210, "type": "Proglacial (extinct)",
     "description": "Enormous ice-age lake larger than all modern Great Lakes combined. Drained ~8,200 years ago, triggering global cooling.",
     "hazard": "Historical", "color": ACCENT_VIOLET},
    {"name": "Galong Co", "lat": 29.5, "lon": 96.5, "region": "Tibet",
     "area_km2": 3.1, "depth_m": 85, "type": "Moraine-dammed",
     "description": "Rapidly expanding glacial lake in southeastern Tibet; GLOF risk to downstream communities.",
     "hazard": "High", "color": ACCENT_ORANGE},
    {"name": "Laguna San Rafael", "lat": -46.67, "lon": -73.85, "region": "Patagonia",
     "area_km2": 32, "depth_m": 200, "type": "Proglacial lagoon",
     "description": "Glacial lagoon at the San Rafael Glacier terminus in Chile's Northern Ice Field.",
     "hazard": "Low", "color": ACCENT_TEAL},
    {"name": "Hooker Lake", "lat": -43.72, "lon": 170.1, "region": "New Zealand",
     "area_km2": 0.5, "depth_m": 135, "type": "Proglacial",
     "description": "Terminal lake of the Hooker Glacier below Aoraki/Mt. Cook; formed only in the last 50 years.",
     "hazard": "Low", "color": ACCENT_EMERALD},
    {"name": "Tilicho Lake", "lat": 28.68, "lon": 83.85, "region": "Nepal Himalayas",
     "area_km2": 4.8, "depth_m": 85, "type": "Glacial",
     "description": "One of the highest lakes in the world at 4,919m, fed by Tilicho Glacier in the Annapurna range.",
     "hazard": "Low", "color": ACCENT_ICE},
    {"name": "Grimsvötn Subglacial Lake", "lat": 64.42, "lon": -17.33, "region": "Iceland",
     "area_km2": 30, "depth_m": 200, "type": "Subglacial (volcanic)",
     "description": "Lake heated by a volcano under Vatnajokull; periodic jokulhlaups flood the southern plains.",
     "hazard": "High (volcanic)", "color": ACCENT_RED},
]

# ═══════════════════════════════════════════════════════════════
# MODE 10: POLAR WILDLIFE
# ═══════════════════════════════════════════════════════════════
POLAR_WILDLIFE = [
    {"name": "Emperor Penguin Colony - Cape Crozier", "lat": -77.45, "lon": 169.25,
     "species": "Emperor Penguin", "type": "Colony", "population": "~300,000 breeding pairs total",
     "region": "Antarctica",
     "description": "One of the largest emperor penguin colonies. These birds breed in the depths of Antarctic winter at -40C.",
     "color": ACCENT_AMBER},
    {"name": "Emperor Penguin Colony - Atka Bay", "lat": -70.62, "lon": -8.15,
     "species": "Emperor Penguin", "type": "Colony", "population": "~10,000 pairs",
     "region": "Antarctica",
     "description": "Large colony near Neumayer Station; well-studied with long-term population data.",
     "color": ACCENT_AMBER},
    {"name": "King Penguin Colony - South Georgia", "lat": -54.28, "lon": -36.5,
     "species": "King Penguin", "type": "Colony", "population": "~450,000 pairs",
     "region": "Sub-Antarctic",
     "description": "St Andrews Bay hosts one of the largest king penguin colonies; over 150,000 pairs on one beach.",
     "color": ACCENT_ORANGE},
    {"name": "Adelie Penguin Colony - Cape Adare", "lat": -71.28, "lon": 170.23,
     "species": "Adelie Penguin", "type": "Colony", "population": "~250,000 pairs",
     "region": "Antarctica",
     "description": "Largest Adelie penguin colony; site of the first Antarctic buildings (Borchgrevink's hut, 1899).",
     "color": ACCENT_TEAL},
    {"name": "Polar Bear Range - Svalbard", "lat": 78.5, "lon": 17.0,
     "species": "Polar Bear", "type": "Range", "population": "~3,000",
     "region": "Arctic (Svalbard)",
     "description": "Barents Sea subpopulation; bears depend on sea ice for hunting ringed seals.",
     "color": ACCENT_SNOW},
    {"name": "Polar Bear Range - Hudson Bay", "lat": 58.77, "lon": -94.17,
     "species": "Polar Bear", "type": "Range", "population": "~800",
     "region": "Arctic (Canada)",
     "description": "Churchill, Manitoba — 'Polar Bear Capital of the World'. Bears gather as Hudson Bay freezes.",
     "color": ACCENT_ICE},
    {"name": "Polar Bear Range - Wrangel Island", "lat": 71.0, "lon": -179.5,
     "species": "Polar Bear", "type": "Denning Site", "population": "~400 dens",
     "region": "Arctic (Russia)",
     "description": "Highest density of polar bear maternity dens in the world; UNESCO World Heritage Site.",
     "color": ACCENT_FROST},
    {"name": "Walrus Haul-out - Round Island", "lat": 58.61, "lon": -159.96,
     "species": "Pacific Walrus", "type": "Haul-out", "population": "~14,000",
     "region": "Alaska",
     "description": "Major walrus haul-out in Bristol Bay; males rest here between feeding dives.",
     "color": ACCENT_PINK},
    {"name": "Walrus Haul-out - Point Lay", "lat": 69.74, "lon": -163.01,
     "species": "Pacific Walrus", "type": "Haul-out", "population": "~35,000",
     "region": "Alaska",
     "description": "Massive haul-out caused by sea ice loss; 35,000+ walruses crowded on a single beach.",
     "color": ACCENT_RED},
    {"name": "Arctic Fox Den Site - Iceland", "lat": 65.8, "lon": -22.0,
     "species": "Arctic Fox", "type": "Range", "population": "~8,000-10,000",
     "region": "Iceland",
     "description": "Only native land mammal in Iceland; Hornstrandir Nature Reserve is a stronghold.",
     "color": ACCENT_VIOLET},
    {"name": "Narwhal Range - Baffin Bay", "lat": 74.0, "lon": -70.0,
     "species": "Narwhal", "type": "Range", "population": "~80,000",
     "region": "Arctic (Canada/Greenland)",
     "description": "Primary habitat for narwhals, the 'unicorn of the sea', with tusks up to 3m long.",
     "color": ACCENT_CYAN},
    {"name": "Elephant Seal Colony - South Georgia", "lat": -54.0, "lon": -37.0,
     "species": "Southern Elephant Seal", "type": "Colony", "population": "~113,000",
     "region": "Sub-Antarctic",
     "description": "Largest elephant seal breeding colony; males weigh up to 4,000 kg.",
     "color": ACCENT_EMERALD},
    {"name": "Leopard Seal Territory", "lat": -64.0, "lon": -62.0,
     "species": "Leopard Seal", "type": "Range", "population": "~220,000-440,000",
     "region": "Antarctic Peninsula",
     "description": "Apex predator of the Antarctic; hunts penguins and other seals around the peninsula.",
     "color": ACCENT_RED},
    {"name": "Snowy Owl Breeding - Barrow", "lat": 71.3, "lon": -156.8,
     "species": "Snowy Owl", "type": "Breeding Ground", "population": "~200,000 globally",
     "region": "Arctic Alaska",
     "description": "Arctic tundra breeding ground; snowy owls depend on lemming cycles for reproduction.",
     "color": ACCENT_SNOW},
    {"name": "Musk Ox Herd - NE Greenland", "lat": 74.0, "lon": -22.0,
     "species": "Musk Ox", "type": "Range", "population": "~4,000 (Greenland)",
     "region": "Arctic (Greenland)",
     "description": "Ice Age survivors; musk ox herds roam the tundra of Northeast Greenland National Park.",
     "color": ACCENT_AMBER},
    {"name": "Beluga Whale - Churchill River", "lat": 58.78, "lon": -94.19,
     "species": "Beluga Whale", "type": "Aggregation", "population": "~57,000",
     "region": "Hudson Bay",
     "description": "Up to 3,000 belugas gather in the Churchill River estuary each summer to feed and calve.",
     "color": ACCENT_FROST},
    {"name": "Caribou Calving Ground - Porcupine Herd", "lat": 69.0, "lon": -140.0,
     "species": "Caribou (Porcupine Herd)", "type": "Calving Ground", "population": "~218,000",
     "region": "Arctic (Alaska/Yukon)",
     "description": "One of the largest caribou herds; calving on the Arctic Coastal Plain of Alaska and Yukon.",
     "color": ACCENT_EMERALD},
    {"name": "Wandering Albatross - South Georgia", "lat": -54.1, "lon": -36.7,
     "species": "Wandering Albatross", "type": "Colony", "population": "~1,500 pairs",
     "region": "Sub-Antarctic",
     "description": "Largest flying bird (3.5m wingspan); breeds on South Georgia and circumnavigates the Southern Ocean.",
     "color": ACCENT_VIOLET},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _render_map(m: folium.Map, height: int = 500):
    """Render a Folium map in Streamlit via components.html."""
    components.html(m._repr_html_(), height=height)


def _make_dataframe(data: list, columns: list) -> pd.DataFrame:
    """Create a DataFrame from list of dicts, selecting only the given columns."""
    rows = []
    for item in data:
        row = {}
        for col in columns:
            val = item.get(col, "")
            row[col.replace("_", " ").title()] = val
        rows.append(row)
    return pd.DataFrame(rows)


def _download_csv(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Provide a CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label=label,
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
    )


def _stats_row(metrics: list):
    """Render a row of st.metric cards.  metrics = [(label, value), ...]"""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def _section_description(text: str):
    """Render a styled description paragraph."""
    st.markdown(
        f"<p style='color:{SECONDARY_TEXT};font-size:15px;margin-bottom:12px'>{text}</p>",
        unsafe_allow_html=True,
    )


def _bar_chart(labels: list, values: list, title: str, color: str = ACCENT_CYAN,
               xlabel: str = "", ylabel: str = "", horizontal: bool = False):
    """Render a matplotlib bar chart with the dark theme."""
    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.35) if horizontal else 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor=color, alpha=0.82)
        ax.set_xlabel(xlabel, color=TEXT_COLOR, fontsize=11)
        ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=11)
        ax.invert_yaxis()
    else:
        bars = ax.bar(labels, values, color=color, edgecolor=color, alpha=0.82)
        ax.set_xlabel(xlabel, color=TEXT_COLOR, fontsize=11)
        ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=11)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x" if horizontal else "y", color="#2a3550", alpha=0.4, linestyle="--")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _popup_html(title: str, fields: dict) -> str:
    """Build a safe HTML popup for folium markers.  All values are escaped."""
    html = (
        f"<div style='font-family:Inter,sans-serif;min-width:220px;'>"
        f"<b style='font-size:14px;color:#0ea5e9'>{escape(str(title))}</b><br>"
    )
    for k, v in fields.items():
        html += f"<span style='color:#94a3b8;font-size:12px'>{escape(str(k))}:</span> "
        html += f"<span style='font-size:12px'>{escape(str(v))}</span><br>"
    html += "</div>"
    return html


def _build_marker_map(data: list, center: list, zoom: int = 2,
                      popup_fields: list = None, cluster: bool = False,
                      circle: bool = False, radius: int = 7) -> folium.Map:
    """Build a folium map with markers for a data list.

    Each item must have 'name', 'lat', 'lon', 'color', 'description'.
    popup_fields: extra keys from the dict to include in the popup.
    """
    m = folium.Map(location=center, zoom_start=zoom, tiles=MAP_TILES)
    target = m
    if cluster:
        mc = MarkerCluster()
        mc.add_to(m)
        target = mc

    for item in data:
        fields = {}
        if popup_fields:
            for key in popup_fields:
                if key in item and key not in ("name", "lat", "lon", "color", "route_points", "points"):
                    label = key.replace("_", " ").title()
                    fields[label] = item[key]
        if "description" in item:
            fields["Info"] = item["description"]

        popup_h = _popup_html(item["name"], fields)
        color = item.get("color", ACCENT_CYAN)

        if circle:
            folium.CircleMarker(
                location=[item["lat"], item["lon"]],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
                popup=folium.Popup(popup_h, max_width=350),
                tooltip=escape(item["name"]),
            ).add_to(target)
        else:
            folium.Marker(
                location=[item["lat"], item["lon"]],
                popup=folium.Popup(popup_h, max_width=350),
                tooltip=escape(item["name"]),
                icon=folium.Icon(color="lightblue", icon="info-sign"),
            ).add_to(target)

    return m


# ═══════════════════════════════════════════════════════════════
# MAP MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_major_glaciers():
    """Mode 1: World's Major Glaciers."""
    _section_description(
        "An atlas of Earth's most significant glaciers — from Antarctica's colossal Lambert-Fisher "
        "Glacier to the iconic Aletsch in the Alps. Glaciers store about 69% of the world's fresh "
        "water, and their retreat is one of the most visible indicators of climate change."
    )

    # Stats
    total_glaciers = len(MAJOR_GLACIERS)
    retreating = sum(1 for g in MAJOR_GLACIERS if "Retreat" in g.get("status", ""))
    advancing = sum(1 for g in MAJOR_GLACIERS if "Advanc" in g.get("status", ""))
    total_area = sum(g["area_km2"] for g in MAJOR_GLACIERS)
    _stats_row([
        ("Total Glaciers", f"{total_glaciers}"),
        ("Retreating", f"{retreating}"),
        ("Advancing", f"{advancing}"),
        ("Total Area", f"{total_area:,.0f} km\u00b2"),
    ])

    # Filter
    regions = sorted(set(g["region"] for g in MAJOR_GLACIERS))
    region_filter = st.selectbox("Filter by Region", ["All"] + regions, key="glac_region")
    data = MAJOR_GLACIERS if region_filter == "All" else [
        g for g in MAJOR_GLACIERS if g["region"] == region_filter
    ]

    # Map
    m = _build_marker_map(
        data, center=[20, 0], zoom=2,
        popup_fields=["area_km2", "length_km", "region", "type", "status"],
        circle=True, radius=8,
    )
    _render_map(m)

    # Chart — top 10 by area
    sorted_g = sorted(MAJOR_GLACIERS, key=lambda x: x["area_km2"], reverse=True)[:12]
    _bar_chart(
        [g["name"] for g in sorted_g],
        [g["area_km2"] for g in sorted_g],
        "Largest Glaciers by Area (km\u00b2)",
        color=ACCENT_CYAN,
        xlabel="", ylabel="Area (km\u00b2)",
        horizontal=True,
    )

    # Table
    df = _make_dataframe(data, ["name", "region", "type", "area_km2", "length_km", "status"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "major_glaciers.csv")


def _render_antarctic_ice_sheet():
    """Mode 2: Antarctic Ice Sheet."""
    _section_description(
        "Antarctica holds 26.5 million km\u00b3 of ice — enough to raise global sea level by 58 meters "
        "if fully melted. This map shows research stations, ice shelves, subglacial features, and "
        "key scientific sites on the frozen continent."
    )

    _stats_row([
        ("Ice Volume", "26.5 M km\u00b3"),
        ("Ice Area", "14.0 M km\u00b2"),
        ("Research Stations", f"{len(ANTARCTIC_STATIONS)}"),
        ("Mean Temperature", "-57\u00b0C"),
    ])

    # Combined data for map
    m = folium.Map(location=[-75, 0], zoom_start=3, tiles=MAP_TILES)

    # Stations
    for s in ANTARCTIC_STATIONS:
        popup_h = _popup_html(s["name"], {
            "Country": s["country"],
            "Established": s["established"],
            "Summer Pop.": s.get("population_summer", "N/A"),
            "Type": s["type"],
            "Info": s["description"],
        })
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=s["color"],
            fill=True, fill_color=s["color"], fill_opacity=0.8,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(s["name"]),
        ).add_to(m)

    # Features
    for f in ANTARCTIC_FEATURES:
        popup_h = _popup_html(f["name"], {
            "Type": f["type"],
            "Area": f"{f['area_km2']:,} km\u00b2" if f["area_km2"] else "N/A",
            "Info": f["description"],
        })
        folium.CircleMarker(
            location=[f["lat"], f["lon"]],
            radius=12,
            color=f["color"],
            fill=True, fill_color=f["color"], fill_opacity=0.4,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(f["name"]),
        ).add_to(m)

    _render_map(m, height=550)

    # Table — stations
    st.subheader("Research Stations")
    df_s = _make_dataframe(ANTARCTIC_STATIONS,
                           ["name", "country", "established", "population_summer", "type"])
    st.dataframe(df_s, width="stretch")

    # Table — features
    st.subheader("Key Features")
    df_f = _make_dataframe(ANTARCTIC_FEATURES, ["name", "type", "area_km2"])
    st.dataframe(df_f, width="stretch")
    _download_csv(
        pd.concat([df_s.assign(Category="Station"), df_f.assign(Category="Feature")], ignore_index=True),
        "antarctic_ice_sheet.csv",
    )


def _render_arctic_region():
    """Mode 3: Arctic Region."""
    _section_description(
        "The Arctic is warming nearly four times faster than the global average. This map shows "
        "Arctic communities, shipping routes (Northwest Passage, Northern Sea Route), and key "
        "settlements above the Arctic Circle. Summer sea ice has declined over 40% since 1979."
    )

    _stats_row([
        ("Arctic Sites", f"{len(ARCTIC_SITES)}"),
        ("Shipping Routes", f"{len(ARCTIC_ROUTES)}"),
        ("Sea Ice Loss", "~13%/decade"),
        ("Warming Rate", "~4x global avg"),
    ])

    m = folium.Map(location=[72, 0], zoom_start=3, tiles=MAP_TILES)

    # Sites
    for s in ARCTIC_SITES:
        popup_h = _popup_html(s["name"], {
            "Type": s["type"],
            "Country": s["country"],
            "Info": s["description"],
        })
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=s["color"],
            fill=True, fill_color=s["color"], fill_opacity=0.8,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(s["name"]),
        ).add_to(m)

    # Routes
    for r in ARCTIC_ROUTES:
        folium.PolyLine(
            locations=r["points"],
            color=r["color"],
            weight=3,
            opacity=0.8,
            tooltip=escape(r["name"]),
            popup=folium.Popup(
                _popup_html(r["name"], {"Type": r["type"], "Info": r["description"]}),
                max_width=350,
            ),
        ).add_to(m)

    # Add Arctic Circle
    arctic_circle_pts = [[66.56, lon] for lon in range(-180, 181, 5)]
    folium.PolyLine(
        locations=arctic_circle_pts,
        color=ACCENT_FROST,
        weight=1,
        dash_array="8 4",
        opacity=0.5,
        tooltip="Arctic Circle (66\u00b034'N)",
    ).add_to(m)

    _render_map(m, height=550)

    # Table
    df = _make_dataframe(ARCTIC_SITES, ["name", "type", "country", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "arctic_region.csv")


def _render_retreating_glaciers():
    """Mode 4: Retreating Glaciers."""
    _section_description(
        "Glaciers are retreating worldwide at accelerating rates. The data below shows documented "
        "retreat distances, rates, and estimated contributions to sea-level rise. Since 1970, glaciers "
        "have lost over 9,600 billion tonnes of ice — enough to cover the entire US in 1.2 meters of water."
    )

    total = len(RETREATING_GLACIERS)
    max_rate = max(g["rate_m_per_year"] for g in RETREATING_GLACIERS)
    total_slr = sum(g["sea_level_mm"] for g in RETREATING_GLACIERS)
    _stats_row([
        ("Glaciers Tracked", f"{total}"),
        ("Max Retreat Rate", f"{max_rate:,} m/yr"),
        ("Combined SLR Potential", f"{total_slr:.1f} mm/yr"),
        ("Avg Rate", f"{np.mean([g['rate_m_per_year'] for g in RETREATING_GLACIERS]):.0f} m/yr"),
    ])

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles=MAP_TILES)
    for g in RETREATING_GLACIERS:
        # Scale radius by retreat rate
        r = min(max(g["rate_m_per_year"] / 50, 5), 20)
        popup_h = _popup_html(g["name"], {
            "Region": g["region"],
            "Retreat": f"{g['retreat_km']} km ({g['retreat_period']})",
            "Rate": f"{g['rate_m_per_year']} m/year",
            "Sea Level Contribution": f"{g['sea_level_mm']} mm/yr",
            "Info": g["description"],
        })
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=r,
            color=g["color"],
            fill=True, fill_color=g["color"], fill_opacity=0.75,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(g["name"]),
        ).add_to(m)

    _render_map(m)

    # Chart — retreat rates
    sorted_g = sorted(RETREATING_GLACIERS, key=lambda x: x["rate_m_per_year"], reverse=True)
    _bar_chart(
        [g["name"] for g in sorted_g],
        [g["rate_m_per_year"] for g in sorted_g],
        "Glacier Retreat Rates (m/year)",
        color=ACCENT_RED,
        ylabel="Retreat Rate (m/yr)",
        horizontal=True,
    )

    # Table
    df = _make_dataframe(RETREATING_GLACIERS,
                         ["name", "region", "retreat_km", "retreat_period", "rate_m_per_year", "sea_level_mm"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "retreating_glaciers.csv")


def _render_icebergs_calving():
    """Mode 5: Icebergs & Calving."""
    _section_description(
        "Massive tabular icebergs calve from Antarctic and Greenland ice shelves, sometimes "
        "larger than entire countries. The largest recorded, B-15, was 295 km long. Icebergs "
        "are tracked by the US National Ice Center and can drift for years before melting."
    )

    _stats_row([
        ("Major Icebergs", f"{len(ICEBERG_EVENTS)}"),
        ("Calving Zones", f"{len(CALVING_ZONES)}"),
        ("Largest Recorded", "11,000 km\u00b2 (B-15)"),
        ("Iceberg Alley Traffic", "~40,000/year"),
    ])

    m = folium.Map(location=[-60, -30], zoom_start=3, tiles=MAP_TILES)

    # Icebergs
    for ib in ICEBERG_EVENTS:
        r = min(max(ib["area_km2"] / 500, 6), 18)
        popup_h = _popup_html(ib["name"], {
            "Year": ib["year"],
            "Source": ib["source"],
            "Area": f"{ib['area_km2']:,} km\u00b2",
            "Type": ib["type"],
            "Info": ib["description"],
        })
        folium.CircleMarker(
            location=[ib["lat"], ib["lon"]],
            radius=r,
            color=ib["color"],
            fill=True, fill_color=ib["color"], fill_opacity=0.7,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(ib["name"]),
        ).add_to(m)

    # Calving zones
    for cz in CALVING_ZONES:
        popup_h = _popup_html(cz["name"], {
            "Danger Level": cz["danger_level"],
            "Info": cz["description"],
        })
        folium.CircleMarker(
            location=[cz["lat"], cz["lon"]],
            radius=20,
            color=cz["color"],
            fill=True, fill_color=cz["color"], fill_opacity=0.2,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(cz["name"]),
        ).add_to(m)

    _render_map(m, height=550)

    # Table — Icebergs
    st.subheader("Major Iceberg Events")
    df_ib = _make_dataframe(ICEBERG_EVENTS, ["name", "year", "source", "area_km2", "type"])
    st.dataframe(df_ib, width="stretch")

    # Table — Calving zones
    st.subheader("Calving Zones")
    df_cz = _make_dataframe(CALVING_ZONES, ["name", "danger_level", "description"])
    st.dataframe(df_cz, width="stretch")

    _download_csv(df_ib, "iceberg_events.csv")


def _render_permafrost():
    """Mode 6: Permafrost Map."""
    _section_description(
        "Permafrost — permanently frozen ground — underlies ~25% of the Northern Hemisphere's land. "
        "It contains roughly 1,700 billion tonnes of carbon, twice what's in the atmosphere. As it "
        "thaws, it releases methane and CO\u2082, creating a dangerous positive feedback loop."
    )

    _stats_row([
        ("Permafrost Zones", f"{len(PERMAFROST_ZONES)}"),
        ("Methane Sites", f"{len(METHANE_SITES)}"),
        ("Carbon Stored", "~1,700 Gt C"),
        ("Area at Risk", "~23 M km\u00b2"),
    ])

    risk_filter = st.selectbox(
        "Filter by Thaw Risk",
        ["All", "Very High", "High", "Moderate", "Low"],
        key="pf_risk",
    )

    # Map
    m = folium.Map(location=[65, 80], zoom_start=3, tiles=MAP_TILES)

    zones = PERMAFROST_ZONES if risk_filter == "All" else [
        z for z in PERMAFROST_ZONES if z.get("thaw_risk") == risk_filter
    ]

    for z in zones:
        popup_h = _popup_html(z["name"], {
            "Type": z["type"],
            "Area": f"{z['area_km2']:,} km\u00b2",
            "Depth": f"{z['depth_m']} m",
            "Thaw Risk": z["thaw_risk"],
            "Info": z["description"],
        })
        folium.CircleMarker(
            location=[z["lat"], z["lon"]],
            radius=min(max(z["area_km2"] / 300000, 8), 22),
            color=z["color"],
            fill=True, fill_color=z["color"], fill_opacity=0.5,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(z["name"]),
        ).add_to(m)

    # Methane sites
    for ms in METHANE_SITES:
        popup_h = _popup_html(ms["name"], {
            "Type": ms["type"],
            "Info": ms["description"],
        })
        folium.Marker(
            location=[ms["lat"], ms["lon"]],
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(ms["name"]),
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
        ).add_to(m)

    _render_map(m, height=550)

    # Chart — thaw risk
    risk_counts = {}
    for z in PERMAFROST_ZONES:
        r = z.get("thaw_risk", "Unknown")
        risk_counts[r] = risk_counts.get(r, 0) + 1
    risk_colors = {"Very High": ACCENT_RED, "High": ACCENT_ORANGE, "Moderate": ACCENT_AMBER,
                   "Low": ACCENT_EMERALD}
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    labels_pie = list(risk_counts.keys())
    sizes = list(risk_counts.values())
    colors_pie = [risk_colors.get(l, ACCENT_CYAN) for l in labels_pie]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels_pie, colors=colors_pie, autopct='%1.0f%%',
        textprops={'color': TEXT_COLOR, 'fontsize': 11},
        startangle=90, pctdistance=0.75,
    )
    for t in autotexts:
        t.set_color(TEXT_COLOR)
    ax.set_title("Permafrost Thaw Risk Distribution", color=TEXT_COLOR, fontsize=14, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Tables
    st.subheader("Permafrost Zones")
    df_z = _make_dataframe(zones, ["name", "type", "area_km2", "depth_m", "thaw_risk"])
    st.dataframe(df_z, width="stretch")

    st.subheader("Methane Release Sites")
    df_m = _make_dataframe(METHANE_SITES, ["name", "type", "description"])
    st.dataframe(df_m, width="stretch")

    _download_csv(df_z, "permafrost_zones.csv")


def _render_polar_expeditions():
    """Mode 7: Polar Expeditions."""
    _section_description(
        "The heroic age of polar exploration (1897-1922) produced some of history's greatest "
        "tales of endurance and tragedy. This map traces the routes of legendary explorers "
        "who risked everything to reach the ends of the Earth."
    )

    _stats_row([
        ("Expeditions", f"{len(POLAR_EXPEDITIONS)}"),
        ("Earliest", "1845 (Franklin)"),
        ("Latest", "1997 (Ousland)"),
        ("Farthest South", "90\u00b0S (Pole)"),
    ])

    exp_filter = st.selectbox(
        "Filter by Region",
        ["All", "Antarctic", "Arctic"],
        key="exp_region",
    )

    def is_antarctic(exp):
        return any(p[0] < -50 for p in exp.get("route_points", []))

    if exp_filter == "Antarctic":
        data = [e for e in POLAR_EXPEDITIONS if is_antarctic(e)]
        center, zoom = [-75, 0], 3
    elif exp_filter == "Arctic":
        data = [e for e in POLAR_EXPEDITIONS if not is_antarctic(e)]
        center, zoom = [75, -30], 3
    else:
        data = POLAR_EXPEDITIONS
        center, zoom = [0, 0], 2

    m = folium.Map(location=center, zoom_start=zoom, tiles=MAP_TILES)

    for exp in data:
        # Draw route
        if "route_points" in exp and len(exp["route_points"]) >= 2:
            folium.PolyLine(
                locations=exp["route_points"],
                color=exp["color"],
                weight=3,
                opacity=0.8,
                dash_array="6 3",
                tooltip=escape(f"{exp['explorer']} ({exp['year']})"),
            ).add_to(m)

        # Marker at destination
        popup_h = _popup_html(exp["name"], {
            "Explorer": exp["explorer"],
            "Year": exp["year"],
            "Nationality": exp["nationality"],
            "Outcome": exp["outcome"],
            "Info": exp["description"],
        })
        folium.CircleMarker(
            location=[exp["lat"], exp["lon"]],
            radius=9,
            color=exp["color"],
            fill=True, fill_color=exp["color"], fill_opacity=0.8,
            popup=folium.Popup(popup_h, max_width=380),
            tooltip=escape(exp["name"]),
        ).add_to(m)

    _render_map(m, height=550)

    # Timeline chart
    sorted_exp = sorted(data, key=lambda x: x["year"])
    colors_list = [e["color"] for e in sorted_exp]
    fig, ax = plt.subplots(figsize=(12, max(4, len(sorted_exp) * 0.4)))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    y_pos = range(len(sorted_exp))
    ax.barh(
        [f"{e['explorer']} ({e['year']})" for e in sorted_exp],
        [e["year"] for e in sorted_exp],
        color=colors_list,
        edgecolor=colors_list,
        alpha=0.8,
        left=0,
    )
    # Actually, a better timeline:
    ax.clear()
    ax.set_facecolor(SURFACE_COLOR)
    for i, exp in enumerate(sorted_exp):
        ax.plot(exp["year"], i, "o", color=exp["color"], markersize=10)
        ax.text(exp["year"] + 1, i, f" {exp['explorer']}", color=TEXT_COLOR,
                fontsize=9, va="center")
    ax.set_yticks([])
    ax.set_xlabel("Year", color=TEXT_COLOR, fontsize=11)
    ax.set_title("Polar Exploration Timeline", color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.4, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = _make_dataframe(data, ["name", "explorer", "year", "nationality", "outcome"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "polar_expeditions.csv")


def _render_ice_core_sites():
    """Mode 8: Ice Core Sites."""
    _section_description(
        "Ice cores are cylindrical samples drilled from glaciers and ice sheets that preserve "
        "a continuous record of past climate. Trapped air bubbles reveal ancient atmospheric "
        "composition, while isotope ratios record temperature. The EPICA core spans 800,000 years."
    )

    _stats_row([
        ("Core Sites", f"{len(ICE_CORE_SITES)}"),
        ("Deepest Core", f"{max(c['depth_m'] for c in ICE_CORE_SITES):,} m"),
        ("Oldest Record", f"{max(c['years_covered'] for c in ICE_CORE_SITES):,} years"),
        ("Continents", "4"),
    ])

    m = _build_marker_map(
        ICE_CORE_SITES, center=[-20, 0], zoom=2,
        popup_fields=["region", "depth_m", "years_covered", "completed", "organization", "key_finding"],
        circle=True, radius=10,
    )
    _render_map(m, height=550)

    # Chart — years covered
    sorted_c = sorted(ICE_CORE_SITES, key=lambda x: x["years_covered"], reverse=True)
    _bar_chart(
        [c["name"] for c in sorted_c],
        [c["years_covered"] for c in sorted_c],
        "Ice Core Climate Records (Years Covered)",
        color=ACCENT_VIOLET,
        ylabel="Years",
        horizontal=True,
    )

    # Chart — depth
    _bar_chart(
        [c["name"] for c in sorted_c],
        [c["depth_m"] for c in sorted_c],
        "Ice Core Depths (meters)",
        color=ACCENT_CYAN,
        ylabel="Depth (m)",
        horizontal=True,
    )

    # Table
    df = _make_dataframe(ICE_CORE_SITES,
                         ["name", "region", "depth_m", "years_covered", "completed", "organization", "key_finding"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "ice_core_sites.csv")


def _render_glacial_lakes():
    """Mode 9: Glacial Lakes."""
    _section_description(
        "Glacial lakes form as glaciers retreat, filling basins with meltwater. While beautiful, "
        "moraine-dammed lakes pose serious flood hazards (GLOFs — Glacial Lake Outburst Floods). "
        "In the Himalayas alone, over 200 glacial lakes are classified as potentially dangerous."
    )

    _stats_row([
        ("Lakes Catalogued", f"{len(GLACIAL_LAKES)}"),
        ("Critical Hazard", f"{sum(1 for l in GLACIAL_LAKES if l.get('hazard') == 'Critical')}"),
        ("High Hazard", f"{sum(1 for l in GLACIAL_LAKES if 'High' in l.get('hazard', ''))}"),
        ("Largest", f"{max(l['area_km2'] for l in GLACIAL_LAKES):,.0f} km\u00b2"),
    ])

    hazard_filter = st.selectbox(
        "Filter by Hazard Level",
        ["All", "Critical", "High", "High (annual)", "High (volcanic)", "Moderate", "Low", "None (sealed)", "Historical"],
        key="gl_hazard",
    )
    data = GLACIAL_LAKES if hazard_filter == "All" else [
        l for l in GLACIAL_LAKES if l.get("hazard") == hazard_filter
    ]

    # Map
    m = folium.Map(location=[30, 30], zoom_start=2, tiles=MAP_TILES)
    for lake in data:
        r = min(max(lake["area_km2"] ** 0.3 * 3, 6), 18)
        popup_h = _popup_html(lake["name"], {
            "Region": lake["region"],
            "Area": f"{lake['area_km2']:,.1f} km\u00b2",
            "Depth": f"{lake['depth_m']} m",
            "Type": lake["type"],
            "Hazard": lake["hazard"],
            "Info": lake["description"],
        })
        folium.CircleMarker(
            location=[lake["lat"], lake["lon"]],
            radius=r,
            color=lake["color"],
            fill=True, fill_color=lake["color"], fill_opacity=0.7,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(lake["name"]),
        ).add_to(m)

    _render_map(m)

    # Chart — hazard distribution
    hazard_counts = {}
    for l in GLACIAL_LAKES:
        h = l.get("hazard", "Unknown")
        hazard_counts[h] = hazard_counts.get(h, 0) + 1
    hazard_colors_map = {"Critical": ACCENT_RED, "High": ACCENT_ORANGE, "High (annual)": ACCENT_ORANGE,
                         "High (volcanic)": ACCENT_RED, "Moderate": ACCENT_AMBER, "Low": ACCENT_EMERALD,
                         "None (sealed)": ACCENT_BLUE, "Historical": ACCENT_VIOLET}
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    bars = ax.bar(
        list(hazard_counts.keys()),
        list(hazard_counts.values()),
        color=[hazard_colors_map.get(h, ACCENT_CYAN) for h in hazard_counts.keys()],
        edgecolor=[hazard_colors_map.get(h, ACCENT_CYAN) for h in hazard_counts.keys()],
        alpha=0.82,
    )
    ax.set_title("Glacial Lake Hazard Distribution", color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("Count", color=TEXT_COLOR, fontsize=11)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    plt.xticks(rotation=35, ha="right")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="y", color="#2a3550", alpha=0.4, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = _make_dataframe(data, ["name", "region", "area_km2", "depth_m", "type", "hazard"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "glacial_lakes.csv")


def _render_polar_wildlife():
    """Mode 10: Polar Wildlife."""
    _section_description(
        "The polar regions support astonishing wildlife adapted to extreme cold. Emperor penguins "
        "breed at -40\u00b0C, polar bears roam sea ice for hundreds of kilometers, and narwhals "
        "dive to 1,500m beneath Arctic ice. Climate change threatens all these species through "
        "habitat loss, shifting prey, and ice decline."
    )

    species_set = sorted(set(w["species"] for w in POLAR_WILDLIFE))
    _stats_row([
        ("Species Mapped", f"{len(species_set)}"),
        ("Total Sites", f"{len(POLAR_WILDLIFE)}"),
        ("Antarctic Species", f"{sum(1 for w in POLAR_WILDLIFE if 'Antarc' in w.get('region', ''))}"),
        ("Arctic Species", f"{sum(1 for w in POLAR_WILDLIFE if 'Arctic' in w.get('region', '') or 'Alaska' in w.get('region', ''))}"),
    ])

    species_filter = st.selectbox(
        "Filter by Species",
        ["All"] + species_set,
        key="pw_species",
    )
    data = POLAR_WILDLIFE if species_filter == "All" else [
        w for w in POLAR_WILDLIFE if w["species"] == species_filter
    ]

    # Map
    m = folium.Map(location=[0, 0], zoom_start=2, tiles=MAP_TILES)
    for w in data:
        popup_h = _popup_html(w["name"], {
            "Species": w["species"],
            "Type": w["type"],
            "Population": w["population"],
            "Region": w["region"],
            "Info": w["description"],
        })
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=9,
            color=w["color"],
            fill=True, fill_color=w["color"], fill_opacity=0.75,
            popup=folium.Popup(popup_h, max_width=350),
            tooltip=escape(w["name"]),
        ).add_to(m)

    _render_map(m, height=550)

    # Species count chart
    sp_counts = {}
    for w in POLAR_WILDLIFE:
        sp_counts[w["species"]] = sp_counts.get(w["species"], 0) + 1
    sorted_sp = sorted(sp_counts.items(), key=lambda x: x[1], reverse=True)
    _bar_chart(
        [s[0] for s in sorted_sp],
        [s[1] for s in sorted_sp],
        "Sites per Species",
        color=ACCENT_EMERALD,
        ylabel="Number of Sites",
        horizontal=True,
    )

    # Table
    df = _make_dataframe(data, ["name", "species", "type", "population", "region"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "polar_wildlife.csv")


# ═══════════════════════════════════════════════════════════════
# MODE REGISTRY
# ═══════════════════════════════════════════════════════════════
MAP_MODES = {
    "World's Major Glaciers": _render_major_glaciers,
    "Antarctic Ice Sheet": _render_antarctic_ice_sheet,
    "Arctic Region": _render_arctic_region,
    "Retreating Glaciers": _render_retreating_glaciers,
    "Icebergs & Calving": _render_icebergs_calving,
    "Permafrost Map": _render_permafrost,
    "Polar Expeditions": _render_polar_expeditions,
    "Ice Core Sites": _render_ice_core_sites,
    "Glacial Lakes": _render_glacial_lakes,
    "Polar Wildlife": _render_polar_wildlife,
}


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_glacier_maps_tab():
    """Render the Glaciers & Polar Regions tab for TerraScout AI."""

    # Tab header
    st.markdown(
        '<div class="tab-header cyan"><h4>\U0001F3D4\uFE0F Glaciers &amp; Polar Regions</h4>'
        '<p>Glaciers, ice sheets, Arctic, Antarctic, permafrost &amp; 10 maps</p></div>',
        unsafe_allow_html=True,
    )

    # Mode selector
    mode = st.selectbox(
        "Select Map Mode",
        list(MAP_MODES.keys()),
        key="glacier_map_mode",
    )

    st.markdown("---")

    # Render selected mode
    MAP_MODES[mode]()
