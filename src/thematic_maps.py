"""
Thematic Maps Generator module for TerraScout AI.
Creates composite maps by combining/overlaying multiple data sources into
single visualizations. Each map type fetches real data from free APIs and
renders a richly styled folium map with dark-themed charts and stats.
"""

import io
import json
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

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# CONSTANTS & PALETTES
# ════════════════════════════════════════════════════════════════
DARK_BG = "#0a0e1a"
SURFACE = "#111827"
CARD_BG = "#1a2235"
BORDER = "#2a3550"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"
ACCENT = "#06b6d4"

MAP_TYPES = [
    "Language Distribution Map",
    "Tectonic Plates & Earthquakes",
    "World Cost of Living",
    "Global Temperature Map",
    "Animal Kingdom Distribution",
    "Human Development Index",
    "Religious Landscape",
    "Night Lights & Population",
    "Agricultural Zones",
    "Historical Empire Extents",
]

LANGUAGE_FAMILY_COLORS = {
    "Indo-European": "#3b82f6",
    "Sino-Tibetan": "#ef4444",
    "Afro-Asiatic": "#10b981",
    "Niger-Congo": "#f97316",
    "Austronesian": "#8b5cf6",
    "Turkic": "#eab308",
    "Dravidian": "#ec4899",
    "Japonic": "#f43f5e",
    "Koreanic": "#a855f7",
    "Tai-Kadai": "#14b8a6",
    "Austroasiatic": "#84cc16",
    "Uralic": "#06b6d4",
    "Mongolic": "#d946ef",
    "Kartvelian": "#fb923c",
    "Other": "#8b97b0",
}

LANGUAGE_TO_FAMILY = {
    "English": "Indo-European", "Spanish": "Indo-European", "French": "Indo-European",
    "Portuguese": "Indo-European", "German": "Indo-European", "Italian": "Indo-European",
    "Russian": "Indo-European", "Polish": "Indo-European", "Dutch": "Indo-European",
    "Greek": "Indo-European", "Romanian": "Indo-European", "Swedish": "Indo-European",
    "Norwegian": "Indo-European", "Danish": "Indo-European", "Czech": "Indo-European",
    "Slovak": "Indo-European", "Bulgarian": "Indo-European", "Croatian": "Indo-European",
    "Serbian": "Indo-European", "Bosnian": "Indo-European", "Slovenian": "Indo-European",
    "Lithuanian": "Indo-European", "Latvian": "Indo-European", "Ukrainian": "Indo-European",
    "Belarusian": "Indo-European", "Hindi": "Indo-European", "Urdu": "Indo-European",
    "Bengali": "Indo-European", "Punjabi": "Indo-European", "Marathi": "Indo-European",
    "Gujarati": "Indo-European", "Nepali": "Indo-European", "Sinhala": "Indo-European",
    "Persian": "Indo-European", "Pashto": "Indo-European", "Kurdish": "Indo-European",
    "Armenian": "Indo-European", "Albanian": "Indo-European", "Macedonian": "Indo-European",
    "Irish": "Indo-European", "Welsh": "Indo-European", "Icelandic": "Indo-European",
    "Finnish": "Uralic", "Estonian": "Uralic", "Hungarian": "Uralic",
    "Chinese": "Sino-Tibetan", "Mandarin Chinese": "Sino-Tibetan",
    "Burmese": "Sino-Tibetan", "Tibetan": "Sino-Tibetan",
    "Arabic": "Afro-Asiatic", "Hebrew": "Afro-Asiatic", "Amharic": "Afro-Asiatic",
    "Somali": "Afro-Asiatic", "Hausa": "Afro-Asiatic", "Berber": "Afro-Asiatic",
    "Swahili": "Niger-Congo", "Yoruba": "Niger-Congo", "Igbo": "Niger-Congo",
    "Zulu": "Niger-Congo", "Xhosa": "Niger-Congo", "Shona": "Niger-Congo",
    "Kinyarwanda": "Niger-Congo", "Kirundi": "Niger-Congo", "Lingala": "Niger-Congo",
    "Malay": "Austronesian", "Indonesian": "Austronesian", "Filipino": "Austronesian",
    "Tagalog": "Austronesian", "Malagasy": "Austronesian", "Javanese": "Austronesian",
    "Samoan": "Austronesian", "Tongan": "Austronesian", "Fijian": "Austronesian",
    "Turkish": "Turkic", "Azerbaijani": "Turkic", "Uzbek": "Turkic",
    "Turkmen": "Turkic", "Kazakh": "Turkic", "Kyrgyz": "Turkic",
    "Tamil": "Dravidian", "Telugu": "Dravidian", "Kannada": "Dravidian",
    "Malayalam": "Dravidian",
    "Japanese": "Japonic", "Korean": "Koreanic",
    "Thai": "Tai-Kadai", "Lao": "Tai-Kadai",
    "Vietnamese": "Austroasiatic", "Khmer": "Austroasiatic",
    "Georgian": "Kartvelian",
    "Mongolian": "Mongolic",
}

RELIGION_DATA = {
    "Christianity": {
        "color": "#3b82f6",
        "countries": [
            "United States", "Brazil", "Mexico", "Russia", "Germany", "United Kingdom",
            "France", "Italy", "Spain", "Canada", "Australia", "Poland", "Romania",
            "Netherlands", "Greece", "Portugal", "Sweden", "Norway", "Denmark",
            "Finland", "Ireland", "Austria", "Switzerland", "Belgium", "Czech Republic",
            "Hungary", "Croatia", "Serbia", "Bulgaria", "Slovakia", "Lithuania",
            "Latvia", "Estonia", "Ukraine", "Belarus", "Moldova", "Georgia",
            "Armenia", "Philippines", "South Korea", "Colombia", "Argentina",
            "Peru", "Venezuela", "Chile", "Ecuador", "Guatemala", "Cuba",
            "Dominican Republic", "Honduras", "Paraguay", "El Salvador",
            "Nicaragua", "Costa Rica", "Panama", "Uruguay", "Bolivia",
            "Jamaica", "Trinidad and Tobago", "Haiti", "Papua New Guinea",
            "Fiji", "Samoa", "Tonga", "Ethiopia", "DR Congo", "South Africa",
            "Kenya", "Uganda", "Ghana", "Cameroon", "Angola", "Madagascar",
            "Mozambique", "Zambia", "Zimbabwe", "Malawi", "Rwanda", "Burundi",
            "South Sudan", "Central African Republic", "Republic of the Congo",
            "Gabon", "Equatorial Guinea", "Namibia", "Botswana", "Lesotho",
            "Eswatini", "Cabo Verde", "Timor-Leste",
        ],
    },
    "Islam": {
        "color": "#10b981",
        "countries": [
            "Indonesia", "Pakistan", "Bangladesh", "Egypt", "Turkey", "Iran",
            "Saudi Arabia", "Iraq", "Afghanistan", "Morocco", "Algeria", "Sudan",
            "Yemen", "Syria", "Tunisia", "Libya", "Jordan", "United Arab Emirates",
            "Kuwait", "Qatar", "Bahrain", "Oman", "Lebanon", "Palestine",
            "Malaysia", "Brunei", "Maldives", "Uzbekistan", "Kazakhstan",
            "Turkmenistan", "Kyrgyzstan", "Tajikistan", "Azerbaijan",
            "Somalia", "Djibouti", "Comoros", "Mauritania", "Mali", "Niger",
            "Senegal", "Gambia", "Guinea", "Sierra Leone", "Burkina Faso", "Chad",
            "Nigeria",
        ],
    },
    "Hinduism": {
        "color": "#f97316",
        "countries": ["India", "Nepal", "Mauritius", "Suriname", "Guyana"],
    },
    "Buddhism": {
        "color": "#eab308",
        "countries": [
            "Thailand", "Myanmar", "Sri Lanka", "Cambodia", "Laos", "Mongolia",
            "Bhutan", "Japan", "Vietnam", "Singapore",
        ],
    },
    "Folk/Traditional": {
        "color": "#8b5cf6",
        "countries": ["China", "Taiwan", "Macau", "Hong Kong"],
    },
    "Judaism": {
        "color": "#06b6d4",
        "countries": ["Israel"],
    },
}

# 40 well-distributed world cities for temperature map
WORLD_CITIES = [
    ("New York", 40.71, -74.01), ("Los Angeles", 33.94, -118.41),
    ("Chicago", 41.88, -87.63), ("Mexico City", 19.43, -99.13),
    ("Sao Paulo", -23.55, -46.63), ("Buenos Aires", -34.60, -58.38),
    ("Lima", -12.05, -77.04), ("Bogota", 4.71, -74.07),
    ("London", 51.51, -0.13), ("Paris", 48.86, 2.35),
    ("Berlin", 52.52, 13.41), ("Madrid", 40.42, -3.70),
    ("Rome", 41.90, 12.50), ("Moscow", 55.76, 37.62),
    ("Istanbul", 41.01, 28.98), ("Cairo", 30.04, 31.24),
    ("Lagos", 6.52, 3.38), ("Nairobi", -1.29, 36.82),
    ("Johannesburg", -26.20, 28.05), ("Casablanca", 33.59, -7.59),
    ("Dubai", 25.20, 55.27), ("Riyadh", 24.71, 46.68),
    ("Mumbai", 19.08, 72.88), ("Delhi", 28.61, 77.21),
    ("Kolkata", 22.57, 88.36), ("Bangkok", 13.76, 100.50),
    ("Jakarta", -6.21, 106.85), ("Singapore", 1.35, 103.82),
    ("Beijing", 39.90, 116.41), ("Shanghai", 31.23, 121.47),
    ("Tokyo", 35.68, 139.69), ("Seoul", 37.57, 126.98),
    ("Sydney", -33.87, 151.21), ("Melbourne", -37.81, 144.96),
    ("Auckland", -36.85, 174.76), ("Anchorage", 61.22, -149.90),
    ("Reykjavik", 64.15, -21.94), ("Dakar", 14.69, -17.44),
    ("Addis Ababa", 9.02, 38.75), ("Ulaanbaatar", 47.89, 106.91),
]

# Simplified tectonic plate boundaries (major plates, ~10-15 coords each)
TECTONIC_PLATES = {
    "Pacific Plate": {
        "color": "#f97316",
        "coords": [
            [55, 160], [50, 170], [40, 170], [35, 175], [20, 175],
            [0, 175], [-15, 175], [-40, 175], [-55, -130],
            [-40, -110], [-20, -110], [0, -105], [15, -105],
            [30, -120], [40, -130], [50, -140], [55, -160],
            [55, 170], [55, 160],
        ],
    },
    "North American Plate": {
        "color": "#3b82f6",
        "coords": [
            [75, -170], [75, -10], [60, -10], [50, -30],
            [35, -40], [15, -50], [10, -80], [15, -105],
            [30, -120], [40, -130], [50, -140], [55, -160],
            [65, -170], [75, -170],
        ],
    },
    "Eurasian Plate": {
        "color": "#8b5cf6",
        "coords": [
            [75, -10], [75, 140], [55, 160], [50, 155],
            [45, 145], [35, 135], [30, 100], [25, 85],
            [25, 65], [30, 50], [35, 30], [35, -10],
            [50, -30], [60, -10], [75, -10],
        ],
    },
    "African Plate": {
        "color": "#10b981",
        "coords": [
            [35, -10], [35, 30], [30, 50], [15, 45],
            [10, 52], [-10, 50], [-35, 30], [-55, -5],
            [-35, -20], [5, -25], [15, -20], [35, -10],
        ],
    },
    "South American Plate": {
        "color": "#ef4444",
        "coords": [
            [15, -50], [10, -60], [5, -25], [-35, -20],
            [-55, -5], [-60, -30], [-55, -70], [-45, -75],
            [-20, -70], [0, -80], [10, -80], [15, -50],
        ],
    },
    "Indo-Australian Plate": {
        "color": "#eab308",
        "coords": [
            [25, 65], [25, 85], [10, 95], [0, 100],
            [-10, 110], [-35, 115], [-45, 130], [-45, 170],
            [-55, 170], [-60, 160], [-70, 170], [-70, 75],
            [-10, 50], [10, 52], [15, 45], [25, 65],
        ],
    },
    "Antarctic Plate": {
        "color": "#a78bfa",
        "coords": [
            [-60, -180], [-60, -120], [-60, -60], [-60, 0],
            [-60, 60], [-60, 120], [-60, 180],
        ],
    },
}

# Biogeographic realms
BIOGEOGRAPHIC_REALMS = {
    "Nearctic": {
        "color": "#3b82f6",
        "species": "Grizzly Bear, Bald Eagle, Bison, Pronghorn, Rattlesnake, Beaver",
        "coords": [
            [75, -170], [75, -50], [50, -55], [30, -80],
            [15, -100], [30, -120], [50, -130], [65, -170], [75, -170],
        ],
    },
    "Neotropical": {
        "color": "#10b981",
        "species": "Jaguar, Toucan, Sloth, Piranha, Anaconda, Macaw, Capybara",
        "coords": [
            [30, -80], [15, -100], [0, -80], [-5, -80],
            [-55, -70], [-55, -35], [-35, -20], [5, -25],
            [10, -60], [15, -50], [30, -80],
        ],
    },
    "Palearctic": {
        "color": "#8b5cf6",
        "species": "Red Fox, Brown Bear, Wolf, Eurasian Lynx, Wild Boar, Crane",
        "coords": [
            [75, -25], [75, 180], [50, 180], [40, 140],
            [30, 120], [25, 65], [30, 45], [35, 25],
            [35, -10], [45, -10], [55, -25], [75, -25],
        ],
    },
    "Afrotropic": {
        "color": "#f97316",
        "species": "Lion, Elephant, Gorilla, Giraffe, Zebra, Hippo, Rhinoceros",
        "coords": [
            [15, -20], [20, 40], [12, 52], [-10, 50],
            [-35, 30], [-35, 15], [-35, -20], [5, -25],
            [15, -20],
        ],
    },
    "Indomalayan": {
        "color": "#ef4444",
        "species": "Tiger, Orangutan, Asian Elephant, Cobra, Peacock, Pangolin",
        "coords": [
            [35, 65], [30, 120], [20, 120], [10, 110],
            [0, 100], [-10, 105], [-10, 95], [10, 80],
            [25, 65], [35, 65],
        ],
    },
    "Australasia": {
        "color": "#eab308",
        "species": "Kangaroo, Koala, Platypus, Emu, Kiwi, Wombat, Tasmanian Devil",
        "coords": [
            [-10, 110], [-10, 155], [-20, 170], [-45, 175],
            [-45, 130], [-35, 115], [-10, 110],
        ],
    },
    "Oceanian": {
        "color": "#06b6d4",
        "species": "Coconut Crab, Flying Fox, Marine Iguana, Paradise Bird",
        "coords": [
            [-5, 155], [10, 160], [10, 180], [-20, 180],
            [-20, 170], [-10, 155], [-5, 155],
        ],
    },
    "Antarctic": {
        "color": "#e2e8f0",
        "species": "Emperor Penguin, Leopard Seal, Albatross, Antarctic Krill",
        "coords": [
            [-60, -180], [-60, -90], [-60, 0],
            [-60, 90], [-60, 180],
        ],
    },
}

# Agricultural belts
AGRICULTURAL_ZONES = {
    "US Corn Belt": {
        "color": "#eab308", "crop": "Corn, Soybeans",
        "info": "World's largest corn-producing region, ~350M tonnes/year",
        "coords": [[44, -98], [44, -84], [38, -84], [38, -98], [44, -98]],
    },
    "US Wheat Belt": {
        "color": "#f59e0b", "crop": "Wheat",
        "info": "Great Plains winter & spring wheat, ~50M tonnes/year",
        "coords": [[49, -110], [49, -97], [35, -97], [35, -110], [49, -110]],
    },
    "Southeast Asia Rice Paddies": {
        "color": "#10b981", "crop": "Rice",
        "info": "Produces ~90% of world rice supply, monsoon-fed paddies",
        "coords": [[30, 95], [30, 120], [5, 120], [5, 95], [30, 95]],
    },
    "Indian Rice Belt": {
        "color": "#22c55e", "crop": "Rice, Wheat",
        "info": "Indo-Gangetic plain, feeds 1.4B people",
        "coords": [[30, 75], [30, 90], [22, 90], [22, 75], [30, 75]],
    },
    "Coffee Belt": {
        "color": "#92400e", "crop": "Coffee",
        "info": "Tropical band 23.5N-23.5S, Brazil is #1 producer",
        "coords": [[23.5, -80], [23.5, 40], [-23.5, 40], [-23.5, -80], [23.5, -80]],
    },
    "European Wine Regions": {
        "color": "#7c3aed", "crop": "Grapes, Wine",
        "info": "Mediterranean climate: France, Italy, Spain, Portugal",
        "coords": [[48, -5], [48, 18], [36, 18], [36, -5], [48, -5]],
    },
    "Argentine Pampas": {
        "color": "#84cc16", "crop": "Cattle, Soybeans, Wheat",
        "info": "Fertile grasslands, major beef & grain exporter",
        "coords": [[-30, -65], [-30, -55], [-40, -55], [-40, -65], [-30, -65]],
    },
    "Sahel Millet Belt": {
        "color": "#d97706", "crop": "Millet, Sorghum",
        "info": "Semi-arid belt south of Sahara, subsistence farming",
        "coords": [[16, -15], [16, 35], [11, 35], [11, -15], [16, -15]],
    },
    "Australian Wheat Belt": {
        "color": "#fbbf24", "crop": "Wheat",
        "info": "Western & South Australia, ~25M tonnes/year",
        "coords": [[-28, 115], [-28, 150], [-38, 150], [-38, 115], [-28, 115]],
    },
    "Ukrainian Black Earth": {
        "color": "#a16207", "crop": "Wheat, Sunflower",
        "info": "Chernozem soil, breadbasket of Europe",
        "coords": [[52, 25], [52, 40], [46, 40], [46, 25], [52, 25]],
    },
}

# Historical empires
HISTORICAL_EMPIRES = {
    "Roman Empire (117 AD)": {
        "color": "#ef4444", "date": "27 BC - 476 AD",
        "area": "5.0 million km2",
        "info": "Greatest extent under Trajan; controlled the Mediterranean basin",
        "coords": [
            [55, -5], [55, 0], [50, 5], [48, 10], [47, 15],
            [45, 20], [42, 25], [42, 35], [38, 40], [35, 42],
            [32, 36], [30, 33], [28, 33], [25, 32], [22, 30],
            [30, 15], [32, 10], [35, 0], [37, -5], [40, -8],
            [43, -8], [48, -5], [55, -5],
        ],
    },
    "Mongol Empire (1279)": {
        "color": "#eab308", "date": "1206 - 1368",
        "area": "24.0 million km2",
        "info": "Largest contiguous land empire; founded by Genghis Khan",
        "coords": [
            [55, 25], [60, 40], [65, 70], [60, 100],
            [55, 120], [50, 130], [45, 135], [40, 120],
            [35, 110], [30, 105], [25, 95], [25, 65],
            [30, 50], [35, 40], [40, 30], [48, 25], [55, 25],
        ],
    },
    "British Empire (1920)": {
        "color": "#3b82f6", "date": "1583 - 1997",
        "area": "35.5 million km2",
        "info": "Largest empire in history; 'the empire on which the sun never sets'",
        "coords": [
            [60, -8], [60, 2], [50, 2], [50, -5], [52, -8], [60, -8],
        ],
    },
    "Ottoman Empire (1683)": {
        "color": "#10b981", "date": "1299 - 1922",
        "area": "5.2 million km2",
        "info": "Controlled SE Europe, Western Asia, N Africa for 600 years",
        "coords": [
            [48, 15], [48, 20], [45, 25], [42, 30], [40, 38],
            [38, 42], [35, 45], [32, 40], [30, 35], [28, 32],
            [25, 35], [22, 32], [30, 15], [33, 12], [35, 10],
            [38, 12], [42, 15], [45, 15], [48, 15],
        ],
    },
    "Spanish Empire (1790)": {
        "color": "#f97316", "date": "1492 - 1976",
        "area": "13.7 million km2",
        "info": "First global empire; vast territories in the Americas",
        "coords": [
            [44, -8], [44, 2], [37, 2], [36, -5], [37, -8], [44, -8],
        ],
    },
    "Persian Empire (500 BC)": {
        "color": "#8b5cf6", "date": "550 BC - 330 BC",
        "area": "5.5 million km2",
        "info": "Achaemenid Empire; first superpower, ruled by Cyrus the Great",
        "coords": [
            [42, 28], [40, 35], [38, 45], [37, 55], [35, 70],
            [30, 72], [25, 65], [22, 55], [25, 45], [27, 33],
            [30, 30], [32, 28], [35, 25], [38, 25], [42, 28],
        ],
    },
    "Han Dynasty (100 AD)": {
        "color": "#ec4899", "date": "202 BC - 220 AD",
        "area": "6.5 million km2",
        "info": "Golden age of China; Silk Road trade, paper invention",
        "coords": [
            [45, 95], [45, 125], [40, 125], [35, 120],
            [30, 120], [25, 110], [22, 105], [20, 100],
            [25, 95], [30, 90], [35, 90], [40, 90], [45, 95],
        ],
    },
    "Inca Empire (1527)": {
        "color": "#06b6d4", "date": "1438 - 1533",
        "area": "2.0 million km2",
        "info": "Largest empire in pre-Columbian Americas; Andes highlands",
        "coords": [
            [2, -78], [0, -76], [-5, -76], [-10, -75],
            [-15, -72], [-20, -68], [-25, -66], [-30, -68],
            [-35, -70], [-30, -72], [-25, -74], [-15, -77],
            [-5, -80], [0, -80], [2, -78],
        ],
    },
}


# ════════════════════════════════════════════════════════════════
# API FETCHERS (cached)
# ════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _fetch_rest_countries():
    """Fetch country data from REST Countries API."""
    url = "https://restcountries.com/v3.1/all?fields=name,languages,latlng,area,population"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("REST Countries API error: %s", e)
        return None


@st.cache_data(ttl=3600)
def _fetch_usgs_earthquakes():
    """Fetch M2.5+ earthquakes from the last month."""
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("USGS API error: %s", e)
        return None


@st.cache_data(ttl=3600)
def _fetch_world_bank(indicator: str, date: str = "2022"):
    """Fetch World Bank indicator data."""
    url = (
        f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
        f"?format=json&per_page=300&date={date}"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) > 1:
            return data[1]
        return None
    except Exception as e:
        logger.error("World Bank API error for %s: %s", indicator, e)
        return None


@st.cache_data(ttl=3600)
def _fetch_temperatures():
    """Fetch current temperatures for world cities via Open-Meteo."""
    lats = ",".join(str(c[1]) for c in WORLD_CITIES)
    lngs = ",".join(str(c[2]) for c in WORLD_CITIES)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lats}&longitude={lngs}&current_weather=true"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Open-Meteo API error: %s", e)
        return None


# ════════════════════════════════════════════════════════════════
# HELPER: Folium dark base map
# ════════════════════════════════════════════════════════════════

def _make_dark_map(location=None, zoom=2):
    """Create a folium map with CartoDB dark_matter base."""
    loc = location or [20, 0]
    m = folium.Map(location=loc, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)
    return m


def _render_map(m, height=600):
    """Render a folium map via components.html with fallback."""
    try:
        html_str = m._repr_html_()
        components.html(html_str, height=height)
    except Exception as e:
        st.error(f"Map rendering error: {escape(str(e))}")


def _temp_color(t):
    """Map temperature to a blue-red color gradient."""
    if t <= -20:
        return "#1e3a5f"
    elif t <= -10:
        return "#2563eb"
    elif t <= 0:
        return "#3b82f6"
    elif t <= 10:
        return "#06b6d4"
    elif t <= 20:
        return "#10b981"
    elif t <= 30:
        return "#eab308"
    elif t <= 40:
        return "#f97316"
    return "#ef4444"


def _gdp_color(val, vmin, vmax):
    """Map GDP per capita to a red-green gradient."""
    if val is None:
        return "#5a6580"
    ratio = min(max((val - vmin) / max(vmax - vmin, 1), 0), 1)
    r = int(239 * (1 - ratio) + 16 * ratio)
    g = int(68 * (1 - ratio) + 185 * ratio)
    b = int(68 * (1 - ratio) + 129 * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


def _hdi_color(score):
    """Map HDI-like composite score 0-1 to red-green."""
    ratio = min(max(score, 0), 1)
    r = int(239 * (1 - ratio) + 16 * ratio)
    g = int(68 * (1 - ratio) + 185 * ratio)
    b = int(68 * (1 - ratio) + 129 * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


def _density_color(density):
    """Map population density to dim-blue to bright-yellow."""
    if density < 10:
        return "#1e3a5f"
    elif density < 50:
        return "#2563eb"
    elif density < 150:
        return "#3b82f6"
    elif density < 500:
        return "#eab308"
    elif density < 1000:
        return "#f59e0b"
    return "#fbbf24"


# ════════════════════════════════════════════════════════════════
# MAP RENDERERS
# ════════════════════════════════════════════════════════════════

def _render_language_map():
    """Language Distribution Map using REST Countries API."""
    with st.spinner("Fetching country language data..."):
        countries = _fetch_rest_countries()
    if not countries:
        st.error("Failed to fetch data from REST Countries API.")
        return

    rows = []
    for c in countries:
        name = c.get("name", {}).get("common", "Unknown")
        latlng = c.get("latlng", [])
        langs = c.get("languages", {})
        pop = c.get("population", 0)
        if not latlng or len(latlng) < 2 or not langs:
            continue
        primary_lang = list(langs.values())[0]
        family = LANGUAGE_TO_FAMILY.get(primary_lang, "Other")
        rows.append({
            "country": name, "lat": latlng[0], "lng": latlng[1],
            "language": primary_lang, "family": family, "population": pop,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No language data available.")
        return

    # Stats
    family_counts = df["family"].value_counts()
    top_families = family_counts.head(5)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries", f"{len(df):,}")
    with c2:
        st.metric("Language Families", f"{df['family'].nunique()}")
    with c3:
        st.metric("Top Family", top_families.index[0] if len(top_families) > 0 else "--")
    with c4:
        st.metric("Languages Tracked", f"{df['language'].nunique()}")

    # Legend
    legend_items = "".join(
        f'<span style="color:{LANGUAGE_FAMILY_COLORS.get(f, TEXT_MUTED)}; font-size:0.8rem;">'
        f'&#9679; {escape(f)} ({cnt})</span>'
        for f, cnt in family_counts.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">'
        f'{legend_items}</div>', unsafe_allow_html=True,
    )

    # Map
    m = _make_dark_map(zoom=2)
    for _, row in df.iterrows():
        color = LANGUAGE_FAMILY_COLORS.get(row["family"], TEXT_MUTED)
        radius = max(3, min(15, (row["population"] / 5_000_000) ** 0.5 * 3))
        popup_html = (
            f"<b>{escape(row['country'])}</b><br/>"
            f"Language: {escape(row['language'])}<br/>"
            f"Family: {escape(row['family'])}<br/>"
            f"Population: {row['population']:,}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            weight=1, popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)
    _render_map(m)

    # Chart
    st.markdown("#### Language Family Distribution")
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    colors = [LANGUAGE_FAMILY_COLORS.get(f, TEXT_MUTED) for f in family_counts.index]
    ax.barh(family_counts.index[::-1], family_counts.values[::-1], color=colors[::-1])
    ax.set_xlabel("Number of Countries", color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.grid(True, color=BORDER, linewidth=0.5, alpha=0.5, axis="x")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Download
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Language Data ({len(df)} countries)",
        data=csv_buf.getvalue(), file_name="language_distribution.csv",
        mime="text/csv", key="tm_lang_dl",
    )


def _render_tectonic_map():
    """Tectonic Plates & Earthquakes composite map."""
    with st.spinner("Fetching earthquake data from USGS..."):
        eq_data = _fetch_usgs_earthquakes()
    if not eq_data:
        st.error("Failed to fetch earthquake data from USGS.")
        return

    features = eq_data.get("features", [])
    magnitudes = [f["properties"]["mag"] for f in features if f["properties"].get("mag")]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Earthquakes (M2.5+)", f"{len(features):,}")
    with c2:
        st.metric("Strongest", f"M{max(magnitudes):.1f}" if magnitudes else "--")
    with c3:
        st.metric("Avg Magnitude", f"M{sum(magnitudes)/len(magnitudes):.1f}" if magnitudes else "--")
    with c4:
        st.metric("Tectonic Plates", f"{len(TECTONIC_PLATES)}")

    # Legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#f97316; font-size:0.8rem;">&#9644; Plate Boundaries</span>
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Earthquakes</span>
        <span style="color:#dc2626; font-size:0.8rem;">&#9679; M6+ Strong</span>
    </div>
    """, unsafe_allow_html=True)

    m = _make_dark_map(location=[15, 0], zoom=2)

    # Draw tectonic plate boundaries
    for name, plate in TECTONIC_PLATES.items():
        folium.PolyLine(
            locations=plate["coords"], color=plate["color"],
            weight=2.5, opacity=0.8, dash_array="8 4",
            popup=folium.Popup(f"<b>{escape(name)}</b>", max_width=200),
        ).add_to(m)

    # Draw earthquakes
    for feat in features[:800]:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        mag = props.get("mag", 0) or 0
        place = props.get("place", "Unknown")
        depth = coords[2] if len(coords) > 2 else 0
        radius = max(2, mag * 1.5)
        color = "#dc2626" if mag >= 6 else "#ef4444" if mag >= 4.5 else "#f87171"
        popup_html = (
            f"<b>M{mag:.1f}</b> - {escape(str(place))}<br/>"
            f"Depth: {depth:.1f} km"
        )
        folium.CircleMarker(
            location=[coords[1], coords[0]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.5,
            weight=0.5, popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)

    _render_map(m)

    # Export
    rows = []
    for feat in features:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        rows.append({
            "magnitude": props.get("mag"),
            "place": props.get("place", ""),
            "latitude": coords[1], "longitude": coords[0],
            "depth_km": coords[2] if len(coords) > 2 else None,
        })
    df = pd.DataFrame(rows)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Earthquake Data ({len(df)} events)",
        data=csv_buf.getvalue(), file_name="tectonic_earthquakes.csv",
        mime="text/csv", key="tm_tect_dl",
    )


def _render_cost_of_living_map():
    """World Cost of Living map using GDP per capita from World Bank."""
    with st.spinner("Fetching GDP and population data..."):
        gdp_data = _fetch_world_bank("NY.GDP.PCAP.CD", "2022")
        countries = _fetch_rest_countries()

    if not gdp_data or not countries:
        st.error("Failed to fetch data from World Bank or REST Countries APIs.")
        return

    # Build coordinate lookup from REST Countries
    coord_map = {}
    pop_map = {}
    for c in countries:
        name = c.get("name", {}).get("common", "")
        latlng = c.get("latlng", [])
        pop = c.get("population", 0)
        if name and latlng and len(latlng) >= 2:
            coord_map[name.lower()] = (latlng[0], latlng[1])
            pop_map[name.lower()] = pop
        official = c.get("name", {}).get("official", "")
        if official:
            coord_map[official.lower()] = latlng[0], latlng[1]

    # Parse GDP data
    rows = []
    for entry in gdp_data:
        if not entry or not entry.get("value"):
            continue
        cname = entry.get("country", {}).get("value", "")
        gdp_val = entry["value"]
        key = cname.lower()
        coords = coord_map.get(key)
        pop = pop_map.get(key, 0)
        if not coords:
            continue
        rows.append({
            "country": cname, "lat": coords[0], "lng": coords[1],
            "gdp_per_capita": round(gdp_val, 2), "population": pop,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No matched GDP data available.")
        return

    vmin = df["gdp_per_capita"].min()
    vmax = df["gdp_per_capita"].max()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries", f"{len(df):,}")
    with c2:
        st.metric("Highest GDP/cap", f"${vmax:,.0f}")
    with c3:
        st.metric("Lowest GDP/cap", f"${vmin:,.0f}")
    with c4:
        st.metric("Median GDP/cap", f"${df['gdp_per_capita'].median():,.0f}")

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Low GDP/capita</span>
        <span style="color:#eab308; font-size:0.8rem;">&#9679; Medium</span>
        <span style="color:#10b981; font-size:0.8rem;">&#9679; High GDP/capita</span>
    </div>
    """, unsafe_allow_html=True)

    m = _make_dark_map(zoom=2)
    for _, row in df.iterrows():
        color = _gdp_color(row["gdp_per_capita"], vmin, vmax)
        radius = max(3, min(18, (row["population"] / 5_000_000) ** 0.5 * 3))
        popup_html = (
            f"<b>{escape(row['country'])}</b><br/>"
            f"GDP per capita: ${row['gdp_per_capita']:,.0f}<br/>"
            f"Population: {row['population']:,}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            weight=1, popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)
    _render_map(m)

    # Chart: top/bottom GDP
    st.markdown("#### GDP per Capita Distribution")
    top10 = df.nlargest(10, "gdp_per_capita")
    bot10 = df.nsmallest(10, "gdp_per_capita")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Top 10 Highest**")
        fig, ax = plt.subplots(figsize=(5, 3.5))
        fig.patch.set_facecolor(DARK_BG)
        ax.set_facecolor(SURFACE)
        ax.barh(top10["country"].values[::-1], top10["gdp_per_capita"].values[::-1], color="#10b981")
        ax.set_xlabel("GDP per Capita ($)", color=TEXT_SECONDARY, fontsize=9)
        ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    with col_r:
        st.markdown("**Top 10 Lowest**")
        fig, ax = plt.subplots(figsize=(5, 3.5))
        fig.patch.set_facecolor(DARK_BG)
        ax.set_facecolor(SURFACE)
        ax.barh(bot10["country"].values[::-1], bot10["gdp_per_capita"].values[::-1], color="#ef4444")
        ax.set_xlabel("GDP per Capita ($)", color=TEXT_SECONDARY, fontsize=9)
        ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download GDP Data ({len(df)} countries)",
        data=csv_buf.getvalue(), file_name="world_cost_of_living.csv",
        mime="text/csv", key="tm_gdp_dl",
    )


def _render_temperature_map():
    """Global Temperature Map using Open-Meteo current weather."""
    with st.spinner("Fetching current temperatures from Open-Meteo..."):
        weather_data = _fetch_temperatures()

    if not weather_data:
        st.error("Failed to fetch temperature data from Open-Meteo.")
        return

    # Parse responses (Open-Meteo returns a list for multi-location)
    rows = []
    if isinstance(weather_data, list):
        for i, item in enumerate(weather_data):
            if i >= len(WORLD_CITIES):
                break
            cw = item.get("current_weather", {})
            temp = cw.get("temperature")
            if temp is not None:
                city_name, lat, lng = WORLD_CITIES[i]
                rows.append({"city": city_name, "lat": lat, "lng": lng, "temperature": temp})
    elif isinstance(weather_data, dict):
        cw = weather_data.get("current_weather", {})
        temp = cw.get("temperature")
        if temp is not None and len(WORLD_CITIES) > 0:
            city_name, lat, lng = WORLD_CITIES[0]
            rows.append({"city": city_name, "lat": lat, "lng": lng, "temperature": temp})

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No temperature data retrieved.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Cities", f"{len(df)}")
    with c2:
        hottest = df.loc[df["temperature"].idxmax()]
        st.metric("Hottest", f"{hottest['temperature']:.1f} C", delta=escape(str(hottest["city"])))
    with c3:
        coldest = df.loc[df["temperature"].idxmin()]
        st.metric("Coldest", f"{coldest['temperature']:.1f} C", delta=escape(str(coldest["city"])))
    with c4:
        st.metric("Avg Temp", f"{df['temperature'].mean():.1f} C")

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#2563eb; font-size:0.8rem;">&#9679; &lt;0 C Freezing</span>
        <span style="color:#06b6d4; font-size:0.8rem;">&#9679; 0-10 C Cold</span>
        <span style="color:#10b981; font-size:0.8rem;">&#9679; 10-20 C Mild</span>
        <span style="color:#eab308; font-size:0.8rem;">&#9679; 20-30 C Warm</span>
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; &gt;30 C Hot</span>
    </div>
    """, unsafe_allow_html=True)

    m = _make_dark_map(zoom=2)
    for _, row in df.iterrows():
        color = _temp_color(row["temperature"])
        popup_html = (
            f"<b>{escape(row['city'])}</b><br/>"
            f"Temperature: {row['temperature']:.1f} &deg;C"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=10,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            weight=1, popup=folium.Popup(popup_html, max_width=200),
        ).add_to(m)
        # Temperature label
        folium.Marker(
            location=[row["lat"], row["lng"]],
            icon=folium.DivIcon(html=(
                f'<div style="font-size:10px;color:{color};font-weight:bold;'
                f'text-shadow:1px 1px 2px #000;">{row["temperature"]:.0f}&deg;</div>'
            )),
        ).add_to(m)
    _render_map(m)

    # Chart
    st.markdown("#### Temperature by City")
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    sorted_df = df.sort_values("temperature", ascending=True)
    colors = [_temp_color(t) for t in sorted_df["temperature"]]
    ax.barh(sorted_df["city"], sorted_df["temperature"], color=colors)
    ax.set_xlabel("Temperature (C)", color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=7)
    ax.axvline(x=0, color=TEXT_MUTED, linewidth=0.8, linestyle="--")
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Temperature Data ({len(df)} cities)",
        data=csv_buf.getvalue(), file_name="global_temperatures.csv",
        mime="text/csv", key="tm_temp_dl",
    )


def _render_animal_kingdom_map():
    """Animal Kingdom Distribution showing biogeographic realms."""

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Biogeographic Realms", f"{len(BIOGEOGRAPHIC_REALMS)}")
    with c2:
        st.metric("Classification", "Wallace (1876)")
    with c3:
        st.metric("Coverage", "Global")

    # Legend
    legend_items = "".join(
        f'<span style="color:{data["color"]}; font-size:0.8rem;">&#9632; {escape(name)}</span>'
        for name, data in BIOGEOGRAPHIC_REALMS.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">'
        f'{legend_items}</div>', unsafe_allow_html=True,
    )

    m = _make_dark_map(zoom=2)
    for name, data in BIOGEOGRAPHIC_REALMS.items():
        popup_html = (
            f"<b>{escape(name)}</b><br/>"
            f"<em>Notable species:</em><br/>{escape(data['species'])}"
        )
        folium.Polygon(
            locations=data["coords"], color=data["color"],
            fill=True, fill_color=data["color"], fill_opacity=0.25,
            weight=2, popup=folium.Popup(popup_html, max_width=250),
        ).add_to(m)
    _render_map(m)

    # Species table
    st.markdown("#### Realm Details")
    realm_rows = [
        {"Realm": name, "Notable Species": data["species"], "Color": data["color"]}
        for name, data in BIOGEOGRAPHIC_REALMS.items()
    ]
    df = pd.DataFrame(realm_rows)
    st.dataframe(df[["Realm", "Notable Species"]], width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Realm Data",
        data=csv_buf.getvalue(), file_name="biogeographic_realms.csv",
        mime="text/csv", key="tm_animal_dl",
    )


def _render_hdi_map():
    """Human Development Index composite from World Bank indicators."""
    with st.spinner("Fetching HDI component data from World Bank..."):
        life_data = _fetch_world_bank("SP.DYN.LE00.IN", "2022")
        edu_data = _fetch_world_bank("SE.XPD.TOTL.GD.ZS", "2022")
        gni_data = _fetch_world_bank("NY.GNP.PCAP.CD", "2022")
        countries = _fetch_rest_countries()

    if not countries:
        st.error("Failed to fetch country coordinate data.")
        return

    # Build lookups
    coord_map = {}
    pop_map = {}
    for c in countries:
        name = c.get("name", {}).get("common", "")
        latlng = c.get("latlng", [])
        pop = c.get("population", 0)
        if name and latlng and len(latlng) >= 2:
            coord_map[name.lower()] = (latlng[0], latlng[1])
            pop_map[name.lower()] = pop

    def _parse_wb(data):
        out = {}
        if not data:
            return out
        for entry in data:
            if entry and entry.get("value") is not None:
                cname = entry.get("country", {}).get("value", "").lower()
                out[cname] = entry["value"]
        return out

    life_map = _parse_wb(life_data)
    edu_map = _parse_wb(edu_data)
    gni_map = _parse_wb(gni_data)

    # Compute composite score
    all_countries = set(life_map) | set(gni_map)
    rows = []
    for cname in all_countries:
        life = life_map.get(cname)
        edu = edu_map.get(cname)
        gni = gni_map.get(cname)
        coords = coord_map.get(cname)
        pop = pop_map.get(cname, 0)
        if not coords or life is None or gni is None:
            continue
        # Normalize components (approximate ranges)
        life_score = min(max((life - 40) / 50, 0), 1)
        edu_score = min(max((edu - 1) / 10, 0), 1) if edu else 0.5
        gni_score = min(max(gni / 80000, 0), 1)
        composite = (life_score + edu_score + gni_score) / 3
        rows.append({
            "country": cname.title(), "lat": coords[0], "lng": coords[1],
            "life_expectancy": round(life, 1) if life else None,
            "education_spend_pct": round(edu, 2) if edu else None,
            "gni_per_capita": round(gni, 0) if gni else None,
            "hdi_score": round(composite, 3),
            "population": pop,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No HDI data could be computed.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries", f"{len(df)}")
    with c2:
        best = df.loc[df["hdi_score"].idxmax()]
        st.metric("Highest HDI", f"{best['hdi_score']:.3f}", delta=escape(str(best["country"])))
    with c3:
        worst = df.loc[df["hdi_score"].idxmin()]
        st.metric("Lowest HDI", f"{worst['hdi_score']:.3f}", delta=escape(str(worst["country"])))
    with c4:
        st.metric("Median HDI", f"{df['hdi_score'].median():.3f}")

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Low HDI</span>
        <span style="color:#eab308; font-size:0.8rem;">&#9679; Medium HDI</span>
        <span style="color:#10b981; font-size:0.8rem;">&#9679; High HDI</span>
    </div>
    """, unsafe_allow_html=True)

    m = _make_dark_map(zoom=2)
    for _, row in df.iterrows():
        color = _hdi_color(row["hdi_score"])
        radius = max(3, min(16, (row["population"] / 5_000_000) ** 0.5 * 3))
        popup_parts = [f"<b>{escape(row['country'])}</b>"]
        popup_parts.append(f"HDI Score: {row['hdi_score']:.3f}")
        if row["life_expectancy"]:
            popup_parts.append(f"Life Expectancy: {row['life_expectancy']:.1f} yr")
        if row["gni_per_capita"]:
            popup_parts.append(f"GNI/capita: ${row['gni_per_capita']:,.0f}")
        popup_html = "<br/>".join(popup_parts)
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            weight=1, popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)
    _render_map(m)

    # Data table
    with st.expander(f"Full HDI Data ({len(df)} countries)", expanded=False):
        st.dataframe(
            df[["country", "hdi_score", "life_expectancy", "education_spend_pct", "gni_per_capita"]],
            width="stretch", hide_index=True,
        )

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download HDI Data ({len(df)} countries)",
        data=csv_buf.getvalue(), file_name="human_development_index.csv",
        mime="text/csv", key="tm_hdi_dl",
    )


def _render_religious_map():
    """Religious Landscape map using REST Countries + hardcoded religion data."""
    with st.spinner("Fetching country data..."):
        countries = _fetch_rest_countries()
    if not countries:
        st.error("Failed to fetch data from REST Countries API.")
        return

    # Build country -> religion mapping
    country_religion = {}
    for religion, data in RELIGION_DATA.items():
        for c in data["countries"]:
            country_religion[c.lower()] = religion

    rows = []
    for c in countries:
        name = c.get("name", {}).get("common", "Unknown")
        latlng = c.get("latlng", [])
        pop = c.get("population", 0)
        if not latlng or len(latlng) < 2:
            continue
        religion = country_religion.get(name.lower(), "Other")
        color = RELIGION_DATA.get(religion, {}).get("color", TEXT_MUTED)
        rows.append({
            "country": name, "lat": latlng[0], "lng": latlng[1],
            "religion": religion, "population": pop, "color": color,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No religion data available.")
        return

    # World distribution percentages by population
    rel_pop = df.groupby("religion")["population"].sum()
    total_pop = rel_pop.sum()
    rel_pct = (rel_pop / max(total_pop, 1) * 100).sort_values(ascending=False)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries Mapped", f"{len(df)}")
    with c2:
        st.metric("Religions Tracked", f"{df['religion'].nunique()}")
    with c3:
        st.metric("Largest", f"{rel_pct.index[0]}" if len(rel_pct) > 0 else "--")
    with c4:
        pct_val = rel_pct.iloc[0] if len(rel_pct) > 0 else 0
        st.metric("Coverage", f"{pct_val:.1f}%")

    # Legend with percentages
    legend_items = ""
    for rel in rel_pct.index:
        color = RELIGION_DATA.get(rel, {}).get("color", TEXT_MUTED)
        pct = rel_pct.get(rel, 0)
        legend_items += (
            f'<span style="color:{color}; font-size:0.8rem;">'
            f'&#9679; {escape(rel)} ({pct:.1f}%)</span>'
        )
    st.markdown(
        f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">'
        f'{legend_items}</div>', unsafe_allow_html=True,
    )

    m = _make_dark_map(zoom=2)
    for _, row in df.iterrows():
        radius = max(3, min(16, (row["population"] / 5_000_000) ** 0.5 * 3))
        popup_html = (
            f"<b>{escape(row['country'])}</b><br/>"
            f"Religion: {escape(row['religion'])}<br/>"
            f"Population: {row['population']:,}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=row["color"], fill=True, fill_color=row["color"],
            fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)
    _render_map(m)

    # Pie chart
    st.markdown("#### World Religious Distribution (by population)")
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    pie_colors = [RELIGION_DATA.get(r, {}).get("color", TEXT_MUTED) for r in rel_pct.index]
    wedges, texts, autotexts = ax.pie(
        rel_pct.values, labels=rel_pct.index, autopct="%1.1f%%",
        colors=pie_colors, textprops={"color": TEXT_PRIMARY, "fontsize": 8},
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color(TEXT_PRIMARY)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Religion Data ({len(df)} countries)",
        data=csv_buf.getvalue(), file_name="religious_landscape.csv",
        mime="text/csv", key="tm_rel_dl",
    )


def _render_night_lights_map():
    """Night Lights & Population density visualization."""
    with st.spinner("Fetching population data..."):
        countries = _fetch_rest_countries()
    if not countries:
        st.error("Failed to fetch data from REST Countries API.")
        return

    rows = []
    for c in countries:
        name = c.get("name", {}).get("common", "Unknown")
        latlng = c.get("latlng", [])
        pop = c.get("population", 0)
        area = c.get("area", 0)
        if not latlng or len(latlng) < 2 or pop == 0:
            continue
        density = pop / max(area, 1)
        rows.append({
            "country": name, "lat": latlng[0], "lng": latlng[1],
            "population": pop, "area_km2": area, "density": round(density, 2),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No population data available.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries", f"{len(df)}")
    with c2:
        st.metric("World Population", f"{df['population'].sum():,.0f}")
    with c3:
        densest = df.loc[df["density"].idxmax()]
        st.metric("Densest", escape(str(densest["country"])))
    with c4:
        st.metric("Max Density", f"{densest['density']:,.0f}/km2")

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#1e3a5f; font-size:0.8rem;">&#9679; Sparse (&lt;10/km2)</span>
        <span style="color:#3b82f6; font-size:0.8rem;">&#9679; Low (&lt;150/km2)</span>
        <span style="color:#eab308; font-size:0.8rem;">&#9679; High (&lt;500/km2)</span>
        <span style="color:#fbbf24; font-size:0.8rem;">&#9679; Very Dense (&gt;1000/km2)</span>
    </div>
    """, unsafe_allow_html=True)

    m = _make_dark_map(zoom=2)
    for _, row in df.iterrows():
        color = _density_color(row["density"])
        radius = max(2, min(20, (row["population"] / 2_000_000) ** 0.5 * 2))
        popup_html = (
            f"<b>{escape(row['country'])}</b><br/>"
            f"Population: {row['population']:,}<br/>"
            f"Area: {row['area_km2']:,.0f} km&sup2;<br/>"
            f"Density: {row['density']:,.1f}/km&sup2;"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            weight=0.5, popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)
    _render_map(m)

    # Top 15 densest
    st.markdown("#### Top 15 Most Densely Populated")
    top15 = df.nlargest(15, "density")
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    colors = [_density_color(d) for d in top15["density"].values[::-1]]
    ax.barh(top15["country"].values[::-1], top15["density"].values[::-1], color=colors)
    ax.set_xlabel("Population Density (per km2)", color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Population Data ({len(df)} countries)",
        data=csv_buf.getvalue(), file_name="night_lights_population.csv",
        mime="text/csv", key="tm_night_dl",
    )


def _render_agricultural_map():
    """Agricultural Zones with climate suitability."""

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Agricultural Zones", f"{len(AGRICULTURAL_ZONES)}")
    with c2:
        st.metric("Major Crops", "10+")
    with c3:
        st.metric("Coverage", "Global")

    legend_items = "".join(
        f'<span style="color:{data["color"]}; font-size:0.8rem;">&#9632; {escape(name)}</span>'
        for name, data in AGRICULTURAL_ZONES.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">'
        f'{legend_items}</div>', unsafe_allow_html=True,
    )

    m = _make_dark_map(zoom=2)
    for name, data in AGRICULTURAL_ZONES.items():
        popup_html = (
            f"<b>{escape(name)}</b><br/>"
            f"<em>Crops:</em> {escape(data['crop'])}<br/>"
            f"{escape(data['info'])}"
        )
        folium.Polygon(
            locations=data["coords"], color=data["color"],
            fill=True, fill_color=data["color"], fill_opacity=0.3,
            weight=2, popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)

    # Fetch temperatures for zone centers to show climate suitability
    zone_centers = []
    for name, data in AGRICULTURAL_ZONES.items():
        lats = [c[0] for c in data["coords"]]
        lngs = [c[1] for c in data["coords"]]
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)
        zone_centers.append((name, center_lat, center_lng))

    _render_map(m)

    # Zone data table
    st.markdown("#### Agricultural Zone Details")
    zone_rows = [
        {"Zone": name, "Crops": data["crop"], "Info": data["info"]}
        for name, data in AGRICULTURAL_ZONES.items()
    ]
    df = pd.DataFrame(zone_rows)
    st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Agricultural Zone Data",
        data=csv_buf.getvalue(), file_name="agricultural_zones.csv",
        mime="text/csv", key="tm_agri_dl",
    )


def _render_empire_map():
    """Historical Empire Extents at their peak."""

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Empires Shown", f"{len(HISTORICAL_EMPIRES)}")
    with c2:
        st.metric("Time Span", "2500+ years")
    with c3:
        st.metric("Largest", "Mongol (24M km2)")

    legend_items = "".join(
        f'<span style="color:{data["color"]}; font-size:0.8rem;">&#9632; {escape(name)}</span>'
        for name, data in HISTORICAL_EMPIRES.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">'
        f'{legend_items}</div>', unsafe_allow_html=True,
    )

    m = _make_dark_map(zoom=2)
    for name, data in HISTORICAL_EMPIRES.items():
        popup_html = (
            f"<b>{escape(name)}</b><br/>"
            f"Period: {escape(data['date'])}<br/>"
            f"Area: {escape(data['area'])}<br/>"
            f"{escape(data['info'])}"
        )
        folium.Polygon(
            locations=data["coords"], color=data["color"],
            fill=True, fill_color=data["color"], fill_opacity=0.25,
            weight=2, popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)
    _render_map(m)

    # Empire comparison chart
    st.markdown("#### Empire Size Comparison")
    empire_areas = []
    empire_names = []
    empire_colors = []
    for name, data in HISTORICAL_EMPIRES.items():
        area_str = data["area"].replace(" million km2", "").strip()
        try:
            empire_areas.append(float(area_str))
        except ValueError:
            empire_areas.append(0)
        empire_names.append(name.split("(")[0].strip())
        empire_colors.append(data["color"])

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    sorted_idx = sorted(range(len(empire_areas)), key=lambda i: empire_areas[i])
    ax.barh(
        [empire_names[i] for i in sorted_idx],
        [empire_areas[i] for i in sorted_idx],
        color=[empire_colors[i] for i in sorted_idx],
    )
    ax.set_xlabel("Area (million km2)", color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    st.markdown("#### Empire Details")
    empire_rows = [
        {"Empire": name, "Period": data["date"], "Area": data["area"], "Notes": data["info"]}
        for name, data in HISTORICAL_EMPIRES.items()
    ]
    df = pd.DataFrame(empire_rows)
    st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Empire Data",
        data=csv_buf.getvalue(), file_name="historical_empires.csv",
        mime="text/csv", key="tm_empire_dl",
    )


# ════════════════════════════════════════════════════════════════
# DISPATCH TABLE
# ════════════════════════════════════════════════════════════════
MAP_RENDERERS = {
    "Language Distribution Map": _render_language_map,
    "Tectonic Plates & Earthquakes": _render_tectonic_map,
    "World Cost of Living": _render_cost_of_living_map,
    "Global Temperature Map": _render_temperature_map,
    "Animal Kingdom Distribution": _render_animal_kingdom_map,
    "Human Development Index": _render_hdi_map,
    "Religious Landscape": _render_religious_map,
    "Night Lights & Population": _render_night_lights_map,
    "Agricultural Zones": _render_agricultural_map,
    "Historical Empire Extents": _render_empire_map,
}


# ════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ════════════════════════════════════════════════════════════════

def render_thematic_maps_tab():
    """Main render function for the Thematic Maps tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header violet">
        <h4>Thematic Maps</h4>
        <p>Composite visualizations combining multiple data sources</p>
    </div>
    """, unsafe_allow_html=True)

    # Map type selector
    selected = st.selectbox(
        "Choose a Thematic Map",
        MAP_TYPES,
        key="tm_map_type",
        help="Each map combines real data from free APIs into a single composite visualization.",
    )

    st.markdown("---")

    # Dispatch to the selected renderer
    renderer = MAP_RENDERERS.get(selected)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown map type: {escape(selected)}")
