# -*- coding: utf-8 -*-
"""
Extreme Geography module for TerraScout AI.
Hardcoded datasets of the world's most extreme geographical features:
highest peaks, deepest points, largest deserts, extreme temperatures,
longest rivers, largest lakes, largest islands, active volcanoes,
waterfalls, and geological formations.
"""

import io
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

# ═══════════════════════════════════════════════════════════════
# MAP TYPE DEFINITIONS
# ═══════════════════════════════════════════════════════════════
MAP_TYPES = [
    "Highest Peaks",
    "Deepest Points",
    "Largest Deserts",
    "Extreme Temperatures",
    "Longest Rivers",
    "Largest Lakes",
    "Largest Islands",
    "Active Volcanoes",
    "Waterfalls",
    "Geological Formations",
]

# ═══════════════════════════════════════════════════════════════
# 1. HIGHEST PEAKS (50+)
# ═══════════════════════════════════════════════════════════════
HIGHEST_PEAKS = [
    # 14 eight-thousanders
    {"name": "Mount Everest", "lat": 27.9881, "lon": 86.9250, "altitude_m": 8849, "range": "Himalayas", "country": "Nepal/China", "first_ascent": 1953},
    {"name": "K2", "lat": 35.8808, "lon": 76.5133, "altitude_m": 8611, "range": "Karakoram", "country": "Pakistan/China", "first_ascent": 1954},
    {"name": "Kangchenjunga", "lat": 27.7025, "lon": 88.1475, "altitude_m": 8586, "range": "Himalayas", "country": "Nepal/India", "first_ascent": 1955},
    {"name": "Lhotse", "lat": 27.9617, "lon": 86.9333, "altitude_m": 8516, "range": "Himalayas", "country": "Nepal/China", "first_ascent": 1956},
    {"name": "Makalu", "lat": 27.8897, "lon": 87.0886, "altitude_m": 8485, "range": "Himalayas", "country": "Nepal/China", "first_ascent": 1955},
    {"name": "Cho Oyu", "lat": 28.0942, "lon": 86.6608, "altitude_m": 8188, "range": "Himalayas", "country": "Nepal/China", "first_ascent": 1954},
    {"name": "Dhaulagiri I", "lat": 28.6967, "lon": 83.4875, "altitude_m": 8167, "range": "Himalayas", "country": "Nepal", "first_ascent": 1960},
    {"name": "Manaslu", "lat": 28.5497, "lon": 84.5597, "altitude_m": 8163, "range": "Himalayas", "country": "Nepal", "first_ascent": 1956},
    {"name": "Nanga Parbat", "lat": 35.2375, "lon": 74.5892, "altitude_m": 8126, "range": "Himalayas", "country": "Pakistan", "first_ascent": 1953},
    {"name": "Annapurna I", "lat": 28.5961, "lon": 83.8203, "altitude_m": 8091, "range": "Himalayas", "country": "Nepal", "first_ascent": 1950},
    {"name": "Gasherbrum I", "lat": 35.7244, "lon": 76.6961, "altitude_m": 8080, "range": "Karakoram", "country": "Pakistan/China", "first_ascent": 1958},
    {"name": "Broad Peak", "lat": 35.8117, "lon": 76.5653, "altitude_m": 8051, "range": "Karakoram", "country": "Pakistan/China", "first_ascent": 1957},
    {"name": "Gasherbrum II", "lat": 35.7583, "lon": 76.6533, "altitude_m": 8035, "range": "Karakoram", "country": "Pakistan/China", "first_ascent": 1956},
    {"name": "Shishapangma", "lat": 28.3528, "lon": 85.7797, "altitude_m": 8027, "range": "Himalayas", "country": "China", "first_ascent": 1964},
    # Continental high points
    {"name": "Aconcagua", "lat": -32.6532, "lon": -70.0109, "altitude_m": 6961, "range": "Andes", "country": "Argentina", "first_ascent": 1897},
    {"name": "Denali", "lat": 63.0695, "lon": -151.0074, "altitude_m": 6190, "range": "Alaska Range", "country": "USA", "first_ascent": 1913},
    {"name": "Mount Kilimanjaro", "lat": -3.0674, "lon": 37.3556, "altitude_m": 5895, "range": "Eastern Rift", "country": "Tanzania", "first_ascent": 1889},
    {"name": "Mount Elbrus", "lat": 43.3499, "lon": 42.4453, "altitude_m": 5642, "range": "Caucasus", "country": "Russia", "first_ascent": 1874},
    {"name": "Mount Vinson", "lat": -78.5254, "lon": -85.6172, "altitude_m": 4892, "range": "Sentinel Range", "country": "Antarctica", "first_ascent": 1966},
    {"name": "Puncak Jaya", "lat": -4.0833, "lon": 137.1833, "altitude_m": 4884, "range": "Sudirman Range", "country": "Indonesia", "first_ascent": 1962},
    {"name": "Mont Blanc", "lat": 45.8326, "lon": 6.8652, "altitude_m": 4809, "range": "Alps", "country": "France/Italy", "first_ascent": 1786},
    {"name": "Mount Kosciuszko", "lat": -36.4564, "lon": 148.2632, "altitude_m": 2228, "range": "Snowy Mountains", "country": "Australia", "first_ascent": 1840},
    # Other notable peaks
    {"name": "Gyachung Kang", "lat": 28.0978, "lon": 86.7422, "altitude_m": 7952, "range": "Himalayas", "country": "Nepal/China", "first_ascent": 1964},
    {"name": "Namcha Barwa", "lat": 29.6375, "lon": 95.1542, "altitude_m": 7782, "range": "Himalayas", "country": "China", "first_ascent": 1992},
    {"name": "Gurla Mandhata", "lat": 30.4333, "lon": 81.2833, "altitude_m": 7694, "range": "Himalayas", "country": "China", "first_ascent": 1985},
    {"name": "Tirich Mir", "lat": 36.2525, "lon": 71.8506, "altitude_m": 7708, "range": "Hindu Kush", "country": "Pakistan", "first_ascent": 1950},
    {"name": "Kongur Tagh", "lat": 38.5883, "lon": 75.3117, "altitude_m": 7649, "range": "Kunlun", "country": "China", "first_ascent": 1981},
    {"name": "Muztagh Ata", "lat": 38.2833, "lon": 75.1167, "altitude_m": 7509, "range": "Kunlun", "country": "China", "first_ascent": 1956},
    {"name": "Communism Peak", "lat": 38.9411, "lon": 72.0139, "altitude_m": 7495, "range": "Pamir", "country": "Tajikistan", "first_ascent": 1933},
    {"name": "Pobeda Peak", "lat": 42.0344, "lon": 80.1278, "altitude_m": 7439, "range": "Tien Shan", "country": "Kyrgyzstan/China", "first_ascent": 1956},
    {"name": "Cerro Ojos del Salado", "lat": -27.1092, "lon": -68.5414, "altitude_m": 6893, "range": "Andes", "country": "Chile/Argentina", "first_ascent": 1937},
    {"name": "Huascaran", "lat": -9.1222, "lon": -77.6042, "altitude_m": 6768, "range": "Andes", "country": "Peru", "first_ascent": 1932},
    {"name": "Illimani", "lat": -16.6533, "lon": -67.7847, "altitude_m": 6438, "range": "Andes", "country": "Bolivia", "first_ascent": 1898},
    {"name": "Chimborazo", "lat": -1.4692, "lon": -78.8175, "altitude_m": 6263, "range": "Andes", "country": "Ecuador", "first_ascent": 1880},
    {"name": "Mount Logan", "lat": 60.5667, "lon": -140.4056, "altitude_m": 5959, "range": "Saint Elias", "country": "Canada", "first_ascent": 1925},
    {"name": "Cotopaxi", "lat": -0.6836, "lon": -78.4378, "altitude_m": 5897, "range": "Andes", "country": "Ecuador", "first_ascent": 1872},
    {"name": "Mount Kenya", "lat": -0.1521, "lon": 37.3083, "altitude_m": 5199, "range": "Eastern Rift", "country": "Kenya", "first_ascent": 1899},
    {"name": "Mount Stanley", "lat": 0.3858, "lon": 29.8722, "altitude_m": 5109, "range": "Rwenzori", "country": "DR Congo/Uganda", "first_ascent": 1906},
    {"name": "Mount Ararat", "lat": 39.7019, "lon": 44.2983, "altitude_m": 5137, "range": "Armenian Highlands", "country": "Turkey", "first_ascent": 1829},
    {"name": "Mount Damavand", "lat": 35.9514, "lon": 52.1089, "altitude_m": 5610, "range": "Alborz", "country": "Iran", "first_ascent": 1837},
    {"name": "Mount Rainier", "lat": 46.8523, "lon": -121.7603, "altitude_m": 4392, "range": "Cascades", "country": "USA", "first_ascent": 1870},
    {"name": "Matterhorn", "lat": 45.9764, "lon": 7.6586, "altitude_m": 4478, "range": "Alps", "country": "Switzerland/Italy", "first_ascent": 1865},
    {"name": "Mount Whitney", "lat": 36.5785, "lon": -118.2923, "altitude_m": 4421, "range": "Sierra Nevada", "country": "USA", "first_ascent": 1873},
    {"name": "Jungfrau", "lat": 46.5367, "lon": 7.9614, "altitude_m": 4158, "range": "Alps", "country": "Switzerland", "first_ascent": 1811},
    {"name": "Mount Olympus", "lat": 40.0859, "lon": 22.3583, "altitude_m": 2917, "range": "Olympus Range", "country": "Greece", "first_ascent": 1913},
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274, "altitude_m": 3776, "range": "Fuji Volcanic Zone", "country": "Japan", "first_ascent": 663},
    {"name": "Mount Cook / Aoraki", "lat": -43.5950, "lon": 170.1418, "altitude_m": 3724, "range": "Southern Alps", "country": "New Zealand", "first_ascent": 1894},
    {"name": "Teide", "lat": 28.2723, "lon": -16.6424, "altitude_m": 3718, "range": "Canary Islands", "country": "Spain", "first_ascent": 1582},
    {"name": "Mount Erebus", "lat": -77.5278, "lon": 167.1531, "altitude_m": 3794, "range": "Ross Island", "country": "Antarctica", "first_ascent": 1908},
    {"name": "Pico de Orizaba", "lat": 19.0303, "lon": -97.2686, "altitude_m": 5636, "range": "Trans-Mexican", "country": "Mexico", "first_ascent": 1848},
    {"name": "Mount Elbrus (W)", "lat": 43.3556, "lon": 42.4392, "altitude_m": 5642, "range": "Caucasus", "country": "Russia", "first_ascent": 1874},
]

# ═══════════════════════════════════════════════════════════════
# 2. DEEPEST POINTS
# ═══════════════════════════════════════════════════════════════
DEEPEST_POINTS = [
    # Ocean trenches
    {"name": "Challenger Deep (Mariana Trench)", "lat": 11.3493, "lon": 142.1996, "depth_m": -10994, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Tonga Trench", "lat": -23.25, "lon": -174.72, "depth_m": -10882, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Galathea Depth (Philippine Trench)", "lat": 7.50, "lon": 126.58, "depth_m": -10540, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Kuril-Kamchatka Trench", "lat": 44.00, "lon": 150.50, "depth_m": -10542, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Kermadec Trench", "lat": -30.00, "lon": -176.50, "depth_m": -10047, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Izu-Bonin Trench", "lat": 29.50, "lon": 142.75, "depth_m": -9810, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Japan Trench", "lat": 36.00, "lon": 143.00, "depth_m": -8412, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Puerto Rico Trench", "lat": 19.72, "lon": -67.00, "depth_m": -8376, "type": "Ocean Trench", "body": "Atlantic Ocean"},
    {"name": "South Sandwich Trench", "lat": -55.00, "lon": -26.00, "depth_m": -8264, "type": "Ocean Trench", "body": "Atlantic Ocean"},
    {"name": "Peru-Chile Trench", "lat": -23.35, "lon": -71.37, "depth_m": -8065, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Aleutian Trench", "lat": 51.00, "lon": -177.00, "depth_m": -7679, "type": "Ocean Trench", "body": "Pacific Ocean"},
    {"name": "Java Trench (Sunda Trench)", "lat": -10.19, "lon": 109.58, "depth_m": -7725, "type": "Ocean Trench", "body": "Indian Ocean"},
    {"name": "Cayman Trough", "lat": 19.20, "lon": -80.00, "depth_m": -7686, "type": "Ocean Trench", "body": "Caribbean Sea"},
    {"name": "Romanche Trench", "lat": -0.30, "lon": -18.50, "depth_m": -7758, "type": "Ocean Trench", "body": "Atlantic Ocean"},
    # Deepest lakes
    {"name": "Lake Baikal", "lat": 53.5587, "lon": 108.1650, "depth_m": -1642, "type": "Lake", "body": "Russia"},
    {"name": "Lake Tanganyika", "lat": -6.30, "lon": 29.50, "depth_m": -1470, "type": "Lake", "body": "Africa"},
    {"name": "Caspian Sea", "lat": 41.94, "lon": 50.67, "depth_m": -1025, "type": "Lake", "body": "Asia"},
    {"name": "Lake Vostok", "lat": -77.50, "lon": 106.00, "depth_m": -900, "type": "Sub-glacial Lake", "body": "Antarctica"},
    {"name": "Lake Malawi", "lat": -12.17, "lon": 34.58, "depth_m": -706, "type": "Lake", "body": "Africa"},
    {"name": "Lake Issyk-Kul", "lat": 42.45, "lon": 77.25, "depth_m": -668, "type": "Lake", "body": "Kyrgyzstan"},
    {"name": "Great Slave Lake", "lat": 61.67, "lon": -114.00, "depth_m": -614, "type": "Lake", "body": "Canada"},
    {"name": "Crater Lake", "lat": 42.9446, "lon": -122.1090, "depth_m": -594, "type": "Lake", "body": "USA"},
    # Deepest caves
    {"name": "Veryovkina Cave", "lat": 43.41, "lon": 40.36, "depth_m": -2212, "type": "Cave", "body": "Georgia"},
    {"name": "Krubera Cave", "lat": 43.41, "lon": 40.31, "depth_m": -2197, "type": "Cave", "body": "Georgia"},
    {"name": "Sarma Cave", "lat": 43.38, "lon": 40.38, "depth_m": -1830, "type": "Cave", "body": "Georgia"},
    {"name": "Snezhnaya Cave", "lat": 43.40, "lon": 40.37, "depth_m": -1760, "type": "Cave", "body": "Georgia"},
    {"name": "Lamprechtsofen", "lat": 47.52, "lon": 12.83, "depth_m": -1735, "type": "Cave", "body": "Austria"},
    {"name": "Gouffre Mirolda", "lat": 46.08, "lon": 6.77, "depth_m": -1733, "type": "Cave", "body": "France"},
    {"name": "Reseau Jean-Bernard", "lat": 46.08, "lon": 6.75, "depth_m": -1602, "type": "Cave", "body": "France"},
    {"name": "Dead Sea Depression", "lat": 31.50, "lon": 35.50, "depth_m": -430, "type": "Land Depression", "body": "Israel/Jordan"},
]

# ═══════════════════════════════════════════════════════════════
# 3. LARGEST DESERTS (15)
# ═══════════════════════════════════════════════════════════════
LARGEST_DESERTS = [
    {"name": "Antarctic Desert", "lat": -82.86, "lon": 55.00, "area_km2": 14200000, "type": "Cold", "continent": "Antarctica"},
    {"name": "Arctic Desert", "lat": 75.00, "lon": 40.00, "area_km2": 13900000, "type": "Cold", "continent": "Arctic"},
    {"name": "Sahara Desert", "lat": 23.42, "lon": 12.00, "area_km2": 9200000, "type": "Hot", "continent": "Africa"},
    {"name": "Arabian Desert", "lat": 23.00, "lon": 46.00, "area_km2": 2330000, "type": "Hot", "continent": "Asia"},
    {"name": "Gobi Desert", "lat": 42.50, "lon": 103.00, "area_km2": 1295000, "type": "Cold", "continent": "Asia"},
    {"name": "Kalahari Desert", "lat": -23.50, "lon": 22.00, "area_km2": 900000, "type": "Hot", "continent": "Africa"},
    {"name": "Patagonian Desert", "lat": -47.00, "lon": -68.00, "area_km2": 673000, "type": "Cold", "continent": "South America"},
    {"name": "Great Victoria Desert", "lat": -29.00, "lon": 129.00, "area_km2": 647000, "type": "Hot", "continent": "Australia"},
    {"name": "Syrian Desert", "lat": 33.00, "lon": 39.00, "area_km2": 500000, "type": "Hot", "continent": "Asia"},
    {"name": "Great Basin Desert", "lat": 40.00, "lon": -117.00, "area_km2": 492000, "type": "Cold", "continent": "North America"},
    {"name": "Chihuahuan Desert", "lat": 30.00, "lon": -106.00, "area_km2": 453000, "type": "Hot", "continent": "North America"},
    {"name": "Karakum Desert", "lat": 38.50, "lon": 58.50, "area_km2": 350000, "type": "Cold", "continent": "Asia"},
    {"name": "Colorado Plateau Desert", "lat": 36.50, "lon": -111.00, "area_km2": 337000, "type": "Cold", "continent": "North America"},
    {"name": "Sonoran Desert", "lat": 32.00, "lon": -113.00, "area_km2": 310000, "type": "Hot", "continent": "North America"},
    {"name": "Thar Desert", "lat": 27.00, "lon": 71.00, "area_km2": 200000, "type": "Hot", "continent": "Asia"},
]

# ═══════════════════════════════════════════════════════════════
# 4. EXTREME TEMPERATURES
# ═══════════════════════════════════════════════════════════════
EXTREME_TEMPERATURES = [
    # Hottest places
    {"name": "Death Valley, USA", "lat": 36.2500, "lon": -116.8250, "record_c": 56.7, "category": "Hottest", "detail": "World record: 10 Jul 1913"},
    {"name": "Kebili, Tunisia", "lat": 33.7072, "lon": 8.9650, "record_c": 55.0, "category": "Hottest", "detail": "Record: 7 Jul 1931"},
    {"name": "Tirat Zvi, Israel", "lat": 32.4200, "lon": -35.5300, "record_c": 54.0, "category": "Hottest", "detail": "Record: 21 Jun 1942"},
    {"name": "Ahvaz, Iran", "lat": 31.3203, "lon": 48.6693, "record_c": 54.0, "category": "Hottest", "detail": "Record: 29 Jun 2017"},
    {"name": "Mitribah, Kuwait", "lat": 29.7758, "lon": 47.6422, "record_c": 53.9, "category": "Hottest", "detail": "Record: 21 Jul 2016"},
    {"name": "Turbat, Pakistan", "lat": 26.0017, "lon": 63.0500, "record_c": 53.7, "category": "Hottest", "detail": "Record: 28 May 2017"},
    {"name": "Dallol, Ethiopia", "lat": 14.2422, "lon": 40.2972, "record_c": 41.0, "category": "Hottest (avg)", "detail": "Highest avg annual temp: 41C"},
    {"name": "Wadi Halfa, Sudan", "lat": 21.8000, "lon": 31.3500, "record_c": 52.8, "category": "Hottest", "detail": "Record observed"},
    # Coldest places
    {"name": "Vostok Station, Antarctica", "lat": -78.4645, "lon": 106.8340, "record_c": -89.2, "category": "Coldest", "detail": "World record: 21 Jul 1983"},
    {"name": "Dome A, Antarctica", "lat": -80.3670, "lon": 77.3520, "record_c": -82.5, "category": "Coldest", "detail": "Satellite measured"},
    {"name": "Dome Fuji, Antarctica", "lat": -77.3167, "lon": 39.7000, "record_c": -79.6, "category": "Coldest", "detail": "Record: 3 Aug 2004"},
    {"name": "Amundsen-Scott Station", "lat": -90.0000, "lon": 0.0000, "record_c": -82.8, "category": "Coldest", "detail": "South Pole station"},
    {"name": "Oymyakon, Russia", "lat": 63.4641, "lon": 142.7737, "record_c": -67.7, "category": "Coldest (inhabited)", "detail": "Coldest inhabited place: 6 Feb 1933"},
    {"name": "Verkhoyansk, Russia", "lat": 67.5536, "lon": 133.3928, "record_c": -67.8, "category": "Coldest (inhabited)", "detail": "Record: 15 Jan 1885"},
    {"name": "Snag, Yukon, Canada", "lat": 62.3833, "lon": -140.4000, "record_c": -63.0, "category": "Coldest (N. America)", "detail": "Record: 3 Feb 1947"},
    {"name": "Prospect Creek, Alaska", "lat": 66.1333, "lon": -150.6833, "record_c": -62.2, "category": "Coldest (USA)", "detail": "Record: 23 Jan 1971"},
    # Wettest places
    {"name": "Mawsynram, India", "lat": 25.2972, "lon": 91.5822, "record_c": 11871, "category": "Wettest (mm/yr)", "detail": "Avg 11,871 mm/year rainfall"},
    {"name": "Cherrapunji, India", "lat": 25.2700, "lon": 91.7314, "record_c": 11430, "category": "Wettest (mm/yr)", "detail": "Avg 11,430 mm/year rainfall"},
    {"name": "Tutunendo, Colombia", "lat": 5.7500, "lon": -76.5333, "record_c": 11770, "category": "Wettest (mm/yr)", "detail": "Avg 11,770 mm/year rainfall"},
    {"name": "Mount Waialeale, Hawaii", "lat": 22.0667, "lon": -159.4833, "record_c": 9763, "category": "Wettest (mm/yr)", "detail": "Avg 9,763 mm/year rainfall"},
    # Driest places
    {"name": "Atacama Desert, Chile", "lat": -24.5000, "lon": -69.2500, "record_c": 0, "category": "Driest", "detail": "Some spots: 0 mm rainfall ever recorded"},
    {"name": "Dry Valleys, Antarctica", "lat": -77.5000, "lon": 162.0000, "record_c": 0, "category": "Driest", "detail": "No precipitation for 2 million years"},
    {"name": "Arica, Chile", "lat": -18.4746, "lon": -70.3114, "record_c": 0.8, "category": "Driest (town)", "detail": "Avg 0.8 mm/year rainfall"},
    {"name": "Aswan, Egypt", "lat": 24.0889, "lon": 32.8998, "record_c": 0.9, "category": "Driest", "detail": "Avg 0.9 mm/year rainfall"},
]

# ═══════════════════════════════════════════════════════════════
# 5. LONGEST RIVERS (25+)
# ═══════════════════════════════════════════════════════════════
LONGEST_RIVERS = [
    {"name": "Nile", "lat": 30.0444, "lon": 31.2357, "length_km": 6650, "discharge_m3s": 2830, "basin_km2": 3349000, "continent": "Africa"},
    {"name": "Amazon", "lat": -3.1190, "lon": -60.0217, "length_km": 6400, "discharge_m3s": 209000, "basin_km2": 7050000, "continent": "South America"},
    {"name": "Yangtze", "lat": 31.2304, "lon": 121.4737, "length_km": 6300, "discharge_m3s": 30166, "basin_km2": 1800000, "continent": "Asia"},
    {"name": "Mississippi-Missouri", "lat": 29.9511, "lon": -90.0715, "length_km": 6275, "discharge_m3s": 16800, "basin_km2": 2981000, "continent": "North America"},
    {"name": "Yenisei-Angara", "lat": 71.8333, "lon": 82.6667, "length_km": 5539, "discharge_m3s": 19600, "basin_km2": 2580000, "continent": "Asia"},
    {"name": "Yellow River (Huang He)", "lat": 37.7750, "lon": 119.1625, "length_km": 5464, "discharge_m3s": 2571, "basin_km2": 752000, "continent": "Asia"},
    {"name": "Ob-Irtysh", "lat": 66.5333, "lon": 66.6000, "length_km": 5410, "discharge_m3s": 12475, "basin_km2": 2990000, "continent": "Asia"},
    {"name": "Parana", "lat": -33.9425, "lon": -59.1000, "length_km": 4880, "discharge_m3s": 17290, "basin_km2": 2583000, "continent": "South America"},
    {"name": "Congo", "lat": -4.3050, "lon": 15.2875, "length_km": 4700, "discharge_m3s": 41000, "basin_km2": 3680000, "continent": "Africa"},
    {"name": "Amur", "lat": 52.9333, "lon": 141.1667, "length_km": 4444, "discharge_m3s": 11400, "basin_km2": 1855000, "continent": "Asia"},
    {"name": "Lena", "lat": 72.4000, "lon": 126.6667, "length_km": 4400, "discharge_m3s": 17100, "basin_km2": 2490000, "continent": "Asia"},
    {"name": "Mekong", "lat": 9.7890, "lon": 106.7010, "length_km": 4350, "discharge_m3s": 16000, "basin_km2": 795000, "continent": "Asia"},
    {"name": "Mackenzie", "lat": 69.0833, "lon": -136.0000, "length_km": 4241, "discharge_m3s": 10300, "basin_km2": 1805000, "continent": "North America"},
    {"name": "Niger", "lat": 5.3167, "lon": 6.4667, "length_km": 4200, "discharge_m3s": 9570, "basin_km2": 2090000, "continent": "Africa"},
    {"name": "Murray-Darling", "lat": -35.3975, "lon": 139.0661, "length_km": 3672, "discharge_m3s": 767, "basin_km2": 1061000, "continent": "Australia"},
    {"name": "Volga", "lat": 46.3500, "lon": 48.5333, "length_km": 3531, "discharge_m3s": 8060, "basin_km2": 1380000, "continent": "Europe"},
    {"name": "Zambezi", "lat": -18.5667, "lon": 36.1333, "length_km": 3540, "discharge_m3s": 3400, "basin_km2": 1390000, "continent": "Africa"},
    {"name": "Madeira", "lat": -3.3833, "lon": -58.7833, "length_km": 3380, "discharge_m3s": 31200, "basin_km2": 1485000, "continent": "South America"},
    {"name": "Danube", "lat": 45.2167, "lon": 29.7500, "length_km": 2860, "discharge_m3s": 6500, "basin_km2": 817000, "continent": "Europe"},
    {"name": "Ganges", "lat": 22.0833, "lon": 90.7500, "length_km": 2525, "discharge_m3s": 38000, "basin_km2": 1080000, "continent": "Asia"},
    {"name": "Indus", "lat": 23.9833, "lon": 67.4667, "length_km": 3180, "discharge_m3s": 7160, "basin_km2": 1165000, "continent": "Asia"},
    {"name": "Brahmaputra", "lat": 25.2000, "lon": 89.7000, "length_km": 2900, "discharge_m3s": 19800, "basin_km2": 651000, "continent": "Asia"},
    {"name": "Euphrates", "lat": 31.0000, "lon": 47.4167, "length_km": 2800, "discharge_m3s": 856, "basin_km2": 500000, "continent": "Asia"},
    {"name": "Colorado", "lat": 31.9000, "lon": -114.9500, "length_km": 2330, "discharge_m3s": 640, "basin_km2": 637000, "continent": "North America"},
    {"name": "Rhine", "lat": 51.8833, "lon": 6.9333, "length_km": 1230, "discharge_m3s": 2300, "basin_km2": 185000, "continent": "Europe"},
    {"name": "Orange River", "lat": -28.6333, "lon": 16.4500, "length_km": 2200, "discharge_m3s": 365, "basin_km2": 973000, "continent": "Africa"},
]

# ═══════════════════════════════════════════════════════════════
# 6. LARGEST LAKES (25+)
# ═══════════════════════════════════════════════════════════════
LARGEST_LAKES = [
    {"name": "Caspian Sea", "lat": 41.94, "lon": 50.67, "area_km2": 371000, "max_depth_m": 1025, "volume_km3": 78200, "continent": "Asia/Europe"},
    {"name": "Lake Superior", "lat": 47.70, "lon": -87.50, "area_km2": 82100, "max_depth_m": 406, "volume_km3": 12100, "continent": "North America"},
    {"name": "Lake Victoria", "lat": -1.00, "lon": 33.00, "area_km2": 68870, "max_depth_m": 84, "volume_km3": 2760, "continent": "Africa"},
    {"name": "Lake Huron", "lat": 44.80, "lon": -82.40, "area_km2": 59600, "max_depth_m": 229, "volume_km3": 3540, "continent": "North America"},
    {"name": "Lake Michigan", "lat": 43.80, "lon": -87.00, "area_km2": 57800, "max_depth_m": 282, "volume_km3": 4920, "continent": "North America"},
    {"name": "Lake Tanganyika", "lat": -6.30, "lon": 29.50, "area_km2": 32900, "max_depth_m": 1470, "volume_km3": 18900, "continent": "Africa"},
    {"name": "Lake Baikal", "lat": 53.56, "lon": 108.17, "area_km2": 31722, "max_depth_m": 1642, "volume_km3": 23615, "continent": "Asia"},
    {"name": "Great Bear Lake", "lat": 66.08, "lon": -121.00, "area_km2": 31153, "max_depth_m": 446, "volume_km3": 2236, "continent": "North America"},
    {"name": "Lake Malawi", "lat": -12.17, "lon": 34.58, "area_km2": 29600, "max_depth_m": 706, "volume_km3": 8400, "continent": "Africa"},
    {"name": "Great Slave Lake", "lat": 61.67, "lon": -114.00, "area_km2": 27200, "max_depth_m": 614, "volume_km3": 2090, "continent": "North America"},
    {"name": "Lake Erie", "lat": 42.20, "lon": -81.20, "area_km2": 25700, "max_depth_m": 64, "volume_km3": 484, "continent": "North America"},
    {"name": "Lake Winnipeg", "lat": 52.12, "lon": -97.25, "area_km2": 24514, "max_depth_m": 36, "volume_km3": 283, "continent": "North America"},
    {"name": "Lake Ontario", "lat": 43.70, "lon": -77.90, "area_km2": 19009, "max_depth_m": 244, "volume_km3": 1640, "continent": "North America"},
    {"name": "Lake Balkhash", "lat": 46.58, "lon": 74.33, "area_km2": 18200, "max_depth_m": 26, "volume_km3": 106, "continent": "Asia"},
    {"name": "Lake Ladoga", "lat": 61.00, "lon": 31.50, "area_km2": 17700, "max_depth_m": 230, "volume_km3": 837, "continent": "Europe"},
    {"name": "Lake Titicaca", "lat": -15.83, "lon": -69.33, "area_km2": 8372, "max_depth_m": 281, "volume_km3": 893, "continent": "South America"},
    {"name": "Lake Onega", "lat": 61.50, "lon": 35.50, "area_km2": 9700, "max_depth_m": 127, "volume_km3": 292, "continent": "Europe"},
    {"name": "Lake Chad", "lat": 13.50, "lon": 14.50, "area_km2": 1350, "max_depth_m": 11, "volume_km3": 72, "continent": "Africa"},
    {"name": "Lake Turkana", "lat": 3.58, "lon": 36.08, "area_km2": 6405, "max_depth_m": 109, "volume_km3": 204, "continent": "Africa"},
    {"name": "Lake Issyk-Kul", "lat": 42.45, "lon": 77.25, "area_km2": 6236, "max_depth_m": 668, "volume_km3": 1738, "continent": "Asia"},
    {"name": "Lake Nicaragua", "lat": 11.50, "lon": -85.50, "area_km2": 8264, "max_depth_m": 26, "volume_km3": 108, "continent": "Central America"},
    {"name": "Lake Athabasca", "lat": 59.17, "lon": -109.42, "area_km2": 7935, "max_depth_m": 124, "volume_km3": 204, "continent": "North America"},
    {"name": "Aral Sea (remnant)", "lat": 45.00, "lon": 59.00, "area_km2": 8300, "max_depth_m": 42, "volume_km3": 75, "continent": "Asia"},
    {"name": "Lake Vostok", "lat": -77.50, "lon": 106.00, "area_km2": 12500, "max_depth_m": 900, "volume_km3": 5400, "continent": "Antarctica"},
    {"name": "Crater Lake", "lat": 42.94, "lon": -122.11, "area_km2": 53, "max_depth_m": 594, "volume_km3": 19, "continent": "North America"},
    {"name": "Lake Toba", "lat": 2.62, "lon": 98.83, "area_km2": 1130, "max_depth_m": 505, "volume_km3": 240, "continent": "Asia"},
]

# ═══════════════════════════════════════════════════════════════
# 7. LARGEST ISLANDS (25+)
# ═══════════════════════════════════════════════════════════════
LARGEST_ISLANDS = [
    {"name": "Greenland", "lat": 71.71, "lon": -42.60, "area_km2": 2166086, "population": 56081, "country": "Denmark"},
    {"name": "New Guinea", "lat": -5.00, "lon": 141.00, "area_km2": 786380, "population": 12000000, "country": "Indonesia/PNG"},
    {"name": "Borneo", "lat": 1.00, "lon": 114.00, "area_km2": 748168, "population": 21300000, "country": "Indonesia/Malaysia/Brunei"},
    {"name": "Madagascar", "lat": -18.77, "lon": 46.87, "area_km2": 587041, "population": 28400000, "country": "Madagascar"},
    {"name": "Baffin Island", "lat": 68.00, "lon": -70.00, "area_km2": 507451, "population": 13000, "country": "Canada"},
    {"name": "Sumatra", "lat": 0.00, "lon": 102.00, "area_km2": 473481, "population": 50000000, "country": "Indonesia"},
    {"name": "Honshu", "lat": 36.00, "lon": 138.00, "area_km2": 227960, "population": 103000000, "country": "Japan"},
    {"name": "Great Britain", "lat": 54.00, "lon": -2.00, "area_km2": 209331, "population": 65000000, "country": "United Kingdom"},
    {"name": "Victoria Island", "lat": 71.00, "lon": -110.00, "area_km2": 217291, "population": 1875, "country": "Canada"},
    {"name": "Ellesmere Island", "lat": 80.00, "lon": -80.00, "area_km2": 196236, "population": 146, "country": "Canada"},
    {"name": "Celebes (Sulawesi)", "lat": -2.00, "lon": 121.00, "area_km2": 180681, "population": 19000000, "country": "Indonesia"},
    {"name": "South Island (NZ)", "lat": -44.00, "lon": 170.00, "area_km2": 150437, "population": 1200000, "country": "New Zealand"},
    {"name": "Java", "lat": -7.50, "lon": 110.00, "area_km2": 129000, "population": 151600000, "country": "Indonesia"},
    {"name": "North Island (NZ)", "lat": -38.00, "lon": 176.00, "area_km2": 113729, "population": 3900000, "country": "New Zealand"},
    {"name": "Luzon", "lat": 16.00, "lon": 121.00, "area_km2": 109965, "population": 53300000, "country": "Philippines"},
    {"name": "Iceland", "lat": 65.00, "lon": -18.00, "area_km2": 103000, "population": 376000, "country": "Iceland"},
    {"name": "Mindanao", "lat": 8.00, "lon": 125.00, "area_km2": 97530, "population": 25500000, "country": "Philippines"},
    {"name": "Ireland", "lat": 53.50, "lon": -8.00, "area_km2": 84421, "population": 6900000, "country": "Ireland/UK"},
    {"name": "Hokkaido", "lat": 43.00, "lon": 143.00, "area_km2": 83424, "population": 5300000, "country": "Japan"},
    {"name": "Hispaniola", "lat": 19.00, "lon": -71.00, "area_km2": 76192, "population": 22300000, "country": "Haiti/Dominican Republic"},
    {"name": "Sakhalin", "lat": 51.00, "lon": 143.00, "area_km2": 72493, "population": 490000, "country": "Russia"},
    {"name": "Banks Island", "lat": 73.00, "lon": -121.50, "area_km2": 70028, "population": 112, "country": "Canada"},
    {"name": "Sri Lanka", "lat": 7.87, "lon": 80.77, "area_km2": 65610, "population": 22000000, "country": "Sri Lanka"},
    {"name": "Tasmania", "lat": -42.00, "lon": 147.00, "area_km2": 68401, "population": 541000, "country": "Australia"},
    {"name": "Devon Island", "lat": 75.00, "lon": -87.00, "area_km2": 55247, "population": 0, "country": "Canada"},
    {"name": "Cuba", "lat": 22.00, "lon": -79.50, "area_km2": 109886, "population": 11300000, "country": "Cuba"},
]

# ═══════════════════════════════════════════════════════════════
# 8. ACTIVE VOLCANOES (40+)
# ═══════════════════════════════════════════════════════════════
ACTIVE_VOLCANOES = [
    {"name": "Kilauea", "lat": 19.4069, "lon": -155.2834, "elevation_m": 1247, "vei_max": 4, "type": "Shield", "country": "USA"},
    {"name": "Mount Etna", "lat": 37.7510, "lon": 14.9934, "elevation_m": 3357, "vei_max": 3, "type": "Stratovolcano", "country": "Italy"},
    {"name": "Stromboli", "lat": 38.7890, "lon": 15.2133, "elevation_m": 924, "vei_max": 3, "type": "Stratovolcano", "country": "Italy"},
    {"name": "Mount Vesuvius", "lat": 40.8210, "lon": 14.4260, "elevation_m": 1281, "vei_max": 5, "type": "Stratovolcano", "country": "Italy"},
    {"name": "Piton de la Fournaise", "lat": -21.2440, "lon": 55.7083, "elevation_m": 2632, "vei_max": 2, "type": "Shield", "country": "France (Reunion)"},
    {"name": "Merapi", "lat": -7.5407, "lon": 110.4457, "elevation_m": 2930, "vei_max": 4, "type": "Stratovolcano", "country": "Indonesia"},
    {"name": "Krakatoa (Anak Krakatau)", "lat": -6.1021, "lon": 105.4230, "elevation_m": 813, "vei_max": 6, "type": "Caldera", "country": "Indonesia"},
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274, "elevation_m": 3776, "vei_max": 5, "type": "Stratovolcano", "country": "Japan"},
    {"name": "Sakurajima", "lat": 31.5850, "lon": 130.6567, "elevation_m": 1117, "vei_max": 4, "type": "Stratovolcano", "country": "Japan"},
    {"name": "Mount Aso", "lat": 32.8842, "lon": 131.1040, "elevation_m": 1592, "vei_max": 7, "type": "Caldera", "country": "Japan"},
    {"name": "Mount St. Helens", "lat": 46.2003, "lon": -122.1806, "elevation_m": 2549, "vei_max": 5, "type": "Stratovolcano", "country": "USA"},
    {"name": "Mount Rainier", "lat": 46.8523, "lon": -121.7603, "elevation_m": 4392, "vei_max": 4, "type": "Stratovolcano", "country": "USA"},
    {"name": "Yellowstone Caldera", "lat": 44.4280, "lon": -110.5885, "elevation_m": 2805, "vei_max": 8, "type": "Caldera", "country": "USA"},
    {"name": "Mauna Loa", "lat": 19.4750, "lon": -155.6083, "elevation_m": 4169, "vei_max": 0, "type": "Shield", "country": "USA"},
    {"name": "Cotopaxi", "lat": -0.6836, "lon": -78.4378, "elevation_m": 5897, "vei_max": 4, "type": "Stratovolcano", "country": "Ecuador"},
    {"name": "Tungurahua", "lat": -1.4677, "lon": -78.4425, "elevation_m": 5023, "vei_max": 3, "type": "Stratovolcano", "country": "Ecuador"},
    {"name": "Villarrica", "lat": -39.4200, "lon": -71.9300, "elevation_m": 2847, "vei_max": 3, "type": "Stratovolcano", "country": "Chile"},
    {"name": "Eyjafjallajokull", "lat": 63.6300, "lon": -19.6117, "elevation_m": 1651, "vei_max": 4, "type": "Stratovolcano", "country": "Iceland"},
    {"name": "Hekla", "lat": 63.9833, "lon": -19.6667, "elevation_m": 1491, "vei_max": 5, "type": "Stratovolcano", "country": "Iceland"},
    {"name": "Bardarbunga", "lat": 64.6333, "lon": -17.5333, "elevation_m": 2009, "vei_max": 6, "type": "Stratovolcano", "country": "Iceland"},
    {"name": "Mount Erebus", "lat": -77.5278, "lon": 167.1531, "elevation_m": 3794, "vei_max": 3, "type": "Stratovolcano", "country": "Antarctica"},
    {"name": "Mount Pinatubo", "lat": 15.1430, "lon": 120.3500, "elevation_m": 1486, "vei_max": 6, "type": "Stratovolcano", "country": "Philippines"},
    {"name": "Taal", "lat": 14.0113, "lon": 120.9983, "elevation_m": 311, "vei_max": 4, "type": "Caldera", "country": "Philippines"},
    {"name": "Mount Nyiragongo", "lat": -1.5200, "lon": 29.2500, "elevation_m": 3470, "vei_max": 1, "type": "Stratovolcano", "country": "DR Congo"},
    {"name": "Mount Cameroon", "lat": 4.2030, "lon": 9.1700, "elevation_m": 4040, "vei_max": 2, "type": "Stratovolcano", "country": "Cameroon"},
    {"name": "Ol Doinyo Lengai", "lat": -2.7631, "lon": 35.9025, "elevation_m": 2962, "vei_max": 2, "type": "Stratovolcano", "country": "Tanzania"},
    {"name": "Popocatepetl", "lat": 19.0225, "lon": -98.6278, "elevation_m": 5426, "vei_max": 5, "type": "Stratovolcano", "country": "Mexico"},
    {"name": "Colima", "lat": 19.5147, "lon": -103.6172, "elevation_m": 3850, "vei_max": 4, "type": "Stratovolcano", "country": "Mexico"},
    {"name": "Semeru", "lat": -8.1080, "lon": 112.9220, "elevation_m": 3676, "vei_max": 3, "type": "Stratovolcano", "country": "Indonesia"},
    {"name": "Sinabung", "lat": 3.1700, "lon": 98.3917, "elevation_m": 2460, "vei_max": 4, "type": "Stratovolcano", "country": "Indonesia"},
    {"name": "Agung", "lat": -8.3433, "lon": 115.5072, "elevation_m": 3031, "vei_max": 5, "type": "Stratovolcano", "country": "Indonesia"},
    {"name": "White Island (Whakaari)", "lat": -37.5208, "lon": 177.1814, "elevation_m": 321, "vei_max": 3, "type": "Stratovolcano", "country": "New Zealand"},
    {"name": "Ruapehu", "lat": -39.2817, "lon": 175.5642, "elevation_m": 2797, "vei_max": 3, "type": "Stratovolcano", "country": "New Zealand"},
    {"name": "Campi Flegrei", "lat": 40.8271, "lon": 14.1389, "elevation_m": 458, "vei_max": 7, "type": "Caldera", "country": "Italy"},
    {"name": "Santorini", "lat": 36.4040, "lon": 25.3961, "elevation_m": 367, "vei_max": 7, "type": "Caldera", "country": "Greece"},
    {"name": "Teide", "lat": 28.2723, "lon": -16.6424, "elevation_m": 3718, "vei_max": 4, "type": "Stratovolcano", "country": "Spain"},
    {"name": "Arenal", "lat": 10.4630, "lon": -84.7031, "elevation_m": 1670, "vei_max": 3, "type": "Stratovolcano", "country": "Costa Rica"},
    {"name": "Pacaya", "lat": 14.3819, "lon": -90.6017, "elevation_m": 2552, "vei_max": 3, "type": "Stratovolcano", "country": "Guatemala"},
    {"name": "Nevado del Ruiz", "lat": 4.8950, "lon": -75.3217, "elevation_m": 5321, "vei_max": 3, "type": "Stratovolcano", "country": "Colombia"},
    {"name": "Mount Unzen", "lat": 32.7610, "lon": 130.2986, "elevation_m": 1500, "vei_max": 4, "type": "Stratovolcano", "country": "Japan"},
    {"name": "Klyuchevskaya Sopka", "lat": 56.0558, "lon": 160.6411, "elevation_m": 4750, "vei_max": 4, "type": "Stratovolcano", "country": "Russia"},
    {"name": "Mount Shasta", "lat": 41.4092, "lon": -122.1949, "elevation_m": 4322, "vei_max": 3, "type": "Stratovolcano", "country": "USA"},
]

# ═══════════════════════════════════════════════════════════════
# 9. WATERFALLS (25+)
# ═══════════════════════════════════════════════════════════════
WATERFALLS = [
    {"name": "Angel Falls", "lat": 5.9701, "lon": -62.5362, "height_m": 979, "type": "Plunge", "country": "Venezuela"},
    {"name": "Tugela Falls", "lat": -28.7328, "lon": 28.9497, "height_m": 948, "type": "Tiered", "country": "South Africa"},
    {"name": "Tres Hermanas Falls", "lat": -14.3833, "lon": -72.5500, "height_m": 914, "type": "Tiered", "country": "Peru"},
    {"name": "Olo'upena Falls", "lat": 21.1000, "lon": -156.8833, "height_m": 900, "type": "Plunge", "country": "USA (Hawaii)"},
    {"name": "Yumbilla Falls", "lat": -5.9333, "lon": -77.9000, "height_m": 896, "type": "Tiered", "country": "Peru"},
    {"name": "Vinnufossen", "lat": 62.1500, "lon": 7.2833, "height_m": 865, "type": "Tiered", "country": "Norway"},
    {"name": "Balaifossen", "lat": 60.5500, "lon": 6.5167, "height_m": 850, "type": "Plunge", "country": "Norway"},
    {"name": "Pu'uka'oku Falls", "lat": 21.1167, "lon": -156.9000, "height_m": 840, "type": "Plunge", "country": "USA (Hawaii)"},
    {"name": "James Bruce Falls", "lat": 51.0500, "lon": -124.8833, "height_m": 840, "type": "Plunge", "country": "Canada"},
    {"name": "Browne Falls", "lat": -45.4333, "lon": 167.1667, "height_m": 836, "type": "Plunge", "country": "New Zealand"},
    {"name": "Detian Falls", "lat": 22.8544, "lon": 107.0517, "height_m": 70, "type": "Multi-step", "country": "China/Vietnam"},
    {"name": "Niagara Falls", "lat": 43.0799, "lon": -79.0747, "height_m": 51, "type": "Curtain", "country": "USA/Canada"},
    {"name": "Iguazu Falls", "lat": -25.6953, "lon": -54.4367, "height_m": 82, "type": "Curtain", "country": "Argentina/Brazil"},
    {"name": "Victoria Falls", "lat": -17.9243, "lon": 25.8572, "height_m": 108, "type": "Curtain", "country": "Zambia/Zimbabwe"},
    {"name": "Kaieteur Falls", "lat": 5.1753, "lon": -59.4815, "height_m": 226, "type": "Plunge", "country": "Guyana"},
    {"name": "Gullfoss", "lat": 64.3271, "lon": -20.1199, "height_m": 32, "type": "Multi-step", "country": "Iceland"},
    {"name": "Dettifoss", "lat": 65.8147, "lon": -16.3844, "height_m": 45, "type": "Plunge", "country": "Iceland"},
    {"name": "Havasu Falls", "lat": 36.2553, "lon": -112.6978, "height_m": 37, "type": "Plunge", "country": "USA"},
    {"name": "Plitvice Waterfalls", "lat": 44.9025, "lon": 15.6092, "height_m": 78, "type": "Tiered", "country": "Croatia"},
    {"name": "Yosemite Falls", "lat": 37.7558, "lon": -119.5964, "height_m": 739, "type": "Tiered", "country": "USA"},
    {"name": "Sutherland Falls", "lat": -44.8167, "lon": 167.7333, "height_m": 580, "type": "Tiered", "country": "New Zealand"},
    {"name": "Jog Falls", "lat": 14.2283, "lon": 74.8124, "height_m": 253, "type": "Plunge", "country": "India"},
    {"name": "Ban Gioc Falls", "lat": 22.8544, "lon": 106.7178, "height_m": 53, "type": "Multi-step", "country": "Vietnam/China"},
    {"name": "Seljalandsfoss", "lat": 63.6156, "lon": -19.9886, "height_m": 65, "type": "Plunge", "country": "Iceland"},
    {"name": "Skogafoss", "lat": 63.5321, "lon": -19.5112, "height_m": 60, "type": "Curtain", "country": "Iceland"},
    {"name": "Kuang Si Falls", "lat": 19.7483, "lon": 101.9936, "height_m": 60, "type": "Tiered", "country": "Laos"},
    {"name": "Nachi Falls", "lat": 33.6750, "lon": 135.8933, "height_m": 133, "type": "Plunge", "country": "Japan"},
]

# ═══════════════════════════════════════════════════════════════
# 10. GEOLOGICAL FORMATIONS (25+)
# ═══════════════════════════════════════════════════════════════
GEOLOGICAL_FORMATIONS = [
    {"name": "Grand Canyon", "lat": 36.1069, "lon": -112.1129, "type": "Canyon", "age": "2 billion years", "country": "USA"},
    {"name": "Uluru (Ayers Rock)", "lat": -25.3444, "lon": 131.0369, "type": "Inselberg", "age": "550 million years", "country": "Australia"},
    {"name": "Giant's Causeway", "lat": 55.2408, "lon": -6.5116, "type": "Basalt Columns", "age": "60 million years", "country": "UK (Northern Ireland)"},
    {"name": "Bryce Canyon", "lat": 37.5930, "lon": -112.1871, "type": "Hoodoos", "age": "40 million years", "country": "USA"},
    {"name": "Monument Valley", "lat": 36.9833, "lon": -110.1000, "type": "Buttes", "age": "250 million years", "country": "USA"},
    {"name": "Cappadocia Fairy Chimneys", "lat": 38.6431, "lon": 34.8308, "type": "Volcanic Tuff Pillars", "age": "10 million years", "country": "Turkey"},
    {"name": "Ha Long Bay", "lat": 20.9101, "lon": 107.1839, "type": "Karst Towers", "age": "500 million years", "country": "Vietnam"},
    {"name": "Zhangjiajie Pillars", "lat": 29.3250, "lon": 110.4342, "type": "Sandstone Pillars", "age": "380 million years", "country": "China"},
    {"name": "Meteora", "lat": 39.7139, "lon": 21.6308, "type": "Sandstone Pillars", "age": "60 million years", "country": "Greece"},
    {"name": "Plitvice Lakes (travertine)", "lat": 44.8654, "lon": 15.5820, "type": "Karst / Travertine", "age": "10,000 years", "country": "Croatia"},
    {"name": "Cliffs of Moher", "lat": 52.9715, "lon": -9.4267, "type": "Sea Cliffs", "age": "320 million years", "country": "Ireland"},
    {"name": "White Cliffs of Dover", "lat": 51.1330, "lon": 1.3340, "type": "Chalk Cliffs", "age": "100 million years", "country": "UK"},
    {"name": "Arches National Park", "lat": 38.7331, "lon": -109.5925, "type": "Natural Arches", "age": "300 million years", "country": "USA"},
    {"name": "Antelope Canyon", "lat": 36.8619, "lon": -111.3743, "type": "Slot Canyon", "age": "5 million years", "country": "USA"},
    {"name": "Bungle Bungle Range", "lat": -17.4400, "lon": 128.3800, "type": "Sandstone Domes", "age": "350 million years", "country": "Australia"},
    {"name": "Tsingy de Bemaraha", "lat": -18.6667, "lon": 44.7500, "type": "Limestone Needles", "age": "200 million years", "country": "Madagascar"},
    {"name": "Wave Rock", "lat": -32.4400, "lon": 118.8969, "type": "Granite Wave", "age": "2.7 billion years", "country": "Australia"},
    {"name": "Devils Tower", "lat": 44.5902, "lon": -104.7147, "type": "Igneous Intrusion", "age": "50 million years", "country": "USA"},
    {"name": "Chocolate Hills", "lat": 9.7944, "lon": 124.1667, "type": "Limestone Hills", "age": "2 million years", "country": "Philippines"},
    {"name": "Door to Hell (Darvaza)", "lat": 40.2525, "lon": 58.4397, "type": "Gas Crater", "age": "1971 (man-made)", "country": "Turkmenistan"},
    {"name": "Pamukkale Travertines", "lat": 37.9208, "lon": 29.1217, "type": "Travertine Terraces", "age": "400,000 years", "country": "Turkey"},
    {"name": "Salar de Uyuni", "lat": -20.1338, "lon": -67.4891, "type": "Salt Flat", "age": "30,000 years", "country": "Bolivia"},
    {"name": "Eye of the Sahara (Richat)", "lat": 21.1239, "lon": -11.4017, "type": "Erosion Dome", "age": "100 million years", "country": "Mauritania"},
    {"name": "Moeraki Boulders", "lat": -45.3453, "lon": 170.8275, "type": "Concretions", "age": "60 million years", "country": "New Zealand"},
    {"name": "Mount Roraima", "lat": 5.1433, "lon": -60.7625, "type": "Tepui", "age": "2 billion years", "country": "Venezuela/Brazil/Guyana"},
    {"name": "Painted Desert", "lat": 35.0767, "lon": -109.7875, "type": "Badlands", "age": "225 million years", "country": "USA"},
    {"name": "Marble Caves (Chile)", "lat": -46.6600, "lon": -72.6300, "type": "Marble Caverns", "age": "6,000 years", "country": "Chile"},
    {"name": "Fingal's Cave", "lat": 56.4314, "lon": -6.3411, "type": "Basalt Sea Cave", "age": "60 million years", "country": "UK (Scotland)"},
]


# ═══════════════════════════════════════════════════════════════
# COLOR PALETTES for each map type
# ═══════════════════════════════════════════════════════════════
def _altitude_color(alt: float) -> str:
    """Color by altitude for peaks."""
    if alt >= 8000:
        return "#ef4444"
    if alt >= 7000:
        return "#f97316"
    if alt >= 6000:
        return "#f59e0b"
    if alt >= 5000:
        return "#eab308"
    if alt >= 4000:
        return "#10b981"
    if alt >= 3000:
        return "#06b6d4"
    return "#8b5cf6"


def _depth_color(depth: float) -> str:
    """Color by depth (negative values)."""
    d = abs(depth)
    if d >= 10000:
        return "#1e3a5f"
    if d >= 5000:
        return "#1e40af"
    if d >= 2000:
        return "#2563eb"
    if d >= 1000:
        return "#3b82f6"
    if d >= 500:
        return "#60a5fa"
    return "#93c5fd"


def _desert_color(dtype: str) -> str:
    """Color by desert type."""
    return "#f59e0b" if dtype == "Hot" else "#60a5fa"


def _temp_color(category: str) -> str:
    """Color by temperature category."""
    cat = category.lower()
    if "hottest" in cat:
        return "#ef4444"
    if "coldest" in cat:
        return "#3b82f6"
    if "wettest" in cat:
        return "#10b981"
    return "#f59e0b"  # driest


def _river_color(length: float) -> str:
    """Color by river length."""
    if length >= 6000:
        return "#06b6d4"
    if length >= 4000:
        return "#3b82f6"
    if length >= 3000:
        return "#8b5cf6"
    return "#a855f7"


def _lake_color(area: float) -> str:
    """Color by lake area."""
    if area >= 50000:
        return "#0ea5e9"
    if area >= 20000:
        return "#38bdf8"
    if area >= 5000:
        return "#7dd3fc"
    return "#bae6fd"


def _island_color(area: float) -> str:
    """Color by island area."""
    if area >= 500000:
        return "#10b981"
    if area >= 100000:
        return "#34d399"
    if area >= 50000:
        return "#6ee7b7"
    return "#a7f3d0"


def _volcano_color(vei: int) -> str:
    """Color by VEI."""
    if vei >= 7:
        return "#7f1d1d"
    if vei >= 5:
        return "#dc2626"
    if vei >= 3:
        return "#f97316"
    if vei >= 1:
        return "#f59e0b"
    return "#fbbf24"


def _waterfall_color(height: float) -> str:
    """Color by waterfall height."""
    if height >= 800:
        return "#06b6d4"
    if height >= 300:
        return "#0ea5e9"
    if height >= 100:
        return "#38bdf8"
    return "#7dd3fc"


def _formation_color(ftype: str) -> str:
    """Color by formation type."""
    mapping = {
        "Canyon": "#ef4444", "Slot Canyon": "#ef4444",
        "Inselberg": "#f59e0b", "Basalt Columns": "#6366f1",
        "Hoodoos": "#f97316", "Buttes": "#d97706",
        "Volcanic Tuff Pillars": "#a855f7", "Karst Towers": "#10b981",
        "Sandstone Pillars": "#eab308", "Sandstone Domes": "#eab308",
        "Karst / Travertine": "#14b8a6", "Sea Cliffs": "#64748b",
        "Chalk Cliffs": "#e2e8f0", "Natural Arches": "#f97316",
        "Limestone Needles": "#8b97b0", "Limestone Hills": "#a3e635",
        "Granite Wave": "#ec4899", "Igneous Intrusion": "#8b5cf6",
        "Gas Crater": "#ef4444", "Travertine Terraces": "#06b6d4",
        "Salt Flat": "#f0f0f0", "Erosion Dome": "#d4a574",
        "Concretions": "#92400e", "Tepui": "#10b981",
        "Badlands": "#c2410c", "Marble Caverns": "#a5b4fc",
        "Basalt Sea Cave": "#6366f1",
    }
    return mapping.get(ftype, "#8b97b0")


# ═══════════════════════════════════════════════════════════════
# HELPER: build a Folium map
# ═══════════════════════════════════════════════════════════════
def _build_map(center_lat: float, center_lon: float, zoom: int = 2) -> folium.Map:
    """Create a dark base Folium map."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        width="100%",
        height=550,
    )
    return m


def _add_circle_marker(m: folium.Map, lat: float, lon: float,
                       color: str, radius: float, popup_html: str,
                       tooltip: str) -> None:
    """Add a circle marker to the map."""
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=tooltip,
    ).add_to(m)


# ═══════════════════════════════════════════════════════════════
# HELPER: dark matplotlib chart
# ═══════════════════════════════════════════════════════════════
def _dark_bar_chart(labels, values, title, xlabel, ylabel, color="#06b6d4", horizontal=False):
    """Create a dark-themed bar chart and return bytes buffer."""
    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.35 if horizontal else 4)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor="#2a3550", linewidth=0.5)
        ax.set_xlabel(xlabel, color="#8b97b0", fontsize=10)
        ax.set_ylabel(ylabel, color="#8b97b0", fontsize=10)
        ax.invert_yaxis()
    else:
        bars = ax.bar(labels, values, color=color, edgecolor="#2a3550", linewidth=0.5)
        ax.set_xlabel(xlabel, color="#8b97b0", fontsize=10)
        ax.set_ylabel(ylabel, color="#8b97b0", fontsize=10)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold", pad=10)
    ax.tick_params(colors="#8b97b0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x" if horizontal else "y", color="#2a3550", alpha=0.3, linestyle="--")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor="#0a0e1a", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════
# INDIVIDUAL MAP RENDERERS
# ═══════════════════════════════════════════════════════════════
def _render_highest_peaks():
    """Render Highest Peaks map, stats, table, and download."""
    data = HIGHEST_PEAKS
    df = pd.DataFrame(data)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Peaks", len(df))
    c2.metric("8000m+ Peaks", int((df["altitude_m"] >= 8000).sum()))
    c3.metric("Highest", f"{df['altitude_m'].max():,} m")
    c4.metric("Countries", df["country"].nunique())

    # Chart
    top20 = df.nlargest(20, "altitude_m")
    chart_buf = _dark_bar_chart(
        top20["name"].tolist(), top20["altitude_m"].tolist(),
        "Top 20 Highest Peaks", "Peak", "Altitude (m)", color="#ef4444",
    )
    st.image(chart_buf, width=900)

    # Map
    m = _build_map(30, 80, zoom=3)
    for _, row in df.iterrows():
        color = _altitude_color(row["altitude_m"])
        radius = max(4, row["altitude_m"] / 1000)
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Altitude: {row['altitude_m']:,} m<br>"
            f"Range: {escape(str(row['range']))}<br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"First ascent: {row['first_ascent']}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    # Table
    st.dataframe(df.sort_values("altitude_m", ascending=False), width="stretch", hide_index=True)

    # Download
    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Highest Peaks CSV", csv_buf, "highest_peaks.csv", "text/csv")


def _render_deepest_points():
    """Render Deepest Points map, stats, table, and download."""
    data = DEEPEST_POINTS
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Points", len(df))
    c2.metric("Ocean Trenches", int((df["type"] == "Ocean Trench").sum()))
    c3.metric("Deepest", f"{abs(df['depth_m'].min()):,} m")
    c4.metric("Caves", int((df["type"] == "Cave").sum()))

    top15 = df.nsmallest(15, "depth_m")
    chart_buf = _dark_bar_chart(
        top15["name"].tolist(), [abs(v) for v in top15["depth_m"].tolist()],
        "Top 15 Deepest Points", "Point", "Depth (m)", color="#3b82f6", horizontal=True,
    )
    st.image(chart_buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _depth_color(row["depth_m"])
        radius = max(4, abs(row["depth_m"]) / 1500)
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Depth: {abs(row['depth_m']):,} m<br>"
            f"Type: {escape(str(row['type']))}<br>"
            f"Body: {escape(str(row['body']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df.sort_values("depth_m"), width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Deepest Points CSV", csv_buf, "deepest_points.csv", "text/csv")


def _render_largest_deserts():
    """Render Largest Deserts map, stats, table, and download."""
    data = LARGEST_DESERTS
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Deserts", len(df))
    c2.metric("Hot Deserts", int((df["type"] == "Hot").sum()))
    c3.metric("Cold Deserts", int((df["type"] == "Cold").sum()))
    c4.metric("Total Area", f"{df['area_km2'].sum() / 1e6:.1f}M km\u00b2")

    chart_buf = _dark_bar_chart(
        df["name"].tolist(), [a / 1e6 for a in df["area_km2"].tolist()],
        "World Deserts by Area", "Desert", "Area (million km\u00b2)", color="#f59e0b", horizontal=True,
    )
    st.image(chart_buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _desert_color(row["type"])
        radius = max(5, row["area_km2"] / 1000000)
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Area: {row['area_km2']:,} km\u00b2<br>"
            f"Type: {escape(str(row['type']))}<br>"
            f"Continent: {escape(str(row['continent']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df.sort_values("area_km2", ascending=False), width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Largest Deserts CSV", csv_buf, "largest_deserts.csv", "text/csv")


def _render_extreme_temperatures():
    """Render Extreme Temperatures map, stats, table, and download."""
    data = EXTREME_TEMPERATURES
    df = pd.DataFrame(data)

    hottest = df[df["category"].str.contains("Hottest", case=False)]
    coldest = df[df["category"].str.contains("Coldest", case=False)]
    wettest = df[df["category"].str.contains("Wettest", case=False)]
    driest = df[df["category"].str.contains("Driest", case=False)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hottest Record", "56.7\u00b0C")
    c2.metric("Coldest Record", "-89.2\u00b0C")
    c3.metric("Wettest (annual)", "11,871 mm")
    c4.metric("Driest", "0 mm")

    # Chart: hottest and coldest side by side
    hot_top = hottest.nlargest(6, "record_c")
    cold_top = coldest.nsmallest(6, "record_c")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("#0a0e1a")
    for ax in (ax1, ax2):
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#8b97b0", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")

    ax1.barh(hot_top["name"].tolist(), hot_top["record_c"].tolist(), color="#ef4444", edgecolor="#2a3550")
    ax1.set_title("Hottest Places (\u00b0C)", color="#e8ecf4", fontsize=12, fontweight="bold")
    ax1.set_xlabel("\u00b0C", color="#8b97b0")
    ax1.invert_yaxis()
    ax1.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")

    ax2.barh(cold_top["name"].tolist(), cold_top["record_c"].tolist(), color="#3b82f6", edgecolor="#2a3550")
    ax2.set_title("Coldest Places (\u00b0C)", color="#e8ecf4", fontsize=12, fontweight="bold")
    ax2.set_xlabel("\u00b0C", color="#8b97b0")
    ax2.invert_yaxis()
    ax2.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor="#0a0e1a", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _temp_color(row["category"])
        radius = 7
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Record: {row['record_c']}<br>"
            f"Category: {escape(str(row['category']))}<br>"
            f"Detail: {escape(str(row['detail']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Extreme Temperatures CSV", csv_buf, "extreme_temperatures.csv", "text/csv")


def _render_longest_rivers():
    """Render Longest Rivers map, stats, table, and download."""
    data = LONGEST_RIVERS
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rivers", len(df))
    c2.metric("Longest", f"{df['length_km'].max():,} km")
    c3.metric("Largest Discharge", f"{df['discharge_m3s'].max():,} m\u00b3/s")
    c4.metric("Continents", df["continent"].nunique())

    top15 = df.nlargest(15, "length_km")
    chart_buf = _dark_bar_chart(
        top15["name"].tolist(), top15["length_km"].tolist(),
        "Top 15 Longest Rivers", "River", "Length (km)", color="#06b6d4", horizontal=True,
    )
    st.image(chart_buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _river_color(row["length_km"])
        radius = max(4, row["length_km"] / 800)
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Length: {row['length_km']:,} km<br>"
            f"Discharge: {row['discharge_m3s']:,} m\u00b3/s<br>"
            f"Basin: {row['basin_km2']:,} km\u00b2<br>"
            f"Continent: {escape(str(row['continent']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df.sort_values("length_km", ascending=False), width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Longest Rivers CSV", csv_buf, "longest_rivers.csv", "text/csv")


def _render_largest_lakes():
    """Render Largest Lakes map, stats, table, and download."""
    data = LARGEST_LAKES
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Lakes", len(df))
    c2.metric("Largest", f"{df['area_km2'].max():,} km\u00b2")
    c3.metric("Deepest", f"{df['max_depth_m'].max():,} m")
    c4.metric("Highest Volume", f"{df['volume_km3'].max():,} km\u00b3")

    top15 = df.nlargest(15, "area_km2")
    chart_buf = _dark_bar_chart(
        top15["name"].tolist(), [a / 1000 for a in top15["area_km2"].tolist()],
        "Top 15 Largest Lakes by Area", "Lake", "Area (x1000 km\u00b2)", color="#0ea5e9", horizontal=True,
    )
    st.image(chart_buf, width=900)

    m = _build_map(30, 0, zoom=2)
    for _, row in df.iterrows():
        color = _lake_color(row["area_km2"])
        radius = max(4, min(15, row["area_km2"] / 20000))
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Area: {row['area_km2']:,} km\u00b2<br>"
            f"Max Depth: {row['max_depth_m']:,} m<br>"
            f"Volume: {row['volume_km3']:,} km\u00b3<br>"
            f"Continent: {escape(str(row['continent']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df.sort_values("area_km2", ascending=False), width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Largest Lakes CSV", csv_buf, "largest_lakes.csv", "text/csv")


def _render_largest_islands():
    """Render Largest Islands map, stats, table, and download."""
    data = LARGEST_ISLANDS
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Islands", len(df))
    c2.metric("Largest", f"{df['area_km2'].max():,} km\u00b2")
    c3.metric("Most Populated", df.loc[df["population"].idxmax(), "name"])
    c4.metric("Max Population", f"{df['population'].max():,.0f}")

    top15 = df.nlargest(15, "area_km2")
    chart_buf = _dark_bar_chart(
        top15["name"].tolist(), [a / 1000 for a in top15["area_km2"].tolist()],
        "Top 15 Largest Islands by Area", "Island", "Area (x1000 km\u00b2)", color="#10b981", horizontal=True,
    )
    st.image(chart_buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _island_color(row["area_km2"])
        radius = max(4, min(14, row["area_km2"] / 100000))
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Area: {row['area_km2']:,} km\u00b2<br>"
            f"Population: {row['population']:,}<br>"
            f"Country: {escape(str(row['country']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df.sort_values("area_km2", ascending=False), width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Largest Islands CSV", csv_buf, "largest_islands.csv", "text/csv")


def _render_active_volcanoes():
    """Render Active Volcanoes map, stats, table, and download."""
    data = ACTIVE_VOLCANOES
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Volcanoes", len(df))
    c2.metric("Stratovolcanoes", int((df["type"] == "Stratovolcano").sum()))
    c3.metric("Calderas", int((df["type"] == "Caldera").sum()))
    c4.metric("Max VEI", int(df["vei_max"].max()))

    # Chart by VEI
    vei_counts = df["vei_max"].value_counts().sort_index()
    chart_buf = _dark_bar_chart(
        [f"VEI {v}" for v in vei_counts.index.tolist()],
        vei_counts.values.tolist(),
        "Volcanoes by Maximum VEI Rating", "VEI", "Count", color="#ef4444",
    )
    st.image(chart_buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _volcano_color(row["vei_max"])
        radius = max(4, row["vei_max"] + 3)
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Elevation: {row['elevation_m']:,} m<br>"
            f"Max VEI: {row['vei_max']}<br>"
            f"Type: {escape(str(row['type']))}<br>"
            f"Country: {escape(str(row['country']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df.sort_values("vei_max", ascending=False), width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Active Volcanoes CSV", csv_buf, "active_volcanoes.csv", "text/csv")


def _render_waterfalls():
    """Render Waterfalls map, stats, table, and download."""
    data = WATERFALLS
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Waterfalls", len(df))
    c2.metric("Tallest", f"{df['height_m'].max()} m")
    c3.metric("Plunge Type", int((df["type"] == "Plunge").sum()))
    c4.metric("Countries", df["country"].nunique())

    top15 = df.nlargest(15, "height_m")
    chart_buf = _dark_bar_chart(
        top15["name"].tolist(), top15["height_m"].tolist(),
        "Top 15 Tallest Waterfalls", "Waterfall", "Height (m)", color="#06b6d4", horizontal=True,
    )
    st.image(chart_buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _waterfall_color(row["height_m"])
        radius = max(4, min(12, row["height_m"] / 80))
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Height: {row['height_m']} m<br>"
            f"Type: {escape(str(row['type']))}<br>"
            f"Country: {escape(str(row['country']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df.sort_values("height_m", ascending=False), width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Waterfalls CSV", csv_buf, "waterfalls.csv", "text/csv")


def _render_geological_formations():
    """Render Geological Formations map, stats, table, and download."""
    data = GEOLOGICAL_FORMATIONS
    df = pd.DataFrame(data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Formations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Formation Types", df["type"].nunique())
    c4.metric("Oldest", "2 billion yr")

    # Chart: count by type
    type_counts = df["type"].value_counts()
    chart_buf = _dark_bar_chart(
        type_counts.index.tolist(), type_counts.values.tolist(),
        "Geological Formations by Type", "Type", "Count", color="#a855f7", horizontal=True,
    )
    st.image(chart_buf, width=900)

    m = _build_map(20, 0, zoom=2)
    for _, row in df.iterrows():
        color = _formation_color(row["type"])
        radius = 7
        popup = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Type: {escape(str(row['type']))}<br>"
            f"Age: {escape(str(row['age']))}<br>"
            f"Country: {escape(str(row['country']))}"
        )
        _add_circle_marker(m, row["lat"], row["lon"], color, radius,
                           popup, escape(str(row["name"])))
    components.html(m._repr_html_(), height=550)

    st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    st.download_button("Download Geological Formations CSV", csv_buf, "geological_formations.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
# DISPATCH TABLE
# ═══════════════════════════════════════════════════════════════
_RENDERERS = {
    "Highest Peaks": _render_highest_peaks,
    "Deepest Points": _render_deepest_points,
    "Largest Deserts": _render_largest_deserts,
    "Extreme Temperatures": _render_extreme_temperatures,
    "Longest Rivers": _render_longest_rivers,
    "Largest Lakes": _render_largest_lakes,
    "Largest Islands": _render_largest_islands,
    "Active Volcanoes": _render_active_volcanoes,
    "Waterfalls": _render_waterfalls,
    "Geological Formations": _render_geological_formations,
}


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def render_extreme_geography_tab():
    """Main entry point for the Extreme Geography tab."""
    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>Extreme Geography</h4>"
        "<p>Explore the world's most extreme geographical features -- highest peaks, "
        "deepest points, largest deserts, volcanoes, waterfalls, and more.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    selected = st.selectbox(
        "Select map type",
        MAP_TYPES,
        key="extreme_geo_map_type",
    )

    st.markdown("---")

    renderer = _RENDERERS.get(selected)
    if renderer:
        renderer()
    else:
        st.warning("Unknown map type selected.")
