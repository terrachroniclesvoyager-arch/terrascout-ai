# -*- coding: utf-8 -*-
"""
Ancient Writing & Scripts Explorer module for TerraScout AI.
Curated geospatial datasets covering 10 modes of world writing systems,
scripts, inscriptions, libraries, printing, postal history, and alphabet
evolution.  All data is embedded (no external API needed), displayed on
Folium dark-matter maps with Matplotlib charts, Pandas tables, and CSV
download.
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

# ═══════════════════════════════════════════════════════════════════════
# COLOR PALETTE  (matches TerraScout glassmorphism theme)
# ═══════════════════════════════════════════════════════════════════════
BG_OUTER  = "#0a0e1a"
BG_INNER  = "#111827"
TEXT_PRI   = "#e8ecf4"
TEXT_SEC   = "#8b97b0"
TEXT_MUT   = "#5a6580"
ACCENT     = "#06b6d4"
GRID_CLR   = "#2a3550"
SPINE_CLR  = "#2a3550"

MODE_COLORS = {
    "Birth of Writing":            "#f59e0b",
    "Undeciphered Scripts":        "#ef4444",
    "Rosetta Stones":              "#8b5cf6",
    "Ancient Libraries":           "#06b6d4",
    "Printing Press Revolution":   "#10b981",
    "World Writing Systems":       "#ec4899",
    "Stone Inscriptions":          "#f97316",
    "Manuscript Traditions":       "#38bdf8",
    "Postal & Communication":      "#a855f7",
    "Alphabet Origins":            "#14b8a6",
}

# ═══════════════════════════════════════════════════════════════════════
# CURATED DATASETS  (10 modes, ~20-30 entries each)
# ═══════════════════════════════════════════════════════════════════════

BIRTH_OF_WRITING = [
    {"name": "Uruk (Warka) - Earliest Cuneiform",       "lat": 31.3225, "lon": 45.6367, "date": "c. 3400 BCE", "script": "Proto-Cuneiform",    "region": "Mesopotamia",  "notes": "Clay tablets with earliest known writing; administrative records from Uruk IV period."},
    {"name": "Kish Tablet",                              "lat": 32.5500, "lon": 44.6333, "date": "c. 3500 BCE", "script": "Proto-Cuneiform",    "region": "Mesopotamia",  "notes": "Limestone tablet possibly pre-dating Uruk; debated as earliest writing."},
    {"name": "Jemdet Nasr",                              "lat": 32.3167, "lon": 44.5333, "date": "c. 3100 BCE", "script": "Proto-Cuneiform",    "region": "Mesopotamia",  "notes": "Administrative tablets with city names; crucial for early Sumerian studies."},
    {"name": "Nippur Library",                           "lat": 32.1264, "lon": 45.2317, "date": "c. 2500 BCE", "script": "Sumerian Cuneiform", "region": "Mesopotamia",  "notes": "One of the oldest known libraries; thousands of cuneiform tablets recovered."},
    {"name": "Abydos - Tomb U-j (Predynastic)",         "lat": 26.1852, "lon": 31.9190, "date": "c. 3320 BCE", "script": "Proto-Hieroglyphs",  "region": "Egypt",        "notes": "Ivory labels with early hieroglyphic signs from tomb of Scorpion I."},
    {"name": "Thebes (Luxor) - Temple Inscriptions",    "lat": 25.6969, "lon": 32.6422, "date": "c. 2000 BCE", "script": "Egyptian Hieroglyphs","region": "Egypt",        "notes": "Karnak and Luxor temples bear some of the most elaborate hieroglyphic texts."},
    {"name": "Saqqara - Pyramid Texts",                 "lat": 29.8713, "lon": 31.2165, "date": "c. 2400 BCE", "script": "Egyptian Hieroglyphs","region": "Egypt",        "notes": "Oldest known religious texts; carved inside pyramid of Unas."},
    {"name": "Memphis - Capital Script Center",         "lat": 29.8486, "lon": 31.2547, "date": "c. 3100 BCE", "script": "Egyptian Hieroglyphs","region": "Egypt",        "notes": "Administrative center; earliest royal inscriptions including Narmer Palette."},
    {"name": "Anyang - Oracle Bone Pits",               "lat": 36.1200, "lon": 114.3500,"date": "c. 1250 BCE", "script": "Oracle Bone Script",  "region": "China",        "notes": "Shang dynasty divination bones; earliest substantial Chinese writing."},
    {"name": "Erlitou - Proto-Chinese Signs",           "lat": 34.6833, "lon": 112.6833,"date": "c. 1900 BCE", "script": "Proto-Chinese",       "region": "China",        "notes": "Possible precursor signs on pottery; linked to Xia dynasty."},
    {"name": "Zhengzhou - Shang Inscriptions",          "lat": 34.7533, "lon": 113.6653,"date": "c. 1500 BCE", "script": "Oracle Bone Script",  "region": "China",        "notes": "Early Shang capital with inscribed bronzes and oracle bones."},
    {"name": "Jiahu Symbols",                           "lat": 33.6167, "lon": 113.6667,"date": "c. 6600 BCE", "script": "Jiahu Symbols",       "region": "China",        "notes": "Tortoise shell carvings; debated as possible proto-writing or tally marks."},
    {"name": "Tartaria Tablets (Romania)",               "lat": 46.0167, "lon": 23.6000, "date": "c. 5500 BCE", "script": "Vinca Symbols",       "region": "Europe",       "notes": "Neolithic tablets with symbols; hotly debated as proto-writing."},
    {"name": "Dispilio Tablet (Greece)",                "lat": 40.4833, "lon": 21.3000, "date": "c. 5260 BCE", "script": "Dispilio Symbols",    "region": "Europe",       "notes": "Wooden tablet with inscribed symbols from lakeside settlement."},
    {"name": "Olmec - San Lorenzo (Mesoamerica)",       "lat": 17.7500, "lon": -94.7667, "date": "c. 900 BCE", "script": "Olmec Glyphs",        "region": "Mesoamerica",  "notes": "Cascajal Block bears earliest New World script; 62 distinct signs."},
    {"name": "Monte Alban - Zapotec Script",            "lat": 17.0436, "lon": -96.7678, "date": "c. 500 BCE", "script": "Zapotec Script",      "region": "Mesoamerica",  "notes": "Danzante slabs with early Mesoamerican writing; calendar and names."},
    {"name": "Harappa - Indus Script Seals",            "lat": 30.6280, "lon": 72.8640, "date": "c. 2600 BCE", "script": "Indus Script",        "region": "South Asia",   "notes": "Steatite seals with undeciphered Indus Valley symbols."},
    {"name": "Mohenjo-daro - Indus Tablets",            "lat": 27.3242, "lon": 68.1385, "date": "c. 2500 BCE", "script": "Indus Script",        "region": "South Asia",   "notes": "Major Indus city with thousands of inscribed seals and tablets."},
    {"name": "Wadi el-Hol Inscriptions",                "lat": 25.9500, "lon": 32.5000, "date": "c. 1900 BCE", "script": "Proto-Sinaitic",      "region": "Egypt",        "notes": "Rock inscriptions representing early alphabet; link to Phoenician."},
    {"name": "Byblos - Early Alphabetic Texts",         "lat": 34.1208, "lon": 35.6517, "date": "c. 1050 BCE", "script": "Phoenician",          "region": "Levant",       "notes": "Ahiram sarcophagus inscription; one of oldest Phoenician texts."},
    {"name": "Ebla - Palace Archive Tablets",            "lat": 35.7983, "lon": 36.7950, "date": "c. 2400 BCE", "script": "Sumerian/Eblaite",    "region": "Levant",       "notes": "1800 cuneiform tablets with earliest known library catalog."},
    {"name": "Tell Brak - Ur III Administration",        "lat": 36.6667, "lon": 41.0500, "date": "c. 2100 BCE", "script": "Sumerian Cuneiform", "region": "Mesopotamia",  "notes": "Administrative center of the Ur III empire; thousands of clay records."},
    {"name": "Persepolis - Old Persian Cuneiform",       "lat": 29.9352, "lon": 52.8906, "date": "c. 500 BCE",  "script": "Old Persian",         "region": "Persia",       "notes": "Royal inscriptions of Darius and Xerxes; purpose-built cuneiform script."},
    {"name": "Tikal - Maya Stelae",                      "lat": 17.2220, "lon": -89.6237, "date": "c. 292 CE",  "script": "Maya Glyphs",         "region": "Mesoamerica",  "notes": "Stela 29 bears earliest Long Count date at Tikal; fully logosyllabic."},
    {"name": "Copan - Maya Hieroglyphic Stairway",       "lat": 14.8400, "lon": -89.1400, "date": "c. 756 CE",  "script": "Maya Glyphs",         "region": "Mesoamerica",  "notes": "Longest known Maya text; 2200 glyphs on 63 steps."},
]

UNDECIPHERED_SCRIPTS = [
    {"name": "Knossos - Linear A Tablets",               "lat": 35.2981, "lon": 25.1631, "date": "c. 1800 BCE", "script": "Linear A",           "status": "Undeciphered", "notes": "Minoan palatial script; ~1400 known texts, language unknown."},
    {"name": "Phaistos - Phaistos Disc",                 "lat": 35.0514, "lon": 24.8139, "date": "c. 1700 BCE", "script": "Phaistos Disc",      "status": "Undeciphered", "notes": "Unique stamped clay disc; 45 distinct signs in spiral arrangement."},
    {"name": "Hagia Triada - Linear A Archive",          "lat": 35.0600, "lon": 24.7700, "date": "c. 1500 BCE", "script": "Linear A",           "status": "Undeciphered", "notes": "Largest cache of Linear A tablets; administrative records."},
    {"name": "Easter Island - Rongorongo",               "lat": -27.1127,"lon": -109.3497,"date": "pre-1860s",  "script": "Rongorongo",          "status": "Undeciphered", "notes": "Wooden tablets with glyphs; only 26 survive worldwide."},
    {"name": "Mohenjo-daro - Indus Seals",               "lat": 27.3242, "lon": 68.1385, "date": "c. 2600 BCE", "script": "Indus Script",       "status": "Undeciphered", "notes": "Over 4000 inscribed objects; average text length only 5 signs."},
    {"name": "Harappa - Indus Valley Tablets",           "lat": 30.6280, "lon": 72.8640, "date": "c. 2500 BCE", "script": "Indus Script",       "status": "Undeciphered", "notes": "Steatite seals with animal motifs and undeciphered script."},
    {"name": "Dholavira - Indus Signboard",              "lat": 23.8880, "lon": 70.2080, "date": "c. 2500 BCE", "script": "Indus Script",       "status": "Undeciphered", "notes": "Large signboard with 10 Indus characters; possibly a city name."},
    {"name": "Beinecke Library - Voynich Manuscript",    "lat": 41.3111, "lon": -72.9267, "date": "c. 1420 CE", "script": "Voynichese",         "status": "Undeciphered", "notes": "240-page illustrated codex in unknown script; carbon-dated 15th century."},
    {"name": "Cypro-Minoan - Enkomi",                   "lat": 35.1550, "lon": 33.8833, "date": "c. 1500 BCE", "script": "Cypro-Minoan",       "status": "Undeciphered", "notes": "Bronze Age script from Cyprus; ~250 known inscriptions."},
    {"name": "Proto-Elamite - Susa",                    "lat": 32.1900, "lon": 48.2500, "date": "c. 3100 BCE", "script": "Proto-Elamite",      "status": "Undeciphered", "notes": "Over 1600 tablets; earliest writing system from Iran."},
    {"name": "Isthmian Script - La Mojarra Stela",       "lat": 18.4333, "lon": -95.6167, "date": "c. 150 CE",  "script": "Isthmian (Epi-Olmec)","status":"Partially read","notes": "Stela 1 with 535 glyphs; partial decipherment debated."},
    {"name": "Wadi el-Hol Proto-Sinaitic",              "lat": 25.9500, "lon": 32.5000, "date": "c. 1900 BCE", "script": "Proto-Sinaitic",     "status": "Partially read","notes": "Rock inscriptions; key link between hieroglyphs and alphabet."},
    {"name": "Byblos Syllabary Texts",                   "lat": 34.1208, "lon": 35.6517, "date": "c. 1800 BCE", "script": "Byblos Syllabary",   "status": "Undeciphered", "notes": "Ten known inscriptions on bronze spatulae and stone."},
    {"name": "Sitovo Inscription (Bulgaria)",            "lat": 41.9833, "lon": 24.6833, "date": "c. 1200 BCE", "script": "Unknown Thracian",   "status": "Undeciphered", "notes": "Rock inscription with unknown script near Plovdiv."},
    {"name": "Cascajal Block - Olmec Script",            "lat": 17.7500, "lon": -94.7667, "date": "c. 900 BCE", "script": "Olmec Glyphs",       "status": "Undeciphered", "notes": "Serpentine block with 62 signs; earliest New World writing."},
    {"name": "Singapore Stone Fragment",                 "lat":  1.2870, "lon": 103.8512, "date": "c. 1000 CE", "script": "Unknown",            "status": "Undeciphered", "notes": "Sandstone fragment with 50+ characters; possibly Old Javanese."},
    {"name": "Cretan Hieroglyphs - Malia",               "lat": 35.2900, "lon": 25.4950, "date": "c. 2100 BCE", "script": "Cretan Hieroglyphs", "status": "Undeciphered", "notes": "Pre-Linear A script found on seals and clay tablets at Malia palace."},
    {"name": "Rapa Nui Museum - Rongorongo Display",     "lat": -27.1500,"lon": -109.4300,"date": "19th cent.", "script": "Rongorongo",          "status": "Undeciphered", "notes": "Museum displays replica boards; original tablets scattered in world museums."},
    {"name": "Khipu Archive - Inkawasi, Peru",           "lat": -13.0500,"lon": -75.8333, "date": "c. 1400 CE", "script": "Quipu (Khipu)",      "status": "Partially read","notes": "Inca knotted string records; debated whether these encode narrative text."},
]

ROSETTA_STONES = [
    {"name": "Rosetta Stone (British Museum)",           "lat": 51.5194, "lon": -0.1269, "date": "196 BCE",     "artifact": "Rosetta Stone",           "scripts": "Hieroglyphic, Demotic, Greek",   "notes": "Decree of Ptolemy V; enabled Champollion's 1822 decipherment of hieroglyphs."},
    {"name": "Rosetta (Rashid) - Discovery Site",        "lat": 31.4000, "lon": 30.4167, "date": "Found 1799", "artifact": "Rosetta Stone (orig.)",    "scripts": "Hieroglyphic, Demotic, Greek",   "notes": "Fort Julien; French soldiers discovered the stone during Napoleon's campaign."},
    {"name": "Behistun Inscription - Kermanshah",        "lat": 34.3886, "lon": 47.4369, "date": "c. 520 BCE", "artifact": "Behistun Inscription",    "scripts": "Old Persian, Elamite, Babylonian","notes": "Trilingual cliff carving by Darius I; key to cuneiform decipherment."},
    {"name": "Karnak Bilingual Stele",                   "lat": 25.7188, "lon": 32.6573, "date": "c. 250 BCE", "artifact": "Karnak Bilingual",        "scripts": "Hieroglyphic, Demotic",          "notes": "Ptolemaic bilingual decree aiding hieroglyphic studies."},
    {"name": "Canopus Decree - Tanis",                   "lat": 30.9797, "lon": 31.8784, "date": "238 BCE",    "artifact": "Canopus Decree",          "scripts": "Hieroglyphic, Demotic, Greek",   "notes": "Trilingual decree pre-dating Rosetta Stone; confirmed decipherment."},
    {"name": "Gortyn Code - Crete",                     "lat": 35.0622, "lon": 24.9461, "date": "c. 450 BCE", "artifact": "Gortyn Code",             "scripts": "Archaic Greek (boustrophedon)",  "notes": "Longest known Greek inscription; 12 columns of civil law."},
    {"name": "Xanthus Trilingual - Turkey",             "lat": 36.3550, "lon": 29.3172, "date": "c. 337 BCE", "artifact": "Xanthus Obelisk",         "scripts": "Lycian, Greek, Aramaic",         "notes": "Trilingual stele; instrumental in deciphering Lycian language."},
    {"name": "Tell el-Amarna Letters",                  "lat": 27.6450, "lon": 30.9000, "date": "c. 1350 BCE", "artifact": "Amarna Letters",          "scripts": "Akkadian Cuneiform",             "notes": "382 diplomatic tablets showing Babylonian as lingua franca."},
    {"name": "Rawlinson's Cuneiform Copies - London",   "lat": 51.5194, "lon": -0.1269, "date": "1850s CE",   "artifact": "Behistun Copies",         "scripts": "Old Persian, Babylonian",        "notes": "Henry Rawlinson's transcriptions that cracked cuneiform script."},
    {"name": "Mesha Stele - Louvre, Paris",             "lat": 48.8606, "lon": 2.3376,  "date": "c. 840 BCE", "artifact": "Moabite Stone",           "scripts": "Moabite (Phoenician variant)",   "notes": "Longest Iron Age inscription in Moabite; confirms biblical king Omri."},
    {"name": "Siloam Inscription - Jerusalem",          "lat": 31.7700, "lon": 35.2353, "date": "c. 700 BCE", "artifact": "Siloam Inscription",      "scripts": "Paleo-Hebrew",                   "notes": "Tunnel inscription describing Hezekiah's water tunnel construction."},
    {"name": "Philae Obelisk",                          "lat": 24.0262, "lon": 32.8841, "date": "c. 118 BCE", "artifact": "Philae Obelisk",          "scripts": "Hieroglyphic, Greek",            "notes": "Paired with Rosetta Stone; helped Champollion confirm phonetic signs."},
    {"name": "Decree of Canopus - Cairo Museum",        "lat": 30.0476, "lon": 31.2336, "date": "238 BCE",    "artifact": "Canopus Stele (copy)",    "scripts": "Hieroglyphic, Demotic, Greek",   "notes": "Museum copy confirming trilingual decree patterns."},
    {"name": "Bilingual Coin of Kanishka",              "lat": 34.0151, "lon": 71.5249, "date": "c. 130 CE",  "artifact": "Kanishka Coin",           "scripts": "Greek, Bactrian",                "notes": "Kushan coins showing script transition from Greek to local script."},
    {"name": "Ezana Stone - Aksum",                     "lat": 14.1308, "lon": 38.7200, "date": "c. 340 CE",  "artifact": "Ezana Inscription",       "scripts": "Ge'ez, Sabaean, Greek",          "notes": "Trilingual stele; earliest evidence of Christianity in Ethiopia."},
    {"name": "Karatepe Bilingual - Cilicia",             "lat": 37.2833, "lon": 36.2500, "date": "c. 700 BCE", "artifact": "Karatepe Inscription",    "scripts": "Phoenician, Luwian Hieroglyphs", "notes": "Key bilingual that confirmed Luwian hieroglyphic decipherment."},
    {"name": "Daiva Inscription - Persepolis",           "lat": 29.9352, "lon": 52.8906, "date": "c. 486 BCE", "artifact": "Xerxes Daiva",            "scripts": "Old Persian, Elamite, Babylonian","notes": "Trilingual tablet declaring Xerxes's religious reforms."},
    {"name": "Darius Suez Canal Stelae",                 "lat": 30.4500, "lon": 32.3500, "date": "c. 500 BCE", "artifact": "Suez Stelae",             "scripts": "Old Persian, Elamite, Babylonian, Hieroglyphs","notes": "Quadrilingual stelae commemorating Darius I's canal construction."},
]

ANCIENT_LIBRARIES = [
    {"name": "Library of Alexandria (site)",             "lat": 31.2089, "lon": 29.9092, "date": "c. 295 BCE", "type": "Royal Library",      "est_volumes": "400,000-700,000", "notes": "Greatest ancient library; destroyed in stages over centuries."},
    {"name": "Bibliotheca Alexandrina (modern)",         "lat": 31.2089, "lon": 29.9092, "date": "2002 CE",    "type": "Modern Revival",     "est_volumes": "8,000,000",       "notes": "UNESCO-backed revival near original site; major research center."},
    {"name": "Library of Pergamum",                      "lat": 39.1317, "lon": 27.1842, "date": "c. 200 BCE", "type": "Royal Library",      "est_volumes": "200,000",         "notes": "Rival to Alexandria; invention of parchment credited to Pergamum."},
    {"name": "Library of Ashurbanipal - Nineveh",        "lat": 36.3594, "lon": 43.1528, "date": "c. 668 BCE", "type": "Royal Archive",      "est_volumes": "30,000+",         "notes": "First systematically collected library; Epic of Gilgamesh found here."},
    {"name": "Qumran - Dead Sea Scrolls",                "lat": 31.7414, "lon": 35.4594, "date": "c. 250 BCE", "type": "Scroll Repository",  "est_volumes": "981 manuscripts", "notes": "Discovered 1947; oldest known biblical manuscripts."},
    {"name": "Library of Celsus - Ephesus",              "lat": 37.9399, "lon": 27.3419, "date": "c. 120 CE",  "type": "Roman Library",      "est_volumes": "12,000",          "notes": "Ornate Roman facade survives; held scrolls in wall niches."},
    {"name": "Villa of the Papyri - Herculaneum",        "lat": 40.8058, "lon": 14.3481, "date": "c. 50 BCE",  "type": "Private Library",    "est_volumes": "1,800",           "notes": "Carbonized scrolls preserved by Vesuvius; being read with AI/X-ray."},
    {"name": "Imperial Library of Constantinople",       "lat": 41.0082, "lon": 28.9784, "date": "c. 357 CE",  "type": "Imperial Library",   "est_volumes": "120,000",         "notes": "Preserved Greek classics through Byzantine era; destroyed 1204."},
    {"name": "House of Wisdom - Baghdad",                "lat": 33.3406, "lon": 44.4009, "date": "c. 830 CE",  "type": "Translation Center", "est_volumes": "400,000+",        "notes": "Abbasid center of learning; translated Greek works into Arabic."},
    {"name": "Nalanda University Library",               "lat": 25.1357, "lon": 85.4458, "date": "c. 500 CE",  "type": "Monastic Library",   "est_volumes": "9,000,000",       "notes": "Three multi-story buildings; said to have burned for months."},
    {"name": "Dunhuang Library Cave (Cave 17)",          "lat": 40.0422, "lon": 94.8036, "date": "c. 400 CE",  "type": "Hidden Repository",  "est_volumes": "50,000+",         "notes": "Sealed c.1000 CE; discovered 1900; earliest printed book (868 CE)."},
    {"name": "Timbuktu Manuscripts",                     "lat": 16.7735, "lon": -3.0074, "date": "c. 1300 CE", "type": "Islamic Libraries",  "est_volumes": "700,000",         "notes": "Hundreds of thousands of manuscripts in private collections."},
    {"name": "Vatican Apostolic Library",                "lat": 41.9022, "lon": 12.4539, "date": "1475 CE",    "type": "Papal Library",      "est_volumes": "1,600,000",       "notes": "Among oldest libraries in continuous operation; 80,000 manuscripts."},
    {"name": "Bodleian Library - Oxford",                "lat": 51.7538, "lon": -1.2544, "date": "1602 CE",    "type": "University Library", "est_volumes": "13,000,000",      "notes": "Major research library; holds original First Folio of Shakespeare."},
    {"name": "Abbey of Monte Cassino",                   "lat": 41.4903, "lon": 13.8142, "date": "c. 529 CE",  "type": "Monastic Library",   "est_volumes": "Unknown",         "notes": "Benedictine monks preserved classical texts; destroyed and rebuilt."},
    {"name": "Library of Ebla - Tell Mardikh",           "lat": 35.7983, "lon": 36.7950, "date": "c. 2400 BCE","type": "Palace Archive",     "est_volumes": "1,800 tablets",   "notes": "Earliest known library catalog; cuneiform tablets in Eblaite language."},
    {"name": "Ugarit Royal Library",                     "lat": 35.6006, "lon": 35.7825, "date": "c. 1200 BCE","type": "Palace Archive",     "est_volumes": "2,000+",          "notes": "Cuneiform tablets in 7 languages; earliest known alphabet (Ugaritic)."},
    {"name": "Chester Beatty Library - Dublin",          "lat": 53.3418, "lon": -6.2674, "date": "1950 CE",    "type": "Manuscript Museum",  "est_volumes": "Priceless coll.", "notes": "Holds earliest known New Testament papyri (Chester Beatty Papyri)."},
    {"name": "Taxila - Gandhara Library",                "lat": 33.7460, "lon": 72.7980, "date": "c. 400 BCE", "type": "Monastic Library",   "est_volumes": "Unknown",         "notes": "Buddhist university complex; Dharmarajika Stupa manuscripts."},
    {"name": "Library of Aristotle - Athens",            "lat": 37.9755, "lon": 23.7348, "date": "c. 335 BCE", "type": "Private Library",    "est_volumes": "Unknown",         "notes": "Perhaps first great private collection; became model for Alexandrian library."},
    {"name": "Vivarium Monastery Library - Calabria",    "lat": 38.7631, "lon": 16.5147, "date": "c. 540 CE",  "type": "Monastic Library",   "est_volumes": "Unknown",         "notes": "Cassiodorus preserved classical texts through systematic copying."},
    {"name": "St. Catherine's Monastery - Sinai",        "lat": 28.5562, "lon": 33.9757, "date": "c. 548 CE",  "type": "Monastic Library",   "est_volumes": "3,300 MSS",       "notes": "Oldest continuously operating library; Codex Sinaiticus found here."},
]

PRINTING_PRESS = [
    {"name": "Gutenberg's Workshop - Mainz",            "lat": 49.9987, "lon": 8.2712,  "date": "c. 1440 CE", "type": "First Movable Type (Europe)", "notes": "Johannes Gutenberg developed movable metal type; printed the 42-line Bible c.1455."},
    {"name": "Gutenberg Museum - Mainz",                 "lat": 50.0003, "lon": 8.2730,  "date": "1900 CE",    "type": "Printing Museum",             "notes": "Houses two original Gutenberg Bibles; world's premier printing museum."},
    {"name": "Subiaco - First Italian Press",            "lat": 41.9253, "lon": 13.0928, "date": "1465 CE",    "type": "Early Press",                 "notes": "German printers Sweynheym & Pannartz set up Italy's first press."},
    {"name": "Venice - Aldus Manutius Press",            "lat": 45.4347, "lon": 12.3385, "date": "1494 CE",    "type": "Aldine Press",                "notes": "Invented italic type and pocket-sized books; printed Greek classics."},
    {"name": "Bi Sheng - Yingshan, Hubei",              "lat": 31.1333, "lon": 115.6833, "date": "c. 1040 CE","type": "First Movable Type (World)",  "notes": "Bi Sheng invented ceramic movable type in Song Dynasty China."},
    {"name": "Jikji Printing Site - Cheongju",          "lat": 36.6357, "lon": 127.4915, "date": "1377 CE",   "type": "Metal Movable Type",          "notes": "Jikji: oldest surviving metal movable type book; UNESCO Memory of World."},
    {"name": "Nara - Hyakumanto Darani",                "lat": 34.6851, "lon": 135.8048, "date": "770 CE",    "type": "Earliest Mass Printing",      "notes": "Empress Shotoku ordered 1 million printed dharani; oldest printed texts."},
    {"name": "Dunhuang Diamond Sutra Site",              "lat": 40.0422, "lon": 94.8036, "date": "868 CE",     "type": "Woodblock Print",             "notes": "Oldest dated printed book; discovered in Cave 17 by Aurel Stein."},
    {"name": "Strasbourg - Early Gutenberg Work",        "lat": 48.5734, "lon": 7.7521,  "date": "c. 1440 CE", "type": "Early Experiments",           "notes": "Gutenberg developed his press techniques here before moving to Mainz."},
    {"name": "Westminster - Caxton's Press",             "lat": 51.4994, "lon": -0.1248, "date": "1476 CE",    "type": "First English Press",         "notes": "William Caxton set up first printing press in England."},
    {"name": "Nuremberg - Koberger Press",               "lat": 49.4521, "lon": 11.0767, "date": "1470 CE",   "type": "Major Early Press",           "notes": "Anton Koberger ran 24 presses; largest publisher in 15th-century Europe."},
    {"name": "Lyon - French Print Center",               "lat": 45.7640, "lon": 4.8357,  "date": "1473 CE",    "type": "French Printing Hub",         "notes": "Major printing center with hundreds of active presses by 1500."},
    {"name": "Hangzhou - Song Woodblock Center",         "lat": 30.2741, "lon": 120.1551,"date": "c. 950 CE",  "type": "Woodblock Hub",               "notes": "Southern Song capital; thousands of woodblock printed books produced."},
    {"name": "Bamberg - 36-Line Bible",                  "lat": 49.8988, "lon": 10.9028, "date": "c. 1458 CE", "type": "Early Bible Printing",        "notes": "Albrecht Pfister printed earliest illustrated books; 36-line Bible."},
    {"name": "Rome - First Italian Bible",               "lat": 41.9028, "lon": 12.4964, "date": "1467 CE",    "type": "Early Roman Press",           "notes": "Sweynheym & Pannartz moved press to Rome; papal support of printing."},
    {"name": "Seville - New World Printer",              "lat": 37.3891, "lon": -5.9845, "date": "1500s CE",   "type": "Colonial Printing",           "notes": "Gateway for books sent to Americas; first presses shipped to Mexico."},
    {"name": "Mexico City - New World Press",            "lat": 19.4326, "lon": -99.1332, "date": "1539 CE",   "type": "First New World Press",       "notes": "Juan Pablos established first printing press in the Americas."},
    {"name": "Philadelphia - Benjamin Franklin Press",   "lat": 39.9526, "lon": -75.1652, "date": "1728 CE",   "type": "Colonial Press",              "notes": "Franklin's Pennsylvania Gazette and Poor Richard's Almanack."},
    {"name": "Leiden - Elzevir Press",                   "lat": 52.1601, "lon": 4.4970,  "date": "1580 CE",    "type": "Dutch Golden Age Press",      "notes": "Elzevir family pioneered affordable small-format scholarly books."},
    {"name": "Antwerp - Plantin-Moretus Museum",         "lat": 51.2194, "lon": 4.3997,  "date": "1555 CE",    "type": "Renaissance Press",           "notes": "UNESCO World Heritage; oldest surviving printing presses in situ."},
    {"name": "Cambridge - University Press",             "lat": 52.2053, "lon": 0.1218,  "date": "1534 CE",    "type": "University Press",            "notes": "Oldest university press in the world; still in operation."},
]

WRITING_SYSTEMS = [
    {"name": "Rome - Latin Script Origin",               "lat": 41.9028, "lon": 12.4964, "date": "c. 700 BCE", "script": "Latin",       "family": "Latin/Roman", "speakers": "~4.9 billion", "notes": "Derived from Etruscan; now the world's most widely used script."},
    {"name": "Athens - Greek Alphabet Codified",         "lat": 37.9838, "lon": 23.7275, "date": "c. 800 BCE", "script": "Greek",       "family": "Greek",       "speakers": "~13 million",  "notes": "First alphabet with vowels; parent of Latin and Cyrillic."},
    {"name": "Preslav - Cyrillic Creation",              "lat": 43.1600, "lon": 26.8125, "date": "c. 893 CE",  "script": "Cyrillic",    "family": "Cyrillic",    "speakers": "~250 million", "notes": "Created by disciples of Cyril and Methodius at Preslav Literary School."},
    {"name": "Medina - Early Arabic Script",             "lat": 24.4672, "lon": 39.6112, "date": "c. 600 CE",  "script": "Arabic",      "family": "Arabic",      "speakers": "~400 million", "notes": "Quran codification standardized Arabic script; now 3rd most used."},
    {"name": "Varanasi - Devanagari Tradition",          "lat": 25.3176, "lon": 83.0064, "date": "c. 700 CE",  "script": "Devanagari",  "family": "Brahmic",     "speakers": "~600 million", "notes": "Used for Hindi, Sanskrit, Marathi, Nepali; derived from Nagari."},
    {"name": "Xi'an - Chinese Character Standardization","lat": 34.2658, "lon": 108.9541,"date": "c. 220 BCE", "script": "Chinese",     "family": "Sinitic",     "speakers": "~1.3 billion", "notes": "Qin Shi Huang standardized characters; Small Seal Script."},
    {"name": "Kyoto - Japanese Script Development",      "lat": 35.0116, "lon": 135.7681,"date": "c. 800 CE",  "script": "Japanese",    "family": "Japanese",    "speakers": "~128 million", "notes": "Hiragana and Katakana developed from Chinese characters (man'yogana)."},
    {"name": "Seoul - Hangul Creation",                  "lat": 37.5665, "lon": 126.9780,"date": "1443 CE",    "script": "Hangul",      "family": "Korean",      "speakers": "~80 million",  "notes": "Created by King Sejong; scientifically designed featural alphabet."},
    {"name": "Bangkok - Thai Script Center",             "lat": 13.7563, "lon": 100.5018,"date": "c. 1283 CE", "script": "Thai",        "family": "Brahmic",     "speakers": "~60 million",  "notes": "Attributed to King Ramkhamhaeng; derived from Khmer script."},
    {"name": "Addis Ababa - Ge'ez Script Heritage",     "lat":  9.0320, "lon": 38.7469, "date": "c. 500 BCE", "script": "Ge'ez/Ethiopic","family": "Semitic",   "speakers": "~100 million", "notes": "Abugida used for Amharic, Tigrinya; one of oldest African scripts."},
    {"name": "Tbilisi - Georgian Script",                "lat": 41.7151, "lon": 44.8271, "date": "c. 300 CE",  "script": "Georgian",    "family": "Kartvelian",  "speakers": "~4 million",   "notes": "Unique script unrelated to any other; UNESCO intangible heritage."},
    {"name": "Yerevan - Armenian Script",                "lat": 40.1792, "lon": 44.4991, "date": "405 CE",     "script": "Armenian",    "family": "Armenian",    "speakers": "~6 million",   "notes": "Created by Mesrop Mashtots; unique 38-letter alphabet."},
    {"name": "Colombo - Sinhala Script Center",          "lat":  6.9271, "lon": 79.8612, "date": "c. 300 BCE", "script": "Sinhala",     "family": "Brahmic",     "speakers": "~16 million",  "notes": "Rounded letterforms evolved from Brahmi; richly curved script."},
    {"name": "Ulaanbaatar - Mongolian Script",           "lat": 47.8864, "lon": 106.9057,"date": "c. 1204 CE", "script": "Mongolian",   "family": "Uyghur",      "speakers": "~6 million",   "notes": "Vertical script adapted from Uyghur; still used in Inner Mongolia."},
    {"name": "Yangon - Myanmar/Burmese Script",          "lat": 16.8661, "lon": 96.1951, "date": "c. 1050 CE", "script": "Myanmar",     "family": "Brahmic",     "speakers": "~33 million",  "notes": "Circular letterforms derived from Mon script; Brahmic family."},
    {"name": "Phnom Penh - Khmer Script Heritage",       "lat": 11.5564, "lon": 104.9282,"date": "c. 600 CE",  "script": "Khmer",       "family": "Brahmic",     "speakers": "~16 million",  "notes": "Largest alphabet in the world (74 letters); derived from Pallava."},
]

STONE_INSCRIPTIONS = [
    {"name": "Behistun Inscription - Iran",              "lat": 34.3886, "lon": 47.4369, "date": "c. 520 BCE", "type": "Cliff Carving",     "notes": "Trilingual inscription by Darius I on cliff face; 15m x 25m; key to cuneiform."},
    {"name": "Code of Hammurabi (Louvre)",                "lat": 48.8606, "lon": 2.3376,  "date": "c. 1754 BCE","type": "Stele",             "notes": "2.25m basalt stele with 282 laws; one of oldest known legal codes."},
    {"name": "Code of Hammurabi - Original Susa",        "lat": 32.1900, "lon": 48.2500, "date": "c. 1754 BCE","type": "Found Site",        "notes": "Taken as war trophy from Babylon to Susa; excavated by French team."},
    {"name": "Aztec Sun Stone - Mexico City",            "lat": 19.4326, "lon": -99.1332, "date": "c. 1427 CE","type": "Carved Monolith",   "notes": "3.6m basalt disc; calendar stone depicting cosmological cycles."},
    {"name": "Moai with Petroglyphs - Easter Island",    "lat": -27.1127,"lon": -109.3497,"date": "c. 1200 CE","type": "Rock Carving",      "notes": "Petroglyphs on moai backs; birdman cult symbols at Orongo."},
    {"name": "Rock Edicts of Ashoka - Shahbazgarhi",     "lat": 34.2167, "lon": 71.9667, "date": "c. 260 BCE", "type": "Rock Edict",        "notes": "Kharosthi script edicts of Emperor Ashoka; Buddhist moral precepts."},
    {"name": "Ashoka Pillar - Lumbini",                  "lat": 27.4833, "lon": 83.2767, "date": "c. 250 BCE", "type": "Pillar Inscription", "notes": "Marks Buddha's birthplace; oldest datable Brahmi inscription."},
    {"name": "Trajan's Column - Rome",                   "lat": 41.8956, "lon": 12.4843, "date": "113 CE",     "type": "Spiral Column",     "notes": "30m column with 155 scenes; inscription is model for Trajan typeface."},
    {"name": "Rune Stones of Jelling - Denmark",         "lat": 55.7537, "lon": 9.4181,  "date": "c. 965 CE",  "type": "Rune Stone",        "notes": "Harald Bluetooth's stone; marks Denmark's conversion to Christianity."},
    {"name": "Rosetta Stone - British Museum",           "lat": 51.5194, "lon": -0.1269, "date": "196 BCE",    "type": "Granodiorite Stele", "notes": "Trilingual decree that unlocked Egyptian hieroglyphs."},
    {"name": "Bisitun Relief - Detail",                  "lat": 34.3886, "lon": 47.4369, "date": "c. 520 BCE", "type": "Rock Relief",       "notes": "Shows Darius I with conquered rebels; UNESCO World Heritage."},
    {"name": "Boundary Stelae of Akhenaten - Amarna",    "lat": 27.6450, "lon": 30.9000, "date": "c. 1350 BCE","type": "Boundary Marker",   "notes": "14 rock-cut stelae marking boundaries of Akhetaten."},
    {"name": "Hittite Rock Inscriptions - Yazilikaya",   "lat": 40.0253, "lon": 34.5903, "date": "c. 1250 BCE","type": "Rock Sanctuary",    "notes": "Open-air sanctuary with Luwian hieroglyphic carvings of gods."},
    {"name": "Tiwanaku Gate of the Sun - Bolivia",       "lat": -16.5546,"lon": -68.6733, "date": "c. 500 CE", "type": "Carved Gateway",    "notes": "Monolithic archway with carved iconography; calendar interpretations debated."},
    {"name": "Ggantija Temples Inscription - Gozo",      "lat": 36.0472, "lon": 14.2692, "date": "c. 3600 BCE","type": "Megalithic Temple",  "notes": "Oldest free-standing structures; possible ritual markings on stones."},
    {"name": "Dighton Rock - Massachusetts",             "lat": 41.7848, "lon": -71.1287, "date": "Unknown",   "type": "Petroglyphs",       "notes": "Mysterious inscriptions; attributed to Norse, Phoenician, or Native American."},
    {"name": "Stone of Scone - Edinburgh",               "lat": 55.9486, "lon": -3.2008, "date": "c. 700 CE",  "type": "Coronation Stone",  "notes": "Scottish coronation stone with possible inscriptions; now in Edinburgh."},
    {"name": "Yonaguni Monument - Japan",                "lat": 24.4353, "lon": 123.0086, "date": "Disputed",  "type": "Submarine Structure","notes": "Underwater step-pyramid structure; natural vs. man-made debate."},
    {"name": "Petroglyphs of Gobustan - Azerbaijan",     "lat": 40.0925, "lon": 49.3825, "date": "c. 10000 BCE","type": "Rock Carving",     "notes": "6000+ petroglyphs spanning 40,000 years; human figures, animals, boats."},
    {"name": "Val Camonica Petroglyphs - Italy",         "lat": 46.0253, "lon": 10.3528, "date": "c. 8000 BCE","type": "Rock Carving",      "notes": "Over 300,000 petroglyphs; UNESCO's first Italian World Heritage site."},
    {"name": "Newgrange Passage Tomb - Ireland",         "lat": 53.6947, "lon": -6.4753, "date": "c. 3200 BCE","type": "Megalithic Carving", "notes": "Tri-spiral and kerbstone carvings; astronomical alignment at solstice."},
    {"name": "Gobekli Tepe Pillar Carvings",             "lat": 37.2231, "lon": 38.9225, "date": "c. 9500 BCE","type": "T-Pillar Carvings",  "notes": "Earliest known monumental stone carvings; animal reliefs on T-pillars."},
]

MANUSCRIPT_TRADITIONS = [
    {"name": "Book of Kells - Trinity College Dublin",   "lat": 53.3438, "lon": -6.2546, "date": "c. 800 CE",  "tradition": "Insular Illumination",   "notes": "Finest example of Insular art; four Gospels in ornate Latin script."},
    {"name": "Lindisfarne Gospels - British Library",    "lat": 51.5299, "lon": -0.1267, "date": "c. 715 CE",  "tradition": "Insular Illumination",   "notes": "Anglo-Saxon masterpiece; elaborate carpet pages and decorated initials."},
    {"name": "Iona Abbey - Scotland",                    "lat": 56.3328, "lon": -6.3886, "date": "c. 563 CE",  "tradition": "Insular Monastic",       "notes": "Columban monastery; Book of Kells possibly created here."},
    {"name": "Skellig Michael - Monastic Scriptorium",   "lat": 51.7703, "lon": -10.5389,"date": "c. 600 CE",  "tradition": "Irish Monastic",         "notes": "Remote island monastery; monks preserved Latin learning."},
    {"name": "Topkapi Palace Library - Istanbul",        "lat": 41.0115, "lon": 28.9833, "date": "c. 1460 CE", "tradition": "Ottoman Calligraphy",    "notes": "Houses masterworks of Islamic calligraphy; imperial manuscripts."},
    {"name": "Alhambra - Granada Calligraphy",           "lat": 37.1760, "lon": -3.5881, "date": "c. 1350 CE", "tradition": "Islamic Calligraphy",    "notes": "Nasrid palace walls covered in ornamental Arabic calligraphy."},
    {"name": "Al-Qarawiyyin Library - Fez",              "lat": 34.0644, "lon": -5.0003, "date": "859 CE",     "tradition": "Islamic Manuscript",     "notes": "Oldest continuously operating library; priceless Quran manuscripts."},
    {"name": "Bodh Gaya - Buddhist Text Center",         "lat": 24.6961, "lon": 84.9911, "date": "c. 200 BCE", "tradition": "Buddhist Sutra",         "notes": "Site of Buddha's enlightenment; earliest Pali canon manuscripts nearby."},
    {"name": "Lhasa - Tibetan Buddhist Archives",        "lat": 29.6525, "lon": 91.1721, "date": "c. 700 CE",  "tradition": "Tibetan Buddhist",       "notes": "Potala Palace archives; Kangyur and Tengyur manuscript traditions."},
    {"name": "Nara - Japanese Buddhist Sutras",          "lat": 34.6851, "lon": 135.8048, "date": "c. 750 CE", "tradition": "Japanese Buddhist",      "notes": "Todai-ji temple archives; some of earliest Japanese manuscripts."},
    {"name": "Vivarium - Calabria",                      "lat": 38.7631, "lon": 16.5147, "date": "c. 540 CE",  "tradition": "Latin Monastic",         "notes": "Cassiodorus's monastery; systematic copying of classical texts."},
    {"name": "Bobbio Abbey - Italy",                     "lat": 44.7667, "lon":  9.3833, "date": "c. 614 CE",  "tradition": "Irish-Italian Monastic", "notes": "Founded by St. Columbanus; palimpsests of lost classical works."},
    {"name": "Bamberg State Library",                    "lat": 49.8988, "lon": 10.9028, "date": "c. 1000 CE", "tradition": "Ottonian Illumination",  "notes": "Emperor Henry II's collection; Bamberg Apocalypse manuscript."},
    {"name": "Samarkand - Quran of Uthman",              "lat": 39.6542, "lon": 66.9597, "date": "c. 650 CE",  "tradition": "Early Quranic",          "notes": "Claims to hold one of oldest Qurans; attributed to Caliph Uthman."},
    {"name": "Ethiopian Church Manuscripts - Lalibela",  "lat": 12.0319, "lon": 39.0472, "date": "c. 1200 CE", "tradition": "Ethiopic/Ge'ez",         "notes": "Rock-hewn churches with illuminated manuscripts in Ge'ez script."},
    {"name": "Dead Sea Scrolls Conservation - Jerusalem","lat": 31.7728, "lon": 35.2043, "date": "c. 250 BCE", "tradition": "Hebrew Scroll",          "notes": "Israel Museum Shrine of the Book; houses most complete scrolls."},
    {"name": "Codex Sinaiticus - British Library",       "lat": 51.5299, "lon": -0.1267, "date": "c. 350 CE",  "tradition": "Greek Uncial",           "notes": "Oldest near-complete Christian Bible; found at St Catherine's Sinai."},
    {"name": "Winchester Bible - Hampshire",             "lat": 51.0632, "lon": -1.3150, "date": "c. 1160 CE", "tradition": "English Romanesque",     "notes": "Largest surviving 12th-century Bible; single scribe, multiple illuminators."},
    {"name": "Reichenau Abbey - Lake Constance",         "lat": 47.6942, "lon": 9.0594,  "date": "c. 900 CE",  "tradition": "Ottonian Illumination",  "notes": "UNESCO site; produced some of finest Ottonian manuscript paintings."},
    {"name": "Clonmacnoise - Irish Scriptorium",         "lat": 53.3267, "lon": -7.9867, "date": "c. 544 CE",  "tradition": "Irish Monastic",         "notes": "Major early Irish monastery; produced Cross of the Scriptures."},
    {"name": "Aachen Palace Library",                    "lat": 50.7753, "lon": 6.0839,  "date": "c. 790 CE",  "tradition": "Carolingian",            "notes": "Charlemagne's court scriptorium; Carolingian minuscule developed here."},
    {"name": "Suleymaniye Library - Istanbul",           "lat": 41.0162, "lon": 28.9637, "date": "c. 1550 CE", "tradition": "Ottoman Manuscript",     "notes": "One of largest Ottoman manuscript collections; 100,000+ works."},
]

POSTAL_COMMUNICATION = [
    {"name": "Susa - Persian Royal Road Start",         "lat": 32.1900, "lon": 48.2500, "date": "c. 500 BCE", "type": "Royal Post (Angareion)",     "notes": "Darius I's postal relay; riders covered 2700km in 7 days."},
    {"name": "Sardis - Persian Royal Road End",          "lat": 38.4722, "lon": 28.0403, "date": "c. 500 BCE", "type": "Royal Post Terminal",        "notes": "Western terminus of Royal Road; 111 relay stations along route."},
    {"name": "Rome - Cursus Publicus HQ",                "lat": 41.9028, "lon": 12.4964, "date": "c. 20 BCE",  "type": "Roman Imperial Post",       "notes": "Augustus established state postal system; relay stations every 10 miles."},
    {"name": "Xi'an - Chinese Imperial Post Origin",     "lat": 34.2658, "lon": 108.9541,"date": "c. 200 BCE", "type": "Chinese Imperial Post",     "notes": "Qin dynasty postal relay; horse riders and foot messengers."},
    {"name": "Thurn und Taxis Castle - Regensburg",      "lat": 49.0195, "lon": 12.1016, "date": "1490 CE",    "type": "European Postal Service",   "notes": "Thurn-und-Taxis family ran first pan-European postal monopoly."},
    {"name": "Royal Mail GPO - London",                  "lat": 51.5185, "lon": -0.0963, "date": "1516 CE",    "type": "National Post Office",      "notes": "Henry VIII established Royal Mail; Penny Black stamp 1840."},
    {"name": "Chappe Telegraph - Paris",                 "lat": 48.8566, "lon": 2.3522,  "date": "1794 CE",    "type": "Optical Telegraph",         "notes": "Claude Chappe's semaphore network; Paris-Lille line first."},
    {"name": "Morse Telegraph Demo - Washington DC",     "lat": 38.8977, "lon": -77.0365, "date": "1844 CE",   "type": "Electric Telegraph",        "notes": "'What hath God wrought' - first telegraph message to Baltimore."},
    {"name": "Baltimore - Telegraph Terminus",           "lat": 39.2904, "lon": -76.6122, "date": "1844 CE",    "type": "Telegraph Terminus",        "notes": "Received Morse's first telegraph message from Washington."},
    {"name": "Pony Express Start - St. Joseph",          "lat": 39.7684, "lon": -94.8463, "date": "1860 CE",   "type": "Horse Mail Relay",          "notes": "1900-mile route to Sacramento; operated only 18 months."},
    {"name": "Pony Express End - Sacramento",            "lat": 38.5816, "lon": -121.4944,"date": "1860 CE",   "type": "Horse Mail Terminus",       "notes": "Western terminus; mail delivered in 10 days coast-to-coast."},
    {"name": "Transatlantic Cable - Valentia Island",    "lat": 51.9230, "lon": -10.3513, "date": "1866 CE",   "type": "Submarine Cable",           "notes": "Eastern terminus of first permanent transatlantic telegraph cable."},
    {"name": "Transatlantic Cable - Heart's Content",    "lat": 47.8667, "lon": -53.3667, "date": "1866 CE",   "type": "Submarine Cable",           "notes": "Western terminus in Newfoundland; completed by SS Great Eastern."},
    {"name": "Inca Chasqui Road - Cusco",               "lat": -13.5320,"lon": -71.9675, "date": "c. 1400 CE", "type": "Runner Relay (Chasqui)",   "notes": "Inca messenger system; quipu knot-records carried across empire."},
    {"name": "Mongol Yam Station - Karakorum",           "lat": 47.2000, "lon": 102.8333, "date": "c. 1220 CE","type": "Mongol Postal Relay",      "notes": "Genghis Khan's Yam system; fastest pre-modern postal network."},
    {"name": "Ottoman Imperial Post - Istanbul",         "lat": 41.0082, "lon": 28.9784, "date": "c. 1400 CE", "type": "Ottoman Postal Service",    "notes": "Menzilhane relay stations across the Ottoman Empire."},
    {"name": "Bengal Dak System - Kolkata",              "lat": 22.5726, "lon": 88.3639, "date": "c. 1766 CE", "type": "British India Post",        "notes": "Dak runners and postal horses; evolved into India Post."},
    {"name": "Universal Postal Union - Bern",            "lat": 46.9480, "lon": 7.4474,  "date": "1874 CE",    "type": "International Treaty",      "notes": "UPU established; standardized international mail exchange."},
    {"name": "Pigeon Post - Paris Siege",                "lat": 48.8566, "lon": 2.3522,  "date": "1870 CE",    "type": "Carrier Pigeon Post",       "notes": "During Prussian siege, microfilm messages carried by 300+ pigeons."},
    {"name": "Cape of Good Hope - Maritime Post",        "lat": -34.3568,"lon": 18.4740, "date": "c. 1500 CE", "type": "Maritime Post Stone",       "notes": "Sailors left letters under marked stones for passing ships to collect."},
    {"name": "Heliograph Station - Fort Apache",         "lat": 33.7867, "lon": -109.9736,"date": "1886 CE",   "type": "Heliograph Signal",         "notes": "Sun-mirror communication used by US Army in Apache campaigns."},
]

ALPHABET_ORIGINS = [
    {"name": "Byblos - Phoenician Alphabet Origin",      "lat": 34.1208, "lon": 35.6517, "date": "c. 1050 BCE","script": "Phoenician",     "family": "Semitic > All",         "letters": 22, "notes": "Ahiram sarcophagus; mother of Greek, Latin, Arabic, Hebrew scripts."},
    {"name": "Serabit el-Khadim - Proto-Sinaitic",       "lat": 29.0375, "lon": 33.4575, "date": "c. 1800 BCE","script": "Proto-Sinaitic", "family": "Egyptian > Phoenician",  "letters": 23, "notes": "Turquoise mines; Semitic workers adapted Egyptian hieroglyphs."},
    {"name": "Athens - Greek Vowel Innovation",          "lat": 37.9838, "lon": 23.7275, "date": "c. 800 BCE", "script": "Greek",          "family": "Phoenician > Greek",    "letters": 24, "notes": "Added vowels to Phoenician consonants; revolutionary writing change."},
    {"name": "Rome - Latin Alphabet Standardized",       "lat": 41.9028, "lon": 12.4964, "date": "c. 700 BCE", "script": "Latin",          "family": "Greek > Etruscan > Latin","letters": 23,"notes": "Adapted from Etruscan; originally 21 letters, expanded over centuries."},
    {"name": "Jerusalem - Paleo-Hebrew Script",          "lat": 31.7767, "lon": 35.2345, "date": "c. 1000 BCE","script": "Paleo-Hebrew",   "family": "Phoenician > Hebrew",   "letters": 22, "notes": "Closely related to Phoenician; used until replaced by Aramaic square script."},
    {"name": "Damascus - Aramaic Square Script",         "lat": 33.5138, "lon": 36.2765, "date": "c. 500 BCE", "script": "Aramaic",        "family": "Phoenician > Aramaic",  "letters": 22, "notes": "Lingua franca of ancient Near East; ancestor of Hebrew and Arabic."},
    {"name": "Mecca - Arabic Script Emergence",          "lat": 21.3891, "lon": 39.8579, "date": "c. 400 CE",  "script": "Arabic",         "family": "Nabataean > Arabic",    "letters": 28, "notes": "Evolved from Nabataean script; standardized with Quran."},
    {"name": "Ashoka Pillars - Brahmi Script",           "lat": 25.3670, "lon": 83.0100, "date": "c. 260 BCE", "script": "Brahmi",         "family": "Brahmi > Indic scripts","letters": 46, "notes": "Mother of all Indic scripts; Devanagari, Thai, Tibetan all descend from Brahmi."},
    {"name": "Kharoshti - Gandhara Region",              "lat": 34.0151, "lon": 71.5249, "date": "c. 300 BCE", "script": "Kharoshti",      "family": "Aramaic > Kharoshti",   "letters": 37, "notes": "Right-to-left script used in Gandhara; died out c. 300 CE."},
    {"name": "Preslav - Glagolitic to Cyrillic",         "lat": 43.1600, "lon": 26.8125, "date": "c. 893 CE",  "script": "Cyrillic",       "family": "Greek > Cyrillic",      "letters": 43, "notes": "Developed from Glagolitic; now used by ~250M people."},
    {"name": "Ohrid - Glagolitic Script Creation",       "lat": 41.1231, "lon": 20.8016, "date": "c. 863 CE",  "script": "Glagolitic",     "family": "Greek > Glagolitic",    "letters": 41, "notes": "Created by Cyril and Methodius for Slavic peoples."},
    {"name": "Musnad - South Arabian Script",            "lat": 15.3556, "lon": 44.2075, "date": "c. 800 BCE", "script": "South Arabian",  "family": "Proto-Sinaitic > South Arabian","letters": 29,"notes": "Ancient Yemeni kingdoms used this monumental script."},
    {"name": "Aksum - Ge'ez Script Origin",              "lat": 14.1308, "lon": 38.7200, "date": "c. 500 BCE", "script": "Ge'ez",          "family": "South Arabian > Ge'ez", "letters": 26, "notes": "Abjad evolved into abugida; unique script direction change."},
    {"name": "Carthage - Punic Script",                  "lat": 36.8528, "lon": 10.3233, "date": "c. 800 BCE", "script": "Punic",          "family": "Phoenician > Punic",    "letters": 22, "notes": "Phoenician colony script; spread across western Mediterranean."},
    {"name": "Ugarit - Cuneiform Alphabet",              "lat": 35.6006, "lon": 35.7825, "date": "c. 1300 BCE","script": "Ugaritic",       "family": "Independent Alphabet",  "letters": 30, "notes": "First known alphabet; cuneiform wedges for alphabetic writing."},
    {"name": "Nubian - Old Nubian Script",               "lat": 21.9225, "lon": 31.6233, "date": "c. 800 CE",  "script": "Old Nubian",     "family": "Coptic/Greek > Nubian", "letters": 28, "notes": "Medieval Christian Nubian script; adapted from Coptic and Greek."},
    {"name": "Tifinagh - Tuareg Script",                 "lat": 23.0000, "lon":  5.0000, "date": "c. 200 BCE", "script": "Tifinagh",       "family": "Libyco-Berber",         "letters": 33, "notes": "Indigenous North African script; revived by modern Amazigh movement."},
    {"name": "Cherokee - Sequoyah's Syllabary",          "lat": 35.5175, "lon": -84.0172, "date": "1821 CE",   "script": "Cherokee",       "family": "Independent Syllabary",  "letters": 85, "notes": "Created by Sequoyah alone; Cherokee literacy exceeded US average."},
    {"name": "N'Ko Script - Kankan, Guinea",             "lat": 10.3833, "lon": -9.3000, "date": "1949 CE",    "script": "N'Ko",           "family": "Independent Alphabet",  "letters": 27, "notes": "Created by Solomana Kante for Manding languages; widely used."},
    {"name": "Vai Script - Liberia",                     "lat":  6.3000, "lon": -10.8000, "date": "c. 1833 CE","script": "Vai",            "family": "Independent Syllabary", "letters": 212,"notes": "Created by Mɔmɔlu Duwalu Bukɛlɛ; one of few independently invented scripts."},
    {"name": "Osmanya Script - Mogadishu",               "lat":  2.0469, "lon": 45.3182, "date": "1920s CE",   "script": "Osmanya",        "family": "Independent Alphabet",  "letters": 30, "notes": "Created by Osman Yusuf Kenadid for Somali language."},
    {"name": "Bamum Script - Foumban, Cameroon",         "lat":  5.7264, "lon": 10.8981, "date": "c. 1896 CE", "script": "Bamum",          "family": "Independent Syllabary", "letters": 80, "notes": "King Njoya created and revised this script through 7 versions."},
    {"name": "Tangut Script - Yinchuan, China",          "lat": 38.4872, "lon": 106.2309, "date": "1036 CE",   "script": "Tangut",         "family": "Sinitic-inspired",      "letters": 6000,"notes": "Complex logographic script of Western Xia kingdom; deciphered from bilingual texts."},
]


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _styled_chart(title: str, categories: list, values: list, colors: list,
                  orientation: str = "h"):
    """Render a horizontal or vertical bar chart with dark theme."""
    fig, ax = plt.subplots(figsize=(7, max(3, len(categories) * 0.35)))
    fig.patch.set_facecolor(BG_OUTER)
    ax.set_facecolor(BG_INNER)

    if orientation == "h":
        bars = ax.barh(range(len(categories)), values, color=colors, alpha=0.85)
        ax.set_yticks(range(len(categories)))
        ax.set_yticklabels([c[:30] for c in categories], color=TEXT_SEC, fontsize=9)
        ax.set_xlabel(title, color=TEXT_SEC, fontsize=10)
        ax.invert_yaxis()
    else:
        bars = ax.bar(range(len(categories)), values, color=colors, alpha=0.85)
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels([c[:15] for c in categories], color=TEXT_SEC,
                           fontsize=8, rotation=45, ha="right")
        ax.set_ylabel(title, color=TEXT_SEC, fontsize=10)

    ax.tick_params(axis="both", colors=TEXT_SEC, labelsize=9)
    ax.grid(True, axis="x" if orientation == "h" else "y",
            color=GRID_CLR, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(SPINE_CLR)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _build_map(data: list, center_lat: float, center_lon: float,
               zoom: int, color: str, popup_fn, radius: int = 6):
    """Build a Folium dark-matter map and render it."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom,
                   tiles="CartoDB dark_matter")
    for item in data:
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            continue
        popup_html = popup_fn(item)
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)
    components.html(m._repr_html_(), height=500)
    return m


def _show_table_and_download(df: pd.DataFrame, label: str, filename: str,
                             key: str):
    """Show dataframe in expander and provide CSV download."""
    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} {label} (CSV)",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def _popup_safe(text: str) -> str:
    """Escape text for safe folium popup HTML."""
    return escape(str(text)) if text else ""


# ═══════════════════════════════════════════════════════════════════════
# MODE 1:  BIRTH OF WRITING
# ═══════════════════════════════════════════════════════════════════════

def _render_birth_of_writing():
    st.markdown("#### Birth of Writing")
    st.markdown(
        "Explore the independent origins of writing across Mesopotamia, Egypt, "
        "China, Mesoamerica, and the Indus Valley.  Each emergence was a "
        "transformative leap in human civilization, enabling administration, "
        "religion, literature, and law."
    )

    data = BIRTH_OF_WRITING

    # -- Stats --
    region_counts = {}
    script_counts = {}
    for d in data:
        region_counts[d["region"]] = region_counts.get(d["region"], 0) + 1
        script_counts[d["script"]] = script_counts.get(d["script"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Sites", len(data))
    cols[1].metric("Regions", len(region_counts))
    cols[2].metric("Scripts", len(script_counts))
    cols[3].metric("Oldest Claim", "c. 6600 BCE")

    # -- Chart --
    cats = list(region_counts.keys())
    vals = list(region_counts.values())
    clrs = [MODE_COLORS["Birth of Writing"]] * len(cats)
    _styled_chart("Sites per Region", cats, vals, clrs)

    # -- Map --
    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:240px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#aaa;">{_popup_safe(item["script"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:120])}</span>'
            f'</div>'
        )
    _build_map(data, 30.0, 50.0, 3, MODE_COLORS["Birth of Writing"], popup)

    # -- Notable highlights --
    st.markdown("---")
    st.markdown("##### Notable Highlights")
    highlights = [
        d for d in data if any(kw in d["name"].lower()
                               for kw in ["uruk", "abydos", "anyang", "jiahu", "olmec"])
    ]
    for h in highlights[:5]:
        st.markdown(
            f'<div style="border-left:3px solid {MODE_COLORS["Birth of Writing"]}; '
            f'padding-left:0.75rem; margin-bottom:0.6rem;">'
            f'<span style="color:{TEXT_PRI};font-weight:600;font-size:0.88rem;">'
            f'{escape(h["name"])}</span><br/>'
            f'<span style="color:{TEXT_SEC};font-size:0.78rem;">'
            f'{escape(h["script"])} &mdash; {escape(h["date"])}</span><br/>'
            f'<span style="color:{TEXT_MUT};font-size:0.75rem;">'
            f'{escape(h["notes"])}</span></div>',
            unsafe_allow_html=True,
        )

    # -- Table & download --
    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Birth of Writing Sites", "birth_of_writing.csv",
                             "dl_birth")


# ═══════════════════════════════════════════════════════════════════════
# MODE 2:  UNDECIPHERED SCRIPTS
# ═══════════════════════════════════════════════════════════════════════

def _render_undeciphered_scripts():
    st.markdown("#### Undeciphered Scripts")
    st.markdown(
        "Some ancient scripts remain mysteries despite decades of effort.  "
        "Linear A, Rongorongo, the Indus Valley script, and the Voynich "
        "Manuscript continue to puzzle linguists and cryptographers worldwide."
    )

    data = UNDECIPHERED_SCRIPTS

    status_counts = {}
    script_counts = {}
    for d in data:
        status_counts[d["status"]] = status_counts.get(d["status"], 0) + 1
        script_counts[d["script"]] = script_counts.get(d["script"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Sites", len(data))
    cols[1].metric("Fully Undeciphered", status_counts.get("Undeciphered", 0))
    cols[2].metric("Partially Read", status_counts.get("Partially read", 0))
    cols[3].metric("Distinct Scripts", len(script_counts))

    cats = list(script_counts.keys())
    vals = list(script_counts.values())
    clrs = [MODE_COLORS["Undeciphered Scripts"]] * len(cats)
    _styled_chart("Sites per Script", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:240px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#f87171;">{_popup_safe(item["script"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Status: {_popup_safe(item["status"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:120])}</span>'
            f'</div>'
        )
    _build_map(data, 25.0, 40.0, 2, MODE_COLORS["Undeciphered Scripts"], popup)

    # -- Status breakdown --
    st.markdown("---")
    st.markdown("##### Decipherment Status Breakdown")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        pct = count / len(data) * 100
        bar_w = int(pct * 2.5)
        st.markdown(
            f'<div style="margin-bottom:0.4rem;">'
            f'<span style="color:{TEXT_PRI};font-size:0.85rem;">{escape(status)}: '
            f'{count}</span> '
            f'<span style="display:inline-block;height:8px;width:{bar_w}px;'
            f'background:{MODE_COLORS["Undeciphered Scripts"]};border-radius:4px;'
            f'vertical-align:middle;"></span>'
            f'<span style="color:{TEXT_MUT};font-size:0.75rem;"> ({pct:.0f}%)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Undeciphered Script Sites",
                             "undeciphered_scripts.csv", "dl_undeciphered")


# ═══════════════════════════════════════════════════════════════════════
# MODE 3:  ROSETTA STONES
# ═══════════════════════════════════════════════════════════════════════

def _render_rosetta_stones():
    st.markdown("#### Rosetta Stones & Decoder Artifacts")
    st.markdown(
        "Bilingual and trilingual inscriptions have been the keys to unlocking "
        "lost languages.  From the Rosetta Stone to the Behistun Inscription, "
        "these artifacts bridged millennia of silence."
    )

    data = ROSETTA_STONES

    script_set = set()
    for d in data:
        for s in d["scripts"].split(", "):
            script_set.add(s.strip())

    cols = st.columns(4)
    cols[0].metric("Total Artifacts", len(data))
    cols[1].metric("Scripts Represented", len(script_set))
    cols[2].metric("Oldest Artifact", "c. 1350 BCE")
    cols[3].metric("Most Recent", "1850s CE")

    # Count scripts
    script_freq = {}
    for d in data:
        for s in d["scripts"].split(", "):
            s = s.strip()
            script_freq[s] = script_freq.get(s, 0) + 1
    cats = sorted(script_freq, key=script_freq.get, reverse=True)[:12]
    vals = [script_freq[c] for c in cats]
    clrs = [MODE_COLORS["Rosetta Stones"]] * len(cats)
    _styled_chart("Occurrences per Script", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:240px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#a78bfa;">{_popup_safe(item["artifact"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Scripts: {_popup_safe(item["scripts"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )
    _build_map(data, 35.0, 30.0, 3, MODE_COLORS["Rosetta Stones"], popup)

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Decoder Artifacts", "rosetta_stones.csv",
                             "dl_rosetta")


# ═══════════════════════════════════════════════════════════════════════
# MODE 4:  ANCIENT LIBRARIES
# ═══════════════════════════════════════════════════════════════════════

def _render_ancient_libraries():
    st.markdown("#### Ancient Libraries & Archives")
    st.markdown(
        "From the legendary Library of Alexandria to the hidden caves of "
        "Dunhuang, explore the great repositories of human knowledge that "
        "preserved and transmitted civilisation across millennia."
    )

    data = ANCIENT_LIBRARIES

    type_counts = {}
    for d in data:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Libraries", len(data))
    cols[1].metric("Library Types", len(type_counts))
    cols[2].metric("Oldest", "c. 2400 BCE")
    cols[3].metric("Span", "~4400 years")

    cats = list(type_counts.keys())
    vals = list(type_counts.values())
    clrs = [MODE_COLORS["Ancient Libraries"]] * len(cats)
    _styled_chart("Libraries by Type", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:260px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#22d3ee;">{_popup_safe(item["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Est. volumes: {_popup_safe(item["est_volumes"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )
    _build_map(data, 35.0, 35.0, 3, MODE_COLORS["Ancient Libraries"], popup, radius=7)

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Ancient Libraries", "ancient_libraries.csv",
                             "dl_libraries")


# ═══════════════════════════════════════════════════════════════════════
# MODE 5:  PRINTING PRESS REVOLUTION
# ═══════════════════════════════════════════════════════════════════════

def _render_printing_press():
    st.markdown("#### Printing Press Revolution")
    st.markdown(
        "Trace the invention and spread of printing technology, from Bi Sheng's "
        "ceramic movable type in 11th-century China, through Korea's metal type "
        "and Japanese woodblock printing, to Gutenberg's transformative press "
        "that ignited the European Renaissance."
    )

    data = PRINTING_PRESS

    type_counts = {}
    for d in data:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Sites", len(data))
    cols[1].metric("Press Types", len(type_counts))
    cols[2].metric("Earliest Print", "770 CE")
    cols[3].metric("Span", "~770 years")

    cats = list(type_counts.keys())
    vals = list(type_counts.values())
    clrs = [MODE_COLORS["Printing Press Revolution"]] * len(cats)
    _styled_chart("Sites per Press Type", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:240px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#34d399;">{_popup_safe(item["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )
    _build_map(data, 35.0, 30.0, 2, MODE_COLORS["Printing Press Revolution"], popup)

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Printing Sites", "printing_press.csv",
                             "dl_printing")


# ═══════════════════════════════════════════════════════════════════════
# MODE 6:  WORLD WRITING SYSTEMS
# ═══════════════════════════════════════════════════════════════════════

def _render_writing_systems():
    st.markdown("#### World's Writing Systems")
    st.markdown(
        "A global survey of the scripts in active use today - Latin, Cyrillic, "
        "Arabic, Devanagari, Chinese, Japanese, Korean, and many more.  Each "
        "script carries the history, identity, and art of its culture."
    )

    data = WRITING_SYSTEMS

    family_counts = {}
    for d in data:
        family_counts[d["family"]] = family_counts.get(d["family"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Scripts Mapped", len(data))
    cols[1].metric("Script Families", len(family_counts))
    cols[2].metric("Oldest Active", "c. 700 BCE")
    cols[3].metric("Newest", "1443 CE")

    cats = list(family_counts.keys())
    vals = list(family_counts.values())
    clrs = [MODE_COLORS["World Writing Systems"]] * len(cats)
    _styled_chart("Scripts per Family", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:250px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;color:#f472b6;">{_popup_safe(item["script"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Family: {_popup_safe(item["family"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Speakers: {_popup_safe(item["speakers"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:120])}</span>'
            f'</div>'
        )
    _build_map(data, 25.0, 50.0, 2, MODE_COLORS["World Writing Systems"], popup,
               radius=7)

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Writing Systems", "writing_systems.csv",
                             "dl_systems")


# ═══════════════════════════════════════════════════════════════════════
# MODE 7:  STONE INSCRIPTIONS
# ═══════════════════════════════════════════════════════════════════════

def _render_stone_inscriptions():
    st.markdown("#### Stone Inscriptions & Monumental Writing")
    st.markdown(
        "From the cliff face of Behistun to the Aztec Sun Stone, monumental "
        "inscriptions were carved to last forever.  Explore famous stelae, "
        "rock edicts, pillars, and carved monoliths around the world."
    )

    data = STONE_INSCRIPTIONS

    type_counts = {}
    for d in data:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Inscriptions", len(data))
    cols[1].metric("Types", len(type_counts))
    cols[2].metric("Oldest", "c. 3600 BCE")
    cols[3].metric("Most Famous", "Rosetta Stone")

    cats = list(type_counts.keys())
    vals = list(type_counts.values())
    clrs = [MODE_COLORS["Stone Inscriptions"]] * len(cats)
    _styled_chart("Inscriptions by Type", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:240px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#fb923c;">{_popup_safe(item["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )
    _build_map(data, 30.0, 30.0, 2, MODE_COLORS["Stone Inscriptions"], popup)

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Stone Inscriptions", "stone_inscriptions.csv",
                             "dl_stones")


# ═══════════════════════════════════════════════════════════════════════
# MODE 8:  MANUSCRIPT TRADITIONS
# ═══════════════════════════════════════════════════════════════════════

def _render_manuscript_traditions():
    st.markdown("#### Manuscript Traditions")
    st.markdown(
        "Illuminated manuscripts, Islamic calligraphy, Buddhist sutras, and "
        "monastic scriptoria preserved and beautified the written word for "
        "centuries.  Explore the workshops that kept knowledge alive through "
        "the ages."
    )

    data = MANUSCRIPT_TRADITIONS

    tradition_counts = {}
    for d in data:
        tradition_counts[d["tradition"]] = tradition_counts.get(d["tradition"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Sites", len(data))
    cols[1].metric("Traditions", len(tradition_counts))
    cols[2].metric("Oldest", "c. 250 BCE")
    cols[3].metric("Span", "~1400 years")

    cats = list(tradition_counts.keys())
    vals = list(tradition_counts.values())
    clrs = [MODE_COLORS["Manuscript Traditions"]] * len(cats)
    _styled_chart("Sites per Tradition", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:250px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#7dd3fc;">{_popup_safe(item["tradition"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )
    _build_map(data, 38.0, 30.0, 2, MODE_COLORS["Manuscript Traditions"], popup,
               radius=7)

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Manuscript Sites", "manuscript_traditions.csv",
                             "dl_manuscripts")


# ═══════════════════════════════════════════════════════════════════════
# MODE 9:  POSTAL & COMMUNICATION HISTORY
# ═══════════════════════════════════════════════════════════════════════

def _render_postal_communication():
    st.markdown("#### Postal & Communication History")
    st.markdown(
        "From the Persian Royal Road's mounted couriers to the electric "
        "telegraph, follow the evolution of long-distance communication.  "
        "Postal relays, semaphore towers, undersea cables, and the Pony "
        "Express connected civilizations across vast distances."
    )

    data = POSTAL_COMMUNICATION

    type_counts = {}
    for d in data:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Total Sites", len(data))
    cols[1].metric("Communication Types", len(type_counts))
    cols[2].metric("Oldest System", "c. 500 BCE")
    cols[3].metric("Newest System", "1874 CE")

    cats = list(type_counts.keys())
    vals = list(type_counts.values())
    clrs = [MODE_COLORS["Postal & Communication"]] * len(cats)
    _styled_chart("Sites per System Type", cats, vals, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:240px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#c084fc;">{_popup_safe(item["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )

    # Draw connecting lines for notable routes
    m = folium.Map(location=[35.0, 30.0], zoom_start=2,
                   tiles="CartoDB dark_matter")

    # Persian Royal Road line
    folium.PolyLine(
        locations=[[32.19, 48.25], [38.47, 28.04]],
        color="#a855f7", weight=2, opacity=0.6,
        dash_array="8 4",
        popup=folium.Popup("Persian Royal Road (c. 500 BCE)", max_width=200),
    ).add_to(m)

    # Pony Express line
    folium.PolyLine(
        locations=[[39.77, -94.85], [38.58, -121.49]],
        color="#a855f7", weight=2, opacity=0.6,
        dash_array="8 4",
        popup=folium.Popup("Pony Express Route (1860)", max_width=200),
    ).add_to(m)

    # Transatlantic cable line
    folium.PolyLine(
        locations=[[51.92, -10.35], [47.87, -53.37]],
        color="#a855f7", weight=2, opacity=0.6,
        dash_array="8 4",
        popup=folium.Popup("Transatlantic Telegraph Cable (1866)", max_width=200),
    ).add_to(m)

    # Morse telegraph line
    folium.PolyLine(
        locations=[[38.90, -77.04], [39.29, -76.61]],
        color="#a855f7", weight=2, opacity=0.6,
        dash_array="8 4",
        popup=folium.Popup("Morse Telegraph Line (1844)", max_width=200),
    ).add_to(m)

    for item in data:
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            continue
        popup_html = (
            f'<div style="max-width:240px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#c084fc;">{_popup_safe(item["type"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color=MODE_COLORS["Postal & Communication"],
            fill=True,
            fill_color=MODE_COLORS["Postal & Communication"],
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Postal & Communication Sites",
                             "postal_communication.csv", "dl_postal")


# ═══════════════════════════════════════════════════════════════════════
# MODE 10:  ALPHABET ORIGINS
# ═══════════════════════════════════════════════════════════════════════

def _render_alphabet_origins():
    st.markdown("#### Alphabet Origins & Family Trees")
    st.markdown(
        "Trace the evolution of alphabets from their Proto-Sinaitic and "
        "Phoenician roots through Greek, Latin, Aramaic, Brahmi, and beyond.  "
        "See how a handful of ancient innovations branched into the hundreds "
        "of scripts used today."
    )

    data = ALPHABET_ORIGINS

    family_counts = {}
    for d in data:
        family_counts[d["family"]] = family_counts.get(d["family"], 0) + 1

    cols = st.columns(4)
    cols[0].metric("Scripts Mapped", len(data))
    cols[1].metric("Family Lines", len(family_counts))
    cols[2].metric("Oldest", "c. 1800 BCE")
    cols[3].metric("Most Recent", "1949 CE")

    # Letter count chart
    scripts = [d["script"] for d in data]
    letter_counts = [d.get("letters", 0) for d in data]
    clrs = [MODE_COLORS["Alphabet Origins"]] * len(scripts)
    _styled_chart("Letters per Script", scripts, letter_counts, clrs)

    st.markdown("---")
    st.markdown("##### Interactive Map")

    def popup(item):
        return (
            f'<div style="max-width:260px;">'
            f'<strong>{_popup_safe(item["name"])}</strong><br/>'
            f'<span style="font-size:0.85rem;color:#2dd4bf;">{_popup_safe(item["script"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Family: {_popup_safe(item["family"])}</span><br/>'
            f'<span style="font-size:0.75rem;">Letters: {_popup_safe(str(item.get("letters", "?")))}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["date"])}</span><br/>'
            f'<span style="font-size:0.75rem;">{_popup_safe(item["notes"][:130])}</span>'
            f'</div>'
        )

    # Custom map with lineage arrows
    m = folium.Map(location=[30.0, 35.0], zoom_start=3,
                   tiles="CartoDB dark_matter")

    # Draw evolution lines (Proto-Sinaitic > Phoenician > Greek > Latin)
    evolution_lines = [
        # Proto-Sinaitic to Phoenician
        {"from": [29.04, 33.46], "to": [34.12, 35.65], "label": "Proto-Sinaitic > Phoenician"},
        # Phoenician to Greek
        {"from": [34.12, 35.65], "to": [37.98, 23.73], "label": "Phoenician > Greek"},
        # Greek to Latin
        {"from": [37.98, 23.73], "to": [41.90, 12.50], "label": "Greek > Latin"},
        # Phoenician to Aramaic
        {"from": [34.12, 35.65], "to": [33.51, 36.28], "label": "Phoenician > Aramaic"},
        # Aramaic to Arabic
        {"from": [33.51, 36.28], "to": [21.39, 39.86], "label": "Aramaic > Arabic"},
        # Phoenician to Hebrew
        {"from": [34.12, 35.65], "to": [31.78, 35.23], "label": "Phoenician > Hebrew"},
        # Brahmi to Devanagari (via mode 6 Varanasi)
        {"from": [25.37, 83.01], "to": [25.32, 83.01], "label": "Brahmi > Indic scripts"},
        # Greek to Cyrillic
        {"from": [37.98, 23.73], "to": [43.16, 26.81], "label": "Greek > Cyrillic"},
    ]

    for line in evolution_lines:
        folium.PolyLine(
            locations=[line["from"], line["to"]],
            color="#14b8a6", weight=2, opacity=0.5,
            dash_array="6 4",
            popup=folium.Popup(escape(line["label"]), max_width=200),
        ).add_to(m)

    for item in data:
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            continue
        popup_html = popup(item)
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=MODE_COLORS["Alphabet Origins"],
            fill=True,
            fill_color=MODE_COLORS["Alphabet Origins"],
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # -- Alphabet family tree text diagram --
    st.markdown("---")
    st.markdown("##### Alphabet Family Tree (simplified)")
    st.code(
        "Proto-Sinaitic (c.1800 BCE)\n"
        "  +-- Phoenician (c.1050 BCE)\n"
        "  |     +-- Greek (c.800 BCE)\n"
        "  |     |     +-- Etruscan > Latin (c.700 BCE)\n"
        "  |     |     +-- Coptic\n"
        "  |     |     +-- Glagolitic > Cyrillic (c.863 CE)\n"
        "  |     |     +-- Armenian (405 CE)\n"
        "  |     |     +-- Georgian (c.300 CE)\n"
        "  |     +-- Aramaic (c.800 BCE)\n"
        "  |     |     +-- Hebrew (square script)\n"
        "  |     |     +-- Nabataean > Arabic (c.400 CE)\n"
        "  |     |     +-- Syriac\n"
        "  |     |     +-- Kharoshti\n"
        "  |     +-- Paleo-Hebrew\n"
        "  |     +-- Punic\n"
        "  |     +-- South Arabian > Ge'ez (c.500 BCE)\n"
        "  |     +-- Libyco-Berber > Tifinagh\n"
        "  +-- Brahmi (c.300 BCE)  [possibly independent]\n"
        "        +-- Devanagari\n"
        "        +-- Tamil / Sinhala / Thai / Khmer / Myanmar / Tibetan\n"
        "\n"
        "Independent:\n"
        "  Chinese (c.1250 BCE) > Japanese Kana / Korean adapted\n"
        "  Hangul (1443 CE) - scientifically designed\n"
        "  Cherokee (1821) - created by Sequoyah\n"
        "  N'Ko (1949) - created by Solomana Kante",
        language=None,
    )

    st.markdown("---")
    df = pd.DataFrame(data)
    _show_table_and_download(df, "Alphabet Origin Sites",
                             "alphabet_origins.csv", "dl_alphabets")


# ═══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════

MAP_MODES = {
    "Birth of Writing":            _render_birth_of_writing,
    "Undeciphered Scripts":        _render_undeciphered_scripts,
    "Rosetta Stones":              _render_rosetta_stones,
    "Ancient Libraries":           _render_ancient_libraries,
    "Printing Press Revolution":   _render_printing_press,
    "World Writing Systems":       _render_writing_systems,
    "Stone Inscriptions":          _render_stone_inscriptions,
    "Manuscript Traditions":       _render_manuscript_traditions,
    "Postal & Communication":      _render_postal_communication,
    "Alphabet Origins":            _render_alphabet_origins,
}


def render_writing_maps_tab():
    """Main entry point -- called from app.py inside a tab."""

    # ── Tab Header ──
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>Ancient Writing &amp; Scripts Explorer</h4>'
        '<p>Map the birth of writing, undeciphered scripts, decoder artifacts, '
        'ancient libraries, printing revolutions, world scripts, stone '
        'inscriptions, manuscript traditions, postal history, and alphabet '
        'family trees across 5 000 years of human communication.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode Selector ──
    st.markdown("#### Select Map Mode")

    mode_names = list(MAP_MODES.keys())
    selected = st.selectbox(
        "Writing & Scripts Map Mode",
        mode_names,
        index=0,
        key="writing_maps_mode",
        help="Choose one of 10 curated map modes exploring writing history.",
    )

    # ── Color legend for all modes ──
    legend_items = " ".join(
        f'<span style="color:{MODE_COLORS[m]}; font-size:0.78rem;">'
        f'{"&#9679;" if m == selected else "&#9675;"} {m}</span>'
        for m in mode_names
    )
    st.markdown(
        f'<div style="display:flex; gap:0.6rem; flex-wrap:wrap; '
        f'margin-bottom:0.75rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Render selected mode ──
    MAP_MODES[selected]()
