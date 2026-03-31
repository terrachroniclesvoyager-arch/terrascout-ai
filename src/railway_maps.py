# -*- coding: utf-8 -*-
"""
Railway & Train Maps module for TerraScout AI.

Provides 10 railway-focused map visualizations using free APIs:
1.  World Railway Stations     (Overpass: railway=station)
2.  High-Speed Rail Networks   (Curated: TGV, Shinkansen, ICE, AVE, CRH, KTX)
3.  Trans-Siberian & Epic Routes (Curated legendary long-distance routes)
4.  Historic Railways          (Curated: 20+ historic firsts 1825-1870)
5.  Metro Systems              (Overpass: station=subway / subway_entrance)
6.  Scenic Railway Routes      (Curated: 25+ world scenic routes)
7.  Railway Bridges & Tunnels  (Curated: 20+ engineering marvels)
8.  Abandoned Railways         (Overpass: railway=abandoned / disused)
9.  Funiculars & Rack Railways (Overpass: railway=funicular / narrow_gauge)
10. Train Stations Architecture (Curated: 25+ architecturally significant stations)

All APIs are free, no keys required.
"""

import io
import json
import math
import logging
from html import escape

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS & COLOUR PALETTE
# =============================================================================

RAILWAY_COLORS = {
    "stations":    "#f59e0b",
    "highspeed":   "#ef4444",
    "epic":        "#8b5cf6",
    "historic":    "#f97316",
    "metro":       "#a855f7",
    "scenic":      "#10b981",
    "bridges":     "#3b82f6",
    "abandoned":   "#64748b",
    "funiculars":  "#22d3ee",
    "architecture":"#ec4899",
}

MAP_MODES = [
    "World Railway Stations",
    "High-Speed Rail Networks",
    "Trans-Siberian & Epic Routes",
    "Historic Railways",
    "Metro Systems",
    "Scenic Railway Routes",
    "Railway Bridges & Tunnels",
    "Abandoned Railways",
    "Funiculars & Rack Railways",
    "Train Stations Architecture",
]

# =============================================================================
# PRESET LOCATIONS
# =============================================================================

STATION_PRESETS = {
    "Custom": None,
    "London Rail Hub": {"lat": 51.53, "lon": -0.13, "radius": 12},
    "Tokyo Rail Network": {"lat": 35.68, "lon": 139.77, "radius": 12},
    "Paris Gare du Nord Area": {"lat": 48.88, "lon": 2.36, "radius": 10},
    "Berlin Hauptbahnhof": {"lat": 52.52, "lon": 13.37, "radius": 10},
    "Zurich Main Station": {"lat": 47.38, "lon": 8.54, "radius": 10},
    "Milan Central": {"lat": 45.48, "lon": 9.20, "radius": 10},
    "Mumbai Railways": {"lat": 19.02, "lon": 72.84, "radius": 12},
    "Chicago Union Station": {"lat": 41.88, "lon": -87.64, "radius": 12},
    "Rome Termini Area": {"lat": 41.90, "lon": 12.50, "radius": 8},
    "Moscow Rail Network": {"lat": 55.76, "lon": 37.62, "radius": 12},
    "Delhi Rail Hub": {"lat": 28.64, "lon": 77.22, "radius": 10},
    "Shanghai Station Area": {"lat": 31.25, "lon": 121.46, "radius": 10},
}

METRO_PRESETS = {
    "Custom": None,
    "London Underground": {"lat": 51.51, "lon": -0.13, "radius": 10},
    "Paris Metro": {"lat": 48.86, "lon": 2.35, "radius": 8},
    "Tokyo Metro": {"lat": 35.68, "lon": 139.77, "radius": 10},
    "New York Subway": {"lat": 40.75, "lon": -73.99, "radius": 10},
    "Moscow Metro": {"lat": 55.76, "lon": 37.62, "radius": 10},
    "Berlin U-Bahn": {"lat": 52.52, "lon": 13.41, "radius": 8},
    "Madrid Metro": {"lat": 40.42, "lon": -3.70, "radius": 8},
    "Rome Metro": {"lat": 41.90, "lon": 12.50, "radius": 8},
    "Shanghai Metro": {"lat": 31.23, "lon": 121.47, "radius": 12},
    "Seoul Metro": {"lat": 37.57, "lon": 126.98, "radius": 10},
    "Mexico City Metro": {"lat": 19.43, "lon": -99.13, "radius": 10},
    "Barcelona Metro": {"lat": 41.39, "lon": 2.17, "radius": 8},
}

ABANDONED_PRESETS = {
    "Custom": None,
    "UK Peak District": {"lat": 53.30, "lon": -1.80, "radius": 15},
    "Welsh Railways": {"lat": 52.62, "lon": -3.73, "radius": 20},
    "Colorado Narrow Gauge": {"lat": 37.28, "lon": -107.88, "radius": 20},
    "German Heritage Lines": {"lat": 51.76, "lon": 11.00, "radius": 20},
    "Italian Apennine Lines": {"lat": 44.06, "lon": 11.78, "radius": 15},
    "Scottish Highlands": {"lat": 56.82, "lon": -5.10, "radius": 25},
    "New England, USA": {"lat": 43.20, "lon": -72.50, "radius": 25},
    "French Countryside": {"lat": 46.50, "lon": 2.50, "radius": 25},
    "Spanish Rural Lines": {"lat": 40.00, "lon": -3.50, "radius": 25},
    "Japanese Heritage Lines": {"lat": 36.20, "lon": 139.10, "radius": 25},
}

FUNICULAR_PRESETS = {
    "Custom": None,
    "Swiss Alps - Jungfrau": {"lat": 46.60, "lon": 7.97, "radius": 15},
    "Austrian Alps - Innsbruck": {"lat": 47.26, "lon": 11.39, "radius": 15},
    "Welsh Narrow Gauge": {"lat": 53.00, "lon": -4.05, "radius": 20},
    "Darjeeling Area, India": {"lat": 27.04, "lon": 88.26, "radius": 10},
    "Norwegian Fjords": {"lat": 60.80, "lon": 7.00, "radius": 20},
    "Lisbon Funiculars": {"lat": 38.72, "lon": -9.14, "radius": 5},
    "Naples & Vesuvius": {"lat": 40.85, "lon": 14.27, "radius": 10},
    "Valparaiso, Chile": {"lat": -33.05, "lon": -71.62, "radius": 5},
    "Budapest Funiculars": {"lat": 47.50, "lon": 19.04, "radius": 5},
    "Hong Kong Peak Tram": {"lat": 22.27, "lon": 114.15, "radius": 5},
}

# =============================================================================
# CURATED DATA: HIGH-SPEED RAIL NETWORKS
# =============================================================================

HIGH_SPEED_ROUTES = [
    {
        "name": "TGV Paris - Lyon",
        "country": "France", "max_speed": 320,
        "color": "#ef4444", "year": 1981,
        "coords": [[48.84, 2.37], [47.32, 3.51], [46.20, 4.83], [45.76, 4.84]],
        "desc": "First European high-speed line. Revolutionized rail travel in France.",
    },
    {
        "name": "TGV Paris - Marseille",
        "country": "France", "max_speed": 320,
        "color": "#ef4444", "year": 2001,
        "coords": [[48.84, 2.37], [47.32, 3.51], [45.76, 4.84], [44.38, 4.80], [43.30, 5.38]],
        "desc": "LGV Mediterranee extension. Paris-Marseille in 3 hours.",
    },
    {
        "name": "Shinkansen Tokaido (Tokyo - Osaka)",
        "country": "Japan", "max_speed": 285,
        "color": "#f59e0b", "year": 1964,
        "coords": [[35.68, 139.77], [35.36, 139.09], [35.17, 136.91], [34.97, 135.76], [34.69, 135.50]],
        "desc": "World's first high-speed rail. Opened for 1964 Tokyo Olympics.",
    },
    {
        "name": "Shinkansen Tohoku (Tokyo - Shin-Aomori)",
        "country": "Japan", "max_speed": 320,
        "color": "#f59e0b", "year": 2010,
        "coords": [[35.68, 139.77], [36.32, 139.81], [37.75, 140.46], [39.72, 140.10], [40.83, 140.73]],
        "desc": "Northern extension of Shinkansen. Fastest service: Hayabusa E5.",
    },
    {
        "name": "ICE Frankfurt - Cologne",
        "country": "Germany", "max_speed": 300,
        "color": "#10b981", "year": 2002,
        "coords": [[50.11, 8.68], [50.35, 7.59], [50.73, 7.10], [50.94, 6.96]],
        "desc": "Germany's fastest high-speed segment. Frankfurt to Cologne in 62 min.",
    },
    {
        "name": "ICE Berlin - Munich",
        "country": "Germany", "max_speed": 300,
        "color": "#10b981", "year": 2017,
        "coords": [[52.52, 13.37], [51.30, 12.37], [50.98, 11.03], [49.45, 11.08], [48.14, 11.56]],
        "desc": "VDE 8 new-build line. Berlin to Munich in under 4 hours.",
    },
    {
        "name": "AVE Madrid - Barcelona",
        "country": "Spain", "max_speed": 310,
        "color": "#8b5cf6", "year": 2008,
        "coords": [[40.41, -3.69], [41.07, -2.49], [41.65, -0.88], [41.38, 2.14]],
        "desc": "Spain's flagship AVE line. Madrid to Barcelona in 2h 30min.",
    },
    {
        "name": "AVE Madrid - Seville",
        "country": "Spain", "max_speed": 300,
        "color": "#8b5cf6", "year": 1992,
        "coords": [[40.41, -3.69], [38.99, -3.93], [37.88, -4.78], [37.39, -5.97]],
        "desc": "Spain's first high-speed line. Built for Expo 92 in Seville.",
    },
    {
        "name": "Beijing - Shanghai HSR",
        "country": "China", "max_speed": 350,
        "color": "#ec4899", "year": 2011,
        "coords": [[39.90, 116.40], [38.05, 117.02], [36.67, 116.98], [34.75, 117.29], [32.19, 118.77], [31.24, 121.47]],
        "desc": "World's most profitable HSR. 1,318 km in 4h 18min.",
    },
    {
        "name": "Beijing - Guangzhou HSR",
        "country": "China", "max_speed": 350,
        "color": "#ec4899", "year": 2012,
        "coords": [[39.90, 116.40], [37.87, 114.52], [34.75, 113.65], [30.59, 114.31], [28.23, 113.00], [23.13, 113.26]],
        "desc": "World's longest HSR at 2,298 km. Beijing to Guangzhou in 8 hours.",
    },
    {
        "name": "KTX Seoul - Busan",
        "country": "South Korea", "max_speed": 305,
        "color": "#3b82f6", "year": 2004,
        "coords": [[37.55, 126.97], [36.80, 127.14], [35.87, 128.60], [35.11, 129.04]],
        "desc": "Korea's first KTX line. Seoul to Busan in 2h 15min.",
    },
    {
        "name": "Eurostar London - Paris",
        "country": "UK/France", "max_speed": 300,
        "color": "#06b6d4", "year": 1994,
        "coords": [[51.53, -0.13], [51.10, 1.08], [50.95, 1.87], [49.90, 2.30], [48.88, 2.36]],
        "desc": "Channel Tunnel service. London St Pancras to Paris Gare du Nord in 2h 16min.",
    },
    {
        "name": "Frecciarossa Rome - Milan",
        "country": "Italy", "max_speed": 300,
        "color": "#f97316", "year": 2009,
        "coords": [[41.90, 12.50], [43.32, 11.33], [44.50, 11.34], [44.65, 10.92], [45.47, 9.19]],
        "desc": "Italy's flagship high-speed. Rome to Milan in 2h 55min.",
    },
    {
        "name": "Thalys Paris - Brussels - Amsterdam",
        "country": "Belgium/Netherlands", "max_speed": 300,
        "color": "#ef4444", "year": 1996,
        "coords": [[48.88, 2.36], [50.46, 3.39], [50.84, 4.35], [52.08, 4.32], [52.38, 4.90]],
        "desc": "Cross-border high-speed linking 4 countries.",
    },
    {
        "name": "Haramain HSR (Mecca - Medina)",
        "country": "Saudi Arabia", "max_speed": 300,
        "color": "#22d3ee", "year": 2018,
        "coords": [[21.42, 39.83], [21.49, 39.24], [22.33, 39.10], [24.47, 39.61]],
        "desc": "Desert high-speed railway. Connects Islam's two holiest cities.",
    },
    {
        "name": "Mumbai - Ahmedabad HSR (under construction)",
        "country": "India", "max_speed": 320,
        "color": "#a855f7", "year": 2028,
        "coords": [[19.08, 72.88], [20.01, 73.02], [21.17, 72.83], [23.02, 72.57]],
        "desc": "India's first bullet train. Based on Shinkansen E5 technology.",
    },
]

# =============================================================================
# CURATED DATA: TRANS-SIBERIAN & EPIC ROUTES
# =============================================================================

EPIC_ROUTES = [
    {
        "name": "Trans-Siberian Railway",
        "length_km": 9289, "duration": "6 days 2 hours",
        "color": "#ef4444", "year": 1916,
        "coords": [
            [55.76, 37.62], [56.84, 60.60], [55.03, 73.37], [56.01, 92.85],
            [52.03, 113.50], [51.83, 107.58], [47.91, 106.91], [48.48, 135.07],
            [43.12, 131.87],
        ],
        "desc": "Moscow to Vladivostok. World's longest railway. Crosses 7 time zones.",
    },
    {
        "name": "Trans-Mongolian Railway",
        "length_km": 7621, "duration": "5 days",
        "color": "#f59e0b", "year": 1956,
        "coords": [
            [55.76, 37.62], [56.84, 60.60], [55.03, 73.37], [52.03, 113.50],
            [51.83, 107.58], [47.91, 106.91], [43.65, 112.00], [39.90, 116.40],
        ],
        "desc": "Moscow to Beijing via Ulaanbaatar. Branches from Trans-Siberian at Ulan-Ude.",
    },
    {
        "name": "Orient Express (Original)",
        "length_km": 2740, "duration": "3 days (historic)",
        "color": "#8b5cf6", "year": 1883,
        "coords": [
            [48.88, 2.36], [48.58, 7.73], [48.14, 11.56], [48.21, 16.37],
            [47.50, 19.04], [44.43, 26.10], [41.01, 28.98],
        ],
        "desc": "Paris to Constantinople. World's most famous luxury train (1883-2009).",
    },
    {
        "name": "Trans-Canadian Railway",
        "length_km": 4466, "duration": "4 days 4 hours",
        "color": "#10b981", "year": 1885,
        "coords": [
            [43.65, -79.38], [46.81, -71.21], [45.51, -73.57], [49.90, -97.14],
            [51.05, -114.07], [51.45, -116.98], [49.28, -123.12],
        ],
        "desc": "Toronto to Vancouver. VIA Rail's 'The Canadian' crosses prairies and Rockies.",
    },
    {
        "name": "Indian Pacific",
        "length_km": 4352, "duration": "65 hours",
        "color": "#3b82f6", "year": 1970,
        "coords": [
            [-33.88, 151.21], [-33.75, 149.13], [-31.95, 141.47],
            [-34.93, 138.60], [-30.75, 121.47], [-31.95, 115.86],
        ],
        "desc": "Sydney to Perth. Crosses the Nullarbor Plain with world's longest straight track (478 km).",
    },
    {
        "name": "Glacier Express",
        "length_km": 291, "duration": "8 hours",
        "color": "#06b6d4", "year": 1930,
        "coords": [
            [46.02, 7.75], [46.31, 7.64], [46.49, 7.98], [46.63, 8.60],
            [46.68, 8.85], [46.84, 9.85],
        ],
        "desc": "Zermatt to St. Moritz. 'Slowest express train in the world'. 291 bridges, 91 tunnels.",
    },
    {
        "name": "The Ghan",
        "length_km": 2979, "duration": "54 hours",
        "color": "#ec4899", "year": 1929,
        "coords": [
            [-34.93, 138.60], [-29.01, 134.75], [-23.70, 133.87],
            [-19.27, 134.16], [-12.46, 130.84],
        ],
        "desc": "Adelaide to Darwin. Named after Afghan cameleers. Crosses the Australian Outback.",
    },
    {
        "name": "Blue Train (South Africa)",
        "length_km": 1600, "duration": "27 hours",
        "color": "#3b82f6", "year": 1946,
        "coords": [
            [-33.92, 18.42], [-32.35, 19.03], [-29.86, 22.49],
            [-28.74, 24.76], [-25.75, 28.19],
        ],
        "desc": "Cape Town to Pretoria. Luxury train through South African landscapes.",
    },
    {
        "name": "Rocky Mountaineer",
        "length_km": 1050, "duration": "2 days",
        "color": "#22d3ee", "year": 1990,
        "coords": [
            [49.28, -123.12], [50.11, -122.95], [50.68, -120.34],
            [51.05, -118.07], [51.18, -115.57], [51.05, -114.07],
        ],
        "desc": "Vancouver to Banff/Calgary. Daylight-only travel through Canadian Rockies.",
    },
    {
        "name": "Rovos Rail (Pride of Africa)",
        "length_km": 1600, "duration": "3 days",
        "color": "#f97316", "year": 1989,
        "coords": [
            [-25.75, 28.19], [-26.20, 28.05], [-28.74, 24.76],
            [-29.12, 26.21], [-33.92, 18.42],
        ],
        "desc": "Pretoria to Cape Town. 'Most luxurious train in the world'.",
    },
    {
        "name": "Belmond Royal Scotsman",
        "length_km": 700, "duration": "4 days",
        "color": "#a855f7", "year": 1985,
        "coords": [
            [55.95, -3.19], [56.40, -3.43], [56.65, -5.05],
            [57.48, -4.22], [57.60, -5.94], [57.27, -5.52],
        ],
        "desc": "Edinburgh circular. Scottish Highlands luxury rail cruise.",
    },
    {
        "name": "Maharajas' Express",
        "length_km": 2500, "duration": "7 days",
        "color": "#f59e0b", "year": 2010,
        "coords": [
            [28.64, 77.22], [27.18, 77.02], [26.92, 75.79],
            [24.58, 73.68], [23.02, 72.57], [19.08, 72.88],
        ],
        "desc": "Delhi to Mumbai via Agra, Jaipur, Udaipur. India's most luxurious train.",
    },
]

# =============================================================================
# CURATED DATA: HISTORIC RAILWAYS (FIRSTS)
# =============================================================================

HISTORIC_RAILWAYS = [
    {"name": "Stockton & Darlington Railway", "year": 1825, "country": "England",
     "lat": 54.57, "lon": -1.57, "color": "#ef4444",
     "desc": "World's first public steam-powered railway. Opened 27 Sep 1825."},
    {"name": "Liverpool & Manchester Railway", "year": 1830, "country": "England",
     "lat": 53.41, "lon": -2.23, "color": "#ef4444",
     "desc": "First inter-city passenger railway. George Stephenson's Rocket."},
    {"name": "Canterbury & Whitstable Railway", "year": 1830, "country": "England",
     "lat": 51.28, "lon": 1.08, "color": "#f59e0b",
     "desc": "First regular passenger service. Used both locomotive and cable haulage."},
    {"name": "Baltimore & Ohio Railroad", "year": 1830, "country": "USA",
     "lat": 39.29, "lon": -76.62, "color": "#3b82f6",
     "desc": "First common carrier railroad in the United States."},
    {"name": "Saint-Etienne - Andrezieux Railway", "year": 1827, "country": "France",
     "lat": 45.44, "lon": 4.39, "color": "#8b5cf6",
     "desc": "First railway in continental Europe. Initially horse-drawn."},
    {"name": "Brussels - Mechelen Railway", "year": 1835, "country": "Belgium",
     "lat": 50.85, "lon": 4.35, "color": "#10b981",
     "desc": "First railway in continental Europe built by a national government."},
    {"name": "Nuremberg - Furth Railway", "year": 1835, "country": "Germany",
     "lat": 49.45, "lon": 11.08, "color": "#10b981",
     "desc": "First railway in Germany. 'Adler' locomotive by Stephenson."},
    {"name": "Naples - Portici Railway", "year": 1839, "country": "Italy",
     "lat": 40.85, "lon": 14.27, "color": "#f97316",
     "desc": "First railway in the Italian peninsula. 7.4 km long."},
    {"name": "Amsterdam - Haarlem Railway", "year": 1839, "country": "Netherlands",
     "lat": 52.38, "lon": 4.64, "color": "#22d3ee",
     "desc": "First railway in the Netherlands. 'De Arend' locomotive."},
    {"name": "Vienna - Deutsch-Wagram", "year": 1837, "country": "Austria",
     "lat": 48.23, "lon": 16.38, "color": "#ec4899",
     "desc": "First steam railway in the Austrian Empire (Kaiser Ferdinand Nordbahn)."},
    {"name": "First Indian Railway (Mumbai)", "year": 1853, "country": "India",
     "lat": 19.08, "lon": 72.88, "color": "#a855f7",
     "desc": "Bombay to Thane. First railway in Asia. 34 km, 3 locomotives."},
    {"name": "First Japanese Railway (Tokyo)", "year": 1872, "country": "Japan",
     "lat": 35.63, "lon": 139.74, "color": "#f59e0b",
     "desc": "Shimbashi to Yokohama. Opened Japan's railway era."},
    {"name": "First Australian Railway (Melbourne)", "year": 1854, "country": "Australia",
     "lat": -37.82, "lon": 144.95, "color": "#3b82f6",
     "desc": "Melbourne to Port Melbourne. First steam railway in Australia."},
    {"name": "Cuba Railroad", "year": 1837, "country": "Cuba",
     "lat": 22.41, "lon": -79.97, "color": "#10b981",
     "desc": "Havana to Bejucal. First railway in Latin America and the Caribbean."},
    {"name": "First Russian Railway (St. Petersburg)", "year": 1837, "country": "Russia",
     "lat": 59.93, "lon": 30.32, "color": "#ef4444",
     "desc": "Tsarskoye Selo Railway. St Petersburg to Tsarskoye Selo."},
    {"name": "First Canadian Railway (Montreal)", "year": 1836, "country": "Canada",
     "lat": 45.50, "lon": -73.57, "color": "#ec4899",
     "desc": "Champlain & St Lawrence Railroad. First railway in Canada."},
    {"name": "First Swiss Railway (Zurich)", "year": 1847, "country": "Switzerland",
     "lat": 47.38, "lon": 8.54, "color": "#06b6d4",
     "desc": "Zurich to Baden. 'Spanisch-Brotli-Bahn' (Spanish Bun Railway)."},
    {"name": "First Swedish Railway", "year": 1856, "country": "Sweden",
     "lat": 58.59, "lon": 13.82, "color": "#3b82f6",
     "desc": "Gothenburg to Jonkoping section. Start of Swedish rail network."},
    {"name": "First Norwegian Railway", "year": 1854, "country": "Norway",
     "lat": 59.91, "lon": 10.75, "color": "#8b5cf6",
     "desc": "Christiania (Oslo) to Eidsvoll. 'Hovedbanen' main line."},
    {"name": "First Chinese Railway (Shanghai)", "year": 1876, "country": "China",
     "lat": 31.24, "lon": 121.47, "color": "#ec4899",
     "desc": "Woosung Road. Short-lived first railway, dismantled by Qing government."},
    {"name": "Transcontinental Railroad (USA)", "year": 1869, "country": "USA",
     "lat": 41.62, "lon": -112.55, "color": "#f59e0b",
     "desc": "Promontory Summit, Utah. Golden Spike ceremony linked East and West."},
    {"name": "First South American Railway (Chile)", "year": 1851, "country": "Chile",
     "lat": -29.91, "lon": -71.25, "color": "#10b981",
     "desc": "Copiapo to Caldera. First railway in South America."},
]

# =============================================================================
# CURATED DATA: SCENIC RAILWAY ROUTES
# =============================================================================

SCENIC_ROUTES = [
    {"name": "Bernina Express", "country": "Switzerland", "color": "#ef4444",
     "coords": [[46.50, 9.84], [46.37, 10.02], [46.33, 10.02], [46.17, 10.14]],
     "desc": "UNESCO World Heritage. Crosses the Alps at 2,253m. 55 tunnels, 196 bridges."},
    {"name": "Flam Railway", "country": "Norway", "color": "#3b82f6",
     "coords": [[60.86, 7.11], [60.83, 7.08], [60.78, 7.06], [60.73, 7.03]],
     "desc": "One of steepest railways. 20 km descent of 863m through Norwegian fjords."},
    {"name": "West Highland Line", "country": "Scotland", "color": "#10b981",
     "coords": [[55.86, -4.25], [56.38, -4.63], [56.67, -5.10], [56.83, -5.44], [56.87, -5.83]],
     "desc": "Glasgow to Mallaig. Crosses Glenfinnan Viaduct (Harry Potter bridge)."},
    {"name": "Darjeeling Himalayan Railway", "country": "India", "color": "#f59e0b",
     "coords": [[26.72, 88.35], [26.87, 88.32], [27.01, 88.26], [27.04, 88.27]],
     "desc": "UNESCO World Heritage. 'Toy Train' climbs to 2,200m in the Himalayas."},
    {"name": "Bergen Railway", "country": "Norway", "color": "#8b5cf6",
     "coords": [[59.91, 10.75], [60.23, 9.62], [60.73, 7.88], [60.59, 6.67], [60.39, 5.33]],
     "desc": "Oslo to Bergen. Crosses Hardangervidda plateau at 1,222m altitude."},
    {"name": "Semmering Railway", "country": "Austria", "color": "#ec4899",
     "coords": [[47.70, 15.83], [47.63, 15.88], [47.62, 15.93]],
     "desc": "First mountain railway. UNESCO World Heritage (1854). 16 viaducts, 15 tunnels."},
    {"name": "Jacobite Steam Train", "country": "Scotland", "color": "#22d3ee",
     "coords": [[56.82, -5.10], [56.86, -5.44], [56.87, -5.83]],
     "desc": "Fort William to Mallaig. The real 'Hogwarts Express' across the Glenfinnan Viaduct."},
    {"name": "Nilgiri Mountain Railway", "country": "India", "color": "#a855f7",
     "coords": [[11.35, 76.76], [11.37, 76.70], [11.40, 76.69], [11.41, 76.70]],
     "desc": "UNESCO World Heritage. Rack railway climbing to Ooty at 2,203m."},
    {"name": "TranzAlpine", "country": "New Zealand", "color": "#06b6d4",
     "coords": [[-43.53, 172.64], [-43.14, 171.75], [-42.97, 171.38], [-42.45, 171.21]],
     "desc": "Christchurch to Greymouth. Crosses Southern Alps via Arthur's Pass."},
    {"name": "Tren a las Nubes (Train to the Clouds)", "country": "Argentina", "color": "#f97316",
     "coords": [[-24.79, -65.41], [-24.22, -65.94], [-24.20, -66.00]],
     "desc": "Reaches 4,220m altitude. One of the highest railways in the world."},
    {"name": "Cinque Terre Railway", "country": "Italy", "color": "#10b981",
     "coords": [[44.15, 9.65], [44.13, 9.70], [44.12, 9.72], [44.10, 9.74], [44.09, 9.82]],
     "desc": "Along the Italian Riviera. Connects five colorful cliffside villages."},
    {"name": "Kandy to Ella Railway", "country": "Sri Lanka", "color": "#3b82f6",
     "coords": [[7.29, 80.63], [7.05, 80.60], [6.87, 81.06]],
     "desc": "Through tea plantations, waterfalls, and misty mountains. One of Asia's best rides."},
    {"name": "Copper Canyon (El Chepe)", "country": "Mexico", "color": "#ef4444",
     "coords": [[25.79, -108.99], [27.02, -108.05], [27.51, -107.86]],
     "desc": "Through Mexico's Copper Canyon. Deeper and wider than the Grand Canyon."},
    {"name": "Old Patagonian Express (La Trochita)", "country": "Argentina", "color": "#8b5cf6",
     "coords": [[-43.25, -71.17], [-43.30, -71.12], [-43.43, -70.61]],
     "desc": "Narrow-gauge steam train through Patagonia. Inspiration for Paul Theroux's book."},
    {"name": "Douro Line", "country": "Portugal", "color": "#f59e0b",
     "coords": [[41.15, -8.61], [41.16, -8.10], [41.18, -7.44], [41.15, -7.08]],
     "desc": "Porto along the Douro River valley. Through port wine vineyards."},
    {"name": "Rhaetian Railway (Albula Line)", "country": "Switzerland", "color": "#ec4899",
     "coords": [[46.68, 9.68], [46.58, 9.86], [46.50, 9.84]],
     "desc": "UNESCO World Heritage. Spiral tunnels and viaducts through the Engadin."},
    {"name": "Settle-Carlisle Line", "country": "England", "color": "#64748b",
     "coords": [[54.07, -2.28], [54.23, -2.36], [54.38, -2.44], [54.89, -2.94]],
     "desc": "Crosses the Ribblehead Viaduct. England's most scenic railway line."},
    {"name": "Reunification Express", "country": "Vietnam", "color": "#22d3ee",
     "coords": [[21.03, 105.84], [18.80, 105.78], [16.07, 108.22], [12.25, 109.19], [10.82, 106.63]],
     "desc": "Hanoi to Ho Chi Minh City. 1,726 km along Vietnam's coast."},
    {"name": "Death Railway", "country": "Thailand", "color": "#f97316",
     "coords": [[13.74, 100.52], [14.00, 99.53], [14.06, 99.09], [13.93, 98.85]],
     "desc": "Bangkok to Nam Tok. Crosses the Bridge over River Kwai. WWII history."},
    {"name": "Qinghai-Tibet Railway", "country": "China", "color": "#a855f7",
     "coords": [[36.62, 101.78], [36.30, 100.13], [35.78, 95.00], [31.98, 91.11], [29.65, 91.10]],
     "desc": "World's highest railway. Reaches 5,072m at Tanggula Pass."},
    {"name": "Rauma Line", "country": "Norway", "color": "#06b6d4",
     "coords": [[62.57, 11.10], [62.57, 8.31], [62.57, 7.69]],
     "desc": "Through the Romsdal valley. Past Trollveggen, Europe's tallest vertical rock face."},
    {"name": "Kalka-Shimla Railway", "country": "India", "color": "#ef4444",
     "coords": [[30.85, 76.94], [31.05, 77.08], [31.10, 77.17]],
     "desc": "UNESCO World Heritage. 102 tunnels and 87 bridges in the Himalayas."},
    {"name": "Serra Verde Express", "country": "Brazil", "color": "#10b981",
     "coords": [[-25.43, -49.27], [-25.41, -49.06], [-25.52, -48.51]],
     "desc": "Curitiba to Morretes. Through Atlantic rainforest and Serra do Mar mountains."},
    {"name": "White Pass & Yukon Route", "country": "USA/Canada", "color": "#3b82f6",
     "coords": [[59.46, -135.31], [59.64, -135.06], [59.78, -135.01]],
     "desc": "Skagway, Alaska to Whitehorse. Built during the Klondike Gold Rush of 1898."},
    {"name": "Inlandsbanan", "country": "Sweden", "color": "#8b5cf6",
     "coords": [[57.78, 14.16], [61.27, 14.27], [63.17, 14.64], [66.34, 17.34], [67.86, 20.23]],
     "desc": "1,288 km through Swedish wilderness. Reindeer, forests, midnight sun."},
]

# =============================================================================
# CURATED DATA: RAILWAY BRIDGES & TUNNELS
# =============================================================================

RAILWAY_ENGINEERING = [
    {"name": "Gotthard Base Tunnel", "type": "Tunnel", "length_km": 57.1,
     "lat": 46.65, "lon": 8.60, "year": 2016, "country": "Switzerland", "color": "#3b82f6",
     "desc": "World's longest and deepest railway tunnel. 57.1 km under the Alps."},
    {"name": "Channel Tunnel", "type": "Tunnel", "length_km": 50.5,
     "lat": 51.01, "lon": 1.13, "year": 1994, "country": "UK/France", "color": "#ef4444",
     "desc": "Undersea tunnel linking England and France. 37.9 km undersea section."},
    {"name": "Seikan Tunnel", "type": "Tunnel", "length_km": 53.9,
     "lat": 41.33, "lon": 140.31, "year": 1988, "country": "Japan", "color": "#f59e0b",
     "desc": "Under the Tsugaru Strait. World's deepest railway tunnel at 240m below sea level."},
    {"name": "Lotschberg Base Tunnel", "type": "Tunnel", "length_km": 34.6,
     "lat": 46.53, "lon": 7.78, "year": 2007, "country": "Switzerland", "color": "#06b6d4",
     "desc": "Part of NRLA project. Key link in the European north-south rail corridor."},
    {"name": "Brenner Base Tunnel (under construction)", "type": "Tunnel", "length_km": 55.0,
     "lat": 47.00, "lon": 11.50, "year": 2032, "country": "Austria/Italy", "color": "#a855f7",
     "desc": "Will become world's longest underground railway tunnel at 55 km."},
    {"name": "Forth Bridge", "type": "Bridge", "length_km": 2.5,
     "lat": 56.00, "lon": -3.39, "year": 1890, "country": "Scotland", "color": "#ef4444",
     "desc": "Iconic cantilever bridge. UNESCO World Heritage. Engineering marvel of the Victorian era."},
    {"name": "Glenfinnan Viaduct", "type": "Bridge", "length_km": 0.38,
     "lat": 56.87, "lon": -5.43, "year": 1901, "country": "Scotland", "color": "#10b981",
     "desc": "21-arch concrete viaduct. Famous as the 'Harry Potter bridge' in films."},
    {"name": "Landwasser Viaduct", "type": "Bridge", "length_km": 0.14,
     "lat": 46.68, "lon": 9.68, "year": 1902, "country": "Switzerland", "color": "#ec4899",
     "desc": "UNESCO World Heritage. Iconic curved viaduct of the Rhaetian Railway."},
    {"name": "Ribblehead Viaduct", "type": "Bridge", "length_km": 0.44,
     "lat": 54.21, "lon": -2.36, "year": 1875, "country": "England", "color": "#f97316",
     "desc": "24 arches across Batty Moss. Icon of the Settle-Carlisle line."},
    {"name": "Millau Viaduct (Rail Access)", "type": "Bridge", "length_km": 2.5,
     "lat": 44.08, "lon": 3.02, "year": 2004, "country": "France", "color": "#8b5cf6",
     "desc": "World's tallest bridge structure at 343m. Though road bridge, connects rail corridors."},
    {"name": "Simplon Tunnel", "type": "Tunnel", "length_km": 19.8,
     "lat": 46.25, "lon": 8.00, "year": 1906, "country": "Switzerland/Italy", "color": "#22d3ee",
     "desc": "Connects Brig (Switzerland) and Iselle (Italy). Key transalpine corridor."},
    {"name": "Mont Cenis / Frejus Rail Tunnel", "type": "Tunnel", "length_km": 13.7,
     "lat": 45.15, "lon": 6.68, "year": 1871, "country": "France/Italy", "color": "#64748b",
     "desc": "World's first major Alpine tunnel. Pioneered compressed-air drilling."},
    {"name": "Viaduc de Garabit", "type": "Bridge", "length_km": 0.56,
     "lat": 44.98, "lon": 3.18, "year": 1885, "country": "France", "color": "#ef4444",
     "desc": "Designed by Gustave Eiffel. Truss arch bridge 122m above the River Truyere."},
    {"name": "Nine Arch Bridge (Demodara)", "type": "Bridge", "length_km": 0.09,
     "lat": 6.88, "lon": 81.06, "year": 1921, "country": "Sri Lanka", "color": "#10b981",
     "desc": "Built without steel. Iconic bridge on the Kandy-Ella scenic line."},
    {"name": "Tsing Ma Bridge (Rail/Road)", "type": "Bridge", "length_km": 2.16,
     "lat": 22.35, "lon": 114.07, "year": 1997, "country": "Hong Kong", "color": "#f59e0b",
     "desc": "World's longest suspension bridge carrying rail. Dual-deck design."},
    {"name": "Oresund Bridge", "type": "Bridge", "length_km": 7.85,
     "lat": 55.57, "lon": 12.85, "year": 2000, "country": "Denmark/Sweden", "color": "#3b82f6",
     "desc": "Combined road and rail bridge-tunnel. Links Copenhagen and Malmo."},
    {"name": "Danyang-Kunshan Grand Bridge", "type": "Bridge", "length_km": 164.8,
     "lat": 31.65, "lon": 120.98, "year": 2010, "country": "China", "color": "#ec4899",
     "desc": "World's longest bridge at 164.8 km. Carries Beijing-Shanghai HSR."},
    {"name": "Chenab Bridge", "type": "Bridge", "length_km": 1.3,
     "lat": 33.15, "lon": 74.85, "year": 2022, "country": "India", "color": "#a855f7",
     "desc": "World's highest railway bridge at 359m above the Chenab River."},
    {"name": "Hoosac Tunnel", "type": "Tunnel", "length_km": 7.6,
     "lat": 42.68, "lon": -72.94, "year": 1875, "country": "USA", "color": "#f97316",
     "desc": "First major tunnel in North America. Pioneered use of nitroglycerin in construction."},
    {"name": "Cascade Tunnel", "type": "Tunnel", "length_km": 12.5,
     "lat": 47.76, "lon": -121.16, "year": 1929, "country": "USA", "color": "#64748b",
     "desc": "Longest railway tunnel in the Americas. Through the Cascade Range, Washington State."},
    {"name": "Stormyrdiep Bridge (Ofoten Line)", "type": "Bridge", "length_km": 0.07,
     "lat": 68.44, "lon": 17.39, "year": 1902, "country": "Norway", "color": "#06b6d4",
     "desc": "On the northernmost railway in Europe. Narvik iron ore line above the Arctic Circle."},
]

# =============================================================================
# CURATED DATA: TRAIN STATION ARCHITECTURE
# =============================================================================

ARCHITECTURAL_STATIONS = [
    {"name": "Grand Central Terminal", "city": "New York, USA", "year": 1913,
     "lat": 40.7527, "lon": -73.9772, "style": "Beaux-Arts", "color": "#f59e0b",
     "desc": "Iconic Beaux-Arts masterpiece. Celestial ceiling, 44 platforms, 67 tracks."},
    {"name": "St Pancras International", "city": "London, UK", "year": 1868,
     "lat": 51.5318, "lon": -0.1262, "style": "Victorian Gothic", "color": "#ef4444",
     "desc": "Victorian Gothic masterpiece by George Gilbert Scott. Barlow train shed spans 73m."},
    {"name": "Gare du Nord", "city": "Paris, France", "year": 1864,
     "lat": 48.8809, "lon": 2.3553, "style": "Neoclassical", "color": "#8b5cf6",
     "desc": "Busiest station in Europe. Neoclassical facade with 23 statues."},
    {"name": "Chhatrapati Shivaji Maharaj Terminus", "city": "Mumbai, India", "year": 1888,
     "lat": 18.9402, "lon": 72.8356, "style": "Victorian Gothic Revival", "color": "#ec4899",
     "desc": "UNESCO World Heritage. Blend of Victorian Gothic and Indian architecture."},
    {"name": "Antwerp-Centraal", "city": "Antwerp, Belgium", "year": 1905,
     "lat": 51.2172, "lon": 4.4213, "style": "Eclectic/Art Nouveau", "color": "#10b981",
     "desc": "Called the 'Railway Cathedral'. Massive stone and iron dome."},
    {"name": "Milano Centrale", "city": "Milan, Italy", "year": 1931,
     "lat": 45.4861, "lon": 9.2047, "style": "Art Deco/Assyrian", "color": "#06b6d4",
     "desc": "Monumental Art Deco design by Ulisse Stacchini. One of Europe's largest stations."},
    {"name": "Sao Bento Station", "city": "Porto, Portugal", "year": 1916,
     "lat": 41.1457, "lon": -8.6105, "style": "Beaux-Arts", "color": "#f97316",
     "desc": "Famous for 20,000 azulejo tiles depicting Portuguese history."},
    {"name": "Atocha Station", "city": "Madrid, Spain", "year": 1892,
     "lat": 40.4065, "lon": -3.6900, "style": "Iron & Glass / Tropical Garden", "color": "#22d3ee",
     "desc": "Old hall converted to tropical garden with 7,000 plants. Rafael Moneo renovation."},
    {"name": "Kanazawa Station", "city": "Kanazawa, Japan", "year": 2005,
     "lat": 36.5781, "lon": 136.6476, "style": "Modern / Traditional Japanese", "color": "#a855f7",
     "desc": "Tsuzumi Gate in wood and glass. Voted one of the world's most beautiful stations."},
    {"name": "Liege-Guillemins", "city": "Liege, Belgium", "year": 2009,
     "lat": 50.6244, "lon": 5.5665, "style": "Futuristic / Santiago Calatrava", "color": "#3b82f6",
     "desc": "Calatrava's glass and steel masterpiece. Soaring white arched roof."},
    {"name": "Berlin Hauptbahnhof", "city": "Berlin, Germany", "year": 2006,
     "lat": 52.5251, "lon": 13.3694, "style": "Modern Glass", "color": "#ef4444",
     "desc": "Europe's largest crossing station. Multi-level glass and steel design."},
    {"name": "Union Station", "city": "Washington DC, USA", "year": 1907,
     "lat": 38.8973, "lon": -77.0064, "style": "Beaux-Arts", "color": "#f59e0b",
     "desc": "Daniel Burnham's Beaux-Arts masterpiece. White granite, gold leaf, 96-foot ceilings."},
    {"name": "Kuala Lumpur Railway Station", "city": "Kuala Lumpur, Malaysia", "year": 1911,
     "lat": 3.1380, "lon": 101.6860, "style": "Moorish Revival", "color": "#10b981",
     "desc": "A.B. Hubback's Mughal-Moorish design. White minarets and horseshoe arches."},
    {"name": "Helsinki Central Station", "city": "Helsinki, Finland", "year": 1919,
     "lat": 60.1719, "lon": 24.9414, "style": "Art Nouveau / National Romantic", "color": "#ec4899",
     "desc": "Eliel Saarinen's landmark. Iconic granite statues holding spherical lanterns."},
    {"name": "Maputo Railway Station", "city": "Maputo, Mozambique", "year": 1916,
     "lat": -25.9653, "lon": 32.5718, "style": "Beaux-Arts / Neo-Manueline", "color": "#8b5cf6",
     "desc": "Often attributed to Gustave Eiffel. Green copper dome and marble interior."},
    {"name": "Dunedin Railway Station", "city": "Dunedin, New Zealand", "year": 1906,
     "lat": -45.8991, "lon": 170.4779, "style": "Flemish Renaissance", "color": "#06b6d4",
     "desc": "George Troup's masterpiece. Dark basalt with white Oamaru limestone."},
    {"name": "Constitución Station", "city": "Buenos Aires, Argentina", "year": 1897,
     "lat": -34.6272, "lon": -58.3856, "style": "Eclectic / Beaux-Arts", "color": "#f97316",
     "desc": "Grand Beaux-Arts structure. One of the busiest stations in South America."},
    {"name": "Gare de Strasbourg", "city": "Strasbourg, France", "year": 1883,
     "lat": 48.5850, "lon": 7.7349, "style": "Neo-Renaissance + Modern Glass", "color": "#22d3ee",
     "desc": "Historic facade enclosed in a stunning modern glass bubble (2007 renovation)."},
    {"name": "Haydarpaşa Terminal", "city": "Istanbul, Turkey", "year": 1909,
     "lat": 40.9971, "lon": 29.0194, "style": "German Neo-Renaissance", "color": "#a855f7",
     "desc": "Waterfront terminus on the Asian side. Gateway to Anatolia."},
    {"name": "Hua Hin Railway Station", "city": "Hua Hin, Thailand", "year": 1926,
     "lat": 12.5710, "lon": 99.9520, "style": "Victorian / Thai", "color": "#ef4444",
     "desc": "Thailand's most beautiful station. Royal waiting room from Nakhon Pathom."},
    {"name": "Jaipur Junction", "city": "Jaipur, India", "year": 1874,
     "lat": 26.9194, "lon": 75.7878, "style": "Rajasthani / Colonial", "color": "#f59e0b",
     "desc": "Pink sandstone design matching the Pink City. Blend of Rajput and colonial styles."},
    {"name": "Tokyo Station", "city": "Tokyo, Japan", "year": 1914,
     "lat": 35.6812, "lon": 139.7671, "style": "Red Brick / European", "color": "#10b981",
     "desc": "Tatsuno Kingo's red-brick landmark. Restored to original 1914 grandeur in 2012."},
    {"name": "Penn Station (original, demolished)", "city": "New York, USA", "year": 1910,
     "lat": 40.7506, "lon": -73.9935, "style": "Beaux-Arts (demolished 1963)", "color": "#64748b",
     "desc": "McKim, Mead & White masterpiece. Its demolition sparked the preservation movement."},
    {"name": "Rossio Station", "city": "Lisbon, Portugal", "year": 1890,
     "lat": 38.7149, "lon": -9.1413, "style": "Neo-Manueline", "color": "#3b82f6",
     "desc": "Horseshoe-arch entrance in Neo-Manueline style. Built into a hillside."},
    {"name": "Flinders Street Station", "city": "Melbourne, Australia", "year": 1909,
     "lat": -37.8183, "lon": 144.9671, "style": "Edwardian Baroque", "color": "#ec4899",
     "desc": "Melbourne's iconic landmark. Famous clocks and golden facade."},
]

# =============================================================================
# UTILITY HELPERS
# =============================================================================

def _bbox_from_center(lat: float, lon: float, radius_km: float):
    """Compute south, west, north, east from center + radius in km."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.01, abs(math.cos(math.radians(lat)))))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def _bbox_str(south, west, north, east):
    return f"{south},{west},{north},{east}"


def _build_folium_map(lat, lon, zoom=11):
    """Create base dark folium map."""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )
    return m


def _render_map(m, height=500):
    """Render folium map via components.html."""
    components.html(m._repr_html_(), height=height)


def _safe_popup(name, category="", extras=None):
    """Build an HTML popup with escaped user content."""
    parts = [f"<strong>{escape(str(name))}</strong>"]
    if category:
        parts.append(f"<br/><span style='font-size:0.85rem;'>{escape(str(category))}</span>")
    if extras:
        for k, v in extras.items():
            parts.append(
                f"<br/><span style='font-size:0.8rem;'>{escape(str(k))}: {escape(str(v))}</span>"
            )
    return folium.Popup("".join(parts), max_width=280)


def _overpass_result_ok(result):
    """Check if overpass result is usable."""
    if result is None:
        st.error("All Overpass servers unreachable. Check your internet connection.")
        return False
    if "_error" in result:
        st.error(f"Overpass query failed: {result['_error']}. Try a smaller area or retry later.")
        return False
    return True


def _build_node_lookup(elements):
    """Build id -> (lat, lon) mapping for nodes."""
    lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lookup[el["id"]] = (el["lat"], el["lon"])
    return lookup


def _way_coords(way, node_lookup):
    """Resolve a way's node references to coordinate list."""
    coords = []
    for nid in way.get("nodes", []):
        if nid in node_lookup:
            coords.append(node_lookup[nid])
    return coords


def _way_centroid(coords):
    """Compute centroid of a coordinate list."""
    if not coords:
        return None, None
    lat = sum(c[0] for c in coords) / len(coords)
    lon = sum(c[1] for c in coords) / len(coords)
    return lat, lon


def _features_to_dataframe(features, columns=None):
    """Convert feature dicts to a pandas DataFrame."""
    if not features:
        return pd.DataFrame()
    df = pd.DataFrame(features)
    if columns:
        available = [c for c in columns if c in df.columns]
        df = df[available]
    return df


def _make_chart(cat_counts, title="Distribution", palette=None):
    """Create a horizontal bar chart with dark theme."""
    if not cat_counts:
        return
    fig, ax = plt.subplots(figsize=(6, max(2.5, len(cat_counts) * 0.45)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    cats = list(cat_counts.keys())
    counts = list(cat_counts.values())
    if palette:
        colors = [palette.get(c, "#06b6d4") for c in cats]
    else:
        colors = ["#06b6d4"] * len(cats)

    ax.barh(range(len(cats)), counts, color=colors, alpha=0.85)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels([c[:30] for c in cats], color="#8b97b0", fontsize=9)
    ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=8)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _download_section(features, prefix="railway"):
    """Render CSV and GeoJSON download buttons."""
    if not features:
        return
    df = _features_to_dataframe(features)
    st.markdown("---")
    st.markdown("#### Export Data")
    dl1, dl2 = st.columns(2)
    with dl1:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download CSV ({len(features)} features)",
            data=csv_buf.getvalue(),
            file_name=f"{prefix}_data.csv",
            mime="text/csv",
            key=f"rw_{prefix}_dl_csv",
            width="stretch",
        )
    with dl2:
        geojson_features = []
        for feat in features:
            lat = feat.get("lat") or feat.get("latitude")
            lon = feat.get("lon") or feat.get("longitude")
            if lat is not None and lon is not None:
                geojson_features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {k: v for k, v in feat.items()
                                   if k not in ("lat", "lon", "latitude", "longitude", "coords")},
                })
        geojson_col = {"type": "FeatureCollection", "features": geojson_features}
        st.download_button(
            "Download GeoJSON",
            data=json.dumps(geojson_col, indent=2, ensure_ascii=False),
            file_name=f"{prefix}_data.geojson",
            mime="application/json",
            key=f"rw_{prefix}_dl_geojson",
            width="stretch",
        )


def _location_controls(prefix, presets, default_lat=48.0, default_lon=10.0,
                        default_radius=10, max_radius=50):
    """Shared location controls: preset selector, lat/lon/radius inputs."""
    preset_name = st.selectbox(
        "Preset Locations", list(presets.keys()), key=f"rw_{prefix}_preset"
    )
    p_lat, p_lon, p_rad = default_lat, default_lon, default_radius
    if preset_name != "Custom" and presets.get(preset_name):
        p = presets[preset_name]
        p_lat, p_lon, p_rad = p["lat"], p["lon"], p["radius"]

    c1, c2, c3 = st.columns(3)
    with c1:
        lat = st.number_input("Latitude", value=p_lat, format="%.4f",
                               min_value=-90.0, max_value=90.0, key=f"rw_{prefix}_lat")
    with c2:
        lon = st.number_input("Longitude", value=p_lon, format="%.4f",
                               min_value=-180.0, max_value=180.0, key=f"rw_{prefix}_lon")
    with c3:
        radius = st.slider("Radius (km)", 1, max_radius, p_rad, key=f"rw_{prefix}_radius")

    return lat, lon, radius


# =============================================================================
# DATA FETCHING FUNCTIONS (cached)
# =============================================================================

@st.cache_data(ttl=3600)
def _fetch_stations(south, west, north, east):
    """Fetch railway station features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  node["railway"="station"]({bbox});
  node["railway"="halt"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_metro(south, west, north, east):
    """Fetch metro/subway stations and entrances from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  node["railway"="subway_entrance"]({bbox});
  node["station"="subway"]({bbox});
  node["railway"="station"]["station"="subway"]({bbox});
  way["railway"="subway"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_abandoned(south, west, north, east):
    """Fetch abandoned/disused railway features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["railway"="abandoned"]({bbox});
  way["railway"="disused"]({bbox});
  node["railway"="abandoned"]({bbox});
  node["railway"="disused"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


@st.cache_data(ttl=3600)
def _fetch_funiculars(south, west, north, east):
    """Fetch funicular and narrow-gauge railway features from Overpass."""
    bbox = _bbox_str(south, west, north, east)
    q = f"""
[out:json][timeout:90];
(
  way["railway"="funicular"]({bbox});
  way["railway"="narrow_gauge"]({bbox});
  node["railway"="funicular"]({bbox});
  way["railway"="miniature"]({bbox});
  node["railway"="station"]["rack"="yes"]({bbox});
);
out body;
>;
out skel qt;
"""
    return query_overpass(q.strip())


# =============================================================================
# MODE 1: WORLD RAILWAY STATIONS
# =============================================================================

def _render_stations_mode():
    """Render World Railway Stations map."""
    st.markdown("##### World Railway Stations")
    st.caption("Discover railway stations and halts in any area using OpenStreetMap data.")

    lat, lon, radius = _location_controls("stations", STATION_PRESETS)

    if st.button("Search Stations", key="rw_stations_btn", type="primary"):
        south, west, north, east = _bbox_from_center(lat, lon, radius)
        with st.spinner("Querying Overpass API for railway stations..."):
            result = _fetch_stations(south, west, north, east)

        if not _overpass_result_ok(result):
            return

        elements = result.get("elements", [])
        stations = []
        for el in elements:
            if el.get("type") == "node" and "lat" in el and "lon" in el:
                tags = el.get("tags", {})
                name = tags.get("name", "Unnamed Station")
                stations.append({
                    "name": name,
                    "lat": el["lat"],
                    "lon": el["lon"],
                    "operator": tags.get("operator", "N/A"),
                    "railway": tags.get("railway", "station"),
                    "network": tags.get("network", "N/A"),
                    "platforms": tags.get("platforms", "N/A"),
                })

        if not stations:
            st.warning("No railway stations found in this area. Try a larger radius.")
            return

        # Stats
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Stations Found", len(stations))
        operators = set(s["operator"] for s in stations if s["operator"] != "N/A")
        sc2.metric("Operators", len(operators))
        named = sum(1 for s in stations if s["name"] != "Unnamed Station")
        sc3.metric("Named Stations", named)

        # Map
        m = _build_folium_map(lat, lon, zoom=12)
        for s in stations:
            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=6,
                color=RAILWAY_COLORS["stations"],
                fill=True,
                fill_color=RAILWAY_COLORS["stations"],
                fill_opacity=0.8,
                popup=_safe_popup(s["name"], "Railway Station", {
                    "Operator": s["operator"],
                    "Network": s["network"],
                    "Platforms": s["platforms"],
                }),
            ).add_to(m)
        _render_map(m)

        # Operator distribution
        op_counts = {}
        for s in stations:
            op = s["operator"] if s["operator"] != "N/A" else "Unknown"
            op_counts[op] = op_counts.get(op, 0) + 1
        if len(op_counts) > 1:
            top_ops = dict(sorted(op_counts.items(), key=lambda x: -x[1])[:15])
            _make_chart(top_ops, "Stations by Operator")

        # Table
        st.markdown("##### Station Data")
        df = _features_to_dataframe(stations,
            ["name", "lat", "lon", "operator", "network", "platforms", "railway"])
        st.dataframe(df, width="stretch")

        _download_section(stations, "railway_stations")


# =============================================================================
# MODE 2: HIGH-SPEED RAIL NETWORKS
# =============================================================================

def _render_highspeed_mode():
    """Render High-Speed Rail Networks map."""
    st.markdown("##### High-Speed Rail Networks")
    st.caption(
        "Major high-speed rail lines worldwide: TGV, Shinkansen, ICE, AVE, CRH, KTX, and more."
    )

    countries = sorted(set(r["country"] for r in HIGH_SPEED_ROUTES))
    selected = st.multiselect(
        "Filter by Country", countries, default=countries, key="rw_hs_countries"
    )

    routes = [r for r in HIGH_SPEED_ROUTES if r["country"] in selected]
    if not routes:
        st.info("Select at least one country to display routes.")
        return

    # Stats
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Routes Shown", len(routes))
    max_speed = max(r["max_speed"] for r in routes) if routes else 0
    sc2.metric("Top Speed (km/h)", max_speed)
    earliest = min(r["year"] for r in routes) if routes else 0
    sc3.metric("Earliest Service", earliest)
    sc4.metric("Countries", len(selected))

    # Map - world view
    m = _build_folium_map(35, 20, zoom=2)
    for r in routes:
        folium.PolyLine(
            locations=r["coords"],
            color=r["color"],
            weight=4,
            opacity=0.85,
            popup=_safe_popup(r["name"], f"{r['country']} | {r['max_speed']} km/h", {
                "Year": r["year"],
                "Info": r["desc"][:100],
            }),
            tooltip=escape(r["name"]),
        ).add_to(m)
        # Start marker
        folium.CircleMarker(
            location=r["coords"][0],
            radius=5,
            color=r["color"],
            fill=True,
            fill_color=r["color"],
            fill_opacity=0.9,
        ).add_to(m)
        # End marker
        folium.CircleMarker(
            location=r["coords"][-1],
            radius=5,
            color=r["color"],
            fill=True,
            fill_color=r["color"],
            fill_opacity=0.9,
        ).add_to(m)
    _render_map(m)

    # Speed chart
    speed_data = {r["name"][:35]: r["max_speed"] for r in sorted(routes, key=lambda x: -x["max_speed"])}
    _make_chart(speed_data, "Maximum Speed (km/h)")

    # Timeline chart
    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    years = [r["year"] for r in sorted(routes, key=lambda x: x["year"])]
    names = [r["name"][:30] for r in sorted(routes, key=lambda x: x["year"])]
    colors = [r["color"] for r in sorted(routes, key=lambda x: x["year"])]
    ax.barh(range(len(years)), years, color=colors, alpha=0.85)
    ax.set_yticks(range(len(years)))
    ax.set_yticklabels(names, color="#8b97b0", fontsize=8)
    ax.set_xlabel("Year Opened", color="#8b97b0", fontsize=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_title("High-Speed Rail Timeline", color="#e8ecf4", fontsize=11, pad=8)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    st.markdown("##### Route Details")
    features = []
    for r in routes:
        features.append({
            "name": r["name"], "country": r["country"],
            "max_speed": r["max_speed"], "year": r["year"],
            "description": r["desc"],
        })
    df = _features_to_dataframe(features)
    st.dataframe(df, width="stretch")


# =============================================================================
# MODE 3: TRANS-SIBERIAN & EPIC ROUTES
# =============================================================================

def _render_epic_routes_mode():
    """Render Trans-Siberian & Epic Routes map."""
    st.markdown("##### Trans-Siberian & Epic Routes")
    st.caption(
        "Legendary long-distance railway journeys: Trans-Siberian, Orient Express, "
        "Indian Pacific, Glacier Express, and more."
    )

    route_names = [r["name"] for r in EPIC_ROUTES]
    selected = st.multiselect(
        "Select Routes", route_names, default=route_names, key="rw_epic_select"
    )

    routes = [r for r in EPIC_ROUTES if r["name"] in selected]
    if not routes:
        st.info("Select at least one route to display.")
        return

    # Stats
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Routes Shown", len(routes))
    longest = max(r["length_km"] for r in routes)
    longest_name = next(r["name"] for r in routes if r["length_km"] == longest)
    sc2.metric("Longest Route", f"{longest:,} km")
    sc3.metric("Longest Name", longest_name[:25])

    # Map - world view
    m = _build_folium_map(30, 50, zoom=2)
    for r in routes:
        folium.PolyLine(
            locations=r["coords"],
            color=r["color"],
            weight=4,
            opacity=0.85,
            dash_array="8",
            popup=_safe_popup(r["name"], f"{r['length_km']:,} km | {r['duration']}", {
                "Year": r["year"],
                "Info": r["desc"][:120],
            }),
            tooltip=escape(r["name"]),
        ).add_to(m)
        # Start and end markers
        folium.Marker(
            location=r["coords"][0],
            popup=_safe_popup(f"{r['name']} - Start", "Departure"),
            icon=folium.Icon(color="green", icon="train", prefix="fa"),
        ).add_to(m)
        folium.Marker(
            location=r["coords"][-1],
            popup=_safe_popup(f"{r['name']} - End", "Arrival"),
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        ).add_to(m)
    _render_map(m)

    # Length comparison chart
    length_data = {r["name"][:30]: r["length_km"]
                   for r in sorted(routes, key=lambda x: -x["length_km"])}
    _make_chart(length_data, "Route Length (km)")

    # Table
    st.markdown("##### Route Details")
    features = []
    for r in routes:
        features.append({
            "name": r["name"], "length_km": r["length_km"],
            "duration": r["duration"], "year": r["year"],
            "description": r["desc"],
        })
    df = _features_to_dataframe(features)
    st.dataframe(df, width="stretch")


# =============================================================================
# MODE 4: HISTORIC RAILWAYS
# =============================================================================

def _render_historic_mode():
    """Render Historic Railways map."""
    st.markdown("##### Historic Railways - Firsts Around the World")
    st.caption(
        "Discover the world's first railways from the 1825 Stockton-Darlington to "
        "the transcontinental lines of the 1860s-1870s."
    )

    # Filter by decade
    decades = sorted(set((r["year"] // 10) * 10 for r in HISTORIC_RAILWAYS))
    decade_labels = [f"{d}s" for d in decades]
    selected_decades = st.multiselect(
        "Filter by Decade", decade_labels, default=decade_labels, key="rw_historic_decades"
    )
    selected_dec_vals = [int(d[:-1]) for d in selected_decades]
    railways = [r for r in HISTORIC_RAILWAYS if (r["year"] // 10) * 10 in selected_dec_vals]

    if not railways:
        st.info("Select at least one decade to display railways.")
        return

    # Stats
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Historic Railways", len(railways))
    countries = set(r["country"] for r in railways)
    sc2.metric("Countries", len(countries))
    oldest = min(r["year"] for r in railways)
    sc3.metric("Earliest", oldest)

    # Map
    m = _build_folium_map(40, 10, zoom=2)
    for r in railways:
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=9,
            color=r["color"],
            fill=True,
            fill_color=r["color"],
            fill_opacity=0.85,
            popup=_safe_popup(r["name"], f"{r['country']} | {r['year']}", {
                "Info": r["desc"],
            }),
            tooltip=escape(f"{r['name']} ({r['year']})"),
        ).add_to(m)
    _render_map(m)

    # Timeline chart
    fig, ax = plt.subplots(figsize=(8, max(3, len(railways) * 0.35)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    sorted_rw = sorted(railways, key=lambda x: x["year"])
    for i, r in enumerate(sorted_rw):
        ax.barh(i, r["year"], color=r["color"], alpha=0.85, left=0)
    ax.set_yticks(range(len(sorted_rw)))
    ax.set_yticklabels([f"{r['name'][:28]} ({r['country']})" for r in sorted_rw],
                        color="#8b97b0", fontsize=8)
    ax.set_xlabel("Year", color="#8b97b0", fontsize=10)
    ax.set_xlim(1820, max(r["year"] for r in sorted_rw) + 5)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_title("Railway Firsts Timeline", color="#e8ecf4", fontsize=11, pad=8)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Country distribution
    country_counts = {}
    for r in railways:
        country_counts[r["country"]] = country_counts.get(r["country"], 0) + 1
    _make_chart(country_counts, "Railways by Country")

    # Table
    st.markdown("##### Historic Railway Data")
    features = [{"name": r["name"], "year": r["year"], "country": r["country"],
                  "lat": r["lat"], "lon": r["lon"], "description": r["desc"]}
                 for r in sorted(railways, key=lambda x: x["year"])]
    df = _features_to_dataframe(features)
    st.dataframe(df, width="stretch")

    _download_section(features, "historic_railways")


# =============================================================================
# MODE 5: METRO SYSTEMS
# =============================================================================

def _render_metro_mode():
    """Render Metro Systems map."""
    st.markdown("##### Metro & Subway Systems")
    st.caption("Explore subway stations, entrances, and metro lines in major cities.")

    lat, lon, radius = _location_controls("metro", METRO_PRESETS)

    if st.button("Search Metro Stations", key="rw_metro_btn", type="primary"):
        south, west, north, east = _bbox_from_center(lat, lon, radius)
        with st.spinner("Querying Overpass API for metro systems..."):
            result = _fetch_metro(south, west, north, east)

        if not _overpass_result_ok(result):
            return

        elements = result.get("elements", [])
        node_lookup = _build_node_lookup(elements)

        stations = []
        lines = []
        for el in elements:
            tags = el.get("tags", {})
            if el.get("type") == "node" and "lat" in el and "lon" in el:
                rw = tags.get("railway", "")
                stn = tags.get("station", "")
                if rw in ("subway_entrance", "station") or stn == "subway":
                    name = tags.get("name", "Unnamed")
                    stations.append({
                        "name": name,
                        "lat": el["lat"],
                        "lon": el["lon"],
                        "type": "Entrance" if rw == "subway_entrance" else "Station",
                        "network": tags.get("network", "N/A"),
                        "line": tags.get("line", tags.get("colour", "N/A")),
                        "wheelchair": tags.get("wheelchair", "N/A"),
                    })
            elif el.get("type") == "way" and tags.get("railway") == "subway":
                coords = _way_coords(el, node_lookup)
                if coords:
                    lines.append({
                        "name": tags.get("name", "Metro Line"),
                        "coords": coords,
                        "colour": tags.get("colour", "#a855f7"),
                    })

        if not stations and not lines:
            st.warning("No metro features found in this area. Try a larger radius.")
            return

        # Stats
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Stations/Entrances", len(stations))
        sc2.metric("Line Segments", len(lines))
        networks = set(s["network"] for s in stations if s["network"] != "N/A")
        sc3.metric("Networks", len(networks))

        # Map
        m = _build_folium_map(lat, lon, zoom=12)
        for line in lines:
            color = line["colour"] if line["colour"].startswith("#") else "#a855f7"
            folium.PolyLine(
                locations=line["coords"],
                color=color,
                weight=3,
                opacity=0.7,
                popup=_safe_popup(line["name"], "Metro Line"),
            ).add_to(m)
        for s in stations:
            color = "#a855f7" if s["type"] == "Station" else "#ec4899"
            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=5 if s["type"] == "Entrance" else 7,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=_safe_popup(s["name"], s["type"], {
                    "Network": s["network"],
                    "Line": s["line"],
                    "Wheelchair": s["wheelchair"],
                }),
            ).add_to(m)
        _render_map(m)

        # Type distribution
        type_counts = {}
        for s in stations:
            type_counts[s["type"]] = type_counts.get(s["type"], 0) + 1
        if type_counts:
            _make_chart(type_counts, "Feature Types")

        # Table
        st.markdown("##### Metro Station Data")
        df = _features_to_dataframe(stations,
            ["name", "lat", "lon", "type", "network", "line", "wheelchair"])
        st.dataframe(df, width="stretch")

        _download_section(stations, "metro_systems")


# =============================================================================
# MODE 6: SCENIC RAILWAY ROUTES
# =============================================================================

def _render_scenic_mode():
    """Render Scenic Railway Routes map."""
    st.markdown("##### Scenic Railway Routes")
    st.caption(
        "The world's most spectacular train journeys: mountain passes, coastal routes, "
        "jungle railways, and UNESCO World Heritage lines."
    )

    countries = sorted(set(r["country"] for r in SCENIC_ROUTES))
    selected = st.multiselect(
        "Filter by Country", countries, default=countries, key="rw_scenic_countries"
    )

    routes = [r for r in SCENIC_ROUTES if r["country"] in selected]
    if not routes:
        st.info("Select at least one country to display routes.")
        return

    # Stats
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Scenic Routes", len(routes))
    sc2.metric("Countries", len(selected))
    continents = set()
    for r in routes:
        c = r["country"]
        if c in ("Switzerland", "Norway", "Scotland", "Austria", "Italy", "England",
                  "Portugal", "Sweden", "France", "Vietnam", "Thailand"):
            continents.add("Europe" if c not in ("Vietnam", "Thailand") else "Asia")
        elif c in ("India", "Sri Lanka", "China", "Japan"):
            continents.add("Asia")
        elif c in ("New Zealand", "Australia"):
            continents.add("Oceania")
        elif c in ("Argentina", "Mexico", "Brazil", "Chile"):
            continents.add("South America")
        elif c in ("USA/Canada", "USA"):
            continents.add("North America")
        else:
            continents.add("Other")
    sc3.metric("Continents", len(continents))

    # Map - world view
    m = _build_folium_map(25, 10, zoom=2)
    for r in routes:
        folium.PolyLine(
            locations=r["coords"],
            color=r["color"],
            weight=4,
            opacity=0.85,
            popup=_safe_popup(r["name"], r["country"], {
                "Info": r["desc"][:120],
            }),
            tooltip=escape(r["name"]),
        ).add_to(m)
        folium.CircleMarker(
            location=r["coords"][0],
            radius=6,
            color=r["color"],
            fill=True,
            fill_color=r["color"],
            fill_opacity=0.9,
            tooltip=escape(f"{r['name']} - Start"),
        ).add_to(m)
    _render_map(m)

    # Country distribution
    country_counts = {}
    for r in routes:
        country_counts[r["country"]] = country_counts.get(r["country"], 0) + 1
    _make_chart(country_counts, "Scenic Routes by Country")

    # Table
    st.markdown("##### Scenic Route Details")
    features = [{"name": r["name"], "country": r["country"], "description": r["desc"]}
                for r in routes]
    df = _features_to_dataframe(features)
    st.dataframe(df, width="stretch")


# =============================================================================
# MODE 7: RAILWAY BRIDGES & TUNNELS
# =============================================================================

def _render_engineering_mode():
    """Render Railway Bridges & Tunnels map."""
    st.markdown("##### Railway Bridges & Tunnels - Engineering Marvels")
    st.caption(
        "Gotthard Base Tunnel, Channel Tunnel, Forth Bridge, Chenab Bridge, "
        "and more iconic railway engineering achievements."
    )

    type_filter = st.radio(
        "Feature Type", ["All", "Bridges", "Tunnels"],
        horizontal=True, key="rw_eng_type"
    )

    if type_filter == "Bridges":
        features_data = [f for f in RAILWAY_ENGINEERING if f["type"] == "Bridge"]
    elif type_filter == "Tunnels":
        features_data = [f for f in RAILWAY_ENGINEERING if f["type"] == "Tunnel"]
    else:
        features_data = RAILWAY_ENGINEERING

    if not features_data:
        st.info("No features to display.")
        return

    # Stats
    sc1, sc2, sc3, sc4 = st.columns(4)
    bridges = [f for f in features_data if f["type"] == "Bridge"]
    tunnels = [f for f in features_data if f["type"] == "Tunnel"]
    sc1.metric("Total Features", len(features_data))
    sc2.metric("Bridges", len(bridges))
    sc3.metric("Tunnels", len(tunnels))
    longest = max(features_data, key=lambda x: x["length_km"])
    sc4.metric("Longest", f"{longest['length_km']} km")

    # Map
    m = _build_folium_map(46, 10, zoom=3)
    for f in features_data:
        color = "#3b82f6" if f["type"] == "Bridge" else "#ef4444"
        icon_name = "bridge" if f["type"] == "Bridge" else "road-tunnel"
        folium.Marker(
            location=[f["lat"], f["lon"]],
            popup=_safe_popup(f["name"], f"{f['type']} | {f['country']}", {
                "Length": f"{f['length_km']} km",
                "Year": f["year"],
                "Info": f["desc"][:120],
            }),
            icon=folium.Icon(
                color="blue" if f["type"] == "Bridge" else "red",
                icon="info-sign",
            ),
            tooltip=escape(f"{f['name']} ({f['year']})"),
        ).add_to(m)
    _render_map(m)

    # Length comparison chart
    length_data = {f["name"][:30]: f["length_km"]
                   for f in sorted(features_data, key=lambda x: -x["length_km"])[:15]}
    _make_chart(length_data, "Length (km)")

    # Timeline
    fig, ax = plt.subplots(figsize=(7, max(3, len(features_data) * 0.35)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    sorted_f = sorted(features_data, key=lambda x: x["year"])
    colors = ["#3b82f6" if f["type"] == "Bridge" else "#ef4444" for f in sorted_f]
    ax.barh(range(len(sorted_f)), [f["year"] for f in sorted_f], color=colors, alpha=0.85)
    ax.set_yticks(range(len(sorted_f)))
    ax.set_yticklabels([f"{f['name'][:28]}" for f in sorted_f],
                        color="#8b97b0", fontsize=8)
    ax.set_xlabel("Year", color="#8b97b0")
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_title("Engineering Marvels Timeline", color="#e8ecf4", fontsize=11, pad=8)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    st.markdown("##### Engineering Details")
    table_feats = [{
        "name": f["name"], "type": f["type"], "length_km": f["length_km"],
        "year": f["year"], "country": f["country"], "description": f["desc"],
        "lat": f["lat"], "lon": f["lon"],
    } for f in features_data]
    df = _features_to_dataframe(table_feats)
    st.dataframe(df, width="stretch")

    _download_section(table_feats, "railway_engineering")


# =============================================================================
# MODE 8: ABANDONED RAILWAYS
# =============================================================================

def _render_abandoned_mode():
    """Render Abandoned Railways map."""
    st.markdown("##### Abandoned & Disused Railways")
    st.caption(
        "Discover abandoned and disused railway lines. Many are now trails, "
        "greenways, or overgrown remnants of the railway age."
    )

    lat, lon, radius = _location_controls("abandoned", ABANDONED_PRESETS,
                                            default_lat=52.0, default_lon=-1.5,
                                            default_radius=15, max_radius=40)

    if st.button("Search Abandoned Railways", key="rw_abandoned_btn", type="primary"):
        south, west, north, east = _bbox_from_center(lat, lon, radius)
        with st.spinner("Querying Overpass API for abandoned railways..."):
            result = _fetch_abandoned(south, west, north, east)

        if not _overpass_result_ok(result):
            return

        elements = result.get("elements", [])
        node_lookup = _build_node_lookup(elements)

        features_list = []
        way_count = 0
        for el in elements:
            tags = el.get("tags", {})
            if el.get("type") == "way":
                coords = _way_coords(el, node_lookup)
                if not coords:
                    continue
                clat, clon = _way_centroid(coords)
                name = tags.get("name", tags.get("old_name", "Unnamed"))
                rw_type = tags.get("railway", "abandoned")
                features_list.append({
                    "name": name,
                    "lat": clat,
                    "lon": clon,
                    "type": rw_type,
                    "coords": coords,
                    "operator": tags.get("operator", tags.get("old_operator", "N/A")),
                    "gauge": tags.get("gauge", "N/A"),
                    "opening_date": tags.get("opening_date", "N/A"),
                })
                way_count += 1
            elif el.get("type") == "node" and "lat" in el and "lon" in el:
                rw = tags.get("railway", "")
                if rw in ("abandoned", "disused"):
                    features_list.append({
                        "name": tags.get("name", "Unnamed"),
                        "lat": el["lat"],
                        "lon": el["lon"],
                        "type": rw,
                        "coords": None,
                        "operator": tags.get("operator", "N/A"),
                        "gauge": tags.get("gauge", "N/A"),
                        "opening_date": tags.get("opening_date", "N/A"),
                    })

        if not features_list:
            st.warning("No abandoned railways found in this area. Try a larger radius.")
            return

        # Stats
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Features Found", len(features_list))
        sc2.metric("Line Segments", way_count)
        abandoned = sum(1 for f in features_list if f["type"] == "abandoned")
        disused = sum(1 for f in features_list if f["type"] == "disused")
        sc3.metric("Abandoned / Disused", f"{abandoned} / {disused}")

        # Map
        m = _build_folium_map(lat, lon, zoom=11)
        for f in features_list:
            if f["coords"]:
                folium.PolyLine(
                    locations=f["coords"],
                    color="#64748b" if f["type"] == "abandoned" else "#8b5cf6",
                    weight=3,
                    opacity=0.7,
                    dash_array="6",
                    popup=_safe_popup(f["name"], f["type"].title(), {
                        "Operator": f["operator"],
                        "Gauge": f["gauge"],
                    }),
                ).add_to(m)
            else:
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=5,
                    color="#64748b",
                    fill=True,
                    fill_color="#64748b",
                    fill_opacity=0.7,
                    popup=_safe_popup(f["name"], f["type"].title()),
                ).add_to(m)
        _render_map(m)

        # Type chart
        type_counts = {}
        for f in features_list:
            type_counts[f["type"].title()] = type_counts.get(f["type"].title(), 0) + 1
        if type_counts:
            _make_chart(type_counts, "Abandoned vs Disused")

        # Table
        st.markdown("##### Abandoned Railway Data")
        table_feats = [{k: v for k, v in f.items() if k != "coords"} for f in features_list]
        df = _features_to_dataframe(table_feats,
            ["name", "lat", "lon", "type", "operator", "gauge", "opening_date"])
        st.dataframe(df, width="stretch")

        _download_section(table_feats, "abandoned_railways")


# =============================================================================
# MODE 9: FUNICULARS & RACK RAILWAYS
# =============================================================================

def _render_funiculars_mode():
    """Render Funiculars & Rack Railways map."""
    st.markdown("##### Funiculars & Rack Railways")
    st.caption(
        "Discover funiculars, rack railways, and narrow-gauge lines. "
        "Mountain railways, heritage lines, and steep-grade marvels."
    )

    lat, lon, radius = _location_controls("funicular", FUNICULAR_PRESETS,
                                            default_lat=46.6, default_lon=8.0,
                                            default_radius=15, max_radius=40)

    if st.button("Search Funiculars & Rack Railways", key="rw_funicular_btn", type="primary"):
        south, west, north, east = _bbox_from_center(lat, lon, radius)
        with st.spinner("Querying Overpass API for funiculars and narrow-gauge..."):
            result = _fetch_funiculars(south, west, north, east)

        if not _overpass_result_ok(result):
            return

        elements = result.get("elements", [])
        node_lookup = _build_node_lookup(elements)

        features_list = []
        line_count = 0
        for el in elements:
            tags = el.get("tags", {})
            if el.get("type") == "way":
                coords = _way_coords(el, node_lookup)
                if not coords:
                    continue
                clat, clon = _way_centroid(coords)
                name = tags.get("name", "Unnamed")
                rw_type = tags.get("railway", "unknown")
                features_list.append({
                    "name": name,
                    "lat": clat,
                    "lon": clon,
                    "type": rw_type,
                    "coords": coords,
                    "operator": tags.get("operator", "N/A"),
                    "gauge": tags.get("gauge", "N/A"),
                    "rack": tags.get("rack", "N/A"),
                    "maxspeed": tags.get("maxspeed", "N/A"),
                })
                line_count += 1
            elif el.get("type") == "node" and "lat" in el and "lon" in el:
                rw = tags.get("railway", "")
                if rw in ("funicular", "station"):
                    features_list.append({
                        "name": tags.get("name", "Unnamed"),
                        "lat": el["lat"],
                        "lon": el["lon"],
                        "type": rw,
                        "coords": None,
                        "operator": tags.get("operator", "N/A"),
                        "gauge": tags.get("gauge", "N/A"),
                        "rack": tags.get("rack", "N/A"),
                        "maxspeed": tags.get("maxspeed", "N/A"),
                    })

        if not features_list:
            st.warning("No funiculars or rack railways found. Try a larger radius or different area.")
            return

        # Stats
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Features Found", len(features_list))
        sc2.metric("Line Segments", line_count)
        types = set(f["type"] for f in features_list)
        sc3.metric("Types", len(types))

        # Map
        m = _build_folium_map(lat, lon, zoom=11)
        type_colors = {
            "funicular": "#22d3ee",
            "narrow_gauge": "#f59e0b",
            "miniature": "#ec4899",
            "station": "#10b981",
        }
        for f in features_list:
            color = type_colors.get(f["type"], "#06b6d4")
            if f["coords"]:
                folium.PolyLine(
                    locations=f["coords"],
                    color=color,
                    weight=3,
                    opacity=0.8,
                    popup=_safe_popup(f["name"], f["type"].replace("_", " ").title(), {
                        "Operator": f["operator"],
                        "Gauge": f["gauge"],
                        "Rack": f["rack"],
                    }),
                ).add_to(m)
            else:
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.8,
                    popup=_safe_popup(f["name"], f["type"].replace("_", " ").title()),
                ).add_to(m)
        _render_map(m)

        # Type distribution
        type_counts = {}
        for f in features_list:
            label = f["type"].replace("_", " ").title()
            type_counts[label] = type_counts.get(label, 0) + 1
        if type_counts:
            _make_chart(type_counts, "Feature Type Distribution")

        # Table
        st.markdown("##### Funicular & Rack Railway Data")
        table_feats = [{k: v for k, v in f.items() if k != "coords"} for f in features_list]
        df = _features_to_dataframe(table_feats,
            ["name", "lat", "lon", "type", "operator", "gauge", "rack", "maxspeed"])
        st.dataframe(df, width="stretch")

        _download_section(table_feats, "funiculars_rack")


# =============================================================================
# MODE 10: TRAIN STATION ARCHITECTURE
# =============================================================================

def _render_architecture_mode():
    """Render Train Stations Architecture map."""
    st.markdown("##### Architecturally Significant Train Stations")
    st.caption(
        "Grand Central, St Pancras, Chhatrapati Shivaji, Antwerp-Centraal, "
        "and more. The world's most beautiful railway stations."
    )

    styles = sorted(set(s["style"] for s in ARCHITECTURAL_STATIONS))
    selected_styles = st.multiselect(
        "Filter by Architectural Style", styles, default=styles, key="rw_arch_styles"
    )

    stations = [s for s in ARCHITECTURAL_STATIONS if s["style"] in selected_styles]
    if not stations:
        st.info("Select at least one style to display stations.")
        return

    # Stats
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Stations Shown", len(stations))
    sc2.metric("Styles", len(selected_styles))
    oldest = min(s["year"] for s in stations)
    newest = max(s["year"] for s in stations)
    sc3.metric("Oldest", oldest)
    sc4.metric("Newest", newest)

    # Map - world view
    m = _build_folium_map(30, 10, zoom=2)
    for s in stations:
        folium.Marker(
            location=[s["lat"], s["lon"]],
            popup=_safe_popup(s["name"], f"{s['city']} | {s['style']}", {
                "Year": s["year"],
                "Info": s["desc"][:120],
            }),
            icon=folium.Icon(color="purple", icon="home", prefix="fa"),
            tooltip=escape(f"{s['name']} ({s['year']})"),
        ).add_to(m)
    _render_map(m)

    # Style distribution chart
    style_counts = {}
    for s in stations:
        style_counts[s["style"]] = style_counts.get(s["style"], 0) + 1
    _make_chart(style_counts, "Stations by Architectural Style")

    # Timeline
    fig, ax = plt.subplots(figsize=(8, max(3, len(stations) * 0.32)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    sorted_s = sorted(stations, key=lambda x: x["year"])
    colors = [s["color"] for s in sorted_s]
    ax.barh(range(len(sorted_s)), [s["year"] for s in sorted_s], color=colors, alpha=0.85)
    ax.set_yticks(range(len(sorted_s)))
    ax.set_yticklabels([f"{s['name'][:25]} ({s['city'][:15]})" for s in sorted_s],
                        color="#8b97b0", fontsize=7)
    ax.set_xlabel("Year", color="#8b97b0")
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_title("Station Architecture Timeline", color="#e8ecf4", fontsize=11, pad=8)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    st.markdown("##### Station Architecture Details")
    features = [{
        "name": s["name"], "city": s["city"], "style": s["style"],
        "year": s["year"], "lat": s["lat"], "lon": s["lon"],
        "description": s["desc"],
    } for s in stations]
    df = _features_to_dataframe(features)
    st.dataframe(df, width="stretch")

    _download_section(features, "station_architecture")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def render_railway_maps_tab():
    """Main entry point for the Railway & Train Maps tab."""
    st.markdown(
        '<div class="tab-header amber"><h4>\U0001f682 Railway & Train Maps</h4>'
        '<p>World railways, high-speed trains, historic routes & metro systems</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Select Map Mode",
        MAP_MODES,
        horizontal=False,
        key="rw_map_mode",
    )

    st.markdown("---")

    if mode == MAP_MODES[0]:
        _render_stations_mode()
    elif mode == MAP_MODES[1]:
        _render_highspeed_mode()
    elif mode == MAP_MODES[2]:
        _render_epic_routes_mode()
    elif mode == MAP_MODES[3]:
        _render_historic_mode()
    elif mode == MAP_MODES[4]:
        _render_metro_mode()
    elif mode == MAP_MODES[5]:
        _render_scenic_mode()
    elif mode == MAP_MODES[6]:
        _render_engineering_mode()
    elif mode == MAP_MODES[7]:
        _render_abandoned_mode()
    elif mode == MAP_MODES[8]:
        _render_funiculars_mode()
    elif mode == MAP_MODES[9]:
        _render_architecture_mode()
