# -*- coding: utf-8 -*-
"""
Markets & Bazaars Maps module for TerraScout AI.
Curated database of 200+ world markets, souks, bazaars, flea markets,
floating markets, fish markets, night markets, spice markets, Christmas
markets, stock exchanges, luxury shopping streets, and historic trading
posts displayed on interactive dark-themed Folium maps with stats and
CSV export.  No API keys required -- all data is curated/embedded.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module
import requests

# ══════════════════════════════════════════════════════════════════════════════
# THEME CONSTANTS  (TerraScout AI Glassmorphism)
# ══════════════════════════════════════════════════════════════════════════════
BG_PRIMARY = "#0a0e1a"
BG_SURFACE = "#111827"
BG_CARD = "#1a2235"
BORDER = "#2a3550"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"

ACCENT_CYAN = "#06b6d4"
ACCENT_PINK = "#ec4899"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"
ACCENT_TEAL = "#14b8a6"
ACCENT_ROSE = "#f43f5e"

# ══════════════════════════════════════════════════════════════════════════════
# 10 MAP MODES
# ══════════════════════════════════════════════════════════════════════════════
MAP_MODES = [
    "Grand Bazaars & Souks",
    "Famous Flea Markets",
    "Floating Markets",
    "Fish Markets",
    "Night Markets",
    "Spice Markets",
    "Christmas Markets",
    "Stock Exchanges",
    "Luxury Shopping Streets",
    "Historic Trading Posts",
]

MODE_COLORS = {
    "Grand Bazaars & Souks": ACCENT_AMBER,
    "Famous Flea Markets": ACCENT_ORANGE,
    "Floating Markets": ACCENT_CYAN,
    "Fish Markets": ACCENT_BLUE,
    "Night Markets": ACCENT_VIOLET,
    "Spice Markets": ACCENT_RED,
    "Christmas Markets": ACCENT_EMERALD,
    "Stock Exchanges": ACCENT_TEAL,
    "Luxury Shopping Streets": ACCENT_PINK,
    "Historic Trading Posts": ACCENT_ROSE,
}

MODE_DESCRIPTIONS = {
    "Grand Bazaars & Souks": (
        "Explore the world's legendary covered markets and souks -- from the "
        "Grand Bazaar of Istanbul with its 4,000 shops to the labyrinthine medinas "
        "of Marrakech and Fez, the bustling Khan el-Khalili of Cairo, and the "
        "ancient bazaars of Isfahan and Aleppo."
    ),
    "Famous Flea Markets": (
        "Discover the planet's best flea markets and antique havens. Portobello "
        "Road in London, the Marche aux Puces de Clignancourt in Paris, Berlin's "
        "Mauerpark, Rose Bowl in Pasadena, and vibrant weekend markets from "
        "Buenos Aires to Bangkok."
    ),
    "Floating Markets": (
        "Navigate the world's floating markets where goods are sold from boats "
        "on rivers, canals, and lakes. Thailand's Damnoen Saduak and Amphawa, "
        "Vietnam's Mekong Delta markets, Kashmir's Dal Lake, and Indonesia's "
        "Banjarmasin river bazaars."
    ),
    "Fish Markets": (
        "Tour the world's greatest fish markets -- from Tokyo's legendary Toyosu "
        "(formerly Tsukiji) and Sydney's Fish Market to Barcelona's La Boqueria, "
        "Seattle's Pike Place, and Bergen's historic Fisketorget. Fresh catches "
        "and centuries of maritime trade."
    ),
    "Night Markets": (
        "Experience the electric atmosphere of the world's best night markets. "
        "Taipei's Shilin and Raohe, Bangkok's Rot Fai, Marrakech's Jemaa el-Fnaa "
        "after dark, Hong Kong's Temple Street, and Richmond's summer night market."
    ),
    "Spice Markets": (
        "Inhale the aromas of the world's great spice bazaars. Istanbul's "
        "Egyptian Bazaar, Delhi's Khari Baoli (Asia's largest spice market), "
        "Zanzibar's legendary spice island, Dubai's Gold and Spice Souk, and "
        "the pepper markets of Kerala."
    ),
    "Christmas Markets": (
        "Wander through Europe's enchanting Christmas markets and beyond. "
        "Strasbourg's Christkindelsmaerik (est. 1570), Nuremberg's "
        "Christkindlesmarkt, Vienna's Rathausplatz, Prague's Old Town Square, "
        "and the magical Tivoli Gardens of Copenhagen."
    ),
    "Stock Exchanges": (
        "Map the world's major financial centres and stock exchanges. From the "
        "New York Stock Exchange on Wall Street and the London Stock Exchange "
        "to the Tokyo Stock Exchange, Shanghai, Mumbai's BSE, and the emerging "
        "digital trading hubs of the 21st century."
    ),
    "Luxury Shopping Streets": (
        "Stroll the world's most prestigious shopping boulevards. Fifth Avenue "
        "in New York, the Champs-Elysees in Paris, Via Montenapoleone in Milan, "
        "Ginza in Tokyo, Bond Street in London, and Rodeo Drive in Beverly Hills."
    ),
    "Historic Trading Posts": (
        "Trace the ancient routes of commerce. Hanseatic League cities along the "
        "Baltic, Silk Road caravanserais from Xi'an to Constantinople, East India "
        "Company outposts, fur trade forts in North America, and Phoenician "
        "trading colonies across the Mediterranean."
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 1. GRAND BAZAARS & SOUKS  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

GRAND_BAZAARS = [
    {"name": "Grand Bazaar", "city": "Istanbul", "country": "Turkey",
     "lat": 41.0106, "lon": 28.9684, "founded": 1461, "shops": 4000,
     "notes": "One of the oldest and largest covered markets in the world; 61 covered streets"},
    {"name": "Khan el-Khalili", "city": "Cairo", "country": "Egypt",
     "lat": 30.0477, "lon": 31.2627, "founded": 1382, "shops": 900,
     "notes": "Medieval-era souk in the heart of Islamic Cairo; coppersmiths and perfumers"},
    {"name": "Medina Souk", "city": "Marrakech", "country": "Morocco",
     "lat": 31.6295, "lon": -7.9811, "founded": 1070, "shops": 3000,
     "notes": "UNESCO-listed medina with labyrinthine alleys; leather, spices, textiles"},
    {"name": "Jemaa el-Fnaa", "city": "Marrakech", "country": "Morocco",
     "lat": 31.6258, "lon": -7.9891, "founded": 1050, "shops": 1500,
     "notes": "UNESCO-listed main square; snake charmers, food stalls, storytellers at night"},
    {"name": "Bazaar of Isfahan", "city": "Isfahan", "country": "Iran",
     "lat": 32.6546, "lon": 51.6780, "founded": 1620, "shops": 2000,
     "notes": "Surrounds Naqsh-e Jahan Square; carpets, miniatures, metalwork"},
    {"name": "Bazaar of Tabriz", "city": "Tabriz", "country": "Iran",
     "lat": 38.0788, "lon": 46.2919, "founded": 1000, "shops": 5500,
     "notes": "UNESCO World Heritage; one of the oldest bazaars in the Middle East"},
    {"name": "Souq Waqif", "city": "Doha", "country": "Qatar",
     "lat": 25.2866, "lon": 51.5316, "founded": 1900, "shops": 600,
     "notes": "Restored traditional market; falcons, spices, textiles, pearl shops"},
    {"name": "Mutrah Souk", "city": "Muscat", "country": "Oman",
     "lat": 23.6169, "lon": 58.5702, "founded": 1507, "shops": 500,
     "notes": "Port-side souk with frankincense, silver, and Omani daggers (khanjar)"},
    {"name": "Fez Medina Souk", "city": "Fez", "country": "Morocco",
     "lat": 34.0622, "lon": -4.9736, "founded": 808, "shops": 9000,
     "notes": "World's largest car-free urban zone; tanneries, ceramics, woodworking"},
    {"name": "Chatuchak Weekend Market", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7999, "lon": 100.5530, "founded": 1942, "shops": 15000,
     "notes": "World's largest weekend market; 27 acres; 200,000 visitors per day"},
    {"name": "Camden Market", "city": "London", "country": "United Kingdom",
     "lat": 51.5414, "lon": -0.1467, "founded": 1974, "shops": 1000,
     "notes": "Iconic alternative market along Regent's Canal; vintage, food, crafts"},
    {"name": "Kapali Carsi (Covered Bazaar)", "city": "Bursa", "country": "Turkey",
     "lat": 40.1838, "lon": 29.0605, "founded": 1340, "shops": 800,
     "notes": "Oldest Ottoman bazaar; silk trade hub; precursor to Istanbul's Grand Bazaar"},
    {"name": "Al-Hamidiyah Souk", "city": "Damascus", "country": "Syria",
     "lat": 33.5115, "lon": 36.3063, "founded": 1780, "shops": 600,
     "notes": "Grand covered market leading to the Umayyad Mosque; Roman-era roots"},
    {"name": "Souq al-Mubarakiya", "city": "Kuwait City", "country": "Kuwait",
     "lat": 29.3761, "lon": 47.9785, "founded": 1900, "shops": 300,
     "notes": "Traditional market with dates, perfumes, and Kuwaiti handicrafts"},
    {"name": "Ben Thanh Market", "city": "Ho Chi Minh City", "country": "Vietnam",
     "lat": 10.7725, "lon": 106.6980, "founded": 1912, "shops": 1500,
     "notes": "Colonial-era central market; Vietnamese lacquerware, street food, fabrics"},
    {"name": "Central Market (Phsar Thmei)", "city": "Phnom Penh", "country": "Cambodia",
     "lat": 11.5692, "lon": 104.9210, "founded": 1937, "shops": 2000,
     "notes": "Art Deco dome structure; gems, textiles, and Khmer handicrafts"},
    {"name": "Chandni Chowk", "city": "Delhi", "country": "India",
     "lat": 28.6506, "lon": 77.2310, "founded": 1650, "shops": 5000,
     "notes": "Mughal-era bazaar street; wholesale markets for textiles, spices, electronics"},
    {"name": "Tehran Grand Bazaar", "city": "Tehran", "country": "Iran",
     "lat": 35.6722, "lon": 51.4220, "founded": 1500, "shops": 10000,
     "notes": "10 km of covered corridors; carpets, gold, spices; centre of 1979 revolution protests"},
    {"name": "Mercado de la Merced", "city": "Mexico City", "country": "Mexico",
     "lat": 19.4258, "lon": -99.1241, "founded": 1880, "shops": 3000,
     "notes": "Largest traditional market in the Americas; chiles, mole, fresh produce"},
    {"name": "Souq al-Hamidiyya", "city": "Aleppo", "country": "Syria",
     "lat": 36.1990, "lon": 37.1566, "founded": 1200, "shops": 1500,
     "notes": "UNESCO-listed medieval souk; heavily damaged in Syrian Civil War; under restoration"},
    {"name": "Deira Gold Souk", "city": "Dubai", "country": "UAE",
     "lat": 25.2677, "lon": 55.2960, "founded": 1940, "shops": 380,
     "notes": "World's largest gold market; 10 tonnes of gold on display at any time"},
    {"name": "Kashgar Sunday Market", "city": "Kashgar", "country": "China",
     "lat": 39.4677, "lon": 75.9898, "founded": 200, "shops": 2000,
     "notes": "Ancient Silk Road livestock and goods market; Uyghur culture hub"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 2. FAMOUS FLEA MARKETS  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

FLEA_MARKETS = [
    {"name": "Portobello Road Market", "city": "London", "country": "United Kingdom",
     "lat": 51.5157, "lon": -0.2050, "day": "Saturday", "specialty": "Antiques & vintage",
     "notes": "World-famous antiques market in Notting Hill; over 1,000 dealers"},
    {"name": "Marche aux Puces de Clignancourt", "city": "Paris", "country": "France",
     "lat": 48.8986, "lon": 2.3440, "day": "Sat-Mon", "specialty": "Antiques & furniture",
     "notes": "World's largest antique market; 7 sub-markets; 2,500+ stalls since 1885"},
    {"name": "Rose Bowl Flea Market", "city": "Pasadena", "country": "USA",
     "lat": 34.1613, "lon": -118.1676, "day": "2nd Sunday", "specialty": "Vintage & collectibles",
     "notes": "2,500 vendors in the Rose Bowl parking lot; iconic Southern California experience"},
    {"name": "Mauerpark Flohmarkt", "city": "Berlin", "country": "Germany",
     "lat": 52.5434, "lon": 13.4024, "day": "Sunday", "specialty": "Vintage & music",
     "notes": "Berlin's beloved Sunday flea market; famous open-air karaoke in the amphitheatre"},
    {"name": "El Rastro", "city": "Madrid", "country": "Spain",
     "lat": 40.4087, "lon": -3.7074, "day": "Sunday", "specialty": "Antiques & curios",
     "notes": "Madrid's legendary outdoor market since 1740; 3,500 stalls along Ribera de Curtidores"},
    {"name": "Brooklyn Flea", "city": "New York City", "country": "USA",
     "lat": 40.6961, "lon": -73.9897, "day": "Sat-Sun", "specialty": "Vintage & crafts",
     "notes": "Brooklyn's premier flea with curated vintage, artisanal food, and local crafts"},
    {"name": "IJ-Hallen", "city": "Amsterdam", "country": "Netherlands",
     "lat": 52.3918, "lon": 4.9076, "day": "Monthly", "specialty": "General flea",
     "notes": "Europe's largest flea market; 750 stalls in the NDSM Wharf warehouses"},
    {"name": "Feira da Ladra", "city": "Lisbon", "country": "Portugal",
     "lat": 38.7142, "lon": -9.1241, "day": "Tue & Sat", "specialty": "Antiques & bric-a-brac",
     "notes": "Lisbon's 'Thieves Market' since the 12th century; vintage tiles and books"},
    {"name": "San Telmo Antiques Fair", "city": "Buenos Aires", "country": "Argentina",
     "lat": -34.6215, "lon": -58.3711, "day": "Sunday", "specialty": "Antiques & tango",
     "notes": "Historic cobblestone market with tango dancers, antique silver, and art"},
    {"name": "Bermondsey Antiques Market", "city": "London", "country": "United Kingdom",
     "lat": 51.4990, "lon": -0.0803, "day": "Friday", "specialty": "High-end antiques",
     "notes": "Dealers-only dawn market; finest silverware, jewelry, and fine art"},
    {"name": "Chatuchak Weekend Market", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7999, "lon": 100.5530, "day": "Sat-Sun", "specialty": "Everything",
     "notes": "15,000 stalls; vintage clothing, handicrafts, pets, art, and street food"},
    {"name": "Monastiraki Flea Market", "city": "Athens", "country": "Greece",
     "lat": 37.9757, "lon": 23.7261, "day": "Daily (Sun best)", "specialty": "Antiques & crafts",
     "notes": "Ancient agora-adjacent market; handmade sandals, icons, vintage records"},
    {"name": "Brimfield Antique Show", "city": "Brimfield", "country": "USA",
     "lat": 42.1226, "lon": -72.1884, "day": "3x yearly", "specialty": "Antiques & vintage",
     "notes": "America's largest outdoor antiques show; 6,000 dealers across 23 fields"},
    {"name": "Marche aux Puces de Vanves", "city": "Paris", "country": "France",
     "lat": 48.8271, "lon": 2.3046, "day": "Sat-Sun", "specialty": "Vintage & curiosities",
     "notes": "Smaller, more local alternative to Clignancourt; genuine Parisian treasures"},
    {"name": "Naschmarkt Flea Market", "city": "Vienna", "country": "Austria",
     "lat": 48.1987, "lon": 16.3613, "day": "Saturday", "specialty": "Antiques & vinyl",
     "notes": "Vienna's beloved Saturday flea alongside the permanent Naschmarkt food market"},
    {"name": "Sungei Road Market", "city": "Singapore", "country": "Singapore",
     "lat": 1.3039, "lon": 103.8587, "day": "Daily (ended 2017)", "specialty": "Vintage & junk",
     "notes": "Singapore's legendary 'Thieves Market'; operated for 80+ years before closure"},
    {"name": "Encants Barcelona", "city": "Barcelona", "country": "Spain",
     "lat": 41.4006, "lon": 2.1880, "day": "Mon-Wed-Fri-Sat", "specialty": "Antiques & bargains",
     "notes": "14th-century flea market in a striking modern mirrored canopy building"},
    {"name": "Porta Portese", "city": "Rome", "country": "Italy",
     "lat": 41.8749, "lon": 12.4730, "day": "Sunday", "specialty": "Vintage & clothing",
     "notes": "Rome's legendary Sunday market along the Tiber; thousands of stalls since 1945"},
    {"name": "Camden Passage", "city": "London", "country": "United Kingdom",
     "lat": 51.5361, "lon": -0.1027, "day": "Wed & Sat", "specialty": "Antiques & art",
     "notes": "Islington's charming antiques quarter; silverware, jewelry, vintage prints"},
    {"name": "Springfield Antique Show", "city": "Springfield", "country": "USA",
     "lat": 39.9242, "lon": -83.8088, "day": "Monthly", "specialty": "Antiques & vintage",
     "notes": "Ohio's premier antique extravaganza; 2,500 booths across the fairgrounds"},
    {"name": "Jaffa Flea Market", "city": "Tel Aviv", "country": "Israel",
     "lat": 32.0530, "lon": 34.7522, "day": "Daily", "specialty": "Vintage & Judaica",
     "notes": "Bohemian market in old Jaffa; antique furniture, rugs, and artisan cafes"},
    {"name": "Ratchada Train Night Market", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7651, "lon": 100.5738, "day": "Thu-Sun", "specialty": "Vintage & street food",
     "notes": "Colourful tent market famous for Instagram-worthy aerial views"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 3. FLOATING MARKETS  (18 entries)
# ══════════════════════════════════════════════════════════════════════════════

FLOATING_MARKETS = [
    {"name": "Damnoen Saduak Floating Market", "city": "Ratchaburi", "country": "Thailand",
     "lat": 13.5181, "lon": 99.9582, "type": "River canal", "est": 1868,
     "notes": "Thailand's most famous floating market; fruit, souvenirs, boat rides on narrow canals"},
    {"name": "Amphawa Floating Market", "city": "Samut Songkhram", "country": "Thailand",
     "lat": 13.4252, "lon": 99.9529, "type": "River canal", "est": 1872,
     "notes": "Weekend evening market; seafood cooked on boats; firefly tours at night"},
    {"name": "Cai Rang Floating Market", "city": "Can Tho", "country": "Vietnam",
     "lat": 10.0131, "lon": 105.7450, "type": "River (Mekong)", "est": 1915,
     "notes": "Mekong Delta's largest wholesale floating market; pineapples, watermelons, produce"},
    {"name": "Cai Be Floating Market", "city": "Tien Giang", "country": "Vietnam",
     "lat": 10.3530, "lon": 105.9513, "type": "River (Mekong)", "est": 1890,
     "notes": "Wholesale fruit market at the confluence of rivers; French-colonial cathedral nearby"},
    {"name": "Dal Lake Floating Market", "city": "Srinagar", "country": "India",
     "lat": 34.1215, "lon": 74.8385, "type": "Lake", "est": 1900,
     "notes": "Early-morning shikara boat market on Dal Lake; vegetables, flowers, lotus roots"},
    {"name": "Taling Chan Floating Market", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7709, "lon": 100.4443, "type": "Canal (klong)", "est": 1987,
     "notes": "Local Thai weekend market; grilled seafood on boats; less touristy than Damnoen Saduak"},
    {"name": "Khlong Lat Mayom Floating Market", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7400, "lon": 100.4100, "type": "Canal (klong)", "est": 2004,
     "notes": "Authentic local market with orchid gardens; Thai desserts and snacks"},
    {"name": "Lok Baintan Floating Market", "city": "Banjarmasin", "country": "Indonesia",
     "lat": -3.3025, "lon": 114.5911, "type": "River (Barito)", "est": 1500,
     "notes": "Iconic Borneo dawn market; Banjar women in jukung canoes selling produce"},
    {"name": "Phong Dien Floating Market", "city": "Can Tho", "country": "Vietnam",
     "lat": 10.0581, "lon": 105.6522, "type": "River (Mekong)", "est": 1920,
     "notes": "Smaller, more authentic Mekong market; best visited at dawn"},
    {"name": "Tha Kha Floating Market", "city": "Samut Songkhram", "country": "Thailand",
     "lat": 13.4035, "lon": 99.9861, "type": "Canal (klong)", "est": 1950,
     "notes": "Tiny, tranquil coconut palm-lined canal market; weekends only"},
    {"name": "Tonle Sap Floating Village", "city": "Siem Reap", "country": "Cambodia",
     "lat": 13.2802, "lon": 103.8570, "type": "Lake", "est": 1500,
     "notes": "Entire floating community on Southeast Asia's largest lake; schools, shops, temples"},
    {"name": "Ganvie Stilt Village Market", "city": "Ganvie", "country": "Benin",
     "lat": 6.4253, "lon": 2.3484, "type": "Lake (Nokoue)", "est": 1600,
     "notes": "Africa's largest lake village; markets on pirogues; 30,000 inhabitants"},
    {"name": "Curacao Floating Market", "city": "Willemstad", "country": "Curacao",
     "lat": 12.1088, "lon": -68.9356, "type": "Harbor", "est": 1940,
     "notes": "Venezuelan traders sell tropical fruit from boats at the Punda waterfront"},
    {"name": "Ha Long Bay Floating Market", "city": "Ha Long", "country": "Vietnam",
     "lat": 20.9517, "lon": 107.0486, "type": "Bay", "est": 1900,
     "notes": "Small market boats ply UNESCO-listed Ha Long Bay among limestone karsts"},
    {"name": "Inle Lake Floating Market", "city": "Nyaungshwe", "country": "Myanmar",
     "lat": 20.5667, "lon": 96.9167, "type": "Lake", "est": 1890,
     "notes": "Rotating 5-day market among Intha leg-rowing fishers and floating gardens"},
    {"name": "Mercado Ver-o-Peso", "city": "Belem", "country": "Brazil",
     "lat": -1.4538, "lon": -48.5025, "type": "River dock", "est": 1688,
     "notes": "Amazonian riverside market; exotic fish, acai, medicinal herbs; oldest in Brazil"},
    {"name": "Haiphong Floating Market", "city": "Haiphong", "country": "Vietnam",
     "lat": 20.8568, "lon": 106.6822, "type": "River", "est": 1920,
     "notes": "Northern Vietnam river market with fresh seafood and limestone backdrop"},
    {"name": "Banjarmasin Floating Market", "city": "Banjarmasin", "country": "Indonesia",
     "lat": -3.3186, "lon": 114.5944, "type": "River (Martapura)", "est": 1526,
     "notes": "Kalimantan's central river market; traditional jukung boats at sunrise"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 4. FISH MARKETS  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

FISH_MARKETS = [
    {"name": "Toyosu Market (formerly Tsukiji)", "city": "Tokyo", "country": "Japan",
     "lat": 35.6455, "lon": 139.7820, "daily_tonnes": 1800, "specialty": "Tuna auctions",
     "notes": "World's largest wholesale fish market; famous tuna auctions at 5:30 am"},
    {"name": "La Boqueria", "city": "Barcelona", "country": "Spain",
     "lat": 41.3816, "lon": 2.1719, "daily_tonnes": 50, "specialty": "Mediterranean seafood",
     "notes": "Iconic market on La Rambla since 1217; fresh seafood, jamon, fruit"},
    {"name": "Pike Place Fish Market", "city": "Seattle", "country": "USA",
     "lat": 47.6097, "lon": -122.3425, "daily_tonnes": 25, "specialty": "Pacific salmon",
     "notes": "Famous fish-throwing tradition since 1930; overlooking Elliott Bay"},
    {"name": "Noryangjin Fish Market", "city": "Seoul", "country": "South Korea",
     "lat": 37.5133, "lon": 126.9401, "daily_tonnes": 300, "specialty": "Live seafood",
     "notes": "24-hour wholesale market; buy live fish and have it prepared upstairs"},
    {"name": "Sydney Fish Market", "city": "Sydney", "country": "Australia",
     "lat": -33.8712, "lon": 151.1936, "daily_tonnes": 55, "specialty": "Sydney rock oysters",
     "notes": "Southern hemisphere's largest fish market; Dutch clock auction system"},
    {"name": "Rialto Fish Market (Pescheria)", "city": "Venice", "country": "Italy",
     "lat": 45.4409, "lon": 12.3357, "daily_tonnes": 15, "specialty": "Adriatic seafood",
     "notes": "Gothic fish market at the foot of the Rialto Bridge since 1097"},
    {"name": "Fisketorget (Fish Market)", "city": "Bergen", "country": "Norway",
     "lat": 60.3943, "lon": 5.3259, "daily_tonnes": 10, "specialty": "Norwegian salmon & king crab",
     "notes": "Historic harbour-side market on Bryggen wharf since the 1200s"},
    {"name": "Mercado de Mariscos", "city": "Panama City", "country": "Panama",
     "lat": 8.9499, "lon": -79.5403, "daily_tonnes": 40, "specialty": "Ceviche & corvina",
     "notes": "Waterfront fish market with upstairs cevicheria; Pacific catch daily"},
    {"name": "Billingsgate Market", "city": "London", "country": "United Kingdom",
     "lat": 51.5075, "lon": -0.0105, "daily_tonnes": 150, "specialty": "North Sea fish",
     "notes": "London's premier wholesale fish market; open since 1699; moved to Canary Wharf 1982"},
    {"name": "Jagalchi Fish Market", "city": "Busan", "country": "South Korea",
     "lat": 35.0967, "lon": 129.0306, "daily_tonnes": 250, "specialty": "Live seafood",
     "notes": "South Korea's largest seafood market; seven-story building; sea-woman divers"},
    {"name": "Mercado Central", "city": "Santiago", "country": "Chile",
     "lat": -33.4350, "lon": -70.6500, "daily_tonnes": 60, "specialty": "Chilean sea bass",
     "notes": "Iron-framed 1872 building; caldillo de congrio (conger eel stew) praised by Neruda"},
    {"name": "Vieux-Port Fish Market", "city": "Marseille", "country": "France",
     "lat": 43.2952, "lon": 5.3739, "daily_tonnes": 20, "specialty": "Bouillabaisse fish",
     "notes": "Dawn fish sale on the Old Port quay; fishermen sell direct from boats"},
    {"name": "Makishi Public Market", "city": "Naha (Okinawa)", "country": "Japan",
     "lat": 26.2151, "lon": 127.6831, "daily_tonnes": 30, "specialty": "Tropical reef fish",
     "notes": "Okinawa's kitchen; colourful tropical fish, sea grapes, tofu, awamori"},
    {"name": "Mercado del Puerto", "city": "Montevideo", "country": "Uruguay",
     "lat": -34.9073, "lon": -56.2120, "daily_tonnes": 10, "specialty": "River plate catch",
     "notes": "1868 iron-frame market; now famous for parrilla (grill) restaurants"},
    {"name": "Deira Fish Market", "city": "Dubai", "country": "UAE",
     "lat": 25.2670, "lon": 55.3000, "daily_tonnes": 100, "specialty": "Hamour & kingfish",
     "notes": "Modern waterfront market opened 2017; traditional Gulf dhow fishing trade"},
    {"name": "Kauppatori (Market Square)", "city": "Helsinki", "country": "Finland",
     "lat": 60.1675, "lon": 24.9514, "daily_tonnes": 8, "specialty": "Baltic herring",
     "notes": "Harbour-side market square; annual Baltic Herring Market since 1743"},
    {"name": "Fulton Fish Market", "city": "New York City", "country": "USA",
     "lat": 40.8117, "lon": -73.8803, "daily_tonnes": 450, "specialty": "Atlantic seafood",
     "notes": "Moved to Hunts Point Bronx in 2005; supplies NYC's restaurants since 1822"},
    {"name": "Mercato del Pesce", "city": "Catania", "country": "Italy",
     "lat": 37.5025, "lon": 15.0881, "daily_tonnes": 20, "specialty": "Sicilian swordfish",
     "notes": "Raucous Sicilian fish market near Piazza Duomo; swordfish, tuna, sardines"},
    {"name": "Kadikoy Fish Market", "city": "Istanbul", "country": "Turkey",
     "lat": 40.9907, "lon": 29.0254, "daily_tonnes": 40, "specialty": "Black Sea anchovies",
     "notes": "Asian-side market in Istanbul; grilled fish sandwiches (balik ekmek)"},
    {"name": "Albert Cuyp Market", "city": "Amsterdam", "country": "Netherlands",
     "lat": 52.3556, "lon": 4.8945, "daily_tonnes": 12, "specialty": "Herring & kibbeling",
     "notes": "Amsterdam's most popular street market since 1905; raw herring stands"},
    {"name": "Mercado de San Miguel", "city": "Madrid", "country": "Spain",
     "lat": 40.4155, "lon": -3.7090, "daily_tonnes": 5, "specialty": "Galician seafood",
     "notes": "Restored 1916 iron-and-glass market; gourmet tapas and fresh shellfish"},
    {"name": "Curacao Floating Fish Market", "city": "Willemstad", "country": "Curacao",
     "lat": 12.1080, "lon": -68.9360, "daily_tonnes": 5, "specialty": "Caribbean reef fish",
     "notes": "Venezuelan fishermen sell catch from boats in Punda harbour"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 5. NIGHT MARKETS  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

NIGHT_MARKETS = [
    {"name": "Shilin Night Market", "city": "Taipei", "country": "Taiwan",
     "lat": 25.0880, "lon": 121.5241, "specialty": "Stinky tofu & bubble tea",
     "visitors": "1,000,000/month", "notes": "Taipei's largest and most famous night market since 1899"},
    {"name": "Raohe Street Night Market", "city": "Taipei", "country": "Taiwan",
     "lat": 25.0508, "lon": 121.5772, "specialty": "Pepper buns & medicinal stew",
     "visitors": "500,000/month", "notes": "Oldest night market in Taipei; ornate Ciyou Temple entrance"},
    {"name": "Patpong Night Market", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7310, "lon": 100.5340, "specialty": "Bargain goods & street food",
     "visitors": "200,000/month", "notes": "Famous Silom district night bazaar; clothing, accessories, souvenirs"},
    {"name": "Jemaa el-Fnaa (Evening)", "city": "Marrakech", "country": "Morocco",
     "lat": 31.6258, "lon": -7.9891, "specialty": "Tagine & grilled meats",
     "visitors": "1,500,000/month", "notes": "UNESCO square transforms at dusk into massive open-air restaurant"},
    {"name": "Richmond Night Market", "city": "Richmond BC", "country": "Canada",
     "lat": 49.1749, "lon": -123.1383, "specialty": "Asian street food",
     "visitors": "200,000/season", "notes": "North America's largest night market; 600+ booths; May-October"},
    {"name": "Temple Street Night Market", "city": "Hong Kong", "country": "China",
     "lat": 22.3048, "lon": 114.1708, "specialty": "Claypot rice & fortune tellers",
     "visitors": "800,000/month", "notes": "Kowloon's iconic night market; Cantonese opera, jade, electronics"},
    {"name": "Donghuamen Night Market", "city": "Beijing", "country": "China",
     "lat": 39.9136, "lon": 116.4077, "specialty": "Exotic skewers",
     "visitors": "300,000/month", "notes": "Wangfujing street market with scorpion, starfish, and centipede skewers"},
    {"name": "Rot Fai Market (Train Market)", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7651, "lon": 100.5738, "specialty": "Vintage collectibles & Thai food",
     "visitors": "400,000/month", "notes": "Retro-themed night market with vintage cars, vinyl, and craft beer"},
    {"name": "Ningxia Night Market", "city": "Taipei", "country": "Taiwan",
     "lat": 25.0554, "lon": 121.5153, "specialty": "Oyster omelettes & taro balls",
     "visitors": "350,000/month", "notes": "Foodie-favorite Taipei market; Michelin guide recommended stalls"},
    {"name": "Myeongdong Night Market", "city": "Seoul", "country": "South Korea",
     "lat": 37.5636, "lon": 126.9860, "specialty": "Korean fried chicken & tteokbokki",
     "visitors": "600,000/month", "notes": "Shopping district transforms at dusk with K-food street stalls"},
    {"name": "Covent Garden Night Market", "city": "London", "country": "United Kingdom",
     "lat": 51.5117, "lon": -0.1227, "specialty": "Artisan goods & street performers",
     "visitors": "400,000/month", "notes": "Historic market hall with evening craft and food events"},
    {"name": "Mercado Roma", "city": "Mexico City", "country": "Mexico",
     "lat": 19.4111, "lon": -99.1620, "specialty": "Gourmet Mexican street food",
     "visitors": "250,000/month", "notes": "Modern food hall with evening mezcal bars and live music"},
    {"name": "Jonker Street Night Market", "city": "Melaka", "country": "Malaysia",
     "lat": 2.1965, "lon": 102.2481, "specialty": "Nyonya cuisine & chicken rice balls",
     "visitors": "200,000/month", "notes": "Weekend night market in UNESCO-listed Chinatown; Peranakan heritage"},
    {"name": "Djemaa Night Market", "city": "Fez", "country": "Morocco",
     "lat": 34.0613, "lon": -4.9739, "specialty": "Pastilla & harira soup",
     "visitors": "100,000/month", "notes": "Fez medina evening food stalls near the tanneries"},
    {"name": "Fengjia Night Market", "city": "Taichung", "country": "Taiwan",
     "lat": 24.1790, "lon": 120.6466, "specialty": "Large sausage wrapping small sausage",
     "visitors": "600,000/month", "notes": "Taiwan's largest night market by area; near Feng Chia University"},
    {"name": "Asiatique The Riverfront", "city": "Bangkok", "country": "Thailand",
     "lat": 13.6999, "lon": 100.5016, "specialty": "Thai crafts & riverside dining",
     "visitors": "300,000/month", "notes": "Upscale night bazaar in renovated colonial-era warehouses on the Chao Phraya"},
    {"name": "Queen Victoria Night Market", "city": "Melbourne", "country": "Australia",
     "lat": -37.8075, "lon": 144.9565, "specialty": "Multicultural street food",
     "visitors": "350,000/season", "notes": "Summer Wednesday night market with food trucks, bars, and live music"},
    {"name": "Gwangjang Market", "city": "Seoul", "country": "South Korea",
     "lat": 37.5700, "lon": 126.9996, "specialty": "Bindaetteok & mayak gimbap",
     "visitors": "500,000/month", "notes": "Korea's oldest market (1905); Netflix Street Food featured; late-night dining"},
    {"name": "Khao San Road Night Market", "city": "Bangkok", "country": "Thailand",
     "lat": 13.7589, "lon": 100.4974, "specialty": "Pad Thai & scorpion snacks",
     "visitors": "300,000/month", "notes": "Backpacker mecca; street food, bars, and budget shopping after dark"},
    {"name": "Ben Thanh Night Market", "city": "Ho Chi Minh City", "country": "Vietnam",
     "lat": 10.7725, "lon": 106.6980, "specialty": "Pho & banh mi",
     "visitors": "200,000/month", "notes": "Evening stalls surround the main market; Vietnamese street food paradise"},
    {"name": "Namdaemun Night Market", "city": "Seoul", "country": "South Korea",
     "lat": 37.5593, "lon": 126.9778, "specialty": "Ginseng & hotteok",
     "visitors": "400,000/month", "notes": "600-year-old gate market; pre-dawn wholesale and evening street food"},
    {"name": "Luang Prabang Night Market", "city": "Luang Prabang", "country": "Laos",
     "lat": 19.8871, "lon": 102.1351, "specialty": "Hmong textiles & mulberry tea",
     "visitors": "100,000/month", "notes": "UNESCO town evening market on Sisavangvong Road; handwoven silk"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 6. SPICE MARKETS  (18 entries)
# ══════════════════════════════════════════════════════════════════════════════

SPICE_MARKETS = [
    {"name": "Spice Bazaar (Egyptian Bazaar)", "city": "Istanbul", "country": "Turkey",
     "lat": 41.0168, "lon": 28.9711, "est": 1664, "key_spice": "Saffron & sumac",
     "notes": "L-shaped covered bazaar near Galata Bridge; 85 shops; dates, lokum, dried fruits"},
    {"name": "Khari Baoli", "city": "Delhi", "country": "India",
     "lat": 28.6560, "lon": 77.2155, "est": 1650, "key_spice": "Chili & turmeric",
     "notes": "Asia's largest wholesale spice market; near Chandni Chowk; eye-watering chili dust"},
    {"name": "Zanzibar Spice Farms & Market", "city": "Stone Town", "country": "Tanzania",
     "lat": -6.1622, "lon": 39.1921, "est": 1840, "key_spice": "Cloves & nutmeg",
     "notes": "Spice Island tours; Zanzibar produces 90% of Tanzania's cloves"},
    {"name": "Dubai Spice Souk", "city": "Dubai", "country": "UAE",
     "lat": 25.2693, "lon": 55.2970, "est": 1900, "key_spice": "Frankincense & saffron",
     "notes": "Deira Creek-side market; saffron from Iran and Kashmir; oud and frankincense"},
    {"name": "Mercado de Sonora", "city": "Mexico City", "country": "Mexico",
     "lat": 19.4259, "lon": -99.1195, "est": 1957, "key_spice": "Chilies & mole pastes",
     "notes": "Mexico's witchcraft and spice market; dried chilies, herbs, remedies"},
    {"name": "Cochin Spice Market", "city": "Kochi (Cochin)", "country": "India",
     "lat": 9.9661, "lon": 76.2422, "est": 1500, "key_spice": "Black pepper & cardamom",
     "notes": "Historic Mattancherry spice trading district; Vasco da Gama's spice destination"},
    {"name": "Spice Souk Marrakech", "city": "Marrakech", "country": "Morocco",
     "lat": 31.6298, "lon": -7.9820, "est": 1050, "key_spice": "Ras el hanout & cumin",
     "notes": "Medina spice stalls with pyramids of coloured spices; ras el hanout blends"},
    {"name": "Aswan Spice Market", "city": "Aswan", "country": "Egypt",
     "lat": 24.0889, "lon": 32.8998, "est": 1800, "key_spice": "Hibiscus & karkade",
     "notes": "Nubian souk along the Nile corniche; dried hibiscus, henna, dates"},
    {"name": "Mapusa Market", "city": "Mapusa (Goa)", "country": "India",
     "lat": 15.5915, "lon": 73.8073, "est": 1800, "key_spice": "Kokum & Goan chilies",
     "notes": "Friday market with Goan spice blends, cashews, and toddy vinegar"},
    {"name": "Mahane Yehuda Market", "city": "Jerusalem", "country": "Israel",
     "lat": 31.7855, "lon": 35.2126, "est": 1928, "key_spice": "Za'atar & baharat",
     "notes": "Shuk with spice shops, halva, dried fruit; transforms into bar scene at night"},
    {"name": "La Merced Spice Section", "city": "Mexico City", "country": "Mexico",
     "lat": 19.4258, "lon": -99.1241, "est": 1880, "key_spice": "Achiote & epazote",
     "notes": "Dried chili section of the Americas' largest market; 80+ chile varieties"},
    {"name": "Crawford Market (Mahatma Jyotiba Phule)", "city": "Mumbai", "country": "India",
     "lat": 18.9476, "lon": 72.8346, "est": 1869, "key_spice": "Garam masala & asafoetida",
     "notes": "British-era market designed by Rudyard Kipling's father; wholesale spices and fruit"},
    {"name": "Osh Bazaar", "city": "Bishkek", "country": "Kyrgyzstan",
     "lat": 42.8757, "lon": 74.5733, "est": 1930, "key_spice": "Cumin & dried fruit",
     "notes": "Central Asia's great market; Silk Road spices, dried fruits, horse sausage (kazy)"},
    {"name": "Spice Bazaar Samarkand", "city": "Samarkand", "country": "Uzbekistan",
     "lat": 39.6500, "lon": 66.9600, "est": 600, "key_spice": "Cumin & barberries",
     "notes": "Ancient Silk Road trading hub; Siab Bazaar near Bibi-Khanym Mosque"},
    {"name": "Central Market Spice Hall", "city": "Budapest", "country": "Hungary",
     "lat": 47.4873, "lon": 19.0590, "est": 1897, "key_spice": "Paprika",
     "notes": "Great Market Hall with paprika garlands; Hungary's national spice"},
    {"name": "Devaraja Market", "city": "Mysore", "country": "India",
     "lat": 12.3120, "lon": 76.6550, "est": 1886, "key_spice": "Sandalwood & turmeric",
     "notes": "Over 130 years old; kumkum powders, incense, jasmine garlands, sandalwood"},
    {"name": "Mercado de Abastos", "city": "Oaxaca", "country": "Mexico",
     "lat": 17.0571, "lon": -96.7195, "est": 1978, "key_spice": "Mole negro ingredients",
     "notes": "Oaxaca's main market; chocolate, chapulines (grasshoppers), 7 moles, mezcal"},
    {"name": "Grand Bazaar Spice Section", "city": "Tehran", "country": "Iran",
     "lat": 35.6722, "lon": 51.4220, "est": 1500, "key_spice": "Saffron & dried lime",
     "notes": "Iranian saffron capital; rose petals, dried limes (limoo amani), barberries"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 7. CHRISTMAS MARKETS  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

CHRISTMAS_MARKETS = [
    {"name": "Christkindelsmaerik", "city": "Strasbourg", "country": "France",
     "lat": 48.5815, "lon": 7.7507, "est": 1570, "stalls": 300,
     "notes": "France's oldest Christmas market; 'Capital of Christmas'; 2M+ visitors per year"},
    {"name": "Christkindlesmarkt", "city": "Nuremberg", "country": "Germany",
     "lat": 49.4540, "lon": 11.0775, "est": 1628, "stalls": 180,
     "notes": "Germany's most famous; Lebkuchen (gingerbread), Gluhwein, Nuremberg sausages"},
    {"name": "Wiener Christkindlmarkt", "city": "Vienna", "country": "Austria",
     "lat": 48.2106, "lon": 16.3568, "est": 1298, "stalls": 150,
     "notes": "Rathausplatz market; dates to the Middle Ages; punch, handicrafts, Krampus parades"},
    {"name": "Kolner Weihnachtsmarkt", "city": "Cologne", "country": "Germany",
     "lat": 50.9413, "lon": 6.9583, "est": 1820, "stalls": 160,
     "notes": "Cathedral backdrop; 7 linked markets; Kolsch beer and Reibekuchen"},
    {"name": "Prague Old Town Christmas Market", "city": "Prague", "country": "Czech Republic",
     "lat": 50.0875, "lon": 14.4213, "est": 1585, "stalls": 120,
     "notes": "Old Town Square market; trdlo (chimney cake), svarak (mulled wine), puppet shows"},
    {"name": "Tivoli Gardens Christmas", "city": "Copenhagen", "country": "Denmark",
     "lat": 55.6736, "lon": 12.5681, "est": 1994, "stalls": 60,
     "notes": "Fairy-tale amusement park Christmas market; glogg, aebleskiver, illuminated gardens"},
    {"name": "Dresdner Striezelmarkt", "city": "Dresden", "country": "Germany",
     "lat": 51.0495, "lon": 13.7363, "est": 1434, "stalls": 240,
     "notes": "Germany's oldest market; famous for Stollen cake; 14-metre step pyramid"},
    {"name": "Salzburger Christkindlmarkt", "city": "Salzburg", "country": "Austria",
     "lat": 47.7990, "lon": 13.0437, "est": 1491, "stalls": 100,
     "notes": "Beneath Hohensalzburg Fortress; Krampus runs, Mozart chocolates, alpine crafts"},
    {"name": "Winter Wonderland", "city": "London", "country": "United Kingdom",
     "lat": 51.5033, "lon": -0.1607, "est": 2007, "stalls": 200,
     "notes": "Hyde Park mega-event; German-style market, ice rink, Bavarian village"},
    {"name": "Tallinn Christmas Market", "city": "Tallinn", "country": "Estonia",
     "lat": 59.4370, "lon": 24.7454, "est": 1441, "stalls": 60,
     "notes": "Town Hall Square; claims the first Christmas tree in Europe (1441); medieval setting"},
    {"name": "Budapest Christmas Fair", "city": "Budapest", "country": "Hungary",
     "lat": 47.4874, "lon": 19.0552, "est": 1998, "stalls": 120,
     "notes": "Vorosmarty Square market; chimney cake, goose liver, folk crafts"},
    {"name": "Christkindlmarkt", "city": "Munich", "country": "Germany",
     "lat": 48.1371, "lon": 11.5753, "est": 1642, "stalls": 160,
     "notes": "Marienplatz market; giant Christmas tree, Krampus parades, Bavarian traditions"},
    {"name": "Mercatino di Natale", "city": "Bolzano", "country": "Italy",
     "lat": 46.4981, "lon": 11.3548, "est": 1991, "stalls": 80,
     "notes": "Italy's most famous Christmas market; Tyrolean-Italian Alpine fusion"},
    {"name": "Skansen Christmas Market", "city": "Stockholm", "country": "Sweden",
     "lat": 59.3268, "lon": 18.1044, "est": 1903, "stalls": 100,
     "notes": "Open-air museum market; traditional Scandinavian crafts, glogg, pepparkakor"},
    {"name": "Grand Place Christmas", "city": "Brussels", "country": "Belgium",
     "lat": 50.8467, "lon": 4.3525, "est": 2002, "stalls": 200,
     "notes": "Light show on guild houses; waffles, Belgian chocolate, ice rink"},
    {"name": "Krakow Christmas Market", "city": "Krakow", "country": "Poland",
     "lat": 50.0614, "lon": 19.9372, "est": 1995, "stalls": 80,
     "notes": "Rynek Glowny main square; szopka (nativity crib) competition; oscypek cheese"},
    {"name": "Zagreb Advent", "city": "Zagreb", "country": "Croatia",
     "lat": 45.8131, "lon": 15.9773, "est": 2010, "stalls": 90,
     "notes": "Voted Europe's best Christmas market 3 years running; Ban Jelacic Square"},
    {"name": "Toronto Christmas Market", "city": "Toronto", "country": "Canada",
     "lat": 43.6504, "lon": -79.3588, "est": 2010, "stalls": 75,
     "notes": "Distillery District; European-style market; poutine, beaver tails, ice sculptures"},
    {"name": "Heidelberger Weihnachtsmarkt", "city": "Heidelberg", "country": "Germany",
     "lat": 49.4093, "lon": 8.6938, "est": 1600, "stalls": 140,
     "notes": "Six linked markets in the Old Town; castle backdrop; ice rink on Karlsplatz"},
    {"name": "Helsinki Christmas Market", "city": "Helsinki", "country": "Finland",
     "lat": 60.1699, "lon": 24.9384, "est": 1890, "stalls": 120,
     "notes": "Senate Square market; Tuomaan Markkinat; Finnish design, reindeer skins, glogg"},
    {"name": "Union Square Holiday Market", "city": "New York City", "country": "USA",
     "lat": 40.7359, "lon": -73.9911, "est": 1994, "stalls": 150,
     "notes": "NYC's premier holiday market; artisan gifts, hot cider, mini donuts"},
    {"name": "Esslingen Medieval Christmas Market", "city": "Esslingen", "country": "Germany",
     "lat": 48.7396, "lon": 9.3108, "est": 1978, "stalls": 180,
     "notes": "Half-timbered medieval backdrop; jousting, blacksmiths, mead, roasted almonds"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 8. STOCK EXCHANGES  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

STOCK_EXCHANGES = [
    {"name": "New York Stock Exchange (NYSE)", "city": "New York City", "country": "USA",
     "lat": 40.7069, "lon": -74.0113, "founded": 1792, "market_cap_usd_tn": 27.7,
     "notes": "World's largest stock exchange by market cap; 11 Wall Street; Buttonwood Agreement"},
    {"name": "NASDAQ", "city": "New York City", "country": "USA",
     "lat": 40.7566, "lon": -73.9863, "founded": 1971, "market_cap_usd_tn": 24.6,
     "notes": "World's first electronic stock exchange; tech-heavy; Times Square MarketSite"},
    {"name": "London Stock Exchange (LSE)", "city": "London", "country": "United Kingdom",
     "lat": 51.5155, "lon": -0.0922, "founded": 1801, "market_cap_usd_tn": 3.2,
     "notes": "One of the oldest exchanges; Paternoster Square; traces to coffee house in 1698"},
    {"name": "Tokyo Stock Exchange (TSE)", "city": "Tokyo", "country": "Japan",
     "lat": 35.6814, "lon": 139.7747, "founded": 1878, "market_cap_usd_tn": 6.5,
     "notes": "Asia's largest exchange; Nikkei 225; Kabuto-cho financial district"},
    {"name": "Shanghai Stock Exchange (SSE)", "city": "Shanghai", "country": "China",
     "lat": 31.2302, "lon": 121.4737, "founded": 1990, "market_cap_usd_tn": 7.4,
     "notes": "World's 3rd largest by market cap; Pudong Lujiazui district"},
    {"name": "Shenzhen Stock Exchange (SZSE)", "city": "Shenzhen", "country": "China",
     "lat": 22.5350, "lon": 114.0540, "founded": 1990, "market_cap_usd_tn": 4.7,
     "notes": "China's tech-focused exchange; striking OMA-designed floating building"},
    {"name": "Euronext", "city": "Paris", "country": "France",
     "lat": 48.8690, "lon": 2.3420, "founded": 2000, "market_cap_usd_tn": 7.3,
     "notes": "Pan-European exchange; Paris, Amsterdam, Brussels, Lisbon, Dublin, Oslo, Milan"},
    {"name": "Hong Kong Stock Exchange (HKEX)", "city": "Hong Kong", "country": "China",
     "lat": 22.2830, "lon": 114.1564, "founded": 1891, "market_cap_usd_tn": 4.3,
     "notes": "Gateway to Chinese capital markets; Central district; typhoon trading rules"},
    {"name": "Bombay Stock Exchange (BSE)", "city": "Mumbai", "country": "India",
     "lat": 18.9290, "lon": 72.8332, "founded": 1875, "market_cap_usd_tn": 4.1,
     "notes": "Asia's oldest exchange; Dalal Street; Sensex 30 index; iconic bull statue"},
    {"name": "National Stock Exchange of India (NSE)", "city": "Mumbai", "country": "India",
     "lat": 19.0554, "lon": 72.8626, "founded": 1992, "market_cap_usd_tn": 3.8,
     "notes": "India's largest by daily turnover; Nifty 50 index; BKC complex"},
    {"name": "Frankfurt Stock Exchange (FWB)", "city": "Frankfurt", "country": "Germany",
     "lat": 50.1109, "lon": 8.6821, "founded": 1585, "market_cap_usd_tn": 2.3,
     "notes": "Borsenplatz; iconic bull and bear statues; Deutsche Borse Group"},
    {"name": "Toronto Stock Exchange (TSX)", "city": "Toronto", "country": "Canada",
     "lat": 43.6490, "lon": -79.3811, "founded": 1852, "market_cap_usd_tn": 3.1,
     "notes": "9th largest globally; mining and resource stocks; Bay Street financial district"},
    {"name": "SIX Swiss Exchange", "city": "Zurich", "country": "Switzerland",
     "lat": 47.3669, "lon": 8.5393, "founded": 1850, "market_cap_usd_tn": 1.9,
     "notes": "Pharma and banking giants; Nestle, Roche, Novartis, UBS; fully electronic since 1995"},
    {"name": "Korea Exchange (KRX)", "city": "Busan", "country": "South Korea",
     "lat": 35.1028, "lon": 129.0305, "founded": 1956, "market_cap_usd_tn": 2.2,
     "notes": "KOSPI and KOSDAQ indices; one of the busiest derivatives markets globally"},
    {"name": "Australian Securities Exchange (ASX)", "city": "Sydney", "country": "Australia",
     "lat": -33.8688, "lon": 151.2093, "founded": 1861, "market_cap_usd_tn": 1.7,
     "notes": "Bridge Street; first exchange to open each global trading day; mining and banks"},
    {"name": "Johannesburg Stock Exchange (JSE)", "city": "Johannesburg", "country": "South Africa",
     "lat": -26.1437, "lon": 28.0473, "founded": 1887, "market_cap_usd_tn": 1.0,
     "notes": "Africa's largest exchange; Sandton financial district; gold and mining origin"},
    {"name": "Singapore Exchange (SGX)", "city": "Singapore", "country": "Singapore",
     "lat": 1.2789, "lon": 103.8536, "founded": 1999, "market_cap_usd_tn": 0.7,
     "notes": "Asia-Pacific derivatives hub; Shenton Way financial centre"},
    {"name": "B3 (Brasil Bolsa Balcao)", "city": "Sao Paulo", "country": "Brazil",
     "lat": -23.5489, "lon": -46.6388, "founded": 1890, "market_cap_usd_tn": 1.0,
     "notes": "Latin America's largest exchange; Bovespa index; Rua XV de Novembro"},
    {"name": "Taiwan Stock Exchange (TWSE)", "city": "Taipei", "country": "Taiwan",
     "lat": 25.0390, "lon": 121.5648, "founded": 1961, "market_cap_usd_tn": 2.1,
     "notes": "Semiconductor-heavy; TSMC alone accounts for ~30% of market cap"},
    {"name": "Saudi Exchange (Tadawul)", "city": "Riyadh", "country": "Saudi Arabia",
     "lat": 24.6907, "lon": 46.6853, "founded": 2007, "market_cap_usd_tn": 2.9,
     "notes": "Middle East's largest; Saudi Aramco listing in 2019 was world's largest IPO"},
    {"name": "Mexican Stock Exchange (BMV)", "city": "Mexico City", "country": "Mexico",
     "lat": 19.4393, "lon": -99.2013, "founded": 1894, "market_cap_usd_tn": 0.5,
     "notes": "Paseo de la Reforma; iconic building; Latin America's 2nd largest exchange"},
    {"name": "Amsterdam Stock Exchange", "city": "Amsterdam", "country": "Netherlands",
     "lat": 52.3676, "lon": 4.8968, "founded": 1602, "market_cap_usd_tn": 1.8,
     "notes": "World's first official stock exchange; Dutch East India Company; Beursplein 5"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 9. LUXURY SHOPPING STREETS  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

LUXURY_STREETS = [
    {"name": "Fifth Avenue", "city": "New York City", "country": "USA",
     "lat": 40.7636, "lon": -73.9733, "avg_rent_sqft": 2000,
     "key_stores": "Tiffany, Saks, Bergdorf Goodman, Louis Vuitton",
     "notes": "World's most expensive retail strip; Midtown section from 49th to 60th St"},
    {"name": "Champs-Elysees", "city": "Paris", "country": "France",
     "lat": 48.8698, "lon": 2.3076, "avg_rent_sqft": 1500,
     "key_stores": "Louis Vuitton, Cartier, Guerlain, Laduree",
     "notes": "Most famous avenue in the world; Arc de Triomphe to Place de la Concorde"},
    {"name": "Via Montenapoleone", "city": "Milan", "country": "Italy",
     "lat": 45.4689, "lon": 9.1959, "avg_rent_sqft": 1700,
     "key_stores": "Gucci, Prada, Versace, Valentino, Armani",
     "notes": "Heart of Milan's Quadrilatero della Moda; world's most expensive shopping street by rent"},
    {"name": "Ginza", "city": "Tokyo", "country": "Japan",
     "lat": 35.6717, "lon": 139.7653, "avg_rent_sqft": 1200,
     "key_stores": "Mikimoto, Wako, Mitsukoshi, Chanel",
     "notes": "Tokyo's luxury district since the Meiji era; weekend pedestrian paradise (Hokoten)"},
    {"name": "New Bond Street", "city": "London", "country": "United Kingdom",
     "lat": 51.5124, "lon": -0.1447, "avg_rent_sqft": 1800,
     "key_stores": "Burberry, Cartier, Tiffany, Asprey, Graff",
     "notes": "London's premier luxury strip; Old Bond meets New Bond; jewelry and haute couture"},
    {"name": "Rodeo Drive", "city": "Beverly Hills", "country": "USA",
     "lat": 34.0669, "lon": -118.4011, "avg_rent_sqft": 900,
     "key_stores": "Chanel, Dior, Harry Winston, Bvlgari",
     "notes": "Hollywood glamour; 3-block 'Golden Triangle'; Pretty Woman filming location"},
    {"name": "Bahnhofstrasse", "city": "Zurich", "country": "Switzerland",
     "lat": 47.3716, "lon": 8.5383, "avg_rent_sqft": 950,
     "key_stores": "Rolex, Bucherer, Grieder, Globus",
     "notes": "Swiss luxury; 1.4 km from lake to station; private banking and watchmakers"},
    {"name": "Avenue Montaigne", "city": "Paris", "country": "France",
     "lat": 48.8666, "lon": 2.3042, "avg_rent_sqft": 1400,
     "key_stores": "Dior HQ, Chanel, Valentino, Celine, Fendi",
     "notes": "Paris's quieter luxury avenue; Christian Dior's flagship at No. 30"},
    {"name": "Rue du Faubourg Saint-Honore", "city": "Paris", "country": "France",
     "lat": 48.8698, "lon": 2.3183, "avg_rent_sqft": 1300,
     "key_stores": "Hermes flagship, Lanvin, Goyard, Elysee Palace",
     "notes": "Historic luxury street; Hermes founded here in 1837; adjacent to Elysee Palace"},
    {"name": "Via Condotti", "city": "Rome", "country": "Italy",
     "lat": 45.6764, "lon": 12.3365, "avg_rent_sqft": 800,
     "key_stores": "Bulgari, Gucci, Prada, Ferragamo, Fendi",
     "notes": "Rome's most exclusive street; Spanish Steps at one end; Caffe Greco since 1760"},
    {"name": "Orchard Road", "city": "Singapore", "country": "Singapore",
     "lat": 1.3036, "lon": 103.8318, "avg_rent_sqft": 600,
     "key_stores": "ION Orchard, Paragon, Takashimaya",
     "notes": "2.2 km shopping boulevard; mega-malls and luxury boutiques; annual Christmas light-up"},
    {"name": "Passeig de Gracia", "city": "Barcelona", "country": "Spain",
     "lat": 41.3926, "lon": 2.1644, "avg_rent_sqft": 500,
     "key_stores": "Loewe, Chanel, Louis Vuitton, Cartier",
     "notes": "Gaudi's Casa Batllo and La Pedrera line this Eixample luxury boulevard"},
    {"name": "Myeongdong", "city": "Seoul", "country": "South Korea",
     "lat": 37.5636, "lon": 126.9860, "avg_rent_sqft": 550,
     "key_stores": "Lotte, Shinsegae, K-beauty flagship stores",
     "notes": "Seoul's main shopping district; K-beauty mecca; 2M+ visitors daily"},
    {"name": "Causeway Bay", "city": "Hong Kong", "country": "China",
     "lat": 22.2793, "lon": 114.1854, "avg_rent_sqft": 1300,
     "key_stores": "Times Square HK, Sogo, Lee Gardens",
     "notes": "World's most expensive commercial rent per sq ft; Russell Street landmark"},
    {"name": "Omotesando", "city": "Tokyo", "country": "Japan",
     "lat": 35.6654, "lon": 139.7095, "avg_rent_sqft": 800,
     "key_stores": "Prada, Louis Vuitton, Dior, Comme des Garcons",
     "notes": "Tokyo's Champs-Elysees; zelkova tree-lined avenue; avant-garde architecture"},
    {"name": "Maximilianstrasse", "city": "Munich", "country": "Germany",
     "lat": 48.1381, "lon": 11.5842, "avg_rent_sqft": 500,
     "key_stores": "Bulgari, Hermes, Escada, Porsche Design",
     "notes": "Munich's royal boulevard; neo-Gothic architecture; opera house to river"},
    {"name": "Collins Street", "city": "Melbourne", "country": "Australia",
     "lat": -37.8136, "lon": 144.9730, "avg_rent_sqft": 350,
     "key_stores": "Louis Vuitton, Chanel, Tiffany, Block Arcade",
     "notes": "Melbourne's 'Paris End'; historic Block Arcade and Royal Arcade"},
    {"name": "Istiklal Avenue", "city": "Istanbul", "country": "Turkey",
     "lat": 41.0335, "lon": 28.9769, "avg_rent_sqft": 250,
     "key_stores": "Beyoglu boutiques, Passage du Pera, Cicek Pasaji",
     "notes": "1.4 km pedestrian boulevard; nostalgic tram; 3M visitors daily"},
    {"name": "Rua Oscar Freire", "city": "Sao Paulo", "country": "Brazil",
     "lat": -23.5629, "lon": -46.6702, "avg_rent_sqft": 300,
     "key_stores": "Havaianas, H. Stern, Osklen, local designers",
     "notes": "South America's luxury capital; Jardins neighbourhood; Brazilian high fashion"},
    {"name": "Koenigsallee (Ko)", "city": "Dusseldorf", "country": "Germany",
     "lat": 51.2240, "lon": 6.7811, "avg_rent_sqft": 400,
     "key_stores": "Chanel, Breguet, Sevens mall, Ko-Galerie",
     "notes": "Tree-lined canal boulevard; Germany's most upscale shopping; art galleries"},
    {"name": "Knightsbridge", "city": "London", "country": "United Kingdom",
     "lat": 51.5014, "lon": -0.1605, "avg_rent_sqft": 1500,
     "key_stores": "Harrods, Harvey Nichols, Sloane Street boutiques",
     "notes": "Home to Harrods since 1849; Sloane Street extends into Chelsea luxury"},
    {"name": "The Dubai Mall & Downtown", "city": "Dubai", "country": "UAE",
     "lat": 25.1972, "lon": 55.2796, "avg_rent_sqft": 600,
     "key_stores": "Fashion Avenue, Bloomingdale's, Galeries Lafayette",
     "notes": "World's largest mall; 1,300+ stores; Burj Khalifa views; Gold Souk extension"},
]

# ══════════════════════════════════════════════════════════════════════════════
# CURATED DATA -- 10. HISTORIC TRADING POSTS  (22 entries)
# ══════════════════════════════════════════════════════════════════════════════

HISTORIC_TRADING_POSTS = [
    {"name": "Bryggen (Hanseatic Wharf)", "city": "Bergen", "country": "Norway",
     "lat": 60.3975, "lon": 5.3240, "era": "1350-1750", "network": "Hanseatic League",
     "notes": "UNESCO World Heritage; colourful wooden warehouses; German merchants traded cod and grain"},
    {"name": "Lubeck Altstadt", "city": "Lubeck", "country": "Germany",
     "lat": 53.8655, "lon": 10.6866, "era": "1159-1669", "network": "Hanseatic League",
     "notes": "Queen of the Hansa; Holstentor gate; capital of the Hanseatic League"},
    {"name": "Tallinn Old Town", "city": "Tallinn", "country": "Estonia",
     "lat": 59.4370, "lon": 24.7454, "era": "1285-1669", "network": "Hanseatic League",
     "notes": "Best-preserved medieval Hanseatic town; Great Guild Hall; spice and fur trade"},
    {"name": "Gdansk Long Market", "city": "Gdansk", "country": "Poland",
     "lat": 54.3486, "lon": 18.6532, "era": "1361-1669", "network": "Hanseatic League",
     "notes": "Baltic amber trade capital; Artus Court; Royal Way merchants' houses"},
    {"name": "Samarkand (Registan)", "city": "Samarkand", "country": "Uzbekistan",
     "lat": 39.6542, "lon": 66.9597, "era": "300 BCE-1500", "network": "Silk Road",
     "notes": "Jewel of the Silk Road; Registan madrasas; Tamerlane's capital; paper and silk trade"},
    {"name": "Kashgar Old City", "city": "Kashgar", "country": "China",
     "lat": 39.4677, "lon": 75.9898, "era": "200 BCE-1500", "network": "Silk Road",
     "notes": "Western Silk Road terminus; Id Kah Mosque; Uyghur livestock and jade market"},
    {"name": "Bukhara Old City", "city": "Bukhara", "country": "Uzbekistan",
     "lat": 39.7681, "lon": 64.4216, "era": "500 BCE-1800", "network": "Silk Road",
     "notes": "UNESCO Silk Road city; covered trading domes (taki); carpets and textiles"},
    {"name": "Aleppo Citadel & Souks", "city": "Aleppo", "country": "Syria",
     "lat": 36.1990, "lon": 37.1566, "era": "3000 BCE-present", "network": "Silk Road / Mediterranean",
     "notes": "One of the oldest continuously inhabited cities; medieval souk was 13 km long"},
    {"name": "Malacca (Melaka) Historic Centre", "city": "Melaka", "country": "Malaysia",
     "lat": 2.1896, "lon": 102.2501, "era": "1400-1641", "network": "Maritime Spice Route",
     "notes": "UNESCO Heritage; Strait of Malacca chokepoint; Portuguese, Dutch, and British colonial layers"},
    {"name": "Fort William (Calcutta)", "city": "Kolkata", "country": "India",
     "lat": 22.5534, "lon": 88.3423, "era": "1696-1947", "network": "East India Company",
     "notes": "British East India Company headquarters; opium, tea, and textile trade hub"},
    {"name": "Factory House, Canton", "city": "Guangzhou", "country": "China",
     "lat": 23.1116, "lon": 113.2530, "era": "1757-1842", "network": "Canton Trade System",
     "notes": "Thirteen Factories foreign trading district; only point of China-Europe trade for 85 years"},
    {"name": "Fort Vancouver", "city": "Vancouver WA", "country": "USA",
     "lat": 45.6249, "lon": -122.6562, "era": "1825-1860", "network": "Hudson's Bay Company",
     "notes": "HBC fur trade headquarters on the Columbia River; Pacific Northwest gateway"},
    {"name": "Bent's Old Fort", "city": "La Junta CO", "country": "USA",
     "lat": 38.0395, "lon": -103.4266, "era": "1833-1849", "network": "Santa Fe Trail",
     "notes": "Adobe trading post on the mountain route of the Santa Fe Trail; buffalo hides and furs"},
    {"name": "Mocha (Al Mokha)", "city": "Mocha", "country": "Yemen",
     "lat": 13.3164, "lon": 43.2447, "era": "1400-1750", "network": "Coffee Trade",
     "notes": "Birthplace of coffee trade; 'mocha' coffee named after this Red Sea port"},
    {"name": "Timbuktu", "city": "Timbuktu", "country": "Mali",
     "lat": 16.7666, "lon": -3.0026, "era": "1200-1600", "network": "Trans-Saharan Trade",
     "notes": "Legendary trading city; gold, salt, manuscripts; Sankore University; 'City of 333 Saints'"},
    {"name": "Zanzibar Stone Town", "city": "Zanzibar City", "country": "Tanzania",
     "lat": -6.1622, "lon": 39.1921, "era": "1698-1890", "network": "Indian Ocean Trade",
     "notes": "Omani-controlled spice and slave trade hub; cloves, ivory, and European colonial layers"},
    {"name": "Batavia (Jakarta Old Town)", "city": "Jakarta", "country": "Indonesia",
     "lat": -6.1352, "lon": 106.8133, "era": "1619-1799", "network": "Dutch East India Company (VOC)",
     "notes": "VOC headquarters in Asia; spice warehouse district; Fatahillah Square museums"},
    {"name": "Galle Fort", "city": "Galle", "country": "Sri Lanka",
     "lat": 6.0267, "lon": 80.2170, "era": "1588-1948", "network": "Spice Trade / Colonial",
     "notes": "Portuguese then Dutch fort; cinnamon trade; UNESCO-listed; lighthouse and ramparts"},
    {"name": "Macau Historic Centre", "city": "Macau", "country": "China",
     "lat": 22.1987, "lon": 113.5439, "era": "1557-1999", "network": "Portuguese Maritime Trade",
     "notes": "First European outpost in China; Ruins of St. Paul's; Portugal-China-Japan trade triangle"},
    {"name": "Elmina Castle", "city": "Elmina", "country": "Ghana",
     "lat": 5.0820, "lon": -1.3497, "era": "1482-1872", "network": "Gold Coast / Slave Trade",
     "notes": "Oldest European structure in sub-Saharan Africa; Portuguese gold trade, then slave trade"},
    {"name": "Dejima Island", "city": "Nagasaki", "country": "Japan",
     "lat": 32.7433, "lon": 129.8724, "era": "1641-1854", "network": "Dutch East India Company (VOC)",
     "notes": "Artificial island; only point of Western trade with Japan for 200 years of sakoku isolation"},
    {"name": "Fort Ross", "city": "Jenner CA", "country": "USA",
     "lat": 38.5146, "lon": -123.2445, "era": "1812-1841", "network": "Russian-American Company",
     "notes": "Southernmost Russian settlement in North America; sea otter fur trade with Alaska"},
]


# ══════════════════════════════════════════════════════════════════════════════
# CACHED FETCH FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _fetch_grand_bazaars():
    """Return curated Grand Bazaars & Souks dataset."""
    return list(GRAND_BAZAARS)

@st.cache_data(ttl=3600)
def _fetch_flea_markets():
    """Return curated Famous Flea Markets dataset."""
    return list(FLEA_MARKETS)

@st.cache_data(ttl=3600)
def _fetch_floating_markets():
    """Return curated Floating Markets dataset."""
    return list(FLOATING_MARKETS)

@st.cache_data(ttl=3600)
def _fetch_fish_markets():
    """Return curated Fish Markets dataset."""
    return list(FISH_MARKETS)

@st.cache_data(ttl=3600)
def _fetch_night_markets():
    """Return curated Night Markets dataset."""
    return list(NIGHT_MARKETS)

@st.cache_data(ttl=3600)
def _fetch_spice_markets():
    """Return curated Spice Markets dataset."""
    return list(SPICE_MARKETS)

@st.cache_data(ttl=3600)
def _fetch_christmas_markets():
    """Return curated Christmas Markets dataset."""
    return list(CHRISTMAS_MARKETS)

@st.cache_data(ttl=3600)
def _fetch_stock_exchanges():
    """Return curated Stock Exchanges dataset."""
    return list(STOCK_EXCHANGES)

@st.cache_data(ttl=3600)
def _fetch_luxury_streets():
    """Return curated Luxury Shopping Streets dataset."""
    return list(LUXURY_STREETS)

@st.cache_data(ttl=3600)
def _fetch_trading_posts():
    """Return curated Historic Trading Posts dataset."""
    return list(HISTORIC_TRADING_POSTS)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _show_stats(metrics: list):
    """Display metric cards in columns. metrics = [(label, value), ...]"""
    cols = st.columns(min(len(metrics), 5))
    for i, (label, value) in enumerate(metrics):
        cols[i % len(cols)].metric(label, value)


def _download_section(df: pd.DataFrame, filename: str, label: str, key: str):
    """Expander with dataframe and CSV download."""
    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label,
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def _build_map(data, lat_key="lat", lon_key="lon", zoom=2, center=None):
    """Create a dark-themed folium map."""
    if center is None:
        center = [20, 0]
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter")
    return m


def _popup_html(lines: list, color: str = ACCENT_AMBER) -> str:
    """Build a styled popup HTML block from a list of (label, value) tuples."""
    inner = ""
    for label, value in lines:
        safe_label = html_module.escape(str(label))
        safe_value = html_module.escape(str(value))
        inner += f"<b>{safe_label}:</b> {safe_value}<br/>"
    return (
        f'<div style="max-width:300px; font-size:0.85rem; '
        f'color:#e8ecf4; background:#1a2235; padding:8px; border-radius:6px; '
        f'border-left:3px solid {color};">'
        f'{inner}</div>'
    )


def _add_markers(m, data, name_key, popup_fields, color, lat_key="lat", lon_key="lon", radius=8):
    """Add CircleMarkers to a folium map."""
    for item in data:
        popup_lines = []
        for label, field in popup_fields:
            if field in item:
                popup_lines.append((label, item[field]))
        popup_h = _popup_html(popup_lines, color)
        safe_name = html_module.escape(str(item.get(name_key, "")))
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_h, max_width=320),
            tooltip=safe_name,
        ).add_to(m)
    return m


def _render_map(m):
    """Render a folium map using st_html."""
    st_html(m._repr_html_(), height=500)


def _legend(items: dict):
    """Render a colour legend. items = {label: color}."""
    spans = " ".join(
        f'<span style="color:{c}; font-size:0.8rem;">&#9679; {html_module.escape(t)}</span>'
        for t, c in items.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-top:0.25rem;">{spans}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# MODE RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def _render_grand_bazaars():
    """Mode 1: Grand Bazaars & Souks."""
    data = sorted(GRAND_BAZAARS, key=lambda x: x["founded"])
    countries = list(set(d["country"] for d in data))
    total_shops = sum(d["shops"] for d in data)
    oldest = min(data, key=lambda x: x["founded"])

    _show_stats([
        ("Markets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Total Shops", f"{total_shops:,}"),
        ("Oldest", f"{html_module.escape(oldest['name'])} ({oldest['founded']})"),
        ("Largest", f"{html_module.escape(max(data, key=lambda x: x['shops'])['name'])}"),
    ])

    st.markdown("---")
    st.markdown("#### Grand Bazaars & Souks Map")

    m = _build_map(data)
    _add_markers(m, data, "name", [
        ("Market", "name"), ("City", "city"), ("Country", "country"),
        ("Founded", "founded"), ("Shops", "shops"), ("Notes", "notes"),
    ], ACCENT_AMBER)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Founded": d["founded"], "Shops": d["shops"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "grand_bazaars_souks.csv",
                      f"Download {len(df)} Grand Bazaars & Souks (CSV)", "dl_bazaars")


def _render_flea_markets():
    """Mode 2: Famous Flea Markets."""
    data = FLEA_MARKETS
    countries = list(set(d["country"] for d in data))
    specialties = list(set(d["specialty"] for d in data))

    _show_stats([
        ("Markets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Specialties", len(specialties)),
        ("Cities", len(set(d["city"] for d in data))),
    ])

    st.markdown("---")
    st.markdown("#### Famous Flea Markets Map")

    m = _build_map(data, zoom=2, center=[30, 0])
    _add_markers(m, data, "name", [
        ("Market", "name"), ("City", "city"), ("Country", "country"),
        ("Day", "day"), ("Specialty", "specialty"), ("Notes", "notes"),
    ], ACCENT_ORANGE)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Day": d["day"], "Specialty": d["specialty"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "flea_markets.csv",
                      f"Download {len(df)} Flea Markets (CSV)", "dl_flea")


def _render_floating_markets():
    """Mode 3: Floating Markets."""
    data = sorted(FLOATING_MARKETS, key=lambda x: x["est"])
    countries = list(set(d["country"] for d in data))
    types = list(set(d["type"] for d in data))
    oldest = min(data, key=lambda x: x["est"])

    _show_stats([
        ("Markets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Water Types", len(types)),
        ("Oldest", f"{html_module.escape(oldest['name'][:25])} ({oldest['est']})"),
    ])

    st.markdown("---")
    st.markdown("#### Floating Markets Map")

    type_colors = {
        "River canal": "#06b6d4",
        "River (Mekong)": "#10b981",
        "Lake": "#3b82f6",
        "Canal (klong)": "#14b8a6",
        "River (Barito)": "#8b5cf6",
        "Harbor": "#f59e0b",
        "Bay": "#ec4899",
        "River dock": "#f97316",
        "River": "#22c55e",
        "Lake (Nokoue)": "#a855f7",
        "River (Martapura)": "#ef4444",
    }

    m = _build_map(data, zoom=3, center=[10, 100])
    for item in data:
        clr = type_colors.get(item["type"], ACCENT_CYAN)
        popup_h = _popup_html([
            ("Market", item["name"]), ("City", item["city"]),
            ("Country", item["country"]), ("Type", item["type"]),
            ("Established", item["est"]), ("Notes", item["notes"]),
        ], clr)
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=9, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_h, max_width=320),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    _legend({k: v for k, v in type_colors.items() if k in set(d["type"] for d in data)})

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Type": d["type"], "Established": d["est"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "floating_markets.csv",
                      f"Download {len(df)} Floating Markets (CSV)", "dl_floating")


def _render_fish_markets():
    """Mode 4: Fish Markets."""
    data = sorted(FISH_MARKETS, key=lambda x: x["daily_tonnes"], reverse=True)
    countries = list(set(d["country"] for d in data))
    total_tonnes = sum(d["daily_tonnes"] for d in data)
    biggest = data[0]

    _show_stats([
        ("Markets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Total Daily Tonnes", f"{total_tonnes:,}"),
        ("Largest", f"{html_module.escape(biggest['name'][:25])}"),
        ("Top Tonnes/Day", f"{biggest['daily_tonnes']:,}"),
    ])

    st.markdown("---")
    st.markdown("#### Fish Markets Map")

    m = _build_map(data)
    for item in data:
        radius = max(5, min(15, item["daily_tonnes"] / 100))
        popup_h = _popup_html([
            ("Market", item["name"]), ("City", item["city"]),
            ("Country", item["country"]),
            ("Daily Tonnes", f"{item['daily_tonnes']:,}"),
            ("Specialty", item["specialty"]), ("Notes", item["notes"]),
        ], ACCENT_BLUE)
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius, color=ACCENT_BLUE, fill=True, fill_color=ACCENT_BLUE,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_h, max_width=320),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Daily Tonnes": d["daily_tonnes"], "Specialty": d["specialty"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "fish_markets.csv",
                      f"Download {len(df)} Fish Markets (CSV)", "dl_fish")


def _render_night_markets():
    """Mode 5: Night Markets."""
    data = NIGHT_MARKETS
    countries = list(set(d["country"] for d in data))
    cities = list(set(d["city"] for d in data))

    _show_stats([
        ("Markets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Cities", len(cities)),
        ("Top Region", "Asia-Pacific"),
    ])

    st.markdown("---")
    st.markdown("#### Night Markets Map")

    m = _build_map(data, zoom=3, center=[20, 105])
    _add_markers(m, data, "name", [
        ("Market", "name"), ("City", "city"), ("Country", "country"),
        ("Specialty", "specialty"), ("Visitors", "visitors"), ("Notes", "notes"),
    ], ACCENT_VIOLET)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Specialty": d["specialty"], "Visitors": d["visitors"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "night_markets.csv",
                      f"Download {len(df)} Night Markets (CSV)", "dl_night")


def _render_spice_markets():
    """Mode 6: Spice Markets."""
    data = sorted(SPICE_MARKETS, key=lambda x: x["est"])
    countries = list(set(d["country"] for d in data))
    oldest = min(data, key=lambda x: x["est"])
    spices = list(set(d["key_spice"] for d in data))

    _show_stats([
        ("Markets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Unique Spice Profiles", len(spices)),
        ("Oldest", f"{html_module.escape(oldest['name'][:25])} ({oldest['est']})"),
    ])

    st.markdown("---")
    st.markdown("#### Spice Markets Map")

    m = _build_map(data, zoom=3, center=[25, 55])
    _add_markers(m, data, "name", [
        ("Market", "name"), ("City", "city"), ("Country", "country"),
        ("Established", "est"), ("Key Spice", "key_spice"), ("Notes", "notes"),
    ], ACCENT_RED)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Established": d["est"], "Key Spice": d["key_spice"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "spice_markets.csv",
                      f"Download {len(df)} Spice Markets (CSV)", "dl_spice")


def _render_christmas_markets():
    """Mode 7: Christmas Markets."""
    data = sorted(CHRISTMAS_MARKETS, key=lambda x: x["est"])
    countries = list(set(d["country"] for d in data))
    total_stalls = sum(d["stalls"] for d in data)
    oldest = min(data, key=lambda x: x["est"])

    _show_stats([
        ("Markets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Total Stalls", f"{total_stalls:,}"),
        ("Oldest", f"{html_module.escape(oldest['city'])} ({oldest['est']})"),
        ("Avg. Stalls", total_stalls // len(data)),
    ])

    st.markdown("---")
    st.markdown("#### Christmas Markets Map")

    m = _build_map(data, zoom=4, center=[50, 10])
    for item in data:
        radius = max(5, min(14, item["stalls"] / 20))
        popup_h = _popup_html([
            ("Market", item["name"]), ("City", item["city"]),
            ("Country", item["country"]), ("Established", item["est"]),
            ("Stalls", item["stalls"]), ("Notes", item["notes"]),
        ], ACCENT_EMERALD)
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius, color=ACCENT_EMERALD, fill=True, fill_color=ACCENT_EMERALD,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_h, max_width=320),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Established": d["est"], "Stalls": d["stalls"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "christmas_markets.csv",
                      f"Download {len(df)} Christmas Markets (CSV)", "dl_christmas")


def _render_stock_exchanges():
    """Mode 8: Stock Exchanges."""
    data = sorted(STOCK_EXCHANGES, key=lambda x: x["market_cap_usd_tn"], reverse=True)
    countries = list(set(d["country"] for d in data))
    total_cap = sum(d["market_cap_usd_tn"] for d in data)
    oldest = min(data, key=lambda x: x["founded"])
    largest = data[0]

    _show_stats([
        ("Exchanges Mapped", len(data)),
        ("Countries", len(countries)),
        ("Total Market Cap", f"${total_cap:.1f}T"),
        ("Oldest", f"{html_module.escape(oldest['name'][:20])} ({oldest['founded']})"),
        ("Largest", f"{html_module.escape(largest['name'][:20])}"),
    ])

    st.markdown("---")
    st.markdown("#### Stock Exchanges Map")

    m = _build_map(data)
    for item in data:
        radius = max(5, min(16, item["market_cap_usd_tn"] * 0.5 + 4))
        popup_h = _popup_html([
            ("Exchange", item["name"]), ("City", item["city"]),
            ("Country", item["country"]), ("Founded", item["founded"]),
            ("Market Cap", f"${item['market_cap_usd_tn']:.1f} Trillion"),
            ("Notes", item["notes"]),
        ], ACCENT_TEAL)
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius, color=ACCENT_TEAL, fill=True, fill_color=ACCENT_TEAL,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_h, max_width=320),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Founded": d["founded"], "Market Cap ($T)": d["market_cap_usd_tn"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "stock_exchanges.csv",
                      f"Download {len(df)} Stock Exchanges (CSV)", "dl_exchanges")


def _render_luxury_streets():
    """Mode 9: Luxury Shopping Streets."""
    data = sorted(LUXURY_STREETS, key=lambda x: x["avg_rent_sqft"], reverse=True)
    countries = list(set(d["country"] for d in data))
    cities = list(set(d["city"] for d in data))
    most_expensive = data[0]
    avg_rent = sum(d["avg_rent_sqft"] for d in data) // len(data)

    _show_stats([
        ("Streets Mapped", len(data)),
        ("Countries", len(countries)),
        ("Cities", len(cities)),
        ("Most Expensive", html_module.escape(most_expensive["name"][:20])),
        ("Avg. Rent/sqft", f"${avg_rent:,}"),
    ])

    st.markdown("---")
    st.markdown("#### Luxury Shopping Streets Map")

    m = _build_map(data)
    for item in data:
        radius = max(5, min(14, item["avg_rent_sqft"] / 150))
        popup_h = _popup_html([
            ("Street", item["name"]), ("City", item["city"]),
            ("Country", item["country"]),
            ("Avg Rent/sqft", f"${item['avg_rent_sqft']:,}"),
            ("Key Stores", item["key_stores"]), ("Notes", item["notes"]),
        ], ACCENT_PINK)
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=radius, color=ACCENT_PINK, fill=True, fill_color=ACCENT_PINK,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_h, max_width=320),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Avg Rent ($/sqft)": d["avg_rent_sqft"],
        "Key Stores": d["key_stores"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "luxury_shopping_streets.csv",
                      f"Download {len(df)} Luxury Shopping Streets (CSV)", "dl_luxury")


def _render_trading_posts():
    """Mode 10: Historic Trading Posts."""
    data = HISTORIC_TRADING_POSTS
    countries = list(set(d["country"] for d in data))
    networks = list(set(d["network"] for d in data))

    network_colors = {
        "Hanseatic League": "#06b6d4",
        "Silk Road": "#f59e0b",
        "Maritime Spice Route": "#10b981",
        "East India Company": "#ec4899",
        "Canton Trade System": "#ef4444",
        "Hudson's Bay Company": "#8b5cf6",
        "Santa Fe Trail": "#f97316",
        "Coffee Trade": "#92400e",
        "Trans-Saharan Trade": "#eab308",
        "Indian Ocean Trade": "#14b8a6",
        "Dutch East India Company (VOC)": "#3b82f6",
        "Spice Trade / Colonial": "#a855f7",
        "Portuguese Maritime Trade": "#22c55e",
        "Gold Coast / Slave Trade": "#f43f5e",
        "Russian-American Company": "#64748b",
        "Silk Road / Mediterranean": "#d97706",
    }

    _show_stats([
        ("Posts Mapped", len(data)),
        ("Countries", len(countries)),
        ("Trade Networks", len(networks)),
        ("Eras Covered", "200 BCE - 1999"),
    ])

    st.markdown("---")
    st.markdown("#### Historic Trading Posts Map")

    m = _build_map(data)
    for item in data:
        clr = network_colors.get(item["network"], ACCENT_ROSE)
        popup_h = _popup_html([
            ("Post", item["name"]), ("City", item["city"]),
            ("Country", item["country"]), ("Era", item["era"]),
            ("Network", item["network"]), ("Notes", item["notes"]),
        ], clr)
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=9, color=clr, fill=True, fill_color=clr,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_h, max_width=320),
            tooltip=html_module.escape(item["name"]),
        ).add_to(m)
    _render_map(m)

    _legend({k: v for k, v in network_colors.items() if k in set(d["network"] for d in data)})

    df = pd.DataFrame([{
        "Name": d["name"], "City": d["city"], "Country": d["country"],
        "Era": d["era"], "Network": d["network"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _download_section(df, "historic_trading_posts.csv",
                      f"Download {len(df)} Historic Trading Posts (CSV)", "dl_trading")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def render_market_maps_tab():
    """Main render function for the Markets & Bazaars Maps tab."""

    # -- Header --
    st.markdown(
        '<div class="tab-header amber">'
        "<h4>\U0001f3ea Markets & Bazaars Maps</h4>"
        "<p>World markets, souks, bazaars, and trading posts</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # -- Mode selector --
    st.markdown("#### Explore World Markets")
    mode = st.selectbox(
        "Map Mode",
        MAP_MODES,
        key="market_maps_mode",
        help="Choose a market category to explore on the map.",
    )

    # -- Mode description --
    color = MODE_COLORS.get(mode, ACCENT_AMBER)
    desc = MODE_DESCRIPTIONS.get(mode, "")
    st.markdown(
        f'<div style="border-left:3px solid {color}; padding:0.5rem 0.75rem; '
        f'margin:0.5rem 0 1rem; background:rgba(15,23,42,0.4); border-radius:0 6px 6px 0;">'
        f'<span style="color:{color}; font-weight:600;">{html_module.escape(mode)}</span><br/>'
        f'<span style="color:#8b97b0; font-size:0.85rem;">{html_module.escape(desc)}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # -- Dispatch to mode renderer --
    mode_map = {
        "Grand Bazaars & Souks": _render_grand_bazaars,
        "Famous Flea Markets": _render_flea_markets,
        "Floating Markets": _render_floating_markets,
        "Fish Markets": _render_fish_markets,
        "Night Markets": _render_night_markets,
        "Spice Markets": _render_spice_markets,
        "Christmas Markets": _render_christmas_markets,
        "Stock Exchanges": _render_stock_exchanges,
        "Luxury Shopping Streets": _render_luxury_streets,
        "Historic Trading Posts": _render_trading_posts,
    }

    renderer = mode_map.get(mode)
    if renderer:
        renderer()
