# -*- coding: utf-8 -*-
"""
Agriculture & Food Production Maps module for TerraScout AI.
Provides 10 agriculture/food production map types using hardcoded data
and Overpass API queries. All free APIs, no API keys needed.
"""

import io
import math
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

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# =====================================================================
# MAP TYPE DEFINITIONS
# =====================================================================
MAP_TYPES = [
    "Global Crop Regions",
    "Wine Regions",
    "Fishing Zones",
    "Livestock Distribution",
    "Coffee & Tea Origins",
    "Organic Farming",
    "Irrigation Systems",
    "Food Production Index",
    "Spice Routes",
    "Agricultural Land Use",
]

# =====================================================================
# COLORS
# =====================================================================
CROP_COLORS = {
    "Wheat": "#f59e0b",
    "Rice": "#10b981",
    "Corn": "#3b82f6",
    "Coffee": "#92400e",
    "Sugarcane": "#8b5cf6",
    "Cotton": "#ec4899",
}

WINE_COLORS = {
    "France": "#ef4444",
    "Italy": "#10b981",
    "Spain": "#f59e0b",
    "USA": "#3b82f6",
    "Argentina": "#8b5cf6",
    "Australia": "#f97316",
    "South Africa": "#ec4899",
    "Portugal": "#06b6d4",
    "Germany": "#84cc16",
    "Chile": "#14b8a6",
    "New Zealand": "#22c55e",
}

LIVESTOCK_COLORS = {
    "Cattle": "#ef4444",
    "Sheep": "#f59e0b",
    "Goat": "#8b5cf6",
    "Pig": "#ec4899",
    "Poultry": "#06b6d4",
}

AGRI_LANDUSE_COLORS = {
    "farmland": "#10b981",
    "orchard": "#f59e0b",
    "vineyard": "#8b5cf6",
    "meadow": "#84cc16",
}

# =====================================================================
# 1. GLOBAL CROP REGIONS DATA
# =====================================================================
CROP_REGIONS = [
    {
        "crop": "Wheat", "region": "US Great Plains",
        "polygon": [[49.0, -104.0], [49.0, -96.0], [37.0, -96.0], [37.0, -104.0]],
        "production_mt": 47.3, "area_mha": 12.8,
        "countries": "USA, Canada",
        "notes": "Winter and spring wheat, semi-arid continental climate",
    },
    {
        "crop": "Wheat", "region": "Ukraine-Russia Black Earth",
        "polygon": [[55.0, 30.0], [55.0, 45.0], [46.0, 45.0], [46.0, 30.0]],
        "production_mt": 110.0, "area_mha": 28.0,
        "countries": "Ukraine, Russia",
        "notes": "Chernozem soils, continental climate, major export region",
    },
    {
        "crop": "Wheat", "region": "Australian Wheat Belt",
        "polygon": [[-26.0, 115.0], [-26.0, 150.0], [-37.0, 150.0], [-37.0, 115.0]],
        "production_mt": 25.0, "area_mha": 12.5,
        "countries": "Australia",
        "notes": "Dryland farming, Mediterranean-like climate",
    },
    {
        "crop": "Rice", "region": "Southeast Asia Lowlands",
        "polygon": [[23.0, 95.0], [23.0, 110.0], [8.0, 110.0], [8.0, 95.0]],
        "production_mt": 120.0, "area_mha": 25.0,
        "countries": "Thailand, Vietnam, Myanmar, Cambodia",
        "notes": "Tropical monsoon paddies, multiple harvests per year",
    },
    {
        "crop": "Rice", "region": "Indian Subcontinent",
        "polygon": [[30.0, 75.0], [30.0, 90.0], [10.0, 90.0], [10.0, 75.0]],
        "production_mt": 195.0, "area_mha": 44.0,
        "countries": "India, Bangladesh",
        "notes": "Monsoon-dependent, Ganges-Brahmaputra floodplains",
    },
    {
        "crop": "Rice", "region": "China Rice Bowl",
        "polygon": [[35.0, 105.0], [35.0, 122.0], [22.0, 122.0], [22.0, 105.0]],
        "production_mt": 212.0, "area_mha": 30.0,
        "countries": "China",
        "notes": "Yangtze and Pearl River deltas, terraced hillsides",
    },
    {
        "crop": "Corn", "region": "US Corn Belt",
        "polygon": [[45.0, -96.0], [45.0, -82.0], [37.0, -82.0], [37.0, -96.0]],
        "production_mt": 384.0, "area_mha": 33.0,
        "countries": "USA",
        "notes": "Iowa, Illinois, Indiana, Ohio; rich prairie soils",
    },
    {
        "crop": "Corn", "region": "Brazil Cerrado",
        "polygon": [[-5.0, -55.0], [-5.0, -42.0], [-20.0, -42.0], [-20.0, -55.0]],
        "production_mt": 116.0, "area_mha": 22.0,
        "countries": "Brazil",
        "notes": "Tropical savanna, safrinha (second crop) system",
    },
    {
        "crop": "Coffee", "region": "Coffee Belt Americas",
        "polygon": [[23.5, -105.0], [23.5, -35.0], [-23.5, -35.0], [-23.5, -105.0]],
        "production_mt": 5.8, "area_mha": 6.0,
        "countries": "Brazil, Colombia, Honduras, Guatemala, Mexico",
        "notes": "Arabica dominant, shade-grown and sun-grown varieties",
    },
    {
        "crop": "Coffee", "region": "Coffee Belt Africa-Asia",
        "polygon": [[23.5, 25.0], [23.5, 130.0], [-23.5, 130.0], [-23.5, 25.0]],
        "production_mt": 4.5, "area_mha": 4.5,
        "countries": "Ethiopia, Vietnam, Indonesia, Uganda, India",
        "notes": "Vietnam: Robusta leader; Ethiopia: Arabica origin",
    },
    {
        "crop": "Sugarcane", "region": "Brazil Sugarcane Belt",
        "polygon": [[-15.0, -52.0], [-15.0, -40.0], [-25.0, -40.0], [-25.0, -52.0]],
        "production_mt": 750.0, "area_mha": 10.0,
        "countries": "Brazil",
        "notes": "Sao Paulo state dominant, ethanol and sugar production",
    },
    {
        "crop": "Sugarcane", "region": "India Sugarcane",
        "polygon": [[30.0, 75.0], [30.0, 87.0], [18.0, 87.0], [18.0, 75.0]],
        "production_mt": 400.0, "area_mha": 5.0,
        "countries": "India",
        "notes": "Uttar Pradesh, Maharashtra; monsoon irrigated",
    },
    {
        "crop": "Sugarcane", "region": "Thailand Sugarcane",
        "polygon": [[19.0, 99.0], [19.0, 105.0], [13.0, 105.0], [13.0, 99.0]],
        "production_mt": 100.0, "area_mha": 1.8,
        "countries": "Thailand",
        "notes": "Central plains, tropical monsoon climate",
    },
    {
        "crop": "Cotton", "region": "US Cotton South",
        "polygon": [[37.0, -100.0], [37.0, -80.0], [30.0, -80.0], [30.0, -100.0]],
        "production_mt": 4.0, "area_mha": 4.5,
        "countries": "USA",
        "notes": "Texas, Georgia, Mississippi; irrigated and dryland",
    },
    {
        "crop": "Cotton", "region": "India Cotton Belt",
        "polygon": [[25.0, 70.0], [25.0, 80.0], [17.0, 80.0], [17.0, 70.0]],
        "production_mt": 6.2, "area_mha": 13.0,
        "countries": "India",
        "notes": "Gujarat, Maharashtra; rainfed black cotton soils",
    },
    {
        "crop": "Cotton", "region": "China Cotton Xinjiang",
        "polygon": [[45.0, 75.0], [45.0, 90.0], [37.0, 90.0], [37.0, 75.0]],
        "production_mt": 6.0, "area_mha": 3.4,
        "countries": "China",
        "notes": "Xinjiang province, irrigated desert agriculture",
    },
]

# =====================================================================
# 2. WINE REGIONS DATA
# =====================================================================
WINE_REGIONS = [
    # France
    {"name": "Bordeaux", "lat": 44.84, "lon": -0.58, "country": "France",
     "grapes": "Cabernet Sauvignon, Merlot, Cab Franc", "climate": "Oceanic",
     "area_ha": 111000, "notes": "Left/Right bank, classified growths since 1855"},
    {"name": "Burgundy", "lat": 47.05, "lon": 4.38, "country": "France",
     "grapes": "Pinot Noir, Chardonnay", "climate": "Continental",
     "area_ha": 29500, "notes": "Grand Cru terroir, Cote d'Or limestone slopes"},
    {"name": "Champagne", "lat": 49.05, "lon": 3.95, "country": "France",
     "grapes": "Chardonnay, Pinot Noir, Pinot Meunier", "climate": "Cool Continental",
     "area_ha": 34000, "notes": "Methode champenoise, chalk subsoil"},
    {"name": "Rhone Valley", "lat": 44.08, "lon": 4.83, "country": "France",
     "grapes": "Syrah, Grenache, Mourvedre", "climate": "Mediterranean/Continental",
     "area_ha": 69000, "notes": "Northern Rhone (Syrah) vs Southern (blends)"},
    {"name": "Loire Valley", "lat": 47.38, "lon": 0.69, "country": "France",
     "grapes": "Sauvignon Blanc, Chenin Blanc, Cab Franc", "climate": "Oceanic/Continental",
     "area_ha": 52000, "notes": "Garden of France, diverse styles"},
    {"name": "Alsace", "lat": 48.32, "lon": 7.44, "country": "France",
     "grapes": "Riesling, Gewurztraminer, Pinot Gris", "climate": "Continental",
     "area_ha": 15600, "notes": "Vosges rain shadow, aromatic whites"},
    # Italy
    {"name": "Tuscany (Chianti)", "lat": 43.47, "lon": 11.25, "country": "Italy",
     "grapes": "Sangiovese, Cab Sauvignon, Merlot", "climate": "Mediterranean",
     "area_ha": 63000, "notes": "Chianti Classico DOCG, Super Tuscans, Brunello"},
    {"name": "Piedmont", "lat": 44.70, "lon": 8.03, "country": "Italy",
     "grapes": "Nebbiolo, Barbera, Dolcetto", "climate": "Continental",
     "area_ha": 44000, "notes": "Barolo and Barbaresco DOCG, foggy hills"},
    {"name": "Veneto", "lat": 45.44, "lon": 12.32, "country": "Italy",
     "grapes": "Glera (Prosecco), Corvina, Garganega", "climate": "Mediterranean/Continental",
     "area_ha": 86000, "notes": "Prosecco, Valpolicella, Amarone, Soave"},
    {"name": "Sicily", "lat": 37.60, "lon": 14.02, "country": "Italy",
     "grapes": "Nero d'Avola, Nerello Mascalese, Grillo", "climate": "Mediterranean",
     "area_ha": 98000, "notes": "Etna DOC volcanic wines, Marsala"},
    # Spain
    {"name": "Rioja", "lat": 42.47, "lon": -2.45, "country": "Spain",
     "grapes": "Tempranillo, Garnacha, Graciano", "climate": "Continental/Mediterranean",
     "area_ha": 65000, "notes": "Crianza/Reserva/Gran Reserva aging system"},
    {"name": "Ribera del Duero", "lat": 41.64, "lon": -3.70, "country": "Spain",
     "grapes": "Tempranillo (Tinto Fino)", "climate": "Continental",
     "area_ha": 23000, "notes": "High altitude plateau, extreme temperature swings"},
    {"name": "Priorat", "lat": 41.19, "lon": 0.75, "country": "Spain",
     "grapes": "Garnacha, Carinena", "climate": "Mediterranean",
     "area_ha": 1900, "notes": "Llicorella slate soils, steep terraced vineyards"},
    # USA
    {"name": "Napa Valley", "lat": 38.50, "lon": -122.33, "country": "USA",
     "grapes": "Cabernet Sauvignon, Chardonnay, Merlot", "climate": "Mediterranean",
     "area_ha": 18200, "notes": "Premium Cab Sauv, Stags Leap, Rutherford Bench"},
    {"name": "Sonoma County", "lat": 38.30, "lon": -122.72, "country": "USA",
     "grapes": "Pinot Noir, Chardonnay, Zinfandel", "climate": "Mediterranean/Cool",
     "area_ha": 24000, "notes": "Russian River Valley, Sonoma Coast fog influence"},
    {"name": "Willamette Valley", "lat": 45.10, "lon": -123.10, "country": "USA",
     "grapes": "Pinot Noir, Pinot Gris, Chardonnay", "climate": "Cool Maritime",
     "area_ha": 12000, "notes": "Oregon Pinot Noir, volcanic Jory soils"},
    {"name": "Walla Walla", "lat": 46.06, "lon": -118.33, "country": "USA",
     "grapes": "Cabernet Sauvignon, Syrah, Merlot", "climate": "Continental",
     "area_ha": 1200, "notes": "Washington State, loess soils, warm days cool nights"},
    # Argentina
    {"name": "Mendoza", "lat": -33.00, "lon": -68.85, "country": "Argentina",
     "grapes": "Malbec, Cabernet Sauvignon, Torrontes", "climate": "Arid Continental",
     "area_ha": 155000, "notes": "Andes foothills, high altitude (800-1500m)"},
    # Chile
    {"name": "Maipo Valley", "lat": -33.75, "lon": -70.70, "country": "Chile",
     "grapes": "Cabernet Sauvignon, Carmenere, Merlot", "climate": "Mediterranean",
     "area_ha": 10800, "notes": "Andes influence, premium Cab Sauv"},
    # Australia
    {"name": "Barossa Valley", "lat": -34.56, "lon": 138.95, "country": "Australia",
     "grapes": "Shiraz, Grenache, Cabernet Sauvignon", "climate": "Mediterranean",
     "area_ha": 13000, "notes": "Old vine Shiraz, rich and powerful reds"},
    {"name": "Hunter Valley", "lat": -32.80, "lon": 151.15, "country": "Australia",
     "grapes": "Semillon, Shiraz, Chardonnay", "climate": "Subtropical",
     "area_ha": 4500, "notes": "Iconic aged Semillon, oldest wine region in Australia"},
    {"name": "Margaret River", "lat": -33.95, "lon": 115.07, "country": "Australia",
     "grapes": "Cabernet Sauvignon, Chardonnay, SSB blend", "climate": "Maritime Mediterranean",
     "area_ha": 5500, "notes": "Western Australia, Bordeaux-style blends"},
    {"name": "Yarra Valley", "lat": -37.75, "lon": 145.50, "country": "Australia",
     "grapes": "Pinot Noir, Chardonnay, Shiraz", "climate": "Cool Maritime",
     "area_ha": 3000, "notes": "Cool-climate elegance, sparkling wines"},
    # South Africa
    {"name": "Stellenbosch", "lat": -33.93, "lon": 18.86, "country": "South Africa",
     "grapes": "Cabernet Sauvignon, Pinotage, Chenin Blanc", "climate": "Mediterranean",
     "area_ha": 16000, "notes": "Cape Winelands, mountain slopes, Pinotage origin"},
    {"name": "Franschhoek", "lat": -33.89, "lon": 19.12, "country": "South Africa",
     "grapes": "Chardonnay, Cabernet Sauvignon, Semillon", "climate": "Mediterranean",
     "area_ha": 2800, "notes": "French Huguenot heritage, valley setting"},
    # Portugal
    {"name": "Douro Valley", "lat": 41.15, "lon": -7.75, "country": "Portugal",
     "grapes": "Touriga Nacional, Tinta Roriz, Touriga Franca", "climate": "Continental Mediterranean",
     "area_ha": 45000, "notes": "Port wine origin, UNESCO terraced vineyards"},
    {"name": "Alentejo", "lat": 38.57, "lon": -7.91, "country": "Portugal",
     "grapes": "Aragonez, Trincadeira, Antao Vaz", "climate": "Hot Mediterranean",
     "area_ha": 23000, "notes": "Southern plains, cork oak landscapes"},
    # Germany
    {"name": "Mosel", "lat": 49.95, "lon": 6.90, "country": "Germany",
     "grapes": "Riesling", "climate": "Cool Continental",
     "area_ha": 8800, "notes": "Steep slate slopes, mineral Riesling, Pradikat system"},
    {"name": "Rheingau", "lat": 50.02, "lon": 8.05, "country": "Germany",
     "grapes": "Riesling, Spatburgunder", "climate": "Cool Continental",
     "area_ha": 3100, "notes": "Rhine river influence, Schloss Johannisberg"},
    # New Zealand
    {"name": "Marlborough", "lat": -41.52, "lon": 173.95, "country": "New Zealand",
     "grapes": "Sauvignon Blanc, Pinot Noir", "climate": "Cool Maritime",
     "area_ha": 26800, "notes": "Pungent Sauvignon Blanc, Wairau Valley"},
    {"name": "Central Otago", "lat": -45.03, "lon": 169.20, "country": "New Zealand",
     "grapes": "Pinot Noir, Riesling", "climate": "Continental",
     "area_ha": 2000, "notes": "Southernmost wine region, schist soils"},
]

# =====================================================================
# 3. FAO FISHING ZONES DATA
# =====================================================================
FAO_FISHING_ZONES = [
    {"name": "NE Atlantic (FAO 27)", "code": 27,
     "polygon": [[70.0, -40.0], [70.0, 30.0], [36.0, 30.0], [36.0, -40.0]],
     "catch_mt": 8.5, "species": "Cod, Herring, Mackerel, Haddock",
     "notes": "North Sea, Norwegian Sea, Baltic approaches"},
    {"name": "NW Atlantic (FAO 21)", "code": 21,
     "polygon": [[70.0, -80.0], [70.0, -40.0], [35.0, -40.0], [35.0, -80.0]],
     "catch_mt": 2.1, "species": "Lobster, Scallop, Cod, Haddock",
     "notes": "Grand Banks, Georges Bank, Gulf of Maine"},
    {"name": "W Central Atlantic (FAO 31)", "code": 31,
     "polygon": [[35.0, -98.0], [35.0, -40.0], [5.0, -40.0], [5.0, -98.0]],
     "catch_mt": 1.5, "species": "Shrimp, Tuna, Mahi-mahi, Snapper",
     "notes": "Gulf of Mexico, Caribbean Sea"},
    {"name": "E Central Atlantic (FAO 34)", "code": 34,
     "polygon": [[36.0, -40.0], [36.0, 20.0], [-5.0, 20.0], [-5.0, -40.0]],
     "catch_mt": 5.0, "species": "Sardine, Octopus, Hake, Tuna",
     "notes": "Canary Current upwelling, Mauritania-Senegal"},
    {"name": "W Central Pacific (FAO 71)", "code": 71,
     "polygon": [[25.0, 100.0], [25.0, 175.0], [-25.0, 175.0], [-25.0, 100.0]],
     "catch_mt": 13.0, "species": "Skipjack Tuna, Anchoveta, Squid",
     "notes": "Largest catch area globally, Philippines, Indonesia"},
    {"name": "NW Pacific (FAO 61)", "code": 61,
     "polygon": [[65.0, 100.0], [65.0, 175.0], [25.0, 175.0], [25.0, 100.0]],
     "catch_mt": 20.0, "species": "Pollock, Squid, Anchovy, Saury",
     "notes": "Japan, Korea, China; most productive zone"},
    {"name": "E Indian Ocean (FAO 57)", "code": 57,
     "polygon": [[25.0, 75.0], [25.0, 130.0], [-50.0, 130.0], [-50.0, 75.0]],
     "catch_mt": 8.0, "species": "Tuna, Shrimp, Sardine, Mackerel",
     "notes": "Bay of Bengal, Andaman Sea, W Australia"},
    {"name": "W Indian Ocean (FAO 51)", "code": 51,
     "polygon": [[25.0, 30.0], [25.0, 75.0], [-50.0, 75.0], [-50.0, 30.0]],
     "catch_mt": 5.5, "species": "Tuna, Shrimp, Sardine, Kingfish",
     "notes": "Arabian Sea, Mozambique Channel, Somali upwelling"},
    {"name": "SE Atlantic (FAO 47)", "code": 47,
     "polygon": [[-5.0, -20.0], [-5.0, 30.0], [-60.0, 30.0], [-60.0, -20.0]],
     "catch_mt": 1.8, "species": "Hake, Horse Mackerel, Pilchard",
     "notes": "Benguela Current upwelling, Namibia, S. Africa"},
    {"name": "SE Pacific (FAO 87)", "code": 87,
     "polygon": [[5.0, -120.0], [5.0, -70.0], [-60.0, -70.0], [-60.0, -120.0]],
     "catch_mt": 8.5, "species": "Anchoveta, Jack Mackerel, Squid",
     "notes": "Humboldt Current, Peru-Chile anchovy fisheries"},
    {"name": "SW Atlantic (FAO 41)", "code": 41,
     "polygon": [[5.0, -70.0], [5.0, -20.0], [-60.0, -20.0], [-60.0, -70.0]],
     "catch_mt": 2.0, "species": "Hake, Shrimp, Squid, Croaker",
     "notes": "Argentine shelf, Falkland/Malvinas Islands"},
    {"name": "NE Pacific (FAO 67)", "code": 67,
     "polygon": [[65.0, -175.0], [65.0, -110.0], [25.0, -110.0], [25.0, -175.0]],
     "catch_mt": 3.2, "species": "Pollock, Salmon, Halibut, Crab",
     "notes": "Alaska, British Columbia, Pacific NW"},
]

# =====================================================================
# 4. LIVESTOCK DISTRIBUTION DATA (million head, country centroids)
# =====================================================================
LIVESTOCK_DATA = [
    {"country": "Brazil", "lat": -14.24, "lon": -51.93, "cattle": 225.0, "sheep": 19.0, "goat": 12.0, "pig": 42.0, "poultry": 1500.0},
    {"country": "India", "lat": 20.59, "lon": 78.96, "cattle": 305.0, "sheep": 74.0, "goat": 149.0, "pig": 9.0, "poultry": 851.0},
    {"country": "China", "lat": 35.86, "lon": 104.20, "cattle": 97.0, "sheep": 316.0, "goat": 135.0, "pig": 440.0, "poultry": 6200.0},
    {"country": "USA", "lat": 37.09, "lon": -95.71, "cattle": 93.0, "sheep": 5.2, "goat": 2.6, "pig": 74.0, "poultry": 9900.0},
    {"country": "Argentina", "lat": -38.42, "lon": -63.62, "cattle": 54.0, "sheep": 14.0, "goat": 4.7, "pig": 6.0, "poultry": 150.0},
    {"country": "Australia", "lat": -25.27, "lon": 133.78, "cattle": 23.0, "sheep": 66.0, "goat": 4.2, "pig": 2.4, "poultry": 130.0},
    {"country": "Ethiopia", "lat": 9.15, "lon": 40.49, "cattle": 65.0, "sheep": 40.0, "goat": 51.0, "pig": 0.04, "poultry": 60.0},
    {"country": "Nigeria", "lat": 9.08, "lon": 8.68, "cattle": 21.0, "sheep": 43.0, "goat": 80.0, "pig": 7.0, "poultry": 180.0},
    {"country": "Pakistan", "lat": 30.38, "lon": 69.35, "cattle": 51.0, "sheep": 31.0, "goat": 78.0, "pig": 0.0, "poultry": 440.0},
    {"country": "Mexico", "lat": 23.63, "lon": -102.55, "cattle": 35.0, "sheep": 8.8, "goat": 8.7, "pig": 19.0, "poultry": 580.0},
    {"country": "Russia", "lat": 61.52, "lon": 105.32, "cattle": 18.0, "sheep": 22.0, "goat": 2.1, "pig": 23.0, "poultry": 590.0},
    {"country": "France", "lat": 46.23, "lon": 2.21, "cattle": 17.5, "sheep": 7.2, "goat": 1.3, "pig": 13.0, "poultry": 250.0},
    {"country": "Germany", "lat": 51.17, "lon": 10.45, "cattle": 11.0, "sheep": 1.5, "goat": 0.15, "pig": 26.0, "poultry": 175.0},
    {"country": "New Zealand", "lat": -40.90, "lon": 174.89, "cattle": 10.0, "sheep": 26.0, "goat": 0.1, "pig": 0.3, "poultry": 25.0},
    {"country": "Kenya", "lat": -0.02, "lon": 37.91, "cattle": 18.0, "sheep": 17.0, "goat": 27.0, "pig": 0.3, "poultry": 44.0},
    {"country": "Sudan", "lat": 12.86, "lon": 30.22, "cattle": 31.0, "sheep": 40.0, "goat": 31.0, "pig": 0.0, "poultry": 55.0},
    {"country": "Turkey", "lat": 38.96, "lon": 35.24, "cattle": 18.0, "sheep": 42.0, "goat": 12.0, "pig": 0.0, "poultry": 350.0},
    {"country": "UK", "lat": 55.38, "lon": -3.44, "cattle": 9.6, "sheep": 33.0, "goat": 0.1, "pig": 5.0, "poultry": 187.0},
    {"country": "Spain", "lat": 40.46, "lon": -3.75, "cattle": 6.7, "sheep": 15.0, "goat": 2.8, "pig": 32.0, "poultry": 165.0},
    {"country": "Italy", "lat": 41.87, "lon": 12.57, "cattle": 6.2, "sheep": 7.0, "goat": 1.0, "pig": 8.5, "poultry": 155.0},
    {"country": "Indonesia", "lat": -0.79, "lon": 113.92, "cattle": 17.0, "sheep": 17.0, "goat": 19.0, "pig": 8.0, "poultry": 3400.0},
    {"country": "Colombia", "lat": 4.57, "lon": -74.30, "cattle": 28.0, "sheep": 2.1, "goat": 1.0, "pig": 6.0, "poultry": 200.0},
    {"country": "South Africa", "lat": -30.56, "lon": 22.94, "cattle": 12.0, "sheep": 22.0, "goat": 5.6, "pig": 1.5, "poultry": 180.0},
    {"country": "Bangladesh", "lat": 23.68, "lon": 90.36, "cattle": 24.0, "sheep": 3.6, "goat": 26.0, "pig": 0.0, "poultry": 350.0},
    {"country": "Vietnam", "lat": 14.06, "lon": 108.28, "cattle": 6.3, "sheep": 0.1, "goat": 2.6, "pig": 28.0, "poultry": 520.0},
]

# =====================================================================
# 5. COFFEE & TEA ORIGINS DATA
# =====================================================================
COFFEE_ORIGINS = [
    {"name": "Brazil", "lat": -14.24, "lon": -51.93, "type": "coffee", "variety": "Arabica & Robusta",
     "production_mt": 3.0, "notes": "World #1 producer, Minas Gerais, Sao Paulo"},
    {"name": "Vietnam", "lat": 14.06, "lon": 108.28, "type": "coffee", "variety": "Robusta",
     "production_mt": 1.8, "notes": "World #2, Central Highlands, rapid growth since 1990s"},
    {"name": "Colombia", "lat": 4.57, "lon": -74.30, "type": "coffee", "variety": "Arabica",
     "production_mt": 0.81, "notes": "High-altitude washed Arabica, Eje Cafetero"},
    {"name": "Ethiopia", "lat": 9.15, "lon": 40.49, "type": "coffee", "variety": "Arabica (origin)",
     "production_mt": 0.47, "notes": "Birthplace of coffee, Yirgacheffe, Sidamo, Harrar"},
    {"name": "Indonesia", "lat": -0.79, "lon": 113.92, "type": "coffee", "variety": "Robusta & Arabica",
     "production_mt": 0.67, "notes": "Sumatra Mandheling, Java, Sulawesi, Kopi Luwak"},
    {"name": "Honduras", "lat": 15.20, "lon": -86.24, "type": "coffee", "variety": "Arabica",
     "production_mt": 0.48, "notes": "Central American leader, Santa Barbara highlands"},
    {"name": "Peru", "lat": -9.19, "lon": -75.02, "type": "coffee", "variety": "Arabica",
     "production_mt": 0.37, "notes": "Organic specialty, Chanchamayo, Cusco"},
    {"name": "Guatemala", "lat": 15.78, "lon": -90.23, "type": "coffee", "variety": "Arabica",
     "production_mt": 0.24, "notes": "Antigua, Huehuetenango, volcanic soils"},
    {"name": "Uganda", "lat": 1.37, "lon": 32.29, "type": "coffee", "variety": "Robusta",
     "production_mt": 0.38, "notes": "Africa top Robusta, Mount Elgon Arabica"},
    {"name": "Costa Rica", "lat": 9.75, "lon": -83.75, "type": "coffee", "variety": "Arabica",
     "production_mt": 0.09, "notes": "Tarrazu, micro-lot specialty, honey process"},
    {"name": "India (Coorg)", "lat": 12.42, "lon": 75.74, "type": "coffee", "variety": "Arabica & Robusta",
     "production_mt": 0.33, "notes": "Monsoon Malabar, shade-grown, Karnataka"},
    {"name": "Jamaica Blue Mountain", "lat": 18.18, "lon": -76.58, "type": "coffee", "variety": "Arabica",
     "production_mt": 0.001, "notes": "Premium single-origin, cool misty peaks"},
    {"name": "Kenya", "lat": -0.02, "lon": 37.91, "type": "coffee", "variety": "Arabica (SL28/SL34)",
     "production_mt": 0.05, "notes": "Bright acidity, Mt. Kenya, auction system"},
]

TEA_ORIGINS = [
    {"name": "China (Fujian)", "lat": 26.07, "lon": 118.17, "type": "tea", "variety": "Green, Oolong, White, Pu-erh",
     "production_mt": 3.1, "notes": "World #1, birthplace of tea, 5000+ years"},
    {"name": "India (Assam)", "lat": 26.20, "lon": 92.94, "type": "tea", "variety": "Black (CTC & Orthodox)",
     "production_mt": 1.4, "notes": "World #2, Assam malty, Darjeeling muscatel"},
    {"name": "India (Darjeeling)", "lat": 27.04, "lon": 88.26, "type": "tea", "variety": "Black (Orthodox)",
     "production_mt": 0.01, "notes": "Champagne of teas, Himalayan foothills"},
    {"name": "Sri Lanka (Ceylon)", "lat": 7.17, "lon": 80.77, "type": "tea", "variety": "Black",
     "production_mt": 0.28, "notes": "High-grown Ceylon, Nuwara Eliya, Uva"},
    {"name": "Kenya (Kericho)", "lat": -0.37, "lon": 35.29, "type": "tea", "variety": "Black (CTC)",
     "production_mt": 0.54, "notes": "Africa #1, equatorial highlands, year-round"},
    {"name": "Japan (Shizuoka)", "lat": 34.98, "lon": 138.38, "type": "tea", "variety": "Green (Sencha, Matcha, Gyokuro)",
     "production_mt": 0.08, "notes": "Premium matcha, shade-grown Gyokuro, Uji"},
    {"name": "Turkey (Rize)", "lat": 41.02, "lon": 40.52, "type": "tea", "variety": "Black",
     "production_mt": 0.28, "notes": "Black Sea coast, cay culture, high per-capita"},
    {"name": "Taiwan (Ali Shan)", "lat": 23.51, "lon": 120.70, "type": "tea", "variety": "Oolong",
     "production_mt": 0.02, "notes": "High mountain oolong, Dong Ding, Oriental Beauty"},
    {"name": "Nepal (Ilam)", "lat": 26.91, "lon": 87.93, "type": "tea", "variety": "Orthodox Black & Green",
     "production_mt": 0.03, "notes": "Himalayan terroir similar to Darjeeling"},
]

# =====================================================================
# 6. ORGANIC FARMING DATA (% of agricultural land that is organic)
# =====================================================================
ORGANIC_FARMING_PCT = [
    {"country": "Liechtenstein", "lat": 47.17, "lon": 9.51, "pct": 41.0, "area_ha": 1400},
    {"country": "Austria", "lat": 47.52, "lon": 14.55, "pct": 26.5, "area_ha": 690000},
    {"country": "Estonia", "lat": 58.60, "lon": 25.01, "pct": 23.4, "area_ha": 230000},
    {"country": "Sweden", "lat": 60.13, "lon": 18.64, "pct": 20.4, "area_ha": 614000},
    {"country": "Switzerland", "lat": 46.82, "lon": 8.23, "pct": 17.0, "area_ha": 178000},
    {"country": "Italy", "lat": 41.87, "lon": 12.57, "pct": 16.6, "area_ha": 2190000},
    {"country": "Czech Republic", "lat": 49.82, "lon": 15.47, "pct": 15.3, "area_ha": 540000},
    {"country": "Latvia", "lat": 56.88, "lon": 24.60, "pct": 14.8, "area_ha": 290000},
    {"country": "Finland", "lat": 61.92, "lon": 25.75, "pct": 14.2, "area_ha": 330000},
    {"country": "Denmark", "lat": 56.26, "lon": 9.50, "pct": 11.4, "area_ha": 300000},
    {"country": "Germany", "lat": 51.17, "lon": 10.45, "pct": 10.8, "area_ha": 1800000},
    {"country": "France", "lat": 46.23, "lon": 2.21, "pct": 10.0, "area_ha": 2800000},
    {"country": "Spain", "lat": 40.46, "lon": -3.75, "pct": 10.5, "area_ha": 2640000},
    {"country": "Greece", "lat": 39.07, "lon": 21.82, "pct": 10.3, "area_ha": 530000},
    {"country": "Portugal", "lat": 39.40, "lon": -8.22, "pct": 8.2, "area_ha": 290000},
    {"country": "UK", "lat": 55.38, "lon": -3.44, "pct": 2.8, "area_ha": 490000},
    {"country": "USA", "lat": 37.09, "lon": -95.71, "pct": 0.6, "area_ha": 2500000},
    {"country": "Canada", "lat": 56.13, "lon": -106.35, "pct": 2.1, "area_ha": 1400000},
    {"country": "Australia", "lat": -25.27, "lon": 133.78, "pct": 8.8, "area_ha": 35700000},
    {"country": "India", "lat": 20.59, "lon": 78.96, "pct": 2.0, "area_ha": 3500000},
    {"country": "China", "lat": 35.86, "lon": 104.20, "pct": 0.6, "area_ha": 3200000},
    {"country": "Brazil", "lat": -14.24, "lon": -51.93, "pct": 0.4, "area_ha": 1200000},
    {"country": "Argentina", "lat": -38.42, "lon": -63.62, "pct": 2.5, "area_ha": 3600000},
    {"country": "New Zealand", "lat": -40.90, "lon": 174.89, "pct": 1.3, "area_ha": 130000},
    {"country": "Japan", "lat": 36.20, "lon": 138.25, "pct": 0.5, "area_ha": 23000},
    {"country": "Mexico", "lat": 23.63, "lon": -102.55, "pct": 0.7, "area_ha": 440000},
    {"country": "Uruguay", "lat": -32.52, "lon": -55.77, "pct": 14.5, "area_ha": 2300000},
    {"country": "Poland", "lat": 51.92, "lon": 19.15, "pct": 3.5, "area_ha": 510000},
    {"country": "Hungary", "lat": 47.16, "lon": 19.50, "pct": 5.7, "area_ha": 300000},
    {"country": "Romania", "lat": 45.94, "lon": 24.97, "pct": 3.0, "area_ha": 400000},
]

# =====================================================================
# 8. FOOD PRODUCTION INDEX DATA (top 30 countries, index base 2015=100)
# =====================================================================
FOOD_PRODUCTION_DATA = [
    {"country": "China", "lat": 35.86, "lon": 104.20, "index": 112, "production_mt": 690, "top_products": "Rice, Wheat, Pork, Vegetables"},
    {"country": "India", "lat": 20.59, "lon": 78.96, "index": 118, "production_mt": 330, "top_products": "Rice, Wheat, Milk, Sugarcane"},
    {"country": "USA", "lat": 37.09, "lon": -95.71, "index": 105, "production_mt": 480, "top_products": "Corn, Soybeans, Beef, Poultry"},
    {"country": "Brazil", "lat": -14.24, "lon": -51.93, "index": 122, "production_mt": 260, "top_products": "Sugarcane, Soybeans, Corn, Coffee"},
    {"country": "Indonesia", "lat": -0.79, "lon": 113.92, "index": 115, "production_mt": 150, "top_products": "Rice, Palm Oil, Rubber, Cocoa"},
    {"country": "Russia", "lat": 61.52, "lon": 105.32, "index": 125, "production_mt": 125, "top_products": "Wheat, Barley, Sunflower, Potatoes"},
    {"country": "France", "lat": 46.23, "lon": 2.21, "index": 98, "production_mt": 72, "top_products": "Wheat, Wine, Dairy, Sugar Beet"},
    {"country": "Germany", "lat": 51.17, "lon": 10.45, "index": 97, "production_mt": 50, "top_products": "Wheat, Pork, Milk, Sugar Beet"},
    {"country": "Turkey", "lat": 38.96, "lon": 35.24, "index": 110, "production_mt": 58, "top_products": "Wheat, Tomatoes, Grapes, Cotton"},
    {"country": "Argentina", "lat": -38.42, "lon": -63.62, "index": 108, "production_mt": 85, "top_products": "Soybeans, Corn, Wheat, Beef"},
    {"country": "Nigeria", "lat": 9.08, "lon": 8.68, "index": 114, "production_mt": 52, "top_products": "Cassava, Yam, Sorghum, Millet"},
    {"country": "Pakistan", "lat": 30.38, "lon": 69.35, "index": 106, "production_mt": 48, "top_products": "Wheat, Cotton, Rice, Sugarcane"},
    {"country": "Mexico", "lat": 23.63, "lon": -102.55, "index": 103, "production_mt": 40, "top_products": "Corn, Avocado, Tomato, Sugarcane"},
    {"country": "Thailand", "lat": 15.87, "lon": 100.99, "index": 102, "production_mt": 42, "top_products": "Rice, Sugarcane, Rubber, Cassava"},
    {"country": "Vietnam", "lat": 14.06, "lon": 108.28, "index": 116, "production_mt": 50, "top_products": "Rice, Coffee, Pepper, Cashew"},
    {"country": "Australia", "lat": -25.27, "lon": 133.78, "index": 99, "production_mt": 35, "top_products": "Wheat, Beef, Wool, Barley"},
    {"country": "Canada", "lat": 56.13, "lon": -106.35, "index": 107, "production_mt": 55, "top_products": "Canola, Wheat, Barley, Lentils"},
    {"country": "Spain", "lat": 40.46, "lon": -3.75, "index": 101, "production_mt": 45, "top_products": "Olive Oil, Wine, Pork, Citrus"},
    {"country": "Italy", "lat": 41.87, "lon": 12.57, "index": 96, "production_mt": 30, "top_products": "Wine, Olive Oil, Tomato, Wheat"},
    {"country": "Egypt", "lat": 26.82, "lon": 30.80, "index": 109, "production_mt": 28, "top_products": "Wheat, Rice, Sugarcane, Citrus"},
    {"country": "Bangladesh", "lat": 23.68, "lon": 90.36, "index": 120, "production_mt": 38, "top_products": "Rice, Jute, Fish, Vegetables"},
    {"country": "Ethiopia", "lat": 9.15, "lon": 40.49, "index": 112, "production_mt": 20, "top_products": "Coffee, Teff, Wheat, Maize"},
    {"country": "Poland", "lat": 51.92, "lon": 19.15, "index": 104, "production_mt": 32, "top_products": "Wheat, Rapeseed, Pork, Potatoes"},
    {"country": "UK", "lat": 55.38, "lon": -3.44, "index": 95, "production_mt": 22, "top_products": "Wheat, Barley, Dairy, Beef"},
    {"country": "Ukraine", "lat": 48.38, "lon": 31.17, "index": 130, "production_mt": 60, "top_products": "Wheat, Corn, Sunflower, Barley"},
    {"country": "Japan", "lat": 36.20, "lon": 138.25, "index": 93, "production_mt": 12, "top_products": "Rice, Vegetables, Pork, Dairy"},
    {"country": "South Africa", "lat": -30.56, "lon": 22.94, "index": 100, "production_mt": 15, "top_products": "Corn, Sugarcane, Wheat, Citrus"},
    {"country": "Colombia", "lat": 4.57, "lon": -74.30, "index": 111, "production_mt": 18, "top_products": "Coffee, Sugarcane, Palm Oil, Rice"},
    {"country": "Iran", "lat": 32.43, "lon": 53.69, "index": 107, "production_mt": 25, "top_products": "Wheat, Pistachio, Saffron, Rice"},
    {"country": "Kenya", "lat": -0.02, "lon": 37.91, "index": 113, "production_mt": 12, "top_products": "Tea, Corn, Sugarcane, Dairy"},
]

# =====================================================================
# 9. SPICE ROUTES DATA
# =====================================================================
SPICE_TRADE_ROUTES = [
    {
        "name": "Maritime Spice Route (Moluccas to Europe)",
        "color": "#f59e0b",
        "points": [
            [0.5, 127.5],   # Moluccas/Maluku
            [-6.0, 106.8],  # Java/Sunda Strait
            [5.0, 80.0],    # Sri Lanka
            [10.0, 52.0],   # Gulf of Aden
            [12.5, 43.0],   # Bab el-Mandeb
            [30.0, 32.5],   # Suez
            [37.0, 15.0],   # Sicily
            [43.3, 5.4],    # Marseille
            [51.5, -0.1],   # London
        ],
    },
    {
        "name": "India to Rome (Pepper Route)",
        "color": "#ef4444",
        "points": [
            [10.0, 76.2],   # Kerala (Malabar Coast)
            [12.5, 43.0],   # Bab el-Mandeb
            [30.0, 32.5],   # Suez/Red Sea
            [31.2, 29.9],   # Alexandria
            [41.9, 12.5],   # Rome
        ],
    },
    {
        "name": "Silk Road (Land Route - Spices)",
        "color": "#8b5cf6",
        "points": [
            [34.3, 108.9],  # Xi'an, China
            [39.5, 76.0],   # Kashgar
            [39.7, 64.4],   # Bukhara
            [35.7, 51.4],   # Tehran
            [36.2, 37.2],   # Aleppo
            [41.0, 29.0],   # Constantinople/Istanbul
            [45.4, 12.3],   # Venice
        ],
    },
    {
        "name": "Portuguese Spice Route (Cape Route)",
        "color": "#06b6d4",
        "points": [
            [38.7, -9.1],   # Lisbon
            [14.7, -17.5],  # Dakar/Cape Verde
            [-33.9, 18.4],  # Cape of Good Hope
            [-6.1, 39.3],   # Zanzibar
            [15.4, 73.8],   # Goa, India
            [2.2, 102.2],   # Malacca
            [0.5, 127.5],   # Moluccas
        ],
    },
    {
        "name": "Arab Frankincense Route",
        "color": "#10b981",
        "points": [
            [17.0, 54.1],   # Dhofar, Oman
            [15.3, 44.2],   # Sana'a, Yemen
            [12.5, 43.0],   # Aden
            [21.5, 39.2],   # Jeddah
            [30.0, 31.2],   # Cairo
            [33.9, 35.5],   # Beirut
            [36.8, 36.2],   # Antioch
        ],
    },
]

SPICE_GROWING_REGIONS = [
    {"name": "Black Pepper", "lat": 10.0, "lon": 76.2, "region": "Kerala, India",
     "color": "#333333", "notes": "King of Spices, Malabar Coast, vine pepper"},
    {"name": "Cinnamon", "lat": 7.0, "lon": 80.0, "region": "Sri Lanka",
     "color": "#d2691e", "notes": "True Ceylon cinnamon, bark of Cinnamomum verum"},
    {"name": "Cardamom", "lat": 10.5, "lon": 77.0, "region": "Western Ghats, India",
     "color": "#228b22", "notes": "Queen of Spices, Elettaria cardamomum, shade-grown"},
    {"name": "Saffron", "lat": 34.0, "lon": 52.0, "region": "Iran (Khorasan)",
     "color": "#ff4500", "notes": "Most expensive spice, Crocus sativus stigmas"},
    {"name": "Saffron", "lat": 37.5, "lon": -2.5, "region": "La Mancha, Spain",
     "color": "#ff4500", "notes": "European saffron, DOP protected"},
    {"name": "Vanilla", "lat": -18.9, "lon": 47.5, "region": "Madagascar",
     "color": "#deb887", "notes": "World #1, Bourbon vanilla, hand-pollinated orchid"},
    {"name": "Vanilla", "lat": 19.5, "lon": -96.9, "region": "Veracruz, Mexico",
     "color": "#deb887", "notes": "Origin of vanilla, Totonac people discovery"},
    {"name": "Clove", "lat": 0.5, "lon": 127.5, "region": "Maluku Islands, Indonesia",
     "color": "#8b0000", "notes": "Original Spice Islands, dried flower buds"},
    {"name": "Clove", "lat": -6.2, "lon": 39.2, "region": "Zanzibar, Tanzania",
     "color": "#8b0000", "notes": "Spice Island of Africa, colonial plantations"},
    {"name": "Nutmeg", "lat": -3.7, "lon": 128.2, "region": "Banda Islands, Indonesia",
     "color": "#cd853f", "notes": "Nutmeg and mace, seed of Myristica fragrans"},
    {"name": "Turmeric", "lat": 15.5, "lon": 78.0, "region": "Andhra Pradesh, India",
     "color": "#ffd700", "notes": "Golden spice, rhizome of Curcuma longa"},
    {"name": "Chili Pepper", "lat": 18.0, "lon": -97.0, "region": "Oaxaca, Mexico",
     "color": "#dc143c", "notes": "Origin of all chili peppers, Capsicum annuum"},
    {"name": "Star Anise", "lat": 22.0, "lon": 108.0, "region": "Guangxi, China",
     "color": "#a0522d", "notes": "Illicium verum, key ingredient in five-spice"},
    {"name": "Ginger", "lat": 10.0, "lon": 76.2, "region": "Kerala, India",
     "color": "#daa520", "notes": "Rhizome of Zingiber officinale, tropical crop"},
]

# =====================================================================
# AGRICULTURE PRESETS (for Overpass-based maps)
# =====================================================================
AGRI_PRESETS = {
    "Custom": None,
    "Tuscany, Italy (Chianti)": {"lat": 43.45, "lon": 11.25, "radius": 10},
    "Champagne, France": {"lat": 49.05, "lon": 3.95, "radius": 10},
    "Napa Valley, California": {"lat": 38.50, "lon": -122.33, "radius": 8},
    "Loire Valley, France": {"lat": 47.38, "lon": 0.69, "radius": 12},
    "Dutch Polders, Netherlands": {"lat": 52.50, "lon": 5.00, "radius": 10},
    "Po Valley, Italy": {"lat": 45.20, "lon": 10.50, "radius": 15},
    "Andalusia, Spain": {"lat": 37.50, "lon": -4.00, "radius": 15},
    "Punjab, India": {"lat": 31.00, "lon": 75.50, "radius": 20},
    "Iowa, USA (Corn Belt)": {"lat": 42.00, "lon": -93.50, "radius": 15},
    "Mekong Delta, Vietnam": {"lat": 10.00, "lon": 106.00, "radius": 12},
    "Barossa Valley, Australia": {"lat": -34.56, "lon": 138.95, "radius": 8},
    "Douro Valley, Portugal": {"lat": 41.15, "lon": -7.75, "radius": 10},
}


# =====================================================================
# OVERPASS QUERY FUNCTIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _query_harbors(south, west, north, east):
    """Query fishing harbors via Overpass."""
    bbox = f"{south},{west},{north},{east}"
    q = f"""
[out:json][timeout:60];
(
  node["leisure"="marina"]({bbox});
  node["harbour"="yes"]({bbox});
  node["seamark:type"="harbour"]({bbox});
  way["leisure"="marina"]({bbox});
  way["harbour"="yes"]({bbox});
);
out center;
"""
    result = query_overpass(q)
    if result is None or "_error" in result:
        return []
    harbors = []
    for el in result.get("elements", []):
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat and lon:
            name = el.get("tags", {}).get("name", "Harbor/Marina")
            harbors.append({"name": name, "lat": lat, "lon": lon})
    return harbors


@st.cache_data(ttl=3600)
def _query_organic_farms(south, west, north, east):
    """Query organic farms/features via Overpass."""
    bbox = f"{south},{west},{north},{east}"
    q = f"""
[out:json][timeout:90];
(
  node["organic"="yes"]({bbox});
  way["organic"="yes"]({bbox});
  node["organic"="only"]({bbox});
  way["organic"="only"]({bbox});
  node["shop"="organic"]({bbox});
  way["shop"="organic"]({bbox});
);
out center;
"""
    result = query_overpass(q)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        return {"error": err, "features": []}
    features = []
    for el in result.get("elements", []):
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat and lon:
            tags = el.get("tags", {})
            name = tags.get("name", "Organic feature")
            ftype = "shop" if tags.get("shop") == "organic" else "farm"
            features.append({"name": name, "lat": lat, "lon": lon, "type": ftype, "tags": tags})
    return {"features": features}


@st.cache_data(ttl=3600)
def _query_irrigation(south, west, north, east):
    """Query irrigation canals and ditches near farmland via Overpass."""
    bbox = f"{south},{west},{north},{east}"
    q = f"""
[out:json][timeout:90];
(
  way["waterway"="canal"]({bbox});
  way["waterway"="ditch"]({bbox});
  way["waterway"="irrigation"]({bbox});
  way["man_made"="irrigation"]({bbox});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(q)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        return {"error": err, "features": []}
    node_lookup = {}
    for el in result.get("elements", []):
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])
    features = []
    for el in result.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags", {})
        if not tags:
            continue
        nodes = el.get("nodes", [])
        coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
        if len(coords) < 2:
            continue
        wtype = tags.get("waterway", tags.get("man_made", "canal"))
        name = tags.get("name", f"{wtype.title()} channel")
        lat = sum(c[0] for c in coords) / len(coords)
        lon = sum(c[1] for c in coords) / len(coords)
        features.append({"name": name, "lat": lat, "lon": lon, "type": wtype, "coords": coords})
    return {"features": features}


@st.cache_data(ttl=3600)
def _query_agri_landuse(south, west, north, east):
    """Query agricultural land use: farmland, orchard, vineyard, meadow."""
    bbox = f"{south},{west},{north},{east}"
    q = f"""
[out:json][timeout:90];
(
  way["landuse"="farmland"]({bbox});
  way["landuse"="orchard"]({bbox});
  way["landuse"="vineyard"]({bbox});
  way["landuse"="meadow"]({bbox});
  relation["landuse"="farmland"]({bbox});
  relation["landuse"="orchard"]({bbox});
  relation["landuse"="vineyard"]({bbox});
  relation["landuse"="meadow"]({bbox});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(q)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        return {"error": err, "features": []}
    node_lookup = {}
    for el in result.get("elements", []):
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])
    features = []
    seen = set()
    for el in result.get("elements", []):
        tags = el.get("tags", {})
        if not tags:
            continue
        eid = el.get("id")
        if eid in seen:
            continue
        seen.add(eid)
        landuse = tags.get("landuse", "")
        if landuse not in AGRI_LANDUSE_COLORS:
            continue
        coords = []
        if el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
        if not coords:
            if "lat" in el and "lon" in el:
                lat, lon = el["lat"], el["lon"]
            else:
                continue
        else:
            lat = sum(c[0] for c in coords) / len(coords)
            lon = sum(c[1] for c in coords) / len(coords)
        name = tags.get("name", f"{landuse.title()} area")
        crop = tags.get("crop", tags.get("produce", ""))
        features.append({
            "name": name, "lat": lat, "lon": lon,
            "landuse": landuse, "crop": crop,
            "color": AGRI_LANDUSE_COLORS.get(landuse, "#10b981"),
            "coords": coords,
        })
    return {"features": features}


# =====================================================================
# CHART HELPER
# =====================================================================
def _dark_bar_chart(labels, values, title, color="#10b981", ylabel=""):
    """Create a dark-themed bar chart and return as BytesIO buffer."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    bars = ax.barh(labels, values, color=color, edgecolor="#2a3550", linewidth=0.5)
    ax.set_xlabel(ylabel, color="#8b97b0", fontsize=10)
    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.invert_yaxis()
    ax.xaxis.grid(True, color="#2a3550", alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor="#0a0e1a", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _dark_pie_chart(labels, values, colors, title):
    """Create a dark-themed pie chart and return as BytesIO buffer."""
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors, autopct="%1.1f%%",
        textprops={"color": "#e8ecf4", "fontsize": 9},
        wedgeprops={"edgecolor": "#2a3550", "linewidth": 0.5},
        pctdistance=0.82,
    )
    for t in autotexts:
        t.set_color("#e8ecf4")
        t.set_fontsize(8)
    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor="#0a0e1a", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# =====================================================================
# FOLIUM MAP HELPER
# =====================================================================
def _create_base_map(lat=20.0, lon=0.0, zoom=2):
    """Create a dark-themed folium map."""
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)
    return m


def _bbox_from_center(lat, lon, radius_km):
    """Compute bounding box from center and radius."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.01, abs(math.cos(math.radians(lat)))))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


# =====================================================================
# MAP RENDER FUNCTIONS
# =====================================================================

def _render_crop_regions():
    """1. Global Crop Regions."""
    st.markdown("#### Global Crop Regions")
    st.caption("Major crop zones worldwide with production data.")

    crop_filter = st.multiselect(
        "Filter by crop", list(CROP_COLORS.keys()),
        default=list(CROP_COLORS.keys()), key="ag_crop_filter",
    )

    if not crop_filter:
        st.warning("Select at least one crop type.")
        return

    filtered = [r for r in CROP_REGIONS if r["crop"] in crop_filter]

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Regions Shown", len(filtered))
    with c2:
        st.metric("Total Production", f"{sum(r['production_mt'] for r in filtered):.0f} Mt")
    with c3:
        st.metric("Total Area", f"{sum(r['area_mha'] for r in filtered):.1f} Mha")
    with c4:
        st.metric("Crop Types", len(crop_filter))

    # Legend
    legend_items = " ".join([
        f'<span style="color:{CROP_COLORS[c]}; font-size:0.8rem;">\u25cf {c}</span>'
        for c in crop_filter
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.7rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    # Map
    m = _create_base_map(lat=20.0, lon=0.0, zoom=2)
    for r in filtered:
        color = CROP_COLORS.get(r["crop"], "#10b981")
        popup_html = (
            f"<b>{escape(r['region'])}</b><br/>"
            f"Crop: {escape(r['crop'])}<br/>"
            f"Production: {r['production_mt']} Mt<br/>"
            f"Area: {r['area_mha']} Mha<br/>"
            f"Countries: {escape(r['countries'])}<br/>"
            f"<i>{escape(r['notes'])}</i>"
        )
        folium.Polygon(
            locations=r["polygon"],
            color=color, fill=True, fill_color=color,
            fill_opacity=0.25, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{r['crop']} - {r['region']}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart
    crop_prod = {}
    for r in filtered:
        crop_prod[r["crop"]] = crop_prod.get(r["crop"], 0) + r["production_mt"]
    if crop_prod:
        labels = list(crop_prod.keys())
        vals = list(crop_prod.values())
        colors = [CROP_COLORS.get(c, "#10b981") for c in labels]
        buf = _dark_pie_chart(labels, vals, colors, "Production by Crop Type (Mt)")
        st.image(buf, width=500)

    # Data table
    st.markdown("#### Crop Region Details")
    df = pd.DataFrame(filtered)
    df = df[["crop", "region", "production_mt", "area_mha", "countries", "notes"]]
    df.columns = ["Crop", "Region", "Production (Mt)", "Area (Mha)", "Countries", "Notes"]
    st.dataframe(df, width="stretch")

    # Download
    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False, encoding="utf-8")
    csv_buf.seek(0)
    st.download_button("Download Crop Regions CSV", csv_buf, "crop_regions.csv", "text/csv")


def _render_wine_regions():
    """2. Wine Regions."""
    st.markdown("#### World Wine Regions")
    st.caption("30+ premier wine regions with grape varieties and climate data.")

    country_filter = st.multiselect(
        "Filter by country",
        sorted(set(w["country"] for w in WINE_REGIONS)),
        default=sorted(set(w["country"] for w in WINE_REGIONS)),
        key="ag_wine_country",
    )

    filtered = [w for w in WINE_REGIONS if w["country"] in country_filter]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Wine Regions", len(filtered))
    with c2:
        st.metric("Countries", len(set(w["country"] for w in filtered)))
    with c3:
        st.metric("Total Vineyard Area", f"{sum(w['area_ha'] for w in filtered):,.0f} ha")

    m = _create_base_map(lat=35.0, lon=10.0, zoom=3)
    for w in filtered:
        color = WINE_COLORS.get(w["country"], "#8b97b0")
        popup_html = (
            f"<b>{escape(w['name'])}</b><br/>"
            f"Country: {escape(w['country'])}<br/>"
            f"Grapes: {escape(w['grapes'])}<br/>"
            f"Climate: {escape(w['climate'])}<br/>"
            f"Area: {w['area_ha']:,} ha<br/>"
            f"<i>{escape(w['notes'])}</i>"
        )
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=max(4, min(14, w["area_ha"] / 8000)),
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{w['name']} ({w['country']})",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: Top 10 by area
    sorted_wines = sorted(filtered, key=lambda x: x["area_ha"], reverse=True)[:15]
    if sorted_wines:
        labels = [f"{w['name']} ({w['country']})" for w in sorted_wines]
        vals = [w["area_ha"] for w in sorted_wines]
        buf = _dark_bar_chart(labels[::-1], vals[::-1], "Top Wine Regions by Vineyard Area (ha)", "#8b5cf6", "Hectares")
        st.image(buf, width=700)

    st.markdown("#### Wine Region Details")
    df = pd.DataFrame(filtered)
    df = df[["name", "country", "grapes", "climate", "area_ha", "notes"]]
    df.columns = ["Region", "Country", "Key Grapes", "Climate", "Area (ha)", "Notes"]
    st.dataframe(df, width="stretch")

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False, encoding="utf-8")
    csv_buf.seek(0)
    st.download_button("Download Wine Regions CSV", csv_buf, "wine_regions.csv", "text/csv")


def _render_fishing_zones():
    """3. Fishing Zones."""
    st.markdown("#### FAO Fishing Zones")
    st.caption("Global fishing areas with catch data. Harbors loaded from OpenStreetMap.")

    show_harbors = st.checkbox("Load harbors from Overpass (optional, slower)", value=False, key="ag_fish_harbors")

    harbor_lat = 45.0
    harbor_lon = 12.0
    harbor_radius = 10
    if show_harbors:
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            harbor_lat = st.number_input("Harbor search lat", value=45.0, format="%.2f", key="ag_h_lat")
        with hc2:
            harbor_lon = st.number_input("Harbor search lon", value=12.0, format="%.2f", key="ag_h_lon")
        with hc3:
            harbor_radius = st.slider("Radius (km)", 5, 50, 10, key="ag_h_rad")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("FAO Zones", len(FAO_FISHING_ZONES))
    with c2:
        st.metric("Total Catch", f"{sum(z['catch_mt'] for z in FAO_FISHING_ZONES):.1f} Mt")
    with c3:
        top_zone = max(FAO_FISHING_ZONES, key=lambda z: z["catch_mt"])
        st.metric("Top Zone", top_zone["name"][:20])

    m = _create_base_map(lat=10.0, lon=0.0, zoom=2)

    zone_colors = ["#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
                    "#ec4899", "#3b82f6", "#f97316", "#14b8a6", "#84cc16",
                    "#22c55e", "#a855f7"]

    for i, z in enumerate(FAO_FISHING_ZONES):
        color = zone_colors[i % len(zone_colors)]
        popup_html = (
            f"<b>{escape(z['name'])}</b><br/>"
            f"Catch: {z['catch_mt']} Mt/yr<br/>"
            f"Key Species: {escape(z['species'])}<br/>"
            f"<i>{escape(z['notes'])}</i>"
        )
        folium.Polygon(
            locations=z["polygon"],
            color=color, fill=True, fill_color=color,
            fill_opacity=0.12, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=z["name"],
        ).add_to(m)

    if show_harbors:
        with st.spinner("Loading harbors from OpenStreetMap..."):
            south, west, north, east = _bbox_from_center(harbor_lat, harbor_lon, harbor_radius)
            harbors = _query_harbors(south, west, north, east)
        if harbors:
            st.info(f"Found {len(harbors)} harbors/marinas in the search area.")
            for h in harbors[:200]:
                folium.CircleMarker(
                    location=[h["lat"], h["lon"]],
                    radius=4, color="#f59e0b", fill=True,
                    fill_color="#f59e0b", fill_opacity=0.8,
                    popup=folium.Popup(f"<b>{escape(h['name'])}</b>", max_width=200),
                    tooltip=escape(h["name"]),
                ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart
    sorted_zones = sorted(FAO_FISHING_ZONES, key=lambda z: z["catch_mt"], reverse=True)
    labels = [z["name"] for z in sorted_zones]
    vals = [z["catch_mt"] for z in sorted_zones]
    buf = _dark_bar_chart(labels[::-1], vals[::-1], "FAO Fishing Zones by Annual Catch (Mt)", "#06b6d4", "Million Tonnes")
    st.image(buf, width=700)

    st.markdown("#### Fishing Zone Details")
    df = pd.DataFrame(FAO_FISHING_ZONES)
    df = df[["name", "code", "catch_mt", "species", "notes"]]
    df.columns = ["Zone", "FAO Code", "Catch (Mt/yr)", "Key Species", "Notes"]
    st.dataframe(df, width="stretch")

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False, encoding="utf-8")
    csv_buf.seek(0)
    st.download_button("Download Fishing Zones CSV", csv_buf, "fao_fishing_zones.csv", "text/csv")


def _render_livestock():
    """4. Livestock Distribution."""
    st.markdown("#### Global Livestock Distribution")
    st.caption("Cattle, sheep, goat, pig, poultry density by country (million head).")

    animal_type = st.selectbox(
        "Livestock type", list(LIVESTOCK_COLORS.keys()), key="ag_livestock_type",
    )
    animal_key = animal_type.lower()

    c1, c2, c3, c4 = st.columns(4)
    all_vals = [d[animal_key] for d in LIVESTOCK_DATA if d[animal_key] > 0]
    with c1:
        st.metric("Countries", len([v for v in all_vals if v > 0]))
    with c2:
        st.metric("Total (M head)", f"{sum(all_vals):,.0f}")
    with c3:
        top_country = max(LIVESTOCK_DATA, key=lambda d: d[animal_key])
        st.metric("Top Producer", top_country["country"])
    with c4:
        st.metric("Top Count (M)", f"{top_country[animal_key]:,.0f}")

    color = LIVESTOCK_COLORS.get(animal_type, "#10b981")
    m = _create_base_map(lat=20.0, lon=0.0, zoom=2)

    max_val = max(all_vals) if all_vals else 1
    for d in LIVESTOCK_DATA:
        val = d[animal_key]
        if val <= 0:
            continue
        radius = max(4, min(30, (val / max_val) * 30))
        popup_html = (
            f"<b>{escape(d['country'])}</b><br/>"
            f"{escape(animal_type)}: {val:,.1f}M head<br/>"
            f"Cattle: {d['cattle']:,.1f}M | Sheep: {d['sheep']:,.1f}M<br/>"
            f"Goat: {d['goat']:,.1f}M | Pig: {d['pig']:,.1f}M<br/>"
            f"Poultry: {d['poultry']:,.0f}M"
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.55, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{d['country']}: {val:,.1f}M {animal_type}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: top 15
    sorted_data = sorted(LIVESTOCK_DATA, key=lambda d: d[animal_key], reverse=True)
    top15 = [d for d in sorted_data if d[animal_key] > 0][:15]
    if top15:
        labels = [d["country"] for d in top15]
        vals = [d[animal_key] for d in top15]
        buf = _dark_bar_chart(labels[::-1], vals[::-1],
                              f"Top 15 Countries: {animal_type} (Million Head)", color, "Million Head")
        st.image(buf, width=700)

    st.markdown("#### Livestock Data Table")
    df = pd.DataFrame(LIVESTOCK_DATA)
    df = df[["country", "cattle", "sheep", "goat", "pig", "poultry"]]
    df.columns = ["Country", "Cattle (M)", "Sheep (M)", "Goat (M)", "Pig (M)", "Poultry (M)"]
    st.dataframe(df, width="stretch")

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False, encoding="utf-8")
    csv_buf.seek(0)
    st.download_button("Download Livestock CSV", csv_buf, "livestock_distribution.csv", "text/csv")


def _render_coffee_tea():
    """5. Coffee & Tea Origins."""
    st.markdown("#### Coffee & Tea Origins")
    st.caption("Major coffee and tea producing regions worldwide.")

    show_type = st.radio("Show", ["Both", "Coffee only", "Tea only"], horizontal=True, key="ag_ct_type")

    coffee_list = COFFEE_ORIGINS if show_type in ["Both", "Coffee only"] else []
    tea_list = TEA_ORIGINS if show_type in ["Both", "Tea only"] else []
    all_items = coffee_list + tea_list

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Coffee Origins", len(coffee_list))
    with c2:
        st.metric("Tea Origins", len(tea_list))
    with c3:
        total_prod = sum(i["production_mt"] for i in all_items)
        st.metric("Total Production", f"{total_prod:.1f} Mt")

    m = _create_base_map(lat=10.0, lon=50.0, zoom=2)

    # Coffee belt shading
    if show_type in ["Both", "Coffee only"]:
        folium.Polygon(
            locations=[[23.5, -180], [23.5, 180], [-23.5, 180], [-23.5, -180]],
            color="#92400e", fill=True, fill_color="#92400e",
            fill_opacity=0.06, weight=1,
            tooltip="Coffee Belt (Tropic of Cancer to Capricorn)",
        ).add_to(m)

    for item in all_items:
        is_coffee = item["type"] == "coffee"
        color = "#92400e" if is_coffee else "#10b981"
        icon_prefix = "\u2615" if is_coffee else "\ud83c\udf75"
        popup_html = (
            f"<b>{icon_prefix} {escape(item['name'])}</b><br/>"
            f"Type: {escape(item['type'].title())}<br/>"
            f"Variety: {escape(item['variety'])}<br/>"
            f"Production: {item['production_mt']} Mt/yr<br/>"
            f"<i>{escape(item['notes'])}</i>"
        )
        radius = max(5, min(15, item["production_mt"] * 5))
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{item['name']} ({item['type'].title()})",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=550)

    # Charts
    if coffee_list:
        sorted_c = sorted(coffee_list, key=lambda x: x["production_mt"], reverse=True)[:12]
        labels = [c["name"] for c in sorted_c]
        vals = [c["production_mt"] for c in sorted_c]
        buf = _dark_bar_chart(labels[::-1], vals[::-1], "Top Coffee Producers (Mt/yr)", "#92400e", "Million Tonnes")
        st.image(buf, width=700)

    if tea_list:
        sorted_t = sorted(tea_list, key=lambda x: x["production_mt"], reverse=True)
        labels = [t["name"] for t in sorted_t]
        vals = [t["production_mt"] for t in sorted_t]
        buf = _dark_bar_chart(labels[::-1], vals[::-1], "Tea Producers (Mt/yr)", "#10b981", "Million Tonnes")
        st.image(buf, width=700)

    st.markdown("#### Origin Details")
    df_data = []
    for item in all_items:
        df_data.append({
            "Name": item["name"],
            "Type": item["type"].title(),
            "Variety": item["variety"],
            "Production (Mt)": item["production_mt"],
            "Notes": item["notes"],
        })
    df = pd.DataFrame(df_data)
    st.dataframe(df, width="stretch")

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False, encoding="utf-8")
    csv_buf.seek(0)
    st.download_button("Download Coffee & Tea CSV", csv_buf, "coffee_tea_origins.csv", "text/csv")


def _render_organic_farming():
    """6. Organic Farming."""
    st.markdown("#### Organic Farming Explorer")
    st.caption("Organic farming percentage by country + Overpass organic features search.")

    sub_mode = st.radio("View", ["Country Overview", "Overpass Search"], horizontal=True, key="ag_org_mode")

    if sub_mode == "Country Overview":
        sorted_org = sorted(ORGANIC_FARMING_PCT, key=lambda x: x["pct"], reverse=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Countries", len(sorted_org))
        with c2:
            st.metric("Highest %", f"{sorted_org[0]['pct']}% ({sorted_org[0]['country']})")
        with c3:
            total_ha = sum(o["area_ha"] for o in sorted_org)
            st.metric("Total Organic Area", f"{total_ha / 1e6:.1f} Mha")

        m = _create_base_map(lat=30.0, lon=10.0, zoom=2)
        max_pct = max(o["pct"] for o in sorted_org)
        for o in sorted_org:
            radius = max(5, min(22, (o["pct"] / max_pct) * 22))
            green_intensity = min(255, int(100 + (o["pct"] / max_pct) * 155))
            color = f"#00{green_intensity:02x}00"
            popup_html = (
                f"<b>{escape(o['country'])}</b><br/>"
                f"Organic: {o['pct']}% of farmland<br/>"
                f"Area: {o['area_ha']:,} ha"
            )
            folium.CircleMarker(
                location=[o["lat"], o["lon"]],
                radius=radius,
                color=color, fill=True, fill_color=color,
                fill_opacity=0.6, weight=2,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{o['country']}: {o['pct']}%",
            ).add_to(m)

        folium.LayerControl().add_to(m)
        components.html(m._repr_html_(), height=550)

        # Chart
        top20 = sorted_org[:20]
        labels = [o["country"] for o in top20]
        vals = [o["pct"] for o in top20]
        buf = _dark_bar_chart(labels[::-1], vals[::-1], "Organic Farming (% of Agricultural Land)", "#10b981", "%")
        st.image(buf, width=700)

        st.markdown("#### Organic Farming by Country")
        df = pd.DataFrame(sorted_org)
        df = df[["country", "pct", "area_ha"]]
        df.columns = ["Country", "Organic %", "Organic Area (ha)"]
        st.dataframe(df, width="stretch")

        csv_buf = io.BytesIO()
        df.to_csv(csv_buf, index=False, encoding="utf-8")
        csv_buf.seek(0)
        st.download_button("Download Organic Farming CSV", csv_buf, "organic_farming.csv", "text/csv")

    else:
        # Overpass search
        col1, col2, col3 = st.columns(3)
        with col1:
            org_lat = st.number_input("Latitude", value=47.52, format="%.4f", key="ag_org_lat")
        with col2:
            org_lon = st.number_input("Longitude", value=14.55, format="%.4f", key="ag_org_lon")
        with col3:
            org_radius = st.slider("Radius (km)", 1, 30, 10, key="ag_org_rad")

        preset_name = st.selectbox("Presets", list(AGRI_PRESETS.keys()), key="ag_org_preset")
        if preset_name != "Custom" and AGRI_PRESETS.get(preset_name):
            p = AGRI_PRESETS[preset_name]
            org_lat = p["lat"]
            org_lon = p["lon"]
            org_radius = p["radius"]

        if st.button("Search Organic Features", key="ag_org_search", type="primary"):
            south, west, north, east = _bbox_from_center(org_lat, org_lon, org_radius)
            with st.spinner("Searching for organic features via OpenStreetMap..."):
                result = _query_organic_farms(south, west, north, east)
            if "error" in result:
                st.error(f"Overpass error: {result['error']}")
                return
            features = result.get("features", [])
            if not features:
                st.warning("No organic features found. Try a larger radius or different location.")
                return

            st.success(f"Found {len(features)} organic features.")

            c1, c2 = st.columns(2)
            farms = [f for f in features if f["type"] == "farm"]
            shops = [f for f in features if f["type"] == "shop"]
            with c1:
                st.metric("Organic Farms/Locations", len(farms))
            with c2:
                st.metric("Organic Shops", len(shops))

            m = _create_base_map(lat=org_lat, lon=org_lon, zoom=12)
            folium.Circle(
                location=[org_lat, org_lon],
                radius=org_radius * 1000,
                color="#10b981", fill=True, fill_opacity=0.03, weight=1,
            ).add_to(m)
            for f in features[:300]:
                color = "#10b981" if f["type"] == "farm" else "#3b82f6"
                popup_html = f"<b>{escape(f['name'])}</b><br/>Type: {escape(f['type'])}"
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=6, color=color, fill=True, fill_color=color,
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=escape(f["name"]),
                ).add_to(m)

            folium.LayerControl().add_to(m)
            components.html(m._repr_html_(), height=550)

            df_data = [{"Name": f["name"], "Type": f["type"], "Lat": f["lat"], "Lon": f["lon"]} for f in features]
            df = pd.DataFrame(df_data)
            st.dataframe(df, width="stretch")

            csv_buf = io.BytesIO()
            df.to_csv(csv_buf, index=False, encoding="utf-8")
            csv_buf.seek(0)
            st.download_button("Download Organic Features CSV", csv_buf, "organic_features.csv", "text/csv")


def _render_irrigation():
    """7. Irrigation Systems."""
    st.markdown("#### Irrigation Systems")
    st.caption("Canals, ditches, and irrigation infrastructure from OpenStreetMap.")

    col1, col2, col3 = st.columns(3)
    with col1:
        irr_lat = st.number_input("Latitude", value=45.20, format="%.4f", key="ag_irr_lat")
    with col2:
        irr_lon = st.number_input("Longitude", value=10.50, format="%.4f", key="ag_irr_lon")
    with col3:
        irr_radius = st.slider("Radius (km)", 1, 25, 8, key="ag_irr_rad")

    preset_name = st.selectbox("Presets", list(AGRI_PRESETS.keys()), key="ag_irr_preset")
    if preset_name != "Custom" and AGRI_PRESETS.get(preset_name):
        p = AGRI_PRESETS[preset_name]
        irr_lat = p["lat"]
        irr_lon = p["lon"]
        irr_radius = p["radius"]

    if st.button("Search Irrigation Infrastructure", key="ag_irr_search", type="primary"):
        south, west, north, east = _bbox_from_center(irr_lat, irr_lon, irr_radius)
        with st.spinner("Searching for irrigation features..."):
            result = _query_irrigation(south, west, north, east)

        if "error" in result:
            st.error(f"Overpass error: {result['error']}")
            return
        features = result.get("features", [])
        if not features:
            st.warning("No irrigation features found. Try a larger radius or different location.")
            return

        st.success(f"Found {len(features)} irrigation channels.")

        type_counts = {}
        for f in features:
            t = f["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        cols = st.columns(min(4, len(type_counts) + 1))
        with cols[0]:
            st.metric("Total Channels", len(features))
        for i, (t, cnt) in enumerate(type_counts.items()):
            if i + 1 < len(cols):
                with cols[i + 1]:
                    st.metric(t.title(), cnt)

        m = _create_base_map(lat=irr_lat, lon=irr_lon, zoom=12)
        folium.Circle(
            location=[irr_lat, irr_lon],
            radius=irr_radius * 1000,
            color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
        ).add_to(m)

        type_colors = {"canal": "#06b6d4", "ditch": "#3b82f6", "irrigation": "#10b981"}
        for f in features[:500]:
            color = type_colors.get(f["type"], "#8b97b0")
            if f["coords"] and len(f["coords"]) >= 2:
                folium.PolyLine(
                    locations=f["coords"],
                    color=color, weight=2, opacity=0.7,
                    popup=folium.Popup(f"<b>{escape(f['name'])}</b><br/>Type: {escape(f['type'])}", max_width=200),
                    tooltip=escape(f["name"]),
                ).add_to(m)
            else:
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=4, color=color, fill=True, fill_color=color,
                    fill_opacity=0.7, weight=1,
                    popup=folium.Popup(f"<b>{escape(f['name'])}</b>", max_width=200),
                ).add_to(m)

        folium.LayerControl().add_to(m)
        components.html(m._repr_html_(), height=550)

        # Chart
        if type_counts:
            labels = list(type_counts.keys())
            vals = list(type_counts.values())
            colors = [type_colors.get(t, "#8b97b0") for t in labels]
            buf = _dark_pie_chart(labels, vals, colors, "Irrigation Channel Types")
            st.image(buf, width=450)

        st.markdown("#### Irrigation Details")
        df_data = [{"Name": f["name"], "Type": f["type"], "Lat": round(f["lat"], 5), "Lon": round(f["lon"], 5)}
                   for f in features]
        df = pd.DataFrame(df_data)
        st.dataframe(df, width="stretch")

        csv_buf = io.BytesIO()
        df.to_csv(csv_buf, index=False, encoding="utf-8")
        csv_buf.seek(0)
        st.download_button("Download Irrigation CSV", csv_buf, "irrigation_systems.csv", "text/csv")


def _render_food_production():
    """8. Food Production Index."""
    st.markdown("#### Food Production Index (Top 30 Countries)")
    st.caption("FAO food production data by country with production index (base 2015=100).")

    sort_by = st.selectbox("Sort by", ["Production (Mt)", "Food Index", "Country Name"], key="ag_fpi_sort")

    if sort_by == "Production (Mt)":
        sorted_data = sorted(FOOD_PRODUCTION_DATA, key=lambda x: x["production_mt"], reverse=True)
    elif sort_by == "Food Index":
        sorted_data = sorted(FOOD_PRODUCTION_DATA, key=lambda x: x["index"], reverse=True)
    else:
        sorted_data = sorted(FOOD_PRODUCTION_DATA, key=lambda x: x["country"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Countries", len(sorted_data))
    with c2:
        st.metric("Total Production", f"{sum(d['production_mt'] for d in sorted_data):,} Mt")
    with c3:
        top_prod = max(sorted_data, key=lambda d: d["production_mt"])
        st.metric("Top Producer", top_prod["country"])
    with c4:
        avg_idx = sum(d["index"] for d in sorted_data) / len(sorted_data)
        st.metric("Avg Index", f"{avg_idx:.0f}")

    m = _create_base_map(lat=20.0, lon=0.0, zoom=2)
    max_prod = max(d["production_mt"] for d in sorted_data)
    for d in sorted_data:
        radius = max(5, min(25, (d["production_mt"] / max_prod) * 25))
        # Color based on index: green if growing, red if declining
        if d["index"] >= 110:
            color = "#10b981"
        elif d["index"] >= 100:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        popup_html = (
            f"<b>{escape(d['country'])}</b><br/>"
            f"Production: {d['production_mt']} Mt<br/>"
            f"Food Index: {d['index']} (2015=100)<br/>"
            f"Top Products: {escape(d['top_products'])}"
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.55, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{d['country']}: {d['production_mt']} Mt",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=550)

    # Bar chart - top 20 by production
    top20 = sorted(sorted_data, key=lambda d: d["production_mt"], reverse=True)[:20]
    labels = [d["country"] for d in top20]
    vals = [d["production_mt"] for d in top20]
    buf = _dark_bar_chart(labels[::-1], vals[::-1], "Top 20 Food Producers (Mt)", "#10b981", "Million Tonnes")
    st.image(buf, width=700)

    # Index chart
    idx_sorted = sorted(sorted_data, key=lambda d: d["index"], reverse=True)[:20]
    labels2 = [d["country"] for d in idx_sorted]
    vals2 = [d["index"] for d in idx_sorted]
    buf2 = _dark_bar_chart(labels2[::-1], vals2[::-1], "Food Production Index (2015=100)", "#06b6d4", "Index")
    st.image(buf2, width=700)

    st.markdown("#### Food Production Data")
    df = pd.DataFrame(sorted_data)
    df = df[["country", "production_mt", "index", "top_products"]]
    df.columns = ["Country", "Production (Mt)", "Food Index", "Top Products"]
    st.dataframe(df, width="stretch")

    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False, encoding="utf-8")
    csv_buf.seek(0)
    st.download_button("Download Food Production CSV", csv_buf, "food_production.csv", "text/csv")


def _render_spice_routes():
    """9. Spice Routes."""
    st.markdown("#### Historical Spice Routes & Growing Regions")
    st.caption("Ancient trade routes and current spice-producing regions.")

    show_routes = st.checkbox("Show trade routes", value=True, key="ag_spice_routes")
    show_regions = st.checkbox("Show growing regions", value=True, key="ag_spice_regions")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Trade Routes", len(SPICE_TRADE_ROUTES))
    with c2:
        st.metric("Spice Origins", len(SPICE_GROWING_REGIONS))
    with c3:
        unique_spices = len(set(s["name"] for s in SPICE_GROWING_REGIONS))
        st.metric("Spice Types", unique_spices)

    m = _create_base_map(lat=20.0, lon=60.0, zoom=3)

    if show_routes:
        for route in SPICE_TRADE_ROUTES:
            folium.PolyLine(
                locations=route["points"],
                color=route["color"], weight=3, opacity=0.8,
                dash_array="8 4",
                popup=folium.Popup(f"<b>{escape(route['name'])}</b>", max_width=250),
                tooltip=route["name"],
            ).add_to(m)
            # Start/end markers
            start = route["points"][0]
            end = route["points"][-1]
            folium.CircleMarker(
                location=start, radius=5,
                color=route["color"], fill=True, fill_color=route["color"],
                fill_opacity=0.9, weight=2,
            ).add_to(m)
            folium.CircleMarker(
                location=end, radius=5,
                color=route["color"], fill=True, fill_color=route["color"],
                fill_opacity=0.9, weight=2,
            ).add_to(m)

    if show_regions:
        for s in SPICE_GROWING_REGIONS:
            popup_html = (
                f"<b>{escape(s['name'])}</b><br/>"
                f"Region: {escape(s['region'])}<br/>"
                f"<i>{escape(s['notes'])}</i>"
            )
            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=8,
                color=s["color"], fill=True, fill_color=s["color"],
                fill_opacity=0.8, weight=2,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{s['name']} - {s['region']}",
            ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=550)

    # Route legend
    if show_routes:
        st.markdown("##### Trade Routes")
        route_legend = " | ".join([
            f'<span style="color:{r["color"]};">\u2501\u2501 {r["name"]}</span>'
            for r in SPICE_TRADE_ROUTES
        ])
        st.markdown(f'<div style="font-size:0.85rem;">{route_legend}</div>', unsafe_allow_html=True)

    # Spice regions table
    if show_regions:
        st.markdown("#### Spice Growing Regions")
        df = pd.DataFrame(SPICE_GROWING_REGIONS)
        df = df[["name", "region", "notes"]]
        df.columns = ["Spice", "Region", "Notes"]
        st.dataframe(df, width="stretch")

        csv_buf = io.BytesIO()
        df.to_csv(csv_buf, index=False, encoding="utf-8")
        csv_buf.seek(0)
        st.download_button("Download Spice Regions CSV", csv_buf, "spice_regions.csv", "text/csv")

    # Routes data download
    if show_routes:
        route_data = []
        for r in SPICE_TRADE_ROUTES:
            for i, pt in enumerate(r["points"]):
                route_data.append({"Route": r["name"], "Waypoint": i + 1, "Lat": pt[0], "Lon": pt[1]})
        df_routes = pd.DataFrame(route_data)
        csv_buf2 = io.BytesIO()
        df_routes.to_csv(csv_buf2, index=False, encoding="utf-8")
        csv_buf2.seek(0)
        st.download_button("Download Spice Routes CSV", csv_buf2, "spice_routes.csv", "text/csv")


def _render_agri_landuse():
    """10. Agricultural Land Use."""
    st.markdown("#### Agricultural Land Use")
    st.caption("Farmland, orchards, vineyards, meadows from OpenStreetMap.")

    col1, col2, col3 = st.columns(3)
    with col1:
        alu_lat = st.number_input("Latitude", value=43.45, format="%.4f", key="ag_alu_lat")
    with col2:
        alu_lon = st.number_input("Longitude", value=11.25, format="%.4f", key="ag_alu_lon")
    with col3:
        alu_radius = st.slider("Radius (km)", 1, 20, 5, key="ag_alu_rad")

    preset_name = st.selectbox("Presets", list(AGRI_PRESETS.keys()), key="ag_alu_preset")
    if preset_name != "Custom" and AGRI_PRESETS.get(preset_name):
        p = AGRI_PRESETS[preset_name]
        alu_lat = p["lat"]
        alu_lon = p["lon"]
        alu_radius = p["radius"]

    # Legend
    legend_items = " ".join([
        f'<span style="color:{c}; font-size:0.8rem;">\u25cf {name.title()}</span>'
        for name, c in AGRI_LANDUSE_COLORS.items()
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.7rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    if st.button("Analyze Agricultural Land Use", key="ag_alu_search", type="primary"):
        south, west, north, east = _bbox_from_center(alu_lat, alu_lon, alu_radius)
        with st.spinner("Loading agricultural land use from OpenStreetMap..."):
            result = _query_agri_landuse(south, west, north, east)

        if "error" in result:
            st.error(f"Overpass error: {result['error']}")
            return
        features = result.get("features", [])
        if not features:
            st.warning("No agricultural land use found. Try a larger radius or different location.")
            return

        st.success(f"Found {len(features)} agricultural parcels.")

        # Stats
        type_counts = {}
        for f in features:
            lu = f["landuse"]
            type_counts[lu] = type_counts.get(lu, 0) + 1

        cols = st.columns(min(5, len(type_counts) + 1))
        with cols[0]:
            st.metric("Total Parcels", len(features))
        for i, (lu, cnt) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
            if i + 1 < len(cols):
                with cols[i + 1]:
                    st.metric(lu.title(), cnt)

        # Map
        m = _create_base_map(lat=alu_lat, lon=alu_lon, zoom=13)
        folium.Circle(
            location=[alu_lat, alu_lon],
            radius=alu_radius * 1000,
            color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
        ).add_to(m)

        for f in features[:500]:
            popup_html = (
                f"<b>{escape(f['name'])}</b><br/>"
                f"Type: {escape(f['landuse'].title())}<br/>"
            )
            if f.get("crop"):
                popup_html += f"Crop: {escape(f['crop'])}<br/>"

            if f["coords"] and len(f["coords"]) >= 3:
                folium.Polygon(
                    locations=f["coords"],
                    color=f["color"], fill=True, fill_color=f["color"],
                    fill_opacity=0.35, weight=1,
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=f"{f['landuse'].title()}: {f['name']}",
                ).add_to(m)
            else:
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=5,
                    color=f["color"], fill=True, fill_color=f["color"],
                    fill_opacity=0.6, weight=1,
                    popup=folium.Popup(popup_html, max_width=200),
                ).add_to(m)

        folium.LayerControl().add_to(m)
        components.html(m._repr_html_(), height=550)

        # Chart
        if type_counts:
            labels = list(type_counts.keys())
            vals = list(type_counts.values())
            colors = [AGRI_LANDUSE_COLORS.get(lu, "#10b981") for lu in labels]
            buf = _dark_pie_chart(
                [lu.title() for lu in labels], vals, colors,
                "Agricultural Land Use Breakdown",
            )
            st.image(buf, width=450)

        # Crop types if present
        crop_counts = {}
        for f in features:
            crop = f.get("crop", "")
            if crop:
                crop_counts[crop] = crop_counts.get(crop, 0) + 1
        if crop_counts:
            st.markdown("##### Identified Crops")
            sorted_crops = sorted(crop_counts.items(), key=lambda x: -x[1])[:15]
            labels_c = [c[0] for c in sorted_crops]
            vals_c = [c[1] for c in sorted_crops]
            buf_c = _dark_bar_chart(labels_c[::-1], vals_c[::-1], "Crop Types Found", "#10b981", "Count")
            st.image(buf_c, width=600)

        st.markdown("#### Agricultural Parcels")
        df_data = [{
            "Name": f["name"],
            "Type": f["landuse"].title(),
            "Crop": f.get("crop", ""),
            "Lat": round(f["lat"], 5),
            "Lon": round(f["lon"], 5),
        } for f in features]
        df = pd.DataFrame(df_data)
        st.dataframe(df, width="stretch")

        csv_buf = io.BytesIO()
        df.to_csv(csv_buf, index=False, encoding="utf-8")
        csv_buf.seek(0)
        st.download_button("Download Agri Land Use CSV", csv_buf, "agricultural_landuse.csv", "text/csv")


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_agriculture_maps_tab():
    """Main entry point for the Agriculture & Food Maps tab."""

    st.markdown("""
    <div class="tab-header emerald">
        <h4>Agriculture &amp; Food Maps</h4>
        <p>Global crop regions, wine zones, fishing areas, livestock, and food production</p>
    </div>
    """, unsafe_allow_html=True)

    map_type = st.selectbox("Select Map Type", MAP_TYPES, key="ag_map_type")

    st.markdown("---")

    if map_type == "Global Crop Regions":
        _render_crop_regions()
    elif map_type == "Wine Regions":
        _render_wine_regions()
    elif map_type == "Fishing Zones":
        _render_fishing_zones()
    elif map_type == "Livestock Distribution":
        _render_livestock()
    elif map_type == "Coffee & Tea Origins":
        _render_coffee_tea()
    elif map_type == "Organic Farming":
        _render_organic_farming()
    elif map_type == "Irrigation Systems":
        _render_irrigation()
    elif map_type == "Food Production Index":
        _render_food_production()
    elif map_type == "Spice Routes":
        _render_spice_routes()
    elif map_type == "Agricultural Land Use":
        _render_agri_landuse()
