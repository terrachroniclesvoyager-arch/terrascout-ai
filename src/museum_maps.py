# -*- coding: utf-8 -*-
"""
Museums & Galleries Maps module for TerraScout AI.
Provides 10 interactive map modes covering the world's greatest museums,
modern art, science centres, natural history, war memorials, ancient
civilizations, art capitals, open-air museums, quirky collections, and
art auction houses / fairs.  All data is hardcoded for offline reliability.
"""

import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module

# =====================================================================
# COLOUR PALETTE (matches TerraScout glassmorphism theme)
# =====================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
ACCENT_CYAN = "#06b6d4"
ACCENT_PINK = "#ec4899"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"

MODE_COLORS = {
    "World's Greatest Museums": "#f59e0b",
    "Modern & Contemporary Art": "#ec4899",
    "Science & Technology Museums": "#06b6d4",
    "Natural History Museums": "#10b981",
    "War & Military Museums": "#ef4444",
    "Ancient Civilization Museums": "#f97316",
    "Art Capitals": "#8b5cf6",
    "Open-Air Museums": "#14b8a6",
    "Quirky & Unusual Museums": "#a855f7",
    "Art Auction Houses & Markets": "#38bdf8",
}

MODE_LIST = list(MODE_COLORS.keys())

# =====================================================================
# HELPER: base dark map
# =====================================================================

def _base_map(center=None, zoom=2):
    if center is None:
        center = [20, 0]
    return folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        width="100%",
        height=500,
    )


def _popup_html(title, lines, color="#06b6d4"):
    safe_title = html_module.escape(str(title))
    body = "".join(
        f"<tr><td style='color:#8b97b0;padding:2px 6px;'>{html_module.escape(str(k))}</td>"
        f"<td style='color:#e8ecf4;padding:2px 6px;'>{html_module.escape(str(v))}</td></tr>"
        for k, v in lines
    )
    return (
        f"<div style='background:#111827;border:1px solid {color};border-radius:8px;"
        f"padding:8px 10px;min-width:200px;font-family:Inter,sans-serif;'>"
        f"<b style='color:{color};font-size:13px;'>{safe_title}</b>"
        f"<table style='margin-top:4px;'>{body}</table></div>"
    )


# =====================================================================
# 1. WORLD'S GREATEST MUSEUMS  (25+)
# =====================================================================
GREATEST_MUSEUMS = [
    {"name": "Louvre Museum", "city": "Paris", "country": "France", "lat": 48.8606, "lon": 2.3376, "founded": 1793, "type": "Art / Universal", "visitors_m": 8.9},
    {"name": "British Museum", "city": "London", "country": "UK", "lat": 51.5194, "lon": -0.1270, "founded": 1753, "type": "Universal", "visitors_m": 5.8},
    {"name": "Metropolitan Museum of Art", "city": "New York", "country": "USA", "lat": 40.7794, "lon": -73.9632, "founded": 1870, "type": "Art / Universal", "visitors_m": 5.4},
    {"name": "Smithsonian National Museum", "city": "Washington D.C.", "country": "USA", "lat": 38.8881, "lon": -77.0260, "founded": 1846, "type": "Universal", "visitors_m": 4.2},
    {"name": "State Hermitage Museum", "city": "Saint Petersburg", "country": "Russia", "lat": 59.9398, "lon": 30.3146, "founded": 1764, "type": "Art / Universal", "visitors_m": 4.2},
    {"name": "Vatican Museums", "city": "Vatican City", "country": "Vatican", "lat": 41.9065, "lon": 12.4536, "founded": 1506, "type": "Art / Religious", "visitors_m": 6.9},
    {"name": "Uffizi Gallery", "city": "Florence", "country": "Italy", "lat": 43.7677, "lon": 11.2553, "founded": 1581, "type": "Art", "visitors_m": 4.4},
    {"name": "Museo del Prado", "city": "Madrid", "country": "Spain", "lat": 40.4138, "lon": -3.6921, "founded": 1819, "type": "Art", "visitors_m": 3.5},
    {"name": "Rijksmuseum", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3600, "lon": 4.8852, "founded": 1800, "type": "Art / History", "visitors_m": 2.7},
    {"name": "National Gallery", "city": "London", "country": "UK", "lat": 51.5089, "lon": -0.1283, "founded": 1824, "type": "Art", "visitors_m": 5.9},
    {"name": "Musee d'Orsay", "city": "Paris", "country": "France", "lat": 48.8600, "lon": 2.3266, "founded": 1986, "type": "Impressionist Art", "visitors_m": 3.7},
    {"name": "National Palace Museum", "city": "Taipei", "country": "Taiwan", "lat": 25.1024, "lon": 121.5485, "founded": 1925, "type": "Chinese Art", "visitors_m": 3.8},
    {"name": "Pergamon Museum", "city": "Berlin", "country": "Germany", "lat": 52.5213, "lon": 13.3968, "founded": 1930, "type": "Archaeology", "visitors_m": 2.3},
    {"name": "Tokyo National Museum", "city": "Tokyo", "country": "Japan", "lat": 35.7189, "lon": 139.7766, "founded": 1872, "type": "Art / History", "visitors_m": 2.1},
    {"name": "National Museum of China", "city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.3914, "founded": 1912, "type": "History / Art", "visitors_m": 7.6},
    {"name": "State Tretyakov Gallery", "city": "Moscow", "country": "Russia", "lat": 55.7415, "lon": 37.6208, "founded": 1856, "type": "Russian Art", "visitors_m": 2.2},
    {"name": "Art Institute of Chicago", "city": "Chicago", "country": "USA", "lat": 41.8796, "lon": -87.6237, "founded": 1879, "type": "Art", "visitors_m": 1.7},
    {"name": "Galleria Borghese", "city": "Rome", "country": "Italy", "lat": 41.9142, "lon": 12.4922, "founded": 1903, "type": "Art", "visitors_m": 0.6},
    {"name": "Egyptian Museum", "city": "Cairo", "country": "Egypt", "lat": 30.0478, "lon": 31.2336, "founded": 1902, "type": "Archaeology", "visitors_m": 1.5},
    {"name": "National Museum of Korea", "city": "Seoul", "country": "South Korea", "lat": 37.5209, "lon": 126.9806, "founded": 1945, "type": "History / Art", "visitors_m": 3.4},
    {"name": "Victoria and Albert Museum", "city": "London", "country": "UK", "lat": 51.4966, "lon": -0.1722, "founded": 1852, "type": "Decorative Arts", "visitors_m": 3.9},
    {"name": "Kunsthistorisches Museum", "city": "Vienna", "country": "Austria", "lat": 48.2034, "lon": 16.3614, "founded": 1891, "type": "Art / History", "visitors_m": 1.7},
    {"name": "Museo Nacional de Antropologia", "city": "Mexico City", "country": "Mexico", "lat": 19.4260, "lon": -99.1862, "founded": 1964, "type": "Anthropology", "visitors_m": 2.4},
    {"name": "State Museum of Fine Arts", "city": "Moscow", "country": "Russia", "lat": 55.7473, "lon": 37.6050, "founded": 1912, "type": "Art", "visitors_m": 1.3},
    {"name": "National Museum of India", "city": "New Delhi", "country": "India", "lat": 28.6117, "lon": 77.2195, "founded": 1949, "type": "Art / History", "visitors_m": 1.0},
    {"name": "Topkapi Palace Museum", "city": "Istanbul", "country": "Turkey", "lat": 41.0115, "lon": 28.9833, "founded": 1924, "type": "History / Art", "visitors_m": 2.0},
    {"name": "Museo Egizio", "city": "Turin", "country": "Italy", "lat": 45.0686, "lon": 7.6842, "founded": 1824, "type": "Egyptology", "visitors_m": 0.9},
    {"name": "Getty Center", "city": "Los Angeles", "country": "USA", "lat": 34.0780, "lon": -118.4741, "founded": 1997, "type": "Art", "visitors_m": 1.8},
    {"name": "Alte Pinakothek", "city": "Munich", "country": "Germany", "lat": 48.1483, "lon": 11.5700, "founded": 1836, "type": "Old Masters", "visitors_m": 0.5},
    {"name": "Museo Nacional de Bellas Artes", "city": "Buenos Aires", "country": "Argentina", "lat": -34.5839, "lon": -58.3931, "founded": 1896, "type": "Art", "visitors_m": 1.0},
    {"name": "National Gallery of Art", "city": "Washington D.C.", "country": "USA", "lat": 38.8913, "lon": -77.0199, "founded": 1937, "type": "Art", "visitors_m": 4.1},
]

# =====================================================================
# 2. MODERN & CONTEMPORARY ART  (20+)
# =====================================================================
MODERN_ART = [
    {"name": "MoMA", "city": "New York", "country": "USA", "lat": 40.7614, "lon": -73.9776, "founded": 1929, "focus": "Modern / Contemporary", "visitors_m": 2.7},
    {"name": "Tate Modern", "city": "London", "country": "UK", "lat": 51.5076, "lon": -0.0994, "founded": 2000, "focus": "Contemporary", "visitors_m": 5.9},
    {"name": "Centre Pompidou", "city": "Paris", "country": "France", "lat": 48.8607, "lon": 2.3524, "founded": 1977, "focus": "Modern / Contemporary", "visitors_m": 3.3},
    {"name": "Guggenheim Bilbao", "city": "Bilbao", "country": "Spain", "lat": 43.2687, "lon": -2.9340, "founded": 1997, "focus": "Contemporary", "visitors_m": 1.2},
    {"name": "MOCA Los Angeles", "city": "Los Angeles", "country": "USA", "lat": 34.0531, "lon": -118.2500, "founded": 1979, "focus": "Contemporary", "visitors_m": 0.4},
    {"name": "Saatchi Gallery", "city": "London", "country": "UK", "lat": 51.4907, "lon": -0.1574, "founded": 1985, "focus": "Contemporary British", "visitors_m": 1.5},
    {"name": "Guggenheim New York", "city": "New York", "country": "USA", "lat": 40.7830, "lon": -73.9590, "founded": 1939, "focus": "Modern / Contemporary", "visitors_m": 1.2},
    {"name": "Whitney Museum", "city": "New York", "country": "USA", "lat": 40.7396, "lon": -74.0089, "founded": 1931, "focus": "American Art", "visitors_m": 0.8},
    {"name": "Hamburger Bahnhof", "city": "Berlin", "country": "Germany", "lat": 52.5285, "lon": 13.3724, "founded": 1996, "focus": "Contemporary", "visitors_m": 0.4},
    {"name": "Stedelijk Museum", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3580, "lon": 4.8798, "founded": 1895, "focus": "Modern / Contemporary", "visitors_m": 0.7},
    {"name": "MAXXI", "city": "Rome", "country": "Italy", "lat": 41.9285, "lon": 12.4653, "founded": 2010, "focus": "Contemporary Art / Architecture", "visitors_m": 0.4},
    {"name": "Louisiana Museum", "city": "Humlebaek", "country": "Denmark", "lat": 55.9709, "lon": 12.5419, "founded": 1958, "focus": "Modern / Contemporary", "visitors_m": 0.7},
    {"name": "Mori Art Museum", "city": "Tokyo", "country": "Japan", "lat": 35.6604, "lon": 139.7292, "founded": 2003, "focus": "Contemporary", "visitors_m": 1.6},
    {"name": "Museo Reina Sofia", "city": "Madrid", "country": "Spain", "lat": 40.4087, "lon": -3.6943, "founded": 1992, "focus": "Modern Spanish", "visitors_m": 4.4},
    {"name": "Palais de Tokyo", "city": "Paris", "country": "France", "lat": 48.8640, "lon": 2.2980, "founded": 2002, "focus": "Contemporary", "visitors_m": 0.9},
    {"name": "New Museum", "city": "New York", "country": "USA", "lat": 40.7224, "lon": -73.9930, "founded": 1977, "focus": "Contemporary", "visitors_m": 0.4},
    {"name": "Fondation Louis Vuitton", "city": "Paris", "country": "France", "lat": 48.8808, "lon": 2.2637, "founded": 2014, "focus": "Contemporary", "visitors_m": 1.2},
    {"name": "Zeitz MOCAA", "city": "Cape Town", "country": "South Africa", "lat": -33.9083, "lon": 18.4183, "founded": 2017, "focus": "Contemporary African", "visitors_m": 0.3},
    {"name": "SFMOMA", "city": "San Francisco", "country": "USA", "lat": 37.7857, "lon": -122.4011, "founded": 1935, "focus": "Modern / Contemporary", "visitors_m": 0.7},
    {"name": "Pinault Collection (Bourse)", "city": "Paris", "country": "France", "lat": 48.8631, "lon": 2.3412, "founded": 2021, "focus": "Contemporary", "visitors_m": 0.8},
    {"name": "K21 Kunstsammlung", "city": "Dusseldorf", "country": "Germany", "lat": 51.2174, "lon": 6.7732, "founded": 2002, "focus": "Contemporary", "visitors_m": 0.3},
    {"name": "Garage Museum", "city": "Moscow", "country": "Russia", "lat": 55.7312, "lon": 37.6032, "founded": 2008, "focus": "Contemporary Russian", "visitors_m": 0.5},
    {"name": "Broad Museum", "city": "Los Angeles", "country": "USA", "lat": 34.0544, "lon": -118.2508, "founded": 2015, "focus": "Contemporary", "visitors_m": 0.9},
    {"name": "Kiasma Museum", "city": "Helsinki", "country": "Finland", "lat": 60.1718, "lon": 24.9371, "founded": 1998, "focus": "Contemporary Finnish", "visitors_m": 0.3},
    {"name": "MACBA Barcelona", "city": "Barcelona", "country": "Spain", "lat": 41.3833, "lon": 2.1677, "founded": 1995, "focus": "Contemporary", "visitors_m": 0.4},
    {"name": "Museum Brandhorst", "city": "Munich", "country": "Germany", "lat": 48.1500, "lon": 11.5742, "founded": 2009, "focus": "Contemporary", "visitors_m": 0.2},
]

# =====================================================================
# 3. SCIENCE & TECHNOLOGY MUSEUMS  (20+)
# =====================================================================
SCIENCE_MUSEUMS = [
    {"name": "Smithsonian Air & Space", "city": "Washington D.C.", "country": "USA", "lat": 38.8882, "lon": -77.0199, "founded": 1946, "focus": "Aviation / Space", "visitors_m": 3.2},
    {"name": "Science Museum London", "city": "London", "country": "UK", "lat": 51.4978, "lon": -0.1745, "founded": 1857, "focus": "Science / Industry", "visitors_m": 3.3},
    {"name": "Deutsches Museum", "city": "Munich", "country": "Germany", "lat": 48.1298, "lon": 11.5833, "founded": 1903, "focus": "Science / Technology", "visitors_m": 1.5},
    {"name": "CERN Science Gateway", "city": "Geneva", "country": "Switzerland", "lat": 46.2330, "lon": 6.0557, "founded": 2023, "focus": "Particle Physics", "visitors_m": 0.5},
    {"name": "Exploratorium", "city": "San Francisco", "country": "USA", "lat": 37.8017, "lon": -122.3976, "founded": 1969, "focus": "Interactive Science", "visitors_m": 0.9},
    {"name": "Cite des Sciences", "city": "Paris", "country": "France", "lat": 48.8958, "lon": 2.3877, "founded": 1986, "focus": "Science / Industry", "visitors_m": 2.4},
    {"name": "National Science Museum", "city": "Tokyo", "country": "Japan", "lat": 35.7163, "lon": 139.7764, "founded": 1871, "focus": "Science / Nature", "visitors_m": 2.7},
    {"name": "CosmoCaixa Barcelona", "city": "Barcelona", "country": "Spain", "lat": 41.4131, "lon": 2.1316, "founded": 2004, "focus": "Interactive Science", "visitors_m": 1.0},
    {"name": "California Science Center", "city": "Los Angeles", "country": "USA", "lat": 34.0153, "lon": -118.2866, "founded": 1951, "focus": "Science / Shuttle Endeavour", "visitors_m": 2.0},
    {"name": "Museum of Science Boston", "city": "Boston", "country": "USA", "lat": 42.3677, "lon": -71.0711, "founded": 1830, "focus": "Science / Engineering", "visitors_m": 1.5},
    {"name": "Copernicus Science Centre", "city": "Warsaw", "country": "Poland", "lat": 52.2420, "lon": 21.0289, "founded": 2010, "focus": "Interactive Science", "visitors_m": 1.1},
    {"name": "NEMO Science Museum", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3740, "lon": 4.9123, "founded": 1997, "focus": "Interactive Science", "visitors_m": 0.7},
    {"name": "Powerhouse Museum", "city": "Sydney", "country": "Australia", "lat": -33.8785, "lon": 151.2003, "founded": 1880, "focus": "Science / Design", "visitors_m": 0.5},
    {"name": "Kennedy Space Center", "city": "Merritt Island", "country": "USA", "lat": 28.5729, "lon": -80.6490, "founded": 1967, "focus": "Space Exploration", "visitors_m": 1.7},
    {"name": "Nobel Prize Museum", "city": "Stockholm", "country": "Sweden", "lat": 59.3250, "lon": 18.0710, "founded": 2001, "focus": "Nobel Prizes", "visitors_m": 0.3},
    {"name": "Museo della Scienza", "city": "Milan", "country": "Italy", "lat": 45.4627, "lon": 9.1707, "founded": 1953, "focus": "Leonardo / Tech", "visitors_m": 0.5},
    {"name": "Technisches Museum Wien", "city": "Vienna", "country": "Austria", "lat": 48.1916, "lon": 16.3183, "founded": 1918, "focus": "Technology", "visitors_m": 0.4},
    {"name": "Hong Kong Science Museum", "city": "Hong Kong", "country": "China", "lat": 22.3013, "lon": 114.1774, "founded": 1991, "focus": "Interactive Science", "visitors_m": 1.0},
    {"name": "Science Centre Singapore", "city": "Singapore", "country": "Singapore", "lat": 1.3329, "lon": 103.7361, "founded": 1977, "focus": "Interactive Science", "visitors_m": 1.0},
    {"name": "Museum of Science & Industry", "city": "Chicago", "country": "USA", "lat": 41.7906, "lon": -87.5831, "founded": 1933, "focus": "Industry / Tech", "visitors_m": 1.5},
    {"name": "Phaeno Science Centre", "city": "Wolfsburg", "country": "Germany", "lat": 52.4311, "lon": 10.7930, "founded": 2005, "focus": "Interactive Science", "visitors_m": 0.3},
    {"name": "Ontario Science Centre", "city": "Toronto", "country": "Canada", "lat": 43.7168, "lon": -79.3386, "founded": 1969, "focus": "Interactive Science", "visitors_m": 0.9},
    {"name": "Museo Interactivo Mirador", "city": "Santiago", "country": "Chile", "lat": -33.5098, "lon": -70.6107, "founded": 2000, "focus": "Interactive Science", "visitors_m": 0.8},
    {"name": "Computer History Museum", "city": "Mountain View", "country": "USA", "lat": 37.4143, "lon": -122.0775, "founded": 1996, "focus": "Computing History", "visitors_m": 0.2},
]

# =====================================================================
# 4. NATURAL HISTORY MUSEUMS  (20+)
# =====================================================================
NATURAL_HISTORY = [
    {"name": "American Museum of Natural History", "city": "New York", "country": "USA", "lat": 40.7813, "lon": -73.9740, "founded": 1869, "highlights": "Dinosaurs, Planetarium", "visitors_m": 4.0},
    {"name": "Natural History Museum London", "city": "London", "country": "UK", "lat": 51.4967, "lon": -0.1764, "founded": 1881, "highlights": "Dippy, Wildlife Garden", "visitors_m": 5.4},
    {"name": "Field Museum", "city": "Chicago", "country": "USA", "lat": 41.8663, "lon": -87.6170, "founded": 1893, "highlights": "Sue the T. Rex", "visitors_m": 1.6},
    {"name": "Museum fur Naturkunde", "city": "Berlin", "country": "Germany", "lat": 52.5300, "lon": 13.3796, "founded": 1810, "highlights": "Giraffatitan", "visitors_m": 0.8},
    {"name": "MNHN Paris", "city": "Paris", "country": "France", "lat": 48.8417, "lon": 2.3562, "founded": 1635, "highlights": "Grande Galerie", "visitors_m": 2.1},
    {"name": "Smithsonian Natural History", "city": "Washington D.C.", "country": "USA", "lat": 38.8913, "lon": -77.0261, "founded": 1910, "highlights": "Hope Diamond", "visitors_m": 4.2},
    {"name": "Naturhistorisches Museum", "city": "Vienna", "country": "Austria", "lat": 48.2052, "lon": 16.3603, "founded": 1889, "highlights": "Venus of Willendorf", "visitors_m": 0.8},
    {"name": "Museo de La Plata", "city": "La Plata", "country": "Argentina", "lat": -34.9068, "lon": -57.9370, "founded": 1884, "highlights": "Paleontology Hall", "visitors_m": 0.4},
    {"name": "Royal Ontario Museum", "city": "Toronto", "country": "Canada", "lat": 43.6677, "lon": -79.3948, "founded": 1914, "highlights": "Crystal Gallery", "visitors_m": 1.3},
    {"name": "National Museum of Nature & Science", "city": "Tokyo", "country": "Japan", "lat": 35.7163, "lon": 139.7764, "founded": 1871, "highlights": "Dinosaurs, Tech", "visitors_m": 2.7},
    {"name": "South Australian Museum", "city": "Adelaide", "country": "Australia", "lat": -34.9211, "lon": 138.6010, "founded": 1856, "highlights": "Aboriginal Heritage", "visitors_m": 0.9},
    {"name": "Swedish Museum of Natural History", "city": "Stockholm", "country": "Sweden", "lat": 59.3694, "lon": 18.0524, "founded": 1819, "highlights": "Cosmonova IMAX", "visitors_m": 0.6},
    {"name": "Melbourne Museum", "city": "Melbourne", "country": "Australia", "lat": -37.8031, "lon": 144.9717, "founded": 2000, "highlights": "Bunjilaka Aboriginal Centre", "visitors_m": 1.8},
    {"name": "Iziko South African Museum", "city": "Cape Town", "country": "South Africa", "lat": -33.9279, "lon": 18.4130, "founded": 1825, "highlights": "Rock Art, Whale Hall", "visitors_m": 0.3},
    {"name": "Peabody Museum", "city": "New Haven", "country": "USA", "lat": 41.3163, "lon": -72.9223, "founded": 1866, "highlights": "Age of Reptiles Mural", "visitors_m": 0.2},
    {"name": "Lee Kong Chian Museum", "city": "Singapore", "country": "Singapore", "lat": 1.2966, "lon": 103.7717, "founded": 2015, "highlights": "Diplodocid Sauropods", "visitors_m": 0.2},
    {"name": "Museo de Ciencias Naturales", "city": "Madrid", "country": "Spain", "lat": 40.4405, "lon": -3.6893, "founded": 1771, "highlights": "Megatherium Skeleton", "visitors_m": 0.5},
    {"name": "Canadian Museum of Nature", "city": "Ottawa", "country": "Canada", "lat": 45.4127, "lon": -75.6888, "founded": 1856, "highlights": "Blue Whale Gallery", "visitors_m": 0.6},
    {"name": "Senckenberg Museum", "city": "Frankfurt", "country": "Germany", "lat": 50.1173, "lon": 8.6524, "founded": 1907, "highlights": "Dinosaur Hall", "visitors_m": 0.5},
    {"name": "Oxford University Museum", "city": "Oxford", "country": "UK", "lat": 51.7585, "lon": -1.2556, "founded": 1860, "highlights": "Dodo, Darwin Debate", "visitors_m": 0.7},
    {"name": "Nairobi National Museum", "city": "Nairobi", "country": "Kenya", "lat": -1.2741, "lon": 36.8142, "founded": 1930, "highlights": "Human Origins", "visitors_m": 0.3},
    {"name": "Museo Paleontologico Egidio Feruglio", "city": "Trelew", "country": "Argentina", "lat": -43.2532, "lon": -65.3075, "founded": 1990, "highlights": "Patagotitan Mayorum", "visitors_m": 0.1},
    {"name": "Natural History Museum of Denmark", "city": "Copenhagen", "country": "Denmark", "lat": 55.6866, "lon": 12.5726, "founded": 1870, "highlights": "Botanical & Zoological", "visitors_m": 0.3},
    {"name": "Naturalis Biodiversity Center", "city": "Leiden", "country": "Netherlands", "lat": 52.1638, "lon": 4.4625, "founded": 1820, "highlights": "T. Rex Trix", "visitors_m": 0.4},
]

# =====================================================================
# 5. WAR & MILITARY MUSEUMS  (20+)
# =====================================================================
WAR_MUSEUMS = [
    {"name": "Imperial War Museum", "city": "London", "country": "UK", "lat": 51.4958, "lon": -0.1086, "founded": 1917, "focus": "World Wars / Conflict", "conflict": "General"},
    {"name": "National WWII Museum", "city": "New Orleans", "country": "USA", "lat": 29.9431, "lon": -90.0706, "founded": 2000, "focus": "World War II", "conflict": "WWII"},
    {"name": "Hiroshima Peace Memorial", "city": "Hiroshima", "country": "Japan", "lat": 34.3955, "lon": 132.4536, "founded": 1955, "focus": "Atomic Bombing / Peace", "conflict": "WWII"},
    {"name": "War Remnants Museum", "city": "Ho Chi Minh City", "country": "Vietnam", "lat": 10.7794, "lon": 106.6923, "founded": 1975, "focus": "Vietnam War", "conflict": "Vietnam War"},
    {"name": "Yad Vashem", "city": "Jerusalem", "country": "Israel", "lat": 31.7741, "lon": 35.1754, "founded": 1953, "focus": "Holocaust", "conflict": "WWII"},
    {"name": "Auschwitz-Birkenau Museum", "city": "Oswiecim", "country": "Poland", "lat": 50.0343, "lon": 19.1781, "founded": 1947, "focus": "Holocaust", "conflict": "WWII"},
    {"name": "Australian War Memorial", "city": "Canberra", "country": "Australia", "lat": -35.2809, "lon": 149.1475, "founded": 1941, "focus": "Australian Military", "conflict": "General"},
    {"name": "Musee de l'Armee", "city": "Paris", "country": "France", "lat": 48.8550, "lon": 2.3125, "founded": 1905, "focus": "French Military", "conflict": "General"},
    {"name": "Canadian War Museum", "city": "Ottawa", "country": "Canada", "lat": 45.4170, "lon": -75.7170, "founded": 1880, "focus": "Canadian Conflicts", "conflict": "General"},
    {"name": "Normandy American Cemetery", "city": "Colleville-sur-Mer", "country": "France", "lat": 49.3597, "lon": -0.8604, "founded": 1956, "focus": "D-Day / WWII", "conflict": "WWII"},
    {"name": "USS Arizona Memorial", "city": "Honolulu", "country": "USA", "lat": 21.3649, "lon": -157.9500, "founded": 1962, "focus": "Pearl Harbor", "conflict": "WWII"},
    {"name": "Tuol Sleng Genocide Museum", "city": "Phnom Penh", "country": "Cambodia", "lat": 11.5497, "lon": 104.9174, "founded": 1980, "focus": "Khmer Rouge Genocide", "conflict": "Cambodian Genocide"},
    {"name": "9/11 Memorial & Museum", "city": "New York", "country": "USA", "lat": 40.7115, "lon": -74.0134, "founded": 2014, "focus": "9/11 Attacks", "conflict": "War on Terror"},
    {"name": "German Tank Museum", "city": "Munster", "country": "Germany", "lat": 52.9756, "lon": 10.0849, "founded": 1983, "focus": "Armoured Vehicles", "conflict": "General"},
    {"name": "Apartheid Museum", "city": "Johannesburg", "country": "South Africa", "lat": -26.2384, "lon": 28.0107, "founded": 2001, "focus": "Apartheid / Resistance", "conflict": "Apartheid"},
    {"name": "Imperial War Museum Duxford", "city": "Duxford", "country": "UK", "lat": 52.0908, "lon": 0.1319, "founded": 1976, "focus": "Aviation / Military", "conflict": "General"},
    {"name": "Museum of the Great Patriotic War", "city": "Moscow", "country": "Russia", "lat": 55.7310, "lon": 37.5052, "founded": 1995, "focus": "Eastern Front WWII", "conflict": "WWII"},
    {"name": "National War Museum Malta", "city": "Valletta", "country": "Malta", "lat": 35.8959, "lon": 14.5128, "founded": 1975, "focus": "WWII Malta Siege", "conflict": "WWII"},
    {"name": "Sachsenhausen Memorial", "city": "Oranienburg", "country": "Germany", "lat": 52.7662, "lon": 13.2639, "founded": 1961, "focus": "Concentration Camp", "conflict": "WWII"},
    {"name": "Korean War Memorial Museum", "city": "Seoul", "country": "South Korea", "lat": 37.5344, "lon": 126.9792, "founded": 1994, "focus": "Korean War", "conflict": "Korean War"},
    {"name": "Checkpoint Charlie Museum", "city": "Berlin", "country": "Germany", "lat": 52.5076, "lon": 13.3904, "founded": 1963, "focus": "Cold War / Berlin Wall", "conflict": "Cold War"},
    {"name": "Caen Memorial", "city": "Caen", "country": "France", "lat": 49.1978, "lon": -0.3847, "founded": 1988, "focus": "D-Day / Peace", "conflict": "WWII"},
    {"name": "Nagasaki Atomic Bomb Museum", "city": "Nagasaki", "country": "Japan", "lat": 32.7740, "lon": 129.8640, "founded": 1996, "focus": "Atomic Bombing / Peace", "conflict": "WWII"},
    {"name": "Gettysburg National Military Park", "city": "Gettysburg", "country": "USA", "lat": 39.8123, "lon": -77.2309, "founded": 1895, "focus": "American Civil War", "conflict": "US Civil War"},
    {"name": "Te Papa Tongarewa (Gallipoli)", "city": "Wellington", "country": "New Zealand", "lat": -41.2904, "lon": 174.7820, "founded": 1998, "focus": "Gallipoli / ANZAC", "conflict": "WWI"},
]

# =====================================================================
# 6. ANCIENT CIVILIZATION MUSEUMS  (20+)
# =====================================================================
ANCIENT_CIV = [
    {"name": "Egyptian Museum Cairo", "city": "Cairo", "country": "Egypt", "lat": 30.0478, "lon": 31.2336, "founded": 1902, "civilization": "Ancient Egypt", "highlights": "Tutankhamun Treasures"},
    {"name": "Grand Egyptian Museum", "city": "Giza", "country": "Egypt", "lat": 29.9946, "lon": 31.1167, "founded": 2024, "civilization": "Ancient Egypt", "highlights": "Largest Archaeological Museum"},
    {"name": "Acropolis Museum", "city": "Athens", "country": "Greece", "lat": 37.9684, "lon": 23.7285, "founded": 2009, "civilization": "Ancient Greece", "highlights": "Parthenon Gallery"},
    {"name": "Iraq Museum", "city": "Baghdad", "country": "Iraq", "lat": 33.3413, "lon": 44.3665, "founded": 1926, "civilization": "Mesopotamia", "highlights": "Sumerian Artifacts"},
    {"name": "Museo Nacional de Antropologia", "city": "Mexico City", "country": "Mexico", "lat": 19.4260, "lon": -99.1862, "founded": 1964, "civilization": "Aztec / Maya", "highlights": "Sun Stone, Aztec Calendar"},
    {"name": "National Museum New Delhi", "city": "New Delhi", "country": "India", "lat": 28.6117, "lon": 77.2195, "founded": 1949, "civilization": "Indus Valley / Indian", "highlights": "Harappan Gallery"},
    {"name": "National Archaeological Museum Athens", "city": "Athens", "country": "Greece", "lat": 37.9891, "lon": 23.7314, "founded": 1829, "civilization": "Ancient Greece", "highlights": "Mask of Agamemnon"},
    {"name": "Pergamon Museum", "city": "Berlin", "country": "Germany", "lat": 52.5213, "lon": 13.3968, "founded": 1930, "civilization": "Babylonian / Greek", "highlights": "Ishtar Gate"},
    {"name": "National Museum of Iran", "city": "Tehran", "country": "Iran", "lat": 35.6867, "lon": 51.4156, "founded": 1937, "civilization": "Persian Empire", "highlights": "Achaemenid Artifacts"},
    {"name": "Bardo National Museum", "city": "Tunis", "country": "Tunisia", "lat": 36.8095, "lon": 10.1345, "founded": 1888, "civilization": "Roman / Carthaginian", "highlights": "Roman Mosaics"},
    {"name": "Heraklion Archaeological Museum", "city": "Heraklion", "country": "Greece", "lat": 35.3388, "lon": 25.1378, "founded": 1883, "civilization": "Minoan", "highlights": "Phaistos Disc"},
    {"name": "Museo Larco", "city": "Lima", "country": "Peru", "lat": -12.0719, "lon": -77.0712, "founded": 1926, "civilization": "Pre-Columbian Peru", "highlights": "Moche Pottery"},
    {"name": "Sanxingdui Museum", "city": "Guanghan", "country": "China", "lat": 31.0012, "lon": 104.1987, "founded": 1997, "civilization": "Ancient Shu", "highlights": "Bronze Masks"},
    {"name": "Museo Nazionale Romano", "city": "Rome", "country": "Italy", "lat": 41.9012, "lon": 12.4986, "founded": 1889, "civilization": "Roman Empire", "highlights": "Classical Sculpture"},
    {"name": "Antalya Archaeological Museum", "city": "Antalya", "country": "Turkey", "lat": 36.8854, "lon": 30.6799, "founded": 1922, "civilization": "Lycian / Roman", "highlights": "Sarcophagi Hall"},
    {"name": "National Museum of Afghanistan", "city": "Kabul", "country": "Afghanistan", "lat": 34.5281, "lon": 69.1723, "founded": 1919, "civilization": "Gandhara / Kushan", "highlights": "Bactrian Gold"},
    {"name": "Izmir Archaeological Museum", "city": "Izmir", "country": "Turkey", "lat": 38.4218, "lon": 27.1423, "founded": 1927, "civilization": "Ionian / Roman", "highlights": "Bronze Poseidon"},
    {"name": "National Museum of Cambodia", "city": "Phnom Penh", "country": "Cambodia", "lat": 11.5636, "lon": 104.9315, "founded": 1920, "civilization": "Khmer Empire", "highlights": "Angkorian Sculpture"},
    {"name": "Museo de Oro", "city": "Bogota", "country": "Colombia", "lat": 4.6018, "lon": -74.0716, "founded": 1939, "civilization": "Muisca / Pre-Columbian", "highlights": "Gold Raft of Eldorado"},
    {"name": "Jordan Archaeological Museum", "city": "Amman", "country": "Jordan", "lat": 31.9522, "lon": 35.9340, "founded": 1951, "civilization": "Nabataean / Roman", "highlights": "Dead Sea Scrolls Copper"},
    {"name": "Terracotta Army Museum", "city": "Xi'an", "country": "China", "lat": 34.3842, "lon": 109.2785, "founded": 1979, "civilization": "Qin Dynasty", "highlights": "8000 Terracotta Warriors"},
    {"name": "Museo Nacional de Arqueologia", "city": "Lima", "country": "Peru", "lat": -12.0677, "lon": -77.0652, "founded": 1826, "civilization": "Inca / Pre-Columbian", "highlights": "Inca Textiles, Nazca Pottery"},
    {"name": "National Museum of Ethiopia", "city": "Addis Ababa", "country": "Ethiopia", "lat": 9.0355, "lon": 38.7620, "founded": 1936, "civilization": "Aksumite / Early Human", "highlights": "Lucy (Australopithecus)"},
    {"name": "Neues Museum Berlin", "city": "Berlin", "country": "Germany", "lat": 52.5207, "lon": 13.3981, "founded": 1855, "civilization": "Egyptian / Prehistoric", "highlights": "Bust of Nefertiti"},
]

# =====================================================================
# 7. ART CAPITALS  (15+ cities with multiple venues)
# =====================================================================
ART_CAPITALS = [
    {"name": "Louvre / Orsay / Pompidou", "city": "Paris", "country": "France", "lat": 48.8606, "lon": 2.3376, "institutions": 136, "vibe": "Renaissance to Contemporary", "highlight": "Mona Lisa, Water Lilies"},
    {"name": "Met / MoMA / Guggenheim / Whitney", "city": "New York", "country": "USA", "lat": 40.7794, "lon": -73.9632, "institutions": 83, "vibe": "Global Art Capital", "highlight": "Museum Mile"},
    {"name": "National Gallery / Tate / V&A / Saatchi", "city": "London", "country": "UK", "lat": 51.5089, "lon": -0.1283, "institutions": 94, "vibe": "Classical to Contemporary", "highlight": "Free Entry Major Museums"},
    {"name": "Uffizi / Accademia / Pitti Palace", "city": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "institutions": 72, "vibe": "Renaissance Epicentre", "highlight": "Botticelli, Michelangelo"},
    {"name": "Mori / Teamlab / National Museum", "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "institutions": 68, "vibe": "Traditional + Digital Art", "highlight": "TeamLab Borderless"},
    {"name": "Pergamon / Hamburger Bahnhof / Neue", "city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "institutions": 57, "vibe": "Museum Island + Galleries", "highlight": "Museum Island UNESCO"},
    {"name": "Prado / Reina Sofia / Thyssen", "city": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038, "institutions": 45, "vibe": "Art Triangle", "highlight": "Guernica, Las Meninas"},
    {"name": "Rijksmuseum / Stedelijk / Van Gogh", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "institutions": 51, "vibe": "Dutch Masters + Modern", "highlight": "Night Watch, Sunflowers"},
    {"name": "Vatican Museums / Galleria Borghese / MAXXI", "city": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964, "institutions": 60, "vibe": "Antiquity to Contemporary", "highlight": "Sistine Chapel"},
    {"name": "Kunsthistorisches / Belvedere / Albertina", "city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "institutions": 38, "vibe": "Imperial Collections", "highlight": "Klimt's The Kiss"},
    {"name": "Art Institute / MCA / Smart Museum", "city": "Chicago", "country": "USA", "lat": 41.8781, "lon": -87.6298, "institutions": 32, "vibe": "Impressionism + Architecture", "highlight": "A Sunday on La Grande Jatte"},
    {"name": "Hermitage / Russian Museum / Erarta", "city": "Saint Petersburg", "country": "Russia", "lat": 59.9343, "lon": 30.3351, "institutions": 43, "vibe": "Imperial + Avant-Garde", "highlight": "Winter Palace"},
    {"name": "LACMA / Getty / Broad / MOCA", "city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "institutions": 37, "vibe": "Contemporary / Film Art", "highlight": "Getty Villa, Urban Light"},
    {"name": "National Gallery / AGO / ROM", "city": "Ottawa / Toronto", "country": "Canada", "lat": 45.3796, "lon": -75.7139, "institutions": 25, "vibe": "Canadian + Indigenous Art", "highlight": "Group of Seven"},
    {"name": "Zeitz MOCAA / Iziko / Norval", "city": "Cape Town", "country": "South Africa", "lat": -33.9249, "lon": 18.4241, "institutions": 18, "vibe": "African Contemporary", "highlight": "Zeitz MOCAA Silo"},
    {"name": "National Museum / Tretyakov / Pushkin", "city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "institutions": 40, "vibe": "Russian Masters", "highlight": "Tretyakov Icons"},
    {"name": "MASP / Pinacoteca / Inhotim", "city": "Sao Paulo", "country": "Brazil", "lat": -23.5614, "lon": -46.6560, "institutions": 22, "vibe": "Latin American Art Hub", "highlight": "MASP Suspended Gallery"},
    {"name": "Neue / Bode / Alte Nationalgalerie", "city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820, "institutions": 34, "vibe": "Pinakothek Quarter", "highlight": "Durer, Rubens"},
    {"name": "National Gallery / AGNSW", "city": "Sydney / Canberra", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "institutions": 20, "vibe": "Pacific + Indigenous Art", "highlight": "Sidney Nolan, Aboriginal Art"},
]

# =====================================================================
# 8. OPEN-AIR MUSEUMS  (15+)
# =====================================================================
OPEN_AIR = [
    {"name": "Skansen", "city": "Stockholm", "country": "Sweden", "lat": 59.3264, "lon": 18.1033, "founded": 1891, "theme": "Swedish Rural Life", "area_ha": 30},
    {"name": "Colonial Williamsburg", "city": "Williamsburg", "country": "USA", "lat": 37.2707, "lon": -76.7075, "founded": 1926, "theme": "18th-Century Colonial America", "area_ha": 121},
    {"name": "Beamish Museum", "city": "County Durham", "country": "UK", "lat": 54.8849, "lon": -1.6586, "founded": 1970, "theme": "North England 1820s-1950s", "area_ha": 121},
    {"name": "Bokrijk Open-Air Museum", "city": "Genk", "country": "Belgium", "lat": 50.9537, "lon": 5.4267, "founded": 1958, "theme": "Flemish Rural Heritage", "area_ha": 550},
    {"name": "Maihaugen", "city": "Lillehammer", "country": "Norway", "lat": 61.1145, "lon": 10.4729, "founded": 1887, "theme": "Norwegian Village Life", "area_ha": 40},
    {"name": "Ballenberg", "city": "Hofstetten", "country": "Switzerland", "lat": 46.7578, "lon": 8.0856, "founded": 1978, "theme": "Swiss Rural Architecture", "area_ha": 66},
    {"name": "Den Gamle By", "city": "Aarhus", "country": "Denmark", "lat": 56.1596, "lon": 10.1930, "founded": 1909, "theme": "Danish Town Life", "area_ha": 4},
    {"name": "Zuiderzeemuseum", "city": "Enkhuizen", "country": "Netherlands", "lat": 52.7073, "lon": 5.2967, "founded": 1948, "theme": "Dutch Fishing Village", "area_ha": 15},
    {"name": "Muzeul Satului", "city": "Bucharest", "country": "Romania", "lat": 44.4726, "lon": 26.0770, "founded": 1936, "theme": "Romanian Village Life", "area_ha": 14},
    {"name": "Estonian Open Air Museum", "city": "Tallinn", "country": "Estonia", "lat": 59.4313, "lon": 24.6370, "founded": 1957, "theme": "Estonian Rural Architecture", "area_ha": 79},
    {"name": "Meiji Mura", "city": "Inuyama", "country": "Japan", "lat": 35.4063, "lon": 136.9634, "founded": 1965, "theme": "Meiji Era Architecture", "area_ha": 100},
    {"name": "Sturbridge Village", "city": "Sturbridge", "country": "USA", "lat": 42.1126, "lon": -72.0932, "founded": 1946, "theme": "1830s New England", "area_ha": 80},
    {"name": "Plimoth Patuxet", "city": "Plymouth", "country": "USA", "lat": 41.9584, "lon": -70.6272, "founded": 1947, "theme": "1627 Pilgrim Settlement", "area_ha": 8},
    {"name": "Highland Folk Museum", "city": "Newtonmore", "country": "UK", "lat": 57.0634, "lon": -4.1229, "founded": 1935, "theme": "Scottish Highland Life", "area_ha": 32},
    {"name": "Hjerl Hede", "city": "Vinderup", "country": "Denmark", "lat": 56.4875, "lon": 8.7562, "founded": 1930, "theme": "Danish Rural 1500-1900", "area_ha": 50},
    {"name": "Black Country Living Museum", "city": "Dudley", "country": "UK", "lat": 52.5194, "lon": -2.0908, "founded": 1978, "theme": "Industrial Black Country", "area_ha": 10},
    {"name": "Sovereign Hill", "city": "Ballarat", "country": "Australia", "lat": -37.5677, "lon": 143.8789, "founded": 1970, "theme": "1850s Gold Rush", "area_ha": 25},
    {"name": "Ecomusee d'Alsace", "city": "Ungersheim", "country": "France", "lat": 47.8509, "lon": 7.2915, "founded": 1984, "theme": "Alsatian Village Heritage", "area_ha": 100},
    {"name": "Jamestown Settlement", "city": "Williamsburg", "country": "USA", "lat": 37.2240, "lon": -76.7800, "founded": 1957, "theme": "1607 English Settlement", "area_ha": 22},
    {"name": "Norsk Folkemuseum", "city": "Oslo", "country": "Norway", "lat": 59.9043, "lon": 10.6833, "founded": 1894, "theme": "Norwegian Heritage", "area_ha": 14},
]

# =====================================================================
# 9. QUIRKY & UNUSUAL MUSEUMS  (20+)
# =====================================================================
QUIRKY_MUSEUMS = [
    {"name": "Museum of Bad Art", "city": "Somerville", "country": "USA", "lat": 42.3976, "lon": -71.0995, "theme": "Terrible Artwork", "oddity": "Art Too Bad to Be Ignored"},
    {"name": "Disgusting Food Museum", "city": "Malmo", "country": "Sweden", "lat": 55.6050, "lon": 13.0038, "theme": "Revolting Cuisine", "oddity": "Casu Marzu, Surstroemming"},
    {"name": "Museum of Medieval Torture", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3730, "lon": 4.8920, "theme": "Torture Devices", "oddity": "Iron Maiden, Rack"},
    {"name": "International Spy Museum", "city": "Washington D.C.", "country": "USA", "lat": 38.8844, "lon": -77.0230, "theme": "Espionage", "oddity": "CIA / KGB Gadgets"},
    {"name": "Icelandic Phallological Museum", "city": "Reykjavik", "country": "Iceland", "lat": 64.1466, "lon": -21.9426, "theme": "Animal Phallology", "oddity": "283 Specimens"},
    {"name": "Cancun Underwater Museum", "city": "Cancun", "country": "Mexico", "lat": 21.2001, "lon": -86.7695, "theme": "Underwater Sculpture", "oddity": "500+ Sculptures Submerged"},
    {"name": "Museum of Broken Relationships", "city": "Zagreb", "country": "Croatia", "lat": 45.8150, "lon": 15.9749, "theme": "Failed Love", "oddity": "Objects from Breakups"},
    {"name": "Sulabh Toilet Museum", "city": "New Delhi", "country": "India", "lat": 28.5860, "lon": 77.1536, "theme": "Toilet History", "oddity": "4500 Years of Sanitation"},
    {"name": "Cup Noodles Museum", "city": "Yokohama", "country": "Japan", "lat": 35.4537, "lon": 139.6380, "theme": "Instant Noodle History", "oddity": "Make Your Own Cup Noodles"},
    {"name": "Vent Haven Museum", "city": "Fort Mitchell", "country": "USA", "lat": 39.0556, "lon": -84.5547, "theme": "Ventriloquism", "oddity": "900+ Ventriloquist Dummies"},
    {"name": "Museum of Death", "city": "Los Angeles", "country": "USA", "lat": 34.1014, "lon": -118.3267, "theme": "Death & Mortality", "oddity": "Serial Killer Art, Autopsy Tools"},
    {"name": "Currywurst Museum", "city": "Berlin", "country": "Germany", "lat": 52.5067, "lon": 13.3910, "theme": "Currywurst Sausage", "oddity": "Dedicated to Berlin's Snack"},
    {"name": "Leila's Hair Museum", "city": "Independence", "country": "USA", "lat": 39.0911, "lon": -94.4155, "theme": "Human Hair Art", "oddity": "Victorian Hair Wreaths"},
    {"name": "Avanos Hair Museum", "city": "Avanos", "country": "Turkey", "lat": 38.7177, "lon": 34.8505, "theme": "Human Hair Locks", "oddity": "16,000+ Hair Samples in Cave"},
    {"name": "Parasitological Museum", "city": "Tokyo", "country": "Japan", "lat": 35.6337, "lon": 139.7082, "theme": "Parasites", "oddity": "8.8m Tapeworm Specimen"},
    {"name": "Museum of Witchcraft & Magic", "city": "Boscastle", "country": "UK", "lat": 50.6847, "lon": -4.6919, "theme": "Witchcraft History", "oddity": "Hex Dolls, Spell Books"},
    {"name": "Momofuku Ando Instant Ramen Museum", "city": "Osaka", "country": "Japan", "lat": 34.7274, "lon": 135.4375, "theme": "Instant Ramen", "oddity": "Origin of Instant Noodles"},
    {"name": "Bread Museum", "city": "Ulm", "country": "Germany", "lat": 48.3974, "lon": 9.9934, "theme": "Bread History", "oddity": "6000 Years of Bread"},
    {"name": "Bunny Museum", "city": "Altadena", "country": "USA", "lat": 34.1900, "lon": -118.1312, "theme": "Rabbit Memorabilia", "oddity": "35,000+ Bunny Items"},
    {"name": "Mini Bottle Gallery", "city": "Oslo", "country": "Norway", "lat": 59.9139, "lon": 10.7522, "theme": "Miniature Bottles", "oddity": "53,000 Mini Bottles"},
    {"name": "Kazimierz Dolny Film Poster Museum", "city": "Kazimierz Dolny", "country": "Poland", "lat": 51.3217, "lon": 21.9564, "theme": "Polish Film Posters", "oddity": "Art Posters Not Film Stills"},
    {"name": "Torture Museum Bruges", "city": "Bruges", "country": "Belgium", "lat": 51.2093, "lon": 3.2247, "theme": "Medieval Torture", "oddity": "Dungeon Under Belfry"},
    {"name": "Mutter Museum", "city": "Philadelphia", "country": "USA", "lat": 39.9536, "lon": -75.1766, "theme": "Medical Oddities", "oddity": "Conjoined Liver, Soap Lady"},
    {"name": "Cat Museum Kuching", "city": "Kuching", "country": "Malaysia", "lat": 1.5535, "lon": 110.3593, "theme": "All Things Cat", "oddity": "4000 Cat Artefacts"},
    {"name": "Nonseum", "city": "Herrnbaumgarten", "country": "Austria", "lat": 48.7000, "lon": 16.6833, "theme": "Useless Inventions", "oddity": "One-Legged Boots, Square Balls"},
]

# =====================================================================
# 10. ART AUCTION HOUSES & MARKETS  (15+)
# =====================================================================
AUCTION_MARKETS = [
    {"name": "Christie's King Street", "city": "London", "country": "UK", "lat": 51.5078, "lon": -0.1383, "founded": 1766, "type": "Auction House", "focus": "Fine Art / Luxury"},
    {"name": "Christie's Rockefeller Center", "city": "New York", "country": "USA", "lat": 40.7587, "lon": -73.9787, "founded": 1977, "type": "Auction House", "focus": "American / Contemporary"},
    {"name": "Sotheby's New Bond Street", "city": "London", "country": "UK", "lat": 51.5141, "lon": -0.1429, "founded": 1744, "type": "Auction House", "focus": "Fine Art / Antiquities"},
    {"name": "Sotheby's York Avenue", "city": "New York", "country": "USA", "lat": 40.7625, "lon": -73.9602, "founded": 1955, "type": "Auction House", "focus": "Post-War / Contemporary"},
    {"name": "Art Basel", "city": "Basel", "country": "Switzerland", "lat": 47.5596, "lon": 7.5886, "founded": 1970, "type": "Art Fair", "focus": "Premier Global Art Fair"},
    {"name": "Art Basel Miami Beach", "city": "Miami Beach", "country": "USA", "lat": 25.8028, "lon": -80.1345, "founded": 2002, "type": "Art Fair", "focus": "Americas / Contemporary"},
    {"name": "Art Basel Hong Kong", "city": "Hong Kong", "country": "China", "lat": 22.3030, "lon": 114.1600, "founded": 2013, "type": "Art Fair", "focus": "Asian / Global Art"},
    {"name": "Frieze London", "city": "London", "country": "UK", "lat": 51.5410, "lon": -0.1530, "founded": 2003, "type": "Art Fair", "focus": "Contemporary / Emerging"},
    {"name": "Frieze New York", "city": "New York", "country": "USA", "lat": 40.7411, "lon": -74.0018, "founded": 2012, "type": "Art Fair", "focus": "Contemporary / Galleries"},
    {"name": "Venice Biennale", "city": "Venice", "country": "Italy", "lat": 45.4298, "lon": 12.3581, "founded": 1895, "type": "Biennale", "focus": "International Art Exhibition"},
    {"name": "Documenta", "city": "Kassel", "country": "Germany", "lat": 51.3127, "lon": 9.4797, "founded": 1955, "type": "Quinquennial Exhibition", "focus": "Contemporary / Conceptual"},
    {"name": "Phillips Auction", "city": "London", "country": "UK", "lat": 51.5050, "lon": -0.1480, "founded": 1796, "type": "Auction House", "focus": "20th-Century / Design"},
    {"name": "Bonhams Auction", "city": "London", "country": "UK", "lat": 51.5115, "lon": -0.1510, "founded": 1793, "type": "Auction House", "focus": "Asian Art / Motoring"},
    {"name": "TEFAF Maastricht", "city": "Maastricht", "country": "Netherlands", "lat": 50.8514, "lon": 5.6910, "founded": 1988, "type": "Art & Antiques Fair", "focus": "Old Masters / Antiquities"},
    {"name": "Sao Paulo Biennale", "city": "Sao Paulo", "country": "Brazil", "lat": -23.5872, "lon": -46.6555, "founded": 1951, "type": "Biennale", "focus": "Latin American / Global"},
    {"name": "Sharjah Biennial", "city": "Sharjah", "country": "UAE", "lat": 25.3463, "lon": 55.4209, "founded": 1993, "type": "Biennale", "focus": "Middle Eastern / Global"},
    {"name": "Istanbul Biennial", "city": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "founded": 1987, "type": "Biennale", "focus": "East-West Bridge"},
    {"name": "Gwangju Biennale", "city": "Gwangju", "country": "South Korea", "lat": 35.1595, "lon": 126.8526, "founded": 1995, "type": "Biennale", "focus": "Asian Contemporary"},
    {"name": "Artcurial Paris", "city": "Paris", "country": "France", "lat": 48.8699, "lon": 2.3063, "founded": 2002, "type": "Auction House", "focus": "French Art / Design"},
    {"name": "Heritage Auctions", "city": "Dallas", "country": "USA", "lat": 32.7767, "lon": -96.7970, "founded": 1976, "type": "Auction House", "focus": "Comics / Collectibles / Coins"},
]


# =====================================================================
# CACHED DATA BUILDERS
# =====================================================================

@st.cache_data(ttl=3600)
def _build_greatest_df():
    return pd.DataFrame(GREATEST_MUSEUMS)


@st.cache_data(ttl=3600)
def _build_modern_art_df():
    return pd.DataFrame(MODERN_ART)


@st.cache_data(ttl=3600)
def _build_science_df():
    return pd.DataFrame(SCIENCE_MUSEUMS)


@st.cache_data(ttl=3600)
def _build_natural_history_df():
    return pd.DataFrame(NATURAL_HISTORY)


@st.cache_data(ttl=3600)
def _build_war_df():
    return pd.DataFrame(WAR_MUSEUMS)


@st.cache_data(ttl=3600)
def _build_ancient_df():
    return pd.DataFrame(ANCIENT_CIV)


@st.cache_data(ttl=3600)
def _build_art_capitals_df():
    return pd.DataFrame(ART_CAPITALS)


@st.cache_data(ttl=3600)
def _build_open_air_df():
    return pd.DataFrame(OPEN_AIR)


@st.cache_data(ttl=3600)
def _build_quirky_df():
    return pd.DataFrame(QUIRKY_MUSEUMS)


@st.cache_data(ttl=3600)
def _build_auction_df():
    return pd.DataFrame(AUCTION_MARKETS)


# =====================================================================
# MAP BUILDERS — one per mode
# =====================================================================

def _map_greatest(df, color):
    m = _base_map()
    for _, r in df.iterrows():
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Type", r["type"]),
            ("Visitors (M)", r["visitors_m"]),
        ], color)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, r["visitors_m"] * 1.5),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_modern_art(df, color):
    m = _base_map()
    for _, r in df.iterrows():
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Focus", r["focus"]),
            ("Visitors (M)", r["visitors_m"]),
        ], color)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, r["visitors_m"] * 2),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_science(df, color):
    m = _base_map()
    for _, r in df.iterrows():
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Focus", r["focus"]),
            ("Visitors (M)", r["visitors_m"]),
        ], color)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, r["visitors_m"] * 2),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_natural_history(df, color):
    m = _base_map()
    for _, r in df.iterrows():
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Highlights", r["highlights"]),
            ("Visitors (M)", r["visitors_m"]),
        ], color)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, r["visitors_m"] * 1.8),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_war(df, color):
    m = _base_map()
    conflict_colors = {
        "WWII": "#ef4444",
        "Vietnam War": "#f59e0b",
        "Cold War": "#3b82f6",
        "Korean War": "#06b6d4",
        "Cambodian Genocide": "#ec4899",
        "War on Terror": "#f97316",
        "Apartheid": "#a855f7",
        "General": "#8b97b0",
    }
    for _, r in df.iterrows():
        c = conflict_colors.get(r["conflict"], color)
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Focus", r["focus"]),
            ("Conflict", r["conflict"]),
        ], c)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=7,
            color=c, fill=True, fill_color=c, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_ancient(df, color):
    m = _base_map(center=[25, 40], zoom=3)
    civ_colors = {
        "Ancient Egypt": "#f59e0b",
        "Ancient Greece": "#3b82f6",
        "Mesopotamia": "#f97316",
        "Aztec / Maya": "#10b981",
        "Indus Valley / Indian": "#ec4899",
        "Babylonian / Greek": "#8b5cf6",
        "Persian Empire": "#14b8a6",
        "Roman / Carthaginian": "#ef4444",
        "Minoan": "#38bdf8",
        "Pre-Columbian Peru": "#a855f7",
        "Ancient Shu": "#facc15",
        "Roman Empire": "#ef4444",
        "Lycian / Roman": "#06b6d4",
        "Gandhara / Kushan": "#84cc16",
        "Ionian / Roman": "#06b6d4",
        "Khmer Empire": "#10b981",
        "Muisca / Pre-Columbian": "#f59e0b",
        "Nabataean / Roman": "#f97316",
        "Qin Dynasty": "#e11d48",
    }
    for _, r in df.iterrows():
        c = civ_colors.get(r["civilization"], color)
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Civilization", r["civilization"]),
            ("Highlights", r["highlights"]),
        ], c)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=c, fill=True, fill_color=c, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_art_capitals(df, color):
    m = _base_map()
    for _, r in df.iterrows():
        popup = _popup_html(r["city"], [
            ("Country", r["country"]),
            ("Institutions", r["institutions"]),
            ("Vibe", r["vibe"]),
            ("Highlight", r["highlight"]),
        ], color)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(6, r["institutions"] / 6),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["city"])),
        ).add_to(m)
    return m


def _map_open_air(df, color):
    m = _base_map(center=[52, 10], zoom=3)
    for _, r in df.iterrows():
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Theme", r["theme"]),
            ("Area (ha)", r["area_ha"]),
        ], color)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, min(r["area_ha"] / 10, 18)),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_quirky(df, color):
    m = _base_map()
    for _, r in df.iterrows():
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Theme", r["theme"]),
            ("Oddity", r["oddity"]),
        ], color)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=7,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


def _map_auction(df, color):
    m = _base_map(center=[45, 0], zoom=3)
    type_colors = {
        "Auction House": "#f59e0b",
        "Art Fair": "#ec4899",
        "Biennale": "#8b5cf6",
        "Quinquennial Exhibition": "#06b6d4",
        "Art & Antiques Fair": "#10b981",
    }
    for _, r in df.iterrows():
        c = type_colors.get(r["type"], color)
        popup = _popup_html(r["name"], [
            ("City", r["city"]),
            ("Country", r["country"]),
            ("Founded", r["founded"]),
            ("Type", r["type"]),
            ("Focus", r["focus"]),
        ], c)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=c, fill=True, fill_color=c, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=html_module.escape(str(r["name"])),
        ).add_to(m)
    return m


# =====================================================================
# STATS ROW HELPERS
# =====================================================================

def _stats_greatest(df):
    cols = st.columns(4)
    cols[0].metric("Total Museums", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Oldest", int(df["founded"].min()))
    cols[3].metric("Top Visitors (M)", f"{df['visitors_m'].max():.1f}")


def _stats_modern_art(df):
    cols = st.columns(4)
    cols[0].metric("Total Galleries", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Oldest", int(df["founded"].min()))
    cols[3].metric("Newest", int(df["founded"].max()))


def _stats_science(df):
    cols = st.columns(4)
    cols[0].metric("Total Museums", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Oldest", int(df["founded"].min()))
    cols[3].metric("Top Visitors (M)", f"{df['visitors_m'].max():.1f}")


def _stats_natural_history(df):
    cols = st.columns(4)
    cols[0].metric("Total Museums", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Oldest", int(df["founded"].min()))
    cols[3].metric("Top Visitors (M)", f"{df['visitors_m'].max():.1f}")


def _stats_war(df):
    cols = st.columns(4)
    cols[0].metric("Total Sites", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Conflicts Covered", df["conflict"].nunique())
    cols[3].metric("Oldest", int(df["founded"].min()))


def _stats_ancient(df):
    cols = st.columns(4)
    cols[0].metric("Total Museums", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Civilizations", df["civilization"].nunique())
    cols[3].metric("Oldest", int(df["founded"].min()))


def _stats_art_capitals(df):
    cols = st.columns(4)
    cols[0].metric("Art Cities", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    total_inst = int(df["institutions"].sum())
    cols[2].metric("Total Institutions", total_inst)
    cols[3].metric("Top City Inst.", int(df["institutions"].max()))


def _stats_open_air(df):
    cols = st.columns(4)
    cols[0].metric("Total Museums", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Total Area (ha)", int(df["area_ha"].sum()))
    cols[3].metric("Oldest", int(df["founded"].min()))


def _stats_quirky(df):
    cols = st.columns(4)
    cols[0].metric("Total Museums", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Unique Themes", df["theme"].nunique())
    cols[3].metric("Cities", df["city"].nunique())


def _stats_auction(df):
    cols = st.columns(4)
    cols[0].metric("Total Venues", len(df))
    cols[1].metric("Countries", df["country"].nunique())
    cols[2].metric("Types", df["type"].nunique())
    cols[3].metric("Oldest", int(df["founded"].min()))


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_museum_maps_tab():
    """Render the Museums & Galleries Maps tab for TerraScout AI."""

    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001f3db\ufe0f Museums & Galleries Maps</h4>'
        '<p>World museums, art galleries, and cultural institutions</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Map Mode",
        MODE_LIST,
        key="museum_maps_mode",
    )

    color = MODE_COLORS.get(mode, ACCENT_CYAN)

    st.divider()

    # --- dispatch per mode ---
    if mode == "World's Greatest Museums":
        df = _build_greatest_df()
        st.subheader("World's Greatest Museums")
        st.caption(
            "The most visited and celebrated museums on earth, spanning art, "
            "history, and culture. Circle size reflects annual visitor numbers."
        )

        # -- filter by country --
        countries = sorted(df["country"].unique().tolist())
        sel_countries = st.multiselect(
            "Filter by Country", countries, default=[], key="gm_country"
        )
        filtered = df[df["country"].isin(sel_countries)] if sel_countries else df

        _stats_greatest(filtered)
        m = _map_greatest(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "This dataset includes **encyclopaedic** and **universal** museums "
                "that house collections spanning millennia and continents. "
                "From the ancient Egyptian galleries of the Louvre to the vast "
                "scroll halls of Taipei's National Palace Museum, these are the "
                "institutions that define our understanding of world heritage.\n\n"
                "**Visitor figures** are approximate annual averages based on the "
                "most recent publicly available data (pre-2024)."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]).sort_values("visitors_m", ascending=False),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "greatest_museums.csv", "text/csv", key="dl_greatest"
        )

    # -----------------------------------------------------------------
    elif mode == "Modern & Contemporary Art":
        df = _build_modern_art_df()
        st.subheader("Modern & Contemporary Art Museums")
        st.caption(
            "Leading institutions for modern and contemporary art worldwide, "
            "from MoMA to the newest African contemporary spaces."
        )

        countries = sorted(df["country"].unique().tolist())
        sel_countries = st.multiselect(
            "Filter by Country", countries, default=[], key="ma_country"
        )
        filtered = df[df["country"].isin(sel_countries)] if sel_countries else df

        _stats_modern_art(filtered)
        m = _map_modern_art(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "Modern art museums emerged in the early 20th century as "
                "galleries dedicated to the art of the present. The movement "
                "was pioneered by MoMA (1929) and has since exploded globally.\n\n"
                "**Key movements covered:** Impressionism (late), Cubism, "
                "Surrealism, Abstract Expressionism, Pop Art, Minimalism, "
                "Conceptual Art, Street Art, Digital Art, NFT exhibitions."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]).sort_values("visitors_m", ascending=False),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "modern_art_museums.csv", "text/csv", key="dl_modern"
        )

    # -----------------------------------------------------------------
    elif mode == "Science & Technology Museums":
        df = _build_science_df()
        st.subheader("Science & Technology Museums")
        st.caption(
            "Interactive science centres, space museums, and technology "
            "showcases that inspire the next generation of innovators."
        )

        countries = sorted(df["country"].unique().tolist())
        sel_countries = st.multiselect(
            "Filter by Country", countries, default=[], key="sci_country"
        )
        filtered = df[df["country"].isin(sel_countries)] if sel_countries else df

        _stats_science(filtered)
        m = _map_science(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "Science museums range from vast Smithsonian complexes to "
                "intimate maker-spaces. Many feature hands-on exhibits, "
                "planetariums, and IMAX theatres.\n\n"
                "**Notable highlights:** Space Shuttle Endeavour at California "
                "Science Center, the Wright Flyer at Smithsonian Air & Space, "
                "CERN's particle accelerator tours, and Deutsches Museum's "
                "mining tunnel replica."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]).sort_values("visitors_m", ascending=False),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "science_museums.csv", "text/csv", key="dl_science"
        )

    # -----------------------------------------------------------------
    elif mode == "Natural History Museums":
        df = _build_natural_history_df()
        st.subheader("Natural History Museums")
        st.caption(
            "Dinosaurs, gems, wildlife and the story of life on Earth "
            "-- from fossils to living ecosystems."
        )

        countries = sorted(df["country"].unique().tolist())
        sel_countries = st.multiselect(
            "Filter by Country", countries, default=[], key="nh_country"
        )
        filtered = df[df["country"].isin(sel_countries)] if sel_countries else df

        _stats_natural_history(filtered)
        m = _map_natural_history(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "Natural history museums are among the oldest scientific "
                "institutions, often originating from royal cabinets of "
                "curiosities. They house millions of specimens -- from "
                "dinosaur skeletons to insect pinnings and mineral crystals.\n\n"
                "**Famous specimens:** Sue the T. Rex (Field Museum), "
                "Dippy the Diplodocus (NHM London), Hope Diamond "
                "(Smithsonian), Venus of Willendorf (Vienna)."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]).sort_values("visitors_m", ascending=False),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "natural_history_museums.csv", "text/csv", key="musm_dl_natural"
        )

    # -----------------------------------------------------------------
    elif mode == "War & Military Museums":
        df = _build_war_df()
        st.subheader("War & Military Museums")
        st.caption(
            "Memorials, battlefields, and museums documenting armed "
            "conflict, remembrance, and the pursuit of peace."
        )

        # -- filter by conflict --
        conflicts = sorted(df["conflict"].unique().tolist())
        sel_conflict = st.multiselect(
            "Filter by Conflict", conflicts, default=[], key="war_conflict"
        )
        filtered = df[df["conflict"].isin(sel_conflict)] if sel_conflict else df

        _stats_war(filtered)
        m = _map_war(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("Colour legend", expanded=False):
            st.markdown(
                "- **Red** -- World War II\n"
                "- **Amber** -- Vietnam War\n"
                "- **Blue** -- Cold War\n"
                "- **Cyan** -- Korean War\n"
                "- **Pink** -- Cambodian Genocide\n"
                "- **Orange** -- War on Terror\n"
                "- **Violet** -- Apartheid\n"
                "- **Grey** -- General / Multiple Conflicts"
            )

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "War museums serve a dual purpose: preserving artefacts for "
                "historical study and honouring those who suffered. Many of "
                "these sites are places of deep emotional resonance.\n\n"
                "**Note:** Visitor counts are omitted for this category out of "
                "respect -- many of these sites are memorials rather than "
                "tourist attractions."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "war_museums.csv", "text/csv", key="dl_war"
        )

    # -----------------------------------------------------------------
    elif mode == "Ancient Civilization Museums":
        df = _build_ancient_df()
        st.subheader("Ancient Civilization Museums")
        st.caption(
            "Museums preserving the treasures of ancient empires and "
            "lost civilizations, from Pharaohs to Terracotta Warriors."
        )

        # -- filter by civilization --
        civs = sorted(df["civilization"].unique().tolist())
        sel_civ = st.multiselect(
            "Filter by Civilization", civs, default=[], key="anc_civ"
        )
        filtered = df[df["civilization"].isin(sel_civ)] if sel_civ else df

        _stats_ancient(filtered)
        m = _map_ancient(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("Colour legend", expanded=False):
            st.markdown(
                "- **Amber** -- Ancient Egypt\n"
                "- **Blue** -- Ancient Greece\n"
                "- **Orange** -- Mesopotamia / Persia\n"
                "- **Emerald** -- Aztec / Maya / Khmer\n"
                "- **Pink** -- Indus Valley / Indian\n"
                "- **Violet** -- Babylonian\n"
                "- **Red** -- Roman Empire\n"
                "- **Yellow** -- Ancient Shu\n"
                "- **Rose** -- Qin Dynasty"
            )

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "These museums are the custodians of humanity's earliest "
                "cultural achievements. Many house artefacts spanning 5,000+ "
                "years, from cuneiform tablets to golden death masks.\n\n"
                "**Controversial repatriation:** Several collections include "
                "items subject to ongoing repatriation debates (e.g. the "
                "Parthenon Marbles, Benin Bronzes, Rosetta Stone)."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "ancient_civilization_museums.csv", "text/csv",
            key="musm_dl_ancient",
        )

    # -----------------------------------------------------------------
    elif mode == "Art Capitals":
        df = _build_art_capitals_df()
        st.subheader("Art Capitals of the World")
        st.caption(
            "Cities with the richest concentration of art institutions "
            "and galleries. Circle size reflects number of institutions."
        )

        _stats_art_capitals(df)
        m = _map_art_capitals(df, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "An 'art capital' is a city where the density of museums, "
                "galleries, artist studios, and art schools creates a self-"
                "sustaining creative ecosystem.\n\n"
                "**Paris** leads historically with 136+ institutions. "
                "**New York** dominates the contemporary market. "
                "**Berlin** attracts emerging artists with affordable studio "
                "space. **Cape Town** is the rising star of African art."
            )

        st.dataframe(
            df.drop(columns=["lat", "lon"]).sort_values("institutions", ascending=False),
            use_container_width=True,
        )
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "art_capitals.csv", "text/csv", key="dl_art_cap"
        )

    # -----------------------------------------------------------------
    elif mode == "Open-Air Museums":
        df = _build_open_air_df()
        st.subheader("Open-Air Museums")
        st.caption(
            "Living history villages and outdoor heritage parks around "
            "the world. Circle size reflects museum area."
        )

        countries = sorted(df["country"].unique().tolist())
        sel_countries = st.multiselect(
            "Filter by Country", countries, default=[], key="oa_country"
        )
        filtered = df[df["country"].isin(sel_countries)] if sel_countries else df

        _stats_open_air(filtered)
        m = _map_open_air(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "Open-air museums (also called living museums) reconstruct "
                "historical buildings and environments in an outdoor setting. "
                "The concept was pioneered by **Skansen** in Stockholm (1891), "
                "the world's first open-air museum.\n\n"
                "**Largest by area:** Bokrijk (Belgium, 550 ha), Colonial "
                "Williamsburg (USA, 121 ha), Beamish (UK, 121 ha).\n\n"
                "Many employ costumed interpreters who demonstrate traditional "
                "crafts, cooking, and daily life from their era."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]).sort_values("area_ha", ascending=False),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "open_air_museums.csv", "text/csv", key="dl_openair"
        )

    # -----------------------------------------------------------------
    elif mode == "Quirky & Unusual Museums":
        df = _build_quirky_df()
        st.subheader("Quirky & Unusual Museums")
        st.caption(
            "The strangest, weirdest, and most wonderful museums you "
            "never knew existed -- from bad art to parasites."
        )

        countries = sorted(df["country"].unique().tolist())
        sel_countries = st.multiselect(
            "Filter by Country", countries, default=[], key="qk_country"
        )
        filtered = df[df["country"].isin(sel_countries)] if sel_countries else df

        _stats_quirky(filtered)
        m = _map_quirky(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "Quirky museums prove that human curiosity knows no bounds. "
                "These institutions celebrate the niche, the absurd, and the "
                "unexpectedly fascinating.\n\n"
                "**Highlights:**\n"
                "- The Museum of Bad Art (MOBA) in Somerville curates works "
                "'too bad to be ignored.'\n"
                "- Malmo's Disgusting Food Museum lets you smell (and taste) "
                "the world's most revolting cuisine.\n"
                "- Tokyo's Meguro Parasitological Museum features an 8.8-metre "
                "tapeworm extracted from a human host.\n"
                "- The Nonseum in Austria showcases inventions nobody needs, "
                "like one-legged ski boots."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "quirky_museums.csv", "text/csv", key="dl_quirky"
        )

    # -----------------------------------------------------------------
    elif mode == "Art Auction Houses & Markets":
        df = _build_auction_df()
        st.subheader("Art Auction Houses & Markets")
        st.caption(
            "Where art changes hands: auction houses, art fairs, "
            "biennales, and the commercial art world."
        )

        # -- filter by type --
        types = sorted(df["type"].unique().tolist())
        sel_type = st.multiselect(
            "Filter by Type", types, default=[], key="auc_type"
        )
        filtered = df[df["type"].isin(sel_type)] if sel_type else df

        _stats_auction(filtered)
        m = _map_auction(filtered, color)
        st_html(m._repr_html_(), height=500)

        with st.expander("Colour legend", expanded=False):
            st.markdown(
                "- **Amber** -- Auction Houses\n"
                "- **Pink** -- Art Fairs\n"
                "- **Violet** -- Biennales\n"
                "- **Cyan** -- Quinquennial Exhibitions\n"
                "- **Emerald** -- Art & Antiques Fairs"
            )

        with st.expander("About this mode", expanded=False):
            st.markdown(
                "The art market is a multi-billion dollar industry. "
                "Christie's and Sotheby's together account for roughly "
                "40% of the global auction market.\n\n"
                "**Art Basel** (founded 1970) is the world's premier art "
                "fair, with satellite editions in Miami Beach and Hong Kong. "
                "The **Venice Biennale** (founded 1895) is the oldest "
                "international art exhibition.\n\n"
                "**Record sale:** Leonardo da Vinci's *Salvator Mundi* sold "
                "at Christie's New York for $450.3 million in 2017."
            )

        st.dataframe(
            filtered.drop(columns=["lat", "lon"]).sort_values("founded"),
            use_container_width=True,
        )
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, "auction_houses_markets.csv", "text/csv",
            key="dl_auction",
        )
