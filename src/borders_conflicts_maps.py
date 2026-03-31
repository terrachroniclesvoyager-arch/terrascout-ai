# -*- coding: utf-8 -*-
"""
Borders, Walls & Conflicts module for TerraScout AI.
Curated geopolitical data covering border walls, disputed territories,
demilitarized zones, enclaves/exclaves, micronations, active conflicts,
Cold War boundaries, colonial border legacy, maritime disputes, and
divided cities. All data is hardcoded -- no API key required.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =====================================================================
# THEME CONSTANTS
# =====================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_SECONDARY = "#8b97b0"
_BORDER = "#2a3550"
_ACCENT = "#06b6d4"

# =====================================================================
# MODE LIST
# =====================================================================
MAP_MODES = [
    "Border Walls & Fences",
    "Disputed Territories",
    "Demilitarized Zones",
    "Enclaves & Exclaves",
    "Micronations",
    "Active Conflict Zones",
    "Cold War Boundaries",
    "Colonial Border Legacy",
    "Maritime Boundary Disputes",
    "Divided Cities",
]

# =====================================================================
# 1. BORDER WALLS & FENCES  (25+)
# =====================================================================
BORDER_WALLS = [
    {"name": "US-Mexico Border Wall", "country": "United States / Mexico", "lat": 31.95, "lon": -106.45, "length_km": 3145, "status": "Partial", "year_started": 1994, "notes": "Multiple sections; ongoing expansion"},
    {"name": "Israel West Bank Barrier", "country": "Israel / Palestine", "lat": 31.78, "lon": 35.22, "length_km": 708, "status": "Mostly Complete", "year_started": 2002, "notes": "Separation barrier; mix of wall and fence"},
    {"name": "Berlin Wall (Historic)", "country": "Germany", "lat": 52.5163, "lon": 13.3777, "length_km": 155, "status": "Historic (1961-1989)", "year_started": 1961, "notes": "Fell November 9, 1989"},
    {"name": "Korean DMZ Fence", "country": "South Korea / North Korea", "lat": 37.95, "lon": 126.95, "length_km": 250, "status": "Active", "year_started": 1953, "notes": "Most heavily fortified border"},
    {"name": "India-Pakistan LoC Fence", "country": "India / Pakistan", "lat": 34.0, "lon": 74.5, "length_km": 550, "status": "Active", "year_started": 2003, "notes": "Line of Control in Kashmir"},
    {"name": "India-Bangladesh Border Fence", "country": "India / Bangladesh", "lat": 24.0, "lon": 89.0, "length_km": 3200, "status": "Mostly Complete", "year_started": 1993, "notes": "One of the longest border fences"},
    {"name": "Saudi-Yemen Border Barrier", "country": "Saudi Arabia / Yemen", "lat": 17.5, "lon": 44.0, "length_km": 1800, "status": "Active", "year_started": 2004, "notes": "Sand berm and fence"},
    {"name": "Saudi-Iraq Border Barrier", "country": "Saudi Arabia / Iraq", "lat": 29.5, "lon": 43.5, "length_km": 900, "status": "Active", "year_started": 2014, "notes": "Fence and ditch system"},
    {"name": "Morocco-Western Sahara Berm", "country": "Morocco / Western Sahara", "lat": 24.0, "lon": -13.0, "length_km": 2720, "status": "Active", "year_started": 1981, "notes": "Sand wall with landmines"},
    {"name": "Hungary-Serbia Border Fence", "country": "Hungary / Serbia", "lat": 46.17, "lon": 19.9, "length_km": 175, "status": "Active", "year_started": 2015, "notes": "Anti-migration razor wire fence"},
    {"name": "Turkey-Syria Border Wall", "country": "Turkey / Syria", "lat": 36.7, "lon": 38.0, "length_km": 911, "status": "Complete", "year_started": 2015, "notes": "Concrete wall with watchtowers"},
    {"name": "Greece-Turkey Evros Fence", "country": "Greece / Turkey", "lat": 41.67, "lon": 26.32, "length_km": 40, "status": "Active", "year_started": 2012, "notes": "Along Evros/Maritsa river"},
    {"name": "Bulgaria-Turkey Border Fence", "country": "Bulgaria / Turkey", "lat": 41.75, "lon": 26.5, "length_km": 234, "status": "Active", "year_started": 2014, "notes": "Razor wire and barbed wire"},
    {"name": "Ceuta Border Fence", "country": "Spain / Morocco", "lat": 35.89, "lon": -5.32, "length_km": 8, "status": "Active", "year_started": 1993, "notes": "Triple-layered 6m fence"},
    {"name": "Melilla Border Fence", "country": "Spain / Morocco", "lat": 35.29, "lon": -2.94, "length_km": 12, "status": "Active", "year_started": 1998, "notes": "Triple-layered fence with razor wire"},
    {"name": "Belfast Peace Walls", "country": "Northern Ireland (UK)", "lat": 54.6, "lon": -5.93, "length_km": 34, "status": "Active", "year_started": 1969, "notes": "Separate Catholic and Protestant areas"},
    {"name": "Egypt-Gaza Border Barrier", "country": "Egypt / Gaza", "lat": 31.25, "lon": 34.22, "length_km": 14, "status": "Active", "year_started": 2009, "notes": "Steel wall with underground barrier"},
    {"name": "Uzbekistan-Kyrgyzstan Fence", "country": "Uzbekistan / Kyrgyzstan", "lat": 41.0, "lon": 71.0, "length_km": 870, "status": "Active", "year_started": 1999, "notes": "Barbed wire and minefields"},
    {"name": "Botswana-Zimbabwe Fence", "country": "Botswana / Zimbabwe", "lat": -21.5, "lon": 27.5, "length_km": 500, "status": "Active", "year_started": 2003, "notes": "Electric fence, anti-migration"},
    {"name": "China-North Korea Border Fence", "country": "China / North Korea", "lat": 42.0, "lon": 129.0, "length_km": 1416, "status": "Active", "year_started": 2006, "notes": "Barbed wire along Yalu/Tumen rivers"},
    {"name": "Iran-Pakistan Border Barrier", "country": "Iran / Pakistan", "lat": 27.0, "lon": 63.0, "length_km": 700, "status": "Partial", "year_started": 2011, "notes": "Concrete wall sections"},
    {"name": "Kuwait-Iraq Border Barrier", "country": "Kuwait / Iraq", "lat": 29.7, "lon": 47.5, "length_km": 217, "status": "Active", "year_started": 1991, "notes": "Trench, berm, and wire fence"},
    {"name": "Pakistan-Afghanistan Fence", "country": "Pakistan / Afghanistan", "lat": 33.5, "lon": 70.0, "length_km": 2670, "status": "Mostly Complete", "year_started": 2017, "notes": "Durand Line fence"},
    {"name": "Lithuania-Belarus Border Fence", "country": "Lithuania / Belarus", "lat": 54.3, "lon": 26.0, "length_km": 550, "status": "Active", "year_started": 2021, "notes": "Razor wire; migration crisis response"},
    {"name": "Poland-Belarus Border Fence", "country": "Poland / Belarus", "lat": 53.2, "lon": 23.8, "length_km": 186, "status": "Complete", "year_started": 2022, "notes": "5.5m steel wall"},
    {"name": "Finland-Russia Border Fence", "country": "Finland / Russia", "lat": 62.0, "lon": 30.0, "length_km": 200, "status": "Under Construction", "year_started": 2023, "notes": "Pilot sections on southeastern border"},
    {"name": "Latvia-Belarus Border Fence", "country": "Latvia / Belarus", "lat": 56.0, "lon": 27.5, "length_km": 173, "status": "Active", "year_started": 2022, "notes": "Razor wire fence"},
]

# =====================================================================
# 2. DISPUTED TERRITORIES  (30+)
# =====================================================================
DISPUTED_TERRITORIES = [
    {"name": "Kashmir", "claimants": "India, Pakistan, China", "lat": 34.5, "lon": 76.0, "status": "Active dispute", "since": 1947, "area_km2": 222236, "notes": "Divided between India (Jammu & Kashmir), Pakistan (Azad Kashmir, Gilgit-Baltistan), China (Aksai Chin)"},
    {"name": "Crimea", "claimants": "Ukraine, Russia", "lat": 44.95, "lon": 34.1, "status": "Annexed by Russia 2014", "since": 2014, "area_km2": 27000, "notes": "Internationally recognized as Ukraine; annexed by Russia"},
    {"name": "Western Sahara", "claimants": "Morocco, Sahrawi Republic (Polisario)", "lat": 24.5, "lon": -13.0, "status": "Non-self-governing territory", "since": 1975, "area_km2": 266000, "notes": "Mostly controlled by Morocco; UN-listed non-self-governing territory"},
    {"name": "Falkland Islands / Malvinas", "claimants": "UK, Argentina", "lat": -51.75, "lon": -59.0, "status": "British Overseas Territory", "since": 1833, "area_km2": 12173, "notes": "1982 war; UK administration; Argentina maintains sovereignty claim"},
    {"name": "Taiwan / Republic of China", "claimants": "PRC, ROC (Taiwan)", "lat": 23.7, "lon": 121.0, "status": "Self-governing; disputed sovereignty", "since": 1949, "area_km2": 36193, "notes": "Governed independently; PRC claims sovereignty"},
    {"name": "South China Sea (Spratly Islands)", "claimants": "China, Vietnam, Philippines, Malaysia, Brunei, Taiwan", "lat": 10.0, "lon": 114.0, "status": "Active multi-party dispute", "since": 1947, "area_km2": 425000, "notes": "Artificial islands, military buildup; UNCLOS arbitration 2016"},
    {"name": "Golan Heights", "claimants": "Israel, Syria", "lat": 33.0, "lon": 35.75, "status": "Israeli-occupied since 1967", "since": 1967, "area_km2": 1800, "notes": "Occupied by Israel in Six-Day War; US recognized sovereignty 2019"},
    {"name": "Nagorno-Karabakh", "claimants": "Azerbaijan, Armenia", "lat": 39.8, "lon": 46.75, "status": "Azerbaijani control since 2023", "since": 1988, "area_km2": 4400, "notes": "2020 war; 2023 Azerbaijani offensive ended Armenian control"},
    {"name": "Transnistria", "claimants": "Moldova, Transnistrian PMR", "lat": 46.85, "lon": 29.6, "status": "De facto independent", "since": 1990, "area_km2": 4163, "notes": "Russian troops present; not internationally recognized"},
    {"name": "Abkhazia", "claimants": "Georgia, Abkhazia", "lat": 43.0, "lon": 41.0, "status": "De facto independent", "since": 1992, "area_km2": 8665, "notes": "Recognized by Russia and a few states"},
    {"name": "South Ossetia", "claimants": "Georgia, South Ossetia", "lat": 42.23, "lon": 43.97, "status": "De facto independent", "since": 1991, "area_km2": 3900, "notes": "2008 war with Georgia; Russian recognition"},
    {"name": "Northern Cyprus (TRNC)", "claimants": "Cyprus, Turkey/TRNC", "lat": 35.2, "lon": 33.4, "status": "De facto independent", "since": 1974, "area_km2": 3355, "notes": "Recognized only by Turkey"},
    {"name": "Arunachal Pradesh / South Tibet", "claimants": "India, China", "lat": 28.2, "lon": 94.7, "status": "Administered by India", "since": 1914, "area_km2": 83743, "notes": "China claims as South Tibet; McMahon Line dispute"},
    {"name": "Kuril Islands / Northern Territories", "claimants": "Russia, Japan", "lat": 44.5, "lon": 146.5, "status": "Russian administration", "since": 1945, "area_km2": 10503, "notes": "Soviet Union seized 1945; no WWII peace treaty signed"},
    {"name": "Dokdo / Takeshima", "claimants": "South Korea, Japan", "lat": 37.24, "lon": 131.87, "status": "South Korean control", "since": 1954, "area_km2": 0.19, "notes": "Islets in Sea of Japan/East Sea"},
    {"name": "Senkaku / Diaoyu Islands", "claimants": "Japan, China, Taiwan", "lat": 25.74, "lon": 123.47, "status": "Japanese administration", "since": 1895, "area_km2": 6.3, "notes": "Uninhabited; East China Sea; frequent naval standoffs"},
    {"name": "Gibraltar", "claimants": "UK, Spain", "lat": 36.14, "lon": -5.35, "status": "British Overseas Territory", "since": 1713, "area_km2": 6.7, "notes": "Treaty of Utrecht; Spain seeks return"},
    {"name": "Ceuta", "claimants": "Spain, Morocco", "lat": 35.89, "lon": -5.31, "status": "Spanish autonomous city", "since": 1668, "area_km2": 18.5, "notes": "Morocco claims; Spanish enclave in Africa"},
    {"name": "Melilla", "claimants": "Spain, Morocco", "lat": 35.29, "lon": -2.94, "status": "Spanish autonomous city", "since": 1497, "area_km2": 12.3, "notes": "Morocco claims; Spanish enclave in Africa"},
    {"name": "Somaliland", "claimants": "Somalia, Somaliland", "lat": 9.56, "lon": 44.06, "status": "De facto independent", "since": 1991, "area_km2": 176120, "notes": "Self-declared independent; no UN recognition"},
    {"name": "Donbas (Donetsk & Luhansk)", "claimants": "Ukraine, Russia", "lat": 48.0, "lon": 38.5, "status": "Conflict zone; Russian occupation", "since": 2014, "area_km2": 52300, "notes": "Russia annexed 2022; internationally recognized as Ukraine"},
    {"name": "Zaporizhzhia & Kherson", "claimants": "Ukraine, Russia", "lat": 47.0, "lon": 35.0, "status": "Partly Russian-occupied", "since": 2022, "area_km2": 45000, "notes": "Russia claims annexation; Ukraine holds parts"},
    {"name": "Paracel Islands", "claimants": "China, Vietnam, Taiwan", "lat": 16.5, "lon": 112.0, "status": "Chinese control", "since": 1974, "area_km2": 7.75, "notes": "Seized by China from South Vietnam 1974"},
    {"name": "Scarborough Shoal", "claimants": "China, Philippines", "lat": 15.15, "lon": 117.76, "status": "Disputed", "since": 2012, "area_km2": 150, "notes": "China controls since 2012 standoff"},
    {"name": "Aksai Chin", "claimants": "India, China", "lat": 35.0, "lon": 79.0, "status": "Chinese administration", "since": 1962, "area_km2": 37244, "notes": "Occupied by China since 1962 war"},
    {"name": "Essequibo", "claimants": "Venezuela, Guyana", "lat": 5.0, "lon": -59.0, "status": "Guyana administration; ICJ case", "since": 1899, "area_km2": 159542, "notes": "Venezuela claims two-thirds of Guyana territory"},
    {"name": "Hans Island / Tartupaluk", "claimants": "Canada, Denmark (resolved 2022)", "lat": 80.83, "lon": -66.46, "status": "Resolved (split 2022)", "since": 1973, "area_km2": 1.3, "notes": "Divided by treaty June 2022; first land border Canada-EU"},
    {"name": "Brcko District", "claimants": "Federation BiH, Republika Srpska", "lat": 44.87, "lon": 18.81, "status": "Self-governing district", "since": 1995, "area_km2": 493, "notes": "Condominium of both BiH entities since Dayton"},
    {"name": "Ilemi Triangle", "claimants": "Kenya, South Sudan, Ethiopia", "lat": 4.5, "lon": 36.0, "status": "Kenyan administration", "since": 1914, "area_km2": 14000, "notes": "Tri-state border area; unresolved colonial legacy"},
    {"name": "Hala'ib Triangle", "claimants": "Egypt, Sudan", "lat": 22.2, "lon": 36.4, "status": "Egyptian administration", "since": 1902, "area_km2": 20580, "notes": "Overlapping colonial-era boundaries"},
    {"name": "Preah Vihear Temple", "claimants": "Cambodia, Thailand", "lat": 14.39, "lon": 104.68, "status": "Cambodian (ICJ 1962, 2013)", "since": 1904, "area_km2": 4.6, "notes": "ICJ awarded temple to Cambodia; surrounding area disputed"},
]

# =====================================================================
# 3. DEMILITARIZED ZONES  (10+)
# =====================================================================
DEMILITARIZED_ZONES = [
    {"name": "Korean DMZ", "countries": "North Korea / South Korea", "lat": 37.95, "lon": 126.95, "length_km": 250, "width_km": 4, "established": 1953, "status": "Active", "notes": "Most fortified border; armistice line; Panmunjom/JSA"},
    {"name": "Cyprus UN Buffer Zone (Green Line)", "countries": "Cyprus / Northern Cyprus", "lat": 35.17, "lon": 33.36, "length_km": 180, "width_km": 3.5, "established": 1974, "status": "Active UNFICYP", "notes": "Divides Nicosia; UN peacekeepers since 1964"},
    {"name": "Golan Heights UNDOF Zone", "countries": "Israel / Syria", "lat": 33.1, "lon": 35.8, "length_km": 80, "width_km": 10, "established": 1974, "status": "Active UNDOF", "notes": "UN Disengagement Observer Force since 1974"},
    {"name": "Sinai MFO Zone", "countries": "Egypt / Israel", "lat": 29.5, "lon": 34.5, "length_km": 250, "width_km": 40, "established": 1982, "status": "Active MFO", "notes": "Multinational Force and Observers since Camp David Accords"},
    {"name": "Vietnam DMZ (Historic)", "countries": "North Vietnam / South Vietnam", "lat": 16.9, "lon": 107.1, "length_km": 100, "width_km": 5, "established": 1954, "status": "Historic (ended 1976)", "notes": "17th parallel; Ben Hai River; Geneva Accords"},
    {"name": "Antarctica (Demilitarized Continent)", "countries": "International", "lat": -85.0, "lon": 0.0, "length_km": 0, "width_km": 0, "established": 1959, "status": "Active Treaty", "notes": "Antarctic Treaty bans military activity; 54 signatory nations"},
    {"name": "Aland Islands", "countries": "Finland", "lat": 60.1, "lon": 19.9, "length_km": 0, "width_km": 0, "established": 1921, "status": "Active", "notes": "Demilitarized Swedish-speaking autonomous region of Finland"},
    {"name": "Svalbard", "countries": "Norway (international treaty)", "lat": 78.2, "lon": 15.6, "length_km": 0, "width_km": 0, "established": 1920, "status": "Active Treaty", "notes": "Spitsbergen Treaty; demilitarized; open to all signatories"},
    {"name": "Rhineland (Historic)", "countries": "Germany", "lat": 50.9, "lon": 6.96, "length_km": 400, "width_km": 50, "established": 1919, "status": "Historic (violated 1936)", "notes": "Treaty of Versailles; remilitarized by Hitler March 1936"},
    {"name": "Iraq-Kuwait DMZ (Historic)", "countries": "Iraq / Kuwait", "lat": 29.5, "lon": 47.5, "length_km": 200, "width_km": 15, "established": 1991, "status": "Ended 2003", "notes": "UNIKOM monitored after Gulf War; dissolved after 2003 Iraq War"},
    {"name": "Temporary Security Zone Eritrea (Historic)", "countries": "Ethiopia / Eritrea", "lat": 15.0, "lon": 39.5, "length_km": 1000, "width_km": 25, "established": 2000, "status": "Ended 2018", "notes": "UNMEE buffer zone; peace agreement 2018"},
]

# =====================================================================
# 4. ENCLAVES & EXCLAVES  (15+)
# =====================================================================
ENCLAVES_EXCLAVES = [
    {"name": "Kaliningrad", "parent": "Russia", "surrounded_by": "Lithuania / Poland / Baltic Sea", "lat": 54.71, "lon": 20.51, "type": "Exclave", "area_km2": 15100, "population": 1013000, "notes": "Former Konigsberg; Russian exclave between EU/NATO states"},
    {"name": "Ceuta", "parent": "Spain", "surrounded_by": "Morocco", "lat": 35.89, "lon": -5.31, "type": "Exclave", "area_km2": 18.5, "population": 84000, "notes": "Spanish autonomous city on African coast"},
    {"name": "Melilla", "parent": "Spain", "surrounded_by": "Morocco", "lat": 35.29, "lon": -2.94, "type": "Exclave", "area_km2": 12.3, "population": 87000, "notes": "Spanish autonomous city on African coast"},
    {"name": "Baarle-Hertog / Baarle-Nassau", "parent": "Belgium / Netherlands", "surrounded_by": "Netherlands / Belgium", "lat": 51.44, "lon": 4.93, "type": "Counter-enclaves", "area_km2": 7.5, "population": 9500, "notes": "22 Belgian exclaves in Netherlands, 7 Dutch counter-enclaves in Belgium"},
    {"name": "Llivia", "parent": "Spain", "surrounded_by": "France", "lat": 42.46, "lon": 1.98, "type": "Exclave", "area_km2": 12.8, "population": 1500, "notes": "Spanish town in French Pyrenees; Treaty of the Pyrenees 1659"},
    {"name": "Campione d'Italia", "parent": "Italy", "surrounded_by": "Switzerland", "lat": 45.97, "lon": 8.97, "type": "Exclave", "area_km2": 1.6, "population": 2100, "notes": "Italian exclave on Lake Lugano; uses Swiss franc"},
    {"name": "Busingen am Hochrhein", "parent": "Germany", "surrounded_by": "Switzerland", "lat": 47.7, "lon": 8.69, "type": "Exclave", "area_km2": 7.6, "population": 1400, "notes": "German exclave; Swiss customs area; Treaty of Verdun origin"},
    {"name": "Nakhchivan", "parent": "Azerbaijan", "surrounded_by": "Armenia / Iran / Turkey", "lat": 39.21, "lon": 45.41, "type": "Exclave", "area_km2": 5500, "population": 460000, "notes": "Azerbaijani autonomous republic; separated by Armenia"},
    {"name": "Oecusse (Ambeno)", "parent": "Timor-Leste", "surrounded_by": "Indonesia (West Timor)", "lat": -9.2, "lon": 124.4, "type": "Exclave", "area_km2": 815, "population": 68000, "notes": "East Timorese exclave in Indonesian West Timor"},
    {"name": "Musandam Peninsula", "parent": "Oman", "surrounded_by": "UAE", "lat": 26.2, "lon": 56.25, "type": "Exclave", "area_km2": 1800, "population": 31000, "notes": "Omani territory at Strait of Hormuz; separated by UAE"},
    {"name": "Cabinda", "parent": "Angola", "surrounded_by": "Congo-Brazzaville / DRC", "lat": -5.55, "lon": 12.19, "type": "Exclave", "area_km2": 7270, "population": 700000, "notes": "Oil-rich Angolan exclave; separatist movement FLEC"},
    {"name": "Dahagram-Angarpota", "parent": "Bangladesh", "surrounded_by": "India", "lat": 26.32, "lon": 88.74, "type": "Enclave", "area_km2": 18.7, "population": 20000, "notes": "Last remaining Bangladesh enclave in India after 2015 exchange"},
    {"name": "Cooch Behar Enclaves (Historic)", "parent": "India / Bangladesh", "surrounded_by": "Each other", "lat": 26.3, "lon": 89.3, "type": "Former Counter-enclaves", "area_km2": 120, "population": 50000, "notes": "162 enclaves exchanged in 2015 Land Boundary Agreement"},
    {"name": "Point Roberts", "parent": "United States", "surrounded_by": "Canada (BC)", "lat": 48.98, "lon": -123.06, "type": "Practical exclave", "area_km2": 12.7, "population": 1300, "notes": "US territory south of 49th parallel accessible only via Canada"},
    {"name": "Northwest Angle", "parent": "United States", "surrounded_by": "Canada (Manitoba / Lake of the Woods)", "lat": 49.38, "lon": -95.15, "type": "Practical exclave", "area_km2": 318, "population": 119, "notes": "Northernmost point in contiguous US; accessible by road through Canada"},
    {"name": "Jungholz", "parent": "Austria", "surrounded_by": "Germany (Bavaria)", "lat": 47.58, "lon": 10.45, "type": "Practical exclave", "area_km2": 7.0, "population": 300, "notes": "Connected to Austria only at a single point"},
    {"name": "Kleinwalsertal", "parent": "Austria", "surrounded_by": "Germany (Bavaria)", "lat": 47.35, "lon": 10.18, "type": "Practical exclave", "area_km2": 97, "population": 5000, "notes": "Accessible by road only from Germany"},
]

# =====================================================================
# 5. MICRONATIONS  (20+)
# =====================================================================
MICRONATIONS = [
    {"name": "Principality of Sealand", "lat": 51.89, "lon": 1.48, "founded": 1967, "population": 27, "area_m2": 4000, "claimed_by": "Paddy Roy Bates", "notes": "Former WWII sea fort; North Sea; self-declared sovereignty"},
    {"name": "Republic of Liberland", "lat": 45.77, "lon": 18.87, "founded": 2015, "population": 0, "area_m2": 7000000, "claimed_by": "Vit Jedlicka", "notes": "Gornja Siga on Serbia-Croatia border; terra nullius claim"},
    {"name": "Republic of Molossia", "lat": 39.24, "lon": -119.59, "founded": 1977, "population": 35, "area_m2": 55000, "claimed_by": "Kevin Baugh", "notes": "Dayton, Nevada, USA; complete with customs, navy, space program"},
    {"name": "Principality of Hutt River (Dissolved)", "lat": -28.07, "lon": 114.49, "founded": 1970, "population": 0, "area_m2": 75000000, "claimed_by": "Leonard Casley", "notes": "Western Australia; dissolved 2020; tax dispute origin"},
    {"name": "Kingdom of North Sudan (Bir Tawil)", "lat": 21.87, "lon": 33.75, "founded": 2014, "population": 0, "area_m2": 2060000000, "claimed_by": "Jeremiah Heaton", "notes": "Bir Tawil triangle; unclaimed by Egypt and Sudan"},
    {"name": "Principality of Seborga", "lat": 43.83, "lon": 7.7, "founded": 1963, "population": 320, "area_m2": 14000000, "claimed_by": "Giorgio Carbone", "notes": "Ligurian village in Italy claiming historic sovereignty"},
    {"name": "Republic of Uzupis", "lat": 54.68, "lon": 25.29, "founded": 1997, "population": 7000, "area_m2": 600000, "claimed_by": "Artists' collective", "notes": "Vilnius, Lithuania; bohemian artists' quarter with constitution"},
    {"name": "Freetown Christiania", "lat": 55.67, "lon": 12.6, "founded": 1971, "population": 900, "area_m2": 340000, "claimed_by": "Commune residents", "notes": "Copenhagen, Denmark; self-governing commune"},
    {"name": "Conch Republic", "lat": 24.56, "lon": -81.8, "founded": 1982, "population": 25000, "area_m2": 0, "claimed_by": "Key West, Florida", "notes": "Tongue-in-cheek secession from USA over road blockade"},
    {"name": "Principality of Wirtland", "lat": 0.0, "lon": 0.0, "founded": 2008, "population": 5000, "area_m2": 0, "claimed_by": "Online community", "notes": "First sovereign cyber-country; no physical territory"},
    {"name": "Kingdom of Lovely", "lat": 51.49, "lon": -0.01, "founded": 2005, "population": 58000, "area_m2": 50, "claimed_by": "Danny Wallace", "notes": "London flat; BBC TV show How to Start Your Own Country"},
    {"name": "Republic of Kugelmugel", "lat": 48.22, "lon": 16.4, "founded": 1984, "population": 1, "area_m2": 8, "claimed_by": "Edwin Lipburger", "notes": "Spherical house in Vienna Prater park; art project"},
    {"name": "Akhzivland", "lat": 33.05, "lon": 35.1, "founded": 1971, "population": 2, "area_m2": 10000, "claimed_by": "Eli Avivi", "notes": "Beach in northern Israel; self-declared micronation"},
    {"name": "Grand Duchy of Westarctica", "lat": -78.0, "lon": -100.0, "founded": 2001, "population": 0, "area_m2": 1610000000000, "claimed_by": "Travis McHenry", "notes": "Claims Marie Byrd Land in Antarctica; unclaimed territory"},
    {"name": "Ladonia", "lat": 56.27, "lon": 12.54, "founded": 1996, "population": 0, "area_m2": 10000, "claimed_by": "Lars Vilks", "notes": "Art sculptures in Kullaberg Nature Reserve, Sweden"},
    {"name": "Elleore", "lat": 55.75, "lon": 12.07, "founded": 1944, "population": 0, "area_m2": 15000, "claimed_by": "School teachers", "notes": "Island in Roskilde Fjord, Denmark; tongue-in-cheek kingdom"},
    {"name": "Principality of Monaco (comparison)", "lat": 43.73, "lon": 7.42, "founded": 1297, "population": 39000, "area_m2": 2020000, "claimed_by": "House of Grimaldi", "notes": "Real microstate for scale comparison; UN member"},
    {"name": "Republic of Minerva (Historic)", "lat": -21.38, "lon": -178.93, "founded": 1972, "population": 0, "area_m2": 0, "claimed_by": "Michael Oliver", "notes": "Artificial island on Minerva Reefs; claimed by Tonga; demolished"},
    {"name": "Filettino", "lat": 41.89, "lon": 13.32, "founded": 2011, "population": 550, "area_m2": 69000000, "claimed_by": "Mayor Luca Sellari", "notes": "Italian village threatened independence over austerity mergers"},
    {"name": "Forvik", "lat": 60.25, "lon": -1.36, "founded": 2008, "population": 1, "area_m2": 10000, "claimed_by": "Stuart Hill", "notes": "Island in Shetland, Scotland; claims Crown dependency status"},
    {"name": "Austenasia", "lat": 51.35, "lon": -0.3, "founded": 2008, "population": 30, "area_m2": 200, "claimed_by": "Jonathan Austen", "notes": "London suburb; active government and diplomatic corps"},
]

# =====================================================================
# 6. ACTIVE CONFLICT ZONES  (15+)
# =====================================================================
ACTIVE_CONFLICTS = [
    {"name": "Russia-Ukraine War", "lat": 48.5, "lon": 37.5, "region": "Eastern Europe", "start_year": 2022, "type": "Interstate war", "severity": "High", "casualties_est": "100,000+", "notes": "Full-scale Russian invasion of Ukraine; largest European war since WWII"},
    {"name": "Gaza Conflict", "lat": 31.35, "lon": 34.31, "region": "Middle East", "start_year": 2023, "type": "Armed conflict", "severity": "High", "casualties_est": "40,000+", "notes": "Israel-Hamas war following October 7 attacks"},
    {"name": "Sudan Civil War", "lat": 15.6, "lon": 32.5, "region": "East Africa", "start_year": 2023, "type": "Civil war", "severity": "High", "casualties_est": "15,000+", "notes": "SAF vs RSF; humanitarian catastrophe; Darfur violence"},
    {"name": "Myanmar Civil War", "lat": 19.75, "lon": 96.1, "region": "Southeast Asia", "start_year": 2021, "type": "Civil war", "severity": "High", "casualties_est": "50,000+", "notes": "Post-coup resistance; ethnic armed organizations vs junta"},
    {"name": "Ethiopian Internal Conflicts", "lat": 9.0, "lon": 38.7, "region": "East Africa", "start_year": 2020, "type": "Internal armed conflict", "severity": "Medium", "casualties_est": "600,000+", "notes": "Tigray ceasefire 2022; Amhara/Oromia ongoing"},
    {"name": "Sahel Insurgency (Mali/Burkina Faso/Niger)", "lat": 14.0, "lon": -2.0, "region": "West Africa", "start_year": 2012, "type": "Insurgency", "severity": "High", "casualties_est": "30,000+", "notes": "Jihadist groups; military coups; French withdrawal"},
    {"name": "Somali Civil War", "lat": 2.05, "lon": 45.3, "region": "East Africa", "start_year": 1991, "type": "Civil war / insurgency", "severity": "Medium", "casualties_est": "500,000+", "notes": "Al-Shabaab insurgency; clan conflicts; fragile government"},
    {"name": "Yemeni Civil War", "lat": 15.35, "lon": 44.2, "region": "Middle East", "start_year": 2014, "type": "Civil war", "severity": "Medium", "casualties_est": "377,000+", "notes": "Houthi vs government; Saudi-led coalition; ceasefire talks"},
    {"name": "Syrian Civil War", "lat": 34.8, "lon": 38.99, "region": "Middle East", "start_year": 2011, "type": "Civil war", "severity": "Medium", "casualties_est": "500,000+", "notes": "Multiple factions; IS remnants; Turkish operations in north"},
    {"name": "DR Congo (M23 & Eastern Conflicts)", "lat": -1.5, "lon": 29.2, "region": "Central Africa", "start_year": 1998, "type": "Armed conflict", "severity": "High", "casualties_est": "6,000,000+", "notes": "M23, ADF, and dozens of armed groups in eastern provinces"},
    {"name": "Colombian Internal Conflict", "lat": 4.6, "lon": -74.08, "region": "South America", "start_year": 1964, "type": "Internal armed conflict", "severity": "Low", "casualties_est": "260,000+", "notes": "Post-FARC deal; ELN, FARC dissidents, drug cartels"},
    {"name": "Afghanistan Taliban Governance", "lat": 34.5, "lon": 69.2, "region": "Central Asia", "start_year": 2021, "type": "Post-conflict governance", "severity": "Low", "casualties_est": "N/A", "notes": "Taliban rule; IS-K attacks; humanitarian crisis"},
    {"name": "Iraq Residual Conflict", "lat": 33.3, "lon": 44.4, "region": "Middle East", "start_year": 2003, "type": "Post-conflict / insurgency", "severity": "Low", "casualties_est": "200,000+", "notes": "IS remnants; militia activity; political instability"},
    {"name": "Nigeria (Boko Haram & Banditry)", "lat": 11.0, "lon": 13.0, "region": "West Africa", "start_year": 2009, "type": "Insurgency / banditry", "severity": "Medium", "casualties_est": "350,000+", "notes": "Boko Haram/ISWAP in northeast; banditry in northwest"},
    {"name": "Mozambique (Cabo Delgado)", "lat": -12.3, "lon": 40.4, "region": "Southern Africa", "start_year": 2017, "type": "Insurgency", "severity": "Medium", "casualties_est": "4,000+", "notes": "IS-affiliated insurgents; gas project disruption"},
    {"name": "Haiti Gang Violence", "lat": 18.54, "lon": -72.34, "region": "Caribbean", "start_year": 2021, "type": "Gang warfare / state collapse", "severity": "Medium", "casualties_est": "5,000+", "notes": "Gang coalitions control Port-au-Prince; multinational intervention"},
]

# =====================================================================
# 7. COLD WAR BOUNDARIES
# =====================================================================
COLD_WAR_ITEMS = [
    {"name": "Berlin Wall", "lat": 52.5163, "lon": 13.3777, "type": "Wall", "bloc": "Iron Curtain", "years": "1961-1989", "status": "Demolished", "color": "#ef4444", "notes": "155 km wall dividing East/West Berlin; 140+ killed crossing"},
    {"name": "Inner German Border", "lat": 51.0, "lon": 11.5, "type": "Border fortification", "bloc": "Iron Curtain", "years": "1949-1990", "status": "Demolished", "color": "#ef4444", "notes": "1,393 km; death strip, mines, auto-firing devices"},
    {"name": "Iron Curtain - Hungary/Austria", "lat": 47.5, "lon": 16.5, "type": "Border fence", "bloc": "Iron Curtain", "years": "1949-1989", "status": "Removed", "color": "#ef4444", "notes": "First breach: Pan-European Picnic, August 1989"},
    {"name": "Iron Curtain - Czechoslovakia/Austria", "lat": 48.7, "lon": 16.0, "type": "Border fence", "bloc": "Iron Curtain", "years": "1948-1989", "status": "Removed", "color": "#ef4444", "notes": "Electric fences and minefields along border"},
    {"name": "Iron Curtain - Bulgaria/Greece/Turkey", "lat": 41.7, "lon": 26.0, "type": "Border fence", "bloc": "Iron Curtain", "years": "1949-1989", "status": "Removed", "color": "#ef4444", "notes": "Heavily mined; many killed attempting to cross"},
    {"name": "NATO HQ Brussels", "lat": 50.88, "lon": 4.42, "type": "Alliance HQ", "bloc": "NATO", "years": "1949-present", "status": "Active", "color": "#3b82f6", "notes": "Western alliance headquarters"},
    {"name": "Warsaw Pact HQ Moscow", "lat": 55.75, "lon": 37.62, "type": "Alliance HQ", "bloc": "Warsaw Pact", "years": "1955-1991", "status": "Dissolved", "color": "#dc2626", "notes": "Eastern bloc military alliance; dissolved July 1991"},
    {"name": "Fulda Gap", "lat": 50.55, "lon": 9.68, "type": "Strategic corridor", "bloc": "Cold War flashpoint", "years": "1945-1990", "status": "Historic", "color": "#f59e0b", "notes": "Expected Soviet invasion route into West Germany"},
    {"name": "GIUK Gap", "lat": 63.0, "lon": -15.0, "type": "Naval chokepoint", "bloc": "NATO", "years": "1945-present", "status": "Active", "color": "#3b82f6", "notes": "Greenland-Iceland-UK gap; submarine detection"},
    {"name": "Korean DMZ (Cold War)", "lat": 37.95, "lon": 126.95, "type": "DMZ", "bloc": "Cold War proxy", "years": "1953-present", "status": "Active", "color": "#f59e0b", "notes": "Korean War armistice; still technically at war"},
    {"name": "Bay of Pigs / Cuba", "lat": 22.1, "lon": -79.0, "type": "Conflict zone", "bloc": "Cold War flashpoint", "years": "1961-1962", "status": "Historic", "color": "#f59e0b", "notes": "Failed invasion 1961; Missile Crisis 1962"},
    {"name": "Vietnam DMZ", "lat": 16.9, "lon": 107.1, "type": "DMZ", "bloc": "Cold War proxy", "years": "1954-1976", "status": "Historic", "color": "#f59e0b", "notes": "17th parallel; Geneva Accords 1954"},
    {"name": "Four Sector Berlin", "lat": 52.5, "lon": 13.4, "type": "Occupied city", "bloc": "Four powers", "years": "1945-1990", "status": "Reunified", "color": "#a855f7", "notes": "US, UK, French, Soviet sectors; Checkpoint Charlie"},
    {"name": "Guantanamo Bay", "lat": 19.9, "lon": -75.1, "type": "US naval base", "bloc": "NATO / US", "years": "1903-present", "status": "Active", "color": "#3b82f6", "notes": "US military base on Cuban soil; Cold War significance"},
    {"name": "Bornholm (Baltic Watch)", "lat": 55.13, "lon": 14.92, "type": "Strategic island", "bloc": "NATO", "years": "1945-present", "status": "Active", "color": "#3b82f6", "notes": "Danish island; Soviet liberation 1945; NATO monitoring"},
]

# =====================================================================
# 8. COLONIAL BORDER LEGACY
# =====================================================================
COLONIAL_BORDERS = [
    {"name": "Scramble for Africa - Berlin Conference Lines", "lat": 0.0, "lon": 20.0, "colonial_power": "Multiple European", "year": 1884, "region": "Africa", "impact": "High", "notes": "1884-85 conference drew borders ignoring ethnic/tribal boundaries; affects 50+ states"},
    {"name": "Sykes-Picot Line", "lat": 34.0, "lon": 39.0, "colonial_power": "UK / France", "year": 1916, "region": "Middle East", "impact": "High", "notes": "Secret agreement dividing Ottoman Empire; created Iraq, Syria, Lebanon, Jordan"},
    {"name": "Durand Line (Afghanistan-Pakistan)", "lat": 33.5, "lon": 70.0, "colonial_power": "British India", "year": 1893, "region": "South Asia", "impact": "High", "notes": "Divided Pashtun tribal areas; Afghanistan never recognized it"},
    {"name": "McMahon Line (India-China)", "lat": 28.0, "lon": 94.0, "colonial_power": "British India", "year": 1914, "region": "South/East Asia", "impact": "High", "notes": "Simla Convention; China rejects; basis of Arunachal Pradesh dispute"},
    {"name": "Radcliffe Line (India-Pakistan Partition)", "lat": 30.0, "lon": 73.0, "colonial_power": "British India", "year": 1947, "region": "South Asia", "impact": "Very High", "notes": "Cyril Radcliffe divided Punjab and Bengal; 1-2 million died in partition"},
    {"name": "49th Parallel (US-Canada)", "lat": 49.0, "lon": -110.0, "colonial_power": "UK / USA", "year": 1818, "region": "North America", "impact": "Low", "notes": "Oregon Treaty 1846 extended to Pacific; world's longest undefended border"},
    {"name": "Mason-Dixon Line", "lat": 39.72, "lon": -77.0, "colonial_power": "British Colonial", "year": 1767, "region": "North America", "impact": "Medium", "notes": "Pennsylvania-Maryland border; symbolic North/South divide in US"},
    {"name": "Curzon Line (Poland)", "lat": 52.0, "lon": 24.0, "colonial_power": "UK / Allied Powers", "year": 1919, "region": "Eastern Europe", "impact": "High", "notes": "Proposed Polish-Soviet border; basis for 1945 border shift"},
    {"name": "Oder-Neisse Line (Germany-Poland)", "lat": 52.0, "lon": 14.5, "colonial_power": "Allied Powers", "year": 1945, "region": "Central Europe", "impact": "High", "notes": "Post-WWII German-Polish border; millions displaced"},
    {"name": "Congo Free State Borders", "lat": -4.0, "lon": 22.0, "colonial_power": "Belgium (Leopold II)", "year": 1885, "region": "Central Africa", "impact": "Very High", "notes": "Artificial borders; brutal exploitation; 10 million deaths estimated"},
    {"name": "Nigeria - Amalgamation", "lat": 9.0, "lon": 7.5, "colonial_power": "British", "year": 1914, "region": "West Africa", "impact": "High", "notes": "Northern and Southern protectorates merged; religious/ethnic tensions persist"},
    {"name": "Rwanda-Burundi Division", "lat": -2.5, "lon": 29.5, "colonial_power": "Germany / Belgium", "year": 1916, "region": "East Africa", "impact": "Very High", "notes": "Colonial-era Hutu/Tutsi classification led to 1994 genocide"},
    {"name": "Balfour Declaration (Palestine)", "lat": 31.78, "lon": 35.22, "colonial_power": "British", "year": 1917, "region": "Middle East", "impact": "Very High", "notes": "Promised Jewish homeland in Palestine; foundation of Israel-Palestine conflict"},
    {"name": "Treaty of Tordesillas Line", "lat": -15.0, "lon": -46.0, "colonial_power": "Spain / Portugal", "year": 1494, "region": "South America", "impact": "High", "notes": "Divided New World between Spain and Portugal; shaped Latin America"},
    {"name": "Maginot-Siegfried Line Region", "lat": 49.0, "lon": 6.5, "colonial_power": "France / Germany", "year": 1930, "region": "Western Europe", "impact": "Medium", "notes": "Fortification lines shaped Franco-German border psychology"},
    {"name": "Mandate Palestine Borders", "lat": 31.5, "lon": 35.0, "colonial_power": "British / League of Nations", "year": 1920, "region": "Middle East", "impact": "Very High", "notes": "British Mandate created borders of modern Israel, Palestine, Jordan"},
]

# =====================================================================
# 9. MARITIME BOUNDARY DISPUTES
# =====================================================================
MARITIME_DISPUTES = [
    {"name": "South China Sea (Nine-Dash Line)", "lat": 12.0, "lon": 114.0, "claimants": "China, Vietnam, Philippines, Malaysia, Brunei, Taiwan", "area_km2": 3500000, "status": "Active", "resource": "Oil, gas, fisheries", "notes": "China's nine-dash line rejected by UNCLOS tribunal 2016; island building"},
    {"name": "Arctic Seabed Claims", "lat": 85.0, "lon": 0.0, "claimants": "Russia, Canada, Denmark, Norway, USA", "area_km2": 14000000, "status": "Active CLCS submissions", "resource": "Oil, gas, minerals, shipping routes", "notes": "Lomonosov Ridge claims; Northwest Passage; Northern Sea Route"},
    {"name": "East China Sea (Senkaku/Diaoyu)", "lat": 26.0, "lon": 124.0, "claimants": "Japan, China, Taiwan", "area_km2": 1249000, "status": "Active", "resource": "Oil, gas, fisheries", "notes": "EEZ overlaps; ADIZ disputes; frequent naval encounters"},
    {"name": "Aegean Sea Disputes", "lat": 39.0, "lon": 25.0, "claimants": "Greece, Turkey", "area_km2": 215000, "status": "Active", "resource": "Oil, gas, fisheries", "notes": "Continental shelf; FIR boundaries; island sovereignty; EEZ limits"},
    {"name": "Persian Gulf Boundaries", "lat": 27.0, "lon": 51.0, "claimants": "Iran, UAE, Saudi Arabia, Bahrain, Qatar", "area_km2": 251000, "status": "Partially resolved", "resource": "Oil, gas", "notes": "Abu Musa and Tunb Islands (Iran/UAE); various maritime boundaries"},
    {"name": "Caspian Sea Legal Status", "lat": 42.0, "lon": 51.0, "claimants": "Russia, Iran, Kazakhstan, Turkmenistan, Azerbaijan", "area_km2": 371000, "status": "Convention 2018", "resource": "Oil, gas", "notes": "2018 Convention on Legal Status; seabed division ongoing"},
    {"name": "Bay of Bengal Maritime", "lat": 15.0, "lon": 88.0, "claimants": "India, Bangladesh, Myanmar", "area_km2": 2172000, "status": "ITLOS rulings 2012/2014", "resource": "Gas, fisheries", "notes": "Bangladesh won significant EEZ in ITLOS rulings"},
    {"name": "Black Sea Maritime", "lat": 44.0, "lon": 33.0, "claimants": "Romania, Ukraine, Turkey, Russia, Georgia, Bulgaria", "area_km2": 436000, "status": "ICJ ruling 2009 (Romania-Ukraine)", "resource": "Gas, fisheries", "notes": "Snake Island area; Romania won ICJ case 2009"},
    {"name": "Timor Sea / Timor Gap", "lat": -11.0, "lon": 127.0, "claimants": "Timor-Leste, Australia", "area_km2": 61000, "status": "Treaty 2018", "resource": "Oil, gas (Greater Sunrise)", "notes": "Maritime boundary treaty 2018 after conciliation"},
    {"name": "Falklands/Malvinas EEZ", "lat": -52.0, "lon": -59.0, "claimants": "UK, Argentina", "area_km2": 400000, "status": "Disputed", "resource": "Oil, fisheries", "notes": "UK enforces exclusion zone; Argentina contests"},
    {"name": "Somalia-Kenya Maritime Border", "lat": -1.7, "lon": 42.0, "claimants": "Somalia, Kenya", "area_km2": 100000, "status": "ICJ ruling 2021", "resource": "Oil, gas", "notes": "ICJ awarded most of disputed area to Somalia"},
    {"name": "Barents Sea (Resolved)", "lat": 73.0, "lon": 35.0, "claimants": "Norway, Russia", "area_km2": 175000, "status": "Resolved 2010", "resource": "Oil, gas, fisheries", "notes": "40-year dispute resolved by 2010 treaty"},
    {"name": "Mediterranean EEZ (Eastern)", "lat": 34.5, "lon": 32.0, "claimants": "Turkey, Greece, Cyprus, Libya, Egypt", "area_km2": 2500000, "status": "Active", "resource": "Gas (Leviathan, Zohr)", "notes": "Turkey-Libya MOU contested; East Med gas pipeline plans"},
]

# =====================================================================
# 10. DIVIDED CITIES
# =====================================================================
DIVIDED_CITIES = [
    {"name": "Berlin (Historic)", "country": "Germany", "lat": 52.5163, "lon": 13.3777, "division_type": "Wall (1961-1989)", "divided_by": "Cold War / Ideological", "year_divided": 1961, "year_reunified": 1989, "status": "Reunified", "notes": "East/West Berlin; Checkpoint Charlie; Berlin Wall; Brandenburg Gate"},
    {"name": "Nicosia", "country": "Cyprus", "lat": 35.17, "lon": 33.36, "division_type": "UN Buffer Zone (Green Line)", "divided_by": "Ethnic / Political", "year_divided": 1974, "year_reunified": None, "status": "Still divided", "notes": "Last divided capital in Europe; Greek south / Turkish north; Ledra Street crossing"},
    {"name": "Jerusalem", "country": "Israel / Palestine", "lat": 31.78, "lon": 35.22, "division_type": "Contested sovereignty", "divided_by": "Ethno-religious / Political", "year_divided": 1948, "year_reunified": None, "status": "Contested", "notes": "East Jerusalem (Palestinian); West (Israeli); Old City; Temple Mount/Haram al-Sharif"},
    {"name": "Mostar", "country": "Bosnia & Herzegovina", "lat": 43.34, "lon": 17.81, "division_type": "Ethnic partition", "divided_by": "Bosniak / Croat", "year_divided": 1993, "year_reunified": None, "status": "De facto divided", "notes": "Stari Most (Old Bridge) destroyed 1993, rebuilt 2004; ethnic segregation persists"},
    {"name": "Belfast", "country": "Northern Ireland (UK)", "lat": 54.6, "lon": -5.93, "division_type": "Peace walls", "divided_by": "Sectarian (Catholic / Protestant)", "year_divided": 1969, "year_reunified": None, "status": "Walls being slowly removed", "notes": "60+ peace walls; Falls Road (Catholic) vs Shankill Road (Protestant)"},
    {"name": "Mitrovica", "country": "Kosovo", "lat": 42.89, "lon": 20.87, "division_type": "Bridge / ethnic line", "divided_by": "Albanian / Serbian", "year_divided": 1999, "year_reunified": None, "status": "Still divided", "notes": "Ibar River divides Albanian south from Serbian north; KFOR presence"},
    {"name": "Hebron (Al-Khalil)", "country": "Palestine / Israel", "lat": 31.53, "lon": 35.1, "division_type": "H1/H2 zones", "divided_by": "Israeli occupation / Palestinian", "year_divided": 1997, "year_reunified": None, "status": "Divided", "notes": "Hebron Protocol; H1 (Palestinian Authority) / H2 (Israeli military control)"},
    {"name": "Beirut (Historic)", "country": "Lebanon", "lat": 33.89, "lon": 35.5, "division_type": "Green Line (1975-1990)", "divided_by": "Civil War factions", "year_divided": 1975, "year_reunified": 1990, "status": "Reunified (scars remain)", "notes": "Damascus Road green line; Christian East / Muslim West; 15-year civil war"},
    {"name": "Vukovar", "country": "Croatia", "lat": 45.35, "lon": 19.0, "division_type": "Ethnic displacement", "divided_by": "Croatian / Serbian", "year_divided": 1991, "year_reunified": 1998, "status": "Reintegrated; tensions persist", "notes": "1991 siege and massacre; UNTAES reintegration 1996-1998; still ethnically split"},
    {"name": "Gorizia / Nova Gorica", "country": "Italy / Slovenia", "lat": 45.94, "lon": 13.63, "division_type": "National border", "divided_by": "Post-WWII treaty", "year_divided": 1947, "year_reunified": None, "status": "Open border (Schengen)", "notes": "Split by Treaty of Paris 1947; joint European Capital of Culture 2025"},
    {"name": "Baarle-Hertog / Baarle-Nassau", "country": "Belgium / Netherlands", "lat": 51.44, "lon": 4.93, "division_type": "Enclave fragmentation", "divided_by": "Medieval treaties", "year_divided": 1198, "year_reunified": None, "status": "Administratively split", "notes": "22 Belgian and 7 Dutch enclaves intertwined; borders run through houses"},
    {"name": "Derry/Londonderry", "country": "Northern Ireland (UK)", "lat": 55.0, "lon": -7.32, "division_type": "Sectarian geography", "divided_by": "Nationalist / Unionist", "year_divided": 1969, "year_reunified": None, "status": "Tensions easing", "notes": "Even the name is disputed; Bogside, Bloody Sunday 1972; peace bridges"},
    {"name": "Kirkuk", "country": "Iraq", "lat": 35.47, "lon": 44.39, "division_type": "Ethnic/political contest", "divided_by": "Kurdish / Arab / Turkmen", "year_divided": 2003, "year_reunified": None, "status": "Disputed", "notes": "Article 140 of Iraqi constitution; oil-rich; multiple demographic shifts"},
    {"name": "Brazzaville / Kinshasa", "country": "Congo-Brazzaville / DR Congo", "lat": -4.27, "lon": 15.28, "division_type": "River boundary", "divided_by": "Colonial / National", "year_divided": 1880, "year_reunified": None, "status": "Two countries", "notes": "Closest capital cities in the world; Congo River divides; ferry connection"},
]

# =====================================================================
# CHART BUILDERS
# =====================================================================

def _dark_fig(rows=1, cols=1, figsize=(10, 5)):
    """Create a dark-themed matplotlib figure."""
    fig, ax = plt.subplots(rows, cols, figsize=figsize)
    fig.patch.set_facecolor(_BG)
    if rows == 1 and cols == 1:
        ax.set_facecolor(_SURFACE)
    else:
        for a in (ax.flat if hasattr(ax, 'flat') else [ax]):
            a.set_facecolor(_SURFACE)
    return fig, ax


def _style_ax(ax, title="", xlabel="", ylabel=""):
    """Apply dark theme to an axes."""
    if title:
        ax.set_title(title, color=_TEXT, fontsize=14, fontweight="bold")
    if xlabel:
        ax.set_xlabel(xlabel, color=_SECONDARY, fontsize=11)
    if ylabel:
        ax.set_ylabel(ylabel, color=_SECONDARY, fontsize=11)
    ax.tick_params(colors=_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.grid(True, alpha=0.15, color=_BORDER)


def _build_walls_chart(df):
    """Horizontal bar chart of wall lengths."""
    fig, ax = _dark_fig(figsize=(10, 7))
    sorted_df = df.sort_values("length_km", ascending=True).tail(15)
    colors = [_ACCENT if s == "Active" else "#f59e0b" if "Partial" in s or "Under" in s
              else "#8b5cf6" if "Historic" in s else "#10b981"
              for s in sorted_df["status"]]
    ax.barh(range(len(sorted_df)), sorted_df["length_km"], color=colors, alpha=0.85,
            edgecolor=_BORDER, height=0.65)
    ax.set_yticks(range(len(sorted_df)))
    ax.set_yticklabels(sorted_df["name"], fontsize=8, color=_SECONDARY)
    _style_ax(ax, title="Border Walls & Fences by Length (km)", xlabel="Length (km)")
    fig.tight_layout()
    return fig


def _build_disputes_chart(df):
    """Scatter plot of disputed territories: year vs area."""
    fig, ax = _dark_fig(figsize=(10, 5))
    areas = df["area_km2"].clip(upper=300000)
    sizes = (areas / areas.max() * 300).clip(lower=15)
    ax.scatter(df["since"], areas, s=sizes, c=_ACCENT, alpha=0.7, edgecolors=_BORDER)
    for _, row in df.iterrows():
        if row["area_km2"] > 50000:
            ax.annotate(row["name"], (row["since"], min(row["area_km2"], 300000)),
                        fontsize=6, color=_SECONDARY, ha="center", va="bottom")
    _style_ax(ax, title="Disputed Territories: Year of Dispute vs Area",
              xlabel="Year Dispute Began", ylabel="Area (km2, capped)")
    fig.tight_layout()
    return fig


def _build_dmz_chart(df):
    """Bar chart of DMZ lengths."""
    fig, ax = _dark_fig(figsize=(10, 5))
    active = df[df["length_km"] > 0].sort_values("length_km", ascending=True)
    colors = [_ACCENT if "Active" in s else "#f59e0b" for s in active["status"]]
    ax.barh(range(len(active)), active["length_km"], color=colors, alpha=0.85,
            edgecolor=_BORDER, height=0.6)
    ax.set_yticks(range(len(active)))
    ax.set_yticklabels(active["name"], fontsize=8, color=_SECONDARY)
    _style_ax(ax, title="Demilitarized Zones by Length (km)", xlabel="Length (km)")
    fig.tight_layout()
    return fig


def _build_enclaves_chart(df):
    """Bar chart of enclave areas."""
    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("area_km2", ascending=True)
    colors = ["#ef4444" if t == "Exclave" else "#3b82f6" if t == "Enclave"
              else "#f59e0b" for t in sorted_df["type"]]
    ax.barh(range(len(sorted_df)), sorted_df["area_km2"], color=colors, alpha=0.85,
            edgecolor=_BORDER, height=0.6)
    ax.set_yticks(range(len(sorted_df)))
    ax.set_yticklabels(sorted_df["name"], fontsize=7, color=_SECONDARY)
    _style_ax(ax, title="Enclaves & Exclaves by Area (km2)", xlabel="Area (km2)")
    fig.tight_layout()
    return fig


def _build_micronations_chart(df):
    """Timeline scatter plot of micronation founding years."""
    fig, ax = _dark_fig(figsize=(10, 5))
    valid = df[df["founded"] > 1900].copy()
    ax.scatter(valid["founded"], range(len(valid)), c=_ACCENT, s=60,
              alpha=0.8, edgecolors=_BORDER, zorder=3)
    ax.set_yticks(range(len(valid)))
    ax.set_yticklabels(valid["name"], fontsize=7, color=_SECONDARY)
    ax.axvline(x=1991, color="#ef4444", linestyle="--", alpha=0.4, label="Soviet Collapse")
    ax.legend(fontsize=8, facecolor=_SURFACE, edgecolor=_BORDER, labelcolor=_SECONDARY)
    _style_ax(ax, title="Micronation Founding Timeline", xlabel="Year Founded")
    fig.tight_layout()
    return fig


def _build_conflicts_chart(df):
    """Bubble chart of active conflicts: severity on y-axis, start year on x."""
    sev_map = {"Low": 1, "Medium": 2, "High": 3}
    fig, ax = _dark_fig(figsize=(10, 5))
    sev_vals = [sev_map.get(s, 1) for s in df["severity"]]
    colors = ["#ef4444" if s == "High" else "#f59e0b" if s == "Medium"
              else "#10b981" for s in df["severity"]]
    ax.scatter(df["start_year"], sev_vals, s=120, c=colors, alpha=0.8,
              edgecolors=_BORDER, zorder=3)
    for _, row in df.iterrows():
        ax.annotate(row["name"], (row["start_year"], sev_map.get(row["severity"], 1)),
                    fontsize=6, color=_SECONDARY, ha="center", va="bottom",
                    xytext=(0, 6), textcoords="offset points")
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["Low", "Medium", "High"])
    _style_ax(ax, title="Active Conflict Zones by Start Year & Severity",
              xlabel="Start Year", ylabel="Severity")
    fig.tight_layout()
    return fig


def _build_cold_war_chart(df):
    """Categorical scatter: Cold War items by year range and bloc."""
    fig, ax = _dark_fig(figsize=(10, 5))
    bloc_map = {}
    for i, b in enumerate(df["bloc"].unique()):
        bloc_map[b] = i
    y_vals = [bloc_map[b] for b in df["bloc"]]
    start_years = []
    for y in df["years"]:
        try:
            start_years.append(int(y.split("-")[0]))
        except (ValueError, AttributeError):
            start_years.append(1950)
    colors = [r["color"] for _, r in df.iterrows()]
    ax.scatter(start_years, y_vals, s=100, c=colors, alpha=0.8,
              edgecolors=_BORDER, zorder=3)
    for i, (_, row) in enumerate(df.iterrows()):
        ax.annotate(row["name"], (start_years[i], y_vals[i]),
                    fontsize=6, color=_SECONDARY, ha="left",
                    xytext=(5, 3), textcoords="offset points")
    ax.set_yticks(range(len(bloc_map)))
    ax.set_yticklabels(list(bloc_map.keys()), fontsize=9, color=_SECONDARY)
    _style_ax(ax, title="Cold War Boundaries & Flashpoints", xlabel="Year")
    fig.tight_layout()
    return fig


def _build_colonial_chart(df):
    """Bar chart of colonial border impacts."""
    impact_map = {"Low": 1, "Medium": 2, "High": 3, "Very High": 4}
    fig, ax = _dark_fig(figsize=(10, 6))
    sorted_df = df.sort_values("year")
    impact_vals = [impact_map.get(i, 2) for i in sorted_df["impact"]]
    colors = ["#dc2626" if v == 4 else "#ef4444" if v == 3 else "#f59e0b" if v == 2
              else "#10b981" for v in impact_vals]
    ax.barh(range(len(sorted_df)), impact_vals, color=colors, alpha=0.85,
            edgecolor=_BORDER, height=0.6)
    ax.set_yticks(range(len(sorted_df)))
    labels = [f"{r['name']} ({r['year']})" for _, r in sorted_df.iterrows()]
    ax.set_yticklabels(labels, fontsize=7, color=_SECONDARY)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels(["Low", "Medium", "High", "Very High"])
    _style_ax(ax, title="Colonial Border Legacy - Impact Rating", xlabel="Impact")
    fig.tight_layout()
    return fig


def _build_maritime_chart(df):
    """Horizontal bar chart of maritime dispute areas."""
    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("area_km2", ascending=True)
    colors = [_ACCENT if s == "Active" else "#10b981" for s in sorted_df["status"]]
    ax.barh(range(len(sorted_df)), sorted_df["area_km2"] / 1000, color=colors,
            alpha=0.85, edgecolor=_BORDER, height=0.6)
    ax.set_yticks(range(len(sorted_df)))
    ax.set_yticklabels(sorted_df["name"], fontsize=7, color=_SECONDARY)
    _style_ax(ax, title="Maritime Boundary Disputes by Area",
              xlabel="Area (x1000 km2)")
    fig.tight_layout()
    return fig


def _build_divided_chart(df):
    """Timeline of divided cities."""
    fig, ax = _dark_fig(figsize=(10, 6))
    current_year = 2025
    for i, (_, row) in enumerate(df.iterrows()):
        start = row["year_divided"]
        end = row["year_reunified"] if row["year_reunified"] else current_year
        duration = max(end - start, 1)
        color = "#10b981" if row["status"] == "Reunified" else "#ef4444" if "divided" in row["status"].lower() or "Contested" in row["status"] else "#f59e0b"
        ax.barh(i, duration, left=start, color=color, height=0.6, alpha=0.8,
                edgecolor=_BORDER)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["name"], fontsize=7, color=_SECONDARY)
    _style_ax(ax, title="Divided Cities - Division Timeline",
              xlabel="Year")
    ax.axvline(x=1989, color="#f59e0b", linestyle="--", alpha=0.4, label="Fall of Berlin Wall")
    ax.legend(fontsize=8, facecolor=_SURFACE, edgecolor=_BORDER, labelcolor=_SECONDARY)
    fig.tight_layout()
    return fig


# =====================================================================
# MAP BUILDERS
# =====================================================================

def _base_map(lat=30.0, lon=10.0, zoom=2):
    """Create a dark-themed folium map."""
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )


def _build_walls_map(data):
    m = _base_map(lat=30, lon=30, zoom=2)
    for w in data:
        status = w.get("status", "Unknown")
        color = "red" if "Active" in status else "orange" if "Partial" in status or "Under" in status else "blue" if "Historic" in status else "green"
        popup_html = (
            f"<b>{escape(w['name'])}</b><br>"
            f"<b>Country:</b> {escape(w['country'])}<br>"
            f"<b>Length:</b> {w['length_km']} km<br>"
            f"<b>Status:</b> {escape(status)}<br>"
            f"<b>Started:</b> {w['year_started']}<br>"
            f"<b>Notes:</b> {escape(w.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=max(4, min(w["length_km"] / 200, 14)),
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(w["name"]),
        ).add_to(m)
    return m


def _build_disputes_map(data):
    m = _base_map(lat=30, lon=50, zoom=2)
    for d in data:
        area = d.get("area_km2", 0)
        radius = max(5, min(area / 10000, 18))
        popup_html = (
            f"<b>{escape(d['name'])}</b><br>"
            f"<b>Claimants:</b> {escape(d['claimants'])}<br>"
            f"<b>Status:</b> {escape(d['status'])}<br>"
            f"<b>Since:</b> {d['since']}<br>"
            f"<b>Area:</b> {d['area_km2']:,} km2<br>"
            f"<b>Notes:</b> {escape(d.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=radius,
            color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(d["name"]),
        ).add_to(m)
    return m


def _build_dmz_map(data):
    m = _base_map(lat=30, lon=50, zoom=2)
    for d in data:
        active = "Active" in d.get("status", "")
        color = "cyan" if active else "orange"
        popup_html = (
            f"<b>{escape(d['name'])}</b><br>"
            f"<b>Countries:</b> {escape(d['countries'])}<br>"
            f"<b>Length:</b> {d['length_km']} km<br>"
            f"<b>Width:</b> {d['width_km']} km<br>"
            f"<b>Established:</b> {d['established']}<br>"
            f"<b>Status:</b> {escape(d['status'])}<br>"
            f"<b>Notes:</b> {escape(d.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8 if active else 6,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(d["name"]),
        ).add_to(m)
    return m


def _build_enclaves_map(data):
    m = _base_map(lat=45, lon=20, zoom=3)
    for e in data:
        t = e.get("type", "")
        color = "red" if t == "Exclave" else "blue" if t == "Enclave" else "orange"
        popup_html = (
            f"<b>{escape(e['name'])}</b><br>"
            f"<b>Parent:</b> {escape(e['parent'])}<br>"
            f"<b>Surrounded by:</b> {escape(e['surrounded_by'])}<br>"
            f"<b>Type:</b> {escape(t)}<br>"
            f"<b>Area:</b> {e['area_km2']:,} km2<br>"
            f"<b>Population:</b> {e['population']:,}<br>"
            f"<b>Notes:</b> {escape(e.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[e["lat"], e["lon"]],
            radius=7,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(e["name"]),
        ).add_to(m)
    return m


def _build_micronations_map(data):
    m = _base_map(lat=35, lon=10, zoom=2)
    for mn in data:
        if mn["lat"] == 0.0 and mn["lon"] == 0.0:
            continue
        popup_html = (
            f"<b>{escape(mn['name'])}</b><br>"
            f"<b>Founded:</b> {mn['founded']}<br>"
            f"<b>Population:</b> {mn['population']}<br>"
            f"<b>Claimed by:</b> {escape(mn['claimed_by'])}<br>"
            f"<b>Notes:</b> {escape(mn.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[mn["lat"], mn["lon"]],
            radius=6,
            color="#a855f7", fill=True, fill_color="#a855f7", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(mn["name"]),
        ).add_to(m)
    return m


def _build_conflicts_map(data):
    m = _base_map(lat=20, lon=30, zoom=2)
    for c in data:
        sev = c.get("severity", "Low")
        color = "red" if sev == "High" else "orange" if sev == "Medium" else "green"
        radius = 12 if sev == "High" else 9 if sev == "Medium" else 6
        popup_html = (
            f"<b>{escape(c['name'])}</b><br>"
            f"<b>Region:</b> {escape(c['region'])}<br>"
            f"<b>Start:</b> {c['start_year']}<br>"
            f"<b>Type:</b> {escape(c['type'])}<br>"
            f"<b>Severity:</b> {escape(sev)}<br>"
            f"<b>Casualties:</b> {escape(c['casualties_est'])}<br>"
            f"<b>Notes:</b> {escape(c.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(c["name"]),
        ).add_to(m)
    return m


def _build_cold_war_map(data):
    m = _base_map(lat=50, lon=15, zoom=3)
    for item in data:
        popup_html = (
            f"<b>{escape(item['name'])}</b><br>"
            f"<b>Type:</b> {escape(item['type'])}<br>"
            f"<b>Bloc:</b> {escape(item['bloc'])}<br>"
            f"<b>Years:</b> {escape(item['years'])}<br>"
            f"<b>Status:</b> {escape(item['status'])}<br>"
            f"<b>Notes:</b> {escape(item.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=item["color"], fill=True, fill_color=item["color"], fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(item["name"]),
        ).add_to(m)
    return m


def _build_colonial_map(data):
    m = _base_map(lat=15, lon=20, zoom=2)
    impact_colors = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444", "Very High": "#dc2626"}
    for c in data:
        color = impact_colors.get(c.get("impact", "Medium"), "#f59e0b")
        popup_html = (
            f"<b>{escape(c['name'])}</b><br>"
            f"<b>Colonial Power:</b> {escape(c['colonial_power'])}<br>"
            f"<b>Year:</b> {c['year']}<br>"
            f"<b>Region:</b> {escape(c['region'])}<br>"
            f"<b>Impact:</b> {escape(c['impact'])}<br>"
            f"<b>Notes:</b> {escape(c.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=9,
            color=color, fill=True, fill_color=color, fill_opacity=0.65,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(c["name"]),
        ).add_to(m)
    return m


def _build_maritime_map(data):
    m = _base_map(lat=20, lon=80, zoom=2)
    for md in data:
        active = md.get("status", "") == "Active"
        color = "#ef4444" if active else "#10b981"
        area = md.get("area_km2", 100000)
        radius = max(6, min(area / 500000, 16))
        popup_html = (
            f"<b>{escape(md['name'])}</b><br>"
            f"<b>Claimants:</b> {escape(md['claimants'])}<br>"
            f"<b>Area:</b> {md['area_km2']:,} km2<br>"
            f"<b>Status:</b> {escape(md['status'])}<br>"
            f"<b>Resources:</b> {escape(md['resource'])}<br>"
            f"<b>Notes:</b> {escape(md.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[md["lat"], md["lon"]],
            radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(md["name"]),
        ).add_to(m)
    return m


def _build_divided_map(data):
    m = _base_map(lat=40, lon=20, zoom=3)
    for dc in data:
        status = dc.get("status", "")
        color = "green" if status == "Reunified" else "red" if "divided" in status.lower() or "Contested" in status else "orange"
        popup_html = (
            f"<b>{escape(dc['name'])}</b><br>"
            f"<b>Country:</b> {escape(dc['country'])}<br>"
            f"<b>Division:</b> {escape(dc['division_type'])}<br>"
            f"<b>Divided by:</b> {escape(dc['divided_by'])}<br>"
            f"<b>Year Divided:</b> {dc['year_divided']}<br>"
            f"<b>Reunified:</b> {dc['year_reunified'] if dc['year_reunified'] else 'Still divided'}<br>"
            f"<b>Status:</b> {escape(status)}<br>"
            f"<b>Notes:</b> {escape(dc.get('notes', ''))}"
        )
        folium.CircleMarker(
            location=[dc["lat"], dc["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(dc["name"]),
        ).add_to(m)
    return m


# =====================================================================
# CACHED DATA HELPERS
# =====================================================================

@st.cache_data(ttl=3600)
def _get_walls_df():
    return pd.DataFrame(BORDER_WALLS)

@st.cache_data(ttl=3600)
def _get_disputes_df():
    return pd.DataFrame(DISPUTED_TERRITORIES)

@st.cache_data(ttl=3600)
def _get_dmz_df():
    return pd.DataFrame(DEMILITARIZED_ZONES)

@st.cache_data(ttl=3600)
def _get_enclaves_df():
    return pd.DataFrame(ENCLAVES_EXCLAVES)

@st.cache_data(ttl=3600)
def _get_micronations_df():
    return pd.DataFrame(MICRONATIONS)

@st.cache_data(ttl=3600)
def _get_conflicts_df():
    return pd.DataFrame(ACTIVE_CONFLICTS)

@st.cache_data(ttl=3600)
def _get_cold_war_df():
    return pd.DataFrame(COLD_WAR_ITEMS)

@st.cache_data(ttl=3600)
def _get_colonial_df():
    return pd.DataFrame(COLONIAL_BORDERS)

@st.cache_data(ttl=3600)
def _get_maritime_df():
    return pd.DataFrame(MARITIME_DISPUTES)

@st.cache_data(ttl=3600)
def _get_divided_df():
    return pd.DataFrame(DIVIDED_CITIES)


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_borders_conflicts_maps_tab():
    """Render the Borders, Walls & Conflicts tab."""
    st.markdown(
        '<div class="tab-header red"><h4>\U0001f3f4 Borders, Walls &amp; Conflicts</h4>'
        '<p>Border disputes, walls, demilitarized zones, territorial claims '
        '&amp; geopolitical hotspots</p></div>',
        unsafe_allow_html=True,
    )

    selected_mode = st.radio(
        "Select Mode",
        MAP_MODES,
        horizontal=True,
        key="borders_conflicts_mode",
    )

    st.markdown("---")

    # =================================================================
    # 1. BORDER WALLS & FENCES
    # =================================================================
    if selected_mode == "Border Walls & Fences":
        st.markdown(
            "<p style='color:#8b97b0;'>Curated database of 25+ border walls, "
            "fences, and barriers worldwide -- from historic (Berlin Wall) to "
            "modern constructions.</p>",
            unsafe_allow_html=True,
        )
        df = _get_walls_df()

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Barriers", len(df))
        active_count = len(df[df["status"].str.contains("Active", na=False)])
        c2.metric("Currently Active", active_count)
        c3.metric("Total Length", f"{df['length_km'].sum():,.0f} km")
        longest = df.loc[df["length_km"].idxmax()]
        c4.metric("Longest", f"{longest['name'][:20]}...")

        # Map
        fmap = _build_walls_map(BORDER_WALLS)
        components.html(fmap._repr_html_(), height=500)

        # Chart
        st.subheader("Wall Length Comparison")
        fig = _build_walls_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        # Dataframe
        st.subheader("Border Walls & Fences Data")
        st.dataframe(df[["name", "country", "length_km", "status", "year_started", "notes"]],
                      width="stretch")

        # Download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Border Walls CSV", csv,
                           "border_walls.csv", "text/csv",
                           key="bcm_dl_walls")

    # =================================================================
    # 2. DISPUTED TERRITORIES
    # =================================================================
    elif selected_mode == "Disputed Territories":
        st.markdown(
            "<p style='color:#8b97b0;'>30+ disputed territories, occupied "
            "regions, and sovereignty conflicts around the world.</p>",
            unsafe_allow_html=True,
        )
        df = _get_disputes_df()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Disputed Territories", len(df))
        total_area = df["area_km2"].sum()
        c2.metric("Total Area", f"{total_area:,.0f} km2")
        oldest = df.loc[df["since"].idxmin()]
        c3.metric("Oldest Dispute", f"{oldest['name'][:18]} ({oldest['since']})")
        newest = df.loc[df["since"].idxmax()]
        c4.metric("Newest Dispute", f"{newest['name'][:18]} ({newest['since']})")

        fmap = _build_disputes_map(DISPUTED_TERRITORIES)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Dispute Timeline")
        fig = _build_disputes_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Disputed Territories Data")
        st.dataframe(df[["name", "claimants", "status", "since", "area_km2", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Disputed Territories CSV", csv,
                           "disputed_territories.csv", "text/csv",
                           key="dl_disputes")

    # =================================================================
    # 3. DEMILITARIZED ZONES
    # =================================================================
    elif selected_mode == "Demilitarized Zones":
        st.markdown(
            "<p style='color:#8b97b0;'>Demilitarized zones, buffer zones, and "
            "arms-free regions -- both active and historical.</p>",
            unsafe_allow_html=True,
        )
        df = _get_dmz_df()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total DMZs", len(df))
        active_dmz = len(df[df["status"].str.contains("Active", na=False)])
        c2.metric("Currently Active", active_dmz)
        total_length = df["length_km"].sum()
        c3.metric("Total Length", f"{total_length:,.0f} km")

        fmap = _build_dmz_map(DEMILITARIZED_ZONES)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("DMZ Lengths")
        fig = _build_dmz_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Demilitarized Zones Data")
        st.dataframe(df[["name", "countries", "length_km", "width_km",
                          "established", "status", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download DMZ CSV", csv,
                           "demilitarized_zones.csv", "text/csv",
                           key="bcm_dl_dmz")

    # =================================================================
    # 4. ENCLAVES & EXCLAVES
    # =================================================================
    elif selected_mode == "Enclaves & Exclaves":
        st.markdown(
            "<p style='color:#8b97b0;'>Enclaves, exclaves, and counter-enclaves "
            "-- territories surrounded by or separated from their parent "
            "state.</p>",
            unsafe_allow_html=True,
        )
        df = _get_enclaves_df()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Entries", len(df))
        exclaves = len(df[df["type"] == "Exclave"])
        c2.metric("Exclaves", exclaves)
        enclaves = len(df[df["type"] == "Enclave"])
        c3.metric("Enclaves", enclaves)
        total_pop = df["population"].sum()
        c4.metric("Total Population", f"{total_pop:,}")

        fmap = _build_enclaves_map(ENCLAVES_EXCLAVES)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Area Comparison")
        fig = _build_enclaves_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Enclaves & Exclaves Data")
        st.dataframe(df[["name", "parent", "surrounded_by", "type",
                          "area_km2", "population", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Enclaves CSV", csv,
                           "enclaves_exclaves.csv", "text/csv",
                           key="dl_enclaves")

    # =================================================================
    # 5. MICRONATIONS
    # =================================================================
    elif selected_mode == "Micronations":
        st.markdown(
            "<p style='color:#8b97b0;'>20+ self-declared micronations -- from "
            "Sealand to Liberland, Molossia, and more.</p>",
            unsafe_allow_html=True,
        )
        df = _get_micronations_df()

        c1, c2, c3 = st.columns(3)
        c1.metric("Micronations Listed", len(df))
        total_pop = df["population"].sum()
        c2.metric("Total Claimed Pop.", f"{total_pop:,}")
        oldest = df.loc[df["founded"].idxmin()]
        c3.metric("Oldest (excl. Monaco)", f"{oldest['name'][:20]}")

        fmap = _build_micronations_map(MICRONATIONS)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Founding Timeline")
        fig = _build_micronations_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Micronations Data")
        st.dataframe(df[["name", "founded", "population", "claimed_by", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Micronations CSV", csv,
                           "micronations.csv", "text/csv",
                           key="dl_micronations")

    # =================================================================
    # 6. ACTIVE CONFLICT ZONES
    # =================================================================
    elif selected_mode == "Active Conflict Zones":
        st.markdown(
            "<p style='color:#8b97b0;'>Currently active armed conflicts, civil "
            "wars, and insurgencies worldwide. Severity based on Uppsala Conflict "
            "Data classifications and recent reporting.</p>",
            unsafe_allow_html=True,
        )
        df = _get_conflicts_df()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Active Conflicts", len(df))
        high = len(df[df["severity"] == "High"])
        c2.metric("High Severity", high)
        medium = len(df[df["severity"] == "Medium"])
        c3.metric("Medium Severity", medium)
        regions = df["region"].nunique()
        c4.metric("Regions Affected", regions)

        fmap = _build_conflicts_map(ACTIVE_CONFLICTS)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Conflict Severity Chart")
        fig = _build_conflicts_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Active Conflicts Data")
        st.dataframe(df[["name", "region", "start_year", "type", "severity",
                          "casualties_est", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Conflicts CSV", csv,
                           "active_conflicts.csv", "text/csv",
                           key="bcm_dl_conflicts")

    # =================================================================
    # 7. COLD WAR BOUNDARIES
    # =================================================================
    elif selected_mode == "Cold War Boundaries":
        st.markdown(
            "<p style='color:#8b97b0;'>Iron Curtain, Berlin Wall, NATO vs Warsaw "
            "Pact flashpoints, and Cold War strategic boundaries (1947-1991).</p>",
            unsafe_allow_html=True,
        )
        df = _get_cold_war_df()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Items Mapped", len(df))
        iron_curtain = len(df[df["bloc"] == "Iron Curtain"])
        c2.metric("Iron Curtain Sites", iron_curtain)
        nato_items = len(df[df["bloc"].str.contains("NATO", na=False)])
        c3.metric("NATO/Western Items", nato_items)
        flashpoints = len(df[df["bloc"].str.contains("flashpoint", na=False)])
        c4.metric("Flashpoints", flashpoints)

        fmap = _build_cold_war_map(COLD_WAR_ITEMS)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Cold War Boundaries & Flashpoints")
        fig = _build_cold_war_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Cold War Data")
        st.dataframe(df[["name", "type", "bloc", "years", "status", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Cold War CSV", csv,
                           "cold_war_boundaries.csv", "text/csv",
                           key="dl_cold_war")

    # =================================================================
    # 8. COLONIAL BORDER LEGACY
    # =================================================================
    elif selected_mode == "Colonial Border Legacy":
        st.markdown(
            "<p style='color:#8b97b0;'>Borders drawn by colonial powers that "
            "continue to shape conflicts today -- from the Scramble for Africa "
            "to Sykes-Picot and the Radcliffe Line.</p>",
            unsafe_allow_html=True,
        )
        df = _get_colonial_df()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Colonial Borders", len(df))
        very_high = len(df[df["impact"] == "Very High"])
        c2.metric("Very High Impact", very_high)
        regions = df["region"].nunique()
        c3.metric("Regions", regions)
        powers = df["colonial_power"].nunique()
        c4.metric("Colonial Powers", powers)

        fmap = _build_colonial_map(COLONIAL_BORDERS)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Colonial Border Impact")
        fig = _build_colonial_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Colonial Border Legacy Data")
        st.dataframe(df[["name", "colonial_power", "year", "region",
                          "impact", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Colonial Borders CSV", csv,
                           "colonial_borders.csv", "text/csv",
                           key="bcm_dl_colonial")

    # =================================================================
    # 9. MARITIME BOUNDARY DISPUTES
    # =================================================================
    elif selected_mode == "Maritime Boundary Disputes":
        st.markdown(
            "<p style='color:#8b97b0;'>EEZ disputes, continental shelf claims, "
            "and maritime boundary conflicts -- from the South China Sea to the "
            "Arctic.</p>",
            unsafe_allow_html=True,
        )
        df = _get_maritime_df()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Maritime Disputes", len(df))
        active_m = len(df[df["status"] == "Active"])
        c2.metric("Active Disputes", active_m)
        total_area = df["area_km2"].sum()
        c3.metric("Total Disputed Area", f"{total_area / 1e6:.1f}M km2")
        largest = df.loc[df["area_km2"].idxmax()]
        c4.metric("Largest", f"{largest['name'][:20]}...")

        fmap = _build_maritime_map(MARITIME_DISPUTES)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Disputed Maritime Areas")
        fig = _build_maritime_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Maritime Disputes Data")
        st.dataframe(df[["name", "claimants", "area_km2", "status",
                          "resource", "notes"]],
                      width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Maritime Disputes CSV", csv,
                           "maritime_disputes.csv", "text/csv",
                           key="bcm_dl_maritime")

    # =================================================================
    # 10. DIVIDED CITIES
    # =================================================================
    elif selected_mode == "Divided Cities":
        st.markdown(
            "<p style='color:#8b97b0;'>Cities that have been or remain divided "
            "by walls, borders, ethnic lines, or conflict -- from Berlin to "
            "Nicosia, Jerusalem, and Belfast.</p>",
            unsafe_allow_html=True,
        )
        df = _get_divided_df()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Divided Cities", len(df))
        still_div = len(df[df["year_reunified"].isna()])
        c2.metric("Still Divided", still_div)
        reunified = len(df[df["year_reunified"].notna()])
        c3.metric("Reunified", reunified)
        oldest_div = df.loc[df["year_divided"].idxmin()]
        c4.metric("Oldest Division", f"{oldest_div['name']} ({oldest_div['year_divided']})")

        fmap = _build_divided_map(DIVIDED_CITIES)
        components.html(fmap._repr_html_(), height=500)

        st.subheader("Division Timelines")
        fig = _build_divided_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Divided Cities Data")
        display_cols = ["name", "country", "division_type", "divided_by",
                        "year_divided", "year_reunified", "status", "notes"]
        st.dataframe(df[display_cols], width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Divided Cities CSV", csv,
                           "divided_cities.csv", "text/csv",
                           key="dl_divided")
