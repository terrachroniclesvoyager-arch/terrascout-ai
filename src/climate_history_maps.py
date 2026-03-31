# -*- coding: utf-8 -*-
"""
Climate History & Paleoclimate module for TerraScout AI.
Curated datasets covering ice ages, medieval warm period, little ice age,
sea level history, desertification, glacier retreat, historical droughts,
climate proxy sites, extreme weather records, and climate tipping points.
All data is hardcoded / curated -- no external API keys required.
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

# =====================================================================
# THEME COLORS
# =====================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_TEXT_SEC = "#8b97b0"
_ACCENT = "#06b6d4"
_GRID = "#2a3550"

# Per-mode accent palette
_CLR_ICE = "#38bdf8"
_CLR_WARM = "#f97316"
_CLR_COLD = "#818cf8"
_CLR_SEA = "#06b6d4"
_CLR_DESERT = "#f59e0b"
_CLR_GLACIER = "#67e8f9"
_CLR_DROUGHT = "#ef4444"
_CLR_PROXY = "#a855f7"
_CLR_EXTREME = "#ec4899"
_CLR_TIPPING = "#10b981"

# =====================================================================
# MODE LIST
# =====================================================================
MODES = [
    "Ice Ages & Glaciation",
    "Medieval Warm Period",
    "Little Ice Age",
    "Sea Level History",
    "Desertification Advance",
    "Glacier Retreat",
    "Historical Droughts",
    "Ancient Climate Proxy Sites",
    "Extreme Weather Records",
    "Climate Tipping Points",
]

# =====================================================================
# 1. ICE AGES & GLACIATION
# =====================================================================
ICE_AGES = [
    {"name": "Huronian Glaciation", "start_mya": 2400, "end_mya": 2100, "severity": "Global", "lat": 46.5, "lon": -81.0, "notes": "Earliest known glaciation, evidence in Ontario Canada"},
    {"name": "Sturtian Glaciation", "start_mya": 717, "end_mya": 660, "severity": "Snowball Earth", "lat": -23.6, "lon": 134.0, "notes": "Snowball Earth event, evidence in Australia"},
    {"name": "Marinoan Glaciation", "start_mya": 650, "end_mya": 635, "severity": "Snowball Earth", "lat": -31.4, "lon": 138.7, "notes": "Second Snowball Earth, Flinders Ranges Australia"},
    {"name": "Gaskiers Glaciation", "start_mya": 580, "end_mya": 579, "severity": "Regional", "lat": 47.5, "lon": -52.8, "notes": "Short glaciation, Newfoundland evidence"},
    {"name": "Andean-Saharan Glaciation", "start_mya": 450, "end_mya": 420, "severity": "Continental", "lat": -30.0, "lon": 25.0, "notes": "Late Ordovician, Gondwana ice sheet"},
    {"name": "Late Paleozoic Ice Age", "start_mya": 360, "end_mya": 260, "severity": "Continental", "lat": -33.9, "lon": 18.4, "notes": "Karoo Ice Age, longest Phanerozoic glaciation"},
    {"name": "Quaternary Glaciation (onset)", "start_mya": 2.58, "end_mya": 0.0, "severity": "Continental", "lat": 78.2, "lon": 15.6, "notes": "Current ice age, Pleistocene-Holocene cycles"},
    {"name": "Gunz Glaciation", "start_mya": 0.68, "end_mya": 0.62, "severity": "Alpine", "lat": 47.4, "lon": 10.9, "notes": "Alpine glacial stage, named after Gunz River Bavaria"},
    {"name": "Mindel Glaciation", "start_mya": 0.48, "end_mya": 0.42, "severity": "Alpine", "lat": 48.1, "lon": 10.5, "notes": "Alpine glacial stage, named after Mindel River"},
    {"name": "Riss Glaciation", "start_mya": 0.30, "end_mya": 0.13, "severity": "Alpine/Continental", "lat": 48.3, "lon": 9.7, "notes": "Penultimate glaciation in Alps, extensive ice sheets"},
    {"name": "Illinoian Glaciation", "start_mya": 0.19, "end_mya": 0.13, "severity": "Continental", "lat": 40.0, "lon": -89.0, "notes": "North American glacial stage covering Illinois"},
    {"name": "Wurm / Wisconsin Glaciation", "start_mya": 0.115, "end_mya": 0.012, "severity": "Continental", "lat": 51.0, "lon": -114.0, "notes": "Last Glacial Maximum ~21 kya, ice reached 40N in NA"},
    {"name": "Last Glacial Maximum (LGM)", "start_mya": 0.026, "end_mya": 0.019, "severity": "Global", "lat": 65.0, "lon": -18.0, "notes": "Peak ice extent: 3 km thick Laurentide sheet, sea level -120 m"},
    {"name": "Younger Dryas", "start_mya": 0.0129, "end_mya": 0.01170, "severity": "Regional", "lat": 72.6, "lon": -38.5, "notes": "Abrupt cold reversal ~12,900 BP, linked to AMOC shutdown"},
    {"name": "8.2 kya Event", "start_mya": 0.0082, "end_mya": 0.0080, "severity": "Regional", "lat": 58.0, "lon": -95.0, "notes": "Lake Agassiz drainage caused abrupt cooling"},
]

# Extent polylines: approximate southern ice-sheet boundary at LGM
LGM_EXTENT_COORDS = [
    # North America Laurentide
    [40.0, -75.0], [41.0, -82.0], [42.0, -89.0], [46.0, -100.0],
    [48.0, -110.0], [52.0, -120.0], [58.0, -135.0], [60.0, -145.0],
    # Eurasia Fennoscandian
    [52.0, -2.0], [52.5, 5.0], [54.0, 12.0], [56.0, 20.0],
    [58.0, 30.0], [60.0, 40.0], [62.0, 50.0], [65.0, 60.0],
]

# =====================================================================
# 2. MEDIEVAL WARM PERIOD (900-1300 CE)
# =====================================================================
MEDIEVAL_WARM = [
    {"name": "Norse Greenland Settlement", "year": 985, "lat": 61.2, "lon": -45.4, "event": "Viking colonization of Greenland under Erik the Red", "evidence": "Archaeological ruins, sagas"},
    {"name": "Norse Vinland Expedition", "year": 1000, "lat": 51.6, "lon": -55.5, "event": "Leif Erikson reaches Newfoundland (L'Anse aux Meadows)", "evidence": "Archaeological site, UNESCO"},
    {"name": "English Vineyards Peak", "year": 1100, "lat": 51.5, "lon": -0.1, "event": "Wine production as far north as York, Domesday Book records", "evidence": "Historical records, pollen"},
    {"name": "Alpine Pass Opening", "year": 1050, "lat": 46.0, "lon": 7.8, "event": "High Alpine passes ice-free, expanded trade routes", "evidence": "Artifact finds in glacial retreat zones"},
    {"name": "Anasazi Flourishing", "year": 1100, "lat": 36.0, "lon": -107.9, "event": "Chaco Canyon Puebloan culture peak, favorable rains", "evidence": "Tree rings, archaeological remains"},
    {"name": "Khmer Empire Expansion", "year": 1150, "lat": 13.4, "lon": 103.9, "event": "Angkor Wat construction during favorable monsoon era", "evidence": "Sediment cores, tree rings"},
    {"name": "Chinese Song Dynasty Agriculture", "year": 1100, "lat": 30.3, "lon": 120.2, "event": "Rice double-cropping expansion, population boom to ~100 M", "evidence": "Historical records, pollen analysis"},
    {"name": "Cahokia Flourishing", "year": 1050, "lat": 38.7, "lon": -90.1, "event": "Mississippian mound city peak population ~20,000", "evidence": "Archaeological excavation, tree rings"},
    {"name": "North Atlantic Warm Current", "year": 1000, "lat": 62.0, "lon": -20.0, "event": "Stronger AMOC, reduced Arctic sea ice, open sailing routes", "evidence": "Marine sediment proxies"},
    {"name": "Sahel Green Phase", "year": 1000, "lat": 14.0, "lon": 0.0, "event": "Enhanced West African monsoon, Lake Chad expansion", "evidence": "Sediment cores, pollen records"},
    {"name": "Polynesian Expansion Peak", "year": 1200, "lat": -17.5, "lon": -149.8, "event": "Settlement of remote Pacific islands during calm conditions", "evidence": "Radiocarbon dating, oral tradition"},
    {"name": "Medieval Japanese Warm Phase", "year": 1100, "lat": 35.0, "lon": 136.0, "event": "Cherry blossom records show earlier spring bloom", "evidence": "Heian court diaries, phenological records"},
    {"name": "Novgorod Trading Boom", "year": 1150, "lat": 58.5, "lon": 31.3, "event": "Extended ice-free rivers boosted Hanseatic trade", "evidence": "Trade records, dendrochronology"},
    {"name": "Tiwanaku Decline", "year": 1000, "lat": -16.6, "lon": -68.7, "event": "Drought stressed Andean agriculture, empire collapse", "evidence": "Ice cores from Quelccaya, lake cores"},
    {"name": "Central European Forest Clearing", "year": 1100, "lat": 50.0, "lon": 12.0, "event": "Warm conditions spurred massive German forest clearing", "evidence": "Pollen diagrams, charcoal records"},
]

# =====================================================================
# 3. LITTLE ICE AGE (1300-1850)
# =====================================================================
LITTLE_ICE_AGE = [
    {"name": "Great Famine of 1315-1317", "year": 1315, "lat": 51.0, "lon": 3.0, "event": "Crop failures from cold wet summers, millions died", "region": "Northern Europe"},
    {"name": "Norse Greenland Abandonment", "year": 1408, "lat": 61.2, "lon": -45.4, "event": "Last recorded Norse settlement contact, sea ice expanded", "region": "Greenland"},
    {"name": "Thames Frost Fairs", "year": 1607, "lat": 51.5, "lon": -0.1, "event": "River Thames froze repeatedly 1607-1814, fairs held on ice", "region": "England"},
    {"name": "Maunder Minimum", "year": 1645, "lat": 48.9, "lon": 2.3, "event": "Near-zero sunspots 1645-1715, coldest LIA phase", "region": "Global"},
    {"name": "Year Without a Summer (1816)", "year": 1816, "lat": 46.2, "lon": 6.1, "event": "Tambora eruption caused global cooling, crop failures", "region": "Global"},
    {"name": "Tambora Eruption", "year": 1815, "lat": -8.25, "lon": 118.0, "event": "VEI-7 eruption, largest in recorded history, 71,000+ deaths", "region": "Indonesia/Global"},
    {"name": "Grindelwald Fluctuation", "year": 1600, "lat": 46.6, "lon": 8.0, "event": "Swiss glaciers advanced to destroy villages", "region": "Swiss Alps"},
    {"name": "Dutch Golden Age Canal Freezing", "year": 1650, "lat": 52.4, "lon": 4.9, "event": "Dutch canals regularly frozen, ice-skating culture", "region": "Netherlands"},
    {"name": "Sporer Minimum", "year": 1460, "lat": 59.3, "lon": 18.1, "event": "Solar minimum 1460-1550, harsh Scandinavian winters", "region": "Northern Europe"},
    {"name": "Dalton Minimum", "year": 1790, "lat": 55.8, "lon": 37.6, "event": "Solar minimum 1790-1830, Napoleon's disastrous 1812 winter", "region": "Global"},
    {"name": "Huaynaputina Eruption", "year": 1600, "lat": -16.6, "lon": -70.9, "event": "VEI-6 eruption, caused coldest year in 500 yrs in N. Hemisphere", "region": "Peru/Global"},
    {"name": "Swiss Alpine Village Burial", "year": 1650, "lat": 46.0, "lon": 7.7, "event": "Village of Le Chatelard destroyed by advancing glacier", "region": "Swiss Alps"},
    {"name": "Iceland Famine (Mist Hardships)", "year": 1783, "lat": 64.1, "lon": -21.9, "event": "Laki eruption: fluorine poisoning, crop failure, 25% population died", "region": "Iceland"},
    {"name": "Baltic Sea Freezing", "year": 1709, "lat": 59.3, "lon": 18.1, "event": "Great Frost of 1709, Baltic froze over, birds fell from sky", "region": "Northern Europe"},
    {"name": "Japanese Tenmei Famine", "year": 1783, "lat": 39.5, "lon": 140.3, "event": "Volcanic winters + floods caused mass famine in Tohoku", "region": "Japan"},
    {"name": "Chinese Qing Dynasty Famines", "year": 1640, "lat": 39.9, "lon": 116.4, "event": "Cold and drought contributed to Ming Dynasty collapse", "region": "China"},
    {"name": "Chamonix Glacier Advance", "year": 1644, "lat": 45.9, "lon": 6.9, "event": "Mer de Glace and Bossons glaciers threatened Chamonix", "region": "French Alps"},
    {"name": "Scottish Crop Failures", "year": 1690, "lat": 56.5, "lon": -4.0, "event": "Seven ill years 1695-1703, ~15% of population died", "region": "Scotland"},
]

# =====================================================================
# 4. SEA LEVEL HISTORY (major coastal cities + projected rise)
# =====================================================================
SEA_LEVEL_DATA = [
    {"city": "Miami", "lat": 25.76, "lon": -80.19, "elevation_m": 1.8, "current_rate_mm_yr": 3.9, "projected_2100_m": 0.6, "risk": "Critical", "notes": "Porous limestone foundation, king tides already flood streets"},
    {"city": "Shanghai", "lat": 31.23, "lon": 121.47, "elevation_m": 4.0, "current_rate_mm_yr": 3.5, "projected_2100_m": 0.7, "risk": "Critical", "notes": "Subsidence + sea rise threatens 24 M people"},
    {"city": "Jakarta", "lat": -6.21, "lon": 106.85, "elevation_m": 1.5, "current_rate_mm_yr": 4.0, "projected_2100_m": 0.8, "risk": "Critical", "notes": "Sinking up to 25 cm/yr in places, capital relocation planned"},
    {"city": "New York City", "lat": 40.71, "lon": -74.01, "elevation_m": 10.0, "current_rate_mm_yr": 3.3, "projected_2100_m": 0.6, "risk": "High", "notes": "Lower Manhattan and JFK airport vulnerable, Sandy showed risk"},
    {"city": "London", "lat": 51.51, "lon": -0.13, "elevation_m": 5.0, "current_rate_mm_yr": 2.8, "projected_2100_m": 0.5, "risk": "Moderate", "notes": "Thames Barrier built 1984, may need replacement by 2070"},
    {"city": "Mumbai", "lat": 19.08, "lon": 72.88, "elevation_m": 8.0, "current_rate_mm_yr": 3.2, "projected_2100_m": 0.6, "risk": "High", "notes": "20 M people, monsoon flooding + sea rise compound risk"},
    {"city": "Venice", "lat": 45.44, "lon": 12.34, "elevation_m": 1.0, "current_rate_mm_yr": 3.5, "projected_2100_m": 0.5, "risk": "Critical", "notes": "MOSE barriers operational 2020, acqua alta increasing"},
    {"city": "Bangkok", "lat": 13.76, "lon": 100.50, "elevation_m": 1.5, "current_rate_mm_yr": 3.7, "projected_2100_m": 0.7, "risk": "Critical", "notes": "Subsidence + sea rise, parts may be underwater by 2050"},
    {"city": "Alexandria", "lat": 31.20, "lon": 29.92, "elevation_m": 2.0, "current_rate_mm_yr": 3.0, "projected_2100_m": 0.5, "risk": "Critical", "notes": "Nile delta subsidence, 2 M people at risk"},
    {"city": "Dhaka", "lat": 23.81, "lon": 90.41, "elevation_m": 4.0, "current_rate_mm_yr": 4.2, "projected_2100_m": 0.8, "risk": "Critical", "notes": "Ganges delta, 17% of Bangladesh could flood with 1 m rise"},
    {"city": "Ho Chi Minh City", "lat": 10.82, "lon": 106.63, "elevation_m": 2.0, "current_rate_mm_yr": 3.6, "projected_2100_m": 0.7, "risk": "Critical", "notes": "Mekong delta, 10 M people at risk from 1 m rise"},
    {"city": "Tokyo", "lat": 35.68, "lon": 139.69, "elevation_m": 5.0, "current_rate_mm_yr": 2.5, "projected_2100_m": 0.5, "risk": "Moderate", "notes": "Eastern Tokyo below sea level, massive flood defenses"},
    {"city": "Lagos", "lat": 6.52, "lon": 3.38, "elevation_m": 2.0, "current_rate_mm_yr": 3.8, "projected_2100_m": 0.7, "risk": "Critical", "notes": "21 M people, rapid growth on low-lying coastal land"},
    {"city": "Kolkata", "lat": 22.57, "lon": 88.36, "elevation_m": 6.0, "current_rate_mm_yr": 3.1, "projected_2100_m": 0.6, "risk": "High", "notes": "Ganges delta, cyclone storm surge risk amplified"},
    {"city": "Copenhagen", "lat": 55.68, "lon": 12.57, "elevation_m": 5.0, "current_rate_mm_yr": 2.5, "projected_2100_m": 0.4, "risk": "Moderate", "notes": "Low-lying harbor area, storm surge risk increasing"},
    {"city": "New Orleans", "lat": 29.95, "lon": -90.07, "elevation_m": -2.0, "current_rate_mm_yr": 4.5, "projected_2100_m": 0.8, "risk": "Critical", "notes": "Already below sea level, levee-dependent, Katrina precedent"},
    {"city": "Tuvalu (Funafuti)", "lat": -8.52, "lon": 179.20, "elevation_m": 1.0, "current_rate_mm_yr": 5.0, "projected_2100_m": 0.9, "risk": "Critical", "notes": "Pacific atoll nation, existential threat from any sea rise"},
    {"city": "Male (Maldives)", "lat": 4.18, "lon": 73.51, "elevation_m": 1.0, "current_rate_mm_yr": 4.0, "projected_2100_m": 0.8, "risk": "Critical", "notes": "Highest point 2.4 m, entire nation at existential risk"},
]

# =====================================================================
# 5. DESERTIFICATION ADVANCE
# =====================================================================
DESERTIFICATION = [
    {"name": "Sahel Desertification Front", "lat": 14.0, "lon": 0.0, "area": "Sahel Belt", "rate_km_yr": 0.8, "period": "1950-present", "cause": "Overgrazing, climate shift", "notes": "Southern Sahara edge advancing, Lake Chad shrank 90%"},
    {"name": "Gobi Desert Expansion", "lat": 42.5, "lon": 103.0, "area": "Mongolia/China", "rate_km_yr": 3.6, "period": "1950-present", "cause": "Overgrazing, wind erosion", "notes": "3,600 km2/yr expansion, Beijing sandstorms"},
    {"name": "Aral Sea Desiccation", "lat": 45.0, "lon": 59.6, "area": "Central Asia", "rate_km_yr": 2.0, "period": "1960-present", "cause": "Irrigation diversion", "notes": "Lost 90% of volume since 1960, toxic dust storms"},
    {"name": "Thar Desert Advance", "lat": 27.0, "lon": 71.0, "area": "India/Pakistan", "rate_km_yr": 0.5, "period": "1970-present", "cause": "Overgrazing, deforestation", "notes": "Indira Gandhi Canal partially reversed trend"},
    {"name": "Atacama Hyper-Arid Zone", "lat": -24.5, "lon": -69.2, "area": "Chile", "rate_km_yr": 0.1, "period": "Stable/slow", "cause": "Rain shadow, cold current", "notes": "Driest non-polar desert, some areas no rain for centuries"},
    {"name": "Australian Outback Expansion", "lat": -25.3, "lon": 134.0, "area": "Australia", "rate_km_yr": 0.3, "period": "1980-present", "cause": "Drought cycles, land clearing", "notes": "Murray-Darling basin severe stress"},
    {"name": "Mesopotamian Marshlands Drain", "lat": 31.0, "lon": 47.0, "area": "Iraq", "rate_km_yr": 1.5, "period": "1991-2003", "cause": "Deliberate drainage", "notes": "90% drained by 2000, partial restoration ongoing"},
    {"name": "Horn of Africa Drying", "lat": 8.0, "lon": 45.0, "area": "Somalia/Ethiopia", "rate_km_yr": 0.6, "period": "1970-present", "cause": "Climate change, overgrazing", "notes": "Recurring mega-droughts, pastoral collapse"},
    {"name": "Patagonian Steppe Degradation", "lat": -45.0, "lon": -70.0, "area": "Argentina", "rate_km_yr": 0.4, "period": "1980-present", "cause": "Sheep overgrazing, wind erosion", "notes": "70% of Patagonian steppe degraded"},
    {"name": "Rajasthan Desert Encroachment", "lat": 26.9, "lon": 70.9, "area": "India", "rate_km_yr": 0.5, "period": "1960-present", "cause": "Groundwater depletion", "notes": "Villages being buried by sand dunes"},
    {"name": "Lake Chad Shrinkage", "lat": 13.0, "lon": 14.0, "area": "Chad Basin", "rate_km_yr": 1.0, "period": "1963-present", "cause": "Climate + irrigation", "notes": "From 25,000 km2 to ~1,350 km2"},
    {"name": "Northern China Desertification", "lat": 40.0, "lon": 110.0, "area": "Inner Mongolia", "rate_km_yr": 2.5, "period": "1950-present", "cause": "Overgrazing, mining", "notes": "Great Green Wall project aims to halt expansion"},
    {"name": "Kalahari Margins", "lat": -23.0, "lon": 22.0, "area": "Southern Africa", "rate_km_yr": 0.3, "period": "1970-present", "cause": "Rainfall decline, cattle ranching", "notes": "Dune reactivation observed on margins"},
    {"name": "Mediterranean Basin Drying", "lat": 37.0, "lon": 15.0, "area": "Southern Europe", "rate_km_yr": 0.2, "period": "1980-present", "cause": "Climate change, agriculture", "notes": "SE Spain, Sicily, Greece experiencing semi-arid shift"},
]

# =====================================================================
# 6. GLACIER RETREAT (30+ major glaciers)
# =====================================================================
GLACIER_RETREAT = [
    {"name": "Jakobshavn Isbrae", "lat": 69.17, "lon": -49.83, "country": "Greenland", "retreat_km": 40.0, "period": "1850-2023", "status": "Rapid retreat", "type": "Outlet glacier"},
    {"name": "Pine Island Glacier", "lat": -75.17, "lon": -100.0, "country": "Antarctica", "retreat_km": 35.0, "period": "1990-2023", "status": "Accelerating", "type": "Ice stream"},
    {"name": "Thwaites Glacier", "lat": -75.5, "lon": -106.75, "country": "Antarctica", "retreat_km": 14.0, "period": "2000-2023", "status": "Critical", "type": "Ice stream"},
    {"name": "Mer de Glace", "lat": 45.9, "lon": 6.93, "country": "France", "retreat_km": 2.5, "period": "1850-2023", "status": "Rapid retreat", "type": "Valley glacier"},
    {"name": "Aletsch Glacier", "lat": 46.45, "lon": 8.07, "country": "Switzerland", "retreat_km": 3.6, "period": "1850-2023", "status": "Retreating", "type": "Valley glacier"},
    {"name": "Rhone Glacier", "lat": 46.58, "lon": 8.39, "country": "Switzerland", "retreat_km": 1.7, "period": "1850-2023", "status": "Rapid retreat", "type": "Valley glacier"},
    {"name": "Gangotri Glacier", "lat": 30.92, "lon": 79.08, "country": "India", "retreat_km": 2.0, "period": "1936-2023", "status": "Retreating", "type": "Valley glacier"},
    {"name": "Siachen Glacier", "lat": 35.42, "lon": 77.1, "country": "India/Pakistan", "retreat_km": 1.8, "period": "1960-2023", "status": "Retreating", "type": "Valley glacier"},
    {"name": "Khumbu Glacier", "lat": 27.98, "lon": 86.83, "country": "Nepal", "retreat_km": 1.0, "period": "1970-2023", "status": "Thinning rapidly", "type": "Valley glacier"},
    {"name": "Perito Moreno Glacier", "lat": -50.5, "lon": -73.05, "country": "Argentina", "retreat_km": 0.2, "period": "1850-2023", "status": "Stable (anomaly)", "type": "Calving glacier"},
    {"name": "Columbia Glacier", "lat": 61.15, "lon": -147.1, "country": "USA (Alaska)", "retreat_km": 20.0, "period": "1980-2023", "status": "Catastrophic retreat", "type": "Tidewater glacier"},
    {"name": "Mendenhall Glacier", "lat": 58.42, "lon": -134.55, "country": "USA (Alaska)", "retreat_km": 3.0, "period": "1929-2023", "status": "Retreating", "type": "Valley glacier"},
    {"name": "Muir Glacier", "lat": 59.0, "lon": -136.1, "country": "USA (Alaska)", "retreat_km": 50.0, "period": "1880-2023", "status": "Retreated out of sight", "type": "Tidewater glacier"},
    {"name": "Athabasca Glacier", "lat": 52.2, "lon": -117.23, "country": "Canada", "retreat_km": 1.5, "period": "1844-2023", "status": "Retreating", "type": "Outlet glacier"},
    {"name": "Quelccaya Ice Cap", "lat": -13.93, "lon": -70.83, "country": "Peru", "retreat_km": 1.6, "period": "1963-2023", "status": "Rapid retreat", "type": "Ice cap"},
    {"name": "Pastoruri Glacier", "lat": -9.9, "lon": -77.2, "country": "Peru", "retreat_km": 1.0, "period": "1980-2023", "status": "Near extinction", "type": "Mountain glacier"},
    {"name": "Furtwangler Glacier", "lat": -3.07, "lon": 37.35, "country": "Tanzania", "retreat_km": 0.3, "period": "1912-2023", "status": "Near extinction", "type": "Ice field"},
    {"name": "Lewis Glacier (Mt Kenya)", "lat": -0.15, "lon": 37.31, "country": "Kenya", "retreat_km": 0.4, "period": "1934-2023", "status": "Near extinction", "type": "Mountain glacier"},
    {"name": "Helheim Glacier", "lat": 66.35, "lon": -38.2, "country": "Greenland", "retreat_km": 8.0, "period": "2000-2023", "status": "Rapid retreat", "type": "Outlet glacier"},
    {"name": "Petermann Glacier", "lat": 80.75, "lon": -60.67, "country": "Greenland", "retreat_km": 30.0, "period": "2010-2023", "status": "Major calving events", "type": "Ice shelf/outlet"},
    {"name": "Franz Josef Glacier", "lat": -43.47, "lon": 170.17, "country": "New Zealand", "retreat_km": 3.0, "period": "1865-2023", "status": "Retreating", "type": "Valley glacier"},
    {"name": "Pasterze Glacier", "lat": 47.08, "lon": 12.7, "country": "Austria", "retreat_km": 2.0, "period": "1856-2023", "status": "Rapid retreat", "type": "Valley glacier"},
    {"name": "Jostedalsbreen", "lat": 61.67, "lon": 6.97, "country": "Norway", "retreat_km": 1.5, "period": "1900-2023", "status": "Retreating", "type": "Ice cap"},
    {"name": "Vatnajokull", "lat": 64.42, "lon": -16.8, "country": "Iceland", "retreat_km": 2.0, "period": "1890-2023", "status": "Thinning rapidly", "type": "Ice cap"},
    {"name": "Taku Glacier", "lat": 58.57, "lon": -134.05, "country": "USA (Alaska)", "retreat_km": 0.1, "period": "1890-2023", "status": "Recently started retreating", "type": "Valley glacier"},
    {"name": "Baltoro Glacier", "lat": 35.73, "lon": 76.5, "country": "Pakistan", "retreat_km": 0.6, "period": "1960-2023", "status": "Slow retreat", "type": "Valley glacier"},
    {"name": "Biafo Glacier", "lat": 35.85, "lon": 75.55, "country": "Pakistan", "retreat_km": 0.5, "period": "1960-2023", "status": "Slow retreat", "type": "Valley glacier"},
    {"name": "Fedchenko Glacier", "lat": 38.83, "lon": 72.28, "country": "Tajikistan", "retreat_km": 1.0, "period": "1933-2023", "status": "Retreating", "type": "Valley glacier"},
    {"name": "Nigardsbreen", "lat": 61.68, "lon": 7.22, "country": "Norway", "retreat_km": 2.5, "period": "1748-2023", "status": "Retreating", "type": "Outlet glacier"},
    {"name": "Gorner Glacier", "lat": 45.97, "lon": 7.8, "country": "Switzerland", "retreat_km": 2.5, "period": "1850-2023", "status": "Retreating", "type": "Valley glacier"},
    {"name": "South Cascade Glacier", "lat": 48.36, "lon": -121.06, "country": "USA (Washington)", "retreat_km": 0.7, "period": "1928-2023", "status": "Near extinction", "type": "Cirque glacier"},
    {"name": "Urumqi Glacier No. 1", "lat": 43.08, "lon": 86.82, "country": "China", "retreat_km": 0.3, "period": "1959-2023", "status": "Rapid retreat", "type": "Mountain glacier"},
]

# =====================================================================
# 7. HISTORICAL DROUGHTS
# =====================================================================
HISTORICAL_DROUGHTS = [
    {"name": "Dust Bowl", "lat": 36.5, "lon": -100.0, "year_start": 1930, "year_end": 1936, "severity": "Extreme", "deaths": "7,000+", "area_affected": "Great Plains, USA/Canada", "cause": "Drought + poor farming practices"},
    {"name": "Sahel Drought", "lat": 14.0, "lon": 0.0, "year_start": 1968, "year_end": 1974, "severity": "Catastrophic", "deaths": "100,000+", "area_affected": "West Africa Sahel belt", "cause": "Rainfall collapse + overgrazing"},
    {"name": "Horn of Africa Drought", "lat": 4.0, "lon": 42.0, "year_start": 2011, "year_end": 2012, "severity": "Catastrophic", "deaths": "260,000+", "area_affected": "Somalia, Kenya, Ethiopia", "cause": "La Nina + climate change"},
    {"name": "Chinese Famine Drought", "lat": 34.0, "lon": 108.0, "year_start": 1876, "year_end": 1879, "severity": "Catastrophic", "deaths": "9-13 million", "area_affected": "Northern China", "cause": "El Nino + monsoon failure"},
    {"name": "Indian Famine Drought", "lat": 23.0, "lon": 78.0, "year_start": 1876, "year_end": 1878, "severity": "Catastrophic", "deaths": "5-10 million", "area_affected": "Deccan Plateau, India", "cause": "El Nino + colonial policies"},
    {"name": "Medieval Megadrought (SW USA)", "lat": 34.5, "lon": -111.0, "year_start": 1276, "year_end": 1299, "severity": "Extreme", "deaths": "Unknown (Puebloan exodus)", "area_affected": "SW USA, Mesa Verde", "cause": "Natural climate variability"},
    {"name": "Millennium Drought (Australia)", "lat": -35.0, "lon": 145.0, "year_start": 1997, "year_end": 2009, "severity": "Extreme", "deaths": "Minimal (economic)", "area_affected": "SE Australia, Murray-Darling", "cause": "Climate change + El Nino"},
    {"name": "California Drought", "lat": 37.0, "lon": -120.0, "year_start": 2012, "year_end": 2016, "severity": "Extreme", "deaths": "Minimal (economic)", "area_affected": "California, USA", "cause": "Climate change + high pressure ridge"},
    {"name": "Syrian Drought (pre-civil war)", "lat": 35.0, "lon": 38.0, "year_start": 2006, "year_end": 2010, "severity": "Severe", "deaths": "Indirect (migration/conflict)", "area_affected": "NE Syria Fertile Crescent", "cause": "Climate change + groundwater depletion"},
    {"name": "Brazilian Northeast Drought", "lat": -8.0, "lon": -38.0, "year_start": 2012, "year_end": 2017, "severity": "Extreme", "deaths": "Minimal (migration)", "area_affected": "Nordeste Brazil", "cause": "ENSO variability + deforestation"},
    {"name": "Cape Town Day Zero", "lat": -33.9, "lon": 18.4, "year_start": 2015, "year_end": 2018, "severity": "Extreme", "deaths": "Minimal (conservation)", "area_affected": "Western Cape, South Africa", "cause": "Climate change + population growth"},
    {"name": "Soviet Virgin Lands Drought", "lat": 51.0, "lon": 67.0, "year_start": 1963, "year_end": 1965, "severity": "Severe", "deaths": "Unknown (crop failure)", "area_affected": "Kazakhstan, Central Asia", "cause": "Overfarming + natural variability"},
    {"name": "Akkadian Empire Collapse Drought", "lat": 35.5, "lon": 43.3, "year_start": -2200, "year_end": -2100, "severity": "Catastrophic", "deaths": "Civilization collapse", "area_affected": "Mesopotamia", "cause": "Abrupt climate shift (4.2 kya event)"},
    {"name": "Maya Collapse Droughts", "lat": 17.2, "lon": -89.6, "year_start": 800, "year_end": 1000, "severity": "Extreme", "deaths": "Civilization collapse", "area_affected": "Central America", "cause": "ITCZ shift + deforestation"},
    {"name": "East African Drought 2022", "lat": 2.0, "lon": 40.0, "year_start": 2020, "year_end": 2023, "severity": "Catastrophic", "deaths": "43,000+ (Somalia alone)", "area_affected": "Horn of Africa", "cause": "Triple La Nina + climate change"},
]

# =====================================================================
# 8. ANCIENT CLIMATE PROXY SITES (25+)
# =====================================================================
CLIMATE_PROXIES = [
    {"name": "Vostok Ice Core", "lat": -78.46, "lon": 106.84, "type": "Ice Core", "record_years": 420000, "country": "Antarctica", "key_finding": "CO2-temperature correlation over 4 glacial cycles"},
    {"name": "EPICA Dome C", "lat": -75.1, "lon": 123.35, "type": "Ice Core", "record_years": 800000, "country": "Antarctica", "key_finding": "Longest continuous ice core, 8 glacial cycles"},
    {"name": "GISP2 / GRIP (Summit)", "lat": 72.58, "lon": -38.46, "type": "Ice Core", "record_years": 110000, "country": "Greenland", "key_finding": "Detailed Holocene + last glacial, Dansgaard-Oeschger events"},
    {"name": "NGRIP", "lat": 75.1, "lon": -42.32, "type": "Ice Core", "record_years": 123000, "country": "Greenland", "key_finding": "Eemian interglacial record, rapid climate shifts"},
    {"name": "Quelccaya Ice Cap", "lat": -13.93, "lon": -70.83, "type": "Ice Core", "record_years": 1800, "country": "Peru", "key_finding": "Tropical ice core, Little Ice Age and El Nino records"},
    {"name": "Bristlecone Pine (White Mountains)", "lat": 37.5, "lon": -118.2, "type": "Tree Ring", "record_years": 9000, "country": "USA", "key_finding": "Oldest living trees, calibration of radiocarbon dating"},
    {"name": "Scandinavian Pine Chronology", "lat": 68.0, "lon": 20.0, "type": "Tree Ring", "record_years": 7400, "country": "Sweden/Finland", "key_finding": "European temperature reconstruction, volcanic cooling events"},
    {"name": "Kauri Tree Chronology", "lat": -36.0, "lon": 174.0, "type": "Tree Ring", "record_years": 4000, "country": "New Zealand", "key_finding": "Southern Hemisphere climate, Laschamp magnetic excursion"},
    {"name": "Siberian Larch Chronology", "lat": 70.0, "lon": 72.0, "type": "Tree Ring", "record_years": 2000, "country": "Russia", "key_finding": "Arctic warming amplification, volcanic eruption signatures"},
    {"name": "Soreq Cave", "lat": 31.76, "lon": 35.02, "type": "Speleothem", "record_years": 250000, "country": "Israel", "key_finding": "Eastern Mediterranean rainfall, sapropel events"},
    {"name": "Dongge Cave", "lat": 25.28, "lon": 108.08, "type": "Speleothem", "record_years": 160000, "country": "China", "key_finding": "Asian monsoon variability, millennial-scale oscillations"},
    {"name": "Hulu Cave", "lat": 32.5, "lon": 119.17, "type": "Speleothem", "record_years": 75000, "country": "China", "key_finding": "East Asian monsoon, Dansgaard-Oeschger event correlation"},
    {"name": "Carlsbad Caverns", "lat": 32.18, "lon": -104.44, "type": "Speleothem", "record_years": 500000, "country": "USA", "key_finding": "Permian Basin paleoclimate, speleothem U-Th dating pioneer"},
    {"name": "Great Barrier Reef Corals", "lat": -18.3, "lon": 147.7, "type": "Coral", "record_years": 400, "country": "Australia", "key_finding": "Sea surface temperature, El Nino frequency changes"},
    {"name": "Red Sea Corals", "lat": 27.0, "lon": 34.0, "type": "Coral", "record_years": 300, "country": "Egypt/Saudi Arabia", "key_finding": "Indian Ocean Dipole, Red Sea salinity-temperature link"},
    {"name": "Bermuda Corals", "lat": 32.3, "lon": -64.8, "type": "Coral", "record_years": 500, "country": "Bermuda (UK)", "key_finding": "North Atlantic Oscillation, Gulf Stream variability"},
    {"name": "Lake Malawi Sediments", "lat": -12.0, "lon": 34.5, "type": "Lake Sediment", "record_years": 1500000, "country": "Malawi", "key_finding": "African megadroughts, human evolution climate context"},
    {"name": "Lake Baikal Sediments", "lat": 53.0, "lon": 108.0, "type": "Lake Sediment", "record_years": 12000000, "country": "Russia", "key_finding": "Central Asian climate, Miocene to present paleoclimate"},
    {"name": "Lake Van Sediments", "lat": 38.63, "lon": 43.27, "type": "Lake Sediment", "record_years": 600000, "country": "Turkey", "key_finding": "Near East paleoclimate, volcanic activity record"},
    {"name": "Cariaco Basin", "lat": 10.5, "lon": -65.17, "type": "Marine Sediment", "record_years": 14500, "country": "Venezuela", "key_finding": "ITCZ shifts, Younger Dryas tropical response"},
    {"name": "ODP Site 677 (E. Pacific)", "lat": 1.2, "lon": -83.7, "type": "Marine Sediment", "record_years": 5000000, "country": "International Waters", "key_finding": "Pliocene-Pleistocene climate transition, benthic d18O stack"},
    {"name": "Kilimanjaro Ice Core", "lat": -3.07, "lon": 37.35, "type": "Ice Core", "record_years": 11700, "country": "Tanzania", "key_finding": "Tropical Holocene climate, 4.2 kya drought event"},
    {"name": "WAIS Divide Ice Core", "lat": -79.47, "lon": -112.09, "type": "Ice Core", "record_years": 68000, "country": "Antarctica", "key_finding": "West Antarctic climate, inter-hemispheric climate phasing"},
    {"name": "Huascaran Ice Core", "lat": -9.11, "lon": -77.61, "type": "Ice Core", "record_years": 19000, "country": "Peru", "key_finding": "Tropical LGM cooling, deglaciation timing"},
    {"name": "Devils Hole (Nevada)", "lat": 36.42, "lon": -116.29, "type": "Speleothem", "record_years": 500000, "country": "USA", "key_finding": "Challenged Milankovitch theory timing, d18O record"},
    {"name": "Mawmluh Cave", "lat": 25.26, "lon": 91.88, "type": "Speleothem", "record_years": 50000, "country": "India", "key_finding": "Indian monsoon variability, 4.2 kya event timing"},
]

# =====================================================================
# 9. EXTREME WEATHER RECORDS
# =====================================================================
EXTREME_WEATHER = [
    {"name": "Death Valley (Hottest)", "lat": 36.46, "lon": -116.87, "record": "56.7 C (134 F)", "category": "Highest Temperature", "date": "1913-07-10", "notes": "Furnace Creek, California USA - hottest reliably recorded"},
    {"name": "Kebili, Tunisia", "lat": 33.71, "lon": 8.97, "record": "55.0 C (131 F)", "category": "Highest Temperature", "date": "1931-07-07", "notes": "Saharan oasis town, Africa's hottest recorded"},
    {"name": "Ahvaz, Iran", "lat": 31.32, "lon": 48.67, "record": "54.0 C (129.2 F)", "category": "Highest Temperature", "date": "2017-06-29", "notes": "Verified by WMO as legitimate reading"},
    {"name": "Mitribah, Kuwait", "lat": 29.98, "lon": 47.13, "record": "53.9 C (129 F)", "category": "Highest Temperature", "date": "2016-07-21", "notes": "Third-highest reliably recorded temperature"},
    {"name": "Vostok Station (Coldest)", "lat": -78.46, "lon": 106.84, "record": "-89.2 C (-128.6 F)", "category": "Lowest Temperature", "date": "1983-07-21", "notes": "Coldest measured air temperature on Earth"},
    {"name": "Dome Fuji (Near-record cold)", "lat": -77.31, "lon": 39.7, "record": "-87.6 C satellite", "category": "Lowest Temperature", "date": "2018 (satellite)", "notes": "Satellite-derived, colder surface temp may exist"},
    {"name": "Oymyakon (Coldest Inhabited)", "lat": 63.46, "lon": 142.79, "record": "-67.7 C (-89.9 F)", "category": "Lowest Temperature", "date": "1933-02-06", "notes": "Coldest permanently inhabited place, ~500 people"},
    {"name": "Verkhoyansk", "lat": 67.55, "lon": 133.39, "record": "-67.8 C (-90.0 F)", "category": "Lowest Temperature", "date": "1892-02-05", "notes": "Also reached 38 C in summer 2020 (100.4 F range)"},
    {"name": "Cherrapunji, India", "lat": 25.26, "lon": 91.73, "record": "26,471 mm/yr", "category": "Wettest Place (annual)", "date": "1860-1861", "notes": "Meghalaya, India, monsoon funnel effect"},
    {"name": "Mawsynram, India", "lat": 25.30, "lon": 91.58, "record": "11,871 mm/yr avg", "category": "Wettest Place (average)", "date": "Ongoing", "notes": "Current wettest average, 15 km from Cherrapunji"},
    {"name": "Atacama Desert (Driest)", "lat": -24.5, "lon": -69.25, "record": "0 mm (some stations)", "category": "Driest Place", "date": "Ongoing", "notes": "Parts have had no measurable rain in recorded history"},
    {"name": "McMurdo Dry Valleys", "lat": -77.5, "lon": 162.0, "record": "~0 mm (ice-free)", "category": "Driest Place", "date": "Ongoing", "notes": "Ice-free Antarctic valleys, driest cold desert"},
    {"name": "Arica, Chile", "lat": -18.48, "lon": -70.31, "record": "0.76 mm/yr avg", "category": "Driest Place", "date": "59-yr average", "notes": "Driest city, 14 consecutive years with zero rainfall"},
    {"name": "Mount Washington (Windiest)", "lat": 44.27, "lon": -71.30, "record": "372 km/h (231 mph)", "category": "Highest Wind Speed (surface)", "date": "1934-04-12", "notes": "Held record for 62 years until Barrow Island"},
    {"name": "Barrow Island, Australia", "lat": -20.78, "lon": 115.40, "record": "408 km/h (253 mph)", "category": "Highest Wind Speed (surface)", "date": "1996-04-10", "notes": "Tropical Cyclone Olivia, current WMO surface wind record"},
    {"name": "Reunion Island (Wettest Day)", "lat": -21.12, "lon": 55.53, "record": "1,825 mm in 24 hr", "category": "Heaviest Rainfall (24h)", "date": "1966-01-08", "notes": "Tropical cyclone, Indian Ocean island"},
    {"name": "Oklahoma City (Hail)", "lat": 35.47, "lon": -97.52, "record": "Softball-sized hail", "category": "Largest Hailstone Area", "date": "Various", "notes": "Tornado Alley, frequent severe hailstorms"},
    {"name": "Vivian, South Dakota", "lat": 43.93, "lon": -100.30, "record": "20.3 cm (8 in) diameter", "category": "Largest Hailstone", "date": "2010-07-23", "notes": "Current world record for hailstone diameter"},
    {"name": "Dallol, Ethiopia (Hottest avg)", "lat": 14.24, "lon": 40.3, "record": "34.4 C annual avg", "category": "Hottest Average Temperature", "date": "1960-1966", "notes": "Danakil Depression, volcanic heat + tropical latitude"},
    {"name": "Plateau Station, Antarctica", "lat": -79.25, "lon": 40.5, "record": "-56.7 C annual avg", "category": "Coldest Average Temperature", "date": "1966-1969", "notes": "Former US station, coldest annual mean recorded"},
    {"name": "Tutunendo, Colombia", "lat": 5.75, "lon": -76.53, "record": "11,770 mm/yr avg", "category": "Wettest Place (Americas)", "date": "Ongoing", "notes": "Choco rainforest, Pacific moisture convergence"},
    {"name": "Lut Desert, Iran (Hottest surface)", "lat": 33.5, "lon": 59.0, "record": "70.7 C surface", "category": "Hottest Land Surface", "date": "2005 (satellite)", "notes": "Satellite-measured ground temperature, not air"},
]

# =====================================================================
# 10. CLIMATE TIPPING POINTS
# =====================================================================
TIPPING_POINTS = [
    {"name": "Amazon Rainforest Dieback", "lat": -3.4, "lon": -60.0, "threshold": "3-4 C global warming", "status": "Approaching", "impact": "CO2 release, biodiversity loss, rainfall collapse in S. America", "current_trend": "20% deforested, dry season lengthening", "timeline": "Could trigger by 2050 under high emissions"},
    {"name": "AMOC Slowdown/Collapse", "lat": 55.0, "lon": -30.0, "threshold": "1.5-4 C global warming", "status": "Weakening observed", "impact": "European cooling, shifted monsoons, sea level rise on US East Coast", "current_trend": "Weakest in 1,600 years per proxy data", "timeline": "Possible collapse 2025-2095 range"},
    {"name": "Greenland Ice Sheet Collapse", "lat": 72.0, "lon": -40.0, "threshold": "1.5-3 C global warming", "status": "Accelerating melt", "impact": "7.4 m sea level rise (full melt over centuries)", "current_trend": "Losing ~280 Gt/yr, accelerating", "timeline": "Irreversible commitment possible by 2100"},
    {"name": "West Antarctic Ice Sheet", "lat": -80.0, "lon": -100.0, "threshold": "1.5-3 C global warming", "status": "Unstable", "impact": "3.3 m sea level rise (full collapse over centuries)", "current_trend": "Thwaites grounding line retreating", "timeline": "Marine ice cliff instability may be underway"},
    {"name": "Arctic Sea Ice Loss", "lat": 85.0, "lon": 0.0, "threshold": "1.5-2 C global warming", "status": "Rapidly declining", "impact": "Albedo feedback, Arctic shipping, ecosystem collapse", "current_trend": "13% decline per decade, ice-free summers projected", "timeline": "First ice-free summer possibly before 2050"},
    {"name": "Permafrost Thaw", "lat": 65.0, "lon": 100.0, "threshold": "1.5-2 C global warming", "status": "Already thawing", "impact": "1,400 Gt carbon release potential, methane emission", "current_trend": "Active layer deepening across Arctic", "timeline": "Continuous release this century, accelerating"},
    {"name": "Coral Reef Die-off", "lat": -18.0, "lon": 147.7, "threshold": "1.5 C global warming", "status": "Mass bleaching underway", "impact": "Fisheries collapse, coastal protection loss, biodiversity", "current_trend": "4th global bleaching event 2024, 70-90% at risk at 1.5 C", "timeline": "Functional loss at 2 C warming"},
    {"name": "Boreal Forest Shift", "lat": 62.0, "lon": 30.0, "threshold": "3-5 C global warming", "status": "Early signs", "impact": "Carbon release, albedo change, biome conversion to grassland", "current_trend": "Increased fires, pest outbreaks, drought stress", "timeline": "Gradual shift over decades to centuries"},
    {"name": "Sahel/West African Monsoon Shift", "lat": 14.0, "lon": 0.0, "threshold": "2-3 C global warming", "status": "Uncertain", "impact": "Could green the Sahara OR collapse monsoon, affecting 100+ M people", "current_trend": "Monsoon strengthening slightly but highly variable", "timeline": "Possible abrupt shift this century"},
    {"name": "East Antarctic Ice Sheet", "lat": -75.0, "lon": 75.0, "threshold": ">5 C global warming", "status": "Currently stable", "impact": "52 m sea level rise if fully melted (over millennia)", "current_trend": "Some marginal thinning detected", "timeline": "Multi-century to millennial timescale"},
    {"name": "Indian Summer Monsoon Disruption", "lat": 22.0, "lon": 78.0, "threshold": "Unknown (aerosol interaction)", "status": "Uncertain", "impact": "1.5 B people depend on monsoon rains for agriculture", "current_trend": "Erratic behavior, extreme events increasing", "timeline": "Possible sudden shift under combined forcing"},
    {"name": "Alpine Glacier Collapse", "lat": 46.5, "lon": 8.0, "threshold": "2 C global warming", "status": "Rapidly losing mass", "impact": "Water supply for 1.5 B in Asia, 100+ M in Europe", "current_trend": "Lost 2% of volume in 2022 alone (record)", "timeline": "Half of Alpine glaciers gone by 2050"},
    {"name": "Methane Hydrate Destabilization", "lat": 70.0, "lon": -160.0, "threshold": "Unknown (deep ocean warming)", "status": "Monitoring", "impact": "Massive methane release, runaway warming potential", "current_trend": "Some seabed methane seeps detected in Arctic", "timeline": "Low probability this century, high impact"},
    {"name": "El Nino Permanent State", "lat": -5.0, "lon": -170.0, "threshold": "Unknown", "status": "Uncertain", "impact": "Permanent drought in Australia/SE Asia, flooding in Americas", "current_trend": "ENSO variability may be changing", "timeline": "Theoretical possibility under very high warming"},
]

# =====================================================================
# CHART HELPERS
# =====================================================================
def _style_ax(ax):
    """Apply TerraScout dark theme to a matplotlib axis."""
    ax.set_facecolor(_SURFACE)
    ax.grid(True, color=_GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", colors=_TEXT_SEC, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(_GRID)


def _new_fig(rows=1, cols=1, height=4.5, width=10):
    """Create a new dark-themed figure."""
    fig, axes = plt.subplots(rows, cols, figsize=(width, height))
    fig.patch.set_facecolor(_BG)
    if rows * cols == 1:
        _style_ax(axes)
    else:
        for ax in (axes.flat if hasattr(axes, "flat") else [axes]):
            _style_ax(ax)
    return fig, axes


def _fig_to_buf(fig):
    """Render matplotlib figure to BytesIO buffer."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# =====================================================================
# FOLIUM MAP HELPERS
# =====================================================================
def _base_map(lat=20.0, lon=0.0, zoom=2):
    """Create a dark CartoDB base map."""
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )


def _add_circle(m, lat, lon, color, radius, popup_html, tooltip_text):
    """Add a styled circle marker to the map."""
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=tooltip_text,
    ).add_to(m)


def _show_map(m, height=500):
    """Render Folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _csv_download(df, filename, label="Download CSV"):
    """Create a CSV download button."""
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    st.download_button(label, buf, filename, "text/csv")


# =====================================================================
# MODE RENDERERS
# =====================================================================

def _render_ice_ages():
    """Render Ice Ages & Glaciation mode."""
    df = pd.DataFrame(ICE_AGES)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glacial Events", len(df))
    c2.metric("Snowball Earth Events", len(df[df["severity"] == "Snowball Earth"]))
    c3.metric("Time Span", "2.4 Gya - present")
    c4.metric("LGM Sea Level Drop", "-120 m")

    # Map
    m = _base_map(40.0, -20.0, zoom=2)
    for _, r in df.iterrows():
        sev_color = {
            "Snowball Earth": "#06b6d4",
            "Global": "#38bdf8",
            "Continental": "#818cf8",
            "Alpine": "#a855f7",
            "Alpine/Continental": "#8b5cf6",
            "Regional": "#f59e0b",
        }.get(r["severity"], _CLR_ICE)
        radius = 8 if r["severity"] in ("Snowball Earth", "Global") else 6
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Start: {r['start_mya']} Mya<br>"
            f"End: {r['end_mya']} Mya<br>"
            f"Severity: {escape(str(r['severity']))}<br>"
            f"{escape(str(r['notes']))}"
        )
        _add_circle(m, r["lat"], r["lon"], sev_color, radius, popup, escape(str(r["name"])))

    # Add LGM extent polyline (North America)
    folium.PolyLine(
        locations=LGM_EXTENT_COORDS[:8],
        color=_CLR_ICE, weight=3, opacity=0.7,
        tooltip="Approx. Laurentide Ice Sheet southern boundary (LGM)",
    ).add_to(m)
    # Eurasian extent
    folium.PolyLine(
        locations=LGM_EXTENT_COORDS[8:],
        color=_CLR_ICE, weight=3, opacity=0.7,
        tooltip="Approx. Fennoscandian Ice Sheet southern boundary (LGM)",
    ).add_to(m)
    _show_map(m)

    # Chart: timeline
    fig, ax = _new_fig(height=5, width=11)
    names = [r["name"] for r in ICE_AGES]
    starts = [r["start_mya"] for r in ICE_AGES]
    durations = [r["start_mya"] - r["end_mya"] for r in ICE_AGES]
    colors_list = [
        "#06b6d4" if ICE_AGES[i]["severity"] in ("Snowball Earth", "Global") else "#818cf8"
        for i in range(len(ICE_AGES))
    ]
    ax.barh(names, durations, left=[e for e in [r["end_mya"] for r in ICE_AGES]],
            color=colors_list, edgecolor=_GRID, linewidth=0.5)
    ax.set_xlabel("Million Years Ago", color=_TEXT, fontsize=9)
    ax.set_title("Ice Ages Timeline (duration)", color=_TEXT, fontsize=11, pad=10)
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_buf(fig), width=900)

    # Dataframe
    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "ice_ages_glaciation.csv", "Download Ice Ages CSV")


def _render_medieval_warm():
    """Render Medieval Warm Period mode."""
    df = pd.DataFrame(MEDIEVAL_WARM)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Events Documented", len(df))
    c2.metric("Time Period", "900-1300 CE")
    c3.metric("Temp Anomaly", "+0.3 to +1.0 C")
    c4.metric("Regions Affected", df["name"].apply(lambda x: x.split(",")[-1].strip() if "," in x else "Global").nunique())

    m = _base_map(30.0, 0.0, zoom=2)
    for _, r in df.iterrows():
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Year: {r['year']} CE<br>"
            f"Event: {escape(str(r['event']))}<br>"
            f"Evidence: {escape(str(r['evidence']))}"
        )
        _add_circle(m, r["lat"], r["lon"], _CLR_WARM, 7, popup, escape(str(r["name"])))
    _show_map(m)

    # Chart: events by year
    fig, ax = _new_fig(height=4.5, width=10)
    years_sorted = df.sort_values("year")
    ax.scatter(years_sorted["year"], range(len(years_sorted)), color=_CLR_WARM, s=60, zorder=5)
    for i, (_, r) in enumerate(years_sorted.iterrows()):
        short = r["name"][:30] + ("..." if len(r["name"]) > 30 else "")
        ax.annotate(short, (r["year"], i), fontsize=6.5, color=_TEXT_SEC,
                    xytext=(8, 0), textcoords="offset points", va="center")
    ax.set_xlabel("Year CE", color=_TEXT, fontsize=9)
    ax.set_title("Medieval Warm Period Events Timeline", color=_TEXT, fontsize=11, pad=10)
    ax.set_yticks([])
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "medieval_warm_period.csv", "Download Medieval Warm Period CSV")


def _render_little_ice_age():
    """Render Little Ice Age mode."""
    df = pd.DataFrame(LITTLE_ICE_AGE)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Events Documented", len(df))
    c2.metric("Time Period", "1300-1850 CE")
    c3.metric("Temp Anomaly", "-0.5 to -1.5 C")
    c4.metric("Regions", df["region"].nunique())

    m = _base_map(45.0, 10.0, zoom=3)
    for _, r in df.iterrows():
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Year: {r['year']} CE<br>"
            f"Event: {escape(str(r['event']))}<br>"
            f"Region: {escape(str(r['region']))}"
        )
        _add_circle(m, r["lat"], r["lon"], _CLR_COLD, 7, popup, escape(str(r["name"])))
    _show_map(m)

    # Chart: events by century
    fig, ax = _new_fig(height=4.5, width=10)
    df["century"] = (df["year"] // 100) * 100
    century_counts = df.groupby("century").size()
    ax.bar(century_counts.index.astype(str), century_counts.values,
           color=_CLR_COLD, edgecolor=_GRID, linewidth=0.5)
    ax.set_xlabel("Century", color=_TEXT, fontsize=9)
    ax.set_ylabel("Number of Events", color=_TEXT, fontsize=9)
    ax.set_title("Little Ice Age Events by Century", color=_TEXT, fontsize=11, pad=10)
    st.image(_fig_to_buf(fig), width=900)

    display_df = df.drop(columns=["century"], errors="ignore")
    st.dataframe(display_df, width="stretch", hide_index=True)
    _csv_download(display_df, "little_ice_age.csv", "Download Little Ice Age CSV")


def _render_sea_level():
    """Render Sea Level History mode."""
    df = pd.DataFrame(SEA_LEVEL_DATA)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities Tracked", len(df))
    critical = len(df[df["risk"] == "Critical"])
    c2.metric("Critical Risk", critical)
    c3.metric("Avg Rise Rate", f"{df['current_rate_mm_yr'].mean():.1f} mm/yr")
    c4.metric("Max Projected (2100)", f"{df['projected_2100_m'].max():.1f} m")

    m = _base_map(20.0, 0.0, zoom=2)
    risk_colors = {"Critical": "#ef4444", "High": "#f97316", "Moderate": "#f59e0b"}
    for _, r in df.iterrows():
        color = risk_colors.get(r["risk"], _CLR_SEA)
        radius = max(5, int(r["projected_2100_m"] * 10))
        popup = (
            f"<b>{escape(str(r['city']))}</b><br>"
            f"Elevation: {r['elevation_m']} m<br>"
            f"Current rise: {r['current_rate_mm_yr']} mm/yr<br>"
            f"Projected 2100: +{r['projected_2100_m']} m<br>"
            f"Risk: {escape(str(r['risk']))}<br>"
            f"{escape(str(r['notes']))}"
        )
        _add_circle(m, r["lat"], r["lon"], color, radius, popup, escape(str(r["city"])))
    _show_map(m)

    # Chart: projected rise by city
    fig, ax = _new_fig(height=5, width=11)
    sorted_df = df.sort_values("projected_2100_m", ascending=True)
    colors_list = [risk_colors.get(r, _CLR_SEA) for r in sorted_df["risk"]]
    ax.barh(sorted_df["city"], sorted_df["projected_2100_m"],
            color=colors_list, edgecolor=_GRID, linewidth=0.5)
    ax.set_xlabel("Projected Sea Level Rise by 2100 (m)", color=_TEXT, fontsize=9)
    ax.set_title("Sea Level Rise Projections by City", color=_TEXT, fontsize=11, pad=10)
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "sea_level_history.csv", "Download Sea Level Data CSV")


def _render_desertification():
    """Render Desertification Advance mode."""
    df = pd.DataFrame(DESERTIFICATION)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Regions Tracked", len(df))
    c2.metric("Fastest Advance", f"{df['rate_km_yr'].max():.1f} km/yr")
    c3.metric("Avg Advance Rate", f"{df['rate_km_yr'].mean():.1f} km/yr")
    c4.metric("Primary Cause", "Overgrazing & Climate")

    m = _base_map(20.0, 40.0, zoom=2)
    for _, r in df.iterrows():
        radius = max(5, int(r["rate_km_yr"] * 5))
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Area: {escape(str(r['area']))}<br>"
            f"Rate: {r['rate_km_yr']} km/yr<br>"
            f"Period: {escape(str(r['period']))}<br>"
            f"Cause: {escape(str(r['cause']))}<br>"
            f"{escape(str(r['notes']))}"
        )
        _add_circle(m, r["lat"], r["lon"], _CLR_DESERT, radius, popup, escape(str(r["name"])))
    _show_map(m)

    # Chart: rates
    fig, ax = _new_fig(height=5, width=10)
    sorted_df = df.sort_values("rate_km_yr", ascending=True)
    ax.barh(sorted_df["name"], sorted_df["rate_km_yr"],
            color=_CLR_DESERT, edgecolor=_GRID, linewidth=0.5)
    ax.set_xlabel("Advance Rate (km/yr)", color=_TEXT, fontsize=9)
    ax.set_title("Desertification Advance Rates", color=_TEXT, fontsize=11, pad=10)
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "desertification_advance.csv", "Download Desertification CSV")


def _render_glacier_retreat():
    """Render Glacier Retreat mode."""
    df = pd.DataFrame(GLACIER_RETREAT)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Glaciers Tracked", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Max Retreat", f"{df['retreat_km'].max():.0f} km")
    near_extinct = len(df[df["status"].str.contains("extinction", case=False)])
    c4.metric("Near Extinction", near_extinct)

    m = _base_map(30.0, 0.0, zoom=2)
    for _, r in df.iterrows():
        status_color = {
            "Critical": "#ef4444",
            "Catastrophic retreat": "#dc2626",
            "Rapid retreat": "#f97316",
            "Accelerating": "#f59e0b",
            "Retreating": _CLR_GLACIER,
            "Near extinction": "#ec4899",
            "Thinning rapidly": "#f97316",
            "Stable (anomaly)": "#10b981",
            "Slow retreat": "#38bdf8",
            "Major calving events": "#ef4444",
            "Recently started retreating": "#f59e0b",
            "Retreated out of sight": "#dc2626",
        }
        color = _CLR_GLACIER
        for key, val in status_color.items():
            if key.lower() in r["status"].lower():
                color = val
                break
        radius = max(4, min(12, int(r["retreat_km"] / 4)))
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Country: {escape(str(r['country']))}<br>"
            f"Retreat: {r['retreat_km']} km<br>"
            f"Period: {escape(str(r['period']))}<br>"
            f"Status: {escape(str(r['status']))}<br>"
            f"Type: {escape(str(r['type']))}"
        )
        _add_circle(m, r["lat"], r["lon"], color, radius, popup, escape(str(r["name"])))
    _show_map(m)

    # Chart: top 15 by retreat
    fig, ax = _new_fig(height=5, width=10)
    top = df.nlargest(15, "retreat_km").sort_values("retreat_km", ascending=True)
    ax.barh(top["name"], top["retreat_km"],
            color=_CLR_GLACIER, edgecolor=_GRID, linewidth=0.5)
    ax.set_xlabel("Retreat Distance (km)", color=_TEXT, fontsize=9)
    ax.set_title("Top 15 Glacier Retreats by Distance", color=_TEXT, fontsize=11, pad=10)
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "glacier_retreat.csv", "Download Glacier Retreat CSV")


def _render_historical_droughts():
    """Render Historical Droughts mode."""
    df = pd.DataFrame(HISTORICAL_DROUGHTS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Droughts Documented", len(df))
    catastrophic = len(df[df["severity"] == "Catastrophic"])
    c2.metric("Catastrophic Events", catastrophic)
    c3.metric("Time Span", "2200 BCE - present")
    c4.metric("Civilization Collapses", len(df[df["deaths"].str.contains("collapse", case=False)]))

    m = _base_map(20.0, 20.0, zoom=2)
    sev_colors = {"Catastrophic": "#ef4444", "Extreme": "#f97316", "Severe": "#f59e0b"}
    for _, r in df.iterrows():
        color = sev_colors.get(r["severity"], _CLR_DROUGHT)
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Period: {r['year_start']} to {r['year_end']}<br>"
            f"Severity: {escape(str(r['severity']))}<br>"
            f"Deaths: {escape(str(r['deaths']))}<br>"
            f"Area: {escape(str(r['area_affected']))}<br>"
            f"Cause: {escape(str(r['cause']))}"
        )
        _add_circle(m, r["lat"], r["lon"], color, 8, popup, escape(str(r["name"])))
    _show_map(m)

    # Chart: severity counts + duration
    fig, (ax1, ax2) = _new_fig(rows=1, cols=2, height=4.5, width=12)
    sev_counts = df["severity"].value_counts()
    bars = ax1.bar(sev_counts.index, sev_counts.values,
                   color=[sev_colors.get(s, _CLR_DROUGHT) for s in sev_counts.index],
                   edgecolor=_GRID, linewidth=0.5)
    ax1.set_ylabel("Count", color=_TEXT, fontsize=9)
    ax1.set_title("Droughts by Severity", color=_TEXT, fontsize=11, pad=10)

    df["duration"] = df["year_end"] - df["year_start"]
    top_dur = df.nlargest(10, "duration").sort_values("duration", ascending=True)
    ax2.barh(top_dur["name"], top_dur["duration"],
             color=_CLR_DROUGHT, edgecolor=_GRID, linewidth=0.5)
    ax2.set_xlabel("Duration (years)", color=_TEXT, fontsize=9)
    ax2.set_title("Longest Droughts", color=_TEXT, fontsize=11, pad=10)
    ax2.tick_params(axis="y", labelsize=7)
    fig.tight_layout(pad=2.0)
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "historical_droughts.csv", "Download Historical Droughts CSV")


def _render_climate_proxies():
    """Render Ancient Climate Proxy Sites mode."""
    df = pd.DataFrame(CLIMATE_PROXIES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Proxy Sites", len(df))
    c2.metric("Proxy Types", df["type"].nunique())
    c3.metric("Max Record", f"{df['record_years'].max():,.0f} yr")
    c4.metric("Countries", df["country"].nunique())

    type_colors = {
        "Ice Core": "#38bdf8",
        "Tree Ring": "#10b981",
        "Speleothem": "#a855f7",
        "Coral": "#ec4899",
        "Lake Sediment": "#f59e0b",
        "Marine Sediment": "#06b6d4",
    }

    m = _base_map(20.0, 0.0, zoom=2)
    for _, r in df.iterrows():
        color = type_colors.get(r["type"], _CLR_PROXY)
        radius = max(5, min(10, int(r["record_years"] / 100000) + 5))
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Type: {escape(str(r['type']))}<br>"
            f"Record: {r['record_years']:,} years<br>"
            f"Country: {escape(str(r['country']))}<br>"
            f"Finding: {escape(str(r['key_finding']))}"
        )
        _add_circle(m, r["lat"], r["lon"], color, radius, popup, escape(str(r["name"])))

    # Add legend as HTML overlay
    legend_html = '<div style="position:fixed;bottom:50px;left:50px;z-index:1000;background:rgba(17,24,39,0.9);padding:10px;border-radius:6px;border:1px solid #2a3550;">'
    for ptype, pcolor in type_colors.items():
        legend_html += f'<div style="margin:3px 0;"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{pcolor};margin-right:6px;"></span><span style="color:#e8ecf4;font-size:11px;">{ptype}</span></div>'
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    _show_map(m)

    # Chart: sites by type + record length
    fig, (ax1, ax2) = _new_fig(rows=1, cols=2, height=4.5, width=12)
    type_counts = df["type"].value_counts()
    ax1.bar(type_counts.index, type_counts.values,
            color=[type_colors.get(t, _CLR_PROXY) for t in type_counts.index],
            edgecolor=_GRID, linewidth=0.5)
    ax1.set_ylabel("Count", color=_TEXT, fontsize=9)
    ax1.set_title("Proxy Sites by Type", color=_TEXT, fontsize=11, pad=10)
    ax1.tick_params(axis="x", rotation=25, labelsize=7)

    top_rec = df.nlargest(12, "record_years").sort_values("record_years", ascending=True)
    ax2.barh(top_rec["name"], top_rec["record_years"],
             color=_CLR_PROXY, edgecolor=_GRID, linewidth=0.5)
    ax2.set_xlabel("Record Length (years)", color=_TEXT, fontsize=9)
    ax2.set_title("Longest Climate Records", color=_TEXT, fontsize=11, pad=10)
    ax2.tick_params(axis="y", labelsize=7)
    fig.tight_layout(pad=2.0)
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "climate_proxy_sites.csv", "Download Climate Proxy Sites CSV")


def _render_extreme_weather():
    """Render Extreme Weather Records mode."""
    df = pd.DataFrame(EXTREME_WEATHER)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records Tracked", len(df))
    c2.metric("Categories", df["category"].nunique())
    c3.metric("Hottest Recorded", "56.7 C")
    c4.metric("Coldest Recorded", "-89.2 C")

    cat_colors = {
        "Highest Temperature": "#ef4444",
        "Lowest Temperature": "#38bdf8",
        "Wettest Place (annual)": "#8b5cf6",
        "Wettest Place (average)": "#a855f7",
        "Wettest Place (Americas)": "#7c3aed",
        "Driest Place": "#f59e0b",
        "Highest Wind Speed (surface)": "#06b6d4",
        "Heaviest Rainfall (24h)": "#6366f1",
        "Largest Hailstone": "#10b981",
        "Largest Hailstone Area": "#34d399",
        "Hottest Average Temperature": "#dc2626",
        "Coldest Average Temperature": "#3b82f6",
        "Hottest Land Surface": "#b91c1c",
    }

    m = _base_map(20.0, 0.0, zoom=2)
    for _, r in df.iterrows():
        color = cat_colors.get(r["category"], _CLR_EXTREME)
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Record: {escape(str(r['record']))}<br>"
            f"Category: {escape(str(r['category']))}<br>"
            f"Date: {escape(str(r['date']))}<br>"
            f"{escape(str(r['notes']))}"
        )
        _add_circle(m, r["lat"], r["lon"], color, 7, popup, escape(str(r["name"])))
    _show_map(m)

    # Chart: records by category
    fig, ax = _new_fig(height=5, width=10)
    cat_counts = df["category"].value_counts()
    colors_list = [cat_colors.get(c, _CLR_EXTREME) for c in cat_counts.index]
    ax.barh(cat_counts.index, cat_counts.values,
            color=colors_list, edgecolor=_GRID, linewidth=0.5)
    ax.set_xlabel("Number of Records", color=_TEXT, fontsize=9)
    ax.set_title("Extreme Weather Records by Category", color=_TEXT, fontsize=11, pad=10)
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "extreme_weather_records.csv", "Download Extreme Weather CSV")


def _render_tipping_points():
    """Render Climate Tipping Points mode."""
    df = pd.DataFrame(TIPPING_POINTS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tipping Elements", len(df))
    approaching = len(df[df["status"].str.contains("Approach|Accelerat|Rapidly|Already|Unstable|underway|bleaching", case=False)])
    c2.metric("Active / Approaching", approaching)
    c3.metric("Lowest Threshold", "1.5 C")
    c4.metric("Max Sea Level Risk", "52+ m (combined)")

    status_colors = {
        "Approaching": "#f97316",
        "Weakening observed": "#f59e0b",
        "Accelerating melt": "#ef4444",
        "Unstable": "#dc2626",
        "Rapidly declining": "#ef4444",
        "Already thawing": "#dc2626",
        "Mass bleaching underway": "#ef4444",
        "Early signs": "#f59e0b",
        "Uncertain": "#8b97b0",
        "Currently stable": "#10b981",
        "Monitoring": "#06b6d4",
        "Rapidly losing mass": "#ef4444",
    }

    m = _base_map(20.0, 0.0, zoom=2)
    for _, r in df.iterrows():
        color = status_colors.get(r["status"], _CLR_TIPPING)
        popup = (
            f"<b>{escape(str(r['name']))}</b><br>"
            f"Threshold: {escape(str(r['threshold']))}<br>"
            f"Status: {escape(str(r['status']))}<br>"
            f"Impact: {escape(str(r['impact']))}<br>"
            f"Trend: {escape(str(r['current_trend']))}<br>"
            f"Timeline: {escape(str(r['timeline']))}"
        )
        _add_circle(m, r["lat"], r["lon"], color, 10, popup, escape(str(r["name"])))
    _show_map(m)

    # Chart: status distribution
    fig, ax = _new_fig(height=5, width=10)
    status_counts = df["status"].value_counts()
    colors_list = [status_colors.get(s, _CLR_TIPPING) for s in status_counts.index]
    ax.barh(status_counts.index, status_counts.values,
            color=colors_list, edgecolor=_GRID, linewidth=0.5)
    ax.set_xlabel("Number of Tipping Elements", color=_TEXT, fontsize=9)
    ax.set_title("Climate Tipping Points by Current Status", color=_TEXT, fontsize=11, pad=10)
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_buf(fig), width=900)

    st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "climate_tipping_points.csv", "Download Tipping Points CSV")


# =====================================================================
# DISPATCH TABLE
# =====================================================================
_RENDERERS = {
    "Ice Ages & Glaciation": _render_ice_ages,
    "Medieval Warm Period": _render_medieval_warm,
    "Little Ice Age": _render_little_ice_age,
    "Sea Level History": _render_sea_level,
    "Desertification Advance": _render_desertification,
    "Glacier Retreat": _render_glacier_retreat,
    "Historical Droughts": _render_historical_droughts,
    "Ancient Climate Proxy Sites": _render_climate_proxies,
    "Extreme Weather Records": _render_extreme_weather,
    "Climate Tipping Points": _render_tipping_points,
}


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
def render_climate_history_maps_tab():
    """Main entry point for the Climate History & Paleoclimate tab."""
    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>\U0001f321\ufe0f Climate History & Paleoclimate</h4>"
        "<p>Ice ages, historical climate events, glaciation, sea level changes "
        "& paleoclimate data</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    selected = st.radio(
        "Select climate history topic",
        MODES,
        key="climate_history_mode",
        horizontal=True,
    )

    st.markdown("---")

    renderer = _RENDERERS.get(selected)
    if renderer:
        renderer()
    else:
        st.warning("Mode not found. Please select a valid topic.")
