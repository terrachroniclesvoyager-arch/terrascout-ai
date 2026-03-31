# -*- coding: utf-8 -*-
"""
TerraScout AI - Internet & Technology Maps Module
Provides 10 interactive map types covering global technology infrastructure:

    1. Submarine Cables       - Major submarine fiber optic cable systems
    2. Data Centers            - Global cloud/colocation data center hubs
    3. Tech Startup Hubs       - Innovation ecosystems with unicorn counts
    4. Internet Exchange Points - IXPs with peak traffic and member counts
    5. Particle Accelerators   - Colliders, synchrotrons, light sources
    6. Space Agencies          - Government and private space organisations
    7. Nuclear Research        - Fusion tokamaks, stellarators, fission reactors
    8. Supercomputers          - TOP500 ranked HPC systems
    9. Telescope Arrays        - Radio arrays, GW detectors, neutrino observatories
   10. Renewable Tech          - Solar, wind, hydro, geothermal megaprojects

All data sources are free / no API key required.
Uses Overpass API for supplementary nuclear research reactor data.
"""

import html
import json
import math
import requests
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit.components.v1 as components
from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DARK_TILE = "CartoDB dark_matter"
MAP_HEIGHT = 550
FOLIUM_DEFAULT_ZOOM = 2
FOLIUM_DEFAULT_CENTER = [20, 0]

# ---------------------------------------------------------------------------
# Hardcoded data sets
# ---------------------------------------------------------------------------

SUBMARINE_CABLES = [
    {"name": "MAREA", "landing_a": "Virginia Beach, USA", "landing_b": "Bilbao, Spain",
     "coords": [[36.85, -75.98], [43.26, -2.93]], "capacity_tbps": 200, "length_km": 6600,
     "rfs_year": 2018, "owners": "Microsoft, Facebook, Telxius", "color": "#06b6d4"},
    {"name": "Dunant", "landing_a": "Virginia Beach, USA", "landing_b": "Saint-Hilaire-de-Riez, France",
     "coords": [[36.85, -75.98], [46.72, -1.82]], "capacity_tbps": 250, "length_km": 6400,
     "rfs_year": 2020, "owners": "Google", "color": "#22d3ee"},
    {"name": "FASTER", "landing_a": "Oregon, USA", "landing_b": "Chikura, Japan",
     "coords": [[44.63, -124.05], [34.93, 140.0]], "capacity_tbps": 60, "length_km": 11629,
     "rfs_year": 2016, "owners": "Google, China Mobile, KDDI, SingTel", "color": "#67e8f9"},
    {"name": "FLAG Europe-Asia (FEA)", "landing_a": "Porthcurno, UK", "landing_b": "Tokyo, Japan",
     "coords": [[50.04, -5.66], [35.68, 139.69]], "capacity_tbps": 3.84, "length_km": 28000,
     "rfs_year": 1997, "owners": "Reliance Globalcom", "color": "#a78bfa"},
    {"name": "SEA-ME-WE 3", "landing_a": "Norden, Germany", "landing_b": "Okinawa, Japan",
     "coords": [[53.60, 7.20], [26.50, 127.76]], "capacity_tbps": 0.96, "length_km": 39000,
     "rfs_year": 1999, "owners": "Consortium (90+ operators)", "color": "#c084fc"},
    {"name": "SEA-ME-WE 4", "landing_a": "Marseille, France", "landing_b": "Singapore",
     "coords": [[43.30, 5.37], [1.35, 103.82]], "capacity_tbps": 1.28, "length_km": 20000,
     "rfs_year": 2005, "owners": "Consortium (16 operators)", "color": "#e879f9"},
    {"name": "SEA-ME-WE 5", "landing_a": "Marseille, France", "landing_b": "Singapore",
     "coords": [[43.30, 5.37], [1.35, 103.82]], "capacity_tbps": 24, "length_km": 20000,
     "rfs_year": 2017, "owners": "Consortium (18 operators)", "color": "#f472b6"},
    {"name": "SEA-ME-WE 6", "landing_a": "Marseille, France", "landing_b": "Singapore",
     "coords": [[43.30, 5.37], [1.35, 103.82]], "capacity_tbps": 100, "length_km": 19200,
     "rfs_year": 2025, "owners": "Consortium (RFS planned)", "color": "#fb7185"},
    {"name": "TAT-14", "landing_a": "Tuckerton, USA", "landing_b": "Norden, Germany",
     "coords": [[39.60, -74.34], [53.60, 7.20]], "capacity_tbps": 3.2, "length_km": 15428,
     "rfs_year": 2001, "owners": "Consortium", "color": "#fbbf24"},
    {"name": "WACS", "landing_a": "London, UK", "landing_b": "Cape Town, South Africa",
     "coords": [[51.51, -0.13], [-33.92, 18.42]], "capacity_tbps": 14.5, "length_km": 14530,
     "rfs_year": 2012, "owners": "MTN, Vodacom, Tata", "color": "#34d399"},
    {"name": "AAE-1", "landing_a": "Marseille, France", "landing_b": "Hong Kong",
     "coords": [[43.30, 5.37], [22.30, 114.17]], "capacity_tbps": 40, "length_km": 25000,
     "rfs_year": 2017, "owners": "Consortium (19 operators)", "color": "#4ade80"},
    {"name": "AEConnect-1", "landing_a": "New York, USA", "landing_b": "Killala, Ireland",
     "coords": [[40.71, -74.01], [54.21, -9.22]], "capacity_tbps": 52, "length_km": 5536,
     "rfs_year": 2016, "owners": "Aqua Comms", "color": "#2dd4bf"},
    {"name": "PEACE", "landing_a": "Karachi, Pakistan", "landing_b": "Marseille, France",
     "coords": [[24.86, 67.01], [43.30, 5.37]], "capacity_tbps": 96, "length_km": 15000,
     "rfs_year": 2022, "owners": "PEACE Cable International", "color": "#818cf8"},
    {"name": "Equiano", "landing_a": "Lisbon, Portugal", "landing_b": "Cape Town, South Africa",
     "coords": [[38.72, -9.14], [-33.92, 18.42]], "capacity_tbps": 144, "length_km": 15000,
     "rfs_year": 2023, "owners": "Google", "color": "#f97316"},
    {"name": "2Africa", "landing_a": "Multiple (Africa ring)", "landing_b": "Multiple",
     "coords": [[36.75, 3.06], [33.59, -7.62], [14.69, -17.44], [6.13, 1.22],
                 [4.05, 9.77], [-4.27, 15.28], [-8.84, 13.23], [-22.57, 17.08],
                 [-33.92, 18.42], [-25.97, 32.57], [-6.16, 39.19], [2.04, 45.34],
                 [11.59, 43.15], [15.35, 44.21], [21.49, 39.19], [30.04, 31.24],
                 [43.30, 5.37], [51.51, -0.13]],
     "capacity_tbps": 180, "length_km": 45000,
     "rfs_year": 2024, "owners": "Meta, MTN, Vodafone, others", "color": "#ef4444"},
    {"name": "Grace Hopper", "landing_a": "New York, USA", "landing_b": "Bude, UK / Bilbao, Spain",
     "coords": [[40.71, -74.01], [50.83, -4.54], [43.26, -2.93]], "capacity_tbps": 340,
     "length_km": 6200, "rfs_year": 2022, "owners": "Google", "color": "#84cc16"},
    {"name": "JUPITER", "landing_a": "Oregon, USA", "landing_b": "Maruyama, Japan",
     "coords": [[44.63, -124.05], [33.52, 135.38]], "capacity_tbps": 60, "length_km": 14000,
     "rfs_year": 2020, "owners": "Google, Facebook, Amazon", "color": "#06b6d4"},
    {"name": "Havfrue/AEC-2", "landing_a": "New Jersey, USA", "landing_b": "Blaabjerg, Denmark",
     "coords": [[40.10, -74.01], [55.51, 8.15]], "capacity_tbps": 108, "length_km": 7200,
     "rfs_year": 2020, "owners": "Google, Facebook, Aqua Comms", "color": "#a3e635"},
    {"name": "BRUSA", "landing_a": "Virginia Beach, USA", "landing_b": "Fortaleza, Brazil",
     "coords": [[36.85, -75.98], [-3.72, -38.52]], "capacity_tbps": 70, "length_km": 10556,
     "rfs_year": 2018, "owners": "Telxius", "color": "#facc15"},
    {"name": "Monet", "landing_a": "Boca Raton, USA", "landing_b": "Fortaleza, Brazil",
     "coords": [[26.36, -80.08], [-3.72, -38.52]], "capacity_tbps": 64, "length_km": 10556,
     "rfs_year": 2017, "owners": "Google, Antel, Angola Cables", "color": "#fb923c"},
    {"name": "SAex1", "landing_a": "Mtunzini, South Africa", "landing_b": "Fortaleza, Brazil",
     "coords": [[-28.95, 31.77], [-3.72, -38.52]], "capacity_tbps": 12.8, "length_km": 6165,
     "rfs_year": 2018, "owners": "SAex International", "color": "#f87171"},
    {"name": "Asia-America Gateway (AAG)", "landing_a": "Hong Kong", "landing_b": "California, USA",
     "coords": [[22.30, 114.17], [33.72, -118.26]], "capacity_tbps": 2.88, "length_km": 20000,
     "rfs_year": 2009, "owners": "Consortium (19 members)", "color": "#c4b5fd"},
    {"name": "PLCN", "landing_a": "Hong Kong", "landing_b": "California, USA",
     "coords": [[22.30, 114.17], [33.72, -118.26]], "capacity_tbps": 144, "length_km": 12800,
     "rfs_year": 2020, "owners": "Google, Facebook", "color": "#7dd3fc"},
    {"name": "EAC-C2C", "landing_a": "Mumbai, India", "landing_b": "Singapore",
     "coords": [[19.08, 72.88], [1.35, 103.82]], "capacity_tbps": 30, "length_km": 6200,
     "rfs_year": 2019, "owners": "Reliance Jio", "color": "#86efac"},
    {"name": "HIFN", "landing_a": "Hong Kong", "landing_b": "Guam",
     "coords": [[22.30, 114.17], [13.44, 144.79]], "capacity_tbps": 20, "length_km": 3900,
     "rfs_year": 2020, "owners": "RTI/NEC", "color": "#fda4af"},
    {"name": "EllaLink", "landing_a": "Sines, Portugal", "landing_b": "Fortaleza, Brazil",
     "coords": [[37.96, -8.87], [-3.72, -38.52]], "capacity_tbps": 72, "length_km": 6200,
     "rfs_year": 2021, "owners": "EllaLink", "color": "#d946ef"},
    {"name": "SJC", "landing_a": "Hong Kong", "landing_b": "Tokyo, Japan",
     "coords": [[22.30, 114.17], [35.68, 139.69]], "capacity_tbps": 28, "length_km": 8900,
     "rfs_year": 2013, "owners": "Google, KDDI, SingTel, others", "color": "#38bdf8"},
    {"name": "TGN-Atlantic", "landing_a": "New York, USA", "landing_b": "London, UK",
     "coords": [[40.71, -74.01], [51.51, -0.13]], "capacity_tbps": 8, "length_km": 13000,
     "rfs_year": 2001, "owners": "Telia Carrier", "color": "#94a3b8"},
    {"name": "Apollo", "landing_a": "New Jersey, USA", "landing_b": "Cornwall, UK / Brittany, France",
     "coords": [[40.10, -74.01], [50.27, -5.05], [48.64, -3.84]], "capacity_tbps": 3.2,
     "length_km": 13000, "rfs_year": 2003, "owners": "Apollo Submarine Cable System", "color": "#e2e8f0"},
    {"name": "NCP", "landing_a": "Oregon, USA", "landing_b": "Maruyama, Japan",
     "coords": [[44.63, -124.05], [33.52, 135.38]], "capacity_tbps": 72, "length_km": 14500,
     "rfs_year": 2023, "owners": "Google, Meta, others", "color": "#fde047"},
    {"name": "INDIGO-West", "landing_a": "Singapore", "landing_b": "Perth, Australia",
     "coords": [[1.35, 103.82], [-31.95, 115.86]], "capacity_tbps": 18, "length_km": 4600,
     "rfs_year": 2019, "owners": "Google, Indosat, Singtel, SubPartners", "color": "#5eead4"},
    {"name": "Curie", "landing_a": "California, USA", "landing_b": "Valparaiso, Chile",
     "coords": [[33.72, -118.26], [-33.05, -71.61]], "capacity_tbps": 72, "length_km": 10476,
     "rfs_year": 2020, "owners": "Google", "color": "#c084fc"},
]


DATA_CENTERS = [
    {"name": "Ashburn, VA (Data Center Alley)", "lat": 39.04, "lon": -77.49, "operator": "AWS, Equinix, Digital Realty", "capacity_mw": 2500, "country": "USA"},
    {"name": "Dublin, Ireland", "lat": 53.35, "lon": -6.26, "operator": "AWS, Microsoft, Google", "capacity_mw": 900, "country": "Ireland"},
    {"name": "Singapore (Jurong / Tuas)", "lat": 1.35, "lon": 103.82, "operator": "Equinix, Digital Realty, ST Telemedia", "capacity_mw": 700, "country": "Singapore"},
    {"name": "Frankfurt, Germany", "lat": 50.11, "lon": 8.68, "operator": "Equinix, Interxion, DE-CIX", "capacity_mw": 800, "country": "Germany"},
    {"name": "Amsterdam, Netherlands", "lat": 52.37, "lon": 4.90, "operator": "Equinix, Interxion, Digital Realty", "capacity_mw": 600, "country": "Netherlands"},
    {"name": "Tokyo, Japan (Inzai)", "lat": 35.83, "lon": 140.15, "operator": "NTT, Equinix, AWS", "capacity_mw": 550, "country": "Japan"},
    {"name": "London, UK (Slough)", "lat": 51.51, "lon": -0.60, "operator": "Equinix, Telehouse, Digital Realty", "capacity_mw": 750, "country": "UK"},
    {"name": "Dallas/Fort Worth, TX", "lat": 32.90, "lon": -97.04, "operator": "CyrusOne, QTS, Digital Realty", "capacity_mw": 500, "country": "USA"},
    {"name": "Chicago, IL", "lat": 41.88, "lon": -87.63, "operator": "Equinix, Digital Realty, QTS", "capacity_mw": 400, "country": "USA"},
    {"name": "Sydney, Australia", "lat": -33.87, "lon": 151.21, "operator": "Equinix, NextDC, Macquarie", "capacity_mw": 350, "country": "Australia"},
    {"name": "Mumbai, India (Navi Mumbai)", "lat": 19.03, "lon": 73.03, "operator": "NTT, STT GDC, CtrlS", "capacity_mw": 300, "country": "India"},
    {"name": "São Paulo, Brazil", "lat": -23.55, "lon": -46.63, "operator": "Equinix, Ascenty, Odata", "capacity_mw": 250, "country": "Brazil"},
    {"name": "Hong Kong, China", "lat": 22.32, "lon": 114.17, "operator": "Equinix, NTT, SUNeVision", "capacity_mw": 400, "country": "China (HK)"},
    {"name": "Phoenix, AZ", "lat": 33.45, "lon": -112.07, "operator": "CyrusOne, QTS, Stream", "capacity_mw": 450, "country": "USA"},
    {"name": "Northern Virginia (Manassas)", "lat": 38.75, "lon": -77.47, "operator": "AWS, Microsoft Azure", "capacity_mw": 1200, "country": "USA"},
    {"name": "Quincy, WA", "lat": 47.23, "lon": -119.85, "operator": "Microsoft, Yahoo, Sabey", "capacity_mw": 300, "country": "USA"},
    {"name": "Council Bluffs, IA", "lat": 41.26, "lon": -95.86, "operator": "Google, Facebook", "capacity_mw": 350, "country": "USA"},
    {"name": "The Dalles, OR", "lat": 45.60, "lon": -121.18, "operator": "Google", "capacity_mw": 250, "country": "USA"},
    {"name": "Hamina, Finland", "lat": 60.57, "lon": 27.20, "operator": "Google", "capacity_mw": 200, "country": "Finland"},
    {"name": "Luleå, Sweden", "lat": 65.58, "lon": 22.15, "operator": "Facebook", "capacity_mw": 180, "country": "Sweden"},
    {"name": "Paris, France (Pantin)", "lat": 48.90, "lon": 2.40, "operator": "Equinix, Interxion, Scaleway", "capacity_mw": 350, "country": "France"},
    {"name": "Zurich, Switzerland", "lat": 47.38, "lon": 8.54, "operator": "Equinix, Interxion, Green", "capacity_mw": 200, "country": "Switzerland"},
    {"name": "Seoul, South Korea", "lat": 37.57, "lon": 126.98, "operator": "KT, LG CNS, Samsung SDS", "capacity_mw": 300, "country": "South Korea"},
    {"name": "Beijing, China (Zhongguancun)", "lat": 39.98, "lon": 116.31, "operator": "China Telecom, Alibaba, Tencent", "capacity_mw": 500, "country": "China"},
    {"name": "Shanghai, China (Waigaoqiao)", "lat": 31.35, "lon": 121.59, "operator": "China Unicom, Alibaba", "capacity_mw": 400, "country": "China"},
    {"name": "Johannesburg, South Africa", "lat": -26.20, "lon": 28.05, "operator": "Teraco, Africa Data Centres", "capacity_mw": 100, "country": "South Africa"},
    {"name": "Milan, Italy", "lat": 45.46, "lon": 9.19, "operator": "Equinix, Data4, Aruba", "capacity_mw": 200, "country": "Italy"},
    {"name": "Madrid, Spain", "lat": 40.42, "lon": -3.70, "operator": "Equinix, Interxion, Nabiax", "capacity_mw": 180, "country": "Spain"},
    {"name": "Stockholm, Sweden", "lat": 59.33, "lon": 18.07, "operator": "Equinix, Interxion, Bahnhof", "capacity_mw": 150, "country": "Sweden"},
    {"name": "Montreal, Canada", "lat": 45.50, "lon": -73.57, "operator": "OVH, eStruxture, QScale", "capacity_mw": 200, "country": "Canada"},
    {"name": "Toronto, Canada", "lat": 43.65, "lon": -79.38, "operator": "Equinix, Cologix, Rogers", "capacity_mw": 250, "country": "Canada"},
    {"name": "Kuala Lumpur, Malaysia", "lat": 3.14, "lon": 101.69, "operator": "TM, AIMS, Bridge", "capacity_mw": 120, "country": "Malaysia"},
    {"name": "Jakarta, Indonesia", "lat": -6.21, "lon": 106.85, "operator": "NTT, DCI, Telkom", "capacity_mw": 150, "country": "Indonesia"},
    {"name": "Warsaw, Poland", "lat": 52.23, "lon": 21.01, "operator": "Equinix, Atman, Beyond.pl", "capacity_mw": 130, "country": "Poland"},
    {"name": "Oslo, Norway", "lat": 59.91, "lon": 10.75, "operator": "DigiPlex, Basefarm, Green Mountain", "capacity_mw": 140, "country": "Norway"},
    {"name": "Salt Lake City, UT", "lat": 40.76, "lon": -111.89, "operator": "C7, Flexential, DataBank", "capacity_mw": 120, "country": "USA"},
    {"name": "Las Vegas, NV", "lat": 36.17, "lon": -115.14, "operator": "Switch (The Citadel)", "capacity_mw": 650, "country": "USA"},
    {"name": "Reno, NV (Tahoe Reno)", "lat": 39.53, "lon": -119.81, "operator": "Switch, Apple, Google", "capacity_mw": 400, "country": "USA"},
    {"name": "Melbourne, Australia", "lat": -37.81, "lon": 144.96, "operator": "NextDC, Equinix, AirTrunk", "capacity_mw": 200, "country": "Australia"},
    {"name": "Chennai, India", "lat": 13.08, "lon": 80.27, "operator": "CtrlS, Sify, NTT", "capacity_mw": 150, "country": "India"},
    {"name": "Dubai, UAE", "lat": 25.20, "lon": 55.27, "operator": "Khazna, Equinix, Gulf Data Hub", "capacity_mw": 200, "country": "UAE"},
]


TECH_HUBS = [
    {"name": "Silicon Valley", "lat": 37.39, "lon": -122.08, "country": "USA", "unicorns": 140, "funding_b": 120.0, "specialty": "AI, Cloud, SaaS, Hardware"},
    {"name": "New York City", "lat": 40.71, "lon": -74.01, "country": "USA", "unicorns": 65, "funding_b": 55.0, "specialty": "Fintech, Media, AdTech"},
    {"name": "London", "lat": 51.51, "lon": -0.13, "country": "UK", "unicorns": 48, "funding_b": 35.0, "specialty": "Fintech, AI, DeepTech"},
    {"name": "Tel Aviv", "lat": 32.09, "lon": 34.78, "country": "Israel", "unicorns": 35, "funding_b": 25.0, "specialty": "Cybersecurity, AI, DeepTech"},
    {"name": "Berlin", "lat": 52.52, "lon": 13.41, "country": "Germany", "unicorns": 18, "funding_b": 12.0, "specialty": "Mobility, SaaS, Fintech"},
    {"name": "Bangalore", "lat": 12.97, "lon": 77.59, "country": "India", "unicorns": 55, "funding_b": 30.0, "specialty": "SaaS, Fintech, E-commerce"},
    {"name": "Shenzhen", "lat": 22.54, "lon": 114.06, "country": "China", "unicorns": 30, "funding_b": 20.0, "specialty": "Hardware, IoT, 5G"},
    {"name": "Singapore", "lat": 1.35, "lon": 103.82, "country": "Singapore", "unicorns": 20, "funding_b": 15.0, "specialty": "Fintech, Logistics, SEA gateway"},
    {"name": "Stockholm", "lat": 59.33, "lon": 18.07, "country": "Sweden", "unicorns": 12, "funding_b": 8.0, "specialty": "Fintech, Gaming, Music streaming"},
    {"name": "Beijing", "lat": 39.91, "lon": 116.40, "country": "China", "unicorns": 80, "funding_b": 60.0, "specialty": "AI, Autonomous vehicles, E-commerce"},
    {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "country": "China", "unicorns": 50, "funding_b": 35.0, "specialty": "E-commerce, EV, Biotech"},
    {"name": "Seoul", "lat": 37.57, "lon": 126.98, "country": "South Korea", "unicorns": 15, "funding_b": 10.0, "specialty": "Gaming, E-commerce, AI"},
    {"name": "Tokyo", "lat": 35.68, "lon": 139.69, "country": "Japan", "unicorns": 10, "funding_b": 6.0, "specialty": "Robotics, Deep Tech, Mobility"},
    {"name": "Paris", "lat": 48.86, "lon": 2.35, "country": "France", "unicorns": 25, "funding_b": 15.0, "specialty": "AI, SaaS, Marketplace"},
    {"name": "Toronto", "lat": 43.65, "lon": -79.38, "country": "Canada", "unicorns": 12, "funding_b": 8.0, "specialty": "AI/ML, Fintech, Quantum"},
    {"name": "Boston", "lat": 42.36, "lon": -71.06, "country": "USA", "unicorns": 30, "funding_b": 22.0, "specialty": "Biotech, AI, Robotics"},
    {"name": "Los Angeles", "lat": 34.05, "lon": -118.24, "country": "USA", "unicorns": 25, "funding_b": 18.0, "specialty": "SpaceTech, Gaming, Streaming"},
    {"name": "Amsterdam", "lat": 52.37, "lon": 4.90, "country": "Netherlands", "unicorns": 10, "funding_b": 6.0, "specialty": "Booking, Fintech, Deep Tech"},
    {"name": "Dubai", "lat": 25.20, "lon": 55.27, "country": "UAE", "unicorns": 5, "funding_b": 4.0, "specialty": "Fintech, E-commerce, PropTech"},
    {"name": "Sao Paulo", "lat": -23.55, "lon": -46.63, "country": "Brazil", "unicorns": 12, "funding_b": 8.0, "specialty": "Fintech, E-commerce, Logistics"},
    {"name": "Austin, TX", "lat": 30.27, "lon": -97.74, "country": "USA", "unicorns": 15, "funding_b": 10.0, "specialty": "SaaS, Crypto, SpaceTech"},
    {"name": "Seattle", "lat": 47.61, "lon": -122.33, "country": "USA", "unicorns": 20, "funding_b": 15.0, "specialty": "Cloud, AI, E-commerce"},
    {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "country": "India", "unicorns": 18, "funding_b": 10.0, "specialty": "Fintech, EdTech, E-commerce"},
    {"name": "Dublin", "lat": 53.35, "lon": -6.26, "country": "Ireland", "unicorns": 8, "funding_b": 5.0, "specialty": "SaaS, Fintech, EU HQ"},
    {"name": "Jakarta", "lat": -6.21, "lon": 106.85, "country": "Indonesia", "unicorns": 8, "funding_b": 6.0, "specialty": "E-commerce, Ride-hailing, Fintech"},
    {"name": "Nairobi", "lat": -1.29, "lon": 36.82, "country": "Kenya", "unicorns": 3, "funding_b": 2.0, "specialty": "Mobile money, AgriTech, HealthTech"},
    {"name": "Lagos", "lat": 6.52, "lon": 3.38, "country": "Nigeria", "unicorns": 5, "funding_b": 3.0, "specialty": "Fintech, E-commerce, Payments"},
    {"name": "Miami", "lat": 25.76, "lon": -80.19, "country": "USA", "unicorns": 8, "funding_b": 5.0, "specialty": "Crypto, LatAm gateway, Fintech"},
    {"name": "Taipei", "lat": 25.03, "lon": 121.57, "country": "Taiwan", "unicorns": 5, "funding_b": 3.0, "specialty": "Semiconductors, Hardware, IoT"},
    {"name": "Helsinki", "lat": 60.17, "lon": 24.94, "country": "Finland", "unicorns": 6, "funding_b": 3.0, "specialty": "Gaming, CleanTech, Health"},
]


IXP_DATA = [
    {"name": "DE-CIX Frankfurt", "lat": 50.11, "lon": 8.68, "peak_tbps": 17.1, "members": 1100, "country": "Germany", "founded": 1995},
    {"name": "AMS-IX Amsterdam", "lat": 52.37, "lon": 4.90, "peak_tbps": 11.2, "members": 900, "country": "Netherlands", "founded": 1997},
    {"name": "LINX London", "lat": 51.51, "lon": -0.13, "peak_tbps": 6.8, "members": 950, "country": "UK", "founded": 1994},
    {"name": "Equinix Ashburn IX", "lat": 39.04, "lon": -77.49, "peak_tbps": 5.5, "members": 350, "country": "USA", "founded": 2000},
    {"name": "IX.br (PTT.br) Sao Paulo", "lat": -23.55, "lon": -46.63, "peak_tbps": 25.0, "members": 2200, "country": "Brazil", "founded": 2004},
    {"name": "MSK-IX Moscow", "lat": 55.76, "lon": 37.62, "peak_tbps": 4.2, "members": 600, "country": "Russia", "founded": 1995},
    {"name": "JPNAP Tokyo", "lat": 35.68, "lon": 139.69, "peak_tbps": 3.0, "members": 250, "country": "Japan", "founded": 1997},
    {"name": "HKIX Hong Kong", "lat": 22.30, "lon": 114.17, "peak_tbps": 2.5, "members": 280, "country": "China (HK)", "founded": 1997},
    {"name": "NAPAfrica Johannesburg", "lat": -26.20, "lon": 28.05, "peak_tbps": 2.8, "members": 650, "country": "South Africa", "founded": 2012},
    {"name": "France-IX Paris", "lat": 48.86, "lon": 2.35, "peak_tbps": 5.5, "members": 500, "country": "France", "founded": 2010},
    {"name": "SGIX Singapore", "lat": 1.35, "lon": 103.82, "peak_tbps": 1.5, "members": 180, "country": "Singapore", "founded": 2009},
    {"name": "KINX Seoul", "lat": 37.57, "lon": 126.98, "peak_tbps": 2.0, "members": 200, "country": "South Korea", "founded": 2002},
    {"name": "MIX Milan", "lat": 45.46, "lon": 9.19, "peak_tbps": 2.5, "members": 350, "country": "Italy", "founded": 2000},
    {"name": "ESPANIX Madrid", "lat": 40.42, "lon": -3.70, "peak_tbps": 1.2, "members": 130, "country": "Spain", "founded": 1997},
    {"name": "SwissIX Zurich", "lat": 47.38, "lon": 8.54, "peak_tbps": 1.0, "members": 200, "country": "Switzerland", "founded": 2001},
    {"name": "VIX Vienna", "lat": 48.21, "lon": 16.37, "peak_tbps": 0.8, "members": 150, "country": "Austria", "founded": 1996},
    {"name": "NYIIX New York", "lat": 40.71, "lon": -74.01, "peak_tbps": 2.0, "members": 250, "country": "USA", "founded": 1996},
    {"name": "SIX Seattle", "lat": 47.61, "lon": -122.33, "peak_tbps": 1.5, "members": 320, "country": "USA", "founded": 1997},
    {"name": "ECIX Berlin", "lat": 52.52, "lon": 13.41, "peak_tbps": 0.6, "members": 120, "country": "Germany", "founded": 2009},
    {"name": "NetNod Stockholm", "lat": 59.33, "lon": 18.07, "peak_tbps": 2.0, "members": 230, "country": "Sweden", "founded": 1996},
    {"name": "CIXP Geneva", "lat": 46.20, "lon": 6.14, "peak_tbps": 0.3, "members": 80, "country": "Switzerland", "founded": 1997},
    {"name": "TorIX Toronto", "lat": 43.65, "lon": -79.38, "peak_tbps": 1.0, "members": 250, "country": "Canada", "founded": 2001},
    {"name": "UAE-IX Dubai", "lat": 25.20, "lon": 55.27, "peak_tbps": 0.8, "members": 90, "country": "UAE", "founded": 2012},
    {"name": "BBIX Tokyo", "lat": 35.68, "lon": 139.69, "peak_tbps": 3.5, "members": 200, "country": "Japan", "founded": 2013},
    {"name": "DE-CIX Mumbai", "lat": 19.08, "lon": 72.88, "peak_tbps": 1.5, "members": 380, "country": "India", "founded": 2018},
    {"name": "JINX Johannesburg", "lat": -26.20, "lon": 28.05, "peak_tbps": 0.5, "members": 60, "country": "South Africa", "founded": 2002},
    {"name": "QIX Doha", "lat": 25.29, "lon": 51.53, "peak_tbps": 0.2, "members": 30, "country": "Qatar", "founded": 2016},
    {"name": "TWIX Taipei", "lat": 25.03, "lon": 121.57, "peak_tbps": 1.0, "members": 100, "country": "Taiwan", "founded": 1999},
    {"name": "MegaIX Sydney", "lat": -33.87, "lon": 151.21, "peak_tbps": 1.2, "members": 200, "country": "Australia", "founded": 2012},
    {"name": "ArmIX Yerevan", "lat": 40.18, "lon": 44.51, "peak_tbps": 0.1, "members": 25, "country": "Armenia", "founded": 2009},
    {"name": "CATNIX Barcelona", "lat": 41.39, "lon": 2.17, "peak_tbps": 0.3, "members": 50, "country": "Spain", "founded": 2003},
]


PARTICLE_ACCELERATORS = [
    {"name": "CERN LHC", "lat": 46.23, "lon": 6.05, "country": "Switzerland/France",
     "circumference_km": 26.7, "energy_gev": 6500, "type": "Proton Synchrotron",
     "experiments": "ATLAS, CMS, ALICE, LHCb", "status": "Operational"},
    {"name": "Fermilab (Tevatron)", "lat": 41.83, "lon": -88.27, "country": "USA",
     "circumference_km": 6.28, "energy_gev": 980, "type": "Proton-Antiproton Synchrotron",
     "experiments": "CDF, D0, NOvA, Muon g-2", "status": "Tevatron retired; neutrino ops active"},
    {"name": "SLAC National Accelerator Lab", "lat": 37.42, "lon": -122.20, "country": "USA",
     "circumference_km": 3.2, "energy_gev": 50, "type": "Linear Accelerator (LCLS-II)",
     "experiments": "LCLS-II X-ray FEL", "status": "Operational"},
    {"name": "DESY (Hamburg)", "lat": 53.58, "lon": 9.88, "country": "Germany",
     "circumference_km": 6.3, "energy_gev": 920, "type": "Electron-Proton (HERA, retired)",
     "experiments": "European XFEL, PETRA III", "status": "XFEL / PETRA III operational"},
    {"name": "KEK (Tsukuba)", "lat": 36.15, "lon": 140.08, "country": "Japan",
     "circumference_km": 3.0, "energy_gev": 7, "type": "Electron-Positron (SuperKEKB)",
     "experiments": "Belle II", "status": "Operational"},
    {"name": "IHEP Beijing (BEPC II)", "lat": 39.98, "lon": 116.31, "country": "China",
     "circumference_km": 0.24, "energy_gev": 2.3, "type": "Electron-Positron Collider",
     "experiments": "BES III", "status": "Operational"},
    {"name": "JINR Dubna", "lat": 56.75, "lon": 37.19, "country": "Russia",
     "circumference_km": 0.05, "energy_gev": 6, "type": "Heavy Ion (NICA)",
     "experiments": "NICA/MPD", "status": "NICA commissioning"},
    {"name": "Brookhaven RHIC", "lat": 40.87, "lon": -72.89, "country": "USA",
     "circumference_km": 3.83, "energy_gev": 255, "type": "Heavy Ion Collider",
     "experiments": "STAR, sPHENIX", "status": "Operational"},
    {"name": "GSI / FAIR Darmstadt", "lat": 49.93, "lon": 8.67, "country": "Germany",
     "circumference_km": 1.1, "energy_gev": 29, "type": "Heavy Ion (FAIR under construction)",
     "experiments": "CBM, PANDA, NUSTAR", "status": "FAIR under construction"},
    {"name": "J-PARC Tokai", "lat": 36.46, "lon": 140.60, "country": "Japan",
     "circumference_km": 1.57, "energy_gev": 50, "type": "Proton Synchrotron",
     "experiments": "T2K, SuperKamiokande link", "status": "Operational"},
    {"name": "TRIUMF Vancouver", "lat": 49.25, "lon": -123.23, "country": "Canada",
     "circumference_km": 0.05, "energy_gev": 0.52, "type": "Cyclotron",
     "experiments": "ISAC, ARIEL", "status": "Operational"},
    {"name": "PSI Villigen", "lat": 47.54, "lon": 8.23, "country": "Switzerland",
     "circumference_km": 0.01, "energy_gev": 0.59, "type": "Cyclotron / SLS",
     "experiments": "Swiss Light Source, SwissFEL", "status": "Operational"},
    {"name": "Australian Synchrotron (Melbourne)", "lat": -37.91, "lon": 145.14, "country": "Australia",
     "circumference_km": 0.22, "energy_gev": 3, "type": "Synchrotron Light Source",
     "experiments": "Beamlines for materials, bio", "status": "Operational"},
    {"name": "ESRF Grenoble", "lat": 45.21, "lon": 5.69, "country": "France",
     "circumference_km": 0.84, "energy_gev": 6, "type": "Synchrotron Radiation Facility",
     "experiments": "44 beamlines", "status": "EBS upgrade operational"},
    {"name": "Diamond Light Source (Harwell)", "lat": 51.57, "lon": -1.32, "country": "UK",
     "circumference_km": 0.56, "energy_gev": 3, "type": "Synchrotron Light Source",
     "experiments": "33 beamlines", "status": "Operational"},
    {"name": "SESAME (Allan, Jordan)", "lat": 32.09, "lon": 35.73, "country": "Jordan",
     "circumference_km": 0.13, "energy_gev": 2.5, "type": "Synchrotron Light Source",
     "experiments": "Middle East science diplomacy", "status": "Operational"},
]


SPACE_AGENCIES = [
    {"name": "NASA", "lat": 38.88, "lon": -77.02, "country": "USA", "budget_b": 25.4, "hq": "Washington DC", "active_missions": 80, "founded": 1958},
    {"name": "ESA", "lat": 48.85, "lon": 2.35, "country": "Europe (22 members)", "budget_b": 7.8, "hq": "Paris, France", "active_missions": 25, "founded": 1975},
    {"name": "Roscosmos", "lat": 55.76, "lon": 37.62, "country": "Russia", "budget_b": 3.5, "hq": "Moscow, Russia", "active_missions": 15, "founded": 1992},
    {"name": "JAXA", "lat": 36.05, "lon": 140.13, "country": "Japan", "budget_b": 1.5, "hq": "Tsukuba, Japan", "active_missions": 12, "founded": 2003},
    {"name": "ISRO", "lat": 12.97, "lon": 77.57, "country": "India", "budget_b": 1.8, "hq": "Bangalore, India", "active_missions": 18, "founded": 1969},
    {"name": "CNSA", "lat": 39.91, "lon": 116.40, "country": "China", "budget_b": 12.0, "hq": "Beijing, China", "active_missions": 30, "founded": 1993},
    {"name": "CSA", "lat": 45.52, "lon": -73.39, "country": "Canada", "budget_b": 0.4, "hq": "Longueuil, Canada", "active_missions": 5, "founded": 1989},
    {"name": "DLR", "lat": 50.86, "lon": 7.12, "country": "Germany", "budget_b": 3.0, "hq": "Cologne, Germany", "active_missions": 8, "founded": 1969},
    {"name": "CNES", "lat": 48.84, "lon": 2.37, "country": "France", "budget_b": 3.2, "hq": "Paris, France", "active_missions": 10, "founded": 1961},
    {"name": "ASI", "lat": 41.83, "lon": 12.67, "country": "Italy", "budget_b": 2.0, "hq": "Rome, Italy", "active_missions": 6, "founded": 1988},
    {"name": "UKSA", "lat": 51.88, "lon": -2.24, "country": "UK", "budget_b": 0.8, "hq": "Swindon, UK", "active_missions": 4, "founded": 2010},
    {"name": "SpaceX", "lat": 33.92, "lon": -118.33, "country": "USA (Private)", "budget_b": 5.0, "hq": "Hawthorne, CA", "active_missions": 40, "founded": 2002},
    {"name": "Blue Origin", "lat": 47.62, "lon": -122.35, "country": "USA (Private)", "budget_b": 2.5, "hq": "Kent, WA", "active_missions": 3, "founded": 2000},
    {"name": "KARI", "lat": 36.37, "lon": 127.36, "country": "South Korea", "budget_b": 0.7, "hq": "Daejeon, South Korea", "active_missions": 5, "founded": 1989},
    {"name": "SUPARCO", "lat": 24.86, "lon": 67.01, "country": "Pakistan", "budget_b": 0.05, "hq": "Karachi, Pakistan", "active_missions": 2, "founded": 1961},
    {"name": "AEB (Brazil)", "lat": -15.79, "lon": -47.88, "country": "Brazil", "budget_b": 0.1, "hq": "Brasilia, Brazil", "active_missions": 3, "founded": 1994},
    {"name": "SSA (Saudi Arabia)", "lat": 24.71, "lon": 46.67, "country": "Saudi Arabia", "budget_b": 2.5, "hq": "Riyadh, Saudi Arabia", "active_missions": 2, "founded": 2018},
    {"name": "UAESA", "lat": 25.20, "lon": 55.27, "country": "UAE", "budget_b": 1.5, "hq": "Abu Dhabi, UAE", "active_missions": 3, "founded": 2014},
    {"name": "Rocket Lab", "lat": -41.29, "lon": 174.78, "country": "NZ/USA (Private)", "budget_b": 0.3, "hq": "Long Beach CA / Auckland NZ", "active_missions": 10, "founded": 2006},
    {"name": "CONAE (Argentina)", "lat": -34.60, "lon": -58.38, "country": "Argentina", "budget_b": 0.06, "hq": "Buenos Aires", "active_missions": 4, "founded": 1991},
]


NUCLEAR_RESEARCH = [
    {"name": "ITER (Tokamak)", "lat": 43.71, "lon": 5.76, "country": "France", "type": "Fusion Tokamak", "status": "Under construction", "energy_output": "500 MW (planned)", "desc": "International thermonuclear experimental reactor, 35 nations"},
    {"name": "NIF (National Ignition Facility)", "lat": 37.69, "lon": -121.70, "country": "USA", "type": "Inertial Confinement Fusion", "status": "Operational", "energy_output": "3.15 MJ achieved", "desc": "Lawrence Livermore, achieved fusion ignition Dec 2022"},
    {"name": "JET (Joint European Torus)", "lat": 51.66, "lon": -1.23, "country": "UK", "type": "Fusion Tokamak", "status": "Decommissioning", "energy_output": "69 MJ record", "desc": "Culham Centre, world record fusion energy 2022"},
    {"name": "EAST (Experimental Advanced Superconducting Tokamak)", "lat": 31.84, "lon": 117.27, "country": "China", "type": "Fusion Tokamak", "status": "Operational", "energy_output": "1056s plasma record", "desc": "Hefei, longest sustained plasma operation"},
    {"name": "Wendelstein 7-X", "lat": 54.08, "lon": 13.43, "country": "Germany", "type": "Stellarator (Fusion)", "status": "Operational", "energy_output": "Experimental", "desc": "Greifswald, worlds largest stellarator"},
    {"name": "KSTAR (Korea Superconducting Tokamak)", "lat": 36.44, "lon": 127.13, "country": "South Korea", "type": "Fusion Tokamak", "status": "Operational", "energy_output": "100M deg plasma", "desc": "Daejeon, 48-second plasma @ 100M degrees C"},
    {"name": "DEMO (EU Fusion Power Plant)", "lat": 43.71, "lon": 5.76, "country": "EU", "type": "Fusion (planned)", "status": "Design phase", "energy_output": "2 GW (planned)", "desc": "Post-ITER demonstration power plant"},
    {"name": "SPARC (MIT/CFS)", "lat": 42.46, "lon": -71.27, "country": "USA", "type": "Compact Fusion Tokamak", "status": "Under construction", "energy_output": "140 MW (planned)", "desc": "Commonwealth Fusion Systems, HTS magnets"},
    {"name": "Oak Ridge HFIR", "lat": 35.93, "lon": -84.31, "country": "USA", "type": "Research Reactor (Fission)", "status": "Operational", "energy_output": "85 MW thermal", "desc": "High Flux Isotope Reactor, neutron science"},
    {"name": "ILL Grenoble", "lat": 45.21, "lon": 5.69, "country": "France", "type": "Research Reactor (Fission)", "status": "Operational", "energy_output": "58.3 MW thermal", "desc": "Institut Laue-Langevin, neutron research"},
    {"name": "ANSTO OPAL (Sydney)", "lat": -34.05, "lon": 151.01, "country": "Australia", "type": "Research Reactor (Fission)", "status": "Operational", "energy_output": "20 MW thermal", "desc": "Open Pool Australian Lightwater reactor"},
    {"name": "PIK Reactor (Gatchina)", "lat": 59.56, "lon": 30.12, "country": "Russia", "type": "Research Reactor (Fission)", "status": "Commissioning", "energy_output": "100 MW thermal", "desc": "Highest flux research reactor in Russia"},
    {"name": "JMTR (Oarai)", "lat": 36.44, "lon": 140.58, "country": "Japan", "type": "Research Reactor (Fission)", "status": "Decommissioning", "energy_output": "50 MW thermal", "desc": "Japan Materials Testing Reactor"},
    {"name": "HL-2M Tokamak (Chengdu)", "lat": 30.57, "lon": 104.07, "country": "China", "type": "Fusion Tokamak", "status": "Operational", "energy_output": "2.5 MA plasma", "desc": "Chinese artificial sun, 150 million degrees"},
    {"name": "SST-1 (IPR Gandhinagar)", "lat": 23.19, "lon": 72.63, "country": "India", "type": "Fusion Tokamak", "status": "Operational", "energy_output": "Experimental", "desc": "Indias first superconducting tokamak"},
    {"name": "JT-60SA (Naka)", "lat": 36.45, "lon": 140.48, "country": "Japan", "type": "Fusion Tokamak", "status": "First plasma 2023", "energy_output": "41 MW heating", "desc": "Largest superconducting tokamak before ITER"},
    {"name": "Cadarache CEA", "lat": 43.69, "lon": 5.77, "country": "France", "type": "Nuclear Research Center", "status": "Operational", "energy_output": "Multiple reactors", "desc": "CEA campus hosting ITER and research reactors"},
    {"name": "Idaho National Laboratory", "lat": 43.52, "lon": -112.94, "country": "USA", "type": "Nuclear Research Center", "status": "Operational", "energy_output": "52 reactors (historical)", "desc": "US DOE lab, SMR development, EBR-I first nuclear electricity"},
    {"name": "Chalk River Laboratories", "lat": 46.05, "lon": -77.36, "country": "Canada", "type": "Research Reactor (Fission)", "status": "Operational", "energy_output": "NRU retired, NRX historical", "desc": "AECL/CNL, birthplace of CANDU technology"},
    {"name": "TAE Technologies (Foothill Ranch)", "lat": 33.69, "lon": -117.66, "country": "USA", "type": "Compact Fusion (FRC)", "status": "Development", "energy_output": "Experimental", "desc": "Field-reversed configuration approach to fusion"},
]


SUPERCOMPUTERS = [
    {"name": "Frontier", "lat": 35.93, "lon": -84.31, "location": "Oak Ridge, TN, USA", "flops_pflops": 1194.0, "cores": 8730112, "power_mw": 22.7, "vendor": "HPE/AMD", "year": 2022},
    {"name": "Aurora", "lat": 41.72, "lon": -87.98, "location": "Argonne, IL, USA", "flops_pflops": 1012.0, "cores": 9264128, "power_mw": 24.7, "vendor": "Intel/HPE", "year": 2024},
    {"name": "Eagle (Microsoft Azure)", "lat": 47.64, "lon": -122.13, "location": "Redmond, WA, USA", "flops_pflops": 561.2, "cores": 2073600, "power_mw": 12.0, "vendor": "Microsoft/NVIDIA", "year": 2023},
    {"name": "Fugaku", "lat": 34.66, "lon": 135.22, "location": "Kobe, Japan", "flops_pflops": 442.0, "cores": 7630848, "power_mw": 29.9, "vendor": "Fujitsu/ARM", "year": 2021},
    {"name": "LUMI", "lat": 65.06, "lon": 25.47, "location": "Kajaani, Finland", "flops_pflops": 379.7, "cores": 2220288, "power_mw": 6.0, "vendor": "HPE/AMD", "year": 2022},
    {"name": "Leonardo", "lat": 44.51, "lon": 11.33, "location": "Bologna, Italy", "flops_pflops": 238.7, "cores": 1824768, "power_mw": 7.4, "vendor": "Atos/NVIDIA", "year": 2022},
    {"name": "Summit", "lat": 35.93, "lon": -84.31, "location": "Oak Ridge, TN, USA", "flops_pflops": 148.8, "cores": 2414592, "power_mw": 10.1, "vendor": "IBM/NVIDIA", "year": 2018},
    {"name": "Sierra", "lat": 37.69, "lon": -121.70, "location": "Livermore, CA, USA", "flops_pflops": 94.6, "cores": 1572480, "power_mw": 7.4, "vendor": "IBM/NVIDIA", "year": 2018},
    {"name": "Sunway TaihuLight", "lat": 31.60, "lon": 120.74, "location": "Wuxi, China", "flops_pflops": 93.0, "cores": 10649600, "power_mw": 15.4, "vendor": "NRCPC/Sunway", "year": 2016},
    {"name": "Perlmutter", "lat": 37.88, "lon": -122.25, "location": "Berkeley, CA, USA", "flops_pflops": 70.9, "cores": 761856, "power_mw": 2.6, "vendor": "HPE/NVIDIA", "year": 2021},
    {"name": "Selene", "lat": 47.64, "lon": -122.13, "location": "Santa Clara, CA, USA", "flops_pflops": 63.5, "cores": 555520, "power_mw": 2.6, "vendor": "NVIDIA DGX", "year": 2020},
    {"name": "Tianhe-2A", "lat": 23.13, "lon": 113.26, "location": "Guangzhou, China", "flops_pflops": 61.4, "cores": 4981760, "power_mw": 18.5, "vendor": "NUDT/Phytium", "year": 2018},
    {"name": "JUWELS Booster", "lat": 50.91, "lon": 6.36, "location": "Julich, Germany", "flops_pflops": 44.1, "cores": 449280, "power_mw": 1.8, "vendor": "Atos/NVIDIA", "year": 2020},
    {"name": "HPC5 (Eni)", "lat": 45.46, "lon": 9.19, "location": "Ferrera Erbognone, Italy", "flops_pflops": 35.5, "cores": 669760, "power_mw": 3.0, "vendor": "Dell/NVIDIA", "year": 2020},
    {"name": "Dammam-7 (Aramco)", "lat": 26.43, "lon": 50.10, "location": "Dhahran, Saudi Arabia", "flops_pflops": 22.4, "cores": 590000, "power_mw": 3.5, "vendor": "HPE/AMD", "year": 2022},
    {"name": "Polaris", "lat": 41.72, "lon": -87.98, "location": "Argonne, IL, USA", "flops_pflops": 44.0, "cores": 358400, "power_mw": 2.5, "vendor": "HPE/NVIDIA", "year": 2022},
    {"name": "MareNostrum 5", "lat": 41.39, "lon": 2.12, "location": "Barcelona, Spain", "flops_pflops": 314.0, "cores": 1120000, "power_mw": 6.0, "vendor": "Atos/NVIDIA/Intel", "year": 2024},
    {"name": "Alps", "lat": 46.95, "lon": 7.45, "location": "Lugano, Switzerland", "flops_pflops": 270.0, "cores": 1300000, "power_mw": 5.5, "vendor": "HPE/NVIDIA", "year": 2024},
    {"name": "Deucalion", "lat": 41.15, "lon": -8.61, "location": "Guimaraes, Portugal", "flops_pflops": 10.0, "cores": 150000, "power_mw": 0.9, "vendor": "Atos/NVIDIA", "year": 2023},
    {"name": "Snellius", "lat": 52.36, "lon": 4.95, "location": "Amsterdam, Netherlands", "flops_pflops": 14.0, "cores": 175000, "power_mw": 1.2, "vendor": "Lenovo/AMD/NVIDIA", "year": 2021},
]


TELESCOPE_ARRAYS = [
    {"name": "Very Large Array (VLA)", "lat": 34.08, "lon": -107.62, "country": "USA (New Mexico)", "type": "Radio interferometer", "dishes": "27 x 25m dishes", "frequency": "1-50 GHz", "purpose": "Radio astronomy, imaging"},
    {"name": "ALMA", "lat": -23.02, "lon": -67.75, "country": "Chile (Atacama)", "type": "Millimeter/submillimeter", "dishes": "66 antennas (12m/7m)", "frequency": "84-950 GHz", "purpose": "Cold universe, planet formation"},
    {"name": "SKA-Low (Murchison)", "lat": -26.70, "lon": 116.67, "country": "Australia (WA)", "type": "Low-freq radio array", "dishes": "131,072 dipole antennas", "frequency": "50-350 MHz", "purpose": "Epoch of reionization, cosmology"},
    {"name": "SKA-Mid (Karoo)", "lat": -30.72, "lon": 21.44, "country": "South Africa", "type": "Mid-freq radio array", "dishes": "197 x 15m dishes", "frequency": "350 MHz - 15.4 GHz", "purpose": "Pulsars, HI surveys, cosmology"},
    {"name": "LOFAR", "lat": 52.91, "lon": 6.87, "country": "Netherlands (EU-wide)", "type": "Low-freq radio array", "dishes": "52 stations across Europe", "frequency": "10-240 MHz", "purpose": "Epoch of reionization, transients"},
    {"name": "MeerKAT", "lat": -30.72, "lon": 21.44, "country": "South Africa", "type": "Radio interferometer", "dishes": "64 x 13.5m dishes", "frequency": "580 MHz - 14.5 GHz", "purpose": "SKA precursor, HI surveys"},
    {"name": "CHIME", "lat": 49.32, "lon": -119.62, "country": "Canada (BC)", "type": "Cylindrical radio telescope", "dishes": "4 x 100m cylinders", "frequency": "400-800 MHz", "purpose": "Fast radio bursts, BAO cosmology"},
    {"name": "IceCube Neutrino Observatory", "lat": -89.99, "lon": 0.0, "country": "South Pole, Antarctica", "type": "Neutrino detector", "dishes": "5,160 DOMs in ice", "frequency": "TeV-PeV neutrinos", "purpose": "Neutrino astronomy, dark matter"},
    {"name": "LIGO Hanford", "lat": 46.46, "lon": -119.41, "country": "USA (Washington)", "type": "Gravitational wave detector", "dishes": "4 km L-shaped arms", "frequency": "10-7000 Hz", "purpose": "Gravitational wave detection"},
    {"name": "LIGO Livingston", "lat": 30.56, "lon": -90.77, "country": "USA (Louisiana)", "type": "Gravitational wave detector", "dishes": "4 km L-shaped arms", "frequency": "10-7000 Hz", "purpose": "Gravitational wave detection"},
    {"name": "Virgo", "lat": 43.63, "lon": 10.50, "country": "Italy (Cascina)", "type": "Gravitational wave detector", "dishes": "3 km L-shaped arms", "frequency": "10-10000 Hz", "purpose": "Gravitational wave detection"},
    {"name": "KAGRA", "lat": 36.43, "lon": 137.31, "country": "Japan (Kamioka)", "type": "Gravitational wave detector", "dishes": "3 km underground arms", "frequency": "10-7000 Hz", "purpose": "Gravitational wave detection"},
    {"name": "FAST (Tianyan)", "lat": 25.65, "lon": 106.86, "country": "China (Guizhou)", "type": "Single dish radio telescope", "dishes": "500m aperture dish", "frequency": "70 MHz - 3 GHz", "purpose": "Pulsars, SETI, HI surveys"},
    {"name": "Arecibo (collapsed 2020)", "lat": 18.35, "lon": -66.75, "country": "Puerto Rico, USA", "type": "Single dish (destroyed)", "dishes": "305m dish (collapsed)", "frequency": "Historical", "purpose": "SETI, radar, pulsars (historical)"},
    {"name": "GMRT", "lat": 19.10, "lon": 74.05, "country": "India (Pune)", "type": "Radio interferometer", "dishes": "30 x 45m dishes", "frequency": "150-1500 MHz", "purpose": "Pulsars, galaxy surveys"},
    {"name": "NOEMA", "lat": 44.63, "lon": 5.91, "country": "France (Bure)", "type": "Millimeter interferometer", "dishes": "12 x 15m antennas", "frequency": "72-373 GHz", "purpose": "Cold gas, high-z galaxies"},
    {"name": "CTA South (Paranal)", "lat": -24.68, "lon": -70.32, "country": "Chile", "type": "Cherenkov gamma-ray", "dishes": "51 telescopes planned", "frequency": "20 GeV - 300 TeV", "purpose": "Gamma-ray astronomy"},
    {"name": "CTA North (La Palma)", "lat": 28.76, "lon": -17.89, "country": "Spain (Canary Islands)", "type": "Cherenkov gamma-ray", "dishes": "13 telescopes planned", "frequency": "20 GeV - 300 TeV", "purpose": "Gamma-ray astronomy"},
    {"name": "Pierre Auger Observatory", "lat": -35.47, "lon": -69.58, "country": "Argentina (Malargue)", "type": "Cosmic ray detector", "dishes": "1660 water Cherenkov tanks", "frequency": ">10^18 eV cosmic rays", "purpose": "Ultra-high energy cosmic rays"},
    {"name": "Event Horizon Telescope (coordinated)", "lat": 19.82, "lon": -155.47, "country": "Global VLBI", "type": "Global VLBI network", "dishes": "11 stations worldwide", "frequency": "230 GHz", "purpose": "Black hole imaging (M87*, Sgr A*)"},
]


RENEWABLE_MEGAPROJECTS = [
    {"name": "Three Gorges Dam", "lat": 30.82, "lon": 111.00, "country": "China", "type": "Hydroelectric", "capacity_gw": 22.5, "cost_b": 31.0, "status": "Operational since 2006", "desc": "Worlds largest power station by capacity"},
    {"name": "Bhadla Solar Park", "lat": 27.55, "lon": 71.91, "country": "India", "type": "Solar PV", "capacity_gw": 2.25, "cost_b": 1.4, "status": "Operational", "desc": "Worlds largest solar park, Rajasthan desert"},
    {"name": "Gansu Wind Farm", "lat": 40.75, "lon": 96.00, "country": "China", "type": "Onshore Wind", "capacity_gw": 20.0, "cost_b": 17.0, "status": "Operational / expanding", "desc": "Worlds largest wind farm complex, Gobi desert"},
    {"name": "Hornsea Wind Farm (1+2+3)", "lat": 53.88, "lon": 1.79, "country": "UK", "type": "Offshore Wind", "capacity_gw": 3.88, "cost_b": 15.0, "status": "H1+H2 operational, H3 construction", "desc": "Worlds largest offshore wind farm complex"},
    {"name": "NEOM The Line Solar", "lat": 28.00, "lon": 35.00, "country": "Saudi Arabia", "type": "Solar + Wind", "capacity_gw": 5.0, "cost_b": 5.0, "status": "Under construction", "desc": "Part of NEOM megacity green energy plan"},
    {"name": "Itaipu Dam", "lat": -25.41, "lon": -54.59, "country": "Brazil/Paraguay", "type": "Hydroelectric", "capacity_gw": 14.0, "cost_b": 19.6, "status": "Operational since 1984", "desc": "Second largest hydro, highest annual generation for decades"},
    {"name": "Dogger Bank Wind Farm", "lat": 54.75, "lon": 2.25, "country": "UK", "type": "Offshore Wind", "capacity_gw": 3.6, "cost_b": 12.0, "status": "Under construction", "desc": "Will be worlds largest offshore wind farm"},
    {"name": "Noor-Ouarzazate Solar Complex", "lat": 31.05, "lon": -6.86, "country": "Morocco", "type": "CSP + Solar PV", "capacity_gw": 0.58, "cost_b": 2.5, "status": "Operational", "desc": "Worlds largest CSP plant, Sahara edge"},
    {"name": "Tengger Desert Solar Park", "lat": 37.50, "lon": 104.95, "country": "China", "type": "Solar PV", "capacity_gw": 1.55, "cost_b": 1.1, "status": "Operational", "desc": "Nicknamed Great Wall of Solar"},
    {"name": "Baihetan Dam", "lat": 27.79, "lon": 102.90, "country": "China", "type": "Hydroelectric", "capacity_gw": 16.0, "cost_b": 34.0, "status": "Operational since 2022", "desc": "Second largest hydro dam in China"},
    {"name": "Walney Extension", "lat": 54.05, "lon": -3.55, "country": "UK", "type": "Offshore Wind", "capacity_gw": 0.66, "cost_b": 1.6, "status": "Operational since 2018", "desc": "Major Irish Sea offshore wind farm"},
    {"name": "Al Dhafra Solar (Abu Dhabi)", "lat": 23.80, "lon": 55.00, "country": "UAE", "type": "Solar PV", "capacity_gw": 2.0, "cost_b": 1.0, "status": "Operational 2023", "desc": "Worlds largest single-site solar at commissioning"},
    {"name": "Vineyard Wind 1", "lat": 41.19, "lon": -70.54, "country": "USA", "type": "Offshore Wind", "capacity_gw": 0.80, "cost_b": 4.0, "status": "Under construction", "desc": "First large-scale US offshore wind farm"},
    {"name": "Guri Dam", "lat": 7.77, "lon": -63.00, "country": "Venezuela", "type": "Hydroelectric", "capacity_gw": 10.24, "cost_b": 5.0, "status": "Operational since 1978", "desc": "Powers ~65% of Venezuelas electricity"},
    {"name": "Topaz Solar Farm", "lat": 35.38, "lon": -119.93, "country": "USA", "type": "Solar PV", "capacity_gw": 0.55, "cost_b": 2.5, "status": "Operational since 2014", "desc": "Major US utility-scale solar in California"},
    {"name": "London Array", "lat": 51.63, "lon": 1.35, "country": "UK", "type": "Offshore Wind", "capacity_gw": 0.63, "cost_b": 3.0, "status": "Operational since 2013", "desc": "Thames Estuary offshore wind farm"},
    {"name": "Middelgrunden", "lat": 55.69, "lon": 12.67, "country": "Denmark", "type": "Offshore Wind", "capacity_gw": 0.04, "cost_b": 0.06, "status": "Operational since 2000", "desc": "Pioneering offshore wind farm near Copenhagen"},
    {"name": "Olkaria Geothermal", "lat": -0.88, "lon": 36.30, "country": "Kenya", "type": "Geothermal", "capacity_gw": 0.86, "cost_b": 1.5, "status": "Operational / expanding", "desc": "Largest geothermal complex in Africa, Rift Valley"},
    {"name": "Hellisheidi Geothermal", "lat": 64.04, "lon": -21.40, "country": "Iceland", "type": "Geothermal", "capacity_gw": 0.30, "cost_b": 0.4, "status": "Operational since 2006", "desc": "Third largest geothermal power station in the world"},
    {"name": "Grand Inga Dam (planned)", "lat": -5.52, "lon": 13.62, "country": "DR Congo", "type": "Hydroelectric (planned)", "capacity_gw": 39.0, "cost_b": 80.0, "status": "Planned", "desc": "Would be worlds largest dam if completed, Congo River"},
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _make_dark_map(center=None, zoom=None):
    """Create a folium map with CartoDB dark_matter tiles."""
    if center is None:
        center = FOLIUM_DEFAULT_CENTER
    if zoom is None:
        zoom = FOLIUM_DEFAULT_ZOOM
    m = folium.Map(location=center, zoom_start=zoom, tiles=DARK_TILE,
                   width="100%", height=MAP_HEIGHT)
    return m


def _render_folium(m):
    """Render a folium map inside Streamlit."""
    components.html(m._repr_html_(), height=MAP_HEIGHT)


def _dark_chart():
    """Return (fig, ax) with dark theme styling."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.tick_params(colors="#8b97b0")
    ax.xaxis.label.set_color("#e8ecf4")
    ax.yaxis.label.set_color("#e8ecf4")
    ax.title.set_color("#e8ecf4")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax


def _safe(text):
    """HTML-escape user content."""
    if text is None:
        return ""
    return html.escape(str(text))


# ---------------------------------------------------------------------------
# Map renderers
# ---------------------------------------------------------------------------

def _render_submarine_cables():
    """Map 1: Submarine fiber optic cables."""
    st.markdown("#### Submarine Fiber Optic Cables")
    st.caption("Major international submarine cable systems with landing points, capacity, and ownership.")

    col1, col2 = st.columns([1, 1])
    with col1:
        min_year = st.slider("Minimum RFS year", 1990, 2025, 1990, key="cable_year")
    with col2:
        min_cap = st.slider("Minimum capacity (Tbps)", 0, 300, 0, key="cable_cap")

    filtered = [c for c in SUBMARINE_CABLES if c["rfs_year"] >= min_year and c["capacity_tbps"] >= min_cap]
    st.info(f"Showing **{len(filtered)}** of {len(SUBMARINE_CABLES)} cables")

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total cables", len(filtered))
    total_cap = sum(c["capacity_tbps"] for c in filtered)
    c2.metric("Total capacity", f"{total_cap:.0f} Tbps")
    total_len = sum(c["length_km"] for c in filtered)
    c3.metric("Total length", f"{total_len:,.0f} km")
    avg_year = sum(c["rfs_year"] for c in filtered) / max(1, len(filtered))
    c4.metric("Avg RFS year", f"{avg_year:.0f}")

    # Map
    m = _make_dark_map()
    for cable in filtered:
        coords = cable["coords"]
        popup_html = (
            f"<b>{_safe(cable['name'])}</b><br>"
            f"Capacity: {cable['capacity_tbps']} Tbps<br>"
            f"Length: {cable['length_km']:,} km<br>"
            f"RFS: {cable['rfs_year']}<br>"
            f"Owners: {_safe(cable['owners'])}<br>"
            f"{_safe(cable['landing_a'])} &harr; {_safe(cable['landing_b'])}"
        )
        folium.PolyLine(
            coords, color=cable.get("color", "#06b6d4"),
            weight=3, opacity=0.8, popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
        # Landing point markers
        for pt in [coords[0], coords[-1]]:
            folium.CircleMarker(
                pt, radius=4, color=cable.get("color", "#06b6d4"),
                fill=True, fill_opacity=0.9
            ).add_to(m)
    _render_folium(m)

    # Chart - top cables by capacity
    fig, ax = _dark_chart()
    sorted_cables = sorted(filtered, key=lambda x: x["capacity_tbps"], reverse=True)[:15]
    names = [c["name"] for c in sorted_cables]
    caps = [c["capacity_tbps"] for c in sorted_cables]
    bars = ax.barh(names[::-1], caps[::-1], color="#06b6d4", edgecolor="#0e7490")
    ax.set_xlabel("Capacity (Tbps)")
    ax.set_title("Top Submarine Cables by Capacity")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table
    df = pd.DataFrame(filtered)[["name", "capacity_tbps", "length_km", "rfs_year", "owners", "landing_a", "landing_b"]]
    df.columns = ["Cable", "Capacity (Tbps)", "Length (km)", "RFS Year", "Owners", "Landing A", "Landing B"]
    st.dataframe(df.sort_values("Capacity (Tbps)", ascending=False), width="stretch")


def _render_data_centers():
    """Map 2: Major data center locations."""
    st.markdown("#### Global Data Center Hubs")
    st.caption("Major data center clusters worldwide with operators and power capacity.")

    countries = sorted(set(d["country"] for d in DATA_CENTERS))
    sel_country = st.multiselect("Filter by country", countries, default=[], key="dc_country")
    min_mw = st.slider("Minimum capacity (MW)", 0, 2500, 0, key="dc_mw")

    filtered = DATA_CENTERS
    if sel_country:
        filtered = [d for d in filtered if d["country"] in sel_country]
    filtered = [d for d in filtered if d["capacity_mw"] >= min_mw]
    st.info(f"Showing **{len(filtered)}** of {len(DATA_CENTERS)} data center hubs")

    c1, c2, c3 = st.columns(3)
    c1.metric("Locations", len(filtered))
    c2.metric("Total capacity", f"{sum(d['capacity_mw'] for d in filtered):,} MW")
    c3.metric("Countries", len(set(d["country"] for d in filtered)))

    m = _make_dark_map()
    for dc in filtered:
        size = max(5, min(25, dc["capacity_mw"] / 100))
        popup_html = (
            f"<b>{_safe(dc['name'])}</b><br>"
            f"Operator(s): {_safe(dc['operator'])}<br>"
            f"Capacity: {dc['capacity_mw']} MW<br>"
            f"Country: {_safe(dc['country'])}"
        )
        folium.CircleMarker(
            [dc["lat"], dc["lon"]], radius=size,
            color="#f97316", fill=True, fill_color="#f97316", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    _render_folium(m)

    # Chart
    fig, ax = _dark_chart()
    sorted_dc = sorted(filtered, key=lambda x: x["capacity_mw"], reverse=True)[:15]
    names = [d["name"][:30] for d in sorted_dc]
    mw = [d["capacity_mw"] for d in sorted_dc]
    ax.barh(names[::-1], mw[::-1], color="#f97316", edgecolor="#c2410c")
    ax.set_xlabel("Capacity (MW)")
    ax.set_title("Top Data Center Hubs by Power Capacity")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(filtered)[["name", "operator", "capacity_mw", "country"]]
    df.columns = ["Location", "Operators", "Capacity (MW)", "Country"]
    st.dataframe(df.sort_values("Capacity (MW)", ascending=False), width="stretch")


def _render_tech_hubs():
    """Map 3: Technology startup hubs."""
    st.markdown("#### Global Tech Startup Hubs")
    st.caption("Major tech ecosystems ranked by unicorn count and funding volume.")

    sort_by = st.radio("Sort by", ["Unicorn count", "Funding volume ($B)"], horizontal=True, key="hub_sort")

    c1, c2, c3 = st.columns(3)
    c1.metric("Tech hubs", len(TECH_HUBS))
    c2.metric("Total unicorns", sum(h["unicorns"] for h in TECH_HUBS))
    c3.metric("Total funding", f"${sum(h['funding_b'] for h in TECH_HUBS):.0f}B")

    m = _make_dark_map()
    max_u = max(h["unicorns"] for h in TECH_HUBS)
    for hub in TECH_HUBS:
        size = max(5, int(hub["unicorns"] / max_u * 25))
        popup_html = (
            f"<b>{_safe(hub['name'])}</b> ({_safe(hub['country'])})<br>"
            f"Unicorns: {hub['unicorns']}<br>"
            f"Funding: ${hub['funding_b']}B<br>"
            f"Specialty: {_safe(hub['specialty'])}"
        )
        folium.CircleMarker(
            [hub["lat"], hub["lon"]], radius=size,
            color="#a78bfa", fill=True, fill_color="#a78bfa", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    _render_folium(m)

    # Chart
    fig, ax = _dark_chart()
    key = "unicorns" if "Unicorn" in sort_by else "funding_b"
    label = "Unicorn count" if key == "unicorns" else "Funding ($B)"
    sorted_hubs = sorted(TECH_HUBS, key=lambda x: x[key], reverse=True)[:15]
    names = [h["name"] for h in sorted_hubs]
    vals = [h[key] for h in sorted_hubs]
    ax.barh(names[::-1], vals[::-1], color="#a78bfa", edgecolor="#7c3aed")
    ax.set_xlabel(label)
    ax.set_title(f"Top Tech Hubs by {label}")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(TECH_HUBS)[["name", "country", "unicorns", "funding_b", "specialty"]]
    df.columns = ["Hub", "Country", "Unicorns", "Funding ($B)", "Specialty"]
    sort_col = "Unicorns" if "Unicorn" in sort_by else "Funding ($B)"
    st.dataframe(df.sort_values(sort_col, ascending=False), width="stretch")


def _render_ixps():
    """Map 4: Internet Exchange Points."""
    st.markdown("#### Internet Exchange Points (IXPs)")
    st.caption("Major IXPs worldwide with peak traffic and member network counts.")

    min_traffic = st.slider("Minimum peak traffic (Tbps)", 0.0, 25.0, 0.0, step=0.5, key="ixp_tbps")
    filtered = [i for i in IXP_DATA if i["peak_tbps"] >= min_traffic]
    st.info(f"Showing **{len(filtered)}** of {len(IXP_DATA)} IXPs")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IXPs", len(filtered))
    c2.metric("Total peak traffic", f"{sum(i['peak_tbps'] for i in filtered):.1f} Tbps")
    c3.metric("Total members", f"{sum(i['members'] for i in filtered):,}")
    c4.metric("Countries", len(set(i["country"] for i in filtered)))

    m = _make_dark_map()
    max_t = max(i["peak_tbps"] for i in filtered) if filtered else 1
    for ixp in filtered:
        size = max(5, int(ixp["peak_tbps"] / max_t * 22))
        popup_html = (
            f"<b>{_safe(ixp['name'])}</b><br>"
            f"Peak traffic: {ixp['peak_tbps']} Tbps<br>"
            f"Members: {ixp['members']}<br>"
            f"Country: {_safe(ixp['country'])}<br>"
            f"Founded: {ixp['founded']}"
        )
        folium.CircleMarker(
            [ixp["lat"], ixp["lon"]], radius=size,
            color="#22d3ee", fill=True, fill_color="#22d3ee", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    _render_folium(m)

    fig, ax = _dark_chart()
    sorted_ixps = sorted(filtered, key=lambda x: x["peak_tbps"], reverse=True)[:15]
    names = [i["name"] for i in sorted_ixps]
    traffic = [i["peak_tbps"] for i in sorted_ixps]
    ax.barh(names[::-1], traffic[::-1], color="#22d3ee", edgecolor="#0891b2")
    ax.set_xlabel("Peak Traffic (Tbps)")
    ax.set_title("Top IXPs by Peak Traffic")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(filtered)[["name", "peak_tbps", "members", "country", "founded"]]
    df.columns = ["IXP", "Peak Traffic (Tbps)", "Members", "Country", "Founded"]
    st.dataframe(df.sort_values("Peak Traffic (Tbps)", ascending=False), width="stretch")


def _render_particle_accelerators():
    """Map 5: Particle accelerators and synchrotron light sources."""
    st.markdown("#### Particle Accelerators & Synchrotrons")
    st.caption("Major particle physics facilities, colliders, and synchrotron light sources.")

    status_filter = st.multiselect(
        "Filter by status keyword",
        ["Operational", "Under construction", "Decommissioning", "commissioning"],
        default=[], key="accel_status"
    )
    filtered = PARTICLE_ACCELERATORS
    if status_filter:
        filtered = [a for a in filtered if any(s.lower() in a["status"].lower() for s in status_filter)]

    st.info(f"Showing **{len(filtered)}** of {len(PARTICLE_ACCELERATORS)} facilities")

    c1, c2, c3 = st.columns(3)
    c1.metric("Facilities", len(filtered))
    max_e = max(a["energy_gev"] for a in filtered) if filtered else 0
    c2.metric("Max beam energy", f"{max_e:,} GeV")
    c3.metric("Countries", len(set(a["country"] for a in filtered)))

    m = _make_dark_map(zoom=2)
    for acc in filtered:
        size = max(6, min(20, int(math.log10(max(1, acc["energy_gev"])) * 5)))
        popup_html = (
            f"<b>{_safe(acc['name'])}</b><br>"
            f"Type: {_safe(acc['type'])}<br>"
            f"Energy: {acc['energy_gev']} GeV<br>"
            f"Circumference: {acc['circumference_km']} km<br>"
            f"Experiments: {_safe(acc['experiments'])}<br>"
            f"Status: {_safe(acc['status'])}<br>"
            f"Country: {_safe(acc['country'])}"
        )
        folium.CircleMarker(
            [acc["lat"], acc["lon"]], radius=size,
            color="#f472b6", fill=True, fill_color="#f472b6", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350)
        ).add_to(m)
    _render_folium(m)

    fig, ax = _dark_chart()
    sorted_acc = sorted(filtered, key=lambda x: x["energy_gev"], reverse=True)[:12]
    names = [a["name"] for a in sorted_acc]
    energies = [a["energy_gev"] for a in sorted_acc]
    ax.barh(names[::-1], energies[::-1], color="#f472b6", edgecolor="#be185d")
    ax.set_xlabel("Beam Energy (GeV)")
    ax.set_title("Particle Accelerators by Beam Energy")
    ax.set_xscale("log")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(filtered)[["name", "type", "energy_gev", "circumference_km", "experiments", "status", "country"]]
    df.columns = ["Facility", "Type", "Energy (GeV)", "Circumference (km)", "Experiments", "Status", "Country"]
    st.dataframe(df.sort_values("Energy (GeV)", ascending=False), width="stretch")


def _render_space_agencies():
    """Map 6: Space agencies and private launch providers."""
    st.markdown("#### Space Agencies & Launch Providers")
    st.caption("Government space agencies and major private space companies worldwide.")

    min_budget = st.slider("Minimum budget ($B)", 0.0, 25.0, 0.0, step=0.1, key="space_budget")
    filtered = [s for s in SPACE_AGENCIES if s["budget_b"] >= min_budget]

    st.info(f"Showing **{len(filtered)}** of {len(SPACE_AGENCIES)} agencies/companies")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agencies", len(filtered))
    c2.metric("Total budget", f"${sum(s['budget_b'] for s in filtered):.1f}B")
    c3.metric("Active missions", sum(s["active_missions"] for s in filtered))
    c4.metric("Countries", len(set(s["country"] for s in filtered)))

    m = _make_dark_map()
    max_b = max(s["budget_b"] for s in filtered) if filtered else 1
    for sa in filtered:
        size = max(6, int(sa["budget_b"] / max_b * 20))
        popup_html = (
            f"<b>{_safe(sa['name'])}</b><br>"
            f"Country: {_safe(sa['country'])}<br>"
            f"Budget: ${sa['budget_b']}B<br>"
            f"Active missions: {sa['active_missions']}<br>"
            f"HQ: {_safe(sa['hq'])}<br>"
            f"Founded: {sa['founded']}"
        )
        color = "#fbbf24" if "Private" not in sa["country"] else "#ef4444"
        folium.CircleMarker(
            [sa["lat"], sa["lon"]], radius=size,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    _render_folium(m)

    fig, ax = _dark_chart()
    sorted_sa = sorted(filtered, key=lambda x: x["budget_b"], reverse=True)[:15]
    names = [s["name"] for s in sorted_sa]
    budgets = [s["budget_b"] for s in sorted_sa]
    colors = ["#ef4444" if "Private" in s["country"] else "#fbbf24" for s in sorted_sa]
    ax.barh(names[::-1], budgets[::-1], color=colors[::-1], edgecolor="#92400e")
    ax.set_xlabel("Budget ($B)")
    ax.set_title("Space Agencies by Budget (yellow=govt, red=private)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(filtered)[["name", "country", "budget_b", "active_missions", "hq", "founded"]]
    df.columns = ["Agency", "Country", "Budget ($B)", "Active Missions", "HQ", "Founded"]
    st.dataframe(df.sort_values("Budget ($B)", ascending=False), width="stretch")


@st.cache_data(ttl=3600)
def _fetch_research_reactors_overpass(bbox=None):
    """Fetch research reactors from Overpass API."""
    try:
        if bbox is None:
            query = """
            [out:json][timeout:30];
            (
              node["facility"="research_reactor"];
              way["facility"="research_reactor"];
              node["generator:source"="nuclear"]["generator:method"="fission"]["operator:type"="research"];
            );
            out center 50;
            """
        else:
            s, w, n, e = bbox
            query = f"""
            [out:json][timeout:30];
            (
              node["facility"="research_reactor"]({s},{w},{n},{e});
              way["facility"="research_reactor"]({s},{w},{n},{e});
            );
            out center 50;
            """
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for el in data.get("elements", []):
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if lat and lon:
                    tags = el.get("tags", {})
                    results.append({
                        "name": tags.get("name", "Unknown Research Reactor"),
                        "lat": lat, "lon": lon,
                        "operator": tags.get("operator", "N/A"),
                        "source": "Overpass API"
                    })
            return results
        return []
    except Exception:
        return []


def _render_nuclear_research():
    """Map 7: Nuclear research reactors and fusion experiments."""
    st.markdown("#### Nuclear Research & Fusion Experiments")
    st.caption("Research reactors, tokamaks, stellarators, and fusion experiments worldwide.")

    show_overpass = st.checkbox("Also fetch research reactors from Overpass API", value=False, key="nuc_overpass")

    type_filter = st.multiselect(
        "Filter by type",
        sorted(set(n["type"] for n in NUCLEAR_RESEARCH)),
        default=[], key="nuc_type"
    )
    filtered = NUCLEAR_RESEARCH
    if type_filter:
        filtered = [n for n in filtered if n["type"] in type_filter]

    overpass_reactors = []
    if show_overpass:
        with st.spinner("Fetching research reactors from Overpass API..."):
            overpass_reactors = _fetch_research_reactors_overpass()
        if overpass_reactors:
            st.success(f"Found {len(overpass_reactors)} reactors from Overpass API")

    st.info(f"Showing **{len(filtered)}** hardcoded + **{len(overpass_reactors)}** from Overpass")

    c1, c2, c3 = st.columns(3)
    c1.metric("Hardcoded sites", len(filtered))
    c2.metric("Overpass results", len(overpass_reactors))
    fusion_count = sum(1 for n in filtered if "Fusion" in n["type"] or "fusion" in n["type"].lower())
    c3.metric("Fusion experiments", fusion_count)

    m = _make_dark_map()
    for nr in filtered:
        is_fusion = "fusion" in nr["type"].lower() or "Tokamak" in nr["type"] or "Stellarator" in nr["type"]
        color = "#22d3ee" if is_fusion else "#fbbf24"
        popup_html = (
            f"<b>{_safe(nr['name'])}</b><br>"
            f"Type: {_safe(nr['type'])}<br>"
            f"Status: {_safe(nr['status'])}<br>"
            f"Output: {_safe(nr['energy_output'])}<br>"
            f"Country: {_safe(nr['country'])}<br>"
            f"{_safe(nr['desc'])}"
        )
        folium.CircleMarker(
            [nr["lat"], nr["lon"]], radius=9,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350)
        ).add_to(m)

    for reactor in overpass_reactors:
        popup_html = (
            f"<b>{_safe(reactor['name'])}</b><br>"
            f"Operator: {_safe(reactor['operator'])}<br>"
            f"Source: Overpass API"
        )
        folium.CircleMarker(
            [reactor["lat"], reactor["lon"]], radius=6,
            color="#94a3b8", fill=True, fill_color="#94a3b8", fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    _render_folium(m)

    # Chart by type
    fig, ax = _dark_chart()
    type_counts = {}
    for nr in filtered:
        t = nr["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    if sorted_types:
        labels = [t[0][:35] for t in sorted_types]
        values = [t[1] for t in sorted_types]
        ax.barh(labels[::-1], values[::-1], color="#22d3ee", edgecolor="#0891b2")
        ax.set_xlabel("Count")
        ax.set_title("Nuclear Research Facilities by Type")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(filtered)[["name", "type", "status", "energy_output", "country", "desc"]]
    df.columns = ["Facility", "Type", "Status", "Output", "Country", "Description"]
    st.dataframe(df, width="stretch")


def _render_supercomputers():
    """Map 8: Top supercomputers."""
    st.markdown("#### World's Top Supercomputers")
    st.caption("Top supercomputers ranked by FLOPS performance with location and specifications.")

    sort_metric = st.radio("Sort by", ["Performance (PFLOPS)", "Power (MW)", "Core count"], horizontal=True, key="sc_sort")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Systems", len(SUPERCOMPUTERS))
    c2.metric("Total PFLOPS", f"{sum(s['flops_pflops'] for s in SUPERCOMPUTERS):,.0f}")
    c3.metric("Total power", f"{sum(s['power_mw'] for s in SUPERCOMPUTERS):.1f} MW")
    c4.metric("Total cores", f"{sum(s['cores'] for s in SUPERCOMPUTERS):,}")

    m = _make_dark_map()
    max_f = max(s["flops_pflops"] for s in SUPERCOMPUTERS)
    for sc in SUPERCOMPUTERS:
        size = max(6, int(sc["flops_pflops"] / max_f * 22))
        popup_html = (
            f"<b>{_safe(sc['name'])}</b><br>"
            f"Location: {_safe(sc['location'])}<br>"
            f"Performance: {sc['flops_pflops']} PFLOPS<br>"
            f"Cores: {sc['cores']:,}<br>"
            f"Power: {sc['power_mw']} MW<br>"
            f"Vendor: {_safe(sc['vendor'])}<br>"
            f"Year: {sc['year']}"
        )
        folium.CircleMarker(
            [sc["lat"], sc["lon"]], radius=size,
            color="#34d399", fill=True, fill_color="#34d399", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    _render_folium(m)

    fig, ax = _dark_chart()
    if "Performance" in sort_metric:
        key, label = "flops_pflops", "PFLOPS"
    elif "Power" in sort_metric:
        key, label = "power_mw", "Power (MW)"
    else:
        key, label = "cores", "Core Count"
    sorted_sc = sorted(SUPERCOMPUTERS, key=lambda x: x[key], reverse=True)[:15]
    names = [s["name"] for s in sorted_sc]
    vals = [s[key] for s in sorted_sc]
    ax.barh(names[::-1], vals[::-1], color="#34d399", edgecolor="#059669")
    ax.set_xlabel(label)
    ax.set_title(f"Top Supercomputers by {label}")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(SUPERCOMPUTERS)[["name", "location", "flops_pflops", "cores", "power_mw", "vendor", "year"]]
    df.columns = ["Name", "Location", "PFLOPS", "Cores", "Power (MW)", "Vendor", "Year"]
    sort_map = {"Performance (PFLOPS)": "PFLOPS", "Power (MW)": "Power (MW)", "Core count": "Cores"}
    st.dataframe(df.sort_values(sort_map.get(sort_metric, "PFLOPS"), ascending=False), width="stretch")


def _render_telescope_arrays():
    """Map 9: Telescope arrays and gravitational wave detectors."""
    st.markdown("#### Telescope Arrays & Observatories")
    st.caption("Radio arrays, gravitational wave detectors, neutrino observatories, and cosmic ray detectors.")

    types = sorted(set(t["type"] for t in TELESCOPE_ARRAYS))
    sel_types = st.multiselect("Filter by type", types, default=[], key="tel_types")
    filtered = TELESCOPE_ARRAYS
    if sel_types:
        filtered = [t for t in filtered if t["type"] in sel_types]

    st.info(f"Showing **{len(filtered)}** of {len(TELESCOPE_ARRAYS)} facilities")

    c1, c2, c3 = st.columns(3)
    c1.metric("Observatories", len(filtered))
    c2.metric("Unique types", len(set(t["type"] for t in filtered)))
    c3.metric("Countries", len(set(t["country"] for t in filtered)))

    m = _make_dark_map()
    type_colors = {
        "Radio interferometer": "#06b6d4",
        "Millimeter/submillimeter": "#22d3ee",
        "Low-freq radio array": "#67e8f9",
        "Mid-freq radio array": "#a5f3fc",
        "Cylindrical radio telescope": "#2dd4bf",
        "Neutrino detector": "#c084fc",
        "Gravitational wave detector": "#f472b6",
        "Single dish radio telescope": "#fbbf24",
        "Single dish (destroyed)": "#94a3b8",
        "Cherenkov gamma-ray": "#ef4444",
        "Cosmic ray detector": "#fb923c",
        "Global VLBI network": "#e879f9",
        "Millimeter interferometer": "#38bdf8",
        "Low-freq radio": "#5eead4",
    }
    for tel in filtered:
        color = type_colors.get(tel["type"], "#8b97b0")
        popup_html = (
            f"<b>{_safe(tel['name'])}</b><br>"
            f"Type: {_safe(tel['type'])}<br>"
            f"Dishes/elements: {_safe(tel['dishes'])}<br>"
            f"Frequency: {_safe(tel['frequency'])}<br>"
            f"Purpose: {_safe(tel['purpose'])}<br>"
            f"Location: {_safe(tel['country'])}"
        )
        folium.CircleMarker(
            [tel["lat"], tel["lon"]], radius=10,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350)
        ).add_to(m)
    _render_folium(m)

    fig, ax = _dark_chart()
    type_counts = {}
    for t in filtered:
        tp = t["type"]
        type_counts[tp] = type_counts.get(tp, 0) + 1
    sorted_tc = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    if sorted_tc:
        labels = [t[0] for t in sorted_tc]
        vals = [t[1] for t in sorted_tc]
        colors_chart = [type_colors.get(l, "#8b97b0") for l in labels]
        ax.barh(labels[::-1], vals[::-1], color=colors_chart[::-1])
        ax.set_xlabel("Count")
        ax.set_title("Telescope/Observatory Types")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(filtered)[["name", "type", "dishes", "frequency", "purpose", "country"]]
    df.columns = ["Name", "Type", "Elements", "Frequency/Range", "Purpose", "Location"]
    st.dataframe(df, width="stretch")


def _render_renewable_tech():
    """Map 10: Renewable energy megaprojects."""
    st.markdown("#### Renewable Energy Megaprojects")
    st.caption("Major renewable energy installations worldwide: solar, wind, hydro, geothermal.")

    energy_types = sorted(set(r["type"] for r in RENEWABLE_MEGAPROJECTS))
    sel_types = st.multiselect("Filter by energy type", energy_types, default=[], key="ren_types")
    min_gw = st.slider("Minimum capacity (GW)", 0.0, 39.0, 0.0, step=0.5, key="ren_gw")

    filtered = RENEWABLE_MEGAPROJECTS
    if sel_types:
        filtered = [r for r in filtered if r["type"] in sel_types]
    filtered = [r for r in filtered if r["capacity_gw"] >= min_gw]

    st.info(f"Showing **{len(filtered)}** of {len(RENEWABLE_MEGAPROJECTS)} projects")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projects", len(filtered))
    c2.metric("Total capacity", f"{sum(r['capacity_gw'] for r in filtered):.1f} GW")
    c3.metric("Total cost", f"${sum(r['cost_b'] for r in filtered):.1f}B")
    c4.metric("Energy types", len(set(r["type"] for r in filtered)))

    type_colors_ren = {
        "Hydroelectric": "#3b82f6",
        "Solar PV": "#fbbf24",
        "Onshore Wind": "#22d3ee",
        "Offshore Wind": "#06b6d4",
        "CSP + Solar PV": "#f97316",
        "Solar + Wind": "#eab308",
        "Geothermal": "#ef4444",
        "Hydroelectric (planned)": "#60a5fa",
    }

    m = _make_dark_map()
    max_gw = max(r["capacity_gw"] for r in filtered) if filtered else 1
    for proj in filtered:
        size = max(6, int(proj["capacity_gw"] / max_gw * 22))
        color = type_colors_ren.get(proj["type"], "#8b97b0")
        popup_html = (
            f"<b>{_safe(proj['name'])}</b><br>"
            f"Type: {_safe(proj['type'])}<br>"
            f"Capacity: {proj['capacity_gw']} GW<br>"
            f"Cost: ${proj['cost_b']}B<br>"
            f"Status: {_safe(proj['status'])}<br>"
            f"Country: {_safe(proj['country'])}<br>"
            f"{_safe(proj['desc'])}"
        )
        folium.CircleMarker(
            [proj["lat"], proj["lon"]], radius=size,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350)
        ).add_to(m)
    _render_folium(m)

    # Chart
    fig, ax = _dark_chart()
    sorted_proj = sorted(filtered, key=lambda x: x["capacity_gw"], reverse=True)[:15]
    names = [p["name"][:30] for p in sorted_proj]
    caps = [p["capacity_gw"] for p in sorted_proj]
    colors_bars = [type_colors_ren.get(p["type"], "#8b97b0") for p in sorted_proj]
    ax.barh(names[::-1], caps[::-1], color=colors_bars[::-1])
    ax.set_xlabel("Capacity (GW)")
    ax.set_title("Top Renewable Energy Projects by Capacity")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Pie chart by type
    fig2, ax2 = _dark_chart()
    type_cap = {}
    for r in filtered:
        type_cap[r["type"]] = type_cap.get(r["type"], 0) + r["capacity_gw"]
    if type_cap:
        labels = list(type_cap.keys())
        sizes = list(type_cap.values())
        pie_colors = [type_colors_ren.get(l, "#8b97b0") for l in labels]
        wedges, texts, autotexts = ax2.pie(
            sizes, labels=labels, autopct="%1.1f%%", colors=pie_colors,
            textprops={"color": "#e8ecf4", "fontsize": 9}
        )
        for at in autotexts:
            at.set_color("#0a0e1a")
            at.set_fontsize(8)
        ax2.set_title("Capacity Share by Energy Type")
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    df = pd.DataFrame(filtered)[["name", "type", "capacity_gw", "cost_b", "status", "country", "desc"]]
    df.columns = ["Project", "Type", "Capacity (GW)", "Cost ($B)", "Status", "Country", "Description"]
    st.dataframe(df.sort_values("Capacity (GW)", ascending=False), width="stretch")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

MAP_OPTIONS = {
    "Submarine Cables": _render_submarine_cables,
    "Data Centers": _render_data_centers,
    "Tech Startup Hubs": _render_tech_hubs,
    "Internet Exchange Points": _render_ixps,
    "Particle Accelerators": _render_particle_accelerators,
    "Space Agencies": _render_space_agencies,
    "Nuclear Research Reactors": _render_nuclear_research,
    "Supercomputers": _render_supercomputers,
    "Telescope Arrays": _render_telescope_arrays,
    "Renewable Tech": _render_renewable_tech,
}


def render_technology_maps_tab():
    """Main entry point for the Internet & Technology Maps tab."""
    st.markdown(
        '<div class="tab-header cyan">'
        "<h4>Internet &amp; Technology Maps</h4>"
        "<p>Data centers, submarine cables, tech hubs, particle accelerators, research labs</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    selected_map = st.selectbox(
        "Select technology map",
        list(MAP_OPTIONS.keys()),
        key="tech_map_select",
    )

    st.markdown("---")

    # Render the selected map
    render_fn = MAP_OPTIONS.get(selected_map)
    if render_fn:
        render_fn()


# ---------------------------------------------------------------------------
# Allow standalone testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    st.set_page_config(page_title="Technology Maps", layout="wide")
    render_technology_maps_tab()
