# -*- coding: utf-8 -*-
"""
Coins & Currency Maps module for TerraScout AI.
Mints, currency history, and numismatic treasures worldwide.
10 curated map modes with hardcoded locations, folium dark maps,
stats dashboards, data tables, and CSV downloads.
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
# 1. World Mints  (26 locations)
# ---------------------------------------------------------------------------

def _world_mints_data():
    """Major world mints — active government and private mints."""
    return [
        {"name": "United States Mint - Philadelphia", "lat": 39.9526, "lon": -75.1652,
         "country": "USA", "founded": 1792,
         "notes": "Oldest US Mint facility, no mint mark on most coins, produces circulating coinage"},
        {"name": "United States Mint - Denver", "lat": 39.7392, "lon": -104.9903,
         "country": "USA", "founded": 1906,
         "notes": "D mint mark, second-largest US circulating coin producer"},
        {"name": "United States Mint - San Francisco", "lat": 37.7749, "lon": -122.4194,
         "country": "USA", "founded": 1854,
         "notes": "S mint mark, proof coins and special collector editions"},
        {"name": "United States Mint - West Point", "lat": 41.3915, "lon": -73.9565,
         "country": "USA", "founded": 1937,
         "notes": "W mint mark, American Eagle gold, silver, and platinum bullion"},
        {"name": "Royal Mint", "lat": 51.5879, "lon": -3.2889,
         "country": "UK", "founded": 886,
         "notes": "Llantrisant, Wales — over 1100 years of coinage, Britannia bullion series"},
        {"name": "Monnaie de Paris", "lat": 48.8566, "lon": 2.3422,
         "country": "France", "founded": 864,
         "notes": "World's oldest operating mint, Quai de Conti, French euro coins"},
        {"name": "Perth Mint", "lat": -31.9505, "lon": 115.8605,
         "country": "Australia", "founded": 1899,
         "notes": "Major gold refinery, Kangaroo and Kookaburra bullion coins"},
        {"name": "Royal Australian Mint", "lat": -35.2996, "lon": 149.1283,
         "country": "Australia", "founded": 1965,
         "notes": "Canberra, produces all circulating Australian decimal coins"},
        {"name": "Swiss Federal Mint (Swissmint)", "lat": 46.9480, "lon": 7.4474,
         "country": "Switzerland", "founded": 1855,
         "notes": "Bern, Swiss franc coins, Vreneli gold commemoratives"},
        {"name": "Royal Canadian Mint - Ottawa", "lat": 45.4306, "lon": -75.6880,
         "country": "Canada", "founded": 1908,
         "notes": "Collector coins, Gold Maple Leaf bullion, high-purity refining"},
        {"name": "Royal Canadian Mint - Winnipeg", "lat": 49.8844, "lon": -97.1464,
         "country": "Canada", "founded": 1976,
         "notes": "Circulating Canadian coins and foreign contract minting"},
        {"name": "Casa de Moneda de Mexico", "lat": 19.4326, "lon": -99.1332,
         "country": "Mexico", "founded": 1535,
         "notes": "Oldest mint in the Americas, Libertad silver and gold bullion"},
        {"name": "South African Mint", "lat": -25.7479, "lon": 28.2293,
         "country": "South Africa", "founded": 1892,
         "notes": "Pretoria, produces the iconic Krugerrand since 1967"},
        {"name": "Japan Mint", "lat": 34.6937, "lon": 135.5023,
         "country": "Japan", "founded": 1871,
         "notes": "Osaka, all Japanese yen coins, cherry blossom open days"},
        {"name": "Korea Minting and Security Printing Corp", "lat": 36.3504, "lon": 127.3845,
         "country": "South Korea", "founded": 1951,
         "notes": "Daejeon, Korean won coins, Chiwoo Cheonwang bullion"},
        {"name": "India Government Mint - Mumbai", "lat": 18.9322, "lon": 72.8347,
         "country": "India", "founded": 1829,
         "notes": "Diamond mint mark below date, Indian rupee coins"},
        {"name": "India Government Mint - Kolkata", "lat": 22.5726, "lon": 88.3639,
         "country": "India", "founded": 1952,
         "notes": "No mint mark identifier, Alipore facility"},
        {"name": "China Banknote Printing and Minting Corp", "lat": 39.9042, "lon": 116.4074,
         "country": "China", "founded": 1908,
         "notes": "Beijing, Panda gold and silver bullion, yuan coinage"},
        {"name": "Royal Dutch Mint", "lat": 52.0907, "lon": 5.1214,
         "country": "Netherlands", "founded": 1567,
         "notes": "Utrecht, Dutch euro coins, foreign contract minting"},
        {"name": "Austrian Mint", "lat": 48.2082, "lon": 16.3738,
         "country": "Austria", "founded": 1194,
         "notes": "Vienna, Philharmonic gold and silver bullion coins"},
        {"name": "Mint of Finland", "lat": 61.2000, "lon": 24.0167,
         "country": "Finland", "founded": 1860,
         "notes": "Vantaa, Finnish euro coins and commemoratives"},
        {"name": "Royal Norwegian Mint (DNM)", "lat": 59.7439, "lon": 10.2045,
         "country": "Norway", "founded": 1686,
         "notes": "Kongsberg, Norwegian krone coins, historic silver mining town"},
        {"name": "Kremnica Mint", "lat": 48.7081, "lon": 18.9169,
         "country": "Slovakia", "founded": 1328,
         "notes": "One of the oldest continuously operating mints in the world"},
        {"name": "Czech Mint", "lat": 49.2186, "lon": 15.8781,
         "country": "Czech Republic", "founded": 1993,
         "notes": "Jablonec nad Nisou, Czech koruna coins and commemoratives"},
        {"name": "Singapore Mint", "lat": 1.3521, "lon": 103.8198,
         "country": "Singapore", "founded": 1968,
         "notes": "Singapore dollar coins, Merlion gold bullion"},
        {"name": "Pobjoy Mint", "lat": 51.3762, "lon": -0.0982,
         "country": "UK", "founded": 1965,
         "notes": "Private mint, coins for Isle of Man, Gibraltar, and British territories"},
        {"name": "Royal Spanish Mint (FNMT)", "lat": 40.4168, "lon": -3.7038,
         "country": "Spain", "founded": 1893,
         "notes": "Madrid, Spanish euro coins, stamps, and national lottery"},
        {"name": "Istituto Poligrafico Zecca dello Stato", "lat": 41.9028, "lon": 12.4964,
         "country": "Italy", "founded": 1911,
         "notes": "Rome, Italian euro coins and historic lira coinage"},
        {"name": "Turkish State Mint", "lat": 39.9334, "lon": 32.8597,
         "country": "Turkey", "founded": 1467,
         "notes": "Istanbul Darphane origins, now Ankara, Turkish lira coins"},
        {"name": "Central Mint of Brazil", "lat": -22.9068, "lon": -43.1729,
         "country": "Brazil", "founded": 1694,
         "notes": "Rio de Janeiro Casa da Moeda, Brazilian real coins and medals"},
    ]


# ---------------------------------------------------------------------------
# 2. Ancient Coin Origins  (22 locations)
# ---------------------------------------------------------------------------

def _ancient_coin_origins_data():
    """Origins and key sites of ancient coinage worldwide."""
    return [
        {"name": "Sardis, Lydia - First Coins", "lat": 38.4892, "lon": 28.0400,
         "country": "Turkey", "era": "c. 600 BC",
         "notes": "Birthplace of coinage — electrum staters under King Alyattes and Croesus"},
        {"name": "Athens - Owl Tetradrachm", "lat": 37.9838, "lon": 23.7275,
         "country": "Greece", "era": "c. 510 BC",
         "notes": "Iconic silver tetradrachm with Athena and owl, symbol of wisdom and commerce"},
        {"name": "Aegina - Silver Turtle Stater", "lat": 37.7475, "lon": 23.4290,
         "country": "Greece", "era": "c. 550 BC",
         "notes": "Sea turtle staters, among the earliest Greek silver coins minted"},
        {"name": "Rome - Denarius at Temple of Juno Moneta", "lat": 41.9028, "lon": 12.4964,
         "country": "Italy", "era": "211 BC",
         "notes": "Roman denarius originated here; word 'money' derives from Moneta"},
        {"name": "Syracuse - Signed Decadrachm", "lat": 37.0755, "lon": 15.2866,
         "country": "Italy", "era": "c. 400 BC",
         "notes": "Finest ancient Greek coins, signed by master engravers Kimon and Euainetos"},
        {"name": "Carthage - Tanit Staters", "lat": 36.8528, "lon": 10.3234,
         "country": "Tunisia", "era": "c. 350 BC",
         "notes": "Carthaginian gold and silver staters with Tanit head and horse motifs"},
        {"name": "Alexandria - Ptolemaic Coinage", "lat": 31.2001, "lon": 29.9187,
         "country": "Egypt", "era": "305 BC",
         "notes": "Ptolemaic dynasty large bronze and gold issues, royal portrait coins"},
        {"name": "Persepolis - Persian Gold Daric", "lat": 29.9352, "lon": 52.8914,
         "country": "Iran", "era": "c. 515 BC",
         "notes": "Gold daric showing Great King as archer, standard of Persian Empire trade"},
        {"name": "Taxila - Indo-Greek Bilingual Coins", "lat": 33.7463, "lon": 72.7988,
         "country": "Pakistan", "era": "c. 180 BC",
         "notes": "Bilingual Greek-Kharosthi coins, Menander I silver drachms"},
        {"name": "Luoyang - Ban Liang Cash Coins", "lat": 34.6197, "lon": 112.4540,
         "country": "China", "era": "c. 500 BC",
         "notes": "Round coins with square holes, Ban Liang and Wu Zhu denominations"},
        {"name": "Anyang - Shang Dynasty Cowrie Shells", "lat": 36.0997, "lon": 114.3929,
         "country": "China", "era": "c. 1500 BC",
         "notes": "Cowrie shells as earliest Chinese currency, found in Shang royal tombs"},
        {"name": "Corinth - Pegasus Stater", "lat": 37.9057, "lon": 22.8796,
         "country": "Greece", "era": "c. 550 BC",
         "notes": "Silver staters with Pegasus, widely circulated across Mediterranean"},
        {"name": "Ephesus - Early Electrum Coins", "lat": 37.9494, "lon": 27.3638,
         "country": "Turkey", "era": "c. 600 BC",
         "notes": "Early electrum coins from Artemis temple, rival to Sardis in coinage innovation"},
        {"name": "Massalia (Marseille) - Greek Obols", "lat": 43.2965, "lon": 5.3698,
         "country": "France", "era": "c. 500 BC",
         "notes": "Greek colony silver obols with Artemis head, spread coinage to Celtic Gaul"},
        {"name": "Knossos, Crete - Labyrinth Staters", "lat": 35.2980, "lon": 25.1631,
         "country": "Greece", "era": "c. 425 BC",
         "notes": "Silver staters with labyrinth and Minotaur motifs from Minoan legacy"},
        {"name": "Gandhara - Bent-Bar Silver Coins", "lat": 34.1688, "lon": 71.8311,
         "country": "Pakistan", "era": "c. 600 BC",
         "notes": "Shatamana bent-bar silver, earliest South Asian coinage form"},
        {"name": "Pantikapaion (Kerch) - Bosporan Gold", "lat": 45.3531, "lon": 36.4686,
         "country": "Ukraine", "era": "c. 480 BC",
         "notes": "Superb gold staters with Pan head, Bosporan Kingdom artistry"},
        {"name": "Tarentum (Taranto) - Dolphin Rider", "lat": 40.4761, "lon": 17.2290,
         "country": "Italy", "era": "c. 500 BC",
         "notes": "Silver didrachms depicting Taras riding dolphin, wide Mediterranean trade"},
        {"name": "Seleucid Antioch - Alexander Tetradrachms", "lat": 36.2000, "lon": 36.1500,
         "country": "Turkey", "era": "300 BC",
         "notes": "Major Seleucid mint, Alexander-type tetradrachms circulated for centuries"},
        {"name": "Magadha - Punch-Marked Karshapana", "lat": 25.6100, "lon": 85.1400,
         "country": "India", "era": "c. 400 BC",
         "notes": "Silver karshapana with multiple punch marks, earliest Indian silver coins"},
        {"name": "Cyzicus - Electrum Staters", "lat": 40.3906, "lon": 27.8833,
         "country": "Turkey", "era": "c. 550 BC",
         "notes": "Cyzicene electrum staters served as international trade currency"},
        {"name": "Metapontum - Ear of Wheat Stater", "lat": 40.3833, "lon": 16.8167,
         "country": "Italy", "era": "c. 540 BC",
         "notes": "Incuse technique silver staters with ear of wheat, Magna Graecia colony"},
        {"name": "Olbia - Dolphin-Shaped Bronze", "lat": 46.6964, "lon": 31.9025,
         "country": "Ukraine", "era": "c. 500 BC",
         "notes": "Unique dolphin-shaped cast bronze coins from Greek Black Sea colony"},
        {"name": "Ai Khanoum - Greco-Bactrian Mint", "lat": 37.1667, "lon": 69.4167,
         "country": "Afghanistan", "era": "c. 250 BC",
         "notes": "Greco-Bactrian city with large silver tetradrachms of Eucratides I"},
    ]


# ---------------------------------------------------------------------------
# 3. Gold Rush Sites  (22 locations)
# ---------------------------------------------------------------------------

def _gold_rush_sites_data():
    """Historic gold rush and gold mining sites worldwide."""
    return [
        {"name": "Sutter's Mill, Coloma", "lat": 38.8024, "lon": -120.8906,
         "country": "USA", "year": 1848,
         "notes": "California Gold Rush started here — James W. Marshall discovery on Jan 24"},
        {"name": "San Francisco Boomtown", "lat": 37.7749, "lon": -122.4194,
         "country": "USA", "year": 1849,
         "notes": "Gateway to the California Gold Rush, population exploded from 200 to 36,000"},
        {"name": "Sacramento Supply Hub", "lat": 38.5816, "lon": -121.4944,
         "country": "USA", "year": 1848,
         "notes": "Supply hub for gold miners, grew into California state capital"},
        {"name": "Dawson City, Klondike", "lat": 64.0600, "lon": -139.4320,
         "country": "Canada", "year": 1896,
         "notes": "Klondike Gold Rush epicenter, 100,000 set out but only 30,000 arrived"},
        {"name": "Skagway, Alaska", "lat": 59.4583, "lon": -135.3139,
         "country": "USA", "year": 1897,
         "notes": "Gateway to Klondike via White Pass and Chilkoot Trail"},
        {"name": "Witwatersrand, Johannesburg", "lat": -26.2041, "lon": 28.0473,
         "country": "South Africa", "year": 1886,
         "notes": "World's largest gold deposits, founding of Johannesburg city"},
        {"name": "Ballarat, Victoria", "lat": -37.5622, "lon": 143.8503,
         "country": "Australia", "year": 1851,
         "notes": "Victorian Gold Rush, Eureka Stockade rebellion of 1854"},
        {"name": "Bendigo, Victoria", "lat": -36.7570, "lon": 144.2794,
         "country": "Australia", "year": 1851,
         "notes": "Deep lead gold mining, rich quartz reefs, elaborate Chinese heritage"},
        {"name": "Bathurst, NSW", "lat": -33.4194, "lon": 149.5786,
         "country": "Australia", "year": 1851,
         "notes": "Edward Hargraves discovery at Ophir triggered Australian gold rush"},
        {"name": "Kalgoorlie, Western Australia", "lat": -30.7489, "lon": 121.4660,
         "country": "Australia", "year": 1893,
         "notes": "Super Pit open-cut mine, still one of Australia's largest gold producers"},
        {"name": "Ouro Preto, Minas Gerais", "lat": -20.3856, "lon": -43.5035,
         "country": "Brazil", "year": 1695,
         "notes": "Brazilian Gold Rush, baroque colonial UNESCO World Heritage Site"},
        {"name": "Serra Pelada", "lat": -5.9406, "lon": -49.6672,
         "country": "Brazil", "year": 1980,
         "notes": "Modern gold rush with 80,000+ garimpeiros in hellish open-pit conditions"},
        {"name": "Pilgrim's Rest, Mpumalanga", "lat": -24.9117, "lon": 30.7564,
         "country": "South Africa", "year": 1873,
         "notes": "First South African gold rush, preserved Victorian mining village"},
        {"name": "Nome, Alaska", "lat": 64.5011, "lon": -165.4064,
         "country": "USA", "year": 1898,
         "notes": "Beach gold discovery, largest gold rush in Alaska history"},
        {"name": "Fairbanks, Alaska", "lat": 64.8378, "lon": -147.7164,
         "country": "USA", "year": 1902,
         "notes": "Felix Pedro discovery, interior Alaska gold rush, dredge mining"},
        {"name": "Barkerville, British Columbia", "lat": 53.0680, "lon": -121.5170,
         "country": "Canada", "year": 1862,
         "notes": "Cariboo Gold Rush, largest town north of San Francisco at its peak"},
        {"name": "Thames, Coromandel", "lat": -36.8619, "lon": 175.5375,
         "country": "New Zealand", "year": 1867,
         "notes": "Coromandel Gold Rush, quartz mining drove regional growth"},
        {"name": "Otago, Gabriel's Gully", "lat": -45.8788, "lon": 170.5028,
         "country": "New Zealand", "year": 1861,
         "notes": "Central Otago Gold Rush, Gabriel Read's discovery at Tuapeka"},
        {"name": "Dahlonega, Georgia", "lat": 34.5326, "lon": -83.9849,
         "country": "USA", "year": 1828,
         "notes": "First major US gold rush, 20 years before California, US Mint branch"},
        {"name": "Cripple Creek, Colorado", "lat": 38.7467, "lon": -105.1783,
         "country": "USA", "year": 1891,
         "notes": "Last great Colorado gold rush, over $1 billion extracted"},
        {"name": "Juneau, Alaska", "lat": 58.3005, "lon": -134.4197,
         "country": "USA", "year": 1880,
         "notes": "Joe Juneau and Richard Harris discovery, Alaska-Juneau mine"},
        {"name": "Beechworth, Victoria", "lat": -36.3575, "lon": 146.6886,
         "country": "Australia", "year": 1852,
         "notes": "Rich alluvial goldfield, Ned Kelly connections, heritage town"},
        {"name": "Deadwood, South Dakota", "lat": 44.3767, "lon": -103.7296,
         "country": "USA", "year": 1876,
         "notes": "Black Hills Gold Rush, Wild Bill Hickok era, Homestake Mine"},
        {"name": "Las Medulas, Leon", "lat": 42.4600, "lon": -6.7700,
         "country": "Spain", "year": -25,
         "notes": "Roman gold mine using hydraulic mining, UNESCO World Heritage Site"},
    ]


# ---------------------------------------------------------------------------
# 4. Currency Museums  (18 locations)
# ---------------------------------------------------------------------------

def _currency_museums_data():
    """Major currency and money museums worldwide."""
    return [
        {"name": "Bank of England Museum", "lat": 51.5142, "lon": -0.0885,
         "country": "UK",
         "notes": "Threadneedle Street, history of British currency, real gold bars to hold"},
        {"name": "Federal Reserve Bank of New York - Gold Vault", "lat": 40.7084, "lon": -74.0083,
         "country": "USA",
         "notes": "Largest gold repository in the world, 80 feet below street level"},
        {"name": "Smithsonian National Numismatic Collection", "lat": 38.8913, "lon": -77.0299,
         "country": "USA",
         "notes": "National Museum of American History, 1.6 million objects including 1804 dollar"},
        {"name": "Deutsche Bundesbank Money Museum", "lat": 50.1109, "lon": 8.6821,
         "country": "Germany",
         "notes": "Frankfurt, from cowrie shells to cryptocurrency, interactive exhibits"},
        {"name": "Monnaie de Paris Museum", "lat": 48.8566, "lon": 2.3422,
         "country": "France",
         "notes": "11 Quai de Conti, minting demonstrations, 1160 years of coinage history"},
        {"name": "Royal Mint Experience", "lat": 51.5879, "lon": -3.2889,
         "country": "UK",
         "notes": "Llantrisant, strike your own coin, see coins being made on factory floor"},
        {"name": "Museum of the National Bank of Belgium", "lat": 50.8503, "lon": 4.3517,
         "country": "Belgium",
         "notes": "Brussels, economic and monetary history, free admission"},
        {"name": "Swiss National Museum - Coin Cabinet", "lat": 47.3769, "lon": 8.5417,
         "country": "Switzerland",
         "notes": "Zurich, 100,000+ Swiss and international coins, medals, and banknotes"},
        {"name": "Bank of Japan Currency Museum", "lat": 35.6862, "lon": 139.7726,
         "country": "Japan",
         "notes": "Nihonbashi, wadokaichin to modern yen, 3000 years of monetary history"},
        {"name": "Reserve Bank of Australia Museum", "lat": -33.8688, "lon": 151.2093,
         "country": "Australia",
         "notes": "Sydney, polymer banknote invention story, Australian currency evolution"},
        {"name": "Perth Mint Gold Exhibition", "lat": -31.9505, "lon": 115.8605,
         "country": "Australia",
         "notes": "Gold pouring demonstrations, 1 tonne gold coin on display"},
        {"name": "American Numismatic Association Money Museum", "lat": 38.8339, "lon": -104.8253,
         "country": "USA",
         "notes": "Colorado Springs, Harry W. Bass Jr. Collection, premier US numismatic museum"},
        {"name": "Bode Museum Numismatic Collection", "lat": 52.5225, "lon": 13.3944,
         "country": "Germany",
         "notes": "Berlin Museum Island, 500,000+ coins and medals from antiquity to present"},
        {"name": "Shanghai Museum Coin Gallery", "lat": 31.2286, "lon": 121.4747,
         "country": "China",
         "notes": "People's Square, Chinese coin history spanning 3,000 years"},
        {"name": "National Museum of India - Coin Gallery", "lat": 28.6117, "lon": 77.2195,
         "country": "India",
         "notes": "New Delhi, from punch-marked coins to Mughal gold mohurs"},
        {"name": "Museum of the Central Bank of Brazil", "lat": -15.7975, "lon": -47.8919,
         "country": "Brazil",
         "notes": "Brasilia, Brazilian currency evolution and hyperinflation-era banknotes"},
        {"name": "Heberden Coin Room, Ashmolean Museum", "lat": 51.7548, "lon": -1.2600,
         "country": "UK",
         "notes": "Oxford, 300,000+ coins from all periods, oldest public museum collection"},
        {"name": "Cabinet des Medailles, Bibliotheque Nationale", "lat": 48.8339, "lon": 2.3389,
         "country": "France",
         "notes": "Paris, one of the world's largest coin collections, royal French medals"},
        {"name": "Austrian National Library - Coin Cabinet", "lat": 48.2060, "lon": 16.3660,
         "country": "Austria",
         "notes": "Vienna Hofburg, Habsburg numismatic collection, 700,000+ objects"},
        {"name": "Hermitage Museum Numismatic Gallery", "lat": 59.9398, "lon": 30.3146,
         "country": "Russia",
         "notes": "St. Petersburg, over 1 million coins in Russian imperial collection"},
    ]


# ---------------------------------------------------------------------------
# 5. Hyperinflation Sites  (17 locations)
# ---------------------------------------------------------------------------

def _hyperinflation_sites_data():
    """Sites associated with historic hyperinflation events."""
    return [
        {"name": "Berlin - Weimar Republic Papiermark", "lat": 52.5200, "lon": 13.4050,
         "country": "Germany", "year": 1923, "peak_rate": "29,500%/month",
         "notes": "Workers paid twice daily with wheelbarrows of cash, bread cost billions"},
        {"name": "Budapest - Hungarian Pengo Crisis", "lat": 47.4979, "lon": 19.0402,
         "country": "Hungary", "year": 1946, "peak_rate": "4.19 x 10^16 %/month",
         "notes": "Worst hyperinflation in recorded history; 100 quintillion pengo banknotes"},
        {"name": "Harare - Zimbabwe Dollar Collapse", "lat": -17.8252, "lon": 31.0335,
         "country": "Zimbabwe", "year": 2008, "peak_rate": "79.6 billion %/month",
         "notes": "100 trillion dollar notes printed, currency abandoned for USD"},
        {"name": "Caracas - Venezuelan Bolivar Crisis", "lat": 10.4806, "lon": -66.9036,
         "country": "Venezuela", "year": 2018, "peak_rate": "1,698,488%/year",
         "notes": "Ongoing crisis, multiple redenominations, mass emigration"},
        {"name": "Belgrade - Yugoslav Dinar Meltdown", "lat": 44.7866, "lon": 20.4489,
         "country": "Serbia", "year": 1994, "peak_rate": "313 million %/month",
         "notes": "Second worst hyperinflation ever; 500 billion dinar banknotes issued"},
        {"name": "Athens - Greek Drachma WWII Collapse", "lat": 37.9838, "lon": 23.7275,
         "country": "Greece", "year": 1944, "peak_rate": "8.55 billion %/month",
         "notes": "Axis occupation hyperinflation, economy exploited by occupying forces"},
        {"name": "Taipei - Old Taiwan Dollar Inflation", "lat": 25.0330, "lon": 121.5654,
         "country": "Taiwan", "year": 1949, "peak_rate": "3,486%/year",
         "notes": "Post-war inflation ended by New Taiwan Dollar monetary reform"},
        {"name": "Beijing - Gold Yuan Collapse", "lat": 39.9042, "lon": 116.4074,
         "country": "China", "year": 1949, "peak_rate": "5,070%/month",
         "notes": "Chinese Civil War era, Gold Yuan currency collapsed within months"},
        {"name": "Lima - Peruvian Inti Hyperinflation", "lat": -12.0464, "lon": -77.0428,
         "country": "Peru", "year": 1990, "peak_rate": "7,481%/year",
         "notes": "Fujishock stabilization program ended crisis, New Sol introduced"},
        {"name": "Minsk - Belarusian Ruble Instability", "lat": 53.9045, "lon": 27.5615,
         "country": "Belarus", "year": 1994, "peak_rate": "1,996%/year",
         "notes": "Post-Soviet monetary collapse, three redenominations since independence"},
        {"name": "Managua - Nicaraguan Cordoba Crisis", "lat": 12.1150, "lon": -86.2362,
         "country": "Nicaragua", "year": 1988, "peak_rate": "33,547%/year",
         "notes": "Sandinista-era economic crisis with currency reform following"},
        {"name": "Kinshasa - Zairean Zaire Collapse", "lat": -4.4419, "lon": 15.2663,
         "country": "DR Congo", "year": 1994, "peak_rate": "23,773%/year",
         "notes": "Mobutu-era economic collapse, Zaire currency abandoned post-regime change"},
        {"name": "Tbilisi - Georgian Coupon Crisis", "lat": 41.7151, "lon": 44.8271,
         "country": "Georgia", "year": 1994, "peak_rate": "7,844%/year",
         "notes": "Post-Soviet hyperinflation stabilized by introduction of the Lari"},
        {"name": "Sarajevo - Bosnian Wartime Inflation", "lat": 43.8563, "lon": 18.4131,
         "country": "Bosnia", "year": 1993, "peak_rate": "322%/month",
         "notes": "Wartime siege hyperinflation during the Bosnian conflict"},
        {"name": "Ankara - Turkish Lira Crisis", "lat": 39.9334, "lon": 32.8597,
         "country": "Turkey", "year": 2001, "peak_rate": "68.5%/year",
         "notes": "Banking crisis, IMF bailout, New Turkish Lira redenomination in 2005"},
        {"name": "Buenos Aires - Argentine Austral Crisis", "lat": -34.6037, "lon": -58.3816,
         "country": "Argentina", "year": 1989, "peak_rate": "12,000%/year",
         "notes": "Austral hyperinflation led to Convertibility Plan pegging peso to USD"},
        {"name": "Hanoi - Vietnamese Dong Inflation", "lat": 21.0285, "lon": 105.8542,
         "country": "Vietnam", "year": 1988, "peak_rate": "774%/year",
         "notes": "Doi Moi reforms stabilized economy after severe post-war inflation"},
        {"name": "Luanda - Angolan Kwanza Crisis", "lat": -8.8390, "lon": 13.2894,
         "country": "Angola", "year": 1996, "peak_rate": "4,145%/year",
         "notes": "Civil war hyperinflation, multiple currency reforms since independence"},
        {"name": "Maputo - Mozambican Metical Crisis", "lat": -25.9692, "lon": 32.5732,
         "country": "Mozambique", "year": 1994, "peak_rate": "70%/year",
         "notes": "Post-civil war inflation, New Metical redenomination in 2006"},
    ]


# ---------------------------------------------------------------------------
# 6. Silk Road Trade Currencies  (22 locations)
# ---------------------------------------------------------------------------

def _silk_road_currencies_data():
    """Silk Road trade routes, cities, and currency exchange sites."""
    return [
        {"name": "Xi'an (Chang'an) - Eastern Terminus", "lat": 34.2658, "lon": 108.9541,
         "country": "China", "era": "2nd century BC",
         "notes": "Start of the Silk Road, Ban Liang and Wu Zhu cash coins dominated trade"},
        {"name": "Dunhuang - Mogao Cave Coin Hoards", "lat": 40.1421, "lon": 94.6619,
         "country": "China", "era": "4th century",
         "notes": "Gateway to the desert, coin hoards discovered in sealed cave temples"},
        {"name": "Turpan (Gaochang) - Oasis Crossroads", "lat": 42.9513, "lon": 89.1895,
         "country": "China", "era": "1st century",
         "notes": "Oasis city with Sino-Kharosthi bilingual coins from multiple kingdoms"},
        {"name": "Kashgar - Route Junction", "lat": 39.4547, "lon": 75.9797,
         "country": "China", "era": "2nd century BC",
         "notes": "Junction of northern and southern Silk Road, major currency exchange point"},
        {"name": "Samarkand - Sogdian Trade Center", "lat": 39.6542, "lon": 66.9597,
         "country": "Uzbekistan", "era": "4th century BC",
         "notes": "Sogdian merchant coins and Islamic dirhams, Registan trading hub"},
        {"name": "Bukhara - Islamic Mint City", "lat": 39.7681, "lon": 64.4556,
         "country": "Uzbekistan", "era": "6th century",
         "notes": "Bukhar Khuda coins, major Samanid and Abbasid-era mint"},
        {"name": "Merv (Mary) - Empire Crossroads", "lat": 37.6639, "lon": 62.1599,
         "country": "Turkmenistan", "era": "3rd century BC",
         "notes": "Seleucid and Parthian coins, largest city in the world circa 1150 AD"},
        {"name": "Balkh (Bactra) - Mother of Cities", "lat": 36.7583, "lon": 66.8975,
         "country": "Afghanistan", "era": "6th century BC",
         "notes": "Greek, Kushan, and Islamic coin finds across millennia of habitation"},
        {"name": "Taxila - University and Mint City", "lat": 33.7463, "lon": 72.7988,
         "country": "Pakistan", "era": "5th century BC",
         "notes": "Indo-Greek and Gandharan coins, major ancient learning center"},
        {"name": "Kabul - Greco-Bactrian Treasury", "lat": 34.5553, "lon": 69.2075,
         "country": "Afghanistan", "era": "2nd century BC",
         "notes": "Greco-Bactrian treasure hoards, Kushan gold coins, trade nexus"},
        {"name": "Baghdad - Abbasid Gold Dinar Capital", "lat": 33.3152, "lon": 44.3661,
         "country": "Iraq", "era": "8th century",
         "notes": "Round City of al-Mansur, gold dinar center of the Islamic Golden Age"},
        {"name": "Isfahan - Safavid Caravanserai Hub", "lat": 32.6546, "lon": 51.6680,
         "country": "Iran", "era": "7th century",
         "notes": "Safavid-era coins at Naqsh-e Jahan, half the world at its peak"},
        {"name": "Aleppo - Ancient Market Crossroads", "lat": 36.2021, "lon": 37.1343,
         "country": "Syria", "era": "3rd millennium BC",
         "notes": "Seleucid and Roman coin finds in one of the oldest continuously inhabited cities"},
        {"name": "Palmyra - Desert Trade Oasis", "lat": 34.5502, "lon": 38.2838,
         "country": "Syria", "era": "1st century",
         "notes": "Palmyrene trade coins linking Roman and Parthian economies"},
        {"name": "Constantinople (Istanbul) - Byzantine Solidus", "lat": 41.0082, "lon": 28.9784,
         "country": "Turkey", "era": "330 AD",
         "notes": "Byzantine gold solidus was the dollar of the medieval world for 700 years"},
        {"name": "Antioch - Seleucid Tetradrachm Mint", "lat": 36.2000, "lon": 36.1500,
         "country": "Turkey", "era": "300 BC",
         "notes": "Major Seleucid mint, Alexander-type tetradrachms traded across empires"},
        {"name": "Herat - Timurid Mint Center", "lat": 34.3529, "lon": 62.2040,
         "country": "Afghanistan", "era": "3rd century BC",
         "notes": "Timurid and Mughal coin production center on the western Silk Road"},
        {"name": "Tashkent - Chach Region Coinage", "lat": 41.2995, "lon": 69.2401,
         "country": "Uzbekistan", "era": "5th century",
         "notes": "Chach region Turkic coins, Islamic-era numismatics hub"},
        {"name": "Ctesiphon - Sasanian Silver Drachms", "lat": 33.0925, "lon": 44.5800,
         "country": "Iraq", "era": "2nd century BC",
         "notes": "Parthian and Sasanian silver drachm mint, capital of two empires"},
        {"name": "Petra - Nabataean Trade Coins", "lat": 30.3285, "lon": 35.4444,
         "country": "Jordan", "era": "4th century BC",
         "notes": "Nabataean coins on the Incense Route, carved city of traders"},
        {"name": "Hormuz Island - Indian Ocean Gateway", "lat": 27.0586, "lon": 56.4608,
         "country": "Iran", "era": "14th century",
         "notes": "Portuguese-era trade coins, gateway between Silk Road and Indian Ocean"},
        {"name": "Trabzon (Trebizond) - Black Sea Terminus", "lat": 41.0027, "lon": 39.7168,
         "country": "Turkey", "era": "8th century BC",
         "notes": "Northern Silk Road terminus, Comnenian Empire gold coins"},
    ]


# ---------------------------------------------------------------------------
# 7. Central Banks  (25 locations)
# ---------------------------------------------------------------------------

def _central_banks_data():
    """Major central banks of the world."""
    return [
        {"name": "Federal Reserve (Eccles Building)", "lat": 38.8928, "lon": -77.0476,
         "country": "USA", "founded": 1913, "currency": "USD",
         "notes": "World's most influential central bank, dual mandate for employment and prices"},
        {"name": "European Central Bank", "lat": 50.1109, "lon": 8.7034,
         "country": "Germany", "founded": 1998, "currency": "EUR",
         "notes": "Frankfurt Ostend, manages euro monetary policy for 20 member states"},
        {"name": "Bank of England", "lat": 51.5142, "lon": -0.0885,
         "country": "UK", "founded": 1694, "currency": "GBP",
         "notes": "Old Lady of Threadneedle Street, model for modern central banking"},
        {"name": "Bank of Japan", "lat": 35.6855, "lon": 139.7700,
         "country": "Japan", "founded": 1882, "currency": "JPY",
         "notes": "Nihonbashi, pioneered quantitative easing and yield curve control"},
        {"name": "People's Bank of China", "lat": 39.9110, "lon": 116.3553,
         "country": "China", "founded": 1948, "currency": "CNY",
         "notes": "Beijing, manages world's largest foreign exchange reserves"},
        {"name": "Swiss National Bank", "lat": 46.9480, "lon": 7.4474,
         "country": "Switzerland", "founded": 1907, "currency": "CHF",
         "notes": "Bern, safe-haven currency, manages gold reserves"},
        {"name": "Reserve Bank of India", "lat": 18.9322, "lon": 72.8347,
         "country": "India", "founded": 1935, "currency": "INR",
         "notes": "Mumbai Fort, manages monetary policy for 1.4 billion people"},
        {"name": "Bank of Canada", "lat": 45.4194, "lon": -75.7010,
         "country": "Canada", "founded": 1934, "currency": "CAD",
         "notes": "Ottawa, pioneered inflation targeting framework in 1991"},
        {"name": "Reserve Bank of Australia", "lat": -33.8688, "lon": 151.2093,
         "country": "Australia", "founded": 1960, "currency": "AUD",
         "notes": "Martin Place Sydney, pioneered polymer banknote technology"},
        {"name": "Banco Central do Brasil", "lat": -15.7975, "lon": -47.8919,
         "country": "Brazil", "founded": 1964, "currency": "BRL",
         "notes": "Brasilia, manages 9th largest economy, Pix instant payment system"},
        {"name": "Central Bank of Russia", "lat": 55.7558, "lon": 37.6173,
         "country": "Russia", "founded": 1990, "currency": "RUB",
         "notes": "Moscow Neglinnaya Street, manages world's 5th largest gold reserves"},
        {"name": "Sveriges Riksbank", "lat": 59.3293, "lon": 18.0686,
         "country": "Sweden", "founded": 1668, "currency": "SEK",
         "notes": "World's oldest central bank, exploring digital e-krona currency"},
        {"name": "Bank of Korea", "lat": 37.5597, "lon": 126.9820,
         "country": "South Korea", "founded": 1950, "currency": "KRW",
         "notes": "Seoul Namdaemun, supports major export-driven economy"},
        {"name": "Central Bank of Turkey", "lat": 39.9334, "lon": 32.8597,
         "country": "Turkey", "founded": 1930, "currency": "TRY",
         "notes": "Ankara, navigating persistent inflationary pressures"},
        {"name": "Saudi Central Bank (SAMA)", "lat": 24.6877, "lon": 46.7219,
         "country": "Saudi Arabia", "founded": 1952, "currency": "SAR",
         "notes": "Riyadh, manages petrodollar reserves and USD peg"},
        {"name": "Banco de Mexico", "lat": 19.4326, "lon": -99.1332,
         "country": "Mexico", "founded": 1925, "currency": "MXN",
         "notes": "Centro Historico, Latin America's second-largest central bank"},
        {"name": "Bank Indonesia", "lat": -6.1751, "lon": 106.8272,
         "country": "Indonesia", "founded": 1953, "currency": "IDR",
         "notes": "Jakarta, manages currency for 275 million people across 17,000 islands"},
        {"name": "South African Reserve Bank", "lat": -25.7479, "lon": 28.2293,
         "country": "South Africa", "founded": 1921, "currency": "ZAR",
         "notes": "Pretoria, oldest central bank in Africa, inflation targeting since 2000"},
        {"name": "Norges Bank", "lat": 59.9139, "lon": 10.7522,
         "country": "Norway", "founded": 1816, "currency": "NOK",
         "notes": "Oslo, manages $1.4 trillion Government Pension Fund Global"},
        {"name": "Reserve Bank of New Zealand", "lat": -41.2866, "lon": 174.7756,
         "country": "New Zealand", "founded": 1934, "currency": "NZD",
         "notes": "Wellington, pioneered explicit inflation targeting in 1990"},
        {"name": "Central Bank of Nigeria", "lat": 9.0579, "lon": 7.4951,
         "country": "Nigeria", "founded": 1958, "currency": "NGN",
         "notes": "Abuja, manages Africa's largest economy by GDP"},
        {"name": "Bank of Thailand", "lat": 13.7563, "lon": 100.5018,
         "country": "Thailand", "founded": 1942, "currency": "THB",
         "notes": "Bangkok, managed baht through 1997 Asian financial crisis"},
        {"name": "Bangko Sentral ng Pilipinas", "lat": 14.5623, "lon": 121.0603,
         "country": "Philippines", "founded": 1993, "currency": "PHP",
         "notes": "Manila, Philippine peso management and financial stability"},
        {"name": "Central Bank of Egypt", "lat": 30.0444, "lon": 31.2357,
         "country": "Egypt", "founded": 1961, "currency": "EGP",
         "notes": "Cairo, manages Egyptian pound, major IMF reform programs"},
        {"name": "Bank Al-Maghrib", "lat": 34.0209, "lon": -6.8416,
         "country": "Morocco", "founded": 1959, "currency": "MAD",
         "notes": "Rabat, manages Moroccan dirham pegged to EUR/USD basket"},
    ]


# ---------------------------------------------------------------------------
# 8. Pirate Treasure & Coin Hoards  (22 locations)
# ---------------------------------------------------------------------------

def _pirate_treasure_data():
    """Pirate treasure finds, sunken ships, and major coin hoards."""
    return [
        {"name": "Nuestra Senora de Atocha Wreck", "lat": 24.5148, "lon": -82.1862,
         "country": "USA", "year_found": 1985,
         "notes": "Mel Fisher's legendary find: $450M in gold, silver bars, and emeralds"},
        {"name": "Black Swan Project - Straits of Gibraltar", "lat": 36.3000, "lon": -7.1000,
         "country": "Atlantic Ocean", "year_found": 2007,
         "notes": "Odyssey Marine recovered $500M silver from Spanish frigate Mercedes"},
        {"name": "Whydah Gally Wreck - Cape Cod", "lat": 41.7700, "lon": -69.9500,
         "country": "USA", "year_found": 1984,
         "notes": "Black Sam Bellamy's flagship, only authenticated pirate shipwreck ever found"},
        {"name": "Port Royal - Sunken Pirate City", "lat": 17.9344, "lon": -76.8410,
         "country": "Jamaica", "year_found": 1692,
         "notes": "Wickedest city on Earth sank in 1692 earthquake, underwater archaeology ongoing"},
        {"name": "Quedagh Merchant - Captain Kidd", "lat": 19.3000, "lon": -69.3000,
         "country": "Dominican Republic", "year_found": 2007,
         "notes": "Captain Kidd's abandoned merchant prize found in shallow water"},
        {"name": "San Jose Galleon - Holy Grail Wreck", "lat": 10.3910, "lon": -76.0064,
         "country": "Colombia", "year_found": 2015,
         "notes": "Holy Grail of shipwrecks off Cartagena, estimated $17B in gold and emeralds"},
        {"name": "Treasure of Lima - Cocos Island", "lat": 5.5228, "lon": -87.0539,
         "country": "Costa Rica", "year_found": None,
         "notes": "Legendary lost treasure, hundreds of expeditions since 1820, never found"},
        {"name": "SS Central America - Ship of Gold", "lat": 31.8000, "lon": -77.0000,
         "country": "USA", "year_found": 1988,
         "notes": "21 tons of California Gold Rush gold recovered from 7,200 feet deep"},
        {"name": "Flor de la Mar - Malacca Strait", "lat": 2.5000, "lon": 104.5000,
         "country": "Malaysia", "year_found": None,
         "notes": "Portuguese carrack sank 1511, possibly richest single cargo ever lost"},
        {"name": "Hoxne Hoard - Suffolk", "lat": 52.3453, "lon": 1.1900,
         "country": "UK", "year_found": 1992,
         "notes": "15,234 Roman gold and silver coins plus 200 silver objects, metal detected"},
        {"name": "Staffordshire Hoard", "lat": 52.6600, "lon": -1.9400,
         "country": "UK", "year_found": 2009,
         "notes": "Largest Anglo-Saxon gold hoard: 11 lbs of gold, 3 lbs of silver"},
        {"name": "Spillings Hoard - Gotland", "lat": 57.7200, "lon": 18.8300,
         "country": "Sweden", "year_found": 1999,
         "notes": "Largest Viking silver hoard: 67 kg total, 14,295 coins from 3 continents"},
        {"name": "Cuerdale Hoard - Lancashire", "lat": 53.7700, "lon": -2.6600,
         "country": "UK", "year_found": 1840,
         "notes": "Largest Viking silver hoard in Western Europe, 8,600+ items, 40 kg silver"},
        {"name": "Saddle Ridge Hoard - Sierra Nevada", "lat": 38.3000, "lon": -120.5000,
         "country": "USA", "year_found": 2013,
         "notes": "1,427 Gold Rush-era US gold coins worth $10M found buried in tin cans"},
        {"name": "SS Republic Wreck - Atlantic", "lat": 31.2500, "lon": -79.7000,
         "country": "USA", "year_found": 2003,
         "notes": "Civil War-era sidewheel steamship, 51,000+ coins and artifacts recovered"},
        {"name": "Caesarea Sunken Gold Coins", "lat": 32.5000, "lon": 34.8903,
         "country": "Israel", "year_found": 2015,
         "notes": "2,000 Fatimid-era gold coins found by recreational divers off ancient port"},
        {"name": "Bactrian Gold - Tillya Tepe", "lat": 36.6600, "lon": 65.7500,
         "country": "Afghanistan", "year_found": 1978,
         "notes": "20,000+ gold artifacts from six Kushan-era nomadic burial mounds"},
        {"name": "Oak Island Money Pit - Nova Scotia", "lat": 44.5131, "lon": -64.2990,
         "country": "Canada", "year_found": 1795,
         "notes": "230+ years of treasure hunting, booby-trapped pit, reality TV show ongoing"},
        {"name": "Mel Fisher Maritime Museum", "lat": 24.5592, "lon": -81.8018,
         "country": "USA", "year_found": 1985,
         "notes": "Key West museum with Atocha and Santa Margarita treasure on display"},
        {"name": "Quedlinburg Treasure", "lat": 51.7893, "lon": 11.1500,
         "country": "Germany", "year_found": 1945,
         "notes": "Medieval church treasury looted in WWII, gold and gem-encrusted manuscripts"},
        {"name": "Mildenhall Treasure - Suffolk", "lat": 52.3453, "lon": 0.5200,
         "country": "UK", "year_found": 1942,
         "notes": "34 Roman silver pieces including Great Dish, now in British Museum"},
        {"name": "Sevso Treasure", "lat": 46.5000, "lon": 17.0000,
         "country": "Hungary", "year_found": 1975,
         "notes": "14 large Roman silver vessels, controversial ownership history"},
        {"name": "Frome Hoard - Somerset", "lat": 51.2279, "lon": -2.3213,
         "country": "UK", "year_found": 2010,
         "notes": "52,503 Roman coins in a single pot, largest ever from Britain"},
        {"name": "Treasure of Guarrazar - Toledo", "lat": 39.8628, "lon": -4.0273,
         "country": "Spain", "year_found": 1858,
         "notes": "Visigothic votive gold crowns and crosses, 7th century regalia"},
    ]


# ---------------------------------------------------------------------------
# 9. Cryptocurrency Hubs  (18 locations)
# ---------------------------------------------------------------------------

def _crypto_hubs_data():
    """Major cryptocurrency hubs, exchanges, and mining centers."""
    return [
        {"name": "Zug - Crypto Valley", "lat": 47.1661, "lon": 8.5155,
         "country": "Switzerland", "type": "Ecosystem",
         "notes": "Ethereum Foundation HQ, 1000+ blockchain companies, favorable regulations"},
        {"name": "San Francisco - Coinbase & Kraken", "lat": 37.7749, "lon": -122.4194,
         "country": "USA", "type": "Exchange",
         "notes": "Coinbase (NASDAQ-listed) and Kraken headquarters, US crypto capital"},
        {"name": "Singapore - Asian Crypto Hub", "lat": 1.3521, "lon": 103.8198,
         "country": "Singapore", "type": "Ecosystem",
         "notes": "Progressive MAS licensing, Crypto.com, Bybit, and DBS digital exchange"},
        {"name": "Miami - Bitcoin City", "lat": 25.7617, "lon": -80.1918,
         "country": "USA", "type": "Ecosystem",
         "notes": "Annual Bitcoin Conference, MiamiCoin, pro-crypto city government"},
        {"name": "El Salvador - Bitcoin Legal Tender", "lat": 13.6929, "lon": -89.2182,
         "country": "El Salvador", "type": "Adoption",
         "notes": "First country to adopt Bitcoin as legal tender in September 2021"},
        {"name": "Hong Kong - Exchange Hub", "lat": 22.3193, "lon": 114.1694,
         "country": "China", "type": "Exchange",
         "notes": "BitMEX origin, OSL licensed exchange, new crypto licensing regime"},
        {"name": "Malta - Blockchain Island", "lat": 35.8997, "lon": 14.5146,
         "country": "Malta", "type": "Regulation",
         "notes": "Virtual Financial Assets Act, Binance initially relocated here"},
        {"name": "Dubai - DMCC Crypto Centre", "lat": 25.2048, "lon": 55.2708,
         "country": "UAE", "type": "Ecosystem",
         "notes": "VARA regulator, Binance and Bybit regional HQs, zero income tax"},
        {"name": "Tallinn - Digital Society Pioneer", "lat": 59.4370, "lon": 24.7536,
         "country": "Estonia", "type": "Regulation",
         "notes": "E-residency, early crypto licensing, blockchain-backed government services"},
        {"name": "Toronto - Ethereum Birthplace", "lat": 43.6532, "lon": -79.3832,
         "country": "Canada", "type": "Innovation",
         "notes": "Vitalik Buterin conceived Ethereum here, strong Web3 developer ecosystem"},
        {"name": "Reykjavik - Geothermal Mining", "lat": 64.1466, "lon": -21.9426,
         "country": "Iceland", "type": "Mining",
         "notes": "Cheap geothermal and hydroelectric power for Bitcoin mining farms"},
        {"name": "Chelan County, WA - Hydro Mining", "lat": 47.8395, "lon": -120.0160,
         "country": "USA", "type": "Mining",
         "notes": "Cheapest electricity in USA, large-scale crypto mining operations"},
        {"name": "Sichuan Province (Chengdu)", "lat": 30.5728, "lon": 104.0668,
         "country": "China", "type": "Mining",
         "notes": "Was world's largest mining region before China's 2021 mining ban"},
        {"name": "Liechtenstein - Blockchain Act", "lat": 47.1660, "lon": 9.5554,
         "country": "Liechtenstein", "type": "Regulation",
         "notes": "Token and Trustworthy Technology Service Providers Act (2020)"},
        {"name": "London - Crypto Finance Hub", "lat": 51.5074, "lon": -0.1278,
         "country": "UK", "type": "Ecosystem",
         "notes": "Major crypto VC hub, FCA regulation, numerous blockchain startups"},
        {"name": "Austin, TX - Web3 Capital", "lat": 30.2672, "lon": -97.7431,
         "country": "USA", "type": "Ecosystem",
         "notes": "Growing crypto hub, Consensus conference, no state income tax"},
        {"name": "Lisbon - Crypto Nomad Hub", "lat": 38.7223, "lon": -9.1393,
         "country": "Portugal", "type": "Ecosystem",
         "notes": "Digital nomad visa, formerly zero crypto tax, thriving Web3 community"},
        {"name": "Central African Republic - Bitcoin Adoption", "lat": 4.3947, "lon": 18.5582,
         "country": "CAR", "type": "Adoption",
         "notes": "Second country to adopt Bitcoin as legal tender in April 2022"},
        {"name": "Seoul - Upbit & Bithumb", "lat": 37.5665, "lon": 126.9780,
         "country": "South Korea", "type": "Exchange",
         "notes": "Korea's largest crypto exchanges, 30%+ of global altcoin volume"},
        {"name": "Bermuda - Digital Asset Regulation", "lat": 32.3078, "lon": -64.7505,
         "country": "Bermuda", "type": "Regulation",
         "notes": "Digital Asset Business Act 2018, progressive offshore crypto framework"},
        {"name": "Tokyo - bitFlyer & Mt. Gox Legacy", "lat": 35.6762, "lon": 139.6503,
         "country": "Japan", "type": "Exchange",
         "notes": "FSA-licensed exchanges, Mt. Gox 2014 collapse shaped global regulation"},
    ]


# ---------------------------------------------------------------------------
# 10. Banknote Printing Works  (18 locations)
# ---------------------------------------------------------------------------

def _banknote_printing_data():
    """Major banknote printing and security printing facilities worldwide."""
    return [
        {"name": "Bureau of Engraving and Printing - Washington DC", "lat": 38.8863, "lon": -77.0327,
         "country": "USA", "founded": 1862,
         "notes": "14th & C Street SW, prints all US paper currency, public tours available"},
        {"name": "Bureau of Engraving and Printing - Fort Worth", "lat": 32.7473, "lon": -97.3306,
         "country": "USA", "founded": 1991,
         "notes": "Western Currency Facility, supplements DC output, FW prefix on notes"},
        {"name": "De La Rue - Basingstoke", "lat": 51.2460, "lon": -0.7670,
         "country": "UK", "founded": 1821,
         "notes": "World's largest commercial banknote printer, prints for 140+ countries"},
        {"name": "Giesecke+Devrient - Munich", "lat": 48.1351, "lon": 11.5820,
         "country": "Germany", "founded": 1852,
         "notes": "Prints banknotes for 60+ central banks, security technology leader"},
        {"name": "Orell Fussli Security Printing - Zurich", "lat": 47.3769, "lon": 8.5417,
         "country": "Switzerland", "founded": 1519,
         "notes": "Prints Swiss franc banknotes, 500+ years of printing heritage"},
        {"name": "Canadian Bank Note Company - Ottawa", "lat": 45.3850, "lon": -75.6960,
         "country": "Canada", "founded": 1897,
         "notes": "Prints Canadian polymer banknotes, passports, and lottery tickets"},
        {"name": "Note Printing Australia - Craigieburn", "lat": -37.8055, "lon": 144.9765,
         "country": "Australia", "founded": 1981,
         "notes": "Invented polymer (plastic) banknote technology, exports globally"},
        {"name": "Banco de Mexico Printing Facility", "lat": 19.3040, "lon": -99.1530,
         "country": "Mexico", "founded": 1969,
         "notes": "Prints Mexican peso polymer banknotes with advanced security features"},
        {"name": "China Banknote Printing and Minting - Beijing", "lat": 39.9042, "lon": 116.4074,
         "country": "China", "founded": 1908,
         "notes": "Multiple printing plants across China, yuan notes and digital yuan R&D"},
        {"name": "Security Printing and Minting Corp of India", "lat": 28.5824, "lon": 77.0520,
         "country": "India", "founded": 1943,
         "notes": "Nashik and Dewas plants, prints rupee banknotes for 1.4 billion people"},
        {"name": "National Printing Bureau of Japan - Tokyo", "lat": 35.7510, "lon": 139.7432,
         "country": "Japan", "founded": 1871,
         "notes": "Prints yen banknotes with world-leading anti-counterfeiting technology"},
        {"name": "Korea Minting and Security Printing - Daejeon", "lat": 36.3504, "lon": 127.3845,
         "country": "South Korea", "founded": 1951,
         "notes": "Prints Korean won banknotes, passports, and security documents"},
        {"name": "Bundesdruckerei - Berlin", "lat": 52.4870, "lon": 13.3650,
         "country": "Germany", "founded": 1879,
         "notes": "Federal Printing Office, euro banknotes, passports, and ID cards"},
        {"name": "Oberthur Fiduciaire - Rennes", "lat": 48.1173, "lon": -1.6778,
         "country": "France", "founded": 1842,
         "notes": "Prints banknotes for African, Middle Eastern, and Asian nations"},
        {"name": "De La Rue Lanka - Biyagama", "lat": 7.2906, "lon": 80.6337,
         "country": "Sri Lanka", "founded": 1985,
         "notes": "De La Rue subsidiary, exports printed banknotes to multiple countries"},
        {"name": "Crane Currency - Tumba Bruk", "lat": 59.1667, "lon": 17.8333,
         "country": "Sweden", "founded": 1755,
         "notes": "Oldest surviving banknote paper mill, prints Swedish krona notes"},
        {"name": "Real Casa de la Moneda - Madrid", "lat": 40.4168, "lon": -3.7038,
         "country": "Spain", "founded": 1893,
         "notes": "FNMT, prints euro banknotes, Spanish stamps, and lottery tickets"},
        {"name": "Istituto Poligrafico e Zecca dello Stato - Rome", "lat": 41.9028, "lon": 12.4964,
         "country": "Italy", "founded": 1928,
         "notes": "Prints Italian-assigned euro banknotes, passports, and stamps"},
        {"name": "Banque de France Printing Works - Chamalières", "lat": 45.7728, "lon": 3.0500,
         "country": "France", "founded": 1914,
         "notes": "Prints French-assigned euro banknotes near Clermont-Ferrand"},
        {"name": "Casa da Moeda do Brasil - Rio", "lat": -22.9068, "lon": -43.1729,
         "country": "Brazil", "founded": 1694,
         "notes": "Prints Brazilian real banknotes, passports, and Olympic medals"},
        {"name": "Reserve Bank of India Note Mudran - Mysuru", "lat": 12.2958, "lon": 76.6394,
         "country": "India", "founded": 1996,
         "notes": "BRBNMPL Mysuru press, supplements main Nashik printing facility"},
    ]


# ---------------------------------------------------------------------------
# Color and icon palettes per mode
# ---------------------------------------------------------------------------

MODE_COLORS = {
    "World Mints": "#06b6d4",
    "Ancient Coin Origins": "#d4a017",
    "Gold Rush Sites": "#f59e0b",
    "Currency Museums": "#8b5cf6",
    "Hyperinflation Sites": "#ef4444",
    "Silk Road Trade Currencies": "#e67e22",
    "Central Banks": "#3b82f6",
    "Pirate Treasure & Coin Hoards": "#10b981",
    "Cryptocurrency Hubs": "#f97316",
    "Banknote Printing Works": "#ec4899",
}

MODE_DESCRIPTIONS = {
    "World Mints": "Active government and private mints producing coins and bullion worldwide.",
    "Ancient Coin Origins": "Where the earliest coins were struck, from Lydian electrum to Roman denarii.",
    "Gold Rush Sites": "Historic gold discoveries that transformed regions and economies.",
    "Currency Museums": "Museums dedicated to numismatics, money history, and currency collections.",
    "Hyperinflation Sites": "Cities that experienced devastating currency collapses and hyperinflation.",
    "Silk Road Trade Currencies": "Key trade cities and caravanserai along the ancient Silk Road routes.",
    "Central Banks": "Headquarters of the world's major central banks and monetary authorities.",
    "Pirate Treasure & Coin Hoards": "Sunken ships, buried treasure, and major numismatic hoard discoveries.",
    "Cryptocurrency Hubs": "Global centers of crypto innovation, exchanges, mining, and adoption.",
    "Banknote Printing Works": "Security printing facilities that produce the world's paper currency.",
}

MODE_ICONS = {
    "World Mints": "Mint",
    "Ancient Coin Origins": "Origin",
    "Gold Rush Sites": "Site",
    "Currency Museums": "Museum",
    "Hyperinflation Sites": "Event",
    "Silk Road Trade Currencies": "City",
    "Central Banks": "Bank",
    "Pirate Treasure & Coin Hoards": "Treasure",
    "Cryptocurrency Hubs": "Hub",
    "Banknote Printing Works": "Printer",
}


# ---------------------------------------------------------------------------
# Data loader with caching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _load_mode_data(mode: str) -> list[dict]:
    """Return the curated dataset for the selected mode (cached 1 hour)."""
    dispatch = {
        "World Mints": _world_mints_data,
        "Ancient Coin Origins": _ancient_coin_origins_data,
        "Gold Rush Sites": _gold_rush_sites_data,
        "Currency Museums": _currency_museums_data,
        "Hyperinflation Sites": _hyperinflation_sites_data,
        "Silk Road Trade Currencies": _silk_road_currencies_data,
        "Central Banks": _central_banks_data,
        "Pirate Treasure & Coin Hoards": _pirate_treasure_data,
        "Cryptocurrency Hubs": _crypto_hubs_data,
        "Banknote Printing Works": _banknote_printing_data,
    }
    fn = dispatch.get(mode)
    if fn is None:
        return []
    return fn()


# ---------------------------------------------------------------------------
# Popup builder — all user content escaped via html_module.escape()
# ---------------------------------------------------------------------------

def _build_popup(row: dict, mode: str, color: str) -> str:
    """Build a styled HTML popup for a folium CircleMarker."""
    name = html_module.escape(str(row.get("name", "Unknown")))
    country = html_module.escape(str(row.get("country", "")))
    notes = html_module.escape(str(row.get("notes", "")))

    # Collect mode-specific extra fields
    extra_lines = []
    if "founded" in row and row["founded"]:
        extra_lines.append(
            f"<b>Founded:</b> {html_module.escape(str(row['founded']))}"
        )
    if "era" in row and row["era"]:
        extra_lines.append(
            f"<b>Era:</b> {html_module.escape(str(row['era']))}"
        )
    if "year" in row and row["year"]:
        extra_lines.append(
            f"<b>Year:</b> {html_module.escape(str(row['year']))}"
        )
    if "year_found" in row and row["year_found"] is not None:
        extra_lines.append(
            f"<b>Found:</b> {html_module.escape(str(row['year_found']))}"
        )
    if "peak_rate" in row and row["peak_rate"]:
        extra_lines.append(
            f"<b>Peak Rate:</b> {html_module.escape(str(row['peak_rate']))}"
        )
    if "currency" in row and row["currency"]:
        extra_lines.append(
            f"<b>Currency:</b> {html_module.escape(str(row['currency']))}"
        )
    if "type" in row and row["type"]:
        extra_lines.append(
            f"<b>Type:</b> {html_module.escape(str(row['type']))}"
        )

    extra_html = "<br>".join(extra_lines)
    if extra_html:
        extra_html = f"<br>{extra_html}"

    popup_html = (
        f'<div style="font-family:Segoe UI,Arial,sans-serif;min-width:220px;'
        f'max-width:310px;background:#1a2235;color:#e8ecf4;'
        f'padding:10px 14px;border-radius:8px;'
        f'border:1px solid {color}50;'
        f'box-shadow:0 2px 12px rgba(0,0,0,0.4);">'
        f'<div style="font-size:13px;font-weight:700;color:{color};'
        f'margin-bottom:5px;line-height:1.3;">{name}</div>'
        f'<div style="font-size:11px;color:#8b97b0;margin-bottom:4px;">'
        f'{country}</div>'
        f'{extra_html}'
        f'<div style="font-size:11px;margin-top:6px;color:#a0aec0;'
        f'line-height:1.45;">{notes}</div>'
        f'</div>'
    )
    return popup_html


# ---------------------------------------------------------------------------
# Folium dark map builder
# ---------------------------------------------------------------------------

def _build_map(df: pd.DataFrame, mode: str) -> folium.Map:
    """Build a CartoDB dark_matter folium map with styled CircleMarkers."""
    color = MODE_COLORS.get(mode, "#06b6d4")

    # Compute center from data points
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    # Adjust zoom based on geographic spread
    lat_spread = df["lat"].max() - df["lat"].min()
    lon_spread = df["lon"].max() - df["lon"].min()
    total_spread = lat_spread + lon_spread
    if total_spread > 200:
        zoom = 2
    elif total_spread > 100:
        zoom = 2
    elif total_spread > 50:
        zoom = 3
    elif total_spread > 20:
        zoom = 4
    else:
        zoom = 5

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Add each location as a CircleMarker
    for _, row in df.iterrows():
        popup_content = _build_popup(row.to_dict(), mode, color)
        tooltip_text = html_module.escape(str(row.get("name", "")))

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.70,
            weight=2,
            popup=folium.Popup(popup_content, max_width=330),
            tooltip=tooltip_text,
        ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Stats dashboard row
# ---------------------------------------------------------------------------

def _render_stats(df: pd.DataFrame, mode: str):
    """Render a row of st.metric widgets summarizing the current dataset."""
    col1, col2, col3, col4 = st.columns(4)

    # Metric 1: Location count
    with col1:
        st.metric("Locations", len(df))

    # Metric 2: Country count
    with col2:
        n_countries = df["country"].nunique() if "country" in df.columns else 0
        st.metric("Countries", n_countries)

    # Metric 3: Mode-specific insight
    with col3:
        if mode == "World Mints" and "founded" in df.columns:
            oldest = int(df["founded"].min())
            st.metric("Oldest Mint", f"{oldest} AD")
        elif mode == "Ancient Coin Origins" and "era" in df.columns:
            st.metric("Eras Covered", df["era"].nunique())
        elif mode == "Gold Rush Sites" and "year" in df.columns:
            earliest = int(df["year"].min())
            st.metric("Earliest Rush", str(earliest))
        elif mode == "Currency Museums":
            st.metric("Continents", df["country"].apply(
                lambda c: {"USA": "NA", "UK": "EU", "Germany": "EU",
                            "France": "EU", "Belgium": "EU",
                            "Switzerland": "EU", "Japan": "AS",
                            "Australia": "OC", "China": "AS",
                            "India": "AS", "Brazil": "SA"}.get(c, "Other")
            ).nunique())
        elif mode == "Hyperinflation Sites" and "year" in df.columns:
            span = int(df["year"].max()) - int(df["year"].min())
            st.metric("Year Span", f"{span} yrs")
        elif mode == "Silk Road Trade Currencies" and "era" in df.columns:
            st.metric("Trade Eras", df["era"].nunique())
        elif mode == "Central Banks" and "founded" in df.columns:
            oldest = int(df["founded"].min())
            st.metric("Oldest Bank", str(oldest))
        elif mode == "Pirate Treasure & Coin Hoards" and "year_found" in df.columns:
            found = df["year_found"].dropna()
            st.metric("Recovered", f"{len(found)}/{len(df)}")
        elif mode == "Cryptocurrency Hubs" and "type" in df.columns:
            st.metric("Hub Types", df["type"].nunique())
        elif mode == "Banknote Printing Works" and "founded" in df.columns:
            oldest = int(df["founded"].min())
            st.metric("Oldest Works", str(oldest))
        else:
            st.metric("Records", len(df))

    # Metric 4: Geographic spread
    with col4:
        lat_range = df["lat"].max() - df["lat"].min()
        st.metric("Lat Spread", f"{lat_range:.1f}\u00b0")


# ---------------------------------------------------------------------------
# Country filter helper
# ---------------------------------------------------------------------------

def _apply_country_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Optional country filter sidebar selectbox."""
    if "country" not in df.columns:
        return df
    countries = sorted(df["country"].unique().tolist())
    countries.insert(0, "All Countries")
    selected = st.selectbox(
        "Filter by Country",
        countries,
        key="coin_maps_country_filter",
    )
    if selected != "All Countries":
        df = df[df["country"] == selected].reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_coin_maps_tab():
    """Render the Coins & Currency Maps tab for TerraScout AI."""

    # ---- Tab header ----
    st.markdown(
        '<div class="tab-header amber">'
        '<h4>\U0001fa99 Coins & Currency Maps</h4>'
        '<p>Mints, currency history, and numismatic treasures worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    modes = [
        "World Mints",
        "Ancient Coin Origins",
        "Gold Rush Sites",
        "Currency Museums",
        "Hyperinflation Sites",
        "Silk Road Trade Currencies",
        "Central Banks",
        "Pirate Treasure & Coin Hoards",
        "Cryptocurrency Hubs",
        "Banknote Printing Works",
    ]
    selected_mode = st.selectbox("Map Mode", modes, key="coin_maps_mode")

    # Show mode description
    description = MODE_DESCRIPTIONS.get(selected_mode, "")
    if description:
        st.caption(description)

    # ---- Load data ----
    raw = _load_mode_data(selected_mode)
    if not raw:
        st.warning("No data available for this mode.")
        return

    df = pd.DataFrame(raw)

    # ---- Country filter ----
    df_filtered = _apply_country_filter(df)

    if df_filtered.empty:
        st.info("No locations match the selected filter.")
        return

    # ---- Stats dashboard ----
    st.markdown("---")
    _render_stats(df_filtered, selected_mode)
    st.markdown("---")

    # ---- Folium map ----
    with st.spinner(f"Building {selected_mode} map..."):
        m = _build_map(df_filtered, selected_mode)
        st_html(m._repr_html_(), height=500)

    # ---- Data table ----
    st.subheader(f"{selected_mode} Data ({len(df_filtered)} locations)")

    # Prepare display columns — keep lat/lon but put notes last
    col_order = [c for c in df_filtered.columns if c != "notes"]
    if "notes" in df_filtered.columns:
        col_order.append("notes")
    st.dataframe(df_filtered[col_order], use_container_width=True)

    # ---- CSV download ----
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    safe_name = selected_mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        label=f"Download {selected_mode} CSV",
        data=csv_bytes,
        file_name=f"coin_maps_{safe_name}.csv",
        mime="text/csv",
        key=f"coin_maps_dl_{safe_name}",
    )

    # ---- Location search / highlight ----
    st.markdown("---")
    search_term = st.text_input(
        "Search locations",
        placeholder="Type a name or keyword to highlight...",
        key="coin_maps_search",
    )
    if search_term and search_term.strip():
        term_lower = search_term.strip().lower()
        matches = df_filtered[
            df_filtered["name"].str.lower().str.contains(term_lower, na=False)
            | df_filtered["notes"].str.lower().str.contains(term_lower, na=False)
        ]
        if not matches.empty:
            st.success(
                f"Found {len(matches)} location(s) matching "
                f"'{html_module.escape(search_term.strip())}':"
            )
            for _, match_row in matches.iterrows():
                escaped_name = html_module.escape(str(match_row["name"]))
                escaped_notes = html_module.escape(str(match_row.get("notes", "")))
                color = MODE_COLORS.get(selected_mode, "#06b6d4")
                st.markdown(
                    f'<div style="border-left:3px solid {color};'
                    f'padding:6px 12px;margin-bottom:6px;'
                    f'background:#111827;border-radius:4px;">'
                    f'<span style="color:{color};font-weight:600;">'
                    f'{escaped_name}</span><br>'
                    f'<span style="color:#8b97b0;font-size:12px;">'
                    f'{escaped_notes}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info(f"No locations matching '{html_module.escape(search_term.strip())}'.")

    # ---- Mode-specific additional context ----
    with st.expander("About this dataset"):
        color = MODE_COLORS.get(selected_mode, "#06b6d4")

        # Build summary details per mode
        detail_lines = []
        if selected_mode == "World Mints":
            detail_lines = [
                "This dataset covers active government and private mints.",
                "Mints produce circulating coins, commemoratives, and bullion.",
                "The oldest listed mint, Monnaie de Paris, dates to 864 AD.",
                "Many mints also accept foreign contracts to strike other nations' coins.",
            ]
        elif selected_mode == "Ancient Coin Origins":
            detail_lines = [
                "The transition from barter to coinage began around 600 BC in Lydia.",
                "Greek city-states developed distinctive iconography for each polis.",
                "Roman coinage standardized trade across the Mediterranean.",
                "Chinese cash coins with square holes circulated for over 2,000 years.",
            ]
        elif selected_mode == "Gold Rush Sites":
            detail_lines = [
                "Gold rushes transformed economies and triggered mass migrations.",
                "The California Gold Rush of 1848-1855 brought 300,000 settlers.",
                "Australian gold rushes of the 1850s doubled the continent's population.",
                "South Africa's Witwatersrand produced 40% of all gold ever mined.",
            ]
        elif selected_mode == "Currency Museums":
            detail_lines = [
                "Currency museums preserve the material history of money.",
                "Collections range from ancient electrum coins to modern polymer notes.",
                "Many central banks maintain public museums at their headquarters.",
                "The Smithsonian holds over 1.6 million numismatic objects.",
            ]
        elif selected_mode == "Hyperinflation Sites":
            detail_lines = [
                "Hyperinflation is defined as prices rising over 50% per month.",
                "Hungary 1946 holds the record: prices doubled every 15 hours.",
                "Zimbabwe printed 100 trillion dollar banknotes before abandoning its currency.",
                "Most hyperinflations were triggered by war, political instability, or debt.",
            ]
        elif selected_mode == "Silk Road Trade Currencies":
            detail_lines = [
                "The Silk Road network spanned 6,400 km from China to the Mediterranean.",
                "Coins served as both currency and diplomatic gifts along trade routes.",
                "Byzantine gold solidus was the most trusted coin for 700 years.",
                "Sogdian merchants were the primary intermediaries of Silk Road trade.",
            ]
        elif selected_mode == "Central Banks":
            detail_lines = [
                "Central banks manage national monetary policy and currency issuance.",
                "Sveriges Riksbank (1668) is the world's oldest central bank.",
                "The Federal Reserve was created after the Panic of 1907.",
                "Norway's Government Pension Fund Global exceeds $1.4 trillion.",
            ]
        elif selected_mode == "Pirate Treasure & Coin Hoards":
            detail_lines = [
                "Coin hoards provide invaluable snapshots of historical economies.",
                "The San Jose galleon is considered the most valuable wreck ever found.",
                "Viking hoards often contain coins from multiple distant civilizations.",
                "Metal detectorists have discovered many of Britain's greatest hoards.",
            ]
        elif selected_mode == "Cryptocurrency Hubs":
            detail_lines = [
                "Bitcoin was launched in 2009 by the pseudonymous Satoshi Nakamoto.",
                "Ethereum was proposed in 2013 by Vitalik Buterin in Toronto.",
                "El Salvador became the first country with Bitcoin legal tender in 2021.",
                "Crypto mining gravitates toward cheap electricity from hydro and geothermal.",
            ]
        elif selected_mode == "Banknote Printing Works":
            detail_lines = [
                "Modern banknotes incorporate holograms, microprinting, and UV features.",
                "Australia invented polymer (plastic) banknotes in 1988.",
                "De La Rue prints currency for approximately 140 countries.",
                "The Bureau of Engraving and Printing produces 7 billion notes per year.",
            ]

        details_html = "<br>".join(
            html_module.escape(line) for line in detail_lines
        )

        st.markdown(
            f'<div style="border-left:3px solid {color};padding-left:12px;'
            f'color:#8b97b0;font-size:13px;line-height:1.6;">'
            f'<b style="color:{color};">{html_module.escape(selected_mode)}</b><br>'
            f'{html_module.escape(description)}<br><br>'
            f'{details_html}<br><br>'
            f'<b>Total Locations:</b> {len(df)} curated entries<br>'
            f'<b>Countries Covered:</b> '
            f'{df["country"].nunique() if "country" in df.columns else "N/A"}<br>'
            f'<b>Source:</b> Curated numismatic and geographic references<br>'
            f'<b>Data:</b> Hardcoded — no external API calls required'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    render_coin_maps_tab()
