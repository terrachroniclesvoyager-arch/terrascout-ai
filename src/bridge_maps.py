# -*- coding: utf-8 -*-
"""
Bridges & Engineering Marvels module for TerraScout AI.
Showcases famous bridges, tunnels, dams, canals, ancient engineering,
mega-construction, engineering disasters, and future megaprojects on
interactive Folium maps with curated datasets.

All data is curated (no API key needed). Optional Overpass API queries
for nearby bridge/tunnel discovery use the shared overpass_client.
"""

import io
import logging
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
import numpy as np

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_RED = "#ef4444"
ACCENT_PINK = "#ec4899"
ACCENT_BLUE = "#3b82f6"
ACCENT_ORANGE = "#f97316"
ACCENT_TEAL = "#14b8a6"

# ═══════════════════════════════════════════════════════════════════
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════
MAP_MODES = [
    "1. World's Greatest Bridges",
    "2. Longest Bridges",
    "3. Highest Bridges",
    "4. Famous Tunnels",
    "5. Great Dams",
    "6. Ancient Engineering",
    "7. Mega Construction",
    "8. Engineering Disasters",
    "9. Canals & Waterways",
    "10. Future Megaprojects",
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 1: WORLD'S GREATEST BRIDGES
# ═══════════════════════════════════════════════════════════════════
GREATEST_BRIDGES = [
    {"name": "Golden Gate Bridge", "lat": 37.8199, "lon": -122.4783, "country": "USA",
     "year": 1937, "span_m": 1280, "type": "Suspension", "note": "Iconic Art Deco towers, San Francisco"},
    {"name": "Tower Bridge", "lat": 51.5055, "lon": -0.0754, "country": "UK",
     "year": 1894, "span_m": 244, "type": "Bascule/Suspension", "note": "Victorian Gothic landmark, London"},
    {"name": "Millau Viaduct", "lat": 44.0775, "lon": 3.0223, "country": "France",
     "year": 2004, "span_m": 2460, "type": "Cable-stayed", "note": "Tallest bridge in the world (343 m)"},
    {"name": "Akashi Kaikyo Bridge", "lat": 34.6167, "lon": 135.0225, "country": "Japan",
     "year": 1998, "span_m": 1991, "type": "Suspension", "note": "Longest central span of any suspension bridge"},
    {"name": "Brooklyn Bridge", "lat": 40.7061, "lon": -73.9969, "country": "USA",
     "year": 1883, "span_m": 486, "type": "Suspension/Cable-stayed", "note": "First steel-wire suspension bridge"},
    {"name": "Sydney Harbour Bridge", "lat": -33.8523, "lon": 151.2108, "country": "Australia",
     "year": 1932, "span_m": 503, "type": "Steel arch", "note": "World's largest steel arch bridge at opening"},
    {"name": "Pont du Gard", "lat": 43.9475, "lon": 4.5353, "country": "France",
     "year": -19, "span_m": 275, "type": "Roman aqueduct", "note": "UNESCO World Heritage, 1st century BC"},
    {"name": "Rialto Bridge", "lat": 45.4380, "lon": 12.3360, "country": "Italy",
     "year": 1591, "span_m": 48, "type": "Stone arch", "note": "Oldest bridge across the Grand Canal, Venice"},
    {"name": "Charles Bridge", "lat": 50.0865, "lon": 14.4114, "country": "Czechia",
     "year": 1402, "span_m": 516, "type": "Stone arch", "note": "Gothic bridge with 30 baroque statues, Prague"},
    {"name": "Forth Bridge", "lat": 56.0000, "lon": -3.3886, "country": "UK",
     "year": 1890, "span_m": 2529, "type": "Cantilever", "note": "UNESCO World Heritage, Scotland"},
    {"name": "Tsing Ma Bridge", "lat": 22.3522, "lon": 114.0739, "country": "China",
     "year": 1997, "span_m": 1377, "type": "Suspension", "note": "Longest suspension bridge carrying rail traffic"},
    {"name": "Ponte Vecchio", "lat": 43.7680, "lon": 11.2531, "country": "Italy",
     "year": 1345, "span_m": 95, "type": "Stone arch", "note": "Medieval bridge with shops, Florence"},
    {"name": "Bosphorus Bridge (15 July Martyrs)", "lat": 41.0453, "lon": 29.0342, "country": "Turkey",
     "year": 1973, "span_m": 1074, "type": "Suspension", "note": "First bridge connecting Europe and Asia"},
    {"name": "Vasco da Gama Bridge", "lat": 38.7633, "lon": -9.0939, "country": "Portugal",
     "year": 1998, "span_m": 829, "type": "Cable-stayed", "note": "Longest bridge in Europe (17.2 km total)"},
    {"name": "Confederation Bridge", "lat": 46.2125, "lon": -63.7405, "country": "Canada",
     "year": 1997, "span_m": 250, "type": "Concrete box girder", "note": "12.9 km, longest over ice-covered water"},
    {"name": "Stari Most (Old Bridge)", "lat": 43.3373, "lon": 17.8150, "country": "Bosnia",
     "year": 1566, "span_m": 28.7, "type": "Stone arch", "note": "Ottoman masterpiece, rebuilt 2004, Mostar"},
    {"name": "Hangzhou Bay Bridge", "lat": 30.4478, "lon": 121.1681, "country": "China",
     "year": 2008, "span_m": 35673, "type": "Cable-stayed", "note": "36 km trans-oceanic crossing"},
    {"name": "Russky Bridge", "lat": 43.0558, "lon": 131.9106, "country": "Russia",
     "year": 2012, "span_m": 1104, "type": "Cable-stayed", "note": "World's longest cable-stayed span"},
    {"name": "Öresund Bridge", "lat": 55.5706, "lon": 12.8500, "country": "Denmark/Sweden",
     "year": 2000, "span_m": 490, "type": "Cable-stayed", "note": "7.8 km road/rail, Denmark to Sweden"},
    {"name": "Nanpu Bridge", "lat": 31.2032, "lon": 121.5063, "country": "China",
     "year": 1991, "span_m": 423, "type": "Cable-stayed", "note": "First cable-stayed bridge over Huangpu River"},
    {"name": "Gateshead Millennium Bridge", "lat": 54.9697, "lon": -1.5994, "country": "UK",
     "year": 2001, "span_m": 126, "type": "Tilting", "note": "World's first tilting bridge, Newcastle"},
    {"name": "Chain Bridge", "lat": 47.4990, "lon": 19.0432, "country": "Hungary",
     "year": 1849, "span_m": 202, "type": "Suspension", "note": "First permanent bridge across Danube at Budapest"},
    {"name": "Pont Neuf", "lat": 48.8570, "lon": 2.3413, "country": "France",
     "year": 1607, "span_m": 232, "type": "Stone arch", "note": "Oldest standing bridge across the Seine, Paris"},
    {"name": "Si-o-se-pol", "lat": 32.6440, "lon": 51.6684, "country": "Iran",
     "year": 1602, "span_m": 298, "type": "Stone arch", "note": "33-arch bridge, Isfahan masterpiece"},
    {"name": "Khaju Bridge", "lat": 32.6380, "lon": 51.6728, "country": "Iran",
     "year": 1650, "span_m": 133, "type": "Stone arch/dam", "note": "Functions as bridge and dam, Isfahan"},
    {"name": "Chapel Bridge", "lat": 47.0514, "lon": 8.3076, "country": "Switzerland",
     "year": 1333, "span_m": 204, "type": "Covered wood", "note": "Europe's oldest covered wooden bridge, Lucerne"},
    {"name": "Jiaozhou Bay Bridge", "lat": 36.1472, "lon": 120.2553, "country": "China",
     "year": 2011, "span_m": 42500, "type": "Cable-stayed", "note": "One of the world's longest sea bridges (42.5 km)"},
    {"name": "Tatara Bridge", "lat": 34.2833, "lon": 133.1000, "country": "Japan",
     "year": 1999, "span_m": 890, "type": "Cable-stayed", "note": "Shimanami Kaido route, elegant design"},
    {"name": "Stonecutters Bridge", "lat": 22.3386, "lon": 114.1258, "country": "China",
     "year": 2009, "span_m": 1018, "type": "Cable-stayed", "note": "Stainless steel/concrete hybrid towers, Hong Kong"},
    {"name": "Alamillo Bridge", "lat": 37.4028, "lon": -6.0015, "country": "Spain",
     "year": 1992, "span_m": 200, "type": "Cable-stayed", "note": "Santiago Calatrava design, Seville"},
    {"name": "Banpo Bridge (Rainbow Fountain)", "lat": 37.5100, "lon": 127.0025, "country": "South Korea",
     "year": 2009, "span_m": 1140, "type": "Concrete", "note": "World's longest bridge fountain, Seoul"},
    {"name": "Juscelino Kubitschek Bridge", "lat": -15.8300, "lon": -47.8500, "country": "Brazil",
     "year": 2002, "span_m": 1200, "type": "Steel arch", "note": "Three asymmetric arches, Brasilia"},
    {"name": "Henderson Waves", "lat": 1.2749, "lon": 103.8152, "country": "Singapore",
     "year": 2008, "span_m": 274, "type": "Pedestrian wave", "note": "Highest pedestrian bridge in Singapore"},
    {"name": "Danjiang Bridge", "lat": 25.1800, "lon": 121.4000, "country": "Taiwan",
     "year": 2024, "span_m": 920, "type": "Cable-stayed", "note": "Zaha Hadid Architects, single-mast design"},
    {"name": "Zhangjiajie Glass Bridge", "lat": 29.3400, "lon": 110.4300, "country": "China",
     "year": 2016, "span_m": 430, "type": "Glass-bottom", "note": "World's highest and longest glass bridge"},
    {"name": "Royal Gorge Bridge", "lat": 38.4628, "lon": -105.3250, "country": "USA",
     "year": 1929, "span_m": 384, "type": "Suspension", "note": "291 m above Arkansas River, Colorado"},
    {"name": "Incheon Bridge", "lat": 37.4042, "lon": 126.5694, "country": "South Korea",
     "year": 2009, "span_m": 800, "type": "Cable-stayed", "note": "21.4 km, connects Incheon Airport to Seoul"},
    {"name": "Great Belt East Bridge", "lat": 55.3417, "lon": 11.0333, "country": "Denmark",
     "year": 1998, "span_m": 1624, "type": "Suspension", "note": "Third longest suspension main span in the world"},
    {"name": "Anji Bridge (Zhaozhou)", "lat": 37.7619, "lon": 114.7464, "country": "China",
     "year": 605, "span_m": 50.8, "type": "Stone arch", "note": "World's oldest open-spandrel stone arch bridge"},
    {"name": "Humber Bridge", "lat": 53.7076, "lon": -0.4508, "country": "UK",
     "year": 1981, "span_m": 1410, "type": "Suspension", "note": "Longest single-span suspension bridge 1981-1998"},
    {"name": "Siduhe River Bridge", "lat": 30.4589, "lon": 109.8725, "country": "China",
     "year": 2009, "span_m": 900, "type": "Suspension", "note": "496 m above river, once world's highest"},
    {"name": "Ponte 25 de Abril", "lat": 38.6897, "lon": -9.1784, "country": "Portugal",
     "year": 1966, "span_m": 1013, "type": "Suspension", "note": "Resembles Golden Gate, Lisbon"},
    {"name": "Erasmus Bridge", "lat": 51.9097, "lon": 4.4869, "country": "Netherlands",
     "year": 1996, "span_m": 802, "type": "Cable-stayed", "note": "The Swan, Rotterdam landmark"},
    {"name": "Chengyang Wind and Rain Bridge", "lat": 25.8647, "lon": 109.7500, "country": "China",
     "year": 1916, "span_m": 77.8, "type": "Covered wood/stone", "note": "Dong people's masterpiece, no nails"},
    {"name": "Helix Bridge", "lat": 1.2864, "lon": 103.8614, "country": "Singapore",
     "year": 2010, "span_m": 280, "type": "Steel helix", "note": "DNA-inspired double helix pedestrian bridge"},
    {"name": "Puente Nuevo", "lat": 36.7406, "lon": -5.1637, "country": "Spain",
     "year": 1793, "span_m": 66, "type": "Stone arch", "note": "98 m above El Tajo gorge, Ronda"},
    {"name": "Vecchio Bridge (Mostar replica)", "lat": 43.3373, "lon": 17.8153, "country": "Bosnia",
     "year": 2004, "span_m": 29, "type": "Stone arch", "note": "Rebuilt after 1993 destruction"},
    {"name": "George Washington Bridge", "lat": 40.8517, "lon": -73.9527, "country": "USA",
     "year": 1931, "span_m": 1067, "type": "Suspension", "note": "World's busiest motor vehicle bridge"},
    {"name": "Mackinac Bridge", "lat": 45.8174, "lon": -84.7278, "country": "USA",
     "year": 1957, "span_m": 1158, "type": "Suspension", "note": "Mighty Mac, connects Michigan's two peninsulas"},
    {"name": "Verrazano-Narrows Bridge", "lat": 40.6066, "lon": -74.0447, "country": "USA",
     "year": 1964, "span_m": 1298, "type": "Suspension", "note": "Longest suspension bridge in Americas"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 2: LONGEST BRIDGES
# ═══════════════════════════════════════════════════════════════════
LONGEST_BRIDGES = [
    {"name": "Danyang-Kunshan Grand Bridge", "lat": 31.2500, "lon": 120.8000, "country": "China",
     "year": 2010, "length_km": 164.8, "type": "Viaduct (rail)", "note": "World's longest bridge, Beijing-Shanghai HSR"},
    {"name": "Changhua-Kaohsiung Viaduct", "lat": 23.5000, "lon": 120.4000, "country": "Taiwan",
     "year": 2004, "length_km": 157.3, "type": "Viaduct (rail)", "note": "Taiwan High Speed Rail"},
    {"name": "Cangde Grand Bridge", "lat": 38.3500, "lon": 116.5000, "country": "China",
     "year": 2010, "length_km": 115.9, "type": "Viaduct (rail)", "note": "Beijing-Shanghai HSR"},
    {"name": "Tianjin Grand Bridge", "lat": 39.1500, "lon": 117.0000, "country": "China",
     "year": 2010, "length_km": 113.7, "type": "Viaduct (rail)", "note": "Beijing-Shanghai HSR"},
    {"name": "Weinan Weihe Grand Bridge", "lat": 34.5000, "lon": 109.3000, "country": "China",
     "year": 2008, "length_km": 79.7, "type": "Viaduct (rail)", "note": "Zhengzhou-Xi'an HSR"},
    {"name": "Bang Na Expressway", "lat": 13.6667, "lon": 100.6333, "country": "Thailand",
     "year": 2000, "length_km": 54.0, "type": "Elevated highway", "note": "Longest road bridge when built"},
    {"name": "Lake Pontchartrain Causeway", "lat": 30.2100, "lon": -90.1100, "country": "USA",
     "year": 1956, "length_km": 38.4, "type": "Concrete trestle", "note": "Longest over-water bridge (continuous)"},
    {"name": "Manchac Swamp Bridge", "lat": 30.2825, "lon": -90.4239, "country": "USA",
     "year": 1979, "length_km": 36.7, "type": "Concrete trestle", "note": "Interstate 55, Louisiana swampland"},
    {"name": "Yangcun Bridge", "lat": 39.3500, "lon": 117.1000, "country": "China",
     "year": 2007, "length_km": 35.8, "type": "Viaduct (rail)", "note": "Beijing-Tianjin Intercity Railway"},
    {"name": "Hangzhou Bay Bridge", "lat": 30.4478, "lon": 121.1681, "country": "China",
     "year": 2008, "length_km": 35.7, "type": "Cable-stayed", "note": "S-shaped trans-oceanic crossing"},
    {"name": "Runyang Bridge", "lat": 32.2167, "lon": 119.3167, "country": "China",
     "year": 2005, "length_km": 35.7, "type": "Suspension+Cable-stayed", "note": "Crosses Yangtze River"},
    {"name": "Jiaozhou Bay Bridge", "lat": 36.1472, "lon": 120.2553, "country": "China",
     "year": 2011, "length_km": 42.5, "type": "Cable-stayed", "note": "Cross-sea bridge, Qingdao"},
    {"name": "Hong Kong-Zhuhai-Macau Bridge", "lat": 22.2833, "lon": 113.7667, "country": "China",
     "year": 2018, "length_km": 55.0, "type": "Cable-stayed+Tunnel", "note": "World's longest sea crossing (bridge-tunnel)"},
    {"name": "Chesapeake Bay Bridge-Tunnel", "lat": 37.0333, "lon": -76.0833, "country": "USA",
     "year": 1964, "length_km": 37.0, "type": "Bridge-Tunnel", "note": "Two tunnels under shipping channels"},
    {"name": "King Fahd Causeway", "lat": 26.1000, "lon": 50.3250, "country": "Saudi Arabia/Bahrain",
     "year": 1986, "length_km": 25.0, "type": "Concrete girder", "note": "Connects Saudi Arabia to Bahrain"},
    {"name": "Crimean Bridge", "lat": 45.3100, "lon": 36.5200, "country": "Russia",
     "year": 2018, "length_km": 19.0, "type": "Steel arch", "note": "Longest bridge in Europe, Kerch Strait"},
    {"name": "Confederation Bridge", "lat": 46.2125, "lon": -63.7405, "country": "Canada",
     "year": 1997, "length_km": 12.9, "type": "Concrete box girder", "note": "Northumberland Strait, ice-covered waters"},
    {"name": "Vasco da Gama Bridge", "lat": 38.7633, "lon": -9.0939, "country": "Portugal",
     "year": 1998, "length_km": 17.2, "type": "Cable-stayed", "note": "Longest bridge in EU"},
    {"name": "Incheon Bridge", "lat": 37.4042, "lon": 126.5694, "country": "South Korea",
     "year": 2009, "length_km": 21.4, "type": "Cable-stayed", "note": "Serves Incheon International Airport"},
    {"name": "Atchafalaya Basin Bridge", "lat": 30.2950, "lon": -91.7800, "country": "USA",
     "year": 1973, "length_km": 29.3, "type": "Concrete trestle", "note": "Interstate 10, Louisiana"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 3: HIGHEST BRIDGES
# ═══════════════════════════════════════════════════════════════════
HIGHEST_BRIDGES = [
    {"name": "Beipanjiang Bridge (Duge)", "lat": 26.3833, "lon": 104.7667, "country": "China",
     "year": 2016, "height_m": 565, "type": "Cable-stayed", "note": "World's highest bridge, Guizhou-Yunnan"},
    {"name": "Siduhe River Bridge", "lat": 30.4589, "lon": 109.8725, "country": "China",
     "year": 2009, "height_m": 496, "type": "Suspension", "note": "Hubei province, deep canyon"},
    {"name": "Puli Bridge", "lat": 26.4167, "lon": 104.6167, "country": "China",
     "year": 2015, "height_m": 485, "type": "Suspension", "note": "Guizhou province"},
    {"name": "Jinsha River Bridge (Hutong)", "lat": 26.8500, "lon": 103.4500, "country": "China",
     "year": 2020, "height_m": 461, "type": "Suspension", "note": "Yunnan province canyon crossing"},
    {"name": "Yachihe River Bridge", "lat": 26.5833, "lon": 106.5500, "country": "China",
     "year": 2016, "height_m": 434, "type": "Steel truss arch", "note": "Guiyang Ring Expressway"},
    {"name": "Pingtang Bridge", "lat": 25.7833, "lon": 107.0333, "country": "China",
     "year": 2019, "height_m": 332, "type": "Cable-stayed", "note": "Tallest concrete bridge tower (328m)"},
    {"name": "Millau Viaduct", "lat": 44.0775, "lon": 3.0223, "country": "France",
     "year": 2004, "height_m": 343, "type": "Cable-stayed", "note": "Tallest bridge structure in the world"},
    {"name": "Royal Gorge Bridge", "lat": 38.4628, "lon": -105.3250, "country": "USA",
     "year": 1929, "height_m": 291, "type": "Suspension", "note": "Over Arkansas River, Colorado"},
    {"name": "Baluarte Bridge", "lat": 23.7500, "lon": -105.7500, "country": "Mexico",
     "year": 2012, "height_m": 403, "type": "Cable-stayed", "note": "Durango-Mazatlan highway, Sierra Madre"},
    {"name": "Hegigio Gorge Pipeline Bridge", "lat": -6.3333, "lon": 143.0833, "country": "Papua New Guinea",
     "year": 2005, "height_m": 393, "type": "Pipeline suspension", "note": "Oil/gas pipeline, Southern Highlands"},
    {"name": "Europabrucke", "lat": 47.0833, "lon": 11.4500, "country": "Austria",
     "year": 1963, "height_m": 190, "type": "Steel box girder", "note": "Brenner Motorway, Alps"},
    {"name": "Mike O'Callaghan-Pat Tillman Bridge", "lat": 36.0133, "lon": -114.7378, "country": "USA",
     "year": 2010, "height_m": 270, "type": "Concrete arch", "note": "Next to Hoover Dam, Colorado River"},
    {"name": "Bloukrans Bridge", "lat": -33.9692, "lon": 23.6475, "country": "South Africa",
     "year": 1984, "height_m": 216, "type": "Concrete arch", "note": "Highest commercial bungee jump bridge"},
    {"name": "New River Gorge Bridge", "lat": 38.0700, "lon": -81.0836, "country": "USA",
     "year": 1977, "height_m": 267, "type": "Steel arch", "note": "Once the world's longest steel arch, West Virginia"},
    {"name": "Aizhai Bridge", "lat": 28.3833, "lon": 109.6333, "country": "China",
     "year": 2012, "height_m": 336, "type": "Suspension", "note": "Hunan province, through mountains and tunnels"},
    {"name": "Pont de la Caille", "lat": 46.0011, "lon": 6.1364, "country": "France",
     "year": 1839, "height_m": 147, "type": "Suspension", "note": "Historic suspension bridge, Haute-Savoie"},
    {"name": "Viaduc de Garabit", "lat": 44.9800, "lon": 3.1800, "country": "France",
     "year": 1885, "height_m": 122, "type": "Iron arch", "note": "Designed by Gustave Eiffel"},
    {"name": "Chenab Bridge", "lat": 33.1333, "lon": 74.9000, "country": "India",
     "year": 2022, "height_m": 359, "type": "Steel arch", "note": "World's highest railway bridge, Jammu & Kashmir"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 4: FAMOUS TUNNELS
# ═══════════════════════════════════════════════════════════════════
FAMOUS_TUNNELS = [
    {"name": "Channel Tunnel (Chunnel)", "lat": 51.0125, "lon": 1.1300, "country": "UK/France",
     "year": 1994, "length_km": 50.5, "type": "Undersea rail", "note": "Longest undersea portion (37.9 km), English Channel"},
    {"name": "Gotthard Base Tunnel", "lat": 46.6500, "lon": 8.6500, "country": "Switzerland",
     "year": 2016, "length_km": 57.1, "type": "Rail", "note": "World's longest and deepest railway tunnel, Alps"},
    {"name": "Seikan Tunnel", "lat": 41.3333, "lon": 140.3000, "country": "Japan",
     "year": 1988, "length_km": 53.9, "type": "Undersea rail", "note": "Connects Honshu and Hokkaido, Tsugaru Strait"},
    {"name": "Laerdal Tunnel", "lat": 61.0833, "lon": 7.1167, "country": "Norway",
     "year": 2000, "length_km": 24.5, "type": "Road", "note": "World's longest road tunnel"},
    {"name": "Mont Blanc Tunnel", "lat": 45.8333, "lon": 6.9333, "country": "France/Italy",
     "year": 1965, "length_km": 11.6, "type": "Road", "note": "Alpine crossing, major Europe route"},
    {"name": "Brenner Base Tunnel", "lat": 47.0000, "lon": 11.5000, "country": "Austria/Italy",
     "year": 2032, "length_km": 64.0, "type": "Rail (under construction)", "note": "Will be world's longest rail tunnel"},
    {"name": "Lotschberg Base Tunnel", "lat": 46.4833, "lon": 7.8333, "country": "Switzerland",
     "year": 2007, "length_km": 34.6, "type": "Rail", "note": "Swiss AlpTransit, Berne-Valais"},
    {"name": "Guoliang Tunnel", "lat": 35.7200, "lon": 113.5700, "country": "China",
     "year": 1977, "length_km": 1.2, "type": "Road", "note": "Hand-carved through cliff, Henan province"},
    {"name": "Thames Tunnel", "lat": 51.5019, "lon": -0.0519, "country": "UK",
     "year": 1843, "length_km": 0.4, "type": "Pedestrian/Rail", "note": "First tunnel under a navigable river"},
    {"name": "Holland Tunnel", "lat": 40.7261, "lon": -74.0117, "country": "USA",
     "year": 1927, "length_km": 2.6, "type": "Road", "note": "First mechanically ventilated vehicle tunnel"},
    {"name": "Lincoln Tunnel", "lat": 40.7603, "lon": -74.0133, "country": "USA",
     "year": 1937, "length_km": 2.4, "type": "Road", "note": "Three tubes under Hudson River, NYC"},
    {"name": "Marmaray Tunnel", "lat": 41.0047, "lon": 28.9750, "country": "Turkey",
     "year": 2013, "length_km": 13.6, "type": "Undersea rail", "note": "Under Bosphorus, connects Europe-Asia rail"},
    {"name": "Frejus Rail Tunnel", "lat": 45.1667, "lon": 6.6667, "country": "France/Italy",
     "year": 1871, "length_km": 13.7, "type": "Rail", "note": "First major trans-Alpine tunnel"},
    {"name": "Eisenhower-Johnson Memorial Tunnel", "lat": 39.6800, "lon": -105.9100, "country": "USA",
     "year": 1973, "length_km": 2.7, "type": "Road", "note": "Highest point on US Interstate system (3,401 m)"},
    {"name": "Zhongnanshan Tunnel", "lat": 33.8500, "lon": 108.8500, "country": "China",
     "year": 2007, "length_km": 18.0, "type": "Road", "note": "Longest road tunnel in Asia, Qinling Mountains"},
    {"name": "Simplon Tunnel", "lat": 46.2500, "lon": 8.0000, "country": "Switzerland/Italy",
     "year": 1906, "length_km": 19.8, "type": "Rail", "note": "Longest rail tunnel for over 75 years"},
    {"name": "Fehmarn Belt Tunnel", "lat": 54.5667, "lon": 11.2333, "country": "Denmark/Germany",
     "year": 2029, "length_km": 18.0, "type": "Immersed (construction)", "note": "Will be longest immersed tube tunnel"},
    {"name": "Ryfast Tunnel", "lat": 59.0333, "lon": 6.0500, "country": "Norway",
     "year": 2019, "length_km": 14.3, "type": "Road (subsea)", "note": "World's longest and deepest subsea road tunnel"},
    {"name": "Eiksund Tunnel", "lat": 62.2500, "lon": 5.8500, "country": "Norway",
     "year": 2008, "length_km": 7.8, "type": "Road (subsea)", "note": "Deepest subsea tunnel at opening (-287 m)"},
    {"name": "Yerba Buena Island Tunnel", "lat": 37.8106, "lon": -122.3603, "country": "USA",
     "year": 1936, "length_km": 0.5, "type": "Road", "note": "Largest-bore tunnel when built, Bay Bridge"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 5: GREAT DAMS
# ═══════════════════════════════════════════════════════════════════
GREAT_DAMS = [
    {"name": "Three Gorges Dam", "lat": 30.8267, "lon": 111.0042, "country": "China",
     "year": 2006, "height_m": 181, "capacity_gw": 22.5, "type": "Concrete gravity",
     "note": "World's largest power station by installed capacity"},
    {"name": "Itaipu Dam", "lat": -25.4083, "lon": -54.5886, "country": "Brazil/Paraguay",
     "year": 1984, "height_m": 196, "capacity_gw": 14.0, "type": "Hollow gravity/Buttress",
     "note": "Second largest hydroelectric, generates most electricity annually"},
    {"name": "Hoover Dam", "lat": 36.0161, "lon": -114.7377, "country": "USA",
     "year": 1936, "height_m": 221, "capacity_gw": 2.1, "type": "Concrete arch-gravity",
     "note": "Art Deco masterpiece, Black Canyon, Colorado River"},
    {"name": "Aswan High Dam", "lat": 23.9706, "lon": 32.8783, "country": "Egypt",
     "year": 1970, "height_m": 111, "capacity_gw": 2.1, "type": "Rock-fill embankment",
     "note": "Created Lake Nasser, controls Nile floods"},
    {"name": "Grand Ethiopian Renaissance Dam", "lat": 11.2153, "lon": 35.0933, "country": "Ethiopia",
     "year": 2023, "height_m": 145, "capacity_gw": 5.2, "type": "Roller-compacted concrete",
     "note": "Africa's largest hydroelectric dam, Blue Nile"},
    {"name": "Jinping-I Dam", "lat": 28.1750, "lon": 101.6333, "country": "China",
     "year": 2013, "height_m": 305, "capacity_gw": 3.6, "type": "Concrete double-curvature arch",
     "note": "World's tallest dam, Yalong River, Sichuan"},
    {"name": "Nurek Dam", "lat": 38.3667, "lon": 69.3333, "country": "Tajikistan",
     "year": 1980, "height_m": 300, "capacity_gw": 3.0, "type": "Earth-fill embankment",
     "note": "Second tallest dam in the world, Vakhsh River"},
    {"name": "Xiaowan Dam", "lat": 24.6750, "lon": 100.0167, "country": "China",
     "year": 2010, "height_m": 294, "capacity_gw": 4.2, "type": "Concrete double-curvature arch",
     "note": "Third tallest dam, Mekong River (Lancang)"},
    {"name": "Xiluodu Dam", "lat": 28.2514, "lon": 103.6428, "country": "China",
     "year": 2014, "height_m": 286, "capacity_gw": 13.9, "type": "Concrete double-curvature arch",
     "note": "Third largest hydroelectric dam, Jinsha River"},
    {"name": "Grand Coulee Dam", "lat": 47.9558, "lon": -118.9842, "country": "USA",
     "year": 1942, "height_m": 168, "capacity_gw": 6.8, "type": "Concrete gravity",
     "note": "Largest concrete structure in USA, Columbia River"},
    {"name": "Oroville Dam", "lat": 39.5381, "lon": -121.4847, "country": "USA",
     "year": 1968, "height_m": 235, "capacity_gw": 0.8, "type": "Earth-fill",
     "note": "Tallest dam in USA, Feather River, California"},
    {"name": "Kariba Dam", "lat": -16.5208, "lon": 28.7614, "country": "Zambia/Zimbabwe",
     "year": 1959, "height_m": 128, "capacity_gw": 1.6, "type": "Concrete double-curvature arch",
     "note": "Created world's largest man-made reservoir by volume"},
    {"name": "Guri Dam (Simon Bolivar)", "lat": 7.7500, "lon": -63.0000, "country": "Venezuela",
     "year": 1986, "height_m": 162, "capacity_gw": 10.2, "type": "Concrete gravity/Earth-fill",
     "note": "Fourth largest hydroelectric, Caroni River"},
    {"name": "Sayano-Shushenskaya Dam", "lat": 52.8264, "lon": 91.3706, "country": "Russia",
     "year": 1987, "height_m": 245, "capacity_gw": 6.4, "type": "Concrete arch-gravity",
     "note": "Largest power plant in Russia, Yenisei River"},
    {"name": "Glen Canyon Dam", "lat": 36.9375, "lon": -111.4856, "country": "USA",
     "year": 1966, "height_m": 216, "capacity_gw": 1.3, "type": "Concrete arch",
     "note": "Created Lake Powell, Colorado River, Arizona"},
    {"name": "Rogun Dam", "lat": 38.4167, "lon": 69.0667, "country": "Tajikistan",
     "year": 2028, "height_m": 335, "capacity_gw": 3.6, "type": "Earth-fill (under construction)",
     "note": "Will be world's tallest dam when completed"},
    {"name": "Tarbela Dam", "lat": 34.0889, "lon": 72.6925, "country": "Pakistan",
     "year": 1976, "height_m": 148, "capacity_gw": 4.9, "type": "Earth-fill/Rock-fill",
     "note": "Largest earth-filled dam, Indus River"},
    {"name": "Daniel-Johnson Dam", "lat": 51.0667, "lon": -68.7000, "country": "Canada",
     "year": 1968, "height_m": 214, "capacity_gw": 2.6, "type": "Multiple arch/Buttress",
     "note": "Largest multiple-arch dam, Manicouagan River"},
    {"name": "Inga Dams (I & II)", "lat": -5.5167, "lon": 13.6167, "country": "DR Congo",
     "year": 1982, "height_m": 53, "capacity_gw": 1.8, "type": "Concrete gravity",
     "note": "Congo River, Grand Inga proposed at 39 GW"},
    {"name": "Bratsk Dam", "lat": 56.2625, "lon": 101.6833, "country": "Russia",
     "year": 1967, "height_m": 125, "capacity_gw": 4.5, "type": "Concrete gravity",
     "note": "Created Bratsk Reservoir, largest by area when built"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 6: ANCIENT ENGINEERING
# ═══════════════════════════════════════════════════════════════════
ANCIENT_ENGINEERING = [
    {"name": "Pont du Gard", "lat": 43.9475, "lon": 4.5353, "country": "France",
     "year": -19, "type": "Roman aqueduct", "height_m": 49,
     "note": "Three-tier aqueduct bridge, supplied Nimes with water, UNESCO World Heritage"},
    {"name": "Great Wall — Badaling", "lat": 40.3553, "lon": 116.0158, "country": "China",
     "year": -700, "type": "Fortification wall", "height_m": 8,
     "note": "Most visited section, Ming Dynasty reconstruction, 21,196 km total"},
    {"name": "Great Wall — Mutianyu", "lat": 40.4319, "lon": 116.5681, "country": "China",
     "year": -550, "type": "Fortification wall", "height_m": 8,
     "note": "Well-preserved watchtowers, fewer crowds than Badaling"},
    {"name": "Persepolis", "lat": 29.9353, "lon": 52.8914, "country": "Iran",
     "year": -515, "type": "Palace complex", "height_m": 14,
     "note": "Achaemenid Empire ceremonial capital, Gate of All Nations"},
    {"name": "Roman Colosseum", "lat": 41.8902, "lon": 12.4922, "country": "Italy",
     "year": 80, "type": "Amphitheatre", "height_m": 48,
     "note": "Largest ancient amphitheatre, held 50,000-80,000 spectators"},
    {"name": "Pantheon", "lat": 41.8986, "lon": 12.4769, "country": "Italy",
     "year": 126, "type": "Temple/Dome", "height_m": 43,
     "note": "Unreinforced concrete dome, largest for 1,300 years"},
    {"name": "Aqueduct of Segovia", "lat": 40.9481, "lon": -4.1181, "country": "Spain",
     "year": 50, "type": "Roman aqueduct", "height_m": 28,
     "note": "166 arches, no mortar, still standing after 2,000 years"},
    {"name": "Appian Way (Via Appia)", "lat": 41.8425, "lon": 12.5236, "country": "Italy",
     "year": -312, "type": "Roman road", "height_m": 0,
     "note": "Queen of Roads, Rome to Brindisi (563 km), UNESCO 2024"},
    {"name": "Cloaca Maxima", "lat": 41.8892, "lon": 12.4858, "country": "Italy",
     "year": -600, "type": "Sewer system", "height_m": 3,
     "note": "Ancient Rome's great sewer, still partially in use"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "country": "Peru",
     "year": 1450, "type": "Inca citadel", "height_m": 0,
     "note": "Stone terraces, water channels, earthquake-resistant dry-stone walls"},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia",
     "year": 1150, "type": "Temple complex", "height_m": 65,
     "note": "Largest religious monument, Khmer Empire, elaborate moat system"},
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342, "country": "Egypt",
     "year": -2560, "type": "Pyramid", "height_m": 146,
     "note": "Tallest man-made structure for 3,800 years, 2.3 million stone blocks"},
    {"name": "Hagia Sophia", "lat": 41.0086, "lon": 28.9802, "country": "Turkey",
     "year": 537, "type": "Domed basilica", "height_m": 55,
     "note": "Largest dome for nearly 1,000 years, Byzantine engineering marvel"},
    {"name": "Qanat of Gonabad", "lat": 34.3500, "lon": 58.6833, "country": "Iran",
     "year": -700, "type": "Underground water channel", "height_m": 0,
     "note": "Oldest known qanat, 45 km long, still supplies water"},
    {"name": "Derinkuyu Underground City", "lat": 38.3736, "lon": 34.7347, "country": "Turkey",
     "year": -700, "type": "Underground city", "height_m": 85,
     "note": "18 stories deep, housed 20,000 people, Cappadocia"},
    {"name": "Petra — Treasury (Al-Khazneh)", "lat": 30.3217, "lon": 35.4514, "country": "Jordan",
     "year": -100, "type": "Rock-cut architecture", "height_m": 40,
     "note": "Nabataean carved sandstone facade, advanced water engineering"},
    {"name": "Moai Statues — Ahu Tongariki", "lat": -27.1256, "lon": -109.2769, "country": "Chile",
     "year": 1400, "type": "Monolithic statues", "height_m": 10,
     "note": "15 moai, largest platform on Easter Island, transported without wheels"},
    {"name": "Pont Flavien", "lat": 43.4072, "lon": 5.1086, "country": "France",
     "year": -10, "type": "Roman bridge", "height_m": 6,
     "note": "Single-arch stone bridge, oldest functional Roman bridge"},
    {"name": "Alcantara Bridge", "lat": 39.7214, "lon": -6.8903, "country": "Spain",
     "year": 106, "type": "Roman bridge", "height_m": 48,
     "note": "Six arches over Tagus River, inscription: 'built to last forever'"},
    {"name": "Jerwan Aqueduct", "lat": 36.6333, "lon": 43.5000, "country": "Iraq",
     "year": -690, "type": "Assyrian aqueduct", "height_m": 9,
     "note": "Oldest known aqueduct, built by Sennacherib for Nineveh"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 7: MEGA CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════
MEGA_CONSTRUCTION = [
    {"name": "Burj Khalifa", "lat": 25.1972, "lon": 55.2744, "country": "UAE",
     "year": 2010, "type": "Skyscraper", "height_m": 828,
     "note": "World's tallest building, 163 floors, Dubai"},
    {"name": "Palm Jumeirah", "lat": 25.1124, "lon": 55.1390, "country": "UAE",
     "year": 2006, "type": "Artificial island", "height_m": 0,
     "note": "Palm-shaped island, 5 km diameter, visible from space"},
    {"name": "Panama Canal", "lat": 9.0800, "lon": -79.6800, "country": "Panama",
     "year": 1914, "type": "Ship canal", "height_m": 0,
     "note": "82 km, connects Atlantic and Pacific, 12,000+ ships/year"},
    {"name": "Suez Canal", "lat": 30.4550, "lon": 32.3500, "country": "Egypt",
     "year": 1869, "type": "Ship canal", "height_m": 0,
     "note": "193 km, no locks, 12% of global trade passes through"},
    {"name": "International Space Station (assembly site)", "lat": 28.5721, "lon": -80.6480, "country": "USA",
     "year": 1998, "type": "Space station (launched from KSC)", "height_m": 0,
     "note": "Largest space structure, 109 m wide, orbits at 408 km altitude"},
    {"name": "Large Hadron Collider", "lat": 46.2333, "lon": 6.0500, "country": "Switzerland/France",
     "year": 2008, "type": "Particle accelerator", "height_m": 0,
     "note": "27 km ring, 100 m underground, discovered Higgs boson"},
    {"name": "NEOM — The Line", "lat": 27.5167, "lon": 36.0500, "country": "Saudi Arabia",
     "year": 2030, "type": "Linear megacity (planned)", "height_m": 500,
     "note": "170 km long, 200 m wide, 500 m tall, 9 million residents planned"},
    {"name": "Kansai International Airport", "lat": 34.4347, "lon": 135.2441, "country": "Japan",
     "year": 1994, "type": "Airport on artificial island", "height_m": 0,
     "note": "4 km artificial island in Osaka Bay, Renzo Piano design"},
    {"name": "Beijing Daxing International Airport", "lat": 39.5098, "lon": 116.4105, "country": "China",
     "year": 2019, "type": "Airport", "height_m": 0,
     "note": "World's largest single-structure airport terminal, Zaha Hadid design"},
    {"name": "Channel Tunnel (Portal — Folkestone)", "lat": 51.0975, "lon": 1.1486, "country": "UK/France",
     "year": 1994, "type": "Undersea rail tunnel", "height_m": 0,
     "note": "50.5 km, 37.9 km undersea, connects UK and continental Europe"},
    {"name": "Jeddah Tower (under construction)", "lat": 21.6236, "lon": 39.1444, "country": "Saudi Arabia",
     "year": 2028, "type": "Skyscraper (under construction)", "height_m": 1000,
     "note": "Will be first 1 km+ building, Kingdom City development"},
    {"name": "Shanghai Tower", "lat": 31.2355, "lon": 121.5016, "country": "China",
     "year": 2015, "type": "Skyscraper", "height_m": 632,
     "note": "World's second tallest, twisting glass facade, Shanghai"},
    {"name": "Taipei 101", "lat": 25.0339, "lon": 121.5645, "country": "Taiwan",
     "year": 2004, "type": "Skyscraper", "height_m": 508,
     "note": "Bamboo-inspired design, 730-ton tuned mass damper"},
    {"name": "One World Trade Center", "lat": 40.7127, "lon": -74.0134, "country": "USA",
     "year": 2014, "type": "Skyscraper", "height_m": 541,
     "note": "1,776 feet (symbolic), tallest in Western Hemisphere"},
    {"name": "Dubai Creek Tower", "lat": 25.2240, "lon": 55.3340, "country": "UAE",
     "year": 2025, "type": "Observation tower (planned)", "height_m": 928,
     "note": "Santiago Calatrava design, cable-stayed observation spire"},
    {"name": "Three Gorges Dam", "lat": 30.8267, "lon": 111.0042, "country": "China",
     "year": 2006, "type": "Hydroelectric dam", "height_m": 181,
     "note": "2,335 m long, 22.5 GW capacity, largest power station on Earth"},
    {"name": "Central Park Tower", "lat": 40.7661, "lon": -73.9809, "country": "USA",
     "year": 2021, "type": "Skyscraper", "height_m": 472,
     "note": "World's tallest residential building, Billionaires' Row, NYC"},
    {"name": "Millau Viaduct", "lat": 44.0775, "lon": 3.0223, "country": "France",
     "year": 2004, "type": "Cable-stayed bridge", "height_m": 343,
     "note": "Tallest bridge structure, taller than Eiffel Tower, Norman Foster design"},
    {"name": "Tokyo Skytree", "lat": 35.7101, "lon": 139.8107, "country": "Japan",
     "year": 2012, "type": "Broadcasting tower", "height_m": 634,
     "note": "World's tallest tower and second tallest structure"},
    {"name": "Petronas Twin Towers", "lat": 3.1578, "lon": 101.7117, "country": "Malaysia",
     "year": 1998, "type": "Twin skyscrapers", "height_m": 452,
     "note": "Tallest twin towers, skybridge at 170 m, Islamic geometry design"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 8: ENGINEERING DISASTERS
# ═══════════════════════════════════════════════════════════════════
ENGINEERING_DISASTERS = [
    {"name": "Tacoma Narrows Bridge", "lat": 47.2690, "lon": -122.5517, "country": "USA",
     "year": 1940, "type": "Suspension bridge collapse", "casualties": 0,
     "note": "Galloping Gertie — aeroelastic flutter caused dramatic collapse, filmed on camera"},
    {"name": "Morandi Bridge (Ponte Morandi)", "lat": 44.4275, "lon": 8.8853, "country": "Italy",
     "year": 2018, "type": "Cable-stayed bridge collapse", "casualties": 43,
     "note": "Genoa, corrosion and design flaws, led to major infrastructure review"},
    {"name": "Vajont Dam", "lat": 46.2656, "lon": 12.3269, "country": "Italy",
     "year": 1963, "type": "Dam overtopping (landslide)", "casualties": 1917,
     "note": "Monte Toc landslide sent 50M m3 wave over dam, Longarone destroyed"},
    {"name": "Banqiao Dam", "lat": 32.9500, "lon": 113.6500, "country": "China",
     "year": 1975, "type": "Dam failure", "casualties": 26000,
     "note": "Typhoon Nina, 62 dams failed, worst dam disaster in history"},
    {"name": "St. Francis Dam", "lat": 34.5475, "lon": -118.5125, "country": "USA",
     "year": 1928, "type": "Dam failure", "casualties": 431,
     "note": "Concrete gravity dam collapse, second-worst US disaster after San Francisco earthquake"},
    {"name": "Silver Bridge", "lat": 38.8411, "lon": -82.1447, "country": "USA",
     "year": 1967, "type": "Eyebar chain suspension collapse", "casualties": 46,
     "note": "Point Pleasant WV, led to creation of US bridge inspection standards"},
    {"name": "Tay Bridge", "lat": 56.4383, "lon": -2.9917, "country": "UK",
     "year": 1879, "type": "Rail bridge collapse", "casualties": 75,
     "note": "Storm collapse during train crossing, design and construction faults"},
    {"name": "Quebec Bridge", "lat": 46.7500, "lon": -71.2833, "country": "Canada",
     "year": 1907, "type": "Cantilever bridge collapse", "casualties": 75,
     "note": "Collapsed twice during construction (1907 & 1916), design error"},
    {"name": "Hyatt Regency Walkway", "lat": 39.0836, "lon": -94.5828, "country": "USA",
     "year": 1981, "type": "Skyway collapse", "casualties": 114,
     "note": "Kansas City, design change from original weakened connections"},
    {"name": "Sampoong Department Store", "lat": 37.5043, "lon": 127.0238, "country": "South Korea",
     "year": 1995, "type": "Building collapse", "casualties": 502,
     "note": "Seoul, illegal modifications and poor construction oversight"},
    {"name": "Ronan Point", "lat": 51.5200, "lon": 0.0200, "country": "UK",
     "year": 1968, "type": "Tower block collapse", "casualties": 4,
     "note": "Gas explosion caused progressive collapse, changed building codes"},
    {"name": "Rana Plaza", "lat": 23.8756, "lon": 90.4089, "country": "Bangladesh",
     "year": 2013, "type": "Building collapse", "casualties": 1134,
     "note": "Dhaka garment factory, structural failures ignored, worst garment industry disaster"},
    {"name": "Dee Bridge", "lat": 53.1833, "lon": -3.0167, "country": "UK",
     "year": 1847, "type": "Rail bridge collapse", "casualties": 5,
     "note": "Robert Stephenson's design, first cast-iron bridge failure investigation"},
    {"name": "Ashtabula River Railroad Disaster", "lat": 41.8781, "lon": -80.7898, "country": "USA",
     "year": 1876, "type": "Iron bridge collapse", "casualties": 92,
     "note": "Bridge failed under train, caught fire in ravine, inspection reforms"},
    {"name": "Cypress Street Viaduct", "lat": 37.8194, "lon": -122.2900, "country": "USA",
     "year": 1989, "type": "Freeway collapse", "casualties": 42,
     "note": "Loma Prieta earthquake, Oakland CA, led to seismic retrofit standards"},
    {"name": "I-35W Mississippi River Bridge", "lat": 44.9778, "lon": -93.2439, "country": "USA",
     "year": 2007, "type": "Steel truss bridge collapse", "casualties": 13,
     "note": "Minneapolis, gusset plate design flaw, led to bridge inspection funding"},
    {"name": "Fern Hollow Bridge", "lat": 40.4356, "lon": -79.8986, "country": "USA",
     "year": 2022, "type": "Bridge collapse", "casualties": 0,
     "note": "Pittsburgh, rated poor condition since 2011, collapsed hours before Biden infrastructure visit"},
    {"name": "Seongsu Bridge", "lat": 37.5414, "lon": 127.0186, "country": "South Korea",
     "year": 1994, "type": "Truss bridge collapse", "casualties": 32,
     "note": "Seoul, poor welding and fatigue cracks, led to nationwide inspections"},
    {"name": "Malpasset Dam", "lat": 43.5106, "lon": 6.7553, "country": "France",
     "year": 1959, "type": "Arch dam failure", "casualties": 423,
     "note": "Frejus, geological fault under foundation, worst French dam disaster"},
    {"name": "Machchu Dam-II", "lat": 22.8167, "lon": 71.3833, "country": "India",
     "year": 1979, "type": "Dam failure", "casualties": 1800,
     "note": "Gujarat, Machchu River flooding, poor spillway capacity"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 9: CANALS & WATERWAYS
# ═══════════════════════════════════════════════════════════════════
CANALS_WATERWAYS = [
    {"name": "Panama Canal — Miraflores Locks", "lat": 9.0153, "lon": -79.5897, "country": "Panama",
     "year": 1914, "length_km": 82, "type": "Lock canal",
     "note": "Connects Atlantic and Pacific, 12,000+ vessels/year, expanded 2016"},
    {"name": "Suez Canal", "lat": 30.4550, "lon": 32.3500, "country": "Egypt",
     "year": 1869, "length_km": 193, "type": "Sea-level canal (no locks)",
     "note": "Connects Mediterranean and Red Sea, 12% of global trade"},
    {"name": "Corinth Canal", "lat": 37.9364, "lon": 22.9853, "country": "Greece",
     "year": 1893, "length_km": 6.3, "type": "Sea-level canal",
     "note": "21 m wide, 8 m deep, cuts through rocky isthmus, narrow for modern ships"},
    {"name": "Grand Canal (Beijing-Hangzhou)", "lat": 35.0000, "lon": 117.0000, "country": "China",
     "year": -486, "length_km": 1794, "type": "Inland waterway",
     "note": "World's longest canal, UNESCO World Heritage, over 2,500 years old"},
    {"name": "Erie Canal — Lock 1", "lat": 42.7700, "lon": -73.7000, "country": "USA",
     "year": 1825, "length_km": 584, "type": "Barge canal",
     "note": "Connected Great Lakes to Atlantic, transformed US economy"},
    {"name": "Kiel Canal (Nord-Ostsee-Kanal)", "lat": 54.3333, "lon": 9.6667, "country": "Germany",
     "year": 1895, "length_km": 98, "type": "Ship canal",
     "note": "World's busiest artificial waterway, connects North Sea and Baltic Sea"},
    {"name": "Canal du Midi", "lat": 43.2964, "lon": 2.3594, "country": "France",
     "year": 1681, "length_km": 240, "type": "Barge canal",
     "note": "UNESCO World Heritage, Pierre-Paul Riquet's masterpiece, 91 locks"},
    {"name": "Manchester Ship Canal", "lat": 53.4631, "lon": -2.7208, "country": "UK",
     "year": 1894, "length_km": 58, "type": "Ship canal",
     "note": "Made Manchester an inland port, Industrial Revolution landmark"},
    {"name": "Welland Canal", "lat": 43.1167, "lon": -79.2167, "country": "Canada",
     "year": 1829, "length_km": 43, "type": "Ship canal",
     "note": "Bypasses Niagara Falls, 8 locks, 99.5 m elevation change"},
    {"name": "White Sea-Baltic Canal", "lat": 63.0000, "lon": 34.0000, "country": "Russia",
     "year": 1933, "length_km": 227, "type": "Inland waterway",
     "note": "Connects White Sea to Lake Onega, built by forced labor (Gulag)"},
    {"name": "Gota Canal", "lat": 58.5333, "lon": 15.6167, "country": "Sweden",
     "year": 1832, "length_km": 190, "type": "Inland waterway",
     "note": "58 locks, connects Gothenburg to Stockholm via lakes and canals"},
    {"name": "Amsterdam-Rhine Canal", "lat": 52.0833, "lon": 5.0833, "country": "Netherlands",
     "year": 1952, "length_km": 72, "type": "Ship canal",
     "note": "Major freight route, connects Port of Amsterdam to Rhine River"},
    {"name": "Volga-Don Canal", "lat": 48.5333, "lon": 44.5167, "country": "Russia",
     "year": 1952, "length_km": 101, "type": "Ship canal",
     "note": "13 locks, connects Volga and Don rivers, 5 seas waterway"},
    {"name": "Caledonian Canal", "lat": 57.1500, "lon": -4.6667, "country": "UK",
     "year": 1822, "length_km": 97, "type": "Ship canal",
     "note": "Thomas Telford design, crosses Scottish Highlands via Loch Ness"},
    {"name": "Saimaa Canal", "lat": 61.0667, "lon": 28.2000, "country": "Finland/Russia",
     "year": 1856, "length_km": 43, "type": "Ship canal",
     "note": "Connects Lake Saimaa to Gulf of Finland, 8 locks"},
    {"name": "Albert Canal", "lat": 51.1667, "lon": 4.4167, "country": "Belgium",
     "year": 1939, "length_km": 130, "type": "Ship canal",
     "note": "Connects Liege to Antwerp, major Belgian freight corridor"},
    {"name": "Rideau Canal — Ottawa Locks", "lat": 45.4255, "lon": -75.6972, "country": "Canada",
     "year": 1832, "length_km": 202, "type": "Slack-water canal",
     "note": "UNESCO World Heritage, oldest continuously operated canal in North America"},
    {"name": "Moscow Canal", "lat": 56.2000, "lon": 37.5500, "country": "Russia",
     "year": 1937, "length_km": 128, "type": "Ship canal",
     "note": "Connects Moscow River to Volga, made Moscow a 'port of five seas'"},
    {"name": "Cape Cod Canal", "lat": 41.7425, "lon": -70.6139, "country": "USA",
     "year": 1914, "length_km": 11.3, "type": "Sea-level canal",
     "note": "Widest sea-level canal in the world, Massachusetts"},
    {"name": "Houston Ship Channel", "lat": 29.7333, "lon": -95.0167, "country": "USA",
     "year": 1914, "length_km": 80, "type": "Ship channel",
     "note": "Made Houston a major port despite being 80 km from the Gulf"},
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATA — MODE 10: FUTURE MEGAPROJECTS
# ═══════════════════════════════════════════════════════════════════
FUTURE_MEGAPROJECTS = [
    {"name": "Strait of Messina Bridge", "lat": 38.2333, "lon": 15.6333, "country": "Italy",
     "year": 2032, "type": "Suspension bridge (planned)", "span_km": 3.3,
     "note": "Would connect Sicily to mainland Italy, world's longest single-span bridge"},
    {"name": "Bering Strait Tunnel", "lat": 65.7500, "lon": -169.0000, "country": "Russia/USA",
     "year": 2050, "type": "Undersea tunnel (proposed)", "span_km": 80,
     "note": "Would connect Alaska to Siberia, proposed since 1905"},
    {"name": "Gibraltar Strait Crossing", "lat": 35.9667, "lon": -5.5833, "country": "Morocco/Spain",
     "year": 2040, "type": "Bridge or tunnel (proposed)", "span_km": 14,
     "note": "Africa-Europe fixed link, various proposals since 1869"},
    {"name": "NEOM — The Line", "lat": 27.5167, "lon": 36.0500, "country": "Saudi Arabia",
     "year": 2030, "type": "Linear megacity", "span_km": 170,
     "note": "500 m tall, 200 m wide mirror-clad city, zero cars, 100% renewable"},
    {"name": "Fehmarn Belt Fixed Link", "lat": 54.5667, "lon": 11.2333, "country": "Denmark/Germany",
     "year": 2029, "type": "Immersed tunnel (under construction)", "span_km": 18,
     "note": "Longest immersed road/rail tunnel, connects Scandinavia to Central Europe"},
    {"name": "TransAtlantic Tunnel", "lat": 50.0000, "lon": -30.0000, "country": "Concept",
     "year": 2100, "type": "Vacuum tube tunnel (theoretical)", "span_km": 5500,
     "note": "Submerged floating tunnel NY-London, 1-hour travel, feasibility studied"},
    {"name": "Rogun Dam Completion", "lat": 38.4167, "lon": 69.0667, "country": "Tajikistan",
     "year": 2028, "type": "World's tallest dam (335 m)", "span_km": 0.6,
     "note": "Under construction since 1976, will be tallest dam globally"},
    {"name": "Grand Inga Dam", "lat": -5.5167, "lon": 13.6167, "country": "DR Congo",
     "year": 2035, "type": "Hydroelectric dam (proposed)", "span_km": 0,
     "note": "Would generate 39 GW — twice Three Gorges, powering half of Africa"},
    {"name": "Hyperloop One Route", "lat": 36.1699, "lon": -115.1398, "country": "USA",
     "year": 2035, "type": "Vacuum tube transport (proposed)", "span_km": 480,
     "note": "Las Vegas to Los Angeles, 1,000+ km/h, Elon Musk concept"},
    {"name": "Space Elevator (Proposed Site)", "lat": 0.0000, "lon": -80.0000, "country": "Concept",
     "year": 2060, "type": "Carbon nanotube elevator", "span_km": 36000,
     "note": "Equatorial site, 36,000 km to geostationary orbit, NASA/JAXA studies"},
    {"name": "Bohai Strait Tunnel", "lat": 37.8333, "lon": 120.5000, "country": "China",
     "year": 2035, "type": "Undersea tunnel (proposed)", "span_km": 106,
     "note": "Connect Dalian to Yantai, reduce travel from 6 hours to 40 minutes"},
    {"name": "Japan-Korea Undersea Tunnel", "lat": 34.0000, "lon": 130.0000, "country": "Japan/South Korea",
     "year": 2040, "type": "Undersea tunnel (proposed)", "span_km": 200,
     "note": "Connect Kyushu to Busan, discussed since 1917"},
    {"name": "Jeddah Tower Completion", "lat": 21.6236, "lon": 39.1444, "country": "Saudi Arabia",
     "year": 2028, "type": "1 km+ skyscraper", "span_km": 0,
     "note": "First building over 1,000 m tall, construction resumed 2023"},
    {"name": "HS2 Phase 2 — Manchester", "lat": 53.4808, "lon": -2.2426, "country": "UK",
     "year": 2040, "type": "High-speed rail (uncertain)", "span_km": 330,
     "note": "London to Manchester, controversial cost overruns, portions canceled"},
    {"name": "Delhi-Mumbai Expressway", "lat": 24.0000, "lon": 75.0000, "country": "India",
     "year": 2025, "type": "8-lane expressway", "span_km": 1350,
     "note": "India's longest expressway, reduces travel time from 24h to 12h"},
    {"name": "Salang Tunnel Replacement", "lat": 35.3200, "lon": 69.0400, "country": "Afghanistan",
     "year": 2030, "type": "Mountain tunnel (proposed)", "span_km": 13,
     "note": "Replace dangerous 1964 Soviet-built tunnel through Hindu Kush"},
    {"name": "Lamu Port (LAPSSET)", "lat": -2.2717, "lon": 40.9020, "country": "Kenya",
     "year": 2030, "type": "Port and corridor", "span_km": 1700,
     "note": "32 berths, 1,700 km corridor to Ethiopia and South Sudan"},
    {"name": "Amazon Waterway Project", "lat": -3.1190, "lon": -60.0217, "country": "Brazil",
     "year": 2030, "type": "River channel improvement", "span_km": 6500,
     "note": "Improve navigation on Amazon and tributaries, reduce deforestation from roads"},
    {"name": "Strait of Malacca Bridge", "lat": 2.5000, "lon": 101.0000, "country": "Malaysia/Indonesia",
     "year": 2045, "type": "Bridge (proposed)", "span_km": 40,
     "note": "Connect Sumatra to Malay Peninsula, would be world's longest bridge"},
    {"name": "V&A Waterfront Extension", "lat": -33.9042, "lon": 18.4188, "country": "South Africa",
     "year": 2027, "type": "Urban development", "span_km": 0,
     "note": "Battery Park expansion, integrate canal district, Cape Town"},
]

# ═══════════════════════════════════════════════════════════════════
# MODE DESCRIPTIONS
# ═══════════════════════════════════════════════════════════════════
MODE_DESCRIPTIONS = {
    MAP_MODES[0]: (
        "Explore the top 50 most iconic bridges on Earth, spanning millennia of engineering "
        "from ancient Roman aqueducts to modern cable-stayed marvels. Each pin represents a "
        "bridge celebrated for its design, history, or cultural significance."
    ),
    MAP_MODES[1]: (
        "The longest bridges on Earth ranked by total length. China dominates with its "
        "high-speed rail viaducts exceeding 100 km, while the USA holds records for the "
        "longest over-water bridges. Click markers for construction details and dimensions."
    ),
    MAP_MODES[2]: (
        "The world's highest bridges ranked by deck height above the surface below. "
        "China's mountainous terrain has driven construction of bridges soaring over 500 m "
        "above river gorges, while France's Millau Viaduct remains the tallest structure."
    ),
    MAP_MODES[3]: (
        "Famous tunnels from around the world, including the Channel Tunnel, the Gotthard Base "
        "Tunnel (world's longest at 57.1 km), and historic firsts like the Thames Tunnel. "
        "Undersea, mountain, and road tunnels that reshaped transportation."
    ),
    MAP_MODES[4]: (
        "The world's greatest dams ranked by height, power capacity, and engineering ambition. "
        "From the 22.5 GW Three Gorges Dam to the planned 335 m Rogun Dam, these structures "
        "control rivers, generate power, and shape entire regions."
    ),
    MAP_MODES[5]: (
        "Marvels of ancient engineering that still inspire awe: Roman aqueducts built without "
        "mortar, the Great Wall stretching 21,196 km, underground cities in Cappadocia, and "
        "the Great Pyramid which stood as the tallest structure for 3,800 years."
    ),
    MAP_MODES[6]: (
        "The largest, tallest, and most ambitious construction projects of the modern era. "
        "Skyscrapers touching 828 m, artificial islands visible from space, particle accelerators "
        "27 km in circumference, and megacities being built from scratch in the desert."
    ),
    MAP_MODES[7]: (
        "Engineering failures and disasters that led to critical safety improvements. Each entry "
        "includes the root cause and the lasting changes in codes, standards, and inspection "
        "practices that followed. Lessons written in tragedy."
    ),
    MAP_MODES[8]: (
        "The great canals and waterways that transformed global trade and connected civilizations. "
        "From the 2,500-year-old Grand Canal of China to the Panama and Suez Canals that "
        "reshaped global shipping routes, plus Europe's historic barge canals."
    ),
    MAP_MODES[9]: (
        "Proposed and under-construction megaprojects that may reshape the world: the Strait of "
        "Messina Bridge, Bering Strait Tunnel, Grand Inga Dam, NEOM's The Line, and even "
        "theoretical concepts like the TransAtlantic Tunnel and Space Elevator."
    ),
}

# ═══════════════════════════════════════════════════════════════════
# MARKER COLORS PER MODE
# ═══════════════════════════════════════════════════════════════════
MODE_COLORS = {
    MAP_MODES[0]: ACCENT_CYAN,
    MAP_MODES[1]: ACCENT_AMBER,
    MAP_MODES[2]: ACCENT_RED,
    MAP_MODES[3]: ACCENT_VIOLET,
    MAP_MODES[4]: ACCENT_BLUE,
    MAP_MODES[5]: ACCENT_ORANGE,
    MAP_MODES[6]: ACCENT_EMERALD,
    MAP_MODES[7]: ACCENT_RED,
    MAP_MODES[8]: ACCENT_TEAL,
    MAP_MODES[9]: ACCENT_PINK,
}

# Folium icon colors (limited palette available)
MODE_FOLIUM_ICONS = {
    MAP_MODES[0]: ("info-sign", "blue"),
    MAP_MODES[1]: ("resize-horizontal", "orange"),
    MAP_MODES[2]: ("arrow-up", "red"),
    MAP_MODES[3]: ("road", "purple"),
    MAP_MODES[4]: ("tint", "blue"),
    MAP_MODES[5]: ("tower", "orange"),
    MAP_MODES[6]: ("globe", "green"),
    MAP_MODES[7]: ("warning-sign", "red"),
    MAP_MODES[8]: ("transfer", "cadetblue"),
    MAP_MODES[9]: ("flash", "pink"),
}


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _get_data_for_mode(mode: str) -> list[dict]:
    """Return the curated dataset for a given mode."""
    mode_data = {
        MAP_MODES[0]: GREATEST_BRIDGES,
        MAP_MODES[1]: LONGEST_BRIDGES,
        MAP_MODES[2]: HIGHEST_BRIDGES,
        MAP_MODES[3]: FAMOUS_TUNNELS,
        MAP_MODES[4]: GREAT_DAMS,
        MAP_MODES[5]: ANCIENT_ENGINEERING,
        MAP_MODES[6]: MEGA_CONSTRUCTION,
        MAP_MODES[7]: ENGINEERING_DISASTERS,
        MAP_MODES[8]: CANALS_WATERWAYS,
        MAP_MODES[9]: FUTURE_MEGAPROJECTS,
    }
    return mode_data.get(mode, [])


def _build_popup_html(item: dict, mode: str) -> str:
    """Build a safe HTML popup for a Folium marker."""
    name = escape(str(item.get("name", "Unknown")))
    country = escape(str(item.get("country", "")))
    note = escape(str(item.get("note", "")))
    year_raw = item.get("year", "")
    year_str = escape(str(abs(year_raw)) + " BC" if isinstance(year_raw, int) and year_raw < 0 else str(year_raw))
    item_type = escape(str(item.get("type", "")))

    # Build detail lines depending on available fields
    detail_lines = []
    if "span_m" in item:
        detail_lines.append(f"<b>Span:</b> {item['span_m']:,.0f} m")
    if "length_km" in item:
        detail_lines.append(f"<b>Length:</b> {item['length_km']:,.1f} km")
    if "height_m" in item:
        detail_lines.append(f"<b>Height:</b> {item['height_m']:,.0f} m")
    if "capacity_gw" in item:
        detail_lines.append(f"<b>Capacity:</b> {item['capacity_gw']:.1f} GW")
    if "casualties" in item:
        detail_lines.append(f"<b>Casualties:</b> {item['casualties']:,}")
    if "span_km" in item and item["span_km"] > 0:
        detail_lines.append(f"<b>Span:</b> {item['span_km']:,.1f} km")

    details_html = "<br>".join(detail_lines)

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:280px;">
        <h4 style="margin:0 0 4px 0;color:#06b6d4;">{name}</h4>
        <div style="color:#ccc;font-size:12px;margin-bottom:4px;">
            {country} &bull; {year_str} &bull; {item_type}
        </div>
        {f'<div style="font-size:12px;color:#ddd;margin-bottom:4px;">{details_html}</div>' if details_html else ''}
        <div style="font-size:11px;color:#aaa;border-top:1px solid #444;padding-top:4px;">
            {note}
        </div>
    </div>
    """
    return html


def _build_folium_map(data: list[dict], mode: str, zoom: int = 2) -> folium.Map:
    """Create a Folium map with markers for the given dataset."""
    # Calculate centroid
    if data:
        avg_lat = sum(d["lat"] for d in data) / len(data)
        avg_lon = sum(d["lon"] for d in data) / len(data)
    else:
        avg_lat, avg_lon = 20.0, 0.0

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    icon_name, icon_color = MODE_FOLIUM_ICONS.get(mode, ("info-sign", "blue"))

    for item in data:
        popup_html = _build_popup_html(item, mode)
        folium.Marker(
            location=[item["lat"], item["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(item.get("name", ""))),
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="glyphicon"),
        ).add_to(m)

    return m


def _make_dataframe(data: list[dict], mode: str) -> pd.DataFrame:
    """Build a display DataFrame from the curated data."""
    if not data:
        return pd.DataFrame()

    # Determine which columns to show based on available keys
    rows = []
    for item in data:
        row = {"Name": item.get("name", ""), "Country": item.get("country", "")}
        year_val = item.get("year", "")
        if isinstance(year_val, int) and year_val < 0:
            row["Year"] = f"{abs(year_val)} BC"
        else:
            row["Year"] = str(year_val)
        row["Type"] = item.get("type", "")

        if "span_m" in item:
            row["Span (m)"] = item["span_m"]
        if "length_km" in item:
            row["Length (km)"] = item["length_km"]
        if "height_m" in item:
            row["Height (m)"] = item["height_m"]
        if "capacity_gw" in item:
            row["Capacity (GW)"] = item["capacity_gw"]
        if "casualties" in item:
            row["Casualties"] = item["casualties"]
        if "span_km" in item:
            row["Span (km)"] = item["span_km"]
        row["Note"] = item.get("note", "")
        row["Lat"] = item["lat"]
        row["Lon"] = item["lon"]
        rows.append(row)

    return pd.DataFrame(rows)


def _make_chart(df: pd.DataFrame, mode: str):
    """Create a matplotlib bar chart for the current mode."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)

    color = MODE_COLORS.get(mode, ACCENT_CYAN)

    # Determine which numeric column to chart
    numeric_col = None
    chart_label = ""
    if "Span (m)" in df.columns:
        numeric_col = "Span (m)"
        chart_label = "Span (m)"
    elif "Length (km)" in df.columns:
        numeric_col = "Length (km)"
        chart_label = "Length (km)"
    elif "Height (m)" in df.columns:
        numeric_col = "Height (m)"
        chart_label = "Height (m)"
    elif "Capacity (GW)" in df.columns:
        numeric_col = "Capacity (GW)"
        chart_label = "Capacity (GW)"
    elif "Casualties" in df.columns:
        numeric_col = "Casualties"
        chart_label = "Casualties"
    elif "Span (km)" in df.columns:
        numeric_col = "Span (km)"
        chart_label = "Span (km)"

    if numeric_col is None or df.empty:
        ax.text(0.5, 0.5, "No numeric data to chart", ha="center", va="center",
                color=TEXT_SECONDARY, fontsize=14, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    # Sort and take top 15
    plot_df = df.dropna(subset=[numeric_col]).sort_values(numeric_col, ascending=False).head(15)

    if plot_df.empty:
        ax.text(0.5, 0.5, "No data to chart", ha="center", va="center",
                color=TEXT_SECONDARY, fontsize=14, transform=ax.transAxes)
        return fig

    names = [n[:22] + "..." if len(str(n)) > 25 else str(n) for n in plot_df["Name"]]
    values = plot_df[numeric_col].astype(float)

    bars = ax.barh(range(len(names)), values, color=color, alpha=0.85, edgecolor=color, linewidth=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8, color=TEXT_PRIMARY)
    ax.set_xlabel(chart_label, color=TEXT_SECONDARY, fontsize=10)
    ax.invert_yaxis()

    # Value labels
    max_val = values.max() if len(values) > 0 else 1
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(bar.get_width() + max_val * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,.1f}" if isinstance(val, float) and val != int(val) else f"{int(val):,}",
                va="center", ha="left", color=TEXT_PRIMARY, fontsize=7)

    ax.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=8)
    ax.tick_params(axis="y", colors=TEXT_PRIMARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3, linewidth=0.5)

    mode_short = mode.split(". ", 1)[-1] if ". " in mode else mode
    ax.set_title(f"Top 15 — {mode_short}", color=TEXT_PRIMARY, fontsize=12, pad=10)
    fig.tight_layout()
    return fig


def _mode_stats(data: list[dict], mode: str) -> dict:
    """Compute summary statistics for a mode."""
    stats = {"total": len(data)}

    countries = set(d.get("country", "") for d in data)
    stats["countries"] = len(countries)

    years = [d["year"] for d in data if isinstance(d.get("year"), (int, float))]
    if years:
        stats["oldest_year"] = min(years)
        stats["newest_year"] = max(years)

    # Mode-specific stats
    if any("span_m" in d for d in data):
        spans = [d["span_m"] for d in data if "span_m" in d and isinstance(d["span_m"], (int, float))]
        if spans:
            stats["max_span_m"] = max(spans)
            stats["avg_span_m"] = sum(spans) / len(spans)

    if any("length_km" in d for d in data):
        lengths = [d["length_km"] for d in data if "length_km" in d]
        if lengths:
            stats["max_length_km"] = max(lengths)
            stats["total_length_km"] = sum(lengths)

    if any("height_m" in d for d in data):
        heights = [d["height_m"] for d in data if "height_m" in d and isinstance(d["height_m"], (int, float))]
        if heights:
            stats["max_height_m"] = max(heights)

    if any("capacity_gw" in d for d in data):
        caps = [d["capacity_gw"] for d in data if "capacity_gw" in d]
        if caps:
            stats["total_capacity_gw"] = sum(caps)
            stats["max_capacity_gw"] = max(caps)

    if any("casualties" in d for d in data):
        cas = [d["casualties"] for d in data if "casualties" in d]
        if cas:
            stats["total_casualties"] = sum(cas)

    if any("span_km" in d for d in data):
        skm = [d["span_km"] for d in data if "span_km" in d and isinstance(d["span_km"], (int, float)) and d["span_km"] > 0]
        if skm:
            stats["max_span_km"] = max(skm)

    return stats


def _display_stats(stats: dict, mode: str):
    """Display statistics in metric columns."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Entries", f"{stats['total']}")
    with col2:
        st.metric("Countries", f"{stats['countries']}")
    with col3:
        if "oldest_year" in stats:
            oldest = stats["oldest_year"]
            if oldest < 0:
                st.metric("Oldest", f"{abs(oldest)} BC")
            else:
                st.metric("Oldest", f"{oldest}")
        elif "total_casualties" in stats:
            st.metric("Total Casualties", f"{stats['total_casualties']:,}")
        else:
            st.metric("Entries", f"{stats['total']}")
    with col4:
        if "max_span_m" in stats:
            st.metric("Max Span", f"{stats['max_span_m']:,.0f} m")
        elif "max_length_km" in stats:
            st.metric("Max Length", f"{stats['max_length_km']:,.1f} km")
        elif "max_height_m" in stats:
            st.metric("Max Height", f"{stats['max_height_m']:,.0f} m")
        elif "total_capacity_gw" in stats:
            st.metric("Total Capacity", f"{stats['total_capacity_gw']:,.1f} GW")
        elif "max_span_km" in stats:
            st.metric("Max Span", f"{stats['max_span_km']:,.1f} km")
        elif "newest_year" in stats:
            st.metric("Newest", f"{stats['newest_year']}")
        else:
            st.metric("Records", f"{stats['total']}")

    # Extra row for modes with more stats
    extra_cols = []
    if "max_height_m" in stats and "max_span_m" in stats:
        extra_cols.append(("Max Height", f"{stats['max_height_m']:,.0f} m"))
    if "total_length_km" in stats:
        extra_cols.append(("Total Length", f"{stats['total_length_km']:,.1f} km"))
    if "total_capacity_gw" in stats:
        if "max_capacity_gw" in stats:
            extra_cols.append(("Largest Plant", f"{stats['max_capacity_gw']:,.1f} GW"))
    if "avg_span_m" in stats:
        extra_cols.append(("Avg Span", f"{stats['avg_span_m']:,.0f} m"))

    if extra_cols:
        cols = st.columns(len(extra_cols))
        for i, (label, value) in enumerate(extra_cols):
            with cols[i]:
                st.metric(label, value)


@st.cache_data(ttl=3600)
def _query_overpass_bridges(lat: float, lon: float, radius_km: float) -> list[dict]:
    """Query Overpass API for bridges, tunnels, and dams near a point."""
    from src.overpass_client import query_overpass

    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["man_made"="bridge"](around:{radius_m},{lat},{lon});
  way["man_made"="bridge"](around:{radius_m},{lat},{lon});
  node["bridge"="yes"](around:{radius_m},{lat},{lon});
  way["bridge"="yes"](around:{radius_m},{lat},{lon});
  node["tunnel"="yes"](around:{radius_m},{lat},{lon});
  way["tunnel"="yes"](around:{radius_m},{lat},{lon});
  node["waterway"="dam"](around:{radius_m},{lat},{lon});
  way["waterway"="dam"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []

    elements = result.get("elements", [])
    # Build node lookup
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        lat_f, lon_f = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat_f, lon_f = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
            if coords:
                lat_f = sum(c[0] for c in coords) / len(coords)
                lon_f = sum(c[1] for c in coords) / len(coords)

        if lat_f is None:
            continue

        # Determine category
        category = "Bridge"
        color = ACCENT_CYAN
        if tags.get("tunnel") == "yes":
            category = "Tunnel"
            color = ACCENT_VIOLET
        elif tags.get("waterway") == "dam":
            category = "Dam"
            color = ACCENT_BLUE
        elif tags.get("man_made") == "bridge" or tags.get("bridge") == "yes":
            category = "Bridge"
            color = ACCENT_CYAN

        name = tags.get("name", tags.get("name:en", "Unnamed"))
        features.append({
            "name": name,
            "category": category,
            "color": color,
            "lat": lat_f,
            "lon": lon_f,
            "type": tags.get("bridge:structure", tags.get("bridge", category)),
            "note": tags.get("description", tags.get("note", "")),
            "osm_id": el.get("id"),
        })

    return features


def _build_overpass_map(features: list[dict], center_lat: float, center_lon: float) -> folium.Map:
    """Build a Folium map from Overpass query results."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB dark_matter",
    )

    cat_icons = {
        "Bridge": ("info-sign", "blue"),
        "Tunnel": ("road", "purple"),
        "Dam": ("tint", "darkblue"),
    }

    for feat in features:
        icon_name, icon_color = cat_icons.get(feat["category"], ("info-sign", "gray"))
        name_safe = escape(str(feat.get("name", "Unnamed")))
        cat_safe = escape(str(feat.get("category", "")))
        type_safe = escape(str(feat.get("type", "")))
        note_safe = escape(str(feat.get("note", "")))

        popup_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:250px;">
            <h4 style="margin:0 0 4px 0;color:#06b6d4;">{name_safe}</h4>
            <div style="color:#ccc;font-size:12px;">{cat_safe} &bull; {type_safe}</div>
            {f'<div style="font-size:11px;color:#aaa;margin-top:4px;">{note_safe}</div>' if note_safe else ''}
        </div>
        """

        folium.Marker(
            location=[feat["lat"], feat["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=name_safe,
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="glyphicon"),
        ).add_to(m)

    return m


# ═══════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════

def render_bridge_maps_tab():
    """Main render function for the Bridges & Engineering Marvels tab."""

    # ── Tab Header ──
    st.markdown(
        '<div class="tab-header amber"><h4>\U0001f309 Bridges & Engineering Marvels</h4>'
        '<p>Famous bridges, tunnels, dams, mega-structures & 10 maps</p></div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════
    # MODE SELECTION
    # ══════════════════════════════════════════════════════════════
    st.markdown("#### Select Map Mode")

    mode = st.selectbox(
        "Choose a category to explore",
        MAP_MODES,
        index=0,
        key="bridge_map_mode",
    )

    # ══════════════════════════════════════════════════════════════
    # DESCRIPTION
    # ══════════════════════════════════════════════════════════════
    description = MODE_DESCRIPTIONS.get(mode, "")
    if description:
        st.info(description)

    # ══════════════════════════════════════════════════════════════
    # GET DATA
    # ══════════════════════════════════════════════════════════════
    data = _get_data_for_mode(mode)

    if not data:
        st.warning("No data available for this mode.")
        return

    # ══════════════════════════════════════════════════════════════
    # STATISTICS
    # ══════════════════════════════════════════════════════════════
    st.markdown("#### Key Statistics")
    stats = _mode_stats(data, mode)
    _display_stats(stats, mode)

    # ══════════════════════════════════════════════════════════════
    # BAR CHART
    # ══════════════════════════════════════════════════════════════
    df = _make_dataframe(data, mode)

    st.markdown("#### Rankings Chart")
    fig = _make_chart(df, mode)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ══════════════════════════════════════════════════════════════
    # INTERACTIVE MAP
    # ══════════════════════════════════════════════════════════════
    st.markdown("#### Interactive Map")

    # Determine appropriate zoom level
    zoom_level = 2
    lats = [d["lat"] for d in data]
    lons = [d["lon"] for d in data]
    lat_range = max(lats) - min(lats) if lats else 0
    lon_range = max(lons) - min(lons) if lons else 0

    if lat_range < 10 and lon_range < 20:
        zoom_level = 5
    elif lat_range < 30 and lon_range < 60:
        zoom_level = 3
    else:
        zoom_level = 2

    fmap = _build_folium_map(data, mode, zoom=zoom_level)
    components.html(fmap._repr_html_(), height=500)

    # ══════════════════════════════════════════════════════════════
    # DATA TABLE
    # ══════════════════════════════════════════════════════════════
    st.markdown("#### Data Table")
    st.dataframe(df, width="stretch")

    # ══════════════════════════════════════════════════════════════
    # CSV DOWNLOAD
    # ══════════════════════════════════════════════════════════════
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    mode_slug = mode.split(". ", 1)[-1].lower().replace(" ", "_").replace("'", "")
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"bridge_maps_{mode_slug}.csv",
        mime="text/csv",
        key=f"bridge_csv_{mode_slug}",
    )

    # ══════════════════════════════════════════════════════════════
    # OVERPASS NEARBY SEARCH (BONUS)
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Discover Nearby Bridges, Tunnels & Dams (OpenStreetMap)")
    st.caption(
        "Use the Overpass API to find engineering features near any point. "
        "This queries OpenStreetMap in real time — no API key needed."
    )

    col_lat, col_lon, col_rad = st.columns(3)
    with col_lat:
        search_lat = st.number_input(
            "Latitude", value=48.8566, format="%.4f",
            min_value=-90.0, max_value=90.0, key="bridge_search_lat",
        )
    with col_lon:
        search_lon = st.number_input(
            "Longitude", value=2.3522, format="%.4f",
            min_value=-180.0, max_value=180.0, key="bridge_search_lon",
        )
    with col_rad:
        search_radius = st.slider(
            "Radius (km)", 1, 30, 5, key="bridge_search_radius",
            help="Search radius for Overpass query",
        )

    # Preset locations for quick search
    SEARCH_PRESETS = {
        "Custom": None,
        "Paris, France": (48.8566, 2.3522),
        "London, UK": (51.5074, -0.1278),
        "New York, USA": (40.7128, -74.0060),
        "San Francisco, USA": (37.7749, -122.4194),
        "Istanbul, Turkey": (41.0082, 28.9784),
        "Sydney, Australia": (-33.8688, 151.2093),
        "Tokyo, Japan": (35.6762, 139.6503),
        "Rome, Italy": (41.9028, 12.4964),
        "Shanghai, China": (31.2304, 121.4737),
        "Dubai, UAE": (25.2048, 55.2708),
    }

    preset = st.selectbox(
        "Quick Location Presets",
        list(SEARCH_PRESETS.keys()),
        key="bridge_search_preset",
    )
    if preset != "Custom" and SEARCH_PRESETS.get(preset):
        search_lat, search_lon = SEARCH_PRESETS[preset]

    if st.button("Search Nearby", key="bridge_search_btn", type="primary"):
        st.session_state["bridge_overpass_params"] = {
            "lat": search_lat, "lon": search_lon, "radius": search_radius,
        }

    if "bridge_overpass_params" in st.session_state:
        params = st.session_state["bridge_overpass_params"]
        with st.spinner("Querying OpenStreetMap for bridges, tunnels, and dams..."):
            features = _query_overpass_bridges(params["lat"], params["lon"], params["radius"])

        if not features:
            st.warning(
                "No bridges, tunnels, or dams found in this area. "
                "Try a larger radius or a different location."
            )
        else:
            # Stats
            bridges_count = sum(1 for f in features if f["category"] == "Bridge")
            tunnels_count = sum(1 for f in features if f["category"] == "Tunnel")
            dams_count = sum(1 for f in features if f["category"] == "Dam")
            named_count = sum(1 for f in features if f["name"] != "Unnamed")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Found", len(features))
            with c2:
                st.metric("Bridges", bridges_count)
            with c3:
                st.metric("Tunnels", tunnels_count)
            with c4:
                st.metric("Dams", dams_count)

            # Map
            osm_map = _build_overpass_map(features, params["lat"], params["lon"])
            components.html(osm_map._repr_html_(), height=500)

            # Table
            osm_df = pd.DataFrame([
                {
                    "Name": f["name"],
                    "Category": f["category"],
                    "Type": f["type"],
                    "Lat": round(f["lat"], 5),
                    "Lon": round(f["lon"], 5),
                    "OSM ID": f.get("osm_id", ""),
                }
                for f in features
            ])
            st.dataframe(osm_df, width="stretch")

            # Download
            osm_csv = io.StringIO()
            osm_df.to_csv(osm_csv, index=False)
            st.download_button(
                label="Download Nearby Features CSV",
                data=osm_csv.getvalue(),
                file_name="nearby_bridges_tunnels_dams.csv",
                mime="text/csv",
                key="bridge_osm_csv",
            )
