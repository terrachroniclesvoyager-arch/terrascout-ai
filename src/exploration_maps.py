# -*- coding: utf-8 -*-
"""
TerraScout AI - Exploration & Discovery Maps Module
Provides 10 thematic exploration map types covering Age of Exploration routes,
polar expeditions, mountain first ascents, deep sea exploration, space launch sites,
ancient trade routes, first contacts & discoveries, cartographic milestones,
scientific expeditions, and last unexplored places.

All data is curated/hardcoded. No API keys needed.
"""

import html
import io

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =====================================================================
# CONSTANTS
# =====================================================================
MAP_MODES = [
    "Age of Exploration Routes",
    "Polar Expeditions",
    "Mountain First Ascents",
    "Deep Sea Exploration",
    "Space Launch Sites",
    "Ancient Trade Routes",
    "First Contacts & Discoveries",
    "Cartographic Milestones",
    "Scientific Expeditions",
    "Last Unexplored Places",
]

# Dark theme palette
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_COLOR = "#06b6d4"
SECONDARY_TEXT = "#8b97b0"

# =====================================================================
# 1. AGE OF EXPLORATION ROUTES
# =====================================================================
EXPLORATION_ROUTES = [
    {
        "name": "Christopher Columbus (1st Voyage)",
        "year": 1492,
        "nationality": "Genoese / Spain",
        "route": [[37.0, -7.0], [28.5, -16.0], [25.0, -30.0], [22.0, -50.0], [24.0, -74.5]],
        "color": "#ef4444",
        "notes": "Departed Palos de la Frontera; reached Bahamas (San Salvador) Oct 12, 1492",
    },
    {
        "name": "Ferdinand Magellan / Elcano (Circumnavigation)",
        "year": 1519,
        "nationality": "Portuguese / Spain",
        "route": [[36.5, -6.3], [28.0, -16.0], [5.0, -30.0], [-22.0, -40.0], [-52.0, -70.0],
                  [-35.0, -90.0], [-15.0, -130.0], [10.0, 126.0], [-6.0, 106.0],
                  [-34.0, 25.0], [5.0, -20.0], [36.5, -6.3]],
        "color": "#f59e0b",
        "notes": "First circumnavigation 1519-1522; Magellan killed in Philippines; Elcano completed voyage",
    },
    {
        "name": "Vasco da Gama (1st Voyage to India)",
        "year": 1497,
        "nationality": "Portuguese",
        "route": [[38.7, -9.1], [28.5, -16.0], [15.0, -24.0], [-5.0, -20.0],
                  [-34.0, 18.0], [-30.0, 31.0], [-12.0, 44.0], [-4.0, 40.0],
                  [11.5, 43.0], [11.9, 75.4]],
        "color": "#22c55e",
        "notes": "First European to reach India by sea via the Cape of Good Hope, arrived Calicut 1498",
    },
    {
        "name": "James Cook (1st Voyage)",
        "year": 1768,
        "nationality": "British",
        "route": [[50.4, -3.5], [28.5, -16.0], [-22.9, -43.2], [-55.0, -68.0],
                  [-17.5, -149.5], [-41.0, 174.0], [-34.0, 151.0], [-34.0, 25.0],
                  [50.4, -3.5]],
        "color": "#3b82f6",
        "notes": "HM Bark Endeavour 1768-1771; observed Transit of Venus; charted New Zealand & E. Australia",
    },
    {
        "name": "Francis Drake (Circumnavigation)",
        "year": 1577,
        "nationality": "English",
        "route": [[50.4, -3.5], [28.0, -16.0], [-5.0, -30.0], [-33.0, -52.0],
                  [-55.0, -68.0], [-33.0, -72.0], [8.0, -80.0], [38.0, -123.0],
                  [15.0, -170.0], [7.0, 126.0], [-6.0, 106.0], [-34.0, 25.0],
                  [15.0, -24.0], [50.4, -3.5]],
        "color": "#a855f7",
        "notes": "Second circumnavigation 1577-1580 aboard the Golden Hind; knighted by Elizabeth I",
    },
    {
        "name": "Bartolomeu Dias",
        "year": 1488,
        "nationality": "Portuguese",
        "route": [[38.7, -9.1], [28.5, -16.0], [15.0, -18.0], [-5.0, -10.0],
                  [-23.0, 14.0], [-34.8, 20.0], [-33.5, 27.0]],
        "color": "#06b6d4",
        "notes": "First European to round the Cape of Good Hope (Cape of Storms); returned 1488",
    },
    {
        "name": "Zheng He (Treasure Voyages)",
        "year": 1405,
        "nationality": "Chinese (Ming Dynasty)",
        "route": [[32.0, 118.8], [23.0, 113.0], [10.0, 107.0], [1.3, 103.8],
                  [7.0, 80.0], [10.0, 76.0], [12.0, 45.0], [-6.0, 39.5],
                  [-12.0, 44.0]],
        "color": "#f472b6",
        "notes": "Seven voyages 1405-1433; massive treasure fleet of 300+ ships; reached East Africa",
    },
    {
        "name": "John Cabot",
        "year": 1497,
        "nationality": "Venetian / England",
        "route": [[51.4, -2.6], [51.0, -10.0], [52.0, -30.0], [47.6, -52.7]],
        "color": "#84cc16",
        "notes": "Reached Newfoundland in 1497; first European since Vikings to reach N. America mainland",
    },
    {
        "name": "Hernan Cortes (to Mexico)",
        "year": 1519,
        "nationality": "Spanish",
        "route": [[21.5, -80.0], [21.0, -86.8], [19.2, -90.5], [19.4, -96.1]],
        "color": "#fb923c",
        "notes": "Departed Cuba 1519; landed Veracruz; conquered Aztec Empire by 1521",
    },
    {
        "name": "Abel Tasman",
        "year": 1642,
        "nationality": "Dutch",
        "route": [[-6.2, 106.8], [-25.0, 90.0], [-42.5, 145.5], [-42.0, 172.0],
                  [-18.0, 178.0], [-5.0, 140.0], [-6.2, 106.8]],
        "color": "#e879f9",
        "notes": "First European to reach Tasmania & New Zealand 1642-1643; mapped parts of Australia",
    },
]

# =====================================================================
# 2. POLAR EXPEDITIONS
# =====================================================================
POLAR_EXPEDITIONS = [
    {
        "name": "Roald Amundsen - South Pole",
        "year": 1911,
        "nationality": "Norwegian",
        "type": "Antarctic",
        "route": [[-78.5, 164.0], [-80.0, 170.0], [-85.0, 175.0], [-90.0, 0.0]],
        "color": "#ef4444",
        "result": "Success",
        "notes": "First to reach South Pole, Dec 14, 1911; used dog sleds from Bay of Whales",
    },
    {
        "name": "Robert Falcon Scott - South Pole",
        "year": 1912,
        "nationality": "British",
        "type": "Antarctic",
        "route": [[-77.8, 166.7], [-80.0, 169.0], [-85.0, 170.0], [-90.0, 0.0]],
        "color": "#3b82f6",
        "result": "Reached Pole; died returning",
        "notes": "Reached South Pole Jan 17, 1912, 34 days after Amundsen; all 5 perished on return",
    },
    {
        "name": "Ernest Shackleton - Endurance",
        "year": 1914,
        "nationality": "British",
        "type": "Antarctic",
        "route": [[-54.3, -36.5], [-63.0, -40.0], [-68.7, -52.3], [-60.7, -45.9], [-54.3, -36.5]],
        "color": "#f59e0b",
        "result": "Ship lost; all crew survived",
        "notes": "Imperial Trans-Antarctic Expedition; Endurance crushed by ice; epic boat journey to South Georgia",
    },
    {
        "name": "Fridtjof Nansen - Fram Expedition",
        "year": 1893,
        "nationality": "Norwegian",
        "type": "Arctic",
        "route": [[69.0, 170.0], [78.0, 135.0], [84.0, 100.0], [86.2, 96.0], [80.0, 20.0]],
        "color": "#22c55e",
        "result": "Record north; survived",
        "notes": "Froze Fram into pack ice to drift across Arctic; reached 86deg14'N on ski, closest to N. Pole at time",
    },
    {
        "name": "Robert Peary - North Pole (claimed)",
        "year": 1909,
        "nationality": "American",
        "type": "Arctic",
        "route": [[76.5, -68.8], [80.0, -70.0], [85.0, -70.0], [90.0, 0.0]],
        "color": "#a855f7",
        "result": "Claimed success (disputed)",
        "notes": "Claimed to reach North Pole Apr 6, 1909 from Cape Columbia, Ellesmere Island; disputed",
    },
    {
        "name": "Shackleton - Nimrod Expedition",
        "year": 1907,
        "nationality": "British",
        "type": "Antarctic",
        "route": [[-77.8, 166.7], [-80.0, 168.0], [-85.0, 170.0], [-88.4, 162.0]],
        "color": "#06b6d4",
        "result": "Turned back 97 miles from Pole",
        "notes": "Reached furthest south (88deg23'S) on Jan 9, 1909; turned back to save lives",
    },
    {
        "name": "Richard Byrd - Antarctic Flight",
        "year": 1929,
        "nationality": "American",
        "type": "Antarctic",
        "route": [[-78.5, 164.0], [-85.0, 170.0], [-90.0, 0.0], [-78.5, 164.0]],
        "color": "#f472b6",
        "result": "First flight over South Pole",
        "notes": "First flight over South Pole on Nov 29, 1929, from Little America base",
    },
    {
        "name": "Vivian Fuchs - Trans-Antarctic",
        "year": 1957,
        "nationality": "British",
        "type": "Antarctic",
        "route": [[-77.9, -34.0], [-82.0, -30.0], [-90.0, 0.0], [-77.8, 166.7]],
        "color": "#84cc16",
        "result": "First overland crossing of Antarctica",
        "notes": "Commonwealth Trans-Antarctic Expedition 1957-58; 99-day crossing with Sno-Cats",
    },
    {
        "name": "Umberto Nobile - Norge Airship",
        "year": 1926,
        "nationality": "Italian / Norwegian",
        "type": "Arctic",
        "route": [[78.2, 15.6], [85.0, 15.0], [90.0, 0.0], [64.5, -165.4]],
        "color": "#fb923c",
        "result": "First verified flight over North Pole",
        "notes": "Norge airship with Amundsen and Ellsworth; first undisputed journey over North Pole, May 12, 1926",
    },
    {
        "name": "Wally Herbert - Surface N. Pole",
        "year": 1969,
        "nationality": "British",
        "type": "Arctic",
        "route": [[71.3, -156.8], [80.0, -150.0], [90.0, 0.0], [80.0, 20.0], [79.0, 12.0]],
        "color": "#e11d48",
        "result": "First confirmed surface journey to N. Pole",
        "notes": "British Trans-Arctic Expedition 1968-69; dog sleds; first undisputed surface reach of North Pole",
    },
    {
        "name": "Douglas Mawson - Australasian Expedition",
        "year": 1911,
        "nationality": "Australian",
        "type": "Antarctic",
        "route": [[-67.0, 142.7], [-68.0, 143.0], [-68.5, 144.0], [-67.0, 142.7]],
        "color": "#14b8a6",
        "result": "Survived alone; two companions died",
        "notes": "Heroic solo survival trek; Mertz and Ninnis died; discovered George V Land",
    },
    {
        "name": "Adolphus Greely - Lady Franklin Bay",
        "year": 1881,
        "nationality": "American",
        "type": "Arctic",
        "route": [[81.7, -64.2], [83.4, -40.5], [81.7, -64.2], [78.7, -74.0]],
        "color": "#c084fc",
        "result": "Record north; 19 of 25 died",
        "notes": "Reached 83deg24'N (record); relief ships failed; rescued at Cape Sabine with 6 survivors",
    },
]

# =====================================================================
# 3. MOUNTAIN FIRST ASCENTS
# =====================================================================
MOUNTAIN_FIRST_ASCENTS = [
    {"name": "Mount Everest", "lat": 27.9881, "lon": 86.9250, "elevation_m": 8849, "first_ascent": "1953-05-29", "climbers": "Edmund Hillary, Tenzing Norgay", "country": "Nepal/China", "range": "Himalayas"},
    {"name": "K2", "lat": 35.8808, "lon": 76.5133, "elevation_m": 8611, "first_ascent": "1954-07-31", "climbers": "Achille Compagnoni, Lino Lacedelli", "country": "Pakistan/China", "range": "Karakoram"},
    {"name": "Kangchenjunga", "lat": 27.7025, "lon": 88.1475, "elevation_m": 8586, "first_ascent": "1955-05-25", "climbers": "Joe Brown, George Band", "country": "Nepal/India", "range": "Himalayas"},
    {"name": "Lhotse", "lat": 27.9617, "lon": 86.9333, "elevation_m": 8516, "first_ascent": "1956-05-18", "climbers": "Fritz Luchsinger, Ernst Reiss", "country": "Nepal/China", "range": "Himalayas"},
    {"name": "Makalu", "lat": 27.8897, "lon": 87.0886, "elevation_m": 8485, "first_ascent": "1955-05-15", "climbers": "Jean Couzy, Lionel Terray", "country": "Nepal/China", "range": "Himalayas"},
    {"name": "Cho Oyu", "lat": 28.0942, "lon": 86.6608, "elevation_m": 8188, "first_ascent": "1954-10-19", "climbers": "Herbert Tichy, Sepp Jochler, Pasang Dawa Lama", "country": "Nepal/China", "range": "Himalayas"},
    {"name": "Dhaulagiri", "lat": 28.6969, "lon": 83.4875, "elevation_m": 8167, "first_ascent": "1960-05-13", "climbers": "Kurt Diemberger, Peter Diener et al.", "country": "Nepal", "range": "Himalayas"},
    {"name": "Manaslu", "lat": 28.5497, "lon": 84.5594, "elevation_m": 8163, "first_ascent": "1956-05-09", "climbers": "Toshio Imanishi, Gyalzen Norbu", "country": "Nepal", "range": "Himalayas"},
    {"name": "Nanga Parbat", "lat": 35.2375, "lon": 74.5892, "elevation_m": 8126, "first_ascent": "1953-07-03", "climbers": "Hermann Buhl (solo)", "country": "Pakistan", "range": "Himalayas"},
    {"name": "Annapurna", "lat": 28.5961, "lon": 83.8203, "elevation_m": 8091, "first_ascent": "1950-06-03", "climbers": "Maurice Herzog, Louis Lachenal", "country": "Nepal", "range": "Himalayas"},
    {"name": "Matterhorn", "lat": 45.9764, "lon": 7.6586, "elevation_m": 4478, "first_ascent": "1865-07-14", "climbers": "Edward Whymper and party", "country": "Switzerland/Italy", "range": "Alps"},
    {"name": "Mont Blanc", "lat": 45.8326, "lon": 6.8652, "elevation_m": 4808, "first_ascent": "1786-08-08", "climbers": "Jacques Balmat, Michel-Gabriel Paccard", "country": "France/Italy", "range": "Alps"},
    {"name": "Denali (McKinley)", "lat": 63.0695, "lon": -151.0074, "elevation_m": 6190, "first_ascent": "1913-06-07", "climbers": "Hudson Stuck, Harry Karstens, Walter Harper, Robert Tatum", "country": "USA", "range": "Alaska Range"},
    {"name": "Aconcagua", "lat": -32.6532, "lon": -70.0109, "elevation_m": 6961, "first_ascent": "1897-01-14", "climbers": "Matthias Zurbriggen", "country": "Argentina", "range": "Andes"},
    {"name": "Kilimanjaro", "lat": -3.0674, "lon": 37.3556, "elevation_m": 5895, "first_ascent": "1889-10-06", "climbers": "Hans Meyer, Ludwig Purtscheller", "country": "Tanzania", "range": "Eastern Rift"},
    {"name": "Elbrus", "lat": 43.3499, "lon": 42.4453, "elevation_m": 5642, "first_ascent": "1874-07-28", "climbers": "Florence Crauford Grove, Frederick Gardner, Horace Walker, Peter Knubel", "country": "Russia", "range": "Caucasus"},
    {"name": "Vinson Massif", "lat": -78.5254, "lon": -85.6172, "elevation_m": 4892, "first_ascent": "1966-12-17", "climbers": "Nicholas Clinch and team", "country": "Antarctica", "range": "Sentinel Range"},
    {"name": "Puncak Jaya (Carstensz Pyramid)", "lat": -4.0833, "lon": 137.1833, "elevation_m": 4884, "first_ascent": "1962-02-13", "climbers": "Heinrich Harrer, Philip Temple, Russell Kippax, Albert Huizenga", "country": "Indonesia", "range": "Sudirman Range"},
    {"name": "Mount Kosciuszko", "lat": -36.4564, "lon": 148.2632, "elevation_m": 2228, "first_ascent": "1840-02-15", "climbers": "Paul Edmund de Strzelecki", "country": "Australia", "range": "Great Dividing Range"},
    {"name": "Eiger North Face", "lat": 46.5775, "lon": 8.0053, "elevation_m": 3967, "first_ascent": "1938-07-24", "climbers": "Anderl Heckmair, Ludwig Vorg, Heinrich Harrer, Fritz Kasparek", "country": "Switzerland", "range": "Alps"},
    {"name": "Cerro Torre", "lat": -49.2931, "lon": -73.1386, "elevation_m": 3128, "first_ascent": "1974-01-13", "climbers": "Casimiro Ferrari and team (first undisputed)", "country": "Argentina", "range": "Patagonian Andes"},
    {"name": "Fitz Roy", "lat": -49.2714, "lon": -73.0428, "elevation_m": 3405, "first_ascent": "1952-02-02", "climbers": "Lionel Terray, Guido Magnone", "country": "Argentina", "range": "Patagonian Andes"},
    {"name": "Mount Kenya", "lat": -0.1521, "lon": 37.3084, "elevation_m": 5199, "first_ascent": "1899-09-13", "climbers": "Halford Mackinder, Cesar Ollier, Joseph Brocherel", "country": "Kenya", "range": "Eastern Rift"},
    {"name": "Mount Olympus", "lat": 40.0859, "lon": 22.3583, "elevation_m": 2917, "first_ascent": "1913-08-02", "climbers": "Christos Kakkalos, Frederic Boissonnas, Daniel Baud-Bovy", "country": "Greece", "range": "Olympus"},
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274, "elevation_m": 3776, "first_ascent": "663 AD", "climbers": "Anonymous monk (En no Ozunu tradition)", "country": "Japan", "range": "Fuji Volcanic Zone"},
    {"name": "Mount Blanc du Tacul", "lat": 45.8558, "lon": 6.8875, "elevation_m": 4248, "first_ascent": "1855-08-08", "climbers": "Members of Alpine Club", "country": "France", "range": "Alps"},
    {"name": "Broad Peak", "lat": 35.8122, "lon": 76.5653, "elevation_m": 8051, "first_ascent": "1957-06-09", "climbers": "Fritz Wintersteller, Marcus Schmuck, Kurt Diemberger, Hermann Buhl", "country": "Pakistan/China", "range": "Karakoram"},
]

# =====================================================================
# 4. DEEP SEA EXPLORATION
# =====================================================================
DEEP_SEA_DIVES = [
    {"name": "Mariana Trench - Challenger Deep (Trieste)", "lat": 11.3493, "lon": 142.1996, "depth_m": 10916, "year": 1960, "vessel": "Trieste", "explorers": "Jacques Piccard, Don Walsh", "notes": "First manned descent to deepest point on Earth; 20 min on bottom"},
    {"name": "Mariana Trench - Challenger Deep (Cameron)", "lat": 11.3493, "lon": 142.1996, "depth_m": 10908, "year": 2012, "vessel": "Deepsea Challenger", "explorers": "James Cameron", "notes": "First solo dive to Challenger Deep; spent 3 hours on bottom"},
    {"name": "Mariana Trench - Challenger Deep (Vescovo)", "lat": 11.3493, "lon": 142.1996, "depth_m": 10928, "year": 2019, "vessel": "DSV Limiting Factor", "explorers": "Victor Vescovo", "notes": "Deepest dive ever recorded; part of Five Deeps Expedition"},
    {"name": "RMS Titanic Wreck Site", "lat": 41.7260, "lon": -49.9469, "depth_m": 3800, "year": 1985, "vessel": "Argo / Alvin", "explorers": "Robert Ballard, Jean-Louis Michel", "notes": "Discovery of Titanic wreck using towed camera sled; first manned visit 1986"},
    {"name": "Bismarck Wreck Site", "lat": 48.9167, "lon": -16.2000, "depth_m": 4791, "year": 1989, "vessel": "Argo", "explorers": "Robert Ballard", "notes": "Found the WWII German battleship upright on a volcanic slope"},
    {"name": "RMS Lusitania Wreck", "lat": 51.3833, "lon": -8.5500, "depth_m": 93, "year": 1935, "vessel": "Diving bell", "explorers": "Jim Jarrett", "notes": "First dives in 1935; controversial torpedo evidence explored over decades"},
    {"name": "Hydrothermal Vents Discovery (Galapagos)", "lat": 0.7930, "lon": -86.1380, "depth_m": 2500, "year": 1977, "vessel": "Alvin", "explorers": "John Corliss, Jack Dymond", "notes": "First discovery of deep-sea hydrothermal vents; chemosynthetic life revolution"},
    {"name": "Black Smokers (East Pacific Rise)", "lat": 20.8333, "lon": -109.1500, "depth_m": 2600, "year": 1979, "vessel": "Alvin", "explorers": "RISE Project team", "notes": "First black smoker discovery; 350C superheated water; tube worms"},
    {"name": "USS Scorpion Wreck", "lat": 32.9167, "lon": -33.1500, "depth_m": 3050, "year": 1968, "vessel": "Trieste II / towed cameras", "explorers": "US Navy", "notes": "Nuclear submarine lost with 99 crew; cause still debated"},
    {"name": "HMHS Britannic Wreck", "lat": 37.7283, "lon": 24.2833, "depth_m": 120, "year": 1975, "vessel": "Free diving / submersible", "explorers": "Jacques Cousteau", "notes": "Titanic's sister ship; Cousteau explored wreck in Kea Channel, Greece"},
    {"name": "Lost City Hydrothermal Field", "lat": 30.1250, "lon": -42.1200, "depth_m": 750, "year": 2000, "vessel": "Alvin", "explorers": "Deborah Kelley", "notes": "Alkaline vents unlike black smokers; possible origin-of-life site; 60m tall carbonate towers"},
    {"name": "Endurance Wreck (Shackleton)", "lat": -68.7500, "lon": -52.3333, "depth_m": 3008, "year": 2022, "vessel": "Saab Sabertooth", "explorers": "Endurance22 expedition", "notes": "Found in remarkable condition in Weddell Sea; world's deepest wooden shipwreck"},
    {"name": "Tonga Trench Dive", "lat": -23.2500, "lon": -174.7000, "depth_m": 10823, "year": 2019, "vessel": "DSV Limiting Factor", "explorers": "Victor Vescovo", "notes": "Deepest point in South Pacific; Five Deeps Expedition"},
    {"name": "Puerto Rico Trench Dive", "lat": 19.7333, "lon": -67.2333, "depth_m": 8376, "year": 2019, "vessel": "DSV Limiting Factor", "explorers": "Victor Vescovo", "notes": "Deepest point in Atlantic Ocean; Five Deeps Expedition"},
    {"name": "Molloy Deep (Arctic)", "lat": 79.1500, "lon": 2.8167, "depth_m": 5669, "year": 2019, "vessel": "DSV Limiting Factor", "explorers": "Victor Vescovo", "notes": "Deepest point in Arctic Ocean; Five Deeps Expedition"},
    {"name": "South Sandwich Trench", "lat": -55.2500, "lon": -25.9167, "depth_m": 8264, "year": 2019, "vessel": "DSV Limiting Factor", "explorers": "Victor Vescovo", "notes": "Deepest point in Southern Ocean; Five Deeps Expedition"},
    {"name": "Java Trench (Sunda)", "lat": -10.3833, "lon": 110.0167, "depth_m": 7290, "year": 2019, "vessel": "DSV Limiting Factor", "explorers": "Victor Vescovo", "notes": "Deepest point in Indian Ocean; Five Deeps Expedition"},
    {"name": "Mid-Atlantic Ridge Exploration", "lat": 36.2333, "lon": -33.2167, "depth_m": 2300, "year": 1974, "vessel": "Alvin / Archimede / Cyana", "explorers": "Project FAMOUS team", "notes": "First direct observation of mid-ocean ridge; confirmed plate tectonics"},
    {"name": "San Jose Galleon Wreck", "lat": 10.3833, "lon": -75.8167, "depth_m": 600, "year": 2015, "vessel": "REMUS 6000 AUV", "explorers": "Colombian Navy / Woods Hole", "notes": "Holy grail of shipwrecks; possibly $17B in gold and emeralds; sunk 1708"},
    {"name": "Monterey Canyon Exploration", "lat": 36.7833, "lon": -122.0000, "depth_m": 3600, "year": 1992, "vessel": "ROV Ventana / Tiburon", "explorers": "MBARI", "notes": "Ongoing deep-sea research; canyon rivals Grand Canyon in size; 150+ new species"},
]

# =====================================================================
# 5. SPACE LAUNCH SITES
# =====================================================================
SPACE_LAUNCH_SITES = [
    {"name": "Kennedy Space Center (LC-39)", "lat": 28.5721, "lon": -80.6480, "country": "USA", "agency": "NASA / SpaceX", "first_launch": 1967, "notable": "Apollo, Shuttle, Falcon 9, Artemis", "status": "Active"},
    {"name": "Cape Canaveral SFS", "lat": 28.4889, "lon": -80.5778, "country": "USA", "agency": "USSF / ULA / SpaceX", "first_launch": 1950, "notable": "First US orbital launch (Explorer 1)", "status": "Active"},
    {"name": "Vandenberg SFB", "lat": 34.7420, "lon": -120.5724, "country": "USA", "agency": "USSF / SpaceX / ULA", "first_launch": 1958, "notable": "Polar orbit launches; SpaceX Starship pad", "status": "Active"},
    {"name": "Baikonur Cosmodrome", "lat": 45.9650, "lon": 63.3050, "country": "Kazakhstan", "agency": "Roscosmos", "first_launch": 1957, "notable": "Sputnik, Vostok (Gagarin), Soyuz, ISS crew", "status": "Active"},
    {"name": "Plesetsk Cosmodrome", "lat": 62.9271, "lon": 40.5777, "country": "Russia", "agency": "Roscosmos", "first_launch": 1966, "notable": "Most launched-from site in history (1600+)", "status": "Active"},
    {"name": "Vostochny Cosmodrome", "lat": 51.8844, "lon": 128.3336, "country": "Russia", "agency": "Roscosmos", "first_launch": 2016, "notable": "Russia's newest cosmodrome; replacing Baikonur dependency", "status": "Active"},
    {"name": "Guiana Space Centre (Kourou)", "lat": 5.2360, "lon": -52.7686, "country": "French Guiana", "agency": "ESA / Arianespace / CNES", "first_launch": 1968, "notable": "Ariane 5/6, Vega, Soyuz; near equator advantage", "status": "Active"},
    {"name": "Jiuquan Satellite Launch Center", "lat": 40.9675, "lon": 100.2781, "country": "China", "agency": "CNSA / CASC", "first_launch": 1970, "notable": "China's first spaceport; Shenzhou crewed missions", "status": "Active"},
    {"name": "Xichang Satellite Launch Center", "lat": 28.2461, "lon": 102.0264, "country": "China", "agency": "CNSA / CASC", "first_launch": 1984, "notable": "BeiDou, Chang'e lunar missions", "status": "Active"},
    {"name": "Wenchang Space Launch Site", "lat": 19.6145, "lon": 110.9510, "country": "China", "agency": "CNSA / CASC", "first_launch": 2016, "notable": "China Space Station modules; Long March 5", "status": "Active"},
    {"name": "Taiyuan Satellite Launch Center", "lat": 38.8489, "lon": 111.6081, "country": "China", "agency": "CNSA / CASC", "first_launch": 1988, "notable": "Sun-synchronous orbit launches", "status": "Active"},
    {"name": "Satish Dhawan Space Centre (Sriharikota)", "lat": 13.7199, "lon": 80.2304, "country": "India", "agency": "ISRO", "first_launch": 1971, "notable": "Chandrayaan, Mangalyaan, PSLV/GSLV", "status": "Active"},
    {"name": "Tanegashima Space Center", "lat": 30.4000, "lon": 131.0000, "country": "Japan", "agency": "JAXA", "first_launch": 1975, "notable": "H-IIA/H3 rockets; Hayabusa missions", "status": "Active"},
    {"name": "Uchinoura Space Center", "lat": 31.2510, "lon": 131.0790, "country": "Japan", "agency": "JAXA", "first_launch": 1962, "notable": "Japan's first satellite launch (Ohsumi 1970)", "status": "Active"},
    {"name": "Naro Space Center", "lat": 34.4317, "lon": 127.5350, "country": "South Korea", "agency": "KARI", "first_launch": 2009, "notable": "Nuri (KSLV-II) orbital success 2022", "status": "Active"},
    {"name": "Palmachim Airbase", "lat": 31.8836, "lon": 34.6842, "country": "Israel", "agency": "ISA / IAI", "first_launch": 1988, "notable": "Shavit rocket; westward launch over Mediterranean", "status": "Active"},
    {"name": "Semnan Space Center", "lat": 35.2345, "lon": 53.9210, "country": "Iran", "agency": "ISA (Iran)", "first_launch": 2009, "notable": "Safir, Simorgh rockets", "status": "Active"},
    {"name": "Esrange Space Center", "lat": 67.8933, "lon": 21.1064, "country": "Sweden", "agency": "SSC", "first_launch": 1966, "notable": "Sounding rockets; future orbital launches planned", "status": "Active"},
    {"name": "Rocket Lab Launch Complex 1", "lat": -39.2615, "lon": 177.8649, "country": "New Zealand", "agency": "Rocket Lab", "first_launch": 2017, "notable": "Electron rocket; first private orbital launch from S. Hemisphere", "status": "Active"},
    {"name": "SpaceX Starbase (Boca Chica)", "lat": 25.9972, "lon": -97.1567, "country": "USA", "agency": "SpaceX", "first_launch": 2023, "notable": "Starship / Super Heavy development and launches", "status": "Active"},
    {"name": "Wallops Flight Facility", "lat": 37.9402, "lon": -75.4664, "country": "USA", "agency": "NASA / Northrop Grumman", "first_launch": 1945, "notable": "Antares/Cygnus ISS resupply; sounding rockets since 1945", "status": "Active"},
    {"name": "Alcantara Launch Center", "lat": -2.3733, "lon": -44.3964, "country": "Brazil", "agency": "AEB", "first_launch": 1990, "notable": "Closest major spaceport to equator; VLS program", "status": "Active"},
    {"name": "San Marco Platform (historic)", "lat": -2.9383, "lon": 40.2133, "country": "Kenya (Italian)", "agency": "ASI (Italy)", "first_launch": 1967, "notable": "Sea-based equatorial launch platform; 9 orbital launches", "status": "Decommissioned"},
    {"name": "Rocket Lab Launch Complex 2", "lat": 37.8403, "lon": -75.4878, "country": "USA", "agency": "Rocket Lab", "first_launch": 2023, "notable": "Electron launches from Virginia; HASTE suborbital", "status": "Active"},
    {"name": "Kodiak Launch Complex", "lat": 57.4358, "lon": -152.3378, "country": "USA", "agency": "Alaska Aerospace / Astra", "first_launch": 1998, "notable": "Polar and sun-synchronous orbits from Alaska", "status": "Active"},
    {"name": "Thumba Equatorial Rocket Launching Station", "lat": 8.5372, "lon": 76.8653, "country": "India", "agency": "ISRO", "first_launch": 1963, "notable": "India's first rocket launch (Nike-Apache sounding rocket)", "status": "Active (sounding)"},
    {"name": "Hammaguir Launch Site (historic)", "lat": 31.0167, "lon": -3.0500, "country": "Algeria (French)", "agency": "CNES", "first_launch": 1952, "notable": "France's first satellite (Asterix 1965); closed after Algerian independence", "status": "Decommissioned"},
]

# =====================================================================
# 6. ANCIENT TRADE ROUTES
# =====================================================================
ANCIENT_TRADE_ROUTES = [
    {
        "name": "Silk Road (Main Land Route)",
        "period": "130 BC - 1450 AD",
        "route": [[34.3, 108.9], [36.0, 103.8], [39.7, 98.5], [40.5, 90.0],
                  [41.3, 80.0], [39.7, 67.0], [38.6, 55.0], [35.7, 51.4],
                  [33.3, 44.4], [36.2, 37.0], [41.0, 29.0]],
        "color": "#ef4444",
        "goods": "Silk, spices, gold, jade, paper, gunpowder",
        "notes": "Greatest trade network in history; connected China to Rome; 6,500+ km overland",
    },
    {
        "name": "Amber Road",
        "period": "1600 BC - 500 AD",
        "route": [[54.4, 18.6], [52.2, 21.0], [50.1, 19.9], [48.2, 16.4],
                  [47.5, 14.6], [46.1, 13.0], [45.4, 12.3], [41.9, 12.5]],
        "color": "#f59e0b",
        "goods": "Baltic amber, furs, salt, metals",
        "notes": "Linked Baltic Sea to Mediterranean; amber prized like gold in antiquity",
    },
    {
        "name": "Incense Route",
        "period": "700 BC - 200 AD",
        "route": [[15.3, 44.2], [17.0, 42.0], [20.0, 41.0], [24.5, 39.6],
                  [26.2, 36.6], [29.5, 35.0], [31.2, 34.4], [31.8, 35.2]],
        "color": "#22c55e",
        "goods": "Frankincense, myrrh, spices",
        "notes": "From Yemen through Arabia to Petra and Gaza; UNESCO desert cities along route",
    },
    {
        "name": "Trans-Saharan Trade Routes",
        "period": "300 BC - 1600 AD",
        "route": [[36.8, 3.0], [32.5, 0.0], [27.0, -2.0], [22.0, -3.0],
                  [17.0, -1.0], [14.0, -2.0], [12.6, -8.0]],
        "color": "#a855f7",
        "goods": "Gold, salt, slaves, ivory, kola nuts",
        "notes": "Connected West Africa (Ghana, Mali, Songhai) to Mediterranean; camel caravans across Sahara",
    },
    {
        "name": "Spice Route (Maritime)",
        "period": "200 BC - 1700 AD",
        "route": [[-6.2, 106.8], [1.3, 103.8], [7.0, 80.0], [12.0, 45.0],
                  [12.5, 43.3], [30.0, 32.5], [38.0, 24.0], [41.0, 29.0],
                  [45.4, 12.3]],
        "color": "#06b6d4",
        "goods": "Pepper, cinnamon, cloves, nutmeg, cardamom",
        "notes": "Maritime route from Spice Islands to Europe via Indian Ocean, Red Sea, and Mediterranean",
    },
    {
        "name": "Tin Route (Atlantic)",
        "period": "2000 BC - 100 BC",
        "route": [[50.2, -5.0], [48.4, -4.5], [47.5, -3.0], [43.4, -8.4],
                  [37.0, -7.0], [36.8, -6.3], [36.0, 10.0]],
        "color": "#84cc16",
        "goods": "Tin, copper, bronze, gold",
        "notes": "Phoenician route from Cornwall (tin mines) to Mediterranean; critical for Bronze Age",
    },
    {
        "name": "Via Salaria (Roman Salt Road)",
        "period": "600 BC - 200 AD",
        "route": [[41.9, 12.5], [42.3, 12.9], [42.5, 13.3], [42.7, 13.7],
                  [42.9, 13.9]],
        "color": "#f472b6",
        "goods": "Salt, agricultural goods",
        "notes": "Roman road from Rome to Adriatic Sea; salt was essential currency (origin of 'salary')",
    },
    {
        "name": "Tea Horse Road",
        "period": "600 AD - 1900 AD",
        "route": [[25.0, 102.7], [27.0, 100.2], [29.6, 98.0], [30.0, 97.0],
                  [29.6, 91.1], [27.5, 89.6]],
        "color": "#e11d48",
        "goods": "Tea, horses, salt, sugar, furs",
        "notes": "Ancient network from Yunnan and Sichuan to Tibet and India; tea bricks for Tibetan horses",
    },
    {
        "name": "King's Highway (Ancient Near East)",
        "period": "3000 BC - 300 AD",
        "route": [[30.0, 31.2], [30.5, 32.3], [29.5, 35.0], [31.2, 35.5],
                  [32.0, 36.0], [33.5, 36.3], [35.2, 38.0], [36.3, 43.1]],
        "color": "#fb923c",
        "goods": "Copper, incense, spices, textiles",
        "notes": "One of the oldest trade routes; connected Egypt through Sinai, Jordan, Syria to Mesopotamia",
    },
    {
        "name": "Varangian Route (Vikings to Constantinople)",
        "period": "800 AD - 1100 AD",
        "route": [[59.9, 30.3], [58.5, 31.3], [56.3, 30.5], [53.9, 30.3],
                  [50.5, 30.5], [48.5, 34.0], [46.5, 35.0], [44.0, 37.0],
                  [41.0, 29.0]],
        "color": "#14b8a6",
        "goods": "Furs, honey, wax, slaves, silver, silk",
        "notes": "Route from the Varangians (Vikings) to the Greeks; through Dnieper river system to Constantinople",
    },
]

# =====================================================================
# 7. FIRST CONTACTS & DISCOVERIES
# =====================================================================
FIRST_CONTACTS = [
    {"name": "Americas (Columbus)", "lat": 24.0, "lon": -74.5, "year": 1492, "explorer": "Christopher Columbus", "nationality": "Genoese / Spain", "notes": "Reached San Salvador (Bahamas) Oct 12, 1492; believed he reached Asia"},
    {"name": "Australia (Dutch sighting)", "lat": -13.8, "lon": 126.8, "year": 1606, "explorer": "Willem Janszoon", "nationality": "Dutch", "notes": "First European to sight and land on Australian continent (Cape York)"},
    {"name": "Australia (Cook / East Coast)", "lat": -33.8, "lon": 151.2, "year": 1770, "explorer": "James Cook", "nationality": "British", "notes": "Charted east coast; claimed for Britain at Botany Bay"},
    {"name": "New Zealand", "lat": -38.7, "lon": 176.3, "year": 1642, "explorer": "Abel Tasman", "nationality": "Dutch", "notes": "First European sighting Dec 13, 1642; Maori already present 700+ years"},
    {"name": "Easter Island (Rapa Nui)", "lat": -27.1, "lon": -109.3, "year": 1722, "explorer": "Jacob Roggeveen", "nationality": "Dutch", "notes": "Discovered on Easter Sunday 1722; famous for Moai statues"},
    {"name": "Hawaii", "lat": 19.8, "lon": -155.5, "year": 1778, "explorer": "James Cook", "nationality": "British", "notes": "First European contact Jan 1778; Cook killed in 1779 on return visit"},
    {"name": "Tahiti", "lat": -17.5, "lon": -149.5, "year": 1767, "explorer": "Samuel Wallis", "nationality": "British", "notes": "HMS Dolphin first European ship; followed by Bougainville (French) and Cook"},
    {"name": "Brazil", "lat": -16.3, "lon": -39.0, "year": 1500, "explorer": "Pedro Alvares Cabral", "nationality": "Portuguese", "notes": "Landed at Porto Seguro Apr 22, 1500; claimed for Portugal"},
    {"name": "Newfoundland (Viking)", "lat": 51.6, "lon": -55.5, "year": 1000, "explorer": "Leif Erikson", "nationality": "Norse", "notes": "L'Anse aux Meadows settlement; first Europeans in Americas ~500 years before Columbus"},
    {"name": "Cape of Good Hope", "lat": -34.4, "lon": 18.5, "year": 1488, "explorer": "Bartolomeu Dias", "nationality": "Portuguese", "notes": "Rounded the cape 1488; opened sea route to India"},
    {"name": "Galapagos Islands", "lat": -0.95, "lon": -90.97, "year": 1535, "explorer": "Fray Tomas de Berlanga", "nationality": "Spanish", "notes": "Bishop of Panama blown off course; later made famous by Darwin 1835"},
    {"name": "Madagascar", "lat": -18.9, "lon": 47.5, "year": 1500, "explorer": "Diogo Dias", "nationality": "Portuguese", "notes": "First European sighting Aug 10, 1500; already settled by Austronesians 1500+ years prior"},
    {"name": "Tonga", "lat": -21.2, "lon": -175.2, "year": 1616, "explorer": "Willem Schouten, Jacob Le Maire", "nationality": "Dutch", "notes": "First Europeans to visit; Cook later named them Friendly Islands"},
    {"name": "Strait of Magellan", "lat": -52.5, "lon": -70.0, "year": 1520, "explorer": "Ferdinand Magellan", "nationality": "Portuguese / Spain", "notes": "Navigated treacherous passage Oct-Nov 1520; named Pacific Ocean"},
    {"name": "Mississippi River", "lat": 29.0, "lon": -89.2, "year": 1541, "explorer": "Hernando de Soto", "nationality": "Spanish", "notes": "First European to cross the Mississippi; died on its banks 1542"},
    {"name": "Victoria Falls", "lat": -17.9, "lon": 25.9, "year": 1855, "explorer": "David Livingstone", "nationality": "British (Scottish)", "notes": "Named after Queen Victoria; locals called it Mosi-oa-Tunya (Smoke That Thunders)"},
    {"name": "Source of the Nile (Lake Victoria)", "lat": -1.3, "lon": 33.0, "year": 1858, "explorer": "John Hanning Speke", "nationality": "British", "notes": "Identified Lake Victoria as source; confirmed 1862; ended centuries of speculation"},
    {"name": "Papua New Guinea Interior", "lat": -5.5, "lon": 145.8, "year": 1930, "explorer": "Michael Leahy, Michael Dwyer", "nationality": "Australian", "notes": "First contact with Highland peoples 1930; one million people unknown to outside world"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "year": 1911, "explorer": "Hiram Bingham III", "nationality": "American", "notes": "Rediscovered lost Inca citadel Jul 24, 1911; locals already knew of it"},
    {"name": "Antarctica (Sighting)", "lat": -69.4, "lon": -2.2, "year": 1820, "explorer": "Fabian von Bellingshausen", "nationality": "Russian", "notes": "First confirmed sighting of Antarctic continent Jan 27, 1820"},
]

# =====================================================================
# 8. CARTOGRAPHIC MILESTONES
# =====================================================================
CARTOGRAPHIC_MILESTONES = [
    {"name": "Ptolemy's Geographia", "lat": 31.2, "lon": 29.9, "year": "~150 AD", "person": "Claudius Ptolemy", "location": "Alexandria, Egypt", "contribution": "Codified latitude/longitude grid; listed 8,000 places; influenced mapmaking for 1,400 years"},
    {"name": "Al-Idrisi's Tabula Rogeriana", "lat": 38.1, "lon": 13.4, "year": "1154", "person": "Muhammad al-Idrisi", "location": "Palermo, Sicily", "contribution": "Most accurate medieval world map; created for Roger II of Sicily; south-oriented"},
    {"name": "Fra Mauro World Map", "lat": 45.4, "lon": 12.3, "year": "1450", "person": "Fra Mauro", "location": "Venice, Italy", "contribution": "Most detailed world map of the 15th century; commissioned by Portugal; challenged Ptolemy"},
    {"name": "Waldseemuller Map (Naming America)", "lat": 48.3, "lon": 6.9, "year": "1507", "person": "Martin Waldseemuller", "location": "Saint-Die-des-Vosges, France", "contribution": "First map to name the New World 'America' after Amerigo Vespucci; only surviving copy at Library of Congress"},
    {"name": "Mercator Projection", "lat": 51.0, "lon": 3.7, "year": "1569", "person": "Gerardus Mercator", "location": "Duisburg, Germany (born Flanders)", "contribution": "Created conformal cylindrical projection; revolutionized navigation; still used today"},
    {"name": "Harrison's Marine Chronometer (H4)", "lat": 53.7, "lon": -0.3, "year": "1761", "person": "John Harrison", "location": "Barrow-upon-Humber, England", "contribution": "Solved the longitude problem; H4 clock enabled precise navigation; tested on voyage to Jamaica"},
    {"name": "Ordnance Survey Founded", "lat": 50.7, "lon": -1.3, "year": "1791", "person": "Board of Ordnance", "location": "Tower of London / Southampton, UK", "contribution": "First national mapping agency; began surveying Britain; set standard for topographic mapping worldwide"},
    {"name": "Cassini Map of France", "lat": 48.8, "lon": 2.3, "year": "1789", "person": "Cassini family (four generations)", "location": "Paris Observatory, France", "contribution": "First topographic map of an entire nation; 182 sheets; took 4 generations of Cassinis"},
    {"name": "Eratosthenes Measures Earth", "lat": 31.2, "lon": 29.9, "year": "~240 BC", "person": "Eratosthenes", "location": "Alexandria, Egypt", "contribution": "Calculated Earth's circumference using shadows and geometry; remarkably accurate (within 2%)"},
    {"name": "Piri Reis Map", "lat": 41.0, "lon": 29.0, "year": "1513", "person": "Piri Reis", "location": "Constantinople (Istanbul)", "contribution": "Early map showing Americas; compiled from 20+ sources including possibly Columbus's charts"},
    {"name": "Behaim Globe (Erdapfel)", "lat": 49.5, "lon": 11.1, "year": "1492", "person": "Martin Behaim", "location": "Nuremberg, Germany", "contribution": "Oldest surviving terrestrial globe; made just before Columbus returned; no Americas"},
    {"name": "Portolan Charts Origin", "lat": 41.4, "lon": 2.2, "year": "~1275", "person": "Unknown (Carta Pisana)", "location": "Genoa / Pisa, Italy", "contribution": "First accurate navigation charts using compass bearings; rhumb lines; Mediterranean focused"},
    {"name": "Hereford Mappa Mundi", "lat": 52.1, "lon": -2.7, "year": "~1300", "person": "Richard of Haldingham", "location": "Hereford Cathedral, England", "contribution": "Largest known medieval map; theological world view with Jerusalem at center; 1,100 drawings"},
    {"name": "Cantino Planisphere", "lat": 44.8, "lon": 11.6, "year": "1502", "person": "Unknown Portuguese cartographer", "location": "Ferrara, Italy (smuggled from Lisbon)", "contribution": "Earliest map showing Portuguese discoveries in Brazil, Africa, India; secret espionage acquisition"},
    {"name": "Survey of India / Great Trigonometrical Survey", "lat": 21.1, "lon": 79.1, "year": "1802", "person": "William Lambton, George Everest", "location": "India (subcontinent-wide)", "contribution": "Measured arc of meridian across India; determined height of Himalayas; Mount Everest named for George Everest"},
    {"name": "US Geological Survey Founded", "lat": 38.9, "lon": -77.0, "year": "1879", "person": "Clarence King (first director)", "location": "Washington, D.C., USA", "contribution": "National mapping and geological survey; topo maps covering entire US; set global standards"},
    {"name": "Prime Meridian Established", "lat": 51.48, "lon": 0.0, "year": "1884", "person": "International Meridian Conference", "location": "Greenwich, London, England", "contribution": "Established Greenwich as 0 degrees longitude; standardized global time zones; 25 nations agreed"},
    {"name": "GPS System Operational", "lat": 38.8, "lon": -104.8, "year": "1995", "person": "US Department of Defense", "location": "Schriever AFB, Colorado, USA", "contribution": "Global Positioning System fully operational; 24 satellites; revolutionized navigation and mapping"},
]

# =====================================================================
# 9. SCIENTIFIC EXPEDITIONS
# =====================================================================
SCIENTIFIC_EXPEDITIONS = [
    {
        "name": "HMS Beagle (Darwin)",
        "year": "1831-1836",
        "leader": "Robert FitzRoy (captain), Charles Darwin (naturalist)",
        "route": [[50.4, -4.1], [28.0, -16.0], [-22.9, -43.2], [-51.8, -59.0],
                  [-33.4, -70.7], [-0.95, -90.97], [-17.5, -149.5],
                  [-33.9, 151.2], [-6.2, 106.0], [-34.0, 25.0], [50.4, -4.1]],
        "color": "#ef4444",
        "field": "Biology / Geology",
        "notes": "Darwin's observations led to theory of evolution by natural selection; visited Galapagos 1835",
    },
    {
        "name": "HMS Challenger Expedition",
        "year": "1872-1876",
        "leader": "Sir Charles Wyville Thomson, John Murray",
        "route": [[50.8, -1.4], [28.5, -16.0], [-33.0, -52.0], [-34.0, 25.0],
                  [-37.0, 140.0], [-55.0, 170.0], [-17.5, -149.5], [-33.4, -70.7],
                  [50.8, -1.4]],
        "color": "#3b82f6",
        "field": "Oceanography",
        "notes": "Birth of modern oceanography; 68,890 nautical miles; discovered 4,700 new species; sounded Mariana Trench",
    },
    {
        "name": "Kon-Tiki Expedition",
        "year": "1947",
        "leader": "Thor Heyerdahl",
        "route": [[-12.0, -77.0], [-10.0, -90.0], [-10.0, -110.0],
                  [-12.0, -130.0], [-14.0, -138.8]],
        "color": "#f59e0b",
        "field": "Anthropology / Navigation",
        "notes": "Balsa wood raft from Peru to Polynesia; proved ancient trans-Pacific contact was possible; 101 days",
    },
    {
        "name": "Alexander von Humboldt (Americas)",
        "year": "1799-1804",
        "leader": "Alexander von Humboldt, Aime Bonpland",
        "route": [[36.7, -6.3], [28.5, -16.0], [10.5, -66.9], [4.6, -74.1],
                  [-0.2, -78.5], [-12.0, -77.0], [19.4, -99.1], [23.1, -82.4],
                  [39.0, -77.0], [48.8, 2.3]],
        "color": "#22c55e",
        "field": "Natural History / Geography",
        "notes": "Father of modern geography; mapped currents, plant zones, volcanoes; coined concepts of ecology",
    },
    {
        "name": "Lewis and Clark Expedition",
        "year": "1804-1806",
        "leader": "Meriwether Lewis, William Clark",
        "route": [[38.6, -90.2], [41.3, -96.0], [43.0, -100.0], [46.8, -111.0],
                  [46.0, -115.0], [46.2, -124.0]],
        "color": "#a855f7",
        "field": "Geography / Natural History",
        "notes": "Explored Louisiana Purchase to Pacific; documented 300 species; mapped American West",
    },
    {
        "name": "HMS Endeavour (Cook's Transit of Venus)",
        "year": "1768-1771",
        "leader": "James Cook, Joseph Banks",
        "route": [[50.4, -3.5], [28.5, -16.0], [-22.9, -43.2], [-55.0, -68.0],
                  [-17.5, -149.5], [-41.0, 174.0], [-34.0, 151.0], [-6.2, 106.0],
                  [-34.0, 25.0], [50.4, -3.5]],
        "color": "#06b6d4",
        "field": "Astronomy / Botany / Cartography",
        "notes": "Observed Transit of Venus in Tahiti; Banks collected 30,000 plant specimens; charted New Zealand",
    },
    {
        "name": "Vostok and Mirny (Bellingshausen)",
        "year": "1819-1821",
        "leader": "Fabian von Bellingshausen, Mikhail Lazarev",
        "route": [[-33.0, -52.0], [-55.0, -36.0], [-69.0, -2.0],
                  [-65.0, 90.0], [-66.0, 160.0], [-55.0, -36.0]],
        "color": "#e11d48",
        "field": "Geography / Exploration",
        "notes": "First confirmed sighting of Antarctic continent Jan 27, 1820; circumnavigated Antarctica",
    },
    {
        "name": "Fridtjof Nansen - Greenland Crossing",
        "year": "1888",
        "leader": "Fridtjof Nansen",
        "route": [[65.6, -38.0], [65.6, -35.0], [65.6, -30.0],
                  [64.2, -51.7]],
        "color": "#84cc16",
        "field": "Geography / Glaciology",
        "notes": "First crossing of Greenland ice sheet; east to west; proved interior was ice cap",
    },
    {
        "name": "Ra II Expedition (Heyerdahl)",
        "year": "1970",
        "leader": "Thor Heyerdahl",
        "route": [[33.6, -7.6], [30.0, -20.0], [25.0, -40.0],
                  [13.2, -59.6]],
        "color": "#f472b6",
        "field": "Anthropology / Navigation",
        "notes": "Papyrus boat from Morocco to Barbados; proved ancient Egyptians could have crossed Atlantic",
    },
    {
        "name": "Vitus Bering (Great Northern Expedition)",
        "year": "1733-1743",
        "leader": "Vitus Bering",
        "route": [[59.9, 30.3], [56.5, 60.0], [55.0, 83.0], [56.0, 106.0],
                  [62.0, 130.0], [59.0, 143.0], [53.0, 159.0], [57.8, -152.4]],
        "color": "#fb923c",
        "field": "Geography / Natural History",
        "notes": "Mapped Siberian coast and Alaska; proved Asia and America not connected; died on Bering Island",
    },
]

# =====================================================================
# 10. LAST UNEXPLORED PLACES
# =====================================================================
LAST_UNEXPLORED = [
    {"name": "North Sentinel Island", "lat": 11.5500, "lon": 92.2333, "region": "Andaman Islands, India", "area_km2": 60, "status": "Forbidden / Protected", "notes": "Sentinelese people refuse all contact; killed visitors in 2006 and 2018; Indian law forbids approach"},
    {"name": "Darien Gap", "lat": 7.5, "lon": -77.5, "region": "Panama / Colombia", "area_km2": 16000, "status": "Roadless jungle", "notes": "Only break in Pan-American Highway; dense jungle, swamps, paramilitaries; extremely dangerous"},
    {"name": "Vale do Javari (Uncontacted Tribes)", "lat": -5.5, "lon": -72.0, "region": "Amazon, Brazil", "area_km2": 85445, "status": "Protected indigenous territory", "notes": "Largest concentration of uncontacted peoples on Earth; 14+ isolated groups; FUNAI protected"},
    {"name": "Gangkhar Puensum", "lat": 28.0422, "lon": 90.4583, "region": "Bhutan / China", "area_km2": 0, "status": "Climbing forbidden", "notes": "Highest unclimbed mountain (7,570m); Bhutan banned mountaineering above 6,000m in 1994"},
    {"name": "Tepui Summits (Venezuela)", "lat": 5.2, "lon": -62.5, "region": "Venezuela / Guyana", "area_km2": 5000, "status": "Remote plateaus", "notes": "Isolated tabletop mountains; unique endemic species; inspired Conan Doyle's Lost World; many unsurveyed"},
    {"name": "Son Doong Cave Interior", "lat": 17.5433, "lon": 106.1453, "region": "Vietnam", "area_km2": 0.04, "status": "Restricted access", "notes": "World's largest cave passage; only discovered 2009; jungle and clouds inside; limited exploration permits"},
    {"name": "Kamchatka Interior", "lat": 55.0, "lon": 159.0, "region": "Russia", "area_km2": 270000, "status": "Remote wilderness", "notes": "Volcanic peninsula; 300+ volcanoes; one of most sparsely populated areas; many valleys unsurveyed"},
    {"name": "Star Mountains (Papua New Guinea)", "lat": -5.0, "lon": 141.0, "region": "Papua New Guinea", "area_km2": 15000, "status": "Uncontacted tribes remain", "notes": "Extremely rugged terrain; first contacts still occurring; unknown species; some of last blank spots on maps"},
    {"name": "Tsingy de Bemaraha", "lat": -18.7, "lon": 44.7, "region": "Madagascar", "area_km2": 1520, "status": "UNESCO / Difficult access", "notes": "Razor-sharp limestone forest; virtually impassable on foot; unknown species discovered regularly"},
    {"name": "Northern Greenland Ice Sheet", "lat": 80.0, "lon": -40.0, "region": "Greenland (Denmark)", "area_km2": 410000, "status": "Ice-covered", "notes": "Sub-glacial landscape never seen by humans; radar reveals mountains, rivers, lakes beneath 3km of ice"},
    {"name": "Lake Vostok (Sub-glacial)", "lat": -77.5, "lon": 106.0, "region": "Antarctica", "area_km2": 12500, "status": "Sealed under 4km of ice", "notes": "Largest sub-glacial lake; isolated 15-25 million years; potential unique life; drilled to surface 2012"},
    {"name": "Mariana Trench Hadal Zone", "lat": 11.35, "lon": 142.2, "region": "Pacific Ocean", "area_km2": 300000, "status": "Extreme deep sea", "notes": "95% of hadal zone (6,000-11,000m) unmapped; unknown ecosystems; pressure 1,000+ atm"},
    {"name": "Namib Sand Sea Interior", "lat": -24.75, "lon": 15.3, "region": "Namibia", "area_km2": 34000, "status": "UNESCO / Extreme desert", "notes": "Oldest desert on Earth (55-80 million years); dune fields to 300m; largely unwalked by humans"},
    {"name": "Fiordland (New Zealand Interior)", "lat": -45.5, "lon": 167.0, "region": "New Zealand", "area_km2": 12500, "status": "Remote national park", "notes": "Dense rainforest and fiords; rarely visited interior; takahe rediscovered 1948 (thought extinct)"},
    {"name": "Saharan Ergs (Great Sand Seas)", "lat": 26.0, "lon": 5.0, "region": "Algeria / Libya", "area_km2": 600000, "status": "Extreme desert", "notes": "Grand Erg Oriental and Occidental; dune fields 100,000+ km2; satellite imagery only; Neolithic rock art hidden within"},
    {"name": "Mid-Atlantic Ridge (Unmapped)", "lat": 30.0, "lon": -42.0, "region": "Atlantic Ocean", "area_km2": 1000000, "status": "Deep ocean", "notes": "65,000 km undersea mountain chain; less than 5% mapped in detail; unknown vents and species"},
    {"name": "Mato Grosso Deep Amazon", "lat": -10.0, "lon": -55.0, "region": "Brazil", "area_km2": 500000, "status": "Dense jungle", "notes": "Percy Fawcett disappeared here 1925; still contains uncontacted groups; largely inaccessible"},
    {"name": "Simien Mountains (Remote Peaks)", "lat": 13.25, "lon": 38.4, "region": "Ethiopia", "area_km2": 4200, "status": "UNESCO / Remote", "notes": "Dramatic escarpments to 4,550m; endemic gelada baboons, Walia ibex; many areas botanically unsurveyed"},
]


# =====================================================================
# HELPER: Dark-themed Matplotlib figure
# =====================================================================
def _make_fig(nrows=1, ncols=1, figsize=(10, 5)):
    fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    fig.patch.set_facecolor(BG_COLOR)
    if isinstance(ax, plt.Axes):
        ax.set_facecolor(SURFACE_COLOR)
        ax.tick_params(colors=TEXT_COLOR)
        ax.xaxis.label.set_color(TEXT_COLOR)
        ax.yaxis.label.set_color(TEXT_COLOR)
        ax.title.set_color(TEXT_COLOR)
        for spine in ax.spines.values():
            spine.set_color(SECONDARY_TEXT)
    else:
        for a in ax.flat:
            a.set_facecolor(SURFACE_COLOR)
            a.tick_params(colors=TEXT_COLOR)
            a.xaxis.label.set_color(TEXT_COLOR)
            a.yaxis.label.set_color(TEXT_COLOR)
            a.title.set_color(TEXT_COLOR)
            for spine in a.spines.values():
                spine.set_color(SECONDARY_TEXT)
    return fig, ax


def _fig_to_buf(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _download_csv(df, filename, label="Download CSV"):
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv_bytes, file_name=filename,
                       mime="text/csv", key=f"dl_{filename}")


# =====================================================================
# CACHED DATA LOADERS
# =====================================================================
@st.cache_data(ttl=3600)
def _load_exploration_routes():
    return pd.DataFrame([
        {
            "Name": r["name"], "Year": r["year"],
            "Nationality": r["nationality"], "Notes": r["notes"],
        }
        for r in EXPLORATION_ROUTES
    ])


@st.cache_data(ttl=3600)
def _load_polar_expeditions():
    return pd.DataFrame([
        {
            "Name": p["name"], "Year": p["year"],
            "Nationality": p["nationality"], "Type": p["type"],
            "Result": p["result"], "Notes": p["notes"],
        }
        for p in POLAR_EXPEDITIONS
    ])


@st.cache_data(ttl=3600)
def _load_mountains():
    return pd.DataFrame(MOUNTAIN_FIRST_ASCENTS)


@st.cache_data(ttl=3600)
def _load_deep_sea():
    return pd.DataFrame(DEEP_SEA_DIVES)


@st.cache_data(ttl=3600)
def _load_launch_sites():
    return pd.DataFrame(SPACE_LAUNCH_SITES)


@st.cache_data(ttl=3600)
def _load_trade_routes():
    return pd.DataFrame([
        {
            "Name": r["name"], "Period": r["period"],
            "Goods": r["goods"], "Notes": r["notes"],
        }
        for r in ANCIENT_TRADE_ROUTES
    ])


@st.cache_data(ttl=3600)
def _load_first_contacts():
    return pd.DataFrame(FIRST_CONTACTS)


@st.cache_data(ttl=3600)
def _load_cartographic():
    return pd.DataFrame(CARTOGRAPHIC_MILESTONES)


@st.cache_data(ttl=3600)
def _load_scientific():
    return pd.DataFrame([
        {
            "Name": e["name"], "Year": e["year"],
            "Leader": e["leader"], "Field": e["field"],
            "Notes": e["notes"],
        }
        for e in SCIENTIFIC_EXPEDITIONS
    ])


@st.cache_data(ttl=3600)
def _load_unexplored():
    return pd.DataFrame(LAST_UNEXPLORED)


# =====================================================================
# MODE RENDERERS
# =====================================================================

def _render_exploration_routes():
    """1. Age of Exploration Routes."""
    df = _load_exploration_routes()

    # --- Stats ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Voyages", len(EXPLORATION_ROUTES))
    c2.metric("Earliest", min(r["year"] for r in EXPLORATION_ROUTES))
    c3.metric("Latest", max(r["year"] for r in EXPLORATION_ROUTES))
    nationalities = set(r["nationality"] for r in EXPLORATION_ROUTES)
    c4.metric("Nationalities", len(nationalities))

    # --- Map ---
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in EXPLORATION_ROUTES:
        folium.PolyLine(
            locations=r["route"], color=r["color"], weight=3, opacity=0.85,
            tooltip=html.escape(f"{r['name']} ({r['year']})"),
        ).add_to(m)
        folium.CircleMarker(
            location=r["route"][0], radius=5, color=r["color"],
            fill=True, fill_opacity=0.9,
            popup=folium.Popup(html.escape(f"{r['name']}<br>{r['notes']}"), max_width=280),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart ---
    fig, ax = _make_fig(figsize=(10, 5))
    names = [r["name"].split("(")[0].strip()[:20] for r in EXPLORATION_ROUTES]
    years = [r["year"] for r in EXPLORATION_ROUTES]
    colors = [r["color"] for r in EXPLORATION_ROUTES]
    ax.barh(names, years, color=colors, edgecolor="none")
    ax.set_xlabel("Year")
    ax.set_title("Age of Exploration - Voyage Start Years")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    # --- Dataframe & Download ---
    st.dataframe(df, width="stretch")
    _download_csv(df, "exploration_routes.csv")


def _render_polar_expeditions():
    """2. Polar Expeditions."""
    df = _load_polar_expeditions()

    arctic = [p for p in POLAR_EXPEDITIONS if p["type"] == "Arctic"]
    antarctic = [p for p in POLAR_EXPEDITIONS if p["type"] == "Antarctic"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Expeditions", len(POLAR_EXPEDITIONS))
    c2.metric("Arctic", len(arctic))
    c3.metric("Antarctic", len(antarctic))
    successes = sum(1 for p in POLAR_EXPEDITIONS if "success" in p["result"].lower() or "first" in p["result"].lower())
    c4.metric("Successes", successes)

    # --- Map ---
    m = folium.Map(location=[0, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for p in POLAR_EXPEDITIONS:
        folium.PolyLine(
            locations=p["route"], color=p["color"], weight=3, opacity=0.85,
            tooltip=html.escape(f"{p['name']} ({p['year']})"),
        ).add_to(m)
        folium.CircleMarker(
            location=p["route"][-1], radius=6, color=p["color"],
            fill=True, fill_opacity=0.9,
            popup=folium.Popup(html.escape(f"{p['name']}: {p['result']}"), max_width=280),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart ---
    fig, ax = _make_fig(figsize=(10, 5))
    names = [p["name"][:25] for p in POLAR_EXPEDITIONS]
    years = [p["year"] for p in POLAR_EXPEDITIONS]
    colors = [p["color"] for p in POLAR_EXPEDITIONS]
    ax.barh(names, years, color=colors, edgecolor="none")
    ax.set_xlabel("Year")
    ax.set_title("Polar Expeditions Timeline")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "polar_expeditions.csv")


def _render_mountain_first_ascents():
    """3. Mountain First Ascents."""
    df = _load_mountains()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peaks", len(MOUNTAIN_FIRST_ASCENTS))
    c2.metric("Highest (m)", max(p["elevation_m"] for p in MOUNTAIN_FIRST_ASCENTS))
    eight_thousanders = sum(1 for p in MOUNTAIN_FIRST_ASCENTS if p["elevation_m"] >= 8000)
    c3.metric("8,000m+ Peaks", eight_thousanders)
    countries = set()
    for p in MOUNTAIN_FIRST_ASCENTS:
        for c in p["country"].split("/"):
            countries.add(c.strip())
    c4.metric("Countries", len(countries))

    # --- Map ---
    m = folium.Map(location=[30, 80], zoom_start=3, tiles="CartoDB dark_matter")
    for p in MOUNTAIN_FIRST_ASCENTS:
        color = "#ef4444" if p["elevation_m"] >= 8000 else ("#f59e0b" if p["elevation_m"] >= 6000 else "#06b6d4")
        folium.CircleMarker(
            location=[p["lat"], p["lon"]], radius=max(4, p["elevation_m"] / 1200),
            color=color, fill=True, fill_opacity=0.8,
            tooltip=html.escape(f"{p['name']} ({p['elevation_m']}m)"),
            popup=folium.Popup(
                html.escape(f"{p['name']}<br>{p['elevation_m']}m<br>First ascent: {p['first_ascent']}<br>{p['climbers']}"),
                max_width=300,
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: Top 15 by elevation ---
    sorted_peaks = sorted(MOUNTAIN_FIRST_ASCENTS, key=lambda x: x["elevation_m"], reverse=True)[:15]
    fig, ax = _make_fig(figsize=(10, 6))
    names = [p["name"][:18] for p in sorted_peaks]
    elevations = [p["elevation_m"] for p in sorted_peaks]
    bar_colors = ["#ef4444" if e >= 8000 else ("#f59e0b" if e >= 6000 else ACCENT_COLOR) for e in elevations]
    ax.barh(names, elevations, color=bar_colors, edgecolor="none")
    ax.set_xlabel("Elevation (m)")
    ax.set_title("Highest Peaks - First Ascent Records")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "mountain_first_ascents.csv")


def _render_deep_sea():
    """4. Deep Sea Exploration."""
    df = _load_deep_sea()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dive Sites", len(DEEP_SEA_DIVES))
    c2.metric("Deepest (m)", max(d["depth_m"] for d in DEEP_SEA_DIVES))
    c3.metric("Earliest", min(d["year"] for d in DEEP_SEA_DIVES))
    c4.metric("Latest", max(d["year"] for d in DEEP_SEA_DIVES))

    # --- Map ---
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for d in DEEP_SEA_DIVES:
        radius = max(4, min(12, d["depth_m"] / 1200))
        color = "#ef4444" if d["depth_m"] >= 8000 else ("#f59e0b" if d["depth_m"] >= 3000 else "#06b6d4")
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=radius,
            color=color, fill=True, fill_opacity=0.8,
            tooltip=html.escape(f"{d['name']} ({d['depth_m']}m, {d['year']})"),
            popup=folium.Popup(
                html.escape(f"{d['name']}<br>Depth: {d['depth_m']}m<br>Year: {d['year']}<br>Vessel: {d['vessel']}<br>{d['notes']}"),
                max_width=320,
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: depth ---
    sorted_dives = sorted(DEEP_SEA_DIVES, key=lambda x: x["depth_m"], reverse=True)[:15]
    fig, ax = _make_fig(figsize=(10, 6))
    names = [d["name"][:30] for d in sorted_dives]
    depths = [d["depth_m"] for d in sorted_dives]
    bar_colors = ["#ef4444" if dp >= 8000 else ("#f59e0b" if dp >= 3000 else ACCENT_COLOR) for dp in depths]
    ax.barh(names, depths, color=bar_colors, edgecolor="none")
    ax.set_xlabel("Depth (m)")
    ax.set_title("Deepest Exploration Dives")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "deep_sea_exploration.csv")


def _render_space_launch_sites():
    """5. Space Launch Sites."""
    df = _load_launch_sites()

    active = sum(1 for s in SPACE_LAUNCH_SITES if s["status"] == "Active")
    countries = set(s["country"] for s in SPACE_LAUNCH_SITES)
    agencies = set(s["agency"] for s in SPACE_LAUNCH_SITES)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Launch Sites", len(SPACE_LAUNCH_SITES))
    c2.metric("Active", active)
    c3.metric("Countries", len(countries))
    c4.metric("Agencies", len(agencies))

    # --- Map ---
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for s in SPACE_LAUNCH_SITES:
        color = ACCENT_COLOR if s["status"] == "Active" else "#6b7280"
        icon_color = "lightblue" if s["status"] == "Active" else "gray"
        folium.Marker(
            location=[s["lat"], s["lon"]],
            icon=folium.Icon(color="darkblue" if s["status"] == "Active" else "gray", icon="rocket", prefix="fa"),
            tooltip=html.escape(f"{s['name']} ({s['agency']})"),
            popup=folium.Popup(
                html.escape(f"{s['name']}<br>Agency: {s['agency']}<br>Country: {s['country']}<br>"
                            f"First launch: {s['first_launch']}<br>{s['notable']}"),
                max_width=300,
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: launches by country ---
    country_counts = {}
    for s in SPACE_LAUNCH_SITES:
        c_name = s["country"]
        country_counts[c_name] = country_counts.get(c_name, 0) + 1
    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    fig, ax = _make_fig(figsize=(10, 5))
    c_names = [c[0][:20] for c in sorted_countries]
    c_vals = [c[1] for c in sorted_countries]
    ax.barh(c_names, c_vals, color=ACCENT_COLOR, edgecolor="none")
    ax.set_xlabel("Number of Launch Sites")
    ax.set_title("Space Launch Sites by Country")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "space_launch_sites.csv")


def _render_ancient_trade_routes():
    """6. Ancient Trade Routes."""
    df = _load_trade_routes()

    c1, c2, c3 = st.columns(3)
    c1.metric("Trade Routes", len(ANCIENT_TRADE_ROUTES))
    all_goods = set()
    for r in ANCIENT_TRADE_ROUTES:
        for g in r["goods"].split(","):
            all_goods.add(g.strip())
    c2.metric("Traded Goods", len(all_goods))
    c3.metric("Spanning", "3000 BC - 1900 AD")

    # --- Map ---
    m = folium.Map(location=[30, 50], zoom_start=3, tiles="CartoDB dark_matter")
    for r in ANCIENT_TRADE_ROUTES:
        folium.PolyLine(
            locations=r["route"], color=r["color"], weight=3, opacity=0.85,
            tooltip=html.escape(f"{r['name']} ({r['period']})"),
        ).add_to(m)
        mid_idx = len(r["route"]) // 2
        folium.CircleMarker(
            location=r["route"][mid_idx], radius=5, color=r["color"],
            fill=True, fill_opacity=0.9,
            popup=folium.Popup(html.escape(f"{r['name']}<br>Goods: {r['goods']}<br>{r['notes']}"), max_width=320),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: goods frequency ---
    goods_count = {}
    for r in ANCIENT_TRADE_ROUTES:
        for g in r["goods"].split(","):
            g = g.strip()
            goods_count[g] = goods_count.get(g, 0) + 1
    sorted_goods = sorted(goods_count.items(), key=lambda x: x[1], reverse=True)[:15]
    fig, ax = _make_fig(figsize=(10, 5))
    g_names = [g[0] for g in sorted_goods]
    g_vals = [g[1] for g in sorted_goods]
    ax.barh(g_names, g_vals, color=ACCENT_COLOR, edgecolor="none")
    ax.set_xlabel("Routes Trading This Good")
    ax.set_title("Most Commonly Traded Goods Across Ancient Routes")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "ancient_trade_routes.csv")


def _render_first_contacts():
    """7. First Contacts & Discoveries."""
    df = _load_first_contacts()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Discoveries", len(FIRST_CONTACTS))
    c2.metric("Earliest", min(d["year"] for d in FIRST_CONTACTS))
    c3.metric("Latest", max(d["year"] for d in FIRST_CONTACTS))
    nats = set(d["nationality"] for d in FIRST_CONTACTS)
    c4.metric("Nationalities", len(nats))

    # --- Map ---
    m = folium.Map(location=[10, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for d in FIRST_CONTACTS:
        folium.Marker(
            location=[d["lat"], d["lon"]],
            icon=folium.Icon(color="orange", icon="flag", prefix="fa"),
            tooltip=html.escape(f"{d['name']} ({d['year']})"),
            popup=folium.Popup(
                html.escape(f"{d['name']}<br>Year: {d['year']}<br>Explorer: {d['explorer']}<br>{d['notes']}"),
                max_width=300,
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: timeline ---
    sorted_fc = sorted(FIRST_CONTACTS, key=lambda x: x["year"])
    fig, ax = _make_fig(figsize=(10, 6))
    names = [d["name"][:25] for d in sorted_fc]
    years = [d["year"] for d in sorted_fc]
    colors_list = [ACCENT_COLOR if y < 1500 else ("#f59e0b" if y < 1700 else "#ef4444") for y in years]
    ax.barh(names, years, color=colors_list, edgecolor="none")
    ax.set_xlabel("Year of Discovery / Contact")
    ax.set_title("First Contacts & Discoveries - Chronological")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "first_contacts.csv")


def _render_cartographic_milestones():
    """8. Cartographic Milestones."""
    df = _load_cartographic()

    c1, c2, c3 = st.columns(3)
    c1.metric("Milestones", len(CARTOGRAPHIC_MILESTONES))
    c2.metric("Time Span", "240 BC - 1995 AD")
    locations = set(m_item["location"].split(",")[-1].strip() for m_item in CARTOGRAPHIC_MILESTONES)
    c3.metric("Countries", len(locations))

    # --- Map ---
    m = folium.Map(location=[40, 10], zoom_start=3, tiles="CartoDB dark_matter")
    for item in CARTOGRAPHIC_MILESTONES:
        folium.Marker(
            location=[item["lat"], item["lon"]],
            icon=folium.Icon(color="cadetblue", icon="map", prefix="fa"),
            tooltip=html.escape(f"{item['person']} ({item['year']})"),
            popup=folium.Popup(
                html.escape(f"{item['name']}<br>Year: {item['year']}<br>Person: {item['person']}<br>"
                            f"Location: {item['location']}<br>{item['contribution']}"),
                max_width=340,
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: timeline by index ---
    fig, ax = _make_fig(figsize=(10, 6))
    names = [f"{item['person'][:20]} ({item['year']})" for item in CARTOGRAPHIC_MILESTONES]
    indices = list(range(len(names)))
    ax.barh(names, indices, color=ACCENT_COLOR, edgecolor="none")
    ax.set_xlabel("Chronological Order")
    ax.set_title("Cartographic Milestones")
    ax.invert_yaxis()
    ax.set_xticks([])
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "cartographic_milestones.csv")


def _render_scientific_expeditions():
    """9. Scientific Expeditions."""
    df = _load_scientific()

    fields = set(e["field"] for e in SCIENTIFIC_EXPEDITIONS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Expeditions", len(SCIENTIFIC_EXPEDITIONS))
    c2.metric("Scientific Fields", len(fields))
    c3.metric("Time Span", "1733 - 1970")

    # --- Map ---
    m = folium.Map(location=[10, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for e in SCIENTIFIC_EXPEDITIONS:
        folium.PolyLine(
            locations=e["route"], color=e["color"], weight=3, opacity=0.85,
            tooltip=html.escape(f"{e['name']} ({e['year']})"),
        ).add_to(m)
        folium.CircleMarker(
            location=e["route"][0], radius=5, color=e["color"],
            fill=True, fill_opacity=0.9,
            popup=folium.Popup(
                html.escape(f"{e['name']}<br>Leader: {e['leader']}<br>Field: {e['field']}<br>{e['notes']}"),
                max_width=320,
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: by field ---
    field_counts = {}
    for e in SCIENTIFIC_EXPEDITIONS:
        for f in e["field"].split("/"):
            f = f.strip()
            field_counts[f] = field_counts.get(f, 0) + 1
    sorted_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)
    fig, ax = _make_fig(figsize=(10, 5))
    f_names = [f[0] for f in sorted_fields]
    f_vals = [f[1] for f in sorted_fields]
    ax.barh(f_names, f_vals, color=ACCENT_COLOR, edgecolor="none")
    ax.set_xlabel("Number of Expeditions")
    ax.set_title("Scientific Expeditions by Field")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "scientific_expeditions.csv")


def _render_last_unexplored():
    """10. Last Unexplored Places."""
    df = _load_unexplored()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Places", len(LAST_UNEXPLORED))
    total_area = sum(p["area_km2"] for p in LAST_UNEXPLORED)
    c2.metric("Total Area (km2)", f"{total_area:,.0f}")
    statuses = set(p["status"] for p in LAST_UNEXPLORED)
    c3.metric("Status Types", len(statuses))
    regions = set(p["region"].split(",")[-1].strip() for p in LAST_UNEXPLORED)
    c4.metric("Regions", len(regions))

    # --- Map ---
    m = folium.Map(location=[10, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for p in LAST_UNEXPLORED:
        radius = max(5, min(15, (p["area_km2"] ** 0.3) * 1.5)) if p["area_km2"] > 0 else 6
        folium.CircleMarker(
            location=[p["lat"], p["lon"]], radius=radius,
            color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.6,
            tooltip=html.escape(f"{p['name']} - {p['status']}"),
            popup=folium.Popup(
                html.escape(f"{p['name']}<br>Region: {p['region']}<br>Area: {p['area_km2']} km2<br>"
                            f"Status: {p['status']}<br>{p['notes']}"),
                max_width=340,
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart: area ---
    sorted_places = sorted(LAST_UNEXPLORED, key=lambda x: x["area_km2"], reverse=True)
    sorted_places = [p for p in sorted_places if p["area_km2"] > 0][:12]
    fig, ax = _make_fig(figsize=(10, 6))
    names = [p["name"][:25] for p in sorted_places]
    areas = [p["area_km2"] for p in sorted_places]
    ax.barh(names, areas, color="#ef4444", edgecolor="none")
    ax.set_xlabel("Area (km2)")
    ax.set_title("Last Unexplored Places by Area")
    ax.invert_yaxis()
    st.image(_fig_to_buf(fig), use_container_width=True)

    st.dataframe(df, width="stretch")
    _download_csv(df, "last_unexplored_places.csv")


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
MODE_DISPATCH = {
    MAP_MODES[0]: _render_exploration_routes,
    MAP_MODES[1]: _render_polar_expeditions,
    MAP_MODES[2]: _render_mountain_first_ascents,
    MAP_MODES[3]: _render_deep_sea,
    MAP_MODES[4]: _render_space_launch_sites,
    MAP_MODES[5]: _render_ancient_trade_routes,
    MAP_MODES[6]: _render_first_contacts,
    MAP_MODES[7]: _render_cartographic_milestones,
    MAP_MODES[8]: _render_scientific_expeditions,
    MAP_MODES[9]: _render_last_unexplored,
}


def render_exploration_maps_tab():
    """Render the Exploration & Discovery Maps tab."""
    st.markdown(
        '<div class="tab-header amber">'
        "<h4>\U0001f9ed Exploration & Discovery Maps</h4>"
        "<p>Great expeditions, first contacts, polar exploration, deep sea & space launch sites</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Select exploration theme",
        MAP_MODES,
        horizontal=True,
        key="exploration_maps_mode",
    )

    st.markdown("---")
    MODE_DISPATCH[mode]()
