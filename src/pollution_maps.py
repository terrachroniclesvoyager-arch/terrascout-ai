# -*- coding: utf-8 -*-
"""
Pollution & Environmental Crisis Maps module for TerraScout AI.
Provides 10 pollution/environmental map types using hardcoded datasets and free APIs.
Maps: Ocean Plastic Gyres, Major Oil Spills, Endangered Species, Deforestation Hotspots,
Nuclear Disaster Zones, Most Polluted Cities, Acid Rain Regions, Plastic Waste Exporters,
E-Waste Dumping, Dead Zones.
"""

import io
import html
import math
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OPEN_METEO_AQ_API = "https://air-quality-api.open-meteo.com/v1/air-quality"

MAP_TYPES = [
    "Ocean Plastic Gyres",
    "Major Oil Spills",
    "Endangered Species",
    "Deforestation Hotspots",
    "Nuclear Disaster Zones",
    "Most Polluted Cities",
    "Acid Rain Regions",
    "Plastic Waste Exporters",
    "E-Waste Dumping",
    "Dead Zones",
]

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "severe": "#ef4444",
    "high": "#f97316",
    "moderate": "#f59e0b",
    "low": "#10b981",
    "info": "#06b6d4",
    "purple": "#8b5cf6",
    "pink": "#ec4899",
}

# ---------------------------------------------------------------------------
# 1. OCEAN PLASTIC GYRES DATA
# ---------------------------------------------------------------------------
OCEAN_GYRES = [
    {
        "name": "Great Pacific Garbage Patch",
        "center_lat": 32.0, "center_lon": -145.0,
        "estimated_mass_tons": 80000,
        "size_km2": 1600000,
        "discovery_year": 1997,
        "description": "Largest accumulation of ocean plastic, between Hawaii and California",
        "color": "#dc2626",
        "polygon": [
            [38.0, -155.0], [38.0, -135.0], [32.0, -130.0],
            [26.0, -135.0], [26.0, -155.0], [32.0, -160.0],
        ],
    },
    {
        "name": "North Atlantic Garbage Patch",
        "center_lat": 30.0, "center_lon": -45.0,
        "estimated_mass_tons": 21000,
        "size_km2": 700000,
        "discovery_year": 1972,
        "description": "Sargasso Sea area concentration of marine debris",
        "color": "#ef4444",
        "polygon": [
            [35.0, -55.0], [35.0, -35.0], [30.0, -30.0],
            [25.0, -35.0], [25.0, -55.0], [30.0, -60.0],
        ],
    },
    {
        "name": "South Pacific Garbage Patch",
        "center_lat": -35.0, "center_lon": -105.0,
        "estimated_mass_tons": 12000,
        "size_km2": 2600000,
        "discovery_year": 2011,
        "description": "Off the coast of Chile and Peru, potentially larger than Great Pacific",
        "color": "#f97316",
        "polygon": [
            [-28.0, -120.0], [-28.0, -90.0], [-35.0, -85.0],
            [-42.0, -90.0], [-42.0, -120.0], [-35.0, -125.0],
        ],
    },
    {
        "name": "South Atlantic Garbage Patch",
        "center_lat": -30.0, "center_lon": -15.0,
        "estimated_mass_tons": 8500,
        "size_km2": 450000,
        "discovery_year": 2009,
        "description": "Between South America and Africa, driven by South Atlantic Gyre",
        "color": "#f59e0b",
        "polygon": [
            [-25.0, -25.0], [-25.0, -5.0], [-30.0, 0.0],
            [-35.0, -5.0], [-35.0, -25.0], [-30.0, -30.0],
        ],
    },
    {
        "name": "Indian Ocean Garbage Patch",
        "center_lat": -25.0, "center_lon": 75.0,
        "estimated_mass_tons": 15000,
        "size_km2": 900000,
        "discovery_year": 2010,
        "description": "Indian Ocean gyre concentration, significant microplastic density",
        "color": "#8b5cf6",
        "polygon": [
            [-18.0, 60.0], [-18.0, 90.0], [-25.0, 95.0],
            [-32.0, 90.0], [-32.0, 60.0], [-25.0, 55.0],
        ],
    },
]

# ---------------------------------------------------------------------------
# 2. MAJOR OIL SPILLS DATA (30+)
# ---------------------------------------------------------------------------
OIL_SPILLS = [
    {"name": "Deepwater Horizon", "lat": 28.74, "lon": -88.39, "year": 2010, "volume_barrels": 4900000, "affected_area_km2": 149000, "country": "USA (Gulf of Mexico)", "cause": "Blowout / explosion"},
    {"name": "Exxon Valdez", "lat": 60.84, "lon": -146.88, "year": 1989, "volume_barrels": 257000, "affected_area_km2": 28000, "country": "USA (Alaska)", "cause": "Grounding"},
    {"name": "Prestige", "lat": 42.17, "lon": -12.03, "year": 2002, "volume_barrels": 461000, "affected_area_km2": 30000, "country": "Spain", "cause": "Structural failure"},
    {"name": "Amoco Cadiz", "lat": 48.59, "lon": -4.77, "year": 1978, "volume_barrels": 1604500, "affected_area_km2": 18000, "country": "France", "cause": "Steering failure / grounding"},
    {"name": "Torrey Canyon", "lat": 49.92, "lon": -6.13, "year": 1967, "volume_barrels": 860000, "affected_area_km2": 19000, "country": "UK", "cause": "Grounding on reef"},
    {"name": "Ixtoc I", "lat": 19.41, "lon": -92.33, "year": 1979, "volume_barrels": 3329000, "affected_area_km2": 280000, "country": "Mexico", "cause": "Blowout"},
    {"name": "Gulf War Oil Spill", "lat": 28.93, "lon": 48.81, "year": 1991, "volume_barrels": 8000000, "affected_area_km2": 100000, "country": "Kuwait / Persian Gulf", "cause": "Deliberate release (war)"},
    {"name": "Atlantic Empress", "lat": 11.17, "lon": -61.70, "year": 1979, "volume_barrels": 2105000, "affected_area_km2": 12000, "country": "Trinidad & Tobago", "cause": "Collision"},
    {"name": "ABT Summer", "lat": -15.0, "lon": 28.0, "year": 1991, "volume_barrels": 1907000, "affected_area_km2": 8000, "country": "Angola (offshore)", "cause": "Explosion"},
    {"name": "Castillo de Bellver", "lat": -33.85, "lon": 17.95, "year": 1983, "volume_barrels": 1852000, "affected_area_km2": 15000, "country": "South Africa", "cause": "Fire / sinking"},
    {"name": "Nowruz Oil Field", "lat": 29.88, "lon": 49.47, "year": 1983, "volume_barrels": 1500000, "affected_area_km2": 35000, "country": "Iran / Persian Gulf", "cause": "War damage / tanker collision"},
    {"name": "Sea Star", "lat": 25.45, "lon": 55.45, "year": 1972, "volume_barrels": 840000, "affected_area_km2": 5000, "country": "Gulf of Oman", "cause": "Collision"},
    {"name": "Odyssey", "lat": 48.0, "lon": -32.0, "year": 1988, "volume_barrels": 1020000, "affected_area_km2": 9000, "country": "North Atlantic", "cause": "Break-up / explosion"},
    {"name": "Haven", "lat": 44.35, "lon": 8.85, "year": 1991, "volume_barrels": 1020000, "affected_area_km2": 12000, "country": "Italy (Genoa)", "cause": "Explosion"},
    {"name": "Braer", "lat": 59.87, "lon": -1.33, "year": 1993, "volume_barrels": 595000, "affected_area_km2": 4000, "country": "UK (Shetland)", "cause": "Grounding"},
    {"name": "Aegean Sea (tanker)", "lat": 43.37, "lon": -8.40, "year": 1992, "volume_barrels": 516000, "affected_area_km2": 7000, "country": "Spain (La Coruna)", "cause": "Grounding / storm"},
    {"name": "Erika", "lat": 47.30, "lon": -3.80, "year": 1999, "volume_barrels": 140000, "affected_area_km2": 8000, "country": "France (Brittany)", "cause": "Structural failure"},
    {"name": "Sea Empress", "lat": 51.68, "lon": -5.05, "year": 1996, "volume_barrels": 506000, "affected_area_km2": 5200, "country": "UK (Wales)", "cause": "Grounding"},
    {"name": "Tasman Spirit", "lat": 24.82, "lon": 66.99, "year": 2003, "volume_barrels": 267000, "affected_area_km2": 3500, "country": "Pakistan (Karachi)", "cause": "Grounding"},
    {"name": "Sanchi", "lat": 30.72, "lon": 124.95, "year": 2018, "volume_barrels": 750000, "affected_area_km2": 10000, "country": "East China Sea", "cause": "Collision / explosion"},
    {"name": "MV Wakashio", "lat": -20.45, "lon": 57.75, "year": 2020, "volume_barrels": 7000, "affected_area_km2": 2000, "country": "Mauritius", "cause": "Grounding on coral reef"},
    {"name": "Hebei Spirit", "lat": 36.86, "lon": 126.04, "year": 2007, "volume_barrels": 73000, "affected_area_km2": 4500, "country": "South Korea", "cause": "Collision with barge"},
    {"name": "MV Solomon Trader", "lat": -11.58, "lon": 160.95, "year": 2019, "volume_barrels": 5000, "affected_area_km2": 800, "country": "Solomon Islands", "cause": "Grounding near UNESCO site"},
    {"name": "Montara", "lat": -12.68, "lon": 124.53, "year": 2009, "volume_barrels": 28000, "affected_area_km2": 90000, "country": "Australia (Timor Sea)", "cause": "Blowout"},
    {"name": "Rena", "lat": -37.55, "lon": 176.44, "year": 2011, "volume_barrels": 2500, "affected_area_km2": 1200, "country": "New Zealand", "cause": "Grounding on reef"},
    {"name": "Penglai 19-3", "lat": 38.36, "lon": 120.35, "year": 2011, "volume_barrels": 5000, "affected_area_km2": 6200, "country": "China (Bohai Bay)", "cause": "Well leak"},
    {"name": "Argo Merchant", "lat": 41.06, "lon": -69.50, "year": 1976, "volume_barrels": 183000, "affected_area_km2": 4000, "country": "USA (Nantucket)", "cause": "Grounding"},
    {"name": "Fergana Valley", "lat": 40.4, "lon": 71.8, "year": 1992, "volume_barrels": 2090000, "affected_area_km2": 2000, "country": "Uzbekistan", "cause": "Well blowout"},
    {"name": "Kolva River", "lat": 64.0, "lon": 56.0, "year": 1994, "volume_barrels": 840000, "affected_area_km2": 18600, "country": "Russia", "cause": "Pipeline rupture"},
    {"name": "Niger Delta (chronic)", "lat": 5.0, "lon": 6.5, "year": 2010, "volume_barrels": 260000, "affected_area_km2": 70000, "country": "Nigeria", "cause": "Chronic pipeline leaks / sabotage"},
    {"name": "Taylor Energy (chronic)", "lat": 28.94, "lon": -88.97, "year": 2004, "volume_barrels": 153000, "affected_area_km2": 25000, "country": "USA (Gulf of Mexico)", "cause": "Hurricane Ivan / platform collapse"},
    {"name": "Kulluk (Shell)", "lat": 57.42, "lon": -154.49, "year": 2012, "volume_barrels": 272, "affected_area_km2": 50, "country": "USA (Alaska)", "cause": "Rig grounding"},
]

# ---------------------------------------------------------------------------
# 3. ENDANGERED SPECIES DATA (40+)
# ---------------------------------------------------------------------------
ENDANGERED_SPECIES = [
    {"name": "Sumatran Rhino", "lat": -2.5, "lon": 104.5, "population": 80, "habitat": "Tropical rainforest", "iucn": "Critically Endangered", "icon": "rhino", "color": "#dc2626"},
    {"name": "Amur Leopard", "lat": 43.5, "lon": 132.5, "population": 120, "habitat": "Temperate forest", "iucn": "Critically Endangered", "icon": "cat", "color": "#dc2626"},
    {"name": "Vaquita", "lat": 30.8, "lon": -114.5, "population": 10, "habitat": "Shallow coastal waters", "iucn": "Critically Endangered", "icon": "fish", "color": "#ff0000"},
    {"name": "Mountain Gorilla", "lat": -1.5, "lon": 29.5, "population": 1063, "habitat": "Montane forest", "iucn": "Endangered", "icon": "gorilla", "color": "#f97316"},
    {"name": "Hawksbill Turtle", "lat": 15.0, "lon": -61.0, "population": 23000, "habitat": "Coral reefs", "iucn": "Critically Endangered", "icon": "turtle", "color": "#dc2626"},
    {"name": "Javan Rhino", "lat": -6.75, "lon": 105.4, "population": 76, "habitat": "Tropical lowland forest", "iucn": "Critically Endangered", "icon": "rhino", "color": "#dc2626"},
    {"name": "Cross River Gorilla", "lat": 6.3, "lon": 9.3, "population": 300, "habitat": "Montane/lowland forest", "iucn": "Critically Endangered", "icon": "gorilla", "color": "#dc2626"},
    {"name": "Sumatran Orangutan", "lat": 3.5, "lon": 98.0, "population": 14000, "habitat": "Tropical rainforest", "iucn": "Critically Endangered", "icon": "primate", "color": "#dc2626"},
    {"name": "Sumatran Tiger", "lat": -0.5, "lon": 101.5, "population": 400, "habitat": "Tropical forest", "iucn": "Critically Endangered", "icon": "cat", "color": "#dc2626"},
    {"name": "South China Tiger", "lat": 27.0, "lon": 113.0, "population": 0, "habitat": "Montane forest (functionally extinct wild)", "iucn": "Critically Endangered", "icon": "cat", "color": "#ff0000"},
    {"name": "Yangtze Finless Porpoise", "lat": 30.5, "lon": 116.0, "population": 1012, "habitat": "Freshwater river", "iucn": "Critically Endangered", "icon": "fish", "color": "#dc2626"},
    {"name": "Saola", "lat": 18.0, "lon": 105.5, "population": 100, "habitat": "Annamite Mountains forest", "iucn": "Critically Endangered", "icon": "deer", "color": "#dc2626"},
    {"name": "Philippine Eagle", "lat": 7.5, "lon": 126.0, "population": 800, "habitat": "Dipterocarp forest", "iucn": "Critically Endangered", "icon": "bird", "color": "#dc2626"},
    {"name": "Kakapo", "lat": -46.0, "lon": 166.7, "population": 252, "habitat": "Island scrubland", "iucn": "Critically Endangered", "icon": "bird", "color": "#dc2626"},
    {"name": "California Condor", "lat": 35.5, "lon": -118.5, "population": 561, "habitat": "Mountainous terrain", "iucn": "Critically Endangered", "icon": "bird", "color": "#dc2626"},
    {"name": "Black-footed Ferret", "lat": 43.5, "lon": -104.0, "population": 370, "habitat": "Prairie grassland", "iucn": "Endangered", "icon": "mammal", "color": "#f97316"},
    {"name": "Pangolin (Sunda)", "lat": 3.0, "lon": 110.0, "population": 50000, "habitat": "Tropical forest", "iucn": "Critically Endangered", "icon": "mammal", "color": "#dc2626"},
    {"name": "Snow Leopard", "lat": 37.0, "lon": 75.0, "population": 4000, "habitat": "Mountain ranges", "iucn": "Vulnerable", "icon": "cat", "color": "#f59e0b"},
    {"name": "Giant Panda", "lat": 30.8, "lon": 103.5, "population": 1864, "habitat": "Bamboo forest", "iucn": "Vulnerable", "icon": "mammal", "color": "#f59e0b"},
    {"name": "Red Panda", "lat": 28.0, "lon": 85.0, "population": 10000, "habitat": "Temperate montane forest", "iucn": "Endangered", "icon": "mammal", "color": "#f97316"},
    {"name": "Orangutan (Bornean)", "lat": 1.0, "lon": 113.0, "population": 104700, "habitat": "Tropical rainforest", "iucn": "Critically Endangered", "icon": "primate", "color": "#dc2626"},
    {"name": "Blue Whale", "lat": -55.0, "lon": -70.0, "population": 15000, "habitat": "Open ocean", "iucn": "Endangered", "icon": "whale", "color": "#f97316"},
    {"name": "North Atlantic Right Whale", "lat": 42.0, "lon": -67.0, "population": 350, "habitat": "Coastal waters", "iucn": "Critically Endangered", "icon": "whale", "color": "#dc2626"},
    {"name": "Leatherback Sea Turtle", "lat": 10.0, "lon": -60.0, "population": 34000, "habitat": "Open ocean / nesting beaches", "iucn": "Vulnerable", "icon": "turtle", "color": "#f59e0b"},
    {"name": "Gharial", "lat": 27.5, "lon": 84.0, "population": 650, "habitat": "Freshwater rivers", "iucn": "Critically Endangered", "icon": "reptile", "color": "#dc2626"},
    {"name": "Addax", "lat": 20.0, "lon": 12.0, "population": 90, "habitat": "Sahara desert", "iucn": "Critically Endangered", "icon": "deer", "color": "#dc2626"},
    {"name": "Iberian Lynx", "lat": 37.9, "lon": -4.5, "population": 1668, "habitat": "Mediterranean scrubland", "iucn": "Endangered", "icon": "cat", "color": "#f97316"},
    {"name": "Ethiopian Wolf", "lat": 7.0, "lon": 39.5, "population": 500, "habitat": "Afroalpine highlands", "iucn": "Endangered", "icon": "mammal", "color": "#f97316"},
    {"name": "Axolotl", "lat": 19.3, "lon": -99.1, "population": 1000, "habitat": "Lake Xochimilco canals", "iucn": "Critically Endangered", "icon": "amphibian", "color": "#dc2626"},
    {"name": "Lemur (Greater Bamboo)", "lat": -21.0, "lon": 47.5, "population": 500, "habitat": "Bamboo forest", "iucn": "Critically Endangered", "icon": "primate", "color": "#dc2626"},
    {"name": "Tapanuli Orangutan", "lat": 1.5, "lon": 99.2, "population": 800, "habitat": "Tropical montane forest", "iucn": "Critically Endangered", "icon": "primate", "color": "#dc2626"},
    {"name": "Spix's Macaw", "lat": -9.5, "lon": -39.5, "population": 0, "habitat": "Caatinga scrubland (extinct in wild)", "iucn": "Extinct in Wild", "icon": "bird", "color": "#ff0000"},
    {"name": "Sumatran Elephant", "lat": 0.5, "lon": 102.5, "population": 2400, "habitat": "Tropical forest", "iucn": "Critically Endangered", "icon": "elephant", "color": "#dc2626"},
    {"name": "African Forest Elephant", "lat": 0.0, "lon": 18.0, "population": 100000, "habitat": "Tropical forest", "iucn": "Critically Endangered", "icon": "elephant", "color": "#dc2626"},
    {"name": "Cheetah (Asiatic)", "lat": 33.5, "lon": 56.0, "population": 12, "habitat": "Semi-desert grassland", "iucn": "Critically Endangered", "icon": "cat", "color": "#ff0000"},
    {"name": "Northern White Rhino", "lat": 0.0, "lon": 36.9, "population": 2, "habitat": "Grassland savanna (functionally extinct)", "iucn": "Critically Endangered", "icon": "rhino", "color": "#ff0000"},
    {"name": "Pygmy Three-toed Sloth", "lat": 9.25, "lon": -82.0, "population": 100, "habitat": "Mangrove island", "iucn": "Critically Endangered", "icon": "mammal", "color": "#dc2626"},
    {"name": "Hainan Gibbon", "lat": 19.0, "lon": 109.5, "population": 37, "habitat": "Tropical rainforest", "iucn": "Critically Endangered", "icon": "primate", "color": "#ff0000"},
    {"name": "Helmeted Hornbill", "lat": 2.0, "lon": 111.0, "population": 2500, "habitat": "Tropical forest canopy", "iucn": "Critically Endangered", "icon": "bird", "color": "#dc2626"},
    {"name": "Irrawaddy Dolphin", "lat": 16.5, "lon": 96.0, "population": 92, "habitat": "Freshwater rivers / coastal", "iucn": "Endangered", "icon": "fish", "color": "#f97316"},
    {"name": "Polar Bear", "lat": 75.0, "lon": -40.0, "population": 26000, "habitat": "Arctic sea ice", "iucn": "Vulnerable", "icon": "mammal", "color": "#f59e0b"},
    {"name": "Komodo Dragon", "lat": -8.55, "lon": 119.5, "population": 3458, "habitat": "Tropical savanna island", "iucn": "Endangered", "icon": "reptile", "color": "#f97316"},
]

# ---------------------------------------------------------------------------
# 4. DEFORESTATION HOTSPOTS DATA (15+)
# ---------------------------------------------------------------------------
DEFORESTATION_HOTSPOTS = [
    {"name": "Amazon Arc of Deforestation", "annual_loss_km2": 10000, "primary_cause": "Cattle ranching, soy farming", "color": "#dc2626",
     "polygon": [[-2.0, -56.0], [-3.0, -52.0], [-6.0, -48.0], [-10.0, -48.0], [-14.0, -50.0], [-14.0, -56.0], [-10.0, -58.0], [-6.0, -58.0]]},
    {"name": "Borneo Deforestation", "annual_loss_km2": 5000, "primary_cause": "Palm oil plantations, logging", "color": "#ef4444",
     "polygon": [[4.0, 108.0], [4.0, 117.0], [1.0, 119.0], [-2.0, 117.0], [-3.5, 112.0], [-2.0, 108.0], [1.0, 107.0]]},
    {"name": "Congo Basin", "annual_loss_km2": 3000, "primary_cause": "Slash-and-burn, charcoal, mining", "color": "#f97316",
     "polygon": [[-1.0, 16.0], [-1.0, 28.0], [-5.0, 29.0], [-5.0, 16.0]]},
    {"name": "Madagascar Eastern Forests", "annual_loss_km2": 1500, "primary_cause": "Slash-and-burn (tavy), logging", "color": "#ef4444",
     "polygon": [[-14.0, 49.0], [-14.0, 50.5], [-22.0, 48.5], [-22.0, 46.5]]},
    {"name": "Sumatra Forests", "annual_loss_km2": 4000, "primary_cause": "Palm oil, pulp & paper", "color": "#dc2626",
     "polygon": [[3.0, 97.0], [3.0, 105.0], [-2.0, 105.0], [-5.0, 104.0], [-5.5, 101.0], [-2.0, 98.0]]},
    {"name": "Gran Chaco", "annual_loss_km2": 3500, "primary_cause": "Soy and cattle expansion", "color": "#f97316",
     "polygon": [[-19.0, -63.0], [-19.0, -58.0], [-24.0, -58.0], [-27.0, -60.0], [-27.0, -63.0]]},
    {"name": "Cerrado (Brazil)", "annual_loss_km2": 6000, "primary_cause": "Agriculture expansion, cattle", "color": "#ef4444",
     "polygon": [[-8.0, -50.0], [-8.0, -43.0], [-14.0, -43.0], [-18.0, -46.0], [-18.0, -52.0], [-12.0, -52.0]]},
    {"name": "Mekong Region", "annual_loss_km2": 2500, "primary_cause": "Rubber, cassava, infrastructure", "color": "#f97316",
     "polygon": [[18.0, 100.0], [18.0, 108.0], [12.0, 108.0], [12.0, 100.0]]},
    {"name": "West Africa (Guinea Forests)", "annual_loss_km2": 2000, "primary_cause": "Cocoa farming, mining, logging", "color": "#f97316",
     "polygon": [[8.0, -10.0], [8.0, -2.0], [5.0, -2.0], [5.0, -10.0]]},
    {"name": "Papua New Guinea", "annual_loss_km2": 1400, "primary_cause": "Logging, palm oil", "color": "#f59e0b",
     "polygon": [[-3.0, 141.0], [-3.0, 150.0], [-8.0, 150.0], [-8.0, 141.0]]},
    {"name": "Central America (Honduras/Guatemala)", "annual_loss_km2": 1200, "primary_cause": "Cattle ranching, palm oil", "color": "#f59e0b",
     "polygon": [[17.0, -91.0], [17.0, -84.0], [13.0, -84.0], [13.0, -91.0]]},
    {"name": "Myanmar Forests", "annual_loss_km2": 1500, "primary_cause": "Agriculture, logging, mining", "color": "#f59e0b",
     "polygon": [[22.0, 95.0], [22.0, 100.0], [16.0, 100.0], [16.0, 95.0]]},
    {"name": "Miombo Woodlands (Tanzania)", "annual_loss_km2": 2200, "primary_cause": "Charcoal, agriculture", "color": "#f97316",
     "polygon": [[-5.0, 29.0], [-5.0, 38.0], [-10.0, 38.0], [-10.0, 29.0]]},
    {"name": "Atlantic Forest (Brazil)", "annual_loss_km2": 800, "primary_cause": "Urban expansion, agriculture (93% lost)", "color": "#ef4444",
     "polygon": [[-15.0, -42.0], [-15.0, -39.0], [-24.0, -45.0], [-24.0, -48.0]]},
    {"name": "Chocó-Darién (Colombia)", "annual_loss_km2": 1000, "primary_cause": "Coca, mining, cattle", "color": "#f97316",
     "polygon": [[7.0, -78.0], [7.0, -76.0], [3.0, -76.0], [3.0, -78.0]]},
    {"name": "Russian Far East Forests", "annual_loss_km2": 1800, "primary_cause": "Logging (legal & illegal)", "color": "#f59e0b",
     "polygon": [[48.0, 130.0], [48.0, 140.0], [42.0, 140.0], [42.0, 130.0]]},
]

# ---------------------------------------------------------------------------
# 5. NUCLEAR DISASTER ZONES DATA
# ---------------------------------------------------------------------------
NUCLEAR_DISASTERS = [
    {"name": "Chernobyl", "lat": 51.39, "lon": 30.10, "year": 1986, "ines_level": 7, "exclusion_radius_km": 30, "country": "Ukraine (USSR)", "radiation_peak": "300 Sv/hr at reactor", "deaths": "31 direct, est. 4000-93000 total", "status": "New Safe Confinement since 2016", "color": "#dc2626"},
    {"name": "Fukushima Daiichi", "lat": 37.42, "lon": 141.03, "year": 2011, "ines_level": 7, "exclusion_radius_km": 20, "country": "Japan", "radiation_peak": "530 Sv/hr (Unit 2)", "deaths": "1 direct (cancer), 2313 evacuation deaths", "status": "Decommissioning in progress", "color": "#dc2626"},
    {"name": "Three Mile Island", "lat": 40.15, "lon": -76.73, "year": 1979, "ines_level": 5, "exclusion_radius_km": 8, "country": "USA (Pennsylvania)", "radiation_peak": "Low release, partial meltdown", "deaths": "0 direct", "status": "Unit 2 permanently closed", "color": "#f97316"},
    {"name": "Kyshtym / Mayak", "lat": 55.71, "lon": 60.85, "year": 1957, "ines_level": 6, "exclusion_radius_km": 25, "country": "Russia (USSR)", "radiation_peak": "74 PBq released", "deaths": "Est. 200+ short-term, 8000+ exposed", "status": "Contaminated area remains", "color": "#ef4444"},
    {"name": "Windscale (Sellafield)", "lat": 54.42, "lon": -3.50, "year": 1957, "ines_level": 5, "exclusion_radius_km": 10, "country": "UK", "radiation_peak": "22 TBq I-131 released", "deaths": "Est. 240 cancer cases", "status": "Decommissioned, remediation ongoing", "color": "#f97316"},
    {"name": "Goiânia Incident", "lat": -16.68, "lon": -49.26, "year": 1987, "ines_level": 5, "exclusion_radius_km": 2, "country": "Brazil", "radiation_peak": "Cs-137 source: 50.9 TBq", "deaths": "4 direct, 249 contaminated", "status": "Cleaned up, memorial site", "color": "#f97316"},
    {"name": "Tokaimura", "lat": 36.47, "lon": 140.56, "year": 1999, "ines_level": 4, "exclusion_radius_km": 5, "country": "Japan", "radiation_peak": "Criticality event, neutron burst", "deaths": "2 direct", "status": "Facility closed", "color": "#f59e0b"},
    {"name": "SL-1 Reactor", "lat": 43.52, "lon": -112.83, "year": 1961, "ines_level": 4, "exclusion_radius_km": 3, "country": "USA (Idaho)", "radiation_peak": "Steam explosion / meltdown", "deaths": "3 direct", "status": "Dismantled and buried", "color": "#f59e0b"},
    {"name": "Saint-Laurent Nuclear", "lat": 47.72, "lon": 1.58, "year": 1980, "ines_level": 4, "exclusion_radius_km": 2, "country": "France", "radiation_peak": "Partial fuel melt, limited release", "deaths": "0", "status": "Repaired, units later closed", "color": "#f59e0b"},
    {"name": "Chalk River", "lat": 46.05, "lon": -77.36, "year": 1952, "ines_level": 5, "exclusion_radius_km": 5, "country": "Canada", "radiation_peak": "NRX reactor partial meltdown", "deaths": "0 direct", "status": "Cleaned up (J. Carter assisted)", "color": "#f97316"},
    {"name": "Lucens Reactor", "lat": 46.69, "lon": 6.84, "year": 1969, "ines_level": 4, "exclusion_radius_km": 1, "country": "Switzerland", "radiation_peak": "Partial meltdown underground", "deaths": "0", "status": "Sealed underground", "color": "#f59e0b"},
    {"name": "Semipalatinsk Test Site", "lat": 50.07, "lon": 78.43, "year": 1949, "ines_level": 0, "exclusion_radius_km": 50, "country": "Kazakhstan (USSR)", "radiation_peak": "456 nuclear tests", "deaths": "Est. 200000 affected", "status": "Closed 1991, contamination remains", "color": "#dc2626"},
    {"name": "Hanford Site", "lat": 46.55, "lon": -119.49, "year": 1944, "ines_level": 0, "exclusion_radius_km": 30, "country": "USA (Washington)", "radiation_peak": "Plutonium production, massive contamination", "deaths": "Chronic exposure, thyroid cancers", "status": "Largest cleanup project in US", "color": "#ef4444"},
    {"name": "Maralinga Test Site", "lat": -30.16, "lon": 131.58, "year": 1956, "ines_level": 0, "exclusion_radius_km": 20, "country": "Australia", "radiation_peak": "British nuclear tests", "deaths": "Indigenous population affected", "status": "Partially remediated", "color": "#f97316"},
    {"name": "Andreeva Bay", "lat": 69.48, "lon": 32.37, "year": 1982, "ines_level": 3, "exclusion_radius_km": 5, "country": "Russia (Murmansk)", "radiation_peak": "Nuclear submarine waste facility leak", "deaths": "Unknown", "status": "Remediation with international help", "color": "#f59e0b"},
]

# ---------------------------------------------------------------------------
# 6. MOST POLLUTED CITIES DATA (30+)
# ---------------------------------------------------------------------------
POLLUTED_CITIES = [
    {"name": "Delhi", "lat": 28.61, "lon": 77.21, "country": "India", "avg_pm25": 110, "rank": 1},
    {"name": "Lahore", "lat": 31.55, "lon": 74.35, "country": "Pakistan", "avg_pm25": 97, "rank": 2},
    {"name": "Dhaka", "lat": 23.81, "lon": 90.41, "country": "Bangladesh", "avg_pm25": 89, "rank": 3},
    {"name": "Hotan", "lat": 37.11, "lon": 79.93, "country": "China", "avg_pm25": 104, "rank": 4},
    {"name": "Ghaziabad", "lat": 28.67, "lon": 77.42, "country": "India", "avg_pm25": 106, "rank": 5},
    {"name": "Faisalabad", "lat": 31.42, "lon": 73.08, "country": "Pakistan", "avg_pm25": 94, "rank": 6},
    {"name": "Peshawar", "lat": 34.01, "lon": 71.58, "country": "Pakistan", "avg_pm25": 84, "rank": 7},
    {"name": "N'Djamena", "lat": 12.13, "lon": 15.06, "country": "Chad", "avg_pm25": 82, "rank": 8},
    {"name": "Muzaffarpur", "lat": 26.12, "lon": 85.39, "country": "India", "avg_pm25": 95, "rank": 9},
    {"name": "Patna", "lat": 25.60, "lon": 85.10, "country": "India", "avg_pm25": 90, "rank": 10},
    {"name": "Lucknow", "lat": 26.85, "lon": 80.95, "country": "India", "avg_pm25": 86, "rank": 11},
    {"name": "Kolkata", "lat": 22.57, "lon": 88.36, "country": "India", "avg_pm25": 84, "rank": 12},
    {"name": "Noida", "lat": 28.57, "lon": 77.32, "country": "India", "avg_pm25": 102, "rank": 13},
    {"name": "Kanpur", "lat": 26.45, "lon": 80.35, "country": "India", "avg_pm25": 88, "rank": 14},
    {"name": "Bamako", "lat": 12.64, "lon": -8.00, "country": "Mali", "avg_pm25": 80, "rank": 15},
    {"name": "Baghdad", "lat": 33.31, "lon": 44.37, "country": "Iraq", "avg_pm25": 72, "rank": 16},
    {"name": "Cairo", "lat": 30.04, "lon": 31.24, "country": "Egypt", "avg_pm25": 76, "rank": 17},
    {"name": "Ulaanbaatar", "lat": 47.92, "lon": 106.91, "country": "Mongolia", "avg_pm25": 75, "rank": 18},
    {"name": "Hanoi", "lat": 21.03, "lon": 105.85, "country": "Vietnam", "avg_pm25": 68, "rank": 19},
    {"name": "Jakarta", "lat": -6.21, "lon": 106.85, "country": "Indonesia", "avg_pm25": 65, "rank": 20},
    {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "country": "India", "avg_pm25": 63, "rank": 21},
    {"name": "Accra", "lat": 5.56, "lon": -0.20, "country": "Ghana", "avg_pm25": 62, "rank": 22},
    {"name": "Kampala", "lat": 0.35, "lon": 32.58, "country": "Uganda", "avg_pm25": 60, "rank": 23},
    {"name": "Karachi", "lat": 24.86, "lon": 67.01, "country": "Pakistan", "avg_pm25": 70, "rank": 24},
    {"name": "Chengdu", "lat": 30.57, "lon": 104.07, "country": "China", "avg_pm25": 55, "rank": 25},
    {"name": "Beijing", "lat": 39.90, "lon": 116.41, "country": "China", "avg_pm25": 53, "rank": 26},
    {"name": "Lima", "lat": -12.05, "lon": -77.04, "country": "Peru", "avg_pm25": 50, "rank": 27},
    {"name": "Wuhan", "lat": 30.59, "lon": 114.31, "country": "China", "avg_pm25": 48, "rank": 28},
    {"name": "Kathmandu", "lat": 27.72, "lon": 85.32, "country": "Nepal", "avg_pm25": 72, "rank": 29},
    {"name": "Bishkek", "lat": 42.87, "lon": 74.59, "country": "Kyrgyzstan", "avg_pm25": 68, "rank": 30},
    {"name": "Rawalpindi", "lat": 33.60, "lon": 73.04, "country": "Pakistan", "avg_pm25": 85, "rank": 31},
    {"name": "Varanasi", "lat": 25.32, "lon": 83.01, "country": "India", "avg_pm25": 92, "rank": 32},
]

# ---------------------------------------------------------------------------
# 7. ACID RAIN REGIONS DATA
# ---------------------------------------------------------------------------
ACID_RAIN_REGIONS = [
    {"name": "NE United States / SE Canada", "avg_ph": 4.2, "primary_pollutant": "SO2 and NOx from coal plants", "severity": "high", "color": "#ef4444",
     "polygon": [[47.0, -80.0], [47.0, -67.0], [40.0, -67.0], [37.0, -75.0], [37.0, -80.0]]},
    {"name": "Central Europe (Black Triangle)", "avg_ph": 4.0, "primary_pollutant": "SO2 from brown coal (lignite)", "severity": "critical", "color": "#dc2626",
     "polygon": [[52.0, 12.0], [52.0, 18.0], [49.0, 18.0], [49.0, 12.0]]},
    {"name": "Southern China", "avg_ph": 3.8, "primary_pollutant": "SO2 from coal power and industry", "severity": "critical", "color": "#dc2626",
     "polygon": [[30.0, 103.0], [30.0, 117.0], [22.0, 117.0], [22.0, 103.0]]},
    {"name": "Scandinavian Lakes", "avg_ph": 4.5, "primary_pollutant": "Transboundary SO2 from UK/Europe", "severity": "moderate", "color": "#f97316",
     "polygon": [[62.0, 5.0], [62.0, 18.0], [57.0, 18.0], [57.0, 5.0]]},
    {"name": "Western Japan", "avg_ph": 4.6, "primary_pollutant": "Transboundary from China, domestic", "severity": "moderate", "color": "#f97316",
     "polygon": [[36.0, 130.0], [36.0, 137.0], [32.0, 137.0], [32.0, 130.0]]},
    {"name": "Indian Industrial Belt", "avg_ph": 4.3, "primary_pollutant": "SO2 from coal power plants", "severity": "high", "color": "#ef4444",
     "polygon": [[28.0, 77.0], [28.0, 88.0], [22.0, 88.0], [22.0, 77.0]]},
    {"name": "Russian Ural Region", "avg_ph": 4.4, "primary_pollutant": "SO2 from smelters (Norilsk area)", "severity": "high", "color": "#ef4444",
     "polygon": [[62.0, 55.0], [62.0, 65.0], [54.0, 65.0], [54.0, 55.0]]},
    {"name": "Southeast Brazil", "avg_ph": 4.7, "primary_pollutant": "NOx from vehicles, industry", "severity": "moderate", "color": "#f97316",
     "polygon": [[-20.0, -48.0], [-20.0, -42.0], [-25.0, -42.0], [-25.0, -48.0]]},
    {"name": "South Korea", "avg_ph": 4.5, "primary_pollutant": "SO2 and NOx industrial and transboundary", "severity": "moderate", "color": "#f97316",
     "polygon": [[38.0, 126.0], [38.0, 130.0], [34.0, 130.0], [34.0, 126.0]]},
    {"name": "UK Pennines/Lake District", "avg_ph": 4.3, "primary_pollutant": "Historic SO2 from coal (improving)", "severity": "moderate", "color": "#f97316",
     "polygon": [[55.0, -3.5], [55.0, -1.0], [53.0, -1.0], [53.0, -3.5]]},
]

# ---------------------------------------------------------------------------
# 8. PLASTIC WASTE EXPORTERS DATA
# ---------------------------------------------------------------------------
PLASTIC_EXPORTERS = [
    {"from_country": "United States", "from_lat": 38.0, "from_lon": -97.0, "to_country": "Malaysia", "to_lat": 4.2, "to_lon": 101.9, "volume_tons_yr": 157000, "color": "#dc2626"},
    {"from_country": "United States", "from_lat": 38.0, "from_lon": -97.0, "to_country": "Vietnam", "to_lat": 14.1, "to_lon": 108.3, "volume_tons_yr": 83000, "color": "#dc2626"},
    {"from_country": "United States", "from_lat": 38.0, "from_lon": -97.0, "to_country": "Indonesia", "to_lat": -0.8, "to_lon": 113.9, "volume_tons_yr": 56000, "color": "#dc2626"},
    {"from_country": "Germany", "from_lat": 51.2, "from_lon": 10.5, "to_country": "Malaysia", "to_lat": 4.2, "to_lon": 101.9, "volume_tons_yr": 130000, "color": "#ef4444"},
    {"from_country": "Germany", "from_lat": 51.2, "from_lon": 10.5, "to_country": "Turkey", "to_lat": 39.0, "to_lon": 35.2, "volume_tons_yr": 95000, "color": "#ef4444"},
    {"from_country": "UK", "from_lat": 55.4, "from_lon": -3.4, "to_country": "Turkey", "to_lat": 39.0, "to_lon": 35.2, "volume_tons_yr": 210000, "color": "#f97316"},
    {"from_country": "UK", "from_lat": 55.4, "from_lon": -3.4, "to_country": "Malaysia", "to_lat": 4.2, "to_lon": 101.9, "volume_tons_yr": 72000, "color": "#f97316"},
    {"from_country": "Japan", "from_lat": 36.2, "from_lon": 138.3, "to_country": "Malaysia", "to_lat": 4.2, "to_lon": 101.9, "volume_tons_yr": 120000, "color": "#8b5cf6"},
    {"from_country": "Japan", "from_lat": 36.2, "from_lon": 138.3, "to_country": "Thailand", "to_lat": 15.9, "to_lon": 100.9, "volume_tons_yr": 82000, "color": "#8b5cf6"},
    {"from_country": "France", "from_lat": 46.2, "from_lon": 2.2, "to_country": "Malaysia", "to_lat": 4.2, "to_lon": 101.9, "volume_tons_yr": 48000, "color": "#06b6d4"},
    {"from_country": "Canada", "from_lat": 56.1, "from_lon": -106.3, "to_country": "India", "to_lat": 20.6, "to_lon": 78.9, "volume_tons_yr": 43000, "color": "#10b981"},
    {"from_country": "Australia", "from_lat": -25.3, "from_lon": 133.8, "to_country": "Indonesia", "to_lat": -0.8, "to_lon": 113.9, "volume_tons_yr": 71000, "color": "#ec4899"},
    {"from_country": "Australia", "from_lat": -25.3, "from_lon": 133.8, "to_country": "Malaysia", "to_lat": 4.2, "to_lon": 101.9, "volume_tons_yr": 38000, "color": "#ec4899"},
    {"from_country": "South Korea", "from_lat": 35.9, "from_lon": 127.8, "to_country": "Vietnam", "to_lat": 14.1, "to_lon": 108.3, "volume_tons_yr": 52000, "color": "#f59e0b"},
    {"from_country": "Netherlands", "from_lat": 52.1, "from_lon": 5.3, "to_country": "Indonesia", "to_lat": -0.8, "to_lon": 113.9, "volume_tons_yr": 35000, "color": "#06b6d4"},
    {"from_country": "Italy", "from_lat": 41.9, "from_lon": 12.6, "to_country": "Turkey", "to_lat": 39.0, "to_lon": 35.2, "volume_tons_yr": 45000, "color": "#f97316"},
    {"from_country": "Belgium", "from_lat": 50.5, "from_lon": 4.5, "to_country": "Turkey", "to_lat": 39.0, "to_lon": 35.2, "volume_tons_yr": 32000, "color": "#ef4444"},
    {"from_country": "Spain", "from_lat": 40.5, "from_lon": -3.7, "to_country": "Indonesia", "to_lat": -0.8, "to_lon": 113.9, "volume_tons_yr": 28000, "color": "#f59e0b"},
    {"from_country": "Hong Kong", "from_lat": 22.3, "from_lon": 114.2, "to_country": "Thailand", "to_lat": 15.9, "to_lon": 100.9, "volume_tons_yr": 64000, "color": "#dc2626"},
    {"from_country": "US", "from_lat": 38.0, "from_lon": -97.0, "to_country": "India", "to_lat": 20.6, "to_lon": 78.9, "volume_tons_yr": 39000, "color": "#dc2626"},
]

# ---------------------------------------------------------------------------
# 9. E-WASTE DUMPING DATA (15+)
# ---------------------------------------------------------------------------
EWASTE_SITES = [
    {"name": "Agbogbloshie", "lat": 5.55, "lon": -0.23, "city": "Accra", "country": "Ghana", "annual_tons": 250000, "workers": 10000, "health_risks": "Lead, mercury, cadmium poisoning; respiratory disease", "description": "World's largest e-waste dump until 2021 relocation", "color": "#dc2626"},
    {"name": "Guiyu", "lat": 23.33, "lon": 116.38, "city": "Shantou", "country": "China", "annual_tons": 150000, "workers": 60000, "health_risks": "Elevated blood lead in children, dioxin exposure", "description": "Former e-waste capital of the world, now partially remediated", "color": "#ef4444"},
    {"name": "Seelampur", "lat": 28.67, "lon": 77.28, "city": "Delhi", "country": "India", "annual_tons": 100000, "workers": 25000, "health_risks": "Lead, mercury, acid burns, respiratory illness", "description": "Largest informal e-waste market in India", "color": "#ef4444"},
    {"name": "Alaba Market", "lat": 6.46, "lon": 3.33, "city": "Lagos", "country": "Nigeria", "annual_tons": 70000, "workers": 5000, "health_risks": "Lead exposure, burning toxic fumes", "description": "Major e-waste dumping and processing hub", "color": "#f97316"},
    {"name": "Mandoli", "lat": 28.71, "lon": 77.32, "city": "Delhi", "country": "India", "annual_tons": 45000, "workers": 8000, "health_risks": "Acid baths, heavy metal exposure", "description": "Informal recycling using primitive acid baths", "color": "#f97316"},
    {"name": "Moradabad", "lat": 28.84, "lon": 78.78, "city": "Moradabad", "country": "India", "annual_tons": 35000, "workers": 5000, "health_risks": "Metal fumes, skin diseases", "description": "Brass city with growing e-waste processing", "color": "#f59e0b"},
    {"name": "Karachi E-waste", "lat": 24.87, "lon": 67.03, "city": "Karachi", "country": "Pakistan", "annual_tons": 40000, "workers": 4000, "health_risks": "Mercury, cadmium, lead exposure", "description": "Import hub for used electronics from Gulf states", "color": "#f97316"},
    {"name": "Bangkok E-waste", "lat": 13.76, "lon": 100.50, "city": "Bangkok", "country": "Thailand", "annual_tons": 60000, "workers": 3000, "health_risks": "PCB exposure, dioxin from open burning", "description": "Surge after China import ban (2018)", "color": "#f97316"},
    {"name": "Chittagong", "lat": 22.36, "lon": 91.78, "city": "Chittagong", "country": "Bangladesh", "annual_tons": 30000, "workers": 3000, "health_risks": "Heavy metals, respiratory disease", "description": "Ship-breaking and e-waste combined site", "color": "#f59e0b"},
    {"name": "Manila E-waste", "lat": 14.60, "lon": 120.98, "city": "Manila", "country": "Philippines", "annual_tons": 25000, "workers": 2000, "health_risks": "Lead, mercury from informal processing", "description": "Growing informal e-waste sector", "color": "#f59e0b"},
    {"name": "Tema", "lat": 5.67, "lon": -0.02, "city": "Tema", "country": "Ghana", "annual_tons": 35000, "workers": 3000, "health_risks": "Lead, cadmium, open burning fumes", "description": "Port city receiving e-waste shipments", "color": "#f97316"},
    {"name": "Cairo E-waste", "lat": 30.05, "lon": 31.25, "city": "Cairo", "country": "Egypt", "annual_tons": 20000, "workers": 2500, "health_risks": "Acid extraction, copper smelting fumes", "description": "Informal recycling in Manshiyat Naser area", "color": "#f59e0b"},
    {"name": "Dar es Salaam", "lat": -6.79, "lon": 39.28, "city": "Dar es Salaam", "country": "Tanzania", "annual_tons": 15000, "workers": 1500, "health_risks": "Open burning, lead contamination", "description": "East African e-waste import point", "color": "#f59e0b"},
    {"name": "Nairobi E-waste", "lat": -1.29, "lon": 36.82, "city": "Nairobi", "country": "Kenya", "annual_tons": 18000, "workers": 2000, "health_risks": "Mercury, cadmium, respiratory illness", "description": "Growing e-waste challenge, limited formal recycling", "color": "#f59e0b"},
    {"name": "Ho Chi Minh City E-waste", "lat": 10.82, "lon": 106.63, "city": "Ho Chi Minh City", "country": "Vietnam", "annual_tons": 55000, "workers": 4000, "health_risks": "PCBs, heavy metals from circuit board processing", "description": "Increased imports after China ban", "color": "#f97316"},
    {"name": "Penang E-waste", "lat": 5.41, "lon": 100.33, "city": "Penang", "country": "Malaysia", "annual_tons": 50000, "workers": 3500, "health_risks": "Plastic burning, heavy metal leaching", "description": "Major destination for diverted waste post-2018", "color": "#f97316"},
]

# ---------------------------------------------------------------------------
# 10. DEAD ZONES DATA (20+)
# ---------------------------------------------------------------------------
DEAD_ZONES = [
    {"name": "Gulf of Mexico", "lat": 29.0, "lon": -90.0, "area_km2": 22720, "cause": "Mississippi River agricultural runoff (nitrogen, phosphorus)", "severity": "critical", "color": "#dc2626", "radius_km": 85},
    {"name": "Baltic Sea", "lat": 57.0, "lon": 19.0, "area_km2": 70000, "cause": "Agricultural runoff, sewage from 9 countries", "severity": "critical", "color": "#dc2626", "radius_km": 150},
    {"name": "Chesapeake Bay", "lat": 37.8, "lon": -76.1, "area_km2": 8000, "cause": "Agricultural runoff, urban development", "severity": "severe", "color": "#ef4444", "radius_km": 50},
    {"name": "Black Sea (NW shelf)", "lat": 44.5, "lon": 31.0, "area_km2": 40000, "cause": "Danube River agricultural discharge", "severity": "severe", "color": "#ef4444", "radius_km": 115},
    {"name": "East China Sea", "lat": 30.5, "lon": 123.0, "area_km2": 15000, "cause": "Yangtze River industrial and agricultural runoff", "severity": "critical", "color": "#dc2626", "radius_km": 70},
    {"name": "Arabian Sea (Oman)", "lat": 16.0, "lon": 62.0, "area_km2": 165000, "cause": "Climate change, ocean warming reducing oxygen", "severity": "critical", "color": "#dc2626", "radius_km": 230},
    {"name": "Oregon Shelf", "lat": 44.5, "lon": -124.5, "area_km2": 3000, "cause": "Upwelling intensification, climate change", "severity": "moderate", "color": "#f97316", "radius_km": 30},
    {"name": "Lake Erie", "lat": 41.7, "lon": -82.7, "area_km2": 5000, "cause": "Phosphorus from agriculture, algal blooms", "severity": "severe", "color": "#ef4444", "radius_km": 40},
    {"name": "Adriatic Sea (Po Delta)", "lat": 44.8, "lon": 12.5, "area_km2": 3500, "cause": "Po River nutrient loading", "severity": "moderate", "color": "#f97316", "radius_km": 33},
    {"name": "Pearl River Estuary", "lat": 22.2, "lon": 113.7, "area_km2": 4000, "cause": "Industrial and urban wastewater", "severity": "severe", "color": "#ef4444", "radius_km": 36},
    {"name": "Mobile Bay (Alabama)", "lat": 30.3, "lon": -88.0, "area_km2": 1200, "cause": "Nutrient runoff, jubilee events", "severity": "moderate", "color": "#f97316", "radius_km": 20},
    {"name": "Kattegat (Denmark-Sweden)", "lat": 57.0, "lon": 11.5, "area_km2": 4000, "cause": "Agricultural runoff, eutrophication", "severity": "moderate", "color": "#f97316", "radius_km": 36},
    {"name": "Tokyo Bay", "lat": 35.4, "lon": 139.8, "area_km2": 1200, "cause": "Urban and industrial wastewater", "severity": "moderate", "color": "#f97316", "radius_km": 20},
    {"name": "Elbe Estuary", "lat": 53.9, "lon": 8.7, "area_km2": 800, "cause": "Industrial and agricultural pollution", "severity": "moderate", "color": "#f59e0b", "radius_km": 16},
    {"name": "Bohai Sea", "lat": 38.5, "lon": 120.0, "area_km2": 5200, "cause": "Industrial discharge, Yellow River nutrients", "severity": "severe", "color": "#ef4444", "radius_km": 40},
    {"name": "Pamlico Sound (NC)", "lat": 35.3, "lon": -76.0, "area_km2": 1800, "cause": "Hog farm runoff, hurricanes", "severity": "moderate", "color": "#f97316", "radius_km": 24},
    {"name": "Manila Bay", "lat": 14.5, "lon": 120.7, "area_km2": 1800, "cause": "Untreated sewage, industrial waste", "severity": "severe", "color": "#ef4444", "radius_km": 24},
    {"name": "Buenos Aires Coast", "lat": -35.0, "lon": -57.0, "area_km2": 3000, "cause": "Rio de la Plata agricultural runoff", "severity": "moderate", "color": "#f97316", "radius_km": 30},
    {"name": "Narragansett Bay (RI)", "lat": 41.6, "lon": -71.4, "area_km2": 600, "cause": "Urban wastewater, nutrient loading", "severity": "moderate", "color": "#f59e0b", "radius_km": 14},
    {"name": "Long Island Sound", "lat": 41.0, "lon": -72.8, "area_km2": 3400, "cause": "Nitrogen from sewage treatment plants", "severity": "moderate", "color": "#f97316", "radius_km": 33},
    {"name": "Laurentian Channel (St. Lawrence)", "lat": 48.5, "lon": -62.0, "area_km2": 7000, "cause": "Deep water deoxygenation, nutrient input", "severity": "severe", "color": "#ef4444", "radius_km": 47},
    {"name": "Osaka Bay", "lat": 34.6, "lon": 135.3, "area_km2": 1450, "cause": "Industrial and urban discharge", "severity": "moderate", "color": "#f97316", "radius_km": 21},
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _severity_color(value, thresholds=(50, 100, 200)):
    """Return color based on value and thresholds."""
    if value >= thresholds[2]:
        return "#dc2626"
    elif value >= thresholds[1]:
        return "#ef4444"
    elif value >= thresholds[0]:
        return "#f97316"
    return "#f59e0b"


def _popup_html(title, rows):
    """Build a safe HTML popup for folium markers."""
    safe_title = html.escape(str(title))
    lines = [f"<b style='font-size:13px'>{safe_title}</b><br>"]
    for label, value in rows:
        safe_label = html.escape(str(label))
        safe_value = html.escape(str(value))
        lines.append(f"<b>{safe_label}:</b> {safe_value}<br>")
    return "".join(lines)


def _dark_chart(title, figsize=(8, 4)):
    """Return a dark-themed matplotlib figure and axes."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold")
    ax.tick_params(colors="#8b97b0")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


def _fig_to_bytes(fig):
    """Convert matplotlib figure to bytes for download."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf


@st.cache_data(ttl=3600)
def _fetch_air_quality(lat, lon):
    """Fetch current air quality from Open-Meteo (free, no key)."""
    try:
        resp = requests.get(OPEN_METEO_AQ_API, params={
            "latitude": lat, "longitude": lon,
            "current": "pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,ozone,carbon_monoxide",
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("current", {})
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Map rendering functions
# ---------------------------------------------------------------------------

def _render_ocean_plastic_gyres():
    """Map 1: Ocean Plastic Gyres."""
    st.markdown("### Ocean Plastic Gyres")
    st.markdown("Five major ocean garbage patches where plastic debris accumulates due to rotating ocean currents (gyres).")

    m = folium.Map(location=[10, -30], zoom_start=2, tiles="CartoDB dark_matter")

    total_mass = 0
    total_area = 0
    for gyre in OCEAN_GYRES:
        popup_text = _popup_html(gyre["name"], [
            ("Estimated Mass", f"{gyre['estimated_mass_tons']:,} tons"),
            ("Size", f"{gyre['size_km2']:,} km\u00b2"),
            ("Discovered", str(gyre["discovery_year"])),
            ("Notes", gyre["description"]),
        ])
        folium.Polygon(
            locations=gyre["polygon"],
            color=gyre["color"],
            fill=True,
            fill_color=gyre["color"],
            fill_opacity=0.25,
            weight=2,
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=html.escape(gyre["name"]),
        ).add_to(m)
        folium.Marker(
            location=[gyre["center_lat"], gyre["center_lon"]],
            icon=folium.DivIcon(html=f"<div style='font-size:10px;color:{gyre['color']};font-weight:bold;text-shadow:1px 1px 2px #000'>{html.escape(gyre['name'][:20])}</div>"),
        ).add_to(m)
        total_mass += gyre["estimated_mass_tons"]
        total_area += gyre["size_km2"]

    components.html(m._repr_html_(), height=550)

    c1, c2, c3 = st.columns(3)
    c1.metric("Gyres Mapped", len(OCEAN_GYRES))
    c2.metric("Total Est. Plastic", f"{total_mass:,} tons")
    c3.metric("Total Area", f"{total_area:,} km\u00b2")

    df = pd.DataFrame(OCEAN_GYRES)[["name", "estimated_mass_tons", "size_km2", "discovery_year", "description"]]
    df.columns = ["Name", "Est. Mass (tons)", "Size (km\u00b2)", "Year Discovered", "Description"]
    st.dataframe(df, width="stretch")

    fig, ax = _dark_chart("Estimated Plastic Mass by Gyre (tons)")
    names = [g["name"].replace("Garbage Patch", "GP").replace("Patch", "P") for g in OCEAN_GYRES]
    masses = [g["estimated_mass_tons"] for g in OCEAN_GYRES]
    colors = [g["color"] for g in OCEAN_GYRES]
    ax.barh(names, masses, color=colors)
    ax.set_xlabel("Estimated Mass (tons)", color="#8b97b0")
    ax.invert_yaxis()
    for i, v in enumerate(masses):
        ax.text(v + 500, i, f"{v:,}", color="#e8ecf4", va="center", fontsize=9)
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "ocean_plastic_gyres.png", "image/png")


def _render_oil_spills():
    """Map 2: Major Oil Spills."""
    st.markdown("### Major Oil Spills")
    st.markdown("30+ significant oil spills in history, from tanker disasters to well blowouts.")

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    for spill in OIL_SPILLS:
        radius = max(4, min(15, math.log10(max(spill["volume_barrels"], 1)) * 2.5))
        color = _severity_color(spill["volume_barrels"], thresholds=(100000, 500000, 2000000))
        popup_text = _popup_html(spill["name"], [
            ("Year", str(spill["year"])),
            ("Volume", f"{spill['volume_barrels']:,} barrels"),
            ("Affected Area", f"{spill['affected_area_km2']:,} km\u00b2"),
            ("Location", spill["country"]),
            ("Cause", spill["cause"]),
        ])
        folium.CircleMarker(
            location=[spill["lat"], spill["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1,
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=html.escape(f"{spill['name']} ({spill['year']})"),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    total_barrels = sum(s["volume_barrels"] for s in OIL_SPILLS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Spills Mapped", len(OIL_SPILLS))
    c2.metric("Total Volume", f"{total_barrels:,} bbl")
    c3.metric("Year Range", f"{min(s['year'] for s in OIL_SPILLS)}-{max(s['year'] for s in OIL_SPILLS)}")

    df = pd.DataFrame(OIL_SPILLS)[["name", "year", "volume_barrels", "affected_area_km2", "country", "cause"]]
    df.columns = ["Name", "Year", "Volume (barrels)", "Affected Area (km\u00b2)", "Location", "Cause"]
    df = df.sort_values("Volume (barrels)", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")

    top15 = sorted(OIL_SPILLS, key=lambda x: x["volume_barrels"], reverse=True)[:15]
    fig, ax = _dark_chart("Top 15 Oil Spills by Volume (barrels)", figsize=(9, 5))
    names = [f"{s['name']} ({s['year']})" for s in top15]
    vols = [s["volume_barrels"] for s in top15]
    colors = [_severity_color(v, (100000, 500000, 2000000)) for v in vols]
    ax.barh(names, vols, color=colors)
    ax.set_xlabel("Barrels", color="#8b97b0")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "oil_spills.png", "image/png")


def _render_endangered_species():
    """Map 3: Endangered Species."""
    st.markdown("### Endangered Species Locations")
    st.markdown("40+ critically endangered and endangered species with approximate habitat locations.")

    iucn_filter = st.multiselect("Filter by IUCN Status", ["Critically Endangered", "Endangered", "Vulnerable", "Extinct in Wild"], default=["Critically Endangered", "Endangered", "Vulnerable", "Extinct in Wild"])
    filtered = [s for s in ENDANGERED_SPECIES if s["iucn"] in iucn_filter]

    m = folium.Map(location=[15, 30], zoom_start=2, tiles="CartoDB dark_matter")

    for sp in filtered:
        popup_text = _popup_html(sp["name"], [
            ("Population", f"~{sp['population']:,}" if sp["population"] > 0 else "Functionally Extinct"),
            ("Habitat", sp["habitat"]),
            ("IUCN Status", sp["iucn"]),
        ])
        icon_color = sp["color"]
        folium.CircleMarker(
            location=[sp["lat"], sp["lon"]],
            radius=max(4, 12 - math.log10(max(sp["population"], 1)) * 2),
            color=icon_color,
            fill=True,
            fill_color=icon_color,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=html.escape(f"{sp['name']} (~{sp['population']})"),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    critically = sum(1 for s in filtered if s["iucn"] == "Critically Endangered")
    c1, c2, c3 = st.columns(3)
    c1.metric("Species Shown", len(filtered))
    c2.metric("Critically Endangered", critically)
    c3.metric("Lowest Population", min(s["population"] for s in filtered) if filtered else "N/A")

    if filtered:
        df = pd.DataFrame(filtered)[["name", "population", "habitat", "iucn"]]
        df.columns = ["Species", "Est. Population", "Habitat", "IUCN Status"]
        df = df.sort_values("Est. Population").reset_index(drop=True)
        st.dataframe(df, width="stretch")

    low_pop = sorted(filtered, key=lambda x: x["population"])[:20]
    if low_pop:
        fig, ax = _dark_chart("Most Endangered (Lowest Populations)", figsize=(9, 6))
        names = [s["name"] for s in low_pop]
        pops = [s["population"] for s in low_pop]
        colors = [s["color"] for s in low_pop]
        ax.barh(names, pops, color=colors)
        ax.set_xlabel("Estimated Population", color="#8b97b0")
        ax.invert_yaxis()
        for i, v in enumerate(pops):
            ax.text(v + max(pops) * 0.02, i, str(v), color="#e8ecf4", va="center", fontsize=8)
        fig.tight_layout()
        buf = _fig_to_bytes(fig)
        st.image(buf, width=700)
        st.download_button("Download Chart", buf.getvalue(), "endangered_species.png", "image/png")


def _render_deforestation():
    """Map 4: Deforestation Hotspots."""
    st.markdown("### Deforestation Hotspots")
    st.markdown("Major regions experiencing significant forest loss worldwide.")

    m = folium.Map(location=[0, 20], zoom_start=2, tiles="CartoDB dark_matter")

    for zone in DEFORESTATION_HOTSPOTS:
        popup_text = _popup_html(zone["name"], [
            ("Annual Loss", f"{zone['annual_loss_km2']:,} km\u00b2/year"),
            ("Primary Cause", zone["primary_cause"]),
        ])
        folium.Polygon(
            locations=zone["polygon"],
            color=zone["color"],
            fill=True,
            fill_color=zone["color"],
            fill_opacity=0.3,
            weight=2,
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=html.escape(zone["name"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    total_loss = sum(z["annual_loss_km2"] for z in DEFORESTATION_HOTSPOTS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Hotspots", len(DEFORESTATION_HOTSPOTS))
    c2.metric("Total Annual Loss", f"{total_loss:,} km\u00b2/yr")
    c3.metric("Worst Region", max(DEFORESTATION_HOTSPOTS, key=lambda x: x["annual_loss_km2"])["name"])

    df = pd.DataFrame(DEFORESTATION_HOTSPOTS)[["name", "annual_loss_km2", "primary_cause"]]
    df.columns = ["Region", "Annual Loss (km\u00b2)", "Primary Cause"]
    df = df.sort_values("Annual Loss (km\u00b2)", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")

    fig, ax = _dark_chart("Annual Deforestation Rate by Region (km\u00b2/year)", figsize=(9, 6))
    sorted_zones = sorted(DEFORESTATION_HOTSPOTS, key=lambda x: x["annual_loss_km2"], reverse=True)
    names = [z["name"] for z in sorted_zones]
    losses = [z["annual_loss_km2"] for z in sorted_zones]
    colors = [z["color"] for z in sorted_zones]
    ax.barh(names, losses, color=colors)
    ax.set_xlabel("Annual Loss (km\u00b2)", color="#8b97b0")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "deforestation.png", "image/png")


def _render_nuclear_disasters():
    """Map 5: Nuclear Disaster Zones."""
    st.markdown("### Nuclear Disaster Zones")
    st.markdown("Major nuclear accidents and contaminated sites with exclusion/affected zones.")

    m = folium.Map(location=[40, 30], zoom_start=2, tiles="CartoDB dark_matter")

    for nd in NUCLEAR_DISASTERS:
        popup_text = _popup_html(nd["name"], [
            ("Year", str(nd["year"])),
            ("INES Level", str(nd["ines_level"]) if nd["ines_level"] > 0 else "Test Site"),
            ("Exclusion Zone", f"{nd['exclusion_radius_km']} km radius"),
            ("Country", nd["country"]),
            ("Radiation", nd["radiation_peak"]),
            ("Deaths", nd["deaths"]),
            ("Status", nd["status"]),
        ])
        folium.Circle(
            location=[nd["lat"], nd["lon"]],
            radius=nd["exclusion_radius_km"] * 1000,
            color=nd["color"],
            fill=True,
            fill_color=nd["color"],
            fill_opacity=0.25,
            weight=2,
            popup=folium.Popup(popup_text, max_width=350),
            tooltip=html.escape(f"{nd['name']} ({nd['year']}) - INES {nd['ines_level']}"),
        ).add_to(m)
        folium.Marker(
            location=[nd["lat"], nd["lon"]],
            icon=folium.Icon(color="red" if nd["ines_level"] >= 6 else "orange" if nd["ines_level"] >= 4 else "gray", icon="radiation" if nd["ines_level"] >= 5 else "warning-sign", prefix="glyphicon"),
            popup=folium.Popup(popup_text, max_width=350),
            tooltip=html.escape(nd["name"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    ines7 = sum(1 for nd in NUCLEAR_DISASTERS if nd["ines_level"] == 7)
    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Mapped", len(NUCLEAR_DISASTERS))
    c2.metric("INES Level 7", ines7)
    c3.metric("Year Range", f"{min(nd['year'] for nd in NUCLEAR_DISASTERS)}-{max(nd['year'] for nd in NUCLEAR_DISASTERS)}")

    df = pd.DataFrame(NUCLEAR_DISASTERS)[["name", "year", "ines_level", "exclusion_radius_km", "country", "status"]]
    df.columns = ["Site", "Year", "INES Level", "Exclusion Radius (km)", "Country", "Status"]
    df = df.sort_values("INES Level", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")

    fig, ax = _dark_chart("Nuclear Incidents by INES Level")
    ines_counts = {}
    for nd in NUCLEAR_DISASTERS:
        lv = nd["ines_level"]
        ines_counts[lv] = ines_counts.get(lv, 0) + 1
    levels = sorted(ines_counts.keys())
    counts = [ines_counts[l] for l in levels]
    ines_colors = {0: "#8b97b0", 3: "#f59e0b", 4: "#f97316", 5: "#ef4444", 6: "#dc2626", 7: "#ff0000"}
    bar_colors = [ines_colors.get(l, "#06b6d4") for l in levels]
    labels = [f"Level {l}" if l > 0 else "Test Site" for l in levels]
    ax.bar(labels, counts, color=bar_colors)
    ax.set_ylabel("Number of Incidents", color="#8b97b0")
    for i, v in enumerate(counts):
        ax.text(i, v + 0.1, str(v), color="#e8ecf4", ha="center", fontsize=10)
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "nuclear_disasters.png", "image/png")


def _render_polluted_cities():
    """Map 6: Most Polluted Cities."""
    st.markdown("### Most Polluted Cities (PM2.5)")
    st.markdown("30+ most polluted cities worldwide. Click a marker to fetch **live** air quality data from Open-Meteo.")

    m = folium.Map(location=[25, 75], zoom_start=3, tiles="CartoDB dark_matter")

    for city in POLLUTED_CITIES:
        color = _severity_color(city["avg_pm25"], thresholds=(55, 80, 100))
        radius = max(5, city["avg_pm25"] / 10)
        popup_text = _popup_html(city["name"], [
            ("Country", city["country"]),
            ("Avg PM2.5", f"{city['avg_pm25']} \u00b5g/m\u00b3"),
            ("Rank", f"#{city['rank']}"),
        ])
        folium.CircleMarker(
            location=[city["lat"], city["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=html.escape(f"{city['name']} - PM2.5: {city['avg_pm25']}"),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    c1, c2, c3 = st.columns(3)
    c1.metric("Cities Mapped", len(POLLUTED_CITIES))
    c2.metric("Avg PM2.5 (all)", f"{sum(c['avg_pm25'] for c in POLLUTED_CITIES) / len(POLLUTED_CITIES):.0f} \u00b5g/m\u00b3")
    c3.metric("Most Polluted", POLLUTED_CITIES[0]["name"])

    # Live data for selected city
    st.markdown("#### Live Air Quality Lookup")
    city_names = [f"{c['name']}, {c['country']}" for c in POLLUTED_CITIES]
    selected = st.selectbox("Select city for live data", city_names)
    idx = city_names.index(selected)
    city = POLLUTED_CITIES[idx]

    if st.button("Fetch Live Air Quality", key="poll_live_aq"):
        with st.spinner("Fetching from Open-Meteo Air Quality API..."):
            aq = _fetch_air_quality(city["lat"], city["lon"])
            if aq:
                ac1, ac2, ac3 = st.columns(3)
                ac1.metric("PM2.5", f"{aq.get('pm2_5', 'N/A')} \u00b5g/m\u00b3")
                ac2.metric("PM10", f"{aq.get('pm10', 'N/A')} \u00b5g/m\u00b3")
                ac3.metric("NO\u2082", f"{aq.get('nitrogen_dioxide', 'N/A')} \u00b5g/m\u00b3")
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("SO\u2082", f"{aq.get('sulphur_dioxide', 'N/A')} \u00b5g/m\u00b3")
                bc2.metric("O\u2083", f"{aq.get('ozone', 'N/A')} \u00b5g/m\u00b3")
                bc3.metric("CO", f"{aq.get('carbon_monoxide', 'N/A')} \u00b5g/m\u00b3")
            else:
                st.warning("Could not fetch live data. Showing historical average only.")

    df = pd.DataFrame(POLLUTED_CITIES)[["name", "country", "avg_pm25", "rank"]]
    df.columns = ["City", "Country", "Avg PM2.5 (\u00b5g/m\u00b3)", "Rank"]
    df = df.sort_values("Rank").reset_index(drop=True)
    st.dataframe(df, width="stretch")

    fig, ax = _dark_chart("Top 20 Most Polluted Cities (Avg PM2.5)", figsize=(9, 6))
    top20 = sorted(POLLUTED_CITIES, key=lambda x: x["avg_pm25"], reverse=True)[:20]
    names = [f"{c['name']}" for c in top20]
    pm_vals = [c["avg_pm25"] for c in top20]
    colors = [_severity_color(v, (55, 80, 100)) for v in pm_vals]
    ax.barh(names, pm_vals, color=colors)
    ax.set_xlabel("PM2.5 (\u00b5g/m\u00b3)", color="#8b97b0")
    ax.axvline(x=15, color="#10b981", linestyle="--", alpha=0.7, label="WHO Guideline (15)")
    ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "polluted_cities.png", "image/png")


def _render_acid_rain():
    """Map 7: Acid Rain Regions."""
    st.markdown("### Acid Rain Regions")
    st.markdown("Major regions affected by acid rain (pH < 5.6) from industrial SO\u2082 and NO\u2093 emissions.")

    m = folium.Map(location=[35, 30], zoom_start=2, tiles="CartoDB dark_matter")

    for region in ACID_RAIN_REGIONS:
        popup_text = _popup_html(region["name"], [
            ("Avg pH", str(region["avg_ph"])),
            ("Primary Pollutant", region["primary_pollutant"]),
            ("Severity", region["severity"].capitalize()),
        ])
        folium.Polygon(
            locations=region["polygon"],
            color=region["color"],
            fill=True,
            fill_color=region["color"],
            fill_opacity=0.3,
            weight=2,
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=html.escape(f"{region['name']} (pH {region['avg_ph']})"),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    lowest_ph = min(r["avg_ph"] for r in ACID_RAIN_REGIONS)
    critical_count = sum(1 for r in ACID_RAIN_REGIONS if r["severity"] == "critical")
    c1, c2, c3 = st.columns(3)
    c1.metric("Regions Mapped", len(ACID_RAIN_REGIONS))
    c2.metric("Lowest pH", lowest_ph)
    c3.metric("Critical Severity", critical_count)

    df = pd.DataFrame(ACID_RAIN_REGIONS)[["name", "avg_ph", "primary_pollutant", "severity"]]
    df.columns = ["Region", "Avg pH", "Primary Pollutant", "Severity"]
    df = df.sort_values("Avg pH").reset_index(drop=True)
    st.dataframe(df, width="stretch")

    fig, ax = _dark_chart("Acid Rain Severity by Region (pH)", figsize=(9, 5))
    sorted_regions = sorted(ACID_RAIN_REGIONS, key=lambda x: x["avg_ph"])
    names = [r["name"] for r in sorted_regions]
    phs = [r["avg_ph"] for r in sorted_regions]
    colors = [r["color"] for r in sorted_regions]
    ax.barh(names, phs, color=colors)
    ax.set_xlabel("Average pH (lower = more acidic)", color="#8b97b0")
    ax.axvline(x=5.6, color="#10b981", linestyle="--", alpha=0.7, label="Normal Rain pH (5.6)")
    ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "acid_rain.png", "image/png")


def _render_plastic_waste_exporters():
    """Map 8: Plastic Waste Exporters."""
    st.markdown("### Plastic Waste Export Routes")
    st.markdown("Major flows of plastic waste from wealthy nations to developing countries for 'recycling'.")

    m = folium.Map(location=[20, 60], zoom_start=2, tiles="CartoDB dark_matter")

    exporters = {}
    importers = {}
    for route in PLASTIC_EXPORTERS:
        exp = route["from_country"]
        imp = route["to_country"]
        exporters[exp] = exporters.get(exp, 0) + route["volume_tons_yr"]
        importers[imp] = importers.get(imp, 0) + route["volume_tons_yr"]

        folium.PolyLine(
            locations=[
                [route["from_lat"], route["from_lon"]],
                [route["to_lat"], route["to_lon"]],
            ],
            color=route["color"],
            weight=max(1, route["volume_tons_yr"] / 40000),
            opacity=0.6,
            tooltip=html.escape(f"{route['from_country']} \u2192 {route['to_country']}: {route['volume_tons_yr']:,} tons/yr"),
            popup=folium.Popup(_popup_html("Plastic Waste Route", [
                ("From", route["from_country"]),
                ("To", route["to_country"]),
                ("Volume", f"{route['volume_tons_yr']:,} tons/year"),
            ]), max_width=300),
        ).add_to(m)

    # Mark exporter countries
    seen_from = set()
    for route in PLASTIC_EXPORTERS:
        key = route["from_country"]
        if key not in seen_from:
            seen_from.add(key)
            folium.CircleMarker(
                location=[route["from_lat"], route["from_lon"]],
                radius=6,
                color="#06b6d4",
                fill=True,
                fill_color="#06b6d4",
                fill_opacity=0.8,
                tooltip=html.escape(f"Exporter: {key} ({exporters[key]:,} tons/yr)"),
            ).add_to(m)

    # Mark importer countries
    seen_to = set()
    for route in PLASTIC_EXPORTERS:
        key = route["to_country"]
        if key not in seen_to:
            seen_to.add(key)
            folium.CircleMarker(
                location=[route["to_lat"], route["to_lon"]],
                radius=8,
                color="#dc2626",
                fill=True,
                fill_color="#dc2626",
                fill_opacity=0.8,
                tooltip=html.escape(f"Importer: {key} ({importers[key]:,} tons/yr)"),
            ).add_to(m)

    components.html(m._repr_html_(), height=550)

    total_flow = sum(r["volume_tons_yr"] for r in PLASTIC_EXPORTERS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Trade Routes", len(PLASTIC_EXPORTERS))
    c2.metric("Total Annual Flow", f"{total_flow:,} tons/yr")
    c3.metric("Top Exporter", max(exporters, key=exporters.get))

    df = pd.DataFrame(PLASTIC_EXPORTERS)[["from_country", "to_country", "volume_tons_yr"]]
    df.columns = ["Exporter", "Importer", "Volume (tons/yr)"]
    df = df.sort_values("Volume (tons/yr)", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("#0a0e1a")
    for ax in [ax1, ax2]:
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#8b97b0")
        for spine in ax.spines.values():
            spine.set_color("#2a3550")

    sorted_exp = sorted(exporters.items(), key=lambda x: x[1], reverse=True)[:10]
    ax1.barh([e[0] for e in sorted_exp], [e[1] for e in sorted_exp], color="#06b6d4")
    ax1.set_title("Top Exporters (tons/yr)", color="#e8ecf4", fontsize=11)
    ax1.set_xlabel("Tons/year", color="#8b97b0")
    ax1.invert_yaxis()

    sorted_imp = sorted(importers.items(), key=lambda x: x[1], reverse=True)
    ax2.barh([i[0] for i in sorted_imp], [i[1] for i in sorted_imp], color="#dc2626")
    ax2.set_title("Top Importers (tons/yr)", color="#e8ecf4", fontsize=11)
    ax2.set_xlabel("Tons/year", color="#8b97b0")
    ax2.invert_yaxis()

    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=800)
    st.download_button("Download Chart", buf.getvalue(), "plastic_exports.png", "image/png")


def _render_ewaste():
    """Map 9: E-Waste Dumping."""
    st.markdown("### E-Waste Dumping Sites")
    st.markdown("Major informal e-waste processing sites worldwide where hazardous electronic waste is handled unsafely.")

    m = folium.Map(location=[15, 50], zoom_start=2, tiles="CartoDB dark_matter")

    for site in EWASTE_SITES:
        popup_text = _popup_html(site["name"], [
            ("City", site["city"]),
            ("Country", site["country"]),
            ("Annual Volume", f"{site['annual_tons']:,} tons"),
            ("Workers", f"~{site['workers']:,}"),
            ("Health Risks", site["health_risks"]),
            ("Description", site["description"]),
        ])
        radius = max(5, math.sqrt(site["annual_tons"] / 1000))
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=radius,
            color=site["color"],
            fill=True,
            fill_color=site["color"],
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_text, max_width=350),
            tooltip=html.escape(f"{site['name']} ({site['annual_tons']:,} tons/yr)"),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    total_tons = sum(s["annual_tons"] for s in EWASTE_SITES)
    total_workers = sum(s["workers"] for s in EWASTE_SITES)
    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Mapped", len(EWASTE_SITES))
    c2.metric("Total E-Waste", f"{total_tons:,} tons/yr")
    c3.metric("Affected Workers", f"~{total_workers:,}")

    df = pd.DataFrame(EWASTE_SITES)[["name", "city", "country", "annual_tons", "workers", "health_risks"]]
    df.columns = ["Site", "City", "Country", "Annual Tons", "Workers", "Health Risks"]
    df = df.sort_values("Annual Tons", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")

    fig, ax = _dark_chart("E-Waste Processing Sites by Volume (tons/year)", figsize=(9, 6))
    sorted_sites = sorted(EWASTE_SITES, key=lambda x: x["annual_tons"], reverse=True)
    names = [f"{s['name']} ({s['country']})" for s in sorted_sites]
    tons = [s["annual_tons"] for s in sorted_sites]
    colors = [s["color"] for s in sorted_sites]
    ax.barh(names, tons, color=colors)
    ax.set_xlabel("Annual Volume (tons)", color="#8b97b0")
    ax.invert_yaxis()
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "ewaste.png", "image/png")


def _render_dead_zones():
    """Map 10: Dead Zones."""
    st.markdown("### Ocean Dead Zones")
    st.markdown("20+ hypoxic (oxygen-depleted) areas where marine life cannot survive, caused mainly by nutrient pollution.")

    m = folium.Map(location=[30, 0], zoom_start=2, tiles="CartoDB dark_matter")

    for dz in DEAD_ZONES:
        popup_text = _popup_html(dz["name"], [
            ("Area", f"{dz['area_km2']:,} km\u00b2"),
            ("Cause", dz["cause"]),
            ("Severity", dz["severity"].capitalize()),
        ])
        folium.Circle(
            location=[dz["lat"], dz["lon"]],
            radius=dz["radius_km"] * 1000,
            color=dz["color"],
            fill=True,
            fill_color=dz["color"],
            fill_opacity=0.3,
            weight=2,
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=html.escape(f"{dz['name']} ({dz['area_km2']:,} km\u00b2)"),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    total_area = sum(dz["area_km2"] for dz in DEAD_ZONES)
    critical_count = sum(1 for dz in DEAD_ZONES if dz["severity"] == "critical")
    c1, c2, c3 = st.columns(3)
    c1.metric("Dead Zones", len(DEAD_ZONES))
    c2.metric("Total Hypoxic Area", f"{total_area:,} km\u00b2")
    c3.metric("Critical Zones", critical_count)

    df = pd.DataFrame(DEAD_ZONES)[["name", "area_km2", "cause", "severity"]]
    df.columns = ["Dead Zone", "Area (km\u00b2)", "Cause", "Severity"]
    df = df.sort_values("Area (km\u00b2)", ascending=False).reset_index(drop=True)
    st.dataframe(df, width="stretch")

    fig, ax = _dark_chart("Dead Zones by Area (km\u00b2)", figsize=(9, 7))
    sorted_dz = sorted(DEAD_ZONES, key=lambda x: x["area_km2"], reverse=True)[:15]
    names = [dz["name"] for dz in sorted_dz]
    areas = [dz["area_km2"] for dz in sorted_dz]
    colors = [dz["color"] for dz in sorted_dz]
    ax.barh(names, areas, color=colors)
    ax.set_xlabel("Area (km\u00b2)", color="#8b97b0")
    ax.invert_yaxis()
    for i, v in enumerate(areas):
        ax.text(v + max(areas) * 0.01, i, f"{v:,}", color="#e8ecf4", va="center", fontsize=8)
    fig.tight_layout()
    buf = _fig_to_bytes(fig)
    st.image(buf, width=700)
    st.download_button("Download Chart", buf.getvalue(), "dead_zones.png", "image/png")


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_pollution_maps_tab():
    """Main entry point for the Pollution & Environment tab."""
    st.markdown(
        '<div class="tab-header red">'
        "<h4>Pollution &amp; Environment</h4>"
        "<p>Ocean plastic, oil spills, endangered species, deforestation, pollution hotspots</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    map_choice = st.selectbox("Select Map Type", MAP_TYPES, key="pollution_map_type")

    st.markdown("---")

    if map_choice == "Ocean Plastic Gyres":
        _render_ocean_plastic_gyres()
    elif map_choice == "Major Oil Spills":
        _render_oil_spills()
    elif map_choice == "Endangered Species":
        _render_endangered_species()
    elif map_choice == "Deforestation Hotspots":
        _render_deforestation()
    elif map_choice == "Nuclear Disaster Zones":
        _render_nuclear_disasters()
    elif map_choice == "Most Polluted Cities":
        _render_polluted_cities()
    elif map_choice == "Acid Rain Regions":
        _render_acid_rain()
    elif map_choice == "Plastic Waste Exporters":
        _render_plastic_waste_exporters()
    elif map_choice == "E-Waste Dumping":
        _render_ewaste()
    elif map_choice == "Dead Zones":
        _render_dead_zones()
