# -*- coding: utf-8 -*-
"""
Wine, Beer & Spirits Maps module for TerraScout AI.
Provides 10 interactive map modes covering wine regions, grape varieties,
craft breweries, whisky distilleries, champagne zones, wine classification,
historic wine routes, beer culture, world spirits, and vineyard terroir.

Data sources:
  - Overpass API (craft=brewery|winery|distillery, landuse=vineyard)
  - Curated datasets for wine regions, appellations, and terroir
All free, no API key required.
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

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS & COLOR PALETTE
# ═══════════════════════════════════════════════════════════════
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"
BORDER = "#2a3550"
ACCENT = "#06b6d4"

MAP_MODES = [
    "1. World Wine Regions",
    "2. Grape Varieties",
    "3. Craft Breweries",
    "4. Whisky Distilleries",
    "5. Champagne & Sparkling",
    "6. Wine Classification",
    "7. Historic Wine Routes",
    "8. Beer Culture",
    "9. Spirits of the World",
    "10. Vineyard Terroir",
]

# ═══════════════════════════════════════════════════════════════
# 1. WORLD WINE REGIONS  (curated)
# ═══════════════════════════════════════════════════════════════
WINE_REGIONS = [
    # France
    {"name": "Bordeaux", "country": "France", "lat": 44.8378, "lon": -0.5792, "grapes": "Cabernet Sauvignon, Merlot, Cabernet Franc", "style": "Full-bodied reds, sweet whites", "area_ha": 111000, "color": "#8b0000"},
    {"name": "Burgundy (Bourgogne)", "country": "France", "lat": 47.0522, "lon": 4.3832, "grapes": "Pinot Noir, Chardonnay", "style": "Elegant reds, mineral whites", "area_ha": 29500, "color": "#800020"},
    {"name": "Champagne", "country": "France", "lat": 49.0469, "lon": 3.9553, "grapes": "Chardonnay, Pinot Noir, Pinot Meunier", "style": "Sparkling wine", "area_ha": 34000, "color": "#FFD700"},
    {"name": "Rhone Valley", "country": "France", "lat": 44.1260, "lon": 4.8058, "grapes": "Syrah, Grenache, Viognier", "style": "Spicy reds, aromatic whites", "area_ha": 71000, "color": "#a0522d"},
    {"name": "Loire Valley", "country": "France", "lat": 47.3941, "lon": 0.6848, "grapes": "Sauvignon Blanc, Chenin Blanc, Cabernet Franc", "style": "Crisp whites, light reds, rose", "area_ha": 57000, "color": "#90ee90"},
    {"name": "Alsace", "country": "France", "lat": 48.1660, "lon": 7.3060, "grapes": "Riesling, Gewurztraminer, Pinot Gris", "style": "Aromatic dry whites", "area_ha": 15600, "color": "#98fb98"},
    {"name": "Languedoc-Roussillon", "country": "France", "lat": 43.2000, "lon": 2.8000, "grapes": "Grenache, Syrah, Mourvedre, Carignan", "style": "Value reds, Vins Doux Naturels", "area_ha": 228000, "color": "#cd5c5c"},
    {"name": "Provence", "country": "France", "lat": 43.5283, "lon": 6.2595, "grapes": "Grenache, Cinsault, Mourvedre", "style": "Rose, light reds", "area_ha": 27000, "color": "#ffb6c1"},
    # Italy
    {"name": "Tuscany (Chianti / Brunello)", "country": "Italy", "lat": 43.3188, "lon": 11.3308, "grapes": "Sangiovese, Cabernet Sauvignon", "style": "Structured reds, Super Tuscans", "area_ha": 63000, "color": "#dc143c"},
    {"name": "Piedmont (Barolo / Barbaresco)", "country": "Italy", "lat": 44.6933, "lon": 8.0353, "grapes": "Nebbiolo, Barbera, Moscato", "style": "Powerful tannic reds, sparkling Moscato", "area_ha": 46000, "color": "#c41e3a"},
    {"name": "Veneto (Valpolicella / Soave)", "country": "Italy", "lat": 45.4384, "lon": 10.9916, "grapes": "Corvina, Garganega, Glera", "style": "Amarone, Prosecco, Soave", "area_ha": 87000, "color": "#e8a0bf"},
    {"name": "Sicily", "country": "Italy", "lat": 37.5999, "lon": 14.0154, "grapes": "Nero d'Avola, Nerello Mascalese, Grillo", "style": "Bold reds, volcanic whites", "area_ha": 98000, "color": "#ff6347"},
    {"name": "Friuli Venezia Giulia", "country": "Italy", "lat": 46.0711, "lon": 13.2346, "grapes": "Pinot Grigio, Friulano, Ribolla Gialla", "style": "Crisp whites, orange wines", "area_ha": 27000, "color": "#ffa07a"},
    # Spain
    {"name": "Rioja", "country": "Spain", "lat": 42.4661, "lon": -2.4460, "grapes": "Tempranillo, Garnacha, Graciano", "style": "Oak-aged reds, Crianza/Reserva", "area_ha": 65000, "color": "#b22222"},
    {"name": "Ribera del Duero", "country": "Spain", "lat": 41.6333, "lon": -3.7000, "grapes": "Tempranillo (Tinto Fino)", "style": "Concentrated reds", "area_ha": 23000, "color": "#a52a2a"},
    {"name": "Priorat", "country": "Spain", "lat": 41.2000, "lon": 0.7500, "grapes": "Garnacha, Carinena", "style": "Intense mineral reds", "area_ha": 1900, "color": "#8b0000"},
    {"name": "Rias Baixas", "country": "Spain", "lat": 42.3000, "lon": -8.7500, "grapes": "Albarino", "style": "Fresh aromatic whites", "area_ha": 4100, "color": "#7cfc00"},
    {"name": "Jerez (Sherry)", "country": "Spain", "lat": 36.6850, "lon": -6.1261, "grapes": "Palomino, Pedro Ximenez, Moscatel", "style": "Fortified wines, Sherry", "area_ha": 7000, "color": "#daa520"},
    # Portugal
    {"name": "Douro Valley (Port)", "country": "Portugal", "lat": 41.1579, "lon": -7.7227, "grapes": "Touriga Nacional, Touriga Franca, Tinta Roriz", "style": "Port wine, still reds", "area_ha": 45000, "color": "#722f37"},
    {"name": "Alentejo", "country": "Portugal", "lat": 38.5667, "lon": -7.9000, "grapes": "Aragonez, Trincadeira, Antao Vaz", "style": "Ripe fruit-forward reds", "area_ha": 24000, "color": "#d2691e"},
    # Germany & Austria
    {"name": "Mosel", "country": "Germany", "lat": 49.7339, "lon": 6.6843, "grapes": "Riesling", "style": "Elegant Riesling, steep slopes", "area_ha": 8770, "color": "#32cd32"},
    {"name": "Rheingau", "country": "Germany", "lat": 50.0167, "lon": 8.0500, "grapes": "Riesling, Spatburgunder", "style": "Classic Riesling, Pinot Noir", "area_ha": 3100, "color": "#3cb371"},
    {"name": "Wachau", "country": "Austria", "lat": 48.3667, "lon": 15.4167, "grapes": "Gruner Veltliner, Riesling", "style": "Dry mineral whites", "area_ha": 1350, "color": "#66cdaa"},
    # USA
    {"name": "Napa Valley", "country": "USA", "lat": 38.5025, "lon": -122.2654, "grapes": "Cabernet Sauvignon, Chardonnay, Merlot", "style": "Premium Cabernet, cult wines", "area_ha": 18200, "color": "#ff4500"},
    {"name": "Sonoma County", "country": "USA", "lat": 38.5110, "lon": -122.8371, "grapes": "Pinot Noir, Chardonnay, Zinfandel", "style": "Diverse styles, coastal influence", "area_ha": 24000, "color": "#ff6347"},
    {"name": "Willamette Valley", "country": "USA", "lat": 45.0000, "lon": -123.0000, "grapes": "Pinot Noir, Pinot Gris, Chardonnay", "style": "Burgundy-style Pinot Noir", "area_ha": 14000, "color": "#c71585"},
    {"name": "Paso Robles", "country": "USA", "lat": 35.6264, "lon": -120.6910, "grapes": "Zinfandel, Cabernet Sauvignon, Rhone varieties", "style": "Bold reds, Rhone blends", "area_ha": 16000, "color": "#e9967a"},
    {"name": "Finger Lakes", "country": "USA", "lat": 42.6167, "lon": -76.9000, "grapes": "Riesling, Cabernet Franc", "style": "Cool-climate Riesling", "area_ha": 4200, "color": "#87ceeb"},
    # South America
    {"name": "Mendoza", "country": "Argentina", "lat": -32.8895, "lon": -68.8458, "grapes": "Malbec, Cabernet Sauvignon, Torrontes", "style": "High-altitude Malbec", "area_ha": 155000, "color": "#9400d3"},
    {"name": "Maipo Valley", "country": "Chile", "lat": -33.6500, "lon": -70.6667, "grapes": "Cabernet Sauvignon, Carmenere", "style": "Premium Cabernet", "area_ha": 11000, "color": "#4169e1"},
    {"name": "Colchagua Valley", "country": "Chile", "lat": -34.6500, "lon": -71.2167, "grapes": "Carmenere, Syrah, Cabernet Sauvignon", "style": "Rich reds, Carmenere", "area_ha": 29000, "color": "#6a5acd"},
    {"name": "Casablanca Valley", "country": "Chile", "lat": -33.3167, "lon": -71.4167, "grapes": "Sauvignon Blanc, Chardonnay, Pinot Noir", "style": "Cool-climate whites", "area_ha": 5600, "color": "#87cefa"},
    # Australia & New Zealand
    {"name": "Barossa Valley", "country": "Australia", "lat": -34.5611, "lon": 138.9500, "grapes": "Shiraz, Grenache, Cabernet Sauvignon", "style": "Rich old-vine Shiraz", "area_ha": 13500, "color": "#ff8c00"},
    {"name": "McLaren Vale", "country": "Australia", "lat": -35.2167, "lon": 138.5500, "grapes": "Shiraz, Grenache, Cabernet", "style": "Mediterranean reds", "area_ha": 8000, "color": "#e65100"},
    {"name": "Margaret River", "country": "Australia", "lat": -33.9500, "lon": 115.0667, "grapes": "Cabernet Sauvignon, Chardonnay, Sauvignon Blanc/Semillon", "style": "Bordeaux-style blends", "area_ha": 5500, "color": "#ff7043"},
    {"name": "Hunter Valley", "country": "Australia", "lat": -32.7833, "lon": 151.1500, "grapes": "Semillon, Shiraz", "style": "Aged Semillon, Shiraz", "area_ha": 4700, "color": "#ffab40"},
    {"name": "Marlborough", "country": "New Zealand", "lat": -41.5134, "lon": 173.9612, "grapes": "Sauvignon Blanc, Pinot Noir", "style": "Pungent Sauvignon Blanc", "area_ha": 26800, "color": "#00e676"},
    {"name": "Central Otago", "country": "New Zealand", "lat": -45.0312, "lon": 169.1320, "grapes": "Pinot Noir, Riesling", "style": "Southern-hemisphere Pinot Noir", "area_ha": 2000, "color": "#e91e63"},
    # South Africa
    {"name": "Stellenbosch", "country": "South Africa", "lat": -33.9368, "lon": 18.8602, "grapes": "Cabernet Sauvignon, Pinotage, Chenin Blanc", "style": "Bordeaux-style reds, Pinotage", "area_ha": 16500, "color": "#ff5722"},
    {"name": "Swartland", "country": "South Africa", "lat": -33.3500, "lon": 18.7333, "grapes": "Chenin Blanc, Syrah, Grenache", "style": "Old-vine natural wines", "area_ha": 14000, "color": "#bf360c"},
    # Other
    {"name": "Tokaj", "country": "Hungary", "lat": 48.1183, "lon": 21.4000, "grapes": "Furmint, Harslevelu", "style": "Sweet Tokaji Aszu", "area_ha": 5500, "color": "#ffc107"},
    {"name": "Santorini", "country": "Greece", "lat": 36.3932, "lon": 25.4615, "grapes": "Assyrtiko", "style": "Volcanic mineral whites", "area_ha": 1200, "color": "#00bcd4"},
    {"name": "Bekaa Valley", "country": "Lebanon", "lat": 33.8500, "lon": 35.9000, "grapes": "Cabernet Sauvignon, Cinsault, Obaideh", "style": "Bordeaux-influenced reds", "area_ha": 3000, "color": "#795548"},
    {"name": "Ningxia", "country": "China", "lat": 38.5000, "lon": 106.2000, "grapes": "Cabernet Sauvignon, Marselan", "style": "Emerging fine reds", "area_ha": 38000, "color": "#e53935"},
    {"name": "Yamanashi", "country": "Japan", "lat": 35.6642, "lon": 138.5684, "grapes": "Koshu, Muscat Bailey A", "style": "Delicate whites, light reds", "area_ha": 3800, "color": "#f48fb1"},
    {"name": "Okanagan Valley", "country": "Canada", "lat": 49.5000, "lon": -119.5833, "grapes": "Pinot Noir, Riesling, Merlot", "style": "Cool-climate, ice wine", "area_ha": 4100, "color": "#42a5f5"},
    {"name": "Georgia (Kakheti)", "country": "Georgia", "lat": 41.8333, "lon": 45.5000, "grapes": "Saperavi, Rkatsiteli", "style": "Amber/orange wine in qvevri", "area_ha": 55000, "color": "#ff9800"},
]

# ═══════════════════════════════════════════════════════════════
# 2. GRAPE VARIETIES  (curated)
# ═══════════════════════════════════════════════════════════════
GRAPE_VARIETIES = [
    # Red grapes
    {"grape": "Cabernet Sauvignon", "type": "Red", "origin": "Bordeaux, France", "regions": "Bordeaux, Napa Valley, Coonawarra, Stellenbosch, Maipo Valley", "lat": 44.84, "lon": -0.58, "flavor": "Blackcurrant, cedar, tobacco", "color": "#8b0000"},
    {"grape": "Merlot", "type": "Red", "origin": "Bordeaux, France", "regions": "Bordeaux (Pomerol), Napa Valley, Chile, NE Italy", "lat": 44.92, "lon": -0.24, "flavor": "Plum, chocolate, herbs", "color": "#a52a2a"},
    {"grape": "Pinot Noir", "type": "Red", "origin": "Burgundy, France", "regions": "Burgundy, Oregon, Central Otago, Marlborough, Sonoma", "lat": 47.05, "lon": 4.38, "flavor": "Cherry, earth, mushroom", "color": "#c41e3a"},
    {"grape": "Syrah / Shiraz", "type": "Red", "origin": "Rhone Valley, France", "regions": "Northern Rhone, Barossa Valley, Washington State", "lat": 45.19, "lon": 4.83, "flavor": "Blackberry, pepper, smoke", "color": "#4a0080"},
    {"grape": "Tempranillo", "type": "Red", "origin": "Rioja, Spain", "regions": "Rioja, Ribera del Duero, Toro, Alentejo", "lat": 42.47, "lon": -2.45, "flavor": "Plum, leather, vanilla", "color": "#b22222"},
    {"grape": "Sangiovese", "type": "Red", "origin": "Tuscany, Italy", "regions": "Chianti, Brunello di Montalcino, Romagna", "lat": 43.32, "lon": 11.33, "flavor": "Cherry, tomato leaf, earth", "color": "#dc143c"},
    {"grape": "Nebbiolo", "type": "Red", "origin": "Piedmont, Italy", "regions": "Barolo, Barbaresco, Langhe", "lat": 44.69, "lon": 8.04, "flavor": "Rose, tar, truffle", "color": "#800020"},
    {"grape": "Malbec", "type": "Red", "origin": "Cahors, France", "regions": "Mendoza, Cahors, Salta", "lat": -32.89, "lon": -68.85, "flavor": "Blackberry, plum, cocoa", "color": "#9400d3"},
    {"grape": "Grenache / Garnacha", "type": "Red", "origin": "Aragon, Spain", "regions": "Southern Rhone, Priorat, Sardinia, Barossa", "lat": 41.65, "lon": -0.88, "flavor": "Raspberry, spice, herbs", "color": "#e74c3c"},
    {"grape": "Zinfandel / Primitivo", "type": "Red", "origin": "Croatia", "regions": "California, Puglia", "lat": 38.50, "lon": -122.27, "flavor": "Jammy berries, pepper, licorice", "color": "#e91e63"},
    {"grape": "Cabernet Franc", "type": "Red", "origin": "Basque Country", "regions": "Loire Valley, Bordeaux, Finger Lakes", "lat": 47.23, "lon": 0.09, "flavor": "Raspberry, bell pepper, violet", "color": "#ad1457"},
    {"grape": "Mourvedre / Monastrell", "type": "Red", "origin": "Spain", "regions": "Bandol, Jumilla, Barossa Valley", "lat": 43.14, "lon": 5.76, "flavor": "Blackberry, game, earth", "color": "#6a1b9a"},
    {"grape": "Pinotage", "type": "Red", "origin": "South Africa", "regions": "Stellenbosch, Swartland", "lat": -33.94, "lon": 18.86, "flavor": "Smoke, banana, red fruit", "color": "#d32f2f"},
    {"grape": "Carmenere", "type": "Red", "origin": "Bordeaux, France", "regions": "Chile (Colchagua, Maipo)", "lat": -34.65, "lon": -71.22, "flavor": "Red pepper, dark fruit, spice", "color": "#b71c1c"},
    {"grape": "Saperavi", "type": "Red", "origin": "Georgia", "regions": "Kakheti, Georgia", "lat": 41.83, "lon": 45.50, "flavor": "Dark cherry, plum, spice", "color": "#880e4f"},
    # White grapes
    {"grape": "Chardonnay", "type": "White", "origin": "Burgundy, France", "regions": "Burgundy, Champagne, Napa, Margaret River, Marlborough", "lat": 46.45, "lon": 4.77, "flavor": "Apple, butter, citrus", "color": "#ffd700"},
    {"grape": "Sauvignon Blanc", "type": "White", "origin": "Loire Valley, France", "regions": "Sancerre, Marlborough, Bordeaux, Stellenbosch", "lat": 47.33, "lon": 2.83, "flavor": "Gooseberry, grass, grapefruit", "color": "#7cfc00"},
    {"grape": "Riesling", "type": "White", "origin": "Rhine, Germany", "regions": "Mosel, Alsace, Finger Lakes, Clare Valley", "lat": 49.73, "lon": 6.68, "flavor": "Lime, petrol, honey", "color": "#32cd32"},
    {"grape": "Pinot Grigio / Pinot Gris", "type": "White", "origin": "Burgundy, France", "regions": "Friuli, Alsace, Oregon, New Zealand", "lat": 46.07, "lon": 13.23, "flavor": "Pear, almond, citrus", "color": "#90ee90"},
    {"grape": "Gewurztraminer", "type": "White", "origin": "Alto Adige / Alsace", "regions": "Alsace, Alto Adige, New Zealand", "lat": 48.17, "lon": 7.31, "flavor": "Lychee, rose, ginger", "color": "#ffb6c1"},
    {"grape": "Chenin Blanc", "type": "White", "origin": "Loire Valley, France", "regions": "Vouvray, Savennieres, Stellenbosch, Swartland", "lat": 47.37, "lon": 0.81, "flavor": "Apple, honey, quince", "color": "#fff44f"},
    {"grape": "Gruner Veltliner", "type": "White", "origin": "Austria", "regions": "Wachau, Kamptal, Kremstal", "lat": 48.37, "lon": 15.42, "flavor": "White pepper, citrus, lentil", "color": "#66cdaa"},
    {"grape": "Albarino", "type": "White", "origin": "NW Iberia", "regions": "Rias Baixas, Vinho Verde", "lat": 42.30, "lon": -8.75, "flavor": "Peach, saline, citrus", "color": "#87ceeb"},
    {"grape": "Viognier", "type": "White", "origin": "Northern Rhone", "regions": "Condrieu, Languedoc, Virginia, Australia", "lat": 45.46, "lon": 4.77, "flavor": "Apricot, blossom, peach", "color": "#ffcc80"},
    {"grape": "Assyrtiko", "type": "White", "origin": "Santorini, Greece", "regions": "Santorini, Attica", "lat": 36.39, "lon": 25.46, "flavor": "Citrus, mineral, saline", "color": "#00bcd4"},
    {"grape": "Torrontes", "type": "White", "origin": "Argentina", "regions": "Salta, Cafayate", "lat": -25.38, "lon": -65.97, "flavor": "Rose petal, peach, lychee", "color": "#f8bbd0"},
    {"grape": "Furmint", "type": "White", "origin": "Hungary", "regions": "Tokaj", "lat": 48.12, "lon": 21.40, "flavor": "Lime, apple, smoke", "color": "#ffc107"},
]

# ═══════════════════════════════════════════════════════════════
# 4. WHISKY DISTILLERY TRAILS  (curated)
# ═══════════════════════════════════════════════════════════════
WHISKY_TRAILS = [
    # Scotland - Speyside
    {"name": "The Glenlivet", "country": "Scotland", "sub_region": "Speyside", "lat": 57.3430, "lon": -3.3400, "type": "Single Malt", "founded": 1824, "color": "#daa520"},
    {"name": "Glenfiddich", "country": "Scotland", "sub_region": "Speyside", "lat": 57.4540, "lon": -3.1280, "type": "Single Malt", "founded": 1887, "color": "#daa520"},
    {"name": "Macallan", "country": "Scotland", "sub_region": "Speyside", "lat": 57.4846, "lon": -3.2100, "type": "Single Malt", "founded": 1824, "color": "#daa520"},
    {"name": "Aberlour", "country": "Scotland", "sub_region": "Speyside", "lat": 57.4670, "lon": -3.2280, "type": "Single Malt", "founded": 1879, "color": "#daa520"},
    {"name": "Cardhu", "country": "Scotland", "sub_region": "Speyside", "lat": 57.4180, "lon": -3.3540, "type": "Single Malt", "founded": 1824, "color": "#daa520"},
    # Scotland - Islay
    {"name": "Laphroaig", "country": "Scotland", "sub_region": "Islay", "lat": 55.6300, "lon": -6.1520, "type": "Single Malt (Peated)", "founded": 1815, "color": "#2e7d32"},
    {"name": "Ardbeg", "country": "Scotland", "sub_region": "Islay", "lat": 55.6400, "lon": -6.1060, "type": "Single Malt (Peated)", "founded": 1815, "color": "#2e7d32"},
    {"name": "Lagavulin", "country": "Scotland", "sub_region": "Islay", "lat": 55.6350, "lon": -6.1260, "type": "Single Malt (Peated)", "founded": 1816, "color": "#2e7d32"},
    {"name": "Bowmore", "country": "Scotland", "sub_region": "Islay", "lat": 55.7580, "lon": -6.2900, "type": "Single Malt", "founded": 1779, "color": "#2e7d32"},
    # Scotland - Highland & Islands
    {"name": "Talisker", "country": "Scotland", "sub_region": "Skye", "lat": 57.3020, "lon": -6.3560, "type": "Single Malt", "founded": 1830, "color": "#1565c0"},
    {"name": "Dalmore", "country": "Scotland", "sub_region": "Highland", "lat": 57.6880, "lon": -4.2440, "type": "Single Malt", "founded": 1839, "color": "#1565c0"},
    {"name": "Oban", "country": "Scotland", "sub_region": "Highland", "lat": 56.4120, "lon": -5.4740, "type": "Single Malt", "founded": 1794, "color": "#1565c0"},
    # Ireland
    {"name": "Jameson (Midleton)", "country": "Ireland", "sub_region": "Cork", "lat": 51.9130, "lon": -8.1170, "type": "Blended Irish", "founded": 1780, "color": "#4caf50"},
    {"name": "Bushmills", "country": "Ireland", "sub_region": "Antrim", "lat": 55.2040, "lon": -6.5170, "type": "Single Malt Irish", "founded": 1608, "color": "#4caf50"},
    {"name": "Redbreast (Midleton)", "country": "Ireland", "sub_region": "Cork", "lat": 51.9135, "lon": -8.1165, "type": "Single Pot Still", "founded": 1903, "color": "#4caf50"},
    {"name": "Teeling", "country": "Ireland", "sub_region": "Dublin", "lat": 53.3378, "lon": -6.2780, "type": "Small Batch", "founded": 2015, "color": "#4caf50"},
    # Kentucky Bourbon Trail
    {"name": "Maker's Mark", "country": "USA", "sub_region": "Kentucky", "lat": 37.8240, "lon": -85.3370, "type": "Bourbon", "founded": 1953, "color": "#ff5722"},
    {"name": "Woodford Reserve", "country": "USA", "sub_region": "Kentucky", "lat": 38.0640, "lon": -84.7400, "type": "Bourbon", "founded": 1812, "color": "#ff5722"},
    {"name": "Buffalo Trace", "country": "USA", "sub_region": "Kentucky", "lat": 38.2100, "lon": -84.8740, "type": "Bourbon", "founded": 1773, "color": "#ff5722"},
    {"name": "Wild Turkey", "country": "USA", "sub_region": "Kentucky", "lat": 38.0440, "lon": -84.8260, "type": "Bourbon", "founded": 1940, "color": "#ff5722"},
    {"name": "Jim Beam (Clermont)", "country": "USA", "sub_region": "Kentucky", "lat": 37.8340, "lon": -85.6220, "type": "Bourbon", "founded": 1795, "color": "#ff5722"},
    {"name": "Four Roses", "country": "USA", "sub_region": "Kentucky", "lat": 37.9800, "lon": -85.0390, "type": "Bourbon", "founded": 1888, "color": "#ff5722"},
    # Japan
    {"name": "Yamazaki", "country": "Japan", "sub_region": "Osaka", "lat": 34.8870, "lon": 135.6780, "type": "Single Malt", "founded": 1923, "color": "#e91e63"},
    {"name": "Hakushu", "country": "Japan", "sub_region": "Yamanashi", "lat": 35.8200, "lon": 138.3100, "type": "Single Malt", "founded": 1973, "color": "#e91e63"},
    {"name": "Nikka Yoichi", "country": "Japan", "sub_region": "Hokkaido", "lat": 43.1900, "lon": 140.7800, "type": "Single Malt", "founded": 1934, "color": "#e91e63"},
    {"name": "Nikka Miyagikyo", "country": "Japan", "sub_region": "Miyagi", "lat": 38.2800, "lon": 140.6800, "type": "Single Malt", "founded": 1969, "color": "#e91e63"},
    # Taiwan
    {"name": "Kavalan", "country": "Taiwan", "sub_region": "Yilan", "lat": 24.7560, "lon": 121.7520, "type": "Single Malt", "founded": 2005, "color": "#9c27b0"},
]

# ═══════════════════════════════════════════════════════════════
# 5. CHAMPAGNE & SPARKLING  (curated)
# ═══════════════════════════════════════════════════════════════
SPARKLING_REGIONS = [
    {"name": "Champagne", "country": "France", "lat": 49.0469, "lon": 3.9553, "method": "Traditional (Methode Champenoise)", "grapes": "Chardonnay, Pinot Noir, Pinot Meunier", "notes": "The original sparkling; only true Champagne comes from here", "area_ha": 34000, "color": "#ffd700"},
    {"name": "Prosecco (Valdobbiadene)", "country": "Italy", "lat": 45.8998, "lon": 11.9938, "method": "Charmat (tank method)", "grapes": "Glera", "notes": "Light, fruity, affordable Italian sparkling", "area_ha": 24000, "color": "#7cfc00"},
    {"name": "Cava (Penedes)", "country": "Spain", "lat": 41.3472, "lon": 1.6889, "method": "Traditional", "grapes": "Macabeo, Parellada, Xarello", "notes": "Spanish sparkling with Champagne method at fraction of price", "area_ha": 33000, "color": "#ff9800"},
    {"name": "Franciacorta", "country": "Italy", "lat": 45.6000, "lon": 10.0000, "method": "Traditional (Metodo Classico)", "grapes": "Chardonnay, Pinot Nero, Pinot Bianco", "notes": "Italy's premium Champagne-method sparkling", "area_ha": 3000, "color": "#e91e63"},
    {"name": "Cremant d'Alsace", "country": "France", "lat": 48.1660, "lon": 7.3060, "method": "Traditional", "grapes": "Pinot Blanc, Riesling, Pinot Gris", "notes": "Alsatian sparkling with elegant floral character", "area_ha": 3700, "color": "#ab47bc"},
    {"name": "Cremant de Bourgogne", "country": "France", "lat": 46.8000, "lon": 4.7000, "method": "Traditional", "grapes": "Chardonnay, Pinot Noir", "notes": "Burgundy sparkling, excellent value", "area_ha": 2700, "color": "#7b1fa2"},
    {"name": "Cremant de Loire", "country": "France", "lat": 47.2167, "lon": -0.0833, "method": "Traditional", "grapes": "Chenin Blanc, Chardonnay, Cabernet Franc", "notes": "Loire Valley sparkling, Chenin Blanc freshness", "area_ha": 2300, "color": "#4a148c"},
    {"name": "Sekt (Rheingau)", "country": "Germany", "lat": 50.0167, "lon": 8.0500, "method": "Traditional & Charmat", "grapes": "Riesling", "notes": "German Riesling sparkling, dry to sweet", "area_ha": 1500, "color": "#00bcd4"},
    {"name": "English Sparkling (Sussex)", "country": "England", "lat": 50.9000, "lon": -0.2500, "method": "Traditional", "grapes": "Chardonnay, Pinot Noir, Pinot Meunier", "notes": "Rising star; chalk soils similar to Champagne", "area_ha": 1800, "color": "#3f51b5"},
    {"name": "Cap Classique (Stellenbosch)", "country": "South Africa", "lat": -33.9368, "lon": 18.8602, "method": "Traditional (Methode Cap Classique)", "grapes": "Chardonnay, Pinot Noir", "notes": "South African traditional-method sparkling", "area_ha": 900, "color": "#ff5722"},
    {"name": "Trento DOC", "country": "Italy", "lat": 46.0667, "lon": 11.1167, "method": "Traditional (Metodo Classico)", "grapes": "Chardonnay, Pinot Nero", "notes": "Alpine sparkling from Trentino, high altitude freshness", "area_ha": 1100, "color": "#009688"},
    {"name": "Tasmania Sparkling", "country": "Australia", "lat": -41.4332, "lon": 147.1441, "method": "Traditional", "grapes": "Chardonnay, Pinot Noir", "notes": "Cool-climate Australian sparkling, world-class quality", "area_ha": 2000, "color": "#ff9800"},
]

# ═══════════════════════════════════════════════════════════════
# 6. WINE CLASSIFICATION SYSTEMS  (curated)
# ═══════════════════════════════════════════════════════════════
CLASSIFICATION_SYSTEMS = [
    {"country": "France", "system": "AOC / AOP", "full_name": "Appellation d'Origine Controlee / Protegee", "tiers": "AOP > IGP > Vin de France", "description": "Strictest system: controls grapes, yields, winemaking. Model for EU.", "example": "Bordeaux AOC, Champagne AOC, Burgundy 1er Cru", "lat": 46.2276, "lon": 2.2137, "color": "#2196f3"},
    {"country": "Italy", "system": "DOC / DOCG", "full_name": "Denominazione di Origine Controllata e Garantita", "tiers": "DOCG > DOC > IGT > Vino", "description": "DOCG is highest: tasted by government panel, numbered labels.", "example": "Barolo DOCG, Chianti Classico DOCG, Prosecco DOC", "lat": 41.8719, "lon": 12.5674, "color": "#4caf50"},
    {"country": "Spain", "system": "DO / DOCa", "full_name": "Denominacion de Origen Calificada", "tiers": "DOCa/DOQ > DO > Vino de Pago > VdlT > Vino", "description": "DOCa is highest (only Rioja & Priorat). Age terms: Joven, Crianza, Reserva, Gran Reserva.", "example": "Rioja DOCa, Ribera del Duero DO", "lat": 40.4168, "lon": -3.7038, "color": "#ff9800"},
    {"country": "Portugal", "system": "DOC / DOP", "full_name": "Denominacao de Origem Controlada", "tiers": "DOC > IPR > Vinho Regional > Vinho", "description": "Port and Douro wines are flagships; Vinho Verde, Dao also DOC.", "example": "Douro DOC, Porto DOC, Alentejo DOC", "lat": 39.3999, "lon": -8.2245, "color": "#9c27b0"},
    {"country": "Germany", "system": "Pradikatswein", "full_name": "Qualitatswein mit Pradikat", "tiers": "Trockenbeerenauslese > Eiswein > Beerenauslese > Auslese > Spatlese > Kabinett", "description": "Classification by grape ripeness (sugar at harvest). VDP adds site hierarchy: Grosse Lage (Grand Cru).", "example": "Mosel Riesling Spatlese, Rheingau Grosses Gewachs", "lat": 51.1657, "lon": 10.4515, "color": "#00bcd4"},
    {"country": "USA", "system": "AVA", "full_name": "American Viticultural Area", "tiers": "AVA (geographic only, no quality tiers)", "description": "Only defines geography, not grape or style. 85% of grapes must come from named AVA.", "example": "Napa Valley AVA, Willamette Valley AVA", "lat": 37.0902, "lon": -95.7129, "color": "#f44336"},
    {"country": "Austria", "system": "DAC", "full_name": "Districtus Austriae Controllatus", "tiers": "DAC Reserve > DAC > Qualitatswein > Landwein > Wein", "description": "Modern system linking region to grape: Kamptal DAC = Gruner Veltliner/Riesling.", "example": "Wachau DAC, Kamptal DAC", "lat": 47.5162, "lon": 14.5501, "color": "#795548"},
    {"country": "South Africa", "system": "WO", "full_name": "Wine of Origin", "tiers": "Single Vineyard > Ward > District > Region", "description": "Geographic hierarchy from broad regions to single vineyards.", "example": "Stellenbosch WO, Swartland WO", "lat": -30.5595, "lon": 22.9375, "color": "#607d8b"},
    {"country": "Australia", "system": "GI", "full_name": "Geographical Indication", "tiers": "GI zones > regions > sub-regions", "description": "Simple geographic system. Langton's Classification is the unofficial quality ranking.", "example": "Barossa Valley GI, Margaret River GI", "lat": -25.2744, "lon": 133.7751, "color": "#ff5722"},
    {"country": "Hungary", "system": "OEM / DHC", "full_name": "Oltalom alatt allo Eredetmegjeloles", "tiers": "DHC > OEM > OFJ > Bor", "description": "Tokaj has own 6-tier classification based on vineyard quality.", "example": "Tokaji Aszu 5 Puttonyos", "lat": 47.1625, "lon": 19.5033, "color": "#ffc107"},
]

# ═══════════════════════════════════════════════════════════════
# 7. HISTORIC WINE ROUTES  (curated)
# ═══════════════════════════════════════════════════════════════
HISTORIC_ROUTES = [
    {"name": "Areni-1 Cave (oldest winery)", "era": "4100 BC", "lat": 39.7310, "lon": 45.0839, "description": "World's oldest known winery. Wine press, fermentation vats, and grape seeds found in Armenian cave.", "country": "Armenia", "color": "#f44336"},
    {"name": "Hajji Firuz Tepe", "era": "5400 BC", "lat": 36.9667, "lon": 45.4667, "description": "Oldest chemical evidence of grape wine found in Neolithic pottery jars.", "country": "Iran", "color": "#e91e63"},
    {"name": "Kakheti Qvevri Tradition", "era": "6000 BC", "lat": 41.8333, "lon": 45.5000, "description": "Georgia's 8000-year winemaking tradition. Qvevri (clay vessels) are UNESCO Intangible Heritage.", "country": "Georgia", "color": "#ff9800"},
    {"name": "Ancient Egyptian Vineyards", "era": "3000 BC", "lat": 31.2001, "lon": 29.9187, "description": "Pharaonic wine production in Nile Delta. Wine jars found in tombs with vintage labels.", "country": "Egypt", "color": "#ffc107"},
    {"name": "Phoenician Wine Trade", "era": "1200 BC", "lat": 33.8938, "lon": 35.5018, "description": "Phoenicians spread viticulture across Mediterranean: Carthage, Sicily, Iberia, Marseille.", "country": "Lebanon", "color": "#ff5722"},
    {"name": "Greek Symposium Wines", "era": "800 BC", "lat": 37.9715, "lon": 23.7267, "description": "Greeks perfected wine culture. Planted vineyards in colonies across Southern Italy, Sicily, Provence.", "country": "Greece", "color": "#2196f3"},
    {"name": "Roman Falernian (Campania)", "era": "200 BC", "lat": 41.1667, "lon": 14.0000, "description": "Rome's most prized wine. Ager Falernus region produced vintages aged 20+ years.", "country": "Italy", "color": "#9c27b0"},
    {"name": "Roman Vineyards at Pompeii", "era": "79 AD", "lat": 40.7509, "lon": 14.4869, "description": "Preserved vineyards under Vesuvius ash. Replanted using ancient root patterns visible in excavations.", "country": "Italy", "color": "#673ab7"},
    {"name": "Roman Mosel Vineyards", "era": "100 AD", "lat": 49.7339, "lon": 6.6843, "description": "Romans planted Riesling precursors on steep Mosel slopes. Neumagener Weinschiff relief shows Roman wine transport.", "country": "Germany", "color": "#4caf50"},
    {"name": "Silk Road Wine (Turpan)", "era": "200 BC", "lat": 42.9476, "lon": 89.1896, "description": "Viticulture spread along Silk Road. Grape Valley near Turpan has continuous 2000-year grape cultivation.", "country": "China", "color": "#f44336"},
    {"name": "Medieval Cistercian Vineyards", "era": "1100 AD", "lat": 47.0744, "lon": 4.7286, "description": "Cistercian monks mapped Burgundy's terroir, creating the cru system. Clos de Vougeot founded 1110.", "country": "France", "color": "#795548"},
    {"name": "Champagne Dom Perignon", "era": "1668 AD", "lat": 49.0794, "lon": 3.9511, "description": "Benedictine monk Dom Perignon refined blending and sparkling wine techniques at Hautvillers Abbey.", "country": "France", "color": "#ffd700"},
    {"name": "Tokaj Aszu Classification", "era": "1730 AD", "lat": 48.1183, "lon": 21.4000, "description": "World's first official wine classification system. Royal decree classified Tokaj vineyards in 1730.", "country": "Hungary", "color": "#ffc107"},
    {"name": "Port Wine Trade (Douro)", "era": "1756 AD", "lat": 41.1579, "lon": -7.7227, "description": "Marquis of Pombal created world's first wine appellation system. Demarcated Douro region.", "country": "Portugal", "color": "#722f37"},
    {"name": "1855 Bordeaux Classification", "era": "1855 AD", "lat": 44.8378, "lon": -0.5792, "description": "Napoleon III ordered classification for Paris Exhibition. 5 tiers of chateaux, still used today.", "country": "France", "color": "#8b0000"},
    {"name": "Phylloxera Crisis", "era": "1863 AD", "lat": 44.0500, "lon": 4.3600, "description": "Phylloxera aphid destroyed European vineyards. American rootstock grafting saved the industry.", "country": "France", "color": "#424242"},
    {"name": "Mission Grapes (California)", "era": "1769 AD", "lat": 32.7502, "lon": -117.1952, "description": "Spanish missionaries planted first California vineyards. Fra Junipero Serra at Mission San Diego.", "country": "USA", "color": "#ff5722"},
    {"name": "1976 Judgment of Paris", "era": "1976 AD", "lat": 38.5025, "lon": -122.2654, "description": "Napa wines beat top Bordeaux in blind tasting. Stag's Leap Cabernet and Chateau Montelena Chardonnay won.", "country": "USA", "color": "#f44336"},
]

# ═══════════════════════════════════════════════════════════════
# 8. BEER CULTURE  (curated)
# ═══════════════════════════════════════════════════════════════
BEER_CULTURE = [
    # Belgian Abbey/Trappist
    {"name": "Westvleteren Brewery", "country": "Belgium", "sub_type": "Trappist Abbey", "lat": 50.8858, "lon": 2.7224, "specialty": "Westvleteren 12 — world's most exclusive Trappist ale", "color": "#795548"},
    {"name": "Chimay (Scourmont Abbey)", "country": "Belgium", "sub_type": "Trappist Abbey", "lat": 49.9992, "lon": 4.3258, "specialty": "Chimay Blue, Red, White — classic Trappist range", "color": "#795548"},
    {"name": "Orval Abbey", "country": "Belgium", "sub_type": "Trappist Abbey", "lat": 49.6364, "lon": 5.3486, "specialty": "Orval — unique Brettanomyces character, dry-hopped", "color": "#795548"},
    {"name": "Rochefort (Notre-Dame)", "country": "Belgium", "sub_type": "Trappist Abbey", "lat": 50.1619, "lon": 5.2206, "specialty": "Rochefort 10 — rich, dark, complex quad", "color": "#795548"},
    {"name": "Cantillon Brewery (Brussels)", "country": "Belgium", "sub_type": "Lambic/Gueuze", "lat": 50.8428, "lon": 4.3333, "specialty": "Spontaneous fermentation lambic and gueuze, sour masterpieces", "color": "#ff9800"},
    {"name": "Drie Fonteinen (Beersel)", "country": "Belgium", "sub_type": "Lambic/Gueuze", "lat": 50.7647, "lon": 4.2936, "specialty": "Traditional gueuze blender, Oude Kriek", "color": "#ff9800"},
    # Germany
    {"name": "Hofbrauhaus Munich", "country": "Germany", "sub_type": "Beer Hall", "lat": 48.1375, "lon": 11.5797, "specialty": "Historic beer hall (1589). Hofbrau Original, Dunkel, Weissbier", "color": "#2196f3"},
    {"name": "Augustiner Brau", "country": "Germany", "sub_type": "Beer Hall", "lat": 48.1351, "lon": 11.5566, "specialty": "Munich's oldest brewery (1328). Helles, Edelstoff", "color": "#2196f3"},
    {"name": "Weihenstephan", "country": "Germany", "sub_type": "Bavarian Monastery", "lat": 48.3947, "lon": 11.7275, "specialty": "World's oldest brewery (1040). Hefeweissbier, Vitus", "color": "#4caf50"},
    {"name": "Bamberg Rauchbier District", "country": "Germany", "sub_type": "Franconian Smoked Beer", "lat": 49.8917, "lon": 10.8917, "specialty": "Aecht Schlenkerla Rauchbier, smoked malt tradition since 1405", "color": "#8d6e63"},
    {"name": "Koelsch Breweries (Cologne)", "country": "Germany", "sub_type": "Kolsch", "lat": 50.9375, "lon": 6.9603, "specialty": "Kolsch — protected appellation light ale, served in 200ml Stangen", "color": "#03a9f4"},
    # Czech Republic
    {"name": "Pilsner Urquell (Plzen)", "country": "Czech Republic", "sub_type": "Original Pilsner", "lat": 49.7472, "lon": 13.3864, "specialty": "Birthplace of pilsner (1842). Original golden lager.", "color": "#ffc107"},
    {"name": "Budvar (Ceske Budejovice)", "country": "Czech Republic", "sub_type": "Czech Lager", "lat": 48.9745, "lon": 14.4747, "specialty": "Original Budweiser. Czech premium lager since 1895.", "color": "#ffc107"},
    {"name": "U Fleku Prague", "country": "Czech Republic", "sub_type": "Historic Brewpub", "lat": 50.0794, "lon": 14.4178, "specialty": "Oldest brewpub (1499). Famous dark 13-degree lager.", "color": "#ffc107"},
    # UK
    {"name": "Fuller's Griffin Brewery", "country": "UK", "sub_type": "Real Ale", "lat": 51.4891, "lon": -0.2262, "specialty": "London Pride, ESB — iconic British cask ales", "color": "#f44336"},
    {"name": "Timothy Taylor (Keighley)", "country": "UK", "sub_type": "Real Ale", "lat": 53.8680, "lon": -1.9050, "specialty": "Landlord — multiple-award-winning best bitter", "color": "#f44336"},
    {"name": "Hook Norton Brewery", "country": "UK", "sub_type": "Victorian Tower Brewery", "lat": 52.0094, "lon": -1.4889, "specialty": "Hooky — gravity-fed Victorian tower brewery (1849)", "color": "#f44336"},
    # Others
    {"name": "Guinness Storehouse (Dublin)", "country": "Ireland", "sub_type": "Stout", "lat": 53.3418, "lon": -6.2868, "specialty": "World's most famous stout since 1759. Gravity bar with city views.", "color": "#212121"},
    {"name": "Anchor Brewing (San Francisco)", "country": "USA", "sub_type": "Craft Pioneer", "lat": 37.7649, "lon": -122.4000, "specialty": "Fritz Maytag revived craft beer (1965). Steam Beer, Liberty Ale", "color": "#ff5722"},
    {"name": "Stone Brewing (San Diego)", "country": "USA", "sub_type": "Craft IPA", "lat": 33.1159, "lon": -117.1183, "specialty": "Arrogant Bastard, Stone IPA — West Coast IPA pioneers", "color": "#ff5722"},
]

# ═══════════════════════════════════════════════════════════════
# 9. SPIRITS OF THE WORLD  (curated)
# ═══════════════════════════════════════════════════════════════
WORLD_SPIRITS = [
    # Tequila & Mezcal
    {"name": "Tequila — Jalisco Lowlands", "spirit": "Tequila", "lat": 20.8200, "lon": -103.3500, "country": "Mexico", "base": "Blue Weber Agave", "notes": "Lowland (El Valle) tequila: fruity, floral, lighter body", "color": "#4caf50"},
    {"name": "Tequila — Jalisco Highlands", "spirit": "Tequila", "lat": 20.9500, "lon": -102.3400, "country": "Mexico", "base": "Blue Weber Agave", "notes": "Highland (Los Altos) tequila: sweeter, more agave-forward", "color": "#66bb6a"},
    {"name": "Oaxaca Mezcal Region", "spirit": "Mezcal", "lat": 16.9000, "lon": -96.7200, "country": "Mexico", "base": "Various agave (espadin, tobala, madrecuixe)", "notes": "Traditional pit-roasted agave. Smoky, complex, artisanal.", "color": "#2e7d32"},
    # Rum
    {"name": "Barbados — Mount Gay", "spirit": "Rum", "lat": 13.1939, "lon": -59.5432, "country": "Barbados", "base": "Sugarcane molasses", "notes": "World's oldest rum distillery (1703). Aged, smooth style.", "color": "#ff9800"},
    {"name": "Jamaica — Appleton Estate", "spirit": "Rum", "lat": 18.2000, "lon": -77.7500, "country": "Jamaica", "base": "Sugarcane molasses", "notes": "High-ester funky Jamaican rum. Pot-still character.", "color": "#ffa726"},
    {"name": "Martinique — Rhum Agricole", "spirit": "Rhum Agricole", "lat": 14.6415, "lon": -61.0242, "country": "Martinique", "base": "Fresh sugarcane juice", "notes": "AOC-controlled rhum agricole from fresh cane juice; grassy, herbal.", "color": "#ffb74d"},
    {"name": "Cuba — Havana Club", "spirit": "Rum", "lat": 23.0514, "lon": -82.3457, "country": "Cuba", "base": "Sugarcane molasses", "notes": "Light, smooth Cuban rum. Column-still, aged in tropical heat.", "color": "#ef6c00"},
    {"name": "Guyana — Demerara (El Dorado)", "spirit": "Rum", "lat": 6.8013, "lon": -58.1553, "country": "Guyana", "base": "Demerara sugar", "notes": "Last wooden Coffey still. Rich, dark, caramel-forward rums.", "color": "#e65100"},
    # Sake
    {"name": "Fushimi (Kyoto) — Gekkeikan", "spirit": "Sake", "lat": 34.9333, "lon": 135.7667, "country": "Japan", "base": "Polished rice + koji", "notes": "Soft Fushimi water produces gentle, smooth sake. Historic district.", "color": "#e91e63"},
    {"name": "Nada (Kobe) — Hakutsuru", "spirit": "Sake", "lat": 34.7167, "lon": 135.2667, "country": "Japan", "base": "Polished rice + koji", "notes": "Miyamizu mineral water creates crisp, dry 'otoko-zake' (man's sake).", "color": "#f06292"},
    {"name": "Niigata — Kubota/Asahi Shuzo", "spirit": "Sake", "lat": 37.9167, "lon": 139.0333, "country": "Japan", "base": "Polished rice + koji", "notes": "Snow-country sake: clean, light, tanrei-karakuchi (dry/clean) style.", "color": "#ce93d8"},
    # Grappa
    {"name": "Veneto Grappa (Bassano del Grappa)", "spirit": "Grappa", "lat": 45.7667, "lon": 11.7333, "country": "Italy", "base": "Grape pomace", "notes": "Historic grappa capital. From pomace of Prosecco, Valpolicella grapes.", "color": "#7b1fa2"},
    {"name": "Trentino Grappa (Bertagnolli)", "spirit": "Grappa", "lat": 46.0667, "lon": 11.1167, "country": "Italy", "base": "Grape pomace", "notes": "Alpine grappa: smooth, aromatic, single-varietal distillation.", "color": "#9c27b0"},
    # Baijiu
    {"name": "Guizhou — Moutai", "spirit": "Baijiu", "lat": 27.8559, "lon": 106.3961, "country": "China", "base": "Sorghum", "notes": "China's national spirit. Sauce-aroma (jiang-xiang) baijiu, fermented in stone pits.", "color": "#f44336"},
    {"name": "Sichuan — Wuliangye (Yibin)", "spirit": "Baijiu", "lat": 28.7600, "lon": 104.6200, "country": "China", "base": "5 grains (sorghum, rice, wheat, corn, glutinous rice)", "notes": "Strong-aroma (nong-xiang) baijiu from 600-year-old fermentation pits.", "color": "#d32f2f"},
    # Cognac & Brandy
    {"name": "Cognac — Grande Champagne", "spirit": "Cognac", "lat": 45.6833, "lon": -0.3333, "country": "France", "base": "Ugni Blanc grapes", "notes": "Premier cru of Cognac. Chalky soils, finest eaux-de-vie, long aging potential.", "color": "#8d6e63"},
    {"name": "Armagnac — Bas-Armagnac", "spirit": "Armagnac", "lat": 43.8000, "lon": -0.1000, "country": "France", "base": "Ugni Blanc, Folle Blanche, Baco 22A", "notes": "Older than Cognac. Single-distillation, earthier, more rustic character.", "color": "#6d4c41"},
    # Others
    {"name": "Jalisco Raicilla", "spirit": "Raicilla", "lat": 20.5200, "lon": -105.0800, "country": "Mexico", "base": "Agave lechuguilla/maximiliana", "notes": "Pre-Hispanic agave spirit from Jalisco mountains. Recently protected DO.", "color": "#43a047"},
    {"name": "Pisco — Ica Valley", "spirit": "Pisco", "lat": -14.0755, "lon": -75.7342, "country": "Peru", "base": "Muscat, Quebranta grapes", "notes": "Single-distillation grape brandy. Must not be diluted or aged in wood.", "color": "#00897b"},
    {"name": "Pisco — Elqui Valley", "spirit": "Pisco", "lat": -30.0333, "lon": -70.5000, "country": "Chile", "base": "Muscat grapes", "notes": "Chilean pisco: may be aged in wood. Pisco Sour is national cocktail.", "color": "#009688"},
    {"name": "Aquavit — Aalborg", "spirit": "Aquavit", "lat": 57.0488, "lon": 9.9217, "country": "Denmark", "base": "Grain/potato, caraway", "notes": "Scandinavian caraway-spiced spirit. Tradition since 15th century.", "color": "#0288d1"},
    {"name": "Shochu — Kagoshima", "spirit": "Shochu", "lat": 31.5969, "lon": 130.5571, "country": "Japan", "base": "Sweet potato (imo)", "notes": "Japan's most popular spirit by volume. Imo-jochu from Satsuma sweet potato.", "color": "#ec407a"},
    {"name": "Slivovitz — Slavonia", "spirit": "Slivovitz", "lat": 45.5511, "lon": 18.6939, "country": "Croatia", "base": "Damson plums", "notes": "Plum brandy tradition across Balkans. Double-distilled, unaged to aged.", "color": "#5c6bc0"},
]

# ═══════════════════════════════════════════════════════════════
# 10. VINEYARD TERROIR  (curated)
# ═══════════════════════════════════════════════════════════════
TERROIR_DATA = [
    {"name": "Chablis — Kimmeridgian Limestone", "region": "Chablis, Burgundy", "lat": 47.8133, "lon": 3.8000, "soil": "Kimmeridgian limestone (ancient seabed with fossilized oyster shells)", "climate": "Continental, cold winters", "altitude_m": 150, "effect": "Steel-mineral Chardonnay with chalky acidity and saline finish", "color": "#e0e0e0"},
    {"name": "Mosel — Blue Devonian Slate", "region": "Mosel, Germany", "lat": 49.9150, "lon": 7.1050, "soil": "Blue/grey Devonian slate", "climate": "Cool continental, steep slopes (up to 65 degrees)", "altitude_m": 120, "effect": "Slate retains heat for ripening. Gives Riesling its petrol/mineral character", "color": "#607d8b"},
    {"name": "Barossa — Ancient Red Earth", "region": "Barossa Valley, Australia", "lat": -34.5611, "lon": 138.9500, "soil": "Red-brown earth over clay with ironstone gravel", "climate": "Mediterranean, warm/dry", "altitude_m": 280, "effect": "Low-vigor old vines concentrate Shiraz flavors. Rich, chocolatey wines", "color": "#bf360c"},
    {"name": "Priorat — Llicorella Schist", "region": "Priorat, Spain", "lat": 41.2000, "lon": 0.7500, "soil": "Llicorella — black slate and quartz schist", "climate": "Hot Mediterranean, low rainfall", "altitude_m": 400, "effect": "Extreme minerality. Vines dig deep for water, producing intensely concentrated wines", "color": "#37474f"},
    {"name": "Champagne — Chalk Bedrock", "region": "Champagne, France", "lat": 49.0469, "lon": 3.9553, "soil": "Cretaceous chalk (belemnite chalk)", "climate": "Cool oceanic/continental", "altitude_m": 150, "effect": "Chalk provides drainage, retains heat, gives Champagne its signature acidity and mineral finesse", "color": "#fafafa"},
    {"name": "Napa Valley — Alluvial Benchland", "region": "Napa Valley, California", "lat": 38.5025, "lon": -122.2654, "soil": "Alluvial gravel, volcanic ash, clay loam", "climate": "Mediterranean, warm days, cool nights (fog influence)", "altitude_m": 60, "effect": "Well-drained gravel benches produce structured, age-worthy Cabernet Sauvignon", "color": "#8d6e63"},
    {"name": "Burgundy Cote d'Or — Marl and Limestone", "region": "Cote d'Or, Burgundy", "lat": 47.0250, "lon": 4.8400, "soil": "Jurassic limestone, marl (clay-limestone mix)", "climate": "Continental, marginal for ripening", "altitude_m": 280, "effect": "Slight soil variations = dramatic wine differences. Basis of Grand Cru/Premier Cru system", "color": "#bcaaa4"},
    {"name": "Santorini — Volcanic Pumice", "region": "Santorini, Greece", "lat": 36.3932, "lon": 25.4615, "soil": "Volcanic pumice,ite, ash over basalt", "climate": "Hot Mediterranean, sea wind, zero rainfall", "altitude_m": 200, "effect": "Bush-trained Assyrtiko (kouloura). Pumice retains night moisture. Extreme minerality and salinity", "color": "#455a64"},
    {"name": "Douro Valley — Schist Terraces", "region": "Douro, Portugal", "lat": 41.1579, "lon": -7.7227, "soil": "Schist rock with thin topsoil on terraced slopes", "climate": "Continental, extreme heat in summer", "altitude_m": 500, "effect": "Schist fractures allow deep root penetration. Heat-retention produces concentrated Port grapes", "color": "#4e342e"},
    {"name": "Mendoza — High-Altitude Alluvial", "region": "Uco Valley, Mendoza", "lat": -33.5500, "lon": -69.2500, "soil": "Alluvial sand, gravel, calcareous deposits from Andes", "climate": "Continental, dry, extreme diurnal range (20C+)", "altitude_m": 1200, "effect": "Altitude preserves acidity and color. UV intensity deepens Malbec's purple hue and tannin structure", "color": "#6a1b9a"},
    {"name": "Willamette Valley — Jory Volcanic", "region": "Willamette Valley, Oregon", "lat": 45.0000, "lon": -123.0000, "soil": "Jory (volcanic basalt) and Willakenzie (marine sedimentary)", "climate": "Cool maritime, long growing season", "altitude_m": 200, "effect": "Volcanic Jory = spicier, darker Pinot Noir. Marine Willakenzie = more floral, lighter", "color": "#d32f2f"},
    {"name": "Etna — Volcanic Lava and Ash", "region": "Mount Etna, Sicily", "lat": 37.7510, "lon": 14.9934, "soil": "Volcanic lava rock, pumice, ash at various elevations", "climate": "Mediterranean modified by altitude and wind", "altitude_m": 800, "effect": "High altitude + volcanic soil = elegant, mineral Nerello Mascalese with Burgundy-like transparency", "color": "#424242"},
    {"name": "Wachau — Gneiss and Loess", "region": "Wachau, Austria", "lat": 48.3667, "lon": 15.4167, "soil": "Primary rock (gneiss, granite) with loess terraces", "climate": "Pannonian/continental blend", "altitude_m": 350, "effect": "Gneiss terraces = powerful Riesling. Loess = rounder Gruner Veltliner. UNESCO landscape", "color": "#78909c"},
    {"name": "Tokaj — Volcanic Zeolite Clay", "region": "Tokaj, Hungary", "lat": 48.1183, "lon": 21.4000, "soil": "Volcanic rhyolite, zeolite-rich clay over loess", "climate": "Continental with autumn botrytis fogs", "altitude_m": 200, "effect": "Zeolite clay retains water for botrytis development. Furmint develops unctuous Aszu character", "color": "#f9a825"},
]


# ═══════════════════════════════════════════════════════════════
# OVERPASS API HELPERS
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _overpass_search(lat: float, lon: float, radius_km: float,
                     craft_types: list[str]) -> list[dict]:
    """
    Query Overpass API for craft breweries/wineries/distilleries
    or vineyard landuse near a point.
    Returns list of dicts with name, lat, lon, craft, etc.
    """
    radius_m = int(radius_km * 1000)
    queries = []
    for ct in craft_types:
        if ct == "vineyard":
            queries.append(f'way["landuse"="vineyard"](around:{radius_m},{lat},{lon});')
            queries.append(f'relation["landuse"="vineyard"](around:{radius_m},{lat},{lon});')
        else:
            queries.append(f'node["craft"="{ct}"](around:{radius_m},{lat},{lon});')
            queries.append(f'way["craft"="{ct}"](around:{radius_m},{lat},{lon});')

    all_q = "\n  ".join(queries)
    query = f"""
[out:json][timeout:60];
(
  {all_q}
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []

    elements = result.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        elat, elon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            elat, elon = el["lat"], el["lon"]
        elif el.get("type") in ("way", "relation"):
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1])
                      for n in nodes if n in node_lookup]
            if coords:
                elat = sum(c[0] for c in coords) / len(coords)
                elon = sum(c[1] for c in coords) / len(coords)

        if elat is None or elon is None:
            continue

        craft = tags.get("craft", tags.get("landuse", "unknown"))
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        features.append({
            "name": name,
            "craft": craft,
            "lat": elat,
            "lon": elon,
            "website": tags.get("website", tags.get("contact:website", "")),
            "addr": tags.get("addr:city", tags.get("addr:street", "")),
            "cuisine": tags.get("cuisine", ""),
            "osm_id": el.get("id"),
        })

    return features


# ═══════════════════════════════════════════════════════════════
# MAP BUILDER HELPERS
# ═══════════════════════════════════════════════════════════════
def _make_dark_map(center: list, zoom: int = 4) -> folium.Map:
    """Create a folium map with CartoDB dark_matter tiles."""
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)
    return m


def _render_folium(m: folium.Map, height: int = 500):
    """Render a folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _csv_download(df: pd.DataFrame, filename: str, label: str, key: str):
    """Render a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename,
                       mime="text/csv", key=key)


def _dark_chart_style(fig, ax):
    """Apply dark theme to matplotlib figure/axes."""
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)
    ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.grid(True, axis="x", color=BORDER, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)


# ═══════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_world_wine_regions():
    """Mode 1: World Wine Regions."""
    st.markdown("#### World Wine Regions")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Major wine-producing regions across the globe &mdash; '
        f'from Bordeaux to Barossa, Napa to Ningxia. Click any marker for details.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    countries = sorted(set(r["country"] for r in WINE_REGIONS))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_countries = st.multiselect("Filter by Country", countries,
                                       default=countries, key="wr_countries")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Country", "Area (ha)"], key="wr_sort")

    filtered = [r for r in WINE_REGIONS if r["country"] in sel_countries]

    if sort_by == "Area (ha)":
        filtered.sort(key=lambda x: x["area_ha"], reverse=True)
    elif sort_by == "Country":
        filtered.sort(key=lambda x: (x["country"], x["name"]))
    else:
        filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Regions Shown", len(filtered))
    c2.metric("Countries", len(set(r["country"] for r in filtered)))
    total_ha = sum(r["area_ha"] for r in filtered)
    c3.metric("Total Vineyard Area", f"{total_ha:,} ha")

    # Map
    m = _make_dark_map([30, 0], zoom=2)
    for r in filtered:
        popup = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(r["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(r["country"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Grapes:</b> {escape(r["grapes"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Style:</b> {escape(r["style"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Area:</b> {r["area_ha"]:,} ha</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(4, min(12, r["area_ha"] / 15000)),
            color=r["color"], fill=True, fill_color=r["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=240),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Region": r["name"], "Country": r["country"],
        "Key Grapes": r["grapes"], "Wine Style": r["style"],
        "Area (ha)": r["area_ha"], "Lat": r["lat"], "Lon": r["lon"],
    } for r in filtered])

    with st.expander(f"Full Data Table ({len(df)} regions)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "wine_regions.csv",
                  f"Download {len(df)} Wine Regions (CSV)", "wr_dl")


def _render_grape_varieties():
    """Mode 2: Grape Varieties."""
    st.markdown("#### Grape Varieties of the World")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Where the world\'s great grape varieties originate and thrive. '
        f'Red and white grapes mapped to their key regions.</p>',
        unsafe_allow_html=True,
    )

    grape_type = st.radio("Grape Type", ["All", "Red", "White"],
                          horizontal=True, key="gv_type")
    filtered = GRAPE_VARIETIES if grape_type == "All" else \
        [g for g in GRAPE_VARIETIES if g["type"] == grape_type]

    c1, c2, c3 = st.columns(3)
    c1.metric("Varieties", len(filtered))
    c2.metric("Red", len([g for g in filtered if g["type"] == "Red"]))
    c3.metric("White", len([g for g in filtered if g["type"] == "White"]))

    m = _make_dark_map([30, 0], zoom=2)
    for g in filtered:
        popup = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(g["grape"])}</strong> '
            f'<span style="font-size:0.8rem;">({escape(g["type"])})</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Origin:</b> {escape(g["origin"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Regions:</b> {escape(g["regions"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Flavor:</b> {escape(g["flavor"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=7,
            color=g["color"], fill=True, fill_color=g["color"],
            fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=240),
        ).add_to(m)

    _render_folium(m)

    df = pd.DataFrame([{
        "Grape": g["grape"], "Type": g["type"], "Origin": g["origin"],
        "Key Regions": g["regions"], "Flavor Profile": g["flavor"],
        "Lat": g["lat"], "Lon": g["lon"],
    } for g in filtered])

    with st.expander(f"Full Data Table ({len(df)} varieties)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "grape_varieties.csv",
                  f"Download {len(df)} Grape Varieties (CSV)", "gv_dl")


def _render_craft_breweries():
    """Mode 3: Craft Breweries (Overpass API)."""
    st.markdown("#### Craft Breweries")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Search for craft breweries near any location '
        f'using OpenStreetMap data via Overpass API.</p>',
        unsafe_allow_html=True,
    )

    presets = {
        "Custom": None,
        "Portland, Oregon": (45.5152, -122.6784),
        "Brussels, Belgium": (50.8503, 4.3517),
        "Munich, Germany": (48.1351, 11.5820),
        "London, UK": (51.5074, -0.1278),
        "San Diego, USA": (32.7157, -117.1611),
        "Denver, Colorado": (39.7392, -104.9903),
        "Prague, Czech Republic": (50.0755, 14.4378),
        "Melbourne, Australia": (-37.8136, 144.9631),
        "Asheville, NC": (35.5951, -82.5515),
        "Amsterdam, Netherlands": (52.3676, 4.9041),
    }

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        preset = st.selectbox("Quick Locations", list(presets.keys()), key="cb_preset")
    default_lat = presets[preset][0] if presets[preset] else 50.85
    default_lon = presets[preset][1] if presets[preset] else 4.35
    with col2:
        lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="cb_lat")
    with col3:
        lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="cb_lon")

    radius = st.slider("Search Radius (km)", 1, 50, 15, key="cb_radius")

    if st.button("Search Breweries", key="cb_search", width="stretch"):
        st.session_state.cb_params = {"lat": lat, "lon": lon, "radius": radius}

    if "cb_params" not in st.session_state:
        st.info("Select a location and click Search to find craft breweries nearby.")
        return

    p = st.session_state.cb_params
    with st.spinner("Querying OpenStreetMap for breweries..."):
        results = _overpass_search(p["lat"], p["lon"], p["radius"], ["brewery"])

    if not results:
        st.warning("No breweries found. Try a larger radius or different location.")
        return

    c1, c2 = st.columns(2)
    c1.metric("Breweries Found", len(results))
    named = [r for r in results if r["name"] != "Unnamed"]
    c2.metric("Named Breweries", len(named))

    m = _make_dark_map([p["lat"], p["lon"]], zoom=11)
    folium.Circle(
        location=[p["lat"], p["lon"]],
        radius=p["radius"] * 1000,
        color=ACCENT, fill=True, fill_opacity=0.05, weight=1,
    ).add_to(m)

    for r in results:
        popup = (
            f'<div style="max-width:200px;">'
            f'<strong>{escape(r["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">Brewery</span>'
        )
        if r["website"]:
            popup += f'<br/><a href="{escape(r["website"])}" target="_blank" style="font-size:0.75rem;">Website</a>'
        if r["addr"]:
            popup += f'<br/><span style="font-size:0.75rem;">{escape(r["addr"])}</span>'
        popup += '</div>'

        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=6, color="#ff9800", fill=True,
            fill_color="#ff9800", fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=220),
        ).add_to(m)

    _render_folium(m)

    df = pd.DataFrame([{
        "Name": r["name"], "Lat": round(r["lat"], 5),
        "Lon": round(r["lon"], 5), "Website": r["website"],
        "Address": r["addr"], "OSM ID": r["osm_id"],
    } for r in results])

    with st.expander(f"Full Data Table ({len(df)} breweries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "craft_breweries.csv",
                  f"Download {len(df)} Breweries (CSV)", "cb_dl")


def _render_whisky_distilleries():
    """Mode 4: Whisky Distilleries."""
    st.markdown("#### Whisky & Bourbon Distilleries")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Legendary whisky trails: Scotland\'s Speyside and Islay, '
        f'Ireland, Kentucky Bourbon Trail, Japanese whisky, and Kavalan in Taiwan.</p>',
        unsafe_allow_html=True,
    )

    countries = sorted(set(w["country"] for w in WHISKY_TRAILS))
    sel_countries = st.multiselect("Filter by Country", countries,
                                   default=countries, key="wd_countries")
    filtered = [w for w in WHISKY_TRAILS if w["country"] in sel_countries]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distilleries", len(filtered))
    c2.metric("Countries", len(set(w["country"] for w in filtered)))
    oldest = min(filtered, key=lambda x: x["founded"]) if filtered else None
    c3.metric("Oldest Founded", oldest["founded"] if oldest else "N/A")
    c4.metric("Sub-regions", len(set(w["sub_region"] for w in filtered)))

    # Center map based on selection
    if filtered:
        avg_lat = sum(w["lat"] for w in filtered) / len(filtered)
        avg_lon = sum(w["lon"] for w in filtered) / len(filtered)
        zoom = 5 if len(sel_countries) == 1 else 2
    else:
        avg_lat, avg_lon, zoom = 50.0, 0.0, 2

    m = _make_dark_map([avg_lat, avg_lon], zoom=zoom)
    for w in filtered:
        popup = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(w["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(w["country"])} &mdash; {escape(w["sub_region"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Type:</b> {escape(w["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Founded:</b> {w["founded"]}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=7, color=w["color"], fill=True,
            fill_color=w["color"], fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=240),
        ).add_to(m)

    _render_folium(m)

    df = pd.DataFrame([{
        "Distillery": w["name"], "Country": w["country"],
        "Sub-region": w["sub_region"], "Type": w["type"],
        "Founded": w["founded"], "Lat": w["lat"], "Lon": w["lon"],
    } for w in filtered])

    with st.expander(f"Full Data Table ({len(df)} distilleries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "whisky_distilleries.csv",
                  f"Download {len(df)} Distilleries (CSV)", "wd_dl")


def _render_champagne_sparkling():
    """Mode 5: Champagne & Sparkling Wine."""
    st.markdown("#### Champagne & Sparkling Wine Regions")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From Champagne to Prosecco, Cava to Cap Classique &mdash; '
        f'the world\'s great sparkling wine regions and their methods.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Sparkling Regions", len(SPARKLING_REGIONS))
    trad = len([s for s in SPARKLING_REGIONS if "Traditional" in s["method"]])
    c2.metric("Traditional Method", trad)
    total_ha = sum(s["area_ha"] for s in SPARKLING_REGIONS)
    c3.metric("Total Area", f"{total_ha:,} ha")

    m = _make_dark_map([45, 5], zoom=3)
    for s in SPARKLING_REGIONS:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{escape(s["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(s["country"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Method:</b> {escape(s["method"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Grapes:</b> {escape(s["grapes"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{escape(s["notes"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Area:</b> {s["area_ha"]:,} ha</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=max(5, min(12, s["area_ha"] / 4000)),
            color=s["color"], fill=True, fill_color=s["color"],
            fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    df = pd.DataFrame([{
        "Region": s["name"], "Country": s["country"],
        "Method": s["method"], "Grapes": s["grapes"],
        "Notes": s["notes"], "Area (ha)": s["area_ha"],
        "Lat": s["lat"], "Lon": s["lon"],
    } for s in SPARKLING_REGIONS])

    with st.expander(f"Full Data Table ({len(df)} regions)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "sparkling_wine_regions.csv",
                  f"Download {len(df)} Sparkling Regions (CSV)", "cs_dl")


def _render_wine_classification():
    """Mode 6: Wine Classification Systems."""
    st.markdown("#### Wine Classification & Appellation Systems")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">AOC, DOC, DOCG, AVA, Pradikatswein &mdash; '
        f'how countries classify and protect their wine quality and origin.</p>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    c1.metric("Classification Systems", len(CLASSIFICATION_SYSTEMS))
    c2.metric("Countries Covered", len(set(c["country"] for c in CLASSIFICATION_SYSTEMS)))

    m = _make_dark_map([35, 10], zoom=2)
    for c in CLASSIFICATION_SYSTEMS:
        popup = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(c["country"])} &mdash; {escape(c["system"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(c["full_name"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Tiers:</b> {escape(c["tiers"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{escape(c["description"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Example:</b> {escape(c["example"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=10, color=c["color"], fill=True,
            fill_color=c["color"], fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Detailed cards
    for c in CLASSIFICATION_SYSTEMS:
        st.markdown(
            f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:8px;'
            f'padding:12px;margin-bottom:8px;">'
            f'<span style="color:{c["color"]};font-weight:700;font-size:1rem;">'
            f'{escape(c["country"])}</span> '
            f'<span style="color:{TEXT_PRIMARY};font-weight:600;"> &mdash; {escape(c["system"])}</span>'
            f'<div style="color:{TEXT_MUTED};font-size:0.8rem;font-style:italic;">{escape(c["full_name"])}</div>'
            f'<div style="color:{TEXT_SECONDARY};font-size:0.85rem;margin-top:4px;">'
            f'<b>Tiers:</b> {escape(c["tiers"])}</div>'
            f'<div style="color:{TEXT_SECONDARY};font-size:0.85rem;">{escape(c["description"])}</div>'
            f'<div style="color:{TEXT_MUTED};font-size:0.8rem;"><b>Example:</b> {escape(c["example"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    df = pd.DataFrame([{
        "Country": c["country"], "System": c["system"],
        "Full Name": c["full_name"], "Quality Tiers": c["tiers"],
        "Description": c["description"], "Example": c["example"],
    } for c in CLASSIFICATION_SYSTEMS])

    _csv_download(df, "wine_classification.csv",
                  f"Download {len(df)} Classification Systems (CSV)", "wc_dl")


def _render_historic_wine_routes():
    """Mode 7: Historic Wine Routes."""
    st.markdown("#### Historic Wine Routes & Milestones")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From 6000 BC Georgian qvevri to the 1976 Judgment of Paris '
        f'&mdash; the pivotal places and moments in wine history.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Historic Sites", len(HISTORIC_ROUTES))
    c2.metric("Countries", len(set(h["country"] for h in HISTORIC_ROUTES)))
    c3.metric("Time Span", "6000 BC to 1976 AD")

    m = _make_dark_map([35, 20], zoom=3)
    for h in HISTORIC_ROUTES:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{escape(h["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#888;">{escape(h["era"])} &mdash; {escape(h["country"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{escape(h["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[h["lat"], h["lon"]],
            radius=8, color=h["color"], fill=True,
            fill_color=h["color"], fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Timeline cards
    st.markdown("---")
    st.markdown("#### Wine History Timeline")
    for h in HISTORIC_ROUTES:
        st.markdown(
            f'<div style="display:flex;align-items:flex-start;margin-bottom:8px;">'
            f'<div style="min-width:90px;color:{h["color"]};font-weight:700;font-size:0.9rem;">'
            f'{escape(h["era"])}</div>'
            f'<div style="width:10px;height:40px;border-radius:5px;background:{h["color"]};'
            f'margin:0 12px;flex-shrink:0;"></div>'
            f'<div>'
            f'<div style="color:{TEXT_PRIMARY};font-weight:600;font-size:0.85rem;">'
            f'{escape(h["name"])}</div>'
            f'<div style="color:{TEXT_SECONDARY};font-size:0.8rem;">{escape(h["country"])}</div>'
            f'<div style="color:{TEXT_MUTED};font-size:0.78rem;">{escape(h["description"])}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    df = pd.DataFrame([{
        "Name": h["name"], "Era": h["era"], "Country": h["country"],
        "Description": h["description"], "Lat": h["lat"], "Lon": h["lon"],
    } for h in HISTORIC_ROUTES])

    _csv_download(df, "historic_wine_routes.csv",
                  f"Download {len(df)} Historic Sites (CSV)", "hw_dl")


def _render_beer_culture():
    """Mode 8: Beer Culture."""
    st.markdown("#### Beer Culture of the World")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Belgian Trappist abbeys, German beer halls, Czech pilsner, '
        f'British real ale, American craft pioneers &mdash; the world\'s great beer landmarks.</p>',
        unsafe_allow_html=True,
    )

    sub_types = sorted(set(b["sub_type"] for b in BEER_CULTURE))
    sel_types = st.multiselect("Filter by Beer Style", sub_types,
                               default=sub_types, key="bc_types")
    filtered = [b for b in BEER_CULTURE if b["sub_type"] in sel_types]

    c1, c2, c3 = st.columns(3)
    c1.metric("Landmarks", len(filtered))
    c2.metric("Countries", len(set(b["country"] for b in filtered)))
    c3.metric("Beer Styles", len(set(b["sub_type"] for b in filtered)))

    if filtered:
        avg_lat = sum(b["lat"] for b in filtered) / len(filtered)
        avg_lon = sum(b["lon"] for b in filtered) / len(filtered)
    else:
        avg_lat, avg_lon = 50.0, 5.0

    m = _make_dark_map([avg_lat, avg_lon], zoom=4)
    for b in filtered:
        popup = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(b["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(b["country"])} &mdash; {escape(b["sub_type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{escape(b["specialty"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=7, color=b["color"], fill=True,
            fill_color=b["color"], fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=240),
        ).add_to(m)

    _render_folium(m)

    df = pd.DataFrame([{
        "Name": b["name"], "Country": b["country"],
        "Style": b["sub_type"], "Specialty": b["specialty"],
        "Lat": b["lat"], "Lon": b["lon"],
    } for b in filtered])

    with st.expander(f"Full Data Table ({len(df)} landmarks)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "beer_culture.csv",
                  f"Download {len(df)} Beer Landmarks (CSV)", "bc_dl")


def _render_spirits_world():
    """Mode 9: Spirits of the World."""
    st.markdown("#### Spirits of the World")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Tequila from Jalisco, rum from the Caribbean, '
        f'sake from Kyoto, grappa from Veneto, baijiu from Guizhou, '
        f'cognac from Grande Champagne &mdash; mapped.</p>',
        unsafe_allow_html=True,
    )

    spirit_types = sorted(set(s["spirit"] for s in WORLD_SPIRITS))
    sel_spirits = st.multiselect("Filter by Spirit", spirit_types,
                                 default=spirit_types, key="sw_spirits")
    filtered = [s for s in WORLD_SPIRITS if s["spirit"] in sel_spirits]

    c1, c2, c3 = st.columns(3)
    c1.metric("Locations", len(filtered))
    c2.metric("Spirit Types", len(set(s["spirit"] for s in filtered)))
    c3.metric("Countries", len(set(s["country"] for s in filtered)))

    m = _make_dark_map([20, 0], zoom=2)
    for s in filtered:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{escape(s["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(s["spirit"])} &mdash; {escape(s["country"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Base:</b> {escape(s["base"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{escape(s["notes"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8, color=s["color"], fill=True,
            fill_color=s["color"], fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Legend
    legend_items = " ".join([
        f'<span style="color:{WORLD_SPIRITS[[s["spirit"] for s in WORLD_SPIRITS].index(sp)]["color"]}; '
        f'font-size:0.8rem;">&#9679; {escape(sp)}</span>'
        for sp in sorted(set(s["spirit"] for s in filtered))
    ])
    if legend_items:
        st.markdown(
            f'<div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin:0.5rem 0;">'
            f'{legend_items}</div>',
            unsafe_allow_html=True,
        )

    df = pd.DataFrame([{
        "Name": s["name"], "Spirit": s["spirit"],
        "Country": s["country"], "Base Ingredient": s["base"],
        "Notes": s["notes"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} spirits)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "world_spirits.csv",
                  f"Download {len(df)} Spirit Locations (CSV)", "sw_dl")


def _render_vineyard_terroir():
    """Mode 10: Vineyard Terroir."""
    st.markdown("#### Vineyard Terroir &mdash; Soil, Climate & Altitude")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">How soil types, climate zones, and altitude shape wine character '
        f'&mdash; from Kimmeridgian limestone in Chablis to volcanic pumice on Santorini.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Terroir Sites", len(TERROIR_DATA))
    avg_alt = int(sum(t["altitude_m"] for t in TERROIR_DATA) / len(TERROIR_DATA))
    c2.metric("Avg. Altitude", f"{avg_alt} m")
    c3.metric("Soil Types", len(set(t["soil"].split("(")[0].strip() for t in TERROIR_DATA)))

    m = _make_dark_map([40, 10], zoom=3)
    for t in TERROIR_DATA:
        popup = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(t["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(t["region"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Soil:</b> {escape(t["soil"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Climate:</b> {escape(t["climate"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Altitude:</b> {t["altitude_m"]}m</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Effect:</b> {escape(t["effect"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=9, color=t["color"], fill=True,
            fill_color=t["color"], fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Terroir detail cards
    st.markdown("---")
    st.markdown("#### Terroir Profiles")
    for t in TERROIR_DATA:
        st.markdown(
            f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:8px;'
            f'padding:12px;margin-bottom:8px;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div style="width:12px;height:50px;border-radius:6px;background:{t["color"]};flex-shrink:0;"></div>'
            f'<div>'
            f'<div style="color:{TEXT_PRIMARY};font-weight:700;font-size:0.9rem;">{escape(t["name"])}</div>'
            f'<div style="color:{TEXT_MUTED};font-size:0.8rem;">{escape(t["region"])} &bull; {t["altitude_m"]}m elevation</div>'
            f'</div></div>'
            f'<div style="margin-top:6px;color:{TEXT_SECONDARY};font-size:0.83rem;">'
            f'<b>Soil:</b> {escape(t["soil"])}</div>'
            f'<div style="color:{TEXT_SECONDARY};font-size:0.83rem;">'
            f'<b>Climate:</b> {escape(t["climate"])}</div>'
            f'<div style="color:{TEXT_PRIMARY};font-size:0.83rem;margin-top:4px;">'
            f'<b>Wine Effect:</b> {escape(t["effect"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Altitude chart
    st.markdown("---")
    st.markdown("#### Altitude Comparison")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sorted_terroir = sorted(TERROIR_DATA, key=lambda x: x["altitude_m"], reverse=True)
    labels = [t["name"].split(" — ")[0][:22] for t in sorted_terroir]
    altitudes = [t["altitude_m"] for t in sorted_terroir]
    colors = [t["color"] for t in sorted_terroir]

    fig, ax = plt.subplots(figsize=(8, 5))
    _dark_chart_style(fig, ax)
    ax.barh(range(len(labels)), altitudes, color=colors, alpha=0.85)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color=TEXT_SECONDARY, fontsize=8)
    ax.set_xlabel("Altitude (m)", color=TEXT_SECONDARY, fontsize=10)
    ax.set_title("Vineyard Altitude by Region", color=TEXT_PRIMARY, fontsize=12, pad=10)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame([{
        "Site": t["name"], "Region": t["region"],
        "Soil": t["soil"], "Climate": t["climate"],
        "Altitude (m)": t["altitude_m"], "Effect on Wine": t["effect"],
        "Lat": t["lat"], "Lon": t["lon"],
    } for t in TERROIR_DATA])

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "vineyard_terroir.csv",
                  f"Download {len(df)} Terroir Profiles (CSV)", "vt_dl")


# ═══════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ═══════════════════════════════════════════════════════════════

def render_wine_maps_tab():
    """Main render function for the Wine, Beer & Spirits Maps tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>\U0001f377 Wine, Beer & Spirits Maps</h4>'
        '<p>Wine regions, breweries, distilleries, vineyards & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.selectbox("Choose a Map Mode", MAP_MODES, key="wine_mode")

    st.markdown("---")

    # ── Dispatch ──
    if mode == MAP_MODES[0]:
        _render_world_wine_regions()
    elif mode == MAP_MODES[1]:
        _render_grape_varieties()
    elif mode == MAP_MODES[2]:
        _render_craft_breweries()
    elif mode == MAP_MODES[3]:
        _render_whisky_distilleries()
    elif mode == MAP_MODES[4]:
        _render_champagne_sparkling()
    elif mode == MAP_MODES[5]:
        _render_wine_classification()
    elif mode == MAP_MODES[6]:
        _render_historic_wine_routes()
    elif mode == MAP_MODES[7]:
        _render_beer_culture()
    elif mode == MAP_MODES[8]:
        _render_spirits_world()
    elif mode == MAP_MODES[9]:
        _render_vineyard_terroir()
