# -*- coding: utf-8 -*-
"""
Linguistic & Language Maps module for TerraScout AI.
Provides 10 interactive map modes exploring world languages, language families,
endangered languages, writing systems, sign languages, creoles, ancient
languages, and linguistic diversity indices.
Uses curated datasets and the REST Countries API (free, no key).
"""

import io
import logging
import streamlit as st
import requests
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

logger = logging.getLogger(__name__)

# =====================================================================
# THEME CONSTANTS
# =====================================================================
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_COLOR = "#06b6d4"
MUTED_COLOR = "#5a6580"
SECONDARY_COLOR = "#8b97b0"

REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,languages,latlng,population"

# =====================================================================
# 1. WORLD LANGUAGE FAMILIES  (curated ~55 representative entries)
# =====================================================================
FAMILY_COLORS = {
    "Indo-European": "#3b82f6",
    "Sino-Tibetan": "#ef4444",
    "Afro-Asiatic": "#f59e0b",
    "Niger-Congo": "#10b981",
    "Austronesian": "#8b5cf6",
    "Dravidian": "#ec4899",
    "Turkic": "#f97316",
    "Japonic": "#06b6d4",
    "Koreanic": "#14b8a6",
    "Uralic": "#a855f7",
    "Tai-Kadai": "#22c55e",
    "Austroasiatic": "#eab308",
    "Mongolic": "#fb923c",
    "Tupian": "#84cc16",
    "Pama-Nyungan": "#d946ef",
    "Nilo-Saharan": "#64748b",
    "Quechuan": "#0ea5e9",
    "Na-Dene": "#7c3aed",
    "Algic": "#dc2626",
    "Eskimo-Aleut": "#94a3b8",
}

LANGUAGE_FAMILIES = [
    {"family": "Indo-European", "lang": "English", "lat": 51.5, "lon": -0.13, "speakers": 1500, "region": "Global"},
    {"family": "Indo-European", "lang": "Spanish", "lat": 40.42, "lon": -3.70, "speakers": 550, "region": "Europe / Americas"},
    {"family": "Indo-European", "lang": "Hindi", "lat": 28.61, "lon": 77.21, "speakers": 600, "region": "South Asia"},
    {"family": "Indo-European", "lang": "Portuguese", "lat": 38.72, "lon": -9.14, "speakers": 260, "region": "Europe / Americas / Africa"},
    {"family": "Indo-European", "lang": "Russian", "lat": 55.75, "lon": 37.62, "speakers": 260, "region": "Eurasia"},
    {"family": "Indo-European", "lang": "German", "lat": 52.52, "lon": 13.41, "speakers": 135, "region": "Central Europe"},
    {"family": "Indo-European", "lang": "French", "lat": 48.86, "lon": 2.35, "speakers": 310, "region": "Global"},
    {"family": "Indo-European", "lang": "Bengali", "lat": 23.81, "lon": 90.41, "speakers": 270, "region": "South Asia"},
    {"family": "Indo-European", "lang": "Punjabi", "lat": 31.55, "lon": 74.35, "speakers": 150, "region": "South Asia"},
    {"family": "Indo-European", "lang": "Persian", "lat": 35.69, "lon": 51.39, "speakers": 110, "region": "West / Central Asia"},
    {"family": "Sino-Tibetan", "lang": "Mandarin Chinese", "lat": 39.91, "lon": 116.40, "speakers": 920, "region": "East Asia"},
    {"family": "Sino-Tibetan", "lang": "Cantonese", "lat": 23.13, "lon": 113.26, "speakers": 85, "region": "South China"},
    {"family": "Sino-Tibetan", "lang": "Burmese", "lat": 16.87, "lon": 96.20, "speakers": 43, "region": "Southeast Asia"},
    {"family": "Sino-Tibetan", "lang": "Tibetan", "lat": 29.65, "lon": 91.17, "speakers": 6, "region": "Central Asia"},
    {"family": "Afro-Asiatic", "lang": "Arabic", "lat": 24.71, "lon": 46.68, "speakers": 380, "region": "Middle East / N. Africa"},
    {"family": "Afro-Asiatic", "lang": "Hausa", "lat": 12.00, "lon": 8.52, "speakers": 80, "region": "West Africa"},
    {"family": "Afro-Asiatic", "lang": "Amharic", "lat": 9.02, "lon": 38.75, "speakers": 57, "region": "East Africa"},
    {"family": "Afro-Asiatic", "lang": "Hebrew", "lat": 31.77, "lon": 35.23, "speakers": 9, "region": "Middle East"},
    {"family": "Afro-Asiatic", "lang": "Somali", "lat": 2.05, "lon": 45.32, "speakers": 22, "region": "East Africa"},
    {"family": "Niger-Congo", "lang": "Swahili", "lat": -6.79, "lon": 39.28, "speakers": 100, "region": "East Africa"},
    {"family": "Niger-Congo", "lang": "Yoruba", "lat": 7.40, "lon": 3.92, "speakers": 50, "region": "West Africa"},
    {"family": "Niger-Congo", "lang": "Igbo", "lat": 6.44, "lon": 3.39, "speakers": 45, "region": "West Africa"},
    {"family": "Niger-Congo", "lang": "Zulu", "lat": -29.86, "lon": 31.02, "speakers": 28, "region": "Southern Africa"},
    {"family": "Niger-Congo", "lang": "Shona", "lat": -17.83, "lon": 31.05, "speakers": 15, "region": "Southern Africa"},
    {"family": "Austronesian", "lang": "Malay / Indonesian", "lat": -6.21, "lon": 106.85, "speakers": 290, "region": "Southeast Asia"},
    {"family": "Austronesian", "lang": "Tagalog", "lat": 14.60, "lon": 120.98, "speakers": 82, "region": "Philippines"},
    {"family": "Austronesian", "lang": "Javanese", "lat": -7.80, "lon": 110.36, "speakers": 82, "region": "Indonesia"},
    {"family": "Austronesian", "lang": "Malagasy", "lat": -18.91, "lon": 47.52, "speakers": 25, "region": "Madagascar"},
    {"family": "Austronesian", "lang": "Hawaiian", "lat": 21.31, "lon": -157.86, "speakers": 0.024, "region": "Pacific"},
    {"family": "Dravidian", "lang": "Tamil", "lat": 13.08, "lon": 80.27, "speakers": 78, "region": "South Asia"},
    {"family": "Dravidian", "lang": "Telugu", "lat": 17.39, "lon": 78.49, "speakers": 83, "region": "South Asia"},
    {"family": "Dravidian", "lang": "Kannada", "lat": 12.97, "lon": 77.59, "speakers": 59, "region": "South Asia"},
    {"family": "Dravidian", "lang": "Malayalam", "lat": 8.52, "lon": 76.94, "speakers": 38, "region": "South Asia"},
    {"family": "Turkic", "lang": "Turkish", "lat": 39.93, "lon": 32.85, "speakers": 82, "region": "West Asia"},
    {"family": "Turkic", "lang": "Uzbek", "lat": 41.30, "lon": 69.28, "speakers": 35, "region": "Central Asia"},
    {"family": "Turkic", "lang": "Azerbaijani", "lat": 40.41, "lon": 49.87, "speakers": 23, "region": "Caucasus"},
    {"family": "Turkic", "lang": "Kazakh", "lat": 51.17, "lon": 71.43, "speakers": 13, "region": "Central Asia"},
    {"family": "Japonic", "lang": "Japanese", "lat": 35.68, "lon": 139.69, "speakers": 125, "region": "East Asia"},
    {"family": "Koreanic", "lang": "Korean", "lat": 37.57, "lon": 126.98, "speakers": 80, "region": "East Asia"},
    {"family": "Uralic", "lang": "Finnish", "lat": 60.17, "lon": 24.94, "speakers": 5.8, "region": "Northern Europe"},
    {"family": "Uralic", "lang": "Hungarian", "lat": 47.50, "lon": 19.04, "speakers": 13, "region": "Central Europe"},
    {"family": "Uralic", "lang": "Estonian", "lat": 59.44, "lon": 24.75, "speakers": 1.1, "region": "Northern Europe"},
    {"family": "Tai-Kadai", "lang": "Thai", "lat": 13.76, "lon": 100.50, "speakers": 60, "region": "Southeast Asia"},
    {"family": "Tai-Kadai", "lang": "Lao", "lat": 17.97, "lon": 102.63, "speakers": 30, "region": "Southeast Asia"},
    {"family": "Austroasiatic", "lang": "Vietnamese", "lat": 21.03, "lon": 105.85, "speakers": 85, "region": "Southeast Asia"},
    {"family": "Austroasiatic", "lang": "Khmer", "lat": 11.56, "lon": 104.92, "speakers": 16, "region": "Southeast Asia"},
    {"family": "Mongolic", "lang": "Mongolian", "lat": 47.91, "lon": 106.91, "speakers": 6, "region": "Central Asia"},
    {"family": "Tupian", "lang": "Guarani", "lat": -25.26, "lon": -57.58, "speakers": 6.5, "region": "South America"},
    {"family": "Pama-Nyungan", "lang": "Western Desert", "lat": -25.0, "lon": 129.0, "speakers": 0.007, "region": "Australia"},
    {"family": "Nilo-Saharan", "lang": "Luo", "lat": 0.09, "lon": 34.76, "speakers": 7, "region": "East Africa"},
    {"family": "Nilo-Saharan", "lang": "Kanuri", "lat": 11.85, "lon": 13.16, "speakers": 10, "region": "West Africa"},
    {"family": "Quechuan", "lang": "Quechua", "lat": -13.52, "lon": -71.97, "speakers": 8.9, "region": "South America"},
    {"family": "Na-Dene", "lang": "Navajo", "lat": 36.07, "lon": -109.19, "speakers": 0.17, "region": "North America"},
    {"family": "Algic", "lang": "Cree", "lat": 53.0, "lon": -90.0, "speakers": 0.096, "region": "North America"},
    {"family": "Eskimo-Aleut", "lang": "Inuktitut", "lat": 63.75, "lon": -68.52, "speakers": 0.039, "region": "Arctic"},
]

# =====================================================================
# 2. MOST SPOKEN LANGUAGES (Top 30 by total speakers, millions)
# =====================================================================
TOP_LANGUAGES = [
    {"rank": 1,  "lang": "English",          "native": 380, "total": 1500, "lat": 51.5,  "lon": -0.13,   "countries": "US, UK, Australia, India, etc."},
    {"rank": 2,  "lang": "Mandarin Chinese",  "native": 920, "total": 1120, "lat": 39.91, "lon": 116.40,  "countries": "China, Taiwan, Singapore"},
    {"rank": 3,  "lang": "Hindi",             "native": 345, "total": 600,  "lat": 28.61, "lon": 77.21,   "countries": "India, Nepal, Fiji"},
    {"rank": 4,  "lang": "Spanish",           "native": 485, "total": 550,  "lat": 40.42, "lon": -3.70,   "countries": "Spain, Latin America, US"},
    {"rank": 5,  "lang": "Arabic",            "native": 310, "total": 380,  "lat": 24.71, "lon": 46.68,   "countries": "22 Arab League states"},
    {"rank": 6,  "lang": "French",            "native": 80,  "total": 310,  "lat": 48.86, "lon": 2.35,    "countries": "France, Africa, Canada"},
    {"rank": 7,  "lang": "Bengali",           "native": 230, "total": 270,  "lat": 23.81, "lon": 90.41,   "countries": "Bangladesh, India"},
    {"rank": 8,  "lang": "Malay / Indonesian", "native": 77,  "total": 290,  "lat": -6.21, "lon": 106.85,  "countries": "Indonesia, Malaysia, Brunei"},
    {"rank": 9,  "lang": "Portuguese",        "native": 230, "total": 260,  "lat": 38.72, "lon": -9.14,   "countries": "Brazil, Portugal, Africa"},
    {"rank": 10, "lang": "Russian",           "native": 150, "total": 260,  "lat": 55.75, "lon": 37.62,   "countries": "Russia, CIS countries"},
    {"rank": 11, "lang": "Japanese",          "native": 125, "total": 125,  "lat": 35.68, "lon": 139.69,  "countries": "Japan"},
    {"rank": 12, "lang": "Punjabi",           "native": 113, "total": 150,  "lat": 31.55, "lon": 74.35,   "countries": "India, Pakistan"},
    {"rank": 13, "lang": "German",            "native": 76,  "total": 135,  "lat": 52.52, "lon": 13.41,   "countries": "Germany, Austria, Switzerland"},
    {"rank": 14, "lang": "Swahili",           "native": 16,  "total": 100,  "lat": -6.79, "lon": 39.28,   "countries": "Tanzania, Kenya, DRC"},
    {"rank": 15, "lang": "Vietnamese",        "native": 85,  "total": 85,   "lat": 21.03, "lon": 105.85,  "countries": "Vietnam"},
    {"rank": 16, "lang": "Javanese",          "native": 82,  "total": 82,   "lat": -7.80, "lon": 110.36,  "countries": "Indonesia (Java)"},
    {"rank": 17, "lang": "Telugu",            "native": 83,  "total": 83,   "lat": 17.39, "lon": 78.49,   "countries": "India (Andhra Pradesh)"},
    {"rank": 18, "lang": "Turkish",           "native": 82,  "total": 82,   "lat": 39.93, "lon": 32.85,   "countries": "Turkey, Cyprus"},
    {"rank": 19, "lang": "Korean",            "native": 80,  "total": 80,   "lat": 37.57, "lon": 126.98,  "countries": "South Korea, North Korea"},
    {"rank": 20, "lang": "Tamil",             "native": 78,  "total": 78,   "lat": 13.08, "lon": 80.27,   "countries": "India, Sri Lanka, Singapore"},
    {"rank": 21, "lang": "Marathi",           "native": 83,  "total": 83,   "lat": 19.08, "lon": 72.88,   "countries": "India (Maharashtra)"},
    {"rank": 22, "lang": "Hausa",             "native": 50,  "total": 80,   "lat": 12.00, "lon": 8.52,    "countries": "Nigeria, Niger, Ghana"},
    {"rank": 23, "lang": "Urdu",              "native": 70,  "total": 70,   "lat": 33.69, "lon": 73.04,   "countries": "Pakistan, India"},
    {"rank": 24, "lang": "Italian",           "native": 65,  "total": 68,   "lat": 41.90, "lon": 12.50,   "countries": "Italy, Switzerland"},
    {"rank": 25, "lang": "Thai",              "native": 21,  "total": 60,   "lat": 13.76, "lon": 100.50,  "countries": "Thailand"},
    {"rank": 26, "lang": "Gujarati",          "native": 57,  "total": 57,   "lat": 23.02, "lon": 72.57,   "countries": "India (Gujarat)"},
    {"rank": 27, "lang": "Polish",            "native": 45,  "total": 45,   "lat": 52.23, "lon": 21.01,   "countries": "Poland"},
    {"rank": 28, "lang": "Amharic",           "native": 32,  "total": 57,   "lat": 9.02,  "lon": 38.75,   "countries": "Ethiopia"},
    {"rank": 29, "lang": "Yoruba",            "native": 45,  "total": 50,   "lat": 7.40,  "lon": 3.92,    "countries": "Nigeria, Benin, Togo"},
    {"rank": 30, "lang": "Kannada",           "native": 44,  "total": 59,   "lat": 12.97, "lon": 77.59,   "countries": "India (Karnataka)"},
]

# =====================================================================
# 3. ENDANGERED LANGUAGES  (UNESCO-inspired, 43 entries)
# =====================================================================
ENDANGERMENT_COLORS = {
    "Critically Endangered": "#ef4444",
    "Severely Endangered": "#f97316",
    "Definitely Endangered": "#f59e0b",
    "Vulnerable": "#eab308",
    "Extinct (recently)": "#64748b",
}

ENDANGERED_LANGUAGES = [
    {"lang": "Ainu",                 "status": "Critically Endangered", "speakers": 10,      "lat": 43.06,  "lon": 141.35,  "country": "Japan",           "family": "Isolate"},
    {"lang": "Livonian",             "status": "Critically Endangered", "speakers": 20,      "lat": 57.57,  "lon": 22.07,   "country": "Latvia",          "family": "Uralic"},
    {"lang": "Ter Sami",             "status": "Critically Endangered", "speakers": 10,      "lat": 68.97,  "lon": 33.09,   "country": "Russia",          "family": "Uralic"},
    {"lang": "Karaim",               "status": "Critically Endangered", "speakers": 80,      "lat": 54.90,  "lon": 23.89,   "country": "Lithuania",       "family": "Turkic"},
    {"lang": "Yagan",                "status": "Critically Endangered", "speakers": 1,       "lat": -54.93, "lon": -67.61,  "country": "Chile",           "family": "Isolate"},
    {"lang": "Kaixana",              "status": "Critically Endangered", "speakers": 1,       "lat": -3.38,  "lon": -64.72,  "country": "Brazil",          "family": "Arawakan"},
    {"lang": "Njerep",               "status": "Critically Endangered", "speakers": 4,       "lat": 6.80,   "lon": 11.30,   "country": "Cameroon",        "family": "Niger-Congo"},
    {"lang": "Chamicuro",            "status": "Critically Endangered", "speakers": 8,       "lat": -5.50,  "lon": -75.25,  "country": "Peru",            "family": "Arawakan"},
    {"lang": "Dumi",                 "status": "Critically Endangered", "speakers": 8,       "lat": 27.38,  "lon": 86.65,   "country": "Nepal",           "family": "Sino-Tibetan"},
    {"lang": "Ongota",               "status": "Critically Endangered", "speakers": 12,      "lat": 5.30,   "lon": 36.55,   "country": "Ethiopia",        "family": "Isolate"},
    {"lang": "Liki",                 "status": "Critically Endangered", "speakers": 11,      "lat": -1.63,  "lon": 138.05,  "country": "Indonesia",       "family": "Austronesian"},
    {"lang": "Tanema",               "status": "Critically Endangered", "speakers": 1,       "lat": -10.72, "lon": 165.80,  "country": "Solomon Islands", "family": "Austronesian"},
    {"lang": "Lemerig",              "status": "Critically Endangered", "speakers": 2,       "lat": -13.83, "lon": 167.25,  "country": "Vanuatu",         "family": "Austronesian"},
    {"lang": "Chulym",               "status": "Critically Endangered", "speakers": 44,      "lat": 56.75,  "lon": 88.05,   "country": "Russia",          "family": "Turkic"},
    {"lang": "Puelche",              "status": "Critically Endangered", "speakers": 5,       "lat": -38.00, "lon": -70.00,  "country": "Argentina",       "family": "Isolate"},
    {"lang": "Siletz Dee-ni",        "status": "Critically Endangered", "speakers": 1,       "lat": 44.72,  "lon": -123.92, "country": "USA",             "family": "Athabaskan"},
    {"lang": "Resigaro",             "status": "Critically Endangered", "speakers": 1,       "lat": -2.75,  "lon": -71.50,  "country": "Peru",            "family": "Arawakan"},
    {"lang": "Koro (Aka-Kora)",      "status": "Critically Endangered", "speakers": 1000,    "lat": 27.10,  "lon": 92.30,   "country": "India",           "family": "Sino-Tibetan"},
    {"lang": "Kusunda",              "status": "Critically Endangered", "speakers": 3,       "lat": 28.25,  "lon": 84.00,   "country": "Nepal",           "family": "Isolate"},
    {"lang": "Michif",               "status": "Critically Endangered", "speakers": 50,      "lat": 52.13,  "lon": -106.67, "country": "Canada",          "family": "Mixed (Cree-French)"},
    {"lang": "Dyirbal",              "status": "Critically Endangered", "speakers": 5,       "lat": -17.63, "lon": 145.98,  "country": "Australia",       "family": "Pama-Nyungan"},
    {"lang": "Sarcee (Tsuut'ina)",   "status": "Severely Endangered",  "speakers": 170,     "lat": 50.90,  "lon": -114.30, "country": "Canada",          "family": "Athabaskan"},
    {"lang": "Breton",               "status": "Severely Endangered",  "speakers": 210000,  "lat": 48.39,  "lon": -4.49,   "country": "France",          "family": "Indo-European"},
    {"lang": "Occitan",              "status": "Severely Endangered",  "speakers": 100000,  "lat": 43.60,  "lon": 1.44,    "country": "France",          "family": "Indo-European"},
    {"lang": "Sorbian",              "status": "Severely Endangered",  "speakers": 20000,   "lat": 51.18,  "lon": 14.43,   "country": "Germany",         "family": "Indo-European"},
    {"lang": "Saterland Frisian",    "status": "Severely Endangered",  "speakers": 2000,    "lat": 53.08,  "lon": 7.68,    "country": "Germany",         "family": "Indo-European"},
    {"lang": "Arberesh Albanian",    "status": "Severely Endangered",  "speakers": 100000,  "lat": 39.57,  "lon": 16.52,   "country": "Italy",           "family": "Indo-European"},
    {"lang": "Tlingit",              "status": "Severely Endangered",  "speakers": 1000,    "lat": 58.30,  "lon": -134.42, "country": "USA",             "family": "Na-Dene"},
    {"lang": "Nuu-chah-nulth",       "status": "Severely Endangered",  "speakers": 150,     "lat": 49.16,  "lon": -125.91, "country": "Canada",          "family": "Wakashan"},
    {"lang": "Scots Gaelic",         "status": "Definitely Endangered", "speakers": 57000,  "lat": 57.48,  "lon": -5.49,   "country": "UK",              "family": "Indo-European"},
    {"lang": "Irish Gaelic",         "status": "Definitely Endangered", "speakers": 80000,  "lat": 53.27,  "lon": -9.06,   "country": "Ireland",         "family": "Indo-European"},
    {"lang": "Aragonese",            "status": "Definitely Endangered", "speakers": 10000,  "lat": 42.44,  "lon": -0.32,   "country": "Spain",           "family": "Indo-European"},
    {"lang": "Romansh",              "status": "Definitely Endangered", "speakers": 40000,  "lat": 46.85,  "lon": 9.53,    "country": "Switzerland",     "family": "Indo-European"},
    {"lang": "Basque",               "status": "Vulnerable",           "speakers": 750000,  "lat": 43.26,  "lon": -2.93,   "country": "Spain / France",  "family": "Isolate"},
    {"lang": "Welsh",                "status": "Vulnerable",           "speakers": 562000,  "lat": 52.13,  "lon": -3.78,   "country": "UK",              "family": "Indo-European"},
    {"lang": "Hadza",                "status": "Vulnerable",           "speakers": 1000,    "lat": -3.75,  "lon": 35.00,   "country": "Tanzania",        "family": "Isolate"},
    {"lang": "Piraha",               "status": "Vulnerable",           "speakers": 800,     "lat": -7.35,  "lon": -61.30,  "country": "Brazil",          "family": "Mura"},
    {"lang": "Xhosa (rural)",        "status": "Vulnerable",           "speakers": 8200000, "lat": -32.99, "lon": 27.90,   "country": "South Africa",    "family": "Niger-Congo"},
    {"lang": "Manx",                 "status": "Extinct (recently)",   "speakers": 0,       "lat": 54.15,  "lon": -4.48,   "country": "Isle of Man",     "family": "Indo-European"},
    {"lang": "Cornish",              "status": "Extinct (recently)",   "speakers": 0,       "lat": 50.27,  "lon": -5.05,   "country": "UK",              "family": "Indo-European"},
    {"lang": "Dalmatian",            "status": "Extinct (recently)",   "speakers": 0,       "lat": 42.64,  "lon": 18.11,   "country": "Croatia",         "family": "Indo-European"},
    {"lang": "Aka-Bo",               "status": "Extinct (recently)",   "speakers": 0,       "lat": 12.50,  "lon": 92.70,   "country": "India (Andaman)", "family": "Great Andamanese"},
    {"lang": "Wichita",              "status": "Extinct (recently)",   "speakers": 0,       "lat": 35.47,  "lon": -97.52,  "country": "USA",             "family": "Caddoan"},
]

# =====================================================================
# 4. WRITING SYSTEMS  (20 scripts)
# =====================================================================
SCRIPT_COLORS = {
    "Latin": "#3b82f6",        "Cyrillic": "#ef4444",
    "Arabic": "#10b981",       "Chinese": "#f59e0b",
    "Devanagari": "#ec4899",   "Bengali / Eastern Nagari": "#8b5cf6",
    "Japanese (mixed)": "#06b6d4", "Korean (Hangul)": "#14b8a6",
    "Thai": "#f97316",         "Georgian": "#a855f7",
    "Armenian": "#22c55e",     "Hebrew": "#eab308",
    "Greek": "#0ea5e9",        "Ethiopic (Ge'ez)": "#d946ef",
    "Tamil": "#fb923c",        "Khmer": "#84cc16",
    "Tibetan": "#64748b",      "Myanmar (Burmese)": "#dc2626",
    "Sinhala": "#7c3aed",      "Lao": "#94a3b8",
}

WRITING_SYSTEMS = [
    {"script": "Latin",                   "countries": "Most of Europe, Americas, Sub-Saharan Africa, Oceania, Turkey", "lat": 48.0, "lon": 2.0,    "pop_pct": 36,  "example": "ABCDEFG"},
    {"script": "Chinese",                 "countries": "China, Taiwan, Singapore (traditional / simplified)",           "lat": 35.0, "lon": 105.0,  "pop_pct": 18,  "example": "\u4e16\u754c\u4f60\u597d"},
    {"script": "Arabic",                  "countries": "Middle East, North Africa, Pakistan, Afghanistan",              "lat": 30.0, "lon": 40.0,   "pop_pct": 10,  "example": "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645"},
    {"script": "Devanagari",              "countries": "India (Hindi, Marathi, Nepali, Sanskrit)",                      "lat": 26.0, "lon": 80.0,   "pop_pct": 9,   "example": "\u0928\u092e\u0938\u094d\u0924\u0947 \u0926\u0941\u0928\u093f\u092f\u093e"},
    {"script": "Cyrillic",               "countries": "Russia, Ukraine, Serbia, Bulgaria, Central Asia",               "lat": 56.0, "lon": 40.0,   "pop_pct": 5,   "example": "\u041f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440"},
    {"script": "Bengali / Eastern Nagari", "countries": "Bangladesh, India (West Bengal, Assam)",                       "lat": 24.0, "lon": 90.0,   "pop_pct": 4,   "example": "\u09a8\u09ae\u09b8\u09cd\u0995\u09be\u09b0"},
    {"script": "Japanese (mixed)",        "countries": "Japan (Kanji + Hiragana + Katakana)",                           "lat": 36.0, "lon": 138.0,  "pop_pct": 2,   "example": "\u3053\u3093\u306b\u3061\u306f\u4e16\u754c"},
    {"script": "Korean (Hangul)",         "countries": "South Korea, North Korea",                                     "lat": 37.0, "lon": 127.5,  "pop_pct": 1.2, "example": "\uc548\ub155\ud558\uc138\uc694"},
    {"script": "Thai",                    "countries": "Thailand",                                                     "lat": 14.0, "lon": 100.5,  "pop_pct": 1,   "example": "\u0e2a\u0e27\u0e31\u0e2a\u0e14\u0e35\u0e0a\u0e32\u0e27\u0e42\u0e25\u0e01"},
    {"script": "Georgian",               "countries": "Georgia",                                                       "lat": 42.0, "lon": 43.8,   "pop_pct": 0.05, "example": "\u10d2\u10d0\u10db\u10d0\u10e0\u10ef\u10dd\u10d1\u10d0"},
    {"script": "Armenian",               "countries": "Armenia",                                                       "lat": 40.2, "lon": 44.5,   "pop_pct": 0.05, "example": "\u0532\u0561\u0580\u0565\u057e"},
    {"script": "Hebrew",                 "countries": "Israel",                                                        "lat": 31.8, "lon": 35.2,   "pop_pct": 0.15, "example": "\u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd"},
    {"script": "Greek",                  "countries": "Greece, Cyprus",                                                "lat": 39.0, "lon": 22.0,   "pop_pct": 0.15, "example": "\u0393\u03b5\u03b9\u03b1 \u03c3\u03bf\u03c5 \u039a\u03cc\u03c3\u03bc\u03b5"},
    {"script": "Ethiopic (Ge'ez)",       "countries": "Ethiopia, Eritrea",                                             "lat": 9.0,  "lon": 39.0,   "pop_pct": 1.5, "example": "\u1230\u120b\u121d \u12d3\u1208\u121d"},
    {"script": "Tamil",                  "countries": "India (Tamil Nadu), Sri Lanka, Singapore",                       "lat": 11.0, "lon": 79.0,   "pop_pct": 1.1, "example": "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd"},
    {"script": "Khmer",                  "countries": "Cambodia",                                                      "lat": 12.6, "lon": 105.0,  "pop_pct": 0.2, "example": "\u179f\u17bd\u179f\u17d2\u178f\u17b8"},
    {"script": "Tibetan",               "countries": "Tibet (China), Bhutan, India",                                   "lat": 30.0, "lon": 91.0,   "pop_pct": 0.08, "example": "\u0f56\u0f40\u0fb2\u0f0b\u0f64\u0f72\u0f66"},
    {"script": "Myanmar (Burmese)",      "countries": "Myanmar",                                                       "lat": 19.8, "lon": 96.2,   "pop_pct": 0.7, "example": "\u1019\u1002\u1064\u101c\u102c\u1015\u102c"},
    {"script": "Sinhala",               "countries": "Sri Lanka",                                                      "lat": 7.0,  "lon": 80.0,   "pop_pct": 0.3, "example": "\u0d86\u0dba\u0dd4\u0db6\u0ddc\u0dc0\u0db1\u0dca"},
    {"script": "Lao",                    "countries": "Laos",                                                          "lat": 18.0, "lon": 103.0,  "pop_pct": 0.1, "example": "\u0eaa\u0eb0\u0e9a\u0eb2\u0e8d\u0e94\u0eb5"},
]

# =====================================================================
# 5. LANGUAGE ISOLATES  (17 entries)
# =====================================================================
ISOLATE_COLOR = "#e879f9"

LANGUAGE_ISOLATES = [
    {"lang": "Basque (Euskara)", "speakers": 750000,   "lat": 43.26, "lon": -2.93,   "country": "Spain / France",       "note": "Pre-Indo-European survival in Pyrenees; no known relatives"},
    {"lang": "Korean",           "speakers": 80000000, "lat": 37.57, "lon": 126.98,  "country": "South / North Korea",  "note": "Sometimes classified Koreanic; debated relation to Japonic"},
    {"lang": "Ainu",             "speakers": 10,       "lat": 43.06, "lon": 141.35,  "country": "Japan (Hokkaido)",     "note": "Indigenous to northern Japan; critically endangered"},
    {"lang": "Burushaski",       "speakers": 100000,   "lat": 36.32, "lon": 74.66,   "country": "Pakistan (Hunza)",     "note": "Spoken in mountainous Karakoram; no accepted relatives"},
    {"lang": "Zuni",             "speakers": 9500,     "lat": 35.07, "lon": -108.85, "country": "USA (New Mexico)",     "note": "Pueblo people; resisted classification attempts"},
    {"lang": "Kusunda",          "speakers": 3,        "lat": 28.25, "lon": 84.00,   "country": "Nepal",                "note": "Nearly extinct; discovered to be isolate in 2004"},
    {"lang": "Hadza",            "speakers": 1000,     "lat": -3.75, "lon": 35.00,   "country": "Tanzania",             "note": "Click language of hunter-gatherers near Lake Eyasi"},
    {"lang": "Sandawe",          "speakers": 60000,    "lat": -5.50, "lon": 35.50,   "country": "Tanzania",             "note": "Click language; debated Khoisan link"},
    {"lang": "Piraha",           "speakers": 800,      "lat": -7.35, "lon": -61.30,  "country": "Brazil",               "note": "Only living Mura language; famously simple phoneme inventory"},
    {"lang": "Sumerian",         "speakers": 0,        "lat": 31.32, "lon": 45.64,   "country": "Iraq (historical)",    "note": "First written language; no known relatives; extinct ~2000 BCE"},
    {"lang": "Nihali",           "speakers": 2000,     "lat": 21.40, "lon": 75.90,   "country": "India (Maharashtra)",  "note": "Spoken by the Nahali people; heavily influenced by neighbors"},
    {"lang": "Ket",              "speakers": 210,      "lat": 63.92, "lon": 87.60,   "country": "Russia (Siberia)",     "note": "Last surviving Yeniseian; linked to Na-Dene hypothesis"},
    {"lang": "Mapudungun",       "speakers": 260000,   "lat": -38.74, "lon": -72.60, "country": "Chile / Argentina",    "note": "Mapuche people language; debated isolate status"},
    {"lang": "Elamite",          "speakers": 0,        "lat": 32.19, "lon": 48.26,   "country": "Iran (historical)",    "note": "Ancient Elam civilization; extinct ~300 BCE"},
    {"lang": "Nivkh",            "speakers": 200,      "lat": 52.95, "lon": 141.71,  "country": "Russia (Sakhalin)",    "note": "Paleosiberian language of Sakhalin and Amur River"},
    {"lang": "Yuchi",            "speakers": 4,        "lat": 35.95, "lon": -96.00,  "country": "USA (Oklahoma)",       "note": "Southeast US indigenous language; critically endangered"},
    {"lang": "Natchez",          "speakers": 0,        "lat": 31.56, "lon": -91.40,  "country": "USA (Mississippi)",    "note": "Mound Builder culture language; extinct since 1957"},
]

# =====================================================================
# 6. SIGN LANGUAGES  (28 entries)
# =====================================================================
SIGN_FAMILY_COLORS = {
    "French Sign Language family": "#3b82f6",
    "British Sign Language family": "#10b981",
    "Swedish Sign Language family": "#8b5cf6",
    "Japanese Sign Language family": "#ef4444",
    "Arab Sign Language family": "#f59e0b",
    "Indo-Pakistani SL family": "#ec4899",
    "Chinese Sign Language family": "#f97316",
    "German Sign Language family": "#06b6d4",
    "Indigenous / Isolate": "#a855f7",
    "Other": "#64748b",
}

SIGN_LANGUAGES = [
    {"name": "American Sign Language (ASL)",     "family": "French Sign Language family",   "lat": 38.90, "lon": -77.04, "country": "USA, Canada",           "users": 500000},
    {"name": "French Sign Language (LSF)",       "family": "French Sign Language family",   "lat": 48.86, "lon": 2.35,   "country": "France",                "users": 100000},
    {"name": "Brazilian Sign Language (Libras)", "family": "French Sign Language family",   "lat": -15.79, "lon": -47.88, "country": "Brazil",               "users": 5000000},
    {"name": "Irish Sign Language (ISL)",        "family": "French Sign Language family",   "lat": 53.35, "lon": -6.26,  "country": "Ireland",               "users": 5000},
    {"name": "Russian Sign Language (RSL)",      "family": "French Sign Language family",   "lat": 55.75, "lon": 37.62,  "country": "Russia",                "users": 120000},
    {"name": "Dutch Sign Language (NGT)",        "family": "French Sign Language family",   "lat": 52.37, "lon": 4.90,   "country": "Netherlands",           "users": 17500},
    {"name": "Mexican Sign Language (LSM)",      "family": "French Sign Language family",   "lat": 19.43, "lon": -99.13, "country": "Mexico",                "users": 400000},
    {"name": "British Sign Language (BSL)",      "family": "British Sign Language family",  "lat": 51.51, "lon": -0.13,  "country": "UK",                    "users": 150000},
    {"name": "Auslan (Australian SL)",           "family": "British Sign Language family",  "lat": -33.87, "lon": 151.21, "country": "Australia",            "users": 20000},
    {"name": "New Zealand Sign Language",        "family": "British Sign Language family",  "lat": -41.29, "lon": 174.78, "country": "New Zealand",          "users": 24000},
    {"name": "South African Sign Language",      "family": "British Sign Language family",  "lat": -33.93, "lon": 18.42, "country": "South Africa",          "users": 600000},
    {"name": "Swedish Sign Language (SSL)",      "family": "Swedish Sign Language family",  "lat": 59.33, "lon": 18.07,  "country": "Sweden",                "users": 30000},
    {"name": "Finnish Sign Language",            "family": "Swedish Sign Language family",  "lat": 60.17, "lon": 24.94,  "country": "Finland",               "users": 5000},
    {"name": "Portuguese Sign Language (LGP)",   "family": "Swedish Sign Language family",  "lat": 38.72, "lon": -9.14,  "country": "Portugal",              "users": 15000},
    {"name": "Japanese Sign Language (JSL)",     "family": "Japanese Sign Language family", "lat": 35.68, "lon": 139.69, "country": "Japan",                 "users": 320000},
    {"name": "Korean Sign Language (KSL)",       "family": "Japanese Sign Language family", "lat": 37.57, "lon": 126.98, "country": "South Korea",           "users": 200000},
    {"name": "Taiwanese Sign Language",          "family": "Japanese Sign Language family", "lat": 25.03, "lon": 121.57, "country": "Taiwan",                "users": 50000},
    {"name": "Arab Sign Language",               "family": "Arab Sign Language family",     "lat": 24.71, "lon": 46.68,  "country": "Saudi Arabia, others",  "users": 100000},
    {"name": "Jordanian Sign Language",          "family": "Arab Sign Language family",     "lat": 31.95, "lon": 35.93,  "country": "Jordan",                "users": 30000},
    {"name": "Indo-Pakistani Sign Language",     "family": "Indo-Pakistani SL family",      "lat": 28.61, "lon": 77.21,  "country": "India, Pakistan",       "users": 6000000},
    {"name": "Nepali Sign Language",             "family": "Indo-Pakistani SL family",      "lat": 27.72, "lon": 85.32,  "country": "Nepal",                 "users": 100000},
    {"name": "Chinese Sign Language (CSL)",      "family": "Chinese Sign Language family",  "lat": 39.91, "lon": 116.40, "country": "China",                 "users": 20000000},
    {"name": "German Sign Language (DGS)",       "family": "German Sign Language family",   "lat": 52.52, "lon": 13.41,  "country": "Germany",               "users": 200000},
    {"name": "Austrian Sign Language",           "family": "German Sign Language family",   "lat": 48.21, "lon": 16.37,  "country": "Austria",               "users": 10000},
    {"name": "Turkish Sign Language (TID)",      "family": "Other",                         "lat": 39.93, "lon": 32.85,  "country": "Turkey",                "users": 350000},
    {"name": "Plains Indian Sign Language",      "family": "Indigenous / Isolate",          "lat": 43.00, "lon": -103.00, "country": "USA / Canada",         "users": 50},
    {"name": "Kata Kolok (Balinese village SL)", "family": "Indigenous / Isolate",          "lat": -8.31, "lon": 115.40, "country": "Indonesia",             "users": 2000},
    {"name": "Al-Sayyid Bedouin SL",            "family": "Indigenous / Isolate",           "lat": 31.15, "lon": 34.80,  "country": "Israel",                "users": 150},
]

# =====================================================================
# 8. CREOLE & PIDGIN LANGUAGES  (25 entries)
# =====================================================================
CREOLE_BASE_COLORS = {
    "English-based": "#3b82f6",   "French-based": "#8b5cf6",
    "Portuguese-based": "#10b981", "Spanish-based": "#f59e0b",
    "Dutch-based": "#f97316",      "Arabic-based": "#ef4444",
    "Malay-based": "#ec4899",      "Mixed": "#06b6d4",
}

CREOLE_LANGUAGES = [
    {"lang": "Haitian Creole",        "base": "French-based",     "speakers": 12000000,  "lat": 18.54,  "lon": -72.34,  "country": "Haiti",                    "note": "Largest French creole; official language"},
    {"lang": "Jamaican Patois",       "base": "English-based",    "speakers": 3200000,   "lat": 18.11,  "lon": -77.30,  "country": "Jamaica",                  "note": "English-lexified Atlantic creole"},
    {"lang": "Tok Pisin",             "base": "English-based",    "speakers": 4000000,   "lat": -6.21,  "lon": 155.55,  "country": "Papua New Guinea",         "note": "Official language of PNG; English-based pidgin"},
    {"lang": "Bislama",               "base": "English-based",    "speakers": 10000,     "lat": -17.73, "lon": 168.32,  "country": "Vanuatu",                  "note": "National language; Pacific English pidgin"},
    {"lang": "Cape Verdean Creole",   "base": "Portuguese-based", "speakers": 900000,    "lat": 14.93,  "lon": -23.51,  "country": "Cape Verde",               "note": "Nine distinct dialects across islands"},
    {"lang": "Papiamento",            "base": "Mixed",            "speakers": 330000,    "lat": 12.17,  "lon": -68.98,  "country": "Curacao, Aruba, Bonaire",  "note": "Portuguese / Spanish / Dutch mix"},
    {"lang": "Sranan Tongo",          "base": "English-based",    "speakers": 500000,    "lat": 5.82,   "lon": -55.17,  "country": "Suriname",                 "note": "English-based lingua franca of Suriname"},
    {"lang": "Seychellois Creole",    "base": "French-based",     "speakers": 73000,     "lat": -4.68,  "lon": 55.49,   "country": "Seychelles",               "note": "French-based; co-official with English and French"},
    {"lang": "Mauritian Creole",      "base": "French-based",     "speakers": 1200000,   "lat": -20.16, "lon": 57.50,   "country": "Mauritius",                "note": "Spoken by most of the population"},
    {"lang": "Louisiana Creole",      "base": "French-based",     "speakers": 10000,     "lat": 30.45,  "lon": -91.19,  "country": "USA (Louisiana)",          "note": "French creole of Louisiana; endangered"},
    {"lang": "Chavacano",             "base": "Spanish-based",    "speakers": 700000,    "lat": 6.91,   "lon": 122.07,  "country": "Philippines",              "note": "Only Spanish-based creole in Asia"},
    {"lang": "Guinea-Bissau Creole",  "base": "Portuguese-based", "speakers": 600000,    "lat": 11.86,  "lon": -15.60,  "country": "Guinea-Bissau",            "note": "Main lingua franca of the country"},
    {"lang": "Sango",                 "base": "Mixed",            "speakers": 5000000,   "lat": 4.37,   "lon": 18.56,   "country": "Central African Republic", "note": "Ngbandi-based with French influence; national lang"},
    {"lang": "Krio",                  "base": "English-based",    "speakers": 4000000,   "lat": 8.48,   "lon": -13.23,  "country": "Sierra Leone",             "note": "English-based; lingua franca of Sierra Leone"},
    {"lang": "Nigerian Pidgin English", "base": "English-based",  "speakers": 75000000,  "lat": 6.52,   "lon": 3.38,    "country": "Nigeria",                  "note": "Largest pidgin / creole by speakers"},
    {"lang": "Cameroon Pidgin English", "base": "English-based",  "speakers": 5000000,   "lat": 4.05,   "lon": 9.70,    "country": "Cameroon",                 "note": "English-based pidgin lingua franca"},
    {"lang": "Reunionese Creole",     "base": "French-based",     "speakers": 600000,    "lat": -21.12, "lon": 55.53,   "country": "Reunion",                  "note": "French-based creole of Reunion Island"},
    {"lang": "Torres Strait Creole",  "base": "English-based",    "speakers": 25000,     "lat": -10.58, "lon": 142.22,  "country": "Australia",                "note": "English-based creole of Torres Strait Islands"},
    {"lang": "Afrikaans",             "base": "Dutch-based",      "speakers": 7200000,   "lat": -33.93, "lon": 18.42,   "country": "South Africa",             "note": "Often classified as creole or semi-creole from Dutch"},
    {"lang": "Nubi",                  "base": "Arabic-based",     "speakers": 50000,     "lat": 0.35,   "lon": 32.62,   "country": "Uganda / Kenya",           "note": "Arabic-based creole of East Africa"},
    {"lang": "Juba Arabic",           "base": "Arabic-based",     "speakers": 800000,    "lat": 4.85,   "lon": 31.58,   "country": "South Sudan",              "note": "Arabic-based pidgin / creole; lingua franca"},
    {"lang": "Baba Malay",            "base": "Malay-based",      "speakers": 10000,     "lat": 2.20,   "lon": 102.25,  "country": "Malaysia / Singapore",     "note": "Peranakan Malay creole; declining"},
    {"lang": "Chabacano de Cavite",   "base": "Spanish-based",    "speakers": 30000,     "lat": 14.48,  "lon": 120.90,  "country": "Philippines",              "note": "Older Spanish creole variety"},
    {"lang": "Betawi",                "base": "Malay-based",      "speakers": 2700000,   "lat": -6.21,  "lon": 106.85,  "country": "Indonesia",                "note": "Malay-based creole of Jakarta"},
    {"lang": "Saramaccan",            "base": "English-based",    "speakers": 58000,     "lat": 4.00,   "lon": -55.50,  "country": "Suriname",                 "note": "English / Portuguese-based maroon creole"},
]

# =====================================================================
# 9. ANCIENT & DEAD LANGUAGES  (22 entries)
# =====================================================================
ERA_COLORS = {
    "Bronze Age": "#f59e0b",
    "Iron Age": "#ef4444",
    "Classical": "#3b82f6",
    "Medieval": "#8b5cf6",
    "Early Modern": "#10b981",
    "Modern (recently extinct)": "#64748b",
}

ANCIENT_LANGUAGES = [
    {"lang": "Sumerian",               "era": "Bronze Age", "years": "4100-2000 BCE",                      "lat": 31.32, "lon": 45.64,  "region": "Mesopotamia (Iraq)",        "note": "First written language; cuneiform; isolate"},
    {"lang": "Akkadian",               "era": "Bronze Age", "years": "2800 BCE - 100 CE",                  "lat": 33.31, "lon": 44.37,  "region": "Mesopotamia (Iraq)",        "note": "Lingua franca of ancient Near East; cuneiform"},
    {"lang": "Ancient Egyptian",       "era": "Bronze Age", "years": "3400 BCE - 600 CE",                  "lat": 29.98, "lon": 31.13,  "region": "Egypt",                     "note": "Hieroglyphic, hieratic, demotic scripts; evolved into Coptic"},
    {"lang": "Hittite",                "era": "Bronze Age", "years": "1600-1178 BCE",                      "lat": 40.02, "lon": 34.61,  "region": "Anatolia (Turkey)",         "note": "Earliest attested Indo-European language; cuneiform"},
    {"lang": "Proto-Indo-European",    "era": "Bronze Age", "years": "~4500-2500 BCE",                     "lat": 46.0,  "lon": 38.0,   "region": "Pontic-Caspian Steppe",     "note": "Reconstructed ancestor of Indo-European family"},
    {"lang": "Sanskrit",               "era": "Iron Age",   "years": "1500 BCE - present (liturgical)",    "lat": 27.18, "lon": 78.02,  "region": "South Asia",                "note": "Sacred language of Hinduism; Devanagari script"},
    {"lang": "Classical Latin",        "era": "Classical",  "years": "75 BCE - 200 CE",                    "lat": 41.90, "lon": 12.50,  "region": "Roman Empire",              "note": "Evolved into Romance languages; scholarly use ongoing"},
    {"lang": "Ancient Greek",          "era": "Classical",  "years": "800-300 BCE",                        "lat": 37.97, "lon": 23.73,  "region": "Greece / Mediterranean",    "note": "Language of Homer, Plato, Aristotle"},
    {"lang": "Classical Chinese",      "era": "Classical",  "years": "500 BCE - 1919 CE",                  "lat": 34.26, "lon": 108.94, "region": "China",                     "note": "Literary standard for 2000+ years; used across East Asia"},
    {"lang": "Old Persian",            "era": "Iron Age",   "years": "525-300 BCE",                        "lat": 30.00, "lon": 52.00,  "region": "Persia (Iran)",             "note": "Achaemenid Empire; cuneiform and Old Persian script"},
    {"lang": "Avestan",                "era": "Iron Age",   "years": "1200-400 BCE",                       "lat": 36.00, "lon": 63.00,  "region": "Central Asia (Afghanistan)", "note": "Sacred language of Zoroastrianism; Avesta texts"},
    {"lang": "Etruscan",               "era": "Iron Age",   "years": "700-100 BCE",                        "lat": 43.30, "lon": 11.30,  "region": "Italy (Tuscany)",           "note": "Pre-Roman Italy; partially deciphered; isolate"},
    {"lang": "Phoenician",             "era": "Iron Age",   "years": "1050-200 BCE",                       "lat": 33.89, "lon": 35.50,  "region": "Lebanon / Mediterranean",   "note": "Origin of most modern alphabets; seafaring traders"},
    {"lang": "Aramaic",                "era": "Iron Age",   "years": "1100 BCE - present (endangered)",    "lat": 37.07, "lon": 41.22,  "region": "Middle East",               "note": "Language of Jesus; Neo-Aramaic still spoken"},
    {"lang": "Old Norse",              "era": "Medieval",   "years": "700-1300 CE",                        "lat": 64.15, "lon": -21.95, "region": "Scandinavia / Iceland",     "note": "Language of Vikings and sagas; runic and Latin scripts"},
    {"lang": "Gothic",                 "era": "Medieval",   "years": "300-800 CE",                         "lat": 44.43, "lon": 26.10,  "region": "Eastern Europe",            "note": "Earliest documented Germanic language; Wulfila Bible"},
    {"lang": "Coptic",                 "era": "Medieval",   "years": "300-1600 CE",                        "lat": 30.05, "lon": 31.23,  "region": "Egypt",                     "note": "Final stage of Egyptian; still used in Coptic Church"},
    {"lang": "Old Church Slavonic",    "era": "Medieval",   "years": "850-1100 CE",                        "lat": 41.99, "lon": 21.43,  "region": "Balkans / Slavic world",    "note": "Created by Cyril and Methodius; Glagolitic / Cyrillic"},
    {"lang": "Tocharian",              "era": "Medieval",   "years": "500-900 CE",                         "lat": 41.73, "lon": 86.15,  "region": "Tarim Basin (China)",       "note": "Easternmost Indo-European; discovered in 20th century"},
    {"lang": "Mayan (Classic)",        "era": "Classical",  "years": "200-900 CE",                         "lat": 17.22, "lon": -89.62, "region": "Mesoamerica",               "note": "Logosyllabic script; deciphered in late 20th century"},
    {"lang": "Old English",            "era": "Medieval",   "years": "450-1100 CE",                        "lat": 51.75, "lon": -1.26,  "region": "England",                   "note": "Anglo-Saxon; Beowulf; evolved into Middle English"},
    {"lang": "Ge'ez",                  "era": "Classical",  "years": "500 BCE - present (liturgical)",     "lat": 13.50, "lon": 39.47,  "region": "Ethiopia / Eritrea",        "note": "Ancient Ethiopian; still used in Orthodox Church"},
]

# =====================================================================
# 10. LINGUISTIC DIVERSITY INDEX  (30 countries)
# =====================================================================
DIVERSITY_INDEX = [
    {"country": "Papua New Guinea", "languages": 840, "lat": -6.31,  "lon": 147.18, "population": 9900000,    "index": 0.99},
    {"country": "Indonesia",        "languages": 710, "lat": -2.55,  "lon": 118.01, "population": 273500000,  "index": 0.81},
    {"country": "Nigeria",          "languages": 525, "lat": 9.08,   "lon": 7.49,   "population": 206000000,  "index": 0.87},
    {"country": "India",            "languages": 456, "lat": 20.59,  "lon": 78.96,  "population": 1400000000, "index": 0.93},
    {"country": "United States",    "languages": 335, "lat": 38.90,  "lon": -77.04, "population": 331000000,  "index": 0.35},
    {"country": "China",            "languages": 305, "lat": 35.86,  "lon": 104.20, "population": 1400000000, "index": 0.51},
    {"country": "Mexico",           "languages": 290, "lat": 23.63,  "lon": -102.55, "population": 128900000, "index": 0.15},
    {"country": "Cameroon",         "languages": 280, "lat": 5.95,   "lon": 10.15,  "population": 26550000,   "index": 0.97},
    {"country": "Australia",        "languages": 260, "lat": -25.27, "lon": 133.78, "population": 25700000,   "index": 0.34},
    {"country": "Brazil",           "languages": 228, "lat": -14.24, "lon": -51.93, "population": 212500000,  "index": 0.07},
    {"country": "DR Congo",         "languages": 215, "lat": -4.04,  "lon": 21.76,  "population": 90000000,   "index": 0.95},
    {"country": "Philippines",      "languages": 185, "lat": 12.88,  "lon": 121.77, "population": 109000000,  "index": 0.84},
    {"country": "Tanzania",         "languages": 127, "lat": -6.37,  "lon": 34.89,  "population": 59700000,   "index": 0.95},
    {"country": "Chad",             "languages": 131, "lat": 15.45,  "lon": 18.73,  "population": 16400000,   "index": 0.95},
    {"country": "Russia",           "languages": 105, "lat": 61.52,  "lon": 105.32, "population": 145900000,  "index": 0.31},
    {"country": "Vanuatu",          "languages": 110, "lat": -15.38, "lon": 166.96, "population": 307000,     "index": 0.98},
    {"country": "Colombia",         "languages": 87,  "lat": 4.57,   "lon": -74.30, "population": 50880000,   "index": 0.04},
    {"country": "Ethiopia",         "languages": 90,  "lat": 9.15,   "lon": 40.49,  "population": 115000000,  "index": 0.87},
    {"country": "Nepal",            "languages": 123, "lat": 28.39,  "lon": 84.12,  "population": 29140000,   "index": 0.83},
    {"country": "Peru",             "languages": 94,  "lat": -9.19,  "lon": -75.02, "population": 32970000,   "index": 0.21},
    {"country": "Malaysia",         "languages": 137, "lat": 4.21,   "lon": 101.98, "population": 32370000,   "index": 0.60},
    {"country": "Myanmar",          "languages": 113, "lat": 21.91,  "lon": 95.96,  "population": 54410000,   "index": 0.52},
    {"country": "Solomon Islands",  "languages": 74,  "lat": -9.43,  "lon": 160.03, "population": 687000,     "index": 0.97},
    {"country": "Kenya",            "languages": 68,  "lat": -0.02,  "lon": 37.91,  "population": 53770000,   "index": 0.89},
    {"country": "Ghana",            "languages": 81,  "lat": 7.95,   "lon": -1.02,  "population": 31070000,   "index": 0.87},
    {"country": "Laos",             "languages": 86,  "lat": 19.86,  "lon": 102.50, "population": 7280000,    "index": 0.64},
    {"country": "South Sudan",      "languages": 72,  "lat": 6.88,   "lon": 31.31,  "population": 11190000,   "index": 0.91},
    {"country": "Japan",            "languages": 15,  "lat": 36.20,  "lon": 138.25, "population": 126000000,  "index": 0.02},
    {"country": "Iceland",          "languages": 2,   "lat": 64.96,  "lon": -19.02, "population": 366000,     "index": 0.01},
    {"country": "North Korea",      "languages": 1,   "lat": 40.34,  "lon": 127.51, "population": 25780000,   "index": 0.00},
]


# =====================================================================
# API FETCH
# =====================================================================

@st.cache_data(ttl=3600)
def _fetch_rest_countries():
    """Fetch country data with official languages from REST Countries API."""
    try:
        resp = requests.get(REST_COUNTRIES_URL, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("REST Countries API error: %s", exc)
        return None


# =====================================================================
# CHART / POPUP HELPERS
# =====================================================================

def _bar_chart(labels, values, title, xlabel, ylabel, colors=None,
               horizontal=False):
    """Create a dark-themed bar chart and return a PNG BytesIO buffer."""
    n = len(labels)
    fig, ax = plt.subplots(figsize=(10, max(5, n * 0.35) if horizontal else 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    if colors is None:
        colors = [ACCENT_COLOR] * n
    if horizontal:
        ax.barh(range(n), values, color=colors, edgecolor="none", height=0.7)
        ax.set_yticks(range(n))
        ax.set_yticklabels(labels, color=TEXT_COLOR, fontsize=9)
        ax.set_xlabel(xlabel, color=TEXT_COLOR, fontsize=10)
        ax.invert_yaxis()
    else:
        ax.bar(range(n), values, color=colors, edgecolor="none", width=0.7)
        ax.set_xticks(range(n))
        ax.set_xticklabels(labels, color=TEXT_COLOR, fontsize=8,
                           rotation=45, ha="right")
        ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=10)
    ax.set_title(title, color=TEXT_COLOR, fontsize=13, fontweight="bold",
                 pad=12)
    ax.tick_params(colors=SECONDARY_COLOR, labelsize=9)
    for sp in ax.spines.values():
        sp.set_color(MUTED_COLOR)
    ax.grid(axis="x" if horizontal else "y", color=MUTED_COLOR,
            alpha=0.2, linestyle="--")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _pie_chart(labels, values, title, colors=None):
    """Create a dark-themed pie chart and return a PNG BytesIO buffer."""
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    if colors is None:
        cmap = plt.cm.get_cmap("tab20", len(labels))
        colors = [cmap(i) for i in range(len(labels))]
    wedges, _texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%", colors=colors,
        pctdistance=0.82, startangle=140,
        wedgeprops={"edgecolor": SURFACE_COLOR, "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_color(TEXT_COLOR)
        t.set_fontsize(8)
    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5),
              fontsize=8, facecolor=SURFACE_COLOR, edgecolor=MUTED_COLOR,
              labelcolor=TEXT_COLOR, framealpha=0.9)
    ax.set_title(title, color=TEXT_COLOR, fontsize=13, fontweight="bold",
                 pad=12)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _popup(title, rows):
    """Build a styled HTML popup with escaped content."""
    hdr = f"<b>{escape(str(title))}</b>"
    body = "<br>".join(
        f"<i>{escape(str(k))}:</i> {escape(str(v))}" for k, v in rows
    )
    return (
        f"<div style='font-family:sans-serif;font-size:12px;min-width:180px;"
        f"color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px;'>"
        f"{hdr}<hr style='border-color:#2a3550;margin:4px 0;'>{body}</div>"
    )


def _legend_html(items):
    """Return inline-legend markdown for a list of (label, color) tuples."""
    parts = " | ".join(
        f"<span style='color:{c}'>\u25cf</span> {escape(str(l))}"
        for l, c in items
    )
    return (
        f"<div style='font-size:12px;color:{SECONDARY_COLOR};'>"
        f"{parts}</div>"
    )


# =====================================================================
# MODE 1 -- World Language Families
# =====================================================================

def _render_language_families():
    st.subheader("World Language Families")
    st.caption(
        "Major language families with representative languages "
        "shown at city locations."
    )
    families = {}
    for item in LANGUAGE_FAMILIES:
        fam = item["family"]
        if fam not in families:
            families[fam] = {"count": 0, "total_speakers": 0}
        families[fam]["count"] += 1
        families[fam]["total_speakers"] += item["speakers"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Language Families", len(families))
    c2.metric("Languages Shown", len(LANGUAGE_FAMILIES))
    tot = sum(f["total_speakers"] for f in families.values())
    c3.metric("Total Speakers", f"{tot:.0f}M")
    c4.metric("Largest Family",
              max(families, key=lambda x: families[x]["total_speakers"]))

    sel = st.multiselect(
        "Filter by family", list(FAMILY_COLORS.keys()),
        default=list(FAMILY_COLORS.keys())[:6],
        help="Select which language families to display.",
    )

    m = folium.Map(location=[20, 0], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for item in LANGUAGE_FAMILIES:
        if item["family"] not in sel:
            continue
        clr = FAMILY_COLORS.get(item["family"], "#8b97b0")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=max(4, min(18, item["speakers"] ** 0.35)),
            color=clr, fill=True, fill_color=clr, fill_opacity=0.7,
            popup=folium.Popup(
                _popup(item["lang"], [
                    ("Family", item["family"]),
                    ("Speakers", f"{item['speakers']}M"),
                    ("Region", item["region"]),
                ]), max_width=280),
            tooltip=f"{escape(item['lang'])} ({escape(item['family'])})",
        ).add_to(m)

    components.html(m._repr_html_(), height=500)
    st.markdown(
        _legend_html([(f, FAMILY_COLORS[f]) for f in sel if f in FAMILY_COLORS]),
        unsafe_allow_html=True,
    )

    # Chart
    chart_fams = [f for f in sel if f in families]
    if chart_fams:
        buf = _bar_chart(
            chart_fams,
            [families[f]["total_speakers"] for f in chart_fams],
            "Total Speakers by Language Family (millions)",
            "Speakers (M)", "Family",
            [FAMILY_COLORS.get(f, ACCENT_COLOR) for f in chart_fams],
            horizontal=True,
        )
        st.image(buf, use_container_width=False, width=800)

    df = pd.DataFrame(LANGUAGE_FAMILIES)
    df = df[df["family"].isin(sel)].sort_values(
        "speakers", ascending=False
    ).reset_index(drop=True)
    df.columns = ["Family", "Language", "Lat", "Lon", "Speakers (M)", "Region"]
    st.dataframe(df, width="stretch", hide_index=True)
    csv = io.BytesIO()
    df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "language_families.csv", "text/csv")


# =====================================================================
# MODE 2 -- Most Spoken Languages
# =====================================================================

def _render_most_spoken():
    st.subheader("Most Spoken Languages")
    st.caption("Top 30 languages ranked by total speakers "
               "(native + second language).")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Shown", len(TOP_LANGUAGES))
    c2.metric("Top by Native", "Mandarin (920M)")
    c3.metric("Top by Total", "English (1.5B)")
    pct = sum(l["total"] for l in TOP_LANGUAGES) / 8000 * 100
    c4.metric("Coverage", f"{pct:.0f}% of world")

    show = st.radio("Size markers by",
                    ["Total speakers", "Native speakers"], horizontal=True)

    m = folium.Map(location=[20, 0], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for item in TOP_LANGUAGES:
        val = item["total"] if show == "Total speakers" else item["native"]
        radius = max(5, min(22, val ** 0.38))
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius, color=ACCENT_COLOR, fill=True,
            fill_color=ACCENT_COLOR, fill_opacity=0.65, weight=1,
            popup=folium.Popup(
                _popup(item["lang"], [
                    ("Rank", f"#{item['rank']}"),
                    ("Native", f"{item['native']}M"),
                    ("Total", f"{item['total']}M"),
                    ("Countries", item["countries"]),
                ]), max_width=300),
            tooltip=f"#{item['rank']} {escape(item['lang'])} ({val}M)",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Grouped bar chart
    top15 = TOP_LANGUAGES[:15]
    labels = [l["lang"] for l in top15]
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    x = range(len(labels))
    ax.bar([i - 0.17 for i in x], [l["total"] for l in top15], 0.34,
           label="Total", color=ACCENT_COLOR, edgecolor="none")
    ax.bar([i + 0.17 for i in x], [l["native"] for l in top15], 0.34,
           label="Native", color="#8b5cf6", edgecolor="none")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, color=TEXT_COLOR, fontsize=8,
                       rotation=45, ha="right")
    ax.set_ylabel("Speakers (millions)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Top 15 Languages: Total vs Native Speakers",
                 color=TEXT_COLOR, fontsize=13, fontweight="bold")
    ax.legend(facecolor=SURFACE_COLOR, edgecolor=MUTED_COLOR,
              labelcolor=TEXT_COLOR)
    ax.tick_params(colors=SECONDARY_COLOR)
    for sp in ax.spines.values():
        sp.set_color(MUTED_COLOR)
    ax.grid(axis="y", color=MUTED_COLOR, alpha=0.2, linestyle="--")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    st.image(buf, use_container_width=False, width=900)

    df = pd.DataFrame(TOP_LANGUAGES)
    df.columns = ["Rank", "Language", "Native (M)", "Total (M)",
                  "Lat", "Lon", "Countries"]
    st.dataframe(
        df[["Rank", "Language", "Native (M)", "Total (M)", "Countries"]],
        width="stretch", hide_index=True,
    )
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "most_spoken_languages.csv", "text/csv")


# =====================================================================
# MODE 3 -- Endangered Languages
# =====================================================================

def _render_endangered():
    st.subheader("Endangered Languages")
    st.caption("Languages at risk, inspired by the UNESCO Atlas of "
               "the World's Languages in Danger.")
    sc = {}
    for la in ENDANGERED_LANGUAGES:
        sc[la["status"]] = sc.get(la["status"], 0) + 1
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Mapped", len(ENDANGERED_LANGUAGES))
    c2.metric("Critically Endangered", sc.get("Critically Endangered", 0))
    c3.metric("Severely Endangered", sc.get("Severely Endangered", 0))
    c4.metric("Recently Extinct", sc.get("Extinct (recently)", 0))

    filt = st.multiselect("Filter by status",
                          list(ENDANGERMENT_COLORS.keys()),
                          default=list(ENDANGERMENT_COLORS.keys()))

    m = folium.Map(location=[20, 0], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for la in ENDANGERED_LANGUAGES:
        if la["status"] not in filt:
            continue
        clr = ENDANGERMENT_COLORS.get(la["status"], "#8b97b0")
        spk = la["speakers"]
        spk_s = f"{spk:,}" if spk > 0 else "Extinct"
        ico = "times" if spk == 0 else "exclamation-triangle"
        folium.Marker(
            location=[la["lat"], la["lon"]],
            popup=folium.Popup(
                _popup(la["lang"], [
                    ("Status", la["status"]), ("Speakers", spk_s),
                    ("Country", la["country"]), ("Family", la["family"]),
                ]), max_width=280),
            tooltip=f"{escape(la['lang'])} - {escape(la['status'])}",
            icon=folium.Icon(
                color="red" if spk == 0 else "orange",
                icon=ico, prefix="fa"),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)
    st.markdown(
        _legend_html(list(ENDANGERMENT_COLORS.items())),
        unsafe_allow_html=True,
    )

    buf = _pie_chart(list(sc.keys()), list(sc.values()),
                     "Endangered Languages by Status",
                     [ENDANGERMENT_COLORS.get(s, ACCENT_COLOR) for s in sc])
    st.image(buf, use_container_width=False, width=600)

    df = pd.DataFrame(ENDANGERED_LANGUAGES)
    df = df[df["status"].isin(filt)].sort_values("speakers").reset_index(
        drop=True)
    df.columns = ["Language", "Status", "Speakers", "Lat", "Lon",
                  "Country", "Family"]
    st.dataframe(df[["Language", "Status", "Speakers", "Country", "Family"]],
                 width="stretch", hide_index=True)
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "endangered_languages.csv", "text/csv")


# =====================================================================
# MODE 4 -- Writing Systems
# =====================================================================

def _render_writing_systems():
    st.subheader("Writing Systems of the World")
    st.caption("Major scripts and their geographic distribution with "
               "example text.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scripts Shown", len(WRITING_SYSTEMS))
    c2.metric("Most Widespread", "Latin (36%)")
    c3.metric("Oldest Active", "Chinese (~3200 yrs)")
    c4.metric("Newest Major", "Hangul (1443 CE)")

    m = folium.Map(location=[20, 30], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for ws in WRITING_SYSTEMS:
        clr = SCRIPT_COLORS.get(ws["script"], "#8b97b0")
        r = max(6, min(25, ws["pop_pct"] ** 0.6 * 4))
        folium.CircleMarker(
            location=[ws["lat"], ws["lon"]],
            radius=r, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(
                _popup(ws["script"], [
                    ("Countries", ws["countries"]),
                    ("World Pop %", f"{ws['pop_pct']}%"),
                    ("Example", ws["example"]),
                ]), max_width=320),
            tooltip=f"{escape(ws['script'])} ({ws['pop_pct']}%)",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)
    st.markdown(
        _legend_html(list(SCRIPT_COLORS.items())),
        unsafe_allow_html=True,
    )

    buf = _bar_chart(
        [ws["script"] for ws in WRITING_SYSTEMS],
        [ws["pop_pct"] for ws in WRITING_SYSTEMS],
        "Writing Systems by World Population %",
        "Population %", "Script",
        [SCRIPT_COLORS.get(ws["script"], ACCENT_COLOR)
         for ws in WRITING_SYSTEMS],
        horizontal=True,
    )
    st.image(buf, use_container_width=False, width=800)

    st.markdown("#### Script Examples")
    cols = st.columns(4)
    for i, ws in enumerate(WRITING_SYSTEMS):
        with cols[i % 4]:
            st.markdown(
                f"<div style='background:{SURFACE_COLOR};padding:8px;"
                f"border-radius:6px;border:1px solid #2a3550;"
                f"margin-bottom:8px;text-align:center;'>"
                f"<div style='font-size:18px;color:{TEXT_COLOR};'>"
                f"{escape(ws['example'])}</div>"
                f"<div style='font-size:11px;color:{SECONDARY_COLOR};'>"
                f"{escape(ws['script'])}</div></div>",
                unsafe_allow_html=True,
            )

    df = pd.DataFrame(WRITING_SYSTEMS)
    df.columns = ["Script", "Countries", "Lat", "Lon", "World Pop %",
                  "Example"]
    df = df.sort_values("World Pop %", ascending=False).reset_index(drop=True)
    st.dataframe(df[["Script", "Countries", "World Pop %", "Example"]],
                 width="stretch", hide_index=True)
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "writing_systems.csv", "text/csv")


# =====================================================================
# MODE 5 -- Language Isolates
# =====================================================================

def _render_language_isolates():
    st.subheader("Language Isolates")
    st.caption("Languages with no demonstrable genetic relationship "
               "to any other language.")
    living = [l for l in LANGUAGE_ISOLATES if l["speakers"] > 0]
    extinct = [l for l in LANGUAGE_ISOLATES if l["speakers"] == 0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Isolates Mapped", len(LANGUAGE_ISOLATES))
    c2.metric("Living", len(living))
    c3.metric("Extinct / Historical", len(extinct))
    c4.metric("Largest", "Korean (80M)")

    m = folium.Map(location=[20, 0], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for item in LANGUAGE_ISOLATES:
        spk = item["speakers"]
        spk_s = f"{spk:,}" if spk > 0 else "Extinct"
        clr = ISOLATE_COLOR if spk > 0 else "#64748b"
        r = max(5, min(16, (spk ** 0.22) * 1.5)) if spk > 0 else 6
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=r, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.75, weight=2,
            popup=folium.Popup(
                _popup(item["lang"], [
                    ("Speakers", spk_s),
                    ("Country", item["country"]),
                    ("Note", item["note"]),
                ]), max_width=320),
            tooltip=f"{escape(item['lang'])} ({spk_s} speakers)",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    df = pd.DataFrame(LANGUAGE_ISOLATES)
    df.columns = ["Language", "Speakers", "Lat", "Lon", "Country", "Notes"]
    df = df.sort_values("Speakers", ascending=False).reset_index(drop=True)
    st.dataframe(df[["Language", "Speakers", "Country", "Notes"]],
                 width="stretch", hide_index=True)
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "language_isolates.csv", "text/csv")


# =====================================================================
# MODE 6 -- Sign Languages
# =====================================================================

def _render_sign_languages():
    st.subheader("Sign Languages of the World")
    st.caption("Major sign languages and their family relationships.")
    fc = {}
    for sl in SIGN_LANGUAGES:
        fc[sl["family"]] = fc.get(sl["family"], 0) + 1
    total_users = sum(sl["users"] for sl in SIGN_LANGUAGES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sign Languages", len(SIGN_LANGUAGES))
    c2.metric("SL Families", len(fc))
    c3.metric("Total Users", f"{total_users / 1e6:.1f}M")
    c4.metric("Largest SL", "Chinese SL (20M)")

    filt = st.multiselect("Filter by SL family",
                          list(SIGN_FAMILY_COLORS.keys()),
                          default=list(SIGN_FAMILY_COLORS.keys()))

    m = folium.Map(location=[20, 0], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for sl in SIGN_LANGUAGES:
        if sl["family"] not in filt:
            continue
        clr = SIGN_FAMILY_COLORS.get(sl["family"], "#8b97b0")
        r = max(5, min(18, (sl["users"] ** 0.25) * 1.2))
        folium.CircleMarker(
            location=[sl["lat"], sl["lon"]],
            radius=r, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(
                _popup(sl["name"], [
                    ("Family", sl["family"]),
                    ("Country", sl["country"]),
                    ("Users", f"{sl['users']:,}"),
                ]), max_width=300),
            tooltip=f"{escape(sl['name'])} ({sl['users']:,} users)",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)
    st.markdown(
        _legend_html([(f, c) for f, c in SIGN_FAMILY_COLORS.items()
                      if f in filt]),
        unsafe_allow_html=True,
    )

    buf = _pie_chart(list(fc.keys()), list(fc.values()),
                     "Sign Languages by Family",
                     [SIGN_FAMILY_COLORS.get(f, ACCENT_COLOR) for f in fc])
    st.image(buf, use_container_width=False, width=600)

    df = pd.DataFrame(SIGN_LANGUAGES)
    df = df[df["family"].isin(filt)]
    df.columns = ["Name", "Family", "Lat", "Lon", "Country", "Users"]
    df = df.sort_values("Users", ascending=False).reset_index(drop=True)
    st.dataframe(df[["Name", "Family", "Country", "Users"]],
                 width="stretch", hide_index=True)
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "sign_languages.csv", "text/csv")


# =====================================================================
# MODE 7 -- Official Languages by Country  (REST Countries API)
# =====================================================================

def _render_official_languages():
    st.subheader("Official Languages by Country")
    st.caption("Official / national languages from the REST Countries API, "
               "color-coded by primary language.")
    data = _fetch_rest_countries()
    if data is None:
        st.error("Failed to fetch data from REST Countries API. "
                 "Please try again later.")
        return

    rows = []
    for c in data:
        name = c.get("name", {}).get("common", "Unknown")
        langs = c.get("languages", {})
        ll = c.get("latlng", [0, 0])
        pop = c.get("population", 0)
        if not langs or len(ll) < 2:
            continue
        primary = list(langs.values())[0]
        rows.append({
            "country": name, "primary_lang": primary,
            "all_languages": ", ".join(langs.values()),
            "num_official": len(langs),
            "lat": ll[0], "lon": ll[1], "population": pop,
        })
    if not rows:
        st.warning("No country data available.")
        return
    df = pd.DataFrame(rows)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Unique Official Langs", df["primary_lang"].nunique())
    most = df["primary_lang"].value_counts().idxmax()
    c3.metric("Most Common Official", most)
    c4.metric("Multilingual Countries",
              len(df[df["num_official"] > 1]))

    top_langs = df["primary_lang"].value_counts().head(15).index.tolist()
    palette = [
        "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
        "#ec4899", "#f97316", "#06b6d4", "#14b8a6", "#a855f7",
        "#22c55e", "#eab308", "#0ea5e9", "#d946ef", "#fb923c",
    ]
    lcm = {lang: palette[i % len(palette)]
           for i, lang in enumerate(top_langs)}

    m = folium.Map(location=[20, 0], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        clr = lcm.get(row["primary_lang"], "#64748b")
        r = max(4, min(14, (row["population"] ** 0.18) * 0.9))
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=r, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=1,
            popup=folium.Popup(
                _popup(row["country"], [
                    ("Primary Language", row["primary_lang"]),
                    ("All Official", row["all_languages"]),
                    ("# Official", str(row["num_official"])),
                    ("Population", f"{row['population']:,}"),
                ]), max_width=320),
            tooltip=(f"{escape(row['country'])}: "
                     f"{escape(row['primary_lang'])}"),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)
    st.markdown(
        _legend_html([(l, lcm[l]) for l in top_langs]) +
        f" | <span style='color:#64748b'>\u25cf</span> Others",
        unsafe_allow_html=True,
    )

    tlc = df["primary_lang"].value_counts().head(15)
    buf = _bar_chart(
        tlc.index.tolist(), tlc.values.tolist(),
        "Most Common Official Languages (by country count)",
        "Countries", "Language",
        [lcm.get(l, ACCENT_COLOR) for l in tlc.index],
        horizontal=True,
    )
    st.image(buf, use_container_width=False, width=800)

    disp = df[["country", "primary_lang", "all_languages",
               "num_official", "population"]]
    disp = disp.sort_values("population", ascending=False).reset_index(
        drop=True)
    disp.columns = ["Country", "Primary Language",
                    "All Official Languages", "# Official", "Population"]
    st.dataframe(disp, width="stretch", hide_index=True)
    csv = io.BytesIO(); disp.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "official_languages.csv", "text/csv")


# =====================================================================
# MODE 8 -- Creole & Pidgin Languages
# =====================================================================

def _render_creoles():
    st.subheader("Creole & Pidgin Languages")
    st.caption("Languages born from contact between communities, "
               "with their lexifier base origins.")
    bc = {}
    for cl in CREOLE_LANGUAGES:
        bc[cl["base"]] = bc.get(cl["base"], 0) + 1
    total_spk = sum(cl["speakers"] for cl in CREOLE_LANGUAGES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Creoles / Pidgins", len(CREOLE_LANGUAGES))
    c2.metric("Lexifier Bases", len(bc))
    c3.metric("Total Speakers", f"{total_spk / 1e6:.0f}M")
    c4.metric("Largest", "Nigerian Pidgin (75M)")

    filt = st.multiselect("Filter by lexifier base",
                          list(CREOLE_BASE_COLORS.keys()),
                          default=list(CREOLE_BASE_COLORS.keys()))

    m = folium.Map(location=[5, 0], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for cl in CREOLE_LANGUAGES:
        if cl["base"] not in filt:
            continue
        clr = CREOLE_BASE_COLORS.get(cl["base"], "#8b97b0")
        r = max(5, min(16, (cl["speakers"] ** 0.2) * 1.8))
        folium.CircleMarker(
            location=[cl["lat"], cl["lon"]],
            radius=r, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(
                _popup(cl["lang"], [
                    ("Base", cl["base"]),
                    ("Speakers", f"{cl['speakers']:,}"),
                    ("Country", cl["country"]),
                    ("Note", cl["note"]),
                ]), max_width=320),
            tooltip=f"{escape(cl['lang'])} ({cl['speakers']:,})",
        ).add_to(m)
    components.html(m._repr_html_(), height=500)
    st.markdown(
        _legend_html([(b, c) for b, c in CREOLE_BASE_COLORS.items()
                      if b in filt]),
        unsafe_allow_html=True,
    )

    buf = _pie_chart(list(bc.keys()), list(bc.values()),
                     "Creoles by Lexifier Base Language",
                     [CREOLE_BASE_COLORS.get(b, ACCENT_COLOR) for b in bc])
    st.image(buf, use_container_width=False, width=600)

    top15 = sorted(CREOLE_LANGUAGES,
                   key=lambda x: x["speakers"], reverse=True)[:15]
    buf2 = _bar_chart(
        [c["lang"] for c in top15],
        [c["speakers"] / 1e6 for c in top15],
        "Top 15 Creoles / Pidgins by Speakers (millions)",
        "Speakers (M)", "Language",
        [CREOLE_BASE_COLORS.get(c["base"], ACCENT_COLOR) for c in top15],
        horizontal=True,
    )
    st.image(buf2, use_container_width=False, width=800)

    df = pd.DataFrame(CREOLE_LANGUAGES)
    df = df[df["base"].isin(filt)].sort_values(
        "speakers", ascending=False
    ).reset_index(drop=True)
    df.columns = ["Language", "Base", "Speakers", "Lat", "Lon",
                  "Country", "Notes"]
    st.dataframe(df[["Language", "Base", "Speakers", "Country", "Notes"]],
                 width="stretch", hide_index=True)
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "creole_languages.csv", "text/csv")


# =====================================================================
# MODE 9 -- Ancient & Dead Languages
# =====================================================================

def _render_ancient_languages():
    st.subheader("Ancient & Dead Languages")
    st.caption("Historical languages from Bronze Age to modern times, "
               "mapped to their regions of origin.")
    ec = {}
    for al in ANCIENT_LANGUAGES:
        ec[al["era"]] = ec.get(al["era"], 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Mapped", len(ANCIENT_LANGUAGES))
    c2.metric("Historical Eras", len(ec))
    c3.metric("Oldest", "Sumerian (~4100 BCE)")
    c4.metric("Most Recent", "Old English (~1100 CE)")

    filt = st.multiselect("Filter by era", list(ERA_COLORS.keys()),
                          default=list(ERA_COLORS.keys()))

    _era_folium = {
        "Bronze Age": "beige", "Iron Age": "red",
        "Classical": "blue", "Medieval": "purple",
        "Early Modern": "green",
        "Modern (recently extinct)": "gray",
    }
    m = folium.Map(location=[30, 40], zoom_start=3,
                   tiles="CartoDB dark_matter")
    for al in ANCIENT_LANGUAGES:
        if al["era"] not in filt:
            continue
        folium.Marker(
            location=[al["lat"], al["lon"]],
            popup=folium.Popup(
                _popup(al["lang"], [
                    ("Era", al["era"]), ("Period", al["years"]),
                    ("Region", al["region"]), ("Note", al["note"]),
                ]), max_width=350),
            tooltip=f"{escape(al['lang'])} ({escape(al['years'])})",
            icon=folium.Icon(
                color=_era_folium.get(al["era"], "gray"),
                icon="book", prefix="fa"),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)
    st.markdown(
        _legend_html([(e, c) for e, c in ERA_COLORS.items() if e in filt]),
        unsafe_allow_html=True,
    )

    chart_e = [e for e in ERA_COLORS if e in ec]
    buf = _bar_chart(
        chart_e, [ec[e] for e in chart_e],
        "Dead Languages by Historical Era",
        "Languages", "Era",
        [ERA_COLORS[e] for e in chart_e],
    )
    st.image(buf, use_container_width=False, width=700)

    st.markdown("#### Language Timeline")
    sorted_al = sorted(ANCIENT_LANGUAGES, key=lambda x: x["years"])
    for al in sorted_al:
        if al["era"] not in filt:
            continue
        clr = ERA_COLORS.get(al["era"], ACCENT_COLOR)
        st.markdown(
            f"<div style='display:flex;align-items:center;"
            f"margin-bottom:4px;'>"
            f"<span style='color:{clr};font-size:14px;"
            f"margin-right:8px;'>\u25cf</span>"
            f"<span style='color:{TEXT_COLOR};font-weight:bold;"
            f"min-width:180px;'>{escape(al['lang'])}</span>"
            f"<span style='color:{SECONDARY_COLOR};"
            f"min-width:200px;'>{escape(al['years'])}</span>"
            f"<span style='color:{MUTED_COLOR};font-size:12px;'>"
            f"{escape(al['region'])}</span></div>",
            unsafe_allow_html=True,
        )

    df = pd.DataFrame(ANCIENT_LANGUAGES)
    df = df[df["era"].isin(filt)]
    df.columns = ["Language", "Era", "Period", "Lat", "Lon",
                  "Region", "Notes"]
    st.dataframe(
        df[["Language", "Era", "Period", "Region", "Notes"]],
        width="stretch", hide_index=True,
    )
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "ancient_languages.csv", "text/csv")


# =====================================================================
# MODE 10 -- Linguistic Diversity Index
# =====================================================================

def _div_color(idx):
    if idx >= 0.9:
        return "#ef4444"
    if idx >= 0.7:
        return "#f97316"
    if idx >= 0.5:
        return "#f59e0b"
    if idx >= 0.3:
        return "#eab308"
    if idx >= 0.1:
        return "#22c55e"
    return "#3b82f6"


def _render_diversity_index():
    st.subheader("Linguistic Diversity Index")
    st.caption("Countries ranked by number of living languages "
               "and Greenberg's diversity index.")
    sd = sorted(DIVERSITY_INDEX, key=lambda x: x["languages"], reverse=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(DIVERSITY_INDEX))
    c2.metric("Most Diverse",
              f"{sd[0]['country']} ({sd[0]['languages']})")
    c3.metric("Least Diverse",
              f"{sd[-1]['country']} ({sd[-1]['languages']})")
    c4.metric("Total Languages",
              f"{sum(d['languages'] for d in DIVERSITY_INDEX):,}")

    m = folium.Map(location=[10, 20], zoom_start=2,
                   tiles="CartoDB dark_matter")
    for d in DIVERSITY_INDEX:
        clr = _div_color(d["index"])
        r = max(5, min(20, d["languages"] ** 0.35))
        lpm = d["languages"] / max(1, d["population"] / 1e6)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=r, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(
                _popup(d["country"], [
                    ("Living Languages", str(d["languages"])),
                    ("Diversity Index", f"{d['index']:.2f}"),
                    ("Population", f"{d['population']:,}"),
                    ("Langs / Million", f"{lpm:.1f}"),
                ]), max_width=300),
            tooltip=(f"{escape(d['country'])}: {d['languages']} "
                     f"languages (index {d['index']:.2f})"),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    legend_items = [
        ("\u2265 0.9 (Very High)", "#ef4444"),
        ("0.7-0.9 (High)", "#f97316"),
        ("0.5-0.7 (Medium)", "#f59e0b"),
        ("0.3-0.5 (Low-Med)", "#eab308"),
        ("0.1-0.3 (Low)", "#22c55e"),
        ("< 0.1 (Very Low)", "#3b82f6"),
    ]
    st.markdown(_legend_html(legend_items), unsafe_allow_html=True)

    top20 = sd[:20]
    buf = _bar_chart(
        [d["country"] for d in top20],
        [d["languages"] for d in top20],
        "Top 20 Countries by Number of Living Languages",
        "Languages", "Country",
        [_div_color(d["index"]) for d in top20],
        horizontal=True,
    )
    st.image(buf, use_container_width=False, width=800)

    by_idx = sorted(DIVERSITY_INDEX, key=lambda x: x["index"],
                    reverse=True)[:20]
    buf2 = _bar_chart(
        [d["country"] for d in by_idx],
        [d["index"] for d in by_idx],
        "Top 20 Countries by Greenberg Diversity Index",
        "Diversity Index (0-1)", "Country",
        [_div_color(d["index"]) for d in by_idx],
        horizontal=True,
    )
    st.image(buf2, use_container_width=False, width=800)

    df = pd.DataFrame(DIVERSITY_INDEX)
    df = df.sort_values("languages", ascending=False).reset_index(drop=True)
    df.columns = ["Country", "Living Languages", "Lat", "Lon",
                  "Population", "Diversity Index"]
    df["Langs / Million Pop"] = (
        df["Living Languages"] / (df["Population"] / 1e6)
    ).round(1)
    st.dataframe(
        df[["Country", "Living Languages", "Diversity Index",
            "Population", "Langs / Million Pop"]],
        width="stretch", hide_index=True,
    )
    csv = io.BytesIO(); df.to_csv(csv, index=False)
    st.download_button("Download CSV", csv.getvalue(),
                       "linguistic_diversity.csv", "text/csv")


# =====================================================================
# MODE REGISTRY & MAIN ENTRY POINT
# =====================================================================

MAP_MODES = {
    "World Language Families": _render_language_families,
    "Most Spoken Languages": _render_most_spoken,
    "Endangered Languages": _render_endangered,
    "Writing Systems": _render_writing_systems,
    "Language Isolates": _render_language_isolates,
    "Sign Languages": _render_sign_languages,
    "Official Languages by Country": _render_official_languages,
    "Creole & Pidgin Languages": _render_creoles,
    "Ancient & Dead Languages": _render_ancient_languages,
    "Linguistic Diversity Index": _render_diversity_index,
}


def render_linguistic_maps_tab():
    """Main entry point for the Linguistic & Language Maps tab."""
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f5e3\ufe0f Linguistic & Language Maps</h4>'
        '<p>World languages, language families, endangered languages '
        '& scripts</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Select map mode",
        options=list(MAP_MODES.keys()),
        horizontal=False,
        help="Choose which linguistic map to display.",
    )

    st.markdown("---")

    render_fn = MAP_MODES.get(mode)
    if render_fn:
        render_fn()
