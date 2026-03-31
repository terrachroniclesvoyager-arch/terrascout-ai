# -*- coding: utf-8 -*-
"""
Gastronomy & Food Culture Maps module for TerraScout AI.
10 map modes covering world cuisines, restaurants, beverages, spices,
and UNESCO food heritage. All hardcoded data, no API keys needed.
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

# =====================================================================
# MAP TYPE DEFINITIONS
# =====================================================================
MAP_TYPES = [
    "Michelin Star Restaurants",
    "World Cuisine Origins",
    "Coffee Culture Map",
    "Beer & Brewery Capitals",
    "Wine Regions of the World",
    "Street Food Capitals",
    "UNESCO Food Heritage",
    "Chocolate & Cacao Origins",
    "Tea Cultures & Origins",
    "Spice Trade Routes",
]

# =====================================================================
# COLORS
# =====================================================================
MICHELIN_COLORS = {"3-star": "#fbbf24", "2-star": "#f59e0b", "1-star": "#d97706"}
CUISINE_COLORS = {
    "Asian": "#ef4444", "European": "#3b82f6", "Latin American": "#10b981",
    "Middle Eastern": "#f59e0b", "African": "#8b5cf6", "North American": "#ec4899",
    "Oceanian": "#06b6d4",
}
COFFEE_COLORS = {"Producer": "#92400e", "Cafe City": "#06b6d4"}
BEER_COLORS = {"Lager": "#f59e0b", "Ale": "#ef4444", "Wheat": "#fbbf24", "Stout": "#1e293b", "Mixed": "#8b5cf6"}
WINE_COLORS_MAP = {
    "Red": "#dc2626", "White": "#fbbf24", "Both": "#8b5cf6",
    "Sparkling": "#06b6d4", "Rosé": "#f472b6",
}
STREET_FOOD_COLORS = {
    "Asia": "#ef4444", "Latin America": "#10b981", "Middle East": "#f59e0b",
    "Africa": "#8b5cf6", "Europe": "#3b82f6", "North America": "#ec4899",
}
UNESCO_COLORS = {"Diet": "#10b981", "Cuisine": "#3b82f6", "Practice": "#f59e0b", "Beverage": "#8b5cf6"}
CHOCOLATE_COLORS = {"Producer": "#92400e", "Chocolate Capital": "#d97706"}
TEA_COLORS = {"Green": "#10b981", "Black": "#1e293b", "Oolong": "#f59e0b", "White": "#e2e8f0", "Mixed": "#8b5cf6"}
SPICE_COLORS = {
    "Hot Spice": "#ef4444", "Aromatic": "#f59e0b", "Sweet": "#ec4899",
    "Savory": "#10b981", "Herb": "#84cc16", "Mixed": "#8b5cf6",
}

# =====================================================================
# 1. MICHELIN STAR RESTAURANTS - Cities with most stars (~40)
# =====================================================================
MICHELIN_CITIES = [
    {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "three_star": 12, "two_star": 39, "one_star": 148, "total_stars": 263, "notes": "Most Michelin stars of any city worldwide"},
    {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "three_star": 9, "two_star": 15, "one_star": 97, "total_stars": 154, "notes": "Birthplace of the Michelin Guide (1900)"},
    {"city": "Kyoto", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "three_star": 7, "two_star": 18, "one_star": 76, "total_stars": 133, "notes": "Kaiseki and traditional Japanese cuisine"},
    {"city": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023, "three_star": 4, "two_star": 15, "one_star": 79, "total_stars": 121, "notes": "Japan's kitchen, street food culture"},
    {"city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "three_star": 5, "two_star": 11, "one_star": 57, "total_stars": 94, "notes": "Diverse culinary scene, fine dining hub"},
    {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "three_star": 3, "two_star": 9, "one_star": 55, "total_stars": 82, "notes": "Global fusion and classic British dining"},
    {"city": "Hong Kong", "country": "China", "lat": 22.3193, "lon": 114.1694, "three_star": 7, "two_star": 12, "one_star": 46, "total_stars": 91, "notes": "Cantonese cuisine, dim sum capital"},
    {"city": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "three_star": 3, "two_star": 7, "one_star": 38, "total_stars": 62, "notes": "Hawker stalls to fine dining"},
    {"city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737, "three_star": 3, "two_star": 8, "one_star": 32, "total_stars": 57, "notes": "Shanghainese and international cuisine"},
    {"city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "three_star": 4, "two_star": 6, "one_star": 22, "total_stars": 46, "notes": "Thai street food meets fine dining"},
    {"city": "Chicago", "country": "USA", "lat": 41.8781, "lon": -87.6298, "three_star": 2, "two_star": 4, "one_star": 17, "total_stars": 31, "notes": "Innovative American cuisine"},
    {"city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194, "three_star": 3, "two_star": 5, "one_star": 20, "total_stars": 39, "notes": "Farm-to-table, California cuisine"},
    {"city": "Macau", "country": "China", "lat": 22.1987, "lon": 113.5439, "three_star": 3, "two_star": 5, "one_star": 11, "total_stars": 30, "notes": "Portuguese-Chinese fusion"},
    {"city": "Lyon", "country": "France", "lat": 45.7640, "lon": 4.8357, "three_star": 4, "two_star": 5, "one_star": 12, "total_stars": 34, "notes": "Gastronomic capital of France, bouchons"},
    {"city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "three_star": 2, "two_star": 7, "one_star": 22, "total_stars": 42, "notes": "Korean royal cuisine and BBQ"},
    {"city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654, "three_star": 3, "two_star": 5, "one_star": 18, "total_stars": 35, "notes": "Night markets to haute cuisine"},
    {"city": "Milan", "country": "Italy", "lat": 45.4642, "lon": 9.1900, "three_star": 3, "two_star": 4, "one_star": 15, "total_stars": 32, "notes": "Northern Italian fine dining"},
    {"city": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686, "three_star": 2, "two_star": 4, "one_star": 15, "total_stars": 29, "notes": "Catalan cuisine and molecular gastronomy"},
    {"city": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964, "three_star": 1, "two_star": 3, "one_star": 18, "total_stars": 27, "notes": "Classic Roman and Italian cuisine"},
    {"city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820, "three_star": 2, "two_star": 4, "one_star": 10, "total_stars": 24, "notes": "Bavarian and modern German cuisine"},
    {"city": "Brussels", "country": "Belgium", "lat": 50.8503, "lon": 4.3517, "three_star": 2, "two_star": 3, "one_star": 12, "total_stars": 24, "notes": "Belgian gastronomy, chocolate, and beer"},
    {"city": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683, "three_star": 2, "two_star": 3, "one_star": 12, "total_stars": 24, "notes": "New Nordic cuisine, Noma influence"},
    {"city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "three_star": 2, "two_star": 4, "one_star": 14, "total_stars": 28, "notes": "Diverse ethnic dining scene"},
    {"city": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038, "three_star": 2, "two_star": 3, "one_star": 13, "total_stars": 25, "notes": "Traditional and avant-garde Spanish"},
    {"city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417, "three_star": 1, "two_star": 3, "one_star": 9, "total_stars": 18, "notes": "Swiss fine dining"},
    {"city": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "three_star": 1, "two_star": 2, "one_star": 10, "total_stars": 17, "notes": "Tuscan cuisine and Renaissance dining"},
    {"city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686, "three_star": 1, "two_star": 2, "one_star": 8, "total_stars": 15, "notes": "Nordic innovation, seafood focus"},
    {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "three_star": 1, "two_star": 3, "one_star": 14, "total_stars": 23, "notes": "Modern European and multicultural"},
    {"city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "three_star": 1, "two_star": 2, "one_star": 9, "total_stars": 16, "notes": "Viennese café culture and pastry"},
    {"city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "three_star": 1, "two_star": 2, "one_star": 10, "total_stars": 17, "notes": "International and Dutch cuisine"},
    {"city": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "three_star": 2, "two_star": 3, "one_star": 9, "total_stars": 21, "notes": "Global luxury dining destination"},
    {"city": "Lisbon", "country": "Portugal", "lat": 38.7223, "lon": -9.1393, "three_star": 1, "two_star": 2, "one_star": 7, "total_stars": 14, "notes": "Portuguese seafood and pastéis"},
    {"city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "three_star": 1, "two_star": 2, "one_star": 8, "total_stars": 15, "notes": "Innovative Australian dining"},
    {"city": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "three_star": 1, "two_star": 2, "one_star": 7, "total_stars": 14, "notes": "Brazilian and international cuisine"},
    {"city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832, "three_star": 1, "two_star": 2, "one_star": 8, "total_stars": 15, "notes": "Multicultural culinary scene"},
    {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "three_star": 2, "two_star": 3, "one_star": 8, "total_stars": 20, "notes": "Mexican haute cuisine, Pujol influence"},
    {"city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074, "three_star": 3, "two_star": 5, "one_star": 17, "total_stars": 36, "notes": "Imperial and modern Chinese cuisine"},
    {"city": "Nagoya", "country": "Japan", "lat": 35.1815, "lon": 136.9066, "three_star": 3, "two_star": 7, "one_star": 32, "total_stars": 55, "notes": "Nagoya meshi regional specialties"},
    {"city": "Bordeaux", "country": "France", "lat": 44.8378, "lon": -0.5792, "three_star": 1, "two_star": 3, "one_star": 8, "total_stars": 17, "notes": "Wine-paired gastronomy"},
    {"city": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "three_star": 1, "two_star": 2, "one_star": 6, "total_stars": 13, "notes": "Ottoman culinary tradition"},
]

# =====================================================================
# 2. WORLD CUISINE ORIGINS (~35)
# =====================================================================
CUISINE_ORIGINS = [
    {"cuisine": "Italian", "region": "Italian Peninsula", "lat": 42.5, "lon": 12.5, "family": "European", "signature_dish": "Pasta, Pizza, Risotto", "year_origin": "~1000 BCE", "notes": "Roman, Etruscan roots; regional diversity across 20 regions"},
    {"cuisine": "Chinese (Cantonese)", "region": "Guangdong, China", "lat": 23.13, "lon": 113.26, "family": "Asian", "signature_dish": "Dim Sum, Roast Duck", "year_origin": "~2000 BCE", "notes": "Light, fresh flavors; steaming and stir-frying"},
    {"cuisine": "Chinese (Sichuan)", "region": "Sichuan, China", "lat": 30.57, "lon": 104.07, "family": "Asian", "signature_dish": "Mapo Tofu, Kung Pao Chicken", "year_origin": "~1500 BCE", "notes": "Mala numbing-spicy profile, Sichuan peppercorn"},
    {"cuisine": "French", "region": "France", "lat": 46.60, "lon": 2.21, "family": "European", "signature_dish": "Coq au Vin, Croissant, Soufflé", "year_origin": "~1600s", "notes": "Codified by Escoffier; mother sauces, haute cuisine"},
    {"cuisine": "Japanese", "region": "Japan", "lat": 36.20, "lon": 138.25, "family": "Asian", "signature_dish": "Sushi, Ramen, Tempura", "year_origin": "~300 BCE", "notes": "Washoku tradition, seasonal ingredients, umami"},
    {"cuisine": "Mexican", "region": "Mesoamerica", "lat": 19.43, "lon": -99.13, "family": "Latin American", "signature_dish": "Tacos, Mole, Tamales", "year_origin": "~7000 BCE", "notes": "Aztec/Mayan roots; corn, chili, cacao trinity"},
    {"cuisine": "Indian (North)", "region": "Northern India", "lat": 28.61, "lon": 77.21, "family": "Asian", "signature_dish": "Butter Chicken, Naan, Biryani", "year_origin": "~3000 BCE", "notes": "Mughal influence, tandoor cooking, rich gravies"},
    {"cuisine": "Indian (South)", "region": "Southern India", "lat": 13.08, "lon": 80.27, "family": "Asian", "signature_dish": "Dosa, Sambar, Idli", "year_origin": "~3000 BCE", "notes": "Rice-based, coconut, curry leaves, fermented batters"},
    {"cuisine": "Thai", "region": "Thailand", "lat": 13.76, "lon": 100.50, "family": "Asian", "signature_dish": "Pad Thai, Green Curry, Tom Yum", "year_origin": "~1200s", "notes": "Balance of sweet, sour, salty, spicy, bitter"},
    {"cuisine": "Spanish", "region": "Iberian Peninsula", "lat": 40.42, "lon": -3.70, "family": "European", "signature_dish": "Paella, Tapas, Jamón", "year_origin": "~200 BCE", "notes": "Moorish influence, olive oil, saffron, seafood"},
    {"cuisine": "Greek", "region": "Greece", "lat": 37.98, "lon": 23.73, "family": "European", "signature_dish": "Moussaka, Souvlaki, Tzatziki", "year_origin": "~800 BCE", "notes": "Ancient Mediterranean diet, olive oil, feta"},
    {"cuisine": "Turkish", "region": "Anatolia", "lat": 39.93, "lon": 32.86, "family": "Middle Eastern", "signature_dish": "Kebab, Baklava, Pide", "year_origin": "~1000s", "notes": "Ottoman empire fusion, Central Asian and Arab influences"},
    {"cuisine": "Korean", "region": "Korean Peninsula", "lat": 37.57, "lon": 126.98, "family": "Asian", "signature_dish": "Kimchi, Bibimbap, Korean BBQ", "year_origin": "~1000 BCE", "notes": "Fermentation mastery, banchan side dishes"},
    {"cuisine": "Vietnamese", "region": "Vietnam", "lat": 21.03, "lon": 105.85, "family": "Asian", "signature_dish": "Pho, Banh Mi, Spring Rolls", "year_origin": "~500 BCE", "notes": "French-colonial influence, fresh herbs, light broths"},
    {"cuisine": "Moroccan", "region": "Morocco", "lat": 33.97, "lon": -6.85, "family": "African", "signature_dish": "Tagine, Couscous, Pastilla", "year_origin": "~700s", "notes": "Berber, Arab, Andalusian blend; preserved lemons, ras el hanout"},
    {"cuisine": "Ethiopian", "region": "Ethiopia", "lat": 9.02, "lon": 38.75, "family": "African", "signature_dish": "Injera, Doro Wat, Kitfo", "year_origin": "~1000 BCE", "notes": "Communal eating, teff-based injera, berbere spice"},
    {"cuisine": "Peruvian", "region": "Peru", "lat": -12.05, "lon": -77.04, "family": "Latin American", "signature_dish": "Ceviche, Lomo Saltado, Ají de Gallina", "year_origin": "~3000 BCE", "notes": "Inca roots, Nikkei and Chifa fusion, potato biodiversity"},
    {"cuisine": "Lebanese", "region": "Lebanon", "lat": 33.89, "lon": 35.50, "family": "Middle Eastern", "signature_dish": "Hummus, Tabbouleh, Shawarma", "year_origin": "~2000 BCE", "notes": "Phoenician trading heritage, mezze culture"},
    {"cuisine": "Indonesian", "region": "Indonesian Archipelago", "lat": -6.21, "lon": 106.85, "family": "Asian", "signature_dish": "Nasi Goreng, Rendang, Satay", "year_origin": "~500s", "notes": "Spice Islands influence, coconut milk, sambal"},
    {"cuisine": "Brazilian", "region": "Brazil", "lat": -15.79, "lon": -47.88, "family": "Latin American", "signature_dish": "Feijoada, Churrasco, Pão de Queijo", "year_origin": "~1500s", "notes": "Portuguese, African, Indigenous fusion"},
    {"cuisine": "German", "region": "Central Europe", "lat": 52.52, "lon": 13.41, "family": "European", "signature_dish": "Bratwurst, Schnitzel, Pretzel", "year_origin": "~500s", "notes": "Hearty, meat-centric, beer culture, regional variety"},
    {"cuisine": "Argentine", "region": "Argentina", "lat": -34.60, "lon": -58.38, "family": "Latin American", "signature_dish": "Asado, Empanadas, Dulce de Leche", "year_origin": "~1800s", "notes": "Gaucho grilling tradition, Italian immigrant influence"},
    {"cuisine": "Malaysian", "region": "Malaysia", "lat": 3.14, "lon": 101.69, "family": "Asian", "signature_dish": "Nasi Lemak, Laksa, Char Kway Teow", "year_origin": "~1400s", "notes": "Malay, Chinese, Indian crossroads"},
    {"cuisine": "Georgian", "region": "Georgia", "lat": 41.72, "lon": 44.79, "family": "European", "signature_dish": "Khachapuri, Khinkali, Churchkhela", "year_origin": "~500 BCE", "notes": "Ancient winemaking, walnut sauces, supra feasts"},
    {"cuisine": "Jamaican", "region": "Jamaica", "lat": 18.11, "lon": -77.30, "family": "Latin American", "signature_dish": "Jerk Chicken, Ackee and Saltfish", "year_origin": "~1600s", "notes": "African, Taino, British, Indian blend; scotch bonnet peppers"},
    {"cuisine": "Egyptian", "region": "Egypt", "lat": 30.04, "lon": 31.24, "family": "Middle Eastern", "signature_dish": "Koshari, Ful Medames, Molokhia", "year_origin": "~3000 BCE", "notes": "Ancient bread culture, Nile River ingredients"},
    {"cuisine": "Filipino", "region": "Philippines", "lat": 14.60, "lon": 120.98, "family": "Asian", "signature_dish": "Adobo, Lechon, Sinigang", "year_origin": "~1000s", "notes": "Malay, Chinese, Spanish layers; vinegar-based cooking"},
    {"cuisine": "Swedish", "region": "Scandinavia", "lat": 59.33, "lon": 18.07, "family": "European", "signature_dish": "Meatballs, Smörgåsbord, Gravlax", "year_origin": "~800s", "notes": "Viking preservation techniques, New Nordic movement"},
    {"cuisine": "Nigerian", "region": "Nigeria", "lat": 9.06, "lon": 7.49, "family": "African", "signature_dish": "Jollof Rice, Suya, Egusi Soup", "year_origin": "~1000s", "notes": "West African powerhouse, palm oil, yam, plantain"},
    {"cuisine": "Sri Lankan", "region": "Sri Lanka", "lat": 6.93, "lon": 79.84, "family": "Asian", "signature_dish": "Rice and Curry, Hoppers, Kottu", "year_origin": "~500 BCE", "notes": "Spice island, cinnamon origin, coconut-rich curries"},
    {"cuisine": "Polynesian", "region": "Pacific Islands", "lat": -17.73, "lon": -149.57, "family": "Oceanian", "signature_dish": "Poi, Kalua Pig, Poke", "year_origin": "~1000s", "notes": "Earth-oven cooking, taro, breadfruit, coconut"},
    {"cuisine": "Iranian (Persian)", "region": "Iran", "lat": 35.69, "lon": 51.39, "family": "Middle Eastern", "signature_dish": "Chelo Kebab, Ghormeh Sabzi, Tahdig", "year_origin": "~500 BCE", "notes": "Saffron, dried limes, pomegranate; ancient empire cuisine"},
    {"cuisine": "Senegalese", "region": "Senegal", "lat": 14.69, "lon": -17.44, "family": "African", "signature_dish": "Thieboudienne, Yassa, Mafé", "year_origin": "~1200s", "notes": "National dish thieboudienne (fish and rice), peanut sauces"},
    {"cuisine": "Uzbek", "region": "Uzbekistan", "lat": 41.30, "lon": 69.28, "family": "Asian", "signature_dish": "Plov, Samsa, Lagman", "year_origin": "~800s", "notes": "Silk Road crossroads, communal rice dishes, tandoor breads"},
    {"cuisine": "Basque", "region": "Basque Country", "lat": 43.26, "lon": -2.93, "family": "European", "signature_dish": "Pintxos, Bacalao, Burnt Cheesecake", "year_origin": "~1000s", "notes": "Highest per-capita Michelin stars, txoko dining societies"},
]

# =====================================================================
# 3. COFFEE CULTURE MAP (~40)
# =====================================================================
COFFEE_DATA = [
    {"name": "Ethiopia (Kaffa)", "lat": 7.25, "lon": 36.50, "type": "Producer", "variety": "Arabica Origin", "annual_tons": 496000, "notes": "Birthplace of coffee, wild Arabica forests"},
    {"name": "Colombia (Eje Cafetero)", "lat": 4.81, "lon": -75.70, "type": "Producer", "variety": "Arabica", "annual_tons": 810000, "notes": "Coffee Triangle, UNESCO cultural landscape"},
    {"name": "Brazil (Minas Gerais)", "lat": -19.92, "lon": -43.94, "type": "Producer", "variety": "Arabica/Robusta", "annual_tons": 3500000, "notes": "World's largest producer since 1840s"},
    {"name": "Vietnam (Central Highlands)", "lat": 12.66, "lon": 108.04, "type": "Producer", "variety": "Robusta", "annual_tons": 1740000, "notes": "Second largest producer, ca phe sua da culture"},
    {"name": "Indonesia (Sumatra)", "lat": 0.59, "lon": 101.43, "type": "Producer", "variety": "Arabica/Robusta", "annual_tons": 670000, "notes": "Mandheling, Lintong, wet-hulled processing"},
    {"name": "Kenya (Central Highlands)", "lat": -0.42, "lon": 36.95, "type": "Producer", "variety": "Arabica (SL28/SL34)", "annual_tons": 45000, "notes": "Bright acidity, berry notes, auction system"},
    {"name": "Guatemala (Antigua)", "lat": 14.56, "lon": -90.73, "type": "Producer", "variety": "Arabica", "annual_tons": 240000, "notes": "Volcanic soil, shade-grown, chocolate notes"},
    {"name": "Costa Rica", "lat": 9.93, "lon": -84.08, "type": "Producer", "variety": "Arabica", "annual_tons": 82000, "notes": "Honey process innovation, banned Robusta"},
    {"name": "Jamaica (Blue Mountains)", "lat": 18.18, "lon": -76.35, "type": "Producer", "variety": "Arabica", "annual_tons": 1200, "notes": "Premium Blue Mountain, smooth mild flavor"},
    {"name": "Yemen (Mocha)", "lat": 13.32, "lon": 43.31, "type": "Producer", "variety": "Arabica", "annual_tons": 18000, "notes": "Ancient port of Mocha, original coffee trade"},
    {"name": "Hawaii (Kona)", "lat": 19.64, "lon": -155.99, "type": "Producer", "variety": "Arabica", "annual_tons": 2700, "notes": "Volcanic slopes, only US coffee region"},
    {"name": "Peru (Chanchamayo)", "lat": -11.05, "lon": -75.32, "type": "Producer", "variety": "Arabica", "annual_tons": 370000, "notes": "Organic shade-grown, cloud forest coffee"},
    {"name": "Honduras", "lat": 14.07, "lon": -87.19, "type": "Producer", "variety": "Arabica", "annual_tons": 475000, "notes": "Central America's largest producer"},
    {"name": "Rwanda", "lat": -1.94, "lon": 29.87, "type": "Producer", "variety": "Arabica (Bourbon)", "annual_tons": 19000, "notes": "Thousand hills, specialty coffee renaissance"},
    {"name": "Panama (Boquete)", "lat": 8.78, "lon": -82.43, "type": "Producer", "variety": "Geisha/Arabica", "annual_tons": 6500, "notes": "Geisha variety auction records, volcanic terroir"},
    {"name": "Tanzania (Kilimanjaro)", "lat": -3.37, "lon": 36.68, "type": "Producer", "variety": "Arabica", "annual_tons": 55000, "notes": "Peaberry specialty, volcanic highland growing"},
    {"name": "India (Karnataka)", "lat": 12.30, "lon": 76.66, "type": "Producer", "variety": "Arabica/Robusta", "annual_tons": 350000, "notes": "Monsoon Malabar specialty, shade-grown"},
    {"name": "Vienna", "lat": 48.21, "lon": 16.37, "type": "Cafe City", "variety": "Viennese Melange", "annual_tons": 0, "notes": "UNESCO-listed café culture since 1683"},
    {"name": "Melbourne", "lat": -37.81, "lon": 144.96, "type": "Cafe City", "variety": "Flat White", "annual_tons": 0, "notes": "Third-wave coffee capital, laneway cafes"},
    {"name": "Seattle", "lat": 47.61, "lon": -122.33, "type": "Cafe City", "variety": "Espresso culture", "annual_tons": 0, "notes": "Birthplace of Starbucks, indie roasters"},
    {"name": "Istanbul", "lat": 41.01, "lon": 28.98, "type": "Cafe City", "variety": "Turkish Coffee", "annual_tons": 0, "notes": "UNESCO-listed Turkish coffee tradition"},
    {"name": "Rome", "lat": 41.90, "lon": 12.50, "type": "Cafe City", "variety": "Espresso", "annual_tons": 0, "notes": "Espresso culture, stand-up bar tradition"},
    {"name": "Addis Ababa", "lat": 9.02, "lon": 38.75, "type": "Cafe City", "variety": "Buna ceremony", "annual_tons": 0, "notes": "Ethiopian coffee ceremony, jebena brewing"},
    {"name": "Portland", "lat": 45.52, "lon": -122.68, "type": "Cafe City", "variety": "Third Wave", "annual_tons": 0, "notes": "Stumptown, micro-roaster pioneer city"},
    {"name": "Bogotá", "lat": 4.71, "lon": -74.07, "type": "Cafe City", "variety": "Tinto culture", "annual_tons": 0, "notes": "Colombian coffee culture, specialty cafes"},
    {"name": "Hanoi", "lat": 21.03, "lon": 105.85, "type": "Cafe City", "variety": "Egg Coffee", "annual_tons": 0, "notes": "Ca phe trung (egg coffee), ca phe sua da"},
    {"name": "Tokyo (Kissaten)", "lat": 35.68, "lon": 139.65, "type": "Cafe City", "variety": "Pour-over/Siphon", "annual_tons": 0, "notes": "Kissaten tradition, precision brewing"},
    {"name": "Stockholm", "lat": 59.33, "lon": 18.07, "type": "Cafe City", "variety": "Fika culture", "annual_tons": 0, "notes": "Fika coffee break tradition, highest per capita consumption"},
    {"name": "Helsinki", "lat": 60.17, "lon": 24.94, "type": "Cafe City", "variety": "Light roast", "annual_tons": 0, "notes": "World's highest per-capita coffee consumption"},
    {"name": "São Paulo", "lat": -23.55, "lon": -46.63, "type": "Cafe City", "variety": "Cafezinho", "annual_tons": 0, "notes": "Cafezinho tradition, specialty scene growing"},
    {"name": "New Orleans", "lat": 29.95, "lon": -90.07, "type": "Cafe City", "variety": "Chicory Coffee", "annual_tons": 0, "notes": "Café du Monde, chicory-blended café au lait"},
    {"name": "Havana", "lat": 23.11, "lon": -82.37, "type": "Cafe City", "variety": "Cafecito", "annual_tons": 0, "notes": "Cuban espresso, strong and sweet"},
    {"name": "Marrakech", "lat": 31.63, "lon": -8.00, "type": "Cafe City", "variety": "Nous-Nous", "annual_tons": 0, "notes": "Half coffee half milk, spiced coffee"},
    {"name": "Amsterdam", "lat": 52.37, "lon": 4.90, "type": "Cafe City", "variety": "Koffie verkeerd", "annual_tons": 0, "notes": "Historic coffee trade center, VOC heritage"},
    {"name": "Trieste", "lat": 45.65, "lon": 13.78, "type": "Cafe City", "variety": "Capo in B", "annual_tons": 0, "notes": "Italy's coffee capital, Illy headquarters"},
    {"name": "Taipei", "lat": 25.03, "lon": 121.57, "type": "Cafe City", "variety": "Pour-over/Specialty", "annual_tons": 0, "notes": "Thriving specialty scene, world barista champions"},
    {"name": "Lviv", "lat": 49.84, "lon": 24.03, "type": "Cafe City", "variety": "Viennese-style", "annual_tons": 0, "notes": "Jerzy Kulczycki legend, Austro-Hungarian café heritage"},
    {"name": "Mexico City", "lat": 19.43, "lon": -99.13, "type": "Cafe City", "variety": "Café de Olla", "annual_tons": 0, "notes": "Clay pot coffee with cinnamon and piloncillo"},
    {"name": "Naples", "lat": 40.85, "lon": 14.27, "type": "Cafe City", "variety": "Caffè Napoletano", "annual_tons": 0, "notes": "Suspended coffee tradition (caffè sospeso)"},
]

# =====================================================================
# 4. BEER & BREWERY CAPITALS (~40)
# =====================================================================
BEER_DATA = [
    {"city": "Munich", "country": "Germany", "lat": 48.14, "lon": 11.58, "style": "Lager", "breweries": 45, "famous_beer": "Augustiner, Hofbräu", "annual_liters_pc": 115, "notes": "Oktoberfest, Reinheitsgebot purity law (1516)"},
    {"city": "Brussels", "country": "Belgium", "lat": 50.85, "lon": 4.35, "style": "Ale", "breweries": 35, "famous_beer": "Cantillon, Delirium", "annual_liters_pc": 68, "notes": "UNESCO-listed Belgian beer culture, lambic tradition"},
    {"city": "Portland", "country": "USA", "lat": 45.52, "lon": -122.68, "style": "Ale", "breweries": 75, "famous_beer": "Deschutes, Widmer", "annual_liters_pc": 95, "notes": "Most breweries per capita in USA, craft beer pioneer"},
    {"city": "Dublin", "country": "Ireland", "lat": 53.35, "lon": -6.26, "style": "Stout", "breweries": 25, "famous_beer": "Guinness, Smithwick's", "annual_liters_pc": 98, "notes": "Guinness Storehouse, stout and red ale tradition"},
    {"city": "Prague", "country": "Czech Republic", "lat": 50.08, "lon": 14.44, "style": "Lager", "breweries": 55, "famous_beer": "Pilsner Urquell, Staropramen", "annual_liters_pc": 142, "notes": "Highest per-capita beer consumption in the world"},
    {"city": "London", "country": "UK", "lat": 51.51, "lon": -0.13, "style": "Ale", "breweries": 115, "famous_beer": "Fuller's, Meantime", "annual_liters_pc": 67, "notes": "Historic porter and IPA birthplace, craft boom"},
    {"city": "Denver", "country": "USA", "lat": 39.74, "lon": -104.99, "style": "Ale", "breweries": 70, "famous_beer": "Great Divide, Breckenridge", "annual_liters_pc": 90, "notes": "Great American Beer Festival host city"},
    {"city": "Amsterdam", "country": "Netherlands", "lat": 52.37, "lon": 4.90, "style": "Lager", "breweries": 40, "famous_beer": "Heineken, Brouwerij 't IJ", "annual_liters_pc": 74, "notes": "Heineken Experience, growing craft scene"},
    {"city": "Bamberg", "country": "Germany", "lat": 49.89, "lon": 10.89, "style": "Lager", "breweries": 11, "famous_beer": "Schlenkerla Rauchbier", "annual_liters_pc": 135, "notes": "Smoked beer (Rauchbier) capital, 11 breweries in town"},
    {"city": "Bruges", "country": "Belgium", "lat": 51.21, "lon": 3.22, "style": "Ale", "breweries": 8, "famous_beer": "De Halve Maan, Straffe Hendrik", "annual_liters_pc": 68, "notes": "Beer pipeline under city, medieval brewing heritage"},
    {"city": "San Diego", "country": "USA", "lat": 32.72, "lon": -117.16, "style": "Ale", "breweries": 155, "famous_beer": "Stone, Ballast Point", "annual_liters_pc": 85, "notes": "Capital of craft IPA, over 150 breweries"},
    {"city": "Melbourne", "country": "Australia", "lat": -37.81, "lon": 144.96, "style": "Mixed", "breweries": 55, "famous_beer": "Mountain Goat, Moon Dog", "annual_liters_pc": 77, "notes": "Australia's craft beer capital, laneway bars"},
    {"city": "Tokyo", "country": "Japan", "lat": 35.68, "lon": 139.65, "style": "Lager", "breweries": 45, "famous_beer": "Asahi, Kirin, Hitachino Nest", "annual_liters_pc": 42, "notes": "Precision brewing, craft ji-biru movement"},
    {"city": "Pilsen", "country": "Czech Republic", "lat": 49.75, "lon": 13.38, "style": "Lager", "breweries": 5, "famous_beer": "Pilsner Urquell", "annual_liters_pc": 142, "notes": "Birthplace of pilsner style (1842)"},
    {"city": "Asheville", "country": "USA", "lat": 35.60, "lon": -82.55, "style": "Ale", "breweries": 45, "famous_beer": "Wicked Weed, Highland", "annual_liters_pc": 100, "notes": "Beer City USA, Appalachian brewing scene"},
    {"city": "Cologne", "country": "Germany", "lat": 50.94, "lon": 6.96, "style": "Ale", "breweries": 20, "famous_beer": "Gaffel Kölsch, Früh", "annual_liters_pc": 120, "notes": "Kölsch style unique to Cologne, served in Stangen glass"},
    {"city": "Düsseldorf", "country": "Germany", "lat": 51.23, "lon": 6.78, "style": "Ale", "breweries": 15, "famous_beer": "Uerige, Schumacher Alt", "annual_liters_pc": 115, "notes": "Altbier capital, copper-colored top-fermented ale"},
    {"city": "Ghent", "country": "Belgium", "lat": 51.05, "lon": 3.72, "style": "Ale", "breweries": 10, "famous_beer": "Gruut, Gentse Strop", "annual_liters_pc": 68, "notes": "Medieval brewing history, Gruut Museum"},
    {"city": "Copenhagen", "country": "Denmark", "lat": 55.68, "lon": 12.57, "style": "Mixed", "breweries": 30, "famous_beer": "Carlsberg, Mikkeller", "annual_liters_pc": 63, "notes": "Carlsberg heritage, Mikkeller craft revolution"},
    {"city": "Guadalajara", "country": "Mexico", "lat": 20.67, "lon": -103.35, "style": "Lager", "breweries": 20, "famous_beer": "Minerva, Modelo", "annual_liters_pc": 64, "notes": "Mexican craft beer hub, cerveza artesanal"},
    {"city": "Cape Town", "country": "South Africa", "lat": -33.93, "lon": 18.42, "style": "Mixed", "breweries": 25, "famous_beer": "Devil's Peak, Jack Black", "annual_liters_pc": 55, "notes": "Africa's craft beer leader, Cape Brewing scene"},
    {"city": "Wellington", "country": "New Zealand", "lat": -41.29, "lon": 174.78, "style": "Ale", "breweries": 20, "famous_beer": "Garage Project, Panhead", "annual_liters_pc": 65, "notes": "Craft beer capital of New Zealand"},
    {"city": "Vienna", "country": "Austria", "lat": 48.21, "lon": 16.37, "style": "Lager", "breweries": 18, "famous_beer": "Ottakringer, Schwechater", "annual_liters_pc": 105, "notes": "Vienna lager style birthplace, Beisl culture"},
    {"city": "Qingdao", "country": "China", "lat": 36.07, "lon": 120.38, "style": "Lager", "breweries": 12, "famous_beer": "Tsingtao", "annual_liters_pc": 45, "notes": "German colonial brewing legacy, annual beer festival"},
    {"city": "Lima", "country": "Peru", "lat": -12.05, "lon": -77.04, "style": "Lager", "breweries": 15, "famous_beer": "Cusqueña, Barbarian", "annual_liters_pc": 46, "notes": "Growing craft scene, chicha tradition"},
    {"city": "Budapest", "country": "Hungary", "lat": 47.50, "lon": 19.04, "style": "Lager", "breweries": 20, "famous_beer": "Dreher, First Craft Beer", "annual_liters_pc": 72, "notes": "Ruin bar culture, reviving craft brewing"},
    {"city": "Krakow", "country": "Poland", "lat": 50.06, "lon": 19.94, "style": "Lager", "breweries": 15, "famous_beer": "Zywiec, Pinta", "annual_liters_pc": 98, "notes": "Medieval beer cellars, growing craft scene"},
    {"city": "Austin", "country": "USA", "lat": 30.27, "lon": -97.74, "style": "Ale", "breweries": 50, "famous_beer": "Jester King, Live Oak", "annual_liters_pc": 88, "notes": "Texas craft capital, farmhouse ales"},
    {"city": "Taipei", "country": "Taiwan", "lat": 25.03, "lon": 121.57, "style": "Mixed", "breweries": 20, "famous_beer": "Taiwan Beer, Taihu", "annual_liters_pc": 25, "notes": "Emerging Asian craft scene, tropical IPAs"},
    {"city": "Edinburgh", "country": "UK", "lat": 55.95, "lon": -3.19, "style": "Ale", "breweries": 20, "famous_beer": "BrewDog, Stewart", "annual_liters_pc": 70, "notes": "Scottish ale tradition, whisky barrel-aged beers"},
    {"city": "Saigon (HCMC)", "country": "Vietnam", "lat": 10.82, "lon": 106.63, "style": "Lager", "breweries": 15, "famous_beer": "Saigon Beer, Pasteur St.", "annual_liters_pc": 43, "notes": "Bia hoi fresh draught culture, Southeast Asian brew scene"},
    {"city": "St. Louis", "country": "USA", "lat": 38.63, "lon": -90.20, "style": "Lager", "breweries": 30, "famous_beer": "Budweiser, 4 Hands", "annual_liters_pc": 85, "notes": "Anheuser-Busch headquarters, German immigrant heritage"},
    {"city": "Antwerp", "country": "Belgium", "lat": 51.22, "lon": 4.40, "style": "Ale", "breweries": 10, "famous_beer": "De Koninck, Seef", "annual_liters_pc": 68, "notes": "Bolleke (De Koninck) tradition, Kulminator beer bar"},
    {"city": "Reykjavik", "country": "Iceland", "lat": 64.15, "lon": -21.94, "style": "Mixed", "breweries": 12, "famous_beer": "Einstök, Borg", "annual_liters_pc": 52, "notes": "Beer legalized only in 1989, rapid craft growth"},
    {"city": "Munich (Freising)", "country": "Germany", "lat": 48.40, "lon": 11.75, "style": "Wheat", "breweries": 2, "famous_beer": "Weihenstephan", "annual_liters_pc": 135, "notes": "Weihenstephan - world's oldest brewery (1040 AD)"},
    {"city": "Yakima Valley", "country": "USA", "lat": 46.60, "lon": -120.51, "style": "Mixed", "breweries": 8, "famous_beer": "Bale Breaker", "annual_liters_pc": 80, "notes": "75% of US hop production, terroir hops"},
    {"city": "Liège", "country": "Belgium", "lat": 50.63, "lon": 5.57, "style": "Ale", "breweries": 8, "famous_beer": "Val-Dieu, Curtius", "annual_liters_pc": 68, "notes": "Walloon brewing tradition, abbey ales"},
    {"city": "Oslo", "country": "Norway", "lat": 59.91, "lon": 10.75, "style": "Mixed", "breweries": 15, "famous_beer": "Nøgne Ø, Lervig", "annual_liters_pc": 55, "notes": "Nordic craft innovation, farmhouse ales (kveik yeast)"},
    {"city": "Accra", "country": "Ghana", "lat": 5.56, "lon": -0.19, "style": "Lager", "breweries": 5, "famous_beer": "Star, Club", "annual_liters_pc": 24, "notes": "West African beer culture, palm wine transition"},
]

# =====================================================================
# 5. WINE REGIONS OF THE WORLD (~50)
# =====================================================================
WINE_REGIONS = [
    {"region": "Bordeaux", "country": "France", "lat": 44.84, "lon": -0.58, "type": "Red", "grapes": "Cabernet Sauvignon, Merlot", "area_ha": 111000, "notes": "Left/Right Bank classification, 1855 Grand Cru"},
    {"region": "Burgundy", "country": "France", "lat": 47.05, "lon": 4.38, "type": "Both", "grapes": "Pinot Noir, Chardonnay", "area_ha": 29000, "notes": "Terroir-focused, Romanée-Conti, village appellations"},
    {"region": "Champagne", "country": "France", "lat": 49.25, "lon": 3.97, "type": "Sparkling", "grapes": "Chardonnay, Pinot Noir, Pinot Meunier", "area_ha": 34000, "notes": "Méthode champenoise, UNESCO World Heritage"},
    {"region": "Rhône Valley", "country": "France", "lat": 44.12, "lon": 4.81, "type": "Red", "grapes": "Syrah, Grenache", "area_ha": 71000, "notes": "Northern (Syrah) and Southern (Grenache blends)"},
    {"region": "Loire Valley", "country": "France", "lat": 47.38, "lon": 0.69, "type": "White", "grapes": "Sauvignon Blanc, Chenin Blanc", "area_ha": 52000, "notes": "Garden of France, Sancerre, Vouvray"},
    {"region": "Alsace", "country": "France", "lat": 48.32, "lon": 7.44, "type": "White", "grapes": "Riesling, Gewürztraminer", "area_ha": 15600, "notes": "Germanic influence, aromatic whites, tall flute bottles"},
    {"region": "Tuscany", "country": "Italy", "lat": 43.35, "lon": 11.35, "type": "Red", "grapes": "Sangiovese", "area_ha": 59000, "notes": "Chianti, Brunello di Montalcino, Super Tuscans"},
    {"region": "Piedmont", "country": "Italy", "lat": 44.69, "lon": 8.03, "type": "Red", "grapes": "Nebbiolo, Barbera", "area_ha": 44000, "notes": "Barolo and Barbaresco DOCG, truffle region"},
    {"region": "Veneto", "country": "Italy", "lat": 45.44, "lon": 12.32, "type": "Both", "grapes": "Corvina, Glera", "area_ha": 84000, "notes": "Amarone, Prosecco, Soave"},
    {"region": "Sicily", "country": "Italy", "lat": 37.60, "lon": 14.02, "type": "Both", "grapes": "Nero d'Avola, Nerello Mascalese", "area_ha": 98000, "notes": "Volcanic Etna wines, ancient Greek winemaking"},
    {"region": "Rioja", "country": "Spain", "lat": 42.47, "lon": -2.45, "type": "Red", "grapes": "Tempranillo, Garnacha", "area_ha": 65000, "notes": "Crianza/Reserva/Gran Reserva aging system"},
    {"region": "Priorat", "country": "Spain", "lat": 41.20, "lon": 0.85, "type": "Red", "grapes": "Garnacha, Cariñena", "area_ha": 1900, "notes": "Llicorella slate soils, intense concentrated wines"},
    {"region": "Ribera del Duero", "country": "Spain", "lat": 41.65, "lon": -3.70, "type": "Red", "grapes": "Tempranillo (Tinto Fino)", "area_ha": 22000, "notes": "High-altitude plateau wines, Vega Sicilia"},
    {"region": "Douro Valley", "country": "Portugal", "lat": 41.16, "lon": -7.79, "type": "Both", "grapes": "Touriga Nacional, Tinta Roriz", "area_ha": 45000, "notes": "Port wine terraced vineyards, UNESCO landscape"},
    {"region": "Napa Valley", "country": "USA", "lat": 38.50, "lon": -122.27, "type": "Red", "grapes": "Cabernet Sauvignon", "area_ha": 18200, "notes": "1976 Judgment of Paris, premium Cab region"},
    {"region": "Sonoma County", "country": "USA", "lat": 38.29, "lon": -122.46, "type": "Both", "grapes": "Pinot Noir, Chardonnay", "area_ha": 24000, "notes": "Diverse microclimates, 18 AVAs"},
    {"region": "Willamette Valley", "country": "USA", "lat": 45.07, "lon": -123.07, "type": "Red", "grapes": "Pinot Noir", "area_ha": 14000, "notes": "Cool-climate Pinot Noir, volcanic Jory soils"},
    {"region": "Mendoza", "country": "Argentina", "lat": -32.89, "lon": -68.83, "type": "Red", "grapes": "Malbec, Bonarda", "area_ha": 155000, "notes": "High-altitude Andes vineyards, Malbec capital"},
    {"region": "Maipo Valley", "country": "Chile", "lat": -33.45, "lon": -70.66, "type": "Red", "grapes": "Cabernet Sauvignon, Carménère", "area_ha": 11000, "notes": "Carménère rediscovery, Andean foothills"},
    {"region": "Barossa Valley", "country": "Australia", "lat": -34.53, "lon": 138.95, "type": "Red", "grapes": "Shiraz, Grenache", "area_ha": 13000, "notes": "Old-vine Shiraz, some vines 150+ years old"},
    {"region": "Margaret River", "country": "Australia", "lat": -33.95, "lon": 115.07, "type": "Both", "grapes": "Cabernet Sauvignon, Chardonnay", "area_ha": 5500, "notes": "Maritime climate, premium boutique wineries"},
    {"region": "Hunter Valley", "country": "Australia", "lat": -32.75, "lon": 151.15, "type": "White", "grapes": "Semillon, Shiraz", "area_ha": 4000, "notes": "Age-worthy Semillon, oldest wine region in Australia"},
    {"region": "Marlborough", "country": "New Zealand", "lat": -41.51, "lon": 173.96, "type": "White", "grapes": "Sauvignon Blanc", "area_ha": 26000, "notes": "Iconic Sauvignon Blanc, Cloudy Bay revolution"},
    {"region": "Central Otago", "country": "New Zealand", "lat": -45.03, "lon": 169.13, "type": "Red", "grapes": "Pinot Noir", "area_ha": 2000, "notes": "Southernmost wine region, continental Pinot Noir"},
    {"region": "Stellenbosch", "country": "South Africa", "lat": -33.93, "lon": 18.86, "type": "Red", "grapes": "Cabernet Sauvignon, Pinotage", "area_ha": 16000, "notes": "Cape Winelands, Pinotage unique to South Africa"},
    {"region": "Constantia", "country": "South Africa", "lat": -34.03, "lon": 18.42, "type": "White", "grapes": "Sauvignon Blanc, Muscat", "area_ha": 500, "notes": "Oldest wine region in Southern Hemisphere (1685)"},
    {"region": "Mosel", "country": "Germany", "lat": 49.73, "lon": 6.63, "type": "White", "grapes": "Riesling", "area_ha": 8800, "notes": "Steep slate slopes, world's finest Riesling"},
    {"region": "Rheingau", "country": "Germany", "lat": 50.03, "lon": 8.06, "type": "White", "grapes": "Riesling, Spätburgunder", "area_ha": 3100, "notes": "Historic Riesling region, Schloss Johannisberg"},
    {"region": "Tokaj", "country": "Hungary", "lat": 48.12, "lon": 21.41, "type": "White", "grapes": "Furmint, Hárslevelű", "area_ha": 5500, "notes": "Tokaji Aszú dessert wine, first classified region (1730)"},
    {"region": "Wachau", "country": "Austria", "lat": 48.37, "lon": 15.42, "type": "White", "grapes": "Grüner Veltliner, Riesling", "area_ha": 1350, "notes": "Danube terraces, Smaragd/Federspiel classification"},
    {"region": "Kakheti", "country": "Georgia", "lat": 41.75, "lon": 45.75, "type": "Both", "grapes": "Saperavi, Rkatsiteli", "area_ha": 48000, "notes": "8000-year winemaking tradition, qvevri clay vessels"},
    {"region": "Bekaa Valley", "country": "Lebanon", "lat": 33.85, "lon": 35.90, "type": "Red", "grapes": "Cabernet Sauvignon, Cinsault", "area_ha": 2000, "notes": "Ancient Phoenician winemaking, Château Musar"},
    {"region": "Franschhoek", "country": "South Africa", "lat": -33.91, "lon": 19.12, "type": "Both", "grapes": "Chenin Blanc, Shiraz", "area_ha": 2500, "notes": "French Huguenot heritage, Cap Classique sparkling"},
    {"region": "Colchagua Valley", "country": "Chile", "lat": -34.67, "lon": -71.22, "type": "Red", "grapes": "Carménère, Syrah", "area_ha": 28000, "notes": "Pacific-influenced terroir, premium reds"},
    {"region": "Swartland", "country": "South Africa", "lat": -33.45, "lon": 18.75, "type": "Both", "grapes": "Chenin Blanc, Syrah", "area_ha": 13000, "notes": "Revolution wines, old-bush-vine Chenin Blanc"},
    {"region": "Santorini", "country": "Greece", "lat": 36.39, "lon": 25.46, "type": "White", "grapes": "Assyrtiko", "area_ha": 1200, "notes": "Volcanic terroir, basket-trained kouloura vines"},
    {"region": "Trentino-Alto Adige", "country": "Italy", "lat": 46.07, "lon": 11.12, "type": "White", "grapes": "Pinot Grigio, Gewürztraminer", "area_ha": 15000, "notes": "Alpine wines, Germanic and Italian influences"},
    {"region": "Finger Lakes", "country": "USA", "lat": 42.65, "lon": -76.95, "type": "White", "grapes": "Riesling", "area_ha": 4000, "notes": "Cool-climate Riesling, glacial lake-effect"},
    {"region": "Cafayate (Salta)", "country": "Argentina", "lat": -26.07, "lon": -65.97, "type": "White", "grapes": "Torrontés", "area_ha": 3400, "notes": "High-altitude white wine at 1700m, aromatic Torrontés"},
    {"region": "Yarra Valley", "country": "Australia", "lat": -37.75, "lon": 145.47, "type": "Both", "grapes": "Pinot Noir, Chardonnay", "area_ha": 3200, "notes": "Cool-climate elegance, sparkling wine production"},
    {"region": "Walla Walla", "country": "USA", "lat": 46.07, "lon": -118.33, "type": "Red", "grapes": "Cabernet Sauvignon, Syrah", "area_ha": 1200, "notes": "Washington State premium reds, basalt terroir"},
    {"region": "Vale dos Vinhedos", "country": "Brazil", "lat": -29.17, "lon": -51.52, "type": "Both", "grapes": "Merlot, Chardonnay", "area_ha": 3600, "notes": "First Brazilian Denomination of Origin"},
    {"region": "Prosecco Hills", "country": "Italy", "lat": 45.90, "lon": 12.00, "type": "Sparkling", "grapes": "Glera", "area_ha": 24000, "notes": "UNESCO heritage hills, Charmat method sparkling"},
    {"region": "Jura", "country": "France", "lat": 46.73, "lon": 5.87, "type": "Both", "grapes": "Savagnin, Poulsard", "area_ha": 2000, "notes": "Vin Jaune oxidative style, biodynamic pioneers"},
    {"region": "Ningxia", "country": "China", "lat": 38.47, "lon": 106.27, "type": "Red", "grapes": "Cabernet Sauvignon", "area_ha": 38000, "notes": "China's Bordeaux, desert terroir at Helan Mountains"},
    {"region": "Etna", "country": "Italy", "lat": 37.75, "lon": 14.99, "type": "Both", "grapes": "Nerello Mascalese, Carricante", "area_ha": 1100, "notes": "Volcanic terroir, altitude vineyards up to 1000m"},
    {"region": "Nahe", "country": "Germany", "lat": 49.83, "lon": 7.80, "type": "White", "grapes": "Riesling", "area_ha": 4200, "notes": "Diverse soils, Helmut Dönnhoff's legendary Rieslings"},
    {"region": "Okanagan Valley", "country": "Canada", "lat": 49.88, "lon": -119.50, "type": "Both", "grapes": "Pinot Noir, Riesling", "area_ha": 4500, "notes": "Canada's premier wine region, icewine production"},
    {"region": "Côtes de Provence", "country": "France", "lat": 43.46, "lon": 6.22, "type": "Rosé", "grapes": "Grenache, Cinsault, Mourvèdre", "area_ha": 27000, "notes": "World rosé capital, 88% rosé production"},
]

# =====================================================================
# 6. STREET FOOD CAPITALS (~35)
# =====================================================================
STREET_FOOD_DATA = [
    {"city": "Bangkok", "country": "Thailand", "lat": 13.76, "lon": 100.50, "region": "Asia", "signature_dish": "Pad Thai, Som Tam, Mango Sticky Rice", "stalls_est": 100000, "avg_price_usd": 1.50, "notes": "Yaowarat (Chinatown), khlong-side vendors, awarded Michelin Bib Gourmand"},
    {"city": "Mexico City", "country": "Mexico", "lat": 19.43, "lon": -99.13, "region": "Latin America", "signature_dish": "Tacos al Pastor, Tlacoyos, Elote", "stalls_est": 50000, "avg_price_usd": 1.00, "notes": "Taco stands on every corner, CDMX street food UNESCO candidate"},
    {"city": "Istanbul", "country": "Turkey", "lat": 41.01, "lon": 28.98, "region": "Middle East", "signature_dish": "Simit, Balık Ekmek, Döner", "stalls_est": 35000, "avg_price_usd": 2.00, "notes": "Bosphorus fish sandwiches, simit carts, köfte stands"},
    {"city": "Marrakech", "country": "Morocco", "lat": 31.63, "lon": -8.00, "region": "Africa", "signature_dish": "Tagine, B'stilla, Snail Soup", "stalls_est": 8000, "avg_price_usd": 1.50, "notes": "Jemaa el-Fnaa night market, UNESCO Intangible Heritage"},
    {"city": "Mumbai", "country": "India", "lat": 19.08, "lon": 72.88, "region": "Asia", "signature_dish": "Vada Pav, Pav Bhaji, Bhel Puri", "stalls_est": 80000, "avg_price_usd": 0.50, "notes": "Beach-side chaat, dabbawala lunch delivery, Bollywood canteens"},
    {"city": "Hanoi", "country": "Vietnam", "lat": 21.03, "lon": 105.85, "region": "Asia", "signature_dish": "Pho, Bun Cha, Banh Mi", "stalls_est": 40000, "avg_price_usd": 1.00, "notes": "Old Quarter street dining, Obama-Bourdain bun cha fame"},
    {"city": "Singapore", "country": "Singapore", "lat": 1.35, "lon": 103.82, "region": "Asia", "signature_dish": "Chicken Rice, Laksa, Chilli Crab", "stalls_est": 6000, "avg_price_usd": 3.00, "notes": "Hawker centers UNESCO heritage, Michelin-starred hawkers"},
    {"city": "Lima", "country": "Peru", "lat": -12.05, "lon": -77.04, "region": "Latin America", "signature_dish": "Ceviche, Anticuchos, Picarones", "stalls_est": 15000, "avg_price_usd": 2.00, "notes": "Mistura food festival, pre-Columbian street food heritage"},
    {"city": "Penang (Georgetown)", "country": "Malaysia", "lat": 5.41, "lon": 100.33, "region": "Asia", "signature_dish": "Char Kway Teow, Asam Laksa, Cendol", "stalls_est": 12000, "avg_price_usd": 1.50, "notes": "UNESCO food city, Chinese-Malay-Indian fusion hawker stalls"},
    {"city": "Ho Chi Minh City", "country": "Vietnam", "lat": 10.82, "lon": 106.63, "region": "Asia", "signature_dish": "Banh Mi, Com Tam, Goi Cuon", "stalls_est": 45000, "avg_price_usd": 1.00, "notes": "Sidewalk pho culture, French-Vietnamese fusion"},
    {"city": "Taipei", "country": "Taiwan", "lat": 25.03, "lon": 121.57, "region": "Asia", "signature_dish": "Bubble Tea, Gua Bao, Stinky Tofu", "stalls_est": 30000, "avg_price_usd": 2.00, "notes": "Night markets (Shilin, Raohe), bubble tea origin"},
    {"city": "Kolkata", "country": "India", "lat": 22.57, "lon": 88.36, "region": "Asia", "signature_dish": "Kathi Roll, Puchka, Jhal Muri", "stalls_est": 50000, "avg_price_usd": 0.30, "notes": "Kathi roll birthplace, Park Street food scene"},
    {"city": "Lagos", "country": "Nigeria", "lat": 6.52, "lon": 3.38, "region": "Africa", "signature_dish": "Suya, Jollof Rice, Puff-Puff", "stalls_est": 40000, "avg_price_usd": 1.00, "notes": "Suya spots along roadsides, bukas (food stalls)"},
    {"city": "Cairo", "country": "Egypt", "lat": 30.04, "lon": 31.24, "region": "Middle East", "signature_dish": "Koshari, Ful, Ta'ameya (Falafel)", "stalls_est": 30000, "avg_price_usd": 0.75, "notes": "Koshari carts, bean fuul breakfast tradition"},
    {"city": "Osaka", "country": "Japan", "lat": 34.69, "lon": 135.50, "region": "Asia", "signature_dish": "Takoyaki, Okonomiyaki, Kushikatsu", "stalls_est": 20000, "avg_price_usd": 3.00, "notes": "Dotonbori food street, kuidaore (eat till you drop) culture"},
    {"city": "Oaxaca", "country": "Mexico", "lat": 17.07, "lon": -96.73, "region": "Latin America", "signature_dish": "Tlayuda, Chapulines, Mole", "stalls_est": 5000, "avg_price_usd": 1.50, "notes": "Mexico's food capital, grasshopper snacks, mezcal"},
    {"city": "Bogotá", "country": "Colombia", "lat": 4.71, "lon": -74.07, "region": "Latin America", "signature_dish": "Arepa, Empanada, Obleas", "stalls_est": 20000, "avg_price_usd": 1.00, "notes": "Arepa vendors on every street, La Candelaria food scene"},
    {"city": "Dakar", "country": "Senegal", "lat": 14.69, "lon": -17.44, "region": "Africa", "signature_dish": "Thieboudienne, Fataya, Dibi", "stalls_est": 8000, "avg_price_usd": 1.00, "notes": "Senegalese street grills, baobab juice vendors"},
    {"city": "Palermo", "country": "Italy", "lat": 38.12, "lon": 13.36, "region": "Europe", "signature_dish": "Arancini, Panelle, Sfincione", "stalls_est": 3000, "avg_price_usd": 2.00, "notes": "Ballarò and Vucciria markets, Arab-Norman food heritage"},
    {"city": "Delhi", "country": "India", "lat": 28.70, "lon": 77.10, "region": "Asia", "signature_dish": "Chaat, Chole Bhature, Paratha", "stalls_est": 70000, "avg_price_usd": 0.50, "notes": "Chandni Chowk food lane, Paranthe Wali Gali since 1872"},
    {"city": "Jemaa el-Fnaa", "country": "Morocco", "lat": 31.63, "lon": -7.99, "region": "Africa", "signature_dish": "Harira, Merguez, Msemen", "stalls_est": 2000, "avg_price_usd": 1.50, "notes": "UNESCO Masterpiece of Heritage, nightly food carnival"},
    {"city": "Chengdu", "country": "China", "lat": 30.57, "lon": 104.07, "region": "Asia", "signature_dish": "Mapo Tofu, Dan Dan Noodles, Hotpot", "stalls_est": 55000, "avg_price_usd": 1.50, "notes": "UNESCO City of Gastronomy, Sichuan spice capital"},
    {"city": "Fez", "country": "Morocco", "lat": 34.03, "lon": -5.00, "region": "Africa", "signature_dish": "Pastilla, Rfissa, Harcha", "stalls_est": 4000, "avg_price_usd": 1.50, "notes": "Medieval medina food stalls, oldest functioning food market"},
    {"city": "Cartagena", "country": "Colombia", "lat": 10.39, "lon": -75.51, "region": "Latin America", "signature_dish": "Arepas de Huevo, Ceviche, Cocadas", "stalls_est": 5000, "avg_price_usd": 1.00, "notes": "Palenquera fruit vendors, Caribbean coast flavors"},
    {"city": "Kuala Lumpur", "country": "Malaysia", "lat": 3.14, "lon": 101.69, "region": "Asia", "signature_dish": "Nasi Lemak, Roti Canai, Satay", "stalls_est": 25000, "avg_price_usd": 1.50, "notes": "Jalan Alor food street, mamak stall culture"},
    {"city": "Naples", "country": "Italy", "lat": 40.85, "lon": 14.27, "region": "Europe", "signature_dish": "Pizza Fritta, Sfogliatella, Cuoppo", "stalls_est": 5000, "avg_price_usd": 2.50, "notes": "Birthplace of pizza, UNESCO pizza-making heritage"},
    {"city": "Accra", "country": "Ghana", "lat": 5.56, "lon": -0.19, "region": "Africa", "signature_dish": "Kelewele, Waakye, Banku", "stalls_est": 15000, "avg_price_usd": 0.75, "notes": "Chop bars and roadside grills, fried plantain culture"},
    {"city": "Yangon", "country": "Myanmar", "lat": 16.87, "lon": 96.20, "region": "Asia", "signature_dish": "Mohinga, Tea Leaf Salad, Shan Noodles", "stalls_est": 20000, "avg_price_usd": 0.75, "notes": "Mohinga breakfast tradition, teahouse culture"},
    {"city": "Durban", "country": "South Africa", "lat": -29.86, "lon": 31.02, "region": "Africa", "signature_dish": "Bunny Chow, Vetkoek, Biltong", "stalls_est": 8000, "avg_price_usd": 1.50, "notes": "Bunny chow (curry in bread loaf), Indian-Zulu fusion"},
    {"city": "Guadalajara", "country": "Mexico", "lat": 20.67, "lon": -103.35, "region": "Latin America", "signature_dish": "Birria, Torta Ahogada, Tejuino", "stalls_est": 15000, "avg_price_usd": 1.50, "notes": "Birria taco origin, drowned sandwich (torta ahogada)"},
    {"city": "Dhaka", "country": "Bangladesh", "lat": 23.81, "lon": 90.41, "region": "Asia", "signature_dish": "Fuchka, Jhalmuri, Kacchi Biryani", "stalls_est": 60000, "avg_price_usd": 0.30, "notes": "Old Dhaka street food heritage, rickshaw-side vendors"},
    {"city": "Tunis", "country": "Tunisia", "lat": 36.81, "lon": 10.18, "region": "Africa", "signature_dish": "Brik, Lablabi, Fricassé", "stalls_est": 5000, "avg_price_usd": 1.00, "notes": "Medina food stalls, harissa on everything"},
    {"city": "Athens", "country": "Greece", "lat": 37.98, "lon": 23.73, "region": "Europe", "signature_dish": "Souvlaki, Koulouri, Loukoumades", "stalls_est": 8000, "avg_price_usd": 2.50, "notes": "Monastiraki souvlaki row, ancient agora food tradition"},
    {"city": "Manila", "country": "Philippines", "lat": 14.60, "lon": 120.98, "region": "Asia", "signature_dish": "Balut, Isaw, Kwek-Kwek", "stalls_est": 35000, "avg_price_usd": 0.50, "notes": "Adventurous street eats, turo-turo (point-point) stalls"},
    {"city": "Seoul", "country": "South Korea", "lat": 37.57, "lon": 126.98, "region": "Asia", "signature_dish": "Tteokbokki, Hotteok, Sundae", "stalls_est": 25000, "avg_price_usd": 2.50, "notes": "Myeongdong and Gwangjang Market, pojangmacha tent bars"},
]

# =====================================================================
# 7. UNESCO FOOD HERITAGE (~25)
# =====================================================================
UNESCO_FOOD = [
    {"name": "Mediterranean Diet", "country": "Spain, Italy, Greece, Morocco", "lat": 41.90, "lon": 12.50, "year_inscribed": 2013, "category": "Diet", "elements": "Olive oil, cereals, fruits, vegetables, fish, wine", "notes": "Shared by 7 countries, emphasis on conviviality and seasonal eating"},
    {"name": "French Gastronomic Meal", "country": "France", "lat": 48.86, "lon": 2.35, "year_inscribed": 2010, "category": "Cuisine", "elements": "Apéritif, entrée, fish, meat, cheese, dessert, digestif", "notes": "Art of fine dining, carefully chosen wines paired with each course"},
    {"name": "Washoku (Japanese Cuisine)", "country": "Japan", "lat": 35.68, "lon": 139.65, "year_inscribed": 2013, "category": "Cuisine", "elements": "Rice, miso, seasonal ingredients, ichiju-sansai format", "notes": "Respect for nature, seasonal awareness, New Year osechi tradition"},
    {"name": "Kimjang (Kimchi Making)", "country": "South Korea", "lat": 37.57, "lon": 126.98, "year_inscribed": 2013, "category": "Practice", "elements": "Napa cabbage, radish, gochugaru, jeotgal, garlic", "notes": "Communal preparation for winter, symbol of Korean identity"},
    {"name": "Turkish Coffee Culture", "country": "Turkey", "lat": 41.01, "lon": 28.98, "year_inscribed": 2013, "category": "Beverage", "elements": "Cezve brewing, fortune telling, serving rituals", "notes": "Ottoman tradition, unfiltered fine-ground coffee, social bonding"},
    {"name": "Lavash Breadmaking", "country": "Armenia", "lat": 40.18, "lon": 44.51, "year_inscribed": 2014, "category": "Practice", "elements": "Flatbread, tonir clay oven, communal baking", "notes": "Thin flatbread baked in underground clay oven, wedding rituals"},
    {"name": "Nsima Culinary Tradition", "country": "Malawi", "lat": -13.96, "lon": 33.79, "year_inscribed": 2017, "category": "Cuisine", "elements": "Maize porridge, relish, communal eating", "notes": "Cornmeal staple dish, social customs around preparation"},
    {"name": "Belgian Beer Culture", "country": "Belgium", "lat": 50.85, "lon": 4.35, "year_inscribed": 2016, "category": "Beverage", "elements": "Lambic, Trappist, abbey, craft brewing", "notes": "Over 1500 beer varieties, lambic spontaneous fermentation"},
    {"name": "Neapolitan Pizza", "country": "Italy", "lat": 40.85, "lon": 14.27, "year_inscribed": 2017, "category": "Practice", "elements": "San Marzano tomatoes, mozzarella, wood-fired oven", "notes": "Art of Pizzaiuolo, dough tossing, 485°C oven tradition"},
    {"name": "Traditional Mexican Cuisine", "country": "Mexico", "lat": 19.43, "lon": -99.13, "year_inscribed": 2010, "category": "Cuisine", "elements": "Corn, beans, chili, mole, tamales", "notes": "Michoacán ancestral cuisine, milpa farming system"},
    {"name": "Hawker Culture Singapore", "country": "Singapore", "lat": 1.35, "lon": 103.82, "year_inscribed": 2020, "category": "Practice", "elements": "Multi-ethnic food stalls, communal dining", "notes": "114 hawker centers, multicultural food tradition"},
    {"name": "Couscous", "country": "Algeria, Morocco, Tunisia, Mauritania", "lat": 36.75, "lon": 3.06, "year_inscribed": 2020, "category": "Cuisine", "elements": "Semolina, vegetables, meat, communal preparation", "notes": "North African staple, hand-rolled, Friday family meals"},
    {"name": "Baguette Craft", "country": "France", "lat": 48.86, "lon": 2.35, "year_inscribed": 2022, "category": "Practice", "elements": "Flour, water, salt, yeast, artisanal shaping", "notes": "Artisanal know-how and culture of baguette bread"},
    {"name": "Oshi Palav", "country": "Tajikistan", "lat": 38.56, "lon": 68.77, "year_inscribed": 2016, "category": "Cuisine", "elements": "Rice, carrots, meat, onions, spices", "notes": "Communal pilaf dish, celebration of hospitality"},
    {"name": "Dolma Making", "country": "Azerbaijan", "lat": 40.41, "lon": 49.87, "year_inscribed": 2017, "category": "Practice", "elements": "Grape leaves, minced meat, rice, herbs", "notes": "Wrapped vine-leaf tradition, communal preparation"},
    {"name": "Flat Bread Making (Saj)", "country": "Iran, Azerbaijan, Turkey, Kazakhstan, Kyrgyzstan", "lat": 35.69, "lon": 51.39, "year_inscribed": 2016, "category": "Practice", "elements": "Dough, convex griddle, communal baking", "notes": "Central Asian bread culture, shared across Silk Road nations"},
    {"name": "Al-Mansaf", "country": "Jordan", "lat": 31.95, "lon": 35.93, "year_inscribed": 2022, "category": "Cuisine", "elements": "Lamb, jameed yogurt, rice, pine nuts", "notes": "Bedouin hospitality feast, eaten with right hand"},
    {"name": "Harissa", "country": "Tunisia", "lat": 36.81, "lon": 10.18, "year_inscribed": 2022, "category": "Practice", "elements": "Dried chili, caraway, coriander, garlic, olive oil", "notes": "Chili paste preparation and social practices"},
    {"name": "Ancestral Brewery (Chicha)", "country": "Colombia", "lat": 4.71, "lon": -74.07, "year_inscribed": 2022, "category": "Beverage", "elements": "Fermented corn beverage, Muisca tradition", "notes": "Pre-Columbian maize beer, ritual and social importance"},
    {"name": "Date Palm Knowledge", "country": "UAE, Saudi Arabia, Bahrain, Egypt, Iraq, Jordan, Kuwait, Mauritania, Morocco, Oman, Palestine, Qatar, Sudan, Tunisia, Yemen", "lat": 24.47, "lon": 54.37, "year_inscribed": 2019, "category": "Practice", "elements": "Date cultivation, harvesting, processing", "notes": "Date palm as symbol of Arabian hospitality"},
    {"name": "Qvevri Winemaking", "country": "Georgia", "lat": 41.72, "lon": 44.79, "year_inscribed": 2013, "category": "Beverage", "elements": "Clay vessel fermentation, skin-contact wines", "notes": "8000-year-old tradition, buried clay qvevri vessels"},
    {"name": "Ristafari Gursha", "country": "Ethiopia", "lat": 9.02, "lon": 38.75, "year_inscribed": 2024, "category": "Practice", "elements": "Hand-feeding, injera, communal eating", "notes": "Gursha feeding tradition, expression of love and respect"},
    {"name": "Pincho Culture", "country": "Spain (Basque Country)", "lat": 43.32, "lon": -1.98, "year_inscribed": 2024, "category": "Cuisine", "elements": "Bar-hopping, small bites on bread, txakoli wine", "notes": "Pintxos bar culture, social ritual of San Sebastián"},
    {"name": "Tteok (Rice Cake Making)", "country": "South Korea", "lat": 37.57, "lon": 126.98, "year_inscribed": 2024, "category": "Practice", "elements": "Glutinous rice, steaming, pounding", "notes": "Celebration rice cakes, songpyeon for Chuseok"},
    {"name": "Sake Brewing", "country": "Japan", "lat": 34.69, "lon": 135.50, "year_inscribed": 2024, "category": "Beverage", "elements": "Rice, koji mold, parallel fermentation", "notes": "Traditional sake-making craft, toji master brewers"},
]

# =====================================================================
# 8. CHOCOLATE & CACAO ORIGINS (~30)
# =====================================================================
CHOCOLATE_DATA = [
    {"name": "Côte d'Ivoire", "lat": 6.83, "lon": -5.55, "type": "Producer", "variety": "Forastero", "annual_tons": 2200000, "pct_world": 38.0, "notes": "World's largest producer, bulk cacao"},
    {"name": "Ghana", "lat": 7.95, "lon": -1.02, "type": "Producer", "variety": "Forastero", "annual_tons": 800000, "pct_world": 14.0, "notes": "Premium West African beans, Cocobod quality control"},
    {"name": "Ecuador (Arriba)", "lat": -1.83, "lon": -79.53, "type": "Producer", "variety": "Nacional (Arriba)", "annual_tons": 365000, "pct_world": 6.3, "notes": "Fine-flavor cacao, floral arriba nacional variety"},
    {"name": "Indonesia (Sulawesi)", "lat": -2.50, "lon": 121.00, "type": "Producer", "variety": "Forastero/Criollo", "annual_tons": 660000, "pct_world": 11.4, "notes": "Third largest producer, Sulawesi and Sumatra beans"},
    {"name": "Nigeria", "lat": 7.49, "lon": 3.90, "type": "Producer", "variety": "Forastero", "annual_tons": 340000, "pct_world": 5.9, "notes": "Fourth largest producer, Ondo and Osun states"},
    {"name": "Cameroon", "lat": 4.05, "lon": 9.70, "type": "Producer", "variety": "Trinitario", "annual_tons": 290000, "pct_world": 5.0, "notes": "Volcanic soil cacao, growing fine-flavor segment"},
    {"name": "Brazil (Bahia)", "lat": -14.79, "lon": -39.04, "type": "Producer", "variety": "Forastero/Trinitario", "annual_tons": 270000, "pct_world": 4.7, "notes": "Historic cacao region, cabruca shade-growing system"},
    {"name": "Peru (San Martín)", "lat": -6.48, "lon": -76.37, "type": "Producer", "variety": "Criollo/Native", "annual_tons": 160000, "pct_world": 2.8, "notes": "Ancient Criollo varieties, Amazon origin hypothesis"},
    {"name": "Dominican Republic", "lat": 18.49, "lon": -69.93, "type": "Producer", "variety": "Trinitario", "annual_tons": 86000, "pct_world": 1.5, "notes": "Largest organic cacao exporter, Hispaniola heritage"},
    {"name": "Colombia", "lat": 7.12, "lon": -73.12, "type": "Producer", "variety": "Criollo/Trinitario", "annual_tons": 65000, "pct_world": 1.1, "notes": "Fine-flavor, Santander region, post-conflict cacao"},
    {"name": "Papua New Guinea", "lat": -6.31, "lon": 147.18, "type": "Producer", "variety": "Trinitario", "annual_tons": 45000, "pct_world": 0.8, "notes": "Unique Pacific Island terroir, small-holder farmers"},
    {"name": "Mexico (Tabasco)", "lat": 17.99, "lon": -92.93, "type": "Producer", "variety": "Criollo", "annual_tons": 28000, "pct_world": 0.5, "notes": "Birthplace of chocolate, Aztec xocolatl tradition"},
    {"name": "Venezuela (Chuao)", "lat": 10.48, "lon": -67.53, "type": "Producer", "variety": "Criollo", "annual_tons": 25000, "pct_world": 0.4, "notes": "Legendary Chuao beans, finest Criollo in the world"},
    {"name": "Trinidad and Tobago", "lat": 10.65, "lon": -61.50, "type": "Producer", "variety": "Trinitario", "annual_tons": 700, "pct_world": 0.01, "notes": "Trinitario variety origin, Imperial College estate"},
    {"name": "Madagascar", "lat": -18.77, "lon": 46.87, "type": "Producer", "variety": "Criollo/Trinitario", "annual_tons": 12000, "pct_world": 0.2, "notes": "Bright fruity beans, Sambirano Valley terroir"},
    {"name": "São Tomé and Príncipe", "lat": 0.19, "lon": 6.61, "type": "Producer", "variety": "Amelonado", "annual_tons": 3500, "pct_world": 0.06, "notes": "Volcanic island cacao, former Portuguese colonial plantations"},
    {"name": "Belize (Toledo)", "lat": 16.10, "lon": -88.80, "type": "Producer", "variety": "Criollo/Trinitario", "annual_tons": 900, "pct_world": 0.02, "notes": "Maya cacao heritage, bean-to-bar movement"},
    {"name": "Hawaii (Big Island)", "lat": 19.70, "lon": -155.09, "type": "Producer", "variety": "Trinitario", "annual_tons": 50, "pct_world": 0.001, "notes": "Only US cacao producer, volcanic terroir"},
    {"name": "Brussels", "lat": 50.85, "lon": 4.35, "type": "Chocolate Capital", "variety": "Praline Capital", "annual_tons": 0, "pct_world": 0.0, "notes": "220000+ tons chocolate produced annually, praline invention (1912)"},
    {"name": "Zurich", "lat": 47.38, "lon": 8.54, "type": "Chocolate Capital", "variety": "Swiss Chocolate", "annual_tons": 0, "pct_world": 0.0, "notes": "Lindt, Sprüngli, Swiss milk chocolate invention (1875)"},
    {"name": "Turin", "lat": 45.07, "lon": 7.69, "type": "Chocolate Capital", "variety": "Gianduja", "annual_tons": 0, "pct_world": 0.0, "notes": "Gianduja hazelnut chocolate, bicerin drink, CioccolaTO festival"},
    {"name": "Modica", "lat": 36.84, "lon": 14.76, "type": "Chocolate Capital", "variety": "Aztec-style", "annual_tons": 0, "pct_world": 0.0, "notes": "Ancient cold-processed chocolate, grainy Aztec technique"},
    {"name": "Bayonne", "lat": 43.49, "lon": -1.47, "type": "Chocolate Capital", "variety": "French Chocolate", "annual_tons": 0, "pct_world": 0.0, "notes": "France's chocolate capital since 1600s, Sephardic Jewish heritage"},
    {"name": "Villajoyosa", "lat": 38.51, "lon": -0.23, "type": "Chocolate Capital", "variety": "Spanish Chocolate", "annual_tons": 0, "pct_world": 0.0, "notes": "Valor chocolate, Spanish chocolate-making center since 1881"},
    {"name": "Hershey, PA", "lat": 40.29, "lon": -76.65, "type": "Chocolate Capital", "variety": "American Chocolate", "annual_tons": 0, "pct_world": 0.0, "notes": "Hershey company town, Chocolate World visitor center"},
    {"name": "Oaxaca", "lat": 17.07, "lon": -96.73, "type": "Chocolate Capital", "variety": "Mexican Chocolate", "annual_tons": 0, "pct_world": 0.0, "notes": "Traditional stone-ground chocolate, mole madre, tejate"},
    {"name": "Vevey", "lat": 46.46, "lon": 6.84, "type": "Chocolate Capital", "variety": "Nestlé/Cailler", "annual_tons": 0, "pct_world": 0.0, "notes": "Nestlé HQ, Alimentarium food museum, Cailler factory"},
    {"name": "Grenada", "lat": 12.12, "lon": -61.68, "type": "Producer", "variety": "Trinitario", "annual_tons": 700, "pct_world": 0.01, "notes": "Spice Isle, organic cacao, Grenada Chocolate Company"},
    {"name": "Tain-l'Hermitage", "lat": 45.07, "lon": 4.84, "type": "Chocolate Capital", "variety": "Valrhona", "annual_tons": 0, "pct_world": 0.0, "notes": "Valrhona headquarters, Cité du Chocolat museum"},
]

# =====================================================================
# 9. TEA CULTURES & ORIGINS (~35)
# =====================================================================
TEA_DATA = [
    {"name": "Yunnan, China", "lat": 25.04, "lon": 102.71, "type": "Black", "variety": "Pu-erh, Dianhong", "annual_tons": 450000, "notes": "Birthplace of tea, ancient tea trees, Pu-erh fermentation"},
    {"name": "Fujian, China", "lat": 26.08, "lon": 119.30, "type": "Oolong", "variety": "Tieguanyin, Da Hong Pao", "annual_tons": 420000, "notes": "Wuyi Mountains oolong, white tea origin (Fuding)"},
    {"name": "Zhejiang, China", "lat": 30.27, "lon": 120.15, "type": "Green", "variety": "Longjing (Dragon Well)", "annual_tons": 380000, "notes": "West Lake Longjing, pan-fired green tea masterpiece"},
    {"name": "Anhui, China", "lat": 30.60, "lon": 117.00, "type": "Green", "variety": "Keemun, Huangshan Maofeng", "annual_tons": 150000, "notes": "Keemun black tea for English Breakfast, Yellow Mountain greens"},
    {"name": "Assam, India", "lat": 26.14, "lon": 91.74, "type": "Black", "variety": "Assam Orthodox/CTC", "annual_tons": 700000, "notes": "World's largest tea-growing region, malty robust flavor"},
    {"name": "Darjeeling, India", "lat": 27.04, "lon": 88.26, "type": "Black", "variety": "Darjeeling First Flush", "annual_tons": 8500, "notes": "Champagne of teas, Himalayan terroir, GI protected"},
    {"name": "Nilgiri, India", "lat": 11.41, "lon": 76.69, "type": "Black", "variety": "Nilgiri", "annual_tons": 62000, "notes": "Blue Mountains of South India, fragrant and brisk"},
    {"name": "Uji, Japan", "lat": 34.88, "lon": 135.80, "type": "Green", "variety": "Matcha, Gyokuro", "annual_tons": 2600, "notes": "Finest matcha origin, shade-grown gyokuro since 1200s"},
    {"name": "Shizuoka, Japan", "lat": 34.98, "lon": 138.38, "type": "Green", "variety": "Sencha", "annual_tons": 30000, "notes": "Japan's largest tea prefecture, Mt. Fuji slopes"},
    {"name": "Kagoshima, Japan", "lat": 31.56, "lon": 130.56, "type": "Green", "variety": "Sencha, Kabusecha", "annual_tons": 24000, "notes": "Volcanic soil, second largest Japanese tea region"},
    {"name": "Sri Lanka (Nuwara Eliya)", "lat": 6.97, "lon": 80.77, "type": "Black", "variety": "Ceylon Highland", "annual_tons": 280000, "notes": "High-grown Ceylon, champagne of Ceylon teas, 2000m altitude"},
    {"name": "Sri Lanka (Uva)", "lat": 6.90, "lon": 81.06, "type": "Black", "variety": "Ceylon Uva", "annual_tons": 50000, "notes": "Eastern monsoon influence, unique character"},
    {"name": "Kenya (Kericho)", "lat": -0.37, "lon": 35.28, "type": "Black", "variety": "Kenyan CTC", "annual_tons": 540000, "notes": "World's largest tea exporter, equatorial highland growing"},
    {"name": "Taiwan (Alishan)", "lat": 23.51, "lon": 120.70, "type": "Oolong", "variety": "Alishan High Mountain Oolong", "annual_tons": 15000, "notes": "Cloud-shrouded peaks, high-mountain oolong perfection"},
    {"name": "Taiwan (Pinglin)", "lat": 24.94, "lon": 121.71, "type": "Oolong", "variety": "Baozhong, Oriental Beauty", "annual_tons": 5000, "notes": "Bug-bitten Oriental Beauty, honey-like oxidized oolong"},
    {"name": "Turkey (Rize)", "lat": 41.02, "lon": 40.52, "type": "Black", "variety": "Rize Çay", "annual_tons": 280000, "notes": "Highest per-capita tea consumption, tulip glass tradition"},
    {"name": "Morocco", "lat": 33.97, "lon": -6.85, "type": "Green", "variety": "Gunpowder + Mint", "annual_tons": 0, "notes": "Mint tea ceremony (atai), hospitality ritual, Chinese gunpowder tea"},
    {"name": "Argentina (Misiones)", "lat": -27.36, "lon": -55.90, "type": "Mixed", "variety": "Yerba Mate", "annual_tons": 320000, "notes": "Mate gourd tradition, shared communal drinking"},
    {"name": "Iran", "lat": 37.27, "lon": 49.59, "type": "Black", "variety": "Lahijan", "annual_tons": 25000, "notes": "Samovar tradition, Caspian coast cultivation"},
    {"name": "Nepal (Ilam)", "lat": 26.91, "lon": 87.93, "type": "Black", "variety": "Nepal Orthodox", "annual_tons": 25000, "notes": "Himalayan terroir similar to Darjeeling, organic focus"},
    {"name": "Malawi", "lat": -15.94, "lon": 35.27, "type": "Black", "variety": "Malawian CTC", "annual_tons": 52000, "notes": "Thyolo and Mulanje highlands, Africa's oldest tea industry"},
    {"name": "Georgia (Guria)", "lat": 42.01, "lon": 42.19, "type": "Black", "variety": "Georgian", "annual_tons": 3500, "notes": "Soviet-era tea powerhouse, specialty revival underway"},
    {"name": "Vietnam (Thai Nguyen)", "lat": 21.59, "lon": 105.85, "type": "Green", "variety": "Thai Nguyen Green", "annual_tons": 200000, "notes": "Tan Cuong region, jasmine teas, growing specialty market"},
    {"name": "Rwanda", "lat": -2.35, "lon": 29.27, "type": "Black", "variety": "Rwandan Orthodox", "annual_tons": 30000, "notes": "Thousand hills terroir, growing specialty reputation"},
    {"name": "UK (London)", "lat": 51.51, "lon": -0.13, "type": "Black", "variety": "English Breakfast, Earl Grey", "annual_tons": 0, "notes": "Afternoon tea tradition since 1840, global tea trade hub"},
    {"name": "Russia", "lat": 55.76, "lon": 37.62, "type": "Black", "variety": "Samovar blends", "annual_tons": 0, "notes": "Samovar culture, tea with jam (varenye), fourth largest consumer"},
    {"name": "Japan (Kyoto)", "lat": 35.01, "lon": 135.77, "type": "Green", "variety": "Matcha ceremony", "annual_tons": 0, "notes": "Chanoyu tea ceremony, wabi-sabi aesthetics, Sen no Rikyu tradition"},
    {"name": "China (Hangzhou)", "lat": 30.25, "lon": 120.17, "type": "Green", "variety": "Longjing ceremony", "annual_tons": 0, "notes": "Gongfu tea ceremony, West Lake tea culture, tea museum"},
    {"name": "Azores, Portugal", "lat": 37.78, "lon": -25.50, "type": "Green", "variety": "Chá Gorreana", "annual_tons": 40, "notes": "Only European tea plantation, volcanic soil since 1883"},
    {"name": "Charleston, SC, USA", "lat": 32.78, "lon": -79.93, "type": "Mixed", "variety": "American Classic", "annual_tons": 50, "notes": "Only US tea garden (Charleston Tea Garden), since 1888"},
    {"name": "Bangladesh (Sylhet)", "lat": 24.89, "lon": 91.87, "type": "Black", "variety": "Sylheti CTC", "annual_tons": 96000, "notes": "Surma Valley tea gardens, largest in Bangladesh"},
    {"name": "Uganda", "lat": 0.35, "lon": 32.58, "type": "Black", "variety": "Ugandan CTC", "annual_tons": 67000, "notes": "East African highland tea, Toro and Ankole regions"},
    {"name": "Tanzania (Usambara)", "lat": -4.72, "lon": 38.35, "type": "Black", "variety": "Usambara", "annual_tons": 38000, "notes": "Usambara Mountains, CTC processing, Luponde estate"},
    {"name": "Colombia (Bitaco)", "lat": 3.71, "lon": -76.63, "type": "Mixed", "variety": "Bitaco", "annual_tons": 800, "notes": "Small but growing specialty tea, Andean terroir"},
]

# =====================================================================
# 10. SPICE TRADE ROUTES (~40)
# =====================================================================
SPICE_DATA = [
    {"spice": "Black Pepper", "origin": "Kerala, India", "lat": 10.85, "lon": 76.27, "category": "Hot Spice", "annual_tons": 55000, "top_producers": "Vietnam, India, Brazil", "notes": "King of spices, drove Age of Exploration, Malabar Coast origin"},
    {"spice": "Cinnamon (True)", "origin": "Sri Lanka", "lat": 6.93, "lon": 79.84, "category": "Sweet", "top_producers": "Sri Lanka, Madagascar", "annual_tons": 35000, "notes": "Ceylon cinnamon (C. verum), ancient Egyptian trade"},
    {"spice": "Cassia Cinnamon", "origin": "Southern China", "lat": 22.82, "lon": 108.32, "category": "Sweet", "top_producers": "China, Indonesia, Vietnam", "annual_tons": 180000, "notes": "Most common commercial cinnamon, thicker bark"},
    {"spice": "Saffron", "origin": "Iran / Kashmir", "lat": 34.83, "lon": 56.22, "category": "Aromatic", "top_producers": "Iran, India, Spain", "annual_tons": 418, "notes": "Most expensive spice by weight, 150000 flowers per kg"},
    {"spice": "Vanilla", "origin": "Mexico (Totonac)", "lat": 20.21, "lon": -96.85, "category": "Sweet", "top_producers": "Madagascar, Indonesia, Mexico", "annual_tons": 7500, "notes": "Aztec/Totonac origin, hand-pollinated orchid"},
    {"spice": "Turmeric", "origin": "Southern India", "lat": 12.97, "lon": 77.59, "category": "Aromatic", "top_producers": "India, Bangladesh, Myanmar", "annual_tons": 1200000, "notes": "Golden spice, curcumin compound, Ayurvedic medicine"},
    {"spice": "Cardamom (Green)", "origin": "Western Ghats, India", "lat": 9.93, "lon": 77.12, "category": "Aromatic", "top_producers": "Guatemala, India, Sri Lanka", "annual_tons": 55000, "notes": "Queen of spices, chai essential, third most expensive"},
    {"spice": "Cloves", "origin": "Maluku Islands, Indonesia", "lat": -2.58, "lon": 128.09, "category": "Aromatic", "top_producers": "Indonesia, Tanzania, Madagascar", "annual_tons": 140000, "notes": "Spice Islands origin, drove Portuguese colonization"},
    {"spice": "Nutmeg & Mace", "origin": "Banda Islands, Indonesia", "lat": -4.52, "lon": 129.89, "category": "Aromatic", "top_producers": "Indonesia, India, Guatemala", "annual_tons": 45000, "notes": "Banda Islands monopoly, Manhattan traded for Run Island"},
    {"spice": "Ginger", "origin": "Southeast Asia", "lat": 13.76, "lon": 100.50, "category": "Hot Spice", "top_producers": "India, Nigeria, China", "annual_tons": 4200000, "notes": "Ancient Austronesian trade, medicinal and culinary staple"},
    {"spice": "Star Anise", "origin": "Southern China / Vietnam", "lat": 22.50, "lon": 108.33, "category": "Aromatic", "top_producers": "China, Vietnam", "annual_tons": 40000, "notes": "Key pho and five-spice ingredient, shikimic acid source"},
    {"spice": "Cumin", "origin": "Eastern Mediterranean", "lat": 33.51, "lon": 36.29, "category": "Savory", "top_producers": "India, Syria, Turkey", "annual_tons": 450000, "notes": "Ancient Egyptian, Roman, and Indian culinary staple"},
    {"spice": "Coriander", "origin": "Mediterranean / Western Asia", "lat": 37.98, "lon": 23.73, "category": "Herb", "top_producers": "India, Morocco, Russia", "annual_tons": 600000, "notes": "Seeds and leaves (cilantro), oldest known spice use"},
    {"spice": "Chili Pepper", "origin": "Mexico / Central America", "lat": 17.07, "lon": -96.73, "category": "Hot Spice", "top_producers": "China, India, Mexico", "annual_tons": 4500000, "notes": "Columbian Exchange, capsaicin heat, Scoville scale"},
    {"spice": "Paprika", "origin": "Central Mexico", "lat": 19.43, "lon": -99.13, "category": "Savory", "top_producers": "Hungary, Spain, China", "annual_tons": 65000, "notes": "Hungarian national spice, smoky pimentón in Spain"},
    {"spice": "Fenugreek", "origin": "Near East", "lat": 33.89, "lon": 35.50, "category": "Savory", "top_producers": "India, Egypt, Morocco", "annual_tons": 320000, "notes": "Methi seeds and leaves, curry powder component"},
    {"spice": "Sumac", "origin": "Middle East", "lat": 33.89, "lon": 35.83, "category": "Savory", "top_producers": "Turkey, Iran, Italy", "annual_tons": 15000, "notes": "Tart berry spice, za'atar blend component"},
    {"spice": "Szechuan Pepper", "origin": "Sichuan, China", "lat": 30.57, "lon": 104.07, "category": "Hot Spice", "top_producers": "China, Japan, Nepal", "annual_tons": 30000, "notes": "Numbing mala sensation, not a true pepper"},
    {"spice": "Allspice", "origin": "Jamaica / Central America", "lat": 18.11, "lon": -77.30, "category": "Aromatic", "top_producers": "Jamaica, Guatemala, Honduras", "annual_tons": 10000, "notes": "Pimento berry, jerk seasoning essential, Columbus discovery"},
    {"spice": "Mustard Seed", "origin": "Mediterranean / India", "lat": 43.30, "lon": -0.37, "category": "Hot Spice", "top_producers": "Canada, Nepal, India", "annual_tons": 700000, "notes": "Dijon tradition, Bengali panch phoron, Roman condiment"},
    {"spice": "Lemongrass", "origin": "South / Southeast Asia", "lat": 13.76, "lon": 100.50, "category": "Herb", "top_producers": "India, Thailand, Guatemala", "annual_tons": 80000, "notes": "Tom yum essential, citral compound, aromatic grass"},
    {"spice": "Galangal", "origin": "Indonesia", "lat": -6.21, "lon": 106.85, "category": "Hot Spice", "top_producers": "Indonesia, Thailand, China", "annual_tons": 25000, "notes": "Tom kha essential, ginger family, medieval European spice"},
    {"spice": "Wasabi", "origin": "Japan", "lat": 35.15, "lon": 138.82, "category": "Hot Spice", "top_producers": "Japan, Taiwan, New Zealand", "annual_tons": 2000, "notes": "Most expensive vegetable to grow, stream-bed cultivation"},
    {"spice": "Za'atar Herb", "origin": "Levant", "lat": 31.77, "lon": 35.23, "category": "Herb", "top_producers": "Palestine, Lebanon, Jordan", "annual_tons": 5000, "notes": "Wild thyme blend with sumac and sesame, breakfast staple"},
    {"spice": "Annatto", "origin": "Tropical Americas", "lat": -3.47, "lon": -62.21, "category": "Savory", "top_producers": "Brazil, Peru, Kenya", "annual_tons": 15000, "notes": "Achiote seed, natural food coloring, Mayan body paint"},
    {"spice": "Tamarind", "origin": "Tropical Africa", "lat": 8.98, "lon": 38.75, "category": "Savory", "top_producers": "India, Thailand, Mexico", "annual_tons": 600000, "notes": "Sweet-sour pod, pad thai and Worcestershire sauce component"},
    {"spice": "Bay Leaf", "origin": "Mediterranean", "lat": 39.62, "lon": 19.92, "category": "Herb", "top_producers": "Turkey, India, Morocco", "annual_tons": 20000, "notes": "Laurus nobilis, Roman laurel wreaths, slow-cook aromatic"},
    {"spice": "Mastic", "origin": "Chios, Greece", "lat": 38.37, "lon": 26.14, "category": "Aromatic", "top_producers": "Greece (Chios only)", "annual_tons": 150, "notes": "Tears of Chios, PDO-protected resin, ice cream and liqueur"},
    {"spice": "Kaffir Lime Leaf", "origin": "Southeast Asia", "lat": 7.87, "lon": 98.38, "category": "Herb", "top_producers": "Thailand, Indonesia, India", "annual_tons": 12000, "notes": "Thai curry essential, makrut lime, citrus fragrance"},
    {"spice": "Asafoetida", "origin": "Central Asia / Iran", "lat": 36.30, "lon": 59.60, "category": "Savory", "top_producers": "Afghanistan, Iran, India", "annual_tons": 1500, "notes": "Devil's dung, hing powder, onion-garlic substitute in Jain cooking"},
    {"spice": "Grains of Paradise", "origin": "West Africa", "lat": 7.95, "lon": -1.02, "category": "Hot Spice", "top_producers": "Ghana, Togo, Nigeria", "annual_tons": 800, "notes": "Medieval pepper substitute, Aframomum melegueta, gin botanical"},
    {"spice": "Long Pepper", "origin": "India / Indonesia", "lat": 10.85, "lon": 76.27, "category": "Hot Spice", "top_producers": "India, Indonesia, Thailand", "annual_tons": 3000, "notes": "Pre-black-pepper trade, ancient Roman favorite, Piper longum"},
    {"spice": "Mahlab", "origin": "Middle East / Mediterranean", "lat": 36.20, "lon": 37.16, "category": "Sweet", "top_producers": "Turkey, Syria, Iran", "annual_tons": 500, "notes": "Cherry pit kernel spice, tsoureki bread, Middle Eastern pastries"},
    {"spice": "Tonka Bean", "origin": "Venezuela / Brazil", "lat": 8.35, "lon": -62.64, "category": "Sweet", "top_producers": "Venezuela, Brazil, Nigeria", "annual_tons": 200, "notes": "Coumarin compound, vanilla-like, banned in US food but prized in perfumery"},
    {"spice": "Juniper Berry", "origin": "Northern Hemisphere", "lat": 46.95, "lon": 7.45, "category": "Aromatic", "top_producers": "Italy, Albania, India", "annual_tons": 5000, "notes": "Gin essential botanical, game meat seasoning, Alpine cuisine"},
    {"spice": "Sumatra Pepper (Andaliman)", "origin": "North Sumatra, Indonesia", "lat": 2.54, "lon": 98.71, "category": "Hot Spice", "top_producers": "Indonesia", "annual_tons": 500, "notes": "Batak cuisine staple, citrusy numbing Zanthoxylum, local terroir spice"},
    {"spice": "Pink Pepper", "origin": "Brazil / Peru", "lat": -22.91, "lon": -43.17, "category": "Aromatic", "top_producers": "Brazil, Réunion, Madagascar", "annual_tons": 4000, "notes": "Schinus molle berry, not true pepper, French nouvelle cuisine"},
    {"spice": "Nigella Seed", "origin": "Western Asia", "lat": 39.93, "lon": 32.86, "category": "Savory", "top_producers": "India, Egypt, Turkey", "annual_tons": 45000, "notes": "Black cumin / kalonji, naan bread topping, Prophetic medicine"},
    {"spice": "Achiote (Annatto)", "origin": "Yucatan, Mexico", "lat": 20.97, "lon": -89.59, "category": "Savory", "top_producers": "Mexico, Guatemala, Peru", "annual_tons": 8000, "notes": "Cochinita pibil essential, recado rojo paste, Mayan heritage"},
]

# =====================================================================
# SPICE TRADE ROUTE LINES (historical maritime/land routes)
# =====================================================================
TRADE_ROUTES = [
    {"name": "Maritime Spice Route (East)", "points": [[1.35, 103.82], [-6.21, 106.85], [-2.58, 128.09], [-4.52, 129.89]], "color": "#ef4444"},
    {"name": "Maritime Spice Route (India-Arabia)", "points": [[10.85, 76.27], [12.97, 77.59], [23.02, 72.57], [21.49, 39.19]], "color": "#f59e0b"},
    {"name": "Maritime Spice Route (Arabia-Europe)", "points": [[21.49, 39.19], [30.04, 32.57], [38.72, -9.14], [51.51, -0.13]], "color": "#3b82f6"},
    {"name": "Silk Road (Land)", "points": [[34.05, 108.93], [39.47, 75.99], [39.65, 66.96], [41.01, 28.98]], "color": "#8b5cf6"},
    {"name": "Cinnamon Route", "points": [[6.93, 79.84], [12.30, 45.03], [30.04, 32.57], [41.90, 12.50]], "color": "#10b981"},
]


# =====================================================================
# HELPER: build a Folium map with dark tiles
# =====================================================================
def _base_map(center=(20, 0), zoom=2):
    """Return a dark-themed folium map."""
    return folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )


def _render_map(m, height=550):
    """Render a folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _download_csv(df, filename, key):
    """Render a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        "Download CSV",
        data=buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def _dark_chart_style():
    """Apply dark background to matplotlib."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": "#0a0e1a",
        "axes.facecolor": "#111827",
        "axes.edgecolor": "#2a3550",
        "text.color": "#e8ecf4",
        "xtick.color": "#8b97b0",
        "ytick.color": "#8b97b0",
        "axes.labelcolor": "#e8ecf4",
        "grid.color": "#2a3550",
    })


# =====================================================================
# MODE RENDERERS
# =====================================================================

def _render_michelin():
    """Mode 1: Michelin Star Restaurants."""
    st.markdown("#### Michelin Star Restaurants by City")
    min_stars = st.slider("Minimum total stars", 10, 200, 20, key="gm_mich_min")
    filtered = [c for c in MICHELIN_CITIES if c["total_stars"] >= min_stars]
    if not filtered:
        st.warning("No cities match the filter.")
        return

    df = pd.DataFrame(filtered)

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Cities shown", len(filtered))
    c2.metric("Total 3-star", int(df["three_star"].sum()))
    c3.metric("Total stars", int(df["total_stars"].sum()))

    # Chart
    _dark_chart_style()
    top = df.nlargest(15, "total_stars")
    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.barh(top["city"], top["total_stars"], color="#06b6d4")
    ax.set_xlabel("Total Michelin Stars")
    ax.set_title("Top Cities by Michelin Stars")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = "#fbbf24" if r["three_star"] >= 5 else "#f59e0b" if r["three_star"] >= 2 else "#d97706"
        popup_html = (
            f"<b>{escape(str(r['city']))}, {escape(str(r['country']))}</b><br>"
            f"3-star: {r['three_star']} | 2-star: {r['two_star']} | 1-star: {r['one_star']}<br>"
            f"<b>Total: {r['total_stars']}</b><br>{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=max(4, r["total_stars"] / 8),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{r['city']}: {r['total_stars']} stars",
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["city", "country", "three_star", "two_star", "one_star", "total_stars", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "michelin_cities.csv", "gm_dl_mich")


def _render_cuisines():
    """Mode 2: World Cuisine Origins."""
    st.markdown("#### World Cuisine Origins")
    families = sorted(set(c["family"] for c in CUISINE_ORIGINS))
    sel_family = st.multiselect("Filter by cuisine family", families, default=families, key="gm_cuis_fam")
    filtered = [c for c in CUISINE_ORIGINS if c["family"] in sel_family]
    if not filtered:
        st.warning("No cuisines match the filter.")
        return

    df = pd.DataFrame(filtered)

    c1, c2 = st.columns(2)
    c1.metric("Cuisines shown", len(filtered))
    family_counts = df["family"].value_counts()
    c2.metric("Families", len(family_counts))

    # Chart
    _dark_chart_style()
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = [CUISINE_COLORS.get(f, "#06b6d4") for f in family_counts.index]
    ax.pie(family_counts.values, labels=family_counts.index, colors=colors, autopct="%1.0f%%", textprops={"color": "#e8ecf4"})
    ax.set_title("Cuisines by Family")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = CUISINE_COLORS.get(r["family"], "#06b6d4")
        popup_html = (
            f"<b>{escape(str(r['cuisine']))}</b><br>"
            f"Region: {escape(str(r['region']))}<br>"
            f"Family: {r['family']}<br>"
            f"Signature: {escape(str(r['signature_dish']))}<br>"
            f"Origin: {r['year_origin']}<br>"
            f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8, color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{r['cuisine']}",
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["cuisine", "region", "family", "signature_dish", "year_origin", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "cuisine_origins.csv", "gm_dl_cuis")


def _render_coffee():
    """Mode 3: Coffee Culture Map."""
    st.markdown("#### Coffee Culture Map")
    show_type = st.radio("Show", ["All", "Producers", "Cafe Cities"], horizontal=True, key="gm_coff_type")
    if show_type == "Producers":
        filtered = [c for c in COFFEE_DATA if c["type"] == "Producer"]
    elif show_type == "Cafe Cities":
        filtered = [c for c in COFFEE_DATA if c["type"] == "Cafe City"]
    else:
        filtered = list(COFFEE_DATA)
    if not filtered:
        st.warning("No data.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Locations", len(filtered))
    producers = df[df["type"] == "Producer"]
    c2.metric("Total production (t)", f"{int(producers['annual_tons'].sum()):,}" if len(producers) else "0")
    c3.metric("Cafe Cities", len(df[df["type"] == "Cafe City"]))

    # Chart - top producers
    if len(producers) > 0:
        _dark_chart_style()
        top = producers.nlargest(12, "annual_tons")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.barh(top["name"], top["annual_tons"] / 1000, color="#92400e")
        ax.set_xlabel("Annual Production (thousand tons)")
        ax.set_title("Top Coffee Producers")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = COFFEE_COLORS.get(r["type"], "#06b6d4")
        icon_prefix = "fa"
        popup_html = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Type: {r['type']}<br>"
            f"Variety: {escape(str(r['variety']))}<br>"
            + (f"Production: {r['annual_tons']:,} tons/yr<br>" if r["annual_tons"] > 0 else "")
            + f"{escape(str(r['notes']))}"
        )
        radius = max(4, min(15, r["annual_tons"] / 200000 + 4)) if r["annual_tons"] > 0 else 6
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(str(r["name"])),
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["name", "type", "variety", "annual_tons", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "coffee_culture.csv", "gm_dl_coff")


def _render_beer():
    """Mode 4: Beer & Brewery Capitals."""
    st.markdown("#### Beer & Brewery Capitals")
    styles = sorted(set(c["style"] for c in BEER_DATA))
    sel_styles = st.multiselect("Filter by beer style", styles, default=styles, key="gm_beer_sty")
    filtered = [c for c in BEER_DATA if c["style"] in sel_styles]
    if not filtered:
        st.warning("No cities match.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Cities", len(filtered))
    c2.metric("Total Breweries", int(df["breweries"].sum()))
    c3.metric("Avg liters/capita", f"{df['annual_liters_pc'].mean():.0f}")

    # Chart
    _dark_chart_style()
    top = df.nlargest(15, "breweries")
    fig, ax = plt.subplots(figsize=(10, 4))
    colors = [BEER_COLORS.get(s, "#f59e0b") for s in top["style"]]
    ax.barh(top["city"], top["breweries"], color=colors)
    ax.set_xlabel("Number of Breweries")
    ax.set_title("Top Beer Cities by Brewery Count")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = BEER_COLORS.get(r["style"], "#f59e0b")
        popup_html = (
            f"<b>{escape(str(r['city']))}, {escape(str(r['country']))}</b><br>"
            f"Style: {r['style']}<br>"
            f"Breweries: {r['breweries']}<br>"
            f"Famous: {escape(str(r['famous_beer']))}<br>"
            f"Consumption: {r['annual_liters_pc']} L/capita/yr<br>"
            f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=max(4, r["breweries"] / 8),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{r['city']}: {r['breweries']} breweries",
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["city", "country", "style", "breweries", "famous_beer", "annual_liters_pc", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "beer_capitals.csv", "gm_dl_beer")


def _render_wine():
    """Mode 5: Wine Regions of the World."""
    st.markdown("#### Wine Regions of the World")
    wine_types = sorted(set(r["type"] for r in WINE_REGIONS))
    sel_types = st.multiselect("Filter by wine type", wine_types, default=wine_types, key="gm_wine_type")
    filtered = [r for r in WINE_REGIONS if r["type"] in sel_types]
    if not filtered:
        st.warning("No regions match.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Regions", len(filtered))
    c2.metric("Total area (ha)", f"{int(df['area_ha'].sum()):,}")
    c3.metric("Countries", df["country"].nunique())

    # Chart
    _dark_chart_style()
    top = df.nlargest(15, "area_ha")
    fig, ax = plt.subplots(figsize=(10, 4))
    colors = [WINE_COLORS_MAP.get(t, "#8b5cf6") for t in top["type"]]
    ax.barh(top["region"], top["area_ha"] / 1000, color=colors)
    ax.set_xlabel("Vineyard Area (thousand ha)")
    ax.set_title("Largest Wine Regions")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = WINE_COLORS_MAP.get(r["type"], "#8b5cf6")
        popup_html = (
            f"<b>{escape(str(r['region']))}</b><br>"
            f"Country: {escape(str(r['country']))}<br>"
            f"Type: {r['type']}<br>"
            f"Grapes: {escape(str(r['grapes']))}<br>"
            f"Area: {r['area_ha']:,} ha<br>"
            f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=max(4, min(14, r["area_ha"] / 8000 + 4)),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{r['region']} ({r['type']})",
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["region", "country", "type", "grapes", "area_ha", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "wine_regions.csv", "gm_dl_wine")


def _render_street_food():
    """Mode 6: Street Food Capitals."""
    st.markdown("#### Street Food Capitals")
    regions = sorted(set(c["region"] for c in STREET_FOOD_DATA))
    sel_reg = st.multiselect("Filter by region", regions, default=regions, key="gm_sf_reg")
    filtered = [c for c in STREET_FOOD_DATA if c["region"] in sel_reg]
    if not filtered:
        st.warning("No cities match.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Cities", len(filtered))
    c2.metric("Est. total stalls", f"{int(df['stalls_est'].sum()):,}")
    c3.metric("Avg price (USD)", f"${df['avg_price_usd'].mean():.2f}")

    # Chart
    _dark_chart_style()
    top = df.nlargest(15, "stalls_est")
    fig, ax = plt.subplots(figsize=(10, 4))
    colors = [STREET_FOOD_COLORS.get(r, "#06b6d4") for r in top["region"]]
    ax.barh(top["city"], top["stalls_est"] / 1000, color=colors)
    ax.set_xlabel("Estimated Street Food Stalls (thousands)")
    ax.set_title("Top Street Food Cities")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = STREET_FOOD_COLORS.get(r["region"], "#06b6d4")
        popup_html = (
            f"<b>{escape(str(r['city']))}, {escape(str(r['country']))}</b><br>"
            f"Region: {r['region']}<br>"
            f"Signature: {escape(str(r['signature_dish']))}<br>"
            f"Stalls: ~{r['stalls_est']:,}<br>"
            f"Avg price: ${r['avg_price_usd']:.2f}<br>"
            f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=max(4, min(14, r["stalls_est"] / 8000 + 4)),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{r['city']}: ~{r['stalls_est']:,} stalls",
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["city", "country", "region", "signature_dish", "stalls_est", "avg_price_usd", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "street_food_capitals.csv", "gm_dl_sf")


def _render_unesco():
    """Mode 7: UNESCO Food Heritage."""
    st.markdown("#### UNESCO Intangible Heritage - Food Traditions")
    categories = sorted(set(u["category"] for u in UNESCO_FOOD))
    sel_cat = st.multiselect("Filter by category", categories, default=categories, key="gm_un_cat")
    filtered = [u for u in UNESCO_FOOD if u["category"] in sel_cat]
    if not filtered:
        st.warning("No entries match.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Heritage entries", len(filtered))
    c2.metric("Earliest inscription", int(df["year_inscribed"].min()))
    c3.metric("Latest inscription", int(df["year_inscribed"].max()))

    # Chart
    _dark_chart_style()
    cat_counts = df["category"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [UNESCO_COLORS.get(c, "#06b6d4") for c in cat_counts.index]
    ax.pie(cat_counts.values, labels=cat_counts.index, colors=colors, autopct="%1.0f%%", textprops={"color": "#e8ecf4"})
    ax.set_title("UNESCO Food Heritage by Category")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = UNESCO_COLORS.get(r["category"], "#06b6d4")
        popup_html = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Country: {escape(str(r['country']))}<br>"
            f"Category: {r['category']}<br>"
            f"Inscribed: {r['year_inscribed']}<br>"
            f"Elements: {escape(str(r['elements']))}<br>"
            f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=9, color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{r['name']} ({r['year_inscribed']})",
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["name", "country", "category", "year_inscribed", "elements", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "unesco_food_heritage.csv", "gm_dl_un")


def _render_chocolate():
    """Mode 8: Chocolate & Cacao Origins."""
    st.markdown("#### Chocolate & Cacao Origins")
    show_type = st.radio("Show", ["All", "Producers", "Chocolate Capitals"], horizontal=True, key="gm_choc_type")
    if show_type == "Producers":
        filtered = [c for c in CHOCOLATE_DATA if c["type"] == "Producer"]
    elif show_type == "Chocolate Capitals":
        filtered = [c for c in CHOCOLATE_DATA if c["type"] == "Chocolate Capital"]
    else:
        filtered = list(CHOCOLATE_DATA)
    if not filtered:
        st.warning("No data.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Locations", len(filtered))
    producers = df[df["type"] == "Producer"]
    c2.metric("Total production (t)", f"{int(producers['annual_tons'].sum()):,}" if len(producers) else "0")
    c3.metric("Varieties", producers["variety"].nunique() if len(producers) else 0)

    # Chart - top producers
    if len(producers) > 0:
        _dark_chart_style()
        top = producers.nlargest(12, "annual_tons")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.barh(top["name"], top["annual_tons"] / 1000, color="#92400e")
        ax.set_xlabel("Annual Production (thousand tons)")
        ax.set_title("Top Cacao Producers")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = CHOCOLATE_COLORS.get(r["type"], "#d97706")
        radius = max(4, min(15, r["annual_tons"] / 150000 + 4)) if r["annual_tons"] > 0 else 7
        popup_html = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Type: {r['type']}<br>"
            f"Variety: {escape(str(r['variety']))}<br>"
            + (f"Production: {r['annual_tons']:,} tons/yr<br>" if r["annual_tons"] > 0 else "")
            + (f"World share: {r['pct_world']}%<br>" if r["pct_world"] > 0 else "")
            + f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(str(r["name"])),
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["name", "type", "variety", "annual_tons", "pct_world", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "chocolate_cacao.csv", "gm_dl_choc")


def _render_tea():
    """Mode 9: Tea Cultures & Origins."""
    st.markdown("#### Tea Cultures & Origins")
    tea_types = sorted(set(t["type"] for t in TEA_DATA))
    sel_types = st.multiselect("Filter by tea type", tea_types, default=tea_types, key="gm_tea_type")
    filtered = [t for t in TEA_DATA if t["type"] in sel_types]
    if not filtered:
        st.warning("No regions match.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Regions", len(filtered))
    prod = df[df["annual_tons"] > 0]
    c2.metric("Total production (t)", f"{int(prod['annual_tons'].sum()):,}" if len(prod) else "0")
    c3.metric("Varieties", df["variety"].nunique())

    # Chart
    if len(prod) > 0:
        _dark_chart_style()
        top = prod.nlargest(12, "annual_tons")
        fig, ax = plt.subplots(figsize=(10, 4))
        colors_list = [TEA_COLORS.get(t, "#10b981") for t in top["type"]]
        ax.barh(top["name"], top["annual_tons"] / 1000, color=colors_list)
        ax.set_xlabel("Annual Production (thousand tons)")
        ax.set_title("Top Tea Producing Regions")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Map
    m = _base_map()
    for _, r in df.iterrows():
        color = TEA_COLORS.get(r["type"], "#10b981")
        if color == "#1e293b":
            color = "#64748b"  # make black tea markers visible on dark map
        if color == "#e2e8f0":
            color = "#94a3b8"  # make white tea markers visible
        radius = max(4, min(14, r["annual_tons"] / 50000 + 4)) if r["annual_tons"] > 0 else 6
        popup_html = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Type: {r['type']}<br>"
            f"Variety: {escape(str(r['variety']))}<br>"
            + (f"Production: {r['annual_tons']:,} tons/yr<br>" if r["annual_tons"] > 0 else "")
            + f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(str(r["name"])),
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["name", "type", "variety", "annual_tons", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "tea_cultures.csv", "gm_dl_tea")


def _render_spice():
    """Mode 10: Spice Trade Routes."""
    st.markdown("#### Spice Trade Routes & Origins")
    categories = sorted(set(s["category"] for s in SPICE_DATA))
    sel_cat = st.multiselect("Filter by spice category", categories, default=categories, key="gm_sp_cat")
    show_routes = st.checkbox("Show historical trade routes", value=True, key="gm_sp_routes")
    filtered = [s for s in SPICE_DATA if s["category"] in sel_cat]
    if not filtered:
        st.warning("No spices match.")
        return

    df = pd.DataFrame(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Spices", len(filtered))
    c2.metric("Total production (t)", f"{int(df['annual_tons'].sum()):,}")
    c3.metric("Categories", df["category"].nunique())

    # Chart
    _dark_chart_style()
    top = df.nlargest(15, "annual_tons")
    fig, ax = plt.subplots(figsize=(10, 4))
    colors_list = [SPICE_COLORS.get(c, "#f59e0b") for c in top["category"]]
    ax.barh(top["spice"], top["annual_tons"] / 1000, color=colors_list)
    ax.set_xlabel("Annual Production (thousand tons)")
    ax.set_title("Top Spices by Production Volume")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = _base_map()

    # Draw trade routes first (if enabled)
    if show_routes:
        for route in TRADE_ROUTES:
            folium.PolyLine(
                route["points"],
                color=route["color"],
                weight=3,
                opacity=0.6,
                dash_array="8",
                tooltip=route["name"],
            ).add_to(m)

    for _, r in df.iterrows():
        color = SPICE_COLORS.get(r["category"], "#f59e0b")
        popup_html = (
            f"<b>{escape(str(r['spice']))}</b><br>"
            f"Origin: {escape(str(r['origin']))}<br>"
            f"Category: {r['category']}<br>"
            f"Production: {r['annual_tons']:,} tons/yr<br>"
            f"Top producers: {escape(str(r['top_producers']))}<br>"
            f"{escape(str(r['notes']))}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=max(4, min(13, r["annual_tons"] / 300000 + 4)),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(r["spice"])),
        ).add_to(m)
    _render_map(m)

    st.dataframe(df[["spice", "origin", "category", "annual_tons", "top_producers", "notes"]], width="stretch", hide_index=True)
    _download_csv(df, "spice_trade.csv", "gm_dl_sp")


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
_MODE_DISPATCH = {
    MAP_TYPES[0]: _render_michelin,
    MAP_TYPES[1]: _render_cuisines,
    MAP_TYPES[2]: _render_coffee,
    MAP_TYPES[3]: _render_beer,
    MAP_TYPES[4]: _render_wine,
    MAP_TYPES[5]: _render_street_food,
    MAP_TYPES[6]: _render_unesco,
    MAP_TYPES[7]: _render_chocolate,
    MAP_TYPES[8]: _render_tea,
    MAP_TYPES[9]: _render_spice,
}


def render_gastronomy_maps_tab():
    """Render the Gastronomy & Food Culture Maps tab."""
    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>Gastronomy &amp; Food Culture</h4>"
        "<p>Explore world cuisines, Michelin stars, coffee &amp; tea cultures, "
        "wine regions, street food, spice routes, and UNESCO food heritage</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Map Mode", MAP_TYPES, key="gm_mode")

    renderer = _MODE_DISPATCH.get(mode)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown mode: {mode}")
