# -*- coding: utf-8 -*-
"""
Ruins & Lost Cities Explorer module for TerraScout AI.
Provides 10 curated map modes covering ancient wonders, lost cities,
abandoned settlements, megalithic sites, underwater ruins, jungle ruins,
desert ruins, castles & fortresses, ancient temples, and ghost towns.
All data uses curated coordinates plus optional Overpass API enrichment
for nearby historic features. Free APIs only.
"""

import io
import math
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


# ═══════════════════════════════════════════════════════════════════
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

MAP_MODES = [
    "Ancient Wonders",
    "Lost Cities",
    "Abandoned Cities",
    "Megalithic Sites",
    "Underwater Ruins",
    "Jungle Ruins",
    "Desert Ruins",
    "Castles & Fortresses",
    "Ancient Temples",
    "Ghost Towns",
]

MODE_ICONS = {
    "Ancient Wonders": "\u26f0\ufe0f",
    "Lost Cities": "\U0001f3da\ufe0f",
    "Abandoned Cities": "\U0001f3d7\ufe0f",
    "Megalithic Sites": "\U0001faa8",
    "Underwater Ruins": "\U0001f30a",
    "Jungle Ruins": "\U0001f333",
    "Desert Ruins": "\U0001f3dc\ufe0f",
    "Castles & Fortresses": "\U0001f3f0",
    "Ancient Temples": "\U0001f6d5",
    "Ghost Towns": "\U0001f47b",
}

MODE_COLORS = {
    "Ancient Wonders": "#f59e0b",
    "Lost Cities": "#8b5cf6",
    "Abandoned Cities": "#64748b",
    "Megalithic Sites": "#10b981",
    "Underwater Ruins": "#06b6d4",
    "Jungle Ruins": "#22c55e",
    "Desert Ruins": "#f97316",
    "Castles & Fortresses": "#ef4444",
    "Ancient Temples": "#ec4899",
    "Ghost Towns": "#a1a1aa",
}

MODE_DESCRIPTIONS = {
    "Ancient Wonders": (
        "Explore humanity's most awe-inspiring ancient constructions -- from the "
        "Great Pyramids of Giza to the Colosseum of Rome. These sites represent "
        "the pinnacle of engineering and ambition in the ancient world."
    ),
    "Lost Cities": (
        "Rediscover cities that were once thriving centers of civilization before "
        "being swallowed by time, disaster, or conquest. From Pompeii buried by "
        "Vesuvius to the legendary Troy besieged by the Greeks."
    ),
    "Abandoned Cities": (
        "Modern ghost cities left behind due to nuclear disasters, mine fires, "
        "economic collapse, or the forces of nature. These eerie places are frozen "
        "in time, reclaimed by the elements."
    ),
    "Megalithic Sites": (
        "Prehistoric stone monuments that predate written history. From Stonehenge's "
        "mysterious circle to Gobekli Tepe, the oldest known temple complex, these "
        "sites challenge our understanding of early human capability."
    ),
    "Underwater Ruins": (
        "Submerged cities and structures lost beneath the waves through earthquakes, "
        "rising seas, or tsunamis. These underwater archaeological sites offer "
        "glimpses into civilizations swallowed by the ocean."
    ),
    "Jungle Ruins": (
        "Ancient cities hidden beneath dense tropical canopies, reclaimed by nature "
        "over centuries. From the towering pyramids of Tikal to the vast complexes "
        "of Angkor, the jungle guards its secrets well."
    ),
    "Desert Ruins": (
        "Once-great cities now standing as monuments amid vast desert landscapes. "
        "The dry climate has preserved remarkable details of civilizations that "
        "flourished along trade routes and oases millennia ago."
    ),
    "Castles & Fortresses": (
        "The most impressive ruined castles and fortifications from around the "
        "world -- from crusader strongholds to samurai keeps and medieval citadels "
        "perched atop impossible cliffs."
    ),
    "Ancient Temples": (
        "Sacred sites and temple complexes that served as the spiritual hearts of "
        "ancient civilizations. These structures showcase extraordinary artistry, "
        "astronomical alignment, and devotion spanning thousands of years."
    ),
    "Ghost Towns": (
        "Towns born from silver rushes, oil booms, and utopian dreams, now "
        "standing empty. From the American West to Australian outback, these "
        "abandoned settlements tell stories of boom and bust."
    ),
}


# ═══════════════════════════════════════════════════════════════════
# CURATED SITE DATA (10 modes, 5-12 sites each)
# ═══════════════════════════════════════════════════════════════════

SITES = {
    # ──────────────────────────────────────────────────
    # 1. Ancient Wonders
    # ──────────────────────────────────────────────────
    "Ancient Wonders": [
        {
            "name": "Great Pyramid of Giza",
            "lat": 29.9792, "lon": 31.1342,
            "country": "Egypt",
            "era": "c. 2560 BC",
            "description": "Last surviving Ancient Wonder. Built as a tomb for Pharaoh Khufu, standing 146m tall for over 3,800 years.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Colosseum",
            "lat": 41.8902, "lon": 12.4922,
            "country": "Italy",
            "era": "c. 70-80 AD",
            "description": "Largest amphitheatre ever built, seating 50,000-80,000 spectators for gladiatorial contests and public spectacles.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Parthenon",
            "lat": 37.9715, "lon": 23.7267,
            "country": "Greece",
            "era": "c. 447-432 BC",
            "description": "Temple dedicated to Athena, the pinnacle of Doric architecture atop the Athenian Acropolis.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Petra (Al-Khazneh)",
            "lat": 30.3285, "lon": 35.4444,
            "country": "Jordan",
            "era": "c. 312 BC",
            "description": "Rose-red city carved into sandstone cliffs by the Nabataeans. Half-built, half-carved into rock.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Angkor Wat",
            "lat": 13.4125, "lon": 103.8670,
            "country": "Cambodia",
            "era": "c. 1113-1150 AD",
            "description": "Largest religious monument in the world, originally Hindu then Buddhist, spanning 162.6 hectares.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Machu Picchu",
            "lat": -13.1631, "lon": -72.5450,
            "country": "Peru",
            "era": "c. 1450 AD",
            "description": "Inca citadel set high in the Andes at 2,430m. Abandoned during the Spanish Conquest and hidden for centuries.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Chichen Itza",
            "lat": 20.6843, "lon": -88.5678,
            "country": "Mexico",
            "era": "c. 600 AD",
            "description": "Pre-Columbian Mayan city famed for the Kukulkan pyramid with its equinox serpent shadow effect.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Ephesus",
            "lat": 37.9394, "lon": 27.3420,
            "country": "Turkey",
            "era": "c. 10th century BC",
            "description": "Once home to the Temple of Artemis (Ancient Wonder). A remarkably well-preserved Greco-Roman city.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Great Wall of China (Mutianyu)",
            "lat": 40.4319, "lon": 116.5704,
            "country": "China",
            "era": "c. 7th century BC onward",
            "description": "Over 21,000 km of walls built across centuries. Mutianyu is one of the best-preserved sections.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Baalbek",
            "lat": 34.0069, "lon": 36.2039,
            "country": "Lebanon",
            "era": "c. 9000 BC onward",
            "description": "Colossal Roman temple complex built on even older foundations with the largest hewn stone blocks ever found.",
            "status": "Partially Ruined",
            "unesco": True,
        },
    ],

    # ──────────────────────────────────────────────────
    # 2. Lost Cities
    # ──────────────────────────────────────────────────
    "Lost Cities": [
        {
            "name": "Pompeii",
            "lat": 40.7509, "lon": 14.4869,
            "country": "Italy",
            "era": "Buried 79 AD",
            "description": "Roman city frozen in time by the eruption of Mount Vesuvius. Extraordinary preservation of daily life.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Troy (Hisarlik)",
            "lat": 39.9574, "lon": 26.2388,
            "country": "Turkey",
            "era": "c. 3000 BC",
            "description": "Legendary city of Homer's Iliad, rediscovered by Heinrich Schliemann. Nine layers of occupation.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Mohenjo-daro",
            "lat": 27.3290, "lon": 68.1389,
            "country": "Pakistan",
            "era": "c. 2500 BC",
            "description": "Sophisticated Indus Valley city with advanced drainage, grid streets, and the Great Bath. Abandoned c. 1900 BC.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Great Zimbabwe",
            "lat": -20.2671, "lon": 30.9339,
            "country": "Zimbabwe",
            "era": "c. 1100-1450 AD",
            "description": "Massive stone ruins of a medieval African kingdom. The largest ancient structure south of the Sahara.",
            "status": "Ruined",
            "unesco": True,
        },
        {
            "name": "Tenochtitlan (Mexico City)",
            "lat": 19.4326, "lon": -99.1332,
            "country": "Mexico",
            "era": "c. 1325-1521 AD",
            "description": "Capital of the Aztec Empire, built on an island in Lake Texcoco. Now buried beneath modern Mexico City.",
            "status": "Buried/Partial",
            "unesco": False,
        },
        {
            "name": "Carthage",
            "lat": 36.8528, "lon": 10.3234,
            "country": "Tunisia",
            "era": "c. 814 BC",
            "description": "Great Phoenician trading power destroyed by Rome in 146 BC. Rebuilt as a Roman city, then abandoned again.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Herculaneum",
            "lat": 40.8059, "lon": 14.3475,
            "country": "Italy",
            "era": "Buried 79 AD",
            "description": "Sister city to Pompeii, buried by pyroclastic flows from Vesuvius. Even better organic preservation.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Taxila",
            "lat": 33.7460, "lon": 72.7978,
            "country": "Pakistan",
            "era": "c. 1000 BC",
            "description": "Ancient Gandharan city, a center of Buddhist learning visited by Alexander the Great.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Akrotiri",
            "lat": 36.3517, "lon": 25.4033,
            "country": "Greece",
            "era": "Buried c. 1627 BC",
            "description": "Minoan Bronze Age settlement on Santorini, buried by one of the largest volcanic eruptions in history.",
            "status": "Excavated",
            "unesco": False,
        },
        {
            "name": "Ctesiphon",
            "lat": 33.0936, "lon": 44.5814,
            "country": "Iraq",
            "era": "c. 120 BC",
            "description": "Capital of the Parthian and Sasanian Empires. The Arch of Ctesiphon remains the largest single-span vault of unreinforced brickwork.",
            "status": "Ruined",
            "unesco": False,
        },
    ],

    # ──────────────────────────────────────────────────
    # 3. Abandoned Cities
    # ──────────────────────────────────────────────────
    "Abandoned Cities": [
        {
            "name": "Pripyat",
            "lat": 51.4045, "lon": 30.0542,
            "country": "Ukraine",
            "era": "Abandoned 1986",
            "description": "Soviet city evacuated after the Chernobyl nuclear disaster. 49,000 residents left within 36 hours.",
            "status": "Abandoned/Radioactive",
            "unesco": False,
        },
        {
            "name": "Centralia",
            "lat": 40.8042, "lon": -76.3404,
            "country": "USA",
            "era": "Abandoned 1984",
            "description": "Pennsylvania coal town above an underground mine fire burning since 1962. Inspired Silent Hill.",
            "status": "Abandoned/Burning",
            "unesco": False,
        },
        {
            "name": "Craco",
            "lat": 40.3809, "lon": 16.4423,
            "country": "Italy",
            "era": "Abandoned 1963",
            "description": "Medieval hilltop village in Basilicata abandoned due to recurring landslides. Popular film location.",
            "status": "Abandoned/Crumbling",
            "unesco": False,
        },
        {
            "name": "Kolmanskop",
            "lat": -26.7044, "lon": 15.2279,
            "country": "Namibia",
            "era": "Abandoned 1954",
            "description": "German diamond-mining town in the Namib Desert, now being swallowed by sand dunes.",
            "status": "Abandoned/Sand-filled",
            "unesco": False,
        },
        {
            "name": "Hashima Island (Gunkanjima)",
            "lat": 32.6275, "lon": 129.7386,
            "country": "Japan",
            "era": "Abandoned 1974",
            "description": "Densely populated coal mining island, once the most crowded place on Earth. James Bond film location.",
            "status": "Abandoned/Decaying",
            "unesco": True,
        },
        {
            "name": "Varosha (Famagusta)",
            "lat": 35.1081, "lon": 33.9552,
            "country": "Cyprus",
            "era": "Abandoned 1974",
            "description": "Once a glamorous Mediterranean resort, sealed off since the Turkish invasion. Hotels and shops frozen in time.",
            "status": "Abandoned/Restricted",
            "unesco": False,
        },
        {
            "name": "Oradour-sur-Glane",
            "lat": 45.9336, "lon": 1.0297,
            "country": "France",
            "era": "Destroyed 1944",
            "description": "French village destroyed by Nazi SS troops. Preserved as a memorial to the 642 victims of the massacre.",
            "status": "Memorial Ruin",
            "unesco": False,
        },
        {
            "name": "Kayakoy (Levissi)",
            "lat": 36.5783, "lon": 29.0853,
            "country": "Turkey",
            "era": "Abandoned 1923",
            "description": "Greek village abandoned during the population exchange between Greece and Turkey. 500 stone houses remain.",
            "status": "Abandoned/Museum",
            "unesco": False,
        },
        {
            "name": "Agdam",
            "lat": 39.9910, "lon": 46.9269,
            "country": "Azerbaijan",
            "era": "Destroyed 1993",
            "description": "City of 40,000 systematically destroyed during the Nagorno-Karabakh conflict. Known as the Hiroshima of the Caucasus.",
            "status": "Destroyed",
            "unesco": False,
        },
        {
            "name": "Wittenoom",
            "lat": -22.2364, "lon": 118.3328,
            "country": "Australia",
            "era": "Abandoned 2007",
            "description": "Australian mining town contaminated with blue asbestos. Officially degazetted, removed from maps.",
            "status": "Abandoned/Contaminated",
            "unesco": False,
        },
    ],

    # ──────────────────────────────────────────────────
    # 4. Megalithic Sites
    # ──────────────────────────────────────────────────
    "Megalithic Sites": [
        {
            "name": "Stonehenge",
            "lat": 51.1789, "lon": -1.8262,
            "country": "England",
            "era": "c. 3000-2000 BC",
            "description": "Iconic prehistoric stone circle on Salisbury Plain. Aligned with the sunrise on the summer solstice.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Carnac Stones",
            "lat": 47.5950, "lon": -3.0783,
            "country": "France",
            "era": "c. 4500-3300 BC",
            "description": "Over 3,000 standing stones arranged in rows stretching for kilometers across Brittany.",
            "status": "Well Preserved",
            "unesco": False,
        },
        {
            "name": "Gobekli Tepe",
            "lat": 37.2233, "lon": 38.9224,
            "country": "Turkey",
            "era": "c. 9500 BC",
            "description": "Oldest known temple complex. Massive T-shaped pillars with animal carvings, built before agriculture.",
            "status": "Partially Excavated",
            "unesco": True,
        },
        {
            "name": "Newgrange",
            "lat": 53.6947, "lon": -6.4756,
            "country": "Ireland",
            "era": "c. 3200 BC",
            "description": "Neolithic passage tomb older than the Pyramids. Winter solstice sunlight illuminates the inner chamber.",
            "status": "Restored",
            "unesco": True,
        },
        {
            "name": "Moai of Easter Island",
            "lat": -27.1127, "lon": -109.3497,
            "country": "Chile",
            "era": "c. 1250-1500 AD",
            "description": "Nearly 900 monolithic human figures carved by the Rapa Nui people. Average height 4m, average weight 12.5 tonnes.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Callanish Stones",
            "lat": 58.1975, "lon": -6.7453,
            "country": "Scotland",
            "era": "c. 2900-2600 BC",
            "description": "Cruciform stone circle on the Isle of Lewis. Predates Stonehenge and rivals it in astronomical significance.",
            "status": "Well Preserved",
            "unesco": False,
        },
        {
            "name": "Dolmen of Menga",
            "lat": 37.0234, "lon": -4.5478,
            "country": "Spain",
            "era": "c. 3750-3650 BC",
            "description": "One of the largest megalithic structures in Europe. A burial mound with a 25m-long chamber.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Almendres Cromlech",
            "lat": 38.5567, "lon": -8.0600,
            "country": "Portugal",
            "era": "c. 6000 BC",
            "description": "One of the oldest megalithic complexes in the Iberian Peninsula with 95 standing stones.",
            "status": "Well Preserved",
            "unesco": False,
        },
        {
            "name": "Avebury",
            "lat": 51.4286, "lon": -1.8544,
            "country": "England",
            "era": "c. 2850 BC",
            "description": "Largest stone circle in the world, enclosing the village of Avebury. Part of a ceremonial landscape.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Nabta Playa",
            "lat": 22.5200, "lon": 30.7100,
            "country": "Egypt",
            "era": "c. 7500-4500 BC",
            "description": "One of the earliest known astronomical alignments. Stone circle in the Nubian Desert predating Stonehenge by millennia.",
            "status": "Partially Preserved",
            "unesco": False,
        },
    ],

    # ──────────────────────────────────────────────────
    # 5. Underwater Ruins
    # ──────────────────────────────────────────────────
    "Underwater Ruins": [
        {
            "name": "Dwarka (Submerged)",
            "lat": 22.2387, "lon": 68.9683,
            "country": "India",
            "era": "c. 1500 BC",
            "description": "Legendary city of Lord Krishna. Underwater ruins off Gujarat coast may date to the 2nd millennium BC.",
            "status": "Submerged",
            "unesco": False,
        },
        {
            "name": "Yonaguni Monument",
            "lat": 24.4350, "lon": 123.0100,
            "country": "Japan",
            "era": "c. 8000 BC (debated)",
            "description": "Massive stepped rock formation off Yonaguni Island. Debate rages over natural formation vs. human construction.",
            "status": "Submerged",
            "unesco": False,
        },
        {
            "name": "Pavlopetri",
            "lat": 36.5193, "lon": 22.5671,
            "country": "Greece",
            "era": "c. 5000 BC",
            "description": "World's oldest known submerged city off the Peloponnese coast. Complete street plan visible underwater.",
            "status": "Submerged",
            "unesco": False,
        },
        {
            "name": "Port Royal",
            "lat": 17.9361, "lon": -76.8413,
            "country": "Jamaica",
            "era": "Sunk 1692",
            "description": "Once the wickedest city on Earth. Two-thirds sank during a massive earthquake in 1692.",
            "status": "Partially Submerged",
            "unesco": False,
        },
        {
            "name": "Cleopatra's Palace (Alexandria)",
            "lat": 31.2136, "lon": 29.8853,
            "country": "Egypt",
            "era": "c. 300 BC",
            "description": "Royal quarters of Cleopatra VII submerged by earthquakes and tsunamis. Statues and sphinxes found underwater.",
            "status": "Submerged",
            "unesco": False,
        },
        {
            "name": "Baiae",
            "lat": 40.8191, "lon": 14.0783,
            "country": "Italy",
            "era": "c. 100 BC",
            "description": "Luxurious Roman resort town, now a submerged archaeological park in the Gulf of Naples. Mosaics visible underwater.",
            "status": "Submerged/Park",
            "unesco": False,
        },
        {
            "name": "Heracleion (Thonis)",
            "lat": 31.3000, "lon": 30.1000,
            "country": "Egypt",
            "era": "c. 12th century BC",
            "description": "Major Egyptian port city lost for 1,200 years. Rediscovered in 2000 in Abu Qir Bay with intact temples.",
            "status": "Submerged",
            "unesco": False,
        },
        {
            "name": "Lion City (Shi Cheng)",
            "lat": 29.5333, "lon": 119.0333,
            "country": "China",
            "era": "Flooded 1959",
            "description": "1,300-year-old city deliberately flooded to create Qiandao Lake. Preserved perfectly at 26-40m depth.",
            "status": "Submerged/Intact",
            "unesco": False,
        },
        {
            "name": "Olous",
            "lat": 35.2500, "lon": 25.7500,
            "country": "Greece",
            "era": "c. 3000 BC",
            "description": "Minoan-era city off the coast of Crete, sunk by tectonic shifts. Mosaic floors visible through clear water.",
            "status": "Submerged",
            "unesco": False,
        },
    ],

    # ──────────────────────────────────────────────────
    # 6. Jungle Ruins
    # ──────────────────────────────────────────────────
    "Jungle Ruins": [
        {
            "name": "Tikal",
            "lat": 17.2220, "lon": -89.6237,
            "country": "Guatemala",
            "era": "c. 200-900 AD",
            "description": "One of the largest Maya cities. Temple IV rises 65m above the jungle canopy in Peten Basin.",
            "status": "Partially Excavated",
            "unesco": True,
        },
        {
            "name": "Angkor Thom",
            "lat": 13.4410, "lon": 103.8586,
            "country": "Cambodia",
            "era": "c. 1181 AD",
            "description": "Walled royal city of the Khmer Empire. The Bayon temple features 216 massive serene stone faces.",
            "status": "Partially Restored",
            "unesco": True,
        },
        {
            "name": "El Mirador",
            "lat": 17.7550, "lon": -89.9200,
            "country": "Guatemala",
            "era": "c. 600 BC",
            "description": "Massive pre-Classic Maya city with La Danta pyramid -- one of the largest pyramids by volume in the world.",
            "status": "Buried in Jungle",
            "unesco": False,
        },
        {
            "name": "Ciudad Perdida",
            "lat": 11.0381, "lon": -73.9254,
            "country": "Colombia",
            "era": "c. 800 AD",
            "description": "The Lost City of the Tairona people in the Sierra Nevada de Santa Marta. 1,200 stone terraces connected by tiled roads.",
            "status": "Partially Cleared",
            "unesco": False,
        },
        {
            "name": "Sigiriya",
            "lat": 7.9570, "lon": 80.7603,
            "country": "Sri Lanka",
            "era": "c. 477-495 AD",
            "description": "Ancient rock fortress rising 200m from the jungle. Features the world's oldest known landscape garden.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Palenque",
            "lat": 17.4838, "lon": -92.0462,
            "country": "Mexico",
            "era": "c. 226 BC-799 AD",
            "description": "Maya city-state in Chiapas jungle. The Temple of Inscriptions houses the tomb of K'inich Janaab Pakal.",
            "status": "Partially Excavated",
            "unesco": True,
        },
        {
            "name": "Calakmul",
            "lat": 18.1054, "lon": -89.8107,
            "country": "Mexico",
            "era": "c. 500 BC-900 AD",
            "description": "Rival superpower to Tikal deep in the Campeche jungle. Over 6,750 structures including two massive pyramids.",
            "status": "Partially Excavated",
            "unesco": True,
        },
        {
            "name": "Koh Ker",
            "lat": 13.7830, "lon": 104.5370,
            "country": "Cambodia",
            "era": "c. 928-944 AD",
            "description": "Brief Khmer capital deep in Cambodian jungle. Prasat Thom pyramid rises 36m in seven tiers.",
            "status": "Jungle-covered",
            "unesco": True,
        },
        {
            "name": "Copan",
            "lat": 14.8400, "lon": -89.1410,
            "country": "Honduras",
            "era": "c. 426-822 AD",
            "description": "Maya city famed for its elaborate stelae, altars, and the longest known Maya hieroglyphic text.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Beng Mealea",
            "lat": 13.5890, "lon": 104.0670,
            "country": "Cambodia",
            "era": "c. 1100 AD",
            "description": "Sprawling temple complex consumed by jungle, largely unrestored. Often called the Indiana Jones temple.",
            "status": "Jungle Ruin",
            "unesco": False,
        },
    ],

    # ──────────────────────────────────────────────────
    # 7. Desert Ruins
    # ──────────────────────────────────────────────────
    "Desert Ruins": [
        {
            "name": "Palmyra",
            "lat": 34.5513, "lon": 38.2690,
            "country": "Syria",
            "era": "c. 2000 BC",
            "description": "Oasis city blending Greco-Roman and Persian architecture. Severely damaged by ISIS in 2015.",
            "status": "Damaged/Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Persepolis",
            "lat": 29.9350, "lon": 52.8914,
            "country": "Iran",
            "era": "c. 515 BC",
            "description": "Ceremonial capital of the Achaemenid Empire, burned by Alexander the Great in 330 BC.",
            "status": "Ruined",
            "unesco": True,
        },
        {
            "name": "Petra",
            "lat": 30.3285, "lon": 35.4444,
            "country": "Jordan",
            "era": "c. 312 BC",
            "description": "Nabataean trading city carved from rose-red sandstone. Features over 800 individual monuments.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Leptis Magna",
            "lat": 32.6378, "lon": 14.2931,
            "country": "Libya",
            "era": "c. 1000 BC",
            "description": "One of the best-preserved Roman cities in the Mediterranean, birthplace of Emperor Septimius Severus.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Abu Simbel",
            "lat": 22.3369, "lon": 31.6256,
            "country": "Egypt",
            "era": "c. 1264 BC",
            "description": "Massive rock-cut temples of Ramesses II, relocated in 1968 to save them from Lake Nasser flooding.",
            "status": "Restored/Relocated",
            "unesco": True,
        },
        {
            "name": "Timgad",
            "lat": 35.4849, "lon": 6.4684,
            "country": "Algeria",
            "era": "c. 100 AD",
            "description": "Roman colonial town in North Africa with perfectly preserved grid plan, Trajan's Arch, and theater.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Meroe Pyramids",
            "lat": 16.9381, "lon": 33.7489,
            "country": "Sudan",
            "era": "c. 300 BC-350 AD",
            "description": "Over 200 pyramids of the Kingdom of Kush. Steeper and more numerous than their Egyptian predecessors.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Hegra (Mada'in Saleh)",
            "lat": 26.7917, "lon": 37.9531,
            "country": "Saudi Arabia",
            "era": "c. 1st century AD",
            "description": "Nabataean sister city to Petra. Over 130 rock-cut monumental tombs with elaborate facades in the desert.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Djenné-Djenno",
            "lat": 13.9053, "lon": -4.5492,
            "country": "Mali",
            "era": "c. 250 BC",
            "description": "One of the oldest known cities in sub-Saharan Africa, showing urban life developed independently of outside influence.",
            "status": "Excavated",
            "unesco": True,
        },
        {
            "name": "Jiaohe",
            "lat": 42.9500, "lon": 89.0667,
            "country": "China",
            "era": "c. 108 BC",
            "description": "Ancient Silk Road garrison city carved from a natural plateau between two rivers in the Turpan Depression.",
            "status": "Ruined/Preserved by Aridity",
            "unesco": False,
        },
    ],

    # ──────────────────────────────────────────────────
    # 8. Castles & Fortresses
    # ──────────────────────────────────────────────────
    "Castles & Fortresses": [
        {
            "name": "Krak des Chevaliers",
            "lat": 34.7571, "lon": 36.2934,
            "country": "Syria",
            "era": "c. 1031-1271 AD",
            "description": "Best-preserved Crusader castle. T.E. Lawrence called it 'the finest castle in the world'.",
            "status": "Partially Damaged",
            "unesco": True,
        },
        {
            "name": "Masada",
            "lat": 31.3156, "lon": 35.3539,
            "country": "Israel",
            "era": "c. 37-31 BC",
            "description": "Herod's mountain-top fortress overlooking the Dead Sea. Site of the famous Jewish last stand against Rome.",
            "status": "Ruined",
            "unesco": True,
        },
        {
            "name": "Rumeli Hisari",
            "lat": 41.0847, "lon": 29.0569,
            "country": "Turkey",
            "era": "1452 AD",
            "description": "Ottoman fortress built in just four months to control the Bosphorus before the conquest of Constantinople.",
            "status": "Well Preserved",
            "unesco": False,
        },
        {
            "name": "Golconda Fort",
            "lat": 17.3833, "lon": 78.4011,
            "country": "India",
            "era": "c. 13th century AD",
            "description": "Massive fortress with an acoustic warning system: a clap at the gate can be heard at the top of the citadel.",
            "status": "Partially Ruined",
            "unesco": False,
        },
        {
            "name": "Dunnottar Castle",
            "lat": 56.9461, "lon": -2.1961,
            "country": "Scotland",
            "era": "c. 15th century AD",
            "description": "Dramatic clifftop ruin overlooking the North Sea. Inspired Franco Zeffirelli's Hamlet.",
            "status": "Ruined",
            "unesco": False,
        },
        {
            "name": "Fasil Ghebbi",
            "lat": 12.6089, "lon": 37.4689,
            "country": "Ethiopia",
            "era": "c. 1636 AD",
            "description": "Royal enclosure of Emperor Fasilides in Gondar, sometimes called the Camelot of Africa.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Brest Fortress",
            "lat": 52.0833, "lon": 23.6556,
            "country": "Belarus",
            "era": "c. 1836-1842 AD",
            "description": "19th-century fortress famous for its heroic defense during the opening days of Operation Barbarossa in 1941.",
            "status": "Ruined/Memorial",
            "unesco": False,
        },
        {
            "name": "Himeji Castle",
            "lat": 34.8394, "lon": 134.6939,
            "country": "Japan",
            "era": "c. 1333 AD onward",
            "description": "Japan's finest surviving feudal castle, known as White Heron Castle for its elegant white exterior.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Chateau Gaillard",
            "lat": 49.2384, "lon": 1.4050,
            "country": "France",
            "era": "1196-1198 AD",
            "description": "Richard the Lionheart's castle above the Seine. Built in just two years, it was considered impregnable.",
            "status": "Ruined",
            "unesco": False,
        },
        {
            "name": "Alamut Castle",
            "lat": 36.4344, "lon": 50.5806,
            "country": "Iran",
            "era": "c. 860 AD",
            "description": "Mountain fortress of the Ismaili Assassins, perched at 2,163m in the Alborz Mountains.",
            "status": "Ruined",
            "unesco": False,
        },
    ],

    # ──────────────────────────────────────────────────
    # 9. Ancient Temples
    # ──────────────────────────────────────────────────
    "Ancient Temples": [
        {
            "name": "Karnak Temple Complex",
            "lat": 25.7188, "lon": 32.6573,
            "country": "Egypt",
            "era": "c. 2055 BC-100 AD",
            "description": "Largest ancient religious site in the world. The Hypostyle Hall has 134 massive columns in 16 rows.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Borobudur",
            "lat": -7.6079, "lon": 110.2038,
            "country": "Indonesia",
            "era": "c. 750-842 AD",
            "description": "World's largest Buddhist temple with 2,672 relief panels and 504 Buddha statues in Central Java.",
            "status": "Restored",
            "unesco": True,
        },
        {
            "name": "Prambanan",
            "lat": -7.7520, "lon": 110.4915,
            "country": "Indonesia",
            "era": "c. 850 AD",
            "description": "Largest Hindu temple in Indonesia. The central Shiva temple rises 47m with exquisite Ramayana reliefs.",
            "status": "Partially Restored",
            "unesco": True,
        },
        {
            "name": "Bagan Temples",
            "lat": 21.1717, "lon": 94.8585,
            "country": "Myanmar",
            "era": "c. 849-1287 AD",
            "description": "Over 2,200 temples and pagodas spread across a 104 sq km plain along the Irrawaddy River.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Hampi (Vijayanagara)",
            "lat": 15.3350, "lon": 76.4600,
            "country": "India",
            "era": "c. 1336-1565 AD",
            "description": "Ruined capital of the Vijayanagara Empire. Over 1,600 remains spread across a surreal boulder-strewn landscape.",
            "status": "Ruined",
            "unesco": True,
        },
        {
            "name": "Luxor Temple",
            "lat": 25.6995, "lon": 32.6392,
            "country": "Egypt",
            "era": "c. 1400 BC",
            "description": "Grand temple on the east bank of the Nile dedicated to the rejuvenation of kingship. Connected to Karnak by an avenue of sphinxes.",
            "status": "Well Preserved",
            "unesco": True,
        },
        {
            "name": "Temple of Artemis (site)",
            "lat": 37.9496, "lon": 27.3639,
            "country": "Turkey",
            "era": "c. 550 BC",
            "description": "One of the Seven Wonders of the Ancient World. Only a single reconstructed column remains on the site.",
            "status": "Destroyed/Archaeological",
            "unesco": False,
        },
        {
            "name": "My Son Sanctuary",
            "lat": 15.7644, "lon": 108.1256,
            "country": "Vietnam",
            "era": "c. 4th-14th century AD",
            "description": "Hindu temple complex of the Champa Kingdom in a jungle valley. Partially damaged by US bombing in 1969.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Konark Sun Temple",
            "lat": 19.8876, "lon": 86.0945,
            "country": "India",
            "era": "c. 1250 AD",
            "description": "Monumental chariot-shaped temple dedicated to the Sun God with 24 elaborately carved wheels.",
            "status": "Partially Ruined",
            "unesco": True,
        },
        {
            "name": "Gobekli Tepe",
            "lat": 37.2233, "lon": 38.9224,
            "country": "Turkey",
            "era": "c. 9500 BC",
            "description": "World's oldest known temple complex predating pottery, metallurgy, and even agriculture.",
            "status": "Partially Excavated",
            "unesco": True,
        },
    ],

    # ──────────────────────────────────────────────────
    # 10. Ghost Towns
    # ──────────────────────────────────────────────────
    "Ghost Towns": [
        {
            "name": "Bodie",
            "lat": 38.2131, "lon": -119.0128,
            "country": "USA",
            "era": "Active 1877-1942",
            "description": "California gold-mining town preserved in a state of arrested decay. Once had 10,000 residents and 65 saloons.",
            "status": "State Historic Park",
            "unesco": False,
        },
        {
            "name": "Rhyolite",
            "lat": 36.9017, "lon": -116.8275,
            "country": "USA",
            "era": "Active 1904-1916",
            "description": "Nevada gold rush town near Death Valley. Grew to 5,000 in two years, abandoned within a decade.",
            "status": "Ruined",
            "unesco": False,
        },
        {
            "name": "Calico",
            "lat": 34.9486, "lon": -116.8667,
            "country": "USA",
            "era": "Active 1881-1907",
            "description": "Silver mining town in the Mojave Desert. Produced $86 million in silver before collapse. Now a county park.",
            "status": "Restored/Tourist Site",
            "unesco": False,
        },
        {
            "name": "Fordlandia",
            "lat": -3.8333, "lon": -55.5000,
            "country": "Brazil",
            "era": "Active 1928-1934",
            "description": "Henry Ford's failed rubber plantation utopia in the Amazon. American-style houses and a hospital still stand.",
            "status": "Abandoned",
            "unesco": False,
        },
        {
            "name": "Humberstone",
            "lat": -20.2078, "lon": -69.7917,
            "country": "Chile",
            "era": "Active 1872-1960",
            "description": "Chilean saltpeter (nitrate) mining town in the Atacama Desert. Preserved as a monument to the nitrate era.",
            "status": "Museum",
            "unesco": True,
        },
        {
            "name": "Thurmond",
            "lat": 38.0760, "lon": -80.8540,
            "country": "USA",
            "era": "Active 1873-1930s",
            "description": "West Virginia coal town that once rivaled the busiest railway stations. Population now under 5.",
            "status": "Near Abandoned",
            "unesco": False,
        },
        {
            "name": "Pyramiden",
            "lat": 78.6553, "lon": 16.3278,
            "country": "Norway (Svalbard)",
            "era": "Active 1910-1998",
            "description": "Soviet-era mining settlement in the Arctic. Abandoned with Lenin bust still facing the glacier.",
            "status": "Abandoned",
            "unesco": False,
        },
        {
            "name": "Walhalla",
            "lat": -37.9400, "lon": 146.4517,
            "country": "Australia",
            "era": "Active 1863-1914",
            "description": "Victorian-era gold mining town in Gippsland. Once had 4,000 residents, now a tiny historic village.",
            "status": "Partially Inhabited",
            "unesco": False,
        },
        {
            "name": "Bannack",
            "lat": 45.1614, "lon": -112.9967,
            "country": "USA",
            "era": "Active 1862-1930s",
            "description": "Montana gold rush town and first territorial capital. Notorious for vigilante justice and road agents.",
            "status": "State Park",
            "unesco": False,
        },
        {
            "name": "Kadykchan",
            "lat": 63.1000, "lon": 135.6500,
            "country": "Russia",
            "era": "Active 1943-1996",
            "description": "Soviet mining town in far-eastern Siberia. Evacuated after a mine explosion, left to the permafrost.",
            "status": "Abandoned",
            "unesco": False,
        },
        {
            "name": "Craco",
            "lat": 40.3809, "lon": 16.4423,
            "country": "Italy",
            "era": "Active 8th c. BC-1963",
            "description": "Perched medieval village abandoned due to landslides. Used as a film set for The Passion of the Christ.",
            "status": "Abandoned",
            "unesco": False,
        },
    ],
}


# ═══════════════════════════════════════════════════════════════════
# OVERPASS ENRICHMENT (nearby ruins search)
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _search_nearby_ruins(lat: float, lon: float, radius_m: int = 10000) -> list:
    """Search for historic ruins near a coordinate via Overpass API."""
    query = f"""
[out:json][timeout:30];
(
  node["historic"="ruins"](around:{radius_m},{lat},{lon});
  way["historic"="ruins"](around:{radius_m},{lat},{lon});
  node["historic"="archaeological_site"](around:{radius_m},{lat},{lon});
  way["historic"="archaeological_site"](around:{radius_m},{lat},{lon});
  node["tourism"="attraction"]["historic"](around:{radius_m},{lat},{lon});
  way["tourism"="attraction"]["historic"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query, timeout=30)
    if result is None or "_error" in result:
        return []

    elements = result.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        name = tags.get("name", tags.get("name:en", ""))
        if not name:
            continue

        elat, elon = None, None
        if el.get("type") == "node" and "lat" in el:
            elat, elon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [node_lookup[n] for n in nodes if n in node_lookup]
            if coords:
                elat = sum(c[0] for c in coords) / len(coords)
                elon = sum(c[1] for c in coords) / len(coords)
        if elat is None:
            continue

        key = f"{name}_{round(elat, 3)}_{round(elon, 3)}"
        if key in seen:
            continue
        seen.add(key)

        features.append({
            "name": name,
            "lat": elat,
            "lon": elon,
            "historic": tags.get("historic", ""),
            "wikipedia": tags.get("wikipedia", ""),
        })

    return features


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _haversine(lat1, lon1, lat2, lon2):
    """Distance between two points in kilometers."""
    R = 6371.0
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = (math.sin(dlat / 2) ** 2
         + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_popup_html(site: dict, mode_color: str) -> str:
    """Build a safe HTML popup for a folium marker."""
    name = escape(str(site.get("name", "Unknown")))
    country = escape(str(site.get("country", "")))
    era = escape(str(site.get("era", "")))
    desc = escape(str(site.get("description", ""))[:200])
    status = escape(str(site.get("status", "")))
    lat = site.get("lat", 0)
    lon = site.get("lon", 0)

    unesco_badge = ""
    if site.get("unesco"):
        unesco_badge = (
            '<span style="background:#f59e0b; color:#000; font-size:0.65rem; '
            'padding:1px 5px; border-radius:3px; font-weight:bold;">UNESCO</span> '
        )

    return f"""
    <div style="max-width:260px; font-family:system-ui,sans-serif;">
        <div style="font-weight:700; font-size:0.9rem; color:{mode_color};
                    margin-bottom:4px;">{name}</div>
        {unesco_badge}
        <div style="font-size:0.78rem; color:#555; margin-bottom:3px;">
            {country} &middot; {era}
        </div>
        <div style="font-size:0.75rem; color:#333; margin-bottom:4px;">{desc}</div>
        <div style="font-size:0.7rem; color:#777;">
            Status: {status}<br/>
            {lat:.4f}, {lon:.4f}
        </div>
    </div>
    """


def _build_folium_map(sites: list, mode: str, zoom: int = 3) -> folium.Map:
    """Create a dark-themed folium map with markers for the given sites."""
    mode_color = MODE_COLORS.get(mode, "#06b6d4")

    # Calculate center from sites
    if sites:
        center_lat = sum(s["lat"] for s in sites) / len(sites)
        center_lon = sum(s["lon"] for s in sites) / len(sites)
    else:
        center_lat, center_lon = 20.0, 0.0

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles=None)

    # Dark base layer
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    # Satellite layer option
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Satellite",
        name="Satellite",
        overlay=False,
    ).add_to(m)

    # Add site markers
    for site in sites:
        popup_html = _build_popup_html(site, mode_color)
        radius = 8 if site.get("unesco") else 6

        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=radius,
            color=mode_color,
            fill=True,
            fill_color=mode_color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(str(site.get("name", ""))),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def _build_dataframe(sites: list) -> pd.DataFrame:
    """Build a pandas DataFrame from site list."""
    rows = []
    for s in sites:
        rows.append({
            "Name": s.get("name", ""),
            "Country": s.get("country", ""),
            "Era": s.get("era", ""),
            "Status": s.get("status", ""),
            "UNESCO": "Yes" if s.get("unesco") else "No",
            "Latitude": round(s.get("lat", 0), 4),
            "Longitude": round(s.get("lon", 0), 4),
            "Description": s.get("description", ""),
        })
    return pd.DataFrame(rows)


def _render_stats(sites: list, mode: str):
    """Render a stats metrics row for the current mode."""
    total = len(sites)
    countries = len(set(s.get("country", "") for s in sites))
    unesco_count = sum(1 for s in sites if s.get("unesco"))
    statuses = {}
    for s in sites:
        st_val = s.get("status", "Unknown")
        statuses[st_val] = statuses.get(st_val, 0) + 1
    most_common_status = max(statuses, key=statuses.get) if statuses else "N/A"

    cols = st.columns(4)
    cols[0].metric("Total Sites", total)
    cols[1].metric("Countries", countries)
    cols[2].metric("UNESCO Sites", unesco_count)
    cols[3].metric("Most Common Status", most_common_status)


def _render_chart(sites: list, mode: str):
    """Render a horizontal bar chart of sites by country in dark theme."""
    country_counts = {}
    for s in sites:
        c = s.get("country", "Unknown")
        country_counts[c] = country_counts.get(c, 0) + 1

    if not country_counts:
        return

    sorted_items = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]
    mode_color = MODE_COLORS.get(mode, "#06b6d4")

    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.45)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    bars = ax.barh(range(len(labels)), values, color=mode_color, alpha=0.8)

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", color="#e8ecf4", fontsize=9, fontweight="bold",
        )

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color="#e8ecf4", fontsize=9)
    ax.set_xlabel("Number of Sites", color="#8b97b0", fontsize=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_color("#2a3550")

    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_status_chart(sites: list, mode: str):
    """Render a pie chart of sites by preservation status."""
    status_counts = {}
    for s in sites:
        st_val = s.get("status", "Unknown")
        status_counts[st_val] = status_counts.get(st_val, 0) + 1

    if not status_counts:
        return

    labels = list(status_counts.keys())
    sizes = list(status_counts.values())

    # Color palette for statuses
    palette = [
        "#06b6d4", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6",
        "#ec4899", "#f97316", "#64748b", "#22c55e", "#a1a1aa",
        "#3b82f6", "#e11d48",
    ]
    colors = [palette[i % len(palette)] for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.80,
        textprops={"color": "#e8ecf4", "fontsize": 8},
    )
    for at in autotexts:
        at.set_color("#e8ecf4")
        at.set_fontsize(8)
        at.set_fontweight("bold")

    ax.set_title(
        "Preservation Status", color="#e8ecf4",
        fontsize=11, fontweight="bold", pad=12,
    )
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_distance_matrix(sites: list, mode: str):
    """Render a distance chart showing pairwise distances between sites."""
    if len(sites) < 2:
        return

    mode_color = MODE_COLORS.get(mode, "#06b6d4")
    distances = []
    for i, s1 in enumerate(sites):
        for j, s2 in enumerate(sites):
            if i < j:
                d = _haversine(s1["lat"], s1["lon"], s2["lat"], s2["lon"])
                distances.append({
                    "from": s1["name"],
                    "to": s2["name"],
                    "distance_km": round(d, 1),
                })

    if not distances:
        return

    distances.sort(key=lambda x: x["distance_km"])

    # Show top 10 closest pairs
    top = distances[:10]
    labels = [f"{d['from'][:15]} - {d['to'][:15]}" for d in top]
    vals = [d["distance_km"] for d in top]

    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.45)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    bars = ax.barh(range(len(labels)), vals, color=mode_color, alpha=0.7)
    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_width() + 20, bar.get_y() + bar.get_height() / 2,
            f"{val:,.0f} km", va="center", color="#e8ecf4", fontsize=8,
        )

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color="#e8ecf4", fontsize=8)
    ax.set_xlabel("Distance (km)", color="#8b97b0", fontsize=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.invert_yaxis()
    ax.set_title(
        "Closest Site Pairs", color="#e8ecf4",
        fontsize=11, fontweight="bold", pad=10,
    )
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════
# DETAIL PANEL FOR INDIVIDUAL SITE
# ═══════════════════════════════════════════════════════════════════

def _render_site_detail(site: dict, mode: str):
    """Render a detailed card for a single selected site with nearby
    Overpass data."""
    mode_color = MODE_COLORS.get(mode, "#06b6d4")
    name = escape(str(site.get("name", "Unknown")))
    country = escape(str(site.get("country", "")))
    era = escape(str(site.get("era", "")))
    desc = escape(str(site.get("description", "")))
    status = escape(str(site.get("status", "")))

    unesco_badge = ""
    if site.get("unesco"):
        unesco_badge = (
            '<span style="background:#f59e0b; color:#000; font-size:0.72rem; '
            'padding:2px 8px; border-radius:4px; font-weight:bold; '
            'margin-left:8px;">UNESCO World Heritage</span>'
        )

    st.markdown(f"""
    <div style="background:rgba(15,23,42,0.65); backdrop-filter:blur(16px);
                border:1px solid #2a3550; border-radius:12px; padding:1.2rem;
                margin-bottom:1rem;">
        <div style="display:flex; align-items:center; margin-bottom:0.6rem;">
            <span style="color:{mode_color}; font-size:1.5rem;
                         margin-right:0.6rem;">
                {MODE_ICONS.get(mode, '')}
            </span>
            <span style="color:#e8ecf4; font-size:1.1rem;
                         font-weight:700;">{name}</span>
            {unesco_badge}
        </div>
        <div style="color:#8b97b0; font-size:0.85rem; margin-bottom:0.5rem;">
            {country} &middot; {era} &middot; Status: {status}
        </div>
        <div style="color:#e8ecf4; font-size:0.82rem; line-height:1.5;">
            {desc}
        </div>
        <div style="color:#5a6580; font-size:0.75rem; margin-top:0.5rem;">
            Coordinates: {site.get('lat', 0):.4f}, {site.get('lon', 0):.4f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Zoomed-in map for this site
    site_map = folium.Map(
        location=[site["lat"], site["lon"]],
        zoom_start=14,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(site_map)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Satellite", name="Satellite", overlay=False,
    ).add_to(site_map)

    # Main site marker
    folium.CircleMarker(
        location=[site["lat"], site["lon"]],
        radius=10,
        color=mode_color,
        fill=True,
        fill_color=mode_color,
        fill_opacity=0.8,
        weight=3,
        tooltip=escape(str(site.get("name", ""))),
    ).add_to(site_map)

    # Search Overpass for nearby ruins
    with st.spinner("Searching nearby ruins via OpenStreetMap..."):
        nearby = _search_nearby_ruins(site["lat"], site["lon"], radius_m=5000)

    if nearby:
        for nb in nearby[:30]:
            nb_name = escape(str(nb.get("name", "Unknown")))
            nb_hist = escape(str(nb.get("historic", "")))
            nb_popup = (
                f'<div style="max-width:200px;">'
                f'<strong>{nb_name}</strong><br/>'
                f'<span style="font-size:0.75rem; color:#666;">'
                f'OSM: {nb_hist}</span>'
                f'</div>'
            )
            folium.CircleMarker(
                location=[nb["lat"], nb["lon"]],
                radius=4,
                color="#8b97b0",
                fill=True,
                fill_color="#8b97b0",
                fill_opacity=0.5,
                weight=1,
                popup=folium.Popup(nb_popup, max_width=220),
                tooltip=nb_name,
            ).add_to(site_map)

        st.caption(
            f"Found {len(nearby)} nearby historic features from "
            f"OpenStreetMap (5 km radius)"
        )

    folium.LayerControl().add_to(site_map)
    components.html(site_map._repr_html_(), height=450)


# ═══════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════

def render_ruins_maps_tab():
    """Main render function for the Ruins & Lost Cities Explorer tab."""

    # ── Tab Header ──
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>Ruins & Lost Cities Explorer</h4>'
        '<p>Discover ancient wonders, lost civilizations, abandoned cities, '
        'megalithic monuments, underwater ruins, and ghost towns across the '
        'globe. 10 curated map modes with detailed site data and Overpass '
        'API enrichment.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ═══════════════════════════════════════════
    st.markdown("#### Select Exploration Mode")

    mode = st.selectbox(
        "Map Mode",
        MAP_MODES,
        format_func=lambda m: f"{MODE_ICONS.get(m, '')} {m}",
        key="ruins_mode",
        help="Choose from 10 curated categories of ruins and abandoned places.",
    )

    mode_color = MODE_COLORS.get(mode, "#06b6d4")
    mode_desc = MODE_DESCRIPTIONS.get(mode, "")

    # Mode description card
    st.markdown(f"""
    <div style="background:rgba(15,23,42,0.65); backdrop-filter:blur(16px);
                border:1px solid #2a3550; border-radius:10px; padding:1rem;
                margin-bottom:1rem; border-left:4px solid {mode_color};">
        <div style="color:{mode_color}; font-weight:700; font-size:0.95rem;
                    margin-bottom:0.4rem;">
            {MODE_ICONS.get(mode, '')} {escape(mode)}
        </div>
        <div style="color:#8b97b0; font-size:0.82rem; line-height:1.5;">
            {escape(mode_desc)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Get sites for current mode
    sites = SITES.get(mode, [])
    if not sites:
        st.warning("No data available for this mode.")
        return

    # ═══════════════════════════════════════════
    # SECTION 2: Stats Overview
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Overview")
    _render_stats(sites, mode)

    # ═══════════════════════════════════════════
    # SECTION 3: Interactive World Map
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### World Map")

    # Legend
    legend_html = (
        '<div style="display:flex; gap:0.75rem; flex-wrap:wrap; '
        'margin-bottom:0.5rem;">'
        f'<span style="color:{mode_color}; font-size:0.8rem;">'
        f'\u25cf Curated Site</span>'
        '<span style="color:#f59e0b; font-size:0.8rem;">'
        '\u25cf UNESCO Heritage</span>'
        '</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)

    fmap = _build_folium_map(sites, mode, zoom=3)
    components.html(fmap._repr_html_(), height=500)

    # ═══════════════════════════════════════════
    # SECTION 4: Charts (side by side)
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Analytics")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("##### Sites by Country")
        _render_chart(sites, mode)

    with chart_col2:
        st.markdown("##### Preservation Status")
        _render_status_chart(sites, mode)

    # Distance matrix
    with st.expander("Site Distance Analysis", expanded=False):
        _render_distance_matrix(sites, mode)

    # ═══════════════════════════════════════════
    # SECTION 5: Site Detail Explorer
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Site Detail Explorer")

    site_names = [s["name"] for s in sites]
    selected_site_name = st.selectbox(
        "Select a site for detailed view",
        site_names,
        key="ruins_site_detail",
        help="Choose a site to see a zoomed-in map with nearby ruins "
             "from OpenStreetMap.",
    )

    selected_site = next(
        (s for s in sites if s["name"] == selected_site_name), None,
    )
    if selected_site:
        _render_site_detail(selected_site, mode)

    # ═══════════════════════════════════════════
    # SECTION 6: Data Table
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Complete Data Table")

    df = _build_dataframe(sites)

    # Filter controls
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        country_filter = st.multiselect(
            "Filter by Country",
            sorted(df["Country"].unique()),
            key="ruins_country_filter",
        )
    with filter_col2:
        unesco_filter = st.selectbox(
            "UNESCO Status",
            ["All", "UNESCO Only", "Non-UNESCO Only"],
            key="ruins_unesco_filter",
        )

    filtered_df = df.copy()
    if country_filter:
        filtered_df = filtered_df[filtered_df["Country"].isin(country_filter)]
    if unesco_filter == "UNESCO Only":
        filtered_df = filtered_df[filtered_df["UNESCO"] == "Yes"]
    elif unesco_filter == "Non-UNESCO Only":
        filtered_df = filtered_df[filtered_df["UNESCO"] == "No"]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(filtered_df)} of {len(df)} sites")

    # ═══════════════════════════════════════════
    # SECTION 7: CSV Download
    # ═══════════════════════════════════════════
    csv_buf = io.StringIO()
    filtered_df.to_csv(csv_buf, index=False)
    safe_mode_name = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        f"Download {len(filtered_df)} Sites as CSV",
        data=csv_buf.getvalue(),
        file_name=f"ruins_{safe_mode_name}.csv",
        mime="text/csv",
        key="ruins_csv_download",
    )

    # ═══════════════════════════════════════════
    # SECTION 8: Overpass Live Search
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Live Ruins Search (Overpass API)")
    st.caption(
        "Search for historic ruins and archaeological sites around any "
        "coordinate using OpenStreetMap's Overpass API. This supplements "
        "the curated data above."
    )

    osm_col1, osm_col2, osm_col3 = st.columns([1, 1, 1])
    with osm_col1:
        osm_lat = st.number_input(
            "Latitude", value=41.8933, format="%.4f",
            min_value=-90.0, max_value=90.0, key="ruins_osm_lat",
        )
    with osm_col2:
        osm_lon = st.number_input(
            "Longitude", value=12.4922, format="%.4f",
            min_value=-180.0, max_value=180.0, key="ruins_osm_lon",
        )
    with osm_col3:
        osm_radius = st.slider(
            "Search Radius (km)", 1, 50, 10, key="ruins_osm_radius",
            help="Radius around the center point to search for ruins.",
        )

    # Quick-jump presets
    osm_presets = {
        "Custom": None,
        "Rome, Italy": {"lat": 41.8933, "lon": 12.4922},
        "Athens, Greece": {"lat": 37.9715, "lon": 23.7267},
        "Cairo, Egypt": {"lat": 29.9792, "lon": 31.1342},
        "Cusco, Peru": {"lat": -13.5320, "lon": -71.9675},
        "Siem Reap, Cambodia": {"lat": 13.4125, "lon": 103.8670},
        "Mexico City, Mexico": {"lat": 19.4326, "lon": -99.1332},
        "Istanbul, Turkey": {"lat": 41.0082, "lon": 28.9784},
        "Luxor, Egypt": {"lat": 25.6872, "lon": 32.6396},
        "Jerusalem, Israel": {"lat": 31.7767, "lon": 35.2345},
        "Bagan, Myanmar": {"lat": 21.1717, "lon": 94.8585},
    }

    osm_preset_name = st.selectbox(
        "Quick-Jump Presets",
        list(osm_presets.keys()),
        key="ruins_osm_preset",
    )
    if osm_preset_name != "Custom" and osm_presets.get(osm_preset_name):
        p = osm_presets[osm_preset_name]
        osm_lat = p["lat"]
        osm_lon = p["lon"]

    if st.button(
        "Search Ruins via Overpass",
        key="ruins_osm_search",
        use_container_width=True,
    ):
        st.session_state.ruins_osm_params = {
            "lat": osm_lat, "lon": osm_lon, "radius": osm_radius,
        }

    if "ruins_osm_params" in st.session_state:
        op = st.session_state.ruins_osm_params
        with st.spinner(
            "Querying Overpass API for ruins and archaeological sites..."
        ):
            osm_results = _search_nearby_ruins(
                op["lat"], op["lon"], radius_m=op["radius"] * 1000,
            )

        if not osm_results:
            st.warning(
                "No ruins found in this area. Try a larger radius or "
                "a different location."
            )
        else:
            st.success(
                f"Found {len(osm_results)} historic features from "
                f"OpenStreetMap"
            )

            # Stats
            osm_stat_cols = st.columns(3)
            osm_stat_cols[0].metric("Features Found", len(osm_results))
            hist_types = {}
            for r in osm_results:
                ht = r.get("historic", "unknown")
                hist_types[ht] = hist_types.get(ht, 0) + 1
            top_type = (
                max(hist_types, key=hist_types.get) if hist_types else "N/A"
            )
            osm_stat_cols[1].metric("Top Type", top_type)
            wiki_count = sum(
                1 for r in osm_results if r.get("wikipedia")
            )
            osm_stat_cols[2].metric("With Wikipedia", wiki_count)

            # Map
            osm_map = folium.Map(
                location=[op["lat"], op["lon"]],
                zoom_start=12,
                tiles=None,
            )
            folium.TileLayer(
                tiles="https://{s}.basemaps.cartocdn.com/dark_all/"
                      "{z}/{x}/{y}{r}.png",
                attr="CartoDB Dark", name="Dark Base",
            ).add_to(osm_map)
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/"
                      "services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri Satellite", name="Satellite", overlay=False,
            ).add_to(osm_map)

            # Search radius
            folium.Circle(
                location=[op["lat"], op["lon"]],
                radius=op["radius"] * 1000,
                color="#06b6d4",
                fill=True,
                fill_opacity=0.03,
                weight=1,
            ).add_to(osm_map)

            # OSM result markers
            type_colors = {
                "ruins": "#ef4444",
                "archaeological_site": "#f59e0b",
                "attraction": "#8b5cf6",
            }
            for r in osm_results:
                r_name = escape(str(r.get("name", "Unknown")))
                r_hist = escape(str(r.get("historic", "")))
                r_color = type_colors.get(r.get("historic", ""), "#06b6d4")

                wiki_link = ""
                if r.get("wikipedia"):
                    wp = r["wikipedia"]
                    lang, title = (
                        wp.split(":", 1) if ":" in wp else ("en", wp)
                    )
                    safe_title = escape(title)
                    safe_lang = escape(lang)
                    wiki_link = (
                        f'<br/><a href="https://{safe_lang}'
                        f'.wikipedia.org/wiki/{safe_title}" '
                        f'target="_blank" '
                        f'style="font-size:0.7rem;">Wikipedia</a>'
                    )

                osm_popup = (
                    f'<div style="max-width:220px;">'
                    f'<strong>{r_name}</strong><br/>'
                    f'<span style="font-size:0.78rem; color:#666;">'
                    f'Type: {r_hist}</span>'
                    f'{wiki_link}'
                    f'<br/><span style="font-size:0.7rem; color:#888;">'
                    f'{r["lat"]:.4f}, {r["lon"]:.4f}</span>'
                    f'</div>'
                )

                folium.CircleMarker(
                    location=[r["lat"], r["lon"]],
                    radius=6,
                    color=r_color,
                    fill=True,
                    fill_color=r_color,
                    fill_opacity=0.7,
                    weight=2,
                    popup=folium.Popup(osm_popup, max_width=240),
                    tooltip=r_name,
                ).add_to(osm_map)

            folium.LayerControl().add_to(osm_map)
            components.html(osm_map._repr_html_(), height=500)

            # OSM Results Table
            osm_rows = []
            for r in osm_results:
                osm_rows.append({
                    "Name": r.get("name", ""),
                    "Type": r.get("historic", ""),
                    "Wikipedia": r.get("wikipedia", ""),
                    "Latitude": round(r.get("lat", 0), 4),
                    "Longitude": round(r.get("lon", 0), 4),
                })
            osm_df = pd.DataFrame(osm_rows)

            with st.expander(
                f"OSM Data Table ({len(osm_df)} features)",
                expanded=False,
            ):
                st.dataframe(
                    osm_df, use_container_width=True, hide_index=True,
                )

            # OSM CSV Download
            osm_csv_buf = io.StringIO()
            osm_df.to_csv(osm_csv_buf, index=False)
            st.download_button(
                f"Download {len(osm_df)} OSM Features (CSV)",
                data=osm_csv_buf.getvalue(),
                file_name="ruins_osm_search.csv",
                mime="text/csv",
                key="ruins_osm_csv_download",
            )

    # ═══════════════════════════════════════════
    # SECTION 9: Mode Comparison
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Cross-Mode Comparison")

    compare_modes = st.multiselect(
        "Select modes to compare",
        MAP_MODES,
        default=[mode],
        key="ruins_compare_modes",
    )

    if compare_modes:
        compare_data = []
        for cm in compare_modes:
            cm_sites = SITES.get(cm, [])
            compare_data.append({
                "Mode": cm,
                "Total Sites": len(cm_sites),
                "Countries": len(
                    set(s.get("country", "") for s in cm_sites)
                ),
                "UNESCO Sites": sum(
                    1 for s in cm_sites if s.get("unesco")
                ),
                "Avg Latitude": round(
                    sum(s["lat"] for s in cm_sites)
                    / max(len(cm_sites), 1), 2,
                ),
                "Avg Longitude": round(
                    sum(s["lon"] for s in cm_sites)
                    / max(len(cm_sites), 1), 2,
                ),
            })
        compare_df = pd.DataFrame(compare_data)
        st.dataframe(
            compare_df, use_container_width=True, hide_index=True,
        )

        # Comparison chart
        if len(compare_modes) > 1:
            fig, ax = plt.subplots(figsize=(8, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#111827")

            mode_labels = [d["Mode"] for d in compare_data]
            total_vals = [d["Total Sites"] for d in compare_data]
            unesco_vals = [d["UNESCO Sites"] for d in compare_data]
            bar_colors = [
                MODE_COLORS.get(m, "#06b6d4") for m in mode_labels
            ]

            x = range(len(mode_labels))
            width = 0.35
            ax.bar(
                [i - width / 2 for i in x], total_vals, width,
                label="Total", color=bar_colors, alpha=0.8,
            )
            ax.bar(
                [i + width / 2 for i in x], unesco_vals, width,
                label="UNESCO", color="#f59e0b", alpha=0.8,
            )

            ax.set_xticks(list(x))
            ax.set_xticklabels(
                [m[:15] for m in mode_labels],
                color="#e8ecf4", fontsize=8, rotation=30, ha="right",
            )
            ax.set_ylabel("Count", color="#8b97b0", fontsize=10)
            ax.tick_params(axis="y", colors="#8b97b0", labelsize=9)
            ax.grid(
                True, axis="y", color="#2a3550",
                linewidth=0.5, alpha=0.7,
            )
            ax.set_axisbelow(True)
            ax.legend(
                facecolor="#111827", edgecolor="#2a3550",
                labelcolor="#e8ecf4", fontsize=9,
            )
            for spine in ax.spines.values():
                spine.set_color("#2a3550")
            ax.set_title(
                "Mode Comparison", color="#e8ecf4",
                fontsize=11, fontweight="bold", pad=10,
            )
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # ═══════════════════════════════════════════
    # SECTION 10: Summary & Full Download
    # ═══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Full Database Export")
    st.caption(
        "Download the complete curated database of all sites across "
        "all 10 modes."
    )

    all_rows = []
    for m_name, m_sites in SITES.items():
        for s in m_sites:
            all_rows.append({
                "Mode": m_name,
                "Name": s.get("name", ""),
                "Country": s.get("country", ""),
                "Era": s.get("era", ""),
                "Status": s.get("status", ""),
                "UNESCO": "Yes" if s.get("unesco") else "No",
                "Latitude": round(s.get("lat", 0), 4),
                "Longitude": round(s.get("lon", 0), 4),
                "Description": s.get("description", ""),
            })
    all_df = pd.DataFrame(all_rows)

    all_stat_cols = st.columns(4)
    all_stat_cols[0].metric("Total Sites (All Modes)", len(all_df))
    all_stat_cols[1].metric(
        "Total Countries", len(all_df["Country"].unique()),
    )
    all_stat_cols[2].metric(
        "UNESCO Sites", len(all_df[all_df["UNESCO"] == "Yes"]),
    )
    all_stat_cols[3].metric("Exploration Modes", len(MAP_MODES))

    with st.expander(
        f"Full Database ({len(all_df)} sites across "
        f"{len(MAP_MODES)} modes)",
        expanded=False,
    ):
        st.dataframe(
            all_df, use_container_width=True, hide_index=True,
        )

    all_csv_buf = io.StringIO()
    all_df.to_csv(all_csv_buf, index=False)
    st.download_button(
        f"Download Complete Database ({len(all_df)} Sites, CSV)",
        data=all_csv_buf.getvalue(),
        file_name="ruins_complete_database.csv",
        mime="text/csv",
        key="ruins_full_csv_download",
    )
