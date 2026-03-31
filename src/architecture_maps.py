# -*- coding: utf-8 -*-
"""
TerraScout AI - Architecture & Monuments Maps Module
Provides 10 architecture map types including tallest buildings, world wonders,
famous bridges, major dams, castles, lighthouses, religious buildings,
famous towers, ancient ruins, and modern marvels.
"""

import html
import io

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.overpass_client import query_overpass


# ---------------------------------------------------------------------------
# Data constants
# ---------------------------------------------------------------------------

TALLEST_BUILDINGS = [
    {"name": "Burj Khalifa", "lat": 25.1972, "lon": 55.2744, "height_m": 828, "floors": 163, "year": 2010, "city": "Dubai", "country": "UAE"},
    {"name": "Merdeka 118", "lat": 3.1415, "lon": 101.7005, "height_m": 679, "floors": 118, "year": 2023, "city": "Kuala Lumpur", "country": "Malaysia"},
    {"name": "Shanghai Tower", "lat": 31.2357, "lon": 121.5016, "height_m": 632, "floors": 128, "year": 2015, "city": "Shanghai", "country": "China"},
    {"name": "Abraj Al-Bait Clock Tower", "lat": 21.4189, "lon": 39.8263, "height_m": 601, "floors": 120, "year": 2012, "city": "Mecca", "country": "Saudi Arabia"},
    {"name": "Ping An Finance Centre", "lat": 22.5333, "lon": 114.0543, "height_m": 599, "floors": 115, "year": 2017, "city": "Shenzhen", "country": "China"},
    {"name": "Lotte World Tower", "lat": 37.5126, "lon": 127.1026, "height_m": 555, "floors": 123, "year": 2017, "city": "Seoul", "country": "South Korea"},
    {"name": "One World Trade Center", "lat": 40.7127, "lon": -74.0134, "height_m": 541, "floors": 104, "year": 2014, "city": "New York", "country": "USA"},
    {"name": "Guangzhou CTF Finance Centre", "lat": 23.1195, "lon": 113.3220, "height_m": 530, "floors": 111, "year": 2016, "city": "Guangzhou", "country": "China"},
    {"name": "Tianjin CTF Finance Centre", "lat": 39.0217, "lon": 117.6940, "height_m": 530, "floors": 97, "year": 2019, "city": "Tianjin", "country": "China"},
    {"name": "CITIC Tower", "lat": 39.9130, "lon": 116.4860, "height_m": 528, "floors": 108, "year": 2018, "city": "Beijing", "country": "China"},
    {"name": "Taipei 101", "lat": 25.0340, "lon": 121.5645, "height_m": 508, "floors": 101, "year": 2004, "city": "Taipei", "country": "Taiwan"},
    {"name": "Shanghai World Financial Center", "lat": 31.2345, "lon": 121.5013, "height_m": 492, "floors": 101, "year": 2008, "city": "Shanghai", "country": "China"},
    {"name": "International Commerce Centre", "lat": 22.3033, "lon": 114.1603, "height_m": 484, "floors": 118, "year": 2010, "city": "Hong Kong", "country": "China"},
    {"name": "Lakhta Center", "lat": 59.9873, "lon": 30.1777, "height_m": 462, "floors": 87, "year": 2019, "city": "St. Petersburg", "country": "Russia"},
    {"name": "Landmark 81", "lat": 10.7955, "lon": 106.7220, "height_m": 461, "floors": 81, "year": 2018, "city": "Ho Chi Minh City", "country": "Vietnam"},
    {"name": "Changsha IFS Tower T1", "lat": 28.1918, "lon": 112.9780, "height_m": 452, "floors": 94, "year": 2018, "city": "Changsha", "country": "China"},
    {"name": "Petronas Tower 1", "lat": 3.1586, "lon": 101.7117, "height_m": 452, "floors": 88, "year": 1998, "city": "Kuala Lumpur", "country": "Malaysia"},
    {"name": "Petronas Tower 2", "lat": 3.1580, "lon": 101.7130, "height_m": 452, "floors": 88, "year": 1998, "city": "Kuala Lumpur", "country": "Malaysia"},
    {"name": "Zifeng Tower", "lat": 32.0631, "lon": 118.7780, "height_m": 450, "floors": 89, "year": 2010, "city": "Nanjing", "country": "China"},
    {"name": "Suzhou IFS", "lat": 31.3040, "lon": 120.6053, "height_m": 450, "floors": 98, "year": 2019, "city": "Suzhou", "country": "China"},
    {"name": "Willis Tower", "lat": 41.8789, "lon": -87.6359, "height_m": 442, "floors": 108, "year": 1974, "city": "Chicago", "country": "USA"},
    {"name": "Wuhan Greenland Center", "lat": 30.5580, "lon": 114.2730, "height_m": 436, "floors": 97, "year": 2022, "city": "Wuhan", "country": "China"},
    {"name": "Vincom Landmark 81 Tower B", "lat": 10.7950, "lon": 106.7215, "height_m": 435, "floors": 81, "year": 2018, "city": "Ho Chi Minh City", "country": "Vietnam"},
    {"name": "432 Park Avenue", "lat": 40.7616, "lon": -73.9712, "height_m": 426, "floors": 85, "year": 2015, "city": "New York", "country": "USA"},
    {"name": "Marina 101", "lat": 25.0897, "lon": 55.1442, "height_m": 425, "floors": 101, "year": 2017, "city": "Dubai", "country": "UAE"},
    {"name": "Trump International Hotel & Tower", "lat": 41.8892, "lon": -87.6268, "height_m": 423, "floors": 98, "year": 2009, "city": "Chicago", "country": "USA"},
    {"name": "Jin Mao Tower", "lat": 31.2355, "lon": 121.5015, "height_m": 421, "floors": 88, "year": 1999, "city": "Shanghai", "country": "China"},
    {"name": "Princess Tower", "lat": 25.0943, "lon": 55.1430, "height_m": 414, "floors": 101, "year": 2012, "city": "Dubai", "country": "UAE"},
    {"name": "Al Hamra Tower", "lat": 29.3808, "lon": 47.9911, "height_m": 413, "floors": 80, "year": 2011, "city": "Kuwait City", "country": "Kuwait"},
    {"name": "Two International Finance Centre", "lat": 22.2861, "lon": 114.1584, "height_m": 412, "floors": 88, "year": 2003, "city": "Hong Kong", "country": "China"},
    {"name": "Haeundae LCT The Sharp", "lat": 35.1600, "lon": 129.1730, "height_m": 411, "floors": 101, "year": 2019, "city": "Busan", "country": "South Korea"},
    {"name": "30 Hudson Yards", "lat": 40.7533, "lon": -74.0010, "height_m": 395, "floors": 73, "year": 2019, "city": "New York", "country": "USA"},
    {"name": "Central Park Tower", "lat": 40.7661, "lon": -73.9810, "height_m": 472, "floors": 98, "year": 2021, "city": "New York", "country": "USA"},
    {"name": "Empire State Building", "lat": 40.7484, "lon": -73.9857, "height_m": 443, "floors": 102, "year": 1931, "city": "New York", "country": "USA"},
    {"name": "Jeddah Tower (under construction)", "lat": 22.7200, "lon": 39.2418, "height_m": 1008, "floors": 167, "year": 2025, "city": "Jeddah", "country": "Saudi Arabia"},
    {"name": "Autograph Tower", "lat": -6.2250, "lon": 106.8100, "height_m": 382, "floors": 75, "year": 2022, "city": "Jakarta", "country": "Indonesia"},
    {"name": "The Exchange 106", "lat": 3.1420, "lon": 101.7188, "height_m": 454, "floors": 97, "year": 2019, "city": "Kuala Lumpur", "country": "Malaysia"},
    {"name": "Salesforce Tower", "lat": 37.7897, "lon": -122.3969, "height_m": 326, "floors": 61, "year": 2018, "city": "San Francisco", "country": "USA"},
    {"name": "The Shard", "lat": 51.5045, "lon": -0.0865, "height_m": 310, "floors": 95, "year": 2012, "city": "London", "country": "UK"},
    {"name": "Commerzbank Tower", "lat": 50.1086, "lon": 8.6716, "height_m": 259, "floors": 56, "year": 1997, "city": "Frankfurt", "country": "Germany"},
    {"name": "Varso Tower", "lat": 52.2320, "lon": 20.9970, "height_m": 310, "floors": 53, "year": 2022, "city": "Warsaw", "country": "Poland"},
    {"name": "Sapphire of Istanbul", "lat": 41.0684, "lon": 29.0170, "height_m": 261, "floors": 54, "year": 2011, "city": "Istanbul", "country": "Turkey"},
]

WORLD_WONDERS = [
    # 7 Ancient Wonders
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342, "category": "Ancient", "year": "2560 BC", "location": "Giza, Egypt", "status": "Extant"},
    {"name": "Hanging Gardens of Babylon", "lat": 32.5355, "lon": 44.4209, "category": "Ancient", "year": "600 BC", "location": "Hillah, Iraq", "status": "Destroyed"},
    {"name": "Statue of Zeus at Olympia", "lat": 37.6379, "lon": 21.6300, "category": "Ancient", "year": "435 BC", "location": "Olympia, Greece", "status": "Destroyed"},
    {"name": "Temple of Artemis at Ephesus", "lat": 37.9497, "lon": 27.3639, "category": "Ancient", "year": "550 BC", "location": "Selcuk, Turkey", "status": "Ruins"},
    {"name": "Mausoleum at Halicarnassus", "lat": 37.0380, "lon": 27.4241, "category": "Ancient", "year": "351 BC", "location": "Bodrum, Turkey", "status": "Ruins"},
    {"name": "Colossus of Rhodes", "lat": 36.4510, "lon": 28.2278, "category": "Ancient", "year": "280 BC", "location": "Rhodes, Greece", "status": "Destroyed"},
    {"name": "Lighthouse of Alexandria", "lat": 31.2139, "lon": 29.8856, "category": "Ancient", "year": "280 BC", "location": "Alexandria, Egypt", "status": "Destroyed"},
    # 7 New Wonders
    {"name": "Great Wall of China", "lat": 40.4319, "lon": 116.5704, "category": "New", "year": "700 BC - 1644 AD", "location": "China", "status": "Extant"},
    {"name": "Petra", "lat": 30.3285, "lon": 35.4444, "category": "New", "year": "312 BC", "location": "Ma'an, Jordan", "status": "Extant"},
    {"name": "Christ the Redeemer", "lat": -22.9519, "lon": -43.2105, "category": "New", "year": "1931 AD", "location": "Rio de Janeiro, Brazil", "status": "Extant"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "category": "New", "year": "1450 AD", "location": "Cusco, Peru", "status": "Extant"},
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678, "category": "New", "year": "600 AD", "location": "Yucatan, Mexico", "status": "Extant"},
    {"name": "Roman Colosseum", "lat": 41.8902, "lon": 12.4922, "category": "New", "year": "80 AD", "location": "Rome, Italy", "status": "Extant"},
    {"name": "Taj Mahal", "lat": 27.1751, "lon": 78.0421, "category": "New", "year": "1653 AD", "location": "Agra, India", "status": "Extant"},
    # 7 Natural Wonders
    {"name": "Grand Canyon", "lat": 36.1069, "lon": -112.1126, "category": "Natural", "year": "N/A", "location": "Arizona, USA", "status": "Natural"},
    {"name": "Great Barrier Reef", "lat": -18.2871, "lon": 147.6992, "category": "Natural", "year": "N/A", "location": "Queensland, Australia", "status": "Natural"},
    {"name": "Harbor of Rio de Janeiro", "lat": -22.9518, "lon": -43.1644, "category": "Natural", "year": "N/A", "location": "Rio de Janeiro, Brazil", "status": "Natural"},
    {"name": "Mount Everest", "lat": 27.9881, "lon": 86.9250, "category": "Natural", "year": "N/A", "location": "Nepal / Tibet", "status": "Natural"},
    {"name": "Aurora Borealis", "lat": 69.6489, "lon": 18.9551, "category": "Natural", "year": "N/A", "location": "Arctic Circle", "status": "Natural"},
    {"name": "Victoria Falls", "lat": -17.9243, "lon": 25.8572, "category": "Natural", "year": "N/A", "location": "Zambia / Zimbabwe", "status": "Natural"},
    {"name": "Paricutin Volcano", "lat": 19.4928, "lon": -102.2514, "category": "Natural", "year": "N/A", "location": "Michoacan, Mexico", "status": "Natural"},
]

FAMOUS_BRIDGES = [
    {"name": "Golden Gate Bridge", "lat": 37.8199, "lon": -122.4783, "span_m": 1280, "type": "Suspension", "year": 1937, "city": "San Francisco", "country": "USA"},
    {"name": "Millau Viaduct", "lat": 44.0775, "lon": 3.0223, "span_m": 2460, "type": "Cable-stayed", "year": 2004, "city": "Millau", "country": "France"},
    {"name": "Akashi Kaikyo Bridge", "lat": 34.6167, "lon": 135.0220, "span_m": 1991, "type": "Suspension", "year": 1998, "city": "Kobe", "country": "Japan"},
    {"name": "Brooklyn Bridge", "lat": 40.7061, "lon": -73.9969, "span_m": 486, "type": "Suspension / Cable-stayed", "year": 1883, "city": "New York", "country": "USA"},
    {"name": "Tower Bridge", "lat": 51.5055, "lon": -0.0754, "span_m": 244, "type": "Bascule / Suspension", "year": 1894, "city": "London", "country": "UK"},
    {"name": "Sydney Harbour Bridge", "lat": -33.8523, "lon": 151.2108, "span_m": 503, "type": "Steel arch", "year": 1932, "city": "Sydney", "country": "Australia"},
    {"name": "Ponte Vecchio", "lat": 43.7680, "lon": 11.2531, "span_m": 30, "type": "Stone arch", "year": 1345, "city": "Florence", "country": "Italy"},
    {"name": "Rialto Bridge", "lat": 45.4381, "lon": 12.3360, "span_m": 29, "type": "Stone arch", "year": 1591, "city": "Venice", "country": "Italy"},
    {"name": "Charles Bridge", "lat": 50.0865, "lon": 14.4114, "span_m": 516, "type": "Stone arch", "year": 1402, "city": "Prague", "country": "Czech Republic"},
    {"name": "Danyang-Kunshan Grand Bridge", "lat": 31.2500, "lon": 120.7500, "span_m": 164800, "type": "Viaduct", "year": 2010, "city": "Jiangsu", "country": "China"},
    {"name": "Tsing Ma Bridge", "lat": 22.3523, "lon": 114.0743, "span_m": 1377, "type": "Suspension", "year": 1997, "city": "Hong Kong", "country": "China"},
    {"name": "Great Belt Fixed Link", "lat": 55.3411, "lon": 11.0344, "span_m": 1624, "type": "Suspension", "year": 1998, "city": "Zealand", "country": "Denmark"},
    {"name": "Confederation Bridge", "lat": 46.2050, "lon": -63.7450, "span_m": 12900, "type": "Box girder", "year": 1997, "city": "Northumberland Strait", "country": "Canada"},
    {"name": "Vasco da Gama Bridge", "lat": 38.7640, "lon": -9.0338, "span_m": 17185, "type": "Cable-stayed", "year": 1998, "city": "Lisbon", "country": "Portugal"},
    {"name": "Humber Bridge", "lat": 53.7088, "lon": -0.4507, "span_m": 1410, "type": "Suspension", "year": 1981, "city": "Humber", "country": "UK"},
    {"name": "Pont du Gard", "lat": 43.9472, "lon": 4.5354, "span_m": 275, "type": "Roman aqueduct", "year": -19, "city": "Nimes", "country": "France"},
    {"name": "Forth Bridge", "lat": 56.0000, "lon": -3.3886, "span_m": 521, "type": "Cantilever", "year": 1890, "city": "Edinburgh", "country": "UK"},
    {"name": "Bosphorus Bridge", "lat": 41.0454, "lon": 29.0342, "span_m": 1074, "type": "Suspension", "year": 1973, "city": "Istanbul", "country": "Turkey"},
    {"name": "Sunshine Skyway Bridge", "lat": 27.6153, "lon": -82.6554, "span_m": 366, "type": "Cable-stayed", "year": 1987, "city": "Tampa Bay", "country": "USA"},
    {"name": "Øresund Bridge", "lat": 55.5719, "lon": 12.8505, "span_m": 7845, "type": "Cable-stayed", "year": 2000, "city": "Copenhagen / Malmo", "country": "Denmark / Sweden"},
    {"name": "Stari Most", "lat": 43.3373, "lon": 17.8153, "span_m": 29, "type": "Stone arch", "year": 1566, "city": "Mostar", "country": "Bosnia"},
    {"name": "Si-o-se-pol", "lat": 32.6428, "lon": 51.6694, "span_m": 298, "type": "Stone arch", "year": 1602, "city": "Isfahan", "country": "Iran"},
    {"name": "Howrah Bridge", "lat": 22.5852, "lon": 88.3468, "span_m": 457, "type": "Cantilever", "year": 1943, "city": "Kolkata", "country": "India"},
    {"name": "Chenab Bridge", "lat": 33.1500, "lon": 74.9500, "span_m": 467, "type": "Steel arch", "year": 2022, "city": "Jammu", "country": "India"},
    {"name": "Puente Nuevo", "lat": 36.7414, "lon": -5.1626, "span_m": 98, "type": "Stone arch", "year": 1793, "city": "Ronda", "country": "Spain"},
    {"name": "Khaju Bridge", "lat": 32.6388, "lon": 51.6780, "span_m": 133, "type": "Stone arch", "year": 1650, "city": "Isfahan", "country": "Iran"},
    {"name": "Russky Bridge", "lat": 43.0553, "lon": 131.9100, "span_m": 1104, "type": "Cable-stayed", "year": 2012, "city": "Vladivostok", "country": "Russia"},
    {"name": "Stonecutters Bridge", "lat": 22.3360, "lon": 114.1230, "span_m": 1018, "type": "Cable-stayed", "year": 2009, "city": "Hong Kong", "country": "China"},
    {"name": "George Washington Bridge", "lat": 40.8517, "lon": -73.9527, "span_m": 1067, "type": "Suspension", "year": 1931, "city": "New York", "country": "USA"},
    {"name": "Jiaozhou Bay Bridge", "lat": 36.1500, "lon": 120.2000, "span_m": 41580, "type": "Cross-sea bridge", "year": 2011, "city": "Qingdao", "country": "China"},
    {"name": "Sidu River Bridge", "lat": 30.4750, "lon": 109.8100, "span_m": 900, "type": "Suspension", "year": 2009, "city": "Hubei", "country": "China"},
]

MAJOR_DAMS = [
    {"name": "Three Gorges Dam", "lat": 30.8231, "lon": 111.0035, "height_m": 181, "capacity_mw": 22500, "year": 2006, "river": "Yangtze", "country": "China"},
    {"name": "Itaipu Dam", "lat": -25.4082, "lon": -54.5886, "height_m": 196, "capacity_mw": 14000, "year": 1984, "river": "Parana", "country": "Brazil / Paraguay"},
    {"name": "Guri Dam", "lat": 7.7597, "lon": -62.9786, "height_m": 162, "capacity_mw": 10235, "year": 1986, "river": "Caroni", "country": "Venezuela"},
    {"name": "Tucurui Dam", "lat": -3.8318, "lon": -49.6464, "height_m": 78, "capacity_mw": 8370, "year": 1984, "river": "Tocantins", "country": "Brazil"},
    {"name": "Grand Coulee Dam", "lat": 47.9561, "lon": -118.9817, "height_m": 168, "capacity_mw": 6809, "year": 1942, "river": "Columbia", "country": "USA"},
    {"name": "Xiangjiaba Dam", "lat": 28.6311, "lon": 104.3922, "height_m": 161, "capacity_mw": 6448, "year": 2014, "river": "Jinsha", "country": "China"},
    {"name": "Longtan Dam", "lat": 25.0256, "lon": 107.0489, "height_m": 216, "capacity_mw": 6426, "year": 2009, "river": "Hongshui", "country": "China"},
    {"name": "Sayano-Shushenskaya Dam", "lat": 52.8281, "lon": 91.3711, "height_m": 245, "capacity_mw": 6400, "year": 1978, "river": "Yenisei", "country": "Russia"},
    {"name": "Xiluodu Dam", "lat": 28.2614, "lon": 103.6458, "height_m": 286, "capacity_mw": 13860, "year": 2014, "river": "Jinsha", "country": "China"},
    {"name": "Robert-Bourassa Dam", "lat": 53.7847, "lon": -77.4536, "height_m": 162, "capacity_mw": 5616, "year": 1981, "river": "La Grande", "country": "Canada"},
    {"name": "Krasnoyarsk Dam", "lat": 55.9344, "lon": 92.2928, "height_m": 124, "capacity_mw": 6000, "year": 1972, "river": "Yenisei", "country": "Russia"},
    {"name": "Hoover Dam", "lat": 36.0160, "lon": -114.7377, "height_m": 221, "capacity_mw": 2080, "year": 1936, "river": "Colorado", "country": "USA"},
    {"name": "Aswan High Dam", "lat": 23.9708, "lon": 32.8781, "height_m": 111, "capacity_mw": 2100, "year": 1970, "river": "Nile", "country": "Egypt"},
    {"name": "Glen Canyon Dam", "lat": 36.9381, "lon": -111.4856, "height_m": 216, "capacity_mw": 1320, "year": 1966, "river": "Colorado", "country": "USA"},
    {"name": "Nurek Dam", "lat": 38.3722, "lon": 69.3208, "height_m": 300, "capacity_mw": 3000, "year": 1980, "river": "Vakhsh", "country": "Tajikistan"},
    {"name": "Jinping-I Dam", "lat": 28.1833, "lon": 101.6333, "height_m": 305, "capacity_mw": 3600, "year": 2014, "river": "Yalong", "country": "China"},
    {"name": "Rogun Dam", "lat": 38.4167, "lon": 69.1000, "height_m": 335, "capacity_mw": 3600, "year": 2025, "river": "Vakhsh", "country": "Tajikistan"},
    {"name": "Tarbela Dam", "lat": 34.0886, "lon": 72.6989, "height_m": 143, "capacity_mw": 4888, "year": 1976, "river": "Indus", "country": "Pakistan"},
    {"name": "Mangla Dam", "lat": 33.1400, "lon": 73.6400, "height_m": 147, "capacity_mw": 1000, "year": 1967, "river": "Jhelum", "country": "Pakistan"},
    {"name": "Daniel-Johnson Dam", "lat": 51.0472, "lon": -68.7214, "height_m": 214, "capacity_mw": 2660, "year": 1968, "river": "Manicouagan", "country": "Canada"},
    {"name": "Oroville Dam", "lat": 39.5408, "lon": -121.4861, "height_m": 235, "capacity_mw": 819, "year": 1968, "river": "Feather", "country": "USA"},
    {"name": "Bhakra Dam", "lat": 31.4111, "lon": 76.4333, "height_m": 226, "capacity_mw": 1325, "year": 1963, "river": "Sutlej", "country": "India"},
    {"name": "Kariba Dam", "lat": -16.5214, "lon": 28.7614, "height_m": 128, "capacity_mw": 1470, "year": 1959, "river": "Zambezi", "country": "Zambia / Zimbabwe"},
    {"name": "Ataturk Dam", "lat": 37.4986, "lon": 38.3264, "height_m": 166, "capacity_mw": 2400, "year": 1990, "river": "Euphrates", "country": "Turkey"},
    {"name": "Belo Monte Dam", "lat": -3.1208, "lon": -51.7969, "height_m": 90, "capacity_mw": 11233, "year": 2019, "river": "Xingu", "country": "Brazil"},
    {"name": "Baihetan Dam", "lat": 27.1250, "lon": 103.0500, "height_m": 289, "capacity_mw": 16000, "year": 2022, "river": "Jinsha", "country": "China"},
]

RELIGIOUS_BUILDINGS = [
    {"name": "St. Peter's Basilica", "lat": 41.9022, "lon": 12.4539, "religion": "Christianity", "year": 1626, "city": "Vatican City", "style": "Renaissance / Baroque"},
    {"name": "Hagia Sophia", "lat": 41.0086, "lon": 28.9802, "religion": "Islam (former church)", "year": 537, "city": "Istanbul", "style": "Byzantine"},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "religion": "Hinduism / Buddhism", "year": 1150, "city": "Siem Reap", "style": "Khmer"},
    {"name": "Notre-Dame de Paris", "lat": 48.8530, "lon": 2.3499, "religion": "Christianity", "year": 1345, "city": "Paris", "style": "Gothic"},
    {"name": "Sagrada Familia", "lat": 41.4036, "lon": 2.1744, "religion": "Christianity", "year": 2026, "city": "Barcelona", "style": "Art Nouveau / Gothic"},
    {"name": "Blue Mosque", "lat": 41.0054, "lon": 28.9768, "religion": "Islam", "year": 1616, "city": "Istanbul", "style": "Ottoman"},
    {"name": "Great Mosque of Mecca", "lat": 21.4225, "lon": 39.8262, "religion": "Islam", "year": 638, "city": "Mecca", "style": "Islamic"},
    {"name": "Western Wall", "lat": 31.7767, "lon": 35.2345, "religion": "Judaism", "year": -19, "city": "Jerusalem", "style": "Herodian stone"},
    {"name": "Golden Temple", "lat": 31.6200, "lon": 74.8765, "religion": "Sikhism", "year": 1604, "city": "Amritsar", "style": "Sikh / Mughal"},
    {"name": "Shwedagon Pagoda", "lat": 16.8714, "lon": 96.1498, "religion": "Buddhism", "year": 600, "city": "Yangon", "style": "Mon / Burmese"},
    {"name": "Borobudur", "lat": -7.6079, "lon": 110.2038, "religion": "Buddhism", "year": 825, "city": "Magelang", "style": "Javanese"},
    {"name": "Meenakshi Temple", "lat": 9.9195, "lon": 78.1193, "religion": "Hinduism", "year": 1623, "city": "Madurai", "style": "Dravidian"},
    {"name": "Canterbury Cathedral", "lat": 51.2796, "lon": 1.0830, "religion": "Christianity", "year": 1077, "city": "Canterbury", "style": "Gothic"},
    {"name": "Cologne Cathedral", "lat": 50.9413, "lon": 6.9580, "religion": "Christianity", "year": 1880, "city": "Cologne", "style": "Gothic"},
    {"name": "Milan Cathedral", "lat": 45.4642, "lon": 9.1917, "religion": "Christianity", "year": 1965, "city": "Milan", "style": "Gothic"},
    {"name": "St. Basil's Cathedral", "lat": 55.7525, "lon": 37.6231, "religion": "Christianity", "year": 1561, "city": "Moscow", "style": "Russian / Byzantine"},
    {"name": "Wat Phra Kaew", "lat": 13.7516, "lon": 100.4927, "religion": "Buddhism", "year": 1784, "city": "Bangkok", "style": "Thai"},
    {"name": "Kinkaku-ji", "lat": 35.0394, "lon": 135.7292, "religion": "Buddhism", "year": 1397, "city": "Kyoto", "style": "Muromachi Zen"},
    {"name": "Faisal Mosque", "lat": 33.7301, "lon": 73.0370, "religion": "Islam", "year": 1986, "city": "Islamabad", "style": "Modern / Turkish"},
    {"name": "Church of the Holy Sepulchre", "lat": 31.7785, "lon": 35.2296, "religion": "Christianity", "year": 335, "city": "Jerusalem", "style": "Romanesque"},
    {"name": "Prambanan", "lat": -7.7520, "lon": 110.4914, "religion": "Hinduism", "year": 850, "city": "Yogyakarta", "style": "Javanese Hindu"},
    {"name": "Mezquita of Cordoba", "lat": 37.8789, "lon": -4.7794, "religion": "Islam / Christianity", "year": 987, "city": "Cordoba", "style": "Moorish"},
    {"name": "Chartres Cathedral", "lat": 48.4478, "lon": 1.4875, "religion": "Christianity", "year": 1220, "city": "Chartres", "style": "Gothic"},
    {"name": "Sheikh Zayed Grand Mosque", "lat": 24.4128, "lon": 54.4750, "religion": "Islam", "year": 2007, "city": "Abu Dhabi", "style": "Modern Islamic"},
    {"name": "Potala Palace", "lat": 29.6573, "lon": 91.1170, "religion": "Buddhism", "year": 1649, "city": "Lhasa", "style": "Tibetan"},
]

FAMOUS_TOWERS = [
    {"name": "Eiffel Tower", "lat": 48.8584, "lon": 2.2945, "height_m": 330, "year": 1889, "city": "Paris", "country": "France", "type": "Lattice tower"},
    {"name": "CN Tower", "lat": 43.6426, "lon": -79.3871, "height_m": 553, "year": 1976, "city": "Toronto", "country": "Canada", "type": "Communications tower"},
    {"name": "Tokyo Skytree", "lat": 35.7101, "lon": 139.8107, "height_m": 634, "year": 2012, "city": "Tokyo", "country": "Japan", "type": "Broadcasting tower"},
    {"name": "Canton Tower", "lat": 23.1064, "lon": 113.3245, "height_m": 604, "year": 2010, "city": "Guangzhou", "country": "China", "type": "Observation tower"},
    {"name": "Ostankino Tower", "lat": 55.8197, "lon": 37.6117, "height_m": 540, "year": 1967, "city": "Moscow", "country": "Russia", "type": "Television tower"},
    {"name": "Oriental Pearl Tower", "lat": 31.2397, "lon": 121.4998, "height_m": 468, "year": 1994, "city": "Shanghai", "country": "China", "type": "Television tower"},
    {"name": "Milad Tower", "lat": 35.7448, "lon": 51.3753, "height_m": 435, "year": 2008, "city": "Tehran", "country": "Iran", "type": "Telecommunications tower"},
    {"name": "KL Tower", "lat": 3.1528, "lon": 101.7036, "height_m": 421, "year": 1995, "city": "Kuala Lumpur", "country": "Malaysia", "type": "Telecommunications tower"},
    {"name": "Tianjin Radio and TV Tower", "lat": 39.0800, "lon": 117.2100, "height_m": 415, "year": 1991, "city": "Tianjin", "country": "China", "type": "Television tower"},
    {"name": "Macau Tower", "lat": 22.1800, "lon": 113.5280, "height_m": 338, "year": 2001, "city": "Macau", "country": "China", "type": "Observation tower"},
    {"name": "Berlin TV Tower", "lat": 52.5208, "lon": 13.4094, "height_m": 368, "year": 1969, "city": "Berlin", "country": "Germany", "type": "Television tower"},
    {"name": "Sky Tower Auckland", "lat": -36.8485, "lon": 174.7622, "height_m": 328, "year": 1997, "city": "Auckland", "country": "New Zealand", "type": "Observation tower"},
    {"name": "Stratosphere Tower", "lat": 36.1474, "lon": -115.1558, "height_m": 350, "year": 1996, "city": "Las Vegas", "country": "USA", "type": "Observation tower"},
    {"name": "Sydney Tower Eye", "lat": -33.8705, "lon": 151.2089, "height_m": 309, "year": 1981, "city": "Sydney", "country": "Australia", "type": "Observation tower"},
    {"name": "Leaning Tower of Pisa", "lat": 43.7230, "lon": 10.3966, "height_m": 56, "year": 1372, "city": "Pisa", "country": "Italy", "type": "Bell tower"},
    {"name": "Space Needle", "lat": 47.6205, "lon": -122.3493, "height_m": 184, "year": 1962, "city": "Seattle", "country": "USA", "type": "Observation tower"},
    {"name": "Juche Tower", "lat": 39.0137, "lon": 125.7764, "height_m": 170, "year": 1982, "city": "Pyongyang", "country": "North Korea", "type": "Monument tower"},
    {"name": "Tokyo Tower", "lat": 35.6586, "lon": 139.7454, "height_m": 333, "year": 1958, "city": "Tokyo", "country": "Japan", "type": "Communications tower"},
    {"name": "N Seoul Tower", "lat": 37.5512, "lon": 126.9882, "height_m": 236, "year": 1975, "city": "Seoul", "country": "South Korea", "type": "Communications tower"},
    {"name": "Blackpool Tower", "lat": 53.8159, "lon": -3.0553, "height_m": 158, "year": 1894, "city": "Blackpool", "country": "UK", "type": "Observation tower"},
    {"name": "Calgary Tower", "lat": 51.0443, "lon": -114.0632, "height_m": 191, "year": 1968, "city": "Calgary", "country": "Canada", "type": "Observation tower"},
    {"name": "Reunion Tower", "lat": 32.7753, "lon": -96.8091, "height_m": 171, "year": 1978, "city": "Dallas", "country": "USA", "type": "Observation tower"},
    {"name": "Spinnaker Tower", "lat": 50.7954, "lon": -1.1087, "height_m": 170, "year": 2005, "city": "Portsmouth", "country": "UK", "type": "Observation tower"},
    {"name": "Avala Tower", "lat": 44.6908, "lon": 20.5139, "height_m": 205, "year": 2010, "city": "Belgrade", "country": "Serbia", "type": "Telecommunications tower"},
    {"name": "Lotus Tower", "lat": 6.9275, "lon": 79.8580, "height_m": 356, "year": 2019, "city": "Colombo", "country": "Sri Lanka", "type": "Telecommunications tower"},
]

ANCIENT_RUINS = [
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "civilization": "Inca", "era": "15th century", "country": "Peru", "type": "Citadel"},
    {"name": "Pompeii", "lat": 40.7509, "lon": 14.4869, "civilization": "Roman", "era": "7th century BC", "country": "Italy", "type": "City"},
    {"name": "Petra", "lat": 30.3285, "lon": 35.4444, "civilization": "Nabataean", "era": "312 BC", "country": "Jordan", "type": "Rock-cut city"},
    {"name": "Roman Colosseum", "lat": 41.8902, "lon": 12.4922, "civilization": "Roman", "era": "70-80 AD", "country": "Italy", "type": "Amphitheatre"},
    {"name": "Parthenon", "lat": 37.9715, "lon": 23.7267, "civilization": "Greek", "era": "447 BC", "country": "Greece", "type": "Temple"},
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678, "civilization": "Maya", "era": "600 AD", "country": "Mexico", "type": "City / Temple"},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438, "civilization": "Mesoamerican", "era": "100 BC", "country": "Mexico", "type": "City"},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "civilization": "Neolithic", "era": "3000 BC", "country": "UK", "type": "Stone circle"},
    {"name": "Great Zimbabwe", "lat": -20.2674, "lon": 30.9336, "civilization": "Shona", "era": "11th century", "country": "Zimbabwe", "type": "Stone enclosure"},
    {"name": "Ephesus", "lat": 37.9411, "lon": 27.3419, "civilization": "Greek / Roman", "era": "10th century BC", "country": "Turkey", "type": "City"},
    {"name": "Persepolis", "lat": 29.9352, "lon": 52.8914, "civilization": "Persian", "era": "515 BC", "country": "Iran", "type": "Palace complex"},
    {"name": "Tikal", "lat": 17.2220, "lon": -89.6237, "civilization": "Maya", "era": "4th century BC", "country": "Guatemala", "type": "City"},
    {"name": "Luxor Temple", "lat": 25.6996, "lon": 32.6390, "civilization": "Egyptian", "era": "1400 BC", "country": "Egypt", "type": "Temple"},
    {"name": "Karnak Temple", "lat": 25.7188, "lon": 32.6573, "civilization": "Egyptian", "era": "2000 BC", "country": "Egypt", "type": "Temple complex"},
    {"name": "Roman Forum", "lat": 41.8925, "lon": 12.4853, "civilization": "Roman", "era": "7th century BC", "country": "Italy", "type": "Public plaza"},
    {"name": "Delphi", "lat": 38.4824, "lon": 22.5010, "civilization": "Greek", "era": "8th century BC", "country": "Greece", "type": "Sanctuary"},
    {"name": "Palmyra", "lat": 34.5503, "lon": 38.2669, "civilization": "Roman / Semitic", "era": "2nd millennium BC", "country": "Syria", "type": "City"},
    {"name": "Mohenjo-daro", "lat": 27.3242, "lon": 68.1358, "civilization": "Indus Valley", "era": "2500 BC", "country": "Pakistan", "type": "City"},
    {"name": "Hampi", "lat": 15.3350, "lon": 76.4600, "civilization": "Vijayanagara", "era": "14th century", "country": "India", "type": "City / Temples"},
    {"name": "Mesa Verde", "lat": 37.1838, "lon": -108.4887, "civilization": "Ancestral Puebloan", "era": "600 AD", "country": "USA", "type": "Cliff dwellings"},
    {"name": "Angkor Thom", "lat": 13.4411, "lon": 103.8573, "civilization": "Khmer", "era": "12th century", "country": "Cambodia", "type": "City"},
    {"name": "Baalbek", "lat": 34.0069, "lon": 36.2039, "civilization": "Phoenician / Roman", "era": "9000 BC", "country": "Lebanon", "type": "Temple complex"},
    {"name": "Troy", "lat": 39.9575, "lon": 26.2388, "civilization": "Bronze Age", "era": "3000 BC", "country": "Turkey", "type": "City"},
    {"name": "Knossos", "lat": 35.2981, "lon": 25.1631, "civilization": "Minoan", "era": "1900 BC", "country": "Greece", "type": "Palace"},
    {"name": "Palenque", "lat": 17.4840, "lon": -92.0461, "civilization": "Maya", "era": "226 BC", "country": "Mexico", "type": "City"},
    {"name": "Herculaneum", "lat": 40.8058, "lon": 14.3471, "civilization": "Roman", "era": "7th century BC", "country": "Italy", "type": "City"},
    {"name": "Mycenae", "lat": 37.7308, "lon": 22.7564, "civilization": "Mycenaean", "era": "1600 BC", "country": "Greece", "type": "Citadel"},
    {"name": "Tulum", "lat": 20.2145, "lon": -87.4291, "civilization": "Maya", "era": "564 AD", "country": "Mexico", "type": "Walled city"},
    {"name": "Volubilis", "lat": 34.0733, "lon": -5.5536, "civilization": "Roman / Berber", "era": "3rd century BC", "country": "Morocco", "type": "City"},
    {"name": "Jerash", "lat": 32.2747, "lon": 35.8911, "civilization": "Greco-Roman", "era": "2nd century BC", "country": "Jordan", "type": "City"},
]

MODERN_MARVELS = [
    {"name": "Sydney Opera House", "lat": -33.8568, "lon": 151.2153, "architect": "Jorn Utzon", "year": 1973, "city": "Sydney", "country": "Australia", "type": "Performing arts"},
    {"name": "Guggenheim Museum Bilbao", "lat": 43.2687, "lon": -2.9340, "architect": "Frank Gehry", "year": 1997, "city": "Bilbao", "country": "Spain", "type": "Museum"},
    {"name": "Burj Al Arab", "lat": 25.1413, "lon": 55.1853, "architect": "Tom Wright", "year": 1999, "city": "Dubai", "country": "UAE", "type": "Hotel"},
    {"name": "The Louvre Pyramid", "lat": 48.8611, "lon": 2.3358, "architect": "I. M. Pei", "year": 1989, "city": "Paris", "country": "France", "type": "Museum entrance"},
    {"name": "Walt Disney Concert Hall", "lat": 34.0553, "lon": -118.2498, "architect": "Frank Gehry", "year": 2003, "city": "Los Angeles", "country": "USA", "type": "Concert hall"},
    {"name": "Beijing National Stadium", "lat": 39.9929, "lon": 116.3969, "architect": "Herzog & de Meuron", "year": 2008, "city": "Beijing", "country": "China", "type": "Stadium"},
    {"name": "Marina Bay Sands", "lat": 1.2834, "lon": 103.8607, "architect": "Moshe Safdie", "year": 2010, "city": "Singapore", "country": "Singapore", "type": "Resort"},
    {"name": "Lotus Temple", "lat": 28.5535, "lon": 77.2588, "architect": "Fariborz Sahba", "year": 1986, "city": "New Delhi", "country": "India", "type": "House of worship"},
    {"name": "The Gherkin (30 St Mary Axe)", "lat": 51.5145, "lon": -0.0803, "architect": "Norman Foster", "year": 2003, "city": "London", "country": "UK", "type": "Office tower"},
    {"name": "Fallingwater", "lat": 39.9064, "lon": -79.4682, "architect": "Frank Lloyd Wright", "year": 1939, "city": "Mill Run", "country": "USA", "type": "Residence"},
    {"name": "Heydar Aliyev Center", "lat": 40.3959, "lon": 49.8679, "architect": "Zaha Hadid", "year": 2012, "city": "Baku", "country": "Azerbaijan", "type": "Cultural center"},
    {"name": "CCTV Headquarters", "lat": 39.9155, "lon": 116.4586, "architect": "Rem Koolhaas / OMA", "year": 2012, "city": "Beijing", "country": "China", "type": "Office"},
    {"name": "Turning Torso", "lat": 55.6133, "lon": 12.9756, "architect": "Santiago Calatrava", "year": 2005, "city": "Malmo", "country": "Sweden", "type": "Residential tower"},
    {"name": "The Vessel (Hudson Yards)", "lat": 40.7536, "lon": -74.0023, "architect": "Thomas Heatherwick", "year": 2019, "city": "New York", "country": "USA", "type": "Public landmark"},
    {"name": "Guangzhou Opera House", "lat": 23.1155, "lon": 113.3213, "architect": "Zaha Hadid", "year": 2010, "city": "Guangzhou", "country": "China", "type": "Opera house"},
    {"name": "One Central Park", "lat": -33.8922, "lon": 151.1979, "architect": "Jean Nouvel", "year": 2014, "city": "Sydney", "country": "Australia", "type": "Residential"},
    {"name": "Museum of the Future", "lat": 25.2195, "lon": 55.2803, "architect": "Killa Design", "year": 2022, "city": "Dubai", "country": "UAE", "type": "Museum"},
    {"name": "Metropol Parasol", "lat": 37.3932, "lon": -5.9917, "architect": "Jurgen Mayer", "year": 2011, "city": "Seville", "country": "Spain", "type": "Public structure"},
    {"name": "Bosco Verticale", "lat": 45.4856, "lon": 9.1899, "architect": "Stefano Boeri", "year": 2014, "city": "Milan", "country": "Italy", "type": "Residential tower"},
    {"name": "The Oculus (WTC Hub)", "lat": 40.7113, "lon": -74.0113, "architect": "Santiago Calatrava", "year": 2016, "city": "New York", "country": "USA", "type": "Transport hub"},
    {"name": "Gardens by the Bay", "lat": 1.2816, "lon": 103.8636, "architect": "Wilkinson Eyre / Grant Associates", "year": 2012, "city": "Singapore", "country": "Singapore", "type": "Garden / Conservatory"},
    {"name": "MAAT Museum", "lat": 38.6964, "lon": -9.1911, "architect": "Amanda Levete", "year": 2016, "city": "Lisbon", "country": "Portugal", "type": "Museum"},
    {"name": "National Museum of Qatar", "lat": 25.2867, "lon": 51.5489, "architect": "Jean Nouvel", "year": 2019, "city": "Doha", "country": "Qatar", "type": "Museum"},
    {"name": "Apple Park", "lat": 37.3349, "lon": -122.0090, "architect": "Norman Foster", "year": 2017, "city": "Cupertino", "country": "USA", "type": "Corporate campus"},
    {"name": "Centre Pompidou", "lat": 48.8607, "lon": 2.3522, "architect": "Renzo Piano / Richard Rogers", "year": 1977, "city": "Paris", "country": "France", "type": "Cultural center"},
]


# ---------------------------------------------------------------------------
# Map type registry
# ---------------------------------------------------------------------------

MAP_TYPES = [
    "Tallest Buildings",
    "World Wonders",
    "Famous Bridges",
    "Major Dams",
    "Castles",
    "Lighthouses",
    "Religious Buildings",
    "Famous Towers",
    "Ancient Ruins",
    "Modern Marvels",
]

MAP_DESCRIPTIONS = {
    "Tallest Buildings": "Explore 40+ of the world's tallest skyscrapers with height, floors, and year of completion.",
    "World Wonders": "The 7 Ancient, 7 New, and 7 Natural Wonders of the World on a single map.",
    "Famous Bridges": "30+ iconic bridges worldwide including suspension, arch, cable-stayed, and ancient spans.",
    "Major Dams": "25+ major hydroelectric and reservoir dams with height and generation capacity.",
    "Castles": "Search for castles and fortifications in a region via OpenStreetMap Overpass API.",
    "Lighthouses": "Search for lighthouses in a coastal region via OpenStreetMap Overpass API.",
    "Religious Buildings": "25+ of the world's most iconic temples, churches, mosques, and sacred sites.",
    "Famous Towers": "25+ observation, communications, and historic towers from the Eiffel Tower to Tokyo Skytree.",
    "Ancient Ruins": "30+ archaeological sites from Machu Picchu to Pompeii, spanning millennia of civilization.",
    "Modern Marvels": "25+ contemporary architectural masterpieces with their visionary architects.",
}

# Colors per map type for markers
MAP_COLORS = {
    "Tallest Buildings": "#06b6d4",
    "World Wonders": "#f59e0b",
    "Famous Bridges": "#8b5cf6",
    "Major Dams": "#3b82f6",
    "Castles": "#a855f7",
    "Lighthouses": "#f97316",
    "Religious Buildings": "#10b981",
    "Famous Towers": "#ec4899",
    "Ancient Ruins": "#ef4444",
    "Modern Marvels": "#14b8a6",
}

# Overpass presets for castles and lighthouses
CASTLE_PRESETS = {
    "Custom": None,
    "England": {"lat": 52.0, "lon": -1.5, "radius": 200},
    "Scotland": {"lat": 56.5, "lon": -4.0, "radius": 150},
    "France - Loire Valley": {"lat": 47.4, "lon": 1.0, "radius": 100},
    "Germany - Rhine Valley": {"lat": 50.4, "lon": 7.6, "radius": 80},
    "Spain - Castilla": {"lat": 39.5, "lon": -3.0, "radius": 150},
    "Italy - Tuscany": {"lat": 43.3, "lon": 11.3, "radius": 80},
    "Romania - Transylvania": {"lat": 46.0, "lon": 24.5, "radius": 100},
    "Japan - Kansai": {"lat": 34.7, "lon": 135.5, "radius": 80},
    "Wales": {"lat": 52.0, "lon": -3.5, "radius": 100},
    "Ireland": {"lat": 53.5, "lon": -7.5, "radius": 150},
}

LIGHTHOUSE_PRESETS = {
    "Custom": None,
    "UK - South Coast": {"lat": 50.7, "lon": -1.3, "radius": 100},
    "France - Brittany": {"lat": 48.5, "lon": -3.5, "radius": 100},
    "Norway - Coast": {"lat": 62.0, "lon": 6.0, "radius": 150},
    "USA - New England": {"lat": 42.0, "lon": -70.5, "radius": 100},
    "USA - Pacific Northwest": {"lat": 46.5, "lon": -124.0, "radius": 100},
    "Greece - Aegean": {"lat": 37.5, "lon": 25.0, "radius": 120},
    "Italy - Sardinia": {"lat": 40.0, "lon": 9.5, "radius": 80},
    "Japan - Pacific Coast": {"lat": 35.0, "lon": 140.0, "radius": 100},
    "Australia - Victoria": {"lat": -38.5, "lon": 144.5, "radius": 100},
    "Portugal - Atlantic": {"lat": 39.0, "lon": -9.3, "radius": 80},
}


# ---------------------------------------------------------------------------
# Overpass queries (castles & lighthouses)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _fetch_castles(lat: float, lon: float, radius_km: float) -> list[dict]:
    """Fetch castles via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:90];
(
  node["historic"="castle"](around:{radius_m},{lat},{lon});
  way["historic"="castle"](around:{radius_m},{lat},{lon});
  relation["historic"="castle"](around:{radius_m},{lat},{lon});
);
out center body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        st.warning(f"Overpass query failed: {err}")
        return []
    elements = result.get("elements", [])
    castles = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}).get("lat"))
        lon_v = el.get("lon") or (el.get("center", {}).get("lon"))
        if lat_v is None or lon_v is None:
            continue
        tags = el.get("tags", {})
        name = tags.get("name", "Unnamed castle")
        castle_type = tags.get("castle_type", tags.get("historic:civilization", "unknown"))
        period = tags.get("start_date", tags.get("heritage:operator", "unknown"))
        wikipedia = tags.get("wikipedia", "")
        castles.append({
            "name": name,
            "lat": lat_v,
            "lon": lon_v,
            "castle_type": castle_type,
            "period": period,
            "wikipedia": wikipedia,
        })
    return castles


@st.cache_data(ttl=3600)
def _fetch_lighthouses(lat: float, lon: float, radius_km: float) -> list[dict]:
    """Fetch lighthouses via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:90];
(
  node["man_made"="lighthouse"](around:{radius_m},{lat},{lon});
  way["man_made"="lighthouse"](around:{radius_m},{lat},{lon});
);
out center body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        st.warning(f"Overpass query failed: {err}")
        return []
    elements = result.get("elements", [])
    lighthouses = []
    for el in elements:
        lat_v = el.get("lat") or (el.get("center", {}).get("lat"))
        lon_v = el.get("lon") or (el.get("center", {}).get("lon"))
        if lat_v is None or lon_v is None:
            continue
        tags = el.get("tags", {})
        name = tags.get("name", "Unnamed lighthouse")
        height = tags.get("height", "unknown")
        ref = tags.get("ref", "")
        wikipedia = tags.get("wikipedia", "")
        lighthouses.append({
            "name": name,
            "lat": lat_v,
            "lon": lon_v,
            "height": height,
            "ref": ref,
            "wikipedia": wikipedia,
        })
    return lighthouses


# ---------------------------------------------------------------------------
# Map builders
# ---------------------------------------------------------------------------

def _build_tallest_buildings_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of the world's tallest buildings."""
    m = folium.Map(
        location=[25.0, 50.0],
        zoom_start=3,
        tiles="CartoDB dark_matter",
    )
    color = MAP_COLORS["Tallest Buildings"]
    for b in TALLEST_BUILDINGS:
        popup_html = (
            f"<b>{html.escape(b['name'])}</b><br>"
            f"Height: {b['height_m']} m<br>"
            f"Floors: {b['floors']}<br>"
            f"Year: {b['year']}<br>"
            f"City: {html.escape(b['city'])}, {html.escape(b['country'])}"
        )
        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=max(4, b["height_m"] / 80),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(b["name"]),
        ).add_to(m)
    df = pd.DataFrame(TALLEST_BUILDINGS)
    df = df.sort_values("height_m", ascending=False).reset_index(drop=True)
    return m, df


def _build_world_wonders_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of the Wonders of the World."""
    cat_colors = {
        "Ancient": "#f59e0b",
        "New": "#06b6d4",
        "Natural": "#10b981",
    }
    m = folium.Map(
        location=[20.0, 20.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )
    for w in WORLD_WONDERS:
        color = cat_colors.get(w["category"], "#8b5cf6")
        popup_html = (
            f"<b>{html.escape(w['name'])}</b><br>"
            f"Category: {html.escape(w['category'])} Wonder<br>"
            f"Year: {html.escape(str(w['year']))}<br>"
            f"Location: {html.escape(w['location'])}<br>"
            f"Status: {html.escape(w['status'])}"
        )
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(w["name"]),
        ).add_to(m)
    df = pd.DataFrame(WORLD_WONDERS)
    return m, df


def _build_famous_bridges_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of famous bridges."""
    m = folium.Map(
        location=[30.0, 10.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )
    color = MAP_COLORS["Famous Bridges"]
    for b in FAMOUS_BRIDGES:
        popup_html = (
            f"<b>{html.escape(b['name'])}</b><br>"
            f"Span: {b['span_m']:,} m<br>"
            f"Type: {html.escape(b['type'])}<br>"
            f"Year: {b['year']}<br>"
            f"Location: {html.escape(b['city'])}, {html.escape(b['country'])}"
        )
        radius = max(4, min(12, b["span_m"] / 3000))
        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(b["name"]),
        ).add_to(m)
    df = pd.DataFrame(FAMOUS_BRIDGES)
    df = df.sort_values("span_m", ascending=False).reset_index(drop=True)
    return m, df


def _build_major_dams_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of major dams."""
    m = folium.Map(
        location=[25.0, 30.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )
    color = MAP_COLORS["Major Dams"]
    for d in MAJOR_DAMS:
        popup_html = (
            f"<b>{html.escape(d['name'])}</b><br>"
            f"Height: {d['height_m']} m<br>"
            f"Capacity: {d['capacity_mw']:,} MW<br>"
            f"Year: {d['year']}<br>"
            f"River: {html.escape(d['river'])}<br>"
            f"Country: {html.escape(d['country'])}"
        )
        radius = max(4, d["capacity_mw"] / 2000)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=min(radius, 14),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(MAJOR_DAMS)
    df = df.sort_values("capacity_mw", ascending=False).reset_index(drop=True)
    return m, df


def _build_castles_map(castles: list[dict]) -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of castles from Overpass data."""
    if not castles:
        m = folium.Map(location=[50.0, 5.0], zoom_start=5, tiles="CartoDB dark_matter")
        return m, pd.DataFrame()
    avg_lat = sum(c["lat"] for c in castles) / len(castles)
    avg_lon = sum(c["lon"] for c in castles) / len(castles)
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=7,
        tiles="CartoDB dark_matter",
    )
    color = MAP_COLORS["Castles"]
    for c in castles:
        popup_html = (
            f"<b>{html.escape(c['name'])}</b><br>"
            f"Type: {html.escape(str(c['castle_type']))}<br>"
            f"Period: {html.escape(str(c['period']))}"
        )
        if c["wikipedia"]:
            wiki_link = html.escape(c["wikipedia"])
            popup_html += f"<br><a href='https://en.wikipedia.org/wiki/{wiki_link}' target='_blank'>Wikipedia</a>"
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(c["name"]),
        ).add_to(m)
    df = pd.DataFrame(castles)
    return m, df


def _build_lighthouses_map(lighthouses: list[dict]) -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of lighthouses from Overpass data."""
    if not lighthouses:
        m = folium.Map(location=[50.0, -3.0], zoom_start=5, tiles="CartoDB dark_matter")
        return m, pd.DataFrame()
    avg_lat = sum(lh["lat"] for lh in lighthouses) / len(lighthouses)
    avg_lon = sum(lh["lon"] for lh in lighthouses) / len(lighthouses)
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=7,
        tiles="CartoDB dark_matter",
    )
    color = MAP_COLORS["Lighthouses"]
    for lh in lighthouses:
        popup_html = (
            f"<b>{html.escape(lh['name'])}</b><br>"
            f"Height: {html.escape(str(lh['height']))}<br>"
            f"Ref: {html.escape(str(lh['ref']))}"
        )
        if lh["wikipedia"]:
            wiki_link = html.escape(lh["wikipedia"])
            popup_html += f"<br><a href='https://en.wikipedia.org/wiki/{wiki_link}' target='_blank'>Wikipedia</a>"
        folium.CircleMarker(
            location=[lh["lat"], lh["lon"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(lh["name"]),
        ).add_to(m)
    df = pd.DataFrame(lighthouses)
    return m, df


def _build_religious_buildings_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of iconic religious buildings."""
    religion_colors = {
        "Christianity": "#3b82f6",
        "Islam": "#10b981",
        "Islam (former church)": "#14b8a6",
        "Islam / Christianity": "#06b6d4",
        "Buddhism": "#f59e0b",
        "Hinduism": "#ef4444",
        "Hinduism / Buddhism": "#f97316",
        "Judaism": "#a855f7",
        "Sikhism": "#ec4899",
    }
    m = folium.Map(
        location=[25.0, 40.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )
    for rb in RELIGIOUS_BUILDINGS:
        color = religion_colors.get(rb["religion"], "#8b97b0")
        popup_html = (
            f"<b>{html.escape(rb['name'])}</b><br>"
            f"Religion: {html.escape(rb['religion'])}<br>"
            f"Year: {rb['year']}<br>"
            f"City: {html.escape(rb['city'])}<br>"
            f"Style: {html.escape(rb['style'])}"
        )
        folium.CircleMarker(
            location=[rb["lat"], rb["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(rb["name"]),
        ).add_to(m)
    df = pd.DataFrame(RELIGIOUS_BUILDINGS)
    return m, df


def _build_famous_towers_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of famous towers."""
    m = folium.Map(
        location=[30.0, 20.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )
    color = MAP_COLORS["Famous Towers"]
    for t in FAMOUS_TOWERS:
        popup_html = (
            f"<b>{html.escape(t['name'])}</b><br>"
            f"Height: {t['height_m']} m<br>"
            f"Year: {t['year']}<br>"
            f"Type: {html.escape(t['type'])}<br>"
            f"City: {html.escape(t['city'])}, {html.escape(t['country'])}"
        )
        radius = max(4, t["height_m"] / 50)
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=min(radius, 14),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(t["name"]),
        ).add_to(m)
    df = pd.DataFrame(FAMOUS_TOWERS)
    df = df.sort_values("height_m", ascending=False).reset_index(drop=True)
    return m, df


def _build_ancient_ruins_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of ancient ruins."""
    civ_colors = {
        "Roman": "#ef4444",
        "Greek": "#3b82f6",
        "Greek / Roman": "#6366f1",
        "Greco-Roman": "#6366f1",
        "Egyptian": "#f59e0b",
        "Maya": "#10b981",
        "Inca": "#f97316",
        "Mesoamerican": "#14b8a6",
        "Nabataean": "#ec4899",
        "Khmer": "#a855f7",
        "Persian": "#8b5cf6",
        "Neolithic": "#64748b",
        "Shona": "#d97706",
        "Minoan": "#06b6d4",
        "Mycenaean": "#0ea5e9",
        "Bronze Age": "#78716c",
        "Indus Valley": "#ea580c",
        "Vijayanagara": "#dc2626",
        "Phoenician / Roman": "#be123c",
        "Ancestral Puebloan": "#65a30d",
        "Roman / Semitic": "#e11d48",
        "Roman / Berber": "#c026d3",
    }
    m = folium.Map(
        location=[25.0, 20.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )
    for r in ANCIENT_RUINS:
        color = civ_colors.get(r["civilization"], "#8b97b0")
        popup_html = (
            f"<b>{html.escape(r['name'])}</b><br>"
            f"Civilization: {html.escape(r['civilization'])}<br>"
            f"Era: {html.escape(r['era'])}<br>"
            f"Type: {html.escape(r['type'])}<br>"
            f"Country: {html.escape(r['country'])}"
        )
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(r["name"]),
        ).add_to(m)
    df = pd.DataFrame(ANCIENT_RUINS)
    return m, df


def _build_modern_marvels_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of modern architectural marvels."""
    m = folium.Map(
        location=[25.0, 20.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )
    color = MAP_COLORS["Modern Marvels"]
    for mm in MODERN_MARVELS:
        popup_html = (
            f"<b>{html.escape(mm['name'])}</b><br>"
            f"Architect: {html.escape(mm['architect'])}<br>"
            f"Year: {mm['year']}<br>"
            f"Type: {html.escape(mm['type'])}<br>"
            f"City: {html.escape(mm['city'])}, {html.escape(mm['country'])}"
        )
        folium.CircleMarker(
            location=[mm["lat"], mm["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=html.escape(mm["name"]),
        ).add_to(m)
    df = pd.DataFrame(MODERN_MARVELS)
    df = df.sort_values("year", ascending=False).reset_index(drop=True)
    return m, df


# ---------------------------------------------------------------------------
# Statistics renderers
# ---------------------------------------------------------------------------

def _render_stats_tallest_buildings():
    """Render summary statistics for tallest buildings."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Buildings", len(TALLEST_BUILDINGS))
    tallest = max(TALLEST_BUILDINGS, key=lambda b: b["height_m"])
    c2.metric("Tallest", f"{tallest['height_m']} m")
    countries = len(set(b["country"] for b in TALLEST_BUILDINGS))
    c3.metric("Countries", countries)
    oldest = min(TALLEST_BUILDINGS, key=lambda b: b["year"])
    c4.metric("Oldest", f"{oldest['name']} ({oldest['year']})")


def _render_stats_world_wonders():
    """Render summary statistics for world wonders."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Wonders", len(WORLD_WONDERS))
    ancient = sum(1 for w in WORLD_WONDERS if w["category"] == "Ancient")
    c2.metric("Ancient Wonders", ancient)
    new = sum(1 for w in WORLD_WONDERS if w["category"] == "New")
    c3.metric("New Wonders", new)
    natural = sum(1 for w in WORLD_WONDERS if w["category"] == "Natural")
    c4.metric("Natural Wonders", natural)


def _render_stats_famous_bridges():
    """Render summary statistics for famous bridges."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Bridges", len(FAMOUS_BRIDGES))
    longest = max(FAMOUS_BRIDGES, key=lambda b: b["span_m"])
    c2.metric("Longest Span", f"{longest['span_m']:,} m")
    countries = len(set(b["country"] for b in FAMOUS_BRIDGES))
    c3.metric("Countries", countries)
    bridge_types = len(set(b["type"] for b in FAMOUS_BRIDGES))
    c4.metric("Bridge Types", bridge_types)


def _render_stats_major_dams():
    """Render summary statistics for major dams."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Dams", len(MAJOR_DAMS))
    biggest = max(MAJOR_DAMS, key=lambda d: d["capacity_mw"])
    c2.metric("Largest Capacity", f"{biggest['capacity_mw']:,} MW")
    tallest_dam = max(MAJOR_DAMS, key=lambda d: d["height_m"])
    c3.metric("Tallest Dam", f"{tallest_dam['height_m']} m")
    total_mw = sum(d["capacity_mw"] for d in MAJOR_DAMS)
    c4.metric("Total Capacity", f"{total_mw:,} MW")


def _render_stats_castles(castles: list[dict]):
    """Render summary statistics for castles."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Castles Found", len(castles))
    named = sum(1 for c in castles if c["name"] != "Unnamed castle")
    c2.metric("Named Castles", named)
    types = len(set(c["castle_type"] for c in castles if c["castle_type"] != "unknown"))
    c3.metric("Castle Types", types)


def _render_stats_lighthouses(lighthouses: list[dict]):
    """Render summary statistics for lighthouses."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Lighthouses Found", len(lighthouses))
    named = sum(1 for lh in lighthouses if lh["name"] != "Unnamed lighthouse")
    c2.metric("Named", named)
    with_ref = sum(1 for lh in lighthouses if lh["ref"])
    c3.metric("With Reference", with_ref)


def _render_stats_religious():
    """Render summary statistics for religious buildings."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(RELIGIOUS_BUILDINGS))
    religions = len(set(rb["religion"] for rb in RELIGIOUS_BUILDINGS))
    c2.metric("Religions", religions)
    oldest = min(RELIGIOUS_BUILDINGS, key=lambda rb: rb["year"])
    c3.metric("Oldest Year", oldest["year"])
    styles = len(set(rb["style"] for rb in RELIGIOUS_BUILDINGS))
    c4.metric("Styles", styles)


def _render_stats_famous_towers():
    """Render summary statistics for famous towers."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Towers", len(FAMOUS_TOWERS))
    tallest = max(FAMOUS_TOWERS, key=lambda t: t["height_m"])
    c2.metric("Tallest", f"{tallest['height_m']} m")
    countries = len(set(t["country"] for t in FAMOUS_TOWERS))
    c3.metric("Countries", countries)
    oldest = min(FAMOUS_TOWERS, key=lambda t: t["year"])
    c4.metric("Oldest", f"{oldest['name']} ({oldest['year']})")


def _render_stats_ancient_ruins():
    """Render summary statistics for ancient ruins."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(ANCIENT_RUINS))
    civs = len(set(r["civilization"] for r in ANCIENT_RUINS))
    c2.metric("Civilizations", civs)
    countries = len(set(r["country"] for r in ANCIENT_RUINS))
    c3.metric("Countries", countries)
    types = len(set(r["type"] for r in ANCIENT_RUINS))
    c4.metric("Site Types", types)


def _render_stats_modern_marvels():
    """Render summary statistics for modern marvels."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Marvels", len(MODERN_MARVELS))
    architects = len(set(mm["architect"] for mm in MODERN_MARVELS))
    c2.metric("Architects", architects)
    countries = len(set(mm["country"] for mm in MODERN_MARVELS))
    c3.metric("Countries", countries)
    newest = max(MODERN_MARVELS, key=lambda mm: mm["year"])
    c4.metric("Newest", f"{newest['name']} ({newest['year']})")


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_architecture_maps_tab():
    """Render the Architecture & Monuments tab in the Streamlit app."""

    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Architecture &amp; Monuments</h4>"
        "<p>Explore iconic buildings, bridges, towers, ruins, and modern masterpieces worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ----- Controls -----
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_map = st.selectbox(
            "Select Map Type",
            MAP_TYPES,
            index=0,
            key="architecture_map_type",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button("Generate Map", key="architecture_generate", type="primary")

    st.caption(MAP_DESCRIPTIONS.get(selected_map, ""))

    # ----- Extra controls for Overpass-based maps -----
    overpass_data = None
    if selected_map == "Castles":
        preset_name = st.selectbox("Region Preset", list(CASTLE_PRESETS.keys()), key="castle_preset")
        preset = CASTLE_PRESETS[preset_name]
        if preset is None:
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                c_lat = st.number_input("Latitude", value=51.5, key="castle_lat")
            with cc2:
                c_lon = st.number_input("Longitude", value=-1.0, key="castle_lon")
            with cc3:
                c_radius = st.number_input("Radius (km)", value=100, min_value=10, max_value=500, key="castle_radius")
        else:
            c_lat = preset["lat"]
            c_lon = preset["lon"]
            c_radius = preset["radius"]

    elif selected_map == "Lighthouses":
        preset_name = st.selectbox("Region Preset", list(LIGHTHOUSE_PRESETS.keys()), key="lh_preset")
        preset = LIGHTHOUSE_PRESETS[preset_name]
        if preset is None:
            lc1, lc2, lc3 = st.columns(3)
            with lc1:
                lh_lat = st.number_input("Latitude", value=50.7, key="archm_lh_lat")
            with lc2:
                lh_lon = st.number_input("Longitude", value=-1.3, key="archm_lh_lon")
            with lc3:
                lh_radius = st.number_input("Radius (km)", value=100, min_value=10, max_value=500, key="archm_lh_radius")
        else:
            lh_lat = preset["lat"]
            lh_lon = preset["lon"]
            lh_radius = preset["radius"]

    if not generate:
        st.info("Select a map type and click **Generate Map** to explore architecture data.")
        return

    # ----- Build map -----
    with st.spinner(f"Building {selected_map} map..."):
        if selected_map == "Tallest Buildings":
            m, df = _build_tallest_buildings_map()
        elif selected_map == "World Wonders":
            m, df = _build_world_wonders_map()
        elif selected_map == "Famous Bridges":
            m, df = _build_famous_bridges_map()
        elif selected_map == "Major Dams":
            m, df = _build_major_dams_map()
        elif selected_map == "Castles":
            castles = _fetch_castles(c_lat, c_lon, c_radius)
            m, df = _build_castles_map(castles)
            overpass_data = castles
        elif selected_map == "Lighthouses":
            lighthouses = _fetch_lighthouses(lh_lat, lh_lon, lh_radius)
            m, df = _build_lighthouses_map(lighthouses)
            overpass_data = lighthouses
        elif selected_map == "Religious Buildings":
            m, df = _build_religious_buildings_map()
        elif selected_map == "Famous Towers":
            m, df = _build_famous_towers_map()
        elif selected_map == "Ancient Ruins":
            m, df = _build_ancient_ruins_map()
        elif selected_map == "Modern Marvels":
            m, df = _build_modern_marvels_map()
        else:
            st.error("Unknown map type.")
            return

    # ----- Stats metrics -----
    st.markdown("---")
    st.subheader("Summary Statistics")

    if selected_map == "Tallest Buildings":
        _render_stats_tallest_buildings()
    elif selected_map == "World Wonders":
        _render_stats_world_wonders()
    elif selected_map == "Famous Bridges":
        _render_stats_famous_bridges()
    elif selected_map == "Major Dams":
        _render_stats_major_dams()
    elif selected_map == "Castles":
        _render_stats_castles(overpass_data or [])
    elif selected_map == "Lighthouses":
        _render_stats_lighthouses(overpass_data or [])
    elif selected_map == "Religious Buildings":
        _render_stats_religious()
    elif selected_map == "Famous Towers":
        _render_stats_famous_towers()
    elif selected_map == "Ancient Ruins":
        _render_stats_ancient_ruins()
    elif selected_map == "Modern Marvels":
        _render_stats_modern_marvels()

    # ----- Folium Map -----
    st.markdown("---")
    st.subheader(f"{selected_map} Map")
    components.html(m._repr_html_(), height=550)

    # ----- Data Table -----
    st.markdown("---")
    st.subheader("Data Table")
    if not df.empty:
        st.dataframe(df, width="stretch")
    else:
        st.warning("No data to display.")

    # ----- Download CSV -----
    if not df.empty:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        csv_data = csv_buf.getvalue()
        file_label = selected_map.lower().replace(" ", "_")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"architecture_{file_label}.csv",
            mime="text/csv",
            key="architecture_csv_download",
        )


# ---------------------------------------------------------------------------
# Allow standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    st.set_page_config(page_title="Architecture & Monuments", layout="wide")
    render_architecture_maps_tab()
