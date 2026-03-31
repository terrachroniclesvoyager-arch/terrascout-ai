# -*- coding: utf-8 -*-
"""
World Cuisine Explorer module for TerraScout AI.
Maps culinary traditions, food origins, spice routes, Michelin restaurants,
street food capitals, coffee, tea, chocolate, beer, UNESCO food heritage,
and superfoods using curated geospatial datasets.
All data is curated — no external API key required.
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

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════
MAP_MODES = [
    "World Cuisine Origins",
    "Michelin Star Restaurants",
    "Street Food Capitals",
    "Coffee Origins & Culture",
    "Tea Traditions",
    "Chocolate & Cacao",
    "Spice Routes & Origins",
    "Beer & Brewing",
    "UNESCO Intangible Food Heritage",
    "Superfoods & Ancient Grains",
]

MODE_DESCRIPTIONS = {
    "World Cuisine Origins": (
        "Trace the birthplaces of the world's most beloved dishes — from Neapolitan pizza "
        "and Japanese sushi to Mexican tacos and Indian curry. Each dish carries centuries of "
        "cultural heritage and tells a story of migration, trade, and local ingredients."
    ),
    "Michelin Star Restaurants": (
        "The Michelin Guide has awarded stars to the finest restaurants since 1926. Tokyo leads "
        "with the most Michelin stars of any city, followed by Paris, Kyoto, and Osaka. Three "
        "stars denote 'exceptional cuisine, worth a special journey.'"
    ),
    "Street Food Capitals": (
        "Street food represents the culinary soul of a city. Bangkok's night markets, Mexico "
        "City's taco stands, Istanbul's simit vendors, and Mumbai's chaat stalls offer "
        "flavours that define entire cultures at an accessible price."
    ),
    "Coffee Origins & Culture": (
        "Coffee was first cultivated in Ethiopia around the 9th century before spreading to "
        "Yemen, the Ottoman Empire, and the world. Today arabica and robusta beans grow in a "
        "tropical 'bean belt' while cafe cultures flourish from Vienna to Melbourne."
    ),
    "Tea Traditions": (
        "Tea originated in China over 5,000 years ago and became central to Japanese ceremony, "
        "Indian chai culture, British afternoon tradition, and Moroccan hospitality. It is the "
        "most consumed beverage on Earth after water."
    ),
    "Chocolate & Cacao": (
        "Theobroma cacao was first domesticated by Mesoamerican civilisations over 3,000 years "
        "ago. Today the cocoa belt spans West Africa, Southeast Asia, and Latin America, while "
        "Belgium, Switzerland, and France lead in artisan chocolate production."
    ),
    "Spice Routes & Origins": (
        "Spices drove global exploration and trade for millennia. Black pepper from India, "
        "saffron from Iran, vanilla from Mexico, cinnamon from Sri Lanka, and cardamom from "
        "Guatemala each shaped empires, economies, and cuisines worldwide."
    ),
    "Beer & Brewing": (
        "Beer is among humanity's oldest beverages, with evidence from 5,000-year-old Sumerian "
        "tablets. Belgian Trappist ales, the German Reinheitsgebot, Czech pilsner, British "
        "cask ales, and the modern craft beer revolution all have deep geographical roots."
    ),
    "UNESCO Intangible Food Heritage": (
        "UNESCO recognises culinary traditions as Intangible Cultural Heritage. French gastronomy, "
        "the Mediterranean diet, Japanese washoku, Korean kimjang (kimchi-making), and Mexican "
        "cuisine are among the traditions safeguarded for future generations."
    ),
    "Superfoods & Ancient Grains": (
        "Ancient grains and superfoods represent thousands of years of agricultural knowledge. "
        "Quinoa from the Andes, acai from the Amazon, turmeric from India, teff from Ethiopia, "
        "and chia from Mesoamerica are now global health-food staples."
    ),
}

MODE_COLORS = {
    "World Cuisine Origins": "#f97316",
    "Michelin Star Restaurants": "#ef4444",
    "Street Food Capitals": "#f59e0b",
    "Coffee Origins & Culture": "#a16207",
    "Tea Traditions": "#10b981",
    "Chocolate & Cacao": "#92400e",
    "Spice Routes & Origins": "#ec4899",
    "Beer & Brewing": "#eab308",
    "UNESCO Intangible Food Heritage": "#3b82f6",
    "Superfoods & Ancient Grains": "#06b6d4",
}

# ═══════════════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════════════

# --- Mode 1: World Cuisine Origins ---
CUISINE_ORIGINS = [
    {"dish": "Pizza Margherita", "origin_city": "Naples", "country": "Italy",
     "year": 1889, "lat": 40.8518, "lon": 14.2681,
     "notes": "Named after Queen Margherita; tomato, mozzarella, basil represent the Italian flag"},
    {"dish": "Sushi (Edomae)", "origin_city": "Tokyo (Edo)", "country": "Japan",
     "year": 1824, "lat": 35.6762, "lon": 139.6503,
     "notes": "Hanaya Yohei pioneered nigiri-zushi using fresh fish from Tokyo Bay"},
    {"dish": "Tacos", "origin_city": "Mexico City", "country": "Mexico",
     "year": 1500, "lat": 19.4326, "lon": -99.1332,
     "notes": "Pre-Columbian origins; tortillas filled with fish, insects, and game"},
    {"dish": "Curry (Kari)", "origin_city": "Chennai", "country": "India",
     "year": -2600, "lat": 13.0827, "lon": 80.2707,
     "notes": "Spice blends dating to the Indus Valley civilisation; 'kari' means sauce in Tamil"},
    {"dish": "Pad Thai", "origin_city": "Bangkok", "country": "Thailand",
     "year": 1938, "lat": 13.7563, "lon": 100.5018,
     "notes": "Promoted by PM Plaek Phibunsongkhram as a national dish to reduce rice consumption"},
    {"dish": "Peking Duck", "origin_city": "Beijing", "country": "China",
     "year": 1330, "lat": 39.9042, "lon": 116.4074,
     "notes": "Imperial court dish since the Yuan Dynasty; air-dried and roasted in wood-fired ovens"},
    {"dish": "Croissant", "origin_city": "Vienna / Paris", "country": "Austria / France",
     "year": 1838, "lat": 48.8566, "lon": 2.3522,
     "notes": "Austrian Kipferl adapted by French baker August Zang in Paris"},
    {"dish": "Kebab (Shish)", "origin_city": "Ankara", "country": "Turkey",
     "year": 1377, "lat": 39.9334, "lon": 32.8597,
     "notes": "Ottoman soldiers grilled meat on swords; mentioned in travel writings of Ibn Battuta"},
    {"dish": "Dim Sum", "origin_city": "Guangzhou", "country": "China",
     "year": 960, "lat": 23.1291, "lon": 113.2644,
     "notes": "Tea-house tradition along Silk Road; 'yum cha' (drinking tea) with small dishes"},
    {"dish": "Pasta (Dried)", "origin_city": "Palermo", "country": "Italy",
     "year": 1154, "lat": 38.1157, "lon": 13.3615,
     "notes": "Al-Idrisi documented dry pasta production in Sicily; Arab-Norman influence"},
    {"dish": "Hamburger", "origin_city": "Hamburg / New Haven", "country": "Germany / USA",
     "year": 1900, "lat": 41.3083, "lon": -72.9279,
     "notes": "Louis' Lunch in New Haven claims the first hamburger in 1900"},
    {"dish": "Pho", "origin_city": "Hanoi", "country": "Vietnam",
     "year": 1910, "lat": 21.0285, "lon": 105.8542,
     "notes": "Fusion of Vietnamese and French culinary traditions; beef bone broth with rice noodles"},
    {"dish": "Paella", "origin_city": "Valencia", "country": "Spain",
     "year": 1840, "lat": 39.4699, "lon": -0.3763,
     "notes": "Rice dish cooked over open fire; originally with rabbit, snails, and beans"},
    {"dish": "Fish and Chips", "origin_city": "London", "country": "United Kingdom",
     "year": 1860, "lat": 51.5074, "lon": -0.1278,
     "notes": "Joseph Malin opened first combined fish-and-chip shop in East London"},
    {"dish": "Tom Yum Goong", "origin_city": "Bangkok", "country": "Thailand",
     "year": 1700, "lat": 13.7563, "lon": 100.5018,
     "notes": "Hot and sour shrimp soup with lemongrass, galangal, kaffir lime, and chillies"},
    {"dish": "Ceviche", "origin_city": "Lima", "country": "Peru",
     "year": -200, "lat": -12.0464, "lon": -77.0428,
     "notes": "Pre-Inca Moche civilisation cured fish in fermented fruit juice; today lime-cured"},
    {"dish": "Moussaka", "origin_city": "Athens", "country": "Greece",
     "year": 1920, "lat": 37.9838, "lon": 23.7275,
     "notes": "Nikolaos Tselementes codified the bechamel-topped version in the 1920s"},
    {"dish": "Rendang", "origin_city": "Padang", "country": "Indonesia",
     "year": 1550, "lat": -0.9471, "lon": 100.4172,
     "notes": "Slow-cooked coconut-spice beef of the Minangkabau; voted world's most delicious food by CNN"},
    {"dish": "Ramen", "origin_city": "Yokohama", "country": "Japan",
     "year": 1910, "lat": 35.4437, "lon": 139.6380,
     "notes": "Chinese-style noodles adapted in Japanese port city; now a national obsession"},
    {"dish": "Tagine", "origin_city": "Fez", "country": "Morocco",
     "year": 800, "lat": 34.0331, "lon": -5.0003,
     "notes": "Named after the conical clay pot; slow-cooked stews with preserved lemons and olives"},
    {"dish": "Jollof Rice", "origin_city": "Saint-Louis", "country": "Senegal",
     "year": 1300, "lat": 16.0179, "lon": -16.4896,
     "notes": "Originated with the Wolof people; one-pot tomato rice beloved across West Africa"},
    {"dish": "Pierogi", "origin_city": "Krakow", "country": "Poland",
     "year": 1200, "lat": 50.0647, "lon": 19.9450,
     "notes": "Filled dumplings brought from the East; central to Polish and Eastern European cuisine"},
    {"dish": "Biryani", "origin_city": "Lucknow", "country": "India",
     "year": 1600, "lat": 26.8467, "lon": 80.9462,
     "notes": "Mughal court dish; layered rice with spiced meat cooked in a sealed pot (dum)"},
    {"dish": "Feijoada", "origin_city": "Rio de Janeiro", "country": "Brazil",
     "year": 1700, "lat": -22.9068, "lon": -43.1729,
     "notes": "Black bean and pork stew; national dish blending Portuguese, African, and indigenous traditions"},
    {"dish": "Kimchi", "origin_city": "Seoul", "country": "South Korea",
     "year": -37, "lat": 37.5665, "lon": 126.9780,
     "notes": "Fermented vegetables; over 200 varieties; central to Korean identity and UNESCO-listed"},
]

# --- Mode 2: Michelin Star Restaurants ---
MICHELIN_CITIES = [
    {"city": "Tokyo", "country": "Japan", "total_stars": 263, "three_star": 12,
     "lat": 35.6762, "lon": 139.6503,
     "notes": "Most Michelin stars of any city in the world since 2007"},
    {"city": "Paris", "country": "France", "total_stars": 118, "three_star": 9,
     "lat": 48.8566, "lon": 2.3522,
     "notes": "Birthplace of the Michelin Guide in 1900; haute cuisine capital"},
    {"city": "Kyoto", "country": "Japan", "total_stars": 104, "three_star": 7,
     "lat": 35.0116, "lon": 135.7681,
     "notes": "Ancient capital; kaiseki and temple cuisine traditions"},
    {"city": "Osaka", "country": "Japan", "total_stars": 97, "three_star": 4,
     "lat": 34.6937, "lon": 135.5023,
     "notes": "Known as Japan's Kitchen (tenka no daidokoro)"},
    {"city": "London", "country": "United Kingdom", "total_stars": 75, "three_star": 3,
     "lat": 51.5074, "lon": -0.1278,
     "notes": "Diverse global dining scene; Gordon Ramsay's flagship 3-star since 2001"},
    {"city": "New York", "country": "USA", "total_stars": 72, "three_star": 5,
     "lat": 40.7128, "lon": -74.0060,
     "notes": "Le Bernardin, Eleven Madison Park, Masa among iconic 3-stars"},
    {"city": "Singapore", "country": "Singapore", "total_stars": 54, "three_star": 3,
     "lat": 1.3521, "lon": 103.8198,
     "notes": "First hawker stalls to receive Michelin stars (2016)"},
    {"city": "Hong Kong", "country": "China", "total_stars": 71, "three_star": 7,
     "lat": 22.3193, "lon": 114.1694,
     "notes": "East-meets-West fine dining; Tim Ho Wan is cheapest Michelin-starred restaurant"},
    {"city": "Bangkok", "country": "Thailand", "total_stars": 36, "three_star": 1,
     "lat": 13.7563, "lon": 100.5018,
     "notes": "First Thai Michelin guide launched 2018; street food to fine dining"},
    {"city": "Lyon", "country": "France", "total_stars": 23, "three_star": 2,
     "lat": 45.7640, "lon": 4.8357,
     "notes": "France's gastronomic capital; Paul Bocuse earned 3 stars for 55 consecutive years"},
    {"city": "San Sebastian", "country": "Spain", "total_stars": 20, "three_star": 3,
     "lat": 43.3183, "lon": -1.9812,
     "notes": "Highest density of Michelin stars per capita; Basque cuisine paradise"},
    {"city": "Chicago", "country": "USA", "total_stars": 24, "three_star": 2,
     "lat": 41.8781, "lon": -87.6298,
     "notes": "Alinea holds 3 stars; pioneering molecular gastronomy and tasting menus"},
    {"city": "Copenhagen", "country": "Denmark", "total_stars": 19, "three_star": 2,
     "lat": 55.6761, "lon": 12.5683,
     "notes": "Noma revolutionised New Nordic cuisine; Geranium earned 3 stars"},
    {"city": "Florence", "country": "Italy", "total_stars": 12, "three_star": 1,
     "lat": 43.7696, "lon": 11.2558,
     "notes": "Enoteca Pinchiorri — Tuscan fine dining with 170,000-bottle wine cellar"},
    {"city": "Taipei", "country": "Taiwan", "total_stars": 31, "three_star": 1,
     "lat": 25.0330, "lon": 121.5654,
     "notes": "First Taipei guide 2018; outstanding Cantonese, Japanese, and Taiwanese cuisines"},
    {"city": "Seoul", "country": "South Korea", "total_stars": 35, "three_star": 2,
     "lat": 37.5665, "lon": 126.9780,
     "notes": "Korean temple food to modern Korean fine dining; guide launched 2016"},
    {"city": "Barcelona", "country": "Spain", "total_stars": 18, "three_star": 1,
     "lat": 41.3874, "lon": 2.1686,
     "notes": "Catalan cuisine; Lasarte and ABaC lead the scene"},
    {"city": "Milan", "country": "Italy", "total_stars": 16, "three_star": 1,
     "lat": 45.4642, "lon": 9.1900,
     "notes": "Northern Italian fine dining; Enrico Bartolini at MUDEC holds 3 stars"},
    {"city": "Los Angeles", "country": "USA", "total_stars": 25, "three_star": 1,
     "lat": 34.0522, "lon": -118.2437,
     "notes": "N/Naka holds 2 stars; diverse food scene from taco trucks to fine dining"},
    {"city": "Munich", "country": "Germany", "total_stars": 14, "three_star": 1,
     "lat": 48.1351, "lon": 11.5820,
     "notes": "Atelier at Bayerischer Hof is Munich's crown jewel of fine dining"},
]

# --- Mode 3: Street Food Capitals ---
STREET_FOOD = [
    {"city": "Bangkok", "country": "Thailand", "specialty": "Pad Thai, Som Tam, Mango Sticky Rice",
     "vendors_est": 400000, "lat": 13.7563, "lon": 100.5018,
     "notes": "Yaowarat (Chinatown) and Khao San Road are legendary street food zones"},
    {"city": "Mexico City", "country": "Mexico", "specialty": "Tacos al Pastor, Tlacoyos, Tamales",
     "vendors_est": 350000, "lat": 19.4326, "lon": -99.1332,
     "notes": "Taco stands on every corner; tacos al pastor adapted from Lebanese shawarma"},
    {"city": "Istanbul", "country": "Turkey", "specialty": "Simit, Balik Ekmek, Doner Kebab",
     "vendors_est": 120000, "lat": 41.0082, "lon": 28.9784,
     "notes": "Balik ekmek (fish sandwich) by the Galata Bridge; simit sellers everywhere"},
    {"city": "Marrakech", "country": "Morocco", "specialty": "Tagine, Msemen, Snail Soup",
     "vendors_est": 30000, "lat": 31.6295, "lon": -7.9811,
     "notes": "Jemaa el-Fnaa square transforms nightly into world's largest open-air restaurant"},
    {"city": "Mumbai", "country": "India", "specialty": "Vada Pav, Pav Bhaji, Bhel Puri",
     "vendors_est": 250000, "lat": 19.0760, "lon": 72.8777,
     "notes": "Vada pav is Mumbai's Rs 10 burger; Chowpatty Beach is chaat paradise"},
    {"city": "Hanoi", "country": "Vietnam", "specialty": "Pho, Bun Cha, Banh Mi",
     "vendors_est": 80000, "lat": 21.0285, "lon": 105.8542,
     "notes": "Old Quarter sidewalk dining; Obama enjoyed bun cha at Huong Lien in 2016"},
    {"city": "Penang", "country": "Malaysia", "specialty": "Char Kway Teow, Laksa, Cendol",
     "vendors_est": 45000, "lat": 5.4141, "lon": 100.3288,
     "notes": "George Town hawker centres are UNESCO-adjacent food heritage sites"},
    {"city": "Cairo", "country": "Egypt", "specialty": "Koshari, Ful Medames, Ta'ameya",
     "vendors_est": 100000, "lat": 30.0444, "lon": 31.2357,
     "notes": "Koshari is Egypt's national dish; lentils, rice, pasta, and tomato sauce"},
    {"city": "Lima", "country": "Peru", "specialty": "Ceviche, Anticuchos, Picarones",
     "vendors_est": 65000, "lat": -12.0464, "lon": -77.0428,
     "notes": "Gastronomic capital of South America; ceviche stands at every fish market"},
    {"city": "Osaka", "country": "Japan", "specialty": "Takoyaki, Okonomiyaki, Kushikatsu",
     "vendors_est": 55000, "lat": 34.6937, "lon": 135.5023,
     "notes": "Dotonbori is street food heaven; 'kuidaore' means to eat until you drop"},
    {"city": "Kolkata", "country": "India", "specialty": "Kathi Roll, Jhal Muri, Phuchka",
     "vendors_est": 150000, "lat": 22.5726, "lon": 88.3639,
     "notes": "Kathi roll invented at Nizam's in 1932; unique Bengali street food culture"},
    {"city": "Taipei", "country": "Taiwan", "specialty": "Bubble Tea, Stinky Tofu, Gua Bao",
     "vendors_est": 75000, "lat": 25.0330, "lon": 121.5654,
     "notes": "Shilin Night Market hosts 500+ vendors; bubble tea invented here in the 1980s"},
    {"city": "Lagos", "country": "Nigeria", "specialty": "Suya, Puff Puff, Jollof Rice",
     "vendors_est": 200000, "lat": 6.5244, "lon": 3.3792,
     "notes": "Suya vendors line major roads after dark; spiced grilled meat skewers"},
    {"city": "Singapore", "country": "Singapore", "specialty": "Hainanese Chicken Rice, Laksa, Satay",
     "vendors_est": 35000, "lat": 1.3521, "lon": 103.8198,
     "notes": "Hawker centres are UNESCO Intangible Heritage; Hill Street Tai Hwa won Michelin star"},
    {"city": "Palermo", "country": "Italy", "specialty": "Arancini, Panelle, Sfincione",
     "vendors_est": 12000, "lat": 38.1157, "lon": 13.3615,
     "notes": "Ballaro and Vucciria markets; Arab-Norman influenced Sicilian street food"},
]

# --- Mode 4: Coffee Origins & Culture ---
COFFEE_DATA = [
    {"name": "Ethiopian Highlands", "type": "Origin (Arabica birthplace)", "country": "Ethiopia",
     "lat": 7.0, "lon": 38.0, "detail": "Kaffa region — legendary goatherd Kaldi discovered coffee c. 850 AD",
     "production_mt": 496000},
    {"name": "Yemen — Mocha Port", "type": "Historic Trade Hub", "country": "Yemen",
     "lat": 13.3194, "lon": 43.2472, "detail": "Port of Mocha exported coffee globally from the 15th century",
     "production_mt": 20000},
    {"name": "Brazil — Minas Gerais", "type": "Top Producer (Arabica)", "country": "Brazil",
     "lat": -19.9167, "lon": -43.9345, "detail": "Brazil produces ~35% of world coffee; cerrado and altitude regions",
     "production_mt": 3800000},
    {"name": "Colombia — Eje Cafetero", "type": "Arabica Region", "country": "Colombia",
     "lat": 4.8133, "lon": -75.6961, "detail": "Coffee Cultural Landscape is UNESCO World Heritage; shade-grown",
     "production_mt": 858000},
    {"name": "Vietnam — Central Highlands", "type": "Top Producer (Robusta)", "country": "Vietnam",
     "lat": 12.6667, "lon": 108.0500, "detail": "Second-largest global producer; mostly robusta for instant coffee",
     "production_mt": 1850000},
    {"name": "Vienna", "type": "Cafe Culture Capital", "country": "Austria",
     "lat": 48.2082, "lon": 16.3738, "detail": "Viennese coffee house culture is UNESCO heritage since 2011",
     "production_mt": 0},
    {"name": "Melbourne", "type": "Modern Cafe Culture", "country": "Australia",
     "lat": -37.8136, "lon": 144.9631, "detail": "Flat white origin city; laneways with world-class roasters",
     "production_mt": 0},
    {"name": "Seattle", "type": "Specialty Coffee Hub", "country": "USA",
     "lat": 47.6062, "lon": -122.3321, "detail": "Birthplace of Starbucks (1971); capital of third-wave coffee",
     "production_mt": 0},
    {"name": "Istanbul", "type": "Historic Coffee Culture", "country": "Turkey",
     "lat": 41.0082, "lon": 28.9784, "detail": "Turkish coffee preparation is UNESCO heritage; kahvehane tradition",
     "production_mt": 0},
    {"name": "Jamaica — Blue Mountains", "type": "Premium Arabica", "country": "Jamaica",
     "lat": 18.1824, "lon": -76.3695, "detail": "Blue Mountain Coffee — among world's most expensive single origins",
     "production_mt": 1200},
    {"name": "Indonesia — Sumatra", "type": "Robusta & Specialty", "country": "Indonesia",
     "lat": 0.5897, "lon": 101.3431, "detail": "Kopi Luwak (civet coffee) and Mandheling single-origin beans",
     "production_mt": 765000},
    {"name": "Costa Rica — Central Valley", "type": "Arabica Region", "country": "Costa Rica",
     "lat": 9.9281, "lon": -84.0907, "detail": "Only arabica is legally grown; SHB (Strictly Hard Bean) grades",
     "production_mt": 82000},
    {"name": "Kenya — Mount Kenya Region", "type": "Specialty Arabica", "country": "Kenya",
     "lat": -0.1517, "lon": 37.3089, "detail": "SL28 and SL34 cultivars produce bright, fruity coffees",
     "production_mt": 45000},
    {"name": "Guatemala — Antigua", "type": "Highland Arabica", "country": "Guatemala",
     "lat": 14.5586, "lon": -90.7295, "detail": "Volcanic soil and altitude produce complex, chocolatey profiles",
     "production_mt": 245000},
    {"name": "Hawaii — Kona", "type": "Premium Arabica", "country": "USA",
     "lat": 19.6400, "lon": -155.9969, "detail": "Kona coffee grown on volcanic slopes of Hualalai and Mauna Loa",
     "production_mt": 3600},
]

# --- Mode 5: Tea Traditions ---
TEA_DATA = [
    {"name": "Yunnan, China", "type": "Origin of Tea", "tradition": "Pu-erh",
     "lat": 25.0389, "lon": 102.7183, "country": "China",
     "detail": "Wild tea trees over 3,000 years old; birthplace of all Camellia sinensis cultivars"},
    {"name": "Fujian, China", "type": "Oolong & White Tea", "tradition": "Gongfu Cha",
     "lat": 26.0785, "lon": 117.9873, "country": "China",
     "detail": "Wuyi Mountain oolongs; gongfu ceremony uses tiny clay teapots and repeated infusions"},
    {"name": "Uji, Kyoto", "type": "Matcha Production", "tradition": "Chanoyu",
     "lat": 34.8843, "lon": 135.8029, "country": "Japan",
     "detail": "Japanese tea ceremony (chanoyu); stone-ground matcha; Sen no Rikyu's wabi-cha philosophy"},
    {"name": "Shizuoka, Japan", "type": "Sencha Region", "tradition": "Daily Green Tea",
     "lat": 34.9769, "lon": 138.3831, "country": "Japan",
     "detail": "Produces 40% of Japan's tea; Mount Fuji backdrop; fukamushi (deep-steamed) sencha"},
    {"name": "Darjeeling, India", "type": "Champagne of Teas", "tradition": "British Colonial",
     "lat": 27.0360, "lon": 88.2627, "country": "India",
     "detail": "Himalayan estates at 2,000 m; first flush is most prized; GI-protected name"},
    {"name": "Assam, India", "type": "Black Tea", "tradition": "Chai Culture",
     "lat": 26.2006, "lon": 92.9376, "country": "India",
     "detail": "World's largest tea-growing region; malty, robust CTC tea; masala chai staple"},
    {"name": "Sri Lanka — Nuwara Eliya", "type": "Ceylon Tea", "tradition": "Colonial Heritage",
     "lat": 6.9497, "lon": 80.7891, "country": "Sri Lanka",
     "detail": "High-grown Ceylon at 1,800 m; light and citrusy; introduced by James Taylor (1867)"},
    {"name": "London, England", "type": "Afternoon Tea", "tradition": "British Tea Culture",
     "lat": 51.5074, "lon": -0.1278, "country": "United Kingdom",
     "detail": "Afternoon tea invented by Duchess of Bedford (1840); daily consumption: 165 million cups"},
    {"name": "Marrakech, Morocco", "type": "Maghrebi Mint Tea", "tradition": "Hospitality",
     "lat": 31.6295, "lon": -7.9811, "country": "Morocco",
     "detail": "Green tea with spearmint and sugar poured from height; 'Berber whiskey'; offered to all guests"},
    {"name": "Istanbul, Turkey", "type": "Cay (Black Tea)", "tradition": "Tea Garden Culture",
     "lat": 41.0082, "lon": 28.9784, "country": "Turkey",
     "detail": "Highest per-capita consumption; tulip-shaped glasses; double teapot (caydanlik) system"},
    {"name": "Hangzhou, China", "type": "Longjing (Dragon Well)", "tradition": "Imperial Tea",
     "lat": 30.2741, "lon": 120.1551, "country": "China",
     "detail": "Emperor's tea; West Lake Longjing is pan-fired green tea; UNESCO area"},
    {"name": "Taiwan — Alishan", "type": "High Mountain Oolong", "tradition": "Taiwanese Gongfu",
     "lat": 23.5082, "lon": 120.7032, "country": "Taiwan",
     "detail": "High-altitude (1,500 m) oolongs with floral notes; bubble tea invented in Taichung (1980s)"},
    {"name": "Rize, Turkey", "type": "Turkish Black Tea", "tradition": "Cay Bardagi",
     "lat": 41.0201, "lon": 40.5234, "country": "Turkey",
     "detail": "Eastern Black Sea coast; Turkey's main tea-growing region; terraced hillsides"},
    {"name": "Kolkata, India", "type": "Chai Capital", "tradition": "Street Chai",
     "lat": 22.5726, "lon": 88.3639, "country": "India",
     "detail": "Chai wallahs on every corner; served in traditional clay cups (kulhar)"},
    {"name": "Nairobi, Kenya", "type": "Purple Tea", "tradition": "East African Tea",
     "lat": -1.2921, "lon": 36.8219, "country": "Kenya",
     "detail": "Kenya is world's largest tea exporter; novel anthocyanin-rich purple tea cultivar"},
]

# --- Mode 6: Chocolate & Cacao ---
CHOCOLATE_DATA = [
    {"name": "Tabasco & Chiapas, Mexico", "type": "Cacao Birthplace", "country": "Mexico",
     "lat": 17.8409, "lon": -92.6189,
     "detail": "Olmec and Maya first cultivated cacao 3,900 years ago; 'xocolatl' (bitter water)"},
    {"name": "Cote d'Ivoire", "type": "Top Producer", "country": "Cote d'Ivoire",
     "lat": 6.8276, "lon": -5.2893,
     "detail": "Produces ~40% of world cacao (2.2M tonnes); Forastero variety dominates"},
    {"name": "Ghana — Ashanti Region", "type": "Major Producer", "country": "Ghana",
     "lat": 6.6666, "lon": -1.6163,
     "detail": "Second-largest producer; Ghanaian cocoa known for consistent quality"},
    {"name": "Brussels, Belgium", "type": "Chocolatier Capital", "country": "Belgium",
     "lat": 50.8503, "lon": 4.3517,
     "detail": "2,000+ chocolate shops; praline invented here (1912); 220,000 tonnes/year production"},
    {"name": "Zurich, Switzerland", "type": "Swiss Chocolate", "country": "Switzerland",
     "lat": 47.3769, "lon": 8.5417,
     "detail": "Daniel Peter invented milk chocolate (1875); Lindt conching process (1879)"},
    {"name": "Ecuador — Los Rios", "type": "Fine Cacao (Nacional)", "country": "Ecuador",
     "lat": -1.0225, "lon": -79.4608,
     "detail": "Arriba Nacional cacao — world's finest flavour bean; floral and fruity notes"},
    {"name": "Madagascar — SAVA Region", "type": "Specialty Cacao", "country": "Madagascar",
     "lat": -14.3551, "lon": 50.1726,
     "detail": "Criollo-Trinitario hybrids; unique fruity and citrus flavour profiles"},
    {"name": "Turin, Italy", "type": "Gianduja & Historic", "country": "Italy",
     "lat": 45.0703, "lon": 7.6869,
     "detail": "Invented gianduja (hazelnut chocolate) in 1865; bicerin coffee-chocolate drink"},
    {"name": "Venezuela — Chuao", "type": "Heirloom Cacao", "country": "Venezuela",
     "lat": 10.5050, "lon": -67.5334,
     "detail": "Chuao criollo cacao — among world's rarest and most sought-after beans"},
    {"name": "Bayonne, France", "type": "French Chocolate Heritage", "country": "France",
     "lat": 43.4929, "lon": -1.4748,
     "detail": "Chocolate arrived in France here via Sephardic Jews from Spain (1615)"},
    {"name": "Indonesia — Sulawesi", "type": "Major Producer", "country": "Indonesia",
     "lat": -2.0, "lon": 121.0,
     "detail": "Third-largest producer; Sulawesi beans used in mass-market chocolate"},
    {"name": "Dominican Republic", "type": "Organic Cacao Leader", "country": "Dominican Republic",
     "lat": 19.0, "lon": -70.1667,
     "detail": "Largest organic cacao exporter; Hispaniola criollo beans prized by craft makers"},
    {"name": "Oaxaca, Mexico", "type": "Traditional Chocolate", "country": "Mexico",
     "lat": 17.0732, "lon": -96.7266,
     "detail": "Mole sauce with chocolate; traditional stone-ground drinking chocolate with spices"},
    {"name": "São Tomé e Príncipe", "type": "Island Cacao", "country": "São Tomé e Príncipe",
     "lat": 0.1864, "lon": 6.6131,
     "detail": "Former Portuguese colony; fine-flavour forastero-amelonado cacao; bean-to-bar movement"},
    {"name": "Peru — Cusco", "type": "Chuncho Cacao", "country": "Peru",
     "lat": -13.5320, "lon": -71.9675,
     "detail": "Chuncho native cacao from Quillabamba Valley; used in award-winning bean-to-bar chocolate"},
]

# --- Mode 7: Spice Routes & Origins ---
SPICE_DATA = [
    {"spice": "Black Pepper", "origin": "Kerala, India", "country": "India",
     "lat": 10.8505, "lon": 76.2711,
     "detail": "King of Spices; Malabar pepper drove Roman, Arab, and Portuguese trade; once worth more than gold",
     "trade_value_usd": 4500000000},
    {"spice": "Saffron", "origin": "Khorasan, Iran", "country": "Iran",
     "lat": 36.2972, "lon": 59.6067,
     "detail": "World's most expensive spice ($5,000/kg); 150,000 crocus flowers per kg; Iran produces 90%",
     "trade_value_usd": 1200000000},
    {"spice": "Vanilla", "origin": "Veracruz, Mexico", "country": "Mexico",
     "lat": 19.1738, "lon": -96.1342,
     "detail": "Totonac people first cultivated; hand-pollinated; Madagascar now produces 80%",
     "trade_value_usd": 900000000},
    {"spice": "Cinnamon (True)", "origin": "Sri Lanka", "country": "Sri Lanka",
     "lat": 7.8731, "lon": 80.7718,
     "detail": "Ceylon cinnamon (C. verum) vs cassia; Arab traders kept source secret for centuries",
     "trade_value_usd": 800000000},
    {"spice": "Cardamom", "origin": "Western Ghats, India", "country": "India",
     "lat": 10.0159, "lon": 77.0639,
     "detail": "Queen of Spices; third most expensive; Guatemala is now largest producer",
     "trade_value_usd": 600000000},
    {"spice": "Turmeric", "origin": "Tamil Nadu, India", "country": "India",
     "lat": 11.1271, "lon": 78.6569,
     "detail": "Used in Ayurveda for 4,000 years; curcumin compound; India produces 80% of world supply",
     "trade_value_usd": 500000000},
    {"spice": "Cloves", "origin": "Maluku Islands, Indonesia", "country": "Indonesia",
     "lat": -2.5000, "lon": 128.0000,
     "detail": "Spice Islands (Moluccas); caused European colonial wars; now also grown in Madagascar and Zanzibar",
     "trade_value_usd": 450000000},
    {"spice": "Nutmeg & Mace", "origin": "Banda Islands, Indonesia", "country": "Indonesia",
     "lat": -4.5250, "lon": 129.8950,
     "detail": "Once worth more than gold; Dutch massacred Bandanese for monopoly control (1621)",
     "trade_value_usd": 380000000},
    {"spice": "Star Anise", "origin": "Guangxi, China", "country": "China",
     "lat": 23.7248, "lon": 108.3200,
     "detail": "Key ingredient in Chinese five-spice and Vietnamese pho; source of shikimic acid (Tamiflu)",
     "trade_value_usd": 250000000},
    {"spice": "Cumin", "origin": "Eastern Mediterranean", "country": "Syria",
     "lat": 34.8021, "lon": 38.9968,
     "detail": "Essential to Middle Eastern, Indian, and Mexican cuisines; mentioned in the Bible",
     "trade_value_usd": 400000000},
    {"spice": "Chili Pepper", "origin": "Puebla, Mexico", "country": "Mexico",
     "lat": 19.0414, "lon": -98.2063,
     "detail": "Domesticated 7,500 years ago; Columbus brought to Europe; now global staple via Columbian Exchange",
     "trade_value_usd": 3000000000},
    {"spice": "Ginger", "origin": "Southeast Asia", "country": "China",
     "lat": 23.1291, "lon": 113.2644,
     "detail": "Confucius mentioned ginger 2,500 years ago; India and China dominate production",
     "trade_value_usd": 700000000},
    {"spice": "Paprika", "origin": "Central Mexico / Hungary", "country": "Hungary",
     "lat": 46.2530, "lon": 20.1414,
     "detail": "Christopher Columbus brought peppers to Spain; Hungary made paprika central to cuisine (16th C)",
     "trade_value_usd": 350000000},
    {"spice": "Sumac", "origin": "Middle East", "country": "Lebanon",
     "lat": 33.8547, "lon": 35.8623,
     "detail": "Tart red berry ground to powder; essential in za'atar; used before lemons reached the region",
     "trade_value_usd": 80000000},
    {"spice": "Wasabi", "origin": "Shizuoka, Japan", "country": "Japan",
     "lat": 34.9769, "lon": 138.3831,
     "detail": "Grows in mountain stream beds; real wasabi is rare and expensive; most 'wasabi' is dyed horseradish",
     "trade_value_usd": 120000000},
]

# --- Mode 8: Beer & Brewing ---
BEER_DATA = [
    {"name": "Westvleteren Brewery", "type": "Trappist", "country": "Belgium",
     "city": "Vleteren", "lat": 50.8885, "lon": 2.7227,
     "detail": "Westvleteren 12 — often rated world's best beer; only sold at monastery gate",
     "founded": 1838},
    {"name": "Bamberg", "type": "Rauchbier (Smoke Beer)", "country": "Germany",
     "city": "Bamberg", "lat": 49.8988, "lon": 10.9028,
     "detail": "9 traditional breweries; smoked malt Rauchbier; UNESCO World Heritage old town",
     "founded": 1122},
    {"name": "Plzen (Pilsen)", "type": "Pilsner Origin", "country": "Czech Republic",
     "city": "Plzen", "lat": 49.7384, "lon": 13.3736,
     "detail": "Pilsner Urquell (1842) — first pale lager; Czech Republic has highest beer consumption per capita",
     "founded": 1842},
    {"name": "Munich — Hofbrauhaus", "type": "Reinheitsgebot Heritage", "country": "Germany",
     "city": "Munich", "lat": 48.1375, "lon": 11.5799,
     "detail": "Reinheitsgebot (1516) purity law; Oktoberfest serves 7 million litres annually",
     "founded": 1589},
    {"name": "Burton upon Trent", "type": "Pale Ale Origin", "country": "United Kingdom",
     "city": "Burton upon Trent", "lat": 52.8021, "lon": -1.6270,
     "detail": "Gypsum-rich water ideal for pale ales; 'Burtonisation' process; Bass Brewery (1777)",
     "founded": 1744},
    {"name": "Dublin — Guinness Storehouse", "type": "Stout Heritage", "country": "Ireland",
     "city": "Dublin", "lat": 53.3418, "lon": -6.2868,
     "detail": "Arthur Guinness signed 9,000-year lease (1759); St. James's Gate brewery; 10M glasses/day",
     "founded": 1759},
    {"name": "Portland, Oregon", "type": "Craft Beer Capital", "country": "USA",
     "city": "Portland", "lat": 45.5051, "lon": -122.6750,
     "detail": "75+ breweries within city limits; 'Beervana'; pioneered American craft hop-forward styles",
     "founded": 1984},
    {"name": "Bruges", "type": "Belgian Beer Heritage", "country": "Belgium",
     "city": "Bruges", "lat": 51.2094, "lon": 3.2247,
     "detail": "De Halve Maan brewery has underground beer pipeline; Belgian beer culture is UNESCO heritage",
     "founded": 1564},
    {"name": "Abbey of Notre-Dame d'Orval", "type": "Trappist", "country": "Belgium",
     "city": "Villers-devant-Orval", "lat": 49.6367, "lon": 5.3486,
     "detail": "Orval — dry-hopped Trappist ale with Brettanomyces yeast; unique bottle shape",
     "founded": 1931},
    {"name": "Rochefort Brewery", "type": "Trappist", "country": "Belgium",
     "city": "Rochefort", "lat": 50.1597, "lon": 5.2214,
     "detail": "Rochefort 10 — dark, complex quad; brewed by monks since 1595",
     "founded": 1595},
    {"name": "Cologne", "type": "Kolsch", "country": "Germany",
     "city": "Cologne", "lat": 50.9375, "lon": 6.9603,
     "detail": "Kolsch is a protected appellation; only breweries in Cologne may use the name",
     "founded": 1396},
    {"name": "Cantillon Brewery", "type": "Lambic (Spontaneous Ferment)", "country": "Belgium",
     "city": "Brussels", "lat": 50.8439, "lon": 4.3369,
     "detail": "Wild yeast lambic fermentation; gueuze and kriek; open coolship exposed to Brussels air",
     "founded": 1900},
    {"name": "Tokyo — Craft Beer Scene", "type": "Asian Craft Capital", "country": "Japan",
     "city": "Tokyo", "lat": 35.6762, "lon": 139.6503,
     "detail": "Japan legalised microbrewing in 1994; unique rice lagers and yuzu ales; 200+ craft breweries",
     "founded": 1994},
    {"name": "Trappistes de Chimay", "type": "Trappist", "country": "Belgium",
     "city": "Chimay", "lat": 50.0489, "lon": 4.3164,
     "detail": "Chimay Blue (Grande Reserve) — classic Belgian Trappist; first commercial Trappist ale",
     "founded": 1862},
    {"name": "Einbeck", "type": "Bock Beer Origin", "country": "Germany",
     "city": "Einbeck", "lat": 51.8175, "lon": 9.8656,
     "detail": "Original bock beer town (14th C); 'ein Bock' corrupted to 'ein Bock' (a goat) — hence goat logo",
     "founded": 1351},
]

# --- Mode 9: UNESCO Intangible Food Heritage ---
UNESCO_FOOD = [
    {"tradition": "French Gastronomic Meal", "country": "France", "year_inscribed": 2010,
     "lat": 48.8566, "lon": 2.3522,
     "detail": "Multi-course meal celebrating important moments; specific structure from aperitif to digestif"},
    {"tradition": "Mediterranean Diet", "country": "Spain, Italy, Greece, Morocco, Croatia, Cyprus, Portugal",
     "year_inscribed": 2013, "lat": 39.4699, "lon": -0.3763,
     "detail": "Olive oil, grains, fish, vegetables; shared table culture; health benefits well-documented"},
    {"tradition": "Washoku — Traditional Japanese Cuisine", "country": "Japan",
     "year_inscribed": 2013, "lat": 35.6762, "lon": 139.6503,
     "detail": "Respect for nature; seasonal ingredients; rice, miso, and fish; New Year osechi-ryori"},
    {"tradition": "Kimjang — Making & Sharing Kimchi", "country": "South Korea",
     "year_inscribed": 2013, "lat": 37.5665, "lon": 126.9780,
     "detail": "Annual communal preparation of kimchi for winter; over 200 varieties; social cohesion"},
    {"tradition": "Traditional Mexican Cuisine", "country": "Mexico",
     "year_inscribed": 2010, "lat": 19.4326, "lon": -99.1332,
     "detail": "Corn, beans, and chili trinity; Michoacan cuisine; ancient nixtamalisation of maize"},
    {"tradition": "Turkish Coffee Culture", "country": "Turkey",
     "year_inscribed": 2013, "lat": 41.0082, "lon": 28.9784,
     "detail": "Cezve preparation; fortune-telling from grounds; 'a cup of coffee commits one to forty years of friendship'"},
    {"tradition": "Georgian Qvevri Wine-Making", "country": "Georgia",
     "year_inscribed": 2013, "lat": 41.7151, "lon": 44.8271,
     "detail": "8,000-year-old tradition; clay qvevri vessels buried underground for fermentation"},
    {"tradition": "Nsima — Malawian Culinary Tradition", "country": "Malawi",
     "year_inscribed": 2017, "lat": -13.9626, "lon": 33.7741,
     "detail": "Maize porridge central to daily life; communal eating; method of cooking and sharing"},
    {"tradition": "Belgian Beer Culture", "country": "Belgium",
     "year_inscribed": 2016, "lat": 50.8503, "lon": 4.3517,
     "detail": "1,500+ beer varieties; lambic, Trappist, abbey ales; craft knowledge passed through generations"},
    {"tradition": "Neapolitan Pizzaiuolo Art", "country": "Italy",
     "year_inscribed": 2017, "lat": 40.8518, "lon": 14.2681,
     "detail": "Art of the Neapolitan pizza maker; dough spinning; wood-fired oven at 485C for 90 seconds"},
    {"tradition": "Hawker Culture in Singapore", "country": "Singapore",
     "year_inscribed": 2020, "lat": 1.3521, "lon": 103.8198,
     "detail": "Community dining in hawker centres; multi-ethnic food heritage; affordable gourmet"},
    {"tradition": "Couscous — Knowledge and Practices", "country": "Algeria, Mauritania, Morocco, Tunisia",
     "year_inscribed": 2020, "lat": 34.0331, "lon": -5.0003,
     "detail": "Semolina steamed over stew; communal preparation; North African culinary identity"},
    {"tradition": "Flatbread — Lavash, Katyrma, Jupka, Yufka", "country": "Turkey, Azerbaijan, Iran, Kazakhstan, Kyrgyzstan",
     "year_inscribed": 2016, "lat": 39.9334, "lon": 32.8597,
     "detail": "Thin flatbread traditions across Central Asia and the Middle East; communal baking"},
    {"tradition": "Al-Mansaf — Festive Banquet", "country": "Jordan",
     "year_inscribed": 2022, "lat": 31.9454, "lon": 35.9284,
     "detail": "Lamb cooked in fermented dried yoghurt (jameed); served on rice; symbol of generosity"},
    {"tradition": "Oshi Palav — Uzbek Pilaf", "country": "Uzbekistan",
     "year_inscribed": 2016, "lat": 41.2995, "lon": 69.2401,
     "detail": "Rice, meat, carrots, and spices cooked in a kazan; prepared for weddings and gatherings"},
    {"tradition": "Viniculture of Kvevri (Ancient Wine)", "country": "Georgia",
     "year_inscribed": 2013, "lat": 42.3154, "lon": 43.3569,
     "detail": "World's oldest winemaking tradition; natural wines fermented in buried clay vessels"},
    {"tradition": "Peking Duck Preparation", "country": "China",
     "year_inscribed": 2021, "lat": 39.9042, "lon": 116.4074,
     "detail": "Imperial dish with 700+ years of history; air-dried and roasted; sliced at the table"},
]

# --- Mode 10: Superfoods & Ancient Grains ---
SUPERFOOD_DATA = [
    {"name": "Quinoa", "type": "Ancient Grain", "origin": "Andes, Peru/Bolivia",
     "country": "Peru", "lat": -15.5000, "lon": -70.0000,
     "detail": "Sacred grain of the Inca ('mother of all grains'); complete protein; grows above 3,500 m",
     "cultivation_years": 5000},
    {"name": "Acai Berry", "type": "Superfruit", "origin": "Amazon Basin, Brazil",
     "country": "Brazil", "lat": -1.4558, "lon": -48.5024,
     "detail": "Acai palm fruit; high anthocyanins; staple of Para state; $2B global market",
     "cultivation_years": 3000},
    {"name": "Turmeric", "type": "Medicinal Spice", "origin": "Southern India",
     "country": "India", "lat": 11.1271, "lon": 78.6569,
     "detail": "Curcumin anti-inflammatory; Ayurvedic medicine for 4,000 years; India produces 80%",
     "cultivation_years": 4000},
    {"name": "Teff", "type": "Ancient Grain", "origin": "Ethiopian Highlands",
     "country": "Ethiopia", "lat": 9.1450, "lon": 40.4897,
     "detail": "Tiny grain (0.7 mm); used for injera flatbread; gluten-free; high iron content",
     "cultivation_years": 5000},
    {"name": "Chia Seeds", "type": "Ancient Seed", "origin": "Central Mexico",
     "country": "Mexico", "lat": 19.4326, "lon": -99.1332,
     "detail": "Aztec warrior superfuel; omega-3 rich; 'chia' means 'strength' in Nahuatl",
     "cultivation_years": 3500},
    {"name": "Goji Berry", "type": "Medicinal Berry", "origin": "Ningxia, China",
     "country": "China", "lat": 38.4715, "lon": 106.2590,
     "detail": "Lycium barbarum; Chinese medicine for 2,000 years; dried berries rich in zeaxanthin",
     "cultivation_years": 2000},
    {"name": "Moringa", "type": "Miracle Tree", "origin": "Sub-Himalayan India",
     "country": "India", "lat": 30.3165, "lon": 78.0322,
     "detail": "Leaves contain 7x vitamin C of oranges; drought-resistant; used in 80+ countries",
     "cultivation_years": 4000},
    {"name": "Amaranth", "type": "Ancient Grain", "origin": "Mesoamerica",
     "country": "Mexico", "lat": 19.3260, "lon": -99.1707,
     "detail": "Aztec staple banned by Conquistadors (used in rituals); high lysine; gluten-free",
     "cultivation_years": 8000},
    {"name": "Spirulina", "type": "Blue-Green Algae", "origin": "Lake Chad, Chad / Lake Texcoco, Mexico",
     "country": "Chad", "lat": 13.4549, "lon": 14.0467,
     "detail": "Aztecs and Kanembu people harvested independently; 60% protein; NASA space food candidate",
     "cultivation_years": 1000},
    {"name": "Maca Root", "type": "Adaptogen Root", "origin": "Junin Plateau, Peru",
     "country": "Peru", "lat": -11.1586, "lon": -75.9931,
     "detail": "Grows at 4,000 m; Incan warriors consumed before battle; adaptogenic properties",
     "cultivation_years": 3800},
    {"name": "Baobab Fruit", "type": "Superfruit", "origin": "Sub-Saharan Africa",
     "country": "Senegal", "lat": 14.4974, "lon": -14.4524,
     "detail": "Tree of Life; fruit has 6x vitamin C of oranges; powder used in smoothies globally",
     "cultivation_years": 2000},
    {"name": "Camu Camu", "type": "Superfruit", "origin": "Amazon Rainforest, Peru",
     "country": "Peru", "lat": -4.0000, "lon": -73.0000,
     "detail": "Highest natural vitamin C concentration of any fruit (2,800 mg/100g); Amazonian riverside shrub",
     "cultivation_years": 1500},
    {"name": "Fonio", "type": "Ancient Grain", "origin": "West Africa (Sahel)",
     "country": "Mali", "lat": 12.6392, "lon": -8.0029,
     "detail": "Digitaria exilis; oldest cereal in West Africa; drought-tolerant; pre-dates rice cultivation in Africa",
     "cultivation_years": 7000},
    {"name": "Cacao Nibs", "type": "Superfood", "origin": "Mesoamerica",
     "country": "Mexico", "lat": 17.8409, "lon": -92.6189,
     "detail": "Raw cacao is rich in flavanols and magnesium; Mayan 'food of the gods'",
     "cultivation_years": 3900},
    {"name": "Hemp Seeds", "type": "Ancient Seed", "origin": "Central Asia",
     "country": "Kazakhstan", "lat": 43.2551, "lon": 76.9126,
     "detail": "Cannabis sativa; complete protein; cultivated since 8,000 BC; omega fatty acid balance",
     "cultivation_years": 10000},
]


# ═══════════════════════════════════════════════════════════════
# HELPER — BUILD FOLIUM MAP
# ═══════════════════════════════════════════════════════════════

def _build_map(data: list, lat_key: str, lon_key: str, label_key: str,
               popup_fields: dict, color: str, center: tuple = None,
               zoom: int = 2, circle_radius: int = 7) -> folium.Map:
    """Build a dark-themed folium map from a list of dicts."""
    if center is None:
        if data:
            center = (
                sum(d[lat_key] for d in data) / len(data),
                sum(d[lon_key] for d in data) / len(data),
            )
        else:
            center = (20, 0)

    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    for item in data:
        popup_lines = []
        for label, key in popup_fields.items():
            val = item.get(key, "")
            if val not in (None, "", 0, "0"):
                popup_lines.append(
                    f"<b>{escape(str(label))}:</b> {escape(str(val))}"
                )
        popup_html = (
            f'<div style="max-width:280px; font-size:0.85rem;">'
            f'<strong>{escape(str(item.get(label_key, "Unknown")))}</strong><br/>'
            + "<br/>".join(popup_lines)
            + "</div>"
        )
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=circle_radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(item.get(label_key, ""))),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def _build_ranked_map(data: list, lat_key: str, lon_key: str, label_key: str,
                      rank_key: str, popup_fields: dict, color: str,
                      center: tuple = None, zoom: int = 2) -> folium.Map:
    """Build map with rank-scaled markers (larger value = larger circle)."""
    if center is None:
        if data:
            center = (
                sum(d[lat_key] for d in data) / len(data),
                sum(d[lon_key] for d in data) / len(data),
            )
        else:
            center = (20, 0)

    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    if data:
        max_val = max(abs(d.get(rank_key, 1)) for d in data) or 1
    else:
        max_val = 1

    for i, item in enumerate(data):
        val = abs(item.get(rank_key, 0))
        radius = max(5, int(4 + 14 * (val / max_val)))

        popup_lines = [f"<b>Rank:</b> #{i + 1}"]
        for label, key in popup_fields.items():
            v = item.get(key, "")
            if v not in (None, "", 0, "0"):
                popup_lines.append(f"<b>{escape(str(label))}:</b> {escape(str(v))}")
        popup_html = (
            f'<div style="max-width:280px; font-size:0.85rem;">'
            f'<strong>{escape(str(item.get(label_key, "Unknown")))}</strong><br/>'
            + "<br/>".join(popup_lines)
            + "</div>"
        )
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.65,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"#{i+1} {escape(str(item.get(label_key, '')))}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════
# HELPER — STATS ROW
# ═══════════════════════════════════════════════════════════════

def _show_stats(metrics: list):
    """Display metric cards in columns. metrics = [(label, value), ...]"""
    cols = st.columns(min(len(metrics), 5))
    for i, (label, value) in enumerate(metrics):
        cols[i % len(cols)].metric(label, value)


# ═══════════════════════════════════════════════════════════════
# HELPER — HORIZONTAL BAR CHART
# ═══════════════════════════════════════════════════════════════

def _bar_chart(labels: list, values: list, color: str, xlabel: str, title: str = ""):
    """Draw a dark-themed horizontal bar chart."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, max(3, 0.35 * len(labels))))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color=color, alpha=0.85, edgecolor=color, linewidth=0.5)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([str(l)[:35] for l in labels], color="#e8ecf4", fontsize=9)
    ax.set_xlabel(xlabel, color="#e8ecf4", fontsize=10)
    if title:
        ax.set_title(title, color="#e8ecf4", fontsize=11, pad=8)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    import matplotlib.pyplot as _plt
    _plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# HELPER — DOWNLOAD SECTION
# ═══════════════════════════════════════════════════════════════

def _download_section(df: pd.DataFrame, filename: str, label: str, key: str):
    """Expander with dataframe and CSV download."""
    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label,
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


# ═══════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_cuisine_origins():
    """Mode 1: World Cuisine Origins."""
    data = sorted(CUISINE_ORIGINS, key=lambda x: x["year"])

    countries = list(set(d["country"] for d in data))
    oldest = min(data, key=lambda x: x["year"])
    newest = max(data, key=lambda x: x["year"])

    _show_stats([
        ("Dishes Mapped", len(data)),
        ("Countries", len(countries)),
        ("Oldest Dish", f"{oldest['dish']} ({oldest['year']})"),
        ("Newest Dish", f"{newest['dish']} ({newest['year']})"),
    ])

    st.markdown("---")
    st.markdown("#### World Cuisine Origins Map")

    m = _build_map(
        data, "lat", "lon", "dish",
        popup_fields={"Origin City": "origin_city", "Country": "country",
                       "Year": "year", "Notes": "notes"},
        color="#f97316", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Dish Origins by Year")
    chart_data = sorted(data, key=lambda x: x["year"], reverse=True)[:20]
    _bar_chart(
        [d["dish"] for d in chart_data],
        [d["year"] for d in chart_data],
        "#f97316", "Year of Origin / First Documentation",
        title="When Were These Dishes Born?",
    )

    df = pd.DataFrame([{
        "Dish": d["dish"], "Origin City": d["origin_city"],
        "Country": d["country"], "Year": d["year"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Notes": d["notes"],
    } for d in data])
    _download_section(df, "cuisine_origins.csv",
                      f"Download {len(df)} Cuisine Origins (CSV)", "dl_cuisine_origins")


def _render_michelin():
    """Mode 2: Michelin Star Restaurants."""
    data = sorted(MICHELIN_CITIES, key=lambda x: x["total_stars"], reverse=True)

    total_stars = sum(d["total_stars"] for d in data)
    total_3star = sum(d["three_star"] for d in data)
    top_city = data[0]

    _show_stats([
        ("Cities Tracked", len(data)),
        ("Total Stars", f"{total_stars:,}"),
        ("3-Star Restaurants", total_3star),
        ("Top City", f"{top_city['city']} ({top_city['total_stars']})"),
        ("Countries", len(set(d["country"] for d in data))),
    ])

    st.markdown("---")
    st.markdown("#### Michelin Star Cities Map")

    m = _build_ranked_map(
        data, "lat", "lon", "city", "total_stars",
        popup_fields={"Country": "country", "Total Stars": "total_stars",
                       "3-Star Restaurants": "three_star", "Notes": "notes"},
        color="#ef4444", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Stars by City")
    _bar_chart(
        [d["city"] for d in data[:15]],
        [d["total_stars"] for d in data[:15]],
        "#ef4444", "Total Michelin Stars",
        title="Cities with Most Michelin Stars",
    )

    df = pd.DataFrame([{
        "City": d["city"], "Country": d["country"],
        "Total Stars": d["total_stars"], "3-Star Count": d["three_star"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Notes": d["notes"],
    } for d in data])
    _download_section(df, "michelin_cities.csv",
                      f"Download {len(df)} Michelin Cities (CSV)", "dl_michelin")


def _render_street_food():
    """Mode 3: Street Food Capitals."""
    data = sorted(STREET_FOOD, key=lambda x: x["vendors_est"], reverse=True)

    total_vendors = sum(d["vendors_est"] for d in data)
    top_city = data[0]

    _show_stats([
        ("Cities Mapped", len(data)),
        ("Est. Total Vendors", f"{total_vendors:,}"),
        ("Top City", f"{top_city['city']}"),
        ("Top Vendor Count", f"{top_city['vendors_est']:,}"),
        ("Countries", len(set(d["country"] for d in data))),
    ])

    st.markdown("---")
    st.markdown("#### Street Food Capitals Map")

    m = _build_ranked_map(
        data, "lat", "lon", "city", "vendors_est",
        popup_fields={"Country": "country", "Specialty": "specialty",
                       "Est. Vendors": "vendors_est", "Notes": "notes"},
        color="#f59e0b", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Estimated Street Food Vendors by City")
    _bar_chart(
        [d["city"] for d in data],
        [d["vendors_est"] for d in data],
        "#f59e0b", "Estimated Vendors",
        title="Street Food Vendor Density",
    )

    df = pd.DataFrame([{
        "City": d["city"], "Country": d["country"],
        "Specialty Dishes": d["specialty"],
        "Estimated Vendors": d["vendors_est"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Notes": d["notes"],
    } for d in data])
    _download_section(df, "street_food_capitals.csv",
                      f"Download {len(df)} Street Food Capitals (CSV)", "dl_streetfood")


def _render_coffee():
    """Mode 4: Coffee Origins & Culture."""
    data = COFFEE_DATA

    producers = [d for d in data if d["production_mt"] > 0]
    culture_hubs = [d for d in data if d["production_mt"] == 0]
    total_production = sum(d["production_mt"] for d in producers)

    _show_stats([
        ("Locations Mapped", len(data)),
        ("Producer Regions", len(producers)),
        ("Cafe Culture Hubs", len(culture_hubs)),
        ("Total Production", f"{total_production:,.0f} MT"),
        ("Countries", len(set(d["country"] for d in data))),
    ])

    st.markdown("---")
    st.markdown("#### Coffee World Map")

    # Color-code: brown for producers, cyan for culture hubs
    m = folium.Map(location=[15, 20], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    for item in data:
        is_producer = item["production_mt"] > 0
        clr = "#a16207" if is_producer else "#06b6d4"
        radius = max(5, int(4 + 12 * (item["production_mt"] / 3800000))) if is_producer else 7

        popup_html = (
            f'<div style="max-width:280px; font-size:0.85rem;">'
            f'<strong>{escape(item["name"])}</strong><br/>'
            f'<b>Type:</b> {escape(item["type"])}<br/>'
            f'<b>Country:</b> {escape(item["country"])}<br/>'
        )
        if is_producer:
            prod_val = f'{item["production_mt"]:,}'
            popup_html += f'<b>Production:</b> {escape(prod_val)} MT<br/>'
        popup_html += f'<b>Detail:</b> {escape(item["detail"])}</div>'

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius,
            color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(item["name"]),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Legend
    st.markdown(
        '<div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-top:0.25rem;">'
        '<span style="color:#a16207; font-size:0.85rem;">&#9679; Producer Region</span>'
        '<span style="color:#06b6d4; font-size:0.85rem;">&#9679; Cafe Culture Hub</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### Coffee Production by Region")
    prod_sorted = sorted(producers, key=lambda x: x["production_mt"], reverse=True)
    _bar_chart(
        [d["name"] for d in prod_sorted],
        [d["production_mt"] for d in prod_sorted],
        "#a16207", "Production (Metric Tonnes)",
        title="Coffee Production by Region",
    )

    df = pd.DataFrame([{
        "Name": d["name"], "Type": d["type"], "Country": d["country"],
        "Production (MT)": d["production_mt"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Detail": d["detail"],
    } for d in data])
    _download_section(df, "coffee_origins.csv",
                      f"Download {len(df)} Coffee Locations (CSV)", "dl_coffee")


def _render_tea():
    """Mode 5: Tea Traditions."""
    data = TEA_DATA

    countries = list(set(d["country"] for d in data))
    traditions = list(set(d["tradition"] for d in data))

    _show_stats([
        ("Locations Mapped", len(data)),
        ("Countries", len(countries)),
        ("Distinct Traditions", len(traditions)),
        ("Tea Types", len(set(d["type"] for d in data))),
    ])

    st.markdown("---")
    st.markdown("#### Tea Traditions World Map")

    # Color by type
    type_colors = {
        "Origin of Tea": "#10b981",
        "Oolong & White Tea": "#06b6d4",
        "Matcha Production": "#22c55e",
        "Sencha Region": "#84cc16",
        "Champagne of Teas": "#f59e0b",
        "Black Tea": "#ef4444",
        "Ceylon Tea": "#f97316",
        "Afternoon Tea": "#8b5cf6",
        "Maghrebi Mint Tea": "#14b8a6",
        "Cay (Black Tea)": "#ec4899",
        "Longjing (Dragon Well)": "#a3e635",
        "High Mountain Oolong": "#06b6d4",
        "Turkish Black Tea": "#ec4899",
        "Chai Capital": "#f59e0b",
        "Purple Tea": "#a855f7",
    }

    m = folium.Map(location=[30, 60], zoom_start=3, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    for item in data:
        clr = type_colors.get(item["type"], "#10b981")
        popup_html = (
            f'<div style="max-width:280px; font-size:0.85rem;">'
            f'<strong>{escape(item["name"])}</strong><br/>'
            f'<b>Type:</b> {escape(item["type"])}<br/>'
            f'<b>Tradition:</b> {escape(item["tradition"])}<br/>'
            f'<b>Country:</b> {escape(item["country"])}<br/>'
            f'<b>Detail:</b> {escape(item["detail"])}</div>'
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(item["name"]),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame([{
        "Location": d["name"], "Tea Type": d["type"],
        "Tradition": d["tradition"], "Country": d["country"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Detail": d["detail"],
    } for d in data])
    _download_section(df, "tea_traditions.csv",
                      f"Download {len(df)} Tea Traditions (CSV)", "dl_tea")


def _render_chocolate():
    """Mode 6: Chocolate & Cacao."""
    data = CHOCOLATE_DATA

    producers = [d for d in data if "Producer" in d["type"] or "Cacao" in d["type"]
                 or "Birthplace" in d["type"] or "Organic" in d["type"]
                 or "Island" in d["type"] or "Heirloom" in d["type"]
                 or "Specialty" in d["type"] or "Chuncho" in d["type"]]
    chocolatiers = [d for d in data if "Chocolatier" in d["type"] or "Swiss" in d["type"]
                    or "Historic" in d["type"] or "Heritage" in d["type"]
                    or "Gianduja" in d["type"] or "Traditional" in d["type"]]

    _show_stats([
        ("Locations Mapped", len(data)),
        ("Cacao Regions", len(producers)),
        ("Chocolate Centres", len(chocolatiers)),
        ("Countries", len(set(d["country"] for d in data))),
    ])

    st.markdown("---")
    st.markdown("#### Chocolate & Cacao World Map")

    m = folium.Map(location=[10, 10], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    for item in data:
        is_production = any(kw in item["type"] for kw in
                            ["Producer", "Cacao", "Birthplace", "Organic", "Heirloom",
                             "Specialty", "Chuncho", "Island"])
        clr = "#92400e" if is_production else "#a855f7"

        popup_html = (
            f'<div style="max-width:280px; font-size:0.85rem;">'
            f'<strong>{escape(item["name"])}</strong><br/>'
            f'<b>Type:</b> {escape(item["type"])}<br/>'
            f'<b>Country:</b> {escape(item["country"])}<br/>'
            f'<b>Detail:</b> {escape(item["detail"])}</div>'
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(item["name"]),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        '<div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-top:0.25rem;">'
        '<span style="color:#92400e; font-size:0.85rem;">&#9679; Cacao Production</span>'
        '<span style="color:#a855f7; font-size:0.85rem;">&#9679; Chocolate Heritage</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame([{
        "Name": d["name"], "Type": d["type"], "Country": d["country"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Detail": d["detail"],
    } for d in data])
    _download_section(df, "chocolate_cacao.csv",
                      f"Download {len(df)} Chocolate & Cacao Locations (CSV)", "dl_chocolate")


def _render_spice_routes():
    """Mode 7: Spice Routes & Origins."""
    data = sorted(SPICE_DATA, key=lambda x: x["trade_value_usd"], reverse=True)

    total_trade = sum(d["trade_value_usd"] for d in data)
    top_spice = data[0]

    _show_stats([
        ("Spices Mapped", len(data)),
        ("Countries", len(set(d["country"] for d in data))),
        ("Top Spice", top_spice["spice"]),
        ("Total Trade", f"${total_trade / 1e9:.1f}B"),
    ])

    st.markdown("---")
    st.markdown("#### Spice Origins World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "spice", "trade_value_usd",
        popup_fields={"Origin": "origin", "Country": "country",
                       "Trade Value": "trade_value_usd", "Detail": "detail"},
        color="#ec4899", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Spice Trade Value")
    _bar_chart(
        [d["spice"] for d in data],
        [d["trade_value_usd"] / 1e6 for d in data],
        "#ec4899", "Annual Trade Value ($ Millions)",
        title="Global Spice Trade Value",
    )

    df = pd.DataFrame([{
        "Spice": d["spice"], "Origin": d["origin"], "Country": d["country"],
        "Trade Value (USD)": d["trade_value_usd"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Detail": d["detail"],
    } for d in data])
    _download_section(df, "spice_routes.csv",
                      f"Download {len(df)} Spice Origins (CSV)", "dl_spices")


def _render_beer():
    """Mode 8: Beer & Brewing."""
    data = sorted(BEER_DATA, key=lambda x: x["founded"])

    countries = list(set(d["country"] for d in data))
    oldest = data[0]
    types = list(set(d["type"] for d in data))
    trappist_count = sum(1 for d in data if "Trappist" in d["type"])

    _show_stats([
        ("Breweries/Sites", len(data)),
        ("Countries", len(countries)),
        ("Beer Styles", len(types)),
        ("Trappist Entries", trappist_count),
        ("Oldest", f"{oldest['name']} ({oldest['founded']})"),
    ])

    st.markdown("---")
    st.markdown("#### Beer & Brewing Heritage Map")

    # Color by type category
    beer_type_colors = {
        "Trappist": "#f59e0b",
        "Pilsner Origin": "#eab308",
        "Reinheitsgebot Heritage": "#f97316",
        "Pale Ale Origin": "#06b6d4",
        "Stout Heritage": "#1a1a2e",
        "Craft Beer Capital": "#10b981",
        "Belgian Beer Heritage": "#ec4899",
        "Lambic (Spontaneous Ferment)": "#a855f7",
        "Rauchbier (Smoke Beer)": "#92400e",
        "Kolsch": "#3b82f6",
        "Asian Craft Capital": "#14b8a6",
        "Bock Beer Origin": "#ef4444",
    }

    m = folium.Map(location=[48, 10], zoom_start=4, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    for item in data:
        clr = beer_type_colors.get(item["type"], "#eab308")
        popup_html = (
            f'<div style="max-width:280px; font-size:0.85rem;">'
            f'<strong>{escape(item["name"])}</strong><br/>'
            f'<b>Style:</b> {escape(item["type"])}<br/>'
            f'<b>City:</b> {escape(item["city"])}<br/>'
            f'<b>Country:</b> {escape(item["country"])}<br/>'
            f'<b>Founded:</b> {escape(str(item["founded"]))}<br/>'
            f'<b>Detail:</b> {escape(item["detail"])}</div>'
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=9,
            color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(item["name"]),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Legend for beer types
    legend_html = " ".join(
        f'<span style="color:{c}; font-size:0.8rem;">&#9679; {escape(t)}</span>'
        for t, c in beer_type_colors.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-top:0.25rem;">{legend_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### Breweries by Founding Year")
    _bar_chart(
        [d["name"] for d in data],
        [d["founded"] for d in data],
        "#eab308", "Year Founded",
        title="Brewery & Beer Heritage Timeline",
    )

    df = pd.DataFrame([{
        "Name": d["name"], "Type": d["type"], "City": d["city"],
        "Country": d["country"], "Founded": d["founded"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Detail": d["detail"],
    } for d in data])
    _download_section(df, "beer_brewing.csv",
                      f"Download {len(df)} Beer & Brewing Sites (CSV)", "dl_beer")


def _render_unesco_food():
    """Mode 9: UNESCO Intangible Food Heritage."""
    data = sorted(UNESCO_FOOD, key=lambda x: x["year_inscribed"])

    countries_all = set()
    for d in data:
        for c in d["country"].split(", "):
            countries_all.add(c.strip())

    _show_stats([
        ("Traditions Listed", len(data)),
        ("Countries Involved", len(countries_all)),
        ("Earliest Inscription", min(d["year_inscribed"] for d in data)),
        ("Latest Inscription", max(d["year_inscribed"] for d in data)),
    ])

    st.markdown("---")
    st.markdown("#### UNESCO Food Heritage Map")

    m = _build_map(
        data, "lat", "lon", "tradition",
        popup_fields={"Country": "country", "Year Inscribed": "year_inscribed",
                       "Detail": "detail"},
        color="#3b82f6", zoom=2, circle_radius=9,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Inscriptions by Year")

    # Group by year
    year_counts = {}
    for d in data:
        yr = d["year_inscribed"]
        year_counts[yr] = year_counts.get(yr, 0) + 1
    years_sorted = sorted(year_counts.keys())
    _bar_chart(
        [str(y) for y in years_sorted],
        [year_counts[y] for y in years_sorted],
        "#3b82f6", "Number of Inscriptions",
        title="UNESCO Food Heritage Inscriptions by Year",
    )

    df = pd.DataFrame([{
        "Tradition": d["tradition"], "Country": d["country"],
        "Year Inscribed": d["year_inscribed"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Detail": d["detail"],
    } for d in data])
    _download_section(df, "unesco_food_heritage.csv",
                      f"Download {len(df)} UNESCO Food Traditions (CSV)", "dl_unesco_food")


def _render_superfoods():
    """Mode 10: Superfoods & Ancient Grains."""
    data = sorted(SUPERFOOD_DATA, key=lambda x: x["cultivation_years"], reverse=True)

    types = list(set(d["type"] for d in data))
    oldest = data[0]
    avg_years = sum(d["cultivation_years"] for d in data) // len(data)

    _show_stats([
        ("Superfoods Mapped", len(data)),
        ("Categories", len(types)),
        ("Countries", len(set(d["country"] for d in data))),
        ("Oldest", f"{oldest['name']} ({oldest['cultivation_years']:,} yr)"),
        ("Avg. Cultivation", f"{avg_years:,} years"),
    ])

    st.markdown("---")
    st.markdown("#### Superfoods & Ancient Grains Map")

    # Color by type
    sf_colors = {
        "Ancient Grain": "#10b981",
        "Superfruit": "#a855f7",
        "Medicinal Spice": "#f59e0b",
        "Ancient Seed": "#06b6d4",
        "Medicinal Berry": "#ef4444",
        "Miracle Tree": "#22c55e",
        "Blue-Green Algae": "#3b82f6",
        "Adaptogen Root": "#ec4899",
        "Superfood": "#92400e",
    }

    m = folium.Map(location=[10, 0], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    for item in data:
        clr = sf_colors.get(item["type"], "#06b6d4")
        popup_html = (
            f'<div style="max-width:280px; font-size:0.85rem;">'
            f'<strong>{escape(item["name"])}</strong><br/>'
            f'<b>Type:</b> {escape(item["type"])}<br/>'
            f'<b>Origin:</b> {escape(item["origin"])}<br/>'
            f'<b>Country:</b> {escape(item["country"])}<br/>'
            f'<b>Cultivated:</b> {escape(str(item["cultivation_years"]))} years<br/>'
            f'<b>Detail:</b> {escape(item["detail"])}</div>'
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=9,
            color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(item["name"]),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Legend
    legend_html = " ".join(
        f'<span style="color:{c}; font-size:0.8rem;">&#9679; {escape(t)}</span>'
        for t, c in sf_colors.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-top:0.25rem;">{legend_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### Cultivation History (Years)")
    _bar_chart(
        [d["name"] for d in data],
        [d["cultivation_years"] for d in data],
        "#06b6d4", "Years of Cultivation",
        title="How Ancient Are These Superfoods?",
    )

    df = pd.DataFrame([{
        "Name": d["name"], "Type": d["type"], "Origin": d["origin"],
        "Country": d["country"], "Cultivation Years": d["cultivation_years"],
        "Latitude": d["lat"], "Longitude": d["lon"],
        "Detail": d["detail"],
    } for d in data])
    _download_section(df, "superfoods_ancient_grains.csv",
                      f"Download {len(df)} Superfoods & Ancient Grains (CSV)", "dl_superfoods")


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_cuisine_maps_tab():
    """Main render function for the World Cuisine Explorer tab."""

    # -- Header --
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>\U0001F35C World Cuisine Explorer</h4>'
        '<p>Food origins, culinary traditions, spice routes, Michelin stars & 10 cuisine maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # -- Mode selector --
    st.markdown("#### Explore World Cuisine")
    mode = st.selectbox(
        "Select Cuisine Map Mode",
        MAP_MODES,
        key="cuisine_map_mode",
        help="Choose a culinary category to explore on the map.",
    )

    # -- Mode description --
    color = MODE_COLORS.get(mode, "#f97316")
    desc = MODE_DESCRIPTIONS.get(mode, "")
    st.markdown(
        f'<div style="border-left:3px solid {color}; padding:0.5rem 0.75rem; '
        f'margin:0.5rem 0 1rem; background:rgba(15,23,42,0.4); border-radius:0 6px 6px 0;">'
        f'<span style="color:{color}; font-weight:600;">{escape(mode)}</span><br/>'
        f'<span style="color:#8b97b0; font-size:0.85rem;">{escape(desc)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # -- Dispatch to mode renderer --
    mode_map = {
        "World Cuisine Origins": _render_cuisine_origins,
        "Michelin Star Restaurants": _render_michelin,
        "Street Food Capitals": _render_street_food,
        "Coffee Origins & Culture": _render_coffee,
        "Tea Traditions": _render_tea,
        "Chocolate & Cacao": _render_chocolate,
        "Spice Routes & Origins": _render_spice_routes,
        "Beer & Brewing": _render_beer,
        "UNESCO Intangible Food Heritage": _render_unesco_food,
        "Superfoods & Ancient Grains": _render_superfoods,
    }

    renderer = mode_map.get(mode)
    if renderer:
        renderer()
