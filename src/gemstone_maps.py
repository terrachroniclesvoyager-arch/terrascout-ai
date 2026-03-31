"""
Gemstone & Crystal Explorer module for TerraScout AI.
Displays famous gemstone mines, cutting centers, and notable gem locations
worldwide on interactive dark-themed maps with preset data.
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
import requests
import html as html_module
from streamlit.components.v1 import html as st_html


# ═══════════════════════════════════════════
# GEM CATEGORY COLORS
# ═══════════════════════════════════════════
GEM_COLORS = {
    "diamond": "#b9f2ff",
    "emerald": "#10b981",
    "ruby": "#ef4444",
    "sapphire": "#3b82f6",
    "opal": "#f59e0b",
    "jade": "#22c55e",
    "amber": "#d97706",
    "turquoise": "#06b6d4",
    "pearl": "#f0f0f0",
    "cutting": "#8b5cf6",
    "crown": "#eab308",
}

# ═══════════════════════════════════════════
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════
MAP_MODES = [
    "Diamond Mines of the World",
    "Emerald Sources",
    "Ruby & Sapphire Origins",
    "Opal Mining",
    "Jade Sources",
    "Amber Deposits",
    "Turquoise Mines",
    "Pearl Farms",
    "Gem Cutting Centers",
    "Crown Jewels & Famous Gems",
]


# ═══════════════════════════════════════════
# PRESET DATA FOR EACH MODE
# ═══════════════════════════════════════════
def _get_diamond_data():
    return [
        {"name": "Cullinan Mine", "lat": -25.763, "lon": 28.526,
         "desc": "South Africa. Produced the largest gem-quality diamond ever found (3,106 carats, 1905). Now part of the Crown Jewels.",
         "country": "South Africa", "status": "Active", "notable": "Cullinan Diamond (3,106 ct)"},
        {"name": "Argyle Mine", "lat": -16.714, "lon": 128.389,
         "desc": "Western Australia. Largest source of pink and red diamonds. Closed in 2020 after 37 years.",
         "country": "Australia", "status": "Closed 2020", "notable": "Pink & red diamonds"},
        {"name": "Mirny Mine", "lat": 62.531, "lon": 113.960,
         "desc": "Yakutia, Russia. One of the largest open-pit mines ever excavated (525m deep). Operated by ALROSA.",
         "country": "Russia", "status": "Underground ops", "notable": "525m deep open pit"},
        {"name": "Orapa Mine", "lat": -21.310, "lon": 25.365,
         "desc": "Botswana. World's largest diamond mine by area. Discovered 1967, operated by Debswana.",
         "country": "Botswana", "status": "Active", "notable": "Largest by area"},
        {"name": "Jwaneng Mine", "lat": -24.523, "lon": 24.658,
         "desc": "Botswana. Richest diamond mine by value in the world. Produces high-quality gems.",
         "country": "Botswana", "status": "Active", "notable": "Richest by value"},
        {"name": "Diavik Mine", "lat": 64.496, "lon": -110.273,
         "desc": "Northwest Territories, Canada. Located on an island in Lac de Gras. Produces ~7 million carats/year.",
         "country": "Canada", "status": "Active", "notable": "7M carats/year"},
        {"name": "Ekati Mine", "lat": 64.717, "lon": -110.617,
         "desc": "Northwest Territories, Canada. First commercial diamond mine in Canada, opened 1998.",
         "country": "Canada", "status": "Active", "notable": "Canada's first diamond mine"},
        {"name": "Catoca Mine", "lat": -9.283, "lon": 20.183,
         "desc": "Lunda Sul, Angola. Fourth-largest diamond mine globally. Kimberlite pipe deposit.",
         "country": "Angola", "status": "Active", "notable": "4th largest globally"},
        {"name": "Venetia Mine", "lat": -22.426, "lon": 29.318,
         "desc": "Limpopo, South Africa. De Beers' flagship mine. Transitioning to underground in 2023.",
         "country": "South Africa", "status": "Active", "notable": "De Beers flagship"},
        {"name": "Williamson Mine", "lat": -3.671, "lon": 33.577,
         "desc": "Mwadui, Tanzania. Famous for producing the Williamson Pink Star diamond.",
         "country": "Tanzania", "status": "Active", "notable": "Williamson Pink Star"},
    ]


def _get_emerald_data():
    return [
        {"name": "Muzo Mine", "lat": 5.533, "lon": -74.107,
         "desc": "Boyaca, Colombia. Produces the finest emeralds in the world. Known for deep green color and 'gota de aceite' effect.",
         "country": "Colombia", "status": "Active", "notable": "Finest emeralds, gota de aceite"},
        {"name": "Chivor Mine", "lat": 4.867, "lon": -73.367,
         "desc": "Boyaca, Colombia. Ancient mine dating to pre-Columbian era. Known for bluish-green emeralds.",
         "country": "Colombia", "status": "Active", "notable": "Pre-Columbian origin"},
        {"name": "Coscuez Mine", "lat": 5.579, "lon": -74.048,
         "desc": "Boyaca, Colombia. One of the 'Big Three' Colombian emerald mines alongside Muzo and Chivor.",
         "country": "Colombia", "status": "Active", "notable": "Big Three Colombian mines"},
        {"name": "Kagem Mine", "lat": -13.100, "lon": 28.150,
         "desc": "Zambia. World's single largest producing emerald mine. Operated by Gemfields. Produces 25% of global supply.",
         "country": "Zambia", "status": "Active", "notable": "Largest single producer"},
        {"name": "Itabira / Belmont Mine", "lat": -19.619, "lon": -43.227,
         "desc": "Minas Gerais, Brazil. Major emerald source. Brazilian emeralds tend toward yellowish-green.",
         "country": "Brazil", "status": "Active", "notable": "Yellowish-green hues"},
        {"name": "Panjshir Valley", "lat": 35.317, "lon": 70.200,
         "desc": "Afghanistan. Produces vivid green emeralds rivaling Colombian quality. Mining dates to antiquity.",
         "country": "Afghanistan", "status": "Active", "notable": "Rivals Colombian quality"},
        {"name": "Swat Valley", "lat": 35.222, "lon": 72.355,
         "desc": "Pakistan. Historic emerald source known since Mughal times. Light to medium green stones.",
         "country": "Pakistan", "status": "Active", "notable": "Mughal-era mining"},
        {"name": "Sandawana Mine", "lat": -20.783, "lon": 30.117,
         "desc": "Zimbabwe. Known for small but intensely colored emeralds. Discovered 1956.",
         "country": "Zimbabwe", "status": "Active", "notable": "Intensely colored small stones"},
    ]


def _get_ruby_sapphire_data():
    return [
        {"name": "Mogok Valley", "lat": 22.920, "lon": 96.500,
         "desc": "Myanmar (Burma). The most legendary ruby source. Produces 'pigeon blood' rubies, the finest in the world.",
         "country": "Myanmar", "status": "Active", "notable": "Pigeon blood rubies", "gem": "Ruby"},
        {"name": "Mong Hsu", "lat": 20.533, "lon": 97.367,
         "desc": "Myanmar. Major ruby source since the 1990s. Stones often heat-treated to improve color.",
         "country": "Myanmar", "status": "Active", "notable": "Heat-treated rubies", "gem": "Ruby"},
        {"name": "Ratnapura", "lat": 6.682, "lon": 80.399,
         "desc": "Sri Lanka (Ceylon). 'City of Gems'. Famous for blue sapphires and star stones for over 2,000 years.",
         "country": "Sri Lanka", "status": "Active", "notable": "Ceylon blue sapphires", "gem": "Sapphire"},
        {"name": "Ilakaka", "lat": -22.683, "lon": 45.517,
         "desc": "Madagascar. Discovered 1998, became one of the world's largest sapphire deposits overnight. Alluvial mining.",
         "country": "Madagascar", "status": "Active", "notable": "Massive alluvial deposit", "gem": "Sapphire"},
        {"name": "Kashmir Sapphire Region", "lat": 33.583, "lon": 76.083,
         "desc": "Jammu & Kashmir, India. Legendary source of the rarest blue sapphires (cornflower blue). Mines largely exhausted.",
         "country": "India", "status": "Largely exhausted", "notable": "Cornflower blue sapphires", "gem": "Sapphire"},
        {"name": "Luc Yen", "lat": 22.100, "lon": 104.733,
         "desc": "Vietnam. Produces fine rubies and sapphires in marble host rock. Discovered in 1980s.",
         "country": "Vietnam", "status": "Active", "notable": "Marble-hosted rubies", "gem": "Ruby"},
        {"name": "Montepuez Ruby Deposit", "lat": -13.117, "lon": 38.983,
         "desc": "Mozambique. Major ruby discovery in 2009. Now one of the most significant new ruby sources globally.",
         "country": "Mozambique", "status": "Active", "notable": "Major new source since 2009", "gem": "Ruby"},
        {"name": "Chanthaburi", "lat": 12.611, "lon": 102.103,
         "desc": "Thailand. Historic sapphire and ruby mining region. Also a major gem trading center.",
         "country": "Thailand", "status": "Declining", "notable": "Trading & mining center", "gem": "Both"},
        {"name": "Yogo Gulch", "lat": 47.017, "lon": -110.467,
         "desc": "Montana, USA. Produces cornflower-blue sapphires. The only North American source of gem-quality sapphires.",
         "country": "USA", "status": "Active", "notable": "Cornflower blue, N. American source", "gem": "Sapphire"},
        {"name": "Pailin", "lat": 12.850, "lon": 102.617,
         "desc": "Cambodia. Historic sapphire mining region near Thai border. Stones known for dark blue hue.",
         "country": "Cambodia", "status": "Declining", "notable": "Dark blue sapphires", "gem": "Sapphire"},
    ]


def _get_opal_data():
    return [
        {"name": "Lightning Ridge", "lat": -29.430, "lon": 147.975,
         "desc": "New South Wales, Australia. World's most famous source of black opals, the rarest and most valuable variety.",
         "country": "Australia", "status": "Active", "notable": "Black opals"},
        {"name": "Coober Pedy", "lat": -29.013, "lon": 134.755,
         "desc": "South Australia. 'Opal Capital of the World'. Produces ~70% of the world's gem opals. Underground town.",
         "country": "Australia", "status": "Active", "notable": "70% world supply, underground town"},
        {"name": "Welo (Wollo) Province", "lat": 11.800, "lon": 39.500,
         "desc": "Ethiopia. Discovered 2008. Produces hydrophane opals with vivid play-of-color. Major new source.",
         "country": "Ethiopia", "status": "Active", "notable": "Hydrophane opals"},
        {"name": "Andamooka", "lat": -30.450, "lon": 137.167,
         "desc": "South Australia. Famous for matrix opal and crystal opal. Mining since 1930.",
         "country": "Australia", "status": "Active", "notable": "Matrix & crystal opal"},
        {"name": "Mintabie", "lat": -27.333, "lon": 133.300,
         "desc": "South Australia. Known for crystal and semi-black opals. Remote outback location.",
         "country": "Australia", "status": "Restricted", "notable": "Crystal & semi-black opal"},
        {"name": "White Cliffs", "lat": -30.850, "lon": 143.083,
         "desc": "New South Wales, Australia. First significant opal field in Australia (1889). Mostly white opals.",
         "country": "Australia", "status": "Active", "notable": "Australia's first opal field"},
        {"name": "Queretaro", "lat": 20.700, "lon": -100.383,
         "desc": "Mexico. Produces fire opals in vivid orange and red. Set in rhyolitic volcanic rock.",
         "country": "Mexico", "status": "Active", "notable": "Fire opals"},
        {"name": "Virgin Valley", "lat": 41.667, "lon": -118.867,
         "desc": "Nevada, USA. Famous for black fire opals. Gems found in opalized wood. Fragile specimens.",
         "country": "USA", "status": "Active", "notable": "Black fire opals, opalized wood"},
    ]


def _get_jade_data():
    return [
        {"name": "Hpakant Jade Mines", "lat": 25.617, "lon": 96.317,
         "desc": "Kachin State, Myanmar. World's primary source of jadeite, the more valuable jade variety. Multi-billion dollar industry.",
         "country": "Myanmar", "status": "Active", "notable": "World's top jadeite source"},
        {"name": "Hetian (Khotan)", "lat": 37.117, "lon": 79.933,
         "desc": "Xinjiang, China. Legendary nephrite jade source for over 5,000 years. Prized for 'mutton fat' white jade.",
         "country": "China", "status": "Active", "notable": "5,000-year nephrite history"},
        {"name": "Kunlun Mountains", "lat": 36.000, "lon": 84.000,
         "desc": "China. Source of nephrite jade boulders carried by rivers. Used in Chinese civilization since Neolithic times.",
         "country": "China", "status": "Active", "notable": "River-carried nephrite boulders"},
        {"name": "South Westland", "lat": -43.383, "lon": 169.850,
         "desc": "New Zealand. Source of pounamu (greenstone/nephrite), taonga (treasure) of Maori culture.",
         "country": "New Zealand", "status": "Protected", "notable": "Pounamu, Maori taonga"},
        {"name": "Motagua Valley", "lat": 14.917, "lon": -89.917,
         "desc": "Guatemala. Only known jadeite source in the Americas. Used by Maya and Olmec civilizations.",
         "country": "Guatemala", "status": "Active", "notable": "Maya & Olmec jadeite"},
        {"name": "Polar Jade Mine", "lat": 59.383, "lon": -125.367,
         "desc": "British Columbia, Canada. Large nephrite jade deposit. Produces deep green 'polar jade'.",
         "country": "Canada", "status": "Active", "notable": "Deep green polar jade"},
        {"name": "Cowell Jade", "lat": -33.683, "lon": 136.917,
         "desc": "South Australia. Significant nephrite jade deposit discovered in 1965. Deep green material.",
         "country": "Australia", "status": "Active", "notable": "South Australian nephrite"},
        {"name": "Kashgar Jade Market", "lat": 39.467, "lon": 75.983,
         "desc": "Xinjiang, China. Historic jade trading center on the Silk Road. Connects Hetian deposits to markets.",
         "country": "China", "status": "Trading hub", "notable": "Silk Road jade trade"},
    ]


def _get_amber_data():
    return [
        {"name": "Kaliningrad", "lat": 54.700, "lon": 20.500,
         "desc": "Russia (former Konigsberg). World's largest amber deposit. Baltic amber (succinite), 40-50 million years old.",
         "country": "Russia", "status": "Active", "notable": "World's largest amber deposit"},
        {"name": "Gdansk", "lat": 54.352, "lon": 18.647,
         "desc": "Poland. Historic Baltic amber capital. Amber has washed up on shores for millennia. Major crafting center.",
         "country": "Poland", "status": "Collecting & craft", "notable": "Baltic amber capital"},
        {"name": "Palanga", "lat": 55.920, "lon": 21.068,
         "desc": "Lithuania. Home to the Palanga Amber Museum. Baltic amber coast with frequent beach finds.",
         "country": "Lithuania", "status": "Collecting", "notable": "Amber Museum"},
        {"name": "Santiago de los Caballeros", "lat": 19.450, "lon": -70.700,
         "desc": "Dominican Republic. Produces rare blue amber (unique fluorescence). 15-40 million years old.",
         "country": "Dominican Republic", "status": "Active", "notable": "Rare blue amber"},
        {"name": "Simojovel", "lat": 17.133, "lon": -92.700,
         "desc": "Chiapas, Mexico. Produces amber rich in insect inclusions. Mined from Miocene lignite deposits.",
         "country": "Mexico", "status": "Active", "notable": "Rich insect inclusions"},
        {"name": "Hukawng Valley", "lat": 26.333, "lon": 96.667,
         "desc": "Kachin State, Myanmar. Burmese amber, ~99 million years old (Cretaceous). Major paleontological source.",
         "country": "Myanmar", "status": "Active", "notable": "99 Ma Cretaceous amber"},
        {"name": "Rivne Oblast", "lat": 50.617, "lon": 26.250,
         "desc": "Ukraine. Significant illegal amber mining region. Ukrainian amber is Baltic-type succinite.",
         "country": "Ukraine", "status": "Active/Informal", "notable": "Succinite deposits"},
        {"name": "Bitterfeld", "lat": 51.633, "lon": 12.333,
         "desc": "Germany. Bitterfeld amber deposits, chemically similar to Baltic amber. Mined from lignite seams.",
         "country": "Germany", "status": "Depleted", "notable": "Lignite-seam amber"},
    ]


def _get_turquoise_data():
    return [
        {"name": "Nishapur Mines", "lat": 36.217, "lon": 58.800,
         "desc": "Iran. Oldest known turquoise mines (since 3,000 BC). Persian turquoise is the benchmark for color quality.",
         "country": "Iran", "status": "Active", "notable": "3,000 BC, benchmark quality"},
        {"name": "Sleeping Beauty Mine", "lat": 33.350, "lon": -110.917,
         "desc": "Globe, Arizona, USA. Famed for robin's-egg blue turquoise without matrix. Closed for turquoise 2012.",
         "country": "USA", "status": "Closed 2012", "notable": "Robin's-egg blue, no matrix"},
        {"name": "Kingman Mine", "lat": 35.200, "lon": -114.050,
         "desc": "Arizona, USA. Produces high-grade turquoise with white quartz matrix. Active since 1960s.",
         "country": "USA", "status": "Active", "notable": "White quartz matrix"},
        {"name": "Bisbee Mine", "lat": 31.433, "lon": -109.917,
         "desc": "Arizona, USA. Legendary turquoise with chocolate brown matrix. Copper mine byproduct. Highly collectible.",
         "country": "USA", "status": "Closed", "notable": "Chocolate brown matrix"},
        {"name": "Cerrillos Hills", "lat": 35.433, "lon": -106.133,
         "desc": "New Mexico, USA. Oldest turquoise mine in North America. Mined by Ancestral Puebloans since 900 AD.",
         "country": "USA", "status": "Historic", "notable": "Oldest in N. America, 900 AD"},
        {"name": "Lhasa Region", "lat": 29.650, "lon": 91.117,
         "desc": "Tibet. Tibetan turquoise has been prized for centuries. Typically greener hue. Cultural significance in Buddhism.",
         "country": "China/Tibet", "status": "Active", "notable": "Buddhist cultural significance"},
        {"name": "Ma'dan (Sinai)", "lat": 29.100, "lon": 33.383,
         "desc": "Sinai Peninsula, Egypt. Ancient Egyptian turquoise mines dating to 3,200 BC. Hathor temple nearby.",
         "country": "Egypt", "status": "Historic", "notable": "Ancient Egyptian mines, 3,200 BC"},
        {"name": "Number 8 Mine", "lat": 40.800, "lon": -116.567,
         "desc": "Eureka County, Nevada, USA. Produced some of the finest spiderweb turquoise. Now a famous collectible.",
         "country": "USA", "status": "Closed", "notable": "Spiderweb turquoise"},
    ]


def _get_pearl_data():
    return [
        {"name": "Mikimoto Pearl Island", "lat": 34.483, "lon": 136.850,
         "desc": "Toba, Japan. Where Kokichi Mikimoto perfected cultured pearl farming in 1893. Birthplace of the pearl industry.",
         "country": "Japan", "status": "Museum & farm", "notable": "Birthplace of cultured pearls"},
        {"name": "Tuamotu Archipelago", "lat": -15.500, "lon": -145.500,
         "desc": "French Polynesia (Tahiti). Source of black Tahitian pearls from black-lipped oysters (Pinctada margaritifera).",
         "country": "French Polynesia", "status": "Active", "notable": "Black Tahitian pearls"},
        {"name": "Broome", "lat": -17.961, "lon": 122.236,
         "desc": "Western Australia. Capital of Australian South Sea pearls. White and golden pearls from Pinctada maxima.",
         "country": "Australia", "status": "Active", "notable": "South Sea pearls, Pinctada maxima"},
        {"name": "Bahrain Pearl Trail", "lat": 26.217, "lon": 50.550,
         "desc": "Persian Gulf. UNESCO World Heritage Site. Natural pearl diving tradition spanning 4,000 years.",
         "country": "Bahrain", "status": "Heritage/Active", "notable": "4,000-year diving tradition"},
        {"name": "Paspaley - Darwin", "lat": -12.463, "lon": 130.844,
         "desc": "Northern Territory, Australia. Paspaley is the world's most important producer of South Sea pearls.",
         "country": "Australia", "status": "Active", "notable": "World's top South Sea producer"},
        {"name": "Zhuji Pearl Market", "lat": 29.717, "lon": 120.250,
         "desc": "Zhejiang, China. World's largest freshwater pearl market. China produces 95% of freshwater pearls.",
         "country": "China", "status": "Active", "notable": "95% of freshwater pearls"},
        {"name": "Mergui Archipelago", "lat": 11.500, "lon": 97.800,
         "desc": "Myanmar. Historic natural pearl diving region. Moken sea-nomad divers. South Sea and golden pearls.",
         "country": "Myanmar", "status": "Active", "notable": "Moken sea-nomad tradition"},
        {"name": "La Paz", "lat": 24.142, "lon": -110.312,
         "desc": "Baja California, Mexico. Historic pearl fishing center. Steinbeck's 'The Pearl' was set here.",
         "country": "Mexico", "status": "Heritage/Farm", "notable": "Steinbeck's 'The Pearl'"},
    ]


def _get_cutting_centers_data():
    return [
        {"name": "Jaipur", "lat": 26.912, "lon": 75.787,
         "desc": "Rajasthan, India. The 'Pink City' is the world's largest gem-cutting center by volume. Over 500,000 cutters.",
         "country": "India", "status": "Major hub", "notable": "500,000+ cutters, largest by volume"},
        {"name": "Surat", "lat": 21.170, "lon": 72.831,
         "desc": "Gujarat, India. Cuts and polishes ~90% of the world's diamonds. Employs over 1 million workers.",
         "country": "India", "status": "Major hub", "notable": "90% of world diamonds cut here"},
        {"name": "Antwerp Diamond District", "lat": 51.218, "lon": 4.416,
         "desc": "Belgium. Global diamond trading capital for 500+ years. 84% of rough diamonds pass through Antwerp.",
         "country": "Belgium", "status": "Trading hub", "notable": "84% of rough diamonds traded"},
        {"name": "Bangkok Gem Quarter", "lat": 13.735, "lon": 100.511,
         "desc": "Thailand. World center for colored gemstone cutting and treatment. Silom Road gem district.",
         "country": "Thailand", "status": "Major hub", "notable": "Colored stone cutting capital"},
        {"name": "Tel Aviv Diamond Exchange", "lat": 32.082, "lon": 34.790,
         "desc": "Ramat Gan, Israel. One of the world's largest diamond exchanges. Known for precision cutting.",
         "country": "Israel", "status": "Major hub", "notable": "Precision cutting expertise"},
        {"name": "Idar-Oberstein", "lat": 49.700, "lon": 7.317,
         "desc": "Germany. European gem-cutting capital since the 15th century. Originally used local agate deposits.",
         "country": "Germany", "status": "Active", "notable": "500-year cutting tradition"},
        {"name": "Chanthaburi Gem Market", "lat": 12.611, "lon": 102.103,
         "desc": "Thailand. Major gem trading center for rubies and sapphires from Southeast Asia and Africa.",
         "country": "Thailand", "status": "Major hub", "notable": "Ruby & sapphire trading"},
        {"name": "Bogota Emerald Market", "lat": 4.601, "lon": -74.072,
         "desc": "Colombia. Center for Colombian emerald trading and cutting. Dealers cluster near Avenida Jimenez.",
         "country": "Colombia", "status": "Trading hub", "notable": "Colombian emerald trade"},
        {"name": "Hong Kong Gem Show", "lat": 22.302, "lon": 114.172,
         "desc": "Hong Kong. Major international gem and jewelry trade fair. Gateway to Chinese consumer market.",
         "country": "Hong Kong", "status": "Trading hub", "notable": "Gateway to Asian market"},
        {"name": "Tucson Gem & Mineral Show", "lat": 32.222, "lon": -110.975,
         "desc": "Arizona, USA. World's largest annual gem, mineral, and fossil show. Held every February.",
         "country": "USA", "status": "Annual event", "notable": "World's largest gem show"},
    ]


def _get_crown_jewels_data():
    return [
        {"name": "Tower of London", "lat": 51.508, "lon": -0.076,
         "desc": "London, UK. Houses the British Crown Jewels including the Cullinan I (530 ct), Koh-i-Noor, and Imperial State Crown.",
         "country": "UK", "status": "Museum", "notable": "Cullinan I, Koh-i-Noor, Imperial State Crown"},
        {"name": "Smithsonian NMNH", "lat": 38.891, "lon": -77.026,
         "desc": "Washington DC, USA. Home of the Hope Diamond (45.52 ct blue), Star of Asia sapphire, and Carmen Lucia ruby.",
         "country": "USA", "status": "Museum", "notable": "Hope Diamond (45.52 ct)"},
        {"name": "American Museum of Natural History", "lat": 40.781, "lon": -73.974,
         "desc": "New York, USA. Houses the Star of India (563 ct star sapphire), Patricia Emerald, and DeLong Star Ruby.",
         "country": "USA", "status": "Museum", "notable": "Star of India (563 ct)"},
        {"name": "Louvre Museum", "lat": 48.861, "lon": 2.336,
         "desc": "Paris, France. French Crown Jewels including the Regent Diamond (140.64 ct) and Cote de Bretagne ruby.",
         "country": "France", "status": "Museum", "notable": "Regent Diamond (140.64 ct)"},
        {"name": "Moscow Kremlin", "lat": 55.752, "lon": 37.617,
         "desc": "Moscow, Russia. Russian Diamond Fund with Orlov Diamond (189.62 ct) and Shah Diamond. Romanov treasures.",
         "country": "Russia", "status": "Museum", "notable": "Orlov Diamond (189.62 ct)"},
        {"name": "Iranian National Jewels", "lat": 35.696, "lon": 51.416,
         "desc": "Tehran, Iran. Central Bank vault. Darya-i-Noor (186 ct pink), Noor-ul-Ain, and the Jeweled Globe.",
         "country": "Iran", "status": "Treasury", "notable": "Darya-i-Noor (186 ct pink)"},
        {"name": "Topkapi Palace", "lat": 41.011, "lon": 28.983,
         "desc": "Istanbul, Turkey. Ottoman Treasury with the Spoonmaker's Diamond (86 ct), Topkapi Dagger, and emerald collection.",
         "country": "Turkey", "status": "Museum", "notable": "Spoonmaker's Diamond (86 ct)"},
        {"name": "Green Vault (Grunes Gewolbe)", "lat": 51.053, "lon": 13.737,
         "desc": "Dresden, Germany. Saxon crown jewels including the Dresden Green Diamond (41 ct) — rarest natural green diamond.",
         "country": "Germany", "status": "Museum", "notable": "Dresden Green Diamond (41 ct)"},
        {"name": "Royal Palace of Madrid", "lat": 40.418, "lon": -3.714,
         "desc": "Madrid, Spain. Spanish Crown Jewels including La Peregrina pearl (once owned by Elizabeth Taylor).",
         "country": "Spain", "status": "Museum", "notable": "La Peregrina pearl"},
        {"name": "Vienna Imperial Treasury", "lat": 48.206, "lon": 16.366,
         "desc": "Vienna, Austria. Habsburg treasures including the Imperial Crown, Holy Lance, and the Florentine Diamond history.",
         "country": "Austria", "status": "Museum", "notable": "Habsburg Imperial Crown"},
    ]


# ═══════════════════════════════════════════
# DATA DISPATCH
# ═══════════════════════════════════════════
MODE_CONFIG = {
    "Diamond Mines of the World": {
        "fn": _get_diamond_data,
        "color": GEM_COLORS["diamond"],
        "icon_color": "lightblue",
        "zoom": 3,
        "center": [10.0, 20.0],
        "subtitle": "Major diamond mines and kimberlite pipe deposits worldwide",
    },
    "Emerald Sources": {
        "fn": _get_emerald_data,
        "color": GEM_COLORS["emerald"],
        "icon_color": "green",
        "zoom": 3,
        "center": [10.0, 0.0],
        "subtitle": "World's premier emerald mining regions from Colombia to Zambia",
    },
    "Ruby & Sapphire Origins": {
        "fn": _get_ruby_sapphire_data,
        "color": GEM_COLORS["ruby"],
        "icon_color": "red",
        "zoom": 3,
        "center": [20.0, 80.0],
        "subtitle": "Legendary ruby and sapphire sources from Myanmar to Montana",
    },
    "Opal Mining": {
        "fn": _get_opal_data,
        "color": GEM_COLORS["opal"],
        "icon_color": "orange",
        "zoom": 3,
        "center": [-15.0, 120.0],
        "subtitle": "Opal mining regions: Australian outback, Ethiopian highlands, and beyond",
    },
    "Jade Sources": {
        "fn": _get_jade_data,
        "color": GEM_COLORS["jade"],
        "icon_color": "green",
        "zoom": 3,
        "center": [30.0, 100.0],
        "subtitle": "Jadeite and nephrite sources from Myanmar to New Zealand",
    },
    "Amber Deposits": {
        "fn": _get_amber_data,
        "color": GEM_COLORS["amber"],
        "icon_color": "orange",
        "zoom": 3,
        "center": [40.0, 30.0],
        "subtitle": "Ancient amber deposits from the Baltic to Burmese Cretaceous",
    },
    "Turquoise Mines": {
        "fn": _get_turquoise_data,
        "color": GEM_COLORS["turquoise"],
        "icon_color": "cadetblue",
        "zoom": 3,
        "center": [35.0, -10.0],
        "subtitle": "Persian, American Southwest, and ancient turquoise mining sites",
    },
    "Pearl Farms": {
        "fn": _get_pearl_data,
        "color": GEM_COLORS["pearl"],
        "icon_color": "white",
        "zoom": 3,
        "center": [10.0, 100.0],
        "subtitle": "Pearl farming regions from Mikimoto Japan to Tahitian atolls",
    },
    "Gem Cutting Centers": {
        "fn": _get_cutting_centers_data,
        "color": GEM_COLORS["cutting"],
        "icon_color": "purple",
        "zoom": 3,
        "center": [25.0, 50.0],
        "subtitle": "Global gem cutting, polishing, and trading centers",
    },
    "Crown Jewels & Famous Gems": {
        "fn": _get_crown_jewels_data,
        "color": GEM_COLORS["crown"],
        "icon_color": "red",
        "zoom": 3,
        "center": [40.0, 10.0],
        "subtitle": "World-famous gem collections and crown jewel treasuries",
    },
}


# ═══════════════════════════════════════════
# WIKI ENRICHMENT (optional, cached)
# ═══════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fetch_wiki_extract(title: str) -> str:
    """Fetch a short Wikipedia extract for a location name."""
    try:
        resp = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(title),
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("extract", "")
    except Exception:
        pass
    return ""


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_gemstone_maps_tab():
    """Main render function for the Gemstone & Crystal Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>\U0001f48e Gemstone &amp; Crystal Explorer</h4>
        <p>Explore the world's most famous gemstone mines, cutting centers, and legendary jewel collections &mdash; from diamond pipes to crown treasuries.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode selector ──
    mode = st.selectbox(
        "Map Mode",
        MAP_MODES,
        key="gem_map_mode",
    )

    config = MODE_CONFIG[mode]
    data = config["fn"]()

    if not data:
        st.warning("No data available for this mode.")
        return

    # ── Stats row ──
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Locations", len(data))
    with c2:
        countries = set(d.get("country", "Unknown") for d in data)
        st.metric("Countries", len(countries))
    with c3:
        active = sum(1 for d in data if "Active" in d.get("status", ""))
        st.metric("Active Sites", active)
    with c4:
        st.metric("Map Mode", mode.split(" ")[0])

    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem; margin-top:0.25rem;">{html_module.escape(config["subtitle"])}</p>',
        unsafe_allow_html=True,
    )

    # ── Build folium map ──
    m = folium.Map(
        location=config["center"],
        zoom_start=config["zoom"],
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Gemstone Locations").add_to(m)

    for item in data:
        lat = item["lat"]
        lon = item["lon"]
        name = html_module.escape(item["name"])
        desc = html_module.escape(item["desc"])
        notable = html_module.escape(item.get("notable", ""))
        status = html_module.escape(item.get("status", ""))
        country = html_module.escape(item.get("country", ""))

        # Popup HTML
        popup_html = (
            f'<div style="background:#1a2235;color:#e8ecf4;padding:10px;border-radius:8px;'
            f'min-width:200px;max-width:280px;font-family:sans-serif;">'
            f'<b style="color:{config["color"]};font-size:0.95rem;">{name}</b><br>'
            f'<span style="color:#8b97b0;font-size:0.8rem;">{country}</span>'
            f'<span style="color:#5a6580;font-size:0.75rem;"> &mdash; {status}</span><br>'
            f'<hr style="border-color:#2a3550;margin:6px 0;">'
            f'<span style="color:#c8d0de;font-size:0.8rem;">{desc}</span><br>'
        )
        if notable:
            popup_html += (
                f'<span style="color:{config["color"]};font-size:0.75rem;margin-top:4px;display:inline-block;">'
                f'Notable: {notable}</span>'
            )
        popup_html += '</div>'

        # Determine marker color for specific gem types (ruby vs sapphire)
        marker_color = config["color"]
        gem_type = item.get("gem", "")
        if gem_type == "Ruby":
            marker_color = GEM_COLORS["ruby"]
        elif gem_type == "Sapphire":
            marker_color = GEM_COLORS["sapphire"]

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=name,
        ).add_to(cluster)

    folium.LayerControl().add_to(m)

    # ── Render map ──
    st_html(m._repr_html_(), height=500)

    # ── Data table ──
    st.markdown("---")
    st.markdown("#### Location Details")

    rows = []
    for item in data:
        row = {
            "Name": item["name"],
            "Country": item.get("country", ""),
            "Latitude": item["lat"],
            "Longitude": item["lon"],
            "Status": item.get("status", ""),
            "Notable": item.get("notable", ""),
            "Description": item.get("desc", ""),
        }
        # Add gem type column for ruby/sapphire mode
        if "gem" in item:
            row["Gem Type"] = item["gem"]
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # ── Location cards ──
    st.markdown("#### Highlights")
    for item in data:
        name = html_module.escape(item["name"])
        desc = html_module.escape(item["desc"])
        notable = html_module.escape(item.get("notable", ""))
        status = html_module.escape(item.get("status", ""))
        country = html_module.escape(item.get("country", ""))
        color = config["color"]

        gem_type = item.get("gem", "")
        if gem_type == "Ruby":
            color = GEM_COLORS["ruby"]
        elif gem_type == "Sapphire":
            color = GEM_COLORS["sapphire"]

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.75rem;">
            <div style="width:8px; height:70px; border-radius:4px; background:{color};
                        margin-right:1rem; flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="color:#e8ecf4; font-weight:700; font-size:0.95rem;">{name}</div>
                <div style="color:{color}; font-size:0.8rem;">{country} &mdash; {status}</div>
                <div style="color:#8b97b0; font-size:0.8rem;">{desc}</div>
                <div style="color:#5a6580; font-size:0.72rem;">Notable: {notable}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── CSV download ──
    st.markdown("---")
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    safe_mode = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        f"Download {len(data)} Locations (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"gemstone_{safe_mode}.csv",
        mime="text/csv",
        key="gem_csv_download",
    )

    # ── Wikipedia enrichment (expandable) ──
    st.markdown("---")
    st.markdown("#### Learn More")
    st.markdown(
        '<p style="color:#8b97b0; font-size:0.85rem;">Expand a location to load a brief Wikipedia summary.</p>',
        unsafe_allow_html=True,
    )
    for item in data[:5]:
        with st.expander(f"{item['name']} — {item.get('country', '')}"):
            wiki = _fetch_wiki_extract(item["name"])
            if wiki:
                st.markdown(
                    f'<p style="color:#c8d0de; font-size:0.85rem;">{html_module.escape(wiki)}</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("No Wikipedia summary available for this location.")
            st.markdown(
                f'<p style="color:#5a6580; font-size:0.75rem;">Coordinates: {item["lat"]}, {item["lon"]}</p>',
                unsafe_allow_html=True,
            )
