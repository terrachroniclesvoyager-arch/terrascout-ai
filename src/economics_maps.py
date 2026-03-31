# -*- coding: utf-8 -*-
"""
Economics & Trade Maps module for TerraScout AI.
Provides 10 interactive map types covering global economic data:
  1. GDP Per Capita        - REST Countries + hardcoded GDP data
  2. Trade Blocs           - Hardcoded membership polygons
  3. Stock Exchanges       - 40+ major exchanges as graduated circles
  4. Cryptocurrency Adopt. - Country-level adoption markers
  5. Tax Havens            - 25 jurisdictions with corporate tax rates
  6. Sovereign Wealth Funds- 25 SWFs as graduated circles by AUM
  7. Container Ports       - Top 40 ports by TEU throughput
  8. Oil & Gas Fields      - 30+ major fields with reserves data
  9. Economic Corridors    - Belt and Road + others as polylines
  10. Currency Zones       - World currencies grouped by zone
All data from free APIs or hardcoded reference datasets. No API keys required.
"""

import io
import logging
import streamlit as st
import requests
import pandas as pd
import numpy as np
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from html import escape

matplotlib.use("Agg")
logger = logging.getLogger(__name__)

# ===================================================================
# REST COUNTRIES API
# ===================================================================
REST_COUNTRIES_URL = (
    "https://restcountries.com/v3.1/all"
    "?fields=name,latlng,population,gini,cca2,region,currencies"
)

# ===================================================================
# 1. GDP PER CAPITA  (~80 countries, 2023 estimates, USD)
# ===================================================================
GDP_PER_CAPITA = {
    "US": 80035, "CH": 99995, "NO": 82830, "IE": 100170, "IS": 73467,
    "LU": 126430, "SG": 72794, "DK": 67803, "AU": 64491, "NL": 57768,
    "SE": 55873, "FI": 53655, "AT": 56802, "CA": 52722, "DE": 52824,
    "BE": 51247, "IL": 52170, "NZ": 48802, "GB": 46125, "FR": 44408,
    "JP": 33950, "KR": 33393, "IT": 37146, "ES": 30996, "CZ": 27220,
    "PT": 26440, "GR": 22440, "PL": 18320, "HU": 18390, "RO": 15790,
    "BG": 13980, "HR": 19290, "SK": 21390, "LT": 24030, "LV": 21630,
    "EE": 28250, "SI": 31260, "CN": 12720, "IN": 2612, "BR": 10412,
    "RU": 13006, "ZA": 6190, "MX": 10820, "TR": 10674, "SA": 29922,
    "AE": 49450, "QA": 83890, "KW": 38124, "BH": 29103, "OM": 21830,
    "EG": 3699, "NG": 2184, "KE": 2099, "ET": 1027, "GH": 2363,
    "TZ": 1200, "TH": 7233, "VN": 4164, "PH": 3905, "MY": 12570,
    "ID": 4788, "PK": 1505, "BD": 2688, "LK": 3474, "MM": 1095,
    "KH": 1785, "LA": 2054, "AR": 10636, "CL": 16800, "CO": 6630,
    "PE": 7126, "UY": 21577, "EC": 6380, "VE": 3740, "BO": 3600,
    "PY": 5890, "PA": 17350, "CR": 13090, "CU": 8920, "DO": 10120,
    "GT": 5580, "HN": 2870, "NI": 2150, "SV": 5120, "TN": 3810,
    "MA": 3700, "DZ": 4474, "IQ": 5540, "JO": 4660, "LB": 4020,
}

# ===================================================================
# 2. TRADE BLOCS
# ===================================================================
TRADE_BLOCS = {
    "European Union (EU)": {
        "color": "#2563eb",
        "members": [
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
            "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE",
        ],
    },
    "USMCA / NAFTA": {
        "color": "#dc2626",
        "members": ["US", "CA", "MX"],
    },
    "ASEAN": {
        "color": "#16a34a",
        "members": ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "VN"],
    },
    "Mercosur": {
        "color": "#ca8a04",
        "members": ["AR", "BR", "PY", "UY", "VE"],
    },
    "African Union (AU)": {
        "color": "#9333ea",
        "members": [
            "DZ", "AO", "BJ", "BW", "BF", "BI", "CV", "CM", "CF", "TD",
            "KM", "CG", "CD", "CI", "DJ", "EG", "GQ", "ER", "SZ", "ET",
            "GA", "GM", "GH", "GN", "GW", "KE", "LS", "LR", "LY", "MG",
            "MW", "ML", "MR", "MU", "MA", "MZ", "NA", "NE", "NG", "RW",
            "ST", "SN", "SC", "SL", "SO", "ZA", "SS", "SD", "TZ", "TG",
            "TN", "UG", "ZM", "ZW",
        ],
    },
    "BRICS": {
        "color": "#ea580c",
        "members": ["BR", "RU", "IN", "CN", "ZA"],
    },
    "OPEC": {
        "color": "#1a1a2e",
        "members": [
            "DZ", "AO", "CG", "GQ", "GA", "IR", "IQ", "KW", "LY",
            "NG", "SA", "AE", "VE",
        ],
    },
    "RCEP": {
        "color": "#0891b2",
        "members": [
            "AU", "BN", "KH", "CN", "ID", "JP", "KR", "LA", "MY",
            "MM", "NZ", "PH", "SG", "TH", "VN",
        ],
    },
    "CPTPP": {
        "color": "#e11d48",
        "members": [
            "AU", "BN", "CA", "CL", "JP", "MY", "MX", "NZ", "PE",
            "SG", "VN",
        ],
    },
}

# ===================================================================
# 3. STOCK EXCHANGES  (40+ global exchanges)
# ===================================================================
STOCK_EXCHANGES = [
    {"name": "New York Stock Exchange (NYSE)", "city": "New York", "lat": 40.7069, "lng": -74.0113, "market_cap_T": 27.69, "founded": 1792, "country": "US"},
    {"name": "NASDAQ", "city": "New York", "lat": 40.7570, "lng": -73.9897, "market_cap_T": 24.56, "founded": 1971, "country": "US"},
    {"name": "Shanghai Stock Exchange (SSE)", "city": "Shanghai", "lat": 31.2320, "lng": 121.4740, "market_cap_T": 6.93, "founded": 1990, "country": "CN"},
    {"name": "Euronext", "city": "Amsterdam", "lat": 52.3702, "lng": 4.8952, "market_cap_T": 7.33, "founded": 2000, "country": "NL"},
    {"name": "Japan Exchange Group (JPX)", "city": "Tokyo", "lat": 35.6812, "lng": 139.7671, "market_cap_T": 6.54, "founded": 1878, "country": "JP"},
    {"name": "Shenzhen Stock Exchange (SZSE)", "city": "Shenzhen", "lat": 22.5431, "lng": 114.0579, "market_cap_T": 4.67, "founded": 1990, "country": "CN"},
    {"name": "Hong Kong Exchange (HKEX)", "city": "Hong Kong", "lat": 22.2855, "lng": 114.1577, "market_cap_T": 4.57, "founded": 1891, "country": "HK"},
    {"name": "London Stock Exchange (LSE)", "city": "London", "lat": 51.5155, "lng": -0.0922, "market_cap_T": 3.42, "founded": 1801, "country": "GB"},
    {"name": "National Stock Exchange (NSE)", "city": "Mumbai", "lat": 19.0544, "lng": 72.8556, "market_cap_T": 3.93, "founded": 1992, "country": "IN"},
    {"name": "BSE (Bombay Stock Exchange)", "city": "Mumbai", "lat": 18.9281, "lng": 72.8333, "market_cap_T": 3.84, "founded": 1875, "country": "IN"},
    {"name": "Toronto Stock Exchange (TSX)", "city": "Toronto", "lat": 43.6489, "lng": -79.3818, "market_cap_T": 3.26, "founded": 1852, "country": "CA"},
    {"name": "Saudi Exchange (Tadawul)", "city": "Riyadh", "lat": 24.7136, "lng": 46.6753, "market_cap_T": 2.89, "founded": 2007, "country": "SA"},
    {"name": "Deutsche Boerse (Xetra)", "city": "Frankfurt", "lat": 50.1109, "lng": 8.6821, "market_cap_T": 2.34, "founded": 1585, "country": "DE"},
    {"name": "SIX Swiss Exchange", "city": "Zurich", "lat": 47.3769, "lng": 8.5417, "market_cap_T": 1.94, "founded": 1850, "country": "CH"},
    {"name": "Korea Exchange (KRX)", "city": "Seoul", "lat": 37.5665, "lng": 126.9780, "market_cap_T": 1.99, "founded": 2005, "country": "KR"},
    {"name": "Nasdaq Nordic (OMX)", "city": "Stockholm", "lat": 59.3293, "lng": 18.0686, "market_cap_T": 1.85, "founded": 1863, "country": "SE"},
    {"name": "Australian Securities Exchange (ASX)", "city": "Sydney", "lat": -33.8688, "lng": 151.2093, "market_cap_T": 1.72, "founded": 1861, "country": "AU"},
    {"name": "Taiwan Stock Exchange (TWSE)", "city": "Taipei", "lat": 25.0330, "lng": 121.5654, "market_cap_T": 1.84, "founded": 1961, "country": "TW"},
    {"name": "Johannesburg Stock Exchange (JSE)", "city": "Johannesburg", "lat": -26.2041, "lng": 28.0473, "market_cap_T": 1.06, "founded": 1887, "country": "ZA"},
    {"name": "B3 (Brasil Bolsa Balcao)", "city": "Sao Paulo", "lat": -23.5505, "lng": -46.6333, "market_cap_T": 0.97, "founded": 1890, "country": "BR"},
    {"name": "BME Spanish Exchanges", "city": "Madrid", "lat": 40.4168, "lng": -3.7038, "market_cap_T": 0.80, "founded": 1831, "country": "ES"},
    {"name": "Singapore Exchange (SGX)", "city": "Singapore", "lat": 1.2812, "lng": 103.8510, "market_cap_T": 0.66, "founded": 1999, "country": "SG"},
    {"name": "Borsa Istanbul", "city": "Istanbul", "lat": 41.0082, "lng": 28.9784, "market_cap_T": 0.40, "founded": 1866, "country": "TR"},
    {"name": "Mexican Stock Exchange (BMV)", "city": "Mexico City", "lat": 19.4326, "lng": -99.1332, "market_cap_T": 0.42, "founded": 1933, "country": "MX"},
    {"name": "Warsaw Stock Exchange (GPW)", "city": "Warsaw", "lat": 52.2297, "lng": 21.0122, "market_cap_T": 0.25, "founded": 1817, "country": "PL"},
    {"name": "Bursa Malaysia", "city": "Kuala Lumpur", "lat": 3.1530, "lng": 101.7032, "market_cap_T": 0.39, "founded": 1930, "country": "MY"},
    {"name": "Tel Aviv Stock Exchange (TASE)", "city": "Tel Aviv", "lat": 32.0853, "lng": 34.7818, "market_cap_T": 0.33, "founded": 1953, "country": "IL"},
    {"name": "Stock Exchange of Thailand (SET)", "city": "Bangkok", "lat": 13.7563, "lng": 100.5018, "market_cap_T": 0.49, "founded": 1975, "country": "TH"},
    {"name": "Indonesia Stock Exchange (IDX)", "city": "Jakarta", "lat": -6.2088, "lng": 106.8456, "market_cap_T": 0.58, "founded": 1912, "country": "ID"},
    {"name": "Qatar Stock Exchange (QSE)", "city": "Doha", "lat": 25.2854, "lng": 51.5310, "market_cap_T": 0.17, "founded": 1995, "country": "QA"},
    {"name": "Abu Dhabi Securities Exchange (ADX)", "city": "Abu Dhabi", "lat": 24.4539, "lng": 54.3773, "market_cap_T": 0.78, "founded": 2000, "country": "AE"},
    {"name": "Dubai Financial Market (DFM)", "city": "Dubai", "lat": 25.2048, "lng": 55.2708, "market_cap_T": 0.17, "founded": 2000, "country": "AE"},
    {"name": "Egyptian Exchange (EGX)", "city": "Cairo", "lat": 30.0444, "lng": 31.2357, "market_cap_T": 0.04, "founded": 1883, "country": "EG"},
    {"name": "Philippine Stock Exchange (PSE)", "city": "Manila", "lat": 14.5995, "lng": 120.9842, "market_cap_T": 0.24, "founded": 1927, "country": "PH"},
    {"name": "Ho Chi Minh Stock Exchange (HOSE)", "city": "Ho Chi Minh City", "lat": 10.7769, "lng": 106.7009, "market_cap_T": 0.19, "founded": 2000, "country": "VN"},
    {"name": "Nairobi Securities Exchange (NSE)", "city": "Nairobi", "lat": -1.2921, "lng": 36.8219, "market_cap_T": 0.02, "founded": 1954, "country": "KE"},
    {"name": "Nigeria Exchange (NGX)", "city": "Lagos", "lat": 6.5244, "lng": 3.3792, "market_cap_T": 0.06, "founded": 1961, "country": "NG"},
    {"name": "Colombo Stock Exchange (CSE)", "city": "Colombo", "lat": 6.9271, "lng": 79.8612, "market_cap_T": 0.02, "founded": 1985, "country": "LK"},
    {"name": "Santiago Stock Exchange (BCS)", "city": "Santiago", "lat": -33.4489, "lng": -70.6693, "market_cap_T": 0.19, "founded": 1893, "country": "CL"},
    {"name": "Bolsa de Valores de Colombia (BVC)", "city": "Bogota", "lat": 4.7110, "lng": -74.0721, "market_cap_T": 0.11, "founded": 1929, "country": "CO"},
    {"name": "Lima Stock Exchange (BVL)", "city": "Lima", "lat": -12.0464, "lng": -77.0428, "market_cap_T": 0.09, "founded": 1860, "country": "PE"},
    {"name": "New Zealand Exchange (NZX)", "city": "Wellington", "lat": -41.2865, "lng": 174.7762, "market_cap_T": 0.08, "founded": 1974, "country": "NZ"},
    {"name": "Casablanca Stock Exchange (CSE)", "city": "Casablanca", "lat": 33.5731, "lng": -7.5898, "market_cap_T": 0.06, "founded": 1929, "country": "MA"},
]

# ===================================================================
# 4. CRYPTOCURRENCY ADOPTION  (country-level)
# ===================================================================
CRYPTO_ADOPTION = [
    {"country": "El Salvador", "cca2": "SV", "lat": 13.69, "lng": -89.22, "adoption_pct": 46.0, "legal_status": "Legal Tender (Bitcoin)", "rank": 1},
    {"country": "Nigeria", "cca2": "NG", "lat": 9.08, "lng": 7.49, "adoption_pct": 35.0, "legal_status": "Restricted", "rank": 2},
    {"country": "Vietnam", "cca2": "VN", "lat": 14.06, "lng": 108.28, "adoption_pct": 26.0, "legal_status": "Unregulated", "rank": 3},
    {"country": "Philippines", "cca2": "PH", "lat": 12.88, "lng": 121.77, "adoption_pct": 20.0, "legal_status": "Regulated", "rank": 4},
    {"country": "Ukraine", "cca2": "UA", "lat": 48.38, "lng": 31.17, "adoption_pct": 18.0, "legal_status": "Legal", "rank": 5},
    {"country": "India", "cca2": "IN", "lat": 20.59, "lng": 78.96, "adoption_pct": 15.0, "legal_status": "Taxed / Regulated", "rank": 6},
    {"country": "United States", "cca2": "US", "lat": 37.09, "lng": -95.71, "adoption_pct": 14.0, "legal_status": "Regulated", "rank": 7},
    {"country": "Pakistan", "cca2": "PK", "lat": 30.38, "lng": 69.35, "adoption_pct": 13.0, "legal_status": "Restricted", "rank": 8},
    {"country": "Brazil", "cca2": "BR", "lat": -14.24, "lng": -51.93, "adoption_pct": 12.0, "legal_status": "Regulated", "rank": 9},
    {"country": "Thailand", "cca2": "TH", "lat": 15.87, "lng": 100.99, "adoption_pct": 12.0, "legal_status": "Regulated", "rank": 10},
    {"country": "Turkey", "cca2": "TR", "lat": 38.96, "lng": 35.24, "adoption_pct": 11.0, "legal_status": "Restricted Payments", "rank": 11},
    {"country": "Russia", "cca2": "RU", "lat": 61.52, "lng": 105.32, "adoption_pct": 11.0, "legal_status": "Legal (not as payment)", "rank": 12},
    {"country": "Argentina", "cca2": "AR", "lat": -38.42, "lng": -63.62, "adoption_pct": 10.0, "legal_status": "Regulated", "rank": 13},
    {"country": "Indonesia", "cca2": "ID", "lat": -0.79, "lng": 113.92, "adoption_pct": 10.0, "legal_status": "Regulated commodity", "rank": 14},
    {"country": "Kenya", "cca2": "KE", "lat": -0.02, "lng": 37.91, "adoption_pct": 9.0, "legal_status": "Unregulated", "rank": 15},
    {"country": "South Africa", "cca2": "ZA", "lat": -30.56, "lng": 22.94, "adoption_pct": 8.5, "legal_status": "Regulated", "rank": 16},
    {"country": "Colombia", "cca2": "CO", "lat": 4.57, "lng": -74.30, "adoption_pct": 8.0, "legal_status": "Legal", "rank": 17},
    {"country": "United Kingdom", "cca2": "GB", "lat": 55.38, "lng": -3.44, "adoption_pct": 7.0, "legal_status": "Regulated", "rank": 18},
    {"country": "Germany", "cca2": "DE", "lat": 51.17, "lng": 10.45, "adoption_pct": 6.0, "legal_status": "Regulated", "rank": 19},
    {"country": "Japan", "cca2": "JP", "lat": 36.20, "lng": 138.25, "adoption_pct": 5.0, "legal_status": "Legal Property", "rank": 20},
    {"country": "Central African Republic", "cca2": "CF", "lat": 6.61, "lng": 20.94, "adoption_pct": 4.0, "legal_status": "Legal Tender (Bitcoin)", "rank": 21},
    {"country": "Venezuela", "cca2": "VE", "lat": 6.42, "lng": -66.59, "adoption_pct": 9.0, "legal_status": "Legal (Petro)", "rank": 22},
    {"country": "Mexico", "cca2": "MX", "lat": 23.63, "lng": -102.55, "adoption_pct": 7.5, "legal_status": "Regulated", "rank": 23},
    {"country": "Singapore", "cca2": "SG", "lat": 1.35, "lng": 103.82, "adoption_pct": 6.5, "legal_status": "Regulated", "rank": 24},
    {"country": "UAE", "cca2": "AE", "lat": 23.42, "lng": 53.85, "adoption_pct": 6.0, "legal_status": "Regulated", "rank": 25},
]

# ===================================================================
# 5. TAX HAVENS  (25 jurisdictions)
# ===================================================================
TAX_HAVENS = [
    {"name": "Cayman Islands", "lat": 19.31, "lng": -81.25, "corp_tax_pct": 0.0, "type": "Offshore Financial Centre"},
    {"name": "British Virgin Islands", "lat": 18.42, "lng": -64.64, "corp_tax_pct": 0.0, "type": "Offshore Financial Centre"},
    {"name": "Luxembourg", "lat": 49.82, "lng": 6.13, "corp_tax_pct": 24.94, "type": "EU Conduit / Holding Companies"},
    {"name": "Ireland", "lat": 53.14, "lng": -7.69, "corp_tax_pct": 12.5, "type": "EU Tech Hub / IP Regime"},
    {"name": "Panama", "lat": 8.54, "lng": -80.78, "corp_tax_pct": 25.0, "type": "Territorial Tax / Secrecy"},
    {"name": "Bermuda", "lat": 32.32, "lng": -64.76, "corp_tax_pct": 0.0, "type": "Offshore Reinsurance Hub"},
    {"name": "Jersey", "lat": 49.21, "lng": -2.13, "corp_tax_pct": 0.0, "type": "Crown Dependency / Finance"},
    {"name": "Singapore", "lat": 1.35, "lng": 103.82, "corp_tax_pct": 17.0, "type": "Asia-Pacific Finance Hub"},
    {"name": "Hong Kong", "lat": 22.32, "lng": 114.17, "corp_tax_pct": 16.5, "type": "Territorial Tax / Finance Hub"},
    {"name": "Switzerland", "lat": 46.82, "lng": 8.23, "corp_tax_pct": 14.93, "type": "Private Banking / Low Tax"},
    {"name": "Netherlands", "lat": 52.13, "lng": 5.29, "corp_tax_pct": 25.8, "type": "EU Conduit / Treaty Network"},
    {"name": "Liechtenstein", "lat": 47.17, "lng": 9.56, "corp_tax_pct": 12.5, "type": "Micro-state / Low Tax"},
    {"name": "Monaco", "lat": 43.73, "lng": 7.42, "corp_tax_pct": 0.0, "type": "No Income Tax"},
    {"name": "Isle of Man", "lat": 54.24, "lng": -4.55, "corp_tax_pct": 0.0, "type": "Crown Dependency / E-Gaming"},
    {"name": "Guernsey", "lat": 49.45, "lng": -2.54, "corp_tax_pct": 0.0, "type": "Crown Dependency / Finance"},
    {"name": "Malta", "lat": 35.94, "lng": 14.38, "corp_tax_pct": 35.0, "type": "EU / Effective 5% via Refunds"},
    {"name": "Bahamas", "lat": 25.03, "lng": -77.40, "corp_tax_pct": 0.0, "type": "Offshore / No Income Tax"},
    {"name": "Mauritius", "lat": -20.35, "lng": 57.55, "corp_tax_pct": 15.0, "type": "Africa Gateway / Treaties"},
    {"name": "Seychelles", "lat": -4.68, "lng": 55.49, "corp_tax_pct": 25.0, "type": "Offshore IBCs"},
    {"name": "Cyprus", "lat": 35.13, "lng": 33.43, "corp_tax_pct": 12.5, "type": "EU / IP Box Regime"},
    {"name": "Barbados", "lat": 13.19, "lng": -59.54, "corp_tax_pct": 5.5, "type": "Offshore / Treaty Network"},
    {"name": "Curacao", "lat": 12.17, "lng": -68.98, "corp_tax_pct": 22.0, "type": "E-Zone / Offshore"},
    {"name": "Turks and Caicos", "lat": 21.69, "lng": -71.80, "corp_tax_pct": 0.0, "type": "No Tax Territory"},
    {"name": "Andorra", "lat": 42.51, "lng": 1.52, "corp_tax_pct": 10.0, "type": "Low Tax Micro-state"},
    {"name": "Vanuatu", "lat": -15.38, "lng": 166.96, "corp_tax_pct": 0.0, "type": "Zero Tax / Citizenship Sales"},
]

# ===================================================================
# 6. SOVEREIGN WEALTH FUNDS  (25 SWFs)
# ===================================================================
SOVEREIGN_WEALTH_FUNDS = [
    {"name": "Government Pension Fund Global (GPFG)", "country": "Norway", "lat": 59.91, "lng": 10.75, "aum_B": 1400, "founded": 1990, "source": "Oil & Gas"},
    {"name": "China Investment Corporation (CIC)", "country": "China", "lat": 39.90, "lng": 116.40, "aum_B": 1350, "founded": 2007, "source": "Foreign Reserves"},
    {"name": "Abu Dhabi Investment Authority (ADIA)", "country": "UAE", "lat": 24.45, "lng": 54.38, "aum_B": 993, "founded": 1976, "source": "Oil"},
    {"name": "Kuwait Investment Authority (KIA)", "country": "Kuwait", "lat": 29.38, "lng": 47.99, "aum_B": 803, "founded": 1953, "source": "Oil"},
    {"name": "GIC Private Limited", "country": "Singapore", "lat": 1.28, "lng": 103.85, "aum_B": 770, "founded": 1981, "source": "Foreign Reserves"},
    {"name": "Public Investment Fund (PIF)", "country": "Saudi Arabia", "lat": 24.71, "lng": 46.68, "aum_B": 930, "founded": 1971, "source": "Oil"},
    {"name": "SAFE Investment Company", "country": "China", "lat": 39.91, "lng": 116.42, "aum_B": 980, "founded": 1997, "source": "Foreign Reserves"},
    {"name": "Hong Kong Monetary Authority (HKMA)", "country": "Hong Kong", "lat": 22.28, "lng": 114.16, "aum_B": 587, "founded": 1993, "source": "Foreign Reserves"},
    {"name": "Temasek Holdings", "country": "Singapore", "lat": 1.30, "lng": 103.86, "aum_B": 382, "founded": 1974, "source": "Government Assets"},
    {"name": "National Council (NCSSF)", "country": "China", "lat": 39.92, "lng": 116.38, "aum_B": 365, "founded": 2000, "source": "Social Security"},
    {"name": "Qatar Investment Authority (QIA)", "country": "Qatar", "lat": 25.29, "lng": 51.53, "aum_B": 475, "founded": 2005, "source": "Oil & Gas"},
    {"name": "Investment Corporation of Dubai (ICD)", "country": "UAE", "lat": 25.20, "lng": 55.27, "aum_B": 320, "founded": 2006, "source": "Oil & Diversified"},
    {"name": "Mubadala Investment Company", "country": "UAE", "lat": 24.46, "lng": 54.37, "aum_B": 284, "founded": 2002, "source": "Oil & Diversified"},
    {"name": "Korea Investment Corporation (KIC)", "country": "South Korea", "lat": 37.57, "lng": 126.98, "aum_B": 200, "founded": 2005, "source": "Foreign Reserves"},
    {"name": "Future Fund", "country": "Australia", "lat": -33.87, "lng": 151.21, "aum_B": 183, "founded": 2006, "source": "Budget Surplus"},
    {"name": "Alaska Permanent Fund", "country": "United States", "lat": 58.30, "lng": -134.42, "aum_B": 78, "founded": 1976, "source": "Oil Royalties"},
    {"name": "National Wealth Fund", "country": "Russia", "lat": 55.76, "lng": 37.62, "aum_B": 148, "founded": 2008, "source": "Oil & Gas"},
    {"name": "Brunei Investment Agency", "country": "Brunei", "lat": 4.94, "lng": 114.95, "aum_B": 60, "founded": 1983, "source": "Oil & Gas"},
    {"name": "Libya Investment Authority", "country": "Libya", "lat": 32.90, "lng": 13.18, "aum_B": 67, "founded": 2006, "source": "Oil"},
    {"name": "Khazanah Nasional", "country": "Malaysia", "lat": 3.14, "lng": 101.69, "aum_B": 33, "founded": 1993, "source": "Government Assets"},
    {"name": "National Development Fund (NDFI)", "country": "Iran", "lat": 35.69, "lng": 51.39, "aum_B": 139, "founded": 2011, "source": "Oil & Gas"},
    {"name": "Ireland Strategic Investment Fund", "country": "Ireland", "lat": 53.35, "lng": -6.26, "aum_B": 12, "founded": 2014, "source": "Budget Surplus"},
    {"name": "Texas Permanent School Fund", "country": "United States", "lat": 30.27, "lng": -97.74, "aum_B": 53, "founded": 1854, "source": "Public Lands / Oil"},
    {"name": "New Zealand Superannuation Fund", "country": "New Zealand", "lat": -36.85, "lng": 174.76, "aum_B": 44, "founded": 2001, "source": "Government Contributions"},
    {"name": "Fundo Soberano de Angola", "country": "Angola", "lat": -8.84, "lng": 13.29, "aum_B": 5, "founded": 2012, "source": "Oil"},
]

# ===================================================================
# 7. CONTAINER PORTS  (top 40 by TEU throughput, millions)
# ===================================================================
CONTAINER_PORTS = [
    {"name": "Shanghai", "country": "China", "lat": 31.36, "lng": 121.62, "teu_M": 49.0},
    {"name": "Singapore", "country": "Singapore", "lat": 1.26, "lng": 103.83, "teu_M": 39.0},
    {"name": "Ningbo-Zhoushan", "country": "China", "lat": 29.87, "lng": 121.88, "teu_M": 35.3},
    {"name": "Shenzhen", "country": "China", "lat": 22.48, "lng": 114.08, "teu_M": 30.0},
    {"name": "Guangzhou", "country": "China", "lat": 22.96, "lng": 113.43, "teu_M": 25.0},
    {"name": "Qingdao", "country": "China", "lat": 36.07, "lng": 120.38, "teu_M": 25.0},
    {"name": "Busan", "country": "South Korea", "lat": 35.10, "lng": 129.04, "teu_M": 22.7},
    {"name": "Tianjin", "country": "China", "lat": 38.99, "lng": 117.78, "teu_M": 21.7},
    {"name": "Hong Kong", "country": "China", "lat": 22.34, "lng": 114.15, "teu_M": 16.6},
    {"name": "Rotterdam", "country": "Netherlands", "lat": 51.95, "lng": 4.13, "teu_M": 14.5},
    {"name": "Dubai (Jebel Ali)", "country": "UAE", "lat": 25.01, "lng": 55.06, "teu_M": 14.0},
    {"name": "Port Klang", "country": "Malaysia", "lat": 2.97, "lng": 101.39, "teu_M": 13.7},
    {"name": "Antwerp-Bruges", "country": "Belgium", "lat": 51.27, "lng": 4.34, "teu_M": 13.5},
    {"name": "Xiamen", "country": "China", "lat": 24.49, "lng": 118.08, "teu_M": 12.0},
    {"name": "Kaohsiung", "country": "Taiwan", "lat": 22.61, "lng": 120.31, "teu_M": 10.0},
    {"name": "Los Angeles", "country": "United States", "lat": 33.74, "lng": -118.26, "teu_M": 9.9},
    {"name": "Tanjung Pelepas", "country": "Malaysia", "lat": 1.37, "lng": 103.55, "teu_M": 9.8},
    {"name": "Hamburg", "country": "Germany", "lat": 53.53, "lng": 9.93, "teu_M": 8.7},
    {"name": "Long Beach", "country": "United States", "lat": 33.76, "lng": -118.19, "teu_M": 8.6},
    {"name": "Laem Chabang", "country": "Thailand", "lat": 13.07, "lng": 100.88, "teu_M": 8.5},
    {"name": "Tanjung Priok (Jakarta)", "country": "Indonesia", "lat": -6.10, "lng": 106.87, "teu_M": 8.2},
    {"name": "Dalian", "country": "China", "lat": 38.92, "lng": 121.64, "teu_M": 7.5},
    {"name": "Colombo", "country": "Sri Lanka", "lat": 6.95, "lng": 79.84, "teu_M": 7.3},
    {"name": "Ho Chi Minh City", "country": "Vietnam", "lat": 10.74, "lng": 106.76, "teu_M": 7.1},
    {"name": "Piraeus", "country": "Greece", "lat": 37.94, "lng": 23.63, "teu_M": 5.4},
    {"name": "Valencia", "country": "Spain", "lat": 39.45, "lng": -0.32, "teu_M": 5.3},
    {"name": "Algeciras", "country": "Spain", "lat": 36.13, "lng": -5.44, "teu_M": 5.1},
    {"name": "Felixstowe", "country": "United Kingdom", "lat": 51.96, "lng": 1.31, "teu_M": 3.8},
    {"name": "Savannah", "country": "United States", "lat": 32.08, "lng": -81.09, "teu_M": 5.8},
    {"name": "Jeddah", "country": "Saudi Arabia", "lat": 21.49, "lng": 39.17, "teu_M": 5.0},
    {"name": "Tanger Med", "country": "Morocco", "lat": 35.89, "lng": -5.50, "teu_M": 7.2},
    {"name": "Mumbai (JNPT)", "country": "India", "lat": 18.95, "lng": 72.95, "teu_M": 5.7},
    {"name": "Mundra", "country": "India", "lat": 22.74, "lng": 69.72, "teu_M": 6.5},
    {"name": "Manila", "country": "Philippines", "lat": 14.52, "lng": 120.97, "teu_M": 5.1},
    {"name": "Santos", "country": "Brazil", "lat": -23.97, "lng": -46.31, "teu_M": 4.8},
    {"name": "New York / New Jersey", "country": "United States", "lat": 40.68, "lng": -74.04, "teu_M": 9.5},
    {"name": "Colon", "country": "Panama", "lat": 9.36, "lng": -79.90, "teu_M": 4.9},
    {"name": "Durban", "country": "South Africa", "lat": -29.87, "lng": 31.04, "teu_M": 2.8},
    {"name": "Manzanillo", "country": "Mexico", "lat": 19.05, "lng": -104.32, "teu_M": 3.4},
    {"name": "Balboa (Panama)", "country": "Panama", "lat": 8.95, "lng": -79.57, "teu_M": 3.2},
]

# ===================================================================
# 8. OIL & GAS FIELDS  (30+ major fields)
# ===================================================================
OIL_GAS_FIELDS = [
    {"name": "Ghawar", "country": "Saudi Arabia", "lat": 25.38, "lng": 49.40, "type": "Oil", "reserves_Bbbl": 75.0, "prod_Mbpd": 3.8, "discovered": 1948},
    {"name": "Burgan", "country": "Kuwait", "lat": 29.07, "lng": 48.08, "type": "Oil", "reserves_Bbbl": 66.0, "prod_Mbpd": 1.7, "discovered": 1938},
    {"name": "Safaniya", "country": "Saudi Arabia", "lat": 28.20, "lng": 48.85, "type": "Oil (Offshore)", "reserves_Bbbl": 37.0, "prod_Mbpd": 1.5, "discovered": 1951},
    {"name": "Rumaila", "country": "Iraq", "lat": 30.60, "lng": 47.30, "type": "Oil", "reserves_Bbbl": 17.8, "prod_Mbpd": 1.4, "discovered": 1953},
    {"name": "Prudhoe Bay", "country": "United States", "lat": 70.25, "lng": -148.34, "type": "Oil", "reserves_Bbbl": 12.0, "prod_Mbpd": 0.2, "discovered": 1968},
    {"name": "Cantarell", "country": "Mexico", "lat": 19.68, "lng": -92.21, "type": "Oil (Offshore)", "reserves_Bbbl": 18.0, "prod_Mbpd": 0.15, "discovered": 1976},
    {"name": "Samotlor", "country": "Russia", "lat": 61.18, "lng": 76.75, "type": "Oil", "reserves_Bbbl": 28.0, "prod_Mbpd": 0.4, "discovered": 1965},
    {"name": "Kashagan", "country": "Kazakhstan", "lat": 46.20, "lng": 51.60, "type": "Oil (Offshore)", "reserves_Bbbl": 13.0, "prod_Mbpd": 0.4, "discovered": 2000},
    {"name": "North Field / South Pars", "country": "Qatar / Iran", "lat": 26.50, "lng": 52.00, "type": "Gas", "reserves_Bbbl": 50.0, "prod_Mbpd": 0.0, "discovered": 1971},
    {"name": "Tengiz", "country": "Kazakhstan", "lat": 46.18, "lng": 53.38, "type": "Oil", "reserves_Bbbl": 9.0, "prod_Mbpd": 0.6, "discovered": 1979},
    {"name": "Zakum (Upper & Lower)", "country": "UAE", "lat": 24.70, "lng": 53.80, "type": "Oil (Offshore)", "reserves_Bbbl": 21.0, "prod_Mbpd": 0.6, "discovered": 1963},
    {"name": "Daqing", "country": "China", "lat": 46.59, "lng": 125.01, "type": "Oil", "reserves_Bbbl": 16.0, "prod_Mbpd": 0.3, "discovered": 1959},
    {"name": "Bolivar Coastal", "country": "Venezuela", "lat": 10.10, "lng": -71.60, "type": "Oil", "reserves_Bbbl": 32.0, "prod_Mbpd": 0.4, "discovered": 1917},
    {"name": "Shaybah", "country": "Saudi Arabia", "lat": 22.52, "lng": 54.08, "type": "Oil", "reserves_Bbbl": 14.3, "prod_Mbpd": 1.0, "discovered": 1968},
    {"name": "Ahwaz", "country": "Iran", "lat": 31.32, "lng": 48.68, "type": "Oil", "reserves_Bbbl": 25.5, "prod_Mbpd": 0.8, "discovered": 1958},
    {"name": "Marlim", "country": "Brazil", "lat": -22.40, "lng": -40.00, "type": "Oil (Deepwater)", "reserves_Bbbl": 8.0, "prod_Mbpd": 0.3, "discovered": 1985},
    {"name": "Tupi / Lula", "country": "Brazil", "lat": -25.35, "lng": -43.00, "type": "Oil (Pre-salt)", "reserves_Bbbl": 8.3, "prod_Mbpd": 1.0, "discovered": 2006},
    {"name": "Hassi Messaoud", "country": "Algeria", "lat": 31.68, "lng": 6.05, "type": "Oil", "reserves_Bbbl": 3.7, "prod_Mbpd": 0.4, "discovered": 1956},
    {"name": "Ekofisk", "country": "Norway", "lat": 56.55, "lng": 3.22, "type": "Oil (Offshore)", "reserves_Bbbl": 3.3, "prod_Mbpd": 0.2, "discovered": 1969},
    {"name": "Johan Sverdrup", "country": "Norway", "lat": 58.78, "lng": 2.50, "type": "Oil (Offshore)", "reserves_Bbbl": 2.7, "prod_Mbpd": 0.7, "discovered": 2010},
    {"name": "Troll", "country": "Norway", "lat": 60.64, "lng": 3.73, "type": "Gas (Offshore)", "reserves_Bbbl": 9.0, "prod_Mbpd": 0.0, "discovered": 1979},
    {"name": "Brent", "country": "United Kingdom", "lat": 61.05, "lng": 1.72, "type": "Oil (Offshore)", "reserves_Bbbl": 4.0, "prod_Mbpd": 0.0, "discovered": 1971},
    {"name": "Bass Strait", "country": "Australia", "lat": -38.50, "lng": 148.00, "type": "Oil & Gas", "reserves_Bbbl": 4.0, "prod_Mbpd": 0.02, "discovered": 1967},
    {"name": "Groningen", "country": "Netherlands", "lat": 53.33, "lng": 6.75, "type": "Gas", "reserves_Bbbl": 2.8, "prod_Mbpd": 0.0, "discovered": 1959},
    {"name": "Permian Basin", "country": "United States", "lat": 31.90, "lng": -102.50, "type": "Oil & Gas (Shale)", "reserves_Bbbl": 46.3, "prod_Mbpd": 5.8, "discovered": 1920},
    {"name": "Eagle Ford Shale", "country": "United States", "lat": 28.70, "lng": -98.50, "type": "Oil & Gas (Shale)", "reserves_Bbbl": 10.0, "prod_Mbpd": 1.2, "discovered": 2008},
    {"name": "Bakken Formation", "country": "United States", "lat": 48.20, "lng": -103.50, "type": "Oil (Shale)", "reserves_Bbbl": 7.4, "prod_Mbpd": 1.1, "discovered": 1953},
    {"name": "West Qurna", "country": "Iraq", "lat": 31.10, "lng": 47.20, "type": "Oil", "reserves_Bbbl": 21.0, "prod_Mbpd": 0.5, "discovered": 1973},
    {"name": "Vaca Muerta", "country": "Argentina", "lat": -38.50, "lng": -69.50, "type": "Oil & Gas (Shale)", "reserves_Bbbl": 16.0, "prod_Mbpd": 0.4, "discovered": 2010},
    {"name": "Agbami", "country": "Nigeria", "lat": 4.13, "lng": 4.53, "type": "Oil (Deepwater)", "reserves_Bbbl": 1.0, "prod_Mbpd": 0.25, "discovered": 1998},
    {"name": "Karachaganak", "country": "Kazakhstan", "lat": 50.08, "lng": 51.88, "type": "Gas / Condensate", "reserves_Bbbl": 2.4, "prod_Mbpd": 0.25, "discovered": 1979},
]

# ===================================================================
# 9. ECONOMIC CORRIDORS
# ===================================================================
ECONOMIC_CORRIDORS = [
    {
        "name": "China-Pakistan Economic Corridor (CPEC)",
        "investment_B": 62,
        "status": "Under Construction",
        "points": [[39.47, 75.98], [35.92, 74.31], [33.69, 73.04], [30.20, 67.01], [25.12, 62.33], [24.87, 66.99]],
        "color": "#ef4444",
    },
    {
        "name": "New Eurasian Land Bridge",
        "investment_B": 40,
        "status": "Operational",
        "points": [[34.26, 108.94], [39.47, 75.98], [41.30, 69.28], [51.17, 71.45], [55.75, 37.62], [52.23, 21.01], [50.11, 8.68], [51.51, -0.13]],
        "color": "#f59e0b",
    },
    {
        "name": "China-Central Asia-West Asia Corridor",
        "investment_B": 35,
        "status": "Under Development",
        "points": [[34.26, 108.94], [43.24, 76.95], [41.30, 69.28], [38.58, 68.77], [35.69, 51.39], [41.01, 28.98]],
        "color": "#8b5cf6",
    },
    {
        "name": "Bangladesh-China-India-Myanmar (BCIM)",
        "investment_B": 22,
        "status": "Proposed",
        "points": [[22.57, 88.36], [21.91, 92.36], [19.76, 96.17], [25.04, 102.68], [30.57, 104.07]],
        "color": "#06b6d4",
    },
    {
        "name": "LAPSSET Corridor",
        "investment_B": 26,
        "status": "Under Construction",
        "points": [[-2.27, 40.90], [0.51, 38.00], [3.59, 38.45], [9.02, 38.75], [2.05, 45.34], [9.15, 42.59]],
        "color": "#10b981",
    },
    {
        "name": "India-Myanmar-Thailand Trilateral Highway",
        "investment_B": 4,
        "status": "Partial Operation",
        "points": [[24.81, 93.95], [21.97, 96.08], [19.76, 96.17], [18.79, 98.98], [13.76, 100.50]],
        "color": "#ec4899",
    },
    {
        "name": "Trans-Saharan Highway",
        "investment_B": 7,
        "status": "Partial / Under Construction",
        "points": [[36.75, 3.06], [32.08, 3.60], [27.15, 2.00], [16.97, 7.99], [9.06, 7.49], [6.52, 3.38]],
        "color": "#ca8a04",
    },
    {
        "name": "China-Indochina Peninsula Corridor",
        "investment_B": 30,
        "status": "Under Development",
        "points": [[22.80, 108.32], [21.03, 105.85], [17.97, 102.63], [13.76, 100.50], [3.14, 101.69], [1.35, 103.82]],
        "color": "#22d3ee",
    },
    {
        "name": "North-South Transport Corridor (INSTC)",
        "investment_B": 25,
        "status": "Operational / Expanding",
        "points": [[18.94, 72.84], [23.42, 58.38], [35.69, 51.39], [40.41, 49.87], [55.75, 37.62], [59.93, 30.32]],
        "color": "#e11d48",
    },
    {
        "name": "China-Mongolia-Russia Economic Corridor",
        "investment_B": 10,
        "status": "Under Development",
        "points": [[39.90, 116.40], [47.91, 106.91], [51.83, 107.59], [55.75, 37.62]],
        "color": "#d946ef",
    },
]

# ===================================================================
# 10. CURRENCY ZONES
# ===================================================================
CURRENCY_ZONES = [
    {"currency": "US Dollar (USD)", "symbol": "$", "zone_color": "#16a34a",
     "countries": [
         {"name": "United States", "lat": 37.09, "lng": -95.71, "cca2": "US"},
         {"name": "Ecuador", "lat": -1.83, "lng": -78.18, "cca2": "EC"},
         {"name": "El Salvador", "lat": 13.79, "lng": -88.90, "cca2": "SV"},
         {"name": "Panama", "lat": 8.54, "lng": -80.78, "cca2": "PA"},
         {"name": "Zimbabwe", "lat": -19.02, "lng": 29.15, "cca2": "ZW"},
     ], "rate_vs_usd": 1.00},
    {"currency": "Euro (EUR)", "symbol": "\u20ac", "zone_color": "#2563eb",
     "countries": [
         {"name": "Germany", "lat": 51.17, "lng": 10.45, "cca2": "DE"},
         {"name": "France", "lat": 46.23, "lng": 2.21, "cca2": "FR"},
         {"name": "Italy", "lat": 41.87, "lng": 12.57, "cca2": "IT"},
         {"name": "Spain", "lat": 40.46, "lng": -3.75, "cca2": "ES"},
         {"name": "Netherlands", "lat": 52.13, "lng": 5.29, "cca2": "NL"},
         {"name": "Belgium", "lat": 50.50, "lng": 4.47, "cca2": "BE"},
         {"name": "Austria", "lat": 47.52, "lng": 14.55, "cca2": "AT"},
         {"name": "Portugal", "lat": 39.40, "lng": -8.22, "cca2": "PT"},
         {"name": "Greece", "lat": 39.07, "lng": 21.82, "cca2": "GR"},
         {"name": "Finland", "lat": 61.92, "lng": 25.75, "cca2": "FI"},
         {"name": "Ireland", "lat": 53.14, "lng": -7.69, "cca2": "IE"},
         {"name": "Slovakia", "lat": 48.67, "lng": 19.70, "cca2": "SK"},
         {"name": "Slovenia", "lat": 46.15, "lng": 14.99, "cca2": "SI"},
         {"name": "Estonia", "lat": 58.60, "lng": 25.01, "cca2": "EE"},
         {"name": "Latvia", "lat": 56.88, "lng": 24.60, "cca2": "LV"},
         {"name": "Lithuania", "lat": 55.17, "lng": 23.88, "cca2": "LT"},
         {"name": "Cyprus", "lat": 35.13, "lng": 33.43, "cca2": "CY"},
         {"name": "Malta", "lat": 35.94, "lng": 14.38, "cca2": "MT"},
         {"name": "Luxembourg", "lat": 49.82, "lng": 6.13, "cca2": "LU"},
         {"name": "Croatia", "lat": 45.10, "lng": 15.20, "cca2": "HR"},
     ], "rate_vs_usd": 0.92},
    {"currency": "British Pound (GBP)", "symbol": "\u00a3", "zone_color": "#dc2626",
     "countries": [
         {"name": "United Kingdom", "lat": 55.38, "lng": -3.44, "cca2": "GB"},
     ], "rate_vs_usd": 0.79},
    {"currency": "Japanese Yen (JPY)", "symbol": "\u00a5", "zone_color": "#e11d48",
     "countries": [
         {"name": "Japan", "lat": 36.20, "lng": 138.25, "cca2": "JP"},
     ], "rate_vs_usd": 149.50},
    {"currency": "Chinese Yuan (CNY)", "symbol": "\u00a5", "zone_color": "#ea580c",
     "countries": [
         {"name": "China", "lat": 35.86, "lng": 104.20, "cca2": "CN"},
     ], "rate_vs_usd": 7.24},
    {"currency": "Indian Rupee (INR)", "symbol": "\u20b9", "zone_color": "#f59e0b",
     "countries": [
         {"name": "India", "lat": 20.59, "lng": 78.96, "cca2": "IN"},
     ], "rate_vs_usd": 83.10},
    {"currency": "Swiss Franc (CHF)", "symbol": "CHF", "zone_color": "#9333ea",
     "countries": [
         {"name": "Switzerland", "lat": 46.82, "lng": 8.23, "cca2": "CH"},
         {"name": "Liechtenstein", "lat": 47.17, "lng": 9.56, "cca2": "LI"},
     ], "rate_vs_usd": 0.88},
    {"currency": "CFA Franc (XOF/XAF)", "symbol": "CFA", "zone_color": "#65a30d",
     "countries": [
         {"name": "Senegal", "lat": 14.50, "lng": -14.45, "cca2": "SN"},
         {"name": "Cote d'Ivoire", "lat": 7.54, "lng": -5.55, "cca2": "CI"},
         {"name": "Mali", "lat": 17.57, "lng": -4.00, "cca2": "ML"},
         {"name": "Burkina Faso", "lat": 12.24, "lng": -1.56, "cca2": "BF"},
         {"name": "Niger", "lat": 17.61, "lng": 8.08, "cca2": "NE"},
         {"name": "Cameroon", "lat": 7.37, "lng": 12.35, "cca2": "CM"},
         {"name": "Chad", "lat": 15.45, "lng": 18.73, "cca2": "TD"},
         {"name": "Gabon", "lat": -0.80, "lng": 11.61, "cca2": "GA"},
     ], "rate_vs_usd": 601.50},
    {"currency": "Australian Dollar (AUD)", "symbol": "A$", "zone_color": "#0ea5e9",
     "countries": [
         {"name": "Australia", "lat": -25.27, "lng": 133.78, "cca2": "AU"},
     ], "rate_vs_usd": 1.54},
    {"currency": "Canadian Dollar (CAD)", "symbol": "C$", "zone_color": "#b91c1c",
     "countries": [
         {"name": "Canada", "lat": 56.13, "lng": -106.35, "cca2": "CA"},
     ], "rate_vs_usd": 1.36},
    {"currency": "Brazilian Real (BRL)", "symbol": "R$", "zone_color": "#059669",
     "countries": [
         {"name": "Brazil", "lat": -14.24, "lng": -51.93, "cca2": "BR"},
     ], "rate_vs_usd": 4.97},
    {"currency": "Russian Ruble (RUB)", "symbol": "\u20bd", "zone_color": "#7c3aed",
     "countries": [
         {"name": "Russia", "lat": 61.52, "lng": 105.32, "cca2": "RU"},
     ], "rate_vs_usd": 92.50},
    {"currency": "South Korean Won (KRW)", "symbol": "\u20a9", "zone_color": "#0284c7",
     "countries": [
         {"name": "South Korea", "lat": 35.91, "lng": 127.77, "cca2": "KR"},
     ], "rate_vs_usd": 1330.0},
    {"currency": "Mexican Peso (MXN)", "symbol": "MX$", "zone_color": "#047857",
     "countries": [
         {"name": "Mexico", "lat": 23.63, "lng": -102.55, "cca2": "MX"},
     ], "rate_vs_usd": 17.15},
    {"currency": "Saudi Riyal (SAR)", "symbol": "SAR", "zone_color": "#15803d",
     "countries": [
         {"name": "Saudi Arabia", "lat": 23.89, "lng": 45.08, "cca2": "SA"},
     ], "rate_vs_usd": 3.75},
]


# ===================================================================
# CACHED API FETCHERS
# ===================================================================

@st.cache_data(ttl=3600)
def _fetch_rest_countries() -> pd.DataFrame:
    """Fetch country centroids, population, gini, and currency info."""
    try:
        resp = requests.get(REST_COUNTRIES_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("REST Countries fetch failed: %s", exc)
        return pd.DataFrame()

    rows = []
    for c in data:
        name = c.get("name", {}).get("common", "")
        cca2 = c.get("cca2", "")
        latlng = c.get("latlng", [None, None])
        pop = c.get("population", 0)
        region = c.get("region", "")
        gini = c.get("gini", {})
        gini_val = list(gini.values())[0] if gini else None
        currencies = c.get("currencies", {})
        curr_code = list(currencies.keys())[0] if currencies else ""
        curr_name = currencies.get(curr_code, {}).get("name", "") if curr_code else ""
        if cca2 and latlng and len(latlng) == 2 and latlng[0] is not None:
            rows.append({
                "country": name,
                "cca2": cca2,
                "lat": latlng[0],
                "lng": latlng[1],
                "population": pop,
                "region": region,
                "gini": gini_val,
                "currency_code": curr_code,
                "currency_name": curr_name,
            })
    return pd.DataFrame(rows)


# ===================================================================
# COLOR / RADIUS HELPERS
# ===================================================================

def _value_to_hex(value: float, vmin: float, vmax: float, cmap_name: str) -> str:
    """Map a numeric value to a hex color using a matplotlib colormap."""
    cmap = plt.get_cmap(cmap_name)
    if vmax == vmin:
        norm = 0.5
    else:
        norm = (value - vmin) / (vmax - vmin)
    norm = max(0.0, min(1.0, norm))
    rgba = cmap(norm)
    return mcolors.to_hex(rgba)


def _marker_radius(value: float, vmin: float, vmax: float,
                   rmin: float = 4.0, rmax: float = 22.0) -> float:
    """Scale value to a marker radius."""
    if vmax == vmin:
        return (rmin + rmax) / 2
    ratio = (value - vmin) / (vmax - vmin)
    ratio = max(0.0, min(1.0, ratio))
    return rmin + ratio * (rmax - rmin)


# ===================================================================
# CHART BUILDER (dark theme matplotlib)
# ===================================================================

def _dark_bar_chart(df: pd.DataFrame, x_col: str, y_col: str,
                    title: str, color: str = "#06b6d4",
                    xlabel: str = "", ylabel: str = "",
                    horizontal: bool = True, top_n: int = 20) -> io.BytesIO:
    """Build a dark-themed horizontal bar chart and return as BytesIO PNG."""
    subset = df.nlargest(top_n, y_col).sort_values(y_col, ascending=True)
    fig, ax = plt.subplots(figsize=(7, max(4, top_n * 0.28)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    if horizontal:
        ax.barh(subset[x_col], subset[y_col], color=color, edgecolor="#2a3550")
        ax.set_xlabel(xlabel or y_col, color="#8b97b0", fontsize=9)
        ax.set_ylabel(ylabel or x_col, color="#8b97b0", fontsize=9)
    else:
        ax.bar(subset[x_col], subset[y_col], color=color, edgecolor="#2a3550")
        ax.set_ylabel(xlabel or y_col, color="#8b97b0", fontsize=9)
        ax.set_xlabel(ylabel or x_col, color="#8b97b0", fontsize=9)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    ax.tick_params(colors="#8b97b0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x" if horizontal else "y", alpha=0.15, color="#5a6580")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#0a0e1a", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# ===================================================================
# MAP BUILDERS  (one function per map type)
# ===================================================================

def _build_gdp_map() -> tuple:
    """1. GDP Per Capita map with colored circles."""
    countries_df = _fetch_rest_countries()
    if countries_df.empty:
        st.error("Failed to fetch country data from REST Countries API.")
        return None, pd.DataFrame()

    # merge hardcoded GDP with country centroids
    gdp_df = pd.DataFrame([
        {"cca2": k, "gdp_per_capita": v} for k, v in GDP_PER_CAPITA.items()
    ])
    merged = countries_df.merge(gdp_df, on="cca2", how="inner")
    if merged.empty:
        st.warning("No GDP data could be matched with country coordinates.")
        return None, pd.DataFrame()

    vmin = merged["gdp_per_capita"].min()
    vmax = merged["gdp_per_capita"].max()

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in merged.iterrows():
        gdp = row["gdp_per_capita"]
        color = _value_to_hex(gdp, vmin, vmax, "RdYlGn")
        radius = _marker_radius(gdp, vmin, vmax, 4, 18)
        popup_html = (
            f"<b>{escape(str(row['country']))}</b><br>"
            f"GDP/capita: <b>${gdp:,.0f}</b><br>"
            f"Population: {row['population']:,.0f}<br>"
            f"Region: {escape(str(row['region']))}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{escape(str(row['country']))}: ${gdp:,.0f}",
        ).add_to(m)

    display_df = merged[["country", "cca2", "gdp_per_capita", "population", "region"]].copy()
    display_df.columns = ["Country", "Code", "GDP/Capita (USD)", "Population", "Region"]
    display_df = display_df.sort_values("GDP/Capita (USD)", ascending=False).reset_index(drop=True)
    return m, display_df


def _build_trade_blocs_map() -> tuple:
    """2. Trade Blocs map with colored markers per bloc membership."""
    countries_df = _fetch_rest_countries()
    if countries_df.empty:
        st.error("Failed to fetch country data.")
        return None, pd.DataFrame()

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    all_rows = []

    for bloc_name, bloc_info in TRADE_BLOCS.items():
        color = bloc_info["color"]
        fg = folium.FeatureGroup(name=bloc_name)
        for member_code in bloc_info["members"]:
            match = countries_df[countries_df["cca2"] == member_code]
            if match.empty:
                continue
            row = match.iloc[0]
            popup_html = (
                f"<b>{escape(str(row['country']))}</b><br>"
                f"Bloc: <b>{escape(bloc_name)}</b><br>"
                f"Population: {row['population']:,.0f}"
            )
            folium.CircleMarker(
                location=[row["lat"], row["lng"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=f"{escape(str(row['country']))} ({escape(bloc_name)})",
            ).add_to(fg)
            all_rows.append({
                "Country": row["country"],
                "Code": member_code,
                "Trade Bloc": bloc_name,
                "Region": row["region"],
            })
        fg.add_to(m)

    folium.LayerControl().add_to(m)
    display_df = pd.DataFrame(all_rows)
    return m, display_df


def _build_stock_exchanges_map() -> tuple:
    """3. Stock Exchanges map with graduated circles by market cap."""
    df = pd.DataFrame(STOCK_EXCHANGES)
    vmin = df["market_cap_T"].min()
    vmax = df["market_cap_T"].max()

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        mc = row["market_cap_T"]
        radius = _marker_radius(mc, vmin, vmax, 5, 25)
        color = _value_to_hex(mc, vmin, vmax, "plasma")
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"City: {escape(str(row['city']))}<br>"
            f"Market Cap: <b>${mc:.2f}T</b><br>"
            f"Founded: {row['founded']}<br>"
            f"Country: {escape(str(row['country']))}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{escape(str(row['name']))}: ${mc:.2f}T",
        ).add_to(m)

    display_df = df[["name", "city", "country", "market_cap_T", "founded"]].copy()
    display_df.columns = ["Exchange", "City", "Country", "Market Cap ($T)", "Founded"]
    display_df = display_df.sort_values("Market Cap ($T)", ascending=False).reset_index(drop=True)
    return m, display_df


def _build_crypto_adoption_map() -> tuple:
    """4. Cryptocurrency Adoption map with colored markers."""
    df = pd.DataFrame(CRYPTO_ADOPTION)
    vmin = df["adoption_pct"].min()
    vmax = df["adoption_pct"].max()

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        pct = row["adoption_pct"]
        color = _value_to_hex(pct, vmin, vmax, "YlOrRd")
        radius = _marker_radius(pct, vmin, vmax, 6, 20)
        status = escape(str(row["legal_status"]))
        popup_html = (
            f"<b>{escape(str(row['country']))}</b><br>"
            f"Adoption: <b>{pct}%</b><br>"
            f"Legal Status: {status}<br>"
            f"Rank: #{row['rank']}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{escape(str(row['country']))}: {pct}%",
        ).add_to(m)

    display_df = df[["country", "cca2", "adoption_pct", "legal_status", "rank"]].copy()
    display_df.columns = ["Country", "Code", "Adoption %", "Legal Status", "Rank"]
    display_df = display_df.sort_values("Adoption %", ascending=False).reset_index(drop=True)
    return m, display_df


def _build_tax_havens_map() -> tuple:
    """5. Tax Havens map with corporate tax rate markers."""
    df = pd.DataFrame(TAX_HAVENS)
    vmin = df["corp_tax_pct"].min()
    vmax = max(df["corp_tax_pct"].max(), 1.0)

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        tax = row["corp_tax_pct"]
        # Lower tax = more red; higher = more green
        color = _value_to_hex(tax, vmin, vmax, "RdYlGn")
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Corporate Tax: <b>{tax}%</b><br>"
            f"Type: {escape(str(row['type']))}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{escape(str(row['name']))}: {tax}%",
        ).add_to(m)

    display_df = df[["name", "corp_tax_pct", "type"]].copy()
    display_df.columns = ["Jurisdiction", "Corporate Tax %", "Type"]
    display_df = display_df.sort_values("Corporate Tax %", ascending=True).reset_index(drop=True)
    return m, display_df


def _build_swf_map() -> tuple:
    """6. Sovereign Wealth Funds map with graduated circles by AUM."""
    df = pd.DataFrame(SOVEREIGN_WEALTH_FUNDS)
    vmin = df["aum_B"].min()
    vmax = df["aum_B"].max()

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        aum = row["aum_B"]
        radius = _marker_radius(aum, vmin, vmax, 5, 28)
        color = _value_to_hex(aum, vmin, vmax, "YlGnBu")
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"AUM: <b>${aum:,.0f}B</b><br>"
            f"Founded: {row['founded']}<br>"
            f"Source: {escape(str(row['source']))}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{escape(str(row['name']))}: ${aum:,.0f}B",
        ).add_to(m)

    display_df = df[["name", "country", "aum_B", "founded", "source"]].copy()
    display_df.columns = ["Fund", "Country", "AUM ($B)", "Founded", "Source"]
    display_df = display_df.sort_values("AUM ($B)", ascending=False).reset_index(drop=True)
    return m, display_df


def _build_container_ports_map() -> tuple:
    """7. Container Ports map with graduated circles by TEU."""
    df = pd.DataFrame(CONTAINER_PORTS)
    vmin = df["teu_M"].min()
    vmax = df["teu_M"].max()

    m = folium.Map(location=[20, 30], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        teu = row["teu_M"]
        radius = _marker_radius(teu, vmin, vmax, 4, 22)
        color = _value_to_hex(teu, vmin, vmax, "viridis")
        popup_html = (
            f"<b>Port of {escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Throughput: <b>{teu:.1f}M TEU</b>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{escape(str(row['name']))}: {teu:.1f}M TEU",
        ).add_to(m)

    display_df = df[["name", "country", "teu_M"]].copy()
    display_df.columns = ["Port", "Country", "TEU (Millions)"]
    display_df = display_df.sort_values("TEU (Millions)", ascending=False).reset_index(drop=True)
    return m, display_df


def _build_oil_gas_map() -> tuple:
    """8. Oil & Gas Fields map with graduated circles by reserves."""
    df = pd.DataFrame(OIL_GAS_FIELDS)
    vmin = df["reserves_Bbbl"].min()
    vmax = df["reserves_Bbbl"].max()

    m = folium.Map(location=[30, 40], zoom_start=2, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        res = row["reserves_Bbbl"]
        radius = _marker_radius(res, vmin, vmax, 5, 22)
        # Oil = orange/red, Gas = blue
        if "Gas" in row["type"] and "Oil" not in row["type"]:
            color = "#38bdf8"
        else:
            color = _value_to_hex(res, vmin, vmax, "YlOrRd")
        prod = row["prod_Mbpd"]
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Type: {escape(str(row['type']))}<br>"
            f"Reserves: <b>{res:.1f} Bbbl equiv.</b><br>"
            f"Production: {prod:.2f} Mbpd<br>"
            f"Discovered: {row['discovered']}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{escape(str(row['name']))}: {res:.1f}B bbl",
        ).add_to(m)

    display_df = df[["name", "country", "type", "reserves_Bbbl", "prod_Mbpd", "discovered"]].copy()
    display_df.columns = ["Field", "Country", "Type", "Reserves (Bbbl)", "Prod (Mbpd)", "Discovered"]
    display_df = display_df.sort_values("Reserves (Bbbl)", ascending=False).reset_index(drop=True)
    return m, display_df


def _build_corridors_map() -> tuple:
    """9. Economic Corridors map with polylines."""
    m = folium.Map(location=[30, 60], zoom_start=3, tiles="CartoDB dark_matter")
    rows = []

    for corridor in ECONOMIC_CORRIDORS:
        name = corridor["name"]
        points = corridor["points"]
        color = corridor["color"]
        inv = corridor["investment_B"]
        status = corridor["status"]

        folium.PolyLine(
            locations=points,
            color=color,
            weight=4,
            opacity=0.85,
            tooltip=f"{escape(name)}: ${inv}B",
            popup=folium.Popup(
                f"<b>{escape(name)}</b><br>"
                f"Investment: <b>${inv}B</b><br>"
                f"Status: {escape(status)}",
                max_width=300,
            ),
        ).add_to(m)

        # Place a marker at the midpoint
        mid_idx = len(points) // 2
        mid = points[mid_idx]
        folium.Marker(
            location=mid,
            icon=folium.DivIcon(html=(
                f'<div style="font-size:9px;color:{color};'
                f'text-shadow:1px 1px 2px #000;white-space:nowrap;">'
                f'{escape(name.split("(")[0].strip())}</div>'
            )),
        ).add_to(m)

        rows.append({
            "Corridor": name,
            "Investment ($B)": inv,
            "Status": status,
            "Segments": len(points) - 1,
        })

    display_df = pd.DataFrame(rows).sort_values("Investment ($B)", ascending=False).reset_index(drop=True)
    return m, display_df


def _build_currency_zones_map() -> tuple:
    """10. Currency Zones map with colored country centroids."""
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    rows = []

    for zone in CURRENCY_ZONES:
        currency = zone["currency"]
        symbol = zone["symbol"]
        color = zone["zone_color"]
        rate = zone["rate_vs_usd"]

        fg = folium.FeatureGroup(name=currency)
        for c in zone["countries"]:
            popup_html = (
                f"<b>{escape(str(c['name']))}</b><br>"
                f"Currency: <b>{escape(currency)}</b><br>"
                f"Symbol: {escape(symbol)}<br>"
                f"Rate vs USD: {rate:,.2f}"
            )
            folium.CircleMarker(
                location=[c["lat"], c["lng"]],
                radius=9,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{escape(str(c['name']))}: {escape(currency)}",
            ).add_to(fg)
            rows.append({
                "Country": c["name"],
                "Code": c["cca2"],
                "Currency": currency,
                "Symbol": symbol,
                "Rate vs USD": rate,
            })
        fg.add_to(m)

    folium.LayerControl().add_to(m)
    display_df = pd.DataFrame(rows)
    return m, display_df


# ===================================================================
# MAP DISPATCH TABLE
# ===================================================================
MAP_OPTIONS = {
    "GDP Per Capita": {
        "builder": _build_gdp_map,
        "desc": "GDP per capita for ~80 countries shown as colored circles. Data from REST Countries API + hardcoded GDP estimates.",
        "icon": "bar-chart",
    },
    "Trade Blocs": {
        "builder": _build_trade_blocs_map,
        "desc": "Major trade blocs (EU, USMCA, ASEAN, Mercosur, AU, BRICS, OPEC, RCEP, CPTPP) with member countries color-coded.",
        "icon": "globe",
    },
    "Stock Exchanges": {
        "builder": _build_stock_exchanges_map,
        "desc": "40+ global stock exchanges as graduated circles by market capitalization.",
        "icon": "trending-up",
    },
    "Cryptocurrency Adoption": {
        "builder": _build_crypto_adoption_map,
        "desc": "Country-level cryptocurrency adoption rates with legal status information.",
        "icon": "cpu",
    },
    "Tax Havens": {
        "builder": _build_tax_havens_map,
        "desc": "25 global tax haven jurisdictions with corporate tax rates and classification.",
        "icon": "shield",
    },
    "Sovereign Wealth Funds": {
        "builder": _build_swf_map,
        "desc": "25 largest sovereign wealth funds by assets under management (AUM).",
        "icon": "database",
    },
    "Container Ports": {
        "builder": _build_container_ports_map,
        "desc": "Top 40 container ports worldwide by TEU throughput.",
        "icon": "anchor",
    },
    "Oil & Gas Fields": {
        "builder": _build_oil_gas_map,
        "desc": "30+ major oil and gas fields with reserves, production, and discovery data.",
        "icon": "droplet",
    },
    "Economic Corridors": {
        "builder": _build_corridors_map,
        "desc": "Major economic corridors including Belt and Road, CPEC, LAPSSET, and more.",
        "icon": "git-branch",
    },
    "Currency Zones": {
        "builder": _build_currency_zones_map,
        "desc": "World currencies grouped by zone with exchange rate information vs USD.",
        "icon": "dollar-sign",
    },
}


# ===================================================================
# MAIN RENDER FUNCTION
# ===================================================================

def render_economics_maps_tab():
    """Main entry point - renders the Economics & Trade Maps tab content."""
    st.markdown(
        '<div class="tab-header amber">'
        "<h4>Economics &amp; Trade Maps</h4>"
        "<p>GDP, trade blocs, stock exchanges, shipping ports, "
        "economic corridors, currencies</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # --- controls ---
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected = st.selectbox(
            "Select Map Type",
            options=list(MAP_OPTIONS.keys()),
            key="econ_map_type",
        )
    with col_btn:
        st.write("")  # vertical spacer
        generate = st.button("Generate Map", key="econ_generate", type="primary")

    map_info = MAP_OPTIONS[selected]
    st.caption(map_info["desc"])

    if not generate:
        st.info("Select a map type and click **Generate Map** to begin.")
        return

    # --- build the map ---
    with st.spinner(f"Building {selected} map..."):
        builder_fn = map_info["builder"]
        folium_map, data_df = builder_fn()

    if folium_map is None:
        st.error("Map generation failed. Please try again.")
        return

    # --- stats metrics ---
    st.markdown("---")
    if not data_df.empty:
        num_cols = [c for c in data_df.columns if data_df[c].dtype in ("float64", "int64", "float32", "int32")]
        metric_cols = st.columns(min(len(num_cols) + 1, 5))
        with metric_cols[0]:
            st.metric("Records", f"{len(data_df):,}")
        for i, nc in enumerate(num_cols[:4]):
            with metric_cols[min(i + 1, len(metric_cols) - 1)]:
                if data_df[nc].max() > 1_000_000:
                    st.metric(nc, f"{data_df[nc].sum():,.0f}")
                else:
                    st.metric(f"Avg {nc}", f"{data_df[nc].mean():,.2f}")

    # --- render folium map ---
    st.subheader(f"{selected}")
    components.html(folium_map._repr_html_(), height=550)

    # --- chart for select map types ---
    if selected == "GDP Per Capita" and not data_df.empty:
        chart_buf = _dark_bar_chart(
            data_df, "Country", "GDP/Capita (USD)",
            "Top 20 Countries by GDP Per Capita",
            color="#10b981", xlabel="GDP/Capita (USD)",
        )
        st.image(chart_buf, caption="Top 20 GDP Per Capita", width=700)

    elif selected == "Stock Exchanges" and not data_df.empty:
        chart_buf = _dark_bar_chart(
            data_df, "Exchange", "Market Cap ($T)",
            "Top 20 Stock Exchanges by Market Cap",
            color="#8b5cf6", xlabel="Market Cap ($T)",
        )
        st.image(chart_buf, caption="Top 20 Exchanges by Market Cap", width=700)

    elif selected == "Sovereign Wealth Funds" and not data_df.empty:
        chart_buf = _dark_bar_chart(
            data_df, "Fund", "AUM ($B)",
            "Top 20 Sovereign Wealth Funds by AUM",
            color="#06b6d4", xlabel="AUM ($B)",
        )
        st.image(chart_buf, caption="Top 20 SWFs by AUM", width=700)

    elif selected == "Container Ports" and not data_df.empty:
        chart_buf = _dark_bar_chart(
            data_df, "Port", "TEU (Millions)",
            "Top 20 Container Ports by TEU Throughput",
            color="#f59e0b", xlabel="TEU (Millions)",
        )
        st.image(chart_buf, caption="Top 20 Container Ports", width=700)

    elif selected == "Oil & Gas Fields" and not data_df.empty:
        chart_buf = _dark_bar_chart(
            data_df, "Field", "Reserves (Bbbl)",
            "Top 20 Oil & Gas Fields by Reserves",
            color="#ef4444", xlabel="Reserves (Billion bbl equiv.)",
        )
        st.image(chart_buf, caption="Top 20 Fields by Reserves", width=700)

    elif selected == "Cryptocurrency Adoption" and not data_df.empty:
        chart_buf = _dark_bar_chart(
            data_df, "Country", "Adoption %",
            "Cryptocurrency Adoption Rates",
            color="#f59e0b", xlabel="Adoption %",
            top_n=25,
        )
        st.image(chart_buf, caption="Crypto Adoption by Country", width=700)

    elif selected == "Economic Corridors" and not data_df.empty:
        chart_buf = _dark_bar_chart(
            data_df, "Corridor", "Investment ($B)",
            "Economic Corridors by Investment",
            color="#ec4899", xlabel="Investment ($B)",
            top_n=10,
        )
        st.image(chart_buf, caption="Corridors by Investment", width=700)

    # --- data table ---
    st.markdown("---")
    st.subheader("Data Table")
    st.dataframe(data_df, width="stretch", height=400)

    # --- download CSV ---
    if not data_df.empty:
        csv_bytes = data_df.to_csv(index=False).encode("utf-8")
        safe_name = selected.lower().replace(" ", "_").replace("&", "and")
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name=f"economics_{safe_name}.csv",
            mime="text/csv",
            key=f"econ_dl_{safe_name}",
        )
