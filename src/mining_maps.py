# -*- coding: utf-8 -*-
"""
Mining & Natural Resources Maps module for TerraScout AI.
Curated datasets of major mines, mineral deposits, oil fields,
and resource extraction sites worldwide. 10 interactive map modes.
All data sources are free and require no API keys.
"""

import io
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

# ═══════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════
RESOURCE_COLORS = {
    "gold": "#ffd700",
    "copper": "#b87333",
    "iron": "#a0522d",
    "coal": "#555555",
    "diamond": "#b9f2ff",
    "uranium": "#39ff14",
    "lithium": "#00bfff",
    "oil": "#1a1a2e",
    "gas": "#ff6347",
    "rare_earth": "#ff69b4",
    "silver": "#c0c0c0",
    "platinum": "#e5e4e2",
    "nickel": "#727472",
    "zinc": "#bac4c8",
    "tin": "#d3d3d3",
    "bauxite": "#cd853f",
    "manganese": "#8b008b",
    "cobalt": "#0047ab",
    "chromium": "#4682b4",
    "phosphate": "#98fb98",
    "deep_sea": "#1e90ff",
    "historical": "#daa520",
}

# ═══════════════════════════════════════════════════════════════
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════
MAP_MODES = [
    "World's Largest Mines",
    "Gold Deposits",
    "Rare Earth Elements",
    "Oil & Gas Fields",
    "Diamond Mines",
    "Coal Regions",
    "Uranium & Nuclear Fuel",
    "Lithium Triangle",
    "Deep Sea Mining",
    "Historical Mining",
]

MODE_DESCRIPTIONS = {
    "World's Largest Mines": (
        "The 50 largest mines on Earth ranked by annual production volume. "
        "These mega-operations extract copper, gold, iron, coal, and other minerals "
        "on an enormous scale, some visible from space."
    ),
    "Gold Deposits": (
        "Major gold mining regions and deposits across six continents. "
        "From the Witwatersrand Basin of South Africa to the Carlin Trend in Nevada, "
        "these sites have produced the majority of the world's gold supply."
    ),
    "Rare Earth Elements": (
        "Rare earth element (REE) deposits critical for modern technology. "
        "China dominates production with ~60% of global output, but deposits exist "
        "in Australia, the US, Brazil, India, and Greenland."
    ),
    "Oil & Gas Fields": (
        "The world's largest oil and gas fields, from Saudi Arabia's Ghawar "
        "to the Permian Basin. These fields collectively hold trillions of barrels "
        "of proven reserves powering the global energy system."
    ),
    "Diamond Mines": (
        "Major diamond mining operations from Botswana's Jwaneng to Russia's "
        "Yakutia. Includes kimberlite pipes, alluvial deposits, and both "
        "gem-quality and industrial diamond sources."
    ),
    "Coal Regions": (
        "Global coal basins showing the ongoing transition from coal in Europe "
        "and North America alongside continued growth in Asia. Includes both "
        "thermal and metallurgical coal deposits."
    ),
    "Uranium & Nuclear Fuel": (
        "Uranium mining sites and processing facilities that supply fuel for "
        "the world's 440+ nuclear reactors. Kazakhstan, Canada, and Australia "
        "are the top three producing nations."
    ),
    "Lithium Triangle": (
        "The lithium supply chain powering the EV revolution. The 'Lithium Triangle' "
        "of Bolivia, Chile, and Argentina holds over half the world's known reserves "
        "in vast salt flats (salares)."
    ),
    "Deep Sea Mining": (
        "Proposed and active deep-sea mining zones targeting manganese nodules, "
        "polymetallic sulfides, and cobalt-rich crusts. The Clarion-Clipperton Zone "
        "in the Pacific is the primary exploration frontier."
    ),
    "Historical Mining": (
        "Ancient and historically significant mines spanning 5,000+ years. "
        "From the silver mines of Laurion that funded Athenian democracy to "
        "Potosi's Cerro Rico that fueled the Spanish Empire."
    ),
}

# ═══════════════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════════════

WORLDS_LARGEST_MINES = [
    {"name": "Bingham Canyon Mine", "country": "USA", "resource": "Copper/Gold/Silver", "lat": 40.5217, "lon": -112.1510, "production_mt": 190.0, "type": "Open-pit", "note": "Largest man-made excavation on Earth, 1.2 km deep"},
    {"name": "Grasberg Mine", "country": "Indonesia", "resource": "Gold/Copper", "lat": -4.0530, "lon": 137.1164, "production_mt": 175.0, "type": "Open-pit/Underground", "note": "Largest gold mine and second largest copper mine"},
    {"name": "Muruntau Mine", "country": "Uzbekistan", "resource": "Gold", "lat": 41.5500, "lon": 64.5667, "production_mt": 66.0, "type": "Open-pit", "note": "Largest open-pit gold mine in the world"},
    {"name": "Escondida Mine", "country": "Chile", "resource": "Copper", "lat": -24.2667, "lon": -69.0667, "production_mt": 206.0, "type": "Open-pit", "note": "World's largest copper mine by output"},
    {"name": "Chuquicamata Mine", "country": "Chile", "resource": "Copper", "lat": -22.2890, "lon": -68.9012, "production_mt": 150.0, "type": "Open-pit/Underground", "note": "Largest open-pit copper mine by volume"},
    {"name": "Mirny Mine", "country": "Russia", "resource": "Diamond", "lat": 62.5167, "lon": 113.9833, "production_mt": 10.0, "type": "Open-pit", "note": "525m deep, second largest excavated hole"},
    {"name": "Carajas Mine", "country": "Brazil", "resource": "Iron Ore", "lat": -6.0750, "lon": -50.1660, "production_mt": 312.0, "type": "Open-pit", "note": "Largest iron ore mine, 18 billion tonnes reserves"},
    {"name": "Olympic Dam", "country": "Australia", "resource": "Copper/Uranium/Gold", "lat": -30.4500, "lon": 136.8833, "production_mt": 180.0, "type": "Underground", "note": "Largest known uranium deposit"},
    {"name": "Morenci Mine", "country": "USA", "resource": "Copper", "lat": 33.0950, "lon": -109.3580, "production_mt": 190.0, "type": "Open-pit", "note": "Largest copper mine in North America"},
    {"name": "Collahuasi Mine", "country": "Chile", "resource": "Copper", "lat": -20.9833, "lon": -68.7167, "production_mt": 140.0, "type": "Open-pit", "note": "One of the world's largest copper reserves"},
    {"name": "El Teniente Mine", "country": "Chile", "resource": "Copper", "lat": -34.0900, "lon": -70.3900, "production_mt": 137.0, "type": "Underground", "note": "World's largest underground copper mine"},
    {"name": "Super Pit (Fimiston)", "country": "Australia", "resource": "Gold", "lat": -30.7750, "lon": 121.5030, "production_mt": 28.0, "type": "Open-pit", "note": "Australia's largest open-pit gold mine"},
    {"name": "Norilsk-Talnakh", "country": "Russia", "resource": "Nickel/Palladium/Copper", "lat": 69.3535, "lon": 88.2027, "production_mt": 240.0, "type": "Underground", "note": "Largest nickel-palladium deposits in the world"},
    {"name": "Cerro Verde Mine", "country": "Peru", "resource": "Copper/Molybdenum", "lat": -16.5380, "lon": -71.6010, "production_mt": 170.0, "type": "Open-pit", "note": "Major copper-molybdenum producer"},
    {"name": "Antamina Mine", "country": "Peru", "resource": "Copper/Zinc", "lat": -9.5340, "lon": -77.0530, "production_mt": 160.0, "type": "Open-pit", "note": "One of the world's largest copper-zinc mines"},
    {"name": "Los Bronces Mine", "country": "Chile", "resource": "Copper", "lat": -33.1500, "lon": -70.2833, "production_mt": 125.0, "type": "Open-pit", "note": "Major Chilean copper operation"},
    {"name": "Kalgoorlie Super Pit", "country": "Australia", "resource": "Gold", "lat": -30.7769, "lon": 121.5031, "production_mt": 25.0, "type": "Open-pit", "note": "Iconic gold mine in Western Australia"},
    {"name": "Mount Whaleback", "country": "Australia", "resource": "Iron Ore", "lat": -23.3670, "lon": 119.6770, "production_mt": 280.0, "type": "Open-pit", "note": "Major iron ore mine in Pilbara region"},
    {"name": "Hamersley Range Mines", "country": "Australia", "resource": "Iron Ore", "lat": -22.6000, "lon": 118.2000, "production_mt": 350.0, "type": "Open-pit", "note": "Multiple mega iron ore operations"},
    {"name": "Mponeng Mine", "country": "South Africa", "resource": "Gold", "lat": -26.4200, "lon": 27.4200, "production_mt": 5.3, "type": "Underground", "note": "Deepest mine on Earth, 4 km below surface"},
    {"name": "Jwaneng Mine", "country": "Botswana", "resource": "Diamond", "lat": -24.5230, "lon": 24.6570, "production_mt": 12.5, "type": "Open-pit", "note": "Richest diamond mine by value in the world"},
    {"name": "Udachny Mine", "country": "Russia", "resource": "Diamond", "lat": 66.4310, "lon": 112.3540, "production_mt": 11.0, "type": "Open-pit/Underground", "note": "Major Yakutian diamond mine"},
    {"name": "Palabora Mine", "country": "South Africa", "resource": "Copper/Phosphate", "lat": -23.9830, "lon": 31.1170, "production_mt": 75.0, "type": "Underground", "note": "Largest open-pit mine in Africa (now underground)"},
    {"name": "Kiruna Mine", "country": "Sweden", "resource": "Iron Ore", "lat": 67.8530, "lon": 20.2170, "production_mt": 85.0, "type": "Underground", "note": "Largest underground iron ore mine in the world"},
    {"name": "Vorkuta Coal Basin", "country": "Russia", "resource": "Coal", "lat": 67.4960, "lon": 64.0600, "production_mt": 60.0, "type": "Underground", "note": "Major Arctic coal mining region"},
    {"name": "Hambach Mine", "country": "Germany", "resource": "Lignite", "lat": 50.9100, "lon": 6.5100, "production_mt": 40.0, "type": "Open-pit", "note": "Deepest open-pit mine in Europe (370m)"},
    {"name": "North Antelope Rochelle", "country": "USA", "resource": "Coal", "lat": 43.6700, "lon": -105.3200, "production_mt": 92.0, "type": "Surface", "note": "World's largest coal mine by reserves"},
    {"name": "Rossing Mine", "country": "Namibia", "resource": "Uranium", "lat": -22.4830, "lon": 15.1830, "production_mt": 4.6, "type": "Open-pit", "note": "Longest running open-pit uranium mine"},
    {"name": "Oyu Tolgoi", "country": "Mongolia", "resource": "Copper/Gold", "lat": 43.0100, "lon": 106.8500, "production_mt": 120.0, "type": "Open-pit/Underground", "note": "One of the largest known copper-gold deposits"},
    {"name": "Venetia Mine", "country": "South Africa", "resource": "Diamond", "lat": -22.4500, "lon": 29.3170, "production_mt": 8.2, "type": "Underground", "note": "De Beers' flagship South African mine"},
    {"name": "Cobre Panama", "country": "Panama", "resource": "Copper", "lat": 8.8330, "lon": -80.6170, "production_mt": 100.0, "type": "Open-pit", "note": "Central America's largest copper mine"},
    {"name": "Las Bambas Mine", "country": "Peru", "resource": "Copper", "lat": -14.0667, "lon": -72.3333, "production_mt": 120.0, "type": "Open-pit", "note": "Major copper mine in Peruvian Andes"},
    {"name": "Kennecott (Bingham Canyon)", "country": "USA", "resource": "Copper", "lat": 40.5230, "lon": -112.1490, "production_mt": 190.0, "type": "Open-pit", "note": "Operating since 1906, iconic open-pit mine"},
    {"name": "Pilbara Iron Ore Complex", "country": "Australia", "resource": "Iron Ore", "lat": -21.5000, "lon": 118.0000, "production_mt": 400.0, "type": "Open-pit", "note": "Multiple mines, BHP and Rio Tinto"},
    {"name": "Malmberget Mine", "country": "Sweden", "resource": "Iron Ore", "lat": 67.1770, "lon": 20.6550, "production_mt": 70.0, "type": "Underground", "note": "Historic Swedish iron ore mine"},
    {"name": "Mount Keith", "country": "Australia", "resource": "Nickel", "lat": -27.2330, "lon": 120.5500, "production_mt": 55.0, "type": "Open-pit", "note": "Largest nickel mine in Australia"},
    {"name": "Cerrejon Mine", "country": "Colombia", "resource": "Coal", "lat": 11.1170, "lon": -72.6170, "production_mt": 27.0, "type": "Open-pit", "note": "One of the largest open-pit coal mines globally"},
    {"name": "Penasquito Mine", "country": "Mexico", "resource": "Gold/Silver/Zinc", "lat": 24.0500, "lon": -101.6000, "production_mt": 42.0, "type": "Open-pit", "note": "Mexico's largest gold mine"},
    {"name": "Kibali Gold Mine", "country": "DRC", "resource": "Gold", "lat": 3.1330, "lon": 30.0670, "production_mt": 12.0, "type": "Open-pit/Underground", "note": "Africa's largest gold mine by production"},
    {"name": "Vaal River Operations", "country": "South Africa", "resource": "Gold", "lat": -27.0000, "lon": 26.7500, "production_mt": 8.0, "type": "Underground", "note": "Part of the Witwatersrand gold field"},
    {"name": "Kambalda Nickel Mines", "country": "Australia", "resource": "Nickel", "lat": -31.2000, "lon": 121.6500, "production_mt": 35.0, "type": "Underground", "note": "Historic nickel mining district"},
    {"name": "Spence Mine", "country": "Chile", "resource": "Copper", "lat": -22.8500, "lon": -69.3000, "production_mt": 80.0, "type": "Open-pit", "note": "BHP copper mine in Atacama Desert"},
    {"name": "Geita Gold Mine", "country": "Tanzania", "resource": "Gold", "lat": -2.8330, "lon": 32.1670, "production_mt": 10.0, "type": "Open-pit", "note": "East Africa's largest gold producer"},
    {"name": "Tarkwa Gold Mine", "country": "Ghana", "resource": "Gold", "lat": 5.3000, "lon": -2.0000, "production_mt": 9.0, "type": "Open-pit", "note": "Historic Gold Coast mining district"},
    {"name": "Konkola Mine", "country": "Zambia", "resource": "Copper", "lat": -12.3830, "lon": 27.8170, "production_mt": 65.0, "type": "Underground", "note": "Zambian Copperbelt flagship mine"},
    {"name": "Kansanshi Mine", "country": "Zambia", "resource": "Copper/Gold", "lat": -12.1000, "lon": 26.4170, "production_mt": 85.0, "type": "Open-pit", "note": "Africa's largest copper mine"},
    {"name": "Salobo Mine", "country": "Brazil", "resource": "Copper/Gold", "lat": -5.7830, "lon": -50.5330, "production_mt": 75.0, "type": "Open-pit", "note": "Major Vale copper-gold operation"},
    {"name": "Pueblo Viejo Mine", "country": "Dominican Republic", "resource": "Gold/Silver", "lat": 18.9500, "lon": -70.1830, "production_mt": 14.0, "type": "Open-pit", "note": "One of the largest gold mines in the Americas"},
    {"name": "Karowe Mine", "country": "Botswana", "resource": "Diamond", "lat": -21.4170, "lon": 25.5830, "production_mt": 3.0, "type": "Open-pit", "note": "Source of world's third-largest gem diamond (1,758 ct)"},
    {"name": "Lihir Gold Mine", "country": "Papua New Guinea", "resource": "Gold", "lat": -3.1230, "lon": 152.6300, "production_mt": 15.0, "type": "Open-pit", "note": "Located inside an active volcanic caldera"},
]

GOLD_DEPOSITS = [
    {"name": "Witwatersrand Basin", "country": "South Africa", "lat": -26.2000, "lon": 27.9000, "production_kg": 50000, "note": "Produced ~40% of all gold ever mined"},
    {"name": "Carlin Trend", "country": "USA (Nevada)", "lat": 40.7200, "lon": -116.0700, "production_kg": 5000, "note": "Largest gold-producing area in the Western Hemisphere"},
    {"name": "Kalgoorlie-Boulder", "country": "Australia", "lat": -30.7490, "lon": 121.4660, "production_kg": 2200, "note": "Rich Golden Mile, over 130 years of production"},
    {"name": "Homestake Mine (Black Hills)", "country": "USA (S. Dakota)", "lat": 44.3500, "lon": -103.7500, "production_kg": 1100, "note": "Deepest mine in North America, now closed"},
    {"name": "Siberian Deposits (Bodaibo)", "country": "Russia", "lat": 57.8500, "lon": 114.2000, "production_kg": 3500, "note": "Lena Goldfields, historic placer and lode deposits"},
    {"name": "Timmins-Porcupine Camp", "country": "Canada", "lat": 48.4667, "lon": -81.3333, "production_kg": 2000, "note": "One of Canada's richest gold camps"},
    {"name": "Kirkland Lake", "country": "Canada", "lat": 48.1500, "lon": -80.0333, "production_kg": 1500, "note": "High-grade gold deposits in Ontario"},
    {"name": "Yanacocha Mine", "country": "Peru", "lat": -6.9830, "lon": -78.5330, "production_kg": 1800, "note": "Largest gold mine in South America"},
    {"name": "Grasberg/Ertsberg", "country": "Indonesia", "lat": -4.0530, "lon": 137.1164, "production_kg": 2500, "note": "World's largest gold reserve, also copper"},
    {"name": "Ashanti Goldfields", "country": "Ghana", "lat": 6.3330, "lon": -1.7830, "production_kg": 1400, "note": "Obuasi Mine, mined since precolonial era"},
    {"name": "Rand (Johannesburg)", "country": "South Africa", "lat": -26.2041, "lon": 28.0473, "production_kg": 48000, "note": "City of Gold, built on the Witwatersrand reef"},
    {"name": "Lihir Island", "country": "Papua New Guinea", "lat": -3.1230, "lon": 152.6300, "production_kg": 900, "note": "Volcanic gold deposit, unique geology"},
    {"name": "Sukhoi Log", "country": "Russia", "lat": 58.0000, "lon": 114.5000, "production_kg": 4000, "note": "One of world's largest undeveloped gold deposits"},
    {"name": "Goldstrike Mine", "country": "USA (Nevada)", "lat": 41.0530, "lon": -116.3670, "production_kg": 1200, "note": "Major Barrick Gold mine on Carlin Trend"},
    {"name": "Pueblo Viejo", "country": "Dominican Republic", "lat": 18.9500, "lon": -70.1830, "production_kg": 800, "note": "Caribbean's largest gold operation"},
    {"name": "Boddington Mine", "country": "Australia", "lat": -32.7470, "lon": 116.3780, "production_kg": 700, "note": "Largest gold mine in Australia"},
    {"name": "Mponeng Deep Mine", "country": "South Africa", "lat": -26.4200, "lon": 27.4200, "production_kg": 500, "note": "Operates 4 km below surface, world's deepest mine"},
    {"name": "Kibali", "country": "DRC", "lat": 3.1330, "lon": 30.0670, "production_kg": 750, "note": "Africa's largest gold mine, in remote NE Congo"},
    {"name": "Olimpiada Mine", "country": "Russia", "lat": 60.0000, "lon": 93.0000, "production_kg": 1300, "note": "Major Polyus mine in Krasnoyarsk region"},
    {"name": "Geita Mine", "country": "Tanzania", "lat": -2.8330, "lon": 32.1670, "production_kg": 550, "note": "Lake Victoria Greenstone Belt"},
    {"name": "Cadia-Ridgeway", "country": "Australia", "lat": -33.4670, "lon": 148.9830, "production_kg": 800, "note": "Largest underground mine in Australia"},
    {"name": "Red Lake Mine", "country": "Canada", "lat": 51.0667, "lon": -93.8333, "production_kg": 600, "note": "Extremely high-grade gold deposit, Ontario"},
    {"name": "Paracatu Mine", "country": "Brazil", "lat": -17.2170, "lon": -46.8670, "production_kg": 650, "note": "Kinross Gold, one of the largest in the Americas"},
    {"name": "Loulo-Gounkoto", "country": "Mali", "lat": 12.8500, "lon": -11.6000, "production_kg": 700, "note": "Barrick Gold, West African gold belt"},
    {"name": "Obuasi Mine", "country": "Ghana", "lat": 6.2020, "lon": -1.6780, "production_kg": 550, "note": "AngloGold Ashanti flagship, centennial mine"},
]

RARE_EARTH_DEPOSITS = [
    {"name": "Bayan Obo", "country": "China", "lat": 41.7833, "lon": 109.9667, "element": "Mixed REE", "reserves_mt": 48.0, "note": "World's largest REE deposit, ~70% of China's output"},
    {"name": "Mount Weld", "country": "Australia", "lat": -28.7300, "lon": 122.5500, "element": "Mixed REE", "reserves_mt": 3.4, "note": "Highest grade REE deposit globally"},
    {"name": "Mountain Pass", "country": "USA", "lat": 35.4750, "lon": -115.5350, "element": "Cerium/Lanthanum", "reserves_mt": 2.1, "note": "Only US REE mine, reopened for supply chain security"},
    {"name": "Ilimaussaq Complex", "country": "Greenland", "lat": 61.0000, "lon": -45.9500, "element": "Mixed REE", "reserves_mt": 6.5, "note": "Kvanefjeld project, controversial environmental issues"},
    {"name": "Nolans Bore", "country": "Australia", "lat": -22.5830, "lon": 133.2500, "element": "Neodymium/Praseodymium", "reserves_mt": 1.8, "note": "Arafura Resources, advanced development"},
    {"name": "Serra Verde", "country": "Brazil", "lat": -14.0000, "lon": -47.0000, "element": "Mixed REE (ionic clay)", "reserves_mt": 2.0, "note": "Ionic clay deposits, lower extraction cost"},
    {"name": "Manavalakurichi", "country": "India", "lat": 8.1470, "lon": 77.3030, "element": "Monazite (REE)", "reserves_mt": 3.1, "note": "Beach sand monazite deposits, state-controlled"},
    {"name": "Lovozero Massif", "country": "Russia", "lat": 67.9000, "lon": 34.7000, "element": "Mixed REE", "reserves_mt": 5.0, "note": "Loparite ore, Kola Peninsula"},
    {"name": "Steenkampskraal", "country": "South Africa", "lat": -31.2830, "lon": 18.5500, "element": "Thorium/REE", "reserves_mt": 0.6, "note": "Historic thorium mine, now REE focus"},
    {"name": "Strange Lake", "country": "Canada", "lat": 56.3170, "lon": -64.1670, "element": "Heavy REE", "reserves_mt": 1.5, "note": "Significant heavy REE deposit in Labrador"},
    {"name": "Ngualla", "country": "Tanzania", "lat": -8.2830, "lon": 32.0330, "element": "Mixed REE", "reserves_mt": 2.7, "note": "One of the largest undeveloped REE deposits"},
    {"name": "Longnan (ion-adsorption)", "country": "China", "lat": 24.9100, "lon": 114.7700, "element": "Heavy REE", "reserves_mt": 1.2, "note": "Southern China ionic clays, key heavy REE source"},
    {"name": "Araxa", "country": "Brazil", "lat": -19.5930, "lon": -46.9430, "element": "Niobium/REE", "reserves_mt": 1.6, "note": "CBMM, controls 80% of world niobium supply"},
    {"name": "Dong Pao", "country": "Vietnam", "lat": 21.8500, "lon": 103.5000, "element": "Mixed REE", "reserves_mt": 5.5, "note": "Largest REE deposit in Vietnam"},
    {"name": "Zandkopsdrift", "country": "South Africa", "lat": -31.3170, "lon": 18.6500, "element": "Light REE", "reserves_mt": 0.9, "note": "High-grade carbonatite deposit"},
]

OIL_GAS_FIELDS = [
    {"name": "Ghawar Field", "country": "Saudi Arabia", "lat": 25.4000, "lon": 49.4000, "type": "Oil", "reserves_bbbl": 75.0, "note": "Largest conventional oil field ever discovered"},
    {"name": "Burgan Field", "country": "Kuwait", "lat": 29.0667, "lon": 47.9833, "type": "Oil", "reserves_bbbl": 66.0, "note": "Second largest oil field in the world"},
    {"name": "Safaniya Field", "country": "Saudi Arabia", "lat": 28.2000, "lon": 48.8000, "type": "Oil", "reserves_bbbl": 37.0, "note": "World's largest offshore oil field"},
    {"name": "Permian Basin", "country": "USA", "lat": 31.9500, "lon": -102.1000, "type": "Oil/Gas", "reserves_bbbl": 46.0, "note": "Largest US oil-producing basin, shale revolution hub"},
    {"name": "Prudhoe Bay", "country": "USA (Alaska)", "lat": 70.2800, "lon": -148.3300, "type": "Oil", "reserves_bbbl": 25.0, "note": "Largest North American oil field"},
    {"name": "Samotlor Field", "country": "Russia", "lat": 61.1667, "lon": 76.7000, "type": "Oil", "reserves_bbbl": 28.0, "note": "Russia's largest oil field, Western Siberia"},
    {"name": "Kashagan Field", "country": "Kazakhstan", "lat": 46.2000, "lon": 51.8000, "type": "Oil", "reserves_bbbl": 13.0, "note": "Largest discovery in past 40 years, Caspian Sea"},
    {"name": "Cantarell Complex", "country": "Mexico", "lat": 19.9500, "lon": -91.7000, "type": "Oil", "reserves_bbbl": 18.0, "note": "Bay of Campeche, declining superfield"},
    {"name": "Daqing Field", "country": "China", "lat": 46.6000, "lon": 125.0000, "type": "Oil", "reserves_bbbl": 16.0, "note": "China's largest oil field, Heilongjiang province"},
    {"name": "North Field / South Pars", "country": "Qatar/Iran", "lat": 26.5000, "lon": 52.0000, "type": "Gas", "reserves_bbbl": 10.0, "note": "World's largest natural gas field (shared)"},
    {"name": "Groningen Field", "country": "Netherlands", "lat": 53.3333, "lon": 6.7500, "type": "Gas", "reserves_bbbl": 2.8, "note": "Europe's largest gas field, being shut down due to earthquakes"},
    {"name": "Tengiz Field", "country": "Kazakhstan", "lat": 46.2833, "lon": 53.3833, "type": "Oil", "reserves_bbbl": 9.0, "note": "Major Caspian field, Chevron-operated"},
    {"name": "Rumaila Field", "country": "Iraq", "lat": 30.5833, "lon": 47.3333, "type": "Oil", "reserves_bbbl": 17.0, "note": "Iraq's largest producing oil field"},
    {"name": "Tupi / Lula Field", "country": "Brazil", "lat": -25.3000, "lon": -42.8000, "type": "Oil", "reserves_bbbl": 8.3, "note": "Pre-salt deepwater, Santos Basin"},
    {"name": "Zakum Field", "country": "UAE", "lat": 24.8333, "lon": 53.8333, "type": "Oil", "reserves_bbbl": 21.0, "note": "Upper and Lower Zakum, Abu Dhabi offshore"},
    {"name": "Ekofisk Field", "country": "Norway", "lat": 56.5449, "lon": 3.2113, "type": "Oil/Gas", "reserves_bbbl": 3.3, "note": "First major North Sea discovery (1969)"},
    {"name": "Brent Field", "country": "UK", "lat": 61.0500, "lon": 1.7167, "type": "Oil", "reserves_bbbl": 2.0, "note": "Namesake of Brent crude oil benchmark"},
    {"name": "Ahwaz Field", "country": "Iran", "lat": 31.3000, "lon": 48.7000, "type": "Oil", "reserves_bbbl": 25.0, "note": "One of Iran's largest onshore fields"},
    {"name": "Manifa Field", "country": "Saudi Arabia", "lat": 27.6500, "lon": 49.0000, "type": "Oil", "reserves_bbbl": 11.0, "note": "Heavy crude offshore field"},
    {"name": "Hassi Messaoud", "country": "Algeria", "lat": 31.6800, "lon": 6.0700, "type": "Oil", "reserves_bbbl": 6.4, "note": "Algeria's largest oil field, Sahara Desert"},
    {"name": "Urengoy Field", "country": "Russia", "lat": 67.0000, "lon": 76.0000, "type": "Gas", "reserves_bbbl": 1.5, "note": "Third largest natural gas field in the world"},
    {"name": "Marcellus Shale", "country": "USA", "lat": 41.0000, "lon": -77.5000, "type": "Gas", "reserves_bbbl": 0.5, "note": "Largest US shale gas play, Appalachian Basin"},
    {"name": "Eagle Ford Shale", "country": "USA", "lat": 28.7000, "lon": -98.5000, "type": "Oil/Gas", "reserves_bbbl": 3.4, "note": "Major Texas tight oil and shale gas play"},
    {"name": "Vaca Muerta", "country": "Argentina", "lat": -38.5000, "lon": -69.0000, "type": "Oil/Gas", "reserves_bbbl": 16.0, "note": "Second largest shale gas deposit globally"},
]

DIAMOND_MINES = [
    {"name": "Jwaneng Mine", "country": "Botswana", "lat": -24.5230, "lon": 24.6570, "carats_mpy": 12.5, "type": "Kimberlite", "note": "World's richest diamond mine by value"},
    {"name": "Orapa Mine", "country": "Botswana", "lat": -21.3170, "lon": 25.3830, "carats_mpy": 11.0, "type": "Kimberlite", "note": "World's largest diamond mine by area"},
    {"name": "Mirny Mine", "country": "Russia", "lat": 62.5167, "lon": 113.9833, "carats_mpy": 2.0, "type": "Kimberlite", "note": "Iconic 525m deep pit in Yakutia, now closed open-pit"},
    {"name": "Udachny Mine", "country": "Russia", "lat": 66.4310, "lon": 112.3540, "carats_mpy": 3.5, "type": "Kimberlite", "note": "One of the largest diamond pipes in Russia"},
    {"name": "Argyle Mine", "country": "Australia", "lat": -16.7170, "lon": 128.3830, "carats_mpy": 0.1, "type": "Lamproite", "note": "Source of 90% of world's pink diamonds, closed 2020"},
    {"name": "Catoca Mine", "country": "Angola", "lat": -9.1330, "lon": 20.3330, "carats_mpy": 6.8, "type": "Kimberlite", "note": "Largest diamond mine in Angola, 4th largest globally"},
    {"name": "Venetia Mine", "country": "South Africa", "lat": -22.4500, "lon": 29.3170, "carats_mpy": 4.5, "type": "Kimberlite", "note": "De Beers' largest operation in South Africa"},
    {"name": "Gahcho Kue Mine", "country": "Canada", "lat": 63.4330, "lon": -109.2000, "carats_mpy": 5.5, "type": "Kimberlite", "note": "Remote Arctic diamond mine, NW Territories"},
    {"name": "Diavik Mine", "country": "Canada", "lat": 64.4960, "lon": -110.2670, "carats_mpy": 6.2, "type": "Kimberlite", "note": "Island mine in Lac de Gras, high-quality gems"},
    {"name": "Ekati Mine", "country": "Canada", "lat": 64.7000, "lon": -110.6167, "carats_mpy": 4.0, "type": "Kimberlite", "note": "Canada's first commercial diamond mine (1998)"},
    {"name": "Kimberley Big Hole", "country": "South Africa", "lat": -28.7282, "lon": 24.7499, "carats_mpy": 0.0, "type": "Kimberlite", "note": "Historic: world's largest hand-dug excavation, closed 1914"},
    {"name": "Cullinan (Premier) Mine", "country": "South Africa", "lat": -25.4000, "lon": 28.5167, "carats_mpy": 2.1, "type": "Kimberlite", "note": "Source of the Cullinan Diamond (3,106 ct)"},
    {"name": "Letseng Mine", "country": "Lesotho", "lat": -29.0000, "lon": 28.8670, "carats_mpy": 0.1, "type": "Kimberlite", "note": "Highest dollar-per-carat mine in the world"},
    {"name": "Mbuji-Mayi", "country": "DRC", "lat": -6.1500, "lon": 23.6000, "carats_mpy": 8.0, "type": "Alluvial/Kimberlite", "note": "Industrial diamonds, massive alluvial deposits"},
    {"name": "Koidu Mine", "country": "Sierra Leone", "lat": 8.6430, "lon": -10.9670, "carats_mpy": 0.4, "type": "Kimberlite", "note": "Post-conflict diamond mine, formerly blood diamonds"},
    {"name": "Aikhal Mine", "country": "Russia", "lat": 65.9500, "lon": 111.4830, "carats_mpy": 3.0, "type": "Kimberlite", "note": "Major ALROSA operation in Yakutia"},
    {"name": "Karowe Mine", "country": "Botswana", "lat": -21.4170, "lon": 25.5830, "carats_mpy": 0.3, "type": "Kimberlite", "note": "Found 1,758 ct Sewelo diamond (2019)"},
    {"name": "Marange Fields", "country": "Zimbabwe", "lat": -19.8000, "lon": 32.8000, "carats_mpy": 4.0, "type": "Alluvial", "note": "Controversial alluvial diamond fields"},
    {"name": "Williamson Mine", "country": "Tanzania", "lat": -3.6830, "lon": 33.4170, "carats_mpy": 0.2, "type": "Kimberlite", "note": "Source of famous Williamson Pink Star diamond"},
]

COAL_REGIONS = [
    {"name": "Powder River Basin", "country": "USA", "lat": 43.8000, "lon": -105.5000, "production_mt": 300, "type": "Thermal", "note": "Largest US coal basin, low-sulfur subbituminous"},
    {"name": "Appalachian Basin", "country": "USA", "lat": 38.5000, "lon": -81.0000, "production_mt": 120, "type": "Metallurgical/Thermal", "note": "Historic US coal region, mountaintop removal controversy"},
    {"name": "Shanxi Province", "country": "China", "lat": 37.8700, "lon": 112.5500, "production_mt": 1000, "type": "Thermal/Metallurgical", "note": "China's largest coal-producing province"},
    {"name": "Inner Mongolia", "country": "China", "lat": 40.8000, "lon": 111.7000, "production_mt": 900, "type": "Thermal", "note": "China's #2 coal province, open-pit surface mining"},
    {"name": "Kuznetsk Basin (Kuzbass)", "country": "Russia", "lat": 54.0000, "lon": 86.5000, "production_mt": 250, "type": "Metallurgical/Thermal", "note": "Russia's primary coal basin"},
    {"name": "Donets Basin (Donbas)", "country": "Ukraine/Russia", "lat": 48.0000, "lon": 38.0000, "production_mt": 30, "type": "Thermal/Metallurgical", "note": "Historic coal region, now conflict zone"},
    {"name": "Jharkhand-Odisha Belt", "country": "India", "lat": 23.6000, "lon": 85.3000, "production_mt": 400, "type": "Thermal", "note": "India's main coal belt, Coal India operations"},
    {"name": "Hunter Valley", "country": "Australia", "lat": -32.5000, "lon": 151.0000, "production_mt": 160, "type": "Thermal", "note": "NSW's premier coal export region"},
    {"name": "Bowen Basin", "country": "Australia", "lat": -22.5000, "lon": 148.5000, "production_mt": 200, "type": "Metallurgical", "note": "World's largest metallurgical coal export region"},
    {"name": "Ruhr Valley", "country": "Germany", "lat": 51.4500, "lon": 7.0000, "production_mt": 0, "type": "Hard Coal", "note": "Historic industrial heartland, last mine closed 2018"},
    {"name": "Silesian Basin", "country": "Poland", "lat": 50.2600, "lon": 19.0200, "production_mt": 55, "type": "Hard Coal", "note": "Poland's coal heartland, EU's largest coal producer"},
    {"name": "South Wales Coalfield", "country": "UK", "lat": 51.7000, "lon": -3.5000, "production_mt": 0, "type": "Anthracite", "note": "Historic coalfield, all deep mines now closed"},
    {"name": "Mpumalanga Coalfields", "country": "South Africa", "lat": -26.0000, "lon": 29.5000, "production_mt": 250, "type": "Thermal", "note": "Supplies majority of South Africa's electricity"},
    {"name": "Latrobe Valley", "country": "Australia", "lat": -38.2000, "lon": 146.5000, "production_mt": 50, "type": "Lignite", "note": "Brown coal open pits, Victoria's power source"},
    {"name": "Cerrejon", "country": "Colombia", "lat": 11.1170, "lon": -72.6170, "production_mt": 27, "type": "Thermal", "note": "Largest coal mine in Latin America"},
    {"name": "Thar Coalfield", "country": "Pakistan", "lat": 24.5000, "lon": 70.0000, "production_mt": 12, "type": "Lignite", "note": "175 billion tonnes reserves, one of the world's largest"},
    {"name": "Hambach/Garzweiler", "country": "Germany", "lat": 50.9100, "lon": 6.5100, "production_mt": 80, "type": "Lignite", "note": "Massive open-pit lignite mines, controversial expansion"},
    {"name": "Kalimantan", "country": "Indonesia", "lat": -1.5000, "lon": 116.0000, "production_mt": 450, "type": "Thermal", "note": "Indonesia's main coal export region"},
]

URANIUM_DEPOSITS = [
    {"name": "McArthur River Mine", "country": "Canada", "lat": 57.7667, "lon": -105.0833, "production_t": 6900, "note": "Highest-grade uranium mine in the world"},
    {"name": "Cigar Lake Mine", "country": "Canada", "lat": 58.0500, "lon": -104.5500, "production_t": 6900, "note": "Second highest-grade deposit, Athabasca Basin"},
    {"name": "Inkai Mine", "country": "Kazakhstan", "lat": 44.2500, "lon": 67.8333, "production_t": 3800, "note": "Major ISL (in-situ leach) operation"},
    {"name": "Tortkuduk Mine", "country": "Kazakhstan", "lat": 44.5000, "lon": 68.0000, "production_t": 3000, "note": "Kazatomprom ISL mine in Chu-Sarysu Basin"},
    {"name": "Husab Mine", "country": "Namibia", "lat": -22.5500, "lon": 15.0500, "production_t": 3400, "note": "Second largest uranium mine globally, Chinese-owned"},
    {"name": "Rossing Mine", "country": "Namibia", "lat": -22.4830, "lon": 15.1830, "production_t": 2100, "note": "Historic open-pit mine, operating since 1976"},
    {"name": "Olympic Dam", "country": "Australia", "lat": -30.4500, "lon": 136.8833, "production_t": 3500, "note": "World's largest known uranium deposit, BHP"},
    {"name": "Ranger Mine", "country": "Australia", "lat": -12.6830, "lon": 132.9170, "production_t": 0, "note": "Closed 2021, in Kakadu National Park"},
    {"name": "Kraznokamensk", "country": "Russia", "lat": 50.1000, "lon": 118.0000, "production_t": 2900, "note": "Russia's primary uranium mine, Transbaikal"},
    {"name": "Somair/Cominak", "country": "Niger", "lat": 18.5000, "lon": 7.3500, "production_t": 2000, "note": "Arlit mines, major African uranium source"},
    {"name": "Langer Heinrich", "country": "Namibia", "lat": -22.8170, "lon": 15.3170, "production_t": 1800, "note": "Calcrete deposit, restarted 2024"},
    {"name": "Budenovskoye", "country": "Kazakhstan", "lat": 44.0000, "lon": 68.5000, "production_t": 2500, "note": "Large ISL deposit, Kazatomprom/Uranium One"},
    {"name": "Four Mile Mine", "country": "Australia", "lat": -30.1000, "lon": 139.5000, "production_t": 800, "note": "ISL mine in South Australia"},
    {"name": "Jaduguda Mine", "country": "India", "lat": 22.6500, "lon": 86.3500, "production_t": 200, "note": "India's oldest uranium mine, Jharkhand state"},
    {"name": "Imouraren", "country": "Niger", "lat": 17.1000, "lon": 7.8000, "production_t": 0, "note": "Undeveloped mega deposit, 200,000 t reserves"},
]

LITHIUM_DEPOSITS = [
    {"name": "Salar de Atacama", "country": "Chile", "lat": -23.5000, "lon": -68.2500, "reserves_kt": 7500, "type": "Brine", "note": "World's largest lithium-producing salar"},
    {"name": "Salar de Uyuni", "country": "Bolivia", "lat": -20.1338, "lon": -67.4891, "reserves_kt": 21000, "type": "Brine", "note": "World's largest salt flat, largest lithium reserve"},
    {"name": "Salar de Hombre Muerto", "country": "Argentina", "lat": -25.3500, "lon": -67.0833, "reserves_kt": 850, "type": "Brine", "note": "Galaxy Resources/Orocobre operation"},
    {"name": "Salar de Olaroz", "country": "Argentina", "lat": -23.5000, "lon": -66.6833, "reserves_kt": 600, "type": "Brine", "note": "Allkem/Toyota Tsusho joint venture"},
    {"name": "Greenbushes Mine", "country": "Australia", "lat": -33.8500, "lon": 116.0500, "reserves_kt": 1500, "type": "Hard Rock (Spodumene)", "note": "Largest hard-rock lithium mine in the world"},
    {"name": "Pilgangoora Mine", "country": "Australia", "lat": -21.3000, "lon": 118.8500, "reserves_kt": 700, "type": "Hard Rock", "note": "Pilbara Minerals, major spodumene producer"},
    {"name": "Mount Cattlin", "country": "Australia", "lat": -33.5670, "lon": 120.2170, "reserves_kt": 250, "type": "Hard Rock", "note": "Allkem operation in Western Australia"},
    {"name": "Jiangxi Province", "country": "China", "lat": 28.6800, "lon": 115.8600, "reserves_kt": 800, "type": "Hard Rock (Lepidolite)", "note": "China's main domestic lithium processing hub"},
    {"name": "Sichuan Province", "country": "China", "lat": 30.5700, "lon": 104.0700, "reserves_kt": 1500, "type": "Hard Rock (Spodumene)", "note": "Ganzi region spodumene deposits"},
    {"name": "Jadar Valley", "country": "Serbia", "lat": 44.2500, "lon": 19.1500, "reserves_kt": 1200, "type": "Jadarite (new mineral)", "note": "Rio Tinto deposit, unique mineral jadarite"},
    {"name": "Thacker Pass", "country": "USA (Nevada)", "lat": 41.3500, "lon": -117.5000, "reserves_kt": 600, "type": "Sedimentary Clay", "note": "Lithium Americas, largest US lithium deposit"},
    {"name": "Manono Project", "country": "DRC", "lat": -7.2833, "lon": 27.4167, "reserves_kt": 1600, "type": "Hard Rock (Pegmatite)", "note": "One of the world's largest lithium pegmatites"},
    {"name": "Cauchari-Olaroz", "country": "Argentina", "lat": -23.4000, "lon": -66.7333, "reserves_kt": 500, "type": "Brine", "note": "Lithium Americas / Ganfeng joint operation"},
    {"name": "Whabouchi", "country": "Canada", "lat": 49.8500, "lon": -75.9000, "reserves_kt": 300, "type": "Hard Rock", "note": "Nemaska Lithium, Quebec spodumene deposit"},
    {"name": "Bikita Mine", "country": "Zimbabwe", "lat": -20.0330, "lon": 31.4000, "reserves_kt": 200, "type": "Hard Rock (Petalite)", "note": "One of Africa's oldest lithium mines"},
    {"name": "Salar del Rincon", "country": "Argentina", "lat": -24.2000, "lon": -67.1500, "reserves_kt": 400, "type": "Brine", "note": "High-altitude brine salar, Salta province"},
    {"name": "Salton Sea", "country": "USA (California)", "lat": 33.2500, "lon": -115.8333, "reserves_kt": 350, "type": "Geothermal Brine", "note": "Lithium extraction from geothermal brines"},
]

DEEP_SEA_MINING = [
    {"name": "Clarion-Clipperton Zone (West)", "country": "International", "lat": 12.0000, "lon": -140.0000, "resource": "Manganese Nodules", "depth_m": 4500, "note": "Primary exploration area, 4-6 billion tonnes of nodules"},
    {"name": "Clarion-Clipperton Zone (Central)", "country": "International", "lat": 11.0000, "lon": -125.0000, "resource": "Manganese Nodules", "depth_m": 4800, "note": "ISA-licensed exploration blocks"},
    {"name": "Clarion-Clipperton Zone (East)", "country": "International", "lat": 10.0000, "lon": -115.0000, "resource": "Manganese Nodules", "depth_m": 4300, "note": "Multiple contractor exploration zones"},
    {"name": "NORI-D Block (Nauru)", "country": "Nauru (sponsor)", "lat": 12.5000, "lon": -116.5000, "resource": "Polymetallic Nodules", "depth_m": 4200, "note": "The Metals Company pilot site, first ocean-floor harvest tests"},
    {"name": "Cook Islands EEZ", "country": "Cook Islands", "lat": -15.0000, "lon": -160.0000, "resource": "Manganese Nodules", "depth_m": 5000, "note": "Trillions of dollars in nodule deposits"},
    {"name": "Mid-Atlantic Ridge (TAG)", "country": "International", "lat": 26.1370, "lon": -44.8260, "resource": "Polymetallic Sulfides", "depth_m": 3600, "note": "Trans-Atlantic Geotraverse hydrothermal field"},
    {"name": "Solwara 1", "country": "Papua New Guinea", "lat": -3.7900, "lon": 152.0900, "resource": "Polymetallic Sulfides", "depth_m": 1600, "note": "First deep-sea mining lease (Nautilus Minerals, now defunct)"},
    {"name": "Central Indian Ocean Basin", "country": "India (sponsor)", "lat": -12.0000, "lon": 76.0000, "resource": "Manganese Nodules", "depth_m": 5200, "note": "India has exploration rights from ISA"},
    {"name": "Penrhyn Basin", "country": "Cook Islands", "lat": -11.0000, "lon": -160.0000, "resource": "Manganese Nodules", "depth_m": 5100, "note": "Estimated 10 billion tonnes of nodules"},
    {"name": "Kermadec Arc", "country": "New Zealand", "lat": -31.0000, "lon": -178.0000, "resource": "Polymetallic Sulfides", "depth_m": 1500, "note": "Hydrothermal vents with copper/gold sulfides"},
    {"name": "Magellan Seamounts", "country": "International", "lat": 15.0000, "lon": 155.0000, "resource": "Cobalt-rich Crusts", "depth_m": 1800, "note": "Seamount crusts rich in cobalt, nickel, manganese"},
    {"name": "Prime Crust Zone (Pacific)", "country": "International", "lat": 20.0000, "lon": 170.0000, "resource": "Cobalt-rich Crusts", "depth_m": 2000, "note": "Japan/China/Korea exploration areas"},
    {"name": "Red Sea Brine Pools", "country": "Saudi Arabia/Sudan", "lat": 21.3500, "lon": 38.0500, "resource": "Metalliferous Muds", "depth_m": 2000, "note": "Zinc, copper, silver in hot brine deposits"},
    {"name": "Bismarck Sea", "country": "Papua New Guinea", "lat": -3.5000, "lon": 149.0000, "resource": "Polymetallic Sulfides", "depth_m": 1700, "note": "Multiple hydrothermal vent systems"},
    {"name": "SW Indian Ridge", "country": "International", "lat": -37.7800, "lon": 49.6500, "resource": "Polymetallic Sulfides", "depth_m": 2800, "note": "China exploration license from ISA"},
]

HISTORICAL_MINES = [
    {"name": "Laurion Silver Mines", "country": "Greece", "lat": 37.7300, "lon": 24.0200, "era": "5th century BCE", "resource": "Silver/Lead", "note": "Funded Athenian navy that defeated Persia at Salamis"},
    {"name": "Rio Tinto Mines", "country": "Spain", "lat": 37.6960, "lon": -6.5990, "era": "3000 BCE - present", "resource": "Copper/Gold/Silver", "note": "5,000 years of continuous mining, Phoenician origins"},
    {"name": "Cerro Rico de Potosi", "country": "Bolivia", "lat": -19.6133, "lon": -65.7533, "era": "1545 CE", "resource": "Silver", "note": "Richest silver deposit ever, 8 million died in its mines"},
    {"name": "King Solomon's Mines (Timna)", "country": "Israel", "lat": 29.7830, "lon": 34.9830, "era": "14th century BCE", "resource": "Copper", "note": "Egyptian-era copper smelting, Biblical associations"},
    {"name": "Rammelsberg Mine", "country": "Germany", "lat": 51.8920, "lon": 10.4200, "era": "968 CE - 1988", "resource": "Copper/Zinc/Lead", "note": "UNESCO site, over 1,000 years of continuous mining"},
    {"name": "Almaden Mercury Mine", "country": "Spain", "lat": 38.7740, "lon": -4.8380, "era": "500 BCE", "resource": "Mercury (Cinnabar)", "note": "Largest mercury deposit ever, UNESCO World Heritage"},
    {"name": "Great Copper Mountain (Falun)", "country": "Sweden", "lat": 60.6020, "lon": 15.6320, "era": "9th century CE", "resource": "Copper", "note": "UNESCO site, funded Swedish Empire's wars"},
    {"name": "Wieliczka Salt Mine", "country": "Poland", "lat": 49.9830, "lon": 20.0550, "era": "13th century CE", "resource": "Salt", "note": "UNESCO site, underground cathedral carved in salt"},
    {"name": "Huancavelica Mercury Mine", "country": "Peru", "lat": -12.7864, "lon": -74.9730, "era": "1563 CE", "resource": "Mercury", "note": "Supplied mercury for colonial silver extraction"},
    {"name": "Broken Hill (Yancowinna)", "country": "Australia", "lat": -31.9500, "lon": 141.4500, "era": "1883 CE", "resource": "Silver/Lead/Zinc", "note": "Birthplace of BHP, still producing after 140+ years"},
    {"name": "Banska Stiavnica", "country": "Slovakia", "lat": 48.4589, "lon": 18.8930, "era": "3rd century BCE", "resource": "Gold/Silver", "note": "UNESCO site, medieval mining academy (first in world)"},
    {"name": "Iwami Ginzan Silver Mine", "country": "Japan", "lat": 35.1100, "lon": 132.4300, "era": "1526 CE", "resource": "Silver", "note": "UNESCO site, produced 1/3 of world's silver in 1600s"},
    {"name": "Rosia Montana", "country": "Romania", "lat": 46.3070, "lon": 23.1270, "era": "106 CE (Roman)", "resource": "Gold", "note": "Roman Alburnus Maior, largest ancient gold mine in Europe"},
    {"name": "Lavrion (Ancient Laurium)", "country": "Greece", "lat": 37.7170, "lon": 24.0500, "era": "3000 BCE", "resource": "Silver/Lead", "note": "Over 2,000 mining shafts, some survive today"},
    {"name": "Dolaucothi Gold Mines", "country": "Wales, UK", "lat": 52.0360, "lon": -3.9340, "era": "75 CE (Roman)", "resource": "Gold", "note": "Only Roman gold mine in Britain, aqueduct-fed hushing"},
    {"name": "Las Medulas", "country": "Spain", "lat": 42.4680, "lon": -6.7670, "era": "1st century CE", "resource": "Gold", "note": "Roman hydraulic mining (ruina montium), UNESCO site"},
    {"name": "Zacatecas Mines", "country": "Mexico", "lat": 22.7709, "lon": -102.5832, "era": "1546 CE", "resource": "Silver", "note": "Key Silver Road mine, fueled Spanish colonial economy"},
    {"name": "Cripple Creek", "country": "USA", "lat": 38.7467, "lon": -105.1783, "era": "1891 CE", "resource": "Gold", "note": "Colorado Gold Rush, $500M in gold by 1961"},
    {"name": "Kolar Gold Fields", "country": "India", "lat": 12.9500, "lon": 78.2800, "era": "2nd century CE", "resource": "Gold", "note": "Among the deepest mines in India, mined since Gupta era"},
    {"name": "Mount Pangaion", "country": "Greece", "lat": 41.0000, "lon": 24.1000, "era": "7th century BCE", "resource": "Gold/Silver", "note": "Funded Philip II of Macedon, father of Alexander the Great"},
    {"name": "Cerro de Pasco", "country": "Peru", "lat": -10.6833, "lon": -76.2500, "era": "1630 CE", "resource": "Silver/Copper/Zinc", "note": "4,380m altitude, pit literally swallowing the city"},
    {"name": "Kongsberg Silver Mine", "country": "Norway", "lat": 59.6330, "lon": 9.6500, "era": "1623 CE", "resource": "Silver", "note": "Native silver crystals, funded Norwegian state"},
    {"name": "Freiberg Mines", "country": "Germany", "lat": 50.9167, "lon": 13.3333, "era": "1168 CE", "resource": "Silver/Lead", "note": "Birthplace of modern mining science and geology"},
]


# ═══════════════════════════════════════════════════════════════
# OVERPASS QUERY HELPER
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _query_mining_osm(lat: float, lon: float, radius_km: float) -> list:
    """Query Overpass API for mining features near a location."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["landuse"="quarry"](around:{radius_m},{lat},{lon});
  way["landuse"="quarry"](around:{radius_m},{lat},{lon});
  node["man_made"="mineshaft"](around:{radius_m},{lat},{lon});
  node["man_made"="adit"](around:{radius_m},{lat},{lon});
  way["man_made"="adit"](around:{radius_m},{lat},{lon});
  node["industrial"="mine"](around:{radius_m},{lat},{lon});
  way["industrial"="mine"](around:{radius_m},{lat},{lon});
  node["man_made"="mine"](around:{radius_m},{lat},{lon});
  way["man_made"="mine"](around:{radius_m},{lat},{lon});
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
            coords = [(node_lookup[n][0], node_lookup[n][1])
                      for n in nodes if n in node_lookup]
            if coords:
                lat_f = sum(c[0] for c in coords) / len(coords)
                lon_f = sum(c[1] for c in coords) / len(coords)
        if lat_f is None or lon_f is None:
            continue
        features.append({
            "name": tags.get("name", tags.get("name:en", "Unnamed site")),
            "type": tags.get("man_made", tags.get("landuse", tags.get("industrial", "unknown"))),
            "resource": tags.get("resource", tags.get("product", "")),
            "operator": tags.get("operator", ""),
            "lat": lat_f,
            "lon": lon_f,
            "osm_id": el.get("id"),
        })
    return features


# ═══════════════════════════════════════════════════════════════
# MAP BUILDING HELPERS
# ═══════════════════════════════════════════════════════════════
def _build_map(data: list, lat_key: str, lon_key: str, name_key: str,
               color: str, popup_fn, zoom: int = 2,
               center: tuple = None) -> folium.Map:
    """Build a folium map from a list of dicts."""
    if center is None:
        if data:
            center = (
                sum(d[lat_key] for d in data) / len(data),
                sum(d[lon_key] for d in data) / len(data),
            )
        else:
            center = (20.0, 0.0)

    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        overlay=False,
    ).add_to(m)

    for item in data:
        popup_html = popup_fn(item)
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=7,
            color=color if isinstance(color, str) else color(item),
            fill=True,
            fill_color=color if isinstance(color, str) else color(item),
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(str(item.get(name_key, ""))),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def _resource_color(resource_str: str) -> str:
    """Pick a color based on resource keywords."""
    r = resource_str.lower()
    if "gold" in r:
        return RESOURCE_COLORS["gold"]
    if "copper" in r:
        return RESOURCE_COLORS["copper"]
    if "iron" in r:
        return RESOURCE_COLORS["iron"]
    if "coal" in r or "lignite" in r:
        return RESOURCE_COLORS["coal"]
    if "diamond" in r:
        return RESOURCE_COLORS["diamond"]
    if "uranium" in r:
        return RESOURCE_COLORS["uranium"]
    if "lithium" in r:
        return RESOURCE_COLORS["lithium"]
    if "oil" in r:
        return "#1a1a2e"
    if "gas" in r:
        return RESOURCE_COLORS["gas"]
    if "nickel" in r:
        return RESOURCE_COLORS["nickel"]
    if "silver" in r:
        return RESOURCE_COLORS["silver"]
    if "platinum" in r or "palladium" in r:
        return RESOURCE_COLORS["platinum"]
    if "zinc" in r:
        return RESOURCE_COLORS["zinc"]
    if "rare" in r or "ree" in r:
        return RESOURCE_COLORS["rare_earth"]
    return "#f59e0b"


def _make_chart(labels: list, values: list, colors: list,
                title: str, xlabel: str = "Count",
                chart_type: str = "barh"):
    """Create a dark-themed matplotlib chart and display via st.pyplot."""
    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.4)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    if chart_type == "barh":
        bars = ax.barh(range(len(labels)), values, color=colors, alpha=0.85)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels([str(l)[:30] for l in labels],
                           color="#e8ecf4", fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel(xlabel, color="#e8ecf4", fontsize=10)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:,.1f}" if isinstance(val, float) else f"{val:,}",
                    va="center", color="#8b97b0", fontsize=8)
    elif chart_type == "bar":
        ax.bar(range(len(labels)), values, color=colors, alpha=0.85)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels([str(l)[:15] for l in labels],
                           color="#e8ecf4", fontsize=8, rotation=45, ha="right")
        ax.set_ylabel(xlabel, color="#e8ecf4", fontsize=10)

    ax.set_title(title, color="#e8ecf4", fontsize=12, pad=10)
    ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x" if chart_type == "barh" else "y",
            color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _show_download(df: pd.DataFrame, filename: str, key: str):
    """Show dataframe and CSV download button."""
    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} records (CSV)",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


# ═══════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_largest_mines():
    """Mode 1: World's Largest Mines."""
    data = WORLDS_LARGEST_MINES
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["World's Largest Mines"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Mines", len(data))
    countries = set(d["country"] for d in data)
    c2.metric("Countries", len(countries))
    total_prod = sum(d["production_mt"] for d in data)
    c3.metric("Total Production", f"{total_prod:,.0f} Mt/yr")
    open_pit = sum(1 for d in data if "Open-pit" in d["type"])
    c4.metric("Open-pit Mines", open_pit)

    # OSM search option
    with st.expander("Search nearby mining sites via OpenStreetMap"):
        oc1, oc2, oc3 = st.columns(3)
        osm_lat = oc1.number_input("Latitude", value=40.52, format="%.2f",
                                   key="mine_osm_lat")
        osm_lon = oc2.number_input("Longitude", value=-112.15, format="%.2f",
                                   key="mine_osm_lon")
        osm_rad = oc3.slider("Radius (km)", 1, 100, 20, key="mine_osm_rad")
        if st.button("Search OSM", key="mine_osm_btn"):
            with st.spinner("Querying Overpass API..."):
                osm_feats = _query_mining_osm(osm_lat, osm_lon, osm_rad)
            if osm_feats:
                st.success(f"Found {len(osm_feats)} mining features from OSM")
                osm_df = pd.DataFrame(osm_feats)
                st.dataframe(osm_df, width="stretch", hide_index=True)
            else:
                st.warning("No mining features found in this area via OSM.")

    # Chart
    st.markdown("##### Top 15 by Production")
    top15 = sorted(data, key=lambda x: x["production_mt"], reverse=True)[:15]
    _make_chart(
        [d["name"] for d in top15],
        [d["production_mt"] for d in top15],
        [_resource_color(d["resource"]) for d in top15],
        "Annual Production (Million Tonnes)",
        xlabel="Mt/yr",
    )

    # Map
    st.markdown("##### Global Mine Map")

    def popup_fn(d):
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">'
            f'{escape(d["country"])} | {escape(d["resource"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Type: {escape(d["type"])}<br/>'
            f'Production: {d["production_mt"]:,.0f} Mt/yr<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=lambda d: _resource_color(d["resource"]),
                   popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    # Table + download
    df = pd.DataFrame(data)
    _show_download(df, "worlds_largest_mines.csv", "dl_largest_mines")


def _render_gold_deposits():
    """Mode 2: Gold Deposits."""
    data = GOLD_DEPOSITS
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Gold Deposits"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Deposits Mapped", len(data))
    countries = set(d["country"] for d in data)
    c2.metric("Countries/Regions", len(countries))
    total_kg = sum(d["production_kg"] for d in data)
    c3.metric("Total Annual Output", f"{total_kg:,.0f} kg/yr")

    st.markdown("##### Top Producers by Annual Output")
    top12 = sorted(data, key=lambda x: x["production_kg"], reverse=True)[:12]
    _make_chart(
        [d["name"] for d in top12],
        [d["production_kg"] for d in top12],
        [RESOURCE_COLORS["gold"]] * len(top12),
        "Annual Gold Production (kg)",
        xlabel="kg/yr",
    )

    st.markdown("##### Gold Deposit Map")

    def popup_fn(d):
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Production: {d["production_kg"]:,} kg/yr<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=RESOURCE_COLORS["gold"],
                   popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "gold_deposits.csv", "dl_gold")


def _render_rare_earth():
    """Mode 3: Rare Earth Elements."""
    data = RARE_EARTH_DEPOSITS
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Rare Earth Elements"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Deposits Mapped", len(data))
    china_count = sum(1 for d in data if d["country"] == "China")
    c2.metric("Chinese Deposits", china_count)
    total_res = sum(d["reserves_mt"] for d in data)
    c3.metric("Total Reserves", f"{total_res:,.1f} Mt REO")

    st.markdown("##### Reserves by Deposit")
    sorted_data = sorted(data, key=lambda x: x["reserves_mt"], reverse=True)
    _make_chart(
        [d["name"] for d in sorted_data],
        [d["reserves_mt"] for d in sorted_data],
        [RESOURCE_COLORS["rare_earth"]] * len(sorted_data),
        "Rare Earth Reserves (Million Tonnes REO)",
        xlabel="Mt REO",
    )

    st.markdown("##### REE Deposit Map")

    def popup_fn(d):
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Element: {escape(d["element"])}<br/>'
            f'Reserves: {d["reserves_mt"]:,.1f} Mt<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=RESOURCE_COLORS["rare_earth"],
                   popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "rare_earth_deposits.csv", "dl_ree")


def _render_oil_gas():
    """Mode 4: Oil & Gas Fields."""
    data = OIL_GAS_FIELDS
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Oil & Gas Fields"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fields Mapped", len(data))
    oil_only = sum(1 for d in data if d["type"] == "Oil")
    c2.metric("Oil Fields", oil_only)
    gas_only = sum(1 for d in data if d["type"] == "Gas")
    c3.metric("Gas Fields", gas_only)
    total_bbbl = sum(d["reserves_bbbl"] for d in data)
    c4.metric("Total Reserves", f"{total_bbbl:,.0f} Bbbl eq.")

    st.markdown("##### Top 15 by Reserves")
    top15 = sorted(data, key=lambda x: x["reserves_bbbl"], reverse=True)[:15]
    colors = ["#1a1a2e" if d["type"] == "Oil" else
              ("#ff6347" if d["type"] == "Gas" else "#f59e0b")
              for d in top15]
    _make_chart(
        [d["name"] for d in top15],
        [d["reserves_bbbl"] for d in top15],
        colors,
        "Estimated Reserves (Billion Barrels equivalent)",
        xlabel="Bbbl eq.",
    )

    legend_html = (
        '<div style="display:flex;gap:1rem;margin-bottom:0.5rem;">'
        '<span style="color:#1a1a2e;font-size:0.8rem;background:#333;padding:2px 6px;'
        'border-radius:4px;">Oil</span>'
        '<span style="color:#ff6347;font-size:0.8rem;">Gas</span>'
        '<span style="color:#f59e0b;font-size:0.8rem;">Oil/Gas</span>'
        '</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)

    st.markdown("##### Oil & Gas Field Map")

    def _oil_color(d):
        t = d["type"]
        if t == "Oil":
            return "#dc2626"
        if t == "Gas":
            return "#ff6347"
        return "#f59e0b"

    def popup_fn(d):
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])} | '
            f'{escape(d["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Reserves: {d["reserves_bbbl"]:,.1f} Bbbl<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=_oil_color, popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "oil_gas_fields.csv", "dl_oil")


def _render_diamond_mines():
    """Mode 5: Diamond Mines."""
    data = DIAMOND_MINES
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Diamond Mines"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Mines Mapped", len(data))
    countries = set(d["country"] for d in data)
    c2.metric("Countries", len(countries))
    total_ct = sum(d["carats_mpy"] for d in data)
    c3.metric("Total Production", f"{total_ct:,.1f} M carats/yr")

    st.markdown("##### Top Producers (Million Carats/Year)")
    top10 = sorted(data, key=lambda x: x["carats_mpy"], reverse=True)[:10]
    _make_chart(
        [d["name"] for d in top10],
        [d["carats_mpy"] for d in top10],
        [RESOURCE_COLORS["diamond"]] * len(top10),
        "Annual Diamond Production (M carats)",
        xlabel="M carats/yr",
    )

    st.markdown("##### Diamond Mine Map")

    def popup_fn(d):
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])} | '
            f'{escape(d["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Production: {d["carats_mpy"]:,.1f} M ct/yr<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=RESOURCE_COLORS["diamond"],
                   popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "diamond_mines.csv", "dl_diamonds")


def _render_coal_regions():
    """Mode 6: Coal Regions."""
    data = COAL_REGIONS
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Coal Regions"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Regions Mapped", len(data))
    active = sum(1 for d in data if d["production_mt"] > 0)
    c2.metric("Active Regions", active)
    total = sum(d["production_mt"] for d in data)
    c3.metric("Total Production", f"{total:,.0f} Mt/yr")
    closed = sum(1 for d in data if d["production_mt"] == 0)
    c4.metric("Closed/Historic", closed)

    st.markdown("##### Production by Region")
    active_data = [d for d in data if d["production_mt"] > 0]
    top_coal = sorted(active_data, key=lambda x: x["production_mt"], reverse=True)[:15]
    _make_chart(
        [d["name"] for d in top_coal],
        [d["production_mt"] for d in top_coal],
        [RESOURCE_COLORS["coal"]] * len(top_coal),
        "Annual Coal Production (Million Tonnes)",
        xlabel="Mt/yr",
    )

    st.markdown("##### Coal Region Map")

    def _coal_color(d):
        if d["production_mt"] == 0:
            return "#5a6580"
        if d["production_mt"] < 50:
            return "#f59e0b"
        if d["production_mt"] < 200:
            return "#f97316"
        return "#ef4444"

    def popup_fn(d):
        status = "Active" if d["production_mt"] > 0 else "Closed/Historic"
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])} | '
            f'{escape(d["type"])} | {status}</span><br/>'
            f'<span style="font-size:0.75rem;">Production: {d["production_mt"]:,} Mt/yr<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=_coal_color, popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "coal_regions.csv", "dl_coal")


def _render_uranium():
    """Mode 7: Uranium & Nuclear Fuel."""
    data = URANIUM_DEPOSITS
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Uranium & Nuclear Fuel"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Mapped", len(data))
    active = sum(1 for d in data if d["production_t"] > 0)
    c2.metric("Active Mines", active)
    total = sum(d["production_t"] for d in data)
    c3.metric("Total Output", f"{total:,.0f} tU/yr")

    st.markdown("##### Production by Mine")
    active_data = sorted([d for d in data if d["production_t"] > 0],
                         key=lambda x: x["production_t"], reverse=True)
    _make_chart(
        [d["name"] for d in active_data],
        [d["production_t"] for d in active_data],
        [RESOURCE_COLORS["uranium"]] * len(active_data),
        "Annual Uranium Production (tonnes U)",
        xlabel="tU/yr",
    )

    st.markdown("##### Uranium Mine Map")

    def popup_fn(d):
        status = "Active" if d["production_t"] > 0 else "Closed/Undeveloped"
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])} | '
            f'{status}</span><br/>'
            f'<span style="font-size:0.75rem;">Production: {d["production_t"]:,} tU/yr<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=RESOURCE_COLORS["uranium"],
                   popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "uranium_deposits.csv", "dl_uranium")


def _render_lithium():
    """Mode 8: Lithium Triangle."""
    data = LITHIUM_DEPOSITS
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Lithium Triangle"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deposits Mapped", len(data))
    brine = sum(1 for d in data if "Brine" in d["type"])
    c2.metric("Brine Deposits", brine)
    hardrock = len(data) - brine
    c3.metric("Hard Rock Deposits", hardrock)
    total_res = sum(d["reserves_kt"] for d in data)
    c4.metric("Total Reserves", f"{total_res:,.0f} kt LCE")

    st.markdown("##### Reserves by Deposit")
    sorted_data = sorted(data, key=lambda x: x["reserves_kt"], reverse=True)[:15]

    def _lith_color(d):
        return "#00bfff" if "Brine" in d["type"] else "#10b981"

    _make_chart(
        [d["name"] for d in sorted_data],
        [d["reserves_kt"] for d in sorted_data],
        [_lith_color(d) for d in sorted_data],
        "Lithium Reserves (Thousand Tonnes LCE)",
        xlabel="kt LCE",
    )

    legend_html = (
        '<div style="display:flex;gap:1rem;margin-bottom:0.5rem;">'
        '<span style="color:#00bfff;font-size:0.8rem;">Brine</span>'
        '<span style="color:#10b981;font-size:0.8rem;">Hard Rock / Other</span>'
        '</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)

    st.markdown("##### Lithium Deposit Map")

    def popup_fn(d):
        return (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])} | '
            f'{escape(d["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Reserves: {d["reserves_kt"]:,} kt LCE<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=lambda d: _lith_color(d),
                   popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "lithium_deposits.csv", "dl_lithium")


def _render_deep_sea():
    """Mode 9: Deep Sea Mining."""
    data = DEEP_SEA_MINING
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Deep Sea Mining"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Mapped", len(data))
    nodules = sum(1 for d in data if "Nodule" in d["resource"])
    c2.metric("Nodule Fields", nodules)
    avg_depth = sum(d["depth_m"] for d in data) / len(data)
    c3.metric("Avg Depth", f"{avg_depth:,.0f} m")

    st.markdown("##### Depth Profile by Site")
    sorted_data = sorted(data, key=lambda x: x["depth_m"], reverse=True)

    def _depth_color(d):
        if d["depth_m"] > 4500:
            return "#1e3a5f"
        if d["depth_m"] > 3000:
            return "#1e90ff"
        return "#00bfff"

    _make_chart(
        [d["name"][:25] for d in sorted_data],
        [d["depth_m"] for d in sorted_data],
        [_depth_color(d) for d in sorted_data],
        "Ocean Depth (meters)",
        xlabel="Depth (m)",
    )

    st.markdown("##### Deep Sea Mining Map")

    def popup_fn(d):
        return (
            f'<div style="max-width:260px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Resource: {escape(d["resource"])}<br/>'
            f'Depth: {d["depth_m"]:,} m<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=RESOURCE_COLORS["deep_sea"],
                   popup_fn=popup_fn, zoom=2,
                   center=(5.0, -140.0))
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(data)
    _show_download(df, "deep_sea_mining.csv", "dl_deep_sea")


def _render_historical():
    """Mode 10: Historical Mining."""
    data = HISTORICAL_MINES
    st.markdown("##### Overview")
    st.markdown(MODE_DESCRIPTIONS["Historical Mining"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Historic Sites", len(data))
    countries = set(d["country"] for d in data)
    c2.metric("Countries", len(countries))
    resources = set(d["resource"].split("/")[0] for d in data)
    c3.metric("Resource Types", len(resources))

    # Resource breakdown chart
    st.markdown("##### Resources Mined Historically")
    res_counts = {}
    for d in data:
        for r in d["resource"].split("/"):
            r = r.strip()
            res_counts[r] = res_counts.get(r, 0) + 1
    sorted_res = sorted(res_counts.items(), key=lambda x: -x[1])
    _make_chart(
        [r[0] for r in sorted_res],
        [r[1] for r in sorted_res],
        [_resource_color(r[0]) for r in sorted_res],
        "Number of Historic Sites by Resource",
        xlabel="Sites",
    )

    st.markdown("##### Historical Mine Map")

    def popup_fn(d):
        return (
            f'<div style="max-width:260px;font-family:sans-serif;">'
            f'<b>{escape(d["name"])}</b><br/>'
            f'<span style="font-size:0.8rem;color:#666;">{escape(d["country"])} | '
            f'Est. {escape(d["era"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Resource: {escape(d["resource"])}<br/>'
            f'{escape(d["note"])}</span></div>'
        )

    m = _build_map(data, "lat", "lon", "name",
                   color=RESOURCE_COLORS["historical"],
                   popup_fn=popup_fn, zoom=2)
    components.html(m._repr_html_(), height=500)

    # Notable sites list
    st.markdown("##### Notable Historic Sites")
    for d in data[:12]:
        st.markdown(
            f'<div style="display:flex;align-items:center;margin-bottom:0.5rem;">'
            f'<div style="width:8px;height:45px;border-radius:4px;'
            f'background:{RESOURCE_COLORS["historical"]};margin-right:0.75rem;'
            f'flex-shrink:0;"></div>'
            f'<div>'
            f'<div style="color:#e8ecf4;font-weight:600;font-size:0.85rem;">'
            f'{escape(d["name"])}'
            f'<span style="color:#8b97b0;font-weight:400;"> ({escape(d["era"])})</span></div>'
            f'<div style="color:#8b97b0;font-size:0.75rem;">'
            f'{escape(d["country"])} | {escape(d["resource"])}</div>'
            f'<div style="color:#5a6580;font-size:0.7rem;">{escape(d["note"])}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    df = pd.DataFrame(data)
    _show_download(df, "historical_mines.csv", "dl_historical")


# ═══════════════════════════════════════════════════════════════
# MODE DISPATCH TABLE
# ═══════════════════════════════════════════════════════════════
_MODE_RENDERERS = {
    "World's Largest Mines": _render_largest_mines,
    "Gold Deposits": _render_gold_deposits,
    "Rare Earth Elements": _render_rare_earth,
    "Oil & Gas Fields": _render_oil_gas,
    "Diamond Mines": _render_diamond_mines,
    "Coal Regions": _render_coal_regions,
    "Uranium & Nuclear Fuel": _render_uranium,
    "Lithium Triangle": _render_lithium,
    "Deep Sea Mining": _render_deep_sea,
    "Historical Mining": _render_historical,
}


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════
def render_mining_maps_tab():
    """Main render function for the Mining & Natural Resources tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header amber">'
        '<h4>Mining & Natural Resources Maps</h4>'
        '<p>Mines, minerals, rare earth, oil fields & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        key="mining_mode",
        help="Choose from 10 curated mining and resource maps",
    )

    st.markdown("---")

    # Dispatch to the selected mode renderer
    renderer = _MODE_RENDERERS.get(mode)
    if renderer:
        renderer()
