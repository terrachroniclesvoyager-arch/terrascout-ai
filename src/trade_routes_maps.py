# -*- coding: utf-8 -*-
"""
Ancient Trade Routes & Paths module for TerraScout AI.
Visualizes 10 historical and modern trade routes on interactive Folium maps
with curated waypoints, polyline routes, historical context, and data tables.
All data is curated/embedded — no API keys required.
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

# ═══════════════════════════════════════════════════════════════
# ROUTE COLOR PALETTE
# ═══════════════════════════════════════════════════════════════
ROUTE_COLORS = {
    "primary": "#06b6d4",
    "secondary": "#8b5cf6",
    "tertiary": "#10b981",
    "quaternary": "#f59e0b",
    "quinary": "#ec4899",
    "senary": "#ef4444",
    "septenary": "#3b82f6",
    "octonary": "#f97316",
    "nonary": "#a855f7",
    "denary": "#14b8a6",
}

CITY_COLORS = {
    "major": "#f59e0b",
    "port": "#06b6d4",
    "oasis": "#10b981",
    "market": "#ec4899",
    "capital": "#ef4444",
    "mine": "#8b5cf6",
    "fortress": "#f97316",
}

# ═══════════════════════════════════════════════════════════════
# 1. SILK ROAD DATA
# ═══════════════════════════════════════════════════════════════
SILK_ROAD = {
    "description": (
        "The Silk Road was a network of trade routes connecting China to the "
        "Mediterranean from the 2nd century BCE to the 15th century CE. It "
        "facilitated the exchange of silk, spices, precious metals, gems, "
        "religions, technologies, and diseases across Eurasia."
    ),
    "period": "130 BCE – 1453 CE",
    "distance_km": 6400,
    "routes": {
        "Northern Route": {
            "color": "#06b6d4",
            "coords": [
                [34.26, 108.94],   # Xi'an (Chang'an)
                [36.06, 103.83],   # Lanzhou
                [37.87, 101.78],   # Wuwei (Liangzhou)
                [38.93, 100.45],   # Zhangye (Ganzhou)
                [39.73, 98.51],    # Jiuquan (Suzhou)
                [40.14, 94.66],    # Dunhuang
                [40.51, 90.17],    # Hami
                [42.95, 89.18],    # Turpan
                [43.80, 87.60],    # Urumqi
                [44.05, 80.33],    # Yining
                [42.48, 75.99],    # Bishkek
                [42.87, 71.29],    # Taraz
                [43.24, 68.67],    # Shymkent
                [39.65, 66.96],    # Samarkand
                [39.77, 64.42],    # Bukhara
                [42.46, 59.60],    # Khiva (Urgench)
                [37.55, 61.84],    # Merv (Mary)
                [35.30, 52.00],    # Tehran
                [38.08, 46.29],    # Tabriz
                [41.01, 28.98],    # Constantinople (Istanbul)
            ],
        },
        "Southern Route": {
            "color": "#8b5cf6",
            "coords": [
                [34.26, 108.94],   # Xi'an
                [36.06, 103.83],   # Lanzhou
                [40.14, 94.66],    # Dunhuang
                [38.42, 87.32],    # Lop Nor area
                [37.62, 79.07],    # Khotan (Hotan)
                [39.47, 75.99],    # Kashgar
                [40.53, 72.80],    # Fergana
                [39.65, 66.96],    # Samarkand
                [37.55, 61.84],    # Merv
                [36.72, 53.05],    # Gorgan
                [32.66, 51.68],    # Isfahan
                [32.62, 44.02],    # Baghdad
                [36.20, 37.13],    # Aleppo
                [33.51, 36.29],    # Damascus
                [34.05, 35.65],    # Byblos / Beirut area
                [31.77, 35.23],    # Jerusalem
                [31.20, 29.92],    # Alexandria
            ],
        },
        "Maritime Silk Route": {
            "color": "#10b981",
            "coords": [
                [22.55, 114.06],   # Guangzhou (Canton)
                [16.05, 108.22],   # Da Nang (Champa)
                [10.82, 106.63],   # Ho Chi Minh (Oc Eo)
                [1.35, 103.82],    # Singapore area
                [3.14, 101.69],    # Malacca
                [6.93, 79.85],     # Colombo (Sri Lanka)
                [9.97, 76.27],     # Kochi (Muziris)
                [15.42, 73.98],    # Goa
                [23.01, 56.24],    # Muscat
                [12.78, 45.03],    # Aden
                [15.63, 39.48],    # Massawa
                [30.04, 31.24],    # Cairo (via Red Sea)
            ],
        },
    },
    "cities": [
        {"name": "Xi'an (Chang'an)", "lat": 34.26, "lon": 108.94, "type": "capital",
         "info": "Eastern terminus, Tang Dynasty capital, population ~1 million"},
        {"name": "Dunhuang", "lat": 40.14, "lon": 94.66, "type": "oasis",
         "info": "Gateway to the Taklamakan Desert, Mogao Caves with 492 grottoes"},
        {"name": "Kashgar", "lat": 39.47, "lon": 75.99, "type": "market",
         "info": "Major crossroads where northern and southern routes converged"},
        {"name": "Samarkand", "lat": 39.65, "lon": 66.96, "type": "capital",
         "info": "Timurid capital, Registan Square, paper-making center from 751 CE"},
        {"name": "Bukhara", "lat": 39.77, "lon": 64.42, "type": "market",
         "info": "Center of Islamic scholarship, 365 caravanserais at its peak"},
        {"name": "Merv", "lat": 37.55, "lon": 61.84, "type": "capital",
         "info": "Largest city in the world circa 1200 CE, population ~500,000"},
        {"name": "Baghdad", "lat": 32.66, "lon": 44.02, "type": "capital",
         "info": "Abbasid capital, House of Wisdom, major trade hub 762-1258 CE"},
        {"name": "Constantinople", "lat": 41.01, "lon": 28.98, "type": "capital",
         "info": "Western terminus, Byzantine capital, gateway to Europe"},
        {"name": "Turpan", "lat": 42.95, "lon": 89.18, "type": "oasis",
         "info": "Oasis city on the northern route, Flaming Mountains, -154m depression"},
        {"name": "Khotan", "lat": 37.62, "lon": 79.07, "type": "market",
         "info": "Famous for jade and silk production, southern route key stop"},
        {"name": "Tabriz", "lat": 38.08, "lon": 46.29, "type": "market",
         "info": "Mongol-era trading hub, described by Marco Polo as a great market"},
        {"name": "Guangzhou", "lat": 22.55, "lon": 114.06, "type": "port",
         "info": "Major maritime trade port, Arab and Persian merchant community"},
        {"name": "Colombo", "lat": 6.93, "lon": 79.85, "type": "port",
         "info": "Sri Lanka, crossroads of Indian Ocean trade, gemstones and spices"},
    ],
    "goods": "Silk, porcelain, jade, spices, gold, silver, glass, horses, paper, gunpowder",
}

# ═══════════════════════════════════════════════════════════════
# 2. SPICE ROUTES DATA
# ═══════════════════════════════════════════════════════════════
SPICE_ROUTES = {
    "description": (
        "The Spice Routes were maritime trade networks that connected the "
        "spice-producing Moluccas (Spice Islands) and India with Europe. "
        "Portuguese navigator Vasco da Gama opened the direct sea route in "
        "1498, breaking the Venetian-Arab monopoly and reshaping world trade."
    ),
    "period": "3000 BCE – 18th century CE (peak: 15th-17th c.)",
    "distance_km": 22000,
    "routes": {
        "Portuguese Route (da Gama)": {
            "color": "#ef4444",
            "coords": [
                [38.72, -9.14],    # Lisbon
                [28.46, -16.25],   # Canary Islands
                [14.69, -17.44],   # Dakar area
                [-14.87, -23.51],  # Cape Verde passing
                [-33.92, 18.42],   # Cape of Good Hope
                [-25.97, 32.57],   # Mozambique
                [-6.16, 39.19],    # Zanzibar
                [-4.04, 39.67],    # Mombasa
                [2.04, 45.34],     # Mogadishu
                [12.78, 45.03],    # Aden
                [9.97, 76.27],     # Calicut (Kozhikode)
                [15.42, 73.98],    # Goa (Portuguese HQ)
            ],
        },
        "Arab-Indian Route": {
            "color": "#f59e0b",
            "coords": [
                [-3.70, 128.18],   # Moluccas (Ternate)
                [-6.17, 106.85],   # Jakarta (Sunda Kelapa)
                [1.35, 103.82],    # Singapore / Malacca Strait
                [3.14, 101.69],    # Malacca
                [6.93, 79.85],     # Colombo
                [9.97, 76.27],     # Calicut
                [23.01, 56.24],    # Muscat
                [26.23, 50.58],    # Bahrain
                [30.51, 47.81],    # Basra
                [12.78, 45.03],    # Aden
                [15.63, 39.48],    # Massawa
                [30.04, 31.24],    # Cairo / Suez
                [31.20, 29.92],    # Alexandria
            ],
        },
        "Venetian-Mediterranean": {
            "color": "#8b5cf6",
            "coords": [
                [31.20, 29.92],    # Alexandria
                [35.17, 33.36],    # Cyprus
                [36.80, 34.63],    # Tarsus
                [36.43, 28.22],    # Rhodes
                [37.94, 23.73],    # Athens / Piraeus
                [39.64, 19.92],    # Corfu
                [45.44, 12.32],    # Venice
                [43.77, 11.25],    # Florence
                [43.30, 5.37],     # Marseille
                [41.38, 2.18],     # Barcelona
            ],
        },
        "Dutch East India Route": {
            "color": "#10b981",
            "coords": [
                [52.38, 4.90],     # Amsterdam
                [51.45, 3.57],     # Zeeland
                [28.46, -16.25],   # Canary Islands
                [-33.92, 18.42],   # Cape Town
                [-20.16, 57.50],   # Mauritius
                [6.93, 79.85],     # Colombo
                [-6.17, 106.85],   # Batavia (Jakarta)
                [-3.70, 128.18],   # Moluccas
                [-8.65, 115.22],   # Bali
            ],
        },
    },
    "cities": [
        {"name": "Moluccas (Ternate)", "lat": -3.70, "lon": 128.18, "type": "market",
         "info": "The original Spice Islands — sole source of cloves and nutmeg"},
        {"name": "Calicut (Kozhikode)", "lat": 9.97, "lon": 76.27, "type": "port",
         "info": "Vasco da Gama arrived 1498, pepper capital of the world"},
        {"name": "Goa", "lat": 15.42, "lon": 73.98, "type": "capital",
         "info": "Portuguese India headquarters from 1510, spice trans-shipment"},
        {"name": "Malacca", "lat": 3.14, "lon": 101.69, "type": "port",
         "info": "Strategic strait, Portuguese captured 1511, key chokepoint"},
        {"name": "Venice", "lat": 45.44, "lon": 12.32, "type": "port",
         "info": "Dominated European spice trade before Portuguese route discovery"},
        {"name": "Alexandria", "lat": 31.20, "lon": 29.92, "type": "port",
         "info": "Ancient spice entrepot, Roman-era link to Indian Ocean trade"},
        {"name": "Lisbon", "lat": 38.72, "lon": -9.14, "type": "capital",
         "info": "Portuguese Empire capital, Casa da India controlled spice monopoly"},
        {"name": "Amsterdam", "lat": 52.38, "lon": 4.90, "type": "capital",
         "info": "VOC headquarters, overtook Lisbon as spice capital in 17th century"},
        {"name": "Zanzibar", "lat": -6.16, "lon": 39.19, "type": "port",
         "info": "East African trade hub for cloves, ivory, and spice re-export"},
        {"name": "Aden", "lat": 12.78, "lon": 45.03, "type": "port",
         "info": "Gateway to the Red Sea, key Arab trading port for millennia"},
    ],
    "goods": "Black pepper, cinnamon, cloves, nutmeg, mace, cardamom, ginger, turmeric, saffron",
}

# ═══════════════════════════════════════════════════════════════
# 3. AMBER ROAD DATA
# ═══════════════════════════════════════════════════════════════
AMBER_ROAD = {
    "description": (
        "The Amber Road was an ancient trade route for the transfer of amber "
        "from the Baltic Sea coast to the Mediterranean. Baltic amber, prized "
        "since the Neolithic period, was as valuable as gold in ancient Egypt "
        "and Greece. The route connected Germanic, Celtic, and Roman worlds."
    ),
    "period": "3000 BCE – 5th century CE",
    "distance_km": 1800,
    "routes": {
        "Main Amber Road": {
            "color": "#f59e0b",
            "coords": [
                [54.70, 20.51],    # Kaliningrad (Sambia Peninsula)
                [54.35, 18.65],    # Gdansk (Danzig)
                [53.43, 14.53],    # Szczecin
                [51.11, 17.04],    # Wroclaw (Breslau)
                [50.07, 14.44],    # Prague
                [48.68, 16.40],    # Brno area
                [48.15, 17.11],    # Bratislava (Carnuntum)
                [47.50, 16.62],    # Sopron (Scarabantia)
                [46.06, 14.51],    # Ljubljana (Emona)
                [45.65, 13.78],    # Trieste (Tergeste)
                [45.05, 13.64],    # Pula
                [44.50, 12.25],    # Ravenna
                [43.77, 11.25],    # Florence
                [41.90, 12.50],    # Rome (Aquileia route)
            ],
        },
        "Eastern Amber Route": {
            "color": "#ec4899",
            "coords": [
                [54.70, 20.51],    # Kaliningrad
                [54.68, 25.28],    # Vilnius
                [51.24, 22.57],    # Lublin
                [50.45, 30.52],    # Kyiv
                [46.48, 30.73],    # Odessa (Black Sea)
                [41.01, 28.98],    # Constantinople
                [37.94, 23.73],    # Athens
            ],
        },
        "Western Branch": {
            "color": "#06b6d4",
            "coords": [
                [54.35, 18.65],    # Gdansk
                [52.23, 21.01],    # Warsaw
                [50.06, 19.94],    # Krakow
                [48.21, 16.37],    # Vienna (Vindobona)
                [47.07, 15.44],    # Graz
                [46.62, 13.85],    # Villach
                [46.50, 11.35],    # Bolzano (Brenner Pass approach)
                [45.44, 12.32],    # Venice
            ],
        },
    },
    "cities": [
        {"name": "Kaliningrad (Sambia)", "lat": 54.70, "lon": 20.51, "type": "mine",
         "info": "World's largest amber deposits, 90% of global amber originates here"},
        {"name": "Gdansk (Danzig)", "lat": 54.35, "lon": 18.65, "type": "port",
         "info": "Major amber processing center since the Bronze Age"},
        {"name": "Carnuntum", "lat": 48.15, "lon": 17.11, "type": "market",
         "info": "Roman legionary fortress and major amber trading post on the Danube"},
        {"name": "Aquileia", "lat": 45.77, "lon": 13.37, "type": "market",
         "info": "Roman city, main amber import hub, UNESCO World Heritage Site"},
        {"name": "Rome", "lat": 41.90, "lon": 12.50, "type": "capital",
         "info": "Final destination, Emperor Nero sent expedition to Baltic for amber"},
        {"name": "Wroclaw (Breslau)", "lat": 51.11, "lon": 17.04, "type": "market",
         "info": "Key intermediary stop on Oder River crossings"},
        {"name": "Ljubljana (Emona)", "lat": 46.06, "lon": 14.51, "type": "market",
         "info": "Roman Emona, gateway between Pannonia and the Adriatic"},
        {"name": "Athens", "lat": 37.94, "lon": 23.73, "type": "capital",
         "info": "Greek amber imports via Black Sea eastern route"},
    ],
    "goods": "Baltic amber, furs, honey, wax, slaves (northbound: wine, olive oil, bronze, glass)",
}

# ═══════════════════════════════════════════════════════════════
# 4. INCENSE ROUTE DATA
# ═══════════════════════════════════════════════════════════════
INCENSE_ROUTE = {
    "description": (
        "The Incense Route was an ancient network of trading routes linking "
        "the Mediterranean with eastern and southern sources of frankincense "
        "and myrrh. These aromatic resins were more valuable than gold and "
        "were essential for religious rituals across the ancient world."
    ),
    "period": "7th century BCE – 2nd century CE",
    "distance_km": 2400,
    "routes": {
        "Main Incense Route": {
            "color": "#f59e0b",
            "coords": [
                [17.02, 54.09],    # Dhofar (Oman) — frankincense groves
                [15.35, 49.13],    # Shabwa (Hadramaut capital)
                [14.79, 46.83],    # Marib (Sabaean capital)
                [15.48, 44.22],    # Sana'a
                [16.84, 43.26],    # Najran
                [20.47, 41.33],    # Al Bahah
                [21.42, 39.83],    # Mecca
                [24.47, 39.61],    # Medina (Yathrib)
                [26.37, 38.19],    # Al-Ula (Dedan)
                [27.53, 36.59],    # Hegra (Mada'in Salih)
                [30.33, 35.44],    # Petra (Nabataean capital)
                [31.51, 34.45],    # Gaza (Mediterranean port)
            ],
        },
        "Frankincense Maritime Route": {
            "color": "#06b6d4",
            "coords": [
                [17.02, 54.09],    # Dhofar coast
                [12.78, 45.03],    # Aden
                [11.59, 43.15],    # Djibouti (Horn of Africa)
                [15.63, 39.48],    # Massawa / Adulis
                [27.19, 33.83],    # Hurghada area
                [29.97, 32.55],    # Suez
                [30.04, 31.24],    # Cairo
                [31.20, 29.92],    # Alexandria
            ],
        },
        "Myrrh Route (Somalia)": {
            "color": "#10b981",
            "coords": [
                [10.44, 50.10],    # Cape Guardafui (Punt)
                [11.59, 43.15],    # Djibouti
                [12.78, 45.03],    # Aden
                [14.79, 46.83],    # Marib
                [30.33, 35.44],    # Petra
                [31.51, 34.45],    # Gaza
                [31.77, 35.23],    # Jerusalem
                [33.51, 36.29],    # Damascus
            ],
        },
    },
    "cities": [
        {"name": "Dhofar (Oman)", "lat": 17.02, "lon": 54.09, "type": "mine",
         "info": "Primary source of frankincense (Boswellia sacra trees), UNESCO site"},
        {"name": "Shabwa", "lat": 15.35, "lon": 49.13, "type": "capital",
         "info": "Hadramaut kingdom capital, incense warehousing and taxation center"},
        {"name": "Marib", "lat": 14.79, "lon": 46.83, "type": "capital",
         "info": "Sabaean capital (Queen of Sheba), Great Dam of Marib"},
        {"name": "Petra", "lat": 30.33, "lon": 35.44, "type": "capital",
         "info": "Nabataean capital, controlled northern incense trade, UNESCO site"},
        {"name": "Gaza", "lat": 31.51, "lon": 34.45, "type": "port",
         "info": "Mediterranean terminus, shipped incense to Egypt, Greece, and Rome"},
        {"name": "Mecca", "lat": 21.42, "lon": 39.83, "type": "market",
         "info": "Pre-Islamic trade center, Quraysh tribe dominated caravan trade"},
        {"name": "Al-Ula (Dedan)", "lat": 26.37, "lon": 38.19, "type": "market",
         "info": "Dedanite and Lihyanite kingdom, oasis rest stop for caravans"},
        {"name": "Hegra (Mada'in Salih)", "lat": 27.53, "lon": 36.59, "type": "market",
         "info": "Southern Nabataean city, rock-cut tombs, UNESCO World Heritage Site"},
    ],
    "goods": "Frankincense, myrrh, balsam, cassia, Indian spices (trans-shipped), gold, ivory",
}

# ═══════════════════════════════════════════════════════════════
# 5. TRANS-SAHARAN ROUTES DATA
# ═══════════════════════════════════════════════════════════════
TRANS_SAHARAN = {
    "description": (
        "The Trans-Saharan trade routes connected sub-Saharan West Africa "
        "with the Mediterranean world via the Sahara Desert. Camel caravans "
        "of up to 12,000 animals carried gold, salt, slaves, and kola nuts. "
        "These routes gave rise to powerful empires: Ghana, Mali, and Songhai."
    ),
    "period": "4th century CE – 19th century CE",
    "distance_km": 3200,
    "routes": {
        "Western Route (Gold Road)": {
            "color": "#f59e0b",
            "coords": [
                [16.77, -3.00],    # Timbuktu
                [18.09, -1.95],    # Arawan
                [21.86, -3.54],    # Taghaza (salt mines)
                [23.70, -3.10],    # Tanezrouft crossing
                [27.07, -2.01],    # Adrar region
                [29.21, -0.59],    # Ghardaia
                [32.88, -0.32],    # Tlemcen area
                [34.05, -1.95],    # Fes
                [35.76, -5.83],    # Tangier (Mediterranean)
            ],
        },
        "Central Route": {
            "color": "#06b6d4",
            "coords": [
                [13.51, 2.11],     # Niamey / Hausaland
                [13.48, 7.49],     # Kano
                [16.97, 7.99],     # Agadez
                [18.73, 8.00],     # Bilma (salt)
                [21.48, 11.07],    # Djado
                [23.30, 11.35],    # Murzuk (Fezzan)
                [26.59, 14.27],    # Sabha
                [30.04, 14.12],    # Awjila
                [32.90, 13.18],    # Tripoli
            ],
        },
        "Eastern Route (Forty Days Road)": {
            "color": "#10b981",
            "coords": [
                [12.05, 24.90],    # Darfur (El Fasher)
                [13.79, 25.35],    # Kutum
                [15.95, 27.71],    # Selima Oasis
                [22.79, 28.97],    # Kharga Oasis
                [24.09, 30.75],    # Asyut (Nile)
                [30.04, 31.24],    # Cairo
            ],
        },
        "Garamantes Route": {
            "color": "#8b5cf6",
            "coords": [
                [16.77, -3.00],    # Timbuktu
                [16.27, 0.05],     # Gao
                [21.07, 2.87],     # In Salah
                [24.97, 9.48],     # Djanet
                [25.93, 13.05],    # Germa (Garamantes capital)
                [30.76, 13.08],    # Leptis Magna
            ],
        },
    },
    "cities": [
        {"name": "Timbuktu", "lat": 16.77, "lon": -3.00, "type": "capital",
         "info": "Center of learning, Sankore University, gold-salt exchange hub"},
        {"name": "Kano", "lat": 13.48, "lon": 7.49, "type": "market",
         "info": "Major Hausa city-state, leather goods, textiles, and indigo"},
        {"name": "Taghaza", "lat": 21.86, "lon": -3.54, "type": "mine",
         "info": "Salt mines, buildings made of salt blocks, extreme conditions"},
        {"name": "Agadez", "lat": 16.97, "lon": 7.99, "type": "market",
         "info": "Tuareg crossroads, gateway to the Air Mountains, caravan assembly point"},
        {"name": "Gao", "lat": 16.27, "lon": 0.05, "type": "capital",
         "info": "Songhai Empire capital, Niger River port, controlled eastern trade"},
        {"name": "Sijilmasa", "lat": 31.28, "lon": -4.28, "type": "market",
         "info": "Northern terminus, first trans-Saharan trading post, now ruins in Morocco"},
        {"name": "Tripoli", "lat": 32.90, "lon": 13.18, "type": "port",
         "info": "Mediterranean export hub, Ottoman-era trade center"},
        {"name": "Cairo", "lat": 30.04, "lon": 31.24, "type": "capital",
         "info": "Nile terminus of the eastern Forty Days Road, Mamluk-era trade"},
    ],
    "goods": "Gold, salt, slaves, kola nuts, ivory, ostrich feathers, leather, textiles, copper",
}

# ═══════════════════════════════════════════════════════════════
# 6. VIKING TRADE ROUTES DATA
# ═══════════════════════════════════════════════════════════════
VIKING_ROUTES = {
    "description": (
        "The Vikings (8th-11th century CE) established vast trade networks "
        "spanning from Scandinavia to Constantinople, Baghdad, and North America. "
        "The Varangians traded furs, amber, and slaves southward along Russian "
        "rivers, while western Vikings traded across the Atlantic."
    ),
    "period": "793 – 1066 CE",
    "distance_km": 5000,
    "routes": {
        "Varangian Route to Constantinople": {
            "color": "#06b6d4",
            "coords": [
                [59.95, 10.75],    # Oslo (Kaupang)
                [59.33, 18.07],    # Stockholm (Birka)
                [57.71, 11.97],    # Gothenburg
                [55.68, 12.57],    # Copenhagen (Hedeby area)
                [56.95, 24.11],    # Riga area
                [59.44, 24.75],    # Tallinn
                [59.95, 30.32],    # St. Petersburg (Staraya Ladoga)
                [58.52, 31.28],    # Novgorod
                [56.33, 43.99],    # Nizhny Novgorod
                [54.19, 37.62],    # Tula area (portage)
                [50.45, 30.52],    # Kyiv
                [46.48, 30.73],    # Odessa area (Black Sea)
                [41.01, 28.98],    # Constantinople (Miklagard)
            ],
        },
        "Volga Trade Route (to Baghdad)": {
            "color": "#f59e0b",
            "coords": [
                [59.95, 30.32],    # Staraya Ladoga
                [58.52, 31.28],    # Novgorod
                [57.63, 39.87],    # Yaroslavl
                [56.33, 43.99],    # Nizhny Novgorod
                [55.80, 49.11],    # Kazan (Bolgar)
                [53.20, 50.14],    # Samara
                [48.72, 44.50],    # Volgograd (portage to Don)
                [46.35, 48.05],    # Astrakhan (Caspian)
                [40.41, 49.87],    # Baku
                [38.08, 46.29],    # Tabriz
                [33.31, 44.37],    # Baghdad
            ],
        },
        "Western Atlantic Route": {
            "color": "#10b981",
            "coords": [
                [59.95, 10.75],    # Norway
                [61.20, -6.91],    # Faroe Islands
                [64.15, -21.94],   # Reykjavik (Iceland)
                [61.22, -45.44],   # East Greenland
                [64.17, -51.74],   # Nuuk (Greenland)
                [51.57, -55.53],   # L'Anse aux Meadows (Newfoundland)
            ],
        },
        "North Sea / British Isles Route": {
            "color": "#ec4899",
            "coords": [
                [55.68, 12.57],    # Denmark (Hedeby)
                [53.87, 8.65],     # Frisia
                [51.51, -0.13],    # London (Lundenwic)
                [53.96, -1.08],    # York (Jorvik)
                [55.95, -3.19],    # Edinburgh
                [57.48, -4.22],    # Inverness
                [58.97, -2.96],    # Orkney
                [60.15, -1.15],    # Shetland
                [62.01, -6.77],    # Faroe Islands
            ],
        },
    },
    "cities": [
        {"name": "Birka", "lat": 59.33, "lon": 18.07, "type": "market",
         "info": "Sweden's first town, major Viking Age trading hub on Lake Malaren"},
        {"name": "Hedeby", "lat": 54.49, "lon": 9.57, "type": "market",
         "info": "Largest Viking trading center, up to 2,000 inhabitants, UNESCO site"},
        {"name": "Constantinople (Miklagard)", "lat": 41.01, "lon": 28.98, "type": "capital",
         "info": "Varangian Guard served Byzantine Emperor, major trade destination"},
        {"name": "Novgorod", "lat": 58.52, "lon": 31.28, "type": "market",
         "info": "Rurikid capital, fur trade hub, gateway to Russian river routes"},
        {"name": "Kyiv", "lat": 50.45, "lon": 30.52, "type": "capital",
         "info": "Kievan Rus capital, Dnieper River trade, Vladimir's baptism 988"},
        {"name": "Jorvik (York)", "lat": 53.96, "lon": -1.08, "type": "market",
         "info": "Viking capital in England, major crafts and trade center"},
        {"name": "Staraya Ladoga", "lat": 59.99, "lon": 32.30, "type": "fortress",
         "info": "Earliest Viking settlement in Russia, founded c. 753 CE"},
        {"name": "L'Anse aux Meadows", "lat": 51.57, "lon": -55.53, "type": "market",
         "info": "Only confirmed Viking site in North America, c. 1000 CE, UNESCO site"},
        {"name": "Baghdad", "lat": 33.31, "lon": 44.37, "type": "capital",
         "info": "Abbasid Caliphate, terminus of Volga silver trade route"},
        {"name": "Reykjavik", "lat": 64.15, "lon": -21.94, "type": "market",
         "info": "Norse settlement from 874 CE, Althing parliament founded 930 CE"},
    ],
    "goods": "Furs, amber, walrus ivory, slaves, honey, wax, silver dirhams, silk, wine, weapons",
}

# ═══════════════════════════════════════════════════════════════
# 7. TIN ROUTES DATA
# ═══════════════════════════════════════════════════════════════
TIN_ROUTES = {
    "description": (
        "The Bronze Age tin trade (c. 3300-600 BCE) was essential for civilization. "
        "Bronze required tin, which was rare — found mainly in Cornwall, Iberia, "
        "and Afghanistan. Phoenician and Greek traders sailed to the 'Cassiterides' "
        "(Tin Islands) to obtain it. Without tin, there would be no Bronze Age."
    ),
    "period": "3300 – 600 BCE",
    "distance_km": 4500,
    "routes": {
        "Phoenician Atlantic Tin Route": {
            "color": "#06b6d4",
            "coords": [
                [50.27, -5.05],    # Cornwall (Land's End)
                [48.38, -4.49],    # Brittany (Finistere)
                [43.37, -8.40],    # A Coruna (Galicia)
                [41.15, -8.61],    # Porto
                [38.72, -9.14],    # Lisbon (Olisipo)
                [36.72, -6.28],    # Cadiz (Gadir)
                [35.76, -5.83],    # Tangier
                [36.80, -2.47],    # Almeria
                [37.62, 0.98],     # Cartagena
                [38.35, -0.48],    # Alicante
                [41.38, 2.18],     # Barcelona
                [43.30, 5.37],     # Marseille (Massalia)
                [33.89, 35.50],    # Byblos
                [34.44, 35.84],    # Tripoli (Lebanon)
                [33.27, 35.19],    # Tyre
            ],
        },
        "Overland European Tin Route": {
            "color": "#f59e0b",
            "coords": [
                [50.27, -5.05],    # Cornwall
                [51.45, -2.59],    # Bristol
                [51.51, -0.13],    # London area
                [51.25, 1.86],     # Canterbury / Dover
                [50.63, 3.06],     # Flanders
                [50.94, 6.96],     # Cologne
                [47.37, 8.54],     # Zurich area
                [46.50, 11.35],    # Brenner Pass
                [45.44, 12.32],    # Venice (Adriatic)
                [37.94, 23.73],    # Athens (Piraeus)
            ],
        },
        "Eastern Tin Route (Afghanistan)": {
            "color": "#10b981",
            "coords": [
                [36.72, 69.17],    # Badakhshan (Afghanistan tin)
                [39.65, 66.96],    # Samarkand
                [37.55, 61.84],    # Merv
                [32.62, 44.02],    # Babylon / Baghdad
                [33.51, 36.29],    # Damascus
                [33.27, 35.19],    # Tyre
                [31.20, 29.92],    # Alexandria
            ],
        },
        "Iberian Tin Route": {
            "color": "#8b5cf6",
            "coords": [
                [42.23, -8.72],    # Vigo (NW Iberia tin mines)
                [41.15, -8.61],    # Porto
                [39.47, -8.48],    # Central Portugal
                [38.72, -9.14],    # Lisbon
                [36.72, -6.28],    # Cadiz
                [35.89, -5.32],    # Strait of Gibraltar
                [36.72, 3.05],     # Algiers
                [36.82, 10.17],    # Carthage (Tunis)
            ],
        },
    },
    "cities": [
        {"name": "Cornwall (Cassiterides)", "lat": 50.27, "lon": -5.05, "type": "mine",
         "info": "Primary European tin source, 'Tin Islands' of Greek legend"},
        {"name": "Cadiz (Gadir)", "lat": 36.72, "lon": -6.28, "type": "port",
         "info": "Phoenician colony founded c. 1104 BCE, Atlantic trade gateway"},
        {"name": "Tyre", "lat": 33.27, "lon": 35.19, "type": "port",
         "info": "Phoenician capital, center of bronze production and maritime trade"},
        {"name": "Carthage", "lat": 36.82, "lon": 10.17, "type": "capital",
         "info": "Punic control of western Mediterranean tin trade after 6th c. BCE"},
        {"name": "Massalia (Marseille)", "lat": 43.30, "lon": 5.37, "type": "port",
         "info": "Greek colony, Pytheas sailed from here to explore tin sources c. 325 BCE"},
        {"name": "Badakhshan", "lat": 36.72, "lon": 69.17, "type": "mine",
         "info": "Afghan tin and lapis lazuli source, supplied Mesopotamia"},
        {"name": "Babylon", "lat": 32.54, "lon": 44.42, "type": "capital",
         "info": "Major bronze production center, imported tin from multiple sources"},
    ],
    "goods": "Tin, copper, bronze, tin ingots (oxhide-shaped), lapis lazuli, gold, silver, pottery",
}

# ═══════════════════════════════════════════════════════════════
# 8. TEA & OPIUM ROUTES DATA
# ═══════════════════════════════════════════════════════════════
TEA_OPIUM_ROUTES = {
    "description": (
        "The Tea-Horse Road (Chamado) was a 1,300-year-old trade route through "
        "Yunnan and Sichuan to Tibet. The 18th-19th century British tea trade "
        "created the infamous Opium Triangle: British textiles to India, Indian "
        "opium to China, Chinese tea to Britain. This imbalance led to the Opium Wars."
    ),
    "period": "7th century CE – 19th century CE",
    "distance_km": 15000,
    "routes": {
        "Tea Horse Road (Yunnan-Tibet)": {
            "color": "#10b981",
            "coords": [
                [22.00, 100.78],   # Xishuangbanna (Pu'er tea origin)
                [22.79, 100.98],   # Pu'er
                [25.04, 102.68],   # Kunming
                [26.87, 100.22],   # Dali
                [27.37, 100.01],   # Lijiang
                [27.83, 99.70],    # Shangri-La (Zhongdian)
                [28.66, 99.07],    # Deqen (Meili Snow Mtn pass)
                [29.33, 97.97],    # Markam
                [29.65, 91.13],    # Lhasa
            ],
        },
        "Tea Horse Road (Sichuan-Tibet)": {
            "color": "#06b6d4",
            "coords": [
                [30.57, 104.07],   # Chengdu
                [29.98, 103.00],   # Ya'an (tea production)
                [30.05, 101.96],   # Kangding (Dartsedo)
                [30.00, 101.12],   # Litang
                [29.65, 99.27],    # Batang
                [29.33, 97.97],    # Markam
                [29.65, 91.13],    # Lhasa
            ],
        },
        "Clipper Tea Route (China-Britain)": {
            "color": "#f59e0b",
            "coords": [
                [31.23, 121.47],   # Shanghai
                [22.28, 114.16],   # Hong Kong
                [10.82, 106.63],   # South China Sea
                [1.35, 103.82],    # Singapore
                [6.93, 79.85],     # Sri Lanka
                [12.78, 45.03],    # Aden
                [30.04, 31.24],    # Suez (after 1869)
                [35.90, -5.34],    # Gibraltar
                [51.51, -0.13],    # London
            ],
        },
        "Opium Triangle Route": {
            "color": "#ef4444",
            "coords": [
                [51.51, -0.13],    # London / Liverpool
                [38.72, -9.14],    # Lisbon area
                [14.69, -17.44],   # West Africa coast
                [-33.92, 18.42],   # Cape of Good Hope
                [18.94, 72.84],    # Bombay (Mumbai) — opium processing
                [22.57, 88.36],    # Calcutta (Kolkata) — Bengal opium
                [6.93, 79.85],     # Colombo
                [1.35, 103.82],    # Singapore
                [22.28, 114.16],   # Hong Kong / Canton
                [31.23, 121.47],   # Shanghai
            ],
        },
    },
    "cities": [
        {"name": "Pu'er", "lat": 22.79, "lon": 100.98, "type": "market",
         "info": "Origin of Pu'er tea, ancient tea horse trade starting point"},
        {"name": "Lhasa", "lat": 29.65, "lon": 91.13, "type": "capital",
         "info": "Tibetan capital, terminus of Tea Horse Road, tea for horses exchange"},
        {"name": "Ya'an", "lat": 29.98, "lon": 103.00, "type": "market",
         "info": "Sichuan compressed tea bricks production center"},
        {"name": "Canton (Guangzhou)", "lat": 22.55, "lon": 114.06, "type": "port",
         "info": "Only port open to foreign trade 1757-1842, 13 Factories district"},
        {"name": "Bombay (Mumbai)", "lat": 18.94, "lon": 72.84, "type": "port",
         "info": "British India opium processing and export hub"},
        {"name": "Calcutta (Kolkata)", "lat": 22.57, "lon": 88.36, "type": "port",
         "info": "East India Company Bengal opium auction center"},
        {"name": "London", "lat": 51.51, "lon": -0.13, "type": "capital",
         "info": "East India Company HQ, world's largest tea consumer by 1800"},
        {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "type": "port",
         "info": "Treaty port after 1842, international settlement, opium trade hub"},
        {"name": "Kangding (Dartsedo)", "lat": 30.05, "lon": 101.96, "type": "market",
         "info": "Sino-Tibetan border market, tea-horse exchange center"},
    ],
    "goods": "Tea (Pu'er, green, brick), horses, opium, silk, textiles, silver, porcelain, wool",
}

# ═══════════════════════════════════════════════════════════════
# 9. SLAVE TRADE ROUTES DATA
# ═══════════════════════════════════════════════════════════════
SLAVE_TRADE_ROUTES = {
    "description": (
        "This map documents the historical slave trade routes for educational "
        "purposes. The Transatlantic slave trade (1500s-1800s) forcibly transported "
        "an estimated 12.5 million Africans to the Americas. The Arab/Indian Ocean "
        "slave trade operated for over a millennium. Understanding these routes is "
        "essential for historical awareness and remembrance."
    ),
    "period": "7th century CE – 19th century CE",
    "distance_km": 12000,
    "routes": {
        "Middle Passage (Transatlantic)": {
            "color": "#ef4444",
            "coords": [
                [6.30, -1.48],     # Elmina Castle (Ghana)
                [6.45, 2.36],      # Ouidah (Dahomey)
                [6.45, 3.40],      # Lagos
                [4.02, 9.70],      # Douala
                [-8.84, 13.23],    # Luanda (Angola)
                [-8.50, -10.00],   # Mid-Atlantic
                [-5.00, -25.00],   # Mid-Atlantic crossing
                [0.00, -40.00],    # Equatorial Atlantic
                [12.97, -61.77],   # Barbados
                [18.00, -76.80],   # Jamaica
                [18.47, -69.88],   # Hispaniola
                [23.13, -82.38],   # Havana (Cuba)
                [32.78, -79.93],   # Charleston, SC
                [37.54, -77.43],   # Richmond, VA
                [-12.97, -38.51],  # Salvador (Brazil)
                [-22.91, -43.17],  # Rio de Janeiro
            ],
        },
        "Arab / Indian Ocean Route": {
            "color": "#f59e0b",
            "coords": [
                [-6.16, 39.19],    # Zanzibar
                [-8.02, 34.89],    # Tabora (interior)
                [-3.38, 36.68],    # Arusha area
                [2.04, 45.34],     # Mogadishu
                [12.78, 45.03],    # Aden
                [23.01, 56.24],    # Muscat (Oman)
                [26.23, 50.58],    # Bahrain
                [30.51, 47.81],    # Basra
                [33.31, 44.37],    # Baghdad
                [30.04, 31.24],    # Cairo
            ],
        },
        "Trans-Saharan Slave Route": {
            "color": "#8b5cf6",
            "coords": [
                [9.06, 7.49],      # Central Nigeria
                [13.48, 7.49],     # Kano
                [16.97, 7.99],     # Agadez
                [23.30, 11.35],    # Murzuk (Fezzan)
                [32.90, 13.18],    # Tripoli
                [30.04, 31.24],    # Cairo
                [36.82, 10.17],    # Tunis
            ],
        },
        "Internal African Routes": {
            "color": "#06b6d4",
            "coords": [
                [-11.68, 27.48],   # Katanga (Congo interior)
                [-8.84, 13.23],    # Luanda
                [-15.42, 28.28],   # Lusaka area
                [-15.39, 35.00],   # Lake Malawi
                [-6.16, 39.19],    # Zanzibar
                [-3.38, 29.36],    # Lake Tanganyika
                [0.32, 32.58],     # Kampala area
                [3.58, 31.57],     # South Sudan
                [15.60, 32.53],    # Khartoum
            ],
        },
    },
    "cities": [
        {"name": "Elmina Castle", "lat": 6.30, "lon": -1.48, "type": "fortress",
         "info": "Portuguese (1482), then Dutch fort. Key slave trading post, UNESCO site"},
        {"name": "Goree Island", "lat": 14.67, "lon": -17.40, "type": "fortress",
         "info": "Senegal, Door of No Return memorial, symbol of slave trade, UNESCO site"},
        {"name": "Zanzibar", "lat": -6.16, "lon": 39.19, "type": "port",
         "info": "Largest slave market in East Africa, Omani Sultanate hub"},
        {"name": "Ouidah", "lat": 6.45, "lon": 2.36, "type": "port",
         "info": "Dahomey (Benin), Route of Slaves memorial, ~1 million shipped from here"},
        {"name": "Luanda", "lat": -8.84, "lon": 13.23, "type": "port",
         "info": "Portuguese Angola, largest source of slaves to Brazil"},
        {"name": "Salvador (Bahia)", "lat": -12.97, "lon": -38.51, "type": "port",
         "info": "First capital of Brazil, received more African slaves than any other city"},
        {"name": "Charleston", "lat": 32.78, "lon": -79.93, "type": "port",
         "info": "Largest slave port in North America, ~40% of all US slave imports"},
        {"name": "Havana", "lat": 23.13, "lon": -82.38, "type": "port",
         "info": "Cuba, sugar plantation labor, last major slave importing country in Americas"},
        {"name": "Khartoum", "lat": 15.60, "lon": 32.53, "type": "market",
         "info": "White Nile slave market, convergence of Saharan and Nile routes"},
    ],
    "goods": "Enslaved people (12.5M transatlantic, 6-10M trans-Saharan, 4M+ Indian Ocean)",
}

# ═══════════════════════════════════════════════════════════════
# 10. MODERN SHIPPING LANES DATA
# ═══════════════════════════════════════════════════════════════
MODERN_SHIPPING = {
    "description": (
        "Modern global shipping carries over 80% of world trade by volume. "
        "About 60,000 cargo ships traverse the oceans, passing through critical "
        "chokepoints like the Strait of Malacca, Suez Canal, and Panama Canal. "
        "Container shipping (invented 1956) revolutionized global commerce."
    ),
    "period": "1956 CE – present",
    "distance_km": 45000,
    "routes": {
        "Asia-Europe (Suez)": {
            "color": "#06b6d4",
            "coords": [
                [31.23, 121.47],   # Shanghai
                [22.28, 114.16],   # Hong Kong
                [10.00, 107.00],   # South China Sea
                [1.25, 103.80],    # Singapore (Malacca Strait)
                [6.93, 79.85],     # Colombo (Sri Lanka)
                [12.78, 45.03],    # Gulf of Aden
                [12.61, 43.14],    # Bab el-Mandeb
                [30.04, 32.30],    # Suez Canal
                [31.40, 32.35],    # Port Said
                [35.90, -5.34],    # Strait of Gibraltar
                [51.95, 1.31],     # English Channel
                [53.55, 9.99],     # Hamburg
                [51.90, 4.50],     # Rotterdam
            ],
        },
        "Transpacific (Asia-Americas)": {
            "color": "#f59e0b",
            "coords": [
                [31.23, 121.47],   # Shanghai
                [35.44, 139.64],   # Tokyo / Yokohama
                [35.10, 129.04],   # Busan
                [37.00, 170.00],   # North Pacific
                [40.00, -155.00],  # Mid-Pacific
                [42.00, -135.00],  # NE Pacific
                [37.81, -122.42],  # San Francisco
                [33.74, -118.27],  # Long Beach / Los Angeles
            ],
        },
        "Transatlantic": {
            "color": "#10b981",
            "coords": [
                [51.90, 4.50],     # Rotterdam
                [53.55, 9.99],     # Hamburg
                [51.95, 1.31],     # English Channel
                [50.00, -10.00],   # Bay of Biscay
                [45.00, -30.00],   # Mid-Atlantic
                [40.69, -74.04],   # New York / New Jersey
                [39.27, -76.58],   # Baltimore
                [29.76, -95.37],   # Houston (Gulf)
            ],
        },
        "Panama Canal Route": {
            "color": "#ec4899",
            "coords": [
                [40.69, -74.04],   # New York
                [25.77, -80.19],   # Miami
                [18.00, -76.80],   # Caribbean
                [9.00, -79.50],    # Panama Canal
                [8.95, -79.57],    # Pacific side
                [5.00, -85.00],    # Eastern Pacific
                [33.74, -118.27],  # Los Angeles
                [37.81, -122.42],  # San Francisco
            ],
        },
        "Cape Route (Asia-Americas alt.)": {
            "color": "#8b5cf6",
            "coords": [
                [31.23, 121.47],   # Shanghai
                [1.25, 103.80],    # Singapore
                [-6.17, 106.85],   # Jakarta
                [-33.86, 25.58],   # Port Elizabeth
                [-33.92, 18.42],   # Cape Town
                [-34.60, -58.38],  # Buenos Aires
                [-23.55, -46.63],  # Santos (Sao Paulo)
                [29.76, -95.37],   # Houston
                [40.69, -74.04],   # New York
            ],
        },
    },
    "cities": [
        {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "type": "port",
         "info": "World's busiest port, ~47 million TEU/year, Yangshan Deep Water Port"},
        {"name": "Singapore", "lat": 1.25, "lon": 103.80, "type": "port",
         "info": "World's busiest transshipment port, Strait of Malacca (25% of trade)"},
        {"name": "Rotterdam", "lat": 51.90, "lon": 4.50, "type": "port",
         "info": "Europe's largest port, ~15 million TEU/year, Europoort complex"},
        {"name": "Suez Canal", "lat": 30.04, "lon": 32.30, "type": "port",
         "info": "12% of global trade, ~50 ships/day, expanded 2015 to two-lane"},
        {"name": "Panama Canal", "lat": 9.00, "lon": -79.50, "type": "port",
         "info": "6% of global trade, Neo-Panamax locks (2016), ~40 ships/day"},
        {"name": "Long Beach / LA", "lat": 33.74, "lon": -118.27, "type": "port",
         "info": "Busiest US port complex, ~9 million TEU/year, gateway for Asian imports"},
        {"name": "Dubai (Jebel Ali)", "lat": 25.02, "lon": 55.06, "type": "port",
         "info": "Middle East's largest port, major transshipment hub, DP World terminal"},
        {"name": "Busan", "lat": 35.10, "lon": 129.04, "type": "port",
         "info": "South Korea's largest port, ~22 million TEU, NE Asia transshipment"},
        {"name": "Hamburg", "lat": 53.55, "lon": 9.99, "type": "port",
         "info": "Germany's largest port, 'Gateway to the World', Elbe River access"},
        {"name": "Strait of Hormuz", "lat": 26.56, "lon": 56.25, "type": "port",
         "info": "21% of global oil trade passes through, 21 miles wide at narrowest"},
    ],
    "goods": "Containers (TEU), crude oil, LNG, bulk minerals, grain, vehicles, electronics",
}

# ═══════════════════════════════════════════════════════════════
# ALL ROUTES INDEX
# ═══════════════════════════════════════════════════════════════
ROUTE_MODES = {
    "Silk Road": SILK_ROAD,
    "Spice Routes": SPICE_ROUTES,
    "Amber Road": AMBER_ROAD,
    "Incense Route": INCENSE_ROUTE,
    "Trans-Saharan Routes": TRANS_SAHARAN,
    "Viking Trade Routes": VIKING_ROUTES,
    "Tin Routes": TIN_ROUTES,
    "Tea & Opium Routes": TEA_OPIUM_ROUTES,
    "Slave Trade Routes": SLAVE_TRADE_ROUTES,
    "Modern Shipping Lanes": MODERN_SHIPPING,
}

MODE_ICONS = {
    "Silk Road": "\U0001F42A",
    "Spice Routes": "\U0001F336\uFE0F",
    "Amber Road": "\U0001F48E",
    "Incense Route": "\U0001F9F4",
    "Trans-Saharan Routes": "\U0001F3DC\uFE0F",
    "Viking Trade Routes": "\u2693",
    "Tin Routes": "\u2692\uFE0F",
    "Tea & Opium Routes": "\U0001FAD6",
    "Slave Trade Routes": "\u26D3\uFE0F",
    "Modern Shipping Lanes": "\U0001F6A2",
}

MODE_DESCRIPTIONS = {
    "Silk Road": "Ancient Eurasian land & sea routes (130 BCE - 1453 CE)",
    "Spice Routes": "Maritime spice trade from Moluccas to Europe",
    "Amber Road": "Baltic amber to Mediterranean (3000 BCE - 5th c. CE)",
    "Incense Route": "Arabian frankincense & myrrh trade network",
    "Trans-Saharan Routes": "Gold, salt & slave routes across the Sahara",
    "Viking Trade Routes": "Norse networks from Scandinavia to Baghdad & Vinland",
    "Tin Routes": "Bronze Age tin from Cornwall, Iberia & Afghanistan",
    "Tea & Opium Routes": "Tea Horse Road, clippers & the Opium Triangle",
    "Slave Trade Routes": "Transatlantic, Arab & internal African routes (educational)",
    "Modern Shipping Lanes": "Current global container & oil shipping routes",
}


# ═══════════════════════════════════════════════════════════════
# HELPER: BUILD FOLIUM MAP FOR A GIVEN ROUTE DATA DICT
# ═══════════════════════════════════════════════════════════════
def _compute_center(data: dict) -> tuple:
    """Compute map center from all route coordinates."""
    all_lats, all_lons = [], []
    for route_info in data["routes"].values():
        for coord in route_info["coords"]:
            all_lats.append(coord[0])
            all_lons.append(coord[1])
    for city in data.get("cities", []):
        all_lats.append(city["lat"])
        all_lons.append(city["lon"])
    if not all_lats:
        return (30.0, 0.0)
    return (sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons))


def _compute_zoom(data: dict) -> int:
    """Heuristic zoom level based on coordinate spread."""
    all_lats, all_lons = [], []
    for route_info in data["routes"].values():
        for coord in route_info["coords"]:
            all_lats.append(coord[0])
            all_lons.append(coord[1])
    if not all_lats:
        return 3
    lat_range = max(all_lats) - min(all_lats)
    lon_range = max(all_lons) - min(all_lons)
    span = max(lat_range, lon_range)
    if span > 200:
        return 2
    if span > 100:
        return 2
    if span > 60:
        return 3
    if span > 30:
        return 4
    if span > 15:
        return 5
    return 6


def _build_map(data: dict, mode_name: str) -> folium.Map:
    """Build a folium map with routes and city markers."""
    center = _compute_center(data)
    zoom = _compute_zoom(data)

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Draw route polylines
    for route_name, route_info in data["routes"].items():
        coords = route_info["coords"]
        color = route_info["color"]
        safe_name = escape(route_name)

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=3,
            opacity=0.85,
            dash_array="8 4",
            tooltip=safe_name,
            popup=folium.Popup(
                f"<div style='min-width:150px'>"
                f"<b style='color:{color}'>{safe_name}</b><br>"
                f"<small>{len(coords)} waypoints</small></div>",
                max_width=250,
            ),
        ).add_to(m)

        # Waypoint dots along the route
        for i, coord in enumerate(coords):
            folium.CircleMarker(
                location=coord,
                radius=3,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                weight=1,
            ).add_to(m)

    # City markers
    icon_map = {
        "capital": ("star", "red"),
        "port": ("anchor", "blue"),
        "oasis": ("tint", "green"),
        "market": ("shopping-cart", "orange"),
        "mine": ("gem", "purple"),
        "fortress": ("shield", "darkred"),
    }

    for city in data.get("cities", []):
        ctype = city.get("type", "market")
        icon_name, icon_color = icon_map.get(ctype, ("info-sign", "blue"))
        safe_city_name = escape(city["name"])
        safe_info = escape(city.get("info", ""))

        popup_html = (
            f"<div style='min-width:200px;max-width:300px;'>"
            f"<b style='font-size:13px;'>{safe_city_name}</b><br>"
            f"<span style='font-size:11px;color:#888;'>{escape(ctype.title())}</span><br>"
            f"<hr style='margin:4px 0;border-color:#444;'>"
            f"<span style='font-size:11px;'>{safe_info}</span>"
            f"</div>"
        )

        folium.Marker(
            location=[city["lat"], city["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=safe_city_name,
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
        ).add_to(m)

    # Legend overlay
    legend_items = ""
    for route_name, route_info in data["routes"].items():
        safe_name = escape(route_name)
        c = route_info["color"]
        legend_items += (
            f"<div style='display:flex;align-items:center;gap:6px;margin:2px 0;'>"
            f"<div style='width:24px;height:3px;background:{c};border-radius:2px;'></div>"
            f"<span style='font-size:11px;color:#e8ecf4;'>{safe_name}</span></div>"
        )

    legend_html = f"""
    <div style="position:fixed;bottom:30px;left:10px;z-index:1000;
        background:rgba(15,23,42,0.88);border:1px solid rgba(255,255,255,0.12);
        border-radius:8px;padding:10px 14px;backdrop-filter:blur(8px);
        max-width:260px;">
        <div style="font-size:12px;font-weight:600;color:#06b6d4;margin-bottom:6px;">
            {escape(mode_name)}
        </div>
        {legend_items}
        <div style="margin-top:6px;font-size:10px;color:#5a6580;">
            Click routes & markers for details
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


# ═══════════════════════════════════════════════════════════════
# HELPER: BUILD STATS METRICS
# ═══════════════════════════════════════════════════════════════
def _render_stats(data: dict, mode_name: str):
    """Display key metrics as Streamlit metric cards."""
    num_routes = len(data["routes"])
    total_waypoints = sum(len(r["coords"]) for r in data["routes"].values())
    num_cities = len(data.get("cities", []))
    distance = data.get("distance_km", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Routes", num_routes)
    c2.metric("Waypoints", total_waypoints)
    c3.metric("Key Cities", num_cities)
    c4.metric("Distance (km)", f"{distance:,}")


# ═══════════════════════════════════════════════════════════════
# HELPER: BUILD ROUTE TABLE
# ═══════════════════════════════════════════════════════════════
def _build_route_table(data: dict) -> pd.DataFrame:
    """Build a DataFrame summarizing the routes."""
    rows = []
    for route_name, route_info in data["routes"].items():
        coords = route_info["coords"]
        if len(coords) >= 2:
            start_lat, start_lon = coords[0]
            end_lat, end_lon = coords[-1]
        else:
            start_lat = start_lon = end_lat = end_lon = 0
        rows.append({
            "Route": route_name,
            "Waypoints": len(coords),
            "Start Lat": round(start_lat, 2),
            "Start Lon": round(start_lon, 2),
            "End Lat": round(end_lat, 2),
            "End Lon": round(end_lon, 2),
            "Color": route_info["color"],
        })
    return pd.DataFrame(rows)


def _build_city_table(data: dict) -> pd.DataFrame:
    """Build a DataFrame listing all key cities."""
    rows = []
    for city in data.get("cities", []):
        rows.append({
            "City": city["name"],
            "Type": city.get("type", "").title(),
            "Latitude": round(city["lat"], 4),
            "Longitude": round(city["lon"], 4),
            "Description": city.get("info", ""),
        })
    return pd.DataFrame(rows)


def _build_all_waypoints_table(data: dict) -> pd.DataFrame:
    """Build a DataFrame of all waypoints across all routes."""
    rows = []
    for route_name, route_info in data["routes"].items():
        for i, coord in enumerate(route_info["coords"]):
            rows.append({
                "Route": route_name,
                "Waypoint #": i + 1,
                "Latitude": round(coord[0], 4),
                "Longitude": round(coord[1], 4),
            })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
# HELPER: HISTORICAL CONTEXT PANELS
# ═══════════════════════════════════════════════════════════════
HISTORICAL_CONTEXT = {
    "Silk Road": [
        ("Origins", "The Han Dynasty envoy Zhang Qian (138 BCE) opened diplomatic "
         "relations with Central Asian kingdoms, establishing the first routes. "
         "Chinese silk became the most prized commodity flowing westward."),
        ("Peak Period", "Under the Tang Dynasty (618-907 CE), Chang'an had a population "
         "of ~1 million and hosted merchants from Persia, Arabia, India, and Byzantium. "
         "The Abbasid Caliphate controlled the western portions."),
        ("Cultural Exchange", "Buddhism spread east from India, Islam spread along "
         "trade routes, paper-making technology moved west (Battle of Talas, 751), "
         "and the Black Death traveled along these routes in the 1340s."),
        ("Decline", "The Ottoman conquest of Constantinople (1453) and the rise of "
         "maritime trade routes made overland routes less profitable. The Silk Road "
         "declined but never fully disappeared."),
    ],
    "Spice Routes": [
        ("Ancient Trade", "Spice trade dates to at least 3000 BCE. Egyptians used "
         "cinnamon for embalming. Roman Empire spent ~100 million sesterces/year on "
         "Indian spices, prompting Pliny to call it 'the drain on the Empire'."),
        ("Arab Monopoly", "Arab merchants controlled the spice trade for centuries, "
         "keeping production sources secret. They told Romans that cinnamon grew in "
         "swamps guarded by winged serpents."),
        ("Age of Discovery", "Portuguese navigator Vasco da Gama reached Calicut in "
         "1498, breaking the monopoly. The Treaty of Tordesillas (1494) divided the "
         "world between Spain and Portugal. The VOC (Dutch East India Company, 1602) "
         "became the world's first multinational corporation."),
        ("Economic Impact", "Spices drove colonization of Southeast Asia. Nutmeg "
         "was so valuable the Dutch traded Manhattan Island to Britain for the tiny "
         "nutmeg island of Run in the Bandas (1667)."),
    ],
    "Amber Road": [
        ("Prehistoric Origins", "Baltic amber has been traded since 13,000 BCE. "
         "Amber beads have been found in Egyptian tombs dating to 2600 BCE, proving "
         "trade connections spanning thousands of kilometers."),
        ("Scientific Interest", "The Greeks called amber 'elektron' (shining) — "
         "the origin of the word 'electricity'. Thales of Miletus (600 BCE) first "
         "noted amber's static-electric properties when rubbed with fur."),
        ("Roman Period", "Emperor Nero (37-68 CE) sent a Roman knight to the Baltic "
         "to secure amber supplies. Amber was used for gladiator arena decorations "
         "and was worth more than a healthy slave by weight."),
        ("Archaeological Evidence", "The Bernsteinstrasse (Amber Road) is one of "
         "the best-documented prehistoric trade routes, with amber finds at "
         "Mycenae, Troy, and throughout Bronze Age Mediterranean sites."),
    ],
    "Incense Route": [
        ("Sacred Economy", "Frankincense and myrrh were burned in temples across "
         "Egypt, Mesopotamia, Greece, and Rome. The Three Magi's gifts to Jesus "
         "symbolized incense's immense value — equal to gold."),
        ("Nabataean Control", "The Nabataeans of Petra dominated the northern "
         "incense trade from the 4th century BCE. They carved their famous rock "
         "city from rose-red sandstone with trade profits."),
        ("Scale of Trade", "Ancient sources report 3,000 tons of frankincense "
         "shipped annually from southern Arabia. Pliny recorded that Emperor Nero "
         "burned a year's supply of frankincense at Poppaea's funeral."),
        ("Modern Dhofar", "The frankincense-producing region of Dhofar (Oman) is "
         "now a UNESCO World Heritage Site. The Boswellia sacra trees that produce "
         "frankincense still grow in the same groves described by ancient writers."),
    ],
    "Trans-Saharan Routes": [
        ("Gold and Salt", "The trade was built on complementary needs: the Sahel "
         "had gold but needed salt for food preservation, while the Sahara had vast "
         "salt deposits (Taghaza, Bilma) but no gold. Pound for pound, gold was "
         "exchanged for salt."),
        ("Empires of Gold", "These routes funded the Ghana Empire (300-1200 CE), "
         "Mali Empire (1235-1600) — whose ruler Mansa Musa is considered the "
         "wealthiest person in history — and the Songhai Empire (1464-1591)."),
        ("Camel Revolution", "The introduction of the camel (c. 200 CE) transformed "
         "Saharan trade. Camels can carry 200kg, travel 40km/day, and survive 10 days "
         "without water. Caravans of 1,000-12,000 camels were common."),
        ("Timbuktu's Golden Age", "By the 14th century, Timbuktu housed the "
         "University of Sankore with 25,000 students and the largest library in "
         "Africa. Manuscripts traded alongside gold and salt."),
    ],
    "Viking Trade Routes": [
        ("Dual Identity", "Vikings were simultaneously raiders and sophisticated "
         "traders. The word 'Viking' likely derives from 'vik' (creek/inlet). "
         "They used standardized weights and silver hack-silver as currency."),
        ("Silver Trade", "The Volga route was primarily about silver. Over 100,000 "
         "Arab dirhams have been found in Scandinavian hoards. The Islamic world's "
         "silver fueled the Viking Age economy (793-1066 CE)."),
        ("Varangian Guard", "Viking warriors (Varangians) served as elite bodyguards "
         "to Byzantine emperors. Harald Hardrada served in Constantinople before "
         "becoming King of Norway (and dying at Stamford Bridge, 1066)."),
        ("North American Contact", "Leif Erikson reached Vinland (Newfoundland) "
         "c. 1000 CE — 492 years before Columbus. L'Anse aux Meadows is the only "
         "confirmed Norse site in the Americas (UNESCO World Heritage Site)."),
    ],
    "Tin Routes": [
        ("Why Tin Mattered", "Bronze = ~90% copper + ~10% tin. Copper is common, "
         "but tin is one of the rarest metals on Earth. Without long-distance tin "
         "trade, the Bronze Age could not have existed."),
        ("Cassiterides Mystery", "Greek and Roman writers spoke of the 'Cassiterides' "
         "(Tin Islands). Herodotus (c. 450 BCE) admitted he did not know their "
         "location — Phoenicians guarded the secret jealously. Most scholars "
         "identify them as Cornwall, UK."),
        ("Uluburun Shipwreck", "A Late Bronze Age shipwreck (c. 1300 BCE) off "
         "Turkey carried 10 tons of copper and 1 ton of tin in oxhide-shaped ingots, "
         "proving the scale of Bronze Age metal trade."),
        ("Collapse Connection", "Disruption of tin trade routes is considered a "
         "contributing factor to the Late Bronze Age Collapse (c. 1200-1150 BCE), "
         "when major civilizations around the Mediterranean fell within decades."),
    ],
    "Tea & Opium Routes": [
        ("Tea Horse Road", "For over 1,300 years, Tibetan and Chinese traders "
         "exchanged compressed tea bricks for Tibetan war horses. Porters carried "
         "up to 150kg of tea on their backs over 4,000m mountain passes."),
        ("British Tea Addiction", "By 1800, Britain imported 24 million pounds of "
         "tea annually. The trade deficit with China drained British silver, leading "
         "the East India Company to push Indian opium as payment."),
        ("Opium Wars", "China's attempts to halt opium imports led to the First "
         "(1839-42) and Second (1856-60) Opium Wars. The resulting Treaty of Nanking "
         "ceded Hong Kong to Britain and opened five treaty ports."),
        ("Clipper Ships", "The tea clipper era (1840s-1870s) produced the fastest "
         "sailing ships ever built. The Great Tea Race of 1866 saw ships race from "
         "Fuzhou to London — Taeping won by 20 minutes after 99 days."),
    ],
    "Slave Trade Routes": [
        ("Scale of Tragedy", "The Transatlantic slave trade (1500s-1800s) forcibly "
         "transported an estimated 12.5 million Africans. About 1.8 million died "
         "during the Middle Passage crossing. Brazil received the most (~5.5 million)."),
        ("Arab Slave Trade", "The Arab/Indian Ocean slave trade lasted over 1,000 "
         "years (7th-19th century), with an estimated 6-10 million people enslaved. "
         "Zanzibar was the main East African market."),
        ("Abolition Movement", "Britain abolished the slave trade in 1807 and "
         "slavery itself in 1833. The Royal Navy's West Africa Squadron freed "
         "~150,000 enslaved people from slave ships between 1808-1860."),
        ("Legacy & Remembrance", "UNESCO designated August 23 as International Day "
         "for Remembrance of the Slave Trade. Sites like Goree Island, Elmina "
         "Castle, and the Door of No Return are preserved as memorials."),
    ],
    "Modern Shipping Lanes": [
        ("Container Revolution", "Malcolm McLean invented standardized container "
         "shipping in 1956. Before containers, loading a ship took weeks; now it "
         "takes hours. This innovation cut shipping costs by 90%."),
        ("Scale Today", "Over 60,000 cargo ships carry 11 billion tonnes of goods "
         "annually — about 80% of global trade by volume. The largest container "
         "ships carry 24,000+ TEU (twenty-foot equivalent units)."),
        ("Chokepoints", "Six chokepoints handle most trade: Malacca Strait (25% of "
         "trade), Suez Canal (12%), Panama Canal (6%), Hormuz Strait (21% of oil), "
         "Bab el-Mandeb, and the Danish Straits."),
        ("Environmental Impact", "Shipping produces ~3% of global CO2 emissions. "
         "The IMO targets 50% reduction by 2050. LNG, wind-assist, and hydrogen "
         "fuel ships are being developed as alternatives to heavy fuel oil."),
    ],
}


# ═══════════════════════════════════════════════════════════════
# HELPER: MATPLOTLIB CHART — TIMELINE / GOODS BREAKDOWN
# ═══════════════════════════════════════════════════════════════
def _render_timeline_chart(mode_name: str, data: dict):
    """Render a simple matplotlib bar chart of waypoints per route."""
    import matplotlib.pyplot as plt
    import matplotlib

    matplotlib.use("Agg")

    route_names = list(data["routes"].keys())
    waypoint_counts = [len(r["coords"]) for r in data["routes"].values()]
    colors = [r["color"] for r in data["routes"].values()]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    bars = ax.barh(route_names, waypoint_counts, color=colors, edgecolor="none", height=0.6)

    for bar, count in zip(bars, waypoint_counts):
        ax.text(
            bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            str(count), va="center", ha="left", color="#e8ecf4",
            fontsize=10, fontweight="bold",
        )

    ax.set_xlabel("Waypoints", color="#8b97b0", fontsize=10)
    ax.set_title(f"{mode_name} — Waypoints per Route", color="#e8ecf4", fontsize=12, fontweight="bold")
    ax.tick_params(colors="#8b97b0", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#2a3550")
    ax.spines["left"].set_color("#2a3550")
    ax.invert_yaxis()

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_city_types_chart(data: dict):
    """Render a pie chart of city types."""
    import matplotlib.pyplot as plt
    import matplotlib

    matplotlib.use("Agg")

    cities = data.get("cities", [])
    if not cities:
        return

    type_counts = {}
    for city in cities:
        t = city.get("type", "other").title()
        type_counts[t] = type_counts.get(t, 0) + 1

    labels = list(type_counts.keys())
    sizes = list(type_counts.values())
    colors_list = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899", "#ef4444", "#3b82f6"]
    pie_colors = [colors_list[i % len(colors_list)] for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(4, 3.5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=pie_colors, autopct="%1.0f%%",
        textprops={"color": "#e8ecf4", "fontsize": 9},
        pctdistance=0.75, startangle=90,
    )
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_color("#e8ecf4")

    ax.set_title("City Types", color="#e8ecf4", fontsize=11, fontweight="bold")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# HELPER: CSV DOWNLOAD
# ═══════════════════════════════════════════════════════════════
def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Offer a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        label=label,
        data=buf.getvalue(),
        file_name=filename,
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════════
# HELPER: RENDER COMPARISON TABLE ACROSS ALL MODES
# ═══════════════════════════════════════════════════════════════
def _render_comparison_table():
    """Show a comparison of all 10 trade route networks."""
    rows = []
    for name, data in ROUTE_MODES.items():
        rows.append({
            "Trade Route": f"{MODE_ICONS.get(name, '')} {name}",
            "Period": data["period"],
            "Distance (km)": f"{data['distance_km']:,}",
            "Routes": len(data["routes"]),
            "Key Cities": len(data.get("cities", [])),
            "Waypoints": sum(len(r["coords"]) for r in data["routes"].values()),
            "Key Goods": data.get("goods", "")[:60] + "...",
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
# HELPER: OVERPASS API QUERY FOR NEARBY HISTORIC FEATURES
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fetch_nearby_historic(lat: float, lon: float, radius_m: int = 50000) -> list:
    """Fetch nearby historic=* features from OpenStreetMap Overpass API."""
    query = f"""
    [out:json][timeout:15];
    (
      node["historic"](around:{radius_m},{lat},{lon});
      way["historic"](around:{radius_m},{lat},{lon});
    );
    out center 30;
    """
    try:
        resp = __import__("requests").get(
            "https://overpass-api.de/api/interpreter",
            params={"data": query},
            timeout=20,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        results = []
        for el in elements:
            lat_val = el.get("lat") or el.get("center", {}).get("lat")
            lon_val = el.get("lon") or el.get("center", {}).get("lon")
            tags = el.get("tags", {})
            name = tags.get("name", tags.get("historic", "Unknown"))
            results.append({
                "name": name,
                "lat": lat_val,
                "lon": lon_val,
                "type": tags.get("historic", ""),
                "description": tags.get("description", tags.get("wikipedia", "")),
            })
        return results
    except Exception:
        return []


@st.cache_data(ttl=3600)
def _fetch_wikidata_trade_route_info(route_keyword: str) -> list:
    """Fetch related Wikidata items for a trade route keyword via SPARQL."""
    sparql_query = f"""
    SELECT ?item ?itemLabel ?itemDescription ?coord WHERE {{
      ?item rdfs:label ?label .
      FILTER(LANG(?label) = "en")
      FILTER(CONTAINS(LCASE(?label), "{route_keyword.lower()}"))
      ?item wdt:P31/wdt:P279* wd:Q83620 .
      OPTIONAL {{ ?item wdt:P625 ?coord . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 20
    """
    try:
        resp = __import__("requests").get(
            "https://query.wikidata.org/sparql",
            params={"query": sparql_query, "format": "json"},
            headers={"User-Agent": "TerraScoutAI/1.0"},
            timeout=15,
        )
        resp.raise_for_status()
        bindings = resp.json().get("results", {}).get("bindings", [])
        results = []
        for b in bindings:
            results.append({
                "label": b.get("itemLabel", {}).get("value", ""),
                "description": b.get("itemDescription", {}).get("value", ""),
                "uri": b.get("item", {}).get("value", ""),
            })
        return results
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════
def render_trade_routes_maps_tab():
    """Render the Ancient Trade Routes & Paths tab for TerraScout AI."""

    # Tab header
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001F42A Ancient Trade Routes & Paths</h4>'
        '<p>Silk Road, spice routes, amber road, incense route & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──────────────────────────────────────────
    mode_options = list(ROUTE_MODES.keys())
    mode_labels = [f"{MODE_ICONS.get(m, '')} {m}" for m in mode_options]

    selected_label = st.selectbox(
        "Select Trade Route",
        mode_labels,
        index=0,
        help="Choose from 10 historical and modern trade route networks",
    )
    selected_mode = mode_options[mode_labels.index(selected_label)]
    data = ROUTE_MODES[selected_mode]

    # ── Description ────────────────────────────────────────────
    st.markdown(
        f"<div style='background:rgba(15,23,42,0.65);border:1px solid rgba(255,255,255,0.08);"
        f"border-radius:8px;padding:14px 18px;margin:8px 0 16px 0;'>"
        f"<span style='color:#06b6d4;font-weight:600;'>{escape(selected_mode)}</span>"
        f"<span style='color:#5a6580;'> | {escape(data['period'])}</span>"
        f"<br><span style='color:#e8ecf4;font-size:14px;'>{escape(data['description'])}</span>"
        f"<br><span style='color:#8b97b0;font-size:12px;margin-top:4px;display:inline-block;'>"
        f"<b>Key goods:</b> {escape(data.get('goods', ''))}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Stats metrics ──────────────────────────────────────────
    _render_stats(data, selected_mode)

    # ── Map ────────────────────────────────────────────────────
    st.markdown(
        f"<div style='color:#8b97b0;font-size:12px;margin:8px 0 4px 0;'>"
        f"Interactive map — click routes and markers for details</div>",
        unsafe_allow_html=True,
    )

    m = _build_map(data, selected_mode)
    components.html(m._repr_html_(), height=500)

    # ── Explore nearby historic features ───────────────────────
    st.markdown("---")
    with st.expander("Explore Nearby Historic Features (OSM Overpass)", expanded=False):
        st.markdown(
            "<span style='color:#8b97b0;font-size:12px;'>"
            "Select a key city to find nearby historic features from OpenStreetMap."
            "</span>",
            unsafe_allow_html=True,
        )
        cities = data.get("cities", [])
        if cities:
            city_names = [c["name"] for c in cities]
            sel_city = st.selectbox("Select city", city_names, key="osm_city_sel")
            radius = st.slider("Search radius (km)", 5, 100, 50, key="osm_radius")

            city_obj = next((c for c in cities if c["name"] == sel_city), None)
            if city_obj and st.button("Search historic features", key="trdrt_osm_search_btn"):
                with st.spinner(f"Querying OSM near {escape(sel_city)}..."):
                    results = _fetch_nearby_historic(
                        city_obj["lat"], city_obj["lon"], radius * 1000
                    )
                if results:
                    st.success(f"Found {len(results)} historic features near {sel_city}")
                    df_osm = pd.DataFrame(results)
                    st.dataframe(df_osm, width="stretch")
                    _csv_download(df_osm, f"osm_historic_{sel_city.replace(' ', '_')}.csv",
                                  "Download OSM results CSV")
                else:
                    st.info("No historic features found in this radius. Try a larger area.")
        else:
            st.info("No cities defined for this route.")

    # ── Wikidata enrichment ────────────────────────────────────
    with st.expander("Wikidata Trade Route Knowledge", expanded=False):
        st.markdown(
            "<span style='color:#8b97b0;font-size:12px;'>"
            "Fetch related Wikidata items about this trade route network."
            "</span>",
            unsafe_allow_html=True,
        )
        search_kw = st.text_input(
            "Search keyword",
            value=selected_mode.split(" ")[0].lower(),
            key="wikidata_kw",
        )
        if st.button("Search Wikidata", key="wikidata_search_btn"):
            with st.spinner("Querying Wikidata SPARQL..."):
                wd_results = _fetch_wikidata_trade_route_info(search_kw)
            if wd_results:
                st.success(f"Found {len(wd_results)} related items")
                df_wd = pd.DataFrame(wd_results)
                st.dataframe(df_wd, width="stretch")
            else:
                st.info("No Wikidata results found. Try different keywords.")

    # ── Historical context ─────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"<div style='color:#e8ecf4;font-size:16px;font-weight:600;margin:8px 0;'>"
        f"Historical Context</div>",
        unsafe_allow_html=True,
    )

    context_items = HISTORICAL_CONTEXT.get(selected_mode, [])
    for title, text in context_items:
        st.markdown(
            f"<div style='background:rgba(15,23,42,0.50);border-left:3px solid #8b5cf6;"
            f"border-radius:4px;padding:10px 14px;margin:6px 0;'>"
            f"<span style='color:#06b6d4;font-weight:600;font-size:13px;'>"
            f"{escape(title)}</span><br>"
            f"<span style='color:#e8ecf4;font-size:13px;'>{escape(text)}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Charts ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='color:#e8ecf4;font-size:16px;font-weight:600;margin:8px 0;'>"
        "Route Analytics</div>",
        unsafe_allow_html=True,
    )

    col_chart1, col_chart2 = st.columns([3, 2])
    with col_chart1:
        _render_timeline_chart(selected_mode, data)
    with col_chart2:
        _render_city_types_chart(data)

    # ── Data tables ────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='color:#e8ecf4;font-size:16px;font-weight:600;margin:8px 0;'>"
        "Data Tables</div>",
        unsafe_allow_html=True,
    )

    tab_routes, tab_cities, tab_waypoints, tab_compare = st.tabs([
        "Routes Summary", "Key Cities", "All Waypoints", "Compare All Routes"
    ])

    with tab_routes:
        df_routes = _build_route_table(data)
        st.dataframe(df_routes, width="stretch")
        _csv_download(
            df_routes,
            f"trade_routes_{selected_mode.replace(' ', '_').lower()}_routes.csv",
            "Download routes CSV",
        )

    with tab_cities:
        df_cities = _build_city_table(data)
        if not df_cities.empty:
            st.dataframe(df_cities, width="stretch")
            _csv_download(
                df_cities,
                f"trade_routes_{selected_mode.replace(' ', '_').lower()}_cities.csv",
                "Download cities CSV",
            )
        else:
            st.info("No city data for this route.")

    with tab_waypoints:
        df_wp = _build_all_waypoints_table(data)
        st.dataframe(df_wp, width="stretch")
        _csv_download(
            df_wp,
            f"trade_routes_{selected_mode.replace(' ', '_').lower()}_waypoints.csv",
            "Download waypoints CSV",
        )

    with tab_compare:
        df_comp = _render_comparison_table()
        st.dataframe(df_comp, width="stretch")
        _csv_download(df_comp, "trade_routes_comparison.csv", "Download comparison CSV")

    # ── Route-specific sub-map: focus on a single route ────────
    st.markdown("---")
    st.markdown(
        "<div style='color:#e8ecf4;font-size:16px;font-weight:600;margin:8px 0;'>"
        "Focus on Individual Route</div>",
        unsafe_allow_html=True,
    )

    route_names = list(data["routes"].keys())
    selected_route = st.selectbox(
        "Select a specific route to zoom in",
        route_names,
        key="focus_route_sel",
    )

    if selected_route:
        route_info = data["routes"][selected_route]
        coords = route_info["coords"]
        color = route_info["color"]

        if coords:
            center_lat = sum(c[0] for c in coords) / len(coords)
            center_lon = sum(c[1] for c in coords) / len(coords)

            lat_range = max(c[0] for c in coords) - min(c[0] for c in coords)
            lon_range = max(c[1] for c in coords) - min(c[1] for c in coords)
            span = max(lat_range, lon_range)
            if span > 100:
                fzoom = 3
            elif span > 50:
                fzoom = 4
            elif span > 20:
                fzoom = 5
            elif span > 10:
                fzoom = 6
            else:
                fzoom = 7

            fm = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=fzoom,
                tiles="CartoDB dark_matter",
            )

            folium.PolyLine(
                locations=coords,
                color=color,
                weight=4,
                opacity=0.9,
                tooltip=escape(selected_route),
            ).add_to(fm)

            for i, coord in enumerate(coords):
                label = f"Waypoint {i + 1}"
                folium.CircleMarker(
                    location=coord,
                    radius=5,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.8,
                    weight=2,
                    tooltip=escape(label),
                    popup=folium.Popup(
                        f"<div style='min-width:120px;'>"
                        f"<b>{escape(label)}</b><br>"
                        f"<small>Lat: {coord[0]:.4f}<br>Lon: {coord[1]:.4f}</small></div>",
                        max_width=200,
                    ),
                ).add_to(fm)

            # Add start/end markers
            folium.Marker(
                location=coords[0],
                tooltip="Start",
                icon=folium.Icon(color="green", icon="play", prefix="fa"),
            ).add_to(fm)
            folium.Marker(
                location=coords[-1],
                tooltip="End",
                icon=folium.Icon(color="red", icon="stop", prefix="fa"),
            ).add_to(fm)

            components.html(fm._repr_html_(), height=420)

            # Route detail stats
            c1, c2, c3 = st.columns(3)
            c1.metric("Waypoints", len(coords))
            c2.metric("Start", f"{coords[0][0]:.2f}, {coords[0][1]:.2f}")
            c3.metric("End", f"{coords[-1][0]:.2f}, {coords[-1][1]:.2f}")

    # ── Footer ─────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;color:#5a6580;font-size:11px;margin:24px 0 8px 0;'>"
        "Trade route data curated from historical sources. Coordinates are approximate "
        "representations of historical paths. OSM data via Overpass API. "
        "Wikidata queries via SPARQL endpoint."
        "</div>",
        unsafe_allow_html=True,
    )
