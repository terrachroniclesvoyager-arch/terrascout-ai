# -*- coding: utf-8 -*-
"""
World Religions & Spiritual Maps module for TerraScout AI.
Curated datasets of religious sites, holy cities, pilgrimage routes,
and religion distribution worldwide.  Uses only free public APIs
(Overpass / OpenStreetMap) plus rich built-in reference data.
No API key required.
"""

import io
import math
import streamlit as st
import pandas as pd
try:
    import folium
    from folium import plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# COLOR PALETTE  (matches TerraScout dark theme)
# ═══════════════════════════════════════════════════════════════════
BG_OUTER = "#0a0e1a"
BG_INNER = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT = "#06b6d4"

RELIGION_COLORS = {
    "Christianity": "#3b82f6",
    "Islam": "#10b981",
    "Hinduism": "#f59e0b",
    "Buddhism": "#f97316",
    "Judaism": "#8b5cf6",
    "Sikhism": "#ec4899",
    "Folk / Traditional": "#a855f7",
    "Shinto": "#ef4444",
    "Baha'i": "#14b8a6",
    "Jainism": "#e879f9",
    "Zoroastrianism": "#facc15",
    "Other": "#64748b",
    "Unaffiliated": "#475569",
}

# ═══════════════════════════════════════════════════════════════════
# 1.  WORLD RELIGION DISTRIBUTION  (curated data, ~60 countries)
# ═══════════════════════════════════════════════════════════════════
RELIGION_BY_COUNTRY = [
    # country, lat, lon, majority, christianity%, islam%, hinduism%, buddhism%, judaism%, other%
    ("United States", 37.09, -95.71, "Christianity", 65, 1.1, 0.7, 1.2, 2.0, 30.0),
    ("Brazil", -14.24, -51.93, "Christianity", 87, 0.1, 0.0, 0.1, 0.0, 12.8),
    ("Mexico", 23.63, -102.55, "Christianity", 90, 0.1, 0.0, 0.1, 0.0, 9.8),
    ("Canada", 56.13, -106.35, "Christianity", 63, 3.2, 1.5, 1.1, 1.0, 30.2),
    ("United Kingdom", 55.38, -3.44, "Christianity", 48, 6.5, 1.7, 0.5, 0.5, 42.8),
    ("France", 46.23, 2.21, "Christianity", 51, 8.8, 0.1, 0.5, 0.5, 39.1),
    ("Germany", 51.17, 10.45, "Christianity", 55, 6.1, 0.1, 0.3, 0.2, 38.3),
    ("Italy", 41.87, 12.57, "Christianity", 80, 3.7, 0.1, 0.2, 0.1, 15.9),
    ("Spain", 40.46, -3.75, "Christianity", 68, 2.6, 0.0, 0.1, 0.1, 29.2),
    ("Poland", 51.92, 19.15, "Christianity", 87, 0.0, 0.0, 0.0, 0.0, 13.0),
    ("Russia", 61.52, 105.32, "Christianity", 73, 10, 0.0, 0.1, 0.2, 16.7),
    ("Greece", 39.07, 21.82, "Christianity", 90, 2.0, 0.0, 0.0, 0.1, 7.9),
    ("Ethiopia", 9.15, 40.49, "Christianity", 62, 34, 0.0, 0.0, 0.0, 4.0),
    ("South Africa", -30.56, 22.94, "Christianity", 80, 1.9, 1.2, 0.2, 0.2, 16.5),
    ("Nigeria", 9.08, 8.68, "Christianity", 46, 52, 0.0, 0.0, 0.0, 2.0),
    ("DR Congo", -4.04, 21.76, "Christianity", 95, 1.5, 0.0, 0.0, 0.0, 3.5),
    ("Kenya", -0.02, 37.91, "Christianity", 85, 11, 0.0, 0.0, 0.0, 4.0),
    ("Egypt", 26.82, 30.80, "Islam", 10, 90, 0.0, 0.0, 0.0, 0.0),
    ("Saudi Arabia", 23.89, 45.08, "Islam", 3, 93, 0.3, 0.2, 0.0, 3.5),
    ("Iran", 32.43, 53.69, "Islam", 0.5, 99, 0.0, 0.0, 0.0, 0.5),
    ("Iraq", 33.22, 43.68, "Islam", 1, 97, 0.0, 0.0, 0.0, 2.0),
    ("Turkey", 38.96, 35.24, "Islam", 0.2, 98, 0.0, 0.0, 0.0, 1.8),
    ("Pakistan", 30.38, 69.35, "Islam", 1.5, 96, 1.6, 0.0, 0.0, 0.9),
    ("Bangladesh", 23.68, 90.36, "Islam", 0.3, 90, 9.0, 0.6, 0.0, 0.1),
    ("Indonesia", -0.79, 113.92, "Islam", 10, 87, 1.7, 0.7, 0.0, 0.6),
    ("Malaysia", 4.21, 101.98, "Islam", 9.2, 61, 6.3, 19.8, 0.0, 3.7),
    ("Morocco", 31.79, -7.09, "Islam", 0.1, 99, 0.0, 0.0, 0.0, 0.9),
    ("Algeria", 28.03, 1.66, "Islam", 0.2, 99, 0.0, 0.0, 0.0, 0.8),
    ("Afghanistan", 33.94, 67.71, "Islam", 0.0, 99.7, 0.0, 0.0, 0.0, 0.3),
    ("Uzbekistan", 41.38, 64.59, "Islam", 2, 93, 0.0, 0.0, 0.0, 5.0),
    ("India", 20.59, 78.96, "Hinduism", 2.3, 14.2, 79.8, 0.7, 0.0, 3.0),
    ("Nepal", 28.39, 84.12, "Hinduism", 1.4, 4.4, 81.3, 9.0, 0.0, 3.9),
    ("Mauritius", -20.35, 57.55, "Hinduism", 32.7, 17.3, 48.5, 0.4, 0.0, 1.1),
    ("Thailand", 15.87, 100.99, "Buddhism", 1.2, 5.4, 0.0, 93, 0.0, 0.4),
    ("Myanmar", 21.92, 95.96, "Buddhism", 6.2, 4.3, 0.5, 88, 0.0, 1.0),
    ("Cambodia", 12.57, 104.99, "Buddhism", 0.5, 2.0, 0.0, 97, 0.0, 0.5),
    ("Sri Lanka", 7.87, 80.77, "Buddhism", 7.4, 9.7, 12.6, 70, 0.0, 0.3),
    ("Japan", 36.20, 138.25, "Buddhism", 1.5, 0.2, 0.0, 36, 0.0, 62.3),
    ("South Korea", 35.91, 127.77, "Christianity", 29, 0.2, 0.0, 23, 0.0, 47.8),
    ("China", 35.86, 104.20, "Folk / Traditional", 5, 1.8, 0.0, 18, 0.0, 75.2),
    ("Vietnam", 14.06, 108.28, "Buddhism", 8.5, 0.1, 0.0, 16, 0.0, 75.4),
    ("Israel", 31.05, 34.85, "Judaism", 2, 17.7, 0.0, 0.2, 74, 6.1),
    ("Philippines", 12.88, 121.77, "Christianity", 92, 5.6, 0.0, 0.1, 0.0, 2.3),
    ("Australia", -25.27, 133.78, "Christianity", 44, 3.2, 1.9, 2.4, 0.4, 48.1),
    ("New Zealand", -40.90, 174.89, "Christianity", 37, 1.3, 2.1, 1.6, 0.2, 57.8),
    ("Argentina", -38.42, -63.62, "Christianity", 85, 1.0, 0.0, 0.1, 0.5, 13.4),
    ("Colombia", 4.57, -74.30, "Christianity", 90, 0.1, 0.0, 0.1, 0.0, 9.8),
    ("Peru", -9.19, -75.02, "Christianity", 94, 0.0, 0.0, 0.1, 0.0, 5.9),
    ("Chile", -35.68, -71.54, "Christianity", 70, 0.1, 0.0, 0.1, 0.0, 29.8),
    ("Ghana", 7.95, -1.02, "Christianity", 71, 18, 0.0, 0.0, 0.0, 11.0),
    ("Tanzania", -6.37, 34.89, "Christianity", 61, 35, 0.0, 0.0, 0.0, 4.0),
    ("Uganda", 1.37, 32.29, "Christianity", 85, 14, 0.0, 0.0, 0.0, 1.0),
    ("Senegal", 14.50, -14.45, "Islam", 4, 95, 0.0, 0.0, 0.0, 1.0),
    ("Sudan", 12.86, 30.22, "Islam", 3, 91, 0.0, 0.0, 0.0, 6.0),
    ("Tunisia", 33.89, 9.54, "Islam", 0.2, 99, 0.0, 0.0, 0.0, 0.8),
    ("Jordan", 30.59, 36.24, "Islam", 2, 97, 0.0, 0.0, 0.0, 1.0),
    ("Lebanon", 33.85, 35.86, "Islam", 34, 61, 0.0, 0.0, 0.0, 5.0),
    ("Singapore", 1.35, 103.82, "Buddhism", 18.8, 14, 5, 33, 0.0, 29.2),
    ("Mongolia", 46.86, 103.85, "Buddhism", 2, 3, 0.0, 54, 0.0, 41.0),
    ("Bhutan", 27.51, 90.43, "Buddhism", 0.5, 0.2, 22.6, 75, 0.0, 1.7),
    ("Laos", 19.86, 102.50, "Buddhism", 1.5, 0.0, 0.0, 65, 0.0, 33.5),
]

# ═══════════════════════════════════════════════════════════════════
# 2.  HOLY CITIES
# ═══════════════════════════════════════════════════════════════════
HOLY_CITIES = [
    {"name": "Jerusalem", "lat": 31.7683, "lon": 35.2137, "religion": "Judaism / Christianity / Islam",
     "significance": "Holiest city for Judaism (Western Wall, Temple Mount), Christianity (Church of the Holy Sepulchre), and third-holiest in Islam (Al-Aqsa Mosque).",
     "visitors": "~4 million/year", "color": "#8b5cf6"},
    {"name": "Mecca", "lat": 21.4225, "lon": 39.8262, "religion": "Islam",
     "significance": "Holiest city in Islam. Site of the Kaaba in the Masjid al-Haram. Every Muslim must perform Hajj here once in a lifetime.",
     "visitors": "~15 million/year (Hajj + Umrah)", "color": "#10b981"},
    {"name": "Medina", "lat": 24.4672, "lon": 39.6112, "religion": "Islam",
     "significance": "Second-holiest city in Islam. Houses the Prophet's Mosque (Al-Masjid an-Nabawi) and the tomb of Prophet Muhammad.",
     "visitors": "~8 million/year", "color": "#10b981"},
    {"name": "Vatican City", "lat": 41.9022, "lon": 12.4534, "religion": "Christianity (Catholic)",
     "significance": "Seat of the Roman Catholic Church and the Pope. St. Peter's Basilica, Sistine Chapel.",
     "visitors": "~5 million/year", "color": "#3b82f6"},
    {"name": "Varanasi (Benares)", "lat": 25.3176, "lon": 83.0065, "religion": "Hinduism",
     "significance": "Oldest living city, holiest city in Hinduism. Ganges ghats, Kashi Vishwanath Temple. Dying here is believed to grant moksha.",
     "visitors": "~6 million/year", "color": "#f59e0b"},
    {"name": "Bodh Gaya", "lat": 24.6961, "lon": 84.9911, "religion": "Buddhism",
     "significance": "Where Siddhartha Gautama attained enlightenment under the Bodhi Tree. Mahabodhi Temple (UNESCO).",
     "visitors": "~3 million/year", "color": "#f97316"},
    {"name": "Lhasa", "lat": 29.6500, "lon": 91.1000, "religion": "Buddhism (Tibetan)",
     "significance": "Traditional seat of the Dalai Lama. Potala Palace, Jokhang Temple. Center of Tibetan Buddhism.",
     "visitors": "~1.5 million/year", "color": "#f97316"},
    {"name": "Amritsar", "lat": 31.6340, "lon": 74.8723, "religion": "Sikhism",
     "significance": "Home of the Golden Temple (Harmandir Sahib), holiest gurdwara in Sikhism. Langar feeds 100,000+ daily.",
     "visitors": "~7 million/year", "color": "#ec4899"},
    {"name": "Haifa", "lat": 32.7940, "lon": 34.9896, "religion": "Baha'i",
     "significance": "World center of the Baha'i Faith. Shrine of the Bab and the terraced gardens (UNESCO).",
     "visitors": "~1 million/year", "color": "#14b8a6"},
    {"name": "Rome", "lat": 41.9028, "lon": 12.4964, "religion": "Christianity (Catholic)",
     "significance": "Eternal City. Major basilicas: St. Peter's, St. John Lateran, Santa Maria Maggiore. Seat of early Christianity.",
     "visitors": "~15 million/year", "color": "#3b82f6"},
    {"name": "Lourdes", "lat": 43.0948, "lon": -0.0459, "religion": "Christianity (Catholic)",
     "significance": "Marian apparition site (1858). Sanctuary of Our Lady of Lourdes. Healing pilgrimages.",
     "visitors": "~5 million/year", "color": "#3b82f6"},
    {"name": "Fatima", "lat": 39.6317, "lon": -8.6742, "religion": "Christianity (Catholic)",
     "significance": "Marian apparition site (1917). Sanctuary of Our Lady of Fatima.",
     "visitors": "~6 million/year", "color": "#3b82f6"},
    {"name": "Kandy", "lat": 7.2906, "lon": 80.6337, "religion": "Buddhism",
     "significance": "Temple of the Sacred Tooth Relic (Sri Dalada Maligawa), most venerated Buddhist relic in Sri Lanka.",
     "visitors": "~2 million/year", "color": "#f97316"},
    {"name": "Kyoto", "lat": 35.0116, "lon": 135.7681, "religion": "Buddhism / Shinto",
     "significance": "Former imperial capital. 2,000+ temples and shrines including Kinkaku-ji, Fushimi Inari.",
     "visitors": "~50 million/year", "color": "#ef4444"},
    {"name": "Allahabad (Prayagraj)", "lat": 25.4358, "lon": 81.8463, "religion": "Hinduism",
     "significance": "Triveni Sangam: confluence of Ganga, Yamuna, and mythical Sarasvati rivers. Site of Kumbh Mela.",
     "visitors": "~5 million/year (120M during Kumbh)", "color": "#f59e0b"},
    {"name": "Bethlehem", "lat": 31.7054, "lon": 35.2024, "religion": "Christianity",
     "significance": "Birthplace of Jesus Christ. Church of the Nativity (UNESCO), one of the oldest churches in the world.",
     "visitors": "~2 million/year", "color": "#3b82f6"},
    {"name": "Nazareth", "lat": 32.6996, "lon": 35.3035, "religion": "Christianity",
     "significance": "Childhood home of Jesus. Basilica of the Annunciation, largest church in the Middle East.",
     "visitors": "~2 million/year", "color": "#3b82f6"},
    {"name": "Karbala", "lat": 32.6160, "lon": 44.0243, "religion": "Islam (Shia)",
     "significance": "Shrine of Imam Husayn. Site of the Battle of Karbala (680 CE). Holiest Shia pilgrimage after Mecca/Medina.",
     "visitors": "~20 million (Arba'een)", "color": "#10b981"},
    {"name": "Najaf", "lat": 31.9965, "lon": 44.3142, "religion": "Islam (Shia)",
     "significance": "Shrine of Imam Ali, first Shia imam. Major center of Islamic scholarship and jurisprudence.",
     "visitors": "~8 million/year", "color": "#10b981"},
    {"name": "Ise", "lat": 34.4551, "lon": 136.7256, "religion": "Shinto",
     "significance": "Ise Grand Shrine (Ise Jingu), most sacred Shinto shrine. Rebuilt every 20 years for 1,300+ years.",
     "visitors": "~8 million/year", "color": "#ef4444"},
    {"name": "Safed (Tzfat)", "lat": 32.9646, "lon": 35.4964, "religion": "Judaism",
     "significance": "One of the four holy cities of Judaism. Center of Kabbalah (Jewish mysticism) since the 16th century.",
     "visitors": "~500,000/year", "color": "#8b5cf6"},
    {"name": "Hebron", "lat": 31.5326, "lon": 35.0998, "religion": "Judaism / Islam",
     "significance": "Cave of the Patriarchs (Machpelah), burial site of Abraham, Isaac, Jacob. Holy to Jews and Muslims.",
     "visitors": "~1 million/year", "color": "#8b5cf6"},
    {"name": "Ujjain", "lat": 23.1828, "lon": 75.7772, "religion": "Hinduism",
     "significance": "One of the four Kumbh Mela sites. Mahakaleshwar Jyotirlinga, one of 12 jyotirlingas of Shiva.",
     "visitors": "~3 million/year", "color": "#f59e0b"},
    {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642, "religion": "Hinduism",
     "significance": "Gateway to the Gods. Where the Ganga enters the Indo-Gangetic plains. Kumbh Mela site. Har Ki Pauri ghat.",
     "visitors": "~5 million/year", "color": "#f59e0b"},
    {"name": "Tirupati", "lat": 13.6288, "lon": 79.4192, "religion": "Hinduism",
     "significance": "Tirumala Venkateswara Temple, richest and most-visited Hindu temple. ~50,000 visitors daily.",
     "visitors": "~18 million/year", "color": "#f59e0b"},
]

# ═══════════════════════════════════════════════════════════════════
# 3.  CATHEDRALS & CHURCHES
# ═══════════════════════════════════════════════════════════════════
CATHEDRALS = [
    {"name": "St. Peter's Basilica", "city": "Vatican City", "lat": 41.9022, "lon": 12.4534,
     "style": "Renaissance / Baroque", "year": 1626, "note": "Largest church in the world. Designed by Bramante, Michelangelo, Bernini."},
    {"name": "Notre-Dame de Paris", "city": "Paris, France", "lat": 48.8530, "lon": 2.3499,
     "style": "French Gothic", "year": 1345, "note": "Iconic Gothic masterpiece. Suffered major fire in 2019, restoration ongoing."},
    {"name": "Sagrada Familia", "city": "Barcelona, Spain", "lat": 41.4036, "lon": 2.1744,
     "style": "Art Nouveau / Gothic", "year": 2026, "note": "Gaudi's unfinished masterpiece, under construction since 1882. UNESCO World Heritage."},
    {"name": "Cologne Cathedral", "city": "Cologne, Germany", "lat": 50.9413, "lon": 6.9583,
     "style": "Gothic", "year": 1880, "note": "Tallest twin-spired church (157m). Construction took 632 years. UNESCO."},
    {"name": "Milan Cathedral (Duomo)", "city": "Milan, Italy", "lat": 45.4641, "lon": 9.1919,
     "style": "Gothic / Renaissance", "year": 1965, "note": "Largest church in Italy. 3,400 statues and 135 spires."},
    {"name": "St. Basil's Cathedral", "city": "Moscow, Russia", "lat": 55.7525, "lon": 37.6231,
     "style": "Russian / Byzantine", "year": 1561, "note": "Iconic onion domes on Red Square. Built by Ivan the Terrible."},
    {"name": "Hagia Sophia", "city": "Istanbul, Turkey", "lat": 41.0086, "lon": 28.9802,
     "style": "Byzantine", "year": 537, "note": "World's largest cathedral for nearly 1,000 years. Church, mosque, museum, mosque again."},
    {"name": "Canterbury Cathedral", "city": "Canterbury, UK", "lat": 51.2798, "lon": 1.0830,
     "style": "Gothic", "year": 1077, "note": "Seat of the Archbishop of Canterbury. Pilgrimage site since Thomas Becket's murder (1170)."},
    {"name": "Westminster Abbey", "city": "London, UK", "lat": 51.4993, "lon": -0.1273,
     "style": "Gothic", "year": 1269, "note": "Coronation church of English monarchs since 1066. Royal burial site."},
    {"name": "Chartres Cathedral", "city": "Chartres, France", "lat": 48.4476, "lon": 1.4877,
     "style": "Gothic", "year": 1220, "note": "Finest example of High Gothic architecture. Original stained glass windows."},
    {"name": "St. Paul's Cathedral", "city": "London, UK", "lat": 51.5138, "lon": -0.0984,
     "style": "English Baroque", "year": 1710, "note": "Christopher Wren's masterpiece. Survived the Blitz. Iconic dome."},
    {"name": "Florence Cathedral (Duomo)", "city": "Florence, Italy", "lat": 43.7731, "lon": 11.2560,
     "style": "Gothic / Renaissance", "year": 1436, "note": "Brunelleschi's dome was the largest in the world. Symbol of the Renaissance."},
    {"name": "Basilica of Our Lady of Guadalupe", "city": "Mexico City, Mexico", "lat": 19.4862, "lon": -99.1172,
     "style": "Modern / Colonial", "year": 1976, "note": "Most visited Catholic pilgrimage site. ~10 million visitors on Dec 12."},
    {"name": "Church of the Holy Sepulchre", "city": "Jerusalem, Israel", "lat": 31.7785, "lon": 35.2296,
     "style": "Romanesque / Byzantine", "year": 335, "note": "Site of Jesus' crucifixion and burial. Holiest site in Christianity."},
    {"name": "St. Sophia Cathedral", "city": "Kyiv, Ukraine", "lat": 50.4527, "lon": 30.5142,
     "style": "Byzantine / Baroque", "year": 1037, "note": "UNESCO World Heritage. 11th-century mosaics and frescoes."},
    {"name": "Basilica of the Sacred Heart", "city": "Paris, France", "lat": 48.8867, "lon": 2.3431,
     "style": "Romano-Byzantine", "year": 1914, "note": "Sacre-Coeur on Montmartre hill. White travertine stone that self-cleans with rain."},
    {"name": "Seville Cathedral", "city": "Seville, Spain", "lat": 37.3861, "lon": -5.9926,
     "style": "Gothic / Renaissance", "year": 1507, "note": "Largest Gothic cathedral. Tomb of Christopher Columbus. Giralda tower."},
    {"name": "St. Stephen's Cathedral", "city": "Vienna, Austria", "lat": 48.2082, "lon": 16.3738,
     "style": "Gothic / Romanesque", "year": 1160, "note": "Symbol of Vienna. 137m south tower. Multi-colored roof tiles."},
    {"name": "Cathedral of Brasilia", "city": "Brasilia, Brazil", "lat": -15.7983, "lon": -47.8753,
     "style": "Modernist", "year": 1970, "note": "Oscar Niemeyer's hyperboloid structure with 16 concrete columns. UNESCO."},
    {"name": "Hallgrimskirkja", "city": "Reykjavik, Iceland", "lat": 64.1417, "lon": -21.9267,
     "style": "Expressionist", "year": 1986, "note": "Iceland's tallest church. Design inspired by basalt lava columns."},
    {"name": "Las Lajas Sanctuary", "city": "Narino, Colombia", "lat": 0.8030, "lon": -77.5850,
     "style": "Gothic Revival", "year": 1949, "note": "Built inside a canyon, spanning a gorge with a 30m bridge. Stunning setting."},
    {"name": "Alexander Nevsky Cathedral", "city": "Sofia, Bulgaria", "lat": 42.6960, "lon": 23.3328,
     "style": "Neo-Byzantine", "year": 1912, "note": "Symbol of Sofia. One of the largest Eastern Orthodox cathedrals."},
]

# ═══════════════════════════════════════════════════════════════════
# 4.  MOSQUES OF THE WORLD
# ═══════════════════════════════════════════════════════════════════
MOSQUES = [
    {"name": "Masjid al-Haram (Grand Mosque)", "city": "Mecca, Saudi Arabia", "lat": 21.4225, "lon": 39.8262,
     "capacity": 4000000, "year": 638, "note": "Largest mosque in the world. Surrounds the Kaaba, Islam's holiest site."},
    {"name": "Al-Masjid an-Nabawi (Prophet's Mosque)", "city": "Medina, Saudi Arabia", "lat": 24.4672, "lon": 39.6112,
     "capacity": 1000000, "year": 622, "note": "Second-holiest mosque. Built by Prophet Muhammad. Houses his tomb."},
    {"name": "Al-Aqsa Mosque", "city": "Jerusalem", "lat": 31.7761, "lon": 35.2358,
     "capacity": 5000, "year": 705, "note": "Third-holiest site in Islam. On the Temple Mount/Haram al-Sharif."},
    {"name": "Sultan Ahmed Mosque (Blue Mosque)", "city": "Istanbul, Turkey", "lat": 41.0054, "lon": 28.9768,
     "capacity": 10000, "year": 1616, "note": "Famous for its blue Iznik tiles. Six minarets. Facing Hagia Sophia."},
    {"name": "Hassan II Mosque", "city": "Casablanca, Morocco", "lat": 33.6086, "lon": -7.6322,
     "capacity": 105000, "year": 1993, "note": "Tallest minaret in the world (210m). Built partly over the Atlantic Ocean."},
    {"name": "Faisal Mosque", "city": "Islamabad, Pakistan", "lat": 33.7295, "lon": 73.0372,
     "capacity": 300000, "year": 1986, "note": "Tent-shaped design by Turkish architect Vedat Dalokay. No traditional dome."},
    {"name": "Sheikh Zayed Grand Mosque", "city": "Abu Dhabi, UAE", "lat": 24.4128, "lon": 54.4750,
     "capacity": 41000, "year": 2007, "note": "82 domes, 1,000+ columns. World's largest hand-knotted carpet (5,627 sqm)."},
    {"name": "Badshahi Mosque", "city": "Lahore, Pakistan", "lat": 31.5882, "lon": 74.3098,
     "capacity": 100000, "year": 1673, "note": "Mughal emperor Aurangzeb's masterpiece. Red sandstone and marble."},
    {"name": "Sultan Qaboos Grand Mosque", "city": "Muscat, Oman", "lat": 23.5859, "lon": 58.4035,
     "capacity": 20000, "year": 2001, "note": "Main prayer hall chandelier weighs 8 tons. Blends contemporary and traditional."},
    {"name": "Istiqlal Mosque", "city": "Jakarta, Indonesia", "lat": -6.1702, "lon": 106.8319,
     "capacity": 200000, "year": 1978, "note": "Largest mosque in Southeast Asia. Faces the Jakarta Cathedral as symbol of tolerance."},
    {"name": "Great Mosque of Djenne", "city": "Djenne, Mali", "lat": 13.9053, "lon": -4.5553,
     "capacity": 3000, "year": 1907, "note": "Largest adobe (mud-brick) building in the world. UNESCO World Heritage."},
    {"name": "Great Mosque of Cordoba (Mezquita)", "city": "Cordoba, Spain", "lat": 37.8789, "lon": -4.7794,
     "capacity": 20000, "year": 784, "note": "Moorish masterpiece with 856 columns. Now a Catholic cathedral."},
    {"name": "Great Mosque of Samarra", "city": "Samarra, Iraq", "lat": 34.2076, "lon": 43.8785,
     "capacity": 10000, "year": 851, "note": "Famous Malwiya Tower (spiral minaret). Once the largest mosque in the world."},
    {"name": "Suleymaniye Mosque", "city": "Istanbul, Turkey", "lat": 41.0162, "lon": 28.9640,
     "capacity": 5000, "year": 1557, "note": "Designed by architect Mimar Sinan for Suleiman the Magnificent."},
    {"name": "Crystal Mosque", "city": "Kuala Terengganu, Malaysia", "lat": 5.3384, "lon": 103.1224,
     "capacity": 1500, "year": 2008, "note": "Made of steel, glass, and crystal. Spectacularly illuminated at night."},
    {"name": "Imam Ali Mosque", "city": "Najaf, Iraq", "lat": 31.9965, "lon": 44.3142,
     "capacity": 8000, "year": 977, "note": "Shrine of Imam Ali. Golden dome. Holiest Shia mosque after Mecca/Medina."},
    {"name": "Nasir al-Mulk Mosque (Pink Mosque)", "city": "Shiraz, Iran", "lat": 29.6022, "lon": 52.5190,
     "capacity": 1000, "year": 1888, "note": "Famous for its stained-glass windows creating kaleidoscopic light effects."},
    {"name": "Wazir Khan Mosque", "city": "Lahore, Pakistan", "lat": 31.5828, "lon": 74.3258,
     "capacity": 3000, "year": 1635, "note": "Known for elaborate Kashi-kari (tile work) and frescoes. Mughal-era jewel."},
]

# ═══════════════════════════════════════════════════════════════════
# 5.  HINDU & BUDDHIST TEMPLES
# ═══════════════════════════════════════════════════════════════════
TEMPLES = [
    {"name": "Angkor Wat", "city": "Siem Reap, Cambodia", "lat": 13.4125, "lon": 103.8670,
     "religion": "Hinduism / Buddhism", "year": 1150, "note": "Largest religious monument in the world. Originally Hindu, now Buddhist."},
    {"name": "Borobudur", "city": "Central Java, Indonesia", "lat": -7.6079, "lon": 110.2038,
     "religion": "Buddhism", "year": 825, "note": "Largest Buddhist temple. 2,672 relief panels, 504 Buddha statues. UNESCO."},
    {"name": "Golden Temple (Harmandir Sahib)", "city": "Amritsar, India", "lat": 31.6200, "lon": 74.8765,
     "religion": "Sikhism", "year": 1604, "note": "Holiest gurdwara. Gold-plated upper floors. Free community kitchen feeds 100,000+ daily."},
    {"name": "Meenakshi Amman Temple", "city": "Madurai, India", "lat": 9.9195, "lon": 78.1193,
     "religion": "Hinduism", "year": 1623, "note": "14 gopurams (towers) with 33,000 sculptures. Dedicated to Parvati and Shiva."},
    {"name": "Kashi Vishwanath Temple", "city": "Varanasi, India", "lat": 25.3109, "lon": 83.0107,
     "religion": "Hinduism", "year": 1780, "note": "One of the 12 Jyotirlinga temples of Shiva. Gold dome. Most sacred Hindu temple."},
    {"name": "Prambanan", "city": "Central Java, Indonesia", "lat": -7.7520, "lon": 110.4915,
     "religion": "Hinduism", "year": 850, "note": "Largest Hindu temple complex in Indonesia. 240 temples. UNESCO."},
    {"name": "Shwedagon Pagoda", "city": "Yangon, Myanmar", "lat": 16.8714, "lon": 96.1499,
     "religion": "Buddhism", "year": -500, "note": "2,500 years old. Gilded stupa 99m tall, covered in gold plates and diamonds."},
    {"name": "Temple of the Tooth (Sri Dalada Maligawa)", "city": "Kandy, Sri Lanka", "lat": 7.2936, "lon": 80.6413,
     "religion": "Buddhism", "year": 1595, "note": "Houses the Sacred Tooth Relic of the Buddha. UNESCO. Annual Esala Perahera festival."},
    {"name": "Tirumala Venkateswara Temple", "city": "Tirupati, India", "lat": 13.6833, "lon": 79.3470,
     "religion": "Hinduism", "year": 300, "note": "Richest temple in the world. Annual revenue ~$1 billion. 50,000+ visitors daily."},
    {"name": "Pashupatinath Temple", "city": "Kathmandu, Nepal", "lat": 27.7107, "lon": 85.3488,
     "religion": "Hinduism", "year": 400, "note": "Holiest Shiva temple in Nepal. On the Bagmati River. UNESCO. Cremation ghats."},
    {"name": "Bagan Temples", "city": "Bagan, Myanmar", "lat": 21.1717, "lon": 94.8585,
     "religion": "Buddhism", "year": 1057, "note": "Over 2,200 surviving temples and pagodas on 40 sq km. UNESCO."},
    {"name": "Todai-ji (Great Eastern Temple)", "city": "Nara, Japan", "lat": 34.6890, "lon": 135.8398,
     "religion": "Buddhism", "year": 752, "note": "Houses the world's largest bronze Buddha (15m). Largest wooden building."},
    {"name": "Konark Sun Temple", "city": "Konark, India", "lat": 19.8876, "lon": 86.0945,
     "religion": "Hinduism", "year": 1250, "note": "Designed as a giant chariot with 24 carved wheels. UNESCO. Dedicated to Surya."},
    {"name": "Ranganathaswamy Temple", "city": "Srirangam, India", "lat": 10.8626, "lon": 78.6872,
     "religion": "Hinduism", "year": 900, "note": "Largest functioning Hindu temple complex (631,000 sqm). 7 concentric walls."},
    {"name": "Wat Phra Kaew (Temple of the Emerald Buddha)", "city": "Bangkok, Thailand", "lat": 13.7516, "lon": 100.4924,
     "religion": "Buddhism", "year": 1784, "note": "Most sacred Buddhist temple in Thailand. Houses the Emerald Buddha."},
    {"name": "Ellora Caves", "city": "Aurangabad, India", "lat": 20.0268, "lon": 75.1791,
     "religion": "Hinduism / Buddhism / Jainism", "year": 600, "note": "34 caves: Hindu, Buddhist, Jain. Kailasa temple carved from one rock. UNESCO."},
    {"name": "Ajanta Caves", "city": "Aurangabad, India", "lat": 20.5519, "lon": 75.7033,
     "religion": "Buddhism", "year": -200, "note": "30 rock-cut Buddhist caves with masterpiece paintings from 2nd century BCE. UNESCO."},
    {"name": "Kinkaku-ji (Golden Pavilion)", "city": "Kyoto, Japan", "lat": 35.0394, "lon": 135.7292,
     "religion": "Buddhism (Zen)", "year": 1397, "note": "Three-story golden temple reflected in a mirror pond. Zen Buddhist temple."},
    {"name": "Akshardham", "city": "New Delhi, India", "lat": 28.6127, "lon": 77.2773,
     "religion": "Hinduism", "year": 2005, "note": "Largest Hindu temple complex. 20,000 carved figures. 10,000 volunteers built it."},
    {"name": "Somnath Temple", "city": "Gujarat, India", "lat": 20.8880, "lon": 70.4012,
     "religion": "Hinduism", "year": 1951, "note": "First of 12 Jyotirlinga temples. Destroyed and rebuilt 17 times throughout history."},
]

# ═══════════════════════════════════════════════════════════════════
# 6.  MONASTERIES
# ═══════════════════════════════════════════════════════════════════
MONASTERIES = [
    {"name": "Mount Athos", "city": "Chalkidiki, Greece", "lat": 40.1564, "lon": 24.3284,
     "religion": "Eastern Orthodox", "founded": 963, "note": "Autonomous monastic state. 20 monasteries. No women allowed since 1046."},
    {"name": "Meteora Monasteries", "city": "Thessaly, Greece", "lat": 39.7217, "lon": 21.6306,
     "religion": "Eastern Orthodox", "founded": 1344, "note": "Six monasteries perched on massive natural sandstone pillars. UNESCO."},
    {"name": "Shaolin Temple", "city": "Henan, China", "lat": 34.5076, "lon": 112.9370,
     "religion": "Buddhism (Chan/Zen)", "founded": 495, "note": "Birthplace of Shaolin Kung Fu. Founded by Indian monk Batuo. UNESCO."},
    {"name": "Potala Palace", "city": "Lhasa, Tibet", "lat": 29.6554, "lon": 91.1171,
     "religion": "Buddhism (Tibetan)", "founded": 1645, "note": "Winter palace of the Dalai Lama. 1,000 rooms, 117m tall. UNESCO."},
    {"name": "Rila Monastery", "city": "Rila Mountains, Bulgaria", "lat": 42.1338, "lon": 23.3404,
     "religion": "Eastern Orthodox", "founded": 927, "note": "Largest and most famous Bulgarian monastery. UNESCO. National symbol."},
    {"name": "Mont Saint-Michel", "city": "Normandy, France", "lat": 48.6361, "lon": -1.5115,
     "religion": "Christianity (Benedictine)", "founded": 966, "note": "Island monastery. Tidal island accessible only at low tide. UNESCO."},
    {"name": "Tiger's Nest (Paro Taktsang)", "city": "Paro, Bhutan", "lat": 27.4914, "lon": 89.3629,
     "religion": "Buddhism (Tibetan)", "founded": 1692, "note": "Clinging to a cliff face 3,120m above sea level. Iconic Bhutanese site."},
    {"name": "Montserrat", "city": "Catalonia, Spain", "lat": 41.5933, "lon": 1.8376,
     "religion": "Christianity (Benedictine)", "founded": 1025, "note": "Mountain monastery. Home of the Black Madonna. Boys' choir (oldest in Europe)."},
    {"name": "Sumela Monastery", "city": "Trabzon, Turkey", "lat": 40.6904, "lon": 39.6582,
     "religion": "Eastern Orthodox", "founded": 386, "note": "Built into a sheer cliff face at 1,200m altitude. Frescoes from 600s."},
    {"name": "Jokhang Temple", "city": "Lhasa, Tibet", "lat": 29.6537, "lon": 91.1328,
     "religion": "Buddhism (Tibetan)", "founded": 647, "note": "Most sacred temple in Tibetan Buddhism. Destination of pilgrimage prostrations."},
    {"name": "Hemis Monastery", "city": "Ladakh, India", "lat": 33.9160, "lon": 77.7110,
     "religion": "Buddhism (Tibetan)", "founded": 1672, "note": "Largest monastery in Ladakh. Famous annual masked dance festival."},
    {"name": "Key Monastery", "city": "Spiti Valley, India", "lat": 32.5292, "lon": 78.0131,
     "religion": "Buddhism (Tibetan)", "founded": 1000, "note": "At 4,166m altitude. Oldest and largest monastery in Spiti. Dramatic hilltop location."},
    {"name": "Drepung Monastery", "city": "Lhasa, Tibet", "lat": 29.6744, "lon": 91.0685,
     "religion": "Buddhism (Tibetan)", "founded": 1416, "note": "Once the largest monastery in the world (10,000 monks). Gelug school."},
    {"name": "Kykkos Monastery", "city": "Troodos, Cyprus", "lat": 34.9833, "lon": 32.7417,
     "religion": "Eastern Orthodox", "founded": 1100, "note": "Wealthiest and most lavish monastery in Cyprus. Icon attributed to St. Luke."},
    {"name": "Subiaco Monastery", "city": "Subiaco, Italy", "lat": 41.9253, "lon": 13.0929,
     "religion": "Christianity (Benedictine)", "founded": 529, "note": "Where St. Benedict founded Western monasticism. Cave hermitage."},
    {"name": "Abbey of Monte Cassino", "city": "Cassino, Italy", "lat": 41.4901, "lon": 13.8136,
     "religion": "Christianity (Benedictine)", "founded": 529, "note": "Mother abbey of the Benedictine Order. Destroyed and rebuilt four times."},
    {"name": "Taktshang (Tiger's Nest)", "city": "Paro, Bhutan", "lat": 27.4914, "lon": 89.3629,
     "religion": "Buddhism", "founded": 1692, "note": "Guru Rinpoche meditated here for 3 years. Clings to cliff at 3,120m."},
    {"name": "Erdene Zuu Monastery", "city": "Kharkhorin, Mongolia", "lat": 47.1964, "lon": 102.8439,
     "religion": "Buddhism (Tibetan)", "founded": 1585, "note": "Oldest Buddhist monastery in Mongolia. Built from ruins of Karakorum."},
    {"name": "Great Lavra", "city": "Mount Athos, Greece", "lat": 40.1564, "lon": 24.3969,
     "religion": "Eastern Orthodox", "founded": 963, "note": "First and largest monastery on Mount Athos. Founded by Athanasius the Athonite."},
    {"name": "Gangtey Monastery", "city": "Phobjikha Valley, Bhutan", "lat": 27.4700, "lon": 90.1667,
     "religion": "Buddhism (Tibetan)", "founded": 1613, "note": "Important Nyingma monastery in the glacial Phobjikha Valley."},
]

# ═══════════════════════════════════════════════════════════════════
# 7.  ANCIENT RELIGIONS
# ═══════════════════════════════════════════════════════════════════
ANCIENT_SITES = [
    {"name": "Karnak Temple Complex", "city": "Luxor, Egypt", "lat": 25.7188, "lon": 32.6573,
     "religion": "Ancient Egyptian", "era": "2055-100 BCE", "note": "Largest ancient religious complex. Dedicated to Amun-Ra. Hypostyle Hall."},
    {"name": "Temple of Luxor", "city": "Luxor, Egypt", "lat": 25.6995, "lon": 32.6390,
     "religion": "Ancient Egyptian", "era": "1400 BCE", "note": "Built by Amenhotep III and Ramesses II. Connected to Karnak by sphinx avenue."},
    {"name": "Delphi (Temple of Apollo)", "city": "Delphi, Greece", "lat": 38.4824, "lon": 22.5010,
     "religion": "Ancient Greek", "era": "8th c. BCE", "note": "Most important oracle in the ancient world. Navel of the world (omphalos)."},
    {"name": "Parthenon", "city": "Athens, Greece", "lat": 37.9715, "lon": 23.7267,
     "religion": "Ancient Greek", "era": "447-432 BCE", "note": "Temple of Athena Parthenos. Pinnacle of Doric architecture. UNESCO."},
    {"name": "Temple of Olympian Zeus", "city": "Athens, Greece", "lat": 37.9693, "lon": 23.7331,
     "religion": "Ancient Greek", "era": "6th c. BCE-131 CE", "note": "Largest temple in Greece. Took 700 years to complete."},
    {"name": "Gobekli Tepe", "city": "Sanliurfa, Turkey", "lat": 37.2232, "lon": 38.9224,
     "religion": "Pre-Pottery Neolithic", "era": "9500 BCE", "note": "Oldest known temple complex. Predates agriculture. Rewrote human history."},
    {"name": "Stonehenge", "city": "Wiltshire, UK", "lat": 51.1789, "lon": -1.8262,
     "religion": "Neolithic / Bronze Age", "era": "3000-2000 BCE", "note": "Iconic stone circle. Solstice alignment. Purpose still debated."},
    {"name": "Newgrange", "city": "County Meath, Ireland", "lat": 53.6947, "lon": -6.4756,
     "religion": "Neolithic", "era": "3200 BCE", "note": "Passage tomb older than Stonehenge and the Pyramids. Winter solstice light box."},
    {"name": "Temple of Hatshepsut", "city": "Deir el-Bahari, Egypt", "lat": 25.7381, "lon": 32.6073,
     "religion": "Ancient Egyptian", "era": "1479 BCE", "note": "Mortuary temple of the female pharaoh. Terraced colonnades against cliffs."},
    {"name": "Yazd Atash Behram", "city": "Yazd, Iran", "lat": 31.8974, "lon": 54.3569,
     "religion": "Zoroastrianism", "era": "470 CE", "note": "Fire temple housing a flame burning continuously since 470 CE. Highest grade fire."},
    {"name": "Tower of Silence", "city": "Yazd, Iran", "lat": 31.8827, "lon": 54.3230,
     "religion": "Zoroastrianism", "era": "Various", "note": "Dakhma where Zoroastrians exposed the dead to birds. Practice now rare."},
    {"name": "Persepolis", "city": "Shiraz, Iran", "lat": 29.9346, "lon": 52.8914,
     "religion": "Zoroastrianism", "era": "515 BCE", "note": "Ceremonial capital of the Achaemenid Empire. Apadana reliefs. UNESCO."},
    {"name": "Temple of Isis (Philae)", "city": "Aswan, Egypt", "lat": 24.0247, "lon": 32.8841,
     "religion": "Ancient Egyptian", "era": "380 BCE", "note": "Last temple where Egyptian hieroglyphs were written. Rescued from flooding."},
    {"name": "Baalbek (Temple of Jupiter)", "city": "Baalbek, Lebanon", "lat": 34.0068, "lon": 36.2040,
     "religion": "Roman / Phoenician", "era": "1st c. BCE", "note": "Largest Roman temple ever built. 6 surviving columns are the tallest in the world."},
    {"name": "Teotihuacan", "city": "Mexico", "lat": 19.6925, "lon": -98.8438,
     "religion": "Mesoamerican", "era": "100 BCE-550 CE", "note": "Pyramid of the Sun, Pyramid of the Moon. Avenue of the Dead. Peak population ~125,000."},
    {"name": "Chichen Itza (El Castillo)", "city": "Yucatan, Mexico", "lat": 20.6843, "lon": -88.5678,
     "religion": "Maya", "era": "600-1200 CE", "note": "Temple of Kukulcan. Equinox serpent shadow effect. UNESCO. New Seven Wonders."},
    {"name": "Machu Picchu (Intihuatana)", "city": "Cusco, Peru", "lat": -13.1631, "lon": -72.5450,
     "religion": "Inca", "era": "1450 CE", "note": "Ritual stone (Intihuatana) for astronomical observation. Sun-tying stone."},
    {"name": "Abu Simbel", "city": "Aswan, Egypt", "lat": 22.3460, "lon": 31.6156,
     "religion": "Ancient Egyptian", "era": "1264 BCE", "note": "Four colossal statues of Ramesses II. Sun aligns with inner chamber twice yearly."},
    {"name": "Temple of Poseidon", "city": "Cape Sounion, Greece", "lat": 37.6503, "lon": 24.0244,
     "religion": "Ancient Greek", "era": "444 BCE", "note": "Marble temple perched on a cliff 60m above the sea. Lord Byron carved his name."},
    {"name": "Ggantija Temples", "city": "Gozo, Malta", "lat": 36.0477, "lon": 14.2690,
     "religion": "Neolithic", "era": "3600 BCE", "note": "Among the oldest freestanding structures on Earth. UNESCO. Predates pyramids."},
]

# ═══════════════════════════════════════════════════════════════════
# 8.  PILGRIMAGE ROUTES
# ═══════════════════════════════════════════════════════════════════
PILGRIMAGE_ROUTES = [
    {"name": "Camino de Santiago (French Way)", "religion": "Christianity",
     "start": "Saint-Jean-Pied-de-Port, France", "end": "Santiago de Compostela, Spain",
     "distance": "780 km", "note": "Most popular Christian pilgrimage. ~300,000 pilgrims/year. UNESCO.",
     "waypoints": [(43.1631, -1.2358), (42.8126, -1.6458), (42.6722, -2.8725),
                   (42.4669, -3.7139), (42.5988, -5.5670), (42.8782, -8.5448)]},
    {"name": "Hajj Pilgrimage", "religion": "Islam",
     "start": "Worldwide to Jeddah", "end": "Mecca, Saudi Arabia",
     "distance": "Various (ritual circuit ~15 km)", "note": "Fifth pillar of Islam. ~2.5 million pilgrims annually. Rituals over 5-6 days.",
     "waypoints": [(21.5169, 39.1884), (21.4225, 39.8262), (21.3549, 39.9841),
                   (21.4225, 39.8262)]},
    {"name": "Kumbh Mela Circuit", "religion": "Hinduism",
     "start": "Allahabad (Prayagraj)", "end": "Rotates among 4 cities",
     "distance": "N/A (ritual bathing)", "note": "Largest religious gathering on Earth. 120 million+ at 2013 Maha Kumbh. Every 12 years.",
     "waypoints": [(25.4358, 81.8463), (29.9457, 78.1642), (23.1828, 75.7772),
                   (19.8762, 73.8806)]},
    {"name": "Shikoku 88 Temple Pilgrimage", "religion": "Buddhism",
     "start": "Temple 1, Ryozen-ji", "end": "Temple 88, Okubo-ji",
     "distance": "1,200 km", "note": "Henro pilgrimage around Shikoku island. 88 temples associated with Kukai (Kobo Daishi).",
     "waypoints": [(34.0754, 134.5162), (33.5601, 133.5311), (33.0100, 132.7657),
                   (33.8416, 132.7654), (34.2272, 134.0222)]},
    {"name": "Via Francigena", "religion": "Christianity",
     "start": "Canterbury, UK", "end": "Rome, Italy",
     "distance": "1,900 km", "note": "Medieval pilgrim route to Rome. Through England, France, Switzerland, Italy.",
     "waypoints": [(51.2798, 1.0830), (50.9483, 1.8580), (49.8941, 2.2958),
                   (49.0134, 3.3964), (46.5197, 6.6323), (45.8150, 8.8530),
                   (43.7696, 11.2558), (41.9028, 12.4964)]},
    {"name": "Char Dham Yatra", "religion": "Hinduism",
     "start": "Yamunotri", "end": "Kedarnath (circuit)",
     "distance": "~1,600 km (by road)", "note": "Four sacred Hindu sites in the Himalayas. ~3 million pilgrims annually. May-Nov only.",
     "waypoints": [(31.0149, 78.4641), (30.9946, 78.9396), (30.7346, 79.0669),
                   (30.4500, 79.2500)]},
    {"name": "Kumano Kodo", "religion": "Shinto / Buddhism",
     "start": "Tanabe", "end": "Kumano Sanzan shrines",
     "distance": "70-200 km", "note": "Ancient pilgrimage routes to Kumano's three grand shrines. UNESCO. 1,000+ year history.",
     "waypoints": [(33.7319, 135.3786), (33.8447, 135.7721), (33.7260, 135.9981),
                   (33.6699, 136.0046)]},
    {"name": "Mount Kailash Kora", "religion": "Hinduism / Buddhism / Jainism / Bon",
     "start": "Darchen, Tibet", "end": "Darchen (circumambulation)",
     "distance": "52 km", "note": "Sacred to 4 religions. Unclimbed. Pilgrims circumambulate at 4,600-5,600m altitude.",
     "waypoints": [(30.9750, 81.3119), (31.0667, 81.3125), (31.0667, 81.3700),
                   (30.9750, 81.3119)]},
    {"name": "St. Olav's Way", "religion": "Christianity",
     "start": "Oslo / Selanger", "end": "Nidaros Cathedral, Trondheim",
     "distance": "640 km", "note": "Norwegian pilgrimage to the shrine of St. Olav. Revived in 1997. Growing popularity.",
     "waypoints": [(59.9139, 10.7522), (60.7945, 11.0679), (62.5745, 11.3945),
                   (63.4305, 10.3951)]},
    {"name": "Abraham Path", "religion": "Judaism / Christianity / Islam",
     "start": "Harran, Turkey", "end": "Hebron, Palestine",
     "distance": "1,500 km", "note": "Traces Abraham's journey. Through Turkey, Syria, Jordan, Palestine. Interfaith initiative.",
     "waypoints": [(36.8600, 39.0282), (36.2022, 36.1604), (34.8021, 36.2765),
                   (32.2226, 35.2621), (31.5326, 35.0998)]},
]

# ═══════════════════════════════════════════════════════════════════
# 9.  RELIGIOUS CONFLICTS & HISTORICAL EVENTS
# ═══════════════════════════════════════════════════════════════════
CONFLICT_SITES = [
    {"name": "Jerusalem", "lat": 31.7683, "lon": 35.2137, "era": "All eras",
     "type": "Interfaith Zone", "note": "Contested by Jews, Christians, Muslims for 3,000+ years. Temple Mount / Haram al-Sharif."},
    {"name": "Constantinople (Siege, 1453)", "lat": 41.0082, "lon": 28.9784, "era": "1453",
     "type": "Crusade / Conquest", "note": "Fall of Byzantine Empire to Ottomans. Hagia Sophia converted to mosque. End of Eastern Christendom."},
    {"name": "Wittenberg (95 Theses)", "lat": 51.8660, "lon": 12.6439, "era": "1517",
     "type": "Reformation", "note": "Martin Luther nailed his 95 Theses here. Sparked the Protestant Reformation."},
    {"name": "Antioch (First Crusade)", "lat": 36.2022, "lon": 36.1604, "era": "1098",
     "type": "Crusade", "note": "Siege of Antioch during the First Crusade. Crusaders took the city after 8 months."},
    {"name": "Acre (Fall of, 1291)", "lat": 32.9226, "lon": 35.0694, "era": "1291",
     "type": "Crusade", "note": "Fall of the last major Crusader stronghold. End of the Crusader states in the Holy Land."},
    {"name": "Ayodhya (Babri Masjid)", "lat": 26.7960, "lon": 82.1998, "era": "1992",
     "type": "Hindu-Muslim Conflict", "note": "Babri Masjid demolished 1992. Believed birthplace of Lord Rama. Ram Mandir built 2024."},
    {"name": "Cordoba (Reconquista)", "lat": 37.8882, "lon": -4.7794, "era": "1236",
     "type": "Reconquista", "note": "Ferdinand III reconquered Cordoba. Mezquita converted from mosque to cathedral."},
    {"name": "Munster (Anabaptist Rebellion)", "lat": 51.9607, "lon": 7.6261, "era": "1534-35",
     "type": "Reformation", "note": "Radical Anabaptists seized the city. Established theocratic commune. Besieged and destroyed."},
    {"name": "Geneva (Calvin's Reformation)", "lat": 46.2044, "lon": 6.1432, "era": "1541",
     "type": "Reformation", "note": "John Calvin established a Protestant theocracy. Geneva became the 'Protestant Rome'."},
    {"name": "Augsburg (Peace of Augsburg)", "lat": 48.3705, "lon": 10.8978, "era": "1555",
     "type": "Reformation", "note": "Treaty allowing rulers to choose Lutheranism or Catholicism. Cuius regio, eius religio."},
    {"name": "Westphalia (Peace of, 1648)", "lat": 52.0215, "lon": 8.5320, "era": "1648",
     "type": "Religious Wars", "note": "Ended the Thirty Years' War. Established religious tolerance in the Holy Roman Empire."},
    {"name": "Karbala (Battle of, 680 CE)", "lat": 32.6160, "lon": 44.0243, "era": "680 CE",
     "type": "Sunni-Shia Split", "note": "Martyrdom of Husayn ibn Ali. Defining event of Sunni-Shia split. Commemorated on Ashura."},
    {"name": "Amritsar (1984 Operation Blue Star)", "lat": 31.6200, "lon": 74.8765, "era": "1984",
     "type": "Sikh Conflict", "note": "Indian Army stormed the Golden Temple complex to flush out Sikh militants. 500+ casualties."},
    {"name": "Sarajevo (Siege, 1992-96)", "lat": 43.8563, "lon": 18.4131, "era": "1992-96",
     "type": "Ethno-Religious Conflict", "note": "Longest siege in modern history. Multi-ethnic city torn by Orthodox-Muslim-Catholic conflict."},
    {"name": "Nicea (Council of Nicea)", "lat": 40.4292, "lon": 29.7211, "era": "325 CE",
     "type": "Doctrinal", "note": "First Ecumenical Council. Established the Nicene Creed. Resolved Arian controversy."},
    {"name": "Partition of India", "lat": 28.6139, "lon": 77.2090, "era": "1947",
     "type": "Hindu-Muslim Partition", "note": "Division of British India into India and Pakistan. 1-2 million killed, 15 million displaced."},
    {"name": "Tours/Poitiers (Battle of, 732)", "lat": 46.5802, "lon": 0.3404, "era": "732",
     "type": "Muslim Expansion", "note": "Charles Martel halted Muslim expansion into Western Europe. Turning point in European history."},
    {"name": "Hattin (Battle of, 1187)", "lat": 32.8065, "lon": 35.4483, "era": "1187",
     "type": "Crusade", "note": "Saladin defeated Crusader army. Led to Muslim reconquest of Jerusalem."},
]

# ═══════════════════════════════════════════════════════════════════
# 10. NEW RELIGIONS & MOVEMENTS
# ═══════════════════════════════════════════════════════════════════
NEW_RELIGIONS = [
    {"name": "Baha'i House of Worship (Lotus Temple)", "city": "New Delhi, India", "lat": 28.5535, "lon": 77.2588,
     "movement": "Baha'i Faith", "year": 1986, "note": "Lotus-shaped. 10,000+ daily visitors. Open to all faiths. One of 10 Baha'i Houses of Worship."},
    {"name": "Baha'i World Centre", "city": "Haifa, Israel", "lat": 32.8131, "lon": 34.9876,
     "movement": "Baha'i Faith", "year": 1953, "note": "Shrine of the Bab. Terraced gardens. Administrative center of the Baha'i Faith. UNESCO."},
    {"name": "Baha'i House of Worship", "city": "Wilmette, Illinois, USA", "lat": 42.0742, "lon": -87.6838,
     "movement": "Baha'i Faith", "year": 1953, "note": "First Baha'i temple in the West. Ornate dome. Nine-sided structure. National Historic Place."},
    {"name": "Church of Scientology (Flag Land Base)", "city": "Clearwater, Florida, USA", "lat": 27.9659, "lon": -82.8001,
     "movement": "Scientology", "year": 1975, "note": "Spiritual headquarters of Scientology. Fort Harrison Hotel. Advanced training center."},
    {"name": "Church of Scientology (Celebrity Centre)", "city": "Los Angeles, USA", "lat": 34.1009, "lon": -118.3200,
     "movement": "Scientology", "year": 1969, "note": "Chateau Elysee building. Caters to artists and celebrities. Founded by L. Ron Hubbard."},
    {"name": "Scientology HQ (Gold Base)", "city": "San Jacinto, California, USA", "lat": 33.8177, "lon": -116.9830,
     "movement": "Scientology", "year": 1978, "note": "International headquarters and film studios. Heavily guarded compound."},
    {"name": "Soka Gakkai International HQ", "city": "Tokyo, Japan", "lat": 35.6999, "lon": 139.7211,
     "movement": "Soka Gakkai (Nichiren Buddhism)", "year": 1930, "note": "12 million members worldwide. Based on Nichiren Buddhist teachings. Peace activism."},
    {"name": "ISKCON Temple (Hare Krishna)", "city": "Vrindavan, India", "lat": 27.5836, "lon": 77.6920,
     "movement": "ISKCON (Hare Krishna)", "year": 1975, "note": "Krishna-Balaram Mandir. International Society for Krishna Consciousness. Founded by Prabhupada."},
    {"name": "Salt Lake Temple", "city": "Salt Lake City, USA", "lat": 40.7706, "lon": -111.8913,
     "movement": "Church of Jesus Christ of Latter-day Saints", "year": 1893, "note": "Iconic 6-spired temple. 40 years to build. Center of the LDS faith."},
    {"name": "Nauvoo Temple", "city": "Nauvoo, Illinois, USA", "lat": 40.5470, "lon": -91.3841,
     "movement": "LDS (Mormon)", "year": 2002, "note": "Rebuilt on site of original 1846 temple. Joseph Smith's city. LDS history landmark."},
    {"name": "Rastafarian Origins (Pinnacle)", "city": "St. Catherine, Jamaica", "lat": 18.2095, "lon": -76.9571,
     "movement": "Rastafari", "year": 1940, "note": "Leonard Howell's commune. First Rastafarian settlement. Destroyed by colonial police."},
    {"name": "Shashemene (Rastafari Land Grant)", "city": "Shashemene, Ethiopia", "lat": 7.1999, "lon": 38.5985,
     "movement": "Rastafari", "year": 1948, "note": "Land granted by Haile Selassie to Rastafarians. African repatriation settlement."},
    {"name": "Tenrikyo Church HQ (Oyasato)", "city": "Tenri, Japan", "lat": 34.5966, "lon": 135.8376,
     "movement": "Tenrikyo", "year": 1838, "note": "Founded by Nakayama Miki. ~2 million followers. Jiba (original place of human creation)."},
    {"name": "Cao Dai Holy See", "city": "Tay Ninh, Vietnam", "lat": 11.2965, "lon": 106.1690,
     "movement": "Cao Dai", "year": 1955, "note": "Syncretic religion founded in 1926. Colorful temple. ~3 million followers. Saints include Victor Hugo."},
    {"name": "Auroville (Universal Township)", "city": "Puducherry, India", "lat": 12.0057, "lon": 79.8105,
     "movement": "Integral Yoga (Sri Aurobindo)", "year": 1968, "note": "Experimental universal township. Matrimandir golden sphere. 3,000 residents from 60 nations."},
    {"name": "Damanhur (Temples of Humankind)", "city": "Piedmont, Italy", "lat": 45.4164, "lon": 7.7648,
     "movement": "Damanhur (New Age)", "year": 1978, "note": "Underground temples carved in secret for 16 years. Called the 'Eighth Wonder of the World'."},
    {"name": "Findhorn Foundation", "city": "Findhorn, Scotland", "lat": 57.6614, "lon": -3.6069,
     "movement": "New Age / Spiritual", "year": 1962, "note": "Intentional spiritual community. Famous for 'miraculous' gardens. Eco-village. 400+ members."},
    {"name": "Unification Church HQ", "city": "Seoul, South Korea", "lat": 37.5552, "lon": 126.9723,
     "movement": "Unification Church", "year": 1954, "note": "Founded by Sun Myung Moon. Known for mass weddings. ~3 million claimed followers."},
]


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _make_map(center_lat=25.0, center_lon=20.0, zoom=2):
    """Create a dark-themed Folium map."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _show_map(m, height=500):
    """Render a Folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _religion_color(religion_str):
    """Get color for a religion string (partial match)."""
    r = religion_str.lower()
    if "christian" in r or "catholic" in r or "orthodox" in r or "protestant" in r:
        return RELIGION_COLORS["Christianity"]
    if "islam" in r or "muslim" in r or "sunni" in r or "shia" in r:
        return RELIGION_COLORS["Islam"]
    if "hindu" in r:
        return RELIGION_COLORS["Hinduism"]
    if "buddh" in r or "zen" in r:
        return RELIGION_COLORS["Buddhism"]
    if "judai" in r or "jewish" in r:
        return RELIGION_COLORS["Judaism"]
    if "sikh" in r:
        return RELIGION_COLORS["Sikhism"]
    if "shinto" in r:
        return RELIGION_COLORS["Shinto"]
    if "baha" in r:
        return RELIGION_COLORS["Baha'i"]
    if "jain" in r:
        return RELIGION_COLORS["Jainism"]
    if "zoroastr" in r:
        return RELIGION_COLORS["Zoroastrianism"]
    if "folk" in r or "traditional" in r:
        return RELIGION_COLORS["Folk / Traditional"]
    return RELIGION_COLORS["Other"]


def _bar_chart(labels, values, title, color_list=None, ylabel="Percentage (%)"):
    """Create a horizontal bar chart with dark theme."""
    fig, ax = plt.subplots(figsize=(8, max(4, len(labels) * 0.35)))
    fig.patch.set_facecolor(BG_OUTER)
    ax.set_facecolor(BG_INNER)

    if color_list is None:
        color_list = [ACCENT] * len(labels)

    bars = ax.barh(range(len(labels)), values, color=color_list, edgecolor="none", height=0.6)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color=TEXT_PRIMARY, fontsize=9)
    ax.set_xlabel(ylabel, color=TEXT_SECONDARY, fontsize=10)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=12, fontweight="bold", pad=12)
    ax.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(TEXT_SECONDARY)
    ax.spines["left"].set_color(TEXT_SECONDARY)
    ax.invert_yaxis()

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:,.1f}" if isinstance(val, float) else f"{val:,}",
                va="center", color=TEXT_PRIMARY, fontsize=8)

    plt.tight_layout()
    return fig


def _pie_chart(labels, values, title, color_list=None):
    """Create a pie chart with dark theme."""
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor(BG_OUTER)
    ax.set_facecolor(BG_INNER)

    if color_list is None:
        color_list = [RELIGION_COLORS.get(l, ACCENT) for l in labels]

    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%", startangle=140,
        colors=color_list, pctdistance=0.80,
        wedgeprops={"edgecolor": BG_OUTER, "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_color(TEXT_PRIMARY)
        t.set_fontsize(8)

    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5),
              fontsize=9, facecolor=BG_INNER, edgecolor=TEXT_SECONDARY,
              labelcolor=TEXT_PRIMARY)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=13, fontweight="bold", pad=16)
    plt.tight_layout()
    return fig


def _csv_download(df, filename, label="Download CSV"):
    """Create a CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(label, csv_buf.getvalue(), file_name=filename, mime="text/csv")


# ═══════════════════════════════════════════════════════════════════
# INDIVIDUAL MAP MODE RENDERERS
# ═══════════════════════════════════════════════════════════════════

def _render_world_distribution():
    """Mode 1: World Religion Distribution by country."""
    st.markdown("### World Religion Distribution by Country")
    st.markdown(
        "Religion adherence percentages for **{} countries** based on census and "
        "survey data. Majority religion shown with proportional circle size.".format(
            len(RELIGION_BY_COUNTRY)
        )
    )

    # ── Summary statistics ──
    religion_counts = {}
    for row in RELIGION_BY_COUNTRY:
        maj = row[3]
        religion_counts[maj] = religion_counts.get(maj, 0) + 1

    cols = st.columns(len(religion_counts))
    for i, (rel, cnt) in enumerate(sorted(religion_counts.items(), key=lambda x: -x[1])):
        with cols[i % len(cols)]:
            st.metric(rel, f"{cnt} countries")

    # ── Map ──
    m = _make_map(center_lat=20, center_lon=0, zoom=2)
    for row in RELIGION_BY_COUNTRY:
        country, lat, lon, majority, christ, islam, hindu, buddh, juda, other = row
        color = _religion_color(majority)
        popup_html = (
            f"<b>{escape(country)}</b><br>"
            f"Majority: {escape(majority)}<br>"
            f"Christianity: {christ}%<br>"
            f"Islam: {islam}%<br>"
            f"Hinduism: {hindu}%<br>"
            f"Buddhism: {buddh}%<br>"
            f"Judaism: {juda}%<br>"
            f"Other/Unaffiliated: {other}%"
        )
        majority_pct = max(christ, islam, hindu, buddh, juda, other)
        radius = max(5, majority_pct / 5)
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(f"{country} — {majority}"),
        ).add_to(m)

    _show_map(m, height=520)

    # ── Chart ──
    labels = list(religion_counts.keys())
    values = [religion_counts[l] for l in labels]
    colors = [RELIGION_COLORS.get(l, ACCENT) for l in labels]
    fig = _pie_chart(labels, values, "Majority Religion by Country Count", colors)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Global adherent pie chart ──
    global_rel = {"Christianity": 2.4, "Islam": 1.9, "Hinduism": 1.2,
                  "Buddhism": 0.5, "Folk / Traditional": 0.4, "Judaism": 0.015,
                  "Other": 0.06, "Unaffiliated": 1.2}
    gl_labels = list(global_rel.keys())
    gl_values = list(global_rel.values())
    gl_colors = [RELIGION_COLORS.get(l, ACCENT) for l in gl_labels]
    fig2 = _pie_chart(
        [f"{l} ({v:.1f}B)" for l, v in zip(gl_labels, gl_values)],
        gl_values,
        "World Population by Religion (~7.7 Billion)",
        gl_colors,
    )
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    # ── Data table ──
    df = pd.DataFrame(RELIGION_BY_COUNTRY, columns=[
        "Country", "Latitude", "Longitude", "Majority Religion",
        "Christianity %", "Islam %", "Hinduism %", "Buddhism %", "Judaism %", "Other %"
    ])
    st.dataframe(df, width="stretch")
    _csv_download(df, "world_religion_distribution.csv")


def _render_holy_cities():
    """Mode 2: Holy Cities of the World."""
    st.markdown("### Holy Cities of the World")
    st.markdown(
        f"**{len(HOLY_CITIES)} major holy cities** across all religions — "
        "the most sacred places on Earth for billions of believers."
    )

    # ── Stats ──
    rel_set = set()
    for c in HOLY_CITIES:
        for r in c["religion"].split(" / "):
            rel_set.add(r.strip())
    c1, c2, c3 = st.columns(3)
    c1.metric("Holy Cities", len(HOLY_CITIES))
    c2.metric("Religions Represented", len(rel_set))
    c3.metric("Combined Annual Visitors", "~200M+")

    # ── Map ──
    m = _make_map(center_lat=28, center_lon=50, zoom=3)
    for city in HOLY_CITIES:
        color = city.get("color", _religion_color(city["religion"]))
        popup_html = (
            f"<b>{escape(city['name'])}</b><br>"
            f"<i>{escape(city['religion'])}</i><br><br>"
            f"{escape(city['significance'])}<br><br>"
            f"Visitors: {escape(city['visitors'])}"
        )
        folium.Marker(
            location=[city["lat"], city["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{city['name']} — {city['religion']}"),
            icon=folium.Icon(color="white", icon_color=color, icon="star", prefix="fa"),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Data ──
    df = pd.DataFrame(HOLY_CITIES)
    df_display = df[["name", "religion", "significance", "visitors"]].copy()
    df_display.columns = ["City", "Religion(s)", "Significance", "Annual Visitors"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "holy_cities.csv")


def _render_cathedrals():
    """Mode 3: Cathedrals & Churches."""
    st.markdown("### Greatest Cathedrals & Churches")
    st.markdown(
        f"**{len(CATHEDRALS)} iconic cathedrals and churches** spanning 1,700 years "
        "of Christian architecture — from early Byzantine to bold Modernist."
    )

    # ── Stats ──
    styles = {}
    for c in CATHEDRALS:
        for s in c["style"].split(" / "):
            s = s.strip()
            styles[s] = styles.get(s, 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Cathedrals & Churches", len(CATHEDRALS))
    c2.metric("Architectural Styles", len(styles))
    oldest = min(CATHEDRALS, key=lambda x: x["year"])
    c3.metric("Oldest", f"{oldest['name']} ({oldest['year']})")

    # ── Map ──
    m = _make_map(center_lat=40, center_lon=10, zoom=3)
    for ch in CATHEDRALS:
        popup_html = (
            f"<b>{escape(ch['name'])}</b><br>"
            f"<i>{escape(ch['city'])}</i><br>"
            f"Style: {escape(ch['style'])}<br>"
            f"Year: {ch['year']}<br><br>"
            f"{escape(ch['note'])}"
        )
        folium.Marker(
            location=[ch["lat"], ch["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{ch['name']} ({ch['year']})"),
            icon=folium.Icon(color="blue", icon="cross", prefix="fa"),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Style chart ──
    sorted_styles = sorted(styles.items(), key=lambda x: -x[1])[:12]
    fig = _bar_chart(
        [s[0] for s in sorted_styles],
        [s[1] for s in sorted_styles],
        "Architectural Styles Represented",
        color_list=[RELIGION_COLORS["Christianity"]] * len(sorted_styles),
        ylabel="Count",
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Data ──
    df = pd.DataFrame(CATHEDRALS)
    df_display = df[["name", "city", "style", "year", "note"]].copy()
    df_display.columns = ["Name", "City", "Style", "Year", "Description"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "cathedrals_churches.csv")


def _render_mosques():
    """Mode 4: Mosques of the World."""
    st.markdown("### Great Mosques of the World")
    st.markdown(
        f"**{len(MOSQUES)} magnificent mosques** — from the Grand Mosque of Mecca "
        "to the mud-brick Djenne and the crystal mosque of Malaysia."
    )

    # ── Stats ──
    total_cap = sum(m["capacity"] for m in MOSQUES)
    largest = max(MOSQUES, key=lambda x: x["capacity"])
    oldest = min(MOSQUES, key=lambda x: x["year"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Mosques Listed", len(MOSQUES))
    c2.metric("Largest Capacity", f"{largest['name']} ({largest['capacity']:,})")
    c3.metric("Total Capacity", f"{total_cap:,}")

    # ── Map ──
    m = _make_map(center_lat=28, center_lon=45, zoom=3)
    for mq in MOSQUES:
        cap = mq["capacity"]
        radius = max(4, min(20, math.log10(max(cap, 1)) * 3))
        popup_html = (
            f"<b>{escape(mq['name'])}</b><br>"
            f"<i>{escape(mq['city'])}</i><br>"
            f"Capacity: {cap:,}<br>"
            f"Year: {mq['year']}<br><br>"
            f"{escape(mq['note'])}"
        )
        folium.CircleMarker(
            location=[mq["lat"], mq["lon"]],
            radius=radius,
            color=RELIGION_COLORS["Islam"],
            fill=True,
            fill_color=RELIGION_COLORS["Islam"],
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{mq['name']} (cap. {cap:,})"),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Capacity chart ──
    sorted_mosques = sorted(MOSQUES, key=lambda x: -x["capacity"])[:12]
    fig = _bar_chart(
        [m["name"][:30] for m in sorted_mosques],
        [m["capacity"] for m in sorted_mosques],
        "Mosque Capacity (Top 12)",
        color_list=[RELIGION_COLORS["Islam"]] * 12,
        ylabel="Capacity",
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Data ──
    df = pd.DataFrame(MOSQUES)
    df_display = df[["name", "city", "capacity", "year", "note"]].copy()
    df_display.columns = ["Name", "City", "Capacity", "Year", "Description"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "mosques_of_the_world.csv")


def _render_temples():
    """Mode 5: Hindu & Buddhist Temples."""
    st.markdown("### Hindu, Buddhist & Jain Temples")
    st.markdown(
        f"**{len(TEMPLES)} iconic temples** — from Angkor Wat to Borobudur, "
        "the Golden Temple to the cave temples of Ellora."
    )

    # ── Stats ──
    rel_counts = {}
    for t in TEMPLES:
        for r in t["religion"].split(" / "):
            r = r.strip()
            rel_counts[r] = rel_counts.get(r, 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Temples Listed", len(TEMPLES))
    c2.metric("Religions", len(rel_counts))
    oldest = min(TEMPLES, key=lambda x: x["year"])
    c3.metric("Oldest", f"{oldest['name']} ({oldest['year']})")

    # ── Map ──
    m = _make_map(center_lat=20, center_lon=85, zoom=3)
    for t in TEMPLES:
        color = _religion_color(t["religion"])
        popup_html = (
            f"<b>{escape(t['name'])}</b><br>"
            f"<i>{escape(t['city'])}</i><br>"
            f"Religion: {escape(t['religion'])}<br>"
            f"Year: {t['year']}<br><br>"
            f"{escape(t['note'])}"
        )
        folium.Marker(
            location=[t["lat"], t["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{t['name']} — {t['religion']}"),
            icon=folium.Icon(
                color="orange" if "Hindu" in t["religion"] else "red",
                icon="university", prefix="fa",
            ),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Religion breakdown chart ──
    sorted_rels = sorted(rel_counts.items(), key=lambda x: -x[1])
    fig = _bar_chart(
        [r[0] for r in sorted_rels],
        [r[1] for r in sorted_rels],
        "Temples by Religion",
        color_list=[_religion_color(r[0]) for r in sorted_rels],
        ylabel="Count",
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Data ──
    df = pd.DataFrame(TEMPLES)
    df_display = df[["name", "city", "religion", "year", "note"]].copy()
    df_display.columns = ["Name", "City", "Religion", "Year", "Description"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "hindu_buddhist_temples.csv")


def _render_monasteries():
    """Mode 6: Monasteries of the World."""
    st.markdown("### Monasteries of the World")
    st.markdown(
        f"**{len(MONASTERIES)} legendary monasteries** — from the cliff-hanging "
        "Tiger's Nest to the island fortress of Mont Saint-Michel."
    )

    # ── Stats ──
    rel_counts = {}
    for mon in MONASTERIES:
        r = mon["religion"]
        rel_counts[r] = rel_counts.get(r, 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Monasteries Listed", len(MONASTERIES))
    oldest = min(MONASTERIES, key=lambda x: x["founded"])
    c2.metric("Oldest", f"{oldest['name']} ({oldest['founded']})")
    c3.metric("Traditions", len(rel_counts))

    # ── Map ──
    m = _make_map(center_lat=38, center_lon=60, zoom=3)
    for mon in MONASTERIES:
        color = _religion_color(mon["religion"])
        popup_html = (
            f"<b>{escape(mon['name'])}</b><br>"
            f"<i>{escape(mon['city'])}</i><br>"
            f"Religion: {escape(mon['religion'])}<br>"
            f"Founded: {mon['founded']}<br><br>"
            f"{escape(mon['note'])}"
        )
        folium.Marker(
            location=[mon["lat"], mon["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{mon['name']} ({mon['founded']})"),
            icon=folium.Icon(color="darkpurple", icon="home", prefix="fa"),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Timeline chart ──
    sorted_mons = sorted(MONASTERIES, key=lambda x: x["founded"])
    fig = _bar_chart(
        [f"{m['name'][:25]} ({m['founded']})" for m in sorted_mons[:15]],
        [m["founded"] for m in sorted_mons[:15]],
        "Oldest Monasteries (by founding year)",
        color_list=[_religion_color(m["religion"]) for m in sorted_mons[:15]],
        ylabel="Year Founded",
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Data ──
    df = pd.DataFrame(MONASTERIES)
    df_display = df[["name", "city", "religion", "founded", "note"]].copy()
    df_display.columns = ["Name", "Location", "Religion", "Founded", "Description"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "monasteries.csv")


def _render_ancient_religions():
    """Mode 7: Ancient Religions & Temples."""
    st.markdown("### Ancient Religions & Sacred Sites")
    st.markdown(
        f"**{len(ANCIENT_SITES)} sites** from Egypt, Greece, Mesoamerica, and beyond — "
        "the temples, sanctuaries, and sacred places of vanished civilizations."
    )

    # ── Stats ──
    rel_counts = {}
    for s in ANCIENT_SITES:
        r = s["religion"]
        rel_counts[r] = rel_counts.get(r, 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Ancient Sites", len(ANCIENT_SITES))
    c2.metric("Civilizations", len(rel_counts))
    c3.metric("Oldest", "Gobekli Tepe (~9500 BCE)")

    # ── Map ──
    m = _make_map(center_lat=30, center_lon=30, zoom=3)
    for site in ANCIENT_SITES:
        color = _religion_color(site["religion"])
        popup_html = (
            f"<b>{escape(site['name'])}</b><br>"
            f"<i>{escape(site['city'])}</i><br>"
            f"Religion: {escape(site['religion'])}<br>"
            f"Era: {escape(site['era'])}<br><br>"
            f"{escape(site['note'])}"
        )
        folium.Marker(
            location=[site["lat"], site["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{site['name']} ({site['era']})"),
            icon=folium.Icon(color="beige", icon="landmark", prefix="fa"),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Religion breakdown chart ──
    sorted_rels = sorted(rel_counts.items(), key=lambda x: -x[1])
    fig = _bar_chart(
        [r[0] for r in sorted_rels],
        [r[1] for r in sorted_rels],
        "Ancient Sites by Civilization / Religion",
        color_list=[_religion_color(r[0]) for r in sorted_rels],
        ylabel="Count",
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Data ──
    df = pd.DataFrame(ANCIENT_SITES)
    df_display = df[["name", "city", "religion", "era", "note"]].copy()
    df_display.columns = ["Name", "Location", "Religion / Culture", "Era", "Description"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "ancient_religion_sites.csv")


def _render_pilgrimage_routes():
    """Mode 8: Pilgrimage Routes."""
    st.markdown("### Great Pilgrimage Routes")
    st.markdown(
        f"**{len(PILGRIMAGE_ROUTES)} pilgrimage routes** — ancient paths walked "
        "by millions of faithful across millennia, from the Camino to the Hajj."
    )

    # ── Stats ──
    rel_counts = {}
    for p in PILGRIMAGE_ROUTES:
        r = p["religion"]
        for rr in r.split(" / "):
            rr = rr.strip()
            rel_counts[rr] = rel_counts.get(rr, 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Routes", len(PILGRIMAGE_ROUTES))
    c2.metric("Religions", len(rel_counts))
    c3.metric("Longest", "Via Francigena (1,900 km)")

    # ── Map ──
    m = _make_map(center_lat=30, center_lon=40, zoom=2)
    route_colors = [
        "#3b82f6", "#10b981", "#f59e0b", "#f97316", "#8b5cf6",
        "#ec4899", "#ef4444", "#14b8a6", "#a855f7", "#38bdf8",
    ]
    for i, route in enumerate(PILGRIMAGE_ROUTES):
        color = route_colors[i % len(route_colors)]
        waypoints = route.get("waypoints", [])
        if waypoints:
            # Draw polyline
            folium.PolyLine(
                locations=waypoints,
                color=color,
                weight=3,
                opacity=0.8,
                tooltip=escape(route["name"]),
            ).add_to(m)
            # Start marker
            start_popup = (
                f"<b>{escape(route['name'])}</b><br>"
                f"<i>{escape(route['religion'])}</i><br>"
                f"From: {escape(route['start'])}<br>"
                f"To: {escape(route['end'])}<br>"
                f"Distance: {escape(route['distance'])}<br><br>"
                f"{escape(route['note'])}"
            )
            folium.Marker(
                location=waypoints[0],
                popup=folium.Popup(start_popup, max_width=320),
                tooltip=escape(f"Start: {route['name']}"),
                icon=folium.Icon(color="green", icon="play", prefix="fa"),
            ).add_to(m)
            # End marker
            folium.Marker(
                location=waypoints[-1],
                tooltip=escape(f"End: {route['name']}"),
                icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
            ).add_to(m)
    _show_map(m, height=520)

    # ── Data ──
    rows = []
    for route in PILGRIMAGE_ROUTES:
        rows.append({
            "Name": route["name"],
            "Religion": route["religion"],
            "Start": route["start"],
            "End": route["end"],
            "Distance": route["distance"],
            "Description": route["note"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch")
    _csv_download(df, "pilgrimage_routes.csv")


def _render_religious_conflicts():
    """Mode 9: Religious Conflicts & Historical Events."""
    st.markdown("### Religious Conflicts & Historical Events")
    st.markdown(
        f"**{len(CONFLICT_SITES)} key sites** in the history of religious conflict — "
        "Crusades, Reformation cities, partition lines, and interfaith flashpoints."
    )

    # ── Stats ──
    type_counts = {}
    for s in CONFLICT_SITES:
        t = s["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Historical Sites", len(CONFLICT_SITES))
    c2.metric("Conflict Types", len(type_counts))
    c3.metric("Time Span", "325 CE - 1992")

    # ── Type color map ──
    type_colors = {
        "Interfaith Zone": "#8b5cf6",
        "Crusade": "#ef4444",
        "Crusade / Conquest": "#dc2626",
        "Reformation": "#3b82f6",
        "Religious Wars": "#f97316",
        "Reconquista": "#f59e0b",
        "Sunni-Shia Split": "#10b981",
        "Hindu-Muslim Conflict": "#ec4899",
        "Hindu-Muslim Partition": "#ec4899",
        "Sikh Conflict": "#14b8a6",
        "Ethno-Religious Conflict": "#a855f7",
        "Doctrinal": "#38bdf8",
        "Muslim Expansion": "#f97316",
    }

    # ── Map ──
    m = _make_map(center_lat=38, center_lon=25, zoom=3)
    for site in CONFLICT_SITES:
        color = type_colors.get(site["type"], "#64748b")
        popup_html = (
            f"<b>{escape(site['name'])}</b><br>"
            f"Type: {escape(site['type'])}<br>"
            f"Era: {escape(site['era'])}<br><br>"
            f"{escape(site['note'])}"
        )
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{site['name']} ({site['era']})"),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Type breakdown chart ──
    sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
    fig = _bar_chart(
        [t[0] for t in sorted_types],
        [t[1] for t in sorted_types],
        "Events by Conflict Type",
        color_list=[type_colors.get(t[0], ACCENT) for t in sorted_types],
        ylabel="Count",
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Data ──
    df = pd.DataFrame(CONFLICT_SITES)
    df_display = df[["name", "type", "era", "note"]].copy()
    df_display.columns = ["Site", "Conflict Type", "Era", "Description"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "religious_conflicts.csv")


def _render_new_religions():
    """Mode 10: New Religions & Movements."""
    st.markdown("### New Religions & Spiritual Movements")
    st.markdown(
        f"**{len(NEW_RELIGIONS)} sites** of modern religious movements — "
        "Baha'i temples, Scientology centers, Rastafarian origins, LDS temples, and more."
    )

    # ── Stats ──
    mov_counts = {}
    for nr in NEW_RELIGIONS:
        mv = nr["movement"]
        # Group similar
        key = mv.split("(")[0].strip()
        mov_counts[key] = mov_counts.get(key, 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Listed", len(NEW_RELIGIONS))
    c2.metric("Movements", len(mov_counts))
    newest = max(NEW_RELIGIONS, key=lambda x: x["year"])
    c3.metric("Newest", f"{newest['name'][:25]}... ({newest['year']})")

    # ── Movement colors ──
    mov_color_map = {
        "Baha'i Faith": "#14b8a6",
        "Scientology": "#f59e0b",
        "Soka Gakkai": "#f97316",
        "ISKCON": "#ec4899",
        "Church of Jesus Christ of Latter-day Saints": "#3b82f6",
        "LDS": "#3b82f6",
        "Rastafari": "#10b981",
        "Tenrikyo": "#ef4444",
        "Cao Dai": "#a855f7",
        "Integral Yoga": "#8b5cf6",
        "Damanhur": "#e879f9",
        "New Age / Spiritual": "#38bdf8",
        "Unification Church": "#64748b",
    }

    def _mov_color(movement):
        for key, color in mov_color_map.items():
            if key.lower() in movement.lower():
                return color
        return ACCENT

    # ── Map ──
    m = _make_map(center_lat=25, center_lon=20, zoom=2)
    for nr in NEW_RELIGIONS:
        color = _mov_color(nr["movement"])
        popup_html = (
            f"<b>{escape(nr['name'])}</b><br>"
            f"<i>{escape(nr['city'])}</i><br>"
            f"Movement: {escape(nr['movement'])}<br>"
            f"Year: {nr['year']}<br><br>"
            f"{escape(nr['note'])}"
        )
        folium.Marker(
            location=[nr["lat"], nr["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(f"{nr['name']} — {nr['movement']}"),
            icon=folium.Icon(color="lightgray", icon="bolt", prefix="fa"),
        ).add_to(m)
    _show_map(m, height=520)

    # ── Movement breakdown chart ──
    sorted_movs = sorted(mov_counts.items(), key=lambda x: -x[1])
    fig = _bar_chart(
        [m[0][:30] for m in sorted_movs],
        [m[1] for m in sorted_movs],
        "Sites by Movement",
        color_list=[_mov_color(m[0]) for m in sorted_movs],
        ylabel="Count",
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Data ──
    df = pd.DataFrame(NEW_RELIGIONS)
    df_display = df[["name", "city", "movement", "year", "note"]].copy()
    df_display.columns = ["Name", "Location", "Movement", "Year", "Description"]
    st.dataframe(df_display, width="stretch")
    _csv_download(df, "new_religions.csv")


# ═══════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════

MAP_MODES = {
    "1. World Religion Distribution": _render_world_distribution,
    "2. Holy Cities": _render_holy_cities,
    "3. Cathedrals & Churches": _render_cathedrals,
    "4. Mosques of the World": _render_mosques,
    "5. Hindu & Buddhist Temples": _render_temples,
    "6. Monasteries": _render_monasteries,
    "7. Ancient Religions": _render_ancient_religions,
    "8. Pilgrimage Routes": _render_pilgrimage_routes,
    "9. Religious Conflicts": _render_religious_conflicts,
    "10. New Religions & Movements": _render_new_religions,
}


def render_religion_maps_tab():
    """Main render function for the World Religions & Spiritual Maps tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f54c World Religions & Spiritual Maps</h4>'
        '<p>Religion distribution, temples, churches, mosques, monasteries & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    mode = st.selectbox(
        "Select Map Mode",
        list(MAP_MODES.keys()),
        index=0,
        help="Choose one of 10 thematic religion maps to explore.",
    )

    st.markdown("---")

    # ── Render selected mode ──
    render_fn = MAP_MODES.get(mode)
    if render_fn:
        render_fn()
