# -*- coding: utf-8 -*-
"""
Animal Distribution Maps module for TerraScout AI.
Curated wildlife distribution data: zoogeographic realms, big cats, primates,
marine megafauna, marsupials, bird flyways, endangered hotspots, invasive species,
deep sea creatures, and extinct species last known locations.
All data is curated (no external API required).
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    from folium import plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ═══════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_COLOR = "#06b6d4"
SECONDARY_TEXT = "#8b97b0"
MUTED_TEXT = "#5a6580"

# ═══════════════════════════════════════════════════════════════
# 1. ZOOGEOGRAPHIC REALMS
# ═══════════════════════════════════════════════════════════════
ZOOGEOGRAPHIC_REALMS = {
    "Nearctic": {
        "center": [50.0, -105.0],
        "color": "#3b82f6",
        "bounds": [[30, -170], [30, -50], [72, -50], [72, -170]],
        "area_km2": "22.9 million",
        "characteristic_species": [
            "Bison (Bison bison)", "Pronghorn (Antilocapra americana)",
            "Bald Eagle (Haliaeetus leucocephalus)", "American Black Bear (Ursus americanus)",
            "Prairie Dog (Cynomys ludovicianus)", "Roadrunner (Geococcyx californianus)",
        ],
        "description": "North America north of tropical Mexico. Characterized by large ungulates, diverse raptors, and temperate forest fauna.",
    },
    "Palearctic": {
        "center": [50.0, 60.0],
        "color": "#8b5cf6",
        "bounds": [[25, -10], [25, 170], [72, 170], [72, -10]],
        "area_km2": "54.1 million",
        "characteristic_species": [
            "Eurasian Brown Bear (Ursus arctos)", "Red Fox (Vulpes vulpes)",
            "Snow Leopard (Panthera uncia)", "Saiga Antelope (Saiga tatarica)",
            "European Robin (Erithacus rubecula)", "Giant Panda (Ailuropoda melanoleuca)",
        ],
        "description": "Europe, northern Asia, North Africa, and northern Arabian Peninsula. Largest biogeographic realm.",
    },
    "Afrotropic": {
        "center": [-2.0, 22.0],
        "color": "#f59e0b",
        "bounds": [[-35, -20], [-35, 55], [20, 55], [20, -20]],
        "area_km2": "22.1 million",
        "characteristic_species": [
            "African Elephant (Loxodonta africana)", "Gorilla (Gorilla gorilla)",
            "Okapi (Okapia johnstoni)", "African Wild Dog (Lycaon pictus)",
            "Shoebill (Balaeniceps rex)", "Aardvark (Orycteropus afer)",
        ],
        "description": "Sub-Saharan Africa, southern Arabian Peninsula, and Madagascar. Richest large mammal fauna on Earth.",
    },
    "Indomalayan": {
        "center": [15.0, 100.0],
        "color": "#10b981",
        "bounds": [[0, 60], [0, 150], [35, 150], [35, 60]],
        "area_km2": "7.5 million",
        "characteristic_species": [
            "Asian Elephant (Elephas maximus)", "Bengal Tiger (Panthera tigris tigris)",
            "Orangutan (Pongo pygmaeus)", "Indian Rhinoceros (Rhinoceros unicornis)",
            "Red Panda (Ailurus fulgens)", "Tarsier (Carlito syrichta)",
        ],
        "description": "South and Southeast Asia, including Indonesia west of Wallace Line. Megadiverse tropical ecosystems.",
    },
    "Australasia": {
        "center": [-25.0, 140.0],
        "color": "#ef4444",
        "bounds": [[-50, 110], [-50, 180], [-5, 180], [-5, 110]],
        "area_km2": "7.6 million",
        "characteristic_species": [
            "Kangaroo (Macropus spp.)", "Platypus (Ornithorhynchus anatinus)",
            "Kiwi (Apteryx spp.)", "Cassowary (Casuarius casuarius)",
            "Koala (Phascolarctos cinereus)", "Tuatara (Sphenodon punctatus)",
        ],
        "description": "Australia, New Guinea, New Zealand, and eastern Indonesia. Unique marsupial and monotreme fauna.",
    },
    "Neotropic": {
        "center": [-10.0, -60.0],
        "color": "#ec4899",
        "bounds": [[-56, -90], [-56, -30], [25, -30], [25, -90]],
        "area_km2": "19.0 million",
        "characteristic_species": [
            "Jaguar (Panthera onca)", "Sloth (Bradypus spp.)",
            "Toucan (Ramphastos spp.)", "Capybara (Hydrochoerus hydrochaeris)",
            "Poison Dart Frog (Dendrobates spp.)", "Anaconda (Eunectes murinus)",
        ],
        "description": "South America, Central America, Caribbean, and tropical Mexico. Highest biodiversity of any realm.",
    },
    "Oceania": {
        "center": [-5.0, -170.0],
        "color": "#06b6d4",
        "bounds": [[-25, 160], [-25, -120], [20, -120], [20, 160]],
        "area_km2": "1.0 million",
        "characteristic_species": [
            "Hawaiian Honeycreeper (Drepanidinae)", "Coconut Crab (Birgus latro)",
            "Fiji Banded Iguana (Brachylophus fasciatus)", "Samoan Flying Fox (Pteropus samoensis)",
            "Hawaiian Monk Seal (Neomonachus schauinslandi)", "Kagu (Rhynochetos jubatus)",
        ],
        "description": "Pacific islands (Polynesia, Micronesia, Fiji). High endemism on isolated island chains.",
    },
    "Antarctic": {
        "center": [-80.0, 0.0],
        "color": "#94a3b8",
        "bounds": [[-90, -180], [-90, 180], [-60, 180], [-60, -180]],
        "area_km2": "14.0 million",
        "characteristic_species": [
            "Emperor Penguin (Aptenodytes forsteri)", "Leopard Seal (Hydrurga leptonyx)",
            "Wandering Albatross (Diomedea exulans)", "Antarctic Krill (Euphausia superba)",
            "Weddell Seal (Leptonychotes weddellii)", "South Polar Skua (Stercorarius maccormicki)",
        ],
        "description": "Antarctica and surrounding Southern Ocean. Extreme cold-adapted marine and avian fauna.",
    },
}

# ═══════════════════════════════════════════════════════════════
# 2. BIG CATS DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
BIG_CATS = {
    "African Lion": {
        "scientific": "Panthera leo",
        "color": "#f59e0b",
        "icon": "paw",
        "status": "Vulnerable",
        "population": "~23,000",
        "range_points": [
            {"lat": -2.3, "lon": 34.8, "name": "Serengeti, Tanzania"},
            {"lat": -13.5, "lon": 31.5, "name": "South Luangwa, Zambia"},
            {"lat": -19.0, "lon": 23.5, "name": "Okavango Delta, Botswana"},
            {"lat": -24.0, "lon": 31.5, "name": "Kruger, South Africa"},
            {"lat": 9.0, "lon": 38.7, "name": "Ethiopian Highlands"},
            {"lat": 1.5, "lon": 32.0, "name": "Queen Elizabeth NP, Uganda"},
            {"lat": -1.3, "lon": 36.8, "name": "Nairobi NP, Kenya"},
            {"lat": -15.5, "lon": 28.3, "name": "Kafue, Zambia"},
        ],
    },
    "Bengal Tiger": {
        "scientific": "Panthera tigris tigris",
        "color": "#ef4444",
        "icon": "paw",
        "status": "Endangered",
        "population": "~3,500",
        "range_points": [
            {"lat": 27.5, "lon": 89.5, "name": "Royal Manas, Bhutan"},
            {"lat": 21.5, "lon": 80.0, "name": "Pench, India"},
            {"lat": 25.0, "lon": 83.0, "name": "Bandhavgarh, India"},
            {"lat": 26.7, "lon": 84.3, "name": "Chitwan, Nepal"},
            {"lat": 22.3, "lon": 89.2, "name": "Sundarbans, Bangladesh"},
            {"lat": 24.5, "lon": 93.5, "name": "Kaziranga, India"},
            {"lat": 15.0, "lon": 74.0, "name": "Western Ghats, India"},
            {"lat": 23.5, "lon": 77.5, "name": "Satpura, India"},
        ],
    },
    "Leopard": {
        "scientific": "Panthera pardus",
        "color": "#a855f7",
        "icon": "paw",
        "status": "Vulnerable",
        "population": "~250,000 (all subspecies)",
        "range_points": [
            {"lat": -2.5, "lon": 34.0, "name": "Serengeti, Tanzania"},
            {"lat": -24.0, "lon": 31.5, "name": "Kruger NP, South Africa"},
            {"lat": 47.0, "lon": 134.0, "name": "Land of the Leopard NP, Russia"},
            {"lat": 10.0, "lon": 76.5, "name": "Western Ghats, India"},
            {"lat": 34.0, "lon": 72.0, "name": "Margalla Hills, Pakistan"},
            {"lat": 3.0, "lon": 101.5, "name": "Taman Negara, Malaysia"},
        ],
    },
    "Jaguar": {
        "scientific": "Panthera onca",
        "color": "#f97316",
        "icon": "paw",
        "status": "Near Threatened",
        "population": "~173,000",
        "range_points": [
            {"lat": -3.0, "lon": -60.0, "name": "Amazon Basin, Brazil"},
            {"lat": -16.7, "lon": -56.8, "name": "Pantanal, Brazil"},
            {"lat": 17.2, "lon": -88.6, "name": "Cockscomb Basin, Belize"},
            {"lat": 10.4, "lon": -84.0, "name": "Corcovado, Costa Rica"},
            {"lat": -21.5, "lon": -59.0, "name": "Gran Chaco, Paraguay"},
            {"lat": 19.5, "lon": -88.0, "name": "Calakmul, Mexico"},
        ],
    },
    "Cheetah": {
        "scientific": "Acinonyx jubatus",
        "color": "#10b981",
        "icon": "paw",
        "status": "Vulnerable",
        "population": "~6,500",
        "range_points": [
            {"lat": -2.3, "lon": 34.8, "name": "Serengeti, Tanzania"},
            {"lat": -21.0, "lon": 17.0, "name": "Etosha, Namibia"},
            {"lat": -24.0, "lon": 31.5, "name": "Kruger, South Africa"},
            {"lat": -19.8, "lon": 25.3, "name": "Central Kalahari, Botswana"},
            {"lat": 34.0, "lon": 51.0, "name": "Touran, Iran (Asiatic)"},
            {"lat": 0.3, "lon": 36.1, "name": "Laikipia, Kenya"},
        ],
    },
    "Snow Leopard": {
        "scientific": "Panthera uncia",
        "color": "#94a3b8",
        "icon": "paw",
        "status": "Vulnerable",
        "population": "~4,000-6,500",
        "range_points": [
            {"lat": 36.0, "lon": 75.0, "name": "Karakoram, Pakistan"},
            {"lat": 43.0, "lon": 77.0, "name": "Tien Shan, Kazakhstan"},
            {"lat": 28.0, "lon": 86.9, "name": "Sagarmatha, Nepal"},
            {"lat": 47.0, "lon": 90.0, "name": "Altai Mountains, Mongolia"},
            {"lat": 34.5, "lon": 77.5, "name": "Hemis, India (Ladakh)"},
            {"lat": 39.0, "lon": 71.0, "name": "Pamir Mountains, Tajikistan"},
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# 3. GREAT APES & PRIMATES
# ═══════════════════════════════════════════════════════════════
PRIMATES = {
    "Mountain Gorilla": {
        "scientific": "Gorilla beringei beringei",
        "color": "#6b7280",
        "status": "Endangered",
        "population": "~1,063",
        "locations": [
            {"lat": -1.4, "lon": 29.5, "name": "Virunga NP, DRC"},
            {"lat": -1.5, "lon": 29.6, "name": "Volcanoes NP, Rwanda"},
            {"lat": -1.1, "lon": 29.6, "name": "Bwindi Impenetrable, Uganda"},
        ],
    },
    "Western Lowland Gorilla": {
        "scientific": "Gorilla gorilla gorilla",
        "color": "#8b5cf6",
        "status": "Critically Endangered",
        "population": "~360,000",
        "locations": [
            {"lat": -0.5, "lon": 14.5, "name": "Odzala-Kokoua, Congo"},
            {"lat": 2.0, "lon": 10.0, "name": "Campo Ma'an, Cameroon"},
            {"lat": 0.5, "lon": 11.5, "name": "Lope NP, Gabon"},
            {"lat": 1.5, "lon": 16.0, "name": "Dzanga-Sangha, CAR"},
        ],
    },
    "Common Chimpanzee": {
        "scientific": "Pan troglodytes",
        "color": "#f59e0b",
        "status": "Endangered",
        "population": "~170,000-300,000",
        "locations": [
            {"lat": -5.5, "lon": 29.6, "name": "Gombe Stream, Tanzania"},
            {"lat": 0.5, "lon": 30.4, "name": "Kibale, Uganda"},
            {"lat": 7.6, "lon": -8.5, "name": "Tai NP, Ivory Coast"},
            {"lat": 1.5, "lon": 10.0, "name": "Monte Alen, Equatorial Guinea"},
            {"lat": -4.5, "lon": 29.2, "name": "Mahale Mountains, Tanzania"},
        ],
    },
    "Bonobo": {
        "scientific": "Pan paniscus",
        "color": "#ec4899",
        "status": "Endangered",
        "population": "~15,000-20,000",
        "locations": [
            {"lat": -1.5, "lon": 21.0, "name": "Salonga NP, DRC"},
            {"lat": -2.5, "lon": 20.5, "name": "Lomako Forest, DRC"},
            {"lat": -0.3, "lon": 21.5, "name": "Luo Reserve, DRC"},
        ],
    },
    "Bornean Orangutan": {
        "scientific": "Pongo pygmaeus",
        "color": "#f97316",
        "status": "Critically Endangered",
        "population": "~104,000",
        "locations": [
            {"lat": 0.5, "lon": 114.0, "name": "Tanjung Puting, Borneo"},
            {"lat": 5.5, "lon": 118.0, "name": "Kinabatangan, Sabah"},
            {"lat": 1.0, "lon": 110.0, "name": "Danau Sentarum, W Kalimantan"},
            {"lat": -1.0, "lon": 116.5, "name": "Kutai NP, E Kalimantan"},
        ],
    },
    "Sumatran Orangutan": {
        "scientific": "Pongo abelii",
        "color": "#ef4444",
        "status": "Critically Endangered",
        "population": "~14,600",
        "locations": [
            {"lat": 3.5, "lon": 97.5, "name": "Gunung Leuser NP, Sumatra"},
            {"lat": 2.5, "lon": 98.0, "name": "Batang Toru, Sumatra"},
        ],
    },
    "Lar Gibbon": {
        "scientific": "Hylobates lar",
        "color": "#06b6d4",
        "status": "Endangered",
        "population": "Unknown (declining)",
        "locations": [
            {"lat": 8.5, "lon": 98.5, "name": "Khao Sok, Thailand"},
            {"lat": 4.0, "lon": 101.0, "name": "Taman Negara, Malaysia"},
            {"lat": 14.5, "lon": 98.5, "name": "Huai Kha Khaeng, Thailand"},
        ],
    },
    "Ring-tailed Lemur": {
        "scientific": "Lemur catta",
        "color": "#a855f7",
        "status": "Endangered",
        "population": "~2,000-2,400 (wild)",
        "locations": [
            {"lat": -23.4, "lon": 46.4, "name": "Andohahela NP, Madagascar"},
            {"lat": -23.0, "lon": 44.6, "name": "Isalo NP, Madagascar"},
            {"lat": -24.8, "lon": 46.2, "name": "Berenty Reserve, Madagascar"},
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# 4. MARINE MEGAFAUNA
# ═══════════════════════════════════════════════════════════════
WHALE_ROUTES = {
    "Humpback Whale (N. Atlantic)": {
        "color": "#3b82f6",
        "route": [
            [65.0, -20.0], [55.0, -25.0], [40.0, -30.0],
            [25.0, -40.0], [18.0, -65.0],
        ],
        "description": "Iceland/Norway to Caribbean breeding grounds",
    },
    "Humpback Whale (N. Pacific)": {
        "color": "#60a5fa",
        "route": [
            [58.0, -152.0], [50.0, -145.0], [40.0, -140.0],
            [30.0, -135.0], [20.0, -156.0],
        ],
        "description": "Alaska to Hawaii breeding grounds",
    },
    "Gray Whale (Eastern Pacific)": {
        "color": "#8b5cf6",
        "route": [
            [65.0, -170.0], [55.0, -165.0], [45.0, -130.0],
            [35.0, -122.0], [25.0, -113.0],
        ],
        "description": "Bering Sea to Baja California lagoons, ~10,000 mi round trip",
    },
    "Blue Whale (Southern Hemisphere)": {
        "color": "#06b6d4",
        "route": [
            [-60.0, -60.0], [-50.0, -40.0], [-35.0, -20.0],
            [-20.0, -10.0], [-10.0, 0.0],
        ],
        "description": "Antarctic feeding to tropical breeding, longest migration of any baleen whale",
    },
}

SHARK_HOTSPOTS = [
    {"lat": -34.0, "lon": 18.5, "name": "False Bay, South Africa", "species": "Great White Shark", "color": "#ef4444"},
    {"lat": 21.3, "lon": -157.8, "name": "North Shore, Oahu", "species": "Tiger Shark", "color": "#f59e0b"},
    {"lat": 24.5, "lon": -77.0, "name": "Bahamas", "species": "Caribbean Reef Shark", "color": "#3b82f6"},
    {"lat": -18.0, "lon": 147.0, "name": "Great Barrier Reef", "species": "Whale Shark", "color": "#8b5cf6"},
    {"lat": 12.0, "lon": -87.0, "name": "Cocos Island, Costa Rica", "species": "Hammerhead Shark", "color": "#ec4899"},
    {"lat": 26.7, "lon": -80.0, "name": "Palm Beach, Florida", "species": "Bull Shark", "color": "#f97316"},
    {"lat": -0.5, "lon": -90.5, "name": "Galapagos Islands", "species": "Galapagos Shark", "color": "#10b981"},
    {"lat": -8.5, "lon": 115.5, "name": "Nusa Penida, Bali", "species": "Mola Mola & Manta Ray", "color": "#06b6d4"},
]

SEA_TURTLE_NESTING = [
    {"lat": 27.5, "lon": -80.3, "name": "Melbourne Beach, Florida", "species": "Loggerhead", "nests_yr": "~15,000", "color": "#f59e0b"},
    {"lat": 20.2, "lon": -87.4, "name": "Riviera Maya, Mexico", "species": "Green & Loggerhead", "nests_yr": "~5,000", "color": "#10b981"},
    {"lat": 5.5, "lon": -54.0, "name": "Suriname Coast", "species": "Leatherback", "nests_yr": "~3,000", "color": "#8b5cf6"},
    {"lat": -23.8, "lon": 35.4, "name": "Bazaruto, Mozambique", "species": "Loggerhead & Green", "nests_yr": "~1,200", "color": "#3b82f6"},
    {"lat": 36.8, "lon": 29.1, "name": "Dalyan, Turkey", "species": "Loggerhead", "nests_yr": "~300", "color": "#ef4444"},
    {"lat": 23.6, "lon": 57.0, "name": "Ras Al Jinz, Oman", "species": "Green Turtle", "nests_yr": "~20,000", "color": "#06b6d4"},
    {"lat": -21.0, "lon": 55.5, "name": "Reunion Island", "species": "Green & Hawksbill", "nests_yr": "~500", "color": "#ec4899"},
    {"lat": -23.4, "lon": 151.9, "name": "Mon Repos, Australia", "species": "Loggerhead", "nests_yr": "~800", "color": "#a855f7"},
]

# ═══════════════════════════════════════════════════════════════
# 5. MARSUPIAL DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
MARSUPIALS = {
    "Red Kangaroo": {
        "scientific": "Osphranter rufus",
        "color": "#ef4444",
        "status": "Least Concern",
        "population": "~11 million",
        "locations": [
            {"lat": -23.7, "lon": 133.8, "name": "Alice Springs, NT"},
            {"lat": -31.5, "lon": 145.0, "name": "Western NSW"},
            {"lat": -26.0, "lon": 140.0, "name": "Sturt NP, NSW"},
            {"lat": -28.0, "lon": 119.0, "name": "Meekatharra, WA"},
        ],
    },
    "Koala": {
        "scientific": "Phascolarctos cinereus",
        "color": "#8b5cf6",
        "status": "Vulnerable",
        "population": "~32,000-58,000",
        "locations": [
            {"lat": -27.5, "lon": 153.0, "name": "Brisbane, QLD"},
            {"lat": -33.7, "lon": 151.2, "name": "Sydney, NSW"},
            {"lat": -38.5, "lon": 143.8, "name": "Great Otway NP, VIC"},
            {"lat": -34.7, "lon": 138.6, "name": "Adelaide Hills, SA"},
            {"lat": -30.5, "lon": 152.9, "name": "Port Macquarie, NSW"},
        ],
    },
    "Common Wombat": {
        "scientific": "Vombatus ursinus",
        "color": "#a0522d",
        "status": "Least Concern",
        "population": "Stable",
        "locations": [
            {"lat": -37.3, "lon": 146.5, "name": "Alpine NP, VIC"},
            {"lat": -41.5, "lon": 146.0, "name": "Cradle Mountain, TAS"},
            {"lat": -33.5, "lon": 150.0, "name": "Blue Mountains, NSW"},
        ],
    },
    "Tasmanian Devil": {
        "scientific": "Sarcophilus harrisii",
        "color": "#1e1e2e",
        "status": "Endangered",
        "population": "~25,000",
        "locations": [
            {"lat": -41.5, "lon": 146.0, "name": "Cradle Mountain, TAS"},
            {"lat": -42.9, "lon": 147.3, "name": "Hobart area, TAS"},
            {"lat": -41.2, "lon": 148.2, "name": "Bay of Fires, TAS"},
        ],
    },
    "Quokka": {
        "scientific": "Setonix brachyurus",
        "color": "#f59e0b",
        "status": "Vulnerable",
        "population": "~8,000-17,000",
        "locations": [
            {"lat": -32.0, "lon": 115.5, "name": "Rottnest Island, WA"},
            {"lat": -34.0, "lon": 115.2, "name": "Two Peoples Bay, WA"},
        ],
    },
    "Sugar Glider": {
        "scientific": "Petaurus breviceps",
        "color": "#10b981",
        "status": "Least Concern",
        "population": "Abundant",
        "locations": [
            {"lat": -16.9, "lon": 145.8, "name": "Daintree, QLD"},
            {"lat": -33.0, "lon": 151.3, "name": "Ku-ring-gai, NSW"},
            {"lat": -5.5, "lon": 141.0, "name": "PNG Lowlands"},
        ],
    },
    "Virginia Opossum": {
        "scientific": "Didelphis virginiana",
        "color": "#94a3b8",
        "status": "Least Concern",
        "population": "Abundant",
        "locations": [
            {"lat": 37.0, "lon": -79.0, "name": "Virginia, USA"},
            {"lat": 30.0, "lon": -90.0, "name": "Louisiana, USA"},
            {"lat": 43.0, "lon": -89.0, "name": "Wisconsin, USA"},
            {"lat": 19.4, "lon": -99.1, "name": "Mexico City, Mexico"},
        ],
    },
    "Monito del Monte": {
        "scientific": "Dromiciops gliroides",
        "color": "#ec4899",
        "status": "Near Threatened",
        "population": "Unknown",
        "locations": [
            {"lat": -39.8, "lon": -72.0, "name": "Valdivian Forest, Chile"},
            {"lat": -41.0, "lon": -71.5, "name": "Patagonian Andes, Argentina"},
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# 6. BIRD MIGRATION FLYWAYS
# ═══════════════════════════════════════════════════════════════
FLYWAYS = {
    "Atlantic Americas Flyway": {
        "color": "#3b82f6",
        "route": [
            [70.0, -60.0], [60.0, -65.0], [45.0, -70.0],
            [35.0, -75.0], [25.0, -80.0], [10.0, -70.0],
            [-5.0, -55.0], [-20.0, -45.0], [-35.0, -55.0],
        ],
        "key_species": "Red Knot, Semipalmated Sandpiper, Whimbrel",
        "description": "Eastern Americas: Arctic Canada to Tierra del Fuego",
    },
    "Mississippi Americas Flyway": {
        "color": "#10b981",
        "route": [
            [65.0, -95.0], [55.0, -95.0], [45.0, -93.0],
            [35.0, -92.0], [25.0, -90.0], [15.0, -88.0],
            [5.0, -80.0], [-10.0, -70.0],
        ],
        "key_species": "Snow Goose, Sandhill Crane, American Golden Plover",
        "description": "Central Americas: Hudson Bay through Mississippi Valley",
    },
    "Central Americas Flyway": {
        "color": "#f59e0b",
        "route": [
            [65.0, -110.0], [55.0, -110.0], [45.0, -108.0],
            [35.0, -105.0], [25.0, -100.0], [15.0, -95.0],
        ],
        "key_species": "Swainson's Hawk, Buff-breasted Sandpiper, Whooping Crane",
        "description": "Great Plains of North America to Central America",
    },
    "Pacific Americas Flyway": {
        "color": "#ef4444",
        "route": [
            [65.0, -165.0], [55.0, -155.0], [45.0, -125.0],
            [35.0, -120.0], [25.0, -115.0], [10.0, -105.0],
            [-5.0, -85.0], [-20.0, -75.0], [-35.0, -72.0],
        ],
        "key_species": "Black Brant, Western Sandpiper, Dunlin",
        "description": "Pacific coast: Alaska to Chile",
    },
    "East Atlantic Flyway": {
        "color": "#8b5cf6",
        "route": [
            [72.0, 20.0], [65.0, 10.0], [55.0, 0.0],
            [45.0, -5.0], [35.0, -8.0], [25.0, -10.0],
            [10.0, -5.0], [0.0, 5.0], [-15.0, 15.0], [-30.0, 20.0],
        ],
        "key_species": "Bar-tailed Godwit, Knot, Sanderling",
        "description": "Scandinavia/Siberia along W. Europe/Africa coast to S. Africa",
    },
    "East Asian-Australasian Flyway": {
        "color": "#ec4899",
        "route": [
            [70.0, 170.0], [60.0, 150.0], [50.0, 140.0],
            [40.0, 130.0], [30.0, 125.0], [20.0, 120.0],
            [5.0, 115.0], [-10.0, 120.0], [-25.0, 130.0],
            [-35.0, 140.0],
        ],
        "key_species": "Spoon-billed Sandpiper, Bar-tailed Godwit, Great Knot",
        "description": "Arctic Russia/Alaska to SE Asia and Australia",
    },
    "Central Asian Flyway": {
        "color": "#f97316",
        "route": [
            [70.0, 75.0], [60.0, 70.0], [50.0, 65.0],
            [40.0, 60.0], [30.0, 55.0], [20.0, 50.0],
            [10.0, 45.0], [0.0, 40.0],
        ],
        "key_species": "Demoiselle Crane, Sociable Lapwing, White-headed Duck",
        "description": "Siberia through Central Asia to India and E. Africa",
    },
    "Black Sea-Mediterranean Flyway": {
        "color": "#06b6d4",
        "route": [
            [60.0, 35.0], [50.0, 30.0], [45.0, 28.0],
            [40.0, 30.0], [35.0, 33.0], [30.0, 32.0],
            [20.0, 30.0], [10.0, 32.0], [0.0, 35.0],
        ],
        "key_species": "White Stork, European Honey Buzzard, Pallid Harrier",
        "description": "Eastern Europe through Turkey and Middle East to E. Africa",
    },
}

# ═══════════════════════════════════════════════════════════════
# 7. ENDANGERED SPECIES HOTSPOTS
# ═══════════════════════════════════════════════════════════════
ENDANGERED_HOTSPOTS = [
    {"lat": -18.9, "lon": 47.5, "name": "Madagascar", "species_count": 11516, "cr_species": 514,
     "description": "Lemurs, chameleons, tenrecs. 90% of wildlife found nowhere else.", "color": "#ef4444", "radius": 22},
    {"lat": 0.8, "lon": 113.0, "name": "Borneo", "species_count": 6200, "cr_species": 245,
     "description": "Orangutans, pygmy elephants, proboscis monkeys. Rapid deforestation threat.", "color": "#f59e0b", "radius": 20},
    {"lat": -3.0, "lon": -60.0, "name": "Amazon Basin", "species_count": 40000, "cr_species": 820,
     "description": "Largest tropical rainforest. Jaguars, harpy eagles, river dolphins.", "color": "#10b981", "radius": 25},
    {"lat": -4.0, "lon": 29.5, "name": "Albertine Rift", "species_count": 5800, "cr_species": 380,
     "description": "Mountain gorillas, golden monkeys. Africa's most biodiverse region.", "color": "#8b5cf6", "radius": 18},
    {"lat": 8.0, "lon": 80.0, "name": "Sri Lanka / Western Ghats", "species_count": 5900, "cr_species": 352,
     "description": "Purple frog, lion-tailed macaque. Global biodiversity hotspot.", "color": "#3b82f6", "radius": 17},
    {"lat": -5.5, "lon": 150.0, "name": "Papua New Guinea", "species_count": 4640, "cr_species": 198,
     "description": "Birds of paradise, tree kangaroos. Third-largest rainforest.", "color": "#ec4899", "radius": 18},
    {"lat": 4.0, "lon": 102.0, "name": "Sundaland (SE Asia)", "species_count": 25000, "cr_species": 1500,
     "description": "Sumatran rhino, Sumatran tiger. Among highest deforestation rates.", "color": "#f97316", "radius": 22},
    {"lat": 10.5, "lon": -84.0, "name": "Mesoamerica", "species_count": 17000, "cr_species": 440,
     "description": "Quetzal, spider monkeys, poison frogs. Biodiversity corridor.", "color": "#06b6d4", "radius": 19},
    {"lat": -16.5, "lon": -68.0, "name": "Tropical Andes", "species_count": 30000, "cr_species": 1200,
     "description": "Spectacled bear, Andean condor, chinchilla. World's richest biodiversity hotspot.", "color": "#a855f7", "radius": 23},
    {"lat": 11.0, "lon": 43.0, "name": "Horn of Africa", "species_count": 5000, "cr_species": 310,
     "description": "Somali wild ass, Walia ibex. High endemism in arid environment.", "color": "#94a3b8", "radius": 16},
    {"lat": 28.0, "lon": 86.0, "name": "Eastern Himalayas", "species_count": 10000, "cr_species": 450,
     "description": "Snow leopard, red panda, takin. Climate-vulnerable montane species.", "color": "#e879f9", "radius": 18},
    {"lat": -17.0, "lon": 25.0, "name": "Miombo-Mopane Woodlands", "species_count": 8500, "cr_species": 260,
     "description": "African wild dog, sable antelope. Vast dry woodland biome under pressure.", "color": "#fbbf24", "radius": 17},
    {"lat": 17.0, "lon": -88.5, "name": "Caribbean Islands", "species_count": 6500, "cr_species": 750,
     "description": "Hutia, solenodon, Cuban crocodile. Island endemics at extreme risk.", "color": "#fb923c", "radius": 18},
    {"lat": 25.0, "lon": 122.0, "name": "Taiwan / Philippines", "species_count": 9200, "cr_species": 550,
     "description": "Philippine eagle, tamaraw, tarsier. Island biodiversity under pressure.", "color": "#2dd4bf", "radius": 17},
]

# ═══════════════════════════════════════════════════════════════
# 8. INVASIVE SPECIES
# ═══════════════════════════════════════════════════════════════
INVASIVE_SPECIES = [
    {"name": "Cane Toad", "scientific": "Rhinella marina", "color": "#10b981",
     "origin": {"lat": -15.0, "lon": -55.0, "name": "Central/South America"},
     "invasions": [
         {"lat": -19.3, "lon": 146.8, "name": "Queensland, Australia", "year": 1935, "impact": "Devastating native predators through toxins"},
         {"lat": 21.3, "lon": -157.8, "name": "Hawaii, USA", "year": 1932, "impact": "Outcompetes native amphibians"},
         {"lat": 18.1, "lon": -66.0, "name": "Puerto Rico", "year": 1920, "impact": "Established throughout island"},
     ]},
    {"name": "European Rabbit", "scientific": "Oryctolagus cuniculus", "color": "#8b5cf6",
     "origin": {"lat": 39.0, "lon": -3.0, "name": "Iberian Peninsula"},
     "invasions": [
         {"lat": -33.8, "lon": 151.2, "name": "Australia", "year": 1859, "impact": "200+ million rabbits devastated ecosystems"},
         {"lat": -41.3, "lon": 174.8, "name": "New Zealand", "year": 1838, "impact": "Severe overgrazing of native vegetation"},
     ]},
    {"name": "Burmese Python", "scientific": "Python bivittatus", "color": "#f59e0b",
     "origin": {"lat": 16.0, "lon": 96.0, "name": "Southeast Asia"},
     "invasions": [
         {"lat": 25.8, "lon": -80.7, "name": "Everglades, Florida", "year": 1979, "impact": "Decimated 90% of small mammals in Everglades"},
     ]},
    {"name": "Brown Tree Snake", "scientific": "Boiga irregularis", "color": "#ef4444",
     "origin": {"lat": -6.0, "lon": 148.0, "name": "Papua New Guinea / N. Australia"},
     "invasions": [
         {"lat": 13.4, "lon": 144.8, "name": "Guam", "year": 1950, "impact": "Extirpated 10 of 12 native forest bird species"},
     ]},
    {"name": "Red Fox", "scientific": "Vulpes vulpes", "color": "#f97316",
     "origin": {"lat": 51.5, "lon": -0.1, "name": "Europe"},
     "invasions": [
         {"lat": -33.8, "lon": 151.2, "name": "Australia", "year": 1855, "impact": "Major predator of native marsupials and ground birds"},
     ]},
    {"name": "Asian Tiger Mosquito", "scientific": "Aedes albopictus", "color": "#94a3b8",
     "origin": {"lat": 35.7, "lon": 139.7, "name": "SE Asia / Japan"},
     "invasions": [
         {"lat": 30.0, "lon": -90.0, "name": "Southeastern USA", "year": 1985, "impact": "Disease vector (dengue, chikungunya, Zika)"},
         {"lat": 41.0, "lon": 12.0, "name": "Southern Europe", "year": 1990, "impact": "Rapidly expanding range with climate change"},
         {"lat": -23.5, "lon": -46.6, "name": "Brazil", "year": 1986, "impact": "Contributes to dengue outbreaks"},
     ]},
    {"name": "Lionfish", "scientific": "Pterois volitans", "color": "#ec4899",
     "origin": {"lat": -8.0, "lon": 115.0, "name": "Indo-Pacific"},
     "invasions": [
         {"lat": 24.5, "lon": -77.5, "name": "Caribbean Sea", "year": 1985, "impact": "Devours native reef fish, no natural predators"},
         {"lat": 30.3, "lon": -81.6, "name": "Atlantic coast, USA", "year": 1985, "impact": "Spreading along SE US coast"},
     ]},
    {"name": "Grey Squirrel", "scientific": "Sciurus carolinensis", "color": "#6b7280",
     "origin": {"lat": 40.0, "lon": -75.0, "name": "Eastern North America"},
     "invasions": [
         {"lat": 51.5, "lon": -0.1, "name": "United Kingdom", "year": 1876, "impact": "Displaced native red squirrels through competition & disease"},
         {"lat": 45.5, "lon": 9.2, "name": "Northern Italy", "year": 1948, "impact": "Threatening European red squirrel populations"},
     ]},
    {"name": "Common Starling", "scientific": "Sturnus vulgaris", "color": "#3b82f6",
     "origin": {"lat": 52.0, "lon": 5.0, "name": "Europe / Western Asia"},
     "invasions": [
         {"lat": 40.8, "lon": -74.0, "name": "New York, USA", "year": 1890, "impact": "200M birds; displaces native cavity-nesters"},
         {"lat": -33.8, "lon": 151.2, "name": "Australia", "year": 1857, "impact": "Agricultural pest and competitor to native birds"},
     ]},
    {"name": "Nile Perch", "scientific": "Lates niloticus", "color": "#06b6d4",
     "origin": {"lat": 7.0, "lon": 30.0, "name": "Nile/Congo basins"},
     "invasions": [
         {"lat": -1.0, "lon": 33.0, "name": "Lake Victoria, East Africa", "year": 1954, "impact": "Caused extinction of 200+ cichlid species"},
     ]},
]

# ═══════════════════════════════════════════════════════════════
# 9. DEEP SEA CREATURES
# ═══════════════════════════════════════════════════════════════
DEEP_SEA_SITES = [
    {"lat": 21.35, "lon": -109.1, "name": "East Pacific Rise (9N)", "depth_m": 2500,
     "type": "Hydrothermal Vent", "species": "Giant Tube Worm (Riftia pachyptila), Pompeii Worm", "color": "#ef4444"},
    {"lat": 47.95, "lon": -129.1, "name": "Juan de Fuca Ridge", "depth_m": 2200,
     "type": "Hydrothermal Vent", "species": "Ridgeia tube worms, vent crabs", "color": "#ef4444"},
    {"lat": 37.8, "lon": -32.3, "name": "Lucky Strike, Mid-Atlantic Ridge", "depth_m": 1700,
     "type": "Hydrothermal Vent", "species": "Vent mussels (Bathymodiolus azoricus), shrimp", "color": "#ef4444"},
    {"lat": 26.1, "lon": -44.8, "name": "TAG, Mid-Atlantic Ridge", "depth_m": 3600,
     "type": "Hydrothermal Vent", "species": "Rimicaris exoculata shrimp swarms", "color": "#ef4444"},
    {"lat": -38.0, "lon": 176.6, "name": "Brothers Volcano, Kermadec Arc", "depth_m": 1600,
     "type": "Hydrothermal Vent", "species": "Vent barnacles, Vulcanolepas", "color": "#ef4444"},
    {"lat": -15.0, "lon": -13.2, "name": "Ascension Fracture Zone", "depth_m": 3000,
     "type": "Hydrothermal Vent", "species": "Kiwa yeti crabs, stalked barnacles", "color": "#ef4444"},
    {"lat": 11.35, "lon": 142.2, "name": "Mariana Trench (Challenger Deep)", "depth_m": 10994,
     "type": "Trench", "species": "Snailfish, amphipods, xenophyophores", "color": "#3b82f6"},
    {"lat": -8.1, "lon": -79.8, "name": "Peru-Chile Trench (Atacama)", "depth_m": 8065,
     "type": "Trench", "species": "Atacama snailfish (Pseudoliparis swirei relative), amphipods", "color": "#3b82f6"},
    {"lat": 36.0, "lon": 142.0, "name": "Japan Trench", "depth_m": 8400,
     "type": "Trench", "species": "Deep-sea fish, giant isopods", "color": "#3b82f6"},
    {"lat": -10.8, "lon": -162.5, "name": "Tonga Trench", "depth_m": 10882,
     "type": "Trench", "species": "Supergiant amphipods, snailfish", "color": "#3b82f6"},
    {"lat": 26.7, "lon": 127.3, "name": "Ryukyu Trench", "depth_m": 7460,
     "type": "Trench", "species": "Giant isopods (Bathynomus giganteus)", "color": "#3b82f6"},
    {"lat": -52.0, "lon": -24.0, "name": "South Sandwich Trench", "depth_m": 8428,
     "type": "Trench", "species": "Deep-sea octopus, cold-adapted amphipods", "color": "#3b82f6"},
    {"lat": 27.0, "lon": -91.0, "name": "Gulf of Mexico Cold Seeps", "depth_m": 2000,
     "type": "Cold Seep", "species": "Tube worms (Lamellibrachia), ice worms, chemosynthetic mussels", "color": "#10b981"},
    {"lat": 44.6, "lon": -125.1, "name": "Hydrate Ridge, Oregon", "depth_m": 800,
     "type": "Cold Seep", "species": "Calyptogena clams, bacterial mats", "color": "#10b981"},
    {"lat": 65.0, "lon": -28.0, "name": "Arctic Mid-Ocean Ridge", "depth_m": 2400,
     "type": "Hydrothermal Vent", "species": "White microbes, specialized vent fauna at extreme latitude", "color": "#ef4444"},
    {"lat": -0.3, "lon": 29.6, "name": "Lake Kivu Depths", "depth_m": 480,
     "type": "Meromictic Lake", "species": "Unique deep-lake endemic cichlids", "color": "#8b5cf6"},
    {"lat": 51.9, "lon": 105.0, "name": "Lake Baikal Deep", "depth_m": 1642,
     "type": "Deep Lake", "species": "Baikal oilfish (Comephorus), endemic amphipods, Baikal seal", "color": "#8b5cf6"},
    {"lat": -15.5, "lon": 65.5, "name": "Saya de Malha Bank, Indian Ocean", "depth_m": 3500,
     "type": "Deep Seamount", "species": "Deep corals, glass sponges, crinoids", "color": "#f59e0b"},
    {"lat": 30.0, "lon": -28.5, "name": "Azores Seamounts", "depth_m": 2500,
     "type": "Deep Seamount", "species": "Deep-sea corals, orange roughy, grenadiers", "color": "#f59e0b"},
    {"lat": -56.0, "lon": -27.0, "name": "South Georgia Deep", "depth_m": 4000,
     "type": "Deep Basin", "species": "Giant sea spiders, colossal squid territory", "color": "#a855f7"},
    {"lat": -60.0, "lon": 0.0, "name": "Southern Ocean Abyss", "depth_m": 5000,
     "type": "Abyssal Plain", "species": "Giant Antarctic isopods, glass sponges, deep sea worms", "color": "#a855f7"},
]

# ═══════════════════════════════════════════════════════════════
# 10. EXTINCT SPECIES LAST LOCATIONS
# ═══════════════════════════════════════════════════════════════
EXTINCT_SPECIES = [
    {"name": "Dodo", "scientific": "Raphus cucullatus", "lat": -20.2, "lon": 57.5,
     "location": "Mauritius", "last_seen": "1662", "cause": "Hunting, invasive species", "color": "#8b5cf6"},
    {"name": "Thylacine (Tasmanian Tiger)", "scientific": "Thylacinus cynocephalus", "lat": -42.9, "lon": 147.3,
     "location": "Hobart Zoo, Tasmania", "last_seen": "1936", "cause": "Hunting, habitat loss, disease", "color": "#f59e0b"},
    {"name": "Passenger Pigeon", "scientific": "Ectopistes migratorius", "lat": 39.1, "lon": -84.5,
     "location": "Cincinnati Zoo, Ohio", "last_seen": "1914 (Martha)", "cause": "Overhunting, habitat destruction", "color": "#3b82f6"},
    {"name": "Quagga", "scientific": "Equus quagga quagga", "lat": -33.9, "lon": 18.4,
     "location": "Amsterdam Zoo (last captive); Cape Colony (wild)", "last_seen": "1883", "cause": "Overhunting by settlers", "color": "#a0522d"},
    {"name": "Great Auk", "scientific": "Pinguinus impennis", "lat": 63.8, "lon": -23.0,
     "location": "Eldey Island, Iceland", "last_seen": "1844", "cause": "Overhunting for feathers and specimens", "color": "#1e3a5f"},
    {"name": "Steller's Sea Cow", "scientific": "Hydrodamalis gigas", "lat": 55.2, "lon": 166.0,
     "location": "Commander Islands, Russia", "last_seen": "1768", "cause": "Overhunting within 27 years of discovery", "color": "#06b6d4"},
    {"name": "Woolly Mammoth", "scientific": "Mammuthus primigenius", "lat": 71.0, "lon": 179.0,
     "location": "Wrangel Island, Russia", "last_seen": "~2000 BCE", "cause": "Climate change, human hunting", "color": "#94a3b8"},
    {"name": "Moa", "scientific": "Dinornis robustus", "lat": -44.0, "lon": 170.0,
     "location": "South Island, New Zealand", "last_seen": "~1440", "cause": "Hunting by Maori", "color": "#10b981"},
    {"name": "Baiji (Yangtze River Dolphin)", "scientific": "Lipotes vexillifer", "lat": 30.6, "lon": 114.3,
     "location": "Yangtze River, Wuhan, China", "last_seen": "2002", "cause": "Pollution, boat traffic, dams", "color": "#3b82f6"},
    {"name": "Western Black Rhinoceros", "scientific": "Diceros bicornis longipes", "lat": 7.0, "lon": 15.0,
     "location": "Northern Cameroon", "last_seen": "2006 (declared extinct 2011)", "cause": "Poaching for horn", "color": "#6b7280"},
    {"name": "Pyrenean Ibex", "scientific": "Capra pyrenaica pyrenaica", "lat": 42.7, "lon": -0.1,
     "location": "Ordesa NP, Spain", "last_seen": "2000 (Celia)", "cause": "Hunting, competition, disease", "color": "#a0522d"},
    {"name": "Caribbean Monk Seal", "scientific": "Neomonachus tropicalis", "lat": 18.2, "lon": -65.6,
     "location": "Serranilla Bank, Caribbean", "last_seen": "1952", "cause": "Hunting, overfishing", "color": "#06b6d4"},
    {"name": "Javan Tiger", "scientific": "Panthera tigris sondaica", "lat": -8.1, "lon": 114.4,
     "location": "Meru Betiri NP, Java", "last_seen": "1976", "cause": "Habitat loss, hunting", "color": "#ef4444"},
    {"name": "Caspian Tiger", "scientific": "Panthera tigris virgata", "lat": 37.5, "lon": 59.0,
     "location": "Turkmenistan/Iran border", "last_seen": "1970s", "cause": "Hunting, habitat destruction", "color": "#f97316"},
    {"name": "Tecopa Pupfish", "scientific": "Cyprinodon nevadensis calidae", "lat": 35.9, "lon": -116.2,
     "location": "Tecopa Hot Springs, California", "last_seen": "1970 (first US ESA extinction)", "cause": "Habitat modification, hot spring diversion", "color": "#ec4899"},
    {"name": "Ivory-billed Woodpecker", "scientific": "Campephilus principalis", "lat": 34.1, "lon": -91.9,
     "location": "Singer Tract, Louisiana (contested AR sighting 2004)", "last_seen": "1944 (confirmed)", "cause": "Logging of old-growth bottomland forest", "color": "#dc2626"},
    {"name": "Golden Toad", "scientific": "Incilius periglenes", "lat": 10.3, "lon": -84.8,
     "location": "Monteverde Cloud Forest, Costa Rica", "last_seen": "1989", "cause": "Chytrid fungus, climate change", "color": "#f59e0b"},
    {"name": "Formosan Clouded Leopard", "scientific": "Neofelis nebulosa brachyura", "lat": 23.5, "lon": 120.9,
     "location": "Central Mountains, Taiwan", "last_seen": "1983 (declared extinct 2013)", "cause": "Hunting, deforestation", "color": "#a855f7"},
    {"name": "Bramble Cay Melomys", "scientific": "Melomys rubicola", "lat": -9.1, "lon": 143.9,
     "location": "Bramble Cay, Torres Strait", "last_seen": "2009 (declared extinct 2019)", "cause": "Sea level rise (first mammalian climate extinction)", "color": "#06b6d4"},
    {"name": "Pinta Island Tortoise", "scientific": "Chelonoidis abingdonii", "lat": 0.6, "lon": -90.8,
     "location": "Pinta Island, Galapagos", "last_seen": "2012 (Lonesome George)", "cause": "Hunting, invasive goats", "color": "#10b981"},
    {"name": "Spix's Macaw", "scientific": "Cyanopsitta spixii", "lat": -9.6, "lon": -39.1,
     "location": "Curaca, Bahia, Brazil", "last_seen": "2000 (wild; captive reintro ongoing)", "cause": "Trapping, habitat loss", "color": "#3b82f6"},
    {"name": "Zanzibar Leopard", "scientific": "Panthera pardus adersi", "lat": -6.2, "lon": 39.3,
     "location": "Unguja Island, Zanzibar", "last_seen": "1996 (possibly later)", "cause": "Persecution as 'witchcraft' animals, habitat loss", "color": "#6b7280"},
    {"name": "Japanese River Otter", "scientific": "Lutra nippon", "lat": 33.3, "lon": 133.0,
     "location": "Shinjo River, Kochi, Japan", "last_seen": "1979 (declared extinct 2012)", "cause": "Hunting, pollution, habitat loss", "color": "#8b5cf6"},
    {"name": "Chinese Paddlefish", "scientific": "Psephurus gladius", "lat": 30.7, "lon": 111.3,
     "location": "Yangtze River, China", "last_seen": "2003 (declared extinct 2020)", "cause": "Overfishing, Gezhouba Dam", "color": "#f97316"},
    {"name": "Splendid Poison Frog", "scientific": "Oophaga speciosa", "lat": 8.5, "lon": -79.5,
     "location": "Western Panama", "last_seen": "1923", "cause": "Habitat destruction, chytrid fungus suspected", "color": "#ec4899"},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _make_base_map(center=None, zoom=2):
    """Create a dark-themed Folium map."""
    if center is None:
        center = [20.0, 0.0]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _safe(text):
    """Escape text for safe HTML popup content."""
    if text is None:
        return ""
    return escape(str(text))


def _popup_html(title, rows):
    """Build a styled popup HTML block."""
    html = (
        f'<div style="font-family:Inter,system-ui,sans-serif;min-width:220px;'
        f'background:{SURFACE_COLOR};color:{TEXT_COLOR};padding:10px;border-radius:8px;'
        f'border:1px solid #2a3550;">'
        f'<b style="color:{ACCENT_COLOR};font-size:13px;">{_safe(title)}</b><br>'
    )
    for label, value in rows:
        html += (
            f'<span style="color:{SECONDARY_TEXT};font-size:11px;">{_safe(label)}:</span> '
            f'<span style="font-size:11px;">{_safe(value)}</span><br>'
        )
    html += "</div>"
    return html


def _stat_card(label, value, icon=""):
    """Render a small metric-like card."""
    st.markdown(
        f'<div style="background:{SURFACE_COLOR};border:1px solid #2a3550;border-radius:8px;'
        f'padding:12px 16px;text-align:center;">'
        f'<div style="color:{SECONDARY_TEXT};font-size:11px;">{icon} {_safe(label)}</div>'
        f'<div style="color:{ACCENT_COLOR};font-size:20px;font-weight:700;">{_safe(str(value))}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
# CACHED DATA BUILDERS
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _build_zoogeographic_df():
    rows = []
    for name, info in ZOOGEOGRAPHIC_REALMS.items():
        rows.append({
            "Realm": name,
            "Area": info["area_km2"],
            "Lat": info["center"][0],
            "Lon": info["center"][1],
            "Characteristic Species": ", ".join(info["characteristic_species"][:3]),
            "Description": info["description"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_big_cats_df():
    rows = []
    for name, info in BIG_CATS.items():
        for pt in info["range_points"]:
            rows.append({
                "Species": name,
                "Scientific Name": info["scientific"],
                "IUCN Status": info["status"],
                "Est. Population": info["population"],
                "Location": pt["name"],
                "Lat": pt["lat"],
                "Lon": pt["lon"],
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_primates_df():
    rows = []
    for name, info in PRIMATES.items():
        for loc in info["locations"]:
            rows.append({
                "Species": name,
                "Scientific Name": info["scientific"],
                "IUCN Status": info["status"],
                "Est. Population": info["population"],
                "Location": loc["name"],
                "Lat": loc["lat"],
                "Lon": loc["lon"],
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_marine_df():
    rows = []
    for name, info in WHALE_ROUTES.items():
        rows.append({"Category": "Whale Route", "Name": name, "Description": info["description"]})
    for s in SHARK_HOTSPOTS:
        rows.append({"Category": "Shark Hotspot", "Name": s["species"], "Description": s["name"]})
    for t in SEA_TURTLE_NESTING:
        rows.append({"Category": "Turtle Nesting", "Name": t["species"], "Description": f"{t['name']} (~{t['nests_yr']} nests/yr)"})
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_marsupial_df():
    rows = []
    for name, info in MARSUPIALS.items():
        for loc in info["locations"]:
            rows.append({
                "Species": name,
                "Scientific Name": info["scientific"],
                "IUCN Status": info["status"],
                "Population": info["population"],
                "Location": loc["name"],
                "Lat": loc["lat"],
                "Lon": loc["lon"],
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_flyways_df():
    rows = []
    for name, info in FLYWAYS.items():
        rows.append({
            "Flyway": name,
            "Key Species": info["key_species"],
            "Description": info["description"],
            "Waypoints": len(info["route"]),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_endangered_df():
    rows = []
    for h in ENDANGERED_HOTSPOTS:
        rows.append({
            "Hotspot": h["name"],
            "Total Species": h["species_count"],
            "Critically Endangered": h["cr_species"],
            "Description": h["description"],
            "Lat": h["lat"],
            "Lon": h["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_invasive_df():
    rows = []
    for sp in INVASIVE_SPECIES:
        for inv in sp["invasions"]:
            rows.append({
                "Species": sp["name"],
                "Scientific Name": sp["scientific"],
                "Origin": sp["origin"]["name"],
                "Invasion Site": inv["name"],
                "Year": inv["year"],
                "Impact": inv["impact"],
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_deep_sea_df():
    rows = []
    for s in DEEP_SEA_SITES:
        rows.append({
            "Site": s["name"],
            "Type": s["type"],
            "Depth (m)": s["depth_m"],
            "Notable Species": s["species"],
            "Lat": s["lat"],
            "Lon": s["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_extinct_df():
    rows = []
    for sp in EXTINCT_SPECIES:
        rows.append({
            "Species": sp["name"],
            "Scientific Name": sp["scientific"],
            "Location": sp["location"],
            "Last Seen": sp["last_seen"],
            "Cause": sp["cause"],
            "Lat": sp["lat"],
            "Lon": sp["lon"],
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
# MAP RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_zoogeographic_map():
    """Render zoogeographic realms map."""
    m = _make_base_map(zoom=2)
    for name, info in ZOOGEOGRAPHIC_REALMS.items():
        bounds = info["bounds"]
        folium.Polygon(
            locations=bounds,
            color=info["color"],
            fill=True,
            fill_color=info["color"],
            fill_opacity=0.15,
            weight=2,
            popup=folium.Popup(
                _popup_html(name, [
                    ("Area", info["area_km2"] + " km2"),
                    ("Key fauna", ", ".join(info["characteristic_species"][:3])),
                    ("Info", info["description"][:120]),
                ]),
                max_width=300,
            ),
        ).add_to(m)
        folium.Marker(
            location=info["center"],
            popup=folium.Popup(
                _popup_html(f"{name} Realm", [
                    ("Area", info["area_km2"] + " km2"),
                    ("Species", ", ".join(info["characteristic_species"])),
                    ("Description", info["description"]),
                ]),
                max_width=320,
            ),
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px;font-weight:bold;color:{info["color"]};'
                     f'text-shadow:0 0 3px #000,0 0 6px #000;">{_safe(name)}</div>',
            ),
        ).add_to(m)
    return m


def _render_big_cats_map():
    """Render big cats distribution map."""
    m = _make_base_map(center=[20.0, 50.0], zoom=3)
    for name, info in BIG_CATS.items():
        fg = folium.FeatureGroup(name=name)
        for pt in info["range_points"]:
            folium.CircleMarker(
                location=[pt["lat"], pt["lon"]],
                radius=9,
                color=info["color"],
                fill=True,
                fill_color=info["color"],
                fill_opacity=0.7,
                popup=folium.Popup(
                    _popup_html(name, [
                        ("Scientific", info["scientific"]),
                        ("Status", info["status"]),
                        ("Population", info["population"]),
                        ("Location", pt["name"]),
                    ]),
                    max_width=280,
                ),
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _render_primates_map():
    """Render great apes and primates map."""
    m = _make_base_map(center=[0.0, 60.0], zoom=3)
    for name, info in PRIMATES.items():
        fg = folium.FeatureGroup(name=name)
        for loc in info["locations"]:
            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=10,
                color=info["color"],
                fill=True,
                fill_color=info["color"],
                fill_opacity=0.7,
                popup=folium.Popup(
                    _popup_html(name, [
                        ("Scientific", info["scientific"]),
                        ("IUCN Status", info["status"]),
                        ("Population", info["population"]),
                        ("Habitat", loc["name"]),
                    ]),
                    max_width=280,
                ),
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _render_marine_map():
    """Render marine megafauna map."""
    m = _make_base_map(zoom=2)

    # Whale migration routes
    whale_fg = folium.FeatureGroup(name="Whale Migration Routes")
    for name, info in WHALE_ROUTES.items():
        folium.PolyLine(
            locations=info["route"],
            color=info["color"],
            weight=3,
            opacity=0.8,
            dash_array="10 6",
            popup=folium.Popup(
                _popup_html(name, [("Route", info["description"])]),
                max_width=280,
            ),
        ).add_to(whale_fg)
        # Start marker
        folium.CircleMarker(
            location=info["route"][0],
            radius=6,
            color=info["color"],
            fill=True,
            fill_color=info["color"],
            fill_opacity=0.9,
        ).add_to(whale_fg)
    whale_fg.add_to(m)

    # Shark hotspots
    shark_fg = folium.FeatureGroup(name="Shark Hotspots")
    for s in SHARK_HOTSPOTS:
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=s["color"],
            fill=True,
            fill_color=s["color"],
            fill_opacity=0.7,
            popup=folium.Popup(
                _popup_html(s["species"], [("Location", s["name"])]),
                max_width=250,
            ),
        ).add_to(shark_fg)
    shark_fg.add_to(m)

    # Sea turtle nesting
    turtle_fg = folium.FeatureGroup(name="Sea Turtle Nesting Sites")
    for t in SEA_TURTLE_NESTING:
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=8,
            color=t["color"],
            fill=True,
            fill_color=t["color"],
            fill_opacity=0.7,
            popup=folium.Popup(
                _popup_html(t["species"], [
                    ("Site", t["name"]),
                    ("Nests/Year", t["nests_yr"]),
                ]),
                max_width=250,
            ),
        ).add_to(turtle_fg)
    turtle_fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _render_marsupial_map():
    """Render marsupial distribution map."""
    m = _make_base_map(center=[-15.0, 135.0], zoom=3)
    for name, info in MARSUPIALS.items():
        fg = folium.FeatureGroup(name=name)
        for loc in info["locations"]:
            folium.CircleMarker(
                location=[loc["lat"], loc["lon"]],
                radius=9,
                color=info["color"],
                fill=True,
                fill_color=info["color"],
                fill_opacity=0.7,
                popup=folium.Popup(
                    _popup_html(name, [
                        ("Scientific", info["scientific"]),
                        ("IUCN Status", info["status"]),
                        ("Population", info["population"]),
                        ("Location", loc["name"]),
                    ]),
                    max_width=280,
                ),
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _render_flyways_map():
    """Render bird migration flyways map."""
    m = _make_base_map(zoom=2)
    for name, info in FLYWAYS.items():
        fg = folium.FeatureGroup(name=name)
        folium.PolyLine(
            locations=info["route"],
            color=info["color"],
            weight=4,
            opacity=0.8,
            popup=folium.Popup(
                _popup_html(name, [
                    ("Key Species", info["key_species"]),
                    ("Description", info["description"]),
                ]),
                max_width=300,
            ),
        ).add_to(fg)
        # Arrow markers at midpoints
        mid_idx = len(info["route"]) // 2
        folium.Marker(
            location=info["route"][mid_idx],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:{info["color"]};'
                     f'text-shadow:0 0 3px #000;white-space:nowrap;">{_safe(name)}</div>',
            ),
        ).add_to(fg)
        # Start and end markers
        for idx, label in [(0, "Start"), (-1, "End")]:
            folium.CircleMarker(
                location=info["route"][idx],
                radius=5,
                color=info["color"],
                fill=True,
                fill_color=info["color"],
                fill_opacity=0.9,
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _render_endangered_map():
    """Render endangered species hotspots map."""
    m = _make_base_map(zoom=2)
    for h in ENDANGERED_HOTSPOTS:
        folium.CircleMarker(
            location=[h["lat"], h["lon"]],
            radius=h["radius"],
            color=h["color"],
            fill=True,
            fill_color=h["color"],
            fill_opacity=0.35,
            weight=2,
            popup=folium.Popup(
                _popup_html(h["name"], [
                    ("Total Species", f"{h['species_count']:,}"),
                    ("Critically Endangered", f"{h['cr_species']:,}"),
                    ("Details", h["description"]),
                ]),
                max_width=300,
            ),
        ).add_to(m)
        folium.Marker(
            location=[h["lat"], h["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;font-weight:bold;color:{h["color"]};'
                     f'text-shadow:0 0 3px #000;white-space:nowrap;">'
                     f'{_safe(h["name"])} ({h["cr_species"]} CR)</div>',
            ),
        ).add_to(m)
    return m


def _render_invasive_map():
    """Render invasive species map."""
    m = _make_base_map(zoom=2)
    for sp in INVASIVE_SPECIES:
        fg = folium.FeatureGroup(name=sp["name"])
        # Origin marker
        org = sp["origin"]
        folium.Marker(
            location=[org["lat"], org["lon"]],
            icon=folium.Icon(color="green", icon="home", prefix="fa"),
            popup=folium.Popup(
                _popup_html(f"{sp['name']} (Origin)", [
                    ("Scientific", sp["scientific"]),
                    ("Native Range", org["name"]),
                ]),
                max_width=260,
            ),
        ).add_to(fg)
        # Invasion sites
        for inv in sp["invasions"]:
            folium.CircleMarker(
                location=[inv["lat"], inv["lon"]],
                radius=9,
                color=sp["color"],
                fill=True,
                fill_color=sp["color"],
                fill_opacity=0.7,
                popup=folium.Popup(
                    _popup_html(f"{sp['name']} - Invasion", [
                        ("Scientific", sp["scientific"]),
                        ("Site", inv["name"]),
                        ("Year", str(inv["year"])),
                        ("Impact", inv["impact"]),
                    ]),
                    max_width=300,
                ),
            ).add_to(fg)
            # Line from origin to invasion
            folium.PolyLine(
                locations=[[org["lat"], org["lon"]], [inv["lat"], inv["lon"]]],
                color=sp["color"],
                weight=2,
                opacity=0.5,
                dash_array="8 4",
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _render_deep_sea_map():
    """Render deep sea creatures map."""
    m = _make_base_map(zoom=2)
    type_colors = {
        "Hydrothermal Vent": "#ef4444",
        "Trench": "#3b82f6",
        "Cold Seep": "#10b981",
        "Deep Seamount": "#f59e0b",
        "Deep Lake": "#8b5cf6",
        "Meromictic Lake": "#8b5cf6",
        "Deep Basin": "#a855f7",
        "Abyssal Plain": "#a855f7",
    }
    for site_type in set(s["type"] for s in DEEP_SEA_SITES):
        fg = folium.FeatureGroup(name=site_type)
        for s in DEEP_SEA_SITES:
            if s["type"] != site_type:
                continue
            color = type_colors.get(s["type"], "#94a3b8")
            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(
                    _popup_html(s["name"], [
                        ("Type", s["type"]),
                        ("Depth", f"{s['depth_m']:,} m"),
                        ("Species", s["species"]),
                    ]),
                    max_width=300,
                ),
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _render_extinct_map():
    """Render extinct species last locations map."""
    m = _make_base_map(zoom=2)
    for sp in EXTINCT_SPECIES:
        folium.Marker(
            location=[sp["lat"], sp["lon"]],
            icon=folium.Icon(color="black", icon="times-circle", prefix="fa"),
            popup=folium.Popup(
                _popup_html(sp["name"], [
                    ("Scientific", sp["scientific"]),
                    ("Location", sp["location"]),
                    ("Last Seen", sp["last_seen"]),
                    ("Cause", sp["cause"]),
                ]),
                max_width=300,
            ),
        ).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════
# CHART RENDERERS
# ═══════════════════════════════════════════════════════════════

def _chart_big_cats_population():
    """Bar chart of big cat estimated populations."""
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    names = []
    pops = []
    colors = []
    for name, info in BIG_CATS.items():
        names.append(name)
        pop_str = info["population"].replace("~", "").replace(",", "").split("(")[0].split("-")[0].strip()
        try:
            pops.append(int(pop_str))
        except ValueError:
            pops.append(0)
        colors.append(info["color"])

    bars = ax.barh(names, pops, color=colors, edgecolor="#2a3550", linewidth=0.5)
    ax.set_xlabel("Estimated Population", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Big Cat Population Estimates", color=TEXT_COLOR, fontsize=13, fontweight="bold")
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.xaxis.label.set_color(TEXT_COLOR)

    for bar, pop in zip(bars, pops):
        ax.text(bar.get_width() + max(pops) * 0.02, bar.get_y() + bar.get_height() / 2,
                f"{pop:,}", va="center", ha="left", color=TEXT_COLOR, fontsize=9)

    plt.tight_layout()
    return fig


def _chart_endangered_hotspots():
    """Horizontal bar chart of critically endangered species by hotspot."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    sorted_hs = sorted(ENDANGERED_HOTSPOTS, key=lambda x: x["cr_species"])
    names = [h["name"] for h in sorted_hs]
    counts = [h["cr_species"] for h in sorted_hs]
    colors = [h["color"] for h in sorted_hs]

    bars = ax.barh(names, counts, color=colors, edgecolor="#2a3550", linewidth=0.5)
    ax.set_xlabel("Critically Endangered Species", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Endangered Species Hotspots", color=TEXT_COLOR, fontsize=13, fontweight="bold")
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")

    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.02, bar.get_y() + bar.get_height() / 2,
                f"{cnt:,}", va="center", ha="left", color=TEXT_COLOR, fontsize=8)

    plt.tight_layout()
    return fig


def _chart_extinct_timeline():
    """Scatter plot of extinct species by approximate year."""
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    items = []
    for sp in EXTINCT_SPECIES:
        raw = sp["last_seen"]
        # Parse year from various formats
        year = None
        for token in raw.replace("(", " ").replace(")", " ").replace("~", "").split():
            try:
                y = int(token)
                if 1000 <= y <= 2100:
                    year = y
                    break
            except ValueError:
                continue
        if "BCE" in raw:
            year = -2000
        if year is not None:
            items.append((year, sp["name"], sp["color"]))

    if items:
        items.sort(key=lambda x: x[0])
        years = [i[0] for i in items]
        names = [i[1] for i in items]
        colors = [i[2] for i in items]

        ax.scatter(years, range(len(years)), c=colors, s=60, zorder=5, edgecolors="#2a3550", linewidth=0.5)
        for idx, (yr, nm, _) in enumerate(items):
            ax.text(yr + 8, idx, nm, color=TEXT_COLOR, fontsize=7, va="center")

        ax.set_xlabel("Year of Last Sighting", color=TEXT_COLOR, fontsize=10)
        ax.set_title("Extinct Species Timeline", color=TEXT_COLOR, fontsize=13, fontweight="bold")
        ax.set_yticks([])
        ax.tick_params(colors=TEXT_COLOR, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")
        ax.axvline(x=1900, color="#ef4444", linestyle="--", alpha=0.4, linewidth=1)
        ax.text(1902, len(items) - 1, "1900", color="#ef4444", fontsize=8, alpha=0.6)

    plt.tight_layout()
    return fig


def _chart_deep_sea_depths():
    """Bar chart of deep sea site depths."""
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    sorted_sites = sorted(DEEP_SEA_SITES, key=lambda x: x["depth_m"], reverse=True)[:15]
    names = [s["name"][:30] for s in sorted_sites]
    depths = [s["depth_m"] for s in sorted_sites]
    colors = [s["color"] for s in sorted_sites]

    bars = ax.barh(names, depths, color=colors, edgecolor="#2a3550", linewidth=0.5)
    ax.set_xlabel("Depth (meters)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Deepest Sites", color=TEXT_COLOR, fontsize=13, fontweight="bold")
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.invert_xaxis()
    for spine in ax.spines.values():
        spine.set_color("#2a3550")

    for bar, d in zip(bars, depths):
        ax.text(bar.get_width() - max(depths) * 0.02, bar.get_y() + bar.get_height() / 2,
                f"{d:,}m", va="center", ha="right", color=TEXT_COLOR, fontsize=8)

    plt.tight_layout()
    return fig


def _chart_invasive_timeline():
    """Bar chart: number of invasive introductions by decade."""
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    decades = {}
    for sp in INVASIVE_SPECIES:
        for inv in sp["invasions"]:
            dec = (inv["year"] // 10) * 10
            decades[dec] = decades.get(dec, 0) + 1

    if decades:
        sorted_dec = sorted(decades.items())
        xs = [str(d[0]) + "s" for d in sorted_dec]
        ys = [d[1] for d in sorted_dec]
        ax.bar(xs, ys, color=ACCENT_COLOR, edgecolor="#2a3550", linewidth=0.5)
        ax.set_ylabel("Introductions", color=TEXT_COLOR, fontsize=10)
        ax.set_title("Invasive Species Introductions by Decade", color=TEXT_COLOR, fontsize=13, fontweight="bold")
        ax.tick_params(colors=TEXT_COLOR, labelsize=9, axis="both")
        plt.xticks(rotation=45, ha="right")
        for spine in ax.spines.values():
            spine.set_color("#2a3550")

    plt.tight_layout()
    return fig


def _chart_primate_status():
    """Pie chart of primate IUCN status distribution."""
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor(BG_COLOR)

    status_counts = {}
    for info in PRIMATES.values():
        s = info["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    status_colors = {
        "Critically Endangered": "#ef4444",
        "Endangered": "#f97316",
        "Vulnerable": "#f59e0b",
        "Near Threatened": "#10b981",
        "Least Concern": "#3b82f6",
    }
    labels = list(status_counts.keys())
    sizes = list(status_counts.values())
    colors = [status_colors.get(l, "#94a3b8") for l in labels]

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        textprops={"color": TEXT_COLOR, "fontsize": 9},
        pctdistance=0.75, startangle=140,
    )
    for t in autotexts:
        t.set_color(TEXT_COLOR)
        t.set_fontsize(9)
    ax.set_title("Primate IUCN Status", color=TEXT_COLOR, fontsize=13, fontweight="bold")
    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_animal_maps_tab():
    """Render the Animal Distribution Maps tab for TerraScout AI."""

    st.markdown(
        '<div class="tab-header emerald"><h4>\U0001f981 Animal Distribution Maps</h4>'
        '<p>Wildlife distribution, endangered species, migration routes & zoogeography</p></div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.radio(
        "Select map mode",
        [
            "Zoogeographic Realms",
            "Big Cats Distribution",
            "Great Apes & Primates",
            "Marine Megafauna",
            "Marsupial Distribution",
            "Bird Migration Flyways",
            "Endangered Species Hotspots",
            "Invasive Species",
            "Deep Sea Creatures",
            "Extinct Species Last Locations",
        ],
        horizontal=True,
        key="animal_map_mode",
    )

    st.markdown("---")

    # ════════════════════════════════════════════════════════════
    # 1. ZOOGEOGRAPHIC REALMS
    # ════════════════════════════════════════════════════════════
    if mode == "Zoogeographic Realms":
        st.subheader("Zoogeographic Realms of the World")
        st.caption(
            "The eight major biogeographic realms, each with distinctive fauna shaped "
            "by continental drift, climate, and evolutionary history."
        )

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _stat_card("Realms", len(ZOOGEOGRAPHIC_REALMS), "🌍")
        with c2:
            total_sp = sum(len(r["characteristic_species"]) for r in ZOOGEOGRAPHIC_REALMS.values())
            _stat_card("Listed Species", total_sp, "🦎")
        with c3:
            _stat_card("Largest", "Palearctic", "📏")
        with c4:
            _stat_card("Most Biodiverse", "Neotropic", "🌿")

        # Map
        m = _render_zoogeographic_map()
        components.html(m._repr_html_(), height=500)

        # Legend
        st.markdown("**Realm Colors:**")
        legend_cols = st.columns(4)
        for idx, (name, info) in enumerate(ZOOGEOGRAPHIC_REALMS.items()):
            with legend_cols[idx % 4]:
                st.markdown(
                    f'<span style="color:{info["color"]};font-weight:bold;">&#9632;</span> {_safe(name)}',
                    unsafe_allow_html=True,
                )

        # Data table
        df = _build_zoogeographic_df()
        st.dataframe(df, width="stretch")

        # Download
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "zoogeographic_realms.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 2. BIG CATS DISTRIBUTION
    # ════════════════════════════════════════════════════════════
    elif mode == "Big Cats Distribution":
        st.subheader("Big Cats of the World")
        st.caption(
            "Distribution of the six major big cat species with population estimates and IUCN status."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            _stat_card("Species", len(BIG_CATS), "🐾")
        with c2:
            total_pts = sum(len(info["range_points"]) for info in BIG_CATS.values())
            _stat_card("Range Points", total_pts, "📍")
        with c3:
            endangered = sum(1 for info in BIG_CATS.values() if info["status"] in ("Endangered", "Critically Endangered"))
            _stat_card("Endangered/CR", endangered, "⚠️")

        m = _render_big_cats_map()
        components.html(m._repr_html_(), height=500)

        # Legend
        st.markdown("**Species Colors:**")
        leg_cols = st.columns(3)
        for idx, (name, info) in enumerate(BIG_CATS.items()):
            with leg_cols[idx % 3]:
                st.markdown(
                    f'<span style="color:{info["color"]};font-weight:bold;">&#9679;</span> '
                    f'{_safe(name)} ({_safe(info["status"])})',
                    unsafe_allow_html=True,
                )

        # Chart
        fig = _chart_big_cats_population()
        st.pyplot(fig)
        plt.close(fig)

        # Data table
        df = _build_big_cats_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "big_cats_distribution.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 3. GREAT APES & PRIMATES
    # ════════════════════════════════════════════════════════════
    elif mode == "Great Apes & Primates":
        st.subheader("Great Apes & Primates")
        st.caption(
            "Habitat locations and conservation status of gorillas, chimpanzees, orangutans, "
            "gibbons, bonobos, and lemurs."
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _stat_card("Species", len(PRIMATES), "🐒")
        with c2:
            total_locs = sum(len(info["locations"]) for info in PRIMATES.values())
            _stat_card("Habitats", total_locs, "🌳")
        with c3:
            cr = sum(1 for info in PRIMATES.values() if info["status"] == "Critically Endangered")
            _stat_card("Critically Endangered", cr, "🔴")
        with c4:
            en = sum(1 for info in PRIMATES.values() if info["status"] == "Endangered")
            _stat_card("Endangered", en, "🟠")

        m = _render_primates_map()
        components.html(m._repr_html_(), height=500)

        # Status pie chart
        col_chart, col_legend = st.columns([1, 1])
        with col_chart:
            fig = _chart_primate_status()
            st.pyplot(fig)
            plt.close(fig)
        with col_legend:
            st.markdown("**Species List:**")
            for name, info in PRIMATES.items():
                status_emoji = {"Critically Endangered": "🔴", "Endangered": "🟠",
                                "Vulnerable": "🟡", "Near Threatened": "🟢", "Least Concern": "🔵"}.get(info["status"], "⚪")
                st.markdown(
                    f'{status_emoji} **{_safe(name)}** (*{_safe(info["scientific"])}*) '
                    f'- {_safe(info["status"])} - Pop: {_safe(info["population"])}',
                    unsafe_allow_html=True,
                )

        df = _build_primates_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "primates_distribution.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 4. MARINE MEGAFAUNA
    # ════════════════════════════════════════════════════════════
    elif mode == "Marine Megafauna":
        st.subheader("Marine Megafauna")
        st.caption(
            "Whale migration routes, shark hotspots, and sea turtle nesting sites across the world's oceans."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            _stat_card("Whale Routes", len(WHALE_ROUTES), "🐋")
        with c2:
            _stat_card("Shark Hotspots", len(SHARK_HOTSPOTS), "🦈")
        with c3:
            _stat_card("Turtle Nesting Sites", len(SEA_TURTLE_NESTING), "🐢")

        m = _render_marine_map()
        components.html(m._repr_html_(), height=500)

        # Sub-sections
        st.markdown("#### Whale Migration Routes")
        for name, info in WHALE_ROUTES.items():
            st.markdown(
                f'<span style="color:{info["color"]};font-weight:bold;">&#9473;&#9473;</span> '
                f'**{_safe(name)}**: {_safe(info["description"])}',
                unsafe_allow_html=True,
            )

        st.markdown("#### Shark Hotspots")
        shark_cols = st.columns(4)
        for idx, s in enumerate(SHARK_HOTSPOTS):
            with shark_cols[idx % 4]:
                st.markdown(
                    f'<span style="color:{s["color"]};font-weight:bold;">&#9679;</span> '
                    f'**{_safe(s["species"])}**<br>'
                    f'<span style="color:{SECONDARY_TEXT};font-size:12px;">{_safe(s["name"])}</span>',
                    unsafe_allow_html=True,
                )

        df = _build_marine_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "marine_megafauna.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 5. MARSUPIAL DISTRIBUTION
    # ════════════════════════════════════════════════════════════
    elif mode == "Marsupial Distribution":
        st.subheader("Marsupial Distribution")
        st.caption(
            "Marsupial species across Australasia and the Americas, including kangaroos, koalas, "
            "wombats, Tasmanian devils, and South American opossums."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            _stat_card("Species", len(MARSUPIALS), "🦘")
        with c2:
            aus_count = sum(1 for info in MARSUPIALS.values()
                           if any(loc["lon"] > 100 for loc in info["locations"]))
            _stat_card("Australasian", aus_count, "🇦🇺")
        with c3:
            amer_count = len(MARSUPIALS) - aus_count
            _stat_card("Americas", amer_count, "🌎")

        m = _render_marsupial_map()
        components.html(m._repr_html_(), height=500)

        # Species details
        st.markdown("#### Species Details")
        for name, info in MARSUPIALS.items():
            with st.expander(f"{name} (*{info['scientific']}*)"):
                st.markdown(
                    f"**IUCN Status:** {_safe(info['status'])}  \n"
                    f"**Population:** {_safe(info['population'])}  \n"
                    f"**Locations:** {', '.join(loc['name'] for loc in info['locations'])}"
                )

        df = _build_marsupial_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "marsupial_distribution.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 6. BIRD MIGRATION FLYWAYS
    # ════════════════════════════════════════════════════════════
    elif mode == "Bird Migration Flyways":
        st.subheader("Bird Migration Flyways")
        st.caption(
            "Major global bird migration flyways connecting breeding grounds to "
            "wintering areas, with key species for each route."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            _stat_card("Flyways", len(FLYWAYS), "🦅")
        with c2:
            total_waypoints = sum(len(f["route"]) for f in FLYWAYS.values())
            _stat_card("Waypoints", total_waypoints, "📍")
        with c3:
            _stat_card("Continents Covered", 7, "🌍")

        m = _render_flyways_map()
        components.html(m._repr_html_(), height=500)

        # Flyway details
        st.markdown("#### Flyway Details")
        for name, info in FLYWAYS.items():
            st.markdown(
                f'<span style="color:{info["color"]};font-weight:bold;">&#9473;&#9473;</span> '
                f'**{_safe(name)}**  \n'
                f'*Key Species:* {_safe(info["key_species"])}  \n'
                f'*Route:* {_safe(info["description"])}',
                unsafe_allow_html=True,
            )

        df = _build_flyways_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "bird_flyways.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 7. ENDANGERED SPECIES HOTSPOTS
    # ════════════════════════════════════════════════════════════
    elif mode == "Endangered Species Hotspots":
        st.subheader("Endangered Species Hotspots")
        st.caption(
            "Global biodiversity hotspots with highest concentrations of critically endangered "
            "species. Data based on IUCN Red List critical areas."
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _stat_card("Hotspots", len(ENDANGERED_HOTSPOTS), "🔥")
        with c2:
            total_sp = sum(h["species_count"] for h in ENDANGERED_HOTSPOTS)
            _stat_card("Total Species", f"{total_sp:,}", "🦎")
        with c3:
            total_cr = sum(h["cr_species"] for h in ENDANGERED_HOTSPOTS)
            _stat_card("Critically Endangered", f"{total_cr:,}", "🔴")
        with c4:
            top = max(ENDANGERED_HOTSPOTS, key=lambda x: x["cr_species"])
            _stat_card("Most Critical", top["name"], "⚠️")

        m = _render_endangered_map()
        components.html(m._repr_html_(), height=500)

        # Chart
        fig = _chart_endangered_hotspots()
        st.pyplot(fig)
        plt.close(fig)

        # Hotspot details
        st.markdown("#### Hotspot Details")
        for h in sorted(ENDANGERED_HOTSPOTS, key=lambda x: x["cr_species"], reverse=True):
            with st.expander(f"{h['name']} - {h['cr_species']:,} CR species"):
                st.markdown(
                    f"**Total Species:** {h['species_count']:,}  \n"
                    f"**Critically Endangered:** {h['cr_species']:,}  \n"
                    f"**Description:** {_safe(h['description'])}  \n"
                    f"**Location:** {h['lat']:.1f}, {h['lon']:.1f}"
                )

        df = _build_endangered_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "endangered_hotspots.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 8. INVASIVE SPECIES
    # ════════════════════════════════════════════════════════════
    elif mode == "Invasive Species":
        st.subheader("Invasive Species Worldwide")
        st.caption(
            "Major invasive animal species that have devastated native ecosystems. "
            "Lines connect native origins to invasion sites."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            _stat_card("Invasive Species", len(INVASIVE_SPECIES), "🦀")
        with c2:
            total_inv = sum(len(sp["invasions"]) for sp in INVASIVE_SPECIES)
            _stat_card("Invasion Events", total_inv, "📍")
        with c3:
            earliest = min(inv["year"] for sp in INVASIVE_SPECIES for inv in sp["invasions"])
            _stat_card("Earliest Recorded", earliest, "📅")

        m = _render_invasive_map()
        components.html(m._repr_html_(), height=500)

        # Chart
        fig = _chart_invasive_timeline()
        st.pyplot(fig)
        plt.close(fig)

        # Species details
        st.markdown("#### Invasive Species Details")
        for sp in INVASIVE_SPECIES:
            with st.expander(f"{sp['name']} (*{sp['scientific']}*)"):
                st.markdown(f"**Native Range:** {_safe(sp['origin']['name'])}")
                for inv in sp["invasions"]:
                    st.markdown(
                        f"- **{_safe(inv['name'])}** ({inv['year']}): {_safe(inv['impact'])}"
                    )

        df = _build_invasive_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "invasive_species.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 9. DEEP SEA CREATURES
    # ════════════════════════════════════════════════════════════
    elif mode == "Deep Sea Creatures":
        st.subheader("Deep Sea Creatures & Habitats")
        st.caption(
            "Hydrothermal vents, deep ocean trenches, cold seeps, and seamounts with their "
            "remarkable chemosynthetic and pressure-adapted species."
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _stat_card("Sites", len(DEEP_SEA_SITES), "🌊")
        with c2:
            vents = sum(1 for s in DEEP_SEA_SITES if s["type"] == "Hydrothermal Vent")
            _stat_card("Vents", vents, "🌋")
        with c3:
            trenches = sum(1 for s in DEEP_SEA_SITES if s["type"] == "Trench")
            _stat_card("Trenches", trenches, "🕳️")
        with c4:
            deepest = max(DEEP_SEA_SITES, key=lambda x: x["depth_m"])
            _stat_card("Deepest", f"{deepest['depth_m']:,}m", "⬇️")

        m = _render_deep_sea_map()
        components.html(m._repr_html_(), height=500)

        # Depth chart
        fig = _chart_deep_sea_depths()
        st.pyplot(fig)
        plt.close(fig)

        # Site type breakdown
        st.markdown("#### Site Types")
        type_counts = {}
        for s in DEEP_SEA_SITES:
            type_counts[s["type"]] = type_counts.get(s["type"], 0) + 1
        type_cols = st.columns(len(type_counts))
        for idx, (t, cnt) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
            with type_cols[idx]:
                _stat_card(t, cnt, "")

        # Details
        st.markdown("#### Site Details")
        for s in sorted(DEEP_SEA_SITES, key=lambda x: x["depth_m"], reverse=True):
            with st.expander(f"{s['name']} ({s['type']} - {s['depth_m']:,}m)"):
                st.markdown(
                    f"**Type:** {_safe(s['type'])}  \n"
                    f"**Depth:** {s['depth_m']:,} meters  \n"
                    f"**Notable Species:** {_safe(s['species'])}  \n"
                    f"**Location:** {s['lat']:.2f}, {s['lon']:.2f}"
                )

        df = _build_deep_sea_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "deep_sea_creatures.csv", "text/csv")

    # ════════════════════════════════════════════════════════════
    # 10. EXTINCT SPECIES LAST LOCATIONS
    # ════════════════════════════════════════════════════════════
    elif mode == "Extinct Species Last Locations":
        st.subheader("Extinct Species - Last Known Locations")
        st.caption(
            "Mapping the last known sightings or confirmed locations of species that have been "
            "declared extinct, from the Dodo to the Bramble Cay Melomys."
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _stat_card("Extinct Species", len(EXTINCT_SPECIES), "💀")
        with c2:
            hunting = sum(1 for sp in EXTINCT_SPECIES if "hunt" in sp["cause"].lower())
            _stat_card("Caused by Hunting", hunting, "🎯")
        with c3:
            habitat = sum(1 for sp in EXTINCT_SPECIES if "habitat" in sp["cause"].lower())
            _stat_card("Habitat Loss", habitat, "🌳")
        with c4:
            recent = sum(1 for sp in EXTINCT_SPECIES if any(
                str(y) in sp["last_seen"] for y in range(2000, 2025)))
            _stat_card("Lost Since 2000", recent, "📅")

        m = _render_extinct_map()
        components.html(m._repr_html_(), height=500)

        # Timeline chart
        fig = _chart_extinct_timeline()
        st.pyplot(fig)
        plt.close(fig)

        # Cause breakdown
        st.markdown("#### Extinction Causes")
        causes = {}
        for sp in EXTINCT_SPECIES:
            for keyword in ["Hunting", "Habitat", "Climate", "Invasive", "Disease", "Pollution", "Overfishing"]:
                if keyword.lower() in sp["cause"].lower():
                    causes[keyword] = causes.get(keyword, 0) + 1
        if causes:
            cause_cols = st.columns(len(causes))
            for idx, (cause, cnt) in enumerate(sorted(causes.items(), key=lambda x: -x[1])):
                with cause_cols[idx]:
                    _stat_card(cause, cnt, "")

        # Species cards
        st.markdown("#### Species Details")
        for sp in sorted(EXTINCT_SPECIES, key=lambda x: x["last_seen"], reverse=True):
            with st.expander(f"{sp['name']} (*{sp['scientific']}*) - Last seen: {sp['last_seen']}"):
                st.markdown(
                    f"**Scientific Name:** *{_safe(sp['scientific'])}*  \n"
                    f"**Last Location:** {_safe(sp['location'])}  \n"
                    f"**Last Confirmed Sighting:** {_safe(sp['last_seen'])}  \n"
                    f"**Cause of Extinction:** {_safe(sp['cause'])}  \n"
                    f"**Coordinates:** {sp['lat']:.2f}, {sp['lon']:.2f}"
                )

        df = _build_extinct_df()
        st.dataframe(df, width="stretch")

        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        st.download_button("Download CSV", buf.getvalue(), "extinct_species.csv", "text/csv")
