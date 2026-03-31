"""
Deep Volcanology Explorer module for TerraScout AI.
Provides 10 curated map modes covering active volcanoes, supervolcanoes,
volcanic island chains, famous eruptions, lava tubes, hot springs,
Ring of Fire, submarine volcanoes, volcanic wine regions, and observatories.
All data is preset with rich lat/lon/name/description entries.
"""

import io
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

# =====================================================================
# PRESET DATA FOR ALL 10 MAP MODES
# =====================================================================

ACTIVE_VOLCANOES = [
    {"name": "Kilauea", "lat": 19.4069, "lon": -155.2834, "country": "USA (Hawaii)", "elevation_m": 1247, "last_eruption": "2023 (ongoing)", "type": "Shield", "desc": "One of the most active volcanoes on Earth; continuous eruptions since 1983."},
    {"name": "Mount Etna", "lat": 37.7510, "lon": 14.9934, "country": "Italy", "elevation_m": 3357, "last_eruption": "2024", "type": "Stratovolcano", "desc": "Europe's tallest and most active volcano, on the east coast of Sicily."},
    {"name": "Stromboli", "lat": 38.7891, "lon": 15.2133, "country": "Italy", "elevation_m": 924, "last_eruption": "2024 (continuous)", "type": "Stratovolcano", "desc": "The Lighthouse of the Mediterranean; near-continuous eruptions for over 2,000 years."},
    {"name": "Sakurajima", "lat": 31.5853, "lon": 130.6567, "country": "Japan", "elevation_m": 1117, "last_eruption": "2024 (ongoing)", "type": "Stratovolcano", "desc": "One of Japan's most active volcanoes, erupting almost constantly since 1955."},
    {"name": "Mount Merapi", "lat": -7.5407, "lon": 110.4457, "country": "Indonesia", "elevation_m": 2930, "last_eruption": "2023", "type": "Stratovolcano", "desc": "Indonesia's most active volcano; deadly eruptions occur regularly."},
    {"name": "Popocatepetl", "lat": 19.0224, "lon": -98.6277, "country": "Mexico", "elevation_m": 5426, "last_eruption": "2024 (ongoing)", "type": "Stratovolcano", "desc": "Smoking Mountain; the second-highest peak in Mexico, highly active."},
    {"name": "Fuego", "lat": 14.4747, "lon": -90.8806, "country": "Guatemala", "elevation_m": 3763, "last_eruption": "2024 (ongoing)", "type": "Stratovolcano", "desc": "One of Central America's most active volcanoes with frequent Vulcanian eruptions."},
    {"name": "Semeru", "lat": -8.1077, "lon": 112.9224, "country": "Indonesia", "elevation_m": 3676, "last_eruption": "2024 (ongoing)", "type": "Stratovolcano", "desc": "Java's highest volcano; almost continuous eruption since 1967."},
    {"name": "Nyiragongo", "lat": -1.5200, "lon": 29.2500, "country": "DR Congo", "elevation_m": 3470, "last_eruption": "2021", "type": "Stratovolcano", "desc": "Home to world's largest persistent lava lake; threatens city of Goma."},
    {"name": "Mauna Loa", "lat": 19.4753, "lon": -155.6082, "country": "USA (Hawaii)", "elevation_m": 4169, "last_eruption": "2022", "type": "Shield", "desc": "The world's largest active volcano by volume, on the Big Island of Hawaii."},
    {"name": "Piton de la Fournaise", "lat": -21.2442, "lon": 55.7083, "country": "Reunion (France)", "elevation_m": 2632, "last_eruption": "2024", "type": "Shield", "desc": "One of the world's most active volcanoes, on Reunion Island in the Indian Ocean."},
    {"name": "Erebus", "lat": -77.5300, "lon": 167.1530, "country": "Antarctica", "elevation_m": 3794, "last_eruption": "2023 (ongoing)", "type": "Stratovolcano", "desc": "The southernmost active volcano on Earth with a persistent lava lake."},
    {"name": "Erta Ale", "lat": 13.6000, "lon": 40.6700, "country": "Ethiopia", "elevation_m": 613, "last_eruption": "2023", "type": "Shield", "desc": "Smoking Mountain in Afar; one of only a few volcanoes with a persistent lava lake."},
    {"name": "Yasur", "lat": -19.5320, "lon": 169.4470, "country": "Vanuatu", "elevation_m": 361, "last_eruption": "2024 (ongoing)", "type": "Stratovolcano", "desc": "Possibly the most accessible active volcano; continuous activity for 800+ years."},
    {"name": "Villarrica", "lat": -39.4200, "lon": -71.9397, "country": "Chile", "elevation_m": 2847, "last_eruption": "2024", "type": "Stratovolcano", "desc": "One of Chile's most active volcanoes with a rare persistent lava lake."},
    {"name": "Sinabung", "lat": 3.1700, "lon": 98.3920, "country": "Indonesia", "elevation_m": 2460, "last_eruption": "2024", "type": "Stratovolcano", "desc": "Dormant for 400 years before reawakening in 2010; now highly active."},
    {"name": "Fagradalsfjall", "lat": 63.9000, "lon": -22.2660, "country": "Iceland", "elevation_m": 385, "last_eruption": "2024", "type": "Tuya/Fissure", "desc": "Reykjanes Peninsula fissure eruptions; first eruption in 800 years in 2021."},
    {"name": "Taal", "lat": 14.0113, "lon": 120.9980, "country": "Philippines", "elevation_m": 311, "last_eruption": "2022", "type": "Caldera", "desc": "A volcano within a lake within a volcano; one of the world's most dangerous."},
    {"name": "Whakaari / White Island", "lat": -37.5210, "lon": 177.1830, "country": "New Zealand", "elevation_m": 321, "last_eruption": "2019", "type": "Stratovolcano", "desc": "New Zealand's most active cone volcano, located offshore in the Bay of Plenty."},
    {"name": "Shishaldin", "lat": 54.7554, "lon": -163.9711, "country": "USA (Alaska)", "elevation_m": 2857, "last_eruption": "2024", "type": "Stratovolcano", "desc": "One of the most active volcanoes in Alaska's Aleutian arc."},
]

SUPERVOLCANOES = [
    {"name": "Yellowstone Caldera", "lat": 44.4280, "lon": -110.5885, "country": "USA", "caldera_km": 72, "last_eruption": "640,000 years ago", "vei": 8, "desc": "The world's most famous supervolcano; sits atop a massive magma chamber beneath Yellowstone National Park."},
    {"name": "Toba Caldera", "lat": 2.6167, "lon": 98.8333, "country": "Indonesia", "caldera_km": 100, "last_eruption": "74,000 years ago", "vei": 8, "desc": "Site of the largest known eruption in the last 2 million years; created Lake Toba in Sumatra."},
    {"name": "Campi Flegrei", "lat": 40.8270, "lon": 14.1390, "country": "Italy", "caldera_km": 13, "last_eruption": "1538 (Monte Nuovo)", "vei": 7, "desc": "Supervolcanic caldera west of Naples; currently showing signs of unrest (bradyseism)."},
    {"name": "Long Valley Caldera", "lat": 37.7000, "lon": -118.8700, "country": "USA", "caldera_km": 32, "last_eruption": "760,000 years ago", "vei": 7, "desc": "Large caldera in eastern California; the Bishop Tuff eruption was catastrophic."},
    {"name": "Taupo Caldera", "lat": -38.8200, "lon": 176.0000, "country": "New Zealand", "caldera_km": 35, "last_eruption": "232 CE (Hatepe)", "vei": 7, "desc": "Lake Taupo fills this caldera; the 232 CE Hatepe eruption was one of the most violent in 5,000 years."},
    {"name": "Aira Caldera", "lat": 31.5930, "lon": 130.6570, "country": "Japan", "caldera_km": 20, "last_eruption": "22,000 years ago (caldera-forming)", "vei": 7, "desc": "Kagoshima Bay fills the caldera; Sakurajima volcano sits on its southern rim."},
    {"name": "Valles Caldera", "lat": 35.8700, "lon": -106.5700, "country": "USA", "caldera_km": 22, "last_eruption": "1.25 million years ago", "vei": 7, "desc": "Well-preserved caldera in the Jemez Mountains of New Mexico; now a national preserve."},
    {"name": "La Garita Caldera", "lat": 37.9000, "lon": -106.9300, "country": "USA", "caldera_km": 75, "last_eruption": "27.8 million years ago", "vei": 9, "desc": "Produced the Fish Canyon Tuff, one of the largest known explosive eruptions in Earth history."},
    {"name": "Cerro Galan", "lat": -25.9800, "lon": -66.9300, "country": "Argentina", "caldera_km": 38, "last_eruption": "2.2 million years ago", "vei": 7, "desc": "One of the best-exposed large calderas on Earth, in the Puna of the Andes."},
    {"name": "Whakamaru Caldera", "lat": -38.4500, "lon": 176.0000, "country": "New Zealand", "caldera_km": 30, "last_eruption": "340,000 years ago", "vei": 8, "desc": "Part of the Taupo Volcanic Zone; produced massive ignimbrite sheets covering central North Island."},
    {"name": "Kikai Caldera", "lat": 30.7900, "lon": 130.3100, "country": "Japan", "caldera_km": 19, "last_eruption": "7,300 years ago", "vei": 7, "desc": "Submarine caldera south of Kyushu; its eruption devastated prehistoric Jomon culture."},
    {"name": "Bennett Lake Caldera", "lat": 60.1000, "lon": -134.8000, "country": "Canada", "caldera_km": 50, "last_eruption": "Paleogene", "vei": 7, "desc": "Ancient supervolcano caldera in Yukon Territory; heavily eroded but still recognizable."},
]

VOLCANIC_ISLAND_CHAINS = [
    {"name": "Big Island, Hawaii", "lat": 19.5429, "lon": -155.6659, "chain": "Hawaii", "desc": "The youngest and largest Hawaiian island; home to Kilauea and Mauna Loa active volcanoes."},
    {"name": "Maui, Hawaii", "lat": 20.7984, "lon": -156.3319, "chain": "Hawaii", "desc": "The Valley Isle; Haleakala last erupted around 1600 CE."},
    {"name": "Oahu, Hawaii", "lat": 21.4389, "lon": -158.0001, "chain": "Hawaii", "desc": "Formed by two shield volcanoes: Waianae and Koolau; heavily eroded."},
    {"name": "Tenerife, Canary Islands", "lat": 28.2916, "lon": -16.6291, "chain": "Canary Islands", "desc": "Home to Mount Teide (3,718 m), the highest peak in Spain and an active volcano."},
    {"name": "Lanzarote, Canary Islands", "lat": 29.0469, "lon": -13.5899, "chain": "Canary Islands", "desc": "Timanfaya National Park showcases dramatic volcanic landscapes from 1730-36 eruptions."},
    {"name": "La Palma, Canary Islands", "lat": 28.6835, "lon": -17.7642, "chain": "Canary Islands", "desc": "Site of the 2021 Cumbre Vieja eruption that lasted 85 days."},
    {"name": "Sao Miguel, Azores", "lat": 37.7833, "lon": -25.5000, "chain": "Azores", "desc": "Largest Azorean island with calderas, hot springs, and Sete Cidades twin lakes."},
    {"name": "Faial, Azores", "lat": 38.5167, "lon": -28.7167, "chain": "Azores", "desc": "Capelinhos volcano erupted from the sea in 1957-58, extending the island."},
    {"name": "Isabela Island, Galapagos", "lat": -0.8300, "lon": -91.1350, "chain": "Galapagos", "desc": "Largest Galapagos island with six shield volcanoes including active Sierra Negra."},
    {"name": "Fernandina Island, Galapagos", "lat": -0.3700, "lon": -91.5500, "chain": "Galapagos", "desc": "Most volcanically active Galapagos island; La Cumbre erupted in 2024."},
    {"name": "Heimaey, Vestmannaeyjar, Iceland", "lat": 63.4280, "lon": -20.2674, "chain": "Iceland", "desc": "Famous for the 1973 Eldfell eruption that nearly buried the town."},
    {"name": "Surtsey, Iceland", "lat": 63.3030, "lon": -20.6050, "chain": "Iceland", "desc": "A volcanic island that emerged from the ocean in 1963; UNESCO World Heritage Site."},
    {"name": "Reunion Island", "lat": -21.1151, "lon": 55.5364, "chain": "Mascarene Islands", "desc": "Home to Piton de la Fournaise, one of the world's most active volcanoes."},
    {"name": "Santorini, Greece", "lat": 36.3932, "lon": 25.4615, "chain": "Cyclades Arc", "desc": "Iconic caldera island formed by the catastrophic Minoan eruption circa 1600 BCE."},
    {"name": "Jeju Island, South Korea", "lat": 33.3617, "lon": 126.5292, "chain": "Jeju", "desc": "Shield volcano island with over 360 parasitic cones and Hallasan peak (1,950 m)."},
]

FAMOUS_ERUPTIONS = [
    {"name": "Vesuvius (79 CE)", "lat": 40.8210, "lon": 14.4260, "year": 79, "vei": 5, "deaths": "~16,000", "desc": "Buried Pompeii and Herculaneum under volcanic ash; the most famous eruption in history."},
    {"name": "Krakatoa (1883)", "lat": -6.1021, "lon": 105.4230, "year": 1883, "vei": 6, "deaths": "~36,000", "desc": "One of the loudest sounds in recorded history; caused tsunamis and global cooling."},
    {"name": "Mount St. Helens (1980)", "lat": 46.1914, "lon": -122.1956, "year": 1980, "vei": 5, "deaths": "57", "desc": "Catastrophic lateral blast removed the entire north face; devastated 600 km2 of forest."},
    {"name": "Pinatubo (1991)", "lat": 15.1429, "lon": 120.3496, "year": 1991, "vei": 6, "deaths": "~800", "desc": "Second-largest eruption of the 20th century; caused global temperatures to drop by 0.5C."},
    {"name": "Tambora (1815)", "lat": -8.2500, "lon": 118.0000, "year": 1815, "vei": 7, "deaths": "~71,000", "desc": "The most powerful eruption in recorded history; caused the Year Without a Summer in 1816."},
    {"name": "Thera/Santorini (~1600 BCE)", "lat": 36.4040, "lon": 25.3960, "year": -1600, "vei": 7, "deaths": "Unknown (destroyed Minoan civilization)", "desc": "Massive caldera-forming eruption that may have inspired the Atlantis legend."},
    {"name": "Mount Pelee (1902)", "lat": 14.8094, "lon": -61.1659, "year": 1902, "vei": 4, "deaths": "~29,000", "desc": "Pyroclastic flows destroyed Saint-Pierre, Martinique in minutes; only 2 survivors."},
    {"name": "Nevado del Ruiz (1985)", "lat": 4.8950, "lon": -75.3220, "year": 1985, "vei": 3, "deaths": "~23,000", "desc": "Small eruption triggered lahars that buried the town of Armero, Colombia."},
    {"name": "Unzen (1792)", "lat": 32.7570, "lon": 130.2930, "year": 1792, "vei": 2, "deaths": "~15,000", "desc": "Dome collapse caused a mega-tsunami in Ariake Bay; Japan's worst volcanic disaster."},
    {"name": "Laki (1783-84)", "lat": 64.0800, "lon": -18.2300, "year": 1783, "vei": 6, "deaths": "~10,000", "desc": "Eight-month fissure eruption in Iceland caused a toxic haze across Europe and famine."},
    {"name": "Novarupta/Katmai (1912)", "lat": 58.2700, "lon": -155.1570, "year": 1912, "vei": 6, "deaths": "0 (remote)", "desc": "Largest eruption of the 20th century; created the Valley of Ten Thousand Smokes in Alaska."},
    {"name": "El Chichon (1982)", "lat": 17.3600, "lon": -93.2280, "year": 1982, "vei": 5, "deaths": "~2,000", "desc": "Destroyed the volcano's summit dome and several villages in Chiapas, Mexico."},
    {"name": "Kelud (2014)", "lat": -7.9300, "lon": 112.3080, "year": 2014, "vei": 4, "deaths": "7", "desc": "Powerful eruption sent ash 17 km high; one of Java's most dangerous volcanoes."},
    {"name": "Eyjafjallajokull (2010)", "lat": 63.6300, "lon": -19.6200, "year": 2010, "vei": 4, "deaths": "0", "desc": "Disrupted European air travel for weeks; ash cloud stranded millions of passengers."},
    {"name": "Mount Agung (2017-2019)", "lat": -8.3420, "lon": 115.5080, "year": 2017, "vei": 3, "deaths": "0", "desc": "Major eruption threat evacuated 140,000 people from Bali; moderate eruptions followed."},
]

LAVA_TUBES = [
    {"name": "Kazumura Cave", "lat": 19.5100, "lon": -155.2100, "country": "USA (Hawaii)", "length_m": 65600, "desc": "The world's longest and deepest lava tube at 65.6 km; formed by Kilauea flows."},
    {"name": "Thurston Lava Tube (Nahuku)", "lat": 19.4137, "lon": -155.2387, "country": "USA (Hawaii)", "length_m": 600, "desc": "Famous walk-through lava tube in Hawaii Volcanoes National Park."},
    {"name": "Cueva del Viento", "lat": 28.3500, "lon": -16.5400, "country": "Spain (Tenerife)", "length_m": 18000, "desc": "Largest lava tube in Europe and one of the longest in the world; in Icod de los Vinos."},
    {"name": "Manjanggul Cave", "lat": 33.5280, "lon": 126.7710, "country": "South Korea (Jeju)", "length_m": 7400, "desc": "UNESCO World Heritage lava tube with spectacular formations on Jeju Island."},
    {"name": "Grotta del Gelo", "lat": 37.8000, "lon": 14.9800, "country": "Italy (Sicily)", "length_m": 125, "desc": "Ice cave inside a lava tube on Mount Etna; southernmost glacier in Europe."},
    {"name": "Undara Lava Tubes", "lat": -18.2880, "lon": 144.6060, "country": "Australia", "length_m": 160000, "desc": "190,000-year-old lava tube system in Queensland; one of Earth's longest flow systems."},
    {"name": "Raufarholshellir", "lat": 63.9440, "lon": -21.3870, "country": "Iceland", "length_m": 1360, "desc": "One of Iceland's longest lava tubes, formed 5,200 years ago; now a popular tour site."},
    {"name": "Lava Beds National Monument", "lat": 41.7500, "lon": -121.5070, "country": "USA (California)", "length_m": 0, "desc": "Over 700 caves from Medicine Lake volcano; largest concentration of lava tubes in North America."},
    {"name": "Grjotagja Cave", "lat": 65.6262, "lon": -16.8832, "country": "Iceland", "length_m": 50, "desc": "Lava cave with geothermal hot spring near Lake Myvatn; famous from Game of Thrones."},
    {"name": "Cueva de los Verdes", "lat": 29.1590, "lon": -13.4350, "country": "Spain (Lanzarote)", "length_m": 6000, "desc": "Spectacular lava tube on Lanzarote extending 1.5 km underwater; concert hall inside."},
    {"name": "Surtshellir", "lat": 64.7900, "lon": -20.5100, "country": "Iceland", "length_m": 1970, "desc": "One of Iceland's longest lava caves; used by Vikings as a shelter in the 10th century."},
    {"name": "Deer Cave", "lat": 4.0300, "lon": 114.8200, "country": "Malaysia (Borneo)", "length_m": 2160, "desc": "Enormous cave passage in Gunung Mulu; one of the world's largest cave openings."},
]

VOLCANIC_HOT_SPRINGS = [
    {"name": "Grand Prismatic Spring", "lat": 44.5251, "lon": -110.8382, "country": "USA (Yellowstone)", "temp_c": 87, "desc": "Largest hot spring in the USA and third-largest in the world; vivid rainbow colors from thermophiles."},
    {"name": "Old Faithful Geyser", "lat": 44.4605, "lon": -110.8281, "country": "USA (Yellowstone)", "temp_c": 95, "desc": "The world's most famous geyser; erupts approximately every 90 minutes."},
    {"name": "Blue Lagoon", "lat": 63.8804, "lon": -22.4495, "country": "Iceland", "temp_c": 39, "desc": "Geothermal spa in a lava field on the Reykjanes Peninsula; milky-blue silica-rich water."},
    {"name": "Geysir (Great Geysir)", "lat": 64.3103, "lon": -20.3024, "country": "Iceland", "temp_c": 100, "desc": "The original geyser that gave its name to all geysers worldwide; largely dormant now."},
    {"name": "Strokkur Geyser", "lat": 64.3104, "lon": -20.3015, "country": "Iceland", "temp_c": 100, "desc": "Iceland's most reliable geyser; erupts every 6-10 minutes up to 30 meters."},
    {"name": "Wai-O-Tapu", "lat": -38.3480, "lon": 176.3690, "country": "New Zealand", "temp_c": 100, "desc": "Champagne Pool, Devil's Bath, and Lady Knox Geyser; vivid geothermal wonderland near Rotorua."},
    {"name": "Beppu Onsen", "lat": 33.2846, "lon": 131.4914, "country": "Japan", "temp_c": 98, "desc": "City of steam with more hot spring sources than anywhere else in Japan; the Hells of Beppu."},
    {"name": "Dallol Hydrothermal Field", "lat": 14.2422, "lon": 40.2967, "country": "Ethiopia", "temp_c": 108, "desc": "Hottest inhabited place on Earth; surreal acid pools and salt formations in the Danakil Depression."},
    {"name": "Pamukkale", "lat": 37.9205, "lon": 29.1196, "country": "Turkey", "temp_c": 36, "desc": "Cotton Castle travertine terraces formed by calcium-rich thermal waters; UNESCO site."},
    {"name": "El Tatio Geysers", "lat": -22.3320, "lon": -68.0130, "country": "Chile", "temp_c": 86, "desc": "Highest geyser field in the world at 4,320 m elevation in the Atacama Desert."},
    {"name": "Solfatara di Pozzuoli", "lat": 40.8272, "lon": 14.1389, "country": "Italy", "temp_c": 160, "desc": "Volcanic crater in Campi Flegrei with fumaroles, mud pots, and sulfurous emissions."},
    {"name": "Deildartunguhver", "lat": 64.6640, "lon": -21.4100, "country": "Iceland", "temp_c": 100, "desc": "Highest-flow hot spring in Europe at 180 liters per second; used for district heating."},
    {"name": "Jigokudani Monkey Park", "lat": 36.7330, "lon": 138.4630, "country": "Japan", "temp_c": 63, "desc": "Famous for Japanese macaques bathing in natural volcanic hot springs in winter."},
    {"name": "Hverir (Namafjall)", "lat": 65.6410, "lon": -16.8190, "country": "Iceland", "temp_c": 100, "desc": "Surreal geothermal area near Myvatn with boiling mud pots, fumaroles, and sulfur deposits."},
    {"name": "Valley of Geysers, Kamchatka", "lat": 54.4300, "lon": 160.1400, "country": "Russia", "temp_c": 98, "desc": "Second-largest concentration of geysers in the world; UNESCO World Heritage Site."},
]

RING_OF_FIRE = [
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274, "country": "Japan", "elevation_m": 3776, "desc": "Japan's iconic sacred mountain; last erupted in 1707 (Hoei eruption)."},
    {"name": "Mount Rainier", "lat": 46.8523, "lon": -121.7603, "country": "USA", "elevation_m": 4392, "desc": "Most glaciated peak in the contiguous USA; considered one of the most dangerous volcanoes due to lahar risk."},
    {"name": "Mount Pinatubo", "lat": 15.1429, "lon": 120.3496, "country": "Philippines", "elevation_m": 1486, "desc": "Site of the devastating 1991 eruption; the second-largest of the 20th century."},
    {"name": "Cotopaxi", "lat": -0.6840, "lon": -78.4380, "country": "Ecuador", "elevation_m": 5897, "desc": "One of the world's highest active volcanoes with a perfect cone shape."},
    {"name": "Mount Bromo", "lat": -7.9425, "lon": 112.9530, "country": "Indonesia", "elevation_m": 2329, "desc": "Active volcano in the Tengger massif; iconic smoking crater in a sea of sand."},
    {"name": "Krakatau (Anak Krakatau)", "lat": -6.1021, "lon": 105.4230, "country": "Indonesia", "elevation_m": 157, "desc": "Child of Krakatoa; island growing from the 1883 caldera, collapsed dramatically in 2018."},
    {"name": "Mount Ruapehu", "lat": -39.2810, "lon": 175.5640, "country": "New Zealand", "elevation_m": 2797, "desc": "Highest point on the North Island; active crater lake and ski resort coexist."},
    {"name": "Osorno Volcano", "lat": -41.1080, "lon": -72.4930, "country": "Chile", "elevation_m": 2652, "desc": "Strikingly symmetrical stratovolcano in the Chilean Lake District; last erupted 1869."},
    {"name": "Mount Aso", "lat": 32.8840, "lon": 131.1040, "country": "Japan", "elevation_m": 1592, "desc": "One of the largest calderas in the world (25 km); Naka-dake crater is constantly active."},
    {"name": "Tungurahua", "lat": -1.4670, "lon": -78.4420, "country": "Ecuador", "elevation_m": 5023, "desc": "Throat of Fire; highly active stratovolcano that erupted frequently from 1999-2016."},
    {"name": "Klyuchevskoy", "lat": 56.0560, "lon": 160.6420, "country": "Russia (Kamchatka)", "elevation_m": 4750, "desc": "The highest active volcano in Eurasia; almost continuously active."},
    {"name": "Colima Volcano", "lat": 19.5120, "lon": -103.6170, "country": "Mexico", "elevation_m": 3850, "desc": "The most active volcano in Mexico with frequent explosive eruptions."},
    {"name": "Avachinsky", "lat": 53.2560, "lon": 158.8300, "country": "Russia (Kamchatka)", "elevation_m": 2741, "desc": "Overlooks Petropavlovsk-Kamchatsky; one of the most active volcanoes in Kamchatka."},
    {"name": "Mount Ontake", "lat": 35.8930, "lon": 137.4800, "country": "Japan", "elevation_m": 3067, "desc": "Sacred mountain; 2014 phreatic eruption killed 63 hikers, Japan's worst volcanic disaster since 1926."},
    {"name": "Sangay", "lat": -2.0020, "lon": -78.3410, "country": "Ecuador", "elevation_m": 5230, "desc": "One of the most active volcanoes in the world; near-continuous activity since 1934."},
    {"name": "Bezymianny", "lat": 55.9780, "lon": 160.5870, "country": "Russia (Kamchatka)", "elevation_m": 2882, "desc": "Famous for its 1956 directed blast, similar to Mount St. Helens 24 years later."},
    {"name": "Mount Agung", "lat": -8.3420, "lon": 115.5080, "country": "Indonesia (Bali)", "elevation_m": 3031, "desc": "Bali's highest peak and most sacred volcano; devastating 1963 eruption killed ~1,500."},
    {"name": "Chimborazo", "lat": -1.4690, "lon": -78.8160, "country": "Ecuador", "elevation_m": 6263, "desc": "Farthest point from Earth's center due to equatorial bulge; last erupted ~550 CE."},
]

SUBMARINE_VOLCANOES = [
    {"name": "Axial Seamount", "lat": 45.9540, "lon": -130.0140, "country": "Pacific (Juan de Fuca Ridge)", "depth_m": 1410, "desc": "The most active submarine volcano in the NE Pacific; erupted in 2015, monitored by seafloor cables."},
    {"name": "Kavachi", "lat": -8.9910, "lon": 157.9720, "country": "Solomon Islands", "depth_m": 20, "desc": "One of the most active submarine volcanoes; forms ephemeral islands that waves erode away."},
    {"name": "Monowai Seamount", "lat": -25.8870, "lon": -177.1880, "country": "Kermadec Arc (NZ)", "depth_m": 100, "desc": "Extremely active submarine volcano; summit height changes by hundreds of meters between eruptions."},
    {"name": "Kick 'em Jenny", "lat": 12.3000, "lon": -61.6380, "country": "Grenada (Caribbean)", "depth_m": 185, "desc": "The most active submarine volcano in the Lesser Antilles; exclusion zone for ships."},
    {"name": "Marsili Seamount", "lat": 39.2500, "lon": 14.3990, "country": "Italy (Tyrrhenian Sea)", "depth_m": 450, "desc": "Europe's largest submarine volcano; potential tsunami risk to southern Italian coasts."},
    {"name": "Loihi Seamount", "lat": 18.9200, "lon": -155.2700, "country": "USA (Hawaii)", "depth_m": 969, "desc": "The next Hawaiian island being formed; will surface in 10,000-100,000 years."},
    {"name": "NW Rota-1", "lat": 14.6010, "lon": 144.7750, "country": "Mariana Arc", "depth_m": 517, "desc": "First submarine eruption observed live by ROV in 2006; Brimstone Pit vent."},
    {"name": "Havre Seamount", "lat": -31.1000, "lon": -179.0300, "country": "Kermadec Arc (NZ)", "depth_m": 700, "desc": "Site of the largest known deep-ocean eruption in modern history (2012); produced giant pumice raft."},
    {"name": "Kolumbo", "lat": 36.5220, "lon": 25.4890, "country": "Greece (Aegean)", "depth_m": 18, "desc": "Active submarine volcano 7 km NE of Santorini; 1650 eruption killed 70 people."},
    {"name": "Hunga Tonga-Hunga Ha'apai", "lat": -20.5460, "lon": -175.3900, "country": "Tonga", "depth_m": 0, "desc": "Massive eruption on 15 Jan 2022 produced the highest-ever recorded plume (57 km) and global shockwaves."},
    {"name": "Orca Seamount", "lat": -60.5800, "lon": -57.4500, "country": "Antarctica (Bransfield Strait)", "depth_m": 500, "desc": "Active submarine volcano near the South Shetland Islands; geothermally heated waters."},
    {"name": "Myojinsho", "lat": 31.9500, "lon": 140.0200, "country": "Japan", "depth_m": 50, "desc": "Submarine volcano in the Izu-Bonin arc; 1952 eruption destroyed a research vessel killing 31."},
]

VOLCANIC_WINE_REGIONS = [
    {"name": "Mount Etna DOC", "lat": 37.7510, "lon": 14.9934, "country": "Italy (Sicily)", "grapes": "Nerello Mascalese, Carricante", "desc": "Volcanic wines from Europe's most active volcano; high-altitude vineyards up to 1,100 m on lava soils."},
    {"name": "Santorini PDO", "lat": 36.4167, "lon": 25.4333, "country": "Greece", "grapes": "Assyrtiko, Aidani, Athiri", "desc": "Ancient basket-trained vines on volcanic ash; Assyrtiko is one of the world's great white wines."},
    {"name": "Lanzarote La Geria", "lat": 28.9750, "lon": -13.6900, "country": "Spain (Canary Islands)", "grapes": "Malvasia Volcanica", "desc": "Extraordinary lunar landscape; vines grown in pits carved into volcanic ash with stone windbreaks."},
    {"name": "Pico Island", "lat": 38.4667, "lon": -28.3000, "country": "Portugal (Azores)", "grapes": "Verdelho, Arinto", "desc": "UNESCO-listed vineyard landscape; stone-walled currais protect vines from Atlantic winds on basalt."},
    {"name": "Soave DOC", "lat": 45.4200, "lon": 11.2400, "country": "Italy (Veneto)", "grapes": "Garganega", "desc": "Ancient volcanic hills of the Lessini Mountains produce minerally white wines."},
    {"name": "Somlo", "lat": 47.1500, "lon": 17.3700, "country": "Hungary", "grapes": "Furmint, Juhfark", "desc": "Wines from an extinct volcano; once reserved for Habsburg wedding nights."},
    {"name": "Tokaj (Volcanic)", "lat": 48.1200, "lon": 21.4100, "country": "Hungary", "grapes": "Furmint, Harslevelu", "desc": "Famous sweet wine region on volcanic soils; some of the world's oldest classified vineyards."},
    {"name": "Tenerife Wine Region", "lat": 28.3500, "lon": -16.5000, "country": "Spain (Canary Islands)", "grapes": "Listan Negro, Listan Blanco", "desc": "Highest vineyards in Europe at 1,700 m on the slopes of Mount Teide."},
    {"name": "Kaiserstuhl", "lat": 48.0900, "lon": 7.6600, "country": "Germany", "grapes": "Spatburgunder, Grauburgunder", "desc": "Extinct volcanic hills in the Rhine Valley; Germany's warmest and sunniest wine area."},
    {"name": "Campania (Vesuvius)", "lat": 40.8200, "lon": 14.4300, "country": "Italy", "grapes": "Lacryma Christi, Piedirosso", "desc": "Vineyards on the slopes of Vesuvius producing Lacryma Christi del Vesuvio wines."},
    {"name": "Madeira", "lat": 32.6500, "lon": -16.9000, "country": "Portugal", "grapes": "Sercial, Verdelho, Bual, Malmsey", "desc": "Volcanic island producing fortified wines aged by heat; some of the longest-lived wines in the world."},
    {"name": "Tahreveli (Kakheti)", "lat": 41.9800, "lon": 45.6500, "country": "Georgia", "grapes": "Saperavi, Rkatsiteli", "desc": "Ancient winemaking region near volcanic highlands of the Caucasus."},
    {"name": "Willamette Valley", "lat": 45.0000, "lon": -123.0000, "country": "USA (Oregon)", "grapes": "Pinot Noir, Chardonnay", "desc": "Volcanic Jory soils from ancient Cascade eruptions produce world-class Pinot Noir."},
    {"name": "Bandol/Provence Volcanic", "lat": 43.1800, "lon": 5.7500, "country": "France", "grapes": "Mourvedre", "desc": "Volcanic terroir in southern France; ancient volcanic soils near the Mediterranean."},
]

VOLCANIC_OBSERVATORIES = [
    {"name": "Hawaiian Volcano Observatory (HVO)", "lat": 19.4200, "lon": -155.2870, "country": "USA", "agency": "USGS", "desc": "Founded in 1912; monitors Kilauea, Mauna Loa, and other Hawaiian volcanoes continuously."},
    {"name": "Cascades Volcano Observatory (CVO)", "lat": 45.6200, "lon": -122.6000, "country": "USA", "agency": "USGS", "desc": "Monitors Mount St. Helens, Rainier, Hood, and all Cascade Range volcanoes."},
    {"name": "Alaska Volcano Observatory (AVO)", "lat": 64.8580, "lon": -147.8500, "country": "USA", "agency": "USGS/UAF/ADGGS", "desc": "Monitors over 50 historically active volcanoes in Alaska and the Aleutian arc."},
    {"name": "Osservatorio Vesuviano", "lat": 40.8282, "lon": 14.3964, "country": "Italy", "agency": "INGV", "desc": "The world's oldest volcanological observatory, founded in 1841 on Mount Vesuvius."},
    {"name": "INGV Catania (Etna Observatory)", "lat": 37.5132, "lon": 15.0830, "country": "Italy", "agency": "INGV", "desc": "Monitors Mount Etna and the Aeolian Islands volcanoes including Stromboli."},
    {"name": "Icelandic Met Office (IMO)", "lat": 64.1282, "lon": -21.8628, "country": "Iceland", "agency": "IMO/IES", "desc": "Monitors all 30+ active volcanic systems in Iceland including Katla, Hekla, and Grimsvotn."},
    {"name": "GNS Science (Wairakei)", "lat": -38.6280, "lon": 176.1700, "country": "New Zealand", "agency": "GNS/GeoNet", "desc": "Monitors Taupo Volcanic Zone, White Island, Ruapehu, and all NZ volcanoes."},
    {"name": "PHIVOLCS", "lat": 14.6500, "lon": 121.0600, "country": "Philippines", "agency": "DOST-PHIVOLCS", "desc": "Monitors Taal, Mayon, Pinatubo, and 24 active Philippine volcanoes."},
    {"name": "JMA Volcanic Division", "lat": 35.6940, "lon": 139.7530, "country": "Japan", "agency": "JMA", "desc": "Monitors 111 active volcanoes across Japan including Fuji, Sakurajima, and Aso."},
    {"name": "CVGHM (Indonesia)", "lat": -6.6000, "lon": 106.7500, "country": "Indonesia", "agency": "BMKG/CVGHM", "desc": "Monitors 127 active volcanoes in Indonesia, the country with the most active volcanoes."},
    {"name": "SERNAGEOMIN (Chile)", "lat": -33.4400, "lon": -70.6600, "country": "Chile", "agency": "SERNAGEOMIN/OVDAS", "desc": "Monitors over 90 active volcanoes along the Chilean Andes."},
    {"name": "OVSICORI (Costa Rica)", "lat": 10.0020, "lon": -84.1140, "country": "Costa Rica", "agency": "OVSICORI-UNA", "desc": "Monitors Poas, Irazu, Arenal, Rincon de la Vieja, and Turrialba volcanoes."},
    {"name": "Kamchatka Volcanic Eruption Response Team", "lat": 53.0200, "lon": 158.6500, "country": "Russia", "agency": "KVERT/IVS", "desc": "Monitors 29 active volcanoes on the Kamchatka Peninsula for aviation and local safety."},
    {"name": "IGEPN (Ecuador)", "lat": -0.2220, "lon": -78.5120, "country": "Ecuador", "agency": "IGEPN", "desc": "Monitors Cotopaxi, Tungurahua, Sangay, Reventador, and other active Andean volcanoes."},
    {"name": "Montserrat Volcano Observatory", "lat": 16.7160, "lon": -62.1770, "country": "Montserrat (UK)", "agency": "MVO/BGS", "desc": "Established after 1995 Soufriere Hills eruption; monitors ongoing volcanic activity."},
]


# =====================================================================
# MAP MODE DEFINITIONS
# =====================================================================

MAP_MODES = [
    "Active Volcanoes Worldwide",
    "Supervolcanoes & Calderas",
    "Volcanic Island Chains",
    "Famous Eruptions History",
    "Lava Tubes & Caves",
    "Volcanic Hot Springs",
    "Ring of Fire Deep Dive",
    "Submarine Volcanoes",
    "Volcanic Wine Regions",
    "Volcanic Observatories",
]

MODE_DATA = {
    "Active Volcanoes Worldwide": ACTIVE_VOLCANOES,
    "Supervolcanoes & Calderas": SUPERVOLCANOES,
    "Volcanic Island Chains": VOLCANIC_ISLAND_CHAINS,
    "Famous Eruptions History": FAMOUS_ERUPTIONS,
    "Lava Tubes & Caves": LAVA_TUBES,
    "Volcanic Hot Springs": VOLCANIC_HOT_SPRINGS,
    "Ring of Fire Deep Dive": RING_OF_FIRE,
    "Submarine Volcanoes": SUBMARINE_VOLCANOES,
    "Volcanic Wine Regions": VOLCANIC_WINE_REGIONS,
    "Volcanic Observatories": VOLCANIC_OBSERVATORIES,
}

MODE_DESCRIPTIONS = {
    "Active Volcanoes Worldwide": "Currently active volcanoes with recent eruption data from around the globe.",
    "Supervolcanoes & Calderas": "Yellowstone, Toba, Campi Flegrei, Long Valley, and other supervolcanic systems.",
    "Volcanic Island Chains": "Hawaii, Canary Islands, Azores, Galapagos, Iceland, and other volcanic archipelagos.",
    "Famous Eruptions History": "Vesuvius, Krakatoa, Mt St Helens, Pinatubo, Tambora, and other historic eruptions.",
    "Lava Tubes & Caves": "Volcanic caves and lava tunnels worldwide, from Hawaii to Iceland to the Canary Islands.",
    "Volcanic Hot Springs": "Geysers, fumaroles, and thermal areas powered by volcanic heat.",
    "Ring of Fire Deep Dive": "The Pacific Ring of Fire volcanoes in detail, from Kamchatka to the Andes.",
    "Submarine Volcanoes": "Underwater volcanoes, seamounts, and new island formations beneath the oceans.",
    "Volcanic Wine Regions": "Vineyards thriving on volcanic soil: Etna, Santorini, Canary Islands, and more.",
    "Volcanic Observatories": "Volcano monitoring stations and observatories protecting communities worldwide.",
}

MODE_ICONS = {
    "Active Volcanoes Worldwide": "fire",
    "Supervolcanoes & Calderas": "cloud",
    "Volcanic Island Chains": "tint",
    "Famous Eruptions History": "exclamation-triangle",
    "Lava Tubes & Caves": "map",
    "Volcanic Hot Springs": "tint",
    "Ring of Fire Deep Dive": "globe",
    "Submarine Volcanoes": "anchor",
    "Volcanic Wine Regions": "glass",
    "Volcanic Observatories": "eye",
}

MODE_COLORS = {
    "Active Volcanoes Worldwide": "#ef4444",
    "Supervolcanoes & Calderas": "#dc2626",
    "Volcanic Island Chains": "#06b6d4",
    "Famous Eruptions History": "#f59e0b",
    "Lava Tubes & Caves": "#8b5cf6",
    "Volcanic Hot Springs": "#10b981",
    "Ring of Fire Deep Dive": "#f97316",
    "Submarine Volcanoes": "#3b82f6",
    "Volcanic Wine Regions": "#a855f7",
    "Volcanic Observatories": "#ec4899",
}

MODE_ZOOM = {
    "Active Volcanoes Worldwide": 2,
    "Supervolcanoes & Calderas": 2,
    "Volcanic Island Chains": 2,
    "Famous Eruptions History": 2,
    "Lava Tubes & Caves": 2,
    "Volcanic Hot Springs": 2,
    "Ring of Fire Deep Dive": 2,
    "Submarine Volcanoes": 2,
    "Volcanic Wine Regions": 2,
    "Volcanic Observatories": 2,
}


# =====================================================================
# SMITHSONIAN GVP API (LIVE DATA FOR ACTIVE VOLCANOES)
# =====================================================================

@st.cache_data(ttl=3600)
def fetch_smithsonian_volcanoes() -> list:
    """Fetch Holocene volcano data from the Smithsonian GVP via public GeoJSON."""
    try:
        resp = requests.get(
            "https://raw.githubusercontent.com/datasets/geo-boundaries/main/data/volcanoes.geojson",
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            results = []
            for f in features:
                props = f.get("properties", {})
                coords = f.get("geometry", {}).get("coordinates", [None, None])
                if coords[0] is not None and coords[1] is not None:
                    results.append({
                        "name": props.get("name", "Unknown"),
                        "lat": coords[1],
                        "lon": coords[0],
                        "country": props.get("country", ""),
                        "elevation_m": props.get("elevation", ""),
                        "type": props.get("type", ""),
                        "desc": f"Holocene volcano: {props.get('name', 'Unknown')} in {props.get('country', 'Unknown')}",
                    })
            return results
    except Exception:
        pass
    return []


# =====================================================================
# HELPER: BUILD MAP FOR A MODE
# =====================================================================

def _build_volcano_map(data: list, mode: str) -> folium.Map:
    """Build a dark-themed folium map with MarkerCluster for a given mode."""
    color = MODE_COLORS.get(mode, "#ef4444")

    # Compute center
    if data:
        avg_lat = sum(d["lat"] for d in data) / len(data)
        avg_lon = sum(d["lon"] for d in data) / len(data)
    else:
        avg_lat, avg_lon = 20.0, 0.0

    zoom = MODE_ZOOM.get(mode, 2)
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=zoom, tiles="CartoDB dark_matter")

    cluster = MarkerCluster(name=html_module.escape(mode)).add_to(m)

    for item in data:
        name = html_module.escape(str(item.get("name", "Unknown")))
        desc = html_module.escape(str(item.get("desc", "")))
        lat = item["lat"]
        lon = item["lon"]

        # Build popup details
        detail_lines = []
        for key in ["country", "elevation_m", "type", "last_eruption", "vei",
                     "deaths", "caldera_km", "chain", "length_m", "temp_c",
                     "depth_m", "grapes", "agency", "year"]:
            val = item.get(key)
            if val is not None and val != "":
                label = key.replace("_", " ").title()
                detail_lines.append(
                    f'<span style="color:#8b97b0;font-size:0.8rem;">'
                    f'{html_module.escape(str(label))}: {html_module.escape(str(val))}'
                    f'</span>'
                )
        details_html = "<br>".join(detail_lines)

        popup_html = (
            f'<div style="background:#1a2235;color:#e8ecf4;padding:10px;'
            f'border-radius:8px;min-width:180px;max-width:280px;">'
            f'<b style="color:{color};font-size:0.95rem;">{name}</b><br>'
            f'{details_html}'
            f'<br><span style="color:#5a6580;font-size:0.75rem;">{desc}</span>'
            f'</div>'
        )

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
        ).add_to(cluster)

    folium.LayerControl().add_to(m)
    return m


def _build_dataframe(data: list, mode: str) -> pd.DataFrame:
    """Build a clean DataFrame from mode data."""
    if not data:
        return pd.DataFrame()

    rows = []
    for item in data:
        row = {"Name": item.get("name", ""), "Latitude": item.get("lat"), "Longitude": item.get("lon")}
        # Add mode-specific columns
        for key in ["country", "elevation_m", "type", "last_eruption", "vei",
                     "deaths", "caldera_km", "chain", "length_m", "temp_c",
                     "depth_m", "grapes", "agency", "year", "desc"]:
            val = item.get(key)
            if val is not None and val != "":
                col_name = key.replace("_", " ").title()
                row[col_name] = val
        rows.append(row)

    return pd.DataFrame(rows)


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_volcano_deep_maps_tab():
    """Main render function for the Deep Volcanology Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header red">
        <h4>Deep Volcanology Explorer</h4>
        <p>Explore 10 curated volcanic map modes &mdash; active volcanoes, supervolcanoes, famous eruptions, lava tubes, hot springs, submarine volcanoes, volcanic wine regions, and more.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    st.markdown("#### Select Map Mode")

    mode = st.selectbox(
        "Volcano Map Mode",
        MAP_MODES,
        key="volcano_deep_mode",
        help="Choose from 10 curated volcanic exploration modes",
    )

    mode_desc = MODE_DESCRIPTIONS.get(mode, "")
    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem;">{html_module.escape(mode_desc)}</p>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ══════════════════════════════════════════
    # SECTION 2: Load Data
    # ══════════════════════════════════════════
    data = MODE_DATA.get(mode, [])

    if not data:
        st.warning("No data available for this mode.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Stats Row
    # ══════════════════════════════════════════
    st.markdown(f"#### {html_module.escape(mode)}")

    color = MODE_COLORS.get(mode, "#ef4444")

    if mode == "Active Volcanoes Worldwide":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Active Volcanoes", len(data))
        with c2:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))
        with c3:
            types = set(d.get("type", "") for d in data if d.get("type"))
            st.metric("Volcano Types", len(types))
        with c4:
            max_elev = max((d.get("elevation_m", 0) for d in data), default=0)
            st.metric("Highest (m)", f"{max_elev:,}")

    elif mode == "Supervolcanoes & Calderas":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Supervolcanoes", len(data))
        with c2:
            max_vei = max((d.get("vei", 0) for d in data), default=0)
            st.metric("Max VEI", max_vei)
        with c3:
            max_caldera = max((d.get("caldera_km", 0) for d in data), default=0)
            st.metric("Largest Caldera (km)", max_caldera)
        with c4:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))

    elif mode == "Volcanic Island Chains":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Islands", len(data))
        with c2:
            chains = set(d.get("chain", "") for d in data)
            st.metric("Chains", len(chains))
        with c3:
            hemispheres = set("N" if d["lat"] > 0 else "S" for d in data)
            st.metric("Hemispheres", len(hemispheres))
        with c4:
            st.metric("Oceans Covered", "4+")

    elif mode == "Famous Eruptions History":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Famous Eruptions", len(data))
        with c2:
            max_vei = max((d.get("vei", 0) for d in data), default=0)
            st.metric("Max VEI", max_vei)
        with c3:
            eruption_years = [d.get("year", 0) for d in data if d.get("year")]
            span = max(eruption_years) - min(eruption_years) if eruption_years else 0
            st.metric("Timespan (years)", f"{span:,}")
        with c4:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))

    elif mode == "Lava Tubes & Caves":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Lava Tubes", len(data))
        with c2:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))
        with c3:
            max_length = max((d.get("length_m", 0) for d in data), default=0)
            st.metric("Longest (m)", f"{max_length:,}")
        with c4:
            total_length = sum(d.get("length_m", 0) for d in data)
            st.metric("Total Length (km)", f"{total_length / 1000:.1f}")

    elif mode == "Volcanic Hot Springs":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Hot Springs", len(data))
        with c2:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))
        with c3:
            max_temp = max((d.get("temp_c", 0) for d in data), default=0)
            st.metric("Hottest (C)", f"{max_temp}")
        with c4:
            avg_temp = sum(d.get("temp_c", 0) for d in data) / max(len(data), 1)
            st.metric("Avg Temp (C)", f"{avg_temp:.0f}")

    elif mode == "Ring of Fire Deep Dive":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Ring of Fire Volcanoes", len(data))
        with c2:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))
        with c3:
            max_elev = max((d.get("elevation_m", 0) for d in data), default=0)
            st.metric("Highest (m)", f"{max_elev:,}")
        with c4:
            avg_elev = sum(d.get("elevation_m", 0) for d in data) / max(len(data), 1)
            st.metric("Avg Elevation (m)", f"{avg_elev:,.0f}")

    elif mode == "Submarine Volcanoes":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Submarine Volcanoes", len(data))
        with c2:
            countries = set(d.get("country", "") for d in data)
            st.metric("Regions", len(countries))
        with c3:
            max_depth = max((d.get("depth_m", 0) for d in data), default=0)
            st.metric("Deepest (m)", f"{max_depth:,}")
        with c4:
            avg_depth = sum(d.get("depth_m", 0) for d in data) / max(len(data), 1)
            st.metric("Avg Depth (m)", f"{avg_depth:,.0f}")

    elif mode == "Volcanic Wine Regions":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Wine Regions", len(data))
        with c2:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))
        with c3:
            all_grapes = set()
            for d in data:
                for g in d.get("grapes", "").split(", "):
                    if g:
                        all_grapes.add(g)
            st.metric("Grape Varieties", len(all_grapes))
        with c4:
            st.metric("Continents", "4")

    elif mode == "Volcanic Observatories":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Observatories", len(data))
        with c2:
            countries = set(d.get("country", "") for d in data)
            st.metric("Countries", len(countries))
        with c3:
            agencies = set(d.get("agency", "") for d in data if d.get("agency"))
            st.metric("Agencies", len(agencies))
        with c4:
            st.metric("Volcanoes Monitored", "500+")

    # ══════════════════════════════════════════
    # SECTION 4: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Volcanic Map")

    # Color legend
    st.markdown(
        f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">'
        f'<span style="color:{color}; font-size:0.8rem;">&#9679; {html_module.escape(mode)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    m = _build_volcano_map(data, mode)
    st_html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 5: Site Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Site Details")

    for item in data:
        name = html_module.escape(str(item.get("name", "Unknown")))
        desc = html_module.escape(str(item.get("desc", "")))
        lat_str = f'{item["lat"]:.4f}'
        lon_str = f'{item["lon"]:.4f}'

        # Build detail badges
        badges = []
        if item.get("country"):
            badges.append(html_module.escape(str(item["country"])))
        if item.get("elevation_m"):
            badges.append(f'{item["elevation_m"]:,} m' if isinstance(item["elevation_m"], (int, float)) else html_module.escape(str(item["elevation_m"])))
        if item.get("type"):
            badges.append(html_module.escape(str(item["type"])))
        if item.get("last_eruption"):
            badges.append(f'Last: {html_module.escape(str(item["last_eruption"]))}')
        if item.get("vei"):
            badges.append(f'VEI {item["vei"]}')
        if item.get("caldera_km"):
            badges.append(f'Caldera: {item["caldera_km"]} km')
        if item.get("chain"):
            badges.append(html_module.escape(str(item["chain"])))
        if item.get("temp_c"):
            badges.append(f'{item["temp_c"]}°C')
        if item.get("depth_m"):
            badges.append(f'Depth: {item["depth_m"]} m')
        if item.get("grapes"):
            badges.append(html_module.escape(str(item["grapes"])))
        if item.get("agency"):
            badges.append(html_module.escape(str(item["agency"])))
        if item.get("deaths"):
            badges.append(f'Deaths: {html_module.escape(str(item["deaths"]))}')
        if item.get("length_m") and item["length_m"] > 0:
            badges.append(f'Length: {item["length_m"]:,} m')

        badge_html = " &middot; ".join(badges)

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.6rem;">
            <div style="width:10px; height:60px; border-radius:5px; background:{color};
                        margin-right:0.75rem; flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="color:#e8ecf4; font-weight:700; font-size:0.9rem;">{name}</div>
                <div style="color:{color}; font-size:0.78rem;">{badge_html}</div>
                <div style="color:#8b97b0; font-size:0.78rem;">{desc}</div>
                <div style="color:#5a6580; font-size:0.7rem;">{lat_str}, {lon_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 6: Data Table & Download
    # ══════════════════════════════════════════
    st.markdown("---")

    df = _build_dataframe(data, mode)

    if not df.empty:
        with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
            st.dataframe(df, width="stretch", hide_index=True)

        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)

        safe_filename = mode.lower().replace(" ", "_").replace("&", "and").replace("'", "")
        st.download_button(
            f"Download {len(df)} {html_module.escape(mode)} entries (CSV)",
            data=csv_buf.getvalue(),
            file_name=f"volcano_{safe_filename}.csv",
            mime="text/csv",
            key=f"volcano_dl_{safe_filename}",
        )
