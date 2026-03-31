# -*- coding: utf-8 -*-
"""
TerraScout AI - Cemeteries & Memorials Maps Module
Explore famous cemeteries, war memorials, and burial traditions worldwide.

10 Map Modes:
  1. Famous Cemeteries
  2. War Memorials & Military Cemeteries
  3. Ancient Burial Sites
  4. Mausoleums & Tombs
  5. Celebrity Graves
  6. Holocaust Memorials
  7. Ossuaries & Bone Churches
  8. Unique Burial Traditions
  9. National Monuments
 10. Genocide Memorials
"""

import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import pandas as pd
import requests
import html as html_module


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODE_DESCRIPTIONS = {
    "Famous Cemeteries": (
        "World-renowned cemeteries known for their historical significance, "
        "stunning architecture, famous residents, and cultural importance. "
        "From the romantic tombs of Pere Lachaise to the solemn rows of "
        "Arlington National Cemetery."
    ),
    "War Memorials & Military Cemeteries": (
        "Battlefields, military cemeteries, and memorials honoring soldiers "
        "who fell in conflicts from World War I through modern engagements. "
        "Sites of remembrance across continents."
    ),
    "Ancient Burial Sites": (
        "Archaeological burial grounds spanning thousands of years of human "
        "history, from Neolithic passage tombs and Egyptian necropoli to "
        "Mesoamerican mounds and Bronze Age barrows."
    ),
    "Mausoleums & Tombs": (
        "Grand mausoleums, royal tombs, and monumental burial structures "
        "that represent the pinnacle of funerary architecture across "
        "civilizations and centuries."
    ),
    "Celebrity Graves": (
        "Final resting places of musicians, artists, writers, scientists, "
        "and cultural icons whose graves have become pilgrimage sites "
        "for fans and admirers worldwide."
    ),
    "Holocaust Memorials": (
        "Concentration camps, memorials, and museums preserving the memory "
        "of the six million Jews and millions of others murdered during "
        "the Holocaust (1933-1945)."
    ),
    "Ossuaries & Bone Churches": (
        "Chapels, crypts, and underground spaces decorated with or "
        "containing human skeletal remains -- from the Catacombs of Paris "
        "to the ornate Sedlec Ossuary in Kutna Hora."
    ),
    "Unique Burial Traditions": (
        "Extraordinary funerary customs from around the world: sky burials, "
        "cliff graves, fantasy coffins, hanging coffins, open-air cremation, "
        "and other practices that reflect diverse cultural beliefs about death."
    ),
    "National Monuments": (
        "Iconic national monuments, triumphal arches, and memorial structures "
        "that honor national heroes, founding ideals, and collective memory "
        "of nations across the globe."
    ),
    "Genocide Memorials": (
        "Sites of remembrance for victims of genocide and mass atrocities, "
        "from Rwanda and Cambodia to Armenia and Bosnia. These memorials "
        "serve as warnings and tributes to lost lives."
    ),
}

_MODE_COLORS = {
    "Famous Cemeteries": "#8b5cf6",
    "War Memorials & Military Cemeteries": "#ef4444",
    "Ancient Burial Sites": "#d97706",
    "Mausoleums & Tombs": "#06b6d4",
    "Celebrity Graves": "#ec4899",
    "Holocaust Memorials": "#6b7280",
    "Ossuaries & Bone Churches": "#78716c",
    "Unique Burial Traditions": "#10b981",
    "National Monuments": "#3b82f6",
    "Genocide Memorials": "#991b1b",
}

_MODE_ICONS = {
    "Famous Cemeteries": "\u26b0\ufe0f",
    "War Memorials & Military Cemeteries": "\u2694\ufe0f",
    "Ancient Burial Sites": "\U0001f3db\ufe0f",
    "Mausoleums & Tombs": "\U0001f3f0",
    "Celebrity Graves": "\u2b50",
    "Holocaust Memorials": "\U0001f56f\ufe0f",
    "Ossuaries & Bone Churches": "\U0001f480",
    "Unique Burial Traditions": "\U0001f30d",
    "National Monuments": "\U0001f3db\ufe0f",
    "Genocide Memorials": "\U0001f54a\ufe0f",
}

_CONTINENT_MAP = {
    "France": "Europe", "United Kingdom": "Europe",
    "United States": "North America", "Argentina": "South America",
    "Austria": "Europe", "Italy": "Europe", "Japan": "Asia",
    "Ireland": "Europe", "Australia": "Oceania", "Spain": "Europe",
    "Denmark": "Europe", "Hungary": "Europe", "Poland": "Europe",
    "Russia": "Europe", "India": "Asia", "Czech Republic": "Europe",
    "Germany": "Europe", "Netherlands": "Europe", "Belgium": "Europe",
    "Turkey": "Asia", "Philippines": "Asia", "Egypt": "Africa",
    "Thailand": "Asia", "Greece": "Europe", "Jordan": "Asia",
    "China": "Asia", "Bulgaria": "Europe", "Peru": "South America",
    "Palestine": "Asia", "Brazil": "South America",
    "South Korea": "Asia", "Namibia": "Africa",
    "South Africa": "Africa", "Mexico": "North America",
    "Serbia": "Europe", "Switzerland": "Europe", "Sweden": "Europe",
    "Portugal": "Europe", "Croatia": "Europe", "Israel": "Asia",
    "Uzbekistan": "Asia", "Iran": "Asia", "Vietnam": "Asia",
    "Morocco": "Africa", "Indonesia": "Asia", "Tibet/China": "Asia",
    "Norway": "Europe", "Madagascar": "Africa", "Ghana": "Africa",
    "Papua New Guinea": "Oceania", "Cambodia": "Asia",
    "Armenia": "Asia", "Bosnia and Herzegovina": "Europe",
    "Rwanda": "Africa", "Iraq (Kurdistan)": "Asia",
    "Ukraine": "Europe", "Singapore": "Asia",
    "Dominican Republic": "North America", "Jamaica": "North America",
    "Korea": "Asia", "Germany/Europe": "Europe",
}


# ---------------------------------------------------------------------------
# Data: Mode 1 -- Famous Cemeteries (25 entries)
# ---------------------------------------------------------------------------

def _famous_cemeteries():
    """Curated list of world-famous cemeteries."""
    return [
        {"name": "Pere Lachaise Cemetery", "city": "Paris", "country": "France", "lat": 48.8611, "lon": 2.3934, "founded": 1804, "area_ha": 44, "notable": "Jim Morrison, Oscar Wilde, Edith Piaf", "visitors_yr": "3.5 million"},
        {"name": "Highgate Cemetery", "city": "London", "country": "United Kingdom", "lat": 51.5672, "lon": -0.1469, "founded": 1839, "area_ha": 15, "notable": "Karl Marx, George Eliot, Douglas Adams", "visitors_yr": "100,000"},
        {"name": "Arlington National Cemetery", "city": "Arlington, VA", "country": "United States", "lat": 38.8783, "lon": -77.0687, "founded": 1864, "area_ha": 253, "notable": "JFK, Unknown Soldiers, military heroes", "visitors_yr": "3 million"},
        {"name": "Recoleta Cemetery", "city": "Buenos Aires", "country": "Argentina", "lat": -34.5878, "lon": -58.3935, "founded": 1822, "area_ha": 5.5, "notable": "Eva Peron, presidents, aristocracy", "visitors_yr": "500,000"},
        {"name": "Zentralfriedhof", "city": "Vienna", "country": "Austria", "lat": 48.1500, "lon": 16.4397, "founded": 1874, "area_ha": 240, "notable": "Beethoven, Brahms, Schubert, Strauss", "visitors_yr": "1 million"},
        {"name": "Staglieno Monumental Cemetery", "city": "Genoa", "country": "Italy", "lat": 44.4306, "lon": 8.9361, "founded": 1851, "area_ha": 33, "notable": "Giuseppe Mazzini, stunning sculptures", "visitors_yr": "200,000"},
        {"name": "Okunoin Cemetery", "city": "Koyasan", "country": "Japan", "lat": 34.2133, "lon": 135.6006, "founded": 819, "area_ha": 20, "notable": "Kobo Daishi, 200,000+ tombstones", "visitors_yr": "1 million"},
        {"name": "Glasnevin Cemetery", "city": "Dublin", "country": "Ireland", "lat": 53.3728, "lon": -6.2756, "founded": 1832, "area_ha": 50, "notable": "Michael Collins, Daniel O'Connell", "visitors_yr": "250,000"},
        {"name": "Sleepy Hollow Cemetery", "city": "Sleepy Hollow, NY", "country": "United States", "lat": 41.0887, "lon": -73.8618, "founded": 1849, "area_ha": 35, "notable": "Washington Irving, Andrew Carnegie", "visitors_yr": "150,000"},
        {"name": "Green-Wood Cemetery", "city": "Brooklyn, NY", "country": "United States", "lat": 40.6582, "lon": -73.9903, "founded": 1838, "area_ha": 193, "notable": "Leonard Bernstein, Boss Tweed, Basquiat", "visitors_yr": "300,000"},
        {"name": "Waverley Cemetery", "city": "Sydney", "country": "Australia", "lat": -33.9036, "lon": 151.2711, "founded": 1877, "area_ha": 16, "notable": "Henry Lawson, Dorothea Mackellar", "visitors_yr": "100,000"},
        {"name": "Cementerio de la Almudena", "city": "Madrid", "country": "Spain", "lat": 40.4133, "lon": -3.6500, "founded": 1884, "area_ha": 120, "notable": "Largest cemetery in Madrid", "visitors_yr": "300,000"},
        {"name": "Assistens Cemetery", "city": "Copenhagen", "country": "Denmark", "lat": 55.6911, "lon": 12.5508, "founded": 1760, "area_ha": 20, "notable": "Hans Christian Andersen, Kierkegaard", "visitors_yr": "200,000"},
        {"name": "Mount Auburn Cemetery", "city": "Cambridge, MA", "country": "United States", "lat": 42.3717, "lon": -71.1467, "founded": 1831, "area_ha": 69, "notable": "First garden cemetery in USA, Longfellow", "visitors_yr": "200,000"},
        {"name": "Kerepesi Cemetery", "city": "Budapest", "country": "Hungary", "lat": 47.4986, "lon": 19.0847, "founded": 1849, "area_ha": 56, "notable": "Lajos Kossuth, Janos Kadar", "visitors_yr": "150,000"},
        {"name": "Powazki Cemetery", "city": "Warsaw", "country": "Poland", "lat": 52.2564, "lon": 20.9778, "founded": 1790, "area_ha": 43, "notable": "Wladyslaw Reymont, Polish national heroes", "visitors_yr": "200,000"},
        {"name": "Novodevichy Cemetery", "city": "Moscow", "country": "Russia", "lat": 55.7253, "lon": 37.5561, "founded": 1898, "area_ha": 7.5, "notable": "Chekhov, Gogol, Khrushchev, Yeltsin", "visitors_yr": "300,000"},
        {"name": "South Park Street Cemetery", "city": "Kolkata", "country": "India", "lat": 22.5411, "lon": 88.3508, "founded": 1767, "area_ha": 3.2, "notable": "Oldest non-church cemetery in India", "visitors_yr": "50,000"},
        {"name": "La Chacarita Cemetery", "city": "Buenos Aires", "country": "Argentina", "lat": -34.5953, "lon": -58.4547, "founded": 1871, "area_ha": 95, "notable": "Carlos Gardel, Juan Peron", "visitors_yr": "200,000"},
        {"name": "Old Jewish Cemetery", "city": "Prague", "country": "Czech Republic", "lat": 50.0900, "lon": 14.4172, "founded": 1439, "area_ha": 1, "notable": "Rabbi Loew, 12,000+ layered tombstones", "visitors_yr": "500,000"},
        {"name": "Cimetiere du Montparnasse", "city": "Paris", "country": "France", "lat": 48.8383, "lon": 2.3264, "founded": 1824, "area_ha": 19, "notable": "Sartre, Beauvoir, Baudelaire, Beckett", "visitors_yr": "500,000"},
        {"name": "Bonaventure Cemetery", "city": "Savannah, GA", "country": "United States", "lat": 32.0497, "lon": -81.0467, "founded": 1846, "area_ha": 40, "notable": "Midnight in the Garden of Good and Evil", "visitors_yr": "150,000"},
        {"name": "Skogskyrkogarden", "city": "Stockholm", "country": "Sweden", "lat": 59.2781, "lon": 18.0964, "founded": 1920, "area_ha": 96, "notable": "UNESCO World Heritage, Greta Garbo", "visitors_yr": "100,000"},
        {"name": "Cemiterio dos Prazeres", "city": "Lisbon", "country": "Portugal", "lat": 38.7100, "lon": -9.1703, "founded": 1833, "area_ha": 11, "notable": "Ornate 19th century mausoleums", "visitors_yr": "80,000"},
        {"name": "Mirogoj Cemetery", "city": "Zagreb", "country": "Croatia", "lat": 45.8292, "lon": 15.9822, "founded": 1876, "area_ha": 28, "notable": "Arcaded walkways, multi-faith burials", "visitors_yr": "100,000"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 2 -- War Memorials & Military Cemeteries (20 entries)
# ---------------------------------------------------------------------------

def _war_memorials():
    """Curated list of war memorials and military cemeteries."""
    return [
        {"name": "Normandy American Cemetery", "city": "Colleville-sur-Mer", "country": "France", "lat": 49.3597, "lon": -0.8606, "war": "World War II", "burials": 9388, "year_est": 1944, "description": "Overlooking Omaha Beach, honors D-Day fallen"},
        {"name": "Tyne Cot Cemetery", "city": "Zonnebeke", "country": "Belgium", "lat": 50.8867, "lon": 2.9994, "war": "World War I", "burials": 11961, "year_est": 1917, "description": "Largest Commonwealth war cemetery in the world"},
        {"name": "Anzac Cove", "city": "Gallipoli", "country": "Turkey", "lat": 40.2375, "lon": 26.2828, "war": "World War I", "burials": 8700, "year_est": 1915, "description": "Site of 1915 Gallipoli Campaign landings"},
        {"name": "Yasukuni Shrine", "city": "Tokyo", "country": "Japan", "lat": 35.6939, "lon": 139.7436, "war": "Multiple conflicts", "burials": 2466532, "year_est": 1869, "description": "Honors Japanese war dead, controversial"},
        {"name": "Thiepval Memorial", "city": "Thiepval", "country": "France", "lat": 50.0517, "lon": 2.6856, "war": "World War I", "burials": 72337, "year_est": 1932, "description": "Names of missing soldiers of the Somme"},
        {"name": "Menin Gate Memorial", "city": "Ypres", "country": "Belgium", "lat": 50.8519, "lon": 2.8917, "war": "World War I", "burials": 54395, "year_est": 1927, "description": "Daily Last Post ceremony since 1928"},
        {"name": "Manila American Cemetery", "city": "Manila", "country": "Philippines", "lat": 14.5339, "lon": 121.0486, "war": "World War II", "burials": 17206, "year_est": 1948, "description": "Largest American overseas WWII cemetery"},
        {"name": "Volgograd Memorial (Mamayev Kurgan)", "city": "Volgograd", "country": "Russia", "lat": 48.7422, "lon": 44.5372, "war": "World War II", "burials": 34505, "year_est": 1967, "description": "Battle of Stalingrad, Motherland Calls statue"},
        {"name": "Korean War Veterans Memorial", "city": "Washington, DC", "country": "United States", "lat": 38.8878, "lon": -77.0478, "war": "Korean War", "burials": 0, "year_est": 1995, "description": "Steel soldier statues in patrol formation"},
        {"name": "Vietnam Veterans Memorial", "city": "Washington, DC", "country": "United States", "lat": 38.8912, "lon": -77.0478, "war": "Vietnam War", "burials": 0, "year_est": 1982, "description": "58,318 names on black granite wall"},
        {"name": "Douaumont Ossuary", "city": "Verdun", "country": "France", "lat": 49.2047, "lon": 5.4261, "war": "World War I", "burials": 130000, "year_est": 1932, "description": "Remains of soldiers from Battle of Verdun"},
        {"name": "Cassino War Cemetery", "city": "Cassino", "country": "Italy", "lat": 41.4889, "lon": 13.8103, "war": "World War II", "burials": 4271, "year_est": 1944, "description": "Battle of Monte Cassino fallen"},
        {"name": "El Alamein War Cemetery", "city": "El Alamein", "country": "Egypt", "lat": 30.8339, "lon": 28.9567, "war": "World War II", "burials": 7367, "year_est": 1942, "description": "North Africa campaign, Commonwealth dead"},
        {"name": "National Memorial Cemetery of the Pacific", "city": "Honolulu", "country": "United States", "lat": 21.3153, "lon": -157.8478, "war": "Multiple conflicts", "burials": 53000, "year_est": 1949, "description": "Punchbowl Crater, Pacific theater dead"},
        {"name": "Ari Burnu Cemetery", "city": "Gallipoli", "country": "Turkey", "lat": 40.2361, "lon": 26.2847, "war": "World War I", "burials": 252, "year_est": 1915, "description": "First landing site of ANZAC troops"},
        {"name": "Kanchanaburi War Cemetery", "city": "Kanchanaburi", "country": "Thailand", "lat": 14.0208, "lon": 99.5136, "war": "World War II", "burials": 6982, "year_est": 1943, "description": "Burma Railway (Death Railway) POW dead"},
        {"name": "Bayeux War Cemetery", "city": "Bayeux", "country": "France", "lat": 49.2747, "lon": -0.7019, "war": "World War II", "burials": 4648, "year_est": 1944, "description": "Largest WWII British cemetery in France"},
        {"name": "Soviet War Memorial (Treptower Park)", "city": "Berlin", "country": "Germany", "lat": 52.4867, "lon": 13.4694, "war": "World War II", "burials": 7000, "year_est": 1949, "description": "Massive Soviet soldier statue, Red Army memorial"},
        {"name": "Hiroshima Peace Memorial", "city": "Hiroshima", "country": "Japan", "lat": 34.3955, "lon": 132.4536, "war": "World War II", "burials": 0, "year_est": 1955, "description": "Atomic Bomb Dome, cenotaph for 200,000+ victims"},
        {"name": "Vimy Ridge Memorial", "city": "Vimy", "country": "France", "lat": 50.3797, "lon": 2.7739, "war": "World War I", "burials": 11285, "year_est": 1936, "description": "Canadian National Vimy Memorial, twin pylons"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 3 -- Ancient Burial Sites (20 entries)
# ---------------------------------------------------------------------------

def _ancient_burial_sites():
    """Curated list of ancient burial sites."""
    return [
        {"name": "Valley of the Kings", "city": "Luxor", "country": "Egypt", "lat": 25.7402, "lon": 32.6014, "period": "1539-1075 BCE", "civilization": "Ancient Egyptian", "description": "Tombs of pharaohs including Tutankhamun"},
        {"name": "Newgrange", "city": "County Meath", "country": "Ireland", "lat": 53.6947, "lon": -6.4756, "period": "3200 BCE", "civilization": "Neolithic", "description": "Passage tomb older than the Pyramids, solstice alignment"},
        {"name": "Terracotta Army", "city": "Xi'an", "country": "China", "lat": 34.3842, "lon": 109.2785, "period": "210 BCE", "civilization": "Qin Dynasty", "description": "8,000+ life-size warriors guarding Qin Shi Huang"},
        {"name": "Sutton Hoo", "city": "Woodbridge", "country": "United Kingdom", "lat": 52.0886, "lon": 1.3378, "period": "6th-7th century CE", "civilization": "Anglo-Saxon", "description": "Ship burial with treasure, likely King Raedwald"},
        {"name": "Carnac Stones", "city": "Carnac", "country": "France", "lat": 47.5950, "lon": -3.0783, "period": "4500-3300 BCE", "civilization": "Neolithic", "description": "Over 3,000 megalithic standing stones in rows"},
        {"name": "Mycenae Royal Tombs", "city": "Mycenae", "country": "Greece", "lat": 37.7308, "lon": 22.7564, "period": "1600-1100 BCE", "civilization": "Mycenaean", "description": "Treasury of Atreus, Mask of Agamemnon"},
        {"name": "Petra Royal Tombs", "city": "Petra", "country": "Jordan", "lat": 30.3285, "lon": 35.4444, "period": "4th century BCE", "civilization": "Nabataean", "description": "Rock-cut tombs including the Treasury (Al-Khazneh)"},
        {"name": "Saqqara Necropolis", "city": "Saqqara", "country": "Egypt", "lat": 29.8713, "lon": 31.2164, "period": "2686-2181 BCE", "civilization": "Ancient Egyptian", "description": "Step Pyramid of Djoser, oldest stone building"},
        {"name": "Tomb of the Leopards", "city": "Tarquinia", "country": "Italy", "lat": 42.2500, "lon": 11.7500, "period": "5th century BCE", "civilization": "Etruscan", "description": "Painted Etruscan burial chambers"},
        {"name": "Kerameikos Cemetery", "city": "Athens", "country": "Greece", "lat": 37.9783, "lon": 23.7186, "period": "3000 BCE-6th century CE", "civilization": "Ancient Greek", "description": "Ancient Athenian cemetery, elaborate grave stelae"},
        {"name": "Tumulus of Bougon", "city": "Bougon", "country": "France", "lat": 46.3753, "lon": -0.0678, "period": "4800 BCE", "civilization": "Neolithic", "description": "Among oldest known tumuli in the world"},
        {"name": "West Kennet Long Barrow", "city": "Avebury", "country": "United Kingdom", "lat": 51.4083, "lon": -1.8536, "period": "3650 BCE", "civilization": "Neolithic", "description": "One of largest Neolithic tombs in Britain"},
        {"name": "Knowth", "city": "County Meath", "country": "Ireland", "lat": 53.7017, "lon": -6.4917, "period": "3200 BCE", "civilization": "Neolithic", "description": "Passage tombs with largest collection of megalithic art"},
        {"name": "Jericho Tombs", "city": "Jericho", "country": "Palestine", "lat": 31.8592, "lon": 35.4606, "period": "9000 BCE", "civilization": "Neolithic", "description": "Among oldest known burial sites in the world"},
        {"name": "Skara Brae", "city": "Orkney", "country": "United Kingdom", "lat": 59.0486, "lon": -3.3417, "period": "3180-2500 BCE", "civilization": "Neolithic", "description": "Preserved settlement with nearby burial cairns"},
        {"name": "Sipan Royal Tombs", "city": "Lambayeque", "country": "Peru", "lat": -6.8000, "lon": -79.5833, "period": "100-700 CE", "civilization": "Moche", "description": "Lord of Sipan, richest unlooted burial in Americas"},
        {"name": "Varna Necropolis", "city": "Varna", "country": "Bulgaria", "lat": 43.2167, "lon": 27.9167, "period": "4600-4200 BCE", "civilization": "Copper Age", "description": "Oldest known gold artifacts found in graves"},
        {"name": "Cahokia Mounds", "city": "Collinsville, IL", "country": "United States", "lat": 38.6547, "lon": -90.0617, "period": "600-1400 CE", "civilization": "Mississippian", "description": "Monks Mound, largest earthen structure in Americas"},
        {"name": "Antequera Dolmens", "city": "Antequera", "country": "Spain", "lat": 37.0236, "lon": -4.5475, "period": "3800-2500 BCE", "civilization": "Neolithic", "description": "UNESCO megalithic tombs, Menga dolmen"},
        {"name": "Gobekli Tepe", "city": "Sanliurfa", "country": "Turkey", "lat": 37.2231, "lon": 38.9225, "period": "9500 BCE", "civilization": "Pre-Pottery Neolithic", "description": "Oldest known monumental site, possible ritual burial"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 4 -- Mausoleums & Tombs (20 entries)
# ---------------------------------------------------------------------------

def _mausoleums_tombs():
    """Curated list of famous mausoleums and tombs."""
    return [
        {"name": "Taj Mahal", "city": "Agra", "country": "India", "lat": 27.1751, "lon": 78.0421, "built": "1632-1653", "style": "Mughal", "entombed": "Mumtaz Mahal, Shah Jahan", "description": "White marble mausoleum, UNESCO World Heritage"},
        {"name": "Great Pyramid of Giza", "city": "Giza", "country": "Egypt", "lat": 29.9792, "lon": 31.1342, "built": "2560 BCE", "style": "Ancient Egyptian", "entombed": "Pharaoh Khufu", "description": "Last surviving Ancient Wonder of the World"},
        {"name": "Lenin Mausoleum", "city": "Moscow", "country": "Russia", "lat": 55.7539, "lon": 37.6208, "built": "1924-1930", "style": "Soviet Constructivist", "entombed": "Vladimir Lenin", "description": "Embalmed body on Red Square display"},
        {"name": "Humayun's Tomb", "city": "Delhi", "country": "India", "lat": 28.5933, "lon": 77.2507, "built": "1569-1572", "style": "Mughal", "entombed": "Emperor Humayun", "description": "Prototype for Taj Mahal, garden tomb"},
        {"name": "Shah-i-Zinda", "city": "Samarkand", "country": "Uzbekistan", "lat": 39.6622, "lon": 66.9875, "built": "9th-19th century", "style": "Timurid", "entombed": "Qutham ibn Abbas, Timurid royalty", "description": "Avenue of mausoleums with stunning tilework"},
        {"name": "Mausoleum of Halicarnassus (ruins)", "city": "Bodrum", "country": "Turkey", "lat": 37.0381, "lon": 27.4242, "built": "353 BCE", "style": "Greek Classical", "entombed": "King Mausolus", "description": "Ancient Wonder, origin of word mausoleum"},
        {"name": "Westminster Abbey", "city": "London", "country": "United Kingdom", "lat": 51.4993, "lon": -0.1273, "built": "960 CE onward", "style": "Gothic", "entombed": "17 monarchs, Newton, Hawking, Darwin", "description": "Royal coronation and burial church"},
        {"name": "Pantheon", "city": "Rome", "country": "Italy", "lat": 41.8986, "lon": 12.4769, "built": "125 CE", "style": "Roman", "entombed": "Raphael, Italian kings", "description": "Best preserved Roman temple, domed rotunda"},
        {"name": "Napoleon's Tomb (Les Invalides)", "city": "Paris", "country": "France", "lat": 48.8550, "lon": 2.3125, "built": "1840-1861", "style": "Neoclassical", "entombed": "Napoleon Bonaparte", "description": "Red quartzite sarcophagus in gilded dome church"},
        {"name": "Mausoleum of the First Qin Emperor", "city": "Xi'an", "country": "China", "lat": 34.3817, "lon": 109.2544, "built": "246-208 BCE", "style": "Qin Dynasty", "entombed": "Qin Shi Huang", "description": "Guarded by Terracotta Army, largely unexcavated"},
        {"name": "Imam Reza Shrine", "city": "Mashhad", "country": "Iran", "lat": 36.2890, "lon": 59.6158, "built": "818 CE onward", "style": "Islamic Persian", "entombed": "Imam Reza (8th Shia Imam)", "description": "Largest mosque by area, 25-30M pilgrims yearly"},
        {"name": "Mausoleum of Genghis Khan", "city": "Ordos", "country": "China", "lat": 39.5842, "lon": 109.8147, "built": "1954 (relocated)", "style": "Mongolian", "entombed": "Cenotaph (actual burial unknown)", "description": "Memorial to Genghis Khan, actual tomb never found"},
        {"name": "Grant's Tomb", "city": "New York City", "country": "United States", "lat": 40.8133, "lon": -73.9628, "built": "1897", "style": "Neoclassical", "entombed": "Ulysses S. Grant", "description": "Largest mausoleum in North America"},
        {"name": "Tomb of Cyrus", "city": "Pasargadae", "country": "Iran", "lat": 30.1942, "lon": 53.1672, "built": "530 BCE", "style": "Achaemenid", "entombed": "Cyrus the Great", "description": "Humble stone tomb of Persian Empire founder"},
        {"name": "Church of the Holy Sepulchre", "city": "Jerusalem", "country": "Israel", "lat": 31.7785, "lon": 35.2296, "built": "335 CE", "style": "Byzantine/Crusader", "entombed": "Site of Jesus' burial and resurrection", "description": "Holiest Christian site, Edicule shrine"},
        {"name": "Ho Chi Minh Mausoleum", "city": "Hanoi", "country": "Vietnam", "lat": 21.0369, "lon": 105.8350, "built": "1975", "style": "Soviet-inspired", "entombed": "Ho Chi Minh", "description": "Embalmed body of Vietnamese revolutionary leader"},
        {"name": "Mao Zedong Mausoleum", "city": "Beijing", "country": "China", "lat": 39.8997, "lon": 116.3908, "built": "1977", "style": "Soviet-inspired", "entombed": "Mao Zedong", "description": "Chairman Mao in Tiananmen Square"},
        {"name": "Anitkabir", "city": "Ankara", "country": "Turkey", "lat": 39.9254, "lon": 32.8369, "built": "1944-1953", "style": "Modern/Hittite-inspired", "entombed": "Mustafa Kemal Ataturk", "description": "Mausoleum of Turkey's founder"},
        {"name": "Saadian Tombs", "city": "Marrakech", "country": "Morocco", "lat": 31.6161, "lon": -7.9856, "built": "16th century", "style": "Moorish", "entombed": "Saadian dynasty rulers", "description": "Rediscovered 1917, ornate carved cedar and stucco"},
        {"name": "Bibi Ka Maqbara", "city": "Aurangabad", "country": "India", "lat": 19.9017, "lon": 75.3222, "built": "1660", "style": "Mughal", "entombed": "Dilras Banu Begum", "description": "Called Taj of the Deccan, replica of Taj Mahal"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 5 -- Celebrity Graves (20 entries)
# ---------------------------------------------------------------------------

def _celebrity_graves():
    """Curated list of famous celebrity graves."""
    return [
        {"name": "Jim Morrison", "cemetery": "Pere Lachaise", "city": "Paris", "country": "France", "lat": 48.8593, "lon": 2.3931, "died": 1971, "profession": "Rock musician (The Doors)", "visitors_note": "Most visited grave in Pere Lachaise"},
        {"name": "Elvis Presley", "cemetery": "Graceland", "city": "Memphis, TN", "country": "United States", "lat": 35.0477, "lon": -90.0263, "died": 1977, "profession": "Rock and roll icon", "visitors_note": "Meditation Garden, 600,000+ visitors yearly"},
        {"name": "Marilyn Monroe", "cemetery": "Westwood Village Memorial", "city": "Los Angeles", "country": "United States", "lat": 34.0584, "lon": -118.4410, "died": 1962, "profession": "Actress, icon", "visitors_note": "Crypt wall, flowers always present"},
        {"name": "Karl Marx", "cemetery": "Highgate Cemetery", "city": "London", "country": "United Kingdom", "lat": 51.5672, "lon": -0.1472, "died": 1883, "profession": "Philosopher, economist", "visitors_note": "Large bronze bust headstone"},
        {"name": "Oscar Wilde", "cemetery": "Pere Lachaise", "city": "Paris", "country": "France", "lat": 48.8611, "lon": 2.3928, "died": 1900, "profession": "Writer, playwright", "visitors_note": "Art Deco angel tomb, once covered in lipstick"},
        {"name": "Freddie Mercury", "cemetery": "Kensal Green (ashes)", "city": "London", "country": "United Kingdom", "lat": 51.5264, "lon": -0.2264, "died": 1991, "profession": "Rock musician (Queen)", "visitors_note": "Ashes scattered by Mary Austin, secret location"},
        {"name": "Bruce Lee", "cemetery": "Lake View Cemetery", "city": "Seattle", "country": "United States", "lat": 47.6317, "lon": -122.3158, "died": 1973, "profession": "Martial artist, actor", "visitors_note": "Buried beside son Brandon Lee"},
        {"name": "Jimi Hendrix", "cemetery": "Greenwood Memorial Park", "city": "Renton, WA", "country": "United States", "lat": 47.4639, "lon": -122.1836, "died": 1970, "profession": "Rock guitarist", "visitors_note": "Memorial with dome and granite columns"},
        {"name": "Bob Marley", "cemetery": "Bob Marley Mausoleum", "city": "Nine Mile", "country": "Jamaica", "lat": 18.3347, "lon": -77.1053, "died": 1981, "profession": "Reggae musician", "visitors_note": "Ethiopian Orthodox burial in childhood village"},
        {"name": "Edith Piaf", "cemetery": "Pere Lachaise", "city": "Paris", "country": "France", "lat": 48.8593, "lon": 2.3945, "died": 1963, "profession": "Singer (La Vie en Rose)", "visitors_note": "Always decorated with flowers and notes"},
        {"name": "Frida Kahlo", "cemetery": "Frida Kahlo Museum (ashes)", "city": "Mexico City", "country": "Mexico", "lat": 19.3550, "lon": -99.1628, "died": 1954, "profession": "Painter", "visitors_note": "Ashes in pre-Columbian urn at Casa Azul"},
        {"name": "Frank Sinatra", "cemetery": "Desert Memorial Park", "city": "Cathedral City, CA", "country": "United States", "lat": 33.7883, "lon": -116.4572, "died": 1998, "profession": "Singer, actor", "visitors_note": "Engraved: The Best Is Yet to Come"},
        {"name": "Princess Diana", "cemetery": "Althorp Estate", "city": "Northampton", "country": "United Kingdom", "lat": 52.2831, "lon": -1.0025, "died": 1997, "profession": "Royal, philanthropist", "visitors_note": "Buried on island in ornamental lake"},
        {"name": "Wolfgang Amadeus Mozart", "cemetery": "St. Marx Cemetery", "city": "Vienna", "country": "Austria", "lat": 48.1867, "lon": 16.3939, "died": 1791, "profession": "Composer", "visitors_note": "Common grave, exact location unknown"},
        {"name": "Ludwig van Beethoven", "cemetery": "Zentralfriedhof", "city": "Vienna", "country": "Austria", "lat": 48.1500, "lon": 16.4400, "died": 1827, "profession": "Composer", "visitors_note": "Ehrengrab (grave of honor) with golden lyre"},
        {"name": "Leonardo da Vinci", "cemetery": "Chapel of Saint-Hubert", "city": "Amboise", "country": "France", "lat": 47.4131, "lon": 0.9864, "died": 1519, "profession": "Polymath, artist", "visitors_note": "Chateau d'Amboise, remains moved to chapel"},
        {"name": "Charlie Chaplin", "cemetery": "Corsier-sur-Vevey Cemetery", "city": "Vevey", "country": "Switzerland", "lat": 46.4667, "lon": 6.8500, "died": 1977, "profession": "Actor, filmmaker", "visitors_note": "Body was famously stolen and recovered 1978"},
        {"name": "Nikola Tesla", "cemetery": "Tesla Museum (urn)", "city": "Belgrade", "country": "Serbia", "lat": 44.8050, "lon": 20.4700, "died": 1943, "profession": "Inventor, engineer", "visitors_note": "Golden urn containing ashes at museum"},
        {"name": "Andy Warhol", "cemetery": "St. John the Baptist Cemetery", "city": "Pittsburgh", "country": "United States", "lat": 40.4800, "lon": -79.8936, "died": 1987, "profession": "Pop artist", "visitors_note": "Webcam live-streams the grave 24/7"},
        {"name": "Albert Einstein", "cemetery": "Cremated (ashes scattered)", "city": "Princeton, NJ", "country": "United States", "lat": 40.3573, "lon": -74.6672, "died": 1955, "profession": "Physicist", "visitors_note": "Ashes scattered in Delaware River"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 6 -- Holocaust Memorials (20 entries)
# ---------------------------------------------------------------------------

def _holocaust_memorials():
    """Curated list of Holocaust memorials and sites."""
    return [
        {"name": "Auschwitz-Birkenau", "city": "Oswiecim", "country": "Poland", "lat": 50.0343, "lon": 19.1781, "type": "Concentration/Extermination camp", "year_est": 1947, "victims": "1.1 million", "description": "Largest Nazi death camp, UNESCO World Heritage"},
        {"name": "Yad Vashem", "city": "Jerusalem", "country": "Israel", "lat": 31.7741, "lon": 35.1753, "type": "Memorial and museum", "year_est": 1953, "victims": "6 million commemorated", "description": "World Holocaust Remembrance Center, Hall of Names"},
        {"name": "Memorial to the Murdered Jews of Europe", "city": "Berlin", "country": "Germany", "lat": 52.5139, "lon": 13.3789, "type": "Memorial", "year_est": 2005, "victims": "6 million commemorated", "description": "2,711 concrete stelae by Peter Eisenman"},
        {"name": "Dachau Concentration Camp", "city": "Dachau", "country": "Germany", "lat": 48.2700, "lon": 11.4681, "type": "Concentration camp memorial", "year_est": 1965, "victims": "41,500+", "description": "First Nazi concentration camp, model for others"},
        {"name": "Anne Frank House", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3752, "lon": 4.8840, "type": "Museum/Memorial", "year_est": 1960, "victims": "Anne Frank family", "description": "Secret annex where Anne Frank wrote her diary"},
        {"name": "Treblinka Extermination Camp", "city": "Treblinka", "country": "Poland", "lat": 52.6313, "lon": 22.0494, "type": "Extermination camp memorial", "year_est": 1964, "victims": "700,000-900,000", "description": "17,000 stones represent destroyed communities"},
        {"name": "Sachsenhausen", "city": "Oranienburg", "country": "Germany", "lat": 52.7664, "lon": 13.2631, "type": "Concentration camp memorial", "year_est": 1961, "victims": "30,000+", "description": "Model camp used to train SS officers"},
        {"name": "Buchenwald", "city": "Weimar", "country": "Germany", "lat": 51.0214, "lon": 11.2483, "type": "Concentration camp memorial", "year_est": 1958, "victims": "56,000+", "description": "Liberated by US forces in 1945"},
        {"name": "Mauthausen Memorial", "city": "Mauthausen", "country": "Austria", "lat": 48.2569, "lon": 14.5014, "type": "Concentration camp memorial", "year_est": 1949, "victims": "90,000+", "description": "Granite quarry, Stairs of Death"},
        {"name": "US Holocaust Memorial Museum", "city": "Washington, DC", "country": "United States", "lat": 38.8868, "lon": -77.0328, "type": "Museum", "year_est": 1993, "victims": "6 million commemorated", "description": "Major US museum and research center"},
        {"name": "Terezin Memorial", "city": "Terezin", "country": "Czech Republic", "lat": 50.5103, "lon": 14.1503, "type": "Ghetto/camp memorial", "year_est": 1947, "victims": "33,000+", "description": "Theresienstadt ghetto and Small Fortress"},
        {"name": "Bergen-Belsen Memorial", "city": "Lohheide", "country": "Germany", "lat": 52.7581, "lon": 9.9064, "type": "Concentration camp memorial", "year_est": 1952, "victims": "70,000+", "description": "Where Anne Frank died, mass graves site"},
        {"name": "Majdanek State Museum", "city": "Lublin", "country": "Poland", "lat": 51.2333, "lon": 22.6000, "type": "Extermination camp memorial", "year_est": 1944, "victims": "78,000+", "description": "Best preserved camp, dome mausoleum of ashes"},
        {"name": "Ravensbrueck Memorial", "city": "Furstenberg", "country": "Germany", "lat": 53.1903, "lon": 13.1689, "type": "Concentration camp memorial", "year_est": 1959, "victims": "30,000-50,000", "description": "Largest women's concentration camp"},
        {"name": "Sobibor Extermination Camp", "city": "Sobibor", "country": "Poland", "lat": 51.4500, "lon": 23.6000, "type": "Extermination camp memorial", "year_est": 1965, "victims": "170,000-250,000", "description": "Site of famous prisoner uprising in 1943"},
        {"name": "Drancy Internment Camp Memorial", "city": "Drancy", "country": "France", "lat": 48.9167, "lon": 2.4500, "type": "Internment camp memorial", "year_est": 2012, "victims": "67,400 deported", "description": "Transit camp for French Jews, Shoah Memorial"},
        {"name": "Stolpersteine (Stumbling Stones)", "city": "Berlin (and 1,200+ cities)", "country": "Germany/Europe", "lat": 52.5200, "lon": 13.4050, "type": "Distributed memorial", "year_est": 1992, "victims": "100,000+ stones", "description": "Brass cobblestones at last known victim addresses"},
        {"name": "Belzec Extermination Camp", "city": "Belzec", "country": "Poland", "lat": 50.3722, "lon": 23.4583, "type": "Extermination camp memorial", "year_est": 2004, "victims": "434,000-600,000", "description": "Field of slag covers mass graves"},
        {"name": "Plaszow Concentration Camp", "city": "Krakow", "country": "Poland", "lat": 50.0306, "lon": 19.9617, "type": "Concentration camp memorial", "year_est": 2002, "victims": "8,000+", "description": "Featured in Schindler's List"},
        {"name": "Natzweiler-Struthof", "city": "Natzwiller", "country": "France", "lat": 48.4528, "lon": 7.2528, "type": "Concentration camp memorial", "year_est": 1960, "victims": "22,000+", "description": "Only concentration camp on French soil (Alsace)"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 7 -- Ossuaries & Bone Churches (15 entries)
# ---------------------------------------------------------------------------

def _ossuaries_bone_churches():
    """Curated list of ossuaries and bone churches."""
    return [
        {"name": "Sedlec Ossuary (Bone Church)", "city": "Kutna Hora", "country": "Czech Republic", "lat": 49.9614, "lon": 15.2881, "bones_count": "40,000-70,000", "period": "14th century onward", "description": "Chandelier of every human bone, coat of arms in bones"},
        {"name": "Capuchin Crypt", "city": "Rome", "country": "Italy", "lat": 41.9047, "lon": 12.4892, "bones_count": "3,700", "period": "1631-1870", "description": "Five chapels decorated with Capuchin monk bones"},
        {"name": "Catacombs of Paris", "city": "Paris", "country": "France", "lat": 48.8339, "lon": 2.3322, "bones_count": "6,000,000+", "period": "1786 onward", "description": "200 miles of tunnels, walls of skulls and femurs"},
        {"name": "Chapel of Bones (Capela dos Ossos)", "city": "Evora", "country": "Portugal", "lat": 38.5697, "lon": -7.9075, "bones_count": "5,000", "period": "16th century", "description": "Inscription: We bones here await yours"},
        {"name": "San Bernardino alle Ossa", "city": "Milan", "country": "Italy", "lat": 41.8836, "lon": 12.4575, "bones_count": "Unknown (thousands)", "period": "1210 onward", "description": "Ossuary chapel adjacent to church, skull walls"},
        {"name": "Skull Tower (Cele Kula)", "city": "Nis", "country": "Serbia", "lat": 43.3203, "lon": 21.9253, "bones_count": "952 skulls (originally)", "period": "1809", "description": "Ottoman tower built from Serbian rebel skulls"},
        {"name": "Hallstatt Charnel House", "city": "Hallstatt", "country": "Austria", "lat": 47.5625, "lon": 13.6467, "bones_count": "1,200+ skulls", "period": "12th century onward", "description": "Painted skulls with names and floral designs"},
        {"name": "Czermna Skull Chapel", "city": "Kudowa-Zdroj", "country": "Poland", "lat": 50.4444, "lon": 16.2450, "bones_count": "3,000 (24,000 below)", "period": "1776", "description": "Walls and ceiling covered with skulls, Silesian Wars"},
        {"name": "Santa Maria della Concezione", "city": "Rome", "country": "Italy", "lat": 41.9050, "lon": 12.4895, "bones_count": "4,000", "period": "17th century", "description": "Capuchin monks arranged in ornate patterns"},
        {"name": "Douaumont Ossuary", "city": "Verdun", "country": "France", "lat": 49.2047, "lon": 5.4261, "bones_count": "130,000", "period": "1932", "description": "WWI soldiers from Battle of Verdun, visible windows"},
        {"name": "Ossuary of Wamba", "city": "Wamba", "country": "Spain", "lat": 41.7000, "lon": -4.9167, "bones_count": "3,000+", "period": "13th-18th century", "description": "Inside Romanesque church of Santa Maria"},
        {"name": "Fontanelle Cemetery", "city": "Naples", "country": "Italy", "lat": 40.8567, "lon": 14.2406, "bones_count": "40,000+", "period": "17th century", "description": "Cave ossuary in tufa quarry, cult of adopted skulls"},
        {"name": "Brno Ossuary", "city": "Brno", "country": "Czech Republic", "lat": 49.1917, "lon": 16.6078, "bones_count": "50,000+", "period": "17th century", "description": "Second largest ossuary in Europe after Paris"},
        {"name": "Opdas Burial Cave", "city": "Benguet", "country": "Philippines", "lat": 16.4167, "lon": 120.5833, "bones_count": "Unknown", "period": "Pre-colonial", "description": "Ibaloi mummy caves with stacked coffins and bones"},
        {"name": "Church of All Saints Ossuary", "city": "Oppenheim", "country": "Germany", "lat": 49.8553, "lon": 8.3586, "bones_count": "20,000+", "period": "15th century", "description": "Underground charnel house beneath Gothic church"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 8 -- Unique Burial Traditions (15 entries)
# ---------------------------------------------------------------------------

def _unique_burial_traditions():
    """Curated list of unique burial traditions worldwide."""
    return [
        {"name": "Toraja Cliff Graves", "city": "Tana Toraja", "country": "Indonesia", "lat": -3.0733, "lon": 119.8419, "tradition": "Cliff burial with tau-tau effigies", "culture": "Torajan", "description": "Coffins placed in cliff face, wooden effigies guard the dead"},
        {"name": "Sky Burial Sites (Drigungtil)", "city": "Lhasa region", "country": "Tibet/China", "lat": 29.7881, "lon": 91.5800, "tradition": "Sky burial (jhator)", "culture": "Tibetan Buddhist", "description": "Bodies offered to vultures as act of generosity"},
        {"name": "Oseberg Viking Ship Burial", "city": "Tonsberg", "country": "Norway", "lat": 59.2775, "lon": 10.3856, "tradition": "Ship burial", "culture": "Viking/Norse", "description": "9th century ship burial of two women with grave goods"},
        {"name": "Hanging Coffins of Sagada", "city": "Sagada", "country": "Philippines", "lat": 17.0833, "lon": 121.0167, "tradition": "Hanging coffins on cliff face", "culture": "Igorot", "description": "Coffins nailed to cliff walls, closer to heaven"},
        {"name": "Famadihana Ceremony Sites", "city": "Ambositra", "country": "Madagascar", "lat": -20.5300, "lon": 47.2400, "tradition": "Turning of the bones", "culture": "Malagasy", "description": "Exhume ancestors, rewrap in fresh cloth, dance with them"},
        {"name": "Varanasi Burning Ghats", "city": "Varanasi", "country": "India", "lat": 25.3109, "lon": 83.0107, "tradition": "Open-air cremation on Ganges", "culture": "Hindu", "description": "Manikarnika Ghat, cremation fires burn 24/7 for centuries"},
        {"name": "Tower of Silence", "city": "Mumbai", "country": "India", "lat": 18.9547, "lon": 72.8056, "tradition": "Excarnation (exposure to vultures)", "culture": "Zoroastrian/Parsi", "description": "Circular towers where dead are placed for scavenger birds"},
        {"name": "Cappadocia Cave Tombs", "city": "Goreme", "country": "Turkey", "lat": 38.6431, "lon": 34.8289, "tradition": "Rock-cut tombs in fairy chimneys", "culture": "Early Christian/Byzantine", "description": "Carved burial chambers in volcanic rock formations"},
        {"name": "Trunyan Village Cemetery", "city": "Bali", "country": "Indonesia", "lat": -8.2500, "lon": 115.4167, "tradition": "Open-air decomposition under banyan", "culture": "Bali Aga", "description": "Bodies placed in bamboo cages, tree neutralizes odor"},
        {"name": "Merina Royal Tombs", "city": "Ambohimanga", "country": "Madagascar", "lat": -18.7606, "lon": 47.5631, "tradition": "Royal ancestral tomb complex", "culture": "Merina", "description": "UNESCO site, sacred hill with royal burial traditions"},
        {"name": "Kutai Kartanegara Floating Graves", "city": "Tenggarong", "country": "Indonesia", "lat": -0.4167, "lon": 116.9833, "tradition": "River-based burial", "culture": "Dayak/Kutai", "description": "Burial structures along Mahakam River waterways"},
        {"name": "Fantasy Coffins of Ga People", "city": "Accra", "country": "Ghana", "lat": 5.5560, "lon": -0.1969, "tradition": "Custom-shaped fantasy coffins", "culture": "Ga", "description": "Coffins shaped as airplanes, fish, cars, Coca-Cola bottles"},
        {"name": "Jade Burial Suits Museum", "city": "Xuzhou", "country": "China", "lat": 34.2600, "lon": 117.1839, "tradition": "Jade burial suits", "culture": "Han Dynasty", "description": "Deceased sewn into suits of jade pieces with gold wire"},
        {"name": "Catacomb Saints Display", "city": "Waldsassen", "country": "Germany", "lat": 50.0058, "lon": 12.3039, "tradition": "Jeweled skeleton saints", "culture": "Roman Catholic", "description": "Skeletons decorated with jewels, displayed in church"},
        {"name": "Lihir Island Shark Calling", "city": "Lihir Island", "country": "Papua New Guinea", "lat": -3.1167, "lon": 152.6333, "tradition": "Sea burial with shark calling", "culture": "Melanesian", "description": "Bodies returned to ocean, sharks called as spiritual escorts"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 9 -- National Monuments (20 entries)
# ---------------------------------------------------------------------------

def _national_monuments():
    """Curated list of national monuments and memorials."""
    return [
        {"name": "Lincoln Memorial", "city": "Washington, DC", "country": "United States", "lat": 38.8893, "lon": -77.0502, "year_built": 1922, "type": "Presidential memorial", "description": "Seated Lincoln statue, I Have a Dream speech site"},
        {"name": "Statue of Liberty", "city": "New York City", "country": "United States", "lat": 40.6892, "lon": -74.0445, "year_built": 1886, "type": "National monument", "description": "Gift from France, symbol of freedom and democracy"},
        {"name": "Christ the Redeemer", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9519, "lon": -43.2105, "year_built": 1931, "type": "Religious monument", "description": "30m Art Deco statue atop Corcovado mountain"},
        {"name": "The Motherland Calls", "city": "Volgograd", "country": "Russia", "lat": 48.7422, "lon": 44.5372, "year_built": 1967, "type": "War memorial", "description": "85m statue, Battle of Stalingrad on Mamayev Kurgan"},
        {"name": "Mount Rushmore", "city": "Keystone, SD", "country": "United States", "lat": 43.8791, "lon": -103.4591, "year_built": 1941, "type": "National memorial", "description": "Four presidents carved into granite mountain face"},
        {"name": "Gateway of India", "city": "Mumbai", "country": "India", "lat": 18.9220, "lon": 72.8347, "year_built": 1924, "type": "Triumphal arch", "description": "Commemorates King George V's visit to India"},
        {"name": "Brandenburg Gate", "city": "Berlin", "country": "Germany", "lat": 52.5163, "lon": 13.3777, "year_built": 1791, "type": "Triumphal gate", "description": "Symbol of German reunification, neoclassical gate"},
        {"name": "Arc de Triomphe", "city": "Paris", "country": "France", "lat": 48.8738, "lon": 2.2950, "year_built": 1836, "type": "Triumphal arch", "description": "Tomb of Unknown Soldier, eternal flame since 1923"},
        {"name": "Angel of Independence", "city": "Mexico City", "country": "Mexico", "lat": 19.4270, "lon": -99.1677, "year_built": 1910, "type": "Victory column", "description": "Golden winged Victoria, heroes interred below"},
        {"name": "Cenotaph", "city": "London", "country": "United Kingdom", "lat": 51.5027, "lon": -0.1268, "year_built": 1920, "type": "War memorial", "description": "Empty tomb honoring all war dead, Remembrance service"},
        {"name": "War Memorial of Korea", "city": "Seoul", "country": "South Korea", "lat": 37.5347, "lon": 126.9772, "year_built": 1994, "type": "War memorial museum", "description": "Museum for Korean War and military history"},
        {"name": "National War Memorial (India)", "city": "New Delhi", "country": "India", "lat": 28.6129, "lon": 77.2295, "year_built": 2019, "type": "War memorial", "description": "Names of 26,466 soldiers since independence"},
        {"name": "ANZAC War Memorial", "city": "Sydney", "country": "Australia", "lat": -33.8781, "lon": 151.2114, "year_built": 1934, "type": "War memorial", "description": "Art Deco memorial in Hyde Park for WWI"},
        {"name": "Voortrekker Monument", "city": "Pretoria", "country": "South Africa", "lat": -25.7764, "lon": 28.1756, "year_built": 1949, "type": "Heritage monument", "description": "Honors Voortrekker pioneers, massive granite structure"},
        {"name": "Jose Rizal Monument", "city": "Manila", "country": "Philippines", "lat": 14.5831, "lon": 120.9778, "year_built": 1913, "type": "National hero memorial", "description": "Honors national hero, Luneta Park execution site"},
        {"name": "Vimy Memorial", "city": "Vimy", "country": "France", "lat": 50.3797, "lon": 2.7739, "year_built": 1936, "type": "War memorial", "description": "Canadian national WWI memorial, twin white pylons"},
        {"name": "Scottish National War Memorial", "city": "Edinburgh", "country": "United Kingdom", "lat": 55.9486, "lon": -3.2008, "year_built": 1927, "type": "War memorial", "description": "In Edinburgh Castle, honors Scottish war dead"},
        {"name": "India Gate", "city": "New Delhi", "country": "India", "lat": 28.6131, "lon": 77.2297, "year_built": 1931, "type": "War memorial arch", "description": "42m arch honoring 70,000 Indian soldiers of WWI"},
        {"name": "Heroes' Acre", "city": "Windhoek", "country": "Namibia", "lat": -22.6181, "lon": 17.0786, "year_built": 2002, "type": "National memorial", "description": "Honors independence struggle heroes"},
        {"name": "Mausoleo de la Patria", "city": "Santo Domingo", "country": "Dominican Republic", "lat": 18.4719, "lon": -69.8922, "year_built": 1976, "type": "National mausoleum", "description": "Entombs founding fathers Duarte, Sanchez, Mella"},
    ]


# ---------------------------------------------------------------------------
# Data: Mode 10 -- Genocide Memorials (15 entries)
# ---------------------------------------------------------------------------

def _genocide_memorials():
    """Curated list of genocide memorials worldwide."""
    return [
        {"name": "Kigali Genocide Memorial", "city": "Kigali", "country": "Rwanda", "lat": -1.9378, "lon": 30.0600, "event": "Rwandan Genocide (1994)", "victims": "250,000+ buried here", "year_est": 2004, "description": "Burial site for 250,000 victims, museum and gardens"},
        {"name": "Killing Fields (Choeung Ek)", "city": "Phnom Penh", "country": "Cambodia", "lat": 11.4842, "lon": 104.9011, "event": "Cambodian Genocide (1975-1979)", "victims": "8,000+ exhumed", "year_est": 1988, "description": "Mass grave site, Buddhist stupa filled with skulls"},
        {"name": "Armenian Genocide Memorial", "city": "Yerevan", "country": "Armenia", "lat": 40.1847, "lon": 44.4903, "event": "Armenian Genocide (1915-1923)", "victims": "1.5 million commemorated", "year_est": 1967, "description": "Eternal flame, 12 slabs for lost provinces"},
        {"name": "Srebrenica Memorial (Potocari)", "city": "Srebrenica", "country": "Bosnia and Herzegovina", "lat": 44.1594, "lon": 19.2039, "event": "Bosnian Genocide (1995)", "victims": "8,372", "year_est": 2003, "description": "Cemetery and memorial for Srebrenica massacre"},
        {"name": "Tuol Sleng Genocide Museum (S-21)", "city": "Phnom Penh", "country": "Cambodia", "lat": 11.5494, "lon": 104.9172, "event": "Cambodian Genocide (1975-1979)", "victims": "12,000-20,000 detained", "year_est": 1980, "description": "Former school turned Khmer Rouge torture prison"},
        {"name": "Murambi Genocide Memorial", "city": "Murambi", "country": "Rwanda", "lat": -2.4756, "lon": 29.6314, "event": "Rwandan Genocide (1994)", "victims": "45,000-50,000", "year_est": 2011, "description": "Preserved lime-covered bodies on display"},
        {"name": "Halabja Monument", "city": "Halabja", "country": "Iraq (Kurdistan)", "lat": 35.1778, "lon": 45.9833, "event": "Anfal Genocide (1988)", "victims": "5,000+", "year_est": 2003, "description": "Memorial for chemical weapons attack on Kurds"},
        {"name": "Nyamata Church Memorial", "city": "Nyamata", "country": "Rwanda", "lat": -2.2833, "lon": 30.0833, "event": "Rwandan Genocide (1994)", "victims": "10,000+", "year_est": 1997, "description": "Church where Tutsis were massacred"},
        {"name": "Nanjing Massacre Memorial Hall", "city": "Nanjing", "country": "China", "lat": 32.0167, "lon": 118.7667, "event": "Nanjing Massacre (1937)", "victims": "300,000+", "year_est": 1985, "description": "Hall over mass grave, Japanese atrocities documented"},
        {"name": "Herero and Nama Genocide Memorial", "city": "Windhoek", "country": "Namibia", "lat": -22.5667, "lon": 17.0833, "event": "Herero and Nama Genocide (1904-1908)", "victims": "65,000-100,000", "year_est": 2014, "description": "First genocide of 20th century by German colonizers"},
        {"name": "Holodomor Memorial", "city": "Kyiv", "country": "Ukraine", "lat": 50.4417, "lon": 30.5256, "event": "Holodomor (1932-1933)", "victims": "3.5-7.5 million", "year_est": 2008, "description": "Candle of Memory for Soviet famine victims"},
        {"name": "Memorial de la Shoah", "city": "Paris", "country": "France", "lat": 48.8544, "lon": 2.3556, "event": "Holocaust (1941-1945)", "victims": "76,000 French Jews", "year_est": 2005, "description": "Wall of Names lists 76,000 deported French Jews"},
        {"name": "Genocide Memorial Church (Ntarama)", "city": "Ntarama", "country": "Rwanda", "lat": -2.2500, "lon": 30.0500, "event": "Rwandan Genocide (1994)", "victims": "5,000+", "year_est": 1995, "description": "Preserved church where thousands sought refuge"},
        {"name": "Kranji War Memorial", "city": "Singapore", "country": "Singapore", "lat": 1.4261, "lon": 103.7619, "event": "Sook Ching Massacre (1942)", "victims": "25,000-50,000", "year_est": 1946, "description": "Memorial for war dead including Sook Ching victims"},
        {"name": "ESMA Memory Site", "city": "Buenos Aires", "country": "Argentina", "lat": -34.5436, "lon": -58.4631, "event": "Dirty War (1976-1983)", "victims": "30,000 disappeared", "year_est": 2004, "description": "Former Navy school, memory site for the disappeared"},
    ]


# ---------------------------------------------------------------------------
# Overpass API nearby search (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _fetch_nearby_pois(lat, lon, radius_m=2000):
    """
    Fetch nearby points of interest around a location using Overpass API.
    Returns a list of dicts with name, type, lat, lon.
    Useful for enriching any selected cemetery/memorial with local context.
    """
    query = f"""
    [out:json][timeout:15];
    (
      node["tourism"](around:{radius_m},{lat},{lon});
      node["historic"](around:{radius_m},{lat},{lon});
      node["amenity"="place_of_worship"](around:{radius_m},{lat},{lon});
    );
    out body 50;
    """
    try:
        resp = requests.get(
            "https://overpass-api.de/api/interpreter",
            params={"data": query},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        elements = resp.json().get("elements", [])
        results = []
        for el in elements:
            name = el.get("tags", {}).get("name", "")
            if not name:
                continue
            poi_type = (
                el.get("tags", {}).get("tourism", "")
                or el.get("tags", {}).get("historic", "")
                or el.get("tags", {}).get("amenity", "")
            )
            results.append({
                "name": name,
                "type": poi_type,
                "lat": el.get("lat", 0),
                "lon": el.get("lon", 0),
            })
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------

def _build_map(df, mode, color):
    """Build a dark-themed folium map with circle markers for the given data."""
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="CartoDB dark_matter",
    )

    icon_char = _MODE_ICONS.get(mode, "\u26b0\ufe0f")

    for _, row in df.iterrows():
        name_safe = html_module.escape(str(row.get("name", "")))

        # --- Build rich popup ---
        popup_lines = [
            f"<div style='min-width:240px;max-width:340px;font-family:sans-serif;"
            f"font-size:12px;color:#e8ecf4;background:#1a2235;padding:12px;"
            f"border-radius:8px;border:1px solid {color};'>",
            f"<b style='color:{color};font-size:14px;'>"
            f"{icon_char} {name_safe}</b><br><hr style='border-color:{color}40;margin:6px 0;'>",
        ]

        skip_cols = {"lat", "lon", "name"}
        for col in df.columns:
            if col in skip_cols:
                continue
            val = row.get(col, "")
            if pd.notna(val) and str(val).strip():
                col_label = html_module.escape(col.replace("_", " ").title())
                val_safe = html_module.escape(str(val))
                popup_lines.append(
                    f"<span style='color:#8b97b0;'>{col_label}:</span> "
                    f"<span style='color:#e8ecf4;'>{val_safe}</span><br>"
                )

        # Add coordinates footer
        lat_s = html_module.escape(f"{row['lat']:.4f}")
        lon_s = html_module.escape(f"{row['lon']:.4f}")
        popup_lines.append(
            f"<hr style='border-color:{color}40;margin:6px 0;'>"
            f"<span style='color:#5a6580;font-size:10px;'>"
            f"Coords: {lat_s}, {lon_s}</span>"
        )
        popup_lines.append("</div>")

        popup_html = "".join(popup_lines)

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=360),
            tooltip=f"{icon_char} {name_safe}",
        ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Stats renderer
# ---------------------------------------------------------------------------

def _render_stats(df, mode):
    """Render a row of metric cards based on the current mode data."""
    num_sites = len(df)

    if mode == "Famous Cemeteries":
        countries = df["country"].nunique()
        oldest = df["founded"].min() if "founded" in df.columns else "N/A"
        continents = df["country"].apply(_continent_from_country).nunique()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Cemeteries", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Oldest Founded", oldest)
        col4.metric("Continents", continents)

    elif mode == "War Memorials & Military Cemeteries":
        total_burials = df["burials"].sum() if "burials" in df.columns else 0
        countries = df["country"].nunique()
        wars = df["war"].nunique() if "war" in df.columns else 0
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Memorials", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Total Burials/Names", f"{total_burials:,}")
        col4.metric("Conflicts Covered", wars)

    elif mode == "Ancient Burial Sites":
        countries = df["country"].nunique()
        civs = df["civilization"].nunique() if "civilization" in df.columns else 0
        oldest_period = df["period"].iloc[0] if "period" in df.columns and len(df) > 0 else "N/A"
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sites", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Civilizations", civs)
        col4.metric("Oldest Period", oldest_period)

    elif mode == "Mausoleums & Tombs":
        countries = df["country"].nunique()
        styles = df["style"].nunique() if "style" in df.columns else 0
        continents = df["country"].apply(_continent_from_country).nunique()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Mausoleums", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Architectural Styles", styles)
        col4.metric("Continents", continents)

    elif mode == "Celebrity Graves":
        countries = df["country"].nunique()
        professions = df["profession"].nunique() if "profession" in df.columns else 0
        earliest = df["died"].min() if "died" in df.columns else "N/A"
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Celebrity Graves", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Professions", professions)
        col4.metric("Earliest Death", earliest)

    elif mode == "Holocaust Memorials":
        countries = df["country"].nunique()
        types = df["type"].nunique() if "type" in df.columns else 0
        earliest = df["year_est"].min() if "year_est" in df.columns else "N/A"
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sites", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Site Types", types)
        col4.metric("Earliest Established", earliest)

    elif mode == "Ossuaries & Bone Churches":
        countries = df["country"].nunique()
        continents = df["country"].apply(_continent_from_country).nunique()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Ossuaries", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Continents", continents)

    elif mode == "Unique Burial Traditions":
        countries = df["country"].nunique()
        cultures = df["culture"].nunique() if "culture" in df.columns else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Traditions Mapped", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Distinct Cultures", cultures)

    elif mode == "National Monuments":
        countries = df["country"].nunique()
        types = df["type"].nunique() if "type" in df.columns else 0
        oldest = df["year_built"].min() if "year_built" in df.columns else "N/A"
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Monuments", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Monument Types", types)
        col4.metric("Oldest Built", oldest)

    elif mode == "Genocide Memorials":
        countries = df["country"].nunique()
        events = df["event"].nunique() if "event" in df.columns else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Memorials", num_sites)
        col2.metric("Countries", countries)
        col3.metric("Genocides / Atrocities", events)

    else:
        col1, col2 = st.columns(2)
        col1.metric("Total Sites", num_sites)
        col2.metric("Countries", df["country"].nunique() if "country" in df.columns else "N/A")


# ---------------------------------------------------------------------------
# Detail expanders
# ---------------------------------------------------------------------------

def _render_detail_expanders(df, mode, color):
    """Render expandable detail cards for each location in the dataset."""
    icon_char = _MODE_ICONS.get(mode, "\u26b0\ufe0f")
    skip_cols = {"lat", "lon", "name"}

    for idx, row in df.iterrows():
        name_safe = html_module.escape(str(row.get("name", "")))
        city_safe = html_module.escape(str(row.get("city", "")))
        country_safe = html_module.escape(str(row.get("country", "")))
        label = f"{icon_char} {name_safe} -- {city_safe}, {country_safe}"

        with st.expander(label, expanded=False):
            detail_cols = [c for c in df.columns if c not in skip_cols]

            # Two-column layout for details
            left, right = st.columns(2)
            half = len(detail_cols) // 2
            for i, col in enumerate(detail_cols):
                val = row.get(col, "")
                if pd.isna(val) or not str(val).strip():
                    continue
                col_label = col.replace("_", " ").title()
                target = left if i <= half else right
                target.markdown(f"**{col_label}:** {val}")

            # Coordinates
            st.caption(f"Coordinates: {row['lat']:.4f}, {row['lon']:.4f}")


# ---------------------------------------------------------------------------
# Country filter helper
# ---------------------------------------------------------------------------

def _apply_country_filter(df):
    """Add a country multiselect filter and return the filtered DataFrame."""
    if "country" not in df.columns:
        return df

    countries = sorted(df["country"].unique().tolist())
    selected = st.multiselect(
        "Filter by country",
        options=countries,
        default=countries,
        key="cemetery_country_filter",
    )
    if selected:
        return df[df["country"].isin(selected)].reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Search helper
# ---------------------------------------------------------------------------

def _apply_text_search(df):
    """Add a text search box and filter the DataFrame by name match."""
    query = st.text_input(
        "Search by name",
        value="",
        placeholder="Type to filter locations...",
        key="cemetery_text_search",
    )
    if query and query.strip():
        mask = df["name"].str.contains(query.strip(), case=False, na=False)
        return df[mask].reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_cemetery_maps_tab():
    """Render the Cemeteries & Memorials Maps tab in TerraScout AI."""

    # ---- Header ----
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>\u26b0\ufe0f Cemeteries & Memorials Maps</h4>"
        "<p>Famous cemeteries, war memorials, and burial traditions worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    modes = [
        "Famous Cemeteries",
        "War Memorials & Military Cemeteries",
        "Ancient Burial Sites",
        "Mausoleums & Tombs",
        "Celebrity Graves",
        "Holocaust Memorials",
        "Ossuaries & Bone Churches",
        "Unique Burial Traditions",
        "National Monuments",
        "Genocide Memorials",
    ]
    mode = st.selectbox("Map Mode", modes, key="cemetery_map_mode")
    color = _MODE_COLORS.get(mode, "#8b5cf6")

    # ---- Mode description ----
    desc = _MODE_DESCRIPTIONS.get(mode, "")
    if desc:
        st.info(f"{_MODE_ICONS.get(mode, '')} **{mode}** -- {desc}")

    # ---- Load data ----
    data_loaders = {
        "Famous Cemeteries": _famous_cemeteries,
        "War Memorials & Military Cemeteries": _war_memorials,
        "Ancient Burial Sites": _ancient_burial_sites,
        "Mausoleums & Tombs": _mausoleums_tombs,
        "Celebrity Graves": _celebrity_graves,
        "Holocaust Memorials": _holocaust_memorials,
        "Ossuaries & Bone Churches": _ossuaries_bone_churches,
        "Unique Burial Traditions": _unique_burial_traditions,
        "National Monuments": _national_monuments,
        "Genocide Memorials": _genocide_memorials,
    }
    loader = data_loaders.get(mode, _famous_cemeteries)
    df = pd.DataFrame(loader())

    # ---- Filters ----
    st.markdown("---")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        search_query = st.text_input(
            "Search by name",
            value="",
            placeholder="Type to filter locations...",
            key="cemetery_text_search",
        )
    with filter_col2:
        if "country" in df.columns:
            all_countries = sorted(df["country"].unique().tolist())
            selected_countries = st.multiselect(
                "Filter by country",
                options=all_countries,
                default=all_countries,
                key="cemetery_country_filter",
            )
        else:
            selected_countries = None

    # Apply filters
    if search_query and search_query.strip():
        df = df[df["name"].str.contains(search_query.strip(), case=False, na=False)]
    if selected_countries is not None and selected_countries:
        df = df[df["country"].isin(selected_countries)]
    df = df.reset_index(drop=True)

    if df.empty:
        st.warning("No locations match the current filters. Adjust your search or country selection.")
        return

    # ---- Stats row ----
    st.markdown("---")
    _render_stats(df, mode)

    # ---- Map ----
    st.markdown("---")
    st.subheader(f"Map: {mode}")
    m = _build_map(df, mode, color)
    st_html(m._repr_html_(), height=500)

    # ---- Detail expanders ----
    st.markdown("---")
    st.subheader(f"Location Details ({len(df)} sites)")
    _render_detail_expanders(df, mode, color)

    # ---- Data table ----
    st.markdown("---")
    st.subheader(f"Data Table: {mode}")
    st.dataframe(df, width=0, height=400)

    # ---- CSV download ----
    csv_data = df.to_csv(index=False).encode("utf-8")
    filename = mode.lower().replace(" ", "_").replace("&", "and") + ".csv"
    st.download_button(
        label=f"Download {mode} CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=f"cemetery_csv_{mode}",
    )

    # ---- Nearby POI lookup ----
    st.markdown("---")
    st.subheader("Nearby Points of Interest")
    st.caption(
        "Select a location to query the Overpass API for nearby tourism, "
        "historic, and worship sites within 2 km."
    )
    location_names = df["name"].tolist()
    selected_name = st.selectbox(
        "Select a location",
        options=location_names,
        key="cemetery_nearby_select",
    )
    if selected_name:
        sel_row = df[df["name"] == selected_name].iloc[0]
        sel_lat = float(sel_row["lat"])
        sel_lon = float(sel_row["lon"])

        if st.button("Search Nearby", key="cemetery_nearby_btn"):
            with st.spinner("Querying Overpass API..."):
                pois = _fetch_nearby_pois(sel_lat, sel_lon, radius_m=2000)
            if pois:
                poi_df = pd.DataFrame(pois)
                st.success(f"Found {len(poi_df)} nearby points of interest.")
                st.dataframe(poi_df, width=0)
            else:
                st.info("No nearby points of interest found (or API timeout).")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _continent_from_country(country):
    """Return the continent for a given country name."""
    return _CONTINENT_MAP.get(country, "Other")
