# -*- coding: utf-8 -*-
"""
Photography & Camera Explorer module for TerraScout AI.
Provides 10 curated map modes covering the world's most photographed places,
camera manufacturing history, photography museums, iconic landscape spots,
street photography capitals, astrophotography dark-sky sites, and more.
All data is hardcoded -- no external API required.
"""

import io
import html as html_module
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

BG_DARK = "#0a0e1a"
BG_SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
GRID_COLOR = "#2a3550"

ACCENT_CYAN = "#06b6d4"
ACCENT_PINK = "#ec4899"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_EMERALD = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"
ACCENT_TEAL = "#14b8a6"
ACCENT_FUCHSIA = "#d946ef"

MODE_COLORS = {
    "World's Most Photographed Places": ACCENT_PINK,
    "Camera Manufacturing History": ACCENT_AMBER,
    "Photography Museums & Galleries": ACCENT_VIOLET,
    "Famous Photo Locations (National Geographic)": ACCENT_EMERALD,
    "Darkroom & Film Heritage Sites": ACCENT_ORANGE,
    "Iconic Landscape Photography Spots": ACCENT_CYAN,
    "Street Photography Capitals": ACCENT_RED,
    "Astrophotography Dark Sky Sites": ACCENT_BLUE,
    "War Photography Historic Sites": ACCENT_TEAL,
    "Underwater Photography Hotspots": ACCENT_FUCHSIA,
}

# ═══════════════════════════════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════════════════════════════

MOST_PHOTOGRAPHED = [
    {"name": "Eiffel Tower", "lat": 48.8584, "lon": 2.2945, "country": "France", "city": "Paris", "est_photos_m": 120, "category": "Landmark", "note": "Most photographed monument in the world"},
    {"name": "Taj Mahal", "lat": 27.1751, "lon": 78.0421, "country": "India", "city": "Agra", "est_photos_m": 95, "category": "Monument", "note": "UNESCO World Heritage, Mughal architecture masterpiece"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "country": "Peru", "city": "Cusco Region", "est_photos_m": 70, "category": "Archaeological", "note": "Lost City of the Incas, 2430m altitude"},
    {"name": "Grand Canyon South Rim", "lat": 36.0544, "lon": -112.1401, "country": "USA", "city": "Arizona", "est_photos_m": 85, "category": "Natural", "note": "277 miles long, 1 mile deep, 6 million years old"},
    {"name": "Colosseum", "lat": 41.8902, "lon": 12.4922, "country": "Italy", "city": "Rome", "est_photos_m": 90, "category": "Monument", "note": "Largest ancient amphitheatre, built 70-80 AD"},
    {"name": "Statue of Liberty", "lat": 40.6892, "lon": -74.0445, "country": "USA", "city": "New York", "est_photos_m": 80, "category": "Monument", "note": "Gift from France 1886, 93m tall"},
    {"name": "Great Wall of China - Badaling", "lat": 40.4319, "lon": 116.5704, "country": "China", "city": "Beijing", "est_photos_m": 75, "category": "Monument", "note": "21,196 km total length, built over 2000 years"},
    {"name": "Big Ben & Houses of Parliament", "lat": 51.5007, "lon": -0.1246, "country": "UK", "city": "London", "est_photos_m": 72, "category": "Landmark", "note": "Elizabeth Tower, iconic clock since 1859"},
    {"name": "Times Square", "lat": 40.7580, "lon": -73.9855, "country": "USA", "city": "New York", "est_photos_m": 110, "category": "Urban", "note": "Crossroads of the World, 50M annual visitors"},
    {"name": "Sydney Opera House", "lat": -33.8568, "lon": 151.2153, "country": "Australia", "city": "Sydney", "est_photos_m": 65, "category": "Landmark", "note": "Designed by Jorn Utzon, opened 1973"},
    {"name": "Sagrada Familia", "lat": 41.4036, "lon": 2.1744, "country": "Spain", "city": "Barcelona", "est_photos_m": 60, "category": "Landmark", "note": "Gaudi's masterpiece, under construction since 1882"},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "city": "Siem Reap", "est_photos_m": 55, "category": "Archaeological", "note": "Largest religious monument in the world"},
    {"name": "Niagara Falls", "lat": 43.0799, "lon": -79.0747, "country": "USA/Canada", "city": "Ontario/New York", "est_photos_m": 68, "category": "Natural", "note": "Combined flow of 750,000 US gallons/sec"},
    {"name": "Golden Gate Bridge", "lat": 37.8199, "lon": -122.4783, "country": "USA", "city": "San Francisco", "est_photos_m": 75, "category": "Landmark", "note": "1,280m main span, International Orange color"},
    {"name": "Christ the Redeemer", "lat": -22.9519, "lon": -43.2105, "country": "Brazil", "city": "Rio de Janeiro", "est_photos_m": 62, "category": "Monument", "note": "30m Art Deco statue atop Corcovado mountain"},
    {"name": "Petra Treasury", "lat": 30.3285, "lon": 35.4444, "country": "Jordan", "city": "Wadi Musa", "est_photos_m": 45, "category": "Archaeological", "note": "Rose-red city carved into sandstone cliffs"},
    {"name": "Burj Khalifa", "lat": 25.1972, "lon": 55.2744, "country": "UAE", "city": "Dubai", "est_photos_m": 58, "category": "Landmark", "note": "Tallest building in the world at 828m"},
    {"name": "Santorini Caldera", "lat": 36.3932, "lon": 25.4615, "country": "Greece", "city": "Oia", "est_photos_m": 50, "category": "Natural", "note": "Iconic blue domes and white-washed buildings"},
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274, "country": "Japan", "city": "Shizuoka", "est_photos_m": 55, "category": "Natural", "note": "Japan's highest peak 3,776m, sacred mountain"},
    {"name": "Piazza San Marco", "lat": 45.4343, "lon": 12.3388, "country": "Italy", "city": "Venice", "est_photos_m": 48, "category": "Landmark", "note": "Napoleon's 'drawing room of Europe'"},
    {"name": "Tower Bridge", "lat": 51.5055, "lon": -0.0754, "country": "UK", "city": "London", "est_photos_m": 52, "category": "Landmark", "note": "Victorian combined bascule and suspension bridge"},
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678, "country": "Mexico", "city": "Yucatan", "est_photos_m": 42, "category": "Archaeological", "note": "El Castillo pyramid, Mayan civilization"},
    {"name": "Trevi Fountain", "lat": 41.9009, "lon": 12.4833, "country": "Italy", "city": "Rome", "est_photos_m": 55, "category": "Landmark", "note": "Baroque fountain, coins-for-wishes tradition"},
    {"name": "Ha Long Bay", "lat": 20.9101, "lon": 107.1839, "country": "Vietnam", "city": "Quang Ninh", "est_photos_m": 38, "category": "Natural", "note": "1,969 limestone islands, UNESCO site"},
    {"name": "Neuschwanstein Castle", "lat": 47.5576, "lon": 10.7498, "country": "Germany", "city": "Schwangau", "est_photos_m": 44, "category": "Landmark", "note": "Inspired Disney's Sleeping Beauty Castle"},
    {"name": "Pyramids of Giza", "lat": 29.9792, "lon": 31.1342, "country": "Egypt", "city": "Giza", "est_photos_m": 80, "category": "Archaeological", "note": "Last surviving Wonder of the Ancient World"},
    {"name": "Shibuya Crossing", "lat": 35.6595, "lon": 139.7004, "country": "Japan", "city": "Tokyo", "est_photos_m": 46, "category": "Urban", "note": "World's busiest pedestrian crossing"},
    {"name": "Cinque Terre", "lat": 44.1461, "lon": 9.6439, "country": "Italy", "city": "Liguria", "est_photos_m": 40, "category": "Landmark", "note": "Five colorful fishing villages on the Italian Riviera"},
    {"name": "Northern Lights - Tromso", "lat": 69.6492, "lon": 18.9553, "country": "Norway", "city": "Tromso", "est_photos_m": 35, "category": "Natural", "note": "Prime aurora borealis viewing spot above Arctic Circle"},
    {"name": "Banff National Park", "lat": 51.4968, "lon": -115.9281, "country": "Canada", "city": "Alberta", "est_photos_m": 42, "category": "Natural", "note": "Canada's first national park, Lake Louise & Moraine Lake"},
    {"name": "Bagan Temples", "lat": 21.1717, "lon": 94.8585, "country": "Myanmar", "city": "Mandalay Region", "est_photos_m": 30, "category": "Archaeological", "note": "Over 2,000 Buddhist temples and pagodas"},
    {"name": "Amalfi Coast", "lat": 40.6340, "lon": 14.6027, "country": "Italy", "city": "Salerno", "est_photos_m": 38, "category": "Natural", "note": "55km of dramatic cliffside coastline"},
    {"name": "Brandenburg Gate", "lat": 52.5163, "lon": 13.3777, "country": "Germany", "city": "Berlin", "est_photos_m": 40, "category": "Monument", "note": "18th-century neoclassical symbol of German unity"},
    {"name": "Matterhorn", "lat": 45.9763, "lon": 7.6586, "country": "Switzerland", "city": "Zermatt", "est_photos_m": 35, "category": "Natural", "note": "Iconic 4,478m pyramidal peak, Alps landmark"},
    {"name": "Blue Mosque", "lat": 41.0054, "lon": 28.9768, "country": "Turkey", "city": "Istanbul", "est_photos_m": 42, "category": "Landmark", "note": "Six minarets, 20,000 Iznik tiles"},
]

CAMERA_MANUFACTURING = [
    {"name": "Leica Camera AG", "lat": 50.5558, "lon": 8.4947, "country": "Germany", "city": "Wetzlar", "founded": 1914, "specialty": "Rangefinder, M-System", "note": "Ur-Leica prototype 1914, defined 35mm photography"},
    {"name": "Nikon Corporation HQ", "lat": 35.6762, "lon": 139.7340, "country": "Japan", "city": "Tokyo", "founded": 1917, "specialty": "SLR, Mirrorless, Optics", "note": "Originally Nippon Kogaku, NASA space cameras"},
    {"name": "Canon Inc. HQ", "lat": 35.6654, "lon": 139.7248, "country": "Japan", "city": "Tokyo", "founded": 1937, "specialty": "SLR, Mirrorless, Cinema", "note": "World's largest camera manufacturer by revenue"},
    {"name": "Hasselblad AB", "lat": 57.7089, "lon": 11.9746, "country": "Sweden", "city": "Gothenburg", "founded": 1941, "specialty": "Medium Format", "note": "Apollo Moon landing cameras, 500C icon"},
    {"name": "Fujifilm HQ", "lat": 35.6620, "lon": 139.7100, "country": "Japan", "city": "Tokyo", "founded": 1934, "specialty": "Film, Mirrorless, Instax", "note": "Preserved film manufacturing, X-series mirrorless"},
    {"name": "Sony Imaging HQ", "lat": 35.6585, "lon": 139.7414, "country": "Japan", "city": "Tokyo", "founded": 1946, "specialty": "Mirrorless, Sensors", "note": "World's largest image sensor manufacturer"},
    {"name": "Olympus (OM System)", "lat": 35.6891, "lon": 139.6917, "country": "Japan", "city": "Tokyo", "founded": 1919, "specialty": "Micro Four Thirds", "note": "Pioneered half-frame and compact cameras"},
    {"name": "Pentax (Ricoh Imaging)", "lat": 35.6848, "lon": 139.7527, "country": "Japan", "city": "Tokyo", "founded": 1919, "specialty": "SLR, Medium Format", "note": "First Japanese SLR (Asahiflex, 1952)"},
    {"name": "Zeiss Camera Lenses", "lat": 50.9271, "lon": 11.5892, "country": "Germany", "city": "Jena", "founded": 1846, "specialty": "Optics, Lenses", "note": "Carl Zeiss optics, Planar & Sonnar designs"},
    {"name": "Zeiss Oberkochen", "lat": 48.7856, "lon": 10.0967, "country": "Germany", "city": "Oberkochen", "founded": 1846, "specialty": "Optics, Lenses", "note": "Post-war West German Zeiss headquarters"},
    {"name": "Rollei (Franke & Heidecke)", "lat": 51.9280, "lon": 10.4234, "country": "Germany", "city": "Braunschweig", "founded": 1920, "specialty": "TLR, Medium Format", "note": "Rolleiflex TLR revolutionized photography"},
    {"name": "Voigtlander Factory", "lat": 51.9280, "lon": 10.4234, "country": "Germany", "city": "Braunschweig", "founded": 1756, "specialty": "Optics, Rangefinder", "note": "Oldest optics company in the world"},
    {"name": "Polaroid HQ (Original)", "lat": 42.3736, "lon": -71.0765, "country": "USA", "city": "Cambridge, MA", "founded": 1937, "specialty": "Instant Film", "note": "Edwin Land's instant photography revolution"},
    {"name": "Kodak Eastman Business Park", "lat": 43.1566, "lon": -77.6088, "country": "USA", "city": "Rochester, NY", "founded": 1888, "specialty": "Film, Cameras", "note": "George Eastman's empire, defined consumer photography"},
    {"name": "Mamiya Factory", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "city": "Tokyo", "founded": 1940, "specialty": "Medium Format", "note": "RB67 and RZ67 professional medium format systems"},
    {"name": "Sigma Corporation", "lat": 36.3626, "lon": 139.4595, "country": "Japan", "city": "Aizu", "founded": 1961, "specialty": "Lenses, Foveon", "note": "Art lens line, Foveon sensor technology"},
    {"name": "Tamron HQ", "lat": 35.8617, "lon": 139.6454, "country": "Japan", "city": "Saitama", "founded": 1950, "specialty": "Lenses", "note": "Pioneer of all-in-one zoom lenses"},
    {"name": "Phase One", "lat": 55.6761, "lon": 12.5683, "country": "Denmark", "city": "Copenhagen", "founded": 1993, "specialty": "Digital Medium Format", "note": "150MP IQ4 backs, aerial & industrial imaging"},
    {"name": "Panasonic Lumix Division", "lat": 34.6937, "lon": 135.5023, "country": "Japan", "city": "Osaka", "founded": 2001, "specialty": "Mirrorless, Video", "note": "GH series pioneered 4K video in stills cameras"},
    {"name": "RED Digital Cinema", "lat": 33.6846, "lon": -117.8265, "country": "USA", "city": "Irvine, CA", "founded": 2005, "specialty": "Digital Cinema", "note": "RED ONE changed filmmaking, 8K sensors"},
    {"name": "ARRI (Arnold & Richter)", "lat": 48.1551, "lon": 11.5418, "country": "Germany", "city": "Munich", "founded": 1917, "specialty": "Cinema Cameras", "note": "ALEXA system, dominant in Hollywood cinema"},
    {"name": "Blackmagic Design", "lat": -37.8136, "lon": 144.9631, "country": "Australia", "city": "Melbourne", "founded": 2001, "specialty": "Cinema, Post-Production", "note": "Pocket Cinema Camera democratized filmmaking"},
    {"name": "DJI HQ", "lat": 22.5431, "lon": 113.9529, "country": "China", "city": "Shenzhen", "founded": 2006, "specialty": "Drone Cameras", "note": "World's largest drone manufacturer, Hasselblad integration"},
    {"name": "GoPro HQ", "lat": 37.5116, "lon": -122.2550, "country": "USA", "city": "San Mateo, CA", "founded": 2002, "specialty": "Action Cameras", "note": "Defined the action camera category"},
    {"name": "Linhof Factory", "lat": 48.1351, "lon": 11.5820, "country": "Germany", "city": "Munich", "founded": 1887, "specialty": "Large Format", "note": "Master Technika, precision large format cameras"},
    {"name": "Ilford Photo", "lat": 51.8305, "lon": -2.5879, "country": "UK", "city": "Mobberley", "founded": 1879, "specialty": "B&W Film & Paper", "note": "HP5 Plus and Delta films, darkroom papers"},
    {"name": "Foma Bohemia", "lat": 49.4688, "lon": 17.1184, "country": "Czech Republic", "city": "Hradec Kralove", "founded": 1921, "specialty": "Film Manufacturing", "note": "One of last independent film manufacturers"},
    {"name": "Agfa-Gevaert", "lat": 51.0910, "lon": 4.3783, "country": "Belgium", "city": "Mortsel", "founded": 1867, "specialty": "Film, Imaging", "note": "Historic German/Belgian imaging giant"},
    {"name": "Graflex (Historic)", "lat": 43.1566, "lon": -77.6088, "country": "USA", "city": "Rochester, NY", "founded": 1887, "specialty": "Press Cameras", "note": "Speed Graphic defined press photography"},
    {"name": "Minolta (Historic HQ)", "lat": 34.6937, "lon": 135.5023, "country": "Japan", "city": "Osaka", "founded": 1928, "specialty": "SLR, Autofocus", "note": "First integrated autofocus SLR (7000, 1985)"},
]

PHOTOGRAPHY_MUSEUMS = [
    {"name": "International Center of Photography (ICP)", "lat": 40.7209, "lon": -73.9942, "country": "USA", "city": "New York", "founded": 1974, "focus": "Contemporary Photography", "note": "Cornell Capa founded, major exhibitions"},
    {"name": "Victoria and Albert Museum - Photography Gallery", "lat": 51.4966, "lon": -0.1722, "country": "UK", "city": "London", "founded": 1852, "focus": "Historic & Contemporary", "note": "300,000+ photographs from 1839 to present"},
    {"name": "Maison Europeenne de la Photographie", "lat": 48.8543, "lon": 2.3615, "country": "France", "city": "Paris", "founded": 1996, "focus": "European Photography", "note": "20,000+ works, video art, contemporary photo"},
    {"name": "Foam Photography Museum", "lat": 52.3640, "lon": 4.8952, "country": "Netherlands", "city": "Amsterdam", "founded": 2001, "focus": "All Photography Genres", "note": "Foam Magazine, emerging talent platform"},
    {"name": "Fotografiska Stockholm", "lat": 59.3177, "lon": 18.0851, "country": "Sweden", "city": "Stockholm", "founded": 2010, "focus": "Contemporary Photography", "note": "One of world's largest photography museums"},
    {"name": "Fotografiska New York", "lat": 40.7394, "lon": -73.9880, "country": "USA", "city": "New York", "founded": 2019, "focus": "Contemporary Photography", "note": "US branch of Stockholm institution"},
    {"name": "George Eastman Museum", "lat": 43.1480, "lon": -77.5783, "country": "USA", "city": "Rochester, NY", "founded": 1947, "focus": "Photography & Cinema History", "note": "World's oldest photography museum, 400,000+ photos"},
    {"name": "Museum of Photography (Berlin)", "lat": 52.5094, "lon": 13.3726, "country": "Germany", "city": "Berlin", "founded": 2004, "focus": "Helmut Newton Foundation", "note": "Newton's estate plus rotating exhibitions"},
    {"name": "National Geographic Museum", "lat": 38.9053, "lon": -77.0386, "country": "USA", "city": "Washington DC", "founded": 2014, "focus": "Documentary & Nature", "note": "Iconic NatGeo photography exhibitions"},
    {"name": "Leica Gallery Wetzlar", "lat": 50.5558, "lon": 8.4947, "country": "Germany", "city": "Wetzlar", "founded": 2014, "focus": "Leica Photography", "note": "Inside Leitz Park, rotating master exhibitions"},
    {"name": "Tokyo Photographic Art Museum", "lat": 35.6419, "lon": 139.7137, "country": "Japan", "city": "Tokyo", "founded": 1990, "focus": "Japanese & International Photo Art", "note": "35,000+ works, Yebisu Garden Place"},
    {"name": "Canadian Photography Institute", "lat": 45.3956, "lon": -75.6986, "country": "Canada", "city": "Ottawa", "founded": 2015, "focus": "Photography Heritage", "note": "Part of National Gallery of Canada"},
    {"name": "Musee Nicephore Niepce", "lat": 46.7810, "lon": 4.8526, "country": "France", "city": "Chalon-sur-Saone", "founded": 1972, "focus": "History of Photography", "note": "Named after inventor of photography, first photo exhibit"},
    {"name": "C/O Berlin", "lat": 52.5065, "lon": 13.3330, "country": "Germany", "city": "Berlin", "founded": 2000, "focus": "Visual Art & Photography", "note": "Amerika Haus, young talent awards"},
    {"name": "Huis Marseille", "lat": 52.3657, "lon": 4.8840, "country": "Netherlands", "city": "Amsterdam", "founded": 1999, "focus": "Photography Art", "note": "17th-century canal house museum"},
    {"name": "Center for Creative Photography", "lat": 32.2310, "lon": -110.9526, "country": "USA", "city": "Tucson, AZ", "founded": 1975, "focus": "Ansel Adams Archive", "note": "90,000+ master prints, Adams archive"},
    {"name": "Arles - Rencontres de la Photographie", "lat": 43.6766, "lon": 4.6278, "country": "France", "city": "Arles", "founded": 1970, "focus": "Annual Photography Festival", "note": "World's oldest and most influential photo festival"},
    {"name": "CAMERA - Centro Italiano per la Fotografia", "lat": 45.0703, "lon": 7.6869, "country": "Italy", "city": "Turin", "founded": 2015, "focus": "Italian & International Photography", "note": "Major exhibitions in former industrial space"},
    {"name": "Aperture Foundation Gallery", "lat": 40.7215, "lon": -74.0016, "country": "USA", "city": "New York", "founded": 1952, "focus": "Fine Art Photography", "note": "Founded by Ansel Adams, Minor White, others"},
    {"name": "Museo de Arte Moderno - Photography Wing", "lat": 19.4270, "lon": -99.1785, "country": "Mexico", "city": "Mexico City", "founded": 1964, "focus": "Mexican Photography", "note": "Manuel Alvarez Bravo collection"},
    {"name": "Magnum Photos Gallery Paris", "lat": 48.8566, "lon": 2.3522, "country": "France", "city": "Paris", "founded": 1947, "focus": "Photojournalism", "note": "Legendary cooperative founded by Capa, Cartier-Bresson"},
    {"name": "Pier 24 Photography", "lat": 37.7910, "lon": -122.3893, "country": "USA", "city": "San Francisco", "founded": 2010, "focus": "Large-Scale Photography", "note": "Largest privately-owned photography collection space"},
    {"name": "Museum of Image and Sound (MIS)", "lat": -23.5614, "lon": -46.6726, "country": "Brazil", "city": "Sao Paulo", "founded": 1970, "focus": "Brazilian Photography & Media", "note": "Audiovisual archives and photography exhibitions"},
    {"name": "Museo Alinari di Fotografia", "lat": 43.7696, "lon": 11.2558, "country": "Italy", "city": "Florence", "founded": 2006, "focus": "Historic Photography", "note": "Alinari Brothers archive since 1852"},
    {"name": "National Media Museum", "lat": 53.7930, "lon": -1.7540, "country": "UK", "city": "Bradford", "founded": 1983, "focus": "Photography, TV, Film", "note": "UNESCO City of Film, massive photo archive"},
    {"name": "Helmut Newton Foundation", "lat": 52.5094, "lon": 13.3726, "country": "Germany", "city": "Berlin", "founded": 2004, "focus": "Fashion Photography", "note": "Permanent Newton collection + June Newton"},
    {"name": "Galerie nationale du Jeu de Paume", "lat": 48.8656, "lon": 2.3233, "country": "France", "city": "Paris", "founded": 2004, "focus": "Image & Photography", "note": "Tuileries Garden, major photo exhibitions"},
    {"name": "Australian Centre for Photography", "lat": -33.8910, "lon": 151.2128, "country": "Australia", "city": "Sydney", "founded": 1974, "focus": "Australian & International", "note": "Workshops, exhibitions, and residencies"},
    {"name": "Kyotographie Festival Venue", "lat": 35.0116, "lon": 135.7681, "country": "Japan", "city": "Kyoto", "founded": 2013, "focus": "International Photography Festival", "note": "Historic Kyoto venues transformed for photography"},
    {"name": "Istanbul Museum of Modern Art - Photo Gallery", "lat": 41.0425, "lon": 28.9833, "country": "Turkey", "city": "Istanbul", "founded": 2004, "focus": "Turkish & Contemporary Photography", "note": "Bosphorus-side museum with dedicated photo wing"},
]

NATGEO_FAMOUS_LOCATIONS = [
    {"name": "Antelope Canyon", "lat": 36.8619, "lon": -111.3743, "country": "USA", "state": "Arizona", "photographer": "Peter Lik / Various", "year": 1997, "note": "Slot canyon, light beams through sandstone"},
    {"name": "Zhangjiajie National Forest", "lat": 29.3249, "lon": 110.4343, "country": "China", "state": "Hunan", "photographer": "Various", "year": 2010, "note": "Avatar Hallelujah Mountains, quartzite pillars"},
    {"name": "Lofoten Islands", "lat": 68.2094, "lon": 14.1540, "country": "Norway", "state": "Nordland", "photographer": "Various", "year": 2005, "note": "Arctic archipelago, dramatic fjords and fishing villages"},
    {"name": "Salar de Uyuni", "lat": -20.1338, "lon": -67.4891, "country": "Bolivia", "state": "Potosi", "photographer": "Various", "year": 2000, "note": "World's largest salt flat, mirror effect"},
    {"name": "Sossusvlei Dunes", "lat": -24.7254, "lon": 15.2993, "country": "Namibia", "state": "Hardap", "photographer": "Frans Lanting", "year": 1990, "note": "Tallest sand dunes on Earth, 325m Dune 7"},
    {"name": "Victoria Falls", "lat": -17.9244, "lon": 25.8567, "country": "Zambia/Zimbabwe", "state": "Matabeleland", "photographer": "Various", "year": 1855, "note": "Mosi-oa-Tunya, 1,708m wide curtain of water"},
    {"name": "Yellowstone Grand Prismatic Spring", "lat": 44.5251, "lon": -110.8382, "country": "USA", "state": "Wyoming", "photographer": "Various", "year": 1871, "note": "Largest hot spring in the US, thermophilic colors"},
    {"name": "Torres del Paine", "lat": -50.9423, "lon": -73.4068, "country": "Chile", "state": "Magallanes", "photographer": "Galen Rowell", "year": 1985, "note": "Iconic granite towers, Patagonian landscape"},
    {"name": "Iguazu Falls", "lat": -25.6953, "lon": -54.4367, "country": "Argentina/Brazil", "state": "Misiones", "photographer": "Various", "year": 1986, "note": "275 individual falls, Devil's Throat"},
    {"name": "Serengeti Great Migration", "lat": -2.3333, "lon": 34.8333, "country": "Tanzania", "state": "Mara Region", "photographer": "Mitsuaki Iwago", "year": 1986, "note": "1.5 million wildebeest annual migration"},
    {"name": "Bora Bora Lagoon", "lat": -16.5004, "lon": -151.7415, "country": "French Polynesia", "state": "Leeward Islands", "photographer": "Various", "year": 1970, "note": "Turquoise lagoon, overwater bungalows"},
    {"name": "Cappadocia Balloon Vista", "lat": 38.6431, "lon": 34.8283, "country": "Turkey", "state": "Nevsehir", "photographer": "Various", "year": 2005, "note": "Hot air balloons over fairy chimneys at dawn"},
    {"name": "Plitvice Lakes", "lat": 44.8654, "lon": 15.5820, "country": "Croatia", "state": "Lika-Senj", "photographer": "Various", "year": 1979, "note": "16 terraced lakes, cascading waterfalls"},
    {"name": "Wadi Rum", "lat": 29.5320, "lon": 35.4110, "country": "Jordan", "state": "Aqaba", "photographer": "Various", "year": 1962, "note": "Valley of the Moon, Lawrence of Arabia filming"},
    {"name": "Trolltunga", "lat": 60.1241, "lon": 6.7400, "country": "Norway", "state": "Vestland", "photographer": "Various", "year": 2010, "note": "Troll's Tongue rock jutting 700m above lake"},
    {"name": "Milford Sound", "lat": -44.6414, "lon": 167.8975, "country": "New Zealand", "state": "Fiordland", "photographer": "Various", "year": 1888, "note": "Rudyard Kipling's Eighth Wonder of the World"},
    {"name": "Seljalandsfoss Waterfall", "lat": 63.6156, "lon": -19.9886, "country": "Iceland", "state": "South", "photographer": "Various", "year": 2008, "note": "Walk-behind waterfall, 60m drop"},
    {"name": "Li River Karst Landscape", "lat": 24.9388, "lon": 110.2990, "country": "China", "state": "Guangxi", "photographer": "Various", "year": 1973, "note": "Featured on 20 yuan banknote"},
    {"name": "Moraine Lake", "lat": 51.3217, "lon": -116.1860, "country": "Canada", "state": "Alberta", "photographer": "Various", "year": 1899, "note": "Ten Peaks backdrop, intense turquoise water"},
    {"name": "Great Barrier Reef Aerial", "lat": -18.2871, "lon": 147.6992, "country": "Australia", "state": "Queensland", "photographer": "David Doubilet", "year": 1981, "note": "World's largest coral reef system, 2,300km"},
    {"name": "Pamukkale Travertines", "lat": 37.9209, "lon": 29.1187, "country": "Turkey", "state": "Denizli", "photographer": "Various", "year": 1988, "note": "Cotton Castle white thermal terraces"},
    {"name": "Death Valley Mesquite Dunes", "lat": 36.6069, "lon": -117.1062, "country": "USA", "state": "California", "photographer": "Ansel Adams", "year": 1948, "note": "Extreme desert landscape, lowest point in N. America"},
    {"name": "Kirkjufell Mountain", "lat": 64.9426, "lon": -23.3068, "country": "Iceland", "state": "Snaefellsnes", "photographer": "Various", "year": 2012, "note": "Most photographed mountain in Iceland"},
    {"name": "Bryce Canyon Hoodoos", "lat": 37.5930, "lon": -112.1871, "country": "USA", "state": "Utah", "photographer": "Various", "year": 1928, "note": "Largest concentration of hoodoos on Earth"},
    {"name": "Rice Terraces of Mu Cang Chai", "lat": 21.7868, "lon": 104.0876, "country": "Vietnam", "state": "Yen Bai", "photographer": "Various", "year": 2007, "note": "Sculpted rice paddies on steep mountain slopes"},
    {"name": "Reynisfjara Black Sand Beach", "lat": 63.4053, "lon": -19.0707, "country": "Iceland", "state": "South", "photographer": "Various", "year": 2015, "note": "Basalt columns, sea stacks, powerful waves"},
    {"name": "Zion Narrows", "lat": 37.2982, "lon": -112.9460, "country": "USA", "state": "Utah", "photographer": "Various", "year": 1930, "note": "Slot canyon carved by the Virgin River"},
    {"name": "Cliffs of Moher", "lat": 52.9715, "lon": -9.4309, "country": "Ireland", "state": "Clare", "photographer": "Various", "year": 1835, "note": "214m sheer cliffs on Atlantic coast"},
    {"name": "Meteora Monasteries", "lat": 39.7217, "lon": 21.6306, "country": "Greece", "state": "Thessaly", "photographer": "Various", "year": 1988, "note": "Monasteries atop sandstone pillars"},
    {"name": "Fairy Pools, Isle of Skye", "lat": 57.2507, "lon": -6.2803, "country": "UK", "state": "Scotland", "photographer": "Various", "year": 2010, "note": "Crystal-clear blue pools below the Cuillin mountains"},
]

DARKROOM_FILM_HERITAGE = [
    {"name": "Kodak Park (Eastman Business Park)", "lat": 43.1566, "lon": -77.6088, "country": "USA", "city": "Rochester, NY", "founded": 1891, "type": "Film Factory", "note": "Where Kodachrome, Tri-X, and Ektachrome were born"},
    {"name": "Ilford Photo Factory", "lat": 51.8305, "lon": -2.5879, "country": "UK", "city": "Mobberley", "founded": 1879, "type": "Film & Paper Factory", "note": "Still producing HP5, FP4, Delta, and darkroom papers"},
    {"name": "Agfa-Gevaert Plant", "lat": 51.0910, "lon": 4.3783, "country": "Belgium", "city": "Mortsel", "founded": 1867, "type": "Film Factory", "note": "Historic European film giant, Agfacolor process"},
    {"name": "Foma Bohemia Factory", "lat": 49.4688, "lon": 17.1184, "country": "Czech Republic", "city": "Hradec Kralove", "founded": 1921, "type": "Film Factory", "note": "Independent B&W film manufacturer, Fomapan range"},
    {"name": "Fujifilm Ashigara Plant", "lat": 35.3130, "lon": 139.0770, "country": "Japan", "city": "Kanagawa", "founded": 1934, "type": "Film Factory", "note": "Where Velvia, Provia, and Acros films are made"},
    {"name": "Polaroid Originals (Impossible Project)", "lat": 51.8127, "lon": 4.6626, "country": "Netherlands", "city": "Enschede", "founded": 2008, "type": "Instant Film Factory", "note": "Rescued last Polaroid film factory from closure"},
    {"name": "Ferrania Film Factory", "lat": 44.3610, "lon": 8.3795, "country": "Italy", "city": "Cairo Montenotte", "founded": 1923, "type": "Film Factory", "note": "Historic Italian film maker, revival project ongoing"},
    {"name": "Zone VI Studios (Historic)", "lat": 43.6273, "lon": -72.5193, "country": "USA", "city": "Newfane, VT", "founded": 1973, "type": "Darkroom Equipment", "note": "Fred Picker's Zone System workshops and enlargers"},
    {"name": "Durst Image Technology", "lat": 46.7117, "lon": 11.4621, "country": "Italy", "city": "Brixen", "founded": 1936, "type": "Enlarger Manufacturing", "note": "Legendary darkroom enlargers, now digital printing"},
    {"name": "Bergger Film Factory", "lat": 46.2044, "lon": 6.1432, "country": "France", "city": "Geneva Area", "founded": 1990, "type": "Film & Paper", "note": "Artisan B&W films and printing papers"},
    {"name": "Adox/Fotokemika Revival", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "city": "Bad Saarow", "founded": 1860, "type": "Film Manufacturing", "note": "Oldest photographic company, CMS 20 film"},
    {"name": "Cinestill Film HQ", "lat": 34.0522, "lon": -118.2437, "country": "USA", "city": "Los Angeles", "founded": 2012, "type": "Film Repurposing", "note": "Motion picture film repurposed for still cameras"},
    {"name": "Lomography HQ", "lat": 48.2082, "lon": 16.3738, "country": "Austria", "city": "Vienna", "founded": 1992, "type": "Analog Revival", "note": "Film camera and film revival movement"},
    {"name": "Harman Technology (Ilford Group)", "lat": 51.8305, "lon": -2.5879, "country": "UK", "city": "Mobberley", "founded": 2005, "type": "B&W Film & Paper", "note": "Parent of Ilford, Kentmere, Harman brands"},
    {"name": "Lucky Film Factory (Historic)", "lat": 38.0428, "lon": 114.5149, "country": "China", "city": "Baoding", "founded": 1958, "type": "Film Factory", "note": "China's largest film manufacturer, now mostly digital"},
    {"name": "Tasma Film Plant (Historic)", "lat": 55.8304, "lon": 49.0661, "country": "Russia", "city": "Kazan", "founded": 1933, "type": "Film Factory", "note": "Soviet-era film manufacturer"},
    {"name": "Forte Fotokemiai (Historic)", "lat": 47.4979, "lon": 19.0402, "country": "Hungary", "city": "Vac", "founded": 1921, "type": "Film & Paper Factory", "note": "Hungarian photographic materials, closed 2007"},
    {"name": "Oriental Photo Industrial (Historic)", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "city": "Tokyo", "founded": 1919, "type": "B&W Paper", "note": "Seagull brand papers, once Japan's finest"},
    {"name": "Kentmere (Historic Site)", "lat": 54.4429, "lon": -2.8423, "country": "UK", "city": "Staveley", "founded": 1979, "type": "Film & Paper", "note": "Lake District-based B&W film and paper maker"},
    {"name": "Shanghai GP3 Film Factory", "lat": 31.2304, "lon": 121.4737, "country": "China", "city": "Shanghai", "founded": 1958, "type": "Film Manufacturing", "note": "Affordable B&W film still in production"},
]

LANDSCAPE_SPOTS = [
    {"name": "Antelope Canyon", "lat": 36.8619, "lon": -111.3743, "country": "USA", "region": "Arizona", "type": "Slot Canyon", "best_light": "Midday (light beams)", "note": "Navajo sandstone sculpted by flash floods"},
    {"name": "Zhangjiajie Pillars", "lat": 29.3249, "lon": 110.4343, "country": "China", "region": "Hunan", "type": "Sandstone Pillars", "best_light": "Early morning fog", "note": "3,000+ quartzite pillars, Avatar Mountains"},
    {"name": "Lofoten Islands", "lat": 68.2094, "lon": 14.1540, "country": "Norway", "region": "Nordland", "type": "Arctic Archipelago", "best_light": "Midnight sun / Winter blue hour", "note": "Dramatic peaks rising from Arctic sea"},
    {"name": "Patagonia - Fitz Roy", "lat": -49.2714, "lon": -72.9894, "country": "Argentina", "region": "Santa Cruz", "type": "Mountain", "best_light": "Sunrise alpenglow", "note": "3,405m granite spire, iconic Patagonia peak"},
    {"name": "Dolomites - Tre Cime", "lat": 46.6191, "lon": 12.3030, "country": "Italy", "region": "South Tyrol", "type": "Mountain Peaks", "best_light": "Golden hour", "note": "Three iconic limestone towers, UNESCO site"},
    {"name": "Faroe Islands - Mulafossur", "lat": 62.1116, "lon": -7.1098, "country": "Faroe Islands", "region": "Vagar", "type": "Waterfall/Sea Cliff", "best_light": "Overcast even light", "note": "Waterfall dropping directly into the Atlantic"},
    {"name": "Monument Valley", "lat": 36.9833, "lon": -110.1000, "country": "USA", "region": "Arizona/Utah", "type": "Desert Buttes", "best_light": "Sunrise/Sunset", "note": "Iconic sandstone buttes, Navajo Nation"},
    {"name": "Yosemite Valley - Tunnel View", "lat": 37.7156, "lon": -119.6778, "country": "USA", "region": "California", "type": "Glacial Valley", "best_light": "Winter sunset", "note": "El Capitan, Bridalveil Fall, Half Dome vista"},
    {"name": "Skogafoss Waterfall", "lat": 63.5320, "lon": -19.5113, "country": "Iceland", "region": "South", "type": "Waterfall", "best_light": "Morning with rainbow", "note": "60m wide, 25m drop, rainbow-prone"},
    {"name": "Lake Bled", "lat": 46.3625, "lon": 14.0936, "country": "Slovenia", "region": "Upper Carniola", "type": "Alpine Lake", "best_light": "Autumn sunrise", "note": "Island church on glacial lake, Julian Alps backdrop"},
    {"name": "Lauterbrunnen Valley", "lat": 46.5935, "lon": 7.9089, "country": "Switzerland", "region": "Bern", "type": "Glacial Valley", "best_light": "Morning light", "note": "72 waterfalls, inspired Tolkien's Rivendell"},
    {"name": "Kauai - Na Pali Coast", "lat": 22.1641, "lon": -159.6400, "country": "USA", "region": "Hawaii", "type": "Sea Cliffs", "best_light": "Golden hour aerial", "note": "Emerald-green 1,200m sea cliffs, Jurassic Park"},
    {"name": "Scottish Highlands - Glencoe", "lat": 56.6826, "lon": -5.1023, "country": "UK", "region": "Scotland", "type": "Mountain Valley", "best_light": "Moody overcast", "note": "Atmospheric glen, Three Sisters peaks"},
    {"name": "Banff - Moraine Lake", "lat": 51.3217, "lon": -116.1860, "country": "Canada", "region": "Alberta", "type": "Alpine Lake", "best_light": "Sunrise July-September", "note": "Ten Peaks, impossibly turquoise glacial water"},
    {"name": "Wanaka Tree", "lat": -44.6973, "lon": 169.0961, "country": "New Zealand", "region": "Otago", "type": "Lone Tree", "best_light": "Sunrise/Sunset", "note": "Solitary willow in Lake Wanaka, viral sensation"},
    {"name": "Deadvlei", "lat": -24.7638, "lon": 15.2921, "country": "Namibia", "region": "Hardap", "type": "Desert Pan", "best_light": "Early morning contrast", "note": "900-year-old dead trees on white clay, red dunes"},
    {"name": "Kirkjufell", "lat": 64.9426, "lon": -23.3068, "country": "Iceland", "region": "Snaefellsnes", "type": "Mountain", "best_light": "Northern Lights / Sunset", "note": "Church Mountain with cascading waterfall"},
    {"name": "Matterhorn from Riffelsee", "lat": 45.9878, "lon": 7.7552, "country": "Switzerland", "region": "Valais", "type": "Mountain Reflection", "best_light": "Dawn reflection", "note": "Perfect Matterhorn reflection in alpine lake"},
    {"name": "The Wave, Arizona", "lat": 36.9960, "lon": -112.0060, "country": "USA", "region": "Arizona", "type": "Sandstone Formation", "best_light": "Midday (no shadows)", "note": "Permit-only, swirling Jurassic sandstone"},
    {"name": "Oia Sunset, Santorini", "lat": 36.4618, "lon": 25.3753, "country": "Greece", "region": "Cyclades", "type": "Village/Sunset", "best_light": "Sunset", "note": "Blue domes, white walls, Aegean sunset"},
    {"name": "Senja Island - Devil's Jaw", "lat": 69.3008, "lon": 17.1005, "country": "Norway", "region": "Troms", "type": "Mountain/Beach", "best_light": "Blue hour / Aurora", "note": "Dramatic Arctic coastline, Segla peak"},
    {"name": "Grand Teton - Snake River", "lat": 43.7904, "lon": -110.6818, "country": "USA", "region": "Wyoming", "type": "Mountain/River", "best_light": "Morning", "note": "Ansel Adams' iconic 1942 photograph location"},
    {"name": "Verdon Gorge", "lat": 43.7547, "lon": 6.3269, "country": "France", "region": "Provence", "type": "Canyon", "best_light": "Afternoon", "note": "Europe's Grand Canyon, turquoise river 700m deep"},
    {"name": "Table Mountain", "lat": -33.9628, "lon": 18.4098, "country": "South Africa", "region": "Western Cape", "type": "Flat-Top Mountain", "best_light": "Sunset from Bloubergstrand", "note": "Iconic flat summit, tablecloth clouds"},
    {"name": "Preikestolen (Pulpit Rock)", "lat": 58.9863, "lon": 6.1882, "country": "Norway", "region": "Rogaland", "type": "Cliff Platform", "best_light": "Sunrise", "note": "604m sheer cliff above Lysefjord"},
    {"name": "Uyuni Mirror", "lat": -20.1338, "lon": -67.4891, "country": "Bolivia", "region": "Potosi", "type": "Salt Flat", "best_light": "Wet season reflection", "note": "World's largest mirror, surreal reflections"},
    {"name": "Japanese Alps - Kamikochi", "lat": 36.2481, "lon": 137.6282, "country": "Japan", "region": "Nagano", "type": "Mountain Valley", "best_light": "Autumn foliage sunrise", "note": "Alpine valley at 1,500m, Azusa River"},
    {"name": "Huangshan (Yellow Mountains)", "lat": 30.1390, "lon": 118.1634, "country": "China", "region": "Anhui", "type": "Granite Peaks", "best_light": "Sunrise above clouds", "note": "Inspired centuries of Chinese painting"},
    {"name": "Seceda Ridgeline", "lat": 46.6015, "lon": 11.7268, "country": "Italy", "region": "South Tyrol", "type": "Mountain Ridge", "best_light": "Sunrise", "note": "Dramatic Dolomite ridge, grassy foreground"},
    {"name": "Torres del Paine W Trek", "lat": -50.9423, "lon": -73.4068, "country": "Chile", "region": "Magallanes", "type": "Mountain/Lake", "best_light": "Sunrise", "note": "Granite towers, glacial lakes, Patagonian wind"},
]

STREET_PHOTOGRAPHY_CAPITALS = [
    {"name": "Tokyo - Shinjuku", "lat": 35.6938, "lon": 139.7034, "country": "Japan", "population_m": 13.96, "style": "Neon Urbanism", "famous_photographer": "Daido Moriyama", "note": "Kabukicho neon, Shinjuku station 3.5M daily"},
    {"name": "New York - Times Square", "lat": 40.7580, "lon": -73.9855, "country": "USA", "population_m": 8.34, "style": "Urban Energy", "famous_photographer": "Garry Winogrand", "note": "Crossroads of the World, 330K daily pedestrians"},
    {"name": "Paris - Le Marais", "lat": 48.8566, "lon": 2.3522, "country": "France", "population_m": 2.16, "style": "Romantic Urban", "famous_photographer": "Henri Cartier-Bresson", "note": "Birthplace of street photography, cafe culture"},
    {"name": "Havana - Old Town", "lat": 23.1136, "lon": -82.3666, "country": "Cuba", "population_m": 2.13, "style": "Vintage Urban", "famous_photographer": "Alex Webb", "note": "Classic cars, colonial architecture, vibrant colors"},
    {"name": "Mumbai - Dharavi", "lat": 19.0176, "lon": 72.8562, "country": "India", "population_m": 20.67, "style": "Human Density", "famous_photographer": "Raghu Rai", "note": "Intense street life, Bollywood industry"},
    {"name": "Istanbul - Grand Bazaar", "lat": 41.0105, "lon": 28.9680, "country": "Turkey", "population_m": 15.46, "style": "East Meets West", "famous_photographer": "Ara Guler", "note": "Crossroads of continents, Grand Bazaar 4,000 shops"},
    {"name": "Hong Kong - Mong Kok", "lat": 22.3193, "lon": 114.1694, "country": "China", "population_m": 7.48, "style": "Vertical Neon", "famous_photographer": "Fan Ho", "note": "Densest neighborhood on Earth, neon signage forest"},
    {"name": "Marrakech - Medina", "lat": 31.6295, "lon": -7.9811, "country": "Morocco", "population_m": 0.93, "style": "Color & Chaos", "famous_photographer": "Bruno Barbey", "note": "Jemaa el-Fnaa square, souks, intense colors"},
    {"name": "London - Brick Lane", "lat": 51.5074, "lon": -0.1278, "country": "UK", "population_m": 8.98, "style": "Multicultural", "famous_photographer": "Martin Parr", "note": "Street art, markets, diverse cultural layers"},
    {"name": "Mexico City - Centro Historico", "lat": 19.4326, "lon": -99.1332, "country": "Mexico", "population_m": 9.21, "style": "Colorful Chaos", "famous_photographer": "Manuel Alvarez Bravo", "note": "Zocalo, muralism, Day of the Dead"},
    {"name": "Bangkok - Chinatown (Yaowarat)", "lat": 13.7563, "lon": 100.5018, "country": "Thailand", "population_m": 10.54, "style": "Nocturnal Street Life", "famous_photographer": "Various", "note": "Street food capital, tuk-tuks, temple culture"},
    {"name": "Kolkata - Howrah Bridge", "lat": 22.5726, "lon": 88.3639, "country": "India", "population_m": 14.85, "style": "Layered Humanity", "famous_photographer": "Raghubir Singh", "note": "City of Joy, flower markets, rickshaws"},
    {"name": "Lisbon - Alfama", "lat": 38.7223, "lon": -9.1393, "country": "Portugal", "population_m": 0.55, "style": "Faded Grandeur", "famous_photographer": "Various", "note": "Tram 28, tile facades, steep narrow streets"},
    {"name": "Berlin - Kreuzberg", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "population_m": 3.64, "style": "Counter-Culture", "famous_photographer": "Various", "note": "Street art, Berlin Wall remnants, diverse"},
    {"name": "Varanasi - Ghats", "lat": 25.3176, "lon": 83.0068, "country": "India", "population_m": 1.21, "style": "Spiritual Drama", "famous_photographer": "Steve McCurry", "note": "Sacred Ganges ghats, 3000-year-old city"},
    {"name": "New Orleans - French Quarter", "lat": 29.9511, "lon": -90.0715, "country": "USA", "population_m": 0.39, "style": "Jazz & Culture", "famous_photographer": "William Claxton", "note": "Bourbon Street, jazz clubs, wrought-iron balconies"},
    {"name": "Seoul - Myeongdong", "lat": 37.5665, "lon": 126.9780, "country": "South Korea", "population_m": 9.74, "style": "K-Culture Neon", "famous_photographer": "Kim Ki-chan", "note": "Neon shopping, K-pop culture, Bukchon hanok village"},
    {"name": "Buenos Aires - La Boca", "lat": -34.6037, "lon": -58.3816, "country": "Argentina", "population_m": 3.06, "style": "Tango & Color", "famous_photographer": "Marcos Lopez", "note": "Caminito colorful houses, tango in the streets"},
    {"name": "Hanoi - Old Quarter", "lat": 21.0285, "lon": 105.8542, "country": "Vietnam", "population_m": 8.05, "style": "Motorbike Chaos", "famous_photographer": "Various", "note": "36 ancient streets, train street, pho vendors"},
    {"name": "Naples - Spaccanapoli", "lat": 40.8518, "lon": 14.2681, "country": "Italy", "population_m": 0.96, "style": "Mediterranean Chaos", "famous_photographer": "Various", "note": "Narrow alleys, laundry lines, street food culture"},
    {"name": "Taipei - Ximending", "lat": 25.0330, "lon": 121.5654, "country": "Taiwan", "population_m": 2.65, "style": "Pop Culture", "famous_photographer": "Chang Chao-Tang", "note": "Youth culture district, night markets, neon"},
    {"name": "Lagos - Victoria Island", "lat": 6.5244, "lon": 3.3792, "country": "Nigeria", "population_m": 15.39, "style": "Afro-Urbanism", "famous_photographer": "Akinbode Akinbiyi", "note": "Largest city in Africa, vibrant street life"},
    {"name": "Fez - Medina", "lat": 34.0181, "lon": -5.0078, "country": "Morocco", "population_m": 1.22, "style": "Medieval Maze", "famous_photographer": "Various", "note": "World's largest car-free urban zone, 9,000 alleys"},
    {"name": "Osaka - Dotonbori", "lat": 34.6937, "lon": 135.5023, "country": "Japan", "population_m": 2.75, "style": "Food & Neon", "famous_photographer": "Various", "note": "Glico Running Man, takoyaki, canal reflections"},
    {"name": "Jaipur - Pink City", "lat": 26.9124, "lon": 75.7873, "country": "India", "population_m": 3.07, "style": "Colorful Heritage", "famous_photographer": "Various", "note": "Hawa Mahal, pink sandstone buildings, bazaars"},
    {"name": "San Francisco - Chinatown", "lat": 37.7749, "lon": -122.4194, "country": "USA", "population_m": 0.87, "style": "Hilly Urban", "famous_photographer": "Fred Lyon", "note": "Cable cars, fog, steep streets, diverse neighborhoods"},
    {"name": "Addis Ababa - Mercato", "lat": 9.0227, "lon": 38.7468, "country": "Ethiopia", "population_m": 5.23, "style": "Market Life", "famous_photographer": "Various", "note": "Largest open-air market in Africa"},
    {"name": "Kathmandu - Thamel", "lat": 27.7172, "lon": 85.3240, "country": "Nepal", "population_m": 1.44, "style": "Spiritual Urban", "famous_photographer": "Various", "note": "Temple squares, prayer flags, Himalayan gateway"},
    {"name": "Palermo - Ballaro Market", "lat": 38.1157, "lon": 13.3615, "country": "Italy", "population_m": 0.67, "style": "Sicilian Street", "famous_photographer": "Letizia Battaglia", "note": "Historic markets, Baroque architecture, raw energy"},
    {"name": "Saigon - District 1", "lat": 10.8231, "lon": 106.6297, "country": "Vietnam", "population_m": 9.00, "style": "Motorbike Urban", "famous_photographer": "Various", "note": "Motorbike rivers, French colonial meets modern glass"},
]

DARK_SKY_SITES = [
    {"name": "Cherry Springs State Park", "lat": 41.6628, "lon": -77.8231, "country": "USA", "region": "Pennsylvania", "bortle": 2, "designation": "IDA Gold Tier", "note": "Eastern USA's darkest sky, naked-eye Milky Way"},
    {"name": "NamibRand Nature Reserve", "lat": -24.9616, "lon": 15.9901, "country": "Namibia", "region": "Hardap", "bortle": 1, "designation": "IDA Gold Tier", "note": "One of darkest places on Earth, zero light pollution"},
    {"name": "Atacama Desert (ALMA)", "lat": -23.0234, "lon": -67.7539, "country": "Chile", "region": "Antofagasta", "bortle": 1, "designation": "World's Best Observatory Site", "note": "Driest desert, 5000m altitude, ALMA radio telescope"},
    {"name": "Aoraki Mackenzie Dark Sky Reserve", "lat": -44.0021, "lon": 170.4778, "country": "New Zealand", "region": "Canterbury", "bortle": 1, "designation": "IDA Gold Tier", "note": "World's largest dark sky reserve, Mt John Observatory"},
    {"name": "Mauna Kea Observatories", "lat": 19.8207, "lon": -155.4680, "country": "USA", "region": "Hawaii", "bortle": 1, "designation": "World-Class Observatory", "note": "4,207m, 13 telescopes, above 40% atmosphere"},
    {"name": "La Palma (Roque de los Muchachos)", "lat": 28.7560, "lon": -17.8863, "country": "Spain", "region": "Canary Islands", "bortle": 1, "designation": "Starlight Reserve", "note": "Light pollution law since 1988, Gran Telescopio Canarias"},
    {"name": "Jasper Dark Sky Preserve", "lat": 52.8737, "lon": -117.8049, "country": "Canada", "region": "Alberta", "bortle": 2, "designation": "IDA Dark Sky Preserve", "note": "World's largest accessible dark sky preserve, 11,000 km2"},
    {"name": "Galloway Forest Dark Sky Park", "lat": 55.0700, "lon": -4.5000, "country": "UK", "region": "Scotland", "bortle": 3, "designation": "IDA Gold Tier", "note": "UK's first Dark Sky Park, 7,500 stars visible"},
    {"name": "Tenerife (Teide Observatory)", "lat": 28.3008, "lon": -16.5120, "country": "Spain", "region": "Canary Islands", "bortle": 2, "designation": "Starlight Reserve", "note": "Above cloud inversion, zodiacal light visible"},
    {"name": "Pic du Midi Observatory", "lat": 42.9372, "lon": 0.1425, "country": "France", "region": "Pyrenees", "bortle": 2, "designation": "IDA Reserve", "note": "2,877m French Pyrenees, Starlight Tourist Destination"},
    {"name": "Elqui Valley", "lat": -30.1669, "lon": -70.8330, "country": "Chile", "region": "Coquimbo", "bortle": 1, "designation": "Astro-Tourism Hub", "note": "350 clear nights/year, multiple observatories"},
    {"name": "Westhavelland Dark Sky Reserve", "lat": 52.7500, "lon": 12.3000, "country": "Germany", "region": "Brandenburg", "bortle": 3, "designation": "IDA Reserve", "note": "Germany's first dark sky reserve, 70km from Berlin"},
    {"name": "Kerry Dark Sky Reserve", "lat": 51.7500, "lon": -10.0000, "country": "Ireland", "region": "Kerry", "bortle": 3, "designation": "IDA Gold Tier", "note": "Northern hemisphere's only gold tier reserve in Ireland"},
    {"name": "Warrumbungle National Park", "lat": -31.2730, "lon": 149.0020, "country": "Australia", "region": "New South Wales", "bortle": 2, "designation": "IDA Dark Sky Park", "note": "Australia's first dark sky park, Siding Spring Observatory"},
    {"name": "Zselic Starry Sky Park", "lat": 46.2330, "lon": 17.7330, "country": "Hungary", "region": "Baranya", "bortle": 3, "designation": "IDA Park", "note": "Central Europe's first dark sky park"},
    {"name": "Aosta Valley", "lat": 45.7389, "lon": 7.4264, "country": "Italy", "region": "Aosta", "bortle": 3, "designation": "Starlight Destination", "note": "Saint-Barthelemy Observatory, Alpine dark skies"},
    {"name": "Natural Bridges National Monument", "lat": 37.6091, "lon": -110.0107, "country": "USA", "region": "Utah", "bortle": 2, "designation": "IDA Park (First)", "note": "World's first International Dark Sky Park, 2007"},
    {"name": "Death Valley National Park", "lat": 36.5054, "lon": -116.9277, "country": "USA", "region": "California", "bortle": 2, "designation": "IDA Gold Tier", "note": "Largest dark sky in USA, excellent winter viewing"},
    {"name": "Sark (Channel Islands)", "lat": 49.4333, "lon": -2.3613, "country": "UK", "region": "Channel Islands", "bortle": 3, "designation": "IDA Dark Sky Island", "note": "World's first dark sky island, no cars, no streetlights"},
    {"name": "Canyonlands National Park", "lat": 38.3269, "lon": -109.8783, "country": "USA", "region": "Utah", "bortle": 2, "designation": "IDA Gold Tier", "note": "Mesa Arch Milky Way, Island in the Sky district"},
    {"name": "Alqueva Dark Sky Reserve", "lat": 38.2000, "lon": -7.4833, "country": "Portugal", "region": "Alentejo", "bortle": 2, "designation": "Starlight Tourism Destination", "note": "First Starlight Tourism Destination certified"},
    {"name": "Ramon Crater (Mitzpe Ramon)", "lat": 30.6100, "lon": 34.8015, "country": "Israel", "region": "Negev", "bortle": 3, "designation": "Dark Sky Site", "note": "World's largest erosion crater, desert dark sky"},
    {"name": "Headlands Dark Sky Park", "lat": 45.7525, "lon": -84.7536, "country": "USA", "region": "Michigan", "bortle": 3, "designation": "IDA Park", "note": "Lake Michigan shore, aurora viewing possible"},
    {"name": "Coll Dark Sky Island", "lat": 56.6230, "lon": -6.5220, "country": "UK", "region": "Scotland", "bortle": 2, "designation": "IDA Community", "note": "Scottish island, minimal light pollution"},
    {"name": "Hortobagy National Park", "lat": 47.5833, "lon": 21.1500, "country": "Hungary", "region": "Hajdu-Bihar", "bortle": 3, "designation": "IDA Park", "note": "Hungarian Great Plain, first dark sky park in Hungary"},
    {"name": "Yeongyang Firefly Eco Park", "lat": 36.6647, "lon": 129.1187, "country": "South Korea", "region": "Gyeongsang", "bortle": 3, "designation": "IDA Park", "note": "Asia's first IDA certified Dark Sky Park"},
    {"name": "Cosmic Campground", "lat": 33.5700, "lon": -108.9700, "country": "USA", "region": "New Mexico", "bortle": 1, "designation": "IDA Sanctuary", "note": "One of only a few IDA Sanctuaries, pristine skies"},
    {"name": "Exmoor National Park", "lat": 51.1500, "lon": -3.6500, "country": "UK", "region": "Somerset/Devon", "bortle": 3, "designation": "IDA Dark Sky Reserve", "note": "England's first Dark Sky Reserve"},
    {"name": "Brecon Beacons", "lat": 51.8833, "lon": -3.4333, "country": "UK", "region": "Wales", "bortle": 3, "designation": "IDA Reserve", "note": "Wales' dark sky reserve, 500 km2"},
    {"name": "Mont-Megantic Observatory", "lat": 45.4553, "lon": -71.1522, "country": "Canada", "region": "Quebec", "bortle": 2, "designation": "IDA Reserve (First)", "note": "World's first International Dark Sky Reserve, 2007"},
    {"name": "Iriomote-Ishigaki National Park", "lat": 24.4032, "lon": 123.7664, "country": "Japan", "region": "Okinawa", "bortle": 2, "designation": "IDA Dark Sky Park", "note": "Japan's first dark sky park, Southern Cross visible"},
]

WAR_PHOTOGRAPHY_SITES = [
    {"name": "Omaha Beach, D-Day", "lat": 49.3703, "lon": -0.8700, "country": "France", "city": "Colleville-sur-Mer", "conflict": "World War II", "year": 1944, "photographer": "Robert Capa", "note": "Magnificent Eleven photos, June 6 1944"},
    {"name": "Iwo Jima (Ioto)", "lat": 24.7580, "lon": 141.2917, "country": "Japan", "city": "Ogasawara", "conflict": "World War II", "year": 1945, "photographer": "Joe Rosenthal", "note": "Raising the Flag, most reproduced photo in history"},
    {"name": "Hiroshima Peace Memorial", "lat": 34.3955, "lon": 132.4536, "country": "Japan", "city": "Hiroshima", "conflict": "World War II", "year": 1945, "photographer": "Various", "note": "Atomic Bomb Dome, August 6 1945"},
    {"name": "Berlin Wall - Brandenburg Gate", "lat": 52.5163, "lon": 13.3777, "country": "Germany", "city": "Berlin", "conflict": "Cold War", "year": 1961, "photographer": "Various", "note": "Symbol of Cold War division and 1989 reunification"},
    {"name": "Saigon - Reunification Palace", "lat": 10.7769, "lon": 106.6955, "country": "Vietnam", "city": "Ho Chi Minh City", "conflict": "Vietnam War", "year": 1975, "photographer": "Various", "note": "Fall of Saigon, tank through gates April 30 1975"},
    {"name": "Napalm Girl Road - Trang Bang", "lat": 11.0328, "lon": 106.3710, "country": "Vietnam", "city": "Tay Ninh", "conflict": "Vietnam War", "year": 1972, "photographer": "Nick Ut", "note": "Pulitzer Prize, changed public opinion on war"},
    {"name": "Auschwitz-Birkenau", "lat": 50.0343, "lon": 19.1781, "country": "Poland", "city": "Oswiecim", "conflict": "World War II / Holocaust", "year": 1945, "photographer": "Various", "note": "1.1 million victims, liberation photos by Red Army"},
    {"name": "Guernica", "lat": 43.3147, "lon": -2.6766, "country": "Spain", "city": "Guernica", "conflict": "Spanish Civil War", "year": 1937, "photographer": "Robert Capa", "note": "Bombing inspired Picasso's masterpiece"},
    {"name": "Vukovar Water Tower", "lat": 45.3448, "lon": 19.0037, "country": "Croatia", "city": "Vukovar", "conflict": "Croatian War", "year": 1991, "photographer": "Various", "note": "Symbol of Croatian resistance, 600+ shell hits"},
    {"name": "Sarajevo - Sniper Alley", "lat": 43.8563, "lon": 18.4131, "country": "Bosnia", "city": "Sarajevo", "conflict": "Bosnian War", "year": 1992, "photographer": "Various", "note": "Zmaja od Bosne street, 1,425 day siege"},
    {"name": "Kuwait Oil Fires", "lat": 29.3759, "lon": 47.9774, "country": "Kuwait", "city": "Kuwait City", "conflict": "Gulf War", "year": 1991, "photographer": "Sebastiao Salgado", "note": "600+ oil wells set ablaze, apocalyptic photos"},
    {"name": "Tiananmen Square", "lat": 39.9042, "lon": 116.3974, "country": "China", "city": "Beijing", "conflict": "Pro-Democracy Protests", "year": 1989, "photographer": "Jeff Widener", "note": "Tank Man, one of most iconic photographs ever"},
    {"name": "Ground Zero - World Trade Center", "lat": 40.7115, "lon": -74.0134, "country": "USA", "city": "New York", "conflict": "War on Terror", "year": 2001, "photographer": "Various", "note": "9/11 attacks, Falling Man by Richard Drew"},
    {"name": "Kabul - Sharbat Gula Location", "lat": 34.5553, "lon": 69.2075, "country": "Afghanistan", "city": "Kabul", "conflict": "Soviet-Afghan / War on Terror", "year": 1984, "photographer": "Steve McCurry", "note": "Afghan Girl, most famous NatGeo cover ever"},
    {"name": "Verdun Battlefield", "lat": 49.2033, "lon": 5.3867, "country": "France", "city": "Verdun", "conflict": "World War I", "year": 1916, "photographer": "Various", "note": "300 days of battle, 700,000 casualties, Douaumont Ossuary"},
    {"name": "Somme Battlefield - Thiepval", "lat": 50.0500, "lon": 2.6850, "country": "France", "city": "Thiepval", "conflict": "World War I", "year": 1916, "photographer": "Various", "note": "57,000 British casualties on first day alone"},
    {"name": "Stalingrad (Volgograd)", "lat": 48.7080, "lon": 44.5133, "country": "Russia", "city": "Volgograd", "conflict": "World War II", "year": 1943, "photographer": "Various", "note": "Turning point of WWII, 2 million casualties"},
    {"name": "Nagasaki Atomic Bomb Hypocenter", "lat": 32.7737, "lon": 129.8615, "country": "Japan", "city": "Nagasaki", "conflict": "World War II", "year": 1945, "photographer": "Yosuke Yamahata", "note": "Second atomic bomb, August 9 1945"},
    {"name": "Cu Chi Tunnels", "lat": 11.1426, "lon": 106.4633, "country": "Vietnam", "city": "Ho Chi Minh City", "conflict": "Vietnam War", "year": 1968, "photographer": "Various", "note": "250km tunnel network, Viet Cong guerrilla base"},
    {"name": "Aleppo - Old City", "lat": 36.1996, "lon": 37.1540, "country": "Syria", "city": "Aleppo", "conflict": "Syrian Civil War", "year": 2012, "photographer": "Various", "note": "UNESCO site devastated, before/after images"},
    {"name": "Mogadishu - Black Hawk Down Site", "lat": 2.0469, "lon": 45.3182, "country": "Somalia", "city": "Mogadishu", "conflict": "Somali Civil War", "year": 1993, "photographer": "Various", "note": "Battle of Mogadishu, US intervention"},
    {"name": "Normandy - Pointe du Hoc", "lat": 49.3955, "lon": -0.9895, "country": "France", "city": "Cricqueville-en-Bessin", "conflict": "World War II", "year": 1944, "photographer": "Robert Capa", "note": "Ranger assault on cliff-top gun battery"},
    {"name": "Pearl Harbor", "lat": 21.3649, "lon": -157.9507, "country": "USA", "city": "Honolulu", "conflict": "World War II", "year": 1941, "photographer": "Various", "note": "USS Arizona Memorial, December 7 1941"},
    {"name": "Gallipoli - Anzac Cove", "lat": 40.2533, "lon": 26.2850, "country": "Turkey", "city": "Canakkale", "conflict": "World War I", "year": 1915, "photographer": "Various", "note": "ANZAC landing, 8 months of trench warfare"},
    {"name": "My Lai Massacre Site", "lat": 15.1755, "lon": 108.8710, "country": "Vietnam", "city": "Quang Ngai", "conflict": "Vietnam War", "year": 1968, "photographer": "Ron Haeberle", "note": "504 civilians killed, photos exposed cover-up"},
    {"name": "Checkpoint Charlie", "lat": 52.5075, "lon": 13.3903, "country": "Germany", "city": "Berlin", "conflict": "Cold War", "year": 1961, "photographer": "Various", "note": "Most famous Berlin Wall crossing point"},
    {"name": "Dien Bien Phu", "lat": 21.3830, "lon": 103.0168, "country": "Vietnam", "city": "Dien Bien", "conflict": "First Indochina War", "year": 1954, "photographer": "Various", "note": "French defeat ended colonial rule in Indochina"},
    {"name": "Coventry Cathedral (Ruins)", "lat": 52.4068, "lon": -1.5070, "country": "UK", "city": "Coventry", "conflict": "World War II", "year": 1940, "photographer": "Various", "note": "Blitz bombing, old cathedral ruins beside new"},
    {"name": "Srebrenica Memorial", "lat": 44.1064, "lon": 19.2961, "country": "Bosnia", "city": "Srebrenica", "conflict": "Bosnian War", "year": 1995, "photographer": "Various", "note": "8,372 victims of genocide, Europe's worst since WWII"},
    {"name": "Rwandan Genocide Memorial", "lat": -1.9403, "lon": 29.8739, "country": "Rwanda", "city": "Kigali", "conflict": "Rwandan Civil War", "year": 1994, "photographer": "James Nachtwey", "note": "800,000 killed in 100 days, documented by photojournalists"},
]

UNDERWATER_PHOTOGRAPHY = [
    {"name": "Great Barrier Reef - Ribbon Reefs", "lat": -16.0817, "lon": 145.7750, "country": "Australia", "region": "Queensland", "depth_m": 30, "specialty": "Coral Gardens", "note": "World's largest reef system, 1,500 fish species"},
    {"name": "Raja Ampat Islands", "lat": -0.4903, "lon": 130.5259, "country": "Indonesia", "region": "West Papua", "depth_m": 40, "specialty": "Biodiversity Epicenter", "note": "75% of all known coral species, manta rays"},
    {"name": "Sipadan Island", "lat": 4.1150, "lon": 118.6284, "country": "Malaysia", "region": "Sabah", "depth_m": 40, "specialty": "Barracuda Tornado", "note": "Jacques Cousteau's favorite, barracuda walls"},
    {"name": "Red Sea - Ras Mohammed", "lat": 27.7297, "lon": 34.2534, "country": "Egypt", "region": "Sinai", "depth_m": 35, "specialty": "Wall Diving", "note": "Crystal clear water, shark reef, Yolanda wreck"},
    {"name": "Galapagos - Wolf Island", "lat": 1.3830, "lon": -91.8170, "country": "Ecuador", "region": "Galapagos", "depth_m": 35, "specialty": "Pelagic Encounters", "note": "Whale sharks, hammerheads, marine iguanas"},
    {"name": "Cenotes - Dos Ojos", "lat": 20.3267, "lon": -87.3916, "country": "Mexico", "region": "Quintana Roo", "depth_m": 10, "specialty": "Cave/Cenote", "note": "Underwater limestone caves, crystal-clear freshwater"},
    {"name": "Maldives - Ari Atoll", "lat": 3.8800, "lon": 72.8206, "country": "Maldives", "region": "South Ari", "depth_m": 30, "specialty": "Manta/Whale Shark", "note": "Year-round whale sharks, overwater bungalow access"},
    {"name": "Palau - Blue Corner", "lat": 7.0861, "lon": 134.2166, "country": "Palau", "region": "Koror", "depth_m": 30, "specialty": "Shark Wall", "note": "Hook diving, grey reef sharks, Napoleon wrasse"},
    {"name": "Cozumel Drift Dives", "lat": 20.4318, "lon": -86.9203, "country": "Mexico", "region": "Quintana Roo", "depth_m": 25, "specialty": "Drift Diving", "note": "Palancar Reef, visibility 30m+, easy currents"},
    {"name": "Truk Lagoon (Chuuk)", "lat": 7.4167, "lon": 151.7833, "country": "Micronesia", "region": "Chuuk State", "depth_m": 40, "specialty": "WWII Wrecks", "note": "60+ Japanese WWII ships, world's best wreck diving"},
    {"name": "Lembeh Strait", "lat": 1.4748, "lon": 125.2330, "country": "Indonesia", "region": "North Sulawesi", "depth_m": 25, "specialty": "Muck/Macro", "note": "Muck diving capital, mimic octopus, frogfish"},
    {"name": "Komodo National Park", "lat": -8.5500, "lon": 119.4833, "country": "Indonesia", "region": "East Nusa Tenggara", "depth_m": 30, "specialty": "Current Diving", "note": "Mantas, strong currents, dragons on shore"},
    {"name": "Thistlegorm Wreck", "lat": 27.8126, "lon": 33.9211, "country": "Egypt", "region": "Red Sea", "depth_m": 30, "specialty": "WWII Wreck", "note": "British WWII cargo ship, motorcycles & trains inside"},
    {"name": "Silfra Fissure", "lat": 64.2561, "lon": -21.1167, "country": "Iceland", "region": "Thingvellir", "depth_m": 18, "specialty": "Tectonic Rift", "note": "Between tectonic plates, 100m+ visibility"},
    {"name": "Tubbataha Reef", "lat": 8.9444, "lon": 119.9117, "country": "Philippines", "region": "Sulu Sea", "depth_m": 40, "specialty": "Remote Reef", "note": "UNESCO site, pristine coral, seasonal access only"},
    {"name": "Poor Knights Islands", "lat": -35.4667, "lon": 174.7333, "country": "New Zealand", "region": "Northland", "depth_m": 30, "specialty": "Temperate Reef", "note": "Cousteau's top 10, giant kelp forests"},
    {"name": "Belize Blue Hole", "lat": 17.3155, "lon": -87.5348, "country": "Belize", "region": "Lighthouse Reef", "depth_m": 40, "specialty": "Sinkhole", "note": "300m diameter, 125m deep, stalactites at 40m"},
    {"name": "Sardine Run - South Africa", "lat": -31.0000, "lon": 30.0000, "country": "South Africa", "region": "KwaZulu-Natal", "depth_m": 15, "specialty": "Migration Event", "note": "Billions of sardines, dolphins, sharks, whales"},
    {"name": "Anilao", "lat": 13.7630, "lon": 120.9295, "country": "Philippines", "region": "Batangas", "depth_m": 25, "specialty": "Macro Photography", "note": "Philippines' macro capital, nudibranch diversity"},
    {"name": "Isla Guadalupe - Great Whites", "lat": 29.1000, "lon": -118.2833, "country": "Mexico", "region": "Baja California", "depth_m": 10, "specialty": "Shark Cage", "note": "Clearest great white shark cage diving on Earth"},
    {"name": "Richelieu Rock", "lat": 9.3617, "lon": 98.0267, "country": "Thailand", "region": "Surin Islands", "depth_m": 35, "specialty": "Whale Sharks", "note": "Thailand's #1 dive site, seasonal whale sharks"},
    {"name": "Sodwana Bay", "lat": -27.5250, "lon": 32.6792, "country": "South Africa", "region": "KwaZulu-Natal", "depth_m": 30, "specialty": "Coelacanth Habitat", "note": "Living fossil coelacanth sightings, pristine reef"},
    {"name": "Bonaire Shore Diving", "lat": 12.1443, "lon": -68.2655, "country": "Netherlands Antilles", "region": "Bonaire", "depth_m": 30, "specialty": "Shore Access", "note": "86 named shore dive sites, entire coast is marine park"},
    {"name": "Cabo Pulmo Reef", "lat": 23.4420, "lon": -109.4248, "country": "Mexico", "region": "Baja California Sur", "depth_m": 20, "specialty": "Marine Recovery", "note": "460% biomass increase after fishing ban, jack balls"},
    {"name": "Wakatobi", "lat": -5.3333, "lon": 123.5833, "country": "Indonesia", "region": "Sulawesi", "depth_m": 30, "specialty": "House Reef", "note": "Pristine coral, pygmy seahorses, luxury liveaboard"},
    {"name": "Tiger Beach - Bahamas", "lat": 26.6080, "lon": -79.0050, "country": "Bahamas", "region": "Grand Bahama", "depth_m": 7, "specialty": "Tiger Sharks", "note": "Shallow water tiger shark encounters on white sand"},
    {"name": "Monterey Bay Kelp Forests", "lat": 36.6000, "lon": -121.9000, "country": "USA", "region": "California", "depth_m": 20, "specialty": "Kelp/Temperate", "note": "Giant kelp canopy, sea otters, harbor seals"},
    {"name": "Maaya Thila", "lat": 3.9000, "lon": 72.8500, "country": "Maldives", "region": "Ari Atoll", "depth_m": 30, "specialty": "Night Diving", "note": "Best night dive in Maldives, nurse sharks, morays"},
    {"name": "Cocos Island", "lat": 5.5280, "lon": -87.0580, "country": "Costa Rica", "region": "Pacific", "depth_m": 35, "specialty": "Hammerhead Schools", "note": "Schooling hammerheads, 36 hours offshore"},
    {"name": "SS Yongala Wreck", "lat": -19.3050, "lon": 147.6217, "country": "Australia", "region": "Queensland", "depth_m": 28, "specialty": "Wreck/Marine Life", "note": "Australia's best dive, giant groupers, sea snakes"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_map(center_lat: float, center_lon: float, zoom: int = 3) -> folium.Map:
    """Create a dark-themed folium map."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)
    return m


def _safe_popup(title: str, fields: dict, max_width: int = 280) -> folium.Popup:
    """Build an HTML popup with html-escaped user data."""
    safe_title = html_module.escape(str(title))
    lines = [
        f'<div style="max-width:{max_width}px;">',
        f'<strong style="font-size:0.9rem;">{safe_title}</strong>',
    ]
    for label, value in fields.items():
        if value:
            safe_val = html_module.escape(str(value))
            lines.append(
                f'<br/><span style="font-size:0.75rem; color:#999;">'
                f'{html_module.escape(label)}:</span> '
                f'<span style="font-size:0.78rem;">{safe_val}</span>'
            )
    lines.append("</div>")
    return folium.Popup("\n".join(lines), max_width=max_width + 20)


def _add_markers(m: folium.Map, items: list, lat_key: str, lon_key: str,
                 popup_fields: list, color: str, radius: int = 7):
    """Add CircleMarkers from a list of dicts to a folium Map."""
    for item in items:
        fields = {k: item.get(k, "") for k in popup_fields}
        popup = _safe_popup(item.get("name", "Unknown"), fields)
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=popup,
        ).add_to(m)


def _show_map(m: folium.Map, height: int = 500):
    """Render a folium map via Streamlit components."""
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=height)


def _csv_download(df: pd.DataFrame, filename: str, label: str, key: str):
    """Offer a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename,
                       mime="text/csv", key=key)


# ═══════════════════════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def _render_most_photographed():
    """World's Most Photographed Places."""
    data = MOST_PHOTOGRAPHED
    st.markdown("#### World's Most Photographed Places")
    st.caption("Iconic landmarks and destinations that attract billions of photographs every year.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    categories = list({d["category"] for d in data})
    total_photos = sum(d["est_photos_m"] for d in data)
    cols[0].metric("Total Locations", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Categories", len(categories))
    cols[3].metric("Est. Photos (M)", f"{total_photos:,.0f}")

    m = _build_map(25.0, 10.0, zoom=2)
    cat_colors = {
        "Landmark": ACCENT_PINK,
        "Monument": ACCENT_VIOLET,
        "Archaeological": ACCENT_AMBER,
        "Natural": ACCENT_EMERALD,
        "Urban": ACCENT_CYAN,
    }
    for item in data:
        color = cat_colors.get(item["category"], ACCENT_PINK)
        popup = _safe_popup(item["name"], {
            "City": item["city"],
            "Country": item["country"],
            "Category": item["category"],
            "Est. Photos (millions)": item["est_photos_m"],
            "Note": item["note"],
        })
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=max(5, item["est_photos_m"] / 10),
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("est_photos_m", ascending=False)
    st.dataframe(df[["name", "city", "country", "category", "est_photos_m", "note"]],
                 use_container_width=True)
    _csv_download(df, "most_photographed_places.csv",
                  "Download Most Photographed Places CSV", "dl_most_photo")


def _render_camera_manufacturing():
    """Camera Manufacturing History."""
    data = CAMERA_MANUFACTURING
    st.markdown("#### Camera Manufacturing History")
    st.caption("Historic and active camera & lens manufacturers around the world.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    oldest = min(d["founded"] for d in data)
    specialties = list({d["specialty"] for d in data})
    cols[0].metric("Manufacturers", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Oldest Founded", oldest)
    cols[3].metric("Specialties", len(specialties))

    m = _build_map(35.0, 20.0, zoom=2)
    country_colors = {
        "Germany": ACCENT_AMBER,
        "Japan": ACCENT_RED,
        "USA": ACCENT_BLUE,
        "Sweden": ACCENT_CYAN,
        "Denmark": ACCENT_TEAL,
        "Australia": ACCENT_EMERALD,
        "China": ACCENT_PINK,
        "UK": ACCENT_VIOLET,
        "Czech Republic": ACCENT_ORANGE,
        "Belgium": ACCENT_FUCHSIA,
    }
    for item in data:
        color = country_colors.get(item["country"], ACCENT_PINK)
        popup = _safe_popup(item["name"], {
            "City": item["city"],
            "Country": item["country"],
            "Founded": item["founded"],
            "Specialty": item["specialty"],
            "Note": item["note"],
        })
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("founded")
    st.dataframe(df[["name", "city", "country", "founded", "specialty", "note"]],
                 use_container_width=True)
    _csv_download(df, "camera_manufacturing_history.csv",
                  "Download Camera Manufacturing CSV", "dl_camera_mfg")


def _render_photography_museums():
    """Photography Museums & Galleries."""
    data = PHOTOGRAPHY_MUSEUMS
    st.markdown("#### Photography Museums & Galleries")
    st.caption("World-class institutions dedicated to the art and history of photography.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    oldest = min(d["founded"] for d in data)
    focuses = list({d["focus"] for d in data})
    cols[0].metric("Museums/Galleries", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Oldest Founded", oldest)
    cols[3].metric("Focus Areas", len(focuses))

    m = _build_map(35.0, 0.0, zoom=2)
    _add_markers(m, data, "lat", "lon",
                 ["city", "country", "founded", "focus", "note"],
                 ACCENT_VIOLET, radius=8)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("founded")
    st.dataframe(df[["name", "city", "country", "founded", "focus", "note"]],
                 use_container_width=True)
    _csv_download(df, "photography_museums.csv",
                  "Download Photography Museums CSV", "dl_photo_museums")


def _render_natgeo_locations():
    """Famous Photo Locations (National Geographic)."""
    data = NATGEO_FAMOUS_LOCATIONS
    st.markdown("#### Famous Photo Locations (National Geographic)")
    st.caption("Breathtaking natural and cultural locations immortalized by legendary photographers.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    oldest_year = min(d["year"] for d in data)
    named_photographers = [d["photographer"] for d in data if d["photographer"] != "Various"]
    cols[0].metric("Locations", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Earliest Year", oldest_year)
    cols[3].metric("Named Photographers", len(named_photographers))

    m = _build_map(20.0, 0.0, zoom=2)
    _add_markers(m, data, "lat", "lon",
                 ["state", "country", "photographer", "year", "note"],
                 ACCENT_EMERALD, radius=8)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("year")
    st.dataframe(df[["name", "country", "state", "photographer", "year", "note"]],
                 use_container_width=True)
    _csv_download(df, "natgeo_photo_locations.csv",
                  "Download NatGeo Photo Locations CSV", "dl_natgeo")


def _render_darkroom_heritage():
    """Darkroom & Film Heritage Sites."""
    data = DARKROOM_FILM_HERITAGE
    st.markdown("#### Darkroom & Film Heritage Sites")
    st.caption("Factories and facilities that produced the world's photographic films and papers.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    oldest = min(d["founded"] for d in data)
    types = list({d["type"] for d in data})
    cols[0].metric("Heritage Sites", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Oldest Founded", oldest)
    cols[3].metric("Facility Types", len(types))

    m = _build_map(40.0, 10.0, zoom=2)
    type_colors = {
        "Film Factory": ACCENT_ORANGE,
        "Film & Paper Factory": ACCENT_AMBER,
        "Film & Paper": ACCENT_AMBER,
        "Instant Film Factory": ACCENT_PINK,
        "Darkroom Equipment": ACCENT_VIOLET,
        "Enlarger Manufacturing": ACCENT_VIOLET,
        "Film Manufacturing": ACCENT_RED,
        "B&W Film & Paper": ACCENT_TEAL,
        "Analog Revival": ACCENT_CYAN,
        "Film Repurposing": ACCENT_FUCHSIA,
        "B&W Paper": ACCENT_EMERALD,
    }
    for item in data:
        color = type_colors.get(item["type"], ACCENT_ORANGE)
        popup = _safe_popup(item["name"], {
            "City": item["city"],
            "Country": item["country"],
            "Founded": item["founded"],
            "Type": item["type"],
            "Note": item["note"],
        })
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("founded")
    st.dataframe(df[["name", "city", "country", "founded", "type", "note"]],
                 use_container_width=True)
    _csv_download(df, "darkroom_film_heritage.csv",
                  "Download Darkroom & Film Heritage CSV", "dl_darkroom")


def _render_landscape_spots():
    """Iconic Landscape Photography Spots."""
    data = LANDSCAPE_SPOTS
    st.markdown("#### Iconic Landscape Photography Spots")
    st.caption("Dream destinations for landscape photographers, with best lighting conditions.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    types = list({d["type"] for d in data})
    lights = list({d["best_light"] for d in data})
    cols[0].metric("Photo Spots", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Landscape Types", len(types))
    cols[3].metric("Light Conditions", len(lights))

    m = _build_map(30.0, 0.0, zoom=2)
    _add_markers(m, data, "lat", "lon",
                 ["region", "country", "type", "best_light", "note"],
                 ACCENT_CYAN, radius=8)
    _show_map(m)

    df = pd.DataFrame(data)
    st.dataframe(df[["name", "country", "region", "type", "best_light", "note"]],
                 use_container_width=True)
    _csv_download(df, "landscape_photography_spots.csv",
                  "Download Landscape Spots CSV", "dl_landscape")


def _render_street_photography():
    """Street Photography Capitals."""
    data = STREET_PHOTOGRAPHY_CAPITALS
    st.markdown("#### Street Photography Capitals")
    st.caption("Cities celebrated for their vibrant street life and photographic culture.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    styles = list({d["style"] for d in data})
    total_pop = sum(d["population_m"] for d in data)
    cols[0].metric("Cities", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Styles", len(styles))
    cols[3].metric("Total Pop. (M)", f"{total_pop:,.1f}")

    m = _build_map(20.0, 20.0, zoom=2)
    for item in data:
        size = max(5, min(12, item["population_m"] / 2))
        popup = _safe_popup(item["name"], {
            "Country": item["country"],
            "Population (M)": f"{item['population_m']:.2f}",
            "Style": item["style"],
            "Famous Photographer": item["famous_photographer"],
            "Note": item["note"],
        })
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=size,
            color=ACCENT_RED, fill=True, fill_color=ACCENT_RED,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("population_m", ascending=False)
    st.dataframe(df[["name", "country", "population_m", "style", "famous_photographer", "note"]],
                 use_container_width=True)
    _csv_download(df, "street_photography_capitals.csv",
                  "Download Street Photography Capitals CSV", "dl_street_photo")


def _render_dark_sky():
    """Astrophotography Dark Sky Sites."""
    data = DARK_SKY_SITES
    st.markdown("#### Astrophotography Dark Sky Sites")
    st.caption("Certified dark sky reserves and observatories for capturing the cosmos.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    designations = list({d["designation"] for d in data})
    avg_bortle = sum(d["bortle"] for d in data) / len(data)
    gold_tier = sum(1 for d in data if "Gold" in d["designation"])
    cols[0].metric("Dark Sky Sites", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Avg Bortle Scale", f"{avg_bortle:.1f}")
    cols[3].metric("Gold Tier / Sanctuary", gold_tier)

    m = _build_map(30.0, 0.0, zoom=2)
    for item in data:
        bortle = item["bortle"]
        if bortle <= 1:
            color = "#1e3a5f"
            radius = 10
        elif bortle <= 2:
            color = "#2563eb"
            radius = 8
        else:
            color = "#60a5fa"
            radius = 6
        popup = _safe_popup(item["name"], {
            "Region": item["region"],
            "Country": item["country"],
            "Bortle Scale": item["bortle"],
            "Designation": item["designation"],
            "Note": item["note"],
        })
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.8, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("bortle")
    st.dataframe(df[["name", "country", "region", "bortle", "designation", "note"]],
                 use_container_width=True)
    _csv_download(df, "dark_sky_sites.csv",
                  "Download Dark Sky Sites CSV", "dl_dark_sky")


def _render_war_photography():
    """War Photography Historic Sites."""
    data = WAR_PHOTOGRAPHY_SITES
    st.markdown("#### War Photography Historic Sites")
    st.caption("Locations where iconic war photographs were taken or conflicts documented.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    conflicts = list({d["conflict"] for d in data})
    named = [d for d in data if d["photographer"] != "Various"]
    cols[0].metric("Historic Sites", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Conflicts Covered", len(conflicts))
    cols[3].metric("Named Photographers", len(named))

    m = _build_map(35.0, 20.0, zoom=2)
    conflict_colors = {
        "World War I": ACCENT_AMBER,
        "World War II": ACCENT_RED,
        "World War II / Holocaust": ACCENT_RED,
        "Cold War": ACCENT_BLUE,
        "Vietnam War": ACCENT_EMERALD,
        "First Indochina War": ACCENT_EMERALD,
        "Spanish Civil War": ACCENT_ORANGE,
        "Bosnian War": ACCENT_VIOLET,
        "Croatian War": ACCENT_VIOLET,
        "Gulf War": ACCENT_CYAN,
        "Syrian Civil War": ACCENT_PINK,
        "War on Terror": ACCENT_TEAL,
        "Soviet-Afghan / War on Terror": ACCENT_TEAL,
        "Pro-Democracy Protests": ACCENT_FUCHSIA,
        "Somali Civil War": ACCENT_ORANGE,
        "Rwandan Civil War": ACCENT_PINK,
    }
    for item in data:
        color = conflict_colors.get(item["conflict"], ACCENT_TEAL)
        popup = _safe_popup(item["name"], {
            "City": item["city"],
            "Country": item["country"],
            "Conflict": item["conflict"],
            "Year": item["year"],
            "Photographer": item["photographer"],
            "Note": item["note"],
        })
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("year")
    st.dataframe(df[["name", "country", "conflict", "year", "photographer", "note"]],
                 use_container_width=True)
    _csv_download(df, "war_photography_sites.csv",
                  "Download War Photography Sites CSV", "dl_war_photo")


def _render_underwater_photography():
    """Underwater Photography Hotspots."""
    data = UNDERWATER_PHOTOGRAPHY
    st.markdown("#### Underwater Photography Hotspots")
    st.caption("Premier dive destinations for underwater photography enthusiasts.")

    cols = st.columns(4)
    countries = list({d["country"] for d in data})
    specialties = list({d["specialty"] for d in data})
    avg_depth = sum(d["depth_m"] for d in data) / len(data)
    cols[0].metric("Dive Sites", len(data))
    cols[1].metric("Countries", len(countries))
    cols[2].metric("Specialties", len(specialties))
    cols[3].metric("Avg Depth (m)", f"{avg_depth:.0f}")

    m = _build_map(5.0, 90.0, zoom=2)
    for item in data:
        depth = item["depth_m"]
        if depth <= 15:
            color = "#22d3ee"
            radius = 6
        elif depth <= 30:
            color = "#0891b2"
            radius = 8
        else:
            color = "#164e63"
            radius = 10
        popup = _safe_popup(item["name"], {
            "Region": item["region"],
            "Country": item["country"],
            "Max Depth (m)": item["depth_m"],
            "Specialty": item["specialty"],
            "Note": item["note"],
        })
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    df = pd.DataFrame(data)
    df = df.sort_values("depth_m", ascending=False)
    st.dataframe(df[["name", "country", "region", "depth_m", "specialty", "note"]],
                 use_container_width=True)
    _csv_download(df, "underwater_photography_hotspots.csv",
                  "Download Underwater Photography CSV", "dl_underwater")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_photography_maps_tab():
    """Main entry point for the Photography & Camera Explorer tab."""
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>Photography & Camera Explorer</h4>'
        '<p>Iconic photo locations, camera factories, photography museums & famous viewpoints</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Select Map Mode", [
        "World's Most Photographed Places",
        "Camera Manufacturing History",
        "Photography Museums & Galleries",
        "Famous Photo Locations (National Geographic)",
        "Darkroom & Film Heritage Sites",
        "Iconic Landscape Photography Spots",
        "Street Photography Capitals",
        "Astrophotography Dark Sky Sites",
        "War Photography Historic Sites",
        "Underwater Photography Hotspots",
    ], key="photography_maps_mode")

    st.divider()

    if mode == "World's Most Photographed Places":
        _render_most_photographed()
    elif mode == "Camera Manufacturing History":
        _render_camera_manufacturing()
    elif mode == "Photography Museums & Galleries":
        _render_photography_museums()
    elif mode == "Famous Photo Locations (National Geographic)":
        _render_natgeo_locations()
    elif mode == "Darkroom & Film Heritage Sites":
        _render_darkroom_heritage()
    elif mode == "Iconic Landscape Photography Spots":
        _render_landscape_spots()
    elif mode == "Street Photography Capitals":
        _render_street_photography()
    elif mode == "Astrophotography Dark Sky Sites":
        _render_dark_sky()
    elif mode == "War Photography Historic Sites":
        _render_war_photography()
    elif mode == "Underwater Photography Hotspots":
        _render_underwater_photography()
