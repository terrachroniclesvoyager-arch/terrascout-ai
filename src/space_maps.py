# -*- coding: utf-8 -*-
"""
Space Exploration Explorer module for TerraScout AI.
Curated datasets of space launch sites, observatories, radio telescopes,
space debris, meteorite craters, astronaut birthplaces, DSN stations,
space museums, satellite ground stations, and Moon/Mars landing sites.
Uses free APIs (NASA ISS, Open Notify) and curated geodata.
"""

import io
import logging
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import requests
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════
BG_DARK = "#0a0e1a"
BG_SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"
ACCENT_CYAN = "#06b6d4"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_EMERALD = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_PINK = "#ec4899"
ACCENT_RED = "#ef4444"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"
BORDER_COLOR = "#2a3550"

# ═══════════════════════════════════════════════════════════════
# MODE 1: SPACE LAUNCH SITES
# ═══════════════════════════════════════════════════════════════
LAUNCH_SITES = [
    {"name": "Kennedy Space Center (LC-39)", "country": "USA", "operator": "NASA",
     "lat": 28.5729, "lon": -80.6490, "status": "Active",
     "description": "Historic Apollo and Space Shuttle launch complex, now used by SpaceX and NASA SLS.",
     "first_launch": 1967, "notable": "Apollo 11, STS-1, Artemis I"},
    {"name": "Cape Canaveral SFS (SLC-40)", "country": "USA", "operator": "SpaceX",
     "lat": 28.5618, "lon": -80.5771, "status": "Active",
     "description": "Primary SpaceX Falcon 9 launch pad on the East Coast.",
     "first_launch": 1965, "notable": "Falcon 9, CRS missions"},
    {"name": "Cape Canaveral SFS (SLC-41)", "country": "USA", "operator": "ULA",
     "lat": 28.5833, "lon": -80.5830, "status": "Active",
     "description": "ULA Atlas V and Vulcan Centaur launch site.",
     "first_launch": 1965, "notable": "Mars rovers, Juno, OSIRIS-REx"},
    {"name": "Vandenberg SFB (SLC-4E)", "country": "USA", "operator": "SpaceX",
     "lat": 34.6321, "lon": -120.6108, "status": "Active",
     "description": "SpaceX West Coast launch site for polar and sun-synchronous orbits.",
     "first_launch": 2013, "notable": "Iridium NEXT, Starlink polar"},
    {"name": "Baikonur Cosmodrome", "country": "Kazakhstan", "operator": "Roscosmos",
     "lat": 45.9650, "lon": 63.3050, "status": "Active",
     "description": "World's first and largest spaceport. Launched Sputnik and Vostok 1.",
     "first_launch": 1957, "notable": "Sputnik 1, Vostok 1, Soyuz missions"},
    {"name": "Vostochny Cosmodrome", "country": "Russia", "operator": "Roscosmos",
     "lat": 51.8844, "lon": 128.3340, "status": "Active",
     "description": "Russia's modern spaceport in the Far East, replacing Baikonur dependency.",
     "first_launch": 2016, "notable": "Soyuz-2, Luna-25"},
    {"name": "Guiana Space Centre (Kourou)", "country": "French Guiana", "operator": "ESA/Arianespace",
     "lat": 5.2360, "lon": -52.7690, "status": "Active",
     "description": "Europe's spaceport near the equator, ideal for geostationary launches.",
     "first_launch": 1968, "notable": "Ariane 5, Ariane 6, JWST launch"},
    {"name": "Jiuquan Satellite Launch Center", "country": "China", "operator": "CNSA",
     "lat": 40.9580, "lon": 100.2910, "status": "Active",
     "description": "China's oldest launch center, used for crewed Shenzhou missions.",
     "first_launch": 1970, "notable": "Shenzhou, Tiangong missions"},
    {"name": "Xichang Satellite Launch Center", "country": "China", "operator": "CNSA",
     "lat": 28.2463, "lon": 102.0268, "status": "Active",
     "description": "Primary site for Chinese geostationary satellite launches.",
     "first_launch": 1984, "notable": "BeiDou, Chang'e missions"},
    {"name": "Wenchang Space Launch Site", "country": "China", "operator": "CNSA",
     "lat": 19.6145, "lon": 110.9510, "status": "Active",
     "description": "China's newest and most southerly launch site on Hainan Island.",
     "first_launch": 2016, "notable": "Long March 5, Tianwen-1"},
    {"name": "Satish Dhawan Space Centre (SHAR)", "country": "India", "operator": "ISRO",
     "lat": 13.7199, "lon": 80.2304, "status": "Active",
     "description": "India's primary orbital launch facility on Sriharikota island.",
     "first_launch": 1971, "notable": "Chandrayaan, Mangalyaan, PSLV"},
    {"name": "Tanegashima Space Center", "country": "Japan", "operator": "JAXA",
     "lat": 30.4009, "lon": 131.0000, "status": "Active",
     "description": "Japan's main launch center, known as the most beautiful spaceport.",
     "first_launch": 1969, "notable": "H-IIA, H3, Hayabusa2"},
    {"name": "Uchinoura Space Center", "country": "Japan", "operator": "JAXA",
     "lat": 31.2510, "lon": 131.0790, "status": "Active",
     "description": "JAXA facility for small solid-fuel rocket launches and sounding rockets.",
     "first_launch": 1962, "notable": "Epsilon, Ohsumi (first Japanese satellite)"},
    {"name": "Naro Space Center", "country": "South Korea", "operator": "KARI",
     "lat": 34.4316, "lon": 127.5350, "status": "Active",
     "description": "South Korea's spaceport, site of the Nuri rocket launches.",
     "first_launch": 2009, "notable": "KSLV-1 (Naro), KSLV-II (Nuri)"},
    {"name": "Rocket Lab Launch Complex 1", "country": "New Zealand", "operator": "Rocket Lab",
     "lat": -39.2615, "lon": 177.8649, "status": "Active",
     "description": "Private small-sat launch site on Mahia Peninsula.",
     "first_launch": 2017, "notable": "Electron rocket, CAPSTONE"},
    {"name": "SpaceX Starbase (Boca Chica)", "country": "USA", "operator": "SpaceX",
     "lat": 25.9972, "lon": -97.1560, "status": "Active",
     "description": "SpaceX's Starship development and launch facility in South Texas.",
     "first_launch": 2023, "notable": "Starship/Super Heavy test flights"},
    {"name": "Mid-Atlantic Regional Spaceport", "country": "USA", "operator": "Virginia Space",
     "lat": 37.8334, "lon": -75.4884, "status": "Active",
     "description": "Wallops Island facility used by Northrop Grumman for ISS resupply.",
     "first_launch": 1995, "notable": "Antares, Cygnus CRS missions"},
    {"name": "Palmachim Airbase", "country": "Israel", "operator": "ISA",
     "lat": 31.8847, "lon": 34.6828, "status": "Active",
     "description": "Israeli launch site for Shavit rockets, launching westward over Mediterranean.",
     "first_launch": 1988, "notable": "Shavit, Ofeq satellites"},
    {"name": "Semnan Space Center", "country": "Iran", "operator": "ISA (Iran)",
     "lat": 35.2345, "lon": 53.9210, "status": "Active",
     "description": "Iran's primary orbital launch site in the Semnan province.",
     "first_launch": 2009, "notable": "Safir, Simorgh rockets"},
    {"name": "Plesetsk Cosmodrome", "country": "Russia", "operator": "Russian MoD",
     "lat": 62.9271, "lon": 40.5777, "status": "Active",
     "description": "World's most-used launch facility by number of launches. Military and civil.",
     "first_launch": 1966, "notable": "Soyuz, Angara, Rockot"},
]

# ═══════════════════════════════════════════════════════════════
# MODE 2: GREAT OBSERVATORIES
# ═══════════════════════════════════════════════════════════════
GREAT_OBSERVATORIES = [
    {"name": "W. M. Keck Observatory", "location": "Mauna Kea, Hawaii, USA",
     "lat": 19.8264, "lon": -155.4747, "type": "Optical/IR",
     "aperture": "10.0 m (x2)", "altitude_m": 4145, "year": 1993,
     "description": "Twin 10-meter segmented-mirror telescopes, among the world's most productive."},
    {"name": "Subaru Telescope (NAOJ)", "location": "Mauna Kea, Hawaii, USA",
     "lat": 19.8253, "lon": -155.4761, "type": "Optical/IR",
     "aperture": "8.2 m", "altitude_m": 4163, "year": 1999,
     "description": "Japanese 8.2m telescope with Hyper Suprime-Cam wide-field imager."},
    {"name": "Gemini North", "location": "Mauna Kea, Hawaii, USA",
     "lat": 19.8238, "lon": -155.4690, "type": "Optical/IR",
     "aperture": "8.1 m", "altitude_m": 4213, "year": 1999,
     "description": "Northern twin of the Gemini Observatory, international partnership."},
    {"name": "Gemini South", "location": "Cerro Pachon, Chile",
     "lat": -30.2407, "lon": -70.7367, "type": "Optical/IR",
     "aperture": "8.1 m", "altitude_m": 2722, "year": 2001,
     "description": "Southern twin providing full-sky coverage with Gemini North."},
    {"name": "Very Large Telescope (VLT)", "location": "Cerro Paranal, Chile",
     "lat": -24.6275, "lon": -70.4044, "type": "Optical/IR",
     "aperture": "8.2 m (x4)", "altitude_m": 2635, "year": 1998,
     "description": "ESO's flagship: four 8.2m Unit Telescopes, can work as interferometer."},
    {"name": "La Silla Observatory", "location": "La Silla, Chile",
     "lat": -29.2563, "lon": -70.7300, "type": "Optical/IR",
     "aperture": "3.6 m (main)", "altitude_m": 2400, "year": 1969,
     "description": "ESO's first observatory, pioneered exoplanet radial velocity surveys."},
    {"name": "Gran Telescopio Canarias (GTC)", "location": "La Palma, Canary Islands, Spain",
     "lat": 28.7567, "lon": -17.8917, "type": "Optical/IR",
     "aperture": "10.4 m", "altitude_m": 2267, "year": 2009,
     "description": "World's largest single-aperture optical telescope."},
    {"name": "Large Binocular Telescope (LBT)", "location": "Mount Graham, Arizona, USA",
     "lat": 32.7016, "lon": -109.8891, "type": "Optical/IR",
     "aperture": "8.4 m (x2)", "altitude_m": 3221, "year": 2005,
     "description": "Twin 8.4m mirrors on a single mount, equivalent to 11.8m aperture."},
    {"name": "Arecibo Observatory (Collapsed)", "location": "Arecibo, Puerto Rico",
     "lat": 18.3464, "lon": -66.7527, "type": "Radio",
     "aperture": "305 m", "altitude_m": 497, "year": 1963,
     "description": "Iconic 305m radio dish, collapsed December 2020. Used for SETI and radar astronomy."},
    {"name": "FAST (Five-hundred-meter Aperture)", "location": "Guizhou, China",
     "lat": 25.6529, "lon": 106.8566, "type": "Radio",
     "aperture": "500 m", "altitude_m": 1000, "year": 2016,
     "description": "World's largest single-dish radio telescope, surpassing Arecibo."},
    {"name": "ALMA (Atacama Large mm Array)", "location": "Chajnantor Plateau, Chile",
     "lat": -23.0193, "lon": -67.7532, "type": "Radio/mm",
     "aperture": "66 antennas (12m+7m)", "altitude_m": 5058, "year": 2011,
     "description": "66 high-precision antennas at 5058m altitude, probing cold universe."},
    {"name": "Vera C. Rubin Observatory", "location": "Cerro Pachon, Chile",
     "lat": -30.2444, "lon": -70.7494, "type": "Optical Survey",
     "aperture": "8.4 m", "altitude_m": 2663, "year": 2025,
     "description": "Wide-field survey telescope with 3.2-gigapixel camera, mapping entire sky every 3 nights."},
    {"name": "South African Large Telescope (SALT)", "location": "Sutherland, South Africa",
     "lat": -32.3758, "lon": 20.8108, "type": "Optical",
     "aperture": "11.1 m (eff. 9.2m)", "altitude_m": 1798, "year": 2005,
     "description": "Largest optical telescope in the southern hemisphere."},
    {"name": "Thirty Meter Telescope (TMT)", "location": "Mauna Kea, Hawaii, USA (planned)",
     "lat": 19.8283, "lon": -155.4722, "type": "Optical/IR (planned)",
     "aperture": "30 m (planned)", "altitude_m": 4050, "year": 2028,
     "description": "Next-gen extremely large telescope, 12x sharper than Hubble."},
    {"name": "European Extremely Large Telescope (ELT)", "location": "Cerro Armazones, Chile",
     "lat": -24.5893, "lon": -70.1916, "type": "Optical/IR (under construction)",
     "aperture": "39.3 m", "altitude_m": 3046, "year": 2028,
     "description": "ESO's ELT will be the world's largest optical/IR telescope."},
    {"name": "Palomar Observatory (Hale)", "location": "Palomar Mountain, California, USA",
     "lat": 33.3564, "lon": -116.8650, "type": "Optical",
     "aperture": "5.08 m", "altitude_m": 1712, "year": 1948,
     "description": "Historic 200-inch Hale Telescope, dominated astronomy for decades."},
    {"name": "Mount Wilson Observatory", "location": "Mount Wilson, California, USA",
     "lat": 34.2260, "lon": -118.0570, "type": "Optical",
     "aperture": "2.5 m (Hooker)", "altitude_m": 1742, "year": 1917,
     "description": "Where Hubble discovered the expanding universe. Historic 100-inch Hooker telescope."},
    {"name": "Magellan Telescopes", "location": "Las Campanas, Chile",
     "lat": -29.0146, "lon": -70.6926, "type": "Optical/IR",
     "aperture": "6.5 m (x2)", "altitude_m": 2516, "year": 2000,
     "description": "Twin 6.5m telescopes at Carnegie's Las Campanas Observatory."},
]

# ═══════════════════════════════════════════════════════════════
# MODE 3: RADIO TELESCOPES
# ═══════════════════════════════════════════════════════════════
RADIO_TELESCOPES = [
    {"name": "Very Large Array (VLA)", "location": "Socorro, New Mexico, USA",
     "lat": 34.0784, "lon": -107.6184, "type": "Interferometer",
     "dishes": 27, "dish_size": "25 m each", "baseline": "36.4 km",
     "year": 1980, "operator": "NRAO",
     "description": "27 antennas in Y-shape, iconic radio interferometer."},
    {"name": "LOFAR (Low-Frequency Array)", "location": "Exloo, Netherlands (core)",
     "lat": 52.9150, "lon": 6.8690, "type": "Low-frequency array",
     "dishes": 52, "dish_size": "Dipole stations", "baseline": "1500 km (intl.)",
     "year": 2010, "operator": "ASTRON",
     "description": "Pan-European low-frequency array, 52 stations across Europe."},
    {"name": "Parkes Radio Telescope (Murriyang)", "location": "Parkes, NSW, Australia",
     "lat": -32.9984, "lon": 148.2636, "type": "Single dish",
     "dishes": 1, "dish_size": "64 m", "baseline": "N/A",
     "year": 1961, "operator": "CSIRO",
     "description": "Iconic 'The Dish', relayed Apollo 11 moonwalk TV, still active in pulsar research."},
    {"name": "Green Bank Telescope (GBT)", "location": "Green Bank, West Virginia, USA",
     "lat": 38.4331, "lon": -79.8397, "type": "Single dish",
     "dishes": 1, "dish_size": "100 m", "baseline": "N/A",
     "year": 2000, "operator": "GBO",
     "description": "World's largest fully steerable radio telescope."},
    {"name": "Australia Telescope Compact Array (ATCA)", "location": "Narrabri, NSW, Australia",
     "lat": -30.3128, "lon": 149.5501, "type": "Interferometer",
     "dishes": 6, "dish_size": "22 m each", "baseline": "6 km",
     "year": 1988, "operator": "CSIRO",
     "description": "Six 22m dishes on a 6km east-west track."},
    {"name": "Effelsberg Radio Telescope", "location": "Effelsberg, Germany",
     "lat": 50.5247, "lon": 6.8828, "type": "Single dish",
     "dishes": 1, "dish_size": "100 m", "baseline": "N/A",
     "year": 1972, "operator": "MPIfR",
     "description": "100m dish, one of the world's largest fully steerable radio telescopes."},
    {"name": "Jodrell Bank (Lovell Telescope)", "location": "Cheshire, England, UK",
     "lat": 53.2367, "lon": -2.3086, "type": "Single dish",
     "dishes": 1, "dish_size": "76 m", "baseline": "N/A",
     "year": 1957, "operator": "University of Manchester",
     "description": "Third-largest steerable dish, UNESCO World Heritage Site."},
    {"name": "Westerbork Synthesis Radio Telescope", "location": "Westerbork, Netherlands",
     "lat": 52.9150, "lon": 6.6044, "type": "Interferometer",
     "dishes": 14, "dish_size": "25 m each", "baseline": "2.7 km",
     "year": 1970, "operator": "ASTRON",
     "description": "14 dishes in a 2.7km east-west array."},
    {"name": "SKA-Mid (under construction)", "location": "Karoo, South Africa",
     "lat": -30.7130, "lon": 21.4430, "type": "Interferometer (future)",
     "dishes": 197, "dish_size": "13.5-15 m", "baseline": "150 km",
     "year": 2028, "operator": "SKAO",
     "description": "197 dishes forming the mid-frequency component of the Square Kilometre Array."},
    {"name": "SKA-Low (under construction)", "location": "Murchison, Western Australia",
     "lat": -26.6970, "lon": 116.6370, "type": "Low-frequency array (future)",
     "dishes": 131072, "dish_size": "Dipole antennas", "baseline": "65 km",
     "year": 2028, "operator": "SKAO",
     "description": "131,072 dipole antennas in 512 stations, probing cosmic dawn."},
    {"name": "MeerKAT", "location": "Karoo, South Africa",
     "lat": -30.7130, "lon": 21.4430, "type": "Interferometer",
     "dishes": 64, "dish_size": "13.5 m each", "baseline": "8 km",
     "year": 2018, "operator": "SARAO",
     "description": "64-dish precursor to SKA, already producing groundbreaking images."},
    {"name": "Nobeyama Radio Observatory", "location": "Nagano, Japan",
     "lat": 35.9417, "lon": 138.4722, "type": "Single dish + array",
     "dishes": 1, "dish_size": "45 m", "baseline": "N/A",
     "year": 1982, "operator": "NAOJ",
     "description": "45m millimeter-wave dish, largest mm-wave telescope in the world at completion."},
    {"name": "GMRT (Giant Metrewave Radio Telescope)", "location": "Pune, India",
     "lat": 19.0965, "lon": 74.0497, "type": "Interferometer",
     "dishes": 30, "dish_size": "45 m each", "baseline": "25 km",
     "year": 1995, "operator": "NCRA-TIFR",
     "description": "30 dishes at meter wavelengths, largest array at those frequencies."},
    {"name": "NOEMA (Northern Extended mm Array)", "location": "Plateau de Bure, French Alps",
     "lat": 44.6339, "lon": 5.9072, "type": "mm Interferometer",
     "dishes": 12, "dish_size": "15 m each", "baseline": "1.7 km",
     "year": 1988, "operator": "IRAM",
     "description": "Most powerful mm-wave interferometer in the Northern Hemisphere."},
]

# ═══════════════════════════════════════════════════════════════
# MODE 4: SPACE DEBRIS DATA (curated summary)
# ═══════════════════════════════════════════════════════════════
SPACE_DEBRIS_ZONES = [
    {"name": "LEO Dense Zone (400-600 km)", "alt_min_km": 400, "alt_max_km": 600,
     "lat": 0.0, "lon": 0.0, "object_count": 12500,
     "description": "Peak debris density zone, ISS altitude. Contains most operational satellites and spent stages.",
     "risk": "High", "category": "LEO"},
    {"name": "LEO Sun-Sync Band (700-900 km)", "alt_min_km": 700, "alt_max_km": 900,
     "lat": 0.0, "lon": 30.0, "object_count": 8200,
     "description": "Sun-synchronous orbit band. Dense with Earth-observation satellite debris.",
     "risk": "High", "category": "LEO"},
    {"name": "Starlink Constellation Shell", "alt_min_km": 540, "alt_max_km": 570,
     "lat": 0.0, "lon": 60.0, "object_count": 6000,
     "description": "SpaceX Starlink operational shell with thousands of active satellites.",
     "risk": "Moderate", "category": "LEO"},
    {"name": "Iridium/OneWeb Band (1000-1200 km)", "alt_min_km": 1000, "alt_max_km": 1200,
     "lat": 0.0, "lon": 90.0, "object_count": 3800,
     "description": "Communication constellation altitude. Iridium 33 collision debris field.",
     "risk": "High", "category": "LEO"},
    {"name": "Fengyun-1C Debris Cloud", "alt_min_km": 800, "alt_max_km": 900,
     "lat": 0.0, "lon": 120.0, "object_count": 3500,
     "description": "2007 Chinese ASAT test debris. Single worst debris-generating event.",
     "risk": "Very High", "category": "LEO"},
    {"name": "Cosmos 2251 / Iridium 33 Field", "alt_min_km": 750, "alt_max_km": 850,
     "lat": 0.0, "lon": 150.0, "object_count": 2300,
     "description": "2009 collision debris. First accidental hypervelocity satellite collision.",
     "risk": "High", "category": "LEO"},
    {"name": "MEO Navigation Belt (19000-24000 km)", "alt_min_km": 19000, "alt_max_km": 24000,
     "lat": 0.0, "lon": -60.0, "object_count": 450,
     "description": "GPS, GLONASS, Galileo, BeiDou constellation orbits.",
     "risk": "Low", "category": "MEO"},
    {"name": "GEO Belt (35786 km)", "alt_min_km": 35600, "alt_max_km": 35900,
     "lat": 0.0, "lon": -90.0, "object_count": 1800,
     "description": "Geostationary belt - communications, weather, military satellites.",
     "risk": "Moderate", "category": "GEO"},
    {"name": "GEO Graveyard Orbit (~36100 km)", "alt_min_km": 36000, "alt_max_km": 36200,
     "lat": 0.0, "lon": -120.0, "object_count": 700,
     "description": "Supersynchronous graveyard orbit for retired GEO satellites.",
     "risk": "Low", "category": "GEO"},
    {"name": "Cosmos 954 Debris Region", "alt_min_km": 250, "alt_max_km": 260,
     "lat": 62.0, "lon": -110.0, "object_count": 65,
     "description": "1978 nuclear-powered satellite debris scattered over northern Canada.",
     "risk": "Decayed", "category": "Historical"},
    {"name": "Vanguard 1 Orbit (oldest satellite)", "alt_min_km": 654, "alt_max_km": 3969,
     "lat": 0.0, "lon": -30.0, "object_count": 1,
     "description": "Launched 1958, oldest object in orbit. Highly elliptical orbit, will stay for 2000+ years.",
     "risk": "None", "category": "Historical"},
    {"name": "Tiangong-1 Re-entry Zone (decayed)", "alt_min_km": 0, "alt_max_km": 0,
     "lat": -13.0, "lon": -164.0, "object_count": 0,
     "description": "Chinese space station re-entered April 2018 over South Pacific.",
     "risk": "Decayed", "category": "Historical"},
]

# ═══════════════════════════════════════════════════════════════
# MODE 5: METEORITE IMPACT CRATERS
# ═══════════════════════════════════════════════════════════════
IMPACT_CRATERS = [
    {"name": "Vredefort Crater", "location": "Free State, South Africa",
     "lat": -27.0000, "lon": 27.5000, "diameter_km": 300, "age_mya": 2023,
     "description": "Largest verified impact structure on Earth. UNESCO World Heritage Site.",
     "impactor": "Asteroid ~15 km", "confirmed": True},
    {"name": "Chicxulub Crater", "location": "Yucatan, Mexico",
     "lat": 21.3960, "lon": -89.5160, "diameter_km": 180, "age_mya": 66,
     "description": "Caused the K-Pg mass extinction that killed the dinosaurs.",
     "impactor": "Asteroid ~10 km", "confirmed": True},
    {"name": "Sudbury Basin", "location": "Ontario, Canada",
     "lat": 46.6000, "lon": -81.1833, "diameter_km": 130, "age_mya": 1849,
     "description": "Second-largest confirmed impact structure, rich in nickel-copper ores.",
     "impactor": "Asteroid ~10-15 km", "confirmed": True},
    {"name": "Popigai Crater", "location": "Siberia, Russia",
     "lat": 71.6500, "lon": 111.1833, "diameter_km": 100, "age_mya": 35.7,
     "description": "Contains vast deposits of impact diamonds (lonsdaleite).",
     "impactor": "Asteroid ~5-8 km", "confirmed": True},
    {"name": "Manicouagan Crater", "location": "Quebec, Canada",
     "lat": 51.3830, "lon": -68.7000, "diameter_km": 100, "age_mya": 214,
     "description": "Striking annular lake visible from space, 'Eye of Quebec'.",
     "impactor": "Asteroid ~5 km", "confirmed": True},
    {"name": "Acraman Crater", "location": "South Australia",
     "lat": -32.0167, "lon": 135.4500, "diameter_km": 90, "age_mya": 580,
     "description": "Ejecta layer found 300 km away in Flinders Ranges.",
     "impactor": "Asteroid ~4 km", "confirmed": True},
    {"name": "Chesapeake Bay Crater", "location": "Virginia, USA",
     "lat": 37.2833, "lon": -76.0167, "diameter_km": 85, "age_mya": 35.5,
     "description": "Buried beneath Chesapeake Bay, influenced regional groundwater.",
     "impactor": "Asteroid ~3 km", "confirmed": True},
    {"name": "Morokweng Crater", "location": "North West, South Africa",
     "lat": -26.4667, "lon": 23.5333, "diameter_km": 70, "age_mya": 145,
     "description": "Jurassic-Cretaceous boundary impact, fossil meteorite found in melt.",
     "impactor": "L-chondrite asteroid", "confirmed": True},
    {"name": "Kara Crater", "location": "Nenetsia, Russia",
     "lat": 69.1000, "lon": 64.1500, "diameter_km": 65, "age_mya": 70.3,
     "description": "Late Cretaceous impact in Arctic Russia.",
     "impactor": "Asteroid ~4 km", "confirmed": True},
    {"name": "Barringer Crater (Meteor Crater)", "location": "Arizona, USA",
     "lat": 35.0280, "lon": -111.0225, "diameter_km": 1.186, "age_mya": 0.05,
     "description": "Best-preserved impact crater on Earth. ~50,000 years old.",
     "impactor": "Iron meteorite ~50 m", "confirmed": True},
    {"name": "Nördlinger Ries", "location": "Bavaria, Germany",
     "lat": 48.8500, "lon": 10.5167, "diameter_km": 24, "age_mya": 14.8,
     "description": "Town of Nördlingen built inside the crater. Contains suevite.",
     "impactor": "Asteroid ~1.5 km", "confirmed": True},
    {"name": "Rochechouart Crater", "location": "Limousin, France",
     "lat": 45.8167, "lon": 0.7833, "diameter_km": 23, "age_mya": 206,
     "description": "End-Triassic impact. Local buildings made of impact breccia.",
     "impactor": "Asteroid ~1 km", "confirmed": True},
    {"name": "Bosumtwi Crater", "location": "Ashanti, Ghana",
     "lat": 6.5042, "lon": -1.4083, "diameter_km": 10.5, "age_mya": 1.07,
     "description": "Sacred lake crater, only natural lake in Ghana.",
     "impactor": "Asteroid ~0.5 km", "confirmed": True},
    {"name": "Lonar Crater", "location": "Maharashtra, India",
     "lat": 19.9767, "lon": 76.5067, "diameter_km": 1.8, "age_mya": 0.052,
     "description": "Only hypervelocity impact crater in basalt. Saline + alkaline lake.",
     "impactor": "Asteroid ~60 m", "confirmed": True},
    {"name": "Wolfe Creek Crater", "location": "Western Australia",
     "lat": -19.1728, "lon": 127.7975, "diameter_km": 0.875, "age_mya": 0.3,
     "description": "Well-preserved crater in Australian outback, second largest with meteorite fragments.",
     "impactor": "Iron meteorite ~15 m", "confirmed": True},
]

# ═══════════════════════════════════════════════════════════════
# MODE 6: ASTRONAUT BIRTHPLACES (by country)
# ═══════════════════════════════════════════════════════════════
ASTRONAUT_COUNTRIES = [
    {"country": "United States", "lat": 38.9072, "lon": -77.0369, "astronauts": 360,
     "agency": "NASA", "first_astronaut": "Alan Shepard (1961)",
     "description": "Most astronauts by far, from Mercury to Artemis programs."},
    {"country": "Russia / Soviet Union", "lat": 55.7558, "lon": 37.6173, "astronauts": 128,
     "agency": "Roscosmos", "first_astronaut": "Yuri Gagarin (1961)",
     "description": "First human in space. Rich spaceflight heritage from Vostok to ISS."},
    {"country": "China", "lat": 39.9042, "lon": 116.4074, "astronauts": 22,
     "agency": "CNSA", "first_astronaut": "Yang Liwei (2003)",
     "description": "Growing taikonaut corps for Tiangong space station."},
    {"country": "Japan", "lat": 35.6762, "lon": 139.6503, "astronauts": 14,
     "agency": "JAXA", "first_astronaut": "Toyohiro Akiyama (1990)",
     "description": "Active ISS participants, Kibo module operators."},
    {"country": "Canada", "lat": 45.4215, "lon": -75.6972, "astronauts": 14,
     "agency": "CSA", "first_astronaut": "Marc Garneau (1984)",
     "description": "Canadarm nation. Chris Hadfield commanded ISS."},
    {"country": "Germany", "lat": 52.5200, "lon": 13.4050, "astronauts": 12,
     "agency": "ESA/DLR", "first_astronaut": "Sigmund Jahn (1978, DDR)",
     "description": "Major ESA contributor. Alexander Gerst commanded ISS."},
    {"country": "France", "lat": 48.8566, "lon": 2.3522, "astronauts": 10,
     "agency": "ESA/CNES", "first_astronaut": "Jean-Loup Chretien (1982)",
     "description": "Strong spaceflight tradition. Thomas Pesquet among most popular astronauts."},
    {"country": "Italy", "lat": 41.9028, "lon": 12.4964, "astronauts": 7,
     "agency": "ESA/ASI", "first_astronaut": "Franco Malerba (1992)",
     "description": "Built ISS modules and MPLM logistics carriers. Samantha Cristoforetti set records."},
    {"country": "India", "lat": 28.6139, "lon": 77.2090, "astronauts": 2,
     "agency": "ISRO", "first_astronaut": "Rakesh Sharma (1984)",
     "description": "Gaganyaan crew program will expand India's astronaut corps."},
    {"country": "United Kingdom", "lat": 51.5074, "lon": -0.1278, "astronauts": 3,
     "agency": "ESA/UKSA", "first_astronaut": "Helen Sharman (1991)",
     "description": "Tim Peake popularized spaceflight for UK. Growing space sector."},
    {"country": "South Korea", "lat": 37.5665, "lon": 126.9780, "astronauts": 1,
     "agency": "KARI", "first_astronaut": "Yi So-yeon (2008)",
     "description": "First Korean in space via Russian Soyuz partnership."},
    {"country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "astronauts": 2,
     "agency": "ESA", "first_astronaut": "Wubbo Ockels (1985)",
     "description": "Andre Kuipers flew ISS long-duration missions."},
    {"country": "Saudi Arabia", "lat": 24.7136, "lon": 46.6753, "astronauts": 3,
     "agency": "SSC", "first_astronaut": "Sultan bin Salman (1985)",
     "description": "Recent Axiom ISS missions expanding Saudi space presence."},
    {"country": "Israel", "lat": 31.7683, "lon": 35.2137, "astronauts": 2,
     "agency": "ISA", "first_astronaut": "Ilan Ramon (2003, STS-107)",
     "description": "Ilan Ramon lost on Columbia. Eytan Stibbe flew Axiom-1."},
    {"country": "Brazil", "lat": -15.7975, "lon": -47.8919, "astronauts": 1,
     "agency": "AEB", "first_astronaut": "Marcos Pontes (2006)",
     "description": "Brazil's first astronaut flew to ISS via Soyuz."},
    {"country": "Sweden", "lat": 59.3293, "lon": 18.0686, "astronauts": 2,
     "agency": "ESA", "first_astronaut": "Christer Fuglesang (2006)",
     "description": "Fuglesang was first Swedish citizen in space."},
    {"country": "UAE", "lat": 24.4539, "lon": 54.3773, "astronauts": 2,
     "agency": "MBRSC", "first_astronaut": "Hazzaa Al Mansoori (2019)",
     "description": "Sultan Al Neyadi completed 6-month ISS mission in 2023."},
    {"country": "Denmark", "lat": 55.6761, "lon": 12.5683, "astronauts": 1,
     "agency": "ESA", "first_astronaut": "Andreas Mogensen (2015)",
     "description": "Mogensen commanded ISS Expedition 70 in 2023."},
]

# ═══════════════════════════════════════════════════════════════
# MODE 7: DEEP SPACE NETWORK
# ═══════════════════════════════════════════════════════════════
DSN_STATIONS = [
    {"name": "Goldstone Deep Space Complex (DSS-14)", "location": "Barstow, California, USA",
     "lat": 35.4267, "lon": -116.8900, "antenna": "70 m",
     "operator": "NASA/JPL", "established": 1966,
     "description": "Mars antenna, 70m dish. Primary station for deep-space communication.",
     "missions": "Voyager, Mars rovers, New Horizons, Juno"},
    {"name": "Goldstone DSS-25 (BWG)", "location": "Barstow, California, USA",
     "lat": 35.2523, "lon": -116.7942, "antenna": "34 m BWG",
     "operator": "NASA/JPL", "established": 1988,
     "description": "34m beam waveguide antenna, supports multiple missions simultaneously."},
    {"name": "Madrid Deep Space Complex (DSS-63)", "location": "Robledo de Chavela, Spain",
     "lat": 40.4314, "lon": -4.2481, "antenna": "70 m",
     "operator": "NASA/INTA", "established": 1964,
     "description": "European anchor of DSN. Covers spacecraft when Americas face away.",
     "missions": "Cassini, Mars Express, ExoMars"},
    {"name": "Madrid DSS-56", "location": "Robledo de Chavela, Spain",
     "lat": 40.4267, "lon": -4.2497, "antenna": "34 m BWG",
     "operator": "NASA/INTA", "established": 2021,
     "description": "Newest DSN antenna, Ka-band capable for future missions."},
    {"name": "Canberra Deep Space Complex (DSS-43)", "location": "Tidbinbilla, ACT, Australia",
     "lat": -35.4014, "lon": 148.9817, "antenna": "70 m",
     "operator": "NASA/CSIRO", "established": 1964,
     "description": "Only antenna able to contact Voyager 2. Upgraded 2020.",
     "missions": "Voyager 2, Perseverance, JWST"},
    {"name": "Canberra DSS-35", "location": "Tidbinbilla, ACT, Australia",
     "lat": -35.3953, "lon": 148.9819, "antenna": "34 m BWG",
     "operator": "NASA/CSIRO", "established": 2014,
     "description": "Modern 34m BWG antenna with Ka-band uplink capability."},
    {"name": "Indian Deep Space Network (IDSN-32)", "location": "Byalalu, Karnataka, India",
     "lat": 13.0340, "lon": 77.3500, "antenna": "32 m + 18 m",
     "operator": "ISRO", "established": 2008,
     "description": "ISRO's deep space tracking for Chandrayaan and Mangalyaan missions.",
     "missions": "Chandrayaan-1/2/3, Mangalyaan"},
    {"name": "ESA Malargue Station (DSA-3)", "location": "Malargue, Mendoza, Argentina",
     "lat": -35.7761, "lon": -69.3983, "antenna": "35 m",
     "operator": "ESA/ESTRACK", "established": 2012,
     "description": "ESA's third deep-space antenna, optimized for L2 and planetary missions.",
     "missions": "Gaia, JUICE, Euclid"},
    {"name": "ESA Cebreros Station (DSA-2)", "location": "Cebreros, Avila, Spain",
     "lat": 40.4528, "lon": -4.3681, "antenna": "35 m",
     "operator": "ESA/ESTRACK", "established": 2005,
     "description": "ESA deep-space station, supports Venus Express, BepiColombo.",
     "missions": "Venus Express, BepiColombo, Solar Orbiter"},
    {"name": "ESA New Norcia Station (DSA-1)", "location": "New Norcia, Western Australia",
     "lat": -31.0483, "lon": 116.1917, "antenna": "35 m",
     "operator": "ESA/ESTRACK", "established": 2002,
     "description": "ESA's first deep-space antenna, supports Rosetta, Mars Express.",
     "missions": "Rosetta, Mars Express, ExoMars TGO"},
    {"name": "JAXA Usuda Deep Space Center", "location": "Saku, Nagano, Japan",
     "lat": 36.1325, "lon": 138.3622, "antenna": "64 m",
     "operator": "JAXA", "established": 1984,
     "description": "JAXA's primary deep-space tracking station.",
     "missions": "Hayabusa, Hayabusa2, SLIM"},
    {"name": "JAXA Misasa Deep Space Station", "location": "Saku, Nagano, Japan",
     "lat": 36.1342, "lon": 138.3617, "antenna": "54 m",
     "operator": "JAXA", "established": 2021,
     "description": "New GREAT antenna for MMX and future JAXA deep-space missions.",
     "missions": "MMX (planned), Destiny+ (planned)"},
]

# ═══════════════════════════════════════════════════════════════
# MODE 8: SPACE MUSEUMS
# ═══════════════════════════════════════════════════════════════
SPACE_MUSEUMS = [
    {"name": "Smithsonian National Air and Space Museum", "city": "Washington, D.C., USA",
     "lat": 38.8882, "lon": -77.0199, "highlights": "Wright Flyer, Apollo 11 CM, Spirit of St. Louis",
     "year_opened": 1976, "visitors_year": "8 million",
     "description": "World's most-visited aerospace museum, houses Apollo 11 command module Columbia."},
    {"name": "Steven F. Udvar-Hazy Center", "city": "Chantilly, Virginia, USA",
     "lat": 38.9114, "lon": -77.4440, "highlights": "Space Shuttle Discovery, SR-71, Concorde",
     "year_opened": 2003, "visitors_year": "1.5 million",
     "description": "Smithsonian annex at Dulles, displays Space Shuttle Discovery."},
    {"name": "Kennedy Space Center Visitor Complex", "city": "Merritt Island, Florida, USA",
     "lat": 28.5240, "lon": -80.6820, "highlights": "Space Shuttle Atlantis, Saturn V, SLS",
     "year_opened": 1966, "visitors_year": "1.7 million",
     "description": "Gateway to NASA's launch operations. Shuttle Atlantis and Saturn V Center."},
    {"name": "Space Center Houston", "city": "Houston, Texas, USA",
     "lat": 29.5519, "lon": -95.0981, "highlights": "Shuttle replica Independence, Saturn V, Mission Control",
     "year_opened": 1992, "visitors_year": "1.2 million",
     "description": "Official visitor center of NASA JSC. Restored Apollo-era Mission Control."},
    {"name": "Cosmosphere (Kansas)", "city": "Hutchinson, Kansas, USA",
     "lat": 38.0608, "lon": -97.9298, "highlights": "Liberty Bell 7, Vostok, SR-71 cockpit",
     "year_opened": 1962, "visitors_year": "200,000",
     "description": "Largest combined collection of US and Russian space artifacts outside DC/Moscow."},
    {"name": "U.S. Space & Rocket Center", "city": "Huntsville, Alabama, USA",
     "lat": 34.7112, "lon": -86.6539, "highlights": "Saturn V, Space Camp, Pathfinder shuttle",
     "year_opened": 1970, "visitors_year": "800,000",
     "description": "Home of Space Camp. Full Saturn V and Pathfinder shuttle stack on display."},
    {"name": "Memorial Museum of Cosmonautics", "city": "Moscow, Russia",
     "lat": 55.8228, "lon": 37.6397, "highlights": "Vostok capsule, Sputnik replica, Buran cabin",
     "year_opened": 1981, "visitors_year": "700,000",
     "description": "Located at base of Monument to Conquerors of Space. Soviet space history."},
    {"name": "Cite de l'Espace", "city": "Toulouse, France",
     "lat": 43.5864, "lon": 1.4914, "highlights": "Ariane 5, Soyuz capsule, Mir station replica",
     "year_opened": 1997, "visitors_year": "400,000",
     "description": "Europe's premier space theme park, full-size Ariane 5 and Mir replica."},
    {"name": "Science Museum - Space Gallery", "city": "London, UK",
     "lat": 51.4978, "lon": -0.1745, "highlights": "Apollo 10 CM, Soyuz TMA-19M, V-2 engine",
     "year_opened": 1857, "visitors_year": "3.3 million (total museum)",
     "description": "Houses Apollo 10 command module and Tim Peake's Soyuz capsule."},
    {"name": "Deutsches Museum - Aerospace", "city": "Munich, Germany",
     "lat": 48.1298, "lon": 11.5833, "highlights": "V-2, Spacelab, Wright Brothers replica",
     "year_opened": 1925, "visitors_year": "1.5 million (total museum)",
     "description": "Extensive aerospace collection including original Spacelab module."},
    {"name": "Pima Air & Space Museum", "city": "Tucson, Arizona, USA",
     "lat": 32.1715, "lon": -110.8565, "highlights": "SR-71, B-52, 400+ aircraft",
     "year_opened": 1976, "visitors_year": "250,000",
     "description": "One of world's largest non-government-funded aerospace museums."},
    {"name": "China Science and Technology Museum", "city": "Beijing, China",
     "lat": 39.9927, "lon": 116.3979, "highlights": "Shenzhou capsule, Long March models, Tiangong",
     "year_opened": 1988, "visitors_year": "3 million",
     "description": "Houses Shenzhou spacecraft and Chinese space program exhibits."},
    {"name": "JAXA Tsukuba Space Center", "city": "Tsukuba, Ibaraki, Japan",
     "lat": 36.0655, "lon": 140.1312, "highlights": "Kibo module mockup, H-II rocket, ISS exhibit",
     "year_opened": 1972, "visitors_year": "400,000",
     "description": "JAXA's main hub, free exhibition hall with rocket garden and ISS Kibo replica."},
    {"name": "Euro Space Center", "city": "Transinne, Belgium",
     "lat": 50.0000, "lon": 5.2500, "highlights": "Space shuttle simulator, ISS mockup, astronaut training",
     "year_opened": 1991, "visitors_year": "80,000",
     "description": "Interactive space education center with astronaut training simulators."},
]

# ═══════════════════════════════════════════════════════════════
# MODE 9: SATELLITE GROUND STATIONS
# ═══════════════════════════════════════════════════════════════
GROUND_STATIONS = [
    {"name": "ESA Kiruna Station", "location": "Kiruna, Sweden",
     "lat": 67.8578, "lon": 20.9644, "operator": "ESA/ESTRACK",
     "antennas": "15m + 13m + multiple", "primary_use": "Polar orbit tracking",
     "description": "Primary ESA station for polar-orbiting satellites due to high latitude."},
    {"name": "ESA Redu Station", "location": "Redu, Belgium",
     "lat": 50.0017, "lon": 5.1464, "operator": "ESA/ESTRACK",
     "antennas": "15m + 13.5m", "primary_use": "Telecom satellite testing",
     "description": "ESA ground station specializing in telecommunications satellite operations."},
    {"name": "ESA Villafranca Station (VILSPA)", "location": "Madrid, Spain",
     "lat": 40.4444, "lon": -3.9528, "operator": "ESA/ESTRACK",
     "antennas": "15m", "primary_use": "Science missions",
     "description": "Supports ESA science missions including XMM-Newton and INTEGRAL."},
    {"name": "ESA Kourou Station", "location": "Kourou, French Guiana",
     "lat": 5.2514, "lon": -52.8047, "operator": "ESA/ESTRACK",
     "antennas": "15m", "primary_use": "Launch tracking",
     "description": "Provides tracking for Ariane and Vega launches from CSG."},
    {"name": "ESA Maspalomas Station", "location": "Gran Canaria, Spain",
     "lat": 27.7628, "lon": -15.6339, "operator": "ESA/ESTRACK",
     "antennas": "15m", "primary_use": "Earth observation",
     "description": "Key station for Sentinel/Copernicus Earth observation data downlink."},
    {"name": "NASA White Sands Complex", "location": "Las Cruces, New Mexico, USA",
     "lat": 32.5428, "lon": -106.6122, "operator": "NASA/TDRS",
     "antennas": "Multiple 18m TDRS terminals", "primary_use": "TDRS relay",
     "description": "Ground terminal for NASA's Tracking and Data Relay Satellite system."},
    {"name": "NASA Wallops Flight Facility", "location": "Wallops Island, Virginia, USA",
     "lat": 37.9380, "lon": -75.4660, "operator": "NASA/GSFC",
     "antennas": "11m + mobile", "primary_use": "Sounding rockets, EO data",
     "description": "Suborbital and small orbital launches, satellite tracking."},
    {"name": "KSAT Svalbard Satellite Station (SvalSat)", "location": "Svalbard, Norway",
     "lat": 78.2297, "lon": 15.3975, "operator": "KSAT",
     "antennas": "100+ antennas (multi-mission)", "primary_use": "Polar orbit data downlink",
     "description": "World's most northerly ground station, sees every polar-orbiting satellite every orbit."},
    {"name": "KSAT TrollSat", "location": "Queen Maud Land, Antarctica",
     "lat": -72.0117, "lon": 2.5350, "operator": "KSAT",
     "antennas": "7.3m + 3.7m", "primary_use": "Antarctic polar tracking",
     "description": "Antarctic ground station, partner to SvalSat for complete polar coverage."},
    {"name": "SSC North Pole Station", "location": "Inuvik, NWT, Canada",
     "lat": 68.3194, "lon": -133.5494, "operator": "SSC (Swedish Space Corp)",
     "antennas": "13m (multiple)", "primary_use": "Polar orbit support",
     "description": "Arctic ground station supporting Earth observation missions."},
    {"name": "Hartebeesthoek Radio Observatory (HartRAO)", "location": "Gauteng, South Africa",
     "lat": -25.8900, "lon": 27.6853, "operator": "NRF/South Africa",
     "antennas": "26m + 15m", "primary_use": "VLBI, satellite tracking",
     "description": "Former NASA tracking station, now radio astronomy and space geodesy."},
    {"name": "Dongara Ground Station", "location": "Dongara, Western Australia",
     "lat": -29.2506, "lon": 115.3469, "operator": "SSC",
     "antennas": "13m (multiple)", "primary_use": "LEO satellite support",
     "description": "Swedish Space Corporation operated station in Australia."},
    {"name": "McMurdo Ground Station", "location": "McMurdo Station, Antarctica",
     "lat": -77.8419, "lon": 166.6863, "operator": "NASA",
     "antennas": "10m TDRS terminal", "primary_use": "Polar relay",
     "description": "NASA TDRS ground terminal at McMurdo for Antarctic satellite relay."},
    {"name": "Santiago Satellite Station", "location": "Santiago, Chile",
     "lat": -33.1511, "lon": -70.6667, "operator": "ESA/ESTRACK",
     "antennas": "15m", "primary_use": "LEO support, Galileo",
     "description": "ESA tracking station supporting Copernicus and Galileo programs."},
]

# ═══════════════════════════════════════════════════════════════
# MODE 10: MOON & MARS LANDING SITES (mapped to Earth coords)
# ═══════════════════════════════════════════════════════════════
MOON_LANDINGS = [
    {"name": "Apollo 11 - Tranquility Base", "body": "Moon",
     "real_lat": 0.6744, "real_lon": 23.4731,
     "earth_lat": 0.6744, "earth_lon": 23.4731,
     "date": "1969-07-20", "mission": "Apollo 11", "country": "USA",
     "description": "First crewed Moon landing. Neil Armstrong and Buzz Aldrin walked on the Moon."},
    {"name": "Apollo 12 - Ocean of Storms", "body": "Moon",
     "real_lat": -3.0124, "real_lon": -23.4216,
     "earth_lat": -3.0124, "earth_lon": -23.4216,
     "date": "1969-11-19", "mission": "Apollo 12", "country": "USA",
     "description": "Precision landing near Surveyor 3 probe. Pete Conrad and Alan Bean."},
    {"name": "Apollo 14 - Fra Mauro", "body": "Moon",
     "real_lat": -3.6453, "real_lon": -17.4714,
     "earth_lat": -3.6453, "earth_lon": -17.4714,
     "date": "1971-02-05", "mission": "Apollo 14", "country": "USA",
     "description": "Alan Shepard hit golf balls on the Moon. Returned 42 kg of samples."},
    {"name": "Apollo 15 - Hadley Rille", "body": "Moon",
     "real_lat": 26.1322, "real_lon": 3.6339,
     "earth_lat": 26.1322, "earth_lon": 3.6339,
     "date": "1971-07-30", "mission": "Apollo 15", "country": "USA",
     "description": "First use of Lunar Roving Vehicle. Genesis Rock discovery."},
    {"name": "Apollo 16 - Descartes Highlands", "body": "Moon",
     "real_lat": -8.9734, "real_lon": 15.5011,
     "earth_lat": -8.9734, "earth_lon": 15.5011,
     "date": "1972-04-21", "mission": "Apollo 16", "country": "USA",
     "description": "Highland terrain exploration. John Young and Charles Duke."},
    {"name": "Apollo 17 - Taurus-Littrow", "body": "Moon",
     "real_lat": 20.1911, "real_lon": 30.7723,
     "earth_lat": 20.1911, "earth_lon": 30.7723,
     "date": "1972-12-11", "mission": "Apollo 17", "country": "USA",
     "description": "Last crewed Moon mission. Gene Cernan last person on Moon. Orange soil discovery."},
    {"name": "Luna 9 - Oceanus Procellarum", "body": "Moon",
     "real_lat": 7.08, "real_lon": -64.37,
     "earth_lat": 7.08, "earth_lon": -64.37,
     "date": "1966-02-03", "mission": "Luna 9", "country": "USSR",
     "description": "First soft landing on the Moon. Proved surface could support a lander."},
    {"name": "Chang'e 4 - Von Karman Crater (far side)", "body": "Moon",
     "real_lat": -45.4561, "real_lon": 177.5885,
     "earth_lat": -45.4561, "earth_lon": 177.5885,
     "date": "2019-01-03", "mission": "Chang'e 4", "country": "China",
     "description": "First landing on the lunar far side. Yutu-2 rover."},
    {"name": "Chandrayaan-3 - Shiv Shakti Point", "body": "Moon",
     "real_lat": -69.3730, "real_lon": 32.3190,
     "earth_lat": -69.3730, "earth_lon": 32.3190,
     "date": "2023-08-23", "mission": "Chandrayaan-3", "country": "India",
     "description": "India's first successful lunar landing near the south pole."},
    {"name": "SLIM - Shioli Crater", "body": "Moon",
     "real_lat": -13.3160, "real_lon": 25.2490,
     "earth_lat": -13.3160, "earth_lon": 25.2490,
     "date": "2024-01-19", "mission": "SLIM", "country": "Japan",
     "description": "Japan's precision lander, landed upside down but still operated."},
]

MARS_LANDINGS = [
    {"name": "Curiosity Rover - Gale Crater", "body": "Mars",
     "real_lat": -4.5895, "real_lon": 137.4417,
     "earth_lat": -4.5895, "earth_lon": 137.4417,
     "date": "2012-08-06", "mission": "MSL Curiosity", "country": "USA",
     "description": "Car-sized rover exploring Mount Sharp. Discovered ancient habitable conditions."},
    {"name": "Perseverance Rover - Jezero Crater", "body": "Mars",
     "real_lat": 18.4447, "real_lon": 77.4508,
     "earth_lat": 18.4447, "earth_lon": 77.4508,
     "date": "2021-02-18", "mission": "Mars 2020 / Perseverance", "country": "USA",
     "description": "Searching for ancient microbial life. Caching samples for Mars Sample Return."},
    {"name": "InSight Lander - Elysium Planitia", "body": "Mars",
     "real_lat": 4.5024, "real_lon": 135.6234,
     "earth_lat": 4.5024, "earth_lon": 135.6234,
     "date": "2018-11-26", "mission": "InSight", "country": "USA",
     "description": "Studied Mars interior with seismometer. Detected marsquakes. Ended 2022."},
    {"name": "Spirit Rover - Gusev Crater", "body": "Mars",
     "real_lat": -14.5684, "real_lon": 175.4726,
     "earth_lat": -14.5684, "earth_lon": 175.4726,
     "date": "2004-01-04", "mission": "MER-A Spirit", "country": "USA",
     "description": "Operated for 6 years (90-day mission). Got stuck in soft soil 2009."},
    {"name": "Opportunity Rover - Meridiani Planum", "body": "Mars",
     "real_lat": -1.9462, "real_lon": -5.5271,
     "earth_lat": -1.9462, "earth_lon": -5.5271,
     "date": "2004-01-25", "mission": "MER-B Opportunity", "country": "USA",
     "description": "Marathon rover, operated 15 years (90-day mission). Dust storm ended it 2018."},
    {"name": "Zhurong Rover - Utopia Planitia", "body": "Mars",
     "real_lat": 25.0660, "real_lon": 109.9258,
     "earth_lat": 25.0660, "earth_lon": 109.9258,
     "date": "2021-05-14", "mission": "Tianwen-1 / Zhurong", "country": "China",
     "description": "China's first Mars rover. Explored for ~1 year before entering hibernation."},
    {"name": "Viking 1 - Chryse Planitia", "body": "Mars",
     "real_lat": 22.2700, "real_lon": -47.9400,
     "earth_lat": 22.2700, "earth_lon": -47.9400,
     "date": "1976-07-20", "mission": "Viking 1", "country": "USA",
     "description": "First successful Mars landing. Operated over 6 years. Searched for life."},
    {"name": "Viking 2 - Utopia Planitia", "body": "Mars",
     "real_lat": 47.6700, "real_lon": -225.7400,
     "earth_lat": 47.6700, "earth_lon": 134.2600,
     "date": "1976-09-03", "mission": "Viking 2", "country": "USA",
     "description": "Second Mars lander, imaged frost on the Martian surface."},
    {"name": "Phoenix Lander - Green Valley", "body": "Mars",
     "real_lat": 68.2188, "real_lon": -125.7492,
     "earth_lat": 68.2188, "earth_lon": -125.7492,
     "date": "2008-05-25", "mission": "Phoenix", "country": "USA",
     "description": "Confirmed water ice in Martian soil near the north pole."},
    {"name": "Pathfinder / Sojourner - Ares Vallis", "body": "Mars",
     "real_lat": 19.0970, "real_lon": -33.2100,
     "earth_lat": 19.0970, "earth_lon": -33.2100,
     "date": "1997-07-04", "mission": "Mars Pathfinder", "country": "USA",
     "description": "First Mars rover (Sojourner). Demonstrated airbag landing system."},
]


# ═══════════════════════════════════════════════════════════════
# ISS LIVE POSITION API (Free)
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def _fetch_iss_position():
    """Fetch current ISS position from Open Notify API."""
    try:
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "lat": float(data["iss_position"]["latitude"]),
            "lon": float(data["iss_position"]["longitude"]),
            "timestamp": data["timestamp"],
        }
    except Exception as e:
        logger.warning("ISS position API failed: %s", e)
        return None


@st.cache_data(ttl=3600)
def _fetch_people_in_space():
    """Fetch list of people currently in space from Open Notify API."""
    try:
        resp = requests.get("http://api.open-notify.org/astros.json", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("people", []), data.get("number", 0)
    except Exception as e:
        logger.warning("People in space API failed: %s", e)
        return [], 0


# ═══════════════════════════════════════════════════════════════
# HELPER: Build a themed folium map
# ═══════════════════════════════════════════════════════════════
def _create_dark_map(center=None, zoom=2):
    """Create a folium map with dark CartoDB tiles."""
    if center is None:
        center = [20, 0]
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark Matter",
        name="Dark Base",
    ).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════
# HELPER: Styled matplotlib chart
# ═══════════════════════════════════════════════════════════════
def _style_ax(fig, ax, xlabel="", ylabel=""):
    """Apply TerraScout dark theme to a matplotlib figure/axes."""
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_SURFACE)
    ax.set_xlabel(xlabel, color=TEXT_SECONDARY, fontsize=10)
    ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(axis="both", colors=TEXT_SECONDARY, labelsize=9)
    ax.grid(True, color=BORDER_COLOR, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)
    ax.title.set_color(TEXT_PRIMARY)


def _render_csv_download(df, filename, label, key):
    """Render a CSV download button for a dataframe."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label,
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


# ═══════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_launch_sites():
    """Mode 1: Space Launch Sites worldwide."""
    st.markdown("#### Space Launch Sites")
    st.markdown(
        "Major spaceports and launch complexes around the world, from historic "
        "Cold War sites to modern commercial pads."
    )

    # Filters
    countries = sorted(set(s["country"] for s in LAUNCH_SITES))
    sel_countries = st.multiselect(
        "Filter by country", countries, default=countries, key="sp_launch_countries"
    )
    sel_status = st.multiselect(
        "Status", ["Active", "Inactive"], default=["Active"], key="sp_launch_status"
    )

    filtered = [
        s for s in LAUNCH_SITES
        if s["country"] in sel_countries and s["status"] in sel_status
    ]

    if not filtered:
        st.warning("No launch sites match your filters.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Sites", len(filtered))
    with c2:
        active = sum(1 for s in filtered if s["status"] == "Active")
        st.metric("Active", active)
    with c3:
        n_countries = len(set(s["country"] for s in filtered))
        st.metric("Countries", n_countries)
    with c4:
        oldest = min(s["first_launch"] for s in filtered)
        st.metric("Oldest Launch", oldest)

    # Map
    m = _create_dark_map(center=[20, 0], zoom=2)
    for site in filtered:
        color = ACCENT_CYAN if site["status"] == "Active" else ACCENT_RED
        popup_html = (
            f'<div style="max-width:250px;">'
            f'<strong>{escape(site["name"])}</strong><br/>'
            f'<em>{escape(site["country"])} &mdash; {escape(site["operator"])}</em><br/>'
            f'<span style="font-size:0.85rem;">{escape(site["description"])}</span><br/>'
            f'<span style="font-size:0.8rem;">First launch: {site["first_launch"]}</span><br/>'
            f'<span style="font-size:0.8rem;">Notable: {escape(site.get("notable", ""))}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(site["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # ISS live position overlay
    iss = _fetch_iss_position()
    if iss:
        st.markdown(
            f"**ISS Live Position:** {iss['lat']:.4f}, {iss['lon']:.4f}"
        )

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Launch Sites Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "space_launch_sites.csv",
                         f"Download {len(df)} Launch Sites (CSV)", "sp_dl_launch")


def _render_observatories():
    """Mode 2: Great Observatories."""
    st.markdown("#### Great Astronomical Observatories")
    st.markdown(
        "The world's most powerful ground-based telescopes, from historic giants "
        "to next-generation extremely large telescopes."
    )

    # Filter by type
    types = sorted(set(o["type"] for o in GREAT_OBSERVATORIES))
    sel_types = st.multiselect("Filter by type", types, default=types, key="sp_obs_types")

    filtered = [o for o in GREAT_OBSERVATORIES if o["type"] in sel_types]
    if not filtered:
        st.warning("No observatories match your filters.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Observatories", len(filtered))
    with c2:
        altitudes = [o["altitude_m"] for o in filtered]
        st.metric("Max Altitude", f"{max(altitudes):,} m")
    with c3:
        oldest = min(o["year"] for o in filtered)
        st.metric("Oldest", oldest)
    with c4:
        newest = max(o["year"] for o in filtered)
        st.metric("Newest/Planned", newest)

    # Map
    m = _create_dark_map(center=[10, -30], zoom=2)
    for obs in filtered:
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(obs["name"])}</strong><br/>'
            f'<em>{escape(obs["location"])}</em><br/>'
            f'Type: {escape(obs["type"])} | Aperture: {escape(obs["aperture"])}<br/>'
            f'Altitude: {obs["altitude_m"]:,} m | Year: {obs["year"]}<br/>'
            f'<span style="font-size:0.85rem;">{escape(obs["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=7,
            color=ACCENT_VIOLET,
            fill=True,
            fill_color=ACCENT_VIOLET,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(obs["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Altitude chart
    st.markdown("#### Observatory Altitudes")
    fig, ax = plt.subplots(figsize=(10, 4))
    _style_ax(fig, ax, xlabel="", ylabel="Altitude (m)")
    names = [o["name"][:25] for o in sorted(filtered, key=lambda x: x["altitude_m"], reverse=True)]
    alts = [o["altitude_m"] for o in sorted(filtered, key=lambda x: x["altitude_m"], reverse=True)]
    bars = ax.barh(names, alts, color=ACCENT_VIOLET, alpha=0.8, edgecolor=BG_DARK)
    ax.tick_params(axis="y", labelsize=7)
    for bar, val in zip(bars, alts):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
                f"{val:,}m", va="center", color=TEXT_SECONDARY, fontsize=7)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Observatories Data ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "observatories.csv",
                         f"Download {len(df)} Observatories (CSV)", "sp_dl_obs")


def _render_radio_telescopes():
    """Mode 3: Radio Telescopes."""
    st.markdown("#### Radio Telescopes & Arrays")
    st.markdown(
        "The world's major radio telescopes and interferometric arrays, "
        "listening to the cosmos at wavelengths invisible to the eye."
    )

    # Filter by type
    rt_types = sorted(set(r["type"] for r in RADIO_TELESCOPES))
    sel_types = st.multiselect("Filter by type", rt_types, default=rt_types, key="sp_radio_types")

    filtered = [r for r in RADIO_TELESCOPES if r["type"] in sel_types]
    if not filtered:
        st.warning("No radio telescopes match your filters.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Facilities", len(filtered))
    with c2:
        total_dishes = sum(r["dishes"] for r in filtered if isinstance(r["dishes"], int))
        st.metric("Total Antennas/Dishes", f"{total_dishes:,}")
    with c3:
        operators = len(set(r["operator"] for r in filtered))
        st.metric("Operators", operators)
    with c4:
        oldest_rt = min(r["year"] for r in filtered)
        st.metric("Oldest", oldest_rt)

    # Map
    m = _create_dark_map(center=[20, 0], zoom=2)
    for rt in filtered:
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(rt["name"])}</strong><br/>'
            f'<em>{escape(rt["location"])}</em><br/>'
            f'Type: {escape(rt["type"])} | Dishes: {rt["dishes"]}<br/>'
            f'Size: {escape(rt["dish_size"])} | Baseline: {escape(rt["baseline"])}<br/>'
            f'Operator: {escape(rt["operator"])} | Year: {rt["year"]}<br/>'
            f'<span style="font-size:0.85rem;">{escape(rt["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[rt["lat"], rt["lon"]],
            radius=8,
            color=ACCENT_EMERALD,
            fill=True,
            fill_color=ACCENT_EMERALD,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(rt["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Timeline chart
    st.markdown("#### Radio Telescope Timeline")
    fig, ax = plt.subplots(figsize=(10, 4))
    _style_ax(fig, ax, xlabel="Year Commissioned", ylabel="")
    sorted_rt = sorted(filtered, key=lambda x: x["year"])
    years = [r["year"] for r in sorted_rt]
    names_rt = [r["name"][:30] for r in sorted_rt]
    ax.barh(names_rt, years, color=ACCENT_EMERALD, alpha=0.8, edgecolor=BG_DARK)
    ax.set_xlim(min(years) - 5, max(years) + 5)
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Radio Telescopes Data ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "radio_telescopes.csv",
                         f"Download {len(df)} Radio Telescopes (CSV)", "sp_dl_radio")


def _render_space_debris():
    """Mode 4: Space Debris Tracking."""
    st.markdown("#### Space Debris Tracking")
    st.markdown(
        "Overview of tracked orbital debris zones, major collision events, "
        "and the growing space junk problem in Earth orbit."
    )

    # Filter by category
    categories = sorted(set(d["category"] for d in SPACE_DEBRIS_ZONES))
    sel_cat = st.multiselect("Orbit category", categories, default=categories, key="sp_debris_cat")

    filtered = [d for d in SPACE_DEBRIS_ZONES if d["category"] in sel_cat]
    if not filtered:
        st.warning("No debris zones match your filters.")
        return

    # Stats
    total_objects = sum(d["object_count"] for d in filtered)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tracked Zones", len(filtered))
    with c2:
        st.metric("Total Objects", f"{total_objects:,}")
    with c3:
        high_risk = sum(1 for d in filtered if d["risk"] in ["High", "Very High"])
        st.metric("High-Risk Zones", high_risk)
    with c4:
        max_alt = max(d["alt_max_km"] for d in filtered)
        st.metric("Max Altitude", f"{max_alt:,} km")

    # Debris density chart (altitude vs object count)
    st.markdown("#### Debris Density by Altitude")
    active_zones = [d for d in filtered if d["object_count"] > 0]
    if active_zones:
        fig, ax = plt.subplots(figsize=(10, 5))
        _style_ax(fig, ax, xlabel="Altitude Range (km)", ylabel="Object Count")
        zone_labels = [f"{d['name'][:30]}" for d in active_zones]
        counts = [d["object_count"] for d in active_zones]
        risk_colors = {
            "Very High": ACCENT_RED,
            "High": ACCENT_ORANGE,
            "Moderate": ACCENT_AMBER,
            "Low": ACCENT_EMERALD,
            "None": ACCENT_CYAN,
            "Decayed": TEXT_MUTED,
        }
        bar_colors = [risk_colors.get(d["risk"], ACCENT_CYAN) for d in active_zones]
        bars = ax.barh(zone_labels, counts, color=bar_colors, alpha=0.85, edgecolor=BG_DARK)
        ax.tick_params(axis="y", labelsize=7)
        for bar, val in zip(bars, counts):
            ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height() / 2,
                    f"{val:,}", va="center", color=TEXT_SECONDARY, fontsize=7)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Color legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Very High Risk</span>
        <span style="color:#f97316; font-size:0.8rem;">&#9679; High Risk</span>
        <span style="color:#f59e0b; font-size:0.8rem;">&#9679; Moderate Risk</span>
        <span style="color:#10b981; font-size:0.8rem;">&#9679; Low Risk</span>
        <span style="color:#5a6580; font-size:0.8rem;">&#9679; Decayed</span>
    </div>
    """, unsafe_allow_html=True)

    # Map (show debris source events and notable orbit zones)
    m = _create_dark_map(center=[20, 0], zoom=2)
    for dz in filtered:
        if dz["object_count"] == 0 and dz["category"] == "Historical":
            color = TEXT_MUTED
        elif dz["risk"] == "Very High":
            color = ACCENT_RED
        elif dz["risk"] == "High":
            color = ACCENT_ORANGE
        elif dz["risk"] == "Moderate":
            color = ACCENT_AMBER
        else:
            color = ACCENT_EMERALD
        radius = max(4, min(15, dz["object_count"] / 1000))
        popup_html = (
            f'<div style="max-width:250px;">'
            f'<strong>{escape(dz["name"])}</strong><br/>'
            f'Category: {escape(dz["category"])} | Risk: {escape(dz["risk"])}<br/>'
            f'Altitude: {dz["alt_min_km"]:,}-{dz["alt_max_km"]:,} km<br/>'
            f'Objects: {dz["object_count"]:,}<br/>'
            f'<span style="font-size:0.85rem;">{escape(dz["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[dz["lat"], dz["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(dz["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    st.info(
        "Note: Debris zones are represented at arbitrary ground locations for visualization. "
        "Actual debris orbits the Earth at the listed altitudes."
    )

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Debris Zone Data ({len(df)} zones)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "space_debris_zones.csv",
                         f"Download {len(df)} Debris Zones (CSV)", "sp_dl_debris")


def _render_impact_craters():
    """Mode 5: Meteorite Impact Craters."""
    st.markdown("#### Meteorite Impact Craters")
    st.markdown(
        "Confirmed impact structures on Earth, from the massive Vredefort dome "
        "to well-preserved smaller craters like Barringer (Meteor Crater)."
    )

    # Diameter filter
    min_diam = st.slider(
        "Minimum diameter (km)", 0.0, 300.0, 0.0, step=1.0, key="sp_crater_diam"
    )
    filtered = [c for c in IMPACT_CRATERS if c["diameter_km"] >= min_diam]

    if not filtered:
        st.warning("No craters match your diameter filter.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Craters", len(filtered))
    with c2:
        largest = max(c["diameter_km"] for c in filtered)
        st.metric("Largest", f"{largest} km")
    with c3:
        oldest_age = max(c["age_mya"] for c in filtered)
        st.metric("Oldest", f"{oldest_age:,} Mya")
    with c4:
        youngest_age = min(c["age_mya"] for c in filtered)
        st.metric("Youngest", f"{youngest_age:.3f} Mya")

    # Map
    m = _create_dark_map(center=[20, 0], zoom=2)
    for crater in filtered:
        radius = max(4, min(18, crater["diameter_km"] / 20))
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(crater["name"])}</strong><br/>'
            f'<em>{escape(crater["location"])}</em><br/>'
            f'Diameter: {crater["diameter_km"]} km | Age: {crater["age_mya"]:,} Mya<br/>'
            f'Impactor: {escape(crater["impactor"])}<br/>'
            f'<span style="font-size:0.85rem;">{escape(crater["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[crater["lat"], crater["lon"]],
            radius=radius,
            color=ACCENT_AMBER,
            fill=True,
            fill_color=ACCENT_AMBER,
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(crater["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Diameter comparison chart
    st.markdown("#### Crater Diameter Comparison")
    fig, ax = plt.subplots(figsize=(10, 5))
    _style_ax(fig, ax, xlabel="Diameter (km)", ylabel="")
    sorted_craters = sorted(filtered, key=lambda x: x["diameter_km"], reverse=True)
    cnames = [c["name"][:25] for c in sorted_craters]
    diams = [c["diameter_km"] for c in sorted_craters]
    bars = ax.barh(cnames, diams, color=ACCENT_AMBER, alpha=0.85, edgecolor=BG_DARK)
    ax.tick_params(axis="y", labelsize=7)
    for bar, val in zip(bars, diams):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val} km", va="center", color=TEXT_SECONDARY, fontsize=7)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Impact Craters Data ({len(df)} craters)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "impact_craters.csv",
                         f"Download {len(df)} Impact Craters (CSV)", "sp_dl_craters")


def _render_astronaut_birthplaces():
    """Mode 6: Astronaut Birthplaces by Country."""
    st.markdown("#### Astronaut Birthplaces by Country")
    st.markdown(
        "Where the world's astronauts, cosmonauts, and taikonauts come from. "
        "Bubble size represents the number of space travelers from each nation."
    )

    # Filter
    min_astronauts = st.slider(
        "Minimum astronauts per country", 1, 50, 1, key="sp_astro_min"
    )
    filtered = [a for a in ASTRONAUT_COUNTRIES if a["astronauts"] >= min_astronauts]

    if not filtered:
        st.warning("No countries match your filter.")
        return

    # Stats
    total_astro = sum(a["astronauts"] for a in filtered)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Spacefaring Nations", len(filtered))
    with c2:
        st.metric("Total Astronauts", f"{total_astro:,}")
    with c3:
        top = max(filtered, key=lambda x: x["astronauts"])
        st.metric("Most Astronauts", f'{top["country"]} ({top["astronauts"]})')
    with c4:
        agencies = len(set(a["agency"] for a in filtered))
        st.metric("Space Agencies", agencies)

    # People in space right now
    people, count = _fetch_people_in_space()
    if count > 0:
        st.markdown(f"**Currently in space:** {count} people")
        for p in people:
            st.markdown(
                f"- {escape(p.get('name', 'Unknown'))} ({escape(p.get('craft', 'Unknown'))})"
            )

    # Map
    m = _create_dark_map(center=[20, 0], zoom=2)
    for ac in filtered:
        radius = max(5, min(25, ac["astronauts"] / 10))
        popup_html = (
            f'<div style="max-width:250px;">'
            f'<strong>{escape(ac["country"])}</strong><br/>'
            f'Astronauts: {ac["astronauts"]} | Agency: {escape(ac["agency"])}<br/>'
            f'First: {escape(ac["first_astronaut"])}<br/>'
            f'<span style="font-size:0.85rem;">{escape(ac["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[ac["lat"], ac["lon"]],
            radius=radius,
            color=ACCENT_PINK,
            fill=True,
            fill_color=ACCENT_PINK,
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f'{escape(ac["country"])} ({ac["astronauts"]})',
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Bar chart
    st.markdown("#### Astronauts by Country")
    fig, ax = plt.subplots(figsize=(10, 5))
    _style_ax(fig, ax, xlabel="Astronauts", ylabel="")
    sorted_ac = sorted(filtered, key=lambda x: x["astronauts"], reverse=True)
    cnames = [a["country"] for a in sorted_ac]
    counts = [a["astronauts"] for a in sorted_ac]
    bars = ax.barh(cnames, counts, color=ACCENT_PINK, alpha=0.85, edgecolor=BG_DARK)
    ax.tick_params(axis="y", labelsize=8)
    for bar, val in zip(bars, counts):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", color=TEXT_SECONDARY, fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Astronaut Data ({len(df)} countries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "astronaut_birthplaces.csv",
                         f"Download {len(df)} Countries (CSV)", "sp_dl_astro")


def _render_deep_space_network():
    """Mode 7: Deep Space Network stations."""
    st.markdown("#### Deep Space Network & Tracking Stations")
    st.markdown(
        "The global network of large antennas that communicate with spacecraft "
        "throughout the solar system. NASA DSN, ESA ESTRACK, ISRO IDSN, and JAXA."
    )

    # Filter by operator
    operators = sorted(set(s["operator"] for s in DSN_STATIONS))
    sel_ops = st.multiselect("Filter by operator", operators, default=operators, key="sp_dsn_ops")

    filtered = [s for s in DSN_STATIONS if s["operator"] in sel_ops]
    if not filtered:
        st.warning("No stations match your filters.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Stations", len(filtered))
    with c2:
        agencies_dsn = len(set(s["operator"] for s in filtered))
        st.metric("Agencies", agencies_dsn)
    with c3:
        oldest_dsn = min(s["established"] for s in filtered)
        st.metric("Oldest", oldest_dsn)
    with c4:
        newest_dsn = max(s["established"] for s in filtered)
        st.metric("Newest", newest_dsn)

    # Map
    m = _create_dark_map(center=[20, 0], zoom=2)
    operator_colors = {
        "NASA/JPL": ACCENT_CYAN,
        "NASA/INTA": ACCENT_BLUE,
        "NASA/CSIRO": ACCENT_BLUE,
        "ISRO": ACCENT_ORANGE,
        "ESA/ESTRACK": ACCENT_VIOLET,
        "JAXA": ACCENT_EMERALD,
    }
    for stn in filtered:
        color = operator_colors.get(stn["operator"], ACCENT_CYAN)
        missions_str = escape(stn.get("missions", "Multiple missions"))
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(stn["name"])}</strong><br/>'
            f'<em>{escape(stn["location"])}</em><br/>'
            f'Antenna: {escape(stn["antenna"])} | Est. {stn["established"]}<br/>'
            f'Operator: {escape(stn["operator"])}<br/>'
            f'Missions: {missions_str}<br/>'
            f'<span style="font-size:0.85rem;">{escape(stn["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[stn["lat"], stn["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(stn["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#06b6d4; font-size:0.8rem;">&#9679; NASA DSN</span>
        <span style="color:#3b82f6; font-size:0.8rem;">&#9679; NASA Partners</span>
        <span style="color:#8b5cf6; font-size:0.8rem;">&#9679; ESA ESTRACK</span>
        <span style="color:#10b981; font-size:0.8rem;">&#9679; JAXA</span>
        <span style="color:#f97316; font-size:0.8rem;">&#9679; ISRO</span>
    </div>
    """, unsafe_allow_html=True)

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"DSN Stations Data ({len(df)} stations)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "deep_space_network.csv",
                         f"Download {len(df)} DSN Stations (CSV)", "sp_dl_dsn")


def _render_space_museums():
    """Mode 8: Space Museums worldwide."""
    st.markdown("#### Space Museums & Visitor Centers")
    st.markdown(
        "The best places on Earth to experience space exploration history, "
        "from the Smithsonian to Kennedy Space Center and beyond."
    )

    filtered = SPACE_MUSEUMS  # Show all by default

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Museums", len(filtered))
    with c2:
        oldest_museum = min(m["year_opened"] for m in filtered)
        st.metric("Oldest", oldest_museum)
    with c3:
        countries_museum = len(set(m["city"].split(",")[-1].strip() for m in filtered))
        st.metric("Countries", countries_museum)
    with c4:
        st.metric("Newest", max(m["year_opened"] for m in filtered))

    # Map
    m = _create_dark_map(center=[30, -20], zoom=2)
    for museum in filtered:
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(museum["name"])}</strong><br/>'
            f'<em>{escape(museum["city"])}</em><br/>'
            f'Opened: {museum["year_opened"]} | Visitors: {escape(museum["visitors_year"])}/yr<br/>'
            f'Highlights: {escape(museum["highlights"])}<br/>'
            f'<span style="font-size:0.85rem;">{escape(museum["description"])}</span>'
            f'</div>'
        )
        folium.Marker(
            location=[museum["lat"], museum["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(museum["name"]),
            icon=folium.Icon(color="purple", icon="star", prefix="fa"),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Highlight cards
    st.markdown("#### Featured Museums")
    for i in range(0, min(6, len(filtered)), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(filtered):
                mus = filtered[idx]
                with col:
                    st.markdown(
                        f'<div class="bio-card" style="margin-bottom:0.5rem;">'
                        f'<div style="color:{TEXT_PRIMARY}; font-weight:600; font-size:0.9rem;">'
                        f'{escape(mus["name"])}</div>'
                        f'<div style="color:{TEXT_SECONDARY}; font-size:0.8rem;">'
                        f'{escape(mus["city"])}</div>'
                        f'<div style="color:{TEXT_MUTED}; font-size:0.75rem; margin-top:0.25rem;">'
                        f'{escape(mus["highlights"])}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Museums Data ({len(df)} museums)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "space_museums.csv",
                         f"Download {len(df)} Museums (CSV)", "sp_dl_museums")


def _render_ground_stations():
    """Mode 9: Satellite Ground Stations."""
    st.markdown("#### Satellite Ground Stations")
    st.markdown(
        "Earth-based tracking and communication stations that support satellite "
        "operations, from Arctic Svalbard to Antarctic McMurdo."
    )

    # Filter by operator
    gs_operators = sorted(set(g["operator"] for g in GROUND_STATIONS))
    sel_gs_ops = st.multiselect(
        "Filter by operator", gs_operators, default=gs_operators, key="sp_gs_ops"
    )

    filtered = [g for g in GROUND_STATIONS if g["operator"] in sel_gs_ops]
    if not filtered:
        st.warning("No stations match your filters.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Stations", len(filtered))
    with c2:
        n_ops = len(set(g["operator"] for g in filtered))
        st.metric("Operators", n_ops)
    with c3:
        north = max(g["lat"] for g in filtered)
        st.metric("Northernmost", f"{north:.1f} N")
    with c4:
        south = min(g["lat"] for g in filtered)
        st.metric("Southernmost", f"{abs(south):.1f} S")

    # Map
    m = _create_dark_map(center=[20, 0], zoom=2)
    gs_colors = {
        "ESA/ESTRACK": ACCENT_VIOLET,
        "NASA/TDRS": ACCENT_CYAN,
        "NASA/GSFC": ACCENT_CYAN,
        "NASA": ACCENT_CYAN,
        "KSAT": ACCENT_EMERALD,
        "SSC (Swedish Space Corp)": ACCENT_AMBER,
        "SSC": ACCENT_AMBER,
        "NRF/South Africa": ACCENT_ORANGE,
    }
    for gs in filtered:
        color = gs_colors.get(gs["operator"], ACCENT_BLUE)
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(gs["name"])}</strong><br/>'
            f'<em>{escape(gs["location"])}</em><br/>'
            f'Operator: {escape(gs["operator"])}<br/>'
            f'Antennas: {escape(gs["antennas"])}<br/>'
            f'Primary use: {escape(gs["primary_use"])}<br/>'
            f'<span style="font-size:0.85rem;">{escape(gs["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[gs["lat"], gs["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(gs["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Latitude distribution chart
    st.markdown("#### Station Latitude Distribution")
    fig, ax = plt.subplots(figsize=(10, 4))
    _style_ax(fig, ax, xlabel="Latitude", ylabel="Station Count")
    lats = [g["lat"] for g in filtered]
    ax.hist(lats, bins=12, color=ACCENT_BLUE, alpha=0.8, edgecolor=BG_DARK)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    df = pd.DataFrame(filtered)
    with st.expander(f"Ground Stations Data ({len(df)} stations)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "satellite_ground_stations.csv",
                         f"Download {len(df)} Ground Stations (CSV)", "sp_dl_gs")


def _render_moon_mars_landings():
    """Mode 10: Moon & Mars Landing Sites."""
    st.markdown("#### Moon & Mars Landing Sites")
    st.markdown(
        "Historic and recent landing sites on the Moon and Mars, mapped using "
        "their actual celestial coordinates projected onto an Earth map for visualization."
    )

    body_choice = st.radio(
        "Select body", ["Moon", "Mars", "Both"], horizontal=True, key="sp_landing_body"
    )

    moon_data = MOON_LANDINGS if body_choice in ["Moon", "Both"] else []
    mars_data = MARS_LANDINGS if body_choice in ["Mars", "Both"] else []
    all_landings = moon_data + mars_data

    if not all_landings:
        st.warning("No landing data selected.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Landings", len(all_landings))
    with c2:
        st.metric("Moon Landings", len(moon_data))
    with c3:
        st.metric("Mars Landings", len(mars_data))
    with c4:
        countries_landing = len(set(l["country"] for l in all_landings))
        st.metric("Countries", countries_landing)

    # Map
    m = _create_dark_map(center=[15, 30], zoom=2)
    for landing in all_landings:
        color = ACCENT_CYAN if landing["body"] == "Moon" else ACCENT_RED
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(landing["name"])}</strong><br/>'
            f'<em>{escape(landing["mission"])} ({escape(landing["country"])})</em><br/>'
            f'Body: {escape(landing["body"])} | Date: {escape(landing["date"])}<br/>'
            f'Coords: {landing["real_lat"]:.4f}, {landing["real_lon"]:.4f}<br/>'
            f'<span style="font-size:0.85rem;">{escape(landing["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[landing["earth_lat"], landing["earth_lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(landing["name"]),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)

    st.info(
        "Note: Landing coordinates are the actual lat/lon on the Moon or Mars. "
        "They are projected onto an Earth map for spatial comparison only."
    )

    # Legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#06b6d4; font-size:0.8rem;">&#9679; Moon Landings</span>
        <span style="color:#ef4444; font-size:0.8rem;">&#9679; Mars Landings</span>
    </div>
    """, unsafe_allow_html=True)

    # Timeline chart
    st.markdown("#### Landing Timeline")
    fig, ax = plt.subplots(figsize=(10, 5))
    _style_ax(fig, ax, xlabel="Year", ylabel="")
    sorted_landings = sorted(all_landings, key=lambda x: x["date"])
    landing_names = [l["name"][:30] for l in sorted_landings]
    landing_years = []
    for l in sorted_landings:
        try:
            landing_years.append(int(l["date"][:4]))
        except (ValueError, IndexError):
            landing_years.append(2000)
    landing_colors = [ACCENT_CYAN if l["body"] == "Moon" else ACCENT_RED for l in sorted_landings]
    ax.barh(landing_names, landing_years, color=landing_colors, alpha=0.85, edgecolor=BG_DARK)
    ax.tick_params(axis="y", labelsize=6)
    ax.set_xlim(1960, 2030)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Data table
    rows = []
    for l in all_landings:
        rows.append({
            "name": l["name"],
            "body": l["body"],
            "mission": l["mission"],
            "country": l["country"],
            "date": l["date"],
            "lat": l["real_lat"],
            "lon": l["real_lon"],
            "description": l["description"],
        })
    df = pd.DataFrame(rows)
    with st.expander(f"Landing Sites Data ({len(df)} landings)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    _render_csv_download(df, "moon_mars_landings.csv",
                         f"Download {len(df)} Landing Sites (CSV)", "sp_dl_landings")


# ═══════════════════════════════════════════════════════════════
# MAP MODE REGISTRY
# ═══════════════════════════════════════════════════════════════
SPACE_MODES = {
    "Space Launch Sites": {
        "renderer": _render_launch_sites,
        "icon": "rocket",
        "description": "Major spaceports and launch complexes worldwide",
    },
    "Great Observatories": {
        "renderer": _render_observatories,
        "icon": "telescope",
        "description": "World's most powerful ground-based telescopes",
    },
    "Radio Telescopes": {
        "renderer": _render_radio_telescopes,
        "icon": "satellite-dish",
        "description": "Radio arrays and dishes listening to the cosmos",
    },
    "Space Debris Tracking": {
        "renderer": _render_space_debris,
        "icon": "circle-nodes",
        "description": "Orbital debris zones and collision events",
    },
    "Meteorite Impact Craters": {
        "renderer": _render_impact_craters,
        "icon": "meteor",
        "description": "Confirmed impact structures on Earth",
    },
    "Astronaut Birthplaces": {
        "renderer": _render_astronaut_birthplaces,
        "icon": "user-astronaut",
        "description": "Space travelers by country of origin",
    },
    "Deep Space Network": {
        "renderer": _render_deep_space_network,
        "icon": "satellite",
        "description": "NASA DSN, ESA ESTRACK, JAXA & ISRO tracking stations",
    },
    "Space Museums": {
        "renderer": _render_space_museums,
        "icon": "building-columns",
        "description": "Top space museums and visitor centers worldwide",
    },
    "Satellite Ground Stations": {
        "renderer": _render_ground_stations,
        "icon": "tower-broadcast",
        "description": "Global satellite tracking and communication stations",
    },
    "Moon & Mars Landing Sites": {
        "renderer": _render_moon_mars_landings,
        "icon": "moon",
        "description": "Historic landing sites on the Moon and Mars",
    },
}


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════
def render_space_maps_tab():
    """Main render function for the Space Exploration Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header cyan">
        <h4>&#128640; Space Exploration Explorer</h4>
        <p>Discover launch sites, observatories, deep-space networks, impact craters,
        and landing sites across Earth and beyond &mdash; all from curated open data.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode Selector ──
    mode_names = list(SPACE_MODES.keys())
    selected_mode = st.selectbox(
        "Select Map Mode",
        mode_names,
        key="sp_mode_select",
        help="Choose a space exploration topic to explore on the map.",
    )

    # Show mode description
    mode_info = SPACE_MODES[selected_mode]
    st.markdown(
        f'<div style="color:{TEXT_SECONDARY}; font-size:0.9rem; margin-bottom:1rem;">'
        f'{escape(mode_info["description"])}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Render selected mode ──
    mode_info["renderer"]()
