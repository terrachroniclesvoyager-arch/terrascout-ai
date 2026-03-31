# -*- coding: utf-8 -*-
"""
Fortresses & Castles Maps module for TerraScout AI.
Provides 10 interactive map modes covering medieval castles, crusader fortresses,
star forts, great walls, Japanese castles, Moorish fortifications, Viking forts,
ancient citadels, prison fortresses, and underground fortifications.
All data is hardcoded -- no API keys required.
"""

import io
import html as html_module
import streamlit as st
import pandas as pd
import requests
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

# ═══════════════════════════════════════════════════════════════════════
# COLOUR PALETTE (dark theme)
# ═══════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_ACCENT = "#06b6d4"
_MUTED = "#5a6580"

# ═══════════════════════════════════════════════════════════════════════
# MAP MODE LIST
# ═══════════════════════════════════════════════════════════════════════
MAP_MODES = [
    "Greatest Medieval Castles",
    "Crusader Fortresses",
    "Star Forts & Bastions",
    "Great Walls & Barriers",
    "Japanese Castles",
    "Moorish & Islamic Fortresses",
    "Viking & Norse Fortifications",
    "Ancient Citadels",
    "Prison Fortresses",
    "Underground & Hidden Fortifications",
]

# ═══════════════════════════════════════════════════════════════════════
# 1. GREATEST MEDIEVAL CASTLES (28 entries)
# ═══════════════════════════════════════════════════════════════════════
MEDIEVAL_CASTLES = [
    {"name": "Neuschwanstein Castle", "lat": 47.5576, "lon": 10.7498, "country": "Germany", "built": "1869-1886", "style": "Romanesque Revival", "notes": "Fairy-tale castle built by Ludwig II of Bavaria; inspired Disney's Sleeping Beauty Castle"},
    {"name": "Edinburgh Castle", "lat": 55.9486, "lon": -3.1999, "country": "Scotland", "built": "12th century", "style": "Medieval fortress", "notes": "Perched on Castle Rock; royal residence since 12th century; hosts the Royal Edinburgh Military Tattoo"},
    {"name": "Windsor Castle", "lat": 51.4839, "lon": -0.6044, "country": "England", "built": "1070", "style": "Medieval/Gothic", "notes": "Oldest and largest occupied castle in the world; primary residence of British monarchs"},
    {"name": "Alhambra", "lat": 37.1760, "lon": -3.5881, "country": "Spain", "built": "1238-1358", "style": "Moorish/Nasrid", "notes": "Palatial fortress complex in Granada; pinnacle of Moorish architecture in Europe"},
    {"name": "Chateau de Chambord", "lat": 47.6161, "lon": 1.5170, "country": "France", "built": "1519-1547", "style": "French Renaissance", "notes": "Largest chateau in the Loire Valley; 440 rooms; double-helix staircase attributed to Da Vinci"},
    {"name": "Himeji Castle", "lat": 34.8394, "lon": 134.6939, "country": "Japan", "built": "1333-1609", "style": "Japanese feudal", "notes": "White Heron Castle; finest surviving example of Japanese castle architecture; UNESCO site"},
    {"name": "Krak des Chevaliers", "lat": 34.7569, "lon": 36.2940, "country": "Syria", "built": "1142-1271", "style": "Crusader fortress", "notes": "Greatest Crusader castle; described by T.E. Lawrence as 'the finest castle in the world'"},
    {"name": "Warwick Castle", "lat": 52.2794, "lon": -1.5846, "country": "England", "built": "1068", "style": "Medieval fortress", "notes": "Built by William the Conqueror; one of the best-preserved medieval castles in England"},
    {"name": "Conwy Castle", "lat": 53.2804, "lon": -3.8258, "country": "Wales", "built": "1283-1289", "style": "Edwardian concentric", "notes": "Built by Edward I during conquest of Wales; 8 massive towers; UNESCO World Heritage"},
    {"name": "Chateau de Chenonceau", "lat": 47.3249, "lon": 1.0704, "country": "France", "built": "1514-1522", "style": "French Renaissance", "notes": "Spans the River Cher; 'Ladies Castle' managed by notable women including Catherine de Medici"},
    {"name": "Malbork Castle", "lat": 54.0397, "lon": 19.0284, "country": "Poland", "built": "1274-1457", "style": "Gothic brick", "notes": "Largest castle in the world by area; Teutonic Knights headquarters; UNESCO site"},
    {"name": "Bran Castle", "lat": 45.5150, "lon": 25.3672, "country": "Romania", "built": "1377-1388", "style": "Medieval Gothic", "notes": "Associated with Dracula legend; strategic mountain pass fortress between Transylvania and Wallachia"},
    {"name": "Alcazar of Segovia", "lat": 40.9481, "lon": -4.1199, "country": "Spain", "built": "12th century", "style": "Romanesque/Gothic", "notes": "Ship-shaped fortress on rocky promontory; inspired Disney's Cinderella Castle"},
    {"name": "Prague Castle", "lat": 50.0910, "lon": 14.4013, "country": "Czech Republic", "built": "870 AD", "style": "Romanesque to Gothic", "notes": "Largest coherent castle complex in the world; seat of Czech rulers for over 1,000 years"},
    {"name": "Bodiam Castle", "lat": 51.0032, "lon": 0.5437, "country": "England", "built": "1385", "style": "Quadrangular moated", "notes": "Iconic moated castle in East Sussex; built during Hundred Years War"},
    {"name": "Eilean Donan Castle", "lat": 57.2740, "lon": -5.5160, "country": "Scotland", "built": "13th century", "style": "Medieval Highland", "notes": "On island at confluence of three lochs; one of most photographed castles in Scotland"},
    {"name": "Mont-Saint-Michel", "lat": 48.6361, "lon": -1.5115, "country": "France", "built": "966-1523", "style": "Gothic abbey-fortress", "notes": "Tidal island monastery-fortress in Normandy; UNESCO site; connected by causeway"},
    {"name": "Carcassonne", "lat": 43.2065, "lon": 2.3631, "country": "France", "built": "3rd-13th century", "style": "Concentric medieval", "notes": "Largest walled city in Europe; double ring of walls with 52 towers; UNESCO site"},
    {"name": "Tower of London", "lat": 51.5081, "lon": -0.0759, "country": "England", "built": "1066", "style": "Norman/Medieval", "notes": "Royal palace, prison, and fortress; houses Crown Jewels; home of the famous ravens"},
    {"name": "Hohenzollern Castle", "lat": 48.3233, "lon": 8.9672, "country": "Germany", "built": "1454 (rebuilt 1846-1867)", "style": "Gothic Revival", "notes": "Ancestral seat of the Hohenzollern dynasty; perched atop Mount Hohenzollern at 855m"},
    {"name": "Castillo de Coca", "lat": 41.2167, "lon": -4.5167, "country": "Spain", "built": "1453", "style": "Mudejar Gothic", "notes": "Unique blend of Moorish and Gothic architecture; built of brick rather than stone"},
    {"name": "Chateau de Versailles", "lat": 48.8049, "lon": 2.1204, "country": "France", "built": "1623-1715", "style": "Baroque/Classical", "notes": "Former royal palace; Hall of Mirrors; Treaty of Versailles signed here in 1919"},
    {"name": "Kronborg Castle", "lat": 56.0390, "lon": 12.6215, "country": "Denmark", "built": "1420s-1585", "style": "Renaissance fortress", "notes": "Setting of Shakespeare's Hamlet; guards entrance to the Oresund strait; UNESCO site"},
    {"name": "Chateau de Carcassonne", "lat": 43.2120, "lon": 2.3639, "country": "France", "built": "12th century", "style": "Comtal castle", "notes": "Inner castle within the walled city; Trencavel viscounts residence"},
    {"name": "Pena Palace", "lat": 38.7876, "lon": -9.3907, "country": "Portugal", "built": "1842-1854", "style": "Romanticist eclectic", "notes": "Colorful hilltop palace in Sintra; mix of Gothic, Manueline, and Moorish styles; UNESCO"},
    {"name": "Corfe Castle", "lat": 50.6397, "lon": -2.0572, "country": "England", "built": "1066-1086", "style": "Norman fortification", "notes": "Dramatic ruins on Purbeck Hills; demolished by Parliamentarians in English Civil War"},
    {"name": "Chateau de Vincennes", "lat": 48.8425, "lon": 2.4353, "country": "France", "built": "1337-1410", "style": "Medieval fortress", "notes": "Tallest medieval fortified tower in Europe at 52m; royal residence and prison"},
    {"name": "Predjama Castle", "lat": 45.8144, "lon": 14.1269, "country": "Slovenia", "built": "1274", "style": "Renaissance/Gothic", "notes": "Built into the mouth of a cave halfway up a 123m cliff; secret tunnel network"},
    {"name": "Chateau de Chillon", "lat": 46.4142, "lon": 6.9275, "country": "Switzerland", "built": "12th century", "style": "Medieval lakeside", "notes": "Island castle on Lake Geneva; inspired Byron's 'Prisoner of Chillon'; 1,000 years old"},
    {"name": "Caernarfon Castle", "lat": 53.1392, "lon": -4.2769, "country": "Wales", "built": "1283-1330", "style": "Edwardian concentric", "notes": "Edward I's mightiest Welsh castle; polygonal towers; Prince of Wales investiture site; UNESCO"},
    {"name": "Dunnottar Castle", "lat": 56.9458, "lon": -2.1972, "country": "Scotland", "built": "15th century", "style": "Medieval cliff fortress", "notes": "Dramatic cliff-top ruin; Scottish Crown Jewels hidden here; Mel Gibson's Hamlet location"},
    {"name": "Burg Eltz", "lat": 50.2053, "lon": 7.3367, "country": "Germany", "built": "1157", "style": "Romanesque/Gothic", "notes": "Medieval castle owned by same family for 850 years; nestled in forested hills above Mosel"},
    {"name": "Matsue Castle", "lat": 35.4750, "lon": 133.0506, "country": "Japan", "built": "1611", "style": "Japanese feudal", "notes": "Black Castle; one of 12 original-keep castles in Japan; national treasure designation"},
    {"name": "Castelo de Guimaraes", "lat": 41.4478, "lon": -8.2903, "country": "Portugal", "built": "10th century", "style": "Romanesque", "notes": "Birthplace of Portugal; Afonso Henriques crowned first king here; national symbol"},
    {"name": "Castillo de Loarre", "lat": 42.3286, "lon": -0.6111, "country": "Spain", "built": "1020-1035", "style": "Romanesque fortress", "notes": "Best-preserved Romanesque fortress in Europe; hilltop in Aragon; Kingdom of Heaven filming"},
]

# ═══════════════════════════════════════════════════════════════════════
# 2. CRUSADER FORTRESSES (22 entries)
# ═══════════════════════════════════════════════════════════════════════
CRUSADER_FORTRESSES = [
    {"name": "Krak des Chevaliers", "lat": 34.7569, "lon": 36.2940, "country": "Syria", "order": "Knights Hospitaller", "built": "1142-1271", "notes": "Greatest surviving Crusader castle; concentric design; withstood 12 sieges"},
    {"name": "Montfort Castle", "lat": 33.0328, "lon": 35.2322, "country": "Israel", "order": "Teutonic Knights", "built": "1227-1271", "notes": "Teutonic headquarters in the Holy Land; ruined hilltop fortress in Upper Galilee"},
    {"name": "Kerak Castle", "lat": 31.1811, "lon": 35.7017, "country": "Jordan", "order": "Kingdom of Jerusalem", "built": "1142", "notes": "Massive Crusader castle; Reynald de Chatillon's stronghold; besieged by Saladin"},
    {"name": "Acre Fortress", "lat": 32.9215, "lon": 35.0677, "country": "Israel", "order": "Knights Hospitaller", "built": "1104-1291", "notes": "Last Crusader capital; Hospitaller complex rediscovered underground; UNESCO site"},
    {"name": "Palace of the Grand Master, Rhodes", "lat": 36.4453, "lon": 28.2262, "country": "Greece", "order": "Knights Hospitaller", "built": "14th century", "notes": "Hospitaller headquarters after loss of Holy Land; medieval walled city; UNESCO site"},
    {"name": "Margat Castle", "lat": 34.8544, "lon": 35.9489, "country": "Syria", "order": "Knights Hospitaller", "built": "1062-1186", "notes": "Massive black basalt fortress; Hospitaller base controlling coastal route to Tripoli"},
    {"name": "Belvoir Fortress", "lat": 32.5833, "lon": 35.5167, "country": "Israel", "order": "Knights Hospitaller", "built": "1168-1189", "notes": "Concentric castle overlooking Jordan Valley; withstood Saladin's siege for 18 months"},
    {"name": "Sidon Sea Castle", "lat": 33.5633, "lon": 35.3700, "country": "Lebanon", "order": "Crusader Kingdom", "built": "1228", "notes": "Fortress built on small island connected by causeway; constructed by Louis IX"},
    {"name": "Beaufort Castle", "lat": 33.3606, "lon": 35.5417, "country": "Lebanon", "order": "Kingdom of Jerusalem", "built": "1139", "notes": "Strategic hilltop castle; changed hands between Crusaders, Muslims, and Mamluks"},
    {"name": "Chastel Blanc", "lat": 34.7333, "lon": 36.1500, "country": "Syria", "order": "Knights Templar", "built": "12th century", "notes": "Templar fortress; well-preserved tower keep still standing in Safita"},
    {"name": "Tartus Cathedral Fortress", "lat": 34.8894, "lon": 35.8867, "country": "Syria", "order": "Knights Templar", "built": "12th century", "notes": "Templar stronghold and cathedral; last Crusader foothold on mainland (1302)"},
    {"name": "Kolossi Castle", "lat": 34.6650, "lon": 32.9339, "country": "Cyprus", "order": "Knights Hospitaller", "built": "1210", "notes": "Sugar production centre; commandery estate; well-preserved three-story keep"},
    {"name": "Kyrenia Castle", "lat": 35.3419, "lon": 33.3214, "country": "Cyprus", "order": "Lusignan Kingdom", "built": "7th century (expanded)", "notes": "Harbour castle rebuilt by Lusignans; shipwreck museum; panoramic views"},
    {"name": "Shobak Castle", "lat": 30.5328, "lon": 35.5611, "country": "Jordan", "order": "Kingdom of Jerusalem", "built": "1115", "notes": "Baldwin I's first Crusader castle east of the Jordan; Montreal fortress"},
    {"name": "Ajloun Castle", "lat": 32.3333, "lon": 35.7528, "country": "Jordan", "order": "Ayyubid (anti-Crusader)", "built": "1184-1185", "notes": "Muslim fortress built by Saladin's nephew to counter Crusader Belvoir Castle"},
    {"name": "Nimrod Fortress", "lat": 33.2511, "lon": 35.7644, "country": "Israel", "order": "Ayyubid/Mamluk", "built": "1228", "notes": "Largest Ayyubid castle; built on Golan Heights ridge to defend against Crusaders"},
    {"name": "Castle of St. Peter (Bodrum)", "lat": 37.0312, "lon": 27.4300, "country": "Turkey", "order": "Knights Hospitaller", "built": "1402-1522", "notes": "Hospitaller castle built using stones from Mausoleum of Halicarnassus"},
    {"name": "Gibelet Castle", "lat": 34.1214, "lon": 35.6486, "country": "Lebanon", "order": "Crusader Lordship", "built": "12th century", "notes": "Embriaco family stronghold in ancient Byblos; Romanesque chapel still intact"},
    {"name": "Tripoli Citadel", "lat": 34.4372, "lon": 35.8456, "country": "Lebanon", "order": "County of Tripoli", "built": "1103", "notes": "Raymond de Saint-Gilles citadel; rebuilt by Mamluks; overlooking old city"},
    {"name": "Atlit (Chateau Pelerin)", "lat": 32.6944, "lon": 34.9333, "country": "Israel", "order": "Knights Templar", "built": "1218", "notes": "Sea fortress never taken by force; last Templar mainland stronghold (1291)"},
    {"name": "Saone Castle (Saladin Castle)", "lat": 35.6078, "lon": 36.0931, "country": "Syria", "order": "Crusader Principality", "built": "12th century", "notes": "Dramatic cliff-top castle; 28m-tall needle rock separates castle from ridge"},
    {"name": "Hospitaller Fortress Tiberias", "lat": 32.7944, "lon": 35.5350, "country": "Israel", "order": "Knights Hospitaller", "built": "12th century", "notes": "Strategic castle on Sea of Galilee; Battle of Hattin 1187 fought nearby"},
    {"name": "Qal'at Salah Ed-Din", "lat": 35.6078, "lon": 36.0931, "country": "Syria", "order": "Crusader Principality", "built": "10th-12th century", "notes": "Saladin's Castle; UNESCO site; dramatic 28m needle rock separates castle from ridge"},
    {"name": "Kantara Castle", "lat": 35.4000, "lon": 33.9167, "country": "Cyprus", "order": "Lusignan Kingdom", "built": "10th century", "notes": "Mountain-top castle in Kyrenia range; 630m altitude; guarded passage across mountains"},
    {"name": "St. Hilarion Castle", "lat": 35.3119, "lon": 33.2811, "country": "Cyprus", "order": "Lusignan Kingdom", "built": "10th century", "notes": "Fairy-tale mountain castle; three tiers; inspired Disney castle designs; Kyrenia mountains"},
    {"name": "Buffavento Castle", "lat": 35.2833, "lon": 33.4333, "country": "Cyprus", "order": "Lusignan Kingdom", "built": "11th century", "notes": "Defier of Winds; highest of three Kyrenia range castles at 954m; watchtower fortress"},
]

# ═══════════════════════════════════════════════════════════════════════
# 3. STAR FORTS & BASTIONS (22 entries)
# ═══════════════════════════════════════════════════════════════════════
STAR_FORTS = [
    {"name": "Palmanova", "lat": 45.9053, "lon": 13.3104, "country": "Italy", "built": "1593", "points": 9, "notes": "Perfect nine-pointed star city; built by Venice; UNESCO World Heritage Site"},
    {"name": "Fort Bourtange", "lat": 53.0064, "lon": 7.1914, "country": "Netherlands", "built": "1593", "points": 5, "notes": "Star-shaped fortress village in Groningen; restored to 1742 appearance"},
    {"name": "Fort McHenry", "lat": 39.2633, "lon": -76.5797, "country": "USA", "built": "1798-1803", "points": 5, "notes": "Defence of Baltimore 1814 inspired Star-Spangled Banner; national monument"},
    {"name": "Citadelle de Lille", "lat": 50.6400, "lon": 3.0456, "country": "France", "built": "1667-1670", "points": 5, "notes": "Vauban's masterpiece; 'Queen of Citadels'; still active military base"},
    {"name": "Fort George", "lat": 57.5817, "lon": -4.0647, "country": "Scotland", "built": "1769", "points": 6, "notes": "One of the most outstanding fortifications in Europe; still an active army barracks"},
    {"name": "Goryokaku", "lat": 41.7965, "lon": 140.7571, "country": "Japan", "built": "1855-1866", "points": 5, "notes": "Western-style star fort in Hakodate; last battle of Boshin War; cherry blossom park"},
    {"name": "Fortezza Nuova", "lat": 43.5525, "lon": 10.3103, "country": "Italy", "built": "1590", "points": 5, "notes": "Medici pentagonal fortress in Livorno; now a public park surrounded by canals"},
    {"name": "Fort Pulaski", "lat": 32.0283, "lon": -80.8906, "country": "USA", "built": "1829-1847", "points": 5, "notes": "Brick masonry fortress near Savannah; rifled cannon test 1862 made forts obsolete"},
    {"name": "Citadel of Jaca", "lat": 42.5714, "lon": -0.5514, "country": "Spain", "built": "1592-1670", "points": 5, "notes": "Best-preserved pentagonal citadel in Europe; Spanish military fortress in Aragon"},
    {"name": "Neuf-Brisach", "lat": 48.0175, "lon": 7.5278, "country": "France", "built": "1698-1707", "points": 8, "notes": "Vauban's final masterpiece; octagonal fortified town; UNESCO World Heritage Site"},
    {"name": "Naarden Fortress", "lat": 52.2958, "lon": 5.1625, "country": "Netherlands", "built": "1685", "points": 6, "notes": "Best-preserved star fort in Europe; double moat system; now museum"},
    {"name": "Hamina Fortress", "lat": 60.5703, "lon": 27.1978, "country": "Finland", "built": "1722", "points": 8, "notes": "Unique circular star fort town plan; Swedish then Russian military base"},
    {"name": "Forte de Graca", "lat": 38.8778, "lon": -7.1611, "country": "Portugal", "built": "1763-1792", "points": 4, "notes": "Star fort overlooking Elvas; finest example of 18th-century military architecture"},
    {"name": "Citadel of Alessandria", "lat": 44.9000, "lon": 8.6000, "country": "Italy", "built": "1728-1745", "points": 6, "notes": "One of the largest 18th-century European fortifications; hexagonal plan"},
    {"name": "Fort Jefferson", "lat": 24.6285, "lon": -82.8732, "country": "USA", "built": "1846-1875", "points": 6, "notes": "Massive hexagonal fortress in Dry Tortugas; never completed; 16 million bricks"},
    {"name": "Kastellet", "lat": 55.6917, "lon": 12.5939, "country": "Denmark", "built": "1626-1664", "points": 5, "notes": "Copenhagen's star citadel; one of best-preserved star forts in Northern Europe"},
    {"name": "Fort Ticonderoga", "lat": 43.8425, "lon": -73.3879, "country": "USA", "built": "1755-1757", "points": 4, "notes": "French-built Fort Carillon; captured by Ethan Allen 1775; key Revolutionary site"},
    {"name": "Citadel of Pamplona", "lat": 42.8125, "lon": -1.6456, "country": "Spain", "built": "1571", "points": 5, "notes": "Renaissance star fortress; now a public park and cultural centre in Navarre"},
    {"name": "Fort William (Kolkata)", "lat": 22.5570, "lon": 88.3422, "country": "India", "built": "1696-1781", "points": 5, "notes": "British East India Company headquarters; irregular star plan; Black Hole incident 1756"},
    {"name": "Forte de Sao Joao Baptista", "lat": 38.5294, "lon": -28.6306, "country": "Portugal (Azores)", "built": "16th century", "points": 4, "notes": "Star fortress guarding Angra do Heroismo harbour; UNESCO World Heritage city"},
    {"name": "Forte da Graca", "lat": 38.8797, "lon": -7.1608, "country": "Portugal", "built": "1763", "points": 4, "notes": "Overlooking Elvas; part of the garrison border town UNESCO site"},
    {"name": "Fredericia Fortress", "lat": 55.5667, "lon": 9.7500, "country": "Denmark", "built": "1650", "points": 6, "notes": "Star-shaped ramparts protecting Jutland; site of decisive 1849 battle"},
    {"name": "Fort Monroe", "lat": 37.0036, "lon": -76.3081, "country": "USA", "built": "1819-1834", "points": 7, "notes": "Largest stone fort in USA; held Jefferson Davis after Civil War; moat-surrounded"},
    {"name": "Citadelle Laferriere", "lat": 19.5728, "lon": -72.2128, "country": "Haiti", "built": "1805-1820", "points": 4, "notes": "Largest fortress in the Americas; built by Henri Christophe; UNESCO World Heritage Site"},
    {"name": "Fort Manoel", "lat": 35.9000, "lon": 14.5025, "country": "Malta", "built": "1723-1733", "points": 4, "notes": "Star fort on Manoel Island; Knights of Malta construction; Game of Thrones filming"},
]

# ═══════════════════════════════════════════════════════════════════════
# 4. GREAT WALLS & BARRIERS (22 entries)
# ═══════════════════════════════════════════════════════════════════════
GREAT_WALLS = [
    {"name": "Great Wall of China (Badaling)", "lat": 40.3593, "lon": 116.0198, "country": "China", "length_km": 21196, "built": "7th century BC - 1644 AD", "notes": "World's longest wall; spans 21,196 km including branches; UNESCO World Heritage Site"},
    {"name": "Hadrian's Wall", "lat": 55.0261, "lon": -2.3755, "country": "England", "length_km": 117, "built": "122-128 AD", "notes": "Roman frontier across northern England; 117 km with forts, milecastles; UNESCO site"},
    {"name": "Antonine Wall", "lat": 55.9647, "lon": -3.9375, "country": "Scotland", "length_km": 63, "built": "142-154 AD", "notes": "Roman turf wall north of Hadrian's Wall; UNESCO World Heritage Site; shorter-lived frontier"},
    {"name": "Berlin Wall Memorial", "lat": 52.5353, "lon": 13.3903, "country": "Germany", "length_km": 155, "built": "1961-1989", "notes": "Cold War barrier dividing East and West Berlin; 155 km total; fell November 9, 1989"},
    {"name": "Maginot Line (Schoenenbourg)", "lat": 48.9486, "lon": 7.9064, "country": "France", "length_km": 450, "built": "1929-1938", "notes": "French fortification line along German border; underground forts; bypassed in 1940"},
    {"name": "Walls of Constantinople", "lat": 41.0089, "lon": 28.9222, "country": "Turkey", "length_km": 22, "built": "413-447 AD", "notes": "Triple-layered Theodosian walls; protected Constantinople for 1,000 years"},
    {"name": "Western Wall (Jerusalem)", "lat": 31.7767, "lon": 35.2345, "country": "Israel", "length_km": 0.488, "built": "19 BC", "notes": "Retaining wall of Temple Mount by Herod the Great; holiest Jewish prayer site"},
    {"name": "Walls of Dubrovnik", "lat": 42.6407, "lon": 18.1082, "country": "Croatia", "length_km": 2, "built": "13th-17th century", "notes": "Complete circuit of medieval walls; up to 25m high; UNESCO World Heritage old town"},
    {"name": "Danevirke", "lat": 54.4833, "lon": 9.5000, "country": "Germany", "length_km": 30, "built": "5th-12th century", "notes": "Danish border earthwork in Schleswig-Holstein; defence against Franks and Saxons"},
    {"name": "Great Wall of Gorgan", "lat": 37.1167, "lon": 54.4833, "country": "Iran", "length_km": 195, "built": "5th-6th century AD", "notes": "Red Snake; second-longest defensive wall after Great Wall of China; Sasanian Empire"},
    {"name": "Walls of Ston", "lat": 42.8378, "lon": 17.6917, "country": "Croatia", "length_km": 5.5, "built": "1358-1506", "notes": "Second-longest fortification wall in Europe; protected Peljesac salt pans for Dubrovnik"},
    {"name": "Offa's Dyke", "lat": 52.0667, "lon": -3.0667, "country": "Wales/England", "length_km": 240, "built": "757-796 AD", "notes": "Anglo-Saxon earthwork marking Welsh-English border; 240 km national trail"},
    {"name": "Atlantic Wall (Pointe du Hoc)", "lat": 48.6340, "lon": -0.9867, "country": "France", "length_km": 5000, "built": "1942-1944", "notes": "Nazi coastal defence system from Norway to Spain; 5,000 km; breached on D-Day"},
    {"name": "Bar Lev Line", "lat": 30.3500, "lon": 32.3500, "country": "Egypt/Israel", "length_km": 160, "built": "1969-1973", "notes": "Israeli fortification along Suez Canal; overrun in 1973 Yom Kippur War"},
    {"name": "Mannerheim Line", "lat": 60.7833, "lon": 29.6000, "country": "Finland", "length_km": 135, "built": "1920-1939", "notes": "Finnish defensive line on Karelian Isthmus; held against Soviets in Winter War 1939-40"},
    {"name": "Siegfried Line (Westwall)", "lat": 50.1000, "lon": 6.3000, "country": "Germany", "length_km": 630, "built": "1936-1940", "notes": "German defensive line along western border; 18,000 bunkers, tunnels, tank traps"},
    {"name": "Great Zimbabwe Walls", "lat": -20.2711, "lon": 30.9336, "country": "Zimbabwe", "length_km": 0.3, "built": "11th-15th century", "notes": "Massive dry-stone walls up to 11m high; Great Enclosure; capital of Kingdom of Zimbabwe"},
    {"name": "Sacsayhuaman", "lat": -13.5094, "lon": -71.9822, "country": "Peru", "length_km": 0.6, "built": "1438-1508", "notes": "Inca fortress with megalithic zigzag walls; stones weighing up to 200 tonnes"},
    {"name": "Aurelian Walls", "lat": 41.8756, "lon": 12.5211, "country": "Italy", "length_km": 19, "built": "271-275 AD", "notes": "Roman city walls encircling Rome; 19 km with 383 towers; largely intact today"},
    {"name": "Korean DMZ", "lat": 37.9575, "lon": 126.6778, "country": "Korea", "length_km": 250, "built": "1953", "notes": "Demilitarized zone; 250 km long, 4 km wide; world's most heavily fortified border"},
    {"name": "Israel-West Bank Barrier", "lat": 31.7500, "lon": 35.1833, "country": "Israel/Palestine", "length_km": 708, "built": "2002-present", "notes": "Separation barrier; mix of concrete walls and fences; highly controversial"},
    {"name": "US-Mexico Border Wall", "lat": 31.9600, "lon": -106.4400, "country": "USA/Mexico", "length_km": 1050, "built": "1990s-present", "notes": "Border barrier sections along 3,145 km border; politically contentious"},
    {"name": "Servian Wall Remains", "lat": 41.9006, "lon": 12.5022, "country": "Italy", "length_km": 11, "built": "4th century BC", "notes": "Early Roman defensive wall; segments visible near Termini station; preceded Aurelian Walls"},
    {"name": "Wall of Philip II (Paris)", "lat": 48.8566, "lon": 2.3522, "country": "France", "length_km": 5, "built": "1190-1215", "notes": "Medieval Paris city wall; traces visible in Louvre basement; protected Right Bank"},
    {"name": "Long Walls of Athens", "lat": 37.9500, "lon": 23.7000, "country": "Greece", "length_km": 6.5, "built": "461-445 BC", "notes": "Connected Athens to Piraeus port; ensured naval supply; destroyed by Sparta 404 BC"},
]

# ═══════════════════════════════════════════════════════════════════════
# 5. JAPANESE CASTLES (24 entries)
# ═══════════════════════════════════════════════════════════════════════
JAPANESE_CASTLES = [
    {"name": "Himeji Castle", "lat": 34.8394, "lon": 134.6939, "prefecture": "Hyogo", "built": "1333 (rebuilt 1609)", "type": "Hilltop", "notes": "White Heron Castle; Japan's finest castle; UNESCO World Heritage; national treasure"},
    {"name": "Osaka Castle", "lat": 34.6873, "lon": 135.5262, "prefecture": "Osaka", "built": "1583", "type": "Hilltop", "notes": "Toyotomi Hideyoshi's masterpiece; rebuilt in 1931; iconic symbol of Osaka"},
    {"name": "Matsumoto Castle", "lat": 36.2388, "lon": 137.9688, "prefecture": "Nagano", "built": "1504 (tower 1593-1594)", "type": "Flatland", "notes": "Crow Castle; oldest five-story donjon; national treasure; black exterior"},
    {"name": "Kumamoto Castle", "lat": 32.8061, "lon": 130.7060, "prefecture": "Kumamoto", "built": "1467 (rebuilt 1601)", "type": "Hilltop", "notes": "One of Japan's three premier castles; severe damage in 2016 earthquake; undergoing restoration"},
    {"name": "Nagoya Castle", "lat": 35.1855, "lon": 136.8993, "prefecture": "Aichi", "built": "1612", "type": "Flatland", "notes": "Golden shachihoko dolphins; Tokugawa stronghold; original destroyed in WWII, reconstructed"},
    {"name": "Nijo Castle", "lat": 35.0142, "lon": 135.7481, "prefecture": "Kyoto", "built": "1603", "type": "Flatland", "notes": "Tokugawa shogunate Kyoto residence; nightingale floors; UNESCO World Heritage Site"},
    {"name": "Hikone Castle", "lat": 35.2758, "lon": 136.2511, "prefecture": "Shiga", "built": "1622", "type": "Hilltop", "notes": "Original donjon; national treasure; one of only five national-treasure castles"},
    {"name": "Matsue Castle", "lat": 35.4750, "lon": 133.0506, "prefecture": "Shimane", "built": "1611", "type": "Hilltop", "notes": "Black Castle; one of 12 original-keep castles; national treasure since 2015"},
    {"name": "Inuyama Castle", "lat": 35.3861, "lon": 136.9394, "prefecture": "Aichi", "built": "1537", "type": "Hilltop", "notes": "Oldest surviving donjon in Japan; national treasure; overlooks Kiso River"},
    {"name": "Kanazawa Castle", "lat": 36.5628, "lon": 136.6594, "prefecture": "Ishikawa", "built": "1583", "type": "Hilltop", "notes": "Maeda clan stronghold; adjacent to famous Kenroku-en garden; stone walls showcase"},
    {"name": "Shuri Castle", "lat": 26.2172, "lon": 127.7194, "prefecture": "Okinawa", "built": "14th century", "type": "Hilltop (Gusuku)", "notes": "Ryukyu Kingdom palace; UNESCO site; destroyed by fire 2019, under reconstruction"},
    {"name": "Hirosaki Castle", "lat": 40.6072, "lon": 140.4633, "prefecture": "Aomori", "built": "1611", "type": "Hilltop", "notes": "Famous for cherry blossoms; original three-story tower; Tsugaru clan stronghold"},
    {"name": "Bitchu Matsuyama Castle", "lat": 34.8111, "lon": 133.6206, "prefecture": "Okayama", "built": "1240", "type": "Mountain", "notes": "Highest castle in Japan at 430m altitude; original keep; mountain fortress"},
    {"name": "Matsuyama Castle", "lat": 33.8456, "lon": 132.7656, "prefecture": "Ehime", "built": "1602", "type": "Hilltop", "notes": "One of 12 original-keep castles; ropeway access; overlooks Matsuyama city"},
    {"name": "Uwajima Castle", "lat": 33.2222, "lon": 132.5611, "prefecture": "Ehime", "built": "1601", "type": "Hilltop", "notes": "Todo Takatora design; original three-story donjon; small but elegant"},
    {"name": "Kochi Castle", "lat": 33.5594, "lon": 133.5317, "prefecture": "Kochi", "built": "1601", "type": "Hilltop", "notes": "One of 12 original-keep castles; only castle with both original keep and palace"},
    {"name": "Marugame Castle", "lat": 34.2872, "lon": 133.7978, "prefecture": "Kagawa", "built": "1597", "type": "Hilltop", "notes": "Highest stone walls of any Japanese castle (60m); original keep; compact design"},
    {"name": "Maruoka Castle", "lat": 36.1519, "lon": 136.2708, "prefecture": "Fukui", "built": "1576", "type": "Hilltop", "notes": "Oldest surviving donjon (disputed); unique stone-roofed tiles; national importance"},
    {"name": "Okayama Castle", "lat": 34.6617, "lon": 133.9344, "prefecture": "Okayama", "built": "1597", "type": "Flatland", "notes": "Crow Castle due to black exterior; reconstruction after WWII; adjacent to Korakuen garden"},
    {"name": "Aizu-Wakamatsu Castle (Tsuruga)", "lat": 37.4869, "lon": 139.9306, "prefecture": "Fukushima", "built": "1384", "type": "Flatland", "notes": "Crane Castle; last stand of Aizu samurai in Boshin War 1868; red-tiled roof"},
    {"name": "Sendai Castle (Aoba)", "lat": 38.2528, "lon": 140.8567, "prefecture": "Miyagi", "built": "1601", "type": "Mountain", "notes": "Date Masamune's stronghold; no keep but massive stone walls; city views"},
    {"name": "Odawara Castle", "lat": 35.2506, "lon": 139.1533, "prefecture": "Kanagawa", "built": "15th century", "type": "Hilltop", "notes": "Hojo clan stronghold; withstood sieges; fell to Toyotomi Hideyoshi 1590"},
    {"name": "Takeda Castle Ruins", "lat": 35.2975, "lon": 134.8289, "prefecture": "Hyogo", "built": "1441", "type": "Mountain", "notes": "Castle in the Sky; stone walls above clouds; spectacular mountain-top ruins at 353m"},
    {"name": "Shimabara Castle", "lat": 32.7889, "lon": 130.3706, "prefecture": "Nagasaki", "built": "1618-1624", "type": "Flatland", "notes": "Matsukura Shigemasa fortress; Shimabara Rebellion nearby; Christian history museum"},
    {"name": "Wakayama Castle", "lat": 34.2261, "lon": 135.1711, "prefecture": "Wakayama", "built": "1585", "type": "Hilltop", "notes": "Toyotomi Hideyoshi built; later Tokugawa branch domain; reconstructed after WWII bombing"},
    {"name": "Fukuyama Castle", "lat": 34.4877, "lon": 133.3626, "prefecture": "Hiroshima", "built": "1619-1622", "type": "Flatland", "notes": "Adjacent to Shinkansen station; reconstructed keep; Mizuno clan stronghold"},
]

# ═══════════════════════════════════════════════════════════════════════
# 6. MOORISH & ISLAMIC FORTRESSES (24 entries)
# ═══════════════════════════════════════════════════════════════════════
MOORISH_FORTRESSES = [
    {"name": "Alhambra", "lat": 37.1760, "lon": -3.5881, "country": "Spain", "period": "Nasrid (1238-1492)", "notes": "Greatest Moorish palace-fortress; Court of the Lions; intricate stucco and tile work"},
    {"name": "Alcazar of Seville", "lat": 37.3828, "lon": -5.9903, "country": "Spain", "period": "Almohad/Mudejar (12th c.)", "notes": "Royal palace with Moorish architecture; still used by Spanish royal family; UNESCO site"},
    {"name": "Ribat of Monastir", "lat": 35.7780, "lon": 10.8308, "country": "Tunisia", "period": "Abbasid (796 AD)", "notes": "Fortified Islamic monastery; oldest ribat in North Africa; watchtower overlooks Mediterranean"},
    {"name": "Citadel of Cairo", "lat": 30.0286, "lon": 31.2614, "country": "Egypt", "period": "Ayyubid (1176-1183)", "notes": "Saladin's fortress; Muhammad Ali Mosque; dominated Cairo skyline for 700 years"},
    {"name": "Red Fort (Lal Qila)", "lat": 28.6562, "lon": 77.2410, "country": "India", "period": "Mughal (1638-1648)", "notes": "Shah Jahan's Delhi fortress; red sandstone walls; UNESCO site; Indian independence symbol"},
    {"name": "Agra Fort", "lat": 27.1795, "lon": 78.0211, "country": "India", "period": "Mughal (1565-1573)", "notes": "Red sandstone and marble fortress; Shah Jahan imprisoned here viewing Taj Mahal; UNESCO"},
    {"name": "Alcazaba of Malaga", "lat": 36.7211, "lon": -4.4161, "country": "Spain", "period": "Hammudid (1057)", "notes": "Palatial fortification on hilltop; double walls; best-preserved Moorish fortress-palace"},
    {"name": "Alhambra de Granada Alcazaba", "lat": 37.1770, "lon": -3.5930, "country": "Spain", "period": "Zirid/Nasrid (11th c.)", "notes": "Military section of Alhambra complex; oldest part; Torre de la Vela bell tower"},
    {"name": "Chellah", "lat": 33.9558, "lon": -6.8175, "country": "Morocco", "period": "Marinid (1339)", "notes": "Fortified necropolis in Rabat; Roman ruins with Islamic gateway; minaret and gardens"},
    {"name": "Kasbah of the Udayas", "lat": 34.0306, "lon": -6.8372, "country": "Morocco", "period": "Almohad (12th c.)", "notes": "Fortified kasbah in Rabat; Moorish gate Bab Oudaia; overlooks Atlantic and Bou Regreg"},
    {"name": "Ait Benhaddou", "lat": 31.0472, "lon": -7.1297, "country": "Morocco", "period": "11th century", "notes": "Fortified ksar (village) in Atlas Mountains; UNESCO site; used in many films"},
    {"name": "Mehrangarh Fort", "lat": 26.2984, "lon": 73.0183, "country": "India", "period": "Rajput (1459)", "notes": "Imposing fortress rising 125m above Jodhpur; massive walls; one of India's largest forts"},
    {"name": "Golconda Fort", "lat": 17.3833, "lon": 78.4011, "country": "India", "period": "Qutb Shahi (1518)", "notes": "Diamond-trade fortress; acoustic engineering -- clap at gate heard at hilltop 1 km away"},
    {"name": "Aleppo Citadel", "lat": 36.1864, "lon": 37.1614, "country": "Syria", "period": "Ayyubid (12th-13th c.)", "notes": "One of oldest and largest castles in the world; on tell occupied since 3rd millennium BC"},
    {"name": "Citadel of Aleppo Glacis", "lat": 36.1861, "lon": 37.1611, "country": "Syria", "period": "Mamluk (13th c.)", "notes": "Massive stone glacis surrounding citadel hill; defensive slope against siege weapons"},
    {"name": "Bahla Fort", "lat": 22.9647, "lon": 57.3006, "country": "Oman", "period": "Nabhanid (12th-15th c.)", "notes": "Massive mudbrick fortress; 12 km surrounding wall; UNESCO World Heritage Site"},
    {"name": "Nizwa Fort", "lat": 23.5928, "lon": 57.5353, "country": "Oman", "period": "Ya'arubi (1668)", "notes": "Largest round tower in Arabia (36m diameter); date palm oasis; former capital"},
    {"name": "Gwalior Fort", "lat": 26.2275, "lon": 78.1697, "country": "India", "period": "Tomar (8th c.)", "notes": "Hill fortress described as 'pearl among Indian fortresses'; Jain sculptures on cliffs"},
    {"name": "Qala'at al-Bahrain", "lat": 26.2339, "lon": 50.5203, "country": "Bahrain", "period": "Islamic (7th c.+)", "notes": "Tell fortress with 4,000 years of occupation; Portuguese fort on top; UNESCO site"},
    {"name": "Fasil Ghebbi", "lat": 12.6089, "lon": 37.4678, "country": "Ethiopia", "period": "17th century", "notes": "Royal Ethiopian fortress-city in Gondar; Portuguese and Indian influences; UNESCO site"},
    {"name": "Lahore Fort", "lat": 31.5881, "lon": 74.3156, "country": "Pakistan", "period": "Mughal (1566)", "notes": "Sheesh Mahal mirror palace; 21 monuments; Alamgiri Gate; UNESCO World Heritage Site"},
    {"name": "Amber Fort", "lat": 26.9855, "lon": 75.8513, "country": "India", "period": "Rajput (1592)", "notes": "Red sandstone and marble hilltop fortress; Sheesh Mahal; elephant ride approach"},
    {"name": "Castillo de Guzman", "lat": 36.1803, "lon": -5.6106, "country": "Spain", "period": "Almohad (12th c.)", "notes": "Tarifa fortress; Guzman el Bueno legend; southernmost point of continental Europe"},
    {"name": "Rabati Castle", "lat": 41.6392, "lon": 43.2908, "country": "Georgia", "period": "Ottoman (16th c.)", "notes": "Fortress complex in Akhaltsikhe; mosque, church, synagogue, bathhouse; recently restored"},
    {"name": "Citadel of Herat", "lat": 34.3450, "lon": 62.1953, "country": "Afghanistan", "period": "Timurid (15th c.)", "notes": "Alexander the Great's original fort; rebuilt by Timurids; massive restored citadel"},
    {"name": "Qaitbay Citadel", "lat": 31.2139, "lon": 29.8853, "country": "Egypt", "period": "Mamluk (1477)", "notes": "Built on site of Lighthouse of Alexandria; Mamluk defensive fortress; Mediterranean views"},
]

# ═══════════════════════════════════════════════════════════════════════
# 7. VIKING & NORSE FORTIFICATIONS (18 entries)
# ═══════════════════════════════════════════════════════════════════════
VIKING_FORTS = [
    {"name": "Trelleborg (Slagelse)", "lat": 55.3961, "lon": 11.2631, "country": "Denmark", "built": "980 AD", "type": "Ring fort", "notes": "Best-preserved Viking ring fort; geometric perfection; 16 longhouses; Harold Bluetooth era"},
    {"name": "Fyrkat", "lat": 56.6228, "lon": 9.7722, "country": "Denmark", "built": "980 AD", "type": "Ring fort", "notes": "Circular Viking fortress; 120m diameter; reconstructed longhouse; Harold Bluetooth"},
    {"name": "Aggersborg", "lat": 56.9928, "lon": 9.2456, "country": "Denmark", "built": "980 AD", "type": "Ring fort", "notes": "Largest Danish Viking ring fort; 240m diameter; 48 longhouses; controlled Limfjord crossing"},
    {"name": "Nonnebakken", "lat": 55.3917, "lon": 10.3850, "country": "Denmark", "built": "980 AD", "type": "Ring fort", "notes": "Viking ring fort beneath modern Odense; discovered 1900s; traces visible in aerial photos"},
    {"name": "Borgeby", "lat": 55.7550, "lon": 13.0833, "country": "Sweden", "built": "980 AD", "type": "Ring fort", "notes": "Viking ring fort in Scania; 150m diameter; part of Harold Bluetooth's fortress network"},
    {"name": "Jelling", "lat": 55.7564, "lon": 9.4194, "country": "Denmark", "built": "958-987 AD", "type": "Royal monument", "notes": "Royal seat of Harold Bluetooth; rune stones, church, burial mounds; UNESCO site"},
    {"name": "Birka", "lat": 59.3333, "lon": 17.5500, "country": "Sweden", "built": "750-975 AD", "type": "Trading post fortress", "notes": "Major Viking Age trading center on Bjorko island; rampart fortress; UNESCO World Heritage"},
    {"name": "Danevirke", "lat": 54.4833, "lon": 9.5000, "country": "Germany", "built": "5th-12th century", "type": "Linear earthwork", "notes": "30 km defensive wall across Jutland isthmus; expanded by Viking kings; UNESCO nominated"},
    {"name": "Hedeby (Haithabu)", "lat": 54.4889, "lon": 9.5667, "country": "Germany", "built": "8th-11th century", "type": "Trading settlement", "notes": "Major Viking trading town; semicircular rampart; connected to Danevirke; UNESCO site"},
    {"name": "Jomsborg (Wolin)", "lat": 53.8500, "lon": 14.6167, "country": "Poland", "built": "960s AD", "type": "Legendary fortress", "notes": "Legendary Jomsvikings stronghold; Wolin island; archaeological evidence of major settlement"},
    {"name": "Eketorp Fort", "lat": 56.4833, "lon": 16.5667, "country": "Sweden", "built": "300-1200 AD", "type": "Ring fort", "notes": "Reconstructed Oland ring fort; three building phases from Iron Age through Viking Age"},
    {"name": "Ismantorp Fortress", "lat": 56.7167, "lon": 16.5833, "country": "Sweden", "built": "200-600 AD", "type": "Ring fort", "notes": "Iron Age ring fort on Oland; 88 house foundations inside 310m circumference walls"},
    {"name": "Torsburgen", "lat": 57.5833, "lon": 18.6333, "country": "Sweden", "built": "400-600 AD", "type": "Hillfort", "notes": "Largest ancient fort in Scandinavia; 1.1 km wall on Gotland; 112.5 hectares enclosed"},
    {"name": "Gamleborg", "lat": 55.0500, "lon": 14.9167, "country": "Denmark", "built": "750-1050 AD", "type": "Hillfort", "notes": "Viking hillfort on Bornholm island; ring wall enclosing 2.5 hectares; cliff-edge location"},
    {"name": "Borg (Lofoten)", "lat": 68.2500, "lon": 14.0000, "country": "Norway", "built": "500-900 AD", "type": "Chieftain's longhouse", "notes": "Largest Viking longhouse found (83m); reconstructed Viking Museum at Borg; Lofoten islands"},
    {"name": "Foteviken Viking Reserve", "lat": 55.4167, "lon": 12.9500, "country": "Sweden", "built": "Reconstruction", "type": "Reconstructed village", "notes": "Open-air museum with reconstructed Viking Age village; 23 buildings; living history"},
    {"name": "Ring of Brodgar", "lat": 59.0014, "lon": -3.2297, "country": "Scotland", "built": "2500-2000 BC (Norse reuse)", "type": "Stone circle/Norse site", "notes": "Neolithic stone circle reused by Norse settlers; runic inscriptions; Orkney UNESCO site"},
    {"name": "Tingwall (Thingvellir)", "lat": 60.1500, "lon": -1.2000, "country": "Scotland (Shetland)", "built": "Viking Age", "type": "Thing assembly", "notes": "Norse parliament site on island in loch; Law Ting Holm; Shetland's Viking heritage"},
    {"name": "Borgarvirki", "lat": 65.4500, "lon": -20.5500, "country": "Iceland", "built": "Viking Age", "type": "Natural fortress", "notes": "Volcanic plug natural fortress in northern Iceland; enhanced with walls; saga references"},
    {"name": "Gokstad Mound", "lat": 59.1500, "lon": 10.2333, "country": "Norway", "built": "900 AD", "type": "Royal burial/stronghold", "notes": "Viking ship burial of warrior king; excavated 1880; fortified royal estate site"},
    {"name": "Staraya Ladoga Fortress", "lat": 59.9967, "lon": 32.2967, "country": "Russia", "built": "753 AD", "type": "Varangian fortress", "notes": "First capital of Rurik dynasty; oldest stone fortress in Russia; Varangian-Norse origins"},
]

# ═══════════════════════════════════════════════════════════════════════
# 8. ANCIENT CITADELS (24 entries)
# ═══════════════════════════════════════════════════════════════════════
ANCIENT_CITADELS = [
    {"name": "Masada", "lat": 31.3156, "lon": 35.3536, "country": "Israel", "period": "1st century BC", "civilization": "Jewish/Herodian", "notes": "Mountain fortress; last stand of Jewish zealots against Rome (73 AD); UNESCO site"},
    {"name": "Mycenae", "lat": 37.7308, "lon": 22.7569, "country": "Greece", "period": "1350-1200 BC", "civilization": "Mycenaean", "notes": "Lion Gate citadel; Agamemnon's legendary seat; Cyclopean walls; UNESCO site"},
    {"name": "Troy (Hisarlik)", "lat": 39.9575, "lon": 26.2389, "country": "Turkey", "period": "3000-500 BC", "civilization": "Trojan/Greek", "notes": "Homer's legendary Troy; nine layers of civilization; Schliemann excavations; UNESCO"},
    {"name": "Tiryns", "lat": 37.5997, "lon": 22.7994, "country": "Greece", "period": "1400-1200 BC", "civilization": "Mycenaean", "notes": "Cyclopean walls up to 8m thick; Heracles' legendary birthplace; UNESCO site"},
    {"name": "Sigiriya", "lat": 7.9569, "lon": 80.7603, "country": "Sri Lanka", "period": "5th century AD", "civilization": "Sinhalese", "notes": "Lion Rock fortress; 200m-high rock column palace; frescoes and water gardens; UNESCO"},
    {"name": "Sacsayhuaman", "lat": -13.5094, "lon": -71.9822, "country": "Peru", "period": "1438-1508", "civilization": "Inca", "notes": "Megalithic zigzag walls; stones up to 200 tonnes; overlooks Cusco; Inti Raymi festival"},
    {"name": "Great Zimbabwe", "lat": -20.2711, "lon": 30.9336, "country": "Zimbabwe", "period": "11th-15th century", "civilization": "Kingdom of Zimbabwe", "notes": "Largest stone structure in sub-Saharan Africa; dry-stone walls; UNESCO site"},
    {"name": "Acropolis of Athens", "lat": 37.9715, "lon": 23.7267, "country": "Greece", "period": "5th century BC", "civilization": "Athenian", "notes": "Parthenon citadel; Pericles' building program; symbol of classical civilization; UNESCO"},
    {"name": "Carthage (Byrsa Hill)", "lat": 36.8528, "lon": 10.3233, "country": "Tunisia", "period": "814 BC", "civilization": "Phoenician", "notes": "Citadel of ancient Carthage; Punic Wars against Rome; destroyed 146 BC; UNESCO site"},
    {"name": "Persepolis", "lat": 29.9353, "lon": 52.8914, "country": "Iran", "period": "518 BC", "civilization": "Achaemenid Persian", "notes": "Ceremonial capital of Persian Empire; Gate of All Nations; destroyed by Alexander; UNESCO"},
    {"name": "Arg-e Bam", "lat": 29.1169, "lon": 58.3567, "country": "Iran", "period": "6th century BC", "civilization": "Achaemenid/Sasanian", "notes": "Largest adobe structure in the world; 2003 earthquake devastated; under restoration; UNESCO"},
    {"name": "Derinkuyu Underground City", "lat": 38.3728, "lon": 34.7339, "country": "Turkey", "period": "8th century BC", "civilization": "Phrygian/Byzantine", "notes": "18-story underground fortress-city; housed 20,000 people; ventilation shafts; Cappadocia"},
    {"name": "Maiden's Tower (Qiz Qalasi)", "lat": 40.3661, "lon": 49.8372, "country": "Azerbaijan", "period": "12th century", "civilization": "Shirvan", "notes": "Cylindrical Baku tower; origins debated (5th-12th c.); UNESCO World Heritage old city"},
    {"name": "Ollantaytambo", "lat": -13.2581, "lon": -72.2636, "country": "Peru", "period": "15th century", "civilization": "Inca", "notes": "Inca fortress and temple; massive terraces; living Inca town; gateway to Machu Picchu"},
    {"name": "Taxila (Sirkap)", "lat": 33.7489, "lon": 72.8147, "country": "Pakistan", "period": "2nd century BC", "civilization": "Indo-Greek", "notes": "Hellenistic fortified city; grid plan; Buddhist stupas within walls; UNESCO site"},
    {"name": "Hattusa", "lat": 40.0200, "lon": 34.6153, "country": "Turkey", "period": "1600-1178 BC", "civilization": "Hittite", "notes": "Capital of Hittite Empire; Lion Gate, King's Gate; 6 km walls; UNESCO site"},
    {"name": "Mohenjo-daro", "lat": 27.3242, "lon": 68.1358, "country": "Pakistan", "period": "2500-1900 BC", "civilization": "Indus Valley", "notes": "Citadel mound of ancient city; Great Bath; advanced urban planning; UNESCO site"},
    {"name": "Chavin de Huantar", "lat": -9.5947, "lon": -77.1769, "country": "Peru", "period": "900-200 BC", "civilization": "Chavin", "notes": "Temple-fortress complex; underground galleries; Lanzon stela; UNESCO site"},
    {"name": "Monte Alban", "lat": 17.0431, "lon": -96.7678, "country": "Mexico", "period": "500 BC - 750 AD", "civilization": "Zapotec", "notes": "Hilltop citadel-city; flattened mountain; astronomical observatory; UNESCO site"},
    {"name": "Tulum", "lat": 20.2145, "lon": -87.4291, "country": "Mexico", "period": "1200-1521 AD", "civilization": "Maya", "notes": "Walled Maya city on Caribbean cliffs; El Castillo pyramid; only Maya coastal fortress"},
    {"name": "Maiden Castle", "lat": 50.6928, "lon": -2.4697, "country": "England", "period": "600 BC", "civilization": "Iron Age Celtic", "notes": "Largest Iron Age hillfort in Europe; multiple ramparts; conquered by Romans 43 AD"},
    {"name": "Nuraghe Su Nuraxi", "lat": 39.7069, "lon": 8.9900, "country": "Italy (Sardinia)", "period": "1500 BC", "civilization": "Nuragic", "notes": "Bronze Age tower fortress; central keep with four corner towers; UNESCO site"},
    {"name": "Zimbabwe Khami Ruins", "lat": -20.1583, "lon": 28.3833, "country": "Zimbabwe", "period": "15th-17th century", "civilization": "Torwa/Rozvi", "notes": "Capital after Great Zimbabwe; decorated stone platforms; UNESCO site"},
    {"name": "Tughlaqabad Fort", "lat": 28.5167, "lon": 77.2583, "country": "India", "period": "1321-1325", "civilization": "Delhi Sultanate", "notes": "Ruined fortress-city of Ghiyath al-Din Tughluq; massive rubble-stone walls; cursed by saint"},
    {"name": "Dun Aonghasa", "lat": 53.1244, "lon": -9.7667, "country": "Ireland", "period": "1100 BC", "civilization": "Bronze Age Celtic", "notes": "Cliff-edge stone fort on Aran Islands; semicircular walls; chevaux de frise stone defence"},
    {"name": "Knossos", "lat": 35.2981, "lon": 25.1631, "country": "Greece (Crete)", "period": "1700-1400 BC", "civilization": "Minoan", "notes": "Palace citadel; Minotaur labyrinth legend; Arthur Evans excavations; advanced plumbing"},
]

# ═══════════════════════════════════════════════════════════════════════
# 9. PRISON FORTRESSES (20 entries)
# ═══════════════════════════════════════════════════════════════════════
PRISON_FORTRESSES = [
    {"name": "Tower of London", "lat": 51.5081, "lon": -0.0759, "country": "England", "built": "1066", "famous_prisoners": "Anne Boleyn, Guy Fawkes, Rudolf Hess", "notes": "Royal fortress, prison, and execution site; Crown Jewels; Beefeaters and ravens"},
    {"name": "Bastille (site)", "lat": 48.8532, "lon": 2.3692, "country": "France", "built": "1370-1383", "famous_prisoners": "Voltaire, Marquis de Sade", "notes": "Symbol of royal tyranny; storming on 14 July 1789 sparked French Revolution; now demolished"},
    {"name": "Chateau d'If", "lat": 43.2800, "lon": 5.3250, "country": "France", "built": "1524-1531", "famous_prisoners": "Comte de Mirabeau, Jose Custodio Faria", "notes": "Island fortress near Marseille; inspired Count of Monte Cristo; Huguenot prisoners"},
    {"name": "Spandau Citadel", "lat": 52.5372, "lon": 13.2050, "country": "Germany", "built": "1559-1594", "famous_prisoners": "Rudolf Hess, Albert Speer, Karl Donitz", "notes": "Renaissance fortress; held Nazi war criminals; Hess sole prisoner 1966-1987; demolished prison"},
    {"name": "Alcatraz Island", "lat": 37.8267, "lon": -122.4233, "country": "USA", "built": "1850s (fortress), 1934 (prison)", "famous_prisoners": "Al Capone, Robert Stroud, Machine Gun Kelly", "notes": "Island fortress in San Francisco Bay; 'inescapable' federal prison 1934-1963"},
    {"name": "Devil's Island", "lat": 5.2944, "lon": -52.5833, "country": "French Guiana", "built": "1852", "famous_prisoners": "Alfred Dreyfus, Henri Charriere (Papillon)", "notes": "Notorious penal colony; 80% mortality rate; closed 1953; jungle reclaiming ruins"},
    {"name": "Edinburgh Castle Prison", "lat": 55.9486, "lon": -3.1999, "country": "Scotland", "built": "12th century", "famous_prisoners": "Jacobite prisoners, Napoleonic war POWs", "notes": "Castle vaults used as prison for centuries; graffiti from Napoleonic prisoners visible"},
    {"name": "Colditz Castle (Oflag IV-C)", "lat": 51.1308, "lon": 12.8139, "country": "Germany", "built": "1083 (WWII prison 1939-1945)", "famous_prisoners": "Douglas Bader, Pat Reid, Airey Neave", "notes": "POW camp for escape-prone officers; 30+ successful escapes; hidden glider in attic"},
    {"name": "Fortress of Peter and Paul", "lat": 59.9500, "lon": 30.3167, "country": "Russia", "built": "1703-1740", "famous_prisoners": "Dostoevsky, Gorky, Trotsky, Kropotkin", "notes": "St Petersburg citadel; Trubetskoy Bastion prison; tsarist political prisoners"},
    {"name": "Spielberg Castle", "lat": 49.1939, "lon": 16.5997, "country": "Czech Republic", "built": "13th century", "famous_prisoners": "Silvio Pellico, Italian revolutionaries", "notes": "Brno fortress used as Habsburg prison; Pellico's 'My Prisons' made it notorious"},
    {"name": "Fort Santiago", "lat": 14.5906, "lon": 120.9700, "country": "Philippines", "built": "1571", "famous_prisoners": "Jose Rizal (executed 1896)", "notes": "Spanish colonial citadel in Manila; Rizal's prison cell preserved; Japanese atrocities in WWII"},
    {"name": "Robben Island", "lat": -33.8060, "lon": 18.3664, "country": "South Africa", "built": "1961 (prison)", "famous_prisoners": "Nelson Mandela (18 years), Walter Sisulu", "notes": "Apartheid political prison; Mandela's cell preserved; UNESCO World Heritage Site"},
    {"name": "Kilmainham Gaol", "lat": 53.3419, "lon": -6.3100, "country": "Ireland", "built": "1796", "famous_prisoners": "Parnell, de Valera, Countess Markievicz", "notes": "Irish political prison; 1916 Easter Rising leaders executed in yard; now museum"},
    {"name": "Forte de Peniche", "lat": 39.3567, "lon": -9.3786, "country": "Portugal", "built": "1557", "famous_prisoners": "Alvaro Cunhal, political prisoners", "notes": "Star fortress used as political prison under Salazar; daring escape in 1960"},
    {"name": "Goree Island", "lat": 14.6672, "lon": -17.3978, "country": "Senegal", "built": "17th century", "famous_prisoners": "Enslaved Africans", "notes": "Slave-trade fortress island; House of Slaves museum; symbol of Atlantic slave trade; UNESCO"},
    {"name": "Sinop Fortress Prison", "lat": 42.0264, "lon": 35.1531, "country": "Turkey", "built": "7th century BC (prison 1887-1999)", "famous_prisoners": "Turkish writers, political dissidents", "notes": "Ancient Black Sea fortress; used as prison for over a century; now museum"},
    {"name": "Castle of Good Hope", "lat": -33.9258, "lon": 18.4269, "country": "South Africa", "built": "1666-1679", "famous_prisoners": "Khoi leaders, political prisoners", "notes": "Oldest colonial building in South Africa; star fort; VOC headquarters; prison dungeon"},
    {"name": "San Juan de Ulua", "lat": 19.2158, "lon": -96.1339, "country": "Mexico", "built": "1535-1707", "famous_prisoners": "Benito Juarez, political prisoners", "notes": "Island fortress in Veracruz harbour; last Spanish stronghold in Mexico (1825)"},
    {"name": "Hoa Lo Prison (Hanoi Hilton)", "lat": 21.0254, "lon": 105.8467, "country": "Vietnam", "built": "1896", "famous_prisoners": "John McCain, American POWs", "notes": "French colonial prison; held American POWs during Vietnam War; partly demolished"},
    {"name": "Elmina Castle", "lat": 5.0847, "lon": -1.3486, "country": "Ghana", "built": "1482", "famous_prisoners": "Enslaved Africans", "notes": "Portuguese-built castle; slave trade dungeon; Door of No Return; UNESCO World Heritage"},
    {"name": "Suomenlinna Fortress", "lat": 60.1456, "lon": 24.9881, "country": "Finland", "built": "1748", "famous_prisoners": "Political prisoners, POWs", "notes": "Sea fortress on six islands; Swedish-built; Finnish independence prison camp; UNESCO site"},
    {"name": "Forte de Sao Jorge da Mina", "lat": 5.0833, "lon": -1.3500, "country": "Ghana", "built": "1482", "famous_prisoners": "Enslaved Africans (millions transited)", "notes": "First European trading post in West Africa; trans-Atlantic slave trade hub; Portuguese fort"},
    {"name": "Theresienstadt (Terezin)", "lat": 50.5131, "lon": 14.1500, "country": "Czech Republic", "built": "1780", "famous_prisoners": "Jews, Roma, political prisoners", "notes": "Habsburg star fortress converted to Nazi ghetto/camp; propaganda 'model settlement'; 33,000 died"},
    {"name": "Carlsten Fortress", "lat": 57.8803, "lon": 11.4497, "country": "Sweden", "built": "1658", "famous_prisoners": "Lasse-Maja (famous Swedish thief)", "notes": "Granite fortress on Marstrand island; prison for centuries; now tourist attraction"},
]

# ═══════════════════════════════════════════════════════════════════════
# 10. UNDERGROUND & HIDDEN FORTIFICATIONS (18 entries)
# ═══════════════════════════════════════════════════════════════════════
UNDERGROUND_FORTS = [
    {"name": "Maginot Line (Ouvrage Schoenenbourg)", "lat": 48.9486, "lon": 7.9064, "country": "France", "built": "1929-1938", "type": "Underground fortress line", "notes": "Vast underground complex; artillery casemates, barracks, railway; bypassed by Germans 1940"},
    {"name": "Derinkuyu Underground City", "lat": 38.3728, "lon": 34.7339, "country": "Turkey", "built": "8th-7th century BC", "type": "Underground city", "notes": "18 stories deep; housed 20,000 people; ventilation shafts; millstone doors; Cappadocia"},
    {"name": "Cu Chi Tunnels", "lat": 11.1422, "lon": 106.4636, "country": "Vietnam", "built": "1948-1975", "type": "Tunnel network", "notes": "250 km network used by Viet Cong; hospitals, kitchens, weapon factories; tourist site"},
    {"name": "Gibraltar Tunnels", "lat": 36.1408, "lon": -5.3536, "country": "Gibraltar (UK)", "built": "1782-WWII", "type": "Rock tunnels", "notes": "52 km of tunnels inside Rock of Gibraltar; WWII operation base for 16,000 troops"},
    {"name": "Fortress Furigen (Swiss Reduit)", "lat": 46.9833, "lon": 8.3500, "country": "Switzerland", "built": "1940s", "type": "Hidden mountain fortress", "notes": "Part of Swiss National Reduit; disguised as chalets and rock faces; nuclear-proof"},
    {"name": "Kaymakli Underground City", "lat": 38.4622, "lon": 34.7497, "country": "Turkey", "built": "8th-7th century BC", "type": "Underground city", "notes": "Eight stories deep; connected to Derinkuyu by tunnel; 3,500 people capacity; Cappadocia"},
    {"name": "Wieliczka Salt Mine Fortress", "lat": 49.9833, "lon": 20.0500, "country": "Poland", "built": "13th century (fortified WWII)", "type": "Underground mine fortress", "notes": "Salt mine with chapels and chambers; Germans used as underground factory in WWII; UNESCO"},
    {"name": "Adrspach-Teplice Rocks Bunkers", "lat": 50.6153, "lon": 16.1219, "country": "Czech Republic", "built": "1936-1938", "type": "Rock fortress bunkers", "notes": "Part of Czechoslovak border fortifications; concrete bunkers in sandstone rock labyrinth"},
    {"name": "Fort Eben-Emael", "lat": 50.7928, "lon": 5.6817, "country": "Belgium", "built": "1932-1935", "type": "Underground fortress", "notes": "Considered impregnable; captured in 11 minutes by German glider troops May 1940"},
    {"name": "Ouvrage Hackenberg", "lat": 49.3506, "lon": 6.3381, "country": "France", "built": "1929-1935", "type": "Maginot fortress", "notes": "Largest Maginot ouvrage; 10 km tunnels; electric railway; 1,000+ garrison; never captured"},
    {"name": "Churchill War Rooms", "lat": 51.5022, "lon": -0.1289, "country": "England", "built": "1938", "type": "Underground command centre", "notes": "Secret bunker beneath Westminster; Churchill's WWII headquarters; preserved as museum"},
    {"name": "Josefov Fortress", "lat": 50.3453, "lon": 15.9394, "country": "Czech Republic", "built": "1780-1787", "type": "Underground star fortress", "notes": "Star fortress with 45 km of underground passages; largest military structure in Central Europe"},
    {"name": "Wolfsschanze (Wolf's Lair)", "lat": 54.0797, "lon": 21.4972, "country": "Poland", "built": "1940-1944", "type": "Bunker complex", "notes": "Hitler's Eastern Front HQ; July 20 assassination attempt 1944; massive concrete ruins"},
    {"name": "Svalbard Global Seed Vault", "lat": 78.2382, "lon": 15.4467, "country": "Norway", "built": "2008", "type": "Underground vault", "notes": "Doomsday vault in Arctic mountain; 1.1 million seed samples; permafrost preservation"},
    {"name": "Burlington Bunker (Site 3)", "lat": 51.4100, "lon": -2.1600, "country": "England", "built": "1950s", "type": "Underground city", "notes": "Secret Cold War city for 4,000 government staff; 35 acres underground; BBC studio"},
    {"name": "Raven Rock Mountain Complex", "lat": 39.7294, "lon": -77.4189, "country": "USA", "built": "1951-1953", "type": "Underground Pentagon", "notes": "Alternate Joint Communications Center; underground Pentagon backup; still classified"},
    {"name": "Cheyenne Mountain Complex", "lat": 38.7456, "lon": -104.8461, "country": "USA", "built": "1961-1966", "type": "Mountain fortress", "notes": "NORAD headquarters inside mountain; blast doors; springs-mounted buildings; nuclear-proof"},
    {"name": "Ligne P (Pyrenees Line)", "lat": 42.5000, "lon": 0.0000, "country": "France/Spain", "built": "1938-1940", "type": "Mountain bunker line", "notes": "Maginot extension in Pyrenees; bunkers and casemates; largely forgotten; now hiking sites"},
    {"name": "Mittelbau-Dora Underground Factory", "lat": 51.5306, "lon": 10.7486, "country": "Germany", "built": "1943-1945", "type": "Underground factory", "notes": "V-2 rocket underground factory in tunnels; 20,000 slave labourers died; memorial site"},
    {"name": "Sonnenberg Tunnel Bunker", "lat": 47.0500, "lon": 8.3000, "country": "Switzerland", "built": "1976", "type": "Civil defence bunker", "notes": "Largest civil defence bunker in world; capacity 20,000 people; inside highway tunnel in Lucerne"},
    {"name": "Riese Complex", "lat": 50.6167, "lon": 16.5000, "country": "Poland", "built": "1943-1945", "type": "Underground complex", "notes": "Nazi underground construction in Owl Mountains; seven structures; purpose debated; slave labour"},
    {"name": "Mount Yamantau", "lat": 54.2500, "lon": 58.1000, "country": "Russia", "built": "1970s-present", "type": "Secret mountain complex", "notes": "Alleged massive underground complex in Urals; nuclear bunker; details remain classified"},
]


# ═══════════════════════════════════════════════════════════════════════
# HELPER: safe HTML for popups
# ═══════════════════════════════════════════════════════════════════════
def _esc(text):
    """Escape user-provided strings for safe HTML embedding."""
    return html_module.escape(str(text))


# ═══════════════════════════════════════════════════════════════════════
# HELPER: render folium map in Streamlit
# ═══════════════════════════════════════════════════════════════════════
def _show_map(m, height=500):
    st_html(m._repr_html_(), height=height)


# ═══════════════════════════════════════════════════════════════════════
# HELPER: CSV download button
# ═══════════════════════════════════════════════════════════════════════
def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, buf.getvalue(), file_name=filename, mime="text/csv")


# ═══════════════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _get_fortress_summary(mode_name: str):
    """Return cached summary statistics for the given mode."""
    data_map = {
        MAP_MODES[0]: ("Medieval Castles", MEDIEVAL_CASTLES, "country"),
        MAP_MODES[1]: ("Crusader Fortresses", CRUSADER_FORTRESSES, "country"),
        MAP_MODES[2]: ("Star Forts", STAR_FORTS, "country"),
        MAP_MODES[3]: ("Great Walls", GREAT_WALLS, "country"),
        MAP_MODES[4]: ("Japanese Castles", JAPANESE_CASTLES, "prefecture"),
        MAP_MODES[5]: ("Moorish Fortresses", MOORISH_FORTRESSES, "country"),
        MAP_MODES[6]: ("Viking Forts", VIKING_FORTS, "country"),
        MAP_MODES[7]: ("Ancient Citadels", ANCIENT_CITADELS, "country"),
        MAP_MODES[8]: ("Prison Fortresses", PRISON_FORTRESSES, "country"),
        MAP_MODES[9]: ("Underground Forts", UNDERGROUND_FORTS, "country"),
    }
    info = data_map.get(mode_name)
    if not info:
        return {}
    label, data, region_key = info
    df = pd.DataFrame(data)
    return {
        "label": label,
        "count": len(df),
        "regions": df[region_key].nunique(),
        "region_key": region_key,
    }


@st.cache_data(ttl=3600)
def _fetch_wiki_snippet(query: str):
    """Fetch a short Wikipedia snippet for a fortress (best-effort, non-blocking)."""
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
            "utf8": 1,
        }
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("query", {}).get("search", [])
        if results:
            snippet = results[0].get("snippet", "")
            title = results[0].get("title", "")
            return {"title": title, "snippet": snippet}
    except Exception:
        pass
    return None


def _render_medieval_castles():
    st.markdown("#### Greatest Medieval Castles")
    st.info(
        "A curated tour of the world's most magnificent medieval castles, "
        "from fairy-tale palaces to impregnable fortresses spanning 1,000 years of history."
    )
    df = pd.DataFrame(MEDIEVAL_CASTLES)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Castles Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Architectural Styles", df["style"].nunique())
    c4.metric("UNESCO Sites", sum(1 for r in MEDIEVAL_CASTLES if "UNESCO" in r["notes"]))

    m = folium.Map(location=[48.0, 10.0], zoom_start=4, tiles="CartoDB dark_matter")
    for r in MEDIEVAL_CASTLES:
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:#f59e0b'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; Built: {_esc(r['built'])}<br>"
            f"Style: {_esc(r['style'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color="#f59e0b",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "built", "style", "notes"]], width="stretch")
    _csv_download(df, "medieval_castles.csv")


def _render_crusader_fortresses():
    st.markdown("#### Crusader Fortresses")
    st.info(
        "22 Crusader-era fortifications across the Holy Land, Cyprus, and the Mediterranean -- "
        "from the mighty Krak des Chevaliers to coastal sea castles."
    )
    df = pd.DataFrame(CRUSADER_FORTRESSES)
    c1, c2, c3 = st.columns(3)
    c1.metric("Fortresses Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Military Orders", df["order"].nunique())

    order_colors = {
        "Knights Hospitaller": "#dc2626",
        "Knights Templar": "#f59e0b",
        "Teutonic Knights": "#3b82f6",
        "Kingdom of Jerusalem": "#10b981",
        "Crusader Kingdom": "#10b981",
        "Crusader Lordship": "#10b981",
        "County of Tripoli": "#8b5cf6",
        "Crusader Principality": "#8b5cf6",
        "Lusignan Kingdom": "#06b6d4",
        "Ayyubid (anti-Crusader)": "#64748b",
        "Ayyubid/Mamluk": "#64748b",
    }

    m = folium.Map(location=[33.5, 35.5], zoom_start=6, tiles="CartoDB dark_matter")
    for r in CRUSADER_FORTRESSES:
        clr = order_colors.get(r["order"], "#94a3b8")
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['order'])}<br>"
            f"Built: {_esc(r['built'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=9,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend:** "
                ":red_circle: Hospitaller &nbsp; "
                ":large_orange_circle: Templar &nbsp; "
                ":large_blue_circle: Teutonic &nbsp; "
                ":green_circle: Kingdom of Jerusalem")

    st.dataframe(df[["name", "country", "order", "built", "notes"]], width="stretch")
    _csv_download(df, "crusader_fortresses.csv")


def _render_star_forts():
    st.markdown("#### Star Forts & Bastions")
    st.info(
        "22 star-shaped fortifications from the age of gunpowder -- geometric masterpieces "
        "designed by Vauban, the Venetians, and military engineers across Europe and beyond."
    )
    df = pd.DataFrame(STAR_FORTS)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Forts Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Avg. Points", f"{df['points'].mean():.1f}")
    c4.metric("UNESCO Sites", sum(1 for r in STAR_FORTS if "UNESCO" in r["notes"]))

    m = folium.Map(location=[45.0, 5.0], zoom_start=4, tiles="CartoDB dark_matter")
    for r in STAR_FORTS:
        points = r["points"]
        if points <= 4:
            clr = "#06b6d4"
        elif points <= 5:
            clr = "#10b981"
        elif points <= 6:
            clr = "#f59e0b"
        else:
            clr = "#dc2626"
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; Built: {_esc(r['built'])}<br>"
            f"Points/sides: {_esc(r['points'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=7 + points,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.65,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend (by points):** "
                ":blue_circle: 4 &nbsp; "
                ":green_circle: 5 &nbsp; "
                ":large_orange_circle: 6 &nbsp; "
                ":red_circle: 7+")

    st.dataframe(df[["name", "country", "built", "points", "notes"]], width="stretch")
    _csv_download(df, "star_forts.csv")


def _render_great_walls():
    st.markdown("#### Great Walls & Barriers")
    st.info(
        "22 of history's greatest defensive walls and barriers -- from the Great Wall of China "
        "to modern separation barriers, spanning 3,000 years of fortification."
    )
    df = pd.DataFrame(GREAT_WALLS)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Walls Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Length", f"{df['length_km'].sum():,.0f} km")
    c4.metric("Longest", f"{df['length_km'].max():,.0f} km")

    m = folium.Map(location=[35.0, 30.0], zoom_start=3, tiles="CartoDB dark_matter")
    for r in GREAT_WALLS:
        length = r["length_km"]
        if length >= 1000:
            clr = "#dc2626"
            rad = 12
        elif length >= 100:
            clr = "#f59e0b"
            rad = 9
        elif length >= 10:
            clr = "#10b981"
            rad = 7
        else:
            clr = "#06b6d4"
            rad = 5
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; Built: {_esc(r['built'])}<br>"
            f"Length: {_esc(r['length_km'])} km<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=rad,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend (by length):** "
                ":red_circle: 1000+ km &nbsp; "
                ":large_orange_circle: 100-999 km &nbsp; "
                ":green_circle: 10-99 km &nbsp; "
                ":blue_circle: <10 km")

    st.dataframe(df[["name", "country", "built", "length_km", "notes"]], width="stretch")
    _csv_download(df, "great_walls.csv")


def _render_japanese_castles():
    st.markdown("#### Japanese Castles")
    st.info(
        "24 iconic Japanese castles spanning from the Sengoku period to the Meiji Restoration -- "
        "hilltop fortresses, flatland castles, and mountain strongholds across Japan."
    )
    df = pd.DataFrame(JAPANESE_CASTLES)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Castles Mapped", len(df))
    c2.metric("Prefectures", df["prefecture"].nunique())
    c3.metric("Castle Types", df["type"].nunique())
    c4.metric("National Treasures", sum(1 for r in JAPANESE_CASTLES if "national treasure" in r["notes"].lower()))

    type_colors = {
        "Hilltop": "#dc2626",
        "Flatland": "#3b82f6",
        "Mountain": "#10b981",
        "Hilltop (Gusuku)": "#f59e0b",
    }

    m = folium.Map(location=[36.5, 137.0], zoom_start=6, tiles="CartoDB dark_matter")
    for r in JAPANESE_CASTLES:
        clr = type_colors.get(r["type"], "#94a3b8")
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['prefecture'])}</i> &middot; Built: {_esc(r['built'])}<br>"
            f"Type: {_esc(r['type'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend:** "
                ":red_circle: Hilltop &nbsp; "
                ":large_blue_circle: Flatland &nbsp; "
                ":green_circle: Mountain &nbsp; "
                ":large_orange_circle: Gusuku")

    st.dataframe(df[["name", "prefecture", "built", "type", "notes"]], width="stretch")
    _csv_download(df, "japanese_castles.csv")


def _render_moorish_fortresses():
    st.markdown("#### Moorish & Islamic Fortresses")
    st.info(
        "24 magnificent Islamic fortifications from Iberia to India -- Moorish alcazars, "
        "Mughal forts, Arabian citadels, and North African kasbahs."
    )
    df = pd.DataFrame(MOORISH_FORTRESSES)
    c1, c2, c3 = st.columns(3)
    c1.metric("Fortresses Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("UNESCO Sites", sum(1 for r in MOORISH_FORTRESSES if "UNESCO" in r["notes"]))

    m = folium.Map(location=[30.0, 40.0], zoom_start=3, tiles="CartoDB dark_matter")
    for r in MOORISH_FORTRESSES:
        period = r["period"]
        if "Mughal" in period:
            clr = "#dc2626"
        elif "Nasrid" in period or "Almohad" in period or "Moorish" in period:
            clr = "#f59e0b"
        elif "Rajput" in period:
            clr = "#e879f9"
        elif "Ayyubid" in period or "Mamluk" in period:
            clr = "#10b981"
        else:
            clr = "#06b6d4"
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['period'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend:** "
                ":red_circle: Mughal &nbsp; "
                ":large_orange_circle: Moorish/Nasrid &nbsp; "
                ":purple_circle: Rajput &nbsp; "
                ":green_circle: Ayyubid/Mamluk &nbsp; "
                ":blue_circle: Other")

    st.dataframe(df[["name", "country", "period", "notes"]], width="stretch")
    _csv_download(df, "moorish_fortresses.csv")


def _render_viking_forts():
    st.markdown("#### Viking & Norse Fortifications")
    st.info(
        "18 Viking Age and Norse fortification sites across Scandinavia and beyond -- "
        "from Harald Bluetooth's geometric ring forts to Iron Age hillforts."
    )
    df = pd.DataFrame(VIKING_FORTS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Fortification Types", df["type"].nunique())

    type_colors = {
        "Ring fort": "#dc2626",
        "Royal monument": "#f59e0b",
        "Trading post fortress": "#10b981",
        "Linear earthwork": "#3b82f6",
        "Trading settlement": "#10b981",
        "Legendary fortress": "#8b5cf6",
        "Hillfort": "#06b6d4",
        "Chieftain's longhouse": "#e879f9",
        "Reconstructed village": "#64748b",
        "Stone circle/Norse site": "#94a3b8",
        "Thing assembly": "#fbbf24",
    }

    m = folium.Map(location=[57.0, 12.0], zoom_start=5, tiles="CartoDB dark_matter")
    for r in VIKING_FORTS:
        clr = type_colors.get(r["type"], "#94a3b8")
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['built'])}<br>"
            f"Type: {_esc(r['type'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend:** "
                ":red_circle: Ring fort &nbsp; "
                ":large_orange_circle: Royal monument &nbsp; "
                ":green_circle: Trading &nbsp; "
                ":large_blue_circle: Earthwork &nbsp; "
                ":purple_circle: Legendary &nbsp; "
                ":blue_circle: Hillfort")

    st.dataframe(df[["name", "country", "built", "type", "notes"]], width="stretch")
    _csv_download(df, "viking_forts.csv")


def _render_ancient_citadels():
    st.markdown("#### Ancient Citadels")
    st.info(
        "24 ancient citadels and fortress-cities from prehistory to the medieval period -- "
        "Mycenaean megaliths, Inca strongholds, and Bronze Age towers."
    )
    df = pd.DataFrame(ANCIENT_CITADELS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Citadels Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Civilizations", df["civilization"].nunique())

    m = folium.Map(location=[25.0, 40.0], zoom_start=3, tiles="CartoDB dark_matter")
    for r in ANCIENT_CITADELS:
        civ = r["civilization"]
        if "Greek" in civ or "Mycenaean" in civ or "Athenian" in civ:
            clr = "#3b82f6"
        elif "Inca" in civ or "Maya" in civ or "Zapotec" in civ or "Chavin" in civ:
            clr = "#10b981"
        elif "Persian" in civ or "Hittite" in civ or "Sasanian" in civ:
            clr = "#f59e0b"
        elif "Jewish" in civ or "Herodian" in civ:
            clr = "#dc2626"
        elif "Indus" in civ or "Delhi" in civ or "Indo" in civ:
            clr = "#e879f9"
        else:
            clr = "#06b6d4"
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['period'])}<br>"
            f"Civilization: {_esc(r['civilization'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend:** "
                ":large_blue_circle: Greek/Mycenaean &nbsp; "
                ":green_circle: Americas &nbsp; "
                ":large_orange_circle: Persian/Hittite &nbsp; "
                ":red_circle: Jewish &nbsp; "
                ":purple_circle: Indian &nbsp; "
                ":blue_circle: Other")

    st.dataframe(df[["name", "country", "period", "civilization", "notes"]], width="stretch")
    _csv_download(df, "ancient_citadels.csv")


def _render_prison_fortresses():
    st.markdown("#### Prison Fortresses")
    st.info(
        "20 fortresses that served as notorious prisons -- from the Tower of London "
        "to Alcatraz, where stone walls held history's most famous captives."
    )
    df = pd.DataFrame(PRISON_FORTRESSES)
    c1, c2, c3 = st.columns(3)
    c1.metric("Prison Fortresses", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Slave Trade Sites", sum(1 for r in PRISON_FORTRESSES if "slave" in r["notes"].lower() or "enslaved" in r["famous_prisoners"].lower()))

    m = folium.Map(location=[30.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in PRISON_FORTRESSES:
        notes_lower = r["notes"].lower()
        if "slave" in notes_lower or "enslaved" in r["famous_prisoners"].lower():
            clr = "#dc2626"
        elif "political" in notes_lower or "apartheid" in notes_lower:
            clr = "#f59e0b"
        elif "POW" in r["notes"] or "war criminal" in notes_lower:
            clr = "#3b82f6"
        else:
            clr = "#06b6d4"
        popup = (
            f"<div style='min-width:240px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; Built: {_esc(r['built'])}<br>"
            f"<b>Famous prisoners:</b> {_esc(r['famous_prisoners'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=9,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend:** "
                ":red_circle: Slave trade &nbsp; "
                ":large_orange_circle: Political prison &nbsp; "
                ":large_blue_circle: POW/War crimes &nbsp; "
                ":blue_circle: Other")

    st.dataframe(df[["name", "country", "built", "famous_prisoners", "notes"]], width="stretch")
    _csv_download(df, "prison_fortresses.csv")


def _render_underground_forts():
    st.markdown("#### Underground & Hidden Fortifications")
    st.info(
        "18 underground and concealed fortifications -- from ancient Cappadocian cities "
        "carved into rock to Cold War nuclear bunkers hidden inside mountains."
    )
    df = pd.DataFrame(UNDERGROUND_FORTS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Fortification Types", df["type"].nunique())

    type_colors = {
        "Underground fortress line": "#dc2626",
        "Underground city": "#f59e0b",
        "Tunnel network": "#10b981",
        "Rock tunnels": "#3b82f6",
        "Hidden mountain fortress": "#8b5cf6",
        "Underground mine fortress": "#e879f9",
        "Rock fortress bunkers": "#64748b",
        "Underground fortress": "#dc2626",
        "Maginot fortress": "#dc2626",
        "Underground command centre": "#06b6d4",
        "Underground star fortress": "#f59e0b",
        "Bunker complex": "#94a3b8",
        "Underground vault": "#10b981",
        "Underground city": "#f59e0b",
        "Underground Pentagon": "#3b82f6",
        "Mountain fortress": "#8b5cf6",
        "Mountain bunker line": "#64748b",
    }

    m = folium.Map(location=[42.0, 20.0], zoom_start=3, tiles="CartoDB dark_matter")
    for r in UNDERGROUND_FORTS:
        clr = type_colors.get(r["type"], "#94a3b8")
        popup = (
            f"<div style='min-width:220px'>"
            f"<b style='color:{clr}'>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; Built: {_esc(r['built'])}<br>"
            f"Type: {_esc(r['type'])}<br>"
            f"<small>{_esc(r['notes'])}</small></div>"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.markdown("**Legend:** "
                ":red_circle: Fortress line &nbsp; "
                ":large_orange_circle: Underground city &nbsp; "
                ":green_circle: Tunnels/Vault &nbsp; "
                ":large_blue_circle: Rock/Pentagon &nbsp; "
                ":purple_circle: Mountain fortress")

    st.dataframe(df[["name", "country", "built", "type", "notes"]], width="stretch")
    _csv_download(df, "underground_forts.csv")


# ═══════════════════════════════════════════════════════════════════════
# RENDERER DISPATCH
# ═══════════════════════════════════════════════════════════════════════
_RENDERERS = {
    MAP_MODES[0]: _render_medieval_castles,
    MAP_MODES[1]: _render_crusader_fortresses,
    MAP_MODES[2]: _render_star_forts,
    MAP_MODES[3]: _render_great_walls,
    MAP_MODES[4]: _render_japanese_castles,
    MAP_MODES[5]: _render_moorish_fortresses,
    MAP_MODES[6]: _render_viking_forts,
    MAP_MODES[7]: _render_ancient_citadels,
    MAP_MODES[8]: _render_prison_fortresses,
    MAP_MODES[9]: _render_underground_forts,
}


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
def render_fortress_maps_tab():
    """Main entry point -- called from app.py inside a tab context."""
    st.markdown(
        '<div class="tab-header amber"><h4>\U0001f3f0 Fortresses & Castles Maps</h4>'
        "<p>Medieval castles, fortifications, and defensive structures worldwide</p></div>",
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Map Mode", MAP_MODES, key="fortress_maps_mode")
    st.markdown("---")
    renderer = _RENDERERS.get(mode)
    if renderer:
        renderer()
    else:
        st.warning("Map mode not found.")
