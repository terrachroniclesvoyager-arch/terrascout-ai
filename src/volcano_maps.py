# -*- coding: utf-8 -*-
"""
Volcanology Explorer module for TerraScout AI.
Provides 10 thematic volcano/tectonic map modes covering active volcanoes,
Ring of Fire, supervolcanoes, tectonic plates, historic eruptions,
hotspots, lava flow types, volcanic islands, geothermal areas,
and volcanic hazard zones.

All data is hardcoded or sourced from free APIs (Overpass). No API keys needed.
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
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# =====================================================================
# CONSTANTS
# =====================================================================
MAP_MODES = [
    "Active Volcanoes",
    "Ring of Fire",
    "Supervolcanoes",
    "Tectonic Plate Boundaries",
    "Historic Eruptions",
    "Volcanic Hotspots",
    "Lava Flow Types",
    "Volcanic Islands",
    "Geothermal Areas",
    "Volcanic Hazard Zones",
]

# VEI color scale
VEI_COLORS = {
    0: "#10b981", 1: "#22d3ee", 2: "#38bdf8",
    3: "#f59e0b", 4: "#f97316", 5: "#ef4444",
    6: "#dc2626", 7: "#991b1b", 8: "#7f1d1d",
}

# =====================================================================
# 1. ACTIVE VOLCANOES DATA (50+)
# =====================================================================
ACTIVE_VOLCANOES = [
    {"name": "Kilauea", "lat": 19.421, "lon": -155.287, "country": "USA", "elevation_m": 1247, "type": "Shield", "last_eruption": "2023", "region": "Hawaii"},
    {"name": "Etna", "lat": 37.751, "lon": 14.993, "country": "Italy", "elevation_m": 3357, "type": "Stratovolcano", "last_eruption": "2023", "region": "Mediterranean"},
    {"name": "Stromboli", "lat": 38.789, "lon": 15.213, "country": "Italy", "elevation_m": 924, "type": "Stratovolcano", "last_eruption": "2023", "region": "Mediterranean"},
    {"name": "Sakurajima", "lat": 31.585, "lon": 130.657, "country": "Japan", "elevation_m": 1117, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Merapi", "lat": -7.541, "lon": 110.446, "country": "Indonesia", "elevation_m": 2930, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Semeru", "lat": -8.108, "lon": 112.922, "country": "Indonesia", "elevation_m": 3676, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Popocatepetl", "lat": 19.023, "lon": -98.622, "country": "Mexico", "elevation_m": 5426, "type": "Stratovolcano", "last_eruption": "2023", "region": "Americas"},
    {"name": "Fuego", "lat": 14.473, "lon": -90.880, "country": "Guatemala", "elevation_m": 3763, "type": "Stratovolcano", "last_eruption": "2023", "region": "Americas"},
    {"name": "Sangay", "lat": -2.005, "lon": -78.341, "country": "Ecuador", "elevation_m": 5230, "type": "Stratovolcano", "last_eruption": "2023", "region": "Americas"},
    {"name": "Erebus", "lat": -77.530, "lon": 167.153, "country": "Antarctica", "elevation_m": 3794, "type": "Stratovolcano", "last_eruption": "2023", "region": "Antarctica"},
    {"name": "Piton de la Fournaise", "lat": -21.244, "lon": 55.708, "country": "France (Reunion)", "elevation_m": 2632, "type": "Shield", "last_eruption": "2023", "region": "Indian Ocean"},
    {"name": "Yasur", "lat": -19.532, "lon": 169.442, "country": "Vanuatu", "elevation_m": 361, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Villarrica", "lat": -39.420, "lon": -71.930, "country": "Chile", "elevation_m": 2860, "type": "Stratovolcano", "last_eruption": "2023", "region": "Americas"},
    {"name": "Mayon", "lat": 13.257, "lon": 123.685, "country": "Philippines", "elevation_m": 2462, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Erta Ale", "lat": 13.600, "lon": 40.670, "country": "Ethiopia", "elevation_m": 613, "type": "Shield", "last_eruption": "2023", "region": "Africa"},
    {"name": "Nyiragongo", "lat": -1.520, "lon": 29.250, "country": "DR Congo", "elevation_m": 3470, "type": "Stratovolcano", "last_eruption": "2021", "region": "Africa"},
    {"name": "Ol Doinyo Lengai", "lat": -2.764, "lon": 35.914, "country": "Tanzania", "elevation_m": 2962, "type": "Stratovolcano", "last_eruption": "2019", "region": "Africa"},
    {"name": "White Island", "lat": -37.521, "lon": 177.183, "country": "New Zealand", "elevation_m": 321, "type": "Stratovolcano", "last_eruption": "2019", "region": "Pacific"},
    {"name": "Ruapehu", "lat": -39.281, "lon": 175.564, "country": "New Zealand", "elevation_m": 2797, "type": "Stratovolcano", "last_eruption": "2007", "region": "Pacific"},
    {"name": "Pacaya", "lat": 14.381, "lon": -90.601, "country": "Guatemala", "elevation_m": 2552, "type": "Complex", "last_eruption": "2021", "region": "Americas"},
    {"name": "Colima", "lat": 19.514, "lon": -103.617, "country": "Mexico", "elevation_m": 3850, "type": "Stratovolcano", "last_eruption": "2019", "region": "Americas"},
    {"name": "Reventador", "lat": -0.078, "lon": -77.656, "country": "Ecuador", "elevation_m": 3562, "type": "Stratovolcano", "last_eruption": "2023", "region": "Americas"},
    {"name": "Taal", "lat": 14.002, "lon": 120.993, "country": "Philippines", "elevation_m": 311, "type": "Caldera", "last_eruption": "2022", "region": "Pacific"},
    {"name": "Sinabung", "lat": 3.170, "lon": 98.392, "country": "Indonesia", "elevation_m": 2460, "type": "Stratovolcano", "last_eruption": "2021", "region": "Pacific"},
    {"name": "Krakatoa (Anak)", "lat": -6.102, "lon": 105.423, "country": "Indonesia", "elevation_m": 155, "type": "Caldera", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Dukono", "lat": 1.693, "lon": 127.894, "country": "Indonesia", "elevation_m": 1229, "type": "Complex", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Ibu", "lat": 1.488, "lon": 127.630, "country": "Indonesia", "elevation_m": 1325, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Suwanosejima", "lat": 29.638, "lon": 129.714, "country": "Japan", "elevation_m": 796, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Aso", "lat": 32.884, "lon": 131.104, "country": "Japan", "elevation_m": 1592, "type": "Caldera", "last_eruption": "2021", "region": "Pacific"},
    {"name": "Sheveluch", "lat": 56.653, "lon": 161.360, "country": "Russia", "elevation_m": 3283, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Klyuchevskoy", "lat": 56.056, "lon": 160.642, "country": "Russia", "elevation_m": 4750, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Bezymianny", "lat": 55.978, "lon": 160.587, "country": "Russia", "elevation_m": 2882, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Karymsky", "lat": 54.049, "lon": 159.443, "country": "Russia", "elevation_m": 1536, "type": "Stratovolcano", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Ebeko", "lat": 50.686, "lon": 156.014, "country": "Russia", "elevation_m": 1156, "type": "Somma", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Nevado del Ruiz", "lat": 4.892, "lon": -75.322, "country": "Colombia", "elevation_m": 5321, "type": "Stratovolcano", "last_eruption": "2023", "region": "Americas"},
    {"name": "Cotopaxi", "lat": -0.677, "lon": -78.436, "country": "Ecuador", "elevation_m": 5911, "type": "Stratovolcano", "last_eruption": "2023", "region": "Americas"},
    {"name": "Tungurahua", "lat": -1.467, "lon": -78.442, "country": "Ecuador", "elevation_m": 5023, "type": "Stratovolcano", "last_eruption": "2016", "region": "Americas"},
    {"name": "Aira (Sakurajima)", "lat": 31.593, "lon": 130.657, "country": "Japan", "elevation_m": 1117, "type": "Caldera", "last_eruption": "2023", "region": "Pacific"},
    {"name": "Vesuvius", "lat": 40.821, "lon": 14.426, "country": "Italy", "elevation_m": 1281, "type": "Somma", "last_eruption": "1944", "region": "Mediterranean"},
    {"name": "Campi Flegrei", "lat": 40.827, "lon": 14.139, "country": "Italy", "elevation_m": 458, "type": "Caldera", "last_eruption": "1538", "region": "Mediterranean"},
    {"name": "Hekla", "lat": 63.983, "lon": -19.667, "country": "Iceland", "elevation_m": 1491, "type": "Stratovolcano", "last_eruption": "2000", "region": "Atlantic"},
    {"name": "Eyjafjallajokull", "lat": 63.633, "lon": -19.613, "country": "Iceland", "elevation_m": 1651, "type": "Stratovolcano", "last_eruption": "2010", "region": "Atlantic"},
    {"name": "Grimsvotn", "lat": 64.416, "lon": -17.316, "country": "Iceland", "elevation_m": 1725, "type": "Subglacial", "last_eruption": "2011", "region": "Atlantic"},
    {"name": "Fagradalsfjall", "lat": 63.903, "lon": -22.266, "country": "Iceland", "elevation_m": 385, "type": "Fissure", "last_eruption": "2023", "region": "Atlantic"},
    {"name": "Mount Rainier", "lat": 46.853, "lon": -121.760, "country": "USA", "elevation_m": 4392, "type": "Stratovolcano", "last_eruption": "1894", "region": "Americas"},
    {"name": "Mount St. Helens", "lat": 46.200, "lon": -122.180, "country": "USA", "elevation_m": 2549, "type": "Stratovolcano", "last_eruption": "2008", "region": "Americas"},
    {"name": "Mount Shasta", "lat": 41.409, "lon": -122.193, "country": "USA", "elevation_m": 4322, "type": "Stratovolcano", "last_eruption": "1250", "region": "Americas"},
    {"name": "Mauna Loa", "lat": 19.475, "lon": -155.608, "country": "USA", "elevation_m": 4169, "type": "Shield", "last_eruption": "2022", "region": "Hawaii"},
    {"name": "Pinatubo", "lat": 15.130, "lon": 120.350, "country": "Philippines", "elevation_m": 1486, "type": "Stratovolcano", "last_eruption": "1991", "region": "Pacific"},
    {"name": "Agung", "lat": -8.343, "lon": 115.508, "country": "Indonesia", "elevation_m": 3031, "type": "Stratovolcano", "last_eruption": "2019", "region": "Pacific"},
    {"name": "Turrialba", "lat": 10.025, "lon": -83.767, "country": "Costa Rica", "elevation_m": 3340, "type": "Stratovolcano", "last_eruption": "2020", "region": "Americas"},
    {"name": "Rincon de la Vieja", "lat": 10.830, "lon": -85.324, "country": "Costa Rica", "elevation_m": 1916, "type": "Complex", "last_eruption": "2023", "region": "Americas"},
]

# =====================================================================
# 2. RING OF FIRE DATA (40+)
# =====================================================================
RING_OF_FIRE = [
    {"name": "Mount Fuji", "lat": 35.361, "lon": 138.731, "country": "Japan", "elevation_m": 3776, "status": "Active", "last_eruption": "1707"},
    {"name": "Sakurajima", "lat": 31.585, "lon": 130.657, "country": "Japan", "elevation_m": 1117, "status": "Erupting", "last_eruption": "2023"},
    {"name": "Unzen", "lat": 32.761, "lon": 130.299, "country": "Japan", "elevation_m": 1500, "status": "Active", "last_eruption": "1996"},
    {"name": "Pinatubo", "lat": 15.130, "lon": 120.350, "country": "Philippines", "elevation_m": 1486, "status": "Active", "last_eruption": "1991"},
    {"name": "Mayon", "lat": 13.257, "lon": 123.685, "country": "Philippines", "elevation_m": 2462, "status": "Active", "last_eruption": "2023"},
    {"name": "Taal", "lat": 14.002, "lon": 120.993, "country": "Philippines", "elevation_m": 311, "status": "Active", "last_eruption": "2022"},
    {"name": "Krakatoa", "lat": -6.102, "lon": 105.423, "country": "Indonesia", "elevation_m": 155, "status": "Active", "last_eruption": "2023"},
    {"name": "Merapi", "lat": -7.541, "lon": 110.446, "country": "Indonesia", "elevation_m": 2930, "status": "Erupting", "last_eruption": "2023"},
    {"name": "Tambora", "lat": -8.250, "lon": 118.000, "country": "Indonesia", "elevation_m": 2850, "status": "Active", "last_eruption": "1967"},
    {"name": "Agung", "lat": -8.343, "lon": 115.508, "country": "Indonesia", "elevation_m": 3031, "status": "Active", "last_eruption": "2019"},
    {"name": "Ruapehu", "lat": -39.281, "lon": 175.564, "country": "New Zealand", "elevation_m": 2797, "status": "Active", "last_eruption": "2007"},
    {"name": "Tongariro", "lat": -39.134, "lon": 175.643, "country": "New Zealand", "elevation_m": 1978, "status": "Active", "last_eruption": "2012"},
    {"name": "Klyuchevskoy", "lat": 56.056, "lon": 160.642, "country": "Russia", "elevation_m": 4750, "status": "Erupting", "last_eruption": "2023"},
    {"name": "Sheveluch", "lat": 56.653, "lon": 161.360, "country": "Russia", "elevation_m": 3283, "status": "Erupting", "last_eruption": "2023"},
    {"name": "Avachinsky", "lat": 53.256, "lon": 158.836, "country": "Russia", "elevation_m": 2741, "status": "Active", "last_eruption": "2001"},
    {"name": "Mount St. Helens", "lat": 46.200, "lon": -122.180, "country": "USA", "elevation_m": 2549, "status": "Active", "last_eruption": "2008"},
    {"name": "Mount Rainier", "lat": 46.853, "lon": -121.760, "country": "USA", "elevation_m": 4392, "status": "Active", "last_eruption": "1894"},
    {"name": "Mount Hood", "lat": 45.374, "lon": -121.696, "country": "USA", "elevation_m": 3426, "status": "Active", "last_eruption": "1866"},
    {"name": "Mount Baker", "lat": 48.777, "lon": -121.813, "country": "USA", "elevation_m": 3286, "status": "Active", "last_eruption": "1880"},
    {"name": "Mount Shasta", "lat": 41.409, "lon": -122.193, "country": "USA", "elevation_m": 4322, "status": "Active", "last_eruption": "1250"},
    {"name": "Augustine", "lat": 59.363, "lon": -153.430, "country": "USA (Alaska)", "elevation_m": 1252, "status": "Active", "last_eruption": "2006"},
    {"name": "Redoubt", "lat": 60.485, "lon": -152.742, "country": "USA (Alaska)", "elevation_m": 3108, "status": "Active", "last_eruption": "2009"},
    {"name": "Popocatepetl", "lat": 19.023, "lon": -98.622, "country": "Mexico", "elevation_m": 5426, "status": "Erupting", "last_eruption": "2023"},
    {"name": "Colima", "lat": 19.514, "lon": -103.617, "country": "Mexico", "elevation_m": 3850, "status": "Active", "last_eruption": "2019"},
    {"name": "Fuego", "lat": 14.473, "lon": -90.880, "country": "Guatemala", "elevation_m": 3763, "status": "Erupting", "last_eruption": "2023"},
    {"name": "Santa Maria", "lat": 14.756, "lon": -91.552, "country": "Guatemala", "elevation_m": 3772, "status": "Active", "last_eruption": "2023"},
    {"name": "Arenal", "lat": 10.463, "lon": -84.703, "country": "Costa Rica", "elevation_m": 1670, "status": "Active", "last_eruption": "2010"},
    {"name": "Cotopaxi", "lat": -0.677, "lon": -78.436, "country": "Ecuador", "elevation_m": 5911, "status": "Active", "last_eruption": "2023"},
    {"name": "Nevado del Ruiz", "lat": 4.892, "lon": -75.322, "country": "Colombia", "elevation_m": 5321, "status": "Active", "last_eruption": "2023"},
    {"name": "Villarrica", "lat": -39.420, "lon": -71.930, "country": "Chile", "elevation_m": 2860, "status": "Active", "last_eruption": "2023"},
    {"name": "Calbuco", "lat": -41.326, "lon": -72.614, "country": "Chile", "elevation_m": 2015, "status": "Active", "last_eruption": "2015"},
    {"name": "Osorno", "lat": -41.108, "lon": -72.493, "country": "Chile", "elevation_m": 2652, "status": "Active", "last_eruption": "1869"},
    {"name": "Llaima", "lat": -38.692, "lon": -71.729, "country": "Chile", "elevation_m": 3125, "status": "Active", "last_eruption": "2009"},
    {"name": "Hudson", "lat": -45.900, "lon": -72.970, "country": "Chile", "elevation_m": 1905, "status": "Active", "last_eruption": "2011"},
    {"name": "Ubinas", "lat": -16.355, "lon": -70.903, "country": "Peru", "elevation_m": 5672, "status": "Active", "last_eruption": "2019"},
    {"name": "Sabancaya", "lat": -15.780, "lon": -71.857, "country": "Peru", "elevation_m": 5976, "status": "Erupting", "last_eruption": "2023"},
    {"name": "Tungurahua", "lat": -1.467, "lon": -78.442, "country": "Ecuador", "elevation_m": 5023, "status": "Active", "last_eruption": "2016"},
    {"name": "Galeras", "lat": 1.222, "lon": -77.359, "country": "Colombia", "elevation_m": 4276, "status": "Active", "last_eruption": "2014"},
    {"name": "Soufriere Hills", "lat": 16.720, "lon": -62.180, "country": "Montserrat", "elevation_m": 915, "status": "Active", "last_eruption": "2013"},
    {"name": "Aoba (Ambae)", "lat": -15.400, "lon": 167.833, "country": "Vanuatu", "elevation_m": 1496, "status": "Active", "last_eruption": "2018"},
    {"name": "Ulawun", "lat": -5.050, "lon": 151.330, "country": "Papua New Guinea", "elevation_m": 2334, "status": "Active", "last_eruption": "2019"},
]

# =====================================================================
# 3. SUPERVOLCANOES DATA (15)
# =====================================================================
SUPERVOLCANOES = [
    {"name": "Yellowstone Caldera", "lat": 44.430, "lon": -110.590, "country": "USA", "last_super": "640000 BP", "caldera_km": 72, "status": "Restless", "notes": "Largest active geothermal system on Earth; 3 super-eruptions"},
    {"name": "Toba", "lat": 2.680, "lon": 98.880, "country": "Indonesia", "last_super": "74000 BP", "caldera_km": 100, "status": "Resurgent", "notes": "Largest eruption in 2 million years; caused volcanic winter"},
    {"name": "Taupo", "lat": -38.820, "lon": 176.000, "country": "New Zealand", "last_super": "26500 BP", "caldera_km": 35, "status": "Active", "notes": "Most recent super-eruption; Oruanui eruption VEI 8"},
    {"name": "Campi Flegrei", "lat": 40.827, "lon": 14.139, "country": "Italy", "last_super": "39000 BP", "caldera_km": 13, "status": "Restless", "notes": "Campanian Ignimbrite eruption; rising ground (bradyseism)"},
    {"name": "Aira Caldera", "lat": 31.593, "lon": 130.657, "country": "Japan", "last_super": "22000 BP", "caldera_km": 20, "status": "Active", "notes": "Contains Sakurajima; constant eruptions; Kagoshima Bay"},
    {"name": "Long Valley Caldera", "lat": 37.700, "lon": -118.870, "country": "USA", "last_super": "760000 BP", "caldera_km": 32, "status": "Restless", "notes": "Bishop Tuff eruption; ongoing uplift and CO2 emissions"},
    {"name": "Valles Caldera", "lat": 35.870, "lon": -106.570, "country": "USA", "last_super": "1250000 BP", "caldera_km": 22, "status": "Dormant", "notes": "Bandelier Tuff; now a national preserve in New Mexico"},
    {"name": "Lake Atitlan", "lat": 14.690, "lon": -91.190, "country": "Guatemala", "last_super": "84000 BP", "caldera_km": 18, "status": "Dormant", "notes": "Los Chocoyos eruption VEI 8; beautiful lake in caldera"},
    {"name": "Cerro Galan", "lat": -25.990, "lon": -66.930, "country": "Argentina", "last_super": "2200000 BP", "caldera_km": 38, "status": "Dormant", "notes": "One of largest exposed calderas; Puna plateau"},
    {"name": "Whakamaru", "lat": -38.430, "lon": 175.900, "country": "New Zealand", "last_super": "340000 BP", "caldera_km": 30, "status": "Dormant", "notes": "Part of Taupo Volcanic Zone; massive ignimbrite sheets"},
    {"name": "La Garita", "lat": 37.900, "lon": -106.930, "country": "USA", "last_super": "27800000 BP", "caldera_km": 75, "status": "Extinct", "notes": "Fish Canyon Tuff; one of largest known eruptions ever (VEI 9.2)"},
    {"name": "Bennett Lake", "lat": 60.100, "lon": -134.600, "country": "Canada", "last_super": "50000000 BP", "caldera_km": 65, "status": "Extinct", "notes": "Ancient supervolcano remnant in Yukon-BC border region"},
    {"name": "Kikai Caldera", "lat": 30.793, "lon": 130.305, "country": "Japan", "last_super": "7300 BP", "caldera_km": 19, "status": "Active", "notes": "Akahoya eruption devastated prehistoric Jomon culture"},
    {"name": "Emeishan Traps", "lat": 29.000, "lon": 104.000, "country": "China", "last_super": "260000000 BP", "caldera_km": 250, "status": "Extinct", "notes": "Massive flood basalt province; linked to end-Capitanian extinction"},
    {"name": "Pacana Caldera", "lat": -23.440, "lon": -67.570, "country": "Chile", "last_super": "4000000 BP", "caldera_km": 60, "status": "Dormant", "notes": "Atana Ignimbrite; Altiplano-Puna volcanic complex"},
]

# =====================================================================
# 4. TECTONIC PLATE BOUNDARIES (simplified polylines)
# =====================================================================
PLATE_BOUNDARIES = [
    {"name": "Mid-Atlantic Ridge (N)", "type": "Divergent", "color": "#10b981",
     "coords": [[65.0, -18.0], [63.0, -20.0], [54.0, -34.0], [40.0, -30.0], [30.0, -42.0], [15.0, -45.0], [0.0, -25.0]]},
    {"name": "Mid-Atlantic Ridge (S)", "type": "Divergent", "color": "#10b981",
     "coords": [[0.0, -25.0], [-15.0, -13.0], [-30.0, -14.0], [-45.0, -15.0], [-55.0, -1.0]]},
    {"name": "East Pacific Rise", "type": "Divergent", "color": "#10b981",
     "coords": [[23.0, -108.0], [10.0, -104.0], [0.0, -102.0], [-15.0, -112.0], [-30.0, -113.0], [-45.0, -115.0], [-55.0, -120.0]]},
    {"name": "Pacific-North American", "type": "Transform", "color": "#f59e0b",
     "coords": [[60.0, -147.0], [55.0, -160.0], [50.0, -175.0], [45.0, 170.0]]},
    {"name": "San Andreas Fault", "type": "Transform", "color": "#f59e0b",
     "coords": [[40.5, -124.5], [38.0, -122.5], [36.0, -121.0], [34.0, -117.5], [32.5, -115.5]]},
    {"name": "Pacific-Philippine (Mariana)", "type": "Convergent", "color": "#ef4444",
     "coords": [[30.0, 142.0], [25.0, 143.5], [20.0, 147.0], [15.0, 148.5], [10.0, 138.0]]},
    {"name": "Indo-Australian / Eurasian (Sunda)", "type": "Convergent", "color": "#ef4444",
     "coords": [[-10.0, 95.0], [-8.0, 105.0], [-7.0, 110.0], [-8.0, 115.0], [-8.5, 120.0], [-5.0, 128.0]]},
    {"name": "Nazca-South American", "type": "Convergent", "color": "#ef4444",
     "coords": [[-5.0, -82.0], [-15.0, -76.0], [-25.0, -71.0], [-35.0, -73.0], [-45.0, -76.0]]},
    {"name": "Himalayan Front", "type": "Convergent", "color": "#ef4444",
     "coords": [[35.0, 72.0], [32.0, 77.0], [28.0, 84.0], [27.0, 88.0], [25.0, 95.0]]},
    {"name": "Japan Trench", "type": "Convergent", "color": "#ef4444",
     "coords": [[45.0, 150.0], [40.0, 145.0], [35.0, 142.0], [30.0, 140.0]]},
    {"name": "East African Rift", "type": "Divergent", "color": "#10b981",
     "coords": [[12.0, 42.0], [8.0, 38.0], [3.0, 36.0], [-2.0, 36.0], [-8.0, 33.0], [-15.0, 35.0]]},
    {"name": "Alpine-Mediterranean", "type": "Convergent", "color": "#ef4444",
     "coords": [[-5.0, -5.0], [36.0, 0.0], [38.0, 10.0], [39.0, 20.0], [37.0, 28.0], [38.0, 40.0]]},
    {"name": "Cascadia Subduction Zone", "type": "Convergent", "color": "#ef4444",
     "coords": [[50.0, -128.0], [47.0, -126.0], [44.0, -125.0], [41.0, -125.0]]},
    {"name": "Tonga-Kermadec Trench", "type": "Convergent", "color": "#ef4444",
     "coords": [[-15.0, -173.0], [-20.0, -176.0], [-25.0, -177.0], [-30.0, -178.0], [-35.0, -179.0]]},
    {"name": "Philippine Trench", "type": "Convergent", "color": "#ef4444",
     "coords": [[20.0, 123.0], [15.0, 127.0], [10.0, 127.5], [5.0, 127.0]]},
]

# =====================================================================
# 5. HISTORIC ERUPTIONS DATA (30+)
# =====================================================================
HISTORIC_ERUPTIONS = [
    {"name": "Thera (Santorini)", "year": -1600, "lat": 36.404, "lon": 25.396, "vei": 7, "deaths": 0, "notes": "Destroyed Minoan civilization; one of largest eruptions in recorded history"},
    {"name": "Vesuvius (79 AD)", "year": 79, "lat": 40.821, "lon": 14.426, "vei": 5, "deaths": 16000, "notes": "Buried Pompeii and Herculaneum; witnessed by Pliny the Younger"},
    {"name": "Hatepe / Taupo (NZ)", "year": 232, "lat": -38.820, "lon": 176.000, "vei": 7, "deaths": 0, "notes": "Most powerful eruption in last 5000 years; Roman-era red skies"},
    {"name": "Eldgja (Iceland)", "year": 934, "lat": 63.967, "lon": -18.783, "vei": 6, "deaths": 0, "notes": "Largest basalt lava flood in recorded history; 18 km fissure"},
    {"name": "Changbaishan / Paektu", "year": 946, "lat": 41.980, "lon": 128.080, "vei": 7, "deaths": 0, "notes": "Millennium Eruption; ash found in Hokkaido 1100 km away"},
    {"name": "Samalas / Rinjani", "year": 1257, "lat": -8.420, "lon": 116.460, "vei": 7, "deaths": 0, "notes": "May have triggered the Little Ice Age; sulfate spike in ice cores"},
    {"name": "Huaynaputina", "year": 1600, "lat": -16.608, "lon": -70.850, "vei": 6, "deaths": 1500, "notes": "Largest historic eruption in South America; cooled global climate"},
    {"name": "Laki (Iceland)", "year": 1783, "lat": 64.067, "lon": -18.233, "vei": 6, "deaths": 9350, "notes": "8-month fissure eruption; poisoned Europe with fluorine haze"},
    {"name": "Tambora", "year": 1815, "lat": -8.250, "lon": 118.000, "vei": 7, "deaths": 71000, "notes": "Year Without a Summer (1816); deadliest eruption in recorded history"},
    {"name": "Krakatoa", "year": 1883, "lat": -6.102, "lon": 105.423, "vei": 6, "deaths": 36000, "notes": "Loudest sound in recorded history; global tsunami; vivid sunsets"},
    {"name": "Mont Pelee", "year": 1902, "lat": 14.810, "lon": -61.170, "vei": 4, "deaths": 29000, "notes": "Destroyed Saint-Pierre, Martinique; deadliest eruption of 20th century"},
    {"name": "Novarupta / Katmai", "year": 1912, "lat": 58.270, "lon": -155.157, "vei": 6, "deaths": 2, "notes": "Largest eruption of 20th century by volume; Valley of Ten Thousand Smokes"},
    {"name": "Agung (1963)", "year": 1963, "lat": -8.343, "lon": 115.508, "vei": 5, "deaths": 1148, "notes": "Largest eruption in Indonesia in 100 years; global cooling 0.4 C"},
    {"name": "Mount St. Helens", "year": 1980, "lat": 46.200, "lon": -122.180, "vei": 5, "deaths": 57, "notes": "Lateral blast removed 400 m from summit; most studied eruption"},
    {"name": "El Chichon", "year": 1982, "lat": 17.360, "lon": -93.228, "vei": 5, "deaths": 2000, "notes": "Largest sulfur dioxide cloud of 20th century; destroyed 9 villages"},
    {"name": "Nevado del Ruiz", "year": 1985, "lat": 4.892, "lon": -75.322, "vei": 3, "deaths": 23000, "notes": "Lahars buried Armero; worst volcanic disaster in Americas since Pelee"},
    {"name": "Pinatubo", "year": 1991, "lat": 15.130, "lon": 120.350, "vei": 6, "deaths": 847, "notes": "Cooled Earth by 0.5 C; 2nd largest eruption of 20th century"},
    {"name": "Soufriere Hills", "year": 1995, "lat": 16.720, "lon": -62.180, "vei": 3, "deaths": 19, "notes": "Destroyed Plymouth, capital of Montserrat; ongoing since 1995"},
    {"name": "Nyiragongo (2002)", "year": 2002, "lat": -1.520, "lon": 29.250, "vei": 1, "deaths": 147, "notes": "Fastest-flowing lava on Earth entered Goma city, DR Congo"},
    {"name": "Eyjafjallajokull", "year": 2010, "lat": 63.633, "lon": -19.613, "vei": 4, "deaths": 0, "notes": "Ash cloud shut down European airspace for 6 days; 10M travelers affected"},
    {"name": "Merapi (2010)", "year": 2010, "lat": -7.541, "lon": 110.446, "vei": 4, "deaths": 353, "notes": "Largest eruption in 100 years; pyroclastic flows devastated slopes"},
    {"name": "Puyehue-Cordon Caulle", "year": 2011, "lat": -40.590, "lon": -72.117, "vei": 5, "deaths": 0, "notes": "Massive ash cloud circled Southern Hemisphere; flights disrupted"},
    {"name": "Calbuco (2015)", "year": 2015, "lat": -41.326, "lon": -72.614, "vei": 4, "deaths": 0, "notes": "Erupted without warning after 43 years; spectacular ash column"},
    {"name": "Fuego (2018)", "year": 2018, "lat": 14.473, "lon": -90.880, "vei": 4, "deaths": 190, "notes": "Pyroclastic flows buried villages; deadliest eruption in Guatemala since 1902"},
    {"name": "Anak Krakatoa (2018)", "year": 2018, "lat": -6.102, "lon": 105.423, "vei": 3, "deaths": 437, "notes": "Flank collapse triggered Sunda Strait tsunami; cone height halved"},
    {"name": "White Island (2019)", "year": 2019, "lat": -37.521, "lon": 177.183, "vei": 2, "deaths": 22, "notes": "Tourists killed by phreatic eruption; raised questions about access policies"},
    {"name": "Taal (2020)", "year": 2020, "lat": 14.002, "lon": 120.993, "vei": 4, "deaths": 39, "notes": "Phreatomagmatic eruption within a lake; volcanic lightning spectacular"},
    {"name": "La Palma / Cumbre Vieja", "year": 2021, "lat": 28.610, "lon": -17.870, "vei": 3, "deaths": 0, "notes": "85-day eruption destroyed 1600+ buildings on Canary Island"},
    {"name": "Hunga Tonga", "year": 2022, "lat": -20.550, "lon": -175.380, "vei": 5, "deaths": 6, "notes": "Largest atmospheric explosion since Krakatoa; global shockwave; 58 km plume"},
    {"name": "Mauna Loa (2022)", "year": 2022, "lat": 19.475, "lon": -155.608, "vei": 0, "deaths": 0, "notes": "First eruption since 1984; lava flows stopped 2.7 km from main highway"},
    {"name": "Nyiragongo (2021)", "year": 2021, "lat": -1.520, "lon": 29.250, "vei": 1, "deaths": 32, "notes": "Lava flows destroyed Buhene neighborhood in Goma; 400,000 evacuated"},
]

# =====================================================================
# 6. VOLCANIC HOTSPOTS DATA
# =====================================================================
VOLCANIC_HOTSPOTS = [
    {"name": "Hawaii Hotspot", "lat": 19.40, "lon": -155.30, "status": "Active", "chain": "Hawaiian-Emperor seamount chain", "notes": "Over 80 million years of activity; moving NW at 7 cm/yr"},
    {"name": "Iceland Hotspot", "lat": 64.50, "lon": -18.00, "status": "Active", "chain": "Iceland plume on Mid-Atlantic Ridge", "notes": "Unique hotspot on a spreading ridge; 30+ active volcanic systems"},
    {"name": "Yellowstone Hotspot", "lat": 44.43, "lon": -110.59, "status": "Active", "chain": "Snake River Plain track", "notes": "Moving ENE at 4.5 cm/yr; 3 super-eruptions in 2.1 Ma"},
    {"name": "Galapagos Hotspot", "lat": -0.37, "lon": -91.55, "status": "Active", "chain": "Carnegie & Cocos ridges", "notes": "Formed Galapagos Islands; Sierra Negra & Fernandina eruptions"},
    {"name": "Reunion Hotspot", "lat": -21.10, "lon": 55.50, "status": "Active", "chain": "Deccan Traps to Reunion Island", "notes": "Deccan Traps 66 Ma; Piton de la Fournaise one of most active volcanoes"},
    {"name": "Azores Hotspot", "lat": 38.73, "lon": -27.23, "status": "Active", "chain": "Azores Plateau", "notes": "Triple junction hotspot; Capelinhos eruption 1957"},
    {"name": "Canary Islands Hotspot", "lat": 28.10, "lon": -15.40, "status": "Active", "chain": "Canary Island chain", "notes": "Oldest islands in east; La Palma 2021 eruption"},
    {"name": "Cape Verde Hotspot", "lat": 14.90, "lon": -24.00, "status": "Active", "chain": "Cape Verde archipelago", "notes": "Fogo volcano erupted 2014; very slow plate motion"},
    {"name": "Samoan Hotspot", "lat": -14.30, "lon": -170.70, "status": "Active", "chain": "Samoan chain", "notes": "Vailulu'u submarine volcano actively growing"},
    {"name": "Easter Island Hotspot", "lat": -27.12, "lon": -109.35, "status": "Dormant", "chain": "Easter-Salas y Gomez chain", "notes": "Created Rapa Nui; extinct on island but active submarine"},
    {"name": "Kerguelen Hotspot", "lat": -49.35, "lon": 69.15, "status": "Active", "chain": "Kerguelen Plateau/Ninetyeast Ridge", "notes": "One of largest oceanic plateaus; 130 Ma of activity"},
    {"name": "Tristan Hotspot", "lat": -37.11, "lon": -12.28, "status": "Active", "chain": "Walvis Ridge & Parana-Etendeka traps", "notes": "Tristan da Cunha - most remote inhabited island"},
    {"name": "Afar Hotspot", "lat": 11.50, "lon": 42.00, "status": "Active", "chain": "Afar Triple Junction", "notes": "Where 3 plates diverge; Erta Ale lava lake; new ocean forming"},
    {"name": "Comoros Hotspot", "lat": -12.38, "lon": 43.25, "status": "Active", "chain": "Comoros archipelago", "notes": "Karthala volcano among most active in Africa"},
    {"name": "Louisville Hotspot", "lat": -50.90, "lon": -139.00, "status": "Active", "chain": "Louisville Ridge", "notes": "Pacific plate hotspot; 80 Ma seamount chain"},
    {"name": "Pitcairn Hotspot", "lat": -25.07, "lon": -130.10, "status": "Active", "chain": "Pitcairn-Gambier chain", "notes": "Active submarine volcanism; Bounty mutineers island"},
    {"name": "Juan Fernandez Hotspot", "lat": -33.75, "lon": -80.75, "status": "Active", "chain": "Juan Fernandez Ridge", "notes": "Robinson Crusoe island; eastward age progression"},
    {"name": "Cameroon Hotspot", "lat": 4.20, "lon": 9.17, "status": "Active", "chain": "Cameroon Volcanic Line", "notes": "Mount Cameroon last erupted 2012; on continental plate"},
]

# =====================================================================
# 7. LAVA FLOW TYPES (educational)
# =====================================================================
LAVA_TYPES = [
    {"type": "Pahoehoe", "temp_c": "1100-1200", "viscosity": "Very Low", "speed_kmh": "1-10", "sio2_pct": "45-52", "description": "Smooth, ropy, billowy lava with a glassy skin; Hawaiian term meaning smooth unbroken", "example_loc": "Kilauea, Hawaii", "lat": 19.421, "lon": -155.287, "color": "#ef4444"},
    {"type": "Aa", "temp_c": "1000-1100", "viscosity": "Low-Medium", "speed_kmh": "0.5-5", "sio2_pct": "45-52", "description": "Rough, jagged, clinkery basalt lava; Hawaiian term for stony rough lava", "example_loc": "Etna, Sicily", "lat": 37.751, "lon": 14.993, "color": "#f97316"},
    {"type": "Pillow Lava", "temp_c": "1100-1200", "viscosity": "Low", "speed_kmh": "N/A (submarine)", "sio2_pct": "45-55", "description": "Bulbous pillow shapes formed underwater at mid-ocean ridges", "example_loc": "Mid-Atlantic Ridge", "lat": 37.750, "lon": -32.000, "color": "#3b82f6"},
    {"type": "Block Lava", "temp_c": "800-1000", "viscosity": "High", "speed_kmh": "0.01-0.5", "sio2_pct": "57-70", "description": "Smooth-faced angular blocks; produced by andesitic/dacitic eruptions", "example_loc": "Colima, Mexico", "lat": 19.514, "lon": -103.617, "color": "#8b5cf6"},
    {"type": "Obsidian Flow", "temp_c": "700-900", "viscosity": "Very High", "speed_kmh": "0.001-0.01", "sio2_pct": "70-77", "description": "Volcanic glass formed when rhyolite lava cools too fast for crystals", "example_loc": "Obsidian Dome, California", "lat": 37.744, "lon": -118.983, "color": "#1e1b4b"},
    {"type": "Pumice Flow", "temp_c": "800-1200", "viscosity": "Variable", "speed_kmh": "50-200 (pyroclastic)", "sio2_pct": "65-77", "description": "Frothy volcanic glass so light it floats on water; formed by explosive eruptions", "example_loc": "Lipari, Italy", "lat": 38.480, "lon": 14.954, "color": "#d4d4d8"},
    {"type": "Carbonatite Lava", "temp_c": "500-600", "viscosity": "Extremely Low", "speed_kmh": "1-30", "sio2_pct": "<1", "description": "Only known natrocarbonatite lava; erupts black, turns white; no silica", "example_loc": "Ol Doinyo Lengai, Tanzania", "lat": -2.764, "lon": 35.914, "color": "#e8ecf4"},
    {"type": "Flood Basalt", "temp_c": "1100-1250", "viscosity": "Very Low", "speed_kmh": "5-50", "sio2_pct": "45-52", "description": "Massive eruptions covering >100,000 sq km; linked to mass extinctions", "example_loc": "Deccan Traps, India", "lat": 18.520, "lon": 73.860, "color": "#991b1b"},
    {"type": "Dacite Lava Dome", "temp_c": "800-1000", "viscosity": "Very High", "speed_kmh": "<0.001", "sio2_pct": "63-70", "description": "Thick, pasty lava that piles up into domes; can collapse causing pyroclastic flows", "example_loc": "Mount St. Helens, USA", "lat": 46.200, "lon": -122.180, "color": "#a855f7"},
    {"type": "Rhyolite Flow", "temp_c": "700-850", "viscosity": "Extremely High", "speed_kmh": "<0.001", "sio2_pct": "70-77", "description": "Most viscous common lava; forms thick, steep-sided flows and coulees", "example_loc": "Yellowstone, USA", "lat": 44.430, "lon": -110.590, "color": "#ec4899"},
]

# =====================================================================
# 8. VOLCANIC ISLANDS DATA (25+)
# =====================================================================
VOLCANIC_ISLANDS = [
    {"name": "Hawaii (Big Island)", "lat": 19.60, "lon": -155.50, "country": "USA", "area_km2": 10430, "highest_m": 4207, "active": True, "notes": "Mauna Kea is tallest mountain from base; 5 shield volcanoes"},
    {"name": "Iceland", "lat": 64.96, "lon": -19.02, "country": "Iceland", "area_km2": 103000, "highest_m": 2110, "active": True, "notes": "Largest volcanic island; straddles Mid-Atlantic Ridge"},
    {"name": "Tenerife", "lat": 28.27, "lon": -16.60, "country": "Spain", "area_km2": 2034, "highest_m": 3718, "active": True, "notes": "Mount Teide is highest point in Spain and Atlantic islands"},
    {"name": "Reunion", "lat": -21.12, "lon": 55.53, "country": "France", "area_km2": 2512, "highest_m": 3071, "active": True, "notes": "Piton de la Fournaise erupts nearly every year"},
    {"name": "Santorini", "lat": 36.39, "lon": 25.46, "country": "Greece", "area_km2": 73, "highest_m": 567, "active": True, "notes": "Caldera island from Minoan eruption; Nea Kameni still active"},
    {"name": "Jeju Island", "lat": 33.36, "lon": 126.53, "country": "South Korea", "area_km2": 1849, "highest_m": 1950, "active": False, "notes": "Hallasan shield volcano; UNESCO World Heritage lava tubes"},
    {"name": "Sicily", "lat": 37.60, "lon": 14.00, "country": "Italy", "area_km2": 25711, "highest_m": 3357, "active": True, "notes": "Mount Etna is Europe's tallest and most active volcano"},
    {"name": "Java", "lat": -7.50, "lon": 110.00, "country": "Indonesia", "area_km2": 129000, "highest_m": 3676, "active": True, "notes": "45 active volcanoes; most volcanically active island on Earth"},
    {"name": "Surtsey", "lat": 63.30, "lon": -20.60, "country": "Iceland", "area_km2": 1.3, "highest_m": 155, "active": False, "notes": "Born 1963 from submarine eruption; UNESCO site for ecological succession"},
    {"name": "Montserrat", "lat": 16.72, "lon": -62.18, "country": "UK", "area_km2": 102, "highest_m": 915, "active": True, "notes": "Soufriere Hills destroyed capital Plymouth in 1997"},
    {"name": "Krakatoa (Anak)", "lat": -6.10, "lon": 105.42, "country": "Indonesia", "area_km2": 3.1, "highest_m": 155, "active": True, "notes": "Child of Krakatoa; emerged 1927; collapsed in 2018 tsunami"},
    {"name": "Isabela Island", "lat": -0.83, "lon": -91.13, "country": "Ecuador", "area_km2": 4588, "highest_m": 1707, "active": True, "notes": "Largest Galapagos island; 5 active shield volcanoes"},
    {"name": "Tristan da Cunha", "lat": -37.11, "lon": -12.28, "country": "UK", "area_km2": 98, "highest_m": 2062, "active": True, "notes": "Most remote inhabited island; erupted 1961, evacuated to UK"},
    {"name": "Hokkaido", "lat": 43.06, "lon": 141.35, "country": "Japan", "area_km2": 83424, "highest_m": 2291, "active": True, "notes": "Multiple active volcanoes; Lake Toya caldera; Tokachi-dake"},
    {"name": "Martinique", "lat": 14.64, "lon": -61.02, "country": "France", "area_km2": 1128, "highest_m": 1397, "active": True, "notes": "Mont Pelee 1902 eruption destroyed St-Pierre; 29,000 dead"},
    {"name": "La Palma", "lat": 28.68, "lon": -17.87, "country": "Spain", "area_km2": 708, "highest_m": 2426, "active": True, "notes": "Cumbre Vieja eruption 2021; longest eruption in recorded history of island"},
    {"name": "Azores (Sao Miguel)", "lat": 37.75, "lon": -25.67, "country": "Portugal", "area_km2": 747, "highest_m": 1103, "active": True, "notes": "Furnas caldera with fumaroles and hot springs; Sete Cidades caldera"},
    {"name": "Dominica", "lat": 15.41, "lon": -61.37, "country": "Dominica", "area_km2": 750, "highest_m": 1447, "active": True, "notes": "9 active volcanoes; Boiling Lake 2nd largest hot spring in world"},
    {"name": "Heard Island", "lat": -53.10, "lon": 73.50, "country": "Australia", "area_km2": 368, "highest_m": 2745, "active": True, "notes": "Big Ben volcano; one of most remote active volcanoes on Earth"},
    {"name": "Fernandina Island", "lat": -0.37, "lon": -91.55, "country": "Ecuador", "area_km2": 642, "highest_m": 1476, "active": True, "notes": "Most active Galapagos volcano; pristine ecosystem; erupted 2020"},
    {"name": "Miyake-jima", "lat": 34.08, "lon": 139.53, "country": "Japan", "area_km2": 55, "highest_m": 775, "active": True, "notes": "Evacuated 2000; volcanic gas masks required for residents until 2005"},
    {"name": "Nisyros", "lat": 36.58, "lon": 27.16, "country": "Greece", "area_km2": 41, "highest_m": 698, "active": True, "notes": "Active caldera with fumaroles; hydrothermal activity; Dodecanese"},
    {"name": "Aogashima", "lat": 32.45, "lon": 139.77, "country": "Japan", "area_km2": 5.98, "highest_m": 423, "active": True, "notes": "Double caldera island; inhabited; last erupted 1785"},
    {"name": "Deception Island", "lat": -62.97, "lon": -60.65, "country": "Antarctica", "area_km2": 98, "highest_m": 539, "active": True, "notes": "Active caldera in Antarctica; ships sail into flooded caldera"},
    {"name": "Ascension Island", "lat": -7.94, "lon": -14.36, "country": "UK", "area_km2": 91, "highest_m": 859, "active": False, "notes": "Volcanic island in mid-Atlantic; Green Mountain cloud forest experiment"},
    {"name": "White Island (Whakaari)", "lat": -37.52, "lon": 177.18, "country": "New Zealand", "area_km2": 3.3, "highest_m": 321, "active": True, "notes": "2019 eruption killed 22 tourists; private island volcano"},
]

# =====================================================================
# 9. GEOTHERMAL -- via Overpass (see function below)
# =====================================================================
GEOTHERMAL_PRESETS = {
    "Custom Area": None,
    "Iceland": {"lat": 64.96, "lon": -19.02, "radius": 200},
    "Yellowstone Region": {"lat": 44.50, "lon": -110.50, "radius": 100},
    "New Zealand (Taupo)": {"lat": -38.70, "lon": 176.10, "radius": 100},
    "Kamchatka, Russia": {"lat": 53.50, "lon": 158.50, "radius": 150},
    "Japan (Tohoku)": {"lat": 39.00, "lon": 140.00, "radius": 150},
    "East Africa Rift": {"lat": -1.00, "lon": 36.50, "radius": 200},
    "Italy (Tuscany)": {"lat": 43.00, "lon": 11.00, "radius": 100},
    "Azores, Portugal": {"lat": 37.75, "lon": -25.67, "radius": 80},
    "Chile (Atacama)": {"lat": -22.50, "lon": -68.00, "radius": 150},
}

# =====================================================================
# 10. VOLCANIC HAZARD ZONES (cities near volcanoes)
# =====================================================================
HAZARD_ZONES = [
    {"city": "Naples", "country": "Italy", "population": 3100000, "lat": 40.851, "lon": 14.268, "volcano": "Vesuvius", "vlat": 40.821, "vlon": 14.426, "distance_km": 12, "risk": "Extreme", "notes": "3M people in red zone; last erupted 1944; overdue for major event"},
    {"city": "Kagoshima", "country": "Japan", "population": 600000, "lat": 31.596, "lon": 130.557, "volcano": "Sakurajima", "vlat": 31.585, "vlon": 130.657, "distance_km": 8, "risk": "Extreme", "notes": "City faces active erupting volcano across bay; daily ash fall"},
    {"city": "Yogyakarta", "country": "Indonesia", "population": 3500000, "lat": -7.797, "lon": 110.361, "volcano": "Merapi", "vlat": -7.541, "vlon": 110.446, "distance_km": 28, "risk": "Very High", "notes": "One of most active volcanoes; killed 353 people in 2010"},
    {"city": "Mexico City", "country": "Mexico", "population": 21600000, "lat": 19.432, "lon": -99.133, "volcano": "Popocatepetl", "vlat": 19.023, "vlon": -98.622, "distance_km": 60, "risk": "High", "notes": "Mega-city within ash fall range; 25M in risk zone; erupting 2023"},
    {"city": "Quito", "country": "Ecuador", "population": 2700000, "lat": -0.181, "lon": -78.467, "volcano": "Cotopaxi", "vlat": -0.677, "vlon": -78.436, "distance_km": 55, "risk": "High", "notes": "Lahars could reach suburbs; Cotopaxi reactivated 2023"},
    {"city": "Seattle-Tacoma", "country": "USA", "population": 4000000, "lat": 47.606, "lon": -122.332, "volcano": "Mount Rainier", "vlat": 46.853, "vlon": -121.760, "distance_km": 90, "risk": "High", "notes": "Lahar risk to valleys; largest glaciated volcano in lower 48"},
    {"city": "Auckland", "country": "New Zealand", "population": 1660000, "lat": -36.848, "lon": 174.763, "volcano": "Auckland Volcanic Field", "vlat": -36.900, "vlon": 174.850, "distance_km": 0, "risk": "Very High", "notes": "City built on 53 volcanic vents; last erupted 600 yrs ago"},
    {"city": "Catania", "country": "Italy", "population": 1100000, "lat": 37.502, "lon": 15.087, "volcano": "Etna", "vlat": 37.751, "vlon": 14.993, "distance_km": 28, "risk": "High", "notes": "Europe's most active volcano looms over city; frequent eruptions"},
    {"city": "Manado", "country": "Indonesia", "population": 450000, "lat": 1.474, "lon": 124.842, "volcano": "Lokon-Empung", "vlat": 1.358, "vlon": 124.792, "distance_km": 15, "risk": "Very High", "notes": "Multiple active volcanoes nearby; eruptions 2012"},
    {"city": "Goma", "country": "DR Congo", "population": 1000000, "lat": -1.679, "lon": 29.222, "volcano": "Nyiragongo", "vlat": -1.520, "vlon": 29.250, "distance_km": 18, "risk": "Extreme", "notes": "Fastest lava on Earth; entered city 2002 and 2021"},
    {"city": "Rabaul", "country": "Papua New Guinea", "population": 14000, "lat": -4.201, "lon": 152.167, "volcano": "Tavurvur", "vlat": -4.240, "vlon": 152.213, "distance_km": 6, "risk": "Extreme", "notes": "Town buried in 1994; caldera eruption destroyed old town center"},
    {"city": "Arequipa", "country": "Peru", "population": 1100000, "lat": -16.409, "lon": -71.537, "volcano": "Misti", "vlat": -16.294, "vlon": -71.409, "distance_km": 17, "risk": "Very High", "notes": "Active stratovolcano overlooking Peru's 2nd largest city"},
    {"city": "Manila", "country": "Philippines", "population": 14400000, "lat": 14.599, "lon": 120.984, "volcano": "Taal", "vlat": 14.002, "vlon": 120.993, "distance_km": 66, "risk": "High", "notes": "Taal erupted 2020 within mega-city ash range; Pinatubo also nearby"},
    {"city": "Pozzuoli", "country": "Italy", "population": 80000, "lat": 40.826, "lon": 14.121, "volcano": "Campi Flegrei", "vlat": 40.827, "vlon": 14.139, "distance_km": 2, "risk": "Extreme", "notes": "Inside a supervolcano caldera; ground rising; seismic swarms 2023"},
    {"city": "Bandung", "country": "Indonesia", "population": 2500000, "lat": -6.905, "lon": 107.613, "volcano": "Tangkuban Parahu", "vlat": -6.770, "vlon": 107.600, "distance_km": 15, "risk": "High", "notes": "Active volcano caldera north of city; phreatic eruption 2019"},
    {"city": "Hilo", "country": "USA (Hawaii)", "population": 46000, "lat": 19.720, "lon": -155.084, "volcano": "Mauna Loa", "vlat": 19.475, "vlon": -155.608, "distance_km": 50, "risk": "High", "notes": "Lava flows from 2022 eruption approached; Kilauea also nearby"},
    {"city": "Shimabara", "country": "Japan", "population": 45000, "lat": 32.789, "lon": 130.370, "volcano": "Unzen", "vlat": 32.761, "vlon": 130.299, "distance_km": 7, "risk": "Very High", "notes": "1792 collapse killed 15,000; pyroclastic flows 1991 killed 43"},
    {"city": "Reykjavik", "country": "Iceland", "population": 140000, "lat": 64.146, "lon": -21.942, "volcano": "Fagradalsfjall", "vlat": 63.903, "vlon": -22.266, "distance_km": 30, "risk": "Moderate", "notes": "Reykjanes Peninsula eruptions 2021-2023; Grindavik evacuated"},
    {"city": "Managua", "country": "Nicaragua", "population": 1050000, "lat": 12.136, "lon": -86.251, "volcano": "Masaya", "vlat": 11.984, "vlon": -86.161, "distance_km": 20, "risk": "High", "notes": "Lava lake visible from city; indigenous called it Mouth of Hell"},
    {"city": "Petropavlovsk-Kamchatsky", "country": "Russia", "population": 180000, "lat": 53.024, "lon": 158.643, "volcano": "Avachinsky & Koryaksky", "vlat": 53.256, "vlon": 158.836, "distance_km": 25, "risk": "Very High", "notes": "Two stratovolcanoes tower over city; Kamchatka Ring of Fire"},
]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def _make_base_map(lat: float = 20.0, lon: float = 0.0, zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map."""
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )


def _render_map(m: folium.Map, height: int = 500):
    """Render a folium map via streamlit components."""
    components.html(m._repr_html_(), height=height)


def _dark_fig(figsize=(10, 5)):
    """Create a matplotlib figure with dark theme."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.tick_params(colors="#8b97b0")
    ax.xaxis.label.set_color("#e8ecf4")
    ax.yaxis.label.set_color("#e8ecf4")
    ax.title.set_color("#e8ecf4")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


def _fig_to_image(fig):
    """Save matplotlib fig to BytesIO and display."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _csv_download(df: pd.DataFrame, filename: str, label: str, key: str):
    """Standard CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(label, data=csv_buf.getvalue(), file_name=filename,
                       mime="text/csv", key=key)


@st.cache_data(ttl=3600)
def _overpass_geothermal(lat: float, lon: float, radius_km: float):
    """Fetch geysers and hot springs via Overpass API."""
    q = f"""
    [out:json][timeout:60];
    (
      node["natural"="geyser"](around:{radius_km * 1000},{lat},{lon});
      node["natural"="hot_spring"](around:{radius_km * 1000},{lat},{lon});
      way["natural"="geyser"](around:{radius_km * 1000},{lat},{lon});
      way["natural"="hot_spring"](around:{radius_km * 1000},{lat},{lon});
    );
    out center body;
    """
    return query_overpass(q)


# =====================================================================
# MODE RENDERING FUNCTIONS
# =====================================================================

def _render_active_volcanoes():
    """Mode 1: Active Volcanoes worldwide."""
    st.markdown("#### Active Volcanoes Worldwide")
    st.markdown("50+ currently active or recently erupting volcanoes with type, elevation, and last eruption data.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        type_filter = st.multiselect("Volcano Type", sorted(set(v["type"] for v in ACTIVE_VOLCANOES)),
                                     default=sorted(set(v["type"] for v in ACTIVE_VOLCANOES)), key="av_type")
    with col_f2:
        region_filter = st.multiselect("Region", sorted(set(v["region"] for v in ACTIVE_VOLCANOES)),
                                       default=sorted(set(v["region"] for v in ACTIVE_VOLCANOES)), key="av_region")

    filtered = [v for v in ACTIVE_VOLCANOES if v["type"] in type_filter and v["region"] in region_filter]

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Volcanoes", len(filtered))
    with c2:
        st.metric("Countries", len(set(v["country"] for v in filtered)))
    with c3:
        st.metric("Highest", f"{max((v['elevation_m'] for v in filtered), default=0):,} m")
    with c4:
        st.metric("Types", len(set(v["type"] for v in filtered)))

    # Map
    m = _make_base_map()
    cluster = MarkerCluster(name="Active Volcanoes")
    type_colors = {"Shield": "#ef4444", "Stratovolcano": "#f97316", "Caldera": "#dc2626",
                   "Complex": "#f59e0b", "Somma": "#e11d48", "Subglacial": "#38bdf8", "Fissure": "#10b981"}
    for v in filtered:
        c = type_colors.get(v["type"], "#06b6d4")
        popup = (
            f"<div style='min-width:200px;'>"
            f"<b>{escape(v['name'])}</b><br>"
            f"<b>Country:</b> {escape(v['country'])}<br>"
            f"<b>Type:</b> {escape(v['type'])}<br>"
            f"<b>Elevation:</b> {v['elevation_m']:,} m<br>"
            f"<b>Last Eruption:</b> {escape(str(v['last_eruption']))}<br>"
            f"<b>Region:</b> {escape(v['region'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[v["lat"], v["lon"]], radius=8,
            color=c, fill=True, fill_color=c, fill_opacity=0.8,
            popup=folium.Popup(popup, max_width=300),
            tooltip=escape(v["name"]),
        ).add_to(cluster)
    cluster.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: elevation by type
    fig, ax = _dark_fig(figsize=(10, 5))
    types = sorted(set(v["type"] for v in filtered))
    avgs = [sum(v["elevation_m"] for v in filtered if v["type"] == t) / max(1, len([v for v in filtered if v["type"] == t])) for t in types]
    bars = ax.bar(types, avgs, color="#06b6d4", edgecolor="#2a3550")
    ax.set_ylabel("Avg Elevation (m)")
    ax.set_title("Average Elevation by Volcano Type")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    _fig_to_image(fig)

    # Dataframe
    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "active_volcanoes.csv", f"Download {len(df)} Active Volcanoes (CSV)", "av_dl")


def _render_ring_of_fire():
    """Mode 2: Ring of Fire."""
    st.markdown("#### Pacific Ring of Fire")
    st.markdown("40+ major volcanoes along the 40,000 km horseshoe-shaped zone of tectonic activity encircling the Pacific Ocean.")

    status_filter = st.radio("Status Filter", ["All", "Erupting", "Active"], horizontal=True, key="rof_status")
    filtered = RING_OF_FIRE if status_filter == "All" else [v for v in RING_OF_FIRE if v["status"] == status_filter]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Volcanoes", len(filtered))
    with c2:
        st.metric("Erupting", len([v for v in filtered if v["status"] == "Erupting"]))
    with c3:
        st.metric("Countries", len(set(v["country"] for v in filtered)))
    with c4:
        st.metric("Highest", f"{max((v['elevation_m'] for v in filtered), default=0):,} m")

    m = _make_base_map(lat=10.0, lon=-170.0, zoom=2)
    for v in filtered:
        c = "#dc2626" if v["status"] == "Erupting" else "#f59e0b"
        popup = (
            f"<div style='min-width:200px;'>"
            f"<b>{escape(v['name'])}</b><br>"
            f"<b>Country:</b> {escape(v['country'])}<br>"
            f"<b>Elevation:</b> {v['elevation_m']:,} m<br>"
            f"<b>Status:</b> {escape(v['status'])}<br>"
            f"<b>Last Eruption:</b> {escape(str(v['last_eruption']))}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[v["lat"], v["lon"]], radius=9 if v["status"] == "Erupting" else 7,
            color=c, fill=True, fill_color=c, fill_opacity=0.85,
            popup=folium.Popup(popup, max_width=300),
            tooltip=escape(v["name"]),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: top 15 by elevation
    fig, ax = _dark_fig(figsize=(10, 5))
    top = sorted(filtered, key=lambda v: v["elevation_m"], reverse=True)[:15]
    names = [v["name"][:20] for v in top]
    elev = [v["elevation_m"] for v in top]
    colors = ["#dc2626" if v["status"] == "Erupting" else "#f59e0b" for v in top]
    ax.barh(names, elev, color=colors, edgecolor="#2a3550")
    ax.set_xlabel("Elevation (m)")
    ax.set_title("Ring of Fire - Top 15 by Elevation")
    ax.invert_yaxis()
    fig.tight_layout()
    _fig_to_image(fig)

    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "ring_of_fire.csv", f"Download {len(df)} Ring of Fire Volcanoes (CSV)", "rof_dl")


def _render_supervolcanoes():
    """Mode 3: Supervolcanoes."""
    st.markdown("#### Supervolcanoes")
    st.markdown("15 known supervolcano calderas capable of VEI 8+ eruptions, with their last catastrophic event and current status.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Supervolcanoes", len(SUPERVOLCANOES))
    with c2:
        st.metric("Restless/Active", len([s for s in SUPERVOLCANOES if s["status"] in ("Restless", "Active", "Resurgent")]))
    with c3:
        st.metric("Largest Caldera", f"{max(s['caldera_km'] for s in SUPERVOLCANOES)} km")
    with c4:
        st.metric("Countries", len(set(s["country"] for s in SUPERVOLCANOES)))

    m = _make_base_map()
    for s in SUPERVOLCANOES:
        status_colors = {"Active": "#dc2626", "Restless": "#f59e0b", "Resurgent": "#f97316",
                         "Dormant": "#8b97b0", "Extinct": "#5a6580"}
        c = status_colors.get(s["status"], "#06b6d4")
        popup = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(s['name'])}</b><br>"
            f"<b>Country:</b> {escape(s['country'])}<br>"
            f"<b>Last Super-eruption:</b> {escape(s['last_super'])}<br>"
            f"<b>Caldera Size:</b> {s['caldera_km']} km<br>"
            f"<b>Status:</b> {escape(s['status'])}<br>"
            f"<b>Notes:</b> {escape(s['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[s["lat"], s["lon"]], radius=max(6, s["caldera_km"] / 5),
            color=c, fill=True, fill_color=c, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=320),
            tooltip=escape(s["name"]),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: caldera size
    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_sv = sorted(SUPERVOLCANOES, key=lambda s: s["caldera_km"], reverse=True)
    names = [s["name"][:22] for s in sorted_sv]
    sizes = [s["caldera_km"] for s in sorted_sv]
    status_colors_list = {"Active": "#dc2626", "Restless": "#f59e0b", "Resurgent": "#f97316",
                          "Dormant": "#8b97b0", "Extinct": "#5a6580"}
    bar_colors = [status_colors_list.get(s["status"], "#06b6d4") for s in sorted_sv]
    ax.barh(names, sizes, color=bar_colors, edgecolor="#2a3550")
    ax.set_xlabel("Caldera Diameter (km)")
    ax.set_title("Supervolcano Caldera Sizes")
    ax.invert_yaxis()
    fig.tight_layout()
    _fig_to_image(fig)

    df = pd.DataFrame(SUPERVOLCANOES)
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "supervolcanoes.csv", f"Download {len(df)} Supervolcanoes (CSV)", "sv_dl")


def _render_tectonic_plates():
    """Mode 4: Tectonic Plate Boundaries."""
    st.markdown("#### Tectonic Plate Boundaries")
    st.markdown("Simplified major plate boundaries showing divergent, convergent, and transform fault zones.")

    type_filter = st.radio("Boundary Type", ["All", "Divergent", "Convergent", "Transform"],
                           horizontal=True, key="volm_tp_type")
    filtered = PLATE_BOUNDARIES if type_filter == "All" else [p for p in PLATE_BOUNDARIES if p["type"] == type_filter]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Boundaries Shown", len(filtered))
    with c2:
        st.metric("Divergent", len([p for p in filtered if p["type"] == "Divergent"]))
    with c3:
        st.metric("Convergent", len([p for p in filtered if p["type"] == "Convergent"]))

    st.markdown(
        '<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.75rem;">'
        '<span style="color:#10b981;font-size:0.85rem;">--- Divergent (spreading)</span>'
        '<span style="color:#ef4444;font-size:0.85rem;">--- Convergent (subduction)</span>'
        '<span style="color:#f59e0b;font-size:0.85rem;">--- Transform (sliding)</span>'
        '</div>', unsafe_allow_html=True)

    m = _make_base_map()
    for p in filtered:
        folium.PolyLine(
            locations=p["coords"], color=p["color"], weight=3, opacity=0.85,
            tooltip=escape(f"{p['name']} ({p['type']})"),
            popup=folium.Popup(
                f"<b>{escape(p['name'])}</b><br><b>Type:</b> {escape(p['type'])}",
                max_width=250),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: boundary count by type
    fig, ax = _dark_fig(figsize=(8, 4))
    types_all = ["Divergent", "Convergent", "Transform"]
    counts = [len([p for p in PLATE_BOUNDARIES if p["type"] == t]) for t in types_all]
    colors = ["#10b981", "#ef4444", "#f59e0b"]
    ax.bar(types_all, counts, color=colors, edgecolor="#2a3550")
    ax.set_ylabel("Count")
    ax.set_title("Plate Boundary Types")
    fig.tight_layout()
    _fig_to_image(fig)

    rows = [{"name": p["name"], "type": p["type"], "points": len(p["coords"])} for p in filtered]
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "tectonic_boundaries.csv", f"Download {len(df)} Boundaries (CSV)", "tp_dl")


def _render_historic_eruptions():
    """Mode 5: Historic Eruptions."""
    st.markdown("#### Historic Eruptions")
    st.markdown("30+ of the most significant volcanic eruptions in human history, ranked by VEI and impact.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        min_vei = st.slider("Minimum VEI", 0, 8, 0, key="he_vei")
    with col_f2:
        min_year = st.slider("Minimum Year", -2000, 2025, -2000, key="he_year")

    filtered = [e for e in HISTORIC_ERUPTIONS if e["vei"] >= min_vei and e["year"] >= min_year]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Eruptions", len(filtered))
    with c2:
        st.metric("Max VEI", max((e["vei"] for e in filtered), default=0))
    with c3:
        total_deaths = sum(e["deaths"] for e in filtered)
        st.metric("Total Deaths", f"{total_deaths:,}")
    with c4:
        st.metric("VEI 7+", len([e for e in filtered if e["vei"] >= 7]))

    st.markdown(
        '<div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-bottom:0.75rem;">'
        '<span style="color:#10b981;font-size:0.8rem;">VEI 0-2</span>'
        '<span style="color:#f59e0b;font-size:0.8rem;">VEI 3-4</span>'
        '<span style="color:#ef4444;font-size:0.8rem;">VEI 5-6</span>'
        '<span style="color:#991b1b;font-size:0.8rem;">VEI 7-8</span>'
        '</div>', unsafe_allow_html=True)

    m = _make_base_map()
    for e in filtered:
        c = VEI_COLORS.get(e["vei"], "#06b6d4")
        r = 5 + e["vei"] * 1.5
        yr_str = f"{e['year']} AD" if e["year"] > 0 else f"{abs(e['year'])} BC"
        popup = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(e['name'])}</b><br>"
            f"<b>Year:</b> {yr_str}<br>"
            f"<b>VEI:</b> {e['vei']}<br>"
            f"<b>Deaths:</b> {e['deaths']:,}<br>"
            f"<b>Notes:</b> {escape(e['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[e["lat"], e["lon"]], radius=r,
            color=c, fill=True, fill_color=c, fill_opacity=0.8,
            popup=folium.Popup(popup, max_width=320),
            tooltip=escape(e["name"]),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: VEI distribution
    fig, ax = _dark_fig(figsize=(10, 5))
    vei_counts = {i: len([e for e in filtered if e["vei"] == i]) for i in range(9)}
    vei_vals = list(vei_counts.keys())
    vei_cnts = list(vei_counts.values())
    bar_colors = [VEI_COLORS.get(v, "#06b6d4") for v in vei_vals]
    ax.bar(vei_vals, vei_cnts, color=bar_colors, edgecolor="#2a3550")
    ax.set_xlabel("Volcanic Explosivity Index (VEI)")
    ax.set_ylabel("Number of Eruptions")
    ax.set_title("Historic Eruptions by VEI")
    ax.set_xticks(vei_vals)
    fig.tight_layout()
    _fig_to_image(fig)

    rows = []
    for e in filtered:
        yr_str = f"{e['year']} AD" if e["year"] > 0 else f"{abs(e['year'])} BC"
        rows.append({"name": e["name"], "year": yr_str, "vei": e["vei"],
                     "deaths": e["deaths"], "lat": e["lat"], "lon": e["lon"],
                     "notes": e["notes"]})
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "historic_eruptions.csv", f"Download {len(df)} Eruptions (CSV)", "he_dl")


def _render_volcanic_hotspots():
    """Mode 6: Volcanic Hotspots."""
    st.markdown("#### Volcanic Hotspots")
    st.markdown("Mantle plumes and hotspot tracks showing how tectonic plates drift over stationary magma sources.")

    status_filter = st.radio("Status", ["All", "Active", "Dormant"], horizontal=True, key="vh_status")
    filtered = VOLCANIC_HOTSPOTS if status_filter == "All" else [h for h in VOLCANIC_HOTSPOTS if h["status"] == status_filter]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Hotspots", len(filtered))
    with c2:
        st.metric("Active", len([h for h in filtered if h["status"] == "Active"]))
    with c3:
        st.metric("Dormant", len([h for h in filtered if h["status"] == "Dormant"]))

    m = _make_base_map()
    for h in filtered:
        c = "#ef4444" if h["status"] == "Active" else "#8b97b0"
        popup = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(h['name'])}</b><br>"
            f"<b>Status:</b> {escape(h['status'])}<br>"
            f"<b>Chain:</b> {escape(h['chain'])}<br>"
            f"<b>Notes:</b> {escape(h['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[h["lat"], h["lon"]], radius=10,
            color=c, fill=True, fill_color=c, fill_opacity=0.75,
            popup=folium.Popup(popup, max_width=320),
            tooltip=escape(h["name"]),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: hotspots by status
    fig, ax = _dark_fig(figsize=(8, 4))
    statuses = ["Active", "Dormant"]
    cnts = [len([h for h in VOLCANIC_HOTSPOTS if h["status"] == s]) for s in statuses]
    ax.bar(statuses, cnts, color=["#ef4444", "#8b97b0"], edgecolor="#2a3550")
    ax.set_ylabel("Count")
    ax.set_title("Volcanic Hotspots by Status")
    fig.tight_layout()
    _fig_to_image(fig)

    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "volcanic_hotspots.csv", f"Download {len(df)} Hotspots (CSV)", "vh_dl")


def _render_lava_flow_types():
    """Mode 7: Lava Flow Types (educational)."""
    st.markdown("#### Lava Flow Types")
    st.markdown("An educational overview of the major lava types, their properties, viscosity, temperature, and silica content.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Lava Types", len(LAVA_TYPES))
    with c2:
        st.metric("Highest SiO2", "70-77%")
    with c3:
        st.metric("Lowest SiO2", "<1% (Carbonatite)")

    m = _make_base_map()
    for lv in LAVA_TYPES:
        popup = (
            f"<div style='min-width:240px;'>"
            f"<b>{escape(lv['type'])}</b><br>"
            f"<b>Temperature:</b> {escape(lv['temp_c'])} C<br>"
            f"<b>Viscosity:</b> {escape(lv['viscosity'])}<br>"
            f"<b>Speed:</b> {escape(lv['speed_kmh'])} km/h<br>"
            f"<b>SiO2:</b> {escape(lv['sio2_pct'])}%<br>"
            f"<b>Example:</b> {escape(lv['example_loc'])}<br>"
            f"<b>Description:</b> {escape(lv['description'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[lv["lat"], lv["lon"]], radius=10,
            color=lv["color"], fill=True, fill_color=lv["color"], fill_opacity=0.8,
            popup=folium.Popup(popup, max_width=340),
            tooltip=escape(lv["type"]),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: viscosity comparison
    fig, ax = _dark_fig(figsize=(10, 5))
    visc_order = {"Extremely Low": 1, "Very Low": 2, "Low": 3, "Low-Medium": 4,
                  "Variable": 5, "High": 6, "Very High": 7, "Extremely High": 8}
    sorted_lava = sorted(LAVA_TYPES, key=lambda x: visc_order.get(x["viscosity"], 5))
    names = [lv["type"] for lv in sorted_lava]
    visc_vals = [visc_order.get(lv["viscosity"], 5) for lv in sorted_lava]
    bar_colors = [lv["color"] for lv in sorted_lava]
    ax.barh(names, visc_vals, color=bar_colors, edgecolor="#2a3550")
    ax.set_xlabel("Viscosity (relative scale)")
    ax.set_title("Lava Types by Viscosity")
    ax.set_xticks(range(1, 9))
    ax.set_xticklabels(["Ext Low", "V Low", "Low", "Low-Med", "Var", "High", "V High", "Ext High"],
                       fontsize=7, color="#8b97b0")
    ax.invert_yaxis()
    fig.tight_layout()
    _fig_to_image(fig)

    df = pd.DataFrame(LAVA_TYPES)
    col_order = ["type", "temp_c", "viscosity", "speed_kmh", "sio2_pct", "example_loc", "description"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "lava_types.csv", f"Download {len(df)} Lava Types (CSV)", "lv_dl")


def _render_volcanic_islands():
    """Mode 8: Volcanic Islands."""
    st.markdown("#### Volcanic Islands")
    st.markdown("25+ notable volcanic islands with area, peak elevation, and eruption status.")

    active_filter = st.radio("Activity", ["All", "Active", "Inactive"], horizontal=True, key="vi_active")
    if active_filter == "Active":
        filtered = [v for v in VOLCANIC_ISLANDS if v["active"]]
    elif active_filter == "Inactive":
        filtered = [v for v in VOLCANIC_ISLANDS if not v["active"]]
    else:
        filtered = VOLCANIC_ISLANDS

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Islands", len(filtered))
    with c2:
        st.metric("Active", len([v for v in filtered if v["active"]]))
    with c3:
        st.metric("Largest", f"{max((v['area_km2'] for v in filtered), default=0):,} km2")
    with c4:
        st.metric("Highest", f"{max((v['highest_m'] for v in filtered), default=0):,} m")

    m = _make_base_map()
    cluster = MarkerCluster(name="Volcanic Islands")
    for v in filtered:
        c = "#ef4444" if v["active"] else "#8b97b0"
        popup = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(v['name'])}</b><br>"
            f"<b>Country:</b> {escape(v['country'])}<br>"
            f"<b>Area:</b> {v['area_km2']:,} km2<br>"
            f"<b>Highest Point:</b> {v['highest_m']:,} m<br>"
            f"<b>Active:</b> {'Yes' if v['active'] else 'No'}<br>"
            f"<b>Notes:</b> {escape(v['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[v["lat"], v["lon"]], radius=8,
            color=c, fill=True, fill_color=c, fill_opacity=0.8,
            popup=folium.Popup(popup, max_width=320),
            tooltip=escape(v["name"]),
        ).add_to(cluster)
    cluster.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: top 15 by area
    fig, ax = _dark_fig(figsize=(10, 5))
    top = sorted(filtered, key=lambda v: v["area_km2"], reverse=True)[:15]
    names = [v["name"][:20] for v in top]
    areas = [v["area_km2"] for v in top]
    bar_colors = ["#ef4444" if v["active"] else "#8b97b0" for v in top]
    ax.barh(names, areas, color=bar_colors, edgecolor="#2a3550")
    ax.set_xlabel("Area (km2)")
    ax.set_title("Volcanic Islands by Area (Top 15)")
    ax.invert_yaxis()
    fig.tight_layout()
    _fig_to_image(fig)

    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "volcanic_islands.csv", f"Download {len(df)} Islands (CSV)", "vi_dl")


def _render_geothermal_areas():
    """Mode 9: Geothermal Areas via Overpass API."""
    st.markdown("#### Geothermal Areas")
    st.markdown("Search for geysers and hot springs worldwide using OpenStreetMap data (Overpass API).")

    region = st.selectbox("Preset Region", list(GEOTHERMAL_PRESETS.keys()), key="geo_region")
    custom_lat, custom_lon, custom_radius = 64.96, -19.02, 200

    if region != "Custom Area":
        preset = GEOTHERMAL_PRESETS[region]
        if preset:
            custom_lat, custom_lon, custom_radius = preset["lat"], preset["lon"], preset["radius"]
    else:
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            custom_lat = st.number_input("Latitude", value=64.96, key="geo_lat", format="%.2f")
        with cc2:
            custom_lon = st.number_input("Longitude", value=-19.02, key="geo_lon", format="%.2f")
        with cc3:
            custom_radius = st.number_input("Radius (km)", value=200, min_value=10, max_value=500, key="geo_rad")

    do_search = st.button("Search Geothermal Features", key="geo_search")

    if do_search:
        with st.spinner("Querying Overpass API for geysers and hot springs..."):
            data = _overpass_geothermal(custom_lat, custom_lon, custom_radius)

        if data and "_error" in data:
            st.warning(f"Overpass error: {data['_error']}")
            return
        if not data:
            st.warning("No response from Overpass API.")
            return

        elements = data.get("elements", [])
        if not elements:
            st.info("No geothermal features found in this area. Try a different region or larger radius.")
            return

        geysers = [e for e in elements if e.get("tags", {}).get("natural") == "geyser"]
        hot_springs = [e for e in elements if e.get("tags", {}).get("natural") == "hot_spring"]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Features", len(elements))
        with c2:
            st.metric("Geysers", len(geysers))
        with c3:
            st.metric("Hot Springs", len(hot_springs))

        m = _make_base_map(lat=custom_lat, lon=custom_lon, zoom=7)
        rows = []
        for el in elements:
            lat_e = el.get("lat") or el.get("center", {}).get("lat")
            lon_e = el.get("lon") or el.get("center", {}).get("lon")
            if lat_e is None or lon_e is None:
                continue
            tags = el.get("tags", {})
            name = tags.get("name", "Unnamed")
            feat_type = tags.get("natural", "unknown")
            c = "#06b6d4" if feat_type == "geyser" else "#f59e0b"
            icon = "tint" if feat_type == "geyser" else "fire"
            popup = (
                f"<div style='min-width:180px;'>"
                f"<b>{escape(name)}</b><br>"
                f"<b>Type:</b> {escape(feat_type)}<br>"
            )
            for k in ["description", "ele", "wikipedia", "website"]:
                if k in tags:
                    popup += f"<b>{escape(k.title())}:</b> {escape(tags[k])}<br>"
            popup += "</div>"
            folium.CircleMarker(
                location=[lat_e, lon_e], radius=7,
                color=c, fill=True, fill_color=c, fill_opacity=0.8,
                popup=folium.Popup(popup, max_width=280),
                tooltip=escape(name),
            ).add_to(m)
            rows.append({"name": name, "type": feat_type, "lat": lat_e, "lon": lon_e})

        folium.LayerControl().add_to(m)
        _render_map(m)

        # Chart: geyser vs hot spring
        fig, ax = _dark_fig(figsize=(6, 4))
        labels = ["Geysers", "Hot Springs"]
        counts = [len(geysers), len(hot_springs)]
        colors = ["#06b6d4", "#f59e0b"]
        ax.bar(labels, counts, color=colors, edgecolor="#2a3550")
        ax.set_ylabel("Count")
        ax.set_title("Geothermal Feature Types")
        fig.tight_layout()
        _fig_to_image(fig)

        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
        _csv_download(df, "geothermal_features.csv", f"Download {len(df)} Features (CSV)", "geo_dl")
    else:
        st.info("Select a region and click Search to find geothermal features.")


def _render_hazard_zones():
    """Mode 10: Volcanic Hazard Zones."""
    st.markdown("#### Volcanic Hazard Zones")
    st.markdown("Major cities located dangerously close to active volcanoes, with population and risk assessment.")

    risk_filter = st.radio("Risk Level", ["All", "Extreme", "Very High", "High", "Moderate"],
                           horizontal=True, key="hz_risk")
    filtered = HAZARD_ZONES if risk_filter == "All" else [h for h in HAZARD_ZONES if h["risk"] == risk_filter]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Cities at Risk", len(filtered))
    with c2:
        total_pop = sum(h["population"] for h in filtered)
        st.metric("Total Population", f"{total_pop / 1e6:.1f}M")
    with c3:
        st.metric("Closest", f"{min((h['distance_km'] for h in filtered), default=0)} km")
    with c4:
        st.metric("Extreme Risk", len([h for h in filtered if h["risk"] == "Extreme"]))

    risk_colors = {"Extreme": "#dc2626", "Very High": "#ef4444", "High": "#f97316", "Moderate": "#f59e0b"}

    m = _make_base_map()
    for h in filtered:
        c = risk_colors.get(h["risk"], "#06b6d4")
        # City marker
        popup = (
            f"<div style='min-width:240px;'>"
            f"<b>{escape(h['city'])}, {escape(h['country'])}</b><br>"
            f"<b>Population:</b> {h['population']:,}<br>"
            f"<b>Nearest Volcano:</b> {escape(h['volcano'])}<br>"
            f"<b>Distance:</b> {h['distance_km']} km<br>"
            f"<b>Risk Level:</b> {escape(h['risk'])}<br>"
            f"<b>Notes:</b> {escape(h['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[h["lat"], h["lon"]], radius=max(5, h["population"] / 1e6),
            color=c, fill=True, fill_color=c, fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=320),
            tooltip=escape(f"{h['city']} ({h['risk']})"),
        ).add_to(m)
        # Volcano marker (triangle via DivIcon)
        folium.CircleMarker(
            location=[h["vlat"], h["vlon"]], radius=5,
            color="#e8ecf4", fill=True, fill_color="#e8ecf4", fill_opacity=0.9,
            tooltip=escape(h["volcano"]),
        ).add_to(m)
        # Line from city to volcano
        folium.PolyLine(
            locations=[[h["lat"], h["lon"]], [h["vlat"], h["vlon"]]],
            color=c, weight=1, opacity=0.5, dash_array="5 5",
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Chart: top 15 cities by population at risk
    fig, ax = _dark_fig(figsize=(10, 5))
    top = sorted(filtered, key=lambda h: h["population"], reverse=True)[:15]
    names = [f"{h['city']}" for h in top]
    pops = [h["population"] / 1e6 for h in top]
    bar_colors = [risk_colors.get(h["risk"], "#06b6d4") for h in top]
    ax.barh(names, pops, color=bar_colors, edgecolor="#2a3550")
    ax.set_xlabel("Population (millions)")
    ax.set_title("Cities Near Active Volcanoes by Population")
    ax.invert_yaxis()
    fig.tight_layout()
    _fig_to_image(fig)

    df = pd.DataFrame(filtered)
    col_order = ["city", "country", "population", "volcano", "distance_km", "risk", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "volcanic_hazard_zones.csv", f"Download {len(df)} Hazard Zones (CSV)", "hz_dl")


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_volcano_maps_tab():
    """Main entry point for the Volcanology Explorer tab."""
    st.markdown(
        '<div class="tab-header red">'
        '<h4>\U0001f30b Volcanology Explorer</h4>'
        '<p>Active volcanoes, eruption history, tectonic plates &amp; volcanic hazards</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio("Select Mode", MAP_MODES, horizontal=True, key="volcano_mode")

    st.markdown("---")

    if mode == "Active Volcanoes":
        _render_active_volcanoes()
    elif mode == "Ring of Fire":
        _render_ring_of_fire()
    elif mode == "Supervolcanoes":
        _render_supervolcanoes()
    elif mode == "Tectonic Plate Boundaries":
        _render_tectonic_plates()
    elif mode == "Historic Eruptions":
        _render_historic_eruptions()
    elif mode == "Volcanic Hotspots":
        _render_volcanic_hotspots()
    elif mode == "Lava Flow Types":
        _render_lava_flow_types()
    elif mode == "Volcanic Islands":
        _render_volcanic_islands()
    elif mode == "Geothermal Areas":
        _render_geothermal_areas()
    elif mode == "Volcanic Hazard Zones":
        _render_hazard_zones()
