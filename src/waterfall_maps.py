# -*- coding: utf-8 -*-
"""
Waterfalls & Great Rivers Explorer module for TerraScout AI.
Provides 10 curated map modes covering famous waterfalls, river systems,
deltas, gorges, rapids, confluences, historic crossings, endangered rivers,
and sacred rivers worldwide. Uses hardcoded scholarly/geographic data
supplemented by Overpass API queries for live OSM enrichment.
All free, no API key required.
"""

import io
import math
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

# ═══════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE  (TerraScout dark theme)
# ═══════════════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_BORDER = "#2a3550"
_TEXT_PRI = "#e8ecf4"
_TEXT_SEC = "#8b97b0"
_TEXT_MUT = "#5a6580"
_ACCENT = "#06b6d4"

# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY COLOURS
# ═══════════════════════════════════════════════════════════════════════════════
TYPE_COLORS = {
    "Plunge": "#06b6d4",
    "Horsetail": "#3b82f6",
    "Cataract": "#8b5cf6",
    "Block": "#10b981",
    "Tiered": "#f59e0b",
    "Cascade": "#38bdf8",
    "Fan": "#ec4899",
    "Segmented": "#a855f7",
    "Frozen": "#94a3b8",
    "Multi-step": "#14b8a6",
}

RIVER_COLORS = {
    "Amazon": "#10b981",
    "Nile": "#f59e0b",
    "Mississippi": "#3b82f6",
    "Yangtze": "#ef4444",
    "Danube": "#8b5cf6",
    "Congo": "#06b6d4",
    "Ganges": "#ec4899",
    "Mekong": "#14b8a6",
    "Volga": "#38bdf8",
    "Rhine": "#a855f7",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. WORLD'S GREATEST WATERFALLS  (top 50 by height/flow)
# ═══════════════════════════════════════════════════════════════════════════════
GREATEST_WATERFALLS = [
    {"name": "Angel Falls", "lat": 5.9701, "lon": -62.5362, "country": "Venezuela", "height_m": 979, "type": "Plunge", "river": "Churun", "note": "World's highest uninterrupted waterfall; drops from Auyantepui"},
    {"name": "Tugela Falls", "lat": -28.7525, "lon": 28.9489, "country": "South Africa", "height_m": 948, "type": "Tiered", "river": "Tugela", "note": "Five-tiered drop in Drakensberg; second tallest on Earth"},
    {"name": "Tres Hermanas Falls", "lat": -14.3833, "lon": -72.2167, "country": "Peru", "height_m": 914, "type": "Tiered", "river": "Cutivireni", "note": "Three-tiered plunge in remote Junin rainforest"},
    {"name": "Olo'upena Falls", "lat": 21.1000, "lon": -156.8500, "country": "USA (Hawaii)", "height_m": 900, "type": "Plunge", "river": "Seasonal", "note": "On the sea cliffs of Molokai; 4th tallest globally"},
    {"name": "Yumbilla Falls", "lat": -5.9333, "lon": -77.9000, "country": "Peru", "height_m": 896, "type": "Tiered", "river": "Yumbilla", "note": "Five-tiered fall in Amazonas region; discovered 2007"},
    {"name": "Vinnufossen", "lat": 62.1497, "lon": 7.1592, "country": "Norway", "height_m": 860, "type": "Horsetail", "river": "Vinnu", "note": "Tallest waterfall in Europe; fed by Vinnufjellet glacier"},
    {"name": "Balatifossen", "lat": 60.2500, "lon": 6.6333, "country": "Norway", "height_m": 850, "type": "Horsetail", "river": "Balati", "note": "Multi-stage cascade in Ullensvang, Hardangerfjord area"},
    {"name": "Pu'uka'oku Falls", "lat": 21.1100, "lon": -156.8600, "country": "USA (Hawaii)", "height_m": 840, "type": "Plunge", "river": "Seasonal", "note": "Sea-cliff waterfall on Molokai's north coast"},
    {"name": "James Bruce Falls", "lat": 50.4500, "lon": -124.7000, "country": "Canada", "height_m": 840, "type": "Plunge", "river": "Seasonal", "note": "Tallest waterfall in Canada, in Princess Louisa Inlet"},
    {"name": "Browne Falls", "lat": -45.3000, "lon": 167.1500, "country": "New Zealand", "height_m": 836, "type": "Plunge", "river": "Browne Stream", "note": "Falls into Doubtful Sound, Fiordland; seasonal flow"},
    {"name": "Strupenfossen", "lat": 61.6000, "lon": 6.8000, "country": "Norway", "height_m": 820, "type": "Horsetail", "river": "Strupen", "note": "In the Stryn municipality, Sogn og Fjordane"},
    {"name": "Ramnefjellsfossen", "lat": 61.7000, "lon": 6.8000, "country": "Norway", "height_m": 818, "type": "Horsetail", "river": "Ramnefjell", "note": "Also called Utigardfossen; near Jostedalsbreen glacier"},
    {"name": "Waihilau Falls", "lat": 19.9500, "lon": -155.1700, "country": "USA (Hawaii)", "height_m": 792, "type": "Plunge", "river": "Waihilau Stream", "note": "In Waimanu Valley on Hawaii's Big Island"},
    {"name": "Colonial Creek Falls", "lat": 48.6900, "lon": -121.1100, "country": "USA (Washington)", "height_m": 788, "type": "Tiered", "river": "Colonial Creek", "note": "Tallest in contiguous US; in North Cascades"},
    {"name": "Mongefossen", "lat": 62.2500, "lon": 7.2500, "country": "Norway", "height_m": 773, "type": "Horsetail", "river": "Monge", "note": "Near Andalsnes in Rauma municipality"},
    {"name": "Gocta Cataracts", "lat": -5.9500, "lon": -77.8833, "country": "Peru", "height_m": 771, "type": "Tiered", "river": "Gocta", "note": "Two-drop fall in Amazonas; discovered internationally 2005"},
    {"name": "Kaieteur Falls", "lat": 5.1756, "lon": -59.4817, "country": "Guyana", "height_m": 226, "type": "Plunge", "river": "Potaro", "note": "World's largest single-drop by volume; 5x Niagara height"},
    {"name": "Niagara Falls", "lat": 43.0799, "lon": -79.0747, "country": "USA/Canada", "height_m": 51, "type": "Block", "river": "Niagara", "note": "Most famous waterfall; 3160 tonnes/sec flow rate; Horseshoe Falls"},
    {"name": "Victoria Falls", "lat": -17.9243, "lon": 25.8572, "country": "Zambia/Zimbabwe", "height_m": 108, "type": "Block", "river": "Zambezi", "note": "Mosi-oa-Tunya ('The Smoke That Thunders'); largest curtain of water"},
    {"name": "Iguazu Falls", "lat": -25.6953, "lon": -54.4367, "country": "Argentina/Brazil", "height_m": 82, "type": "Cataract", "river": "Iguazu", "note": "275 individual drops over 2.7 km; Devil's Throat centrepiece"},
    {"name": "Dettifoss", "lat": 65.8147, "lon": -16.3844, "country": "Iceland", "height_m": 44, "type": "Block", "river": "Jokulsa a Fjollum", "note": "Most powerful waterfall in Europe; 500 m3/s avg"},
    {"name": "Gullfoss", "lat": 64.3271, "lon": -20.1199, "country": "Iceland", "height_m": 32, "type": "Cataract", "river": "Hvita", "note": "Two-stage plunge into a 32m-deep crevice; Golden Circle"},
    {"name": "Godafoss", "lat": 65.6826, "lon": -17.5502, "country": "Iceland", "height_m": 12, "type": "Block", "river": "Skjalfandafljot", "note": "Waterfall of the Gods; Norse pagan idols thrown in 1000 AD"},
    {"name": "Yosemite Falls", "lat": 37.7564, "lon": -119.5964, "country": "USA (California)", "height_m": 739, "type": "Tiered", "river": "Yosemite Creek", "note": "Three-section fall; tallest in Yosemite; seasonal flow"},
    {"name": "Sutherland Falls", "lat": -44.8167, "lon": 167.7333, "country": "New Zealand", "height_m": 580, "type": "Tiered", "river": "Arthur River", "note": "Three-tiered drop in Milford Sound area; Fiordland NP"},
    {"name": "Jog Falls", "lat": 14.2294, "lon": 74.8127, "country": "India", "height_m": 253, "type": "Plunge", "river": "Sharavathi", "note": "Second-highest plunge in India; four distinct cascades"},
    {"name": "Ban Gioc-Detian Falls", "lat": 22.8539, "lon": 106.7236, "country": "Vietnam/China", "height_m": 30, "type": "Cataract", "river": "Quay Son", "note": "Transnational falls on Vietnam-China border; 300m wide"},
    {"name": "Plitvice Waterfalls", "lat": 44.9053, "lon": 15.6089, "country": "Croatia", "height_m": 78, "type": "Cascade", "river": "Korana", "note": "Veliki Slap (Great Waterfall) plus travertine terraces; UNESCO"},
    {"name": "Havasu Falls", "lat": 36.2553, "lon": -112.6979, "country": "USA (Arizona)", "height_m": 30, "type": "Plunge", "river": "Havasu Creek", "note": "Turquoise travertine pool in Grand Canyon; Havasupai"},
    {"name": "Seljalandsfoss", "lat": 63.6156, "lon": -19.9886, "country": "Iceland", "height_m": 60, "type": "Plunge", "river": "Seljalands", "note": "Walk behind the curtain; fed by Eyjafjallajokull glacier"},
    {"name": "Skogafoss", "lat": 63.5321, "lon": -19.5133, "country": "Iceland", "height_m": 60, "type": "Block", "river": "Skoga", "note": "25m wide curtain; Viking legend of hidden treasure chest"},
    {"name": "Huangguoshu Falls", "lat": 25.9942, "lon": 105.6656, "country": "China", "height_m": 77, "type": "Cataract", "river": "Baishui", "note": "Largest waterfall in Asia; curtain cave behind falls"},
    {"name": "Rhine Falls", "lat": 47.6778, "lon": 8.6150, "country": "Switzerland", "height_m": 23, "type": "Cataract", "river": "Rhine", "note": "Largest plain waterfall in Europe; 150m wide, 600 m3/s"},
    {"name": "Nohkalikai Falls", "lat": 25.2714, "lon": 91.6864, "country": "India", "height_m": 340, "type": "Plunge", "river": "Nohkalikai", "note": "Tallest plunge waterfall in India; Meghalaya, wettest place on Earth"},
    {"name": "Salto Para Falls", "lat": 5.6500, "lon": -62.1833, "country": "Venezuela", "height_m": 64, "type": "Cataract", "river": "Caura", "note": "One of world's widest falls; 5.6 km across in flood"},
    {"name": "Wallaman Falls", "lat": -18.6200, "lon": 145.8100, "country": "Australia", "height_m": 268, "type": "Plunge", "river": "Stony Creek", "note": "Australia's highest single-drop waterfall; in wet tropics"},
    {"name": "Cascata delle Marmore", "lat": 42.5530, "lon": 12.7145, "country": "Italy", "height_m": 165, "type": "Tiered", "river": "Velino", "note": "Man-made by Romans in 271 BC; tallest in Italy; 3 tiers"},
    {"name": "Giessbach Falls", "lat": 46.7292, "lon": 7.9681, "country": "Switzerland", "height_m": 500, "type": "Cascade", "river": "Giessbach", "note": "14 stages descending into Lake Brienz; illuminated at night"},
    {"name": "Krimml Falls", "lat": 47.2069, "lon": 12.1722, "country": "Austria", "height_m": 380, "type": "Tiered", "river": "Krimmler Ache", "note": "Highest waterfall in Austria; three tiers in Hohe Tauern NP"},
    {"name": "Kuang Si Falls", "lat": 19.7487, "lon": 101.9943, "country": "Laos", "height_m": 60, "type": "Cascade", "river": "Kuang Si", "note": "Turquoise travertine pools near Luang Prabang; tiered cascade"},
    {"name": "Multnomah Falls", "lat": 45.5762, "lon": -122.1158, "country": "USA (Oregon)", "height_m": 189, "type": "Tiered", "river": "Multnomah Creek", "note": "Two-tiered icon of Columbia River Gorge; year-round flow"},
    {"name": "Nachi Falls", "lat": 33.6672, "lon": 135.8914, "country": "Japan", "height_m": 133, "type": "Plunge", "river": "Nachi River", "note": "Sacred Shinto waterfall; tallest single-drop in Japan"},
    {"name": "Dudhsagar Falls", "lat": 15.3144, "lon": 74.3143, "country": "India", "height_m": 310, "type": "Tiered", "river": "Mandovi", "note": "Sea of Milk; four-tiered monsoon spectacle; railway bridge"},
    {"name": "Cataratas del Tequendama", "lat": 4.5750, "lon": -74.2950, "country": "Colombia", "height_m": 132, "type": "Plunge", "river": "Bogota", "note": "Near Bogota; Muisca sacred site; abandoned hotel overlook"},
    {"name": "Shoshone Falls", "lat": 42.5928, "lon": -114.4000, "country": "USA (Idaho)", "height_m": 65, "type": "Block", "river": "Snake", "note": "Niagara of the West; 274m wide; spring snowmelt peak"},
    {"name": "Erawan Falls", "lat": 14.3667, "lon": 98.8667, "country": "Thailand", "height_m": 171, "type": "Cascade", "river": "Erawan", "note": "Seven-tiered emerald cascade; named for three-headed elephant"},
    {"name": "Langfossen", "lat": 59.8433, "lon": 6.3367, "country": "Norway", "height_m": 612, "type": "Horsetail", "river": "Langfoss", "note": "Roadside waterfall into Akrafjorden; one of most beautiful"},
    {"name": "Palouse Falls", "lat": 46.6639, "lon": -118.2256, "country": "USA (Washington)", "height_m": 61, "type": "Plunge", "river": "Palouse", "note": "Carved by Ice Age Missoula Floods; basalt amphitheatre"},
    {"name": "Cascata di Toce", "lat": 46.3925, "lon": 8.3600, "country": "Italy", "height_m": 143, "type": "Plunge", "river": "Toce", "note": "Alps waterfall in Val Formazza; controlled by dam upstream"},
    {"name": "Agua Azul Cascades", "lat": 17.2569, "lon": -92.1153, "country": "Mexico", "height_m": 30, "type": "Cascade", "river": "Xanil", "note": "Blue-water travertine terraces in Chiapas jungle"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 2. TALLEST WATERFALLS  (ranked by total drop)
# ═══════════════════════════════════════════════════════════════════════════════
TALLEST_WATERFALLS = [
    {"rank": 1, "name": "Angel Falls", "lat": 5.9701, "lon": -62.5362, "country": "Venezuela", "total_m": 979, "longest_drop_m": 807, "type": "Plunge"},
    {"rank": 2, "name": "Tugela Falls", "lat": -28.7525, "lon": 28.9489, "country": "South Africa", "total_m": 948, "longest_drop_m": 411, "type": "Tiered"},
    {"rank": 3, "name": "Tres Hermanas Falls", "lat": -14.3833, "lon": -72.2167, "country": "Peru", "total_m": 914, "longest_drop_m": 350, "type": "Tiered"},
    {"rank": 4, "name": "Olo'upena Falls", "lat": 21.1000, "lon": -156.8500, "country": "USA", "total_m": 900, "longest_drop_m": 900, "type": "Plunge"},
    {"rank": 5, "name": "Yumbilla Falls", "lat": -5.9333, "lon": -77.9000, "country": "Peru", "total_m": 896, "longest_drop_m": 400, "type": "Tiered"},
    {"rank": 6, "name": "Vinnufossen", "lat": 62.1497, "lon": 7.1592, "country": "Norway", "total_m": 860, "longest_drop_m": 420, "type": "Horsetail"},
    {"rank": 7, "name": "Balatifossen", "lat": 60.2500, "lon": 6.6333, "country": "Norway", "total_m": 850, "longest_drop_m": 452, "type": "Horsetail"},
    {"rank": 8, "name": "Pu'uka'oku Falls", "lat": 21.1100, "lon": -156.8600, "country": "USA", "total_m": 840, "longest_drop_m": 840, "type": "Plunge"},
    {"rank": 9, "name": "James Bruce Falls", "lat": 50.4500, "lon": -124.7000, "country": "Canada", "total_m": 840, "longest_drop_m": 840, "type": "Plunge"},
    {"rank": 10, "name": "Browne Falls", "lat": -45.3000, "lon": 167.1500, "country": "New Zealand", "total_m": 836, "longest_drop_m": 244, "type": "Plunge"},
    {"rank": 11, "name": "Strupenfossen", "lat": 61.6000, "lon": 6.8000, "country": "Norway", "total_m": 820, "longest_drop_m": 300, "type": "Horsetail"},
    {"rank": 12, "name": "Ramnefjellsfossen", "lat": 61.7000, "lon": 6.8000, "country": "Norway", "total_m": 818, "longest_drop_m": 600, "type": "Horsetail"},
    {"rank": 13, "name": "Waihilau Falls", "lat": 19.9500, "lon": -155.1700, "country": "USA", "total_m": 792, "longest_drop_m": 792, "type": "Plunge"},
    {"rank": 14, "name": "Colonial Creek Falls", "lat": 48.6900, "lon": -121.1100, "country": "USA", "total_m": 788, "longest_drop_m": 350, "type": "Tiered"},
    {"rank": 15, "name": "Mongefossen", "lat": 62.2500, "lon": 7.2500, "country": "Norway", "total_m": 773, "longest_drop_m": 400, "type": "Horsetail"},
    {"rank": 16, "name": "Gocta Cataracts", "lat": -5.9500, "lon": -77.8833, "country": "Peru", "total_m": 771, "longest_drop_m": 540, "type": "Tiered"},
    {"rank": 17, "name": "Yosemite Falls", "lat": 37.7564, "lon": -119.5964, "country": "USA", "total_m": 739, "longest_drop_m": 436, "type": "Tiered"},
    {"rank": 18, "name": "Mutarazi Falls", "lat": -19.0833, "lon": 32.7667, "country": "Zimbabwe", "total_m": 762, "longest_drop_m": 479, "type": "Plunge"},
    {"rank": 19, "name": "Kjelfossen", "lat": 60.8300, "lon": 6.9300, "country": "Norway", "total_m": 755, "longest_drop_m": 149, "type": "Horsetail"},
    {"rank": 20, "name": "Johannesburgfossen", "lat": 60.2000, "lon": 6.7000, "country": "Norway", "total_m": 731, "longest_drop_m": 250, "type": "Horsetail"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 3. GREAT RIVER SYSTEMS  (course waypoints)
# ═══════════════════════════════════════════════════════════════════════════════
GREAT_RIVERS = {
    "Amazon": {
        "length_km": 6992, "basin_km2": 7050000, "discharge_m3s": 209000,
        "color": "#10b981", "source": "Mantaro River, Andes, Peru",
        "mouth": "Atlantic Ocean, Brazil",
        "note": "Largest river by discharge; 20% of world's freshwater; 1100+ tributaries",
        "waypoints": [
            {"name": "Source (Mantaro)", "lat": -12.18, "lon": -75.59},
            {"name": "Iquitos", "lat": -3.75, "lon": -73.25},
            {"name": "Manaus (Rio Negro confluence)", "lat": -3.12, "lon": -60.02},
            {"name": "Santarem", "lat": -2.44, "lon": -54.71},
            {"name": "Belem (Mouth)", "lat": -1.46, "lon": -48.50},
        ],
    },
    "Nile": {
        "length_km": 6650, "basin_km2": 3349000, "discharge_m3s": 2830,
        "color": "#f59e0b", "source": "Lake Victoria / Burundi highlands",
        "mouth": "Mediterranean Sea, Egypt",
        "note": "Longest river (disputed with Amazon); cradle of Egyptian civilization",
        "waypoints": [
            {"name": "Source (Kagera, Burundi)", "lat": -2.27, "lon": 29.33},
            {"name": "Lake Victoria outlet (Jinja)", "lat": 0.44, "lon": 33.20},
            {"name": "Khartoum (Blue/White Nile)", "lat": 15.60, "lon": 32.53},
            {"name": "Aswan (High Dam)", "lat": 24.09, "lon": 32.90},
            {"name": "Luxor", "lat": 25.69, "lon": 32.64},
            {"name": "Cairo (Delta apex)", "lat": 30.04, "lon": 31.24},
        ],
    },
    "Mississippi-Missouri": {
        "length_km": 6275, "basin_km2": 2980000, "discharge_m3s": 16800,
        "color": "#3b82f6", "source": "Lake Itasca, Minnesota",
        "mouth": "Gulf of Mexico, Louisiana",
        "note": "Drains 31 US states and 2 Canadian provinces; Mark Twain's great river",
        "waypoints": [
            {"name": "Source (Lake Itasca)", "lat": 47.24, "lon": -95.21},
            {"name": "Minneapolis-St. Paul", "lat": 44.98, "lon": -93.27},
            {"name": "St. Louis (Missouri confluence)", "lat": 38.63, "lon": -90.20},
            {"name": "Memphis", "lat": 35.15, "lon": -90.05},
            {"name": "Vicksburg", "lat": 32.35, "lon": -90.88},
            {"name": "New Orleans", "lat": 29.95, "lon": -90.07},
            {"name": "Delta (Mouth)", "lat": 29.15, "lon": -89.25},
        ],
    },
    "Yangtze": {
        "length_km": 6300, "basin_km2": 1800000, "discharge_m3s": 30000,
        "color": "#ef4444", "source": "Tanggula Mountains, Qinghai, China",
        "mouth": "East China Sea, Shanghai",
        "note": "Longest river in Asia; Three Gorges Dam; 400+ million in basin",
        "waypoints": [
            {"name": "Source (Tanggula Mtns)", "lat": 33.43, "lon": 91.17},
            {"name": "Tiger Leaping Gorge", "lat": 27.17, "lon": 100.17},
            {"name": "Chongqing", "lat": 29.56, "lon": 106.55},
            {"name": "Three Gorges Dam", "lat": 30.82, "lon": 111.00},
            {"name": "Wuhan", "lat": 30.59, "lon": 114.31},
            {"name": "Nanjing", "lat": 32.06, "lon": 118.80},
            {"name": "Shanghai (Mouth)", "lat": 31.39, "lon": 121.87},
        ],
    },
    "Danube": {
        "length_km": 2850, "basin_km2": 817000, "discharge_m3s": 6500,
        "color": "#8b5cf6", "source": "Black Forest, Germany",
        "mouth": "Black Sea, Romania",
        "note": "Europe's second-longest; flows through 10 countries; Blue Danube waltz",
        "waypoints": [
            {"name": "Source (Donaueschingen)", "lat": 47.95, "lon": 8.50},
            {"name": "Vienna", "lat": 48.21, "lon": 16.37},
            {"name": "Bratislava", "lat": 48.15, "lon": 17.11},
            {"name": "Budapest", "lat": 47.50, "lon": 19.04},
            {"name": "Belgrade", "lat": 44.82, "lon": 20.46},
            {"name": "Iron Gates Gorge", "lat": 44.67, "lon": 22.52},
            {"name": "Delta (Black Sea)", "lat": 45.15, "lon": 29.67},
        ],
    },
    "Congo": {
        "length_km": 4700, "basin_km2": 3680000, "discharge_m3s": 41000,
        "color": "#06b6d4", "source": "Chambeshi River, Zambia",
        "mouth": "Atlantic Ocean, DRC/Angola",
        "note": "Deepest river (220m+); second by discharge; crosses equator twice",
        "waypoints": [
            {"name": "Source (Chambeshi)", "lat": -10.55, "lon": 28.72},
            {"name": "Kisangani", "lat": 0.52, "lon": 25.20},
            {"name": "Boyoma Falls", "lat": 0.50, "lon": 25.21},
            {"name": "Kinshasa/Brazzaville", "lat": -4.32, "lon": 15.31},
            {"name": "Mouth (Atlantic)", "lat": -6.07, "lon": 12.40},
        ],
    },
    "Ganges": {
        "length_km": 2525, "basin_km2": 1080000, "discharge_m3s": 12000,
        "color": "#ec4899", "source": "Gangotri Glacier, Himalayas",
        "mouth": "Bay of Bengal, Bangladesh",
        "note": "Sacred to Hinduism; 400+ million depend on it; most populated basin",
        "waypoints": [
            {"name": "Source (Gangotri Glacier)", "lat": 30.99, "lon": 79.08},
            {"name": "Haridwar", "lat": 29.95, "lon": 78.16},
            {"name": "Allahabad (Yamuna confluence)", "lat": 25.43, "lon": 81.85},
            {"name": "Varanasi", "lat": 25.32, "lon": 83.01},
            {"name": "Patna", "lat": 25.61, "lon": 85.14},
            {"name": "Delta (Bangladesh)", "lat": 22.00, "lon": 89.50},
        ],
    },
    "Mekong": {
        "length_km": 4350, "basin_km2": 795000, "discharge_m3s": 16000,
        "color": "#14b8a6", "source": "Tibetan Plateau, China",
        "mouth": "South China Sea, Vietnam",
        "note": "Mother of Water; flows through 6 countries; giant catfish habitat",
        "waypoints": [
            {"name": "Source (Tibetan Plateau)", "lat": 33.45, "lon": 94.42},
            {"name": "Luang Prabang, Laos", "lat": 19.89, "lon": 102.13},
            {"name": "Vientiane", "lat": 17.97, "lon": 102.63},
            {"name": "Phnom Penh", "lat": 11.56, "lon": 104.92},
            {"name": "Delta (Ho Chi Minh City)", "lat": 10.05, "lon": 106.68},
        ],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 4. RIVER DELTAS
# ═══════════════════════════════════════════════════════════════════════════════
RIVER_DELTAS = [
    {"name": "Ganges-Brahmaputra Delta", "lat": 22.50, "lon": 89.50, "river": "Ganges + Brahmaputra", "country": "Bangladesh/India", "area_km2": 105000, "type": "Tidal", "note": "Largest delta on Earth; Sundarbans mangroves; 150 million residents"},
    {"name": "Mekong Delta", "lat": 10.00, "lon": 106.00, "river": "Mekong", "country": "Vietnam", "area_km2": 40500, "type": "Arcuate", "note": "Rice bowl of SE Asia; nine river branches; 18 million people"},
    {"name": "Mississippi River Delta", "lat": 29.15, "lon": -89.25, "river": "Mississippi", "country": "USA", "area_km2": 28600, "type": "Bird-foot", "note": "Classic bird-foot delta; losing 40 km2/year to subsidence and erosion"},
    {"name": "Nile Delta", "lat": 31.05, "lon": 30.94, "river": "Nile", "country": "Egypt", "area_km2": 24000, "type": "Arcuate", "note": "Breadbasket of ancient Egypt; Rosetta and Damietta branches; sinking"},
    {"name": "Amazon Delta", "lat": -0.50, "lon": -50.00, "river": "Amazon", "country": "Brazil", "area_km2": 20000, "type": "Estuarine", "note": "Marajo Island (40,100 km2) in mouth; tidal bore (pororoca)"},
    {"name": "Niger Delta", "lat": 5.00, "lon": 6.00, "river": "Niger", "country": "Nigeria", "area_km2": 36000, "type": "Arcuate", "note": "Oil-rich; largest wetland in Africa; mangrove and freshwater swamps"},
    {"name": "Danube Delta", "lat": 45.15, "lon": 29.50, "river": "Danube", "country": "Romania/Ukraine", "area_km2": 4150, "type": "Bird-foot", "note": "UNESCO Biosphere Reserve; 300 bird species; reed-bed labyrinth"},
    {"name": "Irrawaddy Delta", "lat": 16.00, "lon": 95.50, "river": "Irrawaddy", "country": "Myanmar", "area_km2": 40000, "type": "Arcuate", "note": "Rice-producing heartland; devastated by Cyclone Nargis 2008"},
    {"name": "Lena Delta", "lat": 73.00, "lon": 127.00, "river": "Lena", "country": "Russia", "area_km2": 32000, "type": "Arcuate", "note": "Arctic permafrost delta; Lena Pillars UNESCO site upstream"},
    {"name": "Okavango Delta", "lat": -19.50, "lon": 22.90, "river": "Okavango", "country": "Botswana", "area_km2": 22000, "type": "Inland alluvial fan", "note": "World's largest inland delta; never reaches the sea; UNESCO site"},
    {"name": "Volga Delta", "lat": 45.70, "lon": 48.70, "river": "Volga", "country": "Russia", "area_km2": 27000, "type": "Arcuate", "note": "Europe's largest delta; Caspian Sea outlet; lotus fields"},
    {"name": "Indus Delta", "lat": 24.00, "lon": 67.50, "river": "Indus", "country": "Pakistan", "area_km2": 41400, "type": "Arcuate", "note": "Shrinking due to upstream dams; mangrove forests; ancient Sindh"},
    {"name": "Rhine-Meuse-Scheldt Delta", "lat": 51.90, "lon": 4.00, "river": "Rhine/Meuse/Scheldt", "country": "Netherlands", "area_km2": 25000, "type": "Compound", "note": "Heavily engineered; Delta Works sea-defence; below sea level"},
    {"name": "Pearl River Delta", "lat": 22.50, "lon": 113.50, "river": "Pearl (Zhujiang)", "country": "China", "area_km2": 8000, "type": "Estuarine", "note": "Guangzhou, Shenzhen, Hong Kong, Macau; 70 million people megacity region"},
    {"name": "Yukon-Kuskokwim Delta", "lat": 61.50, "lon": -163.00, "river": "Yukon/Kuskokwim", "country": "USA (Alaska)", "area_km2": 32000, "type": "Compound", "note": "Largest delta in Americas; Yup'ik homeland; tundra and permafrost"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 5. GORGES & CANYONS
# ═══════════════════════════════════════════════════════════════════════════════
GORGES_CANYONS = [
    {"name": "Grand Canyon", "lat": 36.1069, "lon": -112.1129, "country": "USA", "depth_m": 1857, "length_km": 446, "river": "Colorado", "note": "2-billion-year geological record; UNESCO; 6 million visitors/yr"},
    {"name": "Yarlung Tsangpo Grand Canyon", "lat": 29.8000, "lon": 95.0000, "country": "China (Tibet)", "depth_m": 6009, "length_km": 504, "river": "Yarlung Tsangpo (Brahmaputra)", "note": "Deepest canyon on Earth; wraps around Namcha Barwa peak"},
    {"name": "Kali Gandaki Gorge", "lat": 28.7500, "lon": 83.6000, "country": "Nepal", "depth_m": 5571, "length_km": 60, "river": "Kali Gandaki", "note": "Between Dhaulagiri and Annapurna; deepest gorge by some measures"},
    {"name": "Cotahuasi Canyon", "lat": -15.2000, "lon": -72.9000, "country": "Peru", "depth_m": 3354, "length_km": 100, "river": "Cotahuasi", "note": "Twice as deep as Grand Canyon; remote Arequipa region"},
    {"name": "Colca Canyon", "lat": -15.6083, "lon": -71.8833, "country": "Peru", "depth_m": 3270, "length_km": 100, "river": "Colca", "note": "Andean condor viewing; pre-Inca terrace farming; hot springs"},
    {"name": "Tiger Leaping Gorge", "lat": 27.1700, "lon": 100.1700, "country": "China (Yunnan)", "depth_m": 3790, "length_km": 15, "river": "Jinsha (Yangtze)", "note": "One of deepest gorges; legendary tiger leap; hiking trail"},
    {"name": "Copper Canyon (Barrancas del Cobre)", "lat": 27.5000, "lon": -108.4000, "country": "Mexico", "depth_m": 1879, "length_km": 655, "river": "Various", "note": "System of 6 canyons; larger and deeper than Grand Canyon combined"},
    {"name": "Verdon Gorge", "lat": 43.7500, "lon": 6.3250, "country": "France", "depth_m": 700, "length_km": 25, "river": "Verdon", "note": "Europe's Grand Canyon; turquoise water; kayaking and climbing"},
    {"name": "Tara River Canyon", "lat": 43.3500, "lon": 19.2500, "country": "Montenegro", "depth_m": 1300, "length_km": 82, "river": "Tara", "note": "Deepest canyon in Europe; UNESCO; crystal-clear rafting"},
    {"name": "Fish River Canyon", "lat": -27.6000, "lon": 17.5900, "country": "Namibia", "depth_m": 550, "length_km": 160, "river": "Fish", "note": "Second-largest canyon; 5-day hiking trail; geological wonder"},
    {"name": "Blyde River Canyon", "lat": -24.5700, "lon": 30.8100, "country": "South Africa", "depth_m": 800, "length_km": 26, "river": "Blyde", "note": "Largest green canyon; Three Rondavels; Bourke's Luck Potholes"},
    {"name": "Samaria Gorge", "lat": 35.2800, "lon": 23.9600, "country": "Greece (Crete)", "depth_m": 500, "length_km": 16, "river": "Samaria", "note": "Longest gorge in Europe; kri-kri ibex habitat; UNESCO tentative"},
    {"name": "Vikos Gorge", "lat": 39.9100, "lon": 20.7500, "country": "Greece", "depth_m": 1200, "length_km": 20, "river": "Voidomatis", "note": "Guinness deepest gorge relative to width; Zagori stone bridges"},
    {"name": "Indus Gorge", "lat": 35.7400, "lon": 74.6300, "country": "Pakistan", "depth_m": 4500, "length_km": 120, "river": "Indus", "note": "Between Nanga Parbat and Rakaposhi; Karakoram Highway"},
    {"name": "Vintgar Gorge", "lat": 46.3925, "lon": 14.0850, "country": "Slovenia", "depth_m": 150, "length_km": 1.6, "river": "Radovna", "note": "Wooden walkway through emerald canyon; near Lake Bled"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 6. RAPIDS & WHITEWATER
# ═══════════════════════════════════════════════════════════════════════════════
RAPIDS_WHITEWATER = [
    {"name": "Zambezi (below Victoria Falls)", "lat": -17.9200, "lon": 25.8700, "country": "Zambia/Zimbabwe", "class": "V", "river": "Zambezi", "note": "23 rapids in Batoka Gorge; world-class commercial rafting"},
    {"name": "Grand Canyon Rapids", "lat": 36.1000, "lon": -112.1000, "country": "USA", "class": "IV-V", "river": "Colorado", "note": "Lava Falls (Class V), Crystal Rapid; 226-mile permit-only trip"},
    {"name": "Futaleufú River", "lat": -43.1833, "lon": -71.8667, "country": "Chile", "class": "V+", "river": "Futaleufú", "note": "Azure glacier melt; Terminator and Himalayas rapids; world top 5"},
    {"name": "Nile (Jinja, Uganda)", "lat": 0.4400, "lon": 33.2000, "country": "Uganda", "class": "V", "river": "White Nile", "note": "Source of the Nile; Bujagali Falls area; warm water rafting year-round"},
    {"name": "Kaituna River", "lat": -37.8000, "lon": 176.3700, "country": "New Zealand", "class": "V", "river": "Kaituna", "note": "Tutea Falls: highest commercially rafted waterfall (7m drop)"},
    {"name": "Ottawa River", "lat": 45.5900, "lon": -76.9200, "country": "Canada", "class": "IV-V", "river": "Ottawa", "note": "Big water volume; Garvin's Chute, Butcher's Knife; warm summer runs"},
    {"name": "Rio Pacuare", "lat": 9.8800, "lon": -83.5500, "country": "Costa Rica", "class": "IV", "river": "Pacuare", "note": "Rainforest canyon; Huacas and Pinball rapids; eco-rafting"},
    {"name": "Ocoee River", "lat": 35.0900, "lon": -84.5200, "country": "USA (Tennessee)", "class": "IV", "river": "Ocoee", "note": "1996 Olympic whitewater venue; dam-release controlled rapids"},
    {"name": "Rio Apurimac", "lat": -14.0000, "lon": -72.9000, "country": "Peru", "class": "V", "river": "Apurimac", "note": "Source of the Amazon; Black Canyon section; remote multi-day"},
    {"name": "Sun Kosi River", "lat": 27.7500, "lon": 86.2500, "country": "Nepal", "class": "IV-V", "river": "Sun Kosi", "note": "River of Gold; 270km trip from Everest foothills; Himalayan views"},
    {"name": "Sjoa River", "lat": 61.6300, "lon": 9.3200, "country": "Norway", "class": "IV-V", "river": "Sjoa", "note": "Arctic whitewater; Amot and Asengjuvet gorge; kayak mecca"},
    {"name": "Tully River", "lat": -17.7700, "lon": 145.9200, "country": "Australia", "class": "IV", "river": "Tully", "note": "Wet tropics rainforest; 45 rapids in 14km; year-round flow"},
    {"name": "Gauley River", "lat": 38.2000, "lon": -80.9000, "country": "USA (West Virginia)", "class": "V", "river": "Gauley", "note": "Beast of the East; Pillow Rock, Lost Paddle; fall dam release"},
    {"name": "Verdon River", "lat": 43.7500, "lon": 6.3200, "country": "France", "class": "IV", "river": "Verdon", "note": "Gorge du Verdon; emerald water; technical kayaking"},
    {"name": "Soca River", "lat": 46.3300, "lon": 13.5800, "country": "Slovenia", "class": "IV", "river": "Soca", "note": "Emerald beauty; Julian Alps; Great Soca Gorge; WWI history"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 7. RIVER CONFLUENCES
# ═══════════════════════════════════════════════════════════════════════════════
CONFLUENCES = [
    {"name": "Meeting of Waters (Rio Negro & Solimoes)", "lat": -3.1300, "lon": -59.8900, "country": "Brazil", "rivers": "Rio Negro + Rio Solimoes (Amazon)", "color_desc": "Black + Sandy Brown", "length_km": 6, "note": "Waters flow side-by-side for 6 km without mixing; temperature and speed differences"},
    {"name": "Rhone & Arve Confluence", "lat": 46.1850, "lon": 6.1200, "country": "Switzerland", "rivers": "Rhone + Arve", "color_desc": "Blue + Grey-Brown", "length_km": 1, "note": "Visible from Jonction park in Geneva; Alpine glacier vs. mountain silt"},
    {"name": "Blue & White Nile", "lat": 15.6000, "lon": 32.5300, "country": "Sudan", "rivers": "Blue Nile + White Nile", "color_desc": "Dark Blue + Pale Grey", "length_km": 3, "note": "Khartoum confluence; al-Mogran point; creates the main Nile"},
    {"name": "Danube & Inn Confluence", "lat": 48.5700, "lon": 13.4700, "country": "Germany", "rivers": "Danube + Inn + Ilz", "color_desc": "Blue + Green + Black", "length_km": 0.5, "note": "Three-river confluence at Passau; each a different color; Dreiflusseck"},
    {"name": "Ganges & Yamuna (Triveni Sangam)", "lat": 25.4300, "lon": 81.8500, "country": "India", "rivers": "Ganges + Yamuna + mythical Saraswati", "color_desc": "Brown + Green + Invisible", "length_km": 2, "note": "Holiest confluence in Hinduism; Kumbh Mela site; 120M+ gather"},
    {"name": "Ohio & Mississippi", "lat": 37.0000, "lon": -89.1300, "country": "USA", "rivers": "Ohio + Mississippi", "color_desc": "Green + Brown", "length_km": 2, "note": "Cairo, Illinois; Fort Defiance; Ohio doubles Mississippi's volume"},
    {"name": "Missouri & Mississippi", "lat": 38.8100, "lon": -90.1200, "country": "USA", "rivers": "Missouri + Mississippi", "color_desc": "Muddy Brown + Greener", "length_km": 4, "note": "Near St. Louis; Lewis & Clark expedition start; Big Muddy meets Big River"},
    {"name": "Drava & Danube", "lat": 45.5400, "lon": 18.6900, "country": "Croatia", "rivers": "Drava + Danube", "color_desc": "Green + Blue-Grey", "length_km": 1, "note": "Osijek area; Kopacki Rit wetland nature park; bird sanctuary"},
    {"name": "Sava & Danube", "lat": 44.8200, "lon": 20.4500, "country": "Serbia", "rivers": "Sava + Danube", "color_desc": "Green + Brown", "length_km": 1, "note": "Belgrade Kalemegdan fortress overlooks confluence; 2 capitals face it"},
    {"name": "Jialing & Yangtze", "lat": 29.5600, "lon": 106.5800, "country": "China", "rivers": "Jialing + Yangtze", "color_desc": "Green + Brown", "length_km": 2, "note": "Chaotianmen, Chongqing; hotpot city; massive river junction"},
    {"name": "Tigris & Euphrates (Shatt al-Arab)", "lat": 31.0000, "lon": 47.4400, "country": "Iraq", "rivers": "Tigris + Euphrates", "color_desc": "Brown + Olive", "length_km": 200, "note": "Cradle of Civilization; Garden of Eden legend; Mesopotamian marshes"},
    {"name": "Alaknanda & Bhagirathi (Devprayag)", "lat": 30.1447, "lon": 78.5989, "country": "India", "rivers": "Alaknanda + Bhagirathi", "color_desc": "Green + White", "length_km": 0.5, "note": "Birth of the Ganges; sacred Hindu site; Panch Prayag pilgrimage"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 8. HISTORIC RIVER CROSSINGS
# ═══════════════════════════════════════════════════════════════════════════════
HISTORIC_CROSSINGS = [
    {"name": "Washington Crosses the Delaware", "lat": 40.2976, "lon": -74.8727, "country": "USA", "year": "1776", "river": "Delaware", "figure": "George Washington", "note": "Christmas night surprise attack on Hessian garrison at Trenton; turning point of American Revolution"},
    {"name": "Caesar Crosses the Rubicon", "lat": 44.1450, "lon": 12.3970, "country": "Italy", "year": "49 BC", "river": "Rubicon", "figure": "Julius Caesar", "note": "Alea iacta est (The die is cast); started Roman civil war; expression for point of no return"},
    {"name": "Hannibal Crosses the Rhone", "lat": 43.8400, "lon": 4.3600, "country": "France", "year": "218 BC", "river": "Rhone", "figure": "Hannibal Barca", "note": "War elephants and 50,000 troops crossed en route to Alps; Second Punic War"},
    {"name": "Hannibal's Alps Crossing", "lat": 45.0500, "lon": 6.7500, "country": "France/Italy", "year": "218 BC", "river": "Various Alpine rivers", "figure": "Hannibal Barca", "note": "Col de Clapier or Col du Petit St Bernard; lost half his army and most elephants"},
    {"name": "Crossing the Rhine (Operation Plunder)", "lat": 51.6300, "lon": 6.7400, "country": "Germany", "year": "1945", "river": "Rhine", "figure": "Allied Forces (Montgomery)", "note": "WWII final push into Germany; largest amphibious river crossing in history"},
    {"name": "Remagen Bridge Capture", "lat": 50.5780, "lon": 7.2300, "country": "Germany", "year": "1945", "river": "Rhine", "figure": "US 9th Armored Division", "note": "Ludendorff Bridge; first Allied crossing of Rhine; collapsed 10 days later"},
    {"name": "Napoleon Crosses the Danube (Wagram)", "lat": 48.3000, "lon": 16.5600, "country": "Austria", "year": "1809", "river": "Danube", "figure": "Napoleon Bonaparte", "note": "Battle of Wagram; 300,000 troops; one of largest battles before WWI"},
    {"name": "Xenophon's March to the Sea", "lat": 41.0000, "lon": 39.7200, "country": "Turkey", "year": "401 BC", "river": "Various (Euphrates, Tigris)", "figure": "Xenophon & Ten Thousand", "note": "Thalatta! Thalatta! (The sea! The sea!); Anabasis retreat from Persia"},
    {"name": "Alexander Crosses the Hydaspes", "lat": 32.7300, "lon": 73.6800, "country": "Pakistan", "year": "326 BC", "river": "Jhelum (Hydaspes)", "figure": "Alexander the Great", "note": "Battle against King Porus; elephants vs. phalanx; easternmost campaign"},
    {"name": "Cortez Burns His Ships (Veracruz)", "lat": 19.2000, "lon": -96.1600, "country": "Mexico", "year": "1519", "river": "Coastal", "figure": "Hernan Cortez", "note": "Scuttled ships to prevent retreat; began march to Tenochtitlan"},
    {"name": "Dunkirk Evacuation (Channel Crossing)", "lat": 51.0340, "lon": 2.3770, "country": "France", "year": "1940", "river": "English Channel", "figure": "338,000 Allied troops", "note": "Operation Dynamo; little ships; miracle of deliverance"},
    {"name": "Normans Cross the English Channel", "lat": 49.4200, "lon": -0.8800, "country": "France/England", "year": "1066", "river": "English Channel", "figure": "William the Conqueror", "note": "From Normandy to Pevensey; Battle of Hastings; changed English history"},
    {"name": "Moses Parts the Red Sea", "lat": 28.9700, "lon": 33.7800, "country": "Egypt (Sinai)", "year": "~1250 BC (traditional)", "river": "Red Sea / Sea of Reeds", "figure": "Moses", "note": "Exodus narrative; proposed sites include Gulf of Suez, Gulf of Aqaba, Lake Timsah"},
    {"name": "Mao's Long March - Luding Bridge", "lat": 29.9100, "lon": 102.2200, "country": "China", "year": "1935", "river": "Dadu River", "figure": "Red Army", "note": "Crossing of chain bridge under fire; pivotal Long March episode; 22 soldiers"},
    {"name": "Roman Bridge at Alcantara", "lat": 39.7200, "lon": -6.8900, "country": "Spain", "year": "106 AD", "river": "Tagus", "figure": "Emperor Trajan", "note": "Still standing after 1900 years; 48m high; finest Roman bridge"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 9. ENDANGERED RIVERS
# ═══════════════════════════════════════════════════════════════════════════════
ENDANGERED_RIVERS = [
    {"name": "Colorado River", "lat": 36.1100, "lon": -112.1100, "country": "USA/Mexico", "threat": "Over-extraction", "status": "Critical", "note": "Rarely reaches the sea; Lake Mead at historic lows; 40 million depend on it"},
    {"name": "Aral Sea Tributaries (Amu Darya & Syr Darya)", "lat": 44.5000, "lon": 58.5000, "country": "Uzbekistan/Kazakhstan", "threat": "Diversion for irrigation", "status": "Catastrophic", "note": "Aral Sea shrank 90% since 1960; one of worst environmental disasters"},
    {"name": "Rio Grande / Rio Bravo", "lat": 29.7600, "lon": -104.4000, "country": "USA/Mexico", "threat": "Over-extraction, drought", "status": "Critical", "note": "Often runs dry before reaching Gulf of Mexico; 6 million depend on it"},
    {"name": "Murray-Darling", "lat": -34.6000, "lon": 142.2000, "country": "Australia", "threat": "Over-extraction, drought", "status": "Critical", "note": "Australia's food bowl; severe ecological decline; fish kills"},
    {"name": "Ganges", "lat": 25.3200, "lon": 83.0100, "country": "India", "threat": "Pollution, over-extraction", "status": "Severely polluted", "note": "1.5 billion litres/day of sewage; industrial waste; religious offerings"},
    {"name": "Yangtze", "lat": 30.6000, "lon": 111.0000, "country": "China", "threat": "Damming, pollution", "status": "Endangered", "note": "Three Gorges Dam changed ecology; Yangtze finless porpoise critically endangered"},
    {"name": "Mekong", "lat": 15.0000, "lon": 105.0000, "country": "Multiple SE Asian", "threat": "Damming upstream", "status": "Threatened", "note": "11 mainstream dams planned/built; fish migration blocked; sediment loss"},
    {"name": "Jordan River", "lat": 31.7600, "lon": 35.5500, "country": "Israel/Jordan/Palestine", "threat": "Diversion", "status": "Critical", "note": "Reduced to a trickle; 98% diverted; Dead Sea shrinking 1m/year"},
    {"name": "Citarum River", "lat": -6.7800, "lon": 107.6300, "country": "Indonesia", "threat": "Industrial pollution", "status": "Most polluted on Earth", "note": "9 million people depend on it; textile factory waste; floating garbage"},
    {"name": "Yamuna River", "lat": 28.6300, "lon": 77.2300, "country": "India", "threat": "Sewage, industrial waste", "status": "Biologically dead", "note": "22 km through Delhi is biologically dead; 58% of Delhi's waste enters it"},
    {"name": "Salween (Thanlwin)", "lat": 16.8000, "lon": 97.6000, "country": "China/Myanmar/Thailand", "threat": "Proposed dams", "status": "Threatened", "note": "One of last free-flowing major rivers in SE Asia; dam proposals halted"},
    {"name": "Niger River", "lat": 11.0000, "lon": 4.0000, "country": "West Africa", "threat": "Desertification, pollution", "status": "Threatened", "note": "Inner Delta shrinking; oil pollution in delta; 100 million depend on it"},
    {"name": "Indus River", "lat": 25.4000, "lon": 68.3000, "country": "Pakistan", "threat": "Over-extraction, glacial melt", "status": "Endangered", "note": "Mangrove loss in delta; Tarbela Dam silting; Himalayan glaciers retreating"},
    {"name": "Lake Chad tributaries", "lat": 13.0000, "lon": 14.5000, "country": "Chad/Nigeria/Niger/Cameroon", "threat": "Climate change, diversion", "status": "Catastrophic", "note": "Lake shrank 90% since 1960s; 30 million affected; conflict over water"},
    {"name": "Danube (lower)", "lat": 44.0000, "lon": 22.5000, "country": "Romania/Bulgaria", "threat": "Pollution, navigation works", "status": "Impacted", "note": "Industrial and agricultural pollution; wetland loss; sturgeon endangered"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 10. SACRED RIVERS
# ═══════════════════════════════════════════════════════════════════════════════
SACRED_RIVERS = [
    {"name": "Ganges (Ganga)", "lat": 25.3200, "lon": 83.0100, "country": "India", "religion": "Hinduism", "deity": "Goddess Ganga", "note": "Holiest river; cremation at Varanasi releases from samsara; Kumbh Mela; personified as goddess"},
    {"name": "Yamuna", "lat": 27.4900, "lon": 77.6800, "country": "India", "religion": "Hinduism", "deity": "Goddess Yamuna", "note": "Sacred twin of Ganges; Krishna's childhood playground at Vrindavan; daughter of Sun god Surya"},
    {"name": "Saraswati", "lat": 29.9600, "lon": 76.8500, "country": "India (mythical)", "religion": "Hinduism", "deity": "Goddess Saraswati", "note": "Lost river of the Vedas; said to flow underground at Triveni Sangam; goddess of knowledge"},
    {"name": "Jordan River", "lat": 32.7100, "lon": 35.5700, "country": "Israel/Jordan", "religion": "Christianity/Judaism", "deity": "None (God's presence)", "note": "Baptism of Jesus by John the Baptist; Israelites crossed into Promised Land; Naaman healed"},
    {"name": "Nile", "lat": 30.0400, "lon": 31.2400, "country": "Egypt", "religion": "Ancient Egyptian", "deity": "Hapi (flood god)", "note": "Source of all life in Egypt; annual inundation worshipped; Osiris myth; Pharaoh's divine right"},
    {"name": "Narmada", "lat": 22.5100, "lon": 75.8200, "country": "India", "religion": "Hinduism", "deity": "Goddess Narmada", "note": "Circumambulation (Parikrama) takes 3 years; every pebble is a Shiva linga; holier than Ganges to some"},
    {"name": "Godavari", "lat": 16.9400, "lon": 82.2300, "country": "India", "religion": "Hinduism", "deity": "Dakshina Ganga", "note": "Ganges of the South; Kumbh Mela at Nashik; Rama's exile route along its banks"},
    {"name": "Kaveri (Cauvery)", "lat": 12.4200, "lon": 76.6900, "country": "India", "religion": "Hinduism", "deity": "Goddess Kaveri", "note": "Sacred river of South India; Srirangam temple island; sangam of seven rivers"},
    {"name": "Euphrates", "lat": 31.0000, "lon": 47.4400, "country": "Iraq", "religion": "Judaism/Christianity/Islam", "deity": "None (Eden river)", "note": "River of Eden (Genesis); Revelation's sixth angel; Babylonian baptism rituals"},
    {"name": "Tigris", "lat": 33.3300, "lon": 44.4000, "country": "Iraq", "religion": "Judaism/Christianity/Islam", "deity": "Hiddekel (Hebrew name)", "note": "Eden's third river; Nineveh on its banks; Noah traditions; Mandaean baptisms"},
    {"name": "Bagmati", "lat": 27.7100, "lon": 85.3500, "country": "Nepal", "religion": "Hinduism/Buddhism", "deity": "Sacred to both faiths", "note": "Pashupatinath cremation ghats; holiest river in Nepal; flows past Kathmandu"},
    {"name": "Irrawaddy", "lat": 21.9000, "lon": 96.1000, "country": "Myanmar", "religion": "Buddhism", "deity": "Ayeyarwady nats (spirits)", "note": "Spiritual heart of Myanmar; Bagan temples along its banks; nat worship"},
    {"name": "Shinano River (Chikuma)", "lat": 37.9200, "lon": 139.0400, "country": "Japan", "religion": "Shinto", "deity": "River kami", "note": "Longest in Japan; Shinto purification rituals (misogi); rice paddy sustenance"},
    {"name": "Styx (mythological)", "lat": 38.0000, "lon": 22.1500, "country": "Greece", "religion": "Ancient Greek", "deity": "Goddess Styx", "note": "River of the Underworld; oaths by the gods; Achilles' invulnerability; real waterfall in Arcadia"},
    {"name": "Sarayu", "lat": 26.7900, "lon": 82.2000, "country": "India", "religion": "Hinduism", "deity": "Sacred to Rama", "note": "Ayodhya stands on its banks; Rama's birthplace; mass ritual bathing site"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# MAP MODES
# ═══════════════════════════════════════════════════════════════════════════════
MAP_MODES = [
    "1. World's Greatest Waterfalls",
    "2. Tallest Waterfalls Ranked",
    "3. Great River Systems",
    "4. River Deltas",
    "5. Gorges & Canyons",
    "6. Rapids & Whitewater",
    "7. River Confluences",
    "8. Historic River Crossings",
    "9. Endangered Rivers",
    "10. Sacred Rivers",
]


# ═══════════════════════════════════════════════════════════════════════════════
# OVERPASS WATERFALL SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _search_waterfalls_overpass(lat: float, lon: float, radius_km: float) -> list:
    """Search waterfalls near a point via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["waterway"="waterfall"](around:{radius_m},{lat},{lon});
  way["waterway"="waterfall"](around:{radius_m},{lat},{lon});
  node["natural"="waterfall"](around:{radius_m},{lat},{lon});
  way["natural"="waterfall"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in (result or {}):
        return []

    features = []
    node_lookup = {}
    for el in result.get("elements", []):
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    for el in result.get("elements", []):
        tags = el.get("tags", {})
        if not tags:
            continue
        lat_f, lon_f = None, None
        if el.get("type") == "node":
            lat_f, lon_f = el.get("lat"), el.get("lon")
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [node_lookup[n] for n in nodes if n in node_lookup]
            if coords:
                lat_f = sum(c[0] for c in coords) / len(coords)
                lon_f = sum(c[1] for c in coords) / len(coords)
        if lat_f is None:
            continue
        features.append({
            "name": tags.get("name", tags.get("name:en", "Unnamed")),
            "lat": lat_f,
            "lon": lon_f,
            "height": tags.get("height", "Unknown"),
            "osm_id": el.get("id"),
        })
    return features


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: build a folium map
# ═══════════════════════════════════════════════════════════════════════════════
def _make_map(center_lat: float = 20.0, center_lon: float = 0.0,
              zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _add_marker(m: folium.Map, lat: float, lon: float, name: str,
                popup_html: str, color: str = "#06b6d4",
                icon: str = "info-sign", radius: float = 7):
    """Add a circle marker with popup."""
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=350),
        tooltip=escape(name),
    ).add_to(m)


def _render_map(m: folium.Map, height: int = 500):
    """Render folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _download_csv(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Offer CSV download."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(label, csv_buf.getvalue(), file_name=filename,
                       mime="text/csv", width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _bar_chart(labels: list, values: list, title: str, xlabel: str, ylabel: str,
               color: str = _ACCENT, horizontal: bool = True):
    """Render a dark-themed matplotlib bar chart."""
    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.35)))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)

    if horizontal:
        bars = ax.barh(range(len(labels)), values, color=color, edgecolor=_BORDER)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=8, color=_TEXT_PRI)
        ax.set_xlabel(xlabel, color=_TEXT_SEC, fontsize=9)
        ax.invert_yaxis()
    else:
        bars = ax.bar(range(len(labels)), values, color=color, edgecolor=_BORDER)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=7, color=_TEXT_PRI, rotation=45, ha="right")
        ax.set_ylabel(ylabel, color=_TEXT_SEC, fontsize=9)

    ax.set_title(title, color=_TEXT_PRI, fontsize=11, pad=10)
    ax.tick_params(colors=_TEXT_SEC, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.grid(axis="x" if horizontal else "y", color=_BORDER, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _pie_chart(labels: list, values: list, title: str, colors: list = None):
    """Render a dark-themed matplotlib pie chart."""
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    if colors is None:
        colors = ["#06b6d4", "#3b82f6", "#8b5cf6", "#10b981", "#f59e0b",
                  "#ec4899", "#ef4444", "#14b8a6", "#a855f7", "#38bdf8",
                  "#f97316", "#84cc16"]
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors[:len(labels)],
        autopct="%1.0f%%", startangle=140,
        textprops={"color": _TEXT_PRI, "fontsize": 8},
    )
    for t in autotexts:
        t.set_color(_TEXT_PRI)
        t.set_fontsize(7)
    ax.set_title(title, color=_TEXT_PRI, fontsize=11, pad=10)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 1: World's Greatest Waterfalls
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_greatest_waterfalls():
    st.markdown("#### World's Greatest Waterfalls")
    st.markdown(
        "The planet's most iconic waterfalls ranked by fame, height, and flow rate. "
        "From the towering Angel Falls in Venezuela to the thundering Niagara on "
        "the US-Canada border, these 50 waterfalls represent nature at its most dramatic."
    )

    df = pd.DataFrame(GREATEST_WATERFALLS)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Waterfalls", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Tallest", f"{df['height_m'].max()} m")
    c4.metric("Avg Height", f"{df['height_m'].mean():.0f} m")

    # Chart: top 20 by height
    top20 = df.nlargest(20, "height_m")
    _bar_chart(
        top20["name"].tolist(), top20["height_m"].tolist(),
        "Top 20 Waterfalls by Height", "Height (m)", "",
        color=_ACCENT,
    )

    # Type distribution
    type_counts = df["type"].value_counts()
    _pie_chart(type_counts.index.tolist(), type_counts.values.tolist(),
               "Waterfall Types Distribution",
               [TYPE_COLORS.get(t, _ACCENT) for t in type_counts.index])

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map()
    for _, row in df.iterrows():
        color = TYPE_COLORS.get(row["type"], _ACCENT)
        radius = max(4, min(15, row["height_m"] / 80))
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<b>Height:</b> {row['height_m']} m<br>"
            f"<b>Type:</b> {escape(row['type'])}<br>"
            f"<b>River:</b> {escape(row['river'])}<br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, color, radius=radius)
    _render_map(m)

    # Live Overpass search
    st.markdown("##### Search OSM Waterfalls Nearby")
    oc1, oc2, oc3 = st.columns(3)
    with oc1:
        s_lat = st.number_input("Latitude", value=43.08, format="%.4f", key="wf_osm_lat")
    with oc2:
        s_lon = st.number_input("Longitude", value=-79.07, format="%.4f", key="wf_osm_lon")
    with oc3:
        s_rad = st.slider("Radius (km)", 5, 100, 30, key="wf_osm_rad")

    if st.button("Search Waterfalls (Overpass)", key="wf_osm_btn", width="stretch"):
        with st.spinner("Querying OpenStreetMap..."):
            osm_falls = _search_waterfalls_overpass(s_lat, s_lon, s_rad)
        if osm_falls:
            st.success(f"Found {len(osm_falls)} waterfalls from OSM")
            osm_df = pd.DataFrame(osm_falls)
            st.dataframe(osm_df, width="stretch")
            mo = _make_map(s_lat, s_lon, zoom=9)
            for f in osm_falls:
                popup = (
                    f"<div style='font-family:sans-serif;'>"
                    f"<b>{escape(str(f['name']))}</b><br>"
                    f"Height: {escape(str(f['height']))}<br>"
                    f"OSM ID: {f['osm_id']}</div>"
                )
                _add_marker(mo, f["lat"], f["lon"], str(f["name"]), popup, "#38bdf8")
            _render_map(mo)
        else:
            st.warning("No waterfalls found in this area. Try a larger radius.")

    # Data table and download
    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "greatest_waterfalls.csv", "Download Greatest Waterfalls CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 2: Tallest Waterfalls Ranked
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_tallest_waterfalls():
    st.markdown("#### Tallest Waterfalls Ranked")
    st.markdown(
        "The 20 tallest waterfalls on Earth ranked by total height, with comparison "
        "of total drop versus longest single drop. Norway dominates with its glacier-fed "
        "horsetail falls, while the Americas hold the records for single plunges."
    )

    df = pd.DataFrame(TALLEST_WATERFALLS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entries", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Max Total", f"{df['total_m'].max()} m")
    c4.metric("Max Single Drop", f"{df['longest_drop_m'].max()} m")

    # Dual bar chart: total vs single drop
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    y_pos = range(len(df))
    ax.barh(y_pos, df["total_m"], color="#06b6d4", alpha=0.8, label="Total Height")
    ax.barh(y_pos, df["longest_drop_m"], color="#ec4899", alpha=0.7, label="Longest Single Drop")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"#{r['rank']} {r['name']}" for _, r in df.iterrows()],
                       fontsize=8, color=_TEXT_PRI)
    ax.set_xlabel("Height (metres)", color=_TEXT_SEC, fontsize=9)
    ax.set_title("Tallest Waterfalls: Total Height vs Longest Single Drop",
                 color=_TEXT_PRI, fontsize=11, pad=10)
    ax.legend(facecolor=_SURFACE, edgecolor=_BORDER, labelcolor=_TEXT_PRI, fontsize=8)
    ax.tick_params(colors=_TEXT_SEC)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.grid(axis="x", color=_BORDER, alpha=0.3)
    ax.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Country distribution
    country_counts = df["country"].value_counts()
    _pie_chart(country_counts.index.tolist(), country_counts.values.tolist(),
               "Tallest Waterfalls by Country")

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map()
    for _, row in df.iterrows():
        color = TYPE_COLORS.get(row["type"], _ACCENT)
        radius = max(5, row["total_m"] / 80)
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>#{row['rank']} {escape(row['name'])}</b><br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<b>Total Height:</b> {row['total_m']} m<br>"
            f"<b>Longest Drop:</b> {row['longest_drop_m']} m<br>"
            f"<b>Type:</b> {escape(row['type'])}</div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, color, radius=radius)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "tallest_waterfalls.csv", "Download Tallest Waterfalls CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 3: Great River Systems
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_great_rivers():
    st.markdown("#### Great River Systems")
    st.markdown(
        "The world's mightiest rivers mapped from source to mouth. Each river system "
        "is plotted with key waypoints along its course, showing the immense scale of "
        "these continental arteries that sustain billions of people."
    )

    # Build summary df
    rows = []
    for name, info in GREAT_RIVERS.items():
        rows.append({
            "River": name,
            "Length (km)": info["length_km"],
            "Basin (km2)": info["basin_km2"],
            "Discharge (m3/s)": info["discharge_m3s"],
            "Source": info["source"],
            "Mouth": info["mouth"],
        })
    df = pd.DataFrame(rows)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rivers Mapped", len(GREAT_RIVERS))
    c2.metric("Longest", f"{df['Length (km)'].max():,} km")
    c3.metric("Highest Discharge", f"{df['Discharge (m3/s)'].max():,} m3/s")
    c4.metric("Largest Basin", f"{df['Basin (km2)'].max():,} km2")

    # Length comparison chart
    _bar_chart(
        df.sort_values("Length (km)", ascending=True)["River"].tolist(),
        df.sort_values("Length (km)", ascending=True)["Length (km)"].tolist(),
        "Great Rivers by Length", "Length (km)", "",
        color="#3b82f6",
    )

    # Discharge comparison
    _bar_chart(
        df.sort_values("Discharge (m3/s)", ascending=True)["River"].tolist(),
        df.sort_values("Discharge (m3/s)", ascending=True)["Discharge (m3/s)"].tolist(),
        "Great Rivers by Average Discharge", "Discharge (m3/s)", "",
        color="#10b981",
    )

    # Map with river courses
    st.markdown("##### Interactive Map")
    m = _make_map(zoom=2)
    for name, info in GREAT_RIVERS.items():
        color = info["color"]
        waypoints = info["waypoints"]
        # Draw polyline for river course
        coords = [[wp["lat"], wp["lon"]] for wp in waypoints]
        folium.PolyLine(
            coords, color=color, weight=3, opacity=0.8,
            tooltip=escape(name),
        ).add_to(m)
        # Mark waypoints
        for i, wp in enumerate(waypoints):
            icon_type = "star" if i == 0 or i == len(waypoints) - 1 else "info-sign"
            radius = 6 if i == 0 or i == len(waypoints) - 1 else 4
            popup = (
                f"<div style='font-family:sans-serif;'>"
                f"<b>{escape(name)}</b> - {escape(wp['name'])}<br>"
                f"Length: {info['length_km']:,} km<br>"
                f"Discharge: {info['discharge_m3s']:,} m3/s<br>"
                f"<small>{escape(info['note'])}</small></div>"
            )
            _add_marker(m, wp["lat"], wp["lon"], f"{name} - {wp['name']}",
                        popup, color, radius=radius)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "great_rivers.csv", "Download Great Rivers CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 4: River Deltas
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_river_deltas():
    st.markdown("#### River Deltas")
    st.markdown(
        "Where rivers meet the sea, they build vast fertile plains from deposited sediment. "
        "These deltas support hundreds of millions of people but face rising seas, subsidence, "
        "and upstream damming. From the Ganges-Brahmaputra to the Mississippi bird-foot."
    )

    df = pd.DataFrame(RIVER_DELTAS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deltas Mapped", len(df))
    c2.metric("Largest", f"{df['area_km2'].max():,} km2")
    c3.metric("Delta Types", df["type"].nunique())
    c4.metric("Total Area", f"{df['area_km2'].sum():,} km2")

    # Area chart
    sorted_df = df.sort_values("area_km2", ascending=True)
    _bar_chart(
        sorted_df["name"].tolist(), sorted_df["area_km2"].tolist(),
        "River Deltas by Area", "Area (km2)", "",
        color="#14b8a6",
    )

    # Type distribution
    type_counts = df["type"].value_counts()
    _pie_chart(type_counts.index.tolist(), type_counts.values.tolist(),
               "Delta Formation Types")

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map()
    for _, row in df.iterrows():
        radius = max(5, math.sqrt(row["area_km2"]) / 30)
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>River:</b> {escape(row['river'])}<br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<b>Area:</b> {row['area_km2']:,} km2<br>"
            f"<b>Type:</b> {escape(row['type'])}<br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, "#14b8a6",
                    radius=radius)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "river_deltas.csv", "Download River Deltas CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 5: Gorges & Canyons
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_gorges_canyons():
    st.markdown("#### Gorges & Canyons")
    st.markdown(
        "The deepest scars on Earth's surface, carved over millions of years by relentless "
        "rivers. From the Yarlung Tsangpo's 6-km-deep gorge in Tibet to the Grand Canyon's "
        "2-billion-year geological story, these are nature's greatest sculptures."
    )

    df = pd.DataFrame(GORGES_CANYONS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gorges Mapped", len(df))
    c2.metric("Deepest", f"{df['depth_m'].max():,} m")
    c3.metric("Longest", f"{df['length_km'].max():,} km")
    c4.metric("Countries", df["country"].nunique())

    # Depth chart
    sorted_df = df.sort_values("depth_m", ascending=True)
    _bar_chart(
        sorted_df["name"].tolist(), sorted_df["depth_m"].tolist(),
        "Gorges & Canyons by Depth", "Depth (m)", "",
        color="#ef4444",
    )

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map()
    for _, row in df.iterrows():
        radius = max(5, row["depth_m"] / 500)
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<b>Depth:</b> {row['depth_m']:,} m<br>"
            f"<b>Length:</b> {row['length_km']} km<br>"
            f"<b>River:</b> {escape(row['river'])}<br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, "#ef4444",
                    radius=radius)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "gorges_canyons.csv", "Download Gorges & Canyons CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 6: Rapids & Whitewater
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_rapids_whitewater():
    st.markdown("#### Rapids & Whitewater")
    st.markdown(
        "The world's most thrilling whitewater destinations, from the Class V Zambezi below "
        "Victoria Falls to the glacier-fed Futaleufuu in Chile. Mapped for rafters, kayakers, "
        "and adventure seekers worldwide."
    )

    df = pd.DataFrame(RAPIDS_WHITEWATER)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rapids Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    class_v_count = len(df[df["class"].str.contains("V")])
    c3.metric("Class V+", class_v_count)
    c4.metric("Continents", 6)

    # Class distribution
    class_counts = df["class"].value_counts()
    _pie_chart(class_counts.index.tolist(), class_counts.values.tolist(),
               "Whitewater Class Distribution",
               ["#ef4444", "#f59e0b", "#06b6d4", "#8b5cf6", "#10b981"])

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map()
    class_colors = {"V": "#ef4444", "V+": "#dc2626", "IV-V": "#f97316",
                    "IV": "#f59e0b", "III-IV": "#10b981"}
    for _, row in df.iterrows():
        color = class_colors.get(row["class"], _ACCENT)
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<b>Class:</b> {escape(row['class'])}<br>"
            f"<b>River:</b> {escape(row['river'])}<br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, color, radius=7)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "rapids_whitewater.csv", "Download Rapids & Whitewater CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 7: River Confluences
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_confluences():
    st.markdown("#### River Confluences")
    st.markdown(
        "Where two great rivers meet, often refusing to mix for kilometres downstream. "
        "The Meeting of Waters near Manaus, where the black Rio Negro meets the sandy "
        "Solimoes, is the most spectacular, but dramatic confluences occur worldwide."
    )

    df = pd.DataFrame(CONFLUENCES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Confluences Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Longest Non-Mixing", f"{df['length_km'].max()} km")
    c4.metric("Continents", 5)

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map()
    confluence_colors = ["#06b6d4", "#3b82f6", "#f59e0b", "#8b5cf6", "#10b981",
                         "#ec4899", "#ef4444", "#14b8a6", "#a855f7", "#38bdf8",
                         "#f97316", "#84cc16"]
    for i, (_, row) in enumerate(df.iterrows()):
        color = confluence_colors[i % len(confluence_colors)]
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>Rivers:</b> {escape(row['rivers'])}<br>"
            f"<b>Colors:</b> {escape(row['color_desc'])}<br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<b>Non-mixing length:</b> {row['length_km']} km<br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, color, radius=8)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    display_df = df.drop(columns=["lat", "lon"], errors="ignore")
    st.dataframe(display_df, width="stretch")
    _download_csv(df, "river_confluences.csv", "Download River Confluences CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 8: Historic River Crossings
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_historic_crossings():
    st.markdown("#### Historic River Crossings")
    st.markdown(
        "Rivers have shaped the course of history as barriers and highways alike. "
        "From Caesar's fateful crossing of the Rubicon to the D-Day armadas across "
        "the English Channel, these crossings changed civilizations."
    )

    df = pd.DataFrame(HISTORIC_CROSSINGS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historic Crossings", len(df))
    c2.metric("Time Span", "1250 BC - 1945 AD")
    c3.metric("Countries", df["country"].nunique())
    c4.metric("Key Figures", df["figure"].nunique())

    # Timeline chart
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)

    # Parse years for timeline (handle BC/AD)
    timeline_data = []
    for _, row in df.iterrows():
        yr_str = str(row["year"]).strip()
        if "BC" in yr_str:
            yr = -int(yr_str.replace("BC", "").replace("~", "").strip())
        elif "AD" in yr_str:
            yr = int(yr_str.replace("AD", "").replace("~", "").strip())
        else:
            yr = int(yr_str.replace("~", "").strip())
        timeline_data.append((yr, row["name"]))

    timeline_data.sort(key=lambda x: x[0])
    years = [t[0] for t in timeline_data]
    names = [t[1] for t in timeline_data]

    # Alternate y positions for readability
    y_positions = [1 if i % 2 == 0 else -1 for i in range(len(years))]
    colors_tl = ["#06b6d4", "#3b82f6", "#f59e0b", "#8b5cf6", "#10b981",
                 "#ec4899", "#ef4444", "#14b8a6", "#a855f7", "#38bdf8",
                 "#f97316", "#84cc16", "#06b6d4", "#3b82f6", "#f59e0b"]

    ax.axhline(y=0, color=_BORDER, linewidth=1)
    for i, (yr, name) in enumerate(timeline_data):
        ax.scatter(yr, 0, color=colors_tl[i % len(colors_tl)], s=60, zorder=5)
        ax.plot([yr, yr], [0, y_positions[i] * 0.5], color=_BORDER, linewidth=0.8)
        label = name if len(name) < 30 else name[:27] + "..."
        ax.text(yr, y_positions[i] * 0.65, label,
                ha="center", va="bottom" if y_positions[i] > 0 else "top",
                fontsize=6, color=_TEXT_PRI, rotation=30)

    ax.set_xlabel("Year", color=_TEXT_SEC, fontsize=9)
    ax.set_title("Timeline of Historic River Crossings", color=_TEXT_PRI, fontsize=11, pad=10)
    ax.set_ylim(-2, 2)
    ax.tick_params(colors=_TEXT_SEC, labelsize=8)
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map(center_lat=35, center_lon=10, zoom=3)
    era_colors = {
        "ancient": "#f59e0b",
        "medieval": "#8b5cf6",
        "modern": "#06b6d4",
    }
    for _, row in df.iterrows():
        yr_str = str(row["year"]).strip()
        if "BC" in yr_str or ("AD" in yr_str and int(yr_str.replace("AD", "").replace("~", "").strip()) < 500):
            color = era_colors["ancient"]
        elif "1" in yr_str[:2] and int(yr_str[:4]) < 1500:
            color = era_colors["medieval"]
        else:
            color = era_colors["modern"]
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>Year:</b> {escape(str(row['year']))}<br>"
            f"<b>Figure:</b> {escape(row['figure'])}<br>"
            f"<b>River:</b> {escape(row['river'])}<br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, color, radius=7)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "historic_crossings.csv", "Download Historic Crossings CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 9: Endangered Rivers
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_endangered_rivers():
    st.markdown("#### Endangered Rivers")
    st.markdown(
        "Rivers under existential threat from damming, pollution, over-extraction, "
        "and climate change. The Aral Sea's tributaries shrank a great inland sea by 90%. "
        "The Colorado rarely reaches the ocean. These are the planet's most at-risk waterways."
    )

    df = pd.DataFrame(ENDANGERED_RIVERS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Endangered Rivers", len(df))
    c2.metric("Critical/Catastrophic", len(df[df["status"].isin(["Critical", "Catastrophic"])]))
    c3.metric("Threat Types", df["threat"].nunique())
    c4.metric("Countries Affected", df["country"].nunique())

    # Threat distribution
    threat_counts = df["threat"].value_counts()
    _pie_chart(threat_counts.index.tolist(), threat_counts.values.tolist(),
               "Primary Threats to Endangered Rivers",
               ["#ef4444", "#f59e0b", "#8b5cf6", "#3b82f6", "#06b6d4",
                "#10b981", "#ec4899", "#a855f7"])

    # Status chart
    status_counts = df["status"].value_counts()
    status_colors = {
        "Catastrophic": "#dc2626",
        "Critical": "#ef4444",
        "Severely polluted": "#f97316",
        "Most polluted on Earth": "#991b1b",
        "Biologically dead": "#7f1d1d",
        "Endangered": "#f59e0b",
        "Threatened": "#eab308",
        "Impacted": "#84cc16",
    }
    colors_list = [status_colors.get(s, _ACCENT) for s in status_counts.index]
    _bar_chart(
        status_counts.index.tolist(), status_counts.values.tolist(),
        "Rivers by Threat Status", "Count", "", color="#ef4444",
    )

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map()
    for _, row in df.iterrows():
        color = status_colors.get(row["status"], "#ef4444")
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<b>Threat:</b> {escape(row['threat'])}<br>"
            f"<b>Status:</b> <span style='color:{color}'>{escape(row['status'])}</span><br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, color, radius=8)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    st.dataframe(df, width="stretch")
    _download_csv(df, "endangered_rivers.csv", "Download Endangered Rivers CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 10: Sacred Rivers
# ═══════════════════════════════════════════════════════════════════════════════
def _mode_sacred_rivers():
    st.markdown("#### Sacred Rivers")
    st.markdown(
        "Rivers worshipped as deities, used for baptism, or revered as sources of spiritual "
        "power. The Ganges is personified as Goddess Ganga in Hinduism. The Jordan saw the "
        "baptism of Jesus. The Styx separated the living from the dead in Greek myth."
    )

    df = pd.DataFrame(SACRED_RIVERS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sacred Rivers", len(df))
    c2.metric("Religions", df["religion"].nunique())
    c3.metric("Countries", df["country"].nunique())
    c4.metric("With Deities", len(df[df["deity"] != "None (God's presence)"]))

    # Religion distribution
    religion_counts = df["religion"].value_counts()
    rel_colors = {
        "Hinduism": "#f59e0b",
        "Christianity/Judaism": "#3b82f6",
        "Buddhism": "#8b5cf6",
        "Ancient Egyptian": "#f97316",
        "Ancient Greek": "#ec4899",
        "Islam": "#10b981",
        "Shinto": "#ef4444",
        "Judaism/Christianity/Islam": "#06b6d4",
        "Hinduism/Buddhism": "#14b8a6",
        "Buddhism/Hinduism": "#14b8a6",
    }
    colors_r = [rel_colors.get(r, _ACCENT) for r in religion_counts.index]
    _pie_chart(religion_counts.index.tolist(), religion_counts.values.tolist(),
               "Sacred Rivers by Religion", colors_r)

    # Map
    st.markdown("##### Interactive Map")
    m = _make_map(center_lat=25, center_lon=75, zoom=3)
    for _, row in df.iterrows():
        color = rel_colors.get(row["religion"], _ACCENT)
        popup = (
            f"<div style='font-family:sans-serif;'>"
            f"<b>{escape(row['name'])}</b><br>"
            f"<b>Religion:</b> {escape(row['religion'])}<br>"
            f"<b>Deity:</b> {escape(row['deity'])}<br>"
            f"<b>Country:</b> {escape(row['country'])}<br>"
            f"<small>{escape(row['note'])}</small></div>"
        )
        _add_marker(m, row["lat"], row["lon"], row["name"], popup, color, radius=8)
    _render_map(m)

    st.markdown("##### Complete Dataset")
    display_df = df.drop(columns=["lat", "lon"], errors="ignore")
    st.dataframe(display_df, width="stretch")
    _download_csv(df, "sacred_rivers.csv", "Download Sacred Rivers CSV")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════
def render_waterfall_maps_tab():
    """Main render function for the Waterfalls & Great Rivers tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>&#x1F30A; Waterfalls & Great Rivers</h4>'
        '<p>Famous waterfalls, river systems, gorges, rapids & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.selectbox("Select Map Mode", MAP_MODES, key="waterfall_map_mode")

    # ── Dispatch ──
    if mode == MAP_MODES[0]:
        _mode_greatest_waterfalls()
    elif mode == MAP_MODES[1]:
        _mode_tallest_waterfalls()
    elif mode == MAP_MODES[2]:
        _mode_great_rivers()
    elif mode == MAP_MODES[3]:
        _mode_river_deltas()
    elif mode == MAP_MODES[4]:
        _mode_gorges_canyons()
    elif mode == MAP_MODES[5]:
        _mode_rapids_whitewater()
    elif mode == MAP_MODES[6]:
        _mode_confluences()
    elif mode == MAP_MODES[7]:
        _mode_historic_crossings()
    elif mode == MAP_MODES[8]:
        _mode_endangered_rivers()
    elif mode == MAP_MODES[9]:
        _mode_sacred_rivers()
