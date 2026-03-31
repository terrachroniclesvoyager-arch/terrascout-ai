"""
Civilization & Culture Maps module for TerraScout AI.
Creates composite maps about human civilization, culture, and development.
Includes hardcoded historical data and API integrations (REST Countries,
Overpass, World Bank) for 10 thematic map types.
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
# 1. ORIGINS OF AGRICULTURE DATA
# =====================================================================
AGRICULTURE_ORIGINS = [
    {
        "name": "Fertile Crescent",
        "date": "~10,000 BC",
        "year": -10000,
        "crops": "Wheat, Barley, Lentils, Peas",
        "color": "#f59e0b",
        "center": [34.0, 42.0],
        "polygon": [
            [31.0, 34.0], [33.0, 36.0], [36.0, 37.0], [37.5, 39.0],
            [37.0, 42.0], [36.0, 44.0], [34.0, 46.0], [32.0, 47.0],
            [30.5, 47.5], [29.5, 46.0], [31.0, 44.0], [30.5, 42.0],
            [30.0, 38.0], [30.5, 35.0], [31.0, 34.0],
        ],
    },
    {
        "name": "Yellow River, China",
        "date": "~8,000 BC",
        "year": -8000,
        "crops": "Rice, Millet, Soybeans",
        "color": "#ef4444",
        "center": [35.0, 110.0],
        "polygon": [
            [33.0, 105.0], [35.0, 104.0], [37.0, 107.0], [38.0, 110.0],
            [37.5, 114.0], [36.0, 117.0], [34.0, 118.0], [32.0, 117.0],
            [31.0, 114.0], [32.0, 110.0], [32.0, 107.0], [33.0, 105.0],
        ],
    },
    {
        "name": "Mesoamerica",
        "date": "~7,000 BC",
        "year": -7000,
        "crops": "Maize, Squash, Beans, Cacao",
        "color": "#10b981",
        "center": [18.0, -97.0],
        "polygon": [
            [14.0, -93.0], [16.0, -91.0], [18.0, -92.0], [20.0, -97.0],
            [21.0, -100.0], [20.0, -103.0], [18.0, -103.0], [16.0, -99.0],
            [15.0, -96.0], [14.0, -93.0],
        ],
    },
    {
        "name": "Papua New Guinea",
        "date": "~7,000 BC",
        "year": -7000,
        "crops": "Taro, Yams, Bananas, Sugar Cane",
        "color": "#8b5cf6",
        "center": [-5.5, 144.0],
        "polygon": [
            [-3.0, 141.0], [-2.5, 144.0], [-4.0, 147.0], [-5.5, 149.0],
            [-7.0, 148.0], [-8.5, 147.0], [-9.0, 144.0], [-8.0, 142.0],
            [-6.0, 141.0], [-3.0, 141.0],
        ],
    },
    {
        "name": "Andes (South America)",
        "date": "~5,000 BC",
        "year": -5000,
        "crops": "Potato, Quinoa, Llama domestication",
        "color": "#06b6d4",
        "center": [-15.0, -72.0],
        "polygon": [
            [-5.0, -78.0], [-4.0, -76.0], [-8.0, -74.0], [-12.0, -73.0],
            [-16.0, -70.0], [-20.0, -68.0], [-22.0, -67.0], [-22.0, -69.0],
            [-18.0, -72.0], [-14.0, -76.0], [-8.0, -78.0], [-5.0, -78.0],
        ],
    },
    {
        "name": "Sahel, Africa",
        "date": "~5,000 BC",
        "year": -5000,
        "crops": "Sorghum, Pearl Millet, African Rice",
        "color": "#ec4899",
        "center": [14.0, 0.0],
        "polygon": [
            [12.0, -15.0], [14.0, -10.0], [15.0, -5.0], [16.0, 0.0],
            [16.0, 10.0], [15.0, 15.0], [14.0, 20.0], [13.0, 20.0],
            [12.0, 15.0], [12.0, 10.0], [13.0, 5.0], [13.0, 0.0],
            [12.0, -5.0], [11.0, -10.0], [12.0, -15.0],
        ],
    },
    {
        "name": "Eastern North America",
        "date": "~3,000 BC",
        "year": -3000,
        "crops": "Sunflower, Goosefoot, Sumpweed",
        "color": "#a855f7",
        "center": [37.0, -87.0],
        "polygon": [
            [34.0, -92.0], [36.0, -93.0], [39.0, -92.0], [41.0, -89.0],
            [41.0, -85.0], [39.0, -82.0], [37.0, -81.0], [35.0, -83.0],
            [34.0, -87.0], [34.0, -92.0],
        ],
    },
]

# =====================================================================
# 2. ANCIENT CIVILIZATIONS DATA
# =====================================================================
ANCIENT_CIVILIZATIONS = [
    {
        "name": "Mesopotamia",
        "start": -3500, "end": -539,
        "capital": "Babylon / Ur",
        "achievements": "Cuneiform writing, Code of Hammurabi, Ziggurat architecture",
        "color": "#f59e0b",
        "polygon": [
            [29.5, 44.0], [31.0, 43.0], [33.0, 42.0], [35.0, 42.5],
            [36.5, 43.0], [37.0, 44.5], [36.0, 46.0], [34.0, 47.0],
            [32.0, 48.0], [30.0, 48.0], [29.5, 47.0], [29.5, 44.0],
        ],
    },
    {
        "name": "Ancient Egypt",
        "start": -3100, "end": -30,
        "capital": "Memphis / Thebes",
        "achievements": "Pyramids, Hieroglyphics, Papyrus, Medicine",
        "color": "#ef4444",
        "polygon": [
            [31.5, 25.0], [31.5, 32.0], [30.0, 33.0], [27.0, 33.5],
            [24.0, 33.0], [22.0, 32.0], [22.0, 30.0], [24.0, 29.0],
            [27.0, 28.0], [30.0, 27.0], [31.5, 25.0],
        ],
    },
    {
        "name": "Indus Valley",
        "start": -3300, "end": -1300,
        "capital": "Mohenjo-daro / Harappa",
        "achievements": "Urban planning, Sanitation, Standardized weights",
        "color": "#10b981",
        "polygon": [
            [28.0, 66.0], [30.0, 68.0], [32.0, 72.0], [33.0, 75.0],
            [30.0, 76.0], [27.0, 73.0], [25.0, 70.0], [24.0, 68.0],
            [25.0, 66.0], [28.0, 66.0],
        ],
    },
    {
        "name": "Shang Dynasty",
        "start": -1600, "end": -1046,
        "capital": "Yin (Anyang)",
        "achievements": "Oracle bones, Bronze casting, Chinese writing",
        "color": "#dc2626",
        "polygon": [
            [32.0, 110.0], [34.0, 108.0], [36.0, 110.0], [37.0, 113.0],
            [37.0, 116.0], [35.0, 117.0], [33.0, 116.0], [32.0, 113.0],
            [32.0, 110.0],
        ],
    },
    {
        "name": "Minoan Civilization",
        "start": -2700, "end": -1450,
        "capital": "Knossos (Crete)",
        "achievements": "Palace complexes, Linear A script, Maritime trade",
        "color": "#06b6d4",
        "polygon": [
            [35.6, 23.5], [35.6, 26.3], [35.0, 26.3], [34.9, 23.5], [35.6, 23.5],
        ],
    },
    {
        "name": "Maya Civilization",
        "start": -2000, "end": 900,
        "capital": "Tikal / Calakmul",
        "achievements": "Calendar, Astronomy, Hieroglyphic writing, Pyramids",
        "color": "#8b5cf6",
        "polygon": [
            [14.5, -92.0], [17.0, -92.0], [18.5, -91.0], [21.0, -88.0],
            [21.0, -86.5], [18.0, -87.5], [15.0, -89.0], [14.5, -92.0],
        ],
    },
    {
        "name": "Olmec Civilization",
        "start": -1500, "end": -400,
        "capital": "San Lorenzo / La Venta",
        "achievements": "Colossal heads, Rubber ball game, Early writing",
        "color": "#a855f7",
        "polygon": [
            [17.5, -96.0], [18.5, -95.5], [19.0, -94.0], [18.5, -93.5],
            [17.5, -94.0], [17.0, -95.0], [17.5, -96.0],
        ],
    },
    {
        "name": "Kingdom of Axum",
        "start": -400, "end": 940,
        "capital": "Axum",
        "achievements": "Obelisks, Ge'ez script, Early Christianity in Africa",
        "color": "#ec4899",
        "polygon": [
            [12.0, 37.0], [14.0, 38.0], [16.0, 39.0], [16.0, 42.0],
            [14.0, 43.0], [12.0, 42.0], [11.0, 40.0], [12.0, 37.0],
        ],
    },
    {
        "name": "Carthage",
        "start": -814, "end": -146,
        "capital": "Carthage (Tunisia)",
        "achievements": "Maritime trade empire, Punic Wars, Harbor engineering",
        "color": "#f97316",
        "polygon": [
            [37.0, 9.5], [37.2, 10.5], [36.5, 11.0], [35.0, 10.5],
            [34.0, 9.0], [34.5, 8.0], [36.0, 8.0], [37.0, 9.5],
        ],
    },
    {
        "name": "Persian Empire (Achaemenid)",
        "start": -550, "end": -330,
        "capital": "Persepolis / Susa",
        "achievements": "Royal Road, Postal system, Zoroastrianism, Qanat irrigation",
        "color": "#38bdf8",
        "polygon": [
            [30.0, 44.0], [33.0, 44.0], [37.0, 44.0], [40.0, 50.0],
            [38.0, 56.0], [35.0, 60.0], [30.0, 62.0], [27.0, 58.0],
            [25.0, 55.0], [26.0, 50.0], [28.0, 47.0], [30.0, 44.0],
        ],
    },
    {
        "name": "Roman Empire",
        "start": -509, "end": 476,
        "capital": "Rome",
        "achievements": "Roads, Aqueducts, Law, Concrete, Republic/Empire governance",
        "color": "#ef4444",
        "polygon": [
            [36.0, -5.0], [37.0, 0.0], [43.0, 5.0], [47.0, 7.0],
            [51.0, 1.0], [51.0, 5.0], [48.0, 12.0], [45.0, 15.0],
            [42.0, 20.0], [38.0, 24.0], [35.0, 28.0], [31.0, 32.0],
            [30.0, 30.0], [32.0, 24.0], [32.0, 15.0], [35.0, 10.0],
            [36.0, 5.0], [36.0, -5.0],
        ],
    },
    {
        "name": "Ancient Greece",
        "start": -800, "end": -146,
        "capital": "Athens / Sparta",
        "achievements": "Democracy, Philosophy, Theater, Olympics, Mathematics",
        "color": "#3b82f6",
        "polygon": [
            [36.5, 21.0], [38.0, 20.5], [39.5, 20.0], [41.0, 22.0],
            [41.0, 25.0], [39.0, 26.0], [37.5, 26.0], [36.0, 23.0],
            [36.5, 21.0],
        ],
    },
    {
        "name": "Maurya Empire",
        "start": -322, "end": -185,
        "capital": "Pataliputra",
        "achievements": "Ashoka's edicts, Unified India, Spread of Buddhism",
        "color": "#f59e0b",
        "polygon": [
            [10.0, 73.0], [15.0, 75.0], [20.0, 73.0], [25.0, 70.0],
            [30.0, 72.0], [33.0, 75.0], [30.0, 80.0], [28.0, 85.0],
            [25.0, 88.0], [20.0, 87.0], [15.0, 82.0], [10.0, 78.0],
            [10.0, 73.0],
        ],
    },
    {
        "name": "Han Dynasty",
        "start": -206, "end": 220,
        "capital": "Chang'an / Luoyang",
        "achievements": "Silk Road, Paper invention, Civil service exams",
        "color": "#dc2626",
        "polygon": [
            [22.0, 100.0], [25.0, 98.0], [30.0, 100.0], [35.0, 105.0],
            [40.0, 110.0], [42.0, 115.0], [40.0, 120.0], [35.0, 122.0],
            [30.0, 120.0], [25.0, 115.0], [22.0, 110.0], [22.0, 100.0],
        ],
    },
]

# =====================================================================
# 3. WRITING SYSTEMS DATA
# =====================================================================
WRITING_SYSTEMS = {
    "Latin": {
        "color": "#3b82f6",
        "countries": [
            "US", "GB", "FR", "DE", "IT", "ES", "PT", "NL", "BE", "AT",
            "CH", "SE", "NO", "DK", "FI", "PL", "CZ", "SK", "HR", "SI",
            "RO", "HU", "IE", "IS", "LT", "LV", "EE", "AL", "MT", "LU",
            "BR", "MX", "AR", "CO", "PE", "VE", "CL", "EC", "BO", "PY",
            "UY", "CA", "AU", "NZ", "PH", "ID", "MY", "VN", "TR", "AZ",
            "UZ", "TM", "NG", "KE", "TZ", "ZA", "GH", "CI", "SN", "CM",
        ],
    },
    "Cyrillic": {
        "color": "#8b5cf6",
        "countries": [
            "RU", "UA", "BY", "BG", "RS", "MK", "BA", "ME", "KZ", "KG",
            "TJ", "MN",
        ],
    },
    "Arabic": {
        "color": "#10b981",
        "countries": [
            "SA", "EG", "IQ", "SY", "JO", "LB", "AE", "QA", "BH", "KW",
            "OM", "YE", "LY", "TN", "DZ", "MA", "MR", "SD", "SO", "DJ",
            "IR", "AF", "PK",
        ],
    },
    "Devanagari": {
        "color": "#f59e0b",
        "countries": ["IN", "NP"],
    },
    "Chinese": {
        "color": "#ef4444",
        "countries": ["CN", "TW", "SG"],
    },
    "Japanese (mixed)": {
        "color": "#ec4899",
        "countries": ["JP"],
    },
    "Korean (Hangul)": {
        "color": "#06b6d4",
        "countries": ["KR", "KP"],
    },
    "Thai": {
        "color": "#a855f7",
        "countries": ["TH"],
    },
    "Greek": {
        "color": "#38bdf8",
        "countries": ["GR", "CY"],
    },
    "Hebrew": {
        "color": "#fbbf24",
        "countries": ["IL"],
    },
    "Georgian": {
        "color": "#f97316",
        "countries": ["GE"],
    },
    "Armenian": {
        "color": "#14b8a6",
        "countries": ["AM"],
    },
    "Ethiopic (Ge'ez)": {
        "color": "#d946ef",
        "countries": ["ET", "ER"],
    },
    "Burmese": {
        "color": "#84cc16",
        "countries": ["MM"],
    },
    "Khmer": {
        "color": "#22d3ee",
        "countries": ["KH"],
    },
    "Tamil": {
        "color": "#fb923c",
        "countries": ["LK"],
    },
    "Bengali": {
        "color": "#4ade80",
        "countries": ["BD"],
    },
}

# =====================================================================
# 4. WORLD RELIGIONS DATA
# =====================================================================
RELIGION_DATA = {
    "Catholic": {
        "color": "#3b82f6",
        "countries": [
            "IT", "ES", "PT", "FR", "PL", "IE", "AT", "HR", "SI", "SK",
            "LT", "MT", "LU", "BE", "MX", "BR", "AR", "CO", "PE", "VE",
            "CL", "EC", "BO", "PY", "UY", "CR", "PA", "HN", "SV", "GT",
            "NI", "DO", "CU", "PR", "PH", "TL", "CV", "ST", "AO", "MZ",
            "CG", "CD", "CM", "GA", "GQ", "BI", "RW",
        ],
    },
    "Protestant": {
        "color": "#60a5fa",
        "countries": [
            "US", "GB", "DE", "NL", "CH", "SE", "NO", "DK", "FI", "IS",
            "EE", "LV", "AU", "NZ", "CA", "JM", "TT", "GY", "BZ", "ZA",
            "KE", "TZ", "UG", "GH", "NG", "LR", "ZW", "MW", "ZM", "BW",
            "NA", "LS", "SZ", "FJ", "TO", "WS", "PG",
        ],
    },
    "Orthodox": {
        "color": "#1e3a5f",
        "countries": [
            "RU", "UA", "BY", "GR", "CY", "RS", "MK", "BA", "ME", "BG",
            "RO", "MD", "GE", "AM", "ET",
        ],
    },
    "Sunni Islam": {
        "color": "#10b981",
        "countries": [
            "SA", "EG", "JO", "SY", "IQ", "AE", "QA", "BH", "KW", "OM",
            "YE", "LY", "TN", "DZ", "MA", "MR", "ML", "NE", "TD", "SD",
            "SO", "DJ", "KM", "TR", "AF", "PK", "BD", "ID", "MY", "BN",
            "UZ", "KZ", "KG", "TJ", "TM", "AZ", "SN", "GM", "GN", "SL",
            "BF", "NG",
        ],
    },
    "Shia Islam": {
        "color": "#047857",
        "countries": ["IR", "BH"],
    },
    "Hinduism": {
        "color": "#f97316",
        "countries": ["IN", "NP", "MU"],
    },
    "Buddhism": {
        "color": "#eab308",
        "countries": ["TH", "MM", "KH", "LA", "LK", "BT", "MN", "VN"],
    },
    "Judaism": {
        "color": "#fbbf24",
        "countries": ["IL"],
    },
    "Indigenous / Folk": {
        "color": "#a0522d",
        "countries": ["HT"],
    },
    "Non-religious": {
        "color": "#6b7280",
        "countries": ["CN", "CZ", "EE", "JP", "KR", "KP", "HK"],
    },
}

RELIGION_GLOBAL_PCT = {
    "Christianity": 31.1,
    "Islam": 24.9,
    "Hinduism": 15.2,
    "Buddhism": 6.6,
    "Folk Religions": 5.6,
    "Judaism": 0.2,
    "Other": 0.8,
    "Non-religious": 15.6,
}

# =====================================================================
# 5. LANGUAGE FAMILIES DATA
# =====================================================================
LANGUAGE_FAMILIES = {
    "Indo-European": {
        "color": "#3b82f6",
        "countries": [
            "US", "GB", "FR", "DE", "IT", "ES", "PT", "NL", "BE", "AT",
            "CH", "SE", "NO", "DK", "IS", "IE", "PL", "CZ", "SK", "HR",
            "SI", "RS", "BA", "ME", "MK", "AL", "RO", "MD", "BG", "GR",
            "CY", "RU", "UA", "BY", "LT", "LV", "GE", "AM", "IR", "AF",
            "PK", "IN", "NP", "BD", "LK", "BR", "MX", "AR", "CO", "PE",
            "VE", "CL", "EC", "BO", "PY", "UY", "CA", "AU", "NZ", "ZA",
        ],
    },
    "Sino-Tibetan": {
        "color": "#ef4444",
        "countries": ["CN", "TW", "SG", "MM", "BT"],
    },
    "Niger-Congo": {
        "color": "#10b981",
        "countries": [
            "NG", "GH", "CI", "SN", "CM", "CG", "CD", "AO", "MZ", "TZ",
            "KE", "UG", "RW", "BI", "MW", "ZM", "ZW", "BW", "NA", "LS",
            "SZ", "MG", "ML", "BF", "GN", "SL", "LR", "TG", "BJ", "GA",
            "GQ",
        ],
    },
    "Afro-Asiatic": {
        "color": "#f59e0b",
        "countries": [
            "SA", "EG", "IQ", "SY", "JO", "LB", "AE", "QA", "BH", "KW",
            "OM", "YE", "LY", "TN", "DZ", "MA", "MR", "SD", "SO", "DJ",
            "ET", "ER", "IL", "TD",
        ],
    },
    "Austronesian": {
        "color": "#8b5cf6",
        "countries": ["ID", "MY", "PH", "MG", "FJ", "TO", "WS", "TL", "PG", "NZ"],
    },
    "Turkic": {
        "color": "#06b6d4",
        "countries": ["TR", "AZ", "UZ", "KZ", "KG", "TM"],
    },
    "Dravidian": {
        "color": "#ec4899",
        "countries": [],
    },
    "Japonic": {
        "color": "#f97316",
        "countries": ["JP"],
    },
    "Koreanic": {
        "color": "#38bdf8",
        "countries": ["KR", "KP"],
    },
    "Mongolic": {
        "color": "#a855f7",
        "countries": ["MN"],
    },
    "Uralic": {
        "color": "#14b8a6",
        "countries": ["FI", "HU", "EE"],
    },
    "Tai-Kadai": {
        "color": "#84cc16",
        "countries": ["TH", "LA"],
    },
    "Austroasiatic": {
        "color": "#d946ef",
        "countries": ["VN", "KH"],
    },
}

MOST_SPOKEN_LANGUAGES = {
    "English": 1452,
    "Mandarin Chinese": 1119,
    "Hindi": 602,
    "Spanish": 548,
    "French": 280,
    "Arabic": 274,
    "Bengali": 273,
    "Portuguese": 258,
    "Russian": 258,
    "Japanese": 126,
    "Indonesian": 199,
    "German": 134,
    "Korean": 82,
    "Turkish": 84,
    "Vietnamese": 85,
}

# =====================================================================
# 7. SILK ROAD & TRADE ROUTES DATA
# =====================================================================
TRADE_ROUTES = {
    "Silk Road (Main)": {
        "color": "#f59e0b",
        "goods": "Silk, Spices, Gold, Jade, Porcelain",
        "period": "130 BC - 1450 AD",
        "coords": [
            [34.26, 108.94],  # Xi'an
            [36.06, 103.83],  # Lanzhou
            [39.47, 98.49],   # Jiayuguan
            [40.14, 94.66],   # Dunhuang
            [42.95, 89.19],   # Turpan
            [43.80, 87.60],   # Urumqi
            [42.48, 76.95],   # Bishkek
            [41.31, 69.28],   # Tashkent
            [39.65, 66.96],   # Samarkand
            [37.58, 61.84],   # Merv
            [35.69, 51.39],   # Tehran
            [36.19, 44.01],   # Mosul
            [36.20, 37.13],   # Aleppo
            [33.51, 36.29],   # Damascus
            [41.01, 28.98],   # Constantinople
        ],
        "cities": [
            {"name": "Xi'an (Chang'an)", "lat": 34.26, "lon": 108.94},
            {"name": "Dunhuang", "lat": 40.14, "lon": 94.66},
            {"name": "Samarkand", "lat": 39.65, "lon": 66.96},
            {"name": "Constantinople", "lat": 41.01, "lon": 28.98},
        ],
    },
    "Silk Road (Southern Branch)": {
        "color": "#fbbf24",
        "goods": "Silk, Cotton, Gems, Horses",
        "period": "200 BC - 1400 AD",
        "coords": [
            [40.14, 94.66],   # Dunhuang
            [38.14, 85.53],   # Hotan
            [37.87, 75.99],   # Kashgar
            [36.72, 68.87],   # Balkh
            [34.52, 69.17],   # Kabul
            [33.69, 73.04],   # Islamabad area
            [30.04, 71.68],   # Multan
        ],
        "cities": [
            {"name": "Kashgar", "lat": 37.87, "lon": 75.99},
            {"name": "Balkh", "lat": 36.72, "lon": 68.87},
        ],
    },
    "Trans-Saharan Trade Route": {
        "color": "#ec4899",
        "goods": "Gold, Salt, Slaves, Ivory, Cloth",
        "period": "300 AD - 1600 AD",
        "coords": [
            [13.52, -1.53],   # Ouagadougou
            [12.65, -8.00],   # Bamako
            [16.77, -3.01],   # Timbuktu
            [20.50, -0.05],   # In Salah
            [32.88, 3.00],    # Ghardaia
            [36.37, 3.04],    # Algiers coast
        ],
        "cities": [
            {"name": "Timbuktu", "lat": 16.77, "lon": -3.01},
            {"name": "Sijilmasa", "lat": 31.28, "lon": -4.28},
        ],
    },
    "Spice Trade Route (Maritime)": {
        "color": "#10b981",
        "goods": "Pepper, Cinnamon, Cloves, Nutmeg, Cardamom",
        "period": "300 BC - 1700 AD",
        "coords": [
            [-6.17, 106.85],  # Jakarta
            [1.35, 103.82],   # Singapore
            [10.82, 106.63],  # Ho Chi Minh area
            [13.08, 80.27],   # Chennai
            [9.93, 76.26],    # Kochi
            [12.30, 45.03],   # Aden
            [15.55, 39.45],   # Massawa
            [30.04, 31.24],   # Cairo / Suez
            [41.01, 28.98],   # Constantinople
            [45.44, 12.33],   # Venice
        ],
        "cities": [
            {"name": "Kochi (Calicut)", "lat": 9.93, "lon": 76.26},
            {"name": "Venice", "lat": 45.44, "lon": 12.33},
            {"name": "Malacca", "lat": 2.19, "lon": 102.25},
        ],
    },
    "Incense Route": {
        "color": "#a855f7",
        "goods": "Frankincense, Myrrh, Spices",
        "period": "700 BC - 200 AD",
        "coords": [
            [15.36, 44.21],   # Sana'a
            [12.80, 45.03],   # Aden
            [16.90, 49.82],   # Salalah / Dhofar
            [21.49, 39.19],   # Jeddah
            [24.71, 46.68],   # Riyadh
            [29.56, 35.39],   # Petra
            [31.50, 34.45],   # Gaza
        ],
        "cities": [
            {"name": "Petra", "lat": 29.56, "lon": 35.39},
            {"name": "Salalah (Dhofar)", "lat": 16.90, "lon": 49.82},
        ],
    },
    "Amber Road": {
        "color": "#f97316",
        "goods": "Amber, Furs, Honey, Wax",
        "period": "1600 BC - 500 AD",
        "coords": [
            [54.35, 18.65],   # Gdansk
            [52.23, 21.01],   # Warsaw
            [50.07, 14.44],   # Prague
            [48.21, 16.37],   # Vienna
            [46.05, 14.51],   # Ljubljana
            [45.44, 12.33],   # Venice
            [41.90, 12.50],   # Rome
        ],
        "cities": [
            {"name": "Gdansk (Amber source)", "lat": 54.35, "lon": 18.65},
            {"name": "Aquileia", "lat": 45.77, "lon": 13.37},
        ],
    },
    "Tea Horse Road": {
        "color": "#84cc16",
        "goods": "Tea, Horses, Salt, Sugar, Herbs",
        "period": "600 AD - 1900 AD",
        "coords": [
            [29.05, 100.22],  # Pu'er (Yunnan)
            [25.04, 102.71],  # Kunming
            [26.87, 100.23],  # Dali
            [27.18, 100.17],  # Lijiang
            [29.65, 91.17],   # Lhasa
            [27.71, 85.32],   # Kathmandu
            [28.23, 83.99],   # Pokhara
        ],
        "cities": [
            {"name": "Pu'er (Tea Origin)", "lat": 29.05, "lon": 100.22},
            {"name": "Lhasa", "lat": 29.65, "lon": 91.17},
        ],
    },
    "Via de la Plata": {
        "color": "#c0c0c0",
        "goods": "Silver, Lead, Tin, Olive Oil, Wine",
        "period": "200 BC - 400 AD (Roman)",
        "coords": [
            [37.39, -5.99],   # Seville
            [38.88, -6.97],   # Merida
            [39.48, -6.37],   # Caceres
            [40.96, -5.66],   # Salamanca
            [42.60, -5.57],   # Leon
            [43.36, -5.85],   # Oviedo/Gijon
        ],
        "cities": [
            {"name": "Emerita Augusta (Merida)", "lat": 38.88, "lon": -6.97},
            {"name": "Hispalis (Seville)", "lat": 37.39, "lon": -5.99},
        ],
    },
}

# =====================================================================
# 8. COLONIALISM DATA
# =====================================================================
COLONIAL_POWERS = {
    "British": {
        "color": "#ef4444",
        "countries": {
            "IN": 1947, "PK": 1947, "BD": 1971, "MM": 1948, "MY": 1957,
            "SG": 1965, "AU": 1901, "NZ": 1907, "CA": 1867, "ZA": 1910,
            "KE": 1963, "TZ": 1961, "UG": 1962, "GH": 1957, "NG": 1960,
            "SL": 1961, "ZM": 1964, "ZW": 1980, "MW": 1964, "BW": 1966,
            "LS": 1966, "SZ": 1968, "JM": 1962, "TT": 1962, "GY": 1966,
            "BZ": 1981, "FJ": 1970, "CY": 1960, "MT": 1964, "LK": 1948,
            "IQ": 1932, "JO": 1946, "EG": 1922, "SD": 1956, "IL": 1948,
            "AE": 1971, "BH": 1971, "QA": 1971, "KW": 1961, "OM": 1951,
            "US": 1776, "IE": 1922, "HK": 1997,
        },
    },
    "French": {
        "color": "#3b82f6",
        "countries": {
            "DZ": 1962, "TN": 1956, "MA": 1956, "SN": 1960, "ML": 1960,
            "CI": 1960, "BF": 1960, "NE": 1960, "TD": 1960, "CF": 1960,
            "CG": 1960, "GA": 1960, "CM": 1960, "BJ": 1960, "TG": 1960,
            "GN": 1958, "DJ": 1977, "MG": 1960, "MR": 1960, "KM": 1975,
            "VN": 1954, "KH": 1953, "LA": 1954, "LB": 1943, "SY": 1946,
            "HT": 1804,
        },
    },
    "Spanish": {
        "color": "#eab308",
        "countries": {
            "MX": 1821, "GT": 1821, "HN": 1821, "SV": 1821, "NI": 1821,
            "CR": 1821, "PA": 1821, "CU": 1898, "DO": 1821, "PR": 1898,
            "CO": 1819, "VE": 1811, "EC": 1822, "PE": 1821, "BO": 1825,
            "PY": 1811, "UY": 1828, "AR": 1816, "CL": 1818, "PH": 1898,
            "GQ": 1968,
        },
    },
    "Portuguese": {
        "color": "#10b981",
        "countries": {
            "BR": 1822, "AO": 1975, "MZ": 1975, "GW": 1974, "CV": 1975,
            "ST": 1975, "TL": 2002, "MO": 1999,
        },
    },
    "Dutch": {
        "color": "#f97316",
        "countries": {
            "ID": 1945, "SR": 1975, "ZA": 1806,
        },
    },
    "Belgian": {
        "color": "#1a1a2e",
        "countries": {
            "CD": 1960, "RW": 1962, "BI": 1962,
        },
    },
    "German": {
        "color": "#6b7280",
        "countries": {
            "NA": 1990, "TZ": 1919, "CM": 1916, "TG": 1916, "PG": 1914,
            "WS": 1914,
        },
    },
    "Italian": {
        "color": "#a0522d",
        "countries": {
            "LY": 1951, "ER": 1952, "SO": 1960, "ET": 1941,
        },
    },
}

# =====================================================================
# 9. NUCLEAR & SPACE AGE DATA
# =====================================================================
NUCLEAR_POWERS = [
    {"country": "United States", "code": "US", "first_test": 1945, "lat": 38.9, "lon": -77.0, "warheads": 5244},
    {"country": "Russia", "code": "RU", "first_test": 1949, "lat": 55.75, "lon": 37.62, "warheads": 6257},
    {"country": "United Kingdom", "code": "GB", "first_test": 1952, "lat": 51.51, "lon": -0.13, "warheads": 225},
    {"country": "France", "code": "FR", "first_test": 1960, "lat": 48.86, "lon": 2.35, "warheads": 290},
    {"country": "China", "code": "CN", "first_test": 1964, "lat": 39.91, "lon": 116.39, "warheads": 500},
    {"country": "India", "code": "IN", "first_test": 1974, "lat": 28.61, "lon": 77.21, "warheads": 172},
    {"country": "Israel (undeclared)", "code": "IL", "first_test": 1979, "lat": 31.77, "lon": 35.23, "warheads": 90},
    {"country": "Pakistan", "code": "PK", "first_test": 1998, "lat": 33.69, "lon": 73.04, "warheads": 170},
    {"country": "North Korea", "code": "KP", "first_test": 2006, "lat": 39.02, "lon": 125.75, "warheads": 50},
]

SPACE_AGENCIES = [
    {"name": "NASA", "country": "United States", "founded": 1958, "lat": 38.88, "lon": -77.02},
    {"name": "ROSCOSMOS", "country": "Russia", "founded": 1992, "lat": 55.75, "lon": 37.62},
    {"name": "ESA", "country": "Europe (HQ Paris)", "founded": 1975, "lat": 48.85, "lon": 2.35},
    {"name": "CNSA", "country": "China", "founded": 1993, "lat": 39.91, "lon": 116.39},
    {"name": "ISRO", "country": "India", "founded": 1969, "lat": 12.97, "lon": 77.59},
    {"name": "JAXA", "country": "Japan", "founded": 2003, "lat": 35.68, "lon": 139.69},
    {"name": "KARI", "country": "South Korea", "founded": 1989, "lat": 36.37, "lon": 127.36},
    {"name": "CSA", "country": "Canada", "founded": 1989, "lat": 45.52, "lon": -73.57},
    {"name": "ASI", "country": "Italy", "founded": 1988, "lat": 41.90, "lon": 12.50},
    {"name": "DLR", "country": "Germany", "founded": 1969, "lat": 50.86, "lon": 7.12},
    {"name": "CNES", "country": "France", "founded": 1961, "lat": 48.85, "lon": 2.35},
    {"name": "UKSA", "country": "United Kingdom", "founded": 2010, "lat": 51.51, "lon": -0.13},
]

LAUNCH_SITES = [
    {"name": "Kennedy Space Center", "country": "US", "lat": 28.57, "lon": -80.65},
    {"name": "Cape Canaveral SFS", "country": "US", "lat": 28.49, "lon": -80.58},
    {"name": "Vandenberg SFB", "country": "US", "lat": 34.74, "lon": -120.57},
    {"name": "Baikonur Cosmodrome", "country": "KZ", "lat": 45.97, "lon": 63.31},
    {"name": "Plesetsk Cosmodrome", "country": "RU", "lat": 62.93, "lon": 40.58},
    {"name": "Vostochny Cosmodrome", "country": "RU", "lat": 51.88, "lon": 128.33},
    {"name": "Jiuquan Satellite Launch", "country": "CN", "lat": 40.96, "lon": 100.29},
    {"name": "Xichang Satellite Launch", "country": "CN", "lat": 28.25, "lon": 102.03},
    {"name": "Wenchang Space Launch", "country": "CN", "lat": 19.61, "lon": 110.95},
    {"name": "Satish Dhawan (Sriharikota)", "country": "IN", "lat": 13.72, "lon": 80.23},
    {"name": "Tanegashima Space Center", "country": "JP", "lat": 30.40, "lon": 131.00},
    {"name": "Guiana Space Centre (Kourou)", "country": "FR/ESA", "lat": 5.24, "lon": -52.77},
    {"name": "Semnan Launch Site", "country": "IR", "lat": 35.23, "lon": 53.92},
    {"name": "Palmachim Airbase", "country": "IL", "lat": 31.88, "lon": 34.69},
    {"name": "Naro Space Center", "country": "KR", "lat": 34.43, "lon": 127.54},
    {"name": "Esrange Space Center", "country": "SE", "lat": 67.89, "lon": 21.10},
    {"name": "San Marco Platform", "country": "IT/KE", "lat": -2.94, "lon": 40.21},
    {"name": "Rocket Lab LC-1", "country": "NZ", "lat": -39.26, "lon": 177.86},
    {"name": "Alcantara Launch Center", "country": "BR", "lat": -2.37, "lon": -44.40},
    {"name": "Sohae Satellite Station", "country": "KP", "lat": 39.66, "lon": 124.71},
]

# =====================================================================
# 10. WORLD CUISINE REGIONS DATA
# =====================================================================
CUISINE_REGIONS = [
    {
        "name": "Mediterranean",
        "dishes": "Paella, Moussaka, Couscous, Bruschetta, Hummus",
        "ingredients": "Olive oil, Garlic, Tomatoes, Herbs, Seafood",
        "color": "#3b82f6",
        "polygon": [
            [30.0, -5.0], [35.0, -5.0], [43.0, 5.0], [45.0, 12.0],
            [42.0, 18.0], [38.0, 25.0], [35.0, 28.0], [32.0, 35.0],
            [30.0, 32.0], [32.0, 15.0], [30.0, -5.0],
        ],
    },
    {
        "name": "East Asian",
        "dishes": "Sushi, Dim Sum, Ramen, Kimchi, Peking Duck",
        "ingredients": "Soy sauce, Rice, Noodles, Ginger, Sesame",
        "color": "#ef4444",
        "polygon": [
            [20.0, 100.0], [25.0, 98.0], [30.0, 105.0], [35.0, 110.0],
            [40.0, 115.0], [45.0, 130.0], [40.0, 140.0], [35.0, 140.0],
            [25.0, 122.0], [20.0, 110.0], [20.0, 100.0],
        ],
    },
    {
        "name": "South Asian",
        "dishes": "Biryani, Curry, Tandoori, Dosa, Naan",
        "ingredients": "Turmeric, Cumin, Cardamom, Chili, Lentils",
        "color": "#f59e0b",
        "polygon": [
            [8.0, 70.0], [8.0, 80.0], [15.0, 82.0], [20.0, 88.0],
            [28.0, 88.0], [35.0, 78.0], [33.0, 70.0], [25.0, 62.0],
            [20.0, 66.0], [15.0, 70.0], [8.0, 70.0],
        ],
    },
    {
        "name": "Middle Eastern",
        "dishes": "Kebab, Falafel, Shawarma, Baklava, Mansaf",
        "ingredients": "Sumac, Za'atar, Tahini, Lamb, Chickpeas",
        "color": "#10b981",
        "polygon": [
            [28.0, 35.0], [30.0, 34.0], [35.0, 36.0], [37.0, 42.0],
            [35.0, 50.0], [30.0, 55.0], [22.0, 50.0], [20.0, 42.0],
            [25.0, 37.0], [28.0, 35.0],
        ],
    },
    {
        "name": "Latin American",
        "dishes": "Tacos, Ceviche, Feijoada, Empanadas, Arepas",
        "ingredients": "Corn, Beans, Avocado, Chili, Lime",
        "color": "#8b5cf6",
        "polygon": [
            [32.0, -117.0], [24.0, -110.0], [20.0, -100.0],
            [15.0, -85.0], [8.0, -77.0], [0.0, -80.0],
            [-10.0, -75.0], [-20.0, -65.0], [-35.0, -58.0],
            [-40.0, -65.0], [-35.0, -72.0], [-20.0, -75.0],
            [-5.0, -82.0], [10.0, -85.0], [20.0, -105.0],
            [32.0, -117.0],
        ],
    },
    {
        "name": "West African",
        "dishes": "Jollof Rice, Fufu, Egusi Soup, Suya, Banku",
        "ingredients": "Palm oil, Yam, Cassava, Okra, Plantain",
        "color": "#ec4899",
        "polygon": [
            [5.0, -15.0], [10.0, -17.0], [15.0, -15.0], [15.0, -5.0],
            [12.0, 5.0], [8.0, 10.0], [5.0, 10.0], [4.0, 3.0],
            [5.0, -5.0], [5.0, -15.0],
        ],
    },
    {
        "name": "Caribbean",
        "dishes": "Jerk Chicken, Roti, Rice & Peas, Ackee & Saltfish",
        "ingredients": "Scotch bonnet, Allspice, Coconut, Rum, Plantain",
        "color": "#06b6d4",
        "polygon": [
            [10.0, -62.0], [12.0, -60.0], [18.0, -62.0], [20.0, -67.0],
            [22.0, -74.0], [23.0, -80.0], [20.0, -84.0], [15.0, -83.0],
            [10.0, -75.0], [10.0, -62.0],
        ],
    },
    {
        "name": "Scandinavian",
        "dishes": "Smorgasbord, Gravlax, Meatballs, Rugbrod, Lutefisk",
        "ingredients": "Salmon, Dill, Rye, Cream, Lingonberry",
        "color": "#38bdf8",
        "polygon": [
            [55.0, 8.0], [58.0, 5.0], [63.0, 5.0], [70.0, 18.0],
            [70.0, 30.0], [65.0, 28.0], [60.0, 25.0], [57.0, 18.0],
            [55.0, 15.0], [55.0, 8.0],
        ],
    },
    {
        "name": "Eastern European",
        "dishes": "Borscht, Pierogi, Goulash, Pelmeni, Sauerkraut",
        "ingredients": "Beet, Potato, Cabbage, Sour cream, Dill",
        "color": "#a855f7",
        "polygon": [
            [45.0, 15.0], [48.0, 14.0], [52.0, 14.0], [55.0, 22.0],
            [57.0, 28.0], [55.0, 40.0], [50.0, 40.0], [47.0, 35.0],
            [44.0, 28.0], [43.0, 20.0], [45.0, 15.0],
        ],
    },
    {
        "name": "Southeast Asian",
        "dishes": "Pad Thai, Pho, Rendang, Laksa, Spring Rolls",
        "ingredients": "Lemongrass, Fish sauce, Coconut milk, Chili, Rice noodles",
        "color": "#14b8a6",
        "polygon": [
            [5.0, 96.0], [10.0, 96.0], [18.0, 98.0], [22.0, 100.0],
            [22.0, 108.0], [15.0, 110.0], [10.0, 115.0], [5.0, 118.0],
            [-5.0, 115.0], [-8.0, 108.0], [-5.0, 100.0], [5.0, 96.0],
        ],
    },
]

# =====================================================================
# REST COUNTRIES API
# =====================================================================
REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,cca2,latlng,region,subregion,area"


@st.cache_data(ttl=3600)
def fetch_countries_basic():
    """Fetch basic country data from REST Countries API."""
    try:
        resp = requests.get(REST_COUNTRIES_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for c in data:
            code = c.get("cca2", "")
            if code and c.get("latlng"):
                result[code] = {
                    "name": c["name"].get("common", code),
                    "lat": c["latlng"][0],
                    "lon": c["latlng"][1],
                    "region": c.get("region", ""),
                    "subregion": c.get("subregion", ""),
                }
        return result
    except Exception:
        return {}


# =====================================================================
# OVERPASS QUERIES
# =====================================================================
@st.cache_data(ttl=3600)
def fetch_unesco_sites(lat: float, lon: float, radius_km: float):
    """Fetch UNESCO World Heritage Sites via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:90];
(
  node["heritage"="world_heritage_site"](around:{radius_m},{lat},{lon});
  way["heritage"="world_heritage_site"](around:{radius_m},{lat},{lon});
  node["heritage:operator"="whc"](around:{radius_m},{lat},{lon});
  way["heritage:operator"="whc"](around:{radius_m},{lat},{lon});
  node["whc:inscription_date"](around:{radius_m},{lat},{lon});
  way["whc:inscription_date"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown") if result else "No response"
        return {"elements": [], "error": err}
    return result


@st.cache_data(ttl=3600)
def fetch_nuclear_plants(lat: float, lon: float, radius_km: float):
    """Fetch nuclear power plants via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["power"="plant"]["plant:source"="nuclear"](around:{radius_m},{lat},{lon});
  way["power"="plant"]["plant:source"="nuclear"](around:{radius_m},{lat},{lon});
  node["power"="generator"]["generator:source"="nuclear"](around:{radius_m},{lat},{lon});
  way["power"="generator"]["generator:source"="nuclear"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown") if result else "No response"
        return {"elements": [], "error": err}
    return result


# =====================================================================
# HELPER: DARK MATPLOTLIB
# =====================================================================
def _dark_fig(figsize=(8, 4)):
    """Create a dark-themed matplotlib figure."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.tick_params(colors="#8b97b0")
    ax.xaxis.label.set_color("#e8ecf4")
    ax.yaxis.label.set_color("#e8ecf4")
    ax.title.set_color("#e8ecf4")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


# =====================================================================
# MAP BUILDERS
# =====================================================================

def _build_agriculture_map():
    """Build the Origins of Agriculture map."""
    m = folium.Map(location=[20, 30], zoom_start=2, tiles="CartoDB dark_matter")

    for region in AGRICULTURE_ORIGINS:
        popup_html = (
            f"<div style='min-width:200px;background:#1a2235;color:#e8ecf4;"
            f"padding:10px;border-radius:8px;border:1px solid {escape(region['color'])};'>"
            f"<b style='color:{escape(region['color'])};font-size:14px;'>"
            f"{escape(region['name'])}</b><br>"
            f"<b>Date:</b> {escape(region['date'])}<br>"
            f"<b>Crops:</b> {escape(region['crops'])}"
            f"</div>"
        )
        folium.Polygon(
            locations=region["polygon"],
            color=region["color"],
            fill=True,
            fill_color=region["color"],
            fill_opacity=0.25,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{region['name']} ({region['date']})",
        ).add_to(m)

        folium.Marker(
            location=region["center"],
            icon=folium.DivIcon(html=(
                f"<div style='font-size:10px;color:{region['color']};"
                f"font-weight:bold;text-shadow:1px 1px 2px #000;white-space:nowrap;'>"
                f"{escape(region['name'])}</div>"
            )),
        ).add_to(m)

    return m


def _build_ancient_civilizations_map(time_period: int):
    """Build Ancient Civilizations map filtered by time period."""
    m = folium.Map(location=[25, 40], zoom_start=3, tiles="CartoDB dark_matter")

    visible = [c for c in ANCIENT_CIVILIZATIONS if c["start"] <= time_period <= c["end"]]

    if not visible:
        visible = [c for c in ANCIENT_CIVILIZATIONS if c["start"] <= time_period]

    for civ in visible:
        start_str = f"{abs(civ['start'])} BC" if civ["start"] < 0 else f"{civ['start']} AD"
        end_str = f"{abs(civ['end'])} BC" if civ["end"] < 0 else f"{civ['end']} AD"

        popup_html = (
            f"<div style='min-width:220px;background:#1a2235;color:#e8ecf4;"
            f"padding:10px;border-radius:8px;border:1px solid {escape(civ['color'])};'>"
            f"<b style='color:{escape(civ['color'])};font-size:14px;'>"
            f"{escape(civ['name'])}</b><br>"
            f"<b>Period:</b> {escape(start_str)} - {escape(end_str)}<br>"
            f"<b>Capital:</b> {escape(civ['capital'])}<br>"
            f"<b>Achievements:</b> {escape(civ['achievements'])}"
            f"</div>"
        )
        folium.Polygon(
            locations=civ["polygon"],
            color=civ["color"],
            fill=True,
            fill_color=civ["color"],
            fill_opacity=0.2,
            weight=2,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{civ['name']} ({start_str} - {end_str})",
        ).add_to(m)

    return m, visible


def _build_writing_systems_map():
    """Build Writing Systems world map."""
    countries = fetch_countries_basic()
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    country_script = {}
    for script, info in WRITING_SYSTEMS.items():
        for code in info["countries"]:
            country_script[code] = {"script": script, "color": info["color"]}

    for code, cdata in countries.items():
        sinfo = country_script.get(code)
        if sinfo:
            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid {escape(sinfo['color'])};'>"
                f"<b>{escape(cdata['name'])}</b><br>"
                f"<b>Script:</b> <span style='color:{escape(sinfo['color'])};'>"
                f"{escape(sinfo['script'])}</span>"
                f"</div>"
            )
            folium.CircleMarker(
                location=[cdata["lat"], cdata["lon"]],
                radius=6,
                color=sinfo["color"],
                fill=True,
                fill_color=sinfo["color"],
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{escape(cdata['name'])}: {escape(sinfo['script'])}",
            ).add_to(m)

    return m


def _build_religions_map():
    """Build World Religions Distribution map."""
    countries = fetch_countries_basic()
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    country_religion = {}
    for religion, info in RELIGION_DATA.items():
        for code in info["countries"]:
            if code not in country_religion:
                country_religion[code] = {"religion": religion, "color": info["color"]}

    for code, cdata in countries.items():
        rinfo = country_religion.get(code)
        if rinfo:
            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid {escape(rinfo['color'])};'>"
                f"<b>{escape(cdata['name'])}</b><br>"
                f"<b>Majority:</b> <span style='color:{escape(rinfo['color'])};'>"
                f"{escape(rinfo['religion'])}</span>"
                f"</div>"
            )
            folium.CircleMarker(
                location=[cdata["lat"], cdata["lon"]],
                radius=7,
                color=rinfo["color"],
                fill=True,
                fill_color=rinfo["color"],
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{escape(cdata['name'])}: {escape(rinfo['religion'])}",
            ).add_to(m)

    return m


def _build_language_families_map():
    """Build Language Families map."""
    countries = fetch_countries_basic()
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    country_family = {}
    for family, info in LANGUAGE_FAMILIES.items():
        for code in info["countries"]:
            if code not in country_family:
                country_family[code] = {"family": family, "color": info["color"]}

    for code, cdata in countries.items():
        finfo = country_family.get(code)
        if finfo:
            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid {escape(finfo['color'])};'>"
                f"<b>{escape(cdata['name'])}</b><br>"
                f"<b>Language Family:</b> <span style='color:{escape(finfo['color'])};'>"
                f"{escape(finfo['family'])}</span>"
                f"</div>"
            )
            folium.CircleMarker(
                location=[cdata["lat"], cdata["lon"]],
                radius=6,
                color=finfo["color"],
                fill=True,
                fill_color=finfo["color"],
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{escape(cdata['name'])}: {escape(finfo['family'])}",
            ).add_to(m)

    return m


def _build_unesco_map(lat: float, lon: float, radius_km: float):
    """Build UNESCO World Heritage Sites map."""
    data = fetch_unesco_sites(lat, lon, radius_km)

    if data.get("error"):
        st.warning(f"Overpass query issue: {data['error']}. Showing available results.")

    elements = data.get("elements", [])

    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    sites = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        elat, elon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            elat, elon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
            if coords:
                elat = sum(c[0] for c in coords) / len(coords)
                elon = sum(c[1] for c in coords) / len(coords)

        if elat is None:
            continue

        name = tags.get("name", tags.get("name:en", "Unnamed site"))
        heritage_val = tags.get("heritage", "")
        whc_criteria = tags.get("whc:criteria_string", tags.get("heritage:criteria", ""))
        inscription = tags.get("whc:inscription_date", tags.get("heritage:inscription_date", ""))

        if "natural" in whc_criteria.lower() or tags.get("boundary") == "national_park":
            category = "Natural"
            color = "#10b981"
        elif "cultural" in whc_criteria.lower() or "mixed" in whc_criteria.lower():
            category = "Cultural"
            color = "#f59e0b"
        else:
            category = "Cultural"
            color = "#f59e0b"

        sites.append({
            "name": name,
            "lat": elat,
            "lon": elon,
            "category": category,
            "color": color,
            "inscription": inscription,
            "criteria": whc_criteria,
            "heritage": heritage_val,
            "wikipedia": tags.get("wikipedia", ""),
        })

    m = folium.Map(location=[lat, lon], zoom_start=5, tiles="CartoDB dark_matter")

    for site in sites:
        popup_html = (
            f"<div style='min-width:200px;background:#1a2235;color:#e8ecf4;"
            f"padding:10px;border-radius:8px;border:1px solid {escape(site['color'])};'>"
            f"<b style='color:{escape(site['color'])};font-size:13px;'>"
            f"{escape(site['name'])}</b><br>"
            f"<b>Category:</b> {escape(site['category'])}<br>"
        )
        if site["inscription"]:
            popup_html += f"<b>Inscribed:</b> {escape(str(site['inscription']))}<br>"
        if site["criteria"]:
            popup_html += f"<b>Criteria:</b> {escape(site['criteria'])}<br>"
        if site["wikipedia"]:
            popup_html += f"<b>Wikipedia:</b> {escape(site['wikipedia'])}<br>"
        popup_html += "</div>"

        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=8,
            color=site["color"],
            fill=True,
            fill_color=site["color"],
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{site['name']} ({site['category']})",
        ).add_to(m)

    return m, sites


def _build_trade_routes_map(selected_routes: list):
    """Build Silk Road & Trade Routes map."""
    m = folium.Map(location=[30, 50], zoom_start=3, tiles="CartoDB dark_matter")

    for route_name in selected_routes:
        route = TRADE_ROUTES.get(route_name)
        if not route:
            continue

        folium.PolyLine(
            locations=route["coords"],
            color=route["color"],
            weight=3,
            opacity=0.8,
            tooltip=f"{route_name} ({route['period']})",
            popup=folium.Popup(
                f"<div style='background:#1a2235;color:#e8ecf4;padding:10px;"
                f"border-radius:8px;border:1px solid {escape(route['color'])};'>"
                f"<b style='color:{escape(route['color'])};'>{escape(route_name)}</b><br>"
                f"<b>Period:</b> {escape(route['period'])}<br>"
                f"<b>Goods:</b> {escape(route['goods'])}</div>",
                max_width=300,
            ),
        ).add_to(m)

        for city in route.get("cities", []):
            folium.CircleMarker(
                location=[city["lat"], city["lon"]],
                radius=6,
                color=route["color"],
                fill=True,
                fill_color=route["color"],
                fill_opacity=0.9,
                weight=2,
                tooltip=escape(city["name"]),
            ).add_to(m)

    return m


def _build_colonialism_map():
    """Build Colonialism map."""
    countries = fetch_countries_basic()
    m = folium.Map(location=[10, 20], zoom_start=2, tiles="CartoDB dark_matter")

    country_colonial = {}
    for power, info in COLONIAL_POWERS.items():
        for code, year in info["countries"].items():
            if code not in country_colonial:
                country_colonial[code] = {
                    "power": power,
                    "color": info["color"],
                    "independence": year,
                }

    for code, cdata in countries.items():
        cinfo = country_colonial.get(code)
        if cinfo:
            display_color = cinfo["color"]
            if display_color == "#1a1a2e":
                display_color = "#4a4a6e"

            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid {escape(display_color)};'>"
                f"<b>{escape(cdata['name'])}</b><br>"
                f"<b>Colonial Power:</b> <span style='color:{escape(display_color)};'>"
                f"{escape(cinfo['power'])}</span><br>"
                f"<b>Independence:</b> {cinfo['independence']}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[cdata["lat"], cdata["lon"]],
                radius=7,
                color=display_color,
                fill=True,
                fill_color=display_color,
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{cdata['name']}: {cinfo['power']} (indep. {cinfo['independence']})",
            ).add_to(m)

    return m, country_colonial


def _build_nuclear_space_map(show_nukes: bool, show_agencies: bool,
                             show_plants: bool, show_launches: bool,
                             plant_lat: float, plant_lon: float,
                             plant_radius: float):
    """Build Nuclear & Space Age map."""
    m = folium.Map(location=[30, 20], zoom_start=2, tiles="CartoDB dark_matter")

    if show_nukes:
        for nuke in NUCLEAR_POWERS:
            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid #ef4444;'>"
                f"<b style='color:#ef4444;'>{escape(nuke['country'])}</b><br>"
                f"<b>First Test:</b> {nuke['first_test']}<br>"
                f"<b>Est. Warheads:</b> ~{nuke['warheads']}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[nuke["lat"], nuke["lon"]],
                radius=max(6, min(14, nuke["warheads"] // 500)),
                color="#ef4444",
                fill=True,
                fill_color="#ef4444",
                fill_opacity=0.6,
                weight=2,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{nuke['country']} - Nuclear ({nuke['first_test']})",
            ).add_to(m)

    if show_agencies:
        for agency in SPACE_AGENCIES:
            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid #3b82f6;'>"
                f"<b style='color:#3b82f6;'>{escape(agency['name'])}</b><br>"
                f"<b>Country:</b> {escape(agency['country'])}<br>"
                f"<b>Founded:</b> {agency['founded']}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[agency["lat"], agency["lon"]],
                radius=7,
                color="#3b82f6",
                fill=True,
                fill_color="#3b82f6",
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{agency['name']} ({agency['country']})",
            ).add_to(m)

    if show_launches:
        for site in LAUNCH_SITES:
            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid #f59e0b;'>"
                f"<b style='color:#f59e0b;'>{escape(site['name'])}</b><br>"
                f"<b>Country:</b> {escape(site['country'])}"
                f"</div>"
            )
            folium.Marker(
                location=[site["lat"], site["lon"]],
                icon=folium.Icon(color="orange", icon="rocket", prefix="fa"),
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=escape(site["name"]),
            ).add_to(m)

    if show_plants:
        plant_data = fetch_nuclear_plants(plant_lat, plant_lon, plant_radius)
        elements = plant_data.get("elements", [])

        node_lookup = {}
        for el in elements:
            if el.get("type") == "node" and "lat" in el and "lon" in el:
                node_lookup[el["id"]] = (el["lat"], el["lon"])

        plant_count = 0
        for el in elements:
            tags = el.get("tags", {})
            if not tags:
                continue

            plat, plon = None, None
            if el.get("type") == "node" and "lat" in el and "lon" in el:
                plat, plon = el["lat"], el["lon"]
            elif el.get("type") == "way":
                nodes = el.get("nodes", [])
                coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
                if coords:
                    plat = sum(c[0] for c in coords) / len(coords)
                    plon = sum(c[1] for c in coords) / len(coords)

            if plat is None:
                continue

            name = tags.get("name", tags.get("name:en", "Nuclear Plant"))
            popup_html = (
                f"<div style='background:#1a2235;color:#e8ecf4;padding:8px;"
                f"border-radius:6px;border:1px solid #10b981;'>"
                f"<b style='color:#10b981;'>{escape(name)}</b><br>"
                f"<b>Type:</b> Nuclear Power Plant"
                f"</div>"
            )
            folium.CircleMarker(
                location=[plat, plon],
                radius=5,
                color="#10b981",
                fill=True,
                fill_color="#10b981",
                fill_opacity=0.8,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=escape(name),
            ).add_to(m)
            plant_count += 1

        if plant_data.get("error"):
            st.info(f"Nuclear plants query note: {plant_data['error']}")

    return m


def _build_cuisine_map(show_spice_routes: bool):
    """Build World Cuisine Regions map."""
    m = folium.Map(location=[20, 20], zoom_start=2, tiles="CartoDB dark_matter")

    for region in CUISINE_REGIONS:
        popup_html = (
            f"<div style='min-width:200px;background:#1a2235;color:#e8ecf4;"
            f"padding:10px;border-radius:8px;border:1px solid {escape(region['color'])};'>"
            f"<b style='color:{escape(region['color'])};font-size:14px;'>"
            f"{escape(region['name'])} Cuisine</b><br>"
            f"<b>Signature Dishes:</b> {escape(region['dishes'])}<br>"
            f"<b>Key Ingredients:</b> {escape(region['ingredients'])}"
            f"</div>"
        )
        folium.Polygon(
            locations=region["polygon"],
            color=region["color"],
            fill=True,
            fill_color=region["color"],
            fill_opacity=0.2,
            weight=2,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{region['name']} Cuisine",
        ).add_to(m)

    if show_spice_routes:
        spice = TRADE_ROUTES.get("Spice Trade Route (Maritime)")
        if spice:
            folium.PolyLine(
                locations=spice["coords"],
                color="#f59e0b",
                weight=2,
                opacity=0.6,
                dash_array="8 4",
                tooltip="Spice Trade Route (Maritime)",
            ).add_to(m)

    return m


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_civilization_maps_tab():
    """Render the Civilization & Culture Maps tab."""

    st.markdown(
        '<div class="tab-header amber">'
        "<h4>Civilization & Culture Maps</h4>"
        "<p>Human history, cultures, languages, trade routes, and heritage</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    MAP_TYPES = [
        "Origins of Agriculture",
        "Ancient Civilizations",
        "Writing Systems Map",
        "World Religions Distribution",
        "Language Families",
        "UNESCO World Heritage Sites",
        "Silk Road & Trade Routes",
        "Colonialism Map",
        "Nuclear & Space Age",
        "World Cuisine Regions",
    ]

    selected_map = st.selectbox("Select Map", MAP_TYPES, key="civ_map_select")

    st.markdown("---")

    # -----------------------------------------------------------------
    # 1. ORIGINS OF AGRICULTURE
    # -----------------------------------------------------------------
    if selected_map == "Origins of Agriculture":
        st.markdown(
            "<p style='color:#8b97b0;'>Independent centers where agriculture originated, "
            "with estimated dates and primary crops domesticated.</p>",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Centers Shown", len(AGRICULTURE_ORIGINS))
        c2.metric("Earliest", "~10,000 BC")
        c3.metric("Latest", "~3,000 BC")

        fmap = _build_agriculture_map()
        components.html(fmap._repr_html_(), height=600)

        # Timeline chart
        st.subheader("Timeline of Agricultural Origins")
        fig, ax = _dark_fig(figsize=(10, 4))
        regions = [r["name"] for r in AGRICULTURE_ORIGINS]
        years = [r["year"] for r in AGRICULTURE_ORIGINS]
        colors = [r["color"] for r in AGRICULTURE_ORIGINS]
        ax.barh(regions, [-y for y in years], color=colors, edgecolor="#2a3550")
        ax.set_xlabel("Years Before Present (approx.)")
        ax.set_title("Independent Origins of Agriculture")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Data table
        df = pd.DataFrame([
            {"Region": r["name"], "Date": r["date"], "Crops": r["crops"]}
            for r in AGRICULTURE_ORIGINS
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Agriculture Origins CSV", csv,
                           "agriculture_origins.csv", "text/csv",
                           key="dl_agri")

    # -----------------------------------------------------------------
    # 2. ANCIENT CIVILIZATIONS
    # -----------------------------------------------------------------
    elif selected_map == "Ancient Civilizations":
        st.markdown(
            "<p style='color:#8b97b0;'>Major ancient civilizations with approximate territories. "
            "Select a time period to see which civilizations existed.</p>",
            unsafe_allow_html=True,
        )

        time_periods = {
            "3000 BC": -3000,
            "2000 BC": -2000,
            "1000 BC": -1000,
            "500 BC": -500,
            "0 AD (Year 1)": 0,
            "500 AD": 500,
        }
        period_label = st.select_slider(
            "Time Period",
            options=list(time_periods.keys()),
            value="500 BC",
            key="civ_time_period",
        )
        time_val = time_periods[period_label]

        fmap, visible = _build_ancient_civilizations_map(time_val)

        c1, c2 = st.columns(2)
        c1.metric("Civilizations at this period", len(visible))
        c2.metric("Total in database", len(ANCIENT_CIVILIZATIONS))

        components.html(fmap._repr_html_(), height=600)

        if visible:
            rows = []
            for c in visible:
                s = f"{abs(c['start'])} BC" if c["start"] < 0 else f"{c['start']} AD"
                e = f"{abs(c['end'])} BC" if c["end"] < 0 else f"{c['end']} AD"
                rows.append({
                    "Civilization": c["name"],
                    "Period": f"{s} - {e}",
                    "Capital": c["capital"],
                    "Key Achievements": c["achievements"],
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Civilizations CSV", csv,
                               "ancient_civilizations.csv", "text/csv",
                               key="dl_civs")

    # -----------------------------------------------------------------
    # 3. WRITING SYSTEMS MAP
    # -----------------------------------------------------------------
    elif selected_map == "Writing Systems Map":
        st.markdown(
            "<p style='color:#8b97b0;'>Current primary writing scripts used by countries worldwide. "
            "Each country is colored by its dominant script system.</p>",
            unsafe_allow_html=True,
        )

        script_counts = {}
        for script, info in WRITING_SYSTEMS.items():
            script_counts[script] = len(info["countries"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Script Systems", len(WRITING_SYSTEMS))
        c2.metric("Most Widespread", "Latin")
        total_countries = sum(script_counts.values())
        c3.metric("Countries Mapped", total_countries)

        with st.spinner("Loading country data..."):
            fmap = _build_writing_systems_map()
        components.html(fmap._repr_html_(), height=600)

        # Legend
        st.markdown("**Script Legend:**")
        legend_cols = st.columns(4)
        for i, (script, info) in enumerate(WRITING_SYSTEMS.items()):
            col = legend_cols[i % 4]
            col.markdown(
                f"<span style='color:{info['color']};'>&#9632;</span> "
                f"{script} ({len(info['countries'])})",
                unsafe_allow_html=True,
            )

        # Bar chart
        st.subheader("Countries per Writing System")
        fig, ax = _dark_fig(figsize=(10, 5))
        scripts = list(script_counts.keys())
        counts = list(script_counts.values())
        colors = [WRITING_SYSTEMS[s]["color"] for s in scripts]
        ax.barh(scripts, counts, color=colors, edgecolor="#2a3550")
        ax.set_xlabel("Number of Countries")
        ax.set_title("Writing Systems by Country Count")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {"Script": s, "Countries": c}
            for s, c in sorted(script_counts.items(), key=lambda x: -x[1])
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Writing Systems CSV", csv,
                           "writing_systems.csv", "text/csv",
                           key="dl_scripts")

    # -----------------------------------------------------------------
    # 4. WORLD RELIGIONS DISTRIBUTION
    # -----------------------------------------------------------------
    elif selected_map == "World Religions Distribution":
        st.markdown(
            "<p style='color:#8b97b0;'>Countries colored by majority religion. "
            "Includes Christianity (Catholic, Protestant, Orthodox), Islam (Sunni, Shia), "
            "Hinduism, Buddhism, Judaism, and more.</p>",
            unsafe_allow_html=True,
        )

        religion_counts = {}
        for rel, info in RELIGION_DATA.items():
            religion_counts[rel] = len(info["countries"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Religion Categories", len(RELIGION_DATA))
        c2.metric("Most Countries", "Sunni Islam")
        c3.metric("Countries Mapped", sum(religion_counts.values()))

        with st.spinner("Loading religion map..."):
            fmap = _build_religions_map()
        components.html(fmap._repr_html_(), height=600)

        # Legend
        st.markdown("**Religion Legend:**")
        legend_cols = st.columns(4)
        for i, (rel, info) in enumerate(RELIGION_DATA.items()):
            col = legend_cols[i % 4]
            col.markdown(
                f"<span style='color:{info['color']};'>&#9632;</span> "
                f"{rel} ({len(info['countries'])})",
                unsafe_allow_html=True,
            )

        # Pie chart of global distribution
        st.subheader("Global Religion Distribution (% of world population)")
        fig, ax = _dark_fig(figsize=(7, 7))
        labels = list(RELIGION_GLOBAL_PCT.keys())
        sizes = list(RELIGION_GLOBAL_PCT.values())
        pie_colors = [
            "#3b82f6", "#10b981", "#f97316", "#eab308",
            "#a0522d", "#fbbf24", "#8b5cf6", "#6b7280",
        ]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.1f%%",
            colors=pie_colors, pctdistance=0.85,
            textprops={"color": "#e8ecf4", "fontsize": 9},
        )
        for at in autotexts:
            at.set_fontsize(8)
            at.set_color("#e8ecf4")
        ax.set_title("World Religion Distribution")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {"Religion": r, "Countries": c}
            for r, c in sorted(religion_counts.items(), key=lambda x: -x[1])
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Religions CSV", csv,
                           "world_religions.csv", "text/csv",
                           key="dl_religions")

    # -----------------------------------------------------------------
    # 5. LANGUAGE FAMILIES
    # -----------------------------------------------------------------
    elif selected_map == "Language Families":
        st.markdown(
            "<p style='color:#8b97b0;'>Countries colored by primary language family. "
            "Covers 13 major language families from Indo-European to Austroasiatic.</p>",
            unsafe_allow_html=True,
        )

        family_counts = {}
        for fam, info in LANGUAGE_FAMILIES.items():
            family_counts[fam] = len(info["countries"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Language Families", len(LANGUAGE_FAMILIES))
        c2.metric("Largest Family", "Indo-European")
        c3.metric("Countries Mapped", sum(family_counts.values()))

        with st.spinner("Loading language families map..."):
            fmap = _build_language_families_map()
        components.html(fmap._repr_html_(), height=600)

        # Legend
        st.markdown("**Language Family Legend:**")
        legend_cols = st.columns(4)
        for i, (fam, info) in enumerate(LANGUAGE_FAMILIES.items()):
            col = legend_cols[i % 4]
            col.markdown(
                f"<span style='color:{info['color']};'>&#9632;</span> "
                f"{fam} ({len(info['countries'])})",
                unsafe_allow_html=True,
            )

        # Most spoken languages bar chart
        st.subheader("Most Spoken Languages (millions of speakers)")
        fig, ax = _dark_fig(figsize=(10, 5))
        langs = list(MOST_SPOKEN_LANGUAGES.keys())
        speakers = list(MOST_SPOKEN_LANGUAGES.values())
        bar_colors = ["#06b6d4" if i % 2 == 0 else "#8b5cf6" for i in range(len(langs))]
        ax.barh(langs, speakers, color=bar_colors, edgecolor="#2a3550")
        ax.set_xlabel("Total Speakers (millions)")
        ax.set_title("Most Spoken Languages Worldwide")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        df = pd.DataFrame([
            {"Family": f, "Countries": c}
            for f, c in sorted(family_counts.items(), key=lambda x: -x[1])
        ])
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Language Families CSV", csv,
                           "language_families.csv", "text/csv",
                           key="dl_lang_fam")

    # -----------------------------------------------------------------
    # 6. UNESCO WORLD HERITAGE SITES
    # -----------------------------------------------------------------
    elif selected_map == "UNESCO World Heritage Sites":
        st.markdown(
            "<p style='color:#8b97b0;'>UNESCO World Heritage Sites queried from OpenStreetMap "
            "via Overpass API. Select a region to explore Cultural, Natural, and Mixed sites.</p>",
            unsafe_allow_html=True,
        )

        UNESCO_PRESETS = {
            "Custom": None,
            "Europe - Western": {"lat": 48.0, "lon": 5.0, "radius": 800},
            "Europe - Mediterranean": {"lat": 40.0, "lon": 15.0, "radius": 600},
            "Europe - Eastern": {"lat": 50.0, "lon": 25.0, "radius": 600},
            "Asia - East": {"lat": 35.0, "lon": 115.0, "radius": 1000},
            "Asia - South": {"lat": 22.0, "lon": 80.0, "radius": 800},
            "Asia - Southeast": {"lat": 5.0, "lon": 110.0, "radius": 800},
            "Middle East": {"lat": 30.0, "lon": 42.0, "radius": 600},
            "Africa - North": {"lat": 30.0, "lon": 10.0, "radius": 700},
            "Africa - Sub-Saharan": {"lat": 0.0, "lon": 25.0, "radius": 1500},
            "Americas - North": {"lat": 40.0, "lon": -100.0, "radius": 1500},
            "Americas - Central": {"lat": 18.0, "lon": -90.0, "radius": 600},
            "Americas - South": {"lat": -15.0, "lon": -60.0, "radius": 1500},
            "Oceania": {"lat": -25.0, "lon": 135.0, "radius": 1500},
        }

        preset = st.selectbox("Region Preset", list(UNESCO_PRESETS.keys()),
                               key="unesco_preset")

        if preset == "Custom":
            uc1, uc2, uc3 = st.columns(3)
            u_lat = uc1.number_input("Latitude", -90.0, 90.0, 45.0, key="unesco_lat")
            u_lon = uc2.number_input("Longitude", -180.0, 180.0, 12.0, key="unesco_lon")
            u_rad = uc3.number_input("Radius (km)", 10, 2000, 500, key="unesco_rad")
        else:
            p = UNESCO_PRESETS[preset]
            u_lat, u_lon, u_rad = p["lat"], p["lon"], p["radius"]
            st.info(f"Searching around ({u_lat}, {u_lon}) within {u_rad} km")

        if st.button("Search UNESCO Sites", key="btn_unesco"):
            with st.spinner("Querying Overpass API for UNESCO sites..."):
                fmap, sites = _build_unesco_map(u_lat, u_lon, u_rad)

            c1, c2, c3 = st.columns(3)
            cultural = sum(1 for s in sites if s["category"] == "Cultural")
            natural = sum(1 for s in sites if s["category"] == "Natural")
            c1.metric("Total Sites Found", len(sites))
            c2.metric("Cultural", cultural)
            c3.metric("Natural", natural)

            components.html(fmap._repr_html_(), height=600)

            if sites:
                df = pd.DataFrame([
                    {
                        "Name": s["name"],
                        "Category": s["category"],
                        "Inscription": s.get("inscription", ""),
                        "Lat": round(s["lat"], 4),
                        "Lon": round(s["lon"], 4),
                    }
                    for s in sites
                ])
                st.dataframe(df, width="stretch")

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download UNESCO Sites CSV", csv,
                                   "unesco_sites.csv", "text/csv",
                                   key="civm_dl_unesco")
            else:
                st.info("No UNESCO World Heritage Sites found in this area. "
                        "Try a larger radius or different region.")

    # -----------------------------------------------------------------
    # 7. SILK ROAD & TRADE ROUTES
    # -----------------------------------------------------------------
    elif selected_map == "Silk Road & Trade Routes":
        st.markdown(
            "<p style='color:#8b97b0;'>Historical trade routes that shaped civilizations. "
            "Select one or more routes to display on the map.</p>",
            unsafe_allow_html=True,
        )

        route_names = list(TRADE_ROUTES.keys())
        selected_routes = st.multiselect(
            "Select Trade Routes",
            route_names,
            default=route_names[:3],
            key="trade_routes_select",
        )

        if not selected_routes:
            st.warning("Please select at least one trade route.")
            return

        c1, c2 = st.columns(2)
        c1.metric("Routes Selected", len(selected_routes))
        total_cities = sum(len(TRADE_ROUTES[r].get("cities", [])) for r in selected_routes)
        c2.metric("Key Cities", total_cities)

        fmap = _build_trade_routes_map(selected_routes)
        components.html(fmap._repr_html_(), height=600)

        # Route details
        st.subheader("Route Details")
        rows = []
        for rname in selected_routes:
            route = TRADE_ROUTES[rname]
            rows.append({
                "Route": rname,
                "Period": route["period"],
                "Goods Traded": route["goods"],
                "Key Cities": ", ".join(c["name"] for c in route.get("cities", [])),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Trade Routes CSV", csv,
                           "trade_routes.csv", "text/csv",
                           key="dl_trade")

    # -----------------------------------------------------------------
    # 8. COLONIALISM MAP
    # -----------------------------------------------------------------
    elif selected_map == "Colonialism Map":
        st.markdown(
            "<p style='color:#8b97b0;'>Countries colored by their primary colonial ruler. "
            "Shows year of independence and colonial power. "
            "Note: Many countries had overlapping colonial histories; "
            "this shows the primary or most recent colonizer.</p>",
            unsafe_allow_html=True,
        )

        with st.spinner("Loading colonialism map..."):
            fmap, country_colonial = _build_colonialism_map()

        power_counts = {}
        for code, info in country_colonial.items():
            p = info["power"]
            power_counts[p] = power_counts.get(p, 0) + 1

        c1, c2, c3 = st.columns(3)
        c1.metric("Colonial Powers", len(COLONIAL_POWERS))
        c2.metric("Countries Colonized", len(country_colonial))
        largest_empire = max(power_counts, key=power_counts.get) if power_counts else "N/A"
        c3.metric("Largest Empire", f"{largest_empire} ({power_counts.get(largest_empire, 0)})")

        components.html(fmap._repr_html_(), height=600)

        # Legend
        st.markdown("**Colonial Power Legend:**")
        legend_cols = st.columns(4)
        for i, (power, info) in enumerate(COLONIAL_POWERS.items()):
            col = legend_cols[i % 4]
            display_color = info["color"] if info["color"] != "#1a1a2e" else "#4a4a6e"
            col.markdown(
                f"<span style='color:{display_color};'>&#9632;</span> "
                f"{power} ({power_counts.get(power, 0)} countries)",
                unsafe_allow_html=True,
            )

        # Decolonization timeline
        st.subheader("Decolonization Timeline")
        decades = {}
        countries_data = fetch_countries_basic()
        for code, info in country_colonial.items():
            decade = (info["independence"] // 10) * 10
            decades[decade] = decades.get(decade, 0) + 1

        if decades:
            fig, ax = _dark_fig(figsize=(10, 4))
            sorted_decades = sorted(decades.items())
            dec_labels = [str(d[0]) + "s" for d in sorted_decades]
            dec_values = [d[1] for d in sorted_decades]
            ax.bar(dec_labels, dec_values, color="#06b6d4", edgecolor="#2a3550")
            ax.set_xlabel("Decade")
            ax.set_ylabel("Countries Gaining Independence")
            ax.set_title("Waves of Decolonization")
            plt.xticks(rotation=45, ha="right")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        # Data table
        rows = []
        for code, info in country_colonial.items():
            cname = countries_data.get(code, {}).get("name", code)
            rows.append({
                "Country": cname,
                "Colonial Power": info["power"],
                "Independence": info["independence"],
            })
        df = pd.DataFrame(rows).sort_values("Independence")
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Colonialism Data CSV", csv,
                           "colonialism_data.csv", "text/csv",
                           key="civm_dl_colonial")

    # -----------------------------------------------------------------
    # 9. NUCLEAR & SPACE AGE
    # -----------------------------------------------------------------
    elif selected_map == "Nuclear & Space Age":
        st.markdown(
            "<p style='color:#8b97b0;'>Nuclear-armed states, space agencies, "
            "launch facilities, and nuclear power plants worldwide.</p>",
            unsafe_allow_html=True,
        )

        st.markdown("**Layer Toggles:**")
        tc1, tc2, tc3, tc4 = st.columns(4)
        show_nukes = tc1.checkbox("Nuclear Powers", True, key="nuke_show")
        show_agencies = tc2.checkbox("Space Agencies", True, key="space_show")
        show_launches = tc3.checkbox("Launch Sites", True, key="launch_show")
        show_plants = tc4.checkbox("Nuclear Plants (Overpass)", False, key="plants_show")

        plant_lat, plant_lon, plant_radius = 48.0, 10.0, 500.0
        if show_plants:
            st.markdown("**Nuclear Plants Search Area:**")
            pc1, pc2, pc3 = st.columns(3)
            plant_lat = pc1.number_input("Plant Search Lat", -90.0, 90.0, 48.0, key="plant_lat")
            plant_lon = pc2.number_input("Plant Search Lon", -180.0, 180.0, 10.0, key="plant_lon")
            plant_radius = pc3.number_input("Radius (km)", 50, 2000, 500, key="plant_rad")

        c1, c2, c3 = st.columns(3)
        c1.metric("Nuclear States", len(NUCLEAR_POWERS))
        c2.metric("Space Agencies", len(SPACE_AGENCIES))
        c3.metric("Launch Sites", len(LAUNCH_SITES))

        with st.spinner("Building Nuclear & Space map..."):
            fmap = _build_nuclear_space_map(
                show_nukes, show_agencies, show_plants, show_launches,
                plant_lat, plant_lon, plant_radius,
            )
        components.html(fmap._repr_html_(), height=600)

        # Legend
        st.markdown("**Legend:**")
        lc1, lc2, lc3, lc4 = st.columns(4)
        lc1.markdown("<span style='color:#ef4444;'>&#9632;</span> Nuclear Powers", unsafe_allow_html=True)
        lc2.markdown("<span style='color:#3b82f6;'>&#9632;</span> Space Agencies", unsafe_allow_html=True)
        lc3.markdown("<span style='color:#f59e0b;'>&#9632;</span> Launch Sites", unsafe_allow_html=True)
        lc4.markdown("<span style='color:#10b981;'>&#9632;</span> Nuclear Plants", unsafe_allow_html=True)

        # Nuclear powers timeline
        st.subheader("Nuclear Weapons Timeline")
        fig, ax = _dark_fig(figsize=(10, 4))
        nuke_names = [n["country"] for n in NUCLEAR_POWERS]
        nuke_years = [n["first_test"] for n in NUCLEAR_POWERS]
        nuke_warheads = [n["warheads"] for n in NUCLEAR_POWERS]
        scatter = ax.scatter(nuke_years, range(len(nuke_names)),
                             s=[w / 10 for w in nuke_warheads],
                             c="#ef4444", alpha=0.7, edgecolors="#2a3550")
        ax.set_yticks(range(len(nuke_names)))
        ax.set_yticklabels(nuke_names)
        ax.set_xlabel("Year of First Nuclear Test")
        ax.set_title("Nuclear Powers Timeline (bubble size = est. warheads)")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Data tables
        tab_n, tab_s, tab_l = st.tabs(["Nuclear Powers", "Space Agencies", "Launch Sites"])
        with tab_n:
            df_n = pd.DataFrame(NUCLEAR_POWERS)
            df_n = df_n[["country", "first_test", "warheads"]]
            df_n.columns = ["Country", "First Test", "Est. Warheads"]
            st.dataframe(df_n, width="stretch")
        with tab_s:
            df_s = pd.DataFrame(SPACE_AGENCIES)
            df_s = df_s[["name", "country", "founded"]]
            df_s.columns = ["Agency", "Country", "Founded"]
            st.dataframe(df_s, width="stretch")
        with tab_l:
            df_l = pd.DataFrame(LAUNCH_SITES)
            df_l = df_l[["name", "country", "lat", "lon"]]
            df_l.columns = ["Site", "Country", "Lat", "Lon"]
            st.dataframe(df_l, width="stretch")

        # Combined download
        all_rows = []
        for n in NUCLEAR_POWERS:
            all_rows.append({"Type": "Nuclear Power", "Name": n["country"],
                             "Detail": f"Test: {n['first_test']}, Warheads: {n['warheads']}"})
        for a in SPACE_AGENCIES:
            all_rows.append({"Type": "Space Agency", "Name": a["name"],
                             "Detail": f"Country: {a['country']}, Founded: {a['founded']}"})
        for l in LAUNCH_SITES:
            all_rows.append({"Type": "Launch Site", "Name": l["name"],
                             "Detail": f"Country: {l['country']}"})
        df_all = pd.DataFrame(all_rows)
        csv = df_all.to_csv(index=False).encode("utf-8")
        st.download_button("Download Nuclear & Space Data CSV", csv,
                           "nuclear_space_data.csv", "text/csv",
                           key="dl_nuke_space")

    # -----------------------------------------------------------------
    # 10. WORLD CUISINE REGIONS
    # -----------------------------------------------------------------
    elif selected_map == "World Cuisine Regions":
        st.markdown(
            "<p style='color:#8b97b0;'>Major culinary regions of the world with signature "
            "dishes, key ingredients, and cultural food traditions.</p>",
            unsafe_allow_html=True,
        )

        show_spice = st.checkbox("Overlay Spice Trade Route", False, key="cuisine_spice")

        c1, c2 = st.columns(2)
        c1.metric("Cuisine Regions", len(CUISINE_REGIONS))
        c2.metric("Spice Route Overlay", "On" if show_spice else "Off")

        fmap = _build_cuisine_map(show_spice)
        components.html(fmap._repr_html_(), height=600)

        # Legend
        st.markdown("**Cuisine Region Legend:**")
        legend_cols = st.columns(4)
        for i, region in enumerate(CUISINE_REGIONS):
            col = legend_cols[i % 4]
            col.markdown(
                f"<span style='color:{region['color']};'>&#9632;</span> "
                f"{region['name']}",
                unsafe_allow_html=True,
            )

        # Details
        st.subheader("Cuisine Region Details")
        rows = []
        for r in CUISINE_REGIONS:
            rows.append({
                "Region": r["name"],
                "Signature Dishes": r["dishes"],
                "Key Ingredients": r["ingredients"],
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Cuisine Regions CSV", csv,
                           "cuisine_regions.csv", "text/csv",
                           key="dl_cuisine")
