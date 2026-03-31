# -*- coding: utf-8 -*-
"""
Maritime & Navigation Maps module for TerraScout AI.
Provides 10 thematic maritime map types covering lighthouses, shipwrecks,
strategic straits, ocean currents, naval battles, pirate history,
exploration voyages, marine protected areas, tidal phenomena,
and submarine volcanoes / hydrothermal vents.

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
MAP_TYPES = [
    "Historic Lighthouses",
    "Famous Shipwrecks",
    "Strategic Straits & Passages",
    "Ocean Currents",
    "Naval Battles",
    "Pirate History",
    "Exploration Voyages",
    "Coral Reefs & Marine Protected",
    "Tidal Phenomena",
    "Submarine Volcanoes & Hydrothermal",
]

# =====================================================================
# 1. HISTORIC LIGHTHOUSES DATA
# =====================================================================
LIGHTHOUSES = [
    {"name": "Pharos of Alexandria (site)", "lat": 31.2139, "lon": 29.8856, "country": "Egypt", "year": "280 BC", "height_m": 100, "range_nm": 30, "notes": "One of the Seven Wonders; destroyed by earthquakes"},
    {"name": "Tower of Hercules", "lat": 43.3861, "lon": -8.4064, "country": "Spain", "year": "2nd c.", "height_m": 55, "range_nm": 23, "notes": "Oldest working Roman lighthouse, UNESCO site"},
    {"name": "Hook Head Lighthouse", "lat": 52.1239, "lon": -6.9292, "country": "Ireland", "year": "1172", "height_m": 35, "range_nm": 23, "notes": "One of oldest operational lighthouses in the world"},
    {"name": "Lanterna di Genova", "lat": 44.4036, "lon": 8.9018, "country": "Italy", "year": "1128", "height_m": 77, "range_nm": 25, "notes": "Symbol of Genoa, oldest surviving lighthouse in Mediterranean"},
    {"name": "Eddystone Lighthouse", "lat": 50.1088, "lon": -4.1559, "country": "UK", "year": "1698", "height_m": 41, "range_nm": 17, "notes": "Four successive towers; current Smeaton's tower relocated"},
    {"name": "Portland Head Light", "lat": 43.6231, "lon": -70.2078, "country": "USA", "year": "1791", "height_m": 24, "range_nm": 15, "notes": "Oldest lighthouse in Maine, commissioned by George Washington"},
    {"name": "Cape Hatteras Lighthouse", "lat": 35.2505, "lon": -75.5288, "country": "USA", "year": "1870", "height_m": 64, "range_nm": 20, "notes": "Tallest brick lighthouse in the US; famously relocated in 1999"},
    {"name": "Boston Light", "lat": 42.3278, "lon": -70.8903, "country": "USA", "year": "1716", "height_m": 27, "range_nm": 16, "notes": "First lighthouse built in what became the United States"},
    {"name": "Cape Byron Lighthouse", "lat": -28.6356, "lon": 153.6386, "country": "Australia", "year": "1901", "height_m": 22, "range_nm": 25, "notes": "Easternmost point of Australia mainland"},
    {"name": "Bell Rock Lighthouse", "lat": 56.4341, "lon": -2.3869, "country": "UK", "year": "1811", "height_m": 35, "range_nm": 18, "notes": "Oldest surviving sea-washed lighthouse, engineering marvel"},
    {"name": "Fastnet Rock Lighthouse", "lat": 51.3833, "lon": -9.6000, "country": "Ireland", "year": "1854", "height_m": 49, "range_nm": 18, "notes": "Known as the Teardrop of Ireland, last sight of emigrants"},
    {"name": "Bishop Rock Lighthouse", "lat": 49.8727, "lon": -6.4444, "country": "UK", "year": "1858", "height_m": 44, "range_nm": 20, "notes": "Smallest island with a building, Guinness record"},
    {"name": "Cape Agulhas Lighthouse", "lat": -34.8317, "lon": 20.0106, "country": "South Africa", "year": "1849", "height_m": 27, "range_nm": 19, "notes": "Southernmost tip of Africa, where Indian and Atlantic oceans meet"},
    {"name": "Lindau Lighthouse", "lat": 47.5436, "lon": 9.6843, "country": "Germany", "year": "1856", "height_m": 33, "range_nm": 10, "notes": "Southernmost lighthouse in Germany, on Lake Constance"},
    {"name": "Phare de Cordouan", "lat": 45.5858, "lon": -1.1717, "country": "France", "year": "1611", "height_m": 68, "range_nm": 22, "notes": "Versailles of the Sea, oldest lighthouse in France, UNESCO"},
    {"name": "La Jument Lighthouse", "lat": 48.4228, "lon": -5.1311, "country": "France", "year": "1911", "height_m": 47, "range_nm": 22, "notes": "Famous stormy photograph location off Brittany"},
    {"name": "Kjeungskjaer Lighthouse", "lat": 63.8494, "lon": 10.0000, "country": "Norway", "year": "1880", "height_m": 21, "range_nm": 13, "notes": "Iconic red octagonal lighthouse on tiny islet"},
    {"name": "Peggy's Point Lighthouse", "lat": 44.4917, "lon": -63.9181, "country": "Canada", "year": "1915", "height_m": 15, "range_nm": 12, "notes": "Most photographed lighthouse in Canada, Nova Scotia icon"},
    {"name": "Cape Leeuwin Lighthouse", "lat": -34.3725, "lon": 115.1358, "country": "Australia", "year": "1895", "height_m": 39, "range_nm": 20, "notes": "Southwestern tip of Australia, meeting point of two oceans"},
    {"name": "Murano Lighthouse", "lat": 45.4567, "lon": 12.3517, "country": "Italy", "year": "1912", "height_m": 35, "range_nm": 15, "notes": "Guides ships into the Venetian Lagoon"},
    {"name": "Point Reyes Lighthouse", "lat": 37.9958, "lon": -123.0228, "country": "USA", "year": "1870", "height_m": 11, "range_nm": 24, "notes": "One of the windiest and foggiest points on the Pacific Coast"},
    {"name": "Gibbs Hill Lighthouse", "lat": 32.2494, "lon": -64.8356, "country": "Bermuda", "year": "1846", "height_m": 36, "range_nm": 26, "notes": "One of oldest cast-iron lighthouses in the world"},
    {"name": "St. Augustine Lighthouse", "lat": 29.8856, "lon": -81.2886, "country": "USA", "year": "1874", "height_m": 50, "range_nm": 19, "notes": "Oldest permanent aid to navigation in the US region"},
    {"name": "Pigeon Point Lighthouse", "lat": 37.1828, "lon": -122.3939, "country": "USA", "year": "1872", "height_m": 35, "range_nm": 18, "notes": "One of tallest lighthouses on the US West Coast"},
    {"name": "Europa Point Lighthouse", "lat": 36.1100, "lon": -5.3450, "country": "Gibraltar", "year": "1841", "height_m": 20, "range_nm": 19, "notes": "At the southern tip of Gibraltar, marking the strait entrance"},
    {"name": "Bengtskars Lighthouse", "lat": 59.7594, "lon": 22.5017, "country": "Finland", "year": "1906", "height_m": 52, "range_nm": 18, "notes": "Tallest lighthouse in Scandinavia"},
    {"name": "Cape Palliser Lighthouse", "lat": -41.6092, "lon": 175.2883, "country": "New Zealand", "year": "1897", "height_m": 18, "range_nm": 16, "notes": "Southernmost lighthouse on the North Island"},
    {"name": "Morro Castle Lighthouse", "lat": 23.1502, "lon": -82.3575, "country": "Cuba", "year": "1845", "height_m": 25, "range_nm": 18, "notes": "Built atop the famous Morro fortress, Havana harbour"},
    {"name": "Makapuu Point Lighthouse", "lat": 21.3103, "lon": -157.6472, "country": "USA (Hawaii)", "year": "1909", "height_m": 14, "range_nm": 28, "notes": "Largest lens-equipped lighthouse in the US, hyper-radial"},
    {"name": "Cape Race Lighthouse", "lat": 46.6569, "lon": -53.0731, "country": "Canada", "year": "1856", "height_m": 24, "range_nm": 16, "notes": "Received Titanic distress signal in 1912"},
    {"name": "Faro de Finisterre", "lat": 42.8828, "lon": -9.2722, "country": "Spain", "year": "1853", "height_m": 17, "range_nm": 23, "notes": "End of the Camino de Santiago, Costa da Morte"},
    {"name": "South Stack Lighthouse", "lat": 53.3058, "lon": -4.6992, "country": "UK (Wales)", "year": "1809", "height_m": 28, "range_nm": 20, "notes": "Built on dramatic cliff island off Anglesey"},
    {"name": "Beachy Head Lighthouse", "lat": 50.7364, "lon": 0.2433, "country": "UK", "year": "1902", "height_m": 43, "range_nm": 16, "notes": "Red-and-white striped, at base of famous chalk cliffs"},
    {"name": "Happisburgh Lighthouse", "lat": 52.8250, "lon": 1.5333, "country": "UK", "year": "1791", "height_m": 26, "range_nm": 14, "notes": "Oldest working lighthouse in East Anglia, threatened by erosion"},
    {"name": "Slettnes Lighthouse", "lat": 71.0892, "lon": 28.2108, "country": "Norway", "year": "1905", "height_m": 15, "range_nm": 18, "notes": "Northernmost mainland lighthouse in the world"},
    {"name": "Cape Point Lighthouse", "lat": -34.3564, "lon": 18.4972, "country": "South Africa", "year": "1860", "height_m": 87, "range_nm": 34, "notes": "One of most powerful lights in the world, near Cape of Good Hope"},
    {"name": "Les Eclaireurs Lighthouse", "lat": -54.8775, "lon": -68.0583, "country": "Argentina", "year": "1920", "height_m": 11, "range_nm": 7, "notes": "Often mistaken for End of the World lighthouse, Beagle Channel"},
    {"name": "Roter Sand Lighthouse", "lat": 53.8569, "lon": 8.0847, "country": "Germany", "year": "1885", "height_m": 28, "range_nm": 12, "notes": "First offshore lighthouse built on open sea in Germany"},
    {"name": "Cape Bonavista Lighthouse", "lat": 48.6983, "lon": -53.0833, "country": "Canada", "year": "1843", "height_m": 15, "range_nm": 12, "notes": "Near John Cabot's 1497 landfall site in Newfoundland"},
    {"name": "Rattray Head Lighthouse", "lat": 57.6114, "lon": -1.8183, "country": "UK (Scotland)", "year": "1895", "height_m": 34, "range_nm": 18, "notes": "Remote lighthouse on Scotland's northeast coast"},
    {"name": "Jeddah Light", "lat": 21.4967, "lon": 39.1522, "country": "Saudi Arabia", "year": "1990", "height_m": 133, "range_nm": 25, "notes": "Tallest lighthouse in the world"},
    {"name": "Yokohama Marine Tower", "lat": 35.4433, "lon": 139.6522, "country": "Japan", "year": "1961", "height_m": 106, "range_nm": 20, "notes": "Once tallest lighthouse in the world, iconic landmark"},
]

LIGHTHOUSE_SEARCH_REGIONS = {
    "Custom Area": None,
    "North Sea & English Channel": {"lat": 51.5, "lon": 1.5, "radius": 200},
    "Mediterranean": {"lat": 37.0, "lon": 15.0, "radius": 300},
    "US East Coast": {"lat": 40.0, "lon": -73.0, "radius": 300},
    "Scandinavia": {"lat": 60.0, "lon": 10.0, "radius": 300},
    "Japan & Korea": {"lat": 35.0, "lon": 132.0, "radius": 300},
    "Australia & NZ": {"lat": -35.0, "lon": 150.0, "radius": 400},
    "Caribbean": {"lat": 18.0, "lon": -70.0, "radius": 400},
    "British Isles": {"lat": 54.0, "lon": -3.0, "radius": 250},
    "West Africa": {"lat": 15.0, "lon": -17.0, "radius": 300},
}

# =====================================================================
# 2. FAMOUS SHIPWRECKS DATA
# =====================================================================
SHIPWRECKS = [
    {"name": "RMS Titanic", "lat": 41.7260, "lon": -49.9469, "year": 1912, "depth_m": 3800, "cause": "Iceberg collision", "casualties": 1517, "notes": "Most famous shipwreck in history"},
    {"name": "Bismarck", "lat": 48.9167, "lon": -16.2000, "year": 1941, "depth_m": 4791, "cause": "Scuttled after battle damage", "casualties": 2104, "notes": "German battleship, sunk in the Atlantic"},
    {"name": "RMS Lusitania", "lat": 51.3833, "lon": -8.5500, "year": 1915, "depth_m": 93, "cause": "Torpedoed by U-20", "casualties": 1198, "notes": "Helped draw US into WWI"},
    {"name": "Mary Rose", "lat": 50.7639, "lon": -1.1058, "year": 1545, "depth_m": 12, "cause": "Capsized in battle", "casualties": 400, "notes": "Henry VIII's warship, raised in 1982"},
    {"name": "Vasa", "lat": 59.3275, "lon": 18.0917, "year": 1628, "depth_m": 32, "cause": "Capsized on maiden voyage", "casualties": 30, "notes": "Raised intact 1961, now a museum in Stockholm"},
    {"name": "SS Andrea Doria", "lat": 40.2958, "lon": -69.8517, "year": 1956, "depth_m": 73, "cause": "Collision with MS Stockholm", "casualties": 46, "notes": "Mount Everest of scuba diving"},
    {"name": "SS Edmund Fitzgerald", "lat": 46.9988, "lon": -85.1128, "year": 1975, "depth_m": 160, "cause": "Storm, structural failure", "casualties": 29, "notes": "Largest ship to sink on the Great Lakes"},
    {"name": "Costa Concordia", "lat": 42.3628, "lon": 10.9219, "year": 2012, "depth_m": 30, "cause": "Ran aground on reef", "casualties": 32, "notes": "Captain abandoned ship before passengers"},
    {"name": "SMS Scharnhorst", "lat": -52.4333, "lon": -57.9000, "year": 1914, "depth_m": 1600, "cause": "Battle of the Falkland Islands", "casualties": 860, "notes": "German armoured cruiser, found 2019"},
    {"name": "USS Arizona", "lat": 21.3647, "lon": -157.9500, "year": 1941, "depth_m": 12, "cause": "Japanese air attack (Pearl Harbor)", "casualties": 1177, "notes": "Now a memorial, still leaks oil"},
    {"name": "HMS Hood", "lat": 63.3333, "lon": -31.8667, "year": 1941, "depth_m": 2800, "cause": "Magazine explosion from Bismarck hit", "casualties": 1415, "notes": "Pride of the Royal Navy, only 3 survivors"},
    {"name": "RMS Empress of Ireland", "lat": 48.6267, "lon": -68.3833, "year": 1914, "depth_m": 40, "cause": "Collision with SS Storstad in fog", "casualties": 1012, "notes": "Worst Canadian maritime disaster"},
    {"name": "General Slocum", "lat": 40.7900, "lon": -73.9350, "year": 1904, "depth_m": 8, "cause": "Fire on board", "casualties": 1021, "notes": "Worst NYC disaster until 9/11"},
    {"name": "MV Wilhelm Gustloff", "lat": 55.0667, "lon": 17.4167, "year": 1945, "depth_m": 44, "cause": "Torpedoed by Soviet sub S-13", "casualties": 9343, "notes": "Deadliest maritime disaster in history"},
    {"name": "MV Dona Paz", "lat": 12.2833, "lon": 121.7833, "year": 1987, "depth_m": 545, "cause": "Collision with oil tanker", "casualties": 4386, "notes": "Deadliest peacetime maritime disaster"},
    {"name": "SS Eastland", "lat": 41.8869, "lon": -87.6333, "year": 1915, "depth_m": 6, "cause": "Capsized at dock", "casualties": 844, "notes": "Rolled over in Chicago River"},
    {"name": "HMS Erebus", "lat": 68.2144, "lon": -98.8539, "year": 1848, "depth_m": 11, "cause": "Ice-trapped, abandoned (Franklin expedition)", "casualties": 129, "notes": "Found 2014, Parks Canada archaeological site"},
    {"name": "Whydah Gally", "lat": 41.6500, "lon": -69.9500, "year": 1717, "depth_m": 5, "cause": "Nor'easter storm off Cape Cod", "casualties": 143, "notes": "Only verified pirate shipwreck ever found"},
    {"name": "SS Central America", "lat": 31.7500, "lon": -77.1000, "year": 1857, "depth_m": 2200, "cause": "Hurricane", "casualties": 425, "notes": "Ship of Gold, $150M+ in gold recovered"},
    {"name": "Nuestra Senora de Atocha", "lat": 24.5139, "lon": -82.1917, "year": 1622, "depth_m": 16, "cause": "Hurricane off Florida Keys", "casualties": 260, "notes": "Mel Fisher's famous treasure find, $450M"},
    {"name": "ARA General Belgrano", "lat": -55.2833, "lon": -61.0500, "year": 1982, "depth_m": 93, "cause": "Torpedoed by HMS Conqueror (Falklands War)", "casualties": 323, "notes": "Most controversial sinking since WWII"},
    {"name": "HMHS Britannic", "lat": 37.7283, "lon": 24.2833, "year": 1916, "depth_m": 120, "cause": "Mine or torpedo in Kea Channel", "casualties": 30, "notes": "Titanic's sister ship, largest ship sunk in WWI"},
    {"name": "SS Arctic", "lat": 46.8000, "lon": -48.5000, "year": 1854, "depth_m": 60, "cause": "Collision with SS Vesta in fog", "casualties": 350, "notes": "Early transatlantic disaster, women and children denied lifeboats"},
    {"name": "MS Estonia", "lat": 59.3833, "lon": 21.7667, "year": 1994, "depth_m": 80, "cause": "Bow visor failure in storm", "casualties": 852, "notes": "Worst European maritime disaster in peacetime since WWII"},
    {"name": "Sultana", "lat": 35.2167, "lon": -90.0667, "year": 1865, "depth_m": 5, "cause": "Boiler explosion on Mississippi", "casualties": 1168, "notes": "Worst US maritime disaster, Union POWs returning home"},
    {"name": "HMS Victory (1744)", "lat": 49.3500, "lon": -4.8500, "year": 1744, "depth_m": 75, "cause": "Storm in the English Channel", "casualties": 1100, "notes": "Not Nelson's ship; lost with all hands, found 2009"},
    {"name": "Tek Sing", "lat": 1.7667, "lon": 106.5833, "year": 1822, "depth_m": 30, "cause": "Struck reef in Gaspar Strait", "casualties": 1600, "notes": "Chinese junk, Titanic of the East, massive porcelain cargo"},
    {"name": "SS Thistlegorm", "lat": 27.8133, "lon": 33.9228, "year": 1941, "depth_m": 30, "cause": "German bombers in Red Sea", "casualties": 9, "notes": "One of world's best wreck dives, full military cargo"},
    {"name": "RMS Carpathia", "lat": 49.3333, "lon": -10.5667, "year": 1918, "depth_m": 155, "cause": "Torpedoed by U-55", "casualties": 5, "notes": "Rescued Titanic survivors, later sunk in WWI"},
    {"name": "Batavia", "lat": -28.4833, "lon": 113.7833, "year": 1629, "depth_m": 5, "cause": "Struck reef in Abrolhos Islands", "casualties": 125, "notes": "Mutiny and mass murder followed the wreck"},
    {"name": "San Jose Galleon", "lat": 10.3833, "lon": -75.8167, "year": 1708, "depth_m": 600, "cause": "British attack off Cartagena", "casualties": 578, "notes": "Possibly $17 billion treasure still on board"},
    {"name": "SS Yongala", "lat": -19.3056, "lon": 147.6222, "year": 1911, "depth_m": 30, "cause": "Cyclone off Queensland", "casualties": 122, "notes": "Australia's premier wreck dive"},
    {"name": "Endurance", "lat": -68.7500, "lon": -52.3333, "year": 1915, "depth_m": 3008, "cause": "Crushed by Antarctic pack ice", "casualties": 0, "notes": "Shackleton's ship, found 2022 in remarkable condition"},
    {"name": "USS Indianapolis", "lat": 12.0333, "lon": 134.8167, "year": 1945, "depth_m": 5500, "cause": "Torpedoed by I-58 submarine", "casualties": 879, "notes": "Worst shark attack in history, crew in water 5 days"},
    {"name": "Kronan", "lat": 56.2667, "lon": 16.3333, "year": 1676, "depth_m": 26, "cause": "Capsized and exploded, Battle of Oland", "casualties": 800, "notes": "Swedish warship, rival to Vasa in importance"},
    {"name": "MV Derbyshire", "lat": 25.3000, "lon": 130.8000, "year": 1980, "depth_m": 4000, "cause": "Typhoon Orchid", "casualties": 44, "notes": "Largest British ship ever lost at sea"},
    {"name": "SS Waratah", "lat": -33.0000, "lon": 29.5000, "year": 1909, "depth_m": 0, "cause": "Vanished without trace", "casualties": 211, "notes": "Australia's Titanic, never found"},
    {"name": "Yamato", "lat": 30.7167, "lon": 128.0667, "year": 1945, "depth_m": 340, "cause": "US carrier aircraft (Operation Ten-Go)", "casualties": 3055, "notes": "Largest battleship ever built, sunk on suicide mission"},
    {"name": "Belgica", "lat": -71.3167, "lon": -85.5000, "year": 1940, "depth_m": 0, "cause": "Scuttled in Norway (original expedition 1897-99)", "casualties": 0, "notes": "First expedition to overwinter in Antarctica"},
    {"name": "MV Sewol", "lat": 34.1667, "lon": 125.9500, "year": 2014, "depth_m": 44, "cause": "Capsized due to cargo shift", "casualties": 304, "notes": "South Korean ferry, mostly Danwon High School students"},
]

# =====================================================================
# 3. STRATEGIC STRAITS & PASSAGES DATA
# =====================================================================
STRAITS = [
    {"name": "Strait of Hormuz", "coords": [[26.6, 56.2], [26.0, 56.5], [26.5, 57.0]], "daily_ships": 2000, "width_km": 54, "notes": "21% of global oil passes through; Iran/Oman"},
    {"name": "Strait of Malacca", "coords": [[4.3, 100.0], [2.5, 101.5], [1.3, 103.8]], "daily_ships": 250, "width_km": 65, "notes": "Shortest route between Indian and Pacific; 25% of trade"},
    {"name": "Strait of Gibraltar", "coords": [[35.9, -5.7], [35.96, -5.4], [35.9, -5.3]], "daily_ships": 300, "width_km": 14, "notes": "Atlantic-Mediterranean gateway; Spain/Morocco"},
    {"name": "Bab-el-Mandeb", "coords": [[12.6, 43.3], [12.5, 43.5], [12.4, 43.7]], "daily_ships": 150, "width_km": 26, "notes": "Red Sea chokepoint; Yemen/Djibouti; critical for Suez route"},
    {"name": "Bosphorus", "coords": [[41.22, 29.0], [41.12, 29.05], [41.02, 29.02]], "daily_ships": 130, "width_km": 0.7, "notes": "World's narrowest strait for international navigation"},
    {"name": "Dardanelles", "coords": [[40.4, 26.4], [40.2, 26.5], [40.1, 26.7]], "daily_ships": 120, "width_km": 1.2, "notes": "Links Sea of Marmara to Aegean; Gallipoli history"},
    {"name": "English Channel", "coords": [[50.8, -1.5], [50.4, 0.0], [50.9, 1.5]], "daily_ships": 500, "width_km": 34, "notes": "World's busiest shipping lane; Dover-Calais narrowest point"},
    {"name": "Strait of Dover", "coords": [[51.1, 1.5], [51.0, 1.7], [50.9, 1.9]], "daily_ships": 400, "width_km": 34, "notes": "Narrowest point of the English Channel"},
    {"name": "Panama Canal", "coords": [[9.38, -79.92], [9.20, -79.75], [9.00, -79.55]], "daily_ships": 40, "width_km": 0.2, "notes": "82 km canal; 6% of world trade; ~14,000 vessels/year"},
    {"name": "Suez Canal", "coords": [[31.28, 32.34], [30.58, 32.33], [29.95, 32.57]], "daily_ships": 55, "width_km": 0.2, "notes": "193 km canal; 12% of world trade; no locks"},
    {"name": "Strait of Taiwan", "coords": [[25.0, 120.5], [23.5, 119.5], [22.0, 118.5]], "daily_ships": 270, "width_km": 130, "notes": "Major shipping lane between China and Taiwan"},
    {"name": "Strait of Messina", "coords": [[38.3, 15.6], [38.2, 15.65], [38.1, 15.7]], "daily_ships": 80, "width_km": 3.1, "notes": "Between Sicily and mainland Italy; Scylla and Charybdis"},
    {"name": "Strait of Magellan", "coords": [[-53.5, -72.0], [-53.8, -71.0], [-52.5, -70.0]], "daily_ships": 5, "width_km": 3, "notes": "Historic passage around South America; 570 km long"},
    {"name": "Strait of Sunda", "coords": [[-6.1, 105.8], [-6.3, 105.5], [-6.5, 105.2]], "daily_ships": 70, "width_km": 24, "notes": "Between Java and Sumatra; Krakatoa eruption site"},
    {"name": "Strait of Lombok", "coords": [[-8.3, 115.7], [-8.5, 115.8], [-8.7, 116.0]], "daily_ships": 50, "width_km": 35, "notes": "Alternative to Malacca for deep-draft vessels"},
    {"name": "Torres Strait", "coords": [[-10.3, 142.0], [-10.5, 142.5], [-10.7, 143.0]], "daily_ships": 25, "width_km": 150, "notes": "Between Australia and Papua New Guinea; reef-filled"},
    {"name": "Strait of Bonifacio", "coords": [[41.3, 9.1], [41.2, 9.2], [41.15, 9.35]], "daily_ships": 40, "width_km": 11, "notes": "Between Corsica and Sardinia; strong currents"},
    {"name": "Oresund (The Sound)", "coords": [[55.9, 12.6], [55.7, 12.7], [55.5, 12.8]], "daily_ships": 90, "width_km": 4, "notes": "Baltic Sea entrance; Denmark/Sweden; famous bridge"},
    {"name": "Strait of Korea (Tsushima)", "coords": [[34.0, 129.0], [34.5, 129.5], [35.0, 130.0]], "daily_ships": 200, "width_km": 200, "notes": "Between Japan and South Korea; Battle of Tsushima 1905"},
    {"name": "Cape of Good Hope", "coords": [[-34.3, 18.5], [-35.0, 19.0], [-34.8, 20.0]], "daily_ships": 30, "width_km": 0, "notes": "Historic route between Atlantic and Indian oceans"},
    {"name": "Northwest Passage", "coords": [[74.0, -95.0], [72.0, -105.0], [69.0, -120.0]], "daily_ships": 1, "width_km": 0, "notes": "Arctic route; becoming navigable due to ice melt"},
    {"name": "Mozambique Channel", "coords": [[-15.0, 42.0], [-18.0, 43.0], [-21.0, 44.0]], "daily_ships": 20, "width_km": 460, "notes": "Between Mozambique and Madagascar; oil tanker route"},
]

# =====================================================================
# 4. OCEAN CURRENTS DATA
# =====================================================================
OCEAN_CURRENTS = [
    {"name": "Gulf Stream", "coords": [[25.0, -80.0], [30.0, -78.0], [35.0, -72.0], [40.0, -60.0], [45.0, -45.0], [50.0, -30.0]], "temp_c": "20-28", "speed_kts": 2.5, "direction": "NE", "color": "#ef4444", "notes": "Warms Western Europe; discovered by Ponce de Leon 1513"},
    {"name": "North Atlantic Drift", "coords": [[50.0, -30.0], [55.0, -15.0], [60.0, -5.0], [65.0, 5.0]], "temp_c": "8-12", "speed_kts": 0.5, "direction": "NE", "color": "#f59e0b", "notes": "Extension of Gulf Stream; keeps NW Europe mild"},
    {"name": "Kuroshio Current", "coords": [[18.0, 122.0], [25.0, 125.0], [30.0, 130.0], [35.0, 140.0], [40.0, 150.0]], "temp_c": "20-28", "speed_kts": 2.0, "direction": "NE", "color": "#dc2626", "notes": "Pacific equivalent of Gulf Stream; Japan Current"},
    {"name": "Antarctic Circumpolar Current", "coords": [[-55.0, -70.0], [-55.0, -30.0], [-55.0, 10.0], [-55.0, 50.0], [-55.0, 90.0], [-55.0, 130.0], [-55.0, 170.0], [-55.0, -170.0], [-55.0, -130.0], [-55.0, -100.0], [-55.0, -70.0]], "temp_c": "0-5", "speed_kts": 0.5, "direction": "E", "color": "#3b82f6", "notes": "Largest ocean current; 130 million m3/s; connects all oceans"},
    {"name": "Humboldt (Peru) Current", "coords": [[-45.0, -75.0], [-35.0, -73.0], [-25.0, -72.0], [-15.0, -76.0], [-5.0, -82.0]], "temp_c": "7-18", "speed_kts": 0.5, "direction": "N", "color": "#06b6d4", "notes": "Cold upwelling; world's most productive marine ecosystem"},
    {"name": "Benguela Current", "coords": [[-35.0, 17.0], [-28.0, 14.0], [-20.0, 12.0], [-12.0, 12.5]], "temp_c": "10-18", "speed_kts": 0.5, "direction": "N", "color": "#0ea5e9", "notes": "Cold current off SW Africa; rich fishing grounds"},
    {"name": "Agulhas Current", "coords": [[-27.0, 33.0], [-30.0, 31.0], [-34.0, 27.0], [-37.0, 22.0]], "temp_c": "22-27", "speed_kts": 1.5, "direction": "SW", "color": "#ef4444", "notes": "Strongest western boundary current; rogue wave zone"},
    {"name": "California Current", "coords": [[48.0, -125.0], [42.0, -125.0], [36.0, -123.0], [30.0, -118.0], [24.0, -114.0]], "temp_c": "10-16", "speed_kts": 0.3, "direction": "S", "color": "#22d3ee", "notes": "Cold eastern boundary current; fog generator"},
    {"name": "Labrador Current", "coords": [[60.0, -60.0], [55.0, -55.0], [50.0, -52.0], [45.0, -50.0], [41.0, -49.0]], "temp_c": "-1-5", "speed_kts": 0.3, "direction": "S", "color": "#818cf8", "notes": "Carries icebergs south; Titanic sinking zone"},
    {"name": "North Equatorial Current", "coords": [[15.0, -75.0], [15.0, -55.0], [15.0, -35.0], [15.0, -15.0]], "temp_c": "25-28", "speed_kts": 0.5, "direction": "W", "color": "#f97316", "notes": "Trade wind-driven; feeds into Gulf Stream system"},
    {"name": "South Equatorial Current", "coords": [[-5.0, -30.0], [-5.0, -10.0], [-5.0, 10.0], [-5.0, 30.0]], "temp_c": "25-28", "speed_kts": 0.7, "direction": "W", "color": "#fb923c", "notes": "Feeds Agulhas and Brazil currents"},
    {"name": "Brazil Current", "coords": [[-5.0, -35.0], [-15.0, -38.0], [-25.0, -44.0], [-35.0, -50.0]], "temp_c": "18-27", "speed_kts": 0.5, "direction": "S", "color": "#f43f5e", "notes": "Warm western boundary current along Brazil"},
    {"name": "East Australian Current", "coords": [[-15.0, 155.0], [-25.0, 155.0], [-35.0, 152.0], [-40.0, 150.0]], "temp_c": "20-26", "speed_kts": 1.0, "direction": "S", "color": "#e11d48", "notes": "Feeds Tasman Sea; Finding Nemo reference"},
    {"name": "Canary Current", "coords": [[35.0, -10.0], [30.0, -12.0], [25.0, -16.0], [20.0, -18.0]], "temp_c": "15-20", "speed_kts": 0.3, "direction": "S", "color": "#67e8f9", "notes": "Cool current off NW Africa; upwelling zone"},
    {"name": "Oyashio Current", "coords": [[55.0, 160.0], [50.0, 155.0], [45.0, 150.0], [40.0, 145.0]], "temp_c": "2-8", "speed_kts": 0.5, "direction": "SW", "color": "#a78bfa", "notes": "Cold nutrient-rich current; meets Kuroshio off Japan"},
    {"name": "Somali Current", "coords": [[-2.0, 43.0], [5.0, 47.0], [10.0, 52.0]], "temp_c": "20-28", "speed_kts": 2.0, "direction": "NE (summer)", "color": "#f472b6", "notes": "Reverses direction with monsoon; unique seasonal behavior"},
    {"name": "West Wind Drift", "coords": [[-45.0, 170.0], [-45.0, -170.0], [-45.0, -140.0], [-45.0, -110.0]], "temp_c": "5-12", "speed_kts": 0.3, "direction": "E", "color": "#94a3b8", "notes": "Northern boundary of Southern Ocean circulation"},
]

# =====================================================================
# 5. NAVAL BATTLES DATA
# =====================================================================
NAVAL_BATTLES = [
    {"name": "Battle of Salamis", "lat": 37.9600, "lon": 23.5900, "year": -480, "forces": "Greek city-states vs Persian Empire", "outcome": "Decisive Greek victory", "notes": "Saved Greek civilization; Themistocles' strategy"},
    {"name": "Battle of Actium", "lat": 38.9500, "lon": 20.7200, "year": -31, "forces": "Octavian vs Antony & Cleopatra", "outcome": "Octavian victory", "notes": "End of Roman Republic, birth of Roman Empire"},
    {"name": "Battle of Lepanto", "lat": 38.3700, "lon": 21.2500, "year": 1571, "forces": "Holy League vs Ottoman Empire", "outcome": "Holy League victory", "notes": "Last great galley battle; halted Ottoman expansion west"},
    {"name": "Spanish Armada", "lat": 50.3500, "lon": -4.5000, "year": 1588, "forces": "England vs Spain", "outcome": "English victory / storm", "notes": "Protestant Wind; changed European power balance"},
    {"name": "Battle of the Nile (Aboukir Bay)", "lat": 31.3500, "lon": 30.0700, "year": 1798, "forces": "Royal Navy vs French Navy", "outcome": "Decisive British victory", "notes": "Nelson destroyed Napoleon's fleet; stranded French army"},
    {"name": "Battle of Trafalgar", "lat": 36.1833, "lon": -6.2500, "year": 1805, "forces": "Royal Navy vs Franco-Spanish fleet", "outcome": "Decisive British victory", "notes": "Nelson killed; British naval supremacy for a century"},
    {"name": "Battle of Tsushima", "lat": 34.5000, "lon": 129.5000, "year": 1905, "forces": "Imperial Japanese Navy vs Russian Baltic Fleet", "outcome": "Japanese victory", "notes": "First modern naval battle; Russia lost 21 of 38 ships"},
    {"name": "Battle of Jutland", "lat": 57.0500, "lon": 6.1200, "year": 1916, "forces": "Royal Navy vs Imperial German Navy", "outcome": "Inconclusive / strategic British victory", "notes": "Largest WWI naval battle; 250 ships involved"},
    {"name": "Battle of Midway", "lat": 28.2000, "lon": -177.3500, "year": 1942, "forces": "US Navy vs Imperial Japanese Navy", "outcome": "Decisive US victory", "notes": "Turning point of Pacific War; Japan lost 4 carriers"},
    {"name": "Battle of the Coral Sea", "lat": -15.5000, "lon": 152.0000, "year": 1942, "forces": "US/Australia vs Japan", "outcome": "Tactical Japanese, strategic Allied victory", "notes": "First carrier vs carrier battle; ships never saw each other"},
    {"name": "Attack on Pearl Harbor", "lat": 21.3650, "lon": -157.9500, "year": 1941, "forces": "Japan vs United States", "outcome": "Japanese tactical victory", "notes": "Day of Infamy; brought US into WWII"},
    {"name": "Battle of the Philippine Sea", "lat": 15.0000, "lon": 138.0000, "year": 1944, "forces": "US Navy vs Imperial Japanese Navy", "outcome": "Decisive US victory", "notes": "Great Marianas Turkey Shoot; Japan lost 3 carriers"},
    {"name": "Battle of Leyte Gulf", "lat": 11.0000, "lon": 126.0000, "year": 1944, "forces": "US/Australia vs Japan", "outcome": "Allied victory", "notes": "Largest naval battle in history; first kamikaze attacks"},
    {"name": "Battle of the Atlantic", "lat": 52.0000, "lon": -30.0000, "year": 1943, "forces": "Allies vs German U-boats", "outcome": "Allied victory", "notes": "Longest campaign of WWII; 1939-1945; 3,500 ships lost"},
    {"name": "Battle of Chesapeake", "lat": 36.9700, "lon": -75.9600, "year": 1781, "forces": "French Navy vs Royal Navy", "outcome": "French victory", "notes": "Led directly to British surrender at Yorktown"},
    {"name": "Battle of Hampton Roads", "lat": 36.9800, "lon": -76.3300, "year": 1862, "forces": "USS Monitor vs CSS Virginia", "outcome": "Inconclusive", "notes": "First battle of ironclad warships; changed naval warfare"},
    {"name": "Battle of the Nile (modern)", "lat": 31.3500, "lon": 30.0700, "year": 1798, "forces": "British vs French", "outcome": "British victory", "notes": "Nelson destroyed French Mediterranean fleet at anchor"},
    {"name": "Battle of Navarino", "lat": 36.9300, "lon": 21.6800, "year": 1827, "forces": "British/French/Russian vs Ottoman/Egyptian", "outcome": "Allied victory", "notes": "Last significant naval battle fought entirely with sailing ships"},
    {"name": "Battle of Manila Bay", "lat": 14.5500, "lon": 120.9000, "year": 1898, "forces": "US Navy vs Spanish Navy", "outcome": "US victory", "notes": "Dewey destroyed Spanish Pacific fleet; US became Pacific power"},
    {"name": "Battle of Santiago de Cuba", "lat": 19.9700, "lon": -75.8700, "year": 1898, "forces": "US Navy vs Spanish Navy", "outcome": "US victory", "notes": "Destroyed Spain's Caribbean fleet; ended Spanish-American War at sea"},
    {"name": "Battle of the Java Sea", "lat": -6.0000, "lon": 112.0000, "year": 1942, "forces": "ABDA vs Imperial Japanese Navy", "outcome": "Japanese victory", "notes": "Japan seized Dutch East Indies; ABDA fleet destroyed"},
    {"name": "Battle of Surigao Strait", "lat": 10.0000, "lon": 125.5000, "year": 1944, "forces": "US Navy vs Imperial Japanese Navy", "outcome": "US victory", "notes": "Last battleship-vs-battleship engagement in history"},
    {"name": "Battle of Cape Matapan", "lat": 36.4000, "lon": 21.0000, "year": 1941, "forces": "Royal Navy vs Italian Navy", "outcome": "British victory", "notes": "Established British dominance in Eastern Mediterranean"},
    {"name": "Battle of the Denmark Strait", "lat": 63.3300, "lon": -31.8700, "year": 1941, "forces": "Royal Navy vs Bismarck & Prinz Eugen", "outcome": "German tactical victory", "notes": "HMS Hood destroyed; led to hunt for Bismarck"},
    {"name": "Battle of River Plate", "lat": -34.8000, "lon": -56.0000, "year": 1939, "forces": "Royal Navy vs Graf Spee", "outcome": "British strategic victory", "notes": "First major naval battle of WWII; Graf Spee scuttled"},
    {"name": "Battle of Gravelines", "lat": 51.0100, "lon": 2.1300, "year": 1588, "forces": "English fleet vs Spanish Armada", "outcome": "English victory", "notes": "Fireships scattered the Armada; decisive engagement"},
    {"name": "Battle of the Falkland Islands", "lat": -51.7500, "lon": -59.0000, "year": 1914, "forces": "Royal Navy vs Imperial German Navy", "outcome": "British victory", "notes": "Revenge for Battle of Coronel; von Spee's squadron destroyed"},
    {"name": "Battle of the Yellow Sea", "lat": 38.3000, "lon": 122.5000, "year": 1904, "forces": "Japan vs Russia", "outcome": "Japanese victory", "notes": "Russo-Japanese War; Russians retreated to Port Arthur"},
    {"name": "Battle of Texel", "lat": 53.0000, "lon": 4.5000, "year": 1673, "forces": "Dutch vs Anglo-French", "outcome": "Dutch victory", "notes": "De Ruyter prevented invasion of Netherlands"},
    {"name": "Battle of the Chesme", "lat": 38.3200, "lon": 26.3000, "year": 1770, "forces": "Russian Empire vs Ottoman Empire", "outcome": "Russian victory", "notes": "Russian fleet destroyed Ottoman fleet in harbor"},
    {"name": "Battle of Cape Ecnomus", "lat": 37.0500, "lon": 13.7500, "year": -256, "forces": "Roman Republic vs Carthage", "outcome": "Roman victory", "notes": "One of largest naval battles in history; ~680 ships total"},
    {"name": "Battle of Myeongnyang", "lat": 34.5700, "lon": 126.3100, "year": 1597, "forces": "Korean Navy vs Japanese Navy", "outcome": "Korean victory", "notes": "Admiral Yi Sun-sin; 13 ships defeated 133"},
]

# =====================================================================
# 6. PIRATE HISTORY DATA
# =====================================================================
PIRATE_HOTSPOTS = [
    {"name": "Nassau, Bahamas (Pirate Republic)", "lat": 25.0480, "lon": -77.3554, "era": "1706-1718", "pirates": "Blackbeard, Charles Vane, Jack Rackham, Anne Bonny", "notes": "Capital of the Republic of Pirates; Woodes Rogers ended it"},
    {"name": "Port Royal, Jamaica", "lat": 17.9367, "lon": -76.8417, "era": "1655-1692", "pirates": "Henry Morgan, Calico Jack", "notes": "Wickedest City on Earth; destroyed by earthquake 1692"},
    {"name": "Tortuga, Haiti", "lat": 20.0456, "lon": -72.7856, "era": "1630-1700", "pirates": "L'Olonnais, Pierre le Grand", "notes": "French buccaneer stronghold; natural harbor fortress"},
    {"name": "Barbary Coast (Algiers)", "lat": 36.7538, "lon": 3.0588, "era": "1500-1830", "pirates": "Barbarossa brothers, Dragut", "notes": "State-sponsored piracy; Europeans enslaved"},
    {"name": "Barbary Coast (Tunis)", "lat": 36.8065, "lon": 10.1815, "era": "1500-1830", "pirates": "Hayreddin Barbarossa, Sinan Reis", "notes": "Ottoman-backed corsairs; US Marines fought here"},
    {"name": "Barbary Coast (Tripoli)", "lat": 32.9022, "lon": 13.1800, "era": "1500-1830", "pirates": "Murad Reis, Dragut", "notes": "First Barbary War (1801); shores of Tripoli"},
    {"name": "Madagascar (Ile Sainte-Marie)", "lat": -17.0833, "lon": 49.8500, "era": "1690-1730", "pirates": "William Kidd, Henry Every, Thomas Tew", "notes": "Pirate haven on Indian Ocean trade routes"},
    {"name": "Somali Coast", "lat": 5.1521, "lon": 46.1996, "era": "2000-present", "pirates": "Modern Somali pirates", "notes": "Gulf of Aden hijackings; international naval patrols"},
    {"name": "Strait of Malacca", "lat": 2.5000, "lon": 101.5000, "era": "1400-present", "pirates": "Various Malay pirates; modern incidents", "notes": "One of most pirated waterways historically and today"},
    {"name": "South China Sea", "lat": 20.0000, "lon": 114.0000, "era": "1790-1810", "pirates": "Ching Shih, Zheng Yi", "notes": "Ching Shih commanded 1,800 ships and 80,000 pirates"},
    {"name": "Gulf of Guinea", "lat": 4.0000, "lon": 3.0000, "era": "2010-present", "pirates": "Nigerian pirates", "notes": "Currently most dangerous waters for piracy worldwide"},
    {"name": "Cilician Coast (Rough Cilicia)", "lat": 36.3000, "lon": 32.5000, "era": "200-67 BC", "pirates": "Cilician pirates", "notes": "Kidnapped Julius Caesar; Pompey crushed them 67 BC"},
    {"name": "Lundy Island, Bristol Channel", "lat": 51.1833, "lon": -4.6667, "era": "1235-1600s", "pirates": "Barbary corsairs, Thomas Benson", "notes": "Island used as pirate base; Barbary raids on England"},
    {"name": "Barataria Bay, Louisiana", "lat": 29.3000, "lon": -89.9500, "era": "1810-1815", "pirates": "Jean Lafitte", "notes": "Lafitte's smuggling empire; helped win Battle of New Orleans"},
    {"name": "Ocracoke Island, NC", "lat": 35.1000, "lon": -75.9833, "era": "1700-1718", "pirates": "Blackbeard (Edward Teach)", "notes": "Blackbeard's favorite anchorage; killed here 1718"},
    {"name": "Sallee (Sale), Morocco", "lat": 34.0531, "lon": -6.8136, "era": "1600-1800", "pirates": "Sale Rovers", "notes": "Republic of Sale; corsairs raided as far as Iceland"},
    {"name": "Riau Islands, Indonesia", "lat": 1.0833, "lon": 104.4667, "era": "1500-1800s", "pirates": "Orang Laut sea peoples", "notes": "Control of Strait of Singapore approaches"},
    {"name": "Sulu Sea, Philippines", "lat": 6.5000, "lon": 121.0000, "era": "1600-present", "pirates": "Moro pirates, Abu Sayyaf", "notes": "Centuries of piracy; modern kidnapping for ransom"},
    {"name": "Libertatia (legendary)", "lat": -15.7167, "lon": 46.3167, "era": "1690s", "pirates": "Captain Misson (possibly fictional)", "notes": "Legendary pirate utopia in Madagascar; may be myth"},
    {"name": "Uskoks of Senj, Croatia", "lat": 44.9897, "lon": 14.9047, "era": "1530-1617", "pirates": "Uskok pirates", "notes": "Croatian pirates raided Venetian and Ottoman shipping"},
    {"name": "Whydah wreck site, Cape Cod", "lat": 41.6500, "lon": -69.9500, "era": "1717", "pirates": "Black Sam Bellamy", "notes": "Only authenticated pirate wreck; richest pirate in history"},
]

# =====================================================================
# 7. EXPLORATION VOYAGES DATA
# =====================================================================
VOYAGES = [
    {"name": "Columbus First Voyage (1492)", "coords": [[37.2, -6.9], [28.1, -15.4], [21.0, -70.0], [19.0, -72.0]], "year": "1492-1493", "explorer": "Christopher Columbus", "ships": "Nina, Pinta, Santa Maria", "color": "#ef4444", "notes": "Reached the Bahamas, Cuba, Hispaniola"},
    {"name": "Magellan Circumnavigation (1519-22)", "coords": [[-1.0, -7.0], [37.4, -6.0], [28.0, -16.0], [-8.0, -35.0], [-35.0, -56.0], [-53.0, -70.0], [-33.0, -90.0], [-15.0, -130.0], [10.0, 126.0], [-6.0, 106.0], [-34.0, 18.5], [37.4, -6.0]], "year": "1519-1522", "explorer": "Ferdinand Magellan / Juan Sebastian Elcano", "ships": "Trinidad, San Antonio, Concepcion, Santiago, Victoria", "color": "#8b5cf6", "notes": "First circumnavigation; Magellan killed in Philippines"},
    {"name": "Vasco da Gama to India (1497-99)", "coords": [[38.7, -9.1], [28.0, -16.0], [-34.0, 18.5], [-12.0, 40.0], [11.4, 75.8]], "year": "1497-1499", "explorer": "Vasco da Gama", "ships": "Sao Gabriel, Sao Rafael, Berrio, store ship", "color": "#10b981", "notes": "First European to reach India by sea; opened spice trade"},
    {"name": "Cook First Voyage (1768-71)", "coords": [[50.7, -1.1], [-23.0, -43.0], [-55.0, -68.0], [-41.0, 174.0], [-34.0, 151.0], [-34.0, 18.5], [50.7, -1.1]], "year": "1768-1771", "explorer": "James Cook", "ships": "HM Bark Endeavour", "color": "#f59e0b", "notes": "Transit of Venus; mapped New Zealand and eastern Australia"},
    {"name": "Cook Second Voyage (1772-75)", "coords": [[50.7, -1.1], [-34.0, 18.5], [-67.0, 30.0], [-41.0, 174.0], [-67.0, -150.0], [-34.0, -70.0], [50.7, -1.1]], "year": "1772-1775", "explorer": "James Cook", "ships": "HMS Resolution, HMS Adventure", "color": "#f97316", "notes": "First to cross Antarctic Circle; disproved Terra Australis"},
    {"name": "Drake Circumnavigation (1577-80)", "coords": [[50.3, -4.1], [28.0, -16.0], [-8.0, -35.0], [-53.0, -70.0], [-33.0, -72.0], [38.0, -122.0], [12.0, 127.0], [-6.0, 106.0], [-34.0, 18.5], [50.3, -4.1]], "year": "1577-1580", "explorer": "Sir Francis Drake", "ships": "Golden Hind", "color": "#ec4899", "notes": "First Englishman to circumnavigate; knighted on return"},
    {"name": "Zheng He Voyages (1405-33)", "coords": [[32.0, 119.0], [21.0, 110.0], [1.3, 103.8], [-7.0, 110.0], [10.0, 76.0], [12.0, 45.0], [-6.0, 39.0], [-12.0, 44.0]], "year": "1405-1433", "explorer": "Admiral Zheng He", "ships": "Treasure Fleet (300+ ships, 28,000 crew)", "color": "#06b6d4", "notes": "Chinese treasure fleet; reached East Africa; largest wooden ships ever"},
    {"name": "Dias rounds Cape of Good Hope (1488)", "coords": [[38.7, -9.1], [28.0, -16.0], [-22.0, 14.0], [-34.4, 18.5], [-34.0, 26.0]], "year": "1487-1488", "explorer": "Bartolomeu Dias", "ships": "Sao Cristovao, Sao Pantaleao", "color": "#a855f7", "notes": "First European to round the southern tip of Africa"},
    {"name": "Norse Voyages to Vinland (~1000)", "coords": [[64.1, -21.9], [61.0, -45.0], [51.0, -56.0], [47.0, -55.0]], "year": "985-1000", "explorer": "Leif Erikson", "ships": "Longships", "color": "#38bdf8", "notes": "First Europeans in North America; L'Anse aux Meadows"},
    {"name": "Darwin on HMS Beagle (1831-36)", "coords": [[50.7, -1.1], [-23.0, -43.0], [-51.0, -69.0], [-33.0, -72.0], [-1.0, -90.0], [-18.0, -150.0], [-34.0, 151.0], [-34.0, 18.5], [50.7, -1.1]], "year": "1831-1836", "explorer": "Charles Darwin", "ships": "HMS Beagle", "color": "#22c55e", "notes": "Galapagos observations led to theory of evolution"},
    {"name": "Shackleton's Endurance (1914-17)", "coords": [[54.6, -5.9], [-34.0, -8.0], [-54.0, -36.0], [-68.7, -52.3], [-60.0, -46.5], [-54.3, -36.5]], "year": "1914-1917", "explorer": "Ernest Shackleton", "ships": "Endurance", "color": "#64748b", "notes": "Ship crushed by ice; epic survival; all 28 crew saved"},
    {"name": "Kon-Tiki Expedition (1947)", "coords": [[-12.0, -77.0], [-8.0, -90.0], [-8.0, -120.0], [-9.0, -139.0]], "year": "1947", "explorer": "Thor Heyerdahl", "ships": "Kon-Tiki (balsa raft)", "color": "#facc15", "notes": "Proved Polynesian settlement from South America was possible"},
]

# =====================================================================
# 8. CORAL REEFS & MARINE PROTECTED AREAS DATA
# =====================================================================
MARINE_PROTECTED = [
    {"name": "Papahanaumokuakea MNM", "lat": 25.0, "lon": -170.0, "area_km2": 1510000, "country": "USA (Hawaii)", "year": 2006, "level": "No-take", "notes": "One of world's largest conservation areas; UNESCO"},
    {"name": "Ross Sea MPA", "lat": -72.0, "lon": 175.0, "area_km2": 1550000, "country": "Antarctica (CCAMLR)", "year": 2016, "level": "Mixed (72% no-take)", "notes": "Largest MPA; pristine Antarctic ecosystem"},
    {"name": "Phoenix Islands Protected Area", "lat": -4.0, "lon": -172.0, "area_km2": 408250, "country": "Kiribati", "year": 2008, "level": "No-take", "notes": "Largest MPA in Pacific at declaration; UNESCO"},
    {"name": "Great Barrier Reef Marine Park", "lat": -18.0, "lon": 147.0, "area_km2": 344400, "country": "Australia", "year": 1975, "level": "Zoned", "notes": "Largest coral reef system; 2,900 reefs; visible from space"},
    {"name": "Galapagos Marine Reserve", "lat": -0.5, "lon": -91.0, "area_km2": 133000, "country": "Ecuador", "year": 1998, "level": "Zoned", "notes": "Darwin's laboratory of evolution; unique marine species"},
    {"name": "Chagos MPA (BIOT)", "lat": -6.5, "lon": 72.0, "area_km2": 640000, "country": "UK/Mauritius (disputed)", "year": 2010, "level": "No-take", "notes": "Largest no-take zone at declaration; Diego Garcia military base"},
    {"name": "Coral Sea Marine Park", "lat": -18.0, "lon": 155.0, "area_km2": 989842, "country": "Australia", "year": 2012, "level": "Zoned", "notes": "Off Queensland; pristine deep-sea coral and reefs"},
    {"name": "Northeast Greenland National Park", "lat": 75.0, "lon": -30.0, "area_km2": 972000, "country": "Denmark (Greenland)", "year": 1974, "level": "National Park", "notes": "World's largest national park; includes marine areas"},
    {"name": "Maldives Biosphere Reserve", "lat": 4.0, "lon": 73.5, "area_km2": 35000, "country": "Maldives", "year": 2020, "level": "Biosphere", "notes": "Baa Atoll UNESCO; manta ray aggregation site"},
    {"name": "Tubbataha Reefs Natural Park", "lat": 8.9, "lon": 119.9, "area_km2": 970, "country": "Philippines", "year": 1988, "level": "No-take", "notes": "UNESCO; pristine Philippine coral reef; rich diving"},
    {"name": "Ningaloo Coast MPA", "lat": -22.7, "lon": 113.8, "area_km2": 6045, "country": "Australia", "year": 1987, "level": "Zoned", "notes": "Whale shark aggregation; fringing reef 260 km long"},
    {"name": "Mariana Trench MNM", "lat": 18.0, "lon": 145.0, "area_km2": 250487, "country": "USA", "year": 2009, "level": "Monument", "notes": "Includes deepest point on Earth (Challenger Deep)"},
    {"name": "Palau National Marine Sanctuary", "lat": 7.5, "lon": 134.5, "area_km2": 500000, "country": "Palau", "year": 2015, "level": "No-take (80%)", "notes": "One of world's largest no-take zones"},
    {"name": "Red Sea Coral Reefs", "lat": 22.0, "lon": 38.0, "area_km2": 20000, "country": "Egypt/Saudi Arabia/Sudan", "year": 1983, "level": "Zoned", "notes": "Heat-resistant corals; hope for climate adaptation"},
    {"name": "Mesoamerican Reef", "lat": 17.0, "lon": -87.5, "area_km2": 1000, "country": "Mexico/Belize/Guatemala/Honduras", "year": 1996, "level": "Zoned", "notes": "Second largest reef in world; 1,000 km long"},
    {"name": "Aldabra Atoll (Seychelles)", "lat": -9.4, "lon": 46.4, "area_km2": 350, "country": "Seychelles", "year": 1981, "level": "UNESCO/Strict", "notes": "Largest raised coral atoll; giant tortoises; pristine"},
    {"name": "Wakatobi National Park", "lat": -5.5, "lon": 124.0, "area_km2": 13900, "country": "Indonesia", "year": 2002, "level": "National Park", "notes": "Part of Coral Triangle; highest reef fish diversity"},
    {"name": "Komodo National Park", "lat": -8.5, "lon": 119.5, "area_km2": 1733, "country": "Indonesia", "year": 1980, "level": "UNESCO/NP", "notes": "Komodo dragons; exceptional marine biodiversity"},
    {"name": "Cocos Island Marine Area", "lat": 5.5, "lon": -87.0, "area_km2": 19900, "country": "Costa Rica", "year": 2001, "level": "No-take", "notes": "UNESCO; hammerhead shark aggregation; treasure island legend"},
    {"name": "Nazca-Desventuradas Marine Park", "lat": -26.0, "lon": -80.0, "area_km2": 300000, "country": "Chile", "year": 2016, "level": "No-take", "notes": "One of most pristine marine areas in the world"},
]

# =====================================================================
# 9. TIDAL PHENOMENA DATA
# =====================================================================
TIDAL_PHENOMENA = [
    {"name": "Bay of Fundy", "lat": 45.3, "lon": -64.9, "country": "Canada", "tidal_range_m": 16.3, "type": "Highest tides in the world", "notes": "100 billion tonnes of water every tide cycle; Burntcoat Head record"},
    {"name": "Mont Saint-Michel", "lat": 48.6361, "lon": -1.5111, "country": "France", "tidal_range_m": 14.0, "type": "Extreme tidal island", "notes": "Tide comes in faster than a galloping horse; UNESCO site"},
    {"name": "Severn Bore", "lat": 51.7100, "lon": -2.3800, "country": "UK", "tidal_range_m": 14.5, "type": "Tidal bore", "notes": "Second highest tidal range in world; surfable bore wave"},
    {"name": "Amazon Pororoca", "lat": -0.3500, "lon": -49.3500, "country": "Brazil", "tidal_range_m": 6.0, "type": "Tidal bore", "notes": "4 m wave travels 800 km upstream; surfed for 12 km record"},
    {"name": "Qiantang River Bore", "lat": 30.3500, "lon": 120.7000, "country": "China", "tidal_range_m": 9.0, "type": "Tidal bore", "notes": "Silver Dragon bore up to 9 m high; 40 km/h; viewed since 8th c."},
    {"name": "Ungava Bay", "lat": 59.5, "lon": -67.5, "country": "Canada", "tidal_range_m": 17.0, "type": "Extreme tides", "notes": "May rival Bay of Fundy; remote subarctic location"},
    {"name": "King Sound, Derby", "lat": -17.3, "lon": 123.6, "country": "Australia", "tidal_range_m": 11.8, "type": "Highest tides in Australia", "notes": "Horizontal waterfalls in nearby Talbot Bay"},
    {"name": "Gulf of Khambhat (Cambay)", "lat": 21.5, "lon": 72.2, "country": "India", "tidal_range_m": 11.0, "type": "Extreme tides", "notes": "Highest tides in India; proposed tidal power station"},
    {"name": "Cook Inlet, Alaska", "lat": 61.0, "lon": -150.5, "country": "USA", "tidal_range_m": 10.7, "type": "Extreme tides with bore", "notes": "Turnagain Arm bore; largest tides in US"},
    {"name": "Rio Gallegos", "lat": -51.6, "lon": -69.2, "country": "Argentina", "tidal_range_m": 12.3, "type": "Extreme tides", "notes": "Highest tidal range in South America; Patagonia"},
    {"name": "Maelstrom (Saltstraumen)", "lat": 67.2333, "lon": 14.6167, "country": "Norway", "tidal_range_m": 3.0, "type": "Strongest tidal current", "notes": "World's strongest maelstrom; 40 km/h whirlpools"},
    {"name": "Corryvreckan Whirlpool", "lat": 56.1572, "lon": -5.7153, "country": "UK (Scotland)", "tidal_range_m": 4.0, "type": "Tidal whirlpool", "notes": "Third largest whirlpool in world; audible 16 km away"},
    {"name": "Naruto Whirlpools", "lat": 34.2206, "lon": 134.6489, "country": "Japan", "tidal_range_m": 1.5, "type": "Tidal whirlpool", "notes": "Up to 20 m diameter; Naruto Strait between Shikoku and Awaji"},
    {"name": "Old Sow Whirlpool", "lat": 44.9667, "lon": -66.8500, "country": "Canada/USA border", "tidal_range_m": 7.0, "type": "Tidal whirlpool", "notes": "Largest whirlpool in Western Hemisphere; 75 m diameter"},
    {"name": "Pentland Firth", "lat": 58.7000, "lon": -3.1000, "country": "UK (Scotland)", "tidal_range_m": 5.0, "type": "Extreme tidal current", "notes": "16 knot tidal streams; massive tidal energy potential"},
    {"name": "Skookumchuck Narrows", "lat": 49.7333, "lon": -123.9000, "country": "Canada (BC)", "tidal_range_m": 3.0, "type": "Tidal rapids", "notes": "Standing waves and whirlpools; kayaking destination"},
]

# =====================================================================
# 10. SUBMARINE VOLCANOES & HYDROTHERMAL VENTS DATA
# =====================================================================
SUBMARINE_FEATURES = [
    {"name": "Marsili Seamount", "lat": 39.2500, "lon": 14.3833, "type": "Submarine volcano", "depth_m": 450, "notes": "Europe's largest submarine volcano; potential tsunami risk to Italy"},
    {"name": "Kick 'em Jenny", "lat": 12.3000, "lon": -61.6333, "type": "Submarine volcano", "depth_m": 180, "notes": "Most active submarine volcano in Caribbean; Grenada; exclusion zone"},
    {"name": "Axial Seamount", "lat": 45.9500, "lon": -130.0167, "type": "Submarine volcano", "depth_m": 1400, "notes": "Most active submarine volcano in NE Pacific; erupted 2015; cabled observatory"},
    {"name": "Lost City Hydrothermal Field", "lat": 30.1167, "lon": -42.1167, "type": "Hydrothermal vent field", "depth_m": 750, "notes": "Alkaline vents; 60 m tall chimneys; may hold clues to origin of life"},
    {"name": "Mid-Atlantic Ridge (TAG field)", "lat": 26.1333, "lon": -44.8333, "type": "Hydrothermal vent field", "depth_m": 3650, "notes": "Trans-Atlantic Geotraverse; active black smokers at 366 C"},
    {"name": "East Pacific Rise (9N)", "lat": 9.8333, "lon": -104.2833, "type": "Hydrothermal vent field", "depth_m": 2500, "notes": "First black smokers discovered 1979; tube worm communities"},
    {"name": "Kolumbo Volcano", "lat": 36.5167, "lon": 25.4833, "type": "Submarine volcano", "depth_m": 18, "notes": "Near Santorini; last erupted 1650; hydrothermal venting; CO2 lake"},
    {"name": "Monowai Seamount", "lat": -25.8833, "lon": -177.1833, "type": "Submarine volcano", "depth_m": 100, "notes": "One of most active submarine volcanoes; Kermadec Arc; New Zealand"},
    {"name": "Brothers Volcano", "lat": -34.8667, "lon": -179.0667, "type": "Submarine volcano", "depth_m": 1200, "notes": "Kermadec Arc; rich mineral deposits; studied for seafloor mining"},
    {"name": "Havre Seamount", "lat": -31.1000, "lon": -179.0333, "type": "Submarine volcano", "depth_m": 650, "notes": "2012 eruption produced largest deep-ocean eruption ever recorded; pumice raft"},
    {"name": "NW Rota-1", "lat": 14.6000, "lon": 144.7833, "type": "Submarine volcano", "depth_m": 517, "notes": "Brimstone Pit; only submarine eruption observed in real-time (2006)"},
    {"name": "Loihi Seamount", "lat": 18.9200, "lon": -155.2700, "type": "Submarine volcano", "depth_m": 975, "notes": "Youngest Hawaiian volcano; will become next Hawaiian island in 10,000-100,000 years"},
    {"name": "Juan de Fuca Ridge (Endeavour)", "lat": 47.9500, "lon": -129.1000, "type": "Hydrothermal vent field", "depth_m": 2250, "notes": "5 major vent fields; Canada's first MPA for hydrothermal vents"},
    {"name": "Snake Pit Hydrothermal Field", "lat": 23.3700, "lon": -44.9500, "type": "Hydrothermal vent field", "depth_m": 3460, "notes": "Mid-Atlantic Ridge; discovered 1985; black and white smokers"},
    {"name": "Lau Basin Vents", "lat": -20.0500, "lon": -176.1333, "type": "Hydrothermal vent field", "depth_m": 1700, "notes": "Back-arc basin; unique chemosynthetic ecosystems; Tonga"},
    {"name": "Kavachi Volcano", "lat": -8.9900, "lon": 157.9700, "type": "Submarine volcano", "depth_m": 20, "notes": "Solomon Islands; sharks live in the crater; Sharkcano"},
    {"name": "Hunga Tonga-Hunga Ha'apai", "lat": -20.5450, "lon": -175.3900, "type": "Submarine volcano", "depth_m": 0, "notes": "Massive eruption Jan 2022; largest atmospheric explosion in decades"},
    {"name": "Anak Krakatau", "lat": -6.1020, "lon": 105.4230, "type": "Submarine/emergent volcano", "depth_m": 0, "notes": "Child of Krakatoa; 2018 flank collapse caused deadly tsunami"},
    {"name": "Empedocles Seamount", "lat": 37.1500, "lon": 12.7000, "type": "Submarine volcano", "depth_m": 7, "notes": "Between Sicily and Tunisia; Graham Island appeared and vanished 1831"},
    {"name": "Banua Wuhu", "lat": 3.1400, "lon": 125.4900, "type": "Submarine volcano", "depth_m": 5, "notes": "Indonesia; periodic eruptions discolor sea; coral growth"},
    {"name": "Didicas Volcano", "lat": 19.0750, "lon": 122.2020, "type": "Submarine/emergent volcano", "depth_m": 0, "notes": "Philippines; emerged from ocean 1952; now a volcanic island"},
    {"name": "Rumble III", "lat": -35.7333, "lon": 178.4833, "type": "Submarine volcano", "depth_m": 200, "notes": "Kermadec Arc; hydrothermal venting; New Zealand EEZ"},
    {"name": "Niuatahi (Volcano O)", "lat": -15.3700, "lon": -174.0000, "type": "Submarine volcano", "depth_m": 1200, "notes": "Tonga; large submarine caldera; active hydrothermal system"},
]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def _make_base_map(lat: float = 20.0, lon: float = 0.0, zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map."""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _render_map(m: folium.Map, height: int = 550):
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


@st.cache_data(ttl=3600)
def _overpass_lighthouses(lat: float, lon: float, radius_km: float):
    """Fetch lighthouses via Overpass API."""
    query = f"""
    [out:json][timeout:60];
    (
      node["man_made"="lighthouse"](around:{radius_km * 1000},{lat},{lon});
      way["man_made"="lighthouse"](around:{radius_km * 1000},{lat},{lon});
    );
    out center body;
    """
    return query_overpass(query)


# =====================================================================
# MAP RENDERING FUNCTIONS
# =====================================================================

def _render_lighthouses():
    """Render Historic Lighthouses map."""
    st.markdown("#### Historic Lighthouses")
    st.markdown("Browse 40+ famous lighthouses worldwide and search for regional lighthouses via OpenStreetMap.")

    col1, col2 = st.columns([1, 1])
    with col1:
        show_famous = st.checkbox("Show Famous Lighthouses (hardcoded)", value=True, key="lh_famous")
    with col2:
        search_region = st.selectbox("Search Regional Lighthouses (Overpass)", list(LIGHTHOUSE_SEARCH_REGIONS.keys()), key="lh_region")

    custom_lat, custom_lon, custom_radius = 51.5, 1.5, 200
    if search_region != "Custom Area":
        preset = LIGHTHOUSE_SEARCH_REGIONS[search_region]
        if preset:
            custom_lat, custom_lon, custom_radius = preset["lat"], preset["lon"], preset["radius"]
    else:
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            custom_lat = st.number_input("Latitude", value=51.5, key="marim_lh_lat")
        with cc2:
            custom_lon = st.number_input("Longitude", value=1.5, key="marim_lh_lon")
        with cc3:
            custom_radius = st.number_input("Radius (km)", value=200, min_value=10, max_value=1000, key="marim_lh_radius")

    do_search = st.button("Search Regional Lighthouses", key="lh_search")

    m = _make_base_map(lat=30.0, lon=0.0, zoom=2)

    if show_famous:
        fg = folium.FeatureGroup(name="Famous Lighthouses")
        for lh in LIGHTHOUSES:
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
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=escape(lh["name"]),
                icon=folium.Icon(color="orange", icon="lightbulb", prefix="fa"),
            ).add_to(fg)
        fg.add_to(m)

    overpass_results = []
    if do_search:
        with st.spinner("Searching Overpass API for lighthouses..."):
            data = _overpass_lighthouses(custom_lat, custom_lon, custom_radius)
            if data and "_error" not in data:
                elements = data.get("elements", [])
                fg2 = folium.FeatureGroup(name="Regional Lighthouses (OSM)")
                for el in elements:
                    lat_e = el.get("lat") or el.get("center", {}).get("lat")
                    lon_e = el.get("lon") or el.get("center", {}).get("lon")
                    if lat_e is None or lon_e is None:
                        continue
                    tags = el.get("tags", {})
                    name = tags.get("name", "Unnamed Lighthouse")
                    popup_html = (
                        f"<div style='min-width:180px;'>"
                        f"<b>{escape(name)}</b><br>"
                        f"<b>Source:</b> OpenStreetMap<br>"
                    )
                    for k in ["description", "height", "start_date", "website"]:
                        if k in tags:
                            popup_html += f"<b>{escape(k.replace('_', ' ').title())}:</b> {escape(tags[k])}<br>"
                    popup_html += "</div>"
                    folium.CircleMarker(
                        location=[lat_e, lon_e],
                        radius=6,
                        color="#f59e0b",
                        fill=True,
                        fill_color="#f59e0b",
                        fill_opacity=0.8,
                        popup=folium.Popup(popup_html, max_width=280),
                        tooltip=escape(name),
                    ).add_to(fg2)
                    overpass_results.append({"name": name, "lat": lat_e, "lon": lon_e})
                fg2.add_to(m)
                st.success(f"Found {len(elements)} lighthouses from OpenStreetMap.")
            elif data and "_error" in data:
                st.warning(f"Overpass error: {data['_error']}")
            else:
                st.warning("No response from Overpass API.")

    folium.LayerControl().add_to(m)
    _render_map(m)

    # Stats
    st.markdown("##### Lighthouse Data")
    df = pd.DataFrame(LIGHTHOUSES)
    col_order = ["name", "country", "year", "height_m", "range_nm", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")

    if overpass_results:
        st.markdown("##### Regional Search Results")
        st.dataframe(pd.DataFrame(overpass_results), width="stretch")

    # Chart: Height distribution
    fig, ax = _dark_fig(figsize=(10, 4))
    heights = [l["height_m"] for l in LIGHTHOUSES if l["height_m"]]
    names = [l["name"][:20] for l in LIGHTHOUSES if l["height_m"]]
    ax.barh(names[:20], heights[:20], color="#f59e0b", edgecolor="#2a3550")
    ax.set_xlabel("Height (m)")
    ax.set_title("Top 20 Lighthouse Heights")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_shipwrecks():
    """Render Famous Shipwrecks map."""
    st.markdown("#### Famous Shipwrecks")
    st.markdown("40+ historically significant shipwrecks worldwide with details on year, depth, cause, and casualties.")

    col1, col2 = st.columns([1, 1])
    with col1:
        min_year = st.slider("Minimum Year", min_value=1500, max_value=2020, value=1500, key="sw_min")
    with col2:
        min_casualties = st.slider("Minimum Casualties", min_value=0, max_value=5000, value=0, key="sw_cas")

    filtered = [s for s in SHIPWRECKS if s["year"] >= min_year and s["casualties"] >= min_casualties]
    st.info(f"Showing {len(filtered)} of {len(SHIPWRECKS)} shipwrecks")

    m = _make_base_map(lat=20.0, lon=0.0, zoom=2)
    cluster = MarkerCluster(name="Shipwrecks")

    for sw in filtered:
        cas_color = "red" if sw["casualties"] > 1000 else ("orange" if sw["casualties"] > 100 else "blue")
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(sw['name'])}</b><br>"
            f"<b>Year:</b> {sw['year']}<br>"
            f"<b>Depth:</b> {sw['depth_m']} m<br>"
            f"<b>Cause:</b> {escape(sw['cause'])}<br>"
            f"<b>Casualties:</b> {sw['casualties']:,}<br>"
            f"<b>Notes:</b> {escape(sw['notes'])}"
            f"</div>"
        )
        folium.Marker(
            location=[sw["lat"], sw["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(sw["name"]),
            icon=folium.Icon(color=cas_color, icon="ship", prefix="fa"),
        ).add_to(cluster)

    cluster.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    # Data table
    st.markdown("##### Shipwreck Data")
    df = pd.DataFrame(filtered)
    col_order = ["name", "year", "depth_m", "cause", "casualties", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")

    # Chart: Top casualties
    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_sw = sorted(filtered, key=lambda x: x["casualties"], reverse=True)[:15]
    names = [s["name"][:25] for s in sorted_sw]
    cas = [s["casualties"] for s in sorted_sw]
    bars = ax.barh(names, cas, color="#ef4444", edgecolor="#2a3550")
    ax.set_xlabel("Casualties")
    ax.set_title("Deadliest Shipwrecks")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_straits():
    """Render Strategic Straits & Passages map."""
    st.markdown("#### Strategic Straits & Passages")
    st.markdown("20+ key maritime chokepoints and canals with daily ship traffic estimates.")

    m = _make_base_map(lat=20.0, lon=30.0, zoom=2)

    for s in STRAITS:
        color = "#ef4444" if s["daily_ships"] > 200 else ("#f59e0b" if s["daily_ships"] > 50 else "#06b6d4")
        weight = max(2, min(8, s["daily_ships"] // 50))
        popup_html = (
            f"<div style='min-width:200px;'>"
            f"<b>{escape(s['name'])}</b><br>"
            f"<b>Daily Ships:</b> ~{s['daily_ships']:,}<br>"
            f"<b>Width:</b> {s['width_km']} km<br>"
            f"<b>Notes:</b> {escape(s['notes'])}"
            f"</div>"
        )
        folium.PolyLine(
            locations=s["coords"],
            color=color,
            weight=weight,
            opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(s["name"]),
        ).add_to(m)
        # Add label marker at midpoint
        mid = s["coords"][len(s["coords"]) // 2]
        folium.Marker(
            location=mid,
            icon=folium.DivIcon(
                html=f"<div style='font-size:9px;color:#e8ecf4;white-space:nowrap;text-shadow:1px 1px 2px black;'>{escape(s['name'][:20])}</div>",
                icon_size=(120, 20),
            ),
        ).add_to(m)

    _render_map(m)

    st.markdown("**Legend:** Red = >200 ships/day | Orange = 50-200 ships/day | Cyan = <50 ships/day")

    st.markdown("##### Strait & Passage Data")
    df = pd.DataFrame(STRAITS)
    df_display = df[["name", "daily_ships", "width_km", "notes"]].copy()
    df_display = df_display.sort_values("daily_ships", ascending=False)
    st.dataframe(df_display, width="stretch")

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_s = sorted(STRAITS, key=lambda x: x["daily_ships"], reverse=True)[:15]
    names = [s["name"][:25] for s in sorted_s]
    traffic = [s["daily_ships"] for s in sorted_s]
    ax.barh(names, traffic, color="#06b6d4", edgecolor="#2a3550")
    ax.set_xlabel("Daily Ship Traffic")
    ax.set_title("Busiest Maritime Chokepoints")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_ocean_currents():
    """Render Ocean Currents map."""
    st.markdown("#### Ocean Currents")
    st.markdown("Major global ocean currents with temperature, speed, and direction.")

    temp_filter = st.radio("Temperature Filter", ["All", "Warm (>15C)", "Cold (<15C)"], horizontal=True, key="oc_temp")

    m = _make_base_map(lat=10.0, lon=0.0, zoom=2)

    for c in OCEAN_CURRENTS:
        # Parse temp range for filtering
        temps = c["temp_c"].split("-")
        avg_temp = (float(temps[0]) + float(temps[1])) / 2 if len(temps) == 2 else float(temps[0])
        if temp_filter == "Warm (>15C)" and avg_temp < 15:
            continue
        if temp_filter == "Cold (<15C)" and avg_temp >= 15:
            continue

        popup_html = (
            f"<div style='min-width:200px;'>"
            f"<b>{escape(c['name'])}</b><br>"
            f"<b>Temperature:</b> {escape(c['temp_c'])} C<br>"
            f"<b>Speed:</b> {c['speed_kts']} knots<br>"
            f"<b>Direction:</b> {escape(c['direction'])}<br>"
            f"<b>Notes:</b> {escape(c['notes'])}"
            f"</div>"
        )
        weight = max(2, min(6, int(c["speed_kts"] * 2)))
        folium.PolyLine(
            locations=c["coords"],
            color=c["color"],
            weight=weight,
            opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(c["name"]),
            dash_array="10 5" if avg_temp < 10 else None,
        ).add_to(m)

        # Direction arrow at midpoint
        mid_idx = len(c["coords"]) // 2
        mid = c["coords"][mid_idx]
        folium.Marker(
            location=mid,
            icon=folium.DivIcon(
                html=f"<div style='font-size:10px;color:{c['color']};white-space:nowrap;text-shadow:1px 1px 2px black;font-weight:bold;'>{escape(c['name'][:18])} ({c['direction']})</div>",
                icon_size=(160, 20),
            ),
        ).add_to(m)

    _render_map(m)
    st.markdown("**Solid lines** = warm currents | **Dashed lines** = cold currents (<10 C avg)")

    st.markdown("##### Ocean Current Data")
    df = pd.DataFrame(OCEAN_CURRENTS)
    df_display = df[["name", "temp_c", "speed_kts", "direction", "notes"]].copy()
    st.dataframe(df_display, width="stretch")


def _render_naval_battles():
    """Render Naval Battles map."""
    st.markdown("#### Naval Battles")
    st.markdown("30+ famous naval battles from antiquity to WWII.")

    col1, col2 = st.columns(2)
    with col1:
        era = st.selectbox("Era", ["All", "Ancient (<500 AD)", "Pre-Modern (500-1800)", "Modern (1800-1945)"], key="nb_era")
    with col2:
        search = st.text_input("Search battles", "", key="nb_search")

    filtered = NAVAL_BATTLES.copy()
    if era == "Ancient (<500 AD)":
        filtered = [b for b in filtered if b["year"] < 500]
    elif era == "Pre-Modern (500-1800)":
        filtered = [b for b in filtered if 500 <= b["year"] <= 1800]
    elif era == "Modern (1800-1945)":
        filtered = [b for b in filtered if b["year"] > 1800]
    if search:
        search_lower = search.lower()
        filtered = [b for b in filtered if search_lower in b["name"].lower() or search_lower in b["forces"].lower()]

    st.info(f"Showing {len(filtered)} battles")

    m = _make_base_map(lat=25.0, lon=10.0, zoom=2)
    for b in filtered:
        year_display = f"{abs(b['year'])} {'BC' if b['year'] < 0 else 'AD'}"
        color = "red" if b["year"] > 1900 else ("orange" if b["year"] > 1500 else "green")
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(b['name'])}</b><br>"
            f"<b>Year:</b> {year_display}<br>"
            f"<b>Forces:</b> {escape(b['forces'])}<br>"
            f"<b>Outcome:</b> {escape(b['outcome'])}<br>"
            f"<b>Notes:</b> {escape(b['notes'])}"
            f"</div>"
        )
        folium.Marker(
            location=[b["lat"], b["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(b['name'])} ({year_display})",
            icon=folium.Icon(color=color, icon="crosshairs", prefix="fa"),
        ).add_to(m)

    _render_map(m)

    st.markdown("**Legend:** Green = Ancient | Orange = Pre-Modern | Red = Modern")

    st.markdown("##### Battle Data")
    rows = []
    for b in filtered:
        year_display = f"{abs(b['year'])} {'BC' if b['year'] < 0 else 'AD'}"
        rows.append({"name": b["name"], "year": year_display, "forces": b["forces"], "outcome": b["outcome"], "notes": b["notes"]})
    st.dataframe(pd.DataFrame(rows), width="stretch")


def _render_pirate_history():
    """Render Pirate History map."""
    st.markdown("#### Pirate History")
    st.markdown("20+ pirate hotspots across eras, from ancient Cilicia to modern Gulf of Guinea.")

    era_filter = st.radio("Era Filter", ["All", "Ancient/Medieval", "Golden Age (1650-1730)", "Modern"], horizontal=True, key="ph_era")

    m = _make_base_map(lat=15.0, lon=-20.0, zoom=2)
    fg = folium.FeatureGroup(name="Pirate Hotspots")

    for p in PIRATE_HOTSPOTS:
        # Simple era filtering
        era_str = p["era"].lower()
        if era_filter == "Ancient/Medieval" and not any(x in era_str for x in ["bc", "12", "13", "14", "15"]):
            continue
        if era_filter == "Golden Age (1650-1730)" and not any(x in era_str for x in ["16", "17"]):
            continue
        if era_filter == "Modern" and not any(x in era_str for x in ["20", "19", "present"]):
            continue

        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(p['name'])}</b><br>"
            f"<b>Era:</b> {escape(p['era'])}<br>"
            f"<b>Famous Pirates:</b> {escape(p['pirates'])}<br>"
            f"<b>Notes:</b> {escape(p['notes'])}"
            f"</div>"
        )
        folium.Marker(
            location=[p["lat"], p["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(p["name"]),
            icon=folium.Icon(color="black", icon="flag", prefix="fa"),
        ).add_to(fg)

    fg.add_to(m)
    folium.LayerControl().add_to(m)
    _render_map(m)

    st.markdown("##### Pirate Hotspot Data")
    df = pd.DataFrame(PIRATE_HOTSPOTS)
    df_display = df[["name", "era", "pirates", "notes"]].copy()
    st.dataframe(df_display, width="stretch")


def _render_exploration_voyages():
    """Render Exploration Voyages map."""
    st.markdown("#### Exploration Voyages")
    st.markdown("Great maritime exploration routes from the Norse to modern expeditions.")

    selected = st.multiselect(
        "Select Voyages to Display",
        [v["name"] for v in VOYAGES],
        default=[v["name"] for v in VOYAGES[:5]],
        key="ev_select",
    )

    m = _make_base_map(lat=10.0, lon=0.0, zoom=2)

    for v in VOYAGES:
        if v["name"] not in selected:
            continue
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(v['name'])}</b><br>"
            f"<b>Explorer:</b> {escape(v['explorer'])}<br>"
            f"<b>Dates:</b> {escape(v['year'])}<br>"
            f"<b>Ships:</b> {escape(v['ships'])}<br>"
            f"<b>Notes:</b> {escape(v['notes'])}"
            f"</div>"
        )
        folium.PolyLine(
            locations=v["coords"],
            color=v["color"],
            weight=3,
            opacity=0.85,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(v["name"]),
        ).add_to(m)
        # Start marker
        folium.CircleMarker(
            location=v["coords"][0],
            radius=6,
            color=v["color"],
            fill=True,
            fill_color=v["color"],
            fill_opacity=1.0,
            tooltip=f"Start: {escape(v['name'])}",
        ).add_to(m)
        # End marker
        folium.CircleMarker(
            location=v["coords"][-1],
            radius=6,
            color=v["color"],
            fill=True,
            fill_color="#e8ecf4",
            fill_opacity=1.0,
            tooltip=f"End: {escape(v['name'])}",
        ).add_to(m)

    _render_map(m)

    st.markdown("##### Voyage Data")
    rows = []
    for v in VOYAGES:
        rows.append({
            "name": v["name"],
            "explorer": v["explorer"],
            "dates": v["year"],
            "ships": v["ships"],
            "notes": v["notes"],
        })
    st.dataframe(pd.DataFrame(rows), width="stretch")


def _render_marine_protected():
    """Render Coral Reefs & Marine Protected Areas map."""
    st.markdown("#### Coral Reefs & Marine Protected Areas")
    st.markdown("20+ largest marine protected areas worldwide with area, protection level, and significance.")

    sort_by = st.selectbox("Sort by", ["area_km2", "year", "name"], key="mpa_sort")

    m = _make_base_map(lat=5.0, lon=30.0, zoom=2)

    for mpa in MARINE_PROTECTED:
        radius = max(8, min(30, int((mpa["area_km2"] / 50000) ** 0.5 * 8)))
        color = "#10b981" if "no-take" in mpa["level"].lower() else ("#f59e0b" if "zoned" in mpa["level"].lower() else "#3b82f6")
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{escape(mpa['name'])}</b><br>"
            f"<b>Country:</b> {escape(mpa['country'])}<br>"
            f"<b>Area:</b> {mpa['area_km2']:,.0f} km2<br>"
            f"<b>Year Established:</b> {mpa['year']}<br>"
            f"<b>Protection Level:</b> {escape(mpa['level'])}<br>"
            f"<b>Notes:</b> {escape(mpa['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[mpa["lat"], mpa["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.4,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(mpa["name"]),
        ).add_to(m)

    _render_map(m)
    st.markdown("**Green** = No-take | **Orange** = Zoned | **Blue** = Other protection")

    st.markdown("##### Marine Protected Area Data")
    df = pd.DataFrame(MARINE_PROTECTED)
    df = df.sort_values(sort_by, ascending=(sort_by == "name"))
    df_display = df[["name", "country", "area_km2", "year", "level", "notes"]].copy()
    st.dataframe(df_display, width="stretch")

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_mpa = sorted(MARINE_PROTECTED, key=lambda x: x["area_km2"], reverse=True)[:12]
    names = [m["name"][:25] for m in sorted_mpa]
    areas = [m["area_km2"] for m in sorted_mpa]
    ax.barh(names, areas, color="#10b981", edgecolor="#2a3550")
    ax.set_xlabel("Area (km2)")
    ax.set_title("Largest Marine Protected Areas")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_tidal_phenomena():
    """Render Tidal Phenomena map."""
    st.markdown("#### Tidal Phenomena")
    st.markdown("15+ locations with extreme tides, tidal bores, whirlpools, and maelstroms.")

    type_filter = st.radio("Type", ["All", "Extreme tides", "Tidal bores", "Whirlpools & Maelstroms"], horizontal=True, key="marim_tp_type")

    m = _make_base_map(lat=30.0, lon=0.0, zoom=2)

    for t in TIDAL_PHENOMENA:
        t_type = t["type"].lower()
        if type_filter == "Extreme tides" and "extreme" not in t_type and "highest" not in t_type:
            continue
        if type_filter == "Tidal bores" and "bore" not in t_type and "rapid" not in t_type:
            continue
        if type_filter == "Whirlpools & Maelstroms" and "whirl" not in t_type and "maelstrom" not in t_type and "current" not in t_type:
            continue

        radius = max(6, min(18, int(t["tidal_range_m"])))
        color = "#3b82f6" if t["tidal_range_m"] > 10 else ("#06b6d4" if t["tidal_range_m"] > 5 else "#8b5cf6")
        popup_html = (
            f"<div style='min-width:200px;'>"
            f"<b>{escape(t['name'])}</b><br>"
            f"<b>Country:</b> {escape(t['country'])}<br>"
            f"<b>Tidal Range:</b> {t['tidal_range_m']} m<br>"
            f"<b>Type:</b> {escape(t['type'])}<br>"
            f"<b>Notes:</b> {escape(t['notes'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(t['name'])} ({t['tidal_range_m']}m)",
        ).add_to(m)

    _render_map(m)

    st.markdown("##### Tidal Phenomena Data")
    df = pd.DataFrame(TIDAL_PHENOMENA)
    df = df.sort_values("tidal_range_m", ascending=False)
    df_display = df[["name", "country", "tidal_range_m", "type", "notes"]].copy()
    st.dataframe(df_display, width="stretch")

    fig, ax = _dark_fig(figsize=(10, 4))
    sorted_t = sorted(TIDAL_PHENOMENA, key=lambda x: x["tidal_range_m"], reverse=True)
    names = [t["name"][:22] for t in sorted_t]
    ranges = [t["tidal_range_m"] for t in sorted_t]
    colors = ["#3b82f6" if r > 10 else ("#06b6d4" if r > 5 else "#8b5cf6") for r in ranges]
    ax.barh(names, ranges, color=colors, edgecolor="#2a3550")
    ax.set_xlabel("Tidal Range (m)")
    ax.set_title("Extreme Tidal Ranges Worldwide")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, width=800)


def _render_submarine_volcanoes():
    """Render Submarine Volcanoes & Hydrothermal Vents map."""
    st.markdown("#### Submarine Volcanoes & Hydrothermal Vents")
    st.markdown("20+ underwater volcanoes and hydrothermal vent fields worldwide.")

    feat_type = st.radio("Feature Type", ["All", "Submarine volcano", "Hydrothermal vent field"], horizontal=True, key="sv_type")

    m = _make_base_map(lat=10.0, lon=30.0, zoom=2)

    for f in SUBMARINE_FEATURES:
        if feat_type != "All" and feat_type.lower() not in f["type"].lower():
            continue

        is_vent = "vent" in f["type"].lower() or "hydrothermal" in f["type"].lower()
        color = "#f59e0b" if is_vent else "#ef4444"
        icon_name = "fire" if not is_vent else "tint"

        popup_html = (
            f"<div style='min-width:200px;'>"
            f"<b>{escape(f['name'])}</b><br>"
            f"<b>Type:</b> {escape(f['type'])}<br>"
            f"<b>Depth:</b> {f['depth_m']} m<br>"
            f"<b>Notes:</b> {escape(f['notes'])}"
            f"</div>"
        )
        folium.Marker(
            location=[f["lat"], f["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(f["name"]),
            icon=folium.Icon(color="red" if not is_vent else "orange", icon=icon_name, prefix="fa"),
        ).add_to(m)

    _render_map(m)
    st.markdown("**Red** = Submarine volcanoes | **Orange** = Hydrothermal vent fields")

    st.markdown("##### Submarine Feature Data")
    filtered = SUBMARINE_FEATURES
    if feat_type != "All":
        filtered = [f for f in SUBMARINE_FEATURES if feat_type.lower() in f["type"].lower()]
    df = pd.DataFrame(filtered)
    df_display = df[["name", "type", "depth_m", "notes"]].copy()
    df_display = df_display.sort_values("depth_m")
    st.dataframe(df_display, width="stretch")

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_f = sorted(filtered, key=lambda x: x["depth_m"], reverse=True)[:15]
    names = [f["name"][:25] for f in sorted_f]
    depths = [f["depth_m"] for f in sorted_f]
    colors = ["#ef4444" if "vent" not in f["type"].lower() else "#f59e0b" for f in sorted_f]
    ax.barh(names, depths, color=colors, edgecolor="#2a3550")
    ax.set_xlabel("Depth (m)")
    ax.set_title("Submarine Features by Depth")
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

def render_maritime_maps_tab():
    """Main entry point for the Maritime & Navigation Maps tab."""
    st.markdown(
        '<div class="tab-header cyan">'
        "<h4>Maritime &amp; Navigation</h4>"
        "<p>Lighthouses, shipwrecks, ports, maritime passages, ocean currents, naval history</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    map_type = st.selectbox("Select Maritime Map Type", MAP_TYPES, key="maritime_map_type")

    st.markdown("---")

    if map_type == "Historic Lighthouses":
        _render_lighthouses()
    elif map_type == "Famous Shipwrecks":
        _render_shipwrecks()
    elif map_type == "Strategic Straits & Passages":
        _render_straits()
    elif map_type == "Ocean Currents":
        _render_ocean_currents()
    elif map_type == "Naval Battles":
        _render_naval_battles()
    elif map_type == "Pirate History":
        _render_pirate_history()
    elif map_type == "Exploration Voyages":
        _render_exploration_voyages()
    elif map_type == "Coral Reefs & Marine Protected":
        _render_marine_protected()
    elif map_type == "Tidal Phenomena":
        _render_tidal_phenomena()
    elif map_type == "Submarine Volcanoes & Hydrothermal":
        _render_submarine_volcanoes()
