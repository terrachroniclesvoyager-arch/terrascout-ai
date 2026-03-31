"""
Historical Maps Explorer module for TerraScout AI.
Overlays historical maps on modern basemaps, visualizes empire boundaries
across time, and plots major historical events with interactive markers.

Sources (all free, no API key):
  - NLS (National Library of Scotland) tile servers
  - OpenHistoricalMap community tiles
  - Stamen Watercolor via Stadia Maps
  - Esri World Imagery (modern comparison)
  - Hardcoded empire polygons & historical event coordinates
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
# HISTORICAL TILE LAYERS
# ═══════════════════════════════════════════════════════════════

HISTORICAL_LAYERS = {
    "NLS OS 1-inch 1885-1900": {
        "url": "https://nls-0.tileserver.com/fpsUZbULUfT/{z}/{x}/{y}.png",
        "attr": "National Library of Scotland",
        "era": "1885-1900",
        "desc": "Ordnance Survey 1-inch to the mile, Great Britain",
        "max_zoom": 16,
    },
    "NLS OS 6-inch 1888-1913": {
        "url": "https://nls-2.tileserver.com/fpsUZba/{z}/{x}/{y}.png",
        "attr": "National Library of Scotland",
        "era": "1888-1913",
        "desc": "Ordnance Survey 6-inch, England and Wales",
        "max_zoom": 17,
    },
    "Roy Military Survey 1747-55": {
        "url": "https://nls-0.tileserver.com/gdTp/{z}/{x}/{y}.png",
        "attr": "National Library of Scotland",
        "era": "1747-1755",
        "desc": "William Roy military survey of Scotland",
        "max_zoom": 14,
    },
    "OpenHistoricalMap": {
        "url": "https://vtiles.openhistoricalmap.org/maps/ohm/{z}/{x}/{y}.png",
        "attr": "OpenHistoricalMap contributors",
        "era": "Community",
        "desc": "Community-sourced historical map data worldwide",
        "max_zoom": 18,
    },
    "Stamen Watercolor": {
        "url": "https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg",
        "attr": "Stamen Design / Stadia Maps",
        "era": "Artistic",
        "desc": "Artistic watercolor rendering evoking historical cartography",
        "max_zoom": 16,
    },
    "Esri World Imagery (Modern)": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri",
        "era": "Modern",
        "desc": "Modern satellite/aerial imagery for comparison",
        "max_zoom": 19,
    },
}

# ═══════════════════════════════════════════════════════════════
# LOCATION PRESETS
# ═══════════════════════════════════════════════════════════════

LOCATION_PRESETS = {
    "Custom": None,
    "London": {"lat": 51.5074, "lon": -0.1278, "zoom": 13},
    "Edinburgh": {"lat": 55.9533, "lon": -3.1883, "zoom": 13},
    "Glasgow": {"lat": 55.8642, "lon": -4.2518, "zoom": 13},
    "Paris": {"lat": 48.8566, "lon": 2.3522, "zoom": 13},
    "Rome": {"lat": 41.9028, "lon": 12.4964, "zoom": 13},
    "Athens": {"lat": 37.9838, "lon": 23.7275, "zoom": 13},
    "Istanbul": {"lat": 41.0082, "lon": 28.9784, "zoom": 13},
    "New York": {"lat": 40.7128, "lon": -74.0060, "zoom": 12},
    "Washington DC": {"lat": 38.9072, "lon": -77.0369, "zoom": 13},
    "Boston": {"lat": 42.3601, "lon": -71.0589, "zoom": 13},
    "Cairo": {"lat": 30.0444, "lon": 31.2357, "zoom": 12},
    "Jerusalem": {"lat": 31.7683, "lon": 35.2137, "zoom": 13},
    "Beijing": {"lat": 39.9042, "lon": 116.4074, "zoom": 12},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "zoom": 12},
    "Vienna": {"lat": 48.2082, "lon": 16.3738, "zoom": 13},
    "Berlin": {"lat": 52.5200, "lon": 13.4050, "zoom": 13},
    "Madrid": {"lat": 40.4168, "lon": -3.7038, "zoom": 13},
    "Amsterdam": {"lat": 52.3676, "lon": 4.9041, "zoom": 13},
    "Venice": {"lat": 45.4408, "lon": 12.3155, "zoom": 14},
    "Florence": {"lat": 43.7696, "lon": 11.2558, "zoom": 14},
}

# ═══════════════════════════════════════════════════════════════
# EMPIRE DATA — simplified polygon boundaries & metadata
# ═══════════════════════════════════════════════════════════════

EMPIRES = {
    "Roman Empire (117 AD)": {
        "color": "#ef4444",
        "year": "117 AD",
        "area_km2": "5,000,000",
        "population": "~70 million",
        "capital": "Rome",
        "desc": "At its greatest extent under Emperor Trajan, the Roman Empire encircled the Mediterranean.",
        "coords": [
            [51.5, -5.0], [51.0, 2.0], [48.0, 8.0], [47.0, 16.0],
            [44.0, 22.0], [44.0, 28.0], [42.0, 33.0], [38.0, 40.0],
            [37.0, 44.0], [33.0, 44.0], [31.0, 36.0], [30.0, 33.0],
            [31.5, 25.0], [30.5, 30.0], [26.0, 30.0], [24.0, 33.0],
            [32.0, 13.0], [37.0, 10.0], [36.0, 0.0], [35.5, -5.0],
            [37.0, -9.0], [43.0, -9.0], [48.0, -5.0], [51.5, -5.0],
        ],
    },
    "Byzantine Empire (555 AD)": {
        "color": "#8b5cf6",
        "year": "555 AD",
        "area_km2": "3,500,000",
        "population": "~26 million",
        "capital": "Constantinople",
        "desc": "Under Justinian I, the Eastern Roman Empire reconquered much of the western Mediterranean.",
        "coords": [
            [45.0, 12.0], [44.0, 18.0], [42.0, 24.0], [43.0, 28.0],
            [41.5, 33.0], [38.0, 40.0], [37.0, 43.0], [34.0, 42.0],
            [31.0, 36.0], [30.0, 33.0], [31.5, 25.0], [32.0, 13.0],
            [37.0, 10.0], [36.5, 3.0], [37.0, -5.0], [40.0, -2.0],
            [39.0, 3.0], [42.0, 9.0], [45.0, 12.0],
        ],
    },
    "Mongol Empire (1279 AD)": {
        "color": "#f59e0b",
        "year": "1279 AD",
        "area_km2": "24,000,000",
        "population": "~110 million",
        "capital": "Karakorum / Khanbaliq (Beijing)",
        "desc": "The largest contiguous land empire in history, spanning from Korea to Hungary.",
        "coords": [
            [50.0, 22.0], [55.0, 30.0], [60.0, 40.0], [62.0, 55.0],
            [65.0, 70.0], [63.0, 90.0], [58.0, 105.0], [55.0, 120.0],
            [50.0, 130.0], [42.0, 130.0], [35.0, 120.0], [30.0, 110.0],
            [25.0, 100.0], [22.0, 100.0], [25.0, 90.0], [28.0, 75.0],
            [25.0, 60.0], [30.0, 50.0], [33.0, 44.0], [38.0, 40.0],
            [42.0, 33.0], [44.0, 28.0], [50.0, 22.0],
        ],
    },
    "Ottoman Empire (1683 AD)": {
        "color": "#10b981",
        "year": "1683 AD",
        "area_km2": "5,200,000",
        "population": "~30 million",
        "capital": "Constantinople (Istanbul)",
        "desc": "At its height before the Siege of Vienna, the Ottoman Empire spanned three continents.",
        "coords": [
            [48.0, 16.0], [47.0, 20.0], [45.0, 22.0], [44.0, 28.0],
            [42.0, 30.0], [38.0, 42.0], [36.0, 44.0], [33.0, 44.0],
            [30.0, 40.0], [26.0, 36.0], [22.0, 36.0], [15.0, 42.0],
            [12.0, 44.0], [24.0, 33.0], [31.5, 25.0], [32.5, 22.0],
            [33.0, 12.0], [37.0, 10.0], [35.5, 0.0], [37.0, -2.0],
            [40.0, 0.0], [42.0, 8.0], [41.5, 16.0], [44.0, 16.0],
            [48.0, 16.0],
        ],
    },
    "British Empire (1920 AD)": {
        "color": "#ec4899",
        "year": "1920 AD",
        "area_km2": "35,500,000",
        "population": "~412 million",
        "capital": "London",
        "desc": "The largest empire in history by total land area, spanning every inhabited continent.",
        "territories": [
            {"name": "British Isles", "coords": [
                [58.0, -7.0], [58.0, 2.0], [51.0, 2.0], [50.0, -5.5],
                [52.0, -10.5], [55.5, -8.0], [58.0, -7.0],
            ]},
            {"name": "India", "coords": [
                [35.0, 70.0], [35.0, 80.0], [28.0, 90.0], [22.0, 92.0],
                [8.0, 80.0], [8.0, 73.0], [20.0, 68.0], [25.0, 62.0],
                [30.0, 65.0], [35.0, 70.0],
            ]},
            {"name": "Australia", "coords": [
                [-12.0, 130.0], [-12.0, 142.0], [-18.0, 148.0],
                [-28.0, 154.0], [-38.0, 148.0], [-38.0, 140.0],
                [-35.0, 136.0], [-32.0, 130.0], [-22.0, 114.0],
                [-12.0, 130.0],
            ]},
            {"name": "Canada", "coords": [
                [70.0, -140.0], [70.0, -60.0], [50.0, -55.0],
                [43.0, -65.0], [42.0, -83.0], [49.0, -95.0],
                [49.0, -123.0], [55.0, -130.0], [60.0, -140.0],
                [70.0, -140.0],
            ]},
            {"name": "East Africa", "coords": [
                [5.0, 34.0], [5.0, 42.0], [-1.0, 42.0], [-11.0, 40.0],
                [-11.0, 34.0], [-1.0, 30.0], [5.0, 34.0],
            ]},
            {"name": "Southern Africa", "coords": [
                [-18.0, 25.0], [-18.0, 33.0], [-27.0, 33.0],
                [-35.0, 28.0], [-34.0, 18.0], [-28.0, 16.0],
                [-22.0, 14.0], [-18.0, 25.0],
            ]},
            {"name": "Egypt & Sudan", "coords": [
                [31.5, 25.0], [31.5, 35.0], [22.0, 37.0], [10.0, 35.0],
                [10.0, 25.0], [22.0, 25.0], [31.5, 25.0],
            ]},
        ],
    },
    "Spanish Empire (1790 AD)": {
        "color": "#f97316",
        "year": "1790 AD",
        "area_km2": "13,700,000",
        "population": "~40 million (colonies)",
        "capital": "Madrid",
        "desc": "At its peak, the Spanish Empire included vast territories in the Americas and the Philippines.",
        "territories": [
            {"name": "Spain", "coords": [
                [43.5, -9.0], [43.5, 3.0], [40.0, 4.0], [37.0, -2.0],
                [36.0, -5.5], [37.0, -9.0], [43.5, -9.0],
            ]},
            {"name": "Central & South America", "coords": [
                [32.0, -117.0], [30.0, -100.0], [22.0, -85.0],
                [10.0, -75.0], [5.0, -77.0], [-5.0, -80.0],
                [-18.0, -70.0], [-35.0, -71.0], [-42.0, -65.0],
                [-55.0, -68.0], [-55.0, -72.0], [-42.0, -73.0],
                [-18.0, -76.0], [-5.0, -81.0], [10.0, -80.0],
                [20.0, -105.0], [32.0, -117.0],
            ]},
            {"name": "Philippines", "coords": [
                [18.0, 117.0], [18.0, 127.0], [5.0, 127.0],
                [5.0, 117.0], [18.0, 117.0],
            ]},
        ],
    },
    "Persian / Achaemenid Empire (500 BC)": {
        "color": "#06b6d4",
        "year": "500 BC",
        "area_km2": "5,500,000",
        "population": "~50 million",
        "capital": "Persepolis",
        "desc": "The Achaemenid Persian Empire was the largest empire of the ancient world under Darius I.",
        "coords": [
            [42.0, 28.0], [42.0, 33.0], [40.0, 44.0], [38.0, 50.0],
            [40.0, 55.0], [40.0, 65.0], [38.0, 72.0], [30.0, 72.0],
            [25.0, 64.0], [24.0, 58.0], [26.0, 50.0], [30.0, 48.0],
            [28.0, 45.0], [22.0, 40.0], [15.0, 43.0], [24.0, 35.0],
            [30.0, 32.0], [31.5, 25.0], [32.5, 20.0], [35.0, 24.0],
            [38.0, 27.0], [42.0, 28.0],
        ],
    },
    "Han Dynasty (100 AD)": {
        "color": "#3b82f6",
        "year": "100 AD",
        "area_km2": "6,500,000",
        "population": "~60 million",
        "capital": "Chang'an (Xi'an)",
        "desc": "One of China's greatest dynasties, the Han extended control deep into Central and Southeast Asia.",
        "coords": [
            [42.0, 80.0], [50.0, 90.0], [50.0, 105.0], [50.0, 120.0],
            [42.0, 128.0], [40.0, 122.0], [35.0, 120.0], [30.0, 122.0],
            [25.0, 120.0], [22.0, 110.0], [18.0, 108.0], [22.0, 100.0],
            [25.0, 98.0], [28.0, 95.0], [30.0, 90.0], [35.0, 82.0],
            [38.0, 76.0], [42.0, 80.0],
        ],
    },
    "Inca Empire (1527 AD)": {
        "color": "#a855f7",
        "year": "1527 AD",
        "area_km2": "2,000,000",
        "population": "~12 million",
        "capital": "Cusco",
        "desc": "The Inca Empire (Tawantinsuyu) stretched along the western coast of South America.",
        "coords": [
            [2.0, -78.0], [0.0, -80.0], [-5.0, -81.0], [-8.0, -79.0],
            [-14.0, -76.0], [-18.0, -70.0], [-22.0, -68.0],
            [-30.0, -70.0], [-35.0, -71.0], [-35.0, -68.0],
            [-30.0, -65.0], [-22.0, -63.0], [-18.0, -65.0],
            [-14.0, -69.0], [-8.0, -74.0], [-2.0, -76.0], [2.0, -78.0],
        ],
    },
    "Aztec Empire (1519 AD)": {
        "color": "#14b8a6",
        "year": "1519 AD",
        "area_km2": "220,000",
        "population": "~6 million",
        "capital": "Tenochtitlan (Mexico City)",
        "desc": "The Aztec Triple Alliance dominated central Mexico before the Spanish conquest.",
        "coords": [
            [21.5, -100.0], [21.5, -97.0], [20.0, -96.5],
            [18.5, -96.0], [16.0, -96.5], [16.0, -99.0],
            [17.0, -101.0], [18.5, -102.0], [20.0, -103.0],
            [21.5, -100.0],
        ],
    },
    "Mali Empire (1312 AD)": {
        "color": "#d97706",
        "year": "1312 AD",
        "area_km2": "1,200,000",
        "population": "~20 million",
        "capital": "Niani",
        "desc": "Under Mansa Musa, the Mali Empire was one of the wealthiest states in the medieval world.",
        "coords": [
            [18.0, -16.0], [18.0, -6.0], [20.0, 0.0], [18.0, 4.0],
            [14.0, 4.0], [10.0, 2.0], [8.0, -2.0], [8.0, -8.0],
            [10.0, -12.0], [12.0, -16.0], [14.0, -17.0], [18.0, -16.0],
        ],
    },
    "Mughal Empire (1700 AD)": {
        "color": "#38bdf8",
        "year": "1700 AD",
        "area_km2": "4,000,000",
        "population": "~150 million",
        "capital": "Delhi / Agra",
        "desc": "At its zenith under Aurangzeb, the Mughal Empire controlled nearly all of the Indian subcontinent.",
        "coords": [
            [36.0, 67.0], [36.0, 75.0], [35.0, 78.0], [30.0, 80.0],
            [28.0, 88.0], [22.0, 92.0], [18.0, 85.0], [12.0, 80.0],
            [8.0, 77.0], [10.0, 73.0], [15.0, 73.0], [20.0, 68.0],
            [25.0, 62.0], [30.0, 63.0], [34.0, 64.0], [36.0, 67.0],
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# HISTORICAL EVENTS DATA
# ═══════════════════════════════════════════════════════════════

ANCIENT_WONDERS = [
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342,
     "year": "2560 BC", "status": "Still standing",
     "desc": "The oldest and only surviving ancient wonder. Built as a tomb for Pharaoh Khufu."},
    {"name": "Hanging Gardens of Babylon", "lat": 32.5355, "lon": 44.4275,
     "year": "600 BC", "status": "Destroyed",
     "desc": "Legendary terraced gardens, possibly built by Nebuchadnezzar II. Existence debated."},
    {"name": "Statue of Zeus at Olympia", "lat": 37.6381, "lon": 21.6300,
     "year": "435 BC", "status": "Destroyed by fire, 5th century AD",
     "desc": "A giant ivory and gold statue by sculptor Phidias, inside the Temple of Zeus."},
    {"name": "Temple of Artemis at Ephesus", "lat": 37.9497, "lon": 27.3639,
     "year": "550 BC", "status": "Destroyed 262 AD",
     "desc": "A Greek temple dedicated to Artemis, rebuilt three times before its final destruction."},
    {"name": "Mausoleum at Halicarnassus", "lat": 37.0380, "lon": 27.4243,
     "year": "351 BC", "status": "Destroyed by earthquakes, 12th-15th century",
     "desc": "Tomb built for Mausolus, satrap of Caria. Origin of the word 'mausoleum'."},
    {"name": "Colossus of Rhodes", "lat": 36.4510, "lon": 28.2278,
     "year": "280 BC", "status": "Destroyed by earthquake, 226 BC",
     "desc": "A bronze statue of the sun god Helios, approximately 33 meters tall."},
    {"name": "Lighthouse of Alexandria", "lat": 31.2139, "lon": 29.8856,
     "year": "280 BC", "status": "Destroyed by earthquakes, 1303-1480 AD",
     "desc": "The Pharos of Alexandria guided sailors for nearly 1,600 years."},
]

MAJOR_BATTLES = [
    {"name": "Battle of Thermopylae", "lat": 38.7962, "lon": 22.5367,
     "year": "480 BC", "century": -5,
     "desc": "300 Spartans and allies held the pass against the Persian army of Xerxes I."},
    {"name": "Battle of Gaugamela", "lat": 36.5600, "lon": 43.4500,
     "year": "331 BC", "century": -4,
     "desc": "Alexander the Great decisively defeated Darius III of Persia."},
    {"name": "Battle of Cannae", "lat": 41.3050, "lon": 16.1325,
     "year": "216 BC", "century": -3,
     "desc": "Hannibal's masterpiece double envelopment annihilated a larger Roman army."},
    {"name": "Battle of Actium", "lat": 38.9500, "lon": 20.7180,
     "year": "31 BC", "century": -1,
     "desc": "Octavian defeated Mark Antony and Cleopatra, establishing the Roman Empire."},
    {"name": "Battle of Tours", "lat": 46.7916, "lon": 0.6933,
     "year": "732 AD", "century": 8,
     "desc": "Charles Martel halted the northward advance of the Umayyad Caliphate into Europe."},
    {"name": "Battle of Hastings", "lat": 50.9144, "lon": 0.4874,
     "year": "1066 AD", "century": 11,
     "desc": "William the Conqueror defeated King Harold II, beginning the Norman conquest of England."},
    {"name": "Fall of Constantinople", "lat": 41.0082, "lon": 28.9784,
     "year": "1453 AD", "century": 15,
     "desc": "Ottoman Sultan Mehmed II conquered the Byzantine capital, ending the Roman Empire."},
    {"name": "Battle of Lepanto", "lat": 38.3372, "lon": 21.0958,
     "year": "1571 AD", "century": 16,
     "desc": "Holy League fleet defeated the Ottoman navy in the last major galley battle."},
    {"name": "Battle of Waterloo", "lat": 50.6803, "lon": 4.4119,
     "year": "1815 AD", "century": 19,
     "desc": "Wellington and Blucher defeated Napoleon, ending his rule and the Napoleonic Wars."},
    {"name": "Battle of Gettysburg", "lat": 39.8109, "lon": -77.2275,
     "year": "1863 AD", "century": 19,
     "desc": "Turning point of the American Civil War; Union forces repelled Lee's invasion."},
    {"name": "Battle of the Somme", "lat": 49.9986, "lon": 2.6928,
     "year": "1916 AD", "century": 20,
     "desc": "One of WWI's bloodiest battles with over a million total casualties."},
    {"name": "Battle of Stalingrad", "lat": 48.7080, "lon": 44.5133,
     "year": "1942-43 AD", "century": 20,
     "desc": "Turning point of WWII in Europe; Soviet forces destroyed the German 6th Army."},
    {"name": "D-Day (Normandy)", "lat": 49.3600, "lon": -0.8800,
     "year": "1944 AD", "century": 20,
     "desc": "Allied amphibious invasion of Nazi-occupied France, the largest seaborne invasion in history."},
]

EXPLORATION_ROUTES = {
    "Columbus 1st Voyage (1492)": {
        "color": "#ef4444",
        "year": "1492",
        "desc": "Christopher Columbus sailed from Spain to the Caribbean, believing he had reached Asia.",
        "coords": [
            [37.0, -7.0], [28.5, -17.0], [28.0, -25.0], [25.0, -40.0],
            [22.0, -55.0], [20.0, -65.0], [24.0, -74.5],
        ],
    },
    "Magellan Circumnavigation (1519-22)": {
        "color": "#8b5cf6",
        "year": "1519-1522",
        "desc": "First expedition to circumnavigate the globe, though Magellan died en route.",
        "coords": [
            [36.7, -6.3], [28.0, -16.0], [0.0, -30.0], [-23.0, -43.0],
            [-52.0, -70.0], [-52.0, -75.0], [-33.0, -90.0], [-20.0, -110.0],
            [0.0, -140.0], [10.0, -170.0], [10.0, 145.0], [10.0, 125.0],
            [-5.0, 110.0], [-10.0, 80.0], [-20.0, 50.0], [-35.0, 20.0],
            [0.0, -10.0], [36.7, -6.3],
        ],
    },
    "Marco Polo Route (1271-95)": {
        "color": "#f59e0b",
        "year": "1271-1295",
        "desc": "Marco Polo's overland journey from Venice to the court of Kublai Khan in China.",
        "coords": [
            [45.4, 12.3], [41.0, 29.0], [37.0, 36.0], [33.0, 44.0],
            [30.0, 52.0], [35.0, 59.0], [37.0, 67.0], [38.0, 72.0],
            [36.0, 76.0], [40.0, 80.0], [42.0, 88.0], [40.0, 100.0],
            [40.0, 112.0], [40.0, 116.5],
        ],
    },
    "Silk Road (Main Route)": {
        "color": "#10b981",
        "year": "~200 BC - 1400 AD",
        "desc": "Ancient trade network connecting East Asia to the Mediterranean via Central Asia.",
        "coords": [
            [34.0, 109.0], [36.0, 104.0], [38.0, 100.0], [40.0, 94.0],
            [42.0, 88.0], [41.0, 80.0], [40.0, 72.0], [38.0, 66.0],
            [36.0, 58.0], [33.0, 52.0], [33.0, 44.0], [36.0, 36.0],
            [37.0, 30.0], [39.0, 27.0], [41.0, 29.0],
        ],
    },
    "Vasco da Gama (1497-99)": {
        "color": "#06b6d4",
        "year": "1497-1499",
        "desc": "First European to reach India by sea, opening the Cape Route.",
        "coords": [
            [38.7, -9.1], [28.0, -16.0], [15.0, -18.0], [0.0, -5.0],
            [-15.0, 5.0], [-34.0, 18.0], [-30.0, 32.0], [-15.0, 40.0],
            [-5.0, 42.0], [5.0, 50.0], [11.5, 43.0], [15.0, 55.0],
            [11.0, 76.0],
        ],
    },
    "Zheng He Voyages (1405-33)": {
        "color": "#ec4899",
        "year": "1405-1433",
        "desc": "Chinese treasure fleet explored Southeast Asia, India, Arabia, and East Africa.",
        "coords": [
            [32.0, 119.0], [22.0, 114.0], [10.0, 106.0], [1.0, 104.0],
            [-6.0, 106.0], [-8.0, 110.0], [5.0, 80.0], [10.0, 76.0],
            [12.0, 55.0], [5.0, 45.0], [-2.0, 41.0], [-6.0, 39.5],
        ],
    },
}

ARCHAEOLOGICAL_SITES = [
    {"name": "Pompeii", "lat": 40.7509, "lon": 14.4869,
     "year": "79 AD (destroyed)", "century": 1,
     "desc": "Roman city preserved by volcanic ash from the eruption of Mount Vesuvius."},
    {"name": "Troy", "lat": 39.9574, "lon": 26.2388,
     "year": "~3000 BC - 500 AD", "century": -30,
     "desc": "Ancient city in modern Turkey, famous from Homer's Iliad."},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450,
     "year": "~1450 AD", "century": 15,
     "desc": "Inca citadel set high in the Andes Mountains of Peru."},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670,
     "year": "~1150 AD", "century": 12,
     "desc": "Largest religious monument in the world, originally a Hindu temple for the Khmer Empire."},
    {"name": "Petra", "lat": 30.3285, "lon": 35.4444,
     "year": "~300 BC", "century": -3,
     "desc": "Rock-cut Nabataean city in Jordan, famous for its rose-red facades."},
    {"name": "Great Wall of China (Badaling)", "lat": 40.3540, "lon": 116.0060,
     "year": "~7th century BC onward", "century": -7,
     "desc": "Series of fortifications stretching thousands of kilometers across northern China."},
    {"name": "Colosseum (Rome)", "lat": 41.8902, "lon": 12.4922,
     "year": "80 AD", "century": 1,
     "desc": "Largest ancient amphitheatre, symbol of Imperial Rome, hosted gladiatorial games."},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262,
     "year": "~3000 BC", "century": -30,
     "desc": "Prehistoric stone circle in England, purpose debated: astronomical observatory or ritual site."},
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678,
     "year": "~600-900 AD", "century": 7,
     "desc": "Major Maya city in the Yucatan; El Castillo pyramid is an iconic landmark."},
    {"name": "Mohenjo-daro", "lat": 27.3290, "lon": 68.1389,
     "year": "~2500 BC", "century": -25,
     "desc": "One of the largest settlements of the ancient Indus Valley Civilization."},
    {"name": "Giza Necropolis", "lat": 29.9792, "lon": 31.1342,
     "year": "~2580 BC", "century": -26,
     "desc": "Complex of pyramids, the Great Sphinx, and ancient tombs on the Giza plateau."},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438,
     "year": "~100 BC - 550 AD", "century": -1,
     "desc": "Massive Mesoamerican city with the Pyramid of the Sun and Moon."},
    {"name": "Persepolis", "lat": 29.9342, "lon": 52.8906,
     "year": "~515 BC", "century": -6,
     "desc": "Ceremonial capital of the Achaemenid Persian Empire, destroyed by Alexander."},
    {"name": "Ephesus", "lat": 37.9392, "lon": 27.3411,
     "year": "~10th century BC", "century": -10,
     "desc": "Ancient Greek and later Roman city; home of the Temple of Artemis."},
    {"name": "Tikal", "lat": 17.2220, "lon": -89.6237,
     "year": "~400 BC - 900 AD", "century": -4,
     "desc": "One of the most powerful Maya city-states, deep in the Guatemalan jungle."},
    {"name": "Borobudur", "lat": -7.6079, "lon": 110.2038,
     "year": "~800 AD", "century": 9,
     "desc": "Largest Buddhist temple in the world, located in central Java, Indonesia."},
    {"name": "Great Zimbabwe", "lat": -20.2674, "lon": 30.9338,
     "year": "~1100-1450 AD", "century": 11,
     "desc": "Medieval stone city in southern Africa, capital of the Kingdom of Zimbabwe."},
    {"name": "Mesa Verde", "lat": 37.1839, "lon": -108.4887,
     "year": "~600-1300 AD", "century": 6,
     "desc": "Ancestral Puebloan cliff dwellings in Colorado, USA."},
]

# Event categories with colors
EVENT_CATEGORIES = {
    "Ancient Wonders": {"color": "#f59e0b", "icon": "star"},
    "Major Battles": {"color": "#ef4444", "icon": "fire"},
    "Exploration Routes": {"color": "#8b5cf6", "icon": "ship"},
    "Archaeological Sites": {"color": "#10b981", "icon": "landmark"},
}


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _build_overlay_map(layer_key: str, lat: float, lon: float,
                       zoom: int, opacity: float) -> folium.Map:
    """Build a folium map with a historical tile overlay."""
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)

    # Dark base layer
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Modern Dark Base",
    ).add_to(m)

    # Historical overlay
    layer_info = HISTORICAL_LAYERS[layer_key]
    folium.TileLayer(
        tiles=layer_info["url"],
        attr=layer_info["attr"],
        name=layer_key,
        overlay=True,
        opacity=opacity,
        max_zoom=layer_info.get("max_zoom", 18),
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def _build_empire_map(empire_key: str, show_borders: bool) -> folium.Map:
    """Build a folium map with an empire polygon overlay."""
    emp = EMPIRES[empire_key]
    color = emp["color"]

    # Determine map center from coordinates
    if "coords" in emp:
        all_coords = emp["coords"]
    else:
        all_coords = []
        for t in emp.get("territories", []):
            all_coords.extend(t["coords"])

    if not all_coords:
        return folium.Map(location=[30, 0], zoom_start=3, tiles=None)

    center_lat = sum(c[0] for c in all_coords) / len(all_coords)
    center_lon = sum(c[1] for c in all_coords) / len(all_coords)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=3, tiles=None)

    # Dark base
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    if show_borders:
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png",
            attr="CartoDB Labels",
            name="Modern Labels",
            overlay=True,
        ).add_to(m)

    # Draw polygon(s)
    popup_text = (
        f"<div style='max-width:250px;'>"
        f"<strong>{escape(empire_key)}</strong><br/>"
        f"<span style='font-size:0.8rem;'>{escape(emp['desc'][:200])}</span><br/>"
        f"<span style='font-size:0.75rem; color:#888;'>"
        f"Capital: {escape(emp['capital'])} | Area: {escape(emp['area_km2'])} km2"
        f"</span></div>"
    )

    if "coords" in emp:
        folium.Polygon(
            locations=emp["coords"],
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.25,
            weight=2,
            popup=folium.Popup(popup_text, max_width=270),
            tooltip=empire_key,
        ).add_to(m)
    else:
        for terr in emp.get("territories", []):
            terr_popup = (
                f"<div style='max-width:200px;'>"
                f"<strong>{escape(terr['name'])}</strong><br/>"
                f"<span style='font-size:0.8rem;'>{escape(empire_key)}</span></div>"
            )
            folium.Polygon(
                locations=terr["coords"],
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.25,
                weight=2,
                popup=folium.Popup(terr_popup, max_width=220),
                tooltip=terr["name"],
            ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def _century_label(century: int) -> str:
    """Convert century number to label string."""
    if century < 0:
        return f"{abs(century)}th century BC"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(century % 10, "th")
    if 11 <= century % 100 <= 13:
        suffix = "th"
    return f"{century}{suffix} century AD"


# ═══════════════════════════════════════════════════════════════
# RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_historical_maps_tab():
    """Main render function for the Historical Maps Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>Historical Maps Explorer</h4>
        <p>Ancient maps, empire boundaries, and historical events on modern maps</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio(
        "Explorer Mode",
        ["Historical Map Overlay", "Empire Timeline", "Historical Events Map"],
        horizontal=True,
        key="hist_mode",
    )

    st.markdown("---")

    # ══════════════════════════════════════════════════════════
    # MODE 1: Historical Map Overlay
    # ══════════════════════════════════════════════════════════
    if mode == "Historical Map Overlay":
        _render_overlay_mode()

    # ══════════════════════════════════════════════════════════
    # MODE 2: Empire Timeline
    # ══════════════════════════════════════════════════════════
    elif mode == "Empire Timeline":
        _render_empire_mode()

    # ══════════════════════════════════════════════════════════
    # MODE 3: Historical Events Map
    # ══════════════════════════════════════════════════════════
    elif mode == "Historical Events Map":
        _render_events_mode()


# ──────────────────────────────────────────────────────────────
# MODE 1: Historical Map Overlay
# ──────────────────────────────────────────────────────────────

def _render_overlay_mode():
    st.markdown("#### Historical Map Overlay")

    col_layer, col_preset = st.columns([1, 1])
    with col_layer:
        layer_key = st.selectbox(
            "Historical Map Layer",
            list(HISTORICAL_LAYERS.keys()),
            key="hist_layer",
        )
    with col_preset:
        preset_name = st.selectbox(
            "Location Preset",
            list(LOCATION_PRESETS.keys()),
            key="hist_preset",
        )

    layer_info = HISTORICAL_LAYERS[layer_key]
    st.markdown(
        f'<div style="color:#8b97b0; font-size:0.85rem; margin-bottom:0.5rem;">'
        f'Era: <span style="color:#f59e0b;">{escape(layer_info["era"])}</span> | '
        f'{escape(layer_info["desc"])}</div>',
        unsafe_allow_html=True,
    )

    # Location controls
    col1, col2, col3 = st.columns([1, 1, 1])
    default_lat = 51.5074
    default_lon = -0.1278
    default_zoom = 13
    if preset_name != "Custom" and LOCATION_PRESETS.get(preset_name):
        p = LOCATION_PRESETS[preset_name]
        default_lat = p["lat"]
        default_lon = p["lon"]
        default_zoom = p["zoom"]

    with col1:
        map_lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                                  min_value=-90.0, max_value=90.0, key="hist_lat")
    with col2:
        map_lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                                  min_value=-180.0, max_value=180.0, key="hist_lon")
    with col3:
        map_zoom = st.slider("Zoom Level", 2, 18, default_zoom, key="hist_zoom")

    opacity = st.slider("Historical Layer Opacity", 0, 100, 70,
                         key="hist_opacity", help="Adjust transparency of the historical overlay") / 100.0

    comparison = st.checkbox("Side-by-side comparison mode", key="hist_compare",
                             help="Show historical and modern maps side by side")

    st.markdown("---")

    if comparison:
        st.markdown("#### Side-by-Side: Historical vs. Modern")
        col_hist, col_mod = st.columns(2)
        with col_hist:
            st.markdown(
                f'<div style="text-align:center; color:#f59e0b; font-weight:600; '
                f'margin-bottom:0.3rem;">{escape(layer_key)}</div>',
                unsafe_allow_html=True,
            )
            m_hist = _build_overlay_map(layer_key, map_lat, map_lon, map_zoom, opacity)
            components.html(m_hist._repr_html_(), height=450)
        with col_mod:
            st.markdown(
                '<div style="text-align:center; color:#06b6d4; font-weight:600; '
                'margin-bottom:0.3rem;">Modern Satellite</div>',
                unsafe_allow_html=True,
            )
            m_mod = folium.Map(location=[map_lat, map_lon], zoom_start=map_zoom, tiles=None)
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri", name="Satellite",
            ).add_to(m_mod)
            folium.LayerControl().add_to(m_mod)
            components.html(m_mod._repr_html_(), height=450)
    else:
        st.markdown("#### Historical Map View")
        m = _build_overlay_map(layer_key, map_lat, map_lon, map_zoom, opacity)
        components.html(m._repr_html_(), height=550)

    # Stats
    st.markdown("---")
    st.markdown("#### Layer Information")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Layer", layer_key[:25])
    c2.metric("Era", layer_info["era"])
    c3.metric("Source", layer_info["attr"][:20])
    c4.metric("Max Zoom", layer_info.get("max_zoom", 18))

    # Layer catalog table
    with st.expander("All Available Historical Layers", expanded=False):
        rows = []
        for name, info in HISTORICAL_LAYERS.items():
            rows.append({
                "Layer": name,
                "Era": info["era"],
                "Source": info["attr"],
                "Description": info["desc"],
                "Max Zoom": info.get("max_zoom", 18),
            })
        df_layers = pd.DataFrame(rows)
        st.dataframe(df_layers, width="stretch", hide_index=True)


# ──────────────────────────────────────────────────────────────
# MODE 2: Empire Timeline
# ──────────────────────────────────────────────────────────────

def _render_empire_mode():
    st.markdown("#### Empire Timeline")

    empire_key = st.selectbox(
        "Select Empire / Dynasty",
        list(EMPIRES.keys()),
        key="hist_empire",
    )

    emp = EMPIRES[empire_key]

    # Info panel
    st.markdown(
        f'<div style="background:rgba(15,23,42,0.65); border:1px solid #2a3550; '
        f'border-radius:12px; padding:1rem; margin-bottom:1rem; '
        f'backdrop-filter:blur(16px);">'
        f'<div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.5rem;">'
        f'<div style="width:14px; height:14px; border-radius:50%; background:{emp["color"]};"></div>'
        f'<span style="color:#e8ecf4; font-weight:700; font-size:1.1rem;">{escape(empire_key)}</span>'
        f'</div>'
        f'<div style="color:#8b97b0; font-size:0.9rem; margin-bottom:0.5rem;">{escape(emp["desc"])}</div>'
        f'<div style="display:flex; gap:1.5rem; flex-wrap:wrap; color:#5a6580; font-size:0.8rem;">'
        f'<span>Capital: <span style="color:#06b6d4;">{escape(emp["capital"])}</span></span>'
        f'<span>Year: <span style="color:#f59e0b;">{escape(emp["year"])}</span></span>'
        f'<span>Area: <span style="color:#10b981;">{escape(emp["area_km2"])} km&sup2;</span></span>'
        f'<span>Population: <span style="color:#ec4899;">{escape(emp["population"])}</span></span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Year", emp["year"])
    c2.metric("Area (km2)", emp["area_km2"])
    c3.metric("Population", emp["population"])
    c4.metric("Capital", emp["capital"][:20])

    show_borders = st.checkbox("Show modern country borders / labels", value=True,
                                key="hist_borders")

    st.markdown("---")
    st.markdown("#### Empire Territory Map")

    m = _build_empire_map(empire_key, show_borders)
    components.html(m._repr_html_(), height=550)

    # Comparison chart: empire areas
    st.markdown("---")
    st.markdown("#### Empire Size Comparison")

    empire_names = []
    empire_areas = []
    empire_colors = []
    for name, data in EMPIRES.items():
        empire_names.append(name.split("(")[0].strip()[:25])
        area_str = data["area_km2"].replace(",", "")
        try:
            empire_areas.append(int(area_str))
        except ValueError:
            empire_areas.append(0)
        empire_colors.append(data["color"])

    # Sort by area
    sorted_indices = sorted(range(len(empire_areas)), key=lambda i: empire_areas[i], reverse=True)
    empire_names = [empire_names[i] for i in sorted_indices]
    empire_areas = [empire_areas[i] for i in sorted_indices]
    empire_colors = [empire_colors[i] for i in sorted_indices]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")

    bars = ax.barh(range(len(empire_names)), [a / 1_000_000 for a in empire_areas],
                   color=empire_colors, alpha=0.8)
    ax.set_yticks(range(len(empire_names)))
    ax.set_yticklabels(empire_names, color="#8b97b0", fontsize=9)
    ax.set_xlabel("Area (million km²)", color="#8b97b0", fontsize=10)
    ax.set_title("Empire Territories by Area", color="#e8ecf4", fontsize=12, pad=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Download empire data
    st.markdown("---")
    rows = []
    for name, data in EMPIRES.items():
        rows.append({
            "Empire": name,
            "Year": data["year"],
            "Area (km2)": data["area_km2"],
            "Population": data["population"],
            "Capital": data["capital"],
            "Description": data["desc"],
        })
    df_emp = pd.DataFrame(rows)

    with st.expander(f"Empire Data Table ({len(df_emp)} empires)", expanded=False):
        st.dataframe(df_emp, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df_emp.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Empire Data ({len(rows)} empires, CSV)",
        data=csv_buf.getvalue(),
        file_name="empire_timeline.csv",
        mime="text/csv",
        key="hist_emp_download",
    )


# ──────────────────────────────────────────────────────────────
# MODE 3: Historical Events Map
# ──────────────────────────────────────────────────────────────

def _render_events_mode():
    st.markdown("#### Historical Events Map")

    category = st.selectbox(
        "Event Category",
        list(EVENT_CATEGORIES.keys()),
        key="hist_event_cat",
    )

    cat_info = EVENT_CATEGORIES[category]

    # ── Ancient Wonders ──
    if category == "Ancient Wonders":
        _render_ancient_wonders()

    # ── Major Battles ──
    elif category == "Major Battles":
        _render_battles()

    # ── Exploration Routes ──
    elif category == "Exploration Routes":
        _render_exploration_routes()

    # ── Archaeological Sites ──
    elif category == "Archaeological Sites":
        _render_archaeological_sites()


def _render_ancient_wonders():
    """Render the Seven Wonders of the Ancient World."""

    st.markdown("##### Seven Wonders of the Ancient World")

    # Stats
    surviving = sum(1 for w in ANCIENT_WONDERS if "standing" in w["status"].lower())
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Wonders", len(ANCIENT_WONDERS))
    c2.metric("Still Standing", surviving)
    c3.metric("Destroyed", len(ANCIENT_WONDERS) - surviving)

    st.markdown("---")

    m = folium.Map(location=[33.0, 30.0], zoom_start=5, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    for w in ANCIENT_WONDERS:
        color = "#10b981" if "standing" in w["status"].lower() else "#ef4444"
        icon_char = "&#9733;" if "standing" in w["status"].lower() else "&#10005;"

        popup_html = (
            f"<div style='max-width:230px;'>"
            f"<strong>{escape(w['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem; color:#666;'>{escape(w['year'])}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(w['desc'][:180])}</span><br/>"
            f"<span style='font-size:0.75rem; color:{'green' if 'standing' in w['status'].lower() else 'red'};'>"
            f"Status: {escape(w['status'])}</span>"
            f"</div>"
        )

        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=w["name"],
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Table
    st.markdown("---")
    rows = []
    for w in ANCIENT_WONDERS:
        rows.append({
            "Wonder": w["name"],
            "Year Built": w["year"],
            "Status": w["status"],
            "Latitude": w["lat"],
            "Longitude": w["lon"],
            "Description": w["desc"],
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Wonders Data Table ({len(df)} wonders)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Ancient Wonders Data (CSV)",
        data=csv_buf.getvalue(),
        file_name="ancient_wonders.csv",
        mime="text/csv",
        key="hist_wonders_dl",
    )


def _render_battles():
    """Render major historical battles with timeline filtering."""

    st.markdown("##### Major Historical Battles")

    # Century filter
    all_centuries = sorted(set(b["century"] for b in MAJOR_BATTLES))
    century_labels = {c: _century_label(c) for c in all_centuries}

    min_cent = min(all_centuries)
    max_cent = max(all_centuries)
    cent_range = st.slider(
        "Filter by Century",
        min_value=min_cent,
        max_value=max_cent,
        value=(min_cent, max_cent),
        key="hist_battle_century",
        help="Negative = BC, Positive = AD",
    )

    filtered = [b for b in MAJOR_BATTLES
                if cent_range[0] <= b["century"] <= cent_range[1]]

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Battles", len(MAJOR_BATTLES))
    c2.metric("Showing", len(filtered))
    c3.metric("Century Range", f"{cent_range[0]} to {cent_range[1]}")

    st.markdown("---")

    if not filtered:
        st.warning("No battles in the selected century range. Adjust the filter.")
        return

    m = folium.Map(location=[38.0, 15.0], zoom_start=4, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    for b in filtered:
        popup_html = (
            f"<div style='max-width:230px;'>"
            f"<strong>{escape(b['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem; color:#f59e0b;'>{escape(b['year'])}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(b['desc'][:200])}</span>"
            f"</div>"
        )

        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=8,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{b['name']} ({b['year']})",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Battle list
    st.markdown("---")
    col_list, col_chart = st.columns([1, 1])

    with col_list:
        st.markdown("##### Battle Details")
        for b in filtered:
            st.markdown(
                f'<div style="background:rgba(15,23,42,0.5); border-left:3px solid #ef4444; '
                f'border-radius:6px; padding:0.5rem 0.75rem; margin-bottom:0.4rem;">'
                f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">'
                f'{escape(b["name"])}</div>'
                f'<div style="color:#f59e0b; font-size:0.75rem;">{escape(b["year"])}</div>'
                f'<div style="color:#8b97b0; font-size:0.75rem;">{escape(b["desc"][:120])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_chart:
        st.markdown("##### Battles by Century")
        cent_counts = {}
        for b in MAJOR_BATTLES:
            label = _century_label(b["century"])
            cent_counts[label] = cent_counts.get(label, 0) + 1

        if cent_counts:
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#0a0e1a")
            labels = list(cent_counts.keys())
            values = list(cent_counts.values())
            ax.barh(range(len(labels)), values, color="#ef4444", alpha=0.8)
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, color="#8b97b0", fontsize=8)
            ax.set_xlabel("Battles", color="#8b97b0", fontsize=10)
            ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
            ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")
            ax.invert_yaxis()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # Download
    st.markdown("---")
    rows = []
    for b in MAJOR_BATTLES:
        rows.append({
            "Battle": b["name"],
            "Year": b["year"],
            "Century": _century_label(b["century"]),
            "Latitude": b["lat"],
            "Longitude": b["lon"],
            "Description": b["desc"],
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Battles Data Table ({len(df)} battles)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Battle Data ({len(rows)} battles, CSV)",
        data=csv_buf.getvalue(),
        file_name="historical_battles.csv",
        mime="text/csv",
        key="hist_battles_dl",
    )


def _render_exploration_routes():
    """Render exploration routes as polylines on the map."""

    st.markdown("##### Great Exploration Routes")

    route_names = list(EXPLORATION_ROUTES.keys())
    selected_routes = st.multiselect(
        "Select routes to display",
        route_names,
        default=route_names[:3],
        key="hist_routes_sel",
    )

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Available Routes", len(EXPLORATION_ROUTES))
    c2.metric("Selected", len(selected_routes))
    total_pts = sum(len(EXPLORATION_ROUTES[r]["coords"]) for r in selected_routes)
    c3.metric("Waypoints", total_pts)

    st.markdown("---")

    if not selected_routes:
        st.info("Select at least one exploration route to display.")
        return

    m = folium.Map(location=[20.0, 20.0], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    # Legend
    legend_items = " ".join([
        f'<span style="color:{EXPLORATION_ROUTES[r]["color"]}; font-size:0.8rem;">&#9644; {escape(r.split("(")[0].strip())}</span>'
        for r in selected_routes
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'{legend_items}</div>',
        unsafe_allow_html=True,
    )

    for route_name in selected_routes:
        route = EXPLORATION_ROUTES[route_name]
        coords = route["coords"]
        color = route["color"]

        # Draw polyline
        folium.PolyLine(
            locations=coords,
            color=color,
            weight=3,
            opacity=0.8,
            tooltip=route_name,
        ).add_to(m)

        # Start marker
        start_popup = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(route_name)}</strong><br/>"
            f"<span style='font-size:0.8rem; color:#888;'>Start</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(route['desc'][:150])}</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=coords[0],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            weight=2,
            popup=folium.Popup(start_popup, max_width=240),
            tooltip=f"Start: {route_name}",
        ).add_to(m)

        # End marker
        end_popup = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(route_name)}</strong><br/>"
            f"<span style='font-size:0.8rem; color:#888;'>End / Destination</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=coords[-1],
            radius=7,
            color=color,
            fill=True,
            fill_color="#0a0e1a",
            fill_opacity=0.9,
            weight=3,
            popup=folium.Popup(end_popup, max_width=240),
            tooltip=f"End: {route_name}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Route details cards
    st.markdown("---")
    st.markdown("##### Route Details")
    for rname in selected_routes:
        route = EXPLORATION_ROUTES[rname]
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.5); border-left:3px solid {route["color"]}; '
            f'border-radius:6px; padding:0.5rem 0.75rem; margin-bottom:0.4rem;">'
            f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">'
            f'{escape(rname)}</div>'
            f'<div style="color:#f59e0b; font-size:0.75rem;">{escape(route["year"])}</div>'
            f'<div style="color:#8b97b0; font-size:0.75rem;">{escape(route["desc"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Download
    st.markdown("---")
    rows = []
    for rname, route in EXPLORATION_ROUTES.items():
        rows.append({
            "Route": rname,
            "Year": route["year"],
            "Description": route["desc"],
            "Waypoints": len(route["coords"]),
            "Start Lat": route["coords"][0][0],
            "Start Lon": route["coords"][0][1],
            "End Lat": route["coords"][-1][0],
            "End Lon": route["coords"][-1][1],
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Routes Data Table ({len(df)} routes)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Exploration Routes (CSV)",
        data=csv_buf.getvalue(),
        file_name="exploration_routes.csv",
        mime="text/csv",
        key="hist_routes_dl",
    )


def _render_archaeological_sites():
    """Render major archaeological sites with timeline filtering."""

    st.markdown("##### Major Archaeological Sites")

    # Century filter
    all_centuries = sorted(set(s["century"] for s in ARCHAEOLOGICAL_SITES))
    min_cent = min(all_centuries)
    max_cent = max(all_centuries)
    cent_range = st.slider(
        "Filter by Century (founding/creation)",
        min_value=min_cent,
        max_value=max_cent,
        value=(min_cent, max_cent),
        key="hist_site_century",
        help="Negative = BC, Positive = AD",
    )

    filtered = [s for s in ARCHAEOLOGICAL_SITES
                if cent_range[0] <= s["century"] <= cent_range[1]]

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sites", len(ARCHAEOLOGICAL_SITES))
    c2.metric("Showing", len(filtered))
    c3.metric("Span", f"{abs(min_cent)} BC - {max_cent} AD")

    st.markdown("---")

    if not filtered:
        st.warning("No sites in the selected century range. Adjust the filter.")
        return

    m = folium.Map(location=[25.0, 30.0], zoom_start=3, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    for s in filtered:
        popup_html = (
            f"<div style='max-width:230px;'>"
            f"<strong>{escape(s['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem; color:#10b981;'>{escape(s['year'])}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(s['desc'][:200])}</span>"
            f"</div>"
        )

        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color="#10b981",
            fill=True,
            fill_color="#10b981",
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{s['name']} ({s['year']})",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Site cards
    st.markdown("---")
    col_list, col_chart = st.columns([1, 1])

    with col_list:
        st.markdown("##### Site Details")
        for s in filtered:
            st.markdown(
                f'<div style="background:rgba(15,23,42,0.5); border-left:3px solid #10b981; '
                f'border-radius:6px; padding:0.5rem 0.75rem; margin-bottom:0.4rem;">'
                f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">'
                f'{escape(s["name"])}</div>'
                f'<div style="color:#10b981; font-size:0.75rem;">{escape(s["year"])}</div>'
                f'<div style="color:#8b97b0; font-size:0.75rem;">{escape(s["desc"][:120])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_chart:
        st.markdown("##### Sites by Region")
        region_counts = {}
        for s in ARCHAEOLOGICAL_SITES:
            lon = s["lon"]
            if lon < -30:
                region = "Americas"
            elif lon < 25:
                region = "Europe"
            elif lon < 50:
                region = "Middle East / Africa"
            elif lon < 90:
                region = "South Asia"
            else:
                region = "East / SE Asia"
            region_counts[region] = region_counts.get(region, 0) + 1

        if region_counts:
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#0a0e1a")
            labels = list(region_counts.keys())
            values = list(region_counts.values())
            colors = ["#ef4444", "#8b5cf6", "#f59e0b", "#06b6d4", "#10b981"]
            ax.barh(range(len(labels)), values,
                    color=colors[:len(labels)], alpha=0.8)
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, color="#8b97b0", fontsize=9)
            ax.set_xlabel("Sites", color="#8b97b0", fontsize=10)
            ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
            ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")
            ax.invert_yaxis()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # Download
    st.markdown("---")
    rows = []
    for s in ARCHAEOLOGICAL_SITES:
        rows.append({
            "Site": s["name"],
            "Year": s["year"],
            "Latitude": s["lat"],
            "Longitude": s["lon"],
            "Description": s["desc"],
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Sites Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Archaeological Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name="archaeological_sites.csv",
        mime="text/csv",
        key="hist_sites_dl",
    )
