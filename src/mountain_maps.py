# -*- coding: utf-8 -*-
"""
Mountains & Peaks of the World module for TerraScout AI.
Curated data on the world's greatest mountains: eight-thousanders, seven summits,
mountain ranges, deadliest peaks, alpine huts, volcanic peaks, sacred mountains,
climbing history, mountain passes, and mountain weather.
All data is curated or fetched from free public APIs (Overpass/OpenStreetMap).
No API keys required.
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
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_EMERALD = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_PINK = "#ec4899"

OVERPASS_API = "https://overpass-api.de/api/interpreter"

# =====================================================================
# 1. EIGHT-THOUSANDERS DATA (all 14 peaks above 8000 m)
# =====================================================================
EIGHT_THOUSANDERS = [
    {"name": "Mount Everest", "alt_name": "Sagarmatha / Chomolungma", "elevation_m": 8849,
     "lat": 27.9881, "lon": 86.9250, "range": "Himalayas", "country": "Nepal / China",
     "first_ascent": "1953-05-29", "first_by": "Edmund Hillary & Tenzing Norgay",
     "deaths": 310, "summits": 6098, "route": "South Col (Nepal) / North Ridge (Tibet)",
     "notes": "Highest point on Earth. Commercialised since 1990s."},
    {"name": "K2", "alt_name": "Chhogori", "elevation_m": 8611,
     "lat": 35.8825, "lon": 76.5133, "range": "Karakoram", "country": "Pakistan / China",
     "first_ascent": "1954-07-31", "first_by": "Achille Compagnoni & Lino Lacedelli",
     "deaths": 91, "summits": 377, "route": "Abruzzi Spur",
     "notes": "Savage Mountain. Second highest, most difficult 8000er."},
    {"name": "Kangchenjunga", "alt_name": "Five Treasures of Snow", "elevation_m": 8586,
     "lat": 27.7025, "lon": 88.1475, "range": "Himalayas", "country": "Nepal / India",
     "first_ascent": "1955-05-25", "first_by": "Joe Brown & George Band",
     "deaths": 44, "summits": 283, "route": "Southwest Face",
     "notes": "Climbers traditionally stop short of true summit out of respect."},
    {"name": "Lhotse", "alt_name": "South Peak", "elevation_m": 8516,
     "lat": 27.9617, "lon": 86.9336, "range": "Himalayas", "country": "Nepal / China",
     "first_ascent": "1956-05-18", "first_by": "Fritz Luchsinger & Ernst Reiss",
     "deaths": 13, "summits": 461, "route": "West Face / Lhotse Face",
     "notes": "Connected to Everest via South Col. Shares base camp."},
    {"name": "Makalu", "alt_name": "Great Black", "elevation_m": 8485,
     "lat": 27.8897, "lon": 87.0886, "range": "Himalayas", "country": "Nepal / China",
     "first_ascent": "1955-05-15", "first_by": "Jean Couzy & Lionel Terray",
     "deaths": 31, "summits": 361, "route": "Normal Route (NW Ridge)",
     "notes": "Isolated pyramid shape. Extremely steep on all sides."},
    {"name": "Cho Oyu", "alt_name": "Turquoise Goddess", "elevation_m": 8188,
     "lat": 28.0942, "lon": 86.6608, "range": "Himalayas", "country": "Nepal / China",
     "first_ascent": "1954-10-19", "first_by": "Herbert Tichy, Joseph Joechler & Pasang Dawa Lama",
     "deaths": 44, "summits": 3138, "route": "NW Ridge",
     "notes": "Considered easiest 8000er. Popular commercial peak."},
    {"name": "Dhaulagiri I", "alt_name": "White Mountain", "elevation_m": 8167,
     "lat": 28.6983, "lon": 83.4875, "range": "Himalayas", "country": "Nepal",
     "first_ascent": "1960-05-13", "first_by": "Kurt Diemberger, Peter Diener & team",
     "deaths": 69, "summits": 448, "route": "NE Ridge",
     "notes": "First 8000er climbed with air support (small plane)."},
    {"name": "Manaslu", "alt_name": "Mountain of the Spirit", "elevation_m": 8163,
     "lat": 28.5497, "lon": 84.5597, "range": "Himalayas", "country": "Nepal",
     "first_ascent": "1956-05-09", "first_by": "Toshio Imanishi & Gyalzen Norbu",
     "deaths": 68, "summits": 1464, "route": "NE Face / Normal Route",
     "notes": "Japanese mountain. Growing popularity as Everest alternative."},
    {"name": "Nanga Parbat", "alt_name": "Naked Mountain / Killer Mountain", "elevation_m": 8126,
     "lat": 35.2375, "lon": 74.5892, "range": "Himalayas", "country": "Pakistan",
     "first_ascent": "1953-07-03", "first_by": "Hermann Buhl (solo, no oxygen)",
     "deaths": 77, "summits": 335, "route": "Rupal Face / Diamir Face",
     "notes": "Killer Mountain. Buhl's solo first ascent is legendary."},
    {"name": "Annapurna I", "alt_name": "Goddess of the Harvests", "elevation_m": 8091,
     "lat": 28.5961, "lon": 83.8203, "range": "Himalayas", "country": "Nepal",
     "first_ascent": "1950-06-03", "first_by": "Maurice Herzog & Louis Lachenal",
     "deaths": 72, "summits": 191, "route": "North Face",
     "notes": "First 8000er ever climbed. Highest fatality rate (~32%)."},
    {"name": "Gasherbrum I", "alt_name": "Hidden Peak", "elevation_m": 8080,
     "lat": 35.7244, "lon": 76.6961, "range": "Karakoram", "country": "Pakistan / China",
     "first_ascent": "1958-07-05", "first_by": "Pete Schoening & Andy Kauffman",
     "deaths": 29, "summits": 334, "route": "Japanese Couloir / NW Face",
     "notes": "Hidden Peak. Remote and technically demanding."},
    {"name": "Broad Peak", "alt_name": "Falchan Kangri", "elevation_m": 8051,
     "lat": 35.8117, "lon": 76.5653, "range": "Karakoram", "country": "Pakistan / China",
     "first_ascent": "1957-06-09", "first_by": "Fritz Wintersteller, Marcus Schmuck & team",
     "deaths": 21, "summits": 404, "route": "West Spur / Normal Route",
     "notes": "Long summit ridge. First climbed alpine style without oxygen."},
    {"name": "Gasherbrum II", "alt_name": "K4", "elevation_m": 8035,
     "lat": 35.7583, "lon": 76.6531, "range": "Karakoram", "country": "Pakistan / China",
     "first_ascent": "1956-07-07", "first_by": "Fritz Moravec, Josef Larch & Hans Willenpart",
     "deaths": 21, "summits": 930, "route": "SW Ridge / Normal Route",
     "notes": "Safest Karakoram 8000er. Often combined with GI."},
    {"name": "Shishapangma", "alt_name": "Crest Above the Grassy Plains", "elevation_m": 8027,
     "lat": 28.3525, "lon": 85.7797, "range": "Himalayas", "country": "China",
     "first_ascent": "1964-05-02", "first_by": "Xu Jing & Chinese expedition",
     "deaths": 25, "summits": 302, "route": "North Ridge / North Face",
     "notes": "Last 8000er to be climbed. Entirely in Tibet."},
]

# =====================================================================
# 2. SEVEN SUMMITS DATA
# =====================================================================
SEVEN_SUMMITS = [
    {"name": "Mount Everest", "elevation_m": 8849, "continent": "Asia",
     "lat": 27.9881, "lon": 86.9250, "country": "Nepal / China",
     "first_ascent": "1953", "first_by": "Hillary & Tenzing",
     "notes": "Highest point on Earth. Khumbu Icefall is the most dangerous section."},
    {"name": "Aconcagua", "elevation_m": 6961, "continent": "South America",
     "lat": -32.6532, "lon": -70.0109, "country": "Argentina",
     "first_ascent": "1897", "first_by": "Matthias Zurbriggen",
     "notes": "Highest peak outside Asia. Non-technical but extreme altitude."},
    {"name": "Denali", "elevation_m": 6190, "continent": "North America",
     "lat": 63.0695, "lon": -151.0074, "country": "United States (Alaska)",
     "first_ascent": "1913", "first_by": "Hudson Stuck & team",
     "notes": "Greatest base-to-summit rise of any mountain on Earth (~5500 m)."},
    {"name": "Mount Kilimanjaro", "elevation_m": 5895, "continent": "Africa",
     "lat": -3.0674, "lon": 37.3556, "country": "Tanzania",
     "first_ascent": "1889", "first_by": "Hans Meyer & Ludwig Purtscheller",
     "notes": "Highest free-standing mountain. Glaciers rapidly retreating."},
    {"name": "Mount Elbrus", "elevation_m": 5642, "continent": "Europe",
     "lat": 43.3499, "lon": 42.4453, "country": "Russia (Caucasus)",
     "first_ascent": "1874", "first_by": "Florence Crauford Grove & team",
     "notes": "Dormant volcano. Highest peak in Europe (by most definitions)."},
    {"name": "Mount Vinson", "elevation_m": 4892, "continent": "Antarctica",
     "lat": -78.5254, "lon": -85.6171, "country": "Antarctica",
     "first_ascent": "1966", "first_by": "Nicholas Clinch & American Antarctic Expedition",
     "notes": "Most remote of Seven Summits. Extreme cold (-40C common)."},
    {"name": "Puncak Jaya (Carstensz Pyramid)", "elevation_m": 4884, "continent": "Oceania",
     "lat": -4.0833, "lon": 137.1833, "country": "Indonesia (Papua)",
     "first_ascent": "1962", "first_by": "Heinrich Harrer & team",
     "notes": "Only technical rock climb among the Seven Summits. Tropical glacier."},
]

# =====================================================================
# 3. WORLD MOUNTAIN RANGES
# =====================================================================
MOUNTAIN_RANGES = [
    {"name": "Himalayas", "lat": 28.0, "lon": 84.0, "length_km": 2400,
     "highest": "Everest (8849 m)", "countries": "Nepal, India, China, Bhutan, Pakistan",
     "color": "#ef4444", "notes": "Contains all 14 eight-thousanders except K2 area peaks."},
    {"name": "Karakoram", "lat": 35.8, "lon": 76.5, "length_km": 500,
     "highest": "K2 (8611 m)", "countries": "Pakistan, China, India",
     "color": "#f97316", "notes": "Most glaciated area outside polar regions. 4 eight-thousanders."},
    {"name": "Andes", "lat": -15.0, "lon": -70.0, "length_km": 7000,
     "highest": "Aconcagua (6961 m)", "countries": "Argentina, Chile, Peru, Bolivia, Colombia, Ecuador, Venezuela",
     "color": "#f59e0b", "notes": "Longest continental mountain range. Over 100 peaks above 6000 m."},
    {"name": "Alps", "lat": 46.5, "lon": 9.5, "length_km": 1200,
     "highest": "Mont Blanc (4809 m)", "countries": "France, Switzerland, Italy, Austria, Germany, Slovenia, Liechtenstein, Monaco",
     "color": "#10b981", "notes": "Birthplace of modern alpinism. Most visited mountain range."},
    {"name": "Rocky Mountains", "lat": 45.0, "lon": -113.0, "length_km": 4800,
     "highest": "Mount Elbert (4401 m)", "countries": "United States, Canada",
     "color": "#06b6d4", "notes": "Backbone of North America. Continental Divide."},
    {"name": "Atlas Mountains", "lat": 31.5, "lon": -5.0, "length_km": 2500,
     "highest": "Toubkal (4167 m)", "countries": "Morocco, Algeria, Tunisia",
     "color": "#8b5cf6", "notes": "Separates Mediterranean and Sahara climates."},
    {"name": "Ural Mountains", "lat": 56.5, "lon": 59.5, "length_km": 2500,
     "highest": "Mount Narodnaya (1895 m)", "countries": "Russia",
     "color": "#ec4899", "notes": "Traditional boundary between Europe and Asia."},
    {"name": "Caucasus Mountains", "lat": 42.5, "lon": 44.5, "length_km": 1100,
     "highest": "Elbrus (5642 m)", "countries": "Russia, Georgia, Azerbaijan, Armenia",
     "color": "#14b8a6", "notes": "Contains Europe's highest peak by most definitions."},
    {"name": "Hindu Kush", "lat": 36.0, "lon": 71.0, "length_km": 800,
     "highest": "Tirich Mir (7708 m)", "countries": "Afghanistan, Pakistan",
     "color": "#a855f7", "notes": "Gateway range between Central and South Asia."},
    {"name": "Appalachian Mountains", "lat": 37.0, "lon": -80.0, "length_km": 2400,
     "highest": "Mount Mitchell (2037 m)", "countries": "United States, Canada",
     "color": "#22c55e", "notes": "Among the oldest mountains on Earth (~480 million years)."},
    {"name": "Scandinavian Mountains", "lat": 63.0, "lon": 14.0, "length_km": 1700,
     "highest": "Galdhopiggen (2469 m)", "countries": "Norway, Sweden, Finland",
     "color": "#3b82f6", "notes": "Heavily glaciated. Norwegian fjords carved by ice ages."},
    {"name": "Southern Alps (NZ)", "lat": -43.5, "lon": 170.0, "length_km": 500,
     "highest": "Aoraki / Mount Cook (3724 m)", "countries": "New Zealand",
     "color": "#f43f5e", "notes": "Tectonically active. Rising ~7mm per year."},
    {"name": "Pamir Mountains", "lat": 38.5, "lon": 73.0, "length_km": 500,
     "highest": "Ismoil Somoni Peak (7495 m)", "countries": "Tajikistan, Afghanistan, China, Kyrgyzstan",
     "color": "#64748b", "notes": "Roof of the World. Junction of Himalayas, Karakoram, Hindu Kush."},
    {"name": "Tian Shan", "lat": 42.0, "lon": 80.0, "length_km": 2500,
     "highest": "Jengish Chokusu (7439 m)", "countries": "Kyrgyzstan, China, Kazakhstan, Uzbekistan",
     "color": "#0ea5e9", "notes": "Celestial Mountains. Major Silk Road crossings."},
    {"name": "Pyrenees", "lat": 42.6, "lon": 0.5, "length_km": 430,
     "highest": "Aneto (3404 m)", "countries": "France, Spain, Andorra",
     "color": "#d946ef", "notes": "Natural border between France and Spain. Last glaciers retreating."},
]

# =====================================================================
# 4. DEADLIEST MOUNTAINS
# =====================================================================
DEADLIEST_MOUNTAINS = [
    {"name": "Annapurna I", "elevation_m": 8091, "lat": 28.5961, "lon": 83.8203,
     "deaths": 72, "summits": 191, "fatality_rate": 32.0, "range": "Himalayas",
     "worst_disaster": "1950 — Herzog expedition frostbite; 2014 — blizzard killed 43 trekkers on circuit",
     "notes": "Highest fatality-to-summit ratio of any 8000er."},
    {"name": "K2", "elevation_m": 8611, "lat": 35.8825, "lon": 76.5133,
     "deaths": 91, "summits": 377, "fatality_rate": 24.1, "range": "Karakoram",
     "worst_disaster": "2008 — serac collapse on Bottleneck killed 11 climbers in single event",
     "notes": "Savage Mountain. No winter ascent until 2021. Bottleneck most dangerous section."},
    {"name": "Nanga Parbat", "elevation_m": 8126, "lat": 35.2375, "lon": 74.5892,
     "deaths": 77, "summits": 335, "fatality_rate": 21.0, "range": "Himalayas",
     "worst_disaster": "1937 — avalanche buried 16 (7 Germans, 9 Sherpas); 2013 — terrorist attack killed 10",
     "notes": "Killer Mountain. Rupal Face is the highest rock wall on Earth (4600 m)."},
    {"name": "Dhaulagiri I", "elevation_m": 8167, "lat": 28.6983, "lon": 83.4875,
     "deaths": 69, "summits": 448, "fatality_rate": 15.4, "range": "Himalayas",
     "worst_disaster": "1969 — avalanche killed 5 Americans and 2 Sherpas on SE Ridge",
     "notes": "White Mountain. Deep Kali Gandaki gorge separates it from Annapurna."},
    {"name": "Manaslu", "elevation_m": 8163, "lat": 28.5497, "lon": 84.5597,
     "deaths": 68, "summits": 1464, "fatality_rate": 4.6, "range": "Himalayas",
     "worst_disaster": "1972 — avalanche killed 15 (largest single-event death toll on an 8000er at the time)",
     "notes": "Mountain of the Spirit. Fatality rate lowered by recent commercial traffic."},
    {"name": "Mount Everest", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "deaths": 310, "summits": 6098, "fatality_rate": 5.1, "range": "Himalayas",
     "worst_disaster": "2015 — earthquake/avalanche at base camp killed 22; 2014 — serac killed 16 Sherpas",
     "notes": "Highest absolute deaths. Death Zone above 8000 m. Over 200 bodies remain on mountain."},
    {"name": "Kangchenjunga", "elevation_m": 8586, "lat": 27.7025, "lon": 88.1475,
     "deaths": 44, "summits": 283, "fatality_rate": 15.5, "range": "Himalayas",
     "worst_disaster": "Multiple avalanche events; 2019 season saw 4 deaths in quick succession",
     "notes": "Climbers stop short of true summit as sacred tradition."},
    {"name": "Mont Blanc", "elevation_m": 4809, "lat": 45.8326, "lon": 6.8652,
     "deaths": 8000, "summits": 30000, "fatality_rate": 0.3, "range": "Alps",
     "worst_disaster": "Hundreds die annually from falls, storms, altitude. Deadliest mountain overall.",
     "notes": "~100 deaths per year. Deadliest mountain by total count due to high traffic."},
    {"name": "Matterhorn", "elevation_m": 4478, "lat": 45.9764, "lon": 7.6586,
     "deaths": 500, "summits": 3000, "fatality_rate": 3.5, "range": "Alps",
     "worst_disaster": "1865 — first ascent by Edward Whymper; 4 of 7 died on descent",
     "notes": "Iconic pyramid shape. First ascent disaster changed mountaineering history."},
    {"name": "Eiger (North Face)", "elevation_m": 3967, "lat": 46.5775, "lon": 8.0053,
     "deaths": 64, "summits": 400, "fatality_rate": 16.0, "range": "Alps",
     "worst_disaster": "1936 — Toni Kurz died hanging from rope after 3 companions fell; famous rescue attempt",
     "notes": "Nordwand (north wall). The Murder Wall. First climbed 1938 by Heckmair team."},
    {"name": "Siula Grande", "elevation_m": 6344, "lat": -10.2667, "lon": -76.8833,
     "deaths": 4, "summits": 12, "fatality_rate": 33.3, "range": "Andes",
     "worst_disaster": "1985 — Joe Simpson survival story (Touching the Void)",
     "notes": "Made famous by Joe Simpson's incredible survival after falling into crevasse."},
    {"name": "Cerro Torre", "elevation_m": 3128, "lat": -49.3167, "lon": -73.0833,
     "deaths": 10, "summits": 50, "fatality_rate": 20.0, "range": "Andes (Patagonia)",
     "worst_disaster": "Persistent storms with 100+ km/h winds. Controversial 1959 Maestri claim.",
     "notes": "Most technically difficult peak for its height. Rime ice mushroom summit."},
]

# =====================================================================
# 5. VOLCANIC PEAKS
# =====================================================================
VOLCANIC_PEAKS = [
    {"name": "Ojos del Salado", "elevation_m": 6893, "lat": -27.1094, "lon": -68.5414,
     "type": "Stratovolcano", "status": "Dormant", "country": "Chile / Argentina",
     "last_eruption": "~1,000-1,500 years ago", "notes": "Highest volcano on Earth."},
    {"name": "Mount Kilimanjaro", "elevation_m": 5895, "lat": -3.0674, "lon": 37.3556,
     "type": "Stratovolcano", "status": "Dormant", "country": "Tanzania",
     "last_eruption": "~360,000 years ago", "notes": "Highest point in Africa. Glaciers disappearing."},
    {"name": "Mount Elbrus", "elevation_m": 5642, "lat": 43.3499, "lon": 42.4453,
     "type": "Stratovolcano", "status": "Dormant", "country": "Russia",
     "last_eruption": "~50 CE", "notes": "Highest peak in Europe (Caucasus)."},
    {"name": "Cotopaxi", "elevation_m": 5897, "lat": -0.6836, "lon": -78.4375,
     "type": "Stratovolcano", "status": "Active", "country": "Ecuador",
     "last_eruption": "2023 (ongoing)", "notes": "One of highest active volcanoes. Perfect cone shape."},
    {"name": "Mount Rainier", "elevation_m": 4392, "lat": 46.8523, "lon": -121.7603,
     "type": "Stratovolcano", "status": "Active", "country": "United States",
     "last_eruption": "1894", "notes": "Most glaciated peak in contiguous US. Lahar risk to Tacoma/Seattle."},
    {"name": "Mount Fuji", "elevation_m": 3776, "lat": 35.3606, "lon": 138.7274,
     "type": "Stratovolcano", "status": "Active", "country": "Japan",
     "last_eruption": "1707", "notes": "Sacred symbol of Japan. UNESCO World Heritage Site."},
    {"name": "Mount Etna", "elevation_m": 3357, "lat": 37.7510, "lon": 14.9934,
     "type": "Stratovolcano", "status": "Active", "country": "Italy",
     "last_eruption": "2024 (ongoing)", "notes": "Tallest active volcano in Europe. Nearly continuous eruption."},
    {"name": "Mauna Kea", "elevation_m": 4207, "lat": 19.8207, "lon": -155.4680,
     "type": "Shield volcano", "status": "Dormant", "country": "United States (Hawaii)",
     "last_eruption": "~4,600 years ago", "notes": "Tallest mountain from base (10,210 m from ocean floor)."},
    {"name": "Mount Erebus", "elevation_m": 3794, "lat": -77.5300, "lon": 167.1700,
     "type": "Stratovolcano", "status": "Active", "country": "Antarctica",
     "last_eruption": "Continuous", "notes": "Southernmost active volcano. Persistent lava lake."},
    {"name": "Popocatepetl", "elevation_m": 5426, "lat": 19.0225, "lon": -98.6278,
     "type": "Stratovolcano", "status": "Active", "country": "Mexico",
     "last_eruption": "2024 (ongoing)", "notes": "Smoking Mountain. 25 million people live within risk zone."},
    {"name": "Mount Vesuvius", "elevation_m": 1281, "lat": 40.8210, "lon": 14.4260,
     "type": "Somma-stratovolcano", "status": "Active", "country": "Italy",
     "last_eruption": "1944", "notes": "Destroyed Pompeii 79 CE. 3 million people in red zone."},
    {"name": "Chimborazo", "elevation_m": 6263, "lat": -1.4697, "lon": -78.8172,
     "type": "Stratovolcano", "status": "Dormant", "country": "Ecuador",
     "last_eruption": "~550 CE", "notes": "Summit is farthest point from Earth's center (equatorial bulge)."},
    {"name": "Mount Ararat", "elevation_m": 5137, "lat": 39.7019, "lon": 44.2983,
     "type": "Stratovolcano", "status": "Dormant", "country": "Turkey",
     "last_eruption": "1840 (phreatic)", "notes": "Biblical landing site of Noah's Ark. Permanent ice cap."},
    {"name": "Teide", "elevation_m": 3718, "lat": 28.2725, "lon": -16.6414,
     "type": "Stratovolcano", "status": "Active", "country": "Spain (Canary Islands)",
     "last_eruption": "1909", "notes": "Highest point in Spain. Third tallest volcanic structure on Earth."},
]

# =====================================================================
# 6. SACRED MOUNTAINS
# =====================================================================
SACRED_MOUNTAINS = [
    {"name": "Mount Kailash", "elevation_m": 6638, "lat": 31.0672, "lon": 81.3119,
     "religion": "Hinduism, Buddhism, Jainism, Bon", "country": "China (Tibet)",
     "significance": "Abode of Lord Shiva. Center of the universe in Hindu cosmology. Never climbed.",
     "pilgrimage": "Kora (circumambulation) — 52 km trek around the mountain."},
    {"name": "Mount Olympus", "elevation_m": 2917, "lat": 40.0859, "lon": 22.3583,
     "religion": "Ancient Greek", "country": "Greece",
     "significance": "Home of the twelve Olympian gods in Greek mythology.",
     "pilgrimage": "Mytikas summit accessible by hiking. Ancient sacrificial sites."},
    {"name": "Mount Fuji", "elevation_m": 3776, "lat": 35.3606, "lon": 138.7274,
     "religion": "Shinto, Buddhism", "country": "Japan",
     "significance": "Sacred symbol of Japan. Shinto goddess Konohanasakuya-hime enshrined at summit.",
     "pilgrimage": "300,000+ climb annually. Traditional night ascent for sunrise (Goraiko)."},
    {"name": "Mount Sinai", "elevation_m": 2285, "lat": 28.5394, "lon": 33.9753,
     "religion": "Judaism, Christianity, Islam", "country": "Egypt",
     "significance": "Where Moses received the Ten Commandments. St. Catherine's Monastery at base.",
     "pilgrimage": "Steps of Repentance (3750 steps). Sunrise pilgrimage tradition."},
    {"name": "Uluru (Ayers Rock)", "elevation_m": 863, "lat": -25.3444, "lon": 131.0369,
     "religion": "Aboriginal Australian (Anangu)", "country": "Australia",
     "significance": "Sacred Tjukurpa (Dreamtime) site. Climbing banned since 2019 out of respect.",
     "pilgrimage": "Base walk (10.6 km). Sacred caves with ancient rock art."},
    {"name": "Machu Picchu (Huayna Picchu)", "elevation_m": 2693, "lat": -13.1631, "lon": -72.5450,
     "religion": "Inca", "country": "Peru",
     "significance": "Sacred citadel of the Incas. Astronomical observatory aligned with solstices.",
     "pilgrimage": "Inca Trail (4-day trek). Inti Watana (Hitching Post of the Sun)."},
    {"name": "Adam's Peak (Sri Pada)", "elevation_m": 2243, "lat": 6.8096, "lon": 80.4994,
     "religion": "Buddhism, Hinduism, Islam, Christianity", "country": "Sri Lanka",
     "significance": "Sacred footprint at summit claimed by all four religions.",
     "pilgrimage": "5,500 steps. Season Dec-May. Night climb for sunrise."},
    {"name": "Mount Athos", "elevation_m": 2033, "lat": 40.1564, "lon": 24.3264,
     "religion": "Eastern Orthodox Christianity", "country": "Greece",
     "significance": "Holy Mountain. 20 monasteries, monastic republic since 800 CE. Women banned.",
     "pilgrimage": "Diamonitirion permit required. Limited to 10 non-Orthodox visitors per day."},
    {"name": "Croagh Patrick", "elevation_m": 764, "lat": 53.7603, "lon": -9.9264,
     "religion": "Christianity (Catholic)", "country": "Ireland",
     "significance": "Where St. Patrick fasted 40 days in 441 CE and banished snakes.",
     "pilgrimage": "Reek Sunday (last Sunday in July). 25,000+ pilgrims, some barefoot."},
    {"name": "Mount Tai", "elevation_m": 1545, "lat": 36.2563, "lon": 117.1008,
     "religion": "Taoism, Confucianism", "country": "China",
     "significance": "Most revered of China's Five Great Mountains. 72 emperors made pilgrimages.",
     "pilgrimage": "6,660 stone steps. Sunrise viewing. UNESCO World Heritage Site."},
    {"name": "Mount Ararat", "elevation_m": 5137, "lat": 39.7019, "lon": 44.2983,
     "religion": "Christianity, Islam, Judaism", "country": "Turkey",
     "significance": "Traditional resting place of Noah's Ark after the Great Flood.",
     "pilgrimage": "Climbing permits required. Visible from Yerevan, Armenia's capital."},
    {"name": "Tongariro", "elevation_m": 1978, "lat": -39.1578, "lon": 175.6425,
     "religion": "Maori", "country": "New Zealand",
     "significance": "Sacred to Ngati Tuwharetoa people. Gifted to nation in 1887 for protection.",
     "pilgrimage": "Tongariro Alpine Crossing (19.4 km). Emerald Lakes sacred site."},
]

# =====================================================================
# 7. CLIMBING HISTORY / FIRST ASCENTS TIMELINE
# =====================================================================
CLIMBING_HISTORY = [
    {"year": 1786, "peak": "Mont Blanc", "elevation_m": 4809, "lat": 45.8326, "lon": 6.8652,
     "climbers": "Jacques Balmat & Michel-Gabriel Paccard",
     "significance": "Birth of alpinism. First major summit climbed.",
     "era": "Enlightenment"},
    {"year": 1811, "peak": "Jungfrau", "elevation_m": 4158, "lat": 46.5365, "lon": 7.9614,
     "climbers": "Johann Rudolf & Hieronymus Meyer",
     "significance": "First 4000m+ Swiss peak. Pioneered Bernese Oberland exploration.",
     "era": "Early Alpinism"},
    {"year": 1857, "peak": "Alpine Club Founded", "elevation_m": 0, "lat": 51.5074, "lon": -0.1278,
     "climbers": "London — world's first mountaineering club",
     "significance": "Formalized the sport. Published Alpine Journal.",
     "era": "Golden Age"},
    {"year": 1865, "peak": "Matterhorn", "elevation_m": 4478, "lat": 45.9764, "lon": 7.6586,
     "climbers": "Edward Whymper (4 of 7 died descending)",
     "significance": "End of the Golden Age of Alpinism. Most dramatic first ascent.",
     "era": "Golden Age"},
    {"year": 1897, "peak": "Aconcagua", "elevation_m": 6961, "lat": -32.6532, "lon": -70.0109,
     "climbers": "Matthias Zurbriggen",
     "significance": "Highest peak outside Himalayas. First major Andean summit.",
     "era": "Exploration Age"},
    {"year": 1913, "peak": "Denali", "elevation_m": 6190, "lat": 63.0695, "lon": -151.0074,
     "climbers": "Hudson Stuck, Harry Karstens, Robert Tatum & Walter Harper",
     "significance": "First confirmed summit of North America's highest peak.",
     "era": "Exploration Age"},
    {"year": 1936, "peak": "Eiger North Face (attempt)", "elevation_m": 3967, "lat": 46.5775, "lon": 8.0053,
     "climbers": "Toni Kurz — died on rope after rescue attempt",
     "significance": "Most famous mountaineering tragedy. Defined the Murder Wall legend.",
     "era": "Pre-War Era"},
    {"year": 1938, "peak": "Eiger North Face", "elevation_m": 3967, "lat": 46.5775, "lon": 8.0053,
     "climbers": "Anderl Heckmair, Ludwig Vorg, Heinrich Harrer, Fritz Kasparek",
     "significance": "Last great problem of the Alps solved. Harrer wrote 'The White Spider'.",
     "era": "Pre-War Era"},
    {"year": 1950, "peak": "Annapurna I", "elevation_m": 8091, "lat": 28.5961, "lon": 83.8203,
     "climbers": "Maurice Herzog & Louis Lachenal",
     "significance": "FIRST 8000-meter peak ever climbed. Herzog lost all fingers and toes.",
     "era": "Himalayan Golden Age"},
    {"year": 1953, "peak": "Mount Everest", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "climbers": "Edmund Hillary & Tenzing Norgay",
     "significance": "Top of the world. Announced on coronation day of Queen Elizabeth II.",
     "era": "Himalayan Golden Age"},
    {"year": 1953, "peak": "Nanga Parbat", "elevation_m": 8126, "lat": 35.2375, "lon": 74.5892,
     "climbers": "Hermann Buhl — solo, no supplemental oxygen",
     "significance": "Greatest solo achievement in mountaineering history to that point.",
     "era": "Himalayan Golden Age"},
    {"year": 1954, "peak": "K2", "elevation_m": 8611, "lat": 35.8825, "lon": 76.5133,
     "climbers": "Achille Compagnoni & Lino Lacedelli (Italian expedition)",
     "significance": "First ascent of world's most dangerous mountain.",
     "era": "Himalayan Golden Age"},
    {"year": 1964, "peak": "Shishapangma", "elevation_m": 8027, "lat": 28.3525, "lon": 85.7797,
     "climbers": "Chinese expedition led by Xu Jing",
     "significance": "Last 8000er to be climbed. All fourteen conquered in 14 years.",
     "era": "Himalayan Golden Age"},
    {"year": 1970, "peak": "Nanga Parbat Rupal Face", "elevation_m": 8126, "lat": 35.2375, "lon": 74.5892,
     "climbers": "Reinhold Messner & Gunther Messner (Gunther died descending)",
     "significance": "First ascent of tallest rock face. Gunther's death haunted Reinhold.",
     "era": "Modern Alpinism"},
    {"year": 1975, "peak": "Everest — first woman", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "climbers": "Junko Tabei (Japan)",
     "significance": "First woman to summit Everest. Pioneer for women in mountaineering.",
     "era": "Modern Alpinism"},
    {"year": 1978, "peak": "Everest without oxygen", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "climbers": "Reinhold Messner & Peter Habeler",
     "significance": "Proved humans can survive at 8849 m without supplemental O2.",
     "era": "Modern Alpinism"},
    {"year": 1980, "peak": "Everest — solo, no O2", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "climbers": "Reinhold Messner",
     "significance": "First solo ascent without oxygen. Greatest individual mountaineering feat.",
     "era": "Modern Alpinism"},
    {"year": 1986, "peak": "All 14 eight-thousanders", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "climbers": "Reinhold Messner — first person to climb all 14",
     "significance": "All without supplemental oxygen. Defined modern Himalayan ambition.",
     "era": "Modern Alpinism"},
    {"year": 1996, "peak": "Everest Disaster", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "climbers": "Rob Hall, Scott Fischer, and 6 others died",
     "significance": "Exposed dangers of commercial Everest climbing. Into Thin Air (Krakauer).",
     "era": "Commercial Era"},
    {"year": 2019, "peak": "Nirmal Purja — 14 peaks in 6 months", "elevation_m": 8849,
     "lat": 27.9881, "lon": 86.9250,
     "climbers": "Nirmal 'Nims' Purja",
     "significance": "All 14 eight-thousanders in 6 months 6 days. Previous record: 7 years 11 months.",
     "era": "Modern Speed"},
    {"year": 2021, "peak": "K2 — first winter ascent", "elevation_m": 8611, "lat": 35.8825, "lon": 76.5133,
     "climbers": "Nepali team of 10 led by Nirmal Purja & Mingma G",
     "significance": "Last 8000er winter problem solved. Temps reached -60C with windchill.",
     "era": "Modern Speed"},
]

# =====================================================================
# 8. MOUNTAIN PASSES
# =====================================================================
MOUNTAIN_PASSES = [
    {"name": "Khardung La", "elevation_m": 5359, "lat": 34.2817, "lon": 77.6025,
     "country": "India (Ladakh)", "range": "Himalayas",
     "road": "Leh-Nubra Valley Highway", "notes": "One of highest motorable passes. Gateway to Nubra Valley."},
    {"name": "Marsimik La", "elevation_m": 5582, "lat": 34.0583, "lon": 77.7833,
     "country": "India (Ladakh)", "range": "Himalayas",
     "road": "Military road", "notes": "Highest motorable pass (claimed). Restricted area."},
    {"name": "Tanglang La", "elevation_m": 5328, "lat": 33.5586, "lon": 77.5672,
     "country": "India (Ladakh)", "range": "Himalayas",
     "road": "Manali-Leh Highway", "notes": "On the famous Manali-Leh highway. Second highest on route."},
    {"name": "Khunjerab Pass", "elevation_m": 4693, "lat": 36.8500, "lon": 75.4167,
     "country": "Pakistan / China", "range": "Karakoram",
     "road": "Karakoram Highway (KKH)", "notes": "Highest paved international border crossing."},
    {"name": "Col du Galibier", "elevation_m": 2642, "lat": 45.0639, "lon": 6.4078,
     "country": "France", "range": "Alps",
     "road": "D902", "notes": "Legendary Tour de France climb. One of highest paved roads in Alps."},
    {"name": "Stelvio Pass", "elevation_m": 2757, "lat": 46.5286, "lon": 10.4531,
     "country": "Italy", "range": "Alps",
     "road": "SS38", "notes": "48 hairpin bends on east side. Highest paved pass in Eastern Alps."},
    {"name": "Col de l'Iseran", "elevation_m": 2770, "lat": 45.4178, "lon": 7.0303,
     "country": "France", "range": "Alps",
     "road": "D902", "notes": "Highest paved pass in the Alps. Open June-October."},
    {"name": "Gotthard Pass", "elevation_m": 2106, "lat": 46.5571, "lon": 8.5648,
     "country": "Switzerland", "range": "Alps",
     "road": "Route 2", "notes": "Most important Alpine crossing historically. Tunnel opened 1882."},
    {"name": "Brenner Pass", "elevation_m": 1370, "lat": 47.0025, "lon": 11.5078,
     "country": "Austria / Italy", "range": "Alps",
     "road": "E45/A13", "notes": "Lowest Alpine crossing. Used since Roman times. Busiest transalpine route."},
    {"name": "Paso de los Libertadores (Cristo Redentor)", "elevation_m": 3832,
     "lat": -32.8333, "lon": -70.0667,
     "country": "Argentina / Chile", "range": "Andes",
     "road": "Ruta 7 / Ruta 60", "notes": "Main road crossing of the Andes. Christ the Redeemer statue."},
    {"name": "Thorong La", "elevation_m": 5416, "lat": 28.7992, "lon": 83.9331,
     "country": "Nepal", "range": "Himalayas",
     "road": "Annapurna Circuit (trekking)", "notes": "Highest point on Annapurna Circuit. Trekking only."},
    {"name": "Rohtang Pass", "elevation_m": 3978, "lat": 32.3722, "lon": 77.2478,
     "country": "India (Himachal Pradesh)", "range": "Himalayas",
     "road": "NH3 / Atal Tunnel bypass", "notes": "Pile of Corpses (translation). Atal Tunnel bypasses it since 2020."},
    {"name": "Furka Pass", "elevation_m": 2429, "lat": 46.5725, "lon": 8.4142,
     "country": "Switzerland", "range": "Alps",
     "road": "Route 19", "notes": "James Bond car chase location (Goldfinger). Rhone Glacier viewpoint."},
    {"name": "Sani Pass", "elevation_m": 2876, "lat": -29.5869, "lon": 29.2833,
     "country": "South Africa / Lesotho", "range": "Drakensberg",
     "road": "Unpaved road", "notes": "4x4 only. Highest pub in Africa at the top."},
    {"name": "Karakoram Pass", "elevation_m": 5540, "lat": 35.5117, "lon": 77.8125,
     "country": "India / China", "range": "Karakoram",
     "road": "Ancient trade route (closed)", "notes": "Ancient Silk Road route. Currently closed to all traffic."},
]

# =====================================================================
# 9. MOUNTAIN WEATHER / EXTREME CLIMATE DATA
# =====================================================================
MOUNTAIN_WEATHER = [
    {"name": "Mount Everest", "elevation_m": 8849, "lat": 27.9881, "lon": 86.9250,
     "death_zone_m": 8000, "min_temp_c": -60, "max_wind_kmh": 280,
     "avg_annual_precip_mm": 450, "climbing_season": "Apr-May, Sep-Oct",
     "weather_notes": "Jet stream sits on summit in winter. Only ~10 days/year with climbable weather."},
    {"name": "K2", "elevation_m": 8611, "lat": 35.8825, "lon": 76.5133,
     "death_zone_m": 8000, "min_temp_c": -62, "max_wind_kmh": 200,
     "avg_annual_precip_mm": 500, "climbing_season": "Jul-Aug only",
     "weather_notes": "Notorious for sudden storms. Weather window often only 2-3 days per season."},
    {"name": "Denali", "elevation_m": 6190, "lat": 63.0695, "lon": -151.0074,
     "death_zone_m": 5500, "min_temp_c": -73, "max_wind_kmh": 240,
     "avg_annual_precip_mm": 1000, "climbing_season": "May-Jul",
     "weather_notes": "Coldest mountain for its latitude. Sub-arctic storms. -40C common at high camp."},
    {"name": "Mount Washington", "elevation_m": 1917, "lat": 44.2706, "lon": -71.3033,
     "death_zone_m": 0, "min_temp_c": -44, "max_wind_kmh": 372,
     "avg_annual_precip_mm": 2540, "climbing_season": "Jun-Sep (safe)",
     "weather_notes": "Held world wind speed record (372 km/h, 1934) until 1996. 'Worst weather in world'."},
    {"name": "Annapurna I", "elevation_m": 8091, "lat": 28.5961, "lon": 83.8203,
     "death_zone_m": 8000, "min_temp_c": -55, "max_wind_kmh": 200,
     "avg_annual_precip_mm": 3800, "climbing_season": "Apr-May, Oct",
     "weather_notes": "Monsoon dumps massive snow. South face creates its own weather systems."},
    {"name": "Mawenzi (Kilimanjaro)", "elevation_m": 5895, "lat": -3.0674, "lon": 37.3556,
     "death_zone_m": 5000, "min_temp_c": -29, "max_wind_kmh": 100,
     "avg_annual_precip_mm": 2000, "climbing_season": "Jan-Mar, Jun-Oct",
     "weather_notes": "Tropical altitude sickness. Temperature swings 50C in 24 hours."},
    {"name": "Mont Blanc", "elevation_m": 4809, "lat": 45.8326, "lon": 6.8652,
     "death_zone_m": 0, "min_temp_c": -43, "max_wind_kmh": 200,
     "avg_annual_precip_mm": 3000, "climbing_season": "Jun-Sep",
     "weather_notes": "Alps create their own weather. Afternoon thunderstorms nearly daily in summer."},
    {"name": "Aconcagua", "elevation_m": 6961, "lat": -32.6532, "lon": -70.0109,
     "death_zone_m": 6000, "min_temp_c": -50, "max_wind_kmh": 240,
     "avg_annual_precip_mm": 200, "climbing_season": "Nov-Mar",
     "weather_notes": "Viento Blanco (White Wind) can bring -50C windchill with zero visibility."},
    {"name": "Cho Oyu", "elevation_m": 8188, "lat": 28.0942, "lon": 86.6608,
     "death_zone_m": 8000, "min_temp_c": -50, "max_wind_kmh": 150,
     "avg_annual_precip_mm": 400, "climbing_season": "Sep-Oct",
     "weather_notes": "Relatively mild for 8000er. Post-monsoon window most stable."},
    {"name": "Nanga Parbat", "elevation_m": 8126, "lat": 35.2375, "lon": 74.5892,
     "death_zone_m": 8000, "min_temp_c": -58, "max_wind_kmh": 180,
     "avg_annual_precip_mm": 800, "climbing_season": "Jun-Aug",
     "weather_notes": "Rupal Face creates massive avalanche conditions. Monsoon influence."},
    {"name": "Kangchenjunga", "elevation_m": 8586, "lat": 27.7025, "lon": 88.1475,
     "death_zone_m": 8000, "min_temp_c": -55, "max_wind_kmh": 160,
     "avg_annual_precip_mm": 3000, "climbing_season": "Apr-May",
     "weather_notes": "Extreme monsoon snowfall. Eastern location catches moisture first."},
    {"name": "Vinson Massif", "elevation_m": 4892, "lat": -78.5254, "lon": -85.6171,
     "death_zone_m": 0, "min_temp_c": -89, "max_wind_kmh": 160,
     "avg_annual_precip_mm": 50, "climbing_season": "Nov-Jan (Antarctic summer)",
     "weather_notes": "Nearby Vostok Station recorded -89.2C (coldest on Earth). 24h daylight in summer."},
]


# =====================================================================
# OVERPASS API HELPER
# =====================================================================
@st.cache_data(ttl=3600)
def _query_overpass(query: str) -> list:
    """Run an Overpass QL query and return elements."""
    try:
        resp = requests.post(OVERPASS_API, data={"data": query}, timeout=30)
        resp.raise_for_status()
        return resp.json().get("elements", [])
    except Exception as exc:
        logger.warning("Overpass query failed: %s", exc)
        return []


@st.cache_data(ttl=3600)
def fetch_alpine_huts(lat: float, lon: float, radius_m: int = 50000) -> list:
    """Fetch alpine huts from Overpass API around a coordinate."""
    query = f"""
    [out:json][timeout:25];
    (
      node["tourism"="alpine_hut"](around:{radius_m},{lat},{lon});
      way["tourism"="alpine_hut"](around:{radius_m},{lat},{lon});
    );
    out center 200;
    """
    return _query_overpass(query)


# =====================================================================
# HELPER: create a dark folium map
# =====================================================================
def _make_dark_map(center=None, zoom=2):
    """Create a folium map with dark tiles."""
    if center is None:
        center = [30, 50]
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)
    return m


# =====================================================================
# HELPER: render map via components.html
# =====================================================================
def _show_map(m, height=500):
    """Render a folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


# =====================================================================
# HELPER: CSV download button
# =====================================================================
def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Show a download button for a DataFrame as CSV."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, buf.getvalue(), file_name=filename, mime="text/csv")


# =====================================================================
# HELPER: matplotlib bar chart with dark theme
# =====================================================================
def _dark_bar_chart(labels, values, title, ylabel, color=ACCENT_CYAN, horizontal=False, figsize=(10, 5)):
    """Render a dark-themed matplotlib bar chart."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_xlabel(ylabel, color=TEXT_COLOR, fontsize=10)
    else:
        bars = ax.bar(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=10)
    ax.set_title(title, color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="y" if not horizontal else "x", color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# =====================================================================
# MODE 1: EIGHT-THOUSANDERS
# =====================================================================
def _render_eight_thousanders():
    st.markdown("#### The 14 Eight-Thousanders")
    st.markdown(
        "All fourteen peaks above **8,000 metres** — the supreme mountaineering challenge. "
        "Only ~44 people have climbed all 14 without supplemental oxygen."
    )

    df = pd.DataFrame(EIGHT_THOUSANDERS)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Peaks", "14")
    with c2:
        st.metric("Highest", f"{df['elevation_m'].max():,} m")
    with c3:
        st.metric("Total Deaths", f"{df['deaths'].sum():,}")
    with c4:
        st.metric("Total Summits", f"{df['summits'].sum():,}")

    # Chart
    sorted_df = df.sort_values("elevation_m", ascending=True)
    _dark_bar_chart(
        sorted_df["name"].tolist(),
        sorted_df["elevation_m"].tolist(),
        "Eight-Thousanders by Elevation",
        "Elevation (m)",
        color=ACCENT_EMERALD,
        horizontal=True,
        figsize=(10, 6),
    )

    # Map
    st.markdown("---")
    st.markdown("#### World Map of Eight-Thousanders")
    m = _make_dark_map(center=[30, 80], zoom=5)
    for pk in EIGHT_THOUSANDERS:
        death_rate = (pk["deaths"] / pk["summits"] * 100) if pk["summits"] > 0 else 0
        popup_html = (
            f'<div style="max-width:260px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;">{escape(pk["name"])}</strong><br/>'
            f'<em>{escape(pk["alt_name"])}</em><br/>'
            f'<b>{pk["elevation_m"]:,} m</b> &mdash; {escape(pk["range"])}<br/>'
            f'First ascent: {escape(pk["first_ascent"])}<br/>'
            f'{escape(pk["first_by"])}<br/>'
            f'Deaths: {pk["deaths"]} | Summits: {pk["summits"]}<br/>'
            f'Fatality rate: {death_rate:.1f}%<br/>'
            f'<span style="font-size:0.8em;color:#8b97b0;">{escape(pk["notes"])}</span>'
            f'</div>'
        )
        radius = max(6, (pk["elevation_m"] - 8000) / 60)
        folium.CircleMarker(
            location=[pk["lat"], pk["lon"]],
            radius=radius,
            color=ACCENT_EMERALD,
            fill=True,
            fill_color=ACCENT_EMERALD,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f'{pk["name"]} ({pk["elevation_m"]:,} m)',
        ).add_to(m)
    _show_map(m)

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "alt_name", "elevation_m", "range", "country",
                     "first_ascent", "first_by", "deaths", "summits", "route"]].copy()
    display_df.columns = ["Peak", "Alt Name", "Elevation (m)", "Range", "Country",
                          "First Ascent", "First By", "Deaths", "Summits", "Route"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "eight_thousanders.csv")


# =====================================================================
# MODE 2: SEVEN SUMMITS
# =====================================================================
def _render_seven_summits():
    st.markdown("#### The Seven Summits")
    st.markdown(
        "The highest peak on each of the seven continents. The challenge was popularised by "
        "Dick Bass (first completion, 1985) and Reinhold Messner (Carstensz list)."
    )

    df = pd.DataFrame(SEVEN_SUMMITS)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Continents", "7")
    with c2:
        st.metric("Highest", f"{df['elevation_m'].max():,} m")
    with c3:
        st.metric("Lowest", f"{df['elevation_m'].min():,} m")

    # Chart
    sorted_df = df.sort_values("elevation_m", ascending=True)
    colors = ["#ef4444", "#f59e0b", "#10b981", "#06b6d4", "#8b5cf6", "#ec4899", "#f97316"]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    bars = ax.barh(
        [f'{r["name"]}\n({r["continent"]})' for _, r in sorted_df.iterrows()],
        sorted_df["elevation_m"].tolist(),
        color=colors,
        edgecolor=colors,
        alpha=0.85,
    )
    ax.set_xlabel("Elevation (m)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Seven Summits by Elevation", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    st.markdown("---")
    st.markdown("#### Seven Summits on the Map")
    m = _make_dark_map(center=[20, 0], zoom=2)
    summit_colors = {
        "Asia": "#ef4444", "South America": "#f59e0b", "North America": "#10b981",
        "Africa": "#06b6d4", "Europe": "#8b5cf6", "Antarctica": "#ec4899",
        "Oceania": "#f97316",
    }
    for pk in SEVEN_SUMMITS:
        clr = summit_colors.get(pk["continent"], ACCENT_CYAN)
        popup_html = (
            f'<div style="max-width:240px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;">{escape(pk["name"])}</strong><br/>'
            f'<b>{pk["elevation_m"]:,} m</b> &mdash; {escape(pk["continent"])}<br/>'
            f'{escape(pk["country"])}<br/>'
            f'First ascent: {escape(pk["first_ascent"])} by {escape(pk["first_by"])}<br/>'
            f'<span style="font-size:0.8em;color:#8b97b0;">{escape(pk["notes"])}</span>'
            f'</div>'
        )
        folium.Marker(
            location=[pk["lat"], pk["lon"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f'{pk["name"]} ({pk["elevation_m"]:,} m)',
            icon=folium.Icon(color="red", icon="mountain", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "elevation_m", "continent", "country",
                     "first_ascent", "first_by", "notes"]].copy()
    display_df.columns = ["Peak", "Elevation (m)", "Continent", "Country",
                          "First Ascent", "First By", "Notes"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "seven_summits.csv")


# =====================================================================
# MODE 3: WORLD MOUNTAIN RANGES
# =====================================================================
def _render_mountain_ranges():
    st.markdown("#### Major Mountain Ranges of the World")
    st.markdown(
        "The great mountain chains that define continents, shape climates, and divide civilizations."
    )

    df = pd.DataFrame(MOUNTAIN_RANGES)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Ranges Shown", f"{len(MOUNTAIN_RANGES)}")
    with c2:
        st.metric("Longest", f"{df['length_km'].max():,} km")
    with c3:
        st.metric("Total Length", f"{df['length_km'].sum():,} km")

    # Chart
    sorted_df = df.sort_values("length_km", ascending=True)
    _dark_bar_chart(
        sorted_df["name"].tolist(),
        sorted_df["length_km"].tolist(),
        "Mountain Ranges by Length",
        "Length (km)",
        color=ACCENT_AMBER,
        horizontal=True,
        figsize=(10, 7),
    )

    # Map
    st.markdown("---")
    st.markdown("#### Global Mountain Range Map")
    m = _make_dark_map(center=[25, 40], zoom=2)
    for rng in MOUNTAIN_RANGES:
        popup_html = (
            f'<div style="max-width:250px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;">{escape(rng["name"])}</strong><br/>'
            f'Length: <b>{rng["length_km"]:,} km</b><br/>'
            f'Highest: {escape(rng["highest"])}<br/>'
            f'Countries: {escape(rng["countries"])}<br/>'
            f'<span style="font-size:0.8em;color:#8b97b0;">{escape(rng["notes"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[rng["lat"], rng["lon"]],
            radius=max(8, rng["length_km"] / 400),
            color=rng["color"],
            fill=True,
            fill_color=rng["color"],
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=270),
            tooltip=f'{rng["name"]} ({rng["length_km"]:,} km)',
        ).add_to(m)
    _show_map(m)

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "length_km", "highest", "countries", "notes"]].copy()
    display_df.columns = ["Range", "Length (km)", "Highest Peak", "Countries", "Notes"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "mountain_ranges.csv")


# =====================================================================
# MODE 4: DEADLIEST MOUNTAINS
# =====================================================================
def _render_deadliest():
    st.markdown("#### The Deadliest Mountains on Earth")
    st.markdown(
        "Mountains ranked by fatality rate, total deaths, and famous disasters. "
        "From the Himalayan eight-thousanders to the Alpine \"Murder Wall\"."
    )

    df = pd.DataFrame(DEADLIEST_MOUNTAINS)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Peaks Listed", f"{len(df)}")
    with c2:
        st.metric("Total Deaths", f"{df['deaths'].sum():,}")
    with c3:
        highest_rate = df.loc[df["fatality_rate"].idxmax()]
        st.metric("Highest Rate", f'{highest_rate["fatality_rate"]:.0f}% ({highest_rate["name"]})')
    with c4:
        most_deaths = df.loc[df["deaths"].idxmax()]
        st.metric("Most Deaths", f'{most_deaths["deaths"]:,} ({most_deaths["name"]})')

    # Chart — fatality rate
    sorted_df = df.sort_values("fatality_rate", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    colors_list = []
    for _, row in sorted_df.iterrows():
        if row["fatality_rate"] >= 20:
            colors_list.append("#ef4444")
        elif row["fatality_rate"] >= 10:
            colors_list.append("#f59e0b")
        elif row["fatality_rate"] >= 5:
            colors_list.append("#f97316")
        else:
            colors_list.append("#10b981")
    ax.barh(sorted_df["name"].tolist(), sorted_df["fatality_rate"].tolist(),
            color=colors_list, edgecolor=colors_list, alpha=0.85)
    ax.set_xlabel("Fatality Rate (%)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Mountains by Fatality Rate (deaths / summits)", color=TEXT_COLOR,
                 fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    st.markdown("---")
    st.markdown("#### Deadliest Peaks Map")
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Rate &ge;20%</span>
        <span style="color:#f59e0b; font-size:0.8rem;">&#9679; Rate 10-20%</span>
        <span style="color:#f97316; font-size:0.8rem;">&#9679; Rate 5-10%</span>
        <span style="color:#10b981; font-size:0.8rem;">&#9679; Rate &lt;5%</span>
    </div>
    """, unsafe_allow_html=True)

    m = _make_dark_map(center=[35, 40], zoom=3)
    for pk in DEADLIEST_MOUNTAINS:
        rate = pk["fatality_rate"]
        if rate >= 20:
            clr = "#ef4444"
        elif rate >= 10:
            clr = "#f59e0b"
        elif rate >= 5:
            clr = "#f97316"
        else:
            clr = "#10b981"
        popup_html = (
            f'<div style="max-width:280px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;color:{clr};">{escape(pk["name"])}</strong><br/>'
            f'<b>{pk["elevation_m"]:,} m</b> &mdash; {escape(pk["range"])}<br/>'
            f'Deaths: <b>{pk["deaths"]}</b> | Summits: <b>{pk["summits"]}</b><br/>'
            f'Fatality rate: <b>{pk["fatality_rate"]:.1f}%</b><br/>'
            f'Worst disaster: {escape(pk["worst_disaster"])}<br/>'
            f'<span style="font-size:0.8em;color:#8b97b0;">{escape(pk["notes"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[pk["lat"], pk["lon"]],
            radius=max(6, pk["fatality_rate"] / 2),
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f'{pk["name"]} — {pk["fatality_rate"]:.1f}% fatality rate',
        ).add_to(m)
    _show_map(m)

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "elevation_m", "range", "deaths", "summits",
                     "fatality_rate", "worst_disaster", "notes"]].copy()
    display_df.columns = ["Peak", "Elevation (m)", "Range", "Deaths", "Summits",
                          "Fatality Rate (%)", "Worst Disaster", "Notes"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "deadliest_mountains.csv")


# =====================================================================
# MODE 5: ALPINE HUTS & REFUGES
# =====================================================================
ALPINE_HUT_REGIONS = {
    "Alps — Mont Blanc Area": {"lat": 45.83, "lon": 6.87, "radius": 30000},
    "Alps — Bernese Oberland": {"lat": 46.55, "lon": 7.96, "radius": 30000},
    "Alps — Dolomites": {"lat": 46.41, "lon": 11.84, "radius": 40000},
    "Alps — Zermatt / Matterhorn": {"lat": 45.98, "lon": 7.66, "radius": 25000},
    "Alps — Tyrol (Austria)": {"lat": 47.05, "lon": 11.40, "radius": 40000},
    "Pyrenees — Central": {"lat": 42.65, "lon": 0.50, "radius": 50000},
    "Himalayas — Everest Region": {"lat": 27.99, "lon": 86.93, "radius": 40000},
    "Himalayas — Annapurna Region": {"lat": 28.60, "lon": 83.82, "radius": 40000},
    "Andes — Patagonia": {"lat": -49.30, "lon": -73.00, "radius": 50000},
    "Scandinavian Mountains — Jotunheimen": {"lat": 61.60, "lon": 8.30, "radius": 40000},
}


def _render_alpine_huts():
    st.markdown("#### Alpine Huts & Mountain Refuges")
    st.markdown(
        "Mountain huts and refuges provide shelter for climbers and hikers in remote alpine terrain. "
        "Data sourced live from **OpenStreetMap** via the Overpass API."
    )

    region_name = st.selectbox(
        "Select a mountain region",
        list(ALPINE_HUT_REGIONS.keys()),
        key="alpine_hut_region",
    )
    region = ALPINE_HUT_REGIONS[region_name]

    with st.spinner(f"Fetching alpine huts near {region_name}..."):
        elements = fetch_alpine_huts(region["lat"], region["lon"], region["radius"])

    if not elements:
        st.warning("No alpine huts found in this area. Try a different region or expand the radius.")
        return

    # Parse results
    huts = []
    for el in elements:
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        huts.append({
            "name": tags.get("name", "Unnamed Hut"),
            "lat": lat,
            "lon": lon,
            "elevation": tags.get("ele", "Unknown"),
            "capacity": tags.get("capacity", "Unknown"),
            "operator": tags.get("operator", "Unknown"),
            "website": tags.get("website", ""),
            "description": tags.get("description", ""),
        })

    df = pd.DataFrame(huts)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Huts Found", f"{len(huts)}")
    with c2:
        known_elev = [h for h in huts if h["elevation"] != "Unknown"]
        if known_elev:
            try:
                max_el = max(int(str(h["elevation"]).replace(",", "").split(".")[0]) for h in known_elev)
                st.metric("Highest Hut", f"{max_el:,} m")
            except (ValueError, TypeError):
                st.metric("Highest Hut", "N/A")
        else:
            st.metric("Highest Hut", "N/A")

    # Map
    st.markdown("---")
    st.markdown(f"#### Alpine Huts — {escape(region_name)}")
    m = _make_dark_map(center=[region["lat"], region["lon"]], zoom=10)
    for h in huts:
        popup_html = (
            f'<div style="max-width:220px;font-family:sans-serif;">'
            f'<strong>{escape(str(h["name"]))}</strong><br/>'
            f'Elevation: {escape(str(h["elevation"]))} m<br/>'
            f'Capacity: {escape(str(h["capacity"]))}<br/>'
            f'Operator: {escape(str(h["operator"]))}<br/>'
        )
        if h["website"]:
            popup_html += f'<a href="{escape(str(h["website"]))}" target="_blank">Website</a><br/>'
        popup_html += '</div>'
        folium.Marker(
            location=[h["lat"], h["lon"]],
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=escape(str(h["name"])),
            icon=folium.Icon(color="green", icon="home", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "lat", "lon", "elevation", "capacity", "operator"]].copy()
    display_df.columns = ["Name", "Lat", "Lon", "Elevation (m)", "Capacity", "Operator"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "alpine_huts.csv")


# =====================================================================
# MODE 6: VOLCANIC PEAKS
# =====================================================================
def _render_volcanic_peaks():
    st.markdown("#### Volcanic Peaks of the World")
    st.markdown(
        "Mountains that are also volcanoes — from the highest (Ojos del Salado, 6,893 m) "
        "to the most dangerous (Vesuvius, Popocatepetl). Includes active, dormant, and extinct peaks."
    )

    df = pd.DataFrame(VOLCANIC_PEAKS)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Volcanoes Listed", f"{len(df)}")
    with c2:
        active = len(df[df["status"] == "Active"])
        st.metric("Active", f"{active}")
    with c3:
        dormant = len(df[df["status"] == "Dormant"])
        st.metric("Dormant", f"{dormant}")
    with c4:
        st.metric("Highest", f"{df['elevation_m'].max():,} m")

    # Chart
    sorted_df = df.sort_values("elevation_m", ascending=True)
    clrs = [ACCENT_RED if r["status"] == "Active" else ACCENT_AMBER for _, r in sorted_df.iterrows()]
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    ax.barh(sorted_df["name"].tolist(), sorted_df["elevation_m"].tolist(),
            color=clrs, edgecolor=clrs, alpha=0.85)
    ax.set_xlabel("Elevation (m)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Volcanic Peaks by Elevation", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Active</span>
        <span style="color:#f59e0b; font-size:0.8rem;">&#9679; Dormant</span>
    </div>
    """, unsafe_allow_html=True)

    # Map
    st.markdown("---")
    st.markdown("#### Volcanic Peaks Map")
    m = _make_dark_map(center=[15, 0], zoom=2)
    for vk in VOLCANIC_PEAKS:
        clr = ACCENT_RED if vk["status"] == "Active" else ACCENT_AMBER
        popup_html = (
            f'<div style="max-width:260px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;color:{clr};">{escape(vk["name"])}</strong><br/>'
            f'<b>{vk["elevation_m"]:,} m</b> &mdash; {escape(vk["country"])}<br/>'
            f'Type: {escape(vk["type"])}<br/>'
            f'Status: <b>{escape(vk["status"])}</b><br/>'
            f'Last eruption: {escape(vk["last_eruption"])}<br/>'
            f'<span style="font-size:0.8em;color:#8b97b0;">{escape(vk["notes"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[vk["lat"], vk["lon"]],
            radius=max(6, vk["elevation_m"] / 800),
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f'{vk["name"]} ({vk["elevation_m"]:,} m) — {vk["status"]}',
        ).add_to(m)
    _show_map(m)

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "elevation_m", "type", "status", "country",
                     "last_eruption", "notes"]].copy()
    display_df.columns = ["Peak", "Elevation (m)", "Type", "Status", "Country",
                          "Last Eruption", "Notes"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "volcanic_peaks.csv")


# =====================================================================
# MODE 7: SACRED MOUNTAINS
# =====================================================================
def _render_sacred_mountains():
    st.markdown("#### Sacred Mountains of the World")
    st.markdown(
        "Mountains revered across religions and cultures, from Hindu/Buddhist Mount Kailash "
        "to Shinto Mount Fuji, Greek Mount Olympus, and Aboriginal Uluru."
    )

    df = pd.DataFrame(SACRED_MOUNTAINS)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Sacred Sites", f"{len(df)}")
    with c2:
        st.metric("Highest", f"{df['elevation_m'].max():,} m")
    with c3:
        religions = set()
        for s in SACRED_MOUNTAINS:
            for r in s["religion"].split(", "):
                religions.add(r.strip())
        st.metric("Religions/Traditions", f"{len(religions)}")

    # Map
    st.markdown("---")
    st.markdown("#### Sacred Mountains Map")
    religion_colors = {
        "Hinduism": "#f97316", "Buddhism": "#f59e0b", "Jainism": "#06b6d4",
        "Bon": "#8b5cf6", "Shinto": "#ef4444", "Christianity": "#3b82f6",
        "Islam": "#10b981", "Judaism": "#ec4899", "Taoism": "#14b8a6",
        "Confucianism": "#a855f7", "Inca": "#f43f5e", "Maori": "#22c55e",
        "Catholic": "#3b82f6", "Eastern Orthodox Christianity": "#0ea5e9",
        "Ancient Greek": "#d946ef", "Aboriginal Australian (Anangu)": "#64748b",
    }
    m = _make_dark_map(center=[25, 50], zoom=2)
    for mt in SACRED_MOUNTAINS:
        # pick color from first religion
        first_rel = mt["religion"].split(",")[0].strip()
        clr = religion_colors.get(first_rel, ACCENT_CYAN)
        popup_html = (
            f'<div style="max-width:280px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;">{escape(mt["name"])}</strong><br/>'
            f'<b>{mt["elevation_m"]:,} m</b> &mdash; {escape(mt["country"])}<br/>'
            f'Religion: {escape(mt["religion"])}<br/>'
            f'Significance: {escape(mt["significance"])}<br/>'
            f'<span style="font-size:0.85em;color:#06b6d4;">{escape(mt["pilgrimage"])}</span>'
            f'</div>'
        )
        folium.Marker(
            location=[mt["lat"], mt["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f'{mt["name"]} — {mt["religion"]}',
            icon=folium.Icon(color="purple", icon="star", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    # Cards
    st.markdown("---")
    st.markdown("#### Sacred Peak Details")
    for mt in SACRED_MOUNTAINS:
        first_rel = mt["religion"].split(",")[0].strip()
        clr = religion_colors.get(first_rel, ACCENT_CYAN)
        st.markdown(
            f'<div style="background:{SURFACE_COLOR}; border:1px solid #2a3550; border-radius:8px; '
            f'padding:1rem; margin-bottom:0.75rem;">'
            f'<div style="display:flex; align-items:center; gap:0.75rem;">'
            f'<div style="width:50px; height:50px; border-radius:50%; background:{clr}20; '
            f'display:flex; align-items:center; justify-content:center; flex-shrink:0;">'
            f'<span style="font-size:1.2rem;">&#9968;</span></div>'
            f'<div>'
            f'<div style="color:{TEXT_COLOR}; font-weight:700; font-size:0.95rem;">'
            f'{escape(mt["name"])} ({mt["elevation_m"]:,} m)</div>'
            f'<div style="color:{clr}; font-size:0.8rem;">{escape(mt["religion"])}</div>'
            f'<div style="color:{TEXT_SECONDARY}; font-size:0.8rem;">{escape(mt["significance"])}</div>'
            f'<div style="color:#5a6580; font-size:0.75rem;">Pilgrimage: {escape(mt["pilgrimage"])}</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "elevation_m", "religion", "country", "significance", "pilgrimage"]].copy()
    display_df.columns = ["Mountain", "Elevation (m)", "Religion", "Country", "Significance", "Pilgrimage"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "sacred_mountains.csv")


# =====================================================================
# MODE 8: CLIMBING HISTORY
# =====================================================================
def _render_climbing_history():
    st.markdown("#### Climbing History Timeline")
    st.markdown(
        "Key milestones from the birth of alpinism in 1786 to the modern speed era. "
        "The golden age of Himalayan climbing (1950-1964) saw all fourteen 8000ers conquered."
    )

    df = pd.DataFrame(CLIMBING_HISTORY)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Events", f"{len(df)}")
    with c2:
        st.metric("Timespan", f'{df["year"].min()}-{df["year"].max()}')
    with c3:
        himgold = len(df[df["era"] == "Himalayan Golden Age"])
        st.metric("Himalayan Golden Age", f"{himgold} events")
    with c4:
        st.metric("Eras Covered", f'{df["era"].nunique()}')

    # Timeline chart
    era_colors = {
        "Enlightenment": "#06b6d4", "Early Alpinism": "#10b981",
        "Golden Age": "#f59e0b", "Exploration Age": "#8b5cf6",
        "Pre-War Era": "#f97316", "Himalayan Golden Age": "#ef4444",
        "Modern Alpinism": "#ec4899", "Commercial Era": "#a855f7",
        "Modern Speed": "#14b8a6",
    }
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    for i, (_, row) in enumerate(df.iterrows()):
        clr = era_colors.get(row["era"], ACCENT_CYAN)
        elev = row["elevation_m"] if row["elevation_m"] > 0 else 2000
        ax.scatter(row["year"], elev, color=clr, s=60, zorder=3, alpha=0.9)
    ax.set_xlabel("Year", color=TEXT_COLOR, fontsize=10)
    ax.set_ylabel("Peak Elevation (m)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Climbing Milestones Through History", color=TEXT_COLOR, fontsize=13,
                 fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Legend
    legend_html = '<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.75rem;">'
    for era_name, era_clr in era_colors.items():
        legend_html += f'<span style="color:{era_clr}; font-size:0.8rem;">&#9679; {escape(era_name)}</span>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)

    # Map
    st.markdown("---")
    st.markdown("#### Key Ascents Map")
    m = _make_dark_map(center=[35, 60], zoom=3)
    seen_locations = set()
    for ev in CLIMBING_HISTORY:
        if ev["elevation_m"] == 0:
            continue
        loc_key = f'{ev["lat"]:.2f},{ev["lon"]:.2f}'
        offset_lat = 0
        offset_lon = 0
        while loc_key in seen_locations:
            offset_lat += 0.15
            offset_lon += 0.15
            loc_key = f'{ev["lat"] + offset_lat:.2f},{ev["lon"] + offset_lon:.2f}'
        seen_locations.add(loc_key)
        clr = era_colors.get(ev["era"], ACCENT_CYAN)
        popup_html = (
            f'<div style="max-width:260px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;">{ev["year"]} — {escape(ev["peak"])}</strong><br/>'
            f'<b>{ev["elevation_m"]:,} m</b><br/>'
            f'Climbers: {escape(ev["climbers"])}<br/>'
            f'Era: {escape(ev["era"])}<br/>'
            f'<span style="font-size:0.85em;color:#06b6d4;">{escape(ev["significance"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[ev["lat"] + offset_lat, ev["lon"] + offset_lon],
            radius=7,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f'{ev["year"]} — {ev["peak"]}',
        ).add_to(m)
    _show_map(m)

    # Timeline cards
    st.markdown("---")
    st.markdown("#### Full Timeline")
    for ev in CLIMBING_HISTORY:
        clr = era_colors.get(ev["era"], ACCENT_CYAN)
        elev_str = f'{ev["elevation_m"]:,} m' if ev["elevation_m"] > 0 else ""
        st.markdown(
            f'<div style="background:{SURFACE_COLOR}; border-left:3px solid {clr}; '
            f'padding:0.75rem 1rem; margin-bottom:0.5rem; border-radius:0 6px 6px 0;">'
            f'<div style="display:flex; align-items:baseline; gap:0.75rem;">'
            f'<span style="color:{clr}; font-weight:800; font-size:1.1rem;">{ev["year"]}</span>'
            f'<span style="color:{TEXT_COLOR}; font-weight:600;">{escape(ev["peak"])}</span>'
            f'<span style="color:{TEXT_SECONDARY}; font-size:0.8rem;">{elev_str}</span>'
            f'</div>'
            f'<div style="color:{TEXT_SECONDARY}; font-size:0.8rem; margin-top:0.2rem;">'
            f'{escape(ev["climbers"])}</div>'
            f'<div style="color:#5a6580; font-size:0.75rem;">{escape(ev["significance"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Table & download
    st.markdown("---")
    display_df = df[["year", "peak", "elevation_m", "climbers", "era", "significance"]].copy()
    display_df.columns = ["Year", "Peak", "Elevation (m)", "Climbers", "Era", "Significance"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "climbing_history.csv")


# =====================================================================
# MODE 9: MOUNTAIN PASSES
# =====================================================================
def _render_mountain_passes():
    st.markdown("#### Mountain Passes of the World")
    st.markdown(
        "The highest and most famous road and trekking passes, from the Himalayan Khardung La "
        "to the legendary Tour de France cols in the Alps."
    )

    df = pd.DataFrame(MOUNTAIN_PASSES)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Passes Listed", f"{len(df)}")
    with c2:
        st.metric("Highest", f"{df['elevation_m'].max():,} m")
    with c3:
        ranges = df["range"].nunique()
        st.metric("Mountain Ranges", f"{ranges}")

    # Chart
    sorted_df = df.sort_values("elevation_m", ascending=True)
    range_colors = {
        "Himalayas": "#ef4444", "Karakoram": "#f97316", "Alps": "#10b981",
        "Andes": "#f59e0b", "Drakensberg": "#8b5cf6",
    }
    clrs = [range_colors.get(r, ACCENT_CYAN) for r in sorted_df["range"]]
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    ax.barh(sorted_df["name"].tolist(), sorted_df["elevation_m"].tolist(),
            color=clrs, edgecolor=clrs, alpha=0.85)
    ax.set_xlabel("Elevation (m)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Mountain Passes by Elevation", color=TEXT_COLOR, fontsize=13,
                 fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    st.markdown("---")
    st.markdown("#### Mountain Passes Map")
    m = _make_dark_map(center=[35, 50], zoom=3)
    for ps in MOUNTAIN_PASSES:
        clr = range_colors.get(ps["range"], ACCENT_CYAN)
        popup_html = (
            f'<div style="max-width:250px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;">{escape(ps["name"])}</strong><br/>'
            f'<b>{ps["elevation_m"]:,} m</b><br/>'
            f'{escape(ps["country"])} &mdash; {escape(ps["range"])}<br/>'
            f'Road: {escape(ps["road"])}<br/>'
            f'<span style="font-size:0.8em;color:#8b97b0;">{escape(ps["notes"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[ps["lat"], ps["lon"]],
            radius=max(5, ps["elevation_m"] / 800),
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=270),
            tooltip=f'{ps["name"]} ({ps["elevation_m"]:,} m)',
        ).add_to(m)
    _show_map(m)

    # Table
    st.markdown("---")
    st.markdown("#### Data Table")
    display_df = df[["name", "elevation_m", "country", "range", "road", "notes"]].copy()
    display_df.columns = ["Pass", "Elevation (m)", "Country", "Range", "Road", "Notes"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "mountain_passes.csv")


# =====================================================================
# MODE 10: MOUNTAIN WEATHER
# =====================================================================
def _render_mountain_weather():
    st.markdown("#### Mountain Weather & Extreme Conditions")
    st.markdown(
        "Death zone altitudes, minimum temperatures, maximum wind speeds, and precipitation data "
        "for the world's highest and most exposed peaks."
    )

    df = pd.DataFrame(MOUNTAIN_WEATHER)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        coldest = df.loc[df["min_temp_c"].idxmin()]
        st.metric("Coldest", f'{coldest["min_temp_c"]}C ({coldest["name"]})')
    with c2:
        windiest = df.loc[df["max_wind_kmh"].idxmax()]
        st.metric("Windiest", f'{windiest["max_wind_kmh"]} km/h ({windiest["name"]})')
    with c3:
        wettest = df.loc[df["avg_annual_precip_mm"].idxmax()]
        st.metric("Wettest", f'{wettest["avg_annual_precip_mm"]:,} mm ({wettest["name"]})')
    with c4:
        death_zones = len(df[df["death_zone_m"] > 0])
        st.metric("Death Zone Peaks", f"{death_zones}")

    # Temperature chart
    sorted_df = df.sort_values("min_temp_c", ascending=True)
    temp_colors = []
    for _, r in sorted_df.iterrows():
        if r["min_temp_c"] <= -70:
            temp_colors.append("#3b82f6")
        elif r["min_temp_c"] <= -55:
            temp_colors.append("#06b6d4")
        elif r["min_temp_c"] <= -40:
            temp_colors.append("#14b8a6")
        else:
            temp_colors.append("#10b981")

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)
    ax.barh(sorted_df["name"].tolist(), sorted_df["min_temp_c"].tolist(),
            color=temp_colors, edgecolor=temp_colors, alpha=0.85)
    ax.set_xlabel("Minimum Temperature (C)", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Coldest Recorded Temperatures", color=TEXT_COLOR, fontsize=13,
                 fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Wind speed chart
    sorted_wind = df.sort_values("max_wind_kmh", ascending=True)
    wind_colors = []
    for _, r in sorted_wind.iterrows():
        if r["max_wind_kmh"] >= 300:
            wind_colors.append("#ef4444")
        elif r["max_wind_kmh"] >= 200:
            wind_colors.append("#f97316")
        elif r["max_wind_kmh"] >= 150:
            wind_colors.append("#f59e0b")
        else:
            wind_colors.append("#10b981")

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    fig2.patch.set_facecolor(BG_COLOR)
    ax2.set_facecolor(SURFACE_COLOR)
    ax2.barh(sorted_wind["name"].tolist(), sorted_wind["max_wind_kmh"].tolist(),
             color=wind_colors, edgecolor=wind_colors, alpha=0.85)
    ax2.set_xlabel("Max Wind Speed (km/h)", color=TEXT_COLOR, fontsize=10)
    ax2.set_title("Maximum Recorded Wind Speeds", color=TEXT_COLOR, fontsize=13,
                  fontweight="bold", pad=12)
    ax2.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    for spine in ax2.spines.values():
        spine.set_color("#2a3550")
    ax2.grid(axis="x", color="#2a3550", alpha=0.3, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # Map
    st.markdown("---")
    st.markdown("#### Mountain Weather Map")
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#3b82f6; font-size:0.8rem;">&#9679; Extreme Cold (&le;-70C)</span>
        <span style="color:#06b6d4; font-size:0.8rem;">&#9679; Severe Cold (-55 to -70C)</span>
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Extreme Wind (&ge;240 km/h)</span>
        <span style="color:#10b981; font-size:0.8rem;">&#9679; Other</span>
    </div>
    """, unsafe_allow_html=True)

    m = _make_dark_map(center=[35, 50], zoom=3)
    for wx in MOUNTAIN_WEATHER:
        if wx["min_temp_c"] <= -70:
            clr = "#3b82f6"
        elif wx["max_wind_kmh"] >= 240:
            clr = "#ef4444"
        elif wx["min_temp_c"] <= -55:
            clr = "#06b6d4"
        else:
            clr = "#10b981"
        dz = f'{wx["death_zone_m"]:,} m' if wx["death_zone_m"] > 0 else "N/A"
        popup_html = (
            f'<div style="max-width:280px;font-family:sans-serif;">'
            f'<strong style="font-size:1rem;">{escape(wx["name"])}</strong><br/>'
            f'<b>{wx["elevation_m"]:,} m</b><br/>'
            f'Death zone: {dz}<br/>'
            f'Min temp: <b>{wx["min_temp_c"]}C</b><br/>'
            f'Max wind: <b>{wx["max_wind_kmh"]} km/h</b><br/>'
            f'Annual precip: {wx["avg_annual_precip_mm"]:,} mm<br/>'
            f'Climbing season: {escape(wx["climbing_season"])}<br/>'
            f'<span style="font-size:0.8em;color:#8b97b0;">{escape(wx["weather_notes"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[wx["lat"], wx["lon"]],
            radius=max(6, abs(wx["min_temp_c"]) / 8),
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f'{wx["name"]} — {wx["min_temp_c"]}C / {wx["max_wind_kmh"]} km/h',
        ).add_to(m)
    _show_map(m)

    # Death zone explanation
    st.markdown("---")
    st.markdown("#### The Death Zone")
    st.markdown(
        f'<div style="background:{SURFACE_COLOR}; border:1px solid #2a3550; border-radius:8px; '
        f'padding:1rem; margin-bottom:1rem;">'
        f'<div style="color:{ACCENT_RED}; font-weight:700; font-size:1rem; margin-bottom:0.5rem;">'
        f'Above 8,000 m: The Death Zone</div>'
        f'<div style="color:{TEXT_SECONDARY}; font-size:0.85rem;">'
        f'At altitudes above ~8,000 m, the partial pressure of oxygen is roughly one-third '
        f'that at sea level. The human body cannot acclimatize — it is actively dying. '
        f'Climbers spend only hours in the death zone, using supplemental oxygen. '
        f'Without it, cognitive function degrades rapidly, leading to confusion, '
        f'hallucinations, and death. Above 7,500 m, most climbers lose 1-2 kg of body '
        f'mass per day. The summit push from high camp is typically 12-18 hours round trip, '
        f'and most deaths occur on the descent when exhaustion peaks.</div></div>',
        unsafe_allow_html=True,
    )

    # Table
    st.markdown("#### Data Table")
    display_df = df[["name", "elevation_m", "death_zone_m", "min_temp_c",
                     "max_wind_kmh", "avg_annual_precip_mm", "climbing_season",
                     "weather_notes"]].copy()
    display_df.columns = ["Peak", "Elevation (m)", "Death Zone (m)", "Min Temp (C)",
                          "Max Wind (km/h)", "Annual Precip (mm)", "Climbing Season",
                          "Weather Notes"]
    st.dataframe(display_df, width="stretch")
    _csv_download(display_df, "mountain_weather.csv")


# =====================================================================
# MAP MODE DISPATCH
# =====================================================================
MAP_MODES = {
    "Eight-Thousanders": _render_eight_thousanders,
    "Seven Summits": _render_seven_summits,
    "World Mountain Ranges": _render_mountain_ranges,
    "Deadliest Mountains": _render_deadliest,
    "Alpine Huts & Refuges": _render_alpine_huts,
    "Volcanic Peaks": _render_volcanic_peaks,
    "Sacred Mountains": _render_sacred_mountains,
    "Climbing History": _render_climbing_history,
    "Mountain Passes": _render_mountain_passes,
    "Mountain Weather": _render_mountain_weather,
}


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_mountain_maps_tab():
    """Render the Mountains & Peaks of the World tab."""
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>&#9968; Mountains & Peaks of the World</h4>'
        '<p>Highest peaks, mountain ranges, climbing routes & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select map mode",
        list(MAP_MODES.keys()),
        key="mountain_map_mode",
    )

    st.markdown("---")

    # Dispatch to selected mode
    render_fn = MAP_MODES[mode]
    render_fn()
