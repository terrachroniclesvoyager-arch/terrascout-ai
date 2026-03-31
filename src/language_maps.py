# -*- coding: utf-8 -*-
"""
Languages & Writing Systems Explorer module for TerraScout AI.
Curated linguistic data: language families, endangered languages, scripts,
dialects, and 10 interactive map modes. All data is embedded — no API keys needed.
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
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT = "#06b6d4"

# ═══════════════════════════════════════════════════════════════
# COLOR PALETTES
# ═══════════════════════════════════════════════════════════════
FAMILY_COLORS = {
    "Indo-European": "#06b6d4",
    "Sino-Tibetan": "#ef4444",
    "Afroasiatic": "#f59e0b",
    "Niger-Congo": "#10b981",
    "Austronesian": "#8b5cf6",
    "Dravidian": "#ec4899",
    "Turkic": "#f97316",
    "Japonic": "#3b82f6",
    "Koreanic": "#14b8a6",
    "Uralic": "#a855f7",
    "Tai-Kadai": "#22c55e",
    "Austroasiatic": "#e879f9",
    "Nilo-Saharan": "#facc15",
    "Mongolic": "#fb923c",
    "Tupian": "#4ade80",
    "Quechuan": "#c084fc",
    "Isolate": "#94a3b8",
    "Creole": "#fbbf24",
    "Constructed": "#67e8f9",
    "Other": "#64748b",
}

SCRIPT_COLORS = {
    "Latin": "#06b6d4",
    "Cyrillic": "#ef4444",
    "Arabic": "#10b981",
    "Chinese": "#f59e0b",
    "Devanagari": "#ec4899",
    "Hangul": "#3b82f6",
    "Japanese": "#8b5cf6",
    "Thai": "#22c55e",
    "Georgian": "#f97316",
    "Armenian": "#a855f7",
    "Ethiopic": "#14b8a6",
    "Hebrew": "#e879f9",
    "Greek": "#facc15",
    "Bengali": "#fb923c",
    "Tamil": "#4ade80",
    "Khmer": "#c084fc",
    "Other": "#64748b",
}

# ═══════════════════════════════════════════════════════════════
# 1. MAJOR LANGUAGE FAMILIES
# ═══════════════════════════════════════════════════════════════
LANGUAGE_FAMILIES = [
    {"family": "Indo-European", "languages": 449, "speakers_b": 3.2, "lat": 48.0, "lon": 20.0, "region": "Europe, S/W Asia, Americas", "branches": "Germanic, Romance, Slavic, Indo-Iranian, Celtic, Baltic, Hellenic, Albanian, Armenian", "example": "English, Spanish, Hindi, Russian, Portuguese"},
    {"family": "Sino-Tibetan", "languages": 456, "speakers_b": 1.4, "lat": 35.0, "lon": 105.0, "region": "East & SE Asia", "branches": "Sinitic, Tibeto-Burman", "example": "Mandarin, Cantonese, Burmese, Tibetan"},
    {"family": "Afroasiatic", "languages": 382, "speakers_b": 0.58, "lat": 15.0, "lon": 30.0, "region": "N Africa, Horn of Africa, Middle East", "branches": "Semitic, Berber, Cushitic, Chadic, Omotic, Egyptian", "example": "Arabic, Amharic, Hausa, Hebrew, Somali"},
    {"family": "Niger-Congo", "languages": 1545, "speakers_b": 0.7, "lat": 5.0, "lon": 15.0, "region": "Sub-Saharan Africa", "branches": "Atlantic-Congo, Mande, Kordofanian", "example": "Swahili, Yoruba, Igbo, Zulu, Shona"},
    {"family": "Austronesian", "languages": 1257, "speakers_b": 0.39, "lat": -5.0, "lon": 120.0, "region": "SE Asia, Oceania, Madagascar", "branches": "Malayo-Polynesian, Formosan", "example": "Malay, Tagalog, Javanese, Malagasy, Hawaiian"},
    {"family": "Dravidian", "languages": 80, "speakers_b": 0.28, "lat": 12.0, "lon": 78.0, "region": "South India, Sri Lanka", "branches": "South, Central, North Dravidian", "example": "Tamil, Telugu, Kannada, Malayalam"},
    {"family": "Turkic", "languages": 44, "speakers_b": 0.2, "lat": 42.0, "lon": 55.0, "region": "Central Asia, Turkey, Siberia", "branches": "Oghuz, Kipchak, Karluk, Siberian", "example": "Turkish, Azerbaijani, Uzbek, Kazakh"},
    {"family": "Austroasiatic", "languages": 167, "speakers_b": 0.12, "lat": 15.0, "lon": 105.0, "region": "SE Asia, E India", "branches": "Mon-Khmer, Munda", "example": "Vietnamese, Khmer, Santali, Mundari"},
    {"family": "Tai-Kadai", "languages": 97, "speakers_b": 0.095, "lat": 18.0, "lon": 103.0, "region": "SE Asia, S China", "branches": "Tai, Kadai, Kam-Sui, Hlai", "example": "Thai, Lao, Shan, Zhuang"},
    {"family": "Uralic", "languages": 38, "speakers_b": 0.025, "lat": 62.0, "lon": 40.0, "region": "N Europe, NW Asia", "branches": "Finno-Ugric, Samoyedic", "example": "Finnish, Hungarian, Estonian, Sami"},
    {"family": "Japonic", "languages": 12, "speakers_b": 0.128, "lat": 36.0, "lon": 138.0, "region": "Japan, Ryukyu Islands", "branches": "Japanese, Ryukyuan", "example": "Japanese, Okinawan, Amami"},
    {"family": "Koreanic", "languages": 2, "speakers_b": 0.081, "lat": 37.0, "lon": 127.0, "region": "Korean Peninsula", "branches": "Korean, Jeju", "example": "Korean, Jeju"},
    {"family": "Nilo-Saharan", "languages": 206, "speakers_b": 0.068, "lat": 8.0, "lon": 30.0, "region": "Central & E Africa", "branches": "Eastern Sudanic, Central Sudanic, Saharan", "example": "Luo, Kanuri, Maasai, Dinka, Nuer"},
    {"family": "Mongolic", "languages": 13, "speakers_b": 0.009, "lat": 47.0, "lon": 106.0, "region": "Mongolia, S Siberia, N China", "branches": "Central, Western, Eastern Mongolic", "example": "Khalkha Mongolian, Buryat, Oirat"},
    {"family": "Tupian", "languages": 76, "speakers_b": 0.006, "lat": -10.0, "lon": -55.0, "region": "South America", "branches": "Tupi-Guarani, Monde, Munduruku", "example": "Guarani, Nheengatu, Munduruku"},
    {"family": "Quechuan", "languages": 47, "speakers_b": 0.009, "lat": -13.0, "lon": -72.0, "region": "Andes (Peru, Bolivia, Ecuador)", "branches": "Quechua I, Quechua II", "example": "Southern Quechua, Ancash Quechua"},
]

# ═══════════════════════════════════════════════════════════════
# 2. MOST SPOKEN LANGUAGES (TOP 50)
# ═══════════════════════════════════════════════════════════════
TOP_LANGUAGES = [
    {"language": "English", "family": "Indo-European", "native_m": 380, "total_m": 1452, "lat": 51.5, "lon": -0.1, "countries": 59, "script": "Latin"},
    {"language": "Mandarin Chinese", "family": "Sino-Tibetan", "native_m": 939, "total_m": 1118, "lat": 39.9, "lon": 116.4, "countries": 3, "script": "Chinese"},
    {"language": "Hindi", "family": "Indo-European", "native_m": 345, "total_m": 602, "lat": 28.6, "lon": 77.2, "countries": 4, "script": "Devanagari"},
    {"language": "Spanish", "family": "Indo-European", "native_m": 486, "total_m": 548, "lat": 40.4, "lon": -3.7, "countries": 20, "script": "Latin"},
    {"language": "French", "family": "Indo-European", "native_m": 80, "total_m": 280, "lat": 48.9, "lon": 2.3, "countries": 29, "script": "Latin"},
    {"language": "Standard Arabic", "family": "Afroasiatic", "native_m": 310, "total_m": 274, "lat": 24.7, "lon": 46.7, "countries": 26, "script": "Arabic"},
    {"language": "Bengali", "family": "Indo-European", "native_m": 234, "total_m": 272, "lat": 23.8, "lon": 90.4, "countries": 2, "script": "Bengali"},
    {"language": "Portuguese", "family": "Indo-European", "native_m": 236, "total_m": 257, "lat": 38.7, "lon": -9.1, "countries": 10, "script": "Latin"},
    {"language": "Russian", "family": "Indo-European", "native_m": 148, "total_m": 255, "lat": 55.8, "lon": 37.6, "countries": 4, "script": "Cyrillic"},
    {"language": "Japanese", "family": "Japonic", "native_m": 123, "total_m": 123, "lat": 35.7, "lon": 139.7, "countries": 1, "script": "Japanese"},
    {"language": "Yue Chinese", "family": "Sino-Tibetan", "native_m": 85, "total_m": 85, "lat": 23.1, "lon": 113.3, "countries": 2, "script": "Chinese"},
    {"language": "Vietnamese", "family": "Austroasiatic", "native_m": 85, "total_m": 85, "lat": 21.0, "lon": 105.8, "countries": 1, "script": "Latin"},
    {"language": "Turkish", "family": "Turkic", "native_m": 82, "total_m": 82, "lat": 39.9, "lon": 32.9, "countries": 3, "script": "Latin"},
    {"language": "Wu Chinese", "family": "Sino-Tibetan", "native_m": 82, "total_m": 82, "lat": 31.2, "lon": 121.5, "countries": 1, "script": "Chinese"},
    {"language": "Korean", "family": "Koreanic", "native_m": 81, "total_m": 81, "lat": 37.6, "lon": 127.0, "countries": 2, "script": "Hangul"},
    {"language": "Marathi", "family": "Indo-European", "native_m": 83, "total_m": 83, "lat": 19.1, "lon": 72.9, "countries": 1, "script": "Devanagari"},
    {"language": "Telugu", "family": "Dravidian", "native_m": 83, "total_m": 83, "lat": 17.4, "lon": 78.5, "countries": 1, "script": "Telugu"},
    {"language": "Tamil", "family": "Dravidian", "native_m": 79, "total_m": 79, "lat": 13.1, "lon": 80.3, "countries": 3, "script": "Tamil"},
    {"language": "German", "family": "Indo-European", "native_m": 76, "total_m": 132, "lat": 52.5, "lon": 13.4, "countries": 6, "script": "Latin"},
    {"language": "Urdu", "family": "Indo-European", "native_m": 70, "total_m": 231, "lat": 33.7, "lon": 73.0, "countries": 2, "script": "Arabic"},
    {"language": "Javanese", "family": "Austronesian", "native_m": 68, "total_m": 68, "lat": -7.3, "lon": 110.4, "countries": 1, "script": "Latin"},
    {"language": "Italian", "family": "Indo-European", "native_m": 67, "total_m": 68, "lat": 41.9, "lon": 12.5, "countries": 4, "script": "Latin"},
    {"language": "Egyptian Arabic", "family": "Afroasiatic", "native_m": 64, "total_m": 64, "lat": 30.0, "lon": 31.2, "countries": 1, "script": "Arabic"},
    {"language": "Gujarati", "family": "Indo-European", "native_m": 57, "total_m": 57, "lat": 23.0, "lon": 72.6, "countries": 1, "script": "Gujarati"},
    {"language": "Iranian Persian", "family": "Indo-European", "native_m": 55, "total_m": 77, "lat": 35.7, "lon": 51.4, "countries": 3, "script": "Arabic"},
    {"language": "Bhojpuri", "family": "Indo-European", "native_m": 53, "total_m": 53, "lat": 25.5, "lon": 84.0, "countries": 1, "script": "Devanagari"},
    {"language": "Min Nan Chinese", "family": "Sino-Tibetan", "native_m": 49, "total_m": 49, "lat": 24.5, "lon": 118.1, "countries": 3, "script": "Chinese"},
    {"language": "Hausa", "family": "Afroasiatic", "native_m": 47, "total_m": 77, "lat": 12.0, "lon": 8.5, "countries": 4, "script": "Latin"},
    {"language": "Kannada", "family": "Dravidian", "native_m": 44, "total_m": 44, "lat": 12.97, "lon": 77.56, "countries": 1, "script": "Kannada"},
    {"language": "Filipino/Tagalog", "family": "Austronesian", "native_m": 28, "total_m": 82, "lat": 14.6, "lon": 121.0, "countries": 1, "script": "Latin"},
    {"language": "Polish", "family": "Indo-European", "native_m": 40, "total_m": 45, "lat": 52.2, "lon": 21.0, "countries": 1, "script": "Latin"},
    {"language": "Yoruba", "family": "Niger-Congo", "native_m": 45, "total_m": 45, "lat": 7.4, "lon": 3.9, "countries": 3, "script": "Latin"},
    {"language": "Malayalam", "family": "Dravidian", "native_m": 38, "total_m": 38, "lat": 10.0, "lon": 76.3, "countries": 1, "script": "Malayalam"},
    {"language": "Odia", "family": "Indo-European", "native_m": 35, "total_m": 35, "lat": 20.3, "lon": 85.8, "countries": 1, "script": "Odia"},
    {"language": "Burmese", "family": "Sino-Tibetan", "native_m": 33, "total_m": 43, "lat": 16.9, "lon": 96.2, "countries": 1, "script": "Burmese"},
    {"language": "Swahili", "family": "Niger-Congo", "native_m": 16, "total_m": 98, "lat": -6.8, "lon": 37.0, "countries": 8, "script": "Latin"},
    {"language": "Ukrainian", "family": "Indo-European", "native_m": 33, "total_m": 40, "lat": 50.4, "lon": 30.5, "countries": 2, "script": "Cyrillic"},
    {"language": "Sundanese", "family": "Austronesian", "native_m": 36, "total_m": 36, "lat": -6.9, "lon": 107.6, "countries": 1, "script": "Latin"},
    {"language": "Punjabi", "family": "Indo-European", "native_m": 113, "total_m": 113, "lat": 31.5, "lon": 74.3, "countries": 2, "script": "Gurmukhi"},
    {"language": "Romanian", "family": "Indo-European", "native_m": 26, "total_m": 28, "lat": 44.4, "lon": 26.1, "countries": 2, "script": "Latin"},
    {"language": "Dutch", "family": "Indo-European", "native_m": 25, "total_m": 30, "lat": 52.4, "lon": 4.9, "countries": 3, "script": "Latin"},
    {"language": "Thai", "family": "Tai-Kadai", "native_m": 21, "total_m": 61, "lat": 13.8, "lon": 100.5, "countries": 1, "script": "Thai"},
    {"language": "Amharic", "family": "Afroasiatic", "native_m": 32, "total_m": 57, "lat": 9.0, "lon": 38.7, "countries": 1, "script": "Ethiopic"},
    {"language": "Igbo", "family": "Niger-Congo", "native_m": 31, "total_m": 31, "lat": 6.4, "lon": 7.5, "countries": 1, "script": "Latin"},
    {"language": "Malay", "family": "Austronesian", "native_m": 77, "total_m": 77, "lat": 3.1, "lon": 101.7, "countries": 4, "script": "Latin"},
    {"language": "Uzbek", "family": "Turkic", "native_m": 34, "total_m": 34, "lat": 41.3, "lon": 69.3, "countries": 3, "script": "Latin"},
    {"language": "Nepali", "family": "Indo-European", "native_m": 16, "total_m": 32, "lat": 27.7, "lon": 85.3, "countries": 2, "script": "Devanagari"},
    {"language": "Cebuano", "family": "Austronesian", "native_m": 27, "total_m": 27, "lat": 10.3, "lon": 123.9, "countries": 1, "script": "Latin"},
    {"language": "Zulu", "family": "Niger-Congo", "native_m": 28, "total_m": 28, "lat": -29.9, "lon": 31.0, "countries": 1, "script": "Latin"},
    {"language": "Sinhala", "family": "Indo-European", "native_m": 17, "total_m": 17, "lat": 6.9, "lon": 79.9, "countries": 1, "script": "Sinhala"},
]

# ═══════════════════════════════════════════════════════════════
# 3. ENDANGERED LANGUAGES
# ═══════════════════════════════════════════════════════════════
ENDANGERED_LANGUAGES = [
    {"language": "Ainu", "status": "Critically Endangered", "speakers": 10, "region": "Hokkaido, Japan", "family": "Isolate", "lat": 43.06, "lon": 141.35, "note": "UNESCO critically endangered; elder speakers only"},
    {"language": "Yaghan / Yamana", "status": "Critically Endangered", "speakers": 1, "region": "Tierra del Fuego, Chile", "family": "Isolate", "lat": -54.93, "lon": -67.61, "note": "Last speaker: Cristina Calderon (d. 2022)"},
    {"language": "Njerep", "status": "Critically Endangered", "speakers": 4, "region": "Cameroon", "family": "Niger-Congo", "lat": 6.9, "lon": 11.1, "note": "Bantoid language, vanishing with elders"},
    {"language": "Tanema", "status": "Critically Endangered", "speakers": 1, "region": "Vanikoro, Solomon Islands", "family": "Austronesian", "lat": -11.67, "lon": 166.87, "note": "Single known speaker on Vanikoro island"},
    {"language": "Liki", "status": "Critically Endangered", "speakers": 11, "region": "Papua, Indonesia", "family": "Austronesian", "lat": -1.62, "lon": 138.12, "note": "Spoken on small island in Sarmi district"},
    {"language": "Chulym", "status": "Critically Endangered", "speakers": 44, "region": "Siberia, Russia", "family": "Turkic", "lat": 56.3, "lon": 88.3, "note": "Along the Chulym River, elders only"},
    {"language": "Kaixana", "status": "Critically Endangered", "speakers": 1, "region": "Amazonas, Brazil", "family": "Isolate", "lat": -3.4, "lon": -65.1, "note": "One remaining speaker near Japura River"},
    {"language": "Ongota", "status": "Critically Endangered", "speakers": 12, "region": "Ethiopia", "family": "Afroasiatic", "lat": 5.3, "lon": 36.5, "note": "12 elders in a single village near Weyt'o River"},
    {"language": "Livonian", "status": "Critically Endangered", "speakers": 20, "region": "Latvia", "family": "Uralic", "lat": 57.6, "lon": 22.1, "note": "Baltic-Finnic, last native speakers aged 80+"},
    {"language": "Dumi", "status": "Critically Endangered", "speakers": 8, "region": "Nepal", "family": "Sino-Tibetan", "lat": 27.5, "lon": 86.7, "note": "Kiranti language of eastern Nepal"},
    {"language": "Seke", "status": "Critically Endangered", "speakers": 700, "region": "Nepal", "family": "Sino-Tibetan", "lat": 28.8, "lon": 83.8, "note": "Spoken in five villages of Mustang district"},
    {"language": "Apalachee", "status": "Extinct (2000s)", "speakers": 0, "region": "Florida/Louisiana, USA", "family": "Muskogean", "lat": 30.4, "lon": -84.3, "note": "Last speakers in Louisiana in early 2000s"},
    {"language": "Eyak", "status": "Extinct (2008)", "speakers": 0, "region": "Alaska, USA", "family": "Na-Dene", "lat": 60.5, "lon": -145.5, "note": "Last speaker Marie Smith Jones died 2008"},
    {"language": "Ubykh", "status": "Extinct (1992)", "speakers": 0, "region": "Turkey (originally Caucasus)", "family": "NW Caucasian", "lat": 40.2, "lon": 29.0, "note": "Last speaker Tevfik Esenc died 1992; 84 consonants"},
    {"language": "Siletz Dee-ni", "status": "Critically Endangered", "speakers": 1, "region": "Oregon, USA", "family": "Na-Dene", "lat": 44.7, "lon": -123.9, "note": "Athabaskan language; revitalization programs active"},
    {"language": "Ter Sami", "status": "Critically Endangered", "speakers": 10, "region": "Kola Peninsula, Russia", "family": "Uralic", "lat": 68.0, "lon": 35.5, "note": "Easternmost Sami language"},
    {"language": "Picard", "status": "Severely Endangered", "speakers": 500000, "region": "N France, Belgium", "family": "Indo-European", "lat": 49.9, "lon": 2.3, "note": "Oïl language, declining speakers, UNESCO-listed"},
    {"language": "Navajo", "status": "Vulnerable", "speakers": 170000, "region": "Arizona/New Mexico, USA", "family": "Na-Dene", "lat": 36.1, "lon": -109.5, "note": "Largest Native American language; code talkers in WWII"},
    {"language": "Irish (Gaeilge)", "status": "Vulnerable", "speakers": 75000, "region": "Ireland", "family": "Indo-European", "lat": 53.3, "lon": -9.0, "note": "Native speakers in Gaeltacht areas only"},
    {"language": "Hawaiian", "status": "Critically Endangered", "speakers": 2000, "region": "Hawaii, USA", "family": "Austronesian", "lat": 20.8, "lon": -156.3, "note": "Revived via immersion schools since 1980s"},
    {"language": "Manx", "status": "Revived", "speakers": 1800, "region": "Isle of Man", "family": "Indo-European", "lat": 54.2, "lon": -4.5, "note": "Died 1974, revived; now ~100 fluent L2 speakers"},
    {"language": "Breton", "status": "Severely Endangered", "speakers": 210000, "region": "Brittany, France", "family": "Indo-European", "lat": 48.1, "lon": -3.0, "note": "Celtic language; Diwan immersion schools"},
    {"language": "Scots Gaelic", "status": "Endangered", "speakers": 57000, "region": "Scotland", "family": "Indo-European", "lat": 57.5, "lon": -6.3, "note": "Strongest in Outer Hebrides"},
    {"language": "Michif", "status": "Critically Endangered", "speakers": 50, "region": "Canada (Manitoba, Saskatchewan)", "family": "Mixed (Cree-French)", "lat": 51.5, "lon": -100.0, "note": "Metis mixed language; French nouns + Cree verbs"},
    {"language": "Taa (ǃXoon)", "status": "Endangered", "speakers": 2500, "region": "Botswana, Namibia", "family": "Tuu", "lat": -23.4, "lon": 21.7, "note": "Most phonemes of any language (~164 consonants)"},
    {"language": "Yuchi", "status": "Critically Endangered", "speakers": 4, "region": "Oklahoma, USA", "family": "Isolate", "lat": 35.9, "lon": -96.1, "note": "Language isolate; tribal revitalization program"},
    {"language": "Karelian", "status": "Endangered", "speakers": 36000, "region": "Russia / Finland border", "family": "Uralic", "lat": 63.0, "lon": 33.0, "note": "Finnic language closely related to Finnish"},
    {"language": "Warlpiri", "status": "Vulnerable", "speakers": 2600, "region": "Northern Territory, Australia", "family": "Pama-Nyungan", "lat": -20.0, "lon": 131.5, "note": "One of healthiest Australian Aboriginal languages"},
    {"language": "Koro (Arunachal)", "status": "Endangered", "speakers": 1500, "region": "Arunachal Pradesh, India", "family": "Sino-Tibetan", "lat": 27.5, "lon": 93.0, "note": "Discovered by linguists in 2010"},
    {"language": "N|uu", "status": "Critically Endangered", "speakers": 3, "region": "Northern Cape, South Africa", "family": "Tuu", "lat": -28.5, "lon": 20.5, "note": "Click language; last speakers are elderly women"},
]

# ═══════════════════════════════════════════════════════════════
# 4. WRITING SYSTEMS
# ═══════════════════════════════════════════════════════════════
WRITING_SYSTEMS = [
    {"script": "Latin", "type": "Alphabet", "languages_using": 1000, "users_b": 4.9, "origin": "Rome, ~700 BCE", "lat": 41.9, "lon": 12.5, "direction": "LTR", "example": "A B C D E", "regions": "Europe, Americas, Africa, Oceania, SE Asia"},
    {"script": "Chinese (Hanzi)", "type": "Logographic", "languages_using": 6, "users_b": 1.4, "origin": "China, ~1200 BCE (Oracle bone)", "lat": 34.3, "lon": 108.9, "direction": "LTR/Vertical", "example": "\u4e2d\u6587\u5b57", "regions": "China, Taiwan, Singapore"},
    {"script": "Arabic", "type": "Abjad", "languages_using": 25, "users_b": 0.67, "origin": "Arabian Peninsula, ~400 CE", "lat": 24.5, "lon": 39.6, "direction": "RTL", "example": "\u0627\u0644\u0639\u0631\u0628\u064a\u0629", "regions": "Middle East, N Africa, Central/South Asia"},
    {"script": "Devanagari", "type": "Abugida", "languages_using": 120, "users_b": 0.61, "origin": "India, ~700 CE", "lat": 26.8, "lon": 81.0, "direction": "LTR", "example": "\u0926\u0947\u0935\u0928\u093e\u0917\u0930\u0940", "regions": "India (Hindi, Sanskrit, Marathi, Nepali)"},
    {"script": "Cyrillic", "type": "Alphabet", "languages_using": 50, "users_b": 0.25, "origin": "Bulgaria, ~940 CE", "lat": 42.7, "lon": 23.3, "direction": "LTR", "example": "\u0410\u0411\u0412\u0413\u0414", "regions": "Russia, Eastern Europe, Central Asia"},
    {"script": "Hangul", "type": "Featural Alphabet", "languages_using": 1, "users_b": 0.081, "origin": "Korea, 1443 CE (King Sejong)", "lat": 37.6, "lon": 127.0, "direction": "LTR", "example": "\ud55c\uad00\uc5b4", "regions": "South Korea, North Korea"},
    {"script": "Bengali", "type": "Abugida", "languages_using": 3, "users_b": 0.27, "origin": "Bengal region, ~1000 CE", "lat": 23.8, "lon": 90.4, "direction": "LTR", "example": "\u09ac\u09be\u0982\u09b2\u09be", "regions": "Bangladesh, eastern India (West Bengal)"},
    {"script": "Japanese (Kanji+Kana)", "type": "Mixed", "languages_using": 1, "users_b": 0.128, "origin": "Japan, ~800 CE (Kana)", "lat": 35.7, "lon": 139.7, "direction": "LTR/Vertical", "example": "\u65e5\u672c\u8a9e \u3072\u3089\u304c\u306a", "regions": "Japan"},
    {"script": "Thai", "type": "Abugida", "languages_using": 3, "users_b": 0.038, "origin": "Thailand, 1283 CE (Ram Khamhaeng)", "lat": 13.8, "lon": 100.5, "direction": "LTR", "example": "\u0e44\u0e17\u0e22", "regions": "Thailand"},
    {"script": "Georgian", "type": "Alphabet", "languages_using": 1, "users_b": 0.004, "origin": "Georgia, ~430 CE", "lat": 41.7, "lon": 44.8, "direction": "LTR", "example": "\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8", "regions": "Georgia"},
    {"script": "Armenian", "type": "Alphabet", "languages_using": 1, "users_b": 0.006, "origin": "Armenia, 405 CE (Mesrop Mashtots)", "lat": 40.2, "lon": 44.5, "direction": "LTR", "example": "\u0540\u0561\u0575\u0565\u0580\u0565\u0576", "regions": "Armenia, diaspora communities"},
    {"script": "Ethiopic (Ge'ez)", "type": "Abugida", "languages_using": 18, "users_b": 0.1, "origin": "Eritrea/Ethiopia, ~500 BCE", "lat": 9.0, "lon": 38.7, "direction": "LTR", "example": "\u12a0\u121b\u122d\u129b", "regions": "Ethiopia, Eritrea"},
    {"script": "Hebrew", "type": "Abjad", "languages_using": 3, "users_b": 0.014, "origin": "Levant, ~800 BCE", "lat": 31.8, "lon": 35.2, "direction": "RTL", "example": "\u05e2\u05d1\u05e8\u05d9\u05ea", "regions": "Israel, Jewish diaspora"},
    {"script": "Greek", "type": "Alphabet", "languages_using": 1, "users_b": 0.013, "origin": "Greece, ~800 BCE", "lat": 37.97, "lon": 23.72, "direction": "LTR", "example": "\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac", "regions": "Greece, Cyprus"},
    {"script": "Tamil", "type": "Abugida", "languages_using": 2, "users_b": 0.079, "origin": "South India, ~300 BCE", "lat": 13.1, "lon": 80.3, "direction": "LTR", "example": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", "regions": "Tamil Nadu (India), Sri Lanka, Singapore"},
    {"script": "Khmer", "type": "Abugida", "languages_using": 1, "users_b": 0.016, "origin": "Cambodia, ~611 CE", "lat": 11.6, "lon": 104.9, "direction": "LTR", "example": "\u1797\u17b6\u179f\u17b6\u1781\u17d2\u1798\u17c2\u179a", "regions": "Cambodia"},
    {"script": "Tibetan", "type": "Abugida", "languages_using": 4, "users_b": 0.005, "origin": "Tibet, ~650 CE", "lat": 29.7, "lon": 91.1, "direction": "LTR", "example": "\u0f56\u0f7c\u0f51\u0f0b\u0f66\u0f90\u0f51\u0f0b", "regions": "Tibet, Bhutan, Nepal, India (Ladakh)"},
    {"script": "Sinhala", "type": "Abugida", "languages_using": 1, "users_b": 0.017, "origin": "Sri Lanka, ~300 BCE", "lat": 6.9, "lon": 79.9, "direction": "LTR", "example": "\u0dc3\u0dd2\u0d82\u0dc4\u0dbd", "regions": "Sri Lanka"},
    {"script": "Mongolian (Vert.)", "type": "Alphabet", "languages_using": 2, "users_b": 0.003, "origin": "Mongolia, ~1204 CE", "lat": 47.9, "lon": 106.9, "direction": "Top-to-bottom", "example": "\u182e\u1823\u1829\u182d\u1823\u182f", "regions": "Inner Mongolia (China)"},
    {"script": "Tifinagh (Berber)", "type": "Abjad", "languages_using": 5, "users_b": 0.015, "origin": "North Africa, ~200 BCE", "lat": 32.0, "lon": -5.0, "direction": "LTR", "example": "\u2d5c\u2d49\u2d3c\u2d49\u2d4f\u2d30\u2d56", "regions": "Morocco, Algeria, Niger, Mali, Libya"},
]

# ═══════════════════════════════════════════════════════════════
# 5. LANGUAGE ISOLATES
# ═══════════════════════════════════════════════════════════════
LANGUAGE_ISOLATES = [
    {"language": "Basque (Euskara)", "speakers": 750000, "region": "Basque Country (Spain/France)", "lat": 43.0, "lon": -2.5, "note": "Pre-Indo-European survival; no known relatives. Ergative-absolutive grammar. Oldest living language isolate in Europe.", "status": "Vulnerable"},
    {"language": "Korean", "speakers": 81000000, "region": "Korean Peninsula", "lat": 37.6, "lon": 127.0, "note": "Often classified as isolate (some link to Koreanic family with Jeju). SOV word order, agglutinative morphology.", "status": "Safe"},
    {"language": "Ainu", "speakers": 10, "region": "Hokkaido, Japan", "lat": 43.06, "lon": 141.35, "note": "Language of indigenous Ainu people. Polysynthetic, SOV order. Nearly extinct; major revival efforts underway.", "status": "Critically Endangered"},
    {"language": "Burushaski", "speakers": 96000, "region": "Hunza & Nagar, Pakistan", "lat": 36.3, "lon": 74.7, "note": "Spoken in Karakoram mountains. Complex four-gender noun class system. No proven relatives.", "status": "Vulnerable"},
    {"language": "Zuni", "speakers": 9500, "region": "New Mexico, USA", "lat": 35.1, "lon": -108.8, "note": "Pueblo people language. Polysynthetic with complex verb morphology. No accepted links to other families.", "status": "Endangered"},
    {"language": "Kusunda", "speakers": 3, "region": "Nepal", "lat": 28.2, "lon": 83.5, "note": "Rediscovered in 2004 after believed extinct. Possibly pre-Himalayan substrate. Only known living speaker studied in 2020.", "status": "Critically Endangered"},
    {"language": "Hadza", "speakers": 1000, "region": "Tanzania (Lake Eyasi)", "lat": -3.8, "lon": 35.0, "note": "Click language. Hunter-gatherer people. Not related to Khoisan despite clicks. One of oldest lineages.", "status": "Endangered"},
    {"language": "Sandawe", "speakers": 60000, "region": "Central Tanzania", "lat": -5.5, "lon": 35.2, "note": "Click language; tentative Khoisan link debated. Tonal with pharyngeal consonants.", "status": "Vulnerable"},
    {"language": "Nihali", "speakers": 2500, "region": "Maharashtra, India", "lat": 21.2, "lon": 75.8, "note": "Spoken by nomadic Nihali people. Heavily influenced by Korku but core vocabulary unrelated.", "status": "Endangered"},
    {"language": "Sumerian", "speakers": 0, "region": "Ancient Mesopotamia (Iraq)", "lat": 31.3, "lon": 45.8, "note": "Extinct ~2000 BCE. First known writing system (cuneiform). Agglutinative, ergative. No related languages ever found.", "status": "Extinct"},
    {"language": "Elamite", "speakers": 0, "region": "Ancient Elam (SW Iran)", "lat": 32.2, "lon": 48.3, "note": "Extinct ~300 BCE. Known from cuneiform tablets. Agglutinative. Used in Achaemenid royal inscriptions.", "status": "Extinct"},
    {"language": "Mapudungun", "speakers": 250000, "region": "Chile & Argentina", "lat": -38.7, "lon": -72.6, "note": "Language of the Mapuche people. Polysynthetic with complex vowel system. Agglutinative.", "status": "Endangered"},
    {"language": "Pirah\u00e3", "speakers": 800, "region": "Amazonas, Brazil", "lat": -7.0, "lon": -62.5, "note": "Famous for alleged lack of recursion, numbers, and color terms. Tonal. Studied extensively by Daniel Everett.", "status": "Endangered"},
    {"language": "Ket", "speakers": 200, "region": "Central Siberia, Russia", "lat": 63.0, "lon": 87.0, "note": "Last surviving Yeniseian language. Linked to Na-Dene (Dene-Yeniseian hypothesis) - possible Beringia connection.", "status": "Critically Endangered"},
    {"language": "Natchez", "speakers": 0, "region": "Mississippi/Oklahoma, USA", "lat": 31.5, "lon": -91.4, "note": "Extinct ~1950s. Language of the Natchez sun-worship civilization. No proven relatives.", "status": "Extinct"},
]

# ═══════════════════════════════════════════════════════════════
# 6. CONSTRUCTED LANGUAGES
# ═══════════════════════════════════════════════════════════════
CONSTRUCTED_LANGUAGES = [
    {"language": "Esperanto", "creator": "L. L. Zamenhof", "year": 1887, "speakers": 2000000, "lat": 53.1, "lon": 23.2, "purpose": "International auxiliary language", "note": "Most successful constructed language. Community in 120+ countries. Native speakers (denaskuloj) exist.", "region": "Warsaw (created), worldwide"},
    {"language": "Klingon (tlhIngan Hol)", "creator": "Marc Okrand", "year": 1984, "speakers": 30, "lat": 34.1, "lon": -118.3, "purpose": "Fictional (Star Trek)", "note": "OVS word order. Klingon Language Institute maintains it. Hamlet translated to Klingon.", "region": "Hollywood origin, global fandom"},
    {"language": "Quenya (Elvish)", "creator": "J.R.R. Tolkien", "year": 1915, "speakers": 0, "lat": 51.75, "lon": -1.25, "purpose": "Fictional (Lord of the Rings)", "note": "Based on Finnish and Latin. Tengwar script. Studied by thousands of enthusiasts.", "region": "Oxford origin, global fandom"},
    {"language": "Sindarin (Elvish)", "creator": "J.R.R. Tolkien", "year": 1930, "speakers": 0, "lat": 51.75, "lon": -1.25, "purpose": "Fictional (Lord of the Rings)", "note": "Based on Welsh phonology. More commonly spoken Elvish in Middle-earth.", "region": "Oxford origin, global fandom"},
    {"language": "Dothraki", "creator": "David J. Peterson", "year": 2009, "speakers": 0, "lat": 34.1, "lon": -118.3, "purpose": "Fictional (Game of Thrones)", "note": "Created for HBO series. ~3,700 words. Growing learner community.", "region": "Hollywood origin, global fandom"},
    {"language": "High Valyrian", "creator": "David J. Peterson", "year": 2013, "speakers": 0, "lat": 34.1, "lon": -118.3, "purpose": "Fictional (Game of Thrones)", "note": "2,000+ words. Available on Duolingo. Highly inflected with 4 genders.", "region": "Hollywood origin, global fandom"},
    {"language": "Volapuk", "creator": "Johann Martin Schleyer", "year": 1879, "speakers": 20, "lat": 47.8, "lon": 10.3, "purpose": "International auxiliary language", "note": "Preceded Esperanto. Once had ~100,000 speakers. Declined rapidly.", "region": "Baden, Germany origin"},
    {"language": "Interlingua", "creator": "IALA (Alexander Gode)", "year": 1951, "speakers": 1500, "lat": 40.7, "lon": -74.0, "purpose": "International auxiliary language", "note": "Based on Romance vocabulary. Designed to be immediately readable by Romance speakers.", "region": "New York origin, Europe"},
    {"language": "Toki Pona", "creator": "Sonja Lang", "year": 2001, "speakers": 4000, "lat": 43.7, "lon": -79.4, "purpose": "Philosophical / minimalist", "note": "Only ~130 root words. Influenced by Taoism. Explores minimal communication.", "region": "Toronto origin, online"},
    {"language": "Lojban", "creator": "Logical Language Group", "year": 1987, "speakers": 200, "lat": 40.7, "lon": -74.0, "purpose": "Logical / research language", "note": "Syntactically unambiguous. Based on predicate logic. Forked from Loglan.", "region": "USA origin, online"},
    {"language": "Ido", "creator": "Louis de Beaufront", "year": 1907, "speakers": 500, "lat": 48.9, "lon": 2.3, "purpose": "International auxiliary language", "note": "Reformed Esperanto. Simpler grammar. Smaller but dedicated community.", "region": "Paris origin, worldwide"},
    {"language": "Blissymbolics", "creator": "Charles K. Bliss", "year": 1949, "speakers": 0, "lat": -33.9, "lon": 151.2, "purpose": "Universal visual language", "note": "Ideographic symbol system. Used in AAC (augmented communication) for disabled persons.", "region": "Sydney origin"},
    {"language": "Na'vi", "creator": "Paul Frommer", "year": 2005, "speakers": 0, "lat": 34.1, "lon": -118.3, "purpose": "Fictional (Avatar)", "note": "Ejective consonants. Tripartite alignment. Active learner community.", "region": "Hollywood origin, global fandom"},
    {"language": "Novial", "creator": "Otto Jespersen", "year": 1928, "speakers": 0, "lat": 55.7, "lon": 12.6, "purpose": "International auxiliary language", "note": "Created by famous Danish linguist. Mixed Romance/Germanic vocabulary.", "region": "Copenhagen origin"},
]

# ═══════════════════════════════════════════════════════════════
# 7. LINGUISTIC DIVERSITY INDEX (countries)
# ═══════════════════════════════════════════════════════════════
LINGUISTIC_DIVERSITY = [
    {"country": "Papua New Guinea", "languages": 840, "population_m": 10.1, "diversity_index": 0.99, "lat": -6.0, "lon": 147.0, "note": "Most linguistically diverse country on Earth. Extreme terrain isolates communities.", "top_langs": "Tok Pisin, Hiri Motu, English (official)"},
    {"country": "Indonesia", "languages": 710, "population_m": 277.5, "diversity_index": 0.81, "lat": -2.0, "lon": 118.0, "note": "17,000 islands create linguistic fragmentation. Bahasa Indonesia unifies.", "top_langs": "Indonesian, Javanese, Sundanese"},
    {"country": "Nigeria", "languages": 524, "population_m": 223.8, "diversity_index": 0.87, "lat": 9.0, "lon": 8.0, "note": "Three major groups: Hausa, Yoruba, Igbo. 520+ minority languages.", "top_langs": "English, Hausa, Yoruba, Igbo"},
    {"country": "India", "languages": 456, "population_m": 1428.6, "diversity_index": 0.93, "lat": 20.5, "lon": 79.0, "note": "22 official languages in constitution. Hindi belt vs. Dravidian south.", "top_langs": "Hindi, Bengali, Telugu, Marathi, Tamil"},
    {"country": "United States", "languages": 337, "population_m": 339.9, "diversity_index": 0.35, "lat": 39.8, "lon": -98.6, "note": "175 indigenous languages, many critically endangered. Spanish 2nd.", "top_langs": "English, Spanish, Chinese, Tagalog"},
    {"country": "Australia", "languages": 312, "population_m": 26.4, "diversity_index": 0.33, "lat": -25.0, "lon": 134.0, "note": "250+ Aboriginal languages before colonization. Most critically endangered.", "top_langs": "English, Mandarin, Arabic, Cantonese"},
    {"country": "China", "languages": 305, "population_m": 1425.9, "diversity_index": 0.51, "lat": 35.0, "lon": 105.0, "note": "Mandarin dominates. 290+ minority languages across 55 ethnic groups.", "top_langs": "Mandarin, Wu, Cantonese, Min"},
    {"country": "Mexico", "languages": 292, "population_m": 128.9, "diversity_index": 0.15, "lat": 23.6, "lon": -102.5, "note": "68 officially recognized indigenous languages. Nahuatl largest.", "top_langs": "Spanish, Nahuatl, Yucatec Maya, Mixtec"},
    {"country": "Cameroon", "languages": 277, "population_m": 28.6, "diversity_index": 0.97, "lat": 6.0, "lon": 12.0, "note": "Called 'Africa in miniature' for linguistic diversity. Bilingual French/English.", "top_langs": "French, English, Fulfulde, Ewondo"},
    {"country": "Brazil", "languages": 228, "population_m": 216.4, "diversity_index": 0.07, "lat": -14.2, "lon": -51.9, "note": "180+ indigenous languages in Amazon. Portuguese dominates (99.7%).", "top_langs": "Portuguese, Ticuna, Kaingang, Guarani"},
    {"country": "Democratic Republic of Congo", "languages": 215, "population_m": 102.3, "diversity_index": 0.95, "lat": -4.0, "lon": 22.0, "note": "4 national languages: Lingala, Swahili, Tshiluba, Kikongo.", "top_langs": "French, Lingala, Swahili, Tshiluba"},
    {"country": "Philippines", "languages": 187, "population_m": 117.3, "diversity_index": 0.84, "lat": 12.9, "lon": 122.0, "note": "7,600 islands. Filipino (Tagalog-based) + English official.", "top_langs": "Filipino, English, Cebuano, Ilocano"},
    {"country": "Tanzania", "languages": 126, "population_m": 65.5, "diversity_index": 0.95, "lat": -6.4, "lon": 34.9, "note": "Swahili as unifying lingua franca. No dominant ethnic group.", "top_langs": "Swahili, English, Sukuma, Chagga"},
    {"country": "Nepal", "languages": 123, "population_m": 30.9, "diversity_index": 0.83, "lat": 28.4, "lon": 84.1, "note": "4 language families converge. Nepali official but 122 others spoken.", "top_langs": "Nepali, Maithili, Bhojpuri, Tamang"},
    {"country": "Vanuatu", "languages": 112, "population_m": 0.33, "diversity_index": 0.99, "lat": -15.4, "lon": 167.0, "note": "Highest language density per capita on Earth. Bislama is lingua franca.", "top_langs": "Bislama, English, French"},
    {"country": "Solomon Islands", "languages": 74, "population_m": 0.72, "diversity_index": 0.97, "lat": -9.4, "lon": 160.0, "note": "Solomon Islands Pijin is common. 70+ distinct Austronesian & Papuan langs.", "top_langs": "Pijin, English, Kwara'ae"},
    {"country": "Chad", "languages": 131, "population_m": 17.7, "diversity_index": 0.96, "lat": 15.4, "lon": 18.7, "note": "3 language families: Afroasiatic, Nilo-Saharan, Niger-Congo. Arabic/French official.", "top_langs": "Arabic, French, Sara, Kanembou"},
    {"country": "Ethiopia", "languages": 92, "population_m": 126.5, "diversity_index": 0.88, "lat": 9.1, "lon": 40.5, "note": "Amharic official. Oromo largest group. Uses Ge'ez script.", "top_langs": "Amharic, Oromo, Tigrinya, Somali"},
    {"country": "Peru", "languages": 104, "population_m": 34.0, "diversity_index": 0.34, "lat": -9.2, "lon": -75.0, "note": "Spanish dominates. Quechua co-official. Amazon hosts dozens of families.", "top_langs": "Spanish, Quechua, Aymara"},
    {"country": "Malaysia", "languages": 140, "population_m": 33.9, "diversity_index": 0.60, "lat": 4.2, "lon": 101.9, "note": "Malay official. Indigenous Orang Asli and Borneo languages.", "top_langs": "Malay, English, Mandarin, Tamil"},
]

# ═══════════════════════════════════════════════════════════════
# 8. OFFICIAL LANGUAGES MAP
# ═══════════════════════════════════════════════════════════════
OFFICIAL_LANGUAGES = [
    {"language": "English", "type": "Official/Co-official", "countries": 59, "un_official": True, "lat": 51.5, "lon": -0.1, "note": "Most widespread official language. Lingua franca of aviation, science, internet.", "regions": "UK, USA, Australia, India, Nigeria, S. Africa, Singapore"},
    {"language": "French", "type": "Official/Co-official", "countries": 29, "un_official": True, "lat": 48.9, "lon": 2.3, "note": "Official in 29 countries (most in Africa). OIF: 88 member states.", "regions": "France, Canada, DRC, Cameroon, Madagascar, Belgium"},
    {"language": "Arabic", "type": "Official/Co-official", "countries": 26, "un_official": True, "lat": 24.7, "lon": 46.7, "note": "Modern Standard Arabic official; local dialects vary hugely. Sacred language of Islam.", "regions": "Saudi Arabia, Egypt, Iraq, Morocco, Algeria"},
    {"language": "Spanish", "type": "Official/Co-official", "countries": 20, "un_official": True, "lat": 40.4, "lon": -3.7, "note": "Official across 20 countries. 2nd most native speakers globally.", "regions": "Spain, Mexico, Colombia, Argentina, Peru, Chile"},
    {"language": "Portuguese", "type": "Official/Co-official", "countries": 10, "un_official": False, "lat": 38.7, "lon": -9.1, "note": "Lusophone world: CPLP community. Brazil has 95% of speakers.", "regions": "Portugal, Brazil, Angola, Mozambique, East Timor"},
    {"language": "Russian", "type": "Official/Co-official", "countries": 4, "un_official": True, "lat": 55.8, "lon": 37.6, "note": "Official in 4 countries. Widely understood across former Soviet states.", "regions": "Russia, Belarus, Kazakhstan, Kyrgyzstan"},
    {"language": "Chinese (Mandarin)", "type": "Official/Co-official", "countries": 3, "un_official": True, "lat": 39.9, "lon": 116.4, "note": "UN official language. Simplified chars in PRC, Traditional in Taiwan/HK.", "regions": "China, Taiwan, Singapore"},
    {"language": "German", "type": "Official/Co-official", "countries": 6, "un_official": False, "lat": 52.5, "lon": 13.4, "note": "EU's most spoken native language. Official in DACH + Luxembourg, Belgium, Liechtenstein.", "regions": "Germany, Austria, Switzerland, Luxembourg"},
    {"language": "Swahili", "type": "Official/Co-official", "countries": 8, "un_official": False, "lat": -6.8, "lon": 37.0, "note": "Bantu lingua franca of East Africa. Proposed as AU official language.", "regions": "Tanzania, Kenya, DRC, Uganda, Rwanda"},
    {"language": "Hindi", "type": "Official/Co-official", "countries": 2, "un_official": False, "lat": 28.6, "lon": 77.2, "note": "Official of India and Fiji (Fiji Hindi). Bollywood drives global spread.", "regions": "India (Hindi belt), Fiji"},
    {"language": "Malay/Indonesian", "type": "Official/Co-official", "countries": 4, "un_official": False, "lat": 3.1, "lon": 101.7, "note": "Bahasa Indonesia/Malaysia are standardized registers of Malay.", "regions": "Indonesia, Malaysia, Brunei, Singapore"},
    {"language": "Dutch", "type": "Official/Co-official", "countries": 6, "un_official": False, "lat": 52.4, "lon": 4.9, "note": "Netherlands, Belgium (Flemish), Suriname, Aruba, Curacao, Sint Maarten.", "regions": "Netherlands, Belgium, Suriname, Caribbean"},
    {"language": "Turkish", "type": "Official/Co-official", "countries": 2, "un_official": False, "lat": 39.9, "lon": 32.9, "note": "Turkey and Cyprus (N. Cyprus). Turkic lingua franca understood across Central Asia.", "regions": "Turkey, Northern Cyprus"},
    {"language": "Italian", "type": "Official/Co-official", "countries": 4, "un_official": False, "lat": 41.9, "lon": 12.5, "note": "Italy, Switzerland, San Marino, Vatican City.", "regions": "Italy, Switzerland, San Marino, Vatican"},
    {"language": "Korean", "type": "Official/Co-official", "countries": 2, "un_official": False, "lat": 37.6, "lon": 127.0, "note": "North and South Korea. Growing global interest via K-pop and hallyu.", "regions": "South Korea, North Korea"},
    {"language": "Japanese", "type": "Official", "countries": 1, "un_official": False, "lat": 35.7, "lon": 139.7, "note": "Official in Japan only. SOV word order. Honorific system (keigo).", "regions": "Japan"},
    {"language": "Quechua", "type": "Co-official", "countries": 3, "un_official": False, "lat": -13.5, "lon": -72.0, "note": "Official in Peru, Bolivia, Ecuador. Language of Inca Empire.", "regions": "Peru, Bolivia, Ecuador"},
    {"language": "Guarani", "type": "Co-official", "countries": 2, "un_official": False, "lat": -25.3, "lon": -57.6, "note": "Co-official in Paraguay and Bolivia. Rare: indigenous lang. with majority speakers.", "regions": "Paraguay, Bolivia"},
]

# ═══════════════════════════════════════════════════════════════
# 9. DEAD / HISTORICAL LANGUAGES
# ═══════════════════════════════════════════════════════════════
DEAD_LANGUAGES = [
    {"language": "Latin", "family": "Indo-European", "era": "~700 BCE - 600 CE", "died": "~600 CE (spoken)", "lat": 41.9, "lon": 12.5, "legacy": "Ancestor of Romance languages. Vatican still uses Ecclesiastical Latin. Scientific nomenclature.", "center": "Rome, Italy", "influence": "Spanish, French, Italian, Portuguese, Romanian, English (60% vocabulary)"},
    {"language": "Ancient Greek", "family": "Indo-European", "era": "~1500 BCE - 300 CE", "died": "~600 CE (Koine)", "lat": 37.97, "lon": 23.72, "legacy": "Philosophy, democracy, theater, science vocabulary. New Testament written in Koine Greek.", "center": "Athens, Greece", "influence": "Modern Greek, scientific terminology, English vocabulary"},
    {"language": "Sanskrit", "family": "Indo-European", "era": "~1500 BCE - 600 CE", "died": "~600 CE (vernacular)", "lat": 26.8, "lon": 81.0, "legacy": "Sacred language of Hinduism. Oldest Vedic texts (~1500 BCE). Still used liturgically.", "center": "Gangetic Plain, India", "influence": "Hindi, Bengali, Marathi, Nepali, Thai, Khmer (vocabulary)"},
    {"language": "Ancient Egyptian", "family": "Afroasiatic", "era": "~3100 BCE - 600 CE", "died": "~700 CE", "lat": 25.7, "lon": 32.6, "legacy": "Hieroglyphic, Hieratic, Demotic scripts. Rosetta Stone decoded by Champollion (1822).", "center": "Thebes (Luxor), Egypt", "influence": "Coptic (liturgical descendant), loanwords in Arabic, Greek"},
    {"language": "Sumerian", "family": "Isolate", "era": "~3100 BCE - 2000 BCE", "died": "~2000 BCE", "lat": 31.3, "lon": 45.8, "legacy": "First known writing (cuneiform). Invented schools, mathematics, codified law.", "center": "Ur / Uruk, Mesopotamia", "influence": "Akkadian loanwords, Babylonian literature, base-60 time system"},
    {"language": "Akkadian", "family": "Afroasiatic", "era": "~2500 BCE - 100 CE", "died": "~100 CE", "lat": 32.5, "lon": 44.4, "legacy": "Lingua franca of ancient Near East. Epic of Gilgamesh. Used cuneiform.", "center": "Babylon, Mesopotamia", "influence": "Assyrian, Babylonian, Hebrew, Aramaic (loanwords)"},
    {"language": "Old Norse", "family": "Indo-European", "era": "~700 CE - 1300 CE", "died": "~1300 CE", "lat": 64.1, "lon": -21.9, "legacy": "Viking saga language. Elder & Younger Edda. Runic inscriptions.", "center": "Scandinavia / Iceland", "influence": "Norwegian, Swedish, Danish, Icelandic, English (skull, saga, berserk)"},
    {"language": "Classical Arabic", "family": "Afroasiatic", "era": "~500 CE - present (liturgical)", "died": "~900 CE (spoken form)", "lat": 21.4, "lon": 39.8, "legacy": "Language of the Quran. Still used in formal/written contexts as MSA base.", "center": "Mecca, Arabian Peninsula", "influence": "All Arabic dialects, Persian, Turkish, Urdu, Malay, Swahili"},
    {"language": "Aramaic", "family": "Afroasiatic", "era": "~1100 BCE - present (small)", "died": "Mostly replaced by Arabic ~700 CE", "lat": 33.5, "lon": 36.3, "legacy": "Lingua franca of Persian Empire. Language of Jesus Christ. Talmud written in Aramaic.", "center": "Damascus / Mesopotamia", "influence": "Hebrew script, Arabic loanwords, Syriac liturgy"},
    {"language": "Coptic", "family": "Afroasiatic", "era": "~100 CE - 1600 CE", "died": "~1600 CE (spoken)", "lat": 30.0, "lon": 31.2, "legacy": "Last stage of Egyptian language. Coptic Church still uses liturgically. Greek alphabet.", "center": "Alexandria, Egypt", "influence": "Coptic liturgy, Egyptian Arabic substrate vocabulary"},
    {"language": "Gothic", "family": "Indo-European", "era": "~350 CE - 800 CE", "died": "~800 CE", "lat": 46.0, "lon": 25.0, "legacy": "Oldest well-attested Germanic language. Wulfila's Bible translation (350 CE).", "center": "Dacia (Romania) / Crimea", "influence": "Comparative Germanic linguistics, Spanish vocabulary (guerra=war)"},
    {"language": "Etruscan", "family": "Isolate", "era": "~700 BCE - 100 CE", "died": "~100 CE", "lat": 43.0, "lon": 11.5, "legacy": "Pre-Roman Italian civilization. Influenced Roman culture, religion, architecture.", "center": "Tuscany, Italy", "influence": "Latin (many loanwords including 'Roma'), Roman numerals may be Etruscan"},
    {"language": "Old English", "family": "Indo-European", "era": "~450 CE - 1100 CE", "died": "~1100 CE (evolved to Middle English)", "lat": 51.5, "lon": -1.5, "legacy": "Beowulf. Anglo-Saxon culture. Germanic grammar with 4 cases.", "center": "Wessex / England", "influence": "Modern English core vocabulary (water, house, be, have, go)"},
    {"language": "Hittite", "family": "Indo-European", "era": "~1600 BCE - 1180 BCE", "died": "~1180 BCE", "lat": 40.0, "lon": 34.6, "legacy": "Oldest attested Indo-European language. Deciphered 1915 by Hrozny.", "center": "Hattusa (Bogazkoy), Anatolia", "influence": "Indo-European linguistics (confirmed laryngeal theory)"},
    {"language": "Phoenician", "family": "Afroasiatic", "era": "~1050 BCE - 300 CE", "died": "~300 CE (Punic lasted to ~600 CE)", "lat": 33.9, "lon": 35.5, "legacy": "Invented the alphabet (~1050 BCE). Spread by maritime trade across Mediterranean.", "center": "Byblos / Tyre, Lebanon", "influence": "Greek, Latin, Arabic, Hebrew alphabets all descend from Phoenician"},
]

# ═══════════════════════════════════════════════════════════════
# 10. PIDGINS & CREOLES
# ═══════════════════════════════════════════════════════════════
PIDGINS_CREOLES = [
    {"language": "Tok Pisin", "type": "Creole", "base": "English", "speakers": 4000000, "lat": -6.0, "lon": 147.0, "country": "Papua New Guinea", "note": "National language of PNG. English-lexified. 'Tok Pisin' = 'talk pidgin'. Used in parliament.", "example": "Mi no save = I don't know"},
    {"language": "Haitian Creole", "type": "Creole", "base": "French", "speakers": 12000000, "lat": 18.5, "lon": -72.3, "country": "Haiti", "note": "Spoken by virtually all Haitians. French-lexified with West African grammar. Co-official.", "example": "Mwen renmen ou = I love you"},
    {"language": "Papiamento", "type": "Creole", "base": "Portuguese/Spanish", "speakers": 330000, "lat": 12.2, "lon": -68.9, "country": "Curacao, Aruba, Bonaire", "note": "Ibero-Romance creole of ABC islands. Dutch, African, Arawak influences.", "example": "Bon dia = Good morning"},
    {"language": "Chavacano", "type": "Creole", "base": "Spanish", "speakers": 700000, "lat": 6.9, "lon": 122.1, "country": "Philippines (Zamboanga)", "note": "Only Spanish-based creole in Asia. Six regional varieties.", "example": "Yo ya come = I already ate"},
    {"language": "Bislama", "type": "Creole", "base": "English", "speakers": 10000, "lat": -17.7, "lon": 168.3, "country": "Vanuatu", "note": "National language of Vanuatu. English-lexified. Name from 'beach-la-mer'.", "example": "Mi no save = I don't know"},
    {"language": "Mauritian Creole", "type": "Creole", "base": "French", "speakers": 1000000, "lat": -20.2, "lon": 57.5, "country": "Mauritius", "note": "Spoken by 90% of Mauritians. French-lexified with Malagasy and Bantu substrate.", "example": "Mo kontan ou = I love you"},
    {"language": "Sranan Tongo", "type": "Creole", "base": "English", "speakers": 500000, "lat": 5.8, "lon": -55.2, "country": "Suriname", "note": "Lingua franca of Suriname. English base with Dutch, Portuguese, African influences.", "example": "Mi lobi yu = I love you"},
    {"language": "Cape Verdean Creole", "type": "Creole", "base": "Portuguese", "speakers": 950000, "lat": 15.0, "lon": -23.6, "country": "Cape Verde", "note": "9 island variants. Portuguese-lexified with West African substrate.", "example": "N sta bon = I am well"},
    {"language": "Jamaican Patois", "type": "Creole", "base": "English", "speakers": 3200000, "lat": 18.1, "lon": -77.3, "country": "Jamaica", "note": "English-lexified. West African grammar and vocabulary. Continuum with English.", "example": "Mi nuh know = I don't know"},
    {"language": "Seychellois Creole", "type": "Creole", "base": "French", "speakers": 73000, "lat": -4.6, "lon": 55.5, "country": "Seychelles", "note": "Official language. French-lexified. First creole to gain official status (1981).", "example": "Mon kontan ou = I love you"},
    {"language": "Kristang", "type": "Creole", "base": "Portuguese", "speakers": 750, "lat": 2.2, "lon": 102.2, "country": "Malaysia (Malacca)", "note": "Portuguese-Malay creole from 1511 colonization. Critically endangered.", "example": "Yo ja kumih = I already ate"},
    {"language": "Nigerian Pidgin", "type": "Pidgin/Creole", "base": "English", "speakers": 75000000, "lat": 6.5, "lon": 3.4, "country": "Nigeria", "note": "Largest pidgin by speakers. Used across ethnic lines. BBC has Pidgin service.", "example": "I no sabi = I don't know"},
    {"language": "Sango", "type": "Creole", "base": "Ngbandi", "speakers": 5000000, "lat": 4.4, "lon": 18.6, "country": "Central African Republic", "note": "Rare African-lexified creole. National language of CAR alongside French.", "example": "Bara ala = How are you?"},
    {"language": "Chinook Jargon", "type": "Pidgin", "base": "Chinook/French/English", "speakers": 100, "lat": 45.5, "lon": -122.7, "country": "USA/Canada (Pacific NW)", "note": "19th century trade language of Pacific Northwest. Some revival efforts.", "example": "Kloshe = Good"},
    {"language": "Kituba", "type": "Creole", "base": "Kikongo", "speakers": 4000000, "lat": -4.3, "lon": 15.3, "country": "Congo/DRC", "note": "Kikongo-based creole. National language of both Congos alongside Lingala.", "example": "Mbote = Hello"},
    {"language": "Lingala", "type": "Creole", "base": "Bobangi", "speakers": 25000000, "lat": -4.3, "lon": 15.3, "country": "DRC / Congo", "note": "Bantu creole/lingua franca of Congo Basin. Used in Congolese music globally.", "example": "Mbote = Hello"},
    {"language": "Russenorsk", "type": "Pidgin (Extinct)", "base": "Russian/Norwegian", "speakers": 0, "lat": 70.0, "lon": 30.0, "country": "Arctic Norway/Russia", "note": "Trade pidgin between Russian and Norwegian fishermen. Died out ~1920.", "example": "Moja pa tvoja = Mine on yours (deal)"},
    {"language": "Unserdeutsch", "type": "Creole", "base": "German", "speakers": 100, "lat": -4.2, "lon": 152.2, "country": "Papua New Guinea", "note": "Only German-based creole in the world. Developed in Rabaul mission school.", "example": "Du kann sprech = You can speak"},
]

# ═══════════════════════════════════════════════════════════════
# STATUS COLORS FOR ENDANGERED LANGUAGES
# ═══════════════════════════════════════════════════════════════
STATUS_COLORS = {
    "Safe": "#10b981",
    "Vulnerable": "#f59e0b",
    "Endangered": "#f97316",
    "Severely Endangered": "#ef4444",
    "Critically Endangered": "#dc2626",
    "Extinct": "#6b7280",
    "Extinct (2000s)": "#6b7280",
    "Extinct (2008)": "#6b7280",
    "Extinct (1992)": "#6b7280",
    "Revived": "#06b6d4",
}


# ═══════════════════════════════════════════════════════════════
# HELPER: build a dark-themed folium map
# ═══════════════════════════════════════════════════════════════
def _make_map(center=(20, 0), zoom=2):
    """Create a dark-themed folium map."""
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _render_map(m, height=500):
    """Render a folium map inside Streamlit."""
    components.html(m._repr_html_(), height=height)


def _make_chart(fig_func, height=5, width=10):
    """Wrapper for matplotlib chart with dark theme."""
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)
    fig_func(fig, ax)
    ax.tick_params(colors=TEXT_PRIMARY, labelsize=9)
    ax.xaxis.label.set_color(TEXT_PRIMARY)
    ax.yaxis.label.set_color(TEXT_PRIMARY)
    ax.title.set_color(TEXT_PRIMARY)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════
# MAP MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _mode_language_families():
    """Mode 1: Major Language Families."""
    st.markdown("#### Major Language Families of the World")
    st.markdown(
        "Language families are groups of languages descended from a common ancestral "
        "language (proto-language). The world's ~7,000 living languages belong to "
        "roughly 140 families, plus isolates with no known relatives."
    )

    df = pd.DataFrame(LANGUAGE_FAMILIES)

    # Stats row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Families Shown", len(df))
    c2.metric("Total Languages", f"{df['languages'].sum():,}")
    c3.metric("Total Speakers", f"{df['speakers_b'].sum():.1f} B")
    c4.metric("Largest Family", "Niger-Congo (1,545 langs)")

    # Chart
    def chart_fn(fig, ax):
        sorted_df = df.sort_values("speakers_b", ascending=True)
        colors = [FAMILY_COLORS.get(f, "#64748b") for f in sorted_df["family"]]
        ax.barh(sorted_df["family"], sorted_df["speakers_b"], color=colors)
        ax.set_xlabel("Speakers (Billions)")
        ax.set_title("Language Families by Number of Speakers")
    buf = _make_chart(chart_fn, height=6)
    st.image(buf, width=900)

    # Map
    m = _make_map()
    for _, row in df.iterrows():
        color = FAMILY_COLORS.get(row["family"], "#64748b")
        popup_html = (
            f"<div style='min-width:220px'>"
            f"<b>{escape(row['family'])}</b><br>"
            f"Languages: {row['languages']}<br>"
            f"Speakers: {row['speakers_b']}B<br>"
            f"Region: {escape(row['region'])}<br>"
            f"Branches: {escape(row['branches'])}<br>"
            f"Examples: {escape(row['example'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=max(8, row["speakers_b"] * 8),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["family"]),
        ).add_to(m)
    _render_map(m)

    st.dataframe(
        df[["family", "languages", "speakers_b", "region", "example"]].rename(
            columns={"speakers_b": "speakers (B)", "family": "Family",
                     "languages": "Languages", "region": "Region",
                     "example": "Example Languages"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "language_families.csv", "text/csv")


def _mode_most_spoken():
    """Mode 2: Most Spoken Languages."""
    st.markdown("#### Most Spoken Languages Worldwide")
    st.markdown(
        "The top 50 languages by number of speakers, showing both native and total "
        "(L1 + L2) speaker counts with their geographic centers and writing systems."
    )

    df = pd.DataFrame(TOP_LANGUAGES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Shown", len(df))
    c2.metric("Total Native Speakers", f"{df['native_m'].sum() / 1000:.1f} B")
    c3.metric("Most Native Speakers", "Mandarin (939M)")
    c4.metric("Most Countries", f"English ({df.loc[0, 'countries']})")

    # Chart: top 15 by total speakers
    def chart_fn(fig, ax):
        top15 = df.nlargest(15, "total_m").sort_values("total_m", ascending=True)
        colors = [FAMILY_COLORS.get(f, "#64748b") for f in top15["family"]]
        bars = ax.barh(top15["language"], top15["total_m"], color=colors, alpha=0.8)
        ax.barh(top15["language"], top15["native_m"], color=colors, alpha=0.4)
        ax.set_xlabel("Speakers (Millions)")
        ax.set_title("Top 15 Languages (dark = native, light = total)")
    buf = _make_chart(chart_fn, height=6)
    st.image(buf, width=900)

    # Map
    m = _make_map()
    for _, row in df.iterrows():
        color = FAMILY_COLORS.get(row["family"], "#64748b")
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b>{escape(row['language'])}</b><br>"
            f"Family: {escape(row['family'])}<br>"
            f"Native: {row['native_m']}M<br>"
            f"Total: {row['total_m']}M<br>"
            f"Countries: {row['countries']}<br>"
            f"Script: {escape(row['script'])}"
            f"</div>"
        )
        radius = max(5, min(25, row["total_m"] / 60))
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.65,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{escape(row['language'])} ({row['total_m']}M)",
        ).add_to(m)
    _render_map(m)

    st.dataframe(
        df[["language", "family", "native_m", "total_m", "countries", "script"]].rename(
            columns={"language": "Language", "family": "Family",
                     "native_m": "Native (M)", "total_m": "Total (M)",
                     "countries": "Countries", "script": "Script"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "most_spoken_languages.csv", "text/csv")


def _mode_endangered():
    """Mode 3: Endangered Languages."""
    st.markdown("#### Endangered & Dying Languages")
    st.markdown(
        "UNESCO estimates that a language dies every two weeks. Of the world's ~7,000 "
        "languages, nearly 3,000 are endangered. These markers show critically "
        "endangered languages, some with only a single remaining speaker."
    )

    df = pd.DataFrame(ENDANGERED_LANGUAGES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Shown", len(df))
    critically = len(df[df["status"].str.contains("Critically")])
    c2.metric("Critically Endangered", critically)
    extinct = len(df[df["status"].str.contains("Extinct")])
    c3.metric("Recently Extinct", extinct)
    single = len(df[df["speakers"] <= 1])
    c4.metric("0-1 Speakers Left", single)

    # Map
    m = _make_map()
    for _, row in df.iterrows():
        color = STATUS_COLORS.get(row["status"], "#64748b")
        speakers_str = f"{row['speakers']:,}" if row["speakers"] > 0 else "Extinct"
        popup_html = (
            f"<div style='min-width:220px'>"
            f"<b>{escape(row['language'])}</b><br>"
            f"Status: <span style='color:{color}'>{escape(row['status'])}</span><br>"
            f"Speakers: {speakers_str}<br>"
            f"Region: {escape(row['region'])}<br>"
            f"Family: {escape(row['family'])}<br>"
            f"<i>{escape(row['note'])}</i>"
            f"</div>"
        )
        icon_color = "gray" if "Extinct" in row["status"] else "red"
        folium.Marker(
            location=(row["lat"], row["lon"]),
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(row['language'])} ({speakers_str} speakers)",
            icon=folium.Icon(color=icon_color, icon="exclamation-sign"),
        ).add_to(m)
    _render_map(m)

    # Chart: speakers on log scale
    def chart_fn(fig, ax):
        alive = df[df["speakers"] > 0].sort_values("speakers", ascending=True).tail(20)
        colors = [STATUS_COLORS.get(s, "#64748b") for s in alive["status"]]
        ax.barh(alive["language"], alive["speakers"], color=colors)
        ax.set_xscale("log")
        ax.set_xlabel("Speakers (log scale)")
        ax.set_title("Endangered Languages by Remaining Speakers")
    buf = _make_chart(chart_fn, height=7)
    st.image(buf, width=900)

    st.dataframe(
        df[["language", "status", "speakers", "region", "family", "note"]].rename(
            columns={"language": "Language", "status": "Status",
                     "speakers": "Speakers", "region": "Region",
                     "family": "Family", "note": "Note"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "endangered_languages.csv", "text/csv")


def _mode_writing_systems():
    """Mode 4: Writing Systems of the World."""
    st.markdown("#### Writing Systems & Scripts")
    st.markdown(
        "The world uses dozens of distinct writing systems. Scripts can be alphabets "
        "(each letter = a sound), abjads (consonants only), abugidas (consonant-vowel "
        "units), logographic (symbols = words), or syllabaries (symbols = syllables)."
    )

    df = pd.DataFrame(WRITING_SYSTEMS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scripts Shown", len(df))
    c2.metric("Total Users", f"{df['users_b'].sum():.1f} B")
    c3.metric("Most Used", "Latin (4.9B)")
    c4.metric("Script Types", df["type"].nunique())

    # Chart
    def chart_fn(fig, ax):
        sorted_df = df.nlargest(12, "users_b").sort_values("users_b", ascending=True)
        colors = [SCRIPT_COLORS.get(s, "#64748b") for s in sorted_df["script"]]
        ax.barh(sorted_df["script"], sorted_df["users_b"], color=colors)
        ax.set_xlabel("Users (Billions)")
        ax.set_title("Writing Systems by Number of Users")
    buf = _make_chart(chart_fn, height=5)
    st.image(buf, width=900)

    # Map
    m = _make_map()
    for _, row in df.iterrows():
        color = SCRIPT_COLORS.get(row["script"], "#64748b")
        popup_html = (
            f"<div style='min-width:220px'>"
            f"<b>{escape(row['script'])}</b><br>"
            f"Type: {escape(row['type'])}<br>"
            f"Users: {row['users_b']}B<br>"
            f"Direction: {escape(row['direction'])}<br>"
            f"Origin: {escape(row['origin'])}<br>"
            f"Languages: {row['languages_using']}<br>"
            f"Example: {escape(row['example'])}<br>"
            f"Regions: {escape(row['regions'])}"
            f"</div>"
        )
        radius = max(6, min(22, row["users_b"] * 6))
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['script'])} ({escape(row['type'])})",
        ).add_to(m)
    _render_map(m)

    st.dataframe(
        df[["script", "type", "users_b", "direction", "origin", "example"]].rename(
            columns={"script": "Script", "type": "Type", "users_b": "Users (B)",
                     "direction": "Direction", "origin": "Origin", "example": "Example"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "writing_systems.csv", "text/csv")


def _mode_isolates():
    """Mode 5: Language Isolates."""
    st.markdown("#### Language Isolates")
    st.markdown(
        "Language isolates are languages with no demonstrable genealogical relationship "
        "to any other known language. They are linguistic 'orphans' -- remnants of "
        "language families lost to time, or unique innovations that never spread."
    )

    df = pd.DataFrame(LANGUAGE_ISOLATES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Isolates Shown", len(df))
    living = df[df["speakers"] > 0]
    c2.metric("Living Isolates", len(living))
    c3.metric("Largest", "Korean (81M)")
    c4.metric("Extinct", len(df[df["speakers"] == 0]))

    # Map
    m = _make_map()
    for _, row in df.iterrows():
        speakers_str = f"{row['speakers']:,}" if row["speakers"] > 0 else "Extinct"
        color = "#06b6d4" if row["speakers"] > 100000 else (
            "#f59e0b" if row["speakers"] > 0 else "#6b7280"
        )
        popup_html = (
            f"<div style='min-width:240px'>"
            f"<b>{escape(row['language'])}</b><br>"
            f"Speakers: {speakers_str}<br>"
            f"Region: {escape(row['region'])}<br>"
            f"Status: {escape(row['status'])}<br>"
            f"<i>{escape(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=max(6, min(18, (row["speakers"] ** 0.3) if row["speakers"] > 0 else 6)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(row['language'])} ({speakers_str})",
        ).add_to(m)
    _render_map(m)

    st.dataframe(
        df[["language", "speakers", "region", "status", "note"]].rename(
            columns={"language": "Language", "speakers": "Speakers",
                     "region": "Region", "status": "Status", "note": "Note"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "language_isolates.csv", "text/csv")


def _mode_constructed():
    """Mode 6: Constructed Languages."""
    st.markdown("#### Constructed Languages (Conlangs)")
    st.markdown(
        "Constructed languages are deliberately designed rather than evolving naturally. "
        "They range from international auxiliary languages (Esperanto) to artistic "
        "fictional languages (Elvish, Klingon) and experimental/philosophical projects."
    )

    df = pd.DataFrame(CONSTRUCTED_LANGUAGES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conlangs Shown", len(df))
    c2.metric("Oldest", f"Volapuk ({1879})")
    c3.metric("Most Speakers", "Esperanto (2M)")
    c4.metric("Fictional Langs", len(df[df["purpose"].str.contains("Fictional")]))

    # Map
    m = _make_map(center=(30, 0), zoom=2)
    for _, row in df.iterrows():
        is_fictional = "Fictional" in row["purpose"]
        color = "#8b5cf6" if is_fictional else "#06b6d4"
        speakers_str = f"{row['speakers']:,}" if row["speakers"] > 0 else "Study/fan only"
        popup_html = (
            f"<div style='min-width:220px'>"
            f"<b>{escape(row['language'])}</b><br>"
            f"Creator: {escape(row['creator'])}<br>"
            f"Year: {row['year']}<br>"
            f"Speakers: {speakers_str}<br>"
            f"Purpose: {escape(row['purpose'])}<br>"
            f"<i>{escape(row['note'])}</i>"
            f"</div>"
        )
        folium.Marker(
            location=(row["lat"], row["lon"]),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['language'])} ({row['year']})",
            icon=folium.Icon(
                color="purple" if is_fictional else "blue",
                icon="star" if is_fictional else "globe",
            ),
        ).add_to(m)
    _render_map(m)

    # Chart: timeline
    def chart_fn(fig, ax):
        sorted_df = df.sort_values("year")
        colors = ["#8b5cf6" if "Fictional" in p else "#06b6d4" for p in sorted_df["purpose"]]
        ax.scatter(sorted_df["year"], range(len(sorted_df)), c=colors, s=80, zorder=5)
        for i, (_, row) in enumerate(sorted_df.iterrows()):
            ax.annotate(row["language"], (row["year"], i),
                        xytext=(8, 0), textcoords="offset points",
                        fontsize=7, color=TEXT_PRIMARY, va="center")
        ax.set_xlabel("Year Created")
        ax.set_title("Constructed Languages Timeline")
        ax.set_yticks([])
    buf = _make_chart(chart_fn, height=6)
    st.image(buf, width=900)

    st.dataframe(
        df[["language", "creator", "year", "speakers", "purpose", "region"]].rename(
            columns={"language": "Language", "creator": "Creator", "year": "Year",
                     "speakers": "Speakers", "purpose": "Purpose", "region": "Region"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "constructed_languages.csv", "text/csv")


def _mode_diversity_index():
    """Mode 7: Linguistic Diversity Index."""
    st.markdown("#### Linguistic Diversity Index by Country")
    st.markdown(
        "The Greenberg Linguistic Diversity Index measures the probability that two "
        "randomly selected people in a country speak different first languages. "
        "A score of 1.0 means maximum diversity; 0.0 means total homogeneity."
    )

    df = pd.DataFrame(LINGUISTIC_DIVERSITY)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries Shown", len(df))
    c2.metric("Total Languages", f"{df['languages'].sum():,}")
    c3.metric("Most Diverse", "Papua New Guinea (0.99)")
    c4.metric("Most Languages", f"PNG ({840})")

    # Chart
    def chart_fn(fig, ax):
        sorted_df = df.sort_values("diversity_index", ascending=True)
        colors = [plt.cm.RdYlGn(v) for v in sorted_df["diversity_index"]]
        ax.barh(sorted_df["country"], sorted_df["diversity_index"], color=colors)
        ax.set_xlabel("Linguistic Diversity Index")
        ax.set_title("Countries by Linguistic Diversity (Greenberg Index)")
        ax.set_xlim(0, 1.05)
    buf = _make_chart(chart_fn, height=7)
    st.image(buf, width=900)

    # Map
    m = _make_map()
    for _, row in df.iterrows():
        di = row["diversity_index"]
        if di >= 0.9:
            color = "#dc2626"
        elif di >= 0.7:
            color = "#f97316"
        elif di >= 0.5:
            color = "#f59e0b"
        elif di >= 0.3:
            color = "#06b6d4"
        else:
            color = "#10b981"
        popup_html = (
            f"<div style='min-width:220px'>"
            f"<b>{escape(row['country'])}</b><br>"
            f"Languages: {row['languages']}<br>"
            f"Diversity Index: {row['diversity_index']}<br>"
            f"Population: {row['population_m']}M<br>"
            f"Top Languages: {escape(row['top_langs'])}<br>"
            f"<i>{escape(row['note'])}</i>"
            f"</div>"
        )
        radius = max(6, min(22, row["languages"] / 40))
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['country'])} ({row['languages']} langs, DI={row['diversity_index']})",
        ).add_to(m)
    _render_map(m)

    st.dataframe(
        df[["country", "languages", "diversity_index", "population_m", "top_langs"]].rename(
            columns={"country": "Country", "languages": "Languages",
                     "diversity_index": "Diversity Index",
                     "population_m": "Population (M)",
                     "top_langs": "Top Languages"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "linguistic_diversity.csv", "text/csv")


def _mode_official_languages():
    """Mode 8: Official Languages Map."""
    st.markdown("#### Official & Lingua Franca Languages")
    st.markdown(
        "Official languages are legally designated for government, education, and law. "
        "Some countries have multiple official languages. The six UN official languages "
        "are Arabic, Chinese, English, French, Russian, and Spanish."
    )

    df = pd.DataFrame(OFFICIAL_LANGUAGES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Shown", len(df))
    un_count = len(df[df["un_official"] == True])
    c2.metric("UN Official Languages", un_count)
    c3.metric("Most Countries", f"English ({59})")
    c4.metric("Co-official Shown", len(df[df["type"].str.contains("Co-official")]))

    # Map
    m = _make_map()
    for _, row in df.iterrows():
        color = "#f59e0b" if row["un_official"] else "#06b6d4"
        popup_html = (
            f"<div style='min-width:220px'>"
            f"<b>{escape(row['language'])}</b><br>"
            f"Type: {escape(row['type'])}<br>"
            f"Countries: {row['countries']}<br>"
            f"UN Official: {'Yes' if row['un_official'] else 'No'}<br>"
            f"Regions: {escape(row['regions'])}<br>"
            f"<i>{escape(row['note'])}</i>"
            f"</div>"
        )
        radius = max(6, min(20, row["countries"]))
        icon_color = "orange" if row["un_official"] else "blue"
        folium.Marker(
            location=(row["lat"], row["lon"]),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['language'])} ({row['countries']} countries)",
            icon=folium.Icon(color=icon_color, icon="flag"),
        ).add_to(m)
    _render_map(m)

    # Chart
    def chart_fn(fig, ax):
        sorted_df = df.nlargest(12, "countries").sort_values("countries", ascending=True)
        colors = ["#f59e0b" if un else "#06b6d4" for un in sorted_df["un_official"]]
        ax.barh(sorted_df["language"], sorted_df["countries"], color=colors)
        ax.set_xlabel("Number of Countries")
        ax.set_title("Official Languages by Country Count (orange = UN official)")
    buf = _make_chart(chart_fn, height=5)
    st.image(buf, width=900)

    st.dataframe(
        df[["language", "type", "countries", "un_official", "regions"]].rename(
            columns={"language": "Language", "type": "Type",
                     "countries": "Countries", "un_official": "UN Official",
                     "regions": "Regions"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "official_languages.csv", "text/csv")


def _mode_dead_languages():
    """Mode 9: Dead / Historical Languages."""
    st.markdown("#### Dead & Historical Languages")
    st.markdown(
        "Dead languages no longer have native speakers but survive through written "
        "records, inscriptions, and liturgical use. Many shaped the foundations of "
        "modern civilization: law, philosophy, religion, science, and literature."
    )

    df = pd.DataFrame(DEAD_LANGUAGES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Shown", len(df))
    c2.metric("Oldest", "Sumerian (~3100 BCE)")
    c3.metric("Families Represented", df["family"].nunique())
    c4.metric("Still Liturgical", "Latin, Sanskrit, Coptic, Arabic")

    # Map
    m = _make_map(center=(30, 30), zoom=3)
    for _, row in df.iterrows():
        color = FAMILY_COLORS.get(row["family"], "#64748b")
        popup_html = (
            f"<div style='min-width:250px'>"
            f"<b>{escape(row['language'])}</b><br>"
            f"Family: {escape(row['family'])}<br>"
            f"Era: {escape(row['era'])}<br>"
            f"Died: {escape(row['died'])}<br>"
            f"Center: {escape(row['center'])}<br>"
            f"Legacy: {escape(row['legacy'])}<br>"
            f"Influence: {escape(row['influence'])}"
            f"</div>"
        )
        folium.Marker(
            location=(row["lat"], row["lon"]),
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{escape(row['language'])} ({escape(row['era'])})",
            icon=folium.Icon(color="gray", icon="book"),
        ).add_to(m)
    _render_map(m)

    # Timeline chart
    def chart_fn(fig, ax):
        # Parse approximate start dates
        starts = []
        for era in df["era"]:
            s = era.split(" - ")[0].replace("~", "").strip()
            if "BCE" in s:
                val = -int(s.replace("BCE", "").strip())
            elif "CE" in s:
                val = int(s.replace("CE", "").strip())
            else:
                val = 0
            starts.append(val)
        df_plot = df.copy()
        df_plot["start_year"] = starts
        df_plot = df_plot.sort_values("start_year")
        colors = [FAMILY_COLORS.get(f, "#64748b") for f in df_plot["family"]]
        ax.scatter(df_plot["start_year"], range(len(df_plot)), c=colors, s=80, zorder=5)
        for i, (_, row) in enumerate(df_plot.iterrows()):
            ax.annotate(row["language"], (row["start_year"], i),
                        xytext=(8, 0), textcoords="offset points",
                        fontsize=7, color=TEXT_PRIMARY, va="center")
        ax.set_xlabel("Approximate Start Year (negative = BCE)")
        ax.set_title("Dead Languages Timeline")
        ax.set_yticks([])
        ax.axvline(x=0, color="#2a3550", linestyle="--", linewidth=0.8)
    buf = _make_chart(chart_fn, height=6)
    st.image(buf, width=900)

    st.dataframe(
        df[["language", "family", "era", "center", "legacy"]].rename(
            columns={"language": "Language", "family": "Family", "era": "Era",
                     "center": "Center", "legacy": "Legacy"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "dead_languages.csv", "text/csv")


def _mode_pidgins_creoles():
    """Mode 10: Pidgins & Creoles."""
    st.markdown("#### Pidgins & Creole Languages")
    st.markdown(
        "Pidgins are simplified contact languages that arise between groups with no "
        "common tongue. When a pidgin becomes a community's native language, it "
        "becomes a creole -- a fully complex natural language born from contact."
    )

    df = pd.DataFrame(PIDGINS_CREOLES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Languages Shown", len(df))
    c2.metric("Total Speakers", f"{df['speakers'].sum() / 1e6:.0f}M")
    c3.metric("English-based", len(df[df["base"] == "English"]))
    c4.metric("French-based", len(df[df["base"] == "French"]))

    # Chart: by base language
    def chart_fn(fig, ax):
        base_counts = df.groupby("base")["speakers"].sum().sort_values(ascending=True)
        base_colors = {
            "English": "#06b6d4", "French": "#3b82f6",
            "Portuguese": "#10b981", "Portuguese/Spanish": "#22c55e",
            "Spanish": "#f59e0b", "Russian/Norwegian": "#ef4444",
            "German": "#8b5cf6", "Ngbandi": "#ec4899",
            "Bobangi": "#f97316", "Kikongo": "#14b8a6",
            "Chinook/French/English": "#a855f7",
        }
        colors = [base_colors.get(b, "#64748b") for b in base_counts.index]
        ax.barh(base_counts.index, base_counts.values / 1e6, color=colors)
        ax.set_xlabel("Speakers (Millions)")
        ax.set_title("Pidgin/Creole Speakers by Lexifier Language")
    buf = _make_chart(chart_fn, height=5)
    st.image(buf, width=900)

    # Map
    m = _make_map()
    base_map_colors = {
        "English": "#06b6d4", "French": "#3b82f6", "Portuguese": "#10b981",
        "Portuguese/Spanish": "#22c55e", "Spanish": "#f59e0b",
        "German": "#8b5cf6", "Ngbandi": "#ec4899", "Bobangi": "#f97316",
        "Kikongo": "#14b8a6", "Russian/Norwegian": "#ef4444",
        "Chinook/French/English": "#a855f7",
    }
    for _, row in df.iterrows():
        color = base_map_colors.get(row["base"], "#64748b")
        speakers_str = f"{row['speakers']:,}" if row["speakers"] > 0 else "Extinct"
        popup_html = (
            f"<div style='min-width:220px'>"
            f"<b>{escape(row['language'])}</b><br>"
            f"Type: {escape(row['type'])}<br>"
            f"Base: {escape(row['base'])}<br>"
            f"Speakers: {speakers_str}<br>"
            f"Country: {escape(row['country'])}<br>"
            f"Example: <i>{escape(row['example'])}</i><br>"
            f"{escape(row['note'])}"
            f"</div>"
        )
        radius = max(5, min(18, (row["speakers"] ** 0.25) if row["speakers"] > 0 else 5))
        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['language'])} ({speakers_str})",
        ).add_to(m)
    _render_map(m)

    st.dataframe(
        df[["language", "type", "base", "speakers", "country", "example"]].rename(
            columns={"language": "Language", "type": "Type", "base": "Base Language",
                     "speakers": "Speakers", "country": "Country", "example": "Example"}
        ),
        width="stretch",
    )
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "pidgins_creoles.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
# MODE DISPATCH TABLE
# ═══════════════════════════════════════════════════════════════
MAP_MODES = {
    "Major Language Families": _mode_language_families,
    "Most Spoken Languages": _mode_most_spoken,
    "Endangered Languages": _mode_endangered,
    "Writing Systems": _mode_writing_systems,
    "Language Isolates": _mode_isolates,
    "Constructed Languages": _mode_constructed,
    "Linguistic Diversity Index": _mode_diversity_index,
    "Official Languages Map": _mode_official_languages,
    "Dead Languages": _mode_dead_languages,
    "Pidgins & Creoles": _mode_pidgins_creoles,
}


# ═══════════════════════════════════════════════════════════════
# MAIN TAB RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════
def render_language_maps_tab():
    """Render the Languages & Writing Systems tab for TerraScout AI."""

    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f5e3\ufe0f Languages & Writing Systems</h4>'
        '<p>Language families, endangered languages, scripts, dialects & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        list(MAP_MODES.keys()),
        help="Choose one of 10 linguistic map modes to explore.",
    )

    st.markdown("---")

    # Dispatch to the selected mode
    MAP_MODES[mode]()
