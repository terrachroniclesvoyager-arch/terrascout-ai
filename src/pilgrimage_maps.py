# -*- coding: utf-8 -*-
"""
Pilgrimage & Sacred Sites Explorer module for TerraScout AI.
Provides 10 curated map types covering holy cities, pilgrimage routes,
temples, mosques, cathedrals, sacred mountains, monasteries, and ancient
religious sites worldwide. Uses hardcoded scholarly data supplemented by
Overpass API queries for live OSM enrichment where noted.
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

from src.overpass_client import query_overpass

# ═══════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE (TerraScout dark theme)
# ═══════════════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_BORDER = "#2a3550"
_TEXT_PRI = "#e8ecf4"
_TEXT_SEC = "#8b97b0"
_TEXT_MUT = "#5a6580"
_ACCENT = "#06b6d4"

RELIGION_COLORS = {
    "Christianity": "#3b82f6",
    "Islam": "#10b981",
    "Hinduism": "#f59e0b",
    "Buddhism": "#8b5cf6",
    "Sikhism": "#f97316",
    "Judaism": "#38bdf8",
    "Shinto": "#ec4899",
    "Jainism": "#a855f7",
    "Taoism": "#14b8a6",
    "Zoroastrianism": "#ef4444",
    "Baha'i": "#e879f9",
    "Indigenous": "#84cc16",
    "Multi-faith": "#06b6d4",
    "Ancient Greek": "#d4a017",
    "Ancient Egyptian": "#c2a000",
    "Megalithic": "#78716c",
    "Neolithic": "#a8a29e",
    "Various": "#8b97b0",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. HOLY CITIES
# ═══════════════════════════════════════════════════════════════════════════════
HOLY_CITIES = [
    {"name": "Jerusalem", "lat": 31.7767, "lon": 35.2345, "religion": "Multi-faith", "significance": "Sacred to Judaism, Christianity, and Islam; Temple Mount, Holy Sepulchre, Al-Aqsa"},
    {"name": "Mecca", "lat": 21.4225, "lon": 39.8262, "religion": "Islam", "significance": "Holiest city in Islam; Kaaba and Masjid al-Haram; destination of Hajj"},
    {"name": "Medina", "lat": 24.4672, "lon": 39.6112, "religion": "Islam", "significance": "Second holiest city in Islam; Prophet's Mosque and burial site"},
    {"name": "Varanasi", "lat": 25.3176, "lon": 83.0064, "religion": "Hinduism", "significance": "Oldest living city; holiest city in Hinduism; cremation ghats on Ganges"},
    {"name": "Vatican City", "lat": 41.9029, "lon": 12.4534, "religion": "Christianity", "significance": "Seat of the Pope; St. Peter's Basilica; smallest sovereign state"},
    {"name": "Bodh Gaya", "lat": 24.6961, "lon": 84.9869, "religion": "Buddhism", "significance": "Site of Buddha's enlightenment under the Bodhi tree; Mahabodhi Temple"},
    {"name": "Amritsar", "lat": 31.6200, "lon": 74.8765, "religion": "Sikhism", "significance": "Golden Temple (Harmandir Sahib); holiest shrine in Sikhism"},
    {"name": "Lhasa", "lat": 29.6500, "lon": 91.1000, "religion": "Buddhism", "significance": "Jokhang Temple and Potala Palace; spiritual capital of Tibetan Buddhism"},
    {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642, "religion": "Hinduism", "significance": "Gateway to the Gods; Kumbh Mela site on the Ganges"},
    {"name": "Kyoto", "lat": 35.0116, "lon": 135.7681, "religion": "Buddhism", "significance": "Over 1600 Buddhist temples and 400 Shinto shrines; former imperial capital"},
    {"name": "Ise", "lat": 34.4551, "lon": 136.7256, "religion": "Shinto", "significance": "Ise Grand Shrine; most sacred Shinto shrine, rebuilt every 20 years"},
    {"name": "Lourdes", "lat": 43.0948, "lon": -0.0459, "religion": "Christianity", "significance": "Marian apparition site; 6 million pilgrims annually; healing waters"},
    {"name": "Fatima", "lat": 39.6315, "lon": -8.6538, "religion": "Christianity", "significance": "Marian apparition of 1917; Basilica of Our Lady of Fatima"},
    {"name": "Allahabad (Prayagraj)", "lat": 25.4358, "lon": 81.8463, "religion": "Hinduism", "significance": "Triveni Sangam confluence; Kumbh Mela, largest religious gathering on Earth"},
    {"name": "Mathura", "lat": 27.4924, "lon": 77.6737, "religion": "Hinduism", "significance": "Birthplace of Lord Krishna; one of the seven sacred cities"},
    {"name": "Ujjain", "lat": 23.1765, "lon": 75.7885, "religion": "Hinduism", "significance": "Mahakaleshwar Jyotirlinga; one of seven sacred cities; Kumbh Mela site"},
    {"name": "Kandy", "lat": 7.2906, "lon": 80.6337, "religion": "Buddhism", "significance": "Temple of the Sacred Tooth Relic of Buddha"},
    {"name": "Bethlehem", "lat": 31.7054, "lon": 35.2024, "religion": "Christianity", "significance": "Birthplace of Jesus Christ; Church of the Nativity"},
    {"name": "Nazareth", "lat": 32.6996, "lon": 35.3035, "religion": "Christianity", "significance": "Childhood home of Jesus; Basilica of the Annunciation"},
    {"name": "Karbala", "lat": 32.6160, "lon": 44.0249, "religion": "Islam", "significance": "Imam Husayn shrine; holiest city for Shia Muslims after Mecca and Medina"},
    {"name": "Najaf", "lat": 32.0003, "lon": 44.3360, "religion": "Islam", "significance": "Imam Ali shrine; major Shia pilgrimage and theological centre"},
    {"name": "Nankana Sahib", "lat": 31.4500, "lon": 73.7000, "religion": "Sikhism", "significance": "Birthplace of Guru Nanak, founder of Sikhism"},
    {"name": "Mount Athos", "lat": 40.1564, "lon": 24.3264, "religion": "Christianity", "significance": "Autonomous monastic state; 20 Eastern Orthodox monasteries since 963 AD"},
    {"name": "Czestochowa", "lat": 50.8118, "lon": 19.1203, "religion": "Christianity", "significance": "Jasna Gora Monastery; Black Madonna icon; Polish national shrine"},
    {"name": "Santiago de Compostela", "lat": 42.8805, "lon": -8.5446, "religion": "Christianity", "significance": "Tomb of St. James; endpoint of the Camino de Santiago pilgrimage"},
    {"name": "Pushkar", "lat": 26.4896, "lon": 74.5531, "religion": "Hinduism", "significance": "Only Brahma temple in the world; sacred lake with 52 bathing ghats"},
    {"name": "Ayodhya", "lat": 26.7922, "lon": 82.1998, "religion": "Hinduism", "significance": "Birthplace of Lord Rama; Ram Janmabhoomi temple"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 2. CAMINO DE SANTIAGO ROUTES
# ═══════════════════════════════════════════════════════════════════════════════
CAMINO_FRANCES = [
    {"name": "St-Jean-Pied-de-Port", "lat": 43.1630, "lon": -1.2381},
    {"name": "Roncesvalles", "lat": 43.0093, "lon": -1.3194},
    {"name": "Pamplona", "lat": 42.8125, "lon": -1.6458},
    {"name": "Puente la Reina", "lat": 42.6720, "lon": -1.8131},
    {"name": "Estella", "lat": 42.6714, "lon": -2.0320},
    {"name": "Los Arcos", "lat": 42.5677, "lon": -2.1929},
    {"name": "Logrono", "lat": 42.4627, "lon": -2.4445},
    {"name": "Najera", "lat": 42.4167, "lon": -2.7333},
    {"name": "Santo Domingo de la Calzada", "lat": 42.4400, "lon": -2.9533},
    {"name": "Belorado", "lat": 42.4206, "lon": -3.1900},
    {"name": "Burgos", "lat": 42.3439, "lon": -3.6969},
    {"name": "Castrojeriz", "lat": 42.2900, "lon": -4.1383},
    {"name": "Fromista", "lat": 42.2675, "lon": -4.4050},
    {"name": "Carrion de los Condes", "lat": 42.3372, "lon": -4.6028},
    {"name": "Sahagun", "lat": 42.3714, "lon": -5.0317},
    {"name": "Leon", "lat": 42.5987, "lon": -5.5671},
    {"name": "Astorga", "lat": 42.4550, "lon": -6.0542},
    {"name": "Ponferrada", "lat": 42.5499, "lon": -6.5962},
    {"name": "Villafranca del Bierzo", "lat": 42.6067, "lon": -6.8108},
    {"name": "O Cebreiro", "lat": 42.7100, "lon": -7.0433},
    {"name": "Sarria", "lat": 42.7806, "lon": -7.4144},
    {"name": "Portomarin", "lat": 42.8078, "lon": -7.6181},
    {"name": "Palas de Rei", "lat": 42.8733, "lon": -7.8683},
    {"name": "Arzua", "lat": 42.9289, "lon": -8.1614},
    {"name": "Santiago de Compostela", "lat": 42.8805, "lon": -8.5446},
]

CAMINO_PORTUGUES = [
    {"name": "Lisbon", "lat": 38.7223, "lon": -9.1393},
    {"name": "Santarem", "lat": 39.2364, "lon": -8.6850},
    {"name": "Tomar", "lat": 39.6035, "lon": -8.4087},
    {"name": "Coimbra", "lat": 40.2033, "lon": -8.4103},
    {"name": "Porto", "lat": 41.1579, "lon": -8.6291},
    {"name": "Barcelos", "lat": 41.5316, "lon": -8.6186},
    {"name": "Ponte de Lima", "lat": 41.7670, "lon": -8.5832},
    {"name": "Valenca", "lat": 42.0273, "lon": -8.6427},
    {"name": "Tui", "lat": 42.0461, "lon": -8.6442},
    {"name": "Redondela", "lat": 42.2833, "lon": -8.6167},
    {"name": "Pontevedra", "lat": 42.4310, "lon": -8.6441},
    {"name": "Caldas de Reis", "lat": 42.6044, "lon": -8.6427},
    {"name": "Padron", "lat": 42.7388, "lon": -8.6609},
    {"name": "Santiago de Compostela", "lat": 42.8805, "lon": -8.5446},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 3. BUDDHIST TEMPLES
# ═══════════════════════════════════════════════════════════════════════════════
BUDDHIST_TEMPLES = [
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "note": "Largest religious monument in the world; originally Hindu then Buddhist"},
    {"name": "Borobudur", "lat": -7.6079, "lon": 110.2038, "country": "Indonesia", "note": "9th-century Mahayana Buddhist temple; largest Buddhist temple in the world"},
    {"name": "Shwedagon Pagoda", "lat": 16.8714, "lon": 96.1499, "country": "Myanmar", "note": "2,500 years old; 99m golden stupa; relics of four Buddhas"},
    {"name": "Mahabodhi Temple", "lat": 24.6961, "lon": 84.9869, "country": "India", "note": "Site of Buddha's enlightenment; UNESCO World Heritage Site"},
    {"name": "Jokhang Temple", "lat": 29.6530, "lon": 91.1015, "country": "China (Tibet)", "note": "Most sacred temple in Tibetan Buddhism; 7th century"},
    {"name": "Todai-ji", "lat": 34.6890, "lon": 135.8398, "country": "Japan", "note": "Houses the Great Buddha (Daibutsu); largest wooden building historically"},
    {"name": "Wat Phra Kaew", "lat": 13.7516, "lon": 100.4927, "country": "Thailand", "note": "Temple of the Emerald Buddha; most sacred Thai Buddhist temple"},
    {"name": "Kinkaku-ji (Golden Pavilion)", "lat": 35.0394, "lon": 135.7292, "country": "Japan", "note": "Zen Buddhist temple covered in gold leaf; iconic Kyoto landmark"},
    {"name": "Tiger's Nest (Paro Taktsang)", "lat": 27.4913, "lon": 89.3636, "country": "Bhutan", "note": "Cliffside temple at 3,120m; Guru Rinpoche meditation site"},
    {"name": "Temple of the Tooth", "lat": 7.2936, "lon": 80.6413, "country": "Sri Lanka", "note": "Houses the Sacred Tooth Relic of the Buddha; Kandy"},
    {"name": "Bagan Temples", "lat": 21.1717, "lon": 94.8585, "country": "Myanmar", "note": "Over 2,000 surviving temples and pagodas from 11th-13th century"},
    {"name": "Wat Arun", "lat": 13.7437, "lon": 100.4888, "country": "Thailand", "note": "Temple of Dawn; 79m Khmer-style prang on Chao Phraya River"},
    {"name": "Haeinsa Temple", "lat": 35.8020, "lon": 128.0994, "country": "South Korea", "note": "Houses the Tripitaka Koreana; 81,258 woodblock Buddhist scriptures"},
    {"name": "Pha That Luang", "lat": 17.9762, "lon": 102.6340, "country": "Laos", "note": "National symbol of Laos; gold-covered Buddhist stupa from 3rd century BCE"},
    {"name": "Dambulla Cave Temple", "lat": 7.8567, "lon": 80.6495, "country": "Sri Lanka", "note": "Five cave shrines with 153 Buddha statues; 2nd century BCE"},
    {"name": "Senso-ji", "lat": 35.7148, "lon": 139.7967, "country": "Japan", "note": "Tokyo's oldest temple; dedicated to Bodhisattva Kannon; 645 AD"},
    {"name": "Swayambhunath (Monkey Temple)", "lat": 27.7149, "lon": 85.2904, "country": "Nepal", "note": "Ancient stupa atop a hill in Kathmandu; eyes of Buddha on all four sides"},
    {"name": "Boudhanath Stupa", "lat": 27.7215, "lon": 85.3620, "country": "Nepal", "note": "One of the largest spherical stupas in the world; Tibetan Buddhist centre"},
    {"name": "Wat Pho", "lat": 13.7468, "lon": 100.4927, "country": "Thailand", "note": "Temple of the Reclining Buddha; 46m gold-plated reclining Buddha"},
    {"name": "Sanchi Stupa", "lat": 23.4793, "lon": 77.7399, "country": "India", "note": "Oldest stone structure in India; 3rd century BCE; Emperor Ashoka"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 4. ISLAMIC MOSQUES
# ═══════════════════════════════════════════════════════════════════════════════
ISLAMIC_MOSQUES = [
    {"name": "Masjid al-Haram", "lat": 21.4225, "lon": 39.8262, "country": "Saudi Arabia", "year": 638, "capacity": 4000000, "note": "Holiest mosque; surrounds the Kaaba"},
    {"name": "Al-Masjid an-Nabawi", "lat": 24.4672, "lon": 39.6112, "country": "Saudi Arabia", "year": 622, "capacity": 1500000, "note": "Prophet's Mosque; second holiest in Islam"},
    {"name": "Al-Aqsa Mosque", "lat": 31.7761, "lon": 35.2358, "country": "Palestine", "year": 705, "capacity": 500000, "note": "Third holiest mosque; Temple Mount / Haram esh-Sharif"},
    {"name": "Sultan Ahmed (Blue Mosque)", "lat": 41.0054, "lon": 28.9768, "country": "Turkey", "year": 1616, "capacity": 10000, "note": "Six minarets; blue Iznik tiles interior"},
    {"name": "Hassan II Mosque", "lat": 33.6086, "lon": -7.6323, "country": "Morocco", "year": 1993, "capacity": 105000, "note": "Tallest minaret in the world (210m); built over the Atlantic"},
    {"name": "Sheikh Zayed Grand Mosque", "lat": 24.4128, "lon": 54.4750, "country": "UAE", "year": 2007, "capacity": 40000, "note": "82 domes; largest hand-knotted carpet; Swarovski chandeliers"},
    {"name": "Faisal Mosque", "lat": 33.7296, "lon": 73.0372, "country": "Pakistan", "year": 1986, "capacity": 300000, "note": "Tent-shaped design; no traditional dome; Margalla Hills backdrop"},
    {"name": "Great Mosque of Djenne", "lat": 13.9055, "lon": -4.5549, "country": "Mali", "year": 1907, "capacity": 3000, "note": "Largest mud-brick building in the world; Sudano-Sahelian architecture"},
    {"name": "Great Mosque of Cordoba", "lat": 37.8789, "lon": -4.7794, "country": "Spain", "year": 784, "capacity": 20000, "note": "Mezquita; double arches; now Cathedral-Mosque of Cordoba"},
    {"name": "Suleymaniye Mosque", "lat": 41.0162, "lon": 28.9641, "country": "Turkey", "year": 1558, "capacity": 5000, "note": "Designed by Mimar Sinan; Ottoman imperial mosque"},
    {"name": "Istiqlal Mosque", "lat": -6.1700, "lon": 106.8312, "country": "Indonesia", "year": 1978, "capacity": 200000, "note": "Largest mosque in Southeast Asia; stainless steel dome"},
    {"name": "Badshahi Mosque", "lat": 31.5882, "lon": 74.3105, "country": "Pakistan", "year": 1673, "capacity": 100000, "note": "Mughal era masterpiece; red sandstone and marble"},
    {"name": "Great Mosque of Xi'an", "lat": 34.2620, "lon": 108.9430, "country": "China", "year": 742, "capacity": 1000, "note": "Chinese architectural style; oldest mosque in China"},
    {"name": "Sultan Qaboos Grand Mosque", "lat": 23.5880, "lon": 58.3948, "country": "Oman", "year": 2001, "capacity": 20000, "note": "Largest carpet and chandelier in a mosque"},
    {"name": "Dome of the Rock", "lat": 31.7780, "lon": 35.2354, "country": "Palestine", "year": 691, "capacity": 3000, "note": "Iconic gold dome; Foundation Stone; earliest surviving Islamic monument"},
    {"name": "Hagia Sophia", "lat": 41.0086, "lon": 28.9802, "country": "Turkey", "year": 537, "capacity": 10000, "note": "Cathedral 537-1453, mosque 1453-1934, museum 1934-2020, mosque again 2020"},
    {"name": "Al-Azhar Mosque", "lat": 30.0456, "lon": 31.2625, "country": "Egypt", "year": 970, "capacity": 20000, "note": "One of the oldest universities in the world; Fatimid dynasty"},
    {"name": "Great Mosque of Samarra", "lat": 34.2059, "lon": 43.8786, "country": "Iraq", "year": 851, "capacity": 10000, "note": "Famous spiral minaret (Malwiya); Abbasid era"},
    {"name": "Wazir Khan Mosque", "lat": 31.5838, "lon": 74.3251, "country": "Pakistan", "year": 1635, "capacity": 5000, "note": "Elaborate tile work and frescoes; Mughal era Lahore"},
    {"name": "Qolsharif Mosque", "lat": 55.7987, "lon": 49.1051, "country": "Russia", "year": 2005, "capacity": 6000, "note": "Rebuilt; originally destroyed by Ivan the Terrible in 1552"},
    {"name": "Masjid Negara", "lat": 3.1414, "lon": 101.6920, "country": "Malaysia", "year": 1965, "capacity": 15000, "note": "National Mosque of Malaysia; 73m minaret; star-shaped roof"},
    {"name": "Crystal Mosque", "lat": 5.3353, "lon": 103.1183, "country": "Malaysia", "year": 2008, "capacity": 1500, "note": "Made of steel, glass, and crystal; Islamic Heritage Park"},
    {"name": "Selimiye Mosque", "lat": 41.6773, "lon": 26.5590, "country": "Turkey", "year": 1575, "capacity": 6000, "note": "Mimar Sinan's masterpiece; UNESCO World Heritage Site; Edirne"},
    {"name": "Jama Masjid Delhi", "lat": 28.6507, "lon": 77.2334, "country": "India", "year": 1656, "capacity": 85000, "note": "Largest mosque in India; Mughal Emperor Shah Jahan; red sandstone"},
    {"name": "Mosque of Muhammad Ali", "lat": 30.0288, "lon": 31.2599, "country": "Egypt", "year": 1848, "capacity": 10000, "note": "Ottoman style on Cairo Citadel; Alabaster Mosque; twin minarets 82m"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 5. CHRISTIAN CATHEDRALS
# ═══════════════════════════════════════════════════════════════════════════════
CHRISTIAN_CATHEDRALS = [
    {"name": "St. Peter's Basilica", "lat": 41.9022, "lon": 12.4539, "country": "Vatican City", "year": 1626, "style": "Renaissance / Baroque"},
    {"name": "Notre-Dame de Paris", "lat": 48.8530, "lon": 2.3499, "country": "France", "year": 1345, "style": "French Gothic"},
    {"name": "Sagrada Familia", "lat": 41.4036, "lon": 2.1744, "country": "Spain", "year": 1882, "style": "Art Nouveau / Gothic"},
    {"name": "Cologne Cathedral", "lat": 50.9413, "lon": 6.9583, "country": "Germany", "year": 1880, "style": "High Gothic"},
    {"name": "Milan Cathedral (Duomo)", "lat": 45.4642, "lon": 9.1919, "country": "Italy", "year": 1965, "style": "Gothic / Neo-Gothic"},
    {"name": "Westminster Abbey", "lat": 51.4993, "lon": -0.1273, "country": "England", "year": 1269, "style": "Gothic"},
    {"name": "Hagia Sophia", "lat": 41.0086, "lon": 28.9802, "country": "Turkey", "year": 537, "style": "Byzantine"},
    {"name": "Canterbury Cathedral", "lat": 51.2798, "lon": 1.0830, "country": "England", "year": 1077, "style": "Romanesque / Gothic"},
    {"name": "St. Basil's Cathedral", "lat": 55.7525, "lon": 37.6231, "country": "Russia", "year": 1561, "style": "Russian Orthodox"},
    {"name": "Chartres Cathedral", "lat": 48.4478, "lon": 1.4877, "country": "France", "year": 1220, "style": "High Gothic"},
    {"name": "Seville Cathedral", "lat": 37.3861, "lon": -5.9926, "country": "Spain", "year": 1528, "style": "Gothic"},
    {"name": "Florence Cathedral (Duomo)", "lat": 43.7731, "lon": 11.2560, "country": "Italy", "year": 1436, "style": "Gothic / Renaissance"},
    {"name": "St. Paul's Cathedral", "lat": 51.5138, "lon": -0.0984, "country": "England", "year": 1710, "style": "English Baroque"},
    {"name": "Cathedral of Brasilia", "lat": -15.7983, "lon": -47.8757, "country": "Brazil", "year": 1970, "style": "Modernist"},
    {"name": "Basilica of the Sacred Heart", "lat": 48.8867, "lon": 2.3431, "country": "France", "year": 1914, "style": "Romano-Byzantine"},
    {"name": "St. Mark's Basilica", "lat": 45.4345, "lon": 12.3396, "country": "Italy", "year": 1094, "style": "Italo-Byzantine"},
    {"name": "Siena Cathedral", "lat": 43.3176, "lon": 11.3295, "country": "Italy", "year": 1263, "style": "Italian Romanesque-Gothic"},
    {"name": "York Minster", "lat": 53.9621, "lon": -1.0819, "country": "England", "year": 1472, "style": "Gothic"},
    {"name": "Burgos Cathedral", "lat": 42.3404, "lon": -3.7037, "country": "Spain", "year": 1260, "style": "French Gothic"},
    {"name": "Reims Cathedral", "lat": 49.2538, "lon": 3.9743, "country": "France", "year": 1275, "style": "High Gothic"},
    {"name": "Amiens Cathedral", "lat": 49.8950, "lon": 2.3022, "country": "France", "year": 1270, "style": "High Gothic"},
    {"name": "Notre-Dame de Strasbourg", "lat": 48.5818, "lon": 7.7510, "country": "France", "year": 1439, "style": "Romanesque / Gothic"},
    {"name": "Basilica of Our Lady of Guadalupe", "lat": 19.4853, "lon": -99.1178, "country": "Mexico", "year": 1976, "style": "Modernist"},
    {"name": "La Seu (Palma Cathedral)", "lat": 39.5674, "lon": 2.6486, "country": "Spain", "year": 1601, "style": "Gothic"},
    {"name": "Washington National Cathedral", "lat": 38.9306, "lon": -77.0707, "country": "USA", "year": 1990, "style": "Neo-Gothic"},
    {"name": "Church of the Holy Sepulchre", "lat": 31.7785, "lon": 35.2296, "country": "Israel", "year": 335, "style": "Romanesque / Crusader"},
    {"name": "Basilica of the National Shrine", "lat": 38.9332, "lon": -76.9942, "country": "USA", "year": 1961, "style": "Byzantine Revival"},
    {"name": "Helsinki Cathedral", "lat": 60.1703, "lon": 24.9522, "country": "Finland", "year": 1852, "style": "Neoclassical"},
    {"name": "Alexander Nevsky Cathedral", "lat": 42.6960, "lon": 23.3329, "country": "Bulgaria", "year": 1912, "style": "Neo-Byzantine"},
    {"name": "Cathedral of Christ the Saviour", "lat": 55.7446, "lon": 37.6056, "country": "Russia", "year": 2000, "style": "Russian Revival (rebuilt)"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 6. HINDU TEMPLES
# ═══════════════════════════════════════════════════════════════════════════════
HINDU_TEMPLES = [
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "note": "Largest Hindu temple complex; dedicated to Vishnu; 12th century"},
    {"name": "Brihadeeswarar Temple", "lat": 10.7828, "lon": 79.1318, "country": "India", "note": "Chola dynasty masterpiece; 1010 AD; granite vimana tower 66m"},
    {"name": "Meenakshi Amman Temple", "lat": 9.9195, "lon": 78.1193, "country": "India", "note": "14 gopurams; 33,000 sculptures; Madurai's living heritage"},
    {"name": "Kashi Vishwanath Temple", "lat": 25.3109, "lon": 83.0107, "country": "India", "note": "Jyotirlinga of Lord Shiva; holiest Shiva temple; Varanasi"},
    {"name": "Jagannath Temple, Puri", "lat": 19.8048, "lon": 85.8180, "country": "India", "note": "One of Char Dham; Rath Yatra festival; 12th century"},
    {"name": "Sri Ranganathaswamy Temple", "lat": 10.8627, "lon": 78.6874, "country": "India", "note": "Largest functioning Hindu temple in the world; 156 acres; Vishnu"},
    {"name": "Somnath Temple", "lat": 20.8880, "lon": 70.4017, "country": "India", "note": "First of 12 Jyotirlinga shrines; destroyed and rebuilt multiple times"},
    {"name": "Tirumala Venkateswara Temple", "lat": 13.6833, "lon": 79.3472, "country": "India", "note": "Richest temple in the world; 50,000+ daily pilgrims"},
    {"name": "Konark Sun Temple", "lat": 19.8876, "lon": 86.0945, "country": "India", "note": "Chariot-shaped temple to Surya; 13th century; UNESCO site"},
    {"name": "Kedarnath Temple", "lat": 30.7352, "lon": 79.0669, "country": "India", "note": "Char Dham; Jyotirlinga; 3,583m altitude; 8th century"},
    {"name": "Badrinath Temple", "lat": 30.7433, "lon": 79.4938, "country": "India", "note": "Char Dham; dedicated to Vishnu; Himalayas at 3,133m"},
    {"name": "Rameswaram Temple", "lat": 9.2881, "lon": 79.3174, "country": "India", "note": "Char Dham; longest corridor of any Hindu temple in India"},
    {"name": "Dwarkadheesh Temple", "lat": 22.2376, "lon": 68.9674, "country": "India", "note": "Char Dham; 5 storeys; believed founded by Lord Krishna's grandson"},
    {"name": "Prambanan", "lat": -7.7520, "lon": 110.4914, "country": "Indonesia", "note": "Largest Hindu temple in Indonesia; 9th century; Trimurti temples"},
    {"name": "Pashupatinath Temple", "lat": 27.7104, "lon": 85.3488, "country": "Nepal", "note": "Holiest Hindu temple in Nepal; on Bagmati River; cremation ghats"},
    {"name": "BAPS Swaminarayan Akshardham", "lat": 28.6127, "lon": 77.2773, "country": "India", "note": "New Delhi; 10,000 years of Indian culture; opened 2005"},
    {"name": "Virupaksha Temple", "lat": 15.3350, "lon": 76.4600, "country": "India", "note": "Hampi; 7th century; continuously functioning since inception"},
    {"name": "Khajuraho Temples", "lat": 24.8318, "lon": 79.9199, "country": "India", "note": "Chandela dynasty; erotic sculptures; UNESCO World Heritage"},
    {"name": "Golden Temple Vellore", "lat": 12.9254, "lon": 79.0697, "country": "India", "note": "Sripuram; covered in 1,500 kg of gold; modern temple"},
    {"name": "Tanah Lot Temple", "lat": -8.6213, "lon": 115.0868, "country": "Indonesia", "note": "Sea temple on rock formation off Bali coast; sunset icon"},
    {"name": "Murugan Temple, Batu Caves", "lat": 3.2379, "lon": 101.6841, "country": "Malaysia", "note": "42.7m Lord Murugan statue; 272 steps; limestone caves"},
    {"name": "Lingaraj Temple", "lat": 20.2388, "lon": 85.8340, "country": "India", "note": "Bhubaneswar; 11th century; 55m deul tower; Shiva-Vishnu"},
    {"name": "Mahabalipuram Shore Temple", "lat": 12.6172, "lon": 80.1994, "country": "India", "note": "Pallava dynasty; 8th century; structural temple on Bay of Bengal"},
    {"name": "Ellora Kailasa Temple", "lat": 20.0268, "lon": 75.1779, "country": "India", "note": "Carved from single rock; 8th century; largest monolithic excavation"},
    {"name": "Sri Padmanabhaswamy Temple", "lat": 8.4826, "lon": 76.9439, "country": "India", "note": "Thiruvananthapuram; richest place of worship; trillion-dollar vault treasures"},
]

CHAR_DHAM_CIRCUIT = [
    {"name": "Yamunotri", "lat": 31.0178, "lon": 78.4633},
    {"name": "Gangotri", "lat": 30.9944, "lon": 78.9400},
    {"name": "Kedarnath", "lat": 30.7352, "lon": 79.0669},
    {"name": "Badrinath", "lat": 30.7433, "lon": 79.4938},
    {"name": "Yamunotri", "lat": 31.0178, "lon": 78.4633},  # close the loop
]

# ═══════════════════════════════════════════════════════════════════════════════
# 7. SACRED MOUNTAINS
# ═══════════════════════════════════════════════════════════════════════════════
SACRED_MOUNTAINS = [
    {"name": "Mount Sinai (Jebel Musa)", "lat": 28.5392, "lon": 33.9750, "elevation_m": 2285, "religion": "Judaism", "note": "Where Moses received the Ten Commandments"},
    {"name": "Mount Kailash", "lat": 31.0672, "lon": 81.3119, "elevation_m": 6638, "religion": "Multi-faith", "note": "Sacred to Hinduism, Buddhism, Jainism, Bon; unclimbed"},
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274, "elevation_m": 3776, "religion": "Shinto", "note": "Japan's highest peak; sacred pilgrimage; UNESCO site"},
    {"name": "Mount Athos", "lat": 40.1564, "lon": 24.3264, "elevation_m": 2033, "religion": "Christianity", "note": "Holy Mountain; 20 monasteries; autonomous monastic state"},
    {"name": "Mount Olympus", "lat": 40.0859, "lon": 22.3583, "elevation_m": 2917, "religion": "Ancient Greek", "note": "Home of the Greek gods; highest peak in Greece"},
    {"name": "Adam's Peak (Sri Pada)", "lat": 6.8096, "lon": 80.4994, "elevation_m": 2243, "religion": "Multi-faith", "note": "Sacred footprint; Buddhist, Hindu, Islamic, Christian traditions"},
    {"name": "Mount Tabor", "lat": 32.6877, "lon": 35.3910, "elevation_m": 575, "religion": "Christianity", "note": "Site of the Transfiguration of Jesus"},
    {"name": "Mount Meru (Arunachala)", "lat": 12.1301, "lon": 79.0668, "elevation_m": 800, "religion": "Hinduism", "note": "Shiva as column of fire; Arunachaleswarar Temple"},
    {"name": "Uluru (Ayers Rock)", "lat": -25.3444, "lon": 131.0369, "elevation_m": 863, "religion": "Indigenous", "note": "Sacred to Anangu Aboriginal people; 600 million years old"},
    {"name": "Mount Tai", "lat": 36.2506, "lon": 117.1009, "elevation_m": 1545, "religion": "Taoism", "note": "Most sacred of China's Five Great Mountains; 6,660 steps"},
    {"name": "Croagh Patrick", "lat": 53.7600, "lon": -9.9017, "elevation_m": 764, "religion": "Christianity", "note": "Ireland's holiest mountain; St. Patrick's 40-day fast"},
    {"name": "Mount Ararat", "lat": 39.7019, "lon": 44.2983, "elevation_m": 5137, "religion": "Christianity", "note": "Traditional resting place of Noah's Ark; Armenia's symbol"},
    {"name": "Emei Shan", "lat": 29.5500, "lon": 103.3333, "elevation_m": 3099, "religion": "Buddhism", "note": "One of China's Four Sacred Buddhist Mountains; golden summit"},
    {"name": "Wutai Shan", "lat": 39.0833, "lon": 113.5833, "elevation_m": 3058, "religion": "Buddhism", "note": "Five Terrace Mountain; Manjushri bodhisattva; oldest Buddhist site in China"},
    {"name": "Mount Zion", "lat": 31.7717, "lon": 35.2292, "elevation_m": 765, "religion": "Multi-faith", "note": "Jerusalem; David's Tomb, Cenacle (Last Supper room), Dormition Abbey"},
    {"name": "Glastonbury Tor", "lat": 51.1443, "lon": -2.6985, "elevation_m": 158, "religion": "Multi-faith", "note": "Mythical Avalon; St. Michael's Tower; ley lines intersection"},
    {"name": "Popocatepetl", "lat": 19.0225, "lon": -98.6278, "elevation_m": 5426, "religion": "Indigenous", "note": "Sacred to Aztecs; Smoking Mountain; active volcano near Mexico City"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 8. MONASTERIES
# ═══════════════════════════════════════════════════════════════════════════════
MONASTERIES = [
    {"name": "Mont Saint-Michel", "lat": 48.6361, "lon": -1.5115, "country": "France", "religion": "Christianity", "note": "Tidal island abbey; Benedictine; founded 708 AD"},
    {"name": "Meteora Monasteries", "lat": 39.7139, "lon": 21.6308, "country": "Greece", "religion": "Christianity", "note": "Six monasteries on sandstone pillars; 14th century"},
    {"name": "Tiger's Nest (Paro Taktsang)", "lat": 27.4913, "lon": 89.3636, "country": "Bhutan", "religion": "Buddhism", "note": "Cliffside monastery at 3,120m; Guru Rinpoche; 1692"},
    {"name": "Rila Monastery", "lat": 42.1334, "lon": 23.3404, "country": "Bulgaria", "religion": "Christianity", "note": "Largest Eastern Orthodox monastery in Bulgaria; 10th century"},
    {"name": "Potala Palace", "lat": 29.6577, "lon": 91.1170, "country": "China (Tibet)", "religion": "Buddhism", "note": "Winter palace of Dalai Lama; 1,000 rooms; 3,700m altitude"},
    {"name": "Sumela Monastery", "lat": 40.6874, "lon": 39.6597, "country": "Turkey", "religion": "Christianity", "note": "Greek Orthodox; carved into cliff face at 1,200m; 386 AD"},
    {"name": "Key Monastery", "lat": 32.5292, "lon": 78.0139, "country": "India", "religion": "Buddhism", "note": "Spiti Valley; 1,000 years old; 4,166m altitude; Tibetan Buddhist"},
    {"name": "Taktshang Goenpa", "lat": 27.2194, "lon": 89.4861, "country": "Bhutan", "religion": "Buddhism", "note": "Second Tiger's Nest; Bumthang valley"},
    {"name": "Montserrat Monastery", "lat": 41.5934, "lon": 1.8383, "country": "Spain", "religion": "Christianity", "note": "Benedictine; Black Madonna; 1025 AD; serrated mountain"},
    {"name": "Great Lavra Monastery", "lat": 40.1583, "lon": 24.3750, "country": "Greece", "religion": "Christianity", "note": "Oldest monastery on Mount Athos; 963 AD; Athanasius the Athonite"},
    {"name": "Monastery of Saint Catherine", "lat": 28.5561, "lon": 33.9761, "country": "Egypt", "religion": "Christianity", "note": "Oldest operating monastery; 6th century; Burning Bush; Mount Sinai"},
    {"name": "Tashilhunpo Monastery", "lat": 29.2733, "lon": 88.8781, "country": "China (Tibet)", "religion": "Buddhism", "note": "Seat of the Panchen Lama; Shigatse; founded 1447"},
    {"name": "Ostrog Monastery", "lat": 42.6750, "lon": 19.0308, "country": "Montenegro", "religion": "Christianity", "note": "Serbian Orthodox; carved into cliff face; 17th century"},
    {"name": "Shaolin Monastery", "lat": 34.5076, "lon": 112.9374, "country": "China", "religion": "Buddhism", "note": "Birthplace of Chan (Zen) Buddhism and Shaolin Kung Fu; 495 AD"},
    {"name": "Mount St. Bernard Abbey", "lat": 52.7442, "lon": -1.3322, "country": "England", "religion": "Christianity", "note": "Trappist; only Cistercian abbey in England; 1835"},
    {"name": "Hanging Monastery (Xuankong Si)", "lat": 39.6553, "lon": 113.7147, "country": "China", "religion": "Multi-faith", "note": "Built into cliff face; Taoist, Buddhist, Confucian; 491 AD"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 9. PILGRIMAGE ROUTES
# ═══════════════════════════════════════════════════════════════════════════════
VIA_FRANCIGENA = [
    {"name": "Canterbury", "lat": 51.2798, "lon": 1.0830},
    {"name": "Calais", "lat": 50.9513, "lon": 1.8587},
    {"name": "Arras", "lat": 50.2910, "lon": 2.7775},
    {"name": "Laon", "lat": 49.5630, "lon": 3.6247},
    {"name": "Reims", "lat": 49.2538, "lon": 3.9743},
    {"name": "Chalons-en-Champagne", "lat": 48.9566, "lon": 4.3630},
    {"name": "Bar-sur-Aube", "lat": 48.2333, "lon": 4.7000},
    {"name": "Besancon", "lat": 47.2378, "lon": 6.0241},
    {"name": "Lausanne", "lat": 46.5197, "lon": 6.6323},
    {"name": "Great St Bernard Pass", "lat": 45.8692, "lon": 7.1708},
    {"name": "Aosta", "lat": 45.7350, "lon": 7.3133},
    {"name": "Ivrea", "lat": 45.4667, "lon": 7.8756},
    {"name": "Vercelli", "lat": 45.3256, "lon": 8.4228},
    {"name": "Pavia", "lat": 45.1847, "lon": 9.1582},
    {"name": "Fidenza", "lat": 44.8667, "lon": 10.0600},
    {"name": "Pontremoli", "lat": 44.3750, "lon": 9.8794},
    {"name": "Lucca", "lat": 43.8431, "lon": 10.5027},
    {"name": "San Gimignano", "lat": 43.4677, "lon": 11.0433},
    {"name": "Siena", "lat": 43.3188, "lon": 11.3308},
    {"name": "Bolsena", "lat": 42.6430, "lon": 11.9870},
    {"name": "Viterbo", "lat": 42.4168, "lon": 12.1086},
    {"name": "Rome", "lat": 41.9028, "lon": 12.4964},
]

SHIKOKU_88_TEMPLES = [
    {"name": "Temple 1 - Ryozen-ji (Tokushima)", "lat": 34.0808, "lon": 134.5081},
    {"name": "Temple 12 - Shosan-ji", "lat": 34.0000, "lon": 134.2833},
    {"name": "Temple 23 - Yakuo-ji", "lat": 33.7333, "lon": 134.5500},
    {"name": "Temple 24 - Hotsumisaki-ji (Kochi)", "lat": 33.2500, "lon": 134.1833},
    {"name": "Temple 31 - Chikurin-ji", "lat": 33.5333, "lon": 133.5667},
    {"name": "Temple 37 - Iwamoto-ji", "lat": 33.0000, "lon": 132.9333},
    {"name": "Temple 38 - Kongofuku-ji", "lat": 32.7333, "lon": 133.0000},
    {"name": "Temple 45 - Iwaya-ji (Ehime)", "lat": 33.6500, "lon": 132.9167},
    {"name": "Temple 51 - Ishite-ji", "lat": 33.8400, "lon": 132.7900},
    {"name": "Temple 60 - Yokomine-ji", "lat": 33.8833, "lon": 133.1333},
    {"name": "Temple 65 - Sankaku-ji", "lat": 33.9833, "lon": 133.3167},
    {"name": "Temple 75 - Zentsu-ji (Kagawa)", "lat": 34.2167, "lon": 133.7667},
    {"name": "Temple 84 - Yashima-ji", "lat": 34.3667, "lon": 134.1167},
    {"name": "Temple 88 - Okuboji", "lat": 34.1667, "lon": 134.1833},
    {"name": "Temple 1 - Ryozen-ji (return)", "lat": 34.0808, "lon": 134.5081},
]

BUDDHIST_CIRCUIT_INDIA = [
    {"name": "Lumbini (Birth)", "lat": 27.4833, "lon": 83.2767},
    {"name": "Bodh Gaya (Enlightenment)", "lat": 24.6961, "lon": 84.9869},
    {"name": "Sarnath (First Sermon)", "lat": 25.3810, "lon": 83.0247},
    {"name": "Kushinagar (Parinirvana)", "lat": 26.7409, "lon": 83.8869},
    {"name": "Rajgir (Nalanda)", "lat": 25.0270, "lon": 85.4220},
    {"name": "Vaishali", "lat": 25.9829, "lon": 85.1313},
    {"name": "Shravasti", "lat": 27.5089, "lon": 82.0411},
    {"name": "Sankassa", "lat": 27.3333, "lon": 79.6167},
    {"name": "Lumbini (return)", "lat": 27.4833, "lon": 83.2767},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 10. ANCIENT RELIGIOUS SITES
# ═══════════════════════════════════════════════════════════════════════════════
ANCIENT_RELIGIOUS_SITES = [
    {"name": "Gobekli Tepe", "lat": 37.2233, "lon": 38.9224, "country": "Turkey", "age_years": 11500, "note": "Oldest known temple complex; predates pottery and agriculture"},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "country": "England", "age_years": 5000, "note": "Neolithic stone circle; solstice alignment; 25-tonne sarsen stones"},
    {"name": "Delphi", "lat": 38.4824, "lon": 22.5010, "country": "Greece", "age_years": 3400, "note": "Oracle of Apollo; navel of the world (omphalos); Pythian Games"},
    {"name": "Karnak Temple Complex", "lat": 25.7188, "lon": 32.6573, "country": "Egypt", "age_years": 4000, "note": "Largest ancient religious site; 2 million sq.m; Amun-Ra"},
    {"name": "Luxor Temple", "lat": 25.6995, "lon": 32.6390, "country": "Egypt", "age_years": 3400, "note": "Avenue of Sphinxes; Amenhotep III and Ramesses II; Thebes"},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4755, "country": "Ireland", "age_years": 5200, "note": "Passage tomb older than Stonehenge; winter solstice light box"},
    {"name": "Chichen Itza (El Castillo)", "lat": 20.6843, "lon": -88.5678, "country": "Mexico", "age_years": 1500, "note": "Maya pyramid; equinox serpent shadow; Kukulkan worship"},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438, "country": "Mexico", "age_years": 2100, "note": "Pyramid of the Sun and Moon; Avenue of the Dead; pre-Aztec"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "country": "Peru", "age_years": 550, "note": "Intihuatana sun stone; Inca sacred site; 2,430m altitude"},
    {"name": "Temple of Artemis (Ephesus)", "lat": 37.9497, "lon": 27.3639, "country": "Turkey", "age_years": 2550, "note": "One of Seven Wonders of the Ancient World; Greek goddess"},
    {"name": "Parthenon", "lat": 37.9715, "lon": 23.7267, "country": "Greece", "age_years": 2460, "note": "Temple of Athena; Athenian Acropolis; Doric perfection"},
    {"name": "Abu Simbel", "lat": 22.3360, "lon": 31.6256, "country": "Egypt", "age_years": 3280, "note": "Four colossal Ramesses II statues; relocated for Aswan Dam"},
    {"name": "Baalbek", "lat": 34.0069, "lon": 36.2039, "country": "Lebanon", "age_years": 2900, "note": "Roman temple of Jupiter; largest stones ever quarried (1,000 tonnes)"},
    {"name": "Persepolis", "lat": 29.9350, "lon": 52.8912, "country": "Iran", "age_years": 2520, "note": "Achaemenid ceremonial capital; Gate of All Nations; Nowruz"},
    {"name": "Avebury", "lat": 51.4288, "lon": -1.8544, "country": "England", "age_years": 4700, "note": "Largest stone circle in the world; entire village inside it"},
    {"name": "Carnac Stones", "lat": 47.5830, "lon": -3.0747, "country": "France", "age_years": 6000, "note": "Over 3,000 megalithic standing stones; Neolithic alignments"},
    {"name": "Mnajdra Temples", "lat": 35.8267, "lon": 14.4361, "country": "Malta", "age_years": 5500, "note": "Among oldest freestanding structures; equinox alignment; Megalithic"},
    {"name": "Gozo Ggantija", "lat": 36.0478, "lon": 14.2689, "country": "Malta", "age_years": 5500, "note": "Predates Stonehenge and Pyramids; two Neolithic temples"},
    {"name": "Moai of Easter Island", "lat": -27.1127, "lon": -109.3497, "country": "Chile", "age_years": 800, "note": "887 monolithic statues; Rapa Nui ancestor worship"},
    {"name": "Tiwanaku", "lat": -16.5546, "lon": -68.6735, "country": "Bolivia", "age_years": 2500, "note": "Pre-Inca spiritual centre; Gate of the Sun; Akapana pyramid"},
    {"name": "Great Zimbabwe", "lat": -20.2674, "lon": 30.9338, "country": "Zimbabwe", "age_years": 900, "note": "Stone city and spiritual centre; Shona civilisation; conical tower"},
    {"name": "Borobudur", "lat": -7.6079, "lon": 110.2038, "country": "Indonesia", "age_years": 1250, "note": "Largest Buddhist monument; 2,672 relief panels; mandala design"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# MAP TYPE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════
MAP_TYPES = [
    "Holy Cities",
    "Camino de Santiago",
    "Buddhist Temples",
    "Islamic Mosques",
    "Christian Cathedrals",
    "Hindu Temples",
    "Sacred Mountains",
    "Monasteries",
    "Pilgrimage Routes",
    "Ancient Religious Sites",
]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: dark-themed Folium base map
# ═══════════════════════════════════════════════════════════════════════════════
def _base_map(center=(25.0, 40.0), zoom=2):
    """Return a Folium map with CartoDB dark_matter tiles."""
    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark Matter",
        name="Dark Base",
    ).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: dark matplotlib style
# ═══════════════════════════════════════════════════════════════════════════════
def _dark_fig(figsize=(8, 4)):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    ax.tick_params(colors=_TEXT_SEC, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.grid(True, color=_BORDER, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    return fig, ax, plt


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: render stats row
# ═══════════════════════════════════════════════════════════════════════════════
def _stats_row(metrics: dict):
    """Display a row of st.metric cards for the given {label: value} dict."""
    cols = st.columns(min(len(metrics), 5))
    for i, (label, value) in enumerate(metrics.items()):
        cols[i % len(cols)].metric(label, value)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: show dataframe + download CSV
# ═══════════════════════════════════════════════════════════════════════════════
def _table_and_download(df: pd.DataFrame, label: str, filename: str, key: str):
    """Show an expandable table and a CSV download button."""
    with st.expander(f"Full Data Table ({len(df)} {label})", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} {label} (CSV)",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# OVERPASS HELPERS (Buddhist Temples, Monasteries)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _overpass_buddhist_temples(lat: float, lon: float, radius_km: float):
    """Fetch Buddhist temples from OSM near a given point."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["amenity"="place_of_worship"]["religion"="buddhist"](around:{radius_m},{lat},{lon});
  way["amenity"="place_of_worship"]["religion"="buddhist"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []
    return _extract_osm_pois(result)


@st.cache_data(ttl=3600)
def _overpass_monasteries(lat: float, lon: float, radius_km: float):
    """Fetch monasteries from OSM near a given point."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["amenity"="monastery"](around:{radius_m},{lat},{lon});
  way["amenity"="monastery"](around:{radius_m},{lat},{lon});
  node["building"="monastery"](around:{radius_m},{lat},{lon});
  way["building"="monastery"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []
    return _extract_osm_pois(result)


def _extract_osm_pois(data: dict) -> list:
    """Extract POIs with coordinates from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])
    pois = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat, lon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [(node_lookup[n][0], node_lookup[n][1]) for n in nodes if n in node_lookup]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)
        if lat is None or lon is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        pois.append({"name": name, "lat": lat, "lon": lon, "tags": tags})
    return pois


# ═══════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL MAP RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def _render_holy_cities():
    """Map 1: Holy Cities of the World."""
    st.markdown("#### Holy Cities of the World")
    st.caption("25+ cities sacred to major world religions, with religious affiliation and cultural significance.")

    # Stats
    religion_counts = {}
    for c in HOLY_CITIES:
        r = c["religion"]
        religion_counts[r] = religion_counts.get(r, 0) + 1
    _stats_row({"Total Holy Cities": len(HOLY_CITIES), **{k: v for k, v in sorted(religion_counts.items(), key=lambda x: -x[1])[:4]}})

    # Map
    m = _base_map()
    for c in HOLY_CITIES:
        color = RELIGION_COLORS.get(c["religion"], "#8b97b0")
        popup_html = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(c['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(c['religion'])}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(c['significance'][:150])}</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=escape(c["name"]),
        ).add_to(m)

    # Legend
    legend_items = " ".join(
        f'<span style="color:{RELIGION_COLORS.get(r, "#8b97b0")}; font-size:0.8rem;">&#9679; {escape(r)}</span>'
        for r in sorted(religion_counts.keys())
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=550)

    # Chart
    fig, ax, plt = _dark_fig()
    religions = list(religion_counts.keys())
    counts = [religion_counts[r] for r in religions]
    colors = [RELIGION_COLORS.get(r, "#8b97b0") for r in religions]
    ax.barh(range(len(religions)), counts, color=colors, alpha=0.85)
    ax.set_yticks(range(len(religions)))
    ax.set_yticklabels([escape(r) for r in religions], color=_TEXT_SEC, fontsize=9)
    ax.set_xlabel("Number of Cities", color=_TEXT_SEC)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Table + download
    df = pd.DataFrame(HOLY_CITIES)
    _table_and_download(df, "Holy Cities", "holy_cities.csv", "dl_holy_cities")


def _render_camino():
    """Map 2: Camino de Santiago routes."""
    st.markdown("#### Camino de Santiago")
    st.caption("The French Way (Camino Frances) and Portuguese Way, two of the most popular pilgrimage routes to Santiago de Compostela.")

    _stats_row({
        "Camino Frances Stages": len(CAMINO_FRANCES),
        "Camino Portugues Stages": len(CAMINO_PORTUGUES),
        "Frances Distance": "~780 km",
        "Portugues Distance": "~620 km",
    })

    m = _base_map(center=(42.5, -4.0), zoom=6)

    # Camino Frances polyline
    coords_fr = [[p["lat"], p["lon"]] for p in CAMINO_FRANCES]
    folium.PolyLine(coords_fr, color="#f59e0b", weight=4, opacity=0.9, tooltip="Camino Frances").add_to(m)
    for p in CAMINO_FRANCES:
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=5,
            color="#f59e0b",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.8,
            weight=1,
            tooltip=escape(p["name"]),
        ).add_to(m)

    # Camino Portugues polyline
    coords_pt = [[p["lat"], p["lon"]] for p in CAMINO_PORTUGUES]
    folium.PolyLine(coords_pt, color="#3b82f6", weight=4, opacity=0.9, tooltip="Camino Portugues").add_to(m)
    for p in CAMINO_PORTUGUES:
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=5,
            color="#3b82f6",
            fill=True,
            fill_color="#3b82f6",
            fill_opacity=0.8,
            weight=1,
            tooltip=escape(p["name"]),
        ).add_to(m)

    # Start/end markers
    folium.Marker(
        location=[CAMINO_FRANCES[0]["lat"], CAMINO_FRANCES[0]["lon"]],
        popup="Start: St-Jean-Pied-de-Port",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        location=[CAMINO_FRANCES[-1]["lat"], CAMINO_FRANCES[-1]["lon"]],
        popup="End: Santiago de Compostela",
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
    ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-bottom:0.5rem;">'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9644; Camino Frances</span>'
        '<span style="color:#3b82f6; font-size:0.8rem;">&#9644; Camino Portugues</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=550)

    # Table
    all_stages = (
        [{"route": "Camino Frances", **s} for s in CAMINO_FRANCES]
        + [{"route": "Camino Portugues", **s} for s in CAMINO_PORTUGUES]
    )
    df = pd.DataFrame(all_stages)
    _table_and_download(df, "Camino Stages", "camino_de_santiago.csv", "dl_camino")


def _render_buddhist_temples():
    """Map 3: Buddhist Temples (hardcoded + optional Overpass)."""
    st.markdown("#### Famous Buddhist Temples")
    st.caption("20 world-renowned Buddhist temples plus optional live Overpass search for nearby temples.")

    _stats_row({
        "Curated Temples": len(BUDDHIST_TEMPLES),
        "Countries": len(set(t["country"] for t in BUDDHIST_TEMPLES)),
    })

    # Optional Overpass enrichment
    with st.expander("Search more temples via OpenStreetMap", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            bt_lat = st.number_input("Latitude", value=13.75, format="%.4f", key="bt_lat")
        with c2:
            bt_lon = st.number_input("Longitude", value=100.49, format="%.4f", key="bt_lon")
        with c3:
            bt_radius = st.slider("Radius (km)", 1, 50, 10, key="bt_radius")
        if st.button("Search OSM", key="bt_osm_search", width="stretch"):
            st.session_state["bt_osm"] = _overpass_buddhist_temples(bt_lat, bt_lon, bt_radius)

    osm_temples = st.session_state.get("bt_osm", [])

    # Map
    m = _base_map(center=(20.0, 100.0), zoom=3)
    for t in BUDDHIST_TEMPLES:
        popup_html = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(t['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(t['country'])}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(t['note'][:150])}</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=7,
            color="#8b5cf6",
            fill=True,
            fill_color="#8b5cf6",
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=escape(t["name"]),
        ).add_to(m)

    # OSM results in different colour
    for t in osm_temples:
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=5,
            color="#06b6d4",
            fill=True,
            fill_color="#06b6d4",
            fill_opacity=0.6,
            weight=1,
            tooltip=escape(t["name"]),
        ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-bottom:0.5rem;">'
        '<span style="color:#8b5cf6; font-size:0.8rem;">&#9679; Famous Temples</span>'
        '<span style="color:#06b6d4; font-size:0.8rem;">&#9679; OSM Results</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=550)

    # Chart by country
    country_counts = {}
    for t in BUDDHIST_TEMPLES:
        country_counts[t["country"]] = country_counts.get(t["country"], 0) + 1
    fig, ax, plt = _dark_fig()
    countries = sorted(country_counts.keys(), key=lambda c: -country_counts[c])
    cnts = [country_counts[c] for c in countries]
    ax.barh(range(len(countries)), cnts, color="#8b5cf6", alpha=0.85)
    ax.set_yticks(range(len(countries)))
    ax.set_yticklabels(countries, color=_TEXT_SEC, fontsize=9)
    ax.set_xlabel("Number of Temples", color=_TEXT_SEC)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(BUDDHIST_TEMPLES)
    if osm_temples:
        osm_df = pd.DataFrame(osm_temples)[["name", "lat", "lon"]]
        osm_df["country"] = "OSM"
        osm_df["note"] = "From OpenStreetMap"
        df = pd.concat([df, osm_df], ignore_index=True)
    _table_and_download(df, "Buddhist Temples", "buddhist_temples.csv", "dl_buddhist")


def _render_islamic_mosques():
    """Map 4: Islamic Mosques."""
    st.markdown("#### Famous Islamic Mosques")
    st.caption("25+ of the world's most significant mosques, with capacity, year of construction, and historical notes.")

    total_capacity = sum(m["capacity"] for m in ISLAMIC_MOSQUES)
    oldest = min(ISLAMIC_MOSQUES, key=lambda m: m["year"])
    _stats_row({
        "Total Mosques": len(ISLAMIC_MOSQUES),
        "Countries": len(set(m["country"] for m in ISLAMIC_MOSQUES)),
        "Combined Capacity": f"{total_capacity:,}",
        "Oldest": f"{oldest['name']} ({oldest['year']})",
    })

    m = _base_map(center=(30.0, 45.0), zoom=3)
    for mosque in ISLAMIC_MOSQUES:
        popup_html = (
            f"<div style='max-width:240px;'>"
            f"<strong>{escape(mosque['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(mosque['country'])} &middot; Built {mosque['year']}</span><br/>"
            f"<span style='font-size:0.75rem;'>Capacity: {mosque['capacity']:,}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(mosque['note'][:150])}</span>"
            f"</div>"
        )
        # Size by capacity
        radius = max(5, min(12, 5 + int(mosque["capacity"] / 500000)))
        folium.CircleMarker(
            location=[mosque["lat"], mosque["lon"]],
            radius=radius,
            color="#10b981",
            fill=True,
            fill_color="#10b981",
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=escape(mosque["name"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    # Chart: capacity by mosque
    fig, ax, plt = _dark_fig(figsize=(8, 6))
    sorted_mosques = sorted(ISLAMIC_MOSQUES, key=lambda m: m["capacity"], reverse=True)[:15]
    names = [m["name"][:30] for m in sorted_mosques]
    caps = [m["capacity"] for m in sorted_mosques]
    ax.barh(range(len(names)), caps, color="#10b981", alpha=0.85)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color=_TEXT_SEC, fontsize=8)
    ax.set_xlabel("Capacity", color=_TEXT_SEC)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(ISLAMIC_MOSQUES)
    _table_and_download(df, "Mosques", "islamic_mosques.csv", "dl_mosques")


def _render_christian_cathedrals():
    """Map 5: Christian Cathedrals."""
    st.markdown("#### Famous Christian Cathedrals & Basilicas")
    st.caption("30+ of the most architecturally significant cathedrals and basilicas, with year, style, and location.")

    styles = {}
    for c in CHRISTIAN_CATHEDRALS:
        primary = c["style"].split("/")[0].strip()
        styles[primary] = styles.get(primary, 0) + 1
    oldest = min(CHRISTIAN_CATHEDRALS, key=lambda c: c["year"])
    _stats_row({
        "Total Cathedrals": len(CHRISTIAN_CATHEDRALS),
        "Countries": len(set(c["country"] for c in CHRISTIAN_CATHEDRALS)),
        "Oldest": f"{oldest['name']} ({oldest['year']})",
        "Styles": len(styles),
    })

    STYLE_COLORS = {
        "Renaissance": "#f59e0b",
        "French Gothic": "#3b82f6",
        "Art Nouveau": "#ec4899",
        "High Gothic": "#8b5cf6",
        "Gothic": "#6366f1",
        "Byzantine": "#ef4444",
        "Romanesque": "#f97316",
        "Russian Orthodox": "#e11d48",
        "English Baroque": "#14b8a6",
        "Modernist": "#06b6d4",
        "Italo-Byzantine": "#e879f9",
        "Italian Romanesque-Gothic": "#a855f7",
        "Neoclassical": "#38bdf8",
        "Neo-Byzantine": "#d946ef",
        "Russian Revival (rebuilt)": "#be123c",
        "Neo-Gothic": "#818cf8",
        "Romano-Byzantine": "#fb923c",
        "Byzantine Revival": "#c084fc",
    }

    m = _base_map(center=(45.0, 10.0), zoom=3)
    for c in CHRISTIAN_CATHEDRALS:
        primary_style = c["style"].split("/")[0].strip()
        color = STYLE_COLORS.get(primary_style, "#8b97b0")
        popup_html = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(c['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(c['country'])} &middot; {c['year']}</span><br/>"
            f"<span style='font-size:0.75rem;'>Style: {escape(c['style'])}</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=escape(c["name"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    # Chart: by style
    fig, ax, plt = _dark_fig()
    style_names = sorted(styles.keys(), key=lambda s: -styles[s])
    style_cnts = [styles[s] for s in style_names]
    colors = [STYLE_COLORS.get(s, "#8b97b0") for s in style_names]
    ax.barh(range(len(style_names)), style_cnts, color=colors, alpha=0.85)
    ax.set_yticks(range(len(style_names)))
    ax.set_yticklabels(style_names, color=_TEXT_SEC, fontsize=9)
    ax.set_xlabel("Number of Cathedrals", color=_TEXT_SEC)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(CHRISTIAN_CATHEDRALS)
    _table_and_download(df, "Cathedrals", "christian_cathedrals.csv", "dl_cathedrals")


def _render_hindu_temples():
    """Map 6: Hindu Temples + Char Dham circuit."""
    st.markdown("#### Famous Hindu Temples")
    st.caption("25+ of the most revered Hindu temples worldwide, plus the sacred Char Dham pilgrimage circuit in India.")

    _stats_row({
        "Curated Temples": len(HINDU_TEMPLES),
        "Countries": len(set(t["country"] for t in HINDU_TEMPLES)),
        "Char Dham Sites": 4,
    })

    m = _base_map(center=(20.0, 80.0), zoom=4)

    # Char Dham circuit polyline
    cd_coords = [[p["lat"], p["lon"]] for p in CHAR_DHAM_CIRCUIT]
    folium.PolyLine(cd_coords, color="#f59e0b", weight=3, opacity=0.9, dash_array="8 4", tooltip="Char Dham Circuit").add_to(m)
    for p in CHAR_DHAM_CIRCUIT[:-1]:  # skip duplicate closing point
        folium.Marker(
            location=[p["lat"], p["lon"]],
            popup=escape(p["name"]),
            icon=folium.Icon(color="orange", icon="star", prefix="fa"),
        ).add_to(m)

    for t in HINDU_TEMPLES:
        popup_html = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(t['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(t['country'])}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(t['note'][:150])}</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=7,
            color="#f59e0b",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=escape(t["name"]),
        ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-bottom:0.5rem;">'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9679; Hindu Temples</span>'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9644;&#9644; Char Dham Circuit</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=550)

    # Chart by country
    country_counts = {}
    for t in HINDU_TEMPLES:
        country_counts[t["country"]] = country_counts.get(t["country"], 0) + 1
    fig, ax, plt = _dark_fig()
    countries = sorted(country_counts.keys(), key=lambda c: -country_counts[c])
    cnts = [country_counts[c] for c in countries]
    ax.barh(range(len(countries)), cnts, color="#f59e0b", alpha=0.85)
    ax.set_yticks(range(len(countries)))
    ax.set_yticklabels(countries, color=_TEXT_SEC, fontsize=9)
    ax.set_xlabel("Number of Temples", color=_TEXT_SEC)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(HINDU_TEMPLES)
    _table_and_download(df, "Hindu Temples", "hindu_temples.csv", "dl_hindu")


def _render_sacred_mountains():
    """Map 7: Sacred Mountains."""
    st.markdown("#### Sacred Mountains of the World")
    st.caption("17 mountains venerated across religions, with elevation data and spiritual significance.")

    highest = max(SACRED_MOUNTAINS, key=lambda m: m["elevation_m"])
    _stats_row({
        "Total Mountains": len(SACRED_MOUNTAINS),
        "Religions": len(set(m["religion"] for m in SACRED_MOUNTAINS)),
        "Highest": f"{highest['name']} ({highest['elevation_m']:,}m)",
    })

    m = _base_map(center=(30.0, 60.0), zoom=2)
    for mt in SACRED_MOUNTAINS:
        color = RELIGION_COLORS.get(mt["religion"], "#8b97b0")
        popup_html = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(mt['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(mt['religion'])} &middot; {mt['elevation_m']:,}m</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(mt['note'][:150])}</span>"
            f"</div>"
        )
        # Scale marker by elevation
        radius = max(5, min(12, 5 + int(mt["elevation_m"] / 1500)))
        folium.CircleMarker(
            location=[mt["lat"], mt["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{escape(mt['name'])} ({mt['elevation_m']:,}m)",
        ).add_to(m)

    components.html(m._repr_html_(), height=550)

    # Elevation chart
    fig, ax, plt = _dark_fig(figsize=(8, 5))
    sorted_mts = sorted(SACRED_MOUNTAINS, key=lambda mt: mt["elevation_m"], reverse=True)
    names = [mt["name"][:25] for mt in sorted_mts]
    elevations = [mt["elevation_m"] for mt in sorted_mts]
    colors = [RELIGION_COLORS.get(mt["religion"], "#8b97b0") for mt in sorted_mts]
    ax.barh(range(len(names)), elevations, color=colors, alpha=0.85)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color=_TEXT_SEC, fontsize=8)
    ax.set_xlabel("Elevation (m)", color=_TEXT_SEC)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(SACRED_MOUNTAINS)
    _table_and_download(df, "Sacred Mountains", "sacred_mountains.csv", "dl_mountains")


def _render_monasteries():
    """Map 8: Monasteries (hardcoded + Overpass)."""
    st.markdown("#### Famous Monasteries")
    st.caption("16 of the world's most remarkable monasteries, plus live OpenStreetMap search for nearby ones.")

    religion_counts = {}
    for mon in MONASTERIES:
        r = mon["religion"]
        religion_counts[r] = religion_counts.get(r, 0) + 1
    _stats_row({
        "Curated Monasteries": len(MONASTERIES),
        "Countries": len(set(mon["country"] for mon in MONASTERIES)),
        **{k: v for k, v in sorted(religion_counts.items(), key=lambda x: -x[1])[:3]},
    })

    # Optional Overpass
    with st.expander("Search more monasteries via OpenStreetMap", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            mn_lat = st.number_input("Latitude", value=40.0, format="%.4f", key="mn_lat")
        with c2:
            mn_lon = st.number_input("Longitude", value=22.0, format="%.4f", key="mn_lon")
        with c3:
            mn_radius = st.slider("Radius (km)", 1, 50, 20, key="mn_radius")
        if st.button("Search OSM", key="mn_osm_search", width="stretch"):
            st.session_state["mn_osm"] = _overpass_monasteries(mn_lat, mn_lon, mn_radius)

    osm_monasteries = st.session_state.get("mn_osm", [])

    m = _base_map(center=(35.0, 40.0), zoom=3)
    for mon in MONASTERIES:
        color = RELIGION_COLORS.get(mon["religion"], "#8b97b0")
        popup_html = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(mon['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(mon['country'])} &middot; {escape(mon['religion'])}</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(mon['note'][:150])}</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[mon["lat"], mon["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=escape(mon["name"]),
        ).add_to(m)

    for mon in osm_monasteries:
        folium.CircleMarker(
            location=[mon["lat"], mon["lon"]],
            radius=5,
            color="#06b6d4",
            fill=True,
            fill_color="#06b6d4",
            fill_opacity=0.6,
            weight=1,
            tooltip=escape(mon["name"]),
        ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-bottom:0.5rem;">'
        '<span style="color:#8b5cf6; font-size:0.8rem;">&#9679; Curated Monasteries</span>'
        '<span style="color:#06b6d4; font-size:0.8rem;">&#9679; OSM Results</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=550)

    df = pd.DataFrame(MONASTERIES)
    if osm_monasteries:
        osm_df = pd.DataFrame(osm_monasteries)[["name", "lat", "lon"]]
        osm_df["country"] = "OSM"
        osm_df["religion"] = ""
        osm_df["note"] = "From OpenStreetMap"
        df = pd.concat([df, osm_df], ignore_index=True)
    _table_and_download(df, "Monasteries", "monasteries.csv", "dl_monasteries")


def _render_pilgrimage_routes():
    """Map 9: Pilgrimage Routes (Via Francigena, 88 Temple Trail, Buddhist Circuit)."""
    st.markdown("#### Major Pilgrimage Routes")
    st.caption("Three iconic pilgrimage trails: Via Francigena (Canterbury to Rome), Shikoku 88 Temple Trail, and the Buddhist Circuit in India/Nepal.")

    _stats_row({
        "Via Francigena Stages": len(VIA_FRANCIGENA),
        "88 Temple Trail Stops": len(SHIKOKU_88_TEMPLES),
        "Buddhist Circuit Sites": len(BUDDHIST_CIRCUIT_INDIA),
        "Total Route Points": len(VIA_FRANCIGENA) + len(SHIKOKU_88_TEMPLES) + len(BUDDHIST_CIRCUIT_INDIA),
    })

    route_choice = st.radio(
        "Select route to display",
        ["All Routes", "Via Francigena", "Shikoku 88 Temple Trail", "Buddhist Circuit India"],
        horizontal=True,
        key="route_choice",
    )

    if route_choice == "Via Francigena":
        center, zoom = (46.0, 7.0), 5
    elif route_choice == "Shikoku 88 Temple Trail":
        center, zoom = (33.7, 133.5), 7
    elif route_choice == "Buddhist Circuit India":
        center, zoom = (27.0, 83.0), 6
    else:
        center, zoom = (35.0, 50.0), 2

    m = _base_map(center=center, zoom=zoom)

    # Via Francigena
    if route_choice in ("All Routes", "Via Francigena"):
        coords_vf = [[p["lat"], p["lon"]] for p in VIA_FRANCIGENA]
        folium.PolyLine(coords_vf, color="#3b82f6", weight=4, opacity=0.9, tooltip="Via Francigena").add_to(m)
        for p in VIA_FRANCIGENA:
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=4,
                color="#3b82f6",
                fill=True,
                fill_color="#3b82f6",
                fill_opacity=0.8,
                weight=1,
                tooltip=escape(p["name"]),
            ).add_to(m)

    # Shikoku 88
    if route_choice in ("All Routes", "Shikoku 88 Temple Trail"):
        coords_88 = [[p["lat"], p["lon"]] for p in SHIKOKU_88_TEMPLES]
        folium.PolyLine(coords_88, color="#8b5cf6", weight=4, opacity=0.9, tooltip="88 Temple Trail").add_to(m)
        for p in SHIKOKU_88_TEMPLES:
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=4,
                color="#8b5cf6",
                fill=True,
                fill_color="#8b5cf6",
                fill_opacity=0.8,
                weight=1,
                tooltip=escape(p["name"]),
            ).add_to(m)

    # Buddhist Circuit
    if route_choice in ("All Routes", "Buddhist Circuit India"):
        coords_bc = [[p["lat"], p["lon"]] for p in BUDDHIST_CIRCUIT_INDIA]
        folium.PolyLine(coords_bc, color="#f59e0b", weight=4, opacity=0.9, tooltip="Buddhist Circuit").add_to(m)
        for p in BUDDHIST_CIRCUIT_INDIA:
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=5,
                color="#f59e0b",
                fill=True,
                fill_color="#f59e0b",
                fill_opacity=0.8,
                weight=1,
                tooltip=escape(p["name"]),
            ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-bottom:0.5rem;">'
        '<span style="color:#3b82f6; font-size:0.8rem;">&#9644; Via Francigena</span>'
        '<span style="color:#8b5cf6; font-size:0.8rem;">&#9644; 88 Temple Trail</span>'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9644; Buddhist Circuit</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=550)

    # Combine all routes for table/download
    all_points = (
        [{"route": "Via Francigena", **p} for p in VIA_FRANCIGENA]
        + [{"route": "Shikoku 88 Temple Trail", **p} for p in SHIKOKU_88_TEMPLES]
        + [{"route": "Buddhist Circuit India", **p} for p in BUDDHIST_CIRCUIT_INDIA]
    )
    df = pd.DataFrame(all_points)
    _table_and_download(df, "Route Points", "pilgrimage_routes.csv", "dl_routes")


def _render_ancient_religious_sites():
    """Map 10: Ancient Religious Sites."""
    st.markdown("#### Ancient Religious Sites")
    st.caption("22 of humanity's oldest and most significant religious and ceremonial sites, with estimated age.")

    oldest = max(ANCIENT_RELIGIOUS_SITES, key=lambda s: s["age_years"])
    _stats_row({
        "Total Sites": len(ANCIENT_RELIGIOUS_SITES),
        "Countries": len(set(s["country"] for s in ANCIENT_RELIGIOUS_SITES)),
        "Oldest": f"{oldest['name']} (~{oldest['age_years']:,} yrs)",
        "Avg. Age": f"~{int(sum(s['age_years'] for s in ANCIENT_RELIGIOUS_SITES) / len(ANCIENT_RELIGIOUS_SITES)):,} yrs",
    })

    m = _base_map(center=(30.0, 20.0), zoom=2)
    for site in ANCIENT_RELIGIOUS_SITES:
        # Colour gradient by age: older = more red, newer = more cyan
        age_frac = site["age_years"] / 12000.0
        if age_frac > 0.6:
            color = "#ef4444"
        elif age_frac > 0.35:
            color = "#f59e0b"
        else:
            color = "#06b6d4"

        popup_html = (
            f"<div style='max-width:220px;'>"
            f"<strong>{escape(site['name'])}</strong><br/>"
            f"<span style='font-size:0.8rem;color:#666;'>{escape(site['country'])} &middot; ~{site['age_years']:,} years old</span><br/>"
            f"<span style='font-size:0.75rem;'>{escape(site['note'][:150])}</span>"
            f"</div>"
        )
        radius = max(5, min(12, 5 + int(site["age_years"] / 2000)))
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{escape(site['name'])} (~{site['age_years']:,} yrs)",
        ).add_to(m)

    st.markdown(
        '<div style="display:flex; gap:1rem; margin-bottom:0.5rem;">'
        '<span style="color:#ef4444; font-size:0.8rem;">&#9679; &gt;7,000 yrs</span>'
        '<span style="color:#f59e0b; font-size:0.8rem;">&#9679; 4,000-7,000 yrs</span>'
        '<span style="color:#06b6d4; font-size:0.8rem;">&#9679; &lt;4,000 yrs</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=550)

    # Timeline chart
    fig, ax, plt = _dark_fig(figsize=(8, 6))
    sorted_sites = sorted(ANCIENT_RELIGIOUS_SITES, key=lambda s: s["age_years"], reverse=True)
    names = [s["name"][:25] for s in sorted_sites]
    ages = [s["age_years"] for s in sorted_sites]
    colors = []
    for s in sorted_sites:
        frac = s["age_years"] / 12000.0
        if frac > 0.6:
            colors.append("#ef4444")
        elif frac > 0.35:
            colors.append("#f59e0b")
        else:
            colors.append("#06b6d4")
    ax.barh(range(len(names)), ages, color=colors, alpha=0.85)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color=_TEXT_SEC, fontsize=8)
    ax.set_xlabel("Estimated Age (years)", color=_TEXT_SEC)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(ANCIENT_RELIGIOUS_SITES)
    _table_and_download(df, "Ancient Sites", "ancient_religious_sites.csv", "dl_ancient")


# ═══════════════════════════════════════════════════════════════════════════════
# RENDERER DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════
_RENDERERS = {
    "Holy Cities": _render_holy_cities,
    "Camino de Santiago": _render_camino,
    "Buddhist Temples": _render_buddhist_temples,
    "Islamic Mosques": _render_islamic_mosques,
    "Christian Cathedrals": _render_christian_cathedrals,
    "Hindu Temples": _render_hindu_temples,
    "Sacred Mountains": _render_sacred_mountains,
    "Monasteries": _render_monasteries,
    "Pilgrimage Routes": _render_pilgrimage_routes,
    "Ancient Religious Sites": _render_ancient_religious_sites,
}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def render_pilgrimage_maps_tab():
    """Main render function for the Pilgrimage & Sacred Sites tab."""

    # ── Tab header ──
    st.markdown("""
    <div class="tab-header violet">
        <h4>Pilgrimage &amp; Sacred Sites</h4>
        <p>Explore holy cities, sacred mountains, pilgrimage routes, temples, mosques, cathedrals, monasteries, and ancient religious sites from every major faith tradition across the globe.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Map type selector ──
    map_type = st.selectbox(
        "Select Map Type",
        MAP_TYPES,
        key="pilgrimage_map_type",
        help="Choose from 10 curated pilgrimage and sacred site map types.",
    )

    st.markdown("---")

    # ── Generate button ──
    if st.button(f"Generate {map_type} Map", key="pilgrimage_generate", width="stretch"):
        st.session_state["pilgrimage_active"] = map_type

    active = st.session_state.get("pilgrimage_active")
    if active is None:
        st.info("Select a map type and click Generate to explore pilgrimage sites and sacred places worldwide.")
        return

    # ── Render selected map ──
    renderer = _RENDERERS.get(active)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown map type: {active}")
