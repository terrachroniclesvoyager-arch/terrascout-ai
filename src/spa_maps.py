# -*- coding: utf-8 -*-
"""
Hot Springs & Spa Maps module for TerraScout AI.
Provides 10 interactive map modes covering Japanese onsen, Roman baths,
Icelandic geothermal pools, European spa towns, US hot springs,
Turkish hammams, New Zealand geothermal, South American thermal baths,
African hot springs, and Asian hot springs.

All data is hardcoded/curated. No API keys required.
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

# ═══════════════════════════════════════════════════════════════
# CONSTANTS & COLOR PALETTE
# ═══════════════════════════════════════════════════════════════
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"
BORDER = "#2a3550"
ACCENT = "#06b6d4"

MAP_MODES = [
    "1. Japanese Onsen",
    "2. Roman Baths & Ancient Thermae",
    "3. Iceland Geothermal",
    "4. European Spa Towns",
    "5. Yellowstone & US Hot Springs",
    "6. Turkish Hammam",
    "7. New Zealand Geothermal",
    "8. South American Hot Springs",
    "9. African Hot Springs",
    "10. Asian Hot Springs",
]

# ═══════════════════════════════════════════════════════════════
# MODE COLORS
# ═══════════════════════════════════════════════════════════════
MODE_COLORS = {
    "onsen": "#ef4444",
    "roman": "#f59e0b",
    "iceland": "#3b82f6",
    "europe": "#8b5cf6",
    "us": "#10b981",
    "hammam": "#f97316",
    "nz": "#22d3ee",
    "south_america": "#ec4899",
    "africa": "#a855f7",
    "asia": "#06b6d4",
}

# ═══════════════════════════════════════════════════════════════
# 1. JAPANESE ONSEN DATA (25+)
# ═══════════════════════════════════════════════════════════════
JAPANESE_ONSEN = [
    {"name": "Beppu Onsen", "lat": 33.2846, "lon": 131.4914, "prefecture": "Oita", "type": "Multiple springs", "temp_c": 98, "specialty": "8 major hot spring areas (Beppu Hatto); largest volume in Japan", "rating": 5},
    {"name": "Kusatsu Onsen", "lat": 36.6217, "lon": 138.5960, "prefecture": "Gunma", "type": "Sulfur/Acid", "temp_c": 65, "specialty": "Yubatake (hot water field); water-cooling yumomi tradition", "rating": 5},
    {"name": "Hakone Onsen", "lat": 35.2326, "lon": 139.1070, "prefecture": "Kanagawa", "type": "Multiple springs", "temp_c": 80, "specialty": "17 distinct spring types; views of Mt Fuji; Owakudani volcanic valley", "rating": 5},
    {"name": "Noboribetsu Onsen", "lat": 42.4934, "lon": 141.1849, "prefecture": "Hokkaido", "type": "Sulfur/Multiple", "temp_c": 90, "specialty": "Jigokudani (Hell Valley); 9 types of hot spring water", "rating": 5},
    {"name": "Dogo Onsen", "lat": 33.8530, "lon": 132.7882, "prefecture": "Ehime", "type": "Alkaline simple", "temp_c": 46, "specialty": "Oldest onsen in Japan (3000+ years); inspired Spirited Away bathhouse", "rating": 5},
    {"name": "Kurokawa Onsen", "lat": 33.1089, "lon": 131.1022, "prefecture": "Kumamoto", "type": "Sulfate/Chloride", "temp_c": 80, "specialty": "Charming mountain village; rotenburo (outdoor baths) passport system", "rating": 5},
    {"name": "Kinosaki Onsen", "lat": 35.6270, "lon": 134.8100, "prefecture": "Hyogo", "type": "Chloride", "temp_c": 73, "specialty": "7 public bathhouses along willow-lined canal; yukata strolling tradition", "rating": 5},
    {"name": "Gero Onsen", "lat": 35.8064, "lon": 137.2448, "prefecture": "Gifu", "type": "Alkaline simple", "temp_c": 84, "specialty": "One of Japan's top 3 onsen; silky smooth water; riverside baths", "rating": 5},
    {"name": "Arima Onsen", "lat": 34.7972, "lon": 135.2470, "prefecture": "Hyogo", "type": "Iron/Sodium chloride", "temp_c": 98, "specialty": "Kin-no-yu (gold bath, iron-rich) and Gin-no-yu (silver bath, carbonated)", "rating": 5},
    {"name": "Ibusuki Onsen", "lat": 31.2293, "lon": 130.6412, "prefecture": "Kagoshima", "type": "Sand bath", "temp_c": 55, "specialty": "Unique sunamushi (sand bath) on beach; naturally heated volcanic sand", "rating": 4},
    {"name": "Nyuto Onsen", "lat": 39.7878, "lon": 140.7549, "prefecture": "Akita", "type": "Sulfur/Milky", "temp_c": 60, "specialty": "7 secluded rustic ryokan; Tsurunoyu 350-year-old milky white bath", "rating": 5},
    {"name": "Ginzan Onsen", "lat": 38.5694, "lon": 140.3183, "prefecture": "Yamagata", "type": "Sodium chloride", "temp_c": 64, "specialty": "Taisho-era wooden ryokan along river; magical snow-lit winter scenery", "rating": 5},
    {"name": "Naruko Onsen", "lat": 38.7311, "lon": 140.7250, "prefecture": "Miyagi", "type": "Multiple (8 types)", "temp_c": 95, "specialty": "8 of Japan's 11 spring classifications; kokeshi doll birthplace", "rating": 4},
    {"name": "Shirahama Onsen", "lat": 33.6825, "lon": 135.3467, "prefecture": "Wakayama", "type": "Sodium chloride", "temp_c": 78, "specialty": "1350+ year history; seaside rotenburo at Saki-no-yu", "rating": 4},
    {"name": "Zao Onsen", "lat": 38.1667, "lon": 140.3978, "prefecture": "Yamagata", "type": "Sulfur/Acid", "temp_c": 52, "specialty": "Strong acid sulfur spring; famous snow monsters (juhyo) in winter", "rating": 4},
    {"name": "Atami Onsen", "lat": 35.0964, "lon": 139.0714, "prefecture": "Shizuoka", "type": "Chloride/Sulfate", "temp_c": 63, "specialty": "Resort town overlooking Sagami Bay; fireworks and plum festivals", "rating": 4},
    {"name": "Yufuin Onsen", "lat": 33.2631, "lon": 131.3694, "prefecture": "Oita", "type": "Simple thermal", "temp_c": 60, "specialty": "Artistic resort village; Lake Kinrin morning mist; gallery cafes", "rating": 5},
    {"name": "Nozawa Onsen", "lat": 36.9222, "lon": 138.6303, "prefecture": "Nagano", "type": "Sulfur/Sodium", "temp_c": 90, "specialty": "13 free public bathhouses (sotoyu); fire festival (Dosojin) in January", "rating": 4},
    {"name": "Jozankei Onsen", "lat": 42.9689, "lon": 141.1647, "prefecture": "Hokkaido", "type": "Sodium chloride", "temp_c": 72, "specialty": "Sapporo's inner parlor; autumn foliage; kappa (water sprite) statues", "rating": 4},
    {"name": "Shibu Onsen", "lat": 36.7366, "lon": 138.4281, "prefecture": "Nagano", "type": "Multiple springs", "temp_c": 63, "specialty": "9 free public baths stamp rally; snow monkeys nearby at Jigokudani", "rating": 4},
    {"name": "Tamatsukuri Onsen", "lat": 35.4106, "lon": 132.9919, "prefecture": "Shimane", "type": "Sulfate/Chloride", "temp_c": 65, "specialty": "Beauty spring (bihada-no-yu); ancient magatama bead-making site", "rating": 4},
    {"name": "Unzen Onsen", "lat": 32.7500, "lon": 130.2628, "prefecture": "Nagasaki", "type": "Sulfur/Acid", "temp_c": 95, "specialty": "Unzen Jigoku (hells); site of Christian martyr persecution; national park", "rating": 4},
    {"name": "Misasa Onsen", "lat": 35.3856, "lon": 133.8806, "prefecture": "Tottori", "type": "Radium/Radon", "temp_c": 65, "specialty": "World-class radon concentration; believed to boost immunity", "rating": 4},
    {"name": "Okuhida Onsen", "lat": 36.2800, "lon": 137.5500, "prefecture": "Gifu", "type": "Simple thermal", "temp_c": 72, "specialty": "5 villages in Northern Alps; largest number of rotenburo in Japan", "rating": 4},
    {"name": "Takaragawa Onsen", "lat": 36.8333, "lon": 139.0500, "prefecture": "Gunma", "type": "Simple alkaline", "temp_c": 63, "specialty": "Massive riverside konyoku (mixed) outdoor baths; deep mountain setting", "rating": 5},
    {"name": "Tsumagoi/Manza Onsen", "lat": 36.6392, "lon": 138.5325, "prefecture": "Gunma", "type": "Sulfur", "temp_c": 80, "specialty": "Highest-altitude onsen resort in Japan (1800m); milky sulfur water", "rating": 4},
]

# ═══════════════════════════════════════════════════════════════
# 2. ROMAN BATHS & ANCIENT THERMAE DATA (20+)
# ═══════════════════════════════════════════════════════════════
ROMAN_BATHS = [
    {"name": "Roman Baths (Aquae Sulis)", "lat": 51.3811, "lon": -2.3590, "country": "United Kingdom", "era": "1st century AD", "type": "Sacred thermal spring", "temp_c": 46, "notes": "Best-preserved Roman bathing complex in northern Europe; dedicated to goddess Sulis Minerva", "status": "Museum"},
    {"name": "Terme di Caracalla", "lat": 41.8790, "lon": 12.4923, "country": "Italy", "era": "217 AD", "type": "Imperial thermae", "temp_c": 0, "notes": "Could hold 1600 bathers; libraries, gardens, art galleries; model for Penn Station NYC", "status": "Ruins"},
    {"name": "Terme di Diocleziano", "lat": 41.9032, "lon": 12.4984, "country": "Italy", "era": "306 AD", "type": "Imperial thermae", "temp_c": 0, "notes": "Largest Roman baths ever built (13 hectares); now houses Museo Nazionale Romano", "status": "Museum"},
    {"name": "Hierapolis & Pamukkale", "lat": 37.9204, "lon": 29.1192, "country": "Turkey", "era": "2nd century BC", "type": "Sacred thermal city", "temp_c": 36, "notes": "White travertine terraces; Cleopatra's Pool; UNESCO World Heritage Site", "status": "Active/Museum"},
    {"name": "Gellert Thermal Bath", "lat": 47.4834, "lon": 19.0530, "country": "Hungary", "era": "13th century (Ottoman expansion)", "type": "Art Nouveau thermal", "temp_c": 47, "notes": "Stunning Art Nouveau architecture; wave pool; 13 thermal pools", "status": "Active"},
    {"name": "Szechenyi Thermal Bath", "lat": 47.5186, "lon": 19.0816, "country": "Hungary", "era": "1913", "type": "Neo-Baroque thermal", "temp_c": 77, "notes": "Largest medicinal bath in Europe; iconic yellow Neo-Baroque building; 18 pools", "status": "Active"},
    {"name": "Rudas Thermal Bath", "lat": 47.4864, "lon": 19.0467, "country": "Hungary", "era": "1550 (Ottoman)", "type": "Ottoman thermal", "temp_c": 42, "notes": "Ottoman-era octagonal pool under domed roof; rooftop pool with city panorama", "status": "Active"},
    {"name": "Hammam al-Ain (Gadara)", "lat": 32.6564, "lon": 35.6767, "country": "Jordan", "era": "2nd century AD", "type": "Roman-Byzantine baths", "temp_c": 51, "notes": "Ancient Gadara thermae; natural hot waterfall; still used for bathing", "status": "Active"},
    {"name": "Thermes de Cluny", "lat": 48.8508, "lon": 2.3443, "country": "France", "era": "1st-3rd century AD", "type": "Gallo-Roman thermae", "temp_c": 0, "notes": "Best-preserved Roman baths in Paris (Lutetia); now Musee de Cluny", "status": "Museum"},
    {"name": "Baths of Trajan", "lat": 41.8928, "lon": 12.4959, "country": "Italy", "era": "109 AD", "type": "Imperial thermae", "temp_c": 0, "notes": "Built atop Nero's Domus Aurea; Apollodorus of Damascus designed them", "status": "Ruins"},
    {"name": "Terme Taurine (Civitavecchia)", "lat": 42.0833, "lon": 11.7667, "country": "Italy", "era": "2nd century BC", "type": "Republican thermae", "temp_c": 37, "notes": "Both Republican and Imperial-era bath complexes; natural sulfur springs", "status": "Ruins/Active"},
    {"name": "Roman Baths of Ankara", "lat": 39.9436, "lon": 32.8648, "country": "Turkey", "era": "3rd century AD", "type": "Roman provincial baths", "temp_c": 0, "notes": "Built under Emperor Caracalla; standard Roman plan with frigidarium, tepidarium, caldarium", "status": "Ruins"},
    {"name": "Aquae Helveticae (Baden)", "lat": 47.4734, "lon": 8.3064, "country": "Switzerland", "era": "1st century AD", "type": "Roman legionary baths", "temp_c": 47, "notes": "Roman garrison town hot springs; 18 thermal springs still active today", "status": "Active"},
    {"name": "Aquae Granni (Aachen)", "lat": 50.7753, "lon": 6.0839, "country": "Germany", "era": "1st century AD", "type": "Roman thermal settlement", "temp_c": 74, "notes": "Hottest springs north of Alps; Charlemagne's capital; Carolus Thermen spa", "status": "Active"},
    {"name": "Thermae of Antoninus (Carthage)", "lat": 36.8575, "lon": 10.3265, "country": "Tunisia", "era": "145-162 AD", "type": "Imperial thermae", "temp_c": 0, "notes": "Largest Roman baths in Africa; massive columns still standing; UNESCO site", "status": "Ruins"},
    {"name": "Leptis Magna Baths", "lat": 32.6386, "lon": 14.2927, "country": "Libya", "era": "2nd century AD", "type": "Hadrianic thermae", "temp_c": 0, "notes": "Hunting Baths with remarkable painted vaults; Emperor Septimius Severus' hometown", "status": "Ruins"},
    {"name": "Butrint Roman Baths", "lat": 39.7444, "lon": 20.0208, "country": "Albania", "era": "2nd century AD", "type": "Roman provincial baths", "temp_c": 0, "notes": "Part of UNESCO-listed Butrint archaeological site; well-preserved hypocaust system", "status": "Ruins"},
    {"name": "Stabian Baths (Pompeii)", "lat": 40.7492, "lon": 14.4886, "country": "Italy", "era": "2nd century BC", "type": "Republican thermae", "temp_c": 0, "notes": "Oldest baths in Pompeii; preserved by Vesuvius eruption in 79 AD; stucco decorations", "status": "Museum"},
    {"name": "Roman Baths of Fordongianus", "lat": 39.9947, "lon": 8.8100, "country": "Italy (Sardinia)", "era": "1st century AD", "type": "Roman provincial baths", "temp_c": 54, "notes": "Forum Traiani hot springs; still active thermal pool beside Roman ruins", "status": "Active/Ruins"},
    {"name": "Hammam Essalihine (Khenchela)", "lat": 35.3644, "lon": 7.0894, "country": "Algeria", "era": "1st century AD (Roman)", "type": "Roman thermal baths", "temp_c": 70, "notes": "Remarkably intact Roman bath still in public use; Aquae Flavianae of antiquity", "status": "Active"},
    {"name": "Thermal Baths of Varna", "lat": 43.2078, "lon": 27.9169, "country": "Bulgaria", "era": "2nd century AD", "type": "Roman provincial thermae", "temp_c": 55, "notes": "Largest Roman thermae in the Balkans; now Archaeological Museum of Varna", "status": "Museum"},
]

# ═══════════════════════════════════════════════════════════════
# 3. ICELAND GEOTHERMAL DATA (15+)
# ═══════════════════════════════════════════════════════════════
ICELAND_GEOTHERMAL = [
    {"name": "Blue Lagoon", "lat": 63.8804, "lon": -22.4495, "region": "Reykjanes", "type": "Geothermal spa", "temp_c": 39, "notes": "Iconic milky-blue silica-rich water; fed by Svartsengi power station runoff", "cost": "High"},
    {"name": "Myvatn Nature Baths", "lat": 65.6311, "lon": -16.8471, "region": "Northeast", "type": "Geothermal lagoon", "temp_c": 40, "notes": "North's answer to Blue Lagoon; silica and sulfur rich; lake views", "cost": "Moderate"},
    {"name": "Landmannalaugar", "lat": 63.9930, "lon": -19.0625, "region": "Highlands", "type": "Natural hot river", "temp_c": 40, "notes": "Colorful rhyolite mountains; hot river mixing geothermal and cold streams", "cost": "Free"},
    {"name": "Secret Lagoon (Gamla Laugin)", "lat": 64.1378, "lon": -20.3100, "region": "South", "type": "Natural hot spring", "temp_c": 40, "notes": "Oldest swimming pool in Iceland (1891); small geysers nearby; rustic charm", "cost": "Moderate"},
    {"name": "Seljavallalaug", "lat": 63.5656, "lon": -19.6072, "region": "South", "type": "Mountain pool", "temp_c": 30, "notes": "Hidden 25m pool built in 1923; tucked into valley below Eyjafjallajokull", "cost": "Free"},
    {"name": "Sky Lagoon", "lat": 64.1025, "lon": -22.0167, "region": "Reykjavik", "type": "Geothermal spa", "temp_c": 39, "notes": "Infinity-edge oceanfront pool; 7-step spa ritual; opened 2021", "cost": "High"},
    {"name": "Reykjadalur Hot Spring River", "lat": 64.0350, "lon": -21.2117, "region": "South", "type": "Natural hot river", "temp_c": 38, "notes": "45-minute hike to steaming river valley; free wild bathing", "cost": "Free"},
    {"name": "Vok Baths", "lat": 65.2645, "lon": -14.3958, "region": "East", "type": "Floating geothermal", "temp_c": 40, "notes": "Floating infinity pools on Lake Urridavatn; first of their kind in Iceland", "cost": "Moderate"},
    {"name": "Krauma Geothermal Baths", "lat": 64.6647, "lon": -21.4167, "region": "West", "type": "Geothermal spa", "temp_c": 40, "notes": "Fed by Deildartunguhver, Europe's most powerful hot spring (180 L/sec)", "cost": "Moderate"},
    {"name": "Hveravellir", "lat": 64.8633, "lon": -19.5567, "region": "Highlands", "type": "Highland hot pot", "temp_c": 40, "notes": "Remote highland oasis between two glaciers; fumaroles and blue pools", "cost": "Free"},
    {"name": "Hofsos Infinity Pool", "lat": 65.8856, "lon": -19.4167, "region": "North", "type": "Municipal pool", "temp_c": 38, "notes": "Dramatic cliff-edge infinity pool overlooking Skagafjordur fjord", "cost": "Low"},
    {"name": "GeoSea Husavik", "lat": 66.0456, "lon": -17.3394, "region": "North", "type": "Sea geothermal baths", "temp_c": 39, "notes": "Infinity pools with panoramic Arctic Ocean views; whale watching town", "cost": "Moderate"},
    {"name": "Laugarvatn Fontana", "lat": 64.2139, "lon": -20.7275, "region": "South", "type": "Lakeside geothermal", "temp_c": 42, "notes": "Steam rooms built over natural hot springs; rye bread baked underground", "cost": "Moderate"},
    {"name": "Gudrunarlaug", "lat": 65.1458, "lon": -21.1667, "region": "West", "type": "Saga-era pool", "temp_c": 39, "notes": "Reconstructed viking-age pool from Laxdaela Saga; free open-air bathing", "cost": "Free"},
    {"name": "Hvammsvik Hot Springs", "lat": 64.4000, "lon": -21.6167, "region": "West", "type": "Oceanside hot pots", "temp_c": 41, "notes": "8 ocean-side geothermal pools with tidal influence; opened 2022", "cost": "Moderate"},
    {"name": "Strokkur & Geysir Area", "lat": 64.3103, "lon": -20.3022, "region": "South", "type": "Geyser field", "temp_c": 100, "notes": "Strokkur erupts every 6-10 minutes; original Geysir (namesake of all geysers)", "cost": "Free"},
    {"name": "Drangsnes Hot Pots", "lat": 65.6919, "lon": -21.4469, "region": "Westfjords", "type": "Seaside hot pots", "temp_c": 42, "notes": "Three free oceanside stone hot tubs in tiny fishing village", "cost": "Free"},
]

# ═══════════════════════════════════════════════════════════════
# 4. EUROPEAN SPA TOWNS DATA (20+)
# ═══════════════════════════════════════════════════════════════
EUROPEAN_SPA_TOWNS = [
    {"name": "Baden-Baden", "lat": 48.7620, "lon": 8.2409, "country": "Germany", "founded": "Roman era", "specialty": "Friedrichsbad Roman-Irish bath; Caracalla Therme; casino town", "famous_water": "Sodium chloride thermal", "temp_c": 68, "unesco": True},
    {"name": "Karlovy Vary (Carlsbad)", "lat": 50.2297, "lon": 12.8714, "country": "Czech Republic", "founded": "1370", "specialty": "13 major hot springs; colonnades; drinking cure tradition; film festival", "famous_water": "Bicarbonate-sulfate-sodium", "temp_c": 73, "unesco": True},
    {"name": "Vichy", "lat": 46.1279, "lon": 3.4258, "country": "France", "founded": "Roman era", "specialty": "5 thermal springs; Celestins source; Art Deco architecture; skincare brand origin", "famous_water": "Bicarbonate-sodium", "temp_c": 43, "unesco": True},
    {"name": "Evian-les-Bains", "lat": 46.4011, "lon": 6.5886, "country": "France", "founded": "1789", "specialty": "Source of Evian water; Lake Geneva views; Palais Lumiere cultural center", "famous_water": "Calcium-bicarbonate", "temp_c": 11, "unesco": False},
    {"name": "Montecatini Terme", "lat": 43.8833, "lon": 10.7703, "country": "Italy", "founded": "14th century", "specialty": "Tettuccio grand spa; 8 thermal establishments; Liberty-style architecture", "famous_water": "Saline-sulfate-alkaline", "temp_c": 34, "unesco": True},
    {"name": "Budapest", "lat": 47.4979, "lon": 19.0402, "country": "Hungary", "founded": "Roman/Ottoman era", "specialty": "City of Spas: Szechenyi, Gellert, Rudas, Kiraly; 120+ natural springs", "famous_water": "Calcium-magnesium-bicarbonate", "temp_c": 77, "unesco": False},
    {"name": "Spa (Belgium)", "lat": 50.4878, "lon": 5.8661, "country": "Belgium", "founded": "14th century", "specialty": "Original namesake of all spas worldwide; Peter the Great visited; Pouhon Pierre", "famous_water": "Iron-bicarbonate", "temp_c": 14, "unesco": True},
    {"name": "Bath", "lat": 51.3811, "lon": -2.3590, "country": "United Kingdom", "founded": "Roman era (Aquae Sulis)", "specialty": "Roman Baths museum; Thermae Bath Spa rooftop pool; Georgian architecture", "famous_water": "Calcium-sulfate", "temp_c": 46, "unesco": True},
    {"name": "Marianske Lazne (Marienbad)", "lat": 49.9647, "lon": 12.7011, "country": "Czech Republic", "founded": "1808", "specialty": "40 mineral springs; Singing Fountain; Goethe and Chopin visited", "famous_water": "Cold acidulous springs", "temp_c": 10, "unesco": True},
    {"name": "Frantiskovy Lazne (Franzensbad)", "lat": 50.1203, "lon": 12.3519, "country": "Czech Republic", "founded": "1793", "specialty": "Oldest peat-bath spa in Czech Republic; fertility springs; elegant parks", "famous_water": "Sulfate-sodium-bicarbonate", "temp_c": 15, "unesco": True},
    {"name": "San Pellegrino Terme", "lat": 45.8339, "lon": 9.6567, "country": "Italy", "founded": "16th century", "specialty": "Grand Hotel & Casino; source of San Pellegrino mineral water", "famous_water": "Calcium-sulfate-bicarbonate", "temp_c": 26, "unesco": False},
    {"name": "Leukerbad", "lat": 46.3833, "lon": 7.6333, "country": "Switzerland", "founded": "Roman era", "specialty": "Largest alpine thermal resort; Gemmi Pass; 3.9 million liters daily", "famous_water": "Calcium-sulfate", "temp_c": 51, "unesco": False},
    {"name": "Saturnia", "lat": 42.6500, "lon": 11.5147, "country": "Italy", "founded": "Etruscan era", "specialty": "Cascate del Mulino free waterfall pools; sulfurous blue water; open 24/7", "famous_water": "Sulfurous thermal", "temp_c": 37, "unesco": False},
    {"name": "Fiuggi", "lat": 41.7986, "lon": 13.2261, "country": "Italy", "founded": "Medieval", "specialty": "Oligomineral water for kidney stones; Michelangelo praised the water", "famous_water": "Oligomineral", "temp_c": 15, "unesco": False},
    {"name": "Wiesbaden", "lat": 50.0782, "lon": 8.2398, "country": "Germany", "founded": "Roman era", "specialty": "26 hot springs; Kaiser Friedrich Therme; Kochbrunnen (66C fountain)", "famous_water": "Sodium chloride", "temp_c": 66, "unesco": False},
    {"name": "Harrogate", "lat": 53.9921, "lon": -1.5418, "country": "United Kingdom", "founded": "16th century", "specialty": "Royal Pump Room Museum; Turkish Baths; 88 mineral springs; Victorian spa town", "famous_water": "Sulfur/Iron/Magnesia", "temp_c": 14, "unesco": False},
    {"name": "Bad Gastein", "lat": 47.1133, "lon": 13.1319, "country": "Austria", "founded": "15th century", "specialty": "Alpine waterfall through town center; radon thermal tunnels (Gasteiner Heilstollen)", "famous_water": "Radon thermal", "temp_c": 47, "unesco": False},
    {"name": "Rogaska Slatina", "lat": 46.2378, "lon": 15.6397, "country": "Slovenia", "founded": "17th century", "specialty": "Highest magnesium-content water in the world; crystal glass tradition", "famous_water": "Magnesium-bicarbonate", "temp_c": 13, "unesco": False},
    {"name": "Piestany", "lat": 48.5947, "lon": 17.8250, "country": "Slovakia", "founded": "1889", "specialty": "Thermal mud treatments on Spa Island in the Vah River; crutch-breaker statue", "famous_water": "Sulfate-calcium thermal", "temp_c": 67, "unesco": False},
    {"name": "Abano Terme", "lat": 45.3578, "lon": 11.7906, "country": "Italy", "founded": "Roman era", "specialty": "Euganean Hills thermal district; fango (volcanic mud) therapy center of Europe", "famous_water": "Saline-bromine-iodine", "temp_c": 87, "unesco": False},
    {"name": "Luchon (Bagneres-de-Luchon)", "lat": 42.7911, "lon": 0.5936, "country": "France", "founded": "Roman era", "specialty": "Queen of the Pyrenees; Vaporarium natural sulfur vapor cave; ski and spa", "famous_water": "Sulfurous sodium", "temp_c": 65, "unesco": False},
]

# ═══════════════════════════════════════════════════════════════
# 5. YELLOWSTONE & US HOT SPRINGS DATA (20+)
# ═══════════════════════════════════════════════════════════════
US_HOT_SPRINGS = [
    {"name": "Grand Prismatic Spring", "lat": 44.5251, "lon": -110.8382, "state": "Wyoming", "type": "Hydrothermal spring", "temp_c": 87, "notes": "Largest hot spring in USA; rainbow microbial mats; Yellowstone icon", "access": "Viewing only"},
    {"name": "Old Faithful Geyser", "lat": 44.4605, "lon": -110.8281, "state": "Wyoming", "type": "Geyser", "temp_c": 96, "notes": "Erupts every 44-125 minutes; 32,000-56,000 liters per eruption", "access": "Viewing only"},
    {"name": "Mammoth Hot Springs", "lat": 44.9725, "lon": -110.7044, "state": "Wyoming", "type": "Travertine terraces", "temp_c": 73, "notes": "Largest carbonate-depositing spring in the world; terraced limestone", "access": "Viewing only"},
    {"name": "Morning Glory Pool", "lat": 44.4658, "lon": -110.8438, "state": "Wyoming", "type": "Hot spring pool", "temp_c": 72, "notes": "Deep blue center with yellow-orange bacterial rim; coin-tossing cooled it", "access": "Viewing only"},
    {"name": "Hot Springs (Bathhouse Row)", "lat": 34.5133, "lon": -93.0524, "state": "Arkansas", "type": "Thermal bathhouses", "temp_c": 62, "notes": "National Park with 8 historic bathhouses; 4000-year-old thermal water", "access": "Public bathing"},
    {"name": "Glenwood Hot Springs", "lat": 39.5464, "lon": -107.3236, "state": "Colorado", "type": "Natural hot pool", "temp_c": 52, "notes": "World's largest hot springs pool (405 feet long); Ute Indian heritage", "access": "Public bathing"},
    {"name": "Ojo Caliente", "lat": 36.3108, "lon": -106.0514, "state": "New Mexico", "type": "Mineral springs resort", "temp_c": 43, "notes": "Only place in the world with 5 geologically distinct springs together", "access": "Public bathing"},
    {"name": "Dunton Hot Springs", "lat": 37.7692, "lon": -108.0953, "state": "Colorado", "type": "Luxury ghost town resort", "temp_c": 42, "notes": "Restored 1800s mining ghost town turned luxury hot springs resort", "access": "Guests only"},
    {"name": "Strawberry Park Hot Springs", "lat": 40.5581, "lon": -106.8350, "state": "Colorado", "type": "Natural hot pools", "temp_c": 40, "notes": "Rustic stone pools in the forest near Steamboat Springs; clothing-optional at night", "access": "Public bathing"},
    {"name": "Chena Hot Springs", "lat": 65.0528, "lon": -146.0558, "state": "Alaska", "type": "Geothermal resort", "temp_c": 41, "notes": "Northern Lights viewing from hot pools; year-round Aurora Ice Museum", "access": "Public bathing"},
    {"name": "Travertine Hot Springs", "lat": 38.2036, "lon": -119.2103, "state": "California", "type": "Wild hot springs", "temp_c": 42, "notes": "Free natural travertine-formed pools with Sierra Nevada views", "access": "Free"},
    {"name": "Hot Creek Geological Site", "lat": 37.6614, "lon": -118.8289, "state": "California", "type": "Geothermal site", "temp_c": 93, "notes": "Boiling geothermal springs in creek; too dangerous to swim (closed 2006)", "access": "Viewing only"},
    {"name": "Pagosa Springs", "lat": 37.2697, "lon": -107.0098, "state": "Colorado", "type": "Deepest hot spring", "temp_c": 57, "notes": "Mother Spring is deepest geothermal spring in the world (over 300m)", "access": "Public bathing"},
    {"name": "Bozeman Hot Springs", "lat": 45.6019, "lon": -111.1778, "state": "Montana", "type": "Community hot springs", "temp_c": 42, "notes": "12 pools ranging from cool to hot; fitness and pool complex; live music", "access": "Public bathing"},
    {"name": "Lava Hot Springs", "lat": 42.6197, "lon": -112.0111, "state": "Idaho", "type": "Public hot pools", "temp_c": 49, "notes": "Five open-air mineral pools; no sulfur smell; Shoshone-Bannock sacred site", "access": "Public bathing"},
    {"name": "Orvis Hot Springs", "lat": 38.1564, "lon": -107.7403, "state": "Colorado", "type": "Natural springs", "temp_c": 41, "notes": "Clothing-optional; 6 outdoor and 2 indoor soaking pools near Ouray", "access": "Public bathing"},
    {"name": "Yellowstone Hot Springs (Gardiner)", "lat": 45.0311, "lon": -110.7147, "state": "Montana", "type": "Modern hot springs", "temp_c": 42, "notes": "Cold plunge to hot pools; near north entrance of Yellowstone", "access": "Public bathing"},
    {"name": "Conundrum Hot Springs", "lat": 39.0036, "lon": -106.8547, "state": "Colorado", "type": "Backcountry hot spring", "temp_c": 38, "notes": "8.5-mile hike to pools at 11,200 ft elevation; permit required", "access": "Hiking only"},
    {"name": "Ten Thousand Waves", "lat": 35.7136, "lon": -105.9014, "state": "New Mexico", "type": "Japanese-style spa", "temp_c": 41, "notes": "Japanese-style mountain spa near Santa Fe; private and communal tubs", "access": "Public bathing"},
    {"name": "Breitenbush Hot Springs", "lat": 44.7789, "lon": -121.9706, "state": "Oregon", "type": "Retreat center", "temp_c": 44, "notes": "Clothing-optional geothermal springs in old-growth forest; meditation retreats", "access": "Guests/Day use"},
    {"name": "Sol Duc Hot Springs", "lat": 47.9686, "lon": -123.8608, "state": "Washington", "type": "National Park springs", "temp_c": 41, "notes": "Three mineral pools in Olympic National Park; old-growth rainforest setting", "access": "Public bathing"},
]

# ═══════════════════════════════════════════════════════════════
# 6. TURKISH HAMMAM DATA (15+)
# ═══════════════════════════════════════════════════════════════
TURKISH_HAMMAM = [
    {"name": "Cemberlitas Hamami", "lat": 41.0083, "lon": 28.9711, "city": "Istanbul", "era": "1584", "architect": "Mimar Sinan", "type": "Historic Ottoman", "notes": "Designed by great architect Sinan; dual male/female sections; iconic dome", "status": "Active"},
    {"name": "Hurrem Sultan Hamami", "lat": 41.0065, "lon": 28.9795, "city": "Istanbul", "era": "1557", "architect": "Mimar Sinan", "type": "Historic Ottoman", "notes": "Between Hagia Sophia and Blue Mosque; built for Suleiman's wife Roxelana", "status": "Active"},
    {"name": "Kilic Ali Pasa Hamami", "lat": 41.0261, "lon": 28.9819, "city": "Istanbul", "era": "1580", "architect": "Mimar Sinan", "type": "Historic Ottoman", "notes": "Meticulously restored 2012; designed by Sinan for naval commander Kilic Ali Pasa", "status": "Active"},
    {"name": "Cagaloglu Hamami", "lat": 41.0117, "lon": 28.9728, "city": "Istanbul", "era": "1741", "architect": "Unknown (Mahmud I era)", "type": "Historic Ottoman", "notes": "Last great hammam of the Ottoman period; featured in 1001 Places to See Before You Die", "status": "Active"},
    {"name": "Suleymaniye Hamami", "lat": 41.0158, "lon": 28.9639, "city": "Istanbul", "era": "1557", "architect": "Mimar Sinan", "type": "Historic Ottoman", "notes": "Part of Suleymaniye mosque complex; recently restored as luxury hammam", "status": "Active"},
    {"name": "Galatasaray Hamami", "lat": 41.0336, "lon": 28.9772, "city": "Istanbul", "era": "1481", "architect": "Bayezid II era", "type": "Historic Ottoman", "notes": "On bustling Istiklal Avenue; one of the oldest hammams in Istanbul", "status": "Active"},
    {"name": "Ayasofya Hurrem Sultan Hamami", "lat": 41.0064, "lon": 28.9793, "city": "Istanbul", "era": "1556", "architect": "Mimar Sinan", "type": "Luxury restored", "notes": "Premium luxury experience with marble massage and Ottoman treatments", "status": "Active"},
    {"name": "Safranbolu Historic Hammam", "lat": 41.2539, "lon": 32.6922, "city": "Safranbolu", "era": "17th century", "architect": "Unknown", "type": "Historic Ottoman", "notes": "In UNESCO-listed Safranbolu old town; Cinci Hamami from 1645", "status": "Active"},
    {"name": "Bursa Eski Kaplica", "lat": 40.1833, "lon": 29.0667, "city": "Bursa", "era": "14th century (possibly Roman)", "type": "Historic thermal", "architect": "Renovated by Murad I", "notes": "Possibly oldest continuously operating bath in Turkey; natural hot springs", "status": "Active"},
    {"name": "Bursa Yeni Kaplica", "lat": 40.1853, "lon": 29.0683, "city": "Bursa", "era": "1555", "architect": "Grand Vizier Rustem Pasha", "type": "Ottoman thermal", "notes": "Built with Rustem Pasha's tiles; feeds from 84C natural thermal source", "status": "Active"},
    {"name": "Iznik Roman-Ottoman Baths", "lat": 40.4286, "lon": 29.7222, "city": "Iznik (Nicaea)", "era": "Roman/Ottoman", "architect": "Multiple periods", "type": "Multi-era baths", "notes": "Layered Roman and Ottoman history; near where Nicene Creed was written", "status": "Ruins/Museum"},
    {"name": "Edirne Old Hamam (Sokollu)", "lat": 41.6772, "lon": 26.5558, "city": "Edirne", "era": "1569", "architect": "Mimar Sinan", "type": "Historic Ottoman", "notes": "Part of Sokollu complex in former Ottoman capital; large hexagonal hararet", "status": "Active"},
    {"name": "Tahtakale Hamami (Antalya)", "lat": 36.8847, "lon": 30.7053, "city": "Antalya", "era": "13th century (Seljuk)", "type": "Seljuk-Ottoman", "architect": "Unknown Seljuk", "notes": "In Antalya's old town Kaleici; Seljuk-era bath with later Ottoman additions", "status": "Active"},
    {"name": "Aga Hamami (Ankara)", "lat": 39.9386, "lon": 32.8547, "city": "Ankara", "era": "15th century", "architect": "Unknown", "type": "Historic Ottoman", "notes": "In Ankara citadel area; traditional neighborhood hammam still in daily use", "status": "Active"},
    {"name": "Vakiflar Hamami (Goreme)", "lat": 38.6431, "lon": 34.8303, "city": "Goreme (Cappadocia)", "era": "Ottoman era", "architect": "Unknown", "type": "Cappadocian hammam", "notes": "Unique hammam experience in fairy chimney landscape of Cappadocia", "status": "Active"},
    {"name": "Sengul Hamami (Ankara)", "lat": 39.9403, "lon": 32.8558, "city": "Ankara", "era": "15th century", "architect": "Unknown", "type": "Historic Ottoman", "notes": "600-year-old bath near Ankara Castle; continuous use since Ottoman founding", "status": "Active"},
]

# ═══════════════════════════════════════════════════════════════
# 7. NEW ZEALAND GEOTHERMAL DATA (15+)
# ═══════════════════════════════════════════════════════════════
NZ_GEOTHERMAL = [
    {"name": "Rotorua (Hell's Gate / Tikitere)", "lat": -38.2551, "lon": 176.3620, "island": "North", "type": "Geothermal reserve", "temp_c": 110, "notes": "Most active geothermal reserve in Rotorua; Maori-owned; mud baths and sulfur spa", "access": "Public"},
    {"name": "Polynesian Spa Rotorua", "lat": -38.1655, "lon": 176.2530, "island": "North", "type": "Lakeside thermal spa", "temp_c": 42, "notes": "Named among world's top 10 spas; 28 pools overlooking Lake Rotorua", "access": "Public"},
    {"name": "Wai-O-Tapu", "lat": -38.3556, "lon": 176.3694, "island": "North", "type": "Volcanic wonderland", "temp_c": 80, "notes": "Champagne Pool, Artist's Palette, Devil's Bath (bright green); Lady Knox Geyser", "access": "Public (viewing)"},
    {"name": "Lake Taupo Hot Stream", "lat": -38.7123, "lon": 176.0738, "island": "North", "type": "Natural hot creek", "temp_c": 38, "notes": "Free hot creek flowing into the Waikato River at Spa Thermal Park", "access": "Free"},
    {"name": "Hot Water Beach (Coromandel)", "lat": -36.8853, "lon": 175.8286, "island": "North", "type": "Geothermal beach", "temp_c": 64, "notes": "Dig your own hot pool in the sand at low tide; underground geothermal vents", "access": "Free"},
    {"name": "Hanmer Springs", "lat": -42.5228, "lon": 172.8289, "island": "South", "type": "Alpine thermal resort", "temp_c": 42, "notes": "South Island's premier thermal resort; 15+ pools; sulphur pools; waterslides", "access": "Public"},
    {"name": "Waimangu Volcanic Valley", "lat": -38.2833, "lon": 176.3833, "island": "North", "type": "Volcanic valley", "temp_c": 100, "notes": "World's youngest geothermal system (formed 1886); Inferno Crater Lake; Frying Pan Lake", "access": "Public (viewing)"},
    {"name": "Kerosene Creek", "lat": -38.3125, "lon": 176.2417, "island": "North", "type": "Wild hot stream", "temp_c": 38, "notes": "Free forest hot stream with waterfall; locals' favorite near Rotorua", "access": "Free"},
    {"name": "Tokaanu Thermal Pools", "lat": -38.9817, "lon": 175.7658, "island": "North", "type": "Public hot pools", "temp_c": 40, "notes": "Near Taupo; Maori village thermal walk; affordable public pools", "access": "Public"},
    {"name": "Te Puia (Whakarewarewa)", "lat": -38.1731, "lon": 176.2597, "island": "North", "type": "Geyser valley", "temp_c": 100, "notes": "Pohutu Geyser erupts up to 30m; NZ Maori Arts and Crafts Institute", "access": "Public"},
    {"name": "Orakei Korako", "lat": -38.4689, "lon": 176.1825, "island": "North", "type": "Geothermal terrace", "temp_c": 70, "notes": "Hidden Valley with NZ's largest silica terraces; Ruatapu Cave with hot pool", "access": "Public"},
    {"name": "Ngawha Springs", "lat": -35.4000, "lon": 173.8667, "island": "North", "type": "Wild thermal pools", "temp_c": 50, "notes": "Remote rustic Maori-managed hot springs in Northland; healing mud pools", "access": "Public"},
    {"name": "Welcome Flat Hot Springs", "lat": -43.5000, "lon": 170.1833, "island": "South", "type": "Backcountry hot pools", "temp_c": 40, "notes": "17km hike into Copland Valley; alpine DOC hut with natural hot pools", "access": "Hiking only"},
    {"name": "Maruia Hot Springs", "lat": -42.3750, "lon": 172.2000, "island": "South", "type": "Japanese-style onsen", "temp_c": 42, "notes": "Japanese-style thermal retreat in Lewis Pass; rock pools and forest bathing", "access": "Public"},
    {"name": "Waiotapu Mud Pool", "lat": -38.3650, "lon": 176.3697, "island": "North", "type": "Bubbling mud pool", "temp_c": 98, "notes": "Massive bubbling mud pool on roadside; free to view; thick gray volcanic mud", "access": "Free (viewing)"},
    {"name": "Parakai Hot Springs", "lat": -36.6667, "lon": 174.4500, "island": "North", "type": "Public thermal resort", "temp_c": 43, "notes": "Near Auckland; family-friendly pools and waterslides; geothermal heated", "access": "Public"},
]

# ═══════════════════════════════════════════════════════════════
# 8. SOUTH AMERICAN HOT SPRINGS DATA (15+)
# ═══════════════════════════════════════════════════════════════
SOUTH_AMERICAN_SPRINGS = [
    {"name": "Termas de Puritama", "lat": -22.8667, "lon": -68.0500, "country": "Chile", "type": "Desert hot pools", "temp_c": 33, "notes": "8 pools connected by wooden walkways in Atacama Desert canyon at 3500m elevation", "region": "Atacama"},
    {"name": "Termas Geometricas", "lat": -39.5117, "lon": -71.8625, "country": "Chile", "type": "Architectural hot springs", "temp_c": 42, "notes": "17 slate-lined pools with red wooden walkways through temperate rainforest ravine", "region": "Araucania"},
    {"name": "Aguas Calientes (Machu Picchu)", "lat": -13.1547, "lon": -72.5231, "country": "Peru", "type": "Village hot springs", "temp_c": 38, "notes": "Natural hot baths at gateway town to Machu Picchu; communal pools", "region": "Cusco"},
    {"name": "Termas de Cacheuta", "lat": -33.0167, "lon": -69.1333, "country": "Argentina", "type": "Andean thermal spa", "temp_c": 45, "notes": "Dramatic Andean canyon setting near Mendoza; 12 thermal pools and waterfalls", "region": "Mendoza"},
    {"name": "Termas del Plomo", "lat": -33.4167, "lon": -70.0500, "country": "Chile", "type": "Wild mountain springs", "temp_c": 50, "notes": "Remote high-altitude wild hot springs in the Andes near Santiago; glacier views", "region": "Santiago"},
    {"name": "Termas de Papallacta", "lat": -0.3667, "lon": -78.1333, "country": "Ecuador", "type": "Cloud forest thermal", "temp_c": 40, "notes": "High-altitude thermal resort in cloud forest at 3300m; near Antisana volcano", "region": "Napo"},
    {"name": "Banos de Agua Santa", "lat": -1.3964, "lon": -78.4247, "country": "Ecuador", "type": "Thermal town", "temp_c": 55, "notes": "Gateway to Amazon; Pailon del Diablo waterfall; Virgin of Holy Water basilica", "region": "Tungurahua"},
    {"name": "Termas de Chillan", "lat": -36.9042, "lon": -71.4167, "country": "Chile", "type": "Volcanic thermal resort", "temp_c": 45, "notes": "At base of Chillan Volcano; ski and soak; fumaroles visible from pools", "region": "Nuble"},
    {"name": "Laguna Colorada Hot Springs", "lat": -22.2000, "lon": -67.8000, "country": "Bolivia", "type": "Altiplano thermal", "temp_c": 38, "notes": "Hot springs near red mineral lake at 4300m; flamingos in surreal landscape", "region": "Potosi"},
    {"name": "Termas del Dayman", "lat": -31.6500, "lon": -57.3167, "country": "Uruguay", "type": "Public thermal resort", "temp_c": 44, "notes": "Uruguay's largest thermal park; Olympic pools and therapeutic baths", "region": "Salto"},
    {"name": "Termas de Puyehue", "lat": -40.6667, "lon": -72.3167, "country": "Chile", "type": "Rainforest thermal", "temp_c": 42, "notes": "Luxury thermal hotel in valdivian rainforest near Puyehue volcano", "region": "Los Lagos"},
    {"name": "Termas de Reyes", "lat": -24.2333, "lon": -65.4833, "country": "Argentina", "type": "Mountain thermal", "temp_c": 48, "notes": "Andean mountain spa near Jujuy; natural grotto pools in Quebrada de Humahuaca", "region": "Jujuy"},
    {"name": "Colca Canyon Hot Springs (La Calera)", "lat": -15.6167, "lon": -71.8333, "country": "Peru", "type": "Canyon hot springs", "temp_c": 40, "notes": "Thermal pools overlooking world's deepest canyon; Andean condor viewing", "region": "Arequipa"},
    {"name": "Lares Hot Springs", "lat": -13.1000, "lon": -72.0500, "country": "Peru", "type": "Inca trail hot springs", "temp_c": 42, "notes": "Stone-lined pools on alternative Inca Trail route; surrounded by Andean peaks", "region": "Cusco"},
    {"name": "Termas de Federacion", "lat": -31.0000, "lon": -57.9000, "country": "Argentina", "type": "Thermal park", "temp_c": 42, "notes": "Argentina's premier thermal complex; 20+ pools; aqua park; night bathing", "region": "Entre Rios"},
    {"name": "Chachimbiro Hot Springs", "lat": 0.4500, "lon": -78.2167, "country": "Ecuador", "type": "Highland thermal complex", "temp_c": 45, "notes": "Volcanic thermal complex north of Quito; 5 pools at different temperatures", "region": "Imbabura"},
]

# ═══════════════════════════════════════════════════════════════
# 9. AFRICAN HOT SPRINGS DATA (15+)
# ═══════════════════════════════════════════════════════════════
AFRICAN_SPRINGS = [
    {"name": "Lake Bogoria Hot Springs", "lat": 0.2667, "lon": 36.1000, "country": "Kenya", "type": "Lakeside geysers", "temp_c": 98, "notes": "Over 200 geysers and hot springs along alkaline Rift Valley lake; flamingo habitat", "region": "Rift Valley"},
    {"name": "Ain Echifa", "lat": 36.4167, "lon": 6.6333, "country": "Algeria", "type": "Thermal spring", "temp_c": 68, "notes": "Roman-era thermal spring (Aquae Calidae); one of 200+ springs across Algeria", "region": "Constantine"},
    {"name": "Wikki Warm Springs", "lat": 10.4167, "lon": 9.7500, "country": "Nigeria", "type": "Natural warm spring", "temp_c": 31, "notes": "Crystal-clear warm spring in Yankari National Park; elephant and baboon habitat", "region": "Bauchi"},
    {"name": "Sodere Hot Springs", "lat": 8.3833, "lon": 39.3500, "country": "Ethiopia", "type": "Thermal resort", "temp_c": 48, "notes": "Popular Ethiopian weekend resort in the Rift Valley; Olympic-size thermal pool", "region": "Oromia"},
    {"name": "Erta Ale Volcanic Hot Springs", "lat": 13.6000, "lon": 40.6700, "country": "Ethiopia", "type": "Volcanic springs", "temp_c": 100, "notes": "Springs around one of the world's oldest continuously active lava lakes in Afar desert", "region": "Afar"},
    {"name": "Hammam Meskoutine", "lat": 36.4500, "lon": 7.2667, "country": "Algeria", "type": "Cascading hot springs", "temp_c": 98, "notes": "Second hottest springs on Earth after Yellowstone; petrified travertine waterfall", "region": "Guelma"},
    {"name": "Filwoha Hot Springs (Addis Ababa)", "lat": 9.0167, "lon": 38.7500, "country": "Ethiopia", "type": "Urban thermal", "temp_c": 60, "notes": "Natural hot springs in heart of Addis Ababa; name means 'boiling water' in Amharic", "region": "Addis Ababa"},
    {"name": "Caledon Hot Springs", "lat": -34.2333, "lon": 19.4167, "country": "South Africa", "type": "Therapeutic thermal", "temp_c": 50, "notes": "Iron-rich therapeutic springs; The Baths resort since 1797; Overberg region", "region": "Western Cape"},
    {"name": "Montagu Hot Springs", "lat": -33.7500, "lon": 20.1500, "country": "South Africa", "type": "Mountain thermal", "temp_c": 43, "notes": "Known as Avalon Springs; radioactive mineral water; Route 62 gem", "region": "Western Cape"},
    {"name": "Mpumalanga Thermal Springs", "lat": -24.6833, "lon": 30.5333, "country": "South Africa", "type": "Lowveld thermal", "temp_c": 52, "notes": "Natural thermal springs near Kruger National Park; mineral-rich pools", "region": "Mpumalanga"},
    {"name": "Lac Assal Hot Springs", "lat": 11.5500, "lon": 42.4000, "country": "Djibouti", "type": "Volcanic lake springs", "temp_c": 65, "notes": "Near lowest point in Africa; hypersaline lake; Afar rift geothermal area", "region": "Tadjoura"},
    {"name": "Kiwira Hot Springs", "lat": -9.2333, "lon": 33.5500, "country": "Tanzania", "type": "Volcanic thermal", "temp_c": 55, "notes": "Near Mt Rungwe volcano; local bathing tradition; emerging geothermal energy site", "region": "Mbeya"},
    {"name": "Kitagata Hot Springs", "lat": -0.6833, "lon": 30.1500, "country": "Uganda", "type": "Community hot spring", "temp_c": 80, "notes": "Sacred Bakiga hot springs believed to cure ailments; communal bathing pools", "region": "Western Uganda"},
    {"name": "Afrera Hot Springs", "lat": 13.0833, "lon": 40.8500, "country": "Ethiopia", "type": "Salt lake thermal", "temp_c": 55, "notes": "Hot springs near salt-mining Lake Afrera in the Danakil Depression", "region": "Afar"},
    {"name": "Cela Springs", "lat": -12.3500, "lon": 15.1333, "country": "Angola", "type": "Tropical thermal", "temp_c": 48, "notes": "Natural hot springs in central Angola highlands; local healing tradition", "region": "Kwanza Sul"},
    {"name": "Siwa Oasis Hot Springs", "lat": 29.2028, "lon": 25.5197, "country": "Egypt", "type": "Desert oasis spring", "temp_c": 38, "notes": "Cleopatra's Bath; warm spring in ancient oasis; Alexander the Great visited Oracle here", "region": "Matruh"},
]

# ═══════════════════════════════════════════════════════════════
# 10. ASIAN HOT SPRINGS DATA (20+)
# ═══════════════════════════════════════════════════════════════
ASIAN_SPRINGS = [
    {"name": "Huanglong Pools", "lat": 32.7500, "lon": 103.8167, "country": "China", "type": "Travertine pools", "temp_c": 21, "notes": "3400+ colorful travertine pools; UNESCO World Heritage; 3100-3600m altitude", "region": "Sichuan"},
    {"name": "Tengchong Hot Sea", "lat": 24.9500, "lon": 98.4833, "country": "China", "type": "Volcanic geothermal", "temp_c": 97, "notes": "80+ hot springs and geysers; Rehai (Hot Sea) volcanic geothermal field in Yunnan", "region": "Yunnan"},
    {"name": "Jiuzhaigou Sparkling Lake", "lat": 33.2600, "lon": 103.9200, "country": "China", "type": "Thermal lake", "temp_c": 25, "notes": "Mineral-rich turquoise lakes; near hot spring resorts; UNESCO site", "region": "Sichuan"},
    {"name": "Manikaran Hot Springs", "lat": 32.0333, "lon": 77.3500, "country": "India", "type": "Sacred thermal spring", "temp_c": 95, "notes": "Sacred to Sikhs and Hindus; Gurudwara langar cooked in hot spring water; Parvati Valley", "region": "Himachal Pradesh"},
    {"name": "Tattapani Hot Springs", "lat": 31.2333, "lon": 76.9833, "country": "India", "type": "River hot spring", "temp_c": 50, "notes": "Hot sulphurous springs along Sutlej River; believed to cure skin diseases", "region": "Himachal Pradesh"},
    {"name": "Rajgir Hot Springs (Brahmakund)", "lat": 25.0167, "lon": 85.4167, "country": "India", "type": "Sacred thermal", "temp_c": 72, "notes": "Sacred springs where Buddha bathed; 22 springs at different temperatures; Saptadhara", "region": "Bihar"},
    {"name": "Banjar Hot Springs", "lat": -8.3333, "lon": 115.3167, "country": "Indonesia (Bali)", "type": "Tropical thermal", "temp_c": 38, "notes": "Sacred hot spring pools in lush tropical setting; dragon-head spouts; temple nearby", "region": "Bali"},
    {"name": "Cipanas Hot Springs", "lat": -6.7167, "lon": 107.0500, "country": "Indonesia (Java)", "type": "Volcanic thermal", "temp_c": 47, "notes": "Hot springs on slopes of Mt Guntur; Dutch colonial-era resort; public and private pools", "region": "West Java"},
    {"name": "Ranong Hot Springs", "lat": 9.9833, "lon": 98.6333, "country": "Thailand", "type": "Mineral hot spring", "temp_c": 65, "notes": "Raksawarin Hot Spring park; Thailand's only significant natural hot spring area", "region": "Southern Thailand"},
    {"name": "San Kamphaeng Hot Springs", "lat": 18.7333, "lon": 99.1833, "country": "Thailand", "type": "National park springs", "temp_c": 100, "notes": "Mineral bathing pools and geyser; cook eggs in boiling springs; near Chiang Mai", "region": "Chiang Mai"},
    {"name": "Panicuason Hot Springs", "lat": 13.6000, "lon": 123.2500, "country": "Philippines", "type": "Volcanic spring", "temp_c": 45, "notes": "Thermal springs at foot of Mt Isarog; multiple resorts with pools; Naga City", "region": "Camarines Sur"},
    {"name": "Puning Hot Springs", "lat": 15.1833, "lon": 120.5333, "country": "Philippines", "type": "Volcanic lahar spring", "temp_c": 42, "notes": "Natural hot springs amid Mt Pinatubo's lahar fields; 4x4 trek to reach pools", "region": "Pampanga"},
    {"name": "Beitou Hot Springs", "lat": 25.1364, "lon": 121.5072, "country": "Taiwan", "type": "Urban onsen district", "temp_c": 60, "notes": "Taipei's onsen district; 3 types of springs (white sulfur, green sulfur, iron); Japanese heritage", "region": "Taipei"},
    {"name": "Wulai Hot Springs", "lat": 24.8647, "lon": 121.5500, "country": "Taiwan", "type": "Indigenous hot spring", "temp_c": 80, "notes": "Atayal indigenous village; riverside open-air baths; waterfall; sodium bicarbonate water", "region": "New Taipei"},
    {"name": "Xinbeitou Thermal Valley", "lat": 25.1381, "lon": 121.5108, "country": "Taiwan", "type": "Geothermal valley", "temp_c": 100, "notes": "Steaming sulfurous valley (Hell Valley); source of Beitou district's hot spring water", "region": "Taipei"},
    {"name": "Jigokudani Monkey Park", "lat": 36.7333, "lon": 138.4628, "country": "Japan", "type": "Monkey onsen", "temp_c": 40, "notes": "Famous snow monkeys bathing in natural hot springs; Nagano winter icon", "region": "Nagano"},
    {"name": "Khir Ganga Hot Springs", "lat": 32.0500, "lon": 77.4667, "country": "India", "type": "Himalayan hot spring", "temp_c": 42, "notes": "Sacred hot pool at 2960m after 12km Himalayan trek; Shiva legend; Parvati Valley", "region": "Himachal Pradesh"},
    {"name": "Ma'in Hot Springs", "lat": 31.6167, "lon": 35.6167, "country": "Jordan", "type": "Desert thermal waterfall", "temp_c": 63, "notes": "Hot waterfalls cascading into Dead Sea valley; Herod the Great bathed here", "region": "Madaba"},
    {"name": "Kheerganga Hot Springs", "lat": 32.0500, "lon": 77.4833, "country": "India", "type": "Alpine hot spring", "temp_c": 40, "notes": "Sacred natural pool surrounded by Himalayan peaks at 2960m elevation", "region": "Himachal Pradesh"},
    {"name": "Zhangjiajie Hot Springs", "lat": 29.1250, "lon": 110.4792, "country": "China", "type": "Scenic hot springs", "temp_c": 50, "notes": "Thermal springs near Avatar-inspiring sandstone pillars; Jiangya Hot Spring", "region": "Hunan"},
    {"name": "Unzen Hot Springs", "lat": 32.7500, "lon": 130.2628, "country": "Japan", "type": "Volcanic onsen", "temp_c": 95, "notes": "Jigoku (hell) boiling springs in Shimabara Peninsula; national park", "region": "Nagasaki"},
]

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _make_dark_map(center, zoom=4):
    """Create a folium map with CartoDB dark_matter tiles."""
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)
    return m


def _render_folium(m, height=500):
    """Render a folium map in Streamlit using st_html."""
    st_html(m._repr_html_(), height=height)


def _csv_download(df, filename, label, key):
    """Render a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename,
                       mime="text/csv", key=key)


def _popup_html(title, fields, color="#06b6d4"):
    """Build a styled popup HTML string with escaped content."""
    safe_title = html_module.escape(str(title))
    lines = [
        f'<div style="min-width:200px;max-width:260px;font-family:sans-serif;">',
        f'<strong style="color:{color};font-size:1rem;">{safe_title}</strong><br/>',
    ]
    for label, value in fields:
        safe_val = html_module.escape(str(value))
        lines.append(
            f'<span style="font-size:0.78rem;"><b>{html_module.escape(str(label))}:</b> '
            f'{safe_val}</span><br/>'
        )
    lines.append('</div>')
    return ''.join(lines)


# ═══════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_japanese_onsen():
    """Mode 1: Japanese Onsen."""
    st.markdown("#### Japanese Onsen")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Japan\'s finest hot spring towns &mdash; from ancient Dogo Onsen '
        f'to the steaming hells of Beppu. Click markers for details.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    prefectures = sorted(set(o["prefecture"] for o in JAPANESE_ONSEN))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_pref = st.multiselect("Filter by Prefecture", prefectures,
                                   default=prefectures, key="onsen_pref")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Prefecture", "Temperature", "Rating"],
                                key="onsen_sort")

    filtered = [o for o in JAPANESE_ONSEN if o["prefecture"] in sel_pref]

    if sort_by == "Temperature":
        filtered.sort(key=lambda x: x["temp_c"], reverse=True)
    elif sort_by == "Prefecture":
        filtered.sort(key=lambda x: (x["prefecture"], x["name"]))
    elif sort_by == "Rating":
        filtered.sort(key=lambda x: x["rating"], reverse=True)
    else:
        filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Onsen Shown", len(filtered))
    c2.metric("Prefectures", len(set(o["prefecture"] for o in filtered)))
    avg_temp = sum(o["temp_c"] for o in filtered) / max(len(filtered), 1)
    c3.metric("Avg Temp", f"{avg_temp:.0f} C")
    top_rated = sum(1 for o in filtered if o["rating"] == 5)
    c4.metric("5-Star Onsen", top_rated)

    # Map
    m = _make_dark_map([36.5, 137.0], zoom=5)
    for o in filtered:
        color = "#ef4444" if o["rating"] == 5 else "#f97316" if o["rating"] == 4 else "#fbbf24"
        popup = _popup_html(o["name"], [
            ("Prefecture", o["prefecture"]),
            ("Type", o["type"]),
            ("Temperature", f"{o['temp_c']} C"),
            ("Rating", f"{'*' * o['rating']}"),
            ("Specialty", o["specialty"]),
        ], color=color)
        folium.CircleMarker(
            location=[o["lat"], o["lon"]],
            radius=6 + o["rating"],
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": o["name"], "Prefecture": o["prefecture"], "Type": o["type"],
        "Temp (C)": o["temp_c"], "Rating": o["rating"],
        "Specialty": o["specialty"], "Lat": o["lat"], "Lon": o["lon"],
    } for o in filtered])

    with st.expander(f"Full Data Table ({len(df)} onsen)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "japanese_onsen.csv",
                  f"Download {len(df)} Onsen (CSV)", "onsen_dl")


def _render_roman_baths():
    """Mode 2: Roman Baths & Ancient Thermae."""
    st.markdown("#### Roman Baths & Ancient Thermae")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From Aquae Sulis to Caracalla &mdash; the bathing culture '
        f'of the ancient world, including still-active thermal baths.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    countries = sorted(set(b["country"] for b in ROMAN_BATHS))
    statuses = sorted(set(b["status"] for b in ROMAN_BATHS))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_countries = st.multiselect("Filter by Country", countries,
                                        default=countries, key="roman_countries")
    with col2:
        sel_status = st.multiselect("Filter by Status", statuses,
                                     default=statuses, key="roman_status")

    filtered = [b for b in ROMAN_BATHS
                if b["country"] in sel_countries and b["status"] in sel_status]
    filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Sites Shown", len(filtered))
    c2.metric("Countries", len(set(b["country"] for b in filtered)))
    active = sum(1 for b in filtered if "Active" in b["status"])
    c3.metric("Still Active", active)

    # Map
    m = _make_dark_map([40.0, 20.0], zoom=3)
    for b in filtered:
        if "Active" in b["status"]:
            color = "#10b981"
        elif b["status"] == "Museum":
            color = "#f59e0b"
        else:
            color = "#6b7280"
        popup = _popup_html(b["name"], [
            ("Country", b["country"]),
            ("Era", b["era"]),
            ("Type", b["type"]),
            ("Temperature", f"{b['temp_c']} C" if b["temp_c"] > 0 else "N/A (ruins)"),
            ("Status", b["status"]),
            ("Notes", b["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=300),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": b["name"], "Country": b["country"], "Era": b["era"],
        "Type": b["type"], "Temp (C)": b["temp_c"] if b["temp_c"] > 0 else "N/A",
        "Status": b["status"], "Notes": b["notes"],
        "Lat": b["lat"], "Lon": b["lon"],
    } for b in filtered])

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "roman_baths.csv",
                  f"Download {len(df)} Roman Baths (CSV)", "roman_dl")


def _render_iceland_geothermal():
    """Mode 3: Iceland Geothermal."""
    st.markdown("#### Iceland Geothermal Pools & Springs")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From the iconic Blue Lagoon to hidden highland hot pots &mdash; '
        f'Iceland\'s extraordinary geothermal bathing culture.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    regions = sorted(set(s["region"] for s in ICELAND_GEOTHERMAL))
    costs = sorted(set(s["cost"] for s in ICELAND_GEOTHERMAL))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_regions = st.multiselect("Filter by Region", regions,
                                      default=regions, key="ice_regions")
    with col2:
        sel_costs = st.multiselect("Filter by Cost", costs,
                                    default=costs, key="ice_costs")

    filtered = [s for s in ICELAND_GEOTHERMAL
                if s["region"] in sel_regions and s["cost"] in sel_costs]
    filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Springs Shown", len(filtered))
    c2.metric("Regions", len(set(s["region"] for s in filtered)))
    free_count = sum(1 for s in filtered if s["cost"] == "Free")
    c3.metric("Free Springs", free_count)
    avg_temp = sum(s["temp_c"] for s in filtered) / max(len(filtered), 1)
    c4.metric("Avg Temp", f"{avg_temp:.0f} C")

    # Map
    m = _make_dark_map([64.9, -18.5], zoom=6)
    cost_colors = {"Free": "#10b981", "Low": "#22d3ee", "Moderate": "#f59e0b", "High": "#ef4444"}
    for s in filtered:
        color = cost_colors.get(s["cost"], "#8b97b0")
        popup = _popup_html(s["name"], [
            ("Region", s["region"]),
            ("Type", s["type"]),
            ("Temperature", f"{s['temp_c']} C"),
            ("Cost", s["cost"]),
            ("Notes", s["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Legend
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.8rem;">'
        '<span style="color:#10b981;">&#9679;</span> Free &nbsp; '
        '<span style="color:#22d3ee;">&#9679;</span> Low &nbsp; '
        '<span style="color:#f59e0b;">&#9679;</span> Moderate &nbsp; '
        '<span style="color:#ef4444;">&#9679;</span> High</p>',
        unsafe_allow_html=True,
    )

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "Region": s["region"], "Type": s["type"],
        "Temp (C)": s["temp_c"], "Cost": s["cost"], "Notes": s["notes"],
        "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} springs)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "iceland_geothermal.csv",
                  f"Download {len(df)} Iceland Springs (CSV)", "ice_dl")


def _render_european_spa_towns():
    """Mode 4: European Spa Towns."""
    st.markdown("#### European Spa Towns")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Historic wellness destinations from Baden-Baden to Budapest &mdash; '
        f'centuries of European spa culture and thermal heritage.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    countries = sorted(set(s["country"] for s in EUROPEAN_SPA_TOWNS))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_countries = st.multiselect("Filter by Country", countries,
                                        default=countries, key="euspa_countries")
    with col2:
        unesco_filter = st.selectbox("UNESCO Status", ["All", "UNESCO Only", "Non-UNESCO"],
                                      key="euspa_unesco")

    filtered = [s for s in EUROPEAN_SPA_TOWNS if s["country"] in sel_countries]
    if unesco_filter == "UNESCO Only":
        filtered = [s for s in filtered if s["unesco"]]
    elif unesco_filter == "Non-UNESCO":
        filtered = [s for s in filtered if not s["unesco"]]
    filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spa Towns Shown", len(filtered))
    c2.metric("Countries", len(set(s["country"] for s in filtered)))
    unesco_ct = sum(1 for s in filtered if s["unesco"])
    c3.metric("UNESCO Sites", unesco_ct)
    avg_temp = sum(s["temp_c"] for s in filtered) / max(len(filtered), 1)
    c4.metric("Avg Water Temp", f"{avg_temp:.0f} C")

    # Map
    m = _make_dark_map([48.0, 12.0], zoom=4)
    for s in filtered:
        color = "#8b5cf6" if s["unesco"] else "#06b6d4"
        popup = _popup_html(s["name"], [
            ("Country", s["country"]),
            ("Founded", s["founded"]),
            ("Water Type", s["famous_water"]),
            ("Temperature", f"{s['temp_c']} C"),
            ("UNESCO", "Yes" if s["unesco"] else "No"),
            ("Specialty", s["specialty"]),
        ], color=color)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=9 if s["unesco"] else 7,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=300),
        ).add_to(m)

    _render_folium(m)

    # Legend
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.8rem;">'
        '<span style="color:#8b5cf6;">&#9679;</span> UNESCO Great Spa &nbsp; '
        '<span style="color:#06b6d4;">&#9679;</span> Other Spa Town</p>',
        unsafe_allow_html=True,
    )

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "Country": s["country"], "Founded": s["founded"],
        "Water Type": s["famous_water"], "Temp (C)": s["temp_c"],
        "UNESCO": "Yes" if s["unesco"] else "No",
        "Specialty": s["specialty"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} spa towns)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "european_spa_towns.csv",
                  f"Download {len(df)} Spa Towns (CSV)", "euspa_dl")


def _render_us_hot_springs():
    """Mode 5: Yellowstone & US Hot Springs."""
    st.markdown("#### Yellowstone & US Hot Springs")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">America\'s geothermal treasures &mdash; from Yellowstone\'s '
        f'Grand Prismatic to backcountry soaking pools across the West.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    states = sorted(set(s["state"] for s in US_HOT_SPRINGS))
    access_types = sorted(set(s["access"] for s in US_HOT_SPRINGS))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_states = st.multiselect("Filter by State", states,
                                     default=states, key="us_states")
    with col2:
        sel_access = st.multiselect("Filter by Access", access_types,
                                     default=access_types, key="us_access")

    filtered = [s for s in US_HOT_SPRINGS
                if s["state"] in sel_states and s["access"] in sel_access]
    filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Springs Shown", len(filtered))
    c2.metric("States", len(set(s["state"] for s in filtered)))
    public = sum(1 for s in filtered if "Public" in s["access"] or s["access"] == "Free")
    c3.metric("Public Bathing", public)
    max_temp = max((s["temp_c"] for s in filtered), default=0)
    c4.metric("Hottest", f"{max_temp} C")

    # Map
    m = _make_dark_map([40.0, -105.0], zoom=4)
    access_colors = {
        "Public bathing": "#10b981", "Viewing only": "#3b82f6",
        "Free": "#22d3ee", "Guests only": "#f59e0b",
        "Hiking only": "#ec4899", "Guests/Day use": "#8b5cf6",
    }
    for s in filtered:
        color = access_colors.get(s["access"], "#06b6d4")
        popup = _popup_html(s["name"], [
            ("State", s["state"]),
            ("Type", s["type"]),
            ("Temperature", f"{s['temp_c']} C"),
            ("Access", s["access"]),
            ("Notes", s["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Legend
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.8rem;">'
        '<span style="color:#10b981;">&#9679;</span> Public Bathing &nbsp; '
        '<span style="color:#3b82f6;">&#9679;</span> Viewing Only &nbsp; '
        '<span style="color:#22d3ee;">&#9679;</span> Free &nbsp; '
        '<span style="color:#f59e0b;">&#9679;</span> Guests Only &nbsp; '
        '<span style="color:#ec4899;">&#9679;</span> Hiking</p>',
        unsafe_allow_html=True,
    )

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "State": s["state"], "Type": s["type"],
        "Temp (C)": s["temp_c"], "Access": s["access"],
        "Notes": s["notes"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} springs)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "us_hot_springs.csv",
                  f"Download {len(df)} US Hot Springs (CSV)", "us_dl")


def _render_turkish_hammam():
    """Mode 6: Turkish Hammam."""
    st.markdown("#### Turkish Hammam Heritage")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Ottoman bathhouse culture &mdash; from Mimar Sinan\'s masterpieces '
        f'in Istanbul to ancient thermal baths across Anatolia.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    cities = sorted(set(h["city"] for h in TURKISH_HAMMAM))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_cities = st.multiselect("Filter by City", cities,
                                     default=cities, key="ham_cities")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "City", "Era"],
                                key="ham_sort")

    filtered = [h for h in TURKISH_HAMMAM if h["city"] in sel_cities]

    if sort_by == "City":
        filtered.sort(key=lambda x: (x["city"], x["name"]))
    elif sort_by == "Era":
        filtered.sort(key=lambda x: x["era"])
    else:
        filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hammams Shown", len(filtered))
    c2.metric("Cities", len(set(h["city"] for h in filtered)))
    sinan = sum(1 for h in filtered if "Sinan" in h.get("architect", ""))
    c3.metric("By Mimar Sinan", sinan)
    active = sum(1 for h in filtered if h["status"] == "Active")
    c4.metric("Still Active", active)

    # Map
    m = _make_dark_map([39.5, 32.0], zoom=6)
    for h in filtered:
        color = "#f97316" if h["status"] == "Active" else "#6b7280"
        arch_info = h.get("architect", "Unknown")
        popup = _popup_html(h["name"], [
            ("City", h["city"]),
            ("Era", h["era"]),
            ("Architect", arch_info),
            ("Type", h["type"]),
            ("Status", h["status"]),
            ("Notes", h["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[h["lat"], h["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=300),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": h["name"], "City": h["city"], "Era": h["era"],
        "Architect": h.get("architect", "Unknown"), "Type": h["type"],
        "Status": h["status"], "Notes": h["notes"],
        "Lat": h["lat"], "Lon": h["lon"],
    } for h in filtered])

    with st.expander(f"Full Data Table ({len(df)} hammams)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "turkish_hammam.csv",
                  f"Download {len(df)} Hammams (CSV)", "ham_dl")


def _render_nz_geothermal():
    """Mode 7: New Zealand Geothermal."""
    st.markdown("#### New Zealand Geothermal")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">Aotearoa\'s volcanic wonderland &mdash; from Rotorua\'s geysers '
        f'to alpine hot pools in the Southern Alps.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    islands = sorted(set(s["island"] for s in NZ_GEOTHERMAL))
    access_types = sorted(set(s["access"] for s in NZ_GEOTHERMAL))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_islands = st.multiselect("Filter by Island", islands,
                                      default=islands, key="nz_islands")
    with col2:
        sel_access = st.multiselect("Filter by Access", access_types,
                                     default=access_types, key="nz_access")

    filtered = [s for s in NZ_GEOTHERMAL
                if s["island"] in sel_islands and s["access"] in sel_access]
    filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Shown", len(filtered))
    north = sum(1 for s in filtered if s["island"] == "North")
    c2.metric("North Island", north)
    south = sum(1 for s in filtered if s["island"] == "South")
    c3.metric("South Island", south)
    free_ct = sum(1 for s in filtered if "Free" in s["access"])
    c4.metric("Free Access", free_ct)

    # Map
    m = _make_dark_map([-39.0, 176.0], zoom=5)
    access_colors_nz = {
        "Public": "#22d3ee", "Free": "#10b981",
        "Public (viewing)": "#3b82f6", "Free (viewing)": "#38bdf8",
        "Hiking only": "#ec4899",
    }
    for s in filtered:
        color = access_colors_nz.get(s["access"], "#06b6d4")
        popup = _popup_html(s["name"], [
            ("Island", s["island"]),
            ("Type", s["type"]),
            ("Temperature", f"{s['temp_c']} C"),
            ("Access", s["access"]),
            ("Notes", s["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "Island": s["island"], "Type": s["type"],
        "Temp (C)": s["temp_c"], "Access": s["access"],
        "Notes": s["notes"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "nz_geothermal.csv",
                  f"Download {len(df)} NZ Geothermal Sites (CSV)", "nz_dl")


def _render_south_american_springs():
    """Mode 8: South American Hot Springs."""
    st.markdown("#### South American Hot Springs")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From Andean thermal pools at 4000m to Patagonian rainforest springs '
        f'&mdash; South America\'s diverse hot spring destinations.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    countries = sorted(set(s["country"] for s in SOUTH_AMERICAN_SPRINGS))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_countries = st.multiselect("Filter by Country", countries,
                                        default=countries, key="spam_sa_countries")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Country", "Temperature", "Region"],
                                key="sa_sort")

    filtered = [s for s in SOUTH_AMERICAN_SPRINGS if s["country"] in sel_countries]

    if sort_by == "Temperature":
        filtered.sort(key=lambda x: x["temp_c"], reverse=True)
    elif sort_by == "Country":
        filtered.sort(key=lambda x: (x["country"], x["name"]))
    elif sort_by == "Region":
        filtered.sort(key=lambda x: x["region"])
    else:
        filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Springs Shown", len(filtered))
    c2.metric("Countries", len(set(s["country"] for s in filtered)))
    avg_temp = sum(s["temp_c"] for s in filtered) / max(len(filtered), 1)
    c3.metric("Avg Temp", f"{avg_temp:.0f} C")

    # Map
    m = _make_dark_map([-20.0, -65.0], zoom=3)
    country_colors = {
        "Chile": "#ec4899", "Peru": "#f59e0b", "Argentina": "#3b82f6",
        "Ecuador": "#10b981", "Bolivia": "#ef4444", "Uruguay": "#8b5cf6",
    }
    for s in filtered:
        color = country_colors.get(s["country"], "#06b6d4")
        popup = _popup_html(s["name"], [
            ("Country", s["country"]),
            ("Region", s["region"]),
            ("Type", s["type"]),
            ("Temperature", f"{s['temp_c']} C"),
            ("Notes", s["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "Country": s["country"], "Region": s["region"],
        "Type": s["type"], "Temp (C)": s["temp_c"],
        "Notes": s["notes"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} springs)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "south_american_springs.csv",
                  f"Download {len(df)} SA Hot Springs (CSV)", "sa_dl")


def _render_african_springs():
    """Mode 9: African Hot Springs."""
    st.markdown("#### African Hot Springs")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From Kenya\'s Rift Valley geysers to Saharan oasis springs '
        f'&mdash; Africa\'s diverse and often overlooked geothermal heritage.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    countries = sorted(set(s["country"] for s in AFRICAN_SPRINGS))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_countries = st.multiselect("Filter by Country", countries,
                                        default=countries, key="af_countries")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Country", "Temperature", "Region"],
                                key="af_sort")

    filtered = [s for s in AFRICAN_SPRINGS if s["country"] in sel_countries]

    if sort_by == "Temperature":
        filtered.sort(key=lambda x: x["temp_c"], reverse=True)
    elif sort_by == "Country":
        filtered.sort(key=lambda x: (x["country"], x["name"]))
    elif sort_by == "Region":
        filtered.sort(key=lambda x: x["region"])
    else:
        filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Springs Shown", len(filtered))
    c2.metric("Countries", len(set(s["country"] for s in filtered)))
    max_temp = max((s["temp_c"] for s in filtered), default=0)
    c3.metric("Hottest Spring", f"{max_temp} C")

    # Map
    m = _make_dark_map([5.0, 25.0], zoom=3)
    for s in filtered:
        # Heatmap: hotter = redder
        if s["temp_c"] >= 80:
            color = "#ef4444"
        elif s["temp_c"] >= 55:
            color = "#f97316"
        elif s["temp_c"] >= 40:
            color = "#f59e0b"
        else:
            color = "#22d3ee"
        popup = _popup_html(s["name"], [
            ("Country", s["country"]),
            ("Region", s["region"]),
            ("Type", s["type"]),
            ("Temperature", f"{s['temp_c']} C"),
            ("Notes", s["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Legend
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:0.8rem;">'
        '<span style="color:#ef4444;">&#9679;</span> 80+ C &nbsp; '
        '<span style="color:#f97316;">&#9679;</span> 55-79 C &nbsp; '
        '<span style="color:#f59e0b;">&#9679;</span> 40-54 C &nbsp; '
        '<span style="color:#22d3ee;">&#9679;</span> &lt;40 C</p>',
        unsafe_allow_html=True,
    )

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "Country": s["country"], "Region": s["region"],
        "Type": s["type"], "Temp (C)": s["temp_c"],
        "Notes": s["notes"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} springs)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "african_springs.csv",
                  f"Download {len(df)} African Springs (CSV)", "af_dl")


def _render_asian_springs():
    """Mode 10: Asian Hot Springs."""
    st.markdown("#### Asian Hot Springs")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY};">From China\'s colorful travertine pools to India\'s sacred springs '
        f'and Southeast Asia\'s tropical thermal baths.</p>',
        unsafe_allow_html=True,
    )

    # Filters
    countries = sorted(set(s["country"] for s in ASIAN_SPRINGS))
    col1, col2 = st.columns([1, 1])
    with col1:
        sel_countries = st.multiselect("Filter by Country", countries,
                                        default=countries, key="asia_countries")
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Country", "Temperature", "Region"],
                                key="asia_sort")

    filtered = [s for s in ASIAN_SPRINGS if s["country"] in sel_countries]

    if sort_by == "Temperature":
        filtered.sort(key=lambda x: x["temp_c"], reverse=True)
    elif sort_by == "Country":
        filtered.sort(key=lambda x: (x["country"], x["name"]))
    elif sort_by == "Region":
        filtered.sort(key=lambda x: x["region"])
    else:
        filtered.sort(key=lambda x: x["name"])

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Springs Shown", len(filtered))
    c2.metric("Countries", len(set(s["country"] for s in filtered)))
    avg_temp = sum(s["temp_c"] for s in filtered) / max(len(filtered), 1)
    c3.metric("Avg Temp", f"{avg_temp:.0f} C")
    sacred = sum(1 for s in filtered if "sacred" in s["notes"].lower() or "Sacred" in s["type"])
    c4.metric("Sacred Springs", sacred)

    # Map
    m = _make_dark_map([25.0, 100.0], zoom=3)
    country_colors_asia = {
        "China": "#ef4444", "India": "#f59e0b", "Indonesia (Bali)": "#10b981",
        "Indonesia (Java)": "#22d3ee", "Thailand": "#ec4899",
        "Philippines": "#8b5cf6", "Taiwan": "#3b82f6",
        "Japan": "#f97316", "Jordan": "#a855f7",
    }
    for s in filtered:
        color = country_colors_asia.get(s["country"], "#06b6d4")
        popup = _popup_html(s["name"], [
            ("Country", s["country"]),
            ("Region", s["region"]),
            ("Type", s["type"]),
            ("Temperature", f"{s['temp_c']} C"),
            ("Notes", s["notes"]),
        ], color=color)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup, max_width=280),
        ).add_to(m)

    _render_folium(m)

    # Data table
    df = pd.DataFrame([{
        "Name": s["name"], "Country": s["country"], "Region": s["region"],
        "Type": s["type"], "Temp (C)": s["temp_c"],
        "Notes": s["notes"], "Lat": s["lat"], "Lon": s["lon"],
    } for s in filtered])

    with st.expander(f"Full Data Table ({len(df)} springs)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    _csv_download(df, "asian_springs.csv",
                  f"Download {len(df)} Asian Springs (CSV)", "asia_dl")


# ═══════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ═══════════════════════════════════════════════════════════════

def render_spa_maps_tab():
    """Main render function for the Hot Springs & Spa Maps tab."""

    # -- Header --
    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>\u2668\ufe0f Hot Springs & Spa Maps</h4>'
        '<p>Thermal baths, onsen, hot springs, and wellness destinations worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # -- Mode selector --
    mode = st.selectbox("Map Mode", MAP_MODES, key="spa_mode")

    st.markdown("---")

    # -- Dispatch --
    if mode == MAP_MODES[0]:
        _render_japanese_onsen()
    elif mode == MAP_MODES[1]:
        _render_roman_baths()
    elif mode == MAP_MODES[2]:
        _render_iceland_geothermal()
    elif mode == MAP_MODES[3]:
        _render_european_spa_towns()
    elif mode == MAP_MODES[4]:
        _render_us_hot_springs()
    elif mode == MAP_MODES[5]:
        _render_turkish_hammam()
    elif mode == MAP_MODES[6]:
        _render_nz_geothermal()
    elif mode == MAP_MODES[7]:
        _render_south_american_springs()
    elif mode == MAP_MODES[8]:
        _render_african_springs()
    elif mode == MAP_MODES[9]:
        _render_asian_springs()
