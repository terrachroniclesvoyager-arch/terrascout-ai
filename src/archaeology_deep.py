# -*- coding: utf-8 -*-
"""
Archaeological Deep Dive module for TerraScout AI.
Ancient wonders, megalithic sites, lost civilizations & archaeological treasures.
Combines curated databases of world-famous sites with live API queries
(Overpass API for Roman sites, Paleobiology Database for fossils).
"""

import io
import logging
import streamlit as st
import requests
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

# ═══════════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_MUTED = "#5a6580"
_GRID = "#2a3550"
_ACCENT = "#06b6d4"

# ═══════════════════════════════════════════════════════════════════════
# MODE 1: SEVEN WONDERS (Ancient + New)
# ═══════════════════════════════════════════════════════════════════════
SEVEN_WONDERS = [
    # Ancient Seven Wonders
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342,
     "period": "c. 2560 BC", "country": "Egypt",
     "description": "Last surviving Ancient Wonder. Tomb of Pharaoh Khufu, 146m tall for 3,800 years the tallest structure on Earth."},
    {"name": "Hanging Gardens of Babylon", "lat": 32.5355, "lon": 44.4275,
     "period": "c. 600 BC", "country": "Iraq",
     "description": "Legendary tiered gardens attributed to Nebuchadnezzar II. Existence debated by scholars; possibly located at Nineveh."},
    {"name": "Statue of Zeus at Olympia", "lat": 37.6380, "lon": 21.6300,
     "period": "c. 435 BC", "country": "Greece",
     "description": "Giant seated figure of Zeus by Phidias, 13m tall, chryselephantine (ivory and gold). Destroyed by fire in 5th century AD."},
    {"name": "Temple of Artemis at Ephesus", "lat": 37.9498, "lon": 27.3639,
     "period": "c. 550 BC", "country": "Turkey",
     "description": "Grand Greek temple dedicated to Artemis, rebuilt three times. Only a single column remains today at Selcuk."},
    {"name": "Mausoleum at Halicarnassus", "lat": 37.0380, "lon": 27.4241,
     "period": "c. 351 BC", "country": "Turkey",
     "description": "Tomb of Mausolus, satrap of Caria. 45m tall, adorned with sculptural reliefs. Origin of the word 'mausoleum'."},
    {"name": "Colossus of Rhodes", "lat": 36.4511, "lon": 28.2278,
     "period": "c. 280 BC", "country": "Greece",
     "description": "Bronze statue of sun god Helios, approximately 33m tall. Stood for only 54 years before earthquake toppled it."},
    {"name": "Lighthouse of Alexandria (Pharos)", "lat": 31.2139, "lon": 29.8856,
     "period": "c. 280 BC", "country": "Egypt",
     "description": "One of tallest structures in the ancient world at 100-137m. Guided sailors for 1,500 years before earthquakes destroyed it."},
    # New Seven Wonders of the World
    {"name": "Great Wall of China", "lat": 40.4319, "lon": 116.5704,
     "period": "7th century BC - 1644 AD", "country": "China",
     "description": "Series of fortifications spanning 21,196 km. Built over centuries to protect against nomadic invasions from the north."},
    {"name": "Petra", "lat": 30.3285, "lon": 35.4444,
     "period": "c. 312 BC", "country": "Jordan",
     "description": "Rose-red city carved into sandstone cliffs by the Nabataeans. Famous Treasury (Al-Khazneh) facade is 40m tall."},
    {"name": "Christ the Redeemer", "lat": -22.9519, "lon": -43.2105,
     "period": "1922-1931 AD", "country": "Brazil",
     "description": "Art Deco statue of Jesus Christ, 30m tall atop Corcovado mountain. Symbol of Rio de Janeiro and Christianity."},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450,
     "period": "c. 1450 AD", "country": "Peru",
     "description": "Inca citadel set high in the Andes at 2,430m. Sophisticated dry-stone construction with panoramic terraces."},
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678,
     "period": "c. 600 AD", "country": "Mexico",
     "description": "Major Maya city featuring the Kukulkan pyramid (El Castillo). Equinox shadow creates feathered serpent illusion."},
    {"name": "Colosseum (Rome)", "lat": 41.8902, "lon": 12.4922,
     "period": "70-80 AD", "country": "Italy",
     "description": "Largest ancient amphitheatre, seating 50,000-80,000 spectators. Arena for gladiatorial contests and public spectacles."},
    {"name": "Taj Mahal", "lat": 27.1751, "lon": 78.0421,
     "period": "1632-1653 AD", "country": "India",
     "description": "White marble mausoleum built by Shah Jahan for wife Mumtaz Mahal. Pinnacle of Mughal architecture."},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 2: MEGALITHIC SITES
# ═══════════════════════════════════════════════════════════════════════
MEGALITHIC_SITES = [
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "period": "3000-2000 BC", "country": "England", "description": "Prehistoric ring of standing stones; aligned with solstice sunrise. Bluestones transported 250 km from Wales."},
    {"name": "Carnac Stones", "lat": 47.5950, "lon": -3.0750, "period": "4500-3300 BC", "country": "France", "description": "Over 3,000 megalithic standing stones arranged in rows stretching 4 km across Brittany."},
    {"name": "Gobekli Tepe", "lat": 37.2231, "lon": 38.9225, "period": "9500 BC", "country": "Turkey", "description": "World's oldest known megalithic temple complex, 6,000 years older than Stonehenge. Massive T-shaped pillars with animal carvings."},
    {"name": "Easter Island (Rapa Nui)", "lat": -27.1127, "lon": -109.3497, "period": "1250-1500 AD", "country": "Chile", "description": "Nearly 900 monolithic Moai statues carved by Rapa Nui people, averaging 4m tall and 12.5 tonnes."},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4755, "period": "3200 BC", "country": "Ireland", "description": "Passage tomb older than the pyramids. Winter solstice sunrise illuminates inner chamber through roof box."},
    {"name": "Avebury", "lat": 51.4288, "lon": -1.8544, "period": "2850-2200 BC", "country": "England", "description": "Largest stone circle in Europe, enclosing a village. Part of UNESCO World Heritage complex with Stonehenge."},
    {"name": "Callanish Stones", "lat": 58.1975, "lon": -6.7456, "period": "2900-2600 BC", "country": "Scotland", "description": "Cruciform setting of standing stones on Isle of Lewis, aligned with the lunar cycle."},
    {"name": "Dolmen de Menga", "lat": 37.0237, "lon": -4.5480, "period": "3750-3650 BC", "country": "Spain", "description": "One of largest known megalithic structures in Europe. Burial chamber with 180-tonne capstone."},
    {"name": "Almendres Cromlech", "lat": 38.5569, "lon": -8.0617, "period": "6000-4000 BC", "country": "Portugal", "description": "One of oldest megalithic complexes in Iberia, with 95 standing stones arranged in elliptical patterns."},
    {"name": "Skara Brae", "lat": 59.0488, "lon": -3.3415, "period": "3180-2500 BC", "country": "Scotland", "description": "Neolithic settlement older than Stonehenge and the Great Pyramids. Stone furniture and covered passages preserved."},
    {"name": "Mnajdra Temples", "lat": 35.8267, "lon": 14.4361, "period": "3600-2500 BC", "country": "Malta", "description": "Megalithic temple complex aligned with equinox sunrises. Among the oldest freestanding structures on Earth."},
    {"name": "Ggantija Temples", "lat": 36.0478, "lon": 14.2689, "period": "3600-3200 BC", "country": "Malta", "description": "Two megalithic temples predating the Egyptian pyramids. Name means 'Giant's Tower' in Maltese."},
    {"name": "Hagar Qim", "lat": 35.8275, "lon": 14.4419, "period": "3600-2500 BC", "country": "Malta", "description": "Megalithic temple on a hilltop overlooking the sea. Features a large stone weighing 20 tonnes."},
    {"name": "Ring of Brodgar", "lat": 59.0015, "lon": -3.2298, "period": "2500-2000 BC", "country": "Scotland", "description": "Neolithic stone circle of 60 stones (27 surviving), 104m diameter, set between two lochs in Orkney."},
    {"name": "Baalbek (Heliopolis)", "lat": 34.0069, "lon": 36.2039, "period": "9000 BC (platform)", "country": "Lebanon", "description": "Roman temple complex built on massive megalithic platform. Trilithon stones weigh 800 tonnes each."},
    {"name": "Tiya Stelae", "lat": 8.4333, "lon": 38.6167, "period": "10th-15th century AD", "country": "Ethiopia", "description": "UNESCO site with 36 standing stones, some with enigmatic sword carvings. Purpose still debated."},
    {"name": "Larabanga Mosque Stones", "lat": 9.2146, "lon": -1.8530, "period": "1421 AD", "country": "Ghana", "description": "Mysterious stones near the oldest mosque in Ghana, associated with local megalithic traditions."},
    {"name": "Plain of Jars", "lat": 19.4333, "lon": 103.1667, "period": "500 BC - 500 AD", "country": "Laos", "description": "Thousands of stone jars up to 3m tall scattered across the Xieng Khouang plateau. Likely funerary urns."},
    {"name": "Dolmen of Bagneux", "lat": 47.2500, "lon": -0.0833, "period": "3000 BC", "country": "France", "description": "One of the largest dolmens in France, 23m long with massive capstones forming a corridor."},
    {"name": "Poulnabrone Dolmen", "lat": 53.0488, "lon": -9.1398, "period": "4200-2900 BC", "country": "Ireland", "description": "Portal tomb in the Burren with remains of 33 individuals found. Iconic Irish megalithic monument."},
    {"name": "Great Dolmen of Zambujeiro", "lat": 38.5603, "lon": -7.9258, "period": "4000-3000 BC", "country": "Portugal", "description": "Tallest dolmen in the Iberian Peninsula at 8m high. Chamber formed by seven massive granite slabs."},
    {"name": "Ales Stenar", "lat": 55.3836, "lon": 14.0531, "period": "600 AD (debated)", "country": "Sweden", "description": "Ship-shaped megalithic monument of 59 boulders, 67m long, overlooking the Baltic Sea."},
    {"name": "Nuraghe Su Nuraxi", "lat": 39.7081, "lon": 8.9908, "period": "1500 BC", "country": "Italy (Sardinia)", "description": "Bronze Age megalithic fortress, finest example of Nuragic civilization. Tower complex with surrounding village."},
    {"name": "Rujm el-Hiri (Gilgal Refaim)", "lat": 32.9928, "lon": 35.8219, "period": "3000-2700 BC", "country": "Israel (Golan Heights)", "description": "Concentric stone circles resembling a bullseye, 150m across. Possibly an ancient astronomical observatory."},
    {"name": "Gunung Padang", "lat": -6.9944, "lon": 107.0567, "period": "Possibly 9000+ BC", "country": "Indonesia", "description": "Controversial megalithic site on a volcanic hill in Java. Some researchers claim it is the oldest pyramid."},
    {"name": "Wainyapu Megalithic Village", "lat": -9.6600, "lon": 119.3400, "period": "Ongoing tradition", "country": "Indonesia (Sumba)", "description": "Living megalithic culture where stone tombs and monuments are still erected for chiefs and nobles."},
    {"name": "Bada Valley Megaliths", "lat": -1.7500, "lon": 120.2000, "period": "1000 BC - 1300 AD", "country": "Indonesia (Sulawesi)", "description": "Mysterious stone statues and kalamba (stone vats) scattered across a remote highland valley."},
    {"name": "Cromeleque dos Almendres", "lat": 38.5564, "lon": -8.0625, "period": "6000 BC", "country": "Portugal", "description": "Oldest stone circle complex in the Iberian Peninsula, predating Stonehenge by millennia."},
    {"name": "Carnac Menhir (Grand Menhir Brise)", "lat": 47.5764, "lon": -3.0953, "period": "4500 BC", "country": "France", "description": "Once the largest known menhir at 20m and 280 tonnes. Now broken into four pieces."},
    {"name": "Brownshill Dolmen", "lat": 52.8280, "lon": -6.8850, "period": "4000-3000 BC", "country": "Ireland", "description": "Holds the heaviest capstone in Europe at approximately 100-150 tonnes."},
    {"name": "Senegambian Stone Circles", "lat": 13.6914, "lon": -15.5280, "period": "3rd century BC - 16th century AD", "country": "Senegal/Gambia", "description": "Over 1,000 stone circles across 93 sites. Largest concentration of megalithic circles in the world. UNESCO site."},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 3: ANCIENT LOST CITIES
# ═══════════════════════════════════════════════════════════════════════
LOST_CITIES = [
    {"name": "Pompeii", "lat": 40.7509, "lon": 14.4869, "period": "7th century BC - 79 AD", "country": "Italy", "description": "Roman city buried under 6m of volcanic ash by Mount Vesuvius eruption. Remarkably preserved time capsule."},
    {"name": "Petra", "lat": 30.3285, "lon": 35.4444, "period": "312 BC - 106 AD", "country": "Jordan", "description": "Nabataean rock-cut city, lost to the Western world until 1812. Half-built, half-carved into rose-red cliffs."},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "period": "c. 1450 AD", "country": "Peru", "description": "Inca royal estate abandoned during Spanish Conquest, rediscovered by Hiram Bingham in 1911."},
    {"name": "Angkor", "lat": 13.4125, "lon": 103.8670, "period": "9th-15th century AD", "country": "Cambodia", "description": "Vast Khmer empire capital with 1,000+ temples including Angkor Wat. Once the largest pre-industrial city in the world."},
    {"name": "Troy", "lat": 39.9575, "lon": 26.2389, "period": "3000 BC - 500 AD", "country": "Turkey", "description": "Legendary city of Homer's Iliad with nine archaeological layers. Rediscovered by Heinrich Schliemann in 1870s."},
    {"name": "Mohenjo-daro", "lat": 27.3242, "lon": 68.1361, "period": "2500-1900 BC", "country": "Pakistan", "description": "Major Indus Valley Civilization city with advanced urban planning, drainage systems, and public baths."},
    {"name": "Herculaneum", "lat": 40.8059, "lon": 14.3480, "period": "Pre-Roman - 79 AD", "country": "Italy", "description": "Sister city of Pompeii, better preserved by pyroclastic flow. Carbonized scrolls and wooden structures survive."},
    {"name": "Great Zimbabwe", "lat": -20.2674, "lon": 30.9339, "period": "11th-15th century AD", "country": "Zimbabwe", "description": "Medieval stone city, largest ancient structure in sub-Saharan Africa. Capital of Kingdom of Zimbabwe."},
    {"name": "Palmyra", "lat": 34.5503, "lon": 38.2691, "period": "2nd millennium BC - 7th century AD", "country": "Syria", "description": "Caravan oasis city blending Greco-Roman and Persian styles. Queen Zenobia briefly challenged Rome."},
    {"name": "Ephesus", "lat": 37.9411, "lon": 27.3419, "period": "10th century BC - 15th century AD", "country": "Turkey", "description": "One of the largest Roman cities, home to the Temple of Artemis. Library of Celsus facade still stands."},
    {"name": "Babylon", "lat": 32.5355, "lon": 44.4275, "period": "2300 BC - 275 BC", "country": "Iraq", "description": "Legendary Mesopotamian city under Hammurabi and Nebuchadnezzar. Ishtar Gate and Hanging Gardens fame."},
    {"name": "Persepolis", "lat": 29.9352, "lon": 52.8906, "period": "515-330 BC", "country": "Iran", "description": "Ceremonial capital of the Achaemenid Empire. Burned by Alexander the Great in 330 BC. Monumental ruins survive."},
    {"name": "Tenochtitlan (Mexico City)", "lat": 19.4326, "lon": -99.1332, "period": "1325-1521 AD", "country": "Mexico", "description": "Aztec island capital on Lake Texcoco with 200,000 inhabitants. Larger than most European cities of its time."},
    {"name": "Carthage", "lat": 36.8528, "lon": 10.3233, "period": "814 BC - 698 AD", "country": "Tunisia", "description": "Phoenician then Roman city, rival of Rome. Destroyed and rebuilt. Punic harbors and Antonine Baths remain."},
    {"name": "Knidos", "lat": 36.6881, "lon": 27.3756, "period": "400 BC - Byzantine era", "country": "Turkey", "description": "Ancient Greek city known for its medical school and the famous Aphrodite statue by Praxiteles."},
    {"name": "Leptis Magna", "lat": 32.6378, "lon": 14.2928, "period": "7th century BC - 7th century AD", "country": "Libya", "description": "One of the best-preserved Roman cities. Birthplace of Emperor Septimius Severus. Spectacular arch and basilica."},
    {"name": "Timgad", "lat": 35.4847, "lon": 6.4683, "period": "100 AD", "country": "Algeria", "description": "Roman colonial town in North Africa with perfect grid plan. Trajan's Arch and Capitoline temple intact."},
    {"name": "Palenque", "lat": 17.4838, "lon": -92.0462, "period": "226-799 AD", "country": "Mexico", "description": "Classic Maya city-state in Chiapas jungle. Temple of the Inscriptions contains Pakal the Great's tomb."},
    {"name": "Harappa", "lat": 30.6310, "lon": 72.8640, "period": "2600-1900 BC", "country": "Pakistan", "description": "Major Indus Valley city that gave the civilization its name. Grid streets, granaries, and standardized bricks."},
    {"name": "Sukhothai", "lat": 17.0200, "lon": 99.7022, "period": "1238-1438 AD", "country": "Thailand", "description": "First capital of Siam. Elegant Buddha statues, lotus-bud stupas, and the invention of Thai script attributed here."},
    {"name": "Taxila", "lat": 33.7458, "lon": 72.7900, "period": "600 BC - 500 AD", "country": "Pakistan", "description": "Gandharan city and ancient university. Visited by Alexander the Great. Blend of Greek, Buddhist, and Hindu art."},
    {"name": "Ctesiphon", "lat": 33.0925, "lon": 44.5814, "period": "120 BC - 637 AD", "country": "Iraq", "description": "Capital of the Parthian and Sassanid Empires. Taq Kasra arch has the largest single-span unreinforced brick vault."},
    {"name": "Hattusa", "lat": 40.0197, "lon": 34.6158, "period": "1600-1178 BC", "country": "Turkey", "description": "Capital of the Hittite Empire. Massive stone walls, Lion Gate, and thousands of cuneiform tablets found."},
    {"name": "Akrotiri (Santorini)", "lat": 36.3517, "lon": 25.4033, "period": "4500-1627 BC", "country": "Greece", "description": "Minoan Bronze Age settlement buried by Thera volcanic eruption. Stunning frescoes and multi-story buildings preserved."},
    {"name": "Caral", "lat": -10.8933, "lon": -77.5206, "period": "3000-1800 BC", "country": "Peru", "description": "Oldest known city in the Americas. Complex of pyramids, sunken plazas, and quipus in the Supe Valley."},
    {"name": "Nan Madol", "lat": 6.8439, "lon": 158.3350, "period": "1200-1500 AD", "country": "Micronesia", "description": "Venice of the Pacific: city of artificial islands built on a coral reef with basalt log-cabin walls."},
    {"name": "Derinkuyu Underground City", "lat": 38.3736, "lon": 34.7347, "period": "8th-7th century BC", "country": "Turkey", "description": "Multi-level underground city in Cappadocia reaching 60m depth, capable of sheltering 20,000 people."},
    {"name": "Chan Chan", "lat": -8.1067, "lon": -79.0747, "period": "850-1470 AD", "country": "Peru", "description": "Largest pre-Columbian city in South America. Chimu capital made of adobe with intricate friezes."},
    {"name": "Sanchi", "lat": 23.4793, "lon": 77.7397, "period": "3rd century BC - 12th century AD", "country": "India", "description": "Buddhist monuments including the Great Stupa, oldest stone structure in India. Ashoka period origin."},
    {"name": "Sigiriya", "lat": 7.9572, "lon": 80.7600, "period": "5th century AD", "country": "Sri Lanka", "description": "Ancient rock fortress and palace on a 200m column of rock. Mirror wall, frescoes, and lion gate remain."},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 4: EGYPTIAN PYRAMIDS & TEMPLES
# ═══════════════════════════════════════════════════════════════════════
EGYPT_SITES = [
    {"name": "Great Pyramid of Giza (Khufu)", "lat": 29.9792, "lon": 31.1342, "period": "c. 2560 BC", "country": "Egypt", "description": "Largest of the three Giza pyramids. 146m original height, 2.3 million limestone blocks, each averaging 2.5 tonnes."},
    {"name": "Pyramid of Khafre", "lat": 29.9761, "lon": 31.1308, "period": "c. 2520 BC", "country": "Egypt", "description": "Second-largest Giza pyramid, appears taller due to higher elevation. Retains limestone casing at its peak."},
    {"name": "Pyramid of Menkaure", "lat": 29.9726, "lon": 31.1280, "period": "c. 2490 BC", "country": "Egypt", "description": "Smallest of the three main Giza pyramids at 65m. Lower courses clad in Aswan granite."},
    {"name": "Great Sphinx of Giza", "lat": 29.9753, "lon": 31.1376, "period": "c. 2500 BC", "country": "Egypt", "description": "Largest monolith statue in the world. Lion body with human head (likely Khafre), 73m long, 20m high."},
    {"name": "Step Pyramid of Djoser (Saqqara)", "lat": 29.8713, "lon": 31.2164, "period": "c. 2670 BC", "country": "Egypt", "description": "Oldest complete hewn-stone building. Designed by architect Imhotep. Six mastabas stacked to 62m height."},
    {"name": "Bent Pyramid (Dahshur)", "lat": 29.7903, "lon": 31.2094, "period": "c. 2600 BC", "country": "Egypt", "description": "Unique double-angled pyramid transitioning from 54 to 43 degrees. Sneferu's experimental pyramid."},
    {"name": "Red Pyramid (Dahshur)", "lat": 29.8092, "lon": 31.2061, "period": "c. 2590 BC", "country": "Egypt", "description": "First true smooth-sided pyramid. Named for reddish limestone. Sneferu's final resting place."},
    {"name": "Karnak Temple Complex", "lat": 25.7188, "lon": 32.6573, "period": "2055 BC - 100 AD", "country": "Egypt", "description": "Largest ancient religious complex. Great Hypostyle Hall has 134 columns, each 23m tall, in 5,000 sq. m."},
    {"name": "Luxor Temple", "lat": 25.6995, "lon": 32.6392, "period": "1400 BC", "country": "Egypt", "description": "Dedicated to Amun-Ra, built primarily by Amenhotep III and Ramesses II. Avenue of Sphinxes connects to Karnak."},
    {"name": "Abu Simbel", "lat": 22.3369, "lon": 31.6256, "period": "1264 BC", "country": "Egypt", "description": "Twin rock temples of Ramesses II. Four 20m seated colossi. Relocated 65m uphill in 1968 to save from Aswan Dam."},
    {"name": "Valley of the Kings", "lat": 25.7402, "lon": 32.6014, "period": "1539-1075 BC", "country": "Egypt", "description": "Royal necropolis with 63 tombs including Tutankhamun. Cut deep into limestone on the Theban west bank."},
    {"name": "Valley of the Queens", "lat": 25.7281, "lon": 32.5986, "period": "1279-1213 BC", "country": "Egypt", "description": "Burial site for queens and princes. Tomb of Nefertari is considered the most beautiful in all Egypt."},
    {"name": "Temple of Hatshepsut (Deir el-Bahari)", "lat": 25.7381, "lon": 32.6075, "period": "c. 1470 BC", "country": "Egypt", "description": "Mortuary temple of female pharaoh Hatshepsut. Three colonnaded terraces cut into cliff face."},
    {"name": "Philae Temple (Agilkia Island)", "lat": 24.0264, "lon": 32.8842, "period": "380-362 BC", "country": "Egypt", "description": "Island temple dedicated to Isis. Last functioning ancient Egyptian temple until 6th century AD. Relocated from Philae island."},
    {"name": "Edfu Temple (Temple of Horus)", "lat": 24.9781, "lon": 32.8733, "period": "237-57 BC", "country": "Egypt", "description": "Best-preserved ancient temple in Egypt. Ptolemaic period. 36m tall pylons with falcon god Horus statues."},
    {"name": "Kom Ombo Temple", "lat": 24.4522, "lon": 32.9281, "period": "180-47 BC", "country": "Egypt", "description": "Unusual double temple dedicated to both Sobek (crocodile god) and Horus. Symmetrical twin design."},
    {"name": "Dendera Temple Complex", "lat": 26.1425, "lon": 32.6700, "period": "2250 BC - Roman era", "country": "Egypt", "description": "Temple of Hathor with famous zodiac ceiling. One of best-preserved roof structures in Egypt."},
    {"name": "Abydos (Temple of Seti I)", "lat": 26.1850, "lon": 31.9186, "period": "1279 BC", "country": "Egypt", "description": "One of the most important archaeological sites. Contains King List and Osireion (underground temple)."},
    {"name": "Colossi of Memnon", "lat": 25.7206, "lon": 32.6103, "period": "1350 BC", "country": "Egypt", "description": "Twin 18m stone statues of Amenhotep III guarding his now-destroyed mortuary temple."},
    {"name": "Pyramid of Meidum", "lat": 29.3881, "lon": 31.1569, "period": "c. 2610 BC", "country": "Egypt", "description": "Transitional pyramid between step and true forms. Now appears as a three-stepped tower rising from sand."},
    {"name": "Temple of Isis (Philae)", "lat": 24.0264, "lon": 32.8842, "period": "380 BC - 6th century AD", "country": "Egypt", "description": "Main temple complex at Philae, center of Isis worship. Contains the last known hieroglyphic inscription."},
    {"name": "Medinet Habu", "lat": 25.7197, "lon": 32.6006, "period": "1150 BC", "country": "Egypt", "description": "Mortuary temple of Ramesses III with vivid battle reliefs. Best preserved temple on Theban west bank."},
    {"name": "Unfinished Obelisk (Aswan)", "lat": 24.0739, "lon": 32.8975, "period": "c. 1490 BC", "country": "Egypt", "description": "Largest known ancient obelisk, abandoned in quarry due to crack. Would have been 42m tall and 1,200 tonnes."},
    {"name": "Temple of Amada", "lat": 22.7300, "lon": 31.9950, "period": "c. 1427 BC", "country": "Egypt", "description": "Oldest surviving temple in Nubia. Built by Thutmose III, with fine painted reliefs inside."},
    {"name": "Tanis (San el-Hagar)", "lat": 30.9778, "lon": 31.8833, "period": "1070-712 BC", "country": "Egypt", "description": "Capital of Egypt during 21st-22nd dynasties. Royal tombs with gold burial masks rivaling Tutankhamun."},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 6: UNDERWATER ARCHAEOLOGY
# ═══════════════════════════════════════════════════════════════════════
UNDERWATER_SITES = [
    {"name": "RMS Titanic", "lat": 41.7258, "lon": -49.9469, "period": "Sunk 1912", "country": "Atlantic Ocean", "description": "Most famous shipwreck. Lies at 3,800m depth, 600 km south of Newfoundland. Discovered by Robert Ballard in 1985."},
    {"name": "Bismarck", "lat": 48.1667, "lon": -16.2000, "period": "Sunk 1941", "country": "Atlantic Ocean", "description": "German WWII battleship sunk after epic chase. Rests at 4,790m depth, 960 km west of Brest, France."},
    {"name": "Dwarka (Legendary City)", "lat": 22.2394, "lon": 68.9678, "period": "c. 1500 BC", "country": "India", "description": "Submerged city in Gulf of Kutch. Hindu tradition identifies it as Lord Krishna's kingdom. Stone structures found underwater."},
    {"name": "Pavlopetri", "lat": 36.5186, "lon": 22.5519, "period": "3000-1000 BC", "country": "Greece", "description": "Oldest known submerged city. Bronze Age settlement with streets, buildings, and tombs visible on seabed at 4m depth."},
    {"name": "Yonaguni Monument", "lat": 24.4350, "lon": 122.9342, "period": "Debated (8000+ BC?)", "country": "Japan", "description": "Massive underwater rock formation off Yonaguni Island. Debated whether natural or man-made stepped pyramid structure."},
    {"name": "Port Royal", "lat": 17.9350, "lon": -76.8419, "period": "Sunk 1692", "country": "Jamaica", "description": "Richest and most sinful city of its age. Two-thirds sank into sea during 1692 earthquake. Pirate capital."},
    {"name": "Heracleion (Thonis)", "lat": 31.3053, "lon": 30.1025, "period": "8th century BC - 8th century AD", "country": "Egypt", "description": "Ancient Egyptian port city in Abu Qir Bay. Rediscovered in 2000. Giant statues, temples, and ships found."},
    {"name": "Cleopatra's Palace (Alexandria)", "lat": 31.2100, "lon": 29.8856, "period": "305-30 BC", "country": "Egypt", "description": "Royal quarters of Ptolemaic Alexandria submerged by earthquakes. Sphinxes, columns, and statuary found offshore."},
    {"name": "Baiae (Roman Resort)", "lat": 40.8198, "lon": 14.0781, "period": "1st century BC", "country": "Italy", "description": "Luxurious Roman resort submerged by bradyseism. Villas, sculptures, mosaics visible in shallow water near Naples."},
    {"name": "SS Thistlegorm", "lat": 27.8133, "lon": 33.9208, "period": "Sunk 1941", "country": "Red Sea, Egypt", "description": "British WWII transport ship. One of world's best wreck dives. Trucks, motorcycles, and munitions still aboard."},
    {"name": "HMS Hood", "lat": 63.3333, "lon": -31.8333, "period": "Sunk 1941", "country": "Denmark Strait", "description": "British battlecruiser sunk by Bismarck. Only 3 of 1,418 crew survived. Rests at 2,800m in three sections."},
    {"name": "Antikythera Shipwreck", "lat": 35.8767, "lon": 23.3100, "period": "c. 60 BC", "country": "Greece", "description": "Ancient Roman cargo ship yielded the Antikythera Mechanism, world's oldest known analog computer."},
    {"name": "Lake Titicaca Offerings", "lat": -16.0206, "lon": -69.3194, "period": "500 AD+", "country": "Bolivia/Peru", "description": "Underwater Tiwanaku and Inca offerings found near Island of the Sun. Gold, ceramic, and stone artifacts."},
    {"name": "Lion City (Shi Cheng)", "lat": 29.5500, "lon": 118.9000, "period": "25-200 AD, flooded 1959", "country": "China", "description": "Ancient city intentionally flooded for Xin'an River hydropower. Perfectly preserved Ming/Qing architecture at 40m depth."},
    {"name": "Atlit-Yam", "lat": 32.7167, "lon": 34.9333, "period": "7000 BC", "country": "Israel", "description": "Submerged Neolithic village off Haifa coast. Oldest known well, stone structures, and evidence of tuberculosis."},
    {"name": "Canopus (Abu Qir)", "lat": 31.3167, "lon": 30.0833, "period": "7th century BC", "country": "Egypt", "description": "Ancient Egyptian coastal city submerged in Abu Qir Bay. Temple of Serapis and Osiris chapel discovered."},
    {"name": "Museo Atlantico (Lanzarote)", "lat": 28.9167, "lon": -13.6667, "period": "2016 AD (modern art)", "country": "Spain (Canary Islands)", "description": "Europe's first underwater sculpture museum by Jason deCaires Taylor. 300+ life-size figures at 12m depth."},
    {"name": "HMHS Britannic", "lat": 37.6833, "lon": 24.2833, "period": "Sunk 1916", "country": "Kea Channel, Greece", "description": "Titanic's sister ship, largest vessel sunk in WWI. Hospital ship struck a mine. Lies at 120m depth."},
    {"name": "Zealandia (Continent)", "lat": -40.0000, "lon": 172.0000, "period": "Submerged 23 Ma", "country": "Pacific Ocean", "description": "Earth's hidden continent, 94% underwater. 4.9 million sq km, only New Zealand and New Caledonia protrude."},
    {"name": "Olous (Crete)", "lat": 35.2611, "lon": 25.7467, "period": "Minoan - Roman era", "country": "Greece", "description": "Ancient Cretan city partially submerged. Mosaic floors visible through crystal-clear shallow water."},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 7: CAVE PAINTINGS & ROCK ART
# ═══════════════════════════════════════════════════════════════════════
CAVE_ART_SITES = [
    {"name": "Lascaux", "lat": 45.0531, "lon": 1.1681, "period": "c. 17,000 BC", "country": "France", "description": "Sistine Chapel of prehistory. Over 600 paintings of aurochs, horses, deer. Closed in 1963 to preserve art."},
    {"name": "Altamira", "lat": 43.3778, "lon": -4.1175, "period": "36,000-15,000 BC", "country": "Spain", "description": "First cave with prehistoric paintings recognized. Polychrome bison ceiling. Limited visitor access."},
    {"name": "Bhimbetka Rock Shelters", "lat": 22.9375, "lon": 77.6111, "period": "30,000 BC - Medieval", "country": "India", "description": "Over 750 rock shelters with paintings spanning 30,000 years. Oldest depict large animals and hunting scenes."},
    {"name": "Tassili n'Ajjer", "lat": 25.5000, "lon": 9.0000, "period": "12,000 BC - 100 AD", "country": "Algeria", "description": "Over 15,000 rock engravings in the Sahara documenting climate change from lush savanna to desert."},
    {"name": "Kakadu (Ubirr)", "lat": -12.4083, "lon": 132.9550, "period": "40,000+ years", "country": "Australia", "description": "Among the oldest continuous rock art traditions. X-ray art style showing animal internal organs. Aboriginal sacred sites."},
    {"name": "Chauvet Cave", "lat": 44.3886, "lon": 4.4181, "period": "36,000-32,000 BC", "country": "France", "description": "Oldest known figurative cave art. Sophisticated charcoal drawings of lions, rhinos, mammoths. UNESCO World Heritage."},
    {"name": "Cueva de las Manos", "lat": -47.1531, "lon": -70.6667, "period": "9,300-700 BC", "country": "Argentina", "description": "Cave of Hands in Patagonia. Stenciled handprints from 9,000 years of indigenous occupation."},
    {"name": "Serra da Capivara", "lat": -8.8333, "lon": -42.5500, "period": "25,000+ BC", "country": "Brazil", "description": "Largest concentration of rock art in the Americas. Over 30,000 paintings across 800+ sites."},
    {"name": "Twyfelfontein (Ui-Aes)", "lat": -20.5928, "lon": 14.3711, "period": "6,000 BC+", "country": "Namibia", "description": "Over 2,500 rock engravings by San hunter-gatherers. Animal tracks, geometric patterns. UNESCO site."},
    {"name": "Font-de-Gaume", "lat": 44.9358, "lon": 1.0658, "period": "17,000 BC", "country": "France", "description": "One of last original prehistoric caves open to visitors. Polychrome paintings of bison, horses, mammoths."},
    {"name": "Niaux Cave", "lat": 42.8167, "lon": 1.5833, "period": "14,000-13,000 BC", "country": "France", "description": "Magdalenian cave art in the Pyrenees. Black Salon features 100+ animal paintings using charcoal and manganese."},
    {"name": "El Castillo Cave", "lat": 43.2875, "lon": -3.9639, "period": "40,800 BC", "country": "Spain", "description": "Contains oldest dated cave art in Europe: a red disk hand stencil at 40,800 years old."},
    {"name": "Pech Merle", "lat": 44.5072, "lon": 1.6372, "period": "25,000 BC", "country": "France", "description": "Famous spotted horses panel and preserved 25,000-year-old human footprints on the cave floor."},
    {"name": "Sulawesi Cave Art", "lat": -4.9833, "lon": 119.6167, "period": "45,500 BC", "country": "Indonesia", "description": "Oldest known figurative art in the world. Hunting scene depicting human-animal hybrid figures."},
    {"name": "Laas Geel", "lat": 9.7833, "lon": 44.4667, "period": "9,000-3,000 BC", "country": "Somalia", "description": "Remarkably well-preserved polychrome cave paintings of cattle, dogs, and decorated humans."},
    {"name": "Drakensberg Rock Art", "lat": -29.2500, "lon": 29.5000, "period": "8,000 BC - 1800s AD", "country": "South Africa", "description": "Largest collection of San rock art. Over 35,000 paintings in 500+ caves across the uKhahlamba range."},
    {"name": "Cave of Swimmers", "lat": 23.5375, "lon": 25.8400, "period": "10,000-8,000 BC", "country": "Egypt/Libya", "description": "Gilf Kebir cave with swimming figures from when the Sahara was green. Inspired 'The English Patient' film."},
    {"name": "Cosquer Cave", "lat": 43.2028, "lon": 5.4497, "period": "27,000-19,000 BC", "country": "France", "description": "Undersea cave near Marseille, entrance 37m below sea level. Charcoal drawings of seals, auks, horses."},
    {"name": "Apollo 11 Cave", "lat": -27.7500, "lon": 17.0833, "period": "25,000-27,000 BC", "country": "Namibia", "description": "Seven stone slabs with oldest known art in Africa. Animal figures painted with charcoal, ochre, and white."},
    {"name": "Gabarnmung", "lat": -13.5833, "lon": 133.2833, "period": "28,000+ BC", "country": "Australia", "description": "Rock shelter with 36,000+ years of Aboriginal art. Multi-layered paintings forming a natural art gallery."},
    {"name": "Creswell Crags", "lat": 53.2642, "lon": -1.1942, "period": "12,500 BC", "country": "England", "description": "Northernmost cave art in Europe. Animal and bird engravings from the Ice Age on limestone walls."},
    {"name": "Magura Cave", "lat": 43.7278, "lon": 22.0583, "period": "8000-4000 BC", "country": "Bulgaria", "description": "Cave paintings made with bat guano depicting dancing women, hunting scenes, and a solar calendar."},
    {"name": "Kondoa Rock Art", "lat": -4.9000, "lon": 35.7833, "period": "Spanning millennia", "country": "Tanzania", "description": "UNESCO rock art sites on eastern slopes of Masai Escarpment. Red and black pigments depict elongated human figures."},
    {"name": "Pedra Furada", "lat": -8.8333, "lon": -42.5500, "period": "Debated 32,000+ BC", "country": "Brazil", "description": "Controversial site in Serra da Capivara with possible oldest human evidence in the Americas."},
    {"name": "Bradshaw (Gwion Gwion) Art", "lat": -15.0000, "lon": 126.0000, "period": "17,000+ BC", "country": "Australia", "description": "Elegant, finely detailed rock art in the Kimberley. Slender human figures with headdresses and tassels."},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 9: MAYAN, AZTEC & MESOAMERICAN
# ═══════════════════════════════════════════════════════════════════════
MESOAMERICAN_SITES = [
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678, "period": "600-1221 AD", "country": "Mexico", "description": "Major Maya city. El Castillo pyramid produces feathered serpent shadow on equinoxes. Sacred cenote for offerings."},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438, "period": "100 BC - 550 AD", "country": "Mexico", "description": "City of the Gods. Pyramid of the Sun (65m) and Moon. Avenue of the Dead. Population once 125,000."},
    {"name": "Tikal", "lat": 17.2220, "lon": -89.6237, "period": "600 BC - 900 AD", "country": "Guatemala", "description": "Major Classic Maya city-state in Peten jungle. Temple I (47m) towers above the rainforest canopy."},
    {"name": "Palenque", "lat": 17.4838, "lon": -92.0462, "period": "226-799 AD", "country": "Mexico", "description": "Elegant Maya city in Chiapas. Temple of Inscriptions tomb of K'inich Janaab Pakal with jade death mask."},
    {"name": "Uxmal", "lat": 20.3597, "lon": -89.7715, "period": "500-1000 AD", "country": "Mexico", "description": "Puuc-style Maya architecture. Pyramid of the Magician with unique rounded form. Governor's Palace mosaic facade."},
    {"name": "Copan", "lat": 14.8386, "lon": -89.1414, "period": "426-820 AD", "country": "Honduras", "description": "Maya city famous for its Hieroglyphic Stairway (2,200 glyphs) and elaborate stelae portrait sculptures."},
    {"name": "Monte Alban", "lat": 17.0437, "lon": -96.7676, "period": "500 BC - 750 AD", "country": "Mexico", "description": "Zapotec capital on a flattened mountaintop overlooking Oaxaca Valley. Los Danzantes carved stone slabs."},
    {"name": "Calakmul", "lat": 18.1053, "lon": -89.8108, "period": "300 BC - 900 AD", "country": "Mexico", "description": "Maya superpower and rival of Tikal. Largest city in the Maya lowlands. Structure II is 45m tall."},
    {"name": "Tulum", "lat": 20.2145, "lon": -87.4291, "period": "1200-1521 AD", "country": "Mexico", "description": "Walled Maya city on a Caribbean cliff. One of last cities inhabited at Spanish arrival. El Castillo overlooks sea."},
    {"name": "Templo Mayor (Tenochtitlan)", "lat": 19.4352, "lon": -99.1318, "period": "1325-1521 AD", "country": "Mexico", "description": "Heart of the Aztec Empire. Double pyramid dedicated to Huitzilopochtli and Tlaloc. Excavated beneath Mexico City."},
    {"name": "Bonampak", "lat": 16.7036, "lon": -91.0647, "period": "580-800 AD", "country": "Mexico", "description": "Famous for vivid Maya murals depicting warfare, sacrifice, and court life. Best-preserved Maya paintings."},
    {"name": "El Mirador", "lat": 17.7553, "lon": -89.9206, "period": "600 BC - 100 AD", "country": "Guatemala", "description": "Preclassic Maya mega-city. La Danta pyramid is 72m tall, one of the largest ancient structures by volume."},
    {"name": "Tula (Tollan)", "lat": 20.0653, "lon": -99.3428, "period": "900-1168 AD", "country": "Mexico", "description": "Capital of the Toltec Empire. Atlantean warrior columns atop Pyramid B. Influenced Chichen Itza."},
    {"name": "Mitla", "lat": 16.9267, "lon": -96.3550, "period": "100-1521 AD", "country": "Mexico", "description": "Zapotec-Mixtec religious center. Geometric fretwork (grecas) mosaics without mortar are unique in Mesoamerica."},
    {"name": "Yaxchilan", "lat": 16.8994, "lon": -90.9650, "period": "359-810 AD", "country": "Mexico", "description": "Maya city on the Usumacinta River with exquisite carved stone lintels depicting bloodletting rituals."},
    {"name": "Caracol", "lat": 16.7631, "lon": -89.1175, "period": "1200 BC - 900 AD", "country": "Belize", "description": "Largest Maya site in Belize. Caana (Sky Palace) at 43m remains tallest man-made structure in the country."},
    {"name": "La Venta", "lat": 18.1033, "lon": -94.0436, "period": "1200-400 BC", "country": "Mexico", "description": "Major Olmec center with colossal basalt heads (up to 3m tall, 50 tonnes). Earliest Mesoamerican pyramid."},
    {"name": "San Lorenzo Tenochtitlan", "lat": 17.7536, "lon": -94.7572, "period": "1500-900 BC", "country": "Mexico", "description": "Oldest known Olmec center. Ten colossal stone heads. Sophisticated drainage system beneath the plateau."},
    {"name": "Tres Zapotes", "lat": 18.4675, "lon": -95.4408, "period": "1500 BC - 900 AD", "country": "Mexico", "description": "Olmec site with Stela C bearing one of the earliest Long Count calendar dates (32 BC)."},
    {"name": "Xochicalco", "lat": 18.8042, "lon": -99.2961, "period": "650-900 AD", "country": "Mexico", "description": "Fortified hilltop city of the Epiclassic period. Pyramid of the Feathered Serpent with Maya-Zapotec-Teotihuacan blend."},
    {"name": "Tonina", "lat": 16.9022, "lon": -92.0136, "period": "217-909 AD", "country": "Mexico", "description": "Maya city with massive acropolis terraces. Captured Palenque's king Kan Bahlam II. Last dated Maya Long Count stela."},
    {"name": "Coba", "lat": 20.4950, "lon": -87.7361, "period": "100 BC - 1550 AD", "country": "Mexico", "description": "Maya city with extensive sacbe (road) network spanning 100 km. Nohoch Mul pyramid is 42m, tallest in Yucatan."},
    {"name": "Cholula Great Pyramid", "lat": 19.0578, "lon": -98.3017, "period": "300 BC - 800 AD", "country": "Mexico", "description": "Largest pyramid by volume in the world (4.45 million cubic meters). Church built atop by Spanish. 8 km of tunnels."},
    {"name": "Kabah", "lat": 20.2500, "lon": -89.6500, "period": "600-1000 AD", "country": "Mexico", "description": "Puuc Maya site. Codz Poop Palace has facade of 250 Chaac rain god masks. Connected to Uxmal by sacbe road."},
    {"name": "Izapa", "lat": 14.9500, "lon": -92.1667, "period": "1500 BC - 100 AD", "country": "Mexico", "description": "Transitional site linking Olmec and Maya cultures. Origin of the Maya Long Count calendar tradition."},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 10: INCA & SOUTH AMERICAN
# ═══════════════════════════════════════════════════════════════════════
SOUTH_AMERICAN_SITES = [
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "period": "c. 1450 AD", "country": "Peru", "description": "Inca royal estate at 2,430m. Terraces, temples, and Intihuatana stone. Abandoned before Spanish Conquest."},
    {"name": "Nazca Lines", "lat": -14.7350, "lon": -75.1300, "period": "500 BC - 500 AD", "country": "Peru", "description": "Giant geoglyphs etched into desert covering 450 sq km. Hummingbird, spider, monkey visible only from air."},
    {"name": "Tiwanaku", "lat": -16.5550, "lon": -68.6725, "period": "300-1000 AD", "country": "Bolivia", "description": "Pre-Inca civilization at 3,850m near Lake Titicaca. Akapana pyramid and Gate of the Sun monolith."},
    {"name": "Chan Chan", "lat": -8.1067, "lon": -79.0747, "period": "850-1470 AD", "country": "Peru", "description": "Largest pre-Columbian city in South America. Chimu adobe capital with nine walled citadels and intricate friezes."},
    {"name": "Sacsayhuaman", "lat": -13.5094, "lon": -71.9822, "period": "c. 1440 AD", "country": "Peru", "description": "Inca fortress above Cusco with zigzag walls of precisely fitted stones, some weighing 200 tonnes."},
    {"name": "Ollantaytambo", "lat": -13.2581, "lon": -72.2628, "period": "c. 1440 AD", "country": "Peru", "description": "Inca royal estate and fortress. Massive terraces and Temple Hill with six monoliths transported from 6 km away."},
    {"name": "Moray (Inca Agricultural Lab)", "lat": -13.3297, "lon": -72.1972, "period": "c. 1400 AD", "country": "Peru", "description": "Concentric circular terraces creating microclimates. Believed to be an Inca agricultural research station."},
    {"name": "Pisac", "lat": -13.4156, "lon": -71.8497, "period": "c. 1440 AD", "country": "Peru", "description": "Inca citadel with agricultural terraces, military architecture, and religious temples above the Sacred Valley."},
    {"name": "Caral", "lat": -10.8933, "lon": -77.5206, "period": "3000-1800 BC", "country": "Peru", "description": "Oldest city in the Americas. Six large pyramids, sunken circular plazas. Contemporary with Egyptian pyramids."},
    {"name": "Chavin de Huantar", "lat": -9.5933, "lon": -77.1769, "period": "900-200 BC", "country": "Peru", "description": "Ceremonial center of Chavin culture. Labyrinthine underground galleries and Lanzon monolith."},
    {"name": "Huaca de la Luna", "lat": -8.1167, "lon": -78.9750, "period": "100-800 AD", "country": "Peru", "description": "Moche ceremonial center near Trujillo. Multi-colored friezes of Ai Apaec (Decapitator God) on temple walls."},
    {"name": "Kuelap", "lat": -6.4183, "lon": -77.9208, "period": "6th century AD", "country": "Peru", "description": "Chachapoya fortress at 3,000m. Massive stone walls up to 19m high. 420 circular buildings inside. 'Machu Picchu of the North'."},
    {"name": "Sipan (Royal Tombs)", "lat": -6.8047, "lon": -79.5978, "period": "c. 250 AD", "country": "Peru", "description": "Moche royal tomb discovery rivaling Tutankhamun. Lord of Sipan buried with gold, silver, copper ornaments."},
    {"name": "Ingapirca", "lat": -2.5461, "lon": -78.8778, "period": "15th century AD", "country": "Ecuador", "description": "Most important Inca ruins in Ecuador. Temple of the Sun with distinctive elliptical platform."},
    {"name": "Ciudad Perdida (Lost City)", "lat": 11.0381, "lon": -73.9264, "period": "800 AD", "country": "Colombia", "description": "Tairona city in Sierra Nevada de Santa Marta jungle. 169 terraces on a mountainside. Discovered in 1972."},
    {"name": "San Agustin Archaeological Park", "lat": 1.8833, "lon": -76.2833, "period": "1st-8th century AD", "country": "Colombia", "description": "Largest group of megalithic funerary monuments in South America. Over 500 carved stone statues of deities and warriors."},
    {"name": "Tierradentro", "lat": 2.5833, "lon": -76.0333, "period": "6th-10th century AD", "country": "Colombia", "description": "Underground tombs carved into volcanic rock with geometric painted patterns. UNESCO World Heritage."},
    {"name": "Tiahuanaco Sun Gate", "lat": -16.5550, "lon": -68.6747, "period": "c. 500 AD", "country": "Bolivia", "description": "Monolithic stone archway carved from single block. Central figure (Viracocha) flanked by 48 winged figures."},
    {"name": "Isla del Sol", "lat": -16.0200, "lon": -69.1700, "period": "Pre-Inca to Inca", "country": "Bolivia", "description": "Sacred island in Lake Titicaca. Inca creation myth origin. Pilko Kaina palace and sacred rock."},
    {"name": "Quilmes Ruins", "lat": -26.4667, "lon": -66.0333, "period": "850-1667 AD", "country": "Argentina", "description": "Largest pre-Columbian settlement in Argentina. Diaguita-Calchaqi city with 5,000 inhabitants at its peak."},
]

# ═══════════════════════════════════════════════════════════════════════
# PBDB (Fossil Sites) API
# ═══════════════════════════════════════════════════════════════════════
PBDB_API = "https://paleobiodb.org/data1.2"


@st.cache_data(ttl=3600)
def _fetch_fossils(lat_min: float, lat_max: float, lon_min: float, lon_max: float, limit: int = 500) -> list:
    """Fetch fossil occurrences from the Paleobiology Database."""
    url = (
        f"{PBDB_API}/occs/list.json?"
        f"lngmin={lon_min}&lngmax={lon_max}&latmin={lat_min}&latmax={lat_max}"
        f"&show=coords,class&limit={limit}"
    )
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "TerraScoutAI/1.0"})
        resp.raise_for_status()
        data = resp.json()
        return data.get("records", [])
    except requests.exceptions.Timeout:
        st.error("Paleobiology Database request timed out. Try a smaller area.")
        return []
    except requests.exceptions.HTTPError as exc:
        st.error(f"PBDB API error: {exc}")
        return []
    except Exception as exc:
        st.error(f"Failed to fetch fossil data: {exc}")
        return []


# ═══════════════════════════════════════════════════════════════════════
# OVERPASS (Roman Empire Sites) QUERY
# ═══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fetch_roman_sites(lat: float, lon: float, radius_km: float) -> list:
    """Fetch Roman ruins via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["historic"="ruins"]["civilization"="roman"](around:{radius_m},{lat},{lon});
  way["historic"="ruins"]["civilization"="roman"](around:{radius_m},{lat},{lon});
  node["historic"="archaeological_site"]["civilization"="roman"](around:{radius_m},{lat},{lon});
  way["historic"="archaeological_site"]["civilization"="roman"](around:{radius_m},{lat},{lon});
  node["historic"="ruins"]["name"~"[Rr]oman|[Rr]oma"](around:{radius_m},{lat},{lon});
  way["historic"="ruins"]["name"~"[Rr]oman|[Rr]oma"](around:{radius_m},{lat},{lon});
  node["historic"="archaeological_site"]["name"~"[Rr]oman|[Rr]oma"](around:{radius_m},{lat},{lon});
  way["historic"="archaeological_site"]["name"~"[Rr]oman|[Rr]oma"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        st.error(f"Overpass query failed: {err}. Try a smaller radius or retry later.")
        return []

    elements = result.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    sites = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat_v, lon_v = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat_v, lon_v = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
            if coords:
                lat_v = sum(c[0] for c in coords) / len(coords)
                lon_v = sum(c[1] for c in coords) / len(coords)
        if lat_v is None or lon_v is None:
            continue
        name = tags.get("name", tags.get("name:en", tags.get("name:la", "Unnamed Roman site")))
        sites.append({
            "name": name,
            "lat": lat_v,
            "lon": lon_v,
            "period": tags.get("start_date", tags.get("heritage:period", "Roman period")),
            "country": tags.get("addr:country", ""),
            "description": tags.get("description", tags.get("description:en", tags.get("note", ""))),
            "historic": tags.get("historic", ""),
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
        })
    return sites


# ═══════════════════════════════════════════════════════════════════════
# HELPER: build folium map from curated site list
# ═══════════════════════════════════════════════════════════════════════
def _build_map(sites: list, color: str = _ACCENT, zoom: int = 3, icon_prefix: str = "fa",
               icon_name: str = "monument") -> folium.Map:
    """Create a folium map with CircleMarkers for each site."""
    if not sites:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        return m

    avg_lat = sum(s["lat"] for s in sites) / len(sites)
    avg_lon = sum(s["lon"] for s in sites) / len(sites)
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=zoom, tiles="CartoDB dark_matter")

    for s in sites:
        safe_name = escape(str(s.get("name", "Unknown")))
        safe_desc = escape(str(s.get("description", ""))[:200])
        safe_period = escape(str(s.get("period", "")))
        safe_country = escape(str(s.get("country", "")))

        popup_html = (
            f'<div style="max-width:260px; font-family:sans-serif;">'
            f'<strong style="font-size:0.9rem;">{safe_name}</strong><br/>'
            f'<span style="color:#888; font-size:0.78rem;">{safe_period}</span>'
        )
        if safe_country:
            popup_html += f' &mdash; <span style="font-size:0.78rem;">{safe_country}</span>'
        popup_html += f'<br/><span style="font-size:0.75rem;">{safe_desc}</span></div>'

        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=safe_name,
        ).add_to(m)

    return m


def _render_map(m: folium.Map):
    """Render a folium map via components.html."""
    components.html(m._repr_html_(), height=500)


# ═══════════════════════════════════════════════════════════════════════
# HELPER: stats row
# ═══════════════════════════════════════════════════════════════════════
def _show_stats(sites: list, label: str = "Sites"):
    """Display metrics row for a list of site dicts."""
    if not sites:
        st.info("No data to display.")
        return

    countries = set()
    periods = set()
    for s in sites:
        c = s.get("country", "")
        if c:
            countries.add(c)
        p = s.get("period", "")
        if p:
            periods.add(p)

    cols = st.columns(4)
    cols[0].metric(f"Total {label}", len(sites))
    cols[1].metric("Countries", len(countries) if countries else "N/A")
    oldest = min(periods) if periods else "N/A"
    cols[2].metric("Earliest Period", str(oldest)[:25] if oldest != "N/A" else "N/A")
    newest = max(periods) if periods else "N/A"
    cols[3].metric("Latest Period", str(newest)[:25] if newest != "N/A" else "N/A")


# ═══════════════════════════════════════════════════════════════════════
# HELPER: data table and CSV download
# ═══════════════════════════════════════════════════════════════════════
def _show_table_and_download(sites: list, key_prefix: str, filename: str):
    """Render expandable data table and CSV download button."""
    if not sites:
        return
    rows = []
    for s in sites:
        rows.append({
            "Name": s.get("name", ""),
            "Latitude": s.get("lat", ""),
            "Longitude": s.get("lon", ""),
            "Period": s.get("period", ""),
            "Country": s.get("country", ""),
            "Description": s.get("description", "")[:300],
        })
    df = pd.DataFrame(rows)
    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=f"{key_prefix}_dl",
    )


# ═══════════════════════════════════════════════════════════════════════
# HELPER: bar chart
# ═══════════════════════════════════════════════════════════════════════
def _country_chart(sites: list, title: str = "Sites by Country"):
    """Horizontal bar chart of sites per country."""
    if not sites:
        return
    counts: dict[str, int] = {}
    for s in sites:
        c = s.get("country", "Unknown")
        if c:
            counts[c] = counts.get(c, 0) + 1
    if not counts:
        return
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:15]
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    fig, ax = plt.subplots(figsize=(6, max(3, len(labels) * 0.35)))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    ax.barh(range(len(labels)), values, color=_ACCENT, alpha=0.85)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color=_TEXT2, fontsize=9)
    ax.set_xlabel("Count", color=_TEXT2, fontsize=10)
    ax.set_title(title, color=_TEXT, fontsize=11, pad=8)
    ax.tick_params(axis="x", colors=_TEXT2, labelsize=9)
    ax.grid(True, axis="x", color=_GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════════════

def _render_seven_wonders():
    """Mode 1 - Seven Wonders of the Ancient and New World."""
    st.markdown("#### Seven Wonders of the World")
    st.caption("The 7 Ancient Wonders and the 7 New Wonders, all on one map.")
    ancient = [s for s in SEVEN_WONDERS if "BC" in s.get("period", "") or "Pharos" in s.get("name", "")]
    new = [s for s in SEVEN_WONDERS if s not in ancient]

    filter_choice = st.radio("Filter", ["All (Ancient + New)", "Ancient Wonders", "New Wonders"],
                             horizontal=True, key="sw_filter")
    if filter_choice == "Ancient Wonders":
        sites = ancient
    elif filter_choice == "New Wonders":
        sites = new
    else:
        sites = SEVEN_WONDERS

    _show_stats(sites, "Wonders")

    m = folium.Map(location=[25, 30], zoom_start=2, tiles="CartoDB dark_matter")
    for s in sites:
        is_ancient = s in ancient
        color = "#f59e0b" if is_ancient else "#06b6d4"
        label = "Ancient" if is_ancient else "New"
        safe_name = escape(s["name"])
        safe_desc = escape(s["description"][:200])
        safe_period = escape(s["period"])
        popup_html = (
            f'<div style="max-width:260px; font-family:sans-serif;">'
            f'<strong>{safe_name}</strong><br/>'
            f'<span style="color:{color}; font-size:0.78rem;">[{label}]</span> '
            f'<span style="color:#888; font-size:0.78rem;">{safe_period}</span><br/>'
            f'<span style="font-size:0.75rem;">{safe_desc}</span></div>'
        )
        folium.CircleMarker(
            location=[s["lat"], s["lon"]], radius=9,
            color=color, fill=True, fill_color=color, fill_opacity=0.8, weight=2,
            popup=folium.Popup(popup_html, max_width=280), tooltip=safe_name,
        ).add_to(m)
    _render_map(m)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### Ancient Wonders")
        for s in ancient:
            st.markdown(
                f'<div style="padding:4px 0;">'
                f'<span style="color:#f59e0b; font-weight:600;">{escape(s["name"])}</span> '
                f'<span style="color:{_MUTED}; font-size:0.8rem;">({escape(s["period"])})</span><br/>'
                f'<span style="color:{_TEXT2}; font-size:0.8rem;">{escape(s["description"][:120])}</span></div>',
                unsafe_allow_html=True)
    with col_b:
        st.markdown("##### New Wonders")
        for s in new:
            st.markdown(
                f'<div style="padding:4px 0;">'
                f'<span style="color:#06b6d4; font-weight:600;">{escape(s["name"])}</span> '
                f'<span style="color:{_MUTED}; font-size:0.8rem;">({escape(s["period"])})</span><br/>'
                f'<span style="color:{_TEXT2}; font-size:0.8rem;">{escape(s["description"][:120])}</span></div>',
                unsafe_allow_html=True)

    _show_table_and_download(sites, "sw", "seven_wonders.csv")


def _render_megalithic():
    """Mode 2 - Megalithic Sites worldwide."""
    st.markdown("#### Megalithic Sites Worldwide")
    st.caption("Stonehenge, Carnac, Gobekli Tepe, Easter Island, and 30+ more ancient stone monuments.")

    countries = sorted(set(s["country"] for s in MEGALITHIC_SITES))
    sel_countries = st.multiselect("Filter by country", countries, default=[], key="mega_countries",
                                   help="Leave empty to show all")
    sites = [s for s in MEGALITHIC_SITES if (not sel_countries or s["country"] in sel_countries)]

    _show_stats(sites, "Megalithic Sites")
    m = _build_map(sites, color="#8b5cf6", zoom=2, icon_name="monument")
    _render_map(m)

    st.markdown("---")
    _country_chart(sites, "Megalithic Sites by Country")
    _show_table_and_download(sites, "mega", "megalithic_sites.csv")


def _render_lost_cities():
    """Mode 3 - Ancient Lost Cities."""
    st.markdown("#### Ancient Lost Cities")
    st.caption("Pompeii, Petra, Angkor, Troy, Mohenjo-daro, and 30+ cities rediscovered.")

    countries = sorted(set(s["country"] for s in LOST_CITIES))
    sel_countries = st.multiselect("Filter by country", countries, default=[], key="lc_countries",
                                   help="Leave empty to show all")
    sites = [s for s in LOST_CITIES if (not sel_countries or s["country"] in sel_countries)]

    _show_stats(sites, "Lost Cities")
    m = _build_map(sites, color="#ef4444", zoom=2, icon_name="institution")
    _render_map(m)

    st.markdown("---")
    _country_chart(sites, "Lost Cities by Country")
    _show_table_and_download(sites, "lc", "lost_cities.csv")


def _render_egyptian():
    """Mode 4 - Egyptian Pyramids & Temples."""
    st.markdown("#### Egyptian Pyramids & Temples")
    st.caption("Giza, Luxor, Abu Simbel, Valley of the Kings, and 25+ sites along the Nile.")

    site_type = st.radio("Filter", ["All", "Pyramids only", "Temples only", "Tombs & Valleys"],
                         horizontal=True, key="egypt_filter")
    if site_type == "Pyramids only":
        sites = [s for s in EGYPT_SITES if "pyramid" in s["name"].lower() or "sphinx" in s["name"].lower()]
    elif site_type == "Temples only":
        sites = [s for s in EGYPT_SITES if "temple" in s["name"].lower() or "temple" in s["description"].lower()]
    elif site_type == "Tombs & Valleys":
        sites = [s for s in EGYPT_SITES if any(kw in s["name"].lower() for kw in ("valley", "tomb", "colossi", "medinet", "obelisk"))]
    else:
        sites = EGYPT_SITES

    _show_stats(sites, "Egyptian Sites")
    m = _build_map(sites, color="#f59e0b", zoom=6, icon_name="star")
    _render_map(m)

    st.markdown("---")
    # Timeline chart by period (North to South along Nile)
    if sites:
        fig, ax = plt.subplots(figsize=(8, max(3, len(sites) * 0.3)))
        fig.patch.set_facecolor(_BG)
        ax.set_facecolor(_SURFACE)
        sorted_sites = sorted(sites, key=lambda s: s["lat"], reverse=True)
        names = [s["name"][:30] for s in sorted_sites]
        lats = [s["lat"] for s in sorted_sites]
        ax.barh(range(len(names)), lats, color="#f59e0b", alpha=0.8)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, color=_TEXT2, fontsize=8)
        ax.set_xlabel("Latitude (North to South along Nile)", color=_TEXT2, fontsize=10)
        ax.set_title("Egyptian Sites by Latitude", color=_TEXT, fontsize=11, pad=8)
        ax.tick_params(axis="x", colors=_TEXT2, labelsize=9)
        ax.grid(True, axis="x", color=_GRID, linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(_GRID)
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    _show_table_and_download(sites, "egypt", "egyptian_sites.csv")


def _render_roman():
    """Mode 5 - Roman Empire Sites via Overpass API + curated fallback."""
    st.markdown("#### Roman Empire Sites")
    st.caption("Search for Roman ruins, aqueducts, roads, and baths across Europe and the Mediterranean.")

    ROMAN_PRESETS = {
        "Custom": None,
        "Rome, Italy": {"lat": 41.8933, "lon": 12.4829, "radius": 10},
        "Pompeii, Italy": {"lat": 40.7509, "lon": 14.4869, "radius": 8},
        "Athens, Greece": {"lat": 37.9715, "lon": 23.7267, "radius": 10},
        "Bath, England": {"lat": 51.3811, "lon": -2.3590, "radius": 5},
        "Trier, Germany": {"lat": 49.7590, "lon": 6.6439, "radius": 8},
        "Nimes, France": {"lat": 43.8367, "lon": 4.3601, "radius": 8},
        "Merida, Spain": {"lat": 38.9160, "lon": -6.3440, "radius": 8},
        "Split, Croatia": {"lat": 43.5081, "lon": 16.4402, "radius": 5},
        "Leptis Magna, Libya": {"lat": 32.6378, "lon": 14.2928, "radius": 5},
        "Carthage, Tunisia": {"lat": 36.8528, "lon": 10.3233, "radius": 8},
        "Ephesus, Turkey": {"lat": 37.9411, "lon": 27.3419, "radius": 5},
        "Jerash, Jordan": {"lat": 32.2747, "lon": 35.8911, "radius": 5},
    }

    preset_name = st.selectbox("Preset Location", list(ROMAN_PRESETS.keys()), key="roman_preset")

    col1, col2, col3 = st.columns(3)
    if preset_name != "Custom" and ROMAN_PRESETS[preset_name]:
        p = ROMAN_PRESETS[preset_name]
        default_lat, default_lon, default_rad = p["lat"], p["lon"], p["radius"]
    else:
        default_lat, default_lon, default_rad = 41.8933, 12.4829, 10

    with col1:
        r_lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                                min_value=-90.0, max_value=90.0, key="roman_lat")
    with col2:
        r_lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                                min_value=-180.0, max_value=180.0, key="roman_lon")
    with col3:
        r_rad = st.slider("Radius (km)", 1, 50, default_rad, key="roman_rad")

    if st.button("Search Roman Sites", key="roman_go", type="primary"):
        st.session_state["roman_params"] = {"lat": r_lat, "lon": r_lon, "radius": r_rad}

    if "roman_params" not in st.session_state:
        st.info("Select a location and click Search to find Roman Empire sites via OpenStreetMap.")
        return

    rp = st.session_state["roman_params"]
    with st.spinner("Querying Overpass API for Roman ruins..."):
        sites = _fetch_roman_sites(rp["lat"], rp["lon"], rp["radius"])

    if not sites:
        st.warning("No Roman sites found in this area. Try a larger radius, different location, or a curated preset.")
        return

    _show_stats(sites, "Roman Sites")

    m = folium.Map(location=[rp["lat"], rp["lon"]], zoom_start=11, tiles="CartoDB dark_matter")
    folium.Circle(
        location=[rp["lat"], rp["lon"]], radius=rp["radius"] * 1000,
        color=_ACCENT, fill=True, fill_opacity=0.03, weight=1,
    ).add_to(m)
    for s in sites:
        safe_name = escape(str(s.get("name", "Unknown")))
        safe_desc = escape(str(s.get("description", ""))[:200])
        safe_period = escape(str(s.get("period", "")))
        wiki_link = ""
        if s.get("wikipedia"):
            wp = s["wikipedia"]
            lang, title = wp.split(":", 1) if ":" in wp else ("en", wp)
            wiki_link = (
                f'<br/><a href="https://{escape(lang)}.wikipedia.org/wiki/{escape(title)}" '
                f'target="_blank" style="font-size:0.75rem;">Wikipedia</a>'
            )
        popup_html = (
            f'<div style="max-width:260px; font-family:sans-serif;">'
            f'<strong>{safe_name}</strong><br/>'
            f'<span style="color:#888; font-size:0.78rem;">{safe_period}</span><br/>'
            f'<span style="font-size:0.75rem;">{safe_desc}</span>{wiki_link}</div>'
        )
        folium.CircleMarker(
            location=[s["lat"], s["lon"]], radius=7,
            color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.75, weight=2,
            popup=folium.Popup(popup_html, max_width=280), tooltip=safe_name,
        ).add_to(m)
    _render_map(m)

    st.markdown("---")
    _show_table_and_download(sites, "roman", "roman_sites.csv")


def _render_underwater():
    """Mode 6 - Underwater Archaeology."""
    st.markdown("#### Underwater Archaeology")
    st.caption("Shipwrecks, sunken cities, and submerged treasures across the world's oceans.")

    category = st.radio("Filter", ["All", "Shipwrecks", "Sunken Cities", "Underwater Monuments"],
                        horizontal=True, key="uw_filter")
    shipwreck_keywords = ["sunk", "wreck", "ship", "hms", "rms", "ss ", "bismarck", "titanic",
                          "hood", "thistlegorm", "britannic"]
    city_keywords = ["city", "palace", "port ", "heracleion", "pavlopetri", "dwarka", "olous",
                     "baiae", "canopus", "lion city", "atlit"]

    if category == "Shipwrecks":
        sites = [s for s in UNDERWATER_SITES
                 if any(kw in s["name"].lower() or kw in s["description"].lower() for kw in shipwreck_keywords)]
    elif category == "Sunken Cities":
        sites = [s for s in UNDERWATER_SITES
                 if any(kw in s["name"].lower() or kw in s["description"].lower() for kw in city_keywords)]
    elif category == "Underwater Monuments":
        sites = [s for s in UNDERWATER_SITES
                 if s not in [x for x in UNDERWATER_SITES
                              if any(kw in x["name"].lower() or kw in x["description"].lower()
                                     for kw in shipwreck_keywords + city_keywords)]]
    else:
        sites = UNDERWATER_SITES

    _show_stats(sites, "Underwater Sites")
    m = _build_map(sites, color="#38bdf8", zoom=2, icon_name="anchor")
    _render_map(m)

    st.markdown("---")
    _country_chart(sites, "Underwater Sites by Location")
    _show_table_and_download(sites, "uw", "underwater_archaeology.csv")


def _render_cave_art():
    """Mode 7 - Cave Paintings & Rock Art."""
    st.markdown("#### Cave Paintings & Rock Art")
    st.caption("Lascaux, Altamira, Bhimbetka, Tassili, Kakadu, and 25+ prehistoric art sites.")

    countries = sorted(set(s["country"] for s in CAVE_ART_SITES))
    sel_countries = st.multiselect("Filter by country", countries, default=[], key="cave_countries",
                                   help="Leave empty to show all")
    sites = [s for s in CAVE_ART_SITES if (not sel_countries or s["country"] in sel_countries)]

    _show_stats(sites, "Rock Art Sites")
    m = _build_map(sites, color="#ec4899", zoom=2, icon_name="paint-brush")
    _render_map(m)

    st.markdown("---")
    _country_chart(sites, "Cave Art / Rock Art Sites by Country")

    # Age chart attempt
    if sites:
        aged_sites = []
        for s in sites:
            period = s.get("period", "")
            # Try to extract earliest year from period string
            import re
            matches = re.findall(r'([\d,]+)\s*(?:BC|\+)', period)
            if matches:
                try:
                    year_bc = int(matches[0].replace(",", ""))
                    aged_sites.append((s["name"], year_bc))
                except ValueError:
                    pass
        if aged_sites:
            aged_sites.sort(key=lambda x: x[1], reverse=True)
            top = aged_sites[:20]
            fig, ax = plt.subplots(figsize=(7, max(3, len(top) * 0.35)))
            fig.patch.set_facecolor(_BG)
            ax.set_facecolor(_SURFACE)
            names = [t[0][:28] for t in top]
            ages = [t[1] for t in top]
            ax.barh(range(len(names)), ages, color="#ec4899", alpha=0.8)
            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names, color=_TEXT2, fontsize=8)
            ax.set_xlabel("Approximate Age (years BC)", color=_TEXT2, fontsize=10)
            ax.set_title("Oldest Cave Art Sites", color=_TEXT, fontsize=11, pad=8)
            ax.tick_params(axis="x", colors=_TEXT2, labelsize=9)
            ax.grid(True, axis="x", color=_GRID, linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_color(_GRID)
            ax.invert_yaxis()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    _show_table_and_download(sites, "cave", "cave_art_sites.csv")


def _render_fossils():
    """Mode 8 - Fossil Sites from the Paleobiology Database."""
    st.markdown("#### Fossil Sites (Paleobiology Database)")
    st.caption("Explore fossil occurrences worldwide using the PBDB open API.")

    FOSSIL_PRESETS = {
        "Custom": None,
        "Western USA": {"lat_min": 30, "lat_max": 50, "lon_min": -125, "lon_max": -100},
        "Europe": {"lat_min": 35, "lat_max": 60, "lon_min": -10, "lon_max": 30},
        "East Africa (Great Rift)": {"lat_min": -10, "lat_max": 10, "lon_min": 28, "lon_max": 42},
        "Gobi Desert, Mongolia": {"lat_min": 40, "lat_max": 48, "lon_min": 95, "lon_max": 115},
        "Patagonia, Argentina": {"lat_min": -52, "lat_max": -38, "lon_min": -72, "lon_max": -62},
        "UK & Ireland": {"lat_min": 49, "lat_max": 59, "lon_min": -11, "lon_max": 2},
        "Australia": {"lat_min": -44, "lat_max": -10, "lon_min": 112, "lon_max": 154},
        "Southeast Asia": {"lat_min": -10, "lat_max": 20, "lon_min": 95, "lon_max": 125},
        "Canada (Alberta)": {"lat_min": 49, "lat_max": 56, "lon_min": -118, "lon_max": -109},
    }

    preset_name = st.selectbox("Preset Region", list(FOSSIL_PRESETS.keys()), key="fossil_preset")

    if preset_name != "Custom" and FOSSIL_PRESETS[preset_name]:
        p = FOSSIL_PRESETS[preset_name]
        d_lat_min, d_lat_max = p["lat_min"], p["lat_max"]
        d_lon_min, d_lon_max = p["lon_min"], p["lon_max"]
    else:
        d_lat_min, d_lat_max = 30.0, 50.0
        d_lon_min, d_lon_max = -125.0, -100.0

    col1, col2 = st.columns(2)
    with col1:
        f_lat_min = st.number_input("Lat Min", value=float(d_lat_min), format="%.2f", key="foss_lat_min")
        f_lon_min = st.number_input("Lon Min", value=float(d_lon_min), format="%.2f", key="foss_lon_min")
    with col2:
        f_lat_max = st.number_input("Lat Max", value=float(d_lat_max), format="%.2f", key="foss_lat_max")
        f_lon_max = st.number_input("Lon Max", value=float(d_lon_max), format="%.2f", key="foss_lon_max")

    f_limit = st.slider("Max results", 50, 1000, 500, step=50, key="foss_limit")

    if st.button("Search Fossils", key="fossil_go", type="primary"):
        st.session_state["fossil_params"] = {
            "lat_min": f_lat_min, "lat_max": f_lat_max,
            "lon_min": f_lon_min, "lon_max": f_lon_max,
            "limit": f_limit,
        }

    if "fossil_params" not in st.session_state:
        st.info("Select a region and click Search to query the Paleobiology Database.")
        return

    fp = st.session_state["fossil_params"]
    with st.spinner("Querying Paleobiology Database..."):
        records = _fetch_fossils(fp["lat_min"], fp["lat_max"], fp["lon_min"], fp["lon_max"], fp["limit"])

    if not records:
        st.warning("No fossil occurrences found in this region. Try a larger area or different location.")
        return

    # Parse PBDB records
    sites = []
    class_counts: dict[str, int] = {}
    for rec in records:
        lat_v = rec.get("lat")
        lon_v = rec.get("lng")
        if lat_v is None or lon_v is None:
            continue
        taxon = rec.get("tna", rec.get("idt", "Unknown"))
        cls = rec.get("cll", rec.get("phl", "Unknown"))
        eag = rec.get("eag", "")
        lag = rec.get("lag", "")
        period_str = f"{eag}-{lag} Ma" if eag and lag else str(eag or lag or "Unknown")
        sites.append({
            "name": taxon,
            "lat": float(lat_v),
            "lon": float(lon_v),
            "period": period_str,
            "country": rec.get("cc2", rec.get("sta", "")),
            "description": f"Class: {cls}. Occurrence #{rec.get('oid', 'N/A')}.",
        })
        class_counts[cls] = class_counts.get(cls, 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Occurrences", len(sites))
    cols[1].metric("Unique Taxa", len(set(s["name"] for s in sites)))
    cols[2].metric("Classes", len(class_counts))
    top_class = max(class_counts, key=class_counts.get) if class_counts else "N/A"
    cols[3].metric("Most Common Class", top_class[:20])

    # Map
    m = folium.Map(
        location=[(fp["lat_min"] + fp["lat_max"]) / 2, (fp["lon_min"] + fp["lon_max"]) / 2],
        zoom_start=5, tiles="CartoDB dark_matter",
    )
    # Bounding box rectangle
    folium.Rectangle(
        bounds=[[fp["lat_min"], fp["lon_min"]], [fp["lat_max"], fp["lon_max"]]],
        color=_ACCENT, fill=False, weight=1.5, dash_array="6",
    ).add_to(m)

    # Color by class
    class_colors = {}
    palette = ["#06b6d4", "#f59e0b", "#ef4444", "#8b5cf6", "#10b981", "#ec4899",
               "#38bdf8", "#f97316", "#a855f7", "#64748b", "#e879f9", "#22d3ee"]
    for i, cls in enumerate(class_counts.keys()):
        class_colors[cls] = palette[i % len(palette)]

    for s in sites:
        cls_name = s["description"].split("Class: ")[1].split(".")[0] if "Class: " in s["description"] else "Unknown"
        c = class_colors.get(cls_name, _ACCENT)
        safe_name = escape(s["name"])
        safe_desc = escape(s["description"][:200])
        safe_period = escape(s["period"])
        popup_html = (
            f'<div style="max-width:240px; font-family:sans-serif;">'
            f'<strong>{safe_name}</strong><br/>'
            f'<span style="color:#888; font-size:0.78rem;">{safe_period}</span><br/>'
            f'<span style="font-size:0.75rem;">{safe_desc}</span></div>'
        )
        folium.CircleMarker(
            location=[s["lat"], s["lon"]], radius=5,
            color=c, fill=True, fill_color=c, fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=260), tooltip=safe_name,
        ).add_to(m)
    _render_map(m)

    # Class distribution chart
    st.markdown("---")
    if class_counts:
        sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        fig, ax = plt.subplots(figsize=(6, max(3, len(sorted_classes) * 0.35)))
        fig.patch.set_facecolor(_BG)
        ax.set_facecolor(_SURFACE)
        cls_names = [item[0][:25] for item in sorted_classes]
        cls_vals = [item[1] for item in sorted_classes]
        cls_cols = [class_colors.get(item[0], _ACCENT) for item in sorted_classes]
        ax.barh(range(len(cls_names)), cls_vals, color=cls_cols, alpha=0.85)
        ax.set_yticks(range(len(cls_names)))
        ax.set_yticklabels(cls_names, color=_TEXT2, fontsize=9)
        ax.set_xlabel("Occurrences", color=_TEXT2, fontsize=10)
        ax.set_title("Fossil Occurrences by Class", color=_TEXT, fontsize=11, pad=8)
        ax.tick_params(axis="x", colors=_TEXT2, labelsize=9)
        ax.grid(True, axis="x", color=_GRID, linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(_GRID)
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Legend
    if class_colors:
        legend_items = " ".join([
            f'<span style="color:{c}; font-size:0.8rem;">&#9679; {escape(n[:20])}</span>'
            for n, c in list(class_colors.items())[:12]
        ])
        st.markdown(
            f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin:0.5rem 0;">{legend_items}</div>',
            unsafe_allow_html=True)

    _show_table_and_download(sites, "fossil", "fossil_occurrences.csv")


def _render_mesoamerican():
    """Mode 9 - Mayan, Aztec & Mesoamerican Sites."""
    st.markdown("#### Mayan, Aztec & Mesoamerican Sites")
    st.caption("Chichen Itza, Teotihuacan, Tikal, Palenque, Olmec heads, and 25+ sites across Central America.")

    culture_filter = st.radio("Filter by culture", ["All", "Maya", "Aztec/Toltec", "Olmec", "Zapotec/Mixtec"],
                              horizontal=True, key="meso_filter")
    maya_kw = ["maya", "chichen", "tikal", "palenque", "uxmal", "copan", "calakmul", "tulum",
               "bonampak", "mirador", "yaxchilan", "caracol", "coba", "kabah", "izapa", "tonina"]
    aztec_kw = ["aztec", "tenochtitlan", "templo mayor", "teotihuacan", "tula", "cholula", "xochicalco"]
    olmec_kw = ["olmec", "la venta", "san lorenzo", "tres zapotes"]
    zapotec_kw = ["zapotec", "mixtec", "monte alban", "mitla"]

    if culture_filter == "Maya":
        sites = [s for s in MESOAMERICAN_SITES
                 if any(kw in s["name"].lower() or kw in s["description"].lower() for kw in maya_kw)]
    elif culture_filter == "Aztec/Toltec":
        sites = [s for s in MESOAMERICAN_SITES
                 if any(kw in s["name"].lower() or kw in s["description"].lower() for kw in aztec_kw)]
    elif culture_filter == "Olmec":
        sites = [s for s in MESOAMERICAN_SITES
                 if any(kw in s["name"].lower() or kw in s["description"].lower() for kw in olmec_kw)]
    elif culture_filter == "Zapotec/Mixtec":
        sites = [s for s in MESOAMERICAN_SITES
                 if any(kw in s["name"].lower() or kw in s["description"].lower() for kw in zapotec_kw)]
    else:
        sites = MESOAMERICAN_SITES

    _show_stats(sites, "Mesoamerican Sites")
    m = _build_map(sites, color="#10b981", zoom=5, icon_name="tree")
    _render_map(m)

    st.markdown("---")
    _country_chart(sites, "Mesoamerican Sites by Country")

    # Culture pie chart
    if sites:
        culture_counts: dict[str, int] = {"Maya": 0, "Aztec/Toltec": 0, "Olmec": 0,
                                           "Zapotec/Mixtec": 0, "Other": 0}
        for s in sites:
            name_desc = (s["name"] + " " + s["description"]).lower()
            if any(kw in name_desc for kw in maya_kw):
                culture_counts["Maya"] += 1
            elif any(kw in name_desc for kw in aztec_kw):
                culture_counts["Aztec/Toltec"] += 1
            elif any(kw in name_desc for kw in olmec_kw):
                culture_counts["Olmec"] += 1
            elif any(kw in name_desc for kw in zapotec_kw):
                culture_counts["Zapotec/Mixtec"] += 1
            else:
                culture_counts["Other"] += 1

        # Remove zero entries
        culture_counts = {k: v for k, v in culture_counts.items() if v > 0}
        if culture_counts:
            fig, ax = plt.subplots(figsize=(5, 4))
            fig.patch.set_facecolor(_BG)
            ax.set_facecolor(_BG)
            pie_colors = ["#10b981", "#f59e0b", "#ef4444", "#8b5cf6", _MUTED]
            wedges, texts, autotexts = ax.pie(
                culture_counts.values(), labels=culture_counts.keys(),
                colors=pie_colors[:len(culture_counts)], autopct="%1.0f%%",
                textprops={"color": _TEXT, "fontsize": 9},
            )
            for at in autotexts:
                at.set_color(_TEXT)
                at.set_fontsize(8)
            ax.set_title("Sites by Culture", color=_TEXT, fontsize=11, pad=8)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    _show_table_and_download(sites, "meso", "mesoamerican_sites.csv")


def _render_south_american():
    """Mode 10 - Inca & South American Sites."""
    st.markdown("#### Inca & South American Archaeological Sites")
    st.caption("Machu Picchu, Nazca Lines, Tiwanaku, Chan Chan, and 20+ sites across the continent.")

    countries = sorted(set(s["country"] for s in SOUTH_AMERICAN_SITES))
    sel_countries = st.multiselect("Filter by country", countries, default=[], key="archd_sa_countries",
                                   help="Leave empty to show all")
    sites = [s for s in SOUTH_AMERICAN_SITES if (not sel_countries or s["country"] in sel_countries)]

    _show_stats(sites, "South American Sites")
    m = _build_map(sites, color="#f97316", zoom=4, icon_name="mountain")
    _render_map(m)

    st.markdown("---")
    _country_chart(sites, "South American Sites by Country")

    # Elevation-latitude scatter (approximate)
    if sites:
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor(_BG)
        ax.set_facecolor(_SURFACE)
        lats = [s["lat"] for s in sites]
        lons = [s["lon"] for s in sites]
        ax.scatter(lons, lats, c="#f97316", s=60, alpha=0.8, edgecolors=_GRID, linewidths=0.5)
        for s in sites:
            ax.annotate(s["name"][:15], (s["lon"], s["lat"]),
                        fontsize=6, color=_TEXT2, textcoords="offset points",
                        xytext=(5, 3))
        ax.set_xlabel("Longitude", color=_TEXT2, fontsize=10)
        ax.set_ylabel("Latitude", color=_TEXT2, fontsize=10)
        ax.set_title("Site Distribution Map (lat/lon)", color=_TEXT, fontsize=11, pad=8)
        ax.tick_params(axis="both", colors=_TEXT2, labelsize=9)
        ax.grid(True, color=_GRID, linewidth=0.5, alpha=0.5)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(_GRID)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    _show_table_and_download(sites, "sa", "south_american_sites.csv")


# ═══════════════════════════════════════════════════════════════════════
# MAP MODE REGISTRY
# ═══════════════════════════════════════════════════════════════════════
_MODES = {
    "Seven Wonders": _render_seven_wonders,
    "Megalithic Sites": _render_megalithic,
    "Ancient Lost Cities": _render_lost_cities,
    "Egyptian Pyramids & Temples": _render_egyptian,
    "Roman Empire Sites": _render_roman,
    "Underwater Archaeology": _render_underwater,
    "Cave Paintings & Rock Art": _render_cave_art,
    "Fossil Sites (PBDB)": _render_fossils,
    "Mayan, Aztec & Mesoamerican": _render_mesoamerican,
    "Inca & South American": _render_south_american,
}


# ═══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════
def render_archaeology_deep_tab():
    """Main entry point for the Archaeological Deep Dive tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header emerald"><h4>\U0001f3fa Archaeological Deep Dive</h4>'
        '<p>Ancient wonders, megalithic sites, lost civilizations & archaeological treasures</p></div>',
        unsafe_allow_html=True,
    )

    # ── Mode Selector ──
    mode = st.radio(
        "Exploration Mode",
        list(_MODES.keys()),
        index=0,
        key="arch_deep_mode",
        horizontal=False,
    )

    st.markdown("---")

    # ── Render selected mode ──
    renderer = _MODES.get(mode)
    if renderer:
        renderer()
    else:
        st.error("Unknown mode selected.")
