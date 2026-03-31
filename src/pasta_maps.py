"""
Pasta & Noodle World Explorer module for TerraScout AI.
Curated maps of pasta regions, noodle traditions, dumpling origins,
famous restaurants, museums, and grain history worldwide.
All data is preset (no external API needed for base data).
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import html as html_module
import streamlit.components.v1 as components


# ═══════════════════════════════════════════
# MAP MODES
# ═══════════════════════════════════════════
MAP_MODES = [
    "Italian Pasta Regions",
    "Ancient Grain Origins",
    "Noodle Traditions of Asia",
    "Pasta Museums & Factories",
    "Famous Italian Restaurants",
    "Dumpling World Tour",
    "Street Food Noodle Markets",
    "Couscous & Semolina Trail",
    "Gnocchi & Potato Pasta",
    "Pasta Shapes Encyclopedia Map",
]

# ═══════════════════════════════════════════
# MARKER COLORS PER MODE
# ═══════════════════════════════════════════
MODE_COLORS = {
    "Italian Pasta Regions": "#f59e0b",
    "Ancient Grain Origins": "#8b5cf6",
    "Noodle Traditions of Asia": "#ef4444",
    "Pasta Museums & Factories": "#06b6d4",
    "Famous Italian Restaurants": "#ec4899",
    "Dumpling World Tour": "#10b981",
    "Street Food Noodle Markets": "#f97316",
    "Couscous & Semolina Trail": "#a855f7",
    "Gnocchi & Potato Pasta": "#38bdf8",
    "Pasta Shapes Encyclopedia Map": "#facc15",
}


# ═══════════════════════════════════════════
# PRESET DATA — MODE 1: ITALIAN PASTA REGIONS
# ═══════════════════════════════════════════
ITALIAN_PASTA_REGIONS = [
    {"name": "Carbonara", "region": "Lazio", "city": "Rome", "lat": 41.9028, "lon": 12.4964,
     "desc": "Guanciale, egg yolk, Pecorino Romano, black pepper. The iconic Roman first course."},
    {"name": "Pesto alla Genovese", "region": "Liguria", "city": "Genova", "lat": 44.4056, "lon": 8.9463,
     "desc": "Fresh basil, pine nuts, garlic, Parmigiano, Pecorino, olive oil. Birthplace of pesto."},
    {"name": "Ragù alla Bolognese", "region": "Emilia-Romagna", "city": "Bologna", "lat": 44.4949, "lon": 11.3426,
     "desc": "Slow-cooked meat sauce with soffritto, tomato, wine. Served on tagliatelle, never spaghetti."},
    {"name": "Cacio e Pepe", "region": "Lazio", "city": "Rome", "lat": 41.8967, "lon": 12.4822,
     "desc": "Pecorino Romano and black pepper emulsified with pasta water. Ancient shepherd's pasta."},
    {"name": "Amatriciana", "region": "Lazio", "city": "Amatrice", "lat": 42.6280, "lon": 13.2903,
     "desc": "Guanciale, tomato, Pecorino Romano, chili. Originally from the hill town of Amatrice."},
    {"name": "Orecchiette con Cime di Rapa", "region": "Puglia", "city": "Bari", "lat": 41.1171, "lon": 16.8719,
     "desc": "Ear-shaped pasta with turnip greens, anchovies, garlic, chili. Iconic Puglian dish."},
    {"name": "Pici all'Aglione", "region": "Toscana", "city": "Siena", "lat": 43.3188, "lon": 11.3308,
     "desc": "Hand-rolled thick spaghetti with garlic-tomato sauce. Tuscan peasant tradition."},
    {"name": "Trofie al Pesto", "region": "Liguria", "city": "Recco", "lat": 44.3614, "lon": 9.1453,
     "desc": "Small twisted pasta with pesto, potatoes, and green beans. Ligurian coastal classic."},
    {"name": "Busiate al Pesto Trapanese", "region": "Sicilia", "city": "Trapani", "lat": 38.0174, "lon": 12.5365,
     "desc": "Corkscrew pasta with tomato-almond-basil pesto. Sicilian-North African fusion."},
    {"name": "Culurgiones", "region": "Sardegna", "city": "Ogliastra", "lat": 39.9285, "lon": 9.5003,
     "desc": "Sardinian stuffed pasta with potato, pecorino, mint. Intricate wheat-ear closure."},
    {"name": "Pizzoccheri", "region": "Lombardia", "city": "Teglio", "lat": 46.1728, "lon": 10.0680,
     "desc": "Buckwheat tagliatelle with Casera cheese, cabbage, potatoes. Alpine Valtellina staple."},
    {"name": "Bigoli in Salsa", "region": "Veneto", "city": "Padova", "lat": 45.4064, "lon": 11.8768,
     "desc": "Thick bronze-extruded spaghetti with onion and sardine sauce. Venetian tradition."},
    {"name": "Tortellini in Brodo", "region": "Emilia-Romagna", "city": "Modena", "lat": 44.6471, "lon": 10.9252,
     "desc": "Tiny filled pasta in capon broth. Modena and Bologna debate the true origin."},
    {"name": "Spaghetti alle Vongole", "region": "Campania", "city": "Napoli", "lat": 40.8518, "lon": 14.2681,
     "desc": "Spaghetti with clams, garlic, white wine, parsley. Neapolitan seaside masterpiece."},
    {"name": "Pasta alla Norma", "region": "Sicilia", "city": "Catania", "lat": 37.5079, "lon": 15.0830,
     "desc": "Rigatoni with fried eggplant, tomato, ricotta salata. Named after Bellini's opera."},
    {"name": "Canederli", "region": "Trentino-Alto Adige", "city": "Bolzano", "lat": 46.4983, "lon": 11.3548,
     "desc": "Bread dumplings in broth, a German-Italian crossover from the Dolomites."},
    {"name": "Fregola con Arselle", "region": "Sardegna", "city": "Cagliari", "lat": 39.2238, "lon": 9.1217,
     "desc": "Toasted semolina granules with clams. Sardinian couscous-like pasta with seafood."},
    {"name": "Paccheri alla Genovese", "region": "Campania", "city": "Napoli", "lat": 40.8366, "lon": 14.2495,
     "desc": "Large tube pasta with slow-cooked onion and beef ragu. Neapolitan Sunday tradition."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 2: ANCIENT GRAIN ORIGINS
# ═══════════════════════════════════════════
ANCIENT_GRAIN_ORIGINS = [
    {"name": "Durum Wheat (Triticum durum)", "lat": 36.8, "lon": 38.0,
     "desc": "Domesticated in the Fertile Crescent ~7000 BCE. The essential grain for pasta and semolina."},
    {"name": "Einkorn (Triticum monococcum)", "lat": 37.5, "lon": 39.5,
     "desc": "One of the first cultivated wheats, ~7500 BCE in southeastern Turkey. Low gluten ancestor."},
    {"name": "Emmer Wheat (Triticum dicoccum)", "lat": 36.0, "lon": 37.0,
     "desc": "Domesticated ~8000 BCE near Karacadag, Turkey. Parent of modern durum wheat."},
    {"name": "Spelt (Triticum spelta)", "lat": 47.5, "lon": 9.0,
     "desc": "Ancient hulled wheat popular in Central Europe since 5000 BCE. Makes nutty, hearty pasta."},
    {"name": "Khorasan Wheat (Kamut)", "lat": 35.7, "lon": 51.4,
     "desc": "Large-kernel ancient wheat from Iran/Egypt region. Buttery flavor, high protein."},
    {"name": "Common Wheat (Triticum aestivum)", "lat": 38.5, "lon": 43.0,
     "desc": "Hexaploid wheat from hybridization ~8000 years ago in the Caucasus. Bread and soft flour."},
    {"name": "Rice Noodle Origins - Yangtze Delta", "lat": 30.6, "lon": 114.3,
     "desc": "Rice cultivation began ~9000 years ago in the Yangtze River valley, giving rise to rice noodles."},
    {"name": "Buckwheat (Fagopyrum esculentum)", "lat": 27.5, "lon": 100.0,
     "desc": "Domesticated ~6000 BCE in Yunnan, China. Used for Japanese soba and Italian pizzoccheri."},
    {"name": "Semolina Milling - Ancient Egypt", "lat": 29.9, "lon": 31.1,
     "desc": "Ancient Egyptians developed milling techniques for coarse semolina flour ~3000 BCE."},
    {"name": "Sorghum (Sorghum bicolor)", "lat": 12.0, "lon": 32.0,
     "desc": "Domesticated in Sudan ~5000 years ago. Used for gluten-free pasta and couscous in Africa."},
    {"name": "Maize (Zea mays)", "lat": 17.0, "lon": -96.5,
     "desc": "Domesticated in Oaxaca, Mexico ~9000 years ago. Corn pasta and tortillas."},
    {"name": "Millet Noodles - Yellow River", "lat": 34.0, "lon": 109.0,
     "desc": "Millet cultivated along the Yellow River ~8000 BCE. The earliest Chinese noodle grain."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 3: NOODLE TRADITIONS OF ASIA
# ═══════════════════════════════════════════
NOODLE_TRADITIONS_ASIA = [
    {"name": "Lamian (Hand-Pulled Noodles)", "city": "Lanzhou", "country": "China", "lat": 36.0611, "lon": 103.8343,
     "desc": "Hand-pulled noodles in beef broth. Lanzhou lamian is China's most iconic noodle soup."},
    {"name": "Dao Xiao Mian (Knife-Cut Noodles)", "city": "Taiyuan", "country": "China", "lat": 37.8706, "lon": 112.5489,
     "desc": "Shanxi specialty: noodles shaved from dough block directly into boiling water."},
    {"name": "Dan Dan Mian", "city": "Chengdu", "country": "China", "lat": 30.5728, "lon": 104.0668,
     "desc": "Sichuan spicy noodles with chili oil, preserved vegetables, minced pork, Sichuan pepper."},
    {"name": "Zhajiangmian (Fried Sauce Noodles)", "city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074,
     "desc": "Thick wheat noodles with soybean paste sauce, cucumber, radish. Beijing comfort food."},
    {"name": "Ramen", "city": "Fukuoka", "country": "Japan", "lat": 33.5904, "lon": 130.4017,
     "desc": "Tonkotsu ramen originated here. Rich pork bone broth, thin noodles, chashu, eggs."},
    {"name": "Udon", "city": "Takamatsu", "country": "Japan", "lat": 34.3401, "lon": 134.0434,
     "desc": "Sanuki udon from Kagawa prefecture. Thick, chewy wheat noodles in dashi broth."},
    {"name": "Soba", "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503,
     "desc": "Buckwheat noodles served hot or cold with tsuyu. Edo-period Tokyo tradition."},
    {"name": "Somen", "city": "Tatsuno", "country": "Japan", "lat": 34.8580, "lon": 134.5445,
     "desc": "Ultra-thin wheat noodles served ice-cold in summer. Banshu tradition since the 1400s."},
    {"name": "Pho", "city": "Hanoi", "country": "Vietnam", "lat": 21.0285, "lon": 105.8542,
     "desc": "Rice noodle soup with beef or chicken, star anise, cinnamon, herbs. Vietnam's national dish."},
    {"name": "Bun Bo Hue", "city": "Hue", "country": "Vietnam", "lat": 16.4637, "lon": 107.5909,
     "desc": "Spicy beef noodle soup with lemongrass, shrimp paste. Central Vietnamese royal cuisine."},
    {"name": "Pad Thai", "city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018,
     "desc": "Stir-fried rice noodles with tamarind, fish sauce, peanuts, shrimp, bean sprouts."},
    {"name": "Japchae", "city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780,
     "desc": "Sweet potato glass noodles stir-fried with vegetables and beef. Korean royal court dish."},
    {"name": "Naengmyeon", "city": "Pyongyang", "country": "North Korea", "lat": 39.0392, "lon": 125.7625,
     "desc": "Cold buckwheat noodles in icy beef broth. Historic dish from northern Korea."},
    {"name": "Laksa", "city": "Penang", "country": "Malaysia", "lat": 5.4164, "lon": 100.3327,
     "desc": "Spicy coconut curry or sour tamarind broth with rice noodles. Peranakan heritage."},
    {"name": "Mohinga", "city": "Yangon", "country": "Myanmar", "lat": 16.8661, "lon": 96.1951,
     "desc": "Fish-based rice noodle soup with banana stem, lemongrass. Myanmar's national dish."},
    {"name": "Khao Soi", "city": "Chiang Mai", "country": "Thailand", "lat": 18.7883, "lon": 98.9853,
     "desc": "Coconut curry noodle soup with crispy egg noodle topping. Northern Thai-Burmese specialty."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 4: PASTA MUSEUMS & FACTORIES
# ═══════════════════════════════════════════
PASTA_MUSEUMS_FACTORIES = [
    {"name": "National Pasta Museum (Museo Nazionale delle Paste Alimentari)", "city": "Rome", "lat": 41.9009, "lon": 12.4833,
     "desc": "Dedicated museum chronicling 800 years of Italian pasta history. Trevi Fountain area."},
    {"name": "Barilla Headquarters & Visitor Center", "city": "Parma", "lat": 44.8015, "lon": 10.3279,
     "desc": "World's largest pasta producer. HQ in Parma with historical archives and pasta academy."},
    {"name": "De Cecco Factory & Museum", "city": "Fara San Martino", "lat": 42.0964, "lon": 14.2059,
     "desc": "Historic pasta factory since 1886. Spring water from the Maiella mountains for dough."},
    {"name": "Pastificio Faella", "city": "Gragnano", "lat": 40.6910, "lon": 14.5191,
     "desc": "Gragnano, the City of Pasta. Traditional bronze-die extrusion and mountain air drying."},
    {"name": "Museo della Pasta - Collecchio", "city": "Collecchio", "lat": 44.7479, "lon": 10.2188,
     "desc": "Barilla pasta museum near Parma with exhibits on durum wheat cultivation and pasta making."},
    {"name": "Pastificio Gentile", "city": "Gragnano", "lat": 40.6880, "lon": 14.5225,
     "desc": "Artisan pasta maker since 1876 in the historic pasta capital. IGP certified Gragnano pasta."},
    {"name": "Rummo Pasta Factory", "city": "Benevento", "lat": 41.1298, "lon": 14.7828,
     "desc": "Family pasta maker since 1846. Famous for Lenta Lavorazione slow-crafting process."},
    {"name": "Voiello Pasta - Torre Annunziata", "city": "Torre Annunziata", "lat": 40.7571, "lon": 14.4519,
     "desc": "Historic Neapolitan brand since 1879. Premium durum wheat pasta from Campania."},
    {"name": "Cup Noodles Museum", "city": "Yokohama", "lat": 35.4536, "lon": 139.6380,
     "desc": "Interactive museum celebrating Momofuku Ando's invention of instant ramen in 1958."},
    {"name": "Shin-Yokohama Ramen Museum", "city": "Yokohama", "lat": 35.5103, "lon": 139.6173,
     "desc": "Food theme park recreating 1958 Tokyo streetscape with ramen shops from across Japan."},
    {"name": "Cup Noodles Museum Osaka Ikeda", "city": "Osaka", "lat": 34.8225, "lon": 135.4278,
     "desc": "Original birthplace museum of instant ramen. Make your own Cup Noodles."},
    {"name": "Pasta Museum of Imperia", "city": "Imperia", "lat": 43.8857, "lon": 8.0265,
     "desc": "Museo dell'Olivo e dell'Olio with pasta-making exhibits in the Ligurian Riviera."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 5: FAMOUS ITALIAN RESTAURANTS
# ═══════════════════════════════════════════
FAMOUS_ITALIAN_RESTAURANTS = [
    {"name": "Roscioli", "city": "Rome", "lat": 41.8936, "lon": 12.4742,
     "desc": "Legendary for cacio e pepe, carbonara, and amatriciana. Roman pasta temple near Campo de' Fiori."},
    {"name": "Da Felice a Testaccio", "city": "Rome", "lat": 41.8757, "lon": 12.4760,
     "desc": "Famous for tonnarelli cacio e pepe. A Testaccio institution since 1936."},
    {"name": "Trattoria da Enzo al 29", "city": "Rome", "lat": 41.8862, "lon": 12.4729,
     "desc": "Trastevere gem. Queue-worthy carbonara and cacio e pepe. Classic Roman trattoria."},
    {"name": "Osteria Francescana", "city": "Modena", "lat": 44.6453, "lon": 10.9219,
     "desc": "Massimo Bottura's 3-Michelin-star restaurant. Deconstructed tortellini and ragu."},
    {"name": "Trattoria da Nennella", "city": "Napoli", "lat": 40.8450, "lon": 14.2515,
     "desc": "Raucous, beloved Quartieri Spagnoli trattoria. Legendary pasta e patate and paccheri."},
    {"name": "Trattoria Sostanza", "city": "Firenze", "lat": 43.7738, "lon": 11.2465,
     "desc": "Florence since 1869. Famous butter pasta and artichoke omelette. No-frills perfection."},
    {"name": "Trattoria dall'Oste", "city": "Firenze", "lat": 43.7743, "lon": 11.2538,
     "desc": "Hearty Tuscan pici and pappardelle al cinghiale. Bistecca and handmade pasta."},
    {"name": "Pipero Roma", "city": "Rome", "lat": 41.9050, "lon": 12.4848,
     "desc": "Cacio e pepe perfected. Michelin-starred contemporary Roman pasta near Via del Corso."},
    {"name": "Il Pagliaccio", "city": "Rome", "lat": 41.8966, "lon": 12.4712,
     "desc": "2-Michelin-star creative Italian. Anthony Genovese's pasta tasting menus."},
    {"name": "Antica Focacceria San Francesco", "city": "Palermo", "lat": 38.1157, "lon": 13.3615,
     "desc": "Since 1834. Iconic Sicilian street food pasta, arancini, and panelle in historic setting."},
    {"name": "Trattoria Mario", "city": "Firenze", "lat": 43.7753, "lon": 11.2527,
     "desc": "Communal tables since 1953. Ribollita and pappardelle. Florence market lunch legend."},
    {"name": "Da Michele", "city": "Napoli", "lat": 40.8497, "lon": 14.2625,
     "desc": "While famous for pizza, also serves classic Neapolitan pasta dishes since 1870."},
    {"name": "Ristorante Diana", "city": "Bologna", "lat": 44.4965, "lon": 11.3467,
     "desc": "Bolognese institution since 1909. Tagliatelle al ragu and tortellini in brodo."},
    {"name": "Le Virtù", "city": "Pescara", "lat": 42.4618, "lon": 14.2134,
     "desc": "Abruzzese tradition. Named after the spring soup mixing 7 dried and 7 fresh pasta shapes."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 6: DUMPLING WORLD TOUR
# ═══════════════════════════════════════════
DUMPLING_WORLD_TOUR = [
    {"name": "Ravioli", "region": "Italy", "city": "Genova", "lat": 44.4056, "lon": 8.9463,
     "desc": "Filled pasta parcels. Ligurian ravioli with meat and greens date to the 13th century."},
    {"name": "Tortellini", "region": "Italy", "city": "Bologna", "lat": 44.4949, "lon": 11.3426,
     "desc": "Navel-shaped pasta filled with pork, prosciutto, mortadella, Parmigiano. Emilian legend."},
    {"name": "Pierogi", "region": "Poland", "city": "Krakow", "lat": 50.0647, "lon": 19.9450,
     "desc": "Stuffed with potato-cheese, sauerkraut, meat, or fruit. Poland's most beloved dumpling."},
    {"name": "Gyoza", "region": "Japan", "city": "Utsunomiya", "lat": 36.5551, "lon": 139.8829,
     "desc": "Pan-fried Japanese dumplings with pork and cabbage. Utsunomiya is Japan's gyoza capital."},
    {"name": "Jiaozi", "region": "China", "city": "Xi'an", "lat": 34.2658, "lon": 108.9541,
     "desc": "Chinese dumplings with over 1,800 years of history. Boiled, steamed, or pan-fried."},
    {"name": "Xiaolongbao", "region": "China", "city": "Shanghai", "lat": 31.2304, "lon": 121.4737,
     "desc": "Soup dumplings with thin skin and hot broth inside. Shanghai's most famous snack."},
    {"name": "Momo", "region": "Nepal/Tibet", "city": "Kathmandu", "lat": 27.7172, "lon": 85.3240,
     "desc": "Tibetan/Nepalese steamed dumplings with spiced meat or vegetables. Himalayan street food."},
    {"name": "Empanada", "region": "Argentina", "city": "Buenos Aires", "lat": -34.6037, "lon": -58.3816,
     "desc": "Baked or fried pastry turnovers with beef, onion, egg, olive. Brought by Spanish colonists."},
    {"name": "Manti", "region": "Turkey/Central Asia", "city": "Kayseri", "lat": 38.7312, "lon": 35.4787,
     "desc": "Tiny Turkish dumplings with spiced lamb, topped with yogurt and chili butter."},
    {"name": "Wonton", "region": "China", "city": "Guangzhou", "lat": 23.1291, "lon": 113.2644,
     "desc": "Cantonese wonton in shrimp broth. Thin-skinned parcels with shrimp and pork filling."},
    {"name": "Pelmeni", "region": "Russia", "city": "Yekaterinburg", "lat": 56.8389, "lon": 60.6057,
     "desc": "Siberian meat dumplings with beef, pork, or lamb. Served with sour cream and vinegar."},
    {"name": "Varenyky", "region": "Ukraine", "city": "Kyiv", "lat": 50.4501, "lon": 30.5234,
     "desc": "Ukrainian dumplings stuffed with potato, cheese, cherries, or cabbage. National treasure."},
    {"name": "Khinkali", "region": "Georgia", "city": "Tbilisi", "lat": 41.7151, "lon": 44.8271,
     "desc": "Georgian soup dumplings with spiced meat, twisted top knob. Eaten by hand."},
    {"name": "Baozi", "region": "China", "city": "Tianjin", "lat": 39.3434, "lon": 117.3616,
     "desc": "Steamed filled buns. Tianjin's Goubuli baozi are among China's most famous."},
    {"name": "Mandu", "region": "South Korea", "city": "Seoul", "lat": 37.5665, "lon": 126.9780,
     "desc": "Korean dumplings with tofu, kimchi, pork, glass noodles. Steamed, boiled, or pan-fried."},
    {"name": "Samosa", "region": "India", "city": "Delhi", "lat": 28.6139, "lon": 77.2090,
     "desc": "Crispy pastry triangles with spiced potato, peas. Originated from Central Asian sambosa."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 7: STREET FOOD NOODLE MARKETS
# ═══════════════════════════════════════════
STREET_FOOD_NOODLE_MARKETS = [
    {"name": "Yaowarat (Chinatown)", "city": "Bangkok", "country": "Thailand", "lat": 13.7407, "lon": 100.5100,
     "desc": "Bangkok's legendary noodle street. Pad thai, boat noodles, kuay jab, ba mee at every corner."},
    {"name": "Chatuchak Market", "city": "Bangkok", "country": "Thailand", "lat": 13.7999, "lon": 100.5503,
     "desc": "Massive weekend market with pad thai stalls, boat noodles, and noodle soup vendors."},
    {"name": "Temple Street Night Market", "city": "Hong Kong", "country": "China", "lat": 22.3050, "lon": 114.1694,
     "desc": "Wonton noodles, cart noodles, and dai pai dong stalls. Kowloon's noodle paradise."},
    {"name": "Mong Kok Noodle District", "city": "Hong Kong", "country": "China", "lat": 22.3193, "lon": 114.1694,
     "desc": "Dense neighborhood of wonton noodle shops, beef brisket noodles, and congee-noodle joints."},
    {"name": "Tsukiji Outer Market", "city": "Tokyo", "country": "Japan", "lat": 35.6654, "lon": 139.7707,
     "desc": "Soba, udon, and ramen stalls alongside fresh seafood. Tokyo's foodie pilgrimage site."},
    {"name": "Shinjuku Omoide Yokocho", "city": "Tokyo", "country": "Japan", "lat": 35.6938, "lon": 139.6989,
     "desc": "Memory Lane / Piss Alley. Tiny ramen and yakitori stalls under the train tracks since 1946."},
    {"name": "Maxwell Food Centre", "city": "Singapore", "country": "Singapore", "lat": 1.2804, "lon": 103.8448,
     "desc": "Iconic hawker center with prawn mee, laksa, bak chor mee, and wonton noodles."},
    {"name": "Old Airport Road Food Centre", "city": "Singapore", "country": "Singapore", "lat": 1.3085, "lon": 103.8832,
     "desc": "Largest hawker center in Singapore. Famous for Hokkien mee, char kway teow, lor mee."},
    {"name": "Gwangjang Market", "city": "Seoul", "country": "South Korea", "lat": 37.5700, "lon": 126.9990,
     "desc": "Korea's oldest market. Kalguksu knife-cut noodles, japchae, and bindaetteok galore."},
    {"name": "Jiufen Old Street", "city": "Jiufen", "country": "Taiwan", "lat": 25.1094, "lon": 121.8443,
     "desc": "Mountain village with famous noodle shops. Taro ball soup and beef noodle stalls."},
    {"name": "Jalan Alor", "city": "Kuala Lumpur", "country": "Malaysia", "lat": 3.1460, "lon": 101.7085,
     "desc": "Night food street with Hokkien mee, prawn noodles, char kway teow, and pan mee."},
    {"name": "Bến Thành Market", "city": "Ho Chi Minh City", "country": "Vietnam", "lat": 10.7725, "lon": 106.6980,
     "desc": "Bustling market with pho stalls, bun bo Hue, and banh canh. Vietnamese noodle central."},
    {"name": "Phsar Thmei (Central Market)", "city": "Phnom Penh", "country": "Cambodia", "lat": 11.5705, "lon": 104.9211,
     "desc": "Art deco market with num banh chok (Khmer noodles), kuy teav, and mi kola."},
    {"name": "Old Quarter Street Food", "city": "Hanoi", "country": "Vietnam", "lat": 21.0340, "lon": 105.8500,
     "desc": "Labyrinthine alleys of pho, bun cha, bun rieu, and pho cuon. Hanoi's soul food district."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 8: COUSCOUS & SEMOLINA TRAIL
# ═══════════════════════════════════════════
COUSCOUS_SEMOLINA_TRAIL = [
    {"name": "Couscous Royal", "city": "Fez", "country": "Morocco", "lat": 34.0181, "lon": -5.0078,
     "desc": "Friday couscous tradition with seven vegetables, lamb, and chickpeas. Moroccan national dish."},
    {"name": "Couscous aux Merguez", "city": "Tunis", "country": "Tunisia", "lat": 36.8065, "lon": 10.1815,
     "desc": "Spicy harissa-laced couscous with merguez sausage. Tunisia claims couscous origins."},
    {"name": "Couscous Kabyle", "city": "Tizi Ouzou", "country": "Algeria", "lat": 36.7169, "lon": 4.0497,
     "desc": "Berber couscous steamed with turnips, chickpeas, and buttermilk. Kabylie mountain tradition."},
    {"name": "Couscous Tfaya", "city": "Marrakech", "country": "Morocco", "lat": 31.6295, "lon": -7.9811,
     "desc": "Sweet couscous with caramelized onions, raisins, and cinnamon. Festive Marrakchi style."},
    {"name": "Libyan Bazin & Couscous", "city": "Tripoli", "country": "Libya", "lat": 32.9022, "lon": 13.1800,
     "desc": "Libyan couscous with lamb stew and hard-boiled eggs. Also bazin dough with sauce."},
    {"name": "Cous Cous Trapanese", "city": "Trapani", "country": "Italy (Sicily)", "lat": 38.0174, "lon": 12.5365,
     "desc": "Sicilian couscous with fish broth and seafood. Arab-Norman heritage. Annual Cous Cous Fest."},
    {"name": "Maftoul (Palestinian Couscous)", "city": "Ramallah", "country": "Palestine", "lat": 31.9038, "lon": 35.2034,
     "desc": "Hand-rolled large-grain couscous steamed with chicken and chickpeas. Levantine tradition."},
    {"name": "Moghrabieh", "city": "Beirut", "country": "Lebanon", "lat": 33.8938, "lon": 35.5018,
     "desc": "Lebanese pearl couscous with chicken, chickpeas, cinnamon, caraway. Festive winter dish."},
    {"name": "Israeli Couscous (Ptitim)", "city": "Tel Aviv", "country": "Israel", "lat": 32.0853, "lon": 34.7818,
     "desc": "Toasted pearl pasta invented in the 1950s as a rice substitute. Now a global pantry staple."},
    {"name": "Senegalese Thieboudienne", "city": "Dakar", "country": "Senegal", "lat": 14.7167, "lon": -17.4677,
     "desc": "Broken rice and fish, but also millet couscous dishes. West African semolina traditions."},
    {"name": "Mauritanian Couscous", "city": "Nouakchott", "country": "Mauritania", "lat": 18.0735, "lon": -15.9582,
     "desc": "Millet and sorghum couscous with camel meat or goat stew. Saharan desert tradition."},
    {"name": "Egyptian Moghrabieh", "city": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357,
     "desc": "Large-grain couscous in rich tomato-onion broth. Egyptian comfort food from ancient grains."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 9: GNOCCHI & POTATO PASTA
# ═══════════════════════════════════════════
GNOCCHI_POTATO_PASTA = [
    {"name": "Gnocchi di Patate", "city": "Verona", "country": "Italy", "lat": 45.4384, "lon": 10.9916,
     "desc": "Verona's Venerdì Gnocolar carnival tradition. Potato gnocchi became popular after 1800s."},
    {"name": "Gnocchi alla Sorrentina", "city": "Sorrento", "country": "Italy", "lat": 40.6263, "lon": 14.3758,
     "desc": "Baked gnocchi with tomato sauce, mozzarella, basil. Sorrentine coast classic."},
    {"name": "Gnocchi alla Romana", "city": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964,
     "desc": "Semolina discs baked with butter and Parmigiano. Not potato-based, ancient Roman origin."},
    {"name": "Gnocchi di Zucca", "city": "Mantova", "country": "Italy", "lat": 45.1564, "lon": 10.7915,
     "desc": "Pumpkin gnocchi with butter and sage. Renaissance Mantuan tradition from the Gonzaga court."},
    {"name": "Gnudi (Ricotta Dumplings)", "city": "Firenze", "country": "Italy", "lat": 43.7696, "lon": 11.2558,
     "desc": "Naked ravioli - ricotta and spinach dumplings without the pasta wrapper. Tuscan lightness."},
    {"name": "Kopytka", "city": "Warsaw", "country": "Poland", "lat": 52.2297, "lon": 21.0122,
     "desc": "Polish potato dumplings similar to gnocchi. Served with butter, breadcrumbs, or mushroom sauce."},
    {"name": "Kartoffelknoedel", "city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820,
     "desc": "Bavarian potato dumplings served with roast pork and gravy. German Sunday lunch staple."},
    {"name": "Halusky", "city": "Bratislava", "country": "Slovakia", "lat": 48.1486, "lon": 17.1077,
     "desc": "Bryndzove halusky: small potato dumplings with sheep cheese and bacon. Slovak national dish."},
    {"name": "Noquis (Argentine Gnocchi)", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816,
     "desc": "29th of the month gnocchi tradition. Italian immigrants brought gnocchi to Argentina."},
    {"name": "Nhoque (Brazilian Gnocchi)", "city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333,
     "desc": "Italian-Brazilian tradition: gnocchi on the 29th with coins under the plate for luck."},
    {"name": "Schupfnudeln", "city": "Stuttgart", "country": "Germany", "lat": 48.7758, "lon": 9.1829,
     "desc": "Swabian finger-shaped potato noodles pan-fried with sauerkraut or in sweet cinnamon."},
    {"name": "Kluski Slaskie", "city": "Wroclaw", "country": "Poland", "lat": 51.1079, "lon": 17.0385,
     "desc": "Silesian dumplings with a thumb indent to hold gravy. Potato and flour dough."},
    {"name": "Canederli / Knoedel", "city": "Bolzano", "country": "Italy", "lat": 46.4983, "lon": 11.3548,
     "desc": "Bread dumplings from South Tyrol. Speck, spinach, or cheese versions in broth or with butter."},
]

# ═══════════════════════════════════════════
# PRESET DATA — MODE 10: PASTA SHAPES ENCYCLOPEDIA MAP
# ═══════════════════════════════════════════
PASTA_SHAPES_ENCYCLOPEDIA = [
    {"name": "Orecchiette", "region": "Puglia", "city": "Bari", "lat": 41.1171, "lon": 16.8719,
     "desc": "Ear-shaped pasta. Women make them by hand on boards in Bari Vecchia's old streets."},
    {"name": "Pappardelle", "region": "Toscana", "city": "Firenze", "lat": 43.7696, "lon": 11.2558,
     "desc": "Wide ribbon pasta from pappare (to gobble up). Perfect with wild boar ragu."},
    {"name": "Trofie", "region": "Liguria", "city": "Genova", "lat": 44.4056, "lon": 8.9463,
     "desc": "Small twisted pasta rolled by hand. Traditional shape for Genovese pesto."},
    {"name": "Busiate", "region": "Sicilia", "city": "Trapani", "lat": 38.0174, "lon": 12.5365,
     "desc": "Corkscrew pasta wound around a knitting needle (busa). Served with pesto trapanese."},
    {"name": "Strozzapreti", "region": "Emilia-Romagna", "city": "Rimini", "lat": 44.0678, "lon": 12.5695,
     "desc": "Priest-stranglers: twisted hand-rolled pasta. Legend says priests choked eating them too fast."},
    {"name": "Cavatelli", "region": "Molise", "city": "Campobasso", "lat": 41.5603, "lon": 14.6627,
     "desc": "Small shell-like pasta pressed with two fingers. Ancient shape from southern Italy."},
    {"name": "Rigatoni", "region": "Lazio", "city": "Rome", "lat": 41.9028, "lon": 12.4964,
     "desc": "Ridged tubes that grip sauce perfectly. Essential for amatriciana and pajata."},
    {"name": "Paccheri", "region": "Campania", "city": "Napoli", "lat": 40.8518, "lon": 14.2681,
     "desc": "Large smooth tubes. Legend: smugglers hid garlic cloves inside to evade Austrian taxes."},
    {"name": "Mafaldine", "region": "Campania", "city": "Napoli", "lat": 40.8600, "lon": 14.2500,
     "desc": "Ruffled-edge ribbons named after Princess Mafalda of Savoy. Neapolitan royal pasta."},
    {"name": "Casarecce", "region": "Sicilia", "city": "Palermo", "lat": 38.1157, "lon": 13.3615,
     "desc": "S-shaped rolled tubes meaning homemade. Sicilian shape that cups chunky sauces."},
    {"name": "Pici", "region": "Toscana", "city": "Siena", "lat": 43.3188, "lon": 11.3308,
     "desc": "Hand-rolled thick spaghetti. Tuscan peasant pasta, irregularly shaped, supremely satisfying."},
    {"name": "Corzetti", "region": "Liguria", "city": "Genova", "lat": 44.4200, "lon": 8.9300,
     "desc": "Stamped coin-shaped pasta with decorative imprints. Noble Ligurian tradition from the 1300s."},
    {"name": "Lorighittas", "region": "Sardegna", "city": "Morgongiori", "lat": 39.8667, "lon": 8.7667,
     "desc": "Braided ring pasta from Sardinia. Made only for All Saints Day, intricate double-strand twist."},
    {"name": "Fileja", "region": "Calabria", "city": "Tropea", "lat": 38.6776, "lon": 15.8971,
     "desc": "Calabrian hand-rolled pasta twisted around a thin rod. Served with nduja and onion sauce."},
    {"name": "Pizzoccheri", "region": "Lombardia", "city": "Teglio", "lat": 46.1728, "lon": 10.0680,
     "desc": "Short buckwheat tagliatelle. Alpine pasta layered with potatoes, cabbage, Casera cheese."},
    {"name": "Sagne 'ncannulate", "region": "Puglia", "city": "Lecce", "lat": 40.3516, "lon": 18.1718,
     "desc": "Twisted ribbon pasta from Salento. Curled around a stick, served with tomato and ricotta forte."},
]


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════
def _build_map(data: list, center: list, zoom: int, color: str, popup_fn) -> folium.Map:
    """Build a dark-themed folium map with markers from preset data."""
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Locations").add_to(m)

    for item in data:
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            continue

        popup_html = popup_fn(item)

        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(cluster)

    return m


def _popup_html(item: dict, fields: list) -> str:
    """Build a dark-themed popup HTML for a marker."""
    name = html_module.escape(str(item.get("name", "Unknown")))
    desc = html_module.escape(str(item.get("desc", "")))

    html_parts = [
        '<div style="background:#1a2235;color:#e8ecf4;padding:10px;border-radius:8px;'
        'min-width:180px;max-width:260px;font-family:sans-serif;">',
        f'<b style="font-size:0.95rem;color:#06b6d4;">{name}</b><br/>',
    ]

    for label, key in fields:
        val = item.get(key, "")
        if val:
            escaped_val = html_module.escape(str(val))
            html_parts.append(
                f'<span style="color:#8b97b0;font-size:0.78rem;">{label}: {escaped_val}</span><br/>'
            )

    html_parts.append(f'<div style="color:#a0aec0;font-size:0.76rem;margin-top:4px;">{desc}</div>')
    html_parts.append('</div>')

    return "".join(html_parts)


def _render_mode(title: str, data: list, color: str, center: list, zoom: int,
                 df_columns: list, popup_fields: list, csv_filename: str):
    """Generic renderer for any pasta map mode."""

    st.markdown(f"#### {html_module.escape(title)}")

    if not data:
        st.warning("No data available for this mode.")
        return

    # Stats row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Locations", len(data))
    with c2:
        countries = set()
        for item in data:
            for key in ("country", "region", "city"):
                val = item.get(key)
                if val:
                    countries.add(val)
                    break
        st.metric("Regions / Countries", len(countries))
    with c3:
        lats = [item["lat"] for item in data if item.get("lat")]
        if lats:
            span = max(lats) - min(lats)
            st.metric("Latitude Span", f"{span:.1f}\u00b0")
        else:
            st.metric("Latitude Span", "N/A")

    st.markdown("---")

    # Build map
    popup_fn = lambda item: _popup_html(item, popup_fields)
    m = _build_map(data, center, zoom, color, popup_fn)
    components.html(m._repr_html_(), height=500)

    st.markdown("---")

    # DataFrame
    rows = []
    for item in data:
        row = {}
        for col_label, col_key in df_columns:
            row[col_label] = item.get(col_key, "")
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # CSV download
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Locations (CSV)",
        data=csv_buf.getvalue(),
        file_name=csv_filename,
        mime="text/csv",
        key=f"pasta_dl_{csv_filename}",
    )


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_pasta_maps_tab():
    """Main render function for the Pasta & Noodle World Explorer tab."""

    # Header
    st.markdown("""
    <div class="tab-header emerald">
        <h4>\U0001f35d Pasta & Noodle World Explorer</h4>
        <p>Explore the global geography of pasta, noodles, dumplings, and grain traditions &mdash; from Italian regional specialties to Asian street food markets.</p>
    </div>
    """, unsafe_allow_html=True)

    # Mode selector
    mode = st.selectbox(
        "Map Mode",
        MAP_MODES,
        key="pasta_map_mode",
    )

    st.markdown("---")

    # ── Mode 1: Italian Pasta Regions ──
    if mode == "Italian Pasta Regions":
        _render_mode(
            title="Italian Pasta Regions",
            data=ITALIAN_PASTA_REGIONS,
            color=MODE_COLORS[mode],
            center=[42.5, 12.5],
            zoom=6,
            df_columns=[
                ("Pasta", "name"), ("Region", "region"), ("City", "city"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("Region", "region"), ("City", "city")],
            csv_filename="italian_pasta_regions.csv",
        )

    # ── Mode 2: Ancient Grain Origins ──
    elif mode == "Ancient Grain Origins":
        _render_mode(
            title="Ancient Grain Origins",
            data=ANCIENT_GRAIN_ORIGINS,
            color=MODE_COLORS[mode],
            center=[35.0, 50.0],
            zoom=3,
            df_columns=[
                ("Grain", "name"), ("Latitude", "lat"), ("Longitude", "lon"),
                ("Description", "desc"),
            ],
            popup_fields=[],
            csv_filename="ancient_grain_origins.csv",
        )

    # ── Mode 3: Noodle Traditions of Asia ──
    elif mode == "Noodle Traditions of Asia":
        _render_mode(
            title="Noodle Traditions of Asia",
            data=NOODLE_TRADITIONS_ASIA,
            color=MODE_COLORS[mode],
            center=[25.0, 110.0],
            zoom=4,
            df_columns=[
                ("Noodle", "name"), ("City", "city"), ("Country", "country"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("City", "city"), ("Country", "country")],
            csv_filename="noodle_traditions_asia.csv",
        )

    # ── Mode 4: Pasta Museums & Factories ──
    elif mode == "Pasta Museums & Factories":
        _render_mode(
            title="Pasta Museums & Factories",
            data=PASTA_MUSEUMS_FACTORIES,
            color=MODE_COLORS[mode],
            center=[40.0, 20.0],
            zoom=4,
            df_columns=[
                ("Name", "name"), ("City", "city"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("City", "city")],
            csv_filename="pasta_museums_factories.csv",
        )

    # ── Mode 5: Famous Italian Restaurants ──
    elif mode == "Famous Italian Restaurants":
        _render_mode(
            title="Famous Italian Restaurants",
            data=FAMOUS_ITALIAN_RESTAURANTS,
            color=MODE_COLORS[mode],
            center=[42.5, 12.5],
            zoom=6,
            df_columns=[
                ("Restaurant", "name"), ("City", "city"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("City", "city")],
            csv_filename="famous_italian_restaurants.csv",
        )

    # ── Mode 6: Dumpling World Tour ──
    elif mode == "Dumpling World Tour":
        _render_mode(
            title="Dumpling World Tour",
            data=DUMPLING_WORLD_TOUR,
            color=MODE_COLORS[mode],
            center=[35.0, 60.0],
            zoom=3,
            df_columns=[
                ("Dumpling", "name"), ("Region", "region"), ("City", "city"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("Region", "region"), ("City", "city")],
            csv_filename="dumpling_world_tour.csv",
        )

    # ── Mode 7: Street Food Noodle Markets ──
    elif mode == "Street Food Noodle Markets":
        _render_mode(
            title="Street Food Noodle Markets",
            data=STREET_FOOD_NOODLE_MARKETS,
            color=MODE_COLORS[mode],
            center=[15.0, 105.0],
            zoom=4,
            df_columns=[
                ("Market", "name"), ("City", "city"), ("Country", "country"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("City", "city"), ("Country", "country")],
            csv_filename="street_food_noodle_markets.csv",
        )

    # ── Mode 8: Couscous & Semolina Trail ──
    elif mode == "Couscous & Semolina Trail":
        _render_mode(
            title="Couscous & Semolina Trail",
            data=COUSCOUS_SEMOLINA_TRAIL,
            color=MODE_COLORS[mode],
            center=[32.0, 10.0],
            zoom=4,
            df_columns=[
                ("Dish", "name"), ("City", "city"), ("Country", "country"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("City", "city"), ("Country", "country")],
            csv_filename="couscous_semolina_trail.csv",
        )

    # ── Mode 9: Gnocchi & Potato Pasta ──
    elif mode == "Gnocchi & Potato Pasta":
        _render_mode(
            title="Gnocchi & Potato Pasta",
            data=GNOCCHI_POTATO_PASTA,
            color=MODE_COLORS[mode],
            center=[45.0, 15.0],
            zoom=4,
            df_columns=[
                ("Dish", "name"), ("City", "city"), ("Country", "country"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("City", "city"), ("Country", "country")],
            csv_filename="gnocchi_potato_pasta.csv",
        )

    # ── Mode 10: Pasta Shapes Encyclopedia Map ──
    elif mode == "Pasta Shapes Encyclopedia Map":
        _render_mode(
            title="Pasta Shapes Encyclopedia Map",
            data=PASTA_SHAPES_ENCYCLOPEDIA,
            color=MODE_COLORS[mode],
            center=[41.0, 13.0],
            zoom=6,
            df_columns=[
                ("Shape", "name"), ("Region", "region"), ("City", "city"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Description", "desc"),
            ],
            popup_fields=[("Region", "region"), ("City", "city")],
            csv_filename="pasta_shapes_encyclopedia.csv",
        )
