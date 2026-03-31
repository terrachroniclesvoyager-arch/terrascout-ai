# -*- coding: utf-8 -*-
"""
Deserts & Arid Landscapes module for TerraScout AI.
Curated catalog of world deserts, sand seas, oases, desert cities,
ancient civilizations, desertification fronts, flora/fauna, salt flats,
geology, and exploration routes — presented across 10 interactive map modes.
All data is curated/static or uses free public APIs (Overpass, Nominatim).
No API keys required.
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

MAP_TILES = "CartoDB dark_matter"

# ═══════════════════════════════════════════════════════════════
# MODE 1: WORLD'S GREAT DESERTS
# ═══════════════════════════════════════════════════════════════
GREAT_DESERTS = [
    {"name": "Sahara", "lat": 23.42, "lon": 2.39, "area_km2": 9200000,
     "type": "Subtropical", "continent": "Africa",
     "description": "Largest hot desert on Earth, spanning 11 countries across North Africa.",
     "temperature_max_c": 58, "annual_rain_mm": 25, "color": ACCENT_AMBER},
    {"name": "Arabian Desert", "lat": 23.0, "lon": 46.0, "area_km2": 2330000,
     "type": "Subtropical", "continent": "Asia",
     "description": "Covers most of the Arabian Peninsula including the Rub' al Khali (Empty Quarter).",
     "temperature_max_c": 54, "annual_rain_mm": 35, "color": ACCENT_ORANGE},
    {"name": "Gobi Desert", "lat": 42.59, "lon": 103.43, "area_km2": 1300000,
     "type": "Cold winter", "continent": "Asia",
     "description": "Rain shadow desert across Mongolia and northern China, home to dinosaur fossils.",
     "temperature_max_c": 45, "annual_rain_mm": 194, "color": "#d97706"},
    {"name": "Kalahari Desert", "lat": -23.5, "lon": 22.0, "area_km2": 900000,
     "type": "Subtropical", "continent": "Africa",
     "description": "Semi-arid sandy savanna in southern Africa, homeland of the San people.",
     "temperature_max_c": 45, "annual_rain_mm": 250, "color": ACCENT_ORANGE},
    {"name": "Patagonian Desert", "lat": -47.0, "lon": -68.0, "area_km2": 673000,
     "type": "Cold winter", "continent": "South America",
     "description": "Largest desert in the Americas, east of the Andes in Argentina.",
     "temperature_max_c": 35, "annual_rain_mm": 200, "color": ACCENT_BLUE},
    {"name": "Great Victoria Desert", "lat": -29.0, "lon": 129.0, "area_km2": 647000,
     "type": "Subtropical", "continent": "Australia",
     "description": "Largest desert in Australia with parallel sand ridges and spinifex grasslands.",
     "temperature_max_c": 40, "annual_rain_mm": 200, "color": ACCENT_RED},
    {"name": "Syrian Desert", "lat": 34.0, "lon": 39.0, "area_km2": 500000,
     "type": "Subtropical", "continent": "Asia",
     "description": "Rocky steppe desert spanning Syria, Jordan, Saudi Arabia, and Iraq.",
     "temperature_max_c": 46, "annual_rain_mm": 125, "color": "#fbbf24"},
    {"name": "Great Basin Desert", "lat": 40.0, "lon": -117.0, "area_km2": 492000,
     "type": "Cold winter", "continent": "North America",
     "description": "Largest US desert between the Sierra Nevada and Rocky Mountains.",
     "temperature_max_c": 37, "annual_rain_mm": 250, "color": ACCENT_TEAL},
    {"name": "Chihuahuan Desert", "lat": 30.0, "lon": -106.0, "area_km2": 453000,
     "type": "Subtropical", "continent": "North America",
     "description": "Most biologically diverse desert in North America, crossing the US-Mexico border.",
     "temperature_max_c": 40, "annual_rain_mm": 235, "color": ACCENT_EMERALD},
    {"name": "Karakum Desert", "lat": 38.5, "lon": 58.5, "area_km2": 350000,
     "type": "Cold winter", "continent": "Asia",
     "description": "Black sand desert in Turkmenistan with the 'Door to Hell' gas crater.",
     "temperature_max_c": 50, "annual_rain_mm": 150, "color": ACCENT_VIOLET},
    {"name": "Colorado Plateau Desert", "lat": 37.0, "lon": -111.0, "area_km2": 337000,
     "type": "Cold winter", "continent": "North America",
     "description": "High desert with iconic mesas, canyons, and arches in the US Southwest.",
     "temperature_max_c": 38, "annual_rain_mm": 250, "color": "#dc2626"},
    {"name": "Sonoran Desert", "lat": 32.0, "lon": -112.5, "area_km2": 310000,
     "type": "Subtropical", "continent": "North America",
     "description": "Hot desert famous for saguaro cacti, spanning Arizona and Sonora, Mexico.",
     "temperature_max_c": 48, "annual_rain_mm": 250, "color": ACCENT_EMERALD},
    {"name": "Kyzylkum Desert", "lat": 42.0, "lon": 64.0, "area_km2": 298000,
     "type": "Cold winter", "continent": "Asia",
     "description": "Red sand desert in Uzbekistan and Kazakhstan between the Amu Darya and Syr Darya.",
     "temperature_max_c": 47, "annual_rain_mm": 100, "color": ACCENT_RED},
    {"name": "Taklamakan Desert", "lat": 38.9, "lon": 82.2, "area_km2": 270000,
     "type": "Cold winter", "continent": "Asia",
     "description": "Shifting sand dunes in China's Tarim Basin, 'go in and you won't come out'.",
     "temperature_max_c": 45, "annual_rain_mm": 38, "color": ACCENT_AMBER},
    {"name": "Thar Desert", "lat": 26.79, "lon": 70.95, "area_km2": 200000,
     "type": "Subtropical", "continent": "Asia",
     "description": "Most densely populated desert in the world, across India and Pakistan.",
     "temperature_max_c": 53, "annual_rain_mm": 250, "color": ACCENT_ORANGE},
    {"name": "Gibson Desert", "lat": -24.0, "lon": 124.0, "area_km2": 156000,
     "type": "Subtropical", "continent": "Australia",
     "description": "Central Australian desert with laterite gravel plains and sand dunes.",
     "temperature_max_c": 40, "annual_rain_mm": 250, "color": "#b45309"},
    {"name": "Simpson Desert", "lat": -25.0, "lon": 137.0, "area_km2": 145000,
     "type": "Subtropical", "continent": "Australia",
     "description": "Famous for its parallel red sand dunes — over 1,100 running north-south.",
     "temperature_max_c": 40, "annual_rain_mm": 150, "color": ACCENT_RED},
    {"name": "Atacama Desert", "lat": -24.5, "lon": -69.25, "area_km2": 105000,
     "type": "Cold coastal", "continent": "South America",
     "description": "Driest non-polar desert on Earth, some areas have never recorded rainfall.",
     "temperature_max_c": 40, "annual_rain_mm": 1, "color": ACCENT_CYAN},
    {"name": "Namib Desert", "lat": -24.5, "lon": 15.5, "area_km2": 81000,
     "type": "Coastal", "continent": "Africa",
     "description": "One of the oldest deserts (55-80 million years), famous for Sossusvlei dunes.",
     "temperature_max_c": 45, "annual_rain_mm": 13, "color": ACCENT_PINK},
    {"name": "Mojave Desert", "lat": 35.0, "lon": -116.0, "area_km2": 65000,
     "type": "Subtropical", "continent": "North America",
     "description": "Home to Death Valley (lowest, driest, hottest in North America) and Joshua Trees.",
     "temperature_max_c": 57, "annual_rain_mm": 137, "color": "#fbbf24"},
    {"name": "Antarctic Desert", "lat": -82.0, "lon": 0.0, "area_km2": 14200000,
     "type": "Polar", "continent": "Antarctica",
     "description": "Technically the largest desert on Earth by area; interior is extremely dry.",
     "temperature_max_c": -12, "annual_rain_mm": 51, "color": "#60a5fa"},
    {"name": "Arctic Desert", "lat": 75.0, "lon": -40.0, "area_km2": 13900000,
     "type": "Polar", "continent": "Arctic",
     "description": "Second largest desert encompassing the Arctic basin, receiving minimal precipitation.",
     "temperature_max_c": 10, "annual_rain_mm": 250, "color": "#93c5fd"},
    {"name": "Lut Desert (Dasht-e Lut)", "lat": 30.5, "lon": 59.0, "area_km2": 51800,
     "type": "Subtropical", "continent": "Asia",
     "description": "Hottest surface temperature ever recorded by satellite: 70.7 C (159.3 F).",
     "temperature_max_c": 56, "annual_rain_mm": 30, "color": ACCENT_RED},
    {"name": "Negev Desert", "lat": 30.8, "lon": 34.8, "area_km2": 12000,
     "type": "Subtropical", "continent": "Asia",
     "description": "Desert occupying southern Israel, with ancient Nabatean cities and makhtesh craters.",
     "temperature_max_c": 46, "annual_rain_mm": 90, "color": ACCENT_AMBER},
    {"name": "Wadi Rum", "lat": 29.57, "lon": 35.42, "area_km2": 720,
     "type": "Subtropical", "continent": "Asia",
     "description": "Valley of the Moon in Jordan — sandstone mountains and red sand, T.E. Lawrence's desert.",
     "temperature_max_c": 44, "annual_rain_mm": 50, "color": ACCENT_ORANGE},
]

# ═══════════════════════════════════════════════════════════════
# MODE 2: SAND SEAS (ERGS)
# ═══════════════════════════════════════════════════════════════
SAND_SEAS = [
    {"name": "Rub' al Khali (Empty Quarter)", "lat": 20.0, "lon": 50.0, "area_km2": 650000,
     "country": "Saudi Arabia/UAE/Oman/Yemen", "dune_height_m": 250,
     "description": "Largest contiguous sand desert in the world. Dunes reach 250m high.",
     "color": ACCENT_AMBER},
    {"name": "Grand Erg Oriental", "lat": 33.5, "lon": 7.0, "area_km2": 192000,
     "country": "Algeria/Tunisia", "dune_height_m": 120,
     "description": "Vast sand sea in the northern Sahara with star and barchan dunes.",
     "color": ACCENT_ORANGE},
    {"name": "Grand Erg Occidental", "lat": 30.5, "lon": -0.5, "area_km2": 103000,
     "country": "Algeria", "dune_height_m": 100,
     "description": "Western companion to the Grand Erg Oriental, fed by ancient river systems.",
     "color": "#d97706"},
    {"name": "Erg Chebbi", "lat": 31.15, "lon": -3.97, "area_km2": 50,
     "country": "Morocco", "dune_height_m": 150,
     "description": "Morocco's most famous erg near Merzouga, a top Saharan tourist destination.",
     "color": ACCENT_AMBER},
    {"name": "Erg Chigaga", "lat": 29.83, "lon": -6.28, "area_km2": 100,
     "country": "Morocco", "dune_height_m": 300,
     "description": "Remote sand sea south of Zagora with enormous dune formations.",
     "color": ACCENT_ORANGE},
    {"name": "Taklamakan Sand Sea", "lat": 38.9, "lon": 82.2, "area_km2": 270000,
     "country": "China", "dune_height_m": 200,
     "description": "Shifting sands of the Tarim Basin — one of the world's largest sandy deserts.",
     "color": "#fbbf24"},
    {"name": "Namib Sand Sea", "lat": -24.75, "lon": 15.3, "area_km2": 34000,
     "country": "Namibia", "dune_height_m": 325,
     "description": "UNESCO World Heritage Site. Dune 7 at 383m is among the tallest in the world.",
     "color": ACCENT_PINK},
    {"name": "Idehan Ubari", "lat": 26.5, "lon": 12.5, "area_km2": 58000,
     "country": "Libya", "dune_height_m": 150,
     "description": "Sand sea in the Fezzan region with hidden salt lakes between the dunes.",
     "color": ACCENT_RED},
    {"name": "Idehan Murzuq", "lat": 25.0, "lon": 13.0, "area_km2": 58000,
     "country": "Libya", "dune_height_m": 200,
     "description": "Vast sand sea south of Murzuq containing ancient cave art sites.",
     "color": ACCENT_ORANGE},
    {"name": "Erg of Bilma", "lat": 18.7, "lon": 12.9, "area_km2": 150000,
     "country": "Niger", "dune_height_m": 100,
     "description": "Major erg in the Tenere region, historically crossed by salt caravans.",
     "color": ACCENT_AMBER},
    {"name": "Great Sand Sea", "lat": 26.5, "lon": 26.0, "area_km2": 72000,
     "country": "Egypt/Libya", "dune_height_m": 140,
     "description": "Vast sand sea on the Egypt-Libya border with parallel seif dunes up to 140km long.",
     "color": "#fbbf24"},
    {"name": "Wahiba Sands (Sharqiya)", "lat": 22.0, "lon": 58.5, "area_km2": 12500,
     "country": "Oman", "dune_height_m": 100,
     "description": "Accessible erg in Oman with red-orange megadunes, popular for desert camping.",
     "color": ACCENT_RED},
    {"name": "Lencois Maranhenses", "lat": -2.5, "lon": -43.1, "area_km2": 1550,
     "country": "Brazil", "dune_height_m": 40,
     "description": "Striking white sand dunes with seasonal blue-green lagoons — not truly arid.",
     "color": ACCENT_CYAN},
    {"name": "Badain Jaran Dune Field", "lat": 40.0, "lon": 102.0, "area_km2": 49000,
     "country": "China", "dune_height_m": 500,
     "description": "Home to the tallest stationary dunes on Earth (up to 500m) with inter-dune lakes.",
     "color": ACCENT_VIOLET},
    {"name": "Simpson Desert Dune Field", "lat": -25.0, "lon": 137.0, "area_km2": 145000,
     "country": "Australia", "dune_height_m": 40,
     "description": "Over 1,100 parallel red sand dunes running north-south across central Australia.",
     "color": ACCENT_RED},
    {"name": "Erg Admer", "lat": 26.0, "lon": 8.0, "area_km2": 12000,
     "country": "Algeria", "dune_height_m": 80,
     "description": "Sand sea near Djanet with prehistoric rock art in surrounding tassili plateaus.",
     "color": ACCENT_AMBER},
    {"name": "Ad-Dahna Desert", "lat": 23.5, "lon": 45.0, "area_km2": 45000,
     "country": "Saudi Arabia", "dune_height_m": 120,
     "description": "Arc-shaped sand corridor connecting the Nafud to the Rub' al Khali.",
     "color": ACCENT_ORANGE},
    {"name": "Great Nafud", "lat": 28.5, "lon": 41.0, "area_km2": 72000,
     "country": "Saudi Arabia", "dune_height_m": 90,
     "description": "Northern Saudi sand sea with distinctive red sand and seasonal lakes.",
     "color": ACCENT_RED},
]

# ═══════════════════════════════════════════════════════════════
# MODE 3: OASES
# ═══════════════════════════════════════════════════════════════
OASES = [
    {"name": "Siwa Oasis", "lat": 29.20, "lon": 25.52, "country": "Egypt",
     "description": "Ancient oasis visited by Alexander the Great to consult the Oracle of Amun.",
     "population": 33000, "water_source": "Natural springs", "color": ACCENT_EMERALD},
    {"name": "Al-Ahsa Oasis", "lat": 25.38, "lon": 49.58, "country": "Saudi Arabia",
     "description": "UNESCO World Heritage Site — largest natural oasis with 2.5 million palm trees.",
     "population": 1200000, "water_source": "Artesian springs", "color": ACCENT_EMERALD},
    {"name": "Huacachina", "lat": -14.09, "lon": -75.76, "country": "Peru",
     "description": "Tiny village built around a natural lagoon amid towering sand dunes.",
     "population": 100, "water_source": "Natural lagoon", "color": ACCENT_CYAN},
    {"name": "Timimoun", "lat": 29.26, "lon": 0.23, "country": "Algeria",
     "description": "Red oasis city on the edge of the Grand Erg Occidental, historic caravan stop.",
     "population": 33000, "water_source": "Foggaras (underground channels)", "color": ACCENT_AMBER},
    {"name": "Ouarzazate", "lat": 30.92, "lon": -6.90, "country": "Morocco",
     "description": "'Door of the Desert' — gateway to the Sahara, major film location.",
     "population": 72000, "water_source": "Draa River / snowmelt", "color": ACCENT_ORANGE},
    {"name": "Tozeur", "lat": 33.92, "lon": 8.13, "country": "Tunisia",
     "description": "Date palm oasis with traditional brick architecture near Chott el Jerid.",
     "population": 43000, "water_source": "Artesian wells", "color": ACCENT_EMERALD},
    {"name": "Turpan Oasis", "lat": 42.95, "lon": 89.19, "country": "China",
     "description": "Silk Road oasis at -154m elevation, using karez irrigation tunnels for millennia.",
     "population": 630000, "water_source": "Karez tunnels (qanat)", "color": ACCENT_VIOLET},
    {"name": "Kharga Oasis", "lat": 25.44, "lon": 30.56, "country": "Egypt",
     "description": "Largest oasis in Egypt's Western Desert, with Temple of Hibis (6th century BC).",
     "population": 70000, "water_source": "Deep wells", "color": ACCENT_EMERALD},
    {"name": "Dakhla Oasis", "lat": 25.49, "lon": 29.00, "country": "Egypt",
     "description": "Remote Egyptian oasis with Roman-era ruins and hot springs.",
     "population": 80000, "water_source": "Artesian wells & springs", "color": ACCENT_EMERALD},
    {"name": "Bahariya Oasis", "lat": 28.35, "lon": 28.86, "country": "Egypt",
     "description": "Egyptian oasis known for the Valley of the Golden Mummies discovery.",
     "population": 38000, "water_source": "Natural springs", "color": ACCENT_CYAN},
    {"name": "Figuig", "lat": 32.11, "lon": -1.23, "country": "Morocco",
     "description": "Border oasis with 200,000 date palms, ancient underground irrigation system.",
     "population": 13000, "water_source": "Artesian springs", "color": ACCENT_AMBER},
    {"name": "Ghardaia (M'zab Valley)", "lat": 32.49, "lon": 3.67, "country": "Algeria",
     "description": "UNESCO Heritage — five fortified cities of the Mozabite Berbers.",
     "population": 150000, "water_source": "Wells & wadis", "color": ACCENT_VIOLET},
    {"name": "Ein Gedi", "lat": 31.46, "lon": 35.39, "country": "Israel",
     "description": "Desert oasis near the Dead Sea with waterfalls and ibex, mentioned in the Bible.",
     "population": 600, "water_source": "Natural springs", "color": ACCENT_CYAN},
    {"name": "Tafilalet", "lat": 31.43, "lon": -4.02, "country": "Morocco",
     "description": "Largest oasis in Morocco — historic Sijilmasa caravan terminus.",
     "population": 100000, "water_source": "Ziz River / khettaras", "color": ACCENT_ORANGE},
    {"name": "Liwa Oasis", "lat": 23.13, "lon": 53.76, "country": "UAE",
     "description": "Crescent-shaped oasis at the edge of the Rub' al Khali, home of Al Nahyan dynasty.",
     "population": 20000, "water_source": "Groundwater", "color": ACCENT_AMBER},
    {"name": "Al Ain Oasis", "lat": 24.22, "lon": 55.77, "country": "UAE",
     "description": "UNESCO Heritage — 3,000 year old falaj irrigation system still in use.",
     "population": 770000, "water_source": "Falaj (underground channels)", "color": ACCENT_EMERALD},
    {"name": "Douz", "lat": 33.46, "lon": 8.13, "country": "Tunisia",
     "description": "'Gateway to the Sahara' in Tunisia, famous for its annual desert festival.",
     "population": 35000, "water_source": "Artesian wells", "color": ACCENT_ORANGE},
    {"name": "Palmyra", "lat": 34.55, "lon": 38.27, "country": "Syria",
     "description": "Ancient Silk Road oasis city — UNESCO Heritage, once ruled by Queen Zenobia.",
     "population": 50000, "water_source": "Efqa spring", "color": ACCENT_PINK},
]

# ═══════════════════════════════════════════════════════════════
# MODE 4: DESERT CITIES
# ═══════════════════════════════════════════════════════════════
DESERT_CITIES = [
    {"name": "Dubai", "lat": 25.20, "lon": 55.27, "country": "UAE",
     "population": 3500000, "desert": "Arabian Desert",
     "description": "From fishing village to megacity in 50 years — extreme desert urbanism.",
     "founded": "1833", "color": ACCENT_CYAN},
    {"name": "Las Vegas", "lat": 36.17, "lon": -115.14, "country": "USA",
     "population": 2890000, "desert": "Mojave Desert",
     "description": "Entertainment capital built in the driest desert of the US Southwest.",
     "founded": "1905", "color": ACCENT_AMBER},
    {"name": "Riyadh", "lat": 24.71, "lon": 46.68, "country": "Saudi Arabia",
     "population": 7680000, "desert": "Arabian Desert",
     "description": "Capital of Saudi Arabia, one of the fastest-growing cities on Earth.",
     "founded": "1737", "color": ACCENT_EMERALD},
    {"name": "Phoenix", "lat": 33.45, "lon": -112.07, "country": "USA",
     "population": 4950000, "desert": "Sonoran Desert",
     "description": "Hottest major city in the US; average summer highs exceed 40 C.",
     "founded": "1881", "color": ACCENT_ORANGE},
    {"name": "Cairo", "lat": 30.04, "lon": 31.24, "country": "Egypt",
     "population": 21300000, "desert": "Sahara (edge)",
     "description": "Largest city in Africa, on the Nile at the edge of the Western Desert.",
     "founded": "969 CE", "color": ACCENT_RED},
    {"name": "Alice Springs", "lat": -23.70, "lon": 133.87, "country": "Australia",
     "population": 26000, "desert": "Simpson/Central Australian",
     "description": "Outback town near Uluru, gateway to Australia's Red Centre.",
     "founded": "1872", "color": ACCENT_RED},
    {"name": "Doha", "lat": 25.29, "lon": 51.53, "country": "Qatar",
     "population": 2400000, "desert": "Arabian Desert",
     "description": "Rapidly modernizing capital on the Persian Gulf coast.",
     "founded": "1825", "color": ACCENT_CYAN},
    {"name": "Tucson", "lat": 32.22, "lon": -110.97, "country": "USA",
     "population": 1060000, "desert": "Sonoran Desert",
     "description": "UNESCO City of Gastronomy surrounded by saguaro forests and mountain 'sky islands'.",
     "founded": "1775", "color": ACCENT_EMERALD},
    {"name": "Marrakech", "lat": 31.63, "lon": -8.0, "country": "Morocco",
     "population": 1070000, "desert": "Sahara (edge)",
     "description": "Red City at the foot of the Atlas Mountains, historic caravan trade hub.",
     "founded": "1070 CE", "color": ACCENT_ORANGE},
    {"name": "Jeddah", "lat": 21.49, "lon": 39.19, "country": "Saudi Arabia",
     "population": 4700000, "desert": "Arabian Desert",
     "description": "Gateway to Mecca on the Red Sea coast, historic port and trading center.",
     "founded": "6th century BC", "color": ACCENT_AMBER},
    {"name": "Abu Dhabi", "lat": 24.45, "lon": 54.65, "country": "UAE",
     "population": 1500000, "desert": "Arabian Desert",
     "description": "Capital of the UAE, island city with massive sovereign wealth.",
     "founded": "1761", "color": ACCENT_CYAN},
    {"name": "Muscat", "lat": 23.61, "lon": 58.54, "country": "Oman",
     "population": 1560000, "desert": "Arabian Desert",
     "description": "Ancient port city squeezed between desert mountains and the sea.",
     "founded": "1st century CE", "color": ACCENT_TEAL},
    {"name": "Windhoek", "lat": -22.57, "lon": 17.08, "country": "Namibia",
     "population": 450000, "desert": "Namib (edge)",
     "description": "Capital of Namibia at 1,700m elevation, gateway to the Namib.",
     "founded": "1890", "color": ACCENT_VIOLET},
    {"name": "Lima", "lat": -12.05, "lon": -77.04, "country": "Peru",
     "population": 10500000, "desert": "Sechura/Atacama coast",
     "description": "Second largest desert city in the world — virtually no rainfall.",
     "founded": "1535", "color": ACCENT_PINK},
    {"name": "Nouakchott", "lat": 18.09, "lon": -15.98, "country": "Mauritania",
     "population": 1200000, "desert": "Sahara",
     "description": "Capital threatened by advancing sand dunes from the Sahara.",
     "founded": "1958", "color": ACCENT_AMBER},
    {"name": "Timbuktu", "lat": 16.77, "lon": -3.01, "country": "Mali",
     "population": 54000, "desert": "Sahara (Sahel edge)",
     "description": "Legendary center of Islamic scholarship at the Sahara's southern edge.",
     "founded": "12th century", "color": ACCENT_ORANGE},
    {"name": "Isfahan", "lat": 32.65, "lon": 51.68, "country": "Iran",
     "population": 2100000, "desert": "Central Iranian Plateau",
     "description": "'Half the World' — stunning Islamic architecture in an arid basin.",
     "founded": "600 BC", "color": ACCENT_VIOLET},
    {"name": "Ashgabat", "lat": 37.96, "lon": 58.33, "country": "Turkmenistan",
     "population": 1030000, "desert": "Karakum Desert",
     "description": "White marble capital at the edge of the Karakum — Guinness record holder.",
     "founded": "1881", "color": ACCENT_CYAN},
]

# ═══════════════════════════════════════════════════════════════
# MODE 5: ANCIENT DESERT CIVILIZATIONS
# ═══════════════════════════════════════════════════════════════
ANCIENT_CIVILIZATIONS = [
    {"name": "Petra (Nabatean Kingdom)", "lat": 30.33, "lon": 35.44,
     "civilization": "Nabatean", "period": "312 BC - 106 AD",
     "description": "Rose-red city carved into sandstone cliffs, masters of desert water management.",
     "color": ACCENT_PINK},
    {"name": "Mesa Verde (Ancestral Puebloans)", "lat": 37.18, "lon": -108.49,
     "civilization": "Ancestral Puebloan", "period": "550 - 1300 AD",
     "description": "Cliff dwellings in the Colorado Plateau desert — over 600 structures.",
     "color": ACCENT_EMERALD},
    {"name": "Chaco Canyon", "lat": 36.06, "lon": -107.96,
     "civilization": "Ancestral Puebloan", "period": "850 - 1250 AD",
     "description": "Great Houses aligned to solar and lunar cycles in the high desert.",
     "color": ACCENT_TEAL},
    {"name": "Garamantes Capital (Germa)", "lat": 26.55, "lon": 13.08,
     "civilization": "Garamantes", "period": "500 BC - 700 AD",
     "description": "Lost Saharan civilization with underground irrigation (foggaras) network.",
     "color": ACCENT_AMBER},
    {"name": "Palmyra", "lat": 34.55, "lon": 38.27,
     "civilization": "Palmyrene", "period": "2000 BC - 272 AD",
     "description": "Silk Road oasis kingdom of Queen Zenobia that challenged Rome.",
     "color": ACCENT_VIOLET},
    {"name": "Thebes / Luxor (New Kingdom)", "lat": 25.70, "lon": 32.64,
     "civilization": "Ancient Egyptian", "period": "1550 - 1070 BC",
     "description": "Valley of the Kings on the Saharan edge — tombs of pharaohs.",
     "color": ACCENT_AMBER},
    {"name": "Meroe (Kingdom of Kush)", "lat": 16.94, "lon": 33.75,
     "civilization": "Kushite", "period": "750 BC - 350 AD",
     "description": "Nubian pyramids in the Sudanese desert — over 200 pyramids survive.",
     "color": ACCENT_ORANGE},
    {"name": "Leptis Magna", "lat": 32.64, "lon": 14.29,
     "civilization": "Phoenician / Roman", "period": "1000 BC - 650 AD",
     "description": "Magnificent Roman city on the Saharan coast, birthplace of Emperor Septimius Severus.",
     "color": ACCENT_RED},
    {"name": "Mohenjo-daro", "lat": 27.33, "lon": 68.14,
     "civilization": "Indus Valley", "period": "2500 - 1900 BC",
     "description": "Advanced urban center in what is now the Thar Desert, with sewage systems.",
     "color": ACCENT_CYAN},
    {"name": "Ur (Sumerian)", "lat": 30.96, "lon": 46.10,
     "civilization": "Sumerian", "period": "3800 - 500 BC",
     "description": "Great Ziggurat in what became the Iraqi desert — Abraham's city of origin.",
     "color": ACCENT_AMBER},
    {"name": "Hatra", "lat": 35.59, "lon": 42.72,
     "civilization": "Parthian/Arab", "period": "300 BC - 240 AD",
     "description": "Fortified desert city that withstood Roman sieges, UNESCO Heritage.",
     "color": ACCENT_ORANGE},
    {"name": "Avdat (Nabatean Negev)", "lat": 30.79, "lon": 34.77,
     "civilization": "Nabatean", "period": "3rd century BC - 7th century AD",
     "description": "Incense Route caravan city in the Negev, UNESCO World Heritage.",
     "color": ACCENT_PINK},
    {"name": "Chan Chan", "lat": -8.11, "lon": -79.07,
     "civilization": "Chimu", "period": "850 - 1470 AD",
     "description": "Largest adobe city in the world on Peru's coastal desert, pre-Inca.",
     "color": ACCENT_BLUE},
    {"name": "Nazca Lines", "lat": -14.74, "lon": -75.13,
     "civilization": "Nazca", "period": "500 BC - 500 AD",
     "description": "Giant geoglyphs in the Peruvian desert visible only from the air.",
     "color": ACCENT_EMERALD},
    {"name": "Jiaohe (Yarkhoto)", "lat": 42.95, "lon": 89.07,
     "civilization": "Jushi/Tang Chinese", "period": "200 BC - 1300 AD",
     "description": "Silk Road garrison city in the Turpan Depression, carved from an earthen plateau.",
     "color": ACCENT_VIOLET},
    {"name": "Gaochang (Khocho)", "lat": 42.86, "lon": 89.53,
     "civilization": "Uyghur/Tang", "period": "1st century BC - 13th century AD",
     "description": "Major Silk Road oasis city in Turpan, once capital of the Uyghur Kingdom.",
     "color": ACCENT_BLUE},
    {"name": "Great Zimbabwe", "lat": -20.27, "lon": 30.93,
     "civilization": "Shona", "period": "1100 - 1450 AD",
     "description": "Stone enclosures in the semi-arid savanna, center of a powerful trading kingdom.",
     "color": ACCENT_EMERALD},
    {"name": "Djenne-Djenno", "lat": 13.91, "lon": -4.55,
     "civilization": "Mande", "period": "250 BC - 1400 AD",
     "description": "One of the oldest cities in sub-Saharan Africa at the Saharan edge.",
     "color": ACCENT_AMBER},
]

# ═══════════════════════════════════════════════════════════════
# MODE 6: DESERTIFICATION FRONTS
# ═══════════════════════════════════════════════════════════════
DESERTIFICATION_FRONTS = [
    {"name": "Sahel — Southern Sahara Advance", "lat": 14.5, "lon": 0.0,
     "region": "West/Central Africa", "area_affected_km2": 3600000,
     "description": "The Sahara advances southward into the Sahel at an estimated rate of 48 km/year in some areas.",
     "severity": "Critical", "color": ACCENT_RED},
    {"name": "Aral Sea Basin", "lat": 45.0, "lon": 59.0,
     "region": "Central Asia", "area_affected_km2": 68000,
     "description": "Once the 4th largest lake, shrunk to 10% of original size. Now the Aralkum desert.",
     "severity": "Catastrophic", "color": ACCENT_RED},
    {"name": "Northern China — Gobi Expansion", "lat": 41.0, "lon": 110.0,
     "region": "East Asia", "area_affected_km2": 2700000,
     "description": "Gobi desert expands south, sending sandstorms to Beijing. Great Green Wall in response.",
     "severity": "Severe", "color": ACCENT_ORANGE},
    {"name": "Thar Desert — Rajasthan Expansion", "lat": 27.0, "lon": 71.0,
     "region": "South Asia", "area_affected_km2": 200000,
     "description": "Thar desert expanding westward into agricultural land in India and Pakistan.",
     "severity": "Moderate", "color": ACCENT_AMBER},
    {"name": "Horn of Africa", "lat": 5.0, "lon": 43.0,
     "region": "East Africa", "area_affected_km2": 500000,
     "description": "Accelerating desertification in Somalia, Ethiopia, and Kenya due to overgrazing and drought.",
     "severity": "Critical", "color": ACCENT_RED},
    {"name": "Lake Chad Basin", "lat": 13.5, "lon": 14.0,
     "region": "Central Africa", "area_affected_km2": 25000,
     "description": "Lake Chad has shrunk 90% since the 1960s. Water conflict affects 30 million people.",
     "severity": "Critical", "color": ACCENT_RED},
    {"name": "Patagonian Steppe", "lat": -45.0, "lon": -69.0,
     "region": "South America", "area_affected_km2": 300000,
     "description": "Overgrazing by sheep has accelerated erosion and desertification in Argentine Patagonia.",
     "severity": "Moderate", "color": ACCENT_AMBER},
    {"name": "Australian Rangelands", "lat": -28.0, "lon": 140.0,
     "region": "Australia", "area_affected_km2": 600000,
     "description": "Pastoral degradation and salinity issues in semi-arid Australia.",
     "severity": "Moderate", "color": ACCENT_ORANGE},
    {"name": "Mediterranean Basin", "lat": 37.0, "lon": 15.0,
     "region": "Southern Europe", "area_affected_km2": 400000,
     "description": "Spain, Italy, Greece, and Turkey face increasing desertification from climate change.",
     "severity": "Moderate", "color": ACCENT_AMBER},
    {"name": "Loess Plateau — Yellow River", "lat": 36.5, "lon": 109.0,
     "region": "East Asia", "area_affected_km2": 640000,
     "description": "Massive erosion and desertification on China's Loess Plateau, now partly restored.",
     "severity": "Recovering", "color": ACCENT_EMERALD},
    {"name": "Ferlo — Senegal", "lat": 14.9, "lon": -13.5,
     "region": "West Africa", "area_affected_km2": 60000,
     "description": "Saharan expansion into the Ferlo region of northern Senegal.",
     "severity": "Severe", "color": ACCENT_ORANGE},
    {"name": "Central Iran Plateau", "lat": 33.0, "lon": 54.0,
     "region": "Middle East", "area_affected_km2": 1000000,
     "description": "Groundwater depletion and dam building desiccating lakes and wetlands across Iran.",
     "severity": "Severe", "color": ACCENT_RED},
]

# ═══════════════════════════════════════════════════════════════
# MODE 7: DESERT FLORA & FAUNA
# ═══════════════════════════════════════════════════════════════
DESERT_FLORA_FAUNA = [
    {"name": "Saguaro Cactus Forests", "lat": 32.18, "lon": -111.17,
     "type": "Flora", "desert": "Sonoran",
     "description": "Iconic columnar cacti up to 12m tall, living 150-200 years. Saguaro National Park.",
     "species": "Carnegiea gigantea", "color": ACCENT_EMERALD},
    {"name": "Welwitschia Plains", "lat": -22.5, "lon": 14.5,
     "type": "Flora", "desert": "Namib",
     "description": "Welwitschia mirabilis — living fossil with only 2 leaves, surviving 1,000+ years.",
     "species": "Welwitschia mirabilis", "color": ACCENT_EMERALD},
    {"name": "Namib Desert Beetles", "lat": -24.0, "lon": 15.0,
     "type": "Fauna", "desert": "Namib",
     "description": "Fog-basking beetles harvest water from fog on their bumpy wing cases — biomimicry inspiration.",
     "species": "Stenocara gracilipes", "color": ACCENT_CYAN},
    {"name": "Dromedary Camel Routes (Sahara)", "lat": 25.0, "lon": 5.0,
     "type": "Fauna", "desert": "Sahara",
     "description": "One-humped camels, domesticated 3,000 years ago, survive weeks without water.",
     "species": "Camelus dromedarius", "color": ACCENT_AMBER},
    {"name": "Bactrian Camel Range (Gobi)", "lat": 43.0, "lon": 100.0,
     "type": "Fauna", "desert": "Gobi",
     "description": "Wild two-humped camels critically endangered — fewer than 1,000 remain in the Gobi.",
     "species": "Camelus ferus", "color": ACCENT_ORANGE},
    {"name": "Arabian Oryx Sanctuary", "lat": 21.0, "lon": 57.0,
     "type": "Fauna", "desert": "Arabian",
     "description": "Oryx was extinct in the wild, reintroduced successfully — a conservation triumph.",
     "species": "Oryx leucoryx", "color": ACCENT_VIOLET},
    {"name": "Joshua Tree Forest", "lat": 33.88, "lon": -115.90,
     "type": "Flora", "desert": "Mojave",
     "description": "Bizarre tree-like yuccas defining the Mojave landscape, pollinated only by one moth.",
     "species": "Yucca brevifolia", "color": ACCENT_EMERALD},
    {"name": "Gila Monster Habitat", "lat": 33.0, "lon": -112.0,
     "type": "Fauna", "desert": "Sonoran",
     "description": "One of only two venomous lizards. Gila monster saliva inspired diabetes medication.",
     "species": "Heloderma suspectum", "color": ACCENT_RED},
    {"name": "Fennec Fox Range", "lat": 30.0, "lon": 5.0,
     "type": "Fauna", "desert": "Sahara",
     "description": "Smallest fox with largest ears relative to body — radiates heat to survive desert nights.",
     "species": "Vulpes zerda", "color": ACCENT_AMBER},
    {"name": "Thorny Devil Habitat", "lat": -25.0, "lon": 130.0,
     "type": "Fauna", "desert": "Central Australian",
     "description": "Lizard covered in thorny scales that channel dew to its mouth via capillary action.",
     "species": "Moloch horridus", "color": ACCENT_ORANGE},
    {"name": "Date Palm Groves (Al-Ahsa)", "lat": 25.38, "lon": 49.58,
     "type": "Flora", "desert": "Arabian",
     "description": "2.5 million date palms in the world's largest oasis — cultivated for 6,000 years.",
     "species": "Phoenix dactylifera", "color": ACCENT_EMERALD},
    {"name": "Desert Tortoise Range", "lat": 35.5, "lon": -116.0,
     "type": "Fauna", "desert": "Mojave/Sonoran",
     "description": "Can survive a year without water; spends 95% of its life in burrows.",
     "species": "Gopherus agassizii", "color": ACCENT_TEAL},
    {"name": "Addax Range (Sahara)", "lat": 20.0, "lon": 12.0,
     "type": "Fauna", "desert": "Sahara",
     "description": "Critically endangered antelope adapted to the deep Sahara — fewer than 100 in the wild.",
     "species": "Addax nasomaculatus", "color": ACCENT_RED},
    {"name": "Quiver Tree Forest", "lat": -28.77, "lon": 17.59,
     "type": "Flora", "desert": "Namib (Kalahari edge)",
     "description": "300-year-old aloe trees (kokerboom) in the Richtersveld, Namibia/South Africa border.",
     "species": "Aloidendron dichotomum", "color": ACCENT_EMERALD},
    {"name": "Sidewinder Rattlesnake Range", "lat": 34.0, "lon": -116.0,
     "type": "Fauna", "desert": "Mojave/Sonoran",
     "description": "Unique sidewinding locomotion for moving efficiently across hot sand.",
     "species": "Crotalus cerastes", "color": ACCENT_ORANGE},
    {"name": "Sand Cat Habitat", "lat": 28.0, "lon": 38.0,
     "type": "Fauna", "desert": "Sahara/Arabian",
     "description": "Smallest wild cat — fur-covered paws act as snowshoes for sand. Rarely seen.",
     "species": "Felis margarita", "color": ACCENT_PINK},
]

# ═══════════════════════════════════════════════════════════════
# MODE 8: SALT FLATS
# ═══════════════════════════════════════════════════════════════
SALT_FLATS = [
    {"name": "Salar de Uyuni", "lat": -20.13, "lon": -67.49, "country": "Bolivia",
     "area_km2": 10582, "elevation_m": 3656,
     "description": "Largest salt flat on Earth — 10 billion tonnes of salt. World's largest lithium reserve.",
     "color": ACCENT_CYAN},
    {"name": "Bonneville Salt Flats", "lat": 40.75, "lon": -113.88, "country": "USA",
     "area_km2": 260, "elevation_m": 1282,
     "description": "Famous for land speed records. Remnant of ancient Lake Bonneville.",
     "color": ACCENT_BLUE},
    {"name": "Etosha Pan", "lat": -18.81, "lon": 16.26, "country": "Namibia",
     "area_km2": 4760, "elevation_m": 1030,
     "description": "Dry salt pan visible from space. Seasonal flooding attracts massive wildlife gatherings.",
     "color": ACCENT_EMERALD},
    {"name": "Dasht-e Kavir (Great Salt Desert)", "lat": 34.5, "lon": 54.0, "country": "Iran",
     "area_km2": 77600, "elevation_m": 800,
     "description": "Vast salt desert in central Iran with treacherous salt crusts over mud.",
     "color": ACCENT_AMBER},
    {"name": "Chott el Jerid", "lat": 33.75, "lon": 8.4, "country": "Tunisia",
     "area_km2": 7000, "elevation_m": 15,
     "description": "Largest salt lake in the Sahara — Tatooine filming location for Star Wars.",
     "color": ACCENT_ORANGE},
    {"name": "Lake Eyre (Kati Thanda)", "lat": -28.37, "lon": 137.37, "country": "Australia",
     "area_km2": 9500, "elevation_m": -15,
     "description": "Lowest point in Australia. Fills once or twice a century to become a vast lake.",
     "color": ACCENT_RED},
    {"name": "Salar de Atacama", "lat": -23.50, "lon": -68.25, "country": "Chile",
     "area_km2": 3000, "elevation_m": 2300,
     "description": "Third largest salt flat, hosting flamingo populations and lithium mining.",
     "color": ACCENT_PINK},
    {"name": "Makgadikgadi Pans", "lat": -20.7, "lon": 25.2, "country": "Botswana",
     "area_km2": 16000, "elevation_m": 900,
     "description": "Among the largest salt flats in the world. Remnant of ancient mega-lake.",
     "color": ACCENT_TEAL},
    {"name": "Rann of Kutch", "lat": 23.9, "lon": 70.0, "country": "India",
     "area_km2": 30000, "elevation_m": 15,
     "description": "Seasonal salt marsh along the India-Pakistan border, largest of its kind.",
     "color": ACCENT_AMBER},
    {"name": "Death Valley (Badwater Basin)", "lat": 36.23, "lon": -116.77, "country": "USA",
     "area_km2": 518, "elevation_m": -86,
     "description": "Lowest point in North America (-86m). Hexagonal salt polygons on the basin floor.",
     "color": ACCENT_RED},
    {"name": "Lake Assal", "lat": 11.56, "lon": 42.42, "country": "Djibouti",
     "area_km2": 54, "elevation_m": -155,
     "description": "Lowest point in Africa, saltiest lake outside Antarctica. 10x saltier than the ocean.",
     "color": ACCENT_VIOLET},
    {"name": "Salar de Coipasa", "lat": -19.45, "lon": -68.13, "country": "Bolivia",
     "area_km2": 2218, "elevation_m": 3657,
     "description": "Second Bolivian salt flat, connected to Uyuni during wet season.",
     "color": ACCENT_CYAN},
    {"name": "Tuz Golu (Salt Lake)", "lat": 38.73, "lon": 33.38, "country": "Turkey",
     "area_km2": 1665, "elevation_m": 905,
     "description": "Turkey's second-largest lake and primary source of table salt.",
     "color": ACCENT_ORANGE},
    {"name": "Sabkha Matti", "lat": 23.0, "lon": 52.0, "country": "UAE/Saudi Arabia",
     "area_km2": 3200, "elevation_m": 10,
     "description": "Massive coastal sabkha (salt flat) at the southern edge of the Persian Gulf.",
     "color": ACCENT_AMBER},
]

# ═══════════════════════════════════════════════════════════════
# MODE 9: DESERT GEOLOGY
# ═══════════════════════════════════════════════════════════════
DESERT_GEOLOGY = [
    {"name": "Grand Canyon", "lat": 36.11, "lon": -112.11, "country": "USA",
     "feature_type": "Canyon", "age": "2 billion years (exposed strata)",
     "description": "Mile-deep canyon carved by the Colorado River exposing 2 billion years of Earth's history.",
     "color": ACCENT_RED},
    {"name": "Monument Valley", "lat": 36.99, "lon": -110.10, "country": "USA",
     "feature_type": "Buttes & Mesas", "age": "~270 million years (Permian)",
     "description": "Iconic sandstone buttes rising 300m from the desert floor — Navajo Nation.",
     "color": ACCENT_ORANGE},
    {"name": "Meteor Crater (Barringer)", "lat": 35.03, "lon": -111.02, "country": "USA",
     "feature_type": "Impact crater", "age": "~50,000 years",
     "description": "Best-preserved meteorite impact crater on Earth — 1.2km wide, 170m deep.",
     "color": ACCENT_AMBER},
    {"name": "White Sands", "lat": 32.78, "lon": -106.17, "country": "USA",
     "feature_type": "Gypsum dune field", "age": "~10,000 years",
     "description": "World's largest gypsum dune field — white sand from evaporated Lake Otero.",
     "color": ACCENT_CYAN},
    {"name": "Tassili n'Ajjer", "lat": 25.5, "lon": 9.0, "country": "Algeria",
     "feature_type": "Sandstone plateau", "age": "~500 million years",
     "description": "Eroded sandstone 'forest of rock' with 15,000+ prehistoric cave paintings.",
     "color": ACCENT_VIOLET},
    {"name": "Uluru (Ayers Rock)", "lat": -25.35, "lon": 131.04, "country": "Australia",
     "feature_type": "Inselberg", "age": "~550 million years (Cambrian)",
     "description": "World's largest sandstone monolith — 348m high, 9.4km circumference.",
     "color": ACCENT_RED},
    {"name": "Sossusvlei Dunes", "lat": -24.73, "lon": 15.29, "country": "Namibia",
     "feature_type": "Star dunes", "age": "~5 million years",
     "description": "Tallest sand dunes in the world (up to 325m), iron oxide gives the red color.",
     "color": ACCENT_ORANGE},
    {"name": "Wadi Rum Sandstone Pillars", "lat": 29.57, "lon": 35.42, "country": "Jordan",
     "feature_type": "Sandstone pillars & arches", "age": "~500 million years",
     "description": "Natural rock bridges and pillars in Jordan's Valley of the Moon.",
     "color": ACCENT_PINK},
    {"name": "Richat Structure (Eye of the Sahara)", "lat": 21.12, "lon": -11.40, "country": "Mauritania",
     "feature_type": "Eroded dome", "age": "~100 million years (Cretaceous)",
     "description": "50km diameter geological dome visible from space — once thought to be a crater.",
     "color": ACCENT_BLUE},
    {"name": "Bryce Canyon Hoodoos", "lat": 37.59, "lon": -112.19, "country": "USA",
     "feature_type": "Hoodoos (erosion pillars)", "age": "~50 million years (Eocene)",
     "description": "Thousands of red-orange hoodoo pillars carved by frost wedging.",
     "color": ACCENT_ORANGE},
    {"name": "Goblin Valley", "lat": 38.57, "lon": -110.71, "country": "USA",
     "feature_type": "Hoodoos & mushroom rocks", "age": "~170 million years (Jurassic)",
     "description": "Thousands of mushroom-shaped sandstone formations (goblins) in Utah.",
     "color": ACCENT_AMBER},
    {"name": "Ennedi Plateau", "lat": 17.0, "lon": 22.0, "country": "Chad",
     "feature_type": "Sandstone arches & pillars", "age": "~400 million years",
     "description": "Saharan plateau with natural arches, pillars, and prehistoric rock art.",
     "color": ACCENT_EMERALD},
    {"name": "Ship Rock (Tse Bit'a'i)", "lat": 36.69, "lon": -108.84, "country": "USA",
     "feature_type": "Volcanic neck", "age": "~27 million years",
     "description": "Sacred Navajo volcanic neck rising 480m with radiating dike walls.",
     "color": ACCENT_VIOLET},
    {"name": "Painted Desert", "lat": 35.07, "lon": -109.78, "country": "USA",
     "feature_type": "Badlands (Chinle Formation)", "age": "~225 million years (Triassic)",
     "description": "Layered sedimentary rocks in vibrant reds, purples, and grays.",
     "color": ACCENT_PINK},
    {"name": "Petrified Forest", "lat": 34.82, "lon": -109.89, "country": "USA",
     "feature_type": "Petrified wood", "age": "~225 million years (Triassic)",
     "description": "Fossilized trees turned to colorful quartz — over 200 tonnes of specimens.",
     "color": ACCENT_TEAL},
    {"name": "Gebel el-Silsila (Sandstone Quarries)", "lat": 24.63, "lon": 32.93, "country": "Egypt",
     "feature_type": "Sandstone narrows", "age": "~100 million years (Cretaceous)",
     "description": "Nile narrows through sandstone — ancient quarries that built Egyptian temples.",
     "color": ACCENT_AMBER},
    {"name": "Libyan Desert Glass Field", "lat": 25.35, "lon": 25.49, "country": "Egypt/Libya",
     "feature_type": "Impact glass", "age": "~29 million years",
     "description": "Mysterious yellow-green glass scattered across the desert — possible airburst or crater origin.",
     "color": ACCENT_CYAN},
    {"name": "Al Wahbah Crater", "lat": 22.91, "lon": 41.14, "country": "Saudi Arabia",
     "feature_type": "Maar (volcanic explosion crater)", "age": "~5,000 years",
     "description": "Volcanic explosion crater 250m deep, 2km wide, with white sodium phosphate floor.",
     "color": ACCENT_RED},
]

# ═══════════════════════════════════════════════════════════════
# MODE 10: DESERT EXPLORATION ROUTES
# ═══════════════════════════════════════════════════════════════
DESERT_EXPLORATION = [
    {"name": "Silk Road — Taklamakan Crossing", "lat": 39.0, "lon": 80.0,
     "era": "200 BC - 1400 AD", "explorer": "Zhang Qian, Marco Polo, Xuanzang",
     "description": "Northern and southern routes skirting the deadly Taklamakan. Many caravans lost forever.",
     "route_km": 3000, "color": ACCENT_AMBER},
    {"name": "Lawrence of Arabia — Aqaba Raid", "lat": 29.2, "lon": 35.8,
     "era": "1917", "explorer": "T.E. Lawrence",
     "description": "Lawrence led a 600-mile desert crossing from Wadi Rum to capture Aqaba from behind.",
     "route_km": 960, "color": ACCENT_ORANGE},
    {"name": "Trans-Saharan Caravan Route", "lat": 22.0, "lon": 2.0,
     "era": "8th - 19th century", "explorer": "Tuareg and Berber traders",
     "description": "Gold, salt, and slave trade routes from Timbuktu to Mediterranean ports.",
     "route_km": 2500, "color": ACCENT_AMBER},
    {"name": "Burke & Wills — Australian Interior", "lat": -28.0, "lon": 141.0,
     "era": "1860-1861", "explorer": "Robert Burke & William Wills",
     "description": "Ill-fated expedition to cross Australia south to north. Only one of four survived.",
     "route_km": 3250, "color": ACCENT_RED},
    {"name": "Freya Stark — Valley of the Assassins", "lat": 36.0, "lon": 50.5,
     "era": "1930s", "explorer": "Freya Stark",
     "description": "British explorer who mapped unmapped desert valleys in Persia and Arabia.",
     "route_km": 800, "color": ACCENT_PINK},
    {"name": "Wilfred Thesiger — Empty Quarter Crossing", "lat": 20.0, "lon": 50.0,
     "era": "1946-1948", "explorer": "Wilfred Thesiger",
     "description": "Two crossings of the Rub' al Khali by camel with Bedouin guides.",
     "route_km": 2000, "color": ACCENT_VIOLET},
    {"name": "Heinrich Barth — Sahara & Sahel", "lat": 16.0, "lon": 3.0,
     "era": "1850-1855", "explorer": "Heinrich Barth",
     "description": "Five-year journey mapping the Sahara and Sahel, reached Timbuktu.",
     "route_km": 20000, "color": ACCENT_CYAN},
    {"name": "Dakar Rally Route", "lat": 18.0, "lon": -5.0,
     "era": "1979-2007 (Africa)", "explorer": "Rally competitors",
     "description": "Paris-Dakar rally across the Sahara — 10,000km of the world's toughest motorsport.",
     "route_km": 10000, "color": ACCENT_RED},
    {"name": "Sven Hedin — Taklamakan Exploration", "lat": 38.0, "lon": 82.0,
     "era": "1893-1908", "explorer": "Sven Hedin",
     "description": "Swedish explorer who nearly died crossing the Taklamakan but discovered ancient cities.",
     "route_km": 5000, "color": ACCENT_BLUE},
    {"name": "Gertrude Bell — Arabian Expeditions", "lat": 30.0, "lon": 43.0,
     "era": "1900-1914", "explorer": "Gertrude Bell",
     "description": "Bell crossed the Syrian and Arabian deserts, mapped ruins, and shaped modern Iraq.",
     "route_km": 4000, "color": ACCENT_PINK},
    {"name": "Ibn Battuta — Saharan Crossing", "lat": 27.0, "lon": -3.0,
     "era": "1325-1354", "explorer": "Ibn Battuta",
     "description": "Moroccan scholar crossed the Sahara to reach Mali — part of his 120,000km journey.",
     "route_km": 2500, "color": ACCENT_EMERALD},
    {"name": "Great Indian Desert Survey", "lat": 27.0, "lon": 71.0,
     "era": "1870s", "explorer": "Survey of India",
     "description": "British surveyors mapped the Thar Desert — the Pundits used disguised instruments.",
     "route_km": 3000, "color": ACCENT_TEAL},
    {"name": "Almasy — Search for Zerzura", "lat": 23.5, "lon": 26.0,
     "era": "1930s", "explorer": "Laszlo Almasy",
     "description": "Hungarian explorer's search for the legendary lost oasis of Zerzura (The English Patient).",
     "route_km": 1500, "color": ACCENT_ORANGE},
    {"name": "Stuart — Central Australia Crossing", "lat": -23.0, "lon": 134.0,
     "era": "1861-1862", "explorer": "John McDouall Stuart",
     "description": "First successful south-to-north crossing of Australia through the Red Centre.",
     "route_km": 3200, "color": ACCENT_AMBER},
    {"name": "Incense Route — Negev to Gaza", "lat": 30.6, "lon": 34.8,
     "era": "7th century BC - 2nd century AD", "explorer": "Nabatean traders",
     "description": "Ancient trade route carrying frankincense from Arabia through the Negev desert.",
     "route_km": 2400, "color": ACCENT_VIOLET},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _build_folium_map(data: list, lat_key: str = "lat", lon_key: str = "lon",
                      popup_fields: list = None, name_key: str = "name",
                      zoom: int = 2, center_lat: float = 25.0,
                      center_lon: float = 20.0, use_cluster: bool = False) -> folium.Map:
    """Build a dark-themed Folium map with markers for the given data list."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=MAP_TILES,
        attr="CartoDB",
    )

    target = MarkerCluster().add_to(m) if use_cluster else m

    for item in data:
        lat = item.get(lat_key)
        lon = item.get(lon_key)
        if lat is None or lon is None:
            continue

        name = escape(str(item.get(name_key, "Unknown")))
        color = item.get("color", ACCENT_AMBER)

        # Build popup HTML
        popup_lines = [f"<b style='color:{color};font-size:14px'>{name}</b>"]
        if popup_fields:
            for field in popup_fields:
                val = item.get(field)
                if val is not None:
                    label = field.replace("_", " ").title()
                    popup_lines.append(
                        f"<br><b>{escape(label)}:</b> {escape(str(val))}"
                    )
        desc = item.get("description")
        if desc:
            popup_lines.append(
                f"<br><i style='color:#8b97b0'>{escape(desc)}</i>"
            )

        popup_html = (
            f"<div style='min-width:220px;max-width:320px;"
            f"background:#1a2235;color:#e8ecf4;padding:10px;"
            f"border-radius:8px;border:1px solid #2a3550;'>"
            f"{''.join(popup_lines)}</div>"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=name,
        ).add_to(target)

    return m


def _render_map(m: folium.Map, height: int = 500):
    """Render a Folium map in Streamlit."""
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
    """Render a row of st.metric cards. metrics = [(label, value), ...]"""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def _section_description(text: str):
    """Render a styled description paragraph."""
    st.markdown(
        f"<p style='color:{SECONDARY_TEXT};font-size:15px;margin-bottom:12px'>{text}</p>",
        unsafe_allow_html=True,
    )


def _bar_chart(labels: list, values: list, title: str, color: str = ACCENT_AMBER,
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


# ═══════════════════════════════════════════════════════════════
# MAP MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_great_deserts():
    """Mode 1: World's Great Deserts."""
    _section_description(
        "A comprehensive atlas of Earth's major deserts — from the scorching Sahara to the "
        "frozen Antarctic interior. Deserts cover about one-third of the planet's land surface "
        "and are defined by receiving less than 250mm of annual precipitation."
    )

    # Filter
    dtype = st.selectbox("Filter by type", ["All", "Subtropical", "Cold winter", "Coastal",
                                             "Cold coastal", "Polar"], key="desert_type_filter")
    if dtype == "All":
        filtered = GREAT_DESERTS
    else:
        filtered = [d for d in GREAT_DESERTS if d["type"] == dtype]

    total_area = sum(d["area_km2"] for d in filtered)
    hottest = max(filtered, key=lambda d: d["temperature_max_c"])
    driest = min(filtered, key=lambda d: d["annual_rain_mm"])

    _stats_row([
        ("Deserts Shown", len(filtered)),
        ("Total Area", f"{total_area:,.0f} km2"),
        ("Hottest", f"{hottest['name']} ({hottest['temperature_max_c']} C)"),
        ("Driest", f"{driest['name']} ({driest['annual_rain_mm']} mm/yr)"),
    ])

    # Map
    m = _build_folium_map(
        filtered,
        popup_fields=["type", "continent", "area_km2", "temperature_max_c", "annual_rain_mm"],
        zoom=2, center_lat=20, center_lon=20,
    )
    _render_map(m, height=520)

    # Chart — top 10 by area
    top10 = sorted(filtered, key=lambda d: d["area_km2"], reverse=True)[:12]
    _bar_chart(
        labels=[d["name"] for d in top10],
        values=[d["area_km2"] / 1_000_000 for d in top10],
        title="Largest Deserts by Area (million km2)",
        color=ACCENT_AMBER,
        ylabel="Area (million km2)",
        horizontal=True,
    )

    # Table
    df = _make_dataframe(filtered, ["name", "type", "continent", "area_km2",
                                     "temperature_max_c", "annual_rain_mm", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "great_deserts.csv", "Download Deserts CSV")


def _render_sand_seas():
    """Mode 2: Sand Seas (Ergs)."""
    _section_description(
        "Sand seas — known as ergs — are vast expanses of wind-sculpted dunes covering "
        "thousands of square kilometers. They contain some of Earth's tallest dunes and "
        "most alien landscapes, shaped over millions of years by persistent winds."
    )

    _stats_row([
        ("Sand Seas", len(SAND_SEAS)),
        ("Largest", "Rub' al Khali (650,000 km2)"),
        ("Tallest Dunes", "Badain Jaran (500m)"),
        ("Countries", f"{len(set(s['country'] for s in SAND_SEAS))}"),
    ])

    m = _build_folium_map(
        SAND_SEAS,
        popup_fields=["country", "area_km2", "dune_height_m"],
        zoom=2, center_lat=28, center_lon=30,
    )
    _render_map(m, height=520)

    # Chart — dune heights
    sorted_ergs = sorted(SAND_SEAS, key=lambda s: s["dune_height_m"], reverse=True)
    _bar_chart(
        labels=[s["name"] for s in sorted_ergs],
        values=[s["dune_height_m"] for s in sorted_ergs],
        title="Maximum Dune Height by Sand Sea (meters)",
        color=ACCENT_ORANGE,
        ylabel="Height (m)",
        horizontal=True,
    )

    df = _make_dataframe(SAND_SEAS, ["name", "country", "area_km2", "dune_height_m", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "sand_seas_ergs.csv", "Download Sand Seas CSV")


def _render_oases():
    """Mode 3: Oases."""
    _section_description(
        "Oases are fertile islands of life in the desert, sustained by underground water sources, "
        "springs, or ancient irrigation systems like qanats and foggaras. They have been vital "
        "stopping points on caravan routes for millennia."
    )

    total_pop = sum(o["population"] for o in OASES)
    water_sources = {}
    for o in OASES:
        src = o["water_source"].split("/")[0].split("(")[0].strip()
        water_sources[src] = water_sources.get(src, 0) + 1
    most_common_src = max(water_sources, key=water_sources.get)

    _stats_row([
        ("Oases", len(OASES)),
        ("Total Population", f"{total_pop:,.0f}"),
        ("Countries", f"{len(set(o['country'] for o in OASES))}"),
        ("Common Water Source", most_common_src),
    ])

    m = _build_folium_map(
        OASES,
        popup_fields=["country", "population", "water_source"],
        zoom=3, center_lat=28, center_lon=20,
    )
    _render_map(m, height=520)

    # Chart — population
    top_oases = sorted(OASES, key=lambda o: o["population"], reverse=True)[:12]
    _bar_chart(
        labels=[o["name"] for o in top_oases],
        values=[o["population"] / 1000 for o in top_oases],
        title="Oasis Population (thousands)",
        color=ACCENT_EMERALD,
        ylabel="Population (thousands)",
        horizontal=True,
    )

    df = _make_dataframe(OASES, ["name", "country", "population", "water_source", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "desert_oases.csv", "Download Oases CSV")


def _render_desert_cities():
    """Mode 4: Desert Cities."""
    _section_description(
        "Millions of people live in cities built in or on the edge of deserts. From ancient "
        "caravan hubs to modern megalopolises, these cities demonstrate humanity's ability "
        "to thrive in the harshest environments — often at enormous resource cost."
    )

    total_pop = sum(c["population"] for c in DESERT_CITIES)
    largest = max(DESERT_CITIES, key=lambda c: c["population"])
    countries = set(c["country"] for c in DESERT_CITIES)

    _stats_row([
        ("Cities", len(DESERT_CITIES)),
        ("Total Population", f"{total_pop / 1_000_000:.0f}M"),
        ("Largest", f"{largest['name']} ({largest['population'] / 1_000_000:.1f}M)"),
        ("Countries", len(countries)),
    ])

    m = _build_folium_map(
        DESERT_CITIES,
        popup_fields=["country", "population", "desert", "founded"],
        zoom=2, center_lat=25, center_lon=30,
    )
    _render_map(m, height=520)

    # Chart — population
    sorted_cities = sorted(DESERT_CITIES, key=lambda c: c["population"], reverse=True)
    _bar_chart(
        labels=[c["name"] for c in sorted_cities],
        values=[c["population"] / 1_000_000 for c in sorted_cities],
        title="Desert City Population (millions)",
        color=ACCENT_CYAN,
        ylabel="Population (millions)",
        horizontal=True,
    )

    df = _make_dataframe(DESERT_CITIES, ["name", "country", "population", "desert",
                                          "founded", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "desert_cities.csv", "Download Desert Cities CSV")


def _render_ancient_civilizations():
    """Mode 5: Ancient Desert Civilizations."""
    _section_description(
        "Deserts were not always barren — or their edges hosted some of history's greatest "
        "civilizations. From the Nabateans who carved Petra from living rock to the Ancestral "
        "Puebloans who built cities in canyon walls, these cultures mastered arid survival."
    )

    civs = set(c["civilization"] for c in ANCIENT_CIVILIZATIONS)
    oldest = min(ANCIENT_CIVILIZATIONS, key=lambda c: int(c["period"].split("-")[0].split()[0].replace("BC", "").replace("AD", "").strip()) * (-1 if "BC" in c["period"].split("-")[0] else 1))

    _stats_row([
        ("Sites", len(ANCIENT_CIVILIZATIONS)),
        ("Civilizations", len(civs)),
        ("Oldest Site", oldest["name"]),
        ("Span", "3800 BC - 1470 AD"),
    ])

    m = _build_folium_map(
        ANCIENT_CIVILIZATIONS,
        popup_fields=["civilization", "period"],
        zoom=2, center_lat=25, center_lon=40,
    )
    _render_map(m, height=520)

    # Civilization count chart
    civ_counts = {}
    for c in ANCIENT_CIVILIZATIONS:
        civ_counts[c["civilization"]] = civ_counts.get(c["civilization"], 0) + 1
    sorted_civs = sorted(civ_counts.items(), key=lambda x: x[1], reverse=True)
    _bar_chart(
        labels=[c[0] for c in sorted_civs],
        values=[c[1] for c in sorted_civs],
        title="Sites by Civilization",
        color=ACCENT_VIOLET,
        ylabel="Number of Sites",
        horizontal=True,
    )

    df = _make_dataframe(ANCIENT_CIVILIZATIONS, ["name", "civilization", "period", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "ancient_desert_civilizations.csv", "Download Civilizations CSV")


def _render_desertification():
    """Mode 6: Desertification Fronts."""
    _section_description(
        "Desertification — the degradation of dryland ecosystems — threatens 40% of the "
        "world's land area and directly affects 250 million people. Climate change, overgrazing, "
        "and unsustainable water use are accelerating the expansion of deserts worldwide."
    )

    total_affected = sum(d["area_affected_km2"] for d in DESERTIFICATION_FRONTS)
    critical_count = sum(1 for d in DESERTIFICATION_FRONTS if d["severity"] in ("Critical", "Catastrophic"))

    _stats_row([
        ("Fronts Tracked", len(DESERTIFICATION_FRONTS)),
        ("Total Area Affected", f"{total_affected / 1_000_000:.1f}M km2"),
        ("Critical/Catastrophic", critical_count),
        ("Regions", f"{len(set(d['region'] for d in DESERTIFICATION_FRONTS))}"),
    ])

    # Color by severity
    severity_colors = {
        "Critical": ACCENT_RED, "Catastrophic": "#dc2626",
        "Severe": ACCENT_ORANGE, "Moderate": ACCENT_AMBER, "Recovering": ACCENT_EMERALD
    }
    for d in DESERTIFICATION_FRONTS:
        d["color"] = severity_colors.get(d["severity"], ACCENT_AMBER)

    m = _build_folium_map(
        DESERTIFICATION_FRONTS,
        popup_fields=["region", "area_affected_km2", "severity"],
        zoom=2, center_lat=20, center_lon=30,
    )
    _render_map(m, height=520)

    # Area chart
    sorted_fronts = sorted(DESERTIFICATION_FRONTS, key=lambda d: d["area_affected_km2"], reverse=True)
    _bar_chart(
        labels=[d["name"][:30] for d in sorted_fronts],
        values=[d["area_affected_km2"] / 1_000_000 for d in sorted_fronts],
        title="Area Affected by Desertification (million km2)",
        color=ACCENT_RED,
        ylabel="Area (million km2)",
        horizontal=True,
    )

    df = _make_dataframe(DESERTIFICATION_FRONTS, ["name", "region", "area_affected_km2",
                                                    "severity", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "desertification_fronts.csv", "Download Desertification CSV")


def _render_flora_fauna():
    """Mode 7: Desert Flora & Fauna."""
    _section_description(
        "Deserts harbor extraordinary life adapted to extremes. From fog-harvesting beetles in "
        "the Namib to 200-year-old saguaro cacti in the Sonoran, desert organisms have evolved "
        "remarkable strategies for water conservation, heat management, and survival."
    )

    flora_count = sum(1 for f in DESERT_FLORA_FAUNA if f["type"] == "Flora")
    fauna_count = sum(1 for f in DESERT_FLORA_FAUNA if f["type"] == "Fauna")
    deserts = set(f["desert"] for f in DESERT_FLORA_FAUNA)

    type_filter = st.selectbox("Filter", ["All", "Flora", "Fauna"], key="ff_type_filter")
    if type_filter == "All":
        filtered = DESERT_FLORA_FAUNA
    else:
        filtered = [f for f in DESERT_FLORA_FAUNA if f["type"] == type_filter]

    _stats_row([
        ("Species Featured", len(filtered)),
        ("Flora", flora_count),
        ("Fauna", fauna_count),
        ("Deserts Represented", len(deserts)),
    ])

    m = _build_folium_map(
        filtered,
        popup_fields=["type", "desert", "species"],
        zoom=2, center_lat=20, center_lon=20,
    )
    _render_map(m, height=520)

    # By desert chart
    desert_counts = {}
    for f in filtered:
        desert_counts[f["desert"]] = desert_counts.get(f["desert"], 0) + 1
    sorted_deserts = sorted(desert_counts.items(), key=lambda x: x[1], reverse=True)
    _bar_chart(
        labels=[d[0] for d in sorted_deserts],
        values=[d[1] for d in sorted_deserts],
        title="Species by Desert Region",
        color=ACCENT_EMERALD,
        ylabel="Species Count",
        horizontal=True,
    )

    df = _make_dataframe(filtered, ["name", "type", "desert", "species", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "desert_flora_fauna.csv", "Download Flora & Fauna CSV")


def _render_salt_flats():
    """Mode 8: Salt Flats."""
    _section_description(
        "Salt flats — or playas — are stark white expanses left behind by evaporated lakes. "
        "From Bolivia's mirror-like Salar de Uyuni to Iran's treacherous Dasht-e Kavir, "
        "these geological features hold records for speed, beauty, and mineral wealth."
    )

    total_area = sum(s["area_km2"] for s in SALT_FLATS)
    lowest = min(SALT_FLATS, key=lambda s: s["elevation_m"])
    largest = max(SALT_FLATS, key=lambda s: s["area_km2"])

    _stats_row([
        ("Salt Flats", len(SALT_FLATS)),
        ("Total Area", f"{total_area:,.0f} km2"),
        ("Largest", f"{largest['name']} ({largest['area_km2']:,} km2)"),
        ("Lowest Point", f"{lowest['name']} ({lowest['elevation_m']}m)"),
    ])

    m = _build_folium_map(
        SALT_FLATS,
        popup_fields=["country", "area_km2", "elevation_m"],
        zoom=2, center_lat=15, center_lon=20,
    )
    _render_map(m, height=520)

    # Area chart
    sorted_flats = sorted(SALT_FLATS, key=lambda s: s["area_km2"], reverse=True)
    _bar_chart(
        labels=[s["name"] for s in sorted_flats],
        values=[s["area_km2"] for s in sorted_flats],
        title="Salt Flat Area (km2)",
        color=ACCENT_CYAN,
        ylabel="Area (km2)",
        horizontal=True,
    )

    df = _make_dataframe(SALT_FLATS, ["name", "country", "area_km2", "elevation_m", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "salt_flats.csv", "Download Salt Flats CSV")


def _render_desert_geology():
    """Mode 9: Desert Geology."""
    _section_description(
        "Desert erosion exposes Earth's geological history like nowhere else. Canyons, mesas, "
        "buttes, arches, volcanic necks, impact craters, and petrified forests reveal billions "
        "of years of planetary evolution in vivid color."
    )

    feature_types = {}
    for g in DESERT_GEOLOGY:
        ft = g["feature_type"]
        feature_types[ft] = feature_types.get(ft, 0) + 1
    countries = set(g["country"] for g in DESERT_GEOLOGY)

    _stats_row([
        ("Sites", len(DESERT_GEOLOGY)),
        ("Feature Types", len(feature_types)),
        ("Countries", len(countries)),
        ("Oldest Feature", "2 billion years"),
    ])

    m = _build_folium_map(
        DESERT_GEOLOGY,
        popup_fields=["country", "feature_type", "age"],
        zoom=2, center_lat=25, center_lon=20,
    )
    _render_map(m, height=520)

    # Feature type chart
    sorted_types = sorted(feature_types.items(), key=lambda x: x[1], reverse=True)
    _bar_chart(
        labels=[t[0] for t in sorted_types],
        values=[t[1] for t in sorted_types],
        title="Geological Features by Type",
        color=ACCENT_RED,
        ylabel="Count",
        horizontal=True,
    )

    df = _make_dataframe(DESERT_GEOLOGY, ["name", "country", "feature_type", "age", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "desert_geology.csv", "Download Desert Geology CSV")


def _render_desert_exploration():
    """Mode 10: Desert Exploration Routes."""
    _section_description(
        "For millennia, brave (or foolish) explorers have ventured into the world's deserts. "
        "From Silk Road caravans crossing the Taklamakan to T.E. Lawrence's desert raids, "
        "these routes trace the history of human courage, curiosity, and commerce."
    )

    total_km = sum(e["route_km"] for e in DESERT_EXPLORATION)
    longest = max(DESERT_EXPLORATION, key=lambda e: e["route_km"])
    explorers = set()
    for e in DESERT_EXPLORATION:
        for name in e["explorer"].split(","):
            explorers.add(name.strip())

    _stats_row([
        ("Routes", len(DESERT_EXPLORATION)),
        ("Total Distance", f"{total_km:,.0f} km"),
        ("Longest", f"{longest['name'][:25]}... ({longest['route_km']:,} km)"),
        ("Named Explorers", len(explorers)),
    ])

    m = _build_folium_map(
        DESERT_EXPLORATION,
        popup_fields=["era", "explorer", "route_km"],
        zoom=2, center_lat=25, center_lon=40,
    )
    _render_map(m, height=520)

    # Route distance chart
    sorted_routes = sorted(DESERT_EXPLORATION, key=lambda e: e["route_km"], reverse=True)
    _bar_chart(
        labels=[r["name"][:30] for r in sorted_routes],
        values=[r["route_km"] for r in sorted_routes],
        title="Exploration Route Distance (km)",
        color=ACCENT_AMBER,
        ylabel="Distance (km)",
        horizontal=True,
    )

    df = _make_dataframe(DESERT_EXPLORATION, ["name", "era", "explorer", "route_km", "description"])
    st.dataframe(df, width="stretch")
    _download_csv(df, "desert_exploration.csv", "Download Exploration Routes CSV")


# ═══════════════════════════════════════════════════════════════
# MAP MODE REGISTRY
# ═══════════════════════════════════════════════════════════════
MAP_MODES = {
    "World's Great Deserts": _render_great_deserts,
    "Sand Seas (Ergs)": _render_sand_seas,
    "Oases": _render_oases,
    "Desert Cities": _render_desert_cities,
    "Ancient Desert Civilizations": _render_ancient_civilizations,
    "Desertification Fronts": _render_desertification,
    "Desert Flora & Fauna": _render_flora_fauna,
    "Salt Flats": _render_salt_flats,
    "Desert Geology": _render_desert_geology,
    "Desert Exploration Routes": _render_desert_exploration,
}


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_desert_maps_tab():
    """Render the Deserts & Arid Landscapes tab for TerraScout AI."""

    # Tab header
    st.markdown(
        '<div class="tab-header amber"><h4>&#x1F3DC;&#xFE0F; Deserts &amp; Arid Landscapes</h4>'
        '<p>World deserts, oases, sand seas, dunes &amp; 10 maps</p></div>',
        unsafe_allow_html=True,
    )

    # Mode selector
    mode = st.selectbox(
        "Select Map Mode",
        list(MAP_MODES.keys()),
        key="desert_map_mode",
    )

    st.markdown("---")

    # Render selected mode
    MAP_MODES[mode]()
