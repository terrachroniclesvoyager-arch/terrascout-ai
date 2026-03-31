# -*- coding: utf-8 -*-
"""
TerraScout AI - UNESCO & World Heritage Maps Module
Provides 10 interactive map modes covering World Heritage Cultural & Natural sites,
Biosphere Reserves, Global Geoparks, Intangible Cultural Heritage, Endangered Heritage,
Memory of the World, Creative Cities Network, Lost/Destroyed Heritage, and Tentative
List Highlights. All data is curated for offline reliability.
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
# COLOUR HELPERS & DARK-THEME UTILITIES
# =====================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
ACCENT_CYAN = "#06b6d4"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_EMERALD = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_PINK = "#ec4899"
ACCENT_RED = "#ef4444"
ACCENT_BLUE = "#3b82f6"
ACCENT_ORANGE = "#f97316"
ACCENT_TEAL = "#14b8a6"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"

CATEGORY_COLORS = [
    "#06b6d4", "#ec4899", "#8b5cf6", "#f59e0b", "#10b981",
    "#ef4444", "#3b82f6", "#f97316", "#14b8a6", "#a855f7",
    "#e11d48", "#84cc16", "#facc15", "#22d3ee", "#c084fc",
]


def _color_for(index: int) -> str:
    return CATEGORY_COLORS[index % len(CATEGORY_COLORS)]


def _dark_fig(rows=1, cols=1, figsize=(10, 5)):
    fig, ax = plt.subplots(rows, cols, figsize=figsize, facecolor=BG_DARK)
    if rows == 1 and cols == 1:
        ax.set_facecolor(SURFACE)
        ax.tick_params(colors=TEXT_SECONDARY)
        ax.xaxis.label.set_color(TEXT_PRIMARY)
        ax.yaxis.label.set_color(TEXT_PRIMARY)
        ax.title.set_color(TEXT_PRIMARY)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")
    return fig, ax


def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _base_map(center=None, zoom=2):
    if center is None:
        center = [20, 0]
    return folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        width="100%",
        height=500,
    )


def _show_map(m):
    components.html(m._repr_html_(), height=500)


def _df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# =====================================================================
# 1. WORLD HERITAGE CULTURAL SITES (50+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_cultural_sites():
    data = [
        {"name": "Historic Centre of Rome", "lat": 41.8967, "lon": 12.4822, "country": "Italy", "year": 1980, "description": "Ancient Roman ruins, Renaissance and Baroque palaces, churches spanning 2800 years of history"},
        {"name": "Acropolis of Athens", "lat": 37.9715, "lon": 23.7267, "country": "Greece", "year": 1987, "description": "Parthenon, Erechtheion and other masterpieces of classical Greek architecture"},
        {"name": "Taj Mahal", "lat": 27.1751, "lon": 78.0421, "country": "India", "year": 1983, "description": "Mughal ivory-white marble mausoleum, jewel of Muslim art in India"},
        {"name": "Great Wall of China", "lat": 40.4319, "lon": 116.5704, "country": "China", "year": 1987, "description": "Series of fortifications spanning over 20,000 km, built from 7th century BC"},
        {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "country": "Peru", "year": 1983, "description": "15th-century Inca citadel set high in the Andes at 2,430 metres"},
        {"name": "Petra", "lat": 30.3285, "lon": 35.4444, "country": "Jordan", "year": 1985, "description": "Nabataean rock-cut city from the 4th century BC, rose-red cliff facades"},
        {"name": "Angkor", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "year": 1992, "description": "Vast Khmer temple complex including Angkor Wat, largest religious monument on Earth"},
        {"name": "Historic Centre of Florence", "lat": 43.7696, "lon": 11.2558, "country": "Italy", "year": 1982, "description": "Birthplace of the Renaissance, home to Duomo, Uffizi, and Ponte Vecchio"},
        {"name": "Alhambra, Generalife and Albayzin", "lat": 37.1761, "lon": -3.5881, "country": "Spain", "year": 1984, "description": "Moorish palatine city with stunning Islamic art and Nasrid architecture"},
        {"name": "Palace of Versailles", "lat": 48.8049, "lon": 2.1204, "country": "France", "year": 1979, "description": "Grand 17th-century royal palace, symbol of French absolutism"},
        {"name": "Pyramids of Giza", "lat": 29.9792, "lon": 31.1342, "country": "Egypt", "year": 1979, "description": "Only surviving Wonder of the Ancient World, tombs of the pharaohs"},
        {"name": "Historic Centre of Prague", "lat": 50.0755, "lon": 14.4378, "country": "Czech Republic", "year": 1992, "description": "Medieval old town with Gothic, Romanesque, Baroque and Art Nouveau architecture"},
        {"name": "Kremlin and Red Square", "lat": 55.7520, "lon": 37.6175, "country": "Russia", "year": 1990, "description": "Medieval fortified complex, heart of Moscow with iconic St. Basil's Cathedral"},
        {"name": "Kyoto Monuments", "lat": 35.0116, "lon": 135.7681, "country": "Japan", "year": 1994, "description": "17 Buddhist temples, Shinto shrines and a castle spanning 794 AD onwards"},
        {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678, "country": "Mexico", "year": 1988, "description": "Major pre-Columbian Maya city, El Castillo pyramid and sacred cenote"},
        {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "country": "United Kingdom", "year": 1986, "description": "Neolithic stone circle dating to around 3000 BC, astronomical alignment"},
        {"name": "Historic Cairo", "lat": 30.0459, "lon": 31.2243, "country": "Egypt", "year": 1979, "description": "One of the world's oldest Islamic cities with mosques, madrasas and hammams"},
        {"name": "Forbidden City", "lat": 39.9163, "lon": 116.3972, "country": "China", "year": 1987, "description": "Imperial palace complex with 980 buildings, largest ancient palatine structure"},
        {"name": "Persepolis", "lat": 29.9352, "lon": 52.8914, "country": "Iran", "year": 1979, "description": "Ceremonial capital of the Achaemenid Empire, 6th-century BC ruins"},
        {"name": "Medina of Fez", "lat": 34.0622, "lon": -4.9826, "country": "Morocco", "year": 1981, "description": "World's largest car-free urban area, medieval Islamic city founded in 789"},
        {"name": "Dubrovnik Old City", "lat": 42.6408, "lon": 18.1082, "country": "Croatia", "year": 1979, "description": "Pearl of the Adriatic, intact medieval walled city on the Dalmatian coast"},
        {"name": "Mont-Saint-Michel", "lat": 48.6361, "lon": -1.5115, "country": "France", "year": 1979, "description": "Tidal island commune with medieval Benedictine abbey perched atop granite"},
        {"name": "Venice and its Lagoon", "lat": 45.4408, "lon": 12.3155, "country": "Italy", "year": 1987, "description": "City built on 118 small islands linked by canals and 400 bridges"},
        {"name": "Borobudur Temple", "lat": -7.6079, "lon": 110.2038, "country": "Indonesia", "year": 1991, "description": "World's largest Buddhist temple, 9th-century monument with 2,672 relief panels"},
        {"name": "Timbuktu", "lat": 16.7735, "lon": -3.0074, "country": "Mali", "year": 1988, "description": "Fabled centre of Islamic scholarship with three great mosques from the golden age"},
        {"name": "Potala Palace", "lat": 29.6577, "lon": 91.1170, "country": "China", "year": 1994, "description": "Winter palace of the Dalai Lamas since 7th century, iconic Tibetan architecture"},
        {"name": "Pompeii", "lat": 40.7509, "lon": 14.4869, "country": "Italy", "year": 1997, "description": "Roman city buried by Vesuvius eruption in 79 AD, perfectly preserved snapshot of antiquity"},
        {"name": "Auschwitz-Birkenau", "lat": 50.0343, "lon": 19.1783, "country": "Poland", "year": 1979, "description": "Nazi concentration and extermination camp, memorial to the Holocaust"},
        {"name": "Hagia Sophia Historic Area", "lat": 41.0086, "lon": 28.9802, "country": "Turkey", "year": 1985, "description": "Istanbul's historic peninsula with Byzantine and Ottoman masterworks"},
        {"name": "Rapa Nui (Easter Island)", "lat": -27.1127, "lon": -109.3497, "country": "Chile", "year": 1995, "description": "Remote volcanic island with nearly 900 monumental moai statues"},
        {"name": "Hampi", "lat": 15.3350, "lon": 76.4600, "country": "India", "year": 1986, "description": "Ruins of Vijayanagara, last great Hindu kingdom, 1,600+ surviving structures"},
        {"name": "Great Zimbabwe", "lat": -20.2712, "lon": 30.9336, "country": "Zimbabwe", "year": 1986, "description": "Largest stone structures in sub-Saharan Africa, medieval Shona kingdom capital"},
        {"name": "Sukhothai Historical Park", "lat": 17.0070, "lon": 99.7032, "country": "Thailand", "year": 1991, "description": "Ruins of the first capital of Siam, 13th-14th century temples and Buddha statues"},
        {"name": "Carcassonne", "lat": 43.2065, "lon": 2.3630, "country": "France", "year": 1997, "description": "Magnificent medieval fortified city with double ring of ramparts and towers"},
        {"name": "Cusco Old Town", "lat": -13.5170, "lon": -71.9785, "country": "Peru", "year": 1983, "description": "Inca capital with Spanish colonial architecture built upon Inca stone foundations"},
        {"name": "Historic Centre of Vienna", "lat": 48.2082, "lon": 16.3738, "country": "Austria", "year": 2001, "description": "Imperial capital with Baroque palaces, Ringstrasse boulevard, and musical heritage"},
        {"name": "Old City of Jerusalem", "lat": 31.7767, "lon": 35.2345, "country": "Israel/Palestine", "year": 1981, "description": "Sacred city for Judaism, Christianity and Islam within 16th-century Ottoman walls"},
        {"name": "Bagan", "lat": 21.1717, "lon": 94.8585, "country": "Myanmar", "year": 2019, "description": "Over 3,500 Buddhist temples, pagodas and monasteries on the Irrawaddy plain"},
        {"name": "Ellora Caves", "lat": 20.0268, "lon": 75.1791, "country": "India", "year": 1983, "description": "34 rock-cut caves representing Buddhist, Hindu and Jain art from 600-1000 AD"},
        {"name": "Tower of London", "lat": 51.5081, "lon": -0.0759, "country": "United Kingdom", "year": 1988, "description": "Medieval royal fortress, palace and prison housing the Crown Jewels since 1066"},
        {"name": "Meteora", "lat": 39.7217, "lon": 21.6306, "country": "Greece", "year": 1988, "description": "Six monasteries perched atop immense sandstone pillars in central Greece"},
        {"name": "Lalibela", "lat": 12.0316, "lon": 39.0436, "country": "Ethiopia", "year": 1978, "description": "Eleven medieval rock-hewn churches carved from volcanic tuff, New Jerusalem"},
        {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438, "country": "Mexico", "year": 1987, "description": "Pre-Columbian city with Pyramid of the Sun, Avenue of the Dead, 100 BC - 700 AD"},
        {"name": "Abu Simbel", "lat": 22.3360, "lon": 31.6256, "country": "Egypt", "year": 1979, "description": "Two massive rock temples of Ramesses II relocated during the Aswan Dam project"},
        {"name": "Samarkand", "lat": 39.6542, "lon": 66.9597, "country": "Uzbekistan", "year": 2001, "description": "Crossroads of cultures on the Silk Road, Registan Square and Timurid mosques"},
        {"name": "Sigiriya", "lat": 7.9571, "lon": 80.7603, "country": "Sri Lanka", "year": 1982, "description": "Ancient rock fortress with frescoes, Lion Gate and water gardens, 5th century AD"},
        {"name": "Historic Centre of Bruges", "lat": 51.2094, "lon": 3.2247, "country": "Belgium", "year": 2000, "description": "Outstanding medieval city, canal network and Gothic architecture in Flanders"},
        {"name": "Mohenjo-daro", "lat": 27.3290, "lon": 68.1389, "country": "Pakistan", "year": 1980, "description": "Ruins of the Indus Valley Civilization city, one of the earliest major urban centres"},
        {"name": "Historic Sanctuary of Machu Picchu", "lat": -13.2263, "lon": -72.4973, "country": "Peru", "year": 1983, "description": "Sacred Inca site blending natural and cultural landscape in cloud forest"},
        {"name": "Rock-Hewn Churches of Ivanovo", "lat": 43.7283, "lon": 25.9736, "country": "Bulgaria", "year": 1979, "description": "Medieval Bulgarian frescoes in rock-cut chapels along the Rusenski Lom river"},
        {"name": "Meidan Emam, Isfahan", "lat": 32.6546, "lon": 51.6776, "country": "Iran", "year": 1979, "description": "Monumental square bordered by masterpieces of Safavid-era Islamic architecture"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 2. WORLD HERITAGE NATURAL SITES (40+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_natural_sites():
    data = [
        {"name": "Great Barrier Reef", "lat": -18.2871, "lon": 147.6992, "country": "Australia", "year": 1981, "description": "World's largest coral reef system, 2,300 km of marine biodiversity"},
        {"name": "Galapagos Islands", "lat": -0.9538, "lon": -90.9656, "country": "Ecuador", "year": 1978, "description": "Volcanic archipelago with unique endemic species that inspired Darwin's theory"},
        {"name": "Yellowstone National Park", "lat": 44.4280, "lon": -110.5885, "country": "USA", "year": 1978, "description": "First national park, geothermal features, geysers and diverse megafauna"},
        {"name": "Serengeti National Park", "lat": -2.3333, "lon": 34.8333, "country": "Tanzania", "year": 1981, "description": "Iconic African savanna with the world's largest terrestrial mammal migration"},
        {"name": "Grand Canyon National Park", "lat": 36.1069, "lon": -112.1126, "country": "USA", "year": 1979, "description": "Immense gorge exposing 2 billion years of geological history"},
        {"name": "Victoria Falls", "lat": -17.9243, "lon": 25.8572, "country": "Zambia/Zimbabwe", "year": 1989, "description": "World's largest sheet of falling water, 1,708 m wide Zambezi curtain"},
        {"name": "Mount Kilimanjaro", "lat": -3.0674, "lon": 37.3556, "country": "Tanzania", "year": 1987, "description": "Africa's highest peak at 5,895 m with five distinct ecological zones"},
        {"name": "Iguazu National Park", "lat": -25.6953, "lon": -54.4367, "country": "Argentina/Brazil", "year": 1984, "description": "275 waterfalls spanning 2.7 km on the Iguazu River in subtropical rainforest"},
        {"name": "Ha Long Bay", "lat": 20.9101, "lon": 107.1839, "country": "Vietnam", "year": 1994, "description": "1,600 limestone pillars and islands in emerald waters of the Gulf of Tonkin"},
        {"name": "Plitvice Lakes National Park", "lat": 44.8654, "lon": 15.5820, "country": "Croatia", "year": 1979, "description": "16 cascading lakes connected by waterfalls amid lush forest"},
        {"name": "Dolomites", "lat": 46.4100, "lon": 11.8400, "country": "Italy", "year": 2009, "description": "Spectacular mountain landscape of 18 peaks above 3,000 m in the Alps"},
        {"name": "Swiss Alps Jungfrau-Aletsch", "lat": 46.5600, "lon": 7.9700, "country": "Switzerland", "year": 2001, "description": "Largest glaciated area in the Alps with outstanding alpine landscape"},
        {"name": "Amazon Rainforest (Central Amazon)", "lat": -2.5000, "lon": -60.0000, "country": "Brazil", "year": 2000, "description": "Largest protected area in the Amazon Basin, extraordinary aquatic biodiversity"},
        {"name": "Komodo National Park", "lat": -8.5500, "lon": 119.4500, "country": "Indonesia", "year": 1991, "description": "Home of the Komodo dragon, volcanic islands with coral reefs"},
        {"name": "Jiuzhaigou Valley", "lat": 33.2600, "lon": 103.9200, "country": "China", "year": 1992, "description": "Colourful lakes, multi-level waterfalls and snow-capped peaks in Sichuan"},
        {"name": "Banff & Canadian Rockies", "lat": 51.4968, "lon": -115.9281, "country": "Canada", "year": 1984, "description": "Mountain landscape with glaciers, hot springs, ice fields and Burgess Shale fossils"},
        {"name": "Sagarmatha (Everest) National Park", "lat": 27.9881, "lon": 86.9250, "country": "Nepal", "year": 1979, "description": "World's highest peak and dramatic Himalayan landscape with rare species"},
        {"name": "Te Wahipounamu (SW New Zealand)", "lat": -44.6700, "lon": 167.9300, "country": "New Zealand", "year": 1990, "description": "Fiordlands, rainforest and glacial lakes, Gondwana relict flora"},
        {"name": "Wulingyuan Scenic Area", "lat": 29.3400, "lon": 110.5500, "country": "China", "year": 1992, "description": "3,000 sandstone pillars up to 200 m tall (inspired Avatar's Hallelujah Mountains)"},
        {"name": "Los Glaciares National Park", "lat": -50.3300, "lon": -73.2500, "country": "Argentina", "year": 1981, "description": "Perito Moreno Glacier and spectacular Patagonian ice cap landscape"},
        {"name": "Okavango Delta", "lat": -19.5000, "lon": 22.5000, "country": "Botswana", "year": 2014, "description": "World's largest inland delta, seasonal flooding supports vast wildlife populations"},
        {"name": "Zhangjiajie National Forest Park", "lat": 29.3167, "lon": 110.4340, "country": "China", "year": 1992, "description": "Towering quartzite sandstone pillars and subtropical forest in Hunan"},
        {"name": "Bwindi Impenetrable Forest", "lat": -1.0500, "lon": 29.6167, "country": "Uganda", "year": 1994, "description": "One of the most biologically diverse areas on Earth, mountain gorilla habitat"},
        {"name": "Sundarbans", "lat": 21.9497, "lon": 89.1833, "country": "Bangladesh/India", "year": 1997, "description": "Largest mangrove forest in the world, home to the Bengal tiger"},
        {"name": "Putorana Plateau", "lat": 68.3500, "lon": 94.0000, "country": "Russia", "year": 2010, "description": "Isolated basalt plateau with pristine arctic lakes and thousands of waterfalls"},
        {"name": "Socotra Archipelago", "lat": 12.4634, "lon": 53.8237, "country": "Yemen", "year": 2008, "description": "Alien-like endemic flora including dragon's blood trees, 37% unique plant species"},
        {"name": "Canaima National Park", "lat": 6.2500, "lon": -62.5000, "country": "Venezuela", "year": 1994, "description": "Tepui table-top mountains and Angel Falls, world's highest uninterrupted waterfall"},
        {"name": "Mount Etna", "lat": 37.7510, "lon": 14.9934, "country": "Italy", "year": 2013, "description": "Europe's highest and most active volcano, 500,000 years of volcanic activity"},
        {"name": "Giant's Causeway", "lat": 55.2408, "lon": -6.5116, "country": "United Kingdom", "year": 1986, "description": "40,000 interlocking basalt columns from ancient volcanic fissure eruption"},
        {"name": "Shiretoko Peninsula", "lat": 44.1000, "lon": 145.2000, "country": "Japan", "year": 2005, "description": "Marine and terrestrial ecosystems with sea ice, brown bears and Steller's sea eagle"},
        {"name": "Daintree Rainforest (Wet Tropics)", "lat": -16.2500, "lon": 145.4167, "country": "Australia", "year": 1988, "description": "Oldest continuously surviving tropical rainforest, 135 million years old"},
        {"name": "Wadi Rum", "lat": 29.5321, "lon": 35.4214, "country": "Jordan", "year": 2011, "description": "Sandstone and granite desert landscape with 25,000 rock carvings and inscriptions"},
        {"name": "Jeju Volcanic Island", "lat": 33.3617, "lon": 126.5292, "country": "South Korea", "year": 2007, "description": "Shield volcano with lava tubes and Hallasan mountain, unique geology"},
        {"name": "Isole Eolie (Aeolian Islands)", "lat": 38.5500, "lon": 14.9500, "country": "Italy", "year": 2000, "description": "Seven volcanic islands providing textbook examples of volcanism"},
        {"name": "Lake Baikal", "lat": 53.5587, "lon": 108.1650, "country": "Russia", "year": 1996, "description": "Oldest (25 million years) and deepest (1,642 m) lake on Earth"},
        {"name": "Ngorongoro Conservation Area", "lat": -3.2000, "lon": 35.5000, "country": "Tanzania", "year": 1979, "description": "Vast volcanic caldera with 25,000 large animals and Laetoli hominin footprints"},
        {"name": "Primeval Beech Forests", "lat": 48.9300, "lon": 22.5400, "country": "Multiple European", "year": 2007, "description": "Outstanding beech forest ecosystems across 18 European countries"},
        {"name": "Tubbataha Reefs Natural Park", "lat": 8.9167, "lon": 119.9167, "country": "Philippines", "year": 1993, "description": "Pristine coral atoll in the Sulu Sea with exceptional marine biodiversity"},
        {"name": "Three Parallel Rivers of Yunnan", "lat": 28.4500, "lon": 98.9000, "country": "China", "year": 2003, "description": "Yangtze, Mekong and Salween flow in parallel gorges through extreme topography"},
        {"name": "Virunga National Park", "lat": -1.0000, "lon": 29.2000, "country": "DR Congo", "year": 1979, "description": "Active volcanoes, graben valleys and mountain gorillas in Africa's oldest park"},
        {"name": "Vatnajokull National Park", "lat": 64.4000, "lon": -16.8000, "country": "Iceland", "year": 2019, "description": "Dynamic volcanic area beneath Europe's largest glacier, fire and ice interplay"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 3. UNESCO BIOSPHERE RESERVES (30+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_biosphere_reserves():
    data = [
        {"name": "Yellowstone Biosphere Reserve", "lat": 44.4280, "lon": -110.5885, "country": "USA", "year": 1976, "area_km2": 8991, "ecosystems": "Geothermal, alpine meadows, boreal forest, grassland"},
        {"name": "Galapagos Biosphere Reserve", "lat": -0.9538, "lon": -90.9656, "country": "Ecuador", "year": 1984, "area_km2": 14761, "ecosystems": "Marine, volcanic, arid, coastal, mangrove"},
        {"name": "Serengeti-Ngorongoro", "lat": -2.7000, "lon": 34.8000, "country": "Tanzania", "year": 1981, "area_km2": 23051, "ecosystems": "Savanna, woodland, grassland, montane forest"},
        {"name": "Amazon Central", "lat": -2.5000, "lon": -60.0000, "country": "Brazil", "year": 2001, "area_km2": 20860, "ecosystems": "Tropical rainforest, flooded forest, river systems"},
        {"name": "Danube Delta", "lat": 45.0833, "lon": 29.5000, "country": "Romania", "year": 1998, "area_km2": 6264, "ecosystems": "Wetland, marsh, sand dunes, freshwater lakes"},
        {"name": "Sundarbans", "lat": 21.9497, "lon": 89.1833, "country": "Bangladesh", "year": 1997, "area_km2": 6017, "ecosystems": "Mangrove, tidal waterways, mudflats, salt-tolerant forest"},
        {"name": "Sierra Nevada (Spain)", "lat": 37.0500, "lon": -3.3500, "country": "Spain", "year": 1986, "area_km2": 1722, "ecosystems": "Mediterranean highland, alpine, steppe, semi-arid"},
        {"name": "Jeju Island", "lat": 33.3617, "lon": 126.5292, "country": "South Korea", "year": 2002, "area_km2": 831, "ecosystems": "Volcanic, subtropical forest, wetland, marine"},
        {"name": "Camargue", "lat": 43.5000, "lon": 4.5000, "country": "France", "year": 1977, "area_km2": 850, "ecosystems": "Wetland, saltwater lagoons, marshes, rice paddies"},
        {"name": "Mount Kenya", "lat": -0.1521, "lon": 37.3084, "country": "Kenya", "year": 1978, "area_km2": 7180, "ecosystems": "Alpine, bamboo forest, moorland, glacial"},
        {"name": "Kronotsky", "lat": 54.4333, "lon": 160.1000, "country": "Russia", "year": 1984, "area_km2": 11476, "ecosystems": "Volcanic, geyser, tundra, boreal forest, marine"},
        {"name": "Torres del Paine", "lat": -51.0000, "lon": -73.0000, "country": "Chile", "year": 1978, "area_km2": 2422, "ecosystems": "Patagonian steppe, glaciers, temperate forest, lakes"},
        {"name": "Waddensea", "lat": 53.6000, "lon": 8.0000, "country": "Germany/Netherlands/Denmark", "year": 1986, "area_km2": 11500, "ecosystems": "Tidal flats, salt marshes, dunes, barrier islands"},
        {"name": "Cat Ba Archipelago", "lat": 20.7333, "lon": 107.0333, "country": "Vietnam", "year": 2004, "area_km2": 263, "ecosystems": "Limestone karst, mangrove, coral reef, tropical forest"},
        {"name": "Tonle Sap", "lat": 12.8333, "lon": 104.0000, "country": "Cambodia", "year": 1997, "area_km2": 14813, "ecosystems": "Freshwater lake, floodplain, floating forest, wetland"},
        {"name": "Manu National Park", "lat": -12.0000, "lon": -71.5000, "country": "Peru", "year": 1977, "area_km2": 18811, "ecosystems": "Andean highland, cloud forest, lowland tropical rainforest"},
        {"name": "Great Sandy", "lat": -25.3000, "lon": 153.1000, "country": "Australia", "year": 2009, "area_km2": 5600, "ecosystems": "Sand island, subtropical rainforest, mangrove, marine"},
        {"name": "Sian Ka'an", "lat": 20.0500, "lon": -87.5000, "country": "Mexico", "year": 1986, "area_km2": 5280, "ecosystems": "Tropical forest, marsh, mangrove, barrier reef, cenotes"},
        {"name": "Mata Atlantica (Atlantic Forest)", "lat": -23.5000, "lon": -46.0000, "country": "Brazil", "year": 1993, "area_km2": 29473, "ecosystems": "Atlantic rainforest, restinga, mangrove, cloud forest"},
        {"name": "Djoudj Bird Sanctuary", "lat": 16.4000, "lon": -16.2000, "country": "Senegal", "year": 1981, "area_km2": 160, "ecosystems": "Sahelian wetland, lake, river delta, migratory bird habitat"},
        {"name": "Changbaishan", "lat": 42.0500, "lon": 128.0600, "country": "China", "year": 1979, "area_km2": 1964, "ecosystems": "Temperate forest, volcanic crater lake, alpine tundra"},
        {"name": "Olympic National Park", "lat": 47.8021, "lon": -123.6044, "country": "USA", "year": 1976, "area_km2": 3734, "ecosystems": "Temperate rainforest, alpine, subalpine, Pacific coast marine"},
        {"name": "Volcanoes of Kamchatka", "lat": 55.0000, "lon": 160.0000, "country": "Russia", "year": 1996, "area_km2": 37810, "ecosystems": "Active volcanoes, geysers, boreal forest, salmon rivers, tundra"},
        {"name": "Lake Tana", "lat": 12.0000, "lon": 37.3333, "country": "Ethiopia", "year": 2015, "area_km2": 6950, "ecosystems": "Highland lake, wetland, island monasteries, papyrus swamp"},
        {"name": "Sinharaja Forest Reserve", "lat": 6.4000, "lon": 80.5000, "country": "Sri Lanka", "year": 1978, "area_km2": 111, "ecosystems": "Tropical lowland rainforest, 60% endemic tree species"},
        {"name": "Cevennes", "lat": 44.3000, "lon": 3.5000, "country": "France", "year": 1985, "area_km2": 3213, "ecosystems": "Mediterranean garrigue, chestnut forest, limestone plateau"},
        {"name": "Nilgiri", "lat": 11.4000, "lon": 76.5000, "country": "India", "year": 1986, "area_km2": 5520, "ecosystems": "Tropical moist forest, dry deciduous forest, shola grassland"},
        {"name": "Noosa", "lat": -26.3833, "lon": 153.0833, "country": "Australia", "year": 2007, "area_km2": 1502, "ecosystems": "Coastal, wallum heathland, subtropical rainforest, marine"},
        {"name": "South-East Rugen", "lat": 54.3667, "lon": 13.6333, "country": "Germany", "year": 1991, "area_km2": 235, "ecosystems": "Chalk cliffs, beech forest, lagoon, Baltic coast"},
        {"name": "Issyk-Kul", "lat": 42.4500, "lon": 77.2500, "country": "Kyrgyzstan", "year": 2001, "area_km2": 43100, "ecosystems": "Alpine lake, mountain steppe, walnut-fruit forest, glacier"},
        {"name": "Palawan", "lat": 10.0000, "lon": 118.8333, "country": "Philippines", "year": 1990, "area_km2": 11580, "ecosystems": "Tropical rainforest, mangrove, coral reef, limestone karst"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 4. GLOBAL GEOPARKS (25+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_geoparks():
    data = [
        {"name": "English Riviera", "lat": 50.4619, "lon": -3.5253, "country": "United Kingdom", "year": 2007, "geological_features": "Devonian limestone, sea caves, fossil reef, karstic landscape"},
        {"name": "Langkawi", "lat": 6.3500, "lon": 99.8000, "country": "Malaysia", "year": 2007, "geological_features": "500-million-year-old rocks, sea stacks, mangrove geomorphology"},
        {"name": "Lesvos Petrified Forest", "lat": 39.2000, "lon": 25.9500, "country": "Greece", "year": 2012, "geological_features": "20-million-year-old petrified forest, volcanic caldera"},
        {"name": "Naturtejo da Meseta Meridional", "lat": 39.7500, "lon": -7.7500, "country": "Portugal", "year": 2006, "geological_features": "Ichnofossils, quartzite ridges, fluvial geomorphology"},
        {"name": "Zhangjiajie", "lat": 29.3167, "lon": 110.4340, "country": "China", "year": 2004, "geological_features": "Sandstone pillar forests, karst plateaus, Devonian stratigraphy"},
        {"name": "Haute-Provence", "lat": 44.0000, "lon": 6.2333, "country": "France", "year": 2000, "geological_features": "Ammonia fossils, Jurassic limestone, lavender-covered geology trail"},
        {"name": "Vulkaneifel", "lat": 50.2833, "lon": 6.8833, "country": "Germany", "year": 2004, "geological_features": "Maar lakes, volcanic craters, mineral springs, basalt columns"},
        {"name": "Araripe", "lat": -7.2500, "lon": -39.4167, "country": "Brazil", "year": 2006, "geological_features": "Cretaceous fossils, pterosaur beds, sedimentary basin, chapada plateau"},
        {"name": "Jeju Island", "lat": 33.3617, "lon": 126.5292, "country": "South Korea", "year": 2012, "geological_features": "Shield volcano, lava tubes, columnar joints, tuff cones"},
        {"name": "Copper Coast", "lat": 52.1667, "lon": -7.3667, "country": "Ireland", "year": 2004, "geological_features": "Ordovician volcanic rocks, copper mining, coastal geology"},
        {"name": "Marble Arch Caves", "lat": 54.2500, "lon": -7.8167, "country": "United Kingdom/Ireland", "year": 2004, "geological_features": "Limestone caves, karst landscape, underground rivers"},
        {"name": "Sierra Norte de Sevilla", "lat": 37.9500, "lon": -5.7167, "country": "Spain", "year": 2011, "geological_features": "Cambrian rocks, stromatolites, granite batholith, mineral veins"},
        {"name": "Burren and Cliffs of Moher", "lat": 53.0000, "lon": -9.4000, "country": "Ireland", "year": 2011, "geological_features": "Karst limestone pavement, Carboniferous marine fossils, sea cliffs"},
        {"name": "Toya-Usu", "lat": 42.5333, "lon": 140.8333, "country": "Japan", "year": 2009, "geological_features": "Active volcanoes, caldera lake, lava domes, geothermal vents"},
        {"name": "Unzen Volcanic Area", "lat": 32.7500, "lon": 130.2500, "country": "Japan", "year": 2009, "geological_features": "Active stratovolcano, pyroclastic flows, hot springs, volcanic dome"},
        {"name": "Qeshm Island", "lat": 26.8000, "lon": 56.0000, "country": "Iran", "year": 2017, "geological_features": "Salt domes, mangrove, canyon geology, Hormuz formation"},
        {"name": "Songshan", "lat": 34.4833, "lon": 113.0667, "country": "China", "year": 2004, "geological_features": "3.6-billion-year-old rocks, Precambrian stratigraphy, tectonic uplift"},
        {"name": "Hong Kong", "lat": 22.3700, "lon": 114.2700, "country": "China", "year": 2011, "geological_features": "Hexagonal columnar joints, volcanic tuff, coastal erosion features"},
        {"name": "Satun", "lat": 6.6200, "lon": 100.0700, "country": "Thailand", "year": 2018, "geological_features": "Cambrian-Ordovician fossils, karst islands, cave systems"},
        {"name": "Ciletuh-Palabuhanratu", "lat": -6.9333, "lon": 106.4333, "country": "Indonesia", "year": 2018, "geological_features": "Ancient oceanic crust, ophiolite, coastal geoheritage, waterfalls"},
        {"name": "Maestrazgo", "lat": 40.6500, "lon": -0.5000, "country": "Spain", "year": 2015, "geological_features": "Mesozoic sedimentary basin, dinosaur tracks, cave paintings"},
        {"name": "Adamello Brenta", "lat": 46.2000, "lon": 10.8667, "country": "Italy", "year": 2008, "geological_features": "Dolomite peaks, granitic batholith, glacial geomorphology"},
        {"name": "Bohemian Paradise", "lat": 50.5333, "lon": 15.1833, "country": "Czech Republic", "year": 2005, "geological_features": "Sandstone rock cities, volcanic necks, Cretaceous marine sediments"},
        {"name": "Odsherred", "lat": 55.7667, "lon": 11.6000, "country": "Denmark", "year": 2014, "geological_features": "Ice Age dead-ice landscape, raised coastlines, glacial deposits"},
        {"name": "Shetland", "lat": 60.3500, "lon": -1.1667, "country": "United Kingdom", "year": 2009, "geological_features": "3-billion-year-old gneiss, ophiolite, tombolo, glacial landforms"},
        {"name": "Las Loras", "lat": 42.7333, "lon": -3.9000, "country": "Spain", "year": 2017, "geological_features": "Mesozoic mesa landscape, sinkholes, river canyons, fossil reefs"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 5. INTANGIBLE CULTURAL HERITAGE (30+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_intangible_heritage():
    data = [
        {"name": "Flamenco", "lat": 37.3886, "lon": -5.9823, "country": "Spain", "year": 2010, "category": "Performing arts", "description": "Andalusian art form encompassing singing, guitar, dance and handclapping"},
        {"name": "Yoga", "lat": 30.0869, "lon": 78.2676, "country": "India", "year": 2016, "category": "Traditional knowledge", "description": "Ancient physical, mental and spiritual practice originating in India"},
        {"name": "Tango", "lat": -34.6037, "lon": -58.3816, "country": "Argentina/Uruguay", "year": 2009, "category": "Performing arts", "description": "Musical genre and associated dance born in the Rio de la Plata region"},
        {"name": "Washoku (Japanese cuisine)", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "year": 2013, "category": "Culinary arts", "description": "Traditional dietary culture emphasizing seasonal ingredients and presentation"},
        {"name": "Chinese calligraphy", "lat": 39.9042, "lon": 116.4074, "country": "China", "year": 2009, "category": "Traditional craftsmanship", "description": "Artistic writing of Chinese characters with brush and ink"},
        {"name": "Carnival of Binche", "lat": 50.4113, "lon": 4.1658, "country": "Belgium", "year": 2008, "category": "Social practices", "description": "Pre-Lenten carnival with Gilles dancers throwing blood oranges"},
        {"name": "Reggae Music", "lat": 18.1096, "lon": -77.2975, "country": "Jamaica", "year": 2018, "category": "Performing arts", "description": "Jamaican music genre with African, Caribbean and American influences"},
        {"name": "Nowruz (Persian New Year)", "lat": 35.6892, "lon": 51.3890, "country": "Iran & others", "year": 2009, "category": "Social practices", "description": "Spring equinox celebration marking the new year in Persian culture"},
        {"name": "Pizzaiuolo (Neapolitan pizza)", "lat": 40.8518, "lon": 14.2681, "country": "Italy", "year": 2017, "category": "Culinary arts", "description": "Art of the Neapolitan pizza maker, dough-twirling tradition"},
        {"name": "Gamelan", "lat": -7.7972, "lon": 110.3688, "country": "Indonesia", "year": 2021, "category": "Performing arts", "description": "Traditional ensemble music using metallic percussion instruments of Java and Bali"},
        {"name": "Fado", "lat": 38.7223, "lon": -9.1393, "country": "Portugal", "year": 2011, "category": "Performing arts", "description": "Melancholic urban folk music genre of Lisbon, expressing saudade"},
        {"name": "Venetian Rowing", "lat": 45.4408, "lon": 12.3155, "country": "Italy", "year": 2024, "category": "Social practices", "description": "Traditional standing rowing technique of Venice's gondoliers and regattas"},
        {"name": "Noh Theatre", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "year": 2008, "category": "Performing arts", "description": "Masked dance-drama combining music, dance and acting since 14th century"},
        {"name": "Mevlevi Sema (Whirling Dervishes)", "lat": 37.8714, "lon": 32.4846, "country": "Turkey", "year": 2008, "category": "Performing arts", "description": "Sufi whirling dance ceremony of the Mevlevi order from Konya"},
        {"name": "Kris (dagger)", "lat": -7.7972, "lon": 110.3688, "country": "Indonesia", "year": 2005, "category": "Traditional craftsmanship", "description": "Asymmetrical dagger with spiritual significance, forged with damascened steel"},
        {"name": "Tapa cloth making", "lat": -21.1789, "lon": -175.1982, "country": "Tonga", "year": 2023, "category": "Traditional craftsmanship", "description": "Bark cloth beaten from paper mulberry, central to Pacific Island ceremonies"},
        {"name": "Alpine transhumance", "lat": 47.0000, "lon": 11.0000, "country": "Austria/Italy/Greece", "year": 2023, "category": "Social practices", "description": "Seasonal driving of livestock between mountain and valley pastures"},
        {"name": "Silk weaving of Varanasi", "lat": 25.3176, "lon": 83.0063, "country": "India", "year": 2009, "category": "Traditional craftsmanship", "description": "Hand-woven Banarasi silk saris with gold and silver brocade"},
        {"name": "Ainu traditional dance", "lat": 43.0642, "lon": 141.3469, "country": "Japan", "year": 2009, "category": "Performing arts", "description": "Indigenous dance performed at ceremonies to honour gods and nature"},
        {"name": "Georgian Polyphonic Singing", "lat": 41.7151, "lon": 44.8271, "country": "Georgia", "year": 2008, "category": "Performing arts", "description": "Ancient multi-part vocal tradition with complex harmonies unique to the Caucasus"},
        {"name": "Mariachi", "lat": 20.6597, "lon": -103.3496, "country": "Mexico", "year": 2011, "category": "Performing arts", "description": "Traditional Mexican ensemble music with trumpets, violins and guitars"},
        {"name": "Carnival of Barranquilla", "lat": 10.9685, "lon": -74.7813, "country": "Colombia", "year": 2008, "category": "Social practices", "description": "Second largest carnival in the world blending indigenous, African and European traditions"},
        {"name": "Batik", "lat": -6.9175, "lon": 110.4195, "country": "Indonesia", "year": 2009, "category": "Traditional craftsmanship", "description": "Wax-resist dyeing technique on fabric with symbolic patterns"},
        {"name": "Capoeira", "lat": -12.9714, "lon": -38.5124, "country": "Brazil", "year": 2014, "category": "Performing arts", "description": "Afro-Brazilian martial art combining dance, acrobatics and music in a roda circle"},
        {"name": "Chinese shadow puppetry", "lat": 34.2619, "lon": 108.9390, "country": "China", "year": 2011, "category": "Performing arts", "description": "Silhouette puppet theatre using articulated leather figures behind lit screen"},
        {"name": "Falconry", "lat": 24.4539, "lon": 54.3773, "country": "UAE & 23 others", "year": 2021, "category": "Traditional knowledge", "description": "Art of training and flying birds of prey, practiced for millennia worldwide"},
        {"name": "Tsiattista improvised poetry", "lat": 35.1856, "lon": 33.3823, "country": "Cyprus", "year": 2024, "category": "Performing arts", "description": "Oral tradition of rhyming couplet improvisation in Cypriot Greek dialect"},
        {"name": "Samba de Roda", "lat": -12.5800, "lon": -38.9700, "country": "Brazil", "year": 2008, "category": "Performing arts", "description": "Afro-Brazilian circle dance with percussion, song and choreography from Bahia"},
        {"name": "Oud craftsmanship", "lat": 33.8869, "lon": 35.5131, "country": "Lebanon/Syria & others", "year": 2022, "category": "Traditional craftsmanship", "description": "Building the pear-shaped fretless lute, cornerstone of Middle Eastern music"},
        {"name": "Khoomei throat singing", "lat": 51.7167, "lon": 94.4333, "country": "Mongolia/Russia (Tuva)", "year": 2010, "category": "Performing arts", "description": "Overtone singing technique producing multiple pitches simultaneously"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 6. ENDANGERED HERITAGE (UNESCO DANGER LIST) (20+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_endangered_heritage():
    data = [
        {"name": "Old City of Jerusalem", "lat": 31.7767, "lon": 35.2345, "country": "Israel/Palestine", "year_listed": 1982, "threat": "Urban development, political conflict, deterioration of historic fabric"},
        {"name": "Chan Chan Archaeological Zone", "lat": -8.1064, "lon": -79.0750, "country": "Peru", "year_listed": 1986, "threat": "El Nino erosion, looting, encroachment, adobe degradation"},
        {"name": "Historic Centre of Vienna", "lat": 48.2082, "lon": 16.3738, "country": "Austria", "year_listed": 2017, "threat": "High-rise development project threatening historic skyline (removed 2023)"},
        {"name": "Rainforests of the Atsinanana", "lat": -15.4500, "lon": 49.7500, "country": "Madagascar", "year_listed": 2010, "threat": "Illegal logging of rosewood and ebony, lemur poaching"},
        {"name": "Liverpool Maritime Mercantile City", "lat": 53.4084, "lon": -2.9916, "country": "United Kingdom", "year_listed": 2012, "threat": "Waterfront development (delisted 2021 due to irreversible change)"},
        {"name": "Humberstone and Santa Laura Saltpeter Works", "lat": -20.2078, "lon": -69.7928, "country": "Chile", "year_listed": 2005, "threat": "Industrial ghost town vulnerability to earthquakes and wind erosion"},
        {"name": "Abu Mena", "lat": 30.8500, "lon": 29.6667, "country": "Egypt", "year_listed": 2001, "threat": "Rising water table causing collapse of underground structures"},
        {"name": "Tropical Rainforest Heritage of Sumatra", "lat": -2.5000, "lon": 101.5000, "country": "Indonesia", "year_listed": 2011, "threat": "Illegal logging, agricultural encroachment, poaching, road building"},
        {"name": "Virunga National Park", "lat": -1.0000, "lon": 29.2000, "country": "DR Congo", "year_listed": 1994, "threat": "Armed conflict, poaching, oil exploration, deforestation for charcoal"},
        {"name": "Garamba National Park", "lat": 4.0000, "lon": 29.5000, "country": "DR Congo", "year_listed": 1996, "threat": "Poaching of elephants and northern white rhinos, armed militia activity"},
        {"name": "Kahuzi-Biega National Park", "lat": -2.3000, "lon": 28.7500, "country": "DR Congo", "year_listed": 1997, "threat": "Mining (coltan), deforestation, gorilla poaching, armed groups"},
        {"name": "Okapi Wildlife Reserve", "lat": 1.5000, "lon": 28.5000, "country": "DR Congo", "year_listed": 1997, "threat": "Gold mining, poaching, civil unrest threatening endemic okapi"},
        {"name": "Salonga National Park", "lat": -2.0000, "lon": 21.0000, "country": "DR Congo", "year_listed": 1999, "threat": "Poaching of bonobos and elephants, lack of management capacity"},
        {"name": "Nan Madol", "lat": 6.8442, "lon": 158.3339, "country": "Micronesia", "year_listed": 2016, "threat": "Siltation, mangrove overgrowth, uncontrolled vegetation, sea-level rise"},
        {"name": "Coro and its Port", "lat": 11.4095, "lon": -69.6800, "country": "Venezuela", "year_listed": 2005, "threat": "Flood damage, inappropriate construction, poor conservation management"},
        {"name": "Historic Centre of Shakhrisyabz", "lat": 39.0500, "lon": 66.8333, "country": "Uzbekistan", "year_listed": 2016, "threat": "Demolition of medieval structures for a tourist park development"},
        {"name": "Selous Game Reserve", "lat": -9.0000, "lon": 37.5000, "country": "Tanzania", "year_listed": 2014, "threat": "Massive elephant poaching, proposed dam and uranium mining (delisted 2023)"},
        {"name": "Islands and Protected Areas of the Gulf of California", "lat": 28.0000, "lon": -112.5000, "country": "Mexico", "year_listed": 2019, "threat": "Illegal gillnet fishing causing vaquita porpoise extinction risk"},
        {"name": "Historic Town of Zabid", "lat": 14.1950, "lon": 43.3200, "country": "Yemen", "year_listed": 2000, "threat": "Replacement of traditional houses with concrete, conflict damage"},
        {"name": "Niokolo-Koba National Park", "lat": 13.0667, "lon": -12.7167, "country": "Senegal", "year_listed": 2007, "threat": "Poaching, dam construction on Gambia River, cattle grazing"},
        {"name": "East Rennell", "lat": -11.6667, "lon": 160.2500, "country": "Solomon Islands", "year_listed": 2013, "threat": "Logging, invasive species, climate change impacts on raised coral atoll"},
        {"name": "Birthplace of Jesus: Bethlehem", "lat": 31.7044, "lon": 35.2076, "country": "Palestine", "year_listed": 2012, "threat": "Water infiltration damage, political instability, roof deterioration"},
        {"name": "Ancient City of Aleppo", "lat": 36.2000, "lon": 37.1500, "country": "Syria", "year_listed": 2013, "threat": "Severe civil war damage to Umayyad Mosque, souks and citadel"},
        {"name": "Ancient City of Damascus", "lat": 33.5138, "lon": 36.2765, "country": "Syria", "year_listed": 2013, "threat": "Armed conflict, urban warfare damage to Old City quarters"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 7. MEMORY OF THE WORLD (25+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_memory_of_world():
    data = [
        {"name": "Gutenberg Bible", "lat": 49.9929, "lon": 8.2473, "country": "Germany", "year": 2001, "type": "Printed book", "description": "First substantial book printed with movable metal type, c.1455"},
        {"name": "Bayeux Tapestry", "lat": 49.2764, "lon": -0.7024, "country": "France", "year": 2007, "type": "Textile", "description": "70-metre embroidered cloth depicting the Norman Conquest of England (1066)"},
        {"name": "Magna Carta", "lat": 51.5074, "lon": -0.1278, "country": "United Kingdom", "year": 2009, "type": "Document", "description": "1215 charter of rights, foundation of constitutional law"},
        {"name": "Dead Sea Scrolls", "lat": 31.7741, "lon": 35.2042, "country": "Israel", "year": 2017, "type": "Manuscript", "description": "Oldest known manuscripts of the Hebrew Bible, discovered in Qumran caves"},
        {"name": "Book of Kells", "lat": 53.3438, "lon": -6.2546, "country": "Ireland", "year": 2011, "type": "Illuminated manuscript", "description": "9th-century masterpiece of Celtic art, the four Gospels in Latin"},
        {"name": "Codex Mendoza", "lat": 51.7520, "lon": -1.2577, "country": "UK (origin: Mexico)", "year": 2015, "type": "Codex", "description": "Aztec pictorial document created for the Spanish viceroy c.1541"},
        {"name": "Anne Frank Diaries", "lat": 52.3676, "lon": 4.8836, "country": "Netherlands", "year": 2009, "type": "Diary", "description": "Personal diary of a Jewish girl hiding during the Nazi occupation of Amsterdam"},
        {"name": "Behistun Inscription", "lat": 34.3867, "lon": 47.4378, "country": "Iran", "year": 2007, "type": "Rock inscription", "description": "Multilingual Achaemenid inscription that unlocked cuneiform script decipherment"},
        {"name": "Codex Suprasliensis", "lat": 53.2078, "lon": 23.3408, "country": "Poland/Russia/Slovenia", "year": 2007, "type": "Manuscript", "description": "Oldest Cyrillic manuscript, 10th-century Old Church Slavonic texts"},
        {"name": "Human Rights Declaration (1789)", "lat": 48.8566, "lon": 2.3522, "country": "France", "year": 2003, "type": "Document", "description": "French Declaration of the Rights of Man and of the Citizen"},
        {"name": "Diary of Mao Zedong", "lat": 39.9042, "lon": 116.4074, "country": "China", "year": 2013, "type": "Manuscript", "description": "Original manuscripts of Mao's Long March period records"},
        {"name": "Hereford Mappa Mundi", "lat": 52.0567, "lon": -2.7160, "country": "United Kingdom", "year": 2007, "type": "Map", "description": "Largest known medieval map of the world, c.1300, depicting 500 drawings"},
        {"name": "Treaty of Waitangi", "lat": -35.2644, "lon": 174.0920, "country": "New Zealand", "year": 1997, "type": "Document", "description": "1840 founding document between British Crown and Maori chiefs"},
        {"name": "Original Negative of The Wizard of Oz", "lat": 34.0522, "lon": -118.2437, "country": "USA", "year": 2009, "type": "Film", "description": "1939 original camera negative of the iconic Technicolor film"},
        {"name": "Emanuel Swedenborg Collection", "lat": 59.3293, "lon": 18.0686, "country": "Sweden", "year": 2005, "type": "Manuscript", "description": "Complete works of the 18th-century scientist, philosopher and mystic"},
        {"name": "Tabula Rogeriana", "lat": 38.1157, "lon": 13.3615, "country": "Italy (origin: Sicily)", "year": 2015, "type": "Map", "description": "1154 world map by al-Idrisi, most advanced medieval world geography"},
        {"name": "Phoenician Alphabet", "lat": 34.1170, "lon": 35.6500, "country": "Lebanon", "year": 2005, "type": "Inscription", "description": "Sarcophagus of Ahiram with earliest known Phoenician alphabet inscription"},
        {"name": "Astrid Lindgren Archives", "lat": 59.3293, "lon": 18.0686, "country": "Sweden", "year": 2005, "type": "Literary archive", "description": "Complete manuscripts and letters of the Pippi Longstocking author"},
        {"name": "Nanjing Massacre Documents", "lat": 32.0603, "lon": 118.7969, "country": "China", "year": 2015, "type": "Archival documents", "description": "Documents, photographs and films recording the 1937 atrocity"},
        {"name": "Vienna Dioscurides", "lat": 48.2082, "lon": 16.3738, "country": "Austria", "year": 1997, "type": "Illuminated manuscript", "description": "6th-century illustrated herbal manuscript, oldest surviving pharmacopoeia"},
        {"name": "Codex Argenteus", "lat": 59.8586, "lon": 17.6389, "country": "Sweden", "year": 2011, "type": "Manuscript", "description": "6th-century Gothic Bible written in silver and gold ink on purple parchment"},
        {"name": "Tuol Sleng Genocide Museum Archives", "lat": 11.5493, "lon": 104.9172, "country": "Cambodia", "year": 2009, "type": "Archive", "description": "Photographs and documents from the Khmer Rouge S-21 security prison"},
        {"name": "Theodor Herzl Archives", "lat": 31.7857, "lon": 35.2007, "country": "Israel", "year": 2013, "type": "Personal archive", "description": "Diaries, letters and manuscripts of the founder of modern Zionism"},
        {"name": "Columbus Letter", "lat": 40.4168, "lon": -3.7038, "country": "Spain", "year": 2005, "type": "Letter", "description": "1493 letter announcing the discovery of the New World"},
        {"name": "Persian Illustrated & Illuminated Manuscripts", "lat": 35.6892, "lon": 51.3890, "country": "Iran", "year": 2007, "type": "Manuscript", "description": "Masterpieces of Persian miniature painting from Shahnameh and other epics"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 8. CREATIVE CITIES NETWORK (30+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_creative_cities():
    data = [
        {"name": "Edinburgh", "lat": 55.9533, "lon": -3.1883, "country": "United Kingdom", "year": 2004, "category": "Literature", "description": "First UNESCO City of Literature, home to the Edinburgh Festival and Fringe"},
        {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816, "country": "Argentina", "year": 2005, "category": "Design", "description": "Latin American design capital with vibrant art deco and contemporary architecture"},
        {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "year": 2005, "category": "Design", "description": "Global hub for industrial and graphic design, Bauhaus heritage"},
        {"name": "Seville", "lat": 37.3886, "lon": -5.9823, "country": "Spain", "year": 2006, "category": "Music", "description": "Flamenco capital with deep musical traditions and opera heritage"},
        {"name": "Bologna", "lat": 44.4949, "lon": 11.3426, "country": "Italy", "year": 2006, "category": "Music", "description": "Rich musical tradition, oldest university in Europe, opera birthplace"},
        {"name": "Santa Fe", "lat": 35.6870, "lon": -105.9378, "country": "USA", "year": 2005, "category": "Design & Crafts", "description": "Adobe architecture and vibrant arts market blending Native American and Spanish heritage"},
        {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631, "country": "Australia", "year": 2008, "category": "Literature", "description": "UNESCO City of Literature with thriving independent publishers and literary festivals"},
        {"name": "Montreal", "lat": 45.5017, "lon": -73.5673, "country": "Canada", "year": 2006, "category": "Design", "description": "Bilingual design hub with strong fashion, gaming and architectural design industries"},
        {"name": "Kobe", "lat": 34.6901, "lon": 135.1956, "country": "Japan", "year": 2008, "category": "Design", "description": "Creative design city rebuilt after the 1995 earthquake with innovative urban planning"},
        {"name": "Lyon", "lat": 45.7640, "lon": 4.8357, "country": "France", "year": 2008, "category": "Media Arts", "description": "Birthplace of cinema (Lumiere brothers), pioneer in digital arts and light festivals"},
        {"name": "Ghent", "lat": 51.0543, "lon": 3.7174, "country": "Belgium", "year": 2009, "category": "Music", "description": "Vibrant music scene spanning medieval polyphony to contemporary electronic music"},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Australia", "year": 2010, "category": "Film", "description": "Major film production hub, home to Fox Studios Australia and Sydney Film Festival"},
        {"name": "Bradford", "lat": 53.7960, "lon": -1.7594, "country": "United Kingdom", "year": 2009, "category": "Film", "description": "First UNESCO City of Film, home to National Science and Media Museum"},
        {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "country": "India", "year": 2015, "category": "Crafts & Folk Art", "description": "Pink City renowned for textile block printing, gem cutting and metalwork"},
        {"name": "Icheon", "lat": 37.2792, "lon": 127.4425, "country": "South Korea", "year": 2010, "category": "Crafts & Folk Art", "description": "Centre of Korean ceramic tradition, famous for celadon pottery since Goryeo dynasty"},
        {"name": "Fabriano", "lat": 43.3397, "lon": 12.9044, "country": "Italy", "year": 2013, "category": "Crafts & Folk Art", "description": "Medieval papermaking centre, home of watermark invention and artisan traditions"},
        {"name": "Enghien-les-Bains", "lat": 48.9697, "lon": 2.3117, "country": "France", "year": 2013, "category": "Media Arts", "description": "Spa town transformed into digital arts laboratory with immersive installations"},
        {"name": "Prague", "lat": 50.0755, "lon": 14.4378, "country": "Czech Republic", "year": 2014, "category": "Literature", "description": "Literary capital of Kafka, Kundera and Havel, major publishing centre"},
        {"name": "Reykjavik", "lat": 64.1466, "lon": -21.9426, "country": "Iceland", "year": 2014, "category": "Literature", "description": "City of sagas with the world's highest per-capita book publication rate"},
        {"name": "Pesaro", "lat": 43.9098, "lon": 12.9131, "country": "Italy", "year": 2017, "category": "Music", "description": "Birthplace of Rossini, hosts the annual Rossini Opera Festival since 1980"},
        {"name": "Galway", "lat": 53.2707, "lon": -9.0568, "country": "Ireland", "year": 2014, "category": "Film", "description": "West Ireland film hub with Galway Film Fleadh and Irish-language cinema tradition"},
        {"name": "Gastronomy: Tucson", "lat": 32.2226, "lon": -110.9747, "country": "USA", "year": 2015, "category": "Gastronomy", "description": "First US City of Gastronomy, 4,000-year Sonoran Desert food heritage"},
        {"name": "Gastronomy: Parma", "lat": 44.8015, "lon": 10.3279, "country": "Italy", "year": 2015, "category": "Gastronomy", "description": "Parmesan cheese and Parma ham capital, cradle of Italian food culture"},
        {"name": "Gastronomy: Hyderabad", "lat": 17.3850, "lon": 78.4867, "country": "India", "year": 2019, "category": "Gastronomy", "description": "Biryani capital with Mughlai-Deccan fusion cuisine and street food culture"},
        {"name": "Dakar", "lat": 14.7167, "lon": -17.4677, "country": "Senegal", "year": 2014, "category": "Media Arts", "description": "Hub of African digital art, Dak'Art Biennale and West African creative industries"},
        {"name": "Bandung", "lat": -6.9175, "lon": 107.6191, "country": "Indonesia", "year": 2015, "category": "Design", "description": "Indonesian creative economy hub with Art Deco heritage and design start-ups"},
        {"name": "Krakow", "lat": 50.0647, "lon": 19.9450, "country": "Poland", "year": 2013, "category": "Literature", "description": "City of Szymborska and Lem, thriving literary scene and independent bookshops"},
        {"name": "Hanoi", "lat": 21.0285, "lon": 105.8542, "country": "Vietnam", "year": 2019, "category": "Design", "description": "Ancient city blending French colonial and Vietnamese design with craft villages"},
        {"name": "Santos", "lat": -23.9608, "lon": -46.3336, "country": "Brazil", "year": 2015, "category": "Film", "description": "Brazilian film city, coffee culture heritage and coastal creative industries"},
        {"name": "Idanha-a-Nova", "lat": 39.9200, "lon": -7.2400, "country": "Portugal", "year": 2015, "category": "Music", "description": "Small rural municipality revitalized through world music festival Boom"},
        {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "country": "Indonesia", "year": 2023, "category": "Film", "description": "Rapidly growing Southeast Asian film industry hub with diverse storytelling"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 9. LOST / DESTROYED HERITAGE (curated)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_lost_heritage():
    data = [
        {"name": "Buddhas of Bamiyan", "lat": 34.8325, "lon": 67.8275, "country": "Afghanistan", "year_destroyed": 2001, "era_built": "6th century", "description": "Two colossal Buddha statues (55 m and 38 m) dynamited by the Taliban"},
        {"name": "Palmyra (Temple of Bel)", "lat": 34.5509, "lon": 38.2686, "country": "Syria", "year_destroyed": 2015, "era_built": "32 AD", "description": "Roman-era temple destroyed by ISIS/ISIL, iconic Silk Road oasis city"},
        {"name": "Notre-Dame de Paris (fire)", "lat": 48.8530, "lon": 2.3499, "country": "France", "year_destroyed": 2019, "era_built": "1163-1345", "description": "Gothic cathedral spire and roof destroyed by accidental fire (restored 2024)"},
        {"name": "Library of Alexandria", "lat": 31.2001, "lon": 29.9187, "country": "Egypt", "year_destroyed": -48, "era_built": "3rd century BC", "description": "Greatest library of antiquity, gradual destruction from 48 BC to 642 AD"},
        {"name": "Old Summer Palace (Yuanmingyuan)", "lat": 40.0089, "lon": 116.3008, "country": "China", "year_destroyed": 1860, "era_built": "1707", "description": "Imperial garden palace looted and burned by Anglo-French forces in Second Opium War"},
        {"name": "Mostar Bridge (Stari Most)", "lat": 43.3373, "lon": 17.8153, "country": "Bosnia", "year_destroyed": 1993, "era_built": "1566", "description": "Ottoman stone arch bridge destroyed by tank shells in Bosnian War (rebuilt 2004)"},
        {"name": "Nalanda University", "lat": 25.1367, "lon": 85.4500, "country": "India", "year_destroyed": 1193, "era_built": "5th century", "description": "Ancient Buddhist centre of learning burned by Bakhtiyar Khilji's army"},
        {"name": "Tomb of Jonah (Nebi Yunus)", "lat": 36.3544, "lon": 43.1500, "country": "Iraq", "year_destroyed": 2014, "era_built": "8th century BC", "description": "Ancient Nineveh shrine and mosque destroyed by ISIS/ISIL explosives"},
        {"name": "Timbuktu Mausoleums", "lat": 16.7735, "lon": -3.0074, "country": "Mali", "year_destroyed": 2012, "era_built": "14th-15th century", "description": "Sufi saints' tombs destroyed by Ansar Dine militants (rebuilt with UNESCO aid)"},
        {"name": "Colossus of Rhodes", "lat": 36.4510, "lon": 28.2278, "country": "Greece", "year_destroyed": -226, "era_built": "3rd century BC", "description": "30-metre bronze statue of Helios, toppled by earthquake after 54 years"},
        {"name": "National Museum of Brazil (fire)", "lat": -22.9053, "lon": -43.2261, "country": "Brazil", "year_destroyed": 2018, "era_built": "1818", "description": "20 million artifacts lost in fire at the oldest scientific institution in Brazil"},
        {"name": "Bamako Manuscripts (partial)", "lat": 12.6392, "lon": -8.0029, "country": "Mali", "year_destroyed": 2013, "era_built": "13th-16th century", "description": "Some of 377,000 Timbuktu manuscripts burned during Islamist occupation"},
        {"name": "Crac des Chevaliers (damaged)", "lat": 34.7569, "lon": 36.2936, "country": "Syria", "year_destroyed": 2013, "era_built": "1031-1271", "description": "Crusader castle damaged by airstrikes and shelling during Syrian Civil War"},
        {"name": "Lighthouse of Alexandria", "lat": 31.2139, "lon": 29.8856, "country": "Egypt", "year_destroyed": 1480, "era_built": "3rd century BC", "description": "One of the Seven Wonders, gradually destroyed by earthquakes over 1,000 years"},
        {"name": "Temple of Artemis at Ephesus", "lat": 37.9497, "lon": 27.3639, "country": "Turkey", "year_destroyed": 356, "era_built": "550 BC", "description": "Greek temple destroyed by arsonist Herostratus, rebuilt, then razed by Goths"},
        {"name": "Baalbek (partial damage)", "lat": 34.0066, "lon": 36.2039, "country": "Lebanon", "year_destroyed": 2020, "era_built": "1st century BC", "description": "Roman temple complex sustaining ongoing conflict-zone deterioration"},
        {"name": "Nimrud (Kalhu)", "lat": 36.0997, "lon": 43.3283, "country": "Iraq", "year_destroyed": 2015, "era_built": "13th century BC", "description": "Assyrian capital bulldozed and dynamited by ISIS/ISIL"},
        {"name": "Khmer Rouge Destruction of Angkor (partial)", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "year_destroyed": 1975, "era_built": "9th-15th century", "description": "Some temples looted and damaged during Khmer Rouge period and subsequent conflict"},
        {"name": "Coventry Cathedral", "lat": 52.4081, "lon": -1.5075, "country": "United Kingdom", "year_destroyed": 1940, "era_built": "14th century", "description": "Medieval cathedral destroyed by Luftwaffe bombing, ruins preserved beside new cathedral"},
        {"name": "Dresden Frauenkirche", "lat": 51.0517, "lon": 13.7412, "country": "Germany", "year_destroyed": 1945, "era_built": "1743", "description": "Baroque Lutheran church collapsed after Allied firebombing (rebuilt 2005)"},
        {"name": "Parthenon (partial)", "lat": 37.9715, "lon": 23.7267, "country": "Greece", "year_destroyed": 1687, "era_built": "447 BC", "description": "Venetian mortar hit Ottoman gunpowder stored in the temple, blowing out the centre"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# 10. TENTATIVE LIST HIGHLIGHTS (25+)
# =====================================================================
@st.cache_data(ttl=3600)
def _get_tentative_list():
    data = [
        {"name": "Great Rift Valley (Kenya Lakes)", "lat": -0.3000, "lon": 36.0000, "country": "Kenya", "year_submitted": 2010, "category": "Natural", "description": "Chain of alkaline lakes with millions of flamingos in the East African Rift"},
        {"name": "Jericho: Tell es-Sultan", "lat": 31.8700, "lon": 35.4444, "country": "Palestine", "year_submitted": 2012, "category": "Cultural", "description": "Oldest known continuously inhabited city, 10,000+ years of occupation layers"},
        {"name": "Viking Sites in North America", "lat": 51.5961, "lon": -55.5330, "country": "Canada", "year_submitted": 2018, "category": "Cultural", "description": "L'Anse aux Meadows and potential additional Norse settlement evidence"},
        {"name": "Salar de Uyuni", "lat": -20.1338, "lon": -67.4891, "country": "Bolivia", "year_submitted": 2013, "category": "Natural", "description": "World's largest salt flat at 10,582 km2, surreal mirror landscape"},
        {"name": "Royal Court of Tiebele", "lat": 11.0833, "lon": -1.0667, "country": "Burkina Faso", "year_submitted": 2012, "category": "Cultural", "description": "Kassena painted mud-brick architecture with geometric Gurunsi murals"},
        {"name": "Table Mountain", "lat": -33.9625, "lon": 18.4000, "country": "South Africa", "year_submitted": 2004, "category": "Natural", "description": "Iconic flat-topped mountain with unique Cape fynbos floral kingdom"},
        {"name": "Phong Nha-Ke Bang Extension", "lat": 17.5000, "lon": 106.2000, "country": "Vietnam", "year_submitted": 2017, "category": "Natural", "description": "Extended cave system including Son Doong, world's largest cave passage"},
        {"name": "Underground Cities of Cappadocia", "lat": 38.6333, "lon": 34.8333, "country": "Turkey", "year_submitted": 2000, "category": "Cultural", "description": "Massive subterranean cities including Derinkuyu (18 levels deep)"},
        {"name": "Rock Islands Southern Lagoon Extension", "lat": 7.1500, "lon": 134.3500, "country": "Palau", "year_submitted": 2017, "category": "Mixed", "description": "Limestone islands, marine lakes with isolated jellyfish populations"},
        {"name": "Chocolate Hills", "lat": 9.8167, "lon": 124.0833, "country": "Philippines", "year_submitted": 2006, "category": "Natural", "description": "1,776 uniformly cone-shaped hills turning brown in dry season"},
        {"name": "Lena Pillars Expansion", "lat": 61.1333, "lon": 128.6667, "country": "Russia", "year_submitted": 2012, "category": "Natural", "description": "Expanded protection of Cambrian rock pillars along the Lena River"},
        {"name": "City of Mombasa", "lat": -4.0435, "lon": 39.6682, "country": "Kenya", "year_submitted": 1997, "category": "Cultural", "description": "Swahili trading port with Fort Jesus and Arab-Portuguese architectural blend"},
        {"name": "Ennedi Plateau Extension", "lat": 17.3000, "lon": 21.8500, "country": "Chad", "year_submitted": 2016, "category": "Mixed", "description": "Sandstone arches, rock art galleries and Saharan endemic species"},
        {"name": "Banks of the Seine Extension (Paris)", "lat": 48.8566, "lon": 2.3522, "country": "France", "year_submitted": 2017, "category": "Cultural", "description": "Extended protection along the Seine including additional Paris landmarks"},
        {"name": "Church of the Nativity Extension", "lat": 31.7044, "lon": 35.2076, "country": "Palestine", "year_submitted": 2019, "category": "Cultural", "description": "Extended buffer zone for the birthplace of Jesus in Bethlehem"},
        {"name": "Dogon Country Landscape", "lat": 14.3500, "lon": -3.5000, "country": "Mali", "year_submitted": 2017, "category": "Mixed", "description": "Cliff dwellings, granaries and ancient Tellem cave burials on Bandiagara escarpment"},
        {"name": "Trang An Extension", "lat": 20.2500, "lon": 105.9000, "country": "Vietnam", "year_submitted": 2018, "category": "Mixed", "description": "Limestone karst landscape with caves bearing evidence of human activity 30,000 years"},
        {"name": "Historic Centre of Paramaribo Extension", "lat": 5.8520, "lon": -55.2038, "country": "Suriname", "year_submitted": 2013, "category": "Cultural", "description": "Dutch colonial wooden architecture blended with tropical adaptation"},
        {"name": "Nazca Lines Extension", "lat": -14.7350, "lon": -75.1300, "country": "Peru", "year_submitted": 2016, "category": "Cultural", "description": "Additional geoglyphs and Palpa Lines beyond current World Heritage boundary"},
        {"name": "Lake Ohrid Region Extension", "lat": 41.1131, "lon": 20.8016, "country": "Albania/North Macedonia", "year_submitted": 2019, "category": "Mixed", "description": "Oldest lake in Europe with unique biodiversity and ancient settlements"},
        {"name": "Armenian Monastic Ensembles of Iran", "lat": 38.9833, "lon": 44.5833, "country": "Iran", "year_submitted": 2008, "category": "Cultural", "description": "Medieval Armenian churches and monasteries in Iranian Azerbaijan"},
        {"name": "Mount Ararat", "lat": 39.7000, "lon": 44.3000, "country": "Turkey", "year_submitted": 2000, "category": "Natural", "description": "Turkey's highest peak (5,137 m), glacial-capped dormant volcano, Noah's Ark legend"},
        {"name": "Ai-Petri / Crimean Mountains", "lat": 44.4525, "lon": 34.0551, "country": "Ukraine", "year_submitted": 2015, "category": "Natural", "description": "Mediterranean-climate mountain landscapes with rich endemic flora"},
        {"name": "Harar Jugol Extension", "lat": 9.3133, "lon": 42.1200, "country": "Ethiopia", "year_submitted": 2016, "category": "Cultural", "description": "Extended protection of the walled Islamic city and hyena feeding traditions"},
        {"name": "Goebekli Tepe (Extended)", "lat": 37.2233, "lon": 38.9225, "country": "Turkey", "year_submitted": 2023, "category": "Cultural", "description": "Additional Neolithic enclosures surrounding the world's oldest known temple complex"},
    ]
    return pd.DataFrame(data)


# =====================================================================
# MARKER COLOUR MAPS PER MODE
# =====================================================================
MODE_COLORS = {
    "World Heritage Cultural": ACCENT_VIOLET,
    "World Heritage Natural": ACCENT_EMERALD,
    "Biosphere Reserves": ACCENT_TEAL,
    "Global Geoparks": ACCENT_AMBER,
    "Intangible Cultural Heritage": ACCENT_PINK,
    "Endangered Heritage": ACCENT_RED,
    "Memory of the World": ACCENT_CYAN,
    "Creative Cities Network": ACCENT_BLUE,
    "Lost/Destroyed Heritage": ACCENT_ORANGE,
    "Tentative List Highlights": "#a855f7",
}


# =====================================================================
# BUILD MAP + CHART + STATS  (one per mode)
# =====================================================================

def _render_cultural_sites():
    """Mode 1: World Heritage Cultural Sites."""
    df = _get_cultural_sites()
    color = MODE_COLORS["World Heritage Cultural"]

    # --- Stats ---
    st.markdown("#### World Heritage Cultural Sites")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Earliest Inscription", int(df["year"].min()))
    c4.metric("Latest Inscription", int(df["year"].max()))

    # --- Chart: inscriptions by decade ---
    df_chart = df.copy()
    df_chart["decade"] = (df_chart["year"] // 10) * 10
    decade_counts = df_chart["decade"].value_counts().sort_index()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar([str(d) + "s" for d in decade_counts.index], decade_counts.values, color=color)
    ax.set_xlabel("Decade")
    ax.set_ylabel("Inscriptions")
    ax.set_title("Cultural Sites Inscribed by Decade")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    # --- Map ---
    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Year Inscribed: {row['year']}<br>"
            f"Description: {escape(str(row['description'])[:120])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    # --- Table & Download ---
    st.dataframe(df[["name", "country", "year", "description"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_cultural_sites.csv",
                       "text/csv", key="dl_cultural")


def _render_natural_sites():
    """Mode 2: World Heritage Natural Sites."""
    df = _get_natural_sites()
    color = MODE_COLORS["World Heritage Natural"]

    st.markdown("#### World Heritage Natural Sites")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Earliest", int(df["year"].min()))
    c4.metric("Latest", int(df["year"].max()))

    # Chart: by country (top 10)
    top_countries = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    bars = ax.barh(top_countries.index[::-1], top_countries.values[::-1],
                   color=[_color_for(i) for i in range(len(top_countries))])
    ax.set_xlabel("Number of Sites")
    ax.set_title("Top Countries by Natural Heritage Sites")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Year: {row['year']}<br>"
            f"{escape(str(row['description'])[:120])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year", "description"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_natural_sites.csv",
                       "text/csv", key="unesm_dl_natural")


def _render_biosphere_reserves():
    """Mode 3: UNESCO Biosphere Reserves."""
    df = _get_biosphere_reserves()
    color = MODE_COLORS["Biosphere Reserves"]

    st.markdown("#### UNESCO Biosphere Reserves")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Reserves", len(df))
    c2.metric("Countries", df["country"].nunique())
    largest = df.loc[df["area_km2"].idxmax()]
    c3.metric("Largest", f"{largest['name'][:20]}...")
    c4.metric("Total Area", f"{df['area_km2'].sum():,.0f} km2")

    # Chart: area comparison (top 10)
    df_sorted = df.nlargest(10, "area_km2")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(df_sorted["name"].values[::-1], df_sorted["area_km2"].values[::-1],
            color=[_color_for(i) for i in range(len(df_sorted))])
    ax.set_xlabel("Area (km2)")
    ax.set_title("Largest Biosphere Reserves")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        radius = max(5, min(15, row["area_km2"] / 3000))
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Year: {row['year']}<br>"
            f"Area: {row['area_km2']:,.0f} km2<br>"
            f"Ecosystems: {escape(str(row['ecosystems'])[:100])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year", "area_km2", "ecosystems"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_biosphere_reserves.csv",
                       "text/csv", key="dl_biosphere")


def _render_geoparks():
    """Mode 4: UNESCO Global Geoparks."""
    df = _get_geoparks()
    color = MODE_COLORS["Global Geoparks"]

    st.markdown("#### UNESCO Global Geoparks")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Geoparks", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Earliest Designated", int(df["year"].min()))
    c4.metric("Latest Designated", int(df["year"].max()))

    # Chart: geoparks by country
    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar(country_counts.index, country_counts.values,
           color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Country")
    ax.set_ylabel("Number of Geoparks")
    ax.set_title("Geoparks by Country")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Year: {row['year']}<br>"
            f"Features: {escape(str(row['geological_features'])[:120])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year", "geological_features"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_geoparks.csv",
                       "text/csv", key="dl_geoparks")


def _render_intangible_heritage():
    """Mode 5: Intangible Cultural Heritage."""
    df = _get_intangible_heritage()
    color = MODE_COLORS["Intangible Cultural Heritage"]

    cat_colors = {cat: _color_for(i) for i, cat in enumerate(df["category"].unique())}

    st.markdown("#### Intangible Cultural Heritage")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Elements", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Categories", df["category"].nunique())
    c4.metric("Year Range", f"{int(df['year'].min())}-{int(df['year'].max())}")

    # Chart: by category
    cat_counts = df["category"].value_counts()
    fig, ax = _dark_fig(figsize=(8, 5))
    wedges, texts, autotexts = ax.pie(
        cat_counts.values,
        labels=cat_counts.index,
        autopct="%1.0f%%",
        colors=[_color_for(i) for i in range(len(cat_counts))],
        textprops={"color": TEXT_PRIMARY, "fontsize": 9},
    )
    for t in autotexts:
        t.set_color(TEXT_PRIMARY)
    ax.set_title("Intangible Heritage by Category")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=700)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        c = cat_colors.get(row["category"], color)
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Year: {row['year']}<br>"
            f"Category: {escape(str(row['category']))}<br>"
            f"{escape(str(row['description'])[:120])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year", "category", "description"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_intangible_heritage.csv",
                       "text/csv", key="dl_intangible")


def _render_endangered_heritage():
    """Mode 6: Endangered Heritage (UNESCO Danger List)."""
    df = _get_endangered_heritage()
    color = MODE_COLORS["Endangered Heritage"]

    st.markdown("#### Endangered Heritage Sites")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites on Danger List", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Earliest Listing", int(df["year_listed"].min()))
    c4.metric("Latest Listing", int(df["year_listed"].max()))

    # Chart: danger listings by decade
    df_chart = df.copy()
    df_chart["decade"] = (df_chart["year_listed"] // 10) * 10
    decade_counts = df_chart["decade"].value_counts().sort_index()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar([str(d) + "s" for d in decade_counts.index], decade_counts.values, color=ACCENT_RED)
    ax.set_xlabel("Decade")
    ax.set_ylabel("Sites Listed")
    ax.set_title("Sites Added to Danger List by Decade")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Danger-listed: {row['year_listed']}<br>"
            f"Threat: {escape(str(row['threat'])[:140])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year_listed", "threat"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_endangered_heritage.csv",
                       "text/csv", key="dl_endangered")


def _render_memory_of_world():
    """Mode 7: Memory of the World Register."""
    df = _get_memory_of_world()
    color = MODE_COLORS["Memory of the World"]

    type_colors = {t: _color_for(i) for i, t in enumerate(df["type"].unique())}

    st.markdown("#### Memory of the World")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Documents", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Document Types", df["type"].nunique())
    c4.metric("Year Range", f"{int(df['year'].min())}-{int(df['year'].max())}")

    # Chart: by document type
    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(type_counts.index[::-1], type_counts.values[::-1],
            color=[_color_for(i) for i in range(len(type_counts))])
    ax.set_xlabel("Count")
    ax.set_title("Memory of the World by Document Type")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        c = type_colors.get(row["type"], color)
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Year Inscribed: {row['year']}<br>"
            f"Type: {escape(str(row['type']))}<br>"
            f"{escape(str(row['description'])[:120])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year", "type", "description"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_memory_of_world.csv",
                       "text/csv", key="dl_memory")


def _render_creative_cities():
    """Mode 8: UNESCO Creative Cities Network."""
    df = _get_creative_cities()
    color = MODE_COLORS["Creative Cities Network"]

    cat_colors = {cat: _color_for(i) for i, cat in enumerate(df["category"].unique())}

    st.markdown("#### UNESCO Creative Cities Network")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Cities", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Categories", df["category"].nunique())
    c4.metric("Year Range", f"{int(df['year'].min())}-{int(df['year'].max())}")

    # Chart: by creative category
    cat_counts = df["category"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar(cat_counts.index, cat_counts.values,
           color=[cat_colors.get(c, color) for c in cat_counts.index])
    ax.set_xlabel("Category")
    ax.set_ylabel("Number of Cities")
    ax.set_title("Creative Cities by Category")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        c = cat_colors.get(row["category"], color)
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Category: {escape(str(row['category']))}<br>"
            f"Year: {row['year']}<br>"
            f"{escape(str(row['description'])[:120])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(str(row['name']))} ({escape(str(row['category']))})",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year", "category", "description"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_creative_cities.csv",
                       "text/csv", key="dl_creative")


def _render_lost_heritage():
    """Mode 9: Lost / Destroyed Heritage."""
    df = _get_lost_heritage()
    color = MODE_COLORS["Lost/Destroyed Heritage"]

    st.markdown("#### Lost / Destroyed Heritage")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(df))
    c2.metric("Countries", df["country"].nunique())
    modern = df[df["year_destroyed"] >= 1900]
    c3.metric("Destroyed since 1900", len(modern))
    conflict = df[df["description"].str.contains("war|ISIS|Taliban|conflict|bomb", case=False, na=False)]
    c4.metric("Conflict-related", len(conflict))

    # Chart: destructions timeline
    df_chart = df[df["year_destroyed"] >= 0].copy()
    df_chart["century"] = (df_chart["year_destroyed"] // 100) * 100
    century_counts = df_chart["century"].value_counts().sort_index()
    fig, ax = _dark_fig(figsize=(10, 4))
    labels = [f"{int(c)}s" for c in century_counts.index]
    ax.bar(labels, century_counts.values, color=ACCENT_ORANGE)
    ax.set_xlabel("Century")
    ax.set_ylabel("Destructions")
    ax.set_title("Heritage Destructions by Century (CE)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Built: {escape(str(row['era_built']))}<br>"
            f"Destroyed: {row['year_destroyed']}<br>"
            f"{escape(str(row['description'])[:140])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year_destroyed", "era_built", "description"]],
                 width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_lost_heritage.csv",
                       "text/csv", key="dl_lost")


def _render_tentative_list():
    """Mode 10: Tentative List Highlights."""
    df = _get_tentative_list()
    color = MODE_COLORS["Tentative List Highlights"]

    cat_colors = {"Cultural": ACCENT_VIOLET, "Natural": ACCENT_EMERALD, "Mixed": ACCENT_AMBER}

    st.markdown("#### Tentative List Highlights")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Cultural", len(df[df["category"] == "Cultural"]))
    c4.metric("Natural / Mixed", len(df[df["category"] != "Cultural"]))

    # Chart: by category
    cat_counts = df["category"].value_counts()
    fig, ax = _dark_fig(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        cat_counts.values,
        labels=cat_counts.index,
        autopct="%1.0f%%",
        colors=[cat_colors.get(c, color) for c in cat_counts.index],
        textprops={"color": TEXT_PRIMARY, "fontsize": 11},
    )
    for t in autotexts:
        t.set_color(TEXT_PRIMARY)
    ax.set_title("Tentative List by Category")
    plt.tight_layout()
    st.image(_fig_to_bytes(fig), width=600)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        c = cat_colors.get(row["category"], color)
        popup_html = (
            f"<b>{escape(str(row['name']))}</b><br>"
            f"Country: {escape(str(row['country']))}<br>"
            f"Category: {escape(str(row['category']))}<br>"
            f"Submitted: {row['year_submitted']}<br>"
            f"{escape(str(row['description'])[:120])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(str(row["name"])),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "year_submitted", "category", "description"]],
                 width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "unesco_tentative_list.csv",
                       "text/csv", key="dl_tentative")


# =====================================================================
# MAP OPTIONS REGISTRY
# =====================================================================
MAP_OPTIONS = {
    "World Heritage Cultural": _render_cultural_sites,
    "World Heritage Natural": _render_natural_sites,
    "Biosphere Reserves": _render_biosphere_reserves,
    "Global Geoparks": _render_geoparks,
    "Intangible Cultural Heritage": _render_intangible_heritage,
    "Endangered Heritage": _render_endangered_heritage,
    "Memory of the World": _render_memory_of_world,
    "Creative Cities Network": _render_creative_cities,
    "Lost/Destroyed Heritage": _render_lost_heritage,
    "Tentative List Highlights": _render_tentative_list,
}


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
def render_unesco_maps_tab():
    """Main entry point for the UNESCO & World Heritage Maps tab."""
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001f3db\ufe0f UNESCO & World Heritage</h4>'
        '<p>World Heritage sites, biosphere reserves, geoparks, '
        'intangible heritage &amp; endangered sites</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected = st.radio(
        "Select Mode",
        list(MAP_OPTIONS.keys()),
        horizontal=True,
        key="unesco_maps_mode",
    )

    if st.button("Generate Map", key="unesco_maps_generate", type="primary"):
        with st.spinner("Building UNESCO map..."):
            MAP_OPTIONS[selected]()
    else:
        st.info("Select a mode above and click **Generate Map** to explore UNESCO heritage data.")


# =====================================================================
# Allow standalone testing
# =====================================================================
if __name__ == "__main__":
    st.set_page_config(page_title="UNESCO & World Heritage", layout="wide")
    render_unesco_maps_tab()
