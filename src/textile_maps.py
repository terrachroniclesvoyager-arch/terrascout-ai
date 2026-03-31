# -*- coding: utf-8 -*-
"""
Textile & Fabric Maps module for TerraScout AI.
Maps 10 thematic views of global textile traditions, silk roads, weaving
centers, dye origins, carpet cultures, and textile museums.
All data is curated; no external API key required.
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

# =====================================================================
# PALETTE CONSTANTS
# =====================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_CARD = "#1a2235"
_BORDER = "#2a3550"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_ACCENT = "#06b6d4"

# =====================================================================
# 1. SILK ROAD HERITAGE (25 locations)
# =====================================================================
SILK_ROAD_HERITAGE = [
    {"name": "Xi'an (Chang'an), China", "lat": 34.26, "lon": 108.94,
     "era": "130 BC", "role": "Eastern terminus",
     "color": "#f59e0b",
     "notes": "Zhang Qian opened the route west; Tang dynasty cosmopolitan capital"},
    {"name": "Dunhuang, China", "lat": 40.14, "lon": 94.66,
     "era": "100 BC", "role": "Jade Gate outpost",
     "color": "#f59e0b",
     "notes": "Mogao Caves silk paintings; gateway to the Taklamakan Desert"},
    {"name": "Kashgar, China", "lat": 39.47, "lon": 75.99,
     "era": "100 BC", "role": "Central hub",
     "color": "#ef4444",
     "notes": "Split point for north and south Taklamakan routes; Sunday bazaar"},
    {"name": "Samarkand, Uzbekistan", "lat": 39.65, "lon": 66.96,
     "era": "300 BC", "role": "Sogdian trade hub",
     "color": "#8b5cf6",
     "notes": "Registan Square; Sogdian merchants dominated silk-for-gold trade"},
    {"name": "Bukhara, Uzbekistan", "lat": 39.77, "lon": 64.42,
     "era": "500 AD", "role": "Caravanserai city",
     "color": "#8b5cf6",
     "notes": "Ikat and suzani embroidery center; covered bazaars"},
    {"name": "Merv (Mary), Turkmenistan", "lat": 37.66, "lon": 62.19,
     "era": "300 BC", "role": "Oasis crossroads",
     "color": "#ec4899",
     "notes": "UNESCO site; once the world's largest city; east-west nexus"},
    {"name": "Isfahan, Iran", "lat": 32.65, "lon": 51.68,
     "era": "500 BC", "role": "Persian silk center",
     "color": "#06b6d4",
     "notes": "Safavid silk brocade; Naqsh-e Jahan Square bazaar"},
    {"name": "Tehran / Rey, Iran", "lat": 35.59, "lon": 51.44,
     "era": "200 BC", "role": "Persian waypoint",
     "color": "#06b6d4",
     "notes": "Ancient Rhages (Rey); Sassanid silk weavers and termeh brocade"},
    {"name": "Palmyra, Syria", "lat": 34.55, "lon": 38.27,
     "era": "100 AD", "role": "Desert caravan city",
     "color": "#10b981",
     "notes": "Palmyrene merchants traded Chinese silk westward through the desert"},
    {"name": "Antioch (Antakya), Turkey", "lat": 36.20, "lon": 36.16,
     "era": "200 AD", "role": "Roman dyeing center",
     "color": "#10b981",
     "notes": "Purple-dyed silks for Roman emperors; Mediterranean trade node"},
    {"name": "Constantinople (Istanbul), Turkey", "lat": 41.01, "lon": 28.98,
     "era": "550 AD", "role": "Western terminus",
     "color": "#10b981",
     "notes": "Byzantine monks smuggled silkworm eggs in hollow bamboo canes"},
    {"name": "Aleppo, Syria", "lat": 36.20, "lon": 37.16,
     "era": "300 BC", "role": "Levantine emporium",
     "color": "#3b82f6",
     "notes": "Khan al-Wazir caravanserai; silk souk active for millennia"},
    {"name": "Balkh, Afghanistan", "lat": 36.76, "lon": 66.90,
     "era": "500 BC", "role": "Bactrian crossroads",
     "color": "#a855f7",
     "notes": "Mother of Cities; Zoroastrian silk trade; Kushan empire hub"},
    {"name": "Turfan, China", "lat": 42.95, "lon": 89.18,
     "era": "200 BC", "role": "Northern route oasis",
     "color": "#f59e0b",
     "notes": "Bezeklik Caves; grape and silk oasis below sea level"},
    {"name": "Khotan (Hotan), China", "lat": 37.11, "lon": 79.93,
     "era": "200 BC", "role": "Southern route oasis",
     "color": "#f59e0b",
     "notes": "Jade and silk center; legend of princess smuggling silkworm eggs"},
    {"name": "Lanzhou, China", "lat": 36.06, "lon": 103.83,
     "era": "100 BC", "role": "Yellow River crossing",
     "color": "#f97316",
     "notes": "Hexi Corridor gateway; critical river ford for silk caravans"},
    {"name": "Tabriz, Iran", "lat": 38.08, "lon": 46.29,
     "era": "700 AD", "role": "Azerbaijani silk hub",
     "color": "#06b6d4",
     "notes": "Grand Bazaar UNESCO site; Ilkhanid and Safavid silk trade center"},
    {"name": "Baghdad, Iraq", "lat": 33.31, "lon": 44.37,
     "era": "750 AD", "role": "Abbasid capital",
     "color": "#14b8a6",
     "notes": "House of Wisdom era; silk tiraz textiles for the caliphate"},
    {"name": "Ctesiphon, Iraq", "lat": 33.09, "lon": 44.58,
     "era": "200 AD", "role": "Sassanid capital",
     "color": "#14b8a6",
     "notes": "Sassanid silk workshops; roundel motif textiles exported west"},
    {"name": "Alexandria, Egypt", "lat": 31.20, "lon": 29.92,
     "era": "300 BC", "role": "Maritime silk port",
     "color": "#3b82f6",
     "notes": "Sea route terminus; Ptolemaic and Roman silk imports from India"},
    {"name": "Venice, Italy", "lat": 45.44, "lon": 12.34,
     "era": "1200 AD", "role": "European gateway",
     "color": "#a855f7",
     "notes": "Marco Polo's route; Venetian silk velvet production"},
    {"name": "Genoa, Italy", "lat": 44.41, "lon": 8.93,
     "era": "1100 AD", "role": "Maritime republic",
     "color": "#a855f7",
     "notes": "Rival to Venice; silk and spice imports; Genoese merchants"},
    {"name": "Trabzon (Trebizond), Turkey", "lat": 41.00, "lon": 39.72,
     "era": "800 AD", "role": "Black Sea port",
     "color": "#10b981",
     "notes": "Northern branch terminus on Black Sea; Comnenian silk trade"},
    {"name": "Karakorum, Mongolia", "lat": 47.20, "lon": 102.83,
     "era": "1220 AD", "role": "Mongol capital",
     "color": "#ec4899",
     "notes": "Genghis Khan's capital; Pax Mongolica secured Silk Road trade"},
    {"name": "Hormuz, Iran", "lat": 27.06, "lon": 56.28,
     "era": "1300 AD", "role": "Persian Gulf port",
     "color": "#06b6d4",
     "notes": "Maritime silk route hub; Portuguese later seized for spice trade"},
]

# =====================================================================
# 2. TRADITIONAL WEAVING CENTERS (22 locations)
# =====================================================================
TRADITIONAL_WEAVING = [
    {"name": "Varanasi (Benares), India", "lat": 25.32, "lon": 83.01,
     "tradition": "Banarasi silk brocade", "color": "#f59e0b",
     "notes": "Gold zari thread weaving; Mughal-era traditions; wedding saris"},
    {"name": "Oaxaca, Mexico", "lat": 17.07, "lon": -96.72,
     "tradition": "Zapotec backstrap loom", "color": "#10b981",
     "notes": "Natural dye weaving; cochineal and indigo; huipil garments"},
    {"name": "Cusco, Peru", "lat": -13.53, "lon": -71.97,
     "tradition": "Andean weaving", "color": "#ef4444",
     "notes": "Inca textile legacy; alpaca and llama fiber; quipu-linked patterns"},
    {"name": "Fez, Morocco", "lat": 34.03, "lon": -5.00,
     "tradition": "Moroccan brocade", "color": "#8b5cf6",
     "notes": "Fes silk belts; hand-loomed caftans; Andalusian weaving heritage"},
    {"name": "Kyoto, Japan", "lat": 35.01, "lon": 135.77,
     "tradition": "Nishijin-ori silk", "color": "#ec4899",
     "notes": "Kimono silk weaving since 5th century; Jacquard-adapted looms"},
    {"name": "Chiang Mai, Thailand", "lat": 18.79, "lon": 98.98,
     "tradition": "Thai silk (mudmee)", "color": "#f97316",
     "notes": "Lanna kingdom weaving; Jim Thompson revival; ikat technique"},
    {"name": "Luang Prabang, Laos", "lat": 19.89, "lon": 102.14,
     "tradition": "Lao silk weaving", "color": "#f97316",
     "notes": "UNESCO town; traditional floor looms; sinh skirt cloth"},
    {"name": "Kanchipuram, India", "lat": 12.83, "lon": 79.70,
     "tradition": "Kanchipuram silk sari", "color": "#f59e0b",
     "notes": "Temple town silk; heavy silk with gold borders; 5,000 weaver families"},
    {"name": "Suzhou, China", "lat": 31.30, "lon": 120.62,
     "tradition": "Su embroidery silk", "color": "#06b6d4",
     "notes": "Double-sided silk embroidery (Su Xiu); Song dynasty heritage"},
    {"name": "Bhutan — Bumthang", "lat": 27.55, "lon": 90.73,
     "tradition": "Bhutanese yathra wool", "color": "#14b8a6",
     "notes": "Highland wool weaving; kushuthara brocade; national dress textiles"},
    {"name": "Guatemala — Chichicastenango", "lat": 14.94, "lon": -91.11,
     "tradition": "Maya backstrap weaving", "color": "#10b981",
     "notes": "K'iche' Maya textile art; huipil blouses; natural dye revival"},
    {"name": "Addis Ababa, Ethiopia", "lat": 9.02, "lon": 38.75,
     "tradition": "Ethiopian cotton shemma", "color": "#3b82f6",
     "notes": "Hand-spun cotton shawls; tibeb decorative borders; Dorze weavers"},
    {"name": "Bhujodi, Gujarat, India", "lat": 23.24, "lon": 69.67,
     "tradition": "Kutch shawl weaving", "color": "#f59e0b",
     "notes": "Vankar Meghwar weavers; wool and cotton; mirror-work embroidery"},
    {"name": "Mahdia, Tunisia", "lat": 35.50, "lon": 11.05,
     "tradition": "Tunisian silk weaving", "color": "#a855f7",
     "notes": "Fatimid-era silk; hand-loomed traditional haik cloth"},
    {"name": "Hoi An, Vietnam", "lat": 15.88, "lon": 108.33,
     "tradition": "Vietnamese silk", "color": "#ec4899",
     "notes": "Ancient trading port; silk lanterns and ao dai tailoring"},
    {"name": "Teotitlan del Valle, Mexico", "lat": 17.00, "lon": -96.52,
     "tradition": "Zapotec wool rugs", "color": "#10b981",
     "notes": "Natural-dye wool weaving; pre-Columbian tradition; cochineal red"},
    {"name": "Assam, India — Sualkuchi", "lat": 26.17, "lon": 91.57,
     "tradition": "Muga & Eri silk", "color": "#f59e0b",
     "notes": "Manchester of the East; golden muga silk unique to Assam"},
    {"name": "Urgut, Uzbekistan", "lat": 39.30, "lon": 67.23,
     "tradition": "Uzbek ikat (atlas)", "color": "#8b5cf6",
     "notes": "Abr-bandi cloud-tying ikat; vibrant silk and cotton resist-dye"},
    {"name": "Patan, Nepal", "lat": 27.67, "lon": 85.33,
     "tradition": "Dhaka topi weaving", "color": "#14b8a6",
     "notes": "Newar weaving culture; dhaka fabric for traditional caps"},
    {"name": "Flores, Indonesia", "lat": -8.66, "lon": 121.07,
     "tradition": "Ikat tenun", "color": "#06b6d4",
     "notes": "Warp ikat cloth; clan identity patterns; natural dye traditions"},
    {"name": "Aleppo, Syria", "lat": 36.20, "lon": 37.16,
     "tradition": "Aleppo brocade", "color": "#ef4444",
     "notes": "Historic silk brocade weaving; aghabani embroidery; souk looms"},
    {"name": "Panajachel, Guatemala", "lat": 14.74, "lon": -91.16,
     "tradition": "Highland Maya weaving", "color": "#10b981",
     "notes": "Lake Atitlan villages; each town has distinct huipil patterns"},
]

# =====================================================================
# 3. COTTON & TEXTILE MILLS (22 locations)
# =====================================================================
COTTON_TEXTILE_MILLS = [
    {"name": "Manchester, England", "lat": 53.48, "lon": -2.24,
     "era": "1770s", "type": "Cotton spinning",
     "color": "#10b981",
     "notes": "Cottonopolis; spinning jenny and water frame; Industrial Revolution epicenter"},
    {"name": "Lowell, Massachusetts, USA", "lat": 42.63, "lon": -71.32,
     "era": "1823", "type": "Planned mill city",
     "color": "#3b82f6",
     "notes": "First planned industrial city in America; Merrimack Manufacturing Company"},
    {"name": "Ahmedabad, Gujarat, India", "lat": 23.02, "lon": 72.57,
     "era": "1861", "type": "Cotton mills",
     "color": "#f59e0b",
     "notes": "Manchester of India; 80+ mills at peak; Gandhi's Sabarmati Ashram"},
    {"name": "Lodz, Poland", "lat": 51.75, "lon": 19.47,
     "era": "1820s", "type": "Textile manufacturing",
     "color": "#8b5cf6",
     "notes": "Polish Manchester; Izrael Poznanski factory; now cultural center"},
    {"name": "Cromford, Derbyshire, England", "lat": 53.11, "lon": -1.56,
     "era": "1771", "type": "Water-powered mill",
     "color": "#10b981",
     "notes": "Arkwright's first water-powered cotton mill; UNESCO World Heritage"},
    {"name": "New Lanark, Scotland", "lat": 55.67, "lon": -3.78,
     "era": "1786", "type": "Utopian mill village",
     "color": "#14b8a6",
     "notes": "Robert Owen's model industrial community; UNESCO World Heritage"},
    {"name": "Fall River, Massachusetts, USA", "lat": 41.70, "lon": -71.16,
     "era": "1811", "type": "Cotton mills",
     "color": "#3b82f6",
     "notes": "Spindle City; 120 mills at peak; Quequechan River power"},
    {"name": "Bombay (Mumbai), India", "lat": 19.08, "lon": 72.88,
     "era": "1854", "type": "Cotton mills",
     "color": "#f59e0b",
     "notes": "First Indian-owned steam mill; Girangaon mill district; 130+ mills"},
    {"name": "Gabrovo, Bulgaria", "lat": 42.87, "lon": 25.32,
     "era": "1834", "type": "Wool & cotton mills",
     "color": "#a855f7",
     "notes": "Bulgarian Manchester; first industrial town in the Balkans"},
    {"name": "Mulhouse, France", "lat": 47.75, "lon": 7.34,
     "era": "1746", "type": "Printed cotton",
     "color": "#ec4899",
     "notes": "Alsatian printed cotton (indiennes); now textile museum city"},
    {"name": "Lawrence, Massachusetts, USA", "lat": 42.71, "lon": -71.16,
     "era": "1845", "type": "Worsted wool",
     "color": "#3b82f6",
     "notes": "Immigrant City; Bread and Roses Strike 1912; Essex Company dam"},
    {"name": "Coimbatore, Tamil Nadu, India", "lat": 11.00, "lon": 76.96,
     "era": "1920s", "type": "Cotton spinning",
     "color": "#f59e0b",
     "notes": "Manchester of South India; 25,000+ power looms; textile hub"},
    {"name": "Dhaka, Bangladesh", "lat": 23.81, "lon": 90.41,
     "era": "1700s", "type": "Muslin weaving",
     "color": "#06b6d4",
     "notes": "Legendary Dhaka muslin 'woven air'; Mughal court fabric"},
    {"name": "Ghent, Belgium", "lat": 51.05, "lon": 3.72,
     "era": "1800s", "type": "Linen & cotton",
     "color": "#14b8a6",
     "notes": "Continental Europe's first mechanized cotton mill; MIAT museum"},
    {"name": "Paisley, Scotland", "lat": 55.85, "lon": -4.42,
     "era": "1800s", "type": "Shawl weaving",
     "color": "#10b981",
     "notes": "Paisley pattern copied from Kashmir; power-loom shawl production"},
    {"name": "Shanghai, China", "lat": 31.24, "lon": 121.47,
     "era": "1860s", "type": "Cotton mills",
     "color": "#f97316",
     "notes": "Treaty-port cotton mills; Suzhou Creek industrial district"},
    {"name": "Barcelona, Spain", "lat": 41.39, "lon": 2.17,
     "era": "1830s", "type": "Cotton manufacturing",
     "color": "#ef4444",
     "notes": "Catalan Manchester; Vapor Vell first steam-powered mill"},
    {"name": "Tampere, Finland", "lat": 61.50, "lon": 23.79,
     "era": "1820", "type": "Cotton & linen",
     "color": "#8b5cf6",
     "notes": "Manchester of Finland; Finlayson cotton mill; rapids-powered"},
    {"name": "Kanagawa (Yokohama), Japan", "lat": 35.44, "lon": 139.64,
     "era": "1859", "type": "Silk reeling",
     "color": "#ec4899",
     "notes": "Meiji-era silk export port; Tomioka Silk Mill nearby"},
    {"name": "Enschede, Netherlands", "lat": 52.22, "lon": 6.89,
     "era": "1830s", "type": "Cotton manufacturing",
     "color": "#06b6d4",
     "notes": "Twente textile region; Jannink factory; now TechMed Centre"},
    {"name": "Greenville, South Carolina, USA", "lat": 34.85, "lon": -82.40,
     "era": "1876", "type": "Cotton mills",
     "color": "#3b82f6",
     "notes": "Textile Capital of the World; Camperdown Mill; Southern mill boom"},
    {"name": "Ivanovo, Russia", "lat": 57.00, "lon": 40.97,
     "era": "1742", "type": "Linen & cotton printing",
     "color": "#a855f7",
     "notes": "Russian Manchester; first Russian calico printing; textile strikes"},
]

# =====================================================================
# 4. CARPET & RUG TRADITIONS (20 locations)
# =====================================================================
CARPET_RUG_TRADITIONS = [
    {"name": "Isfahan, Iran", "lat": 32.65, "lon": 51.68,
     "style": "Persian carpet", "color": "#ef4444",
     "notes": "Shah Abbas carpets; curvilinear floral medallion designs; silk and wool"},
    {"name": "Tabriz, Iran", "lat": 38.08, "lon": 46.29,
     "style": "Persian carpet", "color": "#ef4444",
     "notes": "70 Raj knot density; UNESCO-recognized Tabriz carpet tradition"},
    {"name": "Kashan, Iran", "lat": 33.98, "lon": 51.44,
     "style": "Persian carpet", "color": "#ef4444",
     "notes": "Home of the Ardabil Carpet (1539); Mohtasham workshop masterpieces"},
    {"name": "Hereke, Turkey", "lat": 40.68, "lon": 29.64,
     "style": "Turkish Hereke", "color": "#f59e0b",
     "notes": "Ottoman imperial workshop; silk rugs for Dolmabahce Palace"},
    {"name": "Konya, Turkey", "lat": 37.87, "lon": 32.49,
     "style": "Anatolian carpet", "color": "#f59e0b",
     "notes": "Seljuk-era double-knotted; Rumi's city; geometric prayer rugs"},
    {"name": "Mazar-i-Sharif, Afghanistan", "lat": 36.71, "lon": 67.11,
     "style": "Afghan war rug", "color": "#8b5cf6",
     "notes": "Turkmen and Uzbek weavers; war rug genre with tanks and helicopters"},
    {"name": "Bukhara, Uzbekistan", "lat": 39.77, "lon": 64.42,
     "style": "Turkmen Bukhara", "color": "#8b5cf6",
     "notes": "Tekke gul motif; deep red Bukhara rugs; nomadic Turkmen weavers"},
    {"name": "Fez, Morocco", "lat": 34.03, "lon": -5.00,
     "style": "Moroccan Berber", "color": "#06b6d4",
     "notes": "Beni Ourain rugs; minimalist Berber designs; Atlas Mountain wool"},
    {"name": "Marrakech, Morocco", "lat": 31.63, "lon": -8.00,
     "style": "Berber kilim", "color": "#06b6d4",
     "notes": "Hanbel flat-weave; Azilal and Boucherouite rugs; souk markets"},
    {"name": "Ganado, Arizona, USA", "lat": 35.71, "lon": -109.56,
     "style": "Navajo rug", "color": "#10b981",
     "notes": "Ganado Red style; churro sheep wool; Spider Woman weaving legend"},
    {"name": "Lhasa, Tibet", "lat": 29.65, "lon": 91.17,
     "style": "Tibetan carpet", "color": "#ec4899",
     "notes": "Tibetan tiger rugs; Buddhist dragon motifs; highland sheep wool"},
    {"name": "Kathmandu, Nepal", "lat": 27.70, "lon": 85.32,
     "style": "Tibetan-Nepali carpet", "color": "#ec4899",
     "notes": "Tibetan refugee workshops; hand-knotted on vertical looms"},
    {"name": "Agra, India", "lat": 27.18, "lon": 78.02,
     "style": "Mughal Indo-Persian", "color": "#f97316",
     "notes": "Akbar imported Persian weavers in 1580; Mughal floral designs"},
    {"name": "Donegal, Ireland", "lat": 54.65, "lon": -8.11,
     "style": "Donegal carpet", "color": "#3b82f6",
     "notes": "Hand-tufted Donegal carpets since 1898; Celtic-inspired designs"},
    {"name": "Aubusson, France", "lat": 45.96, "lon": 2.17,
     "style": "Aubusson tapestry", "color": "#a855f7",
     "notes": "UNESCO Intangible Heritage; flat-woven tapestry since 15th century"},
    {"name": "Milas, Turkey", "lat": 37.31, "lon": 27.78,
     "style": "Turkish Milas", "color": "#f59e0b",
     "notes": "Distinctive prayer rugs with mihrab niche; natural dyes; tobacco motif"},
    {"name": "Heriz, Iran", "lat": 38.15, "lon": 47.10,
     "style": "Persian Heriz", "color": "#ef4444",
     "notes": "Bold geometric medallions; durable village carpets; iron-rich water"},
    {"name": "Jaipur, India", "lat": 26.91, "lon": 75.79,
     "style": "Indian dhurrie", "color": "#f97316",
     "notes": "Flat-woven cotton dhurries; prison workshop tradition; bold geometric"},
    {"name": "Ashgabat, Turkmenistan", "lat": 37.96, "lon": 58.38,
     "style": "Turkmen carpet", "color": "#8b5cf6",
     "notes": "National symbol on the flag; Carpet Museum; tekke and yomut guls"},
    {"name": "Axminster, England", "lat": 50.78, "lon": -3.00,
     "style": "Axminster carpet", "color": "#10b981",
     "notes": "Axminster loom invented 1755; tufted cut-pile; Buckingham Palace carpets"},
]

# =====================================================================
# 5. LACE & EMBROIDERY CENTERS (18 locations)
# =====================================================================
LACE_EMBROIDERY = [
    {"name": "Bruges, Belgium", "lat": 51.21, "lon": 3.22,
     "style": "Bruges bobbin lace", "color": "#a855f7",
     "notes": "Bobbin lace since 1500s; Kantcentrum lace school still active"},
    {"name": "Burano, Venice, Italy", "lat": 45.49, "lon": 12.42,
     "style": "Burano needle lace", "color": "#06b6d4",
     "notes": "Punto in aria (stitches in air); school founded 1872 by Countess Marcello"},
    {"name": "Lefkara, Cyprus", "lat": 34.87, "lon": 33.31,
     "style": "Lefkaritika embroidery", "color": "#3b82f6",
     "notes": "UNESCO Intangible Heritage; Leonardo da Vinci bought an altar cloth here"},
    {"name": "Chantilly, France", "lat": 49.19, "lon": 2.47,
     "style": "Chantilly lace", "color": "#ec4899",
     "notes": "Black silk lace; Napoleon III era; delicate floral mesh ground"},
    {"name": "Brussels, Belgium", "lat": 50.85, "lon": 4.35,
     "style": "Brussels needle lace", "color": "#a855f7",
     "notes": "Point de Bruxelles; duchesse lace; royal wedding veils"},
    {"name": "Nottingham, England", "lat": 52.95, "lon": -1.15,
     "style": "Machine lace", "color": "#10b981",
     "notes": "Leavers machine lace since 1760s; democratized lace for the masses"},
    {"name": "Honiton, Devon, England", "lat": 50.80, "lon": -3.19,
     "style": "Honiton bobbin lace", "color": "#10b981",
     "notes": "Queen Victoria's wedding dress lace; floral sprigs on net ground"},
    {"name": "Narsapur, Andhra Pradesh, India", "lat": 16.43, "lon": 81.70,
     "style": "Crochet lace", "color": "#f59e0b",
     "notes": "200,000+ women crochet workers; exported globally since 1844"},
    {"name": "Guizhou Province, China", "lat": 26.65, "lon": 106.63,
     "style": "Miao embroidery", "color": "#f97316",
     "notes": "Hmong silk embroidery; stories encoded in stitches; UNESCO heritage"},
    {"name": "Lucknow, India", "lat": 26.85, "lon": 80.95,
     "style": "Chikankari embroidery", "color": "#06b6d4",
     "notes": "White-on-white shadow work; Mughal Nur Jahan introduced the art"},
    {"name": "Madeira, Portugal", "lat": 32.65, "lon": -16.91,
     "style": "Madeira cutwork embroidery", "color": "#14b8a6",
     "notes": "Bordado Madeira whitework since 1850s; island cottage industry"},
    {"name": "Oaxaca, Mexico", "lat": 17.07, "lon": -96.72,
     "style": "Mexican embroidery", "color": "#f59e0b",
     "notes": "Zapotec and Mixtec traditions; backstrap loom; cross-stitch huipil"},
    {"name": "Tokamachi, Japan", "lat": 37.13, "lon": 138.75,
     "style": "Sashiko stitching", "color": "#ef4444",
     "notes": "Japanese running-stitch reinforcement; boro mending; Edo-era tradition"},
    {"name": "Appenzell, Switzerland", "lat": 47.33, "lon": 9.41,
     "style": "Appenzell embroidery", "color": "#8b5cf6",
     "notes": "Fine whitework; handkerchief embroidery; Swiss precision needlework"},
    {"name": "Beauvais, France", "lat": 49.43, "lon": 2.08,
     "style": "Beauvais tapestry", "color": "#ec4899",
     "notes": "Royal tapestry manufactory since 1664; low-warp technique"},
    {"name": "Alençon, France", "lat": 48.43, "lon": 0.09,
     "style": "Point d'Alencon needle lace", "color": "#ec4899",
     "notes": "UNESCO heritage; finest needle lace; 7-15 hours per square cm"},
    {"name": "Idrija, Slovenia", "lat": 46.00, "lon": 14.03,
     "style": "Idrija bobbin lace", "color": "#3b82f6",
     "notes": "UNESCO Intangible Heritage since 2018; mining town lace tradition"},
    {"name": "Swatow (Shantou), China", "lat": 23.35, "lon": 116.68,
     "style": "Swatow embroidery", "color": "#f97316",
     "notes": "Drawn-thread whitework; exported to Europe as 'Swatow lace'"},
]

# =====================================================================
# 6. DYE & COLOR ORIGINS (22 locations)
# =====================================================================
DYE_COLOR_ORIGINS = [
    {"name": "Sidon, Lebanon", "lat": 33.56, "lon": 35.37,
     "dye": "Tyrian purple", "source": "Murex sea snail",
     "color": "#8b5cf6",
     "notes": "Phoenician purple; 12,000 snails for 1.4g dye; worth its weight in gold"},
    {"name": "Tyre, Lebanon", "lat": 33.27, "lon": 35.20,
     "dye": "Tyrian purple", "source": "Murex brandaris",
     "color": "#8b5cf6",
     "notes": "Ancient dyeing capital; purple restricted to royalty; mounds of crushed shells"},
    {"name": "Gujarat, India", "lat": 22.31, "lon": 72.14,
     "dye": "Indigo", "source": "Indigofera tinctoria",
     "color": "#3b82f6",
     "notes": "Oldest indigo dyeing tradition; Ajrakh block-printing with natural indigo"},
    {"name": "Kano, Nigeria", "lat": 12.00, "lon": 8.52,
     "dye": "Indigo", "source": "Lonchocarpus cyanescens",
     "color": "#3b82f6",
     "notes": "Kano indigo dye pits still active; 'Blue City' of West Africa"},
    {"name": "Oaxaca, Mexico", "lat": 17.07, "lon": -96.72,
     "dye": "Cochineal red", "source": "Dactylopius coccus",
     "color": "#ef4444",
     "notes": "Cochineal insect on nopal cactus; Aztec tribute dye; Spanish colonial export"},
    {"name": "Lanzarote, Canary Islands", "lat": 29.05, "lon": -13.63,
     "dye": "Cochineal red", "source": "Cochineal insect",
     "color": "#ef4444",
     "notes": "Last European cochineal plantation; still cultivated on prickly pear cactus"},
    {"name": "Norfolk, England", "lat": 52.63, "lon": 1.30,
     "dye": "Woad blue", "source": "Isatis tinctoria",
     "color": "#3b82f6",
     "notes": "Ancient Briton war paint; medieval woad balls; replaced by indigo"},
    {"name": "Toulouse, France", "lat": 43.60, "lon": 1.44,
     "dye": "Woad (pastel)", "source": "Isatis tinctoria",
     "color": "#3b82f6",
     "notes": "Pays de Cocagne; woad merchants built Renaissance mansions (hotels particuliers)"},
    {"name": "Isfahan, Iran", "lat": 32.65, "lon": 51.68,
     "dye": "Saffron yellow", "source": "Crocus sativus",
     "color": "#f59e0b",
     "notes": "Persian saffron dyeing tradition; royal yellow for Safavid court textiles"},
    {"name": "Qayen, Iran", "lat": 33.73, "lon": 59.18,
     "dye": "Saffron", "source": "Crocus sativus stigma",
     "color": "#f59e0b",
     "notes": "Khorasan saffron capital; world's highest quality for dyeing and cooking"},
    {"name": "Kutch, Gujarat, India", "lat": 23.73, "lon": 69.86,
     "dye": "Madder red", "source": "Rubia tinctorum",
     "color": "#ef4444",
     "notes": "Alizarin red from madder root; traditional mordant dyeing with alum"},
    {"name": "Iznik, Turkey", "lat": 40.43, "lon": 29.72,
     "dye": "Armenian red (bole)", "source": "Porphyrophora hamelii",
     "color": "#ef4444",
     "notes": "Ottoman ceramic and textile red; Armenian cochineal scale insect"},
    {"name": "Charleston, South Carolina, USA", "lat": 32.78, "lon": -79.93,
     "dye": "Indigo", "source": "Indigofera suffruticosa",
     "color": "#3b82f6",
     "notes": "Eliza Lucas Pinckney's plantations; colonial cash crop alongside rice"},
    {"name": "Tokushima, Japan", "lat": 34.07, "lon": 134.55,
     "dye": "Japanese indigo (ai)", "source": "Persicaria tinctoria",
     "color": "#3b82f6",
     "notes": "Awa indigo tradition; sukumo fermented indigo; Japan Blue heritage"},
    {"name": "Chinchero, Peru", "lat": -13.39, "lon": -72.05,
     "dye": "Cochineal and plant dyes", "source": "Various natural",
     "color": "#ec4899",
     "notes": "Andean dye tradition; 200+ colors from local plants and insects"},
    {"name": "Saint-Denis, Reunion Island", "lat": -20.88, "lon": 55.45,
     "dye": "Vanilla-based tannin", "source": "Tropical plants",
     "color": "#f97316",
     "notes": "Colonial dye-plant gardens; logwood and brazilwood imports"},
    {"name": "Campeche, Mexico", "lat": 19.85, "lon": -90.53,
     "dye": "Logwood black/purple", "source": "Haematoxylum campechianum",
     "color": "#a855f7",
     "notes": "Logwood exported to Europe for black dye; pirates guarded the trade"},
    {"name": "Pernambuco, Brazil", "lat": -8.05, "lon": -34.87,
     "dye": "Brazilwood red", "source": "Paubrasilia echinata",
     "color": "#ef4444",
     "notes": "Country named after the dye tree; pau-brasil red exported to Europe"},
    {"name": "El Salvador", "lat": 13.70, "lon": -89.20,
     "dye": "Maya indigo", "source": "Indigofera suffruticosa",
     "color": "#3b82f6",
     "notes": "Xiquilite plant; Maya Blue pigment for murals and textiles"},
    {"name": "Aix-en-Provence, France", "lat": 43.53, "lon": 5.45,
     "dye": "Synthetic mauveine", "source": "Chemical synthesis",
     "color": "#a855f7",
     "notes": "William Henry Perkin's aniline purple (1856) launched synthetic dye revolution"},
    {"name": "Ludwigshafen, Germany", "lat": 49.48, "lon": 8.44,
     "dye": "Synthetic indigo", "source": "BASF chemical",
     "color": "#3b82f6",
     "notes": "BASF synthesized indigo in 1897; destroyed Indian indigo plantation economy"},
    {"name": "Osaka, Japan", "lat": 34.69, "lon": 135.50,
     "dye": "Ai-zome (indigo)", "source": "Fermented Persicaria",
     "color": "#3b82f6",
     "notes": "Samurai blue; Tokugawa-era cotton indigo dyeing; fire-resistant"},
]

# =====================================================================
# 7. FASHION TEXTILE DISTRICTS (20 locations)
# =====================================================================
FASHION_TEXTILE_DISTRICTS = [
    {"name": "Como, Italy", "lat": 45.81, "lon": 9.08,
     "specialty": "Silk", "color": "#ec4899",
     "notes": "Italian silk capital; 80% of European luxury silk; Ratti, Mantero mills"},
    {"name": "Lyon, France", "lat": 45.76, "lon": 4.84,
     "specialty": "Silk", "color": "#ec4899",
     "notes": "Capital of European silk since 1540; Jacquard loom invented here (1804)"},
    {"name": "Prato, Italy", "lat": 43.88, "lon": 11.10,
     "specialty": "Recycled wool", "color": "#10b981",
     "notes": "Centuries-old cenciaioli wool recycling; circular fashion pioneer"},
    {"name": "Biella, Italy", "lat": 45.56, "lon": 8.05,
     "specialty": "Luxury wool", "color": "#06b6d4",
     "notes": "Zegna, Loro Piana, Cerruti origins; Alpine water for finishing"},
    {"name": "Outer Hebrides, Scotland", "lat": 57.76, "lon": -7.02,
     "specialty": "Harris Tweed", "color": "#14b8a6",
     "notes": "Only fabric protected by Act of Parliament; hand-woven by islanders"},
    {"name": "Yorkshire, England", "lat": 53.80, "lon": -1.55,
     "specialty": "Worsted wool", "color": "#10b981",
     "notes": "Bradford wool exchange; Pennine mills; heritage suiting cloth"},
    {"name": "Krefeld, Germany", "lat": 51.33, "lon": 6.56,
     "specialty": "Silk and velvet", "color": "#a855f7",
     "notes": "Samt und Seide (Velvet and Silk); Huguenot weavers; Verseidag"},
    {"name": "Roubaix, France", "lat": 50.69, "lon": 3.17,
     "specialty": "Wool and cotton", "color": "#8b5cf6",
     "notes": "French Manchester; La Piscine textile museum; Lainiere de Roubaix"},
    {"name": "Surat, Gujarat, India", "lat": 21.17, "lon": 72.83,
     "specialty": "Synthetic textiles", "color": "#f97316",
     "notes": "Zari (metallic thread) capital; 40% of India's synthetic fabric"},
    {"name": "Daegu, South Korea", "lat": 35.87, "lon": 128.60,
     "specialty": "Synthetic fibers", "color": "#3b82f6",
     "notes": "Korean textile capital; polyester and nylon manufacturing hub"},
    {"name": "Bursa, Turkey", "lat": 40.18, "lon": 29.06,
     "specialty": "Silk", "color": "#f59e0b",
     "notes": "Ottoman silk capital; Koza Han silk caravanserai; still produces silk"},
    {"name": "Suzhou, China", "lat": 31.30, "lon": 120.62,
     "specialty": "Silk brocade", "color": "#f59e0b",
     "notes": "Song dynasty silk capital; yunjin cloud brocade; UNESCO heritage"},
    {"name": "Cheshire, England (Macclesfield)", "lat": 53.26, "lon": -2.13,
     "specialty": "Silk", "color": "#10b981",
     "notes": "English silk weaving center; 70+ mills at peak; Silk Heritage Centre"},
    {"name": "Kojima, Okayama, Japan", "lat": 34.47, "lon": 133.81,
     "specialty": "Premium denim", "color": "#3b82f6",
     "notes": "Japanese selvedge denim capital; vintage loom revival; artisan jeans"},
    {"name": "Coimbatore, India", "lat": 11.00, "lon": 76.96,
     "specialty": "Cotton knits", "color": "#f59e0b",
     "notes": "Tirupur nearby: T-shirt capital of the world; knitwear export hub"},
    {"name": "Tilburg, Netherlands", "lat": 51.56, "lon": 5.09,
     "specialty": "Wool", "color": "#06b6d4",
     "notes": "Dutch wool capital; TextielMuseum with working textile lab"},
    {"name": "Savile Row, London, England", "lat": 51.51, "lon": -0.14,
     "specialty": "Bespoke suiting", "color": "#a855f7",
     "notes": "World's finest bespoke tailoring street; Super 200s wool suits"},
    {"name": "Nimes, France", "lat": 43.84, "lon": 4.36,
     "specialty": "Denim", "color": "#3b82f6",
     "notes": "Origin of 'de Nimes' (denim); serge de Nimes cotton twill"},
    {"name": "Varanasi, India", "lat": 25.32, "lon": 83.01,
     "specialty": "Silk brocade", "color": "#f59e0b",
     "notes": "Banarasi silk sari district; 5000+ looms; Mughal-era heritage"},
    {"name": "Hangzhou, China", "lat": 30.27, "lon": 120.15,
     "specialty": "Silk", "color": "#f59e0b",
     "notes": "National Silk Museum; imperial workshops; Marco Polo's City of Heaven"},
]

# =====================================================================
# 8. BATIK & PRINT TRADITIONS (20 locations)
# =====================================================================
BATIK_PRINT_TRADITIONS = [
    {"name": "Solo (Surakarta), Java, Indonesia", "lat": -7.57, "lon": 110.82,
     "style": "Javanese batik tulis", "color": "#f59e0b",
     "notes": "Royal court batik; parang and kawung motifs restricted to royalty"},
    {"name": "Yogyakarta, Java, Indonesia", "lat": -7.80, "lon": 110.36,
     "style": "Javanese batik", "color": "#f59e0b",
     "notes": "Hand-drawn (tulis) batik; UNESCO Intangible Heritage (2009)"},
    {"name": "Pekalongan, Java, Indonesia", "lat": -6.89, "lon": 109.67,
     "style": "Coastal batik pesisir", "color": "#06b6d4",
     "notes": "Chinese, Arab, and Dutch influenced; bright colors; City of Batik"},
    {"name": "Abeokuta, Nigeria", "lat": 7.16, "lon": 3.35,
     "style": "Yoruba adire", "color": "#8b5cf6",
     "notes": "Adire resist-dyeing; starch-paste (eleko) and tied (oniko) methods"},
    {"name": "Kyoto, Japan", "lat": 35.01, "lon": 135.77,
     "style": "Japanese shibori", "color": "#ec4899",
     "notes": "Arashi pole-wrapping; kanoko tie-dyeing; 1300-year tradition"},
    {"name": "Jaipur, Rajasthan, India", "lat": 26.91, "lon": 75.79,
     "style": "Block print (Sanganeri)", "color": "#f97316",
     "notes": "Hand-carved wooden blocks; Sanganer and Bagru printing villages"},
    {"name": "Bamako, Mali", "lat": 12.64, "lon": -8.00,
     "style": "Bogolan (mud cloth)", "color": "#a855f7",
     "notes": "Bogolanfini fermented mud dyeing on cotton; Bamana women's tradition"},
    {"name": "Accra, Ghana", "lat": 5.60, "lon": -0.19,
     "style": "Kente cloth", "color": "#10b981",
     "notes": "Ashanti kente strip-weaving; silk and cotton; royal ceremonial cloth"},
    {"name": "Kumasi, Ghana", "lat": 6.69, "lon": -1.62,
     "style": "Ashanti adinkra", "color": "#10b981",
     "notes": "Bonwire kente village; adinkra stamped mourning cloth"},
    {"name": "Cirebon, Java, Indonesia", "lat": -6.71, "lon": 108.56,
     "style": "Mega mendung batik", "color": "#3b82f6",
     "notes": "Cloud motif from Chinese influence; unique to Cirebon"},
    {"name": "Okinawa, Japan", "lat": 26.34, "lon": 127.80,
     "style": "Bingata stencil-dyeing", "color": "#ec4899",
     "notes": "Ryukyuan resist-dyed textile; stencil paste; vibrant tropical palette"},
    {"name": "Kutch, Gujarat, India", "lat": 23.73, "lon": 69.86,
     "style": "Bandhani tie-dye", "color": "#f97316",
     "notes": "Thousands of tiny tied dots; 5000-year tradition; bridal textiles"},
    {"name": "Vlissingen, Netherlands", "lat": 51.44, "lon": 3.57,
     "style": "Dutch wax print", "color": "#ef4444",
     "notes": "Vlisco founded 1846; copied Indonesian batik with roller printing"},
    {"name": "Kano, Nigeria", "lat": 12.00, "lon": 8.52,
     "style": "Hausa indigo resist", "color": "#3b82f6",
     "notes": "Ancient indigo pits; tied and stitched resist techniques"},
    {"name": "Lome, Togo", "lat": 6.17, "lon": 1.23,
     "style": "Nana Benz wax trade", "color": "#f59e0b",
     "notes": "Nana Benz women traders dominated wax-print commerce in West Africa"},
    {"name": "San Cristobal de las Casas, Mexico", "lat": 16.74, "lon": -92.64,
     "style": "Maya brocade weaving", "color": "#14b8a6",
     "notes": "Tzotzil Maya backstrap loom brocade; each village has unique patterns"},
    {"name": "Rajshahi, Bangladesh", "lat": 24.37, "lon": 88.60,
     "style": "Jamdani muslin", "color": "#06b6d4",
     "notes": "UNESCO Intangible Heritage; supplementary weft floating on fine muslin"},
    {"name": "Isfahan, Iran", "lat": 32.65, "lon": 51.68,
     "style": "Qalamkar block print", "color": "#ef4444",
     "notes": "Hand-printed cotton with wooden blocks; Safavid-era royal textile"},
    {"name": "Ahmedabad, India", "lat": 23.02, "lon": 72.57,
     "style": "Ajrakh block print", "color": "#f97316",
     "notes": "Resist and mordant printing; indigo and madder; Sindhi tradition"},
    {"name": "Arimatsu, Nagoya, Japan", "lat": 35.06, "lon": 136.97,
     "style": "Arimatsu shibori", "color": "#ec4899",
     "notes": "Tokugawa-era shibori center; 100+ tie-dye techniques; national heritage"},
]

# =====================================================================
# 9. TEXTILE MUSEUMS (18 locations)
# =====================================================================
TEXTILE_MUSEUMS = [
    {"name": "The Textile Museum", "city": "Washington, D.C., USA",
     "lat": 38.91, "lon": -77.05, "color": "#3b82f6",
     "notes": "George Hewitt Myers collection; 20,000+ textiles; now at GWU campus"},
    {"name": "MIAT (Museum of Industrial Archaeology and Textiles)", "city": "Ghent, Belgium",
     "lat": 51.06, "lon": 3.73, "color": "#14b8a6",
     "notes": "Working cotton mill; mule jenny demonstrations; industrial heritage"},
    {"name": "Museo del Tessuto", "city": "Prato, Italy",
     "lat": 43.88, "lon": 11.10, "color": "#ef4444",
     "notes": "7,000+ textile samples; medieval to contemporary; wool recycling heritage"},
    {"name": "Fashion and Textile Museum", "city": "London, England",
     "lat": 51.50, "lon": -0.08, "color": "#ec4899",
     "notes": "Founded by Zandra Rhodes; contemporary fashion and textile exhibitions"},
    {"name": "Victoria & Albert Museum", "city": "London, England",
     "lat": 51.50, "lon": -0.17, "color": "#8b5cf6",
     "notes": "World's largest textile collection; 100,000+ objects; Ardabil Carpet"},
    {"name": "National Silk Museum", "city": "Hangzhou, China",
     "lat": 30.24, "lon": 120.14, "color": "#f59e0b",
     "notes": "China's only national silk museum; 5,000-year silk history"},
    {"name": "Musee des Tissus", "city": "Lyon, France",
     "lat": 45.76, "lon": 4.83, "color": "#ec4899",
     "notes": "2.5 million textile pieces; 4,500 years of silk history; Jacquard looms"},
    {"name": "TextielMuseum", "city": "Tilburg, Netherlands",
     "lat": 51.56, "lon": 5.09, "color": "#06b6d4",
     "notes": "Working textile lab; artists-in-residence; digital jacquard weaving"},
    {"name": "Cooper Hewitt Smithsonian Design Museum", "city": "New York, USA",
     "lat": 40.78, "lon": -73.96, "color": "#3b82f6",
     "notes": "30,000+ textiles; wallcoverings; Andrew Carnegie mansion"},
    {"name": "Calico Museum of Textiles", "city": "Ahmedabad, India",
     "lat": 23.04, "lon": 72.58, "color": "#f97316",
     "notes": "Finest Indian textile collection; Mughal court textiles; Sarabhai Foundation"},
    {"name": "Museum of Turkish and Islamic Arts", "city": "Istanbul, Turkey",
     "lat": 41.01, "lon": 28.97, "color": "#f59e0b",
     "notes": "World's finest carpet collection; Seljuk and Ottoman rugs; Ibrahim Pasha Palace"},
    {"name": "Whitchurch Silk Mill", "city": "Hampshire, England",
     "lat": 51.24, "lon": -1.34, "color": "#10b981",
     "notes": "Oldest working silk mill in the UK (est. 1815); waterwheel powered"},
    {"name": "Musee de l'Impression sur Etoffes", "city": "Mulhouse, France",
     "lat": 47.75, "lon": 7.34, "color": "#a855f7",
     "notes": "6 million fabric samples; printed textile history; Alsatian design"},
    {"name": "Japan Folk Crafts Museum (Mingeikan)", "city": "Tokyo, Japan",
     "lat": 35.66, "lon": 139.69, "color": "#ef4444",
     "notes": "Yanagi Soetsu's mingei movement; sashiko, kasuri, boro textiles"},
    {"name": "Textile Museum of Canada", "city": "Toronto, Canada",
     "lat": 43.65, "lon": -79.39, "color": "#14b8a6",
     "notes": "13,000+ artifacts from 200+ regions; contemporary fiber art"},
    {"name": "Museum of International Folk Art", "city": "Santa Fe, NM, USA",
     "lat": 35.67, "lon": -105.93, "color": "#a855f7",
     "notes": "Largest folk art collection; 135,000+ textiles; global weaving traditions"},
    {"name": "Deutsches Textilmuseum", "city": "Krefeld, Germany",
     "lat": 51.33, "lon": 6.56, "color": "#8b5cf6",
     "notes": "30,000+ objects; Coptic textiles; pre-Columbian Andean fabrics"},
    {"name": "National Museum of the American Indian", "city": "Washington, D.C., USA",
     "lat": 38.89, "lon": -77.02, "color": "#3b82f6",
     "notes": "Navajo weaving, Andean textiles, Chilkat blankets; Smithsonian"},
]

# =====================================================================
# 10. FIBER CROP ORIGINS (18 locations)
# =====================================================================
FIBER_CROP_ORIGINS = [
    {"name": "Indus Valley (Mehrgarh), Pakistan", "lat": 29.39, "lon": 67.62,
     "fiber": "Cotton", "era": "5000 BC", "color": "#06b6d4",
     "notes": "Oldest known cotton cultivation; Gossypium arboreum domestication"},
    {"name": "Mohenjo-daro, Pakistan", "lat": 27.33, "lon": 68.14,
     "fiber": "Cotton", "era": "2500 BC", "color": "#06b6d4",
     "notes": "Indus civilization cotton cloth fragments; indigo-dyed cotton found"},
    {"name": "Nile Delta, Egypt", "lat": 30.90, "lon": 31.20,
     "fiber": "Flax (linen)", "era": "5000 BC", "color": "#f59e0b",
     "notes": "Egyptian linen for mummification and daily wear; finest royal linen"},
    {"name": "Jericho, Palestine", "lat": 31.87, "lon": 35.44,
     "fiber": "Flax (linen)", "era": "8000 BC", "color": "#f59e0b",
     "notes": "Earliest known flax fibers from Dzudzuana Cave (nearby Georgia); Neolithic linen"},
    {"name": "Hemudu, Zhejiang, China", "lat": 30.00, "lon": 121.35,
     "fiber": "Silk", "era": "3630 BC", "color": "#ec4899",
     "notes": "Earliest evidence of silk fibers; Bombyx mori domestication began here"},
    {"name": "Yangtze Delta, China", "lat": 31.00, "lon": 121.00,
     "fiber": "Silk", "era": "3000 BC", "color": "#ec4899",
     "notes": "Sericulture heartland; mulberry cultivation; imperial silk industry"},
    {"name": "Gansu, China", "lat": 36.06, "lon": 103.83,
     "fiber": "Hemp", "era": "4000 BC", "color": "#10b981",
     "notes": "Cannabis sativa fiber for rope and cloth; Yangshao culture textiles"},
    {"name": "Central Asia (Kazakhstan steppe)", "lat": 48.00, "lon": 68.00,
     "fiber": "Hemp", "era": "3000 BC", "color": "#10b981",
     "notes": "Scythian hemp use documented by Herodotus; nomadic textile culture"},
    {"name": "Mesopotamia (Southern Iraq)", "lat": 31.00, "lon": 47.00,
     "fiber": "Wool", "era": "4000 BC", "color": "#8b5cf6",
     "notes": "Earliest wool textiles; Sumerian sheep domestication; Uruk period cloth"},
    {"name": "Anatolia (Catalhoyuk), Turkey", "lat": 37.67, "lon": 32.83,
     "fiber": "Wool", "era": "7000 BC", "color": "#8b5cf6",
     "notes": "Earliest sheep herding evidence; proto-wool from wild mouflon"},
    {"name": "Yucatan, Mexico", "lat": 20.63, "lon": -89.62,
     "fiber": "Sisal (henequen)", "era": "Pre-Columbian", "color": "#14b8a6",
     "notes": "Agave sisalana fiber; Maya rope and hammock making; Green Gold era"},
    {"name": "Manila, Philippines", "lat": 14.60, "lon": 120.98,
     "fiber": "Abaca (Manila hemp)", "era": "1500s", "color": "#14b8a6",
     "notes": "Musa textilis banana fiber; world's strongest natural fiber; rope and textiles"},
    {"name": "Bengal Delta, Bangladesh", "lat": 23.00, "lon": 90.00,
     "fiber": "Jute", "era": "1800s", "color": "#f97316",
     "notes": "Golden fiber; world's largest jute producer; burlap and hessian cloth"},
    {"name": "Arequipa, Peru", "lat": -16.41, "lon": -71.54,
     "fiber": "Alpaca", "era": "3000 BC", "color": "#ef4444",
     "notes": "Alpaca domestication for fiber; baby alpaca 22.5 micron; Inca textile legacy"},
    {"name": "Lake Titicaca, Peru/Bolivia", "lat": -15.84, "lon": -70.02,
     "fiber": "Vicuna", "era": "Pre-Inca", "color": "#ef4444",
     "notes": "Finest animal fiber (12 micron); Inca royal cloth of gold; near extinction recovery"},
    {"name": "Changtang Plateau, Tibet/Ladakh", "lat": 33.50, "lon": 77.00,
     "fiber": "Cashmere (pashmina)", "era": "3rd century BC", "color": "#a855f7",
     "notes": "Changthangi goats at 4500m; 12-14 micron fiber; pashmina shawl origin"},
    {"name": "New Zealand (Canterbury)", "lat": -43.53, "lon": 172.63,
     "fiber": "New Zealand flax (harakeke)", "era": "Pre-European", "color": "#3b82f6",
     "notes": "Phormium tenax; Maori weaving (raranga); cloaks and baskets"},
    {"name": "Assam, India", "lat": 26.17, "lon": 91.57,
     "fiber": "Muga silk", "era": "1600s", "color": "#f59e0b",
     "notes": "Golden wild silk from Antheraea assamensis moth; unique to Assam"},
]

# =====================================================================
# MODE CONFIGURATION
# =====================================================================
MAP_MODES = [
    "Silk Road Heritage",
    "Traditional Weaving Centers",
    "Cotton & Textile Mills",
    "Carpet & Rug Traditions",
    "Lace & Embroidery Centers",
    "Dye & Color Origins",
    "Fashion Textile Districts",
    "Batik & Print Traditions",
    "Textile Museums",
    "Fiber Crop Origins",
]

MODE_DATA = {
    "Silk Road Heritage": SILK_ROAD_HERITAGE,
    "Traditional Weaving Centers": TRADITIONAL_WEAVING,
    "Cotton & Textile Mills": COTTON_TEXTILE_MILLS,
    "Carpet & Rug Traditions": CARPET_RUG_TRADITIONS,
    "Lace & Embroidery Centers": LACE_EMBROIDERY,
    "Dye & Color Origins": DYE_COLOR_ORIGINS,
    "Fashion Textile Districts": FASHION_TEXTILE_DISTRICTS,
    "Batik & Print Traditions": BATIK_PRINT_TRADITIONS,
    "Textile Museums": TEXTILE_MUSEUMS,
    "Fiber Crop Origins": FIBER_CROP_ORIGINS,
}

MODE_COLORS = {
    "Silk Road Heritage": "#f59e0b",
    "Traditional Weaving Centers": "#10b981",
    "Cotton & Textile Mills": "#3b82f6",
    "Carpet & Rug Traditions": "#ef4444",
    "Lace & Embroidery Centers": "#a855f7",
    "Dye & Color Origins": "#ec4899",
    "Fashion Textile Districts": "#06b6d4",
    "Batik & Print Traditions": "#f97316",
    "Textile Museums": "#8b5cf6",
    "Fiber Crop Origins": "#14b8a6",
}

MODE_DESCRIPTIONS = {
    "Silk Road Heritage": "Ancient trade routes, Silk Road waypoints, and the 4,000-mile network from Xi'an to Constantinople.",
    "Traditional Weaving Centers": "Living weaving traditions from Varanasi silk to Oaxaca backstrap looms and Kyoto kimono.",
    "Cotton & Textile Mills": "Industrial Revolution mills and factory cities from Manchester to Lowell to Ahmedabad.",
    "Carpet & Rug Traditions": "Hand-knotted and flat-woven carpets spanning Persian, Turkish, Navajo, and Berber cultures.",
    "Lace & Embroidery Centers": "Needle lace, bobbin lace, embroidery, and decorative stitching traditions worldwide.",
    "Dye & Color Origins": "Natural and synthetic dye sources: Tyrian purple, indigo, cochineal, saffron, woad, and more.",
    "Fashion Textile Districts": "Modern textile production hubs from Como silk to Harris Tweed to Japanese selvedge denim.",
    "Batik & Print Traditions": "Resist-dyeing traditions: Javanese batik, Nigerian adire, Japanese shibori, Indian block print.",
    "Textile Museums": "World-class textile museums and collections preserving thousands of years of fabric heritage.",
    "Fiber Crop Origins": "Where textile fibers were first cultivated: cotton, flax, silk, hemp, wool, alpaca, and more.",
}


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def _popup_html(title, fields, accent=_ACCENT):
    """Build a dark-styled HTML popup for Folium, escaping all user data."""
    safe_title = html_module.escape(str(title))
    safe_accent = html_module.escape(str(accent))
    result = (
        f"<div style='min-width:220px;background:{_CARD};color:{_TEXT};"
        f"padding:10px;border-radius:8px;border:1px solid {safe_accent};'>"
        f"<b style='color:{safe_accent};font-size:14px;'>{safe_title}</b><br>"
    )
    for label, value in fields.items():
        safe_label = html_module.escape(str(label))
        safe_val = html_module.escape(str(value))
        result += (
            f"<span style='color:{_TEXT2};'>{safe_label}:</span> "
            f"{safe_val}<br>"
        )
    result += "</div>"
    return result


def _build_map(data, center, zoom, popup_fn, tooltip_fn, route_line=False):
    """Build a dark Folium map with CircleMarkers for the given data."""
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )
    if route_line and len(data) > 1:
        coords = [[d["lat"], d["lon"]] for d in data]
        folium.PolyLine(
            locations=coords,
            color=data[0].get("color", _ACCENT),
            weight=2,
            opacity=0.4,
            dash_array="8 6",
        ).add_to(m)
    for item in data:
        color = item.get("color", _ACCENT)
        popup_content = popup_fn(item)
        tooltip_text = html_module.escape(str(tooltip_fn(item)))
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=tooltip_text,
        ).add_to(m)
    return m


def _render_stats(cols_data):
    """Render a stats row with st.metric."""
    cols = st.columns(len(cols_data))
    for col, (label, value) in zip(cols, cols_data):
        col.metric(label, value)


def _render_table_download(df, filename, key):
    """Show a dataframe and CSV download button."""
    st.dataframe(df, use_container_width=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download {filename}",
        csv_data,
        filename,
        "text/csv",
        key=key,
    )


# =====================================================================
# INDIVIDUAL MODE RENDERERS
# =====================================================================

def _render_silk_road():
    """Render Silk Road Heritage mode."""
    data = SILK_ROAD_HERITAGE
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Silk Road Heritage'])}</p>",
        unsafe_allow_html=True,
    )
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Route Span", "~7,000 km"),
        ("Era Range", "500 BC - 1300 AD"),
        ("Civilizations", "12+"),
    ])
    sorted_data = sorted(data, key=lambda d: d["lon"])
    m = _build_map(
        sorted_data, [38, 65], 3,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Era": d["era"], "Role": d["role"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['era']})",
        route_line=True,
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Era": d["era"], "Role": d["role"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "silk_road_heritage.csv", "dl_silk_road")


def _render_traditional_weaving():
    """Render Traditional Weaving Centers mode."""
    data = TRADITIONAL_WEAVING
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Traditional Weaving Centers'])}</p>",
        unsafe_allow_html=True,
    )
    continents = set()
    for d in data:
        if d["lon"] > 60:
            continents.add("Asia")
        elif d["lon"] < -30:
            continents.add("Americas")
        elif d["lat"] < 15:
            continents.add("Africa")
        else:
            continents.add("Europe/Middle East")
    _render_stats([
        ("Centers Mapped", len(data)),
        ("Continents", len(continents)),
        ("Traditions", len(data)),
    ])
    m = _build_map(
        data, [20, 40], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Tradition": d["tradition"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['tradition']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Tradition": d["tradition"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "traditional_weaving.csv", "dl_trad_weaving")


def _render_cotton_mills():
    """Render Cotton & Textile Mills mode."""
    data = COTTON_TEXTILE_MILLS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Cotton & Textile Mills'])}</p>",
        unsafe_allow_html=True,
    )
    countries = len({d["name"].split(",")[-1].strip() for d in data})
    _render_stats([
        ("Mills Mapped", len(data)),
        ("Countries", countries),
        ("Era Span", "1700s - 1920s"),
    ])
    m = _build_map(
        data, [35, 10], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Era": d["era"], "Type": d["type"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['era']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Era": d["era"], "Type": d["type"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "cotton_textile_mills.csv", "dl_cotton_mills")


def _render_carpet_traditions():
    """Render Carpet & Rug Traditions mode."""
    data = CARPET_RUG_TRADITIONS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Carpet & Rug Traditions'])}</p>",
        unsafe_allow_html=True,
    )
    styles = list({d["style"].split(" ")[0] for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Style Families", len(styles)),
        ("Countries", len({d["name"].split(",")[-1].strip() for d in data})),
    ])
    m = _build_map(
        data, [34, 50], 3,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Style": d["style"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['style']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Style": d["style"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "carpet_rug_traditions.csv", "dl_carpets")


def _render_lace_embroidery():
    """Render Lace & Embroidery Centers mode."""
    data = LACE_EMBROIDERY
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Lace & Embroidery Centers'])}</p>",
        unsafe_allow_html=True,
    )
    countries = len({d["name"].split(",")[-1].strip() for d in data})
    _render_stats([
        ("Centers Mapped", len(data)),
        ("Countries", countries),
        ("Techniques", len(data)),
    ])
    m = _build_map(
        data, [38, 20], 3,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Style": d["style"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['style']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Style": d["style"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "lace_embroidery.csv", "dl_lace")


def _render_dye_origins():
    """Render Dye & Color Origins mode."""
    data = DYE_COLOR_ORIGINS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Dye & Color Origins'])}</p>",
        unsafe_allow_html=True,
    )
    dye_types = list({d["dye"].split(" ")[0] for d in data})
    natural = sum(1 for d in data if "Synthetic" not in d["source"])
    synthetic = sum(1 for d in data if "Synthetic" in d["source"] or "Chemical" in d["source"] or "BASF" in d["source"])
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Dye Types", len(dye_types)),
        ("Natural Sources", natural),
        ("Synthetic", synthetic),
    ])
    m = _build_map(
        data, [30, 30], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Dye": d["dye"], "Source": d["source"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['dye']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Dye": d["dye"], "Source": d["source"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "dye_color_origins.csv", "dl_dyes")


def _render_fashion_districts():
    """Render Fashion Textile Districts mode."""
    data = FASHION_TEXTILE_DISTRICTS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Fashion Textile Districts'])}</p>",
        unsafe_allow_html=True,
    )
    specialties = list({d["specialty"] for d in data})
    _render_stats([
        ("Districts Mapped", len(data)),
        ("Specialties", len(specialties)),
        ("Countries", len({d["name"].split(",")[-1].strip() for d in data})),
    ])
    m = _build_map(
        data, [38, 30], 3,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Specialty": d["specialty"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['specialty']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Specialty": d["specialty"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "fashion_textile_districts.csv", "dl_fashion")


def _render_batik_prints():
    """Render Batik & Print Traditions mode."""
    data = BATIK_PRINT_TRADITIONS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Batik & Print Traditions'])}</p>",
        unsafe_allow_html=True,
    )
    asia_count = sum(1 for d in data if d["lon"] > 60)
    africa_count = sum(1 for d in data if -20 < d["lon"] < 50 and d["lat"] < 20)
    other_count = len(data) - asia_count - africa_count
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Asian Sites", asia_count),
        ("African Sites", africa_count),
        ("Other Regions", other_count),
    ])
    m = _build_map(
        data, [10, 60], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Style": d["style"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['style']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Style": d["style"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "batik_print_traditions.csv", "dl_batik")


def _render_textile_museums():
    """Render Textile Museums mode."""
    data = TEXTILE_MUSEUMS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Textile Museums'])}</p>",
        unsafe_allow_html=True,
    )
    countries = len({d["city"].split(",")[-1].strip() for d in data})
    _render_stats([
        ("Museums Mapped", len(data)),
        ("Countries", countries),
        ("Highlight", "V&A: 100k+ objects"),
    ])
    m = _build_map(
        data, [35, 10], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "City": d["city"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['city']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Museum": d["name"], "City": d["city"],
        "Latitude": d["lat"], "Longitude": d["lon"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "textile_museums.csv", "dl_museums")


def _render_fiber_origins():
    """Render Fiber Crop Origins mode."""
    data = FIBER_CROP_ORIGINS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Fiber Crop Origins'])}</p>",
        unsafe_allow_html=True,
    )
    fibers = list({d["fiber"].split(" ")[0] for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Fiber Types", len(fibers)),
        ("Era Range", "8000 BC - 1800s"),
        ("Continents", "6"),
    ])
    m = _build_map(
        data, [25, 60], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Fiber": d["fiber"], "Era": d["era"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['fiber']} ({d['era']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Fiber": d["fiber"], "Era": d["era"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "fiber_crop_origins.csv", "dl_fibers")


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================

def render_textile_maps_tab():
    """Render the Textile & Fabric Maps tab for TerraScout AI."""

    st.markdown(
        '<div class="tab-header emerald">'
        '<h4>\U0001f9f5 Textile & Fabric Maps</h4>'
        '<p>Weaving traditions, silk roads, and textile heritage worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected = st.selectbox("Map Mode", MAP_MODES, key="textile_maps_mode")

    mode_color = MODE_COLORS.get(selected, _ACCENT)
    st.markdown(
        f"<hr style='border-color:{html_module.escape(mode_color)};opacity:0.4;'>",
        unsafe_allow_html=True,
    )

    # Dispatch to the appropriate renderer
    if selected == "Silk Road Heritage":
        _render_silk_road()
    elif selected == "Traditional Weaving Centers":
        _render_traditional_weaving()
    elif selected == "Cotton & Textile Mills":
        _render_cotton_mills()
    elif selected == "Carpet & Rug Traditions":
        _render_carpet_traditions()
    elif selected == "Lace & Embroidery Centers":
        _render_lace_embroidery()
    elif selected == "Dye & Color Origins":
        _render_dye_origins()
    elif selected == "Fashion Textile Districts":
        _render_fashion_districts()
    elif selected == "Batik & Print Traditions":
        _render_batik_prints()
    elif selected == "Textile Museums":
        _render_textile_museums()
    elif selected == "Fiber Crop Origins":
        _render_fiber_origins()
