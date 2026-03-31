# -*- coding: utf-8 -*-
"""
Pandemic & Disease History Maps module for TerraScout AI.
Visualizes historical pandemics, plague routes, epidemics, and modern disease data
on interactive maps with curated historical datasets and live API data.

Data Sources:
  - disease.sh API (COVID-19 live data, free, no API key)
  - WHO GHO API (vaccination, HIV, malaria indicators)
  - Curated historical datasets (Black Death, Spanish Flu, cholera, etc.)
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
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════
DISEASE_SH_API = "https://disease.sh/v3/covid-19"
WHO_GHO_API = "https://ghoapi.azureedge.net/api"

# ═══════════════════════════════════════════════════════════════
# COLOR PALETTE (matches TerraScout dark theme)
# ═══════════════════════════════════════════════════════════════
BG_PRIMARY = "#0a0e1a"
BG_SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_RED = "#ef4444"
ACCENT_AMBER = "#f59e0b"
ACCENT_GREEN = "#10b981"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_PINK = "#ec4899"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"

SEVERITY_COLORS = {
    "catastrophic": "#991b1b",
    "severe": "#dc2626",
    "high": "#ef4444",
    "moderate": "#f97316",
    "low": "#f59e0b",
    "minimal": "#10b981",
}

# ═══════════════════════════════════════════════════════════════
# MAP MODES
# ═══════════════════════════════════════════════════════════════
MAP_MODES = [
    "1. Black Death (1347-1353)",
    "2. Spanish Flu (1918-1919)",
    "3. Smallpox History",
    "4. Cholera Pandemics",
    "5. COVID-19 Global (Live)",
    "6. Malaria Endemic Zones",
    "7. HIV/AIDS Global",
    "8. Plague of Justinian (541-549)",
    "9. Yellow Fever & Tropical Diseases",
    "10. Vaccination Coverage",
]

# ═══════════════════════════════════════════════════════════════
# CURATED HISTORICAL DATA
# ═══════════════════════════════════════════════════════════════

# ---------- 1. Black Death (1347-1353) ----------
BLACK_DEATH_SPREAD = [
    {"city": "Caffa (Feodosia)", "lat": 45.03, "lon": 35.38, "year": 1346,
     "note": "Siege of Caffa — Mongol army catapults plague corpses; Genoese ships flee",
     "deaths": "Unknown", "pop_loss_pct": 50},
    {"city": "Constantinople", "lat": 41.01, "lon": 28.98, "year": 1347,
     "note": "Major trade hub devastated; Emperor John VI Kantakouzenos records epidemic",
     "deaths": "~100,000", "pop_loss_pct": 50},
    {"city": "Messina, Sicily", "lat": 38.19, "lon": 15.55, "year": 1347,
     "note": "Genoese galleys arrive with infected crew — first European outbreak",
     "deaths": "~50,000", "pop_loss_pct": 60},
    {"city": "Genoa", "lat": 44.41, "lon": 8.93, "year": 1347,
     "note": "Ships turned away but plague already spreading through port",
     "deaths": "~40,000", "pop_loss_pct": 55},
    {"city": "Venice", "lat": 45.44, "lon": 12.34, "year": 1348,
     "note": "Pioneered 40-day quarantine (quarantina); lost 60% of population",
     "deaths": "~100,000", "pop_loss_pct": 60},
    {"city": "Florence", "lat": 43.77, "lon": 11.25, "year": 1348,
     "note": "Boccaccio's Decameron describes the horror; 80,000 of 120,000 died",
     "deaths": "~80,000", "pop_loss_pct": 67},
    {"city": "Avignon", "lat": 43.95, "lon": 4.81, "year": 1348,
     "note": "Papal seat; Pope Clement VI sat between two fires to purify air",
     "deaths": "~50,000", "pop_loss_pct": 50},
    {"city": "Paris", "lat": 48.86, "lon": 2.35, "year": 1348,
     "note": "800 deaths per day at peak; University of Paris loses half its faculty",
     "deaths": "~80,000", "pop_loss_pct": 50},
    {"city": "Marseille", "lat": 43.30, "lon": 5.37, "year": 1348,
     "note": "Port city devastated within weeks of ship arrivals",
     "deaths": "~25,000", "pop_loss_pct": 50},
    {"city": "Barcelona", "lat": 41.39, "lon": 2.17, "year": 1348,
     "note": "Crown of Aragon loses major workforce; social upheaval follows",
     "deaths": "~38,000", "pop_loss_pct": 60},
    {"city": "London", "lat": 51.51, "lon": -0.13, "year": 1348,
     "note": "Arrived autumn 1348; mass graves at East Smithfield",
     "deaths": "~62,000", "pop_loss_pct": 40},
    {"city": "Bordeaux", "lat": 44.84, "lon": -0.57, "year": 1348,
     "note": "English-held territory; Princess Joan of England dies en route to Castile",
     "deaths": "~20,000", "pop_loss_pct": 45},
    {"city": "Strasbourg", "lat": 48.57, "lon": 7.75, "year": 1349,
     "note": "Strasbourg massacre — 2,000 Jews burned alive as scapegoats",
     "deaths": "~16,000", "pop_loss_pct": 40},
    {"city": "Vienna", "lat": 48.21, "lon": 16.37, "year": 1349,
     "note": "Habsburg territories suffer massive depopulation",
     "deaths": "~30,000", "pop_loss_pct": 40},
    {"city": "Cologne", "lat": 50.94, "lon": 6.96, "year": 1349,
     "note": "Rhineland devastated; flagellant movement peaks",
     "deaths": "~20,000", "pop_loss_pct": 35},
    {"city": "Hamburg", "lat": 53.55, "lon": 9.99, "year": 1349,
     "note": "Hanseatic League disrupted; trade routes collapse",
     "deaths": "~15,000", "pop_loss_pct": 40},
    {"city": "Bergen, Norway", "lat": 60.39, "lon": 5.32, "year": 1349,
     "note": "Arrived via English wool ship; Norway loses 60% population",
     "deaths": "~7,000", "pop_loss_pct": 60},
    {"city": "Stockholm", "lat": 59.33, "lon": 18.07, "year": 1350,
     "note": "Scandinavia ravaged; political upheaval and union movements follow",
     "deaths": "~5,000", "pop_loss_pct": 35},
    {"city": "Novgorod", "lat": 58.52, "lon": 31.28, "year": 1351,
     "note": "Russian principalities hit; commerce along rivers spreads disease",
     "deaths": "~20,000", "pop_loss_pct": 35},
    {"city": "Moscow", "lat": 55.76, "lon": 37.62, "year": 1353,
     "note": "Grand Prince Simeon the Proud and his sons all perish",
     "deaths": "~30,000", "pop_loss_pct": 30},
    {"city": "Cairo", "lat": 30.04, "lon": 31.24, "year": 1348,
     "note": "Mamluk Egypt devastated; 10,000-20,000 deaths per day at peak",
     "deaths": "~200,000", "pop_loss_pct": 40},
    {"city": "Damascus", "lat": 33.51, "lon": 36.29, "year": 1348,
     "note": "Ibn Battuta witnessed; 2,400 deaths in a single day",
     "deaths": "~50,000", "pop_loss_pct": 35},
    {"city": "Tunis", "lat": 36.81, "lon": 10.17, "year": 1348,
     "note": "Ibn Khaldun lost both parents; North Africa severely hit",
     "deaths": "~35,000", "pop_loss_pct": 40},
    {"city": "Baghdad", "lat": 33.31, "lon": 44.37, "year": 1348,
     "note": "Already weakened by Mongol sack; further depopulation",
     "deaths": "~30,000", "pop_loss_pct": 30},
]

BLACK_DEATH_REGIONS = pd.DataFrame([
    {"region": "Italy", "est_population": 11_000_000, "est_deaths": 5_500_000, "pct": 50},
    {"region": "France", "est_population": 17_000_000, "est_deaths": 7_000_000, "pct": 41},
    {"region": "England", "est_population": 5_000_000, "est_deaths": 2_000_000, "pct": 40},
    {"region": "Iberian Peninsula", "est_population": 9_000_000, "est_deaths": 4_500_000, "pct": 50},
    {"region": "Holy Roman Empire", "est_population": 12_000_000, "est_deaths": 4_200_000, "pct": 35},
    {"region": "Scandinavia", "est_population": 2_000_000, "est_deaths": 1_200_000, "pct": 60},
    {"region": "Eastern Europe", "est_population": 8_000_000, "est_deaths": 2_400_000, "pct": 30},
    {"region": "Byzantine Empire", "est_population": 5_000_000, "est_deaths": 2_500_000, "pct": 50},
    {"region": "Middle East", "est_population": 10_000_000, "est_deaths": 3_500_000, "pct": 35},
    {"region": "North Africa", "est_population": 5_000_000, "est_deaths": 2_000_000, "pct": 40},
    {"region": "Central Asia", "est_population": 6_000_000, "est_deaths": 1_800_000, "pct": 30},
])

# ---------- 2. Spanish Flu (1918-1919) ----------
SPANISH_FLU_SPREAD = [
    {"city": "Camp Funston, Kansas", "lat": 39.06, "lon": -96.76, "year": 1918, "month": "March",
     "note": "First major military outbreak — 500 soldiers sick in one week at Fort Riley",
     "wave": 1, "deaths": "~500"},
    {"city": "Camp Devens, Massachusetts", "lat": 42.55, "lon": -71.60, "year": 1918, "month": "September",
     "note": "Second wave begins; 100 soldiers die per day; army doctors overwhelmed",
     "wave": 2, "deaths": "~6,000"},
    {"city": "Philadelphia", "lat": 39.95, "lon": -75.17, "year": 1918, "month": "September",
     "note": "Liberty Loan parade on Sept 28 leads to 12,000 deaths in 6 weeks",
     "wave": 2, "deaths": "~16,000"},
    {"city": "New York City", "lat": 40.71, "lon": -74.01, "year": 1918, "month": "September",
     "note": "850 deaths per day at peak; 30,000 total dead in NYC alone",
     "wave": 2, "deaths": "~30,000"},
    {"city": "San Francisco", "lat": 37.77, "lon": -122.42, "year": 1918, "month": "October",
     "note": "Mandatory mask ordinance — the 'Mask Slackers' controversy",
     "wave": 2, "deaths": "~3,500"},
    {"city": "Brest, France", "lat": 48.39, "lon": -4.49, "year": 1918, "month": "April",
     "note": "Major US troop debarkation port; soldiers carry virus to Western Front",
     "wave": 1, "deaths": "~5,000"},
    {"city": "Sierra Leone", "lat": 8.48, "lon": -13.23, "year": 1918, "month": "August",
     "note": "HMS Mantua brings flu to Freetown; spreads across West Africa",
     "wave": 2, "deaths": "~50,000"},
    {"city": "Madrid", "lat": 40.42, "lon": -3.70, "year": 1918, "month": "May",
     "note": "Neutral Spain freely reports cases — gives pandemic its (misleading) name",
     "wave": 1, "deaths": "~260,000"},
    {"city": "London", "lat": 51.51, "lon": -0.13, "year": 1918, "month": "June",
     "note": "First wave mild; deadly second wave September-November 1918",
     "wave": 2, "deaths": "~225,000"},
    {"city": "Mumbai (Bombay)", "lat": 19.08, "lon": 72.88, "year": 1918, "month": "September",
     "note": "India devastated — 18 million dead, highest toll of any nation",
     "wave": 2, "deaths": "~18,000,000"},
    {"city": "Cape Town", "lat": -33.93, "lon": 18.42, "year": 1918, "month": "September",
     "note": "Troopship Jarvis docks; spreads across southern Africa in weeks",
     "wave": 2, "deaths": "~350,000"},
    {"city": "Sydney", "lat": -33.87, "lon": 151.21, "year": 1919, "month": "January",
     "note": "Maritime quarantine delayed arrival; still 12,000+ dead in Australia",
     "wave": 3, "deaths": "~12,000"},
    {"city": "Tokyo", "lat": 35.68, "lon": 139.69, "year": 1918, "month": "October",
     "note": "Japan suffers 390,000+ deaths despite island isolation",
     "wave": 2, "deaths": "~390,000"},
    {"city": "Rio de Janeiro", "lat": -22.91, "lon": -43.17, "year": 1918, "month": "October",
     "note": "President Rodrigues Alves infected; dies January 1919",
     "wave": 2, "deaths": "~35,000"},
    {"city": "Samoa (Apia)", "lat": -13.83, "lon": -171.76, "year": 1918, "month": "November",
     "note": "Western Samoa loses 22% of entire population — worst proportional toll",
     "wave": 2, "deaths": "~8,500"},
    {"city": "Nome, Alaska", "lat": 64.50, "lon": -165.41, "year": 1918, "month": "November",
     "note": "Remote Inuit communities lose 90% of adults; entire villages perish",
     "wave": 2, "deaths": "~1,000"},
    {"city": "Tehran", "lat": 35.69, "lon": 51.39, "year": 1918, "month": "October",
     "note": "Persia loses estimated 8-22% of total population",
     "wave": 2, "deaths": "~2,000,000"},
]

SPANISH_FLU_WAVES = pd.DataFrame([
    {"wave": "First Wave", "period": "Mar-Jul 1918", "severity": "Mild",
     "characteristics": "High morbidity, low mortality; resembled seasonal flu",
     "est_deaths": "~1-2 million"},
    {"wave": "Second Wave", "period": "Sep-Nov 1918", "severity": "Catastrophic",
     "characteristics": "Cytokine storm killed healthy 20-40 year olds; W-shaped mortality curve",
     "est_deaths": "~40-50 million"},
    {"wave": "Third Wave", "period": "Jan-May 1919", "severity": "Moderate",
     "characteristics": "Resurgence in areas with waning immunity; less lethal than second wave",
     "est_deaths": "~5-10 million"},
])

# ---------- 3. Smallpox History ----------
SMALLPOX_TIMELINE = pd.DataFrame([
    {"year": "10,000 BCE", "event": "Earliest evidence of smallpox-like disease in Egyptian mummies",
     "region": "Egypt", "lat": 30.04, "lon": 31.24},
    {"year": "430 BCE", "event": "Plague of Athens (possibly smallpox) kills 75,000-100,000",
     "region": "Greece", "lat": 37.97, "lon": 23.73},
    {"year": "165 CE", "event": "Antonine Plague (likely smallpox) devastates Roman Empire, kills 5M+",
     "region": "Roman Empire", "lat": 41.90, "lon": 12.50},
    {"year": "710 CE", "event": "Smallpox epidemic in Japan kills up to 1/3 of population",
     "region": "Japan", "lat": 35.68, "lon": 139.69},
    {"year": "1520", "event": "Hernan Cortes' men introduce smallpox to Aztec Empire; 5-8M die",
     "region": "Mexico", "lat": 19.43, "lon": -99.13},
    {"year": "1532", "event": "Smallpox devastates Inca Empire; aids Spanish conquest by Pizarro",
     "region": "Peru", "lat": -12.05, "lon": -77.04},
    {"year": "1633", "event": "Epidemic among Native Americans in New England; 70% mortality",
     "region": "Massachusetts", "lat": 42.36, "lon": -71.06},
    {"year": "1721", "event": "Cotton Mather promotes inoculation (variolation) in Boston",
     "region": "Boston", "lat": 42.36, "lon": -71.06},
    {"year": "1796", "event": "Edward Jenner develops cowpox vaccine — birth of vaccination",
     "region": "England", "lat": 51.69, "lon": -2.22},
    {"year": "1853", "event": "UK Vaccination Act makes smallpox vaccination compulsory",
     "region": "United Kingdom", "lat": 51.51, "lon": -0.13},
    {"year": "1958", "event": "WHO launches global smallpox eradication campaign",
     "region": "Geneva", "lat": 46.20, "lon": 6.14},
    {"year": "1967", "event": "Intensified Eradication Program: ring vaccination strategy",
     "region": "Global", "lat": 0.0, "lon": 0.0},
    {"year": "1975", "event": "Last natural case of Variola major (Rahima Banu, Bangladesh)",
     "region": "Bangladesh", "lat": 23.81, "lon": 90.41},
    {"year": "1977", "event": "Last natural case of Variola minor (Ali Maow Maalin, Somalia)",
     "region": "Somalia", "lat": 2.05, "lon": 45.32},
    {"year": "1980", "event": "WHO officially certifies global smallpox eradication",
     "region": "Geneva", "lat": 46.20, "lon": 6.14},
])

# ---------- 4. Cholera Pandemics ----------
CHOLERA_PANDEMICS = pd.DataFrame([
    {"pandemic": "1st Pandemic", "years": "1817-1824", "origin": "Ganges Delta, India",
     "regions_affected": "India, Southeast Asia, Middle East, East Africa, Mauritius",
     "est_deaths": "~100,000+", "key_event": "First pandemic to spread beyond Indian subcontinent",
     "lat": 22.57, "lon": 88.36},
    {"pandemic": "2nd Pandemic", "years": "1829-1851", "origin": "India",
     "regions_affected": "Europe, North America, Russia, Middle East",
     "est_deaths": "~100,000+", "key_event": "Reached Moscow, Paris, London, New York; galvanized public health reform",
     "lat": 25.32, "lon": 83.01},
    {"pandemic": "3rd Pandemic", "years": "1852-1860", "origin": "India",
     "regions_affected": "Russia, Europe, Americas, Africa, Asia",
     "est_deaths": "~1,000,000+", "key_event": "Deadliest; John Snow's 1854 Broad Street pump investigation",
     "lat": 22.57, "lon": 88.36},
    {"pandemic": "4th Pandemic", "years": "1863-1875", "origin": "Ganges Delta",
     "regions_affected": "Europe, Africa, North America",
     "est_deaths": "~600,000", "key_event": "Naples epidemic of 1866-1867; 30,000 dead in Italy",
     "lat": 22.57, "lon": 88.36},
    {"pandemic": "5th Pandemic", "years": "1881-1896", "origin": "India",
     "regions_affected": "Asia, Africa, South America, Europe",
     "est_deaths": "~300,000+", "key_event": "Robert Koch identifies Vibrio cholerae (1884); Hamburg epidemic 1892",
     "lat": 22.57, "lon": 88.36},
    {"pandemic": "6th Pandemic", "years": "1899-1923", "origin": "India",
     "regions_affected": "Middle East, North Africa, Russia, Balkans",
     "est_deaths": "~800,000+", "key_event": "Last major European outbreak; improved sanitation reduces Western spread",
     "lat": 22.57, "lon": 88.36},
    {"pandemic": "7th Pandemic", "years": "1961-present", "origin": "Sulawesi, Indonesia",
     "regions_affected": "Global (currently Yemen, Haiti, Africa)",
     "est_deaths": "Millions (ongoing)", "key_event": "El Tor biotype; Haiti 2010 after earthquake; Yemen since 2016",
     "lat": -1.43, "lon": 121.45},
])

JOHN_SNOW_PUMPS = [
    {"name": "Broad Street Pump (contaminated)", "lat": 51.5134, "lon": -0.1367,
     "note": "Source of 1854 Soho outbreak; handle removed Sept 8", "contaminated": True},
    {"name": "Carnaby Street Pump", "lat": 51.5130, "lon": -0.1390, "note": "Clean water source", "contaminated": False},
    {"name": "Warwick Street Pump", "lat": 51.5113, "lon": -0.1378, "note": "Clean water source", "contaminated": False},
    {"name": "Bridle Lane Pump", "lat": 51.5121, "lon": -0.1352, "note": "Clean water source", "contaminated": False},
    {"name": "Rupert Street Pump", "lat": 51.5118, "lon": -0.1340, "note": "Clean water source", "contaminated": False},
]

JOHN_SNOW_DEATHS = [
    {"lat": 51.5132, "lon": -0.1365, "deaths": 15},
    {"lat": 51.5135, "lon": -0.1370, "deaths": 8},
    {"lat": 51.5130, "lon": -0.1360, "deaths": 12},
    {"lat": 51.5138, "lon": -0.1363, "deaths": 5},
    {"lat": 51.5128, "lon": -0.1368, "deaths": 10},
    {"lat": 51.5136, "lon": -0.1358, "deaths": 6},
    {"lat": 51.5133, "lon": -0.1372, "deaths": 9},
    {"lat": 51.5129, "lon": -0.1355, "deaths": 7},
    {"lat": 51.5140, "lon": -0.1366, "deaths": 4},
    {"lat": 51.5126, "lon": -0.1375, "deaths": 11},
    {"lat": 51.5137, "lon": -0.1350, "deaths": 3},
    {"lat": 51.5131, "lon": -0.1380, "deaths": 6},
    {"lat": 51.5125, "lon": -0.1362, "deaths": 14},
    {"lat": 51.5139, "lon": -0.1375, "deaths": 2},
    {"lat": 51.5127, "lon": -0.1358, "deaths": 8},
]

# ---------- 6. Malaria Endemic Zones ----------
MALARIA_REGIONS = [
    {"region": "Sub-Saharan Africa", "lat": 0.0, "lon": 25.0, "cases_2022": "~234M",
     "deaths_2022": "~580,000", "risk": "Very High",
     "note": "95% of global malaria deaths; P. falciparum dominant", "color": "#991b1b"},
    {"region": "Southeast Asia", "lat": 15.0, "lon": 105.0, "cases_2022": "~5M",
     "deaths_2022": "~8,000", "risk": "Moderate",
     "note": "Drug-resistant strains emerging in Greater Mekong", "color": "#ef4444"},
    {"region": "South Asia (India)", "lat": 22.0, "lon": 78.0, "cases_2022": "~5.5M",
     "deaths_2022": "~6,700", "risk": "Moderate",
     "note": "P. vivax and P. falciparum co-endemic", "color": "#ef4444"},
    {"region": "Western Pacific", "lat": -5.0, "lon": 140.0, "cases_2022": "~1.5M",
     "deaths_2022": "~2,500", "risk": "Low-Moderate",
     "note": "Papua New Guinea highest burden in region", "color": "#f97316"},
    {"region": "Americas", "lat": 5.0, "lon": -65.0, "cases_2022": "~0.6M",
     "deaths_2022": "~550", "risk": "Low",
     "note": "Amazon basin; Venezuela crisis increased cases", "color": "#f59e0b"},
    {"region": "Eastern Mediterranean", "lat": 25.0, "lon": 45.0, "cases_2022": "~8M",
     "deaths_2022": "~15,000", "risk": "Moderate-High",
     "note": "Sudan, Yemen, Somalia, Pakistan, Afghanistan", "color": "#ef4444"},
    {"region": "Central America", "lat": 14.0, "lon": -87.0, "cases_2022": "~0.15M",
     "deaths_2022": "~50", "risk": "Low",
     "note": "P. vivax predominant; Belize near elimination", "color": "#f59e0b"},
]

MALARIA_MILESTONES = pd.DataFrame([
    {"year": 1880, "event": "Charles Laveran discovers malaria parasite in Algeria"},
    {"year": 1897, "event": "Ronald Ross proves mosquito transmission in India"},
    {"year": 1898, "event": "Giovanni Battista Grassi identifies Anopheles mosquito as vector"},
    {"year": 1934, "event": "Chloroquine synthesized (first effective antimalarial drug)"},
    {"year": 1955, "event": "WHO Global Malaria Eradication Programme (DDT spraying)"},
    {"year": 1969, "event": "Eradication campaign abandoned; focus shifts to control"},
    {"year": 2000, "event": "Roll Back Malaria Partnership launched; bed net campaigns scale up"},
    {"year": 2015, "event": "Tu Youyou wins Nobel Prize for discovering artemisinin"},
    {"year": 2021, "event": "WHO recommends RTS,S (Mosquirix) — first malaria vaccine"},
    {"year": 2023, "event": "R21/Matrix-M vaccine approved by WHO — higher efficacy"},
])

# ---------- 8. Plague of Justinian (541-549) ----------
JUSTINIAN_SPREAD = [
    {"city": "Pelusium, Egypt", "lat": 31.05, "lon": 32.56, "year": 541,
     "note": "First recorded outbreak; arrived via grain ships from East Africa",
     "deaths": "Unknown", "pop_loss_pct": 40},
    {"city": "Alexandria", "lat": 31.20, "lon": 29.92, "year": 541,
     "note": "Major grain port; plague spread via rat-infested granaries",
     "deaths": "~200,000", "pop_loss_pct": 40},
    {"city": "Constantinople", "lat": 41.01, "lon": 28.98, "year": 542,
     "note": "10,000 deaths per day at peak; Emperor Justinian himself infected but survived",
     "deaths": "~300,000", "pop_loss_pct": 40},
    {"city": "Antioch", "lat": 36.20, "lon": 36.16, "year": 542,
     "note": "Already weakened by earthquakes; devastating mortality",
     "deaths": "~100,000", "pop_loss_pct": 35},
    {"city": "Jerusalem", "lat": 31.77, "lon": 35.23, "year": 542,
     "note": "Procopius records bodies piling in streets",
     "deaths": "~30,000", "pop_loss_pct": 30},
    {"city": "Carthage", "lat": 36.86, "lon": 10.32, "year": 543,
     "note": "Recently reconquered by Byzantines; plague undermines control",
     "deaths": "~50,000", "pop_loss_pct": 35},
    {"city": "Rome", "lat": 41.90, "lon": 12.50, "year": 543,
     "note": "Gothic Wars already devastating; plague compounds depopulation",
     "deaths": "~100,000", "pop_loss_pct": 30},
    {"city": "Ravenna", "lat": 44.42, "lon": 12.20, "year": 543,
     "note": "Byzantine administrative center in Italy; government disrupted",
     "deaths": "~20,000", "pop_loss_pct": 25},
    {"city": "Marseille", "lat": 43.30, "lon": 5.37, "year": 543,
     "note": "Plague reaches Gaul through Mediterranean trade routes",
     "deaths": "~15,000", "pop_loss_pct": 25},
    {"city": "Athens", "lat": 37.97, "lon": 23.73, "year": 542,
     "note": "Greece devastated; rural areas depopulated",
     "deaths": "~30,000", "pop_loss_pct": 30},
    {"city": "Ctesiphon (Baghdad)", "lat": 33.09, "lon": 44.58, "year": 542,
     "note": "Sasanian Persian capital; weakens Persia militarily",
     "deaths": "~100,000", "pop_loss_pct": 30},
    {"city": "Aksum, Ethiopia", "lat": 14.12, "lon": 38.73, "year": 541,
     "note": "East African origin theory; trade routes carry plague northward",
     "deaths": "Unknown", "pop_loss_pct": 25},
]

# ---------- 9. Yellow Fever & Tropical Diseases ----------
TROPICAL_DISEASE_ZONES = [
    {"disease": "Yellow Fever", "region": "West Africa", "lat": 7.5, "lon": -5.0,
     "status": "Endemic", "note": "Ancestral home of Aedes aegypti; 200,000 cases/yr",
     "color": "#f59e0b"},
    {"disease": "Yellow Fever", "region": "Central Africa", "lat": 0.0, "lon": 20.0,
     "status": "Endemic", "note": "Sylvatic (jungle) cycle with primates",
     "color": "#f59e0b"},
    {"disease": "Yellow Fever", "region": "South America (Amazon)", "lat": -3.0, "lon": -60.0,
     "status": "Endemic", "note": "Brazil 2016-2019 outbreak killed 750+",
     "color": "#f59e0b"},
    {"disease": "Dengue", "region": "Southeast Asia", "lat": 13.0, "lon": 100.0,
     "status": "Hyperendemic", "note": "All 4 serotypes circulating; 390M infections/yr globally",
     "color": "#f97316"},
    {"disease": "Dengue", "region": "Central America & Caribbean", "lat": 18.0, "lon": -75.0,
     "status": "Endemic", "note": "Major outbreaks in Honduras, Puerto Rico, Dominican Republic",
     "color": "#f97316"},
    {"disease": "Dengue", "region": "South Asia", "lat": 20.0, "lon": 78.0,
     "status": "Endemic", "note": "India reports highest case counts globally",
     "color": "#f97316"},
    {"disease": "Zika", "region": "Brazil (origin of 2015 outbreak)", "lat": -8.0, "lon": -35.0,
     "status": "Post-epidemic", "note": "Linked to microcephaly; 2015-2016 epidemic",
     "color": "#8b5cf6"},
    {"disease": "Zika", "region": "Pacific Islands", "lat": -17.0, "lon": -149.0,
     "status": "Post-epidemic", "note": "French Polynesia 2013-2014 outbreak preceded Americas",
     "color": "#8b5cf6"},
    {"disease": "Ebola", "region": "West Africa (2014-2016)", "lat": 7.5, "lon": -10.0,
     "status": "Outbreak ended", "note": "28,616 cases, 11,310 deaths — largest Ebola outbreak",
     "color": "#dc2626"},
    {"disease": "Ebola", "region": "DRC (2018-2020)", "lat": 0.5, "lon": 29.0,
     "status": "Outbreak ended", "note": "Second largest outbreak: 3,481 cases, 2,299 deaths",
     "color": "#dc2626"},
    {"disease": "Chikungunya", "region": "Indian Ocean", "lat": -12.0, "lon": 49.0,
     "status": "Endemic", "note": "Major epidemic 2005-2006 (Reunion Island, India)",
     "color": "#ec4899"},
    {"disease": "Chagas Disease", "region": "Central & South America", "lat": -15.0, "lon": -55.0,
     "status": "Endemic", "note": "Triatomine bug vector; 6-7 million infected",
     "color": "#10b981"},
]

# ═══════════════════════════════════════════════════════════════
# API FETCH FUNCTIONS
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_covid_countries() -> list:
    """Fetch COVID-19 data for all countries from disease.sh."""
    try:
        resp = requests.get(f"{DISEASE_SH_API}/countries", timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("COVID API error: %s", e)
        return []


@st.cache_data(ttl=3600)
def fetch_covid_global() -> dict:
    """Fetch global COVID-19 summary from disease.sh."""
    try:
        resp = requests.get(f"{DISEASE_SH_API}/all", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("COVID global API error: %s", e)
        return {}


@st.cache_data(ttl=3600)
def fetch_covid_historical(days: int = 30) -> dict:
    """Fetch historical COVID-19 timeline from disease.sh."""
    try:
        resp = requests.get(
            f"{DISEASE_SH_API}/historical/all",
            params={"lastdays": days},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("COVID historical API error: %s", e)
        return {}


@st.cache_data(ttl=3600)
def fetch_who_indicator(indicator_code: str, limit: int = 500) -> list:
    """Fetch WHO GHO indicator data (vaccination, HIV, malaria, etc.)."""
    try:
        url = f"{WHO_GHO_API}/{indicator_code}"
        resp = requests.get(url, params={"$top": limit}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("value", [])
    except Exception as e:
        logger.error("WHO GHO API error for %s: %s", indicator_code, e)
        return []


# Country centroids for mapping WHO data
COUNTRY_COORDS = {
    "AFG": (33.93, 67.71), "AGO": (-11.20, 17.87), "ALB": (41.15, 20.17),
    "ARE": (23.42, 53.85), "ARG": (-38.42, -63.62), "ARM": (40.07, 45.04),
    "AUS": (-25.27, 133.78), "AUT": (47.52, 14.55), "AZE": (40.14, 47.58),
    "BDI": (-3.37, 29.92), "BEL": (50.50, 4.47), "BEN": (9.31, 2.32),
    "BFA": (12.24, -1.56), "BGD": (23.68, 90.36), "BGR": (42.73, 25.49),
    "BHR": (25.93, 50.64), "BHS": (25.03, -77.40), "BIH": (43.92, 17.68),
    "BLR": (53.71, 27.95), "BLZ": (17.19, -88.50), "BOL": (-16.29, -63.59),
    "BRA": (-14.24, -51.93), "BRN": (4.54, 114.73), "BTN": (27.51, 90.43),
    "BWA": (-22.33, 24.68), "CAF": (6.61, 20.94), "CAN": (56.13, -106.35),
    "CHE": (46.82, 8.23), "CHL": (-35.68, -71.54), "CHN": (35.86, 104.20),
    "CIV": (7.54, -5.55), "CMR": (7.37, 12.35), "COD": (-4.04, 21.76),
    "COG": (-0.23, 15.83), "COL": (4.57, -74.30), "CRI": (9.75, -83.75),
    "CUB": (21.52, -77.78), "CYP": (35.13, 33.43), "CZE": (49.82, 15.47),
    "DEU": (51.17, 10.45), "DJI": (11.83, 42.59), "DNK": (56.26, 9.50),
    "DOM": (18.74, -70.16), "DZA": (28.03, 1.66), "ECU": (-1.83, -78.18),
    "EGY": (26.82, 30.80), "ERI": (15.18, 39.78), "ESP": (40.46, -3.75),
    "EST": (58.60, 25.01), "ETH": (9.15, 40.49), "FIN": (61.92, 25.75),
    "FRA": (46.23, 2.21), "GAB": (-0.80, 11.61), "GBR": (55.38, -3.44),
    "GEO": (42.32, 43.36), "GHA": (7.95, -1.02), "GIN": (9.95, -9.70),
    "GMB": (13.44, -15.31), "GNB": (11.80, -15.18), "GNQ": (1.65, 10.27),
    "GRC": (39.07, 21.82), "GTM": (15.78, -90.23), "GUY": (4.86, -58.93),
    "HND": (15.20, -86.24), "HRV": (45.10, 15.20), "HTI": (18.97, -72.29),
    "HUN": (47.16, 19.50), "IDN": (-0.79, 113.92), "IND": (20.59, 78.96),
    "IRL": (53.14, -7.69), "IRN": (32.43, 53.69), "IRQ": (33.22, 43.68),
    "ISL": (64.96, -19.02), "ISR": (31.05, 34.85), "ITA": (41.87, 12.57),
    "JAM": (18.11, -77.30), "JOR": (30.59, 36.24), "JPN": (36.20, 138.25),
    "KAZ": (48.02, 66.92), "KEN": (-0.02, 37.91), "KGZ": (41.20, 74.77),
    "KHM": (12.57, 104.99), "KOR": (35.91, 127.77), "KWT": (29.31, 47.48),
    "LAO": (19.86, 102.50), "LBN": (33.85, 35.86), "LBR": (6.43, -9.43),
    "LBY": (26.34, 17.23), "LKA": (7.87, 80.77), "LSO": (-29.61, 28.23),
    "LTU": (55.17, 23.88), "LVA": (56.88, 24.60), "MAR": (31.79, -7.09),
    "MDA": (47.41, 28.37), "MDG": (-18.77, 46.87), "MEX": (23.63, -102.55),
    "MKD": (41.51, 21.75), "MLI": (17.57, -4.00), "MMR": (21.91, 95.96),
    "MNG": (46.86, 103.85), "MOZ": (-18.67, 35.53), "MRT": (21.01, -10.94),
    "MUS": (-20.35, 57.55), "MWI": (-13.25, 34.30), "MYS": (4.21, 101.98),
    "NAM": (-22.96, 18.49), "NER": (17.61, 8.08), "NGA": (9.08, 8.68),
    "NIC": (12.87, -85.21), "NLD": (52.13, 5.29), "NOR": (60.47, 8.47),
    "NPL": (28.39, 84.12), "NZL": (-40.90, 174.89), "OMN": (21.47, 55.98),
    "PAK": (30.38, 69.35), "PAN": (8.54, -80.78), "PER": (-9.19, -75.02),
    "PHL": (12.88, 121.77), "PNG": (-6.31, 143.96), "POL": (51.92, 19.15),
    "PRT": (39.40, -8.22), "PRY": (-23.44, -58.44), "QAT": (25.35, 51.18),
    "ROU": (45.94, 24.97), "RUS": (61.52, 105.32), "RWA": (-1.94, 29.87),
    "SAU": (23.89, 45.08), "SDN": (12.86, 30.22), "SEN": (14.50, -14.45),
    "SGP": (1.35, 103.82), "SLE": (8.46, -11.78), "SLV": (13.79, -88.90),
    "SOM": (5.15, 46.20), "SRB": (44.02, 21.01), "SSD": (6.88, 31.31),
    "SVK": (48.67, 19.70), "SVN": (46.15, 14.99), "SWE": (60.13, 18.64),
    "SWZ": (-26.52, 31.47), "SYR": (34.80, 38.99), "TCD": (15.45, 18.73),
    "TGO": (8.62, 1.21), "THA": (15.87, 100.99), "TJK": (38.86, 71.28),
    "TKM": (38.97, 59.56), "TLS": (-8.87, 125.73), "TTO": (10.69, -61.22),
    "TUN": (33.89, 9.54), "TUR": (38.96, 35.24), "TZA": (-6.37, 34.89),
    "UGA": (1.37, 32.29), "UKR": (48.38, 31.17), "URY": (-32.52, -55.77),
    "USA": (37.09, -95.71), "UZB": (41.38, 64.59), "VEN": (6.42, -66.59),
    "VNM": (14.06, 108.28), "YEM": (15.55, 48.52), "ZAF": (-30.56, 22.94),
    "ZMB": (-13.13, 27.85), "ZWE": (-19.02, 29.15),
}

# WHO indicator codes
WHO_INDICATORS = {
    "measles_vacc": "WHS4_543",      # MCV1 coverage
    "polio_vacc": "WHS4_544",        # Pol3 coverage
    "dtp3_vacc": "WHS8_110",         # DTP3 coverage
    "hiv_prevalence": "MDG_0000000001",  # HIV prevalence 15-49
    "malaria_incidence": "MALARIA_EST_INCIDENCE",
}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _dark_map(location=None, zoom=3):
    """Create a dark-themed Folium map."""
    loc = location or [20, 0]
    m = folium.Map(
        location=loc,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _render_map(m, height=500):
    """Render a Folium map using components.html."""
    components.html(m._repr_html_(), height=height)


def _severity_color(pct_loss):
    """Return color based on percentage population loss."""
    if pct_loss >= 60:
        return SEVERITY_COLORS["catastrophic"]
    elif pct_loss >= 50:
        return SEVERITY_COLORS["severe"]
    elif pct_loss >= 40:
        return SEVERITY_COLORS["high"]
    elif pct_loss >= 30:
        return SEVERITY_COLORS["moderate"]
    elif pct_loss >= 20:
        return SEVERITY_COLORS["low"]
    return SEVERITY_COLORS["minimal"]


def _covid_color(cases_per_million):
    """Return color based on COVID cases per million."""
    if cases_per_million > 200000:
        return "#991b1b"
    elif cases_per_million > 100000:
        return "#dc2626"
    elif cases_per_million > 50000:
        return "#ef4444"
    elif cases_per_million > 20000:
        return "#f97316"
    elif cases_per_million > 5000:
        return "#f59e0b"
    return "#10b981"


def _format_number(n):
    """Format large numbers with commas."""
    if n is None:
        return "N/A"
    if isinstance(n, str):
        return n
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def _dark_bar_chart(df, x_col, y_col, title, color=ACCENT_CYAN, xlabel="", ylabel=""):
    """Create a dark-themed matplotlib bar chart."""
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BG_PRIMARY)
    ax.set_facecolor(BG_SURFACE)

    bars = ax.bar(range(len(df)), df[y_col], color=color, alpha=0.85, edgecolor=color, linewidth=0.5)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df[x_col], rotation=45, ha="right", fontsize=8, color=TEXT_SECONDARY)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, color=TEXT_SECONDARY, fontsize=9)
    ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=9)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#2a3550")
    ax.spines["bottom"].set_color("#2a3550")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _format_number(x)))
    fig.tight_layout()
    return fig


def _dark_line_chart(x_data, y_data, title, color=ACCENT_CYAN, xlabel="", ylabel=""):
    """Create a dark-themed matplotlib line chart."""
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BG_PRIMARY)
    ax.set_facecolor(BG_SURFACE)

    ax.plot(x_data, y_data, color=color, linewidth=2, alpha=0.9)
    ax.fill_between(x_data, y_data, alpha=0.15, color=color)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, color=TEXT_SECONDARY, fontsize=9)
    ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=9)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    plt.xticks(rotation=45, ha="right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#2a3550")
    ax.spines["bottom"].set_color("#2a3550")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _format_number(x)))
    fig.tight_layout()
    return fig


def _to_csv_bytes(df):
    """Convert DataFrame to CSV bytes for download."""
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8")
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════
# MAP MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_black_death():
    """Mode 1: Black Death (1347-1353)."""
    st.markdown("#### The Black Death (1347-1353)")
    st.markdown(
        "The deadliest pandemic in human history. *Yersinia pestis* spread via fleas on black rats "
        "along Silk Road trade routes and Genoese merchant ships, killing an estimated "
        "**75-200 million people** — roughly **30-60% of Europe's population**. "
        "It took over 200 years for European population to recover to pre-plague levels."
    )

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Estimated Deaths", "75-200M", help="Global death toll estimates vary widely")
    with c2:
        st.metric("Europe Pop. Loss", "30-60%", help="Percentage of European population killed")
    with c3:
        st.metric("Duration", "1347-1353", help="Major wave; recurrences continued for centuries")
    with c4:
        st.metric("Pathogen", "Y. pestis", help="Yersinia pestis — bubonic, pneumonic, septicemic")

    st.markdown("---")

    # Map
    st.markdown("##### Spread Route Map")
    m = _dark_map(location=[42, 20], zoom=4)

    # Draw spread route as polyline (chronological order)
    sorted_cities = sorted(BLACK_DEATH_SPREAD, key=lambda x: (x["year"], x["city"]))
    route_coords = [[c["lat"], c["lon"]] for c in sorted_cities]
    folium.PolyLine(
        route_coords,
        color="#ef4444",
        weight=2,
        opacity=0.5,
        dash_array="8 4",
    ).add_to(m)

    # City markers
    for entry in BLACK_DEATH_SPREAD:
        color = _severity_color(entry["pop_loss_pct"])
        radius = max(5, entry["pop_loss_pct"] / 5)
        popup_html = (
            f"<div style='min-width:200px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:#ef4444'>{escape(entry['city'])}</b><br>"
            f"<b>Year:</b> {escape(str(entry['year']))}<br>"
            f"<b>Deaths:</b> {escape(str(entry['deaths']))}<br>"
            f"<b>Pop. Loss:</b> ~{entry['pop_loss_pct']}%<br>"
            f"<small>{escape(entry['note'])}</small></div>"
        )
        folium.CircleMarker(
            location=[entry["lat"], entry["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(entry['city'])} ({entry['year']})",
        ).add_to(m)

    _render_map(m)

    # Regional death toll chart
    st.markdown("##### Estimated Death Toll by Region")
    fig = _dark_bar_chart(
        BLACK_DEATH_REGIONS, "region", "est_deaths",
        "Black Death — Estimated Deaths by Region",
        color=ACCENT_RED, ylabel="Estimated Deaths",
    )
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    st.markdown("##### Spread Timeline Data")
    df = pd.DataFrame(BLACK_DEATH_SPREAD)
    df = df.sort_values("year")
    st.dataframe(df[["year", "city", "deaths", "pop_loss_pct", "note"]], width="stretch")

    # Download
    st.download_button(
        "Download Black Death Data (CSV)",
        _to_csv_bytes(df),
        file_name="black_death_spread.csv",
        mime="text/csv",
        key="dl_black_death",
    )


def _render_spanish_flu():
    """Mode 2: Spanish Flu (1918-1919)."""
    st.markdown("#### The Spanish Flu (1918-1919)")
    st.markdown(
        "The H1N1 influenza pandemic infected an estimated **500 million people** (one-third of the world's "
        "population) and killed **50-100 million**. Despite its name, it did not originate in Spain — "
        "wartime censorship suppressed reporting in belligerent nations, while neutral Spain freely "
        "reported cases. The second wave was uniquely lethal to healthy 20-40 year olds due to "
        "cytokine storms."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Infected", "~500M", help="About 1/3 of world population")
    with c2:
        st.metric("Deaths", "50-100M", help="Conservative: 50M; high estimates: 100M")
    with c3:
        st.metric("Waves", "3 Waves", help="Spring 1918, Fall 1918 (deadliest), Winter 1919")
    with c4:
        st.metric("Mortality Rate", "2-3%", help="Compared to <0.1% for seasonal flu")

    st.markdown("---")

    # Wave info
    st.markdown("##### Three Waves")
    st.dataframe(SPANISH_FLU_WAVES, width="stretch")

    # Map
    st.markdown("##### Global Spread Map")
    m = _dark_map(location=[20, 0], zoom=2)

    wave_colors = {1: "#f59e0b", 2: "#ef4444", 3: "#8b5cf6"}

    for entry in SPANISH_FLU_SPREAD:
        wave = entry["wave"]
        color = wave_colors.get(wave, "#8b97b0")
        popup_html = (
            f"<div style='min-width:220px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:{color}'>{escape(entry['city'])}</b><br>"
            f"<b>Date:</b> {escape(entry['month'])} {entry['year']}<br>"
            f"<b>Wave:</b> {entry['wave']}<br>"
            f"<b>Deaths:</b> {escape(str(entry['deaths']))}<br>"
            f"<small>{escape(entry['note'])}</small></div>"
        )
        folium.CircleMarker(
            location=[entry["lat"], entry["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(entry['city'])} — Wave {entry['wave']}",
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
         background:#1a2235;padding:10px;border-radius:8px;border:1px solid #2a3550">
    <b style="color:#e8ecf4">Waves</b><br>
    <span style="color:#f59e0b">&#9679;</span> <span style="color:#8b97b0">Wave 1 (Spring 1918)</span><br>
    <span style="color:#ef4444">&#9679;</span> <span style="color:#8b97b0">Wave 2 (Fall 1918)</span><br>
    <span style="color:#8b5cf6">&#9679;</span> <span style="color:#8b97b0">Wave 3 (Winter 1919)</span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    _render_map(m)

    # Data table
    st.markdown("##### Spread Data")
    df = pd.DataFrame(SPANISH_FLU_SPREAD)
    st.dataframe(df[["city", "year", "month", "wave", "deaths", "note"]], width="stretch")

    st.download_button(
        "Download Spanish Flu Data (CSV)",
        _to_csv_bytes(df),
        file_name="spanish_flu_spread.csv",
        mime="text/csv",
        key="dl_spanish_flu",
    )


def _render_smallpox():
    """Mode 3: Smallpox History."""
    st.markdown("#### Smallpox — From Ancient Scourge to Eradication")
    st.markdown(
        "Smallpox (caused by **Variola virus**) killed an estimated **300-500 million people** in the 20th "
        "century alone, and billions across human history. It was the **first disease ever eradicated** "
        "through vaccination — a triumph of global public health officially declared by the WHO on "
        "**May 8, 1980**. Edward Jenner's 1796 cowpox vaccine laid the foundation."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("20th Century Deaths", "~300-500M")
    with c2:
        st.metric("Eradicated", "1980")
    with c3:
        st.metric("Fatality Rate", "~30%", help="Variola major case fatality rate")
    with c4:
        st.metric("Last Natural Case", "1977", help="Ali Maow Maalin, Somalia")

    st.markdown("---")

    # Map
    st.markdown("##### Key Events Map")
    m = _dark_map(location=[25, 30], zoom=2)

    for _, row in SMALLPOX_TIMELINE.iterrows():
        popup_html = (
            f"<div style='min-width:220px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:#06b6d4'>{escape(str(row['year']))}</b><br>"
            f"<b>{escape(row['region'])}</b><br>"
            f"<small>{escape(row['event'])}</small></div>"
        )
        # Color earlier events red, later events green (eradication progress)
        try:
            yr = int(str(row["year"]).replace(",", "").split()[0])
            color = ACCENT_GREEN if yr >= 1796 else ACCENT_RED
        except (ValueError, IndexError):
            color = ACCENT_RED

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(str(row['year']))} — {escape(row['region'])}",
        ).add_to(m)

    _render_map(m)

    # Timeline table
    st.markdown("##### Smallpox Timeline")
    st.dataframe(SMALLPOX_TIMELINE[["year", "region", "event"]], width="stretch")

    st.download_button(
        "Download Smallpox Timeline (CSV)",
        _to_csv_bytes(SMALLPOX_TIMELINE),
        file_name="smallpox_timeline.csv",
        mime="text/csv",
        key="dl_smallpox",
    )


def _render_cholera():
    """Mode 4: Cholera Pandemics."""
    st.markdown("#### Cholera Pandemics (1817-present)")
    st.markdown(
        "**Seven cholera pandemics** have swept the globe since 1817, all originating in the Indian "
        "subcontinent. Cholera (*Vibrio cholerae*) spreads through contaminated water and can kill "
        "within hours. **John Snow's** 1854 investigation of the Broad Street pump outbreak in London "
        "is considered the founding event of modern **epidemiology**."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Pandemics", "7", help="7th pandemic still ongoing since 1961")
    with c2:
        st.metric("Total Deaths", "Millions")
    with c3:
        st.metric("Pathogen", "V. cholerae")
    with c4:
        st.metric("Current Hotspots", "Yemen, Haiti", help="Ongoing outbreaks in conflict zones")

    st.markdown("---")

    # Map view selector
    cholera_view = st.radio(
        "Map View",
        ["7 Pandemics Overview", "John Snow's 1854 London Map"],
        key="cholera_view",
        horizontal=True,
    )

    if cholera_view == "7 Pandemics Overview":
        st.markdown("##### Seven Cholera Pandemics")
        m = _dark_map(location=[25, 50], zoom=3)

        colors = ["#ef4444", "#f97316", "#f59e0b", "#10b981", "#06b6d4", "#8b5cf6", "#ec4899"]
        for i, (_, row) in enumerate(CHOLERA_PANDEMICS.iterrows()):
            color = colors[i % len(colors)]
            popup_html = (
                f"<div style='min-width:220px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
                f"<b style='color:{color}'>{escape(row['pandemic'])}</b><br>"
                f"<b>Years:</b> {escape(row['years'])}<br>"
                f"<b>Origin:</b> {escape(row['origin'])}<br>"
                f"<b>Deaths:</b> {escape(str(row['est_deaths']))}<br>"
                f"<b>Regions:</b> {escape(row['regions_affected'])}<br>"
                f"<small>{escape(row['key_event'])}</small></div>"
            )
            folium.CircleMarker(
                location=[row["lat"] + i * 0.5, row["lon"] + i * 0.5],
                radius=10,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"{escape(row['pandemic'])} ({escape(row['years'])})",
            ).add_to(m)

        _render_map(m)

        st.markdown("##### Pandemic Details")
        st.dataframe(
            CHOLERA_PANDEMICS[["pandemic", "years", "origin", "est_deaths", "regions_affected", "key_event"]],
            width="stretch",
        )

    else:
        # John Snow's 1854 Map
        st.markdown("##### John Snow's Broad Street Investigation (1854)")
        st.markdown(
            "In September 1854, Dr. John Snow mapped cholera deaths near the Broad Street pump "
            "in Soho, London, demonstrating the waterborne nature of cholera. By removing the pump "
            "handle on September 8, he helped end the outbreak. This map recreates his pioneering work."
        )

        m = _dark_map(location=[51.5133, -0.1367], zoom=17)

        # Pump markers
        for pump in JOHN_SNOW_PUMPS:
            color = "#ef4444" if pump["contaminated"] else "#10b981"
            icon_color = "red" if pump["contaminated"] else "green"
            popup_html = (
                f"<div style='min-width:180px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
                f"<b style='color:{color}'>{escape(pump['name'])}</b><br>"
                f"<small>{escape(pump['note'])}</small></div>"
            )
            folium.Marker(
                location=[pump["lat"], pump["lon"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=escape(pump["name"]),
                icon=folium.Icon(color=icon_color, icon="tint", prefix="fa"),
            ).add_to(m)

        # Death clusters
        for death in JOHN_SNOW_DEATHS:
            folium.CircleMarker(
                location=[death["lat"], death["lon"]],
                radius=death["deaths"] * 0.8,
                color="#ef4444",
                fill=True,
                fill_color="#ef4444",
                fill_opacity=0.6,
                tooltip=f"{death['deaths']} deaths",
            ).add_to(m)

        _render_map(m)

    st.download_button(
        "Download Cholera Pandemics Data (CSV)",
        _to_csv_bytes(CHOLERA_PANDEMICS),
        file_name="cholera_pandemics.csv",
        mime="text/csv",
        key="dl_cholera",
    )


def _render_covid():
    """Mode 5: COVID-19 Global (Live Data)."""
    st.markdown("#### COVID-19 Global Dashboard (Live)")
    st.markdown(
        "Real-time COVID-19 data from the **disease.sh** open API. "
        "SARS-CoV-2 was first identified in Wuhan, China in December 2019 and declared a pandemic "
        "by the WHO on March 11, 2020. Data updates daily."
    )

    # Fetch data
    with st.spinner("Fetching live COVID-19 data..."):
        global_data = fetch_covid_global()
        countries_data = fetch_covid_countries()

    if not global_data or not countries_data:
        st.error("Unable to fetch COVID-19 data. The disease.sh API may be temporarily unavailable.")
        return

    # Global stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Global Cases", _format_number(global_data.get("cases", 0)))
    with c2:
        st.metric("Global Deaths", _format_number(global_data.get("deaths", 0)))
    with c3:
        st.metric("Recovered", _format_number(global_data.get("recovered", 0)))
    with c4:
        active = global_data.get("active", 0)
        st.metric("Active Cases", _format_number(active))

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("Cases/Million", _format_number(global_data.get("casesPerOneMillion", 0)))
    with c6:
        st.metric("Deaths/Million", _format_number(global_data.get("deathsPerOneMillion", 0)))
    with c7:
        st.metric("Tests", _format_number(global_data.get("tests", 0)))
    with c8:
        st.metric("Countries", _format_number(global_data.get("affectedCountries", 0)))

    st.markdown("---")

    # Sort options
    sort_col = st.selectbox(
        "Sort countries by",
        ["cases", "deaths", "recovered", "active", "casesPerOneMillion", "deathsPerOneMillion"],
        key="covid_sort",
    )

    # Map
    st.markdown("##### Global Map")
    m = _dark_map(location=[20, 0], zoom=2)

    for country in countries_data:
        info = country.get("countryInfo", {})
        lat = info.get("lat")
        lon = info.get("long")
        if lat is None or lon is None:
            continue

        cases = country.get("cases", 0)
        deaths = country.get("deaths", 0)
        cpm = country.get("casesPerOneMillion", 0) or 0
        color = _covid_color(cpm)

        # Scale radius by log of cases
        import math
        radius = max(3, min(20, math.log10(max(cases, 1)) * 2.5))

        name = escape(country.get("country", "Unknown"))
        popup_html = (
            f"<div style='min-width:200px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:#06b6d4'>{name}</b><br>"
            f"<b>Cases:</b> {cases:,}<br>"
            f"<b>Deaths:</b> {deaths:,}<br>"
            f"<b>Recovered:</b> {country.get('recovered', 0):,}<br>"
            f"<b>Active:</b> {country.get('active', 0):,}<br>"
            f"<b>Cases/1M:</b> {cpm:,.0f}<br>"
            f"<b>Deaths/1M:</b> {country.get('deathsPerOneMillion', 0):,.0f}</div>"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{name}: {cases:,} cases",
        ).add_to(m)

    _render_map(m)

    # Historical chart
    st.markdown("##### Historical Trend (Last 90 days)")
    hist_data = fetch_covid_historical(days=90)
    if hist_data and "cases" in hist_data:
        dates = list(hist_data["cases"].keys())
        cases_vals = list(hist_data["cases"].values())
        fig = _dark_line_chart(
            dates, cases_vals,
            "Cumulative Global COVID-19 Cases",
            color=ACCENT_CYAN, xlabel="Date", ylabel="Cases",
        )
        st.pyplot(fig)
        plt.close(fig)

    # Data table
    st.markdown("##### Country Data")
    rows = []
    for c in countries_data:
        rows.append({
            "Country": c.get("country", ""),
            "Cases": c.get("cases", 0),
            "Deaths": c.get("deaths", 0),
            "Recovered": c.get("recovered", 0),
            "Active": c.get("active", 0),
            "Cases/1M": c.get("casesPerOneMillion", 0),
            "Deaths/1M": c.get("deathsPerOneMillion", 0),
            "Tests": c.get("tests", 0),
            "Population": c.get("population", 0),
        })
    df = pd.DataFrame(rows)
    if sort_col in df.columns or sort_col.replace("Per", "/").replace("OneMillion", "1M") in df.columns:
        col_map = {
            "cases": "Cases", "deaths": "Deaths", "recovered": "Recovered",
            "active": "Active", "casesPerOneMillion": "Cases/1M",
            "deathsPerOneMillion": "Deaths/1M",
        }
        mapped = col_map.get(sort_col, sort_col)
        if mapped in df.columns:
            df = df.sort_values(mapped, ascending=False)

    st.dataframe(df, width="stretch")

    st.download_button(
        "Download COVID-19 Data (CSV)",
        _to_csv_bytes(df),
        file_name="covid19_global.csv",
        mime="text/csv",
        key="dl_covid",
    )


def _render_malaria():
    """Mode 6: Malaria Endemic Zones."""
    st.markdown("#### Malaria Endemic Zones")
    st.markdown(
        "Malaria, caused by *Plasmodium* parasites transmitted by *Anopheles* mosquitoes, "
        "remains one of the deadliest infectious diseases. In 2022, there were an estimated "
        "**249 million cases** and **608,000 deaths** worldwide, with **95% of deaths in Africa**. "
        "Children under 5 account for ~80% of all malaria deaths."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Annual Cases", "~249M", help="WHO 2022 estimate")
    with c2:
        st.metric("Annual Deaths", "~608K", help="WHO 2022 estimate")
    with c3:
        st.metric("Endemic Countries", "85")
    with c4:
        st.metric("Pathogen", "Plasmodium spp.", help="P. falciparum most deadly")

    st.markdown("---")

    # Map
    st.markdown("##### Endemic Regions Map")
    m = _dark_map(location=[10, 30], zoom=3)

    for region in MALARIA_REGIONS:
        popup_html = (
            f"<div style='min-width:220px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:{region['color']}'>{escape(region['region'])}</b><br>"
            f"<b>Risk Level:</b> {escape(region['risk'])}<br>"
            f"<b>Cases (2022):</b> {escape(region['cases_2022'])}<br>"
            f"<b>Deaths (2022):</b> {escape(region['deaths_2022'])}<br>"
            f"<small>{escape(region['note'])}</small></div>"
        )
        folium.CircleMarker(
            location=[region["lat"], region["lon"]],
            radius=15,
            color=region["color"],
            fill=True,
            fill_color=region["color"],
            fill_opacity=0.4,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(region['region'])} — {escape(region['risk'])}",
        ).add_to(m)

    _render_map(m)

    # Milestones timeline
    st.markdown("##### Key Milestones in Malaria History")
    st.dataframe(MALARIA_MILESTONES, width="stretch")

    # Region data
    st.markdown("##### Regional Data")
    df = pd.DataFrame(MALARIA_REGIONS)
    display_df = df[["region", "cases_2022", "deaths_2022", "risk", "note"]]
    st.dataframe(display_df, width="stretch")

    st.download_button(
        "Download Malaria Data (CSV)",
        _to_csv_bytes(display_df),
        file_name="malaria_endemic_zones.csv",
        mime="text/csv",
        key="dl_malaria",
    )


def _render_hiv_aids():
    """Mode 7: HIV/AIDS Global."""
    st.markdown("#### HIV/AIDS Global Overview")
    st.markdown(
        "HIV/AIDS has killed an estimated **40+ million people** since the early 1980s, with "
        "**39 million** currently living with HIV. Sub-Saharan Africa bears the highest burden. "
        "Antiretroviral therapy (ART) has transformed HIV from a death sentence into a manageable "
        "chronic condition, but access remains unequal."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Living with HIV", "~39M", help="UNAIDS 2023 estimate")
    with c2:
        st.metric("Total Deaths", "~40M+", help="Since start of epidemic")
    with c3:
        st.metric("New Infections/yr", "~1.3M", help="2022 estimate")
    with c4:
        st.metric("On ART", "~30M", help="Receiving antiretroviral therapy")

    st.markdown("---")

    # Curated HIV prevalence data (15-49 age group, %)
    hiv_data = [
        {"country": "Eswatini", "iso3": "SWZ", "prevalence": 26.8, "note": "Highest prevalence globally"},
        {"country": "Lesotho", "iso3": "LSO", "prevalence": 21.1, "note": "Southern Africa epicenter"},
        {"country": "Botswana", "iso3": "BWA", "prevalence": 20.8, "note": "Strong ART program"},
        {"country": "South Africa", "iso3": "ZAF", "prevalence": 18.3, "note": "Largest epidemic: 7.8M living with HIV"},
        {"country": "Zimbabwe", "iso3": "ZWE", "prevalence": 11.9, "note": "Prevalence declining from peak"},
        {"country": "Mozambique", "iso3": "MOZ", "prevalence": 12.1, "note": "Rising prevalence in some regions"},
        {"country": "Namibia", "iso3": "NAM", "prevalence": 12.6, "note": "Good ART coverage"},
        {"country": "Zambia", "iso3": "ZMB", "prevalence": 11.1, "note": "Significant progress in treatment"},
        {"country": "Malawi", "iso3": "MWI", "prevalence": 8.1, "note": "Declining due to prevention efforts"},
        {"country": "Uganda", "iso3": "UGA", "prevalence": 5.1, "note": "Early success story; ABC campaign"},
        {"country": "Tanzania", "iso3": "TZA", "prevalence": 4.7, "note": "Varied regional prevalence"},
        {"country": "Kenya", "iso3": "KEN", "prevalence": 4.2, "note": "Lake Victoria region higher"},
        {"country": "Nigeria", "iso3": "NGA", "prevalence": 1.3, "note": "Large absolute numbers: 1.9M living with HIV"},
        {"country": "India", "iso3": "IND", "prevalence": 0.2, "note": "2.4M living with HIV — large absolute number"},
        {"country": "Thailand", "iso3": "THA", "prevalence": 1.0, "note": "Successful prevention programs"},
        {"country": "Brazil", "iso3": "BRA", "prevalence": 0.6, "note": "Free ART since 1996"},
        {"country": "Russia", "iso3": "RUS", "prevalence": 1.2, "note": "Growing epidemic; injection drug use"},
        {"country": "USA", "iso3": "USA", "prevalence": 0.4, "note": "1.2M living with HIV; PrEP expanding"},
        {"country": "Haiti", "iso3": "HTI", "prevalence": 1.7, "note": "Highest prevalence in Caribbean"},
        {"country": "Ethiopia", "iso3": "ETH", "prevalence": 0.9, "note": "Large absolute burden"},
    ]

    # Map
    st.markdown("##### HIV Prevalence Map (Adults 15-49)")
    m = _dark_map(location=[5, 25], zoom=3)

    for entry in hiv_data:
        coords = COUNTRY_COORDS.get(entry["iso3"])
        if not coords:
            continue
        prev = entry["prevalence"]
        if prev >= 20:
            color = "#991b1b"
        elif prev >= 10:
            color = "#dc2626"
        elif prev >= 5:
            color = "#ef4444"
        elif prev >= 1:
            color = "#f97316"
        else:
            color = "#f59e0b"

        radius = max(5, min(18, prev * 0.7))
        popup_html = (
            f"<div style='min-width:200px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:{color}'>{escape(entry['country'])}</b><br>"
            f"<b>Prevalence:</b> {entry['prevalence']}%<br>"
            f"<small>{escape(entry['note'])}</small></div>"
        )
        folium.CircleMarker(
            location=[coords[0], coords[1]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{escape(entry['country'])}: {entry['prevalence']}%",
        ).add_to(m)

    _render_map(m)

    # Chart
    st.markdown("##### HIV Prevalence by Country")
    df = pd.DataFrame(hiv_data).sort_values("prevalence", ascending=False)
    fig = _dark_bar_chart(
        df, "country", "prevalence",
        "HIV Prevalence (Adults 15-49) — Selected Countries",
        color=ACCENT_RED, ylabel="Prevalence (%)",
    )
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    st.dataframe(df[["country", "prevalence", "note"]], width="stretch")

    st.download_button(
        "Download HIV/AIDS Data (CSV)",
        _to_csv_bytes(df),
        file_name="hiv_aids_prevalence.csv",
        mime="text/csv",
        key="dl_hiv",
    )


def _render_justinian():
    """Mode 8: Plague of Justinian (541-549)."""
    st.markdown("#### Plague of Justinian (541-549 CE)")
    st.markdown(
        "The first recorded pandemic of bubonic plague struck the Byzantine (Eastern Roman) Empire "
        "during the reign of Emperor **Justinian I**. Caused by *Yersinia pestis* (same pathogen as "
        "the Black Death), it killed an estimated **25-50 million people** — roughly 13-26% of the "
        "world's population. It ended Justinian's dream of restoring the Roman Empire and contributed "
        "to the transition from antiquity to the medieval period."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Estimated Deaths", "25-50M")
    with c2:
        st.metric("World Pop. Loss", "13-26%", help="~40% in affected regions")
    with c3:
        st.metric("Pathogen", "Y. pestis")
    with c4:
        st.metric("Duration", "541-549 CE", help="Recurrences until ~750 CE")

    st.markdown("---")

    # Map
    st.markdown("##### Spread Map")
    m = _dark_map(location=[35, 25], zoom=4)

    # Draw route
    sorted_j = sorted(JUSTINIAN_SPREAD, key=lambda x: x["year"])
    route = [[c["lat"], c["lon"]] for c in sorted_j]
    folium.PolyLine(route, color="#8b5cf6", weight=2, opacity=0.5, dash_array="8 4").add_to(m)

    for entry in JUSTINIAN_SPREAD:
        color = _severity_color(entry["pop_loss_pct"])
        radius = max(5, entry["pop_loss_pct"] / 4)
        popup_html = (
            f"<div style='min-width:200px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:#8b5cf6'>{escape(entry['city'])}</b><br>"
            f"<b>Year:</b> {entry['year']} CE<br>"
            f"<b>Deaths:</b> {escape(str(entry['deaths']))}<br>"
            f"<b>Pop. Loss:</b> ~{entry['pop_loss_pct']}%<br>"
            f"<small>{escape(entry['note'])}</small></div>"
        )
        folium.CircleMarker(
            location=[entry["lat"], entry["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(entry['city'])} ({entry['year']} CE)",
        ).add_to(m)

    _render_map(m)

    # Data
    st.markdown("##### Spread Timeline")
    df = pd.DataFrame(JUSTINIAN_SPREAD)
    df = df.sort_values("year")
    st.dataframe(df[["year", "city", "deaths", "pop_loss_pct", "note"]], width="stretch")

    st.download_button(
        "Download Plague of Justinian Data (CSV)",
        _to_csv_bytes(df),
        file_name="plague_justinian.csv",
        mime="text/csv",
        key="dl_justinian",
    )


def _render_tropical_diseases():
    """Mode 9: Yellow Fever & Tropical Diseases."""
    st.markdown("#### Yellow Fever & Tropical Diseases")
    st.markdown(
        "Tropical vector-borne diseases remain major global health threats. **Yellow Fever** kills "
        "~30,000-60,000 annually in endemic zones. **Dengue** infects ~390 million/year. The 2014-2016 "
        "**Ebola** outbreak in West Africa killed 11,310. **Zika's** link to microcephaly triggered a "
        "2016 public health emergency. These diseases are expanding their range due to climate change."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Dengue Cases/yr", "~390M", help="Including 96M symptomatic")
    with c2:
        st.metric("Yellow Fever Deaths/yr", "~30-60K")
    with c3:
        st.metric("Ebola Fatality Rate", "~50%", help="Average CFR; varies 25-90%")
    with c4:
        st.metric("Diseases Tracked", "6", help="YF, Dengue, Zika, Ebola, Chikungunya, Chagas")

    st.markdown("---")

    # Filter by disease
    disease_filter = st.multiselect(
        "Filter by Disease",
        ["Yellow Fever", "Dengue", "Zika", "Ebola", "Chikungunya", "Chagas Disease"],
        default=["Yellow Fever", "Dengue", "Zika", "Ebola", "Chikungunya", "Chagas Disease"],
        key="tropical_filter",
    )

    # Map
    st.markdown("##### Endemic/Outbreak Zones")
    m = _dark_map(location=[5, 10], zoom=3)

    filtered = [z for z in TROPICAL_DISEASE_ZONES if z["disease"] in disease_filter]

    for zone in filtered:
        popup_html = (
            f"<div style='min-width:220px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:{zone['color']}'>{escape(zone['disease'])}</b><br>"
            f"<b>Region:</b> {escape(zone['region'])}<br>"
            f"<b>Status:</b> {escape(zone['status'])}<br>"
            f"<small>{escape(zone['note'])}</small></div>"
        )
        folium.CircleMarker(
            location=[zone["lat"], zone["lon"]],
            radius=12,
            color=zone["color"],
            fill=True,
            fill_color=zone["color"],
            fill_opacity=0.5,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(zone['disease'])} — {escape(zone['region'])}",
        ).add_to(m)

    _render_map(m)

    # Data
    st.markdown("##### Disease Zone Data")
    df = pd.DataFrame(filtered)
    if not df.empty:
        st.dataframe(df[["disease", "region", "status", "note"]], width="stretch")

    full_df = pd.DataFrame(TROPICAL_DISEASE_ZONES)
    st.download_button(
        "Download Tropical Disease Data (CSV)",
        _to_csv_bytes(full_df),
        file_name="tropical_diseases.csv",
        mime="text/csv",
        key="dl_tropical",
    )


def _render_vaccination():
    """Mode 10: Vaccination Coverage."""
    st.markdown("#### Global Vaccination Coverage")
    st.markdown(
        "Vaccination is one of the most cost-effective public health interventions. "
        "Despite massive progress, **14.3 million children** remain under- or unvaccinated. "
        "This view shows global coverage for key vaccines using data from the WHO Global Health "
        "Observatory and curated datasets."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Measles (MCV1)", "~83%", help="Global coverage 2022")
    with c2:
        st.metric("DTP3", "~84%", help="3 doses of diphtheria-tetanus-pertussis")
    with c3:
        st.metric("Polio (Pol3)", "~84%", help="3 doses of polio vaccine")
    with c4:
        st.metric("Zero-dose Children", "~14.3M", help="Children who have not received any vaccines")

    st.markdown("---")

    vaccine_type = st.selectbox(
        "Select Vaccine",
        ["Measles (MCV1)", "DTP3", "Polio (Pol3)", "COVID-19 (curated)"],
        key="vacc_type",
    )

    # Curated vaccination data for mapping
    vacc_curated = {
        "Measles (MCV1)": [
            {"country": "Chad", "iso3": "TCD", "coverage": 49},
            {"country": "Central African Republic", "iso3": "CAF", "coverage": 49},
            {"country": "South Sudan", "iso3": "SSD", "coverage": 44},
            {"country": "Somalia", "iso3": "SOM", "coverage": 46},
            {"country": "Guinea", "iso3": "GIN", "coverage": 47},
            {"country": "Nigeria", "iso3": "NGA", "coverage": 57},
            {"country": "Afghanistan", "iso3": "AFG", "coverage": 66},
            {"country": "Ethiopia", "iso3": "ETH", "coverage": 62},
            {"country": "DRC", "iso3": "COD", "coverage": 55},
            {"country": "Pakistan", "iso3": "PAK", "coverage": 78},
            {"country": "India", "iso3": "IND", "coverage": 92},
            {"country": "Indonesia", "iso3": "IDN", "coverage": 79},
            {"country": "Brazil", "iso3": "BRA", "coverage": 80},
            {"country": "Mexico", "iso3": "MEX", "coverage": 88},
            {"country": "USA", "iso3": "USA", "coverage": 92},
            {"country": "Germany", "iso3": "DEU", "coverage": 93},
            {"country": "France", "iso3": "FRA", "coverage": 93},
            {"country": "UK", "iso3": "GBR", "coverage": 90},
            {"country": "China", "iso3": "CHN", "coverage": 97},
            {"country": "Japan", "iso3": "JPN", "coverage": 96},
            {"country": "South Korea", "iso3": "KOR", "coverage": 97},
            {"country": "Australia", "iso3": "AUS", "coverage": 94},
            {"country": "Russia", "iso3": "RUS", "coverage": 96},
            {"country": "South Africa", "iso3": "ZAF", "coverage": 80},
            {"country": "Kenya", "iso3": "KEN", "coverage": 83},
            {"country": "Tanzania", "iso3": "TZA", "coverage": 82},
            {"country": "Egypt", "iso3": "EGY", "coverage": 93},
            {"country": "Iran", "iso3": "IRN", "coverage": 98},
            {"country": "Thailand", "iso3": "THA", "coverage": 91},
            {"country": "Vietnam", "iso3": "VNM", "coverage": 89},
        ],
        "DTP3": [
            {"country": "Chad", "iso3": "TCD", "coverage": 42},
            {"country": "South Sudan", "iso3": "SSD", "coverage": 38},
            {"country": "Somalia", "iso3": "SOM", "coverage": 42},
            {"country": "Central African Republic", "iso3": "CAF", "coverage": 40},
            {"country": "Nigeria", "iso3": "NGA", "coverage": 57},
            {"country": "Afghanistan", "iso3": "AFG", "coverage": 66},
            {"country": "Ethiopia", "iso3": "ETH", "coverage": 67},
            {"country": "DRC", "iso3": "COD", "coverage": 55},
            {"country": "Pakistan", "iso3": "PAK", "coverage": 82},
            {"country": "India", "iso3": "IND", "coverage": 93},
            {"country": "Indonesia", "iso3": "IDN", "coverage": 80},
            {"country": "Brazil", "iso3": "BRA", "coverage": 78},
            {"country": "USA", "iso3": "USA", "coverage": 92},
            {"country": "Germany", "iso3": "DEU", "coverage": 92},
            {"country": "France", "iso3": "FRA", "coverage": 96},
            {"country": "UK", "iso3": "GBR", "coverage": 92},
            {"country": "China", "iso3": "CHN", "coverage": 97},
            {"country": "Japan", "iso3": "JPN", "coverage": 97},
            {"country": "Australia", "iso3": "AUS", "coverage": 95},
            {"country": "Russia", "iso3": "RUS", "coverage": 96},
            {"country": "South Africa", "iso3": "ZAF", "coverage": 80},
            {"country": "Kenya", "iso3": "KEN", "coverage": 80},
            {"country": "Egypt", "iso3": "EGY", "coverage": 95},
            {"country": "Iran", "iso3": "IRN", "coverage": 99},
            {"country": "Thailand", "iso3": "THA", "coverage": 92},
            {"country": "Mexico", "iso3": "MEX", "coverage": 83},
        ],
        "Polio (Pol3)": [
            {"country": "Chad", "iso3": "TCD", "coverage": 43},
            {"country": "South Sudan", "iso3": "SSD", "coverage": 39},
            {"country": "Somalia", "iso3": "SOM", "coverage": 43},
            {"country": "Central African Republic", "iso3": "CAF", "coverage": 41},
            {"country": "Nigeria", "iso3": "NGA", "coverage": 56},
            {"country": "Afghanistan", "iso3": "AFG", "coverage": 67},
            {"country": "Pakistan", "iso3": "PAK", "coverage": 83},
            {"country": "India", "iso3": "IND", "coverage": 93},
            {"country": "DRC", "iso3": "COD", "coverage": 55},
            {"country": "Ethiopia", "iso3": "ETH", "coverage": 68},
            {"country": "Indonesia", "iso3": "IDN", "coverage": 80},
            {"country": "Brazil", "iso3": "BRA", "coverage": 77},
            {"country": "USA", "iso3": "USA", "coverage": 93},
            {"country": "Germany", "iso3": "DEU", "coverage": 92},
            {"country": "France", "iso3": "FRA", "coverage": 96},
            {"country": "UK", "iso3": "GBR", "coverage": 92},
            {"country": "China", "iso3": "CHN", "coverage": 97},
            {"country": "Japan", "iso3": "JPN", "coverage": 97},
            {"country": "Australia", "iso3": "AUS", "coverage": 95},
            {"country": "Russia", "iso3": "RUS", "coverage": 96},
            {"country": "South Africa", "iso3": "ZAF", "coverage": 80},
            {"country": "Egypt", "iso3": "EGY", "coverage": 95},
            {"country": "Iran", "iso3": "IRN", "coverage": 99},
            {"country": "Thailand", "iso3": "THA", "coverage": 92},
            {"country": "Kenya", "iso3": "KEN", "coverage": 82},
            {"country": "Mexico", "iso3": "MEX", "coverage": 85},
        ],
        "COVID-19 (curated)": [
            {"country": "DRC", "iso3": "COD", "coverage": 4},
            {"country": "Haiti", "iso3": "HTI", "coverage": 3},
            {"country": "Chad", "iso3": "TCD", "coverage": 9},
            {"country": "South Sudan", "iso3": "SSD", "coverage": 8},
            {"country": "Madagascar", "iso3": "MDG", "coverage": 6},
            {"country": "Nigeria", "iso3": "NGA", "coverage": 14},
            {"country": "Ethiopia", "iso3": "ETH", "coverage": 34},
            {"country": "South Africa", "iso3": "ZAF", "coverage": 36},
            {"country": "India", "iso3": "IND", "coverage": 67},
            {"country": "Indonesia", "iso3": "IDN", "coverage": 63},
            {"country": "Brazil", "iso3": "BRA", "coverage": 80},
            {"country": "USA", "iso3": "USA", "coverage": 68},
            {"country": "Germany", "iso3": "DEU", "coverage": 76},
            {"country": "France", "iso3": "FRA", "coverage": 78},
            {"country": "UK", "iso3": "GBR", "coverage": 75},
            {"country": "Japan", "iso3": "JPN", "coverage": 83},
            {"country": "South Korea", "iso3": "KOR", "coverage": 87},
            {"country": "Australia", "iso3": "AUS", "coverage": 84},
            {"country": "China", "iso3": "CHN", "coverage": 92},
            {"country": "Chile", "iso3": "CHL", "coverage": 91},
            {"country": "Cuba", "iso3": "CUB", "coverage": 90},
            {"country": "UAE", "iso3": "ARE", "coverage": 98},
            {"country": "Portugal", "iso3": "PRT", "coverage": 87},
            {"country": "Russia", "iso3": "RUS", "coverage": 53},
            {"country": "Pakistan", "iso3": "PAK", "coverage": 48},
            {"country": "Afghanistan", "iso3": "AFG", "coverage": 30},
            {"country": "Mexico", "iso3": "MEX", "coverage": 61},
            {"country": "Kenya", "iso3": "KEN", "coverage": 22},
            {"country": "Egypt", "iso3": "EGY", "coverage": 42},
            {"country": "Iran", "iso3": "IRN", "coverage": 72},
        ],
    }

    data = vacc_curated.get(vaccine_type, vacc_curated["Measles (MCV1)"])

    # Map
    st.markdown(f"##### {vaccine_type} Coverage Map")
    m = _dark_map(location=[20, 0], zoom=2)

    for entry in data:
        coords = COUNTRY_COORDS.get(entry["iso3"])
        if not coords:
            continue
        cov = entry["coverage"]
        if cov >= 90:
            color = "#10b981"
        elif cov >= 80:
            color = "#06b6d4"
        elif cov >= 60:
            color = "#f59e0b"
        elif cov >= 40:
            color = "#f97316"
        else:
            color = "#ef4444"

        radius = max(4, min(14, cov / 8))
        popup_html = (
            f"<div style='min-width:180px;color:#e8ecf4;background:#1a2235;padding:8px;border-radius:6px'>"
            f"<b style='color:{color}'>{escape(entry['country'])}</b><br>"
            f"<b>Coverage:</b> {cov}%</div>"
        )
        folium.CircleMarker(
            location=[coords[0], coords[1]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{escape(entry['country'])}: {cov}%",
        ).add_to(m)

    _render_map(m)

    # Chart
    st.markdown(f"##### {vaccine_type} Coverage by Country")
    df = pd.DataFrame(data).sort_values("coverage", ascending=True)
    fig = _dark_bar_chart(
        df, "country", "coverage",
        f"{vaccine_type} — Vaccination Coverage (%)",
        color=ACCENT_GREEN, ylabel="Coverage (%)",
    )
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df_display = df.sort_values("coverage", ascending=False)
    st.dataframe(df_display[["country", "coverage"]], width="stretch")

    st.download_button(
        f"Download {vaccine_type} Data (CSV)",
        _to_csv_bytes(df_display),
        file_name=f"vaccination_{vaccine_type.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="dl_vaccination",
    )


# ═══════════════════════════════════════════════════════════════
# WHO API DATA FETCH (optional enrichment for vaccination)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def fetch_who_vaccination_data(indicator: str) -> pd.DataFrame:
    """Fetch vaccination coverage from WHO GHO API and parse into DataFrame."""
    raw = fetch_who_indicator(indicator, limit=1000)
    if not raw:
        return pd.DataFrame()
    rows = []
    for item in raw:
        country = item.get("SpatialDim", "")
        year = item.get("TimeDim")
        value = item.get("NumericValue")
        if country and year and value is not None:
            rows.append({"country_code": country, "year": year, "coverage": value})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df


# ═══════════════════════════════════════════════════════════════
# PANDEMIC TIMELINE (cross-cutting reference)
# ═══════════════════════════════════════════════════════════════

PANDEMIC_TIMELINE = pd.DataFrame([
    {"year": "430 BCE", "name": "Plague of Athens", "pathogen": "Unknown (typhoid?)",
     "deaths": "~75-100K", "duration": "5 years"},
    {"year": "165 CE", "name": "Antonine Plague", "pathogen": "Smallpox (probable)",
     "deaths": "~5M", "duration": "15 years"},
    {"year": "249 CE", "name": "Plague of Cyprian", "pathogen": "Unknown (smallpox/measles?)",
     "deaths": "~1M+", "duration": "20 years"},
    {"year": "541 CE", "name": "Plague of Justinian", "pathogen": "Yersinia pestis",
     "deaths": "~25-50M", "duration": "200+ years (recurrences)"},
    {"year": "735 CE", "name": "Japanese Smallpox", "pathogen": "Variola major",
     "deaths": "~1M", "duration": "2 years"},
    {"year": "1347", "name": "Black Death", "pathogen": "Yersinia pestis",
     "deaths": "~75-200M", "duration": "7 years (major wave)"},
    {"year": "1520", "name": "New World Smallpox", "pathogen": "Variola major",
     "deaths": "~25-55M", "duration": "100+ years"},
    {"year": "1629", "name": "Italian Plague", "pathogen": "Yersinia pestis",
     "deaths": "~280K", "duration": "2 years"},
    {"year": "1665", "name": "Great Plague of London", "pathogen": "Yersinia pestis",
     "deaths": "~100K", "duration": "2 years"},
    {"year": "1817", "name": "1st Cholera Pandemic", "pathogen": "Vibrio cholerae",
     "deaths": "~100K+", "duration": "7 years"},
    {"year": "1855", "name": "Third Plague Pandemic", "pathogen": "Yersinia pestis",
     "deaths": "~12-15M", "duration": "~100 years"},
    {"year": "1889", "name": "Russian Flu", "pathogen": "Influenza (H3N8 or HCoV-OC43?)",
     "deaths": "~1M", "duration": "3 years"},
    {"year": "1918", "name": "Spanish Flu", "pathogen": "H1N1 Influenza",
     "deaths": "~50-100M", "duration": "2 years"},
    {"year": "1957", "name": "Asian Flu", "pathogen": "H2N2 Influenza",
     "deaths": "~1-2M", "duration": "2 years"},
    {"year": "1968", "name": "Hong Kong Flu", "pathogen": "H3N2 Influenza",
     "deaths": "~1-4M", "duration": "3 years"},
    {"year": "1981", "name": "HIV/AIDS Pandemic", "pathogen": "HIV",
     "deaths": "~40M+ (ongoing)", "duration": "Ongoing"},
    {"year": "2002", "name": "SARS", "pathogen": "SARS-CoV",
     "deaths": "~774", "duration": "2 years"},
    {"year": "2009", "name": "Swine Flu", "pathogen": "H1N1pdm09",
     "deaths": "~151-575K", "duration": "2 years"},
    {"year": "2014", "name": "Ebola (West Africa)", "pathogen": "Ebolavirus",
     "deaths": "~11,310", "duration": "2 years"},
    {"year": "2015", "name": "Zika Epidemic", "pathogen": "Zika virus",
     "deaths": "~50", "duration": "2 years"},
    {"year": "2019", "name": "COVID-19", "pathogen": "SARS-CoV-2",
     "deaths": "~7M+ (official)", "duration": "Ongoing/Endemic"},
])


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_pandemic_maps_tab():
    """Main render function for the Pandemic & Disease History Maps tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header red"><h4>\U0001f9a0 Pandemic & Disease History Maps</h4>'
        '<p>Historical pandemics, plague routes, epidemics &amp; 10 maps</p></div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.selectbox("Select Map Mode", MAP_MODES, key="pandemic_mode")

    st.markdown("---")

    # ── Dispatch to mode renderer ──
    if mode == MAP_MODES[0]:
        _render_black_death()
    elif mode == MAP_MODES[1]:
        _render_spanish_flu()
    elif mode == MAP_MODES[2]:
        _render_smallpox()
    elif mode == MAP_MODES[3]:
        _render_cholera()
    elif mode == MAP_MODES[4]:
        _render_covid()
    elif mode == MAP_MODES[5]:
        _render_malaria()
    elif mode == MAP_MODES[6]:
        _render_hiv_aids()
    elif mode == MAP_MODES[7]:
        _render_justinian()
    elif mode == MAP_MODES[8]:
        _render_tropical_diseases()
    elif mode == MAP_MODES[9]:
        _render_vaccination()

    # ── Cross-cutting: Pandemic Timeline Reference ──
    st.markdown("---")
    with st.expander("Complete Pandemic Timeline (All Major Pandemics)", expanded=False):
        st.markdown(
            "A chronological reference of major pandemics in human history, "
            "from the Plague of Athens (430 BCE) to COVID-19."
        )
        st.dataframe(PANDEMIC_TIMELINE, width="stretch")
        st.download_button(
            "Download Pandemic Timeline (CSV)",
            _to_csv_bytes(PANDEMIC_TIMELINE),
            file_name="pandemic_timeline.csv",
            mime="text/csv",
            key="dl_timeline",
        )
