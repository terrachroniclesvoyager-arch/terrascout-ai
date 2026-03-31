# -*- coding: utf-8 -*-
"""
Medical & Health Maps module for TerraScout AI.
Provides 10 interactive map modes covering world hospitals, disease outbreaks,
life expectancy, vaccination coverage, malaria risk, healthcare access,
medical tourism, pharmaceutical HQs, traditional medicine, and mental health.
Overpass API for live hospital queries; all other data is hardcoded.
"""

import io
import html
import json
import streamlit as st
import pandas as pd
try:
    import folium
    import folium.plugins as folium_plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import requests
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# ──────────────────────────────────────────────────────────────────────
# COLOR PALETTE (dark theme)
# ──────────────────────────────────────────────────────────────────────
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_ACCENT = "#06b6d4"
_MUTED = "#5a6580"

# ──────────────────────────────────────────────────────────────────────
# CITY PRESETS for hospital search
# ──────────────────────────────────────────────────────────────────────
HOSPITAL_PRESETS = {
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Berlin": {"lat": 52.5200, "lon": 13.4050},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Toronto": {"lat": 43.6532, "lon": -79.3832},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Sao Paulo": {"lat": -23.5505, "lon": -46.6333},
    "Cairo": {"lat": 30.0444, "lon": 31.2357},
    "Seoul": {"lat": 37.5665, "lon": 126.9780},
    "Bangkok": {"lat": 13.7563, "lon": 100.5018},
}

# ──────────────────────────────────────────────────────────────────────
# 2. DISEASE OUTBREAK HISTORY - 40 historical epidemics
# ──────────────────────────────────────────────────────────────────────
DISEASE_OUTBREAKS = [
    {"name": "Black Death", "year": "1347-1351", "lat": 45.0, "lon": 10.0, "deaths": "75-200M", "disease": "Bubonic Plague", "region": "Europe/Asia"},
    {"name": "Spanish Flu", "year": "1918-1920", "lat": 39.0, "lon": -98.0, "deaths": "50-100M", "disease": "Influenza H1N1", "region": "Global"},
    {"name": "Plague of Justinian", "year": "541-542", "lat": 41.0, "lon": 29.0, "deaths": "25-50M", "disease": "Bubonic Plague", "region": "Byzantine Empire"},
    {"name": "HIV/AIDS Pandemic", "year": "1981-present", "lat": -1.3, "lon": 29.0, "deaths": "40M+", "disease": "HIV/AIDS", "region": "Global"},
    {"name": "Third Plague Pandemic", "year": "1855-1960", "lat": 25.0, "lon": 102.0, "deaths": "12-15M", "disease": "Bubonic Plague", "region": "China/India/Global"},
    {"name": "Antonine Plague", "year": "165-180", "lat": 41.9, "lon": 12.5, "deaths": "5-10M", "disease": "Smallpox/Measles", "region": "Roman Empire"},
    {"name": "COVID-19 Pandemic", "year": "2019-2023", "lat": 30.6, "lon": 114.3, "deaths": "7M+ (official)", "disease": "SARS-CoV-2", "region": "Global"},
    {"name": "Plague of Athens", "year": "430-426 BC", "lat": 37.97, "lon": 23.72, "deaths": "75-100K", "disease": "Typhoid/Plague", "region": "Athens"},
    {"name": "Asian Flu", "year": "1957-1958", "lat": 35.0, "lon": 105.0, "deaths": "1-2M", "disease": "Influenza H2N2", "region": "Global"},
    {"name": "Hong Kong Flu", "year": "1968-1970", "lat": 22.3, "lon": 114.2, "deaths": "1-4M", "disease": "Influenza H3N2", "region": "Global"},
    {"name": "Russian Flu", "year": "1889-1890", "lat": 55.8, "lon": 37.6, "deaths": "1M", "disease": "Influenza", "region": "Global"},
    {"name": "Cholera Pandemic 1", "year": "1817-1824", "lat": 22.6, "lon": 88.4, "deaths": "100K+", "disease": "Cholera", "region": "India/SE Asia"},
    {"name": "Cholera Pandemic 2", "year": "1829-1851", "lat": 22.6, "lon": 88.4, "deaths": "100K+", "disease": "Cholera", "region": "India/Europe/Americas"},
    {"name": "Cholera Pandemic 3", "year": "1852-1860", "lat": 55.8, "lon": 37.6, "deaths": "1M+", "disease": "Cholera", "region": "Russia/Europe"},
    {"name": "Cholera Pandemic 6", "year": "1899-1923", "lat": 22.6, "lon": 88.4, "deaths": "800K+", "disease": "Cholera", "region": "India/Middle East"},
    {"name": "Yellow Fever (Philadelphia)", "year": "1793", "lat": 39.95, "lon": -75.17, "deaths": "5K", "disease": "Yellow Fever", "region": "Philadelphia, USA"},
    {"name": "London Great Plague", "year": "1665-1666", "lat": 51.5, "lon": -0.13, "deaths": "100K", "disease": "Bubonic Plague", "region": "London, England"},
    {"name": "Italian Plague", "year": "1629-1631", "lat": 45.46, "lon": 9.19, "deaths": "1M", "disease": "Bubonic Plague", "region": "Northern Italy"},
    {"name": "Great Plague of Marseille", "year": "1720-1723", "lat": 43.3, "lon": 5.37, "deaths": "100K", "disease": "Bubonic Plague", "region": "Marseille, France"},
    {"name": "Smallpox in Americas", "year": "1520-1600", "lat": 19.4, "lon": -99.1, "deaths": "25-56M", "disease": "Smallpox", "region": "Americas"},
    {"name": "West African Ebola", "year": "2013-2016", "lat": 7.5, "lon": -11.8, "deaths": "11.3K", "disease": "Ebola", "region": "West Africa"},
    {"name": "Zika Epidemic", "year": "2015-2016", "lat": -15.8, "lon": -47.9, "deaths": "Minimal direct", "disease": "Zika Virus", "region": "Americas"},
    {"name": "SARS Outbreak", "year": "2002-2003", "lat": 23.1, "lon": 113.3, "deaths": "774", "disease": "SARS-CoV", "region": "China/Global"},
    {"name": "MERS Outbreak", "year": "2012-present", "lat": 24.7, "lon": 46.7, "deaths": "858", "disease": "MERS-CoV", "region": "Middle East"},
    {"name": "Swine Flu", "year": "2009-2010", "lat": 23.6, "lon": -102.5, "deaths": "151-575K", "disease": "Influenza H1N1", "region": "Global"},
    {"name": "Typhus Epidemic (WWI)", "year": "1914-1918", "lat": 44.0, "lon": 21.0, "deaths": "3M+", "disease": "Typhus", "region": "Eastern Europe"},
    {"name": "Japanese Encephalitis", "year": "1871-ongoing", "lat": 35.0, "lon": 136.0, "deaths": "10-15K/year", "disease": "JE Virus", "region": "Asia-Pacific"},
    {"name": "Nipah Virus Outbreak", "year": "1998-1999", "lat": 4.0, "lon": 101.7, "deaths": "105", "disease": "Nipah Virus", "region": "Malaysia/Singapore"},
    {"name": "Marburg Virus", "year": "1967", "lat": 50.8, "lon": 8.77, "deaths": "7", "disease": "Marburg Virus", "region": "Germany/Yugoslavia"},
    {"name": "Dengue (SE Asia)", "year": "1950s-ongoing", "lat": 13.7, "lon": 100.5, "deaths": "20K+/year", "disease": "Dengue Fever", "region": "Southeast Asia"},
    {"name": "Sleeping Sickness", "year": "1896-1906", "lat": 0.3, "lon": 32.6, "deaths": "300-500K", "disease": "Trypanosomiasis", "region": "Uganda/Congo"},
    {"name": "Persian Plague", "year": "1772", "lat": 32.4, "lon": 53.7, "deaths": "2M", "disease": "Bubonic Plague", "region": "Persia"},
    {"name": "Cocoliztli Epidemic", "year": "1545-1548", "lat": 19.4, "lon": -99.1, "deaths": "5-15M", "disease": "Salmonella (suspected)", "region": "Mexico"},
    {"name": "Fiji Measles", "year": "1875", "lat": -17.8, "lon": 178.0, "deaths": "40K (1/3 pop)", "disease": "Measles", "region": "Fiji"},
    {"name": "London Cholera (Broad St)", "year": "1854", "lat": 51.5134, "lon": -0.1365, "deaths": "616", "disease": "Cholera", "region": "London, Soho"},
    {"name": "Polio Epidemic (US)", "year": "1916", "lat": 40.7, "lon": -74.0, "deaths": "6K", "disease": "Poliovirus", "region": "United States"},
    {"name": "Encephalitis Lethargica", "year": "1915-1926", "lat": 48.2, "lon": 16.4, "deaths": "500K+", "disease": "Unknown (viral)", "region": "Europe/Global"},
    {"name": "Haiti Cholera", "year": "2010-2019", "lat": 18.97, "lon": -72.28, "deaths": "10K+", "disease": "Cholera", "region": "Haiti"},
    {"name": "Mpox (Monkeypox)", "year": "2022-2023", "lat": 0.3, "lon": 25.0, "deaths": "140+", "disease": "Monkeypox Virus", "region": "Global"},
    {"name": "Diphtheria Epidemic (Russia)", "year": "1990-1998", "lat": 55.8, "lon": 37.6, "deaths": "5K+", "disease": "Diphtheria", "region": "Former Soviet Union"},
]

# ──────────────────────────────────────────────────────────────────────
# 4. VACCINATION COVERAGE - ~40 countries (DTP3 %)
# ──────────────────────────────────────────────────────────────────────
VACCINATION_DATA = {
    "China": {"lat": 35.0, "lon": 105.0, "dtp3": 99, "measles": 99, "polio": 99},
    "India": {"lat": 20.6, "lon": 78.9, "dtp3": 91, "measles": 92, "polio": 91},
    "United States": {"lat": 39.8, "lon": -98.6, "dtp3": 92, "measles": 92, "polio": 93},
    "Brazil": {"lat": -14.2, "lon": -51.9, "dtp3": 80, "measles": 83, "polio": 78},
    "Russia": {"lat": 61.5, "lon": 105.3, "dtp3": 97, "measles": 97, "polio": 97},
    "Japan": {"lat": 36.2, "lon": 138.3, "dtp3": 98, "measles": 97, "polio": 98},
    "Germany": {"lat": 51.2, "lon": 10.4, "dtp3": 92, "measles": 93, "polio": 93},
    "United Kingdom": {"lat": 55.4, "lon": -3.4, "dtp3": 92, "measles": 90, "polio": 92},
    "France": {"lat": 46.2, "lon": 2.2, "dtp3": 97, "measles": 90, "polio": 97},
    "Italy": {"lat": 41.9, "lon": 12.6, "dtp3": 94, "measles": 93, "polio": 95},
    "Canada": {"lat": 56.1, "lon": -106.3, "dtp3": 90, "measles": 89, "polio": 91},
    "Australia": {"lat": -25.3, "lon": 133.8, "dtp3": 95, "measles": 95, "polio": 95},
    "South Korea": {"lat": 35.9, "lon": 127.8, "dtp3": 98, "measles": 98, "polio": 98},
    "Mexico": {"lat": 23.6, "lon": -102.6, "dtp3": 85, "measles": 88, "polio": 86},
    "Indonesia": {"lat": -0.8, "lon": 113.9, "dtp3": 80, "measles": 82, "polio": 79},
    "Turkey": {"lat": 38.9, "lon": 35.2, "dtp3": 96, "measles": 96, "polio": 96},
    "Saudi Arabia": {"lat": 23.9, "lon": 45.1, "dtp3": 97, "measles": 97, "polio": 97},
    "South Africa": {"lat": -30.6, "lon": 22.9, "dtp3": 80, "measles": 84, "polio": 82},
    "Argentina": {"lat": -38.4, "lon": -63.6, "dtp3": 81, "measles": 87, "polio": 82},
    "Nigeria": {"lat": 9.1, "lon": 8.7, "dtp3": 57, "measles": 54, "polio": 60},
    "Egypt": {"lat": 26.8, "lon": 30.8, "dtp3": 95, "measles": 95, "polio": 95},
    "Pakistan": {"lat": 30.4, "lon": 69.3, "dtp3": 75, "measles": 78, "polio": 76},
    "Bangladesh": {"lat": 23.7, "lon": 90.4, "dtp3": 97, "measles": 96, "polio": 97},
    "Ethiopia": {"lat": 9.1, "lon": 40.5, "dtp3": 68, "measles": 62, "polio": 70},
    "Philippines": {"lat": 12.9, "lon": 121.8, "dtp3": 72, "measles": 69, "polio": 71},
    "Vietnam": {"lat": 14.1, "lon": 108.3, "dtp3": 90, "measles": 93, "polio": 91},
    "Thailand": {"lat": 15.9, "lon": 100.9, "dtp3": 97, "measles": 95, "polio": 97},
    "DR Congo": {"lat": -4.0, "lon": 21.8, "dtp3": 55, "measles": 52, "polio": 58},
    "Kenya": {"lat": -0.02, "lon": 37.9, "dtp3": 87, "measles": 86, "polio": 88},
    "Colombia": {"lat": 4.6, "lon": -74.3, "dtp3": 88, "measles": 90, "polio": 89},
    "Peru": {"lat": -9.2, "lon": -75.0, "dtp3": 82, "measles": 85, "polio": 83},
    "Tanzania": {"lat": -6.4, "lon": 34.9, "dtp3": 90, "measles": 88, "polio": 91},
    "Myanmar": {"lat": 21.9, "lon": 95.9, "dtp3": 78, "measles": 80, "polio": 79},
    "Afghanistan": {"lat": 33.9, "lon": 67.7, "dtp3": 66, "measles": 64, "polio": 73},
    "Mozambique": {"lat": -18.7, "lon": 35.5, "dtp3": 73, "measles": 70, "polio": 74},
    "Ghana": {"lat": 7.9, "lon": -1.0, "dtp3": 88, "measles": 85, "polio": 89},
    "Nepal": {"lat": 28.4, "lon": 84.1, "dtp3": 89, "measles": 87, "polio": 90},
    "Sweden": {"lat": 60.1, "lon": 18.6, "dtp3": 97, "measles": 96, "polio": 97},
    "Norway": {"lat": 60.5, "lon": 8.5, "dtp3": 96, "measles": 95, "polio": 96},
    "Finland": {"lat": 61.9, "lon": 25.7, "dtp3": 95, "measles": 96, "polio": 95},
}

# ──────────────────────────────────────────────────────────────────────
# 5. MALARIA RISK ZONES - ~25 tropical regions
# ──────────────────────────────────────────────────────────────────────
MALARIA_RISK_ZONES = [
    {"region": "Sub-Saharan West Africa", "lat": 8.0, "lon": -2.0, "risk": "Very High", "cases_annual": "80M+", "species": "P. falciparum", "radius": 500000},
    {"region": "Central Africa (Congo Basin)", "lat": -1.0, "lon": 22.0, "risk": "Very High", "cases_annual": "50M+", "species": "P. falciparum", "radius": 600000},
    {"region": "East Africa (Lake Victoria)", "lat": -1.0, "lon": 33.0, "risk": "High", "cases_annual": "30M+", "species": "P. falciparum", "radius": 400000},
    {"region": "Mozambique / Madagascar", "lat": -18.0, "lon": 38.0, "risk": "High", "cases_annual": "15M+", "species": "P. falciparum", "radius": 350000},
    {"region": "Nigeria", "lat": 9.0, "lon": 8.0, "risk": "Very High", "cases_annual": "60M+", "species": "P. falciparum", "radius": 400000},
    {"region": "Indian Subcontinent (East)", "lat": 22.0, "lon": 88.0, "risk": "Moderate", "cases_annual": "10M+", "species": "P. vivax / P. falciparum", "radius": 400000},
    {"region": "Indian Subcontinent (West)", "lat": 20.0, "lon": 73.0, "risk": "Moderate", "cases_annual": "5M+", "species": "P. vivax", "radius": 300000},
    {"region": "Southeast Asia (Myanmar)", "lat": 19.0, "lon": 96.0, "risk": "Moderate", "cases_annual": "3M+", "species": "P. vivax / P. falciparum", "radius": 250000},
    {"region": "Cambodia / Laos / Vietnam", "lat": 12.0, "lon": 105.0, "risk": "Moderate", "cases_annual": "1M+", "species": "P. falciparum (drug-resistant)", "radius": 300000},
    {"region": "Papua New Guinea", "lat": -6.0, "lon": 147.0, "risk": "High", "cases_annual": "2M+", "species": "P. falciparum / P. vivax", "radius": 250000},
    {"region": "Amazon Basin (Brazil)", "lat": -3.0, "lon": -60.0, "risk": "Moderate", "cases_annual": "500K+", "species": "P. vivax", "radius": 500000},
    {"region": "Amazon Basin (Peru/Colombia)", "lat": -4.0, "lon": -73.0, "risk": "Moderate", "cases_annual": "200K+", "species": "P. vivax / P. falciparum", "radius": 300000},
    {"region": "Venezuela / Guyana", "lat": 6.0, "lon": -63.0, "risk": "High", "cases_annual": "400K+", "species": "P. vivax", "radius": 250000},
    {"region": "Central America (Honduras/Guatemala)", "lat": 15.0, "lon": -87.0, "risk": "Low-Moderate", "cases_annual": "50K+", "species": "P. vivax", "radius": 200000},
    {"region": "Horn of Africa (Ethiopia/Somalia)", "lat": 8.0, "lon": 42.0, "risk": "High", "cases_annual": "10M+", "species": "P. falciparum / P. vivax", "radius": 400000},
    {"region": "Sahel Region", "lat": 14.0, "lon": 0.0, "risk": "High (seasonal)", "cases_annual": "20M+", "species": "P. falciparum", "radius": 500000},
    {"region": "Southern Africa (Zambia/Zimbabwe)", "lat": -15.0, "lon": 28.0, "risk": "Moderate", "cases_annual": "5M+", "species": "P. falciparum", "radius": 300000},
    {"region": "Indonesian Archipelago", "lat": -2.0, "lon": 120.0, "risk": "Moderate", "cases_annual": "2M+", "species": "P. falciparum / P. vivax", "radius": 400000},
    {"region": "Solomon Islands", "lat": -8.0, "lon": 159.0, "risk": "High", "cases_annual": "100K+", "species": "P. falciparum / P. vivax", "radius": 150000},
    {"region": "Philippines (Mindanao)", "lat": 7.0, "lon": 126.0, "risk": "Low-Moderate", "cases_annual": "30K+", "species": "P. falciparum", "radius": 150000},
    {"region": "Hispaniola (Haiti/DR)", "lat": 19.0, "lon": -71.0, "risk": "Moderate", "cases_annual": "20K+", "species": "P. falciparum", "radius": 150000},
    {"region": "Yemen", "lat": 15.5, "lon": 48.5, "risk": "High", "cases_annual": "1M+", "species": "P. falciparum", "radius": 200000},
    {"region": "Sudan / South Sudan", "lat": 8.0, "lon": 30.0, "risk": "Very High", "cases_annual": "5M+", "species": "P. falciparum", "radius": 400000},
    {"region": "Angola", "lat": -12.0, "lon": 18.0, "risk": "High", "cases_annual": "8M+", "species": "P. falciparum", "radius": 350000},
    {"region": "Pakistan (Sindh/Balochistan)", "lat": 27.0, "lon": 68.0, "risk": "Moderate", "cases_annual": "1M+", "species": "P. vivax", "radius": 250000},
]

# ──────────────────────────────────────────────────────────────────────
# 6. HEALTHCARE ACCESS INDEX - ~40 countries
# ──────────────────────────────────────────────────────────────────────
HEALTHCARE_ACCESS = {
    "Norway": {"lat": 60.5, "lon": 8.5, "index": 97, "doctors_per_10k": 50, "beds_per_10k": 36, "tier": "Universal"},
    "Switzerland": {"lat": 46.8, "lon": 8.2, "index": 96, "doctors_per_10k": 44, "beds_per_10k": 46, "tier": "Universal"},
    "Sweden": {"lat": 60.1, "lon": 18.6, "index": 95, "doctors_per_10k": 54, "beds_per_10k": 21, "tier": "Universal"},
    "Japan": {"lat": 36.2, "lon": 138.3, "index": 94, "doctors_per_10k": 26, "beds_per_10k": 128, "tier": "Universal"},
    "Australia": {"lat": -25.3, "lon": 133.8, "index": 93, "doctors_per_10k": 38, "beds_per_10k": 38, "tier": "Universal"},
    "Germany": {"lat": 51.2, "lon": 10.4, "index": 92, "doctors_per_10k": 44, "beds_per_10k": 79, "tier": "Universal"},
    "France": {"lat": 46.2, "lon": 2.2, "index": 91, "doctors_per_10k": 33, "beds_per_10k": 58, "tier": "Universal"},
    "Canada": {"lat": 56.1, "lon": -106.3, "index": 90, "doctors_per_10k": 25, "beds_per_10k": 26, "tier": "Universal"},
    "United Kingdom": {"lat": 55.4, "lon": -3.4, "index": 89, "doctors_per_10k": 30, "beds_per_10k": 24, "tier": "Universal"},
    "South Korea": {"lat": 35.9, "lon": 127.8, "index": 88, "doctors_per_10k": 25, "beds_per_10k": 124, "tier": "Universal"},
    "Netherlands": {"lat": 52.1, "lon": 5.3, "index": 90, "doctors_per_10k": 38, "beds_per_10k": 31, "tier": "Universal"},
    "Denmark": {"lat": 56.3, "lon": 9.5, "index": 91, "doctors_per_10k": 42, "beds_per_10k": 25, "tier": "Universal"},
    "Finland": {"lat": 61.9, "lon": 25.7, "index": 90, "doctors_per_10k": 38, "beds_per_10k": 36, "tier": "Universal"},
    "Italy": {"lat": 41.9, "lon": 12.6, "index": 87, "doctors_per_10k": 40, "beds_per_10k": 31, "tier": "Universal"},
    "Spain": {"lat": 40.5, "lon": -3.7, "index": 86, "doctors_per_10k": 41, "beds_per_10k": 29, "tier": "Universal"},
    "United States": {"lat": 39.8, "lon": -98.6, "index": 84, "doctors_per_10k": 26, "beds_per_10k": 29, "tier": "Mixed/Private"},
    "Cuba": {"lat": 21.5, "lon": -78.0, "index": 80, "doctors_per_10k": 84, "beds_per_10k": 53, "tier": "Universal"},
    "China": {"lat": 35.0, "lon": 105.0, "index": 78, "doctors_per_10k": 22, "beds_per_10k": 44, "tier": "Universal (developing)"},
    "Brazil": {"lat": -14.2, "lon": -51.9, "index": 72, "doctors_per_10k": 23, "beds_per_10k": 21, "tier": "Universal (SUS)"},
    "Mexico": {"lat": 23.6, "lon": -102.6, "index": 68, "doctors_per_10k": 24, "beds_per_10k": 10, "tier": "Mixed"},
    "Russia": {"lat": 61.5, "lon": 105.3, "index": 75, "doctors_per_10k": 40, "beds_per_10k": 71, "tier": "Universal"},
    "Turkey": {"lat": 38.9, "lon": 35.2, "index": 74, "doctors_per_10k": 19, "beds_per_10k": 28, "tier": "Universal"},
    "Thailand": {"lat": 15.9, "lon": 100.9, "index": 73, "doctors_per_10k": 8, "beds_per_10k": 21, "tier": "Universal"},
    "South Africa": {"lat": -30.6, "lon": 22.9, "index": 55, "doctors_per_10k": 9, "beds_per_10k": 23, "tier": "Mixed"},
    "India": {"lat": 20.6, "lon": 78.9, "index": 52, "doctors_per_10k": 9, "beds_per_10k": 5, "tier": "Mixed"},
    "Indonesia": {"lat": -0.8, "lon": 113.9, "index": 50, "doctors_per_10k": 6, "beds_per_10k": 10, "tier": "Universal (developing)"},
    "Egypt": {"lat": 26.8, "lon": 30.8, "index": 58, "doctors_per_10k": 8, "beds_per_10k": 14, "tier": "Mixed"},
    "Pakistan": {"lat": 30.4, "lon": 69.3, "index": 40, "doctors_per_10k": 10, "beds_per_10k": 6, "tier": "Mixed"},
    "Bangladesh": {"lat": 23.7, "lon": 90.4, "index": 42, "doctors_per_10k": 6, "beds_per_10k": 8, "tier": "Mixed"},
    "Nigeria": {"lat": 9.1, "lon": 8.7, "index": 35, "doctors_per_10k": 4, "beds_per_10k": 5, "tier": "Mixed (underfunded)"},
    "Ethiopia": {"lat": 9.1, "lon": 40.5, "index": 30, "doctors_per_10k": 1, "beds_per_10k": 3, "tier": "Low-resource"},
    "DR Congo": {"lat": -4.0, "lon": 21.8, "index": 25, "doctors_per_10k": 1, "beds_per_10k": 8, "tier": "Low-resource"},
    "Afghanistan": {"lat": 33.9, "lon": 67.7, "index": 22, "doctors_per_10k": 3, "beds_per_10k": 4, "tier": "Low-resource"},
    "Chad": {"lat": 15.5, "lon": 18.7, "index": 18, "doctors_per_10k": 0.5, "beds_per_10k": 4, "tier": "Low-resource"},
    "Somalia": {"lat": 5.2, "lon": 46.2, "index": 15, "doctors_per_10k": 0.3, "beds_per_10k": 9, "tier": "Low-resource"},
    "Saudi Arabia": {"lat": 23.9, "lon": 45.1, "index": 76, "doctors_per_10k": 27, "beds_per_10k": 22, "tier": "Universal"},
    "Israel": {"lat": 31.0, "lon": 34.8, "index": 89, "doctors_per_10k": 36, "beds_per_10k": 30, "tier": "Universal"},
    "New Zealand": {"lat": -40.9, "lon": 174.9, "index": 91, "doctors_per_10k": 36, "beds_per_10k": 26, "tier": "Universal"},
    "Singapore": {"lat": 1.35, "lon": 103.8, "index": 86, "doctors_per_10k": 24, "beds_per_10k": 25, "tier": "Mixed/Universal"},
    "Colombia": {"lat": 4.6, "lon": -74.3, "index": 65, "doctors_per_10k": 22, "beds_per_10k": 17, "tier": "Universal"},
}

# ──────────────────────────────────────────────────────────────────────
# 7. MEDICAL TOURISM - ~30 top cities
# ──────────────────────────────────────────────────────────────────────
MEDICAL_TOURISM = [
    {"city": "Bangkok", "country": "Thailand", "lat": 13.76, "lon": 100.50, "specialty": "Cosmetic Surgery, Cardiac", "hospital": "Bumrungrad International", "patients_yr": "2.5M", "savings": "50-70%"},
    {"city": "Singapore", "country": "Singapore", "lat": 1.35, "lon": 103.82, "specialty": "Oncology, Cardiology", "hospital": "Mount Elizabeth", "patients_yr": "500K", "savings": "30-50%"},
    {"city": "Seoul", "country": "South Korea", "lat": 37.57, "lon": 126.98, "specialty": "Cosmetic, Robotic Surgery", "hospital": "Samsung Medical Center", "patients_yr": "400K", "savings": "30-45%"},
    {"city": "Mumbai", "country": "India", "lat": 19.08, "lon": 72.88, "specialty": "Cardiac, Orthopedic", "hospital": "Kokilaben Hospital", "patients_yr": "2M", "savings": "65-90%"},
    {"city": "Istanbul", "country": "Turkey", "lat": 41.01, "lon": 28.98, "specialty": "Hair Transplant, Dental", "hospital": "Acibadem Healthcare", "patients_yr": "1.2M", "savings": "50-70%"},
    {"city": "Kuala Lumpur", "country": "Malaysia", "lat": 3.14, "lon": 101.69, "specialty": "Fertility, Cardiac", "hospital": "Prince Court Medical", "patients_yr": "1M", "savings": "50-65%"},
    {"city": "San Jose", "country": "Costa Rica", "lat": 9.93, "lon": -84.08, "specialty": "Dental, Cosmetic", "hospital": "CIMA Hospital", "patients_yr": "200K", "savings": "40-65%"},
    {"city": "Mexico City", "country": "Mexico", "lat": 19.43, "lon": -99.13, "specialty": "Dental, Bariatric", "hospital": "Hospital Angeles", "patients_yr": "1.5M", "savings": "40-65%"},
    {"city": "Dubai", "country": "UAE", "lat": 25.20, "lon": 55.27, "specialty": "Orthopedic, Dermatology", "hospital": "Cleveland Clinic Abu Dhabi", "patients_yr": "500K", "savings": "20-40%"},
    {"city": "Taipei", "country": "Taiwan", "lat": 25.03, "lon": 121.57, "specialty": "Liver Transplant, Cardiac", "hospital": "National Taiwan Univ Hospital", "patients_yr": "300K", "savings": "40-55%"},
    {"city": "Budapest", "country": "Hungary", "lat": 47.50, "lon": 19.04, "specialty": "Dental, Thermal Spa Medicine", "hospital": "Various Dental Clinics", "patients_yr": "400K", "savings": "40-70%"},
    {"city": "Tel Aviv", "country": "Israel", "lat": 32.09, "lon": 34.78, "specialty": "Fertility (IVF), Oncology", "hospital": "Sheba Medical Center", "patients_yr": "200K", "savings": "20-30%"},
    {"city": "Medellin", "country": "Colombia", "lat": 6.25, "lon": -75.56, "specialty": "Cosmetic, Dental", "hospital": "Clinica Las Americas", "patients_yr": "100K", "savings": "50-70%"},
    {"city": "Chennai", "country": "India", "lat": 13.08, "lon": 80.27, "specialty": "Cardiac, Orthopedic", "hospital": "Apollo Hospitals", "patients_yr": "800K", "savings": "65-90%"},
    {"city": "Penang", "country": "Malaysia", "lat": 5.42, "lon": 100.33, "specialty": "General Surgery, Oncology", "hospital": "Penang Adventist Hospital", "patients_yr": "500K", "savings": "50-65%"},
    {"city": "Havana", "country": "Cuba", "lat": 23.11, "lon": -82.37, "specialty": "Eye Surgery, Orthopedics", "hospital": "CIMEQ Hospital", "patients_yr": "100K", "savings": "60-80%"},
    {"city": "Bangalore", "country": "India", "lat": 12.97, "lon": 77.59, "specialty": "Neurosurgery, Cardiac", "hospital": "Narayana Health", "patients_yr": "600K", "savings": "65-90%"},
    {"city": "Warsaw", "country": "Poland", "lat": 52.23, "lon": 21.01, "specialty": "Dental, Ophthalmology", "hospital": "Various Specialist Clinics", "patients_yr": "200K", "savings": "40-60%"},
    {"city": "Panama City", "country": "Panama", "lat": 8.98, "lon": -79.52, "specialty": "Dental, Cosmetic", "hospital": "Johns Hopkins Panama", "patients_yr": "80K", "savings": "40-60%"},
    {"city": "Phuket", "country": "Thailand", "lat": 7.88, "lon": 98.39, "specialty": "Cosmetic, Dental", "hospital": "Bangkok Hospital Phuket", "patients_yr": "300K", "savings": "50-70%"},
    {"city": "Abu Dhabi", "country": "UAE", "lat": 24.45, "lon": 54.65, "specialty": "Orthopedic, Oncology", "hospital": "Cleveland Clinic Abu Dhabi", "patients_yr": "200K", "savings": "20-30%"},
    {"city": "Prague", "country": "Czech Republic", "lat": 50.08, "lon": 14.44, "specialty": "Cosmetic, Dental", "hospital": "Canadian Medical", "patients_yr": "150K", "savings": "40-60%"},
    {"city": "Amman", "country": "Jordan", "lat": 31.95, "lon": 35.93, "specialty": "Cardiac, General Surgery", "hospital": "King Hussein Cancer Center", "patients_yr": "250K", "savings": "50-70%"},
    {"city": "Manila", "country": "Philippines", "lat": 14.60, "lon": 120.98, "specialty": "Dental, Cosmetic, Eye", "hospital": "St. Luke's Medical Center", "patients_yr": "200K", "savings": "50-70%"},
    {"city": "Tokyo", "country": "Japan", "lat": 35.68, "lon": 139.65, "specialty": "Robotic Surgery, Oncology", "hospital": "University of Tokyo Hospital", "patients_yr": "100K", "savings": "10-20%"},
    {"city": "Antalya", "country": "Turkey", "lat": 36.90, "lon": 30.69, "specialty": "Dental, Cosmetic", "hospital": "Antalya Medical Park", "patients_yr": "500K", "savings": "50-70%"},
    {"city": "New Delhi", "country": "India", "lat": 28.61, "lon": 77.21, "specialty": "Cardiac, Joint Replacement", "hospital": "Max Super Speciality", "patients_yr": "1M", "savings": "65-90%"},
    {"city": "Bogota", "country": "Colombia", "lat": 4.71, "lon": -74.07, "specialty": "Cosmetic, Dental, Bariatric", "hospital": "Fundacion Santa Fe", "patients_yr": "200K", "savings": "50-70%"},
    {"city": "Riyadh", "country": "Saudi Arabia", "lat": 24.71, "lon": 46.67, "specialty": "Cardiac, Oncology", "hospital": "King Faisal Specialist Hospital", "patients_yr": "150K", "savings": "10-20%"},
    {"city": "Johannesburg", "country": "South Africa", "lat": -26.20, "lon": 28.04, "specialty": "Transplant, Cosmetic", "hospital": "Netcare Group", "patients_yr": "100K", "savings": "30-50%"},
]

# ──────────────────────────────────────────────────────────────────────
# 8. PHARMACEUTICAL HQs - ~40 companies
# ──────────────────────────────────────────────────────────────────────
PHARMA_HQS = [
    {"company": "Pfizer", "city": "New York", "country": "USA", "lat": 40.755, "lon": -73.980, "revenue_b": 58.5, "specialty": "Vaccines, Oncology"},
    {"company": "Johnson & Johnson", "city": "New Brunswick", "country": "USA", "lat": 40.487, "lon": -74.445, "revenue_b": 52.3, "specialty": "Med Devices, Pharma"},
    {"company": "Roche", "city": "Basel", "country": "Switzerland", "lat": 47.560, "lon": 7.590, "revenue_b": 50.1, "specialty": "Oncology, Diagnostics"},
    {"company": "Novartis", "city": "Basel", "country": "Switzerland", "lat": 47.565, "lon": 7.585, "revenue_b": 41.2, "specialty": "Oncology, Gene Therapy"},
    {"company": "Merck & Co.", "city": "Rahway", "country": "USA", "lat": 40.610, "lon": -74.278, "revenue_b": 48.0, "specialty": "Oncology, Vaccines"},
    {"company": "AbbVie", "city": "North Chicago", "country": "USA", "lat": 42.327, "lon": -87.844, "revenue_b": 54.3, "specialty": "Immunology, Oncology"},
    {"company": "Sanofi", "city": "Paris", "country": "France", "lat": 48.858, "lon": 2.286, "revenue_b": 42.9, "specialty": "Vaccines, Rare Disease"},
    {"company": "AstraZeneca", "city": "Cambridge", "country": "UK", "lat": 52.235, "lon": 0.154, "revenue_b": 44.4, "specialty": "Oncology, Respiratory"},
    {"company": "GlaxoSmithKline (GSK)", "city": "London", "country": "UK", "lat": 51.494, "lon": -0.181, "revenue_b": 30.3, "specialty": "Vaccines, Respiratory"},
    {"company": "Novo Nordisk", "city": "Bagsvaerd", "country": "Denmark", "lat": 55.755, "lon": 12.450, "revenue_b": 33.7, "specialty": "Diabetes, Obesity"},
    {"company": "Eli Lilly", "city": "Indianapolis", "country": "USA", "lat": 39.768, "lon": -86.158, "revenue_b": 28.5, "specialty": "Diabetes, Oncology"},
    {"company": "Bristol-Myers Squibb", "city": "New York", "country": "USA", "lat": 40.754, "lon": -73.970, "revenue_b": 26.0, "specialty": "Oncology, Immunology"},
    {"company": "Amgen", "city": "Thousand Oaks", "country": "USA", "lat": 34.189, "lon": -118.874, "revenue_b": 24.2, "specialty": "Biosimilars, Oncology"},
    {"company": "Gilead Sciences", "city": "Foster City", "country": "USA", "lat": 37.558, "lon": -122.271, "revenue_b": 22.1, "specialty": "Antiviral, HIV"},
    {"company": "Bayer", "city": "Leverkusen", "country": "Germany", "lat": 51.040, "lon": 6.990, "revenue_b": 20.5, "specialty": "Cardiology, Crop Science"},
    {"company": "Takeda", "city": "Tokyo", "country": "Japan", "lat": 35.694, "lon": 139.751, "revenue_b": 28.4, "specialty": "GI, Oncology, Rare Disease"},
    {"company": "Boehringer Ingelheim", "city": "Ingelheim", "country": "Germany", "lat": 49.978, "lon": 8.067, "revenue_b": 22.8, "specialty": "Respiratory, Cardio"},
    {"company": "Moderna", "city": "Cambridge", "country": "USA", "lat": 42.363, "lon": -71.080, "revenue_b": 18.4, "specialty": "mRNA Vaccines"},
    {"company": "BioNTech", "city": "Mainz", "country": "Germany", "lat": 49.999, "lon": 8.247, "revenue_b": 17.3, "specialty": "mRNA, Immunotherapy"},
    {"company": "Regeneron", "city": "Tarrytown", "country": "USA", "lat": 41.064, "lon": -73.858, "revenue_b": 12.2, "specialty": "Eye Care, Immunology"},
    {"company": "Teva Pharmaceutical", "city": "Tel Aviv", "country": "Israel", "lat": 32.066, "lon": 34.770, "revenue_b": 14.9, "specialty": "Generics, Biosimilars"},
    {"company": "Astellas Pharma", "city": "Tokyo", "country": "Japan", "lat": 35.688, "lon": 139.698, "revenue_b": 11.1, "specialty": "Urology, Transplant"},
    {"company": "Daiichi Sankyo", "city": "Tokyo", "country": "Japan", "lat": 35.680, "lon": 139.744, "revenue_b": 9.6, "specialty": "Oncology, Cardiology"},
    {"company": "CSL Behring", "city": "Melbourne", "country": "Australia", "lat": -37.814, "lon": 144.963, "revenue_b": 10.5, "specialty": "Plasma, Immunology"},
    {"company": "Sun Pharma", "city": "Mumbai", "country": "India", "lat": 19.090, "lon": 72.870, "revenue_b": 5.4, "specialty": "Generics, Dermatology"},
    {"company": "Dr. Reddy's", "city": "Hyderabad", "country": "India", "lat": 17.385, "lon": 78.487, "revenue_b": 2.9, "specialty": "Generics, Biosimilars"},
    {"company": "Cipla", "city": "Mumbai", "country": "India", "lat": 19.100, "lon": 72.880, "revenue_b": 3.0, "specialty": "Generics, Respiratory"},
    {"company": "Samsung Biologics", "city": "Incheon", "country": "South Korea", "lat": 37.380, "lon": 126.662, "revenue_b": 2.1, "specialty": "Biosimilars, CDMO"},
    {"company": "Celltrion", "city": "Incheon", "country": "South Korea", "lat": 37.400, "lon": 126.670, "revenue_b": 2.0, "specialty": "Biosimilars"},
    {"company": "Sinopharm", "city": "Beijing", "country": "China", "lat": 39.904, "lon": 116.407, "revenue_b": 7.2, "specialty": "Vaccines, Distribution"},
    {"company": "Sinovac", "city": "Beijing", "country": "China", "lat": 39.950, "lon": 116.330, "revenue_b": 3.5, "specialty": "Vaccines"},
    {"company": "Jiangsu Hengrui", "city": "Lianyungang", "country": "China", "lat": 34.600, "lon": 119.222, "revenue_b": 3.8, "specialty": "Oncology, Anesthesia"},
    {"company": "Biocon", "city": "Bangalore", "country": "India", "lat": 12.960, "lon": 77.590, "revenue_b": 1.3, "specialty": "Biosimilars, Insulin"},
    {"company": "Lupin", "city": "Mumbai", "country": "India", "lat": 19.095, "lon": 72.860, "revenue_b": 2.0, "specialty": "Generics, TB drugs"},
    {"company": "Ferring Pharmaceuticals", "city": "Saint-Prex", "country": "Switzerland", "lat": 46.483, "lon": 6.443, "revenue_b": 2.3, "specialty": "Reproductive Health"},
    {"company": "Menarini", "city": "Florence", "country": "Italy", "lat": 43.770, "lon": 11.249, "revenue_b": 4.2, "specialty": "Cardiology, Pain"},
    {"company": "Ipsen", "city": "Paris", "country": "France", "lat": 48.870, "lon": 2.340, "revenue_b": 3.4, "specialty": "Oncology, Rare Disease"},
    {"company": "LEO Pharma", "city": "Ballerup", "country": "Denmark", "lat": 55.730, "lon": 12.360, "revenue_b": 1.6, "specialty": "Dermatology"},
    {"company": "Ono Pharmaceutical", "city": "Osaka", "country": "Japan", "lat": 34.694, "lon": 135.502, "revenue_b": 3.3, "specialty": "Oncology, Immunology"},
    {"company": "Zoetis", "city": "Parsippany", "country": "USA", "lat": 40.857, "lon": -74.416, "revenue_b": 8.1, "specialty": "Animal Health"},
]

# ──────────────────────────────────────────────────────────────────────
# 9. TRADITIONAL MEDICINE CENTERS - ~30 centers
# ──────────────────────────────────────────────────────────────────────
TRADITIONAL_MEDICINE = [
    {"name": "Beijing TCM Hospital", "city": "Beijing", "country": "China", "lat": 39.93, "lon": 116.39, "tradition": "Traditional Chinese Medicine", "specialty": "Acupuncture, Herbal", "founded": "1956"},
    {"name": "Guangzhou TCM University Hospital", "city": "Guangzhou", "country": "China", "lat": 23.13, "lon": 113.28, "tradition": "Traditional Chinese Medicine", "specialty": "Herbal Formulas", "founded": "1964"},
    {"name": "Shanghai Longhua Hospital", "city": "Shanghai", "country": "China", "lat": 31.17, "lon": 121.44, "tradition": "Traditional Chinese Medicine", "specialty": "Oncology TCM", "founded": "1960"},
    {"name": "Arya Vaidya Sala", "city": "Kottakkal", "country": "India", "lat": 10.99, "lon": 76.00, "tradition": "Ayurveda", "specialty": "Panchakarma, Herbal", "founded": "1902"},
    {"name": "Kerala Ayurveda Centre", "city": "Thiruvananthapuram", "country": "India", "lat": 8.52, "lon": 76.94, "tradition": "Ayurveda", "specialty": "Rejuvenation Therapy", "founded": "1943"},
    {"name": "Patanjali Yogpeeth", "city": "Haridwar", "country": "India", "lat": 29.93, "lon": 78.16, "tradition": "Ayurveda / Yoga", "specialty": "Yoga Therapy, Herbal", "founded": "2006"},
    {"name": "Jivagram Naturopathy Centre", "city": "Bangalore", "country": "India", "lat": 12.97, "lon": 77.60, "tradition": "Ayurveda / Naturopathy", "specialty": "Detox, Panchakarma", "founded": "1994"},
    {"name": "Men-Tsee-Khang", "city": "Dharamsala", "country": "India", "lat": 32.22, "lon": 76.32, "tradition": "Tibetan Medicine (Sowa Rigpa)", "specialty": "Herbal, Spiritual Healing", "founded": "1961"},
    {"name": "Kampo Medicine Center (Keio)", "city": "Tokyo", "country": "Japan", "lat": 35.70, "lon": 139.74, "tradition": "Kampo (Japanese Herbal)", "specialty": "Herbal Prescriptions", "founded": "1980"},
    {"name": "Kyung Hee Korean Medicine Hospital", "city": "Seoul", "country": "South Korea", "lat": 37.60, "lon": 127.05, "tradition": "Korean Medicine (Hanbang)", "specialty": "Acupuncture, Herbal", "founded": "1971"},
    {"name": "Jaseng Hospital", "city": "Seoul", "country": "South Korea", "lat": 37.50, "lon": 127.02, "tradition": "Korean Medicine", "specialty": "Spinal, Musculoskeletal", "founded": "2003"},
    {"name": "Penang Tua Pek Kong TCM", "city": "Penang", "country": "Malaysia", "lat": 5.42, "lon": 100.35, "tradition": "Traditional Chinese Medicine", "specialty": "Herbal, Tuina Massage", "founded": "1950"},
    {"name": "Wat Pho Thai Medicine School", "city": "Bangkok", "country": "Thailand", "lat": 13.75, "lon": 100.49, "tradition": "Thai Traditional Medicine", "specialty": "Thai Massage, Herbal", "founded": "1955"},
    {"name": "Chiang Mai Thai Lanna Healing", "city": "Chiang Mai", "country": "Thailand", "lat": 18.79, "lon": 98.98, "tradition": "Lanna Traditional Medicine", "specialty": "Herbal Compress, Tok Sen", "founded": "1985"},
    {"name": "Umnugobi Mongol Medicine Center", "city": "Ulaanbaatar", "country": "Mongolia", "lat": 47.92, "lon": 106.91, "tradition": "Mongolian Traditional Medicine", "specialty": "Bone-setting, Herbal", "founded": "1992"},
    {"name": "Muhimbili Traditional Medicine", "city": "Dar es Salaam", "country": "Tanzania", "lat": -6.80, "lon": 39.28, "tradition": "African Traditional Medicine", "specialty": "Herbal, Spiritual", "founded": "1974"},
    {"name": "PROMETRA International", "city": "Dakar", "country": "Senegal", "lat": 14.69, "lon": -17.44, "tradition": "African Traditional Medicine", "specialty": "Ethno-medicine Research", "founded": "1971"},
    {"name": "Ifakara Traditional Healers Assoc.", "city": "Ifakara", "country": "Tanzania", "lat": -8.13, "lon": 36.68, "tradition": "African Traditional Medicine", "specialty": "Malaria Herbal Treatment", "founded": "1990"},
    {"name": "Unani Medicine Faculty (Aligarh)", "city": "Aligarh", "country": "India", "lat": 27.91, "lon": 78.08, "tradition": "Unani Medicine", "specialty": "Greco-Arabic Herbal", "founded": "1962"},
    {"name": "Curanderismo Center", "city": "Oaxaca", "country": "Mexico", "lat": 17.07, "lon": -96.73, "tradition": "Mesoamerican Curanderismo", "specialty": "Herbal, Spiritual Cleansing", "founded": "Traditional"},
    {"name": "Pachamama Healing Center", "city": "Iquitos", "country": "Peru", "lat": -3.75, "lon": -73.25, "tradition": "Amazonian Plant Medicine", "specialty": "Ayahuasca, Plant Dieta", "founded": "2005"},
    {"name": "Rongoā Māori Centre", "city": "Rotorua", "country": "New Zealand", "lat": -38.14, "lon": 176.25, "tradition": "Rongoā Māori", "specialty": "Native Plant Medicine", "founded": "1998"},
    {"name": "Aboriginal Bush Medicine (Alice Springs)", "city": "Alice Springs", "country": "Australia", "lat": -23.70, "lon": 133.88, "tradition": "Aboriginal Bush Medicine", "specialty": "Native Plant Remedies", "founded": "Traditional"},
    {"name": "Siddha Medicine Government Hospital", "city": "Chennai", "country": "India", "lat": 13.06, "lon": 80.25, "tradition": "Siddha Medicine", "specialty": "Metal-based, Herbal", "founded": "1963"},
    {"name": "Homeopathy Research Institute", "city": "London", "country": "UK", "lat": 51.52, "lon": -0.13, "tradition": "Homeopathy", "specialty": "Research, Clinical Trials", "founded": "2007"},
    {"name": "Naturopathic Medicine (Bastyr)", "city": "Kenmore", "country": "USA", "lat": 47.76, "lon": -122.24, "tradition": "Naturopathy", "specialty": "Natural Medicine Education", "founded": "1978"},
    {"name": "Heilpraktiker Schule Berlin", "city": "Berlin", "country": "Germany", "lat": 52.52, "lon": 13.39, "tradition": "Heilpraktik (Naturopathy)", "specialty": "Herbal, Hydrotherapy", "founded": "1960"},
    {"name": "Jamu Traditional Medicine Center", "city": "Yogyakarta", "country": "Indonesia", "lat": -7.80, "lon": 110.36, "tradition": "Jamu (Javanese Herbal)", "specialty": "Herbal Tonics, Massage", "founded": "Traditional"},
    {"name": "Hilot Filipino Healing Center", "city": "Manila", "country": "Philippines", "lat": 14.60, "lon": 120.98, "tradition": "Hilot (Filipino Massage)", "specialty": "Massage, Herbal", "founded": "Traditional"},
    {"name": "Ethiopian Traditional Medicine Center", "city": "Addis Ababa", "country": "Ethiopia", "lat": 9.02, "lon": 38.75, "tradition": "Ethiopian Herbal Medicine", "specialty": "Herbal, Bone-setting", "founded": "1979"},
]

# ──────────────────────────────────────────────────────────────────────
# 10. MENTAL HEALTH DATA - ~30 countries
# ──────────────────────────────────────────────────────────────────────
MENTAL_HEALTH_DATA = {
    "United States": {"lat": 39.8, "lon": -98.6, "depression_pct": 5.9, "anxiety_pct": 6.3, "psychiatrists_per_100k": 16.0, "suicide_rate": 14.5, "mh_spending_pct_gdp": 0.8},
    "United Kingdom": {"lat": 55.4, "lon": -3.4, "depression_pct": 4.5, "anxiety_pct": 4.7, "psychiatrists_per_100k": 14.0, "suicide_rate": 7.9, "mh_spending_pct_gdp": 0.9},
    "Germany": {"lat": 51.2, "lon": 10.4, "depression_pct": 5.2, "anxiety_pct": 5.8, "psychiatrists_per_100k": 27.0, "suicide_rate": 12.3, "mh_spending_pct_gdp": 1.0},
    "France": {"lat": 46.2, "lon": 2.2, "depression_pct": 4.8, "anxiety_pct": 5.0, "psychiatrists_per_100k": 23.0, "suicide_rate": 13.1, "mh_spending_pct_gdp": 0.8},
    "Japan": {"lat": 36.2, "lon": 138.3, "depression_pct": 4.2, "anxiety_pct": 3.1, "psychiatrists_per_100k": 12.0, "suicide_rate": 15.3, "mh_spending_pct_gdp": 0.5},
    "South Korea": {"lat": 35.9, "lon": 127.8, "depression_pct": 4.7, "anxiety_pct": 3.8, "psychiatrists_per_100k": 9.0, "suicide_rate": 24.1, "mh_spending_pct_gdp": 0.4},
    "Australia": {"lat": -25.3, "lon": 133.8, "depression_pct": 5.9, "anxiety_pct": 7.0, "psychiatrists_per_100k": 13.0, "suicide_rate": 12.1, "mh_spending_pct_gdp": 0.9},
    "Canada": {"lat": 56.1, "lon": -106.3, "depression_pct": 5.3, "anxiety_pct": 5.5, "psychiatrists_per_100k": 16.0, "suicide_rate": 11.8, "mh_spending_pct_gdp": 0.7},
    "Brazil": {"lat": -14.2, "lon": -51.9, "depression_pct": 5.8, "anxiety_pct": 9.3, "psychiatrists_per_100k": 3.2, "suicide_rate": 6.9, "mh_spending_pct_gdp": 0.3},
    "India": {"lat": 20.6, "lon": 78.9, "depression_pct": 4.5, "anxiety_pct": 3.0, "psychiatrists_per_100k": 0.3, "suicide_rate": 12.7, "mh_spending_pct_gdp": 0.05},
    "China": {"lat": 35.0, "lon": 105.0, "depression_pct": 4.2, "anxiety_pct": 3.4, "psychiatrists_per_100k": 2.2, "suicide_rate": 8.0, "mh_spending_pct_gdp": 0.2},
    "Russia": {"lat": 61.5, "lon": 105.3, "depression_pct": 5.5, "anxiety_pct": 4.8, "psychiatrists_per_100k": 11.0, "suicide_rate": 26.5, "mh_spending_pct_gdp": 0.4},
    "Mexico": {"lat": 23.6, "lon": -102.6, "depression_pct": 4.2, "anxiety_pct": 3.6, "psychiatrists_per_100k": 1.6, "suicide_rate": 5.3, "mh_spending_pct_gdp": 0.2},
    "Nigeria": {"lat": 9.1, "lon": 8.7, "depression_pct": 3.9, "anxiety_pct": 2.8, "psychiatrists_per_100k": 0.1, "suicide_rate": 9.5, "mh_spending_pct_gdp": 0.02},
    "South Africa": {"lat": -30.6, "lon": 22.9, "depression_pct": 4.6, "anxiety_pct": 4.0, "psychiatrists_per_100k": 0.3, "suicide_rate": 11.6, "mh_spending_pct_gdp": 0.1},
    "Sweden": {"lat": 60.1, "lon": 18.6, "depression_pct": 5.4, "anxiety_pct": 5.2, "psychiatrists_per_100k": 24.0, "suicide_rate": 13.8, "mh_spending_pct_gdp": 1.1},
    "Norway": {"lat": 60.5, "lon": 8.5, "depression_pct": 4.7, "anxiety_pct": 5.0, "psychiatrists_per_100k": 30.0, "suicide_rate": 12.2, "mh_spending_pct_gdp": 1.0},
    "Netherlands": {"lat": 52.1, "lon": 5.3, "depression_pct": 4.2, "anxiety_pct": 5.3, "psychiatrists_per_100k": 21.0, "suicide_rate": 11.6, "mh_spending_pct_gdp": 1.0},
    "Italy": {"lat": 41.9, "lon": 12.6, "depression_pct": 4.7, "anxiety_pct": 4.4, "psychiatrists_per_100k": 10.0, "suicide_rate": 6.7, "mh_spending_pct_gdp": 0.5},
    "Spain": {"lat": 40.5, "lon": -3.7, "depression_pct": 4.3, "anxiety_pct": 4.1, "psychiatrists_per_100k": 11.0, "suicide_rate": 8.3, "mh_spending_pct_gdp": 0.5},
    "Turkey": {"lat": 38.9, "lon": 35.2, "depression_pct": 4.4, "anxiety_pct": 3.5, "psychiatrists_per_100k": 2.3, "suicide_rate": 2.6, "mh_spending_pct_gdp": 0.2},
    "Egypt": {"lat": 26.8, "lon": 30.8, "depression_pct": 3.5, "anxiety_pct": 3.2, "psychiatrists_per_100k": 0.9, "suicide_rate": 3.4, "mh_spending_pct_gdp": 0.1},
    "Pakistan": {"lat": 30.4, "lon": 69.3, "depression_pct": 4.2, "anxiety_pct": 3.7, "psychiatrists_per_100k": 0.2, "suicide_rate": 7.5, "mh_spending_pct_gdp": 0.02},
    "Indonesia": {"lat": -0.8, "lon": 113.9, "depression_pct": 3.7, "anxiety_pct": 2.7, "psychiatrists_per_100k": 0.3, "suicide_rate": 3.7, "mh_spending_pct_gdp": 0.1},
    "Thailand": {"lat": 15.9, "lon": 100.9, "depression_pct": 3.6, "anxiety_pct": 2.9, "psychiatrists_per_100k": 0.8, "suicide_rate": 7.8, "mh_spending_pct_gdp": 0.2},
    "Poland": {"lat": 51.9, "lon": 19.1, "depression_pct": 4.3, "anxiety_pct": 4.0, "psychiatrists_per_100k": 9.0, "suicide_rate": 11.8, "mh_spending_pct_gdp": 0.4},
    "Argentina": {"lat": -38.4, "lon": -63.6, "depression_pct": 5.7, "anxiety_pct": 6.1, "psychiatrists_per_100k": 17.0, "suicide_rate": 9.1, "mh_spending_pct_gdp": 0.5},
    "Ukraine": {"lat": 48.4, "lon": 31.2, "depression_pct": 6.3, "anxiety_pct": 5.5, "psychiatrists_per_100k": 8.0, "suicide_rate": 18.5, "mh_spending_pct_gdp": 0.2},
    "Colombia": {"lat": 4.6, "lon": -74.3, "depression_pct": 4.7, "anxiety_pct": 3.9, "psychiatrists_per_100k": 2.1, "suicide_rate": 5.8, "mh_spending_pct_gdp": 0.2},
}


# ──────────────────────────────────────────────────────────────────────
# CHART HELPER
# ──────────────────────────────────────────────────────────────────────
def _dark_fig(figsize=(10, 5)):
    """Create a dark-themed matplotlib figure and axis."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


# ──────────────────────────────────────────────────────────────────────
# API FUNCTIONS
# ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _fetch_hospitals_overpass(lat: float, lon: float, radius_m: int = 10000) -> list:
    """Fetch hospitals from Overpass API around a point."""
    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      way["amenity"="hospital"](around:{radius_m},{lat},{lon});
      relation["amenity"="hospital"](around:{radius_m},{lat},{lon});
    );
    out center body;
    """
    data = query_overpass(query)
    if data is None or "_error" in data:
        return []
    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        clat = el.get("lat") or el.get("center", {}).get("lat")
        clon = el.get("lon") or el.get("center", {}).get("lon")
        if clat and clon:
            results.append({
                "name": tags.get("name", "Unknown Hospital"),
                "lat": clat,
                "lon": clon,
                "beds": tags.get("beds", "N/A"),
                "emergency": tags.get("emergency", "N/A"),
                "operator": tags.get("operator", "N/A"),
                "phone": tags.get("phone", "N/A"),
                "website": tags.get("website", ""),
            })
    return results


@st.cache_data(ttl=3600)
def _fetch_rest_countries() -> list:
    """Fetch country data from REST Countries API for life expectancy proxy."""
    try:
        resp = requests.get(
            "https://restcountries.com/v3.1/all",
            params={"fields": "name,latlng,population,region,subregion,flags"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────────────
# LIFE EXPECTANCY HARDCODED (since REST Countries doesn't provide it)
# ──────────────────────────────────────────────────────────────────────
LIFE_EXPECTANCY = {
    "Japan": 84.6, "Switzerland": 83.8, "Australia": 83.4, "Spain": 83.2,
    "Italy": 83.0, "Iceland": 82.9, "Israel": 82.8, "South Korea": 82.7,
    "Sweden": 82.7, "France": 82.5, "Norway": 82.4, "Canada": 82.3,
    "New Zealand": 82.1, "Ireland": 82.0, "Netherlands": 81.9,
    "Germany": 81.3, "United Kingdom": 81.2, "Finland": 81.1,
    "Austria": 81.5, "Belgium": 81.4, "Portugal": 81.3,
    "Denmark": 81.0, "Greece": 81.3, "Singapore": 83.6,
    "Costa Rica": 80.3, "Chile": 80.2, "Cuba": 79.0,
    "United States": 78.9, "Czech Republic": 79.4, "Poland": 78.5,
    "China": 77.3, "Turkey": 77.7, "Mexico": 75.1,
    "Brazil": 75.9, "Argentina": 76.5, "Colombia": 77.3,
    "Thailand": 77.2, "Vietnam": 75.4, "Malaysia": 76.2,
    "Iran": 76.7, "Saudi Arabia": 75.1, "Egypt": 72.0,
    "Indonesia": 71.7, "India": 70.4, "Bangladesh": 72.4,
    "Philippines": 71.2, "Pakistan": 67.3, "Myanmar": 67.1,
    "Russia": 73.2, "Ukraine": 73.5, "South Africa": 64.1,
    "Kenya": 66.7, "Ghana": 64.1, "Tanzania": 65.5,
    "Ethiopia": 66.6, "Nigeria": 54.7, "DR Congo": 60.7,
    "Madagascar": 67.0, "Mozambique": 60.9, "Afghanistan": 64.8,
    "Somalia": 57.4, "Chad": 54.2, "Central African Republic": 53.3,
    "Sierra Leone": 54.7, "Lesotho": 54.3,
}


# ══════════════════════════════════════════════════════════════════════
# RENDER FUNCTIONS (one per mode)
# ══════════════════════════════════════════════════════════════════════

def _render_world_hospitals():
    """Mode 1: World Hospitals via Overpass."""
    st.markdown("#### Search Hospitals Near a City")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox("City Preset", list(HOSPITAL_PRESETS.keys()), key="med_hosp_preset")
    with c2:
        radius_km = st.slider("Radius (km)", 1, 50, 10, key="med_hosp_radius")
    with c3:
        st.markdown("")
        search = st.button("Search Hospitals", type="primary", key="med_hosp_search")

    loc = HOSPITAL_PRESETS[preset]
    if search or st.session_state.get("med_hosp_last_preset") == preset:
        st.session_state["med_hosp_last_preset"] = preset
        with st.spinner("Querying Overpass API for hospitals..."):
            hospitals = _fetch_hospitals_overpass(loc["lat"], loc["lon"], radius_km * 1000)

        if not hospitals:
            st.warning("No hospitals found. Try a larger radius or different city.")
            return

        # Stats
        cols = st.columns(4)
        cols[0].metric("Hospitals Found", len(hospitals))
        with_beds = sum(1 for h in hospitals if h["beds"] != "N/A")
        cols[1].metric("With Bed Data", with_beds)
        with_er = sum(1 for h in hospitals if h["emergency"] == "yes")
        cols[2].metric("With Emergency", with_er)
        cols[3].metric("Search Radius", f"{radius_km} km")

        # Map
        m = folium.Map(location=[loc["lat"], loc["lon"]], zoom_start=12, tiles="CartoDB dark_matter")
        cluster = folium_plugins.MarkerCluster()
        for h in hospitals:
            popup_html = f"""
            <div style='min-width:200px;'>
            <b>{html.escape(h['name'])}</b><br>
            Beds: {html.escape(str(h['beds']))}<br>
            Emergency: {html.escape(str(h['emergency']))}<br>
            Operator: {html.escape(str(h['operator']))}<br>
            Phone: {html.escape(str(h['phone']))}
            </div>
            """
            folium.Marker(
                location=[h["lat"], h["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=html.escape(h["name"]),
                icon=folium.Icon(color="red", icon="plus-sign"),
            ).add_to(cluster)
        cluster.add_to(m)
        components.html(m._repr_html_(), height=550)

        # DataFrame
        df = pd.DataFrame(hospitals)
        st.dataframe(df, width="stretch")

        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, f"hospitals_{preset.lower().replace(' ', '_')}.csv", "text/csv", key="med_hosp_dl")


def _render_disease_outbreaks():
    """Mode 2: Disease Outbreak History."""
    st.markdown("#### Historical Disease Outbreaks")

    diseases = sorted(set(d["disease"] for d in DISEASE_OUTBREAKS))
    sel_disease = st.multiselect("Filter by Disease Type", diseases, default=[], key="med_outbreak_filter")

    filtered = [d for d in DISEASE_OUTBREAKS if not sel_disease or d["disease"] in sel_disease]

    # Stats
    cols = st.columns(4)
    cols[0].metric("Total Outbreaks", len(filtered))
    unique_diseases = len(set(d["disease"] for d in filtered))
    cols[1].metric("Unique Diseases", unique_diseases)
    unique_regions = len(set(d["region"] for d in filtered))
    cols[2].metric("Regions Affected", unique_regions)
    cols[3].metric("Time Span", "430 BC - 2023")

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for d in filtered:
        popup_html = f"""
        <div style='min-width:220px;'>
        <b>{html.escape(d['name'])}</b><br>
        Year: {html.escape(d['year'])}<br>
        Disease: {html.escape(d['disease'])}<br>
        Deaths: {html.escape(d['deaths'])}<br>
        Region: {html.escape(d['region'])}
        </div>
        """
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=10,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html.escape(d["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: outbreaks per disease type
    fig, ax = _dark_fig()
    disease_counts = {}
    for d in filtered:
        disease_counts[d["disease"]] = disease_counts.get(d["disease"], 0) + 1
    sorted_dc = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    if sorted_dc:
        names, counts = zip(*sorted_dc)
        bars = ax.barh(range(len(names)), counts, color="#ef4444", alpha=0.8)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=8, color="#e8ecf4")
        ax.set_xlabel("Number of Outbreaks", color="#8b97b0")
        ax.set_title("Outbreaks by Disease Type", color="#e8ecf4", fontsize=12)
    st.pyplot(fig)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "disease_outbreaks.csv", "text/csv", key="med_outbreak_dl")


def _render_life_expectancy():
    """Mode 3: Life Expectancy world map."""
    st.markdown("#### Global Life Expectancy")

    countries_api = _fetch_rest_countries()
    # Build country -> coords lookup
    coords_map = {}
    for c in countries_api:
        cname = c.get("name", {}).get("common", "")
        ll = c.get("latlng", [])
        if cname and len(ll) == 2:
            coords_map[cname] = {"lat": ll[0], "lon": ll[1]}

    # Merge with hardcoded life expectancy
    records = []
    for country, le in LIFE_EXPECTANCY.items():
        coord = coords_map.get(country)
        if coord:
            records.append({"country": country, "lat": coord["lat"], "lon": coord["lon"], "life_expectancy": le})
        else:
            # fallback coordinates from healthcare access or vaccination data
            for src in [HEALTHCARE_ACCESS, VACCINATION_DATA]:
                if country in src:
                    records.append({"country": country, "lat": src[country]["lat"], "lon": src[country]["lon"], "life_expectancy": le})
                    break

    if not records:
        st.warning("Could not load life expectancy data.")
        return

    # Stats
    le_vals = [r["life_expectancy"] for r in records]
    cols = st.columns(4)
    cols[0].metric("Countries", len(records))
    cols[1].metric("Highest", f"{max(le_vals):.1f} yrs")
    cols[2].metric("Lowest", f"{min(le_vals):.1f} yrs")
    cols[3].metric("Average", f"{sum(le_vals)/len(le_vals):.1f} yrs")

    # Map - choropleth with circles
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in records:
        le = r["life_expectancy"]
        # Color gradient: red (<60) -> yellow (70) -> green (>80)
        if le >= 80:
            color = "#22c55e"
        elif le >= 70:
            color = "#eab308"
        elif le >= 60:
            color = "#f97316"
        else:
            color = "#ef4444"
        popup_html = f"""
        <div style='min-width:160px;'>
        <b>{html.escape(r['country'])}</b><br>
        Life Expectancy: {le:.1f} years
        </div>
        """
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, (le - 50) / 3),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{html.escape(r['country'])}: {le:.1f} yrs",
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:50px;left:50px;z-index:1000;background:#111827;
    padding:10px;border-radius:8px;border:1px solid #2a3550;font-size:12px;color:#e8ecf4;">
    <b>Life Expectancy</b><br>
    <span style="color:#22c55e;">&#9679;</span> 80+ years<br>
    <span style="color:#eab308;">&#9679;</span> 70-79 years<br>
    <span style="color:#f97316;">&#9679;</span> 60-69 years<br>
    <span style="color:#ef4444;">&#9679;</span> &lt;60 years
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    components.html(m._repr_html_(), height=550)

    # Chart
    fig, ax = _dark_fig()
    sorted_records = sorted(records, key=lambda x: x["life_expectancy"], reverse=True)[:30]
    names = [r["country"] for r in sorted_records]
    vals = [r["life_expectancy"] for r in sorted_records]
    colors = ["#22c55e" if v >= 80 else "#eab308" if v >= 70 else "#f97316" if v >= 60 else "#ef4444" for v in vals]
    ax.barh(range(len(names)), vals, color=colors, alpha=0.8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8, color="#e8ecf4")
    ax.set_xlabel("Life Expectancy (years)", color="#8b97b0")
    ax.set_title("Top 30 Countries by Life Expectancy", color="#e8ecf4", fontsize=12)
    ax.invert_yaxis()
    st.pyplot(fig)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame(records).sort_values("life_expectancy", ascending=False)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "life_expectancy.csv", "text/csv", key="med_le_dl")


def _render_vaccination_coverage():
    """Mode 4: Vaccination Coverage."""
    st.markdown("#### Global Vaccination Coverage")

    vaccine_type = st.selectbox("Vaccine Type", ["DTP3", "Measles", "Polio"], key="med_vax_type")
    vax_key = {"DTP3": "dtp3", "Measles": "measles", "Polio": "polio"}[vaccine_type]

    records = []
    for country, d in VACCINATION_DATA.items():
        records.append({
            "country": country,
            "lat": d["lat"],
            "lon": d["lon"],
            "coverage": d[vax_key],
            "dtp3": d["dtp3"],
            "measles": d["measles"],
            "polio": d["polio"],
        })

    # Stats
    cov_vals = [r["coverage"] for r in records]
    cols = st.columns(4)
    cols[0].metric("Countries", len(records))
    cols[1].metric("Avg Coverage", f"{sum(cov_vals)/len(cov_vals):.1f}%")
    cols[2].metric("Highest", f"{max(cov_vals)}%")
    cols[3].metric("Lowest", f"{min(cov_vals)}%")

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in records:
        cov = r["coverage"]
        if cov >= 90:
            color = "#22c55e"
        elif cov >= 75:
            color = "#eab308"
        elif cov >= 60:
            color = "#f97316"
        else:
            color = "#ef4444"
        popup_html = f"""
        <div style='min-width:180px;'>
        <b>{html.escape(r['country'])}</b><br>
        {vaccine_type} Coverage: {cov}%<br>
        DTP3: {r['dtp3']}% | Measles: {r['measles']}% | Polio: {r['polio']}%
        </div>
        """
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, cov / 8),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{html.escape(r['country'])}: {cov}%",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart
    fig, ax = _dark_fig()
    sorted_records = sorted(records, key=lambda x: x["coverage"])
    names = [r["country"] for r in sorted_records]
    vals = [r["coverage"] for r in sorted_records]
    colors = ["#22c55e" if v >= 90 else "#eab308" if v >= 75 else "#f97316" if v >= 60 else "#ef4444" for v in vals]
    ax.barh(range(len(names)), vals, color=colors, alpha=0.8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7, color="#e8ecf4")
    ax.set_xlabel(f"{vaccine_type} Coverage (%)", color="#8b97b0")
    ax.set_title(f"{vaccine_type} Vaccination Coverage by Country", color="#e8ecf4", fontsize=12)
    ax.axvline(x=90, color="#22c55e", linestyle="--", alpha=0.5, label="WHO Target 90%")
    ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4")
    st.pyplot(fig)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame(records).sort_values("coverage", ascending=False)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, f"vaccination_{vax_key}.csv", "text/csv", key="med_vax_dl")


def _render_malaria_risk():
    """Mode 5: Malaria Risk Zones."""
    st.markdown("#### Global Malaria Risk Zones")

    risk_filter = st.multiselect(
        "Filter by Risk Level",
        ["Very High", "High", "Moderate", "Low-Moderate"],
        default=[],
        key="med_malaria_filter",
    )

    filtered = [z for z in MALARIA_RISK_ZONES if not risk_filter or z["risk"] in risk_filter]

    # Stats
    cols = st.columns(4)
    cols[0].metric("Risk Zones", len(filtered))
    very_high = sum(1 for z in filtered if z["risk"] == "Very High")
    cols[1].metric("Very High Risk", very_high)
    high = sum(1 for z in filtered if z["risk"] == "High")
    cols[2].metric("High Risk", high)
    species_set = set(z["species"] for z in filtered)
    cols[3].metric("Parasite Species", len(species_set))

    # Map
    m = folium.Map(location=[5, 20], zoom_start=3, tiles="CartoDB dark_matter")
    risk_colors = {"Very High": "#ef4444", "High": "#f97316", "Moderate": "#eab308", "Low-Moderate": "#22c55e"}
    for z in filtered:
        color = risk_colors.get(z["risk"], "#8b97b0")
        popup_html = f"""
        <div style='min-width:200px;'>
        <b>{html.escape(z['region'])}</b><br>
        Risk Level: {html.escape(z['risk'])}<br>
        Annual Cases: {html.escape(z['cases_annual'])}<br>
        Species: {html.escape(z['species'])}
        </div>
        """
        folium.Circle(
            location=[z["lat"], z["lon"]],
            radius=z["radius"],
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.25,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html.escape(z["region"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: by risk level
    fig, ax = _dark_fig(figsize=(8, 4))
    risk_counts = {}
    for z in filtered:
        risk_counts[z["risk"]] = risk_counts.get(z["risk"], 0) + 1
    labels = list(risk_counts.keys())
    values = list(risk_counts.values())
    bar_colors = [risk_colors.get(l, "#8b97b0") for l in labels]
    ax.bar(labels, values, color=bar_colors, alpha=0.8)
    ax.set_ylabel("Number of Zones", color="#8b97b0")
    ax.set_title("Malaria Risk Zones by Level", color="#e8ecf4", fontsize=12)
    st.pyplot(fig)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "malaria_risk_zones.csv", "text/csv", key="med_malaria_dl")


def _render_healthcare_access():
    """Mode 6: Healthcare Access Index."""
    st.markdown("#### Global Healthcare Access Index")

    tier_filter = st.multiselect(
        "Filter by System Type",
        sorted(set(d["tier"] for d in HEALTHCARE_ACCESS.values())),
        default=[],
        key="med_hca_filter",
    )

    records = []
    for country, d in HEALTHCARE_ACCESS.items():
        if tier_filter and d["tier"] not in tier_filter:
            continue
        records.append({"country": country, **d})

    if not records:
        st.warning("No data for selected filters.")
        return

    # Stats
    idx_vals = [r["index"] for r in records]
    cols = st.columns(4)
    cols[0].metric("Countries", len(records))
    cols[1].metric("Avg Index", f"{sum(idx_vals)/len(idx_vals):.1f}")
    cols[2].metric("Highest", f"{max(idx_vals)}")
    cols[3].metric("Lowest", f"{min(idx_vals)}")

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in records:
        idx = r["index"]
        if idx >= 85:
            color = "#22c55e"
        elif idx >= 65:
            color = "#06b6d4"
        elif idx >= 45:
            color = "#eab308"
        else:
            color = "#ef4444"
        popup_html = f"""
        <div style='min-width:200px;'>
        <b>{html.escape(r['country'])}</b><br>
        Access Index: {idx}/100<br>
        Doctors/10K: {r['doctors_per_10k']}<br>
        Beds/10K: {r['beds_per_10k']}<br>
        System: {html.escape(r['tier'])}
        </div>
        """
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, idx / 8),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{html.escape(r['country'])}: {idx}/100",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: scatter doctors vs beds
    fig, ax = _dark_fig()
    x = [r["doctors_per_10k"] for r in records]
    y = [r["beds_per_10k"] for r in records]
    sizes = [r["index"] * 2 for r in records]
    colors_scatter = [r["index"] for r in records]
    sc = ax.scatter(x, y, s=sizes, c=colors_scatter, cmap="RdYlGn", alpha=0.7, edgecolors="#2a3550", linewidths=0.5)
    for r in records:
        if r["index"] >= 85 or r["index"] <= 30:
            ax.annotate(r["country"], (r["doctors_per_10k"], r["beds_per_10k"]),
                        fontsize=7, color="#e8ecf4", ha="center", va="bottom")
    ax.set_xlabel("Doctors per 10,000", color="#8b97b0")
    ax.set_ylabel("Hospital Beds per 10,000", color="#8b97b0")
    ax.set_title("Healthcare Access: Doctors vs Beds (size = index)", color="#e8ecf4", fontsize=12)
    cbar = plt.colorbar(sc, ax=ax)
    cbar.ax.yaxis.set_tick_params(color="#8b97b0")
    cbar.ax.set_ylabel("Access Index", color="#8b97b0")
    for label in cbar.ax.get_yticklabels():
        label.set_color("#8b97b0")
    st.pyplot(fig)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame(records).sort_values("index", ascending=False)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "healthcare_access.csv", "text/csv", key="med_hca_dl")


def _render_medical_tourism():
    """Mode 7: Medical Tourism Top Destinations."""
    st.markdown("#### Medical Tourism Hotspots")

    country_filter = st.multiselect(
        "Filter by Country",
        sorted(set(d["country"] for d in MEDICAL_TOURISM)),
        default=[],
        key="med_tourism_filter",
    )

    filtered = [d for d in MEDICAL_TOURISM if not country_filter or d["country"] in country_filter]

    # Stats
    cols = st.columns(4)
    cols[0].metric("Destinations", len(filtered))
    countries = set(d["country"] for d in filtered)
    cols[1].metric("Countries", len(countries))
    specialties = set()
    for d in filtered:
        for s in d["specialty"].split(", "):
            specialties.add(s)
    cols[2].metric("Specialties", len(specialties))
    cols[3].metric("Avg Savings", "40-70%")

    # Map
    m = folium.Map(location=[20, 40], zoom_start=2, tiles="CartoDB dark_matter")
    for d in filtered:
        popup_html = f"""
        <div style='min-width:220px;'>
        <b>{html.escape(d['city'])}, {html.escape(d['country'])}</b><br>
        Hospital: {html.escape(d['hospital'])}<br>
        Specialty: {html.escape(d['specialty'])}<br>
        Patients/Year: {html.escape(d['patients_yr'])}<br>
        Savings: {html.escape(d['savings'])}
        </div>
        """
        folium.Marker(
            location=[d["lat"], d["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{html.escape(d['city'])} - {html.escape(d['specialty'])}",
            icon=folium.Icon(color="green", icon="heart", prefix="fa"),
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: patients by city
    fig, ax = _dark_fig()
    sorted_data = sorted(filtered, key=lambda x: x["patients_yr"], reverse=True)[:20]
    labels = [f"{d['city']}" for d in sorted_data]
    # Parse patient numbers for chart
    def parse_patients(val):
        val = val.replace(",", "").replace("+", "").strip()
        if "M" in val:
            return float(val.replace("M", "")) * 1_000_000
        if "K" in val:
            return float(val.replace("K", "")) * 1_000
        try:
            return float(val)
        except ValueError:
            return 0
    vals = [parse_patients(d["patients_yr"]) for d in sorted_data]
    ax.barh(range(len(labels)), [v / 1_000_000 for v in vals], color="#06b6d4", alpha=0.8)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8, color="#e8ecf4")
    ax.set_xlabel("Medical Tourists per Year (millions)", color="#8b97b0")
    ax.set_title("Top Medical Tourism Destinations", color="#e8ecf4", fontsize=12)
    ax.invert_yaxis()
    st.pyplot(fig)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "medical_tourism.csv", "text/csv", key="med_tourism_dl")


def _render_pharma_hqs():
    """Mode 8: Pharmaceutical Company Headquarters."""
    st.markdown("#### Global Pharmaceutical Company Headquarters")

    country_filter = st.multiselect(
        "Filter by Country",
        sorted(set(d["country"] for d in PHARMA_HQS)),
        default=[],
        key="med_pharma_filter",
    )

    filtered = [d for d in PHARMA_HQS if not country_filter or d["country"] in country_filter]

    # Stats
    total_rev = sum(d["revenue_b"] for d in filtered)
    cols = st.columns(4)
    cols[0].metric("Companies", len(filtered))
    cols[1].metric("Countries", len(set(d["country"] for d in filtered)))
    cols[2].metric("Total Revenue", f"${total_rev:.0f}B")
    cols[3].metric("Avg Revenue", f"${total_rev/len(filtered):.1f}B" if filtered else "$0B")

    # Map
    m = folium.Map(location=[30, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for d in filtered:
        rev = d["revenue_b"]
        if rev >= 40:
            color = "red"
        elif rev >= 20:
            color = "orange"
        elif rev >= 10:
            color = "blue"
        else:
            color = "green"
        popup_html = f"""
        <div style='min-width:200px;'>
        <b>{html.escape(d['company'])}</b><br>
        HQ: {html.escape(d['city'])}, {html.escape(d['country'])}<br>
        Revenue: ${d['revenue_b']}B<br>
        Specialty: {html.escape(d['specialty'])}
        </div>
        """
        folium.Marker(
            location=[d["lat"], d["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{html.escape(d['company'])} (${d['revenue_b']}B)",
            icon=folium.Icon(color=color, icon="medkit", prefix="fa"),
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: top by revenue
    fig, ax = _dark_fig()
    sorted_data = sorted(filtered, key=lambda x: x["revenue_b"], reverse=True)[:25]
    names = [d["company"] for d in sorted_data]
    revs = [d["revenue_b"] for d in sorted_data]
    bar_colors = ["#ef4444" if r >= 40 else "#f97316" if r >= 20 else "#3b82f6" if r >= 10 else "#22c55e" for r in revs]
    ax.barh(range(len(names)), revs, color=bar_colors, alpha=0.8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8, color="#e8ecf4")
    ax.set_xlabel("Revenue (Billion USD)", color="#8b97b0")
    ax.set_title("Top Pharmaceutical Companies by Revenue", color="#e8ecf4", fontsize=12)
    ax.invert_yaxis()
    st.pyplot(fig)
    plt.close(fig)

    # By country chart
    fig2, ax2 = _dark_fig(figsize=(8, 4))
    country_rev = {}
    for d in filtered:
        country_rev[d["country"]] = country_rev.get(d["country"], 0) + d["revenue_b"]
    sorted_cr = sorted(country_rev.items(), key=lambda x: x[1], reverse=True)
    cr_names, cr_vals = zip(*sorted_cr) if sorted_cr else ([], [])
    ax2.bar(cr_names, cr_vals, color="#8b5cf6", alpha=0.8)
    ax2.set_ylabel("Total Revenue ($B)", color="#8b97b0")
    ax2.set_title("Pharma Revenue by Country", color="#e8ecf4", fontsize=12)
    ax2.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # DataFrame
    df = pd.DataFrame(filtered).sort_values("revenue_b", ascending=False)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "pharma_hqs.csv", "text/csv", key="med_pharma_dl")


def _render_traditional_medicine():
    """Mode 9: Traditional Medicine Centers."""
    st.markdown("#### Traditional Medicine Centers Worldwide")

    tradition_filter = st.multiselect(
        "Filter by Tradition",
        sorted(set(d["tradition"] for d in TRADITIONAL_MEDICINE)),
        default=[],
        key="med_trad_filter",
    )

    filtered = [d for d in TRADITIONAL_MEDICINE if not tradition_filter or d["tradition"] in tradition_filter]

    # Stats
    cols = st.columns(4)
    cols[0].metric("Centers", len(filtered))
    cols[1].metric("Traditions", len(set(d["tradition"] for d in filtered)))
    cols[2].metric("Countries", len(set(d["country"] for d in filtered)))
    specialties = set()
    for d in filtered:
        for s in d["specialty"].split(", "):
            specialties.add(s.strip())
    cols[3].metric("Specialties", len(specialties))

    # Color per tradition
    traditions = sorted(set(d["tradition"] for d in filtered))
    trad_colors = {}
    palette = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#3b82f6",
               "#8b5cf6", "#ec4899", "#14b8a6", "#f43f5e", "#a855f7", "#64748b"]
    for i, t in enumerate(traditions):
        trad_colors[t] = palette[i % len(palette)]

    # Map
    m = folium.Map(location=[20, 40], zoom_start=2, tiles="CartoDB dark_matter")
    for d in filtered:
        color_hex = trad_colors.get(d["tradition"], "#06b6d4")
        popup_html = f"""
        <div style='min-width:220px;'>
        <b>{html.escape(d['name'])}</b><br>
        City: {html.escape(d['city'])}, {html.escape(d['country'])}<br>
        Tradition: {html.escape(d['tradition'])}<br>
        Specialty: {html.escape(d['specialty'])}<br>
        Founded: {html.escape(d['founded'])}
        </div>
        """
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=9,
            color=color_hex,
            fill=True,
            fill_color=color_hex,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html.escape(d["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: centers per tradition
    fig, ax = _dark_fig()
    trad_counts = {}
    for d in filtered:
        trad_counts[d["tradition"]] = trad_counts.get(d["tradition"], 0) + 1
    sorted_tc = sorted(trad_counts.items(), key=lambda x: x[1], reverse=True)
    if sorted_tc:
        t_names, t_counts = zip(*sorted_tc)
        bar_cols = [trad_colors.get(n, "#06b6d4") for n in t_names]
        ax.barh(range(len(t_names)), t_counts, color=bar_cols, alpha=0.8)
        ax.set_yticks(range(len(t_names)))
        ax.set_yticklabels(t_names, fontsize=8, color="#e8ecf4")
        ax.set_xlabel("Number of Centers", color="#8b97b0")
        ax.set_title("Traditional Medicine Centers by Tradition", color="#e8ecf4", fontsize=12)
    st.pyplot(fig)
    plt.close(fig)

    # DataFrame
    df = pd.DataFrame(filtered)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "traditional_medicine.csv", "text/csv", key="med_trad_dl")


def _render_mental_health():
    """Mode 10: Mental Health Global Map."""
    st.markdown("#### Global Mental Health Overview")

    metric_choice = st.selectbox(
        "Color by Metric",
        ["Depression Rate (%)", "Anxiety Rate (%)", "Psychiatrists per 100K", "Suicide Rate (per 100K)", "MH Spending (% GDP)"],
        key="med_mh_metric",
    )
    metric_key = {
        "Depression Rate (%)": "depression_pct",
        "Anxiety Rate (%)": "anxiety_pct",
        "Psychiatrists per 100K": "psychiatrists_per_100k",
        "Suicide Rate (per 100K)": "suicide_rate",
        "MH Spending (% GDP)": "mh_spending_pct_gdp",
    }[metric_choice]

    records = []
    for country, d in MENTAL_HEALTH_DATA.items():
        records.append({"country": country, **d})

    # Stats
    vals = [r[metric_key] for r in records]
    cols = st.columns(4)
    cols[0].metric("Countries", len(records))
    cols[1].metric("Average", f"{sum(vals)/len(vals):.2f}")
    cols[2].metric("Highest", f"{max(vals):.2f}")
    cols[3].metric("Lowest", f"{min(vals):.2f}")

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    min_val, max_val = min(vals), max(vals)
    val_range = max_val - min_val if max_val != min_val else 1.0
    for r in records:
        v = r[metric_key]
        # Normalize 0-1
        norm = (v - min_val) / val_range
        # For psychiatrists and spending, higher is better (green). For depression/anxiety/suicide, higher is worse (red).
        if metric_key in ("psychiatrists_per_100k", "mh_spending_pct_gdp"):
            if norm >= 0.66:
                color = "#22c55e"
            elif norm >= 0.33:
                color = "#eab308"
            else:
                color = "#ef4444"
        else:
            if norm >= 0.66:
                color = "#ef4444"
            elif norm >= 0.33:
                color = "#eab308"
            else:
                color = "#22c55e"

        popup_html = f"""
        <div style='min-width:220px;'>
        <b>{html.escape(r['country'])}</b><br>
        Depression: {r['depression_pct']}%<br>
        Anxiety: {r['anxiety_pct']}%<br>
        Psychiatrists/100K: {r['psychiatrists_per_100k']}<br>
        Suicide Rate: {r['suicide_rate']}/100K<br>
        MH Spending: {r['mh_spending_pct_gdp']}% GDP
        </div>
        """
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=max(5, v * 1.5) if metric_key not in ("mh_spending_pct_gdp",) else max(5, v * 15),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{html.escape(r['country'])}: {v}",
        ).add_to(m)
    components.html(m._repr_html_(), height=550)

    # Chart: bar chart sorted
    fig, ax = _dark_fig()
    sorted_records = sorted(records, key=lambda x: x[metric_key], reverse=True)
    names = [r["country"] for r in sorted_records]
    chart_vals = [r[metric_key] for r in sorted_records]
    # Color bars
    bar_colors = []
    for v in chart_vals:
        norm = (v - min_val) / val_range
        if metric_key in ("psychiatrists_per_100k", "mh_spending_pct_gdp"):
            bar_colors.append("#22c55e" if norm >= 0.66 else "#eab308" if norm >= 0.33 else "#ef4444")
        else:
            bar_colors.append("#ef4444" if norm >= 0.66 else "#eab308" if norm >= 0.33 else "#22c55e")
    ax.barh(range(len(names)), chart_vals, color=bar_colors, alpha=0.8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7, color="#e8ecf4")
    ax.set_xlabel(metric_choice, color="#8b97b0")
    ax.set_title(f"Mental Health: {metric_choice}", color="#e8ecf4", fontsize=12)
    ax.invert_yaxis()
    st.pyplot(fig)
    plt.close(fig)

    # Correlation: depression vs psychiatrists
    fig2, ax2 = _dark_fig(figsize=(8, 5))
    x = [r["psychiatrists_per_100k"] for r in records]
    y = [r["suicide_rate"] for r in records]
    ax2.scatter(x, y, s=80, c="#ec4899", alpha=0.7, edgecolors="#2a3550")
    for r in records:
        if r["suicide_rate"] > 20 or r["psychiatrists_per_100k"] > 25:
            ax2.annotate(r["country"], (r["psychiatrists_per_100k"], r["suicide_rate"]),
                         fontsize=7, color="#e8ecf4", ha="center", va="bottom")
    ax2.set_xlabel("Psychiatrists per 100K", color="#8b97b0")
    ax2.set_ylabel("Suicide Rate per 100K", color="#8b97b0")
    ax2.set_title("Psychiatrists vs Suicide Rate", color="#e8ecf4", fontsize=12)
    st.pyplot(fig2)
    plt.close(fig2)

    # DataFrame
    df = pd.DataFrame(records).sort_values(metric_key, ascending=False)
    st.dataframe(df, width="stretch")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "mental_health.csv", "text/csv", key="med_mh_dl")


# ══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════
def render_medical_maps_tab():
    """Main entry point for the Medical & Health Maps tab."""
    st.markdown(
        '<div class="tab-header pink"><h4>Medical & Health Maps</h4>'
        "<p>Explore global healthcare infrastructure, disease history, vaccination coverage, "
        "and mental health data across 10 interactive map modes.</p></div>",
        unsafe_allow_html=True,
    )

    MAP_MODES = {
        "World Hospitals": _render_world_hospitals,
        "Disease Outbreak History": _render_disease_outbreaks,
        "Life Expectancy": _render_life_expectancy,
        "Vaccination Coverage": _render_vaccination_coverage,
        "Malaria Risk Zones": _render_malaria_risk,
        "Healthcare Access": _render_healthcare_access,
        "Medical Tourism": _render_medical_tourism,
        "Pharmaceutical HQs": _render_pharma_hqs,
        "Traditional Medicine": _render_traditional_medicine,
        "Mental Health": _render_mental_health,
    }

    mode = st.selectbox("Select Map Mode", list(MAP_MODES.keys()), key="med_map_mode")

    st.markdown("---")

    MAP_MODES[mode]()
