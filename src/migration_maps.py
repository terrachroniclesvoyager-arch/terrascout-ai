# -*- coding: utf-8 -*-
"""
Migration & Diaspora Maps module for TerraScout AI.
Visualises historical and modern human migration patterns, diaspora distributions,
trade routes, refugee flows, and climate displacement projections on interactive maps.
All data is hardcoded or sourced from free APIs (REST Countries).
"""

import io
import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import requests
import json
import html
import matplotlib.pyplot as plt
import streamlit.components.v1 as components


# =====================================================================
# COLOUR PALETTE  (matches TerraScout dark theme)
# =====================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_BORDER = "#2a3550"
_ACCENT = "#06b6d4"

MODE_COLORS = {
    "human_migration": "#f59e0b",
    "refugee":         "#ef4444",
    "diaspora":        "#8b5cf6",
    "colonial":        "#f97316",
    "silk_road":       "#eab308",
    "exploration":     "#3b82f6",
    "slave_trade":     "#dc2626",
    "gold_rush":       "#f59e0b",
    "immigration":     "#10b981",
    "climate":         "#06b6d4",
}


# =====================================================================
# MATPLOTLIB DARK HELPER
# =====================================================================
def _dark_fig(figsize=(10, 4)):
    """Create a dark-themed matplotlib figure."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    ax.tick_params(colors=_TEXT2)
    ax.xaxis.label.set_color(_TEXT)
    ax.yaxis.label.set_color(_TEXT)
    ax.title.set_color(_TEXT)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    return fig, ax


# =====================================================================
# DATA: 1. HUMAN MIGRATION ROUTES (Out of Africa)
# =====================================================================
HUMAN_MIGRATION_ROUTES = [
    {
        "name": "Out of Africa (East)",
        "color": "#ef4444",
        "period": "~70,000 BP",
        "desc": "Early Homo sapiens migrated from East Africa through the Horn of Africa to the Arabian Peninsula.",
        "coords": [
            [9.0, 38.7], [12.5, 43.1], [15.3, 44.2], [15.5, 48.5],
            [24.0, 54.0], [26.0, 56.3],
        ],
    },
    {
        "name": "Southern Coastal Route to Asia",
        "color": "#f97316",
        "period": "~65,000 BP",
        "desc": "Rapid coastal migration along the Indian Ocean rim to SE Asia and Australia.",
        "coords": [
            [26.0, 56.3], [24.5, 62.0], [21.0, 70.0], [16.0, 78.0],
            [10.0, 80.0], [7.0, 81.0], [6.0, 95.0], [3.0, 101.0],
            [-2.0, 110.0], [-6.0, 120.0], [-12.0, 131.0], [-20.0, 135.0],
        ],
    },
    {
        "name": "Into Europe",
        "color": "#3b82f6",
        "period": "~45,000 BP",
        "desc": "Migration from the Levant into Europe via the Balkans and Mediterranean coasts.",
        "coords": [
            [33.0, 35.5], [37.0, 36.0], [39.0, 34.0], [41.0, 29.0],
            [42.0, 24.0], [43.5, 20.0], [45.0, 14.0], [46.5, 7.0],
            [48.5, 2.3], [43.3, -3.7],
        ],
    },
    {
        "name": "Into Central & East Asia",
        "color": "#eab308",
        "period": "~50,000 BP",
        "desc": "Northward migration through Iran into Central Asia and eventually to China and Siberia.",
        "coords": [
            [26.0, 56.3], [32.0, 58.0], [36.0, 62.0], [39.0, 67.0],
            [42.0, 72.0], [44.0, 78.0], [43.0, 87.0], [40.0, 95.0],
            [38.0, 105.0], [35.0, 115.0],
        ],
    },
    {
        "name": "Into Siberia",
        "color": "#a855f7",
        "period": "~40,000 BP",
        "desc": "Humans adapted to cold climates and expanded into northern Siberia.",
        "coords": [
            [42.0, 72.0], [48.0, 75.0], [52.0, 80.0], [56.0, 85.0],
            [60.0, 100.0], [63.0, 130.0], [65.0, 150.0],
        ],
    },
    {
        "name": "Bering Land Bridge to Americas",
        "color": "#10b981",
        "period": "~16,000 BP",
        "desc": "From Siberia across Beringia into North America during the last Ice Age.",
        "coords": [
            [65.0, 150.0], [66.0, 170.0], [65.5, -170.0], [64.0, -155.0],
            [61.0, -150.0], [58.0, -135.0], [52.0, -125.0], [45.0, -120.0],
            [37.0, -118.0], [30.0, -100.0], [20.0, -99.0],
        ],
    },
    {
        "name": "Into South America",
        "color": "#14b8a6",
        "period": "~14,000 BP",
        "desc": "Rapid southward expansion through Central and South America.",
        "coords": [
            [20.0, -99.0], [14.0, -87.0], [9.0, -79.5], [5.0, -74.0],
            [-3.0, -60.0], [-15.0, -47.0], [-23.0, -43.0],
            [-34.0, -58.0], [-42.0, -65.0], [-50.0, -70.0],
        ],
    },
    {
        "name": "Polynesian Expansion",
        "color": "#ec4899",
        "period": "~3,000 BP",
        "desc": "Austronesian seafarers colonised the Pacific islands from Taiwan/SE Asia.",
        "coords": [
            [3.0, 101.0], [1.0, 110.0], [-2.0, 120.0], [-5.0, 135.0],
            [-6.0, 147.0], [-8.0, 157.0], [-13.4, 176.1], [-17.8, -177.9],
            [-21.2, -159.8], [-17.5, -149.5], [-8.0, -140.0],
            [-27.1, -109.3],
        ],
    },
]


# =====================================================================
# DATA: 2. MODERN REFUGEE FLOWS
# =====================================================================
REFUGEE_FLOWS = [
    {"origin": "Syria", "origin_ll": [34.8, 38.9], "dest": "Turkey", "dest_ll": [39.9, 32.8],
     "people": 3600000, "year": 2023, "color": "#ef4444"},
    {"origin": "Syria", "origin_ll": [34.8, 38.9], "dest": "Lebanon", "dest_ll": [33.9, 35.5],
     "people": 830000, "year": 2023, "color": "#ef4444"},
    {"origin": "Syria", "origin_ll": [34.8, 38.9], "dest": "Jordan", "dest_ll": [31.9, 35.9],
     "people": 670000, "year": 2023, "color": "#ef4444"},
    {"origin": "Syria", "origin_ll": [34.8, 38.9], "dest": "Germany", "dest_ll": [51.2, 10.4],
     "people": 850000, "year": 2023, "color": "#ef4444"},
    {"origin": "Ukraine", "origin_ll": [48.4, 31.2], "dest": "Poland", "dest_ll": [51.9, 19.1],
     "people": 1580000, "year": 2023, "color": "#3b82f6"},
    {"origin": "Ukraine", "origin_ll": [48.4, 31.2], "dest": "Germany", "dest_ll": [51.2, 10.4],
     "people": 1130000, "year": 2023, "color": "#3b82f6"},
    {"origin": "Ukraine", "origin_ll": [48.4, 31.2], "dest": "Czech Republic", "dest_ll": [49.8, 15.5],
     "people": 370000, "year": 2023, "color": "#3b82f6"},
    {"origin": "Venezuela", "origin_ll": [6.4, -66.6], "dest": "Colombia", "dest_ll": [4.6, -74.1],
     "people": 2900000, "year": 2023, "color": "#f59e0b"},
    {"origin": "Venezuela", "origin_ll": [6.4, -66.6], "dest": "Peru", "dest_ll": [-12.0, -77.0],
     "people": 1500000, "year": 2023, "color": "#f59e0b"},
    {"origin": "Venezuela", "origin_ll": [6.4, -66.6], "dest": "USA", "dest_ll": [38.9, -77.0],
     "people": 545000, "year": 2023, "color": "#f59e0b"},
    {"origin": "Myanmar", "origin_ll": [19.8, 96.2], "dest": "Bangladesh", "dest_ll": [23.7, 90.4],
     "people": 960000, "year": 2023, "color": "#a855f7"},
    {"origin": "Myanmar", "origin_ll": [19.8, 96.2], "dest": "Thailand", "dest_ll": [15.9, 100.9],
     "people": 92000, "year": 2023, "color": "#a855f7"},
    {"origin": "Afghanistan", "origin_ll": [33.9, 67.7], "dest": "Pakistan", "dest_ll": [30.4, 69.3],
     "people": 1740000, "year": 2023, "color": "#10b981"},
    {"origin": "Afghanistan", "origin_ll": [33.9, 67.7], "dest": "Iran", "dest_ll": [32.4, 53.7],
     "people": 780000, "year": 2023, "color": "#10b981"},
    {"origin": "South Sudan", "origin_ll": [6.9, 31.3], "dest": "Uganda", "dest_ll": [1.4, 32.3],
     "people": 940000, "year": 2023, "color": "#f97316"},
    {"origin": "South Sudan", "origin_ll": [6.9, 31.3], "dest": "Sudan", "dest_ll": [12.9, 30.2],
     "people": 810000, "year": 2023, "color": "#f97316"},
    {"origin": "Somalia", "origin_ll": [5.2, 46.2], "dest": "Kenya", "dest_ll": [-1.3, 36.8],
     "people": 310000, "year": 2023, "color": "#ec4899"},
    {"origin": "Somalia", "origin_ll": [5.2, 46.2], "dest": "Ethiopia", "dest_ll": [9.0, 38.7],
     "people": 250000, "year": 2023, "color": "#ec4899"},
    {"origin": "DRC", "origin_ll": [-4.3, 15.3], "dest": "Uganda", "dest_ll": [1.4, 32.3],
     "people": 500000, "year": 2023, "color": "#14b8a6"},
    {"origin": "Eritrea", "origin_ll": [15.2, 39.8], "dest": "Ethiopia", "dest_ll": [9.0, 38.7],
     "people": 175000, "year": 2023, "color": "#8b5cf6"},
]


# =====================================================================
# DATA: 3. GREAT DIASPORAS
# =====================================================================
GREAT_DIASPORAS = [
    {
        "name": "Jewish Diaspora",
        "color": "#3b82f6",
        "period": "586 BC - Present",
        "origin": "Ancient Israel / Judea",
        "desc": "Forced exile and voluntary migration across Roman, Islamic, and European lands.",
        "communities": [
            {"city": "New York", "lat": 40.7, "lon": -74.0, "pop": 1600000},
            {"city": "Jerusalem", "lat": 31.8, "lon": 35.2, "pop": 900000},
            {"city": "Los Angeles", "lat": 34.1, "lon": -118.2, "pop": 600000},
            {"city": "Haifa", "lat": 32.8, "lon": 35.0, "pop": 280000},
            {"city": "London", "lat": 51.5, "lon": -0.1, "pop": 280000},
            {"city": "Buenos Aires", "lat": -34.6, "lon": -58.4, "pop": 245000},
            {"city": "Paris", "lat": 48.9, "lon": 2.3, "pop": 310000},
            {"city": "Toronto", "lat": 43.7, "lon": -79.4, "pop": 200000},
            {"city": "Moscow", "lat": 55.8, "lon": 37.6, "pop": 165000},
            {"city": "Melbourne", "lat": -37.8, "lon": 145.0, "pop": 55000},
        ],
    },
    {
        "name": "African Diaspora",
        "color": "#f59e0b",
        "period": "1500s - Present",
        "origin": "West & Central Africa",
        "desc": "Forced migration via transatlantic slave trade and later voluntary emigration.",
        "communities": [
            {"city": "Salvador, Brazil", "lat": -12.97, "lon": -38.5, "pop": 2800000},
            {"city": "New York", "lat": 40.7, "lon": -74.0, "pop": 2300000},
            {"city": "Houston", "lat": 29.8, "lon": -95.4, "pop": 1100000},
            {"city": "Atlanta", "lat": 33.7, "lon": -84.4, "pop": 1800000},
            {"city": "London", "lat": 51.5, "lon": -0.1, "pop": 1100000},
            {"city": "Havana", "lat": 23.1, "lon": -82.4, "pop": 900000},
            {"city": "Kingston", "lat": 18.0, "lon": -76.8, "pop": 600000},
            {"city": "Port-au-Prince", "lat": 18.5, "lon": -72.3, "pop": 1200000},
            {"city": "Paris", "lat": 48.9, "lon": 2.3, "pop": 750000},
            {"city": "Detroit", "lat": 42.3, "lon": -83.0, "pop": 670000},
        ],
    },
    {
        "name": "Chinese Diaspora",
        "color": "#ef4444",
        "period": "1800s - Present",
        "origin": "Guangdong, Fujian, Hainan provinces",
        "desc": "Migration driven by economic opportunity, gold rushes, and political upheaval.",
        "communities": [
            {"city": "Bangkok", "lat": 13.8, "lon": 100.5, "pop": 7000000},
            {"city": "Jakarta", "lat": -6.2, "lon": 106.8, "pop": 2800000},
            {"city": "Singapore", "lat": 1.35, "lon": 103.8, "pop": 2900000},
            {"city": "Kuala Lumpur", "lat": 3.1, "lon": 101.7, "pop": 1700000},
            {"city": "San Francisco", "lat": 37.8, "lon": -122.4, "pop": 600000},
            {"city": "New York", "lat": 40.7, "lon": -74.0, "pop": 800000},
            {"city": "Vancouver", "lat": 49.3, "lon": -123.1, "pop": 500000},
            {"city": "Sydney", "lat": -33.9, "lon": 151.2, "pop": 500000},
            {"city": "Manila", "lat": 14.6, "lon": 121.0, "pop": 1400000},
            {"city": "London", "lat": 51.5, "lon": -0.1, "pop": 400000},
        ],
    },
    {
        "name": "Indian Diaspora",
        "color": "#10b981",
        "period": "1830s - Present",
        "origin": "British India (indentured labour, later skilled migration)",
        "desc": "Indentured workers sent to colonies; later waves of professionals worldwide.",
        "communities": [
            {"city": "Dubai", "lat": 25.2, "lon": 55.3, "pop": 3500000},
            {"city": "New York", "lat": 40.7, "lon": -74.0, "pop": 800000},
            {"city": "London", "lat": 51.5, "lon": -0.1, "pop": 1000000},
            {"city": "Toronto", "lat": 43.7, "lon": -79.4, "pop": 700000},
            {"city": "Durban", "lat": -29.9, "lon": 31.0, "pop": 1000000},
            {"city": "Singapore", "lat": 1.35, "lon": 103.8, "pop": 400000},
            {"city": "Kuala Lumpur", "lat": 3.1, "lon": 101.7, "pop": 2000000},
            {"city": "Port Louis", "lat": -20.2, "lon": 57.5, "pop": 900000},
            {"city": "San Jose", "lat": 37.3, "lon": -121.9, "pop": 350000},
            {"city": "Sydney", "lat": -33.9, "lon": 151.2, "pop": 350000},
        ],
    },
    {
        "name": "Irish Diaspora",
        "color": "#22c55e",
        "period": "1845 - Present",
        "origin": "Ireland (Great Famine and economic emigration)",
        "desc": "Massive emigration during the Great Famine; continued waves through the 20th century.",
        "communities": [
            {"city": "Boston", "lat": 42.4, "lon": -71.1, "pop": 500000},
            {"city": "New York", "lat": 40.7, "lon": -74.0, "pop": 800000},
            {"city": "Chicago", "lat": 41.9, "lon": -87.6, "pop": 350000},
            {"city": "Philadelphia", "lat": 39.95, "lon": -75.2, "pop": 250000},
            {"city": "London", "lat": 51.5, "lon": -0.1, "pop": 400000},
            {"city": "Liverpool", "lat": 53.4, "lon": -3.0, "pop": 120000},
            {"city": "Sydney", "lat": -33.9, "lon": 151.2, "pop": 200000},
            {"city": "Melbourne", "lat": -37.8, "lon": 145.0, "pop": 150000},
            {"city": "Toronto", "lat": 43.7, "lon": -79.4, "pop": 180000},
            {"city": "Glasgow", "lat": 55.9, "lon": -4.25, "pop": 90000},
        ],
    },
    {
        "name": "Armenian Diaspora",
        "color": "#f97316",
        "period": "1915 - Present",
        "origin": "Ottoman Empire / Armenia",
        "desc": "Genocide survivors scattered across Middle East, Europe, and Americas.",
        "communities": [
            {"city": "Los Angeles", "lat": 34.1, "lon": -118.2, "pop": 250000},
            {"city": "Moscow", "lat": 55.8, "lon": 37.6, "pop": 120000},
            {"city": "Beirut", "lat": 33.9, "lon": 35.5, "pop": 100000},
            {"city": "Aleppo", "lat": 36.2, "lon": 37.2, "pop": 60000},
            {"city": "Paris", "lat": 48.9, "lon": 2.3, "pop": 80000},
            {"city": "Buenos Aires", "lat": -34.6, "lon": -58.4, "pop": 70000},
            {"city": "Istanbul", "lat": 41.0, "lon": 29.0, "pop": 50000},
            {"city": "Tehran", "lat": 35.7, "lon": 51.4, "pop": 40000},
            {"city": "Fresno", "lat": 36.7, "lon": -119.8, "pop": 40000},
            {"city": "Sydney", "lat": -33.9, "lon": 151.2, "pop": 25000},
        ],
    },
]


# =====================================================================
# DATA: 4. COLONIAL MIGRATION PATTERNS
# =====================================================================
COLONIAL_ROUTES = [
    {
        "name": "Spanish to the Americas",
        "color": "#ef4444",
        "period": "1492-1700",
        "desc": "Spain colonised the Caribbean, Central and South America.",
        "coords": [[37.4, -5.9], [28.1, -15.4], [18.5, -69.9], [19.4, -99.1], [-12.0, -77.0]],
    },
    {
        "name": "Portuguese to Brazil",
        "color": "#22c55e",
        "period": "1500-1800",
        "desc": "Portugal claimed and colonised Brazil.",
        "coords": [[38.7, -9.1], [32.6, -16.9], [-12.97, -38.5]],
    },
    {
        "name": "British to North America",
        "color": "#3b82f6",
        "period": "1607-1776",
        "desc": "English settlers established colonies along the eastern seaboard.",
        "coords": [[50.7, -1.3], [48.0, -10.0], [42.4, -42.0], [37.0, -76.3]],
    },
    {
        "name": "French to Canada & Louisiana",
        "color": "#8b5cf6",
        "period": "1608-1763",
        "desc": "France colonised Quebec and the Mississippi Valley.",
        "coords": [[48.6, -1.7], [47.5, -20.0], [46.8, -71.2], [30.0, -90.1]],
    },
    {
        "name": "Dutch to East Indies",
        "color": "#f97316",
        "period": "1602-1949",
        "desc": "VOC established control over the Indonesian archipelago.",
        "coords": [[52.4, 4.9], [36.7, -6.3], [-33.9, 18.4], [-6.2, 106.8]],
    },
    {
        "name": "British to India",
        "color": "#06b6d4",
        "period": "1757-1947",
        "desc": "East India Company then Crown rule over the Indian subcontinent.",
        "coords": [[51.5, -0.1], [36.7, -6.3], [30.0, 32.0], [19.1, 72.9], [22.6, 88.4]],
    },
    {
        "name": "British to Australia",
        "color": "#14b8a6",
        "period": "1788-1901",
        "desc": "Penal colonies and free settlers to Australia.",
        "coords": [[51.5, -0.1], [36.7, -6.3], [-33.9, 18.4], [-33.9, 151.2]],
    },
    {
        "name": "European Scramble for Africa",
        "color": "#eab308",
        "period": "1880-1914",
        "desc": "European powers partitioned Africa at the Berlin Conference.",
        "coords": [[52.5, 13.4], [48.9, 2.3], [51.5, -0.1], [38.7, -9.1], [40.4, -3.7]],
        "dest_markers": [
            {"city": "Dakar", "lat": 14.7, "lon": -17.5},
            {"city": "Lagos", "lat": 6.5, "lon": 3.4},
            {"city": "Cape Town", "lat": -33.9, "lon": 18.4},
            {"city": "Nairobi", "lat": -1.3, "lon": 36.8},
            {"city": "Algiers", "lat": 36.8, "lon": 3.1},
        ],
    },
    {
        "name": "Japanese to East Asia & Pacific",
        "color": "#ec4899",
        "period": "1895-1945",
        "desc": "Japanese imperial expansion to Korea, Manchuria, SE Asia and Pacific.",
        "coords": [[35.7, 139.7], [37.6, 127.0], [43.8, 125.3], [14.6, 121.0], [1.35, 103.8]],
    },
    {
        "name": "Portuguese to Africa",
        "color": "#a855f7",
        "period": "1500-1975",
        "desc": "Portugal colonised Angola, Mozambique, Guinea-Bissau, and Cape Verde.",
        "coords": [[38.7, -9.1], [14.9, -23.5], [-8.8, 13.2], [-25.9, 32.6]],
    },
]


# =====================================================================
# DATA: 5. SILK ROAD NETWORK
# =====================================================================
SILK_ROAD_CITIES = [
    {"city": "Xi'an (Chang'an)", "lat": 34.3, "lon": 108.9, "role": "Eastern terminus", "era": "206 BC - 1400s AD"},
    {"city": "Lanzhou", "lat": 36.1, "lon": 103.8, "role": "Gateway to the west", "era": "Han Dynasty onward"},
    {"city": "Dunhuang", "lat": 40.1, "lon": 94.7, "role": "Oasis city, Mogao Caves", "era": "111 BC onward"},
    {"city": "Turpan", "lat": 42.9, "lon": 89.2, "role": "Oasis in Taklamakan margin", "era": "1st century BC"},
    {"city": "Kashgar", "lat": 39.5, "lon": 76.0, "role": "Key junction of N/S routes", "era": "2nd century BC"},
    {"city": "Kucha", "lat": 41.7, "lon": 82.9, "role": "Buddhist centre", "era": "2nd century BC"},
    {"city": "Khotan", "lat": 37.1, "lon": 79.9, "role": "Jade and silk trading", "era": "3rd century BC"},
    {"city": "Almaty", "lat": 43.2, "lon": 76.9, "role": "Northern route stop", "era": "Medieval period"},
    {"city": "Tashkent", "lat": 41.3, "lon": 69.3, "role": "Central Asian hub", "era": "2nd century BC"},
    {"city": "Samarkand", "lat": 39.7, "lon": 66.9, "role": "Timurid capital, major trade hub", "era": "8th century BC"},
    {"city": "Bukhara", "lat": 39.8, "lon": 64.4, "role": "Islamic learning center", "era": "6th century BC"},
    {"city": "Merv", "lat": 37.7, "lon": 62.2, "role": "One of largest ancient cities", "era": "3rd millennium BC"},
    {"city": "Balkh", "lat": 36.8, "lon": 66.9, "role": "Mother of Cities", "era": "2000 BC"},
    {"city": "Herat", "lat": 34.3, "lon": 62.2, "role": "Crossroads of Central Asia", "era": "3rd millennium BC"},
    {"city": "Kabul", "lat": 34.5, "lon": 69.2, "role": "Mountain route junction", "era": "Ancient"},
    {"city": "Peshawar", "lat": 34.0, "lon": 71.6, "role": "Gandharan Buddhist center", "era": "Ancient"},
    {"city": "Tehran", "lat": 35.7, "lon": 51.4, "role": "Northern Iranian route", "era": "Medieval"},
    {"city": "Isfahan", "lat": 32.7, "lon": 51.7, "role": "Persian cultural capital", "era": "Safavid era"},
    {"city": "Tabriz", "lat": 38.1, "lon": 46.3, "role": "Mongol-era terminus", "era": "Medieval"},
    {"city": "Baghdad", "lat": 33.3, "lon": 44.4, "role": "Abbasid caliphate capital", "era": "8th century AD"},
    {"city": "Palmyra", "lat": 34.6, "lon": 38.3, "role": "Desert oasis caravan city", "era": "2nd millennium BC"},
    {"city": "Aleppo", "lat": 36.2, "lon": 37.2, "role": "Mediterranean trade link", "era": "3rd millennium BC"},
    {"city": "Antioch", "lat": 36.2, "lon": 36.2, "role": "Roman eastern capital", "era": "300 BC"},
    {"city": "Damascus", "lat": 33.5, "lon": 36.3, "role": "Oldest continuously inhabited", "era": "10000 BC"},
    {"city": "Ctesiphon", "lat": 33.1, "lon": 44.6, "role": "Parthian/Sassanid capital", "era": "2nd century BC"},
    {"city": "Trebizond", "lat": 41.0, "lon": 39.7, "role": "Black Sea port", "era": "Byzantine era"},
    {"city": "Constantinople", "lat": 41.0, "lon": 29.0, "role": "Western terminus, Byzantine capital", "era": "330 AD"},
    {"city": "Alexandria", "lat": 31.2, "lon": 29.9, "role": "Egyptian maritime link", "era": "331 BC"},
    {"city": "Tyre", "lat": 33.3, "lon": 35.2, "role": "Phoenician port", "era": "2750 BC"},
    {"city": "Venice", "lat": 45.4, "lon": 12.3, "role": "European trade gateway", "era": "Medieval"},
    {"city": "Genoa", "lat": 44.4, "lon": 8.9, "role": "Maritime republic", "era": "Medieval"},
    {"city": "Rome", "lat": 41.9, "lon": 12.5, "role": "Silk imports from China", "era": "1st century BC"},
    {"city": "Hormuz", "lat": 27.1, "lon": 56.3, "role": "Persian Gulf port", "era": "14th century AD"},
    {"city": "Aden", "lat": 12.8, "lon": 45.0, "role": "Indian Ocean spice port", "era": "Ancient"},
    {"city": "Taxila", "lat": 33.7, "lon": 72.8, "role": "Gandharan learning center", "era": "6th century BC"},
    {"city": "Yarkand", "lat": 38.4, "lon": 77.3, "role": "Southern route oasis", "era": "Han Dynasty"},
    {"city": "Nisa", "lat": 38.0, "lon": 58.2, "role": "Parthian royal city", "era": "3rd century BC"},
    {"city": "Karakorum", "lat": 47.2, "lon": 102.8, "role": "Mongol Empire capital", "era": "13th century AD"},
    {"city": "Lhasa", "lat": 29.6, "lon": 91.1, "role": "Tibetan trade route", "era": "7th century AD"},
    {"city": "Quanzhou", "lat": 24.9, "lon": 118.6, "role": "Maritime silk road port", "era": "Song Dynasty"},
]

SILK_ROAD_ROUTES = [
    {
        "name": "Northern Route",
        "color": "#ef4444",
        "coords": [
            [34.3, 108.9], [36.1, 103.8], [40.1, 94.7], [42.9, 89.2],
            [41.7, 82.9], [39.5, 76.0], [43.2, 76.9], [41.3, 69.3],
            [39.7, 66.9], [39.8, 64.4], [37.7, 62.2], [38.0, 58.2],
            [35.7, 51.4], [38.1, 46.3], [41.0, 39.7], [41.0, 29.0],
        ],
    },
    {
        "name": "Southern Route",
        "color": "#f59e0b",
        "coords": [
            [34.3, 108.9], [36.1, 103.8], [40.1, 94.7], [37.1, 79.9],
            [38.4, 77.3], [39.5, 76.0], [34.5, 69.2], [34.0, 71.6],
            [33.7, 72.8], [34.3, 62.2], [36.8, 66.9], [33.3, 44.4],
            [34.6, 38.3], [36.2, 37.2], [33.5, 36.3], [33.3, 35.2],
        ],
    },
    {
        "name": "Maritime Route",
        "color": "#06b6d4",
        "coords": [
            [24.9, 118.6], [34.3, 108.9], [24.9, 118.6],
            [14.6, 121.0], [1.35, 103.8], [10.0, 80.0],
            [12.8, 45.0], [27.1, 56.3], [30.0, 32.0],
            [31.2, 29.9], [41.0, 29.0], [45.4, 12.3],
        ],
    },
]


# =====================================================================
# DATA: 6. AGE OF EXPLORATION VOYAGES
# =====================================================================
EXPLORATION_VOYAGES = [
    {
        "name": "Columbus - 1st Voyage (1492)",
        "color": "#ef4444",
        "explorer": "Christopher Columbus",
        "year": 1492,
        "sponsor": "Spain",
        "desc": "First European voyage to the Caribbean, reached the Bahamas.",
        "coords": [
            [37.0, -6.0], [28.0, -15.5], [24.0, -76.0],
            [19.9, -75.8], [21.5, -71.0],
        ],
    },
    {
        "name": "Vasco da Gama (1497-1499)",
        "color": "#22c55e",
        "explorer": "Vasco da Gama",
        "year": 1497,
        "sponsor": "Portugal",
        "desc": "First European to reach India by sea, rounding the Cape of Good Hope.",
        "coords": [
            [38.7, -9.1], [14.9, -23.5], [-5.0, -5.0], [-33.9, 18.4],
            [-25.9, 32.6], [-6.2, 39.3], [12.8, 45.0], [11.0, 75.8],
        ],
    },
    {
        "name": "Magellan / Elcano (1519-1522)",
        "color": "#3b82f6",
        "explorer": "Ferdinand Magellan",
        "year": 1519,
        "sponsor": "Spain",
        "desc": "First circumnavigation of the globe (Magellan killed in Philippines, Elcano completed).",
        "coords": [
            [36.5, -6.3], [28.0, -15.5], [-8.0, -34.9], [-23.0, -43.2],
            [-52.5, -70.0], [-33.5, -100.0], [-17.5, -149.5],
            [10.3, 124.0], [1.35, 103.8], [-6.2, 39.3],
            [-33.9, 18.4], [36.5, -6.3],
        ],
    },
    {
        "name": "Drake Circumnavigation (1577-1580)",
        "color": "#a855f7",
        "explorer": "Francis Drake",
        "year": 1577,
        "sponsor": "England",
        "desc": "Second circumnavigation; raided Spanish ports along the way.",
        "coords": [
            [50.4, -3.5], [28.0, -15.5], [-8.0, -34.9],
            [-52.5, -70.0], [-33.5, -100.0], [37.8, -122.4],
            [47.5, -123.0], [3.0, 101.0], [-33.9, 18.4],
            [50.4, -3.5],
        ],
    },
    {
        "name": "James Cook - 1st Voyage (1768-1771)",
        "color": "#f59e0b",
        "explorer": "James Cook",
        "year": 1768,
        "sponsor": "Britain",
        "desc": "Observed transit of Venus in Tahiti; charted New Zealand and Australia's east coast.",
        "coords": [
            [50.4, -3.5], [28.0, -15.5], [-22.9, -43.2],
            [-55.0, -67.0], [-17.5, -149.5], [-41.3, 174.8],
            [-33.9, 151.2], [-6.2, 106.8], [-33.9, 18.4],
            [50.4, -3.5],
        ],
    },
    {
        "name": "Zheng He Voyages (1405-1433)",
        "color": "#ec4899",
        "explorer": "Zheng He",
        "year": 1405,
        "sponsor": "Ming Dynasty China",
        "desc": "Seven grand maritime expeditions across the Indian Ocean to Africa.",
        "coords": [
            [32.1, 118.8], [24.9, 118.6], [10.0, 106.0],
            [1.35, 103.8], [6.9, 79.9], [10.0, 76.0],
            [12.8, 45.0], [-6.2, 39.3], [-4.0, 39.7],
        ],
    },
    {
        "name": "Vespucci - South America (1499-1502)",
        "color": "#14b8a6",
        "explorer": "Amerigo Vespucci",
        "year": 1499,
        "sponsor": "Spain / Portugal",
        "desc": "Explored South American coast; recognized it as a new continent.",
        "coords": [
            [36.5, -6.3], [28.0, -15.5], [6.0, -52.0],
            [-3.0, -41.0], [-8.0, -34.9], [-23.0, -43.2],
        ],
    },
    {
        "name": "Cabot - North America (1497)",
        "color": "#06b6d4",
        "explorer": "John Cabot",
        "year": 1497,
        "sponsor": "England",
        "desc": "Reached Newfoundland; basis for English claims in North America.",
        "coords": [
            [51.5, -2.6], [51.0, -10.0], [47.6, -52.7],
        ],
    },
]


# =====================================================================
# DATA: 7. TRANSATLANTIC SLAVE TRADE
# =====================================================================
SLAVE_TRADE_ROUTES = [
    {
        "name": "West Africa to Brazil",
        "color": "#dc2626",
        "origin": "Bight of Benin / Angola",
        "dest": "Brazil (Bahia, Rio)",
        "embarked": 5848000,
        "disembarked": 5099000,
        "period": "1560-1850",
        "coords": [[6.4, 2.6], [0.0, -10.0], [-12.97, -38.5]],
    },
    {
        "name": "West Africa to Caribbean (British)",
        "color": "#ef4444",
        "origin": "Gold Coast / Windward Coast",
        "dest": "Jamaica, Barbados",
        "embarked": 2318000,
        "disembarked": 2009000,
        "period": "1640-1807",
        "coords": [[5.6, -0.2], [10.0, -30.0], [18.0, -76.8]],
    },
    {
        "name": "West Africa to Caribbean (French)",
        "color": "#f97316",
        "origin": "Senegambia / Bight of Benin",
        "dest": "Saint-Domingue (Haiti), Martinique",
        "embarked": 1381000,
        "disembarked": 1165000,
        "period": "1660-1831",
        "coords": [[14.7, -17.5], [10.0, -35.0], [18.5, -72.3]],
    },
    {
        "name": "West Africa to Spanish Americas",
        "color": "#eab308",
        "origin": "Senegambia / Angola",
        "dest": "Cuba, Cartagena, Veracruz",
        "embarked": 1061000,
        "disembarked": 906000,
        "period": "1520-1866",
        "coords": [[14.7, -17.5], [10.0, -35.0], [23.1, -82.4]],
    },
    {
        "name": "West Africa to North America",
        "color": "#a855f7",
        "origin": "Senegambia / Sierra Leone",
        "dest": "Virginia, Carolina, Georgia",
        "embarked": 472000,
        "disembarked": 389000,
        "period": "1619-1808",
        "coords": [[8.5, -13.2], [15.0, -40.0], [32.8, -79.9]],
    },
    {
        "name": "West Africa to Dutch Colonies",
        "color": "#3b82f6",
        "origin": "Gold Coast / Loango",
        "dest": "Suriname, Curacao",
        "embarked": 554000,
        "disembarked": 468000,
        "period": "1630-1803",
        "coords": [[5.6, -0.2], [5.0, -25.0], [5.8, -55.2]],
    },
    {
        "name": "East African Trade",
        "color": "#14b8a6",
        "origin": "Mozambique / Zanzibar",
        "dest": "Indian Ocean islands, Arabia",
        "embarked": 400000,
        "disembarked": 340000,
        "period": "1500-1900",
        "coords": [[-6.2, 39.3], [-12.3, 44.3], [-20.2, 57.5], [12.8, 45.0]],
    },
]


# =====================================================================
# DATA: 8. GOLD RUSH MIGRATIONS
# =====================================================================
GOLD_RUSHES = [
    {
        "name": "California Gold Rush",
        "lat": 38.7, "lon": -120.8,
        "year": 1848,
        "peak_pop": 300000,
        "period": "1848-1855",
        "origin_regions": "USA (east), China, Mexico, Europe, Chile, Australia",
        "desc": "Gold discovered at Sutter's Mill; 300,000 people arrived in California.",
        "color": "#f59e0b",
    },
    {
        "name": "Victorian Gold Rush (Australia)",
        "lat": -37.6, "lon": 144.3,
        "year": 1851,
        "peak_pop": 500000,
        "period": "1851-1860s",
        "origin_regions": "Britain, Ireland, China, Europe",
        "desc": "Gold found near Ballarat and Bendigo; tripled Australia's population.",
        "color": "#eab308",
    },
    {
        "name": "Klondike Gold Rush",
        "lat": 63.9, "lon": -139.4,
        "year": 1896,
        "peak_pop": 100000,
        "period": "1896-1899",
        "origin_regions": "USA, Canada, worldwide",
        "desc": "Gold discovered in Yukon; stampede of 100,000 prospectors.",
        "color": "#f97316",
    },
    {
        "name": "Brazilian Gold Rush (Minas Gerais)",
        "lat": -19.9, "lon": -43.9,
        "year": 1693,
        "peak_pop": 400000,
        "period": "1693-1750s",
        "origin_regions": "Portugal, enslaved Africans",
        "desc": "Largest gold rush of the 18th century; transformed colonial Brazil.",
        "color": "#ef4444",
    },
    {
        "name": "Witwatersrand Gold Rush (South Africa)",
        "lat": -26.2, "lon": 28.0,
        "year": 1886,
        "peak_pop": 100000,
        "period": "1886-1899",
        "origin_regions": "Britain, Europe, Africans from across the continent",
        "desc": "World's largest gold deposit; led to founding of Johannesburg.",
        "color": "#a855f7",
    },
    {
        "name": "Fraser Canyon Gold Rush (BC, Canada)",
        "lat": 49.4, "lon": -121.4,
        "year": 1858,
        "peak_pop": 30000,
        "period": "1858-1860",
        "origin_regions": "California miners, British, Chinese",
        "desc": "Gold found in Fraser River; led to creation of British Columbia.",
        "color": "#3b82f6",
    },
    {
        "name": "Otago Gold Rush (New Zealand)",
        "lat": -45.0, "lon": 169.3,
        "year": 1861,
        "peak_pop": 18000,
        "period": "1861-1864",
        "origin_regions": "Australian miners, British, Chinese, Irish",
        "desc": "Gold discovered in Gabriel's Gully; Otago became NZ's richest province.",
        "color": "#10b981",
    },
    {
        "name": "Nome Gold Rush (Alaska)",
        "lat": 64.5, "lon": -165.4,
        "year": 1899,
        "peak_pop": 20000,
        "period": "1899-1909",
        "origin_regions": "Klondike veterans, USA",
        "desc": "Gold on the beaches of Nome; no claims needed, anyone could pan.",
        "color": "#06b6d4",
    },
]


# =====================================================================
# DATA: 9. MODERN IMMIGRATION DATA (hardcoded + REST Countries fallback)
# =====================================================================
IMMIGRATION_HOTSPOTS = [
    {"country": "United Arab Emirates", "lat": 24.5, "lon": 54.7, "imm_pct": 88.1, "pop": 9890000, "color": "#ef4444"},
    {"country": "Qatar", "lat": 25.3, "lon": 51.2, "imm_pct": 77.3, "pop": 2880000, "color": "#ef4444"},
    {"country": "Kuwait", "lat": 29.3, "lon": 47.5, "imm_pct": 72.1, "pop": 4270000, "color": "#ef4444"},
    {"country": "Bahrain", "lat": 26.0, "lon": 50.6, "imm_pct": 55.0, "pop": 1700000, "color": "#f97316"},
    {"country": "Singapore", "lat": 1.35, "lon": 103.8, "imm_pct": 43.0, "pop": 5690000, "color": "#f97316"},
    {"country": "Luxembourg", "lat": 49.6, "lon": 6.1, "imm_pct": 47.4, "pop": 634000, "color": "#f97316"},
    {"country": "Saudi Arabia", "lat": 24.7, "lon": 46.7, "imm_pct": 38.3, "pop": 34810000, "color": "#eab308"},
    {"country": "Switzerland", "lat": 46.8, "lon": 8.2, "imm_pct": 29.9, "pop": 8636000, "color": "#eab308"},
    {"country": "Australia", "lat": -25.3, "lon": 133.8, "imm_pct": 30.0, "pop": 25690000, "color": "#eab308"},
    {"country": "Canada", "lat": 56.1, "lon": -106.3, "imm_pct": 21.3, "pop": 38010000, "color": "#22c55e"},
    {"country": "New Zealand", "lat": -40.9, "lon": 174.9, "imm_pct": 28.8, "pop": 5120000, "color": "#eab308"},
    {"country": "Austria", "lat": 47.5, "lon": 14.6, "imm_pct": 19.4, "pop": 9010000, "color": "#22c55e"},
    {"country": "Germany", "lat": 51.2, "lon": 10.4, "imm_pct": 18.8, "pop": 83200000, "color": "#22c55e"},
    {"country": "Sweden", "lat": 60.1, "lon": 18.6, "imm_pct": 20.0, "pop": 10350000, "color": "#22c55e"},
    {"country": "United States", "lat": 37.1, "lon": -95.7, "imm_pct": 15.3, "pop": 331000000, "color": "#3b82f6"},
    {"country": "United Kingdom", "lat": 55.4, "lon": -3.4, "imm_pct": 14.1, "pop": 67890000, "color": "#3b82f6"},
    {"country": "France", "lat": 46.2, "lon": 2.2, "imm_pct": 12.8, "pop": 67390000, "color": "#3b82f6"},
    {"country": "Spain", "lat": 40.5, "lon": -3.7, "imm_pct": 15.2, "pop": 47350000, "color": "#3b82f6"},
    {"country": "Italy", "lat": 41.9, "lon": 12.6, "imm_pct": 10.5, "pop": 60360000, "color": "#8b5cf6"},
    {"country": "Russia", "lat": 61.5, "lon": 105.3, "imm_pct": 8.0, "pop": 145900000, "color": "#8b5cf6"},
    {"country": "Jordan", "lat": 30.6, "lon": 36.2, "imm_pct": 33.9, "pop": 10200000, "color": "#eab308"},
    {"country": "Oman", "lat": 21.5, "lon": 55.9, "imm_pct": 46.0, "pop": 5110000, "color": "#f97316"},
    {"country": "Ireland", "lat": 53.4, "lon": -8.2, "imm_pct": 17.6, "pop": 4940000, "color": "#22c55e"},
    {"country": "Norway", "lat": 60.5, "lon": 8.5, "imm_pct": 16.3, "pop": 5420000, "color": "#22c55e"},
]


# =====================================================================
# DATA: 10. CLIMATE MIGRATION PROJECTIONS
# =====================================================================
CLIMATE_RISKS = [
    {
        "city": "Miami", "lat": 25.8, "lon": -80.2,
        "risk": "Sea level rise", "severity": "Critical",
        "pop_affected": 6100000, "projection": "1-2m rise by 2100",
        "color": "#ef4444",
    },
    {
        "city": "Jakarta", "lat": -6.2, "lon": 106.8,
        "risk": "Sinking city + sea rise", "severity": "Critical",
        "pop_affected": 10500000, "projection": "Parts 2.5m below sea level by 2050",
        "color": "#ef4444",
    },
    {
        "city": "Dhaka", "lat": 23.8, "lon": 90.4,
        "risk": "Flooding + cyclones", "severity": "Critical",
        "pop_affected": 21000000, "projection": "17% land lost by 2050 with 1m rise",
        "color": "#ef4444",
    },
    {
        "city": "Lagos", "lat": 6.5, "lon": 3.4,
        "risk": "Coastal flooding", "severity": "Critical",
        "pop_affected": 15400000, "projection": "Most of Victoria Island submerged by 2100",
        "color": "#ef4444",
    },
    {
        "city": "Shanghai", "lat": 31.2, "lon": 121.5,
        "risk": "Sea level rise + subsidence", "severity": "High",
        "pop_affected": 24300000, "projection": "Severe flooding risk by 2050",
        "color": "#f97316",
    },
    {
        "city": "Mumbai", "lat": 19.1, "lon": 72.9,
        "risk": "Cyclones + flooding", "severity": "High",
        "pop_affected": 20700000, "projection": "Annual flooding worsening by 2040",
        "color": "#f97316",
    },
    {
        "city": "New Orleans", "lat": 30.0, "lon": -90.1,
        "risk": "Subsidence + hurricanes", "severity": "High",
        "pop_affected": 1270000, "projection": "Below sea level, depends on levees",
        "color": "#f97316",
    },
    {
        "city": "Bangkok", "lat": 13.8, "lon": 100.5,
        "risk": "Sinking + sea rise", "severity": "High",
        "pop_affected": 10500000, "projection": "Much of city below sea level by 2030",
        "color": "#f97316",
    },
    {
        "city": "Ho Chi Minh City", "lat": 10.8, "lon": 106.6,
        "risk": "Mekong Delta flooding", "severity": "High",
        "pop_affected": 9000000, "projection": "Mekong Delta largely submerged by 2050",
        "color": "#f97316",
    },
    {
        "city": "Alexandria", "lat": 31.2, "lon": 29.9,
        "risk": "Mediterranean rise", "severity": "High",
        "pop_affected": 5200000, "projection": "Nile Delta erosion accelerating",
        "color": "#f97316",
    },
    {
        "city": "Sahel Region (Ouagadougou)", "lat": 12.4, "lon": -1.5,
        "risk": "Desertification + drought", "severity": "Critical",
        "pop_affected": 135000000, "projection": "135M at risk across the Sahel by 2030",
        "color": "#ef4444",
    },
    {
        "city": "Central America (Guatemala City)", "lat": 14.6, "lon": -90.5,
        "risk": "Drought + extreme weather", "severity": "High",
        "pop_affected": 8000000, "projection": "Dry Corridor affecting millions",
        "color": "#f97316",
    },
    {
        "city": "Small Island States (Tuvalu)", "lat": -8.5, "lon": 179.2,
        "risk": "Complete submersion", "severity": "Critical",
        "pop_affected": 12000, "projection": "Entire nation uninhabitable by 2050-2100",
        "color": "#ef4444",
    },
    {
        "city": "Maldives (Male)", "lat": 4.2, "lon": 73.5,
        "risk": "Complete submersion", "severity": "Critical",
        "pop_affected": 540000, "projection": "80% of land less than 1m above sea",
        "color": "#ef4444",
    },
    {
        "city": "Kiribati (Tarawa)", "lat": 1.4, "lon": 173.0,
        "risk": "Complete submersion", "severity": "Critical",
        "pop_affected": 120000, "projection": "Already purchasing land in Fiji",
        "color": "#ef4444",
    },
    {
        "city": "Marshall Islands (Majuro)", "lat": 7.1, "lon": 171.4,
        "risk": "Rising seas + storms", "severity": "Critical",
        "pop_affected": 59000, "projection": "2m avg elevation, uninhabitable by 2080",
        "color": "#ef4444",
    },
    {
        "city": "Sub-Saharan Africa (Mogadishu)", "lat": 2.0, "lon": 45.3,
        "risk": "Drought + famine", "severity": "High",
        "pop_affected": 86000000, "projection": "86M internal migrants by 2050 (World Bank)",
        "color": "#f97316",
    },
    {
        "city": "South Asia (Kolkata)", "lat": 22.6, "lon": 88.4,
        "risk": "Flooding + heat", "severity": "High",
        "pop_affected": 40000000, "projection": "40M South Asian internal migrants by 2050",
        "color": "#f97316",
    },
    {
        "city": "Phoenix, USA", "lat": 33.4, "lon": -112.1,
        "risk": "Extreme heat + water scarcity", "severity": "Moderate",
        "pop_affected": 4900000, "projection": "Wet-bulb temps approaching survivability limits",
        "color": "#eab308",
    },
    {
        "city": "Venice", "lat": 45.4, "lon": 12.3,
        "risk": "Adriatic Sea rise + subsidence", "severity": "High",
        "pop_affected": 260000, "projection": "MOSE barriers may be insufficient by 2100",
        "color": "#f97316",
    },
]


# =====================================================================
# API CALL: REST COUNTRIES (for mode 9 enrichment)
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_rest_countries():
    """Fetch country data from REST Countries API."""
    try:
        resp = requests.get(
            "https://restcountries.com/v3.1/all?fields=name,population,region,subregion,latlng,flags",
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


# =====================================================================
# MAP BUILDERS
# =====================================================================

def _base_map(center=None, zoom=2):
    """Create a dark Folium base map."""
    if center is None:
        center = [20, 10]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _build_human_migration_map(selected_routes):
    """Build map of human migration routes."""
    m = _base_map(center=[20, 40], zoom=2)
    for route in HUMAN_MIGRATION_ROUTES:
        if route["name"] not in selected_routes:
            continue
        folium.PolyLine(
            locations=route["coords"],
            color=route["color"],
            weight=3,
            opacity=0.85,
            tooltip=html.escape(route["name"]),
            popup=folium.Popup(
                f"<div style='min-width:200px'>"
                f"<b>{html.escape(route['name'])}</b><br>"
                f"<i>{html.escape(route['period'])}</i><br><br>"
                f"{html.escape(route['desc'])}</div>",
                max_width=300,
            ),
            dash_array="8 4",
        ).add_to(m)
        # Start marker
        start = route["coords"][0]
        folium.CircleMarker(
            location=start,
            radius=5,
            color=route["color"],
            fill=True,
            fill_opacity=0.9,
            tooltip=html.escape(f"Start: {route['name']}"),
        ).add_to(m)
        # End marker
        end = route["coords"][-1]
        folium.CircleMarker(
            location=end,
            radius=6,
            color=route["color"],
            fill=True,
            fill_color="#ffffff",
            fill_opacity=0.8,
            tooltip=html.escape(f"End: {route['name']}"),
        ).add_to(m)
    return m


def _build_refugee_map(origin_filter):
    """Build map of modern refugee flows."""
    m = _base_map(center=[25, 40], zoom=3)
    filtered = [r for r in REFUGEE_FLOWS if origin_filter == "All" or r["origin"] == origin_filter]
    for flow in filtered:
        weight = max(2, min(8, flow["people"] / 500000))
        folium.PolyLine(
            locations=[flow["origin_ll"], flow["dest_ll"]],
            color=flow["color"],
            weight=weight,
            opacity=0.7,
            tooltip=html.escape(
                f"{flow['origin']} -> {flow['dest']}: {flow['people']:,}"
            ),
            popup=folium.Popup(
                f"<div style='min-width:200px'>"
                f"<b>{html.escape(flow['origin'])} &rarr; {html.escape(flow['dest'])}</b><br>"
                f"Refugees: <b>{flow['people']:,}</b><br>"
                f"Year: {flow['year']}</div>",
                max_width=300,
            ),
        ).add_to(m)
        # Origin marker
        folium.CircleMarker(
            location=flow["origin_ll"],
            radius=7,
            color=flow["color"],
            fill=True,
            fill_opacity=0.9,
            tooltip=html.escape(f"Origin: {flow['origin']}"),
        ).add_to(m)
        # Dest marker
        folium.CircleMarker(
            location=flow["dest_ll"],
            radius=5,
            color="#ffffff",
            fill=True,
            fill_color=flow["color"],
            fill_opacity=0.6,
            tooltip=html.escape(f"Dest: {flow['dest']}"),
        ).add_to(m)
    return m, filtered


def _build_diaspora_map(selected_diasporas):
    """Build map of great diasporas."""
    m = _base_map(center=[20, 20], zoom=2)
    for dia in GREAT_DIASPORAS:
        if dia["name"] not in selected_diasporas:
            continue
        for comm in dia["communities"]:
            radius = max(4, min(14, comm["pop"] / 200000))
            folium.CircleMarker(
                location=[comm["lat"], comm["lon"]],
                radius=radius,
                color=dia["color"],
                fill=True,
                fill_opacity=0.7,
                tooltip=html.escape(
                    f"{dia['name']} - {comm['city']}: {comm['pop']:,}"
                ),
                popup=folium.Popup(
                    f"<div style='min-width:180px'>"
                    f"<b>{html.escape(dia['name'])}</b><br>"
                    f"City: {html.escape(comm['city'])}<br>"
                    f"Population: {comm['pop']:,}<br>"
                    f"Period: {html.escape(dia['period'])}</div>",
                    max_width=280,
                ),
            ).add_to(m)
    return m


def _build_colonial_map(selected_routes):
    """Build colonial migration routes map."""
    m = _base_map(center=[20, 10], zoom=2)
    for route in COLONIAL_ROUTES:
        if route["name"] not in selected_routes:
            continue
        folium.PolyLine(
            locations=route["coords"],
            color=route["color"],
            weight=3,
            opacity=0.8,
            tooltip=html.escape(route["name"]),
            popup=folium.Popup(
                f"<div style='min-width:200px'>"
                f"<b>{html.escape(route['name'])}</b><br>"
                f"<i>{html.escape(route['period'])}</i><br><br>"
                f"{html.escape(route['desc'])}</div>",
                max_width=300,
            ),
            dash_array="6 3",
        ).add_to(m)
        start = route["coords"][0]
        folium.CircleMarker(
            location=start, radius=5, color=route["color"],
            fill=True, fill_opacity=0.9,
            tooltip=html.escape(f"Origin: {route['name']}"),
        ).add_to(m)
        end = route["coords"][-1]
        folium.CircleMarker(
            location=end, radius=6, color=route["color"],
            fill=True, fill_color="#ffffff", fill_opacity=0.7,
            tooltip=html.escape(f"Destination: {route['name']}"),
        ).add_to(m)
        # Extra destination markers for Scramble for Africa
        if "dest_markers" in route:
            for dm in route["dest_markers"]:
                folium.CircleMarker(
                    location=[dm["lat"], dm["lon"]], radius=5,
                    color=route["color"], fill=True, fill_opacity=0.7,
                    tooltip=html.escape(dm["city"]),
                ).add_to(m)
    return m


def _build_silk_road_map(show_maritime):
    """Build Silk Road network map."""
    m = _base_map(center=[35, 70], zoom=4)
    for city in SILK_ROAD_CITIES:
        folium.CircleMarker(
            location=[city["lat"], city["lon"]],
            radius=5,
            color="#f59e0b",
            fill=True,
            fill_opacity=0.8,
            tooltip=html.escape(city["city"]),
            popup=folium.Popup(
                f"<div style='min-width:180px'>"
                f"<b>{html.escape(city['city'])}</b><br>"
                f"Role: {html.escape(city['role'])}<br>"
                f"Era: {html.escape(city['era'])}</div>",
                max_width=280,
            ),
        ).add_to(m)
    for route in SILK_ROAD_ROUTES:
        if not show_maritime and route["name"] == "Maritime Route":
            continue
        folium.PolyLine(
            locations=route["coords"],
            color=route["color"],
            weight=3,
            opacity=0.75,
            tooltip=html.escape(route["name"]),
            dash_array="6 4",
        ).add_to(m)
    return m


def _build_exploration_map(selected_voyages):
    """Build Age of Exploration map."""
    m = _base_map(center=[10, -10], zoom=2)
    for voyage in EXPLORATION_VOYAGES:
        if voyage["name"] not in selected_voyages:
            continue
        folium.PolyLine(
            locations=voyage["coords"],
            color=voyage["color"],
            weight=3,
            opacity=0.85,
            tooltip=html.escape(voyage["name"]),
            popup=folium.Popup(
                f"<div style='min-width:220px'>"
                f"<b>{html.escape(voyage['name'])}</b><br>"
                f"Explorer: {html.escape(voyage['explorer'])}<br>"
                f"Sponsor: {html.escape(voyage['sponsor'])}<br><br>"
                f"{html.escape(voyage['desc'])}</div>",
                max_width=320,
            ),
        ).add_to(m)
        start = voyage["coords"][0]
        folium.CircleMarker(
            location=start, radius=5, color=voyage["color"],
            fill=True, fill_opacity=0.9,
            tooltip=html.escape(f"Start: {voyage['name']}"),
        ).add_to(m)
        end = voyage["coords"][-1]
        folium.CircleMarker(
            location=end, radius=6, color=voyage["color"],
            fill=True, fill_color="#ffffff", fill_opacity=0.7,
            tooltip=html.escape(f"End: {voyage['name']}"),
        ).add_to(m)
    return m


def _build_slave_trade_map(selected_routes):
    """Build transatlantic slave trade map."""
    m = _base_map(center=[5, -20], zoom=3)
    for route in SLAVE_TRADE_ROUTES:
        if route["name"] not in selected_routes:
            continue
        weight = max(2, min(9, route["embarked"] / 800000))
        folium.PolyLine(
            locations=route["coords"],
            color=route["color"],
            weight=weight,
            opacity=0.75,
            tooltip=html.escape(
                f"{route['name']}: ~{route['embarked']:,} embarked"
            ),
            popup=folium.Popup(
                f"<div style='min-width:220px'>"
                f"<b>{html.escape(route['name'])}</b><br>"
                f"Origin: {html.escape(route['origin'])}<br>"
                f"Destination: {html.escape(route['dest'])}<br>"
                f"Embarked: <b>{route['embarked']:,}</b><br>"
                f"Disembarked: <b>{route['disembarked']:,}</b><br>"
                f"Period: {html.escape(route['period'])}<br>"
                f"<i>Mortality in transit: ~{route['embarked'] - route['disembarked']:,}</i></div>",
                max_width=320,
            ),
        ).add_to(m)
        # Origin
        start = route["coords"][0]
        folium.CircleMarker(
            location=start, radius=6, color=route["color"],
            fill=True, fill_opacity=0.9,
            tooltip=html.escape(f"Embarkation: {route['origin']}"),
        ).add_to(m)
        # Dest
        end = route["coords"][-1]
        folium.CircleMarker(
            location=end, radius=6, color="#ffffff",
            fill=True, fill_color=route["color"], fill_opacity=0.7,
            tooltip=html.escape(f"Destination: {route['dest']}"),
        ).add_to(m)
    return m


def _build_gold_rush_map():
    """Build gold rush locations map."""
    m = _base_map(center=[20, -10], zoom=2)
    for gr in GOLD_RUSHES:
        radius = max(6, min(14, gr["peak_pop"] / 40000))
        folium.CircleMarker(
            location=[gr["lat"], gr["lon"]],
            radius=radius,
            color=gr["color"],
            fill=True,
            fill_opacity=0.8,
            tooltip=html.escape(f"{gr['name']} ({gr['period']})"),
            popup=folium.Popup(
                f"<div style='min-width:200px'>"
                f"<b>{html.escape(gr['name'])}</b><br>"
                f"Year: {gr['year']}<br>"
                f"Period: {html.escape(gr['period'])}<br>"
                f"Peak Pop.: ~{gr['peak_pop']:,}<br>"
                f"From: {html.escape(gr['origin_regions'])}<br><br>"
                f"{html.escape(gr['desc'])}</div>",
                max_width=320,
            ),
        ).add_to(m)
        # Gold icon label
        folium.Marker(
            location=[gr["lat"], gr["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;color:{gr["color"]};font-weight:bold;'
                     f'text-shadow:0 0 3px #000;">{html.escape(str(gr["year"]))}</div>',
                icon_size=(40, 15),
                icon_anchor=(20, -10),
            ),
        ).add_to(m)
    return m


def _build_immigration_map():
    """Build modern immigration hotspots map."""
    m = _base_map(center=[25, 40], zoom=2)
    for c in IMMIGRATION_HOTSPOTS:
        radius = max(4, min(16, c["imm_pct"] / 5))
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=radius,
            color=c["color"],
            fill=True,
            fill_opacity=0.7,
            tooltip=html.escape(
                f"{c['country']}: {c['imm_pct']}% immigrants"
            ),
            popup=folium.Popup(
                f"<div style='min-width:180px'>"
                f"<b>{html.escape(c['country'])}</b><br>"
                f"Immigrant %: <b>{c['imm_pct']}%</b><br>"
                f"Population: {c['pop']:,}</div>",
                max_width=280,
            ),
        ).add_to(m)
    return m


def _build_climate_map(severity_filter):
    """Build climate migration projection map."""
    m = _base_map(center=[15, 50], zoom=2)
    filtered = [c for c in CLIMATE_RISKS
                if severity_filter == "All" or c["severity"] == severity_filter]
    for cr in filtered:
        radius = max(5, min(15, cr["pop_affected"] / 3000000))
        folium.CircleMarker(
            location=[cr["lat"], cr["lon"]],
            radius=radius,
            color=cr["color"],
            fill=True,
            fill_opacity=0.75,
            tooltip=html.escape(
                f"{cr['city']}: {cr['risk']} ({cr['severity']})"
            ),
            popup=folium.Popup(
                f"<div style='min-width:220px'>"
                f"<b>{html.escape(cr['city'])}</b><br>"
                f"Risk: {html.escape(cr['risk'])}<br>"
                f"Severity: <b>{html.escape(cr['severity'])}</b><br>"
                f"Pop. Affected: {cr['pop_affected']:,}<br>"
                f"Projection: {html.escape(cr['projection'])}</div>",
                max_width=320,
            ),
        ).add_to(m)
        # Pulse ring for critical
        if cr["severity"] == "Critical":
            folium.Circle(
                location=[cr["lat"], cr["lon"]],
                radius=80000,
                color=cr["color"],
                weight=1,
                fill=True,
                fill_opacity=0.12,
            ).add_to(m)
    return m, filtered


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_migration_maps_tab():
    """Render the Migration & Diaspora Maps tab."""

    st.markdown(
        '<div class="tab-header pink">'
        "<h4>Migration &amp; Diaspora Maps</h4>"
        "<p>Explore human migration patterns, diaspora communities, refugee flows, "
        "trade networks, and climate displacement projections across history</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    MAP_MODES = [
        "Human Migration Routes",
        "Modern Refugee Flows",
        "Great Diasporas",
        "Colonial Migration Patterns",
        "Silk Road Network",
        "Age of Exploration Voyages",
        "Transatlantic Slave Trade Routes",
        "Gold Rush Migrations",
        "Modern Immigration Hotspots",
        "Climate Migration Projections",
    ]

    selected_mode = st.selectbox(
        "Select Map Mode", MAP_MODES, key="migration_mode_select"
    )

    st.markdown("---")

    # =================================================================
    # 1. HUMAN MIGRATION ROUTES
    # =================================================================
    if selected_mode == "Human Migration Routes":
        st.markdown(
            "<p style='color:#8b97b0;'>Major prehistoric human migration routes out of Africa, "
            "across continents, including the Bering land bridge crossing and Polynesian expansion.</p>",
            unsafe_allow_html=True,
        )

        route_names = [r["name"] for r in HUMAN_MIGRATION_ROUTES]
        selected_routes = st.multiselect(
            "Select Routes to Display",
            route_names,
            default=route_names,
            key="hmr_routes",
        )

        if not selected_routes:
            st.info("Select at least one migration route to display.")
            return

        # Stats row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Routes Shown", len(selected_routes))
        c2.metric("Total Routes", len(HUMAN_MIGRATION_ROUTES))
        c3.metric("Earliest", "~70,000 BP")
        c4.metric("Latest", "~3,000 BP")

        # Map
        fmap = _build_human_migration_map(selected_routes)
        components.html(fmap._repr_html_(), height=550)

        # Legend
        legend_html = " &nbsp; ".join([
            f'<span style="color:{r["color"]};font-size:0.85rem;">&#9679; {html.escape(r["name"])}</span>'
            for r in HUMAN_MIGRATION_ROUTES if r["name"] in selected_routes
        ])
        st.markdown(
            f"<div style='background:#111827;padding:8px 12px;border-radius:6px;"
            f"border:1px solid #2a3550;margin-top:4px;'>{legend_html}</div>",
            unsafe_allow_html=True,
        )

        # Chart
        st.subheader("Migration Timeline")
        fig, ax = _dark_fig(figsize=(10, 4))
        sel_routes = [r for r in HUMAN_MIGRATION_ROUTES if r["name"] in selected_routes]
        names = [r["name"] for r in sel_routes]
        periods = [r["period"] for r in sel_routes]
        colors = [r["color"] for r in sel_routes]
        # Extract numeric BP values
        bp_vals = []
        for p in periods:
            val = p.replace("~", "").replace(",", "").strip().split()[0]
            try:
                bp_vals.append(int(val))
            except ValueError:
                bp_vals.append(0)
        ax.barh(names, bp_vals, color=colors, edgecolor=_BORDER)
        ax.set_xlabel("Years Before Present (approx.)")
        ax.set_title("Human Migration Timeline")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Dataframe
        df = pd.DataFrame([
            {"Route": r["name"], "Period": r["period"], "Description": r["desc"]}
            for r in HUMAN_MIGRATION_ROUTES if r["name"] in selected_routes
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Migration Routes CSV", csv,
            "human_migration_routes.csv", "text/csv",
            key="dl_hmr",
        )

    # =================================================================
    # 2. MODERN REFUGEE FLOWS
    # =================================================================
    elif selected_mode == "Modern Refugee Flows":
        st.markdown(
            "<p style='color:#8b97b0;'>Major contemporary refugee and displacement flows worldwide. "
            "Line thickness represents number of displaced people.</p>",
            unsafe_allow_html=True,
        )

        origins = ["All"] + sorted(set(r["origin"] for r in REFUGEE_FLOWS))
        origin_filter = st.selectbox(
            "Filter by Origin Country", origins, key="refugee_origin"
        )

        # Stats row
        filtered = [r for r in REFUGEE_FLOWS if origin_filter == "All" or r["origin"] == origin_filter]
        total_people = sum(r["people"] for r in filtered)
        unique_origins = len(set(r["origin"] for r in filtered))
        unique_dests = len(set(r["dest"] for r in filtered))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flows Shown", len(filtered))
        c2.metric("Total Displaced", f"{total_people:,}")
        c3.metric("Origin Countries", unique_origins)
        c4.metric("Host Countries", unique_dests)

        fmap, _ = _build_refugee_map(origin_filter)
        components.html(fmap._repr_html_(), height=550)

        # Chart - top flows
        st.subheader("Top Refugee Flows by Population")
        fig, ax = _dark_fig(figsize=(10, 5))
        sorted_flows = sorted(filtered, key=lambda x: x["people"], reverse=True)[:12]
        labels = [f"{f['origin']} -> {f['dest']}" for f in sorted_flows]
        values = [f["people"] for f in sorted_flows]
        colors = [f["color"] for f in sorted_flows]
        ax.barh(labels, values, color=colors, edgecolor=_BORDER)
        ax.set_xlabel("Number of Refugees")
        ax.set_title("Major Refugee Flows (2023 estimates)")
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {
                "Origin": f["origin"],
                "Destination": f["dest"],
                "Refugees": f["people"],
                "Year": f["year"],
            }
            for f in filtered
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Refugee Flows CSV", csv,
            "refugee_flows.csv", "text/csv",
            key="dl_refugee",
        )

    # =================================================================
    # 3. GREAT DIASPORAS
    # =================================================================
    elif selected_mode == "Great Diasporas":
        st.markdown(
            "<p style='color:#8b97b0;'>Major historical diasporas showing the global spread of "
            "displaced communities. Circle size indicates estimated population.</p>",
            unsafe_allow_html=True,
        )

        dia_names = [d["name"] for d in GREAT_DIASPORAS]
        selected_dias = st.multiselect(
            "Select Diasporas to Display",
            dia_names,
            default=dia_names[:3],
            key="diaspora_select",
        )

        if not selected_dias:
            st.info("Select at least one diaspora to display.")
            return

        # Stats
        sel_data = [d for d in GREAT_DIASPORAS if d["name"] in selected_dias]
        total_comms = sum(len(d["communities"]) for d in sel_data)
        total_pop = sum(c["pop"] for d in sel_data for c in d["communities"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Diasporas Shown", len(selected_dias))
        c2.metric("Communities", total_comms)
        c3.metric("Total Diaspora Pop.", f"{total_pop:,}")

        fmap = _build_diaspora_map(selected_dias)
        components.html(fmap._repr_html_(), height=550)

        # Legend
        legend_html = " &nbsp; ".join([
            f'<span style="color:{d["color"]};font-size:0.85rem;">&#9679; {html.escape(d["name"])}</span>'
            for d in GREAT_DIASPORAS if d["name"] in selected_dias
        ])
        st.markdown(
            f"<div style='background:#111827;padding:8px 12px;border-radius:6px;"
            f"border:1px solid #2a3550;margin-top:4px;'>{legend_html}</div>",
            unsafe_allow_html=True,
        )

        # Chart - population by community
        st.subheader("Diaspora Population by City")
        fig, ax = _dark_fig(figsize=(10, 6))
        all_comms = []
        for d in sel_data:
            for c in d["communities"]:
                all_comms.append({
                    "label": f"{c['city']} ({d['name'][:10]})",
                    "pop": c["pop"],
                    "color": d["color"],
                })
        all_comms.sort(key=lambda x: x["pop"], reverse=True)
        top_comms = all_comms[:15]
        ax.barh(
            [c["label"] for c in top_comms],
            [c["pop"] for c in top_comms],
            color=[c["color"] for c in top_comms],
            edgecolor=_BORDER,
        )
        ax.set_xlabel("Estimated Diaspora Population")
        ax.set_title("Largest Diaspora Communities")
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        rows = []
        for d in sel_data:
            for c in d["communities"]:
                rows.append({
                    "Diaspora": d["name"],
                    "City": c["city"],
                    "Population": c["pop"],
                    "Period": d["period"],
                    "Origin": d["origin"],
                })
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Diasporas CSV", csv,
            "great_diasporas.csv", "text/csv",
            key="dl_diaspora",
        )

    # =================================================================
    # 4. COLONIAL MIGRATION PATTERNS
    # =================================================================
    elif selected_mode == "Colonial Migration Patterns":
        st.markdown(
            "<p style='color:#8b97b0;'>European colonial migration and imperial expansion routes "
            "from the 15th to 20th centuries.</p>",
            unsafe_allow_html=True,
        )

        route_names = [r["name"] for r in COLONIAL_ROUTES]
        selected_col = st.multiselect(
            "Select Colonial Routes",
            route_names,
            default=route_names[:5],
            key="colonial_select",
        )

        if not selected_col:
            st.info("Select at least one colonial route to display.")
            return

        sel_data = [r for r in COLONIAL_ROUTES if r["name"] in selected_col]

        c1, c2, c3 = st.columns(3)
        c1.metric("Routes Shown", len(selected_col))
        c2.metric("Earliest", "1492")
        c3.metric("Latest", "1949")

        fmap = _build_colonial_map(selected_col)
        components.html(fmap._repr_html_(), height=550)

        # Legend
        legend_html = " &nbsp; ".join([
            f'<span style="color:{r["color"]};font-size:0.85rem;">&#9679; {html.escape(r["name"])}</span>'
            for r in sel_data
        ])
        st.markdown(
            f"<div style='background:#111827;padding:8px 12px;border-radius:6px;"
            f"border:1px solid #2a3550;margin-top:4px;'>{legend_html}</div>",
            unsafe_allow_html=True,
        )

        # Timeline chart
        st.subheader("Colonial Timeline")
        fig, ax = _dark_fig(figsize=(10, 5))
        for i, r in enumerate(sel_data):
            parts = r["period"].split("-")
            start_yr = int(parts[0])
            end_yr = int(parts[1])
            ax.barh(
                r["name"], end_yr - start_yr, left=start_yr,
                color=r["color"], edgecolor=_BORDER, height=0.6,
            )
        ax.set_xlabel("Year")
        ax.set_title("Colonial Periods")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {
                "Route": r["name"],
                "Period": r["period"],
                "Description": r["desc"],
            }
            for r in sel_data
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Colonial Routes CSV", csv,
            "colonial_routes.csv", "text/csv",
            key="migm_dl_colonial",
        )

    # =================================================================
    # 5. SILK ROAD NETWORK
    # =================================================================
    elif selected_mode == "Silk Road Network":
        st.markdown(
            "<p style='color:#8b97b0;'>The historical Silk Road network connecting East Asia to "
            "the Mediterranean, with major cities, caravanserais, and trade hubs.</p>",
            unsafe_allow_html=True,
        )

        show_maritime = st.checkbox(
            "Show Maritime Silk Road", value=True, key="silk_maritime"
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cities Mapped", len(SILK_ROAD_CITIES))
        c2.metric("Land Routes", 2)
        c3.metric("Maritime Routes", 1 if show_maritime else 0)
        c4.metric("Span", "~8,000 km")

        fmap = _build_silk_road_map(show_maritime)
        components.html(fmap._repr_html_(), height=550)

        # Route legend
        route_legend = " &nbsp; ".join([
            f'<span style="color:{r["color"]};font-size:0.85rem;">&#9679; {html.escape(r["name"])}</span>'
            for r in SILK_ROAD_ROUTES
            if show_maritime or r["name"] != "Maritime Route"
        ])
        st.markdown(
            f"<div style='background:#111827;padding:8px 12px;border-radius:6px;"
            f"border:1px solid #2a3550;margin-top:4px;'>{route_legend}</div>",
            unsafe_allow_html=True,
        )

        # Chart - cities by longitude (west to east)
        st.subheader("Cities Along the Silk Road (West to East)")
        fig, ax = _dark_fig(figsize=(12, 6))
        sorted_cities = sorted(SILK_ROAD_CITIES, key=lambda c: c["lon"])
        ax.scatter(
            [c["lon"] for c in sorted_cities],
            [c["lat"] for c in sorted_cities],
            c="#f59e0b", s=40, edgecolors=_BORDER, zorder=3,
        )
        for c in sorted_cities[::3]:
            ax.annotate(
                c["city"][:15], (c["lon"], c["lat"]),
                fontsize=6, color=_TEXT2, xytext=(5, 5),
                textcoords="offset points",
            )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("Silk Road City Locations")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {
                "City": c["city"],
                "Latitude": c["lat"],
                "Longitude": c["lon"],
                "Role": c["role"],
                "Era": c["era"],
            }
            for c in SILK_ROAD_CITIES
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Silk Road Cities CSV", csv,
            "silk_road_cities.csv", "text/csv",
            key="dl_silk",
        )

    # =================================================================
    # 6. AGE OF EXPLORATION VOYAGES
    # =================================================================
    elif selected_mode == "Age of Exploration Voyages":
        st.markdown(
            "<p style='color:#8b97b0;'>Famous voyages of exploration from the 15th to 18th centuries, "
            "including Columbus, Magellan, Vasco da Gama, Cook, and Zheng He.</p>",
            unsafe_allow_html=True,
        )

        voyage_names = [v["name"] for v in EXPLORATION_VOYAGES]
        selected_voyages = st.multiselect(
            "Select Voyages to Display",
            voyage_names,
            default=voyage_names[:4],
            key="exploration_select",
        )

        if not selected_voyages:
            st.info("Select at least one voyage to display.")
            return

        sel_data = [v for v in EXPLORATION_VOYAGES if v["name"] in selected_voyages]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Voyages Shown", len(selected_voyages))
        c2.metric("Earliest", min(v["year"] for v in sel_data))
        c3.metric("Latest", max(v["year"] for v in sel_data))
        c4.metric("Sponsors", len(set(v["sponsor"] for v in sel_data)))

        fmap = _build_exploration_map(selected_voyages)
        components.html(fmap._repr_html_(), height=550)

        # Legend
        legend_html = " &nbsp; ".join([
            f'<span style="color:{v["color"]};font-size:0.85rem;">&#9679; {html.escape(v["name"])}</span>'
            for v in sel_data
        ])
        st.markdown(
            f"<div style='background:#111827;padding:8px 12px;border-radius:6px;"
            f"border:1px solid #2a3550;margin-top:4px;'>{legend_html}</div>",
            unsafe_allow_html=True,
        )

        # Timeline chart
        st.subheader("Exploration Timeline")
        fig, ax = _dark_fig(figsize=(10, 4))
        names = [v["name"] for v in sel_data]
        years = [v["year"] for v in sel_data]
        colors = [v["color"] for v in sel_data]
        ax.barh(names, years, color=colors, edgecolor=_BORDER)
        ax.set_xlabel("Year")
        ax.set_title("Age of Exploration Voyages")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {
                "Voyage": v["name"],
                "Explorer": v["explorer"],
                "Year": v["year"],
                "Sponsor": v["sponsor"],
                "Description": v["desc"],
            }
            for v in sel_data
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Exploration Voyages CSV", csv,
            "exploration_voyages.csv", "text/csv",
            key="dl_explore",
        )

    # =================================================================
    # 7. TRANSATLANTIC SLAVE TRADE ROUTES
    # =================================================================
    elif selected_mode == "Transatlantic Slave Trade Routes":
        st.markdown(
            "<p style='color:#8b97b0;'>Major routes of the transatlantic slave trade from the 16th to "
            "19th centuries. Line thickness represents number of people transported. "
            "Data based on the Trans-Atlantic Slave Trade Database estimates.</p>",
            unsafe_allow_html=True,
        )

        route_names = [r["name"] for r in SLAVE_TRADE_ROUTES]
        selected_str = st.multiselect(
            "Select Trade Routes",
            route_names,
            default=route_names,
            key="slave_trade_select",
        )

        if not selected_str:
            st.info("Select at least one route to display.")
            return

        sel_data = [r for r in SLAVE_TRADE_ROUTES if r["name"] in selected_str]
        total_embarked = sum(r["embarked"] for r in sel_data)
        total_disembarked = sum(r["disembarked"] for r in sel_data)
        mortality = total_embarked - total_disembarked

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Routes Shown", len(selected_str))
        c2.metric("Total Embarked", f"{total_embarked:,}")
        c3.metric("Total Disembarked", f"{total_disembarked:,}")
        c4.metric("Mortality in Transit", f"{mortality:,}")

        fmap = _build_slave_trade_map(selected_str)
        components.html(fmap._repr_html_(), height=550)

        # Chart
        st.subheader("Embarked vs Disembarked by Route")
        fig, ax = _dark_fig(figsize=(10, 5))
        short_names = [r["name"].replace("West Africa to ", "") for r in sel_data]
        x_pos = range(len(sel_data))
        bar_width = 0.35
        embarked_vals = [r["embarked"] for r in sel_data]
        disembarked_vals = [r["disembarked"] for r in sel_data]
        bars1 = ax.bar(
            [p - bar_width / 2 for p in x_pos], embarked_vals,
            bar_width, label="Embarked", color="#dc2626", edgecolor=_BORDER,
        )
        bars2 = ax.bar(
            [p + bar_width / 2 for p in x_pos], disembarked_vals,
            bar_width, label="Disembarked", color="#f97316", edgecolor=_BORDER,
        )
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(short_names, rotation=30, ha="right", fontsize=7)
        ax.set_ylabel("Number of People")
        ax.set_title("Transatlantic Slave Trade by Route")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
        ax.legend(facecolor=_SURFACE, edgecolor=_BORDER, labelcolor=_TEXT2)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {
                "Route": r["name"],
                "Origin": r["origin"],
                "Destination": r["dest"],
                "Embarked": r["embarked"],
                "Disembarked": r["disembarked"],
                "Mortality": r["embarked"] - r["disembarked"],
                "Period": r["period"],
            }
            for r in sel_data
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Slave Trade Data CSV", csv,
            "slave_trade_routes.csv", "text/csv",
            key="dl_slave",
        )

    # =================================================================
    # 8. GOLD RUSH MIGRATIONS
    # =================================================================
    elif selected_mode == "Gold Rush Migrations":
        st.markdown(
            "<p style='color:#8b97b0;'>Major gold rush events that triggered massive population "
            "movements across the globe from the 17th to early 20th century.</p>",
            unsafe_allow_html=True,
        )

        sort_by = st.selectbox(
            "Sort By", ["Year", "Peak Population", "Name"], key="gold_sort"
        )

        sorted_rushes = list(GOLD_RUSHES)
        if sort_by == "Year":
            sorted_rushes.sort(key=lambda x: x["year"])
        elif sort_by == "Peak Population":
            sorted_rushes.sort(key=lambda x: x["peak_pop"], reverse=True)
        else:
            sorted_rushes.sort(key=lambda x: x["name"])

        total_pop = sum(g["peak_pop"] for g in GOLD_RUSHES)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gold Rushes", len(GOLD_RUSHES))
        c2.metric("Total Migrants", f"~{total_pop:,}")
        c3.metric("Earliest", "1693")
        c4.metric("Latest", "1899")

        fmap = _build_gold_rush_map()
        components.html(fmap._repr_html_(), height=550)

        # Chart
        st.subheader("Peak Population by Gold Rush")
        fig, ax = _dark_fig(figsize=(10, 4))
        names = [g["name"] for g in sorted_rushes]
        pops = [g["peak_pop"] for g in sorted_rushes]
        colors = [g["color"] for g in sorted_rushes]
        ax.barh(names, pops, color=colors, edgecolor=_BORDER)
        ax.set_xlabel("Estimated Peak Population Influx")
        ax.set_title("Gold Rush Population Movements")
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e3:.0f}K"))
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {
                "Name": g["name"],
                "Year": g["year"],
                "Period": g["period"],
                "Peak Population": g["peak_pop"],
                "Origin Regions": g["origin_regions"],
                "Description": g["desc"],
            }
            for g in sorted_rushes
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Gold Rush Data CSV", csv,
            "gold_rush_migrations.csv", "text/csv",
            key="dl_gold",
        )

    # =================================================================
    # 9. MODERN IMMIGRATION HOTSPOTS
    # =================================================================
    elif selected_mode == "Modern Immigration Hotspots":
        st.markdown(
            "<p style='color:#8b97b0;'>Countries ranked by immigrant population percentage. "
            "Combines hardcoded UN migration data with REST Countries API for context. "
            "Circle size indicates immigrant share of population.</p>",
            unsafe_allow_html=True,
        )

        min_pct = st.slider(
            "Minimum Immigrant %", 0, 80, 10, key="imm_min_pct"
        )

        filtered = [c for c in IMMIGRATION_HOTSPOTS if c["imm_pct"] >= min_pct]

        # Try enrichment from REST Countries
        rest_data = _fetch_rest_countries()
        rest_map = {}
        if rest_data:
            for item in rest_data:
                name = item.get("name", {}).get("common", "")
                rest_map[name] = {
                    "region": item.get("region", ""),
                    "subregion": item.get("subregion", ""),
                }

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Countries Shown", len(filtered))
        c2.metric("Highest %", f"{max(c['imm_pct'] for c in filtered):.1f}%" if filtered else "N/A")
        avg_pct = sum(c["imm_pct"] for c in filtered) / len(filtered) if filtered else 0
        c3.metric("Average %", f"{avg_pct:.1f}%")
        total_imm_pop = sum(int(c["pop"] * c["imm_pct"] / 100) for c in filtered)
        c4.metric("Total Immigrants", f"{total_imm_pop:,}")

        if not filtered:
            st.warning("No countries match the minimum percentage filter.")
            return

        fmap = _build_immigration_map()
        components.html(fmap._repr_html_(), height=550)

        # Chart
        st.subheader("Countries by Immigrant Percentage")
        fig, ax = _dark_fig(figsize=(10, 6))
        sorted_imm = sorted(filtered, key=lambda x: x["imm_pct"], reverse=True)
        names = [c["country"] for c in sorted_imm]
        pcts = [c["imm_pct"] for c in sorted_imm]
        colors = [c["color"] for c in sorted_imm]
        ax.barh(names, pcts, color=colors, edgecolor=_BORDER)
        ax.set_xlabel("Immigrant Population (%)")
        ax.set_title("Countries by Immigration Rate")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        rows = []
        for c in sorted_imm:
            region = rest_map.get(c["country"], {}).get("region", "")
            subregion = rest_map.get(c["country"], {}).get("subregion", "")
            rows.append({
                "Country": c["country"],
                "Immigrant %": c["imm_pct"],
                "Population": c["pop"],
                "Est. Immigrants": int(c["pop"] * c["imm_pct"] / 100),
                "Region": region,
                "Subregion": subregion,
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Immigration Data CSV", csv,
            "immigration_hotspots.csv", "text/csv",
            key="dl_imm",
        )

    # =================================================================
    # 10. CLIMATE MIGRATION PROJECTIONS
    # =================================================================
    elif selected_mode == "Climate Migration Projections":
        st.markdown(
            "<p style='color:#8b97b0;'>Areas at greatest risk of climate-driven displacement, "
            "including coastal cities threatened by sea level rise, drought-prone regions, "
            "and small island states facing submersion. Based on IPCC and World Bank projections.</p>",
            unsafe_allow_html=True,
        )

        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All", "Critical", "High", "Moderate"],
            key="climate_severity",
        )

        filtered = [c for c in CLIMATE_RISKS
                     if severity_filter == "All" or c["severity"] == severity_filter]
        total_affected = sum(c["pop_affected"] for c in filtered)
        critical_count = sum(1 for c in filtered if c["severity"] == "Critical")
        high_count = sum(1 for c in filtered if c["severity"] == "High")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations Shown", len(filtered))
        c2.metric("Pop. at Risk", f"{total_affected:,}")
        c3.metric("Critical Zones", critical_count)
        c4.metric("High Risk Zones", high_count)

        if not filtered:
            st.warning("No locations match the severity filter.")
            return

        fmap, _ = _build_climate_map(severity_filter)
        components.html(fmap._repr_html_(), height=550)

        # Severity legend
        sev_legend = (
            '<span style="color:#ef4444;">&#9679; Critical</span> &nbsp; '
            '<span style="color:#f97316;">&#9679; High</span> &nbsp; '
            '<span style="color:#eab308;">&#9679; Moderate</span>'
        )
        st.markdown(
            f"<div style='background:#111827;padding:8px 12px;border-radius:6px;"
            f"border:1px solid #2a3550;margin-top:4px;'>{sev_legend}</div>",
            unsafe_allow_html=True,
        )

        # Chart - population at risk
        st.subheader("Population at Risk by Location")
        fig, ax = _dark_fig(figsize=(10, 6))
        sorted_risks = sorted(filtered, key=lambda x: x["pop_affected"], reverse=True)[:15]
        names = [r["city"] for r in sorted_risks]
        pops = [r["pop_affected"] for r in sorted_risks]
        colors = [r["color"] for r in sorted_risks]
        ax.barh(names, pops, color=colors, edgecolor=_BORDER)
        ax.set_xlabel("Population at Risk")
        ax.set_title("Climate Displacement Risk (Projected)")
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Risk type pie chart
        st.subheader("Risk Types Distribution")
        risk_types = {}
        for c in filtered:
            rtype = c["risk"].split(" + ")[0].split(" / ")[0].strip()
            risk_types[rtype] = risk_types.get(rtype, 0) + 1
        fig2, ax2 = plt.subplots(figsize=(6, 6))
        fig2.patch.set_facecolor(_BG)
        ax2.set_facecolor(_SURFACE)
        pie_colors = ["#ef4444", "#f97316", "#eab308", "#10b981", "#3b82f6",
                       "#8b5cf6", "#ec4899", "#06b6d4"]
        wedges, texts, autotexts = ax2.pie(
            risk_types.values(),
            labels=risk_types.keys(),
            autopct="%1.0f%%",
            colors=pie_colors[:len(risk_types)],
            textprops={"color": _TEXT, "fontsize": 8},
        )
        for t in autotexts:
            t.set_color(_TEXT)
            t.set_fontsize(7)
        ax2.set_title("Climate Risk Types", color=_TEXT)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

        df = pd.DataFrame([
            {
                "Location": c["city"],
                "Risk": c["risk"],
                "Severity": c["severity"],
                "Pop. Affected": c["pop_affected"],
                "Projection": c["projection"],
                "Lat": c["lat"],
                "Lon": c["lon"],
            }
            for c in filtered
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Climate Risk Data CSV", csv,
            "climate_migration_risks.csv", "text/csv",
            key="dl_climate",
        )
