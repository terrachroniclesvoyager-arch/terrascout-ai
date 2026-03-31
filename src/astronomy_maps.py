# -*- coding: utf-8 -*-
"""
TerraScout AI - Astronomy & Sky Maps Module
Provides 10 astronomy/sky map types including observatories, light pollution,
meteor impacts, launch sites, radio telescopes, dark sky reserves,
satellite ground stations, planetariums, astronomical clocks, and solar eclipses.
"""

import html
import io
import json
import datetime

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------------------------------------------------
# Data constants
# ---------------------------------------------------------------------------

WORLD_OBSERVATORIES = [
    {"name": "Mauna Kea Observatory", "lat": 19.8207, "lon": -155.4681, "alt_m": 4205, "telescope": "Keck I & II", "mirror_m": 10.0, "country": "USA"},
    {"name": "W. M. Keck Observatory", "lat": 19.8264, "lon": -155.4747, "alt_m": 4145, "telescope": "Keck I", "mirror_m": 10.0, "country": "USA"},
    {"name": "Subaru Telescope", "lat": 19.8255, "lon": -155.4761, "alt_m": 4163, "telescope": "Subaru", "mirror_m": 8.2, "country": "Japan"},
    {"name": "Gemini North", "lat": 19.8238, "lon": -155.4690, "alt_m": 4213, "telescope": "Gemini", "mirror_m": 8.1, "country": "USA"},
    {"name": "Canada-France-Hawaii Telescope", "lat": 19.8253, "lon": -155.4689, "alt_m": 4204, "telescope": "CFHT", "mirror_m": 3.6, "country": "Canada/France"},
    {"name": "Paranal Observatory", "lat": -24.6272, "lon": -70.4042, "alt_m": 2635, "telescope": "VLT (UT1-UT4)", "mirror_m": 8.2, "country": "Chile"},
    {"name": "La Silla Observatory", "lat": -29.2567, "lon": -70.7292, "alt_m": 2400, "telescope": "NTT / 3.6m", "mirror_m": 3.6, "country": "Chile"},
    {"name": "Cerro Tololo Inter-American", "lat": -30.1653, "lon": -70.8150, "alt_m": 2200, "telescope": "Blanco 4m", "mirror_m": 4.0, "country": "Chile"},
    {"name": "Gemini South", "lat": -30.2407, "lon": -70.7369, "alt_m": 2722, "telescope": "Gemini", "mirror_m": 8.1, "country": "Chile"},
    {"name": "Las Campanas Observatory", "lat": -29.0089, "lon": -70.6917, "alt_m": 2380, "telescope": "Magellan I & II", "mirror_m": 6.5, "country": "Chile"},
    {"name": "ALMA", "lat": -23.0193, "lon": -67.7532, "alt_m": 5058, "telescope": "ALMA Array (66 antennas)", "mirror_m": 12.0, "country": "Chile"},
    {"name": "Vera C. Rubin Observatory", "lat": -30.2444, "lon": -70.7494, "alt_m": 2663, "telescope": "Simonyi Survey", "mirror_m": 8.4, "country": "Chile"},
    {"name": "Palomar Observatory", "lat": 33.3564, "lon": -116.8650, "alt_m": 1712, "telescope": "Hale Telescope", "mirror_m": 5.08, "country": "USA"},
    {"name": "Mount Wilson Observatory", "lat": 34.2258, "lon": -118.0569, "alt_m": 1742, "telescope": "Hooker 100-inch", "mirror_m": 2.54, "country": "USA"},
    {"name": "Lick Observatory", "lat": 37.3414, "lon": -121.6364, "alt_m": 1283, "telescope": "Shane 3m", "mirror_m": 3.05, "country": "USA"},
    {"name": "Kitt Peak National Observatory", "lat": 31.9583, "lon": -111.5967, "alt_m": 2096, "telescope": "Mayall 4m", "mirror_m": 4.0, "country": "USA"},
    {"name": "McDonald Observatory", "lat": 30.6717, "lon": -104.0217, "alt_m": 2070, "telescope": "Hobby-Eberly", "mirror_m": 9.2, "country": "USA"},
    {"name": "Apache Point Observatory", "lat": 32.7803, "lon": -105.8200, "alt_m": 2788, "telescope": "ARC 3.5m / SDSS", "mirror_m": 3.5, "country": "USA"},
    {"name": "Lowell Observatory", "lat": 35.2028, "lon": -111.6647, "alt_m": 2210, "telescope": "Discovery Channel 4.3m", "mirror_m": 4.3, "country": "USA"},
    {"name": "Fred Lawrence Whipple Observatory", "lat": 31.6811, "lon": -110.8783, "alt_m": 2616, "telescope": "MMT 6.5m", "mirror_m": 6.5, "country": "USA"},
    {"name": "Arecibo Observatory (collapsed)", "lat": 18.3464, "lon": -66.7528, "alt_m": 497, "telescope": "Arecibo 305m (decommissioned)", "mirror_m": 305.0, "country": "Puerto Rico"},
    {"name": "Roque de los Muchachos", "lat": 28.7606, "lon": -17.8816, "alt_m": 2396, "telescope": "GTC 10.4m", "mirror_m": 10.4, "country": "Spain"},
    {"name": "Teide Observatory", "lat": 28.3003, "lon": -16.5106, "alt_m": 2390, "telescope": "IAC-80", "mirror_m": 0.82, "country": "Spain"},
    {"name": "Calar Alto Observatory", "lat": 37.2236, "lon": -2.5461, "alt_m": 2168, "telescope": "3.5m Zeiss", "mirror_m": 3.5, "country": "Spain"},
    {"name": "Isaac Newton Group", "lat": 28.7622, "lon": -17.8775, "alt_m": 2336, "telescope": "William Herschel 4.2m", "mirror_m": 4.2, "country": "UK"},
    {"name": "Royal Greenwich Observatory", "lat": 51.4769, "lon": -0.0005, "alt_m": 47, "telescope": "Historic / Prime Meridian", "mirror_m": 0.71, "country": "UK"},
    {"name": "Jodrell Bank Observatory", "lat": 53.2367, "lon": -2.3085, "alt_m": 77, "telescope": "Lovell Telescope 76m", "mirror_m": 76.0, "country": "UK"},
    {"name": "European Southern Observatory HQ", "lat": 48.2589, "lon": 11.6714, "alt_m": 530, "telescope": "ESO Headquarters", "mirror_m": 0.0, "country": "Germany"},
    {"name": "Haute-Provence Observatory", "lat": 43.9308, "lon": 5.7133, "alt_m": 650, "telescope": "1.93m", "mirror_m": 1.93, "country": "France"},
    {"name": "Pic du Midi Observatory", "lat": 42.9364, "lon": 0.1422, "alt_m": 2877, "telescope": "Bernard Lyot 2m", "mirror_m": 2.0, "country": "France"},
    {"name": "Asiago Astrophysical Observatory", "lat": 45.8486, "lon": 11.5264, "alt_m": 1045, "telescope": "Copernico 1.82m", "mirror_m": 1.82, "country": "Italy"},
    {"name": "South African Astronomical Obs.", "lat": -32.3783, "lon": 20.8106, "alt_m": 1798, "telescope": "SALT 11m", "mirror_m": 11.0, "country": "South Africa"},
    {"name": "Siding Spring Observatory", "lat": -31.2733, "lon": 149.0617, "alt_m": 1165, "telescope": "AAT 3.9m", "mirror_m": 3.9, "country": "Australia"},
    {"name": "Mount Stromlo Observatory", "lat": -35.3206, "lon": 149.0072, "alt_m": 770, "telescope": "SkyMapper 1.35m", "mirror_m": 1.35, "country": "Australia"},
    {"name": "Vainu Bappu Observatory", "lat": 12.5767, "lon": 78.8256, "alt_m": 725, "telescope": "2.34m VBT", "mirror_m": 2.34, "country": "India"},
    {"name": "Indian Astronomical Observatory", "lat": 32.7794, "lon": 78.9642, "alt_m": 4500, "telescope": "GROWTH-India 0.7m", "mirror_m": 2.0, "country": "India"},
    {"name": "Xinglong Station (NAOC)", "lat": 40.3958, "lon": 117.5750, "alt_m": 960, "telescope": "LAMOST", "mirror_m": 4.0, "country": "China"},
    {"name": "Yunnan Observatories", "lat": 25.0292, "lon": 102.7875, "alt_m": 2000, "telescope": "2.4m", "mirror_m": 2.4, "country": "China"},
    {"name": "National Astronomical Obs. Japan", "lat": 35.6747, "lon": 139.5375, "alt_m": 58, "telescope": "NAOJ HQ", "mirror_m": 0.0, "country": "Japan"},
    {"name": "Okayama Astrophysical Observatory", "lat": 34.5761, "lon": 133.5942, "alt_m": 372, "telescope": "3.8m Seimei", "mirror_m": 3.8, "country": "Japan"},
    {"name": "Bohyunsan Optical Astronomy Obs.", "lat": 36.1647, "lon": 128.9764, "alt_m": 1124, "telescope": "1.8m", "mirror_m": 1.8, "country": "South Korea"},
    {"name": "Byurakan Astrophysical Observatory", "lat": 40.3342, "lon": 44.2917, "alt_m": 1490, "telescope": "2.6m", "mirror_m": 2.6, "country": "Armenia"},
    {"name": "Special Astrophysical Observatory", "lat": 43.6467, "lon": 41.4406, "alt_m": 2070, "telescope": "BTA-6 (6m)", "mirror_m": 6.0, "country": "Russia"},
    {"name": "Crimean Astrophysical Observatory", "lat": 44.7272, "lon": 34.0158, "alt_m": 600, "telescope": "Shajn 2.6m", "mirror_m": 2.6, "country": "Ukraine"},
    {"name": "Rozhen National Astronomical Obs.", "lat": 41.6931, "lon": 24.7392, "alt_m": 1759, "telescope": "2m RCC", "mirror_m": 2.0, "country": "Bulgaria"},
    {"name": "LIGO Hanford", "lat": 46.4551, "lon": -119.4076, "alt_m": 142, "telescope": "LIGO Interferometer", "mirror_m": 0.0, "country": "USA"},
    {"name": "LIGO Livingston", "lat": 30.5633, "lon": -90.7742, "alt_m": 7, "telescope": "LIGO Interferometer", "mirror_m": 0.0, "country": "USA"},
    {"name": "Virgo Interferometer", "lat": 43.6314, "lon": 10.5044, "alt_m": 9, "telescope": "Virgo GW Detector", "mirror_m": 0.0, "country": "Italy"},
    {"name": "KAGRA", "lat": 36.4103, "lon": 137.3056, "alt_m": 414, "telescope": "KAGRA GW Detector", "mirror_m": 0.0, "country": "Japan"},
    {"name": "South Pole Telescope", "lat": -89.9911, "lon": -44.6503, "alt_m": 2835, "telescope": "SPT 10m", "mirror_m": 10.0, "country": "Antarctica"},
    {"name": "Extremely Large Telescope (ELT)", "lat": -24.5893, "lon": -70.1916, "alt_m": 3046, "telescope": "ELT 39m (under construction)", "mirror_m": 39.0, "country": "Chile"},
    {"name": "Giant Magellan Telescope (GMT)", "lat": -29.0146, "lon": -70.6847, "alt_m": 2516, "telescope": "GMT 24.5m (under construction)", "mirror_m": 24.5, "country": "Chile"},
    {"name": "Thirty Meter Telescope (TMT)", "lat": 19.8260, "lon": -155.4719, "alt_m": 4050, "telescope": "TMT 30m (planned)", "mirror_m": 30.0, "country": "USA"},
    {"name": "Yerkes Observatory", "lat": 42.5706, "lon": -88.5561, "alt_m": 334, "telescope": "40-inch Refractor", "mirror_m": 1.02, "country": "USA"},
    {"name": "Leoncito Astronomical Complex", "lat": -31.7986, "lon": -69.2956, "alt_m": 2552, "telescope": "Jorge Sahade 2.15m", "mirror_m": 2.15, "country": "Argentina"},
    {"name": "La Plata Observatory", "lat": -34.9069, "lon": -57.9322, "alt_m": 20, "telescope": "Historic refractor", "mirror_m": 0.43, "country": "Argentina"},
    {"name": "Maunakea Spectroscopic Explorer", "lat": 19.8250, "lon": -155.4700, "alt_m": 4200, "telescope": "MSE 11.25m (planned)", "mirror_m": 11.25, "country": "Canada"},
    {"name": "Nordic Optical Telescope", "lat": 28.7572, "lon": -17.8850, "alt_m": 2382, "telescope": "NOT 2.56m", "mirror_m": 2.56, "country": "Nordic"},
    {"name": "TNG - Telescopio Nazionale Galileo", "lat": 28.7539, "lon": -17.8892, "alt_m": 2370, "telescope": "TNG 3.58m", "mirror_m": 3.58, "country": "Italy"},
    {"name": "Large Binocular Telescope", "lat": 32.7013, "lon": -109.8891, "alt_m": 3221, "telescope": "LBT 2x8.4m", "mirror_m": 8.4, "country": "USA/Italy/Germany"},
    {"name": "Vatican Advanced Technology Telescope", "lat": 32.7016, "lon": -109.8719, "alt_m": 3191, "telescope": "VATT 1.8m", "mirror_m": 1.8, "country": "Vatican"},
]


METEOR_IMPACT_SITES = [
    {"name": "Vredefort Crater", "lat": -27.0, "lon": 27.5, "diameter_km": 300, "age_mya": 2023, "country": "South Africa"},
    {"name": "Chicxulub Crater", "lat": 21.4, "lon": -89.5, "diameter_km": 180, "age_mya": 66, "country": "Mexico"},
    {"name": "Sudbury Basin", "lat": 46.6, "lon": -81.2, "diameter_km": 130, "age_mya": 1849, "country": "Canada"},
    {"name": "Popigai Crater", "lat": 71.65, "lon": 111.18, "diameter_km": 100, "age_mya": 35.7, "country": "Russia"},
    {"name": "Manicouagan Crater", "lat": 51.38, "lon": -68.7, "diameter_km": 100, "age_mya": 214, "country": "Canada"},
    {"name": "Acraman Crater", "lat": -32.017, "lon": 135.45, "diameter_km": 90, "age_mya": 580, "country": "Australia"},
    {"name": "Chesapeake Bay Crater", "lat": 37.28, "lon": -76.02, "diameter_km": 85, "age_mya": 35.5, "country": "USA"},
    {"name": "Morokweng Crater", "lat": -26.47, "lon": 23.53, "diameter_km": 70, "age_mya": 145, "country": "South Africa"},
    {"name": "Kara Crater", "lat": 69.1, "lon": 64.15, "diameter_km": 65, "age_mya": 70.3, "country": "Russia"},
    {"name": "Siljan Ring", "lat": 61.03, "lon": 14.87, "diameter_km": 52, "age_mya": 376.8, "country": "Sweden"},
    {"name": "Charlevoix Crater", "lat": 47.53, "lon": -70.3, "diameter_km": 54, "age_mya": 342, "country": "Canada"},
    {"name": "Araguainha Crater", "lat": -16.78, "lon": -52.98, "diameter_km": 40, "age_mya": 254.7, "country": "Brazil"},
    {"name": "Mjolnir Crater", "lat": 73.8, "lon": 29.67, "diameter_km": 40, "age_mya": 142.0, "country": "Norway"},
    {"name": "Woodleigh Crater", "lat": -26.05, "lon": 114.67, "diameter_km": 40, "age_mya": 364, "country": "Australia"},
    {"name": "Clearwater Lakes (West)", "lat": 56.22, "lon": -74.5, "diameter_km": 36, "age_mya": 290, "country": "Canada"},
    {"name": "Clearwater Lakes (East)", "lat": 56.05, "lon": -74.07, "diameter_km": 26, "age_mya": 290, "country": "Canada"},
    {"name": "Ries Crater", "lat": 48.88, "lon": 10.62, "diameter_km": 24, "age_mya": 14.8, "country": "Germany"},
    {"name": "Rochechouart Crater", "lat": 45.82, "lon": 0.78, "diameter_km": 23, "age_mya": 206.9, "country": "France"},
    {"name": "Haughton Crater", "lat": 75.38, "lon": -89.68, "diameter_km": 23, "age_mya": 39, "country": "Canada"},
    {"name": "Steinheim Basin", "lat": 48.68, "lon": 10.07, "diameter_km": 3.8, "age_mya": 14.8, "country": "Germany"},
    {"name": "Gosses Bluff", "lat": -23.82, "lon": 132.31, "diameter_km": 22, "age_mya": 142.5, "country": "Australia"},
    {"name": "Mistastin Lake", "lat": 55.88, "lon": -63.33, "diameter_km": 28, "age_mya": 36.4, "country": "Canada"},
    {"name": "Logancha Crater", "lat": 65.5, "lon": 95.95, "diameter_km": 20, "age_mya": 40, "country": "Russia"},
    {"name": "Obolon Crater", "lat": 49.58, "lon": 32.93, "diameter_km": 20, "age_mya": 169, "country": "Ukraine"},
    {"name": "Nördlinger Ries", "lat": 48.85, "lon": 10.61, "diameter_km": 24, "age_mya": 14.8, "country": "Germany"},
    {"name": "Shoemaker Crater", "lat": -25.87, "lon": 120.88, "diameter_km": 30, "age_mya": 1630, "country": "Australia"},
    {"name": "Wolfe Creek Crater", "lat": -19.17, "lon": 127.8, "diameter_km": 0.875, "age_mya": 0.3, "country": "Australia"},
    {"name": "Barringer Crater (Meteor Crater)", "lat": 35.028, "lon": -111.023, "diameter_km": 1.186, "age_mya": 0.05, "country": "USA"},
    {"name": "Lonar Lake", "lat": 19.975, "lon": 76.51, "diameter_km": 1.83, "age_mya": 0.052, "country": "India"},
    {"name": "Kaali Crater", "lat": 58.373, "lon": 22.67, "diameter_km": 0.11, "age_mya": 0.004, "country": "Estonia"},
    {"name": "Pingualuit Crater", "lat": 61.28, "lon": -73.65, "diameter_km": 3.44, "age_mya": 1.4, "country": "Canada"},
    {"name": "Bosumtwi Crater", "lat": 6.5, "lon": -1.41, "diameter_km": 10.5, "age_mya": 1.07, "country": "Ghana"},
    {"name": "Tswaing Crater", "lat": -25.41, "lon": 28.08, "diameter_km": 1.13, "age_mya": 0.22, "country": "South Africa"},
    {"name": "Upheaval Dome", "lat": 38.44, "lon": -109.93, "diameter_km": 10, "age_mya": 170, "country": "USA"},
    {"name": "Serra da Cangalha", "lat": -8.08, "lon": -46.87, "diameter_km": 12, "age_mya": 220, "country": "Brazil"},
    {"name": "Wetumpka Crater", "lat": 32.52, "lon": -86.17, "diameter_km": 7.6, "age_mya": 83.5, "country": "USA"},
    {"name": "Beyenchime-Salaatin", "lat": 71.0, "lon": 121.67, "diameter_km": 8, "age_mya": 40, "country": "Russia"},
    {"name": "Boltysh Crater", "lat": 48.9, "lon": 32.25, "diameter_km": 24, "age_mya": 65.17, "country": "Ukraine"},
    {"name": "Elgygytgyn Crater", "lat": 67.5, "lon": 172.08, "diameter_km": 18, "age_mya": 3.6, "country": "Russia"},
    {"name": "Tookoonooka Crater", "lat": -27.12, "lon": 142.83, "diameter_km": 55, "age_mya": 128, "country": "Australia"},
    {"name": "Keurusselka Crater", "lat": 62.13, "lon": 24.6, "diameter_km": 30, "age_mya": 1800, "country": "Finland"},
]


SPACE_LAUNCH_SITES = [
    {"name": "Kennedy Space Center / Cape Canaveral", "lat": 28.5721, "lon": -80.6480, "operator": "NASA / SpaceX / ULA", "first_launch": 1950, "country": "USA"},
    {"name": "Vandenberg Space Force Base", "lat": 34.7420, "lon": -120.5724, "operator": "USSF / SpaceX", "first_launch": 1958, "country": "USA"},
    {"name": "Wallops Flight Facility", "lat": 37.9402, "lon": -75.4664, "operator": "NASA / Rocket Lab", "first_launch": 1945, "country": "USA"},
    {"name": "Baikonur Cosmodrome", "lat": 45.9650, "lon": 63.3050, "operator": "Roscosmos", "first_launch": 1957, "country": "Kazakhstan"},
    {"name": "Plesetsk Cosmodrome", "lat": 62.9258, "lon": 40.5777, "operator": "Russian Aerospace Forces", "first_launch": 1966, "country": "Russia"},
    {"name": "Vostochny Cosmodrome", "lat": 51.8844, "lon": 128.3334, "operator": "Roscosmos", "first_launch": 2016, "country": "Russia"},
    {"name": "Guiana Space Centre (Kourou)", "lat": 5.2322, "lon": -52.7693, "operator": "ESA / Arianespace", "first_launch": 1968, "country": "French Guiana"},
    {"name": "Tanegashima Space Center", "lat": 30.4000, "lon": 131.0000, "operator": "JAXA", "first_launch": 1969, "country": "Japan"},
    {"name": "Uchinoura Space Center", "lat": 31.2519, "lon": 131.0792, "operator": "JAXA", "first_launch": 1962, "country": "Japan"},
    {"name": "Satish Dhawan Space Centre", "lat": 13.7200, "lon": 80.2300, "operator": "ISRO", "first_launch": 1971, "country": "India"},
    {"name": "Jiuquan Satellite Launch Center", "lat": 40.9606, "lon": 100.2914, "operator": "CNSA / CASC", "first_launch": 1970, "country": "China"},
    {"name": "Xichang Satellite Launch Center", "lat": 28.2467, "lon": 102.0267, "operator": "CNSA / CASC", "first_launch": 1984, "country": "China"},
    {"name": "Wenchang Spacecraft Launch Site", "lat": 19.6145, "lon": 110.9510, "operator": "CNSA / CASC", "first_launch": 2016, "country": "China"},
    {"name": "Taiyuan Satellite Launch Center", "lat": 38.8490, "lon": 111.6080, "operator": "CNSA / CASC", "first_launch": 1988, "country": "China"},
    {"name": "Naro Space Center", "lat": 34.4317, "lon": 127.5350, "operator": "KARI", "first_launch": 2009, "country": "South Korea"},
    {"name": "Semnan Launch Site", "lat": 35.2344, "lon": 53.9208, "operator": "ISA (Iran)", "first_launch": 2009, "country": "Iran"},
    {"name": "Palmachim Airbase", "lat": 31.8844, "lon": 34.6828, "operator": "ISA (Israel)", "first_launch": 1988, "country": "Israel"},
    {"name": "Hammaguir Launch Site", "lat": 30.8775, "lon": -3.0619, "operator": "CNES (historic)", "first_launch": 1952, "country": "Algeria"},
    {"name": "San Marco Platform (historic)", "lat": -2.9381, "lon": 40.2128, "operator": "ASI (Italy, historic)", "first_launch": 1967, "country": "Kenya"},
    {"name": "Rocket Lab Launch Complex 1", "lat": -39.2615, "lon": 177.8649, "operator": "Rocket Lab", "first_launch": 2017, "country": "New Zealand"},
    {"name": "Esrange Space Center", "lat": 67.8933, "lon": 21.1064, "operator": "SSC (Sweden)", "first_launch": 1966, "country": "Sweden"},
    {"name": "Andoya Space Center", "lat": 69.2944, "lon": 16.0214, "operator": "NAROM (Norway)", "first_launch": 1962, "country": "Norway"},
    {"name": "Alcantara Launch Center", "lat": -2.3733, "lon": -44.3964, "operator": "AEB (Brazil)", "first_launch": 1990, "country": "Brazil"},
    {"name": "Thumba Equatorial Rocket Launching", "lat": 8.5372, "lon": 76.8658, "operator": "ISRO", "first_launch": 1963, "country": "India"},
    {"name": "Kodiak Launch Complex", "lat": 57.4358, "lon": -152.3378, "operator": "AADC (Alaska)", "first_launch": 1998, "country": "USA"},
    {"name": "Spaceport America", "lat": 32.9903, "lon": -106.9697, "operator": "Virgin Galactic", "first_launch": 2006, "country": "USA"},
    {"name": "Starbase Boca Chica", "lat": 25.9972, "lon": -97.1561, "operator": "SpaceX", "first_launch": 2019, "country": "USA"},
    {"name": "Mid-Atlantic Regional Spaceport", "lat": 37.8433, "lon": -75.4878, "operator": "Northrop Grumman", "first_launch": 2006, "country": "USA"},
    {"name": "Woomera Test Range", "lat": -31.1956, "lon": 136.8256, "operator": "RAAF (Australia)", "first_launch": 1957, "country": "Australia"},
    {"name": "Sohae Satellite Launching Station", "lat": 39.6600, "lon": 124.7053, "operator": "NADA (North Korea)", "first_launch": 2012, "country": "North Korea"},
    {"name": "Tonghae Satellite Launching Ground", "lat": 40.8561, "lon": 129.6658, "operator": "NADA (North Korea)", "first_launch": 2006, "country": "North Korea"},
]


RADIO_TELESCOPES = [
    {"name": "FAST (Five-hundred-meter Aperture)", "lat": 25.6529, "lon": 106.8566, "dish_m": 500, "freq_range": "70 MHz - 3 GHz", "country": "China"},
    {"name": "Arecibo Observatory (collapsed 2020)", "lat": 18.3464, "lon": -66.7528, "dish_m": 305, "freq_range": "50 MHz - 10 GHz", "country": "Puerto Rico"},
    {"name": "Green Bank Telescope", "lat": 38.4331, "lon": -79.8397, "dish_m": 100, "freq_range": "0.1 - 116 GHz", "country": "USA"},
    {"name": "Effelsberg Radio Telescope", "lat": 50.5247, "lon": 6.8828, "dish_m": 100, "freq_range": "0.3 - 96 GHz", "country": "Germany"},
    {"name": "Lovell Telescope (Jodrell Bank)", "lat": 53.2367, "lon": -2.3085, "dish_m": 76.2, "freq_range": "0.15 - 10 GHz", "country": "UK"},
    {"name": "Parkes Radio Telescope (Murriyang)", "lat": -32.9983, "lon": 148.2636, "dish_m": 64, "freq_range": "0.7 - 26 GHz", "country": "Australia"},
    {"name": "Very Large Array (VLA)", "lat": 34.0784, "lon": -107.6184, "dish_m": 25, "freq_range": "0.073 - 50 GHz", "country": "USA"},
    {"name": "ALMA (Atacama Large Millimeter Array)", "lat": -23.0193, "lon": -67.7532, "dish_m": 12, "freq_range": "84 - 950 GHz", "country": "Chile"},
    {"name": "Westerbork Synthesis Radio Telescope", "lat": 52.9150, "lon": 6.6044, "dish_m": 25, "freq_range": "0.12 - 8.3 GHz", "country": "Netherlands"},
    {"name": "Australia Telescope Compact Array", "lat": -30.3128, "lon": 149.5500, "dish_m": 22, "freq_range": "1.1 - 105 GHz", "country": "Australia"},
    {"name": "NOEMA (Northern Extended Millimeter Array)", "lat": 44.6339, "lon": 5.9075, "dish_m": 15, "freq_range": "72 - 373 GHz", "country": "France"},
    {"name": "IRAM 30m Telescope", "lat": 37.0661, "lon": -3.3928, "dish_m": 30, "freq_range": "83 - 360 GHz", "country": "Spain"},
    {"name": "Sardinia Radio Telescope", "lat": 39.4930, "lon": 9.2451, "dish_m": 64, "freq_range": "0.3 - 116 GHz", "country": "Italy"},
    {"name": "Nobeyama Radio Observatory", "lat": 35.9417, "lon": 138.4722, "dish_m": 45, "freq_range": "20 - 230 GHz", "country": "Japan"},
    {"name": "Nancay Radio Telescope", "lat": 47.3803, "lon": 2.1950, "dish_m": 200, "freq_range": "1 - 3.5 GHz", "country": "France"},
    {"name": "Molonglo Observatory Synthesis Telescope", "lat": -35.3706, "lon": 149.4244, "dish_m": 778, "freq_range": "843 MHz", "country": "Australia"},
    {"name": "Giant Metrewave Radio Telescope", "lat": 19.0964, "lon": 74.0497, "dish_m": 45, "freq_range": "50 - 1500 MHz", "country": "India"},
    {"name": "Onsala Space Observatory", "lat": 57.3931, "lon": 11.9175, "dish_m": 25, "freq_range": "0.3 - 116 GHz", "country": "Sweden"},
    {"name": "Torun Radio Astronomy Observatory", "lat": 53.0953, "lon": 17.8614, "dish_m": 32, "freq_range": "1.4 - 43 GHz", "country": "Poland"},
    {"name": "Medicina Radio Observatory", "lat": 44.5206, "lon": 11.6469, "dish_m": 32, "freq_range": "0.4 - 26 GHz", "country": "Italy"},
    {"name": "Yebes Observatory", "lat": 40.5247, "lon": -3.0886, "dish_m": 40, "freq_range": "2 - 90 GHz", "country": "Spain"},
    {"name": "Hartebeesthoek Radio Astronomy Obs.", "lat": -25.8900, "lon": 27.6853, "dish_m": 26, "freq_range": "1.4 - 23 GHz", "country": "South Africa"},
    {"name": "MeerKAT Array", "lat": -30.7130, "lon": 21.4439, "dish_m": 13.5, "freq_range": "0.58 - 14.5 GHz", "country": "South Africa"},
    {"name": "Square Kilometre Array (SKA-Mid)", "lat": -30.7130, "lon": 21.4439, "dish_m": 15, "freq_range": "0.35 - 15.4 GHz", "country": "South Africa"},
    {"name": "Square Kilometre Array (SKA-Low)", "lat": -26.6978, "lon": 116.6311, "dish_m": 2, "freq_range": "50 - 350 MHz", "country": "Australia"},
    {"name": "Deep Space Station 43 (Canberra DSN)", "lat": -35.4014, "lon": 148.9817, "dish_m": 70, "freq_range": "S/X/Ka Band", "country": "Australia"},
]


DARK_SKY_RESERVES = [
    {"name": "NamibRand Nature Reserve", "lat": -25.0, "lon": 16.0, "level": "Gold", "designation": "Dark Sky Reserve", "country": "Namibia"},
    {"name": "Aoraki Mackenzie International Dark Sky Reserve", "lat": -43.9867, "lon": 170.465, "level": "Gold", "designation": "Dark Sky Reserve", "country": "New Zealand"},
    {"name": "Brecon Beacons / Bannau Brycheiniog", "lat": 51.8833, "lon": -3.4333, "level": "Silver", "designation": "Dark Sky Reserve", "country": "Wales, UK"},
    {"name": "Kerry International Dark Sky Reserve", "lat": 51.8333, "lon": -9.95, "level": "Gold", "designation": "Dark Sky Reserve", "country": "Ireland"},
    {"name": "Zselic Starry Sky Park", "lat": 46.2667, "lon": 17.7833, "level": "Silver", "designation": "Dark Sky Park", "country": "Hungary"},
    {"name": "Mont-Megantic International Dark Sky Reserve", "lat": 45.4555, "lon": -71.1519, "level": "Silver", "designation": "Dark Sky Reserve", "country": "Canada"},
    {"name": "Exmoor National Park", "lat": 51.13, "lon": -3.65, "level": "N/A", "designation": "Dark Sky Reserve", "country": "England, UK"},
    {"name": "Galloway Forest Dark Sky Park", "lat": 55.1, "lon": -4.4, "level": "Gold", "designation": "Dark Sky Park", "country": "Scotland, UK"},
    {"name": "Westhavelland Dark Sky Reserve", "lat": 52.7333, "lon": 12.2, "level": "Silver", "designation": "Dark Sky Reserve", "country": "Germany"},
    {"name": "Rhon Biosphere Reserve", "lat": 50.45, "lon": 9.95, "level": "Silver", "designation": "Dark Sky Reserve", "country": "Germany"},
    {"name": "Pic du Midi Dark Sky Reserve", "lat": 42.9364, "lon": 0.1422, "level": "Silver", "designation": "Dark Sky Reserve", "country": "France"},
    {"name": "Alpes Azur Mercantour", "lat": 44.1167, "lon": 6.85, "level": "Silver", "designation": "Dark Sky Reserve", "country": "France"},
    {"name": "River Murray Dark Sky Reserve", "lat": -34.2, "lon": 140.4, "level": "Gold", "designation": "Dark Sky Reserve", "country": "Australia"},
    {"name": "Warrumbungle Dark Sky Park", "lat": -31.2733, "lon": 149.0667, "level": "Gold", "designation": "Dark Sky Park", "country": "Australia"},
    {"name": "Natural Bridges National Monument", "lat": 37.6092, "lon": -110.0017, "level": "Gold", "designation": "Dark Sky Park", "country": "USA"},
    {"name": "Cherry Springs State Park", "lat": 41.6628, "lon": -77.8233, "level": "Gold", "designation": "Dark Sky Park", "country": "USA"},
    {"name": "Big Bend National Park", "lat": 29.25, "lon": -103.25, "level": "Gold", "designation": "Dark Sky Park", "country": "USA"},
    {"name": "Death Valley National Park", "lat": 36.505, "lon": -117.079, "level": "Gold", "designation": "Dark Sky Park", "country": "USA"},
    {"name": "Grand Canyon-Parashant National Monument", "lat": 36.4, "lon": -113.7, "level": "N/A", "designation": "Dark Sky Province", "country": "USA"},
    {"name": "Headlands International Dark Sky Park", "lat": 45.5833, "lon": -84.8, "level": "Gold", "designation": "Dark Sky Park", "country": "USA"},
    {"name": "Jasper National Park", "lat": 52.8734, "lon": -117.9543, "level": "N/A", "designation": "Dark Sky Preserve", "country": "Canada"},
    {"name": "Wood Buffalo National Park", "lat": 59.4, "lon": -112.8, "level": "N/A", "designation": "Dark Sky Preserve", "country": "Canada"},
    {"name": "Observatorio del Teide (Starlight Reserve)", "lat": 28.3003, "lon": -16.5106, "level": "Gold", "designation": "Starlight Reserve", "country": "Spain"},
    {"name": "La Palma Starlight Reserve", "lat": 28.75, "lon": -17.88, "level": "Gold", "designation": "Starlight Reserve", "country": "Spain"},
    {"name": "Cevennes National Park", "lat": 44.35, "lon": 3.6, "level": "Silver", "designation": "Dark Sky Reserve", "country": "France"},
    {"name": "Snowdonia / Eryri National Park", "lat": 52.9, "lon": -3.9, "level": "Silver", "designation": "Dark Sky Reserve", "country": "Wales, UK"},
    {"name": "Hortobagy National Park", "lat": 47.583, "lon": 21.15, "level": "Silver", "designation": "Dark Sky Park", "country": "Hungary"},
    {"name": "Gabriela Mistral Dark Sky Sanctuary", "lat": -30.2, "lon": -70.8, "level": "N/A", "designation": "Dark Sky Sanctuary", "country": "Chile"},
    {"name": "Elqui Valley Dark Sky Sanctuary", "lat": -30.17, "lon": -70.5, "level": "N/A", "designation": "Dark Sky Sanctuary", "country": "Chile"},
    {"name": "Manon-ki-Barren Dark Sky Reserve", "lat": 26.0, "lon": 72.0, "level": "N/A", "designation": "Dark Sky Reserve", "country": "India"},
    {"name": "Moffat Dark Sky Town", "lat": 55.334, "lon": -3.442, "level": "N/A", "designation": "Dark Sky Town", "country": "Scotland, UK"},
]


SATELLITE_GROUND_STATIONS = [
    {"name": "Goldstone Deep Space Complex", "lat": 35.4267, "lon": -116.8900, "network": "NASA DSN", "antenna_m": 70, "country": "USA"},
    {"name": "Madrid Deep Space Complex", "lat": 40.4314, "lon": -4.2489, "network": "NASA DSN", "antenna_m": 70, "country": "Spain"},
    {"name": "Canberra Deep Space Complex", "lat": -35.4014, "lon": 148.9817, "network": "NASA DSN", "antenna_m": 70, "country": "Australia"},
    {"name": "Malargue Ground Station", "lat": -35.7758, "lon": -69.3983, "network": "ESA ESTRACK", "antenna_m": 35, "country": "Argentina"},
    {"name": "Cebreros Ground Station", "lat": 40.4525, "lon": -4.3675, "network": "ESA ESTRACK", "antenna_m": 35, "country": "Spain"},
    {"name": "New Norcia Ground Station", "lat": -31.0483, "lon": 116.1917, "network": "ESA ESTRACK", "antenna_m": 35, "country": "Australia"},
    {"name": "Redu Ground Station", "lat": 50.0019, "lon": 5.1461, "network": "ESA ESTRACK", "antenna_m": 15, "country": "Belgium"},
    {"name": "Kiruna Ground Station", "lat": 67.8572, "lon": 20.9644, "network": "ESA ESTRACK", "antenna_m": 15, "country": "Sweden"},
    {"name": "Santa Maria Ground Station", "lat": 36.9975, "lon": -25.1356, "network": "ESA ESTRACK", "antenna_m": 15, "country": "Portugal (Azores)"},
    {"name": "Kourou Ground Station", "lat": 5.2519, "lon": -52.8047, "network": "ESA ESTRACK", "antenna_m": 15, "country": "French Guiana"},
    {"name": "Maspalomas Ground Station", "lat": 27.7628, "lon": -15.6342, "network": "ESA ESTRACK", "antenna_m": 15, "country": "Spain (Canary Is.)"},
    {"name": "Villafranca Ground Station", "lat": 40.4433, "lon": -3.9531, "network": "ESA ESTRACK", "antenna_m": 15, "country": "Spain"},
    {"name": "Usuda Deep Space Center", "lat": 36.1325, "lon": 138.3622, "network": "JAXA", "antenna_m": 64, "country": "Japan"},
    {"name": "Sagamihara Tracking Station", "lat": 35.5611, "lon": 139.3906, "network": "JAXA", "antenna_m": 34, "country": "Japan"},
    {"name": "ISTRAC Bangalore", "lat": 13.0358, "lon": 77.5117, "network": "ISRO ISTRAC", "antenna_m": 32, "country": "India"},
    {"name": "IDSN Byalalu", "lat": 13.1017, "lon": 77.3717, "network": "ISRO IDSN", "antenna_m": 32, "country": "India"},
    {"name": "Bear Lakes RT-64", "lat": 55.8683, "lon": 37.9550, "network": "Roscosmos", "antenna_m": 64, "country": "Russia"},
    {"name": "Yevpatoria RT-70", "lat": 45.1869, "lon": 33.1789, "network": "Former Soviet DSN", "antenna_m": 70, "country": "Ukraine"},
    {"name": "Kashi Deep Space Station", "lat": 38.3333, "lon": 76.0333, "network": "CNSA / CLTC", "antenna_m": 35, "country": "China"},
    {"name": "Jiamusi Deep Space Station", "lat": 46.5167, "lon": 130.2833, "network": "CNSA / CLTC", "antenna_m": 66, "country": "China"},
    {"name": "White Sands Test Facility", "lat": 32.5003, "lon": -106.6108, "network": "NASA TDRS", "antenna_m": 18, "country": "USA"},
    {"name": "Guam Remote Ground Terminal", "lat": 13.6156, "lon": 144.8556, "network": "NASA TDRS", "antenna_m": 18, "country": "Guam, USA"},
    {"name": "Hartebeesthoek (HBK)", "lat": -25.8869, "lon": 27.7072, "network": "SANSA", "antenna_m": 26, "country": "South Africa"},
    {"name": "Svalbard Satellite Station", "lat": 78.2306, "lon": 15.3894, "network": "KSAT / ESA", "antenna_m": 13, "country": "Norway"},
    {"name": "Troll Satellite Station", "lat": -72.0117, "lon": 2.5350, "network": "KSAT", "antenna_m": 7.3, "country": "Antarctica"},
]


PLANETARIUMS = [
    {"name": "Hayden Planetarium", "lat": 40.7812, "lon": -73.9729, "city": "New York", "dome_m": 26, "seats": 429, "country": "USA"},
    {"name": "Griffith Observatory Planetarium", "lat": 34.1184, "lon": -118.3004, "city": "Los Angeles", "dome_m": 23, "seats": 300, "country": "USA"},
    {"name": "Adler Planetarium", "lat": 41.8663, "lon": -87.6068, "city": "Chicago", "dome_m": 20, "seats": 300, "country": "USA"},
    {"name": "Morrison Planetarium", "lat": 37.7699, "lon": -122.4661, "city": "San Francisco", "dome_m": 22.5, "seats": 290, "country": "USA"},
    {"name": "Albert Einstein Planetarium (Smithsonian)", "lat": 38.8880, "lon": -77.0199, "city": "Washington DC", "dome_m": 21, "seats": 235, "country": "USA"},
    {"name": "Burke Baker Planetarium", "lat": 29.7220, "lon": -95.3899, "city": "Houston", "dome_m": 18, "seats": 232, "country": "USA"},
    {"name": "Fels Planetarium", "lat": 39.9607, "lon": -75.1723, "city": "Philadelphia", "dome_m": 20, "seats": 350, "country": "USA"},
    {"name": "Zeiss-Grossplanetarium", "lat": 52.5290, "lon": 13.4297, "city": "Berlin", "dome_m": 23, "seats": 292, "country": "Germany"},
    {"name": "Planetarium Hamburg", "lat": 53.5964, "lon": 10.0139, "city": "Hamburg", "dome_m": 20.6, "seats": 253, "country": "Germany"},
    {"name": "Planetarium Stuttgart", "lat": 48.7817, "lon": 9.1872, "city": "Stuttgart", "dome_m": 20, "seats": 277, "country": "Germany"},
    {"name": "Peter Harrison Planetarium", "lat": 51.4769, "lon": -0.0005, "city": "London", "dome_m": 9, "seats": 120, "country": "UK"},
    {"name": "Moscow Planetarium", "lat": 55.7614, "lon": 37.5836, "city": "Moscow", "dome_m": 25, "seats": 356, "country": "Russia"},
    {"name": "Nehru Planetarium Mumbai", "lat": 18.9748, "lon": 72.8118, "city": "Mumbai", "dome_m": 23, "seats": 286, "country": "India"},
    {"name": "Nehru Planetarium Delhi", "lat": 28.6158, "lon": 77.1929, "city": "New Delhi", "dome_m": 23, "seats": 270, "country": "India"},
    {"name": "Birla Planetarium Kolkata", "lat": 22.5530, "lon": 88.3518, "city": "Kolkata", "dome_m": 23, "seats": 500, "country": "India"},
    {"name": "Beijing Planetarium", "lat": 39.9367, "lon": 116.3456, "city": "Beijing", "dome_m": 23, "seats": 400, "country": "China"},
    {"name": "Shanghai Astronomy Museum", "lat": 30.8800, "lon": 121.7900, "city": "Shanghai", "dome_m": 18, "seats": 300, "country": "China"},
    {"name": "Nagoya City Science Museum Planetarium", "lat": 35.1654, "lon": 136.9002, "city": "Nagoya", "dome_m": 35, "seats": 350, "country": "Japan"},
    {"name": "Osaka Science Museum Planetarium", "lat": 34.6913, "lon": 135.4914, "city": "Osaka", "dome_m": 26.5, "seats": 300, "country": "Japan"},
    {"name": "Cite de l'Espace Planetarium", "lat": 43.5867, "lon": 1.4914, "city": "Toulouse", "dome_m": 20, "seats": 280, "country": "France"},
    {"name": "Planetario de Madrid", "lat": 40.3922, "lon": -3.6808, "city": "Madrid", "dome_m": 17.5, "seats": 260, "country": "Spain"},
    {"name": "CosmoCaixa Planetarium", "lat": 41.4128, "lon": 2.1311, "city": "Barcelona", "dome_m": 14, "seats": 200, "country": "Spain"},
    {"name": "Planetario di Milano", "lat": 45.4753, "lon": 9.1986, "city": "Milan", "dome_m": 19.6, "seats": 315, "country": "Italy"},
    {"name": "Planetario di Roma", "lat": 41.8344, "lon": 12.4731, "city": "Rome", "dome_m": 14, "seats": 100, "country": "Italy"},
    {"name": "Tycho Brahe Planetarium", "lat": 55.6611, "lon": 12.5578, "city": "Copenhagen", "dome_m": 23, "seats": 268, "country": "Denmark"},
    {"name": "Rio Tinto Alcan Planetarium", "lat": 45.5592, "lon": -73.5514, "city": "Montreal", "dome_m": 18, "seats": 230, "country": "Canada"},
    {"name": "H.R. MacMillan Space Centre", "lat": 49.2775, "lon": -123.1442, "city": "Vancouver", "dome_m": 20, "seats": 230, "country": "Canada"},
    {"name": "Planetario de Buenos Aires", "lat": -34.5692, "lon": -58.4133, "city": "Buenos Aires", "dome_m": 20, "seats": 260, "country": "Argentina"},
    {"name": "Johannesburg Planetarium", "lat": -26.1886, "lon": 28.0281, "city": "Johannesburg", "dome_m": 24.5, "seats": 500, "country": "South Africa"},
    {"name": "Iziko Planetarium", "lat": -33.9367, "lon": 18.4233, "city": "Cape Town", "dome_m": 18, "seats": 210, "country": "South Africa"},
    {"name": "Sir Thomas Brisbane Planetarium", "lat": -27.4768, "lon": 152.9757, "city": "Brisbane", "dome_m": 12.5, "seats": 130, "country": "Australia"},
]


ASTRONOMICAL_CLOCKS = [
    {"name": "Prague Astronomical Clock (Orloj)", "lat": 50.0870, "lon": 14.4208, "city": "Prague", "year_built": 1410, "features": "Astronomical dial, Walk of the Apostles, calendar dial", "country": "Czech Republic"},
    {"name": "Strasbourg Astronomical Clock", "lat": 48.5818, "lon": 7.7509, "city": "Strasbourg", "year_built": 1843, "features": "Perpetual calendar, orrery, eclipses, Foucault pendulum", "country": "France"},
    {"name": "Padua Clock Tower (Torre dell'Orologio)", "lat": 45.4078, "lon": 11.8758, "city": "Padua", "year_built": 1344, "features": "Oldest working astronomical clock, zodiac, planetary hours", "country": "Italy"},
    {"name": "Lund Cathedral Astronomical Clock", "lat": 55.7042, "lon": 13.1942, "city": "Lund", "year_built": 1425, "features": "Calendar to 2123, In Dulci Jubilo melody, knight jousting", "country": "Sweden"},
    {"name": "Rostock St. Mary's Church Clock", "lat": 54.0900, "lon": 12.1333, "city": "Rostock", "year_built": 1472, "features": "Calendar disc, zodiac, apostle procession (still runs original)", "country": "Germany"},
    {"name": "Wells Cathedral Clock", "lat": 51.2097, "lon": -2.6478, "city": "Wells", "year_built": 1390, "features": "Jousting knights, quarter-jacks, 24-hour dial, lunar phase", "country": "UK"},
    {"name": "Bern Zytglogge", "lat": 46.9480, "lon": 7.4475, "city": "Bern", "year_built": 1530, "features": "Astronomical dial, rooster, bear parade, jester", "country": "Switzerland"},
    {"name": "Lyon Cathedral Astronomical Clock", "lat": 45.7606, "lon": 4.8264, "city": "Lyon", "year_built": 1598, "features": "Saint days, lunar calendar, sunrise/sunset times", "country": "France"},
    {"name": "Olomouc Astronomical Clock", "lat": 49.5946, "lon": 17.2505, "city": "Olomouc", "year_built": 1422, "features": "Rebuilt 1955 socialist-realist style, proletarian figures", "country": "Czech Republic"},
    {"name": "Munster St. Paul's Cathedral Clock", "lat": 51.9625, "lon": 7.6256, "city": "Munster", "year_built": 1540, "features": "Calendar to 2071, Magi procession, lunar phases", "country": "Germany"},
    {"name": "Lubeck St. Mary's Church Clock", "lat": 53.8672, "lon": 10.6861, "city": "Lubeck", "year_built": 1967, "features": "Replacement after WWII, apostle procession, calendar", "country": "Germany"},
    {"name": "Cremona Torrazzo Clock", "lat": 45.1331, "lon": 10.0233, "city": "Cremona", "year_built": 1583, "features": "Zodiac constellations, tallest medieval bell tower clock", "country": "Italy"},
    {"name": "Gdansk St. Mary's Church Clock", "lat": 54.3489, "lon": 18.6533, "city": "Gdansk", "year_built": 1464, "features": "Calendar, zodiac, saints' days, Adam and Eve figures", "country": "Poland"},
    {"name": "Exeter Cathedral Clock", "lat": 50.7225, "lon": -3.5319, "city": "Exeter", "year_built": 1484, "features": "Earth-centric dial, lunar phase, fleur-de-lis hour hand", "country": "UK"},
    {"name": "Beauvais Cathedral Clock", "lat": 49.4317, "lon": 2.0811, "city": "Beauvais", "year_built": 1868, "features": "52 dials, 90,000 parts, celestial mechanics, Last Judgment scene", "country": "France"},
]


SOLAR_ECLIPSE_PATHS = [
    {
        "name": "Total Solar Eclipse - August 12, 2026",
        "date": "2026-08-12",
        "max_duration_s": 138,
        "path_width_km": 294,
        "regions": "Arctic, Greenland, Iceland, Atlantic, Spain",
        "path": [
            [71.2, -175.0], [71.0, -168.0], [70.5, -160.0],
            [69.8, -150.0], [69.0, -140.0], [67.5, -130.0],
            [66.0, -120.0], [63.5, -110.0], [61.0, -100.0],
            [58.5, -90.0], [56.0, -80.0], [53.0, -70.0],
            [50.0, -60.0], [48.0, -50.0], [46.0, -40.0],
            [44.5, -30.0], [43.0, -20.0], [41.5, -10.0],
            [40.8, -4.0], [40.2, 0.0], [39.5, 5.0],
            [38.5, 10.0], [37.0, 15.0], [35.5, 20.0],
        ],
    },
    {
        "name": "Total Solar Eclipse - August 2, 2027",
        "date": "2027-08-02",
        "max_duration_s": 382,
        "path_width_km": 258,
        "regions": "Atlantic, Morocco, Spain, Algeria, Tunisia, Libya, Egypt, Saudi Arabia, Yemen, Somalia",
        "path": [
            [30.0, -90.0], [30.8, -85.0], [31.5, -80.0],
            [32.2, -70.0], [33.0, -60.0], [33.5, -50.0],
            [34.0, -40.0], [34.5, -30.0], [35.0, -20.0],
            [35.5, -10.0], [35.9, -6.0], [36.0, 0.0],
            [35.9, 5.0], [35.8, 10.0], [35.4, 15.0],
            [35.0, 20.0], [34.2, 25.0], [33.5, 30.0],
            [32.2, 35.0], [31.0, 40.0], [29.5, 45.0],
            [28.0, 50.0], [26.5, 55.0], [25.0, 60.0],
            [23.5, 65.0], [22.0, 70.0], [20.0, 75.0],
            [18.0, 80.0],
        ],
    },
    {
        "name": "Total Solar Eclipse - July 22, 2028",
        "date": "2028-07-22",
        "max_duration_s": 335,
        "path_width_km": 230,
        "regions": "Indian Ocean, Australia, New Zealand, Pacific",
        "path": [
            [-50.0, 60.0], [-48.0, 70.0], [-45.0, 80.0],
            [-43.0, 90.0], [-40.0, 100.0], [-39.0, 105.0],
            [-38.0, 110.0], [-37.0, 115.0], [-36.0, 120.0],
            [-35.0, 125.0], [-34.0, 130.0], [-33.0, 135.0],
            [-32.0, 140.0], [-31.0, 145.0], [-30.0, 150.0],
            [-28.0, 160.0], [-25.0, 170.0], [-22.0, 175.0],
            [-20.0, 180.0], [-17.0, -175.0], [-15.0, -170.0],
        ],
    },
    {
        "name": "Total Solar Eclipse - November 25, 2030",
        "date": "2030-11-25",
        "max_duration_s": 228,
        "path_width_km": 169,
        "regions": "Southern Africa, Indian Ocean, Australia",
        "path": [
            [-15.0, 10.0], [-17.5, 15.0], [-20.0, 20.0],
            [-22.5, 25.0], [-25.0, 30.0], [-27.5, 35.0],
            [-30.0, 40.0], [-32.5, 45.0], [-35.0, 50.0],
            [-36.5, 55.0], [-38.0, 60.0], [-39.0, 65.0],
            [-40.0, 70.0], [-41.0, 75.0], [-42.0, 80.0],
            [-43.0, 85.0], [-44.0, 90.0], [-45.0, 95.0],
            [-46.0, 100.0], [-47.0, 105.0], [-48.0, 110.0],
            [-49.0, 115.0], [-50.0, 120.0], [-51.0, 125.0],
            [-52.0, 130.0], [-53.0, 135.0], [-54.0, 140.0],
            [-54.5, 145.0], [-55.0, 150.0],
        ],
    },
    {
        "name": "Total Solar Eclipse - March 20, 2034",
        "date": "2034-03-20",
        "max_duration_s": 255,
        "path_width_km": 159,
        "regions": "Central Africa, Middle East, Central Asia, China, Korea, Japan, Pacific",
        "path": [
            [20.0, 10.0], [22.0, 15.0], [25.0, 20.0],
            [26.5, 25.0], [28.0, 30.0], [29.0, 35.0],
            [30.0, 40.0], [31.5, 45.0], [33.0, 50.0],
            [34.0, 55.0], [35.0, 60.0], [36.0, 65.0],
            [37.0, 70.0], [37.8, 75.0], [38.5, 80.0],
            [39.0, 85.0], [39.5, 90.0], [39.8, 95.0],
            [40.0, 100.0], [40.2, 105.0], [40.5, 110.0],
            [40.8, 115.0], [41.0, 120.0], [41.2, 125.0],
            [41.5, 130.0], [41.8, 135.0], [42.0, 140.0],
        ],
    },
]


BORTLE_ZONES = [
    {"city": "New York", "lat": 40.7128, "lon": -74.0060, "bortle": 9, "radius_km": 70},
    {"city": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "bortle": 9, "radius_km": 80},
    {"city": "London", "lat": 51.5074, "lon": -0.1278, "bortle": 9, "radius_km": 60},
    {"city": "Tokyo", "lat": 35.6762, "lon": 139.6503, "bortle": 9, "radius_km": 75},
    {"city": "Paris", "lat": 48.8566, "lon": 2.3522, "bortle": 8, "radius_km": 50},
    {"city": "Beijing", "lat": 39.9042, "lon": 116.4074, "bortle": 9, "radius_km": 70},
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "bortle": 9, "radius_km": 55},
    {"city": "Shanghai", "lat": 31.2304, "lon": 121.4737, "bortle": 9, "radius_km": 70},
    {"city": "Chicago", "lat": 41.8781, "lon": -87.6298, "bortle": 8, "radius_km": 60},
    {"city": "Moscow", "lat": 55.7558, "lon": 37.6173, "bortle": 8, "radius_km": 65},
    {"city": "Sao Paulo", "lat": -23.5505, "lon": -46.6333, "bortle": 9, "radius_km": 70},
    {"city": "Cairo", "lat": 30.0444, "lon": 31.2357, "bortle": 8, "radius_km": 45},
    {"city": "Seoul", "lat": 37.5665, "lon": 126.9780, "bortle": 9, "radius_km": 55},
    {"city": "Delhi", "lat": 28.7041, "lon": 77.1025, "bortle": 9, "radius_km": 60},
    {"city": "Sydney", "lat": -33.8688, "lon": 151.2093, "bortle": 8, "radius_km": 50},
    {"city": "Mexico City", "lat": 19.4326, "lon": -99.1332, "bortle": 8, "radius_km": 60},
    {"city": "Berlin", "lat": 52.5200, "lon": 13.4050, "bortle": 7, "radius_km": 40},
    {"city": "Houston", "lat": 29.7604, "lon": -95.3698, "bortle": 8, "radius_km": 65},
    {"city": "Lagos", "lat": 6.5244, "lon": 3.3792, "bortle": 8, "radius_km": 45},
    {"city": "Istanbul", "lat": 41.0082, "lon": 28.9784, "bortle": 8, "radius_km": 55},
]


# ---------------------------------------------------------------------------
# Map type enum
# ---------------------------------------------------------------------------

MAP_TYPES = [
    "World Observatories",
    "Light Pollution (VIIRS Night Lights)",
    "Meteor Impact Sites",
    "Space Launch Sites",
    "Radio Telescopes",
    "Dark Sky Reserves",
    "Satellite Ground Stations",
    "Planetariums",
    "Astronomical Clocks",
    "Solar Eclipse Paths",
]


# ---------------------------------------------------------------------------
# Helper: create dark base map
# ---------------------------------------------------------------------------

def _base_map(center=None, zoom=2):
    """Return a dark-themed Folium map."""
    if center is None:
        center = [20, 0]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


# ---------------------------------------------------------------------------
# Individual map builders
# ---------------------------------------------------------------------------

def _build_observatories_map():
    """Map 1 -- World Observatories."""
    m = _base_map()
    for obs in WORLD_OBSERVATORIES:
        popup_text = (
            f"<b>{html.escape(obs['name'])}</b><br>"
            f"Telescope: {html.escape(obs['telescope'])}<br>"
            f"Mirror/Aperture: {obs['mirror_m']} m<br>"
            f"Altitude: {obs['alt_m']} m<br>"
            f"Country: {html.escape(obs['country'])}"
        )
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=max(4, min(14, obs["mirror_m"] * 1.2)),
            color="#06b6d4",
            fill=True,
            fill_color="#06b6d4",
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=html.escape(obs["name"]),
        ).add_to(m)
    return m, pd.DataFrame(WORLD_OBSERVATORIES)


def _build_light_pollution_map():
    """Map 2 -- Light Pollution with VIIRS Night Lights overlay."""
    m = _base_map(zoom=3)

    # VIIRS Night Lights tile overlay
    folium.TileLayer(
        tiles="https://map1.vis.earthdata.nasa.gov/wmts-webmerc/VIIRS_CityLights_2012/default/2012-01-01/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg",
        attr="NASA GIBS VIIRS",
        name="VIIRS Night Lights 2012",
        overlay=True,
        opacity=0.75,
    ).add_to(m)

    # Bortle zones around major cities
    bortle_colors = {
        9: "#ff0000",
        8: "#ff6600",
        7: "#ffaa00",
        6: "#ffff00",
        5: "#99cc00",
        4: "#33aa33",
        3: "#006633",
        2: "#003366",
        1: "#000033",
    }
    for zone in BORTLE_ZONES:
        color = bortle_colors.get(zone["bortle"], "#ff6600")
        popup_text = (
            f"<b>{html.escape(zone['city'])}</b><br>"
            f"Bortle Class: {zone['bortle']}<br>"
            f"Light Pollution Radius: ~{zone['radius_km']} km"
        )
        folium.Circle(
            location=[zone["lat"], zone["lon"]],
            radius=zone["radius_km"] * 1000,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.2,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"{html.escape(zone['city'])} (Bortle {zone['bortle']})",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    df = pd.DataFrame(BORTLE_ZONES)
    return m, df


def _build_impact_sites_map():
    """Map 3 -- Meteor Impact Sites."""
    m = _base_map()
    for site in METEOR_IMPACT_SITES:
        # Scale circle radius by crater diameter
        radius_px = max(4, min(18, site["diameter_km"] ** 0.5 * 1.5))
        if site["diameter_km"] >= 100:
            color = "#ff2222"
        elif site["diameter_km"] >= 30:
            color = "#ff8800"
        elif site["diameter_km"] >= 10:
            color = "#ffcc00"
        else:
            color = "#66ccff"
        popup_text = (
            f"<b>{html.escape(site['name'])}</b><br>"
            f"Diameter: {site['diameter_km']} km<br>"
            f"Age: {site['age_mya']} Mya<br>"
            f"Country: {html.escape(site['country'])}"
        )
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=radius_px,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=html.escape(site["name"]),
        ).add_to(m)
    return m, pd.DataFrame(METEOR_IMPACT_SITES)


def _build_launch_sites_map():
    """Map 4 -- Space Launch Sites."""
    m = _base_map()
    operator_colors = {
        "NASA": "#0066ff",
        "SpaceX": "#00ccff",
        "Roscosmos": "#ff3333",
        "ESA": "#33cc33",
        "JAXA": "#ff66cc",
        "ISRO": "#ff9900",
        "CNSA": "#ffcc00",
    }
    for site in SPACE_LAUNCH_SITES:
        color = "#8b97b0"
        for key, col in operator_colors.items():
            if key.lower() in site["operator"].lower():
                color = col
                break
        popup_text = (
            f"<b>{html.escape(site['name'])}</b><br>"
            f"Operator: {html.escape(site['operator'])}<br>"
            f"First Launch: {site['first_launch']}<br>"
            f"Country: {html.escape(site['country'])}"
        )
        folium.Marker(
            location=[site["lat"], site["lon"]],
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=html.escape(site["name"]),
            icon=folium.Icon(color="darkblue", icon="rocket", prefix="fa"),
        ).add_to(m)
    return m, pd.DataFrame(SPACE_LAUNCH_SITES)


def _build_radio_telescopes_map():
    """Map 5 -- Radio Telescopes."""
    m = _base_map()
    for rt in RADIO_TELESCOPES:
        radius_px = max(5, min(16, rt["dish_m"] ** 0.4 * 3))
        popup_text = (
            f"<b>{html.escape(rt['name'])}</b><br>"
            f"Dish Size: {rt['dish_m']} m<br>"
            f"Frequency: {html.escape(rt['freq_range'])}<br>"
            f"Country: {html.escape(rt['country'])}"
        )
        folium.CircleMarker(
            location=[rt["lat"], rt["lon"]],
            radius=radius_px,
            color="#a855f7",
            fill=True,
            fill_color="#a855f7",
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=html.escape(rt["name"]),
        ).add_to(m)
    return m, pd.DataFrame(RADIO_TELESCOPES)


def _build_dark_sky_reserves_map():
    """Map 6 -- Dark Sky Reserves."""
    m = _base_map()
    level_colors = {
        "Gold": "#ffd700",
        "Silver": "#c0c0c0",
        "Bronze": "#cd7f32",
        "N/A": "#06b6d4",
    }
    for reserve in DARK_SKY_RESERVES:
        color = level_colors.get(reserve["level"], "#06b6d4")
        popup_text = (
            f"<b>{html.escape(reserve['name'])}</b><br>"
            f"Level: {html.escape(reserve['level'])}<br>"
            f"Designation: {html.escape(reserve['designation'])}<br>"
            f"Country: {html.escape(reserve['country'])}"
        )
        folium.CircleMarker(
            location=[reserve["lat"], reserve["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=html.escape(reserve["name"]),
        ).add_to(m)
    return m, pd.DataFrame(DARK_SKY_RESERVES)


def _build_ground_stations_map():
    """Map 7 -- Satellite Ground Stations."""
    m = _base_map()
    network_colors = {
        "NASA DSN": "#0066ff",
        "ESA ESTRACK": "#33cc33",
        "JAXA": "#ff66cc",
        "ISRO ISTRAC": "#ff9900",
        "ISRO IDSN": "#ff9900",
        "Roscosmos": "#ff3333",
        "CNSA / CLTC": "#ffcc00",
        "NASA TDRS": "#3399ff",
        "KSAT": "#00cccc",
        "KSAT / ESA": "#00ccaa",
        "SANSA": "#cc66ff",
        "Former Soviet DSN": "#cc3333",
    }
    for station in SATELLITE_GROUND_STATIONS:
        color = network_colors.get(station["network"], "#8b97b0")
        popup_text = (
            f"<b>{html.escape(station['name'])}</b><br>"
            f"Network: {html.escape(station['network'])}<br>"
            f"Antenna: {station['antenna_m']} m<br>"
            f"Country: {html.escape(station['country'])}"
        )
        folium.CircleMarker(
            location=[station["lat"], station["lon"]],
            radius=max(5, min(14, station["antenna_m"] * 0.18)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=html.escape(station["name"]),
        ).add_to(m)
    return m, pd.DataFrame(SATELLITE_GROUND_STATIONS)


def _build_planetariums_map():
    """Map 8 -- Planetariums."""
    m = _base_map()
    for p in PLANETARIUMS:
        popup_text = (
            f"<b>{html.escape(p['name'])}</b><br>"
            f"City: {html.escape(p['city'])}<br>"
            f"Dome Diameter: {p['dome_m']} m<br>"
            f"Seats: {p['seats']}<br>"
            f"Country: {html.escape(p['country'])}"
        )
        folium.Marker(
            location=[p["lat"], p["lon"]],
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=html.escape(p["name"]),
            icon=folium.Icon(color="purple", icon="star", prefix="fa"),
        ).add_to(m)
    return m, pd.DataFrame(PLANETARIUMS)


def _build_astronomical_clocks_map():
    """Map 9 -- Astronomical Clocks."""
    m = _base_map(center=[50, 10], zoom=4)
    for clock in ASTRONOMICAL_CLOCKS:
        popup_text = (
            f"<b>{html.escape(clock['name'])}</b><br>"
            f"City: {html.escape(clock['city'])}<br>"
            f"Year Built: {clock['year_built']}<br>"
            f"Features: {html.escape(clock['features'])}<br>"
            f"Country: {html.escape(clock['country'])}"
        )
        folium.Marker(
            location=[clock["lat"], clock["lon"]],
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=html.escape(clock["name"]),
            icon=folium.Icon(color="orange", icon="clock-o", prefix="fa"),
        ).add_to(m)
    return m, pd.DataFrame(ASTRONOMICAL_CLOCKS)


def _build_solar_eclipse_map():
    """Map 10 -- Solar Eclipse Paths."""
    m = _base_map()
    eclipse_colors = ["#ff4444", "#ff8800", "#ffcc00", "#44cc44", "#4488ff"]
    rows = []
    for i, eclipse in enumerate(SOLAR_ECLIPSE_PATHS):
        color = eclipse_colors[i % len(eclipse_colors)]
        path_coords = [[p[0], p[1]] for p in eclipse["path"]]

        regions_text = html.escape(eclipse.get("regions", ""))
        popup_content = (
            f"<b>{html.escape(eclipse['name'])}</b><br>"
            f"Date: {html.escape(eclipse['date'])}<br>"
            f"Max Duration: {eclipse['max_duration_s']} s<br>"
            f"Path Width: {eclipse['path_width_km']} km<br>"
            f"Regions: {regions_text}"
        )

        folium.PolyLine(
            locations=path_coords,
            color=color,
            weight=6,
            opacity=0.8,
            tooltip=html.escape(eclipse["name"]),
            popup=folium.Popup(popup_content, max_width=320),
        ).add_to(m)

        # Add markers at start and end of path
        folium.CircleMarker(
            location=path_coords[0],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"Start: {html.escape(eclipse['name'])}",
        ).add_to(m)
        folium.CircleMarker(
            location=path_coords[-1],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"End: {html.escape(eclipse['name'])}",
        ).add_to(m)

        rows.append({
            "name": eclipse["name"],
            "date": eclipse["date"],
            "max_duration_s": eclipse["max_duration_s"],
            "path_width_km": eclipse["path_width_km"],
            "regions": eclipse.get("regions", ""),
            "num_waypoints": len(path_coords),
        })

    df = pd.DataFrame(rows)
    return m, df


# ---------------------------------------------------------------------------
# Builder dispatch
# ---------------------------------------------------------------------------

MAP_BUILDERS = {
    MAP_TYPES[0]: _build_observatories_map,
    MAP_TYPES[1]: _build_light_pollution_map,
    MAP_TYPES[2]: _build_impact_sites_map,
    MAP_TYPES[3]: _build_launch_sites_map,
    MAP_TYPES[4]: _build_radio_telescopes_map,
    MAP_TYPES[5]: _build_dark_sky_reserves_map,
    MAP_TYPES[6]: _build_ground_stations_map,
    MAP_TYPES[7]: _build_planetariums_map,
    MAP_TYPES[8]: _build_astronomical_clocks_map,
    MAP_TYPES[9]: _build_solar_eclipse_map,
}

MAP_DESCRIPTIONS = {
    MAP_TYPES[0]: "61 major optical and gravitational-wave observatories worldwide with telescope specs, mirror sizes, and altitudes.",
    MAP_TYPES[1]: "NASA VIIRS satellite night-lights overlay combined with Bortle scale light-pollution zones around 20 major cities.",
    MAP_TYPES[2]: "41 confirmed meteor impact craters from the 300 km Vredefort to the 0.11 km Kaali, colour-coded by size.",
    MAP_TYPES[3]: "31 active and historic space launch facilities with operator info and first-launch year.",
    MAP_TYPES[4]: "26 radio telescopes and interferometer arrays with dish sizes and frequency ranges.",
    MAP_TYPES[5]: "31 IDA-certified and Starlight dark-sky reserves, parks, and sanctuaries colour-coded by certification level.",
    MAP_TYPES[6]: "25 satellite ground stations across NASA DSN, ESA ESTRACK, JAXA, ISRO, Roscosmos, and CNSA networks.",
    MAP_TYPES[7]: "31 major planetariums worldwide with dome diameter and seating capacity.",
    MAP_TYPES[8]: "15 famous medieval and Renaissance astronomical clocks across Europe with construction dates and features.",
    MAP_TYPES[9]: "Paths of 5 upcoming total solar eclipses (2026-2034) drawn as polyline corridors with duration and width data.",
}


# ---------------------------------------------------------------------------
# Info panel per map type
# ---------------------------------------------------------------------------

_INFO_PANELS = {
    MAP_TYPES[0]: (
        "About World Observatories",
        "This map displays **61 major astronomical observatories** spanning optical "
        "telescopes, gravitational-wave detectors, and planned next-generation "
        "facilities. Marker size scales with mirror/aperture diameter. Observatories "
        "at extreme altitudes (e.g. ALMA at 5,058 m, Hanle at 4,500 m) are shown in "
        "their precise geographic locations.\n\n"
        "**Colour:** cyan circles. **Size:** proportional to mirror diameter."
    ),
    MAP_TYPES[1]: (
        "About Light Pollution",
        "The VIIRS Day/Night Band (DNB) satellite composite from NASA GIBS reveals "
        "artificial illumination across Earth. Overlaid circles show approximate "
        "**Bortle class** light pollution zones around 20 major metropolitan areas.\n\n"
        "**Bortle Scale:** 1 = pristine dark sky, 9 = inner-city sky glow. "
        "Circles are colour-coded from red (Bortle 9) through yellow/green to "
        "deep blue (Bortle 1)."
    ),
    MAP_TYPES[2]: (
        "About Meteor Impact Sites",
        "41 confirmed terrestrial impact structures are displayed, from the massive "
        "**Vredefort** (300 km, 2,023 Mya) and **Chicxulub** (180 km, 66 Mya) to "
        "small recent craters like **Kaali** (110 m, ~4,000 years ago).\n\n"
        "**Colour coding:** Red = diameter >= 100 km, Orange = 30-99 km, "
        "Yellow = 10-29 km, Light blue = < 10 km."
    ),
    MAP_TYPES[3]: (
        "About Space Launch Sites",
        "31 orbital and suborbital launch facilities are mapped with rocket-icon "
        "markers. Includes active sites like **Cape Canaveral**, **Baikonur**, "
        "**Kourou**, and newer facilities such as **Starbase Boca Chica** and "
        "**Rocket Lab LC-1** in New Zealand.\n\n"
        "**Marker colour** is keyed to major agency/operator where identifiable."
    ),
    MAP_TYPES[4]: (
        "About Radio Telescopes",
        "26 single-dish and interferometer facilities are shown with purple markers "
        "scaled by dish diameter. From the colossal **FAST** (500 m) in Guizhou, "
        "China to compact millimeter-wave arrays like **NOEMA** (15 m dishes).\n\n"
        "The now-collapsed **Arecibo** (305 m) is included for historical reference."
    ),
    MAP_TYPES[5]: (
        "About Dark Sky Reserves",
        "31 IDA-designated dark sky places and Starlight Reserves are mapped, "
        "colour-coded by certification level:\n\n"
        "- **Gold** markers: pristine dark sky, minimal light pollution\n"
        "- **Silver** markers: excellent dark sky with minor light domes\n"
        "- **Cyan** markers: other designations (sanctuary, preserve, town)"
    ),
    MAP_TYPES[6]: (
        "About Satellite Ground Stations",
        "25 deep-space communication and tracking antennas from six networks:\n\n"
        "- **NASA DSN** (Goldstone, Madrid, Canberra) -- 70 m antennas\n"
        "- **ESA ESTRACK** (Malargue, Cebreros, New Norcia, and more)\n"
        "- **JAXA**, **ISRO**, **Roscosmos**, **CNSA** stations\n"
        "- **KSAT** polar stations (Svalbard, Troll Antarctica)\n\n"
        "Marker size scales with antenna diameter."
    ),
    MAP_TYPES[7]: (
        "About Planetariums",
        "31 major planetariums across the globe with dome diameter and seating "
        "capacity. The world's largest planetarium dome is at the **Nagoya City "
        "Science Museum** (35 m). Historic venues include the **Adler Planetarium** "
        "(1930, first in the Western Hemisphere)."
    ),
    MAP_TYPES[8]: (
        "About Astronomical Clocks",
        "15 renowned astronomical clocks, mostly in European cathedrals and town "
        "halls, dating from 1344 (Padua) to 1967 (Lubeck replacement). These "
        "mechanical marvels display planetary positions, zodiac signs, lunar phases, "
        "and ecclesiastical calendars. The **Prague Orloj** (1410) is the world's "
        "oldest still-operating astronomical clock."
    ),
    MAP_TYPES[9]: (
        "About Solar Eclipse Paths",
        "Paths of **5 upcoming total solar eclipses** (2026--2034) are drawn as "
        "polyline corridors. Each line shows the approximate centreline of totality.\n\n"
        "- **Aug 2026** (red): Arctic to Spain, max 2 min 18 s\n"
        "- **Aug 2027** (orange): Atlantic to East Africa, max 6 min 22 s\n"
        "- **Jul 2028** (yellow): Indian Ocean to Pacific via Australia\n"
        "- **Nov 2030** (green): Southern Africa to Australia\n"
        "- **Mar 2034** (blue): Africa across Asia to Japan"
    ),
}


def _render_info_panel(selected_map):
    """Render an information/legend expander for the given map type."""
    title, body = _INFO_PANELS.get(selected_map, ("Info", "No additional information."))
    with st.expander(title, expanded=False):
        st.markdown(body)


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_astronomy_maps_tab():
    """Render the Astronomy & Sky Maps tab in the Streamlit app."""

    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Astronomy &amp; Sky Maps</h4>"
        "<p>Observatories, light pollution, impact sites, launch facilities, dark sky reserves</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ----- Controls -----
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_map = st.selectbox(
            "Select Map Type",
            MAP_TYPES,
            index=0,
            key="astronomy_map_type",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button("Generate Map", key="astronomy_generate", type="primary")

    st.caption(MAP_DESCRIPTIONS.get(selected_map, ""))

    if not generate:
        st.info("Select a map type and click **Generate Map** to explore astronomy data.")
        return

    # ----- Build map -----
    with st.spinner(f"Building {selected_map} map..."):
        builder = MAP_BUILDERS.get(selected_map)
        if builder is None:
            st.error("Unknown map type.")
            return
        m, df = builder()

    # ----- Stats metrics -----
    st.markdown("---")
    st.subheader("Summary Statistics")

    if selected_map == MAP_TYPES[0]:
        # Observatories
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Observatories", len(WORLD_OBSERVATORIES))
        countries = len(set(o["country"] for o in WORLD_OBSERVATORIES))
        c2.metric("Countries", countries)
        max_alt = max(o["alt_m"] for o in WORLD_OBSERVATORIES)
        c3.metric("Highest Altitude", f"{max_alt:,} m")
        max_mirror = max(o["mirror_m"] for o in WORLD_OBSERVATORIES)
        c4.metric("Largest Mirror", f"{max_mirror} m")

    elif selected_map == MAP_TYPES[1]:
        # Light pollution
        c1, c2, c3 = st.columns(3)
        c1.metric("Cities Mapped", len(BORTLE_ZONES))
        avg_bortle = sum(z["bortle"] for z in BORTLE_ZONES) / len(BORTLE_ZONES)
        c2.metric("Avg Bortle Class", f"{avg_bortle:.1f}")
        max_radius = max(z["radius_km"] for z in BORTLE_ZONES)
        c3.metric("Max Light Radius", f"{max_radius} km")

    elif selected_map == MAP_TYPES[2]:
        # Impact sites
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Impact Sites", len(METEOR_IMPACT_SITES))
        largest = max(METEOR_IMPACT_SITES, key=lambda s: s["diameter_km"])
        c2.metric("Largest Crater", f"{largest['diameter_km']} km")
        youngest = min(METEOR_IMPACT_SITES, key=lambda s: s["age_mya"])
        c3.metric("Most Recent", f"{youngest['age_mya']} Mya")
        countries = len(set(s["country"] for s in METEOR_IMPACT_SITES))
        c4.metric("Countries", countries)

    elif selected_map == MAP_TYPES[3]:
        # Launch sites
        c1, c2, c3 = st.columns(3)
        c1.metric("Launch Sites", len(SPACE_LAUNCH_SITES))
        countries = len(set(s["country"] for s in SPACE_LAUNCH_SITES))
        c2.metric("Countries", countries)
        oldest = min(SPACE_LAUNCH_SITES, key=lambda s: s["first_launch"])
        c3.metric("Earliest Facility", f"{oldest['first_launch']}")

    elif selected_map == MAP_TYPES[4]:
        # Radio telescopes
        c1, c2, c3 = st.columns(3)
        c1.metric("Radio Telescopes", len(RADIO_TELESCOPES))
        largest = max(RADIO_TELESCOPES, key=lambda r: r["dish_m"])
        c2.metric("Largest Dish", f"{largest['dish_m']} m")
        countries = len(set(r["country"] for r in RADIO_TELESCOPES))
        c3.metric("Countries", countries)

    elif selected_map == MAP_TYPES[5]:
        # Dark sky
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dark Sky Sites", len(DARK_SKY_RESERVES))
        gold = sum(1 for r in DARK_SKY_RESERVES if r["level"] == "Gold")
        c2.metric("Gold Level", gold)
        silver = sum(1 for r in DARK_SKY_RESERVES if r["level"] == "Silver")
        c3.metric("Silver Level", silver)
        countries = len(set(r["country"] for r in DARK_SKY_RESERVES))
        c4.metric("Countries", countries)

    elif selected_map == MAP_TYPES[6]:
        # Ground stations
        c1, c2, c3 = st.columns(3)
        c1.metric("Ground Stations", len(SATELLITE_GROUND_STATIONS))
        networks = len(set(s["network"] for s in SATELLITE_GROUND_STATIONS))
        c2.metric("Networks", networks)
        max_ant = max(s["antenna_m"] for s in SATELLITE_GROUND_STATIONS)
        c3.metric("Largest Antenna", f"{max_ant} m")

    elif selected_map == MAP_TYPES[7]:
        # Planetariums
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Planetariums", len(PLANETARIUMS))
        max_dome = max(p["dome_m"] for p in PLANETARIUMS)
        c2.metric("Largest Dome", f"{max_dome} m")
        max_seats = max(p["seats"] for p in PLANETARIUMS)
        c3.metric("Most Seats", f"{max_seats:,}")
        countries = len(set(p["country"] for p in PLANETARIUMS))
        c4.metric("Countries", countries)

    elif selected_map == MAP_TYPES[8]:
        # Astronomical clocks
        c1, c2, c3 = st.columns(3)
        c1.metric("Astronomical Clocks", len(ASTRONOMICAL_CLOCKS))
        oldest = min(ASTRONOMICAL_CLOCKS, key=lambda c: c["year_built"])
        c2.metric("Oldest", f"{oldest['year_built']} AD")
        countries = len(set(c["country"] for c in ASTRONOMICAL_CLOCKS))
        c3.metric("Countries", countries)

    elif selected_map == MAP_TYPES[9]:
        # Solar eclipses
        c1, c2, c3 = st.columns(3)
        c1.metric("Eclipse Paths", len(SOLAR_ECLIPSE_PATHS))
        max_dur = max(e["max_duration_s"] for e in SOLAR_ECLIPSE_PATHS)
        c2.metric("Longest Duration", f"{max_dur} s")
        next_eclipse = min(SOLAR_ECLIPSE_PATHS, key=lambda e: e["date"])
        c3.metric("Next Eclipse", next_eclipse["date"])

    # ----- Folium Map -----
    st.markdown("---")
    st.subheader(f"{selected_map} Map")
    map_html = m._repr_html_()
    components.html(map_html, height=550)

    # ----- Data Table -----
    st.markdown("---")
    st.subheader("Data Table")
    st.dataframe(df, width="stretch")

    # ----- Download CSV -----
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    csv_data = csv_buf.getvalue()
    file_label = selected_map.lower().replace(" ", "_").replace("(", "").replace(")", "")
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"astronomy_{file_label}.csv",
        mime="text/csv",
        key="astronomy_csv_download",
    )

    # ----- Legend / Info Panel -----
    st.markdown("---")
    _render_info_panel(selected_map)


# ---------------------------------------------------------------------------
# Allow standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    st.set_page_config(page_title="Astronomy & Sky Maps", layout="wide")
    render_astronomy_maps_tab()
