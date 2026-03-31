# -*- coding: utf-8 -*-
"""
Botanical & Gardens Explorer module for TerraScout AI.
Uses the Overpass API to discover botanical gardens, nature reserves, arboretums,
and other plant-related sites from OpenStreetMap. Integrates with GBIF for species
occurrence data in biodiversity hotspot regions.

10 Map Modes:
  1. World Botanical Gardens
  2. National Parks
  3. Rainforest Reserves
  4. Endemic Plant Hotspots
  5. Cherry Blossom Sites
  6. Ancient & Sacred Trees
  7. Medicinal Plant Gardens
  8. Orchid & Flower Gardens
  9. Arboretums
 10. Biomes & Biodiversity Hotspots
"""

import io
import html
import streamlit as st
import pandas as pd
import requests
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

from src.overpass_client import query_overpass

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS: Map modes, presets, colours
# ══════════════════════════════════════════════════════════════════════════════

MAP_MODES = {
    "World Botanical Gardens": {
        "description": (
            "Explore major botanical gardens worldwide. These living museums "
            "conserve plant diversity, support scientific research, and offer "
            "education on horticulture and ecology."
        ),
        "tags": [
            ("leisure", "garden", "garden:type", "botanical"),
            ("leisure", "garden", "name", "*botanical*"),
        ],
        "fallback_query": (
            'node["leisure"="garden"]["garden:type"="botanical"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["garden:type"="botanical"](around:{radius},{lat},{lon});'
            'node["leisure"="garden"]["name"~"[Bb]otanical|[Bb]otanic"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["name"~"[Bb]otanical|[Bb]otanic"](around:{radius},{lat},{lon});'
        ),
        "color": "#10b981",
        "icon": "leaf",
    },
    "National Parks": {
        "description": (
            "Discover national parks and large protected nature reserves. "
            "These are government-designated areas preserving ecosystems, "
            "wildlife habitats, and natural landscapes."
        ),
        "tags": [
            ("boundary", "national_park", None, None),
            ("leisure", "nature_reserve", None, None),
        ],
        "fallback_query": (
            'node["boundary"="national_park"](around:{radius},{lat},{lon});'
            'way["boundary"="national_park"](around:{radius},{lat},{lon});'
            'relation["boundary"="national_park"](around:{radius},{lat},{lon});'
            'node["leisure"="nature_reserve"](around:{radius},{lat},{lon});'
            'way["leisure"="nature_reserve"](around:{radius},{lat},{lon});'
        ),
        "color": "#059669",
        "icon": "tree",
    },
    "Rainforest Reserves": {
        "description": (
            "Locate tropical and temperate rainforest reserves, protected "
            "forest areas, and nature conservation zones. These ecosystems "
            "harbour the highest terrestrial biodiversity on Earth."
        ),
        "tags": [
            ("natural", "wood", None, None),
            ("landuse", "forest", "leaf_type", "broadleaved"),
        ],
        "fallback_query": (
            'node["leisure"="nature_reserve"]["name"~"[Ff]orest|[Rr]ainforest|[Jj]ungle|[Ss]elva"](around:{radius},{lat},{lon});'
            'way["leisure"="nature_reserve"]["name"~"[Ff]orest|[Rr]ainforest|[Jj]ungle|[Ss]elva"](around:{radius},{lat},{lon});'
            'node["boundary"="protected_area"]["name"~"[Ff]orest|[Rr]ainforest|[Jj]ungle"](around:{radius},{lat},{lon});'
            'way["boundary"="protected_area"]["name"~"[Ff]orest|[Rr]ainforest|[Jj]ungle"](around:{radius},{lat},{lon});'
        ),
        "color": "#047857",
        "icon": "tree",
    },
    "Endemic Plant Hotspots": {
        "description": (
            "Explore regions recognised for exceptional concentrations of "
            "endemic plant species. Uses GBIF occurrence data to identify "
            "areas with high plant endemism and species richness."
        ),
        "tags": [],
        "fallback_query": (
            'node["leisure"="nature_reserve"](around:{radius},{lat},{lon});'
            'way["leisure"="nature_reserve"](around:{radius},{lat},{lon});'
            'node["boundary"="protected_area"](around:{radius},{lat},{lon});'
            'way["boundary"="protected_area"](around:{radius},{lat},{lon});'
        ),
        "color": "#f59e0b",
        "icon": "star",
        "uses_gbif": True,
    },
    "Cherry Blossom Sites": {
        "description": (
            "Find parks and gardens famous for cherry blossoms (sakura). "
            "Includes Japanese hanami spots, Washington D.C. tidal basin, "
            "and other celebrated cherry-tree locations worldwide."
        ),
        "tags": [
            ("species", "Prunus serrulata", None, None),
            ("genus", "Prunus", None, None),
        ],
        "fallback_query": (
            'node["natural"="tree"]["species"~"[Pp]runus"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["name"~"[Cc]herry|[Ss]akura|[Hh]anami"](around:{radius},{lat},{lon});'
            'node["leisure"="park"]["name"~"[Cc]herry|[Ss]akura"](around:{radius},{lat},{lon});'
            'way["leisure"="park"]["name"~"[Cc]herry|[Ss]akura"](around:{radius},{lat},{lon});'
        ),
        "color": "#ec4899",
        "icon": "flower",
    },
    "Ancient & Sacred Trees": {
        "description": (
            "Discover ancient, monumental, and sacred trees recorded in "
            "OpenStreetMap. Many carry natural-heritage protection and have "
            "cultural or spiritual significance spanning centuries."
        ),
        "tags": [
            ("natural", "tree", "denotation", "natural_monument"),
            ("natural", "tree", "monument", "yes"),
        ],
        "fallback_query": (
            'node["natural"="tree"]["denotation"="natural_monument"](around:{radius},{lat},{lon});'
            'node["natural"="tree"]["monument"="yes"](around:{radius},{lat},{lon});'
            'node["natural"="tree"]["historic"](around:{radius},{lat},{lon});'
            'node["natural"="tree"]["age"](around:{radius},{lat},{lon});'
        ),
        "color": "#a855f7",
        "icon": "tree",
    },
    "Medicinal Plant Gardens": {
        "description": (
            "Locate medicinal and herb gardens, physic gardens, and "
            "ethnobotanical collections. These gardens preserve traditional "
            "knowledge and cultivate pharmacologically important species."
        ),
        "tags": [
            ("leisure", "garden", "garden:type", "herb_garden"),
        ],
        "fallback_query": (
            'node["leisure"="garden"]["garden:type"~"herb|medicinal|physic"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["garden:type"~"herb|medicinal|physic"](around:{radius},{lat},{lon});'
            'node["leisure"="garden"]["name"~"[Hh]erb|[Mm]edicinal|[Pp]hysic|[Pp]harmac"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["name"~"[Hh]erb|[Mm]edicinal|[Pp]hysic|[Pp]harmac"](around:{radius},{lat},{lon});'
        ),
        "color": "#14b8a6",
        "icon": "plus-sign",
    },
    "Orchid & Flower Gardens": {
        "description": (
            "Find flower gardens, orchid houses, rose gardens, tulip fields, "
            "and other ornamental plant collections celebrated for their "
            "floral beauty and horticultural displays."
        ),
        "tags": [
            ("leisure", "garden", "garden:type", "flower_garden"),
        ],
        "fallback_query": (
            'node["leisure"="garden"]["garden:type"~"flower|rose|tulip|orchid"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["garden:type"~"flower|rose|tulip|orchid"](around:{radius},{lat},{lon});'
            'node["leisure"="garden"]["name"~"[Oo]rchid|[Rr]ose|[Ff]lower|[Tt]ulip|[Ll]ily"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["name"~"[Oo]rchid|[Rr]ose|[Ff]lower|[Tt]ulip|[Ll]ily"](around:{radius},{lat},{lon});'
        ),
        "color": "#f43f5e",
        "icon": "asterisk",
    },
    "Arboretums": {
        "description": (
            "Explore arboretums and tree collections. These specialised "
            "botanical collections cultivate and display a wide variety of "
            "trees and woody plants for research and public enjoyment."
        ),
        "tags": [
            ("leisure", "garden", "garden:type", "arboretum"),
        ],
        "fallback_query": (
            'node["leisure"="garden"]["garden:type"="arboretum"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["garden:type"="arboretum"](around:{radius},{lat},{lon});'
            'node["leisure"="garden"]["name"~"[Aa]rboretum|[Aa]rboreta"](around:{radius},{lat},{lon});'
            'way["leisure"="garden"]["name"~"[Aa]rboretum|[Aa]rboreta"](around:{radius},{lat},{lon});'
        ),
        "color": "#22c55e",
        "icon": "tree-deciduous",
    },
    "Biomes & Biodiversity Hotspots": {
        "description": (
            "Discover protected biodiversity hotspots, biosphere reserves, "
            "and IUCN-designated areas. These represent the most biologically "
            "rich and threatened regions on the planet."
        ),
        "tags": [
            ("boundary", "protected_area", None, None),
        ],
        "fallback_query": (
            'node["boundary"="protected_area"](around:{radius},{lat},{lon});'
            'way["boundary"="protected_area"](around:{radius},{lat},{lon});'
            'relation["boundary"="protected_area"](around:{radius},{lat},{lon});'
            'node["leisure"="nature_reserve"](around:{radius},{lat},{lon});'
            'way["leisure"="nature_reserve"](around:{radius},{lat},{lon});'
        ),
        "color": "#06b6d4",
        "icon": "globe",
    },
}

# ── Preset locations per mode ────────────────────────────────────────────────

MODE_PRESETS = {
    "World Botanical Gardens": {
        "Custom": None,
        "Kew Gardens, London": {"lat": 51.4787, "lon": -0.2956, "radius": 5},
        "New York Botanical Garden": {"lat": 40.8623, "lon": -73.8779, "radius": 5},
        "Singapore Botanic Gardens": {"lat": 1.3138, "lon": 103.8159, "radius": 3},
        "Jardim Botanico, Rio de Janeiro": {"lat": -22.9671, "lon": -43.2237, "radius": 3},
        "Botanischer Garten, Berlin": {"lat": 52.4567, "lon": 13.3087, "radius": 5},
        "Royal Botanic Gardens, Melbourne": {"lat": -37.8304, "lon": 144.9796, "radius": 3},
        "Orto Botanico, Padova": {"lat": 45.3994, "lon": 11.8803, "radius": 3},
        "Jardin des Plantes, Paris": {"lat": 48.8437, "lon": 2.3596, "radius": 3},
    },
    "National Parks": {
        "Custom": None,
        "Yellowstone, USA": {"lat": 44.4280, "lon": -110.5885, "radius": 50},
        "Kruger, South Africa": {"lat": -23.9884, "lon": 31.5547, "radius": 50},
        "Banff, Canada": {"lat": 51.4968, "lon": -115.9281, "radius": 30},
        "Torres del Paine, Chile": {"lat": -51.0000, "lon": -73.0000, "radius": 30},
        "Plitvice Lakes, Croatia": {"lat": 44.8654, "lon": 15.5820, "radius": 10},
        "Swiss National Park": {"lat": 46.6600, "lon": 10.1700, "radius": 15},
        "Dolomiti Bellunesi, Italy": {"lat": 46.2000, "lon": 12.0000, "radius": 20},
    },
    "Rainforest Reserves": {
        "Custom": None,
        "Amazon Basin, Brazil": {"lat": -3.4653, "lon": -62.2159, "radius": 50},
        "Daintree, Australia": {"lat": -16.2500, "lon": 145.4185, "radius": 20},
        "Borneo, Malaysia": {"lat": 4.5000, "lon": 115.0000, "radius": 50},
        "Congo Basin, DRC": {"lat": -0.7893, "lon": 24.5093, "radius": 50},
        "Monteverde, Costa Rica": {"lat": 10.3155, "lon": -84.8249, "radius": 10},
        "Taman Negara, Malaysia": {"lat": 4.3844, "lon": 102.3914, "radius": 20},
    },
    "Endemic Plant Hotspots": {
        "Custom": None,
        "Cape Floristic Region, SA": {"lat": -33.9616, "lon": 18.6020, "radius": 30},
        "Madagascar Highlands": {"lat": -18.8792, "lon": 47.5079, "radius": 30},
        "Canary Islands, Spain": {"lat": 28.1235, "lon": -15.4363, "radius": 20},
        "Hawaii, USA": {"lat": 19.8968, "lon": -155.5828, "radius": 30},
        "New Caledonia": {"lat": -22.2558, "lon": 166.4580, "radius": 30},
        "Socotra Island, Yemen": {"lat": 12.4634, "lon": 53.8237, "radius": 20},
    },
    "Cherry Blossom Sites": {
        "Custom": None,
        "Tokyo - Ueno Park": {"lat": 35.7146, "lon": 139.7732, "radius": 5},
        "Kyoto - Philosopher's Path": {"lat": 35.0268, "lon": 135.7948, "radius": 5},
        "Washington D.C. - Tidal Basin": {"lat": 38.8853, "lon": -77.0386, "radius": 5},
        "Jinhae, South Korea": {"lat": 35.1477, "lon": 128.6669, "radius": 5},
        "Bonn, Germany - Altstadt": {"lat": 50.7374, "lon": 7.0982, "radius": 3},
        "Vancouver - Stanley Park": {"lat": 49.3017, "lon": -123.1417, "radius": 3},
    },
    "Ancient & Sacred Trees": {
        "Custom": None,
        "Sherwood Forest, UK": {"lat": 53.2043, "lon": -1.0676, "radius": 5},
        "Sequoia NP, California": {"lat": 36.4864, "lon": -118.5658, "radius": 15},
        "Cryptomeria Avenue, Nikko": {"lat": 36.7469, "lon": 139.6048, "radius": 5},
        "Baobab Alley, Madagascar": {"lat": -20.2509, "lon": 44.4189, "radius": 5},
        "Ancient Olive Trees, Puglia": {"lat": 40.3515, "lon": 18.1718, "radius": 10},
        "Methuselah Grove, California": {"lat": 37.3795, "lon": -118.1685, "radius": 10},
    },
    "Medicinal Plant Gardens": {
        "Custom": None,
        "Chelsea Physic Garden, London": {"lat": 51.4845, "lon": -0.1632, "radius": 3},
        "Giardino dei Semplici, Florence": {"lat": 43.7799, "lon": 11.2556, "radius": 3},
        "Leiden Hortus Botanicus": {"lat": 52.1575, "lon": 4.4886, "radius": 3},
        "Traditional Medicine, Beijing": {"lat": 39.9399, "lon": 116.3994, "radius": 10},
        "Kirstenbosch, Cape Town": {"lat": -33.9881, "lon": 18.4327, "radius": 5},
        "Ayurvedic Gardens, Kerala": {"lat": 8.5241, "lon": 76.9366, "radius": 10},
    },
    "Orchid & Flower Gardens": {
        "Custom": None,
        "Keukenhof, Netherlands": {"lat": 52.2697, "lon": 4.5462, "radius": 3},
        "Orchid Garden, Singapore": {"lat": 1.3138, "lon": 103.8159, "radius": 3},
        "Butchart Gardens, Victoria": {"lat": 48.5635, "lon": -123.4706, "radius": 3},
        "Dubai Miracle Garden": {"lat": 25.0568, "lon": 55.2448, "radius": 3},
        "Giverny - Monet's Garden": {"lat": 49.0758, "lon": 1.5339, "radius": 2},
        "Nong Nooch, Thailand": {"lat": 12.7636, "lon": 100.9396, "radius": 3},
    },
    "Arboretums": {
        "Custom": None,
        "Arnold Arboretum, Boston": {"lat": 42.3012, "lon": -71.1254, "radius": 3},
        "Westonbirt Arboretum, UK": {"lat": 51.6019, "lon": -2.2178, "radius": 3},
        "Morton Arboretum, Illinois": {"lat": 41.8164, "lon": -88.0700, "radius": 5},
        "Bedgebury National Pinetum": {"lat": 51.0765, "lon": 0.4493, "radius": 3},
        "Arboretum de Versailles": {"lat": 48.8020, "lon": 2.0842, "radius": 3},
        "National Arboretum, Canberra": {"lat": -35.2795, "lon": 149.0710, "radius": 3},
    },
    "Biomes & Biodiversity Hotspots": {
        "Custom": None,
        "Atlantic Forest, Brazil": {"lat": -22.9068, "lon": -43.1729, "radius": 30},
        "Western Ghats, India": {"lat": 10.9800, "lon": 76.2700, "radius": 30},
        "Mediterranean Basin, S. France": {"lat": 43.2965, "lon": 5.3698, "radius": 30},
        "Sundaland, Indonesia": {"lat": -6.1750, "lon": 106.8283, "radius": 30},
        "Cerrado, Brazil": {"lat": -15.7975, "lon": -47.8919, "radius": 30},
        "Eastern Afromontane": {"lat": -3.0674, "lon": 37.3556, "radius": 30},
    },
}

# ── Curated fallback data for modes that may return sparse Overpass results ──

CURATED_BOTANICAL_GARDENS = [
    {"name": "Royal Botanic Gardens, Kew", "lat": 51.4787, "lon": -0.2956, "country": "United Kingdom", "established": 1759, "area_ha": 132, "species_count": 50000},
    {"name": "New York Botanical Garden", "lat": 40.8623, "lon": -73.8779, "country": "United States", "established": 1891, "area_ha": 101, "species_count": 30000},
    {"name": "Singapore Botanic Gardens", "lat": 1.3138, "lon": 103.8159, "country": "Singapore", "established": 1859, "area_ha": 82, "species_count": 10000},
    {"name": "Jardim Botanico, Rio de Janeiro", "lat": -22.9671, "lon": -43.2237, "country": "Brazil", "established": 1808, "area_ha": 54, "species_count": 6500},
    {"name": "Botanischer Garten, Berlin-Dahlem", "lat": 52.4567, "lon": 13.3087, "country": "Germany", "established": 1897, "area_ha": 43, "species_count": 22000},
    {"name": "Royal Botanic Gardens, Melbourne", "lat": -37.8304, "lon": 144.9796, "country": "Australia", "established": 1846, "area_ha": 38, "species_count": 8500},
    {"name": "Orto Botanico di Padova", "lat": 45.3994, "lon": 11.8803, "country": "Italy", "established": 1545, "area_ha": 2.2, "species_count": 6000},
    {"name": "Jardin des Plantes, Paris", "lat": 48.8437, "lon": 2.3596, "country": "France", "established": 1626, "area_ha": 24, "species_count": 10000},
    {"name": "Missouri Botanical Garden", "lat": 38.6128, "lon": -90.2593, "country": "United States", "established": 1859, "area_ha": 32, "species_count": 18000},
    {"name": "Kirstenbosch National Botanical Garden", "lat": -33.9881, "lon": 18.4327, "country": "South Africa", "established": 1913, "area_ha": 528, "species_count": 7000},
    {"name": "Kunming Botanical Garden", "lat": 25.0160, "lon": 102.7416, "country": "China", "established": 1938, "area_ha": 44, "species_count": 5700},
    {"name": "Koishikawa Korakuen, Tokyo", "lat": 35.7079, "lon": 139.7505, "country": "Japan", "established": 1684, "area_ha": 7, "species_count": 3000},
    {"name": "Hortus Botanicus, Leiden", "lat": 52.1575, "lon": 4.4886, "country": "Netherlands", "established": 1590, "area_ha": 1, "species_count": 10000},
    {"name": "Real Jardin Botanico, Madrid", "lat": 40.4109, "lon": -3.6910, "country": "Spain", "established": 1755, "area_ha": 8, "species_count": 5000},
    {"name": "Bogor Botanical Garden", "lat": -6.5984, "lon": 106.7989, "country": "Indonesia", "established": 1817, "area_ha": 87, "species_count": 15000},
]

CURATED_CHERRY_SITES = [
    {"name": "Ueno Park", "city": "Tokyo", "country": "Japan", "lat": 35.7146, "lon": 139.7732, "trees": 800, "peak_month": "Late March"},
    {"name": "Philosopher's Path", "city": "Kyoto", "country": "Japan", "lat": 35.0268, "lon": 135.7948, "trees": 500, "peak_month": "Early April"},
    {"name": "Tidal Basin", "city": "Washington D.C.", "country": "United States", "lat": 38.8853, "lon": -77.0386, "trees": 3000, "peak_month": "Late March"},
    {"name": "Jinhae Cherry Blossom Festival", "city": "Jinhae", "country": "South Korea", "lat": 35.1477, "lon": 128.6669, "trees": 350000, "peak_month": "Early April"},
    {"name": "Heerstrasse Cherry Alley", "city": "Bonn", "country": "Germany", "lat": 50.7374, "lon": 7.0982, "trees": 300, "peak_month": "Mid April"},
    {"name": "High Park", "city": "Toronto", "country": "Canada", "lat": 43.6465, "lon": -79.4637, "trees": 200, "peak_month": "Early May"},
    {"name": "Meguro River", "city": "Tokyo", "country": "Japan", "lat": 35.6400, "lon": 139.7050, "trees": 800, "peak_month": "Late March"},
    {"name": "Stanley Park", "city": "Vancouver", "country": "Canada", "lat": 49.3017, "lon": -123.1417, "trees": 500, "peak_month": "Late March"},
    {"name": "Shinjuku Gyoen", "city": "Tokyo", "country": "Japan", "lat": 35.6852, "lon": 139.7100, "trees": 1100, "peak_month": "Late March"},
    {"name": "Yeouido Spring Flower Festival", "city": "Seoul", "country": "South Korea", "lat": 37.5219, "lon": 126.9245, "trees": 1800, "peak_month": "Early April"},
    {"name": "Kungstradgarden", "city": "Stockholm", "country": "Sweden", "lat": 59.3317, "lon": 18.0716, "trees": 63, "peak_month": "Late April"},
    {"name": "Jardin des Plantes", "city": "Paris", "country": "France", "lat": 48.8437, "lon": 2.3596, "trees": 150, "peak_month": "Early April"},
]

CURATED_ANCIENT_TREES = [
    {"name": "Major Oak", "location": "Sherwood Forest, UK", "lat": 53.2043, "lon": -1.0676, "species": "Quercus robur", "age_years": 1000, "circumference_m": 10.0},
    {"name": "General Sherman", "location": "Sequoia NP, California", "lat": 36.5819, "lon": -118.7513, "species": "Sequoiadendron giganteum", "age_years": 2200, "circumference_m": 31.1},
    {"name": "Methuselah", "location": "White Mountains, California", "lat": 37.3795, "lon": -118.1685, "species": "Pinus longaeva", "age_years": 4855, "circumference_m": 4.6},
    {"name": "Jomon Sugi", "location": "Yakushima, Japan", "lat": 30.3327, "lon": 130.5379, "species": "Cryptomeria japonica", "age_years": 5000, "circumference_m": 16.4},
    {"name": "Olive Tree of Vouves", "location": "Crete, Greece", "lat": 35.4906, "lon": 23.7870, "species": "Olea europaea", "age_years": 3000, "circumference_m": 12.5},
    {"name": "Llangernyw Yew", "location": "Conwy, Wales", "lat": 53.2201, "lon": -3.5597, "species": "Taxus baccata", "age_years": 4000, "circumference_m": 10.8},
    {"name": "El Arbol del Tule", "location": "Oaxaca, Mexico", "lat": 17.0464, "lon": -96.6363, "species": "Taxodium mucronatum", "age_years": 2000, "circumference_m": 42.0},
    {"name": "Baobab Avenue", "location": "Morondava, Madagascar", "lat": -20.2509, "lon": 44.4189, "species": "Adansonia grandidieri", "age_years": 800, "circumference_m": 25.0},
    {"name": "Tjiktin Chansen", "location": "Schiermonnikoog, Netherlands", "lat": 53.4903, "lon": 6.1535, "species": "Quercus robur", "age_years": 600, "circumference_m": 6.5},
    {"name": "Bowthorpe Oak", "location": "Lincolnshire, UK", "lat": 52.7734, "lon": -0.4430, "species": "Quercus robur", "age_years": 1000, "circumference_m": 12.3},
]

CURATED_BIODIVERSITY_HOTSPOTS = [
    {"name": "Atlantic Forest", "region": "South America", "lat": -22.9068, "lon": -43.1729, "area_km2": 1233875, "endemic_plants": 8000, "threat_level": "Critical"},
    {"name": "Cape Floristic Region", "region": "Africa", "lat": -33.9616, "lon": 18.6020, "area_km2": 78555, "endemic_plants": 6210, "threat_level": "Critical"},
    {"name": "Sundaland", "region": "Southeast Asia", "lat": -6.1750, "lon": 106.8283, "area_km2": 1501063, "endemic_plants": 15000, "threat_level": "Critical"},
    {"name": "Mediterranean Basin", "region": "Europe/N. Africa", "lat": 43.2965, "lon": 5.3698, "area_km2": 2085292, "endemic_plants": 11700, "threat_level": "Endangered"},
    {"name": "Mesoamerica", "region": "Central America", "lat": 15.7835, "lon": -90.2308, "area_km2": 1130019, "endemic_plants": 2941, "threat_level": "Endangered"},
    {"name": "Western Ghats & Sri Lanka", "region": "South Asia", "lat": 10.9800, "lon": 76.2700, "area_km2": 189611, "endemic_plants": 3049, "threat_level": "Endangered"},
    {"name": "Indo-Burma", "region": "Southeast Asia", "lat": 17.9691, "lon": 102.6331, "area_km2": 2373057, "endemic_plants": 7000, "threat_level": "Critical"},
    {"name": "Cerrado", "region": "South America", "lat": -15.7975, "lon": -47.8919, "area_km2": 2031990, "endemic_plants": 4400, "threat_level": "Endangered"},
    {"name": "Madagascar & Indian Ocean Islands", "region": "Africa", "lat": -18.8792, "lon": 47.5079, "area_km2": 600461, "endemic_plants": 11600, "threat_level": "Critical"},
    {"name": "Eastern Afromontane", "region": "Africa", "lat": -3.0674, "lon": 37.3556, "area_km2": 1017806, "endemic_plants": 2350, "threat_level": "Endangered"},
    {"name": "Polynesia-Micronesia", "region": "Pacific", "lat": -17.7134, "lon": -149.4068, "area_km2": 47238, "endemic_plants": 3334, "threat_level": "Critical"},
    {"name": "Caribbean Islands", "region": "Caribbean", "lat": 18.1096, "lon": -77.2975, "area_km2": 229549, "endemic_plants": 6550, "threat_level": "Critical"},
]


# ══════════════════════════════════════════════════════════════════════════════
# API FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _query_overpass_botanical(lat: float, lon: float, radius_km: float,
                              mode_key: str) -> list:
    """
    Query Overpass for botanical/garden features based on the selected mode.
    Returns a list of feature dicts with name, lat, lon, tags, etc.
    """
    mode = MAP_MODES.get(mode_key)
    if not mode:
        return []

    radius_m = int(radius_km * 1000)
    query_body = mode["fallback_query"].format(
        radius=radius_m, lat=lat, lon=lon
    )

    query = f"""
[out:json][timeout:90];
(
  {query_body}
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []

    elements = result.get("elements", [])

    # Build node lookup for way centroid resolution
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    seen_names = set()

    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        lat_f, lon_f = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat_f, lon_f = el["lat"], el["lon"]
        elif el.get("type") in ("way", "relation"):
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1])
                      for n in nodes if n in node_lookup]
            if coords:
                lat_f = sum(c[0] for c in coords) / len(coords)
                lon_f = sum(c[1] for c in coords) / len(coords)

            # For relations, try member nodes
            if lat_f is None and el.get("type") == "relation":
                members = el.get("members", [])
                member_coords = []
                for mem in members:
                    if mem.get("type") == "node" and mem.get("ref") in node_lookup:
                        member_coords.append(node_lookup[mem["ref"]])
                if member_coords:
                    lat_f = sum(c[0] for c in member_coords) / len(member_coords)
                    lon_f = sum(c[1] for c in member_coords) / len(member_coords)

        if lat_f is None or lon_f is None:
            continue

        name = tags.get("name", tags.get("name:en", tags.get("name:it", "")))
        if not name:
            name = tags.get("description", tags.get("operator", "Unnamed"))

        # Deduplicate by name + rough position
        dedup_key = f"{name}_{round(lat_f, 3)}_{round(lon_f, 3)}"
        if dedup_key in seen_names:
            continue
        seen_names.add(dedup_key)

        features.append({
            "name": name,
            "lat": lat_f,
            "lon": lon_f,
            "osm_id": el.get("id", ""),
            "osm_type": el.get("type", ""),
            "tags": tags,
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
            "website": tags.get("website", tags.get("url", "")),
            "species": tags.get("species", tags.get("genus", tags.get("taxon", ""))),
            "description": tags.get("description", tags.get("description:en", "")),
            "opening_hours": tags.get("opening_hours", ""),
            "operator": tags.get("operator", ""),
            "protection_title": tags.get("protect_title", tags.get("protection_title", "")),
        })

    return features


@st.cache_data(ttl=3600)
def _query_gbif_species(lat: float, lon: float, radius_km: float,
                        limit: int = 300) -> list:
    """
    Query GBIF occurrence API for plant species near a location.
    Returns a list of occurrence dicts.
    """
    # GBIF expects decimal degree radius; we approximate with a bounding box
    delta = radius_km / 111.0  # rough degrees
    params = {
        "decimalLatitude": f"{lat - delta},{lat + delta}",
        "decimalLongitude": f"{lon - delta},{lon + delta}",
        "kingdomKey": 6,  # Plantae
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "limit": min(limit, 300),
    }
    try:
        resp = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params=params,
            timeout=20,
            headers={"User-Agent": "TerraScoutAI/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception:
        return []


@st.cache_data(ttl=3600)
def _query_gbif_species_counts(lat: float, lon: float, radius_km: float) -> dict:
    """
    Query GBIF for species counts (faceted) near a location.
    Returns summary statistics dict.
    """
    delta = radius_km / 111.0
    params = {
        "decimalLatitude": f"{lat - delta},{lat + delta}",
        "decimalLongitude": f"{lon - delta},{lon + delta}",
        "kingdomKey": 6,
        "hasCoordinate": "true",
        "limit": 0,
        "facet": "speciesKey",
        "facetLimit": 500,
    }
    try:
        resp = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params=params,
            timeout=20,
            headers={"User-Agent": "TerraScoutAI/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        total_occurrences = data.get("count", 0)
        facets = data.get("facets", [])
        species_count = 0
        for f in facets:
            if f.get("field") == "SPECIES_KEY":
                species_count = len(f.get("counts", []))
                break
        return {
            "total_occurrences": total_occurrences,
            "species_count": species_count,
        }
    except Exception:
        return {"total_occurrences": 0, "species_count": 0}


# ══════════════════════════════════════════════════════════════════════════════
# MAP BUILDER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _build_folium_map(center_lat: float, center_lon: float, zoom: int,
                      radius_km: float = None) -> folium.Map:
    """Create a base dark-themed Folium map with optional search-radius circle."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        overlay=False,
    ).add_to(m)

    if radius_km is not None:
        folium.Circle(
            location=[center_lat, center_lon],
            radius=radius_km * 1000,
            color="#10b981",
            fill=True,
            fill_opacity=0.04,
            weight=1,
        ).add_to(m)

    return m


def _add_markers(m: folium.Map, features: list, color: str,
                 name_key: str = "name") -> folium.Map:
    """Add circle markers with safe HTML popups to a Folium map."""
    for f in features:
        lat = f.get("lat")
        lon = f.get("lon")
        if lat is None or lon is None:
            continue

        safe_name = html.escape(str(f.get(name_key, "Unknown")))
        safe_desc = html.escape(str(f.get("description", ""))[:150])
        safe_species = html.escape(str(f.get("species", "")))

        popup_parts = [f'<div style="max-width:220px;">']
        popup_parts.append(f"<strong>{safe_name}</strong><br/>")
        if safe_species:
            popup_parts.append(
                f'<em style="font-size:0.8rem; color:#10b981;">{safe_species}</em><br/>'
            )
        if safe_desc:
            popup_parts.append(
                f'<span style="font-size:0.75rem; color:#666;">{safe_desc}</span><br/>'
            )

        wiki = f.get("wikipedia", "")
        if wiki and ":" in wiki:
            lang, title = wiki.split(":", 1)
            safe_title = html.escape(title)
            popup_parts.append(
                f'<a href="https://{html.escape(lang)}.wikipedia.org/wiki/'
                f'{safe_title}" target="_blank" style="font-size:0.75rem;">'
                f"Wikipedia</a><br/>"
            )

        website = f.get("website", "")
        if website:
            safe_url = html.escape(website)
            popup_parts.append(
                f'<a href="{safe_url}" target="_blank" '
                f'style="font-size:0.75rem;">Website</a>'
            )

        popup_parts.append("</div>")
        popup_html = "".join(popup_parts)

        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(m)

    return m


def _render_stats_row(metrics: list):
    """Render a row of st.metric cards. metrics = [(label, value), ...]"""
    cols = st.columns(min(len(metrics), 5))
    for i, (label, value) in enumerate(metrics):
        if i < len(cols):
            cols[i].metric(label, value)


def _render_data_table(features: list, columns: list, key_prefix: str):
    """Render a DataFrame table and CSV download button."""
    if not features:
        st.info("No data to display.")
        return

    rows = []
    for f in features:
        row = {}
        for col in columns:
            row[col] = f.get(col, f.get(col.lower(), ""))
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Records (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"terrascout_{key_prefix}.csv",
        mime="text/csv",
        key=f"dl_{key_prefix}",
    )


def _render_matplotlib_bar(labels: list, values: list, colors: list,
                           xlabel: str = "Count", title: str = ""):
    """Render a horizontal bar chart in the TerraScout dark theme."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, max(3, len(labels) * 0.4)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    ax.barh(range(len(labels)), values, color=colors, alpha=0.85)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([l[:30] for l in labels], color="#e8ecf4", fontsize=9)
    ax.set_xlabel(xlabel, color="#e8ecf4", fontsize=10)
    if title:
        ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# MODE RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def _render_world_botanical_gardens(lat: float, lon: float, radius_km: float):
    """Mode 1: World Botanical Gardens."""
    st.markdown("#### World Botanical Gardens")
    st.caption(MAP_MODES["World Botanical Gardens"]["description"])

    with st.spinner("Searching botanical gardens via OpenStreetMap..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "World Botanical Gardens")

    # Merge curated data for global view if local search is sparse
    curated_used = False
    if len(features) < 3:
        st.info(
            "Supplementing with curated list of world-renowned botanical gardens."
        )
        for g in CURATED_BOTANICAL_GARDENS:
            features.append({
                "name": g["name"],
                "lat": g["lat"],
                "lon": g["lon"],
                "description": f"Est. {g['established']}, {g['country']}",
                "species": f"~{g['species_count']:,} species",
                "wikipedia": "",
                "website": "",
                "country": g["country"],
                "established": g["established"],
                "area_ha": g["area_ha"],
                "species_count": g["species_count"],
            })
        curated_used = True

    if not features:
        st.warning("No botanical gardens found. Try a larger radius or different location.")
        return

    # Stats
    total = len(features)
    countries = set()
    total_species = 0
    oldest = None
    for f in features:
        c = f.get("country", f.get("tags", {}).get("addr:country", ""))
        if c:
            countries.add(c)
        sc = f.get("species_count", 0)
        if sc:
            total_species += sc
        est = f.get("established", 0)
        if est and (oldest is None or est < oldest):
            oldest = est

    metrics = [
        ("Gardens Found", f"{total:,}"),
        ("Countries", f"{len(countries) if countries else 'N/A'}"),
    ]
    if total_species > 0:
        metrics.append(("Total Species (est.)", f"{total_species:,}"))
    if oldest:
        metrics.append(("Oldest Est.", str(oldest)))

    _render_stats_row(metrics)

    st.markdown("---")

    # Map
    zoom = 3 if curated_used else 11
    m = _build_folium_map(lat, lon, zoom, radius_km if not curated_used else None)
    _add_markers(m, features, "#10b981")
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Data table
    st.markdown("---")
    st.markdown("#### Garden Details")
    table_cols = ["name", "lat", "lon", "description", "species"]
    if curated_used:
        table_cols = ["name", "country", "established", "area_ha", "species_count", "lat", "lon"]
    _render_data_table(features, table_cols, "botanical_gardens")


def _render_national_parks(lat: float, lon: float, radius_km: float):
    """Mode 2: National Parks."""
    st.markdown("#### National Parks & Nature Reserves")
    st.caption(MAP_MODES["National Parks"]["description"])

    with st.spinner("Searching national parks and reserves via OpenStreetMap..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "National Parks")

    if not features:
        st.warning("No national parks found. Try a larger radius (50 km+).")
        return

    # Categorize
    parks = [f for f in features if "national_park" in str(f.get("tags", {}).get("boundary", ""))]
    reserves = [f for f in features if f not in parks]

    _render_stats_row([
        ("Total Protected Areas", f"{len(features):,}"),
        ("National Parks", f"{len(parks):,}"),
        ("Nature Reserves", f"{len(reserves):,}"),
    ])

    st.markdown("---")

    m = _build_folium_map(lat, lon, 9, radius_km)
    _add_markers(m, parks, "#059669")
    _add_markers(m, reserves, "#34d399")
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Legend
    st.markdown(
        '<div style="display:flex; gap:1rem; margin-top:0.25rem;">'
        '<span style="color:#059669; font-size:0.8rem;">&#9679; National Parks</span>'
        '<span style="color:#34d399; font-size:0.8rem;">&#9679; Nature Reserves</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### Park & Reserve List")
    _render_data_table(
        features,
        ["name", "lat", "lon", "protection_title", "operator", "description"],
        "national_parks",
    )


def _render_rainforest_reserves(lat: float, lon: float, radius_km: float):
    """Mode 3: Rainforest Reserves."""
    st.markdown("#### Rainforest & Forest Reserves")
    st.caption(MAP_MODES["Rainforest Reserves"]["description"])

    with st.spinner("Searching rainforest reserves via OpenStreetMap..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "Rainforest Reserves")

    if not features:
        st.warning(
            "No rainforest reserves found. Try tropical locations "
            "(Amazon, Borneo, Congo Basin) with a large radius."
        )
        return

    _render_stats_row([
        ("Forest Areas Found", f"{len(features):,}"),
        ("Search Radius", f"{radius_km} km"),
    ])

    st.markdown("---")

    m = _build_folium_map(lat, lon, 8, radius_km)
    _add_markers(m, features, "#047857")
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Reserve Details")
    _render_data_table(
        features,
        ["name", "lat", "lon", "protection_title", "operator", "description"],
        "rainforest_reserves",
    )


def _render_endemic_hotspots(lat: float, lon: float, radius_km: float):
    """Mode 4: Endemic Plant Hotspots - uses GBIF for species data."""
    st.markdown("#### Endemic Plant Hotspots")
    st.caption(MAP_MODES["Endemic Plant Hotspots"]["description"])

    col_a, col_b = st.columns(2)
    with col_a:
        use_gbif = st.checkbox(
            "Fetch live GBIF plant occurrences",
            value=True,
            key="bot_gbif_toggle",
            help="Query the GBIF database for plant species near this location.",
        )
    with col_b:
        gbif_limit = st.slider(
            "Max occurrences", 50, 300, 200, step=50, key="bot_gbif_limit"
        )

    # Protected areas from Overpass
    with st.spinner("Searching protected areas via OpenStreetMap..."):
        osm_features = _query_overpass_botanical(
            lat, lon, radius_km, "Endemic Plant Hotspots"
        )

    # GBIF occurrences
    gbif_records = []
    gbif_stats = {"total_occurrences": 0, "species_count": 0}
    if use_gbif:
        with st.spinner("Querying GBIF for plant species data..."):
            gbif_records = _query_gbif_species(lat, lon, radius_km, gbif_limit)
            gbif_stats = _query_gbif_species_counts(lat, lon, radius_km)

    # Use curated biodiversity hotspots as reference
    nearby_hotspots = []
    for hs in CURATED_BIODIVERSITY_HOTSPOTS:
        # Rough distance check (within ~30 degrees)
        if abs(hs["lat"] - lat) < 30 and abs(hs["lon"] - lon) < 30:
            nearby_hotspots.append(hs)

    _render_stats_row([
        ("Protected Areas (OSM)", f"{len(osm_features):,}"),
        ("GBIF Occurrences", f"{gbif_stats['total_occurrences']:,}"),
        ("Unique Species (est.)", f"{gbif_stats['species_count']:,}"),
        ("Known Hotspots Nearby", f"{len(nearby_hotspots)}"),
    ])

    st.markdown("---")

    # Map - show OSM protected areas + GBIF points
    m = _build_folium_map(lat, lon, 9, radius_km)
    _add_markers(m, osm_features, "#f59e0b")

    # Add GBIF occurrences as small dots
    for rec in gbif_records[:200]:
        rlat = rec.get("decimalLatitude")
        rlon = rec.get("decimalLongitude")
        if rlat is None or rlon is None:
            continue
        safe_species = html.escape(str(rec.get("species", "Unknown")))
        safe_family = html.escape(str(rec.get("family", "")))
        popup_html = (
            f'<div style="max-width:180px;">'
            f'<strong style="color:#10b981;">{safe_species}</strong><br/>'
            f'<span style="font-size:0.8rem; color:#666;">{safe_family}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[rlat, rlon],
            radius=4,
            color="#10b981",
            fill=True,
            fill_color="#10b981",
            fill_opacity=0.5,
            weight=1,
            popup=folium.Popup(popup_html, max_width=200),
        ).add_to(m)

    # Mark nearby biodiversity hotspots
    for hs in nearby_hotspots:
        safe_name = html.escape(hs["name"])
        folium.Marker(
            location=[hs["lat"], hs["lon"]],
            icon=folium.Icon(color="orange", icon="star", prefix="glyphicon"),
            popup=folium.Popup(
                f'<div style="max-width:200px;">'
                f'<strong>{safe_name}</strong><br/>'
                f'<span style="font-size:0.8rem;">'
                f'Endemic plants: ~{hs["endemic_plants"]:,}<br/>'
                f'Threat: {html.escape(hs["threat_level"])}'
                f'</span></div>',
                max_width=220,
            ),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-top:0.25rem;">'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9679; Protected Areas</span>'
        '<span style="color:#10b981; font-size:0.8rem;">&#9679; GBIF Occurrences</span>'
        '<span style="color:#f97316; font-size:0.8rem;">&#9733; Biodiversity Hotspots</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # GBIF species table
    if gbif_records:
        st.markdown("---")
        st.markdown("#### Plant Species Occurrences (GBIF)")
        gbif_rows = []
        for rec in gbif_records:
            gbif_rows.append({
                "species": rec.get("species", ""),
                "family": rec.get("family", ""),
                "genus": rec.get("genus", ""),
                "latitude": rec.get("decimalLatitude", ""),
                "longitude": rec.get("decimalLongitude", ""),
                "country": rec.get("country", ""),
                "year": rec.get("year", ""),
                "dataset": rec.get("datasetName", "")[:60] if rec.get("datasetName") else "",
            })

        df_gbif = pd.DataFrame(gbif_rows)
        st.dataframe(df_gbif, use_container_width=True, hide_index=True)

        csv_buf = io.StringIO()
        df_gbif.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download {len(gbif_rows)} GBIF Records (CSV)",
            data=csv_buf.getvalue(),
            file_name="terrascout_endemic_gbif.csv",
            mime="text/csv",
            key="dl_endemic_gbif",
        )

    # Protected areas table
    if osm_features:
        st.markdown("---")
        st.markdown("#### Protected Areas (OSM)")
        _render_data_table(
            osm_features,
            ["name", "lat", "lon", "protection_title", "description"],
            "endemic_osm",
        )


def _render_cherry_blossom(lat: float, lon: float, radius_km: float):
    """Mode 5: Cherry Blossom Sites."""
    st.markdown("#### Cherry Blossom Sites")
    st.caption(MAP_MODES["Cherry Blossom Sites"]["description"])

    with st.spinner("Searching cherry blossom locations..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "Cherry Blossom Sites")

    # Always supplement with curated sakura data
    curated = list(CURATED_CHERRY_SITES)
    curated_features = []
    for s in curated:
        curated_features.append({
            "name": s["name"],
            "lat": s["lat"],
            "lon": s["lon"],
            "description": f"{s['city']}, {s['country']}",
            "species": f"~{s['trees']:,} trees",
            "wikipedia": "",
            "website": "",
            "city": s["city"],
            "country": s["country"],
            "trees": s["trees"],
            "peak_month": s["peak_month"],
        })

    all_features = features + curated_features

    # Stats
    total_trees = sum(s["trees"] for s in curated)
    countries = set(s["country"] for s in curated)

    _render_stats_row([
        ("Sites Found", f"{len(all_features):,}"),
        ("OSM Cherry Trees/Parks", f"{len(features):,}"),
        ("Curated Famous Sites", f"{len(curated):,}"),
        ("Est. Total Trees", f"{total_trees:,}"),
    ])

    st.markdown("---")

    # Map
    m = _build_folium_map(lat, lon, 3)
    # OSM features in light pink
    _add_markers(m, features, "#f9a8d4")
    # Curated in bright pink
    for cf in curated_features:
        safe_name = html.escape(cf["name"])
        safe_city = html.escape(cf.get("city", ""))
        safe_peak = html.escape(cf.get("peak_month", ""))
        trees = cf.get("trees", 0)
        popup_html = (
            f'<div style="max-width:200px;">'
            f'<strong style="color:#ec4899;">{safe_name}</strong><br/>'
            f'<span style="font-size:0.8rem;">{safe_city}</span><br/>'
            f'<span style="font-size:0.75rem;">~{trees:,} trees</span><br/>'
            f'<span style="font-size:0.75rem;">Peak bloom: {safe_peak}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[cf["lat"], cf["lon"]],
            radius=8,
            color="#ec4899",
            fill=True,
            fill_color="#ec4899",
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-top:0.25rem;">'
        '<span style="color:#ec4899; font-size:0.8rem;">&#9679; Famous Sakura Sites</span>'
        '<span style="color:#f9a8d4; font-size:0.8rem;">&#9679; OSM Cherry Trees/Parks</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Bar chart - trees per site
    st.markdown("---")
    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        st.markdown("#### Trees per Site")
        sorted_curated = sorted(curated, key=lambda x: x["trees"], reverse=True)[:10]
        _render_matplotlib_bar(
            labels=[s["name"] for s in sorted_curated],
            values=[s["trees"] for s in sorted_curated],
            colors=["#ec4899"] * len(sorted_curated),
            xlabel="Estimated Trees",
            title="Top Cherry Blossom Sites",
        )

    with col_table:
        st.markdown("#### Bloom Calendar")
        cal_rows = []
        for s in curated:
            cal_rows.append({
                "Site": s["name"],
                "City": s["city"],
                "Peak Bloom": s["peak_month"],
                "Trees": f"{s['trees']:,}",
            })
        df_cal = pd.DataFrame(cal_rows)
        st.dataframe(df_cal, use_container_width=True, hide_index=True)

    # Full download
    st.markdown("---")
    all_rows = []
    for f in all_features:
        all_rows.append({
            "name": f["name"],
            "lat": f["lat"],
            "lon": f["lon"],
            "description": f.get("description", ""),
            "trees": f.get("trees", ""),
            "peak_month": f.get("peak_month", ""),
        })
    df_all = pd.DataFrame(all_rows)
    csv_buf = io.StringIO()
    df_all.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(all_rows)} Cherry Blossom Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name="terrascout_cherry_blossom.csv",
        mime="text/csv",
        key="dl_cherry",
    )


def _render_ancient_trees(lat: float, lon: float, radius_km: float):
    """Mode 6: Ancient & Sacred Trees."""
    st.markdown("#### Ancient & Sacred Trees")
    st.caption(MAP_MODES["Ancient & Sacred Trees"]["description"])

    with st.spinner("Searching ancient trees via OpenStreetMap..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "Ancient & Sacred Trees")

    # Supplement with curated
    curated_features = []
    for t in CURATED_ANCIENT_TREES:
        curated_features.append({
            "name": t["name"],
            "lat": t["lat"],
            "lon": t["lon"],
            "description": t["location"],
            "species": t["species"],
            "wikipedia": "",
            "website": "",
            "age_years": t["age_years"],
            "circumference_m": t["circumference_m"],
            "location_name": t["location"],
        })

    all_features = features + curated_features if len(features) < 5 else features

    if not all_features:
        st.warning("No ancient trees found. Try different coordinates or a larger radius.")
        return

    # Stats
    oldest = max((f.get("age_years", 0) for f in all_features), default=0)
    biggest = max((f.get("circumference_m", 0) for f in all_features), default=0)
    species_set = set(f.get("species", "") for f in all_features if f.get("species"))

    _render_stats_row([
        ("Trees Found", f"{len(all_features):,}"),
        ("Oldest (est.)", f"{oldest:,} yrs" if oldest else "N/A"),
        ("Largest Girth", f"{biggest:.1f} m" if biggest else "N/A"),
        ("Distinct Species", f"{len(species_set)}"),
    ])

    st.markdown("---")

    # Map
    use_curated = len(features) < 5
    zoom = 3 if use_curated else 11
    m = _build_folium_map(lat, lon, zoom, radius_km if not use_curated else None)

    for f in all_features:
        flat, flon = f.get("lat"), f.get("lon")
        if flat is None or flon is None:
            continue
        safe_name = html.escape(str(f.get("name", "Unknown")))
        safe_species = html.escape(str(f.get("species", "")))
        safe_loc = html.escape(str(f.get("description", f.get("location_name", ""))))
        age = f.get("age_years", 0)
        circ = f.get("circumference_m", 0)

        popup_parts = [f'<div style="max-width:220px;">']
        popup_parts.append(f'<strong style="color:#a855f7;">{safe_name}</strong><br/>')
        if safe_species:
            popup_parts.append(f'<em style="font-size:0.8rem;">{safe_species}</em><br/>')
        if safe_loc:
            popup_parts.append(f'<span style="font-size:0.75rem;">{safe_loc}</span><br/>')
        if age:
            popup_parts.append(f'<span style="font-size:0.75rem;">Age: ~{age:,} years</span><br/>')
        if circ:
            popup_parts.append(f'<span style="font-size:0.75rem;">Girth: {circ:.1f} m</span>')
        popup_parts.append('</div>')

        # Size marker by age
        marker_size = 6
        if age > 3000:
            marker_size = 12
        elif age > 1000:
            marker_size = 9

        folium.CircleMarker(
            location=[flat, flon],
            radius=marker_size,
            color="#a855f7",
            fill=True,
            fill_color="#a855f7",
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup("".join(popup_parts), max_width=240),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Chart + table
    st.markdown("---")
    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        st.markdown("#### Age Comparison")
        aged = [f for f in all_features if f.get("age_years")]
        aged_sorted = sorted(aged, key=lambda x: x["age_years"], reverse=True)[:10]
        if aged_sorted:
            _render_matplotlib_bar(
                labels=[f.get("name", "?") for f in aged_sorted],
                values=[f["age_years"] for f in aged_sorted],
                colors=["#a855f7"] * len(aged_sorted),
                xlabel="Estimated Age (years)",
                title="Oldest Known Trees",
            )

    with col_table:
        st.markdown("#### Tree Details")
        tree_rows = []
        for f in all_features:
            tree_rows.append({
                "Name": f.get("name", ""),
                "Species": f.get("species", ""),
                "Age (yrs)": f.get("age_years", ""),
                "Girth (m)": f.get("circumference_m", ""),
                "Location": f.get("description", f.get("location_name", "")),
            })
        df_trees = pd.DataFrame(tree_rows)
        st.dataframe(df_trees, use_container_width=True, hide_index=True)

    # Download
    st.markdown("---")
    dl_rows = []
    for f in all_features:
        dl_rows.append({
            "name": f.get("name", ""),
            "species": f.get("species", ""),
            "age_years": f.get("age_years", ""),
            "circumference_m": f.get("circumference_m", ""),
            "lat": f.get("lat", ""),
            "lon": f.get("lon", ""),
            "location": f.get("description", f.get("location_name", "")),
        })
    df_dl = pd.DataFrame(dl_rows)
    csv_buf = io.StringIO()
    df_dl.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(dl_rows)} Ancient Trees (CSV)",
        data=csv_buf.getvalue(),
        file_name="terrascout_ancient_trees.csv",
        mime="text/csv",
        key="dl_ancient_trees",
    )


def _render_medicinal_gardens(lat: float, lon: float, radius_km: float):
    """Mode 7: Medicinal Plant Gardens."""
    st.markdown("#### Medicinal & Herb Gardens")
    st.caption(MAP_MODES["Medicinal Plant Gardens"]["description"])

    with st.spinner("Searching medicinal and herb gardens via OpenStreetMap..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "Medicinal Plant Gardens")

    if not features:
        st.warning(
            "No medicinal gardens found in this area. Try searching near cities "
            "with historic universities (London, Florence, Leiden, Padova)."
        )
        return

    _render_stats_row([
        ("Gardens Found", f"{len(features):,}"),
        ("Search Radius", f"{radius_km} km"),
    ])

    st.markdown("---")

    m = _build_folium_map(lat, lon, 12, radius_km)
    _add_markers(m, features, "#14b8a6")
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Notable gardens sidebar
    st.markdown("---")
    st.markdown("#### Garden Details")
    for f in features[:15]:
        safe_name = html.escape(str(f.get("name", "Unnamed")))
        safe_desc = html.escape(str(f.get("description", ""))[:200])
        safe_hours = html.escape(str(f.get("opening_hours", "")))
        safe_operator = html.escape(str(f.get("operator", "")))

        info_parts = []
        if safe_operator:
            info_parts.append(f"Operator: {safe_operator}")
        if safe_hours:
            info_parts.append(f"Hours: {safe_hours}")
        if safe_desc:
            info_parts.append(safe_desc)
        info_text = " | ".join(info_parts) if info_parts else "No details available"

        st.markdown(
            f'<div style="display:flex; align-items:center; margin-bottom:0.5rem;">'
            f'<div style="width:8px; height:40px; border-radius:4px; '
            f'background:#14b8a6; margin-right:0.75rem; flex-shrink:0;"></div>'
            f'<div>'
            f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{safe_name}</div>'
            f'<div style="color:#8b97b0; font-size:0.75rem;">{info_text}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    _render_data_table(
        features,
        ["name", "lat", "lon", "operator", "opening_hours", "description"],
        "medicinal_gardens",
    )


def _render_orchid_flower_gardens(lat: float, lon: float, radius_km: float):
    """Mode 8: Orchid & Flower Gardens."""
    st.markdown("#### Orchid & Flower Gardens")
    st.caption(MAP_MODES["Orchid & Flower Gardens"]["description"])

    with st.spinner("Searching flower gardens via OpenStreetMap..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "Orchid & Flower Gardens")

    if not features:
        st.warning(
            "No flower gardens found. Try searching near Keukenhof (Netherlands), "
            "Singapore, or other famous horticultural regions."
        )
        return

    # Classify by flower type from names/tags
    flower_types = {"rose": 0, "orchid": 0, "tulip": 0, "lily": 0, "other": 0}
    for f in features:
        name_lower = f.get("name", "").lower()
        tags_str = str(f.get("tags", {})).lower()
        classified = False
        for ftype in ["rose", "orchid", "tulip", "lily"]:
            if ftype in name_lower or ftype in tags_str:
                flower_types[ftype] += 1
                classified = True
                break
        if not classified:
            flower_types["other"] += 1

    metrics = [("Gardens Found", f"{len(features):,}")]
    for ftype, count in flower_types.items():
        if count > 0:
            metrics.append((ftype.title() + " Gardens", str(count)))
    _render_stats_row(metrics[:5])

    st.markdown("---")

    m = _build_folium_map(lat, lon, 11, radius_km)
    _add_markers(m, features, "#f43f5e")
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # Chart of flower types
    if any(v > 0 for v in flower_types.values()):
        st.markdown("---")
        col_chart, col_list = st.columns([1, 1])
        with col_chart:
            st.markdown("#### Garden Types")
            active_types = {k: v for k, v in flower_types.items() if v > 0}
            flower_colors = {
                "rose": "#f43f5e", "orchid": "#a855f7",
                "tulip": "#f59e0b", "lily": "#ec4899", "other": "#8b97b0",
            }
            _render_matplotlib_bar(
                labels=list(active_types.keys()),
                values=list(active_types.values()),
                colors=[flower_colors.get(k, "#8b97b0") for k in active_types],
                xlabel="Count",
                title="Flower Garden Types",
            )
        with col_list:
            st.markdown("#### Notable Gardens")
            for f in features[:10]:
                safe_name = html.escape(str(f.get("name", "Unnamed")))
                safe_desc = html.escape(str(f.get("description", ""))[:120])
                st.markdown(
                    f'<div style="display:flex; align-items:center; margin-bottom:0.4rem;">'
                    f'<div style="width:8px; height:36px; border-radius:4px; '
                    f'background:#f43f5e; margin-right:0.6rem; flex-shrink:0;"></div>'
                    f'<div>'
                    f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{safe_name}</div>'
                    f'<div style="color:#8b97b0; font-size:0.7rem;">{safe_desc}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    _render_data_table(
        features,
        ["name", "lat", "lon", "operator", "opening_hours", "description"],
        "flower_gardens",
    )


def _render_arboretums(lat: float, lon: float, radius_km: float):
    """Mode 9: Arboretums."""
    st.markdown("#### Arboretums & Tree Collections")
    st.caption(MAP_MODES["Arboretums"]["description"])

    with st.spinner("Searching arboretums via OpenStreetMap..."):
        features = _query_overpass_botanical(lat, lon, radius_km, "Arboretums")

    if not features:
        st.warning(
            "No arboretums found nearby. Try searching near Boston (Arnold), "
            "UK (Westonbirt), or Illinois (Morton)."
        )
        return

    # Collect operator stats
    operators = {}
    for f in features:
        op = f.get("operator", "Unknown")
        operators[op] = operators.get(op, 0) + 1

    _render_stats_row([
        ("Arboretums Found", f"{len(features):,}"),
        ("Operators", f"{len(operators)}"),
        ("Search Radius", f"{radius_km} km"),
    ])

    st.markdown("---")

    m = _build_folium_map(lat, lon, 11, radius_km)
    _add_markers(m, features, "#22c55e")
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Arboretum Details")

    for f in features[:12]:
        safe_name = html.escape(str(f.get("name", "Unnamed")))
        safe_operator = html.escape(str(f.get("operator", "")))
        safe_hours = html.escape(str(f.get("opening_hours", "")))
        safe_species = html.escape(str(f.get("species", "")))

        detail_parts = []
        if safe_operator:
            detail_parts.append(f"Managed by: {safe_operator}")
        if safe_hours:
            detail_parts.append(f"Hours: {safe_hours}")
        if safe_species:
            detail_parts.append(f"Focus: {safe_species}")
        detail_text = " | ".join(detail_parts) if detail_parts else f"{f['lat']:.4f}, {f['lon']:.4f}"

        st.markdown(
            f'<div style="display:flex; align-items:center; margin-bottom:0.5rem;">'
            f'<div style="width:8px; height:40px; border-radius:4px; '
            f'background:#22c55e; margin-right:0.75rem; flex-shrink:0;"></div>'
            f'<div>'
            f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{safe_name}</div>'
            f'<div style="color:#8b97b0; font-size:0.75rem;">{detail_text}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    _render_data_table(
        features,
        ["name", "lat", "lon", "operator", "opening_hours", "website", "description"],
        "arboretums",
    )


def _render_biomes_hotspots(lat: float, lon: float, radius_km: float):
    """Mode 10: Biomes & Biodiversity Hotspots."""
    st.markdown("#### Biomes & Biodiversity Hotspots")
    st.caption(MAP_MODES["Biomes & Biodiversity Hotspots"]["description"])

    with st.spinner("Searching protected areas via OpenStreetMap..."):
        osm_features = _query_overpass_botanical(
            lat, lon, radius_km, "Biomes & Biodiversity Hotspots"
        )

    # Curated hotspots
    hotspots = CURATED_BIODIVERSITY_HOTSPOTS

    total_endemic = sum(h["endemic_plants"] for h in hotspots)
    critical = sum(1 for h in hotspots if h["threat_level"] == "Critical")

    _render_stats_row([
        ("OSM Protected Areas", f"{len(osm_features):,}"),
        ("Global Hotspots (curated)", f"{len(hotspots)}"),
        ("Total Endemic Plants (est.)", f"{total_endemic:,}"),
        ("Critically Threatened", f"{critical}"),
    ])

    st.markdown("---")

    # Global map with curated hotspots + OSM features
    m = _build_folium_map(lat, lon, 3)

    # Curated hotspot markers (larger)
    threat_colors = {"Critical": "#ef4444", "Endangered": "#f59e0b", "Vulnerable": "#f97316"}
    for hs in hotspots:
        safe_name = html.escape(hs["name"])
        safe_region = html.escape(hs["region"])
        threat = hs["threat_level"]
        color = threat_colors.get(threat, "#8b97b0")
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong style="color:{color};">{safe_name}</strong><br/>'
            f'<span style="font-size:0.8rem;">{safe_region}</span><br/>'
            f'<span style="font-size:0.75rem;">Area: {hs["area_km2"]:,} km&sup2;</span><br/>'
            f'<span style="font-size:0.75rem;">Endemic plants: ~{hs["endemic_plants"]:,}</span><br/>'
            f'<span style="font-size:0.75rem; color:{color};">Threat: {html.escape(threat)}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[hs["lat"], hs["lon"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(m)

    # OSM protected areas (smaller, cyan)
    _add_markers(m, osm_features, "#06b6d4")

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-top:0.25rem;">'
        '<span style="color:#ef4444; font-size:0.8rem;">&#9679; Critical</span>'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9679; Endangered</span>'
        '<span style="color:#06b6d4; font-size:0.8rem;">&#9679; OSM Protected Areas</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Charts
    st.markdown("---")
    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        st.markdown("#### Endemic Plants by Hotspot")
        sorted_hs = sorted(hotspots, key=lambda x: x["endemic_plants"], reverse=True)
        _render_matplotlib_bar(
            labels=[h["name"] for h in sorted_hs],
            values=[h["endemic_plants"] for h in sorted_hs],
            colors=[threat_colors.get(h["threat_level"], "#8b97b0") for h in sorted_hs],
            xlabel="Endemic Plant Species",
            title="Global Biodiversity Hotspots",
        )

    with col_table:
        st.markdown("#### Hotspot Details")
        hs_rows = []
        for h in sorted_hs:
            hs_rows.append({
                "Hotspot": h["name"],
                "Region": h["region"],
                "Area (km2)": f"{h['area_km2']:,}",
                "Endemic Plants": f"{h['endemic_plants']:,}",
                "Threat Level": h["threat_level"],
            })
        df_hs = pd.DataFrame(hs_rows)
        st.dataframe(df_hs, use_container_width=True, hide_index=True)

    # Full download
    st.markdown("---")
    all_dl_rows = []
    for h in hotspots:
        all_dl_rows.append({
            "name": h["name"],
            "region": h["region"],
            "lat": h["lat"],
            "lon": h["lon"],
            "area_km2": h["area_km2"],
            "endemic_plants": h["endemic_plants"],
            "threat_level": h["threat_level"],
        })
    for f in osm_features:
        all_dl_rows.append({
            "name": f.get("name", ""),
            "region": "OSM Protected Area",
            "lat": f.get("lat", ""),
            "lon": f.get("lon", ""),
            "area_km2": "",
            "endemic_plants": "",
            "threat_level": "",
        })
    df_all = pd.DataFrame(all_dl_rows)
    csv_buf = io.StringIO()
    df_all.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(all_dl_rows)} Records (CSV)",
        data=csv_buf.getvalue(),
        file_name="terrascout_biomes_hotspots.csv",
        mime="text/csv",
        key="dl_biomes",
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

_MODE_RENDERERS = {
    "World Botanical Gardens": _render_world_botanical_gardens,
    "National Parks": _render_national_parks,
    "Rainforest Reserves": _render_rainforest_reserves,
    "Endemic Plant Hotspots": _render_endemic_hotspots,
    "Cherry Blossom Sites": _render_cherry_blossom,
    "Ancient & Sacred Trees": _render_ancient_trees,
    "Medicinal Plant Gardens": _render_medicinal_gardens,
    "Orchid & Flower Gardens": _render_orchid_flower_gardens,
    "Arboretums": _render_arboretums,
    "Biomes & Biodiversity Hotspots": _render_biomes_hotspots,
}


def render_botanical_maps_tab():
    """Main render function for the Botanical & Gardens Explorer tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>&#127793; Botanical &amp; Gardens Explorer</h4>"
        "<p>Discover botanical gardens, nature reserves, ancient trees, "
        "cherry blossom sites, biodiversity hotspots, and plant geography "
        "worldwide using OpenStreetMap and GBIF data.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 1: Mode & Location Selection
    # ══════════════════════════════════════════
    st.markdown("#### Map Mode")
    mode_names = list(MAP_MODES.keys())
    selected_mode = st.selectbox(
        "Select exploration mode",
        mode_names,
        key="bot_mode",
        help="Each mode focuses on a different aspect of plant geography and conservation.",
    )

    mode_info = MAP_MODES[selected_mode]
    st.caption(mode_info["description"])

    st.markdown("#### Location")

    # Preset selector for the chosen mode
    presets = MODE_PRESETS.get(selected_mode, {"Custom": None})
    preset_name = st.selectbox(
        "Famous Locations",
        list(presets.keys()),
        key="bot_preset",
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    default_lat, default_lon, default_radius = 51.4787, -0.2956, 10
    if preset_name != "Custom" and presets.get(preset_name):
        p = presets[preset_name]
        default_lat = p["lat"]
        default_lon = p["lon"]
        default_radius = p["radius"]

    with col1:
        bot_lat = st.number_input(
            "Latitude", value=default_lat, format="%.4f",
            min_value=-90.0, max_value=90.0, key="bot_lat",
        )
    with col2:
        bot_lon = st.number_input(
            "Longitude", value=default_lon, format="%.4f",
            min_value=-180.0, max_value=180.0, key="bot_lon",
        )
    with col3:
        bot_radius = st.slider(
            "Radius (km)", 1, 100, default_radius, key="bot_radius",
            help="Search radius around center point.",
        )

    if preset_name != "Custom" and presets.get(preset_name):
        p = presets[preset_name]
        bot_lat = p["lat"]
        bot_lon = p["lon"]
        bot_radius = p["radius"]

    # Search button
    if st.button("Explore Botanical Sites", key="bot_search", width="stretch"):
        st.session_state.bot_params = {
            "lat": bot_lat,
            "lon": bot_lon,
            "radius": bot_radius,
            "mode": selected_mode,
        }

    if "bot_params" not in st.session_state:
        st.info(
            "Select a map mode and location, then click **Explore Botanical Sites** "
            "to discover gardens, parks, and plant-related features."
        )
        return

    bp = st.session_state.bot_params

    # ══════════════════════════════════════════
    # SECTION 2: Render Selected Mode
    # ══════════════════════════════════════════
    st.markdown("---")

    renderer = _MODE_RENDERERS.get(bp["mode"])
    if renderer:
        renderer(bp["lat"], bp["lon"], bp["radius"])
    else:
        st.error(f"Unknown mode: {bp['mode']}")
