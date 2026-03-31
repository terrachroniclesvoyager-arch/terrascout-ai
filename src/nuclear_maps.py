# -*- coding: utf-8 -*-
"""
Nuclear & Radiation Maps module for TerraScout AI.
Displays nuclear power plants, disasters, test sites, uranium mines,
weapons states, radiation monitoring, waste storage, decommissioned plants,
research facilities, and Hiroshima & Nagasaki data on interactive maps.
All data from free public APIs (Overpass/OpenStreetMap) and curated datasets.
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

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════
OVERPASS_API = "https://overpass-api.de/api/interpreter"

# ═══════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════
COLORS = {
    "operating":       "#10b981",   # green  — active plants
    "shutdown":        "#8b97b0",   # grey   — decommissioned
    "disaster":        "#ef4444",   # red    — disasters
    "test_atmo":       "#f59e0b",   # amber  — atmospheric tests
    "test_under":      "#f97316",   # orange — underground tests
    "test_uw":         "#06b6d4",   # cyan   — underwater tests
    "uranium":         "#a855f7",   # purple — uranium mines
    "weapons":         "#dc2626",   # dark-red — weapons states
    "monitoring":      "#3b82f6",   # blue   — radiation monitors
    "waste":           "#ec4899",   # pink   — waste storage
    "research":        "#14b8a6",   # teal   — research facilities
    "memorial":        "#f0abfc",   # light-pink — memorials
    "exclusion":       "rgba(255,0,0,0.25)", # transparent red — exclusion zones
}

REACTOR_TYPE_COLORS = {
    "PWR": "#06b6d4",
    "BWR": "#3b82f6",
    "PHWR": "#8b5cf6",
    "LWGR": "#ef4444",
    "GCR": "#f59e0b",
    "FBR": "#ec4899",
    "HTGR": "#14b8a6",
    "Other": "#8b97b0",
}

# ═══════════════════════════════════════════════════════════════
# MAP MODE DESCRIPTIONS
# ═══════════════════════════════════════════════════════════════
MAP_MODES = {
    "Nuclear Power Plants":       "Operating nuclear reactors worldwide (~440 units in 32 countries), with capacity, reactor type, and operator data via OpenStreetMap.",
    "Nuclear Disasters":          "Major nuclear accidents from INES Level 4-7: Chernobyl, Fukushima, Three Mile Island, Windscale, Kyshtym, SL-1, Lucens, and exclusion zones.",
    "Nuclear Test Sites":         "All known nuclear test locations — 2,056 tests by 8 nations (1945-2017) across Nevada, Semipalatinsk, Bikini, Mururoa, Lop Nur, and more.",
    "Uranium Mines":              "Major uranium mining regions in Kazakhstan, Canada, Australia, Niger, Namibia, Russia, Uzbekistan, and the USA.",
    "Nuclear Weapons States":     "The nine nuclear-armed states, their estimated warhead stockpiles, delivery systems, and first-test dates.",
    "Radiation Monitoring":       "Background radiation monitoring stations and environmental dose-rate data points from OpenStreetMap.",
    "Nuclear Waste Storage":      "Spent fuel repositories, reprocessing plants, deep geological disposal sites (Onkalo, Yucca Mountain), and interim storage.",
    "Decommissioned Plants":      "Permanently shut-down nuclear power reactors worldwide, cleanup status, and brownfield redevelopment.",
    "Nuclear Research":           "Particle accelerators (CERN, Fermilab), fusion experiments (ITER, JET, EAST), and research reactor facilities.",
    "Hiroshima & Nagasaki":       "Ground zero sites, blast radii (1 km, 2.5 km, 5 km), peace memorials, and the hibakusha legacy of the 1945 atomic bombings.",
}


# ═══════════════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════════════

NUCLEAR_DISASTERS = [
    {"name": "Chernobyl (RBMK-1000 #4)", "lat": 51.3891, "lon": 26.0444, "date": "1986-04-26",
     "ines": 7, "country": "Ukraine (USSR)", "deaths": "31 immediate; est. 4,000-60,000 long-term",
     "description": "Reactor explosion & fire released 400x Hiroshima fallout. 350,000 evacuated. 30-km exclusion zone still active.",
     "exclusion_km": 30},
    {"name": "Fukushima Daiichi (#1-3)", "lat": 37.4211, "lon": 141.0328, "date": "2011-03-11",
     "ines": 7, "country": "Japan", "deaths": "1 confirmed radiation; 2,202 evacuation-related",
     "description": "Tsunami knocked out cooling. Three meltdowns, hydrogen explosions. 154,000 evacuated. Ongoing water treatment.",
     "exclusion_km": 20},
    {"name": "Kyshtym / Mayak", "lat": 55.7167, "lon": 60.8000, "date": "1957-09-29",
     "ines": 6, "country": "Russia (USSR)", "deaths": "Est. 200+ (classified for decades)",
     "description": "Waste tank explosion at Mayak plutonium plant. 20,000 km2 contaminated. 10,000 evacuated. Soviet secrecy until 1976.",
     "exclusion_km": 15},
    {"name": "Windscale Pile #1", "lat": 54.4209, "lon": -3.4948, "date": "1957-10-10",
     "ines": 5, "country": "United Kingdom", "deaths": "Est. 100-240 cancer deaths",
     "description": "Graphite fire in air-cooled plutonium production reactor. Radioactive iodine-131 released across UK & Europe.",
     "exclusion_km": 0},
    {"name": "Three Mile Island (Unit 2)", "lat": 40.1531, "lon": -76.7253, "date": "1979-03-28",
     "ines": 5, "country": "United States", "deaths": "0 (no measurable health effects)",
     "description": "Partial meltdown — loss of coolant accident. Minimal release. Turned US public opinion against nuclear power.",
     "exclusion_km": 0},
    {"name": "Goiânia Incident", "lat": -16.6869, "lon": -49.2648, "date": "1987-09-13",
     "ines": 5, "country": "Brazil", "deaths": "4 immediate; 249 contaminated",
     "description": "Stolen cesium-137 radiotherapy source opened by scrapyard workers. Glowing blue powder spread across city.",
     "exclusion_km": 0},
    {"name": "SL-1 (Stationary Low-Power #1)", "lat": 43.5225, "lon": -112.8334, "date": "1961-01-03",
     "ines": 4, "country": "United States", "deaths": "3 (all operators killed instantly)",
     "description": "Steam explosion in experimental military reactor at Idaho National Lab. Only fatal reactor accident in US history.",
     "exclusion_km": 0},
    {"name": "Lucens Reactor", "lat": 46.7094, "lon": 6.8356, "date": "1969-01-21",
     "ines": 4, "country": "Switzerland", "deaths": "0",
     "description": "CO2-cooled experimental reactor in underground cavern suffered partial meltdown. Cavern sealed and decontaminated.",
     "exclusion_km": 0},
    {"name": "Saint-Laurent-des-Eaux A1", "lat": 47.7206, "lon": 1.5783, "date": "1980-03-13",
     "ines": 4, "country": "France", "deaths": "0",
     "description": "Fuel channel blockage caused partial fuel meltdown in gas-cooled reactor. No external release. Repaired and restarted.",
     "exclusion_km": 0},
    {"name": "Tokaimura Criticality", "lat": 36.4661, "lon": 140.6064, "date": "1999-09-30",
     "ines": 4, "country": "Japan", "deaths": "2 workers (acute radiation syndrome)",
     "description": "Workers poured uranyl nitrate into precipitation tank by hand, causing uncontrolled criticality for 20 hours.",
     "exclusion_km": 0},
    {"name": "Chalk River NRX", "lat": 46.0500, "lon": -77.3600, "date": "1952-12-12",
     "ines": 5, "country": "Canada", "deaths": "0",
     "description": "Fuel rod failure and hydrogen explosions in research reactor. Jimmy Carter (then Navy officer) helped with cleanup.",
     "exclusion_km": 0},
    {"name": "Jaslovské Bohunice A1", "lat": 48.4900, "lon": 17.6800, "date": "1977-02-22",
     "ines": 4, "country": "Czechoslovakia", "deaths": "0",
     "description": "Severe fuel damage during refueling of KS-150 heavy-water reactor. Facility permanently shut down.",
     "exclusion_km": 0},
]

NUCLEAR_TEST_SITES = [
    # USA
    {"name": "Nevada Test Site (NTS)", "lat": 37.05, "lon": -116.05, "country": "United States",
     "tests": 928, "period": "1951-1992", "type": "Atmospheric & Underground",
     "description": "Primary US continental test site. 100 atmospheric, 828 underground tests. Downwinders suffered fallout exposure."},
    {"name": "Trinity Site, New Mexico", "lat": 33.6773, "lon": -106.4754, "country": "United States",
     "tests": 1, "period": "1945-07-16", "type": "Atmospheric",
     "description": "First nuclear detonation ever — 'The Gadget' (20 kt plutonium implosion). J. Robert Oppenheimer: 'Now I am become Death.'"},
    {"name": "Bikini Atoll", "lat": 11.5833, "lon": 165.3833, "country": "United States",
     "tests": 23, "period": "1946-1958", "type": "Atmospheric & Underwater",
     "description": "Operation Crossroads, Castle Bravo (15 Mt — worst US test). Islanders relocated. Atoll still uninhabitable."},
    {"name": "Enewetak Atoll", "lat": 11.5000, "lon": 162.3500, "country": "United States",
     "tests": 43, "period": "1948-1958", "type": "Atmospheric",
     "description": "Ivy Mike (first H-bomb, 10.4 Mt) tested here 1952. Runit Dome concrete cap covers radioactive debris."},
    {"name": "Johnston Atoll", "lat": 16.7500, "lon": -169.5167, "country": "United States",
     "tests": 12, "period": "1958-1962", "type": "Atmospheric (high-altitude)",
     "description": "Starfish Prime (1.4 Mt, 400 km altitude) created artificial aurora and EMP that damaged Hawaiian electronics."},
    {"name": "Amchitka Island, Alaska", "lat": 51.4000, "lon": 179.1000, "country": "United States",
     "tests": 3, "period": "1965-1971", "type": "Underground",
     "description": "Cannikin (5 Mt) — largest US underground test. Protests led to founding of Greenpeace."},
    # USSR / Russia
    {"name": "Semipalatinsk (The Polygon)", "lat": 50.0700, "lon": 78.4300, "country": "Soviet Union / Kazakhstan",
     "tests": 456, "period": "1949-1989", "type": "Atmospheric & Underground",
     "description": "Primary Soviet test site. First Soviet bomb (1949), first H-bomb (1953). 1.5M people exposed. High cancer rates persist."},
    {"name": "Novaya Zemlya", "lat": 73.3700, "lon": 54.7000, "country": "Soviet Union / Russia",
     "tests": 224, "period": "1955-1990", "type": "Atmospheric & Underground",
     "description": "Tsar Bomba (50 Mt, 1961) — largest nuclear explosion ever. Shockwave circled Earth 3 times. Arctic archipelago."},
    # UK
    {"name": "Maralinga, Australia", "lat": -30.1600, "lon": 131.5800, "country": "United Kingdom",
     "tests": 7, "period": "1956-1963", "type": "Atmospheric",
     "description": "British tests on Aboriginal Maralinga Tjarutja land. Inadequate cleanup until 1990s. Ongoing health claims."},
    {"name": "Monte Bello Islands", "lat": -20.4167, "lon": 115.5667, "country": "United Kingdom",
     "tests": 3, "period": "1952-1956", "type": "Atmospheric",
     "description": "Operation Hurricane (1952) — first British nuclear test. Ship-mounted bomb in lagoon."},
    {"name": "Christmas Island (Kiritimati)", "lat": 1.8833, "lon": -157.4833, "country": "United Kingdom / United States",
     "tests": 33, "period": "1957-1962", "type": "Atmospheric",
     "description": "Operation Grapple: British thermonuclear tests. Also used by US. Servicemen exposed to fallout."},
    # France
    {"name": "Reggane, Algeria", "lat": 26.3167, "lon": 0.0500, "country": "France",
     "tests": 4, "period": "1960-1961", "type": "Atmospheric",
     "description": "Gerboise Bleue (1960) — first French nuclear test. Saharan tests affected Tuareg populations."},
    {"name": "In Ekker, Algeria", "lat": 24.0500, "lon": 5.0500, "country": "France",
     "tests": 13, "period": "1961-1966", "type": "Underground",
     "description": "Béryl test (1962) vented radioactive cloud; French ministers were exposed. France moved tests to Pacific."},
    {"name": "Mururoa Atoll", "lat": -21.8333, "lon": -138.9167, "country": "France",
     "tests": 181, "period": "1966-1996", "type": "Atmospheric & Underground",
     "description": "Primary French Pacific test site. 41 atmospheric, 137 underground. Rainbow Warrior sunk to stop protests."},
    {"name": "Fangataufa Atoll", "lat": -22.2333, "lon": -138.7500, "country": "France",
     "tests": 15, "period": "1966-1996", "type": "Atmospheric & Underground",
     "description": "French thermonuclear test site. Canopus (2.6 Mt, 1968) — first French H-bomb."},
    # China
    {"name": "Lop Nur", "lat": 41.5483, "lon": 88.3317, "country": "China",
     "tests": 45, "period": "1964-1996", "type": "Atmospheric & Underground",
     "description": "All Chinese nuclear tests. First test 1964, first H-bomb 1967. Remote Xinjiang desert. Uyghur health effects reported."},
    # India
    {"name": "Pokhran, Rajasthan", "lat": 27.0950, "lon": 71.7550, "country": "India",
     "tests": 6, "period": "1974, 1998", "type": "Underground",
     "description": "Smiling Buddha (1974) — first Indian test. Pokhran-II (1998) — 5 tests triggered Pakistan response."},
    # Pakistan
    {"name": "Ras Koh Hills, Balochistan", "lat": 28.7800, "lon": 64.9500, "country": "Pakistan",
     "tests": 6, "period": "1998", "type": "Underground",
     "description": "Chagai-I & II (1998) — Pakistan's response to Indian Pokhran-II. Six tests in two weeks."},
    # North Korea
    {"name": "Punggye-ri", "lat": 41.2931, "lon": 129.0778, "country": "North Korea",
     "tests": 6, "period": "2006-2017", "type": "Underground",
     "description": "All 6 DPRK tests. Last (2017) estimated 100-370 kt. Test tunnels reportedly collapsed. Site 'dismantled' 2018."},
]

URANIUM_MINES = [
    {"name": "McArthur River Mine", "lat": 57.7667, "lon": -105.0833, "country": "Canada",
     "production_t": 7520, "status": "Suspended (2018)", "type": "Underground",
     "description": "World's largest high-grade uranium deposit (16.5% U3O8). Cameco-operated. In care & maintenance."},
    {"name": "Cigar Lake Mine", "lat": 58.0667, "lon": -104.5333, "country": "Canada",
     "production_t": 6924, "status": "Operating", "type": "Underground (jet boring)",
     "description": "Highest-grade uranium mine in the world (17.8% U3O8). Cameco/Orano. Flooded twice during construction."},
    {"name": "Olympic Dam", "lat": -30.4500, "lon": 136.8833, "country": "Australia",
     "production_t": 3286, "status": "Operating", "type": "Underground",
     "description": "BHP-operated copper-gold-uranium mine. World's largest uranium deposit by tonnage. South Australia."},
    {"name": "Ranger Mine", "lat": -12.6833, "lon": 132.9167, "country": "Australia",
     "production_t": 0, "status": "Closed (2021)", "type": "Open pit",
     "description": "ERA-operated in Kakadu National Park. Surrounded by UNESCO World Heritage. Rehabilitation underway."},
    {"name": "Rössing Mine", "lat": -22.4833, "lon": 15.2333, "country": "Namibia",
     "production_t": 2509, "status": "Operating", "type": "Open pit",
     "description": "One of the longest-running open-pit uranium mines. CNNC-majority owned since 2019. Erongo Region."},
    {"name": "Husab Mine", "lat": -22.6167, "lon": 15.1500, "country": "Namibia",
     "production_t": 3400, "status": "Operating", "type": "Open pit",
     "description": "Swakop Uranium (CNNC). One of the world's largest uranium mines by volume. Opened 2016."},
    {"name": "Inkai ISL Mine", "lat": 44.2500, "lon": 67.5000, "country": "Kazakhstan",
     "production_t": 3960, "status": "Operating", "type": "In-situ leaching",
     "description": "Cameco/Kazatomprom JV. Kazakhstan is world's #1 uranium producer (43% of global supply)."},
    {"name": "Tortkuduk (Katco)", "lat": 44.0000, "lon": 68.0000, "country": "Kazakhstan",
     "production_t": 4000, "status": "Operating", "type": "In-situ leaching",
     "description": "Orano/Kazatomprom. Central Kazakhstan steppes. ISL extraction with sulfuric acid."},
    {"name": "Budenovskoye", "lat": 44.1000, "lon": 68.3000, "country": "Kazakhstan",
     "production_t": 2500, "status": "Operating", "type": "In-situ leaching",
     "description": "Uranium One / Kazatomprom. One of the largest ISL deposits. Chu-Sarysu basin."},
    {"name": "SOMAIR (Arlit)", "lat": 18.7333, "lon": 7.3833, "country": "Niger",
     "production_t": 1996, "status": "Operating", "type": "Open pit",
     "description": "Orano-operated. Aïr Mountains, Sahara. Niger is Africa's largest uranium producer. Tuareg labor issues."},
    {"name": "COMINAK (Akouta)", "lat": 18.5833, "lon": 7.2500, "country": "Niger",
     "production_t": 0, "status": "Closed (2021)", "type": "Underground",
     "description": "Orano-operated deep underground mine. Closed after 44 years. Decommissioning and site rehabilitation."},
    {"name": "Priargunsky Mining", "lat": 51.2500, "lon": 119.1000, "country": "Russia",
     "production_t": 1600, "status": "Operating", "type": "Underground",
     "description": "ARMZ/Rosatom. Transbaikal region near Chinese border. Russia's primary domestic uranium source."},
    {"name": "Navoi Mining (Uchkuduk)", "lat": 42.1500, "lon": 63.5500, "country": "Uzbekistan",
     "production_t": 3500, "status": "Operating", "type": "In-situ leaching",
     "description": "Navoi Mining & Metallurgy. Kyzylkum Desert. Uzbekistan is world's 5th largest producer."},
    {"name": "Jaduguda Mine", "lat": 22.6500, "lon": 86.3500, "country": "India",
     "production_t": 200, "status": "Operating", "type": "Underground",
     "description": "UCIL-operated. Jharkhand state. India's oldest uranium mine (1967). Health concerns among local tribal populations."},
    {"name": "Moab Uranium Mill Tailings", "lat": 38.5667, "lon": -109.5833, "country": "United States",
     "production_t": 0, "status": "Remediation", "type": "Former mill site",
     "description": "16M tons of radioactive mill tailings on Colorado River bank. DOE relocating to Crescent Junction disposal cell."},
]

NUCLEAR_WEAPONS_STATES = [
    {"country": "Russia", "lat": 55.7558, "lon": 37.6173, "warheads": 5580, "first_test": "1949-08-29",
     "delivery": "ICBMs (SS-18, Topol-M, Sarmat), SLBMs (Bulava), bombers (Tu-160, Tu-95)",
     "status": "Largest stockpile. New START treaty. Sarmat (Satan II) ICBM deployed.",
     "treaty": "NPT (P5), New START"},
    {"country": "United States", "lat": 38.8951, "lon": -77.0364, "warheads": 5044, "first_test": "1945-07-16",
     "delivery": "ICBMs (Minuteman III, Sentinel), SLBMs (Trident II), bombers (B-2, B-52, B-21)",
     "status": "Second largest. Nuclear triad modernization ($1.5T). B-21 Raider entering service.",
     "treaty": "NPT (P5), New START"},
    {"country": "China", "lat": 39.9042, "lon": 116.4074, "warheads": 500, "first_test": "1964-10-16",
     "delivery": "ICBMs (DF-41, DF-5B), SLBMs (JL-3), bombers (H-6K/N), HGVs (DF-ZF)",
     "status": "Rapid expansion — est. 1,000 warheads by 2030. 300+ new ICBM silos detected.",
     "treaty": "NPT (P5)"},
    {"country": "France", "lat": 48.8566, "lon": 2.3522, "warheads": 290, "first_test": "1960-02-13",
     "delivery": "SLBMs (M51), air-launched cruise missiles (ASMP-A), Rafale fighters",
     "status": "Independent deterrent. 4 Triomphant-class SSBNs. No land-based ICBMs.",
     "treaty": "NPT (P5)"},
    {"country": "United Kingdom", "lat": 51.5074, "lon": -0.1278, "warheads": 225, "first_test": "1952-10-03",
     "delivery": "SLBMs (Trident II D5 on Vanguard-class SSBNs)",
     "status": "Sole delivery: submarine-based. Plans to increase cap to 260. Dreadnought-class building.",
     "treaty": "NPT (P5)"},
    {"country": "Pakistan", "lat": 33.6844, "lon": 73.0479, "warheads": 170, "first_test": "1998-05-28",
     "delivery": "Shaheen-III MRBM, Babur cruise missile, Nasr tactical, F-16 aircraft",
     "status": "Fastest-growing arsenal. Tactical nukes for battlefield use. A.Q. Khan network legacy.",
     "treaty": "Non-NPT"},
    {"country": "India", "lat": 28.6139, "lon": 77.2090, "warheads": 172, "first_test": "1974-05-18",
     "delivery": "Agni-V ICBM, Agni-P MRBM, K-4 SLBM, Arihant-class SSBNs, Rafale fighters",
     "status": "No-first-use policy. Triad-capable. INS Arighat second SSBN commissioned.",
     "treaty": "Non-NPT"},
    {"country": "Israel", "lat": 31.7683, "lon": 35.2137, "warheads": 90, "first_test": "Suspected 1979 (Vela Incident)",
     "delivery": "Jericho III ICBM, Dolphin-class submarine cruise missiles, F-35I",
     "status": "Policy of deliberate ambiguity — neither confirms nor denies. Dimona facility.",
     "treaty": "Non-NPT, undeclared"},
    {"country": "North Korea", "lat": 39.0392, "lon": 125.7625, "warheads": 50, "first_test": "2006-10-09",
     "delivery": "Hwasong-17/18 ICBM, Pukguksong SLBM, KN-23/25 tactical missiles",
     "status": "Est. 40-50 warheads. Thermonuclear capability claimed. Solid-fuel ICBM tested 2023.",
     "treaty": "Withdrew from NPT (2003)"},
]

NUCLEAR_WASTE_SITES = [
    {"name": "Onkalo (POSIVA)", "lat": 61.2353, "lon": 21.4817, "country": "Finland",
     "type": "Deep geological repository", "status": "Under construction — first in world",
     "description": "World's first permanent spent fuel repository. 450m deep in Precambrian bedrock. Olkiluoto island. Expected to operate 100+ years."},
    {"name": "Yucca Mountain", "lat": 36.8383, "lon": -116.4283, "country": "United States",
     "type": "Deep geological repository (cancelled)", "status": "Politically blocked since 2010",
     "description": "Designated 1987, licensed 2008, defunded by Obama admin. 70,000+ tons of US spent fuel still in interim storage at 70+ sites."},
    {"name": "Forsmark SFR", "lat": 60.4000, "lon": 18.1667, "country": "Sweden",
     "type": "Deep geological repository", "status": "Approved 2022",
     "description": "SKB's planned final repository for spent fuel in crystalline bedrock. Adjacent to Forsmark NPP. ~500m depth."},
    {"name": "Sellafield", "lat": 54.4200, "lon": -3.4950, "country": "United Kingdom",
     "type": "Reprocessing & interim storage", "status": "Decommissioning (decades remaining)",
     "description": "Europe's largest nuclear site. THORP & Magnox reprocessing. B30 pond: world's most hazardous building. Cleanup cost: >£100B."},
    {"name": "La Hague", "lat": 49.6783, "lon": -1.8817, "country": "France",
     "type": "Reprocessing plant", "status": "Operating",
     "description": "Orano facility. Reprocesses ~1,700 tonnes/yr of spent fuel from France & international clients. MOX fuel production."},
    {"name": "Hanford Site", "lat": 46.5500, "lon": -119.4883, "country": "United States",
     "type": "Former weapons production & waste storage", "status": "Cleanup (est. completion 2070+)",
     "description": "Produced plutonium for Nagasaki bomb & Cold War arsenal. 56M gallons of radioactive waste in 177 underground tanks. Most contaminated site in Western Hemisphere."},
    {"name": "Savannah River Site", "lat": 33.2500, "lon": -81.6167, "country": "United States",
     "type": "Weapons material production & waste", "status": "Cleanup ongoing",
     "description": "DOE facility in South Carolina. Produced tritium & plutonium. Defense Waste Processing Facility vitrifies HLW into glass logs."},
    {"name": "Mayak PA / Ozersk", "lat": 55.7167, "lon": 60.8000, "country": "Russia",
     "type": "Reprocessing & weapons production", "status": "Operating (reprocessing)",
     "description": "Site of 1957 Kyshtym disaster. Still reprocesses naval & civilian spent fuel. Techa River heavily contaminated."},
    {"name": "WIPP (Waste Isolation Pilot Plant)", "lat": 32.3700, "lon": -103.7900, "country": "United States",
     "type": "Deep geological repository (TRU waste)", "status": "Operating",
     "description": "Only operating deep geological repository in the world (for defense transuranic waste). 655m deep in Permian salt beds, New Mexico."},
    {"name": "Gorleben", "lat": 53.0333, "lon": 11.3500, "country": "Germany",
     "type": "Interim storage (salt dome exploration abandoned)", "status": "Abandoned as repository",
     "description": "Decades of protests. Salt dome explored 1979-2012. Ruled out 2020. Germany still searching for permanent HLW site."},
    {"name": "Cigéo (Bure)", "lat": 48.6333, "lon": 5.6167, "country": "France",
     "type": "Deep geological repository (planned)", "status": "Under development",
     "description": "ANDRA's planned deep geological disposal in Callovo-Oxfordian clay, Meuse/Haute-Marne. Target operation ~2035."},
    {"name": "Rokkasho Reprocessing Plant", "lat": 40.9600, "lon": 141.3267, "country": "Japan",
     "type": "Reprocessing plant", "status": "Testing (decades delayed)",
     "description": "JNFL facility. 800 t/yr capacity. Over 25 years delayed, $30B+ cost. Key to Japan's nuclear fuel cycle closure strategy."},
]

DECOMMISSIONED_PLANTS = [
    {"name": "Chernobyl NPP (Units 1-3)", "lat": 51.3891, "lon": 26.0444, "country": "Ukraine",
     "shutdown": "2000", "capacity_mw": 3000, "type": "LWGR (RBMK-1000)",
     "description": "Units 1-3 operated after 1986 disaster until 2000. New Safe Confinement arch (2016) covers Unit 4. Decommissioning: ~2065."},
    {"name": "Fukushima Daiichi (Units 1-6)", "lat": 37.4211, "lon": 141.0328, "country": "Japan",
     "shutdown": "2011", "capacity_mw": 4696, "type": "BWR",
     "description": "All 6 units permanently closed. Fuel debris removal from Units 1-3 ongoing (est. 30-40 years). ALPS treated water release began 2023."},
    {"name": "San Onofre (SONGS)", "lat": 33.3681, "lon": -117.5558, "country": "United States",
     "shutdown": "2013", "capacity_mw": 2150, "type": "PWR",
     "description": "Closed after steam generator tube failures. Spent fuel in dry cask storage on beach. Decommissioning by 2028."},
    {"name": "Vermont Yankee", "lat": 42.7800, "lon": -72.5150, "country": "United States",
     "shutdown": "2014", "capacity_mw": 620, "type": "BWR",
     "description": "GE Mark I BWR. Closed for economic reasons. NorthStar decommissioning. Site restoration target: 2030."},
    {"name": "Doel 3", "lat": 51.3258, "lon": 4.2594, "country": "Belgium",
     "shutdown": "2022", "capacity_mw": 1006, "type": "PWR",
     "description": "Part of Belgium's nuclear phaseout. Shut down September 2022. Doel 4 closed 2025. Tihange units also phasing out."},
    {"name": "Greifswald (Units 1-5)", "lat": 54.1417, "lon": 13.6600, "country": "Germany",
     "shutdown": "1990", "capacity_mw": 2200, "type": "PWR (VVER-440)",
     "description": "Soviet-designed reactors in East Germany. Shut at reunification due to safety concerns. Decommissioning ongoing since 1995."},
    {"name": "Ignalina (Units 1-2)", "lat": 55.6047, "lon": 26.5595, "country": "Lithuania",
     "shutdown": "2009", "capacity_mw": 3000, "type": "LWGR (RBMK-1500)",
     "description": "World's most powerful reactors (1500 MW each). Closed as EU accession condition. Chernobyl-type. Decommissioning funded by EU."},
    {"name": "Oldbury", "lat": 51.6472, "lon": -2.5700, "country": "United Kingdom",
     "shutdown": "2012", "capacity_mw": 434, "type": "GCR (Magnox)",
     "description": "One of the last Magnox reactors. Operated 45 years. Defueled. Full decommissioning deferred to ~2092."},
    {"name": "Calder Hall", "lat": 54.4200, "lon": -3.4883, "country": "United Kingdom",
     "shutdown": "2003", "capacity_mw": 240, "type": "GCR (Magnox)",
     "description": "World's first commercial nuclear power station (1956). Also produced weapons-grade plutonium. 47 years of operation."},
    {"name": "Philippsburg 2", "lat": 49.2500, "lon": 8.4333, "country": "Germany",
     "shutdown": "2019", "capacity_mw": 1468, "type": "PWR",
     "description": "Closed as part of Energiewende. Cooling tower demolished 2020. Last German reactors closed April 2023."},
    {"name": "Indian Point (Units 2-3)", "lat": 41.2700, "lon": -73.9528, "country": "United States",
     "shutdown": "2021", "capacity_mw": 2069, "type": "PWR",
     "description": "35 miles north of NYC. Closed after decades of controversy. Holtec decommissioning. Spent fuel on-site."},
    {"name": "Fessenheim", "lat": 47.9083, "lon": 7.5628, "country": "France",
     "shutdown": "2020", "capacity_mw": 1800, "type": "PWR",
     "description": "France's oldest NPP. Closed after 43 years amid seismic & flooding concerns. Near Rhine, French-German-Swiss border."},
]

NUCLEAR_RESEARCH_FACILITIES = [
    {"name": "CERN (LHC)", "lat": 46.2333, "lon": 6.0500, "country": "Switzerland/France",
     "type": "Particle accelerator", "status": "Operating",
     "description": "Large Hadron Collider — 27 km circumference. Discovered Higgs boson (2012). HL-LHC upgrade underway."},
    {"name": "ITER", "lat": 43.7083, "lon": 5.7583, "country": "France",
     "type": "Fusion reactor (tokamak)", "status": "Under construction",
     "description": "International thermonuclear experimental reactor. 35 nations. First plasma target ~2035. Cadarache, Provence."},
    {"name": "JET (Joint European Torus)", "lat": 51.6592, "lon": -1.2272, "country": "United Kingdom",
     "type": "Fusion reactor (tokamak)", "status": "Decommissioning (record set 2022)",
     "description": "Set fusion energy record: 69 MJ in 2022. Culham Centre for Fusion Energy. MAST Upgrade now operational."},
    {"name": "EAST (Experimental Advanced Superconducting Tokamak)", "lat": 31.8400, "lon": 117.2600,
     "country": "China", "type": "Fusion reactor (tokamak)", "status": "Operating",
     "description": "Hefei, Anhui. Set record: 1,066 seconds of plasma (2023). Key for CFETR fusion power plant design."},
    {"name": "Fermilab (Tevatron)", "lat": 41.8423, "lon": -88.2578, "country": "United States",
     "type": "Particle accelerator", "status": "Research ongoing (Tevatron shut 2011)",
     "description": "Former highest-energy collider. Now runs neutrino experiments (DUNE, NOvA, Mu2e). Batavia, Illinois."},
    {"name": "Brookhaven National Lab (RHIC)", "lat": 40.8683, "lon": -72.8789, "country": "United States",
     "type": "Particle accelerator (heavy ion)", "status": "Operating",
     "description": "Relativistic Heavy Ion Collider. Creates quark-gluon plasma. Also operates NSLS-II synchrotron. Long Island, NY."},
    {"name": "Idaho National Laboratory", "lat": 43.5153, "lon": -112.9353, "country": "United States",
     "type": "Nuclear research & SMR testing", "status": "Operating",
     "description": "52 reactors built (most in world). MARVEL microreactor, NRIC test bed. NuScale SMR planned nearby."},
    {"name": "Oak Ridge National Laboratory", "lat": 35.9311, "lon": -84.3100, "country": "United States",
     "type": "Nuclear research & isotope production", "status": "Operating",
     "description": "Manhattan Project site. Spallation Neutron Source. High-Flux Isotope Reactor produces Cf-252 & medical isotopes."},
    {"name": "KAERI (Korea Atomic Energy Research Institute)", "lat": 36.4250, "lon": 127.3711,
     "country": "South Korea", "type": "Nuclear research", "status": "Operating",
     "description": "HANARO research reactor. Develops Korean APR-1400 reactor design (exported to UAE Barakah). Daejeon Science City."},
    {"name": "JINR (Joint Institute for Nuclear Research)", "lat": 56.7467, "lon": 37.2867,
     "country": "Russia", "type": "Particle physics research", "status": "Operating",
     "description": "Dubna. Discovered elements 104-118 (Rutherfordium through Oganesson). NICA collider under construction."},
    {"name": "Tokai-mura Research Complex", "lat": 36.4500, "lon": 140.6000, "country": "Japan",
     "type": "Nuclear research & reprocessing", "status": "Operating (partially)",
     "description": "JAEA complex. J-PARC spallation source. Site of 1999 criticality accident. Multiple research reactors."},
    {"name": "Cadarache CEA", "lat": 43.6875, "lon": 5.7556, "country": "France",
     "type": "Nuclear research center", "status": "Operating",
     "description": "CEA's largest nuclear research center. Jules Horowitz research reactor under construction. Adjacent to ITER."},
    {"name": "Culham Centre for Fusion Energy", "lat": 51.6592, "lon": -1.2272, "country": "United Kingdom",
     "type": "Fusion research", "status": "Operating",
     "description": "Home of JET and MAST-Upgrade. UKAEA fusion technology hub. STEP (Spherical Tokamak for Energy Production) program HQ."},
    {"name": "Wendelstein 7-X", "lat": 54.0750, "lon": 13.3700, "country": "Germany",
     "type": "Fusion reactor (stellarator)", "status": "Operating",
     "description": "World's largest stellarator. Max Planck Institute, Greifswald. Alternative to tokamak design. Record plasma confinement."},
]

HIROSHIMA_NAGASAKI = [
    {"name": "Hiroshima Ground Zero (Airburst)", "lat": 34.3945, "lon": 132.4536,
     "event": "Little Boy", "date": "1945-08-06", "yield_kt": 15, "altitude_m": 580,
     "deaths": "~80,000 immediate; ~140,000 by Dec 1945",
     "description": "Uranium-235 gun-type bomb. Detonated 580m above Shima Hospital. 1-km radius completely destroyed. Firestorm engulfed 11 km2."},
    {"name": "Hiroshima Peace Memorial (A-Bomb Dome)", "lat": 34.3955, "lon": 132.4536,
     "event": "Memorial", "date": "UNESCO 1996", "yield_kt": 0, "altitude_m": 0,
     "deaths": "", "description": "Genbaku Dome — only structure left standing near hypocenter. UNESCO World Heritage Site. Symbol of nuclear abolition."},
    {"name": "Hiroshima Peace Memorial Park", "lat": 34.3915, "lon": 132.4518,
     "event": "Memorial", "date": "Opened 1954", "yield_kt": 0, "altitude_m": 0,
     "deaths": "", "description": "12-hectare park. Cenotaph, Flame of Peace, Children's Memorial (Sadako & 1,000 cranes). Museum: 2M visitors/year."},
    {"name": "Nagasaki Ground Zero (Airburst)", "lat": 32.7737, "lon": 129.8632,
     "event": "Fat Man", "date": "1945-08-09", "yield_kt": 21, "altitude_m": 503,
     "deaths": "~40,000 immediate; ~70,000 by Dec 1945",
     "description": "Plutonium implosion bomb. Detonated 503m above Urakami Valley. Hills channeled blast — reduced destruction vs. Hiroshima."},
    {"name": "Nagasaki Peace Park", "lat": 32.7755, "lon": 129.8643,
     "event": "Memorial", "date": "Opened 1955", "yield_kt": 0, "altitude_m": 0,
     "deaths": "", "description": "Peace Statue (right hand points to nuclear threat, left extends for peace). Fountain of Peace. Annual ceremony August 9."},
    {"name": "Nagasaki Atomic Bomb Museum", "lat": 32.7733, "lon": 129.8642,
     "event": "Memorial", "date": "Opened 1996", "yield_kt": 0, "altitude_m": 0,
     "deaths": "", "description": "Exhibits include stopped clocks, melted artifacts, hibakusha testimonies. Adjacent to hypocenter park."},
    {"name": "Urakami Cathedral (rebuilt)", "lat": 32.7778, "lon": 129.8659,
     "event": "Destruction & rebuilding", "date": "Destroyed 1945, rebuilt 1959", "yield_kt": 0, "altitude_m": 0,
     "deaths": "~8,500 parishioners killed", "description": "Largest cathedral in East Asia at the time. 500m from hypocenter. Completely destroyed. Rebuilt in 1959. Relocated bomb-damaged statues."},
]


# ═══════════════════════════════════════════════════════════════
# OVERPASS API QUERIES
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _query_overpass(query: str) -> list:
    """Run an Overpass QL query and return elements."""
    try:
        resp = requests.post(OVERPASS_API, data={"data": query}, timeout=60)
        resp.raise_for_status()
        return resp.json().get("elements", [])
    except Exception as e:
        logger.warning("Overpass query failed: %s", e)
        return []


@st.cache_data(ttl=3600)
def fetch_nuclear_power_plants() -> list:
    """Fetch operating nuclear power plants from OpenStreetMap."""
    query = """
    [out:json][timeout:60];
    (
      node["plant:source"="nuclear"]["power"="plant"];
      way["plant:source"="nuclear"]["power"="plant"];
      relation["plant:source"="nuclear"]["power"="plant"];
      node["generator:source"="nuclear"];
      way["generator:source"="nuclear"];
    );
    out center tags;
    """
    return _query_overpass(query)


@st.cache_data(ttl=3600)
def fetch_radiation_monitors() -> list:
    """Fetch radiation monitoring stations from OpenStreetMap."""
    query = """
    [out:json][timeout:60];
    (
      node["monitoring:radiation"="yes"];
      node["man_made"="monitoring_station"]["monitoring:radiation"="yes"];
      node["man_made"="monitoring_station"]["monitoring"~"radiation"];
    );
    out center tags;
    """
    return _query_overpass(query)


@st.cache_data(ttl=3600)
def fetch_decommissioned_osm() -> list:
    """Fetch decommissioned/disused nuclear plants from OSM."""
    query = """
    [out:json][timeout:60];
    (
      node["disused:plant:source"="nuclear"];
      way["disused:plant:source"="nuclear"];
      node["plant:source"="nuclear"]["power"="plant"]["plant:output:electricity"="0"];
      way["plant:source"="nuclear"]["power"="plant"]["plant:output:electricity"="0"];
    );
    out center tags;
    """
    return _query_overpass(query)


# ═══════════════════════════════════════════════════════════════
# HELPER: DARK-THEMED MATPLOTLIB CHART
# ═══════════════════════════════════════════════════════════════

def _dark_bar_chart(labels, values, title, xlabel, ylabel, color="#06b6d4", figsize=(8, 4), horizontal=False):
    """Create a dark-themed bar chart and display via st.pyplot."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor="#0a0e1a", alpha=0.85)
        ax.set_xlabel(ylabel, color="#e8ecf4", fontsize=10)
        ax.set_ylabel(xlabel, color="#e8ecf4", fontsize=10)
    else:
        bars = ax.bar(labels, values, color=color, edgecolor="#0a0e1a", alpha=0.85)
        ax.set_xlabel(xlabel, color="#e8ecf4", fontsize=10)
        ax.set_ylabel(ylabel, color="#e8ecf4", fontsize=10)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color="#e8ecf4", fontsize=12, fontweight="bold", pad=10)
    ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
    ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7, axis="both")
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _make_dark_map(location=None, zoom=2):
    """Create a Folium map with dark tile layer."""
    loc = location or [25, 10]
    m = folium.Map(location=loc, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark Matter",
        name="Dark Base",
    ).add_to(m)
    return m


def _render_map(m, height=500):
    """Render a Folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _csv_download(df, filename, label, key):
    """Render a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename, mime="text/csv", key=key)


# ═══════════════════════════════════════════════════════════════
# MODE 1: NUCLEAR POWER PLANTS
# ═══════════════════════════════════════════════════════════════

def _render_power_plants():
    st.markdown("#### Operating Nuclear Power Plants")
    st.markdown("Data from OpenStreetMap via Overpass API — nuclear-tagged power plants and generators worldwide.")

    with st.spinner("Querying OpenStreetMap for nuclear power plants..."):
        elements = fetch_nuclear_power_plants()

    rows = []
    for el in elements:
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if not lat or not lon:
            continue
        name = tags.get("name", tags.get("operator", "Unknown"))
        capacity = tags.get("plant:output:electricity", tags.get("generator:output:electricity", ""))
        reactor_type = tags.get("generator:type", tags.get("reactor:type", "Unknown"))
        operator = tags.get("operator", "")
        country = tags.get("addr:country", tags.get("is_in:country", ""))
        rows.append({
            "name": name, "lat": lat, "lon": lon, "capacity": capacity,
            "reactor_type": reactor_type, "operator": operator, "country": country,
        })

    # Deduplicate by rounding coordinates
    seen = set()
    unique_rows = []
    for r in rows:
        key = (round(r["lat"], 3), round(r["lon"], 3))
        if key not in seen:
            seen.add(key)
            unique_rows.append(r)
    rows = unique_rows

    if not rows:
        st.warning("No nuclear power plants returned from Overpass API. The server may be busy — try again in a moment.")
        return

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Plants Found", f"{len(rows):,}")
    with c2:
        countries = set(r["country"] for r in rows if r["country"])
        st.metric("Countries", f"{len(countries) if countries else '30+':}")
    with c3:
        types = set(r["reactor_type"] for r in rows if r["reactor_type"] != "Unknown")
        st.metric("Reactor Types", f"{len(types)}")
    with c4:
        st.metric("Global Share", "~10% of electricity")

    # Map
    st.markdown("---")
    m = _make_dark_map(zoom=2)
    for r in rows:
        rtype = r["reactor_type"].upper() if r["reactor_type"] else "Other"
        color = COLORS["operating"]
        for key, clr in REACTOR_TYPE_COLORS.items():
            if key in rtype:
                color = clr
                break
        popup_html = (
            f'<div style="max-width:240px;">'
            f'<strong>{escape(r["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Type: {escape(r["reactor_type"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Capacity: {escape(r["capacity"] or "N/A")}</span><br/>'
            f'<span style="font-size:0.85rem;">Operator: {escape(r["operator"] or "N/A")}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{r["lat"]:.4f}, {r["lon"]:.4f}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[r["lat"], r["lon"]], radius=6,
            color=color, fill=True, fill_color=color, fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=260),
        ).add_to(m)
    _render_map(m)

    # Reactor type legend
    legend_items = " ".join(
        f'<span style="color:{clr}; font-size:0.8rem;">● {t}</span>'
        for t, clr in REACTOR_TYPE_COLORS.items()
    )
    st.markdown(f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">{legend_items}</div>', unsafe_allow_html=True)

    # Data table
    df = pd.DataFrame(rows)
    with st.expander(f"Full Data Table ({len(df)} plants)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "nuclear_power_plants.csv", f"Download {len(df)} Plants (CSV)", "nuc_plants_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 2: NUCLEAR DISASTERS
# ═══════════════════════════════════════════════════════════════

def _render_disasters():
    st.markdown("#### Nuclear Disasters & Major Accidents")
    st.markdown("INES Level 4-7 nuclear accidents — from Chernobyl and Fukushima to lesser-known incidents.")

    data = NUCLEAR_DISASTERS

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Major Accidents", f"{len(data)}")
    with c2:
        ines7 = sum(1 for d in data if d["ines"] == 7)
        st.metric("INES Level 7", f"{ines7}")
    with c3:
        ines56 = sum(1 for d in data if d["ines"] in (5, 6))
        st.metric("INES Level 5-6", f"{ines56}")
    with c4:
        with_exclusion = sum(1 for d in data if d["exclusion_km"] > 0)
        st.metric("Active Exclusion Zones", f"{with_exclusion}")

    # INES color mapping
    ines_colors = {7: "#dc2626", 6: "#ef4444", 5: "#f97316", 4: "#f59e0b"}

    st.markdown("---")
    m = _make_dark_map(location=[40, 30], zoom=3)
    for d in data:
        color = ines_colors.get(d["ines"], "#8b97b0")
        popup_html = (
            f'<div style="max-width:280px;">'
            f'<strong style="color:{color};">{escape(d["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">INES Level: <b>{d["ines"]}</b></span><br/>'
            f'<span style="font-size:0.85rem;">Date: {escape(d["date"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Country: {escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Deaths: {escape(d["deaths"])}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=8 + d["ines"],
            color=color, fill=True, fill_color=color, fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)

        # Exclusion zones
        if d["exclusion_km"] > 0:
            folium.Circle(
                location=[d["lat"], d["lon"]],
                radius=d["exclusion_km"] * 1000,
                color="#ef4444", fill=True, fill_color="#ef4444",
                fill_opacity=0.1, weight=1, dash_array="5,5",
                popup=f'{escape(d["name"])}: {d["exclusion_km"]} km exclusion zone',
            ).add_to(m)

    _render_map(m)

    # INES legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#dc2626; font-size:0.8rem;">● INES 7 — Major Accident</span>
        <span style="color:#ef4444; font-size:0.8rem;">● INES 6 — Serious Accident</span>
        <span style="color:#f97316; font-size:0.8rem;">● INES 5 — Accident w/ Wider Consequences</span>
        <span style="color:#f59e0b; font-size:0.8rem;">● INES 4 — Accident w/ Local Consequences</span>
    </div>
    """, unsafe_allow_html=True)

    # Chart — INES distribution
    ines_counts = {}
    for d in data:
        lvl = f"INES {d['ines']}"
        ines_counts[lvl] = ines_counts.get(lvl, 0) + 1
    _dark_bar_chart(
        list(ines_counts.keys()), list(ines_counts.values()),
        "Accidents by INES Level", "INES Level", "Count", color="#ef4444"
    )

    # Data table
    df = pd.DataFrame(data)
    with st.expander(f"Full Data Table ({len(df)} incidents)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "nuclear_disasters.csv", f"Download {len(df)} Disasters (CSV)", "nuc_disaster_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 3: NUCLEAR TEST SITES
# ═══════════════════════════════════════════════════════════════

def _render_test_sites():
    st.markdown("#### Nuclear Test Sites")
    st.markdown("All known nuclear weapon test locations — 2,056 detonations by 8 nations from 1945 to 2017.")

    data = NUCLEAR_TEST_SITES

    # Stats
    total_tests = sum(d["tests"] for d in data)
    countries_tested = len(set(d["country"].split("/")[0].split("(")[0].strip() for d in data))
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Tests", f"{total_tests:,}")
    with c2:
        st.metric("Test Sites", f"{len(data)}")
    with c3:
        st.metric("Nations", f"{countries_tested}")
    with c4:
        st.metric("Period", "1945-2017")

    # Map
    st.markdown("---")
    m = _make_dark_map(zoom=2)
    for d in data:
        # Color by test type
        ttype = d["type"].lower()
        if "atmospheric" in ttype and "underground" in ttype:
            color = "#f59e0b"
        elif "atmospheric" in ttype:
            color = COLORS["test_atmo"]
        elif "underwater" in ttype or "underwater" in ttype:
            color = COLORS["test_uw"]
        else:
            color = COLORS["test_under"]

        radius = max(5, min(15, d["tests"] / 50 + 5))
        popup_html = (
            f'<div style="max-width:280px;">'
            f'<strong>{escape(d["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Country: {escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Tests: <b>{d["tests"]}</b></span><br/>'
            f'<span style="font-size:0.85rem;">Period: {escape(d["period"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Type: {escape(d["type"])}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)
    _render_map(m)

    # Legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#f59e0b; font-size:0.8rem;">● Atmospheric & Underground</span>
        <span style="color:#f97316; font-size:0.8rem;">● Underground Only</span>
        <span style="color:#06b6d4; font-size:0.8rem;">● Underwater</span>
    </div>
    <div style="color:#5a6580; font-size:0.75rem; margin-top:0.25rem;">Circle size proportional to number of tests.</div>
    """, unsafe_allow_html=True)

    # Chart — tests by country
    country_tests = {}
    for d in data:
        c = d["country"].split("/")[0].split("(")[0].strip()
        if c == "Soviet Union ":
            c = "Soviet Union"
        country_tests[c] = country_tests.get(c, 0) + d["tests"]
    sorted_ct = sorted(country_tests.items(), key=lambda x: x[1], reverse=True)
    _dark_bar_chart(
        [x[0] for x in sorted_ct], [x[1] for x in sorted_ct],
        "Nuclear Tests by Country", "Country", "Number of Tests", color="#f59e0b"
    )

    # Data table
    df = pd.DataFrame(data)
    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "nuclear_test_sites.csv", f"Download {len(df)} Test Sites (CSV)", "nuc_test_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 4: URANIUM MINES
# ═══════════════════════════════════════════════════════════════

def _render_uranium_mines():
    st.markdown("#### Uranium Mining Regions")
    st.markdown("Major uranium mines worldwide — Kazakhstan, Canada, Australia, Niger, and Namibia produce ~75% of global supply.")

    data = URANIUM_MINES

    # Stats
    total_prod = sum(d["production_t"] for d in data)
    operating = sum(1 for d in data if "Operating" in d["status"])
    countries = len(set(d["country"] for d in data))
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Mines Listed", f"{len(data)}")
    with c2:
        st.metric("Currently Operating", f"{operating}")
    with c3:
        st.metric("Countries", f"{countries}")
    with c4:
        st.metric("Combined Production", f"{total_prod:,} tU/yr")

    # Map
    st.markdown("---")
    m = _make_dark_map(zoom=2)
    for d in data:
        is_operating = "Operating" in d["status"]
        color = COLORS["uranium"] if is_operating else COLORS["shutdown"]
        radius = max(5, min(12, d["production_t"] / 500 + 4))
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(d["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Country: {escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Production: {d["production_t"]:,} tU/yr</span><br/>'
            f'<span style="font-size:0.85rem;">Status: {escape(d["status"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Type: {escape(d["type"])}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)
    _render_map(m)

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#a855f7; font-size:0.8rem;">● Operating</span>
        <span style="color:#8b97b0; font-size:0.8rem;">● Closed / Suspended / Remediation</span>
    </div>
    """, unsafe_allow_html=True)

    # Chart — production by mine
    operating_mines = [d for d in data if d["production_t"] > 0]
    operating_mines.sort(key=lambda x: x["production_t"], reverse=True)
    _dark_bar_chart(
        [d["name"][:20] for d in operating_mines],
        [d["production_t"] for d in operating_mines],
        "Annual Uranium Production by Mine (tU)", "Mine", "Production (tU/yr)",
        color="#a855f7"
    )

    # Data table
    df = pd.DataFrame(data)
    with st.expander(f"Full Data Table ({len(df)} mines)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "uranium_mines.csv", f"Download {len(df)} Mines (CSV)", "nuc_uranium_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 5: NUCLEAR WEAPONS STATES
# ═══════════════════════════════════════════════════════════════

def _render_weapons_states():
    st.markdown("#### Nuclear Weapons States")
    st.markdown("Nine nations possess nuclear weapons — collectively ~12,500 warheads, down from a Cold War peak of ~70,000.")

    data = NUCLEAR_WEAPONS_STATES

    # Stats
    total_warheads = sum(d["warheads"] for d in data)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Nuclear-Armed States", f"{len(data)}")
    with c2:
        st.metric("Total Warheads (est.)", f"~{total_warheads:,}")
    with c3:
        st.metric("Cold War Peak", "~70,300 (1986)")
    with c4:
        st.metric("NPT Nuclear States (P5)", "5")

    # Map
    st.markdown("---")
    m = _make_dark_map(zoom=2)
    for d in data:
        radius = max(6, min(18, d["warheads"] / 400 + 5))
        color = COLORS["weapons"]
        popup_html = (
            f'<div style="max-width:300px;">'
            f'<strong style="color:#dc2626;">{escape(d["country"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Warheads: <b>{d["warheads"]:,}</b></span><br/>'
            f'<span style="font-size:0.85rem;">First Test: {escape(str(d["first_test"]))}</span><br/>'
            f'<span style="font-size:0.85rem;">Delivery: {escape(d["delivery"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Treaty: {escape(d["treaty"])}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d["status"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.65, weight=2,
            popup=folium.Popup(popup_html, max_width=320),
        ).add_to(m)
    _render_map(m)

    st.markdown(
        '<div style="color:#5a6580; font-size:0.75rem;">Circle size proportional to estimated warhead count.</div>',
        unsafe_allow_html=True,
    )

    # Chart — warheads by country
    sorted_data = sorted(data, key=lambda x: x["warheads"], reverse=True)
    _dark_bar_chart(
        [d["country"] for d in sorted_data],
        [d["warheads"] for d in sorted_data],
        "Estimated Nuclear Warheads by Country", "Country", "Warheads",
        color="#dc2626"
    )

    # Data table
    df = pd.DataFrame(data)
    with st.expander(f"Full Data Table ({len(df)} states)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "nuclear_weapons_states.csv", f"Download {len(df)} States (CSV)", "nuc_weapons_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 6: RADIATION MONITORING
# ═══════════════════════════════════════════════════════════════

def _render_radiation_monitoring():
    st.markdown("#### Radiation Monitoring Stations")
    st.markdown("Environmental radiation monitoring points from OpenStreetMap — gamma dose rate stations and environmental sensors.")

    with st.spinner("Querying OpenStreetMap for radiation monitoring stations..."):
        elements = fetch_radiation_monitors()

    rows = []
    for el in elements:
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if not lat or not lon:
            continue
        name = tags.get("name", tags.get("operator", "Monitoring Station"))
        operator = tags.get("operator", "")
        ref = tags.get("ref", "")
        rows.append({"name": name, "lat": lat, "lon": lon, "operator": operator, "ref": ref})

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Stations Found", f"{len(rows):,}")
    with c2:
        operators = set(r["operator"] for r in rows if r["operator"])
        st.metric("Operators", f"{len(operators)}")
    with c3:
        st.metric("Data Source", "OpenStreetMap")
    with c4:
        st.metric("Global Networks", "CTBTO, EURDEP, EPA RadNet")

    if not rows:
        st.info("No radiation monitoring stations found in OSM. This data layer depends on community mapping contributions.")
        st.markdown("""
        **Known global monitoring networks** (not all mapped in OSM):
        - **CTBTO IMS**: 321 stations in 89 countries (seismic, hydroacoustic, infrasound, radionuclide)
        - **EURDEP**: 5,500+ stations across Europe (real-time gamma dose rates)
        - **EPA RadNet**: 140+ stations across the United States
        - **SAFECAST**: 100M+ citizen-science measurements (open data, post-Fukushima)
        """)
        return

    # Map
    st.markdown("---")
    m = _make_dark_map(zoom=3)
    for r in rows:
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>{escape(r["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Operator: {escape(r["operator"] or "N/A")}</span><br/>'
            f'<span style="font-size:0.85rem;">Ref: {escape(r["ref"] or "N/A")}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{r["lat"]:.4f}, {r["lon"]:.4f}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[r["lat"], r["lon"]], radius=5,
            color=COLORS["monitoring"], fill=True, fill_color=COLORS["monitoring"],
            fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(m)
    _render_map(m)

    # Info on background radiation
    st.markdown("---")
    st.markdown("##### Background Radiation Reference Levels")
    ref_data = [
        ("Natural background (avg.)", "2.4 mSv/yr", "Cosmic rays, radon, soil, food"),
        ("Chest X-ray", "0.02 mSv", "Single exposure"),
        ("CT scan (abdomen)", "8 mSv", "Single exposure"),
        ("Airline crew (annual)", "2-5 mSv/yr", "Cosmic radiation at altitude"),
        ("Radon in homes (avg.)", "1.2 mSv/yr", "Varies by geology"),
        ("US annual limit (public)", "1 mSv/yr", "Above natural background"),
        ("Nuclear worker limit", "20 mSv/yr", "Averaged over 5 years"),
        ("Acute radiation syndrome", "1,000+ mSv", "Single acute dose"),
    ]
    ref_df = pd.DataFrame(ref_data, columns=["Source", "Dose", "Notes"])
    st.dataframe(ref_df, width="stretch", hide_index=True)

    # Data table
    df = pd.DataFrame(rows)
    with st.expander(f"Full Data Table ({len(df)} stations)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "radiation_monitors.csv", f"Download {len(df)} Stations (CSV)", "nuc_monitor_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 7: NUCLEAR WASTE STORAGE
# ═══════════════════════════════════════════════════════════════

def _render_waste_storage():
    st.markdown("#### Nuclear Waste Storage & Repositories")
    st.markdown("Spent fuel repositories, reprocessing plants, and deep geological disposal sites worldwide.")

    data = NUCLEAR_WASTE_SITES

    # Stats
    operating = sum(1 for d in data if "Operating" in d["status"])
    planned = sum(1 for d in data if "construction" in d["status"].lower() or "development" in d["status"].lower() or "Approved" in d["status"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Sites Listed", f"{len(data)}")
    with c2:
        st.metric("Operating", f"{operating}")
    with c3:
        st.metric("Under Development", f"{planned}")
    with c4:
        st.metric("Global Spent Fuel", "~400,000 tonnes")

    # Map
    st.markdown("---")
    m = _make_dark_map(location=[45, 10], zoom=3)
    for d in data:
        is_active = "Operating" in d["status"] or "construction" in d["status"].lower()
        color = COLORS["waste"] if is_active else COLORS["shutdown"]
        popup_html = (
            f'<div style="max-width:280px;">'
            f'<strong>{escape(d["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Country: {escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Type: {escape(d["type"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Status: {escape(d["status"])}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)
    _render_map(m)

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#ec4899; font-size:0.8rem;">● Operating / Under Construction</span>
        <span style="color:#8b97b0; font-size:0.8rem;">● Cancelled / Abandoned / Decommissioning</span>
    </div>
    """, unsafe_allow_html=True)

    # Chart — sites by type
    type_counts = {}
    for d in data:
        t = d["type"].split("(")[0].strip()
        type_counts[t] = type_counts.get(t, 0) + 1
    _dark_bar_chart(
        list(type_counts.keys()), list(type_counts.values()),
        "Nuclear Waste Sites by Type", "Type", "Count",
        color="#ec4899"
    )

    # Data table
    df = pd.DataFrame(data)
    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "nuclear_waste_sites.csv", f"Download {len(df)} Sites (CSV)", "nuc_waste_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 8: DECOMMISSIONED PLANTS
# ═══════════════════════════════════════════════════════════════

def _render_decommissioned():
    st.markdown("#### Decommissioned Nuclear Power Plants")
    st.markdown("Permanently shut-down nuclear reactors worldwide — cleanup timelines, brownfield status, and reactor types.")

    data = DECOMMISSIONED_PLANTS

    # Also try to enrich from OSM
    with st.spinner("Fetching additional decommissioned plants from OpenStreetMap..."):
        osm_data = fetch_decommissioned_osm()

    osm_rows = []
    for el in osm_data:
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if not lat or not lon:
            continue
        name = tags.get("name", "Unknown Facility")
        # Check not already in curated list
        already = any(abs(d["lat"] - lat) < 0.05 and abs(d["lon"] - lon) < 0.05 for d in data)
        if not already:
            osm_rows.append({
                "name": name, "lat": lat, "lon": lon,
                "country": tags.get("addr:country", ""),
                "shutdown": "", "capacity_mw": 0,
                "type": tags.get("reactor:type", "Unknown"),
                "description": f"Decommissioned facility (OSM data). Operator: {tags.get('operator', 'N/A')}",
            })

    combined = data + osm_rows

    # Stats
    total_capacity = sum(d["capacity_mw"] for d in data)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Curated Entries", f"{len(data)}")
    with c2:
        st.metric("OSM Additional", f"{len(osm_rows)}")
    with c3:
        st.metric("Total Capacity Lost", f"{total_capacity:,} MW")
    with c4:
        st.metric("Countries", f"{len(set(d['country'] for d in data))}")

    # Map
    st.markdown("---")
    m = _make_dark_map(location=[45, 10], zoom=3)
    for d in combined:
        is_curated = d in data
        color = COLORS["shutdown"]
        radius = 7 if is_curated else 5
        name = d["name"]
        popup_html = (
            f'<div style="max-width:260px;">'
            f'<strong>{escape(name)}</strong><br/>'
            f'<span style="font-size:0.85rem;">Country: {escape(d.get("country", ""))}</span><br/>'
            f'<span style="font-size:0.85rem;">Shutdown: {escape(str(d.get("shutdown", "N/A")))}</span><br/>'
            f'<span style="font-size:0.85rem;">Capacity: {d.get("capacity_mw", 0):,} MW</span><br/>'
            f'<span style="font-size:0.85rem;">Type: {escape(d.get("type", "Unknown"))}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d.get("description", ""))}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.6, weight=1,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)
    _render_map(m)

    # Chart — capacity by plant
    sorted_data = sorted(data, key=lambda x: x["capacity_mw"], reverse=True)
    _dark_bar_chart(
        [d["name"][:25] for d in sorted_data if d["capacity_mw"] > 0],
        [d["capacity_mw"] for d in sorted_data if d["capacity_mw"] > 0],
        "Decommissioned Plant Capacity (MW)", "Plant", "Capacity (MW)",
        color="#8b97b0"
    )

    # Data table
    df = pd.DataFrame(combined)
    with st.expander(f"Full Data Table ({len(df)} plants)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "decommissioned_plants.csv", f"Download {len(df)} Plants (CSV)", "nuc_decom_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 9: NUCLEAR RESEARCH
# ═══════════════════════════════════════════════════════════════

def _render_research():
    st.markdown("#### Nuclear Research Facilities")
    st.markdown("Particle accelerators, fusion experiments, and research reactor complexes worldwide.")

    data = NUCLEAR_RESEARCH_FACILITIES

    # Stats
    fusion = sum(1 for d in data if "fusion" in d["type"].lower() or "tokamak" in d["type"].lower() or "stellarator" in d["type"].lower())
    accelerators = sum(1 for d in data if "accelerator" in d["type"].lower())
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Facilities Listed", f"{len(data)}")
    with c2:
        st.metric("Fusion Experiments", f"{fusion}")
    with c3:
        st.metric("Particle Accelerators", f"{accelerators}")
    with c4:
        st.metric("Countries", f"{len(set(d['country'].split('/')[0] for d in data))}")

    # Map
    st.markdown("---")
    type_colors = {
        "accelerator": "#06b6d4",
        "fusion": "#10b981",
        "tokamak": "#10b981",
        "stellarator": "#10b981",
        "research": "#14b8a6",
        "smr": "#a855f7",
    }
    m = _make_dark_map(location=[40, 10], zoom=3)
    for d in data:
        color = COLORS["research"]
        for key, clr in type_colors.items():
            if key in d["type"].lower():
                color = clr
                break
        popup_html = (
            f'<div style="max-width:280px;">'
            f'<strong>{escape(d["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Country: {escape(d["country"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Type: {escape(d["type"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Status: {escape(d["status"])}</span><br/>'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.7, weight=1,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)
    _render_map(m)

    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#06b6d4; font-size:0.8rem;">● Particle Accelerator</span>
        <span style="color:#10b981; font-size:0.8rem;">● Fusion Experiment</span>
        <span style="color:#14b8a6; font-size:0.8rem;">● Research Center</span>
        <span style="color:#a855f7; font-size:0.8rem;">● SMR / Advanced Reactor</span>
    </div>
    """, unsafe_allow_html=True)

    # Data table
    df = pd.DataFrame(data)
    with st.expander(f"Full Data Table ({len(df)} facilities)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "nuclear_research.csv", f"Download {len(df)} Facilities (CSV)", "nuc_research_dl")


# ═══════════════════════════════════════════════════════════════
# MODE 10: HIROSHIMA & NAGASAKI
# ═══════════════════════════════════════════════════════════════

def _render_hiroshima_nagasaki():
    st.markdown("#### Hiroshima & Nagasaki — 1945 Atomic Bombings")
    st.markdown("Ground zero sites, blast radii, peace memorials, and the legacy of the only wartime use of nuclear weapons.")

    data = HIROSHIMA_NAGASAKI

    # Stats
    hiroshima_deaths = "~140,000"
    nagasaki_deaths = "~70,000"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Hiroshima Deaths (by Dec 1945)", hiroshima_deaths)
    with c2:
        st.metric("Nagasaki Deaths (by Dec 1945)", nagasaki_deaths)
    with c3:
        st.metric("Little Boy Yield", "15 kt")
    with c4:
        st.metric("Fat Man Yield", "21 kt")

    # City selector
    city = st.radio("Select City", ["Both", "Hiroshima", "Nagasaki"], horizontal=True, key="nuc_hn_city")

    st.markdown("---")

    # Map
    if city == "Hiroshima":
        center = [34.3945, 132.4536]
        zoom = 14
        filtered = [d for d in data if "Hiroshima" in d["name"] or "hiroshima" in d["name"].lower()]
    elif city == "Nagasaki":
        center = [32.7737, 129.8632]
        zoom = 14
        filtered = [d for d in data if "Nagasaki" in d["name"] or "Urakami" in d["name"]]
    else:
        center = [34.0, 131.5]
        zoom = 7
        filtered = data

    m = _make_dark_map(location=center, zoom=zoom)

    # Draw blast radii for ground zeros
    ground_zeros = [d for d in filtered if d["yield_kt"] > 0]
    for gz in ground_zeros:
        # Inner fireball / total destruction (~1 km)
        folium.Circle(
            location=[gz["lat"], gz["lon"]], radius=1000,
            color="#dc2626", fill=True, fill_color="#dc2626",
            fill_opacity=0.15, weight=1,
            popup=f'{escape(gz["name"])}: ~1 km — total destruction zone',
        ).add_to(m)
        # Severe damage (~2.5 km)
        folium.Circle(
            location=[gz["lat"], gz["lon"]], radius=2500,
            color="#ef4444", fill=True, fill_color="#ef4444",
            fill_opacity=0.08, weight=1, dash_array="5,5",
            popup=f'{escape(gz["name"])}: ~2.5 km — severe blast damage',
        ).add_to(m)
        # Moderate damage / thermal burns (~5 km)
        folium.Circle(
            location=[gz["lat"], gz["lon"]], radius=5000,
            color="#f59e0b", fill=True, fill_color="#f59e0b",
            fill_opacity=0.05, weight=1, dash_array="10,5",
            popup=f'{escape(gz["name"])}: ~5 km — thermal burns, moderate damage',
        ).add_to(m)

    # Markers for all locations
    for d in filtered:
        is_ground_zero = d["yield_kt"] > 0
        is_memorial = d["event"] == "Memorial" or d["event"] == "Destruction & rebuilding"

        if is_ground_zero:
            color = "#dc2626"
            radius = 10
        elif is_memorial:
            color = COLORS["memorial"]
            radius = 7
        else:
            color = "#f59e0b"
            radius = 6

        deaths_line = f'<span style="font-size:0.85rem;">Deaths: {escape(d["deaths"])}</span><br/>' if d["deaths"] else ""
        yield_line = f'<span style="font-size:0.85rem;">Yield: {d["yield_kt"]} kt at {d["altitude_m"]}m altitude</span><br/>' if d["yield_kt"] > 0 else ""

        popup_html = (
            f'<div style="max-width:280px;">'
            f'<strong>{escape(d["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;">Event: {escape(d["event"])}</span><br/>'
            f'<span style="font-size:0.85rem;">Date: {escape(d["date"])}</span><br/>'
            f'{yield_line}'
            f'{deaths_line}'
            f'<span style="font-size:0.8rem; color:#8b97b0;">{escape(d["description"])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[d["lat"], d["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.8, weight=2,
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(m)

    _render_map(m, height=550)

    # Legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0;">
        <span style="color:#dc2626; font-size:0.8rem;">● Ground Zero / Total Destruction (~1 km)</span>
        <span style="color:#ef4444; font-size:0.8rem;">◯ Severe Blast Damage (~2.5 km)</span>
        <span style="color:#f59e0b; font-size:0.8rem;">◯ Thermal Burns / Moderate Damage (~5 km)</span>
        <span style="color:#f0abfc; font-size:0.8rem;">● Peace Memorials</span>
    </div>
    """, unsafe_allow_html=True)

    # Historical context
    st.markdown("---")
    st.markdown("##### Timeline")
    timeline = [
        ("1945-07-16", "Trinity Test", "First nuclear detonation at Alamogordo, New Mexico (20 kt)"),
        ("1945-07-26", "Potsdam Declaration", "Allies demand Japan's unconditional surrender"),
        ("1945-08-06 08:15", "Hiroshima", "B-29 Enola Gay drops 'Little Boy' (uranium-235, 15 kt). 80,000 killed instantly."),
        ("1945-08-09 11:02", "Nagasaki", "B-29 Bockscar drops 'Fat Man' (plutonium-239, 21 kt). 40,000 killed instantly. Originally targeted Kokura."),
        ("1945-08-15", "Japan surrenders", "Emperor Hirohito announces surrender. WWII ends."),
        ("1945-12-31", "Death toll", "Est. 210,000 dead from both bombings by year end (radiation sickness, burns, injuries)"),
        ("1950s-present", "Hibakusha", "Survivors (est. 650,000 total) suffered increased cancer rates. Japan provides medical support. ~113,000 survivors alive as of 2023."),
    ]
    for date, event, desc in timeline:
        st.markdown(
            f'<div style="margin-bottom:0.5rem;">'
            f'<span style="color:#06b6d4; font-weight:600;">{date}</span> — '
            f'<span style="color:#e8ecf4; font-weight:600;">{event}</span><br/>'
            f'<span style="color:#8b97b0; font-size:0.85rem;">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Data table
    df = pd.DataFrame(data)
    with st.expander(f"Full Data Table ({len(df)} locations)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    _csv_download(df, "hiroshima_nagasaki.csv", f"Download {len(df)} Locations (CSV)", "nuc_hn_dl")


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_nuclear_maps_tab():
    """Main render function for the Nuclear & Radiation Maps tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header red"><h4>☢️ Nuclear & Radiation Maps</h4>'
        '<p>Nuclear sites, disasters, test sites, reactors & 10 maps</p></div>',
        unsafe_allow_html=True,
    )

    # ── Mode Selector ──
    mode = st.selectbox(
        "Select Map Mode",
        list(MAP_MODES.keys()),
        key="nuc_mode",
        help="Choose a nuclear/radiation data layer to explore.",
    )

    # Description for selected mode
    st.markdown(
        f'<div style="color:#8b97b0; font-size:0.9rem; margin-bottom:1rem;">{MAP_MODES[mode]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Dispatch to mode renderer ──
    if mode == "Nuclear Power Plants":
        _render_power_plants()
    elif mode == "Nuclear Disasters":
        _render_disasters()
    elif mode == "Nuclear Test Sites":
        _render_test_sites()
    elif mode == "Uranium Mines":
        _render_uranium_mines()
    elif mode == "Nuclear Weapons States":
        _render_weapons_states()
    elif mode == "Radiation Monitoring":
        _render_radiation_monitoring()
    elif mode == "Nuclear Waste Storage":
        _render_waste_storage()
    elif mode == "Decommissioned Plants":
        _render_decommissioned()
    elif mode == "Nuclear Research":
        _render_research()
    elif mode == "Hiroshima & Nagasaki":
        _render_hiroshima_nagasaki()
