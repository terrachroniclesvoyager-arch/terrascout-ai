# -*- coding: utf-8 -*-
"""
Ancient Weapons & Armor Maps module for TerraScout AI.
Provides 10 interactive map modes covering katana forges, European swords,
Damascus steel, medieval armor, battlefields, museums, Viking weapons,
Asian weapons heritage, gunpowder origins, and siege warfare sites.
All data is hardcoded -- no API keys required.
"""

import io
import html as html_module
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

# ===================================================================
# COLOUR PALETTE (dark theme)
# ===================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_ACCENT = "#06b6d4"
_MUTED = "#5a6580"

# ===================================================================
# MAP MODE LIST
# ===================================================================
MAP_MODES = [
    "Japanese Katana Forges",
    "European Sword Making Centers",
    "Damascus Steel Origins",
    "Medieval Armor Workshops",
    "Famous Ancient Battlefields",
    "Weapons & Armor Museums",
    "Viking Weapon Finds",
    "Chinese & Asian Weapons Heritage",
    "Gunpowder & Firearms Origins",
    "Ancient Siege Warfare Sites",
]

# ===================================================================
# 1. JAPANESE KATANA FORGES (30 entries)
# ===================================================================
KATANA_FORGES = [
    {"name": "Seki City Swordsmith Museum", "lat": 35.4953, "lon": 136.9178, "region": "Gifu", "era": "Kamakura-present", "tradition": "Mino", "notes": "Capital of Japanese bladesmithing since 13th century; 300+ swordsmiths at peak"},
    {"name": "Bizen Osafune Sword Museum", "lat": 34.7361, "lon": 134.1833, "region": "Okayama", "era": "Kamakura-Muromachi", "tradition": "Bizen", "notes": "Bizen school produced more swords than any other; famed for choji hamon patterns"},
    {"name": "Sagano Bamboo Grove Forges", "lat": 35.0173, "lon": 135.6726, "region": "Kyoto", "era": "Heian-Edo", "tradition": "Yamashiro", "notes": "Yamashiro tradition centered in Kyoto; elegant and refined blades for nobility"},
    {"name": "Sakai Traditional Knife Museum", "lat": 34.5731, "lon": 135.4831, "region": "Osaka", "era": "Muromachi-present", "tradition": "Sakai", "notes": "Sakai bladesmiths transitioned from swords to kitchen knives; 90% of Japanese pro knives"},
    {"name": "Nikko Toshogu Shrine Forge Site", "lat": 36.7581, "lon": 139.5994, "region": "Tochigi", "era": "Edo", "tradition": "Mino", "notes": "Tokugawa shrine swordsmiths crafted ceremonial blades for shogunate rituals"},
    {"name": "Atsuta Shrine Sword Treasury", "lat": 35.1275, "lon": 136.9089, "region": "Nagoya", "era": "Ancient", "tradition": "Imperial", "notes": "Houses Kusanagi no Tsurugi, one of three Imperial Regalia of Japan"},
    {"name": "Echizen Forge District", "lat": 35.9057, "lon": 136.1651, "region": "Fukui", "era": "Nanbokucho-Edo", "tradition": "Echizen", "notes": "Echizen swordsmiths famed for robust tachi blades; later pivoted to knives and sickles"},
    {"name": "Hizen Forge District", "lat": 33.2494, "lon": 130.3008, "region": "Saga", "era": "Edo", "tradition": "Hizen", "notes": "Tadayoshi lineage produced refined blades for Nabeshima clan; distinctive suguha hamon"},
    {"name": "Sendai Kunikane Workshop", "lat": 38.2682, "lon": 140.8694, "region": "Miyagi", "era": "Edo", "tradition": "Sendai", "notes": "Date clan swordsmiths; Kunikane line produced blades for samurai of Sendai domain"},
    {"name": "Satsuma Forge District", "lat": 31.5969, "lon": 130.5571, "region": "Kagoshima", "era": "Kamakura-Edo", "tradition": "Satsuma", "notes": "Satsuma samurai prized heavy, practical blades; strong influence on Meiji Restoration"},
    {"name": "Aizu Wakamatsu Forge", "lat": 37.4947, "lon": 139.9297, "region": "Fukushima", "era": "Edo", "tradition": "Aizu", "notes": "Aizu domain swordsmiths; Kanesada line known for durable battlefield blades"},
    {"name": "Yamato Province Forge Site", "lat": 34.6851, "lon": 135.8048, "region": "Nara", "era": "Heian-Kamakura", "tradition": "Yamato", "notes": "One of five main traditions (gokaden); temple-linked smiths produced austere, functional blades"},
    {"name": "Soshu Kamakura Forge Site", "lat": 35.3192, "lon": 139.5467, "region": "Kanagawa", "era": "Kamakura", "tradition": "Soshu", "notes": "Masamune's tradition; created nie-based hamon; considered pinnacle of Japanese swordmaking"},
    {"name": "Ise Shrine Forge Complex", "lat": 34.4551, "lon": 136.7260, "region": "Mie", "era": "Ancient-present", "tradition": "Ise", "notes": "Sacred forging rituals for Shinto ceremonial swords; rebuilt every 20 years"},
    {"name": "Tosa Forge District", "lat": 33.5597, "lon": 133.5311, "region": "Kochi", "era": "Muromachi-Edo", "tradition": "Tosa", "notes": "Tosa blades known for rugged outdoor knives; Sakamoto Ryoma carried Tosa blade"},
    {"name": "Morioka Nanbu Forge", "lat": 39.7036, "lon": 141.1527, "region": "Iwate", "era": "Edo", "tradition": "Nanbu", "notes": "Nanbu clan swordsmiths also famous for ironware; cold-climate forging techniques"},
    {"name": "Izumo Forge Site", "lat": 35.4017, "lon": 132.6853, "region": "Shimane", "era": "Ancient-Heian", "tradition": "Izumo", "notes": "Mythological origin of Japanese swordmaking; tatara iron smelting tradition"},
    {"name": "Tanba Forge District", "lat": 35.1750, "lon": 135.2500, "region": "Hyogo", "era": "Kamakura-Muromachi", "tradition": "Tanba", "notes": "Minor tradition producing utilitarian blades for local warriors and farmers"},
    {"name": "Kuwana Muramasa Workshop", "lat": 35.0623, "lon": 136.6841, "region": "Mie", "era": "Muromachi", "tradition": "Ise/Mino", "notes": "Muramasa blades legendary as cursed swords; feared by Tokugawa clan"},
    {"name": "Shimane Tatara Ironworks", "lat": 35.1833, "lon": 132.8833, "region": "Shimane", "era": "Ancient-Meiji", "tradition": "Tatara", "notes": "Traditional Japanese iron smelting; produced tamahagane steel for sword forging"},
    {"name": "Gassan Forge", "lat": 38.3167, "lon": 140.0167, "region": "Yamagata", "era": "Kamakura-present", "tradition": "Gassan", "notes": "Famous for ayasugi-hada (wavy wood grain) pattern; revived in modern era"},
    {"name": "Nagasone Kotetsu Workshop Site", "lat": 35.7141, "lon": 139.7775, "region": "Tokyo (Edo)", "era": "Early Edo", "tradition": "Edo", "notes": "Kotetsu blades among most prized in shinto period; famed cutting tests"},
    {"name": "Bitchu Forge District", "lat": 34.7833, "lon": 133.6167, "region": "Okayama", "era": "Kamakura-Muromachi", "tradition": "Bitchu", "notes": "Aoe school produced distinctive blades; absorbed into Bizen tradition"},
    {"name": "Chikuzen Forge District", "lat": 33.5903, "lon": 130.4017, "region": "Fukuoka", "era": "Kamakura-Muromachi", "tradition": "Chikuzen", "notes": "Sa school swordsmiths influenced by Southern Chinese techniques"},
    {"name": "Kaga Forge District", "lat": 36.5783, "lon": 136.6486, "region": "Ishikawa", "era": "Edo", "tradition": "Kaga", "notes": "Maeda clan patronized skilled swordsmiths; ornate mountings and fittings"},
    {"name": "Tsuruga Forge Site", "lat": 35.6453, "lon": 136.0556, "region": "Fukui", "era": "Muromachi", "tradition": "Echizen", "notes": "Port city forge supplied blades for trade and naval forces"},
    {"name": "Bungo Forge District", "lat": 33.2333, "lon": 131.6000, "region": "Oita", "era": "Kamakura-Muromachi", "tradition": "Bungo", "notes": "Yukihira line known for distinctive forging; regional warrior traditions"},
    {"name": "Suruga Bay Forge Site", "lat": 34.9756, "lon": 138.3828, "region": "Shizuoka", "era": "Muromachi-Edo", "tradition": "Suruga", "notes": "Imagawa and Tokugawa domain swordsmiths; strategic Tokaido road location"},
    {"name": "Hitachi Forge District", "lat": 36.3917, "lon": 140.4467, "region": "Ibaraki", "era": "Kamakura-Edo", "tradition": "Hitachi", "notes": "Ancient ironworking region; supplied blades to eastern warrior bands"},
    {"name": "Yoshino Forge Site", "lat": 34.3833, "lon": 135.8667, "region": "Nara", "era": "Nanbokucho", "tradition": "Yamato", "notes": "Southern Court swordsmiths forged blades during imperial civil war period"},
]

# ===================================================================
# 2. EUROPEAN SWORD MAKING CENTERS (30 entries)
# ===================================================================
EUROPEAN_SWORDS = [
    {"name": "Toledo Sword Workshops", "lat": 39.8628, "lon": -4.0273, "country": "Spain", "era": "Roman-present", "specialty": "Espada ropera / Toledo steel", "notes": "2000+ years of bladesmithing; Roman gladius to Renaissance rapiers; legendary Toledo steel"},
    {"name": "Solingen Blade District", "lat": 51.1653, "lon": 7.0834, "country": "Germany", "era": "Medieval-present", "specialty": "All edged weapons", "notes": "City of Blades since Middle Ages; rival to Toledo; still global cutlery capital"},
    {"name": "Brescia Armory Quarter", "lat": 45.5416, "lon": 10.2118, "country": "Italy", "era": "Renaissance", "specialty": "Swords and firearms", "notes": "Major arms production center; supplied Venetian Republic armies"},
    {"name": "Passau Wolf Workshops", "lat": 48.5748, "lon": 13.4631, "country": "Germany", "era": "Medieval", "specialty": "Passau Wolf mark blades", "notes": "Running wolf mark became most counterfeited blade stamp in medieval Europe"},
    {"name": "Thiers Cutlery District", "lat": 45.8574, "lon": 3.5486, "country": "France", "era": "15th century-present", "specialty": "Knives and swords", "notes": "French capital of cutlery; Laguiole and Opinel traditions originate nearby"},
    {"name": "Sheffield Steel Works", "lat": 53.3811, "lon": -1.4701, "country": "England", "era": "14th century-present", "specialty": "Crucible steel blades", "notes": "Crucible steel revolution; Benjamin Huntsman's process transformed European bladesmithing"},
    {"name": "Augsburg Blade Workshops", "lat": 48.3705, "lon": 10.8978, "country": "Germany", "era": "Renaissance", "specialty": "Decorated swords", "notes": "Renowned for ornate ceremonial swords; Fugger family patronage of arms trade"},
    {"name": "Milan Armorer Guild", "lat": 45.4642, "lon": 9.1900, "country": "Italy", "era": "Medieval-Renaissance", "specialty": "Milanese swords and armor", "notes": "Missaglia family workshop among finest in Europe; armed knights across continent"},
    {"name": "Nuremberg Arms Market", "lat": 49.4521, "lon": 11.0767, "country": "Germany", "era": "Medieval-Renaissance", "specialty": "Trade swords", "notes": "Major arms trading hub; strict quality marks and guild regulations"},
    {"name": "Bordeaux Sword District", "lat": 44.8378, "lon": -0.5792, "country": "France", "era": "Medieval", "specialty": "Gascon blades", "notes": "Armed Gascon mercenaries and Hundred Years War combatants"},
    {"name": "Bilbao Basque Forges", "lat": 43.2630, "lon": -2.9350, "country": "Spain", "era": "Medieval-Renaissance", "specialty": "Basque iron blades", "notes": "Rich iron deposits fueled Basque bladesmithing; exported across Atlantic"},
    {"name": "Zlatoust Arms Factory", "lat": 55.1713, "lon": 59.6508, "country": "Russia", "era": "1815-present", "specialty": "Decorated blades", "notes": "Imperial Russian state arms factory; famed for engraved and gilded presentation swords"},
    {"name": "Klingenthal Manufacture", "lat": 48.3667, "lon": 7.3333, "country": "France", "era": "1730-present", "specialty": "Military swords", "notes": "French royal then state sword factory in Alsace; supplied Napoleonic armies"},
    {"name": "Wilkinson Sword London", "lat": 51.4816, "lon": -0.1922, "country": "England", "era": "1772-present", "specialty": "Military swords", "notes": "Official supplier of British military swords; every VC sword made here"},
    {"name": "Eibar Arms District", "lat": 43.1847, "lon": -2.4722, "country": "Spain", "era": "16th century-present", "specialty": "Firearms and blades", "notes": "Basque arms capital; Royal Arms Factory; supplied Spanish Empire"},
    {"name": "Belluno Forge Valley", "lat": 46.1425, "lon": 12.2167, "country": "Italy", "era": "Medieval", "specialty": "Alpine blades", "notes": "Mountain forges used hydropower for bellows and hammers; armed Venetian troops"},
    {"name": "Styria Iron Road", "lat": 47.3833, "lon": 14.8000, "country": "Austria", "era": "Medieval-present", "specialty": "Styrian steel blades", "notes": "Erzberg iron mountain supplied raw material; Styrian steel renowned across Europe"},
    {"name": "Suhl Arms Town", "lat": 50.6081, "lon": 10.6930, "country": "Germany", "era": "16th century-present", "specialty": "Firearms and blades", "notes": "Thuringian Forest arms center; supplied weapons to multiple European conflicts"},
    {"name": "Prague Castle Armory", "lat": 50.0909, "lon": 14.4003, "country": "Czech Republic", "era": "Medieval-Renaissance", "specialty": "Bohemian blades", "notes": "Bohemian crown armory; skilled Czech smiths served Holy Roman Emperors"},
    {"name": "Landsknecht Blade Workshops Innsbruck", "lat": 47.2692, "lon": 11.4041, "country": "Austria", "era": "Renaissance", "specialty": "Zweihander / Katzbalger", "notes": "Armed the feared Landsknecht mercenaries; massive two-handed swords"},
    {"name": "Liege Arms Quarter", "lat": 50.6292, "lon": 5.5736, "country": "Belgium", "era": "14th century-present", "specialty": "Firearms and edged weapons", "notes": "Major European arms center; FN Herstal origins; Proof House since 1672"},
    {"name": "Birmingham Gun Quarter", "lat": 52.4862, "lon": -1.8904, "country": "England", "era": "17th century-present", "specialty": "Blades and firearms", "notes": "Mass production of military blades; armed British Empire campaigns"},
    {"name": "Tula Arms Plant", "lat": 54.1961, "lon": 37.6182, "country": "Russia", "era": "1712-present", "specialty": "Military weapons", "notes": "Founded by Peter the Great; produced swords, muskets; still active defense plant"},
    {"name": "Sardinian Pattada Workshops", "lat": 40.5667, "lon": 9.1167, "country": "Italy", "era": "18th century-present", "specialty": "Resolza folding knives", "notes": "Traditional Sardinian knife-making; myrtle-leaf blade shape; pastoral heritage"},
    {"name": "Albacete Knife District", "lat": 38.9943, "lon": -1.8585, "country": "Spain", "era": "15th century-present", "specialty": "Navajas / folding knives", "notes": "Spanish navaja capital; ornate folding knives with Moorish-influenced designs"},
    {"name": "Mora Knife Workshops", "lat": 61.0050, "lon": 14.5450, "country": "Sweden", "era": "17th century-present", "specialty": "Scandinavian knives", "notes": "Morakniv tradition since 1600s; every household produced knives as cottage industry"},
    {"name": "Kauhava Puukko District", "lat": 63.1000, "lon": 23.0667, "country": "Finland", "era": "18th century-present", "specialty": "Puukko knives", "notes": "Finnish national knife; Ostrobothnian tradition; military and survival use"},
    {"name": "Frosolone Blade Town", "lat": 41.6000, "lon": 14.4500, "country": "Italy", "era": "14th century-present", "specialty": "Scissors and knives", "notes": "Molise mountain blade town; 50+ workshops in village of 3000; living museum"},
    {"name": "Maniago Knife District", "lat": 46.1667, "lon": 12.7167, "country": "Italy", "era": "15th century-present", "specialty": "Knives and blades", "notes": "Friulian blade center; guild records from 1453; industrial knife production"},
    {"name": "Nogent Cutlery Basin", "lat": 48.1833, "lon": 4.7333, "country": "France", "era": "16th century-present", "specialty": "Cutlery and surgical blades", "notes": "Champagne region cutlery; supplied surgical instruments and table knives"},
]

# ===================================================================
# 3. DAMASCUS STEEL ORIGINS (25 entries)
# ===================================================================
DAMASCUS_STEEL = [
    {"name": "Damascus Historic Souks", "lat": 33.5138, "lon": 36.3066, "country": "Syria", "era": "Ancient-Medieval", "type": "Trade hub", "notes": "Namesake city of Damascus steel; major trade center for wootz steel blades from India"},
    {"name": "Hyderabad Wootz Forges", "lat": 17.3850, "lon": 78.4867, "country": "India", "era": "300 BC-1700s", "type": "Production center", "notes": "Deccan plateau crucible steel production; primary source of wootz ingots"},
    {"name": "Kodumanal Ancient Forge", "lat": 11.0167, "lon": 77.8833, "country": "India", "era": "3rd century BC", "type": "Archaeological site", "notes": "Tamil Nadu crucible steel workshop; earliest archaeological evidence of wootz production"},
    {"name": "Merv Oasis Forge", "lat": 37.6625, "lon": 62.1700, "country": "Turkmenistan", "era": "Medieval", "type": "Production center", "notes": "Silk Road oasis; crucible steel workshops discovered by archaeologists"},
    {"name": "Isfahan Blade Bazaar", "lat": 32.6546, "lon": 51.6680, "country": "Iran", "era": "Safavid", "type": "Trade/production", "notes": "Persian blade center; shamshir curved swords with damascus steel blades"},
    {"name": "Bukhara Silk Road Forge", "lat": 39.7747, "lon": 64.4286, "country": "Uzbekistan", "era": "Medieval", "type": "Trade hub", "notes": "Central Asian trade node for Damascus steel; Timurid patronage of bladesmiths"},
    {"name": "Aleppo Arms Souk", "lat": 36.1997, "lon": 37.1628, "country": "Syria", "era": "Medieval", "type": "Trade hub", "notes": "Major arms market; Crusaders first encountered Damascus steel blades here"},
    {"name": "Jaipur Royal Armory", "lat": 26.9124, "lon": 75.7873, "country": "India", "era": "16th-18th century", "type": "Royal workshop", "notes": "Rajput royal workshops produced finest wootz steel tulwars and katar daggers"},
    {"name": "Mosul Forge District", "lat": 36.3350, "lon": 43.1189, "country": "Iraq", "era": "Medieval", "type": "Production center", "notes": "Northern Mesopotamian blade center; Mosul steel referenced in medieval texts"},
    {"name": "Cairo Citadel Armory", "lat": 30.0288, "lon": 31.2609, "country": "Egypt", "era": "Mamluk", "type": "State armory", "notes": "Mamluk sultanate armory; Damascus steel weapons for elite warrior caste"},
    {"name": "Golconda Fort Forge", "lat": 17.3833, "lon": 78.4011, "country": "India", "era": "14th-17th century", "type": "Production center", "notes": "Deccan sultanate wootz center; diamonds and steel were twin exports"},
    {"name": "Samarkand Timurid Workshops", "lat": 39.6542, "lon": 66.9597, "country": "Uzbekistan", "era": "Timurid", "type": "Royal workshop", "notes": "Tamerlane's capital; captured bladesmiths from Damascus brought here in 1401"},
    {"name": "Herat Timurid Forge", "lat": 34.3529, "lon": 62.2040, "country": "Afghanistan", "era": "Timurid-Mughal", "type": "Production center", "notes": "Afghan blade center; supplied wootz weapons along Silk Road trade routes"},
    {"name": "Lahore Mughal Armory", "lat": 31.5204, "lon": 74.3587, "country": "Pakistan", "era": "Mughal", "type": "Royal workshop", "notes": "Mughal imperial armory; finest damascus steel weapons for emperor's guard"},
    {"name": "Sri Lanka Ancient Ironworks", "lat": 7.9519, "lon": 80.7514, "country": "Sri Lanka", "era": "Ancient", "type": "Production center", "notes": "Wind-powered furnaces; monsoon-driven smelting produced high-carbon steel"},
    {"name": "Constantinople Imperial Armory", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "era": "Byzantine-Ottoman", "type": "State armory", "notes": "Topkapi Palace armory holds finest collection of Damascus steel weapons"},
    {"name": "Khorasan Forge Region", "lat": 36.3000, "lon": 59.6000, "country": "Iran", "era": "Medieval", "type": "Production center", "notes": "Persian Khorasan produced distinctive patterned steel; referenced by al-Biruni"},
    {"name": "Thanjavur Arms Workshop", "lat": 10.7870, "lon": 79.1378, "country": "India", "era": "Chola-Nayak", "type": "Production center", "notes": "South Indian wootz production; Chola dynasty warriors used crucible steel blades"},
    {"name": "Shiraz Blade Market", "lat": 29.5918, "lon": 52.5837, "country": "Iran", "era": "Zand-Qajar", "type": "Trade center", "notes": "Persian blade trading center; Zand dynasty patronized decorated damascus blades"},
    {"name": "Tbilisi Georgian Forges", "lat": 41.7151, "lon": 44.8271, "country": "Georgia", "era": "Medieval", "type": "Production center", "notes": "Caucasus iron tradition; Georgian swords combined local and Persian techniques"},
    {"name": "Nishapur Forge Site", "lat": 36.2132, "lon": 58.7961, "country": "Iran", "era": "Medieval", "type": "Archaeological site", "notes": "Major Khorasan city; crucible steel fragments found in archaeological excavations"},
    {"name": "Bursa Ottoman Forge", "lat": 40.1828, "lon": 29.0661, "country": "Turkey", "era": "Early Ottoman", "type": "Production center", "notes": "First Ottoman capital; early Ottoman yatagan and kilij swords forged here"},
    {"name": "Gwalior Fort Armory", "lat": 26.2183, "lon": 78.1828, "country": "India", "era": "Medieval-Mughal", "type": "Fort armory", "notes": "Hilltop fortress armory; stored thousands of wootz steel weapons"},
    {"name": "Konya Seljuk Workshops", "lat": 37.8746, "lon": 32.4932, "country": "Turkey", "era": "Seljuk", "type": "Royal workshop", "notes": "Seljuk sultanate capital; court bladesmiths produced ceremonial damascus swords"},
    {"name": "Balkh Ancient Forge", "lat": 36.7583, "lon": 66.8975, "country": "Afghanistan", "era": "Ancient-Medieval", "type": "Archaeological site", "notes": "Mother of Cities; ancient ironworking predating Islamic conquest; Silk Road node"},
]

# ===================================================================
# 4. MEDIEVAL ARMOR WORKSHOPS (30 entries)
# ===================================================================
ARMOR_WORKSHOPS = [
    {"name": "Milan Missaglia Workshop", "lat": 45.4654, "lon": 9.1859, "country": "Italy", "era": "15th century", "specialty": "Full plate armor", "notes": "Missaglia family produced finest Italian plate armor; exported across Europe"},
    {"name": "Augsburg Helmschmied Workshop", "lat": 48.3657, "lon": 10.8945, "country": "Germany", "era": "15th-16th century", "specialty": "Maximilian armor", "notes": "Lorenz Helmschmied armored Emperor Maximilian I; distinctive fluted style"},
    {"name": "Innsbruck Court Armory", "lat": 47.2654, "lon": 11.3928, "country": "Austria", "era": "15th-16th century", "specialty": "Tournament armor", "notes": "Habsburg court armory; Konrad Seusenhofer created masterpiece tournament suits"},
    {"name": "Nuremberg Armorer Guild", "lat": 49.4521, "lon": 11.0767, "country": "Germany", "era": "14th-16th century", "specialty": "Gothic plate armor", "notes": "German Gothic armor style originated here; angular, fluted designs"},
    {"name": "Greenwich Royal Armory", "lat": 51.4769, "lon": 0.0005, "country": "England", "era": "1515-1649", "specialty": "English plate armor", "notes": "Henry VIII founded royal workshop; Greenwich style armor for English nobility"},
    {"name": "Brescia Armory District", "lat": 45.5394, "lon": 10.2106, "country": "Italy", "era": "15th-17th century", "specialty": "Swords and firearms", "notes": "Major Italian arms center; supplied Venetian Republic military"},
    {"name": "Landshut Armory", "lat": 48.5369, "lon": 12.1522, "country": "Germany", "era": "15th century", "specialty": "Bavarian plate armor", "notes": "Bavarian ducal armory; supplied armor for famous 1475 Landshut Wedding tournament"},
    {"name": "Cologne Armor Market", "lat": 50.9375, "lon": 6.9603, "country": "Germany", "era": "Medieval", "specialty": "Mail and plate", "notes": "Rhine trade hub for armor; guild of mail-makers (Sarwurter) prominent"},
    {"name": "Bordeaux Armory", "lat": 44.8378, "lon": -0.5792, "country": "France", "era": "14th-15th century", "specialty": "Gascon armor", "notes": "English-held Gascony produced armor for Hundred Years War campaigns"},
    {"name": "Burgos Spanish Armory", "lat": 42.3440, "lon": -3.6969, "country": "Spain", "era": "15th-16th century", "specialty": "Spanish morion helmets", "notes": "Castilian royal armory; armed Reconquista and New World conquistadors"},
    {"name": "Tours Royal Armory", "lat": 47.3941, "lon": 0.6848, "country": "France", "era": "15th century", "specialty": "French plate armor", "notes": "French royal workshop; armed knights for Italian Wars campaigns"},
    {"name": "Churburg Castle Armory", "lat": 46.6333, "lon": 10.7167, "country": "Italy (South Tyrol)", "era": "14th-16th century", "specialty": "Alpine armor collection", "notes": "Best-preserved medieval private armory; 50+ complete suits spanning 200 years"},
    {"name": "Pamplona Armory", "lat": 42.8125, "lon": -1.6458, "country": "Spain", "era": "Medieval", "specialty": "Navarrese armor", "notes": "Kingdom of Navarre armory; crossbow bolt-resistant designs for mountain warfare"},
    {"name": "Graz Styrian Armory", "lat": 47.0707, "lon": 15.4395, "country": "Austria", "era": "16th-17th century", "specialty": "Border defense armor", "notes": "Landeszeughaus holds 32,000 pieces; largest historic armory in the world"},
    {"name": "Lyon Armory Quarter", "lat": 45.7640, "lon": 4.8357, "country": "France", "era": "15th-16th century", "specialty": "French parade armor", "notes": "Silk and armor city; decorated ceremonial armor for French nobility"},
    {"name": "Bruges Flemish Workshops", "lat": 51.2093, "lon": 3.2247, "country": "Belgium", "era": "14th-15th century", "specialty": "Flemish armor", "notes": "Wealthy Burgundian court patronized luxury decorated armor"},
    {"name": "Praga Armory District", "lat": 50.0880, "lon": 14.4208, "country": "Czech Republic", "era": "15th-16th century", "specialty": "Hussite war armor", "notes": "Bohemian armorsmiths innovated during Hussite Wars; wagon fort equipment"},
    {"name": "Kremnica Mint & Armory", "lat": 48.7053, "lon": 18.9169, "country": "Slovakia", "era": "14th-16th century", "specialty": "Hungarian-style armor", "notes": "Mining town produced both coins and weapons; Slovak-Hungarian frontier defense"},
    {"name": "Venice Arsenal Armory", "lat": 45.4361, "lon": 12.3531, "country": "Italy", "era": "12th-18th century", "specialty": "Naval armor and weapons", "notes": "Largest industrial complex in pre-industrial Europe; armed Venetian fleet and army"},
    {"name": "Wroclaw Silesian Workshops", "lat": 51.1079, "lon": 17.0385, "country": "Poland", "era": "14th-16th century", "specialty": "Eastern European armor", "notes": "Silesian armorers blended German and Polish traditions; hussar wing racks"},
    {"name": "Saragossa Armory", "lat": 41.6488, "lon": -0.8891, "country": "Spain", "era": "15th century", "specialty": "Aragonese armor", "notes": "Crown of Aragon armory; Mediterranean-influenced lighter armor designs"},
    {"name": "Kremlin Armory Moscow", "lat": 55.7520, "lon": 37.6175, "country": "Russia", "era": "1511-present", "specialty": "Russian armor", "notes": "Tsarist state armory; now museum with finest Russian arms and armor collection"},
    {"name": "Arboga Armory", "lat": 59.3942, "lon": 15.8389, "country": "Sweden", "era": "16th-17th century", "specialty": "Swedish military armor", "notes": "Supplied Gustavus Adolphus armies; Swedish pike-and-shot equipment"},
    {"name": "Istanbul Tophane Arsenal", "lat": 41.0267, "lon": 28.9819, "country": "Turkey", "era": "Ottoman", "specialty": "Ottoman armor", "notes": "Ottoman imperial arsenal; mail-and-plate armor, mirror armor, sipahi equipment"},
    {"name": "Florence Stibbert Workshop", "lat": 43.7855, "lon": 11.2484, "country": "Italy", "era": "Renaissance", "specialty": "Etched parade armor", "notes": "Florentine Renaissance armorers; acid-etched decoration technique pioneers"},
    {"name": "Nagoya Castle Armory", "lat": 35.1856, "lon": 136.8994, "country": "Japan", "era": "Edo", "specialty": "Samurai armor (yoroi)", "notes": "Owari Tokugawa domain armory; lacquered plate and lamellar armor"},
    {"name": "Sialkot Arms Workshops", "lat": 32.4945, "lon": 74.5229, "country": "Pakistan", "era": "Mughal-present", "specialty": "Indo-Persian armor", "notes": "Historic arms center; four-mirror (char-aina) body armor production"},
    {"name": "Cairo Mamluk Arsenal", "lat": 30.0364, "lon": 31.2636, "country": "Egypt", "era": "Mamluk", "specialty": "Islamic armor", "notes": "Mamluk warriors wore mail-plate combos; Citadel workshops supplied elite cavalry"},
    {"name": "Stockholm Royal Armory", "lat": 59.3265, "lon": 18.0719, "country": "Sweden", "era": "16th century-present", "specialty": "Swedish royal armor", "notes": "Livrustkammaren is oldest museum in Sweden; royal armor since Gustav Vasa"},
    {"name": "Tower of London Armory", "lat": 51.5081, "lon": -0.0759, "country": "England", "era": "Medieval-present", "specialty": "English royal armor", "notes": "Royal Armouries national collection; Henry VIII armor suits on display"},
]

# ===================================================================
# 5. FAMOUS ANCIENT BATTLEFIELDS (30 entries)
# ===================================================================
BATTLEFIELDS = [
    {"name": "Thermopylae", "lat": 38.7967, "lon": 22.5367, "country": "Greece", "year": "480 BC", "combatants": "Greeks vs Persians", "notes": "300 Spartans under Leonidas held the pass against Xerxes' massive Persian army"},
    {"name": "Marathon", "lat": 38.1536, "lon": 23.9636, "country": "Greece", "year": "490 BC", "combatants": "Athens vs Persia", "notes": "Athenian hoplites defeated Persian invasion force; Pheidippides' legendary run"},
    {"name": "Gaugamela", "lat": 36.5750, "lon": 43.4500, "country": "Iraq", "year": "331 BC", "combatants": "Macedonia vs Persia", "notes": "Alexander the Great decisively defeated Darius III; ended the Persian Empire"},
    {"name": "Cannae", "lat": 41.3050, "lon": 16.1328, "country": "Italy", "year": "216 BC", "combatants": "Carthage vs Rome", "notes": "Hannibal's double envelopment destroyed 8 Roman legions; textbook tactical masterpiece"},
    {"name": "Alesia", "lat": 47.5364, "lon": 4.5028, "country": "France", "year": "52 BC", "combatants": "Rome vs Gauls", "notes": "Caesar besieged Vercingetorix with double ring of fortifications; ended Gallic resistance"},
    {"name": "Teutoburg Forest", "lat": 52.4050, "lon": 8.1300, "country": "Germany", "year": "9 AD", "combatants": "Germanic tribes vs Rome", "notes": "Arminius ambushed and destroyed 3 Roman legions; halted Roman expansion into Germania"},
    {"name": "Masada", "lat": 31.3156, "lon": 35.3536, "country": "Israel", "year": "73 AD", "combatants": "Jewish Zealots vs Rome", "notes": "Roman siege ramp assault on desert fortress; mass suicide of defenders"},
    {"name": "Adrianople", "lat": 41.6772, "lon": 26.5558, "country": "Turkey", "year": "378 AD", "combatants": "Goths vs Rome", "notes": "Gothic cavalry destroyed Roman army; Emperor Valens killed; marked decline of Roman infantry"},
    {"name": "Tours/Poitiers", "lat": 46.5802, "lon": 0.3404, "country": "France", "year": "732 AD", "combatants": "Franks vs Umayyads", "notes": "Charles Martel halted Muslim advance into Western Europe; pivotal moment in European history"},
    {"name": "Hastings", "lat": 50.9103, "lon": 0.4872, "country": "England", "year": "1066", "combatants": "Normans vs Anglo-Saxons", "notes": "William the Conqueror defeated Harold II; Norman conquest transformed England forever"},
    {"name": "Hattin", "lat": 32.8167, "lon": 35.4833, "country": "Israel", "year": "1187", "combatants": "Ayyubids vs Crusaders", "notes": "Saladin annihilated Crusader army; led to fall of Jerusalem; triggered Third Crusade"},
    {"name": "Crecy", "lat": 50.2544, "lon": 1.8889, "country": "France", "year": "1346", "combatants": "England vs France", "notes": "English longbowmen decimated French knights; revolutionized medieval warfare"},
    {"name": "Agincourt", "lat": 50.4633, "lon": 2.1406, "country": "France", "year": "1415", "combatants": "England vs France", "notes": "Henry V's outnumbered army destroyed French cavalry with longbow volleys in mud"},
    {"name": "Constantinople Fall", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "year": "1453", "combatants": "Ottomans vs Byzantines", "notes": "Mehmed II breached Theodosian Walls with cannons; ended Byzantine Empire after 1100 years"},
    {"name": "Bannockburn", "lat": 56.0875, "lon": -3.9139, "country": "Scotland", "year": "1314", "combatants": "Scotland vs England", "notes": "Robert the Bruce defeated Edward II; secured Scottish independence for generations"},
    {"name": "Lepanto", "lat": 38.3992, "lon": 21.7994, "country": "Greece", "year": "1571", "combatants": "Holy League vs Ottomans", "notes": "Last great galley battle; Christian coalition broke Ottoman naval dominance"},
    {"name": "Issus", "lat": 36.8500, "lon": 36.1667, "country": "Turkey", "year": "333 BC", "combatants": "Macedonia vs Persia", "notes": "Alexander defeated Darius III in narrow coastal plain; Persian royal family captured"},
    {"name": "Zama", "lat": 36.3000, "lon": 8.5500, "country": "Tunisia", "year": "202 BC", "combatants": "Rome vs Carthage", "notes": "Scipio Africanus defeated Hannibal; ended Second Punic War; Rome dominated Mediterranean"},
    {"name": "Plataea", "lat": 38.2167, "lon": 23.2833, "country": "Greece", "year": "479 BC", "combatants": "Greeks vs Persians", "notes": "Greek coalition crushed Persian army; ended Xerxes' invasion of Greece"},
    {"name": "Red Cliffs", "lat": 29.8500, "lon": 113.6833, "country": "China", "year": "208 AD", "combatants": "Sun-Liu vs Cao Cao", "notes": "Fire ships destroyed Cao Cao's fleet; divided China into Three Kingdoms"},
    {"name": "Manzikert", "lat": 39.1431, "lon": 43.4833, "country": "Turkey", "year": "1071", "combatants": "Seljuks vs Byzantines", "notes": "Seljuk Turks captured Emperor Romanos IV; opened Anatolia to Turkish settlement"},
    {"name": "Kalka River", "lat": 47.2667, "lon": 37.3000, "country": "Ukraine", "year": "1223", "combatants": "Mongols vs Rus-Cuman", "notes": "Mongol reconnaissance force crushed Kievan Rus princes; prelude to Mongol invasion"},
    {"name": "Towton", "lat": 53.8539, "lon": -1.2994, "country": "England", "year": "1461", "combatants": "York vs Lancaster", "notes": "Bloodiest battle on English soil; 28,000+ casualties in snowstorm; Wars of the Roses"},
    {"name": "Mohi", "lat": 47.9833, "lon": 20.9833, "country": "Hungary", "year": "1241", "combatants": "Mongols vs Hungary", "notes": "Batu Khan destroyed Hungarian army; Mongol invasion devastated Kingdom of Hungary"},
    {"name": "Sekigahara", "lat": 35.3650, "lon": 136.4600, "country": "Japan", "year": "1600", "combatants": "Tokugawa vs Western Army", "notes": "Tokugawa Ieyasu's victory unified Japan; began 260 years of Tokugawa shogunate"},
    {"name": "Ankara", "lat": 39.8833, "lon": 32.7333, "country": "Turkey", "year": "1402", "combatants": "Timurids vs Ottomans", "notes": "Tamerlane defeated and captured Sultan Bayezid I; delayed Ottoman expansion by decades"},
    {"name": "Leuctra", "lat": 38.3667, "lon": 23.1500, "country": "Greece", "year": "371 BC", "combatants": "Thebes vs Sparta", "notes": "Epaminondas' oblique order shattered Spartan army; ended Spartan military dominance"},
    {"name": "Carrhae", "lat": 36.8667, "lon": 39.0333, "country": "Turkey", "year": "53 BC", "combatants": "Parthia vs Rome", "notes": "Parthian horse archers annihilated Crassus' legions; worst Roman defeat in the East"},
    {"name": "Ain Jalut", "lat": 32.5550, "lon": 35.3475, "country": "Israel", "year": "1260", "combatants": "Mamluks vs Mongols", "notes": "First major Mongol defeat; Mamluks stopped Mongol expansion into Africa"},
    {"name": "Salamis", "lat": 37.9500, "lon": 23.5000, "country": "Greece", "year": "480 BC", "combatants": "Greeks vs Persians", "notes": "Greek triremes destroyed Persian fleet in narrow strait; Themistocles' brilliant strategy"},
    {"name": "Nagashino", "lat": 34.9500, "lon": 137.5667, "country": "Japan", "year": "1575", "combatants": "Oda-Tokugawa vs Takeda", "notes": "Oda Nobunaga's 3000 arquebusiers in rotating volleys destroyed Takeda cavalry charge"},
    {"name": "Panipat (First)", "lat": 29.3900, "lon": 76.9700, "country": "India", "year": "1526", "combatants": "Mughals vs Delhi Sultanate", "notes": "Babur's cannon and matchlocks defeated Ibrahim Lodi; founded Mughal Empire in India"},
    {"name": "Tenochtitlan", "lat": 19.4326, "lon": -99.1332, "country": "Mexico", "year": "1521", "combatants": "Spanish-Tlaxcalan vs Aztec", "notes": "Cortes besieged Aztec island capital with brigantines; smallpox and starvation forced surrender"},
    {"name": "Grunwald (Tannenberg)", "lat": 53.4833, "lon": 20.1000, "country": "Poland", "year": "1410", "combatants": "Poland-Lithuania vs Teutonic Order", "notes": "Largest medieval European battle; Polish-Lithuanian victory broke Teutonic Knights' power"},
    {"name": "Watling Street", "lat": 52.4500, "lon": -1.0833, "country": "England", "year": "61 AD", "combatants": "Rome vs Iceni", "notes": "Suetonius Paulinus defeated Boudicca's massive Celtic rebellion with disciplined legions"},
    {"name": "Kadesh", "lat": 34.5667, "lon": 36.5167, "country": "Syria", "year": "1274 BC", "combatants": "Egypt vs Hittites", "notes": "Ramesses II vs Muwatalli II; largest chariot battle in history; earliest known peace treaty"},
    {"name": "Chalons (Catalaunian Plains)", "lat": 48.9500, "lon": 4.3500, "country": "France", "year": "451 AD", "combatants": "Romans-Visigoths vs Huns", "notes": "Aetius and Theodoric halted Attila the Hun; saved Western Europe from Hunnic conquest"},
    {"name": "Bosworth Field", "lat": 52.6078, "lon": -1.3975, "country": "England", "year": "1485", "combatants": "Lancaster vs York", "notes": "Henry Tudor defeated Richard III; last English king killed in battle; ended Wars of Roses"},
    {"name": "Pydna", "lat": 40.3667, "lon": 22.5333, "country": "Greece", "year": "168 BC", "combatants": "Rome vs Macedonia", "notes": "Roman legions defeated Macedonian phalanx; proved flexibility beat rigid formation"},
]

# ===================================================================
# 6. WEAPONS & ARMOR MUSEUMS (30 entries)
# ===================================================================
MUSEUMS = [
    {"name": "Royal Armouries, Leeds", "lat": 53.7920, "lon": -1.5318, "country": "England", "collection": "100,000+ objects", "highlights": "Henry VIII armor, elephant armor, Oriental arms", "notes": "UK national collection of arms and armor; free admission; three sites"},
    {"name": "Metropolitan Museum Arms & Armor", "lat": 40.7794, "lon": -73.9632, "country": "USA", "collection": "14,000+ objects", "highlights": "Jousting armor, Japanese samurai suits, Islamic arms", "notes": "World-class collection spanning 5 continents; iconic mounted knight display"},
    {"name": "Wallace Collection", "lat": 51.5175, "lon": -1.5179, "country": "England", "collection": "2,500+ objects", "highlights": "European and Oriental arms", "notes": "One of finest arms collections in world; housed in Hertford House mansion"},
    {"name": "Musee de l'Armee Paris", "lat": 48.8550, "lon": 2.3125, "country": "France", "collection": "500,000+ objects", "highlights": "Napoleon's sword, medieval armor hall", "notes": "Les Invalides military museum; covers French military history from antiquity"},
    {"name": "Kunsthistorisches Museum Vienna", "lat": 48.2036, "lon": 16.3614, "country": "Austria", "collection": "Extensive", "highlights": "Habsburg tournament armor, ceremonial weapons", "notes": "Imperial collections include some of finest Renaissance armor in existence"},
    {"name": "Deutsches Historisches Museum Berlin", "lat": 52.5186, "lon": 13.3964, "country": "Germany", "collection": "Extensive", "highlights": "Medieval to modern German arms", "notes": "German history museum in former Zeughaus (arsenal); comprehensive arms displays"},
    {"name": "Stibbert Museum Florence", "lat": 43.7855, "lon": 11.2484, "country": "Italy", "collection": "16,000+ objects", "highlights": "Cavalcade of mounted knights, Japanese armor", "notes": "Frederick Stibbert's personal collection; hall of mounted warriors is spectacular"},
    {"name": "Tower of London Royal Armouries", "lat": 51.5081, "lon": -0.0759, "country": "England", "collection": "Extensive", "highlights": "Line of Kings, Henry VIII armor", "notes": "Oldest museum display in world (1660); Crown Jewels and historic royal armor"},
    {"name": "Graz Landeszeughaus", "lat": 47.0707, "lon": 15.4395, "country": "Austria", "collection": "32,000 objects", "highlights": "Complete 17th-century armory", "notes": "Largest historic armory in world; entire building filled floor to ceiling with weapons"},
    {"name": "Topkapi Palace Armory Istanbul", "lat": 41.0115, "lon": 28.9833, "country": "Turkey", "collection": "52,000+ objects", "highlights": "Ottoman imperial weapons, Sword of Muhammad", "notes": "Ottoman sultan's collection; finest Islamic arms and armor in existence"},
    {"name": "Kremlin Armory Museum Moscow", "lat": 55.7520, "lon": 37.6175, "country": "Russia", "collection": "4,000+ objects", "highlights": "Tsarist ceremonial arms, Persian gifts", "notes": "Oldest museum in Moscow; Russian state regalia and diplomatic weapons gifts"},
    {"name": "Museo Stibbert Florence", "lat": 43.7855, "lon": 11.2484, "country": "Italy", "collection": "16,000+", "highlights": "Japanese and European armor cavalcade", "notes": "Anglo-Italian collector's stunning private museum of world arms"},
    {"name": "National Museum Tokyo (Arms)", "lat": 35.7189, "lon": 139.7761, "country": "Japan", "collection": "Extensive", "highlights": "National treasure swords, samurai armor", "notes": "Finest collection of Japanese swords; many designated National Treasures"},
    {"name": "Higgins Armory (Worcester Art)", "lat": 42.2626, "lon": -71.8023, "country": "USA", "collection": "6,000+ objects", "highlights": "Medieval armor, dog armor", "notes": "Collection now at Worcester Art Museum; famed for interactive medieval exhibits"},
    {"name": "Musee de Cluny Paris", "lat": 48.8505, "lon": 2.3443, "country": "France", "collection": "Medieval collection", "highlights": "Lady and the Unicorn tapestries, arms", "notes": "National Museum of the Middle Ages; medieval weapons in Gothic setting"},
    {"name": "Palazzo Ducale Turin Armory", "lat": 45.0703, "lon": 7.6869, "country": "Italy", "collection": "5,000+ objects", "highlights": "Savoy royal arms collection", "notes": "One of richest armories in Europe; Savoy dynasty weapons spanning centuries"},
    {"name": "Philadelphia Museum of Art Arms", "lat": 39.9656, "lon": -75.1810, "country": "USA", "collection": "3,000+ objects", "highlights": "European and Asian arms", "notes": "Kienbusch collection of arms and armor; one of finest in Americas"},
    {"name": "Swedish Army Museum Stockholm", "lat": 59.3340, "lon": 18.0785, "country": "Sweden", "collection": "Extensive", "highlights": "Viking weapons, Gustavus Adolphus arms", "notes": "1000 years of Swedish military history; authentic Viking Age weapons"},
    {"name": "National Museum of Scotland Arms", "lat": 55.9470, "lon": -3.1894, "country": "Scotland", "collection": "Extensive", "highlights": "Claymores, Highland weapons", "notes": "Scottish weapons from Bronze Age through Jacobite risings"},
    {"name": "Historiska Museet Stockholm", "lat": 59.3347, "lon": 18.0908, "country": "Sweden", "collection": "10 million+", "highlights": "Viking swords, Gold Room", "notes": "Swedish History Museum; largest Viking Age weapons collection in world"},
    {"name": "Germanisches Nationalmuseum", "lat": 49.4478, "lon": 11.0772, "country": "Germany", "collection": "Extensive", "highlights": "Germanic weapons, medieval armor", "notes": "Largest museum of German culture; superb arms and armor galleries"},
    {"name": "Musee Royal Armee Bruxelles", "lat": 50.8411, "lon": 4.3928, "country": "Belgium", "collection": "Extensive", "highlights": "Medieval to modern Belgian arms", "notes": "Royal Museum of Armed Forces; covers 1000 years of military history"},
    {"name": "Museo Poldi Pezzoli Milan", "lat": 45.4693, "lon": 9.1907, "country": "Italy", "collection": "Select arms", "highlights": "Renaissance Italian armor", "notes": "Private collector's museum; exquisite Renaissance weapons in palatial setting"},
    {"name": "Castel Sant'Angelo Armory Rome", "lat": 41.9031, "lon": 12.4663, "country": "Italy", "collection": "Extensive", "highlights": "Papal guard weapons, siege equipment", "notes": "Former papal fortress; military collection includes Renaissance-era papal arms"},
    {"name": "National War Museum Valletta", "lat": 35.8989, "lon": 14.5147, "country": "Malta", "collection": "Extensive", "highlights": "Knights of Malta arms, Ottoman siege weapons", "notes": "Great Siege of 1565 artifacts; Knights Hospitaller weapons and armor"},
    {"name": "Seki Sword Tradition Museum", "lat": 35.4944, "lon": 136.9183, "country": "Japan", "collection": "Focused", "highlights": "Seki tradition katanas, modern knives", "notes": "Living tradition museum; swordsmiths demonstrate forging techniques"},
    {"name": "Museo Naval Madrid", "lat": 40.4151, "lon": -3.6928, "country": "Spain", "collection": "Extensive", "highlights": "Conquistador weapons, naval arms", "notes": "Spanish naval weapons; Age of Exploration era arms and boarding weapons"},
    {"name": "Danish National Museum Arms", "lat": 55.6744, "lon": 12.5747, "country": "Denmark", "collection": "Extensive", "highlights": "Viking weapons, Bronze Age swords", "notes": "Finest Danish prehistoric and Viking weaponry; Bronze Age ceremonial swords"},
    {"name": "Army Museum Invalides Paris", "lat": 48.8567, "lon": 2.3128, "country": "France", "collection": "500,000+", "highlights": "Francis I armor, Napoleonic swords", "notes": "Largest military museum in France; armor gallery spans medieval to modern"},
    {"name": "Livrustkammaren Stockholm", "lat": 59.3265, "lon": 18.0719, "country": "Sweden", "collection": "Royal arms", "highlights": "Gustav II Adolf battle armor", "notes": "Oldest museum in Sweden (1628); royal weapons and armor from 500 years"},
]

# ===================================================================
# 7. VIKING WEAPON FINDS (30 entries)
# ===================================================================
VIKING_WEAPONS = [
    {"name": "Gjermundbu Helmet Find", "lat": 60.2333, "lon": 10.2333, "country": "Norway", "year": "10th century", "type": "Helmet", "notes": "Only complete Viking Age helmet ever found; spectacle guard type; national icon"},
    {"name": "Oseberg Ship Burial", "lat": 59.3167, "lon": 10.3333, "country": "Norway", "year": "834 AD", "type": "Ship burial weapons", "notes": "Richest Viking ship burial; weapons, tools, and ceremonial items for two women"},
    {"name": "Gokstad Ship Burial", "lat": 59.1500, "lon": 10.2167, "country": "Norway", "year": "900 AD", "type": "Ship burial weapons", "notes": "Warrior king's burial ship; 64 shields along gunwales; weapons for afterlife"},
    {"name": "Sutton Hoo Burial", "lat": 52.0889, "lon": 1.3417, "country": "England", "year": "625 AD", "type": "Anglo-Saxon weapons", "notes": "Magnificent Anglo-Saxon ship burial; sword, helmet, shield; possibly King Raedwald"},
    {"name": "Hedeby Viking Settlement", "lat": 54.4900, "lon": 9.5700, "country": "Germany", "year": "8th-11th century", "type": "Settlement weapons", "notes": "Major Viking trading center; extensive weapon finds including swords and axes"},
    {"name": "Birka Viking Town", "lat": 59.3333, "lon": 17.5500, "country": "Sweden", "year": "8th-10th century", "type": "Garrison weapons", "notes": "Major trading town; warrior graves with swords, spears, shields; Birka warrior woman"},
    {"name": "Jorvik (York) Viking Finds", "lat": 53.9591, "lon": -1.0822, "country": "England", "year": "9th-10th century", "type": "Urban weapon finds", "notes": "Viking capital of Danelaw; axes, swords, and arrowheads found in excavations"},
    {"name": "Trelleborg Viking Fortress", "lat": 55.3925, "lon": 11.2650, "country": "Denmark", "year": "980 AD", "type": "Fortress weapons", "notes": "Ring fortress of Harald Bluetooth; standardized military equipment found"},
    {"name": "L'Anse aux Meadows", "lat": 51.5961, "lon": -55.5339, "country": "Canada", "year": "1000 AD", "type": "Settlement finds", "notes": "Only confirmed Viking site in North America; iron rivets and metalworking evidence"},
    {"name": "Roskilde Viking Ship Museum", "lat": 55.6500, "lon": 12.0833, "country": "Denmark", "year": "11th century", "type": "Warship weapons", "notes": "Five scuttled Viking ships; warships and cargo vessels with associated weaponry"},
    {"name": "Gotland Viking Hoards", "lat": 57.5000, "lon": 18.5500, "country": "Sweden", "year": "8th-11th century", "type": "Hoards with weapons", "notes": "More silver hoards than rest of Scandinavia combined; sword pommels and fittings"},
    {"name": "Dublin Viking Quarter", "lat": 53.3472, "lon": -6.2711, "country": "Ireland", "year": "9th-11th century", "type": "Urban weapons", "notes": "Viking Dublin excavations at Wood Quay; swords, axes, spearheads in quantity"},
    {"name": "Repton Great Army Camp", "lat": 52.8333, "lon": -1.5500, "country": "England", "year": "873 AD", "type": "Army camp weapons", "notes": "Great Heathen Army winter camp; mass grave with weapons; charnel deposit"},
    {"name": "Kaupang Trading Post", "lat": 59.0500, "lon": 10.0500, "country": "Norway", "year": "8th-10th century", "type": "Trading post finds", "notes": "Earliest Norwegian Viking trading town; weapons and craft tools excavated"},
    {"name": "Jelling Royal Monuments", "lat": 55.7547, "lon": 9.4197, "country": "Denmark", "year": "10th century", "type": "Royal burial weapons", "notes": "Royal seat of Denmark; Harald Bluetooth's runestones; burial chamber weapons"},
    {"name": "Staffordshire Hoard", "lat": 52.6667, "lon": -1.9333, "country": "England", "year": "7th-8th century", "type": "Weapon fittings hoard", "notes": "Largest Anglo-Saxon gold hoard; 11 lbs of gold; mostly stripped sword fittings"},
    {"name": "Skuldelev Ships", "lat": 55.6500, "lon": 12.0833, "country": "Denmark", "year": "1070 AD", "type": "Warship finds", "notes": "Five ships blocking Roskilde fjord; longships with weapon storage and shields"},
    {"name": "Ribe Viking Center", "lat": 55.3333, "lon": 8.7500, "country": "Denmark", "year": "8th century", "type": "Town finds", "notes": "Oldest town in Scandinavia; metalworking evidence and weapon production debris"},
    {"name": "Lindisfarne Priory", "lat": 55.6833, "lon": -1.8000, "country": "England", "year": "793 AD", "type": "Raid site", "notes": "First recorded Viking raid; shocked Christian Europe; arrowheads found on site"},
    {"name": "Aggersborg Fortress", "lat": 56.9833, "lon": 9.2500, "country": "Denmark", "year": "980 AD", "type": "Fortress weapons", "notes": "Largest Viking ring fortress; 240m diameter; military equipment for 3000 warriors"},
    {"name": "Mammen Grave", "lat": 56.3333, "lon": 9.4167, "country": "Denmark", "year": "970 AD", "type": "Elite burial weapons", "notes": "Richly decorated axe defining Mammen art style; elite warrior grave goods"},
    {"name": "Valsgarde Boat Graves", "lat": 59.8667, "lon": 17.5833, "country": "Sweden", "year": "6th-11th century", "type": "Boat burial weapons", "notes": "62 graves spanning Vendel and Viking periods; complete weapon sets in boats"},
    {"name": "Vendel Boat Graves", "lat": 59.8833, "lon": 17.6000, "country": "Sweden", "year": "6th-8th century", "type": "Pre-Viking weapons", "notes": "Elite warrior graves preceding Viking Age; crested helmets and pattern-welded swords"},
    {"name": "Lough Corrib Sword Find", "lat": 53.4500, "lon": -9.3500, "country": "Ireland", "year": "9th-10th century", "type": "Lake find", "notes": "Viking sword found in Irish lake; possibly ritual deposition or battle loss"},
    {"name": "Kilmainham Viking Graves", "lat": 53.3417, "lon": -6.3083, "country": "Ireland", "year": "9th century", "type": "Cemetery weapons", "notes": "Viking warrior cemetery in Dublin; swords, spears, and oval brooches"},
    {"name": "Tune Ship Burial", "lat": 59.2833, "lon": 11.0333, "country": "Norway", "year": "900 AD", "type": "Ship burial", "notes": "Third great Norwegian ship burial; warrior equipment including horse gear"},
    {"name": "Gnezdovo Burial Ground", "lat": 54.7833, "lon": 31.8500, "country": "Russia", "year": "10th century", "type": "Varangian graves", "notes": "Largest Viking Age burial ground outside Scandinavia; Varangian warrior graves"},
    {"name": "Fyrkat Viking Fortress", "lat": 56.6236, "lon": 9.7678, "country": "Denmark", "year": "980 AD", "type": "Fortress finds", "notes": "Harald Bluetooth ring fortress; reconstructed longhouse; military finds"},
    {"name": "Cuerdale Hoard", "lat": 53.7667, "lon": -2.6833, "country": "England", "year": "905 AD", "type": "Viking silver hoard", "notes": "Largest Viking silver hoard outside Russia; 8600+ items including hack-silver and ingots"},
    {"name": "Galloway Hoard", "lat": 54.8833, "lon": -4.0167, "country": "Scotland", "year": "900 AD", "type": "Viking Age hoard", "notes": "Discovered 2014; gold, silver, jewelled cross; Viking and Anglo-Saxon objects mixed"},
]

# ===================================================================
# 8. CHINESE & ASIAN WEAPONS HERITAGE (30 entries)
# ===================================================================
ASIAN_WEAPONS = [
    {"name": "Terracotta Army Pit 2 (Weapons)", "lat": 34.3842, "lon": 109.2785, "country": "China", "era": "221 BC", "type": "Bronze weapons cache", "notes": "Over 40,000 bronze weapons found; crossbow triggers, swords, halberds still sharp after 2200 years"},
    {"name": "Longquan Sword Village", "lat": 28.0742, "lon": 119.1417, "country": "China", "era": "Spring & Autumn-present", "type": "Sword forging center", "notes": "2600-year tradition of sword-making; Ou Yezi legendary swordsmith; UNESCO intangible heritage"},
    {"name": "Shaolin Temple", "lat": 34.5075, "lon": 112.9350, "country": "China", "era": "495 AD-present", "type": "Martial arts weapons", "notes": "Birthplace of Shaolin kung fu; 18 weapons of Shaolin; staff fighting tradition"},
    {"name": "Wudang Mountains", "lat": 32.4000, "lon": 111.0000, "country": "China", "era": "Tang-present", "type": "Taoist sword tradition", "notes": "Taoist martial arts center; jian (straight sword) tradition; wudang sword forms"},
    {"name": "Hwarang Training Ground Gyeongju", "lat": 35.8564, "lon": 129.2247, "country": "South Korea", "era": "Silla dynasty", "type": "Korean warrior training", "notes": "Elite Silla warrior youth corps; Korean sword, bow, and spear traditions"},
    {"name": "Angkor Wat Battle Reliefs", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "era": "12th century", "type": "Depicted weapons", "notes": "Bas-reliefs show Khmer and Cham warriors with spears, bows, and war elephants"},
    {"name": "Kris Forge Bali", "lat": -8.3405, "lon": 115.0920, "country": "Indonesia", "era": "Ancient-present", "type": "Kris dagger forging", "notes": "Sacred keris daggers with wavy blades; believed to possess spiritual power; UNESCO heritage"},
    {"name": "Suwon Hwaseong Fortress", "lat": 37.2878, "lon": 127.0130, "country": "South Korea", "era": "1794-1796", "type": "Korean fortification weapons", "notes": "UNESCO fortress; innovative Korean siege weapons; hwachae multiple rocket launcher"},
    {"name": "Hue Imperial Citadel Armory", "lat": 16.4698, "lon": 107.5774, "country": "Vietnam", "era": "Nguyen dynasty", "type": "Vietnamese imperial weapons", "notes": "Nguyen dynasty armory; Vietnamese swords, crossbows, and early firearms"},
    {"name": "Forbidden City Armory Beijing", "lat": 39.9163, "lon": 116.3972, "country": "China", "era": "Ming-Qing", "type": "Imperial weapons", "notes": "Imperial Palace armory; ceremonial and military weapons of Chinese emperors"},
    {"name": "Nara Todai-ji Temple Swords", "lat": 34.6889, "lon": 135.8397, "country": "Japan", "era": "Nara period", "type": "Temple sword treasury", "notes": "Shosoin repository holds 8th-century swords from Silk Road trade"},
    {"name": "Ayutthaya Arsenal", "lat": 14.3532, "lon": 100.5685, "country": "Thailand", "era": "1351-1767", "type": "Siamese weapons", "notes": "Siamese kingdom capital; krabi-krabong weapon arts; elephant-mounted warriors"},
    {"name": "Gyeongbokgung Palace Guard Arms", "lat": 37.5796, "lon": 126.9770, "country": "South Korea", "era": "Joseon dynasty", "type": "Korean palace guard", "notes": "Joseon royal guard weapons; Korean hwando swords and flail weapons"},
    {"name": "Mughal Red Fort Armory Delhi", "lat": 28.6562, "lon": 77.2410, "country": "India", "era": "Mughal", "type": "Mughal imperial arms", "notes": "Mughal emperor's arsenal; tulwar swords, katar daggers, composite bows"},
    {"name": "Jodhpur Mehrangarh Fort Arms", "lat": 26.2986, "lon": 73.0184, "country": "India", "era": "15th century-present", "type": "Rajput weapons", "notes": "Spectacular Rajput arms collection; khanda swords, chakram throwing discs"},
    {"name": "Mandalay Royal Palace", "lat": 21.9588, "lon": 96.0891, "country": "Myanmar", "era": "Konbaung dynasty", "type": "Burmese royal arms", "notes": "Last Burmese royal capital; dha swords and spears of Konbaung warriors"},
    {"name": "Thang Long Citadel Hanoi", "lat": 21.0354, "lon": 105.8400, "country": "Vietnam", "era": "11th century-present", "type": "Vietnamese weapons", "notes": "1000-year citadel; Vietnamese independence weapons; crossbow traditions"},
    {"name": "Matsumoto Castle Armory", "lat": 36.2381, "lon": 137.9691, "country": "Japan", "era": "1504-present", "type": "Samurai weapons display", "notes": "Black Crow Castle; gun collection showing firearms adoption in feudal Japan"},
    {"name": "Golden Temple Armory Amritsar", "lat": 31.6200, "lon": 74.8765, "country": "India", "era": "Sikh Empire", "type": "Sikh weapons", "notes": "Sikh warrior tradition; kirpan daggers, chakram rings, and Khalsa arms"},
    {"name": "Bagan Temple Weapons Reliefs", "lat": 21.1717, "lon": 94.8585, "country": "Myanmar", "era": "9th-13th century", "type": "Depicted weapons", "notes": "Temple reliefs show Pagan dynasty warriors with swords, spears, and bows"},
    {"name": "Chiang Mai Night Bazaar Blades", "lat": 18.7883, "lon": 98.9953, "country": "Thailand", "era": "Lanna-present", "type": "Traditional Thai blades", "notes": "Northern Thai blade tradition; enep (short sword) and dha crafting continues"},
    {"name": "Zhangjiajie Miao Weapons", "lat": 29.1167, "lon": 110.4792, "country": "China", "era": "Ancient-present", "type": "Ethnic minority weapons", "notes": "Miao/Hmong silverwork and weapon traditions; crossbow and sword heritage"},
    {"name": "Kathmandu Durbar Square Arms", "lat": 27.7042, "lon": 85.3076, "country": "Nepal", "era": "Malla-Shah", "type": "Nepalese weapons", "notes": "Royal Nepalese armory; kukri knives, kora swords; Gurkha warrior tradition"},
    {"name": "Osaka Castle Armory", "lat": 34.6873, "lon": 135.5262, "country": "Japan", "era": "1583-present", "type": "Samurai armor display", "notes": "Toyotomi then Tokugawa fortress; extensive samurai weapon and armor exhibits"},
    {"name": "Udaipur City Palace Arms", "lat": 24.5764, "lon": 73.6913, "country": "India", "era": "Mewar kingdom", "type": "Rajput arms", "notes": "Mewar royal collection; Rajput swords, shields, and elephant armor"},
    {"name": "Luoyang Ancient Tomb Weapons", "lat": 34.6197, "lon": 112.4540, "country": "China", "era": "Zhou-Han", "type": "Tomb weapons", "notes": "Ancient capital tombs yielded bronze ge halberds, ji spears, and jian swords"},
    {"name": "Jeonju Hanok Village Armory", "lat": 35.8151, "lon": 127.1530, "country": "South Korea", "era": "Joseon", "type": "Korean traditional arms", "notes": "Korean traditional village; demonstrations of Korean martial arts and weapons"},
    {"name": "Thanjavur Palace Armory", "lat": 10.7862, "lon": 79.1318, "country": "India", "era": "Chola-Nayak", "type": "South Indian arms", "notes": "Tamil royal weapons; urumi flexible sword, vel spear; Chola bronze weaponry"},
    {"name": "Gyeongju National Museum Arms", "lat": 35.8372, "lon": 129.2227, "country": "South Korea", "era": "Silla dynasty", "type": "Ancient Korean weapons", "notes": "Silla kingdom swords and horse armor; gold-decorated ceremonial weapons"},
    {"name": "Yunnan Bronze Weapons Site", "lat": 24.8801, "lon": 102.8329, "country": "China", "era": "Warring States-Han", "type": "Dian kingdom weapons", "notes": "Dian kingdom bronze weapons; unique animal-motif weapons unlike Chinese mainland styles"},
]

# ===================================================================
# 9. GUNPOWDER & FIREARMS ORIGINS (28 entries)
# ===================================================================
GUNPOWDER_ORIGINS = [
    {"name": "Dunhuang Gunpowder Caves", "lat": 40.1422, "lon": 94.6619, "country": "China", "era": "9th century", "type": "Earliest gunpowder texts", "notes": "Mogao caves manuscripts describe earliest known gunpowder formulas by Chinese alchemists"},
    {"name": "Kaifeng Song Arsenal", "lat": 34.7972, "lon": 114.3081, "country": "China", "era": "10th-12th century", "type": "Fire lance production", "notes": "Song dynasty capital; first military use of gunpowder; fire lances and bombs"},
    {"name": "Wujing Zongyao Publication Site", "lat": 34.2649, "lon": 108.9432, "country": "China", "era": "1044 AD", "type": "Military manual", "notes": "First published gunpowder formulas in military compendium; fire arrows and bombs"},
    {"name": "Mongol Siege of Xiangyang", "lat": 32.0420, "lon": 112.1440, "country": "China", "era": "1267-1273", "type": "Early cannon use", "notes": "Mongols used counterweight trebuchets and explosive shells; pivotal siege"},
    {"name": "Crecy Cannon Site", "lat": 50.2544, "lon": 1.8889, "country": "France", "era": "1346", "type": "Early European cannon", "notes": "English may have used primitive cannon (ribaldequins) against French cavalry"},
    {"name": "Constantinople 1453 Cannon Site", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "era": "1453", "type": "Great Bombard", "notes": "Orban's massive bombard breached Theodosian Walls; proved cannon could destroy any fortification"},
    {"name": "Tannenberg Handgonne Find", "lat": 50.6333, "lon": 9.0833, "country": "Germany", "era": "1399", "type": "Earliest dated European firearm", "notes": "Oldest surviving European handgun with a date; found in castle ruins"},
    {"name": "Darjiling (Xanadu) Gunpowder Route", "lat": 42.3583, "lon": 116.1833, "country": "China", "era": "13th century", "type": "Mongol transmission point", "notes": "Kublai Khan's summer capital; Mongol conquests spread gunpowder technology westward"},
    {"name": "Roger Bacon's Oxford", "lat": 51.7520, "lon": -1.2577, "country": "England", "era": "1267", "type": "European gunpowder text", "notes": "Bacon described gunpowder formula in Opus Majus; among first European descriptions"},
    {"name": "Schwarz Freiburg Workshop", "lat": 47.9990, "lon": 7.8421, "country": "Germany", "era": "14th century", "type": "Legendary gunpowder site", "notes": "Berthold Schwarz, legendary monk credited with inventing European gunpowder weapons"},
    {"name": "Venice Arsenal Cannon Foundry", "lat": 45.4361, "lon": 12.3531, "country": "Italy", "era": "15th century", "type": "Naval cannon production", "notes": "Venice Arsenal mass-produced naval cannon; armed the largest Mediterranean fleet"},
    {"name": "Liege Gun Proof House", "lat": 50.6292, "lon": 5.5736, "country": "Belgium", "era": "1672-present", "type": "Firearms proofing", "notes": "Oldest proof house still operating; every firearm tested before sale since 1672"},
    {"name": "Beretta Brescia Workshop", "lat": 45.5416, "lon": 10.2118, "country": "Italy", "era": "1526-present", "type": "Oldest firearms company", "notes": "Oldest active firearms manufacturer in world; supplied Venice with arquebus barrels in 1526"},
    {"name": "Tower of London Gun Stores", "lat": 51.5081, "lon": -0.0759, "country": "England", "era": "16th century", "type": "Royal gun stores", "notes": "Henry VIII expanded gun stores; housed thousands of muskets and cannon"},
    {"name": "Springfield Armory", "lat": 42.1075, "lon": -72.5836, "country": "USA", "era": "1777-1968", "type": "US government armory", "notes": "First US national armory; interchangeable parts revolution; M1 Garand produced here"},
    {"name": "Enfield Lock Royal Small Arms", "lat": 51.6667, "lon": -0.0333, "country": "England", "era": "1816-1988", "type": "British military firearms", "notes": "Produced Lee-Enfield rifles; armed British Empire; Bren gun production in WWII"},
    {"name": "Saint-Etienne Manufacture", "lat": 45.4397, "lon": 4.3872, "country": "France", "era": "1764-present", "type": "French state arms factory", "notes": "Royal then state arms factory; produced Chassepot, Lebel, and FAMAS rifles"},
    {"name": "Tula Arms Factory", "lat": 54.1961, "lon": 37.6182, "country": "Russia", "era": "1712-present", "type": "Russian state arms", "notes": "Founded by Peter the Great; Mosin-Nagant and Tokarev production; still active"},
    {"name": "Tanegashima Gun Island", "lat": 30.7333, "lon": 131.0000, "country": "Japan", "era": "1543", "type": "Firearms introduction to Japan", "notes": "Portuguese brought first firearms to Japan; Japanese rapidly copied and improved them"},
    {"name": "Nagashino Battlefield", "lat": 34.9500, "lon": 137.5667, "country": "Japan", "era": "1575", "type": "Mass firearms battle", "notes": "Oda Nobunaga used 3000 arquebus in rotating volleys; revolutionized Japanese warfare"},
    {"name": "Harper's Ferry Armory", "lat": 39.3246, "lon": -77.7286, "country": "USA", "era": "1799-1862", "type": "US government armory", "notes": "John Brown's raid 1859; produced rifles and pistols; destroyed in Civil War"},
    {"name": "Oberndorf Mauser Works", "lat": 48.2939, "lon": 8.5731, "country": "Germany", "era": "1874-present", "type": "Bolt-action rifle origin", "notes": "Mauser rifle factory; Gewehr 98 bolt action influenced nearly all modern rifles"},
    {"name": "Herstal FN Factory", "lat": 50.6583, "lon": 5.6333, "country": "Belgium", "era": "1889-present", "type": "Firearms manufacturer", "notes": "Fabrique Nationale; produced Browning designs, FAL rifle, P90; major NATO supplier"},
    {"name": "Birmingham Gun Quarter", "lat": 52.4862, "lon": -1.8904, "country": "England", "era": "17th century-present", "type": "Mass firearms production", "notes": "Produced millions of firearms; armed British Empire and exported globally"},
    {"name": "Colt Factory Hartford", "lat": 41.7551, "lon": -72.6710, "country": "USA", "era": "1847-present", "type": "Revolver production", "notes": "Samuel Colt's revolver factory; 'God made men, Colt made them equal'"},
    {"name": "Izhevsk Arms Factory", "lat": 56.8431, "lon": 53.2114, "country": "Russia", "era": "1807-present", "type": "Russian arms production", "notes": "Produced AK-47 and derivatives; largest small arms factory in Russia"},
    {"name": "Suhl Arms Center", "lat": 50.6081, "lon": 10.6930, "country": "Germany", "era": "16th century-present", "type": "German arms center", "notes": "Thuringian Forest arms town; produced hunting weapons and military firearms"},
    {"name": "Eibar Basque Arms Town", "lat": 43.1847, "lon": -2.4722, "country": "Spain", "era": "16th century-present", "type": "Spanish firearms", "notes": "Basque arms capital; Astra, Star, and Llama pistol production; armed Spanish military"},
]

# ===================================================================
# 10. ANCIENT SIEGE WARFARE SITES (28 entries)
# ===================================================================
SIEGE_SITES = [
    {"name": "Masada Roman Siege Ramp", "lat": 31.3156, "lon": 35.3536, "country": "Israel", "year": "73 AD", "besiegers": "Roman Empire", "notes": "Romans built massive earth ramp to breach hilltop fortress; 8 siege camps still visible"},
    {"name": "Syracuse Siege (Archimedes)", "lat": 37.0755, "lon": 15.2866, "country": "Italy", "year": "214-212 BC", "besiegers": "Roman Republic", "notes": "Archimedes' war machines defended city; burning mirrors legend; death of Archimedes"},
    {"name": "Constantinople Theodosian Walls", "lat": 41.0150, "lon": 28.9230, "country": "Turkey", "year": "Multiple sieges", "besiegers": "Various", "notes": "Triple wall system repelled sieges for 1000 years until gunpowder cannons in 1453"},
    {"name": "Tyre Siege by Alexander", "lat": 33.2705, "lon": 35.1956, "country": "Lebanon", "year": "332 BC", "besiegers": "Macedonia", "notes": "Alexander built causeway to island city; 7-month siege; engineering marvel of ancient world"},
    {"name": "Alesia Double Circumvallation", "lat": 47.5364, "lon": 4.5028, "country": "France", "year": "52 BC", "besiegers": "Roman Republic", "notes": "Caesar built double ring of fortifications; besieged Vercingetorix while fending off relief army"},
    {"name": "Jerusalem Siege (70 AD)", "lat": 31.7767, "lon": 35.2345, "country": "Israel", "year": "70 AD", "besiegers": "Roman Empire", "notes": "Titus destroyed Second Temple; circumvallation wall; 1.1 million killed per Josephus"},
    {"name": "Carthage Final Siege", "lat": 36.8528, "lon": 10.3233, "country": "Tunisia", "year": "149-146 BC", "besiegers": "Roman Republic", "notes": "Three-year siege ended Punic Wars; city razed; Scipio Aemilianus' total destruction"},
    {"name": "Siege of Acre (Crusader)", "lat": 32.9233, "lon": 35.0678, "country": "Israel", "year": "1189-1191", "besiegers": "Crusaders", "notes": "Two-year siege during Third Crusade; Richard Lionheart and Philip II retook city from Saladin"},
    {"name": "Rhodes Siege (Demetrius)", "lat": 36.4510, "lon": 28.2278, "country": "Greece", "year": "305 BC", "besiegers": "Antigonus dynasty", "notes": "Demetrius Poliorcetes used massive siege tower Helepolis; failed; Colossus built from spoils"},
    {"name": "Siege of Orleans", "lat": 47.9029, "lon": 1.9092, "country": "France", "year": "1428-1429", "besiegers": "England", "notes": "Joan of Arc lifted English siege; turning point of Hundred Years War"},
    {"name": "Troy (Hisarlik)", "lat": 39.9575, "lon": 26.2389, "country": "Turkey", "year": "c. 1180 BC", "besiegers": "Achaean Greeks", "notes": "Legendary 10-year siege from Homer's Iliad; Trojan Horse stratagem; archaeological remains"},
    {"name": "Numantia", "lat": 41.8081, "lon": -2.4422, "country": "Spain", "year": "134-133 BC", "besiegers": "Roman Republic", "notes": "Scipio Aemilianus besieged Celtiberian city; 7 camps and circumvallation; mass suicide of defenders"},
    {"name": "Chateau Gaillard", "lat": 49.2381, "lon": 1.3003, "country": "France", "year": "1203-1204", "besiegers": "France", "notes": "Richard Lionheart's impregnable castle fell to Philip II; innovative concentric design failed"},
    {"name": "Malta Great Siege", "lat": 35.8879, "lon": 14.5101, "country": "Malta", "year": "1565", "besiegers": "Ottoman Empire", "notes": "Knights of St. John repelled 40,000 Ottomans; one of greatest sieges in history"},
    {"name": "Tenochtitlan Siege", "lat": 19.4326, "lon": -99.1332, "country": "Mexico", "year": "1521", "besiegers": "Spanish & allies", "notes": "Cortes besieged Aztec island capital; brigantines on lake; smallpox devastated defenders"},
    {"name": "Vicksburg Siege", "lat": 32.3526, "lon": -90.8779, "country": "USA", "year": "1863", "besiegers": "Union Army", "notes": "47-day siege by Grant; city surrendered July 4; Union controlled Mississippi River"},
    {"name": "Kenilworth Castle Siege", "lat": 52.3440, "lon": -1.5830, "country": "England", "year": "1266", "besiegers": "Henry III", "notes": "Longest siege in English medieval history; 172 days; massive water defenses"},
    {"name": "Szigetvar Siege", "lat": 46.0486, "lon": 17.7983, "country": "Hungary", "year": "1566", "besiegers": "Ottoman Empire", "notes": "Zrinyi's 2,300 defenders held 100,000 Ottomans; Suleiman died during siege"},
    {"name": "Caffa Siege (Black Death)", "lat": 45.0319, "lon": 35.3825, "country": "Ukraine (Crimea)", "year": "1346", "besiegers": "Mongol Golden Horde", "notes": "Mongols catapulted plague-infected corpses; possibly spread Black Death to Europe"},
    {"name": "Osaka Castle Siege", "lat": 34.6873, "lon": 135.5262, "country": "Japan", "year": "1614-1615", "besiegers": "Tokugawa Shogunate", "notes": "Two campaigns to destroy Toyotomi; largest samurai battle; ended Sengoku period"},
    {"name": "Antioch Siege (First Crusade)", "lat": 36.2025, "lon": 36.1603, "country": "Turkey", "year": "1097-1098", "besiegers": "Crusaders", "notes": "Eight-month Crusader siege; Bohemond's treachery opened gates; Holy Lance discovery"},
    {"name": "Vienna Siege 1529", "lat": 48.2082, "lon": 16.3738, "country": "Austria", "year": "1529", "besiegers": "Ottoman Empire", "notes": "Suleiman's failed siege; high-water mark of Ottoman expansion into Central Europe"},
    {"name": "Leningrad Siege", "lat": 59.9311, "lon": 30.3609, "country": "Russia", "year": "1941-1944", "besiegers": "Nazi Germany", "notes": "872-day siege; deadliest in history; ~1 million civilian deaths from starvation"},
    {"name": "Trebizond Siege", "lat": 41.0027, "lon": 39.7168, "country": "Turkey", "year": "1461", "besiegers": "Ottoman Empire", "notes": "Fall of last Byzantine successor state; Mehmed II conquered Trebizond Empire"},
    {"name": "Candia Siege (Heraklion)", "lat": 35.3387, "lon": 25.1442, "country": "Greece (Crete)", "year": "1648-1669", "besiegers": "Ottoman Empire", "notes": "Longest siege in history at 21 years; Venetians vs Ottomans on Crete"},
    {"name": "Badajoz Siege", "lat": 38.8794, "lon": -6.9706, "country": "Spain", "year": "1812", "besiegers": "Anglo-Portuguese", "notes": "Wellington stormed French-held fortress; horrific breaching assault; sack of city followed"},
    {"name": "Sevastopol Siege (Crimean War)", "lat": 44.6167, "lon": 33.5254, "country": "Ukraine", "year": "1854-1855", "besiegers": "Allied forces", "notes": "Year-long siege during Crimean War; Charge of the Light Brigade nearby; massive bombardment"},
    {"name": "Lucknow Siege", "lat": 26.8467, "lon": 80.9462, "country": "India", "year": "1857", "besiegers": "Indian Sepoys", "notes": "British Residency besieged during Indian Rebellion; 87-day siege; fierce fighting"},
    {"name": "Dien Bien Phu", "lat": 21.3833, "lon": 103.0167, "country": "Vietnam", "year": "1954", "besiegers": "Viet Minh", "notes": "Vietnamese forces besieged French garrison in valley; artillery on surrounding hills; ended French Indochina"},
    {"name": "Stalingrad", "lat": 48.7080, "lon": 44.5133, "country": "Russia", "year": "1942-1943", "besiegers": "Soviet Union", "notes": "Deadliest battle in WWII; Soviet encirclement of German 6th Army; turning point of Eastern Front"},
    {"name": "Cuzco Siege", "lat": -13.5320, "lon": -71.9675, "country": "Peru", "year": "1536-1537", "besiegers": "Inca Empire", "notes": "Manco Inca besieged Spanish garrison; 10-month siege; Inca used captured European weapons"},
    {"name": "Port Arthur Siege", "lat": 38.8514, "lon": 121.2619, "country": "China", "year": "1904-1905", "besiegers": "Imperial Japan", "notes": "Russo-Japanese War siege; first modern siege with machine guns and heavy artillery; 5-month campaign"},
    {"name": "Drogheda Siege", "lat": 53.7189, "lon": -6.3478, "country": "Ireland", "year": "1649", "besiegers": "Cromwell's New Model Army", "notes": "Cromwell's brutal storming of Royalist-held town; garrison massacred; notorious in Irish history"},
    {"name": "Harlech Castle Siege", "lat": 52.8600, "lon": -4.1094, "country": "Wales", "year": "1461-1468", "besiegers": "Yorkist forces", "notes": "Longest siege in British history at 7 years; inspired song Men of Harlech; Wars of the Roses"},
    {"name": "Verdun", "lat": 49.1600, "lon": 5.3831, "country": "France", "year": "1916", "besiegers": "Imperial Germany", "notes": "10-month WWI battle/siege; 700,000+ casualties; French fortress city became symbol of endurance"},
    {"name": "Alamo", "lat": 29.4260, "lon": -98.4861, "country": "USA", "year": "1836", "besiegers": "Mexican Army", "notes": "Santa Anna besieged Texan defenders for 13 days; all defenders killed; rallying cry for Texas independence"},
]

# ===================================================================
# DATA MAP: mode -> (dataset, icon, colour, popup_fields)
# ===================================================================
_MODE_MAP = {
    "Japanese Katana Forges": {
        "data": KATANA_FORGES,
        "icon": "fire",
        "color": "red",
        "fields": ["region", "era", "tradition", "notes"],
        "labels": ["Region", "Era", "Tradition", "Notes"],
    },
    "European Sword Making Centers": {
        "data": EUROPEAN_SWORDS,
        "icon": "wrench",
        "color": "blue",
        "fields": ["country", "era", "specialty", "notes"],
        "labels": ["Country", "Era", "Specialty", "Notes"],
    },
    "Damascus Steel Origins": {
        "data": DAMASCUS_STEEL,
        "icon": "star",
        "color": "orange",
        "fields": ["country", "era", "type", "notes"],
        "labels": ["Country", "Era", "Type", "Notes"],
    },
    "Medieval Armor Workshops": {
        "data": ARMOR_WORKSHOPS,
        "icon": "shield",
        "color": "gray",
        "fields": ["country", "era", "specialty", "notes"],
        "labels": ["Country", "Era", "Specialty", "Notes"],
    },
    "Famous Ancient Battlefields": {
        "data": BATTLEFIELDS,
        "icon": "screenshot",
        "color": "darkred",
        "fields": ["country", "year", "combatants", "notes"],
        "labels": ["Country", "Year", "Combatants", "Notes"],
    },
    "Weapons & Armor Museums": {
        "data": MUSEUMS,
        "icon": "home",
        "color": "purple",
        "fields": ["country", "collection", "highlights", "notes"],
        "labels": ["Country", "Collection", "Highlights", "Notes"],
    },
    "Viking Weapon Finds": {
        "data": VIKING_WEAPONS,
        "icon": "flash",
        "color": "darkblue",
        "fields": ["country", "year", "type", "notes"],
        "labels": ["Country", "Year", "Type", "Notes"],
    },
    "Chinese & Asian Weapons Heritage": {
        "data": ASIAN_WEAPONS,
        "icon": "flag",
        "color": "cadetblue",
        "fields": ["country", "era", "type", "notes"],
        "labels": ["Country", "Era", "Type", "Notes"],
    },
    "Gunpowder & Firearms Origins": {
        "data": GUNPOWDER_ORIGINS,
        "icon": "certificate",
        "color": "darkgreen",
        "fields": ["country", "era", "type", "notes"],
        "labels": ["Country", "Era", "Type", "Notes"],
    },
    "Ancient Siege Warfare Sites": {
        "data": SIEGE_SITES,
        "icon": "tower",
        "color": "black",
        "fields": ["country", "year", "besiegers", "notes"],
        "labels": ["Country", "Year", "Besiegers", "Notes"],
    },
}

# ===================================================================
# HELPERS
# ===================================================================

def _build_popup(entry: dict, fields: list, labels: list) -> str:
    """Build a rich HTML popup string with escaped content."""
    name = html_module.escape(str(entry.get("name", "")))
    rows = ""
    for field, label in zip(fields, labels):
        val = html_module.escape(str(entry.get(field, "N/A")))
        rows += (
            f'<tr>'
            f'<td style="padding:3px 8px;font-weight:600;color:{_ACCENT};'
            f'vertical-align:top;white-space:nowrap;">{label}</td>'
            f'<td style="padding:3px 8px;color:{_TEXT};">{val}</td>'
            f'</tr>'
        )
    return (
        f'<div style="font-family:Inter,sans-serif;min-width:260px;max-width:340px;'
        f'background:{_SURFACE};border:1px solid #2a3550;border-radius:8px;padding:10px;">'
        f'<h4 style="margin:0 0 8px;color:{_ACCENT};font-size:14px;">{name}</h4>'
        f'<table style="border-collapse:collapse;font-size:12px;">{rows}</table>'
        f'</div>'
    )


def _build_map(data: list, mode_cfg: dict, zoom: int = 2) -> folium.Map:
    """Create a folium map with markers for the given dataset."""
    if not data:
        return folium.Map(location=[20, 0], zoom_start=zoom, tiles="CartoDB dark_matter")

    avg_lat = sum(d["lat"] for d in data) / len(data)
    avg_lon = sum(d["lon"] for d in data) / len(data)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    for entry in data:
        popup_html = _build_popup(entry, mode_cfg["fields"], mode_cfg["labels"])
        folium.Marker(
            location=[entry["lat"], entry["lon"]],
            popup=folium.Popup(popup_html, max_width=360),
            tooltip=entry["name"],
            icon=folium.Icon(
                icon=mode_cfg["icon"],
                prefix="glyphicon",
                color=mode_cfg["color"],
            ),
        ).add_to(m)

    return m


def _get_country_stats(data: list) -> dict:
    """Count entries per country (or region for katana forges)."""
    key = "country" if "country" in data[0] else "region"
    counts: dict = {}
    for d in data:
        c = d.get(key, "Unknown")
        counts[c] = counts.get(c, 0) + 1
    return counts


# ===================================================================
# MAIN RENDER FUNCTION
# ===================================================================

def render_ancient_weapons_maps_tab():
    """Render the Ancient Weapons & Armor Explorer tab."""

    # ---- Header ----
    st.markdown(
        '<div class="tab-header amber">'
        "<h4>Ancient Weapons & Armor Explorer</h4>"
        "<p>Sword forges, armor workshops, famous battlefields & weapons museums</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        key="ancient_weapons_maps_mode",
    )

    cfg = _MODE_MAP[mode]
    data = cfg["data"]

    # ---- Stats row ----
    country_stats = _get_country_stats(data)
    top_country = max(country_stats, key=country_stats.get) if country_stats else "N/A"
    top_count = country_stats.get(top_country, 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Locations", len(data))
    c2.metric("Countries / Regions", len(country_stats))
    c3.metric("Top Region", top_country)
    c4.metric("Locations in Top", top_count)

    # ---- Description blurbs ----
    _DESCRIPTIONS = {
        "Japanese Katana Forges": (
            "Explore the legendary sword-forging traditions of Japan, from the five "
            "main schools (Gokaden) to remote mountain tatara ironworks. Each location "
            "represents centuries of blade-making heritage passed down through master-"
            "apprentice lineages."
        ),
        "European Sword Making Centers": (
            "From Toledo's 2,000-year bladesmithing legacy to Solingen's modern cutlery "
            "empire, European sword making shaped warfare, trade, and culture across the "
            "continent for millennia."
        ),
        "Damascus Steel Origins": (
            "Trace the Silk Road journey of wootz crucible steel from Indian foundries "
            "to the legendary blade markets of Damascus and beyond. The secret of true "
            "Damascus steel was lost for centuries."
        ),
        "Medieval Armor Workshops": (
            "The master armorers of Milan, Augsburg, and Greenwich created wearable works "
            "of art in steel. Their workshops armed the knights, kings, and armies that "
            "defined medieval and Renaissance warfare."
        ),
        "Famous Ancient Battlefields": (
            "Walk the grounds where history was decided by the sword, spear, and bow. "
            "From Thermopylae to Sekigahara, these battlefields shaped civilizations "
            "and changed the course of empires."
        ),
        "Weapons & Armor Museums": (
            "The world's greatest arms and armor collections, from the Graz Landeszeughaus "
            "with 32,000 pieces to the Metropolitan Museum's iconic mounted knight displays."
        ),
        "Viking Weapon Finds": (
            "Archaeological discoveries that illuminate the Viking warrior world: ship "
            "burials, fortress garrisons, battlefield hoards, and the only complete "
            "Viking helmet ever found."
        ),
        "Chinese & Asian Weapons Heritage": (
            "From the Terracotta Army's 40,000 bronze weapons to the sacred kris forges "
            "of Indonesia, Asian weapons heritage spans thousands of years and a vast "
            "diversity of martial traditions."
        ),
        "Gunpowder & Firearms Origins": (
            "Follow the journey of gunpowder from 9th-century Chinese alchemists to "
            "the arms factories of modern Europe. The invention that transformed warfare "
            "forever started with Taoist monks seeking immortality."
        ),
        "Ancient Siege Warfare Sites": (
            "The greatest sieges in history: Roman circumvallations, Crusader assaults, "
            "Ottoman bombardments, and the 21-year siege of Candia. Siege warfare was "
            "the ultimate test of engineering, endurance, and willpower."
        ),
    }

    st.markdown(
        f'<div style="background:{_SURFACE};border:1px solid #2a3550;border-radius:8px;'
        f'padding:14px 18px;margin:8px 0 12px;color:{_TEXT};font-size:14px;line-height:1.5;">'
        f'{_DESCRIPTIONS.get(mode, "")}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ---- Map ----
    zoom = 4 if mode == "Japanese Katana Forges" else 2
    m = _build_map(data, cfg, zoom=zoom)
    st_html(m._repr_html_(), height=500)

    # ---- Dataframe ----
    st.markdown(
        f"#### Data Table: {mode}",
    )

    # Build a clean dataframe from the dataset
    df_records = []
    for entry in data:
        row = {"Name": entry["name"], "Latitude": entry["lat"], "Longitude": entry["lon"]}
        for field, label in zip(cfg["fields"], cfg["labels"]):
            row[label] = entry.get(field, "N/A")
        df_records.append(row)

    df = pd.DataFrame(df_records)
    st.dataframe(df, use_container_width=True)

    # ---- CSV Download ----
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    st.download_button(
        label=f"Download {mode} CSV",
        data=csv_bytes,
        file_name=f"ancient_weapons_{mode.lower().replace(' ', '_').replace('&', 'and')}.csv",
        mime="text/csv",
        key=f"dl_ancient_weapons_{mode}",
    )

    # ---- Country / Region breakdown ----
    st.markdown("#### Regional Breakdown")
    key_label = "Region" if mode == "Japanese Katana Forges" else "Country"
    breakdown_df = (
        pd.DataFrame(
            [(k, v) for k, v in sorted(country_stats.items(), key=lambda x: -x[1])]
        )
        .rename(columns={0: key_label, 1: "Count"})
    )
    st.dataframe(breakdown_df, use_container_width=True)

    # ---- Footer ----
    st.markdown("---")
    st.caption(
        "Data is curated from historical records, archaeological publications, "
        "and museum catalogs. Coordinates are approximate for historical sites. "
        "Sources include the Royal Armouries, Metropolitan Museum of Art, "
        "UNESCO Intangible Cultural Heritage lists, and peer-reviewed archaeology journals."
    )
