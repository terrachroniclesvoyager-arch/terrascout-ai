# -*- coding: utf-8 -*-
"""
Festivals & World Events module for TerraScout AI.
Curated database of 300+ festivals, expos, sporting events and celebrations
displayed on interactive dark-themed Folium maps with stats and CSV export.
No API keys required — all data is curated/embedded.
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

# ══════════════════════════════════════════════════════════════════════════════
# THEME CONSTANTS  (TerraScout AI Glassmorphism)
# ══════════════════════════════════════════════════════════════════════════════
BG_PRIMARY   = "#0a0e1a"
BG_SURFACE   = "#111827"
BG_CARD      = "#1a2235"
BORDER       = "#2a3550"
TEXT_PRIMARY  = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED    = "#5a6580"

ACCENT_CYAN    = "#06b6d4"
ACCENT_PINK    = "#ec4899"
ACCENT_VIOLET  = "#8b5cf6"
ACCENT_AMBER   = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_RED     = "#ef4444"
ACCENT_ORANGE  = "#f97316"
ACCENT_BLUE    = "#3b82f6"
ACCENT_TEAL    = "#14b8a6"
ACCENT_ROSE    = "#f43f5e"

# ══════════════════════════════════════════════════════════════════════════════
# 10 MAP MODES — titles, colours, descriptions
# ══════════════════════════════════════════════════════════════════════════════
MAP_MODES = [
    "World's Greatest Festivals",
    "Music Festivals Worldwide",
    "Film Festivals",
    "World Expos & Fairs",
    "New Year Celebrations",
    "Food Festivals",
    "Religious Festivals",
    "Traditional Ceremonies",
    "Art & Cultural Events",
    "Sporting Events Calendar",
]

MODE_COLORS = {
    "World's Greatest Festivals":  ACCENT_PINK,
    "Music Festivals Worldwide":   ACCENT_VIOLET,
    "Film Festivals":              ACCENT_AMBER,
    "World Expos & Fairs":         ACCENT_CYAN,
    "New Year Celebrations":       ACCENT_EMERALD,
    "Food Festivals":              ACCENT_ORANGE,
    "Religious Festivals":         ACCENT_TEAL,
    "Traditional Ceremonies":      ACCENT_RED,
    "Art & Cultural Events":       ACCENT_BLUE,
    "Sporting Events Calendar":    ACCENT_ROSE,
}

MODE_ICONS = {
    "World's Greatest Festivals":  "star",
    "Music Festivals Worldwide":   "music",
    "Film Festivals":              "film",
    "World Expos & Fairs":         "globe",
    "New Year Celebrations":       "fire",
    "Food Festivals":              "cutlery",
    "Religious Festivals":         "cloud",
    "Traditional Ceremonies":      "heart",
    "Art & Cultural Events":       "eye-open",
    "Sporting Events Calendar":    "flag",
}

MODE_DESCRIPTIONS = {
    "World's Greatest Festivals": (
        "Explore the planet's most iconic celebrations — from Carnival in Rio "
        "and Oktoberfest in Munich to Diwali across India and Chinese New Year "
        "festivities spanning East Asia. These events draw millions each year."
    ),
    "Music Festivals Worldwide": (
        "Map the world's legendary music gatherings. From Glastonbury's muddy "
        "fields to the Nevada desert of Burning Man, Tomorrowland's electronic "
        "beats, and Fuji Rock in Japan's mountains."
    ),
    "Film Festivals": (
        "Discover the global circuit of prestigious film festivals — Cannes on "
        "the French Riviera, Venice's Lido, Sundance in Park City, TIFF in "
        "Toronto, and the Berlinale in Germany's capital."
    ),
    "World Expos & Fairs": (
        "Journey through the grandest international expositions — Expo 2025 Osaka, "
        "historic World Fairs from London 1851 to Dubai 2020, and future expo bids. "
        "These events reshape cities and showcase innovation."
    ),
    "New Year Celebrations": (
        "Ring in the New Year around the globe. Times Square's ball drop, "
        "Sydney Harbour fireworks, Tokyo shrine visits, London's Thames "
        "display, and Songkran water battles in Thailand."
    ),
    "Food Festivals": (
        "Taste the world through its culinary celebrations. La Tomatina's tomato "
        "battles, Naples' Pizzafest, the Cooper's Hill Cheese Roll, and the "
        "greatest street food festivals from Bangkok to Buenos Aires."
    ),
    "Religious Festivals": (
        "Journey through humanity's most profound spiritual gatherings — the "
        "Kumbh Mela's sacred rivers, Christmas markets across Europe, Vesak "
        "celebrations in Asia, and the Hajj pilgrimage to Mecca."
    ),
    "Traditional Ceremonies": (
        "Explore deep-rooted cultural traditions — Mexico's Day of the Dead, "
        "Japan's Obon festival, Venice's masked Carnival, Pamplona's Running "
        "of the Bulls, and Mongolia's Naadam games."
    ),
    "Art & Cultural Events": (
        "Discover the world's premier art destinations — Venice Biennale, "
        "Art Basel in three cities, Documenta in Kassel, Edinburgh Fringe, "
        "and spectacular light festivals from Sydney to Lyon."
    ),
    "Sporting Events Calendar": (
        "Follow the planet's greatest sporting spectacles — the Olympics, "
        "FIFA World Cup, Tour de France, Wimbledon, the Super Bowl, and "
        "iconic marathons from Boston to Tokyo."
    ),
}

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA — 1. WORLD'S GREATEST FESTIVALS  (50 entries)
# ══════════════════════════════════════════════════════════════════════════════

FESTIVAL_DATA = {

"World's Greatest Festivals": [
    {"name": "Carnival of Rio de Janeiro", "city": "Rio de Janeiro", "country": "Brazil",
     "lat": -22.9068, "lon": -43.1729, "month": "February", "attendance": "2,000,000+",
     "type": "Carnival", "description": "World's largest carnival with samba parades in the Sambadrome."},
    {"name": "Oktoberfest", "city": "Munich", "country": "Germany",
     "lat": 48.1313, "lon": 11.5497, "month": "Sep-Oct", "attendance": "6,300,000+",
     "type": "Beer Festival", "description": "World's largest beer festival on the Theresienwiese since 1810."},
    {"name": "Diwali — Festival of Lights", "city": "Varanasi", "country": "India",
     "lat": 25.3176, "lon": 83.0064, "month": "Oct-Nov", "attendance": "Nationwide",
     "type": "Festival of Lights", "description": "Hindu festival of lights celebrated with oil lamps, fireworks and sweets."},
    {"name": "Chinese New Year", "city": "Beijing", "country": "China",
     "lat": 39.9042, "lon": 116.4074, "month": "Jan-Feb", "attendance": "800,000,000+",
     "type": "Cultural", "description": "Spring Festival with dragon dances, fireworks and family reunions."},
    {"name": "Holi — Festival of Colors", "city": "Mathura", "country": "India",
     "lat": 27.4924, "lon": 77.6737, "month": "March", "attendance": "500,000+",
     "type": "Color Festival", "description": "Ancient Hindu festival throwing colored powders celebrating spring."},
    {"name": "Mardi Gras", "city": "New Orleans", "country": "USA",
     "lat": 29.9511, "lon": -90.0715, "month": "Feb-Mar", "attendance": "1,400,000+",
     "type": "Carnival", "description": "Iconic jazz-fueled parades and celebration before Lent."},
    {"name": "Songkran Water Festival", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7563, "lon": 100.5018, "month": "April", "attendance": "10,000,000+",
     "type": "Water Festival", "description": "Thai New Year celebrated with the world's largest water fight."},
    {"name": "Day of the Dead", "city": "Oaxaca", "country": "Mexico",
     "lat": 17.0732, "lon": -96.7266, "month": "Nov 1-2", "attendance": "2,000,000+",
     "type": "Traditional", "description": "Celebration honoring deceased loved ones with altars and marigolds."},
    {"name": "Carnival of Venice", "city": "Venice", "country": "Italy",
     "lat": 45.4408, "lon": 12.3155, "month": "February", "attendance": "3,000,000+",
     "type": "Carnival", "description": "Elaborate masks and costumes in St. Mark's Square since the 12th century."},
    {"name": "Edinburgh Festival Fringe", "city": "Edinburgh", "country": "UK",
     "lat": 55.9533, "lon": -3.1883, "month": "August", "attendance": "3,500,000+",
     "type": "Arts", "description": "World's largest arts festival with thousands of performances."},
    {"name": "Burning Man", "city": "Black Rock Desert", "country": "USA",
     "lat": 40.7864, "lon": -119.2065, "month": "Aug-Sep", "attendance": "80,000",
     "type": "Art/Culture", "description": "Radical self-expression community in the Nevada desert."},
    {"name": "St. Patrick's Day Festival", "city": "Dublin", "country": "Ireland",
     "lat": 53.3498, "lon": -6.2603, "month": "March 17", "attendance": "500,000+",
     "type": "Cultural", "description": "Ireland's national celebration with parades and green festivities."},
    {"name": "Notting Hill Carnival", "city": "London", "country": "UK",
     "lat": 51.5170, "lon": -0.2048, "month": "August", "attendance": "2,500,000+",
     "type": "Carnival", "description": "Europe's largest street carnival celebrating Caribbean culture."},
    {"name": "Lantern Festival (Pingxi)", "city": "Pingxi", "country": "Taiwan",
     "lat": 25.0255, "lon": 121.7384, "month": "February", "attendance": "600,000+",
     "type": "Lantern", "description": "Thousands of sky lanterns released into the night sky."},
    {"name": "Carnival of Barranquilla", "city": "Barranquilla", "country": "Colombia",
     "lat": 10.9685, "lon": -74.7813, "month": "February", "attendance": "1,500,000+",
     "type": "Carnival", "description": "UNESCO Intangible Heritage carnival with cumbia music."},
    {"name": "Glastonbury Festival", "city": "Pilton", "country": "UK",
     "lat": 51.1537, "lon": -2.5864, "month": "June", "attendance": "210,000",
     "type": "Music", "description": "Legendary music and performing arts festival."},
    {"name": "Tomorrowland", "city": "Boom", "country": "Belgium",
     "lat": 51.0897, "lon": 4.3758, "month": "July", "attendance": "400,000",
     "type": "Music", "description": "Premier electronic dance music festival with fantasy stages."},
    {"name": "Running of the Bulls", "city": "Pamplona", "country": "Spain",
     "lat": 42.8125, "lon": -1.6458, "month": "Jul 6-14", "attendance": "1,000,000+",
     "type": "Traditional", "description": "San Fermin festival with bull running through streets since 1591."},
    {"name": "Cherry Blossom Festival", "city": "Tokyo", "country": "Japan",
     "lat": 35.6762, "lon": 139.6503, "month": "Mar-Apr", "attendance": "3,000,000+",
     "type": "Nature", "description": "Hanami celebration under blooming cherry trees."},
    {"name": "Bastille Day", "city": "Paris", "country": "France",
     "lat": 48.8566, "lon": 2.3522, "month": "July 14", "attendance": "500,000+",
     "type": "National", "description": "French National Day with military parade and fireworks."},
    {"name": "Harbin Ice Festival", "city": "Harbin", "country": "China",
     "lat": 45.8038, "lon": 126.5350, "month": "Jan-Feb", "attendance": "18,000,000+",
     "type": "Ice/Snow", "description": "Massive illuminated ice sculptures in northeast China."},
    {"name": "Albuquerque Balloon Fiesta", "city": "Albuquerque", "country": "USA",
     "lat": 35.1982, "lon": -106.5956, "month": "October", "attendance": "886,000+",
     "type": "Balloon", "description": "World's largest hot air balloon festival."},
    {"name": "Fallas de Valencia", "city": "Valencia", "country": "Spain",
     "lat": 39.4699, "lon": -0.3763, "month": "Mar 15-19", "attendance": "2,000,000+",
     "type": "Fire Festival", "description": "Giant papier-mache figures burned in spectacular fires."},
    {"name": "Carnival of Oruro", "city": "Oruro", "country": "Bolivia",
     "lat": -17.9647, "lon": -67.1064, "month": "February", "attendance": "400,000+",
     "type": "Carnival", "description": "UNESCO masterpiece of Andean folklore with La Diablada dance."},
    {"name": "Up Helly Aa", "city": "Lerwick", "country": "UK",
     "lat": 60.1550, "lon": -1.1450, "month": "January", "attendance": "10,000+",
     "type": "Fire Festival", "description": "Viking fire festival with torchlit procession in Shetland."},
    {"name": "Gion Matsuri", "city": "Kyoto", "country": "Japan",
     "lat": 35.0116, "lon": 135.7681, "month": "July", "attendance": "1,000,000+",
     "type": "Traditional", "description": "Month-long festival with ornate float processions since 869 AD."},
    {"name": "Pushkar Camel Fair", "city": "Pushkar", "country": "India",
     "lat": 26.4897, "lon": 74.5511, "month": "November", "attendance": "200,000+",
     "type": "Traditional", "description": "World's largest camel fair with trading and cultural events."},
    {"name": "Yi Peng Lantern Festival", "city": "Chiang Mai", "country": "Thailand",
     "lat": 18.7883, "lon": 98.9853, "month": "November", "attendance": "100,000+",
     "type": "Lantern", "description": "Thousands of floating lanterns illuminate the night sky."},
    {"name": "Coachella", "city": "Indio", "country": "USA",
     "lat": 33.6803, "lon": -116.2389, "month": "April", "attendance": "250,000+",
     "type": "Music", "description": "Premier music and arts festival in the California desert."},
    {"name": "Carnaval de Nice", "city": "Nice", "country": "France",
     "lat": 43.7102, "lon": 7.2620, "month": "February", "attendance": "1,200,000+",
     "type": "Carnival", "description": "Major carnival on the French Riviera with flower battles."},
    {"name": "Naadam Festival", "city": "Ulaanbaatar", "country": "Mongolia",
     "lat": 47.9077, "lon": 106.9133, "month": "Jul 11-15", "attendance": "300,000+",
     "type": "Traditional", "description": "Three manly games: wrestling, horse racing, archery."},
    {"name": "White Nights Festival", "city": "Saint Petersburg", "country": "Russia",
     "lat": 59.9343, "lon": 30.3351, "month": "Jun-Jul", "attendance": "1,000,000+",
     "type": "Arts", "description": "Classical music and ballet under the midnight sun."},
    {"name": "Sapporo Snow Festival", "city": "Sapporo", "country": "Japan",
     "lat": 43.0618, "lon": 141.3545, "month": "February", "attendance": "2,000,000+",
     "type": "Snow/Ice", "description": "Massive snow and ice sculptures along city streets."},
    {"name": "Boryeong Mud Festival", "city": "Boryeong", "country": "South Korea",
     "lat": 36.3334, "lon": 126.6128, "month": "July", "attendance": "3,000,000+",
     "type": "Mud", "description": "Mud wrestling, slides and cosmetic mud baths."},
    {"name": "Sziget Festival", "city": "Budapest", "country": "Hungary",
     "lat": 47.5512, "lon": 19.0553, "month": "August", "attendance": "530,000+",
     "type": "Music", "description": "Island of Freedom music festival on the Danube."},
    {"name": "Quebec Winter Carnival", "city": "Quebec City", "country": "Canada",
     "lat": 46.8139, "lon": -71.2080, "month": "February", "attendance": "500,000+",
     "type": "Winter", "description": "World's largest winter carnival with ice palace."},
    {"name": "Carnival of Binche", "city": "Binche", "country": "Belgium",
     "lat": 50.4101, "lon": 4.1646, "month": "February", "attendance": "100,000+",
     "type": "Carnival", "description": "UNESCO masterpiece with Gilles masked performers."},
    {"name": "Palio di Siena", "city": "Siena", "country": "Italy",
     "lat": 43.3188, "lon": 11.3308, "month": "Jul/Aug", "attendance": "50,000+",
     "type": "Horse Race", "description": "Historic bareback horse race around Piazza del Campo."},
    {"name": "Timkat (Epiphany)", "city": "Gondar", "country": "Ethiopia",
     "lat": 12.6030, "lon": 37.4521, "month": "January", "attendance": "200,000+",
     "type": "Religious", "description": "Ethiopian Orthodox baptism re-enactment festival."},
    {"name": "Paro Tsechu", "city": "Paro", "country": "Bhutan",
     "lat": 27.4286, "lon": 89.4164, "month": "Mar-Apr", "attendance": "30,000+",
     "type": "Religious", "description": "Masked dance festival at Paro Dzong monastery."},
    {"name": "La Tomatina", "city": "Bunol", "country": "Spain",
     "lat": 39.4186, "lon": -0.7914, "month": "August", "attendance": "20,000+",
     "type": "Food Fight", "description": "World's largest tomato fight in the streets of Bunol."},
    {"name": "Tapati Rapa Nui", "city": "Easter Island", "country": "Chile",
     "lat": -27.1127, "lon": -109.3497, "month": "February", "attendance": "5,000+",
     "type": "Traditional", "description": "Rapa Nui cultural competition on Easter Island."},
    {"name": "Inti Raymi", "city": "Cusco", "country": "Peru",
     "lat": -13.5320, "lon": -71.9675, "month": "June 24", "attendance": "50,000+",
     "type": "Traditional", "description": "Inca Festival of the Sun at Sacsayhuaman fortress."},
    {"name": "Loi Krathong", "city": "Sukhothai", "country": "Thailand",
     "lat": 17.0068, "lon": 99.8234, "month": "November", "attendance": "500,000+",
     "type": "Traditional", "description": "Floating candle baskets on rivers and waterways."},
    {"name": "Mevlana Whirling Dervishes", "city": "Konya", "country": "Turkey",
     "lat": 37.8746, "lon": 32.4932, "month": "December", "attendance": "100,000+",
     "type": "Religious", "description": "Sufi whirling ceremony honoring the poet Rumi."},
    {"name": "Carnival of Santa Cruz", "city": "Santa Cruz de Tenerife", "country": "Spain",
     "lat": 28.4636, "lon": -16.2518, "month": "February", "attendance": "1,000,000+",
     "type": "Carnival", "description": "Second-largest carnival after Rio with queen election."},
    {"name": "Reed Dance (Umhlanga)", "city": "Mbabane", "country": "Eswatini",
     "lat": -26.3054, "lon": 31.1367, "month": "Aug-Sep", "attendance": "80,000+",
     "type": "Traditional", "description": "Swazi reed dance ceremony with thousands of maidens."},
    {"name": "Festival au Desert", "city": "Timbuktu", "country": "Mali",
     "lat": 16.7735, "lon": -3.0074, "month": "January", "attendance": "30,000+",
     "type": "Music", "description": "Tuareg music festival in the Sahara Desert."},
    {"name": "Fiesta de la Vendimia", "city": "Mendoza", "country": "Argentina",
     "lat": -32.8895, "lon": -68.8458, "month": "March", "attendance": "200,000+",
     "type": "Wine/Harvest", "description": "Grape harvest festival with wine tasting and music."},
    {"name": "Festa di San Gennaro", "city": "Naples", "country": "Italy",
     "lat": 40.8518, "lon": 14.2681, "month": "September", "attendance": "500,000+",
     "type": "Religious", "description": "Blood miracle celebration of Naples' patron saint."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 2. MUSIC FESTIVALS WORLDWIDE
# ══════════════════════════════════════════════════════════════════════════════
"Music Festivals Worldwide": [
    {"name": "Glastonbury Festival", "city": "Pilton", "country": "UK",
     "lat": 51.1537, "lon": -2.5864, "month": "June", "attendance": "210,000",
     "type": "Multi-genre", "description": "World's most iconic festival on Worthy Farm with Pyramid Stage."},
    {"name": "Coachella", "city": "Indio, California", "country": "USA",
     "lat": 33.6803, "lon": -116.2389, "month": "April", "attendance": "250,000",
     "type": "Multi-genre", "description": "Premier desert music and arts festival."},
    {"name": "Tomorrowland", "city": "Boom", "country": "Belgium",
     "lat": 51.0897, "lon": 4.3758, "month": "July", "attendance": "400,000",
     "type": "EDM", "description": "World's leading electronic dance music festival."},
    {"name": "Burning Man", "city": "Black Rock Desert", "country": "USA",
     "lat": 40.7864, "lon": -119.2065, "month": "Aug-Sep", "attendance": "80,000",
     "type": "Art/Experimental", "description": "Counter-culture art and music gathering in the desert."},
    {"name": "Lollapalooza", "city": "Chicago", "country": "USA",
     "lat": 41.8756, "lon": -87.6189, "month": "August", "attendance": "400,000",
     "type": "Multi-genre", "description": "Major multi-genre festival in Grant Park."},
    {"name": "Rock in Rio", "city": "Rio de Janeiro", "country": "Brazil",
     "lat": -22.9756, "lon": -43.3656, "month": "Sep-Oct", "attendance": "700,000",
     "type": "Rock/Pop", "description": "One of the world's largest rock festivals since 1985."},
    {"name": "Primavera Sound", "city": "Barcelona", "country": "Spain",
     "lat": 41.3874, "lon": 2.1945, "month": "May-Jun", "attendance": "200,000",
     "type": "Indie/Alternative", "description": "Barcelona's premier indie and alternative festival."},
    {"name": "Roskilde Festival", "city": "Roskilde", "country": "Denmark",
     "lat": 55.6186, "lon": 12.0546, "month": "Jun-Jul", "attendance": "130,000",
     "type": "Multi-genre", "description": "Northern Europe's largest music festival since 1971."},
    {"name": "Fuji Rock Festival", "city": "Yuzawa", "country": "Japan",
     "lat": 36.8424, "lon": 138.8105, "month": "July", "attendance": "120,000",
     "type": "Rock/Electronic", "description": "Japan's largest outdoor music event in mountain setting."},
    {"name": "Exit Festival", "city": "Novi Sad", "country": "Serbia",
     "lat": 45.2517, "lon": 19.8613, "month": "July", "attendance": "200,000",
     "type": "Multi-genre", "description": "Award-winning festival in Petrovaradin Fortress."},
    {"name": "Sziget Festival", "city": "Budapest", "country": "Hungary",
     "lat": 47.5512, "lon": 19.0553, "month": "August", "attendance": "530,000",
     "type": "Multi-genre", "description": "Island of Freedom on the Danube River."},
    {"name": "Ultra Music Festival", "city": "Miami", "country": "USA",
     "lat": 25.7743, "lon": -80.1855, "month": "March", "attendance": "170,000",
     "type": "EDM", "description": "Premier electronic music festival in Miami."},
    {"name": "Bonnaroo", "city": "Manchester, Tennessee", "country": "USA",
     "lat": 35.4760, "lon": -86.0598, "month": "June", "attendance": "80,000",
     "type": "Multi-genre", "description": "Multi-day camping festival in Tennessee."},
    {"name": "SXSW Music", "city": "Austin", "country": "USA",
     "lat": 30.2672, "lon": -97.7431, "month": "March", "attendance": "300,000+",
     "type": "Multi-genre", "description": "Music, film and tech convergence festival."},
    {"name": "Montreux Jazz Festival", "city": "Montreux", "country": "Switzerland",
     "lat": 46.4312, "lon": 6.9107, "month": "July", "attendance": "250,000",
     "type": "Jazz/World", "description": "World's most prestigious jazz festival on Lake Geneva."},
    {"name": "New Orleans Jazz & Heritage", "city": "New Orleans", "country": "USA",
     "lat": 29.9830, "lon": -90.0313, "month": "Apr-May", "attendance": "475,000",
     "type": "Jazz/Blues/Gospel", "description": "Celebration of Louisiana's music and culture."},
    {"name": "Sonar Festival", "city": "Barcelona", "country": "Spain",
     "lat": 41.3734, "lon": 2.1501, "month": "June", "attendance": "126,000",
     "type": "Electronic", "description": "International festival of advanced music and media art."},
    {"name": "Download Festival", "city": "Donington Park", "country": "UK",
     "lat": 52.8304, "lon": -1.3747, "month": "June", "attendance": "120,000",
     "type": "Rock/Metal", "description": "UK's premier rock and metal festival."},
    {"name": "Reading & Leeds Festival", "city": "Reading", "country": "UK",
     "lat": 51.4454, "lon": -0.9508, "month": "August", "attendance": "195,000",
     "type": "Rock/Alternative", "description": "Legendary twin-site rock festivals since 1961."},
    {"name": "Electric Daisy Carnival", "city": "Las Vegas", "country": "USA",
     "lat": 36.2710, "lon": -115.0129, "month": "May", "attendance": "450,000",
     "type": "EDM", "description": "Massive EDM carnival under the neon lights."},
    {"name": "Mawazine", "city": "Rabat", "country": "Morocco",
     "lat": 34.0209, "lon": -6.8417, "month": "June", "attendance": "2,500,000",
     "type": "World/Pop", "description": "One of the world's biggest music festivals by attendance."},
    {"name": "Splendour in the Grass", "city": "Byron Bay", "country": "Australia",
     "lat": -28.6474, "lon": 153.6020, "month": "July", "attendance": "40,000",
     "type": "Indie/Rock", "description": "Australia's favourite festival in Byron Bay."},
    {"name": "Summerfest", "city": "Milwaukee", "country": "USA",
     "lat": 43.0296, "lon": -87.8965, "month": "Jun-Jul", "attendance": "800,000",
     "type": "Multi-genre", "description": "World's largest music festival by duration."},
    {"name": "Afropunk", "city": "Brooklyn", "country": "USA",
     "lat": 40.6612, "lon": -73.9693, "month": "August", "attendance": "60,000",
     "type": "Afro-Punk/R&B", "description": "Multicultural music and art festival."},
    {"name": "Creamfields", "city": "Daresbury", "country": "UK",
     "lat": 53.3365, "lon": -2.6227, "month": "August", "attendance": "70,000",
     "type": "EDM", "description": "UK's biggest dance music festival."},
    {"name": "Colours of Ostrava", "city": "Ostrava", "country": "Czech Republic",
     "lat": 49.8209, "lon": 18.2625, "month": "July", "attendance": "50,000",
     "type": "Multi-genre", "description": "Festival in former steelworks industrial complex."},
    {"name": "Austin City Limits", "city": "Austin", "country": "USA",
     "lat": 30.2653, "lon": -97.7494, "month": "October", "attendance": "450,000",
     "type": "Multi-genre", "description": "Two-weekend festival in Zilker Park."},
    {"name": "Wireless Festival", "city": "London", "country": "UK",
     "lat": 51.5613, "lon": -0.0742, "month": "July", "attendance": "150,000",
     "type": "Hip-Hop/R&B", "description": "London's biggest urban music festival."},
    {"name": "Electric Forest", "city": "Rothbury", "country": "USA",
     "lat": 43.6934, "lon": -85.9394, "month": "June", "attendance": "40,000",
     "type": "EDM/Jam", "description": "Enchanted forest festival in Michigan."},
    {"name": "Woodstock (historic)", "city": "Bethel", "country": "USA",
     "lat": 41.7009, "lon": -74.8782, "month": "Aug 1969", "attendance": "400,000",
     "type": "Rock", "description": "Historic 1969 counter-culture rock festival."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 3. FILM FESTIVALS
# ══════════════════════════════════════════════════════════════════════════════
"Film Festivals": [
    {"name": "Cannes Film Festival", "city": "Cannes", "country": "France",
     "lat": 43.5528, "lon": 7.0174, "month": "May", "attendance": "200,000+",
     "type": "International (Palme d'Or)", "description": "World's most prestigious film festival since 1946."},
    {"name": "Venice Film Festival", "city": "Venice", "country": "Italy",
     "lat": 45.3545, "lon": 12.3567, "month": "Aug-Sep", "attendance": "100,000+",
     "type": "International (Golden Lion)", "description": "Oldest film festival in the world, on the Lido since 1932."},
    {"name": "Berlin International Film Festival", "city": "Berlin", "country": "Germany",
     "lat": 52.5100, "lon": 13.3761, "month": "February", "attendance": "500,000+",
     "type": "International (Golden Bear)", "description": "Major Berlinale with focus on political cinema."},
    {"name": "Toronto International Film Festival", "city": "Toronto", "country": "Canada",
     "lat": 43.6532, "lon": -79.3832, "month": "September", "attendance": "480,000+",
     "type": "International (People's Choice)", "description": "Major Oscar-season launch pad (TIFF)."},
    {"name": "Sundance Film Festival", "city": "Park City", "country": "USA",
     "lat": 40.6461, "lon": -111.4980, "month": "January", "attendance": "120,000+",
     "type": "Independent (Grand Jury Prize)", "description": "World's premier independent film festival."},
    {"name": "San Sebastian Film Festival", "city": "San Sebastian", "country": "Spain",
     "lat": 43.3183, "lon": -1.9812, "month": "September", "attendance": "180,000+",
     "type": "International (Golden Shell)", "description": "Spain's premier film festival."},
    {"name": "Locarno Film Festival", "city": "Locarno", "country": "Switzerland",
     "lat": 46.1670, "lon": 8.7942, "month": "August", "attendance": "150,000+",
     "type": "International (Golden Leopard)", "description": "Open-air screenings in Piazza Grande."},
    {"name": "Karlovy Vary Film Festival", "city": "Karlovy Vary", "country": "Czech Republic",
     "lat": 50.2318, "lon": 12.8715, "month": "Jun-Jul", "attendance": "140,000+",
     "type": "International (Crystal Globe)", "description": "Major Central European film festival."},
    {"name": "Tribeca Film Festival", "city": "New York", "country": "USA",
     "lat": 40.7195, "lon": -74.0089, "month": "June", "attendance": "150,000+",
     "type": "Major (Founders Award)", "description": "Founded by Robert De Niro post-9/11."},
    {"name": "SXSW Film", "city": "Austin", "country": "USA",
     "lat": 30.2672, "lon": -97.7431, "month": "March", "attendance": "300,000+",
     "type": "Major (Grand Jury Award)", "description": "Tech-savvy film and media festival."},
    {"name": "Telluride Film Festival", "city": "Telluride", "country": "USA",
     "lat": 37.9375, "lon": -107.8123, "month": "September", "attendance": "5,000+",
     "type": "Major (Silver Medallion)", "description": "Intimate mountain-town festival for cinephiles."},
    {"name": "Rotterdam Film Festival", "city": "Rotterdam", "country": "Netherlands",
     "lat": 51.9244, "lon": 4.4777, "month": "Jan-Feb", "attendance": "100,000+",
     "type": "Major (Tiger Award)", "description": "Champion of independent and experimental cinema."},
    {"name": "BFI London Film Festival", "city": "London", "country": "UK",
     "lat": 51.5074, "lon": -0.1278, "month": "October", "attendance": "200,000+",
     "type": "Major", "description": "UK's leading film event."},
    {"name": "Busan International Film Festival", "city": "Busan", "country": "South Korea",
     "lat": 35.1588, "lon": 129.1604, "month": "October", "attendance": "220,000+",
     "type": "International (New Currents)", "description": "Asia's largest and most prestigious film festival."},
    {"name": "Tokyo International Film Festival", "city": "Tokyo", "country": "Japan",
     "lat": 35.6595, "lon": 139.7004, "month": "Oct-Nov", "attendance": "100,000+",
     "type": "A-list (Tokyo Grand Prix)", "description": "Japan's premier international film event."},
    {"name": "Cairo International Film Festival", "city": "Cairo", "country": "Egypt",
     "lat": 30.0444, "lon": 31.2357, "month": "Nov-Dec", "attendance": "50,000+",
     "type": "A-list (Golden Pyramid)", "description": "Middle East and Africa's oldest film festival."},
    {"name": "Mumbai Film Festival (MAMI)", "city": "Mumbai", "country": "India",
     "lat": 19.0760, "lon": 72.8777, "month": "October", "attendance": "60,000+",
     "type": "Major (Golden Gateway)", "description": "India's premier international film festival."},
    {"name": "Mar del Plata Film Festival", "city": "Mar del Plata", "country": "Argentina",
     "lat": -38.0055, "lon": -57.5426, "month": "November", "attendance": "80,000+",
     "type": "A-list (Astor Award)", "description": "Latin America's only A-list accredited festival."},
    {"name": "Annecy Animation Festival", "city": "Annecy", "country": "France",
     "lat": 45.8992, "lon": 6.1294, "month": "June", "attendance": "100,000+",
     "type": "Major (Cristal Award)", "description": "World's premier animation festival."},
    {"name": "Shanghai International Film Festival", "city": "Shanghai", "country": "China",
     "lat": 31.2304, "lon": 121.4737, "month": "June", "attendance": "300,000+",
     "type": "A-list (Golden Goblet)", "description": "China's top international film event."},
    {"name": "Tallinn Black Nights", "city": "Tallinn", "country": "Estonia",
     "lat": 59.4370, "lon": 24.7536, "month": "November", "attendance": "80,000+",
     "type": "A-list", "description": "Unique northern European autumn festival."},
    {"name": "Sitges Film Festival", "city": "Sitges", "country": "Spain",
     "lat": 41.2348, "lon": 1.8124, "month": "October", "attendance": "50,000+",
     "type": "Major (Fantasy/Horror)", "description": "World's best-known genre film festival."},
    {"name": "Sarajevo Film Festival", "city": "Sarajevo", "country": "Bosnia",
     "lat": 43.8563, "lon": 18.4131, "month": "August", "attendance": "100,000+",
     "type": "Major (Heart of Sarajevo)", "description": "Founded during the siege, now a major regional event."},
    {"name": "Goteborg Film Festival", "city": "Gothenburg", "country": "Sweden",
     "lat": 57.7089, "lon": 11.9746, "month": "Jan-Feb", "attendance": "150,000+",
     "type": "Major (Dragon Award)", "description": "Scandinavia's leading film festival."},
    {"name": "Melbourne International Film Festival", "city": "Melbourne", "country": "Australia",
     "lat": -37.8136, "lon": 144.9631, "month": "August", "attendance": "200,000+",
     "type": "Major", "description": "One of the oldest film festivals in the world."},
    {"name": "Morelia Film Festival", "city": "Morelia", "country": "Mexico",
     "lat": 19.7060, "lon": -101.1950, "month": "October", "attendance": "50,000+",
     "type": "Major", "description": "Mexico's top film festival for new Mexican cinema."},
    {"name": "Clermont-Ferrand Short Film Festival", "city": "Clermont-Ferrand", "country": "France",
     "lat": 45.7772, "lon": 3.0870, "month": "February", "attendance": "170,000+",
     "type": "Major (Grand Prix)", "description": "World's largest short film festival."},
    {"name": "Zurich Film Festival", "city": "Zurich", "country": "Switzerland",
     "lat": 47.3769, "lon": 8.5417, "month": "Sep-Oct", "attendance": "100,000+",
     "type": "Major (Golden Eye)", "description": "Rapidly growing Swiss film event."},
    {"name": "Warsaw Film Festival", "city": "Warsaw", "country": "Poland",
     "lat": 52.2297, "lon": 21.0122, "month": "October", "attendance": "90,000+",
     "type": "Major", "description": "Central Europe's key discovery festival."},
    {"name": "Fantasia Film Festival", "city": "Montreal", "country": "Canada",
     "lat": 45.5017, "lon": -73.5673, "month": "July", "attendance": "100,000+",
     "type": "Major (Genre)", "description": "North America's top genre film festival."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 4. WORLD EXPOS & FAIRS
# ══════════════════════════════════════════════════════════════════════════════
"World Expos & Fairs": [
    {"name": "Expo 2025 Osaka", "city": "Osaka", "country": "Japan",
     "lat": 34.6537, "lon": 135.4101, "month": "Apr-Oct 2025", "attendance": "28,000,000 (est)",
     "type": "World Expo", "description": "Theme: Designing Future Society for Our Lives, on Yumeshima island."},
    {"name": "Expo 2020 Dubai", "city": "Dubai", "country": "UAE",
     "lat": 24.9616, "lon": 55.1471, "month": "Oct 2021-Mar 2022", "attendance": "24,102,967",
     "type": "World Expo", "description": "Theme: Connecting Minds, Creating the Future. 192 country pavilions."},
    {"name": "Expo 2015 Milan", "city": "Milan", "country": "Italy",
     "lat": 45.5197, "lon": 9.0923, "month": "May-Oct 2015", "attendance": "21,500,000",
     "type": "World Expo", "description": "Theme: Feeding the Planet, Energy for Life."},
    {"name": "Expo 2010 Shanghai", "city": "Shanghai", "country": "China",
     "lat": 31.1847, "lon": 121.4749, "month": "May-Oct 2010", "attendance": "73,084,400",
     "type": "World Expo", "description": "Most attended expo ever. Theme: Better City, Better Life."},
    {"name": "Expo 2005 Aichi", "city": "Nagoya", "country": "Japan",
     "lat": 35.1711, "lon": 137.0569, "month": "Mar-Sep 2005", "attendance": "22,049,544",
     "type": "World Expo", "description": "Theme: Nature's Wisdom. Featured robot technology."},
    {"name": "Expo 2000 Hannover", "city": "Hannover", "country": "Germany",
     "lat": 52.3220, "lon": 9.8122, "month": "Jun-Oct 2000", "attendance": "18,000,000",
     "type": "World Expo", "description": "Theme: Humankind, Nature, Technology."},
    {"name": "Expo 98 Lisbon", "city": "Lisbon", "country": "Portugal",
     "lat": 38.7652, "lon": -9.0944, "month": "May-Sep 1998", "attendance": "11,000,000",
     "type": "World Expo", "description": "Theme: The Oceans, a Heritage for the Future. Built Parque das Nacoes."},
    {"name": "Expo 92 Seville", "city": "Seville", "country": "Spain",
     "lat": 37.3935, "lon": -6.0127, "month": "Apr-Oct 1992", "attendance": "41,814,571",
     "type": "World Expo", "description": "500th anniversary of Columbus. Theme: Age of Discovery."},
    {"name": "Great Exhibition 1851", "city": "London", "country": "UK",
     "lat": 51.5023, "lon": -0.1741, "month": "May-Oct 1851", "attendance": "6,039,195",
     "type": "World Fair (Historic)", "description": "First World's Fair in the Crystal Palace, Hyde Park."},
    {"name": "1889 Paris Exposition", "city": "Paris", "country": "France",
     "lat": 48.8584, "lon": 2.2945, "month": "May-Oct 1889", "attendance": "32,000,000",
     "type": "World Fair (Historic)", "description": "Built the Eiffel Tower. Centennial of the French Revolution."},
    {"name": "1893 World's Columbian Exposition", "city": "Chicago", "country": "USA",
     "lat": 41.7897, "lon": -87.5767, "month": "May-Oct 1893", "attendance": "27,300,000",
     "type": "World Fair (Historic)", "description": "The White City. Introduced Ferris wheel and alternating current."},
    {"name": "1900 Paris Exposition", "city": "Paris", "country": "France",
     "lat": 48.8618, "lon": 2.2876, "month": "Apr-Nov 1900", "attendance": "50,860,801",
     "type": "World Fair (Historic)", "description": "Showcased Art Nouveau, moving sidewalks, and early cinema."},
    {"name": "1939 New York World's Fair", "city": "New York", "country": "USA",
     "lat": 40.7465, "lon": -73.8451, "month": "Apr-Oct 1939/1940", "attendance": "44,000,000",
     "type": "World Fair (Historic)", "description": "Theme: Building the World of Tomorrow. Trylon and Perisphere."},
    {"name": "Expo 67 Montreal", "city": "Montreal", "country": "Canada",
     "lat": 45.5134, "lon": -73.5314, "month": "Apr-Oct 1967", "attendance": "50,306,648",
     "type": "World Expo", "description": "Theme: Man and His World. Geodesic dome by Buckminster Fuller."},
    {"name": "Expo 70 Osaka", "city": "Osaka", "country": "Japan",
     "lat": 34.8077, "lon": 135.5326, "month": "Mar-Sep 1970", "attendance": "64,218,770",
     "type": "World Expo", "description": "Theme: Progress and Harmony for Mankind. Tower of the Sun."},
    {"name": "1964 New York World's Fair", "city": "New York", "country": "USA",
     "lat": 40.7465, "lon": -73.8451, "month": "Apr-Oct 1964/1965", "attendance": "51,607,037",
     "type": "World Fair (Historic)", "description": "Unisphere and Disney's It's a Small World debut."},
    {"name": "Expo 88 Brisbane", "city": "Brisbane", "country": "Australia",
     "lat": -27.4733, "lon": 153.0189, "month": "Apr-Oct 1988", "attendance": "18,000,000",
     "type": "World Expo", "description": "Theme: Leisure in the Age of Technology."},
    {"name": "Expo 2030 Riyadh (Upcoming)", "city": "Riyadh", "country": "Saudi Arabia",
     "lat": 24.7136, "lon": 46.6753, "month": "Oct 2030-Mar 2031", "attendance": "TBD",
     "type": "World Expo (Future)", "description": "Theme: The Era of Change. First expo in the Middle East region."},
    {"name": "Expo 2035 (Bidding)", "city": "Various", "country": "TBD",
     "lat": 48.8566, "lon": 2.3522, "month": "2035", "attendance": "TBD",
     "type": "World Expo (Future)", "description": "Multiple cities bidding for the 2035 World Expo."},
    {"name": "1958 Brussels World's Fair", "city": "Brussels", "country": "Belgium",
     "lat": 50.8946, "lon": 4.3418, "month": "Apr-Oct 1958", "attendance": "41,454,412",
     "type": "World Fair (Historic)", "description": "Built the Atomium. Theme: Balance for a More Human World."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 5. NEW YEAR CELEBRATIONS
# ══════════════════════════════════════════════════════════════════════════════
"New Year Celebrations": [
    {"name": "Times Square Ball Drop", "city": "New York City", "country": "USA",
     "lat": 40.7580, "lon": -73.9855, "month": "December 31", "attendance": "1,000,000+",
     "type": "Ball Drop", "description": "Iconic Waterford Crystal ball drop watched by a billion worldwide."},
    {"name": "Sydney Harbour Fireworks", "city": "Sydney", "country": "Australia",
     "lat": -33.8568, "lon": 151.2153, "month": "December 31", "attendance": "1,600,000+",
     "type": "Fireworks", "description": "Spectacular fireworks off the Harbour Bridge and Opera House."},
    {"name": "Chinese New Year (Beijing)", "city": "Beijing", "country": "China",
     "lat": 39.9042, "lon": 116.4074, "month": "Jan-Feb", "attendance": "800,000,000+",
     "type": "Lunar New Year", "description": "Spring Festival with dragon dances, fireworks, and temple fairs."},
    {"name": "Hatsumode (Meiji Shrine)", "city": "Tokyo", "country": "Japan",
     "lat": 35.6764, "lon": 139.6993, "month": "January 1-3", "attendance": "3,000,000+",
     "type": "Shrine Visit", "description": "Traditional first shrine visit of the New Year at Meiji Jingu."},
    {"name": "London New Year Fireworks", "city": "London", "country": "UK",
     "lat": 51.5014, "lon": -0.1193, "month": "December 31", "attendance": "250,000+",
     "type": "Fireworks", "description": "Thames fireworks display centred on the London Eye."},
    {"name": "Copacabana Beach Party", "city": "Rio de Janeiro", "country": "Brazil",
     "lat": -22.9711, "lon": -43.1822, "month": "December 31", "attendance": "2,000,000+",
     "type": "Beach Party", "description": "Reveillon celebrations with white-clad crowds on Copacabana."},
    {"name": "Hogmanay", "city": "Edinburgh", "country": "UK",
     "lat": 55.9533, "lon": -3.1883, "month": "December 31", "attendance": "150,000+",
     "type": "Street Party", "description": "Scotland's famous New Year with torchlight procession."},
    {"name": "Dubai Burj Khalifa Fireworks", "city": "Dubai", "country": "UAE",
     "lat": 25.1972, "lon": 55.2744, "month": "December 31", "attendance": "1,000,000+",
     "type": "Fireworks", "description": "Record-breaking fireworks display from the Burj Khalifa."},
    {"name": "Chinese New Year (Hong Kong)", "city": "Hong Kong", "country": "China",
     "lat": 22.3193, "lon": 114.1694, "month": "Jan-Feb", "attendance": "Millions",
     "type": "Lunar New Year", "description": "Night parade, fireworks over Victoria Harbour."},
    {"name": "Brandenburg Gate Celebration", "city": "Berlin", "country": "Germany",
     "lat": 52.5163, "lon": 13.3777, "month": "December 31", "attendance": "1,000,000+",
     "type": "Party Mile", "description": "Europe's largest open-air New Year party."},
    {"name": "Champs-Elysees Light Show", "city": "Paris", "country": "France",
     "lat": 48.8698, "lon": 2.3075, "month": "December 31", "attendance": "600,000+",
     "type": "Light Show", "description": "Laser and light show on the Arc de Triomphe."},
    {"name": "Taipei 101 Fireworks", "city": "Taipei", "country": "Taiwan",
     "lat": 25.0338, "lon": 121.5645, "month": "December 31", "attendance": "500,000+",
     "type": "Fireworks", "description": "Fireworks launched directly from the Taipei 101 skyscraper."},
    {"name": "Songkran (Thai New Year)", "city": "Chiang Mai", "country": "Thailand",
     "lat": 18.7883, "lon": 98.9853, "month": "April 13-15", "attendance": "10,000,000+",
     "type": "Water Festival", "description": "Thai New Year with massive water fights nationwide."},
    {"name": "Reykjavik Bonfire Night", "city": "Reykjavik", "country": "Iceland",
     "lat": 64.1466, "lon": -21.9426, "month": "December 31", "attendance": "100,000+",
     "type": "Bonfire/Fireworks", "description": "Community bonfires and citizen-launched fireworks."},
    {"name": "Nowruz (Persian New Year)", "city": "Tehran", "country": "Iran",
     "lat": 35.6892, "lon": 51.3890, "month": "March 20-21", "attendance": "80,000,000+",
     "type": "Cultural", "description": "Persian New Year celebrating the spring equinox across Central Asia."},
    {"name": "Losar (Tibetan New Year)", "city": "Lhasa", "country": "China",
     "lat": 29.6520, "lon": 91.1721, "month": "Feb-Mar", "attendance": "500,000+",
     "type": "Cultural/Buddhist", "description": "Tibetan New Year with monastery ceremonies and folk dances."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 6. FOOD FESTIVALS
# ══════════════════════════════════════════════════════════════════════════════
"Food Festivals": [
    {"name": "La Tomatina", "city": "Bunol", "country": "Spain",
     "lat": 39.4186, "lon": -0.7914, "month": "August", "attendance": "20,000+",
     "type": "Tomato Fight", "description": "World's largest tomato-throwing festival."},
    {"name": "Pizzafest", "city": "Naples", "country": "Italy",
     "lat": 40.8518, "lon": 14.2681, "month": "September", "attendance": "100,000+",
     "type": "Pizza Festival", "description": "Celebration of Neapolitan pizza with tastings and competitions."},
    {"name": "Cooper's Hill Cheese Rolling", "city": "Brockworth", "country": "UK",
     "lat": 51.8423, "lon": -2.1519, "month": "May", "attendance": "5,000+",
     "type": "Cheese/Traditional", "description": "Competitors chase a 9lb Double Gloucester cheese downhill."},
    {"name": "Bacon Festival", "city": "Easton, Pennsylvania", "country": "USA",
     "lat": 40.6912, "lon": -75.2082, "month": "November", "attendance": "30,000+",
     "type": "Bacon", "description": "PA Bacon Fest celebrating all things bacon."},
    {"name": "Taste of Chicago", "city": "Chicago", "country": "USA",
     "lat": 41.8751, "lon": -87.6200, "month": "July", "attendance": "1,600,000+",
     "type": "Street Food", "description": "World's largest outdoor food festival in Grant Park."},
    {"name": "Melbourne Food and Wine Festival", "city": "Melbourne", "country": "Australia",
     "lat": -37.8136, "lon": 144.9631, "month": "March", "attendance": "250,000+",
     "type": "Food & Wine", "description": "Australia's premier food and wine event with 300+ events."},
    {"name": "Salon du Chocolat", "city": "Paris", "country": "France",
     "lat": 48.8566, "lon": 2.3522, "month": "October", "attendance": "130,000+",
     "type": "Chocolate", "description": "World's largest event dedicated to chocolate and cocoa."},
    {"name": "World Street Food Congress", "city": "Singapore", "country": "Singapore",
     "lat": 1.3521, "lon": 103.8198, "month": "May-Jun", "attendance": "50,000+",
     "type": "Street Food", "description": "Global gathering of street food masters and hawker culture."},
    {"name": "Hokkaido Food Festival", "city": "Sapporo", "country": "Japan",
     "lat": 43.0618, "lon": 141.3545, "month": "September", "attendance": "2,000,000+",
     "type": "Harvest Food", "description": "Celebration of Hokkaido's seafood, dairy, and produce."},
    {"name": "Feast of San Gennaro", "city": "New York City", "country": "USA",
     "lat": 40.7195, "lon": -73.9963, "month": "September", "attendance": "1,000,000+",
     "type": "Italian Food", "description": "Little Italy's iconic street food festival since 1926."},
    {"name": "Beaujolais Nouveau Day", "city": "Beaujeu", "country": "France",
     "lat": 46.1556, "lon": 4.5875, "month": "November", "attendance": "Nationwide",
     "type": "Wine Release", "description": "Annual midnight release of the first Beaujolais wine."},
    {"name": "Night Noodle Markets", "city": "Sydney", "country": "Australia",
     "lat": -33.8724, "lon": 151.2145, "month": "October", "attendance": "200,000+",
     "type": "Asian Street Food", "description": "Open-air Asian street food markets at Hyde Park."},
    {"name": "Feria de Abril (Food)", "city": "Seville", "country": "Spain",
     "lat": 37.3886, "lon": -5.9823, "month": "April", "attendance": "1,000,000+",
     "type": "Food & Dance", "description": "Spring fair with tapas, sherry and flamenco."},
    {"name": "Grape Harvest Festival", "city": "Mendoza", "country": "Argentina",
     "lat": -32.8895, "lon": -68.8458, "month": "March", "attendance": "200,000+",
     "type": "Wine Harvest", "description": "Vendimia festival celebrating Argentina's premier wine region."},
    {"name": "Gilroy Garlic Festival", "city": "Gilroy", "country": "USA",
     "lat": 37.0058, "lon": -121.5683, "month": "July", "attendance": "100,000+",
     "type": "Garlic", "description": "Garlic capital of the world celebrates with cook-offs and tastings."},
    {"name": "Oktoberfest (Food Focus)", "city": "Munich", "country": "Germany",
     "lat": 48.1313, "lon": 11.5497, "month": "Sep-Oct", "attendance": "6,300,000+",
     "type": "Beer & Food", "description": "Traditional pretzels, sausages, roast chicken alongside beer."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 7. RELIGIOUS FESTIVALS
# ══════════════════════════════════════════════════════════════════════════════
"Religious Festivals": [
    {"name": "Kumbh Mela", "city": "Prayagraj", "country": "India",
     "lat": 25.4358, "lon": 81.8463, "month": "Jan-Mar (varies)", "attendance": "120,000,000+",
     "type": "Hindu Pilgrimage", "description": "World's largest religious gathering at sacred river confluence."},
    {"name": "Hajj Pilgrimage", "city": "Mecca", "country": "Saudi Arabia",
     "lat": 21.4225, "lon": 39.8262, "month": "Islamic calendar", "attendance": "2,500,000+",
     "type": "Islamic Pilgrimage", "description": "Annual Islamic pilgrimage to the Kaaba."},
    {"name": "Eid al-Fitr (Istanbul)", "city": "Istanbul", "country": "Turkey",
     "lat": 41.0082, "lon": 28.9784, "month": "Islamic calendar", "attendance": "Millions",
     "type": "Islamic", "description": "End of Ramadan celebrations at Blue Mosque and Hagia Sophia."},
    {"name": "Christmas Markets (Nuremberg)", "city": "Nuremberg", "country": "Germany",
     "lat": 49.4521, "lon": 11.0767, "month": "December", "attendance": "2,000,000+",
     "type": "Christian/Christmas", "description": "Christkindlesmarkt: Germany's most famous Christmas market."},
    {"name": "Christmas Markets (Vienna)", "city": "Vienna", "country": "Austria",
     "lat": 48.2082, "lon": 16.3738, "month": "Nov-Dec", "attendance": "3,000,000+",
     "type": "Christian/Christmas", "description": "Historic Rathausplatz Christmas market since 1298."},
    {"name": "Christmas Markets (Strasbourg)", "city": "Strasbourg", "country": "France",
     "lat": 48.5734, "lon": 7.7521, "month": "Nov-Dec", "attendance": "2,000,000+",
     "type": "Christian/Christmas", "description": "Capital of Christmas market since 1570."},
    {"name": "Easter in Vatican City", "city": "Vatican City", "country": "Vatican City",
     "lat": 41.9029, "lon": 12.4534, "month": "Mar-Apr", "attendance": "100,000+",
     "type": "Christian", "description": "Papal Easter Mass and Urbi et Orbi blessing in St. Peter's Square."},
    {"name": "Semana Santa", "city": "Seville", "country": "Spain",
     "lat": 37.3886, "lon": -5.9823, "month": "Mar-Apr", "attendance": "1,000,000+",
     "type": "Christian", "description": "Spectacular Holy Week processions with elaborate pasos."},
    {"name": "Vesak (Buddha Day)", "city": "Kandy", "country": "Sri Lanka",
     "lat": 7.2906, "lon": 80.6337, "month": "May", "attendance": "500,000+",
     "type": "Buddhist", "description": "Celebration of Buddha's birth, enlightenment, and passing."},
    {"name": "Rath Yatra (Chariot Festival)", "city": "Puri", "country": "India",
     "lat": 19.8135, "lon": 85.8312, "month": "Jun-Jul", "attendance": "1,000,000+",
     "type": "Hindu", "description": "Annual chariot procession of Lord Jagannath."},
    {"name": "Ganesh Chaturthi", "city": "Mumbai", "country": "India",
     "lat": 19.0760, "lon": 72.8777, "month": "Aug-Sep", "attendance": "Millions",
     "type": "Hindu", "description": "Ten-day festival honoring Lord Ganesha with grand immersion."},
    {"name": "Navratri / Durga Puja", "city": "Kolkata", "country": "India",
     "lat": 22.5726, "lon": 88.3639, "month": "Sep-Oct", "attendance": "Millions",
     "type": "Hindu", "description": "Nine nights celebrating goddess Durga with pandals and dance."},
    {"name": "Timkat (Ethiopian Epiphany)", "city": "Gondar", "country": "Ethiopia",
     "lat": 12.6090, "lon": 37.4684, "month": "January", "attendance": "200,000+",
     "type": "Orthodox Christian", "description": "Ethiopian Orthodox celebration of the Baptism of Jesus."},
    {"name": "Obon Festival", "city": "Kyoto", "country": "Japan",
     "lat": 35.0116, "lon": 135.7681, "month": "August", "attendance": "Millions",
     "type": "Buddhist", "description": "Japanese festival honoring ancestors with Bon dancing."},
    {"name": "Sukkot (Feast of Tabernacles)", "city": "Jerusalem", "country": "Israel",
     "lat": 31.7767, "lon": 35.2345, "month": "Sep-Oct", "attendance": "200,000+",
     "type": "Jewish", "description": "Jewish harvest festival with decorative booths."},
    {"name": "Dia de la Candelaria", "city": "Puno", "country": "Peru",
     "lat": -15.8402, "lon": -70.0219, "month": "February", "attendance": "100,000+",
     "type": "Catholic/Indigenous", "description": "UNESCO-listed festival blending Catholic and Andean traditions."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 8. TRADITIONAL CEREMONIES
# ══════════════════════════════════════════════════════════════════════════════
"Traditional Ceremonies": [
    {"name": "Day of the Dead (Dia de los Muertos)", "city": "Oaxaca", "country": "Mexico",
     "lat": 17.0732, "lon": -96.7266, "month": "Nov 1-2", "attendance": "2,000,000+",
     "type": "Ancestor Worship", "description": "Families build altars (ofrendas) with marigolds and sugar skulls."},
    {"name": "Obon Festival", "city": "Kyoto", "country": "Japan",
     "lat": 35.0116, "lon": 135.7681, "month": "August", "attendance": "Millions",
     "type": "Ancestor Worship", "description": "Buddhist festival honouring ancestors with Gozan no Okuribi fires."},
    {"name": "Carnival of Venice", "city": "Venice", "country": "Italy",
     "lat": 45.4408, "lon": 12.3155, "month": "February", "attendance": "3,000,000+",
     "type": "Masked Carnival", "description": "Elaborate masks and costumes since the 12th century."},
    {"name": "Running of the Bulls (San Fermin)", "city": "Pamplona", "country": "Spain",
     "lat": 42.8125, "lon": -1.6458, "month": "Jul 6-14", "attendance": "1,000,000+",
     "type": "Bull Running", "description": "Centuries-old tradition of running ahead of bulls."},
    {"name": "Songkran Water Festival", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7563, "lon": 100.5018, "month": "Apr 13-15", "attendance": "10,000,000+",
     "type": "Water Festival", "description": "Thai New Year with world's biggest water fight."},
    {"name": "Gion Matsuri", "city": "Kyoto", "country": "Japan",
     "lat": 35.0042, "lon": 135.7764, "month": "July", "attendance": "1,000,000+",
     "type": "Shinto Festival", "description": "Month-long festival with grand float processions since 869 AD."},
    {"name": "Naadam Festival", "city": "Ulaanbaatar", "country": "Mongolia",
     "lat": 47.9184, "lon": 106.9177, "month": "Jul 11-15", "attendance": "300,000+",
     "type": "Traditional Sports", "description": "Three Manly Games: wrestling, horse racing, and archery."},
    {"name": "Fallas de Valencia", "city": "Valencia", "country": "Spain",
     "lat": 39.4699, "lon": -0.3763, "month": "Mar 15-19", "attendance": "2,000,000+",
     "type": "Fire Festival", "description": "Giant satirical sculptures burned on the final night."},
    {"name": "Pushkar Camel Fair", "city": "Pushkar", "country": "India",
     "lat": 26.4897, "lon": 74.5511, "month": "November", "attendance": "200,000+",
     "type": "Traditional Market", "description": "Ancient livestock fair with camel trading and races."},
    {"name": "Carnival of Oruro", "city": "Oruro", "country": "Bolivia",
     "lat": -17.9647, "lon": -67.1142, "month": "February", "attendance": "400,000+",
     "type": "Traditional/Religious", "description": "UNESCO-listed Andean carnival with La Diablada devil dance."},
    {"name": "Boryeong Mud Festival", "city": "Boryeong", "country": "South Korea",
     "lat": 36.3309, "lon": 126.6132, "month": "July", "attendance": "3,000,000+",
     "type": "Modern/Fun", "description": "Mud wrestling, mud sliding, and cosmetic mud baths."},
    {"name": "Up Helly Aa", "city": "Lerwick", "country": "UK",
     "lat": 60.1550, "lon": -1.1450, "month": "January", "attendance": "10,000+",
     "type": "Viking Fire Festival", "description": "Torchlit procession and Viking galley burning in Shetland."},
    {"name": "Inti Raymi", "city": "Cusco", "country": "Peru",
     "lat": -13.5320, "lon": -71.9675, "month": "June 24", "attendance": "50,000+",
     "type": "Inca Ceremony", "description": "Recreation of Inca sun worship ceremony at solstice."},
    {"name": "Lantern Festival (Pingxi)", "city": "Pingxi", "country": "Taiwan",
     "lat": 25.0255, "lon": 121.7384, "month": "February", "attendance": "600,000+",
     "type": "Lantern Release", "description": "Thousands of sky lanterns released into the night."},
    {"name": "Reed Dance (Umhlanga)", "city": "Mbabane", "country": "Eswatini",
     "lat": -26.3054, "lon": 31.1367, "month": "Aug-Sep", "attendance": "80,000+",
     "type": "Royal Ceremony", "description": "Swazi reed dance ceremony with thousands of maidens."},
    {"name": "Paro Tsechu", "city": "Paro", "country": "Bhutan",
     "lat": 27.4286, "lon": 89.4164, "month": "Mar-Apr", "attendance": "30,000+",
     "type": "Buddhist Ceremony", "description": "Masked sacred dance festival at Paro Dzong monastery."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 9. ART & CULTURAL EVENTS
# ══════════════════════════════════════════════════════════════════════════════
"Art & Cultural Events": [
    {"name": "Venice Biennale", "city": "Venice", "country": "Italy",
     "lat": 45.4294, "lon": 12.3567, "month": "Apr-Nov", "attendance": "600,000+",
     "type": "Art Biennale", "description": "Prestigious international art exhibition with national pavilions."},
    {"name": "Art Basel (Basel)", "city": "Basel", "country": "Switzerland",
     "lat": 47.5596, "lon": 7.5886, "month": "June", "attendance": "100,000+",
     "type": "Art Fair", "description": "World's premier modern and contemporary art fair."},
    {"name": "Art Basel (Miami Beach)", "city": "Miami Beach", "country": "USA",
     "lat": 25.7907, "lon": -80.1300, "month": "December", "attendance": "83,000+",
     "type": "Art Fair", "description": "Americas edition of Art Basel with satellite fairs."},
    {"name": "Art Basel (Hong Kong)", "city": "Hong Kong", "country": "China",
     "lat": 22.3193, "lon": 114.1694, "month": "March", "attendance": "88,000+",
     "type": "Art Fair", "description": "Asia's leading international art fair."},
    {"name": "Documenta", "city": "Kassel", "country": "Germany",
     "lat": 51.3127, "lon": 9.4797, "month": "Jun-Sep (every 5 yr)", "attendance": "900,000+",
     "type": "Contemporary Art", "description": "Major exhibition of modern and contemporary art."},
    {"name": "Edinburgh Fringe Festival", "city": "Edinburgh", "country": "UK",
     "lat": 55.9533, "lon": -3.1883, "month": "August", "attendance": "3,500,000+",
     "type": "Performing Arts", "description": "World's largest arts festival with theatre, comedy, music."},
    {"name": "Vivid Sydney", "city": "Sydney", "country": "Australia",
     "lat": -33.8568, "lon": 151.2153, "month": "May-Jun", "attendance": "2,500,000+",
     "type": "Light & Art", "description": "Light projections on the Opera House and harbour installations."},
    {"name": "Fete des Lumieres", "city": "Lyon", "country": "France",
     "lat": 45.7640, "lon": 4.8357, "month": "December", "attendance": "4,000,000+",
     "type": "Light Festival", "description": "Four-night festival transforming Lyon's buildings with light art."},
    {"name": "Amsterdam Light Festival", "city": "Amsterdam", "country": "Netherlands",
     "lat": 52.3676, "lon": 4.9041, "month": "Nov-Jan", "attendance": "750,000+",
     "type": "Light Art", "description": "Light art installations along Amsterdam's canals."},
    {"name": "Sao Paulo Bienal", "city": "Sao Paulo", "country": "Brazil",
     "lat": -23.5870, "lon": -46.6568, "month": "Sep-Dec (even years)", "attendance": "700,000+",
     "type": "Art Biennale", "description": "Second-oldest art biennale in the world."},
    {"name": "Nuit Blanche (White Night)", "city": "Paris", "country": "France",
     "lat": 48.8566, "lon": 2.3522, "month": "October", "attendance": "2,000,000+",
     "type": "All-Night Art", "description": "Overnight art event where galleries and streets come alive."},
    {"name": "Sculpture by the Sea", "city": "Sydney", "country": "Australia",
     "lat": -33.8915, "lon": 151.2767, "month": "October", "attendance": "500,000+",
     "type": "Outdoor Sculpture", "description": "World's largest free outdoor sculpture exhibition."},
    {"name": "Signal Festival", "city": "Prague", "country": "Czech Republic",
     "lat": 50.0755, "lon": 14.4378, "month": "October", "attendance": "300,000+",
     "type": "Light Art", "description": "Light and new media art across Prague's historic centre."},
    {"name": "Kobe Luminarie", "city": "Kobe", "country": "Japan",
     "lat": 34.6901, "lon": 135.1956, "month": "December", "attendance": "4,000,000+",
     "type": "Light Memorial", "description": "Illumination honouring the 1995 earthquake victims."},
    {"name": "LUMA Arles", "city": "Arles", "country": "France",
     "lat": 43.6766, "lon": 4.6278, "month": "Year-round", "attendance": "300,000+",
     "type": "Art Center", "description": "Frank Gehry-designed arts centre with exhibitions."},
    {"name": "Ars Electronica", "city": "Linz", "country": "Austria",
     "lat": 48.3069, "lon": 14.2858, "month": "September", "attendance": "100,000+",
     "type": "Digital Art/Tech", "description": "Festival for art, technology and society."},
],

# ══════════════════════════════════════════════════════════════════════════════
# 10. SPORTING EVENTS CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
"Sporting Events Calendar": [
    {"name": "Summer Olympics 2024", "city": "Paris", "country": "France",
     "lat": 48.8566, "lon": 2.3522, "month": "Jul-Aug 2024", "attendance": "10,000,000+",
     "type": "Olympics", "description": "XXXIII Olympiad in Paris with Seine ceremony."},
    {"name": "Summer Olympics 2028", "city": "Los Angeles", "country": "USA",
     "lat": 34.0522, "lon": -118.2437, "month": "Jul-Aug 2028", "attendance": "TBD",
     "type": "Olympics", "description": "XXXIV Olympiad returning to LA for the third time."},
    {"name": "Summer Olympics 2032", "city": "Brisbane", "country": "Australia",
     "lat": -27.4698, "lon": 153.0251, "month": "Jul-Aug 2032", "attendance": "TBD",
     "type": "Olympics", "description": "XXXV Olympiad in Queensland, Australia."},
    {"name": "FIFA World Cup 2026", "city": "USA/Canada/Mexico", "country": "USA",
     "lat": 40.7128, "lon": -74.0060, "month": "Jun-Jul 2026", "attendance": "5,000,000+",
     "type": "Football (Soccer)", "description": "First 48-team World Cup across three nations."},
    {"name": "Tour de France", "city": "Paris (finish)", "country": "France",
     "lat": 48.8738, "lon": 2.2950, "month": "July (annual)", "attendance": "12,000,000+",
     "type": "Cycling", "description": "World's most prestigious cycling race finishing on Champs-Elysees."},
    {"name": "Super Bowl", "city": "Various (annual)", "country": "USA",
     "lat": 25.9580, "lon": -80.2389, "month": "February", "attendance": "70,000+",
     "type": "American Football", "description": "NFL championship game, most-watched US broadcast annually."},
    {"name": "Wimbledon", "city": "London", "country": "UK",
     "lat": 51.4340, "lon": -0.2143, "month": "Jun-Jul (annual)", "attendance": "500,000+",
     "type": "Tennis", "description": "Oldest and most prestigious tennis tournament since 1877."},
    {"name": "Boston Marathon", "city": "Boston", "country": "USA",
     "lat": 42.3601, "lon": -71.0589, "month": "April (annual)", "attendance": "500,000+",
     "type": "Marathon", "description": "World's oldest annual marathon since 1897."},
    {"name": "Tokyo Marathon", "city": "Tokyo", "country": "Japan",
     "lat": 35.6762, "lon": 139.6503, "month": "March (annual)", "attendance": "1,000,000+",
     "type": "Marathon", "description": "One of the World Marathon Majors through Tokyo's streets."},
    {"name": "The Masters (Augusta)", "city": "Augusta", "country": "USA",
     "lat": 33.5032, "lon": -82.0205, "month": "April (annual)", "attendance": "45,000+",
     "type": "Golf", "description": "Most prestigious golf major at Augusta National."},
    {"name": "Le Mans 24 Hours", "city": "Le Mans", "country": "France",
     "lat": 47.9562, "lon": 0.2074, "month": "June (annual)", "attendance": "250,000+",
     "type": "Motorsport", "description": "World's oldest active endurance racing event since 1923."},
    {"name": "Monaco Grand Prix", "city": "Monte Carlo", "country": "Monaco",
     "lat": 43.7347, "lon": 7.4206, "month": "May (annual)", "attendance": "200,000+",
     "type": "Formula 1", "description": "Most prestigious F1 race through Monte Carlo streets."},
    {"name": "The Ashes", "city": "London (Lord's)", "country": "UK",
     "lat": 51.5294, "lon": -0.1727, "month": "Varies (biennial)", "attendance": "500,000+",
     "type": "Cricket", "description": "Historic cricket test series between England and Australia."},
    {"name": "Rugby World Cup 2027", "city": "Various", "country": "Australia",
     "lat": -33.8688, "lon": 151.2093, "month": "Oct-Nov 2027", "attendance": "2,000,000+",
     "type": "Rugby", "description": "Rugby union's premier international competition."},
    {"name": "Winter Olympics 2026", "city": "Milan-Cortina", "country": "Italy",
     "lat": 45.4642, "lon": 9.1900, "month": "Feb 2026", "attendance": "1,500,000+",
     "type": "Winter Olympics", "description": "XXV Winter Games across Milan and Cortina d'Ampezzo."},
    {"name": "Cricket World Cup", "city": "Various", "country": "International",
     "lat": 28.6139, "lon": 77.2090, "month": "Varies (quadrennial)", "attendance": "1,000,000+",
     "type": "Cricket", "description": "ICC Cricket World Cup with 10+ competing nations."},
],

}  # End of FESTIVAL_DATA


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _safe(text) -> str:
    """HTML-escape user data for safe Folium popup rendering."""
    if text is None:
        return ""
    return escape(str(text))


def _build_popup(festival: dict, color: str) -> str:
    """Build an HTML popup for a festival marker, escaping all data fields."""
    name = _safe(festival.get("name", "Unknown"))
    city = _safe(festival.get("city", ""))
    country = _safe(festival.get("country", ""))
    month = _safe(festival.get("month", ""))
    attendance = _safe(festival.get("attendance", ""))
    ftype = _safe(festival.get("type", ""))
    desc = _safe(festival.get("description", ""))

    return (
        f'<div style="min-width:200px; max-width:280px; font-family:Arial,sans-serif;">'
        f'<div style="font-weight:700; font-size:0.95rem; color:{color}; '
        f'margin-bottom:4px;">{name}</div>'
        f'<div style="font-size:0.8rem; color:#555; margin-bottom:6px;">'
        f'{city}, {country}</div>'
        f'<table style="font-size:0.78rem; border-collapse:collapse; width:100%;">'
        f'<tr><td style="color:#888; padding:2px 6px 2px 0;">When</td>'
        f'<td style="padding:2px 0;">{month}</td></tr>'
        f'<tr><td style="color:#888; padding:2px 6px 2px 0;">Type</td>'
        f'<td style="padding:2px 0;">{ftype}</td></tr>'
        f'<tr><td style="color:#888; padding:2px 6px 2px 0;">Attendance</td>'
        f'<td style="padding:2px 0;">{attendance}</td></tr>'
        f'</table>'
        f'<div style="font-size:0.75rem; color:#666; margin-top:6px; '
        f'border-top:1px solid #ddd; padding-top:4px;">{desc}</div>'
        f'</div>'
    )


def _build_dataframe(festivals: list) -> pd.DataFrame:
    """Convert a list of festival dicts into a clean DataFrame."""
    rows = []
    for f in festivals:
        rows.append({
            "Festival": f.get("name", ""),
            "City": f.get("city", ""),
            "Country": f.get("country", ""),
            "Month": f.get("month", ""),
            "Type": f.get("type", ""),
            "Attendance": f.get("attendance", ""),
            "Latitude": f.get("lat", 0.0),
            "Longitude": f.get("lon", 0.0),
            "Description": f.get("description", ""),
        })
    return pd.DataFrame(rows)


def _build_csv(df: pd.DataFrame) -> str:
    """Export DataFrame to CSV string."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def _compute_stats(festivals: list) -> dict:
    """Compute summary statistics from a list of festival dicts."""
    countries = set()
    types = {}
    continents_approx = {
        "N. America": 0, "S. America": 0, "Europe": 0,
        "Africa": 0, "Asia": 0, "Oceania": 0,
    }

    for f in festivals:
        countries.add(f.get("country", "Unknown"))
        t = f.get("type", "Other")
        types[t] = types.get(t, 0) + 1

        lat = f.get("lat", 0)
        lon = f.get("lon", 0)
        if lat > 10 and -170 < lon < -25:
            continents_approx["N. America"] += 1
        elif lat <= 10 and -85 < lon < -30:
            continents_approx["S. America"] += 1
        elif 35 < lat < 72 and -25 < lon < 45:
            continents_approx["Europe"] += 1
        elif lat < 35 and 15 < lon < 55 and lat > -40:
            continents_approx["Africa"] += 1
        elif -15 < lat < 72 and 45 < lon < 180:
            continents_approx["Asia"] += 1
        elif lat < -10 and lon > 100:
            continents_approx["Oceania"] += 1
        else:
            continents_approx["Europe"] += 1

    top_type = max(types, key=types.get) if types else "N/A"
    top_continent = max(continents_approx, key=continents_approx.get)

    return {
        "total": len(festivals),
        "countries": len(countries),
        "types": len(types),
        "top_type": top_type,
        "top_continent": top_continent,
        "continents": continents_approx,
    }


def _folium_icon_color(hex_color: str) -> str:
    """Map accent hex colour to a Folium built-in icon colour name."""
    mapping = {
        ACCENT_PINK:    "darkred",
        ACCENT_RED:     "red",
        ACCENT_ROSE:    "darkred",
        ACCENT_VIOLET:  "purple",
        ACCENT_AMBER:   "orange",
        ACCENT_ORANGE:  "orange",
        ACCENT_EMERALD: "green",
        ACCENT_TEAL:    "green",
        ACCENT_BLUE:    "blue",
        ACCENT_CYAN:    "cadetblue",
    }
    return mapping.get(hex_color, "cadetblue")


def _create_map(festivals: list, mode: str) -> folium.Map:
    """Create a Folium map with festival markers on CartoDB dark_matter."""
    color = MODE_COLORS.get(mode, ACCENT_CYAN)
    icon_name = MODE_ICONS.get(mode, "info-sign")
    folium_color = _folium_icon_color(color)

    if festivals:
        avg_lat = sum(f["lat"] for f in festivals) / len(festivals)
        avg_lon = sum(f["lon"] for f in festivals) / len(festivals)
    else:
        avg_lat, avg_lon = 20.0, 0.0

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )

    for f in festivals:
        popup_html = _build_popup(f, color)
        folium.Marker(
            location=[f["lat"], f["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=_safe(f.get("name", "")),
            icon=folium.Icon(
                color=folium_color,
                icon=icon_name,
                prefix="glyphicon",
            ),
        ).add_to(m)

    return m


def _create_distribution_chart(stats: dict, mode: str):
    """Create a matplotlib horizontal bar chart of continent distribution."""
    continents = stats.get("continents", {})
    data = {k: v for k, v in continents.items() if v > 0}
    if not data:
        return None

    color = MODE_COLORS.get(mode, ACCENT_CYAN)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_facecolor(BG_PRIMARY)
    ax.set_facecolor(BG_SURFACE)

    names = list(data.keys())
    values = list(data.values())

    bars = ax.barh(range(len(names)), values, color=color, alpha=0.8, height=0.6)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color=TEXT_SECONDARY, fontsize=9)
    ax.set_xlabel("Number of Festivals", color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=9)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", color=TEXT_PRIMARY, fontsize=9, fontweight="bold")

    ax.grid(True, axis="x", color=BORDER, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.invert_yaxis()
    fig.tight_layout()
    return fig


def _create_type_chart(festivals: list, mode: str):
    """Create a matplotlib pie chart of festival types."""
    types = {}
    for f in festivals:
        t = f.get("type", "Other")
        types[t] = types.get(t, 0) + 1
    if not types:
        return None

    base_colors = [
        ACCENT_CYAN, ACCENT_PINK, ACCENT_VIOLET, ACCENT_AMBER, ACCENT_EMERALD,
        ACCENT_RED, ACCENT_ORANGE, ACCENT_BLUE, ACCENT_TEAL, ACCENT_ROSE,
    ]

    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor(BG_PRIMARY)
    ax.set_facecolor(BG_PRIMARY)

    labels = list(types.keys())
    sizes = list(types.values())
    colors_list = base_colors[:len(labels)]
    while len(colors_list) < len(labels):
        colors_list.append(TEXT_MUTED)

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct="%1.0f%%",
        colors=colors_list, startangle=90,
        pctdistance=0.82,
        wedgeprops={"edgecolor": BG_PRIMARY, "linewidth": 2},
    )

    for t in autotexts:
        t.set_color(TEXT_PRIMARY)
        t.set_fontsize(8)
        t.set_fontweight("bold")

    ax.legend(
        wedges, [f"{lab} ({s})" for lab, s in zip(labels, sizes)],
        loc="center left", bbox_to_anchor=(1.0, 0.5),
        fontsize=7.5, frameon=False,
        labelcolor=TEXT_SECONDARY,
    )

    ax.set_title("Festival Types", color=TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=10)
    fig.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# ENRICHMENT — optional Overpass API venue search
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _fetch_nearby_venues(lat: float, lon: float, radius_m: int = 5000) -> list:
    """
    Fetch nearby event venues, theatres and stadiums from Overpass API.
    Returns a list of dicts with name, type, lat, lon.
    """
    import requests as _req

    query = f"""
[out:json][timeout:30];
(
  node["amenity"="theatre"](around:{radius_m},{lat},{lon});
  node["amenity"="events_venue"](around:{radius_m},{lat},{lon});
  node["leisure"="stadium"](around:{radius_m},{lat},{lon});
  node["tourism"="attraction"](around:{radius_m},{lat},{lon});
  way["amenity"="theatre"](around:{radius_m},{lat},{lon});
  way["leisure"="stadium"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]
    for server in servers:
        try:
            resp = _req.post(server, data={"data": query}, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                venues = []
                node_lookup = {}
                for el in data.get("elements", []):
                    if el.get("type") == "node" and "lat" in el:
                        node_lookup[el["id"]] = (el["lat"], el["lon"])

                for el in data.get("elements", []):
                    tags = el.get("tags", {})
                    if not tags:
                        continue
                    vlat, vlon = None, None
                    if el.get("type") == "node" and "lat" in el:
                        vlat, vlon = el["lat"], el["lon"]
                    elif el.get("type") == "way":
                        nodes = el.get("nodes", [])
                        coords = [node_lookup[n] for n in nodes if n in node_lookup]
                        if coords:
                            vlat = sum(c[0] for c in coords) / len(coords)
                            vlon = sum(c[1] for c in coords) / len(coords)
                    if vlat is None:
                        continue
                    vtype = (tags.get("amenity") or tags.get("leisure")
                             or tags.get("tourism") or "venue")
                    venues.append({
                        "name": tags.get("name", tags.get("name:en", "Unnamed Venue")),
                        "type": vtype,
                        "lat": vlat,
                        "lon": vlon,
                    })
                return venues
        except Exception:
            continue
    return []


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def render_festival_maps_tab():
    """Main render function for the Festivals & World Events tab."""

    # ── Tab Header ──
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f3aa Festivals & World Events</h4>'
        '<p>Carnivals, cultural festivals, world fairs, celebrations & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 1 — Mode Selection
    # ══════════════════════════════════════════
    st.markdown("#### Select Festival Category")

    col_mode, col_filter = st.columns([2, 1])

    with col_mode:
        selected_mode = st.selectbox(
            "Map Mode",
            MAP_MODES,
            key="fest_mode",
            help="Choose from 10 curated festival categories to explore on the map.",
        )

    with col_filter:
        country_filter = st.text_input(
            "Filter by Country (optional)",
            value="",
            key="fest_country_filter",
            help="Type a country name to filter the festival list.",
        )

    # Mode description panel
    desc = MODE_DESCRIPTIONS.get(selected_mode, "")
    mode_color = MODE_COLORS.get(selected_mode, ACCENT_CYAN)
    st.markdown(
        f'<div style="background:{BG_CARD}; border-left:4px solid {mode_color}; '
        f'padding:12px 16px; border-radius:8px; margin:8px 0 16px 0;">'
        f'<span style="color:{TEXT_PRIMARY}; font-size:0.9rem;">{escape(desc)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 2 — Load and Filter Data
    # ══════════════════════════════════════════
    festivals = list(FESTIVAL_DATA.get(selected_mode, []))

    if country_filter.strip():
        query = country_filter.strip().lower()
        festivals = [f for f in festivals if query in f.get("country", "").lower()]

    if not festivals:
        st.warning("No festivals found matching your filter. Try a different country or clear the filter.")
        return

    # ══════════════════════════════════════════
    # SECTION 3 — Statistics
    # ══════════════════════════════════════════
    stats = _compute_stats(festivals)

    st.markdown("---")
    st.markdown("#### Overview")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Festivals", stats["total"])
    with c2:
        st.metric("Countries", stats["countries"])
    with c3:
        st.metric("Festival Types", stats["types"])
    with c4:
        st.metric("Top Type", stats["top_type"])
    with c5:
        st.metric("Top Region", stats["top_continent"])

    # ══════════════════════════════════════════
    # SECTION 4 — Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Festival Map")

    legend_html = (
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; '
        f'margin-bottom:0.5rem; align-items:center;">'
        f'<span style="color:{mode_color}; font-size:0.85rem; font-weight:600;">'
        f'\u25cf {escape(selected_mode)}</span>'
        f'<span style="color:{TEXT_MUTED}; font-size:0.78rem;">'
        f'({stats["total"]} festivals in {stats["countries"]} countries)</span>'
        f'</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)

    m = _create_map(festivals, selected_mode)
    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 5 — Charts & Festival Cards
    # ══════════════════════════════════════════
    st.markdown("---")

    col_chart, col_cards = st.columns([1, 1])

    with col_chart:
        st.markdown("#### Geographic Distribution")
        fig_dist = _create_distribution_chart(stats, selected_mode)
        if fig_dist is not None:
            st.pyplot(fig_dist)
            plt.close(fig_dist)
        else:
            st.info("No geographic distribution data available.")

        st.markdown("#### Type Breakdown")
        fig_type = _create_type_chart(festivals, selected_mode)
        if fig_type is not None:
            st.pyplot(fig_type)
            plt.close(fig_type)

    with col_cards:
        st.markdown("#### Featured Festivals")

        for f in festivals[:12]:
            name_safe = escape(f.get("name", ""))
            city_safe = escape(f.get("city", ""))
            country_safe = escape(f.get("country", ""))
            month_safe = escape(f.get("month", ""))
            att_safe = escape(f.get("attendance", ""))
            desc_safe = escape(f.get("description", "")[:120])

            st.markdown(
                f'<div style="display:flex; align-items:flex-start; margin-bottom:0.6rem; '
                f'padding:8px 10px; background:{BG_CARD}; border-radius:8px; '
                f'border-left:3px solid {mode_color};">'
                f'<div style="flex:1;">'
                f'<div style="color:{TEXT_PRIMARY}; font-weight:600; font-size:0.85rem;">'
                f'{name_safe}</div>'
                f'<div style="color:{TEXT_SECONDARY}; font-size:0.75rem;">'
                f'{city_safe}, {country_safe} &bull; {month_safe}</div>'
                f'<div style="color:{TEXT_MUTED}; font-size:0.7rem; margin-top:2px;">'
                f'{desc_safe}</div>'
                f'<div style="color:{mode_color}; font-size:0.7rem; margin-top:2px;">'
                f'Attendance: {att_safe}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════
    # SECTION 6 — Nearby Venues (Overpass API)
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Explore Festival Venues Nearby")
    st.markdown(
        f'<span style="color:{TEXT_MUTED}; font-size:0.8rem;">'
        'Select a festival to discover nearby event venues, theatres, and '
        'attractions via OpenStreetMap.</span>',
        unsafe_allow_html=True,
    )

    festival_names = [f"{f['name']} ({f['city']})" for f in festivals]
    selected_festival_idx = st.selectbox(
        "Select a Festival",
        range(len(festival_names)),
        format_func=lambda i: festival_names[i],
        key="fest_venue_select",
    )

    col_venue_btn, col_venue_radius = st.columns([1, 1])
    with col_venue_radius:
        venue_radius = st.slider("Search Radius (km)", 1, 20, 5, key="fest_venue_radius")
    with col_venue_btn:
        search_venues = st.button(
            "Search Nearby Venues",
            key="fest_venue_search",
        )

    if search_venues:
        sel_fest = festivals[selected_festival_idx]
        with st.spinner(f"Searching venues near {sel_fest['name']}..."):
            venues = _fetch_nearby_venues(
                sel_fest["lat"], sel_fest["lon"], venue_radius * 1000,
            )

        if venues:
            st.success(f"Found {len(venues)} nearby venue(s).")

            vc1, vc2, vc3 = st.columns(3)
            venue_types = {}
            for v in venues:
                vt = v.get("type", "other")
                venue_types[vt] = venue_types.get(vt, 0) + 1
            with vc1:
                st.metric("Venues Found", len(venues))
            with vc2:
                st.metric("Venue Types", len(venue_types))
            with vc3:
                top_vt = max(venue_types, key=venue_types.get) if venue_types else "N/A"
                st.metric("Most Common", top_vt.replace("_", " ").title())

            vm = folium.Map(
                location=[sel_fest["lat"], sel_fest["lon"]],
                zoom_start=14,
                tiles="CartoDB dark_matter",
            )

            folium.Marker(
                location=[sel_fest["lat"], sel_fest["lon"]],
                popup=folium.Popup(
                    _build_popup(sel_fest, mode_color), max_width=300,
                ),
                tooltip=_safe(sel_fest["name"]),
                icon=folium.Icon(color="red", icon="star", prefix="glyphicon"),
            ).add_to(vm)

            folium.Circle(
                location=[sel_fest["lat"], sel_fest["lon"]],
                radius=venue_radius * 1000,
                color=ACCENT_CYAN,
                fill=True,
                fill_opacity=0.05,
                weight=1,
            ).add_to(vm)

            for v in venues:
                venue_popup = (
                    f'<div style="min-width:160px;">'
                    f'<strong>{_safe(v["name"])}</strong><br/>'
                    f'<span style="font-size:0.8rem; color:#888;">'
                    f'{_safe(v["type"].replace("_", " ").title())}</span>'
                    f'</div>'
                )
                folium.CircleMarker(
                    location=[v["lat"], v["lon"]],
                    radius=6,
                    color=ACCENT_CYAN,
                    fill=True,
                    fill_color=ACCENT_CYAN,
                    fill_opacity=0.7,
                    weight=2,
                    popup=folium.Popup(venue_popup, max_width=200),
                    tooltip=_safe(v["name"]),
                ).add_to(vm)

            components.html(vm._repr_html_(), height=500)

            venue_df = pd.DataFrame([
                {
                    "Name": v["name"],
                    "Type": v["type"].replace("_", " ").title(),
                    "Latitude": round(v["lat"], 5),
                    "Longitude": round(v["lon"], 5),
                }
                for v in venues
            ])
            with st.expander(f"Venue Data ({len(venues)} results)", expanded=False):
                st.dataframe(venue_df, width="stretch", hide_index=True)

            venue_csv = _build_csv(venue_df)
            st.download_button(
                f"Download {len(venues)} Venues (CSV)",
                data=venue_csv,
                file_name=f"festival_venues_{_safe(sel_fest['city']).replace(' ', '_')}.csv",
                mime="text/csv",
                key="fest_venue_download",
            )
        else:
            st.info(
                "No nearby venues found via OpenStreetMap. "
                "Try a larger radius or a different festival location."
            )

    # ══════════════════════════════════════════
    # SECTION 7 — Full Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Full Festival Data")

    df = _build_dataframe(festivals)

    with st.expander(f"Festival Data Table ({len(df)} festivals)", expanded=True):
        st.dataframe(df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 8 — CSV Download
    # ══════════════════════════════════════════
    csv_data = _build_csv(df)
    mode_slug = selected_mode.lower().replace(" ", "_").replace("&", "and").replace("'", "")
    st.download_button(
        f"Download {len(df)} Festivals (CSV)",
        data=csv_data,
        file_name=f"terrascout_{mode_slug}.csv",
        mime="text/csv",
        key="fest_main_download",
    )

    # ══════════════════════════════════════════
    # SECTION 9 — Cross-Mode Comparison
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Cross-Category Comparison")
    st.markdown(
        f'<span style="color:{TEXT_MUTED}; font-size:0.8rem;">'
        'Compare festival counts and geographic spread across all 10 categories.</span>',
        unsafe_allow_html=True,
    )

    if st.button("Show Comparison", key="fest_compare_btn"):
        comparison_rows = []
        for mode_name in MAP_MODES:
            mode_data = FESTIVAL_DATA.get(mode_name, [])
            mode_stats = _compute_stats(mode_data)
            comparison_rows.append({
                "Category": mode_name,
                "Festivals": mode_stats["total"],
                "Countries": mode_stats["countries"],
                "Types": mode_stats["types"],
                "Top Region": mode_stats["top_continent"],
                "Top Type": mode_stats["top_type"],
            })

        comp_df = pd.DataFrame(comparison_rows)
        st.dataframe(comp_df, width="stretch", hide_index=True)

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(BG_PRIMARY)
        ax.set_facecolor(BG_SURFACE)

        categories = [r["Category"][:20] for r in comparison_rows]
        fest_counts = [r["Festivals"] for r in comparison_rows]
        country_counts = [r["Countries"] for r in comparison_rows]
        colors = [MODE_COLORS.get(r["Category"], ACCENT_CYAN) for r in comparison_rows]

        x = range(len(categories))
        width = 0.35

        bars1 = ax.bar([i - width / 2 for i in x], fest_counts, width,
                       color=colors, alpha=0.85, label="Festivals")
        bars2 = ax.bar([i + width / 2 for i in x], country_counts, width,
                       color=colors, alpha=0.45, label="Countries")

        ax.set_xticks(list(x))
        ax.set_xticklabels(categories, color=TEXT_SECONDARY, fontsize=7.5, rotation=35, ha="right")
        ax.set_ylabel("Count", color=TEXT_SECONDARY, fontsize=10)
        ax.tick_params(axis="y", colors=TEXT_SECONDARY, labelsize=9)
        ax.legend(fontsize=9, facecolor=BG_CARD, edgecolor=BORDER, labelcolor=TEXT_SECONDARY)
        ax.grid(True, axis="y", color=BORDER, linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(BORDER)

        for bar in bars1:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.2, str(int(h)),
                    ha="center", va="bottom", color=TEXT_PRIMARY, fontsize=7.5, fontweight="bold")

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        comp_csv = _build_csv(comp_df)
        st.download_button(
            "Download Comparison (CSV)",
            data=comp_csv,
            file_name="terrascout_festival_comparison.csv",
            mime="text/csv",
            key="fest_compare_download",
        )

    # ── Footer ──
    st.markdown(
        f'<div style="text-align:center; color:{TEXT_MUTED}; font-size:0.75rem; '
        f'margin-top:24px; padding:12px 0; border-top:1px solid {BORDER};">'
        'Festival data curated from public sources. Venue data from OpenStreetMap (Overpass API). '
        'All APIs are free and require no API key.'
        '</div>',
        unsafe_allow_html=True,
    )
