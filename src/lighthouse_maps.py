# -*- coding: utf-8 -*-
"""
Lighthouses & Beacons of the World module for TerraScout AI.
Provides 10 thematic lighthouse map modes covering famous lighthouses,
ancient beacons, regional exploration, tallest structures, haunted legends,
architectural styles, decommissioned ruins, remote towers, keeper stories,
and modern navigation systems.

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
    "World's Most Famous Lighthouses",
    "Ancient Lighthouses",
    "Lighthouses by Country",
    "Tallest Lighthouses",
    "Haunted Lighthouses",
    "Lighthouse Architecture",
    "Decommissioned & Ruins",
    "Remote & Extreme Lighthouses",
    "Lighthouse Keepers' Stories",
    "Modern Navigation",
]

# =====================================================================
# 1. WORLD'S MOST FAMOUS LIGHTHOUSES (Top 50)
# =====================================================================
FAMOUS_LIGHTHOUSES = [
    {"name": "Tower of Hercules", "lat": 43.3861, "lon": -8.4064, "country": "Spain", "year": "2nd c. AD", "height_m": 55, "range_nm": 23, "photo_url": "", "notes": "Oldest working Roman lighthouse, UNESCO World Heritage Site since 2009"},
    {"name": "Eddystone Lighthouse", "lat": 50.1088, "lon": -4.1559, "country": "UK", "year": "1698", "height_m": 41, "range_nm": 17, "photo_url": "", "notes": "Four successive towers built on treacherous reef; Smeaton's tower relocated to Plymouth Hoe"},
    {"name": "Portland Head Light", "lat": 43.6231, "lon": -70.2078, "country": "USA", "year": "1791", "height_m": 24, "range_nm": 15, "photo_url": "", "notes": "Oldest lighthouse in Maine, commissioned by George Washington"},
    {"name": "Cape Hatteras Lighthouse", "lat": 35.2505, "lon": -75.5288, "country": "USA", "year": "1870", "height_m": 64, "range_nm": 20, "photo_url": "", "notes": "Tallest brick lighthouse in the US; famously relocated 870m inland in 1999"},
    {"name": "Boston Light", "lat": 42.3278, "lon": -70.8903, "country": "USA", "year": "1716", "height_m": 27, "range_nm": 16, "photo_url": "", "notes": "First lighthouse built in what became the United States; last to be automated (1998)"},
    {"name": "Bell Rock Lighthouse", "lat": 56.4341, "lon": -2.3869, "country": "UK", "year": "1811", "height_m": 35, "range_nm": 18, "photo_url": "", "notes": "Oldest surviving sea-washed lighthouse, Robert Stevenson's engineering marvel"},
    {"name": "Fastnet Rock Lighthouse", "lat": 51.3833, "lon": -9.6000, "country": "Ireland", "year": "1854", "height_m": 49, "range_nm": 18, "photo_url": "", "notes": "Known as the Teardrop of Ireland, last sight of emigrants heading to America"},
    {"name": "Bishop Rock Lighthouse", "lat": 49.8727, "lon": -6.4444, "country": "UK", "year": "1858", "height_m": 44, "range_nm": 20, "photo_url": "", "notes": "Built on smallest island with a building (Guinness record); marks western Scilly Isles"},
    {"name": "Phare de Cordouan", "lat": 45.5858, "lon": -1.1717, "country": "France", "year": "1611", "height_m": 68, "range_nm": 22, "photo_url": "", "notes": "The Versailles of the Sea; oldest lighthouse in France; UNESCO World Heritage 2021"},
    {"name": "La Jument Lighthouse", "lat": 48.4228, "lon": -5.1311, "country": "France", "year": "1911", "height_m": 47, "range_nm": 22, "photo_url": "", "notes": "Famous photograph by Jean Guichard of keeper during 1989 storm off Brittany"},
    {"name": "Peggy's Point Lighthouse", "lat": 44.4917, "lon": -63.9181, "country": "Canada", "year": "1915", "height_m": 15, "range_nm": 12, "photo_url": "", "notes": "Most photographed lighthouse in Canada; icon of Nova Scotia"},
    {"name": "Cape Byron Lighthouse", "lat": -28.6356, "lon": 153.6386, "country": "Australia", "year": "1901", "height_m": 22, "range_nm": 25, "photo_url": "", "notes": "Easternmost point of the Australian mainland; heritage listed"},
    {"name": "Lanterna di Genova", "lat": 44.4036, "lon": 8.9018, "country": "Italy", "year": "1128", "height_m": 77, "range_nm": 25, "photo_url": "", "notes": "Symbol of Genoa, oldest surviving lighthouse in the Mediterranean region"},
    {"name": "Hook Head Lighthouse", "lat": 52.1239, "lon": -6.9292, "country": "Ireland", "year": "1172", "height_m": 35, "range_nm": 23, "photo_url": "", "notes": "One of the oldest operational lighthouses in the world; Norman tower"},
    {"name": "Cape Agulhas Lighthouse", "lat": -34.8317, "lon": 20.0106, "country": "South Africa", "year": "1849", "height_m": 27, "range_nm": 19, "photo_url": "", "notes": "Southernmost tip of Africa where Indian and Atlantic oceans meet"},
    {"name": "Lindau Lighthouse", "lat": 47.5436, "lon": 9.6843, "country": "Germany", "year": "1856", "height_m": 33, "range_nm": 10, "photo_url": "", "notes": "Southernmost lighthouse in Germany, on Lake Constance (Bodensee)"},
    {"name": "Kjeungskjaer Lighthouse", "lat": 63.8494, "lon": 10.0000, "country": "Norway", "year": "1880", "height_m": 21, "range_nm": 13, "photo_url": "", "notes": "Iconic red octagonal lighthouse perched on a tiny islet in Trondheimsfjorden"},
    {"name": "Cape Leeuwin Lighthouse", "lat": -34.3725, "lon": 115.1358, "country": "Australia", "year": "1895", "height_m": 39, "range_nm": 20, "photo_url": "", "notes": "Southwestern tip of Australia; meeting point of Indian and Southern oceans"},
    {"name": "Point Reyes Lighthouse", "lat": 37.9958, "lon": -123.0228, "country": "USA", "year": "1870", "height_m": 11, "range_nm": 24, "photo_url": "", "notes": "One of the windiest and foggiest points on the US Pacific Coast"},
    {"name": "Gibbs Hill Lighthouse", "lat": 32.2494, "lon": -64.8356, "country": "Bermuda", "year": "1846", "height_m": 36, "range_nm": 26, "photo_url": "", "notes": "One of the oldest cast-iron lighthouses in the world"},
    {"name": "St. Augustine Lighthouse", "lat": 29.8856, "lon": -81.2886, "country": "USA", "year": "1874", "height_m": 50, "range_nm": 19, "photo_url": "", "notes": "Oldest permanent aid to navigation in the US; reported haunted"},
    {"name": "Pigeon Point Lighthouse", "lat": 37.1828, "lon": -122.3939, "country": "USA", "year": "1872", "height_m": 35, "range_nm": 18, "photo_url": "", "notes": "One of the tallest lighthouses on the US West Coast; hostel on grounds"},
    {"name": "Europa Point Lighthouse", "lat": 36.1100, "lon": -5.3450, "country": "Gibraltar", "year": "1841", "height_m": 20, "range_nm": 19, "photo_url": "", "notes": "Southern tip of Gibraltar marking the entrance to the Strait"},
    {"name": "Bengtskars Lighthouse", "lat": 59.7594, "lon": 22.5017, "country": "Finland", "year": "1906", "height_m": 52, "range_nm": 18, "photo_url": "", "notes": "Tallest lighthouse in Scandinavia; survived WWII Soviet bombing"},
    {"name": "Cape Palliser Lighthouse", "lat": -41.6092, "lon": 175.2883, "country": "New Zealand", "year": "1897", "height_m": 18, "range_nm": 16, "photo_url": "", "notes": "Southernmost lighthouse on North Island; 258 steps to reach"},
    {"name": "Makapuu Point Lighthouse", "lat": 21.3103, "lon": -157.6472, "country": "USA (Hawaii)", "year": "1909", "height_m": 14, "range_nm": 28, "photo_url": "", "notes": "Largest hyper-radial lens in the US; spectacular coastal trail"},
    {"name": "Cape Race Lighthouse", "lat": 46.6569, "lon": -53.0731, "country": "Canada", "year": "1856", "height_m": 24, "range_nm": 16, "photo_url": "", "notes": "Received the RMS Titanic distress signal in April 1912"},
    {"name": "Faro de Finisterre", "lat": 42.8828, "lon": -9.2722, "country": "Spain", "year": "1853", "height_m": 17, "range_nm": 23, "photo_url": "", "notes": "End of the Camino de Santiago; on the deadly Costa da Morte"},
    {"name": "South Stack Lighthouse", "lat": 53.3058, "lon": -4.6992, "country": "UK (Wales)", "year": "1809", "height_m": 28, "range_nm": 20, "photo_url": "", "notes": "Built on dramatic cliff island off Anglesey; 400 steps descent"},
    {"name": "Beachy Head Lighthouse", "lat": 50.7364, "lon": 0.2433, "country": "UK", "year": "1902", "height_m": 43, "range_nm": 16, "photo_url": "", "notes": "Iconic red-and-white stripes at base of famous chalk cliffs"},
    {"name": "Slettnes Lighthouse", "lat": 71.0892, "lon": 28.2108, "country": "Norway", "year": "1905", "height_m": 15, "range_nm": 18, "photo_url": "", "notes": "Northernmost mainland lighthouse in the world; 71 degrees N"},
    {"name": "Cape Point Lighthouse", "lat": -34.3564, "lon": 18.4972, "country": "South Africa", "year": "1860", "height_m": 87, "range_nm": 34, "photo_url": "", "notes": "One of the most powerful lights in the world; near Cape of Good Hope"},
    {"name": "Les Eclaireurs Lighthouse", "lat": -54.8775, "lon": -68.0583, "country": "Argentina", "year": "1920", "height_m": 11, "range_nm": 7, "photo_url": "", "notes": "Often called End of the World lighthouse; Beagle Channel, Ushuaia"},
    {"name": "Roter Sand Lighthouse", "lat": 53.8569, "lon": 8.0847, "country": "Germany", "year": "1885", "height_m": 28, "range_nm": 12, "photo_url": "", "notes": "First offshore lighthouse built on open sea in Germany; now a museum/hotel"},
    {"name": "Jeddah Light", "lat": 21.4967, "lon": 39.1522, "country": "Saudi Arabia", "year": "1990", "height_m": 133, "range_nm": 25, "photo_url": "", "notes": "Tallest lighthouse in the world at 133 meters"},
    {"name": "Yokohama Marine Tower", "lat": 35.4433, "lon": 139.6522, "country": "Japan", "year": "1961", "height_m": 106, "range_nm": 20, "photo_url": "", "notes": "Once tallest lighthouse in the world; iconic Yokohama landmark"},
    {"name": "Ile Vierge Lighthouse", "lat": 48.6381, "lon": -4.5675, "country": "France", "year": "1902", "height_m": 82.5, "range_nm": 27, "photo_url": "", "notes": "Tallest traditional stone lighthouse in the world; 365 steps"},
    {"name": "Morro Castle Lighthouse", "lat": 23.1502, "lon": -82.3575, "country": "Cuba", "year": "1845", "height_m": 25, "range_nm": 18, "photo_url": "", "notes": "Built atop the famous Morro fortress guarding Havana harbour"},
    {"name": "Cape Bonavista Lighthouse", "lat": 48.6983, "lon": -53.0833, "country": "Canada", "year": "1843", "height_m": 15, "range_nm": 12, "photo_url": "", "notes": "Near John Cabot's 1497 landfall site in Newfoundland"},
    {"name": "Split Point Lighthouse", "lat": -38.4728, "lon": 144.0594, "country": "Australia", "year": "1891", "height_m": 34, "range_nm": 15, "photo_url": "", "notes": "Known as the White Queen; featured in TV series Round the Twist"},
    {"name": "Cabo da Roca Lighthouse", "lat": 38.7808, "lon": -9.4991, "country": "Portugal", "year": "1772", "height_m": 22, "range_nm": 26, "photo_url": "", "notes": "Westernmost point of continental Europe; dramatic clifftop setting"},
    {"name": "Lighthouse of Madonetta", "lat": 41.3828, "lon": 9.1539, "country": "France (Corsica)", "year": "1854", "height_m": 16, "range_nm": 14, "photo_url": "", "notes": "Guards the entrance to Bonifacio; perched on chalk cliffs"},
    {"name": "Vieste Lighthouse", "lat": 41.8856, "lon": 16.1839, "country": "Italy", "year": "1867", "height_m": 10, "range_nm": 15, "photo_url": "", "notes": "On the island of Santa Eufemia off the Gargano coast; Adriatic"},
    {"name": "Bass Rock Lighthouse", "lat": 56.0778, "lon": -2.6411, "country": "UK (Scotland)", "year": "1902", "height_m": 20, "range_nm": 10, "photo_url": "", "notes": "On volcanic rock island; world's largest Northern gannet colony"},
    {"name": "Smeaton's Tower (relocated)", "lat": 50.3654, "lon": -4.1425, "country": "UK", "year": "1759", "height_m": 22, "range_nm": 0, "photo_url": "", "notes": "Pioneered use of hydraulic lime in marine construction; now on Plymouth Hoe"},
    {"name": "Lindesnes Lighthouse", "lat": 57.9828, "lon": 7.0486, "country": "Norway", "year": "1656", "height_m": 16, "range_nm": 17, "photo_url": "", "notes": "Southernmost point of Norway; first lighthouse in the country"},
    {"name": "Cabo de Sao Vicente Lighthouse", "lat": 37.0228, "lon": -8.9972, "country": "Portugal", "year": "1846", "height_m": 22, "range_nm": 32, "photo_url": "", "notes": "Southwestern tip of Portugal; one of Europe's most powerful lights"},
    {"name": "Fanad Head Lighthouse", "lat": 55.2756, "lon": -7.6339, "country": "Ireland", "year": "1817", "height_m": 22, "range_nm": 18, "photo_url": "", "notes": "Named one of the most beautiful lighthouses in the world; Donegal"},
    {"name": "Cape Otway Lighthouse", "lat": -38.8556, "lon": 143.5117, "country": "Australia", "year": "1848", "height_m": 20, "range_nm": 17, "photo_url": "", "notes": "Oldest surviving lighthouse on mainland Australia; Great Ocean Road"},
    {"name": "Happisburgh Lighthouse", "lat": 52.8250, "lon": 1.5333, "country": "UK", "year": "1791", "height_m": 26, "range_nm": 14, "photo_url": "", "notes": "Oldest working lighthouse in East Anglia; threatened by coastal erosion"},
]

# =====================================================================
# 2. ANCIENT LIGHTHOUSES
# =====================================================================
ANCIENT_LIGHTHOUSES = [
    {"name": "Pharos of Alexandria", "lat": 31.2139, "lon": 29.8856, "country": "Egypt", "year": "c. 280 BC", "height_m": 100, "status": "Destroyed (earthquakes 956-1480 AD)", "notes": "One of the Seven Wonders of the Ancient World; guided ships into Alexandria harbour for over 1,500 years; fire and mirrors at summit; remains found underwater by Franck Goddio"},
    {"name": "Tower of Hercules", "lat": 43.3861, "lon": -8.4064, "country": "Spain", "year": "2nd century AD", "height_m": 55, "status": "Active (renovated 1791)", "notes": "Built by the Romans as Brigantium; oldest working lighthouse in continuous use; UNESCO 2009; dedicated to Mars by architect Gaius Sevius Lupus"},
    {"name": "Lanterna di Genova", "lat": 44.4036, "lon": 8.9018, "country": "Italy", "year": "1128 (current 1543)", "height_m": 77, "status": "Active", "notes": "First documented in 1128; current structure dates to 1543; symbol of Genoa; Antonio Colombo (uncle of Christopher Columbus) was a keeper"},
    {"name": "Hook Head Lighthouse", "lat": 52.1239, "lon": -6.9292, "country": "Ireland", "year": "c. 1172", "height_m": 35, "status": "Active", "notes": "Monks lit fires here from the 5th century; Norman tower built by William Marshal c. 1172; one of the oldest operational lighthouses in the world"},
    {"name": "Patara Lighthouse", "lat": 36.2633, "lon": 29.3136, "country": "Turkey", "year": "c. 60 AD", "height_m": 26, "status": "Ruins", "notes": "Roman lighthouse at the Lycian port of Patara; partially restored; one of the few surviving Roman lighthouses"},
    {"name": "Dover Roman Lighthouse", "lat": 51.1281, "lon": 1.3256, "country": "UK", "year": "c. 50 AD", "height_m": 24, "status": "Ruins (partial)", "notes": "Roman pharos within Dover Castle; one of only three surviving Roman lighthouses; guided ships across the English Channel"},
    {"name": "Boulogne Roman Lighthouse (Tour d'Ordre)", "lat": 50.7264, "lon": 1.6139, "country": "France", "year": "39 AD", "height_m": 60, "status": "Destroyed (1644)", "notes": "Built by Emperor Caligula; octagonal Roman pharos that guided ships across the Channel; collapsed from cliff erosion in 1644"},
    {"name": "La Coruna Roman Lighthouse", "lat": 43.3861, "lon": -8.4064, "country": "Spain", "year": "2nd century AD", "height_m": 34, "status": "Active (as Tower of Hercules)", "notes": "Original Roman core still exists inside the 18th-century exterior; legend says Hercules built it after slaying the giant Geryon"},
    {"name": "Leptis Magna Lighthouse", "lat": 32.6375, "lon": 14.2925, "country": "Libya", "year": "c. 200 AD", "height_m": 20, "status": "Ruins", "notes": "Part of the great Roman port city; guided ships into one of the finest harbours in North Africa"},
    {"name": "Portus Lighthouse (Ostia)", "lat": 41.7789, "lon": 12.2556, "country": "Italy", "year": "c. 50 AD", "height_m": 30, "status": "Destroyed", "notes": "Built by Emperor Claudius at the main port of Rome; modeled on the Pharos of Alexandria; depicted on Roman coins"},
    {"name": "Brigantium Watchtower", "lat": 43.3700, "lon": -8.3950, "country": "Spain", "year": "1st century BC", "height_m": 15, "status": "Destroyed", "notes": "Celtic-Roman watchtower that predated the Tower of Hercules; fire signals warned of approaching fleets"},
    {"name": "Dubris (Dover) West Pharos", "lat": 51.1264, "lon": 1.3189, "country": "UK", "year": "c. 50 AD", "height_m": 12, "status": "Foundations only", "notes": "Western pair to the surviving Dover Castle pharos; two lighthouses guided ships into the Roman port of Dubris"},
    {"name": "Corunna Beacon (pre-Roman)", "lat": 43.3850, "lon": -8.4075, "country": "Spain", "year": "c. 500 BC", "height_m": 8, "status": "Destroyed", "notes": "Phoenician or Celtic fire beacon that preceded the Roman Tower of Hercules; earliest known navigation aid in Iberia"},
    {"name": "Messina Lighthouse", "lat": 38.1978, "lon": 15.5603, "country": "Italy", "year": "c. 42 AD", "height_m": 18, "status": "Destroyed (earthquakes)", "notes": "Roman lighthouse guiding ships through the Strait of Messina between Scylla and Charybdis; rebuilt multiple times"},
    {"name": "Chrysopolis Lighthouse", "lat": 41.0236, "lon": 29.0158, "country": "Turkey", "year": "c. 330 AD", "height_m": 25, "status": "Destroyed", "notes": "Byzantine-era lighthouse on the Asian shore of the Bosphorus near Uskudar; guided ships entering Constantinople"},
]

# =====================================================================
# 3. LIGHTHOUSES BY COUNTRY (Overpass search regions)
# =====================================================================
COUNTRY_REGIONS = {
    "Custom Area": None,
    "United Kingdom": {"lat": 54.0, "lon": -2.0, "radius": 400},
    "Ireland": {"lat": 53.5, "lon": -8.0, "radius": 250},
    "France": {"lat": 47.0, "lon": 2.0, "radius": 400},
    "Spain & Portugal": {"lat": 40.0, "lon": -4.0, "radius": 400},
    "Italy": {"lat": 42.0, "lon": 13.0, "radius": 400},
    "Scandinavia": {"lat": 62.0, "lon": 12.0, "radius": 500},
    "Germany & Netherlands": {"lat": 53.0, "lon": 9.0, "radius": 300},
    "Greece & Turkey": {"lat": 38.5, "lon": 27.0, "radius": 400},
    "US East Coast": {"lat": 38.0, "lon": -75.0, "radius": 500},
    "US West Coast": {"lat": 40.0, "lon": -124.0, "radius": 400},
    "Eastern Canada": {"lat": 47.0, "lon": -62.0, "radius": 400},
    "Australia": {"lat": -33.0, "lon": 150.0, "radius": 500},
    "New Zealand": {"lat": -41.0, "lon": 175.0, "radius": 300},
    "Japan": {"lat": 35.0, "lon": 136.0, "radius": 400},
    "Caribbean": {"lat": 18.0, "lon": -70.0, "radius": 500},
    "South Africa": {"lat": -33.0, "lon": 25.0, "radius": 400},
    "Baltic States": {"lat": 58.0, "lon": 24.0, "radius": 300},
    "Croatia & Montenegro": {"lat": 43.5, "lon": 16.0, "radius": 200},
    "Brazil": {"lat": -15.0, "lon": -40.0, "radius": 500},
}

# =====================================================================
# 4. TALLEST LIGHTHOUSES
# =====================================================================
TALLEST_LIGHTHOUSES = [
    {"name": "Jeddah Light", "lat": 21.4967, "lon": 39.1522, "country": "Saudi Arabia", "year": 1990, "height_m": 133, "range_nm": 25, "notes": "Tallest lighthouse in the world; concrete structure at end of outer pier"},
    {"name": "Yokohama Marine Tower", "lat": 35.4433, "lon": 139.6522, "country": "Japan", "year": 1961, "height_m": 106, "range_nm": 20, "notes": "Steel lattice tower; was tallest lighthouse 1961-1990; now observation tower"},
    {"name": "Ile Vierge Lighthouse", "lat": 48.6381, "lon": -4.5675, "country": "France", "year": 1902, "height_m": 82.5, "range_nm": 27, "notes": "Tallest traditional stone lighthouse in the world; 365 steps; Finistere coast"},
    {"name": "Lanterna di Genova", "lat": 44.4036, "lon": 8.9018, "country": "Italy", "year": 1543, "height_m": 77, "range_nm": 25, "notes": "Tallest lighthouse in Italy; medieval origins; symbol of Genoa"},
    {"name": "Phare de Gatteville", "lat": 49.6942, "lon": -1.2653, "country": "France", "year": 1835, "height_m": 75, "range_nm": 29, "notes": "One of tallest in France; 365 steps; Barfleur, Normandy"},
    {"name": "Phare d'Eckmuehl", "lat": 47.7961, "lon": -4.3725, "country": "France", "year": 1897, "height_m": 65, "range_nm": 24, "notes": "Funded by Marquise de Blocqueville as memorial to father; Penmarc'h, Brittany"},
    {"name": "Cape Hatteras Lighthouse", "lat": 35.2505, "lon": -75.5288, "country": "USA", "year": 1870, "height_m": 64, "range_nm": 20, "notes": "Tallest brick lighthouse in USA; black-and-white spiral pattern; relocated 1999"},
    {"name": "Phare de Cordouan", "lat": 45.5858, "lon": -1.1717, "country": "France", "year": 1611, "height_m": 68, "range_nm": 22, "notes": "The Versailles of the Sea; ornate Renaissance interior; UNESCO 2021"},
    {"name": "Absecon Lighthouse", "lat": 39.3664, "lon": -74.4156, "country": "USA", "year": 1857, "height_m": 52, "range_nm": 19, "notes": "Tallest lighthouse in New Jersey; Atlantic City landmark; designed by George Meade"},
    {"name": "Bengtskars Lighthouse", "lat": 59.7594, "lon": 22.5017, "country": "Finland", "year": 1906, "height_m": 52, "range_nm": 18, "notes": "Tallest in Scandinavia; survived Soviet bombing in WWII; granite construction"},
    {"name": "Punta Penna Lighthouse", "lat": 42.1703, "lon": 14.7089, "country": "Italy", "year": 1906, "height_m": 70, "range_nm": 25, "notes": "Second tallest in Italy; white octagonal tower on Adriatic coast near Vasto"},
    {"name": "St. Augustine Lighthouse", "lat": 29.8856, "lon": -81.2886, "country": "USA", "year": 1874, "height_m": 50, "range_nm": 19, "notes": "Black-and-white spiral; 219 steps; claimed to be haunted"},
    {"name": "Phare du Stiff", "lat": 48.4742, "lon": -5.0592, "country": "France", "year": 1700, "height_m": 49, "range_nm": 24, "notes": "On Ile d'Ouessant; Vauban-designed; one of oldest in Brittany"},
    {"name": "Fastnet Rock Lighthouse", "lat": 51.3833, "lon": -9.6000, "country": "Ireland", "year": 1854, "height_m": 49, "range_nm": 18, "notes": "Granite tower; Teardrop of Ireland; marks southern extremity"},
    {"name": "Cap Frehel Lighthouse", "lat": 48.6808, "lon": -2.3167, "country": "France", "year": 1950, "height_m": 47, "range_nm": 29, "notes": "Rebuilt after WWII destruction; 70m above sea on dramatic cliffs"},
    {"name": "Flamborough Head Lighthouse", "lat": 54.1169, "lon": -0.0847, "country": "UK", "year": 1806, "height_m": 26.5, "range_nm": 24, "notes": "Chalk headland location; predecessor built 1674; Yorkshire coast"},
    {"name": "Perry Memorial Light (Put-in-Bay)", "lat": 41.6533, "lon": -82.8117, "country": "USA", "year": 1915, "height_m": 107, "range_nm": 0, "notes": "Doric column on South Bass Island; memorial to War of 1812; not a traditional lighthouse"},
    {"name": "Cape Point Lighthouse", "lat": -34.3564, "lon": 18.4972, "country": "South Africa", "year": 1860, "height_m": 87, "range_nm": 34, "notes": "High above sea level on clifftop; one of most powerful lights worldwide"},
    {"name": "Phare de Creac'h", "lat": 48.4719, "lon": -5.1308, "country": "France", "year": 1863, "height_m": 55, "range_nm": 34, "notes": "One of most powerful in world; Ile d'Ouessant; houses lighthouse museum"},
    {"name": "Anacapa Island Lighthouse", "lat": 34.0153, "lon": -119.3614, "country": "USA", "year": 1932, "height_m": 16, "range_nm": 20, "notes": "Channel Islands; Spanish Colonial Revival style; automated 1966"},
]

# =====================================================================
# 5. HAUNTED LIGHTHOUSES
# =====================================================================
HAUNTED_LIGHTHOUSES = [
    {"name": "Flannan Isles Lighthouse", "lat": 58.2883, "lon": -7.5889, "country": "UK (Scotland)", "year": 1899, "legend": "Three keepers vanished", "notes": "In December 1900, three keepers (Thomas Marshall, James Ducat, Donald MacArthur) vanished without trace. Clocks stopped, meals were uneaten, oilskins were missing. No bodies were ever found. Theories range from rogue waves to madness to supernatural causes."},
    {"name": "Point Lookout Lighthouse", "lat": 38.0422, "lon": -76.3281, "country": "USA (Maryland)", "year": 1830, "legend": "Civil War ghosts", "notes": "Built near a Civil War prison camp where 3,384 Confederate soldiers died. Paranormal investigators have recorded voices, footsteps, and apparitions. Multiple keepers reported ghostly encounters over decades."},
    {"name": "St. Augustine Lighthouse", "lat": 29.8856, "lon": -81.2886, "country": "USA (Florida)", "year": 1874, "legend": "Drowned girls haunt the tower", "notes": "Two daughters of superintendent Hezekiah Pittee drowned in 1873 during construction when a supply cart fell into the ocean. Their giggles and footsteps are reportedly heard throughout the tower."},
    {"name": "Seguin Island Lighthouse", "lat": 43.7072, "lon": -69.7578, "country": "USA (Maine)", "year": 1795, "legend": "Keeper murdered wife over a tune", "notes": "A keeper's wife owned a piano but could only play one tune. The isolated keeper went mad and killed her with an axe, then took his own life. Visitors report hearing a faint piano melody on foggy nights."},
    {"name": "Penfield Reef Lighthouse", "lat": 41.1172, "lon": -73.2222, "country": "USA (Connecticut)", "year": 1874, "legend": "Ghost of keeper Fred Jordan", "notes": "Keeper Frederick Jordan drowned in 1916 while rowing to shore. His ghost reportedly turned log book pages and was photographed as a shadowy figure by a boy in 1969."},
    {"name": "Old Presque Isle Lighthouse", "lat": 45.3594, "lon": -83.4906, "country": "USA (Michigan)", "year": 1840, "legend": "Keeper George Parris walks at night", "notes": "George Parris served as keeper and reportedly never wanted to leave. His wife was locked in the basement by her second husband. Both ghosts are said to haunt the tower; Parris lights the lamp at night."},
    {"name": "Heceta Head Lighthouse", "lat": 44.1372, "lon": -124.1283, "country": "USA (Oregon)", "year": 1894, "legend": "The Gray Lady (Rue)", "notes": "A female apparition named Rue, believed to be the mother of a child buried on the grounds, appears in the keeper's quarters. She is said to clean and rearrange objects. Rated one of the most haunted places in Oregon."},
    {"name": "New London Ledge Lighthouse", "lat": 41.3058, "lon": -72.0778, "country": "USA (Connecticut)", "year": 1909, "legend": "Ernie the ghost", "notes": "Keeper John Randolph (Ernie) reportedly slit his throat in 1936 after his wife ran off with the captain of the Block Island Ferry. Doors open and close, footsteps echo, and the foghorn activates on its own."},
    {"name": "Eilean Mor (Flannan Isles)", "lat": 58.2883, "lon": -7.5889, "country": "UK (Scotland)", "year": 1899, "legend": "Phantom lights", "notes": "Fishermen report seeing ghostly lights on the island and three shadowy figures walking together near the lighthouse where the three keepers disappeared in 1900."},
    {"name": "Yaquina Bay Lighthouse", "lat": 44.6178, "lon": -124.0706, "country": "USA (Oregon)", "year": 1871, "legend": "Muriel Trevenard's ghost", "notes": "In a famous 1899 story, a girl named Muriel entered the lighthouse and was never seen again; only a pool of blood and her handkerchief were found. Her ghost is said to peer from the upper windows."},
    {"name": "Gibraltar Point Lighthouse", "lat": 43.6128, "lon": -79.3822, "country": "Canada (Ontario)", "year": 1808, "legend": "Murdered keeper J.P. Radan", "notes": "First keeper J.P. Radan Muller was allegedly murdered by soldiers from Fort York in 1815 over a dispute about bootleg beer. His bones were found in 1893. His ghost reportedly roams the grounds."},
    {"name": "Battery Point Lighthouse", "lat": 41.7472, "lon": -124.2014, "country": "USA (California)", "year": 1856, "legend": "Rocking chair moves on its own", "notes": "Keepers report a rocking chair that moves by itself, the sound of footsteps, and items being rearranged. The Cat Lady ghost is also reported by multiple witnesses."},
    {"name": "Dungeness Lighthouse", "lat": 48.1792, "lon": -123.1111, "country": "USA (Washington)", "year": 1857, "legend": "Multiple ghost sightings", "notes": "Several keepers reported ghostly appearances. The lighthouse is on the Dungeness Spit, one of the longest natural sand spits in the world, adding to its eerie isolation."},
    {"name": "Phare de Tevennec", "lat": 48.0644, "lon": -4.8453, "country": "France", "year": 1875, "legend": "Cursed lighthouse of Brittany", "notes": "Keepers went insane from isolation and relentless storms on this tiny rock off Pointe du Raz. Screams and voices heard in the wind drove multiple keepers mad. A priest was stationed there to perform exorcisms."},
    {"name": "Smalls Lighthouse", "lat": 51.4333, "lon": -5.6667, "country": "UK (Wales)", "year": 1776, "legend": "Dead keeper kept by the living", "notes": "In 1801, keeper Thomas Howell was trapped with the decomposing body of Thomas Griffith for weeks. He tied the corpse to the railing where it appeared to wave at passing ships. This tragedy led to the three-keeper rule."},
    {"name": "Ram Island Ledge Light", "lat": 43.6311, "lon": -70.1875, "country": "USA (Maine)", "year": 1905, "legend": "Ghost ship appears in fog", "notes": "Keepers reported seeing a phantom schooner approaching the lighthouse during fog, only to vanish when it got close. The ghost of a former keeper also reportedly walks the catwalk."},
]

# =====================================================================
# 6. LIGHTHOUSE ARCHITECTURE STYLES
# =====================================================================
ARCHITECTURE_STYLES = [
    {"name": "Conical / Tapered Tower", "examples": [
        {"name": "Cape Hatteras Lighthouse", "lat": 35.2505, "lon": -75.5288, "country": "USA", "notes": "Classic conical brick tower; spiral black-and-white daymark; 64m tall"},
        {"name": "Ile Vierge Lighthouse", "lat": 48.6381, "lon": -4.5675, "country": "France", "notes": "Tallest stone conical tower; 82.5m; narrow taper from base to lantern"},
        {"name": "St. Augustine Lighthouse", "lat": 29.8856, "lon": -81.2886, "country": "USA", "notes": "Conical brick with black-and-white spiral stripes; 50m"},
        {"name": "Cape Agulhas Lighthouse", "lat": -34.8317, "lon": 20.0106, "country": "South Africa", "notes": "Classic conical tower at Africa's southern tip; 27m"},
    ], "color": "#06b6d4", "description": "The most common lighthouse shape: a tapering cylindrical tower that narrows toward the top, providing structural strength against wind and waves."},
    {"name": "Square / Rectangular Tower", "examples": [
        {"name": "Portland Head Light", "lat": 43.6231, "lon": -70.2078, "country": "USA", "notes": "Rubblestone square tower; 24m; attached keeper's house"},
        {"name": "Hook Head Lighthouse", "lat": 52.1239, "lon": -6.9292, "country": "Ireland", "notes": "Medieval Norman square tower; 35m; fortress-like walls"},
        {"name": "Boston Light", "lat": 42.3278, "lon": -70.8903, "country": "USA", "notes": "Conical-to-square transition tower; 27m; oldest US lighthouse"},
        {"name": "Cabo de Sao Vicente", "lat": 37.0228, "lon": -8.9972, "country": "Portugal", "notes": "Square white tower; 22m; attached to monastery ruins"},
    ], "color": "#f59e0b", "description": "Square or rectangular towers were common in medieval and early modern construction, often built as part of fortifications or monasteries."},
    {"name": "Octagonal Tower", "examples": [
        {"name": "Kjeungskjaer Lighthouse", "lat": 63.8494, "lon": 10.0000, "country": "Norway", "notes": "Red octagonal wooden lighthouse on tiny islet; 21m"},
        {"name": "Gibbs Hill Lighthouse", "lat": 32.2494, "lon": -64.8356, "country": "Bermuda", "notes": "Cast-iron octagonal tower; 36m; 1846; one of oldest iron lighthouses"},
        {"name": "Cape Byron Lighthouse", "lat": -28.6356, "lon": 153.6386, "country": "Australia", "notes": "White octagonal concrete tower; 22m; easternmost mainland point"},
        {"name": "Absecon Lighthouse", "lat": 39.3664, "lon": -74.4156, "country": "USA", "notes": "Octagonal brick tower; 52m; designed by General George Meade"},
    ], "color": "#8b5cf6", "description": "Octagonal towers combine the strength of a cylindrical shape with easier construction using flat panels. Popular in the 18th-19th centuries."},
    {"name": "Skeletal / Lattice Tower", "examples": [
        {"name": "Yokohama Marine Tower", "lat": 35.4433, "lon": 139.6522, "country": "Japan", "notes": "Steel lattice; 106m; once world's tallest lighthouse"},
        {"name": "Sanibel Island Lighthouse", "lat": 26.4511, "lon": -82.0128, "country": "USA", "notes": "Iron skeletal tower; 30m; designed to let hurricane winds pass through"},
        {"name": "Alligator Reef Lighthouse", "lat": 24.8500, "lon": -80.6189, "country": "USA", "notes": "Screw-pile skeletal tower; Florida Keys reef light; 45m"},
        {"name": "Sand Key Lighthouse", "lat": 24.4533, "lon": -81.8775, "country": "USA", "notes": "Skeletal iron tower; 20m; designed after 1846 hurricane destroyed predecessor"},
    ], "color": "#10b981", "description": "Open-framework towers built of iron or steel, designed to minimize wind resistance. Common in hurricane-prone and shallow-water locations."},
    {"name": "Caisson / Offshore Platform", "examples": [
        {"name": "New London Ledge Lighthouse", "lat": 41.3058, "lon": -72.0778, "country": "USA", "notes": "French Second Empire building on concrete caisson; appears to float"},
        {"name": "Thomas Point Shoal Light", "lat": 38.8972, "lon": -76.4364, "country": "USA", "notes": "Hexagonal cottage on screw-pile foundation; last unaltered screwpile in Chesapeake"},
        {"name": "Fourteen Foot Bank Light", "lat": 39.0489, "lon": -75.1822, "country": "USA", "notes": "Cast-iron caisson lighthouse; Delaware Bay; 1887"},
        {"name": "Roter Sand Lighthouse", "lat": 53.8569, "lon": 8.0847, "country": "Germany", "notes": "Caisson foundation on open sea; 28m; 1885; now heritage hotel"},
    ], "color": "#ec4899", "description": "Built on submerged caissons or screw-pile foundations in shallow water, these lighthouses stand directly in the sea on artificial platforms."},
    {"name": "Wave-Swept / Rock Tower", "examples": [
        {"name": "Bell Rock Lighthouse", "lat": 56.4341, "lon": -2.3869, "country": "UK", "notes": "Oldest surviving sea-washed tower; granite; 35m; Robert Stevenson 1811"},
        {"name": "Eddystone Lighthouse", "lat": 50.1088, "lon": -4.1559, "country": "UK", "notes": "Four towers built on same reef; current tower 1882; 41m"},
        {"name": "Bishop Rock Lighthouse", "lat": 49.8727, "lon": -6.4444, "country": "UK", "notes": "Smallest island in world with a building; 44m; granite"},
        {"name": "Fastnet Rock Lighthouse", "lat": 51.3833, "lon": -9.6000, "country": "Ireland", "notes": "Granite tower on isolated rock; 49m; Teardrop of Ireland"},
    ], "color": "#ef4444", "description": "Towers built directly on exposed rocks in the open sea, battered by waves. The most challenging and dangerous lighthouse construction projects."},
]

# =====================================================================
# 7. DECOMMISSIONED & RUINS
# =====================================================================
DECOMMISSIONED = [
    {"name": "Aniva Lighthouse", "lat": 46.0206, "lon": 143.4158, "country": "Russia (Sakhalin)", "year": 1939, "status": "Abandoned (nuclear-powered until 2006)", "notes": "Japanese-built concrete tower on remote cape; powered by radioisotope thermoelectric generators; one of the most photographed abandoned lighthouses"},
    {"name": "Rubjerg Knude Lighthouse", "lat": 57.4486, "lon": 9.7744, "country": "Denmark", "year": 1900, "status": "Decommissioned 1968; relocated 2019", "notes": "Was being buried by migrating sand dunes; relocated 70m inland in 2019 in dramatic engineering feat; will eventually be claimed by the sea"},
    {"name": "Smeaton's Tower (original location)", "lat": 50.1088, "lon": -4.1559, "country": "UK", "year": 1759, "status": "Relocated to Plymouth Hoe 1882", "notes": "Revolutionary design using hydraulic lime; upper portion moved stone-by-stone; stump still visible on Eddystone Reef"},
    {"name": "Klein Curacao Lighthouse", "lat": 11.9833, "lon": -68.6500, "country": "Curacao", "year": 1879, "status": "Decommissioned; ruins", "notes": "On uninhabited island; surrounded by shipwrecks; popular day-trip destination; slowly deteriorating"},
    {"name": "Mys Aniva Lighthouse", "lat": 46.0206, "lon": 143.4158, "country": "Russia", "year": 1939, "status": "Abandoned", "notes": "Same as Aniva; designed by Japanese architect Shinobu Miura; concrete art deco style; accessible only by sea"},
    {"name": "Great Isaac Cay Lighthouse", "lat": 26.0200, "lon": -79.0900, "country": "Bahamas", "year": 1859, "status": "Decommissioned 1969", "notes": "Two keepers vanished in 1969 (never found); hurricane damage; skeleton of iron lighthouse remains standing"},
    {"name": "Phare des Baleines (old tower)", "lat": 46.2525, "lon": -1.5639, "country": "France", "year": 1682, "status": "Decommissioned 1854; museum", "notes": "Old Vauban-era tower preserved alongside its 1854 replacement on Ile de Re; named for beached whales"},
    {"name": "Tillamook Rock Lighthouse", "lat": 45.9378, "lon": -124.0194, "country": "USA (Oregon)", "year": 1881, "status": "Decommissioned 1957; columbarium", "notes": "Terrible Tilly; built on isolated basalt rock; now a columbarium (urn repository); listed on National Register"},
    {"name": "Sabine Pass Lighthouse", "lat": 29.7300, "lon": -93.8700, "country": "USA (Texas)", "year": 1857, "status": "Decommissioned 1952", "notes": "Surviving Civil War lighthouse; Confederate forces defended it; deteriorating but preservation efforts ongoing"},
    {"name": "Port Lairge Lighthouse", "lat": 52.2600, "lon": -6.9900, "country": "Ireland", "year": 1819, "status": "Decommissioned; converted to residence", "notes": "One of many Irish lighthouses converted to luxury vacation homes; managed by Great Lighthouses of Ireland"},
    {"name": "Race Rocks Lighthouse", "lat": 48.2983, "lon": -123.5314, "country": "Canada (BC)", "year": 1860, "status": "Automated 1997; ecological reserve", "notes": "Granite shipped from Scotland; now surrounded by marine ecological reserve; staffed by volunteer eco-guardians"},
    {"name": "Rattray Head Lighthouse", "lat": 57.6114, "lon": -1.8183, "country": "UK (Scotland)", "year": 1895, "status": "Decommissioned 1982", "notes": "Granite tower; stranded 100m offshore due to coastal erosion; accessible at low tide; fog horn station demolished"},
    {"name": "Phare de Tevennec", "lat": 48.0644, "lon": -4.8453, "country": "France", "year": 1875, "status": "Automated 1910; now artist residency", "notes": "Once cursed lighthouse where keepers went mad; now hosts artists-in-residence program by Tout Commence en Finistere"},
    {"name": "South Solitary Island Lighthouse", "lat": -30.2050, "lon": 153.2700, "country": "Australia", "year": 1880, "status": "Decommissioned 1975; heritage", "notes": "Remote island lighthouse; inspired the film The Light Between Oceans; accessible by boat; whale watching"},
    {"name": "Cape Bowling Green Lighthouse", "lat": -19.2600, "lon": 147.1000, "country": "Australia", "year": 1874, "status": "Relocated 1987; original ruins", "notes": "Original cast-iron tower relocated to Townsville museum; only foundation and cistern remain on sand spit"},
]

# =====================================================================
# 8. REMOTE & EXTREME LIGHTHOUSES
# =====================================================================
REMOTE_LIGHTHOUSES = [
    {"name": "Flannan Isles Lighthouse", "lat": 58.2883, "lon": -7.5889, "country": "UK (Scotland)", "year": 1899, "isolation": "35 km from nearest inhabited island", "danger": "Extreme exposure; three keepers vanished 1900", "notes": "On Eilean Mor in the Outer Hebrides; accessible only by boat in calm weather; the mystery of the three vanished keepers has never been solved"},
    {"name": "Stannard Rock Lighthouse", "lat": 47.1833, "lon": -87.2250, "country": "USA (Michigan)", "year": 1882, "isolation": "39 km from nearest land", "danger": "Lake Superior storms; isolation", "notes": "Called the loneliest place in America; furthest from land of any lighthouse in the US; massive ice formations in winter"},
    {"name": "Hyskeir Lighthouse", "lat": 56.5833, "lon": -6.6833, "country": "UK (Scotland)", "year": 1904, "isolation": "11 km from nearest island (Rum)", "danger": "Extreme Atlantic exposure", "notes": "Tiny rock islet in the Sea of the Hebrides; built by David and Charles Stevenson; automated 1997"},
    {"name": "Phare de Kereonnec (Ar-Men)", "lat": 48.0333, "lon": -4.9833, "country": "France", "year": 1881, "isolation": "15 km off Ile de Sein", "danger": "Most dangerous lighthouse construction in history", "notes": "Ar-Men means the rock in Breton; took 14 years to build (workers could only land 100 hours per year); battered by 20m waves; called Hell of Hells"},
    {"name": "Phare de la Jument", "lat": 48.4228, "lon": -5.1311, "country": "France", "year": 1911, "isolation": "2 km from Ile d'Ouessant", "danger": "Extreme wave exposure", "notes": "Famous photograph by Jean Guichard showed keeper opening door as massive wave crashed behind him; waves regularly overtop the 47m tower"},
    {"name": "Skerryvore Lighthouse", "lat": 56.3197, "lon": -7.1500, "country": "UK (Scotland)", "year": 1844, "isolation": "18 km from Tiree", "danger": "Exposed Atlantic rock; violent storms", "notes": "Alan Stevenson's masterpiece; 48m granite tower; called the most graceful lighthouse ever built; Robert Louis Stevenson dedicated Kidnapped to it"},
    {"name": "Muckle Flugga Lighthouse", "lat": 60.8583, "lon": -0.8833, "country": "UK (Shetland)", "year": 1858, "isolation": "Northernmost point of British Isles", "danger": "Arctic storms; extreme latitude", "notes": "Built during Crimean War to guide Royal Navy; Thomas and David Stevenson design; 20m tower on dramatic cliff"},
    {"name": "Morant Point Lighthouse", "lat": 17.9158, "lon": -76.1833, "country": "Jamaica", "year": 1842, "isolation": "Extreme eastern tip of Jamaica", "danger": "Hurricanes; remote access", "notes": "Cast-iron tower shipped from London; only accessible by rough dirt road; exposed to every Caribbean hurricane"},
    {"name": "Cape Reinga Lighthouse", "lat": -34.4289, "lon": 172.6772, "country": "New Zealand", "year": 1941, "isolation": "North tip of New Zealand", "danger": "Colliding ocean currents", "notes": "Where the Tasman Sea meets the Pacific Ocean; sacred to Maori as Te Rerenga Wairua (leaping-off place of spirits)"},
    {"name": "Les Eclaireurs Lighthouse", "lat": -54.8775, "lon": -68.0583, "country": "Argentina", "year": 1920, "isolation": "Beagle Channel, near Ushuaia", "danger": "Subantarctic storms; icebergs", "notes": "Often called End of the World lighthouse; one of southernmost lighthouses; red-and-white bands; small rocky island"},
    {"name": "Slettnes Lighthouse", "lat": 71.0892, "lon": 28.2108, "country": "Norway", "year": 1905, "isolation": "Northernmost mainland lighthouse (71 N)", "danger": "Extreme cold; polar nights", "notes": "Cast-iron tower; midnight sun in summer; complete darkness in winter; aurora borealis viewing site"},
    {"name": "Cape Horn Lighthouse", "lat": -55.9833, "lon": -67.2667, "country": "Chile", "year": 1991, "isolation": "Southernmost point of South America", "danger": "Worst seas on Earth; 100+ knot winds", "notes": "Unmanned solar-powered light on Isla Hornos; memorial to 10,000+ sailors who died rounding the Horn; Chilean Navy maintains it"},
    {"name": "Thacher Island Twin Lights", "lat": 42.6378, "lon": -70.5747, "country": "USA (Massachusetts)", "year": 1771, "isolation": "1.6 km offshore", "danger": "North Atlantic storms", "notes": "Only surviving twin lighthouses in the US; named after Anthony Thacher who was shipwrecked here in 1635; 21 of 23 aboard died"},
    {"name": "Tillamook Rock Lighthouse", "lat": 45.9378, "lon": -124.0194, "country": "USA (Oregon)", "year": 1881, "isolation": "2 km offshore on basalt rock", "danger": "Massive Pacific storm waves", "notes": "Terrible Tilly; waves threw rocks and debris through lantern room; a surveyor was swept to his death before construction began"},
    {"name": "Wolf Rock Lighthouse", "lat": 49.9683, "lon": -5.8100, "country": "UK", "year": 1870, "isolation": "13 km from Land's End", "danger": "Fully exposed to Atlantic gales", "notes": "Took 8 years to build on submerged granite pinnacle; only 60m x 40m exposed at low tide; helipad added for servicing"},
]

# =====================================================================
# 9. LIGHTHOUSE KEEPERS' STORIES
# =====================================================================
KEEPER_STORIES = [
    {"name": "Ida Lewis — Lime Rock Lighthouse", "lat": 41.4772, "lon": -71.3264, "country": "USA (Rhode Island)", "year_range": "1857-1911", "keeper": "Ida Lewis", "story": "Heroic rescuer", "notes": "Ida Lewis saved at least 18 people from drowning over her career. She became the most famous lighthouse keeper in America and was awarded the Gold Lifesaving Medal. She served for 54 years and died at her post in 1911."},
    {"name": "Grace Darling — Longstone Lighthouse", "lat": 55.6347, "lon": -1.6167, "country": "UK", "year_range": "1838", "keeper": "Grace Darling & William Darling", "story": "Heroic rescue of SS Forfarshire survivors", "notes": "In September 1838, 22-year-old Grace and her father rowed through a violent storm to rescue 9 survivors of the SS Forfarshire wreck. She became a national heroine overnight and died of tuberculosis aged 26."},
    {"name": "Thomas Marshall, James Ducat, Donald MacArthur — Flannan Isles", "lat": 58.2883, "lon": -7.5889, "country": "UK (Scotland)", "year_range": "1900", "keeper": "Three keepers", "story": "The Flannan Isles mystery", "notes": "All three keepers vanished in December 1900. The relief keeper found the lighthouse dark, the clock stopped, and the beds unmade. No trace of the men was ever found. The mystery has inspired poems, songs, operas, and films."},
    {"name": "Thomas Howell & Thomas Griffith — Smalls Lighthouse", "lat": 51.4333, "lon": -5.6667, "country": "UK (Wales)", "year_range": "1801", "keeper": "Thomas Howell", "story": "Trapped with a dead colleague", "notes": "When Thomas Griffith died, Howell feared being accused of murder if he disposed of the body. He lashed the corpse to the external railing. For weeks, the dead man's arm appeared to beckon passing ships. Howell emerged a broken man. This tragedy led to the three-keeper rule."},
    {"name": "Abigail Burgess — Matinicus Rock Light", "lat": 43.7833, "lon": -68.8556, "country": "USA (Maine)", "year_range": "1853-1861", "keeper": "Abigail Burgess", "story": "Teenage keeper during storms", "notes": "At age 17, Abigail kept the light burning for four weeks during terrible storms while her father was stranded ashore. She later married the son of a keeper and continued tending lights for over 25 years. She wrote: The light is my child."},
    {"name": "Juliet Nichols — Angel Island Lighthouse", "lat": 37.8608, "lon": -122.4222, "country": "USA (California)", "year_range": "1902-1914", "keeper": "Juliet Nichols", "story": "Solitary woman keeper for 12 years", "notes": "Juliet became keeper after her husband's death. For 12 years she maintained the light alone on the island, hand-cranking the fog bell thousands of times per day during foggy periods. She was awarded an efficiency star."},
    {"name": "Marcus Hanna — Cape Elizabeth", "lat": 43.5667, "lon": -70.2000, "country": "USA (Maine)", "year_range": "1885", "keeper": "Marcus Hanna", "story": "Congressional Medal of Honor rescue", "notes": "During a terrible January 1885 blizzard, Hanna (a Civil War veteran) rescued two sailors from the wreck of the schooner Australia, climbing ice-covered rocks in darkness. He was awarded the only Congressional Medal of Honor ever given for lighthouse service."},
    {"name": "Fanny Salter — Turkey Point Lighthouse", "lat": 39.4444, "lon": -76.0000, "country": "USA (Maryland)", "year_range": "1925-1947", "keeper": "Fanny Salter", "story": "Last female civilian lighthouse keeper in US", "notes": "Fanny became keeper after her husband's death and served alone for 22 years. She carried oil up 38-foot tower steps, maintained the grounds, and refused to leave despite government pressure to automate."},
    {"name": "Robert Stevenson Family — Bell Rock", "lat": 56.4341, "lon": -2.3869, "country": "UK (Scotland)", "year_range": "1811-1940s", "keeper": "Stevenson engineering dynasty", "story": "Family built 97 Scottish lighthouses", "notes": "Robert Stevenson built Bell Rock (1811). His sons David, Thomas, and Alan, and grandsons David Alan and Charles built virtually every Scottish lighthouse. Robert Louis Stevenson (the author) was Thomas's son and almost became a lighthouse engineer himself."},
    {"name": "Harriet Colfax — Michigan City Light", "lat": 41.7275, "lon": -86.9053, "country": "USA (Indiana)", "year_range": "1861-1904", "keeper": "Harriet Colfax", "story": "43 years of solitary service", "notes": "Harriet served as keeper for 43 years, making her one of the longest-serving keepers in US history. She survived storms, ice floes, and loneliness. Her diary reveals a dedicated public servant in extreme isolation."},
    {"name": "Kate Walker — Robbins Reef Lighthouse", "lat": 40.6578, "lon": -74.0650, "country": "USA (New York)", "year_range": "1886-1919", "keeper": "Kate Walker", "story": "Tiny woman, enormous courage", "notes": "At just 4 feet 10 inches, Kate took over after her husband died of pneumonia. She served 33 years and saved at least 50 lives. Her husband's dying words were: Mind the light, Kate. She did, for three more decades."},
    {"name": "Juan de Dios — Isla de los Estados", "lat": -54.8000, "lon": -64.3000, "country": "Argentina", "year_range": "1884-1902", "keeper": "Various Argentine Navy keepers", "story": "The loneliest lighthouse posting", "notes": "Keepers at San Juan de Salvamento (the Lighthouse at the End of the World, inspiration for Jules Verne's novel) endured sub-Antarctic isolation, scurvy, and madness. Several went insane from loneliness."},
]

# =====================================================================
# 10. MODERN NAVIGATION
# =====================================================================
MODERN_NAVIGATION = [
    {"name": "DGPS Station Yokohama", "lat": 35.4433, "lon": 139.6522, "country": "Japan", "type": "DGPS Reference Station", "notes": "Provides differential GPS corrections for Tokyo Bay; accuracy to sub-meter level for shipping"},
    {"name": "DGPS Station Hoek van Holland", "lat": 51.9794, "lon": 4.1200, "country": "Netherlands", "type": "DGPS Reference Station", "notes": "Covers North Sea approaches; critical for Rotterdam port traffic; IALA standard"},
    {"name": "Vardo AIS Station", "lat": 70.3700, "lon": 31.1100, "country": "Norway", "type": "AIS Base Station", "notes": "Monitors Arctic shipping traffic; part of Norwegian Coastal Administration network; tracks Northern Sea Route"},
    {"name": "Singapore VTMS", "lat": 1.2600, "lon": 103.8200, "country": "Singapore", "type": "Vessel Traffic Management System", "notes": "One of the world's most sophisticated maritime traffic systems; manages 130,000+ vessels/year through the strait"},
    {"name": "Dover Strait VTMS", "lat": 51.1200, "lon": 1.3300, "country": "UK", "type": "Vessel Traffic Management System", "notes": "Monitors world's busiest shipping lane; 500+ vessel movements daily; operated by Maritime and Coastguard Agency"},
    {"name": "Borkum RACON", "lat": 53.5900, "lon": 6.6600, "country": "Germany", "type": "Radar Beacon (RACON)", "notes": "Radar transponder beacon marking approach to Ems estuary; appears as coded dash on ship radar screens"},
    {"name": "Haisborough Sand Buoy (LED)", "lat": 52.8700, "lon": 1.7800, "country": "UK", "type": "LED Navigation Buoy", "notes": "Modern LED-lit buoy replacing traditional gas; solar-powered; marks dangerous sandbank off Norfolk coast"},
    {"name": "Port Said Approach (AtoN)", "lat": 31.2800, "lon": 32.3400, "country": "Egypt", "type": "Automated AtoN System", "notes": "Automated Aids to Navigation system guiding vessels into the Suez Canal; integrated with VTS"},
    {"name": "Macquarie Lighthouse (automated)", "lat": -33.8583, "lon": 151.2806, "country": "Australia", "type": "Automated LED Lighthouse", "notes": "Australia's first and longest-serving lighthouse (1818); fully automated with modern LED optics replacing original oil lamp"},
    {"name": "Ambrose Channel Buoy", "lat": 40.4600, "lon": -73.8300, "country": "USA", "type": "DGPS-Enhanced Navigation Buoy", "notes": "Marks approach to New York Harbor; AIS-equipped, LED-lit, solar-powered; handles 5,000+ ship movements annually"},
    {"name": "Malin Head Radio Station", "lat": 55.3700, "lon": -7.3400, "country": "Ireland", "type": "Marine Radio & NAVTEX Station", "notes": "Broadcasts weather and navigation warnings for North Atlantic; critical for GMDSS safety communications"},
    {"name": "Isle of May NtM Station", "lat": 56.1850, "lon": -2.5550, "country": "UK (Scotland)", "type": "Automated Lighthouse + AIS", "notes": "Medieval to modern: monks lit fires in 1636; now fully automated LED with AIS transponder and remote monitoring"},
    {"name": "Buzzards Bay Entrance Light", "lat": 41.3978, "lon": -71.0339, "country": "USA", "type": "Automated Texas Tower", "notes": "Replaced lightship in 1961; oil-rig style platform; fully automated; marks approach to Cape Cod Canal"},
    {"name": "Phare du Four (automated)", "lat": 48.5167, "lon": -4.8000, "country": "France", "type": "Automated Solar + LED", "notes": "Remote Breton lighthouse; converted to solar/LED; monitored remotely from Brest; no keeper since 1993"},
    {"name": "E-Navigation Test Bed Busan", "lat": 35.1000, "lon": 129.0300, "country": "South Korea", "type": "E-Navigation Pilot Zone", "notes": "IMO e-Navigation test bed; integrated digital communications, real-time charts, automated weather routing for autonomous shipping"},
    {"name": "Cape Roca eLoran Station", "lat": 38.7808, "lon": -9.4991, "country": "Portugal", "type": "eLoran Transmitter", "notes": "Enhanced Long Range Navigation; GPS backup system providing independent position fixing; part of European eLoran network"},
    {"name": "Panama Canal AIS Network", "lat": 9.2000, "lon": -79.7500, "country": "Panama", "type": "Canal AIS + VTS Integration", "notes": "Full AIS coverage of 82 km canal; automated scheduling; real-time vessel tracking; manages 14,000 transits per year"},
    {"name": "Malacca Strait AIS Network", "lat": 2.5000, "lon": 101.5000, "country": "Malaysia/Singapore/Indonesia", "type": "Tri-National AIS Network", "notes": "Cooperative AIS network monitoring 90,000+ vessels/year; anti-piracy surveillance; environmental monitoring"},
]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def _make_base_map(lat: float = 30.0, lon: float = 0.0, zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map."""
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )


def _render_map(m: folium.Map, height: int = 500):
    """Render a folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _dark_fig(figsize=(10, 5)):
    """Create a matplotlib figure with dark theme."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.tick_params(colors="#e8ecf4")
    ax.xaxis.label.set_color("#e8ecf4")
    ax.yaxis.label.set_color("#e8ecf4")
    ax.title.set_color("#e8ecf4")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Provide CSV download button."""
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv, file_name=filename, mime="text/csv")


@st.cache_data(ttl=3600)
def _overpass_lighthouses(lat: float, lon: float, radius_km: float) -> dict | None:
    """Search lighthouses via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:90];
(
  node["man_made"="lighthouse"](around:{radius_m},{lat},{lon});
  way["man_made"="lighthouse"](around:{radius_m},{lat},{lon});
  node["seamark:type"="light_major"](around:{radius_m},{lat},{lon});
  node["seamark:type"="light_minor"](around:{radius_m},{lat},{lon});
);
out center body;
"""
    return query_overpass(query)


@st.cache_data(ttl=3600)
def _overpass_navigation_aids(lat: float, lon: float, radius_km: float) -> dict | None:
    """Search modern navigation aids via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:90];
(
  node["seamark:type"="light_major"](around:{radius_m},{lat},{lon});
  node["seamark:type"="light_minor"](around:{radius_m},{lat},{lon});
  node["seamark:type"="buoy_lateral"](around:{radius_m},{lat},{lon});
  node["seamark:type"="buoy_cardinal"](around:{radius_m},{lat},{lon});
  node["seamark:type"="beacon_lateral"](around:{radius_m},{lat},{lon});
  node["man_made"="lighthouse"](around:{radius_m},{lat},{lon});
);
out center body;
"""
    return query_overpass(query)


# =====================================================================
# MAP MODE RENDERERS
# =====================================================================

def _render_famous():
    """Mode 1: World's Most Famous Lighthouses."""
    st.markdown("#### World's Most Famous Lighthouses")
    st.markdown(
        "Explore the top 50 most iconic lighthouses across every continent, "
        "from ancient Roman towers to 19th-century engineering marvels."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Lighthouses", len(FAMOUS_LIGHTHOUSES))
    with col2:
        countries = len(set(lh["country"] for lh in FAMOUS_LIGHTHOUSES))
        st.metric("Countries", countries)
    with col3:
        avg_h = sum(lh["height_m"] for lh in FAMOUS_LIGHTHOUSES) / len(FAMOUS_LIGHTHOUSES)
        st.metric("Avg Height", f"{avg_h:.1f} m")

    # Filters
    all_countries = sorted(set(lh["country"] for lh in FAMOUS_LIGHTHOUSES))
    sel_countries = st.multiselect(
        "Filter by Country", all_countries, default=[], key="famous_countries"
    )
    filtered = FAMOUS_LIGHTHOUSES
    if sel_countries:
        filtered = [lh for lh in FAMOUS_LIGHTHOUSES if lh["country"] in sel_countries]

    st.info(f"Showing {len(filtered)} of {len(FAMOUS_LIGHTHOUSES)} lighthouses")

    # Map
    m = _make_base_map()
    cluster = MarkerCluster(name="Famous Lighthouses")
    for lh in filtered:
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(lh['name'])}</b><br>"
            f"<b>Country:</b> {escape(str(lh['country']))}<br>"
            f"<b>Year Built:</b> {escape(str(lh['year']))}<br>"
            f"<b>Height:</b> {lh['height_m']} m<br>"
            f"<b>Range:</b> {lh['range_nm']} nm<br>"
            f"<b>Notes:</b> {escape(lh['notes'])}"
            f"</div>"
        )
        folium.Marker(
            location=[lh["lat"], lh["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(lh["name"]),
            icon=folium.Icon(color="orange", icon="lightbulb", prefix="fa"),
        ).add_to(cluster)
    cluster.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Data table
    st.markdown("##### Lighthouse Data")
    df = pd.DataFrame(filtered)
    col_order = ["name", "country", "year", "height_m", "range_nm", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "famous_lighthouses.csv")

    # Chart: heights
    fig, ax = _dark_fig(figsize=(10, 6))
    sorted_lh = sorted(filtered, key=lambda x: x["height_m"], reverse=True)[:25]
    names = [lh["name"][:25] for lh in sorted_lh]
    heights = [lh["height_m"] for lh in sorted_lh]
    ax.barh(names, heights, color="#f59e0b", edgecolor="#2a3550")
    ax.set_xlabel("Height (m)")
    ax.set_title("Top 25 Famous Lighthouses by Height")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_ancient():
    """Mode 2: Ancient Lighthouses."""
    st.markdown("#### Ancient Lighthouses")
    st.markdown(
        "From the legendary Pharos of Alexandria to Roman pharos towers, "
        "these are the earliest lighthouses and navigation beacons in human history."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ancient Lighthouses", len(ANCIENT_LIGHTHOUSES))
    with col2:
        active = sum(1 for a in ANCIENT_LIGHTHOUSES if "Active" in a["status"])
        st.metric("Still Active", active)

    # Map
    m = _make_base_map(lat=38.0, lon=15.0, zoom=4)
    for lh in ANCIENT_LIGHTHOUSES:
        color = "green" if "Active" in lh["status"] else ("red" if "Destroyed" in lh["status"] else "gray")
        popup_html = (
            f"<div style='min-width:240px;'>"
            f"<b>{escape(lh['name'])}</b><br>"
            f"<b>Country:</b> {escape(lh['country'])}<br>"
            f"<b>Built:</b> {escape(lh['year'])}<br>"
            f"<b>Height:</b> {lh['height_m']} m<br>"
            f"<b>Status:</b> {escape(lh['status'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{escape(lh['notes'])}</i>"
            f"</div>"
        )
        folium.Marker(
            location=[lh["lat"], lh["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=escape(lh["name"]),
            icon=folium.Icon(color=color, icon="fire", prefix="fa"),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Data table
    st.markdown("##### Ancient Lighthouse Records")
    df = pd.DataFrame(ANCIENT_LIGHTHOUSES)
    col_order = ["name", "country", "year", "height_m", "status", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "ancient_lighthouses.csv")

    # Timeline chart
    fig, ax = _dark_fig(figsize=(10, 5))
    names = [lh["name"][:25] for lh in ANCIENT_LIGHTHOUSES]
    heights = [lh["height_m"] for lh in ANCIENT_LIGHTHOUSES]
    colors = ["#10b981" if "Active" in lh["status"] else "#ef4444" for lh in ANCIENT_LIGHTHOUSES]
    ax.barh(names, heights, color=colors, edgecolor="#2a3550")
    ax.set_xlabel("Height (m)")
    ax.set_title("Ancient Lighthouses by Height (Green = Active, Red = Destroyed/Ruins)")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_by_country():
    """Mode 3: Lighthouses by Country (Overpass search)."""
    st.markdown("#### Lighthouses by Country")
    st.markdown(
        "Search for lighthouses in specific countries and regions using OpenStreetMap data. "
        "Select a preset region or define a custom search area."
    )

    region = st.selectbox("Select Region", list(COUNTRY_REGIONS.keys()), key="lbc_region")

    custom_lat, custom_lon, custom_radius = 54.0, -2.0, 400
    if region != "Custom Area":
        preset = COUNTRY_REGIONS[region]
        if preset:
            custom_lat = preset["lat"]
            custom_lon = preset["lon"]
            custom_radius = preset["radius"]
    else:
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            custom_lat = st.number_input("Latitude", value=54.0, key="lbc_lat")
        with cc2:
            custom_lon = st.number_input("Longitude", value=-2.0, key="lbc_lon")
        with cc3:
            custom_radius = st.number_input(
                "Radius (km)", value=400, min_value=10, max_value=1000, key="lbc_radius"
            )

    do_search = st.button("Search Lighthouses", key="lbc_search")

    if do_search:
        with st.spinner(f"Searching Overpass API for lighthouses in {region}..."):
            data = _overpass_lighthouses(custom_lat, custom_lon, custom_radius)
            if data and "_error" not in data:
                elements = data.get("elements", [])
                features = []
                for el in elements:
                    lat_e = el.get("lat") or el.get("center", {}).get("lat")
                    lon_e = el.get("lon") or el.get("center", {}).get("lon")
                    if lat_e is None or lon_e is None:
                        continue
                    tags = el.get("tags", {})
                    name = tags.get("name", tags.get("name:en", "Unnamed Lighthouse"))
                    features.append({
                        "name": name,
                        "lat": lat_e,
                        "lon": lon_e,
                        "seamark_type": tags.get("seamark:type", "lighthouse"),
                        "height": tags.get("height", "N/A"),
                        "start_date": tags.get("start_date", "N/A"),
                        "description": tags.get("description", ""),
                        "website": tags.get("website", ""),
                    })

                st.success(f"Found {len(features)} lighthouses and navigation lights in {region}.")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Lighthouses Found", len(features))
                with col2:
                    named = sum(1 for f in features if f["name"] != "Unnamed Lighthouse")
                    st.metric("Named", named)

                # Map
                m = _make_base_map(lat=custom_lat, lon=custom_lon, zoom=6)
                cluster = MarkerCluster(name="Lighthouses (OSM)")
                for f in features:
                    popup_html = (
                        f"<div style='min-width:200px;'>"
                        f"<b>{escape(f['name'])}</b><br>"
                        f"<b>Type:</b> {escape(f['seamark_type'])}<br>"
                        f"<b>Height:</b> {escape(str(f['height']))}<br>"
                        f"<b>Built:</b> {escape(str(f['start_date']))}<br>"
                    )
                    if f["website"]:
                        popup_html += f"<b>Website:</b> {escape(f['website'])}<br>"
                    if f["description"]:
                        popup_html += f"<i>{escape(f['description'][:200])}</i><br>"
                    popup_html += "</div>"
                    folium.CircleMarker(
                        location=[f["lat"], f["lon"]],
                        radius=6,
                        color="#f59e0b",
                        fill=True,
                        fill_color="#f59e0b",
                        fill_opacity=0.8,
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=escape(f["name"]),
                    ).add_to(cluster)
                cluster.add_to(m)
                folium.LayerControl().add_to(m)
                _render_map(m)

                # Table
                st.markdown("##### Search Results")
                df = pd.DataFrame(features)
                st.dataframe(df, width="stretch")
                _csv_download(df, f"lighthouses_{region.replace(' ', '_').lower()}.csv")
            elif data and "_error" in data:
                st.warning(f"Overpass error: {data['_error']}")
            else:
                st.warning("No response from Overpass API. Try again or reduce the radius.")
    else:
        st.info("Click 'Search Lighthouses' to query OpenStreetMap for the selected region.")
        m = _make_base_map(lat=custom_lat, lon=custom_lon, zoom=4)
        folium.Circle(
            location=[custom_lat, custom_lon],
            radius=custom_radius * 1000,
            color="#06b6d4",
            fill=True,
            fill_opacity=0.1,
            tooltip=f"Search area: {custom_radius} km radius",
        ).add_to(m)
        _render_map(m)


def _render_tallest():
    """Mode 4: Tallest Lighthouses."""
    st.markdown("#### Tallest Lighthouses in the World")
    st.markdown(
        "The world's tallest lighthouses ranked by height, from the 133-meter "
        "Jeddah Light to classic stone and iron towers."
    )

    sorted_lh = sorted(TALLEST_LIGHTHOUSES, key=lambda x: x["height_m"], reverse=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tallest", f"{sorted_lh[0]['height_m']} m", sorted_lh[0]["name"])
    with col2:
        avg = sum(lh["height_m"] for lh in sorted_lh) / len(sorted_lh)
        st.metric("Average Height", f"{avg:.1f} m")
    with col3:
        st.metric("Total Listed", len(sorted_lh))

    min_h = st.slider("Minimum Height (m)", 0, 130, 0, key="tallest_min_h")
    filtered = [lh for lh in sorted_lh if lh["height_m"] >= min_h]
    st.info(f"Showing {len(filtered)} lighthouses above {min_h}m")

    # Map
    m = _make_base_map()
    for lh in filtered:
        # Scale marker radius by height
        radius = max(5, lh["height_m"] / 5)
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(lh['name'])}</b><br>"
            f"<b>Country:</b> {escape(str(lh['country']))}<br>"
            f"<b>Year:</b> {lh['year']}<br>"
            f"<b>Height:</b> <span style='color:#f59e0b;font-weight:bold;'>{lh['height_m']} m</span><br>"
            f"<b>Range:</b> {lh['range_nm']} nm<br>"
            f"<b>Notes:</b> {escape(lh['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[lh["lat"], lh["lon"]],
            radius=radius,
            color="#f59e0b",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(lh['name'])} ({lh['height_m']}m)",
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Data table
    st.markdown("##### Tallest Lighthouses Data")
    df = pd.DataFrame(filtered)
    col_order = ["name", "country", "year", "height_m", "range_nm", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "tallest_lighthouses.csv")

    # Chart
    fig, ax = _dark_fig(figsize=(10, 7))
    names = [lh["name"][:28] for lh in filtered]
    heights = [lh["height_m"] for lh in filtered]
    bar_colors = ["#ef4444" if h >= 100 else "#f59e0b" if h >= 60 else "#06b6d4" for h in heights]
    ax.barh(names, heights, color=bar_colors, edgecolor="#2a3550")
    ax.set_xlabel("Height (m)")
    ax.set_title("World's Tallest Lighthouses")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_haunted():
    """Mode 5: Haunted Lighthouses."""
    st.markdown("#### Haunted Lighthouses")
    st.markdown(
        "Lighthouses have always attracted ghost stories -- isolation, tragedy, "
        "and relentless storms create the perfect setting for legends and hauntings."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Haunted Lighthouses", len(HAUNTED_LIGHTHOUSES))
    with col2:
        us_count = sum(1 for h in HAUNTED_LIGHTHOUSES if "USA" in h["country"])
        st.metric("In the USA", us_count)

    # Map
    m = _make_base_map(lat=45.0, lon=-30.0, zoom=3)
    for lh in HAUNTED_LIGHTHOUSES:
        popup_html = (
            f"<div style='min-width:260px;'>"
            f"<b>{escape(lh['name'])}</b><br>"
            f"<b>Country:</b> {escape(lh['country'])}<br>"
            f"<b>Year Built:</b> {lh['year']}<br>"
            f"<b>Legend:</b> <i>{escape(lh['legend'])}</i><br>"
            f"<hr style='margin:4px 0;'>"
            f"{escape(lh['notes'][:300])}"
            f"</div>"
        )
        folium.Marker(
            location=[lh["lat"], lh["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=escape(lh["name"]),
            icon=folium.Icon(color="darkred", icon="ghost", prefix="fa"),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Story cards
    st.markdown("##### Ghost Stories & Legends")
    for lh in HAUNTED_LIGHTHOUSES:
        with st.expander(f"{lh['name']} ({lh['country']}, {lh['year']}) -- {lh['legend']}"):
            st.write(lh["notes"])

    # Data table
    st.markdown("##### Data Table")
    df = pd.DataFrame(HAUNTED_LIGHTHOUSES)
    col_order = ["name", "country", "year", "legend", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "haunted_lighthouses.csv")


def _render_architecture():
    """Mode 6: Lighthouse Architecture Styles."""
    st.markdown("#### Lighthouse Architecture")
    st.markdown(
        "Lighthouses come in many shapes: conical towers, square keeps, "
        "octagonal pillars, skeletal frames, wave-swept rocks, and offshore caissons."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Architecture Styles", len(ARCHITECTURE_STYLES))
    with col2:
        total_examples = sum(len(s["examples"]) for s in ARCHITECTURE_STYLES)
        st.metric("Example Lighthouses", total_examples)

    sel_style = st.selectbox(
        "Select Architecture Style",
        [s["name"] for s in ARCHITECTURE_STYLES],
        key="arch_style",
    )

    style = next(s for s in ARCHITECTURE_STYLES if s["name"] == sel_style)
    st.markdown(f"**{style['name']}:** {style['description']}")

    # Map
    m = _make_base_map(lat=40.0, lon=-20.0, zoom=3)
    # Show all styles as background
    for s in ARCHITECTURE_STYLES:
        fg = folium.FeatureGroup(name=s["name"])
        for ex in s["examples"]:
            is_selected = (s["name"] == sel_style)
            radius = 10 if is_selected else 5
            opacity = 0.9 if is_selected else 0.4
            popup_html = (
                f"<div style='min-width:200px;'>"
                f"<b>{escape(ex['name'])}</b><br>"
                f"<b>Style:</b> {escape(s['name'])}<br>"
                f"<b>Country:</b> {escape(ex['country'])}<br>"
                f"<b>Notes:</b> {escape(ex['notes'])}"
                f"</div>"
            )
            folium.CircleMarker(
                location=[ex["lat"], ex["lon"]],
                radius=radius,
                color=s["color"],
                fill=True,
                fill_color=s["color"],
                fill_opacity=opacity,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{escape(ex['name'])} ({escape(s['name'])})",
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Details for selected style
    st.markdown(f"##### {sel_style} Examples")
    for ex in style["examples"]:
        st.markdown(f"- **{ex['name']}** ({ex['country']}): {ex['notes']}")

    # Data table
    all_data = []
    for s in ARCHITECTURE_STYLES:
        for ex in s["examples"]:
            all_data.append({
                "style": s["name"],
                "name": ex["name"],
                "country": ex["country"],
                "lat": ex["lat"],
                "lon": ex["lon"],
                "notes": ex["notes"],
            })
    df = pd.DataFrame(all_data)
    st.dataframe(df, width="stretch")
    _csv_download(df, "lighthouse_architecture.csv")

    # Chart: count per style
    fig, ax = _dark_fig(figsize=(8, 4))
    style_names = [s["name"] for s in ARCHITECTURE_STYLES]
    counts = [len(s["examples"]) for s in ARCHITECTURE_STYLES]
    colors = [s["color"] for s in ARCHITECTURE_STYLES]
    ax.bar(range(len(style_names)), counts, color=colors, edgecolor="#2a3550")
    ax.set_xticks(range(len(style_names)))
    ax.set_xticklabels([n[:12] for n in style_names], rotation=45, ha="right", color="#e8ecf4")
    ax.set_ylabel("Examples")
    ax.set_title("Lighthouse Architecture Styles")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=700)


def _render_decommissioned():
    """Mode 7: Decommissioned & Ruins."""
    st.markdown("#### Decommissioned & Ruined Lighthouses")
    st.markdown(
        "Abandoned, decommissioned, and ruined lighthouses around the world. "
        "Many have been converted to hotels, museums, residences, or art spaces."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Listed", len(DECOMMISSIONED))
    with col2:
        converted = sum(1 for d in DECOMMISSIONED if "museum" in d["status"].lower() or "hotel" in d["notes"].lower() or "converted" in d["status"].lower() or "residency" in d["status"].lower())
        st.metric("Converted/Repurposed", converted)
    with col3:
        ruins = sum(1 for d in DECOMMISSIONED if "ruin" in d["status"].lower() or "Abandoned" in d["status"])
        st.metric("Abandoned/Ruins", ruins)

    # Map
    m = _make_base_map()
    for lh in DECOMMISSIONED:
        if "Abandoned" in lh["status"] or "ruin" in lh["status"].lower():
            color = "red"
            icon_name = "ban"
        elif "museum" in lh["status"].lower() or "converted" in lh["status"].lower() or "residency" in lh["status"].lower():
            color = "green"
            icon_name = "home"
        else:
            color = "orange"
            icon_name = "exclamation-triangle"

        popup_html = (
            f"<div style='min-width:240px;'>"
            f"<b>{escape(lh['name'])}</b><br>"
            f"<b>Country:</b> {escape(lh['country'])}<br>"
            f"<b>Year Built:</b> {lh['year']}<br>"
            f"<b>Status:</b> {escape(lh['status'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{escape(lh['notes'])}</i>"
            f"</div>"
        )
        folium.Marker(
            location=[lh["lat"], lh["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=escape(lh["name"]),
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Data table
    st.markdown("##### Decommissioned Lighthouses Data")
    df = pd.DataFrame(DECOMMISSIONED)
    col_order = ["name", "country", "year", "status", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "decommissioned_lighthouses.csv")


def _render_remote():
    """Mode 8: Remote & Extreme Lighthouses."""
    st.markdown("#### Remote & Extreme Lighthouses")
    st.markdown(
        "The most isolated, dangerous, and difficult-to-maintain lighthouses in the world. "
        "Wave-swept towers, Arctic outposts, and subantarctic beacons."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Extreme Lighthouses", len(REMOTE_LIGHTHOUSES))
    with col2:
        northernmost = max(REMOTE_LIGHTHOUSES, key=lambda x: x["lat"])
        st.metric("Northernmost", f"{northernmost['lat']:.1f} N", northernmost["name"][:20])
    with col3:
        southernmost = min(REMOTE_LIGHTHOUSES, key=lambda x: x["lat"])
        st.metric("Southernmost", f"{abs(southernmost['lat']):.1f} S", southernmost["name"][:20])

    # Map
    m = _make_base_map(lat=30.0, lon=-10.0, zoom=2)
    for lh in REMOTE_LIGHTHOUSES:
        popup_html = (
            f"<div style='min-width:260px;'>"
            f"<b>{escape(lh['name'])}</b><br>"
            f"<b>Country:</b> {escape(lh['country'])}<br>"
            f"<b>Year Built:</b> {lh['year']}<br>"
            f"<b>Isolation:</b> {escape(lh['isolation'])}<br>"
            f"<b>Danger:</b> <span style='color:#ef4444;'>{escape(lh['danger'])}</span><br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{escape(lh['notes'][:300])}</i>"
            f"</div>"
        )
        folium.Marker(
            location=[lh["lat"], lh["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=escape(lh["name"]),
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa"),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Danger cards
    st.markdown("##### Remote Lighthouse Profiles")
    for lh in REMOTE_LIGHTHOUSES:
        with st.expander(f"{lh['name']} ({lh['country']}, {lh['year']})"):
            st.markdown(f"**Isolation:** {lh['isolation']}")
            st.markdown(f"**Danger:** {lh['danger']}")
            st.write(lh["notes"])

    # Data table
    df = pd.DataFrame(REMOTE_LIGHTHOUSES)
    col_order = ["name", "country", "year", "isolation", "danger", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "remote_lighthouses.csv")


def _render_keepers():
    """Mode 9: Lighthouse Keepers' Stories."""
    st.markdown("#### Lighthouse Keepers' Stories")
    st.markdown(
        "The men and women who kept the lights burning through storms, isolation, "
        "and tragedy. Their stories of heroism, endurance, and sacrifice."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stories", len(KEEPER_STORIES))
    with col2:
        women = sum(1 for k in KEEPER_STORIES if k["keeper"] in [
            "Ida Lewis", "Grace Darling & William Darling", "Abigail Burgess",
            "Juliet Nichols", "Fanny Salter", "Kate Walker", "Harriet Colfax"
        ])
        st.metric("Women Keepers Featured", women)

    # Map
    m = _make_base_map(lat=48.0, lon=-20.0, zoom=3)
    for story in KEEPER_STORIES:
        popup_html = (
            f"<div style='min-width:260px;'>"
            f"<b>{escape(story['name'])}</b><br>"
            f"<b>Keeper:</b> {escape(story['keeper'])}<br>"
            f"<b>Period:</b> {escape(story['year_range'])}<br>"
            f"<b>Story:</b> <i>{escape(story['story'])}</i><br>"
            f"<hr style='margin:4px 0;'>"
            f"{escape(story['notes'][:250])}"
            f"</div>"
        )
        folium.Marker(
            location=[story["lat"], story["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{escape(story['keeper'])} - {escape(story['name'][:30])}",
            icon=folium.Icon(color="blue", icon="user", prefix="fa"),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Story cards
    st.markdown("##### Keeper Profiles")
    for story in KEEPER_STORIES:
        with st.expander(f"{story['keeper']} -- {story['story']} ({story['year_range']})"):
            st.markdown(f"**Location:** {story['name']}")
            st.markdown(f"**Country:** {story['country']}")
            st.write(story["notes"])

    # Data table
    st.markdown("##### Data Table")
    df = pd.DataFrame(KEEPER_STORIES)
    col_order = ["keeper", "name", "country", "year_range", "story", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "lighthouse_keepers.csv")


def _render_modern():
    """Mode 10: Modern Navigation."""
    st.markdown("#### Modern Navigation Systems")
    st.markdown(
        "LED lights, DGPS stations, AIS beacons, RACON transponders, VTMS systems, "
        "and eLoran transmitters -- the automated future of maritime navigation."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Systems Listed", len(MODERN_NAVIGATION))
    with col2:
        types = len(set(n["type"] for n in MODERN_NAVIGATION))
        st.metric("Technology Types", types)
    with col3:
        countries = len(set(n["country"] for n in MODERN_NAVIGATION))
        st.metric("Countries", countries)

    # Type filter
    all_types = sorted(set(n["type"] for n in MODERN_NAVIGATION))
    sel_type = st.selectbox("Filter by Technology", ["All"] + all_types, key="modern_type")

    filtered = MODERN_NAVIGATION
    if sel_type != "All":
        filtered = [n for n in MODERN_NAVIGATION if n["type"] == sel_type]

    st.info(f"Showing {len(filtered)} of {len(MODERN_NAVIGATION)} systems")

    # Overpass search for nearby navigation aids
    st.markdown("---")
    st.markdown("##### Search for Navigation Aids (Overpass API)")
    nav_cols = st.columns(3)
    with nav_cols[0]:
        nav_lat = st.number_input("Latitude", value=51.5, key="nav_lat")
    with nav_cols[1]:
        nav_lon = st.number_input("Longitude", value=1.5, key="nav_lon")
    with nav_cols[2]:
        nav_radius = st.number_input("Radius (km)", value=50, min_value=5, max_value=500, key="nav_radius")
    do_nav_search = st.button("Search Navigation Aids", key="nav_search")

    # Map
    m = _make_base_map(lat=30.0, lon=0.0, zoom=2)

    type_colors = {
        "DGPS Reference Station": "#06b6d4",
        "AIS Base Station": "#10b981",
        "Vessel Traffic Management System": "#f59e0b",
        "Radar Beacon (RACON)": "#8b5cf6",
        "LED Navigation Buoy": "#ec4899",
        "Automated AtoN System": "#ef4444",
        "Automated LED Lighthouse": "#f97316",
        "DGPS-Enhanced Navigation Buoy": "#3b82f6",
        "Marine Radio & NAVTEX Station": "#a855f7",
        "Automated Lighthouse + AIS": "#14b8a6",
        "Automated Texas Tower": "#64748b",
        "Automated Solar + LED": "#22d3ee",
        "E-Navigation Pilot Zone": "#facc15",
        "eLoran Transmitter": "#fb923c",
        "Canal AIS + VTS Integration": "#38bdf8",
        "Tri-National AIS Network": "#4ade80",
    }

    for nav in filtered:
        color = type_colors.get(nav["type"], "#06b6d4")
        popup_html = (
            f"<div style='min-width:240px;'>"
            f"<b>{escape(nav['name'])}</b><br>"
            f"<b>Country:</b> {escape(nav['country'])}<br>"
            f"<b>Type:</b> {escape(nav['type'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{escape(nav['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[nav["lat"], nav["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(nav['name'])} ({escape(nav['type'][:20])})",
        ).add_to(m)

    # Overpass results
    osm_features = []
    if do_nav_search:
        with st.spinner("Searching Overpass API for navigation aids..."):
            data = _overpass_navigation_aids(nav_lat, nav_lon, nav_radius)
            if data and "_error" not in data:
                elements = data.get("elements", [])
                fg = folium.FeatureGroup(name="OSM Navigation Aids")
                for el in elements:
                    lat_e = el.get("lat") or el.get("center", {}).get("lat")
                    lon_e = el.get("lon") or el.get("center", {}).get("lon")
                    if lat_e is None or lon_e is None:
                        continue
                    tags = el.get("tags", {})
                    name = tags.get("name", tags.get("seamark:name", "Unnamed"))
                    sm_type = tags.get("seamark:type", tags.get("man_made", "unknown"))
                    popup_html = (
                        f"<div style='min-width:180px;'>"
                        f"<b>{escape(name)}</b><br>"
                        f"<b>Type:</b> {escape(sm_type)}<br>"
                    )
                    for k in ["seamark:light:colour", "seamark:light:range", "height"]:
                        if k in tags:
                            popup_html += f"<b>{escape(k.split(':')[-1].title())}:</b> {escape(tags[k])}<br>"
                    popup_html += "</div>"
                    folium.CircleMarker(
                        location=[lat_e, lon_e],
                        radius=4,
                        color="#38bdf8",
                        fill=True,
                        fill_color="#38bdf8",
                        fill_opacity=0.7,
                        popup=folium.Popup(popup_html, max_width=280),
                        tooltip=escape(name),
                    ).add_to(fg)
                    osm_features.append({"name": name, "type": sm_type, "lat": lat_e, "lon": lon_e})
                fg.add_to(m)
                st.success(f"Found {len(osm_features)} navigation aids from OpenStreetMap.")
            elif data and "_error" in data:
                st.warning(f"Overpass error: {data['_error']}")

    folium.LayerControl().add_to(m)
    _render_map(m)

    if osm_features:
        st.markdown("##### OSM Navigation Aids Found")
        osm_df = pd.DataFrame(osm_features)
        st.dataframe(osm_df, width="stretch")

    # Data table
    st.markdown("##### Modern Navigation Systems Data")
    df = pd.DataFrame(filtered)
    col_order = ["name", "country", "type", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "modern_navigation.csv")

    # Chart: types breakdown
    fig, ax = _dark_fig(figsize=(10, 5))
    type_counts = {}
    for n in MODERN_NAVIGATION:
        t = n["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    t_names = [t[0][:25] for t in sorted_types]
    t_counts = [t[1] for t in sorted_types]
    t_colors = [type_colors.get(t[0], "#06b6d4") for t in sorted_types]
    ax.barh(t_names, t_counts, color=t_colors, edgecolor="#2a3550")
    ax.set_xlabel("Count")
    ax.set_title("Modern Navigation Systems by Type")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_lighthouse_maps_tab():
    """Main entry point for the Lighthouses & Beacons of the World tab."""
    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>\U0001f3e0 Lighthouses &amp; Beacons of the World</h4>'
        '<p>Historic lighthouses, navigation beacons, coastal landmarks &amp; 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    map_mode = st.selectbox("Select Lighthouse Map Mode", MAP_MODES, key="lighthouse_map_mode")

    st.markdown("---")

    if map_mode == "World's Most Famous Lighthouses":
        _render_famous()
    elif map_mode == "Ancient Lighthouses":
        _render_ancient()
    elif map_mode == "Lighthouses by Country":
        _render_by_country()
    elif map_mode == "Tallest Lighthouses":
        _render_tallest()
    elif map_mode == "Haunted Lighthouses":
        _render_haunted()
    elif map_mode == "Lighthouse Architecture":
        _render_architecture()
    elif map_mode == "Decommissioned & Ruins":
        _render_decommissioned()
    elif map_mode == "Remote & Extreme Lighthouses":
        _render_remote()
    elif map_mode == "Lighthouse Keepers' Stories":
        _render_keepers()
    elif map_mode == "Modern Navigation":
        _render_modern()
