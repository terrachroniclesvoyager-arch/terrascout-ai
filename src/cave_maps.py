# -*- coding: utf-8 -*-
"""
Caves, Karst & Underground World module for TerraScout AI.
Explores cave systems, cenotes, underground rivers, lava tubes, karst landscapes,
and cave biodiversity using curated datasets and the Overpass API.
All data sources are free and require no API keys.
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
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════
MAP_MODES = [
    "World's Longest Caves",
    "Deepest Caves",
    "Show Caves & Tourist",
    "Cave Paintings & Art",
    "Cenotes & Sinkholes",
    "Lava Tubes",
    "Underground Rivers",
    "Crystal Caves",
    "Cave Biodiversity",
    "Karst Landscapes",
]

MODE_DESCRIPTIONS = {
    "World's Longest Caves": (
        "The longest surveyed cave systems on Earth, ranked by total passage length. "
        "Mammoth Cave in Kentucky holds the record at over 685 km of mapped passages. "
        "Many of these systems are still being actively explored and surveyed."
    ),
    "Deepest Caves": (
        "The deepest caves plunge over 2 km below the surface. Veryovkina Cave in Georgia "
        "(Caucasus) holds the world depth record at 2,212 m. Reaching these depths requires "
        "weeks of underground expedition through vertical shafts and sumps."
    ),
    "Show Caves & Tourist": (
        "Commercially developed caves open to the public, featuring lighting, walkways, "
        "and guided tours. From the glowworms of Waitomo to the grandeur of Carlsbad "
        "Caverns, these caves welcome millions of visitors annually."
    ),
    "Cave Paintings & Art": (
        "Prehistoric cave art sites preserving humanity's earliest artistic expressions. "
        "The oldest known paintings date back over 45,000 years. These fragile treasures "
        "include Lascaux, Altamira, Chauvet, and recently discovered sites in Indonesia."
    ),
    "Cenotes & Sinkholes": (
        "Cenotes are natural sinkholes formed by limestone collapse, exposing groundwater. "
        "The Yucatan Peninsula alone has over 6,000 cenotes. Blue holes are underwater "
        "sinkholes found in coastal karst, including the Great Blue Hole of Belize."
    ),
    "Lava Tubes": (
        "Lava tubes form when the outer surface of a lava flow solidifies while molten lava "
        "continues flowing inside. Found in volcanic regions worldwide, they serve as analogs "
        "for potential habitats on the Moon and Mars."
    ),
    "Underground Rivers": (
        "Subterranean rivers flow through cave systems carved by water over millions of years. "
        "The Puerto Princesa Underground River in the Philippines is one of the longest "
        "navigable underground waterways, stretching over 8 km."
    ),
    "Crystal Caves": (
        "Caves hosting extraordinary mineral formations including giant selenite crystals, "
        "rare speleothems, and unique mineral deposits. The Naica Crystal Cave in Mexico "
        "contained crystals up to 12 m long in 58 degrees C heat."
    ),
    "Cave Biodiversity": (
        "Cave ecosystems harbor unique troglobitic species adapted to perpetual darkness. "
        "Blind cave fish, cave salamanders, transparent crustaceans, and extremophile "
        "bacteria represent millions of years of evolution in isolation."
    ),
    "Karst Landscapes": (
        "Karst terrain forms when soluble rock (limestone, dolomite, gypsum) dissolves, "
        "creating sinkholes, towers, poljes, and vast underground drainage networks. "
        "About 20% of Earth's ice-free land is karst, hosting 25% of the world's population."
    ),
}

MODE_COLORS = {
    "World's Longest Caves": "#06b6d4",
    "Deepest Caves": "#ef4444",
    "Show Caves & Tourist": "#f59e0b",
    "Cave Paintings & Art": "#ec4899",
    "Cenotes & Sinkholes": "#3b82f6",
    "Lava Tubes": "#f97316",
    "Underground Rivers": "#14b8a6",
    "Crystal Caves": "#a855f7",
    "Cave Biodiversity": "#10b981",
    "Karst Landscapes": "#8b5cf6",
}

# ═══════════════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════════════

LONGEST_CAVES = [
    {"name": "Mammoth Cave", "country": "USA", "state": "Kentucky", "length_km": 685.6,
     "lat": 37.187, "lon": -86.100, "notes": "World's longest known cave system, UNESCO World Heritage Site"},
    {"name": "Sistema Sac Actun", "country": "Mexico", "state": "Quintana Roo", "length_km": 376.7,
     "lat": 20.326, "lon": -87.394, "notes": "Longest underwater cave system, connected to Dos Ojos"},
    {"name": "Jewel Cave", "country": "USA", "state": "South Dakota", "length_km": 354.9,
     "lat": 43.729, "lon": -103.830, "notes": "Third longest cave, calcite crystals and formations"},
    {"name": "Sistema Ox Bel Ha", "country": "Mexico", "state": "Quintana Roo", "length_km": 319.0,
     "lat": 20.276, "lon": -87.370, "notes": "Second longest underwater cave, coastal aquifer system"},
    {"name": "Optymistychna Cave", "country": "Ukraine", "state": "Ternopil", "length_km": 257.0,
     "lat": 48.753, "lon": 25.973, "notes": "Longest gypsum cave in the world"},
    {"name": "Wind Cave", "country": "USA", "state": "South Dakota", "length_km": 252.8,
     "lat": 43.556, "lon": -103.483, "notes": "Famous for boxwork formations, one of longest caves"},
    {"name": "Lechuguilla Cave", "country": "USA", "state": "New Mexico", "length_km": 241.0,
     "lat": 32.141, "lon": -104.505, "notes": "Pristine cave with rare formations, restricted access"},
    {"name": "Fisher Ridge Cave System", "country": "USA", "state": "Kentucky", "length_km": 200.0,
     "lat": 37.200, "lon": -86.070, "notes": "Near Mammoth Cave, may eventually connect"},
    {"name": "Hoelloch", "country": "Switzerland", "state": "Schwyz", "length_km": 207.5,
     "lat": 46.978, "lon": 8.765, "notes": "Longest cave in Switzerland, alpine karst system"},
    {"name": "Clearwater Cave", "country": "Malaysia", "state": "Sarawak", "length_km": 236.0,
     "lat": 4.129, "lon": 114.892, "notes": "Longest cave in Southeast Asia, Mulu National Park"},
    {"name": "Sistema Huautla", "country": "Mexico", "state": "Oaxaca", "length_km": 89.1,
     "lat": 18.120, "lon": -96.835, "notes": "Deepest cave in the Western Hemisphere"},
    {"name": "Ogof Draenen", "country": "UK", "state": "Wales", "length_km": 76.5,
     "lat": 51.802, "lon": -3.109, "notes": "Longest cave in the UK"},
    {"name": "Ease Gill Caverns", "country": "UK", "state": "Yorkshire", "length_km": 85.0,
     "lat": 54.196, "lon": -2.511, "notes": "Longest connected cave in the UK"},
    {"name": "Gouffre de la Pierre Saint-Martin", "country": "France/Spain", "state": "Pyrenees", "length_km": 83.0,
     "lat": 42.970, "lon": -0.766, "notes": "Massive alpine cave system crossing the border"},
    {"name": "Reseau Felix Trombe", "country": "France", "state": "Haute-Garonne", "length_km": 110.0,
     "lat": 43.045, "lon": 0.576, "notes": "Longest cave in France, Pyrenean marble"},
    {"name": "Siebenhengste-Hohgant", "country": "Switzerland", "state": "Bern", "length_km": 161.0,
     "lat": 46.805, "lon": 7.811, "notes": "Major alpine cave system in the Bernese Oberland"},
    {"name": "Ogof Ffynnon Ddu", "country": "UK", "state": "Wales", "length_km": 56.5,
     "lat": 51.850, "lon": -3.574, "notes": "Deepest cave in the UK at 308m depth"},
    {"name": "Tham Luang", "country": "Thailand", "state": "Chiang Rai", "length_km": 10.3,
     "lat": 20.383, "lon": 99.867, "notes": "Famous for the 2018 rescue of 12 boys and their coach"},
    {"name": "Postojna Cave", "country": "Slovenia", "state": "Inner Carniola", "length_km": 24.1,
     "lat": 45.782, "lon": 14.204, "notes": "Most visited show cave in Europe, home of the olm"},
    {"name": "Carlsbad Caverns", "country": "USA", "state": "New Mexico", "length_km": 63.0,
     "lat": 32.148, "lon": -104.556, "notes": "Spectacular Big Room, 400,000+ bats, UNESCO site"},
]

DEEPEST_CAVES = [
    {"name": "Veryovkina Cave", "country": "Georgia", "state": "Abkhazia", "depth_m": 2212,
     "lat": 43.410, "lon": 40.362, "notes": "Deepest known cave on Earth, Arabika Massif"},
    {"name": "Krubera Cave (Voronya)", "country": "Georgia", "state": "Abkhazia", "depth_m": 2199,
     "lat": 43.410, "lon": 40.362, "notes": "Former deepest cave, Arabika Massif"},
    {"name": "Sarma Cave", "country": "Georgia", "state": "Abkhazia", "depth_m": 1830,
     "lat": 43.384, "lon": 40.380, "notes": "Third deepest, also on Arabika Massif"},
    {"name": "Illyuzia-Mezhonnogo-Snezhnaya", "country": "Georgia", "state": "Abkhazia", "depth_m": 1760,
     "lat": 43.398, "lon": 40.400, "notes": "Connected deep system on Arabika"},
    {"name": "Lamprechtsofen", "country": "Austria", "state": "Salzburg", "depth_m": 1735,
     "lat": 47.524, "lon": 12.827, "notes": "Deepest through-trip cave, Leoganger Steinberge"},
    {"name": "Gouffre Mirolda", "country": "France", "state": "Haute-Savoie", "depth_m": 1733,
     "lat": 46.242, "lon": 6.758, "notes": "Deepest in France, Haut-Giffre massif"},
    {"name": "Gouffre Jean-Bernard", "country": "France", "state": "Haute-Savoie", "depth_m": 1602,
     "lat": 46.167, "lon": 6.767, "notes": "Former world depth record holder"},
    {"name": "Torca del Cerro del Cuevon", "country": "Spain", "state": "Asturias", "depth_m": 1589,
     "lat": 43.210, "lon": -4.849, "notes": "Picos de Europa, deep alpine shaft"},
    {"name": "Gouffre Berger", "country": "France", "state": "Isere", "length_km": 1271,
     "depth_m": 1271, "lat": 45.080, "lon": 5.548, "notes": "First cave deeper than 1000 m (1956)"},
    {"name": "Sistema del Alto del Tejuelo", "country": "Spain", "state": "Cantabria", "depth_m": 1507,
     "lat": 43.180, "lon": -4.750, "notes": "Deep system in Picos de Europa"},
    {"name": "Ceki 2", "country": "Slovenia", "state": "Julian Alps", "depth_m": 1502,
     "lat": 46.257, "lon": 13.786, "notes": "Kanin massif, deepest in Slovenia"},
    {"name": "Shakta Vjacheslav Pantjukhina", "country": "Georgia", "state": "Abkhazia", "depth_m": 1508,
     "lat": 43.380, "lon": 40.374, "notes": "Deep shaft on the Arabika Massif"},
    {"name": "Sima de la Cornisa", "country": "Spain", "state": "Asturias", "depth_m": 1507,
     "lat": 43.192, "lon": -4.830, "notes": "Picos de Europa deep pot system"},
    {"name": "Schwersystem", "country": "Austria", "state": "Salzburg", "depth_m": 1340,
     "lat": 47.460, "lon": 13.210, "notes": "Hagengebirge massif, glacial karst"},
    {"name": "Reseau de la Pierre Saint-Martin", "country": "France/Spain", "state": "Pyrenees", "depth_m": 1408,
     "lat": 42.970, "lon": -0.766, "notes": "Classic deep system crossing French-Spanish border"},
    {"name": "Lukina Jama-Trojama", "country": "Croatia", "state": "Velebit", "depth_m": 1431,
     "lat": 44.771, "lon": 14.973, "notes": "Deepest in Croatia, Northern Velebit NP"},
    {"name": "Complesso del Foran del Muss", "country": "Italy", "state": "Friuli-Venezia Giulia", "depth_m": 1249,
     "lat": 46.361, "lon": 13.438, "notes": "Canin massif, Italian-Slovenian border"},
    {"name": "Abisso Paolo Roversi", "country": "Italy", "state": "Tuscany", "depth_m": 1350,
     "lat": 44.070, "lon": 10.230, "notes": "Apuan Alps, deepest cave in Italy"},
    {"name": "Kijahe Xontjoa", "country": "Mexico", "state": "Oaxaca", "depth_m": 1223,
     "lat": 18.140, "lon": -96.800, "notes": "Sierra Mazateca, deep tropical karst"},
    {"name": "Hirlatzhohle", "country": "Austria", "state": "Upper Austria", "depth_m": 1175,
     "lat": 47.534, "lon": 13.663, "notes": "Dachstein massif, glaciokarst system"},
]

SHOW_CAVES = [
    {"name": "Carlsbad Caverns", "country": "USA", "state": "New Mexico", "visitors_yr": 440000,
     "lat": 32.148, "lon": -104.556, "notes": "Big Room, bat flights, self-guided tours, UNESCO site"},
    {"name": "Postojna Cave", "country": "Slovenia", "state": "Inner Carniola", "visitors_yr": 900000,
     "lat": 45.782, "lon": 14.204, "notes": "Electric train ride, Proteus olm, 200+ years of tourism"},
    {"name": "Waitomo Glowworm Caves", "country": "New Zealand", "state": "Waikato", "visitors_yr": 500000,
     "lat": -38.261, "lon": 175.106, "notes": "Bioluminescent glowworms, boat rides through grottos"},
    {"name": "Mammoth Cave", "country": "USA", "state": "Kentucky", "visitors_yr": 500000,
     "lat": 37.187, "lon": -86.100, "notes": "World's longest cave, multiple tour options, UNESCO"},
    {"name": "Skocjan Caves", "country": "Slovenia", "state": "Karst", "visitors_yr": 200000,
     "lat": 45.663, "lon": 13.990, "notes": "Massive underground canyon, UNESCO World Heritage"},
    {"name": "Jenolan Caves", "country": "Australia", "state": "New South Wales", "visitors_yr": 250000,
     "lat": -33.820, "lon": 150.024, "notes": "Oldest open caves in the world, 340 million years old"},
    {"name": "Cuevas del Drach", "country": "Spain", "state": "Mallorca", "visitors_yr": 700000,
     "lat": 39.537, "lon": 3.332, "notes": "Underground lake Martel, classical music concerts"},
    {"name": "Reed Flute Cave", "country": "China", "state": "Guangxi", "visitors_yr": 800000,
     "lat": 25.301, "lon": 110.270, "notes": "Multicolored lighting, 240m of limestone cave"},
    {"name": "Cango Caves", "country": "South Africa", "state": "Western Cape", "visitors_yr": 200000,
     "lat": -33.394, "lon": 22.214, "notes": "Dripstone formations, adventure and heritage tours"},
    {"name": "Eisriesenwelt", "country": "Austria", "state": "Salzburg", "visitors_yr": 150000,
     "lat": 47.503, "lon": 13.189, "notes": "World's largest ice cave, 42 km of passages"},
    {"name": "Blue Grotto (Grotta Azzurra)", "country": "Italy", "state": "Capri", "visitors_yr": 500000,
     "lat": 40.561, "lon": 14.205, "notes": "Sea cave with brilliant blue water glow"},
    {"name": "Phong Nha Cave", "country": "Vietnam", "state": "Quang Binh", "visitors_yr": 350000,
     "lat": 17.592, "lon": 106.283, "notes": "River cave, UNESCO World Heritage, near Son Doong"},
    {"name": "Jewel Cave", "country": "USA", "state": "South Dakota", "visitors_yr": 100000,
     "lat": 43.729, "lon": -103.830, "notes": "Calcite nailhead spar crystals, scenic tour"},
    {"name": "Luray Caverns", "country": "USA", "state": "Virginia", "visitors_yr": 500000,
     "lat": 38.665, "lon": -78.484, "notes": "Great Stalacpipe Organ, mirrored Dream Lake"},
    {"name": "Grotte di Frasassi", "country": "Italy", "state": "Marche", "visitors_yr": 300000,
     "lat": 43.401, "lon": 12.964, "notes": "Massive caverns, Ancona Grande room 240m long"},
    {"name": "Aggtelek Caves", "country": "Hungary", "state": "Aggtelek", "visitors_yr": 250000,
     "lat": 48.470, "lon": 20.490, "notes": "Baradla Cave system, UNESCO World Heritage"},
    {"name": "Cradle of Humankind", "country": "South Africa", "state": "Gauteng", "visitors_yr": 200000,
     "lat": -25.930, "lon": 27.780, "notes": "Sterkfontein Caves, early hominid fossils, UNESCO"},
    {"name": "Grottes de Han", "country": "Belgium", "state": "Namur", "visitors_yr": 350000,
     "lat": 50.123, "lon": 5.183, "notes": "Underground river Lesse, large chambers"},
    {"name": "Fingal's Cave", "country": "UK", "state": "Scotland", "visitors_yr": 50000,
     "lat": 56.432, "lon": -6.340, "notes": "Basalt column sea cave on Staffa, Mendelssohn overture"},
    {"name": "Batu Caves", "country": "Malaysia", "state": "Selangor", "visitors_yr": 1500000,
     "lat": 3.238, "lon": 101.684, "notes": "Hindu temple cave, 272 steps, Thaipusam festival"},
]

CAVE_ART_SITES = [
    {"name": "Lascaux Cave", "country": "France", "state": "Dordogne", "age_years": 17000,
     "lat": 45.054, "lon": 1.169, "notes": "Hall of the Bulls, 600+ paintings, replica open to public"},
    {"name": "Altamira Cave", "country": "Spain", "state": "Cantabria", "age_years": 36000,
     "lat": 43.378, "lon": -4.121, "notes": "Polychrome bison ceiling, UNESCO, limited access"},
    {"name": "Chauvet Cave", "country": "France", "state": "Ardeche", "age_years": 36000,
     "lat": 44.388, "lon": 4.418, "notes": "Oldest known cave paintings in Europe, lions and rhinos"},
    {"name": "Leang Tedongnge", "country": "Indonesia", "state": "Sulawesi", "age_years": 45500,
     "lat": -4.975, "lon": 119.860, "notes": "Oldest known figurative art, Sulawesi warty pig"},
    {"name": "Cueva de las Manos", "country": "Argentina", "state": "Santa Cruz", "age_years": 9300,
     "lat": -47.153, "lon": -70.665, "notes": "Cave of the Hands, stenciled handprints, UNESCO"},
    {"name": "Bhimbetka Rock Shelters", "country": "India", "state": "Madhya Pradesh", "age_years": 30000,
     "lat": 22.937, "lon": 77.612, "notes": "500+ shelters with prehistoric paintings, UNESCO"},
    {"name": "Cosquer Cave", "country": "France", "state": "Marseille", "age_years": 27000,
     "lat": 43.201, "lon": 5.447, "notes": "Underwater entrance, sea animals, handprints"},
    {"name": "Font-de-Gaume", "country": "France", "state": "Dordogne", "age_years": 17000,
     "lat": 44.934, "lon": 1.005, "notes": "Last original polychrome cave open to public"},
    {"name": "Magura Cave", "country": "Bulgaria", "state": "Vidin", "age_years": 8000,
     "lat": 43.728, "lon": 22.602, "notes": "Prehistoric paintings with bat guano, large chambers"},
    {"name": "Pech Merle", "country": "France", "state": "Lot", "age_years": 25000,
     "lat": 44.507, "lon": 1.640, "notes": "Spotted horses, handprints, still open to visitors"},
    {"name": "Ubirr Rock Art", "country": "Australia", "state": "Northern Territory", "age_years": 40000,
     "lat": -12.407, "lon": 132.954, "notes": "Aboriginal X-ray art, Kakadu NP, UNESCO"},
    {"name": "Serra da Capivara", "country": "Brazil", "state": "Piaui", "age_years": 25000,
     "lat": -8.833, "lon": -42.550, "notes": "Largest concentration of rock art in Americas, UNESCO"},
    {"name": "Tassili n'Ajjer", "country": "Algeria", "state": "Sahara", "age_years": 12000,
     "lat": 25.670, "lon": 8.000, "notes": "15,000+ Saharan rock engravings, green Sahara period"},
    {"name": "Niaux Cave", "country": "France", "state": "Ariege", "age_years": 14000,
     "lat": 42.820, "lon": 1.595, "notes": "Salon Noir with bison, horses, ibex paintings"},
    {"name": "Coliboaia Cave", "country": "Romania", "state": "Bihor", "age_years": 35000,
     "lat": 46.556, "lon": 22.540, "notes": "Oldest cave art in Central Europe, charcoal drawings"},
    {"name": "Apollo 11 Cave", "country": "Namibia", "state": "Karas", "age_years": 30000,
     "lat": -27.750, "lon": 17.083, "notes": "Oldest known art in Africa, animal figure slabs"},
    {"name": "Gabarnmung Rock Shelter", "country": "Australia", "state": "Northern Territory", "age_years": 28000,
     "lat": -13.983, "lon": 133.117, "notes": "Pillar-supported shelter, layered art spanning millennia"},
    {"name": "Cave of El Castillo", "country": "Spain", "state": "Cantabria", "age_years": 40800,
     "lat": 43.290, "lon": -3.968, "notes": "Red disk oldest known European art, stenciled hands"},
    {"name": "Drakensberg Rock Art", "country": "South Africa", "state": "KwaZulu-Natal", "age_years": 3000,
     "lat": -29.350, "lon": 29.350, "notes": "San Bushmen paintings, UNESCO, 35,000+ images"},
    {"name": "Rouffignac Cave", "country": "France", "state": "Dordogne", "age_years": 13000,
     "lat": 45.029, "lon": 0.985, "notes": "Cave of 100 mammoths, electric train tour"},
]

CENOTES_SINKHOLES = [
    {"name": "Great Blue Hole", "country": "Belize", "state": "Lighthouse Reef", "diameter_m": 300,
     "depth_m": 124, "lat": 17.316, "lon": -87.535,
     "notes": "Iconic marine sinkhole, UNESCO, formed during ice ages"},
    {"name": "Cenote Ik Kil", "country": "Mexico", "state": "Yucatan", "diameter_m": 60,
     "depth_m": 40, "lat": 20.668, "lon": -88.551,
     "notes": "Sacred Mayan cenote near Chichen Itza, open for swimming"},
    {"name": "Dean's Blue Hole", "country": "Bahamas", "state": "Long Island", "diameter_m": 25,
     "depth_m": 202, "lat": 23.107, "lon": -75.105,
     "notes": "Deepest known blue hole for decades (now surpassed)"},
    {"name": "Cenote Dos Ojos", "country": "Mexico", "state": "Quintana Roo", "diameter_m": 100,
     "depth_m": 119, "lat": 20.325, "lon": -87.391,
     "notes": "Two eyes cenote, world-class cave diving, crystal clear water"},
    {"name": "Dragon Hole (Yongle)", "country": "China", "state": "Paracel Islands", "diameter_m": 130,
     "depth_m": 300, "lat": 16.518, "lon": 111.765,
     "notes": "Deepest known underwater sinkhole in the world"},
    {"name": "Cenote Suytun", "country": "Mexico", "state": "Yucatan", "diameter_m": 50,
     "depth_m": 5, "lat": 20.698, "lon": -88.474,
     "notes": "Instagram-famous cenote with single light beam"},
    {"name": "Cenote Samula", "country": "Mexico", "state": "Yucatan", "diameter_m": 40,
     "depth_m": 30, "lat": 20.724, "lon": -88.224,
     "notes": "Underground cenote with tree roots hanging from ceiling"},
    {"name": "Xiaozhai Tiankeng", "country": "China", "state": "Chongqing", "diameter_m": 626,
     "depth_m": 662, "lat": 30.761, "lon": 108.855,
     "notes": "World's deepest sinkhole (tiankeng), lush ecosystem inside"},
    {"name": "Dashiwei Tiankeng", "country": "China", "state": "Guangxi", "diameter_m": 600,
     "depth_m": 613, "lat": 24.460, "lon": 106.950,
     "notes": "Group of massive sinkholes, ancient forest at bottom"},
    {"name": "Sima Humboldt", "country": "Venezuela", "state": "Bolivar", "diameter_m": 352,
     "depth_m": 314, "lat": 5.300, "lon": -64.967,
     "notes": "Sinkhole atop a tepui, isolated ecosystem, quartzite"},
    {"name": "Crveno Jezero (Red Lake)", "country": "Croatia", "state": "Dalmatia", "diameter_m": 200,
     "depth_m": 530, "lat": 43.434, "lon": 17.065,
     "notes": "Collapsed cave with deep lake, red cliff walls"},
    {"name": "Cenote Angelita", "country": "Mexico", "state": "Quintana Roo", "diameter_m": 30,
     "depth_m": 60, "lat": 20.260, "lon": -87.404,
     "notes": "Underwater river of hydrogen sulfide at 30m depth"},
    {"name": "Sawai Man Singh Baoli", "country": "India", "state": "Rajasthan", "diameter_m": 50,
     "depth_m": 25, "lat": 26.897, "lon": 75.821,
     "notes": "Stepwell sinkhole, ancient water harvesting structure"},
    {"name": "Pozzo del Merro", "country": "Italy", "state": "Lazio", "diameter_m": 90,
     "depth_m": 392, "lat": 42.102, "lon": 12.867,
     "notes": "Deepest known sinkhole in Europe, near Rome"},
    {"name": "Cenote Zaci", "country": "Mexico", "state": "Yucatan", "diameter_m": 120,
     "depth_m": 80, "lat": 20.688, "lon": -88.210,
     "notes": "Open cenote in the heart of Valladolid, catfish"},
    {"name": "Harwood Hole", "country": "New Zealand", "state": "Nelson", "diameter_m": 50,
     "depth_m": 357, "lat": -41.014, "lon": 172.834,
     "notes": "Deepest natural vertical shaft in NZ, marble karst"},
    {"name": "El Zacaton", "country": "Mexico", "state": "Tamaulipas", "diameter_m": 116,
     "depth_m": 339, "lat": 22.994, "lon": -98.162,
     "notes": "Deepest known water-filled sinkhole, volcanic origin"},
    {"name": "Qattara Depression", "country": "Egypt", "state": "Western Desert", "diameter_m": 80000,
     "depth_m": 133, "lat": 29.500, "lon": 26.900,
     "notes": "Massive wind-eroded depression, 134 m below sea level"},
    {"name": "Bottomless Lakes", "country": "USA", "state": "New Mexico", "diameter_m": 30,
     "depth_m": 27, "lat": 33.312, "lon": -104.332,
     "notes": "Chain of cenote-like sinkhole lakes in gypsum karst"},
    {"name": "Mount Gambier Blue Lake", "country": "Australia", "state": "South Australia", "diameter_m": 1100,
     "depth_m": 77, "lat": -37.847, "lon": 140.770,
     "notes": "Volcanic crater lake that turns vivid blue each November"},
]

LAVA_TUBES = [
    {"name": "Kazumura Cave", "country": "USA", "state": "Hawaii", "length_km": 65.5,
     "lat": 19.521, "lon": -155.198, "notes": "World's longest and deepest lava tube, Kilauea flows"},
    {"name": "Manjanggul (Manjang)", "country": "South Korea", "state": "Jeju", "length_km": 7.4,
     "lat": 33.528, "lon": 126.771, "notes": "UNESCO Geomunkeum system, spectacular lava formations"},
    {"name": "Cueva del Viento", "country": "Spain", "state": "Tenerife", "length_km": 18.0,
     "lat": 28.344, "lon": -16.519, "notes": "Fifth longest lava tube, multi-level system"},
    {"name": "Thurston Lava Tube (Nahuku)", "country": "USA", "state": "Hawaii", "length_km": 0.6,
     "lat": 19.413, "lon": -155.235, "notes": "Most visited lava tube, easy walkthrough, Volcanoes NP"},
    {"name": "Raufarholshellir", "country": "Iceland", "state": "Southern", "length_km": 1.36,
     "lat": 63.931, "lon": -21.395, "notes": "Lava Falls walkway, ice formations, near Reykjavik"},
    {"name": "Undara Lava Tubes", "country": "Australia", "state": "Queensland", "length_km": 100.0,
     "lat": -18.282, "lon": 144.588, "notes": "190,000-year-old tubes, unique biodiversity"},
    {"name": "Vidgelmir", "country": "Iceland", "state": "Western", "length_km": 1.59,
     "lat": 64.751, "lon": -20.764, "notes": "Largest lava cave in Iceland, colorful mineral deposits"},
    {"name": "Gruta das Torres", "country": "Portugal", "state": "Azores (Pico)", "length_km": 5.15,
     "lat": 38.493, "lon": -28.471, "notes": "Longest lava tube in Portugal and Atlantic islands"},
    {"name": "Cueva de los Verdes", "country": "Spain", "state": "Lanzarote", "length_km": 6.1,
     "lat": 29.161, "lon": -13.436, "notes": "Part of Atlantida Tunnel, concert venue inside"},
    {"name": "Surtshellir", "country": "Iceland", "state": "Western", "length_km": 1.97,
     "lat": 64.779, "lon": -20.599, "notes": "Viking age shelter, historical artifacts found inside"},
    {"name": "Kaumana Caves", "country": "USA", "state": "Hawaii", "length_km": 40.2,
     "lat": 19.748, "lon": -155.140, "notes": "1881 Mauna Loa flow tube, free public access"},
    {"name": "Valentine Cave", "country": "USA", "state": "California", "length_km": 0.5,
     "lat": 41.711, "lon": -121.526, "notes": "Lava Beds NM, perfect tube cross-section"},
    {"name": "Jungnyeong Lava Tube", "country": "South Korea", "state": "Jeju", "length_km": 3.5,
     "lat": 33.440, "lon": 126.720, "notes": "UNESCO, multi-colored carbonate formations"},
    {"name": "Ana Te Pahu", "country": "Chile", "state": "Easter Island", "length_km": 1.0,
     "lat": -27.120, "lon": -109.380, "notes": "Rapa Nui lava tube, used as shelter by islanders"},
    {"name": "Leviathan Cave", "country": "Kenya", "state": "Eastern", "length_km": 12.5,
     "lat": -1.850, "lon": 37.900, "notes": "Longest lava tube in Africa, Chyulu Hills"},
    {"name": "Hana Lava Tube (Ka'eleku)", "country": "USA", "state": "Hawaii (Maui)", "length_km": 0.5,
     "lat": 20.797, "lon": -156.100, "notes": "Self-guided tour through Maui lava tube"},
    {"name": "Susuki Lava Tube", "country": "Japan", "state": "Shizuoka", "length_km": 0.3,
     "lat": 35.383, "lon": 138.738, "notes": "Fuji lava tube, near Aokigahara forest"},
    {"name": "Cueva del Llano", "country": "Spain", "state": "Fuerteventura", "length_km": 0.65,
     "lat": 28.595, "lon": -14.010, "notes": "Unique cave spider and isopod species"},
    {"name": "Deer Cave", "country": "Malaysia", "state": "Sarawak", "length_km": 1.7,
     "lat": 4.040, "lon": 114.820, "notes": "World's largest cave passage by volume (partial lava)"},
    {"name": "Grjotagja", "country": "Iceland", "state": "Northern", "length_km": 0.1,
     "lat": 65.627, "lon": -16.882, "notes": "Small lava cave with hot spring, Game of Thrones site"},
]

UNDERGROUND_RIVERS = [
    {"name": "Puerto Princesa Underground River", "country": "Philippines", "state": "Palawan",
     "length_km": 8.2, "lat": 10.168, "lon": 118.920,
     "notes": "UNESCO, longest navigable underground river, limestone karst"},
    {"name": "Son Doong Cave River", "country": "Vietnam", "state": "Quang Binh",
     "length_km": 9.0, "lat": 17.456, "lon": 106.140,
     "notes": "World's largest cave passage, underground river and jungle"},
    {"name": "Waitomo Caves Underground Stream", "country": "New Zealand", "state": "Waikato",
     "length_km": 3.5, "lat": -38.261, "lon": 175.106,
     "notes": "Glowworm-lit underground river, boat tours through caves"},
    {"name": "Riviere Souterraine de Labouiche", "country": "France", "state": "Ariege",
     "length_km": 1.5, "lat": 43.050, "lon": 1.617,
     "notes": "Longest navigable underground river in Europe open to tourists"},
    {"name": "Timavo River", "country": "Italy/Slovenia", "state": "Friuli-Venezia Giulia",
     "length_km": 38.0, "lat": 45.770, "lon": 13.621,
     "notes": "Flows underground through classic karst for 38 km"},
    {"name": "Reka River (Skocjan)", "country": "Slovenia", "state": "Karst",
     "length_km": 34.0, "lat": 45.663, "lon": 13.990,
     "notes": "Disappears into Skocjan Caves, UNESCO site, rejoins as Timavo"},
    {"name": "Clearwater Cave River", "country": "Malaysia", "state": "Sarawak",
     "length_km": 107.0, "lat": 4.129, "lon": 114.892,
     "notes": "Longest underground river in SE Asia, Gunung Mulu NP"},
    {"name": "Cenote Sac Actun River", "country": "Mexico", "state": "Quintana Roo",
     "length_km": 376.0, "lat": 20.326, "lon": -87.394,
     "notes": "World's longest underwater river/cave, Yucatan aquifer"},
    {"name": "Trebiciano Abyss (Reka)", "country": "Italy", "state": "Trieste",
     "length_km": 5.0, "lat": 45.636, "lon": 13.855,
     "notes": "Deep shaft to underground Reka river, 330m deep"},
    {"name": "Craighead Caverns (Lost Sea)", "country": "USA", "state": "Tennessee",
     "length_km": 2.0, "lat": 35.595, "lon": -84.653,
     "notes": "America's largest underground lake, glass-bottom boat tours"},
    {"name": "Lesse River (Grottes de Han)", "country": "Belgium", "state": "Namur",
     "length_km": 2.0, "lat": 50.123, "lon": 5.183,
     "notes": "River Lesse flows through Han-sur-Lesse caves, boat tours"},
    {"name": "Xe Bang Fai River Cave", "country": "Laos", "state": "Khammouane",
     "length_km": 7.6, "lat": 17.467, "lon": 105.567,
     "notes": "Massive river passage, some of the largest in the world"},
    {"name": "Krizna Jama Underground Lakes", "country": "Slovenia", "state": "Inner Carniola",
     "length_km": 8.3, "lat": 45.722, "lon": 14.403,
     "notes": "22 underground lakes, boat tours, cave bear remains"},
    {"name": "Punkva River (Macocha Abyss)", "country": "Czech Republic", "state": "Moravia",
     "length_km": 2.0, "lat": 49.372, "lon": 16.738,
     "notes": "River through Moravian Karst, boat ride past Macocha chasm"},
    {"name": "Chong Ong Cave River", "country": "Vietnam", "state": "Quang Binh",
     "length_km": 5.0, "lat": 17.520, "lon": 106.120,
     "notes": "Swimming underground river, Phong Nha-Ke Bang NP"},
    {"name": "Cuevas de Bellamar River", "country": "Cuba", "state": "Matanzas",
     "length_km": 3.0, "lat": 23.020, "lon": -81.589,
     "notes": "Underground river and crystal formations, oldest show cave in Cuba"},
    {"name": "Loltun Cave Springs", "country": "Mexico", "state": "Yucatan",
     "length_km": 2.0, "lat": 20.250, "lon": -89.459,
     "notes": "Mayan sacred cave with underground water sources and pottery"},
    {"name": "Oliero Caves Springs", "country": "Italy", "state": "Veneto",
     "length_km": 1.5, "lat": 45.878, "lon": 11.643,
     "notes": "Resurgence of underground rivers, boat tours in crystal water"},
    {"name": "Planina Cave", "country": "Slovenia", "state": "Inner Carniola",
     "length_km": 6.7, "lat": 45.817, "lon": 14.250,
     "notes": "Confluence of two underground rivers inside the cave"},
    {"name": "Cueva del Agua (Tiscar)", "country": "Spain", "state": "Jaen",
     "length_km": 0.5, "lat": 37.753, "lon": -3.003,
     "notes": "Underground waterfall and sacred grotto in Sierras de Cazorla"},
]

CRYSTAL_CAVES = [
    {"name": "Naica Crystal Cave", "country": "Mexico", "state": "Chihuahua",
     "lat": 27.851, "lon": -105.497, "crystal_type": "Selenite (gypsum)",
     "notes": "Giant crystals up to 12m, 58C heat, now re-flooded and sealed"},
    {"name": "Lechuguilla Cave", "country": "USA", "state": "New Mexico",
     "lat": 32.141, "lon": -104.505, "crystal_type": "Aragonite, sulfur, gypsum",
     "notes": "Pristine formations, chandelier ballroom, restricted scientific access"},
    {"name": "Cave of the Crystals (Pulpi)", "country": "Spain", "state": "Almeria",
     "lat": 37.395, "lon": -1.737, "crystal_type": "Selenite (gypsum)",
     "notes": "European equivalent of Naica, 8m geode, opened to limited tours 2019"},
    {"name": "Ochtinska Aragonite Cave", "country": "Slovakia", "state": "Kosice",
     "lat": 48.668, "lon": 20.313, "crystal_type": "Aragonite",
     "notes": "UNESCO, one of only 3 aragonite caves open to public worldwide"},
    {"name": "Crystal Cave (Bermuda)", "country": "Bermuda", "state": "Hamilton Parish",
     "lat": 32.350, "lon": -64.703, "crystal_type": "Calcite stalactites",
     "notes": "Crystal clear underground lake, cathedral ceiling of stalactites"},
    {"name": "Crystal Cave (Skaftafell)", "country": "Iceland", "state": "Vatnajokull",
     "lat": 64.014, "lon": -16.966, "crystal_type": "Ice crystals",
     "notes": "Glacial ice cave with blue crystal formations, seasonal access"},
    {"name": "Mlynky Crystal Cave", "country": "Ukraine", "state": "Ternopil",
     "lat": 48.620, "lon": 25.950, "crystal_type": "Gypsum",
     "notes": "Part of world's longest gypsum cave system, crystal galleries"},
    {"name": "Kaiserstuhl Crystal Cave", "country": "Germany", "state": "Baden-Wurttemberg",
     "lat": 48.088, "lon": 7.648, "crystal_type": "Amethyst, calcite",
     "notes": "Volcanic amethyst geodes in basalt, mineral paradise"},
    {"name": "Cumberland Caverns", "country": "USA", "state": "Tennessee",
     "lat": 35.658, "lon": -85.647, "crystal_type": "Calcite, selenite",
     "notes": "Hall of the Mountain King, underground ballroom concerts"},
    {"name": "Jeita Grotto", "country": "Lebanon", "state": "Keserwan",
     "lat": 33.944, "lon": 35.639, "crystal_type": "Calcite stalactites",
     "notes": "World's longest stalactite (8.2m), underground river and upper gallery"},
    {"name": "Soreq Cave", "country": "Israel", "state": "Jerusalem Hills",
     "lat": 31.753, "lon": 35.029, "crystal_type": "Calcite, aragonite",
     "notes": "Avshalom Cave, dense colorful stalactites and stalagmites"},
    {"name": "Wind Cave Boxwork", "country": "USA", "state": "South Dakota",
     "lat": 43.556, "lon": -103.483, "crystal_type": "Calcite boxwork",
     "notes": "95% of the world's known boxwork formations are here"},
    {"name": "Kungur Ice Cave", "country": "Russia", "state": "Perm Krai",
     "lat": 57.441, "lon": 57.005, "crystal_type": "Ice, gypsum, anhydrite",
     "notes": "Spectacular ice formations, 5.7 km of passages, 70+ lakes"},
    {"name": "Grotta di Castellana", "country": "Italy", "state": "Puglia",
     "lat": 40.878, "lon": 17.148, "crystal_type": "Alabaster, stalactites",
     "notes": "White Grotto of translucent alabaster formations"},
    {"name": "Nettlebed Cave", "country": "New Zealand", "state": "Nelson",
     "lat": -41.048, "lon": 172.783, "crystal_type": "Calcite, aragonite",
     "notes": "Deepest cave in NZ at 889m, rare helictite formations"},
    {"name": "Cheddar Gorge Caves", "country": "UK", "state": "Somerset",
     "lat": 51.284, "lon": -2.764, "crystal_type": "Calcite, stalagmites",
     "notes": "Oldest complete human skeleton in Britain found here"},
    {"name": "Tham Lod Cave", "country": "Thailand", "state": "Mae Hong Son",
     "lat": 19.545, "lon": 98.273, "crystal_type": "Calcite columns",
     "notes": "Massive column formations, coffin caves, Nam Lang river"},
    {"name": "Ali Sadr Cave", "country": "Iran", "state": "Hamadan",
     "lat": 35.298, "lon": 48.307, "crystal_type": "Calcite, travertine",
     "notes": "World's longest water cave boat ride, pedal-boat tours"},
    {"name": "Caverna do Diabo", "country": "Brazil", "state": "Sao Paulo",
     "lat": -24.627, "lon": -48.415, "crystal_type": "Stalactites, flowstone",
     "notes": "Devil's Cave, largest tourist cave in Brazil, Atlantic Forest"},
    {"name": "Marble Caves (Cuevas de Marmol)", "country": "Chile", "state": "Aysen",
     "lat": -46.660, "lon": -72.625, "crystal_type": "Marble (calcium carbonate)",
     "notes": "Turquoise water erosion patterns in marble, boat access only"},
]

CAVE_BIODIVERSITY = [
    {"name": "Movile Cave", "country": "Romania", "state": "Constanta",
     "lat": 43.825, "lon": 28.562, "species_count": 48,
     "notes": "Sealed for 5.5 million years, chemosynthetic ecosystem, 35 endemic species"},
    {"name": "Postojna Cave (Olm)", "country": "Slovenia", "state": "Inner Carniola",
     "lat": 45.782, "lon": 14.204, "species_count": 100,
     "notes": "Home of the olm (Proteus anguinus), Europe's only cave vertebrate"},
    {"name": "Mammoth Cave Ecosystem", "country": "USA", "state": "Kentucky",
     "lat": 37.187, "lon": -86.100, "species_count": 130,
     "notes": "Kentucky cave shrimp, eyeless cave fish, cave crickets"},
    {"name": "Edwards Aquifer Caves", "country": "USA", "state": "Texas",
     "lat": 29.660, "lon": -98.320, "species_count": 80,
     "notes": "Texas blind salamander, Comal Springs riffle beetle, many endemics"},
    {"name": "Bracken Bat Cave", "country": "USA", "state": "Texas",
     "lat": 29.692, "lon": -98.373, "species_count": 15,
     "notes": "Largest bat colony on Earth, 15-20 million Mexican free-tailed bats"},
    {"name": "Deer Cave (Bat Exodus)", "country": "Malaysia", "state": "Sarawak",
     "lat": 4.040, "lon": 114.820, "species_count": 12,
     "notes": "3 million wrinkle-lipped bats, spectacular evening exodus"},
    {"name": "Batu Caves (Biodiversity)", "country": "Malaysia", "state": "Selangor",
     "lat": 3.238, "lon": 101.684, "species_count": 50,
     "notes": "Trapdoor spiders, long-legged centipedes, cave racer snakes"},
    {"name": "Waitomo Cave (Glowworms)", "country": "New Zealand", "state": "Waikato",
     "lat": -38.261, "lon": 175.106, "species_count": 30,
     "notes": "Arachnocampa luminosa glowworms, bioluminescent cave ceiling"},
    {"name": "Cueva de Villa Luz", "country": "Mexico", "state": "Tabasco",
     "lat": 17.456, "lon": -92.757, "species_count": 40,
     "notes": "Sulfur cave, toxic atmosphere, extremophile bacteria, snottites"},
    {"name": "Liang Bua Cave", "country": "Indonesia", "state": "Flores",
     "lat": -8.531, "lon": 120.441, "species_count": 25,
     "notes": "Homo floresiensis discovery site, Komodo rats, giant storks"},
    {"name": "Gomantong Caves", "country": "Malaysia", "state": "Sabah",
     "lat": 5.531, "lon": 118.076, "species_count": 45,
     "notes": "Edible bird's nest harvest, cockroach rivers, cave swiftlets"},
    {"name": "Frasassi Caves Ecosystem", "country": "Italy", "state": "Marche",
     "lat": 43.401, "lon": 12.964, "species_count": 60,
     "notes": "Sulfidic cave, chemolithoautotrophic bacteria, Niphargus amphipods"},
    {"name": "Vjetrenica Cave", "country": "Bosnia", "state": "Herzegovina",
     "lat": 42.836, "lon": 17.986, "species_count": 200,
     "notes": "Most biodiverse cave in the world, 200+ species, 100+ endemic"},
    {"name": "Pestera de la Movile", "country": "Romania", "state": "Dobrogea",
     "lat": 43.825, "lon": 28.562, "species_count": 48,
     "notes": "Isolated chemosynthetic ecosystem with unique food web"},
    {"name": "Cueva de los Tayos", "country": "Ecuador", "state": "Morona-Santiago",
     "lat": -3.083, "lon": -78.217, "species_count": 35,
     "notes": "Oilbird (guacharo) colonies, explored by Neil Armstrong in 1976"},
    {"name": "Ayyalon Cave", "country": "Israel", "state": "Ramla",
     "lat": 31.934, "lon": 34.868, "species_count": 8,
     "notes": "Sealed ecosystem, blind scorpions, new crustacean species, 2006 discovery"},
    {"name": "Bayliss Cave", "country": "Australia", "state": "Queensland",
     "lat": -17.470, "lon": 144.545, "species_count": 20,
     "notes": "High CO2 atmosphere (6%), unique invertebrate community"},
    {"name": "Gruta do Lago Azul", "country": "Brazil", "state": "Mato Grosso do Sul",
     "lat": -21.134, "lon": -56.573, "species_count": 15,
     "notes": "Blue lake cave, Pleistocene fossils, giant sloth bones"},
    {"name": "Krubera Cave Biome", "country": "Georgia", "state": "Abkhazia",
     "lat": 43.410, "lon": 40.362, "species_count": 4,
     "notes": "Plutomurus ortobalaganensis found at -2140m, deepest cave-dwelling animal"},
    {"name": "Son Doong Cave Ecosystem", "country": "Vietnam", "state": "Quang Binh",
     "lat": 17.456, "lon": 106.140, "species_count": 60,
     "notes": "Underground jungle, unique vegetation in dolines, cave pearls"},
]

KARST_LANDSCAPES = [
    {"name": "South China Karst", "country": "China", "state": "Guizhou/Yunnan/Guangxi",
     "lat": 25.015, "lon": 104.690, "karst_type": "Tower karst, fenglin, fengcong",
     "area_km2": 550000, "notes": "UNESCO, world's finest tower karst, Stone Forest (Shilin)"},
    {"name": "Dinaric Karst", "country": "Slovenia/Croatia/Bosnia", "state": "Balkans",
     "lat": 45.500, "lon": 14.500, "karst_type": "Classic karst, poljes, dolines",
     "area_km2": 60000, "notes": "Type locality of 'karst' (from Kras/Carso), Postojna and Skocjan"},
    {"name": "Yucatan Karst Platform", "country": "Mexico", "state": "Yucatan Peninsula",
     "lat": 20.500, "lon": -88.000, "karst_type": "Cenotes, underground rivers",
     "area_km2": 165000, "notes": "Flat limestone platform, 6000+ cenotes, Chicxulub fracture zone"},
    {"name": "Burren", "country": "Ireland", "state": "County Clare",
     "lat": 53.070, "lon": -9.020, "karst_type": "Limestone pavement, clints and grikes",
     "area_km2": 250, "notes": "Bare limestone landscape, Mediterranean and Arctic flora coexist"},
    {"name": "Tsingy de Bemaraha", "country": "Madagascar", "state": "Melaky",
     "lat": -18.667, "lon": 44.717, "karst_type": "Needle karst (tsingy)",
     "area_km2": 1520, "notes": "UNESCO, razor-sharp limestone pinnacles, unique lemur habitat"},
    {"name": "Guilin Tower Karst", "country": "China", "state": "Guangxi",
     "lat": 25.274, "lon": 110.290, "karst_type": "Tower karst (fenglin)",
     "area_km2": 5000, "notes": "Iconic limestone towers along Li River, depicted on 20 yuan note"},
    {"name": "Cockpit Country", "country": "Jamaica", "state": "Trelawny/St. James",
     "lat": 18.350, "lon": -77.583, "karst_type": "Cockpit karst",
     "area_km2": 1300, "notes": "Star-shaped sinkholes, 40% endemic species, Maroon refuge"},
    {"name": "Ha Long Bay", "country": "Vietnam", "state": "Quang Ninh",
     "lat": 20.910, "lon": 107.180, "karst_type": "Drowned tower karst",
     "area_km2": 1553, "notes": "UNESCO, 1,600+ limestone islands and islets in the sea"},
    {"name": "Phong Nha-Ke Bang", "country": "Vietnam", "state": "Quang Binh",
     "lat": 17.590, "lon": 106.280, "karst_type": "Tropical karst, giant caves",
     "area_km2": 857, "notes": "UNESCO, Son Doong and 300+ caves, oldest karst in Asia"},
    {"name": "Plitvice Lakes", "country": "Croatia", "state": "Lika-Senj",
     "lat": 44.880, "lon": 15.616, "karst_type": "Travertine dams, tufa lakes",
     "area_km2": 296, "notes": "UNESCO, 16 terraced lakes connected by waterfalls"},
    {"name": "Mulu Karst", "country": "Malaysia", "state": "Sarawak",
     "lat": 4.050, "lon": 114.800, "karst_type": "Tropical pinnacle karst",
     "area_km2": 528, "notes": "UNESCO, Deer Cave, Clearwater Cave, 45m stone pinnacles"},
    {"name": "Nullarbor Plain Karst", "country": "Australia", "state": "WA/SA",
     "lat": -31.000, "lon": 128.000, "karst_type": "Arid karst, blowholes, dolines",
     "area_km2": 200000, "notes": "World's largest limestone plateau, deep underwater caves"},
    {"name": "Velebit Karst", "country": "Croatia", "state": "Lika-Senj",
     "lat": 44.700, "lon": 15.000, "karst_type": "Alpine karst, deep pits",
     "area_km2": 2274, "notes": "Lukina Jama (-1431m), northern Velebit NP, UNESCO Biosphere"},
    {"name": "Kentucky Karst", "country": "USA", "state": "Kentucky",
     "lat": 37.200, "lon": -86.100, "karst_type": "Sinkhole plain",
     "area_km2": 25000, "notes": "Mammoth Cave region, classic temperate sinkhole landscape"},
    {"name": "Cantabrian Karst", "country": "Spain", "state": "Cantabria/Asturias",
     "lat": 43.200, "lon": -4.800, "karst_type": "Alpine karst, deep shafts",
     "area_km2": 5000, "notes": "Picos de Europa, deepest caves in Spain, cave art region"},
    {"name": "Apuseni Karst", "country": "Romania", "state": "Transylvania",
     "lat": 46.550, "lon": 22.700, "karst_type": "Poljes, gorges, caves",
     "area_km2": 3500, "notes": "Ice caves, Scarisoara glacier, bear caves"},
    {"name": "Nakanai Karst", "country": "Papua New Guinea", "state": "East New Britain",
     "lat": -5.500, "lon": 151.200, "karst_type": "Tropical cone karst",
     "area_km2": 2500, "notes": "Some of the world's least-explored caves, Ora cave"},
    {"name": "Chocolate Hills", "country": "Philippines", "state": "Bohol",
     "lat": 9.795, "lon": 124.167, "karst_type": "Residual cone karst",
     "area_km2": 50, "notes": "1,200+ conical hills, brown grass in dry season, UNESCO tentative"},
    {"name": "Yorkshire Dales Karst", "country": "UK", "state": "Yorkshire",
     "lat": 54.150, "lon": -2.100, "karst_type": "Limestone pavement, potholes",
     "area_km2": 2179, "notes": "Malham Cove, Gaping Gill, Ingleborough Cave system"},
    {"name": "Madre de Dios Karst", "country": "Peru", "state": "Madre de Dios",
     "lat": -12.500, "lon": -69.000, "karst_type": "Tropical karst, blind valleys",
     "area_km2": 8000, "notes": "Unexplored karst at Amazon fringe, new species discoveries"},
]


# ═══════════════════════════════════════════════════════════════
# OVERPASS QUERIES
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _search_caves_overpass(lat: float, lon: float, radius_km: float) -> list:
    """Search for caves via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["natural"="cave_entrance"](around:{radius_m},{lat},{lon});
  way["natural"="cave_entrance"](around:{radius_m},{lat},{lon});
  node["geological"="karst"](around:{radius_m},{lat},{lon});
  way["geological"="karst"](around:{radius_m},{lat},{lon});
  node["natural"="sinkhole"](around:{radius_m},{lat},{lon});
  way["natural"="sinkhole"](around:{radius_m},{lat},{lon});
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
        lat_f, lon_f = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat_f, lon_f = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
            if coords:
                lat_f = sum(c[0] for c in coords) / len(coords)
                lon_f = sum(c[1] for c in coords) / len(coords)
        if lat_f is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed cave"))
        features.append({
            "name": name,
            "lat": lat_f,
            "lon": lon_f,
            "type": tags.get("natural", tags.get("geological", "cave")),
            "description": tags.get("description", ""),
            "wikipedia": tags.get("wikipedia", ""),
            "osm_id": el.get("id"),
        })
    return features


# ═══════════════════════════════════════════════════════════════
# HELPER — BUILD FOLIUM MAP
# ═══════════════════════════════════════════════════════════════

def _build_map(data: list, lat_key: str, lon_key: str, label_key: str,
               popup_fields: dict, color: str, center: tuple = None,
               zoom: int = 3, circle_radius: int = 7) -> folium.Map:
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
            f'<div style="max-width:260px; font-size:0.85rem;">'
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
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(str(item.get(label_key, ""))),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def _build_ranked_map(data: list, lat_key: str, lon_key: str, label_key: str,
                      rank_key: str, popup_fields: dict, color: str,
                      center: tuple = None, zoom: int = 3) -> folium.Map:
    """Build map with rank-scaled markers."""
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
            f'<div style="max-width:260px; font-size:0.85rem;">'
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
            popup=folium.Popup(popup_html, max_width=280),
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
# HELPER — CHART (horizontal bar)
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
    ax.set_yticklabels([str(l)[:30] for l in labels], color="#e8ecf4", fontsize=9)
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
# HELPER — DOWNLOAD
# ═══════════════════════════════════════════════════════════════

def _download_section(df: pd.DataFrame, filename: str, label: str, key: str):
    """Expander with dataframe and CSV download."""
    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
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

def _render_longest_caves():
    """Mode 1: World's Longest Caves."""
    data = sorted(LONGEST_CAVES, key=lambda x: x["length_km"], reverse=True)

    _show_stats([
        ("Caves Listed", len(data)),
        ("Longest", f"{data[0]['length_km']} km"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Total Surveyed", f"{sum(d['length_km'] for d in data):,.0f} km"),
    ])

    st.markdown("---")
    st.markdown("#### Longest Caves World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "length_km",
        popup_fields={"Length": "length_km", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#06b6d4", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["length_km"] for d in top],
        "#06b6d4", "Total Length (km)", "World's Longest Caves",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "length_km", "lat", "lon", "notes"]]
    df = df.sort_values("length_km", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "longest_caves.csv",
                      f"Download {len(df)} Longest Caves (CSV)", "dl_longest")


def _render_deepest_caves():
    """Mode 2: Deepest Caves."""
    data = sorted(DEEPEST_CAVES, key=lambda x: x["depth_m"], reverse=True)

    _show_stats([
        ("Caves Listed", len(data)),
        ("Deepest", f"{data[0]['depth_m']} m"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Avg Depth", f"{sum(d['depth_m'] for d in data) // len(data)} m"),
    ])

    st.markdown("---")
    st.markdown("#### Deepest Caves World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "depth_m",
        popup_fields={"Depth": "depth_m", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#ef4444", zoom=3,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["depth_m"] for d in top],
        "#ef4444", "Depth (meters)", "World's Deepest Caves",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "depth_m", "lat", "lon", "notes"]]
    df = df.sort_values("depth_m", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "deepest_caves.csv",
                      f"Download {len(df)} Deepest Caves (CSV)", "dl_deepest")


def _render_show_caves():
    """Mode 3: Show Caves & Tourist."""
    data = sorted(SHOW_CAVES, key=lambda x: x["visitors_yr"], reverse=True)

    total_visitors = sum(d["visitors_yr"] for d in data)
    _show_stats([
        ("Show Caves", len(data)),
        ("Most Visited", data[0]["name"]),
        ("Countries", len(set(d["country"] for d in data))),
        ("Total Visitors/yr", f"{total_visitors / 1e6:.1f}M"),
    ])

    st.markdown("---")
    st.markdown("#### Tourist Caves World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "visitors_yr",
        popup_fields={"Visitors/Year": "visitors_yr", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#f59e0b", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["visitors_yr"] / 1000 for d in top],
        "#f59e0b", "Annual Visitors (thousands)", "Most Visited Show Caves",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "visitors_yr", "lat", "lon", "notes"]]
    df = df.sort_values("visitors_yr", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "show_caves.csv",
                      f"Download {len(df)} Show Caves (CSV)", "dl_showcaves")


def _render_cave_art():
    """Mode 4: Cave Paintings & Art."""
    data = sorted(CAVE_ART_SITES, key=lambda x: x["age_years"], reverse=True)

    _show_stats([
        ("Art Sites", len(data)),
        ("Oldest", f"{data[0]['age_years']:,} years"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Avg Age", f"{sum(d['age_years'] for d in data) // len(data):,} yrs"),
    ])

    st.markdown("---")
    st.markdown("#### Cave Art Sites World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "age_years",
        popup_fields={"Age": "age_years", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#ec4899", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["age_years"] / 1000 for d in top],
        "#ec4899", "Age (thousands of years)", "Oldest Cave Art Sites",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "age_years", "lat", "lon", "notes"]]
    df = df.sort_values("age_years", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "cave_art.csv",
                      f"Download {len(df)} Cave Art Sites (CSV)", "dl_art")


def _render_cenotes():
    """Mode 5: Cenotes & Sinkholes."""
    data = sorted(CENOTES_SINKHOLES, key=lambda x: x["depth_m"], reverse=True)

    _show_stats([
        ("Sites", len(data)),
        ("Deepest", f"{data[0]['depth_m']} m"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Largest Dia.", f"{max(d['diameter_m'] for d in data):,} m"),
    ])

    st.markdown("---")
    st.markdown("#### Cenotes & Sinkholes World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "depth_m",
        popup_fields={"Depth": "depth_m", "Diameter": "diameter_m",
                       "Country": "country", "Notes": "notes"},
        color="#3b82f6", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = sorted(data, key=lambda x: x["depth_m"], reverse=True)[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["depth_m"] for d in top],
        "#3b82f6", "Depth (meters)", "Deepest Cenotes & Sinkholes",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "depth_m", "diameter_m", "lat", "lon", "notes"]]
    df = df.sort_values("depth_m", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "cenotes_sinkholes.csv",
                      f"Download {len(df)} Cenotes & Sinkholes (CSV)", "dl_cenotes")


def _render_lava_tubes():
    """Mode 6: Lava Tubes."""
    data = sorted(LAVA_TUBES, key=lambda x: x["length_km"], reverse=True)

    _show_stats([
        ("Lava Tubes", len(data)),
        ("Longest", f"{data[0]['length_km']} km"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Total Length", f"{sum(d['length_km'] for d in data):,.1f} km"),
    ])

    st.markdown("---")
    st.markdown("#### Lava Tubes World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "length_km",
        popup_fields={"Length": "length_km", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#f97316", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["length_km"] for d in top],
        "#f97316", "Length (km)", "Longest Lava Tubes",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "length_km", "lat", "lon", "notes"]]
    df = df.sort_values("length_km", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "lava_tubes.csv",
                      f"Download {len(df)} Lava Tubes (CSV)", "dl_lava")


def _render_underground_rivers():
    """Mode 7: Underground Rivers."""
    data = sorted(UNDERGROUND_RIVERS, key=lambda x: x["length_km"], reverse=True)

    _show_stats([
        ("Rivers Listed", len(data)),
        ("Longest", f"{data[0]['length_km']} km"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Total Length", f"{sum(d['length_km'] for d in data):,.0f} km"),
    ])

    st.markdown("---")
    st.markdown("#### Underground Rivers World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "length_km",
        popup_fields={"Length": "length_km", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#14b8a6", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["length_km"] for d in top],
        "#14b8a6", "Length (km)", "Longest Underground Rivers",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "length_km", "lat", "lon", "notes"]]
    df = df.sort_values("length_km", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "underground_rivers.csv",
                      f"Download {len(df)} Underground Rivers (CSV)", "dl_rivers")


def _render_crystal_caves():
    """Mode 8: Crystal Caves."""
    data = CRYSTAL_CAVES

    crystal_types = set()
    for d in data:
        for t in d["crystal_type"].split(","):
            crystal_types.add(t.strip())

    _show_stats([
        ("Crystal Caves", len(data)),
        ("Countries", len(set(d["country"] for d in data))),
        ("Crystal Types", len(crystal_types)),
    ])

    st.markdown("---")
    st.markdown("#### Crystal & Mineral Caves World Map")

    m = _build_map(
        data, "lat", "lon", "name",
        popup_fields={"Crystal Type": "crystal_type", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#a855f7", zoom=2, circle_radius=8,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Crystal Types Distribution")

    type_counts = {}
    for d in data:
        for t in d["crystal_type"].split(","):
            t = t.strip()
            type_counts[t] = type_counts.get(t, 0) + 1
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    _bar_chart(
        [t[0] for t in sorted_types],
        [t[1] for t in sorted_types],
        "#a855f7", "Number of Caves", "Crystal Types Found",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "crystal_type", "lat", "lon", "notes"]]
    _download_section(df, "crystal_caves.csv",
                      f"Download {len(df)} Crystal Caves (CSV)", "dl_crystal")


def _render_cave_biodiversity():
    """Mode 9: Cave Biodiversity."""
    data = sorted(CAVE_BIODIVERSITY, key=lambda x: x["species_count"], reverse=True)

    _show_stats([
        ("Cave Ecosystems", len(data)),
        ("Most Biodiverse", data[0]["name"]),
        ("Top Species Count", data[0]["species_count"]),
        ("Countries", len(set(d["country"] for d in data))),
    ])

    st.markdown("---")
    st.markdown("#### Cave Biodiversity Hotspots Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "species_count",
        popup_fields={"Species": "species_count", "Country": "country",
                       "State/Region": "state", "Notes": "notes"},
        color="#10b981", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top],
        [d["species_count"] for d in top],
        "#10b981", "Number of Species", "Most Biodiverse Cave Ecosystems",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "species_count", "lat", "lon", "notes"]]
    df = df.sort_values("species_count", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "cave_biodiversity.csv",
                      f"Download {len(df)} Cave Ecosystems (CSV)", "dl_bio")


def _render_karst_landscapes():
    """Mode 10: Karst Landscapes."""
    data = sorted(KARST_LANDSCAPES, key=lambda x: x["area_km2"], reverse=True)

    total_area = sum(d["area_km2"] for d in data)
    _show_stats([
        ("Karst Regions", len(data)),
        ("Largest", f"{data[0]['area_km2']:,} km2"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Total Area", f"{total_area:,} km2"),
    ])

    st.markdown("---")
    st.markdown("#### Major Karst Landscapes World Map")

    m = _build_ranked_map(
        data, "lat", "lon", "name", "area_km2",
        popup_fields={"Type": "karst_type", "Area": "area_km2",
                       "Country": "country", "Notes": "notes"},
        color="#8b5cf6", zoom=2,
    )
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Karst Type Distribution")
    type_counts = {}
    for d in data:
        for t in d["karst_type"].split(","):
            t = t.strip()
            type_counts[t] = type_counts.get(t, 0) + 1
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:12]
    _bar_chart(
        [t[0] for t in sorted_types],
        [t[1] for t in sorted_types],
        "#8b5cf6", "Number of Regions", "Karst Landscape Types",
    )

    df = pd.DataFrame(data)[["name", "country", "state", "karst_type", "area_km2", "lat", "lon", "notes"]]
    df = df.sort_values("area_km2", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "karst_landscapes.csv",
                      f"Download {len(df)} Karst Landscapes (CSV)", "dl_karst")


# ═══════════════════════════════════════════════════════════════
# OVERPASS LIVE SEARCH SECTION
# ═══════════════════════════════════════════════════════════════

def _render_overpass_search():
    """Live Overpass API cave search panel (shown below every mode)."""
    st.markdown("---")
    st.markdown("#### Live Cave Search (OpenStreetMap)")
    st.caption(
        "Search for cave entrances, sinkholes, and karst features mapped in OSM "
        "near any location. This uses the Overpass API in real time."
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        osm_lat = st.number_input("Latitude", value=45.78, format="%.4f",
                                  min_value=-90.0, max_value=90.0, key="cave_osm_lat")
    with c2:
        osm_lon = st.number_input("Longitude", value=14.20, format="%.4f",
                                  min_value=-180.0, max_value=180.0, key="cave_osm_lon")
    with c3:
        osm_radius = st.slider("Radius (km)", 1, 100, 20, key="cave_osm_radius")

    presets = {
        "Custom": None,
        "Postojna & Skocjan, Slovenia": (45.78, 14.20),
        "Mammoth Cave, Kentucky": (37.19, -86.10),
        "Yucatan Cenotes, Mexico": (20.50, -87.40),
        "Guilin Karst, China": (25.27, 110.29),
        "Dinaric Karst, Croatia": (44.88, 15.62),
        "Yorkshire Dales, UK": (54.15, -2.10),
        "Phong Nha, Vietnam": (17.59, 106.28),
        "Carlsbad, New Mexico": (32.15, -104.56),
    }
    preset = st.selectbox("Quick Locations", list(presets.keys()), key="cave_osm_preset")
    if preset != "Custom" and presets[preset]:
        osm_lat, osm_lon = presets[preset]

    if st.button("Search Caves in OSM", key="cave_osm_search", use_container_width=True):
        with st.spinner("Querying OpenStreetMap via Overpass API..."):
            features = _search_caves_overpass(osm_lat, osm_lon, osm_radius)

        if not features:
            st.warning("No cave features found in this area. Try a larger radius or different location.")
            return

        st.success(f"Found {len(features)} cave/karst features in OSM.")

        osm_map = folium.Map(location=[osm_lat, osm_lon], zoom_start=10, tiles=None)
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="CartoDB Dark", name="Dark Base",
        ).add_to(osm_map)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Satellite", overlay=False,
        ).add_to(osm_map)

        folium.Circle(
            location=[osm_lat, osm_lon],
            radius=osm_radius * 1000,
            color="#06b6d4", fill=True, fill_opacity=0.03, weight=1,
        ).add_to(osm_map)

        type_colors = {
            "cave_entrance": "#06b6d4",
            "sinkhole": "#3b82f6",
            "karst": "#8b5cf6",
            "cave": "#14b8a6",
        }

        for f in features:
            color = type_colors.get(f["type"], "#8b97b0")
            popup_html = (
                f'<div style="max-width:220px; font-size:0.85rem;">'
                f'<strong>{escape(f["name"])}</strong><br/>'
                f'<b>Type:</b> {escape(f["type"])}<br/>'
            )
            if f["description"]:
                popup_html += f'<span style="font-size:0.75rem;">{escape(f["description"][:150])}</span><br/>'
            if f["wikipedia"]:
                lang_title = f["wikipedia"].split(":", 1)
                if len(lang_title) == 2:
                    lang, title = lang_title
                else:
                    lang, title = "en", f["wikipedia"]
                popup_html += (
                    f'<a href="https://{escape(lang)}.wikipedia.org/wiki/{escape(title)}" '
                    f'target="_blank" style="font-size:0.75rem;">Wikipedia</a>'
                )
            popup_html += "</div>"

            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=6, color=color, fill=True, fill_color=color,
                fill_opacity=0.7, weight=2,
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=escape(f["name"]),
            ).add_to(osm_map)

        folium.LayerControl().add_to(osm_map)
        components.html(osm_map._repr_html_(), height=500)

        # Legend
        legend_html = " ".join(
            f'<span style="color:{c}; font-size:0.8rem;">&#9679; {t.replace("_"," ").title()}</span>'
            for t, c in type_colors.items()
        )
        st.markdown(
            f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:0.25rem;">{legend_html}</div>',
            unsafe_allow_html=True,
        )

        rows = []
        for f in features:
            rows.append({
                "name": f["name"],
                "type": f["type"],
                "latitude": f["lat"],
                "longitude": f["lon"],
                "description": f["description"],
                "wikipedia": f["wikipedia"],
                "osm_id": f["osm_id"],
            })
        df = pd.DataFrame(rows)
        _download_section(df, "osm_caves.csv",
                          f"Download {len(df)} OSM Cave Features (CSV)", "dl_osm_caves")


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_cave_maps_tab():
    """Main render function for the Caves, Karst & Underground World tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001F573\uFE0F Caves, Karst & Underground World</h4>'
        '<p>Cave systems, cenotes, underground rivers, lava tubes & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    st.markdown("#### Explore Underground")
    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        key="cave_mode",
        help="Choose a category of underground features to explore.",
    )

    # ── Mode description ──
    color = MODE_COLORS.get(mode, "#06b6d4")
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

    # ── Dispatch to mode renderer ──
    mode_map = {
        "World's Longest Caves": _render_longest_caves,
        "Deepest Caves": _render_deepest_caves,
        "Show Caves & Tourist": _render_show_caves,
        "Cave Paintings & Art": _render_cave_art,
        "Cenotes & Sinkholes": _render_cenotes,
        "Lava Tubes": _render_lava_tubes,
        "Underground Rivers": _render_underground_rivers,
        "Crystal Caves": _render_crystal_caves,
        "Cave Biodiversity": _render_cave_biodiversity,
        "Karst Landscapes": _render_karst_landscapes,
    }

    renderer = mode_map.get(mode)
    if renderer:
        renderer()

    # ── Overpass live search (always shown) ──
    _render_overpass_search()
