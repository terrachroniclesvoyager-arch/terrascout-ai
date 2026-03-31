# -*- coding: utf-8 -*-
"""
Amusement & Theme Parks Explorer module for TerraScout AI.
Provides 10 curated map modes covering theme parks, roller coasters, water parks,
historic amusement parks, zoos, circus heritage, entertainment districts,
miniature worlds, adventure parks, and casino resort cities.
Uses the Overpass API for live OSM queries and curated datasets for world-famous venues.
"""

import io
import html
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

BG_DARK = "#0a0e1a"
BG_SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"
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
    "World's Greatest Theme Parks": ACCENT_PINK,
    "Roller Coasters": ACCENT_RED,
    "Water Parks": ACCENT_CYAN,
    "Historic Amusement Parks": ACCENT_AMBER,
    "Zoos & Aquariums": ACCENT_EMERALD,
    "Circus & Carnival Heritage": ACCENT_ORANGE,
    "Entertainment Districts": ACCENT_VIOLET,
    "Miniature Worlds": ACCENT_TEAL,
    "Adventure Parks": ACCENT_FUCHSIA,
    "Casino & Resort Cities": ACCENT_BLUE,
}

# ═══════════════════════════════════════════════════════════════════════════════
# CURATED DATASETS  (each mode has a handcrafted list of landmark venues)
# ═══════════════════════════════════════════════════════════════════════════════

GREATEST_THEME_PARKS = [
    {"name": "Walt Disney World - Magic Kingdom", "lat": 28.4177, "lon": -81.5812, "country": "USA", "opened": 1971, "visitors_m": 17.1, "note": "Most visited theme park on Earth"},
    {"name": "Disneyland Park", "lat": 33.8121, "lon": -117.9190, "country": "USA", "opened": 1955, "visitors_m": 16.9, "note": "Walt Disney's original park"},
    {"name": "Tokyo Disneyland", "lat": 35.6329, "lon": 139.8804, "country": "Japan", "opened": 1983, "visitors_m": 12.6, "note": "First Disney park outside the US"},
    {"name": "Tokyo DisneySea", "lat": 35.6267, "lon": 139.8850, "country": "Japan", "opened": 2001, "visitors_m": 10.1, "note": "Nautical-themed, world's most unique Disney park"},
    {"name": "Universal Studios Japan", "lat": 34.6654, "lon": 135.4323, "country": "Japan", "opened": 2001, "visitors_m": 14.3, "note": "Super Nintendo World debut location"},
    {"name": "Disneyland Paris", "lat": 48.8674, "lon": 2.7836, "country": "France", "opened": 1992, "visitors_m": 9.9, "note": "Europe's most visited theme park"},
    {"name": "Europa-Park", "lat": 48.2661, "lon": 7.7220, "country": "Germany", "opened": 1975, "visitors_m": 6.0, "note": "Best theme park in Europe (Golden Ticket)"},
    {"name": "Shanghai Disneyland", "lat": 31.1440, "lon": 121.6570, "country": "China", "opened": 2016, "visitors_m": 11.2, "note": "Newest Disney castle park, largest castle"},
    {"name": "Universal Studios Florida", "lat": 28.4742, "lon": -81.4687, "country": "USA", "opened": 1990, "visitors_m": 10.7, "note": "Home of the Wizarding World of Harry Potter"},
    {"name": "Islands of Adventure", "lat": 28.4712, "lon": -81.4701, "country": "USA", "opened": 1999, "visitors_m": 11.0, "note": "Velocicoaster, Hagrid's Motorbike Adventure"},
    {"name": "Efteling", "lat": 51.6499, "lon": 5.0497, "country": "Netherlands", "opened": 1952, "visitors_m": 5.4, "note": "Fairy tale forest, oldest theme park in the Benelux"},
    {"name": "Tivoli Gardens", "lat": 55.6736, "lon": 12.5681, "country": "Denmark", "opened": 1843, "visitors_m": 3.9, "note": "Inspired Walt Disney, 2nd oldest operating park"},
    {"name": "PortAventura World", "lat": 41.0867, "lon": 1.1563, "country": "Spain", "opened": 1995, "visitors_m": 5.2, "note": "Mediterranean coast, Ferrari Land included"},
    {"name": "Hong Kong Disneyland", "lat": 22.3130, "lon": 114.0413, "country": "China", "opened": 2005, "visitors_m": 5.8, "note": "World of Frozen opened 2023"},
    {"name": "EPCOT", "lat": 28.3747, "lon": -81.5494, "country": "USA", "opened": 1982, "visitors_m": 12.2, "note": "Future-world & World Showcase pavilions"},
    {"name": "Lotte World", "lat": 37.5112, "lon": 127.0981, "country": "South Korea", "opened": 1989, "visitors_m": 5.9, "note": "World's largest indoor theme park"},
    {"name": "Universal Studios Hollywood", "lat": 34.1381, "lon": -118.3534, "country": "USA", "opened": 1964, "visitors_m": 9.8, "note": "Working film studio + theme park"},
    {"name": "Gardaland", "lat": 45.4496, "lon": 10.7148, "country": "Italy", "opened": 1975, "visitors_m": 2.9, "note": "Italy's premier amusement park"},
    {"name": "Liseberg", "lat": 57.6953, "lon": 11.9924, "country": "Sweden", "opened": 1923, "visitors_m": 3.1, "note": "Scandinavia's largest amusement park"},
    {"name": "Phantasialand", "lat": 50.7994, "lon": 6.8792, "country": "Germany", "opened": 1967, "visitors_m": 2.1, "note": "Immersive theming, Taron & F.L.Y. coasters"},
]

ROLLER_COASTERS = [
    {"name": "Kingda Ka", "park": "Six Flags Great Adventure", "lat": 40.1374, "lon": -74.4408, "country": "USA", "height_m": 139, "speed_kmh": 206, "type": "Steel - Launched"},
    {"name": "Top Thrill 2", "park": "Cedar Point", "lat": 41.4808, "lon": -82.6831, "country": "USA", "height_m": 128, "speed_kmh": 193, "type": "Steel - Launched"},
    {"name": "Formula Rossa", "park": "Ferrari World Abu Dhabi", "lat": 24.4836, "lon": 54.6073, "country": "UAE", "height_m": 52, "speed_kmh": 240, "type": "Steel - Launched"},
    {"name": "Fury 325", "park": "Carowinds", "lat": 35.1013, "lon": -80.9412, "country": "USA", "height_m": 99, "speed_kmh": 153, "type": "Steel - Giga"},
    {"name": "Steel Vengeance", "park": "Cedar Point", "lat": 41.4789, "lon": -82.6844, "country": "USA", "height_m": 62, "speed_kmh": 117, "type": "Hybrid RMC"},
    {"name": "Velocicoaster", "park": "Islands of Adventure", "lat": 28.4720, "lon": -81.4688, "country": "USA", "height_m": 47, "speed_kmh": 112, "type": "Steel - Multi-launch"},
    {"name": "Taron", "park": "Phantasialand", "lat": 50.7995, "lon": 6.8794, "country": "Germany", "height_m": 30, "speed_kmh": 117, "type": "Steel - Multi-launch"},
    {"name": "Hakugei", "park": "Nagashima Spa Land", "lat": 35.0268, "lon": 136.7263, "country": "Japan", "height_m": 55, "speed_kmh": 107, "type": "Hybrid RMC"},
    {"name": "Zadra", "park": "Energylandia", "lat": 49.9728, "lon": 19.8419, "country": "Poland", "height_m": 63, "speed_kmh": 121, "type": "Hybrid RMC"},
    {"name": "Silver Star", "park": "Europa-Park", "lat": 48.2660, "lon": 7.7222, "country": "Germany", "height_m": 73, "speed_kmh": 127, "type": "Steel - B&M Hyper"},
    {"name": "Shambhala", "park": "PortAventura", "lat": 41.0870, "lon": 1.1565, "country": "Spain", "height_m": 76, "speed_kmh": 134, "type": "Steel - B&M Hyper"},
    {"name": "The Smiler", "park": "Alton Towers", "lat": 52.9904, "lon": -1.8902, "country": "UK", "height_m": 30, "speed_kmh": 85, "type": "Steel - 14 inversions (world record)"},
    {"name": "Lightning Rod", "park": "Dollywood", "lat": 35.7960, "lon": -83.5316, "country": "USA", "height_m": 51, "speed_kmh": 117, "type": "Hybrid RMC - Launched"},
    {"name": "Iron Gwazi", "park": "Busch Gardens Tampa", "lat": 28.0362, "lon": -82.4214, "country": "USA", "height_m": 63, "speed_kmh": 122, "type": "Hybrid RMC"},
    {"name": "Expedition GeForce", "park": "Holiday Park", "lat": 49.3179, "lon": 8.2977, "country": "Germany", "height_m": 53, "speed_kmh": 120, "type": "Steel - Intamin Mega"},
    {"name": "Kondaa", "park": "Walibi Belgium", "lat": 50.6987, "lon": 4.5944, "country": "Belgium", "height_m": 50, "speed_kmh": 113, "type": "Steel - Intamin Mega"},
    {"name": "Steel Dragon 2000", "park": "Nagashima Spa Land", "lat": 35.0260, "lon": 136.7268, "country": "Japan", "height_m": 97, "speed_kmh": 153, "type": "Steel - Longest (2,479m)"},
    {"name": "X2", "park": "Six Flags Magic Mountain", "lat": 34.4256, "lon": -118.5972, "country": "USA", "height_m": 53, "speed_kmh": 122, "type": "Steel - 4th Dimension"},
    {"name": "Helix", "park": "Liseberg", "lat": 57.6950, "lon": 11.9920, "country": "Sweden", "height_m": 41, "speed_kmh": 100, "type": "Steel - Multi-launch"},
    {"name": "Untamed", "park": "Walibi Holland", "lat": 52.2935, "lon": 5.7711, "country": "Netherlands", "height_m": 36, "speed_kmh": 90, "type": "Hybrid RMC"},
]

WATER_PARKS = [
    {"name": "Therme Erding", "lat": 48.2872, "lon": 11.9148, "country": "Germany", "type": "Indoor/Outdoor", "area_sqm": 185000, "note": "World's largest thermal spa & water park"},
    {"name": "Tropical Islands", "lat": 52.0406, "lon": 13.7504, "country": "Germany", "type": "Indoor", "area_sqm": 66000, "note": "Built inside a former airship hangar"},
    {"name": "Siam Park", "lat": 28.0717, "lon": -16.7260, "country": "Spain", "type": "Outdoor", "area_sqm": 185000, "note": "Best water park in the world (TripAdvisor)"},
    {"name": "Aquaventure Waterpark", "lat": 25.1320, "lon": 55.1172, "country": "UAE", "type": "Outdoor", "area_sqm": 170000, "note": "Atlantis The Palm, Dubai"},
    {"name": "Chimelong Water Park", "lat": 23.0016, "lon": 113.3286, "country": "China", "type": "Outdoor", "area_sqm": 400000, "note": "Most visited water park globally"},
    {"name": "Caribbean Bay", "lat": 37.2920, "lon": 127.0215, "country": "South Korea", "type": "Indoor/Outdoor", "area_sqm": 95000, "note": "Part of Everland resort complex"},
    {"name": "Yas Waterworld", "lat": 24.4881, "lon": 54.6012, "country": "UAE", "type": "Outdoor", "area_sqm": 150000, "note": "43 rides, Emirati pearl-diving theme"},
    {"name": "Waterbom Bali", "lat": -8.7272, "lon": 115.1667, "country": "Indonesia", "type": "Outdoor", "area_sqm": 38000, "note": "Asia's #1 water park, tropical setting"},
    {"name": "Typhoon Lagoon", "lat": 28.3656, "lon": -81.5286, "country": "USA", "type": "Outdoor", "area_sqm": 56000, "note": "Disney's surf-pool water park"},
    {"name": "Volcano Bay", "lat": 28.4622, "lon": -81.4706, "country": "USA", "type": "Outdoor", "area_sqm": 110000, "note": "Universal's TapuTapu wearable tech park"},
    {"name": "Schlitterbahn", "lat": 29.7120, "lon": -98.1292, "country": "USA", "type": "Outdoor", "area_sqm": 280000, "note": "Texas' iconic river-based water park"},
    {"name": "Atlantis Aquaventure Sanya", "lat": 18.2218, "lon": 109.7395, "country": "China", "type": "Outdoor", "area_sqm": 200000, "note": "Atlantis resort on Hainan Island"},
    {"name": "Aquatica Orlando", "lat": 28.4117, "lon": -81.4590, "country": "USA", "type": "Outdoor", "area_sqm": 59000, "note": "SeaWorld's water theme park"},
    {"name": "Wadi Adventure", "lat": 24.1275, "lon": 55.7855, "country": "UAE", "type": "Outdoor", "area_sqm": 55000, "note": "White-water rafting at base of Jebel Hafeet"},
    {"name": "Noah's Ark Waterpark", "lat": 43.6206, "lon": -89.7706, "country": "USA", "type": "Outdoor", "area_sqm": 283000, "note": "America's largest water park, Wisconsin Dells"},
    {"name": "Aquapalace Prague", "lat": 49.9932, "lon": 14.5020, "country": "Czech Republic", "type": "Indoor", "area_sqm": 31000, "note": "Central Europe's largest indoor water park"},
    {"name": "Splash Works", "lat": 43.8425, "lon": -79.5393, "country": "Canada", "type": "Outdoor", "area_sqm": 81000, "note": "Canada's Wonderland water park section"},
    {"name": "Wild Wadi", "lat": 25.1406, "lon": 55.1875, "country": "UAE", "type": "Outdoor", "area_sqm": 49000, "note": "Jumeirah Beach, Sindbad-themed slides"},
]

HISTORIC_PARKS = [
    {"name": "Bakken (Dyrehavsbakken)", "lat": 55.7741, "lon": 12.5789, "country": "Denmark", "founded": 1583, "note": "World's oldest operating amusement park"},
    {"name": "Tivoli Gardens", "lat": 55.6736, "lon": 12.5681, "country": "Denmark", "founded": 1843, "note": "2nd oldest, inspired Walt Disney"},
    {"name": "Blackpool Pleasure Beach", "lat": 53.7891, "lon": -3.0557, "country": "UK", "founded": 1896, "note": "UK's most visited amusement park"},
    {"name": "Luna Park (Coney Island)", "lat": 40.5742, "lon": -73.9790, "country": "USA", "founded": 1903, "note": "Iconic NY boardwalk amusement zone"},
    {"name": "Wiener Prater", "lat": 48.2166, "lon": 16.3964, "country": "Austria", "founded": 1766, "note": "Riesenrad giant Ferris wheel since 1897"},
    {"name": "Linnanmaki", "lat": 60.1876, "lon": 24.9406, "country": "Finland", "founded": 1950, "note": "Helsinki's charity-funded amusement park"},
    {"name": "Kennywood", "lat": 40.3867, "lon": -79.8625, "country": "USA", "founded": 1898, "note": "National Historic Landmark, Pittsburgh"},
    {"name": "Lake Compounce", "lat": 41.6348, "lon": -72.8340, "country": "USA", "founded": 1846, "note": "Oldest continuously operating US park"},
    {"name": "Knoebels", "lat": 40.8778, "lon": -76.5032, "country": "USA", "founded": 1926, "note": "Free admission, classic American park"},
    {"name": "Tibidabo", "lat": 41.4225, "lon": 2.1186, "country": "Spain", "founded": 1901, "note": "Mountaintop park overlooking Barcelona"},
    {"name": "Grona Lund", "lat": 59.3232, "lon": 18.0964, "country": "Sweden", "founded": 1883, "note": "Stockholm island amusement park"},
    {"name": "Wurstelprater", "lat": 48.2172, "lon": 16.3998, "country": "Austria", "founded": 1766, "note": "Prater's amusement zone, Viennese icon"},
    {"name": "Puy du Fou", "lat": 46.8897, "lon": -0.9322, "country": "France", "founded": 1989, "note": "World's best show park, no rides needed"},
    {"name": "Efteling", "lat": 51.6499, "lon": 5.0497, "country": "Netherlands", "founded": 1952, "note": "Fairy tale magic, Dutch cultural treasure"},
    {"name": "Dreamland Margate", "lat": 51.3858, "lon": 1.3813, "country": "UK", "founded": 1880, "note": "Grade II listed scenic railway"},
    {"name": "Cedar Point", "lat": 41.4808, "lon": -82.6831, "country": "USA", "founded": 1870, "note": "Roller Coaster Capital of the World"},
    {"name": "Idlewild", "lat": 40.2417, "lon": -79.2394, "country": "USA", "founded": 1878, "note": "Pennsylvania family heritage park"},
    {"name": "Jardin d'Acclimatation", "lat": 48.8773, "lon": 2.2628, "country": "France", "founded": 1860, "note": "Paris garden-park, Napoleon III era"},
]

ZOOS_AQUARIUMS = [
    {"name": "San Diego Zoo", "lat": 32.7353, "lon": -117.1490, "country": "USA", "type": "Zoo", "species": 3700, "note": "100+ acres, conservation leader"},
    {"name": "Singapore Zoo", "lat": 1.4043, "lon": 103.7930, "country": "Singapore", "type": "Zoo", "species": 2800, "note": "Open-concept, Night Safari pioneer"},
    {"name": "Tiergarten Schonbrunn", "lat": 48.1822, "lon": 16.3031, "country": "Austria", "type": "Zoo", "species": 700, "note": "World's oldest zoo (1752)"},
    {"name": "Chester Zoo", "lat": 53.2274, "lon": -2.8910, "country": "UK", "type": "Zoo", "species": 35000, "note": "125 acres, UK's most visited zoo"},
    {"name": "Georgia Aquarium", "lat": 33.7634, "lon": -84.3951, "country": "USA", "type": "Aquarium", "species": 120000, "note": "10M gallons, whale sharks & manta rays"},
    {"name": "Monterey Bay Aquarium", "lat": 36.6183, "lon": -121.9018, "country": "USA", "type": "Aquarium", "species": 35000, "note": "Kelp forest exhibit, sea otter rehab"},
    {"name": "Churaumi Aquarium", "lat": 26.6935, "lon": 127.8779, "country": "Japan", "type": "Aquarium", "species": 21000, "note": "Kuroshio Sea tank, whale shark exhibit"},
    {"name": "Berlin Zoological Garden", "lat": 52.5079, "lon": 13.3373, "country": "Germany", "type": "Zoo", "species": 20200, "note": "Most species of any zoo in the world"},
    {"name": "Kruger National Park", "lat": -23.9884, "lon": 31.5547, "country": "South Africa", "type": "Safari", "species": 1982, "note": "Big Five, nearly 2M hectares"},
    {"name": "Dubai Aquarium & Underwater Zoo", "lat": 25.1972, "lon": 55.2796, "country": "UAE", "type": "Aquarium", "species": 33000, "note": "10M litre tank inside Dubai Mall"},
    {"name": "Loro Parque", "lat": 28.4086, "lon": -16.5650, "country": "Spain", "type": "Zoo", "species": 4500, "note": "Tenerife, world's largest parrot collection"},
    {"name": "Bronx Zoo", "lat": 40.8506, "lon": -73.8769, "country": "USA", "type": "Zoo", "species": 6000, "note": "265 acres, Congo Gorilla Forest"},
    {"name": "S.E.A. Aquarium", "lat": 1.2583, "lon": 103.8198, "country": "Singapore", "type": "Aquarium", "species": 100000, "note": "Sentosa, 45M litre oceanarium"},
    {"name": "Taronga Zoo", "lat": -33.8433, "lon": 151.2411, "country": "Australia", "type": "Zoo", "species": 4000, "note": "Sydney Harbour views, ferry access"},
    {"name": "Henry Doorly Zoo", "lat": 41.2260, "lon": -95.9283, "country": "USA", "type": "Zoo", "species": 17000, "note": "Desert Dome, world's largest indoor desert"},
    {"name": "ZSL London Zoo", "lat": 51.5353, "lon": -0.1534, "country": "UK", "type": "Zoo", "species": 18000, "note": "World's oldest scientific zoo (1828)"},
    {"name": "Lisbon Oceanarium", "lat": 38.7636, "lon": -9.0937, "country": "Portugal", "type": "Aquarium", "species": 16000, "note": "Europe's largest indoor aquarium"},
    {"name": "Bioparc Valencia", "lat": 39.4789, "lon": -0.4094, "country": "Spain", "type": "Zoo", "species": 4000, "note": "Zoo-immersion concept, barrier-free habitats"},
]

CIRCUS_CARNIVAL = [
    {"name": "Circus Maximus", "lat": 41.8862, "lon": 12.4853, "country": "Italy", "era": "6th c. BC", "type": "Ancient Chariot Racing", "note": "Rome's original entertainment venue, 250K spectators"},
    {"name": "Sarasota - Ringling Circus Museum", "lat": 27.3260, "lon": -82.5508, "country": "USA", "era": "1927", "type": "Circus Heritage", "note": "Ringling Bros. winter quarters & museum"},
    {"name": "Baraboo - Circus World Museum", "lat": 43.4726, "lon": -89.7531, "country": "USA", "era": "1884", "type": "Circus Heritage", "note": "Original Ringling Bros. birthplace"},
    {"name": "Blackpool Tower Circus", "lat": 53.8159, "lon": -3.0553, "country": "UK", "era": "1894", "type": "Permanent Circus", "note": "130+ years of continuous circus performances"},
    {"name": "Carnival of Venice", "lat": 45.4408, "lon": 12.3155, "country": "Italy", "era": "1162", "type": "Carnival", "note": "World's most famous masked carnival"},
    {"name": "Rio Carnival - Sambodromo", "lat": -22.9114, "lon": -43.1964, "country": "Brazil", "era": "1723", "type": "Carnival", "note": "Largest carnival on Earth, samba schools"},
    {"name": "Mardi Gras - New Orleans", "lat": 29.9511, "lon": -90.0715, "country": "USA", "era": "1699", "type": "Carnival", "note": "Krewes, parades, French Quarter celebrations"},
    {"name": "Cirque du Soleil HQ", "lat": 45.5697, "lon": -73.5356, "country": "Canada", "era": "1984", "type": "Nouveau Cirque", "note": "Reinvented circus arts, Montreal HQ"},
    {"name": "Moscow State Circus (Bolshoi)", "lat": 55.7697, "lon": 37.6332, "country": "Russia", "era": "1880", "type": "State Circus", "note": "Grand circus on Tsvetnoy Boulevard"},
    {"name": "Zippos Circus Winter Quarters", "lat": 51.3900, "lon": -0.2900, "country": "UK", "era": "1986", "type": "Touring Circus", "note": "Britain's biggest touring big-top"},
    {"name": "Cologne Carnival", "lat": 50.9375, "lon": 6.9603, "country": "Germany", "era": "1341", "type": "Carnival", "note": "Rhineland Karneval tradition, Rose Monday"},
    {"name": "Notting Hill Carnival", "lat": 51.5143, "lon": -0.2040, "country": "UK", "era": "1966", "type": "Carnival", "note": "Europe's largest street carnival, Caribbean roots"},
    {"name": "Nice Carnival", "lat": 43.6961, "lon": 7.2667, "country": "France", "era": "1294", "type": "Carnival", "note": "Flower battles on the Riviera"},
    {"name": "Circo Price", "lat": 40.4092, "lon": -3.6988, "country": "Spain", "era": "1853", "type": "Historic Circus", "note": "Madrid's historic circus theater"},
    {"name": "Tenerife Carnival", "lat": 28.4682, "lon": -16.2546, "country": "Spain", "era": "1700s", "type": "Carnival", "note": "Second largest carnival after Rio"},
    {"name": "Basel Fasnacht", "lat": 47.5596, "lon": 7.5886, "country": "Switzerland", "era": "1376", "type": "Carnival", "note": "UNESCO Intangible Heritage, lantern parade"},
    {"name": "Binche Carnival", "lat": 50.4114, "lon": 4.1658, "country": "Belgium", "era": "14th c.", "type": "Carnival", "note": "UNESCO Heritage, famous Gilles characters"},
    {"name": "Trinidad Carnival", "lat": 10.6510, "lon": -61.5175, "country": "Trinidad & Tobago", "era": "1785", "type": "Carnival", "note": "Calypso, steelpan, mas bands origins"},
]

ENTERTAINMENT_DISTRICTS = [
    {"name": "Las Vegas Strip", "lat": 36.1147, "lon": -115.1728, "country": "USA", "type": "Casino/Entertainment", "note": "6.8 km of mega-casinos, shows, and nightlife"},
    {"name": "Orlando Theme Park Corridor", "lat": 28.4177, "lon": -81.5812, "country": "USA", "type": "Theme Parks", "note": "Disney, Universal, SeaWorld - world's theme park capital"},
    {"name": "Times Square", "lat": 40.7580, "lon": -73.9855, "country": "USA", "type": "Theater/Entertainment", "note": "Broadway theaters, dazzling billboards, NYC icon"},
    {"name": "Shibuya & Shinjuku", "lat": 35.6595, "lon": 139.7004, "country": "Japan", "type": "Entertainment/Nightlife", "note": "Neon-lit mega-entertainment zone, Robot Restaurant"},
    {"name": "Akihabara Electric Town", "lat": 35.6984, "lon": 139.7731, "country": "Japan", "type": "Gaming/Anime", "note": "Otaku culture, arcades, maid cafes, electronics"},
    {"name": "West End", "lat": 51.5114, "lon": -0.1281, "country": "UK", "type": "Theater", "note": "London's theater district, 40+ venues"},
    {"name": "Dubai Parks & Resorts", "lat": 24.9200, "lon": 55.0079, "country": "UAE", "type": "Theme Parks", "note": "Motiongate, Legoland, Bollywood Parks"},
    {"name": "Sentosa Island", "lat": 1.2494, "lon": 103.8303, "country": "Singapore", "type": "Resort Island", "note": "Universal Studios, S.E.A. Aquarium, beaches"},
    {"name": "Hollywood", "lat": 34.0928, "lon": -118.3287, "country": "USA", "type": "Film/Entertainment", "note": "Walk of Fame, studios, Griffith Observatory"},
    {"name": "Reeperbahn", "lat": 53.5496, "lon": 9.9651, "country": "Germany", "type": "Nightlife", "note": "Hamburg's mile of sin, where the Beatles played"},
    {"name": "Ibiza Town", "lat": 38.9067, "lon": 1.4206, "country": "Spain", "type": "Nightlife/Clubs", "note": "Global clubbing capital, superclub culture"},
    {"name": "Gangnam District", "lat": 37.4979, "lon": 127.0276, "country": "South Korea", "type": "Entertainment/K-Pop", "note": "K-pop agencies, entertainment HQs, style capital"},
    {"name": "Genting Highlands", "lat": 3.4236, "lon": 101.7933, "country": "Malaysia", "type": "Casino/Resort", "note": "Mountaintop resort, theme park, casino complex"},
    {"name": "Branson", "lat": 36.6437, "lon": -93.2185, "country": "USA", "type": "Shows/Music", "note": "Live music capital of the USA, Silver Dollar City"},
    {"name": "Niagara Falls Clifton Hill", "lat": 43.0896, "lon": -79.0782, "country": "Canada", "type": "Tourist Entertainment", "note": "The Street of Fun, haunted houses, Ferris wheel"},
    {"name": "The Palm Jumeirah", "lat": 25.1124, "lon": 55.1390, "country": "UAE", "type": "Resort Island", "note": "Atlantis resort, artificial island mega-project"},
    {"name": "Odaiba", "lat": 35.6295, "lon": 139.7756, "country": "Japan", "type": "Entertainment Island", "note": "TeamLab, Gundam, Giant Sky Wheel, futuristic district"},
    {"name": "Pigeon Forge & Gatlinburg", "lat": 35.7884, "lon": -83.5543, "country": "USA", "type": "Family Entertainment", "note": "Dollywood, aquarium, pancake houses, Great Smokies"},
]

MINIATURE_WORLDS = [
    {"name": "Legoland Billund", "lat": 55.7351, "lon": 9.1269, "country": "Denmark", "opened": 1968, "type": "LEGO Theme Park", "note": "Original Legoland, Miniland made of 20M+ bricks"},
    {"name": "Legoland Windsor", "lat": 51.4634, "lon": -0.6484, "country": "UK", "opened": 1996, "type": "LEGO Theme Park", "note": "55+ rides, Miniland with iconic London landmarks"},
    {"name": "Legoland Deutschland", "lat": 48.4271, "lon": 10.2997, "country": "Germany", "opened": 2002, "type": "LEGO Theme Park", "note": "German engineering meets LEGO creativity"},
    {"name": "Madurodam", "lat": 52.0994, "lon": 4.2998, "country": "Netherlands", "opened": 1952, "type": "Miniature City", "note": "1:25 scale Netherlands in miniature"},
    {"name": "Minimundus", "lat": 46.6238, "lon": 14.2634, "country": "Austria", "opened": 1958, "type": "Miniature World", "note": "150+ world monuments at 1:25 scale"},
    {"name": "Miniatur Wunderland", "lat": 53.5439, "lon": 9.9888, "country": "Germany", "opened": 2001, "type": "Model Railway", "note": "World's largest model railway, 16km of track"},
    {"name": "Window of the World", "lat": 22.5348, "lon": 113.9748, "country": "China", "opened": 1994, "type": "Miniature World", "note": "130 world landmarks in Shenzhen"},
    {"name": "Tobu World Square", "lat": 36.8203, "lon": 139.6917, "country": "Japan", "opened": 1993, "type": "Miniature World", "note": "102 world structures at 1:25 scale"},
    {"name": "Italia in Miniatura", "lat": 44.0793, "lon": 12.5651, "country": "Italy", "opened": 1970, "type": "Miniature Country", "note": "270+ miniatures of Italian landmarks"},
    {"name": "Bekonscot Model Village", "lat": 51.6122, "lon": -0.6427, "country": "UK", "opened": 1929, "type": "Model Village", "note": "World's oldest model village, Enid Blyton's inspiration"},
    {"name": "Pueblo Chico", "lat": 28.3962, "lon": -16.5234, "country": "Spain", "opened": 2005, "type": "Miniature Park", "note": "Tenerife landmarks in miniature"},
    {"name": "Swissminiatur", "lat": 45.9580, "lon": 8.9610, "country": "Switzerland", "opened": 1959, "type": "Miniature Country", "note": "120+ Swiss landmarks at 1:25 scale"},
    {"name": "Cockington Green Gardens", "lat": -35.2384, "lon": 149.0602, "country": "Australia", "opened": 1979, "type": "Miniature Village", "note": "International buildings in miniature, Canberra"},
    {"name": "The Model Village (Bourton)", "lat": 51.8834, "lon": -1.7560, "country": "UK", "opened": 1937, "type": "Model Village", "note": "1:9 scale Cotswold village with model of itself"},
    {"name": "Legoland California", "lat": 33.1264, "lon": -117.3116, "country": "USA", "opened": 1999, "type": "LEGO Theme Park", "note": "30M LEGO bricks, Carlsbad coastline setting"},
    {"name": "Babbacombe Model Village", "lat": 50.4674, "lon": -3.5089, "country": "UK", "opened": 1963, "type": "Model Village", "note": "400+ models with humorous scenes"},
]

ADVENTURE_PARKS = [
    {"name": "Skyline Luge Sentosa", "lat": 1.2530, "lon": 103.8185, "country": "Singapore", "type": "Luge/Skyride", "note": "Gravity-fueled luge through tropical tracks"},
    {"name": "AJ Hackett Macau Tower", "lat": 22.1804, "lon": 113.5370, "country": "China", "type": "Bungee Jump", "note": "233m - World's highest commercial bungee jump"},
    {"name": "Zip World Velocity", "lat": 53.1218, "lon": -4.0718, "country": "UK", "type": "Zip Line", "note": "Longest zip line in Europe, 160km/h, Welsh quarry"},
    {"name": "Toro Verde Adventure Park", "lat": 18.1786, "lon": -66.5667, "country": "Puerto Rico", "type": "Zip Line", "note": "The Monster - one of world's longest zip lines (2.5km)"},
    {"name": "Skypark by AJ Hackett (Sochi)", "lat": 43.5265, "lon": 39.9396, "country": "Russia", "type": "Bungee/Swing", "note": "207m bungee, world's longest footbridge (439m)"},
    {"name": "TreeTop Adventure Park", "lat": -33.6974, "lon": 151.1508, "country": "Australia", "type": "Treetop Course", "note": "Sydney's forest canopy adventure, 100+ challenges"},
    {"name": "Go Ape Sherwood Forest", "lat": 53.2050, "lon": -1.0738, "country": "UK", "type": "Treetop Course", "note": "Robin Hood's forest, zip lines & rope bridges"},
    {"name": "Jungala Bali", "lat": -8.2823, "lon": 115.2429, "country": "Indonesia", "type": "Waterfall Pool", "note": "Infinity pools in the jungle canopy, Ubud"},
    {"name": "Canyoning Interlaken", "lat": 46.6863, "lon": 7.8632, "country": "Switzerland", "type": "Canyoning", "note": "Alpine gorge adventures in the Bernese Oberland"},
    {"name": "Nevis Swing", "lat": -45.0215, "lon": 168.9989, "country": "New Zealand", "type": "Giant Swing", "note": "World's biggest swing, 160m arc over river canyon"},
    {"name": "Flyover Iceland", "lat": 64.1466, "lon": -21.9350, "country": "Iceland", "type": "Flying Theater", "note": "Immersive flight ride over Iceland's landscapes"},
    {"name": "iFly Singapore", "lat": 1.2541, "lon": 103.8195, "country": "Singapore", "type": "Indoor Skydiving", "note": "Largest indoor skydiving wind tunnel in SE Asia"},
    {"name": "Rotorua Canopy Tours", "lat": -38.1601, "lon": 176.2739, "country": "New Zealand", "type": "Canopy Walk", "note": "Ancient native forest, 1,100-year-old trees"},
    {"name": "Titan RT Bridge", "lat": 51.7446, "lon": 10.8162, "country": "Germany", "type": "Suspension Bridge", "note": "458m hanging rope bridge, Harz Mountains"},
    {"name": "Via Ferrata Murren", "lat": 46.5585, "lon": 7.8928, "country": "Switzerland", "type": "Via Ferrata", "note": "Fixed-rope alpine climbing above Lauterbrunnen Valley"},
    {"name": "Bloukrans Bridge Bungee", "lat": -33.9697, "lon": 23.6473, "country": "South Africa", "type": "Bungee Jump", "note": "216m - Highest commercial bridge bungee in the world"},
    {"name": "Jetboat Queenstown", "lat": -44.9999, "lon": 168.7583, "country": "New Zealand", "type": "Jet Boat", "note": "Shotover Jet, canyon jet boating at 85km/h"},
    {"name": "Chamonix Aiguille du Midi", "lat": 45.8786, "lon": 6.8873, "country": "France", "type": "Skywalk", "note": "Step Into the Void glass box at 3,842m altitude"},
]

CASINO_RESORT_CITIES = [
    {"name": "Las Vegas Strip", "lat": 36.1147, "lon": -115.1728, "country": "USA", "revenue_b": 15.0, "casinos": 30, "note": "Global gambling capital, mega-resort strip"},
    {"name": "Macau - Cotai Strip", "lat": 22.1491, "lon": 113.5619, "country": "China", "revenue_b": 21.5, "casinos": 41, "note": "World's highest gambling revenue, Asia's Las Vegas"},
    {"name": "Monte Carlo Casino", "lat": 43.7389, "lon": 7.4279, "country": "Monaco", "revenue_b": 0.7, "casinos": 4, "note": "Legendary elegance, James Bond's casino"},
    {"name": "Atlantic City Boardwalk", "lat": 39.3643, "lon": -74.4229, "country": "USA", "revenue_b": 2.7, "casinos": 9, "note": "Boardwalk Empire, East Coast gaming hub"},
    {"name": "Marina Bay Sands", "lat": 1.2834, "lon": 103.8607, "country": "Singapore", "revenue_b": 3.4, "casinos": 2, "note": "Iconic infinity pool, integrated resort"},
    {"name": "Sun City Resort", "lat": -25.3335, "lon": 27.0926, "country": "South Africa", "revenue_b": 0.3, "casinos": 2, "note": "Lost City Palace, Valley of Waves"},
    {"name": "Baden-Baden Casino", "lat": 48.7620, "lon": 8.2405, "country": "Germany", "revenue_b": 0.2, "casinos": 1, "note": "Europe's most beautiful casino (Marlene Dietrich)"},
    {"name": "Casino de Monte-Carlo", "lat": 43.7393, "lon": 7.4281, "country": "Monaco", "revenue_b": 0.5, "casinos": 1, "note": "Beaux-Arts masterpiece, opened 1863"},
    {"name": "Crown Melbourne", "lat": -37.8236, "lon": 144.9581, "country": "Australia", "revenue_b": 2.1, "casinos": 1, "note": "Southbank mega-complex, fire show nightly"},
    {"name": "Resorts World Genting", "lat": 3.4236, "lon": 101.7933, "country": "Malaysia", "revenue_b": 2.5, "casinos": 1, "note": "Mountaintop resort, 10,000+ hotel rooms"},
    {"name": "Campione d'Italia Casino", "lat": 45.9686, "lon": 8.9713, "country": "Italy", "revenue_b": 0.1, "casinos": 1, "note": "Italian enclave in Switzerland, Lake Lugano"},
    {"name": "Casino Estoril", "lat": 38.7073, "lon": -9.3975, "country": "Portugal", "revenue_b": 0.2, "casinos": 1, "note": "Europe's largest casino, WWII spy intrigue"},
    {"name": "Foxwoods Resort Casino", "lat": 41.4715, "lon": -71.9716, "country": "USA", "revenue_b": 0.9, "casinos": 6, "note": "Largest casino in the Americas by gaming floor"},
    {"name": "Mohegan Sun", "lat": 41.4971, "lon": -72.0874, "country": "USA", "revenue_b": 0.8, "casinos": 3, "note": "Connecticut tribal casino, 364,000 sq ft gaming"},
    {"name": "City of Dreams Manila", "lat": 14.5248, "lon": 121.0192, "country": "Philippines", "revenue_b": 1.2, "casinos": 1, "note": "Entertainment City complex, Melco Resorts"},
    {"name": "Jeju Shinhwa World", "lat": 33.3060, "lon": 126.3648, "country": "South Korea", "revenue_b": 0.4, "casinos": 1, "note": "Volcanic island resort, Landing Casino"},
    {"name": "Punta del Este Casino", "lat": -34.9587, "lon": -54.9477, "country": "Uruguay", "revenue_b": 0.2, "casinos": 3, "note": "South America's Monaco, beachfront gaming"},
    {"name": "Casino Barriere Deauville", "lat": 49.3572, "lon": 0.0697, "country": "France", "revenue_b": 0.1, "casinos": 1, "note": "Belle Epoque Normandy resort casino"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# OVERPASS QUERY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _overpass_theme_parks(lat: float, lon: float, radius_km: float) -> list:
    """Query Overpass for theme parks, amusement parks, and water parks."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["tourism"="theme_park"](around:{radius_m},{lat},{lon});
  way["tourism"="theme_park"](around:{radius_m},{lat},{lon});
  relation["tourism"="theme_park"](around:{radius_m},{lat},{lon});
  node["leisure"="amusement_arcade"](around:{radius_m},{lat},{lon});
  way["leisure"="amusement_arcade"](around:{radius_m},{lat},{lon});
  node["leisure"="water_park"](around:{radius_m},{lat},{lon});
  way["leisure"="water_park"](around:{radius_m},{lat},{lon});
  node["attraction"="amusement_ride"](around:{radius_m},{lat},{lon});
  way["attraction"="amusement_ride"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []
    return _extract_osm_features(result)


@st.cache_data(ttl=3600)
def _overpass_zoos_aquariums(lat: float, lon: float, radius_km: float) -> list:
    """Query Overpass for zoos, aquariums, and wildlife parks."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["tourism"="zoo"](around:{radius_m},{lat},{lon});
  way["tourism"="zoo"](around:{radius_m},{lat},{lon});
  node["tourism"="aquarium"](around:{radius_m},{lat},{lon});
  way["tourism"="aquarium"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []
    return _extract_osm_features(result)


@st.cache_data(ttl=3600)
def _overpass_entertainment(lat: float, lon: float, radius_km: float) -> list:
    """Query Overpass for entertainment venues - casinos, cinemas, nightclubs."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["amenity"="casino"](around:{radius_m},{lat},{lon});
  way["amenity"="casino"](around:{radius_m},{lat},{lon});
  node["amenity"="cinema"](around:{radius_m},{lat},{lon});
  way["amenity"="cinema"](around:{radius_m},{lat},{lon});
  node["amenity"="nightclub"](around:{radius_m},{lat},{lon});
  way["amenity"="nightclub"](around:{radius_m},{lat},{lon});
  node["amenity"="theatre"](around:{radius_m},{lat},{lon});
  way["amenity"="theatre"](around:{radius_m},{lat},{lon});
  node["leisure"="miniature_golf"](around:{radius_m},{lat},{lon});
  way["leisure"="miniature_golf"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []
    return _extract_osm_features(result)


def _extract_osm_features(data: dict) -> list:
    """Extract features with coordinates from an Overpass response."""
    elements = data.get("elements", [])

    # Build node lookup for way/relation centroid resolution
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        lat, lon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1])
                      for n in nodes if n in node_lookup]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)

        if lat is None or lon is None:
            continue

        name = tags.get("name", tags.get("name:en", "Unnamed"))
        ftype = (tags.get("tourism") or tags.get("leisure")
                 or tags.get("amenity") or tags.get("attraction") or "venue")
        features.append({
            "name": name,
            "type": ftype,
            "lat": lat,
            "lon": lon,
            "tags": tags,
            "osm_id": el.get("id"),
            "website": tags.get("website", tags.get("contact:website", "")),
            "wikipedia": tags.get("wikipedia", ""),
            "opening_hours": tags.get("opening_hours", ""),
        })

    return features


# ═══════════════════════════════════════════════════════════════════════════════
# MAP BUILDING HELPERS
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


def _safe_popup(title: str, fields: dict, max_width: int = 260) -> folium.Popup:
    """Build an HTML popup with html-escaped user data."""
    safe_title = html.escape(str(title))
    lines = [f'<div style="max-width:{max_width}px;">',
             f'<strong style="font-size:0.9rem;">{safe_title}</strong>']
    for label, value in fields.items():
        if value:
            safe_val = html.escape(str(value))
            lines.append(f'<br/><span style="font-size:0.75rem; color:#999;">'
                         f'{html.escape(label)}:</span> '
                         f'<span style="font-size:0.78rem;">{safe_val}</span>')
    lines.append('</div>')
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


def _show_map(m: folium.Map):
    """Render a folium map via Streamlit components."""
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)


def _dark_bar_chart(labels: list, values: list, colors: list, xlabel: str,
                    ylabel: str, title: str, horizontal: bool = True):
    """Render a dark-themed matplotlib bar chart."""
    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.35)))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_SURFACE)

    if horizontal:
        bars = ax.barh(range(len(labels)), values, color=colors, alpha=0.85)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels([str(l)[:30] for l in labels], color=TEXT_SECONDARY, fontsize=8)
        ax.set_xlabel(xlabel, color=TEXT_SECONDARY, fontsize=10)
        ax.invert_yaxis()
    else:
        bars = ax.bar(range(len(labels)), values, color=colors, alpha=0.85)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels([str(l)[:18] for l in labels], color=TEXT_SECONDARY,
                           fontsize=7, rotation=45, ha="right")
        ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=10)

    ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=8)
    ax.grid(True, axis="x" if horizontal else "y", color=GRID_COLOR, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
    if title:
        ax.set_title(title, color=TEXT_PRIMARY, fontsize=11, pad=10)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _csv_download(df: pd.DataFrame, filename: str, label: str, key: str):
    """Offer a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename,
                       mime="text/csv", key=key)


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 1 - WORLD'S GREATEST THEME PARKS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_greatest_theme_parks():
    """World's greatest theme parks with visitor stats and global map."""
    st.markdown("#### World's Greatest Theme Parks")
    st.markdown(
        '<p style="color:#8b97b0;">A curated atlas of the planet\'s most iconic '
        'theme parks by annual attendance, legacy, and cultural impact.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(GREATEST_THEME_PARKS)

    # Stats row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Parks Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Visitors (M/yr)", f"{df['visitors_m'].sum():.1f}")
    c4.metric("Oldest Opened", int(df["opened"].min()))

    # Chart - top parks by visitors
    top = df.nlargest(12, "visitors_m")
    _dark_bar_chart(
        labels=top["name"].tolist(),
        values=top["visitors_m"].tolist(),
        colors=[ACCENT_PINK] * len(top),
        xlabel="Annual Visitors (millions)",
        ylabel="",
        title="Top Theme Parks by Annual Attendance",
    )

    # Map
    st.markdown("##### Global Theme Park Map")
    m = _build_map(30, 0, zoom=2)
    _add_markers(m, GREATEST_THEME_PARKS, "lat", "lon",
                 ["country", "opened", "visitors_m", "note"],
                 ACCENT_PINK, radius=8)
    _show_map(m)

    # Data table
    with st.expander(f"Full Data Table ({len(df)} parks)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "greatest_theme_parks.csv",
                  f"Download {len(df)} Theme Parks (CSV)", "dl_theme_parks")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 2 - ROLLER COASTERS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_roller_coasters():
    """World's tallest, fastest, and most thrilling roller coasters."""
    st.markdown("#### Legendary Roller Coasters")
    st.markdown(
        '<p style="color:#8b97b0;">The world\'s most extreme and acclaimed '
        'roller coasters - record holders for height, speed, and thrill factor.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(ROLLER_COASTERS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Coasters Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Max Speed (km/h)", int(df["speed_kmh"].max()))
    c4.metric("Max Height (m)", int(df["height_m"].max()))

    # Speed chart
    top_speed = df.nlargest(12, "speed_kmh")
    _dark_bar_chart(
        labels=[f"{r['name']} ({r['park'][:20]})" for _, r in top_speed.iterrows()],
        values=top_speed["speed_kmh"].tolist(),
        colors=[ACCENT_RED] * len(top_speed),
        xlabel="Top Speed (km/h)",
        ylabel="",
        title="Fastest Roller Coasters in the World",
    )

    # Height chart
    top_height = df.nlargest(12, "height_m")
    _dark_bar_chart(
        labels=[f"{r['name']} ({r['park'][:20]})" for _, r in top_height.iterrows()],
        values=top_height["height_m"].tolist(),
        colors=[ACCENT_ORANGE] * len(top_height),
        xlabel="Height (meters)",
        ylabel="",
        title="Tallest Roller Coasters in the World",
    )

    # Map
    st.markdown("##### Roller Coaster World Map")
    m = _build_map(30, 0, zoom=2)
    _add_markers(m, ROLLER_COASTERS, "lat", "lon",
                 ["park", "country", "height_m", "speed_kmh", "type", "note"],
                 ACCENT_RED, radius=7)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} coasters)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "roller_coasters.csv",
                  f"Download {len(df)} Roller Coasters (CSV)", "dl_coasters")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 3 - WATER PARKS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_water_parks():
    """Largest and most spectacular water parks worldwide."""
    st.markdown("#### World's Greatest Water Parks")
    st.markdown(
        '<p style="color:#8b97b0;">From massive indoor tropical paradises to '
        'sun-soaked mega slides - the planet\'s premier aquatic playgrounds.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(WATER_PARKS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Water Parks", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Indoor Parks", len(df[df["type"].str.contains("Indoor")]))
    c4.metric("Largest (sqm)", f"{df['area_sqm'].max():,.0f}")

    # Area chart
    top_area = df.nlargest(12, "area_sqm")
    _dark_bar_chart(
        labels=top_area["name"].tolist(),
        values=[a / 1000 for a in top_area["area_sqm"].tolist()],
        colors=[ACCENT_CYAN] * len(top_area),
        xlabel="Area (thousand sqm)",
        ylabel="",
        title="Largest Water Parks by Area",
    )

    # Map
    st.markdown("##### Water Park World Map")
    m = _build_map(25, 20, zoom=2)
    for wp in WATER_PARKS:
        color = "#06b6d4" if "Indoor" in wp["type"] else "#3b82f6"
        popup = _safe_popup(wp["name"], {
            "Country": wp["country"], "Type": wp["type"],
            "Area": f"{wp['area_sqm']:,} sqm", "Note": wp["note"]
        })
        folium.CircleMarker(
            location=[wp["lat"], wp["lon"]], radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} water parks)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "water_parks.csv",
                  f"Download {len(df)} Water Parks (CSV)", "dl_water_parks")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 4 - HISTORIC AMUSEMENT PARKS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_historic_parks():
    """Oldest amusement parks with rich heritage."""
    st.markdown("#### Historic Amusement Parks")
    st.markdown(
        '<p style="color:#8b97b0;">The oldest amusement parks still in operation '
        '- some dating back centuries. Living monuments to joy and wonder.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(HISTORIC_PARKS)
    df_sorted = df.sort_values("founded")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historic Parks", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest Founded", int(df["founded"].min()))
    c4.metric("Avg Age (years)", int(2026 - df["founded"].mean()))

    # Timeline chart
    _dark_bar_chart(
        labels=df_sorted["name"].tolist(),
        values=df_sorted["founded"].tolist(),
        colors=[ACCENT_AMBER] * len(df_sorted),
        xlabel="Year Founded",
        ylabel="",
        title="Historic Parks - Founding Timeline",
    )

    # Map
    st.markdown("##### Historic Parks World Map")
    m = _build_map(45, 0, zoom=3)
    for park in HISTORIC_PARKS:
        age = 2026 - park["founded"]
        popup = _safe_popup(park["name"], {
            "Country": park["country"],
            "Founded": str(park["founded"]),
            "Age": f"{age} years",
            "Note": park["note"],
        })
        # Older parks get bigger markers
        r = min(12, max(5, age // 30))
        folium.CircleMarker(
            location=[park["lat"], park["lon"]], radius=r,
            color=ACCENT_AMBER, fill=True, fill_color=ACCENT_AMBER,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} parks)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "historic_amusement_parks.csv",
                  f"Download {len(df)} Historic Parks (CSV)", "dl_historic")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 5 - ZOOS & AQUARIUMS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_zoos_aquariums():
    """World's greatest zoos, aquariums, and safari parks."""
    st.markdown("#### World's Greatest Zoos & Aquariums")
    st.markdown(
        '<p style="color:#8b97b0;">From the oldest scientific zoo to the largest '
        'aquarium tanks - a global atlas of wildlife conservation and wonder.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(ZOOS_AQUARIUMS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Venues Listed", len(df))
    c2.metric("Zoos", len(df[df["type"] == "Zoo"]))
    c3.metric("Aquariums", len(df[df["type"] == "Aquarium"]))
    c4.metric("Safari Parks", len(df[df["type"] == "Safari"]))

    # Species chart
    top_species = df.nlargest(12, "species")
    colors_chart = []
    for _, row in top_species.iterrows():
        if row["type"] == "Aquarium":
            colors_chart.append(ACCENT_BLUE)
        elif row["type"] == "Safari":
            colors_chart.append(ACCENT_AMBER)
        else:
            colors_chart.append(ACCENT_EMERALD)
    _dark_bar_chart(
        labels=top_species["name"].tolist(),
        values=top_species["species"].tolist(),
        colors=colors_chart,
        xlabel="Number of Species / Animals",
        ylabel="",
        title="Zoos & Aquariums by Species Count",
    )

    # Map
    st.markdown("##### Global Zoos & Aquariums Map")
    m = _build_map(25, 20, zoom=2)
    type_colors = {"Zoo": ACCENT_EMERALD, "Aquarium": ACCENT_BLUE, "Safari": ACCENT_AMBER}
    for venue in ZOOS_AQUARIUMS:
        color = type_colors.get(venue["type"], ACCENT_TEAL)
        popup = _safe_popup(venue["name"], {
            "Type": venue["type"], "Country": venue["country"],
            "Species": str(venue["species"]), "Note": venue["note"],
        })
        folium.CircleMarker(
            location=[venue["lat"], venue["lon"]], radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)

    # Legend
    st.markdown(
        '<div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'<span style="color:{ACCENT_EMERALD}; font-size:0.8rem;">&#9679; Zoo</span>'
        f'<span style="color:{ACCENT_BLUE}; font-size:0.8rem;">&#9679; Aquarium</span>'
        f'<span style="color:{ACCENT_AMBER}; font-size:0.8rem;">&#9679; Safari</span>'
        '</div>', unsafe_allow_html=True,
    )
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} venues)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "zoos_aquariums.csv",
                  f"Download {len(df)} Zoos & Aquariums (CSV)", "dl_zoos")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 6 - CIRCUS & CARNIVAL HERITAGE
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_circus_carnival():
    """Famous circus origins and carnival traditions around the world."""
    st.markdown("#### Circus & Carnival Heritage")
    st.markdown(
        '<p style="color:#8b97b0;">From ancient Roman spectacles to Rio\'s Sambodromo '
        'and Venetian masks - the world\'s greatest celebration traditions.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(CIRCUS_CARNIVAL)

    # Type breakdown
    type_counts = df["type"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Venues / Events", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Carnivals", int(type_counts.get("Carnival", 0)))
    c4.metric("Circus Heritage", len(df) - int(type_counts.get("Carnival", 0)))

    # Type distribution chart
    _dark_bar_chart(
        labels=type_counts.index.tolist(),
        values=type_counts.values.tolist(),
        colors=[ACCENT_ORANGE] * len(type_counts),
        xlabel="Count",
        ylabel="",
        title="Circus & Carnival by Category",
    )

    # Map
    st.markdown("##### Circus & Carnival World Map")
    m = _build_map(30, 0, zoom=2)
    for venue in CIRCUS_CARNIVAL:
        is_carnival = "Carnival" in venue.get("type", "")
        color = ACCENT_FUCHSIA if is_carnival else ACCENT_ORANGE
        popup = _safe_popup(venue["name"], {
            "Type": venue["type"], "Country": venue["country"],
            "Era": venue["era"], "Note": venue["note"],
        })
        folium.CircleMarker(
            location=[venue["lat"], venue["lon"]], radius=7,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'<span style="color:{ACCENT_FUCHSIA}; font-size:0.8rem;">&#9679; Carnival</span>'
        f'<span style="color:{ACCENT_ORANGE}; font-size:0.8rem;">&#9679; Circus</span>'
        '</div>', unsafe_allow_html=True,
    )
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} venues)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "circus_carnival_heritage.csv",
                  f"Download {len(df)} Circus & Carnival Venues (CSV)", "dl_circus")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 7 - ENTERTAINMENT DISTRICTS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_entertainment_districts():
    """Las Vegas, Orlando, Dubai, Tokyo - world's entertainment mega-zones."""
    st.markdown("#### World's Entertainment Districts")
    st.markdown(
        '<p style="color:#8b97b0;">The neon-lit, high-energy entertainment corridors '
        'where the world comes to play - from the Las Vegas Strip to Shibuya Crossing.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(ENTERTAINMENT_DISTRICTS)

    type_counts = df["type"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Districts Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Unique Types", df["type"].nunique())
    c4.metric("USA Districts", len(df[df["country"] == "USA"]))

    # Type distribution
    _dark_bar_chart(
        labels=type_counts.index.tolist(),
        values=type_counts.values.tolist(),
        colors=[ACCENT_VIOLET] * len(type_counts),
        xlabel="Count",
        ylabel="",
        title="Entertainment Districts by Category",
    )

    # Map
    st.markdown("##### Entertainment Districts World Map")
    m = _build_map(25, 0, zoom=2)
    _add_markers(m, ENTERTAINMENT_DISTRICTS, "lat", "lon",
                 ["country", "type", "note"], ACCENT_VIOLET, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} districts)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "entertainment_districts.csv",
                  f"Download {len(df)} Entertainment Districts (CSV)", "dl_entertainment")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 8 - MINIATURE WORLDS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_miniature_worlds():
    """Legoland, Madurodam, miniature village parks."""
    st.markdown("#### Miniature Worlds & Model Parks")
    st.markdown(
        '<p style="color:#8b97b0;">Tiny replicas of our biggest landmarks - '
        'from LEGO empires to 1:25 scale nations. Big imagination, small scale.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(MINIATURE_WORLDS)

    type_counts = df["type"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Miniature Parks", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("LEGO Parks", len(df[df["type"].str.contains("LEGO")]))
    c4.metric("Oldest (opened)", int(df["opened"].min()))

    # Timeline
    df_sorted = df.sort_values("opened")
    _dark_bar_chart(
        labels=df_sorted["name"].tolist(),
        values=df_sorted["opened"].tolist(),
        colors=[ACCENT_TEAL] * len(df_sorted),
        xlabel="Year Opened",
        ylabel="",
        title="Miniature Parks - Opening Timeline",
    )

    # Map
    st.markdown("##### Miniature Parks World Map")
    m = _build_map(45, 10, zoom=3)
    for park in MINIATURE_WORLDS:
        is_lego = "LEGO" in park.get("type", "")
        color = ACCENT_AMBER if is_lego else ACCENT_TEAL
        popup = _safe_popup(park["name"], {
            "Type": park["type"], "Country": park["country"],
            "Opened": str(park["opened"]), "Note": park["note"],
        })
        folium.CircleMarker(
            location=[park["lat"], park["lon"]], radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'<span style="color:{ACCENT_AMBER}; font-size:0.8rem;">&#9679; LEGO Theme Park</span>'
        f'<span style="color:{ACCENT_TEAL}; font-size:0.8rem;">&#9679; Model / Miniature Park</span>'
        '</div>', unsafe_allow_html=True,
    )
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} parks)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "miniature_worlds.csv",
                  f"Download {len(df)} Miniature Parks (CSV)", "dl_miniature")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 9 - ADVENTURE PARKS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_adventure_parks():
    """Zip lines, treetop walks, bungee jumps, extreme sport parks."""
    st.markdown("#### Adventure & Extreme Parks")
    st.markdown(
        '<p style="color:#8b97b0;">Adrenaline beyond theme parks - zip lines over '
        'canyons, bungee jumps from towers, via ferratas on Alpine cliffs, and '
        'canopy walks through ancient forests.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(ADVENTURE_PARKS)

    type_counts = df["type"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Adventure Venues", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Activity Types", df["type"].nunique())
    c4.metric("Bungee Jumps", len(df[df["type"].str.contains("Bungee")]))

    # Activity type breakdown
    _dark_bar_chart(
        labels=type_counts.index.tolist(),
        values=type_counts.values.tolist(),
        colors=[ACCENT_FUCHSIA] * len(type_counts),
        xlabel="Count",
        ylabel="",
        title="Adventure Activities by Type",
    )

    # Map
    st.markdown("##### Adventure Parks World Map")
    m = _build_map(20, 20, zoom=2)
    activity_colors = {
        "Bungee Jump": ACCENT_RED,
        "Zip Line": ACCENT_EMERALD,
        "Treetop Course": ACCENT_AMBER,
        "Canopy Walk": ACCENT_AMBER,
        "Via Ferrata": ACCENT_CYAN,
        "Canyoning": ACCENT_BLUE,
        "Giant Swing": ACCENT_PINK,
        "Skywalk": ACCENT_VIOLET,
    }
    for venue in ADVENTURE_PARKS:
        color = activity_colors.get(venue["type"], ACCENT_FUCHSIA)
        popup = _safe_popup(venue["name"], {
            "Type": venue["type"], "Country": venue["country"],
            "Note": venue["note"],
        })
        folium.CircleMarker(
            location=[venue["lat"], venue["lon"]], radius=7,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} venues)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "adventure_parks.csv",
                  f"Download {len(df)} Adventure Parks (CSV)", "dl_adventure")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 10 - CASINO & RESORT CITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_casino_resorts():
    """Monte Carlo, Macau, Atlantic City, Las Vegas - gaming capitals."""
    st.markdown("#### Casino & Resort Cities")
    st.markdown(
        '<p style="color:#8b97b0;">Where fortune favors the bold - the world\'s '
        'most glamorous casino destinations from Monte Carlo elegance to '
        'Macau\'s staggering revenue powerhouses.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(CASINO_RESORT_CITIES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Casino Destinations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Revenue ($B)", f"{df['revenue_b'].sum():.1f}")
    c4.metric("Total Casinos", int(df["casinos"].sum()))

    # Revenue chart
    top_rev = df.nlargest(12, "revenue_b")
    _dark_bar_chart(
        labels=top_rev["name"].tolist(),
        values=top_rev["revenue_b"].tolist(),
        colors=[ACCENT_BLUE] * len(top_rev),
        xlabel="Annual Revenue ($ Billion)",
        ylabel="",
        title="Top Casino Destinations by Revenue",
    )

    # Map
    st.markdown("##### Casino & Resort World Map")
    m = _build_map(25, 20, zoom=2)
    for venue in CASINO_RESORT_CITIES:
        # Scale radius by revenue
        r = max(5, min(14, int(venue["revenue_b"] * 2) + 4))
        popup = _safe_popup(venue["name"], {
            "Country": venue["country"],
            "Revenue": f"${venue['revenue_b']}B",
            "Casinos": str(venue["casinos"]),
            "Note": venue["note"],
        })
        folium.CircleMarker(
            location=[venue["lat"], venue["lon"]], radius=r,
            color=ACCENT_BLUE, fill=True, fill_color=ACCENT_BLUE,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} destinations)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "casino_resort_cities.csv",
                  f"Download {len(df)} Casino Destinations (CSV)", "dl_casinos")


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE OVERPASS SEARCH SUB-TAB
# ═══════════════════════════════════════════════════════════════════════════════

LIVE_PRESETS = {
    "Custom": None,
    "Orlando, Florida": {"lat": 28.4177, "lon": -81.5812, "radius": 30},
    "Tokyo Disney / Chiba": {"lat": 35.6329, "lon": 139.8804, "radius": 15},
    "Paris - Disneyland Area": {"lat": 48.8674, "lon": 2.7836, "radius": 20},
    "Los Angeles - Hollywood": {"lat": 34.0928, "lon": -118.3287, "radius": 20},
    "Las Vegas Strip": {"lat": 36.1147, "lon": -115.1728, "radius": 10},
    "Dubai": {"lat": 25.1972, "lon": 55.2796, "radius": 25},
    "Singapore - Sentosa": {"lat": 1.2494, "lon": 103.8303, "radius": 10},
    "Rust - Europa-Park": {"lat": 48.2661, "lon": 7.7220, "radius": 15},
    "Copenhagen - Tivoli": {"lat": 55.6736, "lon": 12.5681, "radius": 10},
    "Gold Coast, Australia": {"lat": -27.9885, "lon": 153.4310, "radius": 20},
}


def _mode_live_search():
    """Live Overpass search for theme parks, rides, and entertainment nearby."""
    st.markdown("#### Live Amusement Search (OpenStreetMap)")
    st.markdown(
        '<p style="color:#8b97b0;">Search for real theme parks, amusement rides, '
        'water parks, zoos, aquariums, and entertainment venues from OpenStreetMap\'s '
        'live database via Overpass API.</p>',
        unsafe_allow_html=True,
    )

    # Controls
    st.markdown("##### Search Parameters")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        live_lat = st.number_input("Latitude", value=28.4177, format="%.4f",
                                   min_value=-90.0, max_value=90.0, key="amuse_lat")
    with col2:
        live_lon = st.number_input("Longitude", value=-81.5812, format="%.4f",
                                   min_value=-180.0, max_value=180.0, key="amuse_lon")
    with col3:
        live_radius = st.slider("Radius (km)", 1, 50, 15, key="amuse_radius")

    preset_name = st.selectbox("Quick Location Presets",
                               list(LIVE_PRESETS.keys()), key="amuse_preset")
    if preset_name != "Custom" and LIVE_PRESETS.get(preset_name):
        p = LIVE_PRESETS[preset_name]
        live_lat = p["lat"]
        live_lon = p["lon"]
        live_radius = p["radius"]

    search_types = st.multiselect(
        "Feature Types to Search",
        ["Theme Parks & Rides", "Zoos & Aquariums", "Entertainment Venues"],
        default=["Theme Parks & Rides"],
        key="amuse_search_types",
    )

    if st.button("Search Amusement Venues", key="amuse_search_btn", use_container_width=True):
        st.session_state.amuse_search = {
            "lat": live_lat, "lon": live_lon,
            "radius": live_radius, "types": search_types,
        }

    if "amuse_search" not in st.session_state:
        st.info("Configure search parameters and click Search to find "
                "amusement venues from OpenStreetMap.")
        return

    params = st.session_state.amuse_search
    all_features = []

    with st.spinner("Querying Overpass API for amusement venues..."):
        if "Theme Parks & Rides" in params["types"]:
            all_features.extend(_overpass_theme_parks(
                params["lat"], params["lon"], params["radius"]))
        if "Zoos & Aquariums" in params["types"]:
            all_features.extend(_overpass_zoos_aquariums(
                params["lat"], params["lon"], params["radius"]))
        if "Entertainment Venues" in params["types"]:
            all_features.extend(_overpass_entertainment(
                params["lat"], params["lon"], params["radius"]))

    if not all_features:
        st.warning("No amusement venues found. Try a larger radius or different location.")
        return

    # Deduplicate by osm_id
    seen_ids = set()
    unique = []
    for f in all_features:
        fid = f.get("osm_id")
        if fid and fid not in seen_ids:
            seen_ids.add(fid)
            unique.append(f)
        elif not fid:
            unique.append(f)
    all_features = unique

    # Stats
    st.markdown("---")
    st.markdown("#### Search Results")
    type_counts = {}
    for f in all_features:
        t = f.get("type", "other")
        type_counts[t] = type_counts.get(t, 0) + 1

    cols = st.columns(min(len(type_counts) + 1, 5))
    cols[0].metric("Total Venues", len(all_features))
    for i, (t, cnt) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(cols):
            cols[i + 1].metric(t.replace("_", " ").title()[:20], cnt)

    # Map
    st.markdown("##### Venue Map")
    m = _build_map(params["lat"], params["lon"], zoom=11)
    folium.Circle(
        location=[params["lat"], params["lon"]],
        radius=params["radius"] * 1000,
        color=ACCENT_CYAN, fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)

    osm_type_colors = {
        "theme_park": ACCENT_PINK,
        "water_park": ACCENT_CYAN,
        "zoo": ACCENT_EMERALD,
        "aquarium": ACCENT_BLUE,
        "casino": ACCENT_AMBER,
        "cinema": ACCENT_VIOLET,
        "nightclub": ACCENT_FUCHSIA,
        "theatre": ACCENT_RED,
        "amusement_arcade": ACCENT_ORANGE,
        "amusement_ride": ACCENT_PINK,
        "miniature_golf": ACCENT_TEAL,
    }

    for f in all_features:
        color = osm_type_colors.get(f["type"], TEXT_MUTED)
        popup = _safe_popup(f["name"], {
            "Type": f["type"].replace("_", " ").title(),
            "Website": f.get("website", ""),
            "Hours": f.get("opening_hours", ""),
            "OSM ID": str(f.get("osm_id", "")),
        })
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=7,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2, popup=popup,
        ).add_to(m)
    _show_map(m)

    # Data table
    rows = []
    for f in all_features:
        rows.append({
            "name": f["name"],
            "type": f["type"],
            "latitude": round(f["lat"], 5),
            "longitude": round(f["lon"], 5),
            "website": f.get("website", ""),
            "opening_hours": f.get("opening_hours", ""),
            "osm_id": f.get("osm_id", ""),
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} venues)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "osm_amusement_venues.csv",
                  f"Download {len(df)} OSM Venues (CSV)", "dl_osm_amuse")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

MAP_MODES = [
    "World's Greatest Theme Parks",
    "Roller Coasters",
    "Water Parks",
    "Historic Amusement Parks",
    "Zoos & Aquariums",
    "Circus & Carnival Heritage",
    "Entertainment Districts",
    "Miniature Worlds",
    "Adventure Parks",
    "Casino & Resort Cities",
    "Live Overpass Search",
]

MODE_ICONS = {
    "World's Greatest Theme Parks": "\U0001f3f0",
    "Roller Coasters": "\U0001f3a2",
    "Water Parks": "\U0001f30a",
    "Historic Amusement Parks": "\U0001f3aa",
    "Zoos & Aquariums": "\U0001f418",
    "Circus & Carnival Heritage": "\U0001f3ad",
    "Entertainment Districts": "\U0001f3b0",
    "Miniature Worlds": "\U0001f9e9",
    "Adventure Parks": "\U0001fa82",
    "Casino & Resort Cities": "\U0001f0cf",
    "Live Overpass Search": "\U0001f50d",
}


def render_amusement_maps_tab():
    """Main render function for the Amusement & Theme Parks Explorer tab."""

    # Tab header
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f3a2 Amusement & Theme Parks Explorer</h4>'
        '<p>Discover the world\'s greatest theme parks, roller coasters, water parks, '
        'zoos, entertainment districts, and more. 10 curated map modes plus live '
        'OpenStreetMap search powered by Overpass API.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Mode selector
    selected_mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        format_func=lambda x: f"{MODE_ICONS.get(x, '')} {x}",
        key="amuse_mode_select",
    )

    st.markdown("---")

    # Route to mode
    if selected_mode == "World's Greatest Theme Parks":
        _mode_greatest_theme_parks()
    elif selected_mode == "Roller Coasters":
        _mode_roller_coasters()
    elif selected_mode == "Water Parks":
        _mode_water_parks()
    elif selected_mode == "Historic Amusement Parks":
        _mode_historic_parks()
    elif selected_mode == "Zoos & Aquariums":
        _mode_zoos_aquariums()
    elif selected_mode == "Circus & Carnival Heritage":
        _mode_circus_carnival()
    elif selected_mode == "Entertainment Districts":
        _mode_entertainment_districts()
    elif selected_mode == "Miniature Worlds":
        _mode_miniature_worlds()
    elif selected_mode == "Adventure Parks":
        _mode_adventure_parks()
    elif selected_mode == "Casino & Resort Cities":
        _mode_casino_resorts()
    elif selected_mode == "Live Overpass Search":
        _mode_live_search()
