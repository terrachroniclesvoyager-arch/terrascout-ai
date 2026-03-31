# -*- coding: utf-8 -*-
"""
Water Parks & Swimming Explorer module for TerraScout AI.
Provides 10 interactive map modes covering water parks, natural pools,
infinity pools, historic baths, Olympic venues, water slides, wave pools,
thermal bathing, river swimming, and lake swimming destinations.

Data sources:
  - Curated datasets for worldwide aquatic attractions
  - Overpass API for nearby amenities (optional)
All free, no API key required.
"""

import io
import logging
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import requests
import html as html_module
from streamlit.components.v1 import html as st_html

logger = logging.getLogger(__name__)

# ===================================================================
# CONSTANTS & COLOR PALETTE
# ===================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"
BORDER = "#2a3550"
ACCENT = "#06b6d4"

MAP_MODES = [
    "1. World's Best Water Parks",
    "2. Natural Swimming Pools",
    "3. Famous Infinity Pools",
    "4. Historic Public Baths",
    "5. Olympic Swimming Venues",
    "6. Water Slides Records",
    "7. Wave Pools & Surf Parks",
    "8. Thermal Bathing Culture",
    "9. River Swimming Spots",
    "10. Lake Swimming",
]

# ===================================================================
# 1. WORLD'S BEST WATER PARKS (curated)
# ===================================================================
WATER_PARKS = [
    {"name": "Typhoon Lagoon", "location": "Orlando, FL, USA", "lat": 28.3655, "lon": -81.5298,
     "desc": "Disney's tropical storm-themed water park with one of the world's largest wave pools",
     "highlights": "Surf pool, Crush 'n' Gusher, Castaway Creek", "year_opened": 1989, "color": "#06b6d4"},
    {"name": "Aquaventure Waterpark", "location": "Dubai, UAE", "lat": 25.1304, "lon": 55.1174,
     "desc": "Atlantis The Palm's record-breaking waterpark with shark-filled lagoon",
     "highlights": "Leap of Faith, Aquaconda, Shark Attack tunnel", "year_opened": 2008, "color": "#3b82f6"},
    {"name": "Siam Park", "location": "Tenerife, Spain", "lat": 28.0713, "lon": -16.7260,
     "desc": "Thai-themed water kingdom repeatedly voted world's best water park",
     "highlights": "Tower of Power, The Dragon, Wave Palace", "year_opened": 2008, "color": "#8b5cf6"},
    {"name": "Therme Erding", "location": "Erding, Germany", "lat": 48.2900, "lon": 11.9064,
     "desc": "World's largest thermal spa and water slide complex",
     "highlights": "Galaxy Erding slides, VitalityOasis, 27 slides", "year_opened": 1999, "color": "#10b981"},
    {"name": "Waterbom Bali", "location": "Kuta, Bali, Indonesia", "lat": -8.7234, "lon": 115.1699,
     "desc": "Eco-friendly tropical water park set among lush gardens",
     "highlights": "Climax, Smashdown 2.0, Lazy River", "year_opened": 1993, "color": "#f59e0b"},
    {"name": "Blizzard Beach", "location": "Orlando, FL, USA", "lat": 28.3530, "lon": -81.5769,
     "desc": "Disney's ski-resort-themed water park with Summit Plummet free-fall slide",
     "highlights": "Summit Plummet (120 ft), Teamboat Springs, Tike's Peak", "year_opened": 1995, "color": "#e0f2fe"},
    {"name": "Tropical Islands", "location": "Krausnick, Germany", "lat": 52.0388, "lon": 13.7475,
     "desc": "Indoor tropical water park inside a former airship hangar - world's largest indoor pool",
     "highlights": "Tropical Sea, Bali Lagoon, rainforest, 66,000 m2 hall", "year_opened": 2004, "color": "#22c55e"},
    {"name": "Yas Waterworld", "location": "Abu Dhabi, UAE", "lat": 24.4886, "lon": 54.6088,
     "desc": "Pearl-diving themed mega waterpark with 45 rides and attractions",
     "highlights": "Dawwama, Liwa Loop, Jebel Drop, Bubble's Barrel", "year_opened": 2013, "color": "#eab308"},
    {"name": "Beach Park", "location": "Fortaleza, Brazil", "lat": -3.8310, "lon": -38.4059,
     "desc": "Tropical beachside water park home to Insano - once the world's tallest slide",
     "highlights": "Insano (41m), Kalafrio, Arrepius", "year_opened": 1985, "color": "#14b8a6"},
    {"name": "Caribbean Bay", "location": "Yongin, South Korea", "lat": 37.2927, "lon": 127.2020,
     "desc": "One of the world's most-visited water parks inside Everland Resort",
     "highlights": "Mega Storm, Tower Boomerango, indoor/outdoor zones", "year_opened": 1996, "color": "#a855f7"},
    {"name": "Volcano Bay", "location": "Orlando, FL, USA", "lat": 28.4621, "lon": -81.4718,
     "desc": "Universal's TapuTapu wearable-tech water theme park with Krakatau volcano",
     "highlights": "Ko'okiri Body Plunge, Krakatau Aqua Coaster, Wave Village", "year_opened": 2017, "color": "#ef4444"},
    {"name": "Chimelong Water Park", "location": "Guangzhou, China", "lat": 23.0012, "lon": 113.3300,
     "desc": "World record-holding water park by annual attendance",
     "highlights": "Behemoth Bowl, Giant Water Fortress, Super Horn", "year_opened": 2007, "color": "#f97316"},
    {"name": "Wild Wadi Waterpark", "location": "Dubai, UAE", "lat": 25.1411, "lon": 55.1875,
     "desc": "Arabian adventure-themed park in the shadow of the Burj Al Arab",
     "highlights": "Jumeirah Sceirah, Master Blaster, Tantrum Alley", "year_opened": 1999, "color": "#0ea5e9"},
    {"name": "Schlitterbahn", "location": "New Braunfels, TX, USA", "lat": 29.7081, "lon": -98.1311,
     "desc": "Legendary Texas water park with heated spring-fed rides and river adventures",
     "highlights": "Master Blaster, Torrent River, The Falls", "year_opened": 1966, "color": "#84cc16"},
    {"name": "Wuxi Sunac Water World", "location": "Wuxi, China", "lat": 31.5689, "lon": 120.2186,
     "desc": "Massive indoor water park with year-round tropical climate",
     "highlights": "Indoor wave pool, tube slides, themed zones", "year_opened": 2019, "color": "#06b6d4"},
]

# ===================================================================
# 2. NATURAL SWIMMING POOLS (curated)
# ===================================================================
NATURAL_POOLS = [
    {"name": "Ik Kil Cenote", "location": "Yucatan, Mexico", "lat": 20.6618, "lon": -88.5514,
     "type": "Cenote", "desc": "Sacred Maya cenote with hanging vines and turquoise water 26m below ground",
     "depth_m": 40, "color": "#06b6d4"},
    {"name": "Gran Cenote", "location": "Tulum, Mexico", "lat": 20.2457, "lon": -87.4680,
     "type": "Cenote", "desc": "Crystal-clear cavern cenote popular for snorkeling and diving",
     "depth_m": 10, "color": "#0ea5e9"},
    {"name": "To Sua Ocean Trench", "location": "Lotofaga, Samoa", "lat": -13.8683, "lon": -171.7517,
     "type": "Ocean Trench", "desc": "30-meter deep natural swimming hole connected to the sea via lava tubes",
     "depth_m": 30, "color": "#3b82f6"},
    {"name": "Fairy Pools", "location": "Isle of Skye, Scotland", "lat": 57.2514, "lon": -6.2823,
     "type": "Rock Pool", "desc": "Crystal-clear blue pools and waterfalls in the Cuillin Mountains",
     "depth_m": 3, "color": "#8b5cf6"},
    {"name": "Giola Lagoon", "location": "Thassos, Greece", "lat": 40.6000, "lon": 24.6667,
     "type": "Rock Pool", "desc": "Natural rock pool carved into cliff overlooking the Aegean Sea",
     "depth_m": 3, "color": "#14b8a6"},
    {"name": "Devil's Pool", "location": "Victoria Falls, Zambia", "lat": -17.9244, "lon": 25.8567,
     "type": "Rock Pool", "desc": "Infinity pool at the edge of Victoria Falls - swim to the precipice",
     "depth_m": 2, "color": "#ef4444"},
    {"name": "Hamilton Pool", "location": "Austin, TX, USA", "lat": 30.3422, "lon": -98.1266,
     "type": "Grotto", "desc": "Collapsed grotto with 15m waterfall and jade-green swimming hole",
     "depth_m": 7, "color": "#10b981"},
    {"name": "Kuang Si Falls", "location": "Luang Prabang, Laos", "lat": 19.7481, "lon": 101.9944,
     "type": "Waterfall Pool", "desc": "Multi-tiered turquoise waterfalls with natural swimming pools",
     "depth_m": 5, "color": "#22c55e"},
    {"name": "Pamukkale Travertines", "location": "Denizli, Turkey", "lat": 37.9203, "lon": 29.1201,
     "type": "Thermal Pool", "desc": "White travertine terraces filled with warm mineral-rich water",
     "depth_m": 1, "color": "#f0f9ff"},
    {"name": "Blue Lagoon (Grindavik)", "location": "Reykjavik, Iceland", "lat": 63.8804, "lon": -22.4495,
     "type": "Geothermal", "desc": "Milky-blue geothermal spa amid black lava fields",
     "depth_m": 1.5, "color": "#7dd3fc"},
    {"name": "Havasu Falls", "location": "Supai, AZ, USA", "lat": 36.2552, "lon": -112.6979,
     "type": "Waterfall Pool", "desc": "Stunning blue-green waterfall in the Grand Canyon's Havasupai reservation",
     "depth_m": 6, "color": "#0891b2"},
    {"name": "Cenote Suytun", "location": "Valladolid, Mexico", "lat": 20.6353, "lon": -88.1908,
     "type": "Cenote", "desc": "Underground cenote with a single beam of light illuminating a stone platform",
     "depth_m": 15, "color": "#1e40af"},
    {"name": "Queen's Bath", "location": "Kauai, HI, USA", "lat": 22.2292, "lon": -159.3572,
     "type": "Tidal Pool", "desc": "Volcanic tidal pool on Kauai's north shore formed by ancient lava flows",
     "depth_m": 2, "color": "#0d9488"},
    {"name": "Hierve el Agua", "location": "Oaxaca, Mexico", "lat": 16.8661, "lon": -96.2756,
     "type": "Petrified Waterfall", "desc": "Mineral spring infinity pools on a cliff with petrified waterfall formations",
     "depth_m": 1, "color": "#67e8f9"},
    {"name": "Cano Cristales", "location": "Serrania de la Macarena, Colombia", "lat": 2.2484, "lon": -73.7894,
     "type": "River Pool", "desc": "Rainbow river with red, blue, yellow and green aquatic plants",
     "depth_m": 2, "color": "#f43f5e"},
]

# ===================================================================
# 3. FAMOUS INFINITY POOLS (curated)
# ===================================================================
INFINITY_POOLS = [
    {"name": "Marina Bay Sands SkyPark", "location": "Singapore", "lat": 1.2834, "lon": 103.8607,
     "hotel": "Marina Bay Sands", "desc": "Iconic 150m rooftop infinity pool 57 stories above Singapore",
     "elevation_m": 200, "color": "#06b6d4"},
    {"name": "Hanging Gardens of Bali", "location": "Ubud, Bali", "lat": -8.4019, "lon": 115.3792,
     "hotel": "Hanging Gardens of Bali", "desc": "Multi-level infinity pools cascading into the rainforest canopy",
     "elevation_m": 350, "color": "#10b981"},
    {"name": "Hotel du Cap-Eden-Roc", "location": "Antibes, France", "lat": 43.5513, "lon": 7.1278,
     "hotel": "Hotel du Cap-Eden-Roc", "desc": "Legendary cliffside saltwater pool on the French Riviera since 1914",
     "elevation_m": 10, "color": "#3b82f6"},
    {"name": "Grace Hotel Santorini", "location": "Santorini, Greece", "lat": 36.4615, "lon": 25.3753,
     "hotel": "Grace Hotel", "desc": "Caldera-edge infinity pool with views over the Aegean and volcano",
     "elevation_m": 250, "color": "#8b5cf6"},
    {"name": "Jade Mountain", "location": "St. Lucia, Caribbean", "lat": 13.8560, "lon": -61.0680,
     "hotel": "Jade Mountain Resort", "desc": "Open-wall suites with private infinity pools facing the Pitons",
     "elevation_m": 180, "color": "#22c55e"},
    {"name": "Ubud Hanging Gardens Pool", "location": "Ubud, Bali", "lat": -8.4100, "lon": 115.3600,
     "hotel": "Kamandalu Ubud", "desc": "Jungle infinity pool overlooking terraced rice paddies and tropical valley",
     "elevation_m": 300, "color": "#14b8a6"},
    {"name": "Hotel Caruso Pool", "location": "Ravello, Italy", "lat": 40.6492, "lon": 14.6117,
     "hotel": "Belmond Hotel Caruso", "desc": "Infinity pool perched above the Amalfi Coast with sweeping sea views",
     "elevation_m": 350, "color": "#f59e0b"},
    {"name": "The Mulia Bali", "location": "Nusa Dua, Bali", "lat": -8.8175, "lon": 115.2320,
     "hotel": "The Mulia", "desc": "Ultra-luxury beachfront infinity pool with Indian Ocean panorama",
     "elevation_m": 5, "color": "#0ea5e9"},
    {"name": "Alila Villas Uluwatu", "location": "Uluwatu, Bali", "lat": -8.8152, "lon": 115.1247,
     "hotel": "Alila Villas Uluwatu", "desc": "Clifftop infinity pool 100m above the Indian Ocean",
     "elevation_m": 100, "color": "#6366f1"},
    {"name": "Katikies Hotel", "location": "Oia, Santorini", "lat": 36.4621, "lon": 25.3748,
     "hotel": "Katikies Hotel", "desc": "Three cascading infinity pools on the caldera cliff of Oia",
     "elevation_m": 200, "color": "#ec4899"},
    {"name": "Four Seasons Bora Bora", "location": "Bora Bora, French Polynesia", "lat": -16.5004, "lon": -151.7415,
     "hotel": "Four Seasons Resort", "desc": "Overwater infinity pool with Mt. Otemanu views in the South Pacific",
     "elevation_m": 3, "color": "#0891b2"},
    {"name": "Hoshinoya Bali", "location": "Ubud, Bali", "lat": -8.4622, "lon": 115.3242,
     "hotel": "Hoshinoya Bali", "desc": "Crescent-shaped infinity canal pool winding through lush tropical gardens",
     "elevation_m": 250, "color": "#059669"},
]

# ===================================================================
# 4. HISTORIC PUBLIC BATHS (curated)
# ===================================================================
HISTORIC_BATHS = [
    {"name": "Terme di Caracalla", "location": "Rome, Italy", "lat": 41.8790, "lon": 12.4924,
     "type": "Roman Thermae", "desc": "Massive 3rd-century Roman bath complex that held 1,600 bathers",
     "era": "212-216 AD", "color": "#ef4444"},
    {"name": "Roman Baths", "location": "Bath, England", "lat": 51.3812, "lon": -2.3596,
     "type": "Roman Thermae", "desc": "Remarkably preserved Roman bathing complex fed by natural hot springs",
     "era": "60-70 AD", "color": "#dc2626"},
    {"name": "Hammam al-Ayn", "location": "Damascus, Syria", "lat": 33.5138, "lon": 36.3106,
     "type": "Turkish Hammam", "desc": "One of the oldest continuously operating hammams in the world",
     "era": "12th century", "color": "#f97316"},
    {"name": "Cagaloglu Hamami", "location": "Istanbul, Turkey", "lat": 41.0084, "lon": 28.9750,
     "type": "Turkish Hammam", "desc": "Grand Ottoman hammam built in 1741 - one of Istanbul's most famous",
     "era": "1741", "color": "#f59e0b"},
    {"name": "Rudas Baths", "location": "Budapest, Hungary", "lat": 47.4862, "lon": 19.0489,
     "type": "Ottoman Bath", "desc": "16th-century Ottoman thermal bath with octagonal pool under a domed roof",
     "era": "1566", "color": "#eab308"},
    {"name": "Gellert Baths", "location": "Budapest, Hungary", "lat": 47.4833, "lon": 19.0531,
     "type": "Art Nouveau Bath", "desc": "Ornate Art Nouveau thermal bath complex with wave pool and open-air terraces",
     "era": "1918", "color": "#a855f7"},
    {"name": "Szechenyi Baths", "location": "Budapest, Hungary", "lat": 47.5188, "lon": 19.0823,
     "type": "Neo-Baroque Bath", "desc": "Largest medicinal bath in Europe with 18 pools in a yellow neo-baroque palace",
     "era": "1913", "color": "#8b5cf6"},
    {"name": "Dogo Onsen", "location": "Matsuyama, Japan", "lat": 33.8522, "lon": 132.7878,
     "type": "Japanese Onsen", "desc": "Japan's oldest onsen - 3,000 years of bathing history, inspiration for Spirited Away",
     "era": "c. 700 AD", "color": "#ec4899"},
    {"name": "Oedo Onsen Monogatari", "location": "Tokyo, Japan", "lat": 35.6250, "lon": 139.7750,
     "type": "Japanese Sento", "desc": "Edo-period themed hot spring theme park on Tokyo Bay",
     "era": "2003 (Edo theme)", "color": "#f472b6"},
    {"name": "Friedrichsbad", "location": "Baden-Baden, Germany", "lat": 48.7611, "lon": 8.2400,
     "type": "Roman-Irish Bath", "desc": "Renaissance bathhouse with Roman-Irish bathing ritual since 1877",
     "era": "1877", "color": "#14b8a6"},
    {"name": "Thermes de Cluny", "location": "Paris, France", "lat": 48.8505, "lon": 2.3442,
     "type": "Roman Thermae", "desc": "Gallo-Roman baths from the 1st century, now part of the Musee de Cluny",
     "era": "1st-3rd century AD", "color": "#b91c1c"},
    {"name": "Banyas al-Sham", "location": "Aleppo, Syria", "lat": 36.1998, "lon": 37.1560,
     "type": "Turkish Hammam", "desc": "Medieval hammam in Aleppo's historic souk district",
     "era": "13th century", "color": "#d97706"},
    {"name": "Takegawara Onsen", "location": "Beppu, Japan", "lat": 33.2789, "lon": 131.5057,
     "type": "Japanese Onsen", "desc": "Historic sand bath onsen from the Meiji era with traditional architecture",
     "era": "1879", "color": "#e11d48"},
    {"name": "Terme di Saturnia", "location": "Grosseto, Italy", "lat": 42.6500, "lon": 11.5125,
     "type": "Thermal Springs", "desc": "Etruscan-era sulfurous hot springs cascading through travertine terraces",
     "era": "Pre-Roman", "color": "#0d9488"},
]

# ===================================================================
# 5. OLYMPIC SWIMMING VENUES (curated)
# ===================================================================
OLYMPIC_VENUES = [
    {"name": "London Aquatics Centre", "location": "London, UK", "lat": 51.5414, "lon": -0.0135,
     "year": 2012, "architect": "Zaha Hadid", "desc": "Wave-shaped roof designed by Zaha Hadid for the 2012 Olympics",
     "legacy": "Public swimming, diving, water polo", "color": "#3b82f6"},
    {"name": "Beijing Water Cube", "location": "Beijing, China", "lat": 39.9928, "lon": 116.3850,
     "year": 2008, "architect": "PTW Architects", "desc": "ETFE-clad bubble structure where 25 world records were broken",
     "legacy": "Water park and swimming center", "color": "#06b6d4"},
    {"name": "Tokyo Aquatics Centre", "location": "Tokyo, Japan", "lat": 35.6469, "lon": 139.8375,
     "year": 2020, "architect": "Yamashita Sekkei", "desc": "15,000-seat venue for the 2020 (2021) Olympics with massive timber roof",
     "legacy": "Competition and public swimming", "color": "#ef4444"},
    {"name": "Sydney International Aquatic Centre", "location": "Sydney, Australia", "lat": -33.8468, "lon": 151.0693,
     "year": 2000, "architect": "Philip Cox", "desc": "Olympic Park venue where Ian Thorpe became the Thorpedo",
     "legacy": "Public swimming and events", "color": "#f59e0b"},
    {"name": "Centre Aquatique Olympique", "location": "Saint-Denis, Paris, France", "lat": 48.9303, "lon": 2.3556,
     "year": 2024, "architect": "VenhoevenCS & Ateliers 2/3/4/", "desc": "Timber and photovoltaic-roofed aquatics center for Paris 2024",
     "legacy": "Community aquatics center", "color": "#8b5cf6"},
    {"name": "Piscina Municipal de Montjuic", "location": "Barcelona, Spain", "lat": 41.3626, "lon": 2.1538,
     "year": 1992, "architect": "Original 1929, renovated", "desc": "Outdoor Olympic diving pool with panoramic views over Barcelona",
     "legacy": "Public pool and diving facility", "color": "#f97316"},
    {"name": "Olympic Swimming Pool (Helsinki)", "location": "Helsinki, Finland", "lat": 60.1870, "lon": 24.9271,
     "year": 1952, "architect": "Jorma Jarvi", "desc": "1952 Helsinki Olympics outdoor pool - pioneering modern Games",
     "legacy": "Heritage site and public pool", "color": "#10b981"},
    {"name": "Olympia-Schwimmhalle", "location": "Munich, Germany", "lat": 48.1748, "lon": 11.5524,
     "year": 1972, "architect": "Behnisch & Partners", "desc": "Tent-roofed pool under the iconic Munich Olympic Park tensile roof",
     "legacy": "Public swimming and events", "color": "#22c55e"},
    {"name": "Georgia Tech Aquatic Center", "location": "Atlanta, GA, USA", "lat": 33.7729, "lon": -84.3924,
     "year": 1996, "architect": "Various", "desc": "Home to the 1996 Atlanta Olympics swimming events",
     "legacy": "Georgia Tech campus recreation", "color": "#eab308"},
    {"name": "Aquatics Centre (Rio)", "location": "Rio de Janeiro, Brazil", "lat": -22.9720, "lon": -43.3952,
     "year": 2016, "architect": "Various", "desc": "Temporary venue in Barra Olympic Park for Rio 2016",
     "legacy": "Two 50m pools relocated to public facilities", "color": "#14b8a6"},
    {"name": "Foro Italico Pool", "location": "Rome, Italy", "lat": 41.9342, "lon": 12.4564,
     "year": 1960, "architect": "Enrico Del Debbio", "desc": "1960 Rome Olympics outdoor pool in the Fascist-era Foro Italico complex",
     "legacy": "International swimming competitions", "color": "#dc2626"},
    {"name": "Susie O'Neill Pool", "location": "Brisbane, Australia", "lat": -27.4686, "lon": 153.0218,
     "year": 2032, "architect": "TBD", "desc": "Planned aquatics venue for the Brisbane 2032 Olympics",
     "legacy": "Future community aquatics hub", "color": "#a855f7"},
]

# ===================================================================
# 6. WATER SLIDES RECORDS (curated)
# ===================================================================
WATER_SLIDES = [
    {"name": "Verruckt (demolished)", "location": "Kansas City, KS, USA", "lat": 39.0797, "lon": -94.6100,
     "record": "Tallest ever", "height_m": 51.4, "speed_kmh": 105,
     "desc": "Former world's tallest water slide at 168.7 ft - demolished after fatal accident",
     "park": "Schlitterbahn Kansas City", "color": "#ef4444"},
    {"name": "Kilimanjaro", "location": "Rio de Janeiro, Brazil", "lat": -22.8700, "lon": -43.4132,
     "record": "Tallest operating (Americas)", "height_m": 49.9, "speed_kmh": 100,
     "desc": "41-story near-vertical body slide reaching highway speeds",
     "park": "Aldeia das Aguas Park Resort", "color": "#f97316"},
    {"name": "Tower of Power", "location": "Tenerife, Spain", "lat": 28.0713, "lon": -16.7260,
     "record": "Iconic near-vertical", "height_m": 28, "speed_kmh": 80,
     "desc": "Near-vertical drop through a shark-filled aquarium tunnel at Siam Park",
     "park": "Siam Park", "color": "#8b5cf6"},
    {"name": "Leap of Faith", "location": "Dubai, UAE", "lat": 25.1304, "lon": 55.1174,
     "record": "Most famous plunge", "height_m": 27.5, "speed_kmh": 75,
     "desc": "Near-vertical body slide through a shark lagoon tunnel",
     "park": "Aquaventure Waterpark", "color": "#3b82f6"},
    {"name": "Insano", "location": "Fortaleza, Brazil", "lat": -3.8310, "lon": -38.4059,
     "record": "Former tallest", "height_m": 41, "speed_kmh": 105,
     "desc": "14-story near-free-fall slide that was the world's tallest for years",
     "park": "Beach Park", "color": "#14b8a6"},
    {"name": "Summit Plummet", "location": "Orlando, FL, USA", "lat": 28.3530, "lon": -81.5769,
     "record": "Fastest free-fall in US", "height_m": 36.6, "speed_kmh": 97,
     "desc": "120-foot near-vertical drop from a ski jump at Disney's Blizzard Beach",
     "park": "Blizzard Beach", "color": "#06b6d4"},
    {"name": "Jumeirah Sceirah", "location": "Dubai, UAE", "lat": 25.1411, "lon": 55.1875,
     "record": "Tallest slide in Middle East", "height_m": 33, "speed_kmh": 80,
     "desc": "Capsule-launch body slide with 80 km/h speeds in 3 seconds",
     "park": "Wild Wadi", "color": "#0ea5e9"},
    {"name": "AquaDuck", "location": "At Sea (Disney Cruise)", "lat": 28.3655, "lon": -81.5298,
     "record": "First shipboard water coaster", "height_m": 20, "speed_kmh": 35,
     "desc": "Transparent tube water coaster that extends over the edge of a cruise ship",
     "park": "Disney Dream/Fantasy", "color": "#f59e0b"},
    {"name": "Ko'okiri Body Plunge", "location": "Orlando, FL, USA", "lat": 28.4621, "lon": -81.4718,
     "record": "Tallest trap-door drop", "height_m": 38, "speed_kmh": 99,
     "desc": "70-degree free-fall drop from 125 feet through a trap door in a volcano",
     "park": "Volcano Bay", "color": "#dc2626"},
    {"name": "King Cobra", "location": "Tenerife, Spain", "lat": 28.0713, "lon": -16.7260,
     "record": "Longest intertwined slides", "height_m": 30, "speed_kmh": 60,
     "desc": "Two intertwined half-pipe slides racing side by side like dueling cobras",
     "park": "Siam Park", "color": "#a855f7"},
    {"name": "Miss Adventure Falls", "location": "Orlando, FL, USA", "lat": 28.3655, "lon": -81.5298,
     "record": "Longest at Disney", "height_m": 12, "speed_kmh": 30,
     "desc": "Family raft ride - the longest water attraction in Disney history",
     "park": "Typhoon Lagoon", "color": "#22c55e"},
    {"name": "Mammoth", "location": "Santa Claus, IN, USA", "lat": 38.1208, "lon": -86.9142,
     "record": "World's longest water coaster", "height_m": 21, "speed_kmh": 50,
     "desc": "The world's longest water coaster at 1,763 feet long",
     "park": "Holiday World", "color": "#eab308"},
]

# ===================================================================
# 7. WAVE POOLS & SURF PARKS (curated)
# ===================================================================
WAVE_POOLS = [
    {"name": "Surf Ranch (Kelly Slater)", "location": "Lemoore, CA, USA", "lat": 36.2944, "lon": -119.7800,
     "type": "Artificial Wave", "desc": "Kelly Slater's perfect artificial wave machine for professional surfing",
     "tech": "Kelly Slater Wave Company hydrofoil", "wave_height_m": 2.1, "color": "#06b6d4"},
    {"name": "Urbnsurf Melbourne", "location": "Melbourne, Australia", "lat": -37.7173, "lon": 144.8560,
     "type": "Surf Park", "desc": "Australia's first surf park with Wavegarden Cove technology",
     "tech": "Wavegarden Cove", "wave_height_m": 1.9, "color": "#10b981"},
    {"name": "The Wave Bristol", "location": "Bristol, England", "lat": 51.4860, "lon": -2.6316,
     "type": "Surf Park", "desc": "Inland surf destination using Wavegarden Cove technology",
     "tech": "Wavegarden Cove", "wave_height_m": 1.8, "color": "#3b82f6"},
    {"name": "BSR Cable Park", "location": "Waco, TX, USA", "lat": 31.6082, "lon": -97.2200,
     "type": "Surf Park", "desc": "American Wave Machines' PerfectSwell generating customizable waves",
     "tech": "PerfectSwell by AWM", "wave_height_m": 2.0, "color": "#f59e0b"},
    {"name": "Wavegarden Praia da Gale", "location": "Lourinha, Portugal", "lat": 39.2500, "lon": -9.3167,
     "type": "Surf Park", "desc": "Wavegarden headquarters demo facility near Lisbon",
     "tech": "Wavegarden Cove", "wave_height_m": 1.8, "color": "#8b5cf6"},
    {"name": "Surf Abu Dhabi", "location": "Abu Dhabi, UAE", "lat": 24.4200, "lon": 54.5100,
     "type": "Surf Park", "desc": "Kelly Slater Wave Company's largest facility with 3.3-foot barrels",
     "tech": "KSWC hydrofoil", "wave_height_m": 2.4, "color": "#eab308"},
    {"name": "Typhoon Lagoon Surf Pool", "location": "Orlando, FL, USA", "lat": 28.3655, "lon": -81.5298,
     "type": "Wave Pool", "desc": "One of the world's largest wave pools producing 6-foot surf waves",
     "tech": "Hydraulic wave chamber", "wave_height_m": 1.8, "color": "#14b8a6"},
    {"name": "Siam Park Wave Palace", "location": "Tenerife, Spain", "lat": 28.0713, "lon": -16.7260,
     "type": "Wave Pool", "desc": "World's largest man-made wave producing 3.3m waves",
     "tech": "Pneumatic wave system", "wave_height_m": 3.3, "color": "#ec4899"},
    {"name": "Alaiya Bay", "location": "Weligama, Sri Lanka", "lat": 5.9727, "lon": 80.4293,
     "type": "Surf Park", "desc": "South Asia's first artificial surf park with tropical setting",
     "tech": "Wavegarden Cove", "wave_height_m": 1.8, "color": "#22c55e"},
    {"name": "Surf Snowdonia (Adventure Parc)", "location": "Dolgarrog, Wales", "lat": 53.1833, "lon": -3.8167,
     "type": "Surf Park", "desc": "World's first commercial Wavegarden in a stunning valley setting",
     "tech": "Wavegarden original", "wave_height_m": 1.7, "color": "#0ea5e9"},
    {"name": "UNIT Surf Pool", "location": "Multiple locations", "lat": 52.5200, "lon": 13.4050,
     "type": "Standing Wave", "desc": "German-engineered standing wave technology for urban surf pools",
     "tech": "UNIT Surf Pool standing wave", "wave_height_m": 1.6, "color": "#a855f7"},
    {"name": "NLand Surf Park", "location": "Austin, TX, USA", "lat": 30.1653, "lon": -97.6361,
     "type": "Surf Park", "desc": "One of America's first surf parks, powered by Wavegarden technology",
     "tech": "Wavegarden", "wave_height_m": 1.8, "color": "#f97316"},
]

# ===================================================================
# 8. THERMAL BATHING CULTURE (curated)
# ===================================================================
THERMAL_BATHS = [
    {"name": "Blue Lagoon", "location": "Grindavik, Iceland", "lat": 63.8804, "lon": -22.4495,
     "culture": "Icelandic Geothermal", "temp_c": 39, "mineral": "Silica, sulfur, algae",
     "desc": "World-famous milky-blue geothermal spa in a black lava field", "color": "#7dd3fc"},
    {"name": "Friedrichsbad", "location": "Baden-Baden, Germany", "lat": 48.7611, "lon": 8.2400,
     "culture": "German Kur", "temp_c": 36, "mineral": "Sodium chloride, trace minerals",
     "desc": "17-step Roman-Irish bathing ritual in a grand Renaissance building", "color": "#10b981"},
    {"name": "Caracalla Therme", "location": "Baden-Baden, Germany", "lat": 48.7625, "lon": 8.2388,
     "culture": "German Kur", "temp_c": 38, "mineral": "Thermal springs, sodium chloride",
     "desc": "Modern thermal spa with indoor/outdoor pools fed by natural hot springs", "color": "#22c55e"},
    {"name": "Szechenyi Thermal Bath", "location": "Budapest, Hungary", "lat": 47.5188, "lon": 19.0823,
     "culture": "Hungarian Thermal", "temp_c": 38, "mineral": "Calcium, magnesium, sulfate",
     "desc": "Europe's largest medicinal bath with 18 pools in a neo-baroque palace", "color": "#f59e0b"},
    {"name": "Gellert Thermal Bath", "location": "Budapest, Hungary", "lat": 47.4833, "lon": 19.0531,
     "culture": "Hungarian Thermal", "temp_c": 40, "mineral": "Calcium, magnesium, fluoride",
     "desc": "Art Nouveau masterpiece with ornate mosaics and outdoor wave pool", "color": "#a855f7"},
    {"name": "Wai-O-Tapu", "location": "Rotorua, New Zealand", "lat": -38.3594, "lon": 176.3690,
     "culture": "Maori Geothermal", "temp_c": 100, "mineral": "Sulfur, silica, arsenic",
     "desc": "Sacred geothermal wonderland with champagne pool, mud pools, and geysers",
     "color": "#f97316"},
    {"name": "Polynesian Spa", "location": "Rotorua, New Zealand", "lat": -38.0776, "lon": 176.2544,
     "culture": "Maori Geothermal", "temp_c": 42, "mineral": "Alkaline, acidic sulfur pools",
     "desc": "Lake-edge thermal spa with alkaline and acidic pools overlooking Lake Rotorua",
     "color": "#ef4444"},
    {"name": "Pamukkale Thermal Pools", "location": "Denizli, Turkey", "lat": 37.9203, "lon": 29.1201,
     "culture": "Anatolian Thermal", "temp_c": 36, "mineral": "Calcium carbonate travertine",
     "desc": "White travertine terraces with warm mineral water used since Greco-Roman era",
     "color": "#f0f9ff"},
    {"name": "Termas de Pucon", "location": "Pucon, Chile", "lat": -39.3559, "lon": -71.6472,
     "culture": "Chilean Termas", "temp_c": 40, "mineral": "Volcanic mineral springs",
     "desc": "Hot springs at the foot of Villarrica volcano in the Chilean Lake District",
     "color": "#14b8a6"},
    {"name": "Beitou Hot Springs", "location": "Taipei, Taiwan", "lat": 25.1370, "lon": 121.5097,
     "culture": "Taiwanese Onsen", "temp_c": 45, "mineral": "Sulfur, radium",
     "desc": "Historic hot spring district developed during Japanese colonial era",
     "color": "#ec4899"},
    {"name": "Terme di Saturnia", "location": "Grosseto, Italy", "lat": 42.6500, "lon": 11.5125,
     "culture": "Italian Terme", "temp_c": 37, "mineral": "Sulfurous, calcium, magnesium",
     "desc": "Etruscan-era sulfur springs cascading through travertine terraces",
     "color": "#06b6d4"},
    {"name": "Sky Lagoon", "location": "Reykjavik, Iceland", "lat": 64.1050, "lon": -21.9378,
     "culture": "Icelandic Geothermal", "temp_c": 39, "mineral": "Geothermal mineral water",
     "desc": "Modern infinity-edge geothermal lagoon with ocean views and 7-step ritual",
     "color": "#3b82f6"},
    {"name": "Onsen at Kurokawa", "location": "Minami-Oguni, Japan", "lat": 33.1147, "lon": 131.0964,
     "culture": "Japanese Onsen", "temp_c": 42, "mineral": "Sulfur, iron, sodium",
     "desc": "Charming mountain onsen village with 30+ ryokans and open-air rotenburo baths",
     "color": "#e11d48"},
    {"name": "Hammam Al Andalus", "location": "Granada, Spain", "lat": 37.1762, "lon": -3.5952,
     "culture": "Arab-Andalusian Hammam", "temp_c": 38, "mineral": "Essential oils, thermal",
     "desc": "Recreated Arab baths beneath the Alhambra in a 13th-century building",
     "color": "#d97706"},
]

# ===================================================================
# 9. RIVER SWIMMING SPOTS (curated)
# ===================================================================
RIVER_SWIMMING = [
    {"name": "Pont d'Arc (Ardeche)", "location": "Vallon-Pont-d'Arc, France", "lat": 44.3924, "lon": 4.3924,
     "river": "Ardeche", "desc": "Swimming under a natural stone arch in the Ardeche Gorge",
     "water_quality": "Excellent", "best_season": "Jun-Sep", "color": "#06b6d4"},
    {"name": "Hampstead Heath Ponds", "location": "London, England", "lat": 51.5637, "lon": -0.1647,
     "river": "Fleet (spring-fed)", "desc": "Three legendary swimming ponds in the heart of London since the 1860s",
     "water_quality": "Good", "best_season": "May-Sep", "color": "#3b82f6"},
    {"name": "Barton Springs Pool", "location": "Austin, TX, USA", "lat": 30.2641, "lon": -97.7713,
     "river": "Barton Creek (spring-fed)", "desc": "Natural spring-fed pool at a constant 68F in downtown Austin",
     "water_quality": "Excellent", "best_season": "Year-round", "color": "#10b981"},
    {"name": "Verzasca River", "location": "Ticino, Switzerland", "lat": 46.2647, "lon": 8.8639,
     "river": "Verzasca", "desc": "Impossibly clear emerald water flowing over smooth granite boulders",
     "water_quality": "Excellent", "best_season": "Jul-Sep", "color": "#22c55e"},
    {"name": "Liard River Hot Springs", "location": "British Columbia, Canada", "lat": 59.4253, "lon": -126.0964,
     "river": "Liard (hot spring)", "desc": "Canada's largest natural hot spring along the Alaska Highway",
     "water_quality": "Excellent", "best_season": "Year-round", "color": "#14b8a6"},
    {"name": "Rio Celeste", "location": "Tenorio Volcano, Costa Rica", "lat": 10.7131, "lon": -85.0297,
     "river": "Celeste", "desc": "Surreal sky-blue river colored by volcanic minerals in the rainforest",
     "water_quality": "Good", "best_season": "Dec-Apr", "color": "#0ea5e9"},
    {"name": "Krka Waterfalls", "location": "Sibenik, Croatia", "lat": 43.8000, "lon": 15.9611,
     "river": "Krka", "desc": "Swimming at the base of travertine waterfalls in Krka National Park",
     "water_quality": "Excellent", "best_season": "Jun-Sep", "color": "#8b5cf6"},
    {"name": "Mossman Gorge", "location": "Queensland, Australia", "lat": -16.4711, "lon": 145.3578,
     "river": "Mossman", "desc": "Crystal-clear swimming holes in Daintree Rainforest boulder pools",
     "water_quality": "Excellent", "best_season": "May-Oct", "color": "#f59e0b"},
    {"name": "Wadi Shab", "location": "Tiwi, Oman", "lat": 22.8411, "lon": 59.2242,
     "river": "Wadi Shab", "desc": "Turquoise wadi pools and cave swimming in a dramatic Omani canyon",
     "water_quality": "Good", "best_season": "Oct-Apr", "color": "#eab308"},
    {"name": "Semuc Champey", "location": "Lanquin, Guatemala", "lat": 15.5286, "lon": -89.9536,
     "river": "Cahabon", "desc": "Tiered turquoise limestone pools bridging over the rushing Cahabon River",
     "water_quality": "Good", "best_season": "Feb-May", "color": "#a855f7"},
    {"name": "River Cam (The Backs)", "location": "Cambridge, England", "lat": 52.2053, "lon": 0.1118,
     "river": "Cam", "desc": "Punting and wild swimming along The Backs behind Cambridge colleges",
     "water_quality": "Moderate", "best_season": "Jun-Aug", "color": "#ec4899"},
    {"name": "Jacob's Well", "location": "Wimberley, TX, USA", "lat": 30.0343, "lon": -98.1256,
     "river": "Cypress Creek (spring)", "desc": "Artesian spring emerging from an underwater cave system - crystal clear blue",
     "water_quality": "Excellent", "best_season": "May-Sep", "color": "#0891b2"},
]

# ===================================================================
# 10. LAKE SWIMMING (curated)
# ===================================================================
LAKE_SWIMMING = [
    {"name": "Lake Bled", "location": "Bled, Slovenia", "lat": 46.3625, "lon": 14.0937,
     "desc": "Alpine lake with a fairy-tale island church and medieval cliffside castle",
     "water_temp_c": 22, "best_season": "Jun-Sep", "altitude_m": 475, "color": "#06b6d4"},
    {"name": "Lake Como (Lido di Bellagio)", "location": "Bellagio, Italy", "lat": 45.9869, "lon": 9.2618,
     "desc": "Swimming in Italy's most glamorous lake surrounded by villas and mountains",
     "water_temp_c": 24, "best_season": "Jun-Sep", "altitude_m": 198, "color": "#3b82f6"},
    {"name": "Lake Tahoe", "location": "CA/NV, USA", "lat": 39.0968, "lon": -120.0324,
     "desc": "Crystal-clear alpine lake straddling California and Nevada at 6,200 ft elevation",
     "water_temp_c": 19, "best_season": "Jul-Sep", "altitude_m": 1897, "color": "#8b5cf6"},
    {"name": "Lake Malawi (Cape Maclear)", "location": "Cape Maclear, Malawi", "lat": -14.0190, "lon": 35.1370,
     "desc": "Warm freshwater lake with tropical fish - the Lake of Stars",
     "water_temp_c": 27, "best_season": "May-Oct", "altitude_m": 474, "color": "#f59e0b"},
    {"name": "Lake Lucerne", "location": "Lucerne, Switzerland", "lat": 47.0186, "lon": 8.3330,
     "desc": "Swimming in an Alpine lake surrounded by dramatic Swiss peaks and historic towns",
     "water_temp_c": 20, "best_season": "Jun-Sep", "altitude_m": 434, "color": "#10b981"},
    {"name": "Crater Lake", "location": "Oregon, USA", "lat": 42.9446, "lon": -122.1090,
     "desc": "Deepest lake in the USA (594m) with stunningly pure cobalt-blue water",
     "water_temp_c": 13, "best_season": "Jul-Aug", "altitude_m": 1883, "color": "#1e40af"},
    {"name": "Lake Atitlan", "location": "Solola, Guatemala", "lat": 14.6873, "lon": -91.2012,
     "desc": "Volcanic lake ringed by three volcanoes and Maya villages",
     "water_temp_c": 21, "best_season": "Nov-Apr", "altitude_m": 1562, "color": "#22c55e"},
    {"name": "Lake Wanaka", "location": "Wanaka, New Zealand", "lat": -44.6933, "lon": 169.1322,
     "desc": "Pristine glacial lake with the famous lone Wanaka Tree and mountain views",
     "water_temp_c": 16, "best_season": "Dec-Mar", "altitude_m": 274, "color": "#14b8a6"},
    {"name": "Plitvice Lakes", "location": "Plitvice, Croatia", "lat": 44.8654, "lon": 15.5820,
     "desc": "16 terraced turquoise lakes connected by waterfalls in a UNESCO World Heritage forest",
     "water_temp_c": 15, "best_season": "Jun-Sep (no swimming - viewing)", "altitude_m": 500, "color": "#a855f7"},
    {"name": "Lake Ohrid", "location": "North Macedonia / Albania", "lat": 41.1132, "lon": 20.8019,
     "desc": "One of Europe's oldest and deepest lakes - a UNESCO site over 3 million years old",
     "water_temp_c": 23, "best_season": "Jun-Sep", "altitude_m": 693, "color": "#ec4899"},
    {"name": "Lake Titicaca", "location": "Peru / Bolivia", "lat": -15.9254, "lon": -69.3354,
     "desc": "World's highest navigable lake at 3,812m with floating Uros islands",
     "water_temp_c": 11, "best_season": "May-Oct", "altitude_m": 3812, "color": "#f97316"},
    {"name": "Dead Sea", "location": "Israel / Jordan", "lat": 31.5, "lon": 35.5,
     "desc": "Earth's lowest point - float effortlessly in water 10x saltier than the ocean",
     "water_temp_c": 31, "best_season": "Mar-May, Sep-Nov", "altitude_m": -430, "color": "#0d9488"},
    {"name": "Lake Garda (Sirmione)", "location": "Sirmione, Italy", "lat": 45.4953, "lon": 10.6068,
     "desc": "Italy's largest lake with thermal springs, Roman ruins, and Mediterranean climate",
     "water_temp_c": 23, "best_season": "Jun-Sep", "altitude_m": 65, "color": "#0ea5e9"},
    {"name": "Lake Baikal", "location": "Siberia, Russia", "lat": 53.5587, "lon": 108.1650,
     "desc": "World's deepest, oldest, and largest freshwater lake by volume - Siberia's Sacred Sea",
     "water_temp_c": 10, "best_season": "Jul-Aug", "altitude_m": 455, "color": "#6366f1"},
]


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

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
    st_html(m._repr_html_(), height=height)


def _csv_download(df: pd.DataFrame, filename: str, label: str, key: str):
    """Render a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename,
                       mime="text/csv", key=key)


# ===================================================================
# MODE RENDERERS
# ===================================================================

def _render_water_parks():
    """Mode 1: World's Best Water Parks."""
    st.markdown("#### World's Best Water Parks")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">The planet\'s top-rated water parks &mdash; '
        f'from Disney\'s Typhoon Lagoon to Siam Park in Tenerife. Click markers for details.</p>',
        unsafe_allow_html=True,
    )

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Water Parks", len(WATER_PARKS))
    countries = set(p["location"].split(", ")[-1] for p in WATER_PARKS)
    c2.metric("Countries", len(countries))
    oldest = min(p["year_opened"] for p in WATER_PARKS)
    c3.metric("Oldest Opened", str(oldest))

    # Map
    m = _make_dark_map([20, 0], zoom=2)
    cluster = MarkerCluster().add_to(m)
    for p in WATER_PARKS:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(p["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(p["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(p["desc"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Highlights:</b> {html_module.escape(p["highlights"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Opened:</b> {p["year_opened"]}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=8,
            color=p["color"], fill=True, fill_color=p["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(cluster)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": p["name"], "Location": p["location"],
        "Highlights": p["highlights"], "Year Opened": p["year_opened"],
        "Lat": p["lat"], "Lon": p["lon"],
    } for p in WATER_PARKS])

    with st.expander(f"Full Data Table ({len(df)} parks)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "water_parks.csv",
                  f"Download {len(df)} Water Parks (CSV)", "wp_dl")


def _render_natural_pools():
    """Mode 2: Natural Swimming Pools."""
    st.markdown("#### Natural Swimming Pools")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Cenotes, rock pools, grottos and natural swimming holes '
        f'around the world. Click markers for details.</p>',
        unsafe_allow_html=True,
    )

    # Filter by type
    pool_types = sorted(set(p["type"] for p in NATURAL_POOLS))
    sel_types = st.multiselect("Filter by Type", pool_types, default=pool_types, key="np_types")
    filtered = [p for p in NATURAL_POOLS if p["type"] in sel_types]

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Pools Shown", len(filtered))
    c2.metric("Types", len(set(p["type"] for p in filtered)))
    max_depth = max((p["depth_m"] for p in filtered), default=0)
    c3.metric("Deepest", f"{max_depth} m")

    # Map
    m = _make_dark_map([20, 0], zoom=2)
    for p in filtered:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(p["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(p["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Type:</b> {html_module.escape(p["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(p["desc"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Depth:</b> {p["depth_m"]} m</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=7,
            color=p["color"], fill=True, fill_color=p["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": p["name"], "Location": p["location"], "Type": p["type"],
        "Description": p["desc"], "Depth (m)": p["depth_m"],
        "Lat": p["lat"], "Lon": p["lon"],
    } for p in filtered])

    with st.expander(f"Full Data Table ({len(df)} pools)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "natural_pools.csv",
                  f"Download {len(df)} Natural Pools (CSV)", "np_dl")


def _render_infinity_pools():
    """Mode 3: Famous Infinity Pools."""
    st.markdown("#### Famous Infinity Pools")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">The world\'s most iconic hotel infinity pools &mdash; '
        f'from Marina Bay Sands to Santorini\'s caldera edge. Click markers for details.</p>',
        unsafe_allow_html=True,
    )

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Infinity Pools", len(INFINITY_POOLS))
    max_elev = max(p["elevation_m"] for p in INFINITY_POOLS)
    c2.metric("Highest Elevation", f"{max_elev} m")
    countries = set(p["location"].split(", ")[-1] for p in INFINITY_POOLS)
    c3.metric("Destinations", len(countries))

    # Map
    m = _make_dark_map([15, 50], zoom=2)
    for p in INFINITY_POOLS:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(p["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(p["hotel"])}</span><br/>'
            f'<span style="font-size:0.8rem;color:#888;">{html_module.escape(p["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(p["desc"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Elevation:</b> {p["elevation_m"]} m</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=8,
            color=p["color"], fill=True, fill_color=p["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": p["name"], "Hotel": p["hotel"], "Location": p["location"],
        "Description": p["desc"], "Elevation (m)": p["elevation_m"],
        "Lat": p["lat"], "Lon": p["lon"],
    } for p in INFINITY_POOLS])

    with st.expander(f"Full Data Table ({len(df)} pools)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "infinity_pools.csv",
                  f"Download {len(df)} Infinity Pools (CSV)", "ip_dl")


def _render_historic_baths():
    """Mode 4: Historic Public Baths."""
    st.markdown("#### Historic Public Baths")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Roman thermae, Turkish hammams, Japanese sento and onsen &mdash; '
        f'thousands of years of bathing culture mapped worldwide.</p>',
        unsafe_allow_html=True,
    )

    # Filter by type
    bath_types = sorted(set(b["type"] for b in HISTORIC_BATHS))
    sel_types = st.multiselect("Filter by Bath Type", bath_types, default=bath_types, key="hb_types")
    filtered = [b for b in HISTORIC_BATHS if b["type"] in sel_types]

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Baths Shown", len(filtered))
    c2.metric("Bath Types", len(set(b["type"] for b in filtered)))
    c3.metric("Countries", len(set(b["location"].split(", ")[-1] for b in filtered)))

    # Map
    m = _make_dark_map([35, 30], zoom=3)
    for b in filtered:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(b["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(b["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Type:</b> {html_module.escape(b["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(b["desc"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Era:</b> {html_module.escape(b["era"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=7,
            color=b["color"], fill=True, fill_color=b["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": b["name"], "Location": b["location"], "Type": b["type"],
        "Era": b["era"], "Description": b["desc"],
        "Lat": b["lat"], "Lon": b["lon"],
    } for b in filtered])

    with st.expander(f"Full Data Table ({len(df)} baths)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "historic_baths.csv",
                  f"Download {len(df)} Historic Baths (CSV)", "hb_dl")


def _render_olympic_venues():
    """Mode 5: Olympic Swimming Venues."""
    st.markdown("#### Olympic Swimming Venues")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Historic and current Olympic aquatics venues &mdash; '
        f'from Helsinki 1952 to Brisbane 2032. Click markers for architectural details.</p>',
        unsafe_allow_html=True,
    )

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Olympic Venues", len(OLYMPIC_VENUES))
    years = [v["year"] for v in OLYMPIC_VENUES]
    c2.metric("Earliest", str(min(years)))
    c3.metric("Latest", str(max(years)))

    # Map
    m = _make_dark_map([30, 0], zoom=2)
    for v in OLYMPIC_VENUES:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(v["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(v["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Olympics:</b> {v["year"]}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Architect:</b> {html_module.escape(v["architect"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(v["desc"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Legacy:</b> {html_module.escape(v["legacy"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[v["lat"], v["lon"]],
            radius=8,
            color=v["color"], fill=True, fill_color=v["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": v["name"], "Location": v["location"], "Year": v["year"],
        "Architect": v["architect"], "Description": v["desc"],
        "Legacy Use": v["legacy"], "Lat": v["lat"], "Lon": v["lon"],
    } for v in OLYMPIC_VENUES])

    with st.expander(f"Full Data Table ({len(df)} venues)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "olympic_swimming_venues.csv",
                  f"Download {len(df)} Olympic Venues (CSV)", "ov_dl")


def _render_water_slides():
    """Mode 6: Water Slides Records."""
    st.markdown("#### Water Slides Records")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">The tallest, longest, and fastest water slides ever built &mdash; '
        f'from the legendary Verruckt to Siam Park\'s Tower of Power.</p>',
        unsafe_allow_html=True,
    )

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Record Slides", len(WATER_SLIDES))
    max_h = max(s["height_m"] for s in WATER_SLIDES)
    c2.metric("Tallest", f"{max_h} m")
    max_s = max(s["speed_kmh"] for s in WATER_SLIDES)
    c3.metric("Fastest", f"{max_s} km/h")
    avg_h = sum(s["height_m"] for s in WATER_SLIDES) / len(WATER_SLIDES)
    c4.metric("Avg Height", f"{avg_h:.0f} m")

    # Map
    m = _make_dark_map([25, -20], zoom=2)
    for s in WATER_SLIDES:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(s["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(s["park"])}</span><br/>'
            f'<span style="font-size:0.8rem;color:#888;">{html_module.escape(s["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Record:</b> {html_module.escape(s["record"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Height:</b> {s["height_m"]} m | '
            f'<b>Speed:</b> {s["speed_kmh"]} km/h</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(s["desc"])}</span>'
            f'</div>'
        )
        # Scale radius by height
        radius = max(5, min(14, s["height_m"] / 4))
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=radius,
            color=s["color"], fill=True, fill_color=s["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "Park": s["park"], "Location": s["location"],
        "Record": s["record"], "Height (m)": s["height_m"],
        "Speed (km/h)": s["speed_kmh"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in WATER_SLIDES])

    with st.expander(f"Full Data Table ({len(df)} slides)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "water_slides_records.csv",
                  f"Download {len(df)} Water Slides (CSV)", "ws_dl")


def _render_wave_pools():
    """Mode 7: Wave Pools & Surf Parks."""
    st.markdown("#### Wave Pools & Surf Parks")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Artificial wave technology venues worldwide &mdash; '
        f'from Kelly Slater\'s Surf Ranch to Wavegarden parks. Click for tech specs.</p>',
        unsafe_allow_html=True,
    )

    # Filter by type
    wave_types = sorted(set(w["type"] for w in WAVE_POOLS))
    sel_types = st.multiselect("Filter by Venue Type", wave_types, default=wave_types, key="wv_types")
    filtered = [w for w in WAVE_POOLS if w["type"] in sel_types]

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Venues Shown", len(filtered))
    max_wave = max((w["wave_height_m"] for w in filtered), default=0)
    c2.metric("Tallest Wave", f"{max_wave} m")
    techs = set(w["tech"].split(" ")[0] for w in filtered)
    c3.metric("Technologies", len(techs))

    # Map
    m = _make_dark_map([25, -10], zoom=2)
    for w in filtered:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(w["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(w["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Type:</b> {html_module.escape(w["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Tech:</b> {html_module.escape(w["tech"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Max Wave:</b> {w["wave_height_m"]} m</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(w["desc"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=8,
            color=w["color"], fill=True, fill_color=w["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": w["name"], "Location": w["location"], "Type": w["type"],
        "Technology": w["tech"], "Max Wave (m)": w["wave_height_m"],
        "Lat": w["lat"], "Lon": w["lon"],
    } for w in filtered])

    with st.expander(f"Full Data Table ({len(df)} venues)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "wave_pools_surf_parks.csv",
                  f"Download {len(df)} Wave/Surf Venues (CSV)", "wv_dl")


def _render_thermal_baths():
    """Mode 8: Thermal Bathing Culture."""
    st.markdown("#### Thermal Bathing Culture")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From Baden-Baden to Budapest, Rotorua to Reykjavik &mdash; '
        f'the world\'s great thermal bathing traditions and their iconic venues.</p>',
        unsafe_allow_html=True,
    )

    # Filter by culture
    cultures = sorted(set(t["culture"] for t in THERMAL_BATHS))
    sel_cultures = st.multiselect("Filter by Culture", cultures, default=cultures, key="tb_cultures")
    filtered = [t for t in THERMAL_BATHS if t["culture"] in sel_cultures]

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Baths Shown", len(filtered))
    c2.metric("Cultures", len(set(t["culture"] for t in filtered)))
    max_temp = max((t["temp_c"] for t in filtered), default=0)
    c3.metric("Hottest", f"{max_temp} C")
    avg_temp = sum(t["temp_c"] for t in filtered) / max(len(filtered), 1)
    c4.metric("Avg Temp", f"{avg_temp:.0f} C")

    # Map
    m = _make_dark_map([35, 20], zoom=2)
    for t in filtered:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(t["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(t["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Culture:</b> {html_module.escape(t["culture"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Temp:</b> {t["temp_c"]} C</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Minerals:</b> {html_module.escape(t["mineral"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(t["desc"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=8,
            color=t["color"], fill=True, fill_color=t["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": t["name"], "Location": t["location"], "Culture": t["culture"],
        "Temp (C)": t["temp_c"], "Minerals": t["mineral"],
        "Description": t["desc"], "Lat": t["lat"], "Lon": t["lon"],
    } for t in filtered])

    with st.expander(f"Full Data Table ({len(df)} baths)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "thermal_baths.csv",
                  f"Download {len(df)} Thermal Baths (CSV)", "tb_dl")


def _render_river_swimming():
    """Mode 9: River Swimming Spots."""
    st.markdown("#### River Swimming Spots")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Safe and spectacular river swimming locations worldwide &mdash; '
        f'from Swiss alpine rivers to tropical waterfall pools.</p>',
        unsafe_allow_html=True,
    )

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Swimming Spots", len(RIVER_SWIMMING))
    excellent = len([r for r in RIVER_SWIMMING if r["water_quality"] == "Excellent"])
    c2.metric("Excellent Quality", excellent)
    year_round = len([r for r in RIVER_SWIMMING if "Year-round" in r["best_season"]])
    c3.metric("Year-Round", year_round)

    # Map
    m = _make_dark_map([25, -10], zoom=2)
    for r in RIVER_SWIMMING:
        quality_color = {"Excellent": "#10b981", "Good": "#f59e0b", "Moderate": "#f97316"}
        dot_color = quality_color.get(r["water_quality"], "#8b97b0")
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(r["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(r["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>River:</b> {html_module.escape(r["river"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(r["desc"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Water Quality:</b> {html_module.escape(r["water_quality"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Best Season:</b> {html_module.escape(r["best_season"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=7,
            color=r["color"], fill=True, fill_color=r["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Water quality legend
    st.markdown(
        '<div style="display:flex; gap:1rem; margin-top:0.5rem;">'
        '<span style="color:#10b981; font-size:0.8rem;">&#9679; Excellent</span>'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9679; Good</span>'
        '<span style="color:#f97316; font-size:0.8rem;">&#9679; Moderate</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Data table
    df = pd.DataFrame([{
        "Name": r["name"], "Location": r["location"], "River": r["river"],
        "Water Quality": r["water_quality"], "Best Season": r["best_season"],
        "Description": r["desc"], "Lat": r["lat"], "Lon": r["lon"],
    } for r in RIVER_SWIMMING])

    with st.expander(f"Full Data Table ({len(df)} spots)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "river_swimming.csv",
                  f"Download {len(df)} River Spots (CSV)", "rs_dl")


def _render_lake_swimming():
    """Mode 10: Lake Swimming."""
    st.markdown("#### Lake Swimming Destinations")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Famous lake swimming destinations worldwide &mdash; '
        f'from Alpine jewels like Lake Bled to the otherworldly Dead Sea.</p>',
        unsafe_allow_html=True,
    )

    # Sort options
    sort_by = st.selectbox("Sort by", ["Name", "Water Temp (warm first)", "Altitude (high first)"],
                           key="ls_sort")
    filtered = list(LAKE_SWIMMING)
    if sort_by == "Water Temp (warm first)":
        filtered.sort(key=lambda x: x["water_temp_c"], reverse=True)
    elif sort_by == "Altitude (high first)":
        filtered.sort(key=lambda x: x["altitude_m"], reverse=True)
    else:
        filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lakes", len(filtered))
    max_alt = max(l["altitude_m"] for l in filtered)
    c2.metric("Highest", f"{max_alt} m")
    min_alt = min(l["altitude_m"] for l in filtered)
    c3.metric("Lowest", f"{min_alt} m")
    avg_temp = sum(l["water_temp_c"] for l in filtered) / len(filtered)
    c4.metric("Avg Water Temp", f"{avg_temp:.0f} C")

    # Map
    m = _make_dark_map([25, 10], zoom=2)
    for l in filtered:
        popup = (
            f'<div style="max-width:240px;">'
            f'<strong>{html_module.escape(l["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{html_module.escape(l["location"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{html_module.escape(l["desc"])}</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Water Temp:</b> {l["water_temp_c"]} C</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Altitude:</b> {l["altitude_m"]} m</span><br/>'
            f'<span style="font-size:0.75rem;"><b>Best Season:</b> {html_module.escape(l["best_season"])}</span>'
            f'</div>'
        )
        # Color intensity by water temp
        folium.CircleMarker(
            location=[l["lat"], l["lon"]],
            radius=8,
            color=l["color"], fill=True, fill_color=l["color"],
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": l["name"], "Location": l["location"],
        "Water Temp (C)": l["water_temp_c"], "Altitude (m)": l["altitude_m"],
        "Best Season": l["best_season"], "Description": l["desc"],
        "Lat": l["lat"], "Lon": l["lon"],
    } for l in filtered])

    with st.expander(f"Full Data Table ({len(df)} lakes)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "lake_swimming.csv",
                  f"Download {len(df)} Lake Destinations (CSV)", "ls_dl")


# ===================================================================
# MAIN TAB RENDERER
# ===================================================================

def render_waterpark_maps_tab():
    """Main render function for the Water Parks & Swimming Explorer tab."""

    # -- Header --
    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>\U0001f3ca Water Parks & Swimming Explorer</h4>'
        '<p>Water parks, natural pools, infinity pools, historic baths, Olympic venues & more &mdash; 10 aquatic maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # -- Mode selector --
    mode = st.selectbox("Choose a Map Mode", MAP_MODES, key="waterpark_mode")

    st.markdown("---")

    # -- Dispatch --
    if mode == MAP_MODES[0]:
        _render_water_parks()
    elif mode == MAP_MODES[1]:
        _render_natural_pools()
    elif mode == MAP_MODES[2]:
        _render_infinity_pools()
    elif mode == MAP_MODES[3]:
        _render_historic_baths()
    elif mode == MAP_MODES[4]:
        _render_olympic_venues()
    elif mode == MAP_MODES[5]:
        _render_water_slides()
    elif mode == MAP_MODES[6]:
        _render_wave_pools()
    elif mode == MAP_MODES[7]:
        _render_thermal_baths()
    elif mode == MAP_MODES[8]:
        _render_river_swimming()
    elif mode == MAP_MODES[9]:
        _render_lake_swimming()
