# -*- coding: utf-8 -*-
"""
Genetics & DNA Maps module for TerraScout AI.
Curated data for haplogroups, human migration routes, genetic diversity,
blood types, lactose tolerance, eye color, genetic diseases, and ancient DNA sites.
All data is curated/embedded -- no external API required.
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
import numpy as np

# ═══════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_COLOR = "#06b6d4"
MUTED_COLOR = "#5a6580"
SECONDARY_COLOR = "#8b97b0"

# ═══════════════════════════════════════════════════════════════
# 1. Y-DNA HAPLOGROUP DATA
# ═══════════════════════════════════════════════════════════════
YDNA_HAPLOGROUPS = [
    {"haplogroup": "R1b", "desc": "Most common Western European lineage", "color": "#3b82f6",
     "regions": [
         {"name": "Ireland", "lat": 53.0, "lon": -8.0, "freq": 85},
         {"name": "Basque Country", "lat": 43.0, "lon": -2.5, "freq": 88},
         {"name": "Wales", "lat": 52.0, "lon": -3.5, "freq": 83},
         {"name": "France", "lat": 46.5, "lon": 2.5, "freq": 58},
         {"name": "Spain", "lat": 40.0, "lon": -4.0, "freq": 65},
         {"name": "England", "lat": 52.0, "lon": -1.0, "freq": 60},
         {"name": "Germany", "lat": 51.0, "lon": 10.0, "freq": 45},
         {"name": "Italy", "lat": 42.0, "lon": 12.5, "freq": 40},
         {"name": "Portugal", "lat": 39.5, "lon": -8.0, "freq": 56},
         {"name": "Belgium", "lat": 50.8, "lon": 4.4, "freq": 61},
         {"name": "Cameroon (R1b-V88)", "lat": 6.0, "lon": 12.0, "freq": 45},
     ]},
    {"haplogroup": "R1a", "desc": "Eastern European & South Asian lineage", "color": "#ef4444",
     "regions": [
         {"name": "Poland", "lat": 52.0, "lon": 19.0, "freq": 57},
         {"name": "Russia", "lat": 56.0, "lon": 38.0, "freq": 46},
         {"name": "Ukraine", "lat": 49.0, "lon": 32.0, "freq": 44},
         {"name": "Northern India", "lat": 28.5, "lon": 77.0, "freq": 40},
         {"name": "Kyrgyzstan", "lat": 41.0, "lon": 75.0, "freq": 63},
         {"name": "Tajikistan", "lat": 38.5, "lon": 69.0, "freq": 30},
         {"name": "Norway", "lat": 62.0, "lon": 10.0, "freq": 26},
         {"name": "Czech Republic", "lat": 50.0, "lon": 15.0, "freq": 34},
         {"name": "Slovakia", "lat": 48.7, "lon": 19.7, "freq": 42},
     ]},
    {"haplogroup": "I1", "desc": "Nordic/Germanic lineage", "color": "#06b6d4",
     "regions": [
         {"name": "Sweden", "lat": 62.0, "lon": 15.0, "freq": 40},
         {"name": "Norway", "lat": 62.0, "lon": 10.0, "freq": 34},
         {"name": "Denmark", "lat": 56.0, "lon": 10.0, "freq": 35},
         {"name": "Finland", "lat": 62.0, "lon": 26.0, "freq": 28},
         {"name": "Iceland", "lat": 65.0, "lon": -18.0, "freq": 25},
         {"name": "Northern Germany", "lat": 54.0, "lon": 10.0, "freq": 22},
     ]},
    {"haplogroup": "I2", "desc": "Balkan & Western European lineage", "color": "#a855f7",
     "regions": [
         {"name": "Bosnia", "lat": 44.0, "lon": 18.0, "freq": 55},
         {"name": "Croatia", "lat": 45.0, "lon": 16.0, "freq": 38},
         {"name": "Serbia", "lat": 44.0, "lon": 21.0, "freq": 34},
         {"name": "Sardinia", "lat": 40.0, "lon": 9.0, "freq": 40},
         {"name": "Romania", "lat": 46.0, "lon": 25.0, "freq": 20},
         {"name": "Ukraine", "lat": 49.0, "lon": 32.0, "freq": 21},
     ]},
    {"haplogroup": "J2", "desc": "Near Eastern / Mediterranean lineage", "color": "#f59e0b",
     "regions": [
         {"name": "Georgia", "lat": 42.0, "lon": 44.0, "freq": 30},
         {"name": "Turkey", "lat": 39.0, "lon": 35.0, "freq": 24},
         {"name": "Iran", "lat": 32.0, "lon": 53.0, "freq": 23},
         {"name": "Italy (South)", "lat": 40.0, "lon": 16.0, "freq": 20},
         {"name": "Greece", "lat": 39.0, "lon": 22.0, "freq": 23},
         {"name": "Lebanon", "lat": 33.9, "lon": 35.9, "freq": 30},
         {"name": "Iraq", "lat": 33.3, "lon": 44.4, "freq": 25},
     ]},
    {"haplogroup": "J1", "desc": "Arabian / Semitic lineage", "color": "#f97316",
     "regions": [
         {"name": "Yemen", "lat": 15.5, "lon": 48.5, "freq": 72},
         {"name": "Saudi Arabia", "lat": 24.0, "lon": 45.0, "freq": 40},
         {"name": "Ethiopia (Amhara)", "lat": 9.0, "lon": 38.7, "freq": 35},
         {"name": "Palestine", "lat": 31.9, "lon": 35.2, "freq": 38},
         {"name": "Sudan", "lat": 16.0, "lon": 32.0, "freq": 25},
     ]},
    {"haplogroup": "E1b1b", "desc": "Northeast African / Mediterranean lineage", "color": "#10b981",
     "regions": [
         {"name": "Somalia", "lat": 2.0, "lon": 45.0, "freq": 78},
         {"name": "Ethiopia", "lat": 9.0, "lon": 38.7, "freq": 62},
         {"name": "Morocco", "lat": 32.0, "lon": -6.0, "freq": 45},
         {"name": "Tunisia", "lat": 34.0, "lon": 9.0, "freq": 38},
         {"name": "Greece", "lat": 39.0, "lon": 22.0, "freq": 21},
         {"name": "Albania", "lat": 41.0, "lon": 20.0, "freq": 35},
     ]},
    {"haplogroup": "N", "desc": "Uralic / Northeast Asian lineage", "color": "#ec4899",
     "regions": [
         {"name": "Finland", "lat": 62.0, "lon": 26.0, "freq": 58},
         {"name": "Lithuania", "lat": 55.0, "lon": 24.0, "freq": 42},
         {"name": "Estonia", "lat": 59.0, "lon": 25.0, "freq": 34},
         {"name": "Yakutia, Russia", "lat": 62.0, "lon": 130.0, "freq": 75},
         {"name": "Nenets, Russia", "lat": 67.0, "lon": 53.0, "freq": 60},
     ]},
    {"haplogroup": "O", "desc": "East Asian & Southeast Asian lineage", "color": "#14b8a6",
     "regions": [
         {"name": "China (Han)", "lat": 35.0, "lon": 105.0, "freq": 75},
         {"name": "Japan", "lat": 36.0, "lon": 138.0, "freq": 52},
         {"name": "Korea", "lat": 37.0, "lon": 127.0, "freq": 73},
         {"name": "Vietnam", "lat": 16.0, "lon": 108.0, "freq": 60},
         {"name": "Thailand", "lat": 15.0, "lon": 101.0, "freq": 42},
         {"name": "Philippines", "lat": 12.0, "lon": 122.0, "freq": 39},
         {"name": "Indonesia", "lat": -2.0, "lon": 118.0, "freq": 35},
     ]},
    {"haplogroup": "Q", "desc": "Native American & Central Asian lineage", "color": "#8b5cf6",
     "regions": [
         {"name": "Peru (Quechua)", "lat": -13.5, "lon": -72.0, "freq": 90},
         {"name": "Mexico (Maya)", "lat": 20.0, "lon": -89.0, "freq": 75},
         {"name": "Bolivia", "lat": -17.0, "lon": -65.0, "freq": 80},
         {"name": "Colombia", "lat": 4.0, "lon": -72.0, "freq": 55},
         {"name": "Navajo, USA", "lat": 36.0, "lon": -109.5, "freq": 78},
         {"name": "Siberia (Ket)", "lat": 63.0, "lon": 87.0, "freq": 94},
     ]},
    {"haplogroup": "D", "desc": "Tibetan / Japanese / Andaman lineage", "color": "#d946ef",
     "regions": [
         {"name": "Tibet", "lat": 30.0, "lon": 91.0, "freq": 50},
         {"name": "Japan (Ainu)", "lat": 43.0, "lon": 143.0, "freq": 38},
         {"name": "Andaman Islands", "lat": 12.0, "lon": 93.0, "freq": 60},
         {"name": "Philippines (Mamanwa)", "lat": 9.0, "lon": 126.0, "freq": 30},
     ]},
]

# ═══════════════════════════════════════════════════════════════
# 2. mtDNA HAPLOGROUP DATA
# ═══════════════════════════════════════════════════════════════
MTDNA_HAPLOGROUPS = [
    {"haplogroup": "H", "desc": "Most common European mtDNA lineage", "color": "#3b82f6",
     "regions": [
         {"name": "Basque Country", "lat": 43.0, "lon": -2.5, "freq": 50},
         {"name": "Scandinavia", "lat": 62.0, "lon": 15.0, "freq": 45},
         {"name": "Central Europe", "lat": 50.0, "lon": 10.0, "freq": 44},
         {"name": "British Isles", "lat": 54.0, "lon": -2.0, "freq": 45},
         {"name": "Iberia", "lat": 40.0, "lon": -4.0, "freq": 42},
         {"name": "Caucasus", "lat": 42.5, "lon": 44.0, "freq": 28},
     ]},
    {"haplogroup": "U", "desc": "Ancient European hunter-gatherer lineage", "color": "#a855f7",
     "regions": [
         {"name": "Sami (Finland/Norway)", "lat": 69.0, "lon": 25.0, "freq": 48},
         {"name": "India (U2)", "lat": 22.0, "lon": 78.0, "freq": 18},
         {"name": "North Africa (U6)", "lat": 33.0, "lon": 2.0, "freq": 20},
         {"name": "Eastern Europe", "lat": 52.0, "lon": 20.0, "freq": 20},
         {"name": "Berbers (U6)", "lat": 32.0, "lon": -5.0, "freq": 25},
     ]},
    {"haplogroup": "L0", "desc": "Oldest mtDNA lineage - San/Khoisan peoples", "color": "#ef4444",
     "regions": [
         {"name": "San, Southern Africa", "lat": -24.0, "lon": 22.0, "freq": 70},
         {"name": "Khoisan, Namibia", "lat": -22.0, "lon": 17.0, "freq": 60},
         {"name": "East Africa", "lat": -3.0, "lon": 37.0, "freq": 15},
     ]},
    {"haplogroup": "L1", "desc": "Central & West African lineage", "color": "#f97316",
     "regions": [
         {"name": "Central Africa (Pygmies)", "lat": 1.0, "lon": 20.0, "freq": 50},
         {"name": "West Africa", "lat": 10.0, "lon": -5.0, "freq": 25},
         {"name": "East Africa", "lat": -5.0, "lon": 35.0, "freq": 15},
     ]},
    {"haplogroup": "L2", "desc": "West & Central African lineage, carried to Americas", "color": "#f59e0b",
     "regions": [
         {"name": "West Africa (Senegal)", "lat": 14.5, "lon": -14.0, "freq": 35},
         {"name": "Nigeria", "lat": 9.0, "lon": 8.0, "freq": 30},
         {"name": "African Americans (US)", "lat": 33.0, "lon": -84.0, "freq": 20},
         {"name": "Central Africa", "lat": 0.0, "lon": 22.0, "freq": 22},
     ]},
    {"haplogroup": "L3", "desc": "Source of all non-African mtDNA lineages", "color": "#10b981",
     "regions": [
         {"name": "East Africa (Ethiopia)", "lat": 9.0, "lon": 38.7, "freq": 40},
         {"name": "Horn of Africa", "lat": 8.0, "lon": 46.0, "freq": 30},
         {"name": "Arabian Peninsula", "lat": 22.0, "lon": 48.0, "freq": 15},
     ]},
    {"haplogroup": "M", "desc": "Daughter of L3; major Asian lineage", "color": "#06b6d4",
     "regions": [
         {"name": "India", "lat": 22.0, "lon": 78.0, "freq": 60},
         {"name": "Southeast Asia", "lat": 13.0, "lon": 102.0, "freq": 30},
         {"name": "Tibet", "lat": 30.0, "lon": 91.0, "freq": 40},
         {"name": "Australia (Aboriginal)", "lat": -25.0, "lon": 134.0, "freq": 25},
     ]},
    {"haplogroup": "N", "desc": "Daughter of L3; ancestor of R, widespread in Eurasia", "color": "#ec4899",
     "regions": [
         {"name": "Europe (via R)", "lat": 50.0, "lon": 10.0, "freq": 35},
         {"name": "Central Asia", "lat": 42.0, "lon": 65.0, "freq": 20},
         {"name": "Australia (Aboriginal)", "lat": -25.0, "lon": 134.0, "freq": 15},
     ]},
    {"haplogroup": "B", "desc": "East Asian & Polynesian lineage", "color": "#14b8a6",
     "regions": [
         {"name": "Polynesia", "lat": -17.0, "lon": -150.0, "freq": 90},
         {"name": "Southeast Asia", "lat": 10.0, "lon": 110.0, "freq": 25},
         {"name": "China (South)", "lat": 25.0, "lon": 110.0, "freq": 22},
         {"name": "Native Americans (Navajo)", "lat": 36.0, "lon": -109.5, "freq": 28},
         {"name": "Japan", "lat": 36.0, "lon": 138.0, "freq": 12},
     ]},
    {"haplogroup": "A", "desc": "Northern Asian & Native American lineage", "color": "#8b5cf6",
     "regions": [
         {"name": "Chukchi, Siberia", "lat": 66.0, "lon": 170.0, "freq": 40},
         {"name": "Eskimo/Inuit", "lat": 68.0, "lon": -100.0, "freq": 35},
         {"name": "Central America", "lat": 15.0, "lon": -90.0, "freq": 20},
         {"name": "Japan", "lat": 36.0, "lon": 138.0, "freq": 8},
     ]},
]

# ═══════════════════════════════════════════════════════════════
# 3. HUMAN MIGRATION OUT OF AFRICA
# ═══════════════════════════════════════════════════════════════
MIGRATION_ROUTES = [
    {"name": "Out of Africa (Southern Route)", "color": "#ef4444", "weight": 4,
     "date_range": "~70,000 years ago",
     "desc": "Coastal migration along Arabian Peninsula to South Asia and Australia",
     "path": [
         [12.0, 43.0], [14.0, 48.0], [20.0, 56.0], [24.0, 60.0],
         [22.0, 68.0], [18.0, 78.0], [12.0, 80.0], [8.0, 85.0],
         [2.0, 98.0], [-5.0, 110.0], [-15.0, 128.0], [-25.0, 134.0],
     ]},
    {"name": "Out of Africa (Northern Route)", "color": "#f59e0b", "weight": 4,
     "date_range": "~60,000-50,000 years ago",
     "desc": "Through Sinai into Levant, then into Central Asia and Europe",
     "path": [
         [12.0, 43.0], [27.0, 34.0], [32.0, 35.0], [35.0, 38.0],
         [37.0, 42.0], [40.0, 50.0], [42.0, 60.0], [45.0, 68.0],
     ]},
    {"name": "Into Europe", "color": "#3b82f6", "weight": 3,
     "date_range": "~45,000-40,000 years ago",
     "desc": "Modern humans enter Europe, replacing Neanderthals",
     "path": [
         [37.0, 42.0], [40.0, 35.0], [42.0, 28.0], [44.0, 22.0],
         [46.0, 15.0], [48.0, 8.0], [50.0, 3.0], [52.0, -2.0],
     ]},
    {"name": "Into East Asia", "color": "#10b981", "weight": 3,
     "date_range": "~50,000-40,000 years ago",
     "desc": "Migration into China, Southeast Asia, and eventually Japan",
     "path": [
         [42.0, 60.0], [40.0, 70.0], [38.0, 80.0],
         [35.0, 95.0], [32.0, 105.0], [35.0, 115.0], [37.0, 127.0],
     ]},
    {"name": "Into Siberia", "color": "#a855f7", "weight": 3,
     "date_range": "~40,000-30,000 years ago",
     "desc": "Northward expansion into Siberian steppe",
     "path": [
         [45.0, 68.0], [50.0, 75.0], [55.0, 82.0],
         [60.0, 90.0], [63.0, 100.0], [65.0, 120.0],
     ]},
    {"name": "Into Americas (Beringia)", "color": "#8b5cf6", "weight": 4,
     "date_range": "~20,000-15,000 years ago",
     "desc": "Crossing Beringia land bridge during last glacial maximum",
     "path": [
         [65.0, 120.0], [66.0, 150.0], [65.0, 170.0],
         [66.0, -170.0], [65.0, -160.0], [62.0, -150.0],
         [58.0, -140.0], [52.0, -125.0],
     ]},
    {"name": "Americas (Southward)", "color": "#ec4899", "weight": 3,
     "date_range": "~15,000-12,000 years ago",
     "desc": "Rapid colonization down the Pacific coast and inland",
     "path": [
         [52.0, -125.0], [45.0, -120.0], [37.0, -118.0],
         [25.0, -105.0], [15.0, -90.0], [5.0, -76.0],
         [-5.0, -70.0], [-15.0, -65.0], [-30.0, -60.0],
         [-42.0, -68.0], [-50.0, -72.0],
     ]},
    {"name": "Into Polynesia (Austronesian)", "color": "#14b8a6", "weight": 3,
     "date_range": "~5,000-1,000 years ago",
     "desc": "Maritime expansion from Taiwan through Pacific islands",
     "path": [
         [25.0, 120.0], [18.0, 118.0], [12.0, 122.0],
         [5.0, 125.0], [-2.0, 130.0], [-6.0, 145.0],
         [-10.0, 160.0], [-15.0, 168.0], [-18.0, 178.0],
         [-17.0, -150.0], [-22.0, -135.0],
     ]},
    {"name": "Into Madagascar", "color": "#f97316", "weight": 2,
     "date_range": "~2,000-1,500 years ago",
     "desc": "Austronesian mariners reach Madagascar from Borneo",
     "path": [
         [0.0, 115.0], [-5.0, 100.0], [-10.0, 85.0],
         [-15.0, 65.0], [-18.0, 50.0], [-19.0, 47.0],
     ]},
]

MIGRATION_LANDMARKS = [
    {"name": "Omo Kibish, Ethiopia", "lat": 5.4, "lon": 35.9,
     "desc": "Oldest Homo sapiens fossils (~233,000 BP)", "color": "#ef4444"},
    {"name": "Jebel Irhoud, Morocco", "lat": 31.85, "lon": -8.87,
     "desc": "Early H. sapiens remains (~300,000 BP)", "color": "#ef4444"},
    {"name": "Skhul Cave, Israel", "lat": 32.67, "lon": 35.0,
     "desc": "Early Out of Africa attempt (~120,000 BP)", "color": "#f59e0b"},
    {"name": "Niah Cave, Borneo", "lat": 3.82, "lon": 114.2,
     "desc": "Early modern human in SE Asia (~40,000 BP)", "color": "#10b981"},
    {"name": "Lake Mungo, Australia", "lat": -33.7, "lon": 143.1,
     "desc": "Oldest human remains in Australia (~42,000 BP)", "color": "#06b6d4"},
    {"name": "Cro-Magnon, France", "lat": 44.94, "lon": 1.0,
     "desc": "Iconic early European modern humans (~32,000 BP)", "color": "#3b82f6"},
    {"name": "Monte Verde, Chile", "lat": -41.5, "lon": -73.2,
     "desc": "One of the oldest sites in Americas (~14,500 BP)", "color": "#8b5cf6"},
    {"name": "Clovis, New Mexico", "lat": 34.4, "lon": -103.2,
     "desc": "Clovis culture type site (~13,000 BP)", "color": "#8b5cf6"},
]

# ═══════════════════════════════════════════════════════════════
# 4. NEANDERTHAL DNA DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
NEANDERTHAL_DATA = [
    {"population": "East Asians", "region": "East Asia", "lat": 35.0, "lon": 105.0, "pct": 2.6,
     "note": "Slightly higher Neanderthal ancestry than Europeans"},
    {"population": "Europeans", "region": "Europe", "lat": 50.0, "lon": 10.0, "pct": 2.0,
     "note": "Average ~2% Neanderthal DNA"},
    {"population": "South Asians", "region": "South Asia", "lat": 22.0, "lon": 78.0, "pct": 2.2,
     "note": "Comparable to European levels"},
    {"population": "Native Americans", "region": "Americas", "lat": 20.0, "lon": -100.0, "pct": 1.7,
     "note": "Variable; some populations up to 2%"},
    {"population": "Middle Eastern", "region": "Middle East", "lat": 32.0, "lon": 45.0, "pct": 2.2,
     "note": "Near Neanderthal range; expected higher admixture"},
    {"population": "Central Asian", "region": "Central Asia", "lat": 42.0, "lon": 65.0, "pct": 2.4,
     "note": "High Neanderthal ancestry"},
    {"population": "Southeast Asian", "region": "SE Asia", "lat": 10.0, "lon": 105.0, "pct": 2.3,
     "note": "Similar to East Asian levels"},
    {"population": "North African", "region": "North Africa", "lat": 32.0, "lon": 5.0, "pct": 1.2,
     "note": "Lower due to back-migration from Europe mixing with local"},
    {"population": "Sub-Saharan African", "region": "Sub-Saharan Africa", "lat": 0.0, "lon": 20.0, "pct": 0.3,
     "note": "Very low; mostly via back-migration from Eurasia"},
    {"population": "Oceanian (Papuan)", "region": "Oceania", "lat": -6.0, "lon": 147.0, "pct": 2.0,
     "note": "Also carries ~3-5% Denisovan DNA"},
    {"population": "Australian Aboriginal", "region": "Australia", "lat": -25.0, "lon": 134.0, "pct": 2.0,
     "note": "Also carries Denisovan DNA"},
    {"population": "Melanesian", "region": "Melanesia", "lat": -8.0, "lon": 159.0, "pct": 2.1,
     "note": "Highest combined archaic DNA (Neanderthal + Denisovan)"},
]

# ═══════════════════════════════════════════════════════════════
# 5. GENETIC DIVERSITY (HETEROZYGOSITY)
# ═══════════════════════════════════════════════════════════════
GENETIC_DIVERSITY = [
    {"population": "San (Khoisan)", "region": "Southern Africa", "lat": -24.0, "lon": 22.0, "het": 0.77,
     "note": "Highest genetic diversity on Earth"},
    {"population": "Mbuti Pygmy", "region": "Central Africa", "lat": 1.5, "lon": 29.0, "het": 0.76,
     "note": "Ancient isolated lineage with very high diversity"},
    {"population": "Yoruba", "region": "West Africa", "lat": 7.5, "lon": 4.0, "het": 0.74,
     "note": "Major West African population"},
    {"population": "Mandenka", "region": "West Africa", "lat": 12.5, "lon": -12.0, "het": 0.73,
     "note": "Senegambian population"},
    {"population": "Bantu", "region": "East Africa", "lat": -3.0, "lon": 37.0, "het": 0.72,
     "note": "Bantu expansion from West Africa"},
    {"population": "Ethiopian", "region": "East Africa", "lat": 9.0, "lon": 38.7, "het": 0.71,
     "note": "Gateway for Out of Africa migration"},
    {"population": "Middle Eastern", "region": "Middle East", "lat": 32.0, "lon": 45.0, "het": 0.68,
     "note": "First stop after Out of Africa"},
    {"population": "South Asian", "region": "South Asia", "lat": 22.0, "lon": 78.0, "het": 0.67,
     "note": "Along southern migration route"},
    {"population": "European", "region": "Europe", "lat": 50.0, "lon": 10.0, "het": 0.64,
     "note": "Serial founder effect reduces diversity"},
    {"population": "Central Asian", "region": "Central Asia", "lat": 42.0, "lon": 65.0, "het": 0.65,
     "note": "Crossroads of Eurasian populations"},
    {"population": "East Asian", "region": "East Asia", "lat": 35.0, "lon": 105.0, "het": 0.63,
     "note": "Reduced diversity from founder effects"},
    {"population": "Southeast Asian", "region": "SE Asia", "lat": 10.0, "lon": 105.0, "het": 0.64,
     "note": "Mix of southern route and East Asian ancestry"},
    {"population": "Papuan", "region": "Oceania", "lat": -6.0, "lon": 147.0, "het": 0.62,
     "note": "Long isolation but early colonization"},
    {"population": "Australian Aboriginal", "region": "Australia", "lat": -25.0, "lon": 134.0, "het": 0.60,
     "note": "One of oldest populations outside Africa"},
    {"population": "Siberian", "region": "Siberia", "lat": 62.0, "lon": 100.0, "het": 0.59,
     "note": "Small population size reduced diversity"},
    {"population": "Native American", "region": "Americas", "lat": 15.0, "lon": -90.0, "het": 0.56,
     "note": "Multiple bottlenecks entering Americas"},
    {"population": "Polynesian", "region": "Polynesia", "lat": -17.0, "lon": -150.0, "het": 0.53,
     "note": "Recent colonization, strong founder effect"},
]

# ═══════════════════════════════════════════════════════════════
# 6. BLOOD TYPE DISTRIBUTION BY COUNTRY
# ═══════════════════════════════════════════════════════════════
BLOOD_TYPE_DATA = [
    {"country": "Peru", "lat": -12.0, "lon": -77.0, "O": 71, "A": 19, "B": 9, "AB": 1},
    {"country": "United Kingdom", "lat": 52.0, "lon": -1.0, "O": 47, "A": 42, "B": 8, "AB": 3},
    {"country": "United States", "lat": 39.0, "lon": -98.0, "O": 44, "A": 42, "B": 10, "AB": 4},
    {"country": "France", "lat": 46.5, "lon": 2.5, "O": 43, "A": 45, "B": 9, "AB": 3},
    {"country": "Germany", "lat": 51.0, "lon": 10.0, "O": 41, "A": 43, "B": 11, "AB": 5},
    {"country": "Japan", "lat": 36.0, "lon": 138.0, "O": 30, "A": 38, "B": 22, "AB": 10},
    {"country": "China", "lat": 35.0, "lon": 105.0, "O": 34, "A": 28, "B": 29, "AB": 9},
    {"country": "India", "lat": 22.0, "lon": 78.0, "O": 37, "A": 22, "B": 33, "AB": 8},
    {"country": "Russia", "lat": 56.0, "lon": 38.0, "O": 33, "A": 36, "B": 23, "AB": 8},
    {"country": "Brazil", "lat": -14.0, "lon": -51.0, "O": 45, "A": 34, "B": 17, "AB": 4},
    {"country": "Nigeria", "lat": 9.0, "lon": 8.0, "O": 52, "A": 21, "B": 23, "AB": 4},
    {"country": "South Africa", "lat": -30.0, "lon": 25.0, "O": 45, "A": 30, "B": 20, "AB": 5},
    {"country": "Australia", "lat": -25.0, "lon": 134.0, "O": 49, "A": 38, "B": 10, "AB": 3},
    {"country": "Mexico", "lat": 23.0, "lon": -102.0, "O": 62, "A": 27, "B": 8, "AB": 3},
    {"country": "Turkey", "lat": 39.0, "lon": 35.0, "O": 33, "A": 43, "B": 18, "AB": 6},
    {"country": "Iran", "lat": 32.0, "lon": 53.0, "O": 37, "A": 33, "B": 22, "AB": 8},
    {"country": "Egypt", "lat": 26.0, "lon": 30.0, "O": 33, "A": 36, "B": 24, "AB": 7},
    {"country": "Kenya", "lat": 0.0, "lon": 37.0, "O": 60, "A": 19, "B": 18, "AB": 3},
    {"country": "Thailand", "lat": 15.0, "lon": 101.0, "O": 39, "A": 22, "B": 33, "AB": 6},
    {"country": "South Korea", "lat": 37.0, "lon": 127.0, "O": 27, "A": 34, "B": 27, "AB": 12},
    {"country": "Argentina", "lat": -34.0, "lon": -64.0, "O": 45, "A": 36, "B": 14, "AB": 5},
    {"country": "Colombia", "lat": 4.0, "lon": -72.0, "O": 61, "A": 26, "B": 10, "AB": 3},
    {"country": "Sweden", "lat": 62.0, "lon": 15.0, "O": 38, "A": 47, "B": 10, "AB": 5},
    {"country": "Poland", "lat": 52.0, "lon": 19.0, "O": 33, "A": 39, "B": 20, "AB": 8},
    {"country": "Pakistan", "lat": 30.0, "lon": 70.0, "O": 31, "A": 25, "B": 34, "AB": 10},
    {"country": "Bangladesh", "lat": 24.0, "lon": 90.0, "O": 27, "A": 23, "B": 39, "AB": 11},
    {"country": "Indonesia", "lat": -2.0, "lon": 118.0, "O": 41, "A": 26, "B": 29, "AB": 4},
    {"country": "Ethiopia", "lat": 9.0, "lon": 38.7, "O": 45, "A": 27, "B": 22, "AB": 6},
    {"country": "Mongolia", "lat": 47.0, "lon": 105.0, "O": 30, "A": 23, "B": 38, "AB": 9},
    {"country": "Iceland", "lat": 65.0, "lon": -18.0, "O": 56, "A": 32, "B": 10, "AB": 2},
]

# ═══════════════════════════════════════════════════════════════
# 7. LACTOSE TOLERANCE DATA
# ═══════════════════════════════════════════════════════════════
LACTOSE_TOLERANCE = [
    {"region": "Sweden", "lat": 62.0, "lon": 15.0, "tolerance_pct": 96, "note": "Highest lactase persistence rate"},
    {"region": "Denmark", "lat": 56.0, "lon": 10.0, "tolerance_pct": 96, "note": "Northern European high rate"},
    {"region": "Ireland", "lat": 53.0, "lon": -8.0, "tolerance_pct": 96, "note": "Celtic population very high"},
    {"region": "Netherlands", "lat": 52.0, "lon": 5.0, "tolerance_pct": 95, "note": "Long dairy-farming history"},
    {"region": "United Kingdom", "lat": 54.0, "lon": -2.0, "tolerance_pct": 93, "note": "High northern European rate"},
    {"region": "Germany", "lat": 51.0, "lon": 10.0, "tolerance_pct": 85, "note": "High central European rate"},
    {"region": "France", "lat": 46.5, "lon": 2.5, "tolerance_pct": 78, "note": "Gradient from north to south"},
    {"region": "United States", "lat": 39.0, "lon": -98.0, "tolerance_pct": 74, "note": "Mixed population; varies by ancestry"},
    {"region": "Spain", "lat": 40.0, "lon": -4.0, "tolerance_pct": 66, "note": "Mediterranean lower rate"},
    {"region": "Italy", "lat": 42.0, "lon": 12.5, "tolerance_pct": 49, "note": "South Italy ~30%, North ~60%"},
    {"region": "Greece", "lat": 39.0, "lon": 22.0, "tolerance_pct": 45, "note": "Mediterranean pattern"},
    {"region": "Turkey", "lat": 39.0, "lon": 35.0, "tolerance_pct": 28, "note": "Transitional zone"},
    {"region": "Fulani (W. Africa)", "lat": 12.0, "lon": -2.0, "tolerance_pct": 60, "note": "Pastoral Fulani - independent LP evolution"},
    {"region": "Tutsi (Rwanda)", "lat": -2.0, "lon": 30.0, "tolerance_pct": 50, "note": "East African pastoralist convergent evolution"},
    {"region": "Maasai (Kenya)", "lat": -2.5, "lon": 37.0, "tolerance_pct": 62, "note": "Cattle-herding; independent LP mutation"},
    {"region": "Arabia", "lat": 24.0, "lon": 45.0, "tolerance_pct": 20, "note": "Bedouin populations higher (~25%)"},
    {"region": "India (North)", "lat": 28.5, "lon": 77.0, "tolerance_pct": 35, "note": "Indo-European pastoralist heritage"},
    {"region": "India (South)", "lat": 13.0, "lon": 78.0, "tolerance_pct": 15, "note": "Less dairy-dependent historically"},
    {"region": "Russia", "lat": 56.0, "lon": 38.0, "tolerance_pct": 60, "note": "Northern populations higher"},
    {"region": "China", "lat": 35.0, "lon": 105.0, "tolerance_pct": 8, "note": "Very low; no traditional dairy culture"},
    {"region": "Japan", "lat": 36.0, "lon": 138.0, "tolerance_pct": 6, "note": "Historically no dairy farming"},
    {"region": "Korea", "lat": 37.0, "lon": 127.0, "tolerance_pct": 4, "note": "Very low persistence"},
    {"region": "Thailand", "lat": 15.0, "lon": 101.0, "tolerance_pct": 5, "note": "Southeast Asian low rate"},
    {"region": "West Africa (Non-Fulani)", "lat": 7.0, "lon": 0.0, "tolerance_pct": 10, "note": "Non-pastoralist populations"},
    {"region": "Peru", "lat": -12.0, "lon": -77.0, "tolerance_pct": 5, "note": "Native American very low rate"},
    {"region": "Australia (Aboriginal)", "lat": -25.0, "lon": 134.0, "tolerance_pct": 3, "note": "No dairy tradition"},
    {"region": "Mongolia", "lat": 47.0, "lon": 105.0, "tolerance_pct": 12, "note": "Fermented dairy instead (kumis, airag)"},
]

# ═══════════════════════════════════════════════════════════════
# 8. EYE COLOR DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
EYE_COLOR_DATA = [
    {"region": "Estonia", "lat": 59.0, "lon": 25.0, "blue": 70, "green": 15, "hazel": 8, "brown": 7},
    {"region": "Finland", "lat": 62.0, "lon": 26.0, "blue": 72, "green": 12, "hazel": 8, "brown": 8},
    {"region": "Sweden", "lat": 62.0, "lon": 15.0, "blue": 70, "green": 14, "hazel": 8, "brown": 8},
    {"region": "Iceland", "lat": 65.0, "lon": -18.0, "blue": 75, "green": 12, "hazel": 6, "brown": 7},
    {"region": "Ireland", "lat": 53.0, "lon": -8.0, "blue": 57, "green": 22, "hazel": 12, "brown": 9},
    {"region": "United Kingdom", "lat": 54.0, "lon": -2.0, "blue": 48, "green": 18, "hazel": 16, "brown": 18},
    {"region": "Netherlands", "lat": 52.0, "lon": 5.0, "blue": 61, "green": 16, "hazel": 10, "brown": 13},
    {"region": "Germany", "lat": 51.0, "lon": 10.0, "blue": 43, "green": 17, "hazel": 15, "brown": 25},
    {"region": "Poland", "lat": 52.0, "lon": 19.0, "blue": 45, "green": 12, "hazel": 13, "brown": 30},
    {"region": "France", "lat": 46.5, "lon": 2.5, "blue": 22, "green": 15, "hazel": 20, "brown": 43},
    {"region": "Spain", "lat": 40.0, "lon": -4.0, "blue": 17, "green": 10, "hazel": 16, "brown": 57},
    {"region": "Italy", "lat": 42.0, "lon": 12.5, "blue": 15, "green": 10, "hazel": 15, "brown": 60},
    {"region": "Greece", "lat": 39.0, "lon": 22.0, "blue": 8, "green": 7, "hazel": 15, "brown": 70},
    {"region": "Turkey", "lat": 39.0, "lon": 35.0, "blue": 6, "green": 5, "hazel": 12, "brown": 77},
    {"region": "Iran", "lat": 32.0, "lon": 53.0, "blue": 3, "green": 5, "hazel": 10, "brown": 82},
    {"region": "India", "lat": 22.0, "lon": 78.0, "blue": 1, "green": 1, "hazel": 3, "brown": 95},
    {"region": "China", "lat": 35.0, "lon": 105.0, "blue": 0, "green": 0, "hazel": 1, "brown": 99},
    {"region": "Japan", "lat": 36.0, "lon": 138.0, "blue": 0, "green": 0, "hazel": 1, "brown": 99},
    {"region": "Korea", "lat": 37.0, "lon": 127.0, "blue": 0, "green": 0, "hazel": 1, "brown": 99},
    {"region": "Nigeria", "lat": 9.0, "lon": 8.0, "blue": 0, "green": 0, "hazel": 1, "brown": 99},
    {"region": "Ethiopia", "lat": 9.0, "lon": 38.7, "blue": 0, "green": 1, "hazel": 3, "brown": 96},
    {"region": "Russia", "lat": 56.0, "lon": 38.0, "blue": 33, "green": 12, "hazel": 15, "brown": 40},
    {"region": "Afghanistan", "lat": 34.0, "lon": 69.0, "blue": 6, "green": 8, "hazel": 10, "brown": 76},
]

# ═══════════════════════════════════════════════════════════════
# 9. GENETIC DISEASE HOTSPOTS
# ═══════════════════════════════════════════════════════════════
GENETIC_DISEASES = [
    {"disease": "Sickle Cell Disease", "color": "#ef4444", "icon": "heartbeat",
     "desc": "Hemoglobin S mutation; heterozygous carriers have malaria resistance",
     "hotspots": [
         {"name": "Sub-Saharan Africa", "lat": 5.0, "lon": 15.0, "prevalence": "10-25% carrier rate",
          "detail": "Highest prevalence; correlates with malaria belt"},
         {"name": "West Africa (Nigeria)", "lat": 9.0, "lon": 8.0, "prevalence": "25-30% carrier rate",
          "detail": "Up to 3% of births affected"},
         {"name": "India (Tribal)", "lat": 20.0, "lon": 80.0, "prevalence": "5-35% carrier rate",
          "detail": "High in tribal populations of central India"},
         {"name": "Saudi Arabia (Eastern)", "lat": 25.0, "lon": 50.0, "prevalence": "5-25% carrier rate",
          "detail": "Arabian/Indian haplotype"},
         {"name": "Mediterranean (Greece)", "lat": 39.0, "lon": 22.0, "prevalence": "1-5% carrier rate",
          "detail": "Historical malaria regions"},
     ]},
    {"disease": "Thalassemia (Beta)", "color": "#f59e0b", "icon": "tint",
     "desc": "Reduced hemoglobin production; carriers have malaria resistance",
     "hotspots": [
         {"name": "Mediterranean (Cyprus)", "lat": 35.0, "lon": 33.0, "prevalence": "14% carrier rate",
          "detail": "Highest beta-thal frequency in world"},
         {"name": "Sardinia, Italy", "lat": 40.0, "lon": 9.0, "prevalence": "12% carrier rate",
          "detail": "Island population with high founder effect"},
         {"name": "Southeast Asia (Thailand)", "lat": 15.0, "lon": 101.0, "prevalence": "3-9% carrier rate",
          "detail": "High alpha and beta thalassemia"},
         {"name": "Middle East (Iran)", "lat": 32.0, "lon": 53.0, "prevalence": "4-8% carrier rate",
          "detail": "Northern provinces highest"},
         {"name": "South China", "lat": 23.0, "lon": 110.0, "prevalence": "2-8% carrier rate",
          "detail": "Guangxi and Guangdong provinces"},
     ]},
    {"disease": "Cystic Fibrosis", "color": "#3b82f6", "icon": "lungs",
     "desc": "CFTR gene mutation affecting lungs and digestion; most common in Northern Europeans",
     "hotspots": [
         {"name": "Ireland", "lat": 53.0, "lon": -8.0, "prevalence": "1 in 19 carriers",
          "detail": "Highest CF rate worldwide"},
         {"name": "Northern Europe", "lat": 55.0, "lon": 10.0, "prevalence": "1 in 25 carriers",
          "detail": "Celtic/Germanic populations most affected"},
         {"name": "United States (Caucasian)", "lat": 39.0, "lon": -98.0, "prevalence": "1 in 29 carriers",
          "detail": "European-descent population"},
         {"name": "Australia", "lat": -25.0, "lon": 134.0, "prevalence": "1 in 25 carriers",
          "detail": "European-descent population"},
     ]},
    {"disease": "Tay-Sachs Disease", "color": "#a855f7", "icon": "brain",
     "desc": "HEXA gene mutation causing neurodegeneration; high in Ashkenazi Jewish populations",
     "hotspots": [
         {"name": "Ashkenazi Jewish (Global)", "lat": 32.0, "lon": 35.0, "prevalence": "1 in 30 carriers",
          "detail": "Founder effect in medieval European Jewish populations"},
         {"name": "French Canadian (Quebec)", "lat": 47.0, "lon": -71.0, "prevalence": "1 in 30 carriers",
          "detail": "Founder effect; Saguenay-Lac-Saint-Jean region"},
         {"name": "Cajun (Louisiana)", "lat": 30.0, "lon": -92.0, "prevalence": "1 in 30 carriers",
          "detail": "French-Canadian founder population"},
         {"name": "Irish American", "lat": 42.0, "lon": -72.0, "prevalence": "Elevated rate",
          "detail": "Higher than general European population"},
     ]},
    {"disease": "G6PD Deficiency", "color": "#10b981", "icon": "flask",
     "desc": "X-linked enzyme deficiency; carriers have malaria resistance; affects 400M+ people",
     "hotspots": [
         {"name": "Sub-Saharan Africa", "lat": 5.0, "lon": 20.0, "prevalence": "10-25% males",
          "detail": "Strong malaria selection"},
         {"name": "Middle East", "lat": 30.0, "lon": 45.0, "prevalence": "5-15% males",
          "detail": "Kurdish populations up to 25%"},
         {"name": "Southeast Asia", "lat": 10.0, "lon": 105.0, "prevalence": "5-15% males",
          "detail": "Multiple G6PD variants"},
         {"name": "Mediterranean (Sardinia)", "lat": 40.0, "lon": 9.0, "prevalence": "4-15% males",
          "detail": "Mediterranean variant"},
         {"name": "India", "lat": 22.0, "lon": 78.0, "prevalence": "5-15% males",
          "detail": "Tribal populations higher"},
     ]},
    {"disease": "Hemochromatosis (HFE)", "color": "#f97316", "icon": "magnet",
     "desc": "Iron overload disorder; C282Y mutation most common in Celtic populations",
     "hotspots": [
         {"name": "Ireland", "lat": 53.0, "lon": -8.0, "prevalence": "1 in 5 carriers",
          "detail": "Highest HFE C282Y frequency worldwide"},
         {"name": "United Kingdom", "lat": 54.0, "lon": -2.0, "prevalence": "1 in 8 carriers",
          "detail": "Celtic/Anglo-Saxon populations"},
         {"name": "Scandinavia", "lat": 62.0, "lon": 15.0, "prevalence": "1 in 10 carriers",
          "detail": "Viking-era spread"},
         {"name": "France (Brittany)", "lat": 48.0, "lon": -3.0, "prevalence": "1 in 7 carriers",
          "detail": "Celtic Breton population"},
     ]},
    {"disease": "Phenylketonuria (PKU)", "color": "#ec4899", "icon": "dna",
     "desc": "PAH gene mutation causing phenylalanine buildup; screened at birth in many countries",
     "hotspots": [
         {"name": "Ireland", "lat": 53.0, "lon": -8.0, "prevalence": "1 in 4,500 births",
          "detail": "Highest in Europe"},
         {"name": "Turkey", "lat": 39.0, "lon": 35.0, "prevalence": "1 in 2,600 births",
          "detail": "High consanguinity rate contributes"},
         {"name": "China (Northern)", "lat": 40.0, "lon": 116.0, "prevalence": "1 in 6,000 births",
          "detail": "Northern provinces higher"},
         {"name": "Italy", "lat": 42.0, "lon": 12.5, "prevalence": "1 in 8,000 births",
          "detail": "Variable across regions"},
     ]},
]

# ═══════════════════════════════════════════════════════════════
# 10. ANCIENT DNA SITES
# ═══════════════════════════════════════════════════════════════
ANCIENT_DNA_SITES = [
    {"name": "Denisova Cave", "lat": 51.4, "lon": 84.68, "country": "Russia (Altai)",
     "age": "~50,000-300,000 BP", "color": "#a855f7",
     "findings": "Denisovan hominin discovery; Denisova 11 (Neanderthal-Denisovan hybrid)"},
    {"name": "Vindija Cave", "lat": 46.3, "lon": 16.07, "country": "Croatia",
     "age": "~40,000-50,000 BP", "color": "#ef4444",
     "findings": "High-quality Neanderthal genome; key for admixture studies"},
    {"name": "Atapuerca (Sima de los Huesos)", "lat": 42.35, "lon": -3.51, "country": "Spain",
     "age": "~430,000 BP", "color": "#f59e0b",
     "findings": "Oldest nuclear DNA; early Neanderthal/Denisovan split lineage"},
    {"name": "Pestera cu Oase", "lat": 44.89, "lon": 21.74, "country": "Romania",
     "age": "~40,000 BP", "color": "#3b82f6",
     "findings": "Early European modern human; 6-9% Neanderthal DNA (recent admixture)"},
    {"name": "Ust-Ishim", "lat": 57.7, "lon": 71.2, "country": "Russia (Siberia)",
     "age": "~45,000 BP", "color": "#06b6d4",
     "findings": "Oldest modern human genome; dates Neanderthal admixture to ~50-60kya"},
    {"name": "Kostenki", "lat": 51.38, "lon": 39.05, "country": "Russia",
     "age": "~37,000 BP", "color": "#10b981",
     "findings": "Early European; shows population already differentiated from Asian lineages"},
    {"name": "Goyet Caves", "lat": 50.44, "lon": 4.88, "country": "Belgium",
     "age": "~35,000 BP", "color": "#ec4899",
     "findings": "Aurignacian population; later replaced by Gravettian groups"},
    {"name": "Sungir", "lat": 56.17, "lon": 40.51, "country": "Russia",
     "age": "~34,000 BP", "color": "#f97316",
     "findings": "Rich burial with aDNA; low inbreeding suggests complex social networks"},
    {"name": "Dolni Vestonice", "lat": 48.88, "lon": 16.66, "country": "Czech Republic",
     "age": "~31,000 BP", "color": "#14b8a6",
     "findings": "Gravettian culture; triple burial with aDNA; early European genetics"},
    {"name": "El Sidrón Cave", "lat": 43.38, "lon": -5.33, "country": "Spain",
     "age": "~49,000 BP", "color": "#d946ef",
     "findings": "12 Neanderthal individuals; evidence of cannibalism; FOXP2 gene present"},
    {"name": "Tianyuan Cave", "lat": 39.7, "lon": 115.9, "country": "China",
     "age": "~40,000 BP", "color": "#22c55e",
     "findings": "Early modern human in East Asia; related to present-day Asian/Native American ancestry"},
    {"name": "Mal'ta (Lake Baikal)", "lat": 52.8, "lon": 103.6, "country": "Russia",
     "age": "~24,000 BP", "color": "#fbbf24",
     "findings": "Ancient North Eurasian (ANE); ancestor of Native Americans and Europeans"},
    {"name": "Kennewick Man", "lat": 46.22, "lon": -119.17, "country": "USA (Washington)",
     "age": "~9,000 BP", "color": "#8b5cf6",
     "findings": "Ancient Native American; genome closest to modern Native Americans"},
    {"name": "Anzick-1", "lat": 46.0, "lon": -111.0, "country": "USA (Montana)",
     "age": "~12,600 BP", "color": "#fb923c",
     "findings": "Clovis-associated burial; direct ancestor of Central/South American peoples"},
    {"name": "Spirit Cave Mummy", "lat": 39.8, "lon": -118.8, "country": "USA (Nevada)",
     "age": "~10,600 BP", "color": "#64748b",
     "findings": "One of oldest North American remains with aDNA; Native American ancestry confirmed"},
    {"name": "Shum Laka", "lat": 5.85, "lon": 10.07, "country": "Cameroon",
     "age": "~8,000 BP", "color": "#34d399",
     "findings": "Ancient Central African; reveals deep divergence in African populations"},
    {"name": "Mota Cave", "lat": 6.2, "lon": 37.7, "country": "Ethiopia",
     "age": "~4,500 BP", "color": "#c084fc",
     "findings": "Pre-Eurasian back-migration; shows ancient East African genetics before admixture"},
    {"name": "Motala", "lat": 58.53, "lon": 15.04, "country": "Sweden",
     "age": "~7,000 BP", "color": "#38bdf8",
     "findings": "Mesolithic Scandinavian hunter-gatherers; blue eyes + dark skin combination"},
    {"name": "Loschbour", "lat": 49.72, "lon": 6.23, "country": "Luxembourg",
     "age": "~8,000 BP", "color": "#4ade80",
     "findings": "Western European hunter-gatherer; dark skin, blue eyes, lactose intolerant"},
    {"name": "Stuttgart (LBK)", "lat": 48.78, "lon": 9.18, "country": "Germany",
     "age": "~7,000 BP", "color": "#facc15",
     "findings": "Early Neolithic farmer; Near Eastern ancestry; light skin, brown eyes"},
    {"name": "Yamnaya (Samara)", "lat": 53.2, "lon": 50.1, "country": "Russia",
     "age": "~5,000 BP", "color": "#fb7185",
     "findings": "Bronze Age steppe pastoralists; massive migration into Europe reshaped genetics"},
    {"name": "Botai", "lat": 51.8, "lon": 70.9, "country": "Kazakhstan",
     "age": "~5,500 BP", "color": "#2dd4bf",
     "findings": "Earliest horse domestication site; Ancient North Eurasian + East Asian ancestry"},
    {"name": "Taforalt (Grotte des Pigeons)", "lat": 34.82, "lon": -2.4, "country": "Morocco",
     "age": "~15,000 BP", "color": "#e879f9",
     "findings": "Oldest aDNA from Africa; Iberomaurusian culture; Sub-Saharan + Eurasian mix"},
    {"name": "Sunghir (Child Burial)", "lat": 56.17, "lon": 40.51, "country": "Russia",
     "age": "~34,000 BP", "color": "#f97316",
     "findings": "Elaborate child burials; surprisingly low inbreeding; long-distance mate networks"},
    {"name": "Hohlenstein-Stadel", "lat": 48.55, "lon": 10.17, "country": "Germany",
     "age": "~124,000 BP", "color": "#7c3aed",
     "findings": "Neanderthal femur; deeply diverged Neanderthal mtDNA lineage"},
    {"name": "Xiahe (Baishiya Cave)", "lat": 35.45, "lon": 102.04, "country": "China (Tibet)",
     "age": "~160,000 BP", "color": "#0ea5e9",
     "findings": "Denisovan mandible at 3,280m elevation; protein analysis confirmed Denisovan"},
    {"name": "Chagyrskaya Cave", "lat": 51.44, "lon": 83.15, "country": "Russia (Altai)",
     "age": "~50,000-60,000 BP", "color": "#f43f5e",
     "findings": "Multiple Neanderthals; small inbred community; Mousterian tools"},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _make_map(center=None, zoom=2):
    """Create a dark-themed Folium map."""
    if center is None:
        center = [20, 10]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _popup_html(title, lines):
    """Build a dark-themed popup HTML string with escaped text."""
    safe_title = escape(str(title))
    body = "".join(
        f"<div style='color:#8b97b0;font-size:0.78rem;'>{escape(str(line))}</div>"
        for line in lines
    )
    return (
        f"<div style='background:#111827;color:#e8ecf4;padding:8px 10px;"
        f"border-radius:8px;min-width:180px;font-family:sans-serif;'>"
        f"<div style='font-weight:700;font-size:0.9rem;color:#06b6d4;margin-bottom:4px;'>"
        f"{safe_title}</div>{body}</div>"
    )


def _dark_fig(figsize=(10, 5)):
    """Create a matplotlib figure with dark theme."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    ax.tick_params(colors=SECONDARY_COLOR, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(MUTED_COLOR)
    return fig, ax


def _styled_metric(label, value, delta=None):
    """Render a styled metric card in HTML."""
    delta_html = ""
    if delta is not None:
        delta_html = f"<div style='color:#06b6d4;font-size:0.75rem;'>{escape(str(delta))}</div>"
    return (
        f"<div style='background:#1a2235;border:1px solid #2a3550;border-radius:10px;"
        f"padding:12px 16px;text-align:center;'>"
        f"<div style='color:#8b97b0;font-size:0.75rem;'>{escape(str(label))}</div>"
        f"<div style='color:#e8ecf4;font-size:1.5rem;font-weight:700;'>{escape(str(value))}</div>"
        f"{delta_html}</div>"
    )


# ═══════════════════════════════════════════════════════════════
# CACHED DATA BUILDERS
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _build_ydna_df():
    rows = []
    for hg in YDNA_HAPLOGROUPS:
        for r in hg["regions"]:
            rows.append({
                "Haplogroup": hg["haplogroup"],
                "Description": hg["desc"],
                "Region": r["name"],
                "Latitude": r["lat"],
                "Longitude": r["lon"],
                "Frequency (%)": r["freq"],
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_mtdna_df():
    rows = []
    for hg in MTDNA_HAPLOGROUPS:
        for r in hg["regions"]:
            rows.append({
                "Haplogroup": hg["haplogroup"],
                "Description": hg["desc"],
                "Region": r["name"],
                "Latitude": r["lat"],
                "Longitude": r["lon"],
                "Frequency (%)": r["freq"],
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_neanderthal_df():
    return pd.DataFrame(NEANDERTHAL_DATA)


@st.cache_data(ttl=3600)
def _build_diversity_df():
    return pd.DataFrame(GENETIC_DIVERSITY)


@st.cache_data(ttl=3600)
def _build_blood_df():
    return pd.DataFrame(BLOOD_TYPE_DATA)


@st.cache_data(ttl=3600)
def _build_lactose_df():
    return pd.DataFrame(LACTOSE_TOLERANCE)


@st.cache_data(ttl=3600)
def _build_eye_color_df():
    return pd.DataFrame(EYE_COLOR_DATA)


@st.cache_data(ttl=3600)
def _build_disease_df():
    rows = []
    for d in GENETIC_DISEASES:
        for h in d["hotspots"]:
            rows.append({
                "Disease": d["disease"],
                "Location": h["name"],
                "Latitude": h["lat"],
                "Longitude": h["lon"],
                "Prevalence": h["prevalence"],
                "Detail": h["detail"],
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _build_adna_df():
    return pd.DataFrame(ANCIENT_DNA_SITES)


# ═══════════════════════════════════════════════════════════════
# RENDER FUNCTIONS FOR EACH MODE
# ═══════════════════════════════════════════════════════════════

def _render_ydna_haplogroups():
    """Mode 1: Y-DNA Haplogroups world map."""
    st.markdown("#### Y-DNA Haplogroup Distribution")
    st.caption(
        "Major Y-chromosome haplogroups and their geographic concentrations. "
        "Frequency percentages represent approximate carrier rates in each population."
    )

    df = _build_ydna_df()

    # --- Stats ---
    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Haplogroups", len(YDNA_HAPLOGROUPS)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Data Points", len(df)), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Max Frequency", f"{df['Frequency (%)'].max()}%"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Avg Frequency", f"{df['Frequency (%)'].mean():.1f}%"), unsafe_allow_html=True)

    # --- Filter ---
    selected = st.multiselect(
        "Filter haplogroups",
        options=[h["haplogroup"] for h in YDNA_HAPLOGROUPS],
        default=[h["haplogroup"] for h in YDNA_HAPLOGROUPS],
        key="ydna_filter",
    )

    # --- Map ---
    m = _make_map()
    for hg in YDNA_HAPLOGROUPS:
        if hg["haplogroup"] not in selected:
            continue
        fg = folium.FeatureGroup(name=f"Y-DNA {hg['haplogroup']}")
        for r in hg["regions"]:
            radius = max(4, r["freq"] / 5)
            popup = _popup_html(
                f"Y-DNA {hg['haplogroup']}",
                [r["name"], f"Frequency: ~{r['freq']}%", hg["desc"]],
            )
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=radius,
                color=hg["color"],
                fill=True,
                fill_color=hg["color"],
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup, max_width=260),
                tooltip=f"{hg['haplogroup']} - {r['name']} ({r['freq']}%)",
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Bar chart ---
    st.markdown("#### Frequency by Region")
    df_filtered = df[df["Haplogroup"].isin(selected)]
    if not df_filtered.empty:
        fig, ax = _dark_fig((12, 5))
        hg_list = df_filtered["Haplogroup"].unique()
        color_map = {h["haplogroup"]: h["color"] for h in YDNA_HAPLOGROUPS}
        x_positions = np.arange(len(df_filtered))
        bars = ax.bar(
            x_positions,
            df_filtered["Frequency (%)"].values,
            color=[color_map.get(h, ACCENT_COLOR) for h in df_filtered["Haplogroup"].values],
            edgecolor="#2a3550",
            linewidth=0.5,
        )
        ax.set_xticks(x_positions)
        ax.set_xticklabels(
            [f"{row['Haplogroup']}\n{row['Region']}" for _, row in df_filtered.iterrows()],
            rotation=60, ha="right", fontsize=6, color=SECONDARY_COLOR,
        )
        ax.set_ylabel("Frequency (%)", color=TEXT_COLOR, fontsize=9)
        ax.set_title("Y-DNA Haplogroup Frequencies", color=TEXT_COLOR, fontsize=11, pad=10)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # --- Table ---
    st.markdown("#### Data Table")
    st.dataframe(df_filtered, width="stretch", hide_index=True)

    # --- Download ---
    csv = df_filtered.to_csv(index=False)
    st.download_button("Download CSV", csv, "ydna_haplogroups.csv", "text/csv", key="dl_ydna")


def _render_mtdna_haplogroups():
    """Mode 2: mtDNA Haplogroups world map."""
    st.markdown("#### mtDNA Haplogroup Distribution")
    st.caption(
        "Major mitochondrial DNA lineages tracing maternal ancestry. "
        "All non-African mtDNA descends from macro-haplogroups M and N (daughters of L3)."
    )

    df = _build_mtdna_df()

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Haplogroups", len(MTDNA_HAPLOGROUPS)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Data Points", len(df)), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Oldest Lineage", "L0 (>150 kya)"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Avg Frequency", f"{df['Frequency (%)'].mean():.1f}%"), unsafe_allow_html=True)

    selected = st.multiselect(
        "Filter haplogroups",
        options=[h["haplogroup"] for h in MTDNA_HAPLOGROUPS],
        default=[h["haplogroup"] for h in MTDNA_HAPLOGROUPS],
        key="mtdna_filter",
    )

    m = _make_map()
    for hg in MTDNA_HAPLOGROUPS:
        if hg["haplogroup"] not in selected:
            continue
        fg = folium.FeatureGroup(name=f"mtDNA {hg['haplogroup']}")
        for r in hg["regions"]:
            radius = max(4, r["freq"] / 5)
            popup = _popup_html(
                f"mtDNA {hg['haplogroup']}",
                [r["name"], f"Frequency: ~{r['freq']}%", hg["desc"]],
            )
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=radius,
                color=hg["color"],
                fill=True,
                fill_color=hg["color"],
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup, max_width=260),
                tooltip=f"{hg['haplogroup']} - {r['name']} ({r['freq']}%)",
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart ---
    st.markdown("#### Frequency Comparison")
    df_f = df[df["Haplogroup"].isin(selected)]
    if not df_f.empty:
        fig, ax = _dark_fig((12, 5))
        color_map = {h["haplogroup"]: h["color"] for h in MTDNA_HAPLOGROUPS}
        x_pos = np.arange(len(df_f))
        ax.bar(
            x_pos, df_f["Frequency (%)"].values,
            color=[color_map.get(h, ACCENT_COLOR) for h in df_f["Haplogroup"].values],
            edgecolor="#2a3550", linewidth=0.5,
        )
        ax.set_xticks(x_pos)
        ax.set_xticklabels(
            [f"{row['Haplogroup']}\n{row['Region']}" for _, row in df_f.iterrows()],
            rotation=60, ha="right", fontsize=6, color=SECONDARY_COLOR,
        )
        ax.set_ylabel("Frequency (%)", color=TEXT_COLOR, fontsize=9)
        ax.set_title("mtDNA Haplogroup Frequencies", color=TEXT_COLOR, fontsize=11, pad=10)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.markdown("#### Data Table")
    st.dataframe(df_f, width="stretch", hide_index=True)
    csv = df_f.to_csv(index=False)
    st.download_button("Download CSV", csv, "mtdna_haplogroups.csv", "text/csv", key="dl_mtdna")


def _render_migration_routes():
    """Mode 3: Human Migration Out of Africa."""
    st.markdown("#### Human Migration Out of Africa")
    st.caption(
        "Major migration routes of Homo sapiens from ~70,000 to ~1,000 years ago. "
        "Lines show approximate paths; markers show key fossil/archaeological sites."
    )

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Routes", len(MIGRATION_ROUTES)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Key Sites", len(MIGRATION_LANDMARKS)), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Time Span", "~70,000 yrs"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Origin", "East Africa"), unsafe_allow_html=True)

    selected_routes = st.multiselect(
        "Filter migration routes",
        options=[r["name"] for r in MIGRATION_ROUTES],
        default=[r["name"] for r in MIGRATION_ROUTES],
        key="migration_filter",
    )

    m = _make_map(center=[15, 40], zoom=2)

    # Draw routes
    for route in MIGRATION_ROUTES:
        if route["name"] not in selected_routes:
            continue
        folium.PolyLine(
            locations=route["path"],
            color=route["color"],
            weight=route["weight"],
            opacity=0.85,
            tooltip=f"{route['name']} ({route['date_range']})",
            popup=folium.Popup(
                _popup_html(route["name"], [route["date_range"], route["desc"]]),
                max_width=280,
            ),
            dash_array="8" if "Polynesia" in route["name"] or "Madagascar" in route["name"] else None,
        ).add_to(m)

        # Arrow at end of route
        end = route["path"][-1]
        folium.CircleMarker(
            location=end,
            radius=5,
            color=route["color"],
            fill=True,
            fill_color=route["color"],
            fill_opacity=0.9,
            weight=2,
        ).add_to(m)

    # Draw landmarks
    for lm in MIGRATION_LANDMARKS:
        popup = _popup_html(lm["name"], [lm["desc"]])
        folium.Marker(
            location=[lm["lat"], lm["lon"]],
            popup=folium.Popup(popup, max_width=260),
            tooltip=lm["name"],
            icon=folium.Icon(color="darkred" if "Homo sapiens" in lm["desc"] else "blue",
                             icon="star" if "oldest" in lm["desc"].lower() else "info-sign"),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # --- Timeline ---
    st.markdown("#### Migration Timeline")
    fig, ax = _dark_fig((12, 4))
    route_data = [r for r in MIGRATION_ROUTES if r["name"] in selected_routes]
    y_pos = np.arange(len(route_data))
    for i, r in enumerate(route_data):
        # Extract approximate start year from date_range
        date_str = r["date_range"].replace("~", "").replace(",", "")
        parts = date_str.split("-")
        try:
            start_yr = int(parts[0].strip().split()[0])
        except (ValueError, IndexError):
            start_yr = 50000
        try:
            end_yr = int(parts[1].strip().split()[0]) if len(parts) > 1 else start_yr - 10000
        except (ValueError, IndexError):
            end_yr = start_yr - 10000
        ax.barh(i, start_yr - end_yr, left=end_yr, color=r["color"], height=0.6, edgecolor="#2a3550")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([r["name"] for r in route_data], fontsize=7, color=TEXT_COLOR)
    ax.set_xlabel("Years Before Present", color=TEXT_COLOR, fontsize=9)
    ax.set_title("Migration Timeline", color=TEXT_COLOR, fontsize=11, pad=10)
    ax.invert_xaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # --- Landmark table ---
    st.markdown("#### Key Archaeological Sites")
    lm_df = pd.DataFrame(MIGRATION_LANDMARKS)
    st.dataframe(lm_df[["name", "lat", "lon", "desc"]], width="stretch", hide_index=True)


def _render_neanderthal_dna():
    """Mode 4: Neanderthal DNA Distribution."""
    st.markdown("#### Neanderthal DNA in Modern Populations")
    st.caption(
        "Percentage of Neanderthal ancestry in present-day human populations. "
        "Admixture occurred ~50,000-60,000 years ago; most non-Africans carry ~2%."
    )

    df = _build_neanderthal_df()

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Populations", len(df)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Max %", f"{df['pct'].max():.1f}%"), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Min %", f"{df['pct'].min():.1f}%"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Avg %", f"{df['pct'].mean():.2f}%"), unsafe_allow_html=True)

    m = _make_map()
    for _, row in df.iterrows():
        pct = row["pct"]
        # Color gradient: low=green, mid=yellow, high=red
        if pct < 0.5:
            color = "#10b981"
        elif pct < 1.5:
            color = "#f59e0b"
        elif pct < 2.2:
            color = "#f97316"
        else:
            color = "#ef4444"
        radius = max(6, pct * 6)
        popup = _popup_html(
            row["population"],
            [f"Neanderthal DNA: {pct}%", row["region"], row["note"]],
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{row['population']}: {pct}%",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Bar chart ---
    st.markdown("#### Neanderthal Ancestry by Population")
    fig, ax = _dark_fig((12, 5))
    df_sorted = df.sort_values("pct", ascending=True)
    colors = []
    for p in df_sorted["pct"]:
        if p < 0.5:
            colors.append("#10b981")
        elif p < 1.5:
            colors.append("#f59e0b")
        elif p < 2.2:
            colors.append("#f97316")
        else:
            colors.append("#ef4444")
    ax.barh(range(len(df_sorted)), df_sorted["pct"].values, color=colors, edgecolor="#2a3550", height=0.7)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted["population"].values, fontsize=8, color=TEXT_COLOR)
    ax.set_xlabel("Neanderthal DNA (%)", color=TEXT_COLOR, fontsize=9)
    ax.set_title("Neanderthal Ancestry Across Modern Populations", color=TEXT_COLOR, fontsize=11, pad=10)
    for i, v in enumerate(df_sorted["pct"].values):
        ax.text(v + 0.05, i, f"{v}%", va="center", fontsize=7, color=TEXT_COLOR)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("#### Data Table")
    st.dataframe(df[["population", "region", "pct", "note"]], width="stretch", hide_index=True)
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "neanderthal_dna.csv", "text/csv", key="dl_nean")


def _render_genetic_diversity():
    """Mode 5: Genetic Diversity by Region."""
    st.markdown("#### Genetic Diversity (Heterozygosity)")
    st.caption(
        "Expected heterozygosity decreases with geographic distance from Africa, "
        "reflecting serial founder effects during human migration. Africa retains the highest diversity."
    )

    df = _build_diversity_df()

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Populations", len(df)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Highest", f"{df['het'].max():.2f}"), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Lowest", f"{df['het'].min():.2f}"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Range", f"{df['het'].max() - df['het'].min():.2f}"), unsafe_allow_html=True)

    m = _make_map()
    for _, row in df.iterrows():
        het = row["het"]
        # Color gradient: high diversity=green, low=red
        if het >= 0.72:
            color = "#10b981"
        elif het >= 0.65:
            color = "#06b6d4"
        elif het >= 0.60:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        radius = max(5, het * 14)
        popup = _popup_html(
            row["population"],
            [f"Heterozygosity: {het:.2f}", row["region"], row["note"]],
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{row['population']}: {het:.2f}",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart ---
    st.markdown("#### Heterozygosity Index by Population")
    fig, ax = _dark_fig((12, 5))
    df_sorted = df.sort_values("het", ascending=True)
    colors = []
    for h in df_sorted["het"]:
        if h >= 0.72:
            colors.append("#10b981")
        elif h >= 0.65:
            colors.append("#06b6d4")
        elif h >= 0.60:
            colors.append("#f59e0b")
        else:
            colors.append("#ef4444")
    ax.barh(range(len(df_sorted)), df_sorted["het"].values, color=colors, edgecolor="#2a3550", height=0.7)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted["population"].values, fontsize=8, color=TEXT_COLOR)
    ax.set_xlabel("Expected Heterozygosity", color=TEXT_COLOR, fontsize=9)
    ax.set_title("Genetic Diversity Decreasing With Distance From Africa", color=TEXT_COLOR, fontsize=11, pad=10)
    for i, v in enumerate(df_sorted["het"].values):
        ax.text(v + 0.003, i, f"{v:.2f}", va="center", fontsize=7, color=TEXT_COLOR)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("#### Data Table")
    st.dataframe(df[["population", "region", "het", "note"]], width="stretch", hide_index=True)
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "genetic_diversity.csv", "text/csv", key="dl_div")


def _render_blood_types():
    """Mode 6: Blood Type Distribution."""
    st.markdown("#### ABO Blood Type Distribution by Country")
    st.caption(
        "Blood type frequencies vary significantly across populations. "
        "Type O is most common globally; type B is most frequent in Central/South Asia."
    )

    df = _build_blood_df()

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Countries", len(df)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Highest O%", f"{df['O'].max()}% (Peru)"), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Highest B%", f"{df['B'].max()}% (Bangladesh)"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Highest AB%", f"{df['AB'].max()}% (S. Korea)"), unsafe_allow_html=True)

    bt_display = st.radio(
        "Highlight blood type",
        ["O", "A", "B", "AB"],
        horizontal=True,
        key="blood_type_sel",
    )
    bt_colors = {"O": "#ef4444", "A": "#3b82f6", "B": "#10b981", "AB": "#f59e0b"}

    m = _make_map()
    for _, row in df.iterrows():
        freq = row[bt_display]
        radius = max(4, freq / 4)
        popup = _popup_html(
            row["country"],
            [f"O: {row['O']}%  |  A: {row['A']}%",
             f"B: {row['B']}%  |  AB: {row['AB']}%"],
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=bt_colors[bt_display],
            fill=True,
            fill_color=bt_colors[bt_display],
            fill_opacity=min(0.9, freq / 100 + 0.3),
            weight=2,
            popup=folium.Popup(popup, max_width=260),
            tooltip=f"{row['country']}: {bt_display}={freq}%",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Stacked bar chart ---
    st.markdown("#### Blood Type Frequencies")
    fig, ax = _dark_fig((14, 6))
    df_sorted = df.sort_values("O", ascending=False)
    countries = df_sorted["country"].values
    x = np.arange(len(countries))
    w = 0.65
    bottom = np.zeros(len(countries))
    for bt, color in [("O", "#ef4444"), ("A", "#3b82f6"), ("B", "#10b981"), ("AB", "#f59e0b")]:
        vals = df_sorted[bt].values.astype(float)
        ax.bar(x, vals, w, bottom=bottom, color=color, label=f"Type {bt}", edgecolor="#2a3550", linewidth=0.3)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(countries, rotation=70, ha="right", fontsize=6, color=SECONDARY_COLOR)
    ax.set_ylabel("Percentage (%)", color=TEXT_COLOR, fontsize=9)
    ax.set_title("ABO Blood Type Distribution by Country", color=TEXT_COLOR, fontsize=11, pad=10)
    ax.legend(loc="upper right", fontsize=7, facecolor=SURFACE_COLOR, edgecolor=MUTED_COLOR, labelcolor=TEXT_COLOR)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("#### Data Table")
    st.dataframe(df_sorted, width="stretch", hide_index=True)
    csv = df_sorted.to_csv(index=False)
    st.download_button("Download CSV", csv, "blood_types.csv", "text/csv", key="dl_blood")


def _render_lactose_tolerance():
    """Mode 7: Lactose Tolerance worldwide."""
    st.markdown("#### Lactase Persistence (Lactose Tolerance) Worldwide")
    st.caption(
        "Lactase persistence evolved independently in multiple pastoral populations. "
        "Northern Europeans, East African pastoralists, and some Arabian groups show high rates."
    )

    df = _build_lactose_df()

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Regions", len(df)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Highest", f"{df['tolerance_pct'].max()}%"), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Lowest", f"{df['tolerance_pct'].min()}%"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Global Avg", f"~35%"), unsafe_allow_html=True)

    m = _make_map()
    for _, row in df.iterrows():
        pct = row["tolerance_pct"]
        if pct >= 80:
            color = "#10b981"
        elif pct >= 50:
            color = "#06b6d4"
        elif pct >= 20:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        radius = max(4, pct / 6)
        popup = _popup_html(
            row["region"],
            [f"Lactase persistence: {pct}%", row["note"]],
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup, max_width=260),
            tooltip=f"{row['region']}: {pct}%",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Chart ---
    st.markdown("#### Lactase Persistence Rates")
    fig, ax = _dark_fig((14, 6))
    df_sorted = df.sort_values("tolerance_pct", ascending=True)
    colors = []
    for p in df_sorted["tolerance_pct"]:
        if p >= 80:
            colors.append("#10b981")
        elif p >= 50:
            colors.append("#06b6d4")
        elif p >= 20:
            colors.append("#f59e0b")
        else:
            colors.append("#ef4444")
    ax.barh(range(len(df_sorted)), df_sorted["tolerance_pct"].values, color=colors,
            edgecolor="#2a3550", height=0.7)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted["region"].values, fontsize=7, color=TEXT_COLOR)
    ax.set_xlabel("Lactose Tolerance (%)", color=TEXT_COLOR, fontsize=9)
    ax.set_title("Lactase Persistence by Region", color=TEXT_COLOR, fontsize=11, pad=10)
    for i, v in enumerate(df_sorted["tolerance_pct"].values):
        ax.text(v + 0.5, i, f"{v}%", va="center", fontsize=6, color=TEXT_COLOR)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("#### Data Table")
    st.dataframe(df_sorted[["region", "lat", "lon", "tolerance_pct", "note"]], width="stretch", hide_index=True)
    csv = df_sorted.to_csv(index=False)
    st.download_button("Download CSV", csv, "lactose_tolerance.csv", "text/csv", key="dl_lact")


def _render_eye_color():
    """Mode 8: Eye Color Distribution."""
    st.markdown("#### Eye Color Distribution by Region")
    st.caption(
        "Eye color is polygenic (OCA2/HEXA genes primary). "
        "Blue eyes originated ~6,000-10,000 years ago near the Black Sea; "
        "brown is ancestral and globally dominant."
    )

    df = _build_eye_color_df()

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Regions", len(df)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Most Blue", f"{df['blue'].max()}% (Iceland)"), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Most Green", f"{df['green'].max()}% (Ireland)"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Most Brown", f"{df['brown'].max()}%"), unsafe_allow_html=True)

    ec_display = st.radio(
        "Highlight eye color",
        ["blue", "green", "hazel", "brown"],
        horizontal=True,
        key="eye_color_sel",
    )
    ec_colors = {"blue": "#3b82f6", "green": "#10b981", "hazel": "#f59e0b", "brown": "#92400e"}

    m = _make_map(center=[40, 20], zoom=3)
    for _, row in df.iterrows():
        freq = row[ec_display]
        if freq == 0:
            continue
        radius = max(3, freq / 4)
        popup = _popup_html(
            row["region"],
            [f"Blue: {row['blue']}%  |  Green: {row['green']}%",
             f"Hazel: {row['hazel']}%  |  Brown: {row['brown']}%"],
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=ec_colors[ec_display],
            fill=True,
            fill_color=ec_colors[ec_display],
            fill_opacity=min(0.9, freq / 100 + 0.3),
            weight=2,
            popup=folium.Popup(popup, max_width=260),
            tooltip=f"{row['region']}: {ec_display}={freq}%",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Stacked bar ---
    st.markdown("#### Eye Color Frequencies")
    fig, ax = _dark_fig((14, 6))
    df_sorted = df.sort_values("blue", ascending=False)
    regions = df_sorted["region"].values
    x = np.arange(len(regions))
    w = 0.65
    bottom = np.zeros(len(regions))
    for ec, color in [("blue", "#3b82f6"), ("green", "#10b981"), ("hazel", "#f59e0b"), ("brown", "#92400e")]:
        vals = df_sorted[ec].values.astype(float)
        ax.bar(x, vals, w, bottom=bottom, color=color, label=ec.capitalize(), edgecolor="#2a3550", linewidth=0.3)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(regions, rotation=70, ha="right", fontsize=6, color=SECONDARY_COLOR)
    ax.set_ylabel("Percentage (%)", color=TEXT_COLOR, fontsize=9)
    ax.set_title("Eye Color Distribution by Region", color=TEXT_COLOR, fontsize=11, pad=10)
    ax.legend(loc="upper right", fontsize=7, facecolor=SURFACE_COLOR, edgecolor=MUTED_COLOR, labelcolor=TEXT_COLOR)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("#### Data Table")
    st.dataframe(df_sorted, width="stretch", hide_index=True)
    csv = df_sorted.to_csv(index=False)
    st.download_button("Download CSV", csv, "eye_color.csv", "text/csv", key="dl_eye")


def _render_genetic_diseases():
    """Mode 9: Genetic Disease Hotspots."""
    st.markdown("#### Genetic Disease Geographic Hotspots")
    st.caption(
        "Many genetic diseases show geographic clustering due to founder effects, "
        "consanguinity, or heterozygote advantage (e.g., malaria resistance for sickle cell carriers)."
    )

    df = _build_disease_df()
    disease_names = [d["disease"] for d in GENETIC_DISEASES]

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Diseases Mapped", len(GENETIC_DISEASES)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Hotspot Locations", len(df)), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Malaria-linked", "3 diseases"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Founder Effect", "4 diseases"), unsafe_allow_html=True)

    selected_diseases = st.multiselect(
        "Filter diseases",
        options=disease_names,
        default=disease_names,
        key="disease_filter",
    )

    m = _make_map()
    for disease in GENETIC_DISEASES:
        if disease["disease"] not in selected_diseases:
            continue
        fg = folium.FeatureGroup(name=disease["disease"])
        for h in disease["hotspots"]:
            popup = _popup_html(
                disease["disease"],
                [h["name"], f"Prevalence: {h['prevalence']}", h["detail"], disease["desc"]],
            )
            folium.CircleMarker(
                location=[h["lat"], h["lon"]],
                radius=10,
                color=disease["color"],
                fill=True,
                fill_color=disease["color"],
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup, max_width=300),
                tooltip=f"{disease['disease']} - {h['name']}",
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Disease cards ---
    st.markdown("#### Disease Summaries")
    for disease in GENETIC_DISEASES:
        if disease["disease"] not in selected_diseases:
            continue
        with st.expander(f"{disease['disease']}", expanded=False):
            st.markdown(
                f"<div style='color:{SECONDARY_COLOR};font-size:0.85rem;'>"
                f"{escape(disease['desc'])}</div>",
                unsafe_allow_html=True,
            )
            hotspot_df = pd.DataFrame(disease["hotspots"])
            st.dataframe(hotspot_df[["name", "prevalence", "detail"]], width="stretch", hide_index=True)

    # --- Chart ---
    st.markdown("#### Hotspot Count by Disease")
    fig, ax = _dark_fig((10, 4))
    d_names = [d["disease"] for d in GENETIC_DISEASES if d["disease"] in selected_diseases]
    d_counts = [len(d["hotspots"]) for d in GENETIC_DISEASES if d["disease"] in selected_diseases]
    d_colors = [d["color"] for d in GENETIC_DISEASES if d["disease"] in selected_diseases]
    ax.barh(range(len(d_names)), d_counts, color=d_colors, edgecolor="#2a3550", height=0.6)
    ax.set_yticks(range(len(d_names)))
    ax.set_yticklabels(d_names, fontsize=8, color=TEXT_COLOR)
    ax.set_xlabel("Number of Hotspot Regions", color=TEXT_COLOR, fontsize=9)
    ax.set_title("Genetic Disease Hotspot Distribution", color=TEXT_COLOR, fontsize=11, pad=10)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("#### Full Data Table")
    df_filtered = df[df["Disease"].isin(selected_diseases)]
    st.dataframe(df_filtered, width="stretch", hide_index=True)
    csv = df_filtered.to_csv(index=False)
    st.download_button("Download CSV", csv, "genetic_diseases.csv", "text/csv", key="dl_disease")


def _render_ancient_dna_sites():
    """Mode 10: Ancient DNA Discovery Sites."""
    st.markdown("#### Ancient DNA Discovery Sites")
    st.caption(
        "Major archaeological sites where ancient DNA has been successfully extracted and sequenced. "
        "These findings have revolutionized our understanding of human evolution and migration."
    )

    df = _build_adna_df()

    cols = st.columns(4)
    cols[0].markdown(_styled_metric("Sites", len(ANCIENT_DNA_SITES)), unsafe_allow_html=True)
    cols[1].markdown(_styled_metric("Oldest", "~300,000 BP"), unsafe_allow_html=True)
    cols[2].markdown(_styled_metric("Newest", "~4,500 BP"), unsafe_allow_html=True)
    cols[3].markdown(_styled_metric("Continents", "5"), unsafe_allow_html=True)

    # Search filter
    search = st.text_input("Search sites by name, country, or findings", "", key="adna_search")
    if search:
        mask = (
            df["name"].str.contains(search, case=False, na=False)
            | df["country"].str.contains(search, case=False, na=False)
            | df["findings"].str.contains(search, case=False, na=False)
        )
        df_display = df[mask]
    else:
        df_display = df

    m = _make_map(center=[40, 30], zoom=2)
    for _, row in df_display.iterrows():
        popup = _popup_html(
            row["name"],
            [row["country"], f"Age: {row['age']}", row["findings"]],
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=f"{row['name']} ({row['age']})",
            icon=folium.Icon(
                color="red" if "Neanderthal" in row.get("findings", "") else
                       "purple" if "Denisov" in row.get("findings", "") else "blue",
                icon="map-marker",
            ),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # --- Timeline chart ---
    st.markdown("#### Ancient DNA Timeline")
    fig, ax = _dark_fig((14, 7))
    site_ages = []
    for site in ANCIENT_DNA_SITES:
        age_str = site["age"].replace("~", "").replace(",", "").replace("BP", "").strip()
        parts = age_str.split("-")
        try:
            age_val = int(parts[0].strip())
        except (ValueError, IndexError):
            age_val = 0
        site_ages.append((site["name"], age_val, site["color"]))
    site_ages.sort(key=lambda x: x[1])
    names = [s[0] for s in site_ages]
    ages = [s[1] for s in site_ages]
    colors_list = [s[2] for s in site_ages]
    y_pos = np.arange(len(names))
    ax.barh(y_pos, ages, color=colors_list, edgecolor="#2a3550", height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=6, color=TEXT_COLOR)
    ax.set_xlabel("Approximate Age (Years Before Present)", color=TEXT_COLOR, fontsize=9)
    ax.set_title("Ancient DNA Sites by Age", color=TEXT_COLOR, fontsize=11, pad=10)
    for i, v in enumerate(ages):
        label = f"{v:,}" if v > 0 else "?"
        ax.text(v + 500, i, label, va="center", fontsize=5.5, color=SECONDARY_COLOR)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # --- Table ---
    st.markdown("#### Site Details")
    st.dataframe(
        df_display[["name", "country", "age", "findings"]],
        width="stretch",
        hide_index=True,
    )
    csv = df_display.to_csv(index=False)
    st.download_button("Download CSV", csv, "ancient_dna_sites.csv", "text/csv", key="dl_adna")


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

MAP_MODES = {
    "Y-DNA Haplogroups": _render_ydna_haplogroups,
    "mtDNA Haplogroups": _render_mtdna_haplogroups,
    "Human Migration Out of Africa": _render_migration_routes,
    "Neanderthal DNA Distribution": _render_neanderthal_dna,
    "Genetic Diversity by Region": _render_genetic_diversity,
    "Blood Type Distribution": _render_blood_types,
    "Lactose Tolerance": _render_lactose_tolerance,
    "Eye Color Distribution": _render_eye_color,
    "Genetic Disease Hotspots": _render_genetic_diseases,
    "Ancient DNA Sites": _render_ancient_dna_sites,
}


def render_genetics_maps_tab():
    """Main entry point for the Genetics & DNA Maps tab."""
    st.markdown(
        '<div class="tab-header violet"><h4>\U0001f9ec Genetics & DNA Maps</h4>'
        '<p>Haplogroups, genetic diversity, human evolution & population genetics</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Select map mode",
        list(MAP_MODES.keys()),
        key="genetics_map_mode",
        horizontal=False,
    )

    st.markdown("---")

    # Render the selected mode
    render_fn = MAP_MODES.get(mode)
    if render_fn:
        render_fn()
