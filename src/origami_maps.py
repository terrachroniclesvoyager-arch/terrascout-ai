# -*- coding: utf-8 -*-
"""
Origami & Paper Arts Explorer module for TerraScout AI.
Maps 10 thematic views of origami heritage, papermaking history, paper art
museums, kirigami traditions, kite-making cultures, and paper architecture.
All data is curated; no external API key required.
"""

import streamlit as st
try:
    import folium
    from folium.plugins import MarkerCluster
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
# 1. JAPANESE ORIGAMI HERITAGE (22 locations)
# =====================================================================
JAPANESE_ORIGAMI_HERITAGE = [
    {"name": "Origami Kaikan, Tokyo", "lat": 35.7013, "lon": 139.7630,
     "type": "Museum & Workshop",
     "color": "#ef4444",
     "notes": "Iconic origami center in Yushima; daily workshops, gallery of master works, paper dyeing studio"},
    {"name": "Nippon Origami Association, Tokyo", "lat": 35.6897, "lon": 139.6917,
     "type": "Organization HQ",
     "color": "#ef4444",
     "notes": "Japan's national origami society; certifies origami instructors; publishes monthly magazine"},
    {"name": "Ochanomizu Origamido, Tokyo", "lat": 35.6996, "lon": 139.7632,
     "type": "Studio & Gallery",
     "color": "#f59e0b",
     "notes": "Historic paper arts district; master folders demonstrate traditional and modern techniques"},
    {"name": "International Origami Center, Tokyo", "lat": 35.6762, "lon": 139.6503,
     "type": "Cultural Center",
     "color": "#f59e0b",
     "notes": "Promotes origami as cultural diplomacy; hosts international exchange programs"},
    {"name": "Sendai Tanabata Festival Origami", "lat": 38.2602, "lon": 140.8822,
     "type": "Festival & Tradition",
     "color": "#8b5cf6",
     "notes": "Annual August festival featuring massive origami kusudama streamers and paper decorations"},
    {"name": "Kyoto Paper Museum (Kamigyo)", "lat": 35.0302, "lon": 135.7584,
     "type": "Museum",
     "color": "#06b6d4",
     "notes": "Traditional washi paper museum; Heian period paper folding artifacts; chiyogami displays"},
    {"name": "Echizen Washi Village, Fukui", "lat": 35.9073, "lon": 136.1668,
     "type": "Paper Making Heritage",
     "color": "#10b981",
     "notes": "1,500-year washi tradition; UNESCO Intangible Heritage; origami-grade paper production"},
    {"name": "Gifu City Paper Lantern Workshop", "lat": 35.4233, "lon": 136.7607,
     "type": "Studio",
     "color": "#f97316",
     "notes": "Paper lantern and origami tradition; cormorant fishing paper boat floats"},
    {"name": "Akita Katagami Paper Stencils", "lat": 39.7186, "lon": 140.1024,
     "type": "Heritage Craft",
     "color": "#ec4899",
     "notes": "Intricate paper stencil cutting (katagami) for kimono dyeing since Edo period"},
    {"name": "Mino Washi Museum, Gifu", "lat": 35.5446, "lon": 136.9075,
     "type": "Museum & Workshop",
     "color": "#10b981",
     "notes": "UNESCO-listed Mino washi papermaking; origami paper workshops; 1,300-year tradition"},
    {"name": "Kurotani Washi, Kyoto", "lat": 35.3453, "lon": 135.1972,
     "type": "Paper Mill Heritage",
     "color": "#06b6d4",
     "notes": "800-year mulberry paper tradition; samurai armor paper; modern origami sheets"},
    {"name": "Tosa Washi Center, Kochi", "lat": 33.5590, "lon": 133.5311,
     "type": "Museum & Workshop",
     "color": "#3b82f6",
     "notes": "Tosa washi since 1,000 AD; thinnest handmade paper in world; origami specialty sheets"},
    {"name": "Ise Grand Shrine Origami Ofuda", "lat": 34.4551, "lon": 136.7260,
     "type": "Sacred Tradition",
     "color": "#a855f7",
     "notes": "Shinto paper folding (shide, gohei); sacred zigzag paper streamers; ritual origami"},
    {"name": "Ogawamachi Washi Village, Saitama", "lat": 36.0568, "lon": 139.2638,
     "type": "Paper Village",
     "color": "#14b8a6",
     "notes": "Hosokawa-shi washi (UNESCO); handmade origami paper; traditional paper screens"},
    {"name": "Matsue Horikawa Paper Boats", "lat": 35.4738, "lon": 133.0486,
     "type": "Living Tradition",
     "color": "#8b5cf6",
     "notes": "Paper boat floating ceremonies; castle moat paper lantern festival"},
    {"name": "Hakone Yosegi-Zaiku & Origami", "lat": 35.2329, "lon": 139.0701,
     "type": "Craft Center",
     "color": "#f59e0b",
     "notes": "Traditional puzzle boxes and origami; marquetry paper craft; Tokaido road heritage"},
    {"name": "Nagoya Noshi Origami Tradition", "lat": 35.1815, "lon": 136.9066,
     "type": "Cultural Tradition",
     "color": "#ef4444",
     "notes": "Noshi ceremonial paper wrapping; wedding gift origami; formal folding school"},
    {"name": "Awagami Factory, Tokushima", "lat": 34.0658, "lon": 134.5593,
     "type": "Paper Mill & Gallery",
     "color": "#10b981",
     "notes": "Awa washi since 1585; artisan origami papers; international artist collaborations"},
    {"name": "Ozu Washi, Tokyo Nihonbashi", "lat": 35.6870, "lon": 139.7747,
     "type": "Historic Paper Shop",
     "color": "#f97316",
     "notes": "Founded 1653; Edo-period washi merchant; largest chiyogami origami paper selection"},
    {"name": "Yoshino Washi, Nara", "lat": 34.3978, "lon": 135.8582,
     "type": "Paper Heritage",
     "color": "#3b82f6",
     "notes": "Yoshino handmade paper; ultra-thin for conservation origami; 1,000+ year tradition"},
    {"name": "Shikoku Mura Paper Pavilion, Kagawa", "lat": 34.3381, "lon": 134.1015,
     "type": "Museum",
     "color": "#a855f7",
     "notes": "Open-air museum with traditional paper-making house; origami demonstrations"},
    {"name": "Itchiku Kubota Art Museum, Kawaguchiko", "lat": 35.5119, "lon": 138.7504,
     "type": "Art Museum",
     "color": "#ec4899",
     "notes": "Paper-inspired kimono art; tsujigahana dyeing meets origami pleating techniques"},
]

# =====================================================================
# 2. PAPER MAKING HISTORY (22 locations)
# =====================================================================
PAPER_MAKING_HISTORY = [
    {"name": "Cai Lun Birthplace, Leiyang, China", "lat": 26.4224, "lon": 112.8463,
     "era": "105 AD", "tradition": "Chinese invention",
     "color": "#ef4444",
     "notes": "Cai Lun credited with inventing modern paper from bark, hemp, rags, and fishnets"},
    {"name": "Dunhuang Paper Finds, China", "lat": 40.1420, "lon": 94.6620,
     "era": "200 BC", "tradition": "Earliest paper fragments",
     "color": "#ef4444",
     "notes": "Oldest paper samples found in Fangmatan tomb; predates Cai Lun by centuries"},
    {"name": "Xuan Paper Village, Jingxian, China", "lat": 30.6536, "lon": 118.4156,
     "era": "Tang Dynasty", "tradition": "Xuan paper",
     "color": "#f59e0b",
     "notes": "UNESCO heritage; finest calligraphy and origami paper; 1,000+ year craft"},
    {"name": "Samarkand Paper Mill, Uzbekistan", "lat": 39.6542, "lon": 66.9597,
     "era": "751 AD", "tradition": "Islamic paper",
     "color": "#8b5cf6",
     "notes": "Battle of Talas brought Chinese papermakers; first mill outside China"},
    {"name": "Baghdad House of Wisdom, Iraq", "lat": 33.3152, "lon": 44.3661,
     "era": "800 AD", "tradition": "Abbasid paper",
     "color": "#06b6d4",
     "notes": "Paper enabled golden age of Islamic scholarship; warraq paper merchants"},
    {"name": "Fez Paper Souk, Morocco", "lat": 34.0622, "lon": -4.9826,
     "era": "1100 AD", "tradition": "North African paper",
     "color": "#10b981",
     "notes": "Paper mills supplied Qarawiyyin university (oldest in world); leather-bound books"},
    {"name": "Xativa (Jativa), Spain", "lat": 38.9901, "lon": -0.5186,
     "era": "1056 AD", "tradition": "European paper origins",
     "color": "#3b82f6",
     "notes": "First paper mill in Europe; Moorish papermakers; supplied medieval manuscripts"},
    {"name": "Fabriano, Italy", "lat": 43.3396, "lon": 12.9056,
     "era": "1276 AD", "tradition": "Italian paper innovation",
     "color": "#a855f7",
     "notes": "Invented watermarks and gelatin sizing; Fabriano paper still world-renowned"},
    {"name": "Nuremberg Paper Mill, Germany", "lat": 49.4521, "lon": 11.0767,
     "era": "1390 AD", "tradition": "German paper milling",
     "color": "#14b8a6",
     "notes": "Ulman Stromer's mill; first in Germany; enabled Gutenberg's printing revolution"},
    {"name": "Basel Paper Mill Museum, Switzerland", "lat": 47.5545, "lon": 7.5942,
     "era": "1453 AD", "tradition": "Swiss paper heritage",
     "color": "#ec4899",
     "notes": "Working medieval paper mill museum; visitors make paper by hand; Gallician waterwheel"},
    {"name": "Dartford Paper Mill, England", "lat": 51.4467, "lon": 0.2148,
     "era": "1588 AD", "tradition": "English paper",
     "color": "#f97316",
     "notes": "John Spilman's mill; first successful English paper mill; supplied Tudor court"},
    {"name": "Rittenhouse Mill, Philadelphia, USA", "lat": 40.0534, "lon": -75.2096,
     "era": "1690 AD", "tradition": "American paper",
     "color": "#3b82f6",
     "notes": "First paper mill in British America; supplied Benjamin Franklin's printing press"},
    {"name": "Amalfi Paper Museum, Italy", "lat": 40.6340, "lon": 14.6027,
     "era": "1100 AD", "tradition": "Amalfi paper",
     "color": "#a855f7",
     "notes": "Museo della Carta; medieval water-powered paper mills; bambagina paper tradition"},
    {"name": "Tosashimizu, Kochi, Japan", "lat": 32.7808, "lon": 132.9561,
     "era": "700 AD", "tradition": "Japanese washi",
     "color": "#ef4444",
     "notes": "Among earliest Japanese paper sites; kozo mulberry fiber; court supply"},
    {"name": "Damascus Paper Market, Syria", "lat": 33.5131, "lon": 36.2919,
     "era": "900 AD", "tradition": "Syrian paper",
     "color": "#06b6d4",
     "notes": "Damascus paper (charta damascena) traded across Mediterranean; cotton-rag paper"},
    {"name": "Cairo Paper Workshops, Egypt", "lat": 30.0444, "lon": 31.2357,
     "era": "900 AD", "tradition": "Egyptian paper",
     "color": "#f59e0b",
     "notes": "Fatimid-era paper production; replaced papyrus; Al-Azhar library supply"},
    {"name": "Angouleme, France", "lat": 45.6500, "lon": 0.1590,
     "era": "1516 AD", "tradition": "French paper capital",
     "color": "#8b5cf6",
     "notes": "Capital of French paper industry; 70+ mills on Charente River; still active"},
    {"name": "Capellades Paper Museum, Spain", "lat": 41.5280, "lon": 1.6899,
     "era": "1700 AD", "tradition": "Catalan paper",
     "color": "#3b82f6",
     "notes": "Working paper museum; medieval-style vats; produced paper for Spanish colonies"},
    {"name": "Suzhou Paper Workshop, China", "lat": 31.2990, "lon": 120.5853,
     "era": "500 AD", "tradition": "Decorative paper",
     "color": "#ef4444",
     "notes": "Silk-infused paper; fan mounting paper; traditional Chinese painting sheets"},
    {"name": "Troyes Paper Mills, France", "lat": 48.2973, "lon": 4.0744,
     "era": "1340 AD", "tradition": "Champagne paper",
     "color": "#ec4899",
     "notes": "Supplied great medieval fairs; rag-based paper for Champagne trade documents"},
    {"name": "Tervuren Paper Museum, Belgium", "lat": 50.8272, "lon": 4.5133,
     "era": "1400 AD", "tradition": "Flemish paper",
     "color": "#14b8a6",
     "notes": "Royal Museum for Central Africa paper collection; colonial-era document papers"},
    {"name": "Mainz, Germany", "lat": 49.9929, "lon": 8.2473,
     "era": "1450 AD", "tradition": "Printing paper",
     "color": "#f97316",
     "notes": "Gutenberg's Bible printed here on locally-milled paper and vellum; printing revolution"},
]

# =====================================================================
# 3. WORLD ORIGAMI CONVENTIONS (20 locations)
# =====================================================================
WORLD_ORIGAMI_CONVENTIONS = [
    {"name": "OrigamiUSA Convention, New York", "lat": 40.7580, "lon": -73.9855,
     "frequency": "Annual (June)", "founded": "1980",
     "color": "#3b82f6",
     "notes": "Largest origami convention in Americas; 800+ attendees; master classes and exhibitions"},
    {"name": "British Origami Society, Birmingham", "lat": 52.4862, "lon": -1.8904,
     "frequency": "Biannual", "founded": "1967",
     "color": "#06b6d4",
     "notes": "One of oldest origami societies; biannual conventions; publishes quarterly magazine"},
    {"name": "Japan Origami Academic Society, Tokyo", "lat": 35.7100, "lon": 139.8107,
     "frequency": "Annual (Dec)", "founded": "1989",
     "color": "#ef4444",
     "notes": "Academic origami; mathematics of folding; computational origami presentations"},
    {"name": "Origami Deutschland, Hamburg", "lat": 53.5511, "lon": 9.9937,
     "frequency": "Annual", "founded": "1988",
     "color": "#f59e0b",
     "notes": "German national convention; paper-folding marathon; guest international masters"},
    {"name": "EMOZ - Origami Museum, Zaragoza, Spain", "lat": 41.6521, "lon": -0.8809,
     "frequency": "Permanent + Annual festival", "founded": "2013",
     "color": "#8b5cf6",
     "notes": "Europe's dedicated origami museum; annual Origami Festival; 3,000+ model collection"},
    {"name": "Centro Diffusione Origami, Italy", "lat": 44.4949, "lon": 11.3426,
     "frequency": "Annual (spring)", "founded": "1978",
     "color": "#a855f7",
     "notes": "Italian origami association convention; Mediterranean origami tradition"},
    {"name": "Origami Tanteidan Convention, Tokyo", "lat": 35.6585, "lon": 139.7454,
     "frequency": "Annual (Aug)", "founded": "1994",
     "color": "#ef4444",
     "notes": "Japan's premier complex origami convention; super-complex models; world's best folders"},
    {"name": "Pacific Coast Origami, San Francisco", "lat": 37.7749, "lon": -122.4194,
     "frequency": "Annual", "founded": "1996",
     "color": "#10b981",
     "notes": "West coast origami gathering; Silicon Valley tech-meets-paper innovation"},
    {"name": "Origami Australia Convention, Melbourne", "lat": -37.8136, "lon": 144.9631,
     "frequency": "Biennial", "founded": "1995",
     "color": "#f97316",
     "notes": "Southern hemisphere origami; unique native animal models; bushcraft paper folding"},
    {"name": "Korean Origami Association, Seoul", "lat": 37.5665, "lon": 126.9780,
     "frequency": "Annual", "founded": "1987",
     "color": "#ec4899",
     "notes": "Jong-ie Jupgi (Korean origami); hanji paper craft; traditional Korean paper folding"},
    {"name": "Israel Origami Center, Jerusalem", "lat": 31.7683, "lon": 35.2137,
     "frequency": "Annual", "founded": "2005",
     "color": "#14b8a6",
     "notes": "Middle East origami hub; interfaith paper folding workshops; peace crane projects"},
    {"name": "Mouvement Francais des Plieurs de Papier, Paris", "lat": 48.8566, "lon": 2.3522,
     "frequency": "Annual (Oct)", "founded": "1978",
     "color": "#8b5cf6",
     "notes": "French paper folders convention; elegant geometric designs; Parisian paper arts"},
    {"name": "Singapore Origami Club", "lat": 1.3521, "lon": 103.8198,
     "frequency": "Quarterly meets", "founded": "2004",
     "color": "#06b6d4",
     "notes": "Southeast Asian origami hub; tropical paper-folding; community workshops"},
    {"name": "Sociedad Espanola de Papiroflexia, Barcelona", "lat": 41.3851, "lon": 2.1734,
     "frequency": "Annual", "founded": "1972",
     "color": "#f59e0b",
     "notes": "Spanish paper folding society; annual conference; Miguel de Unamuno legacy"},
    {"name": "Hong Kong Origami Society", "lat": 22.3193, "lon": 114.1694,
     "frequency": "Monthly meets", "founded": "2001",
     "color": "#ef4444",
     "notes": "Cross-cultural East-West origami; Chinese paper folding roots; urban workshops"},
    {"name": "Origami Polska, Warsaw", "lat": 52.2297, "lon": 21.0122,
     "frequency": "Annual", "founded": "2005",
     "color": "#3b82f6",
     "notes": "Polish origami convention; modular origami specialty; Slavic paper traditions"},
    {"name": "Mexico Origami Convention, Mexico City", "lat": 19.4326, "lon": -99.1332,
     "frequency": "Annual (Nov)", "founded": "2003",
     "color": "#10b981",
     "notes": "Latin American origami hub; papel picado meets origami; Day of Dead paper art"},
    {"name": "Origami Society Netherlands, Amsterdam", "lat": 52.3676, "lon": 4.9041,
     "frequency": "Quarterly", "founded": "1982",
     "color": "#f97316",
     "notes": "Dutch origami tradition; tulip and windmill models; mathematical origami research"},
    {"name": "Russia Origami Society, Moscow", "lat": 55.7558, "lon": 37.6173,
     "frequency": "Annual", "founded": "1996",
     "color": "#a855f7",
     "notes": "Russian origami renaissance; Soviet-era educational folding; complex animal models"},
    {"name": "Origami South Africa, Johannesburg", "lat": -26.2041, "lon": 28.0473,
     "frequency": "Biannual", "founded": "2008",
     "color": "#ec4899",
     "notes": "African origami community; Big Five animal models; community outreach programs"},
]

# =====================================================================
# 4. PAPER ART MUSEUMS (20 locations)
# =====================================================================
PAPER_ART_MUSEUMS = [
    {"name": "EMOZ - Origami Museum, Zaragoza, Spain", "lat": 41.6521, "lon": -0.8809,
     "focus": "Origami", "collection": "3,000+ models",
     "color": "#8b5cf6",
     "notes": "World's only dedicated origami museum; permanent exhibition of masterworks"},
    {"name": "Paper Museum (Kami no Hakubutsukan), Tokyo", "lat": 35.7531, "lon": 139.7489,
     "focus": "Paper history", "collection": "40,000+ items",
     "color": "#ef4444",
     "notes": "Comprehensive paper history from ancient China to modern; washi demonstrations"},
    {"name": "Papiermuseum Basel, Switzerland", "lat": 47.5545, "lon": 7.5942,
     "focus": "Papermaking", "collection": "Working mill",
     "color": "#06b6d4",
     "notes": "Medieval paper mill; visitors make paper by hand; printing and bookbinding workshops"},
    {"name": "Robert C. Williams Museum of Papermaking, Atlanta", "lat": 33.7770, "lon": -84.3976,
     "focus": "Papermaking history", "collection": "10,000+ items",
     "color": "#3b82f6",
     "notes": "At Georgia Tech; oldest paper artifacts to modern; papyrus to digital paper"},
    {"name": "Museu Moli Paperer, Capellades, Spain", "lat": 41.5280, "lon": 1.6899,
     "focus": "Paper milling", "collection": "Working vats",
     "color": "#f59e0b",
     "notes": "15th-century mill; hands-on paper making; medieval techniques preserved"},
    {"name": "Deutsches Buch- und Schriftmuseum, Leipzig", "lat": 51.3233, "lon": 12.3961,
     "focus": "Books & paper", "collection": "500,000+ items",
     "color": "#14b8a6",
     "notes": "German Museum of Books and Writing; paper arts collection; printing heritage"},
    {"name": "Museo della Carta, Amalfi, Italy", "lat": 40.6340, "lon": 14.6027,
     "focus": "Paper heritage", "collection": "Medieval mills",
     "color": "#a855f7",
     "notes": "13th-century water-powered paper mills; bambagina paper; Amalfi Coast heritage"},
    {"name": "Moulin a Papier Vallis Clausa, Fontaine-de-Vaucluse, France",
     "lat": 43.9214, "lon": 5.1289,
     "focus": "Artisan paper", "collection": "Working mill",
     "color": "#ec4899",
     "notes": "Restored 15th-century mill by the source of Sorgue; handmade flower papers"},
    {"name": "Awagami Paper Museum, Tokushima, Japan", "lat": 34.0658, "lon": 134.5593,
     "focus": "Washi & origami", "collection": "Awa washi heritage",
     "color": "#ef4444",
     "notes": "Working washi factory; origami paper demonstrations; international artist residency"},
    {"name": "Paper Discovery Center, Appleton, USA", "lat": 44.2619, "lon": -88.4154,
     "focus": "Paper science", "collection": "Interactive exhibits",
     "color": "#10b981",
     "notes": "Fox River Valley paper heritage; interactive paper-making; children's origami"},
    {"name": "Musee du Papier, Angouleme, France", "lat": 45.6500, "lon": 0.1590,
     "focus": "French paper industry", "collection": "Industrial heritage",
     "color": "#f97316",
     "notes": "In former paper mill on Charente River; industrial paper history; comic book paper"},
    {"name": "Echizen Paper Museum, Fukui, Japan", "lat": 35.9073, "lon": 136.1668,
     "focus": "Traditional washi", "collection": "UNESCO heritage",
     "color": "#06b6d4",
     "notes": "1,500-year washi tradition; papermaking goddess shrine; hands-on workshops"},
    {"name": "Paper Museum of Mino, Gifu, Japan", "lat": 35.5446, "lon": 136.9075,
     "focus": "Mino washi", "collection": "UNESCO heritage",
     "color": "#3b82f6",
     "notes": "UNESCO Intangible Heritage; traditional screen-making; origami-grade paper creation"},
    {"name": "Rijksmuseum Paper Conservation, Amsterdam", "lat": 52.3600, "lon": 4.8852,
     "focus": "Paper art conservation", "collection": "1M+ prints/drawings",
     "color": "#8b5cf6",
     "notes": "World-class paper art collection; conservation lab; Rembrandt paper studies"},
    {"name": "National Paper Museum, Manchester, UK", "lat": 53.4808, "lon": -2.2426,
     "focus": "Industrial paper", "collection": "Mill heritage",
     "color": "#14b8a6",
     "notes": "Cotton-to-paper heritage; Industrial Revolution paper mills; archive collections"},
    {"name": "TWM Paper Art Space, Taipei", "lat": 25.0330, "lon": 121.5654,
     "focus": "Paper art", "collection": "Contemporary paper art",
     "color": "#f59e0b",
     "notes": "Contemporary paper arts; origami installations; Taiwanese paper craft traditions"},
    {"name": "Stickelberg Paper Mill, Duszniki-Zdroj, Poland", "lat": 50.3982, "lon": 16.3920,
     "focus": "Historic mill", "collection": "17th-century mill",
     "color": "#ec4899",
     "notes": "One of oldest working paper mills in Europe; 1605 founding; watermark collection"},
    {"name": "Xuan Paper Cultural Park, Jingxian, China", "lat": 30.6536, "lon": 118.4156,
     "focus": "Xuan paper", "collection": "UNESCO heritage",
     "color": "#ef4444",
     "notes": "UNESCO heritage site; xuan paper production for calligraphy and origami"},
    {"name": "Gangoji Temple Paper Museum, Nara, Japan", "lat": 34.6817, "lon": 135.8326,
     "focus": "Buddhist paper arts", "collection": "Temple heritage",
     "color": "#a855f7",
     "notes": "Ancient Buddhist paper traditions; sutra copying; ceremonial paper folding"},
    {"name": "Paper & Watermark Museum, Fabriano, Italy", "lat": 43.3396, "lon": 12.9056,
     "focus": "Watermarks & paper", "collection": "Medieval archives",
     "color": "#06b6d4",
     "notes": "Birthplace of watermarks (1282); Fabriano paper heritage; working demonstrations"},
]

# =====================================================================
# 5. KIRIGAMI & PAPER CUTTING (22 locations)
# =====================================================================
KIRIGAMI_PAPER_CUTTING = [
    {"name": "Yuxian Jianzhi Village, Hebei, China", "lat": 39.8400, "lon": 114.5700,
     "tradition": "Chinese jianzhi", "color": "#ef4444",
     "notes": "UNESCO masterpiece; 1,500-year window paper cutting; dyed paper knife-cut art"},
    {"name": "Foshan Paper Cutting, Guangdong, China", "lat": 23.0218, "lon": 113.1218,
     "tradition": "Cantonese jianzhi", "color": "#ef4444",
     "notes": "Gold-foil paper cutting; New Year decorations; dragon and phoenix motifs"},
    {"name": "Zhouzhuang Paper Cut Museum, China", "lat": 31.1144, "lon": 120.8467,
     "tradition": "Jiangnan paper cutting", "color": "#f59e0b",
     "notes": "Water town paper craft; delicate scenic jianzhi; silk-paper hybrid cuts"},
    {"name": "Shaanxi Paper Cutting, Xi'an, China", "lat": 34.2658, "lon": 108.9541,
     "tradition": "Northwestern jianzhi", "color": "#ef4444",
     "notes": "Bold red folk style; wedding double-happiness cuts; zodiac animal designs"},
    {"name": "San Salvador Huixcolotla, Puebla, Mexico", "lat": 18.9278, "lon": -97.7839,
     "tradition": "Papel picado", "color": "#10b981",
     "notes": "Capital of papel picado; tissue paper banners; Day of the Dead perforated art"},
    {"name": "Mexico City Papel Picado Market", "lat": 19.4284, "lon": -99.1276,
     "tradition": "Papel picado", "color": "#10b981",
     "notes": "Mercado de Sonora; elaborate tissue paper designs; festival decorations"},
    {"name": "Lowicz, Poland", "lat": 52.1090, "lon": 19.9430,
     "tradition": "Polish wycinanki", "color": "#8b5cf6",
     "notes": "Colorful layered paper cutting; rooster and flower motifs; Corpus Christi decorations"},
    {"name": "Kurpie Region, Poland", "lat": 53.3000, "lon": 21.3000,
     "tradition": "Kurpie wycinanki", "color": "#8b5cf6",
     "notes": "Single-color cut-outs; tree of life motif; spruce forest inspiration"},
    {"name": "Scherenschnitte Museum, Pays-d'Enhaut, Switzerland", "lat": 46.4754, "lon": 7.1229,
     "tradition": "Swiss scherenschnitte", "color": "#06b6d4",
     "notes": "Alpine paper silhouette cutting; pastoral scenes; Johann Jakob Hauswirth tradition"},
    {"name": "Andersen Museum Paper Cuts, Odense, Denmark", "lat": 55.3960, "lon": 10.3886,
     "tradition": "Danish paper cutting", "color": "#14b8a6",
     "notes": "Hans Christian Andersen's paper cuts; fairy tale silhouettes; literary paper art"},
    {"name": "Jewish Paper Cutting, Krakow, Poland", "lat": 50.0647, "lon": 19.9450,
     "tradition": "Mizrach & shiviti", "color": "#a855f7",
     "notes": "Ashkenazi paper cut art; synagogue decorations; intricate geometric paper lace"},
    {"name": "Otomi Paper Art, San Pablito, Mexico", "lat": 20.1200, "lon": -98.0200,
     "tradition": "Amate bark paper", "color": "#10b981",
     "notes": "Pre-Columbian bark paper (amate); spirit figures; ceremonial paper dolls"},
    {"name": "Turkish Paper Cutting (Katia), Istanbul", "lat": 41.0082, "lon": 28.9784,
     "tradition": "Ottoman katia", "color": "#f97316",
     "notes": "Ottoman paper cutting art; floral arabesques; calligraphic paper designs"},
    {"name": "Japanese Kirigami Center, Tokyo", "lat": 35.6762, "lon": 139.6503,
     "tradition": "Japanese kirigami", "color": "#ec4899",
     "notes": "Cut-and-fold paper art; architectural pop-ups; Masahiro Chatani kirigami school"},
    {"name": "Lithuanian Paper Cutting, Vilnius", "lat": 54.6872, "lon": 25.2797,
     "tradition": "Lithuanian karpiniai", "color": "#3b82f6",
     "notes": "Symmetrical folk paper cuts; Easter and Christmas decorations; snowflake designs"},
    {"name": "Chinese Shadow Puppet Paper, Tangshan", "lat": 39.6308, "lon": 118.1801,
     "tradition": "Pi ying (shadow puppets)", "color": "#f59e0b",
     "notes": "Translucent dyed leather/paper puppets; cut and articulated for shadow theater"},
    {"name": "German Scherenschnitte, Stuttgart", "lat": 48.7758, "lon": 9.1829,
     "tradition": "German silhouette cutting", "color": "#14b8a6",
     "notes": "18th-century silhouette portrait cutting; Goethe era; decorative folk art"},
    {"name": "Papel de Amate, Guerrero, Mexico", "lat": 17.5500, "lon": -99.5000,
     "tradition": "Nahua bark painting", "color": "#10b981",
     "notes": "Painted amate bark paper; vibrant floral and animal scenes; tourist art tradition"},
    {"name": "Monkiri Paper Crest Cutting, Kyoto, Japan", "lat": 35.0116, "lon": 135.7681,
     "tradition": "Mon-kiri", "color": "#ec4899",
     "notes": "Family crest paper cutting; Edo-period design book; symmetrical folded cuts"},
    {"name": "Indian Sanjhi Paper Cutting, Mathura", "lat": 27.4924, "lon": 77.6737,
     "tradition": "Sanjhi art", "color": "#f59e0b",
     "notes": "Hindu temple paper stencils; Krishna stories; cut paper rangoli patterns"},
    {"name": "Ethiopian Paper Icon Art, Lalibela", "lat": 12.0319, "lon": 39.0475,
     "tradition": "Parchment art", "color": "#3b82f6",
     "notes": "Ge'ez manuscript tradition; religious paper/parchment art; rock-hewn church scrolls"},
    {"name": "Lei Cheng Uk Paper Offerings, Hong Kong", "lat": 22.3375, "lon": 114.1597,
     "tradition": "Joss paper art", "color": "#f97316",
     "notes": "Elaborate joss paper sculptures; ancestral offerings; paper houses and goods"},
]

# =====================================================================
# 6. BOOK BINDING HERITAGE (20 locations)
# =====================================================================
BOOK_BINDING_HERITAGE = [
    {"name": "Bodleian Library Bindery, Oxford, UK", "lat": 51.7548, "lon": -1.2544,
     "tradition": "English binding", "era": "1602",
     "color": "#8b5cf6",
     "notes": "One of Europe's oldest libraries; preservation bindery; Romanesque to modern"},
    {"name": "Bibliotheque nationale de France, Paris", "lat": 48.8336, "lon": 2.3755,
     "tradition": "French binding", "era": "1461",
     "color": "#06b6d4",
     "notes": "Royal bindings; maroquin leather; dorure a la fanfare; art deco bindings"},
    {"name": "Vatican Apostolic Library, Rome", "lat": 41.9049, "lon": 12.4534,
     "tradition": "Papal binding", "era": "1451",
     "color": "#ef4444",
     "notes": "Papal manuscript bindings; gold-tooled leather; oldest Western book binding examples"},
    {"name": "Trinity College Library, Dublin", "lat": 53.3438, "lon": -6.2546,
     "tradition": "Irish binding", "era": "800 AD",
     "color": "#10b981",
     "notes": "Book of Kells; cumdach shrine bindings; Celtic knotwork covers"},
    {"name": "Topkapi Palace Library, Istanbul", "lat": 41.0115, "lon": 28.9833,
     "tradition": "Ottoman binding", "era": "1459",
     "color": "#f59e0b",
     "notes": "Ottoman filigree bindings; marbled paper endsheets (ebru); Islamic geometric patterns"},
    {"name": "Marrakech Medina Bookbinders, Morocco", "lat": 31.6295, "lon": -7.9811,
     "tradition": "Moroccan leather binding", "era": "1200",
     "color": "#ec4899",
     "notes": "Morocco leather originates here; goatskin tanning; blind-tooled Islamic bindings"},
    {"name": "Wittenberg Luther Bible Bindery, Germany", "lat": 51.8661, "lon": 12.6432,
     "tradition": "German Reformation binding", "era": "1534",
     "color": "#14b8a6",
     "notes": "Luther Bible bindings; pigskin over wooden boards; blind-stamped Protestant books"},
    {"name": "Florence Leather School (Santa Croce)", "lat": 43.7687, "lon": 11.2625,
     "tradition": "Florentine binding", "era": "1950",
     "color": "#a855f7",
     "notes": "In Santa Croce basilica; marbled paper endpapers; Florentine gold tooling"},
    {"name": "Sangorski & Sutcliffe, London", "lat": 51.5072, "lon": -0.1276,
     "tradition": "Jeweled binding", "era": "1901",
     "color": "#f97316",
     "notes": "Great Omar jeweled binding (lost on Titanic); recreated; luxury binding masters"},
    {"name": "Chester Beatty Library, Dublin", "lat": 53.3428, "lon": -6.2674,
     "tradition": "Islamic & Asian binding", "era": "1950",
     "color": "#3b82f6",
     "notes": "Finest collection of Islamic, Chinese, and Japanese bindings outside Asia"},
    {"name": "Ethiopian Binding, Addis Ababa", "lat": 9.0054, "lon": 38.7636,
     "tradition": "Coptic binding", "era": "400 AD",
     "color": "#ef4444",
     "notes": "Coptic stitch binding origin; wooden boards with leather; chain stitch sewing"},
    {"name": "Leiden University Library, Netherlands", "lat": 52.1570, "lon": 4.4850,
     "tradition": "Dutch binding", "era": "1575",
     "color": "#06b6d4",
     "notes": "Vellum binding tradition; Elzevir press bindings; gilt-tooled calf leather"},
    {"name": "Suzhou Xylographic Bindery, China", "lat": 31.2990, "lon": 120.5853,
     "tradition": "Chinese stab binding", "era": "200 AD",
     "color": "#f59e0b",
     "notes": "Thread-bound book tradition (xian zhuang); butterfly binding; accordion books"},
    {"name": "Nara Sutra Bindery, Japan", "lat": 34.6851, "lon": 135.8048,
     "tradition": "Japanese stab binding", "era": "700 AD",
     "color": "#ec4899",
     "notes": "Buddhist sutra binding; orihon (accordion) style; tetsuyoso (pouch) binding"},
    {"name": "Salamanca University Library, Spain", "lat": 40.9629, "lon": -5.6672,
     "tradition": "Spanish binding", "era": "1218",
     "color": "#8b5cf6",
     "notes": "Mudejar-style bindings; interlaced leather tooling; Moorish-Christian hybrid art"},
    {"name": "St. Catherine's Monastery, Sinai, Egypt", "lat": 28.5560, "lon": 33.9758,
     "tradition": "Early Christian binding", "era": "565 AD",
     "color": "#10b981",
     "notes": "Codex Sinaiticus origin; earliest complete Bible bindings; desert preservation"},
    {"name": "National Diet Library, Tokyo", "lat": 35.6769, "lon": 139.7448,
     "tradition": "Japanese modern binding", "era": "1948",
     "color": "#3b82f6",
     "notes": "Western and Japanese binding fusion; yotsume-toji to modern; conservation lab"},
    {"name": "Isfahan Bazaar Bookbinders, Iran", "lat": 32.6546, "lon": 51.6680,
     "tradition": "Persian lacquer binding", "era": "1500",
     "color": "#f97316",
     "notes": "Papier-mache lacquer covers; miniature paintings on bindings; Safavid masterworks"},
    {"name": "Morgan Library & Museum, New York", "lat": 40.7491, "lon": -73.9812,
     "tradition": "Rare book conservation", "era": "1906",
     "color": "#a855f7",
     "notes": "J.P. Morgan collection; medieval to Renaissance bindings; jeweled Gospel covers"},
    {"name": "Timbuktu Manuscript Libraries, Mali", "lat": 16.7735, "lon": -3.0074,
     "tradition": "West African binding", "era": "1300",
     "color": "#14b8a6",
     "notes": "300,000+ manuscripts; goatskin leather bindings; Saharan trade route scholarship"},
]

# =====================================================================
# 7. PAPYRUS ORIGINS (18 locations)
# =====================================================================
PAPYRUS_ORIGINS = [
    {"name": "Pharaonic Village Papyrus Workshop, Cairo", "lat": 30.0131, "lon": 31.2089,
     "era": "3000 BC tradition", "material": "Papyrus",
     "color": "#f59e0b",
     "notes": "Living museum; papyrus reed harvesting and sheet-making; ancient techniques revived"},
    {"name": "Alexandria Library (Bibliotheca), Egypt", "lat": 31.2089, "lon": 29.9093,
     "era": "300 BC", "material": "Papyrus scrolls",
     "color": "#06b6d4",
     "notes": "Greatest ancient library; 400,000+ papyrus scrolls; Ptolemaic scholarship center"},
    {"name": "Luxor Papyrus Institute, Egypt", "lat": 25.6872, "lon": 32.6396,
     "era": "3000 BC tradition", "material": "Papyrus",
     "color": "#f59e0b",
     "notes": "Near Valley of Kings; demonstrates pharaonic papermaking; Theban scroll tradition"},
    {"name": "Herculaneum Papyrus Villa, Italy", "lat": 40.8059, "lon": 14.3480,
     "era": "79 AD preserved", "material": "Carbonized papyrus",
     "color": "#ef4444",
     "notes": "Villa of the Papyri; 1,800 carbonized scrolls; Epicurean philosophy library"},
    {"name": "Oxyrhynchus, Egypt", "lat": 28.5344, "lon": 30.6594,
     "era": "300 BC-700 AD", "material": "Papyrus dump",
     "color": "#10b981",
     "notes": "Greatest papyrus archaeological find; 500,000+ fragments; lost literary works"},
    {"name": "Elephantine Island, Aswan, Egypt", "lat": 24.0850, "lon": 32.8872,
     "era": "500 BC", "material": "Aramaic papyri",
     "color": "#8b5cf6",
     "notes": "Jewish colony papyri; Aramaic legal documents; Persian-era diplomatic letters"},
    {"name": "Fayum Region, Egypt", "lat": 29.3084, "lon": 30.8428,
     "era": "200 BC", "material": "Fayum papyri & portraits",
     "color": "#ec4899",
     "notes": "Fayum mummy portraits on wood; papyrus administrative records; Ptolemaic archives"},
    {"name": "Pergamon (Bergama), Turkey", "lat": 39.1217, "lon": 27.1833,
     "era": "200 BC", "material": "Parchment (pergamena)",
     "color": "#a855f7",
     "notes": "Invented parchment when Egypt banned papyrus exports; 200,000-scroll library"},
    {"name": "Dead Sea Scrolls, Qumran, Israel", "lat": 31.7414, "lon": 35.4589,
     "era": "200 BC-70 AD", "material": "Parchment & papyrus",
     "color": "#3b82f6",
     "notes": "Oldest Hebrew Bible manuscripts; parchment and papyrus scrolls in clay jars"},
    {"name": "Nag Hammadi, Egypt", "lat": 26.0504, "lon": 32.2830,
     "era": "350 AD", "material": "Papyrus codices",
     "color": "#14b8a6",
     "notes": "Gnostic Gospels discovery; 13 leather-bound papyrus codices; early book format"},
    {"name": "Syracuse Papyrus Museum, Sicily", "lat": 37.0755, "lon": 15.2866,
     "era": "Greek era", "material": "Papyrus",
     "color": "#f97316",
     "notes": "Only European site where papyrus grows wild; Ciane River papyrus beds; museum"},
    {"name": "Abu Sir, Egypt", "lat": 29.8939, "lon": 31.2053,
     "era": "2400 BC", "material": "Oldest papyrus archive",
     "color": "#f59e0b",
     "notes": "Abusir Papyri; oldest surviving papyrus collection; 5th Dynasty temple records"},
    {"name": "Vindolanda Roman Fort, UK", "lat": 55.0092, "lon": -2.3608,
     "era": "100 AD", "material": "Wooden tablets",
     "color": "#06b6d4",
     "notes": "Thin wooden writing tablets (not papyrus); Roman frontier letters; unique survival"},
    {"name": "Bodmer Library, Geneva, Switzerland", "lat": 46.2832, "lon": 6.1740,
     "era": "200 AD collection", "material": "Papyrus collection",
     "color": "#10b981",
     "notes": "Bodmer Papyri; oldest New Testament manuscripts; Egyptian literary papyri"},
    {"name": "Austrian National Library Papyrus, Vienna", "lat": 48.2060, "lon": 16.3660,
     "era": "Collection", "material": "180,000 papyri",
     "color": "#8b5cf6",
     "notes": "Largest papyrus collection in world; Rainer Collection; multilingual ancient texts"},
    {"name": "Chester Beatty Papyri, Dublin", "lat": 53.3428, "lon": -6.2674,
     "era": "150 AD", "material": "Biblical papyri",
     "color": "#ec4899",
     "notes": "Earliest near-complete biblical papyrus books; Egyptian provenance; 2nd-3rd century"},
    {"name": "British Library Papyrus Collection, London", "lat": 51.5299, "lon": -0.1272,
     "era": "2000 BC-700 AD", "material": "Major collection",
     "color": "#a855f7",
     "notes": "Including the Greenfield Papyrus (Book of the Dead); Aristotle papyrus; Egyptian texts"},
    {"name": "Wadi Daliyeh Cave, Palestine", "lat": 32.0167, "lon": 35.3500,
     "era": "375 BC", "material": "Samaria Papyri",
     "color": "#14b8a6",
     "notes": "4th-century BC legal papyri; Samaritan refugees; Persian-period administrative docs"},
]

# =====================================================================
# 8. KITE MAKING TRADITIONS (22 locations)
# =====================================================================
KITE_MAKING_TRADITIONS = [
    {"name": "Weifang, Shandong, China", "lat": 36.7068, "lon": 119.1617,
     "tradition": "Chinese dragon kites", "color": "#ef4444",
     "notes": "World Kite Capital; annual International Kite Festival; 2,000-year kite heritage"},
    {"name": "Nantong Kite Museum, China", "lat": 32.0584, "lon": 120.8735,
     "tradition": "Nantong whistling kites", "color": "#f59e0b",
     "notes": "Distinctive hexagonal kites with bamboo whistles; musical kites; Jiangsu tradition"},
    {"name": "Beijing Kite Workshop, China", "lat": 39.9042, "lon": 116.4074,
     "tradition": "Beijing swallow kites", "color": "#ef4444",
     "notes": "Sha Yan (fat swallow) kite; imperial court tradition; painted silk kites"},
    {"name": "Ahmedabad Makar Sankranti, India", "lat": 23.0225, "lon": 72.5714,
     "tradition": "Indian fighter kites", "color": "#10b981",
     "notes": "Uttarayan kite festival; glass-coated string (manjha); millions fly kites simultaneously"},
    {"name": "Jaipur Kite Festival, India", "lat": 26.9124, "lon": 75.7873,
     "tradition": "Rajasthani kites (patang)", "color": "#10b981",
     "notes": "Patang fighter kites; rooftop battles; Makar Sankranti celebrations"},
    {"name": "Lucknow Kite Market, India", "lat": 26.8467, "lon": 80.9462,
     "tradition": "Lucknowi guddi kites", "color": "#8b5cf6",
     "notes": "Nawabi kite tradition; elaborate painted kites; Basant Panchami festival"},
    {"name": "Hamamatsu, Japan", "lat": 34.7107, "lon": 137.7262,
     "tradition": "Japanese kite festival", "color": "#ec4899",
     "notes": "Annual Hamamatsu Kite Festival; 174 neighborhood kites; celebration of firstborn sons"},
    {"name": "Sagami Giant Kite, Kanagawa, Japan", "lat": 35.3938, "lon": 139.3456,
     "tradition": "Odako giant kites", "color": "#ec4899",
     "notes": "9m x 9m giant kite tradition; 100+ people to launch; Children's Day celebration"},
    {"name": "Nagasaki Hata Kite, Japan", "lat": 32.7503, "lon": 129.8777,
     "tradition": "Hata fighter kites", "color": "#f97316",
     "notes": "Dutch-influenced diamond kites; sharp-line fighting; 400-year Nagasaki tradition"},
    {"name": "Kabul Kite Flying, Afghanistan", "lat": 34.5553, "lon": 69.2075,
     "tradition": "Afghan fighter kites (gudiparan)", "color": "#3b82f6",
     "notes": "The Kite Runner tradition; glass-string battles; cultural heritage of competition"},
    {"name": "Bali Kite Festival, Indonesia", "lat": -8.6500, "lon": 115.2167,
     "tradition": "Balinese ceremonial kites", "color": "#14b8a6",
     "notes": "Annual July festival; bebean (fish), janggan (bird), pecukan (leaf) traditional forms"},
    {"name": "Pasir Gudang Kite Festival, Malaysia", "lat": 1.4725, "lon": 103.8860,
     "tradition": "Wau bulan (moon kite)", "color": "#a855f7",
     "notes": "Malaysia's iconic crescent-moon kite; featured on banknotes; annual festival"},
    {"name": "Guatemala Giant Kites, Sumpango", "lat": 14.6458, "lon": -90.7283,
     "tradition": "Barriletes gigantes", "color": "#10b981",
     "notes": "Day of the Dead giant kites; 12m+ diameter; messages to deceased; UNESCO nominated"},
    {"name": "Dieppe International Kite Festival, France", "lat": 49.9253, "lon": 1.0800,
     "tradition": "European kite festival", "color": "#06b6d4",
     "notes": "Largest kite festival in Europe; biennial; artistic and sport kites worldwide"},
    {"name": "Scheveningen Kite Festival, Netherlands", "lat": 52.1081, "lon": 4.2728,
     "tradition": "Dutch kite festival", "color": "#f59e0b",
     "notes": "International Kite Festival on North Sea beach; sport and art kites"},
    {"name": "Bristol International Kite Festival, UK", "lat": 51.4545, "lon": -2.5879,
     "tradition": "British kite festival", "color": "#3b82f6",
     "notes": "Annual festival on Durdham Downs; kite-making workshops; team sport kites"},
    {"name": "Busan Kite Festival, South Korea", "lat": 35.1796, "lon": 129.0756,
     "tradition": "Yeon (Korean kite)", "color": "#ec4899",
     "notes": "Rectangular fighting kites; Lunar New Year tradition; Haeundae Beach festival"},
    {"name": "Lahore Basant Festival, Pakistan", "lat": 31.5204, "lon": 74.3587,
     "tradition": "Basant patang", "color": "#8b5cf6",
     "notes": "Spring kite festival; glass-coated string battles; Mughal-era tradition"},
    {"name": "Thai Kite Museum, Bangkok", "lat": 13.7563, "lon": 100.5018,
     "tradition": "Thai chula & pakpao kites", "color": "#14b8a6",
     "notes": "Star-shaped chula (male) vs diamond pakpao (female) kite battles; royal sport"},
    {"name": "Long Beach Kite Festival, Washington, USA", "lat": 46.3523, "lon": -124.0543,
     "tradition": "American sport kites", "color": "#f97316",
     "notes": "Washington State International Kite Festival; world record attempts; kite museum"},
    {"name": "Cervia International Kite Festival, Italy", "lat": 44.2612, "lon": 12.3525,
     "tradition": "Italian kite festival", "color": "#a855f7",
     "notes": "Adriatic coast kite festival; artistic kites; Italian kite-making master workshops"},
    {"name": "Berck-sur-Mer Kite Festival, France", "lat": 50.4068, "lon": 1.5650,
     "tradition": "French kite rencontres", "color": "#06b6d4",
     "notes": "Rencontres Internationales de Cerfs-Volants; world's top kite artists gather annually"},
]

# =====================================================================
# 9. PAPER CRANE MEMORIALS (18 locations)
# =====================================================================
PAPER_CRANE_MEMORIALS = [
    {"name": "Hiroshima Peace Memorial (A-Bomb Dome)", "lat": 34.3955, "lon": 132.4536,
     "type": "Peace memorial", "color": "#ef4444",
     "notes": "Sadako Sasaki's 1,000 cranes legacy; Children's Peace Monument; millions of cranes received annually"},
    {"name": "Sadako Sasaki Statue, Hiroshima", "lat": 34.3925, "lon": 132.4527,
     "type": "Children's monument", "color": "#ef4444",
     "notes": "Girl with the Golden Crane statue; senbazuru (1,000 cranes) tradition origin; peace symbol"},
    {"name": "Nagasaki Peace Park", "lat": 32.7741, "lon": 129.8636,
     "type": "Peace memorial", "color": "#3b82f6",
     "notes": "Paper crane offerings at Peace Statue; complementary to Hiroshima memorial"},
    {"name": "Sadako Statue, Seattle, USA", "lat": 47.6218, "lon": -122.3198,
     "type": "Peace park statue", "color": "#06b6d4",
     "notes": "Seattle Peace Park; life-size Sadako statue; sister city to Kobe; crane displays"},
    {"name": "Sadako Peace Garden, Santa Barbara, USA", "lat": 34.4208, "lon": -119.6982,
     "type": "Peace garden", "color": "#10b981",
     "notes": "Peace garden with origami crane installations; thousand crane projects"},
    {"name": "9/11 Memorial Cranes, New York, USA", "lat": 40.7115, "lon": -74.0134,
     "type": "Tribute memorial", "color": "#8b5cf6",
     "notes": "Paper cranes sent from Japan after 9/11; symbol of healing and solidarity"},
    {"name": "Pearl Harbor Paper Cranes, Hawaii, USA", "lat": 21.3648, "lon": -157.9387,
     "type": "Reconciliation memorial", "color": "#f59e0b",
     "notes": "Japanese students send cranes for reconciliation; displayed at USS Arizona Memorial"},
    {"name": "United Nations HQ Crane Displays, New York", "lat": 40.7489, "lon": -73.9680,
     "type": "International peace", "color": "#a855f7",
     "notes": "Senbazuru donated by world peace organizations; displayed during peace assemblies"},
    {"name": "Auschwitz Paper Crane Offerings, Poland", "lat": 50.0343, "lon": 19.1784,
     "type": "Holocaust memorial", "color": "#ec4899",
     "notes": "Paper cranes left by Japanese visitors; universal peace and remembrance symbol"},
    {"name": "Senbazuru at Meiji Shrine, Tokyo", "lat": 35.6764, "lon": 139.6993,
     "type": "Shrine tradition", "color": "#f97316",
     "notes": "Traditional senbazuru (1,000 crane) offerings for health and good fortune"},
    {"name": "Fushimi Inari Paper Cranes, Kyoto", "lat": 34.9671, "lon": 135.7727,
     "type": "Shrine offering", "color": "#14b8a6",
     "notes": "Origami crane ema (prayer boards); paper offerings alongside torii gates"},
    {"name": "Children's Peace Library, Hiroshima", "lat": 34.3941, "lon": 132.4528,
     "type": "Library", "color": "#3b82f6",
     "notes": "Books from around world with paper crane bookmarks; Sadako story translations"},
    {"name": "Crane Memorial, Trieste, Italy", "lat": 45.6495, "lon": 13.7768,
     "type": "Peace installation", "color": "#8b5cf6",
     "notes": "Paper crane peace installation at Risiera di San Sabba memorial; cross-cultural peace"},
    {"name": "Robben Island Crane Project, South Africa", "lat": -33.8066, "lon": 18.3716,
     "type": "Reconciliation project", "color": "#10b981",
     "notes": "Paper cranes for peace and reconciliation; connecting Mandela's legacy with Japanese peace"},
    {"name": "Paper Crane Project, Chernobyl Museum, Kyiv", "lat": 50.4548, "lon": 30.5274,
     "type": "Memorial project", "color": "#f59e0b",
     "notes": "Paper cranes honoring nuclear disaster victims; parallel with Hiroshima peace movement"},
    {"name": "Westminster Abbey Crane Installation, London", "lat": 51.4993, "lon": -0.1273,
     "type": "Temporary installation", "color": "#06b6d4",
     "notes": "Peace crane installations for Remembrance; connecting WWI/WWII and nuclear peace"},
    {"name": "Crane Shrine at Itsukushima, Miyajima, Japan", "lat": 34.2959, "lon": 132.3197,
     "type": "Shrine tradition", "color": "#ec4899",
     "notes": "Floating torii gate shrine; paper crane and paper deer offerings; UNESCO site"},
    {"name": "Atomic Bomb Museum, Nagasaki", "lat": 32.7730, "lon": 129.8640,
     "type": "Museum", "color": "#a855f7",
     "notes": "Permanent senbazuru displays; paper crane folding station for visitors; peace education"},
]

# =====================================================================
# 10. MODERN PAPER ARCHITECTURE (20 locations)
# =====================================================================
MODERN_PAPER_ARCHITECTURE = [
    {"name": "Shigeru Ban Paper Tube Shelter, Kobe, Japan", "lat": 34.6901, "lon": 135.1956,
     "type": "Emergency shelter", "architect": "Shigeru Ban",
     "color": "#ef4444",
     "notes": "1995 earthquake; recycled paper tube shelters; beer-crate foundations; humanitarian design"},
    {"name": "Paper Church, Kobe, Japan", "lat": 34.6937, "lon": 135.1970,
     "type": "Paper tube church", "architect": "Shigeru Ban",
     "color": "#ef4444",
     "notes": "Rebuilt church from paper tubes after 1995 earthquake; later relocated to Taiwan"},
    {"name": "Cardboard Cathedral, Christchurch, NZ", "lat": -43.5347, "lon": 172.6451,
     "type": "Cathedral", "architect": "Shigeru Ban",
     "color": "#06b6d4",
     "notes": "Post-2011 earthquake; 98 cardboard tubes; A-frame design; seats 700; permanent structure"},
    {"name": "Paper Log House, Turkey (Duzce)", "lat": 40.8438, "lon": 31.1565,
     "type": "Earthquake housing", "architect": "Shigeru Ban",
     "color": "#f59e0b",
     "notes": "1999 earthquake relief; paper tube walls on beer-crate foundations; roof membrane"},
    {"name": "Paper Pavilion, Metz, France", "lat": 49.1089, "lon": 6.1785,
     "type": "Exhibition pavilion", "architect": "Shigeru Ban",
     "color": "#8b5cf6",
     "notes": "Centre Pompidou-Metz; paper tube exhibition; hexagonal woven timber and paper"},
    {"name": "Paper Bridge, Pont du Gard, France", "lat": 43.9470, "lon": 4.5353,
     "type": "Temporary bridge", "architect": "Shigeru Ban",
     "color": "#8b5cf6",
     "notes": "Paper tube bridge next to Roman aqueduct; proved structural viability of cardboard"},
    {"name": "Westborough Primary School, Essex, UK", "lat": 51.5399, "lon": 0.7049,
     "type": "School building", "architect": "Cottrell & Vermeulen",
     "color": "#10b981",
     "notes": "UK's first cardboard school building; recyclable paper panels; educational showcase"},
    {"name": "Paper Tea House, Tokyo, Japan", "lat": 35.6762, "lon": 139.6503,
     "type": "Tea house", "architect": "Shigeru Ban",
     "color": "#ec4899",
     "notes": "Temporary paper tube tea house installations; traditional ceremony meets innovation"},
    {"name": "Wikkelhouse, Amsterdam, Netherlands", "lat": 52.3676, "lon": 4.9041,
     "type": "Cardboard house", "architect": "Fiction Factory",
     "color": "#3b82f6",
     "notes": "Modular cardboard houses; 24 layers of recycled cardboard; 100-year lifespan claim"},
    {"name": "Paper Concert Hall, L'Aquila, Italy", "lat": 42.3498, "lon": 13.3995,
     "type": "Concert hall", "architect": "Shigeru Ban",
     "color": "#a855f7",
     "notes": "2009 earthquake relief; paper tube concert hall; acoustic engineering in cardboard"},
    {"name": "Nomadic Museum, NYC, USA", "lat": 40.7468, "lon": -74.0079,
     "type": "Exhibition space", "architect": "Shigeru Ban",
     "color": "#f97316",
     "notes": "Paper tube columns; shipping containers; Gregory Colbert photography exhibition"},
    {"name": "Hualien Emergency Shelter, Taiwan", "lat": 23.9910, "lon": 121.6011,
     "type": "Emergency shelter", "architect": "Shigeru Ban",
     "color": "#14b8a6",
     "notes": "2018 earthquake; relocated Kobe paper church; paper tube shelters; humanitarian"},
    {"name": "Paper Partition System, Fukushima, Japan", "lat": 37.7500, "lon": 140.4678,
     "type": "Refugee partitions", "architect": "Shigeru Ban",
     "color": "#ef4444",
     "notes": "2011 tsunami; paper tube privacy partitions for evacuation centers; dignified shelter"},
    {"name": "Paper Studio, Paris, France", "lat": 48.8566, "lon": 2.3522,
     "type": "Design studio", "architect": "Shigeru Ban",
     "color": "#06b6d4",
     "notes": "Shigeru Ban Architects European HQ; paper tube interior; rooftop studio"},
    {"name": "Cardboard Castle, Melbourne, Australia", "lat": -37.8136, "lon": 144.9631,
     "type": "Art installation", "architect": "Various",
     "color": "#f59e0b",
     "notes": "Federation Square cardboard architecture installations; children's design workshops"},
    {"name": "Paper Nursery, Rwanda", "lat": -1.9403, "lon": 29.8739,
     "type": "Humanitarian shelter", "architect": "Shigeru Ban",
     "color": "#10b981",
     "notes": "Rwandan refugee shelters; paper tubes with pressed earth; humanitarian architecture"},
    {"name": "Camper Paper Pavilion, Alicante, Spain", "lat": 38.3452, "lon": -0.4810,
     "type": "Commercial pavilion", "architect": "Shigeru Ban",
     "color": "#ec4899",
     "notes": "Paper tube shoe pavilion for Camper brand; commercial cardboard architecture"},
    {"name": "Paper Dome, Puli, Taiwan", "lat": 23.9660, "lon": 120.9690,
     "type": "Community center", "architect": "Shigeru Ban",
     "color": "#3b82f6",
     "notes": "Relocated from Kobe; paper tube dome; community gathering space; earthquake heritage"},
    {"name": "Container x Cardboard Art Space, Seoul", "lat": 37.5665, "lon": 126.9780,
     "type": "Art gallery", "architect": "Various",
     "color": "#8b5cf6",
     "notes": "Temporary cardboard exhibition spaces; Korean paper architecture experiments"},
    {"name": "Paper Tiger Community Center, Haiti", "lat": 18.5944, "lon": -72.3074,
     "type": "Community center", "architect": "Shigeru Ban",
     "color": "#a855f7",
     "notes": "2010 earthquake relief; paper tube community structures; paper as humanitarian tool"},
]


# =====================================================================
# MAP MODES, COLORS, DESCRIPTIONS
# =====================================================================
MAP_MODES = [
    "Japanese Origami Heritage",
    "Paper Making History",
    "World Origami Conventions",
    "Paper Art Museums",
    "Kirigami & Paper Cutting",
    "Book Binding Heritage",
    "Papyrus Origins",
    "Kite Making Traditions",
    "Paper Crane Memorials",
    "Modern Paper Architecture",
]

MODE_DATA = {
    "Japanese Origami Heritage": JAPANESE_ORIGAMI_HERITAGE,
    "Paper Making History": PAPER_MAKING_HISTORY,
    "World Origami Conventions": WORLD_ORIGAMI_CONVENTIONS,
    "Paper Art Museums": PAPER_ART_MUSEUMS,
    "Kirigami & Paper Cutting": KIRIGAMI_PAPER_CUTTING,
    "Book Binding Heritage": BOOK_BINDING_HERITAGE,
    "Papyrus Origins": PAPYRUS_ORIGINS,
    "Kite Making Traditions": KITE_MAKING_TRADITIONS,
    "Paper Crane Memorials": PAPER_CRANE_MEMORIALS,
    "Modern Paper Architecture": MODERN_PAPER_ARCHITECTURE,
}

MODE_COLORS = {
    "Japanese Origami Heritage": "#ef4444",
    "Paper Making History": "#f59e0b",
    "World Origami Conventions": "#8b5cf6",
    "Paper Art Museums": "#06b6d4",
    "Kirigami & Paper Cutting": "#10b981",
    "Book Binding Heritage": "#a855f7",
    "Papyrus Origins": "#ec4899",
    "Kite Making Traditions": "#3b82f6",
    "Paper Crane Memorials": "#ef4444",
    "Modern Paper Architecture": "#f97316",
}

MODE_DESCRIPTIONS = {
    "Japanese Origami Heritage": "Origami museums, washi paper studios, master folders, and sacred paper folding traditions across Japan.",
    "Paper Making History": "From Cai Lun's 105 AD invention in China through Islamic paper mills to European Renaissance paper centers.",
    "World Origami Conventions": "Annual origami conventions, societies, and gatherings bringing paper folders together worldwide.",
    "Paper Art Museums": "Museums and cultural centers dedicated to paper arts, papermaking heritage, and origami collections.",
    "Kirigami & Paper Cutting": "Chinese jianzhi, Mexican papel picado, Polish wycinanki, Japanese kirigami, and paper cutting traditions worldwide.",
    "Book Binding Heritage": "Historic book binding centers from Coptic stitching to Florentine gold tooling, vellum, and calfskin traditions.",
    "Papyrus Origins": "Egyptian papyrus workshops, ancient scroll libraries, parchment invention, and the earliest writing surfaces.",
    "Kite Making Traditions": "Chinese dragon kites, Indian fighter kites, Japanese festival kites, and Afghan gudiparan traditions worldwide.",
    "Paper Crane Memorials": "Sadako Sasaki's legacy, Hiroshima peace cranes, senbazuru (1,000 cranes) traditions, and peace memorials.",
    "Modern Paper Architecture": "Shigeru Ban's paper tube buildings, cardboard cathedrals, and humanitarian paper architecture worldwide.",
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
def _render_japanese_origami():
    """Render Japanese Origami Heritage mode."""
    data = JAPANESE_ORIGAMI_HERITAGE
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Japanese Origami Heritage'])}</p>",
        unsafe_allow_html=True,
    )
    types = list({d["type"] for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Site Types", len(types)),
        ("Country", "Japan"),
        ("Tradition Span", "800+ years"),
    ])
    m = _build_map(
        data, [36.5, 137.0], 6,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Type": d["type"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['type']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Type": d["type"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "japanese_origami_heritage.csv", "dl_jp_origami")


def _render_paper_making():
    """Render Paper Making History mode."""
    data = PAPER_MAKING_HISTORY
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Paper Making History'])}</p>",
        unsafe_allow_html=True,
    )
    countries = len({d["name"].split(",")[-1].strip() for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Countries", countries),
        ("Era Span", "200 BC - 1700 AD"),
        ("Traditions", len({d["tradition"] for d in data})),
    ])
    sorted_data = sorted(data, key=lambda d: d["lon"])
    m = _build_map(
        sorted_data, [35, 40], 3,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Era": d["era"], "Tradition": d["tradition"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['era']})",
        route_line=True,
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Era": d["era"], "Tradition": d["tradition"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "paper_making_history.csv", "dl_paper_hist")


def _render_origami_conventions():
    """Render World Origami Conventions mode."""
    data = WORLD_ORIGAMI_CONVENTIONS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['World Origami Conventions'])}</p>",
        unsafe_allow_html=True,
    )
    continents = set()
    for d in data:
        if d["lon"] > 60:
            continents.add("Asia/Oceania")
        elif d["lon"] < -30:
            continents.add("Americas")
        elif d["lat"] < 20:
            continents.add("Africa")
        else:
            continents.add("Europe/Middle East")
    _render_stats([
        ("Conventions", len(data)),
        ("Continents", len(continents)),
        ("Oldest Founded", "1967"),
        ("Newest Founded", "2008"),
    ])
    m = _build_map(
        data, [30, 10], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Frequency": d["frequency"], "Founded": d["founded"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['frequency']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Frequency": d["frequency"], "Founded": d["founded"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "origami_conventions.csv", "dl_origami_conv")


def _render_paper_museums():
    """Render Paper Art Museums mode."""
    data = PAPER_ART_MUSEUMS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Paper Art Museums'])}</p>",
        unsafe_allow_html=True,
    )
    countries = len({d["name"].split(",")[-1].strip() for d in data})
    _render_stats([
        ("Museums Mapped", len(data)),
        ("Countries", countries),
        ("Focus Areas", len({d["focus"] for d in data})),
    ])
    m = _build_map(
        data, [35, 20], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Focus": d["focus"], "Collection": d["collection"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['focus']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Focus": d["focus"], "Collection": d["collection"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "paper_art_museums.csv", "dl_paper_museums")


def _render_kirigami():
    """Render Kirigami & Paper Cutting mode."""
    data = KIRIGAMI_PAPER_CUTTING
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Kirigami & Paper Cutting'])}</p>",
        unsafe_allow_html=True,
    )
    traditions = list({d["tradition"] for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Traditions", len(traditions)),
        ("Countries", len({d["name"].split(",")[-1].strip() for d in data if "," in d["name"]})),
    ])
    m = _build_map(
        data, [30, 50], 2,
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
    _render_table_download(df, "kirigami_paper_cutting.csv", "dl_kirigami")


def _render_book_binding():
    """Render Book Binding Heritage mode."""
    data = BOOK_BINDING_HERITAGE
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Book Binding Heritage'])}</p>",
        unsafe_allow_html=True,
    )
    countries = len({d["name"].split(",")[-1].strip() for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Countries", countries),
        ("Era Span", "400 AD - 1950"),
        ("Traditions", len({d["tradition"] for d in data})),
    ])
    m = _build_map(
        data, [35, 20], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Tradition": d["tradition"], "Era": d["era"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['era']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Tradition": d["tradition"], "Era": d["era"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "book_binding_heritage.csv", "dl_book_bind")


def _render_papyrus():
    """Render Papyrus Origins mode."""
    data = PAPYRUS_ORIGINS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Papyrus Origins'])}</p>",
        unsafe_allow_html=True,
    )
    materials = list({d["material"] for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Material Types", len(materials)),
        ("Era Span", "3000 BC - 700 AD"),
        ("Countries", len({d["name"].split(",")[-1].strip() for d in data})),
    ])
    m = _build_map(
        data, [32, 25], 3,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Era": d["era"], "Material": d["material"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['era']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Era": d["era"], "Material": d["material"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "papyrus_origins.csv", "dl_papyrus")


def _render_kite_traditions():
    """Render Kite Making Traditions mode."""
    data = KITE_MAKING_TRADITIONS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Kite Making Traditions'])}</p>",
        unsafe_allow_html=True,
    )
    traditions = list({d["tradition"] for d in data})
    countries = set()
    for d in data:
        parts = d["name"].split(",")
        if len(parts) > 1:
            countries.add(parts[-1].strip())
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Traditions", len(traditions)),
        ("Countries", len(countries)),
        ("Heritage Span", "2,000+ years"),
    ])
    m = _build_map(
        data, [25, 60], 2,
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
    _render_table_download(df, "kite_traditions.csv", "dl_kites")


def _render_paper_cranes():
    """Render Paper Crane Memorials mode."""
    data = PAPER_CRANE_MEMORIALS
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Paper Crane Memorials'])}</p>",
        unsafe_allow_html=True,
    )
    types = list({d["type"] for d in data})
    _render_stats([
        ("Sites Mapped", len(data)),
        ("Memorial Types", len(types)),
        ("Countries", len({d["name"].split(",")[-1].strip() for d in data})),
        ("Legacy", "Sadako 1955"),
    ])
    m = _build_map(
        data, [35, 60], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Type": d["type"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} ({d['type']})",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Type": d["type"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "paper_crane_memorials.csv", "dl_cranes")


def _render_paper_architecture():
    """Render Modern Paper Architecture mode."""
    data = MODERN_PAPER_ARCHITECTURE
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(MODE_DESCRIPTIONS['Modern Paper Architecture'])}</p>",
        unsafe_allow_html=True,
    )
    architects = list({d["architect"] for d in data})
    types = list({d["type"] for d in data})
    _render_stats([
        ("Buildings Mapped", len(data)),
        ("Architects", len(architects)),
        ("Building Types", len(types)),
        ("Pioneer", "Shigeru Ban"),
    ])
    m = _build_map(
        data, [30, 30], 2,
        popup_fn=lambda d: _popup_html(d["name"], {
            "Type": d["type"], "Architect": d["architect"], "Notes": d["notes"],
        }, accent=d["color"]),
        tooltip_fn=lambda d: f"{d['name']} - {d['architect']}",
    )
    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame([{
        "Name": d["name"], "Latitude": d["lat"], "Longitude": d["lon"],
        "Type": d["type"], "Architect": d["architect"], "Notes": d["notes"],
    } for d in data])
    _render_table_download(df, "paper_architecture.csv", "dl_paper_arch")


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_origami_maps_tab():
    """Render the Origami & Paper Arts Explorer tab for TerraScout AI."""

    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001f9a2 Origami & Paper Arts Explorer</h4>'
        '<p>Explore origami heritage, papermaking history, kirigami traditions, and paper architecture worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected = st.selectbox("Map Mode", MAP_MODES, key="origami_maps_mode")

    mode_color = MODE_COLORS.get(selected, _ACCENT)
    st.markdown(
        f"<hr style='border-color:{html_module.escape(mode_color)};opacity:0.4;'>",
        unsafe_allow_html=True,
    )

    # Dispatch to the appropriate renderer
    if selected == "Japanese Origami Heritage":
        _render_japanese_origami()
    elif selected == "Paper Making History":
        _render_paper_making()
    elif selected == "World Origami Conventions":
        _render_origami_conventions()
    elif selected == "Paper Art Museums":
        _render_paper_museums()
    elif selected == "Kirigami & Paper Cutting":
        _render_kirigami()
    elif selected == "Book Binding Heritage":
        _render_book_binding()
    elif selected == "Papyrus Origins":
        _render_papyrus()
    elif selected == "Kite Making Traditions":
        _render_kite_traditions()
    elif selected == "Paper Crane Memorials":
        _render_paper_cranes()
    elif selected == "Modern Paper Architecture":
        _render_paper_architecture()
